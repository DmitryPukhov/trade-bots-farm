import json
from unittest.mock import MagicMock, AsyncMock

import pandas as pd

from preproc_base import PreprocBase
import pytest

class TestPreprocBase:

    @staticmethod
    def new_preproc_base():
        """ Preproc base with mocket aggregation function."""
        preproc_base = PreprocBase()
        preproc_base._aggregate = AsyncMock()
        preproc_base._aggregate.return_value = [1]

        return preproc_base

    @pytest.mark.asyncio
    async def test_process(self):
        ts1 = pd.Timestamp("2025-06-03 14:11:00")
        ts2 = pd.Timestamp("2025-06-03 14:12:10")
        ts3 = pd.Timestamp("2025-06-03 14:12:11")

        msg = {
            "ch": "topic1",
            "tick": {
                "bids": [[98, 1], [99, 2]],
                "asks": [[101, 3], [102, 4]],
                "ts": ts1.value // 1_000_0000,  # nanos to millis
            }
        }

        preproc_base = self.new_preproc_base()

        # Accumulate minute 1, don't process
        msg["tick"]["ts"] = ts1.value // 1_000_000
        preprocessed = pd.DataFrame(await preproc_base.process(json.dumps(msg)))
        assert preprocessed.empty
        assert list(preproc_base._buffer.keys()) == [pd.Timestamp("2025-06-03 14:11:00")]

        # Accumulate minute 2, don't process minute 1 because of timeout not elapsed
        msg["tick"]["ts"] = ts2.value // 1_000_000
        preprocessed = pd.DataFrame(await preproc_base.process(json.dumps(msg)))
        assert preprocessed.empty
        assert  list(preproc_base._buffer.keys()) == [pd.Timestamp("2025-06-03 14:11:00"), pd.Timestamp("2025-06-03 14:12:00")]

        # Accumulate minute 2, process minute 1 and delete from buffer
        msg["tick"]["ts"] = ts3.value // 1_000_000
        preprocessed = await preproc_base.process(json.dumps(msg))
        assert len(preprocessed) == 1
        assert list(preproc_base._buffer.keys()) == [pd.Timestamp("2025-06-03 14:12:00")]

