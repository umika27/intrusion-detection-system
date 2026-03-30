# flow_features.py
import pandas as pd
import numpy as np

def compute_flow_features(packets: list) -> dict | None:
    if len(packets) < 2:
        return None

    df = pd.DataFrame(packets)
    df = df.sort_values("timestamp").reset_index(drop=True)
    duration = df["timestamp"].max() - df["timestamp"].min()
    if duration == 0:
        duration = 1e-6

    origin_ip = df["src_ip"].iloc[0]
    fwd = df[df["src_ip"] == origin_ip]
    bwd = df[df["src_ip"] != origin_ip]

    # Volume & rates
    fwd_bytes, bwd_bytes = fwd["length"].sum(), bwd["length"].sum()
    total_bytes = fwd_bytes + bwd_bytes
    total_packets, fwd_packets, bwd_packets = len(df), len(fwd), len(bwd)
    fwd_mbps = (fwd_bytes*8)/(duration*1e6)
    bwd_mbps = (bwd_bytes*8)/(duration*1e6)
    packets_per_sec = total_packets/duration
    bytes_per_sec = total_bytes/duration

    # Ratios
    fwd_bwd_pkt_ratio  = fwd_packets/(bwd_packets+1e-6)
    fwd_bwd_byte_ratio = fwd_bytes/(bwd_bytes+1e-6)

    # Packet sizes
    fwd_pkt_len_mean, bwd_pkt_len_mean = fwd["length"].mean(), bwd["length"].mean()
    fwd_pkt_len_std, bwd_pkt_len_std   = fwd["length"].std(), bwd["length"].std()
    fwd_pkt_len_max, fwd_pkt_len_min   = fwd["length"].max(), fwd["length"].min()

    # IAT
    def iat_stats(subset):
        if len(subset)<2: return 0,0,0,0
        times = subset["timestamp"].values
        iats = np.diff(times)
        return iats.mean(), iats.std(), iats.max(), iats.min()
    fwd_iat_mean, fwd_iat_std, fwd_iat_max, fwd_iat_min = iat_stats(fwd)
    bwd_iat_mean, bwd_iat_std, bwd_iat_max, bwd_iat_min = iat_stats(bwd)

    # TCP Flags
    def count_flag(subset, flag):
        if "tcp_flags" not in subset.columns:
            return 0
        return subset["tcp_flags"].dropna().apply(lambda f: 1 if flag in str(f) else 0).sum()
    syn_count = count_flag(df,"S")
    ack_count = count_flag(df,"A")
    fin_count = count_flag(df,"F")
    rst_count = count_flag(df,"R")
    psh_count = count_flag(df,"P")
    syn_ack_ratio = syn_count/(ack_count+1e-6)

    # Diversity
    unique_dst_ips   = df["dst_ip"].nunique()
    unique_dst_ports = df["dst_port"].dropna().nunique()
    unique_src_ports = df["src_port"].dropna().nunique()

    # Variance & burst
    var_pps = df.groupby(df["timestamp"].astype(int))["length"].count().var() or 0
    per_sec = df.groupby(df["timestamp"].astype(int))["length"].count()
    burst_count = int((per_sec>per_sec.mean()*2).sum())

    return {
        "fwd_bytes": fwd_bytes,
        "bwd_bytes": bwd_bytes,
        "total_bytes": total_bytes,
        "total_packets": total_packets,
        "fwd_packets": fwd_packets,
        "bwd_packets": bwd_packets,
        "fwd_mbps": round(fwd_mbps,4),
        "bwd_mbps": round(bwd_mbps,4),
        "mean_pps": round(packets_per_sec,4),
        "mean_bps": round(bytes_per_sec,4),
        "fwd_bwd_pkt_ratio": round(fwd_bwd_pkt_ratio,4),
        "fwd_bwd_byte_ratio": round(fwd_bwd_byte_ratio,4),
        "fwd_pkt_len_mean": round(fwd_pkt_len_mean,4),
        "bwd_pkt_len_mean": round(bwd_pkt_len_mean,4),
        "fwd_pkt_len_std": round(fwd_pkt_len_std or 0,4),
        "bwd_pkt_len_std": round(bwd_pkt_len_std or 0,4),
        "fwd_pkt_len_max": fwd_pkt_len_max,
        "fwd_pkt_len_min": fwd_pkt_len_min,
        "fwd_iat_mean": round(fwd_iat_mean,6),
        "fwd_iat_std": round(fwd_iat_std,6),
        "fwd_iat_max": round(fwd_iat_max,6),
        "fwd_iat_min": round(fwd_iat_min,6),
        "bwd_iat_mean": round(bwd_iat_mean,6),
        "bwd_iat_std": round(bwd_iat_std,6),
        "syn_count": int(syn_count),
        "ack_count": int(ack_count),
        "fin_count": int(fin_count),
        "rst_count": int(rst_count),
        "psh_count": int(psh_count),
        "syn_ack_ratio": round(syn_ack_ratio,4),
        "unique_dst_ips": int(unique_dst_ips),
        "unique_dst_ports": int(unique_dst_ports),
        "unique_src_ports": int(unique_src_ports),
        "var_pps": round(var_pps,4),
        "burst_count": burst_count,
        "flow_duration": round(duration,4)
    }