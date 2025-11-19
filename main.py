from faster_whisper import WhisperModel, BatchedInferencePipeline
import os

audio_path = "data/audio/#485 – David Kirtley Nuclear Fusion, Plasma Physics, and the Future of Energy.mp3"

# Getting the number of avaliable cpu cores
num_cors= os.cpu_count() or 1

recommended_number= int(0.75 * num_cors)

# Load the model
model = WhisperModel(
    model_size_or_path="distil-small.en", 
    device="cpu",
    num_workers=3,
    cpu_threads= recommended_number,
    compute_type="int8"
    )

batched_model = BatchedInferencePipeline(model= model)

# Transcribe the audio
segments, info = batched_model.transcribe(
    audio_path,
    language="en",
    task="transcribe",
    log_progress=True,
    beam_size=3,    
    vad_filter=True,
    vad_parameters=dict(
        min_silence_duration_ms=500,
    ),
    chunk_length=30,  
    batch_size=2,     
    without_timestamps=True,
)

out_dir = "transcripts"
os.makedirs(out_dir, exist_ok=True)
base = os.path.splitext(os.path.basename(audio_path))[0]
out_path = os.path.join(out_dir, f"{base}.txt")


with open(out_path, "w", encoding="utf-8") as f:
    for segment in segments:
        f.write(f"{segment.text}\n")
    f.write("\n")


print(f"Saved transcript to: {out_path}")
