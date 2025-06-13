import asyncio
import logging
import os

import pandas as pd

from common_tools import CommonTools
from connector_batch_s3_external_metrics import ConnectorBatchS3ExternalMetrics
from history_s3_downloader import HistoryS3Downloader


class ConnectorBatchS3ExternalApp:
    """ Main class"""

    def __init__(self):
        CommonTools.init_logging()
        self._history_s3_downloader = HistoryS3Downloader()
        self.history_days_limit = int(os.environ.get("HISTORY_DAYS", "1"))
        self._metrics = ConnectorBatchS3ExternalMetrics()
        logging.info(f"Updating history from HISTORY_DAYS = {self.history_days_limit}")

    async def run_async(self):
        self._metrics.job_runs.inc()
        # Start the periodic metrics push (properly managed)
        metrics_task = asyncio.create_task(
            self._metrics.push_to_gateway_periodical()
        )
        await self._history_s3_downloader.update_local_history(
            start_date=pd.Timestamp.now() - pd.Timedelta(days=self.history_days_limit)
        )
        self._metrics.run_flag = False


    def run(self):
        asyncio.run(self.run_async())

if __name__ == '__main__':
    ConnectorBatchS3ExternalApp().run()
