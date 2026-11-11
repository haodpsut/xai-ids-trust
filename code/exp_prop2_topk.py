"""Proposition 2 gia dinh chinh sach doc lo giai thich CHI QUA `topk`. Bo phan tich
vien cua bai doc vector LIEN TUC day du. Script nay do ca hai lop chinh sach.

⛔⛔ Vi sao can, doc ngoai vong 1 diem 2(c), 09/11/2026. Thu phan bien noi bo phan tich
vien "splits on raw magnitudes". Chu "raw" SAI: `attr()` co chuan hoa L1 tung vector,
nen chenh lech thang do tong the da bi khu. Nhan nguyen cau ay vao bai la tu viet mot
cau sai ve chinh ma cua minh. ⇒ [[feedback-point-to-point-chi-phan-bien-that]]

⛔ NHUNG phan cau truc thi DUNG, va la diem manh nhat ca thu:
  - Proposition 2 (trang 16) gia dinh chinh sach phu thuoc `e` CHI QUA `topk(e, x)`.
  - Bo phan tich vien doc `attr(m, X)`, tuc vector lien tuc DAY DU: no thay ca DAU va
    ca HINH DANG phan bo theo tung dac trung, khong chi thay TAP top-5.
  - Grep `exp_harm.py` va `exp_auditor_control.py`: KHONG co bo doc top-k indicator nao.
  ⇒ Menh de khong ap duoc vao chinh thi nghiem ma bai noi no "instantiate".

Phep do: cung quan the, cung cach huan luyen, chi doi BIEU DIEN dau vao cua bo doc.
  cont  = attr chuan hoa L1 (nhu bai dang lam)
  topk  = vector CHI BAO 0/1, 1 o dung k vi tri top-k  (lop Proposition 2 gia dinh)

`p_excess = p_cross - p_self` moi la dai luong bai duoc quyen tuyen bo: `p_self` la SAN
loi cua chinh bo doc tren mo hinh no duoc huan luyen de doc. Neu `p_excess` o `topk`
co lai gan 0 thi KET LUAN AN NINH CUA BAI PHAI VIET LAI, vi no chi song o lop chinh
sach rong hon lop menh de noi tới. ⇒ [[feedback-dieu-kien-can-dung-nhu-dieu-kien-du]]

Doi chung: `rand` thay quy gan bang nhieu, giu nguyen moi thu khac. Neu `p_excess` cua
`rand` cung lon thi so do khong noi gi ve lo giai thich. ⇒ [[feedback-null-condition-cho-so-headline]]
"""
import csv
import os

import numpy as np
import torch
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from data import DATASETS, load
from harness import (KAN, MLP, flow_bao_dong, match_mlp, nparams, predict,
                     quy_gan_chuan_hoa, saliency, topk_features, train)

# ⛔⛔ 11/11/2026, doc ngoai vong 2 diem 2(a). Ban dau script nay CHI dung
# LogisticRegression, trong khi con so headline cua bai (0,028 -> 0,539 tren CICIDS2017)
# la cua bo doc RandomForest. Doan van trong bai lai viet "The simulated analyst of
# Section 6" va "held fixed". Tuc la: doi chung cho mot tuyen bo da chay tren MOT BO DOC
# KHAC voi bo doc mang tuyen bo ay, va khong cho nao noi ra. Nay chay CA HAI.
# ⇒ [[feedback-nhan-tap-A-khong-chung-nhan-tap-B]] · [[feedback-do-thay-the-khong-co-doi-chung]]
K = 5           # so mo hinh em, trung voi exp_auditor_control.py
TOPK = 5        # cung k voi moi phep do top-k khac cua du an


# ⛔⛔ float64, khong float32. Do 11/11/2026: `saliency` tra ve float32, va sklearn
# giu nguyen dtype, nen lbfgs tinh `X @ weights` trong float32 va TRAN SO khi trong so
# lon dan. Ba script cu (`exp_harm`, `exp_auditor_control`, `exp_gate_attack`) deu co
# `warnings.filterwarnings("ignore")` nen tran so ay IM LANG o do. Toi da do: f32 va
# f64 cho p_self/p_cross GIONG NHAU tren ca nam tap, nen tran so ay vo hai va so cua
# bai van dung. Nhung mot bo chan canh bao toan phan da che mot canh bao SO HOC that,
# va lan sau no co the khong vo hai. ⇒ [[feedback-cong-cu-hong-khong-phai-ket-qua-am]]
def attr_cont(model, X):
    # Cung MOT cong thuc voi harness.quy_gan_chuan_hoa, chi khac dtype: o day can
    # float64 vi lbfgs tinh `X @ weights` trong dtype cua dau vao. `dtype=` ep TRUOC
    # khi chia, dung nhu ban goc, nen phep gom nay khong doi mot con so nao.
    return quy_gan_chuan_hoa(model, X, dtype=np.float64)


def attr_topk(model, X):
    """Vector CHI BAO 0/1 cua tap top-k. Day la TOAN BO thong tin ma mot chinh sach
    phu thuoc `e` chi qua `topk` duoc nhin thay."""
    idx = topk_features(saliency(model, X), TOPK)
    out = np.zeros(X.shape, dtype=np.float64)
    np.put_along_axis(out, idx, 1.0, axis=1)
    return out


def run(ds):
    np.random.seed(0)
    torch.manual_seed(0)
    Xtr, ytr, Xte, yte, _ = load(ds)
    din = Xtr.shape[1]
    h = match_mlp(din, nparams(KAN(din, 16, 4)))
    models = [train(MLP(din, h), Xtr, ytr, s) for s in range(K)]

    preds = np.stack([predict(m, Xte) for m in models], 1)
    tp = flow_bao_dong(None, Xte, yte, mat_na=True, du_doan=preds)
    Xtp = Xte[tp]

    ra = []
    for bo, nhan, bieu_dien in [(bo, n, b)
                                for bo in ("logistic", "rf")
                                for n, b in (("cont", attr_cont), ("topk", attr_topk))]:
        A0tr = bieu_dien(models[0], Xtr)
        Atp = [bieu_dien(m, Xtp) for m in models]
        g = (LogisticRegression(max_iter=300) if bo == "logistic" else
             RandomForestClassifier(n_estimators=80, max_depth=8, random_state=0)).fit(A0tr, ytr)
        acc = float((g.predict(bieu_dien(models[0], Xte)) == yte).mean())
        act = np.stack([g.predict(a) for a in Atp], 1)
        p_self = float((act[:, 0] == 0).mean())
        p_cross = float((act[:, 1:] == 0).mean())

        # doi chung: quy gan thay bang nhieu, giu nguyen bo doc da huan luyen
        rng = np.random.default_rng(0)
        nhieu = rng.normal(size=Xtp.shape)
        if nhan == "topk":
            i2 = topk_features(nhieu, TOPK)
            nh = np.zeros(Xtp.shape, dtype=np.float64)
            np.put_along_axis(nh, i2, 1.0, axis=1)
        else:
            nh = nhieu / (np.abs(nhieu).sum(1, keepdims=True) + 1e-9)
        p_rand = float((g.predict(nh) == 0).mean())

        ra.append(dict(dataset=ds, auditor=bo, reader=nhan, n_flows=int(tp.sum()),
                       auditor_acc=round(acc, 3),
                       p_self=round(p_self, 3), p_cross=round(p_cross, 3),
                       p_excess=round(p_cross - p_self, 3),
                       p_rand_attr=round(p_rand, 3)))
    return ra


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = []
    for ds in DATASETS:
        for r in run(ds):
            rows.append(r)
            print(f"{r['dataset']:14s} [{r['auditor']:8s}/{r['reader']:4s}] acc={r['auditor_acc']:.3f} | "
                  f"p_self={r['p_self']:.3f} p_cross={r['p_cross']:.3f} "
                  f"(excess {r['p_excess']:+.3f}) | p_rand={r['p_rand_attr']:.3f}")
    with open("results/prop2_topk.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote results/prop2_topk.csv")
