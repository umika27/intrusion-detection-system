# live_pipeline.py (context-aware version with vector classification)

import time
import threading
import json
import pandas as pd

from capture import start_capture, get_and_clear_buffer
from flow_features import compute_flow_features
from context_labeling import label_traffic_context
from vector_classification import classify_vector

# -------------------------
# CONFIG
# -------------------------
WINDOW_INTERVAL = 5.0
INTERFACE = "eth0"

# -------------------------
# WINDOW HISTORY
# -------------------------
window_history = pd.DataFrame()

def process_window():
    global window_history

    packets = get_and_clear_buffer()
    if len(packets) < 2:
        print("[pipeline] Not enough packets in window, skipping...")
        return

    # Compute flow features
    features = compute_flow_features(packets)
    if features is None:
        return

    # Append to history
    window_history = pd.concat([window_history, pd.DataFrame([features])], ignore_index=True)

    # Context labeling
    window_history = label_traffic_context(window_history)
    current_window = window_history.iloc[-1]

    # --------------------------
    # Vector classification
    # --------------------------
    vector_result = classify_vector(features)

    # --------------------------
    # Prepare JSON for dashboard/log (fixed)
    # --------------------------
    window_json = {
        "timestamp": float(time.time()),
        "fwd_mbps": float(features.get("fwd_mbps", 0)),
        "bwd_mbps": float(features.get("bwd_mbps", 0)),
        "total_packets": int(features.get("total_packets", 0)),
        "total_bytes": int(features.get("total_bytes", 0)),
        "context": str(current_window.get("context", "unknown")),
        "vector_category": str(vector_result.get("category", "Unknown"))
    }

    # Print JSON nicely
    print("[window JSON]", json.dumps(window_json, indent=2))

    # Optional: write to file
    with open("live_window_log.json", "a") as f:
        f.write(json.dumps(window_json) + "\n")


def run():
    capture_thread = threading.Thread(
        target=start_capture,
        kwargs={"interface": INTERFACE},
        daemon=True
    )
    capture_thread.start()
    print(f"[pipeline] Capture started on {INTERFACE}")
    print(f"[pipeline] Processing windows every {WINDOW_INTERVAL}s\n")

    while True:
        time.sleep(WINDOW_INTERVAL)
        process_window()


if __name__ == "__main__":
    run()