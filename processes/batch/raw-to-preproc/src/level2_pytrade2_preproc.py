import pandas as pd

from pytrade2.features.level2.Level2Features import Level2Features


class Level2PyTrade2Preproc:
    """
    Process raw level2 data in pytrade2 stream downloader format
    Just a wrapper to call a library function"""

    def process(self, raw_level2_df: pd.DataFrame) -> pd.DataFrame:
        # clean up and prepare
        df = raw_level2_df
        if "datetime.1" in df.columns:
            del df["datetime.1"]
        df["datetime"] = df["datetime"].astype('datetime64[ms]')
        df.set_index("datetime", drop=False, inplace=True)
        df = Level2Features().expectation(df).resample("1min", label = "right", closed = "right").agg("mean")
        return df
