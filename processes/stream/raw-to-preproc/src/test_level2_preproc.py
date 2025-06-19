import json

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_series_equal

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
        assert list(level2_preproc._buffer.keys()) == [pd.Timestamp("2025-06-03 14:11:00"),
                                                       pd.Timestamp("2025-06-03 14:12:00")]

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
                "ts": pd.Timestamp("2025-06-03 14:11:00").value / 1_000_000,
                "bids": [[101, 1], [102, 2]],
                "asks": [[103, 3], [104, 4]]
            }
        }
        aggregated = await Level2Preproc()._aggregate([raw_msg])

        # Just ensure something is calculated, no need to test pandas mean function
        assert len(aggregated) == 1
        assert aggregated[0]["bid_max"] == 102

    @pytest.mark.asyncio
    async def test_htx_raw_to_pytrade2_raw_df_should_convert_empty_list(self):
        converted = await Level2Preproc()._htx_raw_to_pytrade2_raw_df([])
        assert converted is not None
        assert converted.empty

    @pytest.mark.asyncio
    async def test_htx_raw_to_pytrade2_raw_df_should_convert_list_of_single_msg(self):
        raw_msgs = [
            {
                "ch": "topic1",
                "tick": {
                    "ts": pd.Timestamp("2025-06-03 14:11:00").value / 1_000_000,
                    "bids": [[101, 1], [102, 2]],
                    "asks": [[103, 3], [104, 4]]
                }
            },
            {
                "ch": "topic1",
                "tick": {
                    "ts": pd.Timestamp("2025-06-03 14:12:00").value / 1_000_000,
                    "bids": [[201, 21], [202, 22]],
                    "asks": [[203, 23], [204, 24]]
                }
            },

        ]

        # Call conversion
        converted = await Level2Preproc()._htx_raw_to_pytrade2_raw_df(raw_msgs)

        # Assert that htx raw input converted to pytrade2 raw input, with a row per bid or ask
        assert converted.index.to_list() == [pd.Timestamp("2025-06-03 14:11:00")] * 4 + [
            pd.Timestamp("2025-06-03 14:12:00")] * 4
        assert_series_equal(converted["datetime"],
                            pd.Series([pd.Timestamp("2025-06-03 14:11:00")] * 4
                                      + [pd.Timestamp("2025-06-03 14:12:00")] * 4,
                                      name="datetime", index=converted.index)
                            .astype("datetime64[ms]"))
        assert_series_equal(converted["bid"],
                            pd.Series([101.0, 102.0, np.nan, np.nan, 201.0, 202.0, np.nan, np.nan], name="bid",
                                      index=converted.index))
        assert_series_equal(converted["bid_vol"],
                            pd.Series([1.0, 2.0, np.nan, np.nan, 21.0, 22.0, np.nan, np.nan], name="bid_vol",
                                      index=converted.index))

        assert_series_equal(converted["ask"],
                            pd.Series([np.nan, np.nan, 103.0, 104.0, np.nan, np.nan, 203.0, 204.0], name="ask",
                                      index=converted.index))
        assert_series_equal(converted["ask_vol"],
                            pd.Series([np.nan, np.nan, 3.0, 4.0, np.nan, np.nan, 23.0, 24.0], name="ask_vol",
                                      index=converted.index))
