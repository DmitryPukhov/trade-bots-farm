import pandas as pd

from libs.pytrade2.pytrade2.features.level2.Level2Features import Level2Features


class Level2PyTrade2Preproc:
    """
    Process raw level2 data in pytrade2 stream downloader format
    Just a wrapper to call a library function"""

    def process(self, raw_level2_df: pd.DataFrame) -> pd.DataFrame:
        return Level2Features().expectation(raw_level2_df)