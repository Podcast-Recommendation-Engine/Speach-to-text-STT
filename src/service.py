
import logging
import time
from config import *
from faster_whisper import BatchedInferencePipeline, WhisperModel
from utils import extract_content, save_data

logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.Formatter.converter = time.gmtime


def init_model():
    model= WhisperModel(
        model_size_or_path= MODEL_PATH,
        device= DEVICE,
        num_workers= NUM_WORKERS,
        cpu_threads= CPU_NUM,
        compute_type= COMPUTE_TYPE
    )
    return model

def model_start(model, audio_path):
    batched_model = BatchedInferencePipeline(model= model)
    segments, info = batched_model.transcribe(
        audio_path,
        language="en",
        task="transcribe",
        log_progress=True,
        beam_size=3,    
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
        chunk_length=30,  
        batch_size=2,     
        without_timestamps=True,
    )
    return segments, info

def process_audio(audio_path, model):
    try:
        segments, info = model_start(model=model, audio_path=audio_path)
        segments_list_content = extract_content(segments=segments)

        # I need to extract the excact file name without the extention 
        filename_with_extention= audio_path.split("/")[-1]
        filename =filename_with_extention.split(".")[0]
        save_data(segments=segments_list_content, filename=f"data/transcripts/{filename}.txt")
        logging.info(f"✓ Completed: {audio_path} with info {info}")
    except Exception as e:
        logging.error(f"✗ Error processing {audio_path}: {e}")