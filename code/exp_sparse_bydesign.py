"""Can a sparse-BY-DESIGN detector buy back determinacy and groundedness, and at what cost?

The question an external reviewer put to us on 11/08/2026, and the one this paper most needed to
answer. Every negative result here concerns post-hoc explanations of a dense model. Our own
positive control (Table `tab:ceiling`) shows all three properties reach ~1.0 when the ground truth
is genuinely sparse, and Proposition 3 shows P2/P3 decay monotonically as the signal spreads --
which raises the obvious prescription: stop explaining dense models, deploy a model whose decision
rule is already short. If that works on real corpora, the paper turns from a complaint into advice.
If it does not, the negative result is far stronger than the one we currently report.

Three sparse-by-design detectors, each with a decision rule an analyst can read in full:
  L1-LOGIT      logistic regression, L1 penalty tuned per fit to land near TARGET_NNZ nonzeros
  TOP5-LOGIT    mutual-information selection of 5 features, then unpenalised logistic on those
  TREE-D3       depth-3 decision tree: at most 7 tests, the whole model fits on one line

THE METHODOLOGICAL POINT, and the reason this file is longer than it looks. Groundedness must be
measured across INDEPENDENT FITS, which means the feature selection has to happen inside the seed
loop. Selecting features once and sharing them across seeds makes P3 identically 1.0 by
construction -- the pipeline would then be measuring its own fixed feature list, not the stability
of the method. Each seed here gets its own bootstrap resample of the training set and runs its own
selection, so P3 is the honest quantity: how often two analysts who ran the same sparse pipeline on
the same distribution would be shown the same reason.

ATTRIBUTIONS. For the linear models we use input x gradient, a(x) = w (*) x, normalised. Plain
gradient is degenerate here -- it equals w for every flow, so the top-k set is identical on every
input and determinacy would be trivially 1.0 while telling the analyst nothing flow-specific. That
degeneracy is itself worth reporting and is why we do not use it. For the tree, a flow's
attribution is the impurity decrease at each node on its own root-to-leaf path: exact,
deterministic, and precisely the reason the tree gives.

Determinacy (P2) is top-5 Jaccard across three attribution definitions that real deployments use
interchangeably: the model's own weights or impurities, permutation importance, and
leave-one-feature-out F1 drop. Groundedness (P3) is top-5 Jaccard across the five independent fits.
The dense MLP baseline is retrained here rather than read from another CSV, so the F1 comparison
is against a model trained by the same code path on the same split.

Finally we re-run the analyst-calibration measurement of exp_auditor_control.py on these models:
if the sparse route works, the gap between reading the model you calibrated on and reading an
equally accurate sibling should close. That gap, not the property scores, is what the paper's
security claim rests on.
"""
import csv
import os
import warnings

import numpy as np
import torch

warnings.filterwarnings("ignore")
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import mutual_info_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.tree import DecisionTreeClassifier

from data import DATASETS, load
from harness import KAN, MLP, match_mlp, nparams, predict, train

K = 5              # independent fits, matching exp_harm.py
TOPK = 5           # top-k for every Jaccard in this paper
TARGET_NNZ = 5     # sparsity budget for the L1 model


def jac(a, b, k=TOPK):
    A, B = set(np.argsort(-a)[:k]), set(np.argsort(-b)[:k])
    return len(A & B) / len(A | B)


def mean_pairwise_jac(vecs):
    n = len(vecs)
    return float(np.mean([jac(vecs[i], vecs[j]) for i in range(n) for j in range(i + 1, n)]))


# ---------------------------------------------------------------- sparse fits

def fit_l1(X, y, rng):
    """L1 logistic, C halved until the fit is at or below the sparsity budget."""
    C = 1.0
    for _ in range(14):
        m = LogisticRegression(penalty="l1", C=C, solver="liblinear", max_iter=400).fit(X, y)
        if int((np.abs(m.coef_[0]) > 1e-8).sum()) <= TARGET_NNZ:
            return m, np.where(np.abs(m.coef_[0]) > 1e-8)[0]
        C /= 2
    return m, np.where(np.abs(m.coef_[0]) > 1e-8)[0]


def fit_top5(X, y, rng):
    sub = rng.choice(len(y), size=min(4000, len(y)), replace=False)   # MI is the slow part
    mi = mutual_info_classif(X[sub], y[sub], random_state=0)
    idx = np.argsort(-mi)[:TOPK]
    Z = np.zeros_like(X)
    Z[:, idx] = X[:, idx]
    return LogisticRegression(max_iter=400).fit(Z, y), idx


def fit_tree(X, y, rng):
    m = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X, y)
    return m, np.where(m.feature_importances_ > 0)[0]


def mask(X, idx):
    Z = np.zeros_like(X)
    Z[:, idx] = X[:, idx]
    return Z


def predict_sparse(kind, m, idx, X):
    return m.predict(mask(X, idx) if kind == "top5-logit" else X)


def attr_sparse(kind, m, idx, X):
    """Per-flow attribution. Linear: input x gradient. Tree: impurity decrease on the flow's path."""
    if kind == "tree-d3":
        t = m.tree_
        node = m.decision_path(X)
        imp = np.zeros(t.node_count)
        tot = t.weighted_n_node_samples[0]
        for n in range(t.node_count):
            if t.children_left[n] == -1:
                continue
            l, r = t.children_left[n], t.children_right[n]
            imp[n] = (t.weighted_n_node_samples[n] * t.impurity[n]
                      - t.weighted_n_node_samples[l] * t.impurity[l]
                      - t.weighted_n_node_samples[r] * t.impurity[r]) / tot
        A = np.zeros((X.shape[0], X.shape[1]))
        node = node.toarray().astype(bool)
        for n in range(t.node_count):
            if t.children_left[n] == -1 or imp[n] <= 0:
                continue
            A[node[:, n], t.feature[n]] += imp[n]
        return A / (np.abs(A).sum(1, keepdims=True) + 1e-9)
    w = m.coef_[0]
    A = (mask(X, idx) if kind == "top5-logit" else X) * w
    return np.abs(A) / (np.abs(A).sum(1, keepdims=True) + 1e-9)


def global_attrs(kind, m, idx, X, y):
    """Three attribution definitions deployments use interchangeably -> determinacy across them."""
    if kind == "tree-d3":
        own = m.feature_importances_.copy()
    else:
        own = np.abs(m.coef_[0])
    base = f1_score(y, predict_sparse(kind, m, idx, X), zero_division=0)
    rng = np.random.default_rng(0)
    perm = np.zeros(X.shape[1])
    loo = np.zeros(X.shape[1])
    for j in (idx if len(idx) else range(X.shape[1])):
        Xp = X.copy()
        Xp[:, j] = rng.permutation(Xp[:, j])
        perm[j] = base - f1_score(y, predict_sparse(kind, m, idx, Xp), zero_division=0)
        Xz = X.copy()
        Xz[:, j] = 0.0
        loo[j] = base - f1_score(y, predict_sparse(kind, m, idx, Xz), zero_division=0)
    return [own, np.abs(perm), np.abs(loo)]


FITS = {"l1-logit": fit_l1, "top5-logit": fit_top5, "tree-d3": fit_tree}


def run(ds):
    np.random.seed(0)
    torch.manual_seed(0)
    Xtr, ytr, Xte, yte, feats = load(ds)

    din = Xtr.shape[1]
    h = match_mlp(din, nparams(KAN(din, 16, 4)))
    mlp_f1 = float(np.mean([f1_score(yte, predict(train(MLP(din, h), Xtr, ytr, s), Xte),
                                     zero_division=0) for s in range(3)]))

    out = []
    for kind, fit in FITS.items():
        fits, idxs, f1s = [], [], []
        for s in range(K):
            rng = np.random.default_rng(s)
            b = rng.choice(len(ytr), size=len(ytr), replace=True)   # independent refit per seed
            m, idx = fit(Xtr[b], ytr[b], rng)
            fits.append(m)
            idxs.append(idx)
            f1s.append(f1_score(yte, predict_sparse(kind, m, idx, Xte), zero_division=0))

        # P3: agreement across the five independent fits, on their mean per-flow attribution
        gm = [attr_sparse(kind, m, i, Xte).mean(0) for m, i in zip(fits, idxs)]
        p3 = mean_pairwise_jac(gm)
        # P2: agreement across three attribution definitions of the SAME fit (seed 0)
        p2 = mean_pairwise_jac(global_attrs(kind, fits[0], idxs[0], Xte, yte))

        # analyst calibration, same protocol as exp_auditor_control.py
        A0tr = attr_sparse(kind, fits[0], idxs[0], Xtr)
        g = RandomForestClassifier(n_estimators=80, max_depth=8, random_state=0).fit(A0tr, ytr)
        preds = np.stack([predict_sparse(kind, m, i, Xte) for m, i in zip(fits, idxs)], 1)
        tp = (yte == 1) & (preds == 1).all(1)
        if tp.sum() >= 50:
            acts = np.stack([g.predict(attr_sparse(kind, m, i, Xte[tp]))
                             for m, i in zip(fits, idxs)], 1)
            p_self = float((acts[:, 0] == 0).mean())
            p_cross = float((acts[:, 1:] == 0).mean())
        else:
            p_self = p_cross = float("nan")

        out.append({
            "dataset": ds, "model": kind,
            "n_features_used": int(np.median([len(i) for i in idxs])),
            "f1_mean": round(float(np.mean(f1s)), 3), "f1_std": round(float(np.std(f1s)), 3),
            "mlp_f1": round(mlp_f1, 3), "f1_gap_vs_mlp": round(mlp_f1 - float(np.mean(f1s)), 3),
            "p2_determinacy": round(p2, 3), "p3_groundedness": round(p3, 3),
            "p_self": round(p_self, 3), "p_cross": round(p_cross, 3),
            "p_excess": round(p_cross - p_self, 3),
        })
        r = out[-1]
        print("  %-13s %-11s nnz=%2d | F1 %.3f (MLP %.3f, gap %+0.3f) | P2 %.2f P3 %.2f | "
              "p_self %.3f -> p_cross %.3f" % (ds, kind, r["n_features_used"], r["f1_mean"],
                                               mlp_f1, -r["f1_gap_vs_mlp"], p2, p3, p_self, p_cross), flush=True)
    return out


def main():
    import time
    os.makedirs("results", exist_ok=True)
    rows = []
    t0 = time.time()
    for n, ds in enumerate(DATASETS, 1):
        t = time.time()
        rows.extend(run(ds))
        print("  [%d/%d] %s xong sau %.0fs (tong %.0fs)"
              % (n, len(DATASETS), ds, time.time() - t, time.time() - t0), flush=True)
    with open("results/sparse_bydesign.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote results/sparse_bydesign.csv (%d rows)" % len(rows))

    for kind in FITS:
        rs = [r for r in rows if r["model"] == kind]
        print("\n%-11s  F1 gap vs MLP %+0.3f  |  P2 %.2f  P3 %.2f  |  p_excess %+0.3f"
              % (kind, np.mean([r["f1_gap_vs_mlp"] for r in rs]),
                 np.mean([r["p2_determinacy"] for r in rs]),
                 np.mean([r["p3_groundedness"] for r in rs]),
                 np.nanmean([r["p_excess"] for r in rs])))


if __name__ == "__main__":
    main()
