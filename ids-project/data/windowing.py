import pandas as pd
from config import WINDOW_SIZE

def create_windows(df):
    windows = []

    for i in range(0, len(df), WINDOW_SIZE):
        chunk = df.iloc[i:i+WINDOW_SIZE]

        if len(chunk) < WINDOW_SIZE:
            continue

        window = {
            "mean_pps": chunk["mean_pps"].mean(),
            "mean_bps": chunk["mean_bps"].mean(),
            "total_packets": chunk["total_packets"].sum(),
            "total_bytes": chunk["total_bytes"].sum(),
            "var_pps": chunk["mean_pps"].var()
        }
        if "label" in chunk.columns:
            window["label"] = chunk["label"].mode()[0]

        windows.append(window)

    return pd.DataFrame(windows)