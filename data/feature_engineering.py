# feature_engineering.py

def compute_features(df):
    # Assumes dataset has these columns:
    # 'Total Fwd Packets', 'Total Backward Packets', 'Flow Duration', 'Total Length of Fwd Packets', etc.

    # --- TOTAL PACKETS ---
    if "Total Fwd Packets" in df.columns and "Total Backward Packets" in df.columns:
        df["total_packets"] = df["Total Fwd Packets"] + df["Total Backward Packets"]
    elif "packets" in df.columns:
        df["total_packets"] = df["packets"]
    else:
        df["total_packets"] = 1  # fallback

    # --- TOTAL BYTES ---
    if "Total Length of Fwd Packets" in df.columns:
        df["total_bytes"] = df["Total Length of Fwd Packets"]
    elif "bytes" in df.columns:
        df["total_bytes"] = df["bytes"]
    else:
        df["total_bytes"] = 0  # fallback

    # --- FLOW DURATION ---
    if "Flow Duration" in df.columns:
        duration = df["Flow Duration"] / 1e6  # convert microseconds → seconds
        duration = duration.replace(0, 1e-6)
    else:
        duration = 1  # fallback

    # --- PACKETS PER SECOND ---
    df["packets_per_sec"] = df["total_packets"] / duration

    # --- BYTES PER SECOND ---
    df["bytes_per_sec"] = df["total_bytes"] / duration

    return df