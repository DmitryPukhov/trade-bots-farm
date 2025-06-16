import asyncio
import json
import logging
import os

import pandas as pd
from aiokafka import AIOKafkaConsumer

from common_tools import CommonTools
from multi_indi_features_calc import MultiIndiFeaturesCalc
from features_metrics import FeaturesMetrics
from feed.kafka_with_s3_feed import KafkaWithS3Feed


class FeaturesApp:
    """ Main class"""

    def __init__(self):
        """ Configure producer and consumer """
        CommonTools.init_logging()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.app_name = os.environ["APP_NAME"]
        self.features_topic = os.getenv("KAFKA_TOPIC_FEATURES")
        self.ticker = os.environ["TICKER"]
        self._bootstrap_servers = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
        self._kafka_offset = os.environ.get("KAFKA_OFFSET", "latest")
        self._last_produced_datetime = None
        self._feed = None
        self._stop_event = asyncio.Event()

        self._features_calc = MultiIndiFeaturesCalc(metrics_labels={"topic": self.features_topic})

    async def get_last_produced_datetime(self) -> pd.Timestamp:
        """
        Go to Kafka topic for last previously produced feature and get datetime from there
        Method to run initially
        """
    
        self._logger.info(f"Getting last produced datetime for {self.features_topic}")
        group_id = f"{self.__class__.__name__}"
    
        consumer = AIOKafkaConsumer(  # *self.features_topic,
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
    
    async def processing_loop(self):
        while not self._stop_event.is_set():
            await self._feed.new_data_event.wait()
            self._feed.new_data_event.clear()
            input_df = self._feed.data.copy()
            features_df = await self._features_calc.calc(input_df)


    async def run_async(self):
        # Create feed which reads history then listens to new data in kafka
        new_data_event = asyncio.Event()
        stop_event = asyncio.Event()
        self._last_produced_datetime = await self.get_last_produced_datetime()
        self._feed = KafkaWithS3Feed(self.app_name, new_data_event=new_data_event, stop_event=stop_event)
        await asyncio.gather(self.processing_loop(),
                             self._feed.run_async(),
                             FeaturesMetrics.push_to_gateway_periodical())

    def run(self):
        asyncio.run(self.run_async())


if __name__ == '__main__':
    FeaturesApp().run()
