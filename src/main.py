import os
import logging
from config import GROUP_ID, PORT, TOPIC_AUDIO, TOPIC_LLM, URL
from service import init_model, trancribe
from quixstreams import Application
from utils import setup_logging


def main(url: str, port: int, consumer_group: str, topic_in: str, topic_out: str):
    # Initialize model once at startup
    logging.info("Initializing Whisper model...")
    model = init_model()
    logging.info("Model initialized successfully")
    
    app= Application(
        broker_address= f"{url}:{port}",
        auto_offset_reset= "earliest",
        consumer_group= consumer_group,
        consumer_extra_config={
            "max.poll.interval.ms": 1800000,   # 30 minutes
            "session.timeout.ms": 45000,       # optional: 45 sec instead of 10
        }
    )
    input_topic= app.topic(topic_in)
    output_topic= app.topic(topic_out)

    sdf= app.dataframe(input_topic)
    sdf= sdf.apply(lambda msg: trancribe(msg, model))
    sdf= sdf.to_topic(output_topic)
    app.run()

if __name__ == "__main__":
    setup_logging()
    main(URL, PORT, GROUP_ID, TOPIC_AUDIO, TOPIC_LLM)
