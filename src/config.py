MODEL_PATH= "models/faster-distil-whisper-small.en"


# I test the process with 75% of my cpu core, I test on cpu intel i5, 12 cores,
# but i will set a nb of process this time
CPU_NUM= 6
NUM_WORKERS= 3
DEVICE= "cpu"
COMPUTE_TYPE= "int8"
LANGUAGE= "en"
BEAM_SIZE= 3
BATCH_SIZE= 2
CHUNK_LENGTH= 30
LOG_PROCESS= False
VAD_FILTER= True
MIN_SILENCE_DURATION= 500