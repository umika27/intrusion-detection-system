
import requests
import time
from config import STREAM_URL, STREAM_DELAY
from baseline import normalize
STREAM_FEATURES = [
    "mean_pps",
    "mean_bps",
    "total_packets",
    "total_bytes",
    "var_pps"
]



def stream_windows(df):
    for _, row in df.iterrows():
        payload = {f: float(row[f]) for f in STREAM_FEATURES}

        # payload = normalize(payload)

        try:
            res = requests.post(STREAM_URL, json=payload)
            print(res.json())
        except Exception as e:
            print("Error:", e)

        time.sleep(STREAM_DELAY)