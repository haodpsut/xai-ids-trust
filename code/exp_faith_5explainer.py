"""
Phase-2: faithfulness is not a gradient-only problem. We compute comprehensiveness (drop in
attack-probability when the top-5 attributed features are removed) for all FIVE explainers,
including SHAP and LIME. If SHAP/LIME are also unfaithful, no popular explainer escapes.
"""
import numpy as np, torch, csv, os, warnings
warnings.filterwarnings("ignore")
import shap
from lime.lime_tabular import LimeTabularExplainer
from harness import (MLP, KAN, nparams, match_mlp, train, predict, saliency,
                     input_x_gradient, integrated_gradients, topk_features)
from data import load, DATASETS

TOPK = 5
NSAMP = 120


def prob_attack(model, X):
    with torch.no_grad():
        return torch.softmax(model(torch.tensor(X, dtype=torch.float32)), 1)[:, 1].numpy()


def proba_fn(model):
    def f(X):
        with torch.no_grad():
            return torch.softmax(model(torch.tensor(np.asarray(X), dtype=torch.float32)), 1).numpy()
    return f


def comp_of_topk(model, Xm, base, tk):
    Xrm = Xm.copy()
    for r in range(len(Xm)):
        Xrm[r, tk[r]] = base[tk[r]]
    return float((prob_attack(model, Xm) - prob_attack(model, Xrm)).mean())


def run(ds):
    np.random.seed(0); torch.manual_seed(0)             # determinism for SHAP/LIME sampling
    Xtr, ytr, Xte, yte, feats = load(ds); din = Xtr.shape[1]
    f = train(MLP(din, match_mlp(din, nparams(KAN(din, 16, 4)))), Xtr, ytr, 0)
    idx = np.where((predict(f, Xte) == 1) & (yte == 1))[0][:NSAMP]
    Xm = Xte[idx]; base = Xtr.mean(0)
    tks = {
        "grad": topk_features(saliency(f, Xm), TOPK),
        "ixg": topk_features(input_x_gradient(f, Xm), TOPK),
        "ig": topk_features(integrated_gradients(f, Xm), TOPK),
    }
    sv = shap.KernelExplainer(proba_fn(f), shap.kmeans(Xtr[:1500], 15)).shap_values(Xm, nsamples=300, silent=True)
    sv = sv[1] if isinstance(sv, list) else sv[..., 1]
    tks["shap"] = topk_features(np.asarray(sv), TOPK)
    ex = LimeTabularExplainer(Xtr[:1500], feature_names=[str(c) for c in feats],
                              discretize_continuous=False, mode="classification", random_state=0)
    lime_tk = np.zeros((len(Xm), TOPK), int)
    for r in range(len(Xm)):
        e = ex.explain_instance(Xm[r], proba_fn(f), num_features=TOPK, labels=(1,), num_samples=800)
        lime_tk[r] = [i for i, _ in e.local_exp[1][:TOPK]]
    tks["lime"] = lime_tk
    return dict(dataset=ds, **{m: round(comp_of_topk(f, Xm, base, tk), 3) for m, tk in tks.items()})


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = [run(ds) for ds in DATASETS]
    with open("results/faith_5explainer.csv", "w", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    for r in rows:
        print(f"{r['dataset']}: comprehensiveness grad={r['grad']} ixg={r['ixg']} ig={r['ig']} "
              f"shap={r['shap']} lime={r['lime']}")
    print("wrote results/faith_5explainer.csv")
