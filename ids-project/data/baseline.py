import json
import os

BASELINE_PATH = os.path.join(os.path.dirname(__file__), "baseline.json")

def load_baseline():
    with open(BASELINE_PATH, "r") as f:
        return json.load(f)

def normalize(payload):
    baseline = load_baseline()   # ✅ FIX HERE

    norm = {}
    for key in payload:
        mean = baseline["mean"][key]
        std = baseline["std"][key]
        norm[key] = (payload[key] - mean) / (std + 1e-6)

    return norm



def compute_baseline(window_df):
    

    mean = window_df.mean().to_dict()
    std = window_df.std().replace(0, 1e-6).to_dict()
    return {
        "mean": mean,
        "std": std
    }

def save_baseline(baseline, path="baseline.json"):
    with open(path, "w") as f:
        json.dump(baseline, f, indent=4)