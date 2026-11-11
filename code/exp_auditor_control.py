"""IV-1 controls for the action-divergence measurement of exp_harm.py.

Why this exists. `harm.csv` reports a suppression rate and an action-divergence rate, and the
paper quotes them as evidence that explanation instability causes a security harm. Neither number
was ever placed against a floor, so neither could be falsified. An external reviewer on
11/08/2026 asked the obvious question -- is the divergence anything more than five independent
coin flips at the observed suppression rate? -- and the paper had no answer in it. That is a
violation of our own rule: every headline ratio must be printed next to the value it would take
when the effect under study is switched off.

Four controls, all on the same true-positive flows exp_harm.py uses:

  1. AUDITOR COMPETENCE. The analyst is a classifier trained on model 0's TRAINING explanations.
     If it cannot recover the label from model 0's own TEST explanations, then a "suppressed"
     attack says nothing about explanation instability -- it is just auditor error. `p_self` is
     that floor; `p_cross` is the rate on the four models the auditor never saw. The quantity the
     paper is entitled to claim is the EXCESS, p_cross - p_self.

  2. INDEPENDENCE NULL. Divergence is 1 - P(all five escalate) - P(all five suppress). If the
     five per-model actions were independent Bernoulli(p) with p the observed marginal, divergence
     would be exactly 1 - p^5 - (1-p)^5. Note the exponent is FIVE: exp_harm.py trains K=5 seeds.
     Excess above this null is the only part of divergence that is not already implied by the
     suppression rate; without it, divergence and suppression rate are one finding, not two.

  3. SHUFFLE NULL. The analytic null assumes a single p shared by all flows. Real flows are
     heterogeneous, which pushes divergence down for reasons that have nothing to do with
     explanations. Permuting each model's action column independently across flows keeps every
     per-model marginal and destroys only the flow-level coupling, giving a null that survives
     heterogeneity. Reported alongside, because where the two nulls disagree, this one is right.

  4. SIGNAL-FREE ATTRIBUTIONS. Feed the auditor attribution vectors drawn by permuting each
     feature's attribution column across flows. Attribution magnitudes and the marginal
     distribution are preserved; the link between a flow and its explanation is gone. If
     divergence here matches divergence there, the explanations carry no decision-relevant signal
     at all and the harm claim collapses.

Reads nothing from harm.csv: the models, auditors and actions are retrained here from data.py
with the same seeds, so `p_all` reproduces harm.csv's `suppression_rate` and `div_measured`
reproduces its `action_divergence`. Those two columns are the cross-check that this file and
harm.csv describe the same experiment; if they ever disagree, one of the two scripts has drifted.
"""
import csv
import os
import warnings

import numpy as np
import torch

warnings.filterwarnings("ignore")
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from data import DATASETS, load
from harness import KAN, MLP, match_mlp, nparams, predict, saliency, train, flow_bao_dong, quy_gan_chuan_hoa

K = 5


# ⛔ MOT dinh nghia, o harness.quy_gan_chuan_hoa. Xem ghi chu o do.
attr = quy_gan_chuan_hoa


def divergence(actions):
    """Fraction of flows on which the K models do not agree. actions: [n, K] of 0/1."""
    unan = (actions == 1).all(1) | (actions == 0).all(1)
    return float((~unan).mean())


def null_independent(p, k=K):
    """Divergence if the k per-model actions were independent Bernoulli(p)."""
    return 1.0 - p ** k - (1.0 - p) ** k


def run(ds, rng):
    np.random.seed(0)
    torch.manual_seed(0)
    Xtr, ytr, Xte, yte, feats = load(ds)
    din = Xtr.shape[1]
    h = match_mlp(din, nparams(KAN(din, 16, 4)))
    models = [train(MLP(din, h), Xtr, ytr, s) for s in range(K)]

    preds = np.stack([predict(m, Xte) for m in models], 1)
    # ⛔ `tp` o day dung CA HAI vai: `Xte[tp]` va `int(tp.sum())`. Phai lay MAT NA,
    # khong thi `.sum()` cong CAC CHI SO lai: do la cach `n_true_attacks` ra
    # 47012435 thay vi 7851 ngay 10/11/2026. Truyen `du_doan=preds` de khong
    # chay lai 5 lan `predict` va de `preds` van la nguon duy nhat.
    tp = flow_bao_dong(None, Xte, yte, mat_na=True, du_doan=preds)
    Xtp = Xte[tp]
    A0tr = attr(models[0], Xtr)
    Atp = [attr(m, Xtp) for m in models]
    A0te = attr(models[0], Xte)

    out = []
    for name in ("logistic", "rf"):
        if name == "logistic":
            g = LogisticRegression(max_iter=300).fit(A0tr, ytr)
        else:
            g = RandomForestClassifier(n_estimators=80, max_depth=8, random_state=0).fit(A0tr, ytr)

        # 1. auditor competence, measured on the model it was trained to read
        acc = float((g.predict(A0te) == yte).mean())
        actions = np.stack([g.predict(a) for a in Atp], 1)          # [n_tp, K]
        p_self = float((actions[:, 0] == 0).mean())                 # model 0: the auditor's own floor
        p_cross = float((actions[:, 1:] == 0).mean())               # four unseen seeds
        p_all = float((actions == 0).mean())                        # == harm.csv suppression_rate

        div_meas = divergence(actions)
        div_null = null_independent(p_all)

        # 3. shuffle null: keep every per-model marginal, destroy the flow-level coupling
        sh = np.empty((512,), dtype=float)
        for b in range(sh.size):
            perm = np.stack([rng.permutation(actions[:, j]) for j in range(K)], 1)
            sh[b] = divergence(perm)
        div_shuffle = float(sh.mean())
        div_shuffle_sd = float(sh.std())

        # 4. signal-free attributions: same marginals per feature, no flow-explanation link
        dr = np.empty((16,), dtype=float)
        pr = np.empty((16,), dtype=float)
        for b in range(dr.size):
            fake = np.stack(
                [g.predict(np.stack([rng.permutation(a[:, c]) for c in range(a.shape[1])], 1))
                 for a in Atp], 1)
            dr[b] = divergence(fake)
            pr[b] = float((fake == 0).mean())
        div_rand = float(dr.mean())
        p_rand = float(pr.mean())

        out.append({
            "dataset": ds, "auditor": name, "n_true_attacks": int(tp.sum()),
            "auditor_test_acc": round(acc, 3),
            "p_self": round(p_self, 3), "p_cross": round(p_cross, 3),
            "p_excess": round(p_cross - p_self, 3), "p_all": round(p_all, 3),
            "div_measured": round(div_meas, 3),
            "div_null_indep": round(div_null, 3),
            "div_excess": round(div_meas - div_null, 3),
            "div_shuffle": round(div_shuffle, 3),
            "div_shuffle_sd": round(div_shuffle_sd, 4),
            "div_excess_shuffle": round(div_meas - div_shuffle, 3),
            "p_rand_attr": round(p_rand, 3),
            "div_rand_attr": round(div_rand, 3),
        })
        r = out[-1]
        print("  %-13s [%-8s] acc=%.3f | p_self=%.3f p_cross=%.3f (excess %+0.3f) | "
              "div=%.3f null=%.3f shuffle=%.3f (excess %+0.3f) | rand-attr div=%.3f"
              % (ds, name, acc, p_self, p_cross, p_cross - p_self, div_meas, div_null,
                 div_shuffle, div_meas - div_shuffle, div_rand))
    return out


def main():
    os.makedirs("results", exist_ok=True)
    rng = np.random.default_rng(0)
    rows = []
    for ds in DATASETS:
        rows.extend(run(ds, rng))
    with open("results/auditor_control.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote results/auditor_control.csv (%d rows)" % len(rows))

    above = [r for r in rows if r["div_excess_shuffle"] > 0.02]
    at = [r for r in rows if abs(r["div_excess_shuffle"]) <= 0.02]
    print("\nrows ABOVE the shuffle null by >0.02: %d/%d" % (len(above), len(rows)))
    print("rows INDISTINGUISHABLE from it (|excess| <= 0.02): %d/%d" % (len(at), len(rows)))


if __name__ == "__main__":
    main()
