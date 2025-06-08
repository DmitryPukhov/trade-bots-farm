import pandas as pd


class CandlesPreproc():
    """ Accumulate Level 2 messages and aggregate them"""

    def process(self, raw_level2_df: pd.DataFrame) -> pd.DataFrame:
        # In row candles volume is small at the start end increasing till the end of each minute
        # We are interested only in the last state of each candle per a minute
        return raw_level2_df.resample("1min", on="close_time").agg("last")
