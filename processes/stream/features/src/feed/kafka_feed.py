import asyncio
import logging
import os

from aiokafka import AIOKafkaConsumer


class KafkaFeed:
    def __init__(self, candles_queue: asyncio.Queue, level2_queue: asyncio.Queue):
        self.level2_topic = os.environ["KAFKA_TOPIC_LEVEL2"]
        self.candles_topic = os.environ["KAFKA_TOPIC_CANDLES"]
        self.features_topic = os.environ["KAFKA_TOPIC_FEATURES"]
        self.ticker = os.environ["TICKER"]
        self.bootstrap_servers = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
        self.kafka_offset = os.environ.get("KAFKA_OFFSET", "latest")
        self._queues = {self.level2_topic: level2_queue, self.candles_topic: candles_queue}

    async def create_consumer(self) -> AIOKafkaConsumer:
        group_id = f"{self.ticker}_{self.__class__.__name__}"
        topics = [self.candles_topic, self.level2_topic]
        consumer = AIOKafkaConsumer(*topics,
                                    bootstrap_servers=self.bootstrap_servers,
                                    auto_offset_reset=self.kafka_offset,
                                    group_id=group_id,
                                    enable_auto_commit=True)
        logging.info(
            f"Created consumer: bootstrap_servers={self.bootstrap_servers}, group_id={group_id}, kafka_offset={self.kafka_offset}, topics={topics}")
        return consumer

    async def seek_offset(self, consumer):
        """ For dev only method"""
        if self.kafka_offset == 'latest':
            return

        # Wait for assignment
        while not consumer.assignment():
            await asyncio.sleep(0.1)
        # Force seek to beginning
        for tp in consumer.assignment():
            if self.kafka_offset == 'earliest':
                await consumer.seek_to_beginning(tp)
            else:
                consumer.seek(tp, int(self.kafka_offset))
        print(f"Offsets forcefully reset to {self.kafka_offset}")

    async def run(self):
        logging.info(
            f"Starting {self.__class__.__name__}, listen to {[self.level2_topic, self.candles_topic]}, transform, produce to {self.features_topic}")

        consumer = await self.create_consumer()
        await consumer.start()
        await self.seek_offset(consumer)

        try:
            async for msg in consumer:
                self._queues[msg.topic].put_nowait(msg)
        finally:
            # Will leave consumer group; perform autocommit if enabled.
            await consumer.stop()
