import asyncio
import logging

import pandas as pd

from feed.kafka_with_s3_feed import KafkaWithS3Feed


class FeaturesCalc:
    def __init__(self, feed: KafkaWithS3Feed, stop_event: asyncio.Event):
        self._feed = feed
        self._stop_event = stop_event

    async def calc(self, df: pd.DataFrame):
        logging.info(f"Calculating features. Last time: {df.index.max()}")
        return pd.DataFrame()

    async def run_async(self):
        while not self._stop_event.is_set():
            await self._feed.new_data_event.wait()
            self._feed.new_data_event.clear()
            df = self._feed.data.copy()
            features = await self.calc(df)
