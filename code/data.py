"""
Unified loader for three MODERN NIDS datasets, each with named, interpretable features so
that a feature attribution is a claim about a real network quantity:
  - UNSW-NB15 (2015 standard; parquet)               label: 'label' (0/1)
  - CICIDS2017 cleaned (flow features)               label: 'Attack Type' (Normal Traffic vs *)
  - 5G-NIDD (2022-23, live 5G testbed; Hao's domain) label: 'Label' (Benign/Malicious)
Returns balanced-ish binary normal-vs-attack splits with standardized numeric features.
"""
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split

BASE = "../data"


def _prep(df, label_col, normal_values, feat_names, seed=0, n=40000):
    y = (~df[label_col].isin(normal_values)).astype(int).values      # 1 = attack
    X = df[feat_names].copy()
    for c in X.columns:                                              # encode any categoricals
        if str(X[c].dtype) in ("object", "category") or not np.issubdtype(X[c].dtype, np.number):
            X[c] = LabelEncoder().fit_transform(X[c].astype(str))
    X = X.apply(lambda s: s.astype(np.float64)).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    X = X.astype(np.float32).values
    rng = np.random.default_rng(seed)
    if len(X) > n:
        idx = rng.choice(len(X), n, replace=False); X, y = X[idx], y[idx]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)
    sc = StandardScaler().fit(Xtr)
    return sc.transform(Xtr).astype(np.float32), ytr, sc.transform(Xte).astype(np.float32), yte, feat_names


def load(name, seed=0):
    if name == "UNSW":
        df = pd.read_parquet(f"{BASE}/unsw/UNSW_NB15_training-set.parquet")
        feats = [c for c in df.columns if c not in ("label", "attack_cat", "id")]
        return _prep(df, "label", [0], feats, seed)
    if name == "CICIDS":
        df = pd.read_csv(f"{BASE}/cicids/cicids2017_cleaned.csv")
        feats = [c for c in df.columns if c != "Attack Type"]
        return _prep(df, "Attack Type", ["Normal Traffic", "BENIGN", "Benign"], feats, seed)
    if name == "5G-NIDD":
        df = pd.read_csv(f"{BASE}/g5nidd/Combined.csv", low_memory=False)
        drop = {"Label", "Attack Type", "Attack Tool", "Unnamed: 0"}
        feats = [c for c in df.columns if c not in drop]
        return _prep(df, "Label", ["Benign"], feats, seed)
    raise ValueError(name)


DATASETS = ["UNSW", "CICIDS", "5G-NIDD"]
