import logging
import os


class CommonTools:

    @staticmethod
    def init_logging():
        # Setup logging
        logging.basicConfig(
            level=os.environ.get("LOG_LEVEL") or logging.INFO,
            format='%(asctime)s -  %(module)s.%(funcName)s:%(lineno)d  - %(levelname)s - %(message)s'
        )
