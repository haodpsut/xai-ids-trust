"""
G2 confound audit for the reliability detector: is its predictive power just an OOD detector in
disguise, or do the explanation-specific signals add value? We compare the AUC of the full
4-signal detector against each single signal alone and against sensible baselines
(margin-only = confidence, ood-only = distribution distance). If the full detector beats every
single-signal baseline, the reliability signal is not reducible to confidence or OOD.
"""
import numpy as np, torch, csv, os, warnings
warnings.filterwarnings("ignore")
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from harness import MLP, KAN, nparams, match_mlp, train, predict, flow_bao_dong
from exp_defense import ground_truth_reliability, cheap_signals, K
from data import load, DATASETS

SIGNAL_NAMES = ["margin", "concentration", "fidelity", "ood"]


def auc_of(S, y):
    return round(float(cross_val_score(LogisticRegression(max_iter=500), S, y, cv=5,
                                       scoring="roc_auc").mean()), 3)


def run(ds):
    np.random.seed(0); torch.manual_seed(0)             # determinism for reproducible ablation AUCs
    Xtr, ytr, Xte, yte, feats = load(ds)
    din = Xtr.shape[1]; h = match_mlp(din, nparams(KAN(din, 16, 4)))
    models = [train(MLP(din, h), Xtr, ytr, s) for s in range(K)]
    idx = flow_bao_dong(models[0], Xte, yte, 2000)
    Xm = Xte[idx]
    rel = ground_truth_reliability(models, Xm)
    y = (rel > np.median(rel)).astype(int)
    S = cheap_signals(models[0], Xm, Xtr)
    out = dict(dataset=ds, full_auc=auc_of(S, y))
    for i, nm in enumerate(SIGNAL_NAMES):
        out[nm + "_only"] = auc_of(S[:, [i]], y)
    return out


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = []
    for ds in DATASETS:
        r = run(ds); rows.append(r)
        singles = " ".join(f"{n}={r[n+'_only']}" for n in SIGNAL_NAMES)
        print(f"{ds}: FULL={r['full_auc']} | {singles}")
    with open("results/defense_ablate.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("wrote results/defense_ablate.csv")
