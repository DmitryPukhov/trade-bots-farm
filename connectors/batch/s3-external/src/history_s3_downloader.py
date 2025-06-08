import logging
import os
import tempfile

import boto3
import pandas as pd

from s3_tools import S3Tools


class HistoryS3Downloader:
    """
    Download necessary history data from s3
    """

    def __init__(self):
        # Try feed specific s3 config then global s3 config
        # Configure s3
        self._external_s3_endpoint_url = os.environ.get("EXTERNAL_S3_ENDPOINT_URL")
        self._external_s3_bucket = os.environ.get("EXTERNAL_S3_BUCKET")
        self._external_s3_access_key = os.environ.get("EXTERNAL_S3_ACCESS_KEY")
        self._external_s3_secret_key = os.environ.get("EXTERNAL_S3_SECRET_KEY")
        self._external_s3_data_prefix = os.environ.get("EXTERNAL_S3_DATA_PREFIX") or "data"

        self._s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL")
        self._s3_bucket = os.environ.get("S3_BUCKET")
        self._s3_access_key = os.environ.get("S3_ACCESS_KEY")
        self._s3_secret_key = os.environ.get("S3_SECRET_KEY")
        self._s3_data_prefix = os.environ.get("S3_DATA_PREFIX") or "data"
        logging.info(
            f"External s3: {os.path.join(self._external_s3_endpoint_url, self._external_s3_bucket, self._external_s3_data_prefix)}")
        logging.info(f"Internal s3: {os.path.join(self._s3_endpoint_url, self._s3_bucket, self._s3_data_prefix)}")

        # Create s3 clients for external and internal s3
        session = boto3.session.Session()
        self._s3_client = session.client(service_name='s3', endpoint_url=self._s3_endpoint_url,
                                         aws_access_key_id=self._s3_access_key,
                                         aws_secret_access_key=self._s3_secret_key)

        self._s3_external_client = session.client(service_name='s3', endpoint_url=self._external_s3_endpoint_url,
                                                  aws_access_key_id=self._external_s3_access_key,
                                                  aws_secret_access_key=self._external_s3_secret_key)

    def _download_file(self, external_s3_dir: str, internal_s3_dir: str, file_name: str):
        """ Download a single file from external S3 to internal S3 """

        external_file_key = os.path.join(external_s3_dir, file_name)
        internal_file_key = os.path.join(internal_s3_dir, file_name)
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name

                # Download from S3 to temp file
                self._s3_external_client.download_file(
                    Bucket=self._external_s3_bucket,
                    Key=external_file_key,
                    Filename=temp_path
                )

                # Upload from temp file to MinIO
                self._s3_client.upload_file(
                    Filename=temp_path,
                    Bucket=self._s3_bucket,
                    Key=internal_file_key,
                    ExtraArgs={
                        'ContentType': self._s3_external_client.head_object(
                            Bucket=self._external_s3_bucket,
                            Key=external_file_key
                        )['ContentType']
                    }
                )
                # Clean up
                os.unlink(temp_path)

        except Exception as e:
            # Ensure temp file is cleaned up even on error
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def update_local_history(self, tickers: [str], kinds=("level2", "candles", "bid_ask"),
                             start_date=pd.Timestamp.min, end_date=pd.Timestamp.max):
        """ Download new history data from s3 to local data directory.
        :returns: True if any files were downloaded, False otherwise.
        """
        logging.info(
            f"Downloading new data from {self._external_s3_bucket}/{self._external_s3_data_prefix} to {self._s3_bucket}/{self._s3_data_prefix}")
        for ticker in tickers:
            for kind in kinds:
                # Get list of files to download
                external_s3_dir = os.path.join(self._external_s3_data_prefix, "raw", kind)
                internal_s3_dir = os.path.join(self._s3_data_prefix, "raw", kind)
                download_list = S3Tools.find_updated_files(start_date, end_date,
                                                           self._s3_external_client, self._external_s3_bucket, self._external_s3_data_prefix,
                                                           self._s3_client, self._s3_bucket, self._s3_data_prefix,)
                total_count = len(download_list)
                logging.info(f"Found {total_count} {kind} files to download")
                for i, file_name in enumerate(download_list, start=1):
                    logging.info(
                        f"Downloading {kind} {i} of {total_count} files to s3://{self._s3_bucket}/{internal_s3_dir}/{file_name}")
                    self._download_file(external_s3_dir, internal_s3_dir, file_name)
        logging.info("Download completed")
