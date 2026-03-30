# vector_classification.py
# Classifies a flow window into high-level CICIDS2017 attack vectors
# Outputs a simple JSON: { "category": <label> }

from typing import Dict

# -------------------------------------------------------
# High-level CICIDS2017 categories for radar
# -------------------------------------------------------
CICIDS_CATEGORIES = [
    "DDoS",
    "Brute Force",
    "SQL Injection",
    "Port Scan",
    "Malware",
    "Phishing"   # placeholder; can be extended
]

def classify_vector(features: Dict) -> Dict:
    """
    Given a flow feature dict (from flow_features.py),
    returns a single category for radar visualization.

    This is rule-based for live vector analysis.
    """

    # Safety: if features empty, return unknown
    if not features:
        return {"category": "Unknown"}

    # --------------------------
    # 1. DDoS / DoS
    # High packet rate + burst + low diversity
    # --------------------------
    if features.get("mean_pps", 0) > 1000 and features.get("burst_count", 0) > 5:
        return {"category": "DDoS"}

    # --------------------------
    # 2. Brute Force
    # Many SYNs with no ACKs, few destination IPs
    # --------------------------
    if features.get("syn_ack_ratio", 0) > 3 and features.get("unique_dst_ips", 0) <= 5:
        return {"category": "Brute Force"}

    # --------------------------
    # 3. SQL Injection / Web Attack
    # High request volume but small packet sizes, moderate SYN/ACK
    # --------------------------
    if features.get("fwd_bwd_pkt_ratio", 0) > 2 and features.get("fwd_pkt_len_mean", 0) < 300:
        return {"category": "SQL Injection"}

    # --------------------------
    # 4. Port Scan / Infiltration
    # Many destination IPs, few packets per IP, small sizes
    # --------------------------
    if features.get("unique_dst_ips", 0) > 10 and features.get("fwd_pkt_len_mean", 0) < 200:
        return {"category": "Port Scan"}

    # --------------------------
    # 5. Malware / Bot / Heartbleed
    # Small steady packets, repeated to few IPs
    # --------------------------
    if features.get("mean_bps", 0) < 1000 and features.get("unique_dst_ips", 0) <= 3:
        return {"category": "Malware"}

    # --------------------------
    # 6. Default / Phishing
    # Could be used for unknown or future vectors
    # --------------------------
    return {"category": "Phishing"}


# --------------------------
# Quick test
# --------------------------
if __name__ == "__main__":
    sample_features = {
        "mean_pps": 1200,
        "burst_count": 8,
        "syn_ack_ratio": 0.5,
        "unique_dst_ips": 2,
        "fwd_bwd_pkt_ratio": 1.2,
        "fwd_pkt_len_mean": 500,
        "mean_bps": 500
    }

    result = classify_vector(sample_features)
    print(result)
    # Output: {'category': 'DDoS'}