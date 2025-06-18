import asyncio
import logging
import os
from datetime import datetime

import pandas as pd

from features_metrics import FeaturesMetrics
from pytrade2.features.CandlesFeatures import CandlesFeatures
from pytrade2.features.CandlesMultiIndiFeatures import CandlesMultiIndiFeatures
from pytrade2.features.FeatureCleaner import FeatureCleaner
from pytrade2.features.level2.Level2MultiIndiFeatures import Level2MultiIndiFeatures


class MultiIndiFeaturesCalc:
    """ Calculate level2 and candles multiple indicators in the same dataframe. Ichimoku, RSI, MACD, BB, Stochastic, etc..."""

    def __init__(self, metrics_labels: dict[str, str]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._input_level2_cols = [
            "datetime", "l2_bid_max", "l2_bid_expect", "l2_bid_vol", "l2_ask_min", "l2_ask_expect", "l2_ask_vol"
        ]
        self._input_candles_cols = ["open_time", "close_time", "open", "high", "low", "close", "vol"]

        # Indicators periods for features
        self.features_candles_periods = os.getenv("FEATURES_CANDLES_PERIODS", "1min").replace(" ", "").split(",")
        self.features_level2_periods = os.getenv("FEATURES_LEVEL2_PERIODS", "1min").replace(" ", "").split(",")
        self._metrics_labels = metrics_labels

    async def calc(self, df: pd.DataFrame, old_datetime: pd.Timestamp = pd.Timestamp.min):
        """ Features calculation"""
        if df.empty:
            self._logger.debug("Input dataframe is empty, nothing to do")
            return pd.DataFrame()
        if df.index[-1] <= old_datetime:
            self._logger.debug(f"Dataframe last index: {df.index[-1]} is before previously calculated: {old_datetime}, nothing to do")
            return pd.DataFrame()

        # Logging
        logging.debug(f"Calculating features on input interval from {df.index[0]} to {df.index[-1]}")
        start_ts = datetime.now()

        # Drop duplicates
        # df = df.groupby(df.index).last()
        df = df.resample("1min").last()

        # Level2 features
        level2_df = df[self._input_level2_cols].sort_index()
        level2_features = Level2MultiIndiFeatures.level2_features_of(level2_df, self.features_level2_periods)
        await asyncio.sleep(0.001)

        # Candles features
        candles_1min_df = df[self._input_candles_cols].sort_index()
        candles_1min_df["close_time"] = candles_1min_df.index
        candles_1min_df["open_time"] = candles_1min_df["close_time"] - pd.Timedelta("1min")

        candles_by_periods = CandlesFeatures.rolling_candles_by_periods(candles_1min_df, self.features_candles_periods)
        candles_features = CandlesMultiIndiFeatures.multi_indi_features(candles_by_periods)
        await asyncio.sleep(0.001)

        # Inner merge level2 and candles features, clean and drop NaN
        features = pd.merge(candles_features, level2_features, left_index=True, right_index=True)
        features = FeatureCleaner.clean(df, features).dropna()

        # Drop previously produced. If features topic does not exist or don't contain records, no filter
        features_new = features[features.index > old_datetime] if old_datetime else features
        await asyncio.sleep(0.001)

        # Set metrics
        duration = (datetime.now() - start_ts).total_seconds()
        FeaturesMetrics.feature_calc_duration_sec.labels(self._metrics_labels).set(duration)

        time_lag_sec = max(0.0, (datetime.now() - features_new.index.max()).total_seconds())
        await asyncio.sleep(0.001)
        FeaturesMetrics.feature_time_lag_sec.labels(self._metrics_labels).set(time_lag_sec)
        features_new["datetime"] = features_new.index.copy()
        return features_new
