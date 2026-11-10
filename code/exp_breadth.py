"""
Breadth for P2 (determinacy): does explanation method-disagreement hold across FUNDAMENTALLY
different explainer families, not just the gradient family? We add KernelSHAP and LIME (both
model-agnostic, perturbation-based) and measure top-k agreement among five explainers:
gradient saliency, input x gradient, integrated gradients, KernelSHAP, LIME. If even these
disagree, "the reason" the analyst is shown is deeply under-determined. Pre-empts the standard
"you only tried gradient methods" objection.

SHAP/LIME are expensive; we run them on a modest sample of flagged-malicious flows.
"""
import numpy as np, torch, csv, os, warnings
warnings.filterwarnings("ignore")
import shap
from lime.lime_tabular import LimeTabularExplainer
from harness import (MLP, KAN, nparams, match_mlp, train, predict, saliency,
                     input_x_gradient, integrated_gradients, topk_features, flow_bao_dong)
from data import load, DATASETS

TOPK = 5
NSAMP = 120          # SHAP/LIME are slow; modest sample


def _jac(a, b):
    return len(set(a) & set(b)) / len(set(a) | set(b))


def proba_fn(model):
    def f(X):
        with torch.no_grad():
            z = model(torch.tensor(np.asarray(X), dtype=torch.float32))
            return torch.softmax(z, 1).numpy()
    return f


def shap_topk(model, Xbg, Xm):
    f = proba_fn(model)
    expl = shap.KernelExplainer(f, shap.kmeans(Xbg, 15))
    sv = expl.shap_values(Xm, nsamples=1000, silent=True)
    sv = sv[1] if isinstance(sv, list) else sv[..., 1]           # attack-class attributions
    return topk_features(np.asarray(sv), TOPK)


def lime_topk(model, Xtr, Xm, feats):
    f = proba_fn(model)
    ex = LimeTabularExplainer(Xtr, feature_names=[str(c) for c in feats],
                              class_names=["benign", "attack"], discretize_continuous=False,
                              mode="classification", random_state=0)
    out = np.zeros((len(Xm), TOPK), int)
    for r in range(len(Xm)):
        e = ex.explain_instance(Xm[r], f, num_features=TOPK, labels=(1,), num_samples=3000)
        out[r] = [idx for idx, _ in e.local_exp[1][:TOPK]]
    return out


def run(ds):
    np.random.seed(0); torch.manual_seed(0)             # determinism for SHAP/LIME sampling
    Xtr, ytr, Xte, yte, feats = load(ds)
    din = Xtr.shape[1]
    mlp = train(MLP(din, match_mlp(din, nparams(KAN(din, 16, 4)))), Xtr, ytr, 0)
    idx = flow_bao_dong(mlp, Xte, yte, NSAMP)
    Xm = Xte[idx]
    tk = {
        "grad": topk_features(saliency(mlp, Xm), TOPK),
        "ixg": topk_features(input_x_gradient(mlp, Xm), TOPK),
        "ig": topk_features(integrated_gradients(mlp, Xm), TOPK),
        "shap": shap_topk(mlp, Xtr[:1500], Xm),
        "lime": lime_topk(mlp, Xtr[:1500], Xm, feats),
    }
    names = list(tk)
    ov = {}
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            key = f"{names[a]}_vs_{names[b]}"
            ov[key] = float(np.mean([_jac(tk[names[a]][r], tk[names[b]][r]) for r in range(len(Xm))]))
    allpairs = float(np.mean(list(ov.values())))
    return dict(dataset=ds, mean_all_pairs=round(allpairs, 3),
                **{k: round(v, 3) for k, v in ov.items()})


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = []
    for ds in DATASETS:
        r = run(ds); rows.append(r)
        print(f"{ds}: mean 5-explainer agreement={r['mean_all_pairs']} | SHAP-vs-LIME={r.get('shap_vs_lime')} "
              f"| grad-vs-SHAP={r.get('grad_vs_shap')}")
    keys = sorted(set().union(*[set(r) for r in rows]), key=lambda k: (k != "dataset", k))
    with open("results/breadth.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in keys})
    print("wrote results/breadth.csv")
