import pandas as pd
import numpy as np

def load_and_clean(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)

    return df