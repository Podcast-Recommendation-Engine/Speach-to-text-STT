

FROM nvidia/cuda:12.2.2-cudnn8-devel-ubuntu22.04 AS builder
ENV DEBIAN_FRONTEND=noninteractive

# Install cuDNN 9 - the repos are already configured in the base image
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv ffmpeg libsndfile1 git \
    libcudnn9-cuda-12 libcudnn9-dev-cuda-12 \
    && pip install --upgrade pip setuptools wheel \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY pyproject.toml .
COPY src ./src

RUN pip install .

FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 python3-pip ffmpeg libsndfile1 \
    libcudnn9-cuda-12 \
    && rm -rf /var/lib/apt/lists/*

# Enable GPU usage inside container
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local /usr/local
COPY src ./src

CMD ["python3", "src/main.py"]
