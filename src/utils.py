import os


def extract_content(segments) -> list:
    text= []
    for segment in segments:
        text.append(segment.text)
    return text

def save_data(segments: list, filename)  -> str:

    full_episode= " ".join(segments)
    with open(filename, "w") as file:
        file.write(full_episode)

    return full_episode


def config(url: str, port: int, group_id: str):
    config_dict= {
        "bootstrap.servers": f"{url}:{port}",
        "group.id": group_id,
        "auto.offset.reset": "latest",
        "enable.auto.commit": False
    }
    return config_dict
