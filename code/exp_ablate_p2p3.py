"""
Phase-2 ablations for determinacy (P2) and groundedness (P3):
  P2 x k     -- does cross-method top-k agreement improve if we show more features (k=3/5/10)?
  P3 x E     -- does cross-seed explanation agreement stabilize with a larger ensemble (E=4/6/10)?
Both test whether the failures are artifacts of our specific k or ensemble size. They are not.
"""
import numpy as np, csv, os, warnings
warnings.filterwarnings("ignore")
from harness import (MLP, KAN, nparams, match_mlp, train, predict, saliency,
                     input_x_gradient, integrated_gradients)
from data import load, DATASETS


def topk(attr, k):
    return np.argsort(-np.abs(attr), axis=1)[:, :k]


def jac(a, b):
    return len(set(a) & set(b)) / len(set(a) | set(b))


def p2_at_k(f, Xm, k):
    A = [saliency(f, Xm), input_x_gradient(f, Xm), integrated_gradients(f, Xm)]
    tks = [topk(a, k) for a in A]
    ov = []
    for i in range(3):
        for j in range(i + 1, 3):
            ov += [jac(tks[i][r], tks[j][r]) for r in range(len(Xm))]
    return float(np.mean(ov))


def p3_at_E(models, Xm, k=5):
    tks = [topk(saliency(m, Xm), k) for m in models]
    ov = []
    for i in range(len(models)):
        for j in range(i + 1, len(models)):
            ov += [jac(tks[i][r], tks[j][r]) for r in range(len(Xm))]
    return float(np.mean(ov))


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rk, rE = [], []
    for ds in DATASETS:
        Xtr, ytr, Xte, yte, feats = load(ds); din = Xtr.shape[1]
        h = match_mlp(din, nparams(KAN(din, 16, 4)))
        models = [train(MLP(din, h), Xtr, ytr, s) for s in range(10)]
        idx = np.where((predict(models[0], Xte) == 1) & (yte == 1))[0][:1000]
        Xm = Xte[idx]
        row_k = dict(dataset=ds)
        for k in [3, 5, 10]:
            row_k[f"k{k}"] = round(p2_at_k(models[0], Xm, k), 3)
        rk.append(row_k)
        row_e = dict(dataset=ds)
        for E in [4, 6, 10]:
            row_e[f"E{E}"] = round(p3_at_E(models[:E], Xm), 3)
        rE.append(row_e)
        print(f"{ds}: P2 k3/5/10={row_k['k3']}/{row_k['k5']}/{row_k['k10']} | "
              f"P3 E4/6/10={row_e['E4']}/{row_e['E6']}/{row_e['E10']}")
    with open("results/ablate_p2k.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rk[0].keys())); w.writeheader(); w.writerows(rk)
    with open("results/ablate_p3E.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rE[0].keys())); w.writeheader(); w.writerows(rE)
    print("wrote results/ablate_p2k.csv, ablate_p3E.csv")
