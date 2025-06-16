import asyncio
import logging
import os

import pandas as pd
from anyio import sleep

from feed.kafka_feed import KafkaFeed
from feed.s3_feed import S3Feed


class KafkaWithS3Feed:
    """ Read history data from s3 then listen kafka for new data"""

    def __init__(self, feature_name: str, new_data_event: asyncio.Event, stop_event: asyncio.Event):
        self._logger = logging.getLogger(__class__.__name__)
        self.data = pd.DataFrame()
        self._feature_name = feature_name
        self._candles_buf = pd.DataFrame()
        self._level2_buf = pd.DataFrame()
        self._merge_tolerance = pd.Timedelta(seconds=59)  # Fixed typo
        self._level2_queue = asyncio.Queue()
        self._candles_queue = asyncio.Queue()
        self.new_data_event = new_data_event
        self.stop_event = stop_event
        self._last_candle_time = pd.Timestamp(0)

        # Settings to track gap between s3 and kafka
        self._max_history_datetime = None  # Updated when loading history at the beginning
        self._min_stream_datetime = None  # Updated when reading first messages from kafka
        self._history_stream_max_time_gap = pd.Timedelta(minutes=1)
        self._history_try_interval = pd.Timedelta(os.getenv("HISTORY_TRY_INTERVAL", "1min"))

        self._s3_feed = None
        self._kafka_feed = None
        self._last_tried_kafka_offsets_time = None

    async def on_level2(self, msg):
        # Convert message to DataFrame row with datetime index
        df = pd.DataFrame([msg])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True, drop=False)

        # Use pd.concat instead of append
        self._level2_buf = pd.concat([self._level2_buf, df])
        self._logger.debug(f"Got level2 message {msg}. Last level2 message time {self._level2_buf.index[-1]}")

    async def on_candle(self, msg):
        df = pd.DataFrame([msg])
        df['close_time'] = pd.to_datetime(df['close_time'])
        df.set_index('close_time', inplace=True, drop=False)
        self._candles_buf = pd.concat([self._candles_buf, df])
        self._logger.debug(f"Got candle message {msg}. Last candle message time {self._candles_buf.index[-1]}")

    async def flush_buffers(self):
        """
        If data in buffer is ready, put it to main merged dataframe. In good case each buffer contains one record per minute
        In case of time lags, consider pandas buffers with many messages
        """
        self._logger.debug(
            f"Flushing buffers. Level2 buf size: {len(self._level2_buf)}, candles buf size: {len(self._candles_buf)}, data size:{len(self.data)}")
        if self._level2_buf.empty or self._candles_buf.empty:
            self._logger.debug("Buffers are empty. Skipping flushing")
            return
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
            self._min_stream_datetime = min(self._min_stream_datetime or pd.Timestamp.max, merged_df["datetime"].min())
            merged_df.set_index("datetime", inplace=True, drop=False)

            # Append the merged data to the main dataframe
            self.data = pd.concat([df for df in [self.data, merged_df] if not df.empty])
            self._logger.debug(f"Flush buffers complete. Data size: {len(self.data)}, "
                               f"level2 buf size: {len(self._level2_buf)}, "
                               f"candles buf size: {len(self._candles_buf)}")

            # Notify about new data
            self.new_data_event.set()

    async def get_time_gap(self) -> pd.Timedelta:
        """ Calculate the time gap between the last message from s3 and the first message from kafka"""
        if self._min_stream_datetime and self._max_history_datetime:
            time_gap = self._min_stream_datetime.tz_localize(
                "UTC").to_pydatetime() - self._max_history_datetime.tz_localize("UTC").to_pydatetime()
        else:
            time_gap = None
        self._logger.debug(f"Calculated time gap: {time_gap}. "
                           f"Max history datetime: {self._max_history_datetime}, min stream datetime: {self._min_stream_datetime}")
        return time_gap

    async def handle_time_gap(self):
        """
        If there is a time gap between s3 and kafka, try to load new history from s3
         or move kafka committed offset to the past
        """
        while not self.stop_event.is_set():
            def time_gap_log_message(time_gap_: pd.Timedelta):
                self._logger.info(
                    f"Time gap between s3 and kafka is: {time_gap_}, max allowed: {self._history_stream_max_time_gap}. "
                    f"Max history datetime: {self._max_history_datetime}, min stream datetime: {self._min_stream_datetime}")

            self._logger.debug(f"Checking time gap with interval {self._history_try_interval.total_seconds()} sec")
            # If we have time gap, try to load more history from s3
            time_gap = await self.get_time_gap()

            if time_gap and time_gap > self._history_stream_max_time_gap:
                # Don't go to s3 too often, wait some time
                self._logger.info(time_gap_log_message(time_gap))
                self._logger.info(f"Try to load new history from s3")
                await self.read_history()

            # If loading history above did not help, try to move kafka committed offsets down to the end of the history data
            time_gap = await self.get_time_gap()
            if time_gap and time_gap > self._history_stream_max_time_gap and self._max_history_datetime is not None:
                self._logger.info(time_gap_log_message(time_gap))
                if self._last_tried_kafka_offsets_time is None:
                    self._last_tried_kafka_offsets_time = self._min_stream_datetime
                else:
                    self._last_tried_kafka_offsets_time -= time_gap
                self._logger.info(
                    f"Move kafka committed offsets to max history datetime or below it: {self._last_tried_kafka_offsets_time}")
                await self._kafka_feed.set_offsets_to_time(self._last_tried_kafka_offsets_time)

            await asyncio.sleep(self._history_try_interval.total_seconds())

    async def processing_loop(self):
        """ Get new messages from stream, add to buffers, flush buffers to main dataframe"""

        while not self.stop_event.is_set():
            # Read buffers
            if not self._level2_queue.empty():
                await self.on_level2(await self._level2_queue.get())
            if not self._candles_queue.empty():
                await self.on_candle(await self._candles_queue.get())

            #  Process new data if it comes
            if not (self._level2_buf.empty or self._candles_buf.empty):
                await self.flush_buffers()

            await asyncio.sleep(0.1)

    async def read_history(self):
        """ Read history from s3 and put it to main dataframe"""

        start_date = self._max_history_datetime.date() if self._max_history_datetime else None
        end_date = self._min_stream_datetime.date() if self._min_stream_datetime else None
        # Read history from s3
        history_df = await self._s3_feed.read_history(
            start_date=start_date,
            end_date=end_date,
            modified_after=self._min_stream_datetime)
        if not history_df.empty:
            self._max_history_datetime = history_df.index.max()
            if not self.data.empty:
                history_df = history_df[~history_df.index.isin(self.data.index)]
            self.data = pd.concat([self.data, history_df]).sort_index()

    async def run_async(self):
        """ Initial read s3 history then listen kafka for new data and append to dataframe"""
        # Initial read s3 history
        self._s3_feed = S3Feed(self._feature_name, merge_tolerance=self._merge_tolerance)
        task = asyncio.create_task(self.handle_time_gap())
        await self.read_history()

        # Connect to kafka
        self._kafka_feed = KafkaFeed(level2_queue=self._level2_queue, candles_queue=self._candles_queue)
        await asyncio.gather(self._kafka_feed.run(start_time=self._max_history_datetime), self.processing_loop())
