import pandas as pd

from preproc_base import PreprocBase


class CandlesPreproc(PreprocBase):
    """ Accumulate Level 2 messages and aggregate them"""

    async def _aggregate(self, raw_messages: []) -> dict:
        """
        Aggregate accumulated messages within a minute.
        Method is called once a minute
        """
        # {
        #     'open_time': 'min',
        #     'close_time': 'max',      # Equivalent to 'last' for time
        #     'open': lambda x: x.iloc[0],    # First value
        #     'high': 'max',
        #     'low': 'min',
        #     'close': lambda x: x.iloc[-1],   # Last value
        #     'vol': 'sum'}
        if not raw_messages:
            return {}

        df_1min = pd.DataFrame([msg["tick"] for msg in raw_messages]).copy()
        df_1min["ts"] = [msg["ts"] for msg in raw_messages].copy()

        df_1min["close_time"] = pd.to_datetime(df_1min["ts"], unit="ms")
        df_1min["open_time"] = df_1min["close_time"] - pd.Timedelta("1min")
        df_1min["vol"] = df_1min["amount"]
        df_1min = df_1min[["open_time", "close_time", "open", "high", "low", "close", "vol"]]
        df_1min_resampled = df_1min.resample("1min", label="right", closed="right", on="close_time").agg({
            'open_time': 'min',
            'close_time': 'max',  # Equivalent to 'last' for time
            'open': "first",  # First value
            'high': 'max',
            'low': 'min',
            'close': "last",  # Last value
            'vol': 'max'
        })
        df_1min_resampled[["open_time", "close_time"]] = df_1min_resampled[["open_time", "close_time"]].astype("str")

        if len(df_1min_resampled) > 1:
            raise ValueError("Messages, accumulated for aggregation should be inside a minute")
        return df_1min_resampled.to_dict(orient='records')
