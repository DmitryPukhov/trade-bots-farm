import datetime
import json
import logging
import os
from datetime import timezone

from confluent_kafka import Producer

from connector_stream_htx_metrics import ConnectorStreamHtxMetrics


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

    async def on_message(self, topic, raw_message):
        try:
            now = datetime.datetime.now(timezone.utc)
            message_ts = raw_message["tick"]["ts"] if "ts" in raw_message[
                "tick"] else raw_message["ts"]
            message_dt = datetime.datetime.fromtimestamp(message_ts / 1000, tz=timezone.utc)
            raw_message["datetime"]  = str(message_dt)

            # Produce message to kafka
            prefix = "raw.htx."
            if not topic.startswith(prefix): topic = prefix + topic
            #logging.debug(f"Raw message: {raw_message}")
            self._producer.produce(topic, json.dumps(raw_message))
            self._producer.flush()

            # Set metrics
            ConnectorStreamHtxMetrics.message_processed.labels(topic=topic).inc(1)

            # Time lag metric
            lag_sec = (now - message_dt).total_seconds()
            ConnectorStreamHtxMetrics.time_lag_sec.labels(topic=topic).set(lag_sec)
        except Exception as e:
            logging.error(f"Error producing message to kafka topic: {topic}")
            raise e