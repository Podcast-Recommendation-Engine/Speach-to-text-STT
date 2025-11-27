import logging
import os
import json
import time


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




def setup_logging():
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.Formatter.converter = time.gmtime

