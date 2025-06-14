import asyncio
import json
import logging
import os
from datetime import datetime

from aiokafka import AIOKafkaConsumer, TopicPartition, OffsetAndMetadata


class KafkaFeed:
    def __init__(self, candles_queue: asyncio.Queue, level2_queue: asyncio.Queue):
        self.level2_topic = os.environ["KAFKA_TOPIC_LEVEL2"]
        self.candles_topic = os.environ["KAFKA_TOPIC_CANDLES"]
        self._topics = [self.level2_topic, self.candles_topic]

        self.features_topic = os.environ["KAFKA_TOPIC_FEATURES"]
        self.ticker = os.environ["TICKER"]
        self.bootstrap_servers = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
        self.kafka_offset = os.environ.get("KAFKA_OFFSET", "latest")
        self._queues = {self.level2_topic: level2_queue, self.candles_topic: candles_queue}
        self._consumer = None

    async def create_consumer(self) -> AIOKafkaConsumer:
        group_id = f"{self.ticker}_{self.__class__.__name__}"

        consumer = AIOKafkaConsumer(*self._topics,
                                    bootstrap_servers=self.bootstrap_servers,
                                    auto_offset_reset=self.kafka_offset,
                                    group_id=group_id,
                                    enable_auto_commit=True)
        logging.info(
            f"Created consumer: bootstrap_servers={self.bootstrap_servers}, group_id={group_id}, kafka_offset={self.kafka_offset}, topics={self._topics}")
        return consumer

    async def set_offsets_to_time(self, target_time: datetime):
        """ Set kafka topic offsets to target time in past. We need to close the gap between the history end and kafka start"""

        for topic in self._topics:
            logging.info(f"Set offsets to {target_time} for topic {topic}")

            # Get partitions and calculate target time
            partitions = [TopicPartition(topic, p) for p in self._consumer.partitions_for_topic(topic)]

            # target_time = int((datetime.utcnow() - timedelta(minutes=10)).timestamp() * 1000)
            target_time_millis = int(target_time.timestamp() * 1000)
            # Get offsets for target time
            offsets = await self._consumer.offsets_for_times({tp: target_time_millis for tp in partitions})

            # Commit the offsets for the group
            for tp in partitions:
                if offsets[tp]:
                    await self._consumer.commit({tp: OffsetAndMetadata(offsets[tp].offset, "")})
                else:
                    beginning = await self._consumer.beginning_offsets([tp])
                    await self._consumer.commit({tp: OffsetAndMetadata(beginning[tp], "")})

    async def run(self, start_time: datetime):
        """ Listen to the kafka messages starting from given time in the past """

        logging.info(f"Starting {self.__class__.__name__}, listen to {[self.level2_topic, self.candles_topic]}, "
                     f"transform, produce to {self.features_topic}")

        # Consumer initialization
        self._consumer = await self.create_consumer()
        await self._consumer.start()
        await self.set_offsets_to_time(start_time)

        try:
            async for msg in self._consumer:
                try:
                    # Decode message and put it to queue
                    data = json.loads(msg.value.decode('utf-8'))
                    self._queues[msg.topic].put_nowait(data)
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to decode JSON: {e}")
                except UnicodeDecodeError as e:
                    logging.error(f"Failed to decode message bytes: {e}")
        finally:
            # Will leave consumer group; perform autocommit if enabled.
            await self._consumer.stop()
