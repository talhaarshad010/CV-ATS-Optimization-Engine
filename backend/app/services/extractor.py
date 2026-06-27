import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

MINIMUM_TEXT_LENGTH = 100


def _extract_with_pymupdf(file_bytes: bytes) -> Optional[str]:
    try:
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "\n".join(page.get_text("text", sort=True) for page in doc)
        doc.close()
        return text.strip() if len(text.strip()) >= MINIMUM_TEXT_LENGTH else None
    except Exception as e:
        logger.warning(f"PyMuPDF failed: {e}")
        return None


def _extract_with_pdfplumber(file_bytes: bytes) -> Optional[str]:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text.strip() if len(text.strip()) >= MINIMUM_TEXT_LENGTH else None
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")
        return None


def _extract_with_easyocr(file_bytes: bytes) -> Optional[str]:
    try:
        import fitz
        import easyocr
        from PIL import Image
        import numpy as np

        reader = easyocr.Reader(["en"], gpu=False)
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        all_text = []
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            result = reader.readtext(np.array(img), detail=0)
            all_text.append(" ".join(result))
        doc.close()
        text = "\n".join(all_text).strip()
        return text if len(text) >= MINIMUM_TEXT_LENGTH else None
    except Exception as e:
        logger.warning(f"EasyOCR failed: {e}")
        return None


def extract_pdf(file_bytes: bytes, candidate_id: Optional[str] = None) -> str:
    """Fallback chain: PyMuPDF -> pdfplumber -> EasyOCR."""
    import time
    start_time = time.time()
    method = None

    text = _extract_with_pymupdf(file_bytes)
    if text:
        method = "pymupdf"
        logger.info("Extracted with PyMuPDF")
    else:
        text = _extract_with_pdfplumber(file_bytes)
        if text:
            method = "pdfplumber"
            logger.info("Extracted with pdfplumber")
        else:
            text = _extract_with_easyocr(file_bytes)
            if text:
                method = "easyocr"
                logger.info("Extracted with EasyOCR (scanned PDF)")
            else:
                raise ValueError("Could not extract text from PDF — file may be corrupted or empty.")

    duration = time.time() - start_time
    if candidate_id and method:
        try:
            import sys
            import os
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
            from ml import tracking
            tracking.log_extraction_run(candidate_id, method, len(text), duration)
        except Exception as e:
            logger.warning(f"Failed to log extraction run to MLflow: {e}")

    return text


def _extract_with_python_docx(file_bytes: bytes) -> Optional[str]:
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        text = "\n".join(p.text for p in doc.paragraphs)
        return text.strip() if len(text.strip()) >= MINIMUM_TEXT_LENGTH else None
    except Exception as e:
        logger.warning(f"python-docx failed: {e}")
        return None


def _extract_with_mammoth(file_bytes: bytes) -> Optional[str]:
    try:
        import mammoth
        result = mammoth.extract_raw_text(io.BytesIO(file_bytes))
        text = result.value.strip()
        return text if len(text) >= MINIMUM_TEXT_LENGTH else None
    except Exception as e:
        logger.warning(f"Mammoth failed: {e}")
        return None


def extract_docx(file_bytes: bytes, candidate_id: Optional[str] = None) -> str:
    """Fallback chain: python-docx -> Mammoth."""
    import time
    start_time = time.time()
    method = None

    text = _extract_with_python_docx(file_bytes)
    if text:
        method = "python-docx"
        logger.info("Extracted with python-docx")
    else:
        text = _extract_with_mammoth(file_bytes)
        if text:
            method = "mammoth"
            logger.info("Extracted with Mammoth")
        else:
            raise ValueError("Could not extract text from DOCX — file may be corrupted or empty.")

    duration = time.time() - start_time
    if candidate_id and method:
        try:
            import sys
            import os
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
            from ml import tracking
            tracking.log_extraction_run(candidate_id, method, len(text), duration)
        except Exception as e:
            logger.warning(f"Failed to log extraction run to MLflow: {e}")

    return text


SUPPORTED_TYPES = {
    "application/pdf": extract_pdf,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": extract_docx,
    "application/msword": extract_docx,
}


def extract(file_bytes: bytes, content_type: str, candidate_id: Optional[str] = None) -> str:
    """Main extraction entry point. Routes by content type."""
    extractor_fn = SUPPORTED_TYPES.get(content_type)
    if not extractor_fn:
        raise ValueError(
            f"Unsupported file type: {content_type}. Supported: PDF, DOCX"
        )
    return extractor_fn(file_bytes, candidate_id)
