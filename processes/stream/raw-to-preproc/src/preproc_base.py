import json
import logging
import os
from collections import defaultdict

import pandas as pd
import sortedcontainers

from process_stream_raw_to_preproc_metrics import ProcessStreamRawToPreprocMetrics


class PreprocBase:
    """ Accumulate raw messages and aggregate them"""

    def __init__(self):
        self._buffer = defaultdict()
        self._buffer = sortedcontainers.SortedDict()
        self._order_timeout = pd.Timedelta(os.getenv("ORDER_TIMEOUT", "10s"))
        logging.info(f"{self.__class__.__name__} initialized with order timeout %s", self._order_timeout)

    async def process(self, raw_message: str) -> []:
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
        message_ts = pd.Timestamp(raw_message["tick"]["ts"], unit='ms') if "ts" in raw_message[
            "tick"] else pd.Timestamp(raw_message["ts"], unit="ms")  # noqa: E501

        start_minute_ts = message_ts.floor('1min')
        self._buffer.setdefault(start_minute_ts, []).append(raw_message)

        out = []
        # Check if previous minute is accumulated in the buffer
        buffer_min_ts = self._buffer.keys()[0]  # minimum start minute in buffer
        time_from_buffer_started = message_ts - buffer_min_ts
        # 1 previous minute should be accumulated in the buffer with order_timeout extra for late messages
        timeout_from_buffer_started = pd.Timedelta("1min") + self._order_timeout
        if time_from_buffer_started > timeout_from_buffer_started:
            # Process buffer minutes except current one (one previous minute)
            for buf_start_minute_ts, buf_messages in self._buffer.items()[:-1]:
                out.append(self._aggregate(buf_messages))
                del self._buffer[buf_start_minute_ts]

        # Set metrics
        ProcessStreamRawToPreprocMetrics.time_lag_sec.labels(raw_message["ch"]).set((pd.Timestamp.utcnow() - message_ts.tz_localize("utc")).total_seconds())
        return out

    async def _aggregate(self, messages: []):
        """
        Aggregate accumulated messages within a minute.
        Method is called once a minute
        To be implemented by subclasses
        """
        raise NotImplementedError()
