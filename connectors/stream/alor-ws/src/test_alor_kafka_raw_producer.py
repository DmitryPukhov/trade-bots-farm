import asyncio

import pytest
from datetime import datetime
from alor_kafka_raw_producer import AlorKafkaRawProducer


class TestAlorKafkaRawProducer:
    @pytest.mark.asyncio
    async def test_get_time_field__time_seconds(self):
        original_dt = datetime(2025, 7, 1, 19, 32, second = 10)
        raw_message = {
            "data": {"t": original_dt.timestamp()}}


        producer = AlorKafkaRawProducer(asyncio.Queue(), asyncio.Queue(), asyncio.Queue())
        actual_dt = await producer._get_time_field(raw_message)
        assert actual_dt == original_dt

    @pytest.mark.asyncio
    async def test_get_time_field_timestamp_millis(self):
        for field in ["tso", "tst"]:
            original_dt = datetime(2025, 7, 1, 19, 32, second = 10, microsecond=123000)
            raw_message = {
                "data": {field: int(original_dt.timestamp()*1000)}}

            producer = AlorKafkaRawProducer(asyncio.Queue(), asyncio.Queue(), asyncio.Queue())
            actual_dt = await producer._get_time_field(raw_message)
            assert actual_dt == original_dt


    @pytest.mark.asyncio
    async def test_get_time_field__time_seconds(self):
        original_dt = datetime(2025, 7, 1, 19, 32, second = 10, microsecond=123000)
        raw_message = {
            "data": {"tso": int(original_dt.timestamp()*1000)}}

        producer = AlorKafkaRawProducer(asyncio.Queue(), asyncio.Queue(), asyncio.Queue())
        actual_dt = await producer._get_time_field(raw_message)
        assert actual_dt == original_dt
