import json
import logging
import os

from confluent_kafka import Producer


class KafkaRawProducer:
    """ Producer raw messages to kafka"""
    def __init__(self):
        conf = {
            "bootstrap.servers": os.environ.get("KAFKA_BOOTSTRAP_SERVERS","localhost:9092"),
            "queue.buffering.max.ms": int(os.environ.get("KAFKA_AUTO_FLUSH_SEC","1"))*1000,  # Auto-flush every 1000ms (1 second)
            "batch.num.messages": 100,       # OR: Flush after 100 messages
        }
        logging.info(f"Confluent Kafka Producer parameters: {conf}")
        self._producer = Producer(conf)

    def on_message(self, topic, raw_message):
        prefix = "raw."
        if not topic.startswith(prefix): topic = prefix + topic
        #logging.debug(f"Raw message: {raw_message}")
        self._producer.produce(topic, json.dumps(raw_message))
        #self._producer.flush()
