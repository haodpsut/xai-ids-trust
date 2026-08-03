"""
E: fidelity is not a KAN-symbolic artifact. We test the fidelity property across several standard
``interpretable renderings'' of a deployed MLP-IDS: (1) a depth-capped decision tree, (2) a
sparse logistic model, (3) a shallow rule list via a depth-2 tree, each fit to MIMIC the deployed
model (global post-hoc surrogate, the standard interpretable-by-approximation story). We report
the surrogate's decision agreement with the deployed model and its detection F1. If any faithful,
readable surrogate existed, fidelity would hold; it does not.
"""
import numpy as np, csv, os, warnings
warnings.filterwarnings("ignore")
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, accuracy_score
from harness import MLP, KAN, nparams, match_mlp, train, predict
from data import load, DATASETS


def run(ds):
    Xtr, ytr, Xte, yte, feats = load(ds)
    din = Xtr.shape[1]
    f = train(MLP(din, match_mlp(din, nparams(KAN(din, 16, 4)))), Xtr, ytr, 0)
    ftr, fte = predict(f, Xtr), predict(f, Xte)         # deployed model's decisions
    f1_dep = f1_score(yte, fte)
    surr = {
        "tree(d=4)": DecisionTreeClassifier(max_depth=4, random_state=0),
        "tree(d=2)": DecisionTreeClassifier(max_depth=2, random_state=0),
        "sparse-logit": LogisticRegression(penalty="l1", solver="liblinear", C=0.1, max_iter=300),
    }
    out = dict(dataset=ds, deployed_f1=round(float(f1_dep), 3))
    for name, m in surr.items():
        m.fit(Xtr, ftr)                                  # distill: mimic deployed decisions
        pred = m.predict(Xte)
        agree = accuracy_score(fte, pred)                # fidelity: same decisions as deployed?
        f1s = f1_score(yte, pred)
        out[f"{name}_agree"] = round(float(agree), 3)
        out[f"{name}_f1"] = round(float(f1s), 3)
    return out


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = [run(ds) for ds in DATASETS]
    keys = list(rows[0].keys())
    with open("results/fidelity_multi.csv", "w", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=keys); w.writeheader(); w.writerows(rows)
    for r in rows:
        print(f"{r['dataset']}: deployed F1={r['deployed_f1']} | "
              + " ".join(f"{k.replace('_agree','')}=agree{r[k]}" for k in r if k.endswith('_agree')))
    print("wrote results/fidelity_multi.csv")
