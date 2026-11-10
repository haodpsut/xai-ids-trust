"""
New measurement axis: FAITHFULNESS (not agreement). An explanation is faithful if the features it
names are the ones the model actually uses. We measure the two standard faithfulness metrics
(ERASER; DeYoung et al. 2020) for each explainer on each dataset, on flagged-attack flows:

  COMPREHENSIVENESS: drop the top-k attributed features (mean-impute) -> how much does the
    attack-probability fall? A faithful explanation names features whose removal hurts a lot.
  SUFFICIENCY: keep only the top-k features -> how much attack-probability remains? A faithful
    explanation's top-k should suffice; low sufficiency means the reason is not enough.

We report comprehensiveness (higher = more faithful) and sufficiency-gap = p_full - p_topk
(lower = more faithful). This adds a faithfulness axis to the agreement-based P1-P3, and answers
our own caveat that stability is not faithfulness.
"""
import numpy as np, torch, csv, os, warnings
warnings.filterwarnings("ignore")
from harness import MLP, KAN, nparams, match_mlp, train, predict, saliency, topk_features, flow_bao_dong
from data import load, DATASETS

TOPK = 5


def prob_attack(model, X):
    with torch.no_grad():
        return torch.softmax(model(torch.tensor(X, dtype=torch.float32)), 1)[:, 1].numpy()


# ⛔⛔ Vi sao do NHIEU SEED thay vi mot luot, do duoc 10/11/2026: chay lai tren may
# thu hai (x86) so voi may sinh ra so cua bai (Apple Silicon), CUNG ma, CUNG du lieu
# da kiem bam, thi `faithfulness.csv` lech toi **0,062** va **8/15 o DOI khi lam tron
# 2 chu so**. Nang nhat: comprehensiveness TON-IoT 0,044 -> 0,106, in `0.04` thanh
# `0.11`. Da tach nguyen nhan: cung may thi TIEN DINH tung byte, va GHIM luong ve 1
# KHONG lam thay doi gi ca, nen do la khac biet kien truc/BLAS, khong phai so luong.
#
# ⭐ Co che: sai so 1e-3 di qua cac lua chon ROI RAC roi phong dai. Mo hinh lech chut
# -> `flow_bao_dong` chon TAP FLOW khac -> top-5 dac trung DOI THU TU khi hai
# attribution gan bang nhau -> comprehensiveness (do bang cach BO top-5) nhay 0,06.
# ⇒ Mot so di qua phep chon roi rac thi KHONG duoc bao dang DIEM. Nay bao mean±std
# tren SEEDS, de con so mang theo do rong cua chinh no.
SEEDS = range(4)          # ⛔ KHONG trung voi exp_multiseed.py: vong NGOAI cua no la
                          # SEEDS=[0,1,2] (3 seed). Chi `p3_groundedness` dung range(4).
                          # Nen bang nay tinh tren 4 seed ngoai, tab:main P1/P2 tren 3.
                          # Do 11/11/2026; chu thich cu khai sai la 'cung 4 seed'.


def mot_seed(ds, seed):
    np.random.seed(seed); torch.manual_seed(seed)
    Xtr, ytr, Xte, yte, feats = load(ds); din = Xtr.shape[1]
    f = train(MLP(din, match_mlp(din, nparams(KAN(din, 16, 4)))), Xtr, ytr, seed)
    idx = flow_bao_dong(f, Xte, yte, 1500)
    Xm = Xte[idx]; base = Xtr.mean(0)
    p_full = prob_attack(f, Xm)
    tk = topk_features(saliency(f, Xm), TOPK)
    # comprehensiveness: remove top-k
    Xrm = Xm.copy()
    for r in range(len(Xm)):
        Xrm[r, tk[r]] = base[tk[r]]
    comp = float((p_full - prob_attack(f, Xrm)).mean())
    # sufficiency: keep only top-k
    Xkeep = np.tile(base, (len(Xm), 1)).astype(np.float32)
    for r in range(len(Xm)):
        Xkeep[r, tk[r]] = Xm[r, tk[r]]
    suff_gap = float((p_full - prob_attack(f, Xkeep)).mean())
    return dict(deployed_attack_prob=float(p_full.mean()),
                comprehensiveness=comp, sufficiency_gap=suff_gap)


def run(ds):
    rs = [mot_seed(ds, s) for s in SEEDS]
    out = dict(dataset=ds, n_seeds=len(rs))
    for k in ("deployed_attack_prob", "comprehensiveness", "sufficiency_gap"):
        v = np.array([r[k] for r in rs], dtype=float)
        out[k] = round(float(v.mean()), 3)
        out[k + "_std"] = round(float(v.std()), 3)
    return out


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = [run(ds) for ds in DATASETS]
    with open("results/faithfulness.csv", "w", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    for r in rows:
        print(f"{r['dataset']}: comprehensiveness={r['comprehensiveness']}"
              f"±{r['comprehensiveness_std']} "
              f"sufficiency-gap={r['sufficiency_gap']}±{r['sufficiency_gap_std']} "
              f"(p_full={r['deployed_attack_prob']}, {r['n_seeds']} seeds)")
    print("wrote results/faithfulness.csv")
