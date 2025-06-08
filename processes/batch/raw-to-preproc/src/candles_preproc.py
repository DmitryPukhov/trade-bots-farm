import pandas as pd


class CandlesPreproc:
    """ Accumulate Level 2 messages and aggregate them"""

    def process(self, raw_candles: pd.DataFrame) -> pd.DataFrame:
        # In row candles volume is small at the start end increasing till the end of each minute
        # We are interested only in the last state of each candle per a minute

        raw_candles[["open_time", "close_time"]] = raw_candles[["open_time", "close_time"]].astype('datetime64[ms]')
        bad_col = "close_time.1"
        if bad_col in raw_candles.columns:
            del raw_candles[bad_col]
        columns = raw_candles.columns.tolist()
        resampled_df = raw_candles.resample("1min", on="close_time").agg("last").reset_index()
        resampled_df[["open_time", "close_time"]] = resampled_df[["open_time", "close_time"]].astype('str')
        resampled_df = resampled_df[columns]
        return resampled_df
