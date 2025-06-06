import json
from unittest import TestCase

import pandas as pd

from candles_preproc import CandlesPreproc
from level2_preproc import Level2Preproc


class TestCandlesPreproc(TestCase):
    def test_process(self):
        ts1 = pd.Timestamp("2025-06-03 14:11:00")
        ts2 = pd.Timestamp("2025-06-03 14:12:10")
        ts3 = pd.Timestamp("2025-06-03 14:12:11")

        msg = {
            "tick": {
                "id": ts1.value // 1_000_000,  # nanos to millis
                "open": 100,
                "high": 102,
                "low": 100,
                "close": 101,
                "amount": 1000
            }
        }

        candles_preproc = CandlesPreproc()

        # Accumulate minute 1, don't process
        msg["tick"]["id"] = ts1.value // 1_000_000
        preprocessed = pd.DataFrame(candles_preproc.process(json.dumps(msg)))
        self.assertTrue(preprocessed.empty)
        self.assertListEqual([pd.Timestamp("2025-06-03 14:11:00")], list(candles_preproc._buffer.keys()))

        # Accumulate minute 2, don't process minute 1 because of timeout not elapsed
        msg["tick"]["id"] = ts2.value // 1_000_000
        preprocessed = pd.DataFrame(candles_preproc.process(json.dumps(msg)))
        self.assertTrue(preprocessed.empty)
        self.assertListEqual([pd.Timestamp("2025-06-03 14:11:00"), pd.Timestamp("2025-06-03 14:12:00")], list(candles_preproc._buffer.keys()))

        # Accumulate minute 2, process minute 1 and delete from buffer
        msg["tick"]["id"] = ts3.value // 1_000_000
        preprocessed = pd.DataFrame(candles_preproc.process(json.dumps(msg)))
        self.assertEqual(1, len(preprocessed))
        self.assertListEqual([pd.Timestamp("2025-06-03 14:12:00")], list(candles_preproc._buffer.keys()))

    def test_aggregate_empty(self):
        aggregated = CandlesPreproc()._aggregate([])
        self.assertEqual(0, len(aggregated))

    def test_aggregate(self):
        raw_msgs = [
            {"tick": {
                "id": pd.Timestamp("2025-06-03 14:11:01").value // 1_000_000,
                "open": 100,
                "high": 102,
                "low": 98,
                "close": 110,
                "amount": 1000
            }},
            {"tick": {
                "id": pd.Timestamp("2025-06-03 14:11:30").value // 1_000_000,
                "open": 110,
                "high": 104,
                "low": 97,
                "close": 120,
                "amount": 2000
            }},
            {"tick": {
                "id": pd.Timestamp("2025-06-03 14:12:00").value // 1_000_000,
                "open": 120,
                "high": 103,
                "low": 99,
                "close": 101,
                "amount": 50
            }},

        ]
        aggregated = CandlesPreproc()._aggregate(raw_msgs)

        # Just ensure something is calculated, no need to test pandas mean function
        self.assertEqual(1, len(aggregated))
        self.assertEqual(100, aggregated[0]["open"])
        self.assertEqual(104, aggregated[0]["high"])
        self.assertEqual(97, aggregated[0]["low"])
        self.assertEqual(101, aggregated[0]["close"])
        self.assertEqual(2000, aggregated[0]["vol"])

