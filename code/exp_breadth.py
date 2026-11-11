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
# ⛔⛔ 11/11/2026, doc ngoai vong 3 diem 2(b). Ban cu lay NSAMP=120 luong, MOT hat,
# khong khoang tin cay. Ba thu do deu doc tu day: Bang A.15, Hinh 4, va cot eps_det
# cua bang do dung sai. Ma eps_det la `1 - min` tren MUOI uoc luong cap, nen voi n
# nho no bi CHECH XUONG mot cach co he thong: min cua muoi so nhieu thi thap hon min
# that. Tuc con so 0,86 co the mot phan la hien vat cua co mau.
# ⇒ [[feedback-so-cuc-tri-la-dau-hieu-bo-do-hong]] · [[feedback-tap-kiem-thien-lech]]
NSAMP = 1000         # SHAP/LIME van cham; day la muc doc ngoai vong 3 doi
SEEDS = (0, 1, 2)    # ba bo do doc lap, de tach nhieu lay mau khoi nhieu mo hinh
NBOOT = 2000         # so lan lay lai mau de dung khoang tin cay


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


def mot_hat(ds, Xtr, ytr, Xte, yte, feats, hat):
    """Tra ve {cap: vector Jaccard TUNG LUONG} cho mot bo do duoc gieo bang `hat`."""
    np.random.seed(hat); torch.manual_seed(hat)      # determinism for SHAP/LIME sampling
    din = Xtr.shape[1]
    mlp = train(MLP(din, match_mlp(din, nparams(KAN(din, 16, 4)))), Xtr, ytr, hat)
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
    tung_luong = {}
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            key = f"{names[a]}_vs_{names[b]}"
            tung_luong[key] = np.array(
                [_jac(tk[names[a]][r], tk[names[b]][r]) for r in range(len(Xm))])
    return tung_luong, len(Xm)


def run(ds):
    Xtr, ytr, Xte, yte, feats = load(ds)
    gom, n_luong = {}, []
    for h in SEEDS:
        tung, n = mot_hat(ds, Xtr, ytr, Xte, yte, feats, h)
        n_luong.append(n)
        for k, v in tung.items():
            gom.setdefault(k, []).append(v)
        print(f"    {ds} hat {h}: {n} luong", flush=True)
    cap = sorted(gom)

    # Trung binh tren CA ba bo do: noi hai truc nhieu lai roi lay trung binh.
    tb = {k: float(np.mean(np.concatenate(gom[k]))) for k in cap}

    # ⛔ Khoang tin cay cua `min tren cac cap`, khong phai cua tung cap roi lay min
    # cua cac can duoi: dai luong bai dung la CHINH cai min, nen phai lay lai mau
    # roi tinh lai min moi lan. ⇒ [[feedback-so-cuc-tri-la-dau-hieu-bo-do-hong]]
    rng = np.random.default_rng(0)
    noi = {k: np.concatenate(gom[k]) for k in cap}
    N = len(noi[cap[0]])
    mins = np.empty(NBOOT)
    for b in range(NBOOT):
        j = rng.integers(0, N, N)                   # lay lai mau THEO LUONG
        mins[b] = min(float(noi[k][j].mean()) for k in cap)
    lo, hi = (float(x) for x in np.percentile(mins, [2.5, 97.5]))
    cap_min = min(cap, key=lambda k: tb[k])

    hang = dict(dataset=ds, mean_all_pairs=round(float(np.mean(list(tb.values()))), 3),
                **{k: round(v, 3) for k, v in tb.items()})
    ci = dict(dataset=ds, n_flows=int(np.sum(n_luong)), n_seeds=len(SEEDS),
              min_pair=cap_min, min_mean=round(tb[cap_min], 3),
              min_lo=round(lo, 3), min_hi=round(hi, 3),
              eps_det=round(1 - tb[cap_min], 3),
              eps_det_lo=round(1 - hi, 3), eps_det_hi=round(1 - lo, 3))
    return hang, ci


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows, cis = [], []
    for ds in DATASETS:
        r, ci = run(ds); rows.append(r); cis.append(ci)
        print(f"{ds}: mean 5-explainer agreement={r['mean_all_pairs']} | worst pair "
              f"{ci['min_pair']}={ci['min_mean']} [{ci['min_lo']}, {ci['min_hi']}] "
              f"=> eps_det={ci['eps_det']} [{ci['eps_det_lo']}, {ci['eps_det_hi']}]", flush=True)
    keys = sorted(set().union(*[set(r) for r in rows]), key=lambda k: (k != "dataset", k))
    with open("results/breadth.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in keys})
    with open("results/breadth_ci.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cis[0].keys())); w.writeheader()
        w.writerows(cis)
    print("wrote results/breadth.csv va results/breadth_ci.csv")
