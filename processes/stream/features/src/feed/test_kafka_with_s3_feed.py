# test_kafka_with_s3_feed.py
import asyncio
from unittest.mock import AsyncMock, patch, call

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
        return AsyncMock()

    @pytest.fixture
    def mock_kafka_feed(self):
        """Fixture to create a mock KafkaFeed instance"""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_processing_loop_should_set_kafka_offsets_to_last_s3_data(self, mock_s3_feed, mock_kafka_feed):

        # Configure the mock S3Feed to return the desired data
        mock_s3_feed.read_history.side_effect = [
            pd.DataFrame([{"datetime": pd.Timestamp("2025-06-15 02:45:00")}]).set_index("datetime", drop=False),
            pd.DataFrame([{"datetime": pd.Timestamp("2025-06-15 02:55:00")}]).set_index("datetime", drop=False)]

        with patch("feed.kafka_with_s3_feed.S3Feed", return_value=mock_s3_feed), \
                patch("feed.kafka_with_s3_feed.KafkaFeed", return_value=mock_kafka_feed):

            # This feed is under test
            feed = KafkaWithS3Feed("test", asyncio.Event())
            feed._initial_history_reload_interval = pd.Timedelta(0)

            # Kafka stream feed emulation
            await feed._candles_queue.put({"close_time": "2025-06-15 02:55", "close": 100})
            await feed._level2_queue.put({"datetime": "2025-06-15 02:55:00", "bid": 200})
            await feed._candles_queue.put({"close_time": "2025-06-15 02:56", "close": 100})
            await feed._level2_queue.put({"datetime": "2025-06-15 02:56:00", "bid": 200})

            # Run the feed for a while
            with pytest.raises(asyncio.TimeoutError):
                # Run the feed under test for a while
                await asyncio.wait_for(feed.run_async(), 0.1)

            # Initial history load + next loads because stream data is too late after S3
            assert mock_s3_feed.read_history.call_count == 2

            # Assert initial call to load data from S3
            assert mock_s3_feed.read_history.call_args_list[0] == call(
                start_date=pd.Timestamp.min.date(), end_date=pd.Timestamp.max.date(), modified_after=pd.Timestamp.min)

            # Assert incremental call to load data from S3 up to the beginning of the stream data
            assert mock_s3_feed.read_history.call_args_list[1] == call(
                start_date=pd.Timestamp("2025-06-15").date(), end_date=pd.Timestamp("2025-06-15").date(),
                modified_after=pd.Timestamp("2025-06-15 02:55:00"))

            assert feed.data.index.tolist() == [pd.Timestamp("2025-06-15 02:45:00"),
                                                pd.Timestamp("2025-06-15 02:55:00"),
                                                pd.Timestamp("2025-06-15 02:56:00"),
                                                ]
