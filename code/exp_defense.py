"""
Pivot (c): a constructive defense. Since interpretability-based trust fails by default
(P1-P3), we do not ask the analyst to trust blindly; we give a per-alarm RELIABILITY GATE that
predicts whether THIS flow's explanation can be trusted, cheaply, from a single deployed model.

Ground-truth reliability (expensive; the thing we want but cannot run per alarm): an explanation
is reliable for a flow if it is STABLE, i.e. its top-k features agree both across an ensemble of
equally-good models (groundedness holds locally) and across attribution methods (determinacy
holds locally). We label a flow's explanation "reliable" if this combined stability exceeds a
threshold.

Cheap detector (deployable; single model, no ensemble): predict reliability from signals an
analyst-side tool can compute on one model: decision margin, attribution concentration (how
peaked the explanation is), local linear surrogate fidelity, and an out-of-distribution score.
If the cheap detector predicts the expensive reliability well (high AUC), the analyst can be told
when NOT to trust an explanation, for free. That is the constructive contribution.
"""
import numpy as np, torch, csv, os
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import cross_val_score
from scipy.stats import spearmanr
from harness import (MLP, KAN, nparams, match_mlp, train, predict, saliency,
                     input_x_gradient, integrated_gradients, topk_features, flow_bao_dong)
from data import load, DATASETS

K = 5            # ensemble size for ground-truth stability
TOPK = 5


def _jac(a, b):
    return len(set(a) & set(b)) / len(set(a) | set(b))


def ground_truth_reliability(models, Xm):
    """Combined stability in [0,1]: mean top-k agreement across models AND across 3 methods,
    per flow. High = the explanation would be reproduced by an equally-good model and another
    method (P2 and P3 hold locally) = reliable."""
    # cross-model (groundedness): pairwise top-k Jaccard of gradient saliency across ensemble
    tks = [topk_features(saliency(m, Xm), TOPK) for m in models]
    n = len(Xm)
    cm = np.zeros(n)
    cnt = 0
    for a in range(len(models)):
        for b in range(a + 1, len(models)):
            cm += np.array([_jac(tks[a][r], tks[b][r]) for r in range(n)]); cnt += 1
    cm /= cnt
    # cross-method (determinacy) on the deployed model (model 0)
    g = topk_features(saliency(models[0], Xm), TOPK)
    ixg = topk_features(input_x_gradient(models[0], Xm), TOPK)
    ig = topk_features(integrated_gradients(models[0], Xm), TOPK)
    cx = np.array([(_jac(g[r], ixg[r]) + _jac(g[r], ig[r]) + _jac(ixg[r], ig[r])) / 3 for r in range(n)])
    return 0.5 * cm + 0.5 * cx


def cheap_signals(model, Xm, Xtr):
    """Signals computable on ONE deployed model at alarm time."""
    with torch.no_grad():
        logit = model(torch.tensor(Xm, dtype=torch.float32)).numpy()
    margin = np.abs(logit[:, 1] - logit[:, 0])                    # decision confidence
    a = np.abs(saliency(model, Xm)) + 1e-12
    p = a / a.sum(1, keepdims=True)
    # ⛔⛔ TRUOC 11/11/2026 dong nay la `-(p*log p).sum(1)`, tuc ENTROPY, va chu
    # thich goi no la "attribution entropy (peakedness)", gop hai thu TRAI NGHIA
    # vao mot dong. Bien thi ten `concentration`. Proposition cua bai dinh nghia
    # kappa = sum p log p = -H, "high when peaked", nen MA va BAI dung hai dai luong
    # NGUOC DAU nhau duoi cung mot ten. AUC khong thay doi (hoi quy logistic hut
    # dau vao trong so), nen khong cong nao thay. Nhung:
    #   1. `conc_rel_rho` doi dau, va bai doc no canh Proposition de noi ve HUONG.
    #   2. `exp_gate_attack.py` day diem cong bang `w[1] * (-ent)`, tuc no GIA DINH
    #      dac trung la -H; voi dac trung +H thi mot trong hai thanh phan gradient
    #      cua tan cong day NGUOC huong, nen so tan cong bai bao la CHAN DUOI.
    # Sua o DAY, mot cho duy nhat, thi ca bon script dung cheap_signals deu khop.
    # ⇒ [[feedback-nhan-cot-giong-nhau-nghia-khac-nhau]] · [[feedback-mot-tham-so-dieu-khien-hai-thu]]
    concentration = (p * np.log(p)).sum(1)        # kappa = -H, cao khi quy gan NHON
    # local linear surrogate fidelity: correlation of saliency-linearization with the logit gap
    lin = (saliency(model, Xm) * Xm).sum(1)
    fidelity = np.abs(lin) / (np.abs(lin).std() + 1e-9)
    # OOD score: distance to training mean in standardized space
    ood = np.sqrt(((Xm - Xtr.mean(0)) ** 2).sum(1))
    return np.stack([margin, concentration, fidelity, ood], 1)


def run(ds):
    Xtr, ytr, Xte, yte, feats = load(ds)
    din = Xtr.shape[1]; h = match_mlp(din, nparams(KAN(din, 16, 4)))
    models = [train(MLP(din, h), Xtr, ytr, s) for s in range(K)]
    idx = flow_bao_dong(models[0], Xte, yte, 2000)
    Xm = Xte[idx]
    rel = ground_truth_reliability(models, Xm)
    y_rel = (rel > np.median(rel)).astype(int)                   # reliable vs not (balanced split)
    S = cheap_signals(models[0], Xm, Xtr)
    # cross-validated AUC of the cheap detector predicting expensive reliability
    clf = LogisticRegression(max_iter=500)
    auc = cross_val_score(clf, S, y_rel, cv=5, scoring="roc_auc").mean()
    # utility: if analyst trusts only top-half-reliable alarms, how much more stable are they?
    clf.fit(S, y_rel); score = clf.predict_proba(S)[:, 1]
    hi = score > np.median(score)
    stab_gain = float(rel[hi].mean() - rel[~hi].mean())
    # ⛔ Bai tuyen bo "their correlation is \approx 0.82 in magnitude" giua do TAP
    # TRUNG cua quy gan (kappa) va nhan do tin cay S(x), va dung no lam CHUNG CU
    # THUC NGHIEM ngay canh Proposition. Do 11/11/2026: KHONG CSV nao chua con so ay,
    # khong script nao tinh ra no. Mot tuyen bo chiu luc ma khong co hien vat.
    # Gan lien ket don dieu nen dung Spearman. ⇒ [[feedback-tuyen-bo-khong-co-chu-so]]
    rho = spearmanr(S[:, 1], rel).correlation
    return dict(dataset=ds, detector_auc=round(float(auc), 3),
                conc_rel_rho=round(float(rho), 3),
                reliable_stability=round(float(rel[hi].mean()), 3),
                unreliable_stability=round(float(rel[~hi].mean()), 3),
                stability_gain=round(stab_gain, 3))


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = []
    for ds in DATASETS:
        r = run(ds); rows.append(r)
        print(f"{ds}: reliability-detector AUC={r['detector_auc']} | gated-reliable stability="
              f"{r['reliable_stability']} vs ungated={r['unreliable_stability']} (gain {r['stability_gain']})")
    with open("results/defense.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("wrote results/defense.csv")
