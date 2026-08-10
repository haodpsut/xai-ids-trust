"""
New measurement axis: FAITHFULNESS (not agreement). An explanation is faithful if the features it
names are the ones the model actually uses. We measure the two standard faithfulness metrics
(ERASER; DeYoung et al. 2020) for each explainer on each dataset, on flagged-attack flows:

  COMPREHENSIVENESS: drop the top-k attributed features (mean-impute) -> how much does the
    attack-probability fall? A faithful explanation names features whose removal hurts a lot.
  SUFFICIENCY: keep only the top-k features -> how much attack-probability remains? A faithful
    explanation's top-k should suffice; low sufficiency means the reason is not enough.

We report comprehensiveness (higher = more faithful) and sufficiency-gap = p_full - p_topk
(lower = more faithful). This adds a faithfulness axis to the agreement-based P1-P3, and answers
our own caveat that stability is not faithfulness.
"""
import numpy as np, torch, csv, os, warnings
warnings.filterwarnings("ignore")
from harness import MLP, KAN, nparams, match_mlp, train, predict, saliency, topk_features
from data import load, DATASETS

TOPK = 5


def prob_attack(model, X):
    with torch.no_grad():
        return torch.softmax(model(torch.tensor(X, dtype=torch.float32)), 1)[:, 1].numpy()


def run(ds):
    np.random.seed(0); torch.manual_seed(0)             # determinism
    Xtr, ytr, Xte, yte, feats = load(ds); din = Xtr.shape[1]
    f = train(MLP(din, match_mlp(din, nparams(KAN(din, 16, 4)))), Xtr, ytr, 0)
    idx = np.where((predict(f, Xte) == 1) & (yte == 1))[0][:1500]
    Xm = Xte[idx]; base = Xtr.mean(0)
    p_full = prob_attack(f, Xm)
    tk = topk_features(saliency(f, Xm), TOPK)
    # comprehensiveness: remove top-k
    Xrm = Xm.copy()
    for r in range(len(Xm)):
        Xrm[r, tk[r]] = base[tk[r]]
    comp = float((p_full - prob_attack(f, Xrm)).mean())
    # sufficiency: keep only top-k
    Xkeep = np.tile(base, (len(Xm), 1)).astype(np.float32)
    for r in range(len(Xm)):
        Xkeep[r, tk[r]] = Xm[r, tk[r]]
    suff_gap = float((p_full - prob_attack(f, Xkeep)).mean())
    return dict(dataset=ds, deployed_attack_prob=round(float(p_full.mean()), 3),
                comprehensiveness=round(comp, 3), sufficiency_gap=round(suff_gap, 3))


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = [run(ds) for ds in DATASETS]
    with open("results/faithfulness.csv", "w", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    for r in rows:
        print(f"{r['dataset']}: comprehensiveness={r['comprehensiveness']} "
              f"sufficiency-gap={r['sufficiency_gap']} (p_full={r['deployed_attack_prob']})")
    print("wrote results/faithfulness.csv")
