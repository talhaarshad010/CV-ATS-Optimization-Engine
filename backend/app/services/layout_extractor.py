import os
import io
import logging
import re
import fitz
import torch
from PIL import Image
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

# Global cached instances of processor and model
_processor = None
_model = None

def get_layoutlmv3() -> Tuple[Any, Any]:
    """Lazily loads and caches the LayoutLMv3 processor and model, selecting device."""
    global _processor, _model
    if _processor is None or _model is None:
        logger.info("Loading LayoutLMv3 model 'microsoft/layoutlmv3-base' from HuggingFace (~500MB)...")
        from transformers import LayoutLMv3Processor, LayoutLMv3Model
        
        _processor = LayoutLMv3Processor.from_pretrained("microsoft/layoutlmv3-base")
        _model = LayoutLMv3Model.from_pretrained("microsoft/layoutlmv3-base")
        
        # Select PyTorch device
        device = "cpu"
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
            
        _model = _model.to(device)
        logger.info(f"LayoutLMv3 model loaded successfully on device: {device}")
        
    return _processor, _model

def run_ocr(img: Image.Image) -> Tuple[List[str], List[List[int]]]:
    """Runs OCR on a PIL Image and returns words and bounding boxes [x0, y0, x1, y1]."""
    # 1. Try PyTesseract first
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        
        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        words = []
        boxes = []
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            if text:
                words.append(text)
                x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                boxes.append([x, y, x + w, y + h])
        if words:
            logger.info("OCR completed successfully using PyTesseract.")
            return words, boxes
    except Exception as e:
        logger.debug(f"PyTesseract is not available or failed: {e}. Falling back to EasyOCR.")
        
    # 2. Try EasyOCR fallback (already in requirements.txt)
    try:
        import easyocr
        import numpy as np
        
        reader = easyocr.Reader(['en'], gpu=False)
        img_np = np.array(img)
        ocr_results = reader.readtext(img_np)
        
        words = []
        boxes = []
        for bbox, text, conf in ocr_results:
            text = text.strip()
            if text:
                words.append(text)
                # bbox is [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
                x0 = int(bbox[0][0])
                y0 = int(bbox[0][1])
                x1 = int(bbox[2][0])
                y1 = int(bbox[2][1])
                boxes.append([x0, y0, x1, y1])
        if words:
            logger.info("OCR completed successfully using EasyOCR.")
            return words, boxes
    except Exception as e:
        logger.error(f"EasyOCR failed: {e}")
        
    return [], []

def sort_layout_blocks(words: List[str], boxes: List[List[int]]) -> List[str]:
    """
    Sorts words by reading order layout: top-to-bottom, then left-to-right.
    Uses horizontal overlap and vertical coordinates.
    """
    items = list(zip(words, boxes))
    items.sort(key=lambda x: x[1][1])  # Sort primarily by y0 (top coordinate)
    
    lines = []
    current_line = []
    
    for item in items:
        word, box = item
        x0, y0, x1, y1 = box
        
        if not current_line:
            current_line.append(item)
        else:
            # Check if this item belongs to the current line
            ref_box = current_line[0][1]
            ref_y0, ref_y1 = ref_box[1], ref_box[3]
            ref_height = ref_y1 - ref_y0
            
            mid_y = (y0 + y1) / 2
            # 30% vertical overlap tolerance
            if ref_y0 - ref_height * 0.3 <= mid_y <= ref_y1 + ref_height * 0.3:
                current_line.append(item)
            else:
                # Close current line, sort it left-to-right by x0
                current_line.sort(key=lambda x: x[1][0])
                lines.append(current_line)
                current_line = [item]
                
    if current_line:
        current_line.sort(key=lambda x: x[1][0])
        lines.append(current_line)
        
    # Flatten sorted lines
    sorted_words = []
    for line in lines:
        for word, _ in line:
            sorted_words.append(word)
            
    return sorted_words

def extract_with_layout(file_bytes: bytes) -> Optional[str]:
    """
    Checks if a PDF requires LayoutLMv3 text extraction (less than 200 chars plain text on first page).
    If needed, runs LayoutLMv3 to extract and return structured text; otherwise, returns None.
    """
    try:
        # 1. Detect if PDF needs LayoutLMv3
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if len(doc) == 0:
            return None
            
        first_page_text = doc[0].get_text().strip()
        if len(first_page_text) >= 200:
            logger.info(f"Skipping LayoutLMv3: Plain text extraction is sufficient ({len(first_page_text)} chars).")
            doc.close()
            return None
            
        logger.info(f"Plain text extraction is poor ({len(first_page_text)} chars). Running LayoutLMv3 fallback...")
        
        # 2. Setup LayoutLMv3
        processor, model = get_layoutlmv3()
        device = model.device
        pages_text = []
        
        # Process each page
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            
            # Convert PDF page to PIL image at 150 DPI (zoom factor = 150 / 72 = 2.0833)
            zoom = 150 / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
            
            # Run OCR to get words and coordinates
            words, boxes = run_ocr(img)
            if not words:
                continue
                
            # Normalize boxes to 0-1000 range for LayoutLMv3
            width, height = img.size
            normalized_boxes = []
            for box in boxes:
                nx0 = int(max(0, min(1000, 1000 * (box[0] / width))))
                ny0 = int(max(0, min(1000, 1000 * (box[1] / height))))
                nx1 = int(max(0, min(1000, 1000 * (box[2] / width))))
                ny1 = int(max(0, min(1000, 1000 * (box[3] / height))))
                normalized_boxes.append([nx0, ny0, nx1, ny1])
                
            # Prepare inputs and run LayoutLMv3 forward pass
            encoding = processor(img, words, boxes=normalized_boxes, return_tensors="pt")
            inputs = {k: v.to(device) for k, v in encoding.items()}
            
            with torch.no_grad():
                # Runs forward pass to compute visual-textual layout representation
                _ = model(**inputs)
                
            # Sort extracted text blocks by reading order layout
            sorted_words = sort_layout_blocks(words, boxes)
            pages_text.append(" ".join(sorted_words))
            
        doc.close()
        return "\n\n".join(pages_text)
        
    except Exception as e:
        logger.error(f"LayoutLMv3 text extraction failed: {e}", exc_info=True)
        return None
