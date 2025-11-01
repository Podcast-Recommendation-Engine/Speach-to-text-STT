"""gRPC server startup and lifecycle management."""
import grpc
from concurrent import futures
import logging
import sys
import os

from src.config import Config
from src.server.servicer import PodcastTranscriberServicer
from src.generated import podcast_transcriber_pb2_grpc


def serve():
    """Start the gRPC server."""
    
    # Load configuration
    config = Config()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Print startup banner
    logging.info("=" * 60)
    logging.info("Podcast Transcriber gRPC Server")
    logging.info("=" * 60)
    logging.info(f"Model path: {config.VOSK_MODEL_PATH}")
    logging.info(f"Server address: {config.HOST}:{config.PORT}")
    logging.info(f"Max workers: {config.MAX_WORKERS}")
    logging.info(f"Log level: {config.LOG_LEVEL}")
    
    # Verify model exists
    if not os.path.exists(config.VOSK_MODEL_PATH):
        logging.error(f"Model path does not exist: {config.VOSK_MODEL_PATH}")
        sys.exit(1)
    
    # Create gRPC server
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=config.MAX_WORKERS),
        options=[
            ('grpc.max_send_message_length', config.MAX_MESSAGE_LENGTH),
            ('grpc.max_receive_message_length', config.MAX_MESSAGE_LENGTH),
        ]
    )
    
    # Add servicer
    podcast_transcriber_pb2_grpc.add_PodcastTranscriberServicer_to_server(
        PodcastTranscriberServicer(config.VOSK_MODEL_PATH),
        server
    )
    
    # Bind to port
    server_address = f"{config.HOST}:{config.PORT}"
    server.add_insecure_port(server_address)
    
    # Start server
    logging.info(f"Starting Podcast Transcriber on {server_address}...")
    server.start()
    logging.info("Server is ready to accept connections")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logging.info("Shutting down server...")
        server.stop(0)


if __name__ == "__main__":
    serve()
