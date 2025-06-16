import json
import logging
import logging.config
import os
from pathlib import Path

import yaml


class CommonTools:
    @staticmethod
    def _load_config():
        """Load configuration file with fallback support"""
        config_name = "logging.yaml"
        try:
            # Try package resources first (works when installed)
            from importlib.resources import files
            config_text = files("features.config").joinpath(config_name).read_text()
            return yaml.safe_load(config_text)
        except:
            # Fallback for development environment
            dev_path = os.path.join("../config", config_name)
            with open(dev_path) as f:
                return yaml.safe_load(f)

    @staticmethod
    def init_logging():
        # Basic config
        log_level = os.environ.get("LOG_LEVEL") or logging.INFO
        print(f"Init logging, set log level to {log_level}")
        # Setup logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s -  %(module)s.%(funcName)s:%(lineno)d  - %(levelname)s - %(message)s'
        )

        # Load logging.yaml
        CommonTools._load_config()

        # Test logging
        print("Logging init done. Test messages are below.")
        logging.error("Error test")
        logging.warning("Warning test")
        logging.info("Info test")
        logging.debug("Debug test")
