import logging
import os
import json


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


def save_json_data(data: dict, filename: str) -> None:
    """Save dictionary data as JSON file"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logging.info(f"✓ Saved JSON data to: {filename}")


def consumer_config(url: str, port: int, group_id: str):
    config_dict= {
        "bootstrap.servers": f"{url}:{port}",
        "group.id": group_id,
        "auto.offset.reset": "latest",
        "enable.auto.commit": False
    }
    return config_dict


def producer_config(url: str, port: int, acks: int):
    config_dict = {
        "bootstrap.servers": f"{url}:{port}",
        "acks": acks
    }
    return config_dict 


def delivery_report(err, msg):
    if err :
        logging.error(f"Delivery Failed: {err}")
        return
    logging.info(f"Delivered message to {msg.topic()} [{msg.partition()}]")


