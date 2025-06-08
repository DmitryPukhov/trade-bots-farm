from unittest import TestCase

import pandas as pd

from candles_preproc import CandlesPreproc


class TestCandlesPreproc(TestCase):
    def test_process_should_skip_duplicate_close_time_col(self):
        raw_candles_df = pd.DataFrame(
            [{
                "open_time": "2025-08-25 11:41:00", "close_time": "2025-08-25 11:42:00", "close_time.1": "2025-08-25 11:42:00",
                "open": 100, "high": 105, "low": 95, "close": 101, "vol": 1
            }]
        )
        processed_candles_df = CandlesPreproc().process(raw_candles_df)
        self.assertEqual(1, len(processed_candles_df))
    def test_process(self):
        raw_candles_df = pd.DataFrame(
            [{
                "open_time": "2025-08-25 11:41:00", "close_time": "2025-08-25 11:42:00",
                "open": 100, "high": 105, "low": 95, "close": 101, "vol": 1
            },
                {
                    "open_time": "2025-08-25 11:41:00", "close_time": "2025-08-25 11:42:00",
                    "open": 101, "high": 106, "low": 96, "close": 102, "vol": 2
                },
                {
                    "open_time": "2025-08-25 11:41:00", "close_time": "2025-08-25 11:42:00",
                    "open": 102, "high": 107, "low": 97, "close": 103, "vol": 3
                },
            ]
        )
        processed_candles_df = CandlesPreproc().process(raw_candles_df)
        self.assertEqual(1, len(processed_candles_df))
        self.assertEqual(["2025-08-25 11:41:00", "2025-08-25 11:42:00", 102, 107, 97, 103, 3], processed_candles_df.values[0].tolist())

        self.assertEqual(102, processed_candles_df["open"][0])