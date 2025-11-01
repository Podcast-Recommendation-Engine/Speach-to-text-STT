"""Quick test script to test the STT service with your WAV files."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.client.streaming_client import StreamingTranscriptionClient


def main():
    """Test the service with audio files in the audio/ folder."""
    print("=" * 70)
    print("🎙️  STT Service Test Script")
    print("=" * 70)
    print()
    
    # Check for audio files
    audio_dir = Path(__file__).parent / "audio"
    
    if not audio_dir.exists():
        print(f"❌ Audio directory not found: {audio_dir}")
        print("   Please create an 'audio' folder and add WAV files to test.")
        return
    
    # Find WAV files
    wav_files = list(audio_dir.glob("*.wav")) + list(audio_dir.glob("*.WAV"))
    
    if not wav_files:
        print(f"❌ No WAV files found in: {audio_dir}")
        print("   Please add WAV files (16kHz, mono recommended) to the audio/ folder.")
        return
    
    print(f"📁 Found {len(wav_files)} WAV file(s) in audio/:\n")
    for i, wav_file in enumerate(wav_files, 1):
        size_mb = wav_file.stat().st_size / (1024 * 1024)
        print(f"   {i}. {wav_file.name} ({size_mb:.2f} MB)")
    
    print("\n" + "=" * 70)
    
    # Let user choose a file
    if len(wav_files) == 1:
        selected_file = wav_files[0]
        print(f"\n▶️  Testing with: {selected_file.name}\n")
    else:
        try:
            choice = input(f"\nSelect a file (1-{len(wav_files)}) or press Enter for file 1: ").strip()
            if not choice:
                choice = "1"
            idx = int(choice) - 1
            if idx < 0 or idx >= len(wav_files):
                print("❌ Invalid choice. Using first file.")
                idx = 0
            selected_file = wav_files[idx]
            print(f"\n▶️  Testing with: {selected_file.name}\n")
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Cancelled.")
            return
    
    # Create client
    server_address = "localhost:50052"
    print(f"🔌 Server: {server_address}\n")
    
    client = StreamingTranscriptionClient(server_address=server_address)
    
    # Transcribe the file
    try:
        client.transcribe_file(
            audio_path=str(selected_file),
            sample_rate=16000,  # Adjust if your files have different sample rate
            channels=1,         # Adjust if stereo
            enable_word_timestamps=True
        )
    except KeyboardInterrupt:
        print("\n\n⏹️  Cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure Docker container is running:")
        print("      docker-compose up -d")
        print("   2. Check container status:")
        print("      docker ps | findstr podcast-stt-service")
        print("   3. Check container logs:")
        print("      docker logs podcast-stt-service")


if __name__ == "__main__":
    main()
