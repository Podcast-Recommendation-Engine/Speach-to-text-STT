# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for faster-whisper
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*


COPY pyproject.toml .
COPY src/ ./src/
COPY models/ ./models/

RUN pip install --no-cache-dir . && rm -rf build


# Create necessary directories
RUN mkdir -p data/audio data/raw data/transcripts

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose volume mount points for data
VOLUME ["/app/data/audio", "/app/data/transcripts"]

# Run the application
CMD ["python", "src/main.py"]
