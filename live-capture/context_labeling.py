# context_labeling.py
import pandas as pd

def label_traffic_context(windows_df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a 'context' column to windows_df based on rolling bytes/sec.
    High sustained traffic is labeled 'high_activity'.
    Sudden spikes > 3x rolling mean are labeled 'spike'.
    """
    df = windows_df.copy()
    df["rolling_bps"] = df["mean_bps"].rolling(window=5, min_periods=1).mean()
    
    def label_row(row):
        return "high_activity" if row["mean_bps"] < row["rolling_bps"] * 3 else "spike"
    
    df["context"] = df.apply(label_row, axis=1)
    return df