#static baseline
import pandas as pd
from config import WINDOW_SIZE

def create_windows(df):
    windows = []

    for i in range(0, len(df), WINDOW_SIZE):
        chunk = df.iloc[i:i+WINDOW_SIZE]

        if len(chunk) < WINDOW_SIZE:
            continue

        window = {
            "mean_pps": chunk["packets_per_sec"].mean(),
            "mean_bps": chunk["bytes_per_sec"].mean(),
            "total_packets": chunk["total_packets"].sum(),
            "total_bytes": chunk["total_bytes"].sum(),
            "var_pps": chunk["packets_per_sec"].var() or 0,
        }

        if "Label" in chunk.columns:
            window["label"] = chunk["Label"].mode()[0]
        elif "attack_cat" in chunk.columns:
            window["label"] = "BENIGN" if chunk["attack_cat"].mode()[0] == "Normal" else "ATTACK"
        else:
            window["label"] = "UNKNOWN"

        windows.append(window)

    return pd.DataFrame(windows)