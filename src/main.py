import json
import logging
import time
from service import init_model, process_and_queue
from utils import consumer_config, producer_config, save_json_data  # ✅ Add save_json_data
from confluent_kafka import Consumer, Producer
import threading
from queue import Queue
from config import ACKS, TOPIC_AUDIO, TOPIC_LLM, URL, PORT, GROUP_ID



def main():
    consumer_config_value = consumer_config(url=URL, port=PORT, group_id=GROUP_ID)
    consumer = Consumer(consumer_config_value)
    consumer.subscribe([TOPIC_AUDIO])

    producer_config_value= producer_config(url=URL, port=PORT, acks= ACKS)
    producer= Producer(producer_config_value)
    
    # Create a queue to collect results
    result_queue = Queue()
    
    # Define the output topic name
    TOPIC_TRANSCRIPTION = TOPIC_LLM  

    logging.info(f"Consumer is subcribing to {TOPIC_AUDIO} topic")
    model = init_model()
    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                # Check for completed results and produce to output topic
                while not result_queue.empty():
                    result_data = result_queue.get()
                    
                    if result_data['status'] == 'success':
                        output_message = json.dumps(result_data['data']).encode('utf-8')
                        
                        producer.produce(
                            TOPIC_TRANSCRIPTION,
                            value=output_message,
                            callback=lambda err, msg: logging.error(f"Delivery failed: {err}") if err else logging.info(f"Message delivered to {msg.topic()}")
                        )
                        producer.poll(0)
                        
                        logging.info(f"Processing complete for: {result_data['data'].get('title', 'Unknown')}")
                        
                        # ✅ Save enriched data using utility function
                        title = result_data['data'].get('title', 'unknown_title')
                       
                        save_json_data(
                            data=result_data['data'],
                            filename=f"data/silver/episode/{title}.json"
                        )
                    else:
                        logging.error(f"Failed to process: {result_data.get('error')}")
                
                continue
                
            if msg.error():
                logging.error(f"Got error {msg.error()}")
                continue

            raw = msg.value().decode('utf-8')
            data= json.loads(raw)
            episode_path= data['full_path']

            # Process in background thread
            thread = threading.Thread(
                target=process_and_queue,
                args=(episode_path, data, model, result_queue)
            )
            thread.daemon = True
            thread.start()

            logging.info(f"Started processing: {episode_path}")
            
            # Commit the offset to prevent reprocessing
            consumer.commit(msg)

    except KeyboardInterrupt:
        logging.info("\n  Stopping consumer gracefully")
    finally:
        producer.flush()  # Ensure all messages are sent
        consumer.close()


if __name__ == "__main__":
    logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
    logging.Formatter.converter = time.gmtime

    main()