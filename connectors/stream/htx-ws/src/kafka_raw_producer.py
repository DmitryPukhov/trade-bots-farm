import datetime
import json
import logging
import os
from datetime import timezone

from confluent_kafka import Producer

from Metrics import Metrics


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
        self._metrics = Metrics()


    def on_message(self, topic, raw_message):
        now = datetime.datetime.now(timezone.utc)

        # Produce message to kafka
        prefix = "raw.htx."
        if not topic.startswith(prefix): topic = prefix + topic
        #logging.debug(f"Raw message: {raw_message}")
        self._producer.produce(topic, json.dumps(raw_message))

        # Set metrics
        self._metrics.MESSAGES_PROCESSED.labels(topic=topic).inc(1)

        # Time lag metric
        message_ts = raw_message["tick"]["ts"] if "ts" in raw_message[
            "tick"] else raw_message["ts"]
        message_dt = datetime.datetime.fromtimestamp(message_ts / 1000, tz=timezone.utc)
        lag_sec = (now - message_dt).total_seconds()
        self._metrics.TIME_LAG_SEC.labels(topic=topic).set(lag_sec)