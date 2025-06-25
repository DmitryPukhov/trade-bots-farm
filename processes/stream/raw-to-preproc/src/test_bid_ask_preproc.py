import json

import pytest

from bid_ask_preproc import BidAskPreproc


class TestBidAskPreproc:
    @pytest.mark.asyncio
    async def test_bid_ask_preproc_good_message(self):
        raw_msg ={ "ch": "market.BTC-USDT.bbo",
            "ts": 1750851712043,
            "tick": {
                "bid": [
                    1,
                    2
                ],
                "ask": [
                    3,
                    4
                ],
                "ts": 1750851712041,
            }
        }
        processed_msg = await BidAskPreproc().process(json.dumps(raw_msg))[0]
        assert processed_msg["bid"] == 1
        assert processed_msg["bid_vol"] == 2
        assert processed_msg["ask"] == 3
        assert processed_msg["ask_vol"] == 4
        assert processed_msg["datetime"] =="2025-06-25 11:41:52.041000"

    @pytest.mark.asyncio
    async def test_bid_ask_preproc_empty(self):
        raw_msg ={ "ch": "market.BTC-USDT.bbo",
                   "ts": 1750851712043,
                   "tick": {
                       "bid": [
                           1,
                           2
                       ],
                       "ask": [
                           3,
                           4
                       ],
                       "ts": 1750851712041,
                   }
                   }
        processed_msg = await BidAskPreproc().process("{}")
        assert processed_msg == []
