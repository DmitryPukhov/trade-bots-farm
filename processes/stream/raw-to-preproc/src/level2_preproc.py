from dataclasses import dataclass

import pandas as pd

from preproc_base import PreprocBase


class Level2Preproc(PreprocBase):
    """ Accumulate Level 2 messages and aggregate them"""

    @dataclass
    class _PreprocMessageEntity:
        """ Intermediate entity for preprocessed level2 message inside a minute"""
        bid_max: float
        bid_vol_sum: float
        bid_mul_vol_sum: float
        bid_expect: float
        ask_min: float
        ask_vol_sum: float
        ask_mul_vol_sum: float
        ask_expect: float
        expect: float

    def _transform_message(self, raw_message) -> _PreprocMessageEntity:
        """ Calculates big, ask, bid/ask expectations and returns them"""
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

        return self._PreprocMessageEntity(bid_max=max(bids)[0], bid_vol_sum=bid_vol_sum,
                                          bid_mul_vol_sum=bid_mul_vol_sum,
                                          bid_expect=bid_expect, ask_min=min(asks)[0], ask_vol_sum=ask_vol_sum,
                                          ask_mul_vol_sum=ask_mul_vol_sum, ask_expect=ask_expect, expect=expect)

    def _aggregate(self, raw_messages: []) -> dict:
        """
        Aggregate accumulated messages within a minute.
        Method is called once a minute
        """
        transformed = (self._transform_message(msg) for msg in raw_messages)
        df_transformed = pd.DataFrame(transformed)
        df_aggregated = df_transformed.agg('mean')
        res =  df_aggregated.to_dict()
        return res
