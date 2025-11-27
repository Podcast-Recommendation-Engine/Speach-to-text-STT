import logging
import os
import time

from faster_whisper import BatchedInferencePipeline, WhisperModel
from config import BATCH_SIZE, BEAM_SIZE, CHUNK_LENGTH, COMPUTE_TYPE, CPU_NUM, DEVICE, LANGUAGE, MIN_SILENCE_DURATION, MODEL_PATH, NUM_WORKERS, TOPIC_LLM, VAD_FILTER
from utils import extract_content, save_data, save_json_data




def init_model():
    """Initialize Whisper model with GPU or CPU"""
    logging.info(f"Loading model on {DEVICE} with compute type {COMPUTE_TYPE}")
    model = WhisperModel(
        model_size_or_path=MODEL_PATH,
        device=DEVICE,
        num_workers=NUM_WORKERS,
        cpu_threads=CPU_NUM,
        compute_type=COMPUTE_TYPE
    )
    return model


def model_start(model, audio_path):
    """Run transcription using BatchedInferencePipeline"""
    batched_model = BatchedInferencePipeline(model=model)
    segments, info = batched_model.transcribe(
        audio_path,
        language=LANGUAGE,
        task="transcribe",
        log_progress=True,
        beam_size=BEAM_SIZE,
        vad_filter=VAD_FILTER,
        vad_parameters=dict(min_silence_duration_ms=MIN_SILENCE_DURATION),
        chunk_length=CHUNK_LENGTH,
        batch_size=BATCH_SIZE,
        without_timestamps=True,
    )
    return segments, info


def process_audio(audio_path, model):
    """Transcribe a single audio file and save transcript"""
    try:
        segments, info = model_start(model=model, audio_path=audio_path)
        segments_list_content = extract_content(segments=segments)

        # Extract file name without extension
        filename_with_ext = os.path.basename(audio_path)
        filename = os.path.splitext(filename_with_ext)[0]

        # Saving the data is for debugging purposes, i should make sure each data generated
        # is persisted in my local storage

        full_transcript = save_data(
            segments=segments_list_content,
            filename=f"data/silver/transcripts/{filename}.txt"
        )
        logging.info(f"✓ Completed: {audio_path}")

        return full_transcript

    except Exception as e:
        logging.error(f"✗ Error processing {audio_path}: {e}")

def trancribe(msg, model):
    logging.info(f" Received: {msg.get('title')}")
    logging.info(f" Processing audio: {msg.get('full_path')}")
    
    # Process audio and get transcription
    transcription = process_audio(msg.get('full_path'), model)
    
    if transcription:
        logging.info(f" Transcription completed for ID: {msg.get('id')}")
        
        # Enrich transcription with metadata
        result = {
            "id": msg.get('id'),
            "title": msg.get('title'),
            "audio_url": msg.get('audio_url'),
            "authors": msg.get('authors'),
            "year": msg.get('year'),
            "month": msg.get('month'),
            "day": msg.get('day'),
            "itunes_duration": msg.get('itunes_duration'),
            "transcription": transcription,
            "full_path": msg.get('full_path')
        }
        
        logging.info(f" Sending enriched transcription to {TOPIC_LLM}")
        filename = f"data/silver/episode/{result.get('title')}.json"
        save_json_data(result, filename)
        return result
    else:
        logging.warning(f" No transcription returned for ID: {msg.get('id')}")
        return None