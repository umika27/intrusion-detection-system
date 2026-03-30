WINDOW_SIZE = 50

RAW_DATA_PATHS = [
    "data/cicids.csv",
    "data/genis.csv",
    "data/unsw.csv"
]

STREAM_URL = "http://127.0.0.1:8000/predict"

STREAM_DELAY = 0.5

FEATURE_COLUMNS = {
    "fwd_packets": ["Total Fwd Packets", "sbytes"],
    "bwd_packets": ["Total Backward Packets", "dbytes"],
}