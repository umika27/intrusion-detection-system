WINDOW_SIZE = 50

import os

BASE_DIR = os.path.dirname(__file__)

RAW_DATA_PATHS = [
    os.path.join(BASE_DIR, "cicids.csv"),
    #os.path.join(BASE_DIR, "unsw.csv"),
    #os.path.join(BASE_DIR, "genis.csv"),
]

STREAM_URL = "http://127.0.0.1:8000/predict"

STREAM_DELAY = 0.5

FEATURE_COLUMNS = {
    "fwd_packets": ["total fwd packets", "sbytes"],
    "bwd_packets": ["total backward packets", "dbytes"],
}