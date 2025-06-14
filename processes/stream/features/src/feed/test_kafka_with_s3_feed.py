# test_kafka_with_s3_feed.py
import asyncio

import pandas as pd
import pytest

from feed.kafka_with_s3_feed import KafkaWithS3Feed


class TestKafkaWithS3Feed:

    @pytest.mark.asyncio
    async def test_on_candle(self):
        feed = KafkaWithS3Feed("test", asyncio.Event())
        test_msg = {"close_time": "2020-01-01 00:00:00", "data": "test_data"}

        await feed.on_candle(test_msg)

        # Verify
        assert not feed._candles_buf.empty
        assert isinstance(feed._candles_buf, pd.DataFrame)
        assert pd.to_datetime("2020-01-01 00:00:00") in feed._candles_buf.index
        assert len(feed._candles_buf) == 1

    @pytest.mark.asyncio
    async def test_on_level2(self):
        feed = KafkaWithS3Feed("test", asyncio.Event())
        test_msg = {"datetime": "2020-01-01 00:00:00", "data": "test_data"}

        await feed.on_level2(test_msg)

        # Verify
        assert not feed._level2_buf.empty
        assert isinstance(feed._level2_buf, pd.DataFrame)
        assert pd.to_datetime("2020-01-01 00:00:00") in feed._level2_buf.index
        assert len(feed._level2_buf) == 1
