from service import init_model, model_start
from utils import extract_content, save_data
from config import AUDIO_PATH

def main():
    model = init_model()
    segments= model_start(model=model)
    segments_list_content= extract_content(segments=segments)
    full_episode= save_data(segments= segments_list_content, filename="test.txt", path=AUDIO_PATH)


if __name__=="__name__":
    main()