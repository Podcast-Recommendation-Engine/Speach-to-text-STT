from service import init_model, model_start
from utils import config, extract_content, save_data
from confluent_kafka import Consumer
import threading
from queue import Queue


def process_audio(audio_path, model):
    """Process audio in background thread"""
    try:
        segments = model_start(model=model, audio_path=audio_path)
        segments_list_content = extract_content(segments=segments)
        save_data(segments=segments_list_content, filename="test.txt")
        print(f"✓ Completed: {audio_path}")
    except Exception as e:
        print(f"✗ Error processing {audio_path}: {e}")


def main():
    url = 'localhost'
    port = 29092
    group_id = "Nato"
    config_value = config(url=url, port=port, group_id=group_id)
    consumer = Consumer(config_value)
    consumer.subscribe(["podcast_audio"])
    print("Consumer is subcribing to audio podcast topic")
    model = init_model()

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(f"Got error {msg.error()}")
                continue

            value = msg.value().decode('utf-8')

            # Process in background thread
            thread = threading.Thread(target=process_audio, args=(value, model))
            thread.daemon = True
            thread.start()

            print(f"⚙ Started processing: {value}")

    except KeyboardInterrupt:
        print("\n  Stopping consumer gracefully")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()