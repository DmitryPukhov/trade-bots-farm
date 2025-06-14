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

    @pytest.mark.asyncio
    async def test_flush_buffers_should_flush_both_buffers_exact_time(self):
        feed = KafkaWithS3Feed("test", asyncio.Event())

        # Fill buffers
        new_candle = {"close_time": "2020-01-01 00:00:00", "close": 100}
        await feed.on_candle(new_candle)
        new_level2 = {"datetime": "2020-01-01 00:00:00", "bid": 200}
        await feed.on_level2(new_level2)

        # Call the method under test
        await feed.flush_buffers()

        # Verify buffers are empty
        assert feed._candles_buf.empty
        assert feed._level2_buf.empty

        # Verify the data
        assert not feed.data.empty
        assert len(feed.data) == 1
        assert pd.to_datetime("2020-01-01 00:00:00") in feed.data.index
        assert feed.data["close"].iloc[0] == 100
        assert feed.data["bid"].iloc[0] == 200

    @pytest.mark.asyncio
    async def test_flush_buffers_should_flush_both_buffers_with_small_time_diff(self):
        feed = KafkaWithS3Feed("test", asyncio.Event())

        # Fill buffers
        new_candle = {"close_time": "2020-01-01 00:00:00", "close": 100}
        await feed.on_candle(new_candle)
        # time is 59 seconds later than candle time, but still in 59 seconds merge tolerance. 1 minute would be too big
        new_level2 = {"datetime": "2020-01-01 00:00:59", "bid": 200}
        await feed.on_level2(new_level2)

        # Call the method under test
        await feed.flush_buffers()

        # Verify buffers are empty
        assert feed._candles_buf.empty
        assert feed._level2_buf.empty

        # Verify the data
        assert not feed.data.empty
        assert len(feed.data) == 1
        assert pd.to_datetime("2020-01-01 00:00:59") in feed.data.index
        assert feed.data["close"].iloc[0] == 100
        assert feed.data["bid"].iloc[0] == 200

    @pytest.mark.asyncio
    async def test_flush_buffers_should_not_flush_if_too_big_time_diff(self):
        feed = KafkaWithS3Feed("test", asyncio.Event())

        # Fill buffers
        new_candle = {"close_time": "2020-01-01 00:00:00", "close": 100}
        await feed.on_candle(new_candle)
        # time is 1 minute later, out of merge tolerance, no merge
        new_level2 = {"datetime": "2020-01-01 00:01:00", "bid": 200}
        await feed.on_level2(new_level2)

        # Call the method under test
        await feed.flush_buffers()

        # Verify buffers are empty
        assert feed.data.empty
        assert not feed._candles_buf.empty
        assert not feed._level2_buf.empty

    @pytest.mark.asyncio
    async def test_processing_loop(self):
        feed = KafkaWithS3Feed("test", asyncio.Event())

        # Fill buffers
        new_candle = {"close_time": "2020-01-01 00:00:00", "close": 100}
        new_level2 = {"datetime": "2020-01-01 00:00:00", "bid": 200}
        # Put messages in queues (non-blocking)
        await feed._candles_queue.put(new_candle)
        await feed._level2_queue.put(new_level2)
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(feed.processing_loop(), 0.5)

        # Simple verify that buffers are flushed
        assert feed._candles_buf.empty
        assert feed._level2_buf.empty
        assert not feed.data.empty

