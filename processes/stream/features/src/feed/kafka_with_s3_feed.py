import asyncio
import logging

import pandas as pd

from feed.kafka_feed import KafkaFeed
from feed.s3_feed import S3Feed


class KafkaWithS3Feed:
    """ Read history data from s3 then listen kafka for new data"""

    def __init__(self, feature_name: str, new_data_event: asyncio.Event):
        self.data = pd.DataFrame()
        self._feature_name = feature_name
        self._candles_buf = pd.DataFrame()
        self._level2_buf = pd.DataFrame()
        self._merge_tolerance = pd.Timedelta(seconds=59)  # Fixed typo
        self._level2_queue = asyncio.Queue()
        self._candles_queue = asyncio.Queue()
        self.new_data_event = new_data_event
        self._last_candle_time = pd.Timestamp(0)

        # Settings to track gap between s3 and kafka
        self._max_history_datetime = self.data.index.max() if not self.data.empty else pd.Timestamp.min
        self._min_stream_datetime = pd.Timestamp.max
        self._history_stream_max_time_gap = pd.Timedelta(minutes=1)
        self._initial_history_reload_interval = pd.Timedelta(minutes=1)

        self._s3_feed = None

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
            merged_df["datetime"] = merged_df[["datetime", "close_time"]].max(axis=1)
            self._min_stream_datetime = min(self._min_stream_datetime, merged_df["datetime"].min())
            merged_df.set_index("datetime", inplace=True, drop=False)

            # Append the merged data to the main dataframe
            self.data = pd.concat([df for df in [self.data, merged_df] if not df.empty])

            # Notify about new data
            self.new_data_event.set()

    async def processing_loop(self):
        """ Get new messages from stream, add to buffers, flush buffers to main dataframe"""
        while True:
            # Read buffers
            if not self._level2_queue.empty():
                await self.on_level2(await self._level2_queue.get())
            if not self._candles_queue.empty():
                await self.on_candle(await self._candles_queue.get())

            #  Process new data if it comes
            if not (self._level2_buf.empty and self._candles_buf.empty):
                await self.flush_buffers()

            # Check if we have gap between s3 and kafka and try to load absent data from s3
            time_gap = self._min_stream_datetime.tz_localize(
                "UTC").to_pydatetime() - self._max_history_datetime.tz_localize("UTC").to_pydatetime()
            if time_gap > self._history_stream_max_time_gap:
                # Don't go to s3 too often, wait some time
                await asyncio.sleep(self._initial_history_reload_interval.total_seconds())
                logging.info(
                    f"Gap between s3 and kafka is {time_gap} > {self._history_stream_max_time_gap}. "
                    f"Try to load new history from s3")
                await self.read_history()
            else:
                await asyncio.sleep(1)

    async def read_history(self):
        """ Read history from s3 and put it to main dataframe"""

        # Read history from s3
        history_df = await self._s3_feed.read_history(
            start_date=self._max_history_datetime.date(),
            end_date=self._min_stream_datetime.date(),
            modified_after=self._min_stream_datetime if self._min_stream_datetime.date() < pd.Timestamp.max.date() else pd.Timestamp.min)
        if not history_df.empty:
            if not self.data.empty:
                self._max_history_datetime = max(self._max_history_datetime, history_df.index.max())
                history_df = history_df[~history_df.index.isin(self.data.index)]
            self.data = pd.concat([self.data, history_df]).sort_index()

    async def run_async(self):
        """ Initial read s3 history then listen kafka for new data and append to dataframe"""
        # Initial read s3 history
        self._s3_feed = S3Feed(self._feature_name, merge_tolerance=self._merge_tolerance)
        await self.read_history()
        self._max_history_datetime = self.data.index.max() if not self.data.empty else pd.Timestamp(0)

        # Connect to kafka
        kafka_feed = KafkaFeed(level2_queue=self._level2_queue, candles_queue=self._candles_queue)
        await asyncio.gather(kafka_feed.run(start_time=self._max_history_datetime), self.processing_loop())
