import asyncio

from common_tools import CommonTools
from features_calc import FeaturesCalc
from features_metrics import FeaturesMetrics
from feed.kafka_with_s3_feed import KafkaWithS3Feed


class MultiIndiFeaturesApp:
    """ Main class"""

    def __init__(self):
        """ Configure producer and consumer """
        CommonTools.init_logging()

    @staticmethod
    async def run_async():
        # Create feed which reads history then listens to new data in kafka
        new_data_event = asyncio.Event()
        stop_event = asyncio.Event()
        kafka_with_s3_feed = KafkaWithS3Feed("multi_indi_features", new_data_event=new_data_event, stop_event=stop_event)
        features = FeaturesCalc(kafka_with_s3_feed, stop_event)
        await asyncio.gather(features.run_async(),
                             kafka_with_s3_feed.run_async(),
                             FeaturesMetrics.push_to_gateway_periodical())

    def run(self):
        asyncio.run(self.run_async())


if __name__ == '__main__':
    MultiIndiFeaturesApp().run()
