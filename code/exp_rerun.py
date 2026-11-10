"""Tu-nhat-quan khi CHAY LAI cua KernelSHAP va LIME, theo ngan sach lay mau.

⛔⛔ Vi sao can, do ngay 11/11/2026. Bai viet:
    "at low sampling budgets SHAP and LIME are not even self-consistent (rerun
     agreement ~ 0.43), so part of their mutual disagreement is Monte-Carlo noise"
va dung cau ay de BIEN MINH cho viec neo tuyen bo determinacy vao cap KHAC HO thay
vi cap SHAP-vs-LIME. Nhung **khong CSV nao chua con so 0,43**, va khong script nao
tinh ra no: quet 24 CSV thi moi o bang ~0,43 deu la o khac nghia (p_cross cua
CICIDS, div_shuffle cua TON-IoT, p2_determinacy cua che do diffuse...). Mot tuyen bo
CHIU LUC ma khong co hien vat nao. ⇒ [[feedback-tuyen-bo-khong-co-chu-so]]

⛔ Co che bai NEU TEN la nhieu Monte-Carlo cua phep LAY MAU, nen phep do phai co
lap dung thu ay: NEN (background cua KernelSHAP, lay bang k-means) duoc GIU NGUYEN
moi luot, chi doi HAT cua phep lay mau. Doi ca nen thi so do tron hai nguyen nhan.
⇒ [[feedback-do-thay-the-khong-co-doi-chung]]

⛔ Va phai do o CA HAI ngan sach, khong chi ngan sach thap: bai dung ngan sach
1000/3000 xuyen suot, nen neu o ngan sach ay hai bo cung khong tu nhat quan thi ket
luan cua bai doi khac. Khong co doi chung thi "thap" khong co nghia gi.
"""
import csv
import os
import warnings

import numpy as np
import torch

warnings.filterwarnings("ignore")
import shap
from lime.lime_tabular import LimeTabularExplainer

from data import DATASETS, load
from harness import (KAN, MLP, flow_bao_dong, match_mlp, nparams, topk_features,
                     train)

TOPK = 5
NSAMP = 120              # cung co mau voi exp_breadth.py de so sanh duoc
# ⛔ Do 11/11/2026 tren Mac, hai tap, truoc khi chay that: ngan sach `thap` cho
# shap 0,432 (UNSW) va 0,376 (CICIDS), tuc dung quanh con so 0,43 bai dang in;
# nhung o ngan sach `breadth` ma bai THUC SU dung thi la 0,866 va 0,763. Neu chi
# do ngan sach thap thi toi se "xac nhan" dung con so cu va giu nguyen mot cau
# biem minh khong ap cho phep do nao cua bai. ⇒ [[feedback-tap-kiem-thien-lech]]
HAT_NEN = 0              # hat dung cho NEN, giu nguyen moi luot
HAT_LUOT = (0, 1)        # hai luot chay lai: chi hat LAY MAU doi
# (ten, so mau KernelSHAP, so mau LIME). ⛔ Bai dung HAI ngan sach khac nhau o hai
# thi nghiem khac nhau, nen do mot ngan sach la khong tra loi duoc cau cua bai:
#   exp_breadth.py          nsamples=1000, num_samples=3000
#   exp_faith_5explainer.py nsamples=300,  num_samples=800
# `thap` la doi chung SAN: khong script nao dung no. Do ca ba thi moi biet con so
# "~0,43" cua bai thuoc ngan sach nao, va no co ap cho phep do no dang bien minh
# hay khong. ⇒ [[feedback-dai-gia-tri-tron-giao-thuc]] · [[feedback-do-thay-the-khong-co-doi-chung]]
NGAN_SACH = [("thap", 100, 300), ("faith5", 300, 800), ("breadth", 1000, 3000)]


def _jac(a, b):
    return len(set(a) & set(b)) / len(set(a) | set(b))


def proba_fn(model):
    def f(X):
        with torch.no_grad():
            z = model(torch.tensor(np.asarray(X), dtype=torch.float32))
            return torch.softmax(z, 1).numpy()
    return f


def shap_topk(model, Xbg, Xm, n_mau, hat):
    f = proba_fn(model)
    np.random.seed(HAT_NEN)                      # NEN giu nguyen moi luot
    nen = shap.kmeans(Xbg, 15)
    expl = shap.KernelExplainer(f, nen)
    np.random.seed(hat)                          # chi doi hat LAY MAU
    sv = expl.shap_values(Xm, nsamples=n_mau, silent=True)
    sv = sv[1] if isinstance(sv, list) else sv[..., 1]
    return topk_features(np.asarray(sv), TOPK)


def lime_topk(model, Xtr, Xm, feats, n_mau, hat):
    f = proba_fn(model)
    ex = LimeTabularExplainer(Xtr, feature_names=[str(c) for c in feats],
                              class_names=["benign", "attack"],
                              discretize_continuous=False, mode="classification",
                              random_state=hat)
    out = np.zeros((len(Xm), TOPK), int)
    for r in range(len(Xm)):
        e = ex.explain_instance(Xm[r], f, num_features=TOPK, labels=(1,),
                                num_samples=n_mau)
        out[r] = [i for i, _ in e.local_exp[1][:TOPK]]
    return out


def dong_thuan(a, b):
    return float(np.mean([_jac(a[r], b[r]) for r in range(len(a))]))


def run(ds):
    np.random.seed(0)
    torch.manual_seed(0)
    Xtr, ytr, Xte, yte, feats = load(ds)
    din = Xtr.shape[1]
    mlp = train(MLP(din, match_mlp(din, nparams(KAN(din, 16, 4)))), Xtr, ytr, 0)
    Xm = Xte[flow_bao_dong(mlp, Xte, yte, NSAMP)]
    ra = []
    for ten, ns, nl in NGAN_SACH:
        s = [shap_topk(mlp, Xtr[:1500], Xm, ns, h) for h in HAT_LUOT]
        l = [lime_topk(mlp, Xtr[:1500], Xm, feats, nl, h) for h in HAT_LUOT]
        ra.append(dict(dataset=ds, budget=ten, shap_nsamples=ns, lime_nsamples=nl,
                       n_flows=len(Xm),
                       shap_rerun_agree=round(dong_thuan(s[0], s[1]), 3),
                       lime_rerun_agree=round(dong_thuan(l[0], l[1]), 3)))
    return ra


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = []
    for ds in DATASETS:
        for r in run(ds):
            rows.append(r)
            print(f"{ds} [{r['budget']}]: SHAP rerun={r['shap_rerun_agree']} "
                  f"LIME rerun={r['lime_rerun_agree']}")
    with open("results/rerun.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote results/rerun.csv")
