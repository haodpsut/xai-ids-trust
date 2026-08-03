"""
Multi-seed rigor pass: repeat the headline measurements over several data/model seeds and
report mean +/- std, so no NDSS number rests on a single run. Covers P1 fidelity drop,
P2 determinacy (gradient-method agreement), P3 groundedness, and the reliability-detector AUC.
"""
import numpy as np, csv, os
from exp_trust import p1_fidelity, p2_determinacy, p3_groundedness
from exp_defense import run as defense_run
from data import load, DATASETS

SEEDS = [0, 1, 2]


def ci(vals):
    v = np.array(vals, float)
    return round(float(v.mean()), 3), round(float(v.std()), 3)


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = []
    for ds in DATASETS:
        p1d, p2m, p3a, auc = [], [], [], []
        for s in SEEDS:
            Xtr, ytr, Xte, yte, feats = load(ds, s)
            mlp, r1 = p1_fidelity(Xtr, ytr, Xte, yte)
            r2 = p2_determinacy(mlp, Xte, yte)
            r3 = p3_groundedness(Xtr, ytr, Xte, yte)
            p1d.append(r1["fidelity_drop"]); p2m.append(r2["mean_agree"]); p3a.append(r3["topk_jaccard"])
        # defense AUC already 5-fold CV internally; repeat across seeds for stability
        for s in SEEDS:
            auc.append(defense_run(ds)["detector_auc"])
        m = dict(dataset=ds)
        for name, vals in [("p1_fidelity_drop", p1d), ("p2_method_agree", p2m),
                           ("p3_seed_agree", p3a), ("defense_auc", auc)]:
            mean, sd = ci(vals); m[name + "_mean"] = mean; m[name + "_std"] = sd
        rows.append(m)
        print(f"{ds}: P1drop={m['p1_fidelity_drop_mean']}±{m['p1_fidelity_drop_std']} "
              f"P2={m['p2_method_agree_mean']}±{m['p2_method_agree_std']} "
              f"P3={m['p3_seed_agree_mean']}±{m['p3_seed_agree_std']} "
              f"AUC={m['defense_auc_mean']}±{m['defense_auc_std']}")
    with open("results/multiseed.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("wrote results/multiseed.csv")
