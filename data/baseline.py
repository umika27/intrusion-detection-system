#static

BASELINE = {
    "mean": {
        "mean_pps": 50,
        "mean_bps": 2000,
        "total_packets": 3000,
        "total_bytes": 150000,
        "var_pps": 10
    },
    "std": {
        "mean_pps": 20,
        "mean_bps": 800,
        "total_packets": 1000,
        "total_bytes": 50000,
        "var_pps": 5
    }
}


def normalize(payload):
    norm = {}
    for key in payload:
        mean = BASELINE["mean"][key]
        std = BASELINE["std"][key]
        norm[key] = (payload[key] - mean) / (std + 1e-6)
    return norm