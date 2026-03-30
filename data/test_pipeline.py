# test_pipeline.py
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(__file__))

from preprocess import load_and_clean
from feature_engineering import compute_features
from windowing import create_windows
from dataset_split import split_windows
from utils import merge_datasets
from config import RAW_DATA_PATHS
from baseline import normalize

STREAM_FEATURES = [
    "mean_pps",
    "mean_bps",
    "total_packets",
    "total_bytes",
    "var_pps"
]

def stream_to_json_file(df, file_handle, start_index=0, delay=0.2, is_last=False):
    """
    Stream each row of df to a JSON file, one window at a time.
    file_handle should be an open file in append mode.
    start_index sets the starting window number.
    is_last should be True only for the final chunk to close the JSON array.
    """
    total_rows = len(df)
    for i, row in enumerate(df.itertuples(), start=start_index):
        raw_payload = {f: float(getattr(row, f)) for f in STREAM_FEATURES}
        normalized_payload = normalize(raw_payload)

        window_json = {
            "window": i,
            "raw": raw_payload,
            "normalized": normalized_payload
        }

        json.dump(window_json, file_handle, indent=4)
        # Add comma unless last item
        if i < start_index + total_rows - 1 or not is_last:
            file_handle.write(",\n")
        else:
            file_handle.write("\n")

        time.sleep(delay)  # simulate streaming delay


# -----------------------------
# RUN PIPELINE
# -----------------------------
dfs = []

for path in RAW_DATA_PATHS:
    df = load_and_clean(path)
    df = compute_features(df)
    dfs.append(df)

merged_df = merge_datasets(dfs)
windows_df = create_windows(merged_df)
normal, attack = split_windows(windows_df)

# Open JSON file and start array
with open("stream_results.json", "w") as f:
    f.write("[\n")
    # Stream normal traffic
    stream_to_json_file(normal, f, start_index=0, delay=0.2)
    # Stream attack traffic, continue numbering
    stream_to_json_file(attack, f, start_index=len(normal), delay=0.2, is_last=True)
    # Close JSON array
    f.write("]\n")

# Save full windows.csv as before
windows_df.to_csv("windows.csv", index=False)
print("✅ stream_results.json and windows.csv saved")