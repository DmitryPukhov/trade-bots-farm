import logging

import pandas as pd

from feed.kafka_with_s3_feed import KafkaWithS3Feed


class FeaturesCalc:
    def __init__(self, feed: KafkaWithS3Feed):
        self._feed = feed

    async def calc(self, df: pd.DataFrame):
        logging.info(f"Calculating features. Input shape: {df.shape}")
        return pd.DataFrame()

    async def run_async(self):
        await self._feed.new_data_event.wait()
        df = self._feed.data.copy()
        features = await self.calc(df)
