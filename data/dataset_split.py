def split_windows(df):
    normal = df[df["label"] == "BENIGN"]
    attack = df[df["label"] != "BENIGN"]

    return normal, attack