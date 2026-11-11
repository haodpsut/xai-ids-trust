"""Doi chung QUYET DINH: bo doc huan luyen tren quy gan GOP tu nhieu sibling.

⛔⛔ Vi sao can, doc ngoai vong 2, diem 2(b). Phan bien dat dung mot cau hoi ma bai
chua tra loi duoc: toan bo "harm" cua bai do bang MOT bo doc hieu chinh tren MOT mo
hinh roi dem doc giai thich cua bon mo hinh anh em. Neu bo doc ay gap bat cu dau vao
LA nao cung dap, thi `p_cross > p_self` khong noi gi ve lo giai thich, no noi ve CHE DO
HUAN LUYEN cua bo doc.

Bang chung bai TU DUA RA lai ung ho cach doc ay: `exp_prop2_topk.py` do duoc bo doc dap
toi 0,98 luong khi dua cho no quy gan NHIEU. Mot bo doc dap moi thu la cho no chua tung
thay thi khong con la nhan chung cho tinh chat cua loi giai thich.
⇒ [[feedback-do-thay-the-khong-co-doi-chung]] · [[feedback-dieu-kien-can-dung-nhu-dieu-kien-du]]

Phep do. Giu NGUYEN quan the (`flow_bao_dong`), NGUYEN bo sibling, NGUYEN cach huan
luyen; chi doi mot thu: tap quy gan dung de hieu chinh bo doc.
  single  bo doc fit tren quy gan cua mo hinh 0        (dung nhu bai dang lam)
  pooled  bo doc fit tren quy gan GOP cua 4 sibling, do tren sibling THU 5 bi giu lai,
          lam du ca 5 luot giu-mot-ra, roi lay trung binh

`p_excess = p_cross - p_self` o che do `pooled`:
  - neu VAN lon  ⇒ harm khong phai hieu ung cua viec hieu chinh tren mot mo hinh,
                   ket luan an ninh cua bai dung vung hon truoc;
  - neu VE GAN 0 ⇒ harm la hien vat cua hieu chinh mot mo hinh, va KET LUAN AN NINH
                   CUA BAI PHAI VIET LAI. Script nay duoc viet de co the tra loi ve 0.

⛔ Nhanh `single` o day phai TAI LAP DUNG `auditor_control.csv`. Khong phai de cho dep:
hai duong ong cung mo ta mot thi nghiem ma lech nhau thi mot trong hai da troi, va
cach duy nhat biet duoc la BAT chung so voi nhau. Script TU NEM neu lech.
⇒ [[feedback-hai-duong-ong-so-phu-noi-vao-mot]] · [[feedback-cong-khong-so-hai-nguon]]
"""
import csv
import os
import warnings

import numpy as np
import torch

warnings.filterwarnings("ignore")
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from data import DATASETS, load
from harness import (KAN, MLP, flow_bao_dong, match_mlp, nparams, predict,
                     quy_gan_chuan_hoa, train)

K = 5
# Sai so cho phep khi doi chieu nhanh `single` voi auditor_control.csv. Hai ben in ra
# 3 chu so thap phan, nen 0.0005 la DO LAM TRON, khong phai mot nguong duoc noi long.
LAM_TRON = 0.0005

attr = quy_gan_chuan_hoa


def bo_doc(ten, X, y):
    if ten == "logistic":
        return LogisticRegression(max_iter=300).fit(X, y)
    return RandomForestClassifier(n_estimators=80, max_depth=8, random_state=0).fit(X, y)


def ty_le_dap(g, A):
    """Ty le luong bo doc doc thanh BENIGN (dap canh bao) tren mot ma tran quy gan."""
    return float((g.predict(A) == 0).mean())


def doc_doi_chieu():
    """auditor_control.csv neu co, de nhanh `single` tu doi chieu."""
    p = os.path.join("results", "auditor_control.csv")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return {(r["dataset"], r["auditor"]): r for r in csv.DictReader(f)}


def run(ds, rng, doi_chieu):
    np.random.seed(0)
    torch.manual_seed(0)
    Xtr, ytr, Xte, yte, feats = load(ds)
    din = Xtr.shape[1]
    h = match_mlp(din, nparams(KAN(din, 16, 4)))
    models = [train(MLP(din, h), Xtr, ytr, s) for s in range(K)]

    preds = np.stack([predict(m, Xte) for m in models], 1)
    tp = flow_bao_dong(None, Xte, yte, mat_na=True, du_doan=preds)
    Xtp = Xte[tp]

    Atr = [attr(m, Xtr) for m in models]
    Atp = [attr(m, Xtp) for m in models]
    A0te = attr(models[0], Xte)

    out, lech = [], []
    for ten in ("logistic", "rf"):
        # --- single: dung nhu bai dang lam, mot mo hinh hieu chinh ---
        g = bo_doc(ten, Atr[0], ytr)
        acc = float((g.predict(A0te) == yte).mean())
        p_self = ty_le_dap(g, Atp[0])
        p_cross = float(np.mean([ty_le_dap(g, Atp[j]) for j in range(1, K)]))
        out.append(dict(dataset=ds, reader=ten, mode="single", n_folds=1,
                        n_flows=int(tp.sum()), auditor_acc=round(acc, 3),
                        p_self=round(p_self, 3), p_cross=round(p_cross, 3),
                        p_excess=round(p_cross - p_self, 3), p_rand=""))

        # ⛔ Doi chieu NGAY voi duong ong kia, truoc khi di tiep.
        if doi_chieu and (ds, ten) in doi_chieu:
            r = doi_chieu[(ds, ten)]
            for ten_o, ta in (("p_self", p_self), ("p_cross", p_cross)):
                ho = float(r[ten_o])
                if abs(ho - round(ta, 3)) > LAM_TRON:
                    lech.append(f"{ds}/{ten}/{ten_o}: pooled_reader {ta:.3f} "
                                f"vs auditor_control {ho:.3f}")

        # --- pooled: giu-mot-sibling-ra, lam du 5 luot ---
        ps, pc, pr, accs = [], [], [], []
        for giu in range(K):
            con = [j for j in range(K) if j != giu]
            Xg = np.concatenate([Atr[j] for j in con], 0)
            yg = np.tile(ytr, len(con))
            gp = bo_doc(ten, Xg, yg)
            accs.append(float((gp.predict(A0te) == yte).mean()))
            ps.append(float(np.mean([ty_le_dap(gp, Atp[j]) for j in con])))
            pc.append(ty_le_dap(gp, Atp[giu]))
            # Doi chung nhieu: giu nguyen bien theo tung dac trung, pha lien ket
            # luong--giai thich, dung phep nhu exp_auditor_control.
            gia = np.stack([rng.permutation(Atp[giu][:, c])
                            for c in range(Atp[giu].shape[1])], 1)
            pr.append(ty_le_dap(gp, gia))
        out.append(dict(dataset=ds, reader=ten, mode="pooled", n_folds=K,
                        n_flows=int(tp.sum()), auditor_acc=round(float(np.mean(accs)), 3),
                        p_self=round(float(np.mean(ps)), 3),
                        p_cross=round(float(np.mean(pc)), 3),
                        p_excess=round(float(np.mean(pc)) - float(np.mean(ps)), 3),
                        p_rand=round(float(np.mean(pr)), 3)))
    return out, lech


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rng = np.random.default_rng(0)
    doi_chieu = doc_doi_chieu()
    if doi_chieu is None:
        print("⚠ khong co auditor_control.csv: nhanh `single` se KHONG duoc doi chieu")
    rows, lech = [], []
    for ds in DATASETS:
        r, l = run(ds, rng, doi_chieu)
        rows += r
        lech += l
        for x in r:
            print(f"{ds:14s} [{x['reader']:8s}/{x['mode']:6s}] "
                  f"p_self={x['p_self']:.3f} p_cross={x['p_cross']:.3f} "
                  f"p_excess={x['p_excess']:+.3f} p_rand={x['p_rand']}")
    with open("results/pooled_reader.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("\nwrote results/pooled_reader.csv")
    if lech:
        raise SystemExit("⛔ nhanh `single` KHONG tai lap auditor_control.csv:\n  "
                         + "\n  ".join(lech))
    if doi_chieu:
        print("  nhanh `single` tai lap dung auditor_control.csv tren ca "
              f"{len(DATASETS)} tap, hai bo doc")
