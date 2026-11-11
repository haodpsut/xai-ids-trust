"""Doi EXPLAINER, giu nguyen MO HINH: bat dong determinacy co doi HANH DONG khong?

⛔⛔ Vi sao can, doc ngoai vong 3 diem 1 va cau hoi 2. Bai moi them mot doan thua nhan
(theo \\citet{han2022which}) rang cac explainer bat dong nhau la chuyen DU DOAN DUOC,
roi dat y nghia cua minh vao cau: "our contribution is not that it exists but that it
is large enough, on deployed NIDS, to change an action".

Cau ay tao mot nghia vu ma bai CHUA tra: thi nghiem hanh dong duy nhat (muc harm) doi
HAT GIONG, khong doi EXPLAINER. Tuc determinacy duoc gan y nghia bang lap luan chu
khong bang phep do. ⇒ [[feedback-dieu-kien-can-dung-nhu-dieu-kien-du]]

Phep do o day giu MOI thu co dinh tru mot: bo phan tich vien duoc hieu chinh tren quy
gan cua explainer A, roi duoc cho xem quy gan cua explainer B tren CUNG MOT mo hinh va
CUNG mot quan the luong. `p_self` la duong cheo (A doc A), `p_cross` la o ngoai cheo.

  p_excess = p_cross - p_self  > 0 ⇒ doi explainer LAM DOI hanh dong, va cau tren dung
                               ~ 0 ⇒ cau tren PHAI RUT: bat dong co that nhung khong
                                     den duoc muc hanh dong.

⛔ Ngan sach lay mau khai ngay o day va bai phai in ra: KernelSHAP va LIME dat, nen
quan the nho hon muc harm. Mot con so khong kem ngan sach thi khong so duoc voi con so
khac. ⇒ [[feedback-khai-may-chay-truoc-khi-bao-so]]
"""
import csv
import os
import warnings

import numpy as np
import torch

warnings.filterwarnings("ignore")
import shap
from lime.lime_tabular import LimeTabularExplainer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from data import DATASETS, load
from harness import (KAN, MLP, flow_bao_dong, input_x_gradient,
                     integrated_gradients, match_mlp, nparams, predict,
                     quy_gan_chuan_hoa, saliency, train)

N_ALARM = 600        # luong canh bao duoc giai thich boi CA NAM explainer
N_FIT = 3000         # hang tap huan luyen dung de hieu chinh bo doc
SHAP_NS = 300        # cung ngan sach voi exp_faith_5explainer.py
LIME_NS = 800
HIEU_CHINH = ("grad", "ig", "shap")     # ba ho duoc dung lam goc hieu chinh


def _chuan(a):
    """Chuan hoa L1 tung mau, dung phep nhu harness.quy_gan_chuan_hoa."""
    a = np.asarray(a, dtype=np.float64)
    return a / (np.abs(a).sum(1, keepdims=True) + 1e-9)


def _proba(model):
    def f(X):
        with torch.no_grad():
            z = model(torch.tensor(np.asarray(X), dtype=torch.float32))
            return torch.softmax(z, 1).numpy()
    return f


def quy_gan(ten, model, X, Xbg, feats):
    """Ma tran quy gan DA CHUAN HOA cua mot explainer tren X."""
    if ten == "grad":
        return _chuan(saliency(model, X))
    if ten == "ixg":
        return _chuan(input_x_gradient(model, X))
    if ten == "ig":
        return _chuan(integrated_gradients(model, X))
    if ten == "shap":
        sv = shap.KernelExplainer(_proba(model), shap.kmeans(Xbg, 15)).shap_values(
            X, nsamples=SHAP_NS, silent=True)
        sv = sv[1] if isinstance(sv, list) else sv[..., 1]
        return _chuan(np.asarray(sv))
    if ten == "lime":
        ex = LimeTabularExplainer(Xbg, feature_names=[str(c) for c in feats],
                                  class_names=["benign", "attack"],
                                  discretize_continuous=False, mode="classification",
                                  random_state=0)
        out = np.zeros(X.shape)
        for r in range(len(X)):
            e = ex.explain_instance(X[r], _proba(model), num_features=X.shape[1],
                                    labels=(1,), num_samples=LIME_NS)
            for j, w in e.local_exp[1]:
                out[r, j] = w
        return _chuan(out)
    raise ValueError(ten)


def run(ds):
    np.random.seed(0)
    torch.manual_seed(0)
    Xtr, ytr, Xte, yte, feats = load(ds)
    din = Xtr.shape[1]
    mlp = train(MLP(din, match_mlp(din, nparams(KAN(din, 16, 4)))), Xtr, ytr, 0)

    # ⛔ MOT mo hinh duy nhat tu dau den cuoi: bien duy nhat duoc phep doi la explainer.
    Xfit, yfit = Xtr[:N_FIT], ytr[:N_FIT]
    idx = flow_bao_dong(mlp, Xte, yte, N_ALARM)
    Xal = Xte[idx]
    bg = Xtr[:1500]

    ten_expl = ("grad", "ixg", "ig", "shap", "lime")
    A_fit = {t: quy_gan(t, mlp, Xfit, bg, feats) for t in HIEU_CHINH}
    A_al = {t: quy_gan(t, mlp, Xal, bg, feats) for t in ten_expl}
    # ⛔ Nang luc cua bo doc phai duoc bao CANH excess. Mot bo doc GOP nhieu ho co
    # the kem han tren chinh ho no biet, va luc ay excess khong con doc duoc.
    # ⇒ [[feedback-cong-cu-hong-khong-phai-ket-qua-am]]
    n_acc = min(2000, len(Xte))
    A_te = {t: quy_gan(t, mlp, Xte[:n_acc], bg, feats) for t in HIEU_CHINH}
    yte_acc = yte[:n_acc]
    print(f"    {ds}: {len(Xal)} luong canh bao, {len(Xfit)} hang hieu chinh", flush=True)

    ra = []
    # ⛔⛔ Doi chung BAT BUOC, cung lap luan da thu hep ket qua sibling: mot bo doc
    # hieu chinh tren MOT explainer co the dap moi quy gan co HINH DANG la, va the
    # thi `p_cross` do che do huan luyen chu khong do bat dong giai thich. Nen ta
    # cung do mot bo doc hieu chinh tren quy gan GOP cua ba ho, roi thu tren hai ho
    # BI GIU LAI han (ixg va lime). Neu excess van lon o do thi ket luan dung;
    # neu no sup thi phai rut. ⇒ [[feedback-do-thay-the-khong-co-doi-chung]]
    giu_lai = [t for t in ("ixg", "lime") if t not in HIEU_CHINH]
    Xg = np.concatenate([A_fit[t] for t in HIEU_CHINH], 0)
    yg = np.tile(yfit, len(HIEU_CHINH))
    for bo in ("logistic", "rf"):
        gp = (LogisticRegression(max_iter=300) if bo == "logistic" else
              RandomForestClassifier(n_estimators=80, max_depth=8,
                                     random_state=0)).fit(Xg, yg)
        dap = {t: float((gp.predict(A_al[t]) == 0).mean()) for t in ten_expl}
        acc = float(np.mean([(gp.predict(A_te[t]) == yte_acc).mean() for t in HIEU_CHINH]))
        p_self = float(np.mean([dap[t] for t in HIEU_CHINH]))
        p_cross = float(np.mean([dap[t] for t in giu_lai]))
        ra.append(dict(dataset=ds, auditor=bo, calibrated_on="pooled3",
                       auditor_acc=round(acc, 3),
                       n_alarm=len(Xal), n_fit=len(Xfit) * len(HIEU_CHINH),
                       p_self=round(p_self, 3),
                       p_cross_mean=round(p_cross, 3),
                       p_cross_max=round(max(dap[t] for t in giu_lai), 3),
                       p_excess_mean=round(p_cross - p_self, 3),
                       p_excess_max=round(max(dap[t] for t in giu_lai) - p_self, 3),
                       **{f"shown_{t}": round(dap[t], 3) for t in ten_expl}))
    for bo in ("logistic", "rf"):
        for goc in HIEU_CHINH:
            g = (LogisticRegression(max_iter=300) if bo == "logistic" else
                 RandomForestClassifier(n_estimators=80, max_depth=8,
                                        random_state=0)).fit(A_fit[goc], yfit)
            dap = {t: float((g.predict(A_al[t]) == 0).mean()) for t in ten_expl}
            acc = float((g.predict(A_te[goc]) == yte_acc).mean())
            p_self = dap[goc]
            khac = [t for t in ten_expl if t != goc]
            ra.append(dict(dataset=ds, auditor=bo, calibrated_on=goc,
                           auditor_acc=round(acc, 3),
                           n_alarm=len(Xal), n_fit=len(Xfit),
                           p_self=round(p_self, 3),
                           p_cross_mean=round(float(np.mean([dap[t] for t in khac])), 3),
                           p_cross_max=round(max(dap[t] for t in khac), 3),
                           p_excess_mean=round(float(np.mean([dap[t] for t in khac])) - p_self, 3),
                           p_excess_max=round(max(dap[t] for t in khac) - p_self, 3),
                           **{f"shown_{t}": round(dap[t], 3) for t in ten_expl}))
    return ra


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = []
    for ds in DATASETS:
        for r in run(ds):
            rows.append(r)
            print(f"{ds:14s} [{r['auditor']:8s}] hieu chinh tren {r['calibrated_on']:5s}: "
                  f"p_self={r['p_self']:.3f} p_cross(tb)={r['p_cross_mean']:.3f} "
                  f"excess={r['p_excess_mean']:+.3f} (max {r['p_excess_max']:+.3f})",
                  flush=True)
    with open("results/explainer_swap.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote results/explainer_swap.csv")
