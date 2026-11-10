"""
Reviewer stress-test (metric ceiling / positive control). The paper's bar is "each property must
score ~1.0, and none does on real NIDS." A skeptic could reply: maybe the metrics are simply
unsatisfiable by construction. We refute that here. We build a SYNTHETIC task with (i) decorrelated
features and (ii) a KNOWN sparse ground-truth: only k of d independent Gaussian features drive a
linearly separable label. On this favorable construction the three properties SHOULD score ~1.0:
  P1 fidelity     -- the decision is (near) linear, so an interpretable surrogate reproduces it.
  P2 determinacy  -- one strong sparse signal, so every attribution method points to the same top-k.
  P3 groundedness -- a unique strong solution, so seeds converge on the same features.
We then turn a difficulty knob (spread the signal over more features, i.e. remove the sparse,
decorrelated structure that interpretability implicitly assumes) and show the scores fall toward
the real-NIDS regime. The metrics are therefore satisfiable AND calibrated, not rigged to fail.

Deterministic (seeded).
"""
import numpy as np, torch, csv, os, warnings
warnings.filterwarnings("ignore")
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from harness import MLP, KAN, nparams, match_mlp, train, predict, saliency, topk_features, flow_bao_dong
from exp_trust import p1_fidelity, p2_determinacy, p3_groundedness

D = 32                       # total features (all independent -> decorrelated)
N = 40000
TOPK = 5


def make_synthetic(n_informative, seed=0, gain=4.0):
    """Independent N(0,1) features; label is a sparse linear rule on the first n_informative,
    balanced by its own median. gain makes the informative signal dominate. Returns the standard
    (Xtr, ytr, Xte, yte, feats) tuple plus the set of TRUE informative feature indices."""
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((N, D)).astype(np.float32)            # decorrelated by construction
    w = rng.choice([-1.0, 1.0], size=n_informative) * rng.uniform(0.6, 1.4, n_informative)
    z = gain * (X[:, :n_informative] @ w.astype(np.float32))
    y = (z > np.median(z)).astype(int)                           # balanced, linearly separable
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)
    sc = StandardScaler().fit(Xtr)
    Xtr = sc.transform(Xtr).astype(np.float32); Xte = sc.transform(Xte).astype(np.float32)
    return Xtr, ytr, Xte, yte, [f"f{i}" for i in range(D)], set(range(n_informative))


def gt_recovery(Xtr, ytr, Xte, yte, true_set):
    """Does the model's top-5 saliency land on the TRUE informative features? (groundedness vs an
    actual ground truth, not just cross-seed agreement)."""
    din = Xtr.shape[1]; h = match_mlp(din, nparams(KAN(din, 16, 4)))
    m = train(MLP(din, h), Xtr, ytr, 0)
    idx = flow_bao_dong(m, Xte, yte, 1000)
    tk = topk_features(saliency(m, Xte[idx]), TOPK)
    hit = np.mean([len(set(tk[r].tolist()) & true_set) / TOPK for r in range(len(idx))])
    return float(hit)


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    # EASY = sparse+decorrelated (ceiling); MED/HARD spread the signal over more features
    regimes = [("sparse-k5", 5), ("mid-k12", 12), ("diffuse-k28", 28)]
    rows = []
    for name, k in regimes:
        np.random.seed(0); torch.manual_seed(0)
        Xtr, ytr, Xte, yte, feats, true_set = make_synthetic(k)
        mlp, r1 = p1_fidelity(Xtr, ytr, Xte, yte)
        r2 = p2_determinacy(mlp, Xte, yte)
        r3 = p3_groundedness(Xtr, ytr, Xte, yte)
        rec = gt_recovery(Xtr, ytr, Xte, yte, true_set)
        p1_ret = 1.0 - r1["fidelity_drop"]                       # fidelity RETENTION (1.0 = perfect)
        row = dict(regime=name, k_informative=k,
                   p1_fidelity_retention=round(p1_ret, 3),
                   p1_topk_sufficiency=round(r1["topk5_sufficiency"], 3),
                   p2_determinacy=round(r2["mean_agree"], 3),
                   p3_groundedness=round(r3["topk_jaccard"], 3),
                   gt_recovery=round(rec, 3))
        rows.append(row)
        print(f"{name:12s} (k={k:2d}) | P1-fid-retain={row['p1_fidelity_retention']:.3f} "
              f"P1-suff={row['p1_topk_sufficiency']:.3f} P2-det={row['p2_determinacy']:.3f} "
              f"P3-grnd={row['p3_groundedness']:.3f} | GT-recovery={row['gt_recovery']:.3f}")
    with open("results/ceiling.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("\nwrote results/ceiling.csv")
