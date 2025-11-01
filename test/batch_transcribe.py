"""Batch transcribe all audio files in a directory."""
import sys
from pathlib import Path
from datetime import datetime
import json
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.client.streaming_client import StreamingTranscriptionClient


def batch_transcribe(
    audio_dir: Path = Path("audio"),
    output_dir: Path = Path("transcriptions"),
    server_address: str = "localhost:50052",
    sample_rate: int = 16000,
    channels: int = 1,
    enable_word_timestamps: bool = False  # Disabled by default for speed
):
    """Transcribe all WAV files in a directory."""
    
    print("=" * 70)
    print("🎙️  Batch Transcription")
    print("=" * 70)
    print()
    
    # Find audio files
    wav_files = sorted(list(audio_dir.glob("*.wav")) + list(audio_dir.glob("*.WAV")))
    
    if not wav_files:
        print(f"❌ No WAV files found in: {audio_dir}")
        return
    
    print(f"📁 Found {len(wav_files)} WAV file(s):\n")
    total_size = 0
    for i, wav_file in enumerate(wav_files, 1):
        size_mb = wav_file.stat().st_size / (1024 * 1024)
        total_size += wav_file.stat().st_size
        print(f"   {i}. {wav_file.name} ({size_mb:.2f} MB)")
    
    print(f"\n📊 Total size: {total_size / (1024 * 1024):.2f} MB")
    print(f"📂 Output directory: {output_dir.absolute()}")
    print(f"🔌 Server: {server_address}")
    print(f"⏱️  Word timestamps: {'Enabled' if enable_word_timestamps else 'Disabled (faster)'}")
    print()
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Confirmation
    try:
        confirm = input(f"🚀 Start batch transcription of {len(wav_files)} files? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Cancelled.")
            return
    except KeyboardInterrupt:
        print("\n❌ Cancelled.")
        return
    
    print("\n" + "=" * 70)
    print("⏳ Processing...")
    print("=" * 70 + "\n")
    
    # Create client
    client = StreamingTranscriptionClient(server_address)
    
    # Process each file
    results = []
    start_time = time.time()
    
    for i, wav_file in enumerate(wav_files, 1):
        print(f"\n{'='*70}")
        print(f"📝 [{i}/{len(wav_files)}] Processing: {wav_file.name}")
        print(f"{'='*70}\n")
        
        file_start = time.time()
        
        try:
            # Connect
            client.connect()
            
            # Transcribe
            responses = client.stub.TranscribeStreamingBidirectional(
                client.audio_chunk_generator(
                    wav_file,
                    sample_rate=sample_rate,
                    channels=channels,
                    enable_word_timestamps=enable_word_timestamps
                )
            )
            
            # Track progress
            last_progress = -1
            final_result = None
            
            for progress in responses:
                if progress.progress_percentage != last_progress:
                    bar_length = 40
                    filled = int(bar_length * progress.progress_percentage / 100)
                    bar = '█' * filled + '░' * (bar_length - filled)
                    print(f"\r⏳ [{bar}] {progress.progress_percentage}%", end='', flush=True)
                    last_progress = progress.progress_percentage
                
                if progress.progress_percentage == 100 and progress.final_result:
                    final_result = progress.final_result
                    break
            
            print()  # New line after progress
            
            if final_result:
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = wav_file.stem
                txt_file = output_dir / f"{base_name}_{timestamp}.txt"
                json_file = output_dir / f"{base_name}_{timestamp}.json"
                
                # Save text
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write(f"File: {wav_file.name}\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Duration: {final_result.duration_seconds:.2f}s\n")
                    f.write(f"Confidence: {final_result.confidence:.2%}\n")
                    f.write("\n" + "-" * 70 + "\n\n")
                    f.write(final_result.transcript)
                
                # Save JSON
                data = {
                    "file": wav_file.name,
                    "timestamp": datetime.now().isoformat(),
                    "duration_seconds": final_result.duration_seconds,
                    "processing_time_seconds": final_result.processing_time_seconds,
                    "confidence": final_result.confidence,
                    "transcript": final_result.transcript,
                    "word_count": len(final_result.words)
                }
                
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                file_time = time.time() - file_start
                
                # Record result
                results.append({
                    "file": wav_file.name,
                    "success": True,
                    "duration": final_result.duration_seconds,
                    "processing_time": final_result.processing_time_seconds,
                    "confidence": final_result.confidence,
                    "output_files": [str(txt_file.name), str(json_file.name)],
                    "time_elapsed": file_time
                })
                
                print(f"✅ Success! Saved to {txt_file.name}")
                print(f"   Duration: {final_result.duration_seconds:.1f}s | "
                      f"Confidence: {final_result.confidence:.1%} | "
                      f"Time: {file_time:.1f}s")
            else:
                results.append({
                    "file": wav_file.name,
                    "success": False,
                    "error": "No result received"
                })
                print(f"❌ Failed: No result received")
                
        except Exception as e:
            results.append({
                "file": wav_file.name,
                "success": False,
                "error": str(e)
            })
            print(f"❌ Error: {e}")
        finally:
            if client.channel:
                client.channel.close()
                client.channel = None
                client.stub = None
    
    # Summary
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r.get("success"))
    
    print("\n" + "=" * 70)
    print("📊 BATCH PROCESSING COMPLETE")
    print("=" * 70)
    print(f"\n✅ Successful: {successful}/{len(wav_files)}")
    print(f"⏱️  Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"📂 Output directory: {output_dir.absolute()}\n")
    
    # Save summary
    summary_file = output_dir / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "batch_date": datetime.now().isoformat(),
            "total_files": len(wav_files),
            "successful": successful,
            "failed": len(wav_files) - successful,
            "total_time_seconds": total_time,
            "results": results
        }, f, indent=2)
    
    print(f"📄 Summary saved to: {summary_file.name}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch transcribe audio files")
    parser.add_argument("--audio-dir", default="audio", help="Directory containing audio files")
    parser.add_argument("--output-dir", default="transcriptions", help="Output directory")
    parser.add_argument("--server", default="localhost:50052", help="Server address")
    parser.add_argument("--sample-rate", type=int, default=16000, help="Sample rate")
    parser.add_argument("--channels", type=int, default=1, help="Number of channels")
    parser.add_argument("--with-timestamps", action="store_true", help="Enable word timestamps")
    
    args = parser.parse_args()
    
    batch_transcribe(
        audio_dir=Path(args.audio_dir),
        output_dir=Path(args.output_dir),
        server_address=args.server,
        sample_rate=args.sample_rate,
        channels=args.channels,
        enable_word_timestamps=args.with_timestamps
    )
