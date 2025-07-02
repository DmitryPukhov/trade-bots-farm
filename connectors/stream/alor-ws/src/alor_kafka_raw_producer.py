import asyncio
import json
import logging
import os
from datetime import timezone, datetime

from confluent_kafka import Producer

from connector_stream_alor_metrics import ConnectorStreamAlorMetrics


class AlorKafkaRawProducer:
    """ Producer raw messages to kafka"""

    def __init__(self, candles_1min_queue: asyncio.Queue, level2_queue: asyncio.Queue, bid_ask_queue: asyncio.Queue):
        self._logger = logging.getLogger(__class__.__name__)
        conf = {
            "bootstrap.servers": os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            "queue.buffering.max.ms": int(os.environ.get("KAFKA_AUTO_FLUSH_SEC", "1")) * 1000,
            # Auto-flush every 1000ms (1 second)
            "batch.num.messages": 100,  # OR: Flush after 100 messages
        }
        self._logger.info(f"Confluent Kafka Producer parameters: {conf}")
        self._producer = Producer(conf)
        self._topic_prefix = "raw.alor."
        self._ticket = os.environ.get("ALOR_TICKET", "unknown")
        self._candles_queue = candles_1min_queue
        self._level2_queue = level2_queue
        self._bid_ask_queue = bid_ask_queue

    async def create_tasks(self):
        _ = asyncio.create_task(self.listen_queue(queue=self._candles_queue, kind="candles.1min"))
        _ = asyncio.create_task(self.listen_queue(queue=self._level2_queue, kind="level2"))
        _ = asyncio.create_task(self.listen_queue(queue=self._bid_ask_queue, kind="bid_ask"))

    async def listen_queue(self, queue: asyncio.Queue, kind: str):
        """ Redurect"""
        topic = f"{self._topic_prefix}.{self._ticket}.{kind}"
        self._logger.info(f"Queue of {kind} will be written to Kafka topic: {topic}")
        while True:
            message = await queue.get()
            self._logger.debug(f"Received {kind} message: {message}")
            await self._on_message(message, kind)
            ConnectorStreamAlorMetrics.messages_in_queue.labels(topic=topic).set(queue.qsize())


    async def _get_time_field(self, raw_message: dict) -> datetime:
        """
        Extracts a timestamp from raw_message and converts it to a datetime object.
        Returns:
            datetime: The parsed datetime or datetime.min if no timestamp is found.
        """
        data = raw_message.get("data", {})
        #ms: 1703862267800
        #s:    1537529040
        # Check timestamp fields in priority order
        for field in ["tso", "tst", "t"]:
            if field in data:
                # If millis, convert to float seconds
                time_val = float(data[field])
                1751442430
                if time_val > 9999999999:
                    time_val /= 1000.0
                return datetime.fromtimestamp(time_val)

        return datetime.min

    def topic_of(self, kind: str) -> str:
        return f"{self._topic_prefix}{self._ticket}.{kind}"

    async def _on_message(self, raw_message, kind: str):
        try:
            now = datetime.now()
            if isinstance(raw_message, str):
                raw_message = json.loads(raw_message)
            message_dt = await self._get_time_field(raw_message)
            raw_message["datetime"] = str(message_dt)
            topic = self.topic_of(kind)
            self._producer.produce(topic, json.dumps(raw_message))

            # Set metrics
            ConnectorStreamAlorMetrics.message_processed.labels(topic=topic).inc(1)

            # Time lag metric
            lag_sec = (now - message_dt).total_seconds()
            ConnectorStreamAlorMetrics.time_lag_sec.labels(topic=topic).set(lag_sec)

            await asyncio.sleep(0)

        except Exception as e:
            logging.error(f"Error producing {kind} message to kafka")
            raise e
