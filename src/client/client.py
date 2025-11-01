"""Example gRPC client for testing the transcription service."""
import grpc
import logging
from typing import Iterator

from src.generated import podcast_transcriber_pb2
from src.generated import podcast_transcriber_pb2_grpc


class TranscriptionClient:
    """Client for the PodcastTranscriber gRPC service."""
    
    def __init__(self, server_address: str = 'localhost:50052'):
        
        self.server_address = server_address
        self.channel = grpc.insecure_channel(server_address)
        self.stub = podcast_transcriber_pb2_grpc.PodcastTranscriberStub(self.channel)
        logging.info(f"Connected to server at {server_address}")
    
    def transcribe_file_streaming(
        self,
        audio_path: str,
        sample_rate: int = 16000,
        channels: int = 1,
        enable_word_timestamps: bool = False
    ) -> Iterator[podcast_transcriber_pb2.TranscribeProgressResponse]:
       
        # Read audio file
        logging.info(f"Reading audio file: {audio_path}")
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        
        logging.info(f"Audio file size: {len(audio_data)} bytes")
        
        # Create request
        request = podcast_transcriber_pb2.TranscribeFileRequest(
            audio_data=audio_data,
            sample_rate=sample_rate,
            channels=channels,
            enable_word_timestamps=enable_word_timestamps
        )
        
        # Stream results
        logging.info("Starting transcription...")
        for progress in self.stub.TranscribeFileStreaming(request):
            yield progress
    
    def close(self):
        """Close the client connection."""
        logging.info("Closing connection")
        self.channel.close()


def main():
    """Example usage of the transcription client."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Example audio file path - update this to your actual file
    audio_file = "examples/sample_audio.wav"
    
    client = TranscriptionClient('localhost:50052')
    
    try:
        print(f"Transcribing audio file: {audio_file}")
        print("-" * 60)
        
        for progress in client.transcribe_file_streaming(
            audio_file,
            enable_word_timestamps=True
        ):
            # Show progress updates
            print(f"Progress: {progress.progress_percentage}% - {progress.status}")
            
            # Show partial transcript
            if progress.partial_transcript:
                print(f"Partial: {progress.partial_transcript[:100]}...")
            
            # Show final result
            if progress.progress_percentage == 100:
                result = progress.final_result
                print("\n" + "=" * 60)
                print("✅ Transcription Complete!")
                print("=" * 60)
                print(f"Transcript: {result.transcript}")
                print(f"Confidence: {result.confidence:.2%}")
                print(f"Duration: {result.duration_seconds:.2f}s")
                print(f"Processing Time: {result.processing_time_seconds:.2f}s")
                
                if result.words:
                    print(f"\nWord Count: {len(result.words)}")
                    print("\nFirst 10 words with timestamps:")
                    for word in result.words[:10]:
                        print(f"  [{word.start_time:.2f}s - {word.end_time:.2f}s] "
                              f"{word.word} (conf: {word.confidence:.2f})")
                
    except FileNotFoundError:
        print(f"❌ Error: Audio file not found: {audio_file}")
        print("Please create an 'examples' folder and add a 'sample_audio.wav' file")
    except grpc.RpcError as e:
        print(f"❌ gRPC Error: {e.code()} - {e.details()}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
