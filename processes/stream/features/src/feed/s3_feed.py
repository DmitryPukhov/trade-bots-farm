import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta, date

import pandas as pd
import s3fs

from features_metrics import FeaturesMetrics
from s3_tools import S3Tools


class S3Feed:
    def __init__(self, feature_name: str, merge_tolerance):
        # S3 directories starting from bucket name
        self._feature_name = feature_name
        self._s3_level2_dir = os.getenv("S3_LEVEL2_DIR")
        self._s3_candles_dir = os.getenv("S3_CANDLES_DIR")
        self._s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL")
        self._s3_access_key = os.environ.get("S3_ACCESS_KEY")
        self._s3_secret_key = os.environ.get("S3_SECRET_KEY")
        self.ticker = os.environ.get("TICKER")
        self._s3_fs = s3fs.S3FileSystem(client_kwargs={"endpoint_url": self._s3_endpoint_url},
                                        key=self._s3_access_key,
                                        secret=self._s3_secret_key)
        self.history_days_limit = int(os.environ.get("HISTORY_DAYS", "1"))
        self.storage_options = {
            "key": self._s3_access_key,
            "secret": self._s3_secret_key,
            "client_kwargs": {"endpoint_url": self._s3_endpoint_url},
        }
        # tolerance for merge_asof()
        self._merge_tolerance = pd.Timedelta(minutes=1)

        logging.info(f"s3 endpoint url: {self._s3_endpoint_url}, "
                     f"level2_dir: {self._s3_level2_dir}, candles_dir: {self._s3_candles_dir}, "
                     f"assess_key: ***{self._s3_access_key[:-3]}, secret_key: ***{self._s3_secret_key[-3]}")

    async def _merge_inputs(self, level2_df, candles_df):
        # Merge with respect to tolerance

        logging.info(f"Merge level2 and candles data with tolerance {self._merge_tolerance}")
        merged_df = pd.merge_asof(level2_df, candles_df, left_index=True, right_index=True,
                                  tolerance=self._merge_tolerance).sort_index()
        merged_df_dirty_len = len(merged_df)
        merged_df = merged_df.dropna().sort_index()

        # Set metrics
        merged_df_len = len(merged_df)
        FeaturesMetrics.input_s3_rows_not_merged.labels(feature=self._feature_name).inc(
            merged_df_dirty_len - merged_df_len)
        FeaturesMetrics.input_s3_rows_good.labels(feature=self._feature_name).inc(merged_df_len)

        return merged_df

    async def _read_csv(self, s3_dir: str, daily_paths: [str], index_col) -> pd.DataFrame:
        """ Read daily files from s3 dir containing data between dates"""

        # Find which files to read
        # daily_paths = S3Tools.find_daily_files(self._s3_fs, s3_dir, start_date, end_date)

        # Read all files to a single dataframe
        daily_files = []
        for i, daily_path in enumerate(daily_paths):
            daily_path = f"s3://{daily_path}"
            logging.info(f"Reading {i}/{len(daily_paths)} file: {daily_path}")
            daily_df = pd.read_csv(daily_path, storage_options=self.storage_options)
            daily_files.append(daily_df)
            await asyncio.sleep(0.001)
        df = pd.concat(daily_files)

        # Clean dirty columns
        df = await self._postread_proc(df, index_col)

        # Set metrics
        FeaturesMetrics.input_s3_rows.labels(s3_dir=s3_dir).inc(len(df))
        time_lag = (datetime.utcnow() - df.index.max()).total_seconds()
        FeaturesMetrics.input_s3_time_lag_sec.labels(s3_dir=s3_dir).set(time_lag)

        return df

    @staticmethod
    async def _postread_proc(df: pd.DataFrame, index_col: str) -> pd.DataFrame:
        # Convert datetime columns from string to datetime
        datetime_cols = [col for col in df.columns if col.lower() == "datetime" or col.lower().endswith("_time")]
        df[datetime_cols] = df[datetime_cols].apply(pd.to_datetime)
        df = df.set_index(index_col, drop=False)
        # Some rubbish columns can happen in csv files
        good_cols = [col for col in df.columns if not col.startswith("Unnamed:")]
        return df[good_cols]

    async def read_history(self, start_date: date = None, end_date: date = None,
                           modified_after=pd.Timestamp.min.tz_localize("UTC")) -> pd.DataFrame:
        """ Read historical data from s3."""
        end_date = end_date or datetime.now(timezone.utc).date()
        start_date = start_date or end_date - timedelta(days=self.history_days_limit)

        # Find which files to read
        level2_paths = S3Tools.find_daily_files(self._s3_fs, self._s3_level2_dir, start_date, end_date, modified_after)
        candles_paths = S3Tools.find_daily_files(self._s3_fs, self._s3_candles_dir, start_date, end_date,
                                                 modified_after)
        if not (level2_paths and candles_paths):
            # No data found
            return pd.DataFrame()

        # Read and merge level2 and candles
        level2_df = await self._read_csv(self._s3_level2_dir, level2_paths, "datetime")
        candles_df = await self._read_csv(self._s3_candles_dir, candles_paths, "close_time")
        return await self._merge_inputs(level2_df, candles_df)
