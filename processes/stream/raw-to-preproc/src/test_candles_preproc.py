import json

import pandas as pd
import pytest

from candles_preproc import CandlesPreproc


class TestCandlesPreproc:
    @pytest.mark.asyncio
    async def test_process(self):
        ts1 = pd.Timestamp("2025-06-03 14:11:00")
        ts2 = pd.Timestamp("2025-06-03 14:12:10")
        ts3 = pd.Timestamp("2025-06-03 14:12:11")

        msg = {
            "ch": "topic1",
            "ts": ts1.value // 1_000_000,  # nanos to millis
            "tick": {
                # "id": ts1.value // 1_000_000,  # nanos to millis
                "open": 100,
                "high": 102,
                "low": 100,
                "close": 101,
                "amount": 1000
            }
        }

        candles_preproc = CandlesPreproc()

        # Accumulate minute 1, don't process
        msg["ts"] = ts1.value // 1_000_000
        res = await candles_preproc.process(json.dumps(msg))
        preprocessed = pd.DataFrame(res)
        assert preprocessed.empty
        # self.assertTrue(preprocessed.empty)
        # self.assertListEqual([pd.Timestamp("2025-06-03 14:11:00")], list(candles_preproc._buffer.keys()))
        assert list(candles_preproc._buffer.keys()) == [pd.Timestamp("2025-06-03 14:11:00")]

        # Accumulate minute 2, don't process minute 1 because of timeout not elapsed
        msg["ts"] = ts2.value // 1_000_000
        preprocessed = pd.DataFrame(await candles_preproc.process(json.dumps(msg)))
        assert preprocessed.empty
        assert [pd.Timestamp("2025-06-03 14:11:00"), pd.Timestamp("2025-06-03 14:12:00")] == \
               list(candles_preproc._buffer.keys())

        # Accumulate minute 2, process minute 1 and delete from buffer
        msg["ts"] = ts3.value // 1_000_000
        preprocessed = pd.DataFrame(await candles_preproc.process(json.dumps(msg)))
        assert len(preprocessed) == 1
        assert list(candles_preproc._buffer.keys()) == [pd.Timestamp("2025-06-03 14:12:00")]

    @pytest.mark.asyncio
    async def test_aggregate_empty(self):
        aggregated = await CandlesPreproc()._aggregate([])
        assert len(aggregated) == 0

    @pytest.mark.asyncio
    async def test_process_candles(self):
        raw_msgs = [
            {"ts": pd.Timestamp("2025-06-03 14:11:01").value // 1_000_000,
             "tick": {
                 "open": 100,
                 "high": 102,
                 "low": 98,
                 "close": 110,
                 "amount": 1000
             }},
            {
                "ts": pd.Timestamp("2025-06-03 14:11:30").value // 1_000_000,
                "tick": {
                    "open": 120,
                    "high": 103,
                    "low": 99,
                    "close": 101,
                    "amount": 50
                }},
            {
                "ts": pd.Timestamp("2025-06-03 14:12").value // 1_000_000,
                "tick": {
                    "open": 110,
                    "high": 104,
                    "low": 97,
                    "close": 120,
                    "amount": 2000
                }},
            {
                "ts": pd.Timestamp("2025-06-03 14:12:01").value // 1_000_000,
                "tick": {
                    "open": 200,
                    "high": 300,
                    "low": 100,
                    "close": 210,
                    "amount": 500
                }}
        ]
        aggregated = await CandlesPreproc()._aggregate(raw_msgs)

        # Just ensure something is calculated, no need to test pandas mean function
        assert len(aggregated) == 2
        # Last candle in 14:11-14:12 interval, closed at 14:12:00
        assert aggregated[0]["open_time"] == "2025-06-03 14:11:00"
        assert aggregated[0]["close_time"] == "2025-06-03 14:12:00"
        assert aggregated[0]["open"] == 110
        assert aggregated[0]["high"] == 104
        assert aggregated[0]["low"] == 97
        assert aggregated[0]["close"] == 120
        assert aggregated[0]["vol"] == 2000
        # Last candle in 14:12-14:1 interval, closed at 14:13:00
        assert aggregated[1]["open_time"] == "2025-06-03 14:12:00"
        assert aggregated[1]["close_time"] == "2025-06-03 14:13:00"
        assert aggregated[1]["open"] == 200
        assert aggregated[1]["high"] == 300
        assert aggregated[1]["low"] == 100
        assert aggregated[1]["close"] == 210
        assert aggregated[1]["vol"] == 500
