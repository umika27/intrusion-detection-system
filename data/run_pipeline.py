#static baseline
from preprocess import load_and_clean
from feature_engineering import compute_features
from windowing import create_windows
from dataset_split import split_windows
from streamer import stream_windows
from utils import merge_datasets
from config import RAW_DATA_PATHS

dfs = []

for path in RAW_DATA_PATHS:
    df = load_and_clean(path)
    df = compute_features(df)
    dfs.append(df)

merged_df = merge_datasets(dfs)

windows_df = create_windows(merged_df)

normal, attack = split_windows(windows_df)

print("Normal windows:", len(normal))
print("Attack windows:", len(attack))

windows_df.to_csv("windows.csv", index=False)

stream_windows(windows_df)