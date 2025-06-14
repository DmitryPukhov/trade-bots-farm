import asyncio

import pandas as pd

from processes.stream.features.src.feed.kafka_feed import KafkaFeed
from processes.stream.features.src.feed.s3_feed import S3Feed


class KafkaWithS3Feed:
    def __init__(self, feature_name: str, new_data_event: asyncio.Event):
        self.data = None
        self._feature_name = feature_name
        self._candles_buf = pd.DataFrame()
        self._level2_buf = pd.DataFrame()
        self._merge_tolerance = pd.Timedelta(miniutes=1)
        self.data = None
        self._level2_queue = asyncio.Queue()
        self._candles_queue = asyncio.Queue()
        self.new_data_event = new_data_event

    async def on_level2(self, msg):
        self._level2_buf.append(msg, ignore_index=True)

    async def on_candle(self, msg):
        self._candles_buf.append(msg, ignore_index=True)

    async def flush_buffers(self):
        """
        If data in buffer is ready, put it to main merged dataframe. In good case each buffer contains one record per minute
        In case of time lags, consider pandas buffers with many messages
        """

        if not self.data:
            # Initial data is not read from s3 yet
            return
        merged_df = pd.merge_asof(left=self._candles_buf, right=self._level2_buf, left_index=True, right_index=True,
                                  tolerance=self._merge_tolerance)

        # Clean the original buffers by removing data that was successfully merged
        if not merged_df.empty:
            merged_timestamps = merged_df.index
            self._candles_buf = self._candles_buf[~self._candles_buf.index.isin(merged_timestamps)]
            self._level2_buf = self._level2_buf[~self._level2_buf.index.isin(merged_timestamps)]

            # Clean the merged DataFrame from NaN values and append to main data
            merged_df = merged_df.dropna()
            self.data = self.data.append(merged_df)

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
