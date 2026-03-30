from ml.model import predict, BASELINE_PATH
import json
import numpy as np
import json
import os
import json
normal_window = {
    "mean_pps": 45,
    "mean_bps": 1800,
    "total_packets": 2800,
    "total_bytes": 140000,
    "var_pps": 8
}

attack_window = {
    "mean_pps": 200,
    "mean_bps": 8000,
    "total_packets": 12000,
    "total_bytes": 600000,
    "var_pps": 50
}

def main():
    print("\n--- NORMAL TRAFFIC ---")
    print(predict(normal_window))

    print("\n--- ATTACK TRAFFIC ---")
    print(predict(attack_window))


if __name__ == "__main__":
    main()

with open(BASELINE_PATH, "r") as f:
    data = json.load(f)

baseline = data["mean"]
std_dev = data["std"]
print("Baseline being used:", baseline)
print("Standard deviations being used:", std_dev)