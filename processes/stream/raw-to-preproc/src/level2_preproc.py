import asyncio
from dataclasses import dataclass

import pandas as pd

from preproc_base import PreprocBase
from process_stream_raw_to_preproc_metrics import ProcessStreamRawToPreprocMetrics


class Level2Preproc(PreprocBase):
    """ Accumulate Level 2 messages and aggregate them"""

    @dataclass
    class _PreprocMessageEntity:
        """ Intermediate entity for preprocessed level2 message inside a minute"""
        datetime: pd.Timestamp
        bid_max: float
        bid_vol_sum: float
        bid_mul_vol_sum: float
        bid_expect: float
        ask_min: float
        ask_vol_sum: float
        ask_mul_vol_sum: float
        ask_expect: float
        expect: float

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

        ts = pd.Timestamp(raw_message['tick']['ts'] , unit='ms')
        return self._PreprocMessageEntity(datetime=ts,
                                          bid_max=max(bids)[0], bid_vol_sum=bid_vol_sum,
                                          bid_mul_vol_sum=bid_mul_vol_sum,
                                          bid_expect=bid_expect, ask_min=min(asks)[0], ask_vol_sum=ask_vol_sum,
                                          ask_mul_vol_sum=ask_mul_vol_sum, ask_expect=ask_expect, expect=expect)
    #
    async def _aggregate(self, raw_messages: []) -> dict:
        """
        Aggregate accumulated messages within a minute.
        Method is called once a minute
        """
        if not raw_messages:
            return []
        transformed = [self._transform_message(msg) for msg in raw_messages]
        transformed = await asyncio.gather(*transformed)
        df_transformed = pd.DataFrame(transformed)
        df_aggregated = df_transformed.agg('mean')
        dt = df_transformed["datetime"].max()
        df_aggregated["datetime"] = str(dt)
        res = df_aggregated.to_dict()
        return res
