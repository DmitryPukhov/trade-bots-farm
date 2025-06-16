import asyncio
import logging

import pandas as pd

from pytrade2.features.CandlesFeatures import CandlesFeatures
from pytrade2.features.CandlesMultiIndiFeatures import CandlesMultiIndiFeatures
from feed.kafka_with_s3_feed import KafkaWithS3Feed
from pytrade2.features.FeatureCleaner import FeatureCleaner
from pytrade2.features.level2.Level2MultiIndiFeatures import Level2MultiIndiFeatures


class FeaturesCalc:
    def __init__(self, feed: KafkaWithS3Feed, stop_event: asyncio.Event):
        self._feed = feed
        self._stop_event = stop_event
        print (pd.__version__)
        # Input columns
        # self.input_level2_cols = [
        #     "datetime", "l2_bid_max", "l2_bid_vol_sum", "l2_bid_mul_vol_sum", "l2_bid_expect", "l2_ask_min", "l2_ask_vol_sum",
        #     "l2_ask_mul_vol_sum", "l2_ask_expect", "l2_expect"
        # ]
        self.input_level2_cols = [
            "datetime", "l2_bid_max","l2_bid_expect", "l2_bid_vol", "l2_ask_min",  "l2_ask_expect", "l2_ask_vol"
        ]
        self.input_candles_cols = ["open_time", "close_time", "open", "high", "low", "close", "vol"]

        # Indicators periods for features
        self.features_candles_periods = ["10min", "15min", "25min", "40min", "50min", "60min"]
        self.features_level2_periods = ["10min", "15min", "25min",  "40min", "50min", "60min"]

    async def calc(self, df: pd.DataFrame):
        """ Features calculation"""
        logging.info(f"Calculating features. Last input time: {df.index.max()}")

        # Level2 features
        level2_df = df[self.input_level2_cols].sort_index()
        level2_features = Level2MultiIndiFeatures.level2_features_of(level2_df, self.features_level2_periods)

        # Candles features
        candles_1min_df = df[self.input_candles_cols].sort_index()
        candles_by_periods = CandlesFeatures.rolling_candles_by_periods(candles_1min_df, self.features_candles_periods)
        candles_features = CandlesMultiIndiFeatures.multi_indi_features(candles_by_periods)

        # Calculate features, clean time gaps
        features = pd.merge_asof(candles_features, level2_features, left_index = True, right_index=True)
        features = FeatureCleaner.clean(df, features).dropna()
        return features


    async def run_async(self):
        while not self._stop_event.is_set():
            await self._feed.new_data_event.wait()
            self._feed.new_data_event.clear()
            input_df = self._feed.data.copy()
            features_df = await self.calc(input_df)
