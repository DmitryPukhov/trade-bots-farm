import pandas as pd

from pytrade2.features.level2.Level2Features import Level2Features


class Level2PyTrade2Preproc:
    """
    Process raw level2 data in pytrade2 stream downloader format
    Just a wrapper to call a library function"""

    def process(self, raw_level2_df: pd.DataFrame) -> pd.DataFrame:
        Level2Features().expectation(raw_level2_df).resample("1min", label = "right", closed = "right").agg("mean")