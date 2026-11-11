"""Do do nhay: bo HAN cac tap co trung lap train/test roi tinh lai hang so headline.

⛔⛔ Vi sao can. Bai khai o muc 10 rang hai trong nam tap co hang test trung TUNG
BYTE voi hang train (UNSW-NB15 45%, TON-IoT 53%, ba tap con lai toi da 1,4%), roi
do anh huong len F1 va so hai NUA cua cung mot tap. Cai con thieu: ba trong bon
hang so headline duoc dat ra boi CHINH hai tap ay.

    eps_fid  = 1 - min tree(d=4)_agree         ⇐ UNSW
    eps_det  = 1 - min o cap explainer         ⇐ UNSW
    eps_grnd = 1 - min p3_seed_agree_mean      ⇐ TON-IoT

Mot loi khai gioi han khong tra loi duoc cau hoi "neu bo chung ra thi ket luan co
con khong". Phep do nay tra loi. Bo han tap nhiem con NGHIEM NGAT hon khu trung
lap, vi khu trung lap chi cat bot trong tap, con day thi khong dung tap ay nua.
⇒ [[feedback-ghi-dau-nghi-van-ma-van-dung]] · [[feedback-do-thay-the-khong-co-doi-chung]]

⛔ Script nay KHONG huan luyen gi: no gop lai cac CSV da co. Nen no tai lap tuyet
doi va khong phu thuoc may, khac moi `exp_*` khac. Do chinh la ly do ket qua cua no
duoc dung lam doi chung: neu no can huan luyen lai thi nos lai mang them sai so
xuyen may vao dung cho ta dang muon doc mot phep tru.
⇒ [[feedback-khai-may-chay-truoc-khi-bao-so]]
"""
import csv
import os

# Nguong ty le trung lap de goi mot tap la NHIEM. Cong `cong_ro_ri.py` doc chinh
# bien nay tu day chu khong go lai, va no doi hoi khong tap nao nam sat nguong.
# Do duoc: ty le that la 0,0 / 0,0 / 0,014 / 0,447 / 0,525, nen moi nguong trong
# khoang (0,014; 0,447] cho cung mot tap nhiem.
NGUONG_RO = 0.10

HERE = os.path.dirname(os.path.abspath(__file__))
KQ = os.path.join(HERE, "results")


def hang(tep):
    with open(os.path.join(KQ, tep), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cuc_tieu(rows, lay, chi=None):
    ds = [(v, r["dataset"]) for r in rows
          if chi is None or r["dataset"] in chi for v in lay(r)]
    return min(ds)


def main():
    lk = {h["dataset"]: float(h["ty_le_trung"]) for h in hang("leakage.csv")}
    nhiem = sorted(d for d, v in lk.items() if v >= NGUONG_RO)
    sach = sorted(set(lk) - set(nhiem))
    if not nhiem:
        raise SystemExit("⛔ khong tap nao vuot nguong: phep do nay khong con "
                         "doi tuong, dung bao so 0 nhu mot ket qua")

    fm, ms, bd = hang("fidelity_multi.csv"), hang("multiseed.csv"), hang("breadth.csv")
    cap = [c for c in bd[0] if "_vs_" in c]

    DAI_LUONG = [
        ("eps_fid_clean", True, fm, lambda r: [float(r["tree(d=4)_agree"])],
         "1 - min tree(d=4)_agree"),
        ("eps_det_clean", True, bd, lambda r: [float(r[c]) for c in cap],
         "1 - min o cap explainer"),
        ("eps_grnd_clean", True, ms, lambda r: [float(r["p3_seed_agree_mean"])],
         "1 - min p3_seed_agree_mean"),
        ("p2_min_clean", False, ms, lambda r: [float(r["p2_method_agree_mean"])],
         "min p2_method_agree_mean"),
    ]
    ra = []
    for ten, bu, rows, lay, nhan in DAI_LUONG:
        ca, cl = cuc_tieu(rows, lay), cuc_tieu(rows, lay, chi=set(sach))
        va = (1 - ca[0]) if bu else ca[0]
        vc = (1 - cl[0]) if bu else cl[0]
        ra.append(dict(quantity=ten, definition=nhan,
                       value_all=round(va, 4), dataset_all=ca[1],
                       value_clean=round(vc, 4), dataset_clean=cl[1],
                       delta=round(vc - va, 4),
                       n_all=len(lk), n_clean=len(sach),
                       dropped=" ".join(nhiem), dup_threshold=NGUONG_RO))

    os.makedirs(KQ, exist_ok=True)
    with open(os.path.join(KQ, "leak_sensitivity.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(ra[0].keys()))
        w.writeheader()
        w.writerows(ra)

    print(f"  tap nhiem (ty le trung >= {NGUONG_RO}): {nhiem}")
    print(f"  tap sach con lai: {sach}")
    for r in ra:
        print(f"  {r['quantity']:16s} ca {r['n_all']} tap {r['value_all']:.3f} "
              f"({r['dataset_all']})  bo nhiem {r['value_clean']:.3f} "
              f"({r['dataset_clean']})  lech {r['delta']:+.3f}")
    print(f"  dich nhieu nhat {max(abs(r['delta']) for r in ra):.3f}")
    print("wrote results/leak_sensitivity.csv")


if __name__ == "__main__":
    main()
