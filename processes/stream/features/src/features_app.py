import asyncio
import logging
import os
from typing import Optional

from common_tools import CommonTools
from features_kafka_producer import FeaturesKafkaProducer
from features_metrics import FeaturesMetrics
from feed.kafka_with_s3_feed import KafkaWithS3Feed
from multi_indi_features_calc import MultiIndiFeaturesCalc


class FeaturesApp:
    """ Main class"""

    def __init__(self):
        """ Configure producer and consumer """
        CommonTools.init_logging()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.app_name = os.environ["APP_NAME"]
        self.features_topic = os.getenv("KAFKA_TOPIC_FEATURES")
        self._feed:Optional[KafkaWithS3Feed] = None
        self._stop_event = asyncio.Event()
        self._kafka_producer: Optional[FeaturesKafkaProducer] = None
        self._features_calc = MultiIndiFeaturesCalc(metrics_labels={"topic": self.features_topic})

    async def processing_loop(self):
        """ Listen kafka input, calculate features and produce to kafka output"""
        while not self._stop_event.is_set():
            # Wait for new data
            await self._feed.new_data_event.wait()
            self._feed.new_data_event.clear()
            input_df = self._feed.data.copy()

            old_datetime = await self._kafka_producer.get_last_produced_datetime()
            # Calculate features
            features_df = await self._features_calc.calc(input_df, old_datetime)
            await asyncio.sleep(0.001)
            # Produce features to kafka
            await self._kafka_producer.produce_features(features_df)

    async def run_async(self):
        # Create feed which reads history then listens to new data in kafka
        new_data_event = asyncio.Event()
        stop_event = asyncio.Event()
        self._kafka_producer = FeaturesKafkaProducer()
        old_datetime = await self._kafka_producer.get_last_produced_datetime()

        self._feed = KafkaWithS3Feed(self.app_name, new_data_event=new_data_event, stop_event=stop_event, old_datetime=old_datetime)

        # Run the processes
        await asyncio.gather(self.processing_loop(),
                             self._feed.run_async(),
                             FeaturesMetrics.push_to_gateway_periodical())

    def run(self):
        asyncio.run(self.run_async())


if __name__ == '__main__':
    FeaturesApp().run()
