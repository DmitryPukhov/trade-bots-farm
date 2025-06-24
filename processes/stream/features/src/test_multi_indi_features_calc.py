import pandas as pd
import pytest

from multi_indi_features_calc import MultiIndiFeaturesCalc


class TestMultiIndiFeaturesCalc:

    def params(self):
        period_params = {"cca": {"window": 2},
                         "ichimoku": {"window1": 1, "window2": 1, "window3": 1},
                         "adx": {"window": 2},
                         "rsi": {"window": 1},
                         "stoch": {"window": 2, "smooth_window": 1},
                         "macd": {"slow": 1, "fast": 1}
                         }
        return {
                "5min": period_params,
                "3min": period_params}

    @pytest.mark.asyncio
    async def test_calc(self):
        start_time = pd.Timestamp("2025-06-24 13:01:00")
        n = 100
        times = [start_time + pd.Timedelta(minutes=i) for i in range(n)]

        input_data = {"datetime": times, "open_time": times, "close_time": times}

        for col in ["l2_bid_max", "l2_bid_expect", "l2_bid_vol", "l2_ask_min", "l2_ask_expect", "l2_ask_vol",
                    "open_time", "close_time", "open", "high", "low", "close", "vol"]:
            input_data[col] = range(len(times))

        input_df = pd.DataFrame(input_data)
        time_cols = ['datetime', 'open_time', 'close_time']
        input_df[time_cols] = input_df[time_cols].apply(pd.to_datetime)
        input_df.set_index("datetime", drop=False, inplace=True)

        features_df = await MultiIndiFeaturesCalc(metrics_labels={}, indicators_params=self.params()).calc(input_df)
        assert not features_df.empty
