import json
import logging
import os
from collections import defaultdict

import pandas as pd
import sortedcontainers


class PreprocBase:
    """ Accumulate raw messages and aggregate them"""

    def __init__(self):
        self._buffer = defaultdict()
        self._buffer = sortedcontainers.SortedDict()
        self._order_timeout = pd.Timedelta(os.getenv("ORDER_TIMEOUT", "10s"))
        logging.info(f"{self.__class__.__name__} initialized with order timeout %s", self._order_timeout)

    def process(self, raw_message: str):
        """ Process a raw message, returns processed messages if time comes or [] if not
         Example of raw message
         {
             "ch": "market.BTC-USDT.depth.step13",
             "ts": 1748795596110,
             "tick": {
                 "mrid": 100059369495645,
                 "id": 1748795596,
                 "bids": [[105030,7592],[105020,9324],[105010,633],[105000,6916],[104990,12448],[104980,3072],[104970,5177],[104960,9202],[104950,15168],[104940,594],[104930,560],[104920,3082],[104910,15063],[104900,9913],[104890,19030],[104880,2136],[104870,1375],[104860,397],[104850,1410],[104840,1284]
                 ],
                 "asks": [[105040,1653],[105050,1408],[105060,5919],[105070,2932],[105080,9737],[105090,9034],[105100,3171],[105110,22793],[105120,2914],[105130,1672],[105140,5804],[105150,15920],[105160,14369],[105170,2688],[105180,8740],[105190,3576],[105200,2328],[105210,289],[105220,500],[105230,1218]
                 ],
                 "ts": 1748795596089,
                 "version": 1748795596,
                 "ch": "market.BTC-USDT.depth.step13"
             }
         }
        """

        # Add to buffer
        raw_message = json.loads(raw_message)
        message_ts = pd.Timestamp(raw_message["tick"]["id"], unit='ms')
        start_minute_ts = message_ts.floor('1min')
        self._buffer.setdefault(start_minute_ts, []).append(raw_message)

        out = []
        # Process previous minute if ordering timeout is passed
        if message_ts - start_minute_ts > self._order_timeout:
            # If we have previous minute in the bufferr, process it
            # sorted_keys = sorted(self._buffer.keys())
            while len(self._buffer) > 1:
                cur_minute_ts = next(iter(self._buffer))
                cur_minute_messages = self._buffer[cur_minute_ts]
                out.append(self._aggregate(cur_minute_messages))
                del self._buffer[cur_minute_ts]

        return out

    def _aggregate(self, messages: []):
        """
        Aggregate accumulated messages within a minute.
        Method is called once a minute
        To be implemented by subclasses
        """
        raise NotImplementedError()
