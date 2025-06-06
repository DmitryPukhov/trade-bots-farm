import json
from unittest import TestCase

import pandas as pd

from level2_preproc import Level2Preproc


class TestLevel2Preproc(TestCase):
    def test_process(self):
        ts1 = pd.Timestamp("2025-06-03 14:11:00")
        ts2 = pd.Timestamp("2025-06-03 14:12:10")
        ts3 = pd.Timestamp("2025-06-03 14:12:11")

        msg = {
            "tick": {
                "bids": [[98, 1], [99, 2]],
                "asks": [[101, 3], [102, 4]],
                "ts": ts1.value // 1_000_000,  # nanos to millis
            }
        }

        level2_preproc = Level2Preproc()

        # Accumulate minute 1, don't process
        msg["tick"]["ts"] = ts1.value // 1_000_000
        preprocessed = pd.DataFrame(level2_preproc.process(json.dumps(msg)))
        self.assertTrue(preprocessed.empty)
        self.assertListEqual([pd.Timestamp("2025-06-03 14:11:00")], list(level2_preproc._buffer.keys()))

        # Accumulate minute 2, don't process minute 1 because of timeout not elapsed
        msg["tick"]["ts"] = ts2.value // 1_000_000
        preprocessed = pd.DataFrame(level2_preproc.process(json.dumps(msg)))
        self.assertTrue(preprocessed.empty)
        self.assertListEqual([pd.Timestamp("2025-06-03 14:11:00"), pd.Timestamp("2025-06-03 14:12:00")], list(level2_preproc._buffer.keys()))

        # Accumulate minute 2, process minute 1 and delete from buffer
        msg["tick"]["ts"] = ts3.value // 1_000_000
        preprocessed = pd.DataFrame(level2_preproc.process(json.dumps(msg)))
        self.assertEqual(1, len(preprocessed))
        self.assertListEqual([pd.Timestamp("2025-06-03 14:12:00")], list(level2_preproc._buffer.keys()))

    def test_transform_message(self):
        raw_msg = {
            "tick": {
                "ts": pd.Timestamp("2025-06-03 14:11:00").value / 1_000_000,
                "bids": [[101, 1], [102, 2]],
                "asks": [[103, 3], [104, 4]]
            }
        }
        transformed = Level2Preproc()._transform_message(raw_msg)

        self.assertEqual(transformed.bid_max, 102)
        self.assertEqual(transformed.ask_min, 103)
        self.assertEqual(transformed.bid_vol_sum, 3)
        self.assertEqual(transformed.ask_vol_sum, 7)
        self.assertEqual(transformed.bid_mul_vol_sum, 101 * 1 + 102 * 2)
        self.assertEqual(transformed.ask_mul_vol_sum, 103 * 3 + 104 * 4)
        self.assertEqual(transformed.bid_expect, (101 * 1 + 102 * 2) / (1 + 2))
        self.assertEqual(transformed.ask_expect, (103 * 3 + 104 * 4) / (3 + 4))
        self.assertEqual(transformed.expect,
                         ((103 * 3 + 104 * 4) - (101 * 1 + 102 * 2)) / (1 + 2 + 3 + 4))

    def test_aggregate(self):
        raw_msg = {
            "tick": {
                "ts":pd.Timestamp("2025-06-03 14:11:00").value/1_000_000,
                "bids": [[101, 1], [102, 2]],
                "asks": [[103, 3], [104, 4]]
            }
        }
        aggregated = Level2Preproc()._aggregate([raw_msg])

        # Just ensure something is calculated, no need to test pandas mean function
        self.assertEqual(aggregated["bid_max"], 102)
