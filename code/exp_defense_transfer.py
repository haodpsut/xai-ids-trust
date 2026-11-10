"""
Does the reliability gate GENERALIZE across datasets? A deployable gate must work without being
re-fit on the target dataset's expensive (ensemble + multi-method) reliability label. We fit the
gate on one dataset and test its AUC on another. If cross-dataset AUC is near or below chance, the
gate is not deployable: it needs the very label it was supposed to spare the operator.
"""
import numpy as np, torch, csv, os, warnings
warnings.filterwarnings("ignore")
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from harness import MLP, KAN, nparams, match_mlp, train, predict, flow_bao_dong
from exp_defense import ground_truth_reliability, cheap_signals, K
from data import load, DATASETS


def build(ds):
    np.random.seed(0); torch.manual_seed(0)             # determinism for reproducible transfer AUCs
    Xtr, ytr, Xte, yte, feats = load(ds)
    din = Xtr.shape[1]; h = match_mlp(din, nparams(KAN(din, 16, 4)))
    models = [train(MLP(din, h), Xtr, ytr, s) for s in range(K)]
    idx = flow_bao_dong(models[0], Xte, yte, 2000)
    Xm = Xte[idx]
    rel = ground_truth_reliability(models, Xm)
    y = (rel > np.median(rel)).astype(int)
    S = cheap_signals(models[0], Xm, Xtr)
    return S, y


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    cache = {ds: build(ds) for ds in DATASETS}
    rows = []
    for tr in DATASETS:
        Str, ytr = cache[tr]
        sc = StandardScaler().fit(Str)
        clf = LogisticRegression(max_iter=500).fit(sc.transform(Str), ytr)
        for te in DATASETS:
            Ste, yte = cache[te]
            auc = roc_auc_score(yte, clf.predict_proba(sc.transform(Ste))[:, 1])
            rows.append(dict(train_on=tr, test_on=te, auc=round(float(auc), 3)))
            tag = "(in-dist)" if tr == te else ""
            print(f"train {tr:8s} -> test {te:8s}: AUC={auc:.3f} {tag}")
    with open("results/defense_transfer.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["train_on", "test_on", "auc"]); w.writeheader(); w.writerows(rows)
    cross = [r["auc"] for r in rows if r["train_on"] != r["test_on"]]
    print(f"\ncross-dataset AUC: mean={np.mean(cross):.3f} min={np.min(cross):.3f} max={np.max(cross):.3f}")
    print("wrote results/defense_transfer.csv")
