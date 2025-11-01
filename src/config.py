import os
from dataclasses import dataclass
from pathlib import Path
from tokenize import Double
from typing import Optional


@dataclass
class ServerConfig:
    """Server configuration settings."""
    host: str = '0.0.0.0'
    port: int = 50052
    max_workers: int = 4
    max_message_length: int = 2147483647  # 2GB - Max gRPC message size (2^31 - 1)
    
    @classmethod
    def from_env(cls) -> 'ServerConfig':
        return cls(
            host=os.getenv('PODCAST_TRANSCRIBER_HOST', cls.host),
            port=int(os.getenv('PODCAST_TRANSCRIBER_PORT', cls.port)),
            max_workers=int(os.getenv('PODCAST_TRANSCRIBER_MAX_WORKERS', cls.max_workers)),
        )


@dataclass
class TranscriptionConfig:
    """Transcription configuration settings."""
    model_path: str = '/opt/vosk-model-en/model'
    default_sample_rate: int = 16000
    default_channels: int = 1
    chunk_size: int = 4000
    wav_header_size: int = 44
    
    @classmethod
    def from_env(cls) -> 'TranscriptionConfig':
        return cls(
            model_path=os.getenv('VOSK_MODEL_PATH', cls.model_path),
        )


@dataclass
class LogConfig:
    """Logging configuration."""
    level: str = 'INFO'
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def from_env(cls) -> 'LogConfig':
        return cls(
            level=os.getenv('PODCAST_TRANSCRIBER_LOG_LEVEL', cls.level).upper(),
        )


class Config:
    """Configuration class for the STT service."""
    
    # Model configuration
    VOSK_MODEL_PATH = os.getenv(
        'VOSK_MODEL_PATH',
        str(Path(__file__).parent.parent / 'model' / 'model')
    )
    
    # Server configuration
    HOST = os.getenv('PODCAST_TRANSCRIBER_HOST', '0.0.0.0')
    PORT = int(os.getenv('PODCAST_TRANSCRIBER_PORT', '50052'))
    MAX_WORKERS = int(os.getenv('PODCAST_TRANSCRIBER_MAX_WORKERS', '4'))
    
    # Logging configuration
    LOG_LEVEL = os.getenv('PODCAST_TRANSCRIBER_LOG_LEVEL', 'INFO')
    
    # gRPC configuration - Maximum safe value for gRPC (2GB)
    MAX_MESSAGE_LENGTH = int(os.getenv('GRPC_MAX_MESSAGE_LENGTH', 2147483647))  # 2GB (2^31 - 1)
    
    # Audio configuration defaults
    DEFAULT_SAMPLE_RATE = 16000
    DEFAULT_CHANNELS = 1
    DEFAULT_LANGUAGE = "en"
    
    @classmethod
    def validate(cls):
        """Validate configuration settings."""
        if not os.path.exists(cls.VOSK_MODEL_PATH):
            raise ValueError(f"Model path does not exist: {cls.VOSK_MODEL_PATH}")
        
        if cls.PORT < 1024 or cls.PORT > 65535:
            raise ValueError(f"Invalid port number: {cls.PORT}")
        
        if cls.MAX_WORKERS < 1:
            raise ValueError(f"Invalid MAX_WORKERS: {cls.MAX_WORKERS}")
        
        return True


# Singleton instance
config = Config()
