# test_pipeline.py
import sys
import os
import json
import time
from ml.model import predict
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

def stream_to_json_file(df, file_handle, start_index=0, delay=0.2):
    for i, row in enumerate(df.itertuples(), start=start_index):

        # Extract features
        raw_payload = {
            "mean_pps": float(getattr(row, "mean_pps")),
            "mean_bps": float(getattr(row, "mean_bps")),
            "total_packets": float(getattr(row, "total_packets")),
            "total_bytes": float(getattr(row, "total_bytes")),
            "var_pps": float(getattr(row, "var_pps")),
        }

        # 🔥 ML INTEGRATION
        prediction = predict(raw_payload)

        window_json = {
            "window": i,
            "raw": raw_payload,
            "prediction": prediction
        }

        json.dump(window_json, file_handle)
        file_handle.write(",\n")
        file_handle.flush()

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
try:
    with open("stream_results.json", "w") as f:
        f.write("[\n")

        while True:
            stream_to_json_file(normal, f, start_index=0, delay=0.1)

except KeyboardInterrupt:
    print("\n🛑 Streaming stopped cleanly")

# Save full windows.csv as before
windows_df.to_csv("windows.csv", index=False)
print("✅ stream_results.json and windows.csv saved")