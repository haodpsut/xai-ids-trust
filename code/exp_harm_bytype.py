"""
Phase-2: does the explanation-induced action divergence (Sec. harm) vary by ATTACK TYPE? On the
multiclass datasets (CICIDS 'Attack Type', TON-IoT 'type'), we recompute action divergence per
attack category on correctly-detected true attacks. If some attack types are far more likely to
be dismissed than others, mis-founded trust creates blind spots concentrated on specific threats.
"""
import numpy as np, pandas as pd, torch, csv, os, warnings
warnings.filterwarnings("ignore")
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from harness import MLP, KAN, nparams, match_mlp, train, predict, saliency
from data import BASE

K = 5


def load_typed(name):
    if name == "CICIDS":
        df = pd.read_csv(f"{BASE}/cicids/cicids2017_cleaned.csv")
        typecol = "Attack Type"; benign = ["Normal Traffic", "BENIGN", "Benign"]
    else:  # TON-IoT
        df = pd.read_csv(f"{BASE}/toniot/train_test_network.csv", low_memory=False)
        typecol = "type"; benign = ["normal", "benign"]
    y = (~df[typecol].isin(benign)).astype(int).values
    types = df[typecol].astype(str).values
    drop = {typecol, "label", "Attack Type", "src_ip", "dst_ip", "src_port", "dst_port", "ts"}
    feats = [c for c in df.columns if c not in drop]
    X = df[feats].copy()
    for c in X.columns:
        if str(X[c].dtype) in ("object", "category"):
            X[c] = LabelEncoder().fit_transform(X[c].astype(str))
    X = X.apply(lambda s: s.astype(np.float64)).replace([np.inf, -np.inf], np.nan).fillna(0.0).astype(np.float32).values
    rng = np.random.default_rng(0); idx = rng.permutation(len(X))[:40000]
    X, y, types = X[idx], y[idx], types[idx]
    ntr = int(0.7 * len(X)); sc = StandardScaler().fit(X[:ntr])
    Xs = sc.transform(X).astype(np.float32)
    return Xs[:ntr], y[:ntr], Xs[ntr:], y[ntr:], types[ntr:]


def attr(m, X):
    a = saliency(m, X); return a / (np.abs(a).sum(1, keepdims=True) + 1e-9)


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = []
    for ds in ["CICIDS", "TON-IoT"]:
        np.random.seed(0); torch.manual_seed(0)         # determinism for reproducible per-type rates
        Xtr, ytr, Xte, yte, types = load_typed(ds); din = Xtr.shape[1]
        h = match_mlp(din, nparams(KAN(din, 16, 4)))
        models = [train(MLP(din, h), Xtr, ytr, s) for s in range(5)]
        g = LogisticRegression(max_iter=300).fit(attr(models[0], Xtr), ytr)
        preds = np.stack([predict(m, Xte) for m in models], 1)
        tp = (yte == 1) & (preds == 1).all(1)
        print(f"\n=== {ds} action-divergence by attack type ===")
        for t in sorted(set(types[tp])):
            mask = tp & (types == t)
            if mask.sum() < 30:
                continue
            Xt = Xte[mask]
            acts = np.stack([g.predict(attr(m, Xt)) for m in models], 1)
            div = float((~((acts == 1).all(1) | (acts == 0).all(1))).mean())
            supp = float((acts == 0).mean())
            rows.append(dict(dataset=ds, attack_type=t, n=int(mask.sum()),
                             action_divergence=round(div, 3), suppress_rate=round(supp, 3)))
            print(f"  {t:22s} n={mask.sum():5d} divergence={div:.3f} suppress={supp:.3f}")
    with open("results/harm_bytype.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("\nwrote results/harm_bytype.csv")
