import asyncio
import logging
import os
from typing import Optional

import pandas as pd

from feed.kafka_feed import KafkaFeed
from feed.s3_feed import S3Feed


class KafkaWithS3Feed:
    """ Read history data from s3 then listen kafka for new data"""

    def __init__(self, feature_name: str, new_data_event: asyncio.Event, stop_event: asyncio.Event, old_datetime: pd.Timestamp):
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
        self.history_minutes_limit = int(os.environ.get("HISTORY_MINUTES", "1600"))

        self._s3_feed:Optional[S3Feed] = None
        self._kafka_feed:Optional[KafkaFeed] = None
        self._last_tried_kafka_offsets_time = None
        self._old_datetime = old_datetime

    async def on_level2(self, msg):
        # Convert message to DataFrame row with datetime index
        df = pd.DataFrame([msg])
        dt = pd.to_datetime(msg['datetime'])
        df['datetime'] = dt
        df.set_index('datetime', inplace=True, drop=False)

        # Use pd.concat instead of append
        self._level2_buf = pd.concat([self._level2_buf, df])
        self._logger.debug(f"Got level2 message. datetime: {dt}, message: {msg}")

    async def on_candle(self, msg):
        df = pd.DataFrame([msg])
        dt = pd.to_datetime(msg['close_time'])
        df['close_time'] = dt
        df.set_index('close_time', inplace=True, drop=False)
        self._candles_buf = pd.concat([self._candles_buf, df])
        self._logger.debug(f"Got candle message. datetime: {dt}, message: {msg}")

    async def flush_buffers(self):
        """
        If data in buffer is ready, put it to main merged dataframe. In good case each buffer contains one record per minute
        In case of time lags, consider pandas buffers with many messages
        """

        self._logger.debug(
            f"Flushing buffers. Level2 buf size: {len(self._level2_buf)}, candles buf size: {len(self._candles_buf)}, data size:{len(self.data)}")

        # Buffer checks, latest bound should be after start_datetime
        if self._level2_buf.empty or self._candles_buf.empty:
            self._logger.debug("Buffers are empty. Skipping flushing")
            return
        if self._old_datetime:
            last_level2_datetime = self._level2_buf.index.max()
            last_candles_datetime = self._candles_buf.index.max()

            if last_level2_datetime <= self._old_datetime or last_candles_datetime <= self._old_datetime:
                self._logger.debug(f"Buffer is too old. Last level2: {self._level2_buf.index.max()}, candle: {self._candles_buf.index.max()}, but should be after {self._old_datetime}.")
                return
        self._logger.debug(f"Buffer has new messages after {self._old_datetime}.")

        is_good_time_gap_previous, time_gap_previous = await self.get_time_gap(supress_logging=True)

        stream_df = pd.merge_asof(left=self._candles_buf, right=self._level2_buf, left_index=True, right_index=True,
                                  tolerance=self._merge_tolerance, direction="nearest")
        stream_df = stream_df.dropna()

        if not stream_df.empty:
            # Clean level2 buffer
            level2_matched_mask = self._level2_buf.index.isin(stream_df["datetime"])
            self._level2_buf = self._level2_buf[~level2_matched_mask]

            # For candles
            candles_matched_mask = self._candles_buf.index.isin(stream_df["close_time"])
            self._candles_buf = self._candles_buf[~candles_matched_mask]

            # Now we can clean close_time and set index and datetime to the latest value
            stream_df["datetime"] = stream_df[["datetime", "close_time"]].max(axis=1)
            self._min_stream_datetime = min(self._min_stream_datetime or pd.Timestamp.max, stream_df["datetime"].min())
            stream_df.set_index("datetime", inplace=True, drop=False)

            # Append the merged data to the main dataframe
            stream_df = stream_df[~stream_df.index.isin(self.data.index)]
            self.data = pd.concat([df for df in [self.data, stream_df] if not df.empty])
            self._logger.debug(f"Flush buffers complete. Data size: {len(self.data)}, "
                               f"level2 buf size: {len(self._level2_buf)}, "
                               f"candles buf size: {len(self._candles_buf)}")
            self.data = self.data[-self.history_minutes_limit:]

            # If time gap is good, notify about new data
            is_good_time_gap, time_gap = await self.get_time_gap(supress_logging=True)
            if is_good_time_gap:
                # When initial time gap is closed, write to log about it. It happens only once.
                if not is_good_time_gap_previous:
                    self._logger.info(
                        f"Time gap is good now. Old time gap: {time_gap_previous}, new time gap: {time_gap}, "
                        f"max allowed time gap: {self._history_stream_max_time_gap}, "
                        f"max history datetime: {self._max_history_datetime}, "
                        f"min stream datetime: {self._min_stream_datetime}"
                    )
                # Notify that new data is available
                self.new_data_event.set()

    async def get_time_gap(self, supress_logging=False) -> (bool, pd.Timedelta):
        """ Calculate the time gap between the last message from s3 and the first message from kafka"""

        if self._min_stream_datetime and self._max_history_datetime:
            time_gap = self._min_stream_datetime.tz_localize(
                "UTC").to_pydatetime() - self._max_history_datetime.tz_localize("UTC").to_pydatetime()
            time_gap = max(time_gap, pd.Timedelta(seconds=0))
            is_good_gap = time_gap < self._history_stream_max_time_gap
        else:
            time_gap = None
            is_good_gap = False
        log_msg = f"Calculated time gap: {time_gap}, is good: {is_good_gap}. max allowed: {self._history_stream_max_time_gap}."
        f"Max history datetime: {self._max_history_datetime}, min stream datetime: {self._min_stream_datetime}"
        if not supress_logging:
            self._logger.info(log_msg)
        else:
            self._logger.debug(log_msg)

        return is_good_gap, time_gap

    async def handle_time_gap_periodically(self):
        """
        If there is a time gap between s3 and kafka, try to load new history from s3
         or move kafka committed offset to the past
        """

        # Initial history already loaded, kafka is not started yet, so wait for kafka to start
        self._logger.debug(f"Checking time gap with interval {self._history_try_interval.total_seconds()} sec")
        await asyncio.sleep(self._history_try_interval.total_seconds())

        # Main loop: check time gap, try to incrementally load new history, try to move kafka offsets
        is_good_gap = False
        while not self.stop_event.is_set() and not is_good_gap:
            try:
                # Read s3 history
                is_good_gap, time_gap = await self.get_time_gap()
                if not is_good_gap:
                    self._logger.info(f"Try to load new history from s3")
                    await self.read_history()
                # Move kafka offsets before last s3 data
                is_good_gap, time_gap = await self.get_time_gap()
                if not is_good_gap:
                    if self._last_tried_kafka_offsets_time is None:
                        self._last_tried_kafka_offsets_time = self._min_stream_datetime
                    else:
                        self._last_tried_kafka_offsets_time -= time_gap
                    self._logger.info(
                        f"Move kafka committed offsets to max history datetime or below it: {self._last_tried_kafka_offsets_time}")
                    await self._kafka_feed.set_offsets_to_time(self._last_tried_kafka_offsets_time)
            except Exception as e:
                logging.error(f"Error while handling time gap: {e}")

            # Wait some time and check again
            if not is_good_gap:
                await asyncio.sleep(self._history_try_interval.total_seconds())
                is_good_gap, time_gap = await self.get_time_gap()

        logging.info(f"Exiting time gap checking loop because of time gap is good")

    async def processing_loop(self):
        """ Get new messages from stream, add to buffers, flush buffers to main dataframe"""

        while not self.stop_event.is_set():
            is_new_data = False
            # Read buffers
            if not self._level2_queue.empty():
                await self.on_level2(await self._level2_queue.get())
                is_new_data |= True
            if not self._candles_queue.empty():
                await self.on_candle(await self._candles_queue.get())
                is_new_data |= True

            #  Process new data if it comes
            if is_new_data:
                await self.flush_buffers()
                await asyncio.sleep(0)
            else:
                await asyncio.sleep(1)

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

        # Initial read s3 history, modified after last kafka message = None, i.e. read all history
        self._s3_feed = S3Feed(self._feature_name, merge_tolerance=self._merge_tolerance)
        await self.read_history()

        # Check time gap in background, if it is bad, both read history incremental and move kafka offsets down
        task = asyncio.create_task(self.handle_time_gap_periodically())

        # Connect to kafka and listen for new data
        self._kafka_feed = KafkaFeed(level2_queue=self._level2_queue, candles_queue=self._candles_queue)
        await asyncio.gather(self._kafka_feed.run(start_time=self._max_history_datetime), self.processing_loop())
