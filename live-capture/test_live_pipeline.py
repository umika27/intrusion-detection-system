# test_live_pipeline.py (updated)
import time
import live_pipeline  # import the module to access window_history
from capture import buffer_lock, packet_buffer

# -----------------------------
# Function to add mock packets
# -----------------------------
def add_mock_packets(mock_type="default"):
    """
    Add simulated packets to buffer.
    mock_type can be used to simulate different attack patterns.
    """
    base_time = time.time()
    if mock_type == "default":
        packets = [
            {"timestamp": base_time + i*0.01,
             "src_ip":"10.0.0.1","dst_ip":f"10.0.0.{i+2}",
             "length": 500 - i*50, "protocol":6,
             "src_port":1234, "dst_port":80+i, "tcp_flags":"S" if i%2==0 else "A"}
            for i in range(5)
        ]
    elif mock_type == "ddos":
        # High PPS + bursts
        packets = [
            {"timestamp": base_time + i*0.001,
             "src_ip":"10.0.0.1","dst_ip":"10.0.0.2",
             "length": 200, "protocol":6,
             "src_port":1234, "dst_port":80, "tcp_flags":"S"}
            for i in range(1200)  # triggers DDoS
        ]
    else:
        packets = []  # empty for safety

    with buffer_lock:
        packet_buffer.extend(packets)


# -----------------------------
# Simulate multiple windows
# -----------------------------
def simulate_live_pipeline(interval=2, windows=3):
    for i in range(windows):
        print(f"\n--- Window {i+1} ---")
        if i == 1:
            add_mock_packets("ddos")  # simulate DDoS in 2nd window
        else:
            add_mock_packets("default")

        live_pipeline.process_window()  # process the window
        time.sleep(interval)

    print("\nFinal window_history (last 5 rows):")
    print(live_pipeline.window_history.tail())


# -----------------------------
# Run simulation
# -----------------------------
if __name__ == "__main__":
    print("Starting simulated live pipeline test...")
    simulate_live_pipeline(interval=1, windows=3)  # faster testing