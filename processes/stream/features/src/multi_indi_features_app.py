import asyncio

from common_tools import CommonTools
from processes.stream.features.src.feed.kafka_with_s3_feed import KafkaWithS3Feed
from processes.stream.features.src.feed.s3_feed import S3Feed


class MultiIndiFeaturesApp:
    """ Main class"""

    def __init__(self):
        """ Configure producer and consumer """
        CommonTools.init_logging()

    @staticmethod
    async def run_async():
        # Create feed which reads history then listens to new data in kafka
        new_data_event = asyncio.Event()
        kafka_with_s3_feed = KafkaWithS3Feed("multi_indi_features", new_data_event = new_data_event)
        await kafka_with_s3_feed.run_async()

    def run(self):
        asyncio.run(self.run_async())


if __name__ == '__main__':
    MultiIndiFeaturesApp().run()
