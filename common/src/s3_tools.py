import logging
from datetime import date

import pandas as pd
import s3fs


class S3Tools:
    @staticmethod
    def find_daily_files(file_system: s3fs.S3FileSystem, s3_dir: str, start_date, end_date) -> list[str]:
        # modified time: file name dictionary
        modified_dict = {}

        # List objects in the bucket
        if not file_system.exists(f"{s3_dir}"):
            logging.info(f"Skipping file search in {s3_dir}, it doesn't exist")
            return modified_dict

        # Get all files in the directory with date in name between start_date and end_date inclusive.
        file_names = [obj['Key'] for obj in file_system.listdir(s3_dir)]
        files_in_date_range = [name for name in file_names if
                               start_date <= S3Tools.get_file_date_from_name(name) <= end_date]

        logging.info(f"Found {len(files_in_date_range)} files in {s3_dir} between {start_date} and {end_date}")
        return sorted(files_in_date_range)

    @staticmethod
    def get_file_date_from_name(file_name: str) -> date:
        """ Extract date from filename (assuming format: YYYY-MM-DD_BTC-USDT_level2.csv.zip) """
        file_name_only = file_name.split('/')[-1]
        file_datetime_str = file_name_only.split('_')[0]
        file_date = pd.to_datetime(file_datetime_str).date()
        return file_date

    @staticmethod
    def _get_s3_modified_dict(file_system: s3fs.S3FileSystem,
                              s3_dir: str,
                              start_date,
                              end_date) -> dict[str, pd.Timestamp]:
        """ Create last file name: modified time dictionary for files in s3 directory between start_date and end_date inclusive."""
        endpoint_url = file_system.client_kwargs.get('endpoint_url')
        # modified time: file name dictionary
        modified_dict = {}

        # List objects in the bucket
        if not file_system.exists(f"{s3_dir}"):
            logging.info(f"Skipping file search in {endpoint_url}://{s3_dir}, it doesn't exist")
            return modified_dict

        objects = file_system.listdir(s3_dir)

        # Filter files by date range
        for obj in objects:
            s3_file_path = obj['Key']
            if not s3_file_path.endswith('.csv.zip') and not s3_file_path.endswith('.csv'):
                # Skip non-csv.zip files
                logging.info(f"Skipping file {s3_file_path}, not a csv.zip or csv file")
                continue
            file_name = s3_file_path.split('/')[-1]
            # Extract date from filename (assuming format: YYYY-MM-DD_BTC-USDT_level2.csv.zip)
            try:
                file_date = S3Tools.get_file_date_from_name(file_name)
                if not (start_date.date() <= file_date <= end_date.date()):
                    continue
                modified_time = pd.Timestamp(obj['LastModified'])
                # Remove extensions
                modified_dict[file_name] = modified_time
            except (IndexError, ValueError):
                logging.info(f"Error parsing date from file {s3_file_path}, skipping")
                continue
        return modified_dict

    @staticmethod
    def find_updated_files(start_date, end_date,
                           src_s3_client: s3fs.S3FileSystem,
                           src_s3_dir: str,
                           dst_s3_client: s3fs.S3FileSystem,
                           dst_s3_dir: str) -> list[str]:
        """ Find file names (not fill paths) of files in source s3 directory
        that are not in target s3 directory or have been modified."""

        # Create modified time: file name dictionaries if not provided
        src_modified_dict = S3Tools._get_s3_modified_dict(src_s3_client,
                                                          src_s3_dir,
                                                          start_date,
                                                          end_date)
        dst_modified_dict = S3Tools._get_s3_modified_dict(dst_s3_client,
                                                          dst_s3_dir,
                                                          start_date,
                                                          end_date)
        download_list = []
        for src_file_name, src_file_datetime in src_modified_dict.items():
            # If absent or older, include in download list
            if (
                    (src_file_name.rstrip(".zip") not in dst_modified_dict
                     and src_file_name not in dst_modified_dict)
                    or
                    (src_file_datetime > (dst_modified_dict.get(src_file_name) or dst_modified_dict.get(
                        src_file_name.rstrip(".zip"))))):
                download_list.append(src_file_name)
        return sorted(download_list)
