# Speech-to-Text (STT) Service

A high-performance microservice for converting podcast audio into text transcriptions using Vosk speech recognition engine. Built with gRPC for efficient streaming and designed for integration into the Podcast Recommendation Platform.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Docker Deployment](#docker-deployment)
  - [Local Development](#local-development)
  - [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Audio Format Requirements](#audio-format-requirements)
- [Project Structure](#project-structure)
- [Performance Considerations](#performance-considerations)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This Speech-to-Text service provides real-time and batch audio transcription capabilities specifically optimized for podcast content. The service uses the Vosk offline speech recognition engine, ensuring privacy and eliminating external API dependencies.

The service exposes both gRPC and REST interfaces, supporting streaming transcription for real-time applications and batch processing for high-volume scenarios.

---

## Features

- **Offline Speech Recognition**: Uses Vosk for local, privacy-preserving transcription
- **High-Performance gRPC API**: Streaming support for real-time transcription
- **Optimized for Podcasts**: Configured for spoken word content with 16kHz mono audio
- **Docker Support**: Fully containerized for easy deployment and scaling
- **Word-Level Timestamps**: Optional detailed timing information for each word
- **Confidence Scores**: Per-word and overall transcription confidence metrics
- **Batch Processing**: Support for processing multiple files efficiently
- **Language Support**: Extensible model system supporting multiple languages

---

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ gRPC/REST
       ▼
┌─────────────────┐
│  STT Service    │
│  (Docker)       │
│  ├─ gRPC Server │
│  ├─ Vosk Engine │
│  └─ Model       │
└─────────────────┘
```

The service receives audio streams via gRPC, processes them using the Vosk speech recognition model, and returns transcribed text with metadata including confidence scores and optional word timestamps.

---

## Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows with Docker
- **RAM**: Minimum 4GB (8GB recommended for large models)
- **CPU**: Multi-core processor recommended
- **Storage**: 2GB for base model, more for larger models

### Software Dependencies
- Docker 20.10+
- Docker Compose 1.29+
- Python 3.11+ (for local development)
- FFmpeg (for audio preprocessing)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Podcast-Recommendation-Engine/Speach-to-text-STT.git
cd Speach-to-text-STT
```

### 2. Download Vosk Model

Download a Vosk model from [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models):

**Recommended for English podcasts:**
- `vosk-model-en-us-0.22` (1.8GB) - Best accuracy
- `vosk-model-small-en-us-0.15` (40MB) - Faster, less accurate

```bash
# Example: Download and extract model
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip -d model/
```

### 3. Configure Environment

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Server Configuration
GRPC_PORT=50052
MODEL_PATH=/opt/vosk-model-en

# Audio Processing
SAMPLE_RATE=16000
CHANNELS=1
CHUNK_SIZE=4000

# Performance
MAX_WORKERS=4
ENABLE_WORD_TIMESTAMPS=true
```

---

## Configuration

### Audio Format Requirements

For optimal transcription accuracy, audio files should be:

- **Sample Rate**: 16000 Hz (16 kHz)
- **Channels**: 1 (mono)
- **Format**: WAV with PCM encoding
- **Bit Depth**: 16-bit

### Converting Audio Files

Use the provided audio converter:

```python
from util.audio_converter import convert_to_wav

# Convert MP3 to optimized WAV
wav_file = convert_to_wav('podcast.mp3')
```

Or use FFmpeg directly:

```bash
ffmpeg -i input.mp3 -ar 16000 -ac 1 -acodec pcm_s16le output.wav
```

---

## Usage

### Docker Deployment

**Build and start the service:**

```bash
docker-compose up --build
```

The service will be available at:
- gRPC: `localhost:50052`

**Stop the service:**

```bash
docker-compose down
```

### Local Development

**Install dependencies:**

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Start the server:**

```bash
python -m src.server.server
```

### API Endpoints

#### gRPC Streaming Transcription

```python
from src.client.streaming_client import StreamingTranscriptionClient

client = StreamingTranscriptionClient('localhost:50052')
result = client.transcribe_file('audio/podcast.wav')

print(f"Transcript: {result.text}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Duration: {result.audio_duration:.2f}s")
```

---

## Testing

### Run Test Scripts

**Test with existing audio file:**

```bash
python test/test_and_save.py
```

**Batch transcription:**

```bash
python test/batch_transcribe.py
```

**Check audio format:**

```bash
ffprobe audio/your-file.wav
```

Expected output:
```
Stream #0:0: Audio: pcm_s16le, 16000 Hz, 1 channels, s16, 256 kb/s
```

### Performance Benchmarks

Example results for a 30-minute podcast (Elon Musk episode):

```
Audio Duration: 2031.61 seconds (33.86 minutes)
Processing Time: 155.48 seconds
Speed: 13.06x realtime
Confidence: 89.61%
Word Count: 6,119 words
File Size: ~60 MB (16kHz mono)
```

---

## Audio Format Requirements

### Why 16kHz Mono?

1. **Model Training**: Vosk models are trained on 16kHz audio
2. **Speech Frequency Range**: Human speech is 80Hz-8kHz, fully captured at 16kHz
3. **File Size**: 75% smaller than 44.1kHz stereo
4. **Processing Speed**: Faster transcription with lower sample rates
5. **Accuracy**: Better results with format matching training data

### Format Comparison

| Format | Sample Rate | Channels | File Size (1hr) | Use Case |
|--------|-------------|----------|-----------------|----------|
| **Podcast Optimized** | 16 kHz | Mono | ~115 MB | Speech-to-Text |
| CD Quality | 44.1 kHz | Stereo | ~605 MB | Music |
| Phone Quality | 8 kHz | Mono | ~58 MB | Telephony |

---

## Project Structure

```
Speach-to-text-STT/
├── audio/                      # Audio files for processing
├── model/                      # Vosk speech recognition model
│   ├── am/                     # Acoustic model
│   ├── conf/                   # Configuration files
│   ├── graph/                  # Language model graph
│   └── ivector/                # i-vector extractor
├── proto/                      # Protocol Buffer definitions
│   └── podcast_transcriber.proto
├── src/
│   ├── client/                 # gRPC client implementation
│   │   └── streaming_client.py
│   ├── generated/              # Generated gRPC code
│   │   ├── podcast_transcriber_pb2.py
│   │   └── podcast_transcriber_pb2_grpc.py
│   ├── server/                 # gRPC server implementation
│   │   ├── server.py
│   │   └── servicer.py
│   └── config.py               # Configuration management
├── test/                       # Test scripts
│   ├── test_and_save.py       # Single file transcription
│   └── batch_transcribe.py    # Batch processing
├── transcriptions/             # Output directory for transcripts
├── util/                       # Utility functions
│   └── audio_converter.py     # Audio format conversion
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Docker image definition
├── pyproject.toml              # Python project configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## Performance Considerations

### Optimization Tips

1. **Use Appropriate Model Size**:
   - Small models (40MB): 5-10x realtime, lower accuracy
   - Medium models (1.8GB): 10-15x realtime, high accuracy
   - Large models (2.3GB+): 5-8x realtime, best accuracy

2. **Audio Preprocessing**:
   - Always convert to 16kHz mono before transcription
   - Remove silence and normalize audio levels if needed

3. **Resource Allocation**:
   - Allocate at least 2GB RAM per concurrent transcription
   - Use multi-core CPUs for parallel processing

4. **Streaming vs Batch**:
   - Streaming: Lower latency, real-time results
   - Batch: Higher throughput, resource-efficient

### Scaling

For high-volume deployments:

```yaml
# docker-compose.yml
services:
  stt-service:
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

---

## Troubleshooting

### Common Issues

**Issue: Gibberish transcription output**
- **Cause**: Incorrect audio format (44.1kHz stereo)
- **Solution**: Convert audio to 16kHz mono

**Issue: Low confidence scores**
- **Cause**: Background noise, music, poor audio quality
- **Solution**: Use audio preprocessing, better source material

**Issue: Slow processing**
- **Cause**: Large model, insufficient resources
- **Solution**: Use smaller model or increase CPU allocation

**Issue: Out of memory errors**
- **Cause**: Model too large for available RAM
- **Solution**: Increase RAM or use smaller model

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Create a Pull Request

---

## License

This project is licensed under the MIT License. See LICENSE file for details.

---

## Acknowledgments

- [Vosk](https://alphacephei.com/vosk/) - Open-source speech recognition toolkit
- [gRPC](https://grpc.io/) - High-performance RPC framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework for APIs

---
