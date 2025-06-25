import json

import pandas as pd


class BidAskPreproc:
    """ Process bbo message, don't accumulate"""

    async def process(self, raw_message: str) -> []:
        """ Process bbo message, don't accumulate """
        # Message example
        #     { "ch": "market.BTC-USDT.bbo",
        #     "ts": 1750851712043,
        #     "tick": {
        #         "mrid": 100061251400506,
        #         "id": 1750851712,
        #         "bid": [
        #             107073.5,
        #             2535
        #         ],
        #         "ask": [
        #             107073.6,
        #             11152
        #         ],
        #         "ts": 1750851712041,
        #         "version": 100061251400506,
        #         "ch": "market.BTC-USDT.bbo"
        #     },
        #     "datetime": "2025-06-25 11:41:52.041000+00:00"
        # }
        msg = json.loads(raw_message)
        bid, bid_vol = msg['tick']['bid']
        ask, ask_vol = msg['tick']['ask']
        dt = pd.Timestamp(msg["tick"]["ts"], unit='ms')

        return [{
            "datetime": str(dt),
            "bid": bid, "bid_vol": bid_vol, "ask": ask, "ask_vol": ask_vol
        }]
