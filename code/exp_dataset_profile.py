"""Profile of every dataset AS THE PAPER LOADS IT -- feature count and attack rate.

Why this exists. Table 1 of the paper (tab:data) described the corpus with numbers that lived
nowhere but the LaTeX source: 34/52/48/38/39 features and 0.68/0.17/0.61/0.76/0.97 attack rate.
The feature counts happened to agree with redundancy.csv, but the attack rates were not derivable
from any released artifact, so a reader could not tell a typo from a result. That is the same
defect the paper accuses the field of -- a stated quantity with no way to recompute it.

The numbers here are properties of the loaded split, not of the vendor's download: `data.load`
drops identifier columns, encodes categoricals and subsamples to n=40000 with seed 0, so the
attack rate is the rate the experiments actually saw. Anything reported about the raw archive
(release year, capture setting, device count) stays prose, because no code of ours produces it.
"""
import csv
import os

import data


def main():
    os.makedirs("results", exist_ok=True)
    rows = []
    for name in data.DATASETS:
        Xtr, ytr, Xte, yte, feats = data.load(name, seed=0)
        n = len(ytr) + len(yte)
        n_att = int(ytr.sum() + yte.sum())
        rows.append({
            "dataset": name,
            "n_features": Xtr.shape[1],
            "n_rows_used": n,
            "n_attack": n_att,
            "attack_rate": round(n_att / n, 2),
        })
        print("  %-14s features=%3d  rows=%6d  attack_rate=%.4f"
              % (name, Xtr.shape[1], n, n_att / n))
    with open("results/dataset_profile.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("wrote results/dataset_profile.csv (%d datasets)" % len(rows))


if __name__ == "__main__":
    main()
