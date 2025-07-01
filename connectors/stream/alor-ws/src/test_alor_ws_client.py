import json

import pytest

from alor_ws_client import AlorWsClient


class TestAlorWsClient:

    @pytest.mark.asyncio
    async def test__on_message_should_put_to_the_queue(self):
        client = AlorWsClient()
        for guid, queue in client._queue_dict.items():
            # on_message call
            msg = {"guid": guid, "value": "value1"}
            await client._on_message(msg)

            # Message should be put into the queue by it's guid
            assert queue.qsize() == 1
            item = queue.get_nowait()
            assert item == json.dumps(msg)

    @pytest.mark.asyncio
    async def test__on_message_should_ignore_unknown_guid(self):
        client = AlorWsClient()
        await client._on_message({"guid": "unknown", "value": "value1"})

        for queue in client._queue_dict.values():
            isempty = queue.empty()
            assert isempty
