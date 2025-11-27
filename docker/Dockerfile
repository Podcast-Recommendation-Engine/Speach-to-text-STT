FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*


COPY pyproject.toml .
COPY src/ ./src/
# COPY models/ ./models/

# RUN pip install --no-cache-dir . && rm -rf build
RUN pip install . 


# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "src/main.py"]