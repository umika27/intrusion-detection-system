from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from model import predict
import random
import math
import csv
import os
import itertools

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Load windows.csv once at startup and create an infinite cyclic iterator
# ---------------------------------------------------------------------------
_WINDOWS_PATH = os.path.join(os.path.dirname(__file__), "windows.csv")
_windows_rows: list[dict] = []

try:
    with open(_WINDOWS_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                _windows_rows.append({
                    "mean_pps":      float(row["mean_pps"]),
                    "mean_bps":      float(row["mean_bps"]),
                    "total_packets": float(row["total_packets"]),
                    "total_bytes":   float(row["total_bytes"]),
                    "var_pps":       float(row["var_pps"]),
                    "label":         row.get("label", "UNKNOWN"),
                })
            except (ValueError, KeyError):
                continue  # skip malformed rows
    print(f"✅ Loaded {len(_windows_rows)} windows from windows.csv")
except FileNotFoundError:
    print("⚠️  windows.csv not found — /next_window will return simulated data")

_csv_cycle = itertools.cycle(_windows_rows) if _windows_rows else None


# ---------------------------------------------------------------------------
# Input schema with validation bounds (CIC-IDS 2017 derived)
# ---------------------------------------------------------------------------
class WindowInput(BaseModel):
    mean_pps:      float = Field(..., ge=0.0, le=500.0)
    mean_bps:      float = Field(..., ge=0.0, le=50000.0)
    total_packets: float = Field(..., ge=0.0, le=100000.0)
    total_bytes:   float = Field(..., ge=0.0, le=10_000_000.0)
    var_pps:       float = Field(..., ge=0.0, le=500.0)

    @validator("mean_pps", "mean_bps", "total_packets", "total_bytes", "var_pps", pre=True)
    def must_be_finite(cls, v):
        if not math.isfinite(float(v)):
            raise ValueError("Value must be a finite number (no inf or NaN)")
        return v


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def home():
    return {"message": "Backend running successfully"}


@app.post("/predict")
def get_prediction(window: WindowInput):
    try:
        return predict(window.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/next_window")
def next_window():
    """Return the next real CIC-IDS window with its ML prediction (cycles through windows.csv)."""
    if _csv_cycle is None:
        # Fallback: simulated sample if CSV not loaded
        anomaly = random.random() < 0.3
        sample = {
            "mean_pps":      round(random.uniform(0.15, 0.5),   6) if anomaly else round(random.uniform(0.0, 0.1), 6),
            "mean_bps":      round(random.uniform(10.0, 30.0),  4) if anomaly else round(random.uniform(0.0, 5.0), 4),
            "total_packets": round(random.uniform(1500, 4000),  2) if anomaly else round(random.uniform(100, 1300), 2),
            "total_bytes":   round(random.uniform(400000, 900000), 2) if anomaly else round(random.uniform(10000, 240000), 2),
            "var_pps":       round(random.uniform(0.2, 0.5),    6) if anomaly else round(random.uniform(0.0, 0.09), 6),
        }
        prediction = predict(sample)
        return {"source": "simulated", "window": sample, "prediction": prediction}

    row = next(_csv_cycle)
    window_features = {k: v for k, v in row.items() if k != "label"}
    prediction = predict(window_features)
    return {
        "source":     "csv",
        "label":      row["label"],         # ground-truth label from dataset
        "window":     window_features,
        "prediction": prediction,
    }


@app.get("/predict_stream")
def stream_predictions():
    """Return 10 consecutive real windows with predictions."""
    results = []
    for _ in range(10):
        results.append(next_window())
    return results
