import json
import pytest
import pandas as pd

from level2_preproc import Level2Preproc


class TestLevel2Preproc:
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
                "ts": ts1.value // 1_000_000,  # nanos to millis
            }
        }

        level2_preproc = Level2Preproc()

        # Accumulate minute 1, don't process
        msg["tick"]["ts"] = ts1.value // 1_000_000
        preprocessed = pd.DataFrame(await level2_preproc.process(json.dumps(msg)))
        assert preprocessed.empty
        assert list(level2_preproc._buffer.keys()) == [pd.Timestamp("2025-06-03 14:11:00")]

        # Accumulate minute 2, don't process minute 1 because of timeout not elapsed
        msg["tick"]["ts"] = ts2.value // 1_000_000
        preprocessed = pd.DataFrame(await level2_preproc.process(json.dumps(msg)))
        assert preprocessed.empty
        assert list(level2_preproc._buffer.keys()) == [pd.Timestamp("2025-06-03 14:11:00"), pd.Timestamp("2025-06-03 14:12:00")]

        # Accumulate minute 2, process minute 1 and delete from buffer
        msg["tick"]["ts"] = ts3.value // 1_000_000
        preprocessed = pd.DataFrame(await level2_preproc.process(json.dumps(msg)))
        assert len(preprocessed) == 1
        assert list(level2_preproc._buffer.keys()) == [pd.Timestamp("2025-06-03 14:12:00")]

    @pytest.mark.asyncio
    async def test_transform_message(self):
        raw_msg = {
            "ch": "topic1",
            "tick": {
                "ts": pd.Timestamp("2025-06-03 14:11:00").value / 1_000_000,
                "bids": [[101, 1], [102, 2]],
                "asks": [[103, 3], [104, 4]]
            }
        }
        transformed = await Level2Preproc()._transform_message(raw_msg)

        assert transformed.l2_bid_max == 102
        assert transformed.l2_ask_min == 103
        assert transformed.l2_bid_vol_sum == 3
        assert transformed.l2_ask_vol_sum == 7
        assert transformed.l2_bid_mul_vol_sum == 101 * 1 + 102 * 2
        assert transformed.l2_ask_mul_vol_sum == 103 * 3 + 104 * 4
        assert transformed.l2_bid_expect == (101 * 1 + 102 * 2) / (1 + 2)
        assert transformed.l2_ask_expect == (103 * 3 + 104 * 4) / (3 + 4)
        assert transformed.l2_expect == ((103 * 3 + 104 * 4) - (101 * 1 + 102 * 2)) / (1 + 2 + 3 + 4)

    @pytest.mark.asyncio
    async def test_aggregate(self):
        raw_msg = {
            "ch": "topic1",
            "tick": {
                "ts":pd.Timestamp("2025-06-03 14:11:00").value/1_000_000,
                "bids": [[101, 1], [102, 2]],
                "asks": [[103, 3], [104, 4]]
            }
        }
        aggregated = await Level2Preproc()._aggregate([raw_msg])

        # Just ensure something is calculated, no need to test pandas mean function
        assert len(aggregated) == 1
        assert aggregated[0]["bid_max"] == 102
