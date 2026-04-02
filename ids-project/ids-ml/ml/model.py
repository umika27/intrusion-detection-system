import numpy as np
import json
import os

# -------------------------------
# Load baseline from file
# -------------------------------
BASELINE_PATH = os.path.join(os.path.dirname(__file__), "baseline.json")
with open(BASELINE_PATH, "r") as f:
    data = json.load(f)

baseline = data["mean"]
std_dev = data["std"]

# -------------------------------
# Features used
# -------------------------------
FEATURES = [
    "mean_pps",
    "mean_bps",
    "total_packets",
    "total_bytes",
    "var_pps"
]

# -------------------------------
# Compute Risk (Z-score based)
# -------------------------------
def compute_risk(window):
    z_scores = {}

    for f in FEATURES:
        value = window.get(f, 0)
        mean = baseline[f]
        std = std_dev[f] + 1e-6  # prevent division by zero

        z = (value - mean) / std
        z_scores[f] = abs(z)

    # Average deviation
    anomaly_score = np.mean(list(z_scores.values()))

    # Scale to 0–100
    risk = min(100, anomaly_score * 25)

    return risk, z_scores


# -------------------------------
# Status Classification
# -------------------------------
def get_status(risk):
    if risk > 70:
        return "HIGH RISK"
    elif risk > 30:
        return "SUSPICIOUS"
    else:
        return "NORMAL"


# -------------------------------
# Explanation Generator
# -------------------------------
def generate_explanation(z_scores, window):
    # Sort by highest deviation
    sorted_features = sorted(z_scores.items(), key=lambda x: x[1], reverse=True)

    explanations = []

    for f, z in sorted_features[:2]:
        base = baseline[f] + 1e-6
        val = window[f]

        factor = val / base

        if factor > 1:
            explanations.append(f"{f} increased {factor:.2f}x")
        else:
            explanations.append(f"{f} decreased to {factor:.2f}x")

    return explanations


# -------------------------------
# Main Predict Function
# -------------------------------
def predict(window):
    risk, z_scores = compute_risk(window)

    status = get_status(risk)

    explanation = generate_explanation(z_scores, window)

    return {
        "risk": round(risk, 2),
        "status": status,
        "explanation": explanation
    }