import logging
import os

import pandas as pd
import s3fs

from candles_preproc import CandlesPreproc
from common.build.lib.common_tools import CommonTools
from level2_pytrade2_preproc import Level2PyTrade2Preproc
from s3_tools import S3Tools


class ProcessBatchRawToPreprocApp:

    def __init__(self):

        CommonTools.init_logging()

        self._src_s3_dir = os.environ["S3_SRC_DIR"]
        self._dst_s3_dir = os.environ["S3_DST_DIR"]
        self.kind = os.environ["KIND"]
        logging.info(
            f"{self.__class__.__name__} for {self.kind}, RAW_KIND={self.kind}Source: {self._src_s3_dir}, Destination: {self._dst_s3_dir}")

        self._preprocessor = self.create_preprocessor(self.kind)

        # S3 client
        self._s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL")
        # self._s3_bucket = os.environ.get("S3_BUCKET")
        self._s3_access_key = os.environ.get("S3_ACCESS_KEY")
        self._s3_secret_key = os.environ.get("S3_SECRET_KEY")
        self._s3_dir = os.environ.get("S3_DIR") or "data"

        self._s3_file_system = s3fs.S3FileSystem(endpoint_url=self._s3_endpoint_url,
                                                 key=self._s3_access_key,
                                                 secret=self._s3_secret_key)
        self.history_days_limit = int(os.environ.get("HISTORY_DAYS", "1"))

    def create_preprocessor(self, kind: str):
        """ Return preprocessor instance for specified kind of data"""
        match kind:
            case "level2":
                return Level2PyTrade2Preproc()
            case "candles":
                return CandlesPreproc()

    def _process_file(self, src_path: str, dst_path: str):
        """ Process single file from source folder, write result to destination folder """
        storage_options = {
            "key": self._s3_access_key,
            "secret": self._s3_secret_key,
            "client_kwargs": {"endpoint_url": self._s3_endpoint_url},
        }
        src_df = pd.read_csv(src_path, compression='zip', storage_options=storage_options)
        dst_df = self._preprocessor.process(src_df)
        dst_df.to_csv(dst_path, storage_options=storage_options)

    def run(self):
        logging.info(
            f"Preprocess s3 files in s3://{self._s3_endpoint_url}/{self._src_s3_dir}, "
            f"write result to s3://{self._s3_endpoint_url}/{self._dst_s3_dir}")
        # Get file names, not processed yet or updated in source folder
        files = S3Tools.find_updated_files(pd.Timestamp.now() - pd.Timedelta(days=self.history_days_limit),  # from
                                           pd.Timestamp.now(),  # to
                                           self._s3_file_system, self._src_s3_dir,
                                           self._s3_file_system, self._dst_s3_dir)
        total_files = len(files)
        logging.info(f"Found {total_files} files to process")
        for i, file_name in enumerate(files, 1):
            src_path = f"s3://{self._src_s3_dir}/{file_name}"
            dst_path = f"s3://{self._dst_s3_dir}/{file_name.rstrip(".zip")}"

            logging.info(f"Processing [{i}/{total_files}]. Read {src_path}, transform, write to {dst_path}")
            self._process_file(src_path, dst_path)


if __name__ == '__main__':
    ProcessBatchRawToPreprocApp().run()
