from datetime import date

from s3_tools import S3Tools

class TestS3Tools:

    def test_get_file_date_from_name__should_parse_file_name_only(self):
        assert  S3Tools.get_file_date_from_name("2025-06-14_BTC-USDT.csv") == date(2025, 6, 14)

    def test_get_file_date_from_name__should_parse_full_path(self):
        assert  S3Tools.get_file_date_from_name("/opt/data/2025-06-14_BTC-USDT.csv") == date(2025, 6, 14)
