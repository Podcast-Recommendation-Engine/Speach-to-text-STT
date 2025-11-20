import os


def extract_content(segments) -> list:
    text= []
    for segment in segments:
        text.append(segment)
    return text

def save_data(segments: list, filename: str, path: str)  -> str:
    os.makedirs(path, exist_ok= True)
    full_path= os.path.join(path, filename)
    full_episode= " ".join(segments)
    with open(filename, "w") as file:
        file.write(full_episode)

    return full_path