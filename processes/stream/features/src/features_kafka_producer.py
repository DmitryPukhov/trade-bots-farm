import json
import logging
import os

import pandas as pd
from aiokafka import AIOKafkaConsumer

from common_tools import CommonTools


class FeaturesKafkaProducer:
    """ Produce features to Kafka. Contains some tools for features in kafka"""

    def __init__(self):
        """ Configure producer and consumer """
        CommonTools.init_logging()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.features_topic = os.getenv("KAFKA_TOPIC_FEATURES")
        self._bootstrap_servers = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
        self._kafka_offset = os.environ.get("KAFKA_OFFSET", "latest")
        self._last_produced_datetime = None

    @property
    async def last_produced_datetime(self):
        if self._last_produced_datetime is None:
            self._last_produced_datetime = await self._get_last_produced_datetime()
        return self._last_produced_datetime

    async def _get_last_produced_datetime(self) -> pd.Timestamp:
        """
        Go to Kafka topic for last previously produced feature and get datetime from there
        Method to run initially
        """

        self._logger.info(f"Getting last produced datetime for {self.features_topic}")
        group_id = f"{self.__class__.__name__}"

        consumer = AIOKafkaConsumer(  self.features_topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=group_id)
        await consumer.start()

        # Value to return
        last_time = pd.Timestamp.min

        # If topic does not exist, return min time
        topics = await consumer.topics()
        if self.features_topic not in topics:
            self._logger.info(f"Topic {self.features_topic} does not exist. Returning min time.")
            return last_time

        try:
            # Get the latest offset for each partition
            partitions = consumer.assignment()
            end_offsets = await consumer.end_offsets(partitions)
            for partition, offset in end_offsets.items():
                if offset > 0:  # If partition has messages
                    await consumer.seek(partition, offset - 1)  # Seek to last message
                    msg_encoded = await consumer.getone()
                    msg = json.loads(msg_encoded.value.decode('utf-8'))
                    msg_time = pd.Timestamp(msg["datetime"])
                    last_time = max(last_time, msg_time)
        finally:
            await consumer.stop()
            self._logger.info(f"Last produced datetime for {self.features_topic} is {last_time}")
            return last_time

    async def produce_features(self, features_df: pd.DataFrame):
        print(f"Producing {len(features_df)} features to {self.features_topic}")
        self._logger.debug(f"Producing {len(features_df)} features to {self.features_topic}")
        if features_df.empty:
            return


        # Update last produced datetime
        self._last_produced_datetime = features_df.index.max()