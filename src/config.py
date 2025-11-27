import os
from dotenv import load_dotenv
load_dotenv()


MODEL_PATH= "models/faster-distil-whisper-small.en"
URL= os.getenv('URL', 'docker')
PORT= int(os.getenv('PORT', 9092))
GROUP_ID= os.getenv('GROUP_ID', 'Nato')
TOPIC_AUDIO= os.getenv('TOPIC_TO_READ', 'podcast_audio')
ACKS = int(os.getenv('ACKS', 1))
TOPIC_LLM= os.getenv('TOPIC_TO_WRITE', "podcast_transcription")




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
DEVICE = "cpu"
COMPUTE_TYPE= "int8"
