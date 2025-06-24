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

    def __init__(self, metrics_labels: dict[str, str], indicators_params = CandlesMultiIndiFeatures.default_params):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._input_level2_cols = [
            "datetime", "l2_bid_max", "l2_bid_expect", "l2_bid_vol", "l2_ask_min", "l2_ask_expect", "l2_ask_vol"
        ]
        self._input_candles_cols = ["open_time", "close_time", "open", "high", "low", "close", "vol"]

        # Indicators periods for features
        self.features_candles_periods = os.getenv("FEATURES_CANDLES_PERIODS", "1min").replace(" ", "").split(",")
        self.features_level2_periods = os.getenv("FEATURES_LEVEL2_PERIODS", "1min").replace(" ", "").split(",")
        self._metrics_labels = metrics_labels
        self._indicators_params = indicators_params

    async def calc(self, input_df: pd.DataFrame, previous_datetime: pd.Timestamp = pd.Timestamp.min):
        """ Features calculation"""
        if input_df.empty:
            self._logger.debug("Input dataframe is empty, nothing to do")
            return pd.DataFrame()
        if input_df.index[-1] <= previous_datetime:
            self._logger.debug(f"Dataframe last index: {input_df.index[-1]} is before previously calculated: {previous_datetime}, nothing to do")
            return pd.DataFrame()

        # Logging
        logging.debug(f"Calculating features on input interval from {input_df.index[0]} to {input_df.index[-1]}")
        start_ts = datetime.now()
        FeaturesMetrics.input_rows.labels(self._metrics_labels).inc(len(input_df))

        # Level2 features
        level2_df = input_df[self._input_level2_cols].sort_index()
        level2_features = Level2MultiIndiFeatures.level2_features_of(level2_df, self.features_level2_periods, self._indicators_params)
        await asyncio.sleep(0)

        # Candles features
        candles_1min_df = input_df[self._input_candles_cols].sort_index()
        candles_1min_df["close_time"] = candles_1min_df.index
        candles_1min_df["open_time"] = candles_1min_df["close_time"] - pd.Timedelta("1min")
        candles_by_periods = CandlesFeatures.rolling_candles_by_periods(candles_1min_df, self.features_candles_periods)
        candles_features = CandlesMultiIndiFeatures.multi_indi_features(candles_by_periods, self._indicators_params)
        await asyncio.sleep(0)

        # Inner merge level2 and candles features, clean and drop NaN
        features = pd.merge(candles_features, level2_features, left_index=True, right_index=True)
        FeaturesMetrics.features_dirty_rows.labels(self._metrics_labels).inc(len(features))

        features = FeatureCleaner.clean(input_df, features).dropna()
        FeaturesMetrics.features_cleaned_rows.labels(self._metrics_labels).inc(len(features))

        # Drop previously produced. If features topic does not exist or don't contain records, no filter
        if not features.empty:
            self._logger.debug(f"Last processed dt: {previous_datetime}. Input last index:{input_df.index[-1]}, features last index:{features.index[-1]}, Input max index:{input_df.index.max()}, features max index:{features.index.max()}")
        else:
            self._logger.debug(f"Features are empty")
        features_new = features[features.index > previous_datetime] if previous_datetime and not features.empty else features
        self._logger.debug(f"New features new len: {len(features_new)}, from {features_new.index[0] if not features_new.empty else 'None'} to {features_new.index[-1] if not features_new.empty else 'None'}")
        FeaturesMetrics.features_new_rows.labels(self._metrics_labels).inc(len(features_new))
        await asyncio.sleep(0)

        # Set metrics
        duration = (datetime.now() - start_ts).total_seconds()
        FeaturesMetrics.features_calc_duration_sec.labels(self._metrics_labels).set(duration)
        time_lag_sec = max(0.0, (datetime.now() - features_new.index.max()).total_seconds())
        await asyncio.sleep(0.001)
        FeaturesMetrics.features_output_rows.labels(self._metrics_labels).inc()
        FeaturesMetrics.features_time_lag_sec.labels(self._metrics_labels).set(time_lag_sec)
        features_new["datetime"] = features_new.index.copy()

        return features_new
