import logging
import os

import pandas as pd

from history_s3_downloader import HistoryS3Downloader


class ConnectorBatchS3ExternalApp:
    """ Main class"""

    def __init__(self):
        self._init_logging()
        self._history_s3_downloader = HistoryS3Downloader()
        self.tickers = [ticker.strip() for ticker in os.environ.get("TICKERS").split(",")]
        self.kinds = [kind.strip() for kind in os.environ.get("KINDS", "level2,candles,bid_ask").split(",")]
        self.history_days_limit = int(os.environ.get("HISTORY_DAYS_LIMIT", "1"))
        logging.info(f"Updating history for tickers: {self.tickers} and kinds: {self.kinds}. History days limit: {self.history_days_limit}")

    def _init_logging(self):
        # Setup logging
        logging.basicConfig(
            level=os.environ.get("LOG_LEVEL") or logging.INFO,
            format='%(asctime)s -  %(module)s.%(funcName)s:%(lineno)d  - %(levelname)s - %(message)s'
        )

    def run(self):
        self._history_s3_downloader.update_local_history(tickers=self.tickers, kinds=self.kinds,
                                                         start_date=pd.Timestamp.now() - pd.Timedelta(days=self.history_days_limit))



if __name__ == '__main__':
    ConnectorBatchS3ExternalApp().run()
