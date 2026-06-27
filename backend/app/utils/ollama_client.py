import time
import logging
import requests
import ollama

logger = logging.getLogger(__name__)

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "llama3.1:8b-instruct-q4_K_M"


def is_ollama_running() -> bool:
    """Pings http://localhost:11434 and returns True if Ollama is active."""
    try:
        response = requests.get(OLLAMA_HOST, timeout=2.0)
        return response.status_code == 200
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False


def generate(prompt: str, system: str = "", temperature: float = 0.3) -> str:
    """
    Sends a prompt to Ollama using Llama 3.1 8B Instruct.
    Raises RuntimeError if Ollama is offline or unavailable.
    """
    if not is_ollama_running():
        raise RuntimeError("Ollama is not running. Start it with: ollama serve")

    start_time = time.time()
    logger.info(f"Sending request to Ollama ({MODEL_NAME})...")

    try:
        response = ollama.generate(
            model=MODEL_NAME,
            prompt=prompt,
            system=system,
            options={
                "temperature": temperature
            }
        )
        duration = time.time() - start_time
        logger.info(f"Ollama generation completed in {duration:.2f} seconds.")
        return response.get("response", "")
    except Exception as e:
        logger.error(f"Ollama generation failed: {e}", exc_info=True)
        raise RuntimeError(f"Ollama generation error: {e}")
