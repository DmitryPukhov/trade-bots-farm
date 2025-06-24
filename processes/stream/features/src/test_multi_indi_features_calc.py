import pandas as pd
import pytest

from multi_indi_features_calc import MultiIndiFeaturesCalc


class TestMultiIndiFeaturesCalc:

    def params(self):
        return {"1min": {"cca": {"window": 2},
                         "ichimoku": {"window1": 1, "window2": 1, "window3": 1},
                         "adx": {"window": 1},
                         "rsi": {"window": 1},
                         "stoch": {"window": 2, "smooth_window": 1},
                         "macd": {"slow": 1, "fast": 1}
                         }}

    @pytest.mark.asyncio
    async def test_calc(self):
        times = ["2025-06-24 13:01:00", "2025-06-24 13:02:00", "2025-06-24 13:03:00","2025-06-24 13:04:00", "2025-06-24 13:05:00", "2025-06-24 13:01:00"]
        input_df = pd.DataFrame({
            'datetime': times,
            "l2_bid_max": [1, 2, 3, 4, 5, 6],
            "l2_bid_expect": [1, 2, 3, 4, 5, 6],
            "l2_bid_vol": [1, 2, 3, 4, 5, 6],
            "l2_ask_min": [1, 2, 3, 4, 5, 6],
            "l2_ask_expect": [1, 2, 3, 4, 5, 6],
            "l2_ask_vol": [1, 2, 3, 4, 5, 6],
            "open_time": times,
            "close_time": times,
            "open": [1, 2, 3, 4, 5, 6],
            "high": [1, 2, 3, 4, 5, 6],
            "low": [1, 2, 3, 4, 5, 6],
            "close": [1, 2, 3, 4, 5, 6],
            "vol": [1, 2, 3, 4, 5, 6],
        })
        time_cols = ['datetime', 'open_time', 'close_time']
        input_df[time_cols] = input_df[time_cols].apply(pd.to_datetime)
        input_df.set_index("datetime", drop=False, inplace=True)

        features_df = await MultiIndiFeaturesCalc(metrics_labels={}, indicators_params=self.params()).calc(input_df)
        assert not features_df.empty
