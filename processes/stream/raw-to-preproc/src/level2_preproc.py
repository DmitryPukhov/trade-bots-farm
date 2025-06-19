from dataclasses import dataclass

import pandas as pd

from preproc_base import PreprocBase
from pytrade2.features.level2.Level2Features import Level2Features


class Level2Preproc(PreprocBase):
    """ Accumulate Level 2 messages and aggregate them"""

    @dataclass
    class _PreprocMessageEntity:
        """ Intermediate entity for preprocessed level2 message inside a minute"""
        datetime: pd.Timestamp
        l2_bid_max: float
        l2_bid_vol_sum: float
        l2_bid_mul_vol_sum: float
        l2_bid_expect: float
        l2_ask_min: float
        l2_ask_vol_sum: float
        l2_ask_mul_vol_sum: float
        l2_ask_expect: float
        l2_expect: float

    async def _transform_message(self, raw_message) -> _PreprocMessageEntity:
        """ Calculates big, ask, bid/ask expectations and returns them"""
        #
        # level2_tick_df = pd.DataFrame([msg["tick"] for msg in raw_messages]).copy()
        # level2_raw_df = level2_tick_df[["bids", "asks", "ts"]]
        # level2_raw_df.columns = ["bids", "asks", "datetime"]
        # transformed_df  = Level2Features().expectation(level2_raw_df)
        # if len(transformed_df) > 1:
        #     raise ValueError("Messages, accumulated for aggregation should be inside a minute")
        # return transformed_df.to_dict(orient='records')
        # Bid expectation calculation
        bids = raw_message['tick']['bids']
        bid_vol_sum = sum([vol for _, vol in bids])
        bid_mul_vol_sum = sum([bid * vol for bid, vol in bids])
        bid_expect = bid_mul_vol_sum / bid_vol_sum

        # Ask expectation calculation
        asks = raw_message['tick']['asks']
        ask_vol_sum = sum([vol for _, vol in asks])
        ask_mul_vol_sum = sum([ask * vol for ask, vol in asks])
        ask_expect = ask_mul_vol_sum / ask_vol_sum

        # Bidask expectation
        expect = (ask_mul_vol_sum - bid_mul_vol_sum) / (ask_vol_sum + bid_vol_sum)

        ts = pd.Timestamp(raw_message['tick']['ts'], unit='ms')
        return self._PreprocMessageEntity(datetime=ts,
                                          l2_bid_max=max(bids)[0], l2_bid_vol_sum=bid_vol_sum,
                                          l2_bid_mul_vol_sum=bid_mul_vol_sum,
                                          l2_bid_expect=bid_expect, l2_ask_min=min(asks)[0], l2_ask_vol_sum=ask_vol_sum,
                                          l2_ask_mul_vol_sum=ask_mul_vol_sum, l2_ask_expect=ask_expect,
                                          l2_expect=expect)

    @staticmethod
    async def _htx_raw_to_pytrade2_raw_df(htx_raw_messages: [dict]) -> [dict]:
        # Extract bids and asks from htx raw messages
        pytrade2_rows = []
        for htx_raw_message in htx_raw_messages:
            dt = pd.Timestamp(htx_raw_message["tick"]["ts"], unit='ms')
            bids = [{"datetime": dt, "bid": bid[0], "bid_vol": bid[1]} for bid in htx_raw_message["tick"]["bids"]]
            pytrade2_rows.extend(bids)
            asks = [{"datetime": dt, "ask": ask[0], "ask_vol": ask[1]} for ask in htx_raw_message["tick"]["asks"]]
            pytrade2_rows.extend(asks)

        # Convert to dataframe
        pytrade2_df = pd.DataFrame(pytrade2_rows, columns =["datetime", "bid", "bid_vol", "ask", "ask_vol"])
        pytrade2_df["datetime"] = pytrade2_df["datetime"].astype('datetime64[ms]')
        pytrade2_df = pytrade2_df.set_index('datetime', drop=False)
        return pytrade2_df

    async def _aggregate(self, raw_messages: []) -> []:
        """
        Aggregate accumulated messages within a minute.
        Method is called once a minute
        """
        if not raw_messages:
            return []
        raw_df = self._htx_raw_to_pytrade2_raw_df(raw_messages)
        level2_df = Level2Features().expectation(raw_df)
        res = level2_df.to_dict(orient='records')
        return res
