import json
import logging
import time
from service import init_model, model_start, process_audio
from utils import config, extract_content, save_data
from confluent_kafka import Consumer
import threading
from queue import Queue
from config import TOPIC_AUDIO, URL, PORT, GROUP_ID


logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.Formatter.converter = time.gmtime

def main():
    config_value = config(url=URL, port=PORT, group_id=GROUP_ID)
    consumer = Consumer(config_value)

    consumer.subscribe([TOPIC_AUDIO])

    logging.info(f"Consumer is subcribing to {TOPIC_AUDIO} topic")
    model = init_model()

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                logging.error(f"Got error {msg.error()}")
                continue

            raw = msg.value().decode('utf-8')
            data= json.loads(raw)
            episode_path= data['full_path']

            # Process in background thread
            thread = threading.Thread(target=process_audio, args=(episode_path, model))
            thread.daemon = True
            thread.start()

            logging.info(f"Started processing: {episode_path}")
            
            # Commit the offset to prevent reprocessing
            consumer.commit(msg)

    except KeyboardInterrupt:
        logging.info("\n  Stopping consumer gracefully")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()