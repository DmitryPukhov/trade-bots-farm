import asyncio
import logging
import os

import pandas as pd
import s3fs

from connector_batch_s3_external_metrics import ConnectorBatchS3ExternalMetrics
from s3_tools import S3Tools


class HistoryS3Downloader:
    """
    Download necessary history data from s3
    """

    def __init__(self):
        # Configure s3
        self._src_s3_endpoint_url = os.environ.get("SRC_S3_ENDPOINT_URL")
        self._src_s3_access_key = os.environ.get("SRC_S3_ACCESS_KEY")
        self._src_s3_secret_key = os.environ.get("SRC_S3_SECRET_KEY")
        self._src_s3_dir = os.environ.get("SRC_S3_DIR")

        self._dst_s3_endpoint_url = os.environ.get("DST_S3_ENDPOINT_URL")
        self._dst_s3_access_key = os.environ.get("DST_S3_ACCESS_KEY")
        self._dst_s3_secret_key = os.environ.get("DST_S3_SECRET_KEY")
        self._dst_s3_dir = os.environ.get("DST_S3_DIR")
        logging.info(f"Source s3: {self._src_s3_endpoint_url}/{self._src_s3_dir}")
        logging.info(f"Destination s3: {self._dst_s3_endpoint_url}/{self._dst_s3_dir}")

        # Create s3 clients for external and internal s3
        self._s3_external_fs = s3fs.S3FileSystem(client_kwargs={"endpoint_url": self._src_s3_endpoint_url},
                                                 key=self._src_s3_access_key,
                                                 secret=self._src_s3_secret_key)
        self._s3_internal_fs = s3fs.S3FileSystem(client_kwargs={"endpoint_url": self._dst_s3_endpoint_url},
                                                 key=self._dst_s3_access_key,
                                                 secret=self._dst_s3_secret_key)
        self._file_download_attempts = os.environ.get("FILE_DOWNLOAD_ATTEMPTS", 3)
        self._file_download_attempts_delay_seconds = os.environ.get("FILE_DOWNLOAD_ATTEMPTS_DELAY_SECONDS", 60)


    async def _transfer_file(self, external_s3_dir: str, internal_s3_dir: str, file_name: str):
        """ Download a single file from external S3 to internal S3 """

        src_path = f"{external_s3_dir}/{file_name}"
        dst_path = f"{internal_s3_dir}/{file_name}"
        is_downloaded = False
        for attempt in range(1, self._file_download_attempts + 1):
            try:
                logging.info(f"Downloading {self._s3_external_fs.client_kwargs['endpoint_url']}/{src_path} to {dst_path}")
                with self._s3_external_fs.open(src_path, 'rb') as src_file:
                    with self._s3_internal_fs.open(dst_path, 'wb') as dest_file:
                        dest_file.write(src_file.read())
                is_downloaded = True
            except Exception as e:
                # Log error and retry
                logging.error(f"Attempt {attempt}/{self._file_download_attempts} failed to download {src_path} to {dst_path}. {e}")
                logging.info(f"Waiting {self._file_download_attempts_delay_seconds} seconds before retry to download {src_path}")
                await asyncio.sleep(self._file_download_attempts_delay_seconds)

        if not is_downloaded:
            raise IOError(f"Failed to download {src_path} to {dst_path} in {self._file_download_attempts} attempts")

    async def update_local_history(self, start_date=pd.Timestamp.min, end_date=pd.Timestamp.max):
        """ Download new history data from external s3 to internal s3.
        :returns: True if any files were downloaded, False otherwise.
        """

        # Reset metrics
        ConnectorBatchS3ExternalMetrics.files_transferred.labels(external_s3_dir=self._src_s3_dir).reset()
        await ConnectorBatchS3ExternalMetrics.push_to_gateway_()

        # Determine what to download
        logging.info(
            f"Downloading history data from  {self._src_s3_endpoint_url}/{self._src_s3_dir} "
            f"to {self._dst_s3_endpoint_url}/{self._dst_s3_dir}")
        logging.info(f"Consider only period [{start_date}, {end_date}]")
        # Get list of files to download
        download_list = S3Tools.find_updated_files(start_date, end_date,
                                                   self._s3_external_fs, self._src_s3_dir,
                                                   self._s3_internal_fs, self._dst_s3_dir)
        # Download one by one. s3fs does not support async transfer, do it synchronously
        total_count = len(download_list)
        logging.info(f"Found {total_count} files to download")
        for i, file_name in enumerate(download_list, start=1):
            logging.info(
                f"Downloading  [{i}/{total_count}] {self._s3_external_fs.client_kwargs.get("endpoint_url")}/{self._src_s3_dir}/{file_name} "
                f"to {self._s3_internal_fs.client_kwargs.get("endpoint_url")}/{self._dst_s3_dir}/{file_name}")
            await self._transfer_file(self._src_s3_dir, self._dst_s3_dir, file_name)
            ConnectorBatchS3ExternalMetrics.files_transferred.labels(external_s3_dir=self._src_s3_dir).inc()

            await asyncio.sleep(0)
        logging.info("Download completed")
