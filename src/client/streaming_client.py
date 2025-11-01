"""Streaming client for transcribing large audio files (no size limit!)."""
import grpc
import sys
import time
from pathlib import Path
from typing import Iterator

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.generated import podcast_transcriber_pb2
from src.generated import podcast_transcriber_pb2_grpc


class StreamingTranscriptionClient:
    """
    Client that streams large audio files to the server in chunks.
    
    Features:
    - No 2GB file size limit
    - Real-time progress updates
    - Low memory usage
    - Production-ready
    """
    
    # Chunk size: 5MB (balance between network efficiency and responsiveness)
    CHUNK_SIZE = 5 * 1024 * 1024
    
    def __init__(self, server_address: str = "localhost:50052"):
        """
        Initialize streaming client.
        
        Args:
            server_address: gRPC server address (host:port)
        """
        self.server_address = server_address
        self.channel = None
        self.stub = None
    
    def connect(self):
        """Connect to gRPC server (no large message limits needed!)."""
        print(f"🔌 Connecting to {self.server_address}...")
        
        # With streaming, we don't need huge message size limits!
        # Each chunk is only 5MB
        self.channel = grpc.insecure_channel(self.server_address)
        self.stub = podcast_transcriber_pb2_grpc.PodcastTranscriberStub(self.channel)
        
        print("✅ Connected!\n")
    
    def audio_chunk_generator(
        self,
        audio_path: Path,
        sample_rate: int = 16000,
        channels: int = 1,
        enable_word_timestamps: bool = True
    ) -> Iterator[podcast_transcriber_pb2.AudioChunk]:
        """
        Generate audio chunks from file for streaming upload.
        
        Args:
            audio_path: Path to audio file
            sample_rate: Audio sample rate (Hz)
            channels: Number of audio channels
            enable_word_timestamps: Whether to include word timestamps
            
        Yields:
            AudioChunk messages
        """
        file_size = audio_path.stat().st_size
        filename = audio_path.name
        
        print(f"📁 File: {filename}")
        print(f"📊 Size: {file_size:,} bytes ({file_size / (1024**2):.2f} MB)")
        print(f"📦 Chunk size: {self.CHUNK_SIZE:,} bytes ({self.CHUNK_SIZE / (1024**2):.2f} MB)\n")
        
        with open(audio_path, 'rb') as f:
            chunk_number = 0
            bytes_sent = 0
            
            while True:
                # Read chunk
                chunk_data = f.read(self.CHUNK_SIZE)
                if not chunk_data:
                    break
                
                is_first = (chunk_number == 0)
                bytes_sent += len(chunk_data)
                is_last = (bytes_sent >= file_size)
                
                # Create chunk message
                chunk = podcast_transcriber_pb2.AudioChunk(
                    audio_data=chunk_data,
                    chunk_number=chunk_number,
                    is_first_chunk=is_first,
                    is_last_chunk=is_last
                )
                
                # Add metadata in first chunk
                if is_first:
                    chunk.sample_rate = sample_rate
                    chunk.channels = channels
                    chunk.total_size = file_size
                    chunk.filename = filename
                    chunk.enable_word_timestamps = enable_word_timestamps
                
                yield chunk
                
                # Progress feedback
                chunk_number += 1
                progress = int((bytes_sent / file_size) * 100)
                print(f"📤 Uploading... {progress}% ({chunk_number} chunks, {bytes_sent:,} bytes)", end='\r')
                
                if is_last:
                    print(f"\n✅ Upload complete! Sent {chunk_number} chunks\n")
                    break
    
    def transcribe_file(
        self,
        audio_path: str,
        sample_rate: int = 16000,
        channels: int = 1,
        enable_word_timestamps: bool = True
    ):
        """
        Transcribe an audio file using bidirectional streaming.
        
        Args:
            audio_path: Path to audio file
            sample_rate: Audio sample rate (default: 16000 Hz)
            channels: Number of audio channels (default: 1 for mono)
            enable_word_timestamps: Enable word-level timestamps (default: True)
        """
        audio_file = Path(audio_path)
        
        if not audio_file.exists():
            print(f"❌ File not found: {audio_path}")
            return
        
        print("=" * 70)
        print("🎙️  Streaming Transcription Client")
        print("=" * 70)
        print()
        
        try:
            self.connect()
            
            # Start bidirectional streaming
            print("🚀 Starting transcription with streaming upload...\n")
            
            responses = self.stub.TranscribeStreamingBidirectional(
                self.audio_chunk_generator(
                    audio_file,
                    sample_rate=sample_rate,
                    channels=channels,
                    enable_word_timestamps=enable_word_timestamps
                )
            )
            
            # Process progress updates from server
            last_progress = -1
            
            for progress in responses:
                # Show progress bar
                if progress.progress_percentage != last_progress:
                    bar_length = 50
                    filled = int(bar_length * progress.progress_percentage / 100)
                    bar = '█' * filled + '░' * (bar_length - filled)
                    
                    print(f"\r⏳ [{bar}] {progress.progress_percentage}% - {progress.status}", end='', flush=True)
                    last_progress = progress.progress_percentage
                
                # Show partial transcript updates
                if progress.partial_transcript and len(progress.partial_transcript) > 50:
                    preview = progress.partial_transcript[:100] + "..."
                    print(f"\n   💬 {preview}")
                
                # Final result
                if progress.progress_percentage == 100:
                    result = progress.final_result
                    print("\n\n" + "=" * 70)
                    print("✅ TRANSCRIPTION COMPLETE!")
                    print("=" * 70)
                    print(f"\n📝 Transcript:")
                    print(f"{result.transcript}\n")
                    print("-" * 70)
                    print(f"⏱️  Audio Duration: {result.duration_seconds:.2f}s")
                    print(f"🚀 Processing Time: {result.processing_time_seconds:.2f}s")
                    print(f"📊 Confidence: {result.confidence:.2%}")
                    print(f"⚡ Speed: {result.duration_seconds / result.processing_time_seconds:.2f}x realtime")
                    
                    if result.words:
                        print(f"📝 Word Count: {len(result.words)} words")
                        
                        if enable_word_timestamps and len(result.words) > 0:
                            print(f"\n🎯 Sample words with timestamps (first 10):")
                            for i, word in enumerate(result.words[:10], 1):
                                print(f"   {i:2d}. [{word.start_time:6.2f}s - {word.end_time:6.2f}s] "
                                      f"{word.word:15s} (conf: {word.confidence:.2f})")
            
            print("\n" + "=" * 70)
            print("✅ Done!")
            print("=" * 70 + "\n")
            
        except grpc.RpcError as e:
            print(f"\n\n❌ gRPC Error: {e.code()}")
            print(f"   Details: {e.details()}")
            print("\n💡 Make sure the Docker container is running:")
            print("   docker ps | grep podcast-stt-service")
        except KeyboardInterrupt:
            print("\n\n⏹️  Cancelled by user")
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.channel:
                self.channel.close()
                print("\n🔌 Connection closed")


def main():
    """Main function with command-line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Stream large audio files to transcription service (no size limit!)"
    )
    parser.add_argument(
        "audio_file",
        help="Path to audio file (WAV format)"
    )
    parser.add_argument(
        "--server",
        default="localhost:50052",
        help="gRPC server address (default: localhost:50052)"
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="Audio sample rate in Hz (default: 16000)"
    )
    parser.add_argument(
        "--channels",
        type=int,
        default=1,
        help="Number of audio channels (default: 1 for mono)"
    )
    parser.add_argument(
        "--no-timestamps",
        action="store_true",
        help="Disable word-level timestamps"
    )
    
    args = parser.parse_args()
    
    # Create client and transcribe
    client = StreamingTranscriptionClient(server_address=args.server)
    client.transcribe_file(
        audio_path=args.audio_file,
        sample_rate=args.sample_rate,
        channels=args.channels,
        enable_word_timestamps=not args.no_timestamps
    )


if __name__ == "__main__":
    main()
