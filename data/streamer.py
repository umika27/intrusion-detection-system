#static baseline
import requests
import time
from config import STREAM_URL, STREAM_DELAY

STREAM_FEATURES = [
    "mean_pps",
    "mean_bps",
    "total_packets",
    "total_bytes",
    "var_pps"
]

# 🔒 STATIC BASELINE (from ML teammate)
BASELINE = {
    "mean": {
        "mean_pps": 50,
        "mean_bps": 2000,
        "total_packets": 3000,
        "total_bytes": 150000,
        "var_pps": 10
    },
    "std": {
        "mean_pps": 20,
        "mean_bps": 800,
        "total_packets": 1000,
        "total_bytes": 50000,
        "var_pps": 5
    }
}

def normalize(payload):
    norm = {}
    for key in payload:
        mean = BASELINE["mean"][key]
        std = BASELINE["std"][key]
        norm[key] = (payload[key] - mean) / (std + 1e-6)
    return norm


def stream_windows(df):
    for _, row in df.iterrows():
        payload = {f: float(row[f]) for f in STREAM_FEATURES}

        payload = normalize(payload)

        try:
            res = requests.post(STREAM_URL, json=payload)
            print(res.json())
        except Exception as e:
            print("Error:", e)

        time.sleep(STREAM_DELAY)