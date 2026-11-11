"""Ba doi chung cho tap DUY NHAT con mang ket luan an ninh (CICIDS2017).

⛔⛔ Doc ngoai vong 3, diem 2(d) va cau hoi 3. Sau khi bo doc GOP thu hep harm ve mot
tap, cai con lai phai chiu mot gia thuyet thay the ma bai chua loai:

  (a) CAN BANG LOP. CICIDS2017 la tap thua attack it nhat trong nam. Mot bo doc hoc
      tren nhan lech se dat nguong khac di, va cach no dap tren dau vao LA cung khac.
      Hieu ung con lai co the bam theo CAN BANG LOP chu khong theo bat on giai thich.
  (b) BIEN QUYET DINH. CICIDS2017 cung la tap co detection_agreement thap nhat
      (0,888). Quan the canh bao da han che o luong MOI sibling deu bao, nhung bien
      quyet dinh giua cac sibling van co the lech co he thong.

Neu excess bien mat khi can bang lai lop, hoac chi song o mot tang bien, thi no khong
phai bang chung ve giai thich. ⇒ [[feedback-do-thay-the-khong-co-doi-chung]]

Doi chung thu ba tra loi muc 5 cua cung vong doc: \\citet{laberge2023partial} de xuat
chi bao cao nhung quan he quy gan ma MOI mo hinh trong tap Rashomon dong y. Voi nam
sibling thi tap dong thuan top-k tinh duoc truc tiep, va bai dang noi "trust is not
cheaply recovered" ma chua thu cai re nhat. ⇒ [[feedback-do-thay-the-khong-co-doi-chung]]
"""
import csv
import os
import warnings

import numpy as np
import torch

warnings.filterwarnings("ignore")
from sklearn.ensemble import RandomForestClassifier

from data import DATASETS, load
from harness import (KAN, MLP, flow_bao_dong, match_mlp, nparams, predict,
                     quy_gan_chuan_hoa, topk_features, train)

K = 5
TOPK = 5
attr = quy_gan_chuan_hoa


def bien_quyet_dinh(models, X):
    """Do lech |p_attack - 0.5| cua tung mo hinh, tra ve [n, K]."""
    ra = []
    for m in models:
        with torch.no_grad():
            p = torch.softmax(m(torch.tensor(X, dtype=torch.float32)), 1)[:, 1].numpy()
        ra.append(np.abs(p - 0.5))
    return np.stack(ra, 1)


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
    A0tr = attr(models[0], Xtr)
    Atp = [attr(m, Xtp) for m in models]

    ra = []
    # (a) bo doc THUONG vs bo doc CAN BANG LOP, cung moi thu khac.
    for nhan, trong in (("plain", None), ("balanced", "balanced")):
        g = RandomForestClassifier(n_estimators=80, max_depth=8, random_state=0,
                                   class_weight=trong).fit(A0tr, ytr)
        act = np.stack([g.predict(a) for a in Atp], 1)
        p_self = float((act[:, 0] == 0).mean())
        p_cross = float((act[:, 1:] == 0).mean())
        ra.append(dict(dataset=ds, control=f"reader_{nhan}", stratum="all",
                       n_flows=int(tp.sum()), p_self=round(p_self, 3),
                       p_cross=round(p_cross, 3),
                       p_excess=round(p_cross - p_self, 3), extra=""))

    # (a2) GO CA HAI gia thuyet thay the cung luc: gop sibling VA can bang lop.
    # ⛔ Neu chi go tung cai mot thi moi lan van con cai kia giai thich ho. Con so
    # bai nen dem ra lam headline la o nay. ⇒ [[feedback-ablation-chi-ke-mot-huong-loi]]
    for nhan, trong in (("plain", None), ("balanced", "balanced")):
        ps, pc = [], []
        for giu in range(K):
            con = [j for j in range(K) if j != giu]
            Xg = np.concatenate([attr(models[j], Xtr) for j in con], 0)
            yg = np.tile(ytr, len(con))
            gp = RandomForestClassifier(n_estimators=80, max_depth=8, random_state=0,
                                        class_weight=trong).fit(Xg, yg)
            ps.append(float(np.mean([(gp.predict(Atp[j]) == 0).mean() for j in con])))
            pc.append(float((gp.predict(Atp[giu]) == 0).mean()))
        ra.append(dict(dataset=ds, control=f"pooled_{nhan}", stratum="all",
                       n_flows=int(tp.sum()), p_self=round(float(np.mean(ps)), 3),
                       p_cross=round(float(np.mean(pc)), 3),
                       p_excess=round(float(np.mean(pc)) - float(np.mean(ps)), 3),
                       extra=f"folds={K}"))

    # (b) phan tang theo muc DONG THUAN cua bien quyet dinh giua cac sibling.
    g = RandomForestClassifier(n_estimators=80, max_depth=8, random_state=0).fit(A0tr, ytr)
    act = np.stack([g.predict(a) for a in Atp], 1)
    bien = bien_quyet_dinh(models, Xtp)
    rong = bien.max(1) - bien.min(1)              # do TAN cua bien giua 5 sibling
    nguong = float(np.median(rong))
    for nhan, mat in (("margin_tight", rong <= nguong), ("margin_wide", rong > nguong)):
        if mat.sum() < 30:
            continue
        a = act[mat]
        ps = float((a[:, 0] == 0).mean())
        pc = float((a[:, 1:] == 0).mean())
        ra.append(dict(dataset=ds, control="reader_plain", stratum=nhan,
                       n_flows=int(mat.sum()), p_self=round(ps, 3),
                       p_cross=round(pc, 3), p_excess=round(pc - ps, 3),
                       extra=f"margin_spread_median={nguong:.4f}"))

    # (c) duong co so kieu Laberge: tap top-k MOI sibling deu dong y.
    tk = [set(map(tuple, topk_features(a, TOPK))) for a in Atp]
    giao = []
    for r in range(len(Xtp)):
        s = set(topk_features(Atp[0], TOPK)[r])
        for j in range(1, K):
            s &= set(topk_features(Atp[j], TOPK)[r])
        giao.append(len(s))
    giao = np.array(giao)
    ra.append(dict(dataset=ds, control="consensus_topk", stratum="all",
                   n_flows=int(tp.sum()), p_self="", p_cross="", p_excess="",
                   extra=f"mean_size={giao.mean():.2f};frac_nonempty={(giao > 0).mean():.3f};"
                         f"frac_full={(giao == TOPK).mean():.3f}"))
    return ra


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = []
    for ds in DATASETS:
        for r in run(ds):
            rows.append(r)
            print(f"{ds:14s} {r['control']:16s} {r['stratum']:12s} "
                  f"n={r['n_flows']:6d} excess={r['p_excess']} {r['extra']}", flush=True)
    with open("results/reader_controls.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote results/reader_controls.csv")
