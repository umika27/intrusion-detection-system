# feature_engineering.py

def get_column(df, possible_names):
    df_cols = [c.strip().lower() for c in df.columns]

    for name in possible_names:
        if name.strip().lower() in df_cols:
            return df.columns[df_cols.index(name.strip().lower())]

    return None


from config import FEATURE_COLUMNS

def compute_features(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    print("Columns:", df.columns.tolist())
     # --- GET COLUMNS DYNAMICALLY ---
    fwd_col = get_column(df, FEATURE_COLUMNS["fwd_packets"])
    bwd_col = get_column(df, FEATURE_COLUMNS["bwd_packets"])

    if fwd_col and bwd_col:
        df["total_packets"] = df[fwd_col] + df[bwd_col]
    else:
        raise ValueError(f"Packet columns not found! Available: {df.columns}")

    # --- TOTAL PACKETS ---
    if "total fwd packets" in df.columns and "total backward packets" in df.columns:
        df["total_packets"] = df["total fwd packets"] + df["total backward packets"]
    else:
        raise ValueError("Packet columns not found!")

    # --- TOTAL BYTES ---
    if "total length of fwd packets" in df.columns:
        df["total_bytes"] = df["total length of fwd packets"]
    else:
        raise ValueError("Byte columns not found!")

    # --- FLOW DURATION ---
    duration_col = get_column(df, ["Flow Duration", "dur"])

    if duration_col:
        duration = df[duration_col] / 1e6 if "Flow Duration" in duration_col else df[duration_col]
    else:
        duration = 1

    duration = duration.replace(0, 1e-6)

    # --- FEATURES ---
    df["packets_per_sec"] = df["total_packets"] / duration
    df["bytes_per_sec"] = df["total_bytes"] / duration

    df["mean_pps"] = df["packets_per_sec"]
    df["mean_bps"] = df["bytes_per_sec"]

    return df