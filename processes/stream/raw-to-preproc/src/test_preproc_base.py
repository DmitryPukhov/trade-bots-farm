import json
from unittest import TestCase
from unittest.mock import MagicMock

import pandas as pd

from preproc_base import PreprocBase


class TestPreprocBase(TestCase):

    @staticmethod
    def new_preproc_base():
        """ Preproc base with mocket aggregation function."""
        preproc_base = PreprocBase()
        preproc_base._aggregate = MagicMock()
        return preproc_base

    def test_process(self):
        ts1 = pd.Timestamp("2025-06-03 14:11:00")
        ts2 = pd.Timestamp("2025-06-03 14:12:10")
        ts3 = pd.Timestamp("2025-06-03 14:12:11")

        msg = {
            "tick": {
                "bids": [[98, 1], [99, 2]],
                "asks": [[101, 3], [102, 4]],
                "id": ts1.value // 1_000_000,  # nanos to millis
            }
        }

        preproc_base = self.new_preproc_base()

        # Accumulate minute 1, don't process
        msg["tick"]["id"] = ts1.value // 1_000_000
        preprocessed = pd.DataFrame(preproc_base.process(json.dumps(msg)))
        self.assertTrue(preprocessed.empty)
        self.assertListEqual([pd.Timestamp("2025-06-03 14:11:00")], list(preproc_base._buffer.keys()))

        # Accumulate minute 2, don't process minute 1 because of timeout not elapsed
        msg["tick"]["id"] = ts2.value // 1_000_000
        preprocessed = pd.DataFrame(preproc_base.process(json.dumps(msg)))
        self.assertTrue(preprocessed.empty)
        self.assertListEqual([pd.Timestamp("2025-06-03 14:11:00"), pd.Timestamp("2025-06-03 14:12:00")], list(preproc_base._buffer.keys()))

        # Accumulate minute 2, process minute 1 and delete from buffer
        msg["tick"]["id"] = ts3.value // 1_000_000
        preprocessed = pd.DataFrame(preproc_base.process(json.dumps(msg)))
        self.assertEqual(1, len(preprocessed))
        self.assertListEqual([pd.Timestamp("2025-06-03 14:12:00")], list(preproc_base._buffer.keys()))

