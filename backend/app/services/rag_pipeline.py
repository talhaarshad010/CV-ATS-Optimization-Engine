import os
import logging
import threading
from typing import Dict, Any, List, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.utils.supabase_client import supabase
from app.utils.ollama_client import generate

logger = logging.getLogger(__name__)

INDEX_PATH = "/Users/muhammadtalhaarshad/Downloads/cv-platform/ml/models/faiss_index"

_lock = threading.RLock()
_embeddings = None
_vector_store = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Lazily loads and caches HuggingFaceEmbeddings with thread safety."""
    global _embeddings
    with _lock:
        if _embeddings is None:
            logger.info("Initializing HuggingFaceEmbeddings ('all-MiniLM-L6-v2')...")
            # Suppress deprecation warnings from LangChain internally
            import warnings
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings


def get_vector_store() -> FAISS:
    """Lazily loads the local FAISS index or builds a new one if missing with thread safety."""
    global _vector_store
    with _lock:
        if _vector_store is None:
            embeddings = get_embeddings()
            if os.path.exists(os.path.join(INDEX_PATH, "index.faiss")):
                logger.info("Loading existing FAISS index...")
                try:
                    _vector_store = FAISS.load_local(
                        INDEX_PATH, 
                        embeddings, 
                        allow_dangerous_deserialization=True
                    )
                except Exception as e:
                    logger.error(f"Failed to load FAISS index from local cache: {e}. Rebuilding index...")
                    _vector_store = refresh_index()
            else:
                logger.info("Local FAISS index not found. Building index from scratch...")
                _vector_store = refresh_index()
    return _vector_store


def refresh_index() -> FAISS:
    """
    Rebuilds the FAISS vector store by fetching all raw_text records 
    for candidates and job descriptions from Supabase, chunking them, 
    generating embeddings, and persisting the index.
    """
    global _vector_store
    _lock.acquire()
    try:
        logger.info("Rebuilding FAISS index from Supabase data...")
        
        documents = []
        
        # 1. Fetch Candidates raw text
        try:
            candidates_resp = supabase.table("candidates").select("id, file_name, raw_text").execute()
            candidates = candidates_resp.data or []
            for cand in candidates:
                text = cand.get("raw_text", "").strip()
                if text:
                    documents.append(Document(
                        page_content=text,
                        metadata={
                            "type": "candidate",
                            "candidate_id": cand.get("id"),
                            "file_name": cand.get("file_name", "Unknown File")
                        }
                    ))
        except Exception as e:
            logger.warning(f"Failed to fetch candidates for FAISS index: {e}")
            
        # 2. Fetch Job Descriptions raw text
        try:
            jds_resp = supabase.table("job_descriptions").select("id, title, raw_text").execute()
            jds = jds_resp.data or []
            for jd in jds:
                text = jd.get("raw_text", "").strip()
                if text:
                    documents.append(Document(
                        page_content=text,
                        metadata={
                            "type": "job_description",
                            "job_id": jd.get("id"),
                            "title": jd.get("title", "Unknown Title")
                        }
                    ))
        except Exception as e:
            logger.warning(f"Failed to fetch job descriptions for FAISS index: {e}")
            
        # 3. Split into 500-character chunks with 50-character overlap
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)
        
        embeddings = get_embeddings()
        
        if not chunks:
            logger.warning("No document chunks found to index. Creating empty placeholder vector store.")
            placeholder = Document(
                page_content="Placeholder document for empty vector store.", 
                metadata={"type": "placeholder"}
            )
            db = FAISS.from_documents([placeholder], embeddings)
        else:
            logger.info(f"Indexing {len(chunks)} text chunks in FAISS...")
            db = FAISS.from_documents(chunks, embeddings)
            
        # Save index locally for persistence
        os.makedirs(INDEX_PATH, exist_ok=True)
        db.save_local(INDEX_PATH)
        logger.info(f"Successfully persisted FAISS index at: {INDEX_PATH}")
        
        _vector_store = db
        return db
    finally:
        _lock.release()


def ask(question: str, candidate_id: str = None) -> Dict[str, Any]:
    """
    Retrieves top relevant chunks from FAISS and queries Llama 3.1
    to answer recruitment and CV questions.
    """
    db = get_vector_store()
    retrieved_docs = []
    
    # Retrieve top 3 relevant chunks, safely applying filtering if candidate_id is specified
    try:
        if candidate_id:
            # Query candidate specific chunks with score
            cv_results = db.similarity_search_with_score(
                question, 
                k=3, 
                filter={"type": "candidate", "candidate_id": candidate_id}
            )
            # Query JD chunks with score
            jd_results = db.similarity_search_with_score(
                question, 
                k=3, 
                filter={"type": "job_description"}
            )
            # Combine and sort by score ascending (lower L2 distance = more relevant)
            combined = cv_results + jd_results
            combined.sort(key=lambda x: x[1])
            retrieved_docs = [doc for doc, _ in combined[:3]]
        else:
            retrieved_docs = db.similarity_search(question, k=3)
    except Exception as e:
        logger.warning(f"Filtered vector search failed: {e}. Falling back to manual metadata sorting.")
        all_results = db.similarity_search_with_score(question, k=20)
        if candidate_id:
            filtered = []
            for doc, score in all_results:
                m = doc.metadata
                if m.get("type") == "job_description" or (m.get("type") == "candidate" and m.get("candidate_id") == candidate_id):
                    filtered.append((doc, score))
            filtered.sort(key=lambda x: x[1])
            retrieved_docs = [doc for doc, _ in filtered[:3]]
        else:
            retrieved_docs = [doc for doc, _ in all_results[:3]]
            
    # Build context string and accumulate source references
    context_parts = []
    sources = []
    
    for doc in retrieved_docs:
        context_parts.append(doc.page_content)
        m = doc.metadata
        if m.get("type") == "candidate":
            sources.append(f"Candidate CV Chunk (File: {m.get('file_name')})")
        elif m.get("type") == "job_description":
            sources.append(f"Job Description Chunk (Title: {m.get('title')})")
        elif m.get("type") == "placeholder":
            sources.append("System Placeholder")
        else:
            sources.append("General Reference")
            
    context_str = "\n---\n".join(context_parts)
    
    system_prompt = (
        "You are a recruitment assistant. Answer questions about CVs and job descriptions "
        "using only the provided context. Be concise."
    )
    
    user_prompt = f"Context:\n{context_str}\n\nQuestion: {question}"
    
    try:
        answer = generate(prompt=user_prompt, system=system_prompt, temperature=0.3)
    except Exception as e:
        logger.error(f"Failed to generate answer from Ollama: {e}", exc_info=True)
        answer = "I'm sorry, I could not generate an answer due to an internal LLM error."
        
    return {
        "answer": answer.strip(),
        "sources": sorted(list(set(sources))),
        "candidate_id": candidate_id
    }


# Automatically trigger vector store loading/building in a background thread on module load (On Startup)
def _init_vector_store_background():
    try:
        get_vector_store()
    except Exception as e:
        logger.error(f"Error building/loading vector store in background: {e}")

threading.Thread(target=_init_vector_store_background, daemon=True).start()
