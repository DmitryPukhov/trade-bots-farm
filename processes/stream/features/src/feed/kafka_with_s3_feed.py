import asyncio

import numpy as np
import pandas as pd

from feed.kafka_feed import KafkaFeed
from feed.s3_feed import S3Feed


class KafkaWithS3Feed:
    def __init__(self, feature_name: str, new_data_event: asyncio.Event):
        self.data = pd.DataFrame()
        self._feature_name = feature_name
        self._candles_buf = pd.DataFrame()
        self._level2_buf = pd.DataFrame()
        self._merge_tolerance = pd.Timedelta(seconds=59)  # Fixed typo
        self._level2_queue = asyncio.Queue()
        self._candles_queue = asyncio.Queue()
        self.new_data_event = new_data_event

    async def on_level2(self, msg):
        # Convert message to DataFrame row with datetime index
        df = pd.DataFrame([msg])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True, drop=False)

        # Use pd.concat instead of append
        self._level2_buf = pd.concat([self._level2_buf, df])

    async def on_candle(self, msg):
        # Similar handling for candles
        df = pd.DataFrame([msg])
        df['close_time'] = pd.to_datetime(df['close_time'])
        df.set_index('close_time', inplace=True, drop=False)
        self._candles_buf = pd.concat([self._candles_buf, df])

    async def flush_buffers(self):
        """
        If data in buffer is ready, put it to main merged dataframe. In good case each buffer contains one record per minute
        In case of time lags, consider pandas buffers with many messages
        """

        merged_df = pd.merge_asof(left=self._candles_buf, right=self._level2_buf, left_index=True, right_index=True,
                                  tolerance=self._merge_tolerance, direction="nearest")
        merged_df = merged_df.dropna()

        if not merged_df.empty:
            # Clean level2 buffer
            level2_matched_mask = self._level2_buf.index.isin(merged_df["datetime"])
            self._level2_buf = self._level2_buf[~level2_matched_mask]

            # For candles
            candles_matched_mask = self._candles_buf.index.isin(merged_df["close_time"])
            self._candles_buf = self._candles_buf[~candles_matched_mask]

            # Now we can clean close_time and set index and datetime to the latest value
            merged_df["datetime"] =  merged_df[["datetime", "close_time"]].max(axis=1)
            merged_df.set_index("datetime", inplace=True, drop=False)

            # Append the merged data to the main dataframe
            self.data = pd.concat([df for df in [self.data, merged_df] if not df.empty])

            self.new_data_event.set()

    async def processing_loop(self):
        """ Get new messages from stream, add to buffers, flush buffers to main dataframe"""
        while True:
            # Read buffers
            if not self._level2_queue.empty():
                self._level2_buf.append(await self._level2_queue.get())
            if not self._candles_queue.empty():
                self._candles_buf.append(await self._candles_queue.get())

            # Process new data if it comes
            if not (self._level2_buf.empty and self._candles_buf.empty):
                await self.flush_buffers()
            else:
                await asyncio.sleep(1)

    async def run_async(self):
        """ Initial read s3 history then listen kafka for new data and append to dataframe"""

        # Connect to kafka
        kafka_feed = KafkaFeed(level2_queue=self._level2_queue, candles_queue=self._candles_queue)
        await kafka_feed.run()

        # Initial read s3 history
        s3_feed = S3Feed(self._feature_name, merge_tolerance=self._merge_tolerance)
        self.data = await s3_feed.read_history()
