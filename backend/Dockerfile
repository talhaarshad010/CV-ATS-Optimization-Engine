FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies required for FAISS, PyMuPDF, and EasyOCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgomp1 \
    libglib2.0-0 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file first to utilize Docker build layer caching
COPY requirements.txt .

# Upgrade pip and install package dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Download required SpaCy NLP model and NLTK corpora
RUN python -m spacy download en_core_web_sm && \
    python -m nltk.downloader stopwords punkt

# Copy the rest of the application files
COPY . .

# Expose API port
EXPOSE 8000

# Start FastAPI using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
