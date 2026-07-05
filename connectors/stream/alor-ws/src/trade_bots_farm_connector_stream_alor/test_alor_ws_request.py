import json
import uuid

import pytest
from alor_ws_request import AlorWsRequest

class TestAlorWsRequest:
    @pytest.mark.asyncio
    async def test_subscribe_candles_1min(self):
        guid = str(uuid.uuid4())
        token = "token1"
        reqdump = await AlorWsRequest.subscribe_candles_1min_msg(token, guid, "MOEX.TQBR.SBER")
        req = json.loads(reqdump)
        assert req["guid"] == guid
        assert req["token"] == token

