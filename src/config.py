import os
from dotenv import load_dotenv
load_dotenv()

MODEL_PATH= "models/faster-distil-whisper-small.en"
URL= os.getenv('STT_KAFKA_URL', 'kafka')
PORT= int(os.getenv('STT_KAFKA_PORT', 9092))
GROUP_ID= os.getenv('STT_KAFKA_GROUP_ID', 'Nato')
TOPIC_AUDIO= os.getenv('STT_KAFKA_TOPIC_IN', 'podcast_audio')
TOPIC_LLM= os.getenv('STT_KAFKA_TOPIC_OUT', "podcast_transcription")
ACKS = int(os.getenv('STT_KAFKA_ACKS', 1))

# Audio data needs preprocessing before going into the GPU: 
# Loading files from disk
# Resampling audio
# Splitting into chunks
# Voice activity detection (VAD)
CPU_NUM= 6 

NUM_WORKERS= 2
LANGUAGE= "en"
BEAM_SIZE= 3
BATCH_SIZE= 2
CHUNK_LENGTH= 30
LOG_PROCESS= False
VAD_FILTER= True
MIN_SILENCE_DURATION= 500
DEVICE = "cuda"
COMPUTE_TYPE= "int8"
