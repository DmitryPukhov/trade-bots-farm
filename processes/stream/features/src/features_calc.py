import asyncio
import json
import logging
import os
from datetime import datetime

import pandas as pd
from aiokafka import AIOKafkaConsumer

from features_metrics import FeaturesMetrics
from feed.kafka_with_s3_feed import KafkaWithS3Feed
from pytrade2.features.CandlesFeatures import CandlesFeatures
from pytrade2.features.CandlesMultiIndiFeatures import CandlesMultiIndiFeatures
from pytrade2.features.FeatureCleaner import FeatureCleaner
from pytrade2.features.level2.Level2MultiIndiFeatures import Level2MultiIndiFeatures


class FeaturesCalc:
    def __init__(self, feed: KafkaWithS3Feed, stop_event: asyncio.Event):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._feed = feed
        self._stop_event = stop_event
        self._input_level2_cols = [
            "datetime", "l2_bid_max", "l2_bid_expect", "l2_bid_vol", "l2_ask_min", "l2_ask_expect", "l2_ask_vol"
        ]
        self._input_candles_cols = ["open_time", "close_time", "open", "high", "low", "close", "vol"]

        # Indicators periods for features
        self.features_candles_periods = os.getenv("FEATURES_CANDLES_PERIODS", "1min").replace(" ", "").split(",")
        self.features_level2_periods = os.getenv("FEATURES_LEVEL2_PERIODS", "1min").replace(" ", "").split(",")

        self.features_topic = os.getenv("KAFKA_TOPIC_FEATURES")
        self.ticker = os.environ["TICKER"]
        self._bootstrap_servers = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
        self._kafka_offset = os.environ.get("KAFKA_OFFSET", "latest")
        self._last_produced_datetime = None

    async def get_last_produced_datetime(self) -> pd.Timestamp:
        """
        Go to Kafka topic for last previously produced feature and get datetime from there
        Method to run initially
        """

        self._logger.info(f"Getting last produced datetime for {self.features_topic}")
        group_id = f"{self.__class__.__name__}"

        consumer = AIOKafkaConsumer(  # *self.features_topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=group_id)
        await consumer.start()

        # Value to return
        last_time = pd.Timestamp.min

        # If topic does not exist, return min time
        topics = await consumer.topics()
        if self.features_topic not in topics:
            self._logger.info(f"Topic {self.features_topic} does not exist. Returning min time.")
            return last_time

        try:
            # Get the latest offset for each partition
            partitions = consumer.assignment()
            end_offsets = await consumer.end_offsets(partitions)
            for partition, offset in end_offsets.items():
                if offset > 0:  # If partition has messages
                    await consumer.seek(partition, offset - 1)  # Seek to last message
                    msg_encoded = await consumer.getone()
                    msg = json.loads(msg_encoded.value.decode('utf-8'))
                    msg_time = pd.Timestamp(msg["datetime"])
                    last_time = max(last_time, msg_time)
        finally:
            await consumer.stop()
            self._logger.info(f"Last produced datetime for {self.features_topic} is {last_time}")
            return last_time

    async def calc(self, df: pd.DataFrame):
        """ Features calculation"""

        start_ts = datetime.now()
        logging.debug(f"Calculating features. Last input time: {df.index.max()}")

        # Drop duplicates
        df = df.groupby(df.index).last()

        # Level2 features
        level2_df = df[self._input_level2_cols].sort_index()
        level2_features = Level2MultiIndiFeatures.level2_features_of(level2_df, self.features_level2_periods)

        # Candles features
        candles_1min_df = df[self._input_candles_cols].sort_index()
        candles_by_periods = CandlesFeatures.rolling_candles_by_periods(candles_1min_df, self.features_candles_periods)
        candles_features = CandlesMultiIndiFeatures.multi_indi_features(candles_by_periods)

        # Inner merge level2 and candles features, clean and drop NaN
        features = pd.merge(candles_features, level2_features, left_index=True, right_index=True)
        features = FeatureCleaner.clean(df, features).dropna()

        # Drop previously produced
        features_new = features[features.index > self._last_produced_datetime]

        # Set metrics
        duration = (datetime.now() - start_ts).total_seconds()
        FeaturesMetrics.feature_calc_duration_sec.labels(topic=self.features_topic).set(duration)

        time_lag_sec = max(0.0, (datetime.now() - features_new.index.max()).total_seconds())
        FeaturesMetrics.feature_time_lag_sec.labels(topic=self.features_topic).set(time_lag_sec)

        return features_new

    async def run_async(self):
        self._last_produced_datetime = await self.get_last_produced_datetime()
        while not self._stop_event.is_set():
            await self._feed.new_data_event.wait()
            self._feed.new_data_event.clear()
            input_df = self._feed.data.copy()
            features_df = await self.calc(input_df)
