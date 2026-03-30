from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from model import predict
import random
import time

app = FastAPI()

# Input data
class WindowInput(BaseModel):
    mean_pps: float
    mean_bps: float
    total_packets: int
    total_bytes: int
    var_pps: float

# Health check-up
@app.get("/")
def home():
    return {"message": "Backend running successfully"}


# Prediction end-point
@app.post("/predict")
def get_prediction(window: WindowInput):
    try:
        return predict(window.dict())
    except Exception:
        raise HTTPException(status_code=500, detail="Prediction failed")

# Streaming random end-point
@app.get("/predict_stream")
def stream_predictions():
    results = []

    for _ in range(10):
        sample = {
            "mean_pps": random.randint(50, 300),
            "mean_bps": random.randint(1000, 6000),
            "total_packets": random.randint(100, 1000),
            "total_bytes": random.randint(5000, 50000),
            "var_pps": random.randint(5, 50)
        }

        try:
            results.append(predict(sample))
        except:
            results.append({"error": "prediction failed"})

        time.sleep(0.5)

    return results
