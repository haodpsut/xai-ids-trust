"""Ro ri TRUNG LAP qua ranh gioi chia train/test, va no co pha ket luan khong.

⛔⛔ Vi sao can, do ngay 11/11/2026. Doc ngoai vong 1 (muc 2h) neu: `data.py` chia
`train_test_split(..., stratify=y)`, tuc NGAU NHIEN, tren tap co trung lap flow nang
=> dung cai bay Arp va cs. (2022) ma CHINH BAI trich o trang 4. Thu doan tap CICIDS2017.
Do that thi thu DOAN SAI TAP, va so nang hon:

    tap           ty le hang test co BAN SAO Y NGUYEN trong train   trong do la tan cong
    UNSW          44,7%                                             5031/5367 = 94%
    TON-IoT       52,5%                                             4902/6301 = 78%
    CICIDS         0,0%
    5G-NIDD        0,0%
    CIC-IoT-2023   1,4%                                             168/168 = 100%

Ro ri DON VAO LOP TAN CONG, dung lop ma F1 phat hien va ca phan tich tac hai dua vao.
⇒ [[feedback-tap-du-lieu-cat-theo-tep-khong-theo-mau]] · [[feedback-tap-kiem-thien-lech]]

⛔ Cau hoi cua script nay KHONG phai "co ro ri khong" (da biet la co) ma la **ro ri co
pha KET LUAN khong**. Bai ket luan ve TINH CHAT CUA LOI GIAI THICH, khong ve do chinh
xac phat hien. Nen phep do quyet dinh la: tach tap kiem thanh hai nua, nua CO ban sao
trong train va nua KHONG, roi do P2 va P3 tren tung nua.

  - Hai nua cho muc bat dong NHU NHAU  => ket luan khong phu thuoc ro ri, chi phai KHAI.
  - Hai nua KHAC nhau                   => phai loc trung truoc khi chia va chay lai het.

F1 tren tung nua in ra de thay HIEU UNG GHI NHO truc tiep: neu nua co ban sao cho F1
cao hon ro ret thi do la ghi nho, khong phai tong quat hoa.
⇒ [[feedback-do-thay-the-khong-co-doi-chung]]
"""
import csv
import os

import numpy as np
import torch

from data import DATASETS, load
from exp_trust import p2_determinacy, p3_groundedness
from harness import KAN, MLP, match_mlp, nparams, predict, train

TOI_THIEU = 200          # mot nua duoi nguong nay thi P2/P3 tren no khong doc duoc


def mat_na_trung(Xtr, Xte):
    """Mat na cac hang Xte co BAN SAO Y NGUYEN (tung byte) trong Xtr.

    ⛔ So tung byte o do chinh xac DAY DU, khong lam tron. Do 11/11/2026: lam tron
    6 chu so day TON-IoT tu 52,5% len 76,0%, tuc phep lam tron TU TAO ra trung lap.
    ⇒ [[feedback-chuan-hoa-lam-mat-phan-biet-hai-tu]]
    """
    tr = set(map(bytes, np.ascontiguousarray(Xtr)))
    return np.array([bytes(r) in tr for r in np.ascontiguousarray(Xte)], dtype=bool)


def f1(y, p):
    tp = int(((p == 1) & (y == 1)).sum())
    fp = int(((p == 1) & (y == 0)).sum())
    fn = int(((p == 0) & (y == 1)).sum())
    return 0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn)


def run(ds):
    np.random.seed(0)
    torch.manual_seed(0)
    Xtr, ytr, Xte, yte, _ = load(ds)
    din = Xtr.shape[1]
    mlp = train(MLP(din, match_mlp(din, nparams(KAN(din, 16, 4)))), Xtr, ytr, 0)
    du = predict(mlp, Xte)

    m = mat_na_trung(Xtr, Xte)
    ra = dict(dataset=ds, n_test=int(len(Xte)),
              n_trung=int(m.sum()), ty_le_trung=round(float(m.mean()), 4),
              n_trung_tan_cong=int((yte[m] == 1).sum()),
              f1_all=round(f1(yte, du), 4))

    for nhan, sel in (("trung", m), ("sach", ~m)):
        n = int(sel.sum())
        ra[f"n_{nhan}"] = n
        if n < TOI_THIEU:
            # ⛔ Khong bia so cho nua qua nho: in NaN de nguoi doc thay la KHONG DO DUOC.
            for k in ("f1", "p2", "p3"):
                ra[f"{k}_{nhan}"] = ""
            continue
        ra[f"f1_{nhan}"] = round(f1(yte[sel], du[sel]), 4)
        r2 = p2_determinacy(mlp, Xte[sel], yte[sel])
        ra[f"p2_{nhan}"] = round(float(r2["mean_agree"]), 4)
        r3 = p3_groundedness(Xtr, ytr, Xte[sel], yte[sel])
        ra[f"p3_{nhan}"] = round(float(r3["topk_jaccard"]), 4)
    return ra


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = [run(ds) for ds in DATASETS]
    cot = ["dataset", "n_test", "n_trung", "ty_le_trung", "n_trung_tan_cong",
           "f1_all", "n_trung", "f1_trung", "p2_trung", "p3_trung",
           "n_sach", "f1_sach", "p2_sach", "p3_sach"]
    cot = list(dict.fromkeys(cot))
    with open("results/leakage.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cot, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f"{r['dataset']:14s} trung={r['ty_le_trung']:.1%} "
              f"F1 trung={r.get('f1_trung','--')} vs sach={r.get('f1_sach','--')} | "
              f"P2 {r.get('p2_trung','--')} vs {r.get('p2_sach','--')} | "
              f"P3 {r.get('p3_trung','--')} vs {r.get('p3_sach','--')}")
    print("wrote results/leakage.csv")
