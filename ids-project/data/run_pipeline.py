import pandas as pd
from config import RAW_DATA_PATHS
from dataset_split import split_windows
from feature_engineering import compute_features
from windowing import create_windows
from baseline import compute_baseline, save_baseline
import json

def load_data():
    dfs = []
    for path in RAW_DATA_PATHS:
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip()
        dfs.append(df)
    return pd.concat(dfs)


def main():
    df = load_data()

    # Normalize label column name
    df.columns = [c.lower() for c in df.columns]
    if "label" in df.columns:
       df["label"] = df["label"].astype(str).str.strip().str.upper()
    # Split normal traffic
    normal_df, _ = split_windows(df)

    # Feature engineering
    normal_df = compute_features(normal_df)

    # Create windows
    windows_df = create_windows(normal_df)
    # Compute baseline ONLY on normal windows
    normal, attack = split_windows(windows_df)
    features_only = normal.drop(columns=["label"])
    baseline = {
        "mean": features_only.mean().to_dict(),
        "std": features_only.std().replace(0, 1e-6).to_dict()
    }
    with open("baseline.json", "w") as f:
        json.dump(baseline, f, indent=4)
    print("✅ Baseline saved")

    # Save
    save_baseline(baseline)

    print("✅ Baseline generated!")


if __name__ == "__main__":
    main()