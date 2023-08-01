import os
import pandas as pd

if __name__ == "__main__":
    svo_filename = "../ptb_data/svo/deps_train.csv"

    counter = 0
    df = pd.read_csv(svo_filename, engine="python")
    indices = []
    for idx, row in df.iterrows():
        if row["original_sent"] == row["reordered_sent"]:
            indices.append(idx)
    indices = indices[:500]
    
    df = df.iloc[indices]

    os.makedirs("./svo", exist_ok=True)
    df.to_csv("./svo/deps_train.csv", index=False)

    for word_order in ["sov", "osv", "ovs", "vos", "vso"]:
        filename = "../ptb_data/" + word_order + "/deps_train.csv"
        df = pd.read_csv(filename, engine="python")
        df = df.iloc[indices]
        os.makedirs("./" + word_order, exist_ok=True)
        df.to_csv("./" + word_order + "/deps_train.csv", index=False)