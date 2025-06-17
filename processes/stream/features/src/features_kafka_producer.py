import json
import logging
import os

import pandas as pd
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

from common_tools import CommonTools


class FeaturesKafkaProducer:
    """ Produce features to Kafka. Contains some tools for features in kafka"""

    def __init__(self):
        """ Configure producer and consumer """
        CommonTools.init_logging()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.features_topic = os.getenv("KAFKA_TOPIC_FEATURES")
        self._bootstrap_servers = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
        self._last_produced_datetime = None
        self._producer = None

    async def _ensure_producer(self):
        if not self._producer:
            self._logger.debug("Creating producer for bootstrap servers: {self._bootstrap_servers}")
            self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap_servers)
            await self._producer.start()


    async def get_last_produced_datetime(self) -> pd.Timestamp:

        if self._last_produced_datetime:
            # We already have the last produced datetime
            return self._last_produced_datetime
        # Else go to kafka and get the last produced datetime

        self._logger.info(f"Getting last produced datetime for {self.features_topic}")
        last_time = pd.Timestamp.min

        # Create temporarily consumer
        group_id = f"{self.__class__.__name__}"
        consumer = AIOKafkaConsumer(  self.features_topic,
                                      bootstrap_servers=self._bootstrap_servers,
                                      group_id=group_id)
        await consumer.start()

        # If topic does not exist, return min time
        topics = await consumer.topics()
        if self.features_topic not in topics:
            self._logger.info(f"Topic {self.features_topic} does not exist. Returning min time.")
            return self._last_produced_datetime

        try:
            # Get the latest offset for each partition
            partitions = consumer.assignment()
            end_offsets = await consumer.end_offsets(partitions)
            for partition, offset in end_offsets.items():
                if offset > 0:  # If partition has messages
                    consumer.seek(partition, offset - 1)  # Seek to last message
                    kafka_msg = await consumer.getone()
                    #msg = json.loads(kafka_msg.value.decode('utf-8'))
                    msg_time = pd.Timestamp(kafka_msg.timestamp, unit='ms')
                    last_time = max(last_time, msg_time)
        except Exception as e:
            self._logger.error(f"Error getting last produced datetime: {str(e)}")
        finally:
            await consumer.stop()
            if last_time > pd.Timestamp.min:
                self._last_produced_datetime = last_time
            self._logger.info(f"Last produced datetime for {self.features_topic} is {self._last_produced_datetime}")
            # Final value across all partitions
            return self._last_produced_datetime


    async def produce_features(self, features_df: pd.DataFrame):
        """ Producer features dataframe to Kafka"""
        self._logger.debug(f"Producing {len(features_df)} features to {self.features_topic}")
        if features_df.empty:
            return

        await self._ensure_producer()

        try:
            # Convert each row to dict and send to Kafka
            for _, row in features_df.iterrows():
                message = row.to_dict()
                self._logger.debug(f"Sending to kafka topic {self.features_topic} message: {message}")
                message_encoded = json.dumps(message).encode('utf-8')
                await self._producer.send(self.features_topic, value=message_encoded, timestamp_ms=row.datetime.timestamp())
                await self._producer.flush()
            await self._producer.flush()
            self._last_produced_datetime = features_df.index.max()
        except Exception as e:
            self._logger.error(f"Error producing messages: {str(e)}")
