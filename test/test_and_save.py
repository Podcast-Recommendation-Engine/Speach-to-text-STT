"""Test script that saves transcription results to a file."""
import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.client.streaming_client import StreamingTranscriptionClient
from src.generated import podcast_transcriber_pb2


class TranscriptionSaver:
    """Client that saves transcription results to files."""
    
    def __init__(self, server_address: str = "localhost:50052", output_dir: str = "transcriptions"):
        self.server_address = server_address
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.client = StreamingTranscriptionClient(server_address)
    
    def transcribe_and_save(
        self,
        audio_path: Path,
        sample_rate: int = 16000,
        channels: int = 1,
        enable_word_timestamps: bool = True
    ):
        """Transcribe audio file and save results."""
        print("=" * 70)
        print("🎙️  STT Service - Transcribe and Save")
        print("=" * 70)
        print()
        print(f"📁 Input: {audio_path.name}")
        print(f"📂 Output dir: {self.output_dir.absolute()}")
        print(f"🔌 Server: {self.server_address}\n")
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = audio_path.stem
        txt_file = self.output_dir / f"{base_name}_{timestamp}.txt"
        json_file = self.output_dir / f"{base_name}_{timestamp}.json"
        
        try:
            # Connect to server
            print(f"🔌 Connecting to {self.server_address}...")
            self.client.connect()
            print("✅ Connected!\n")
            
            # Start transcription
            print("🚀 Starting transcription...\n")
            
            responses = self.client.stub.TranscribeStreamingBidirectional(
                self.client.audio_chunk_generator(
                    audio_path,
                    sample_rate=sample_rate,
                    channels=channels,
                    enable_word_timestamps=enable_word_timestamps
                )
            )
            
            # Track progress
            last_progress = -1
            final_result = None
            
            for progress in responses:
                # Show progress
                if progress.progress_percentage != last_progress:
                    bar_length = 50
                    filled = int(bar_length * progress.progress_percentage / 100)
                    bar = '█' * filled + '░' * (bar_length - filled)
                    print(f"\r⏳ [{bar}] {progress.progress_percentage}% - {progress.status}", end='', flush=True)
                    last_progress = progress.progress_percentage
                
                # Capture final result
                if progress.progress_percentage == 100 and progress.final_result:
                    final_result = progress.final_result
                    break
            
            print("\n\n" + "=" * 70)
            
            if final_result:
                # Save transcript to text file
                print(f"💾 Saving transcript to: {txt_file.name}")
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write("=" * 70 + "\n")
                    f.write(f"Transcription Results\n")
                    f.write("=" * 70 + "\n\n")
                    f.write(f"File: {audio_path.name}\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Duration: {final_result.duration_seconds:.2f} seconds\n")
                    f.write(f"Processing Time: {final_result.processing_time_seconds:.2f} seconds\n")
                    f.write(f"Confidence: {final_result.confidence:.2%}\n")
                    f.write(f"Words: {len(final_result.words)}\n")
                    f.write("\n" + "-" * 70 + "\n")
                    f.write("TRANSCRIPT:\n")
                    f.write("-" * 70 + "\n\n")
                    f.write(final_result.transcript)
                    f.write("\n\n")
                    
                    # Add word timestamps if available
                    if final_result.words and enable_word_timestamps:
                        f.write("\n" + "=" * 70 + "\n")
                        f.write("WORD TIMESTAMPS:\n")
                        f.write("=" * 70 + "\n\n")
                        for i, word in enumerate(final_result.words, 1):
                            f.write(f"{i:5d}. [{word.start_time:8.2f}s - {word.end_time:8.2f}s] "
                                  f"{word.word:20s} (conf: {word.confidence:.2f})\n")
                
                print(f"✅ Text file saved!\n")
                
                # Save detailed JSON
                print(f"💾 Saving detailed JSON to: {json_file.name}")
                data = {
                    "metadata": {
                        "file": audio_path.name,
                        "timestamp": datetime.now().isoformat(),
                        "audio_duration_seconds": final_result.duration_seconds,
                        "processing_time_seconds": final_result.processing_time_seconds,
                        "confidence": final_result.confidence,
                        "word_count": len(final_result.words),
                        "sample_rate": sample_rate,
                        "channels": channels
                    },
                    "transcript": final_result.transcript,
                    "words": [
                        {
                            "word": w.word,
                            "start_time": w.start_time,
                            "end_time": w.end_time,
                            "confidence": w.confidence
                        }
                        for w in final_result.words
                    ] if enable_word_timestamps else []
                }
                
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ JSON file saved!\n")
                
                # Print summary
                print("=" * 70)
                print("📊 SUMMARY")
                print("=" * 70)
                print(f"📝 Transcript preview (first 500 chars):")
                print(f"   {final_result.transcript[:500]}...")
                print()
                print(f"⏱️  Audio Duration: {final_result.duration_seconds:.2f}s")
                print(f"🚀 Processing Time: {final_result.processing_time_seconds:.2f}s")
                print(f"📊 Confidence: {final_result.confidence:.2%}")
                print(f"⚡ Speed: {final_result.duration_seconds / final_result.processing_time_seconds:.2f}x realtime")
                print(f"📝 Word Count: {len(final_result.words)} words")
                print()
                print(f"📁 Output files:")
                print(f"   • {txt_file.absolute()}")
                print(f"   • {json_file.absolute()}")
                print("=" * 70)
                
            else:
                print("❌ No final result received")
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Cancelled by user")
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.client.channel:
                self.client.channel.close()


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Transcribe audio files and save results"
    )
    parser.add_argument(
        "audio_file",
        nargs='?',
        help="Path to audio file (WAV format). If not provided, lists files in audio/ folder."
    )
    parser.add_argument(
        "--server",
        default="localhost:50052",
        help="gRPC server address (default: localhost:50052)"
    )
    parser.add_argument(
        "--output-dir",
        default="transcriptions",
        help="Output directory for transcription files (default: transcriptions/)"
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
        help="Disable word-level timestamps (faster)"
    )
    
    args = parser.parse_args()
    
    # If no file specified, show files in audio/ folder
    if not args.audio_file:
        audio_dir = Path("audio")
        if not audio_dir.exists():
            print("❌ Audio directory not found. Please create 'audio/' folder.")
            return
        
        wav_files = list(audio_dir.glob("*.wav")) + list(audio_dir.glob("*.WAV"))
        if not wav_files:
            print("❌ No WAV files found in audio/ folder.")
            return
        
        print("=" * 70)
        print("🎙️  Available Audio Files")
        print("=" * 70)
        print()
        for i, wav_file in enumerate(wav_files, 1):
            size_mb = wav_file.stat().st_size / (1024 * 1024)
            print(f"   {i}. {wav_file.name} ({size_mb:.2f} MB)")
        print()
        
        try:
            choice = input(f"Select a file (1-{len(wav_files)}): ").strip()
            idx = int(choice) - 1
            if idx < 0 or idx >= len(wav_files):
                print("❌ Invalid choice.")
                return
            audio_file = wav_files[idx]
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Cancelled.")
            return
    else:
        audio_file = Path(args.audio_file)
        if not audio_file.exists():
            print(f"❌ File not found: {audio_file}")
            return
    
    # Create saver and transcribe
    saver = TranscriptionSaver(
        server_address=args.server,
        output_dir=args.output_dir
    )
    
    saver.transcribe_and_save(
        audio_path=audio_file,
        sample_rate=args.sample_rate,
        channels=args.channels,
        enable_word_timestamps=not args.no_timestamps
    )


if __name__ == "__main__":
    main()
