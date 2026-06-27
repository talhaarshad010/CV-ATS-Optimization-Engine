import sys
import os
import logging
from app.services.rag_pipeline import refresh_index, ask

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_rag_pipeline():
    logger.info("Starting RAG Pipeline test...")
    
    # 1. Test Refreshing / Rebuilding FAISS Index
    logger.info("Building FAISS vector index...")
    db = refresh_index()
    
    # Ensure index files were created
    index_dir = "/Users/muhammadtalhaarshad/Downloads/cv-platform/ml/models/faiss_index"
    assert os.path.exists(os.path.join(index_dir, "index.faiss"))
    assert os.path.exists(os.path.join(index_dir, "index.pkl"))
    logger.info("✔ FAISS index files created successfully!")
    
    # 2. Test Ask function
    question = "Who is Muhammad Talha Arshad and what are his top backend skills?"
    logger.info(f"Asking RAG: '{question}'")
    
    # Run the query
    result = ask(question)
    
    logger.info("RAG Answer Response:")
    logger.info(result["answer"])
    logger.info(f"Sources: {result['sources']}")
    
    assert "answer" in result
    assert "sources" in result
    assert len(result["sources"]) > 0
    
    logger.info("✔ RAG Pipeline unit tests passed successfully!")

if __name__ == "__main__":
    test_rag_pipeline()
