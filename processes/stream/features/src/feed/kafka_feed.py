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

    async def offsets_report_msg(self, prefix: str):
        partitions = self._consumer.assignment()

        # Get all offset information
        current = {tp: await self._consumer.position(tp) for tp in partitions}
        committed = {tp: await self._consumer.committed(tp) for tp in partitions}
        end = await self._consumer.end_offsets(partitions)

        # Build output message
        message = [f"\n{prefix} offset information:"]

        for tp in sorted(partitions, key=lambda x: (x.topic, x.partition)):
            message.append(
                f"  Topic {tp.topic}, partition {tp.partition}:\n"
                f"    Current position: {current[tp]}\n"
                f"    Last committed: {committed[tp] or 'None'}\n"
                f"    Last available: {end[tp]}"
            )

        message.append(f"\nLogged at: {datetime.now().isoformat()}")
        return "\n".join(message)

    async def set_offsets_to_time(self, target_time: datetime):
        """Set kafka topic offsets to target time in past"""
        logging.info(await self.offsets_report_msg(f"Before setting offsets to {target_time}"))

        for topic in self._topics:
            logging.info(f"Setting offsets to {target_time} for topic {topic}")
            partitions = [TopicPartition(topic, p) for p in self._consumer.partitions_for_topic(topic)]
            target_time_millis = int(target_time.timestamp() * 1000)

            # Get offsets for target time
            offsets = await self._consumer.offsets_for_times({tp: target_time_millis for tp in partitions})

            for tp in partitions:
                if offsets[tp] is None or offsets[tp].offset == -1:
                    # No messages at/before target time - go to beginning
                    beginning = await self._consumer.beginning_offsets([tp])
                    target_offset = beginning[tp]
                    logging.warning(f"No messages before {target_time} in {tp}, using beginning offset {target_offset}")
                else:
                    target_offset = offsets[tp].offset

                # Commit and seek to the target offset
                await self._consumer.commit({tp: OffsetAndMetadata(target_offset, "")})
                self._consumer.seek(tp, target_offset)

                # Verify the new position
                current_position = await self._consumer.position(tp)
                if current_position != target_offset:
                    logging.error(f"Failed to set position for {tp}! Expected {target_offset}, got {current_position}")

        logging.info(await self.offsets_report_msg(f"After setting offsets to {target_time}"))

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
