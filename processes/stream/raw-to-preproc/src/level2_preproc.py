from dataclasses import dataclass

import pandas as pd

from preproc_base import PreprocBase
from pytrade2.features.level2.Level2Features import Level2Features


class Level2Preproc(PreprocBase):
    """ Accumulate Level 2 messages and aggregate them"""

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
        converted_raw_df = await self._htx_raw_to_pytrade2_raw_df(raw_messages)
        level2_df = Level2Features().expectation(converted_raw_df).resample("1min", label = "right", closed = "right").agg("mean")
        out_dict = level2_df.to_dict(orient='records')
        return out_dict
