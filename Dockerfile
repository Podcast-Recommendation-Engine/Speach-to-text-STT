FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install uv (lightweight package manager)
RUN pip install --no-cache-dir uv

# Copy project metadata files
COPY pyproject.toml uv.lock ./

# Install dependencies exactly as locked
RUN uv sync --frozen --no-dev

# Copy proto files and source code
COPY proto/ ./proto/
COPY src/ ./src/

# Generate gRPC code from proto file
RUN uv run python -m grpc_tools.protoc \
    -I./proto \
    --python_out=./src/generated \
    --grpc_python_out=./src/generated \
    ./proto/podcast_transcriber.proto && \
    sed -i 's/^import podcast_transcriber_pb2/from . import podcast_transcriber_pb2/' \
    ./src/generated/podcast_transcriber_pb2_grpc.py

# Expose gRPC port
EXPOSE 50052

# Run the server using uv
CMD ["uv", "run", "python", "-m", "src.server.server"]
