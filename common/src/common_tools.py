import logging
import os


class CommonTools:

    @staticmethod
    def init_logging():
        log_level = os.environ.get("LOG_LEVEL") or logging.INFO
        print(f"Init logging, set log level to {log_level}")
        # Setup logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s -  %(module)s.%(funcName)s:%(lineno)d  - %(levelname)s - %(message)s'
        )
        logging.error("Error test")
        logging.warning("Warning test")
        logging.info("Info test")
        logging.debug("Debug test")
