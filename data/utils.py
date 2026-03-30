import pandas as pd

def merge_datasets(dfs):
    return pd.concat(dfs, ignore_index=True)