# test_kafka_with_s3_feed.py
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pandas as pd
import pytest

from feed.kafka_with_s3_feed import KafkaWithS3Feed


class TestKafkaWithS3Feed:


    @pytest.mark.asyncio
    async def test_on_candle(self):
        from feed.kafka_with_s3_feed import KafkaWithS3Feed
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
        from feed.kafka_with_s3_feed import KafkaWithS3Feed
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
        from feed.kafka_with_s3_feed import KafkaWithS3Feed
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
        from feed.kafka_with_s3_feed import KafkaWithS3Feed
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
        from feed.kafka_with_s3_feed import KafkaWithS3Feed
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
    async def test_processing_loop_should_flush_both_buffers(self):
        from feed.kafka_with_s3_feed import KafkaWithS3Feed
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

    @pytest.fixture
    def mock_s3_feed(self):
        """Fixture to create a mock S3Feed instance"""
        mock = AsyncMock()
        mock.read_history.return_value = pd.DataFrame({
            "timestamp": [pd.Timestamp("2025-06-15 02:50:00")],
            "value": [100]
        })
        return mock

    @pytest.fixture
    def mock_kafka_feed(self):
        """Fixture to create a mock KafkaFeed instance"""
        mock = AsyncMock()
        mock.run = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_processing_loop_should_set_kafka_offsets_to_last_s3_data(self, mock_s3_feed, mock_kafka_feed):

        mock_s3_feed.read_history.side_effect = [
            # Initial call to load data from S3
            pd.DataFrame([{"datetime": pd.Timestamp("2025-06-15 02:45:00")}]).set_index("datetime", drop=False),
            # Second call to load additional data from S3 to close time gap
            pd.DataFrame([{"datetime": pd.Timestamp("2025-06-15 02:50:00")}]).set_index("datetime", drop=False),
        ]

        with patch("feed.kafka_with_s3_feed.S3Feed", return_value=mock_s3_feed), \
                patch("feed.kafka_with_s3_feed.KafkaFeed", return_value=mock_kafka_feed):

            feed = KafkaWithS3Feed("test", asyncio.Event())
            feed._initial_history_reload_interval = pd.Timedelta(0)

            # Prepare kafka stream emulation
            new_candle = {"close_time": "2020-06-15 02:55", "close": 100}
            new_level2 = {"datetime": "2020-06-15 02:55:00", "bid": 200}
            await feed._candles_queue.put(new_candle)
            await feed._level2_queue.put(new_level2)

            with pytest.raises(asyncio.TimeoutError):

                # Run the feed under test for a while
                await asyncio.wait_for(feed.run_async(), 0.5)

            # Verify that feed tried to get previous kafka data just after s3 data ended
            mock_kafka_feed.run.assert_called_with(start_time=pd.Timestamp("2025-06-15 02:45:00"))
            # todo: verify that it was called twice
            #mock_s3_feed.read_history.assert_called_with(end_time=[pd.Timestamp("2025-06-15 02:55:00")])

