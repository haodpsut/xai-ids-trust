"""
Reviewer stress-test (feature redundancy). Flow features are highly redundant (e.g. CICIDS
'Fwd Packet Length Mean' vs 'Max'), so a raw top-k Jaccard may score two explainers that pick
DIFFERENT-BUT-EQUIVALENT features as a disagreement. We re-measure determinacy (P2) and
groundedness (P3) after collapsing features into Spearman-correlation clusters: a top-k set is
mapped to the SET OF CLUSTERS it touches, and agreement is Jaccard over clusters. If the failures
survive clustering, they are semantic, not a redundancy artifact; if agreement jumps to ~1.0, the
paper's claim is (partly) an artifact and must be reframed.

Deterministic (seeded). Reports raw vs clustered agreement at several correlation thresholds.
"""
import numpy as np, torch, csv, os, warnings
warnings.filterwarnings("ignore")
from scipy.stats import spearmanr
from sklearn.metrics import f1_score
from harness import (MLP, KAN, nparams, match_mlp, train, predict, saliency, topk_features,
                     input_x_gradient, integrated_gradients, flow_bao_dong)
from data import load, DATASETS

K = 5
TAUS = [0.80, 0.90, 0.95]        # |rho| thresholds for "near-duplicate" feature clusters


def clusters(Xtr, tau):
    """Union-find connected components of features with |Spearman rho| >= tau."""
    d = Xtr.shape[1]
    rho = np.atleast_2d(spearmanr(Xtr).correlation).astype(float)
    rho = np.nan_to_num(rho, nan=0.0)                 # constant features -> uncorrelated
    parent = list(range(d))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x

    for i in range(d):
        for j in range(i + 1, d):
            if abs(rho[i, j]) >= tau:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj
    cid = np.array([find(i) for i in range(d)])
    return cid, len(set(cid.tolist()))


def jac_raw(a, b):
    sa, sb = set(a.tolist()), set(b.tolist())
    return len(sa & sb) / len(sa | sb)


def jac_clustered(a, b, cid):
    sa, sb = set(cid[a].tolist()), set(cid[b].tolist())
    return len(sa & sb) / len(sa | sb)


def p2_pairs(mlp, Xte, yte):
    """Top-k sets from the three gradient-family methods on flagged-malicious flows."""
    idx = flow_bao_dong(mlp, Xte, yte, 1000)
    Xm = Xte[idx]
    return [topk_features(saliency(mlp, Xm), K),
            topk_features(input_x_gradient(mlp, Xm), K),
            topk_features(integrated_gradients(mlp, Xm), K)]


def p3_sets(Xtr, ytr, Xte, yte, din, h):
    models = [train(MLP(din, h), Xtr, ytr, s) for s in range(4)]
    # ⛔ cung cap loi nhu exp_trust.py: xem chu thich o do.
    sub = Xte[flow_bao_dong(models, Xte, yte, 1000)]
    return [topk_features(saliency(m, sub), K) for m in models], len(sub)


def mean_pairwise(tks, n, fn):
    vals = []
    for a in range(len(tks)):
        for b in range(a + 1, len(tks)):
            vals += [fn(tks[a][r], tks[b][r]) for r in range(n)]
    return float(np.mean(vals))


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = []
    for ds in DATASETS:
        np.random.seed(0); torch.manual_seed(0)
        Xtr, ytr, Xte, yte, feats = load(ds)
        din = Xtr.shape[1]; h = match_mlp(din, nparams(KAN(din, 16, 4)))
        mlp = train(MLP(din, h), Xtr, ytr, 0)

        # P2 determinacy (3 gradient methods, same model)
        p2 = p2_pairs(mlp, Xte, yte); n2 = len(p2[0])
        p2_raw = mean_pairwise(p2, n2, jac_raw)
        # P3 groundedness (4 seeds)
        p3, n3 = p3_sets(Xtr, ytr, Xte, yte, din, h)
        p3_raw = mean_pairwise(p3, n3, jac_raw)

        rec = dict(dataset=ds, n_features=din, p2_raw=round(p2_raw, 3), p3_raw=round(p3_raw, 3))
        line = f"{ds:8s} d={din:2d} | P2 raw={p2_raw:.3f}  P3 raw={p3_raw:.3f}"
        for tau in TAUS:
            cid, ncl = clusters(Xtr, tau)
            p2_c = mean_pairwise(p2, n2, lambda a, b: jac_clustered(a, b, cid))
            p3_c = mean_pairwise(p3, n3, lambda a, b: jac_clustered(a, b, cid))
            t = str(int(tau * 100))
            rec[f"n_clusters_{t}"] = ncl
            rec[f"p2_clustered_{t}"] = round(p2_c, 3)
            rec[f"p3_clustered_{t}"] = round(p3_c, 3)
            line += f"  || tau={tau} clusters={ncl:2d}: P2={p2_c:.3f} P3={p3_c:.3f}"
        rows.append(rec)
        print(line)

    with open("results/redundancy.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("\nwrote results/redundancy.csv")
