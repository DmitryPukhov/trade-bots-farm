import logging
import os

import pandas as pd

from common_tools import CommonTools
from history_s3_downloader import HistoryS3Downloader


class ConnectorBatchS3ExternalApp:
    """ Main class"""

    def __init__(self):
        CommonTools.init_logging()
        self._history_s3_downloader = HistoryS3Downloader()
        self.history_days_limit = int(os.environ.get("HISTORY_DAYS", "1"))
        self._metrics_port = os.getenv('METRICS_PORT', 8000)
        logging.info(f"Updating history from HISTORY_DAYS = {self.history_days_limit}")

    def run(self):
        self._history_s3_downloader.update_local_history(
            start_date=pd.Timestamp.now() - pd.Timedelta(days=self.history_days_limit))


if __name__ == '__main__':
    ConnectorBatchS3ExternalApp().run()
