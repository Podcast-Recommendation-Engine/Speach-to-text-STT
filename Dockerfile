# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for faster-whisper
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy project configuration
COPY pyproject.toml .

# Install Python dependencies from pyproject.toml
RUN pip install --no-cache-dir .

# Copy application source code
COPY src/ ./src/

# Copy models directory
COPY models/ ./models/

# Create necessary directories
RUN mkdir -p data/audio data/raw data/transcripts

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose volume mount points for data
VOLUME ["/app/data/audio", "/app/data/transcripts"]

# Run the application
CMD ["python", "src/main.py"]
