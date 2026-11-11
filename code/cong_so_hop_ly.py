"""Hoi nguoc MOI so trong 24 CSV: no co nam trong khoang mot nguoi doc bai cho phep?

⛔⛔ Vi sao co tep nay. Ngay 10/11/2026 `n_true_attacks` ra **47012435** trong khi
tap kiem chi co 12000 dong; do la tong CAC CHI SO vi mot mat na bien thanh mang chi
so. Muoi mot cong cua kho deu XANH tren con so ay: cong_quan_the chi doc CU PHAP,
cong_bang_tu_csv chi doi chieu bai voi CSV (bai se in dung con so vo ly ay), con
cong_dong_bo chi doi chieu ba noi (ba noi cung sai thi van khop). Khong cong nao
HOI con so co nghia hay khong. Mot so dap vao mat ma khong cong nao thay duoc thi
ca bo cong dang do NHAT QUAN, khong do DUNG.
⇒ [[feedback-cong-hoi-nguoc-moi-so-in-ra]] · [[feedback-cong-khong-thay-duoc-thu-dap-vao-mat]]

Luat kiem, tat ca lay tu CHINH du lieu chu khong go tay:
  H1. Cot dang DEM (`n_*`, `num_*`, `count*`) phai la so nguyen >= 0 va <= tran cua
      no. Tran lay tu `dataset_profile.csv`: so dong dung, hoac so dac trung.
  H2. Cot dang TY LE / do do chuan hoa phai nam trong [0, 1] (hoac [-1, 1] voi
      tuong quan va cac cot hieu `*_gain`, `*_gap`, `*_drop`, `delta*`).
  H3. Moi o phai doc duoc thanh so (tru cot nhan chu), khong `nan`, khong rong.
  H4. Cot `*_std` phai >= 0.
Khong co luat nao o day doan y nghia: cot nao chua biet kieu thi KE RA, khong cho
qua im lang. ⇒ [[feedback-kiem-0-don-vi-khong-phai-sach]]
"""
import functools, builtins
builtins.print = functools.partial(builtins.print, flush=True)

import csv, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")

loi, da_cham = [], []


def dat(ten, ok, td):
    da_cham.append(ten)
    print(f"  {'' if ok else '⛔ '}{ten} {td}")
    if not ok:
        loi.append(f"{ten} {td}")


def doc(f):
    with open(os.path.join(RES, f), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def so(v):
    """Tra ve float, hoac None neu o nay khong phai so."""
    if v is None:
        return None
    s = v.strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


# ── tran cho cot dem, doc tu dataset_profile.csv ────────────────────────────────
def ho_so():
    """{tap: {'rows': n_rows_used, 'feat': n_features, 'atk': n_attack}} + muc TRAN."""
    h = doc("dataset_profile.csv")
    d = {}
    for x in h:
        d[x["dataset"]] = {k: so(x[c]) for k, c in
                           (("rows", "n_rows_used"), ("feat", "n_features"),
                            ("atk", "n_attack"))}
    assert d and all(v is not None for r in d.values() for v in r.values())
    d["*"] = {k: max(r[k] for n, r in d.items() if n != "*") for k in ("rows", "feat", "atk")}
    return d


# ── phan loai cot bang QUAN HE voi du lieu, khong bang danh sach ten ───────────
# Cot nhan: KHONG o nao trong cot doc duoc thanh so. Nhan ra bang quan he nhu vay
# thi mot cot nhan moi them vao khong lam cong bao dong gia, con mot cot so bi TRON
# chu vao van bi bat. ⇒ [[feedback-nhan-dien-bang-quan-he-khong-bang-thuoc-tinh]]
DEM = re.compile(r"^(n|k|num|count)(_|$)", re.I)
FEAT = re.compile(r"(feature|cluster|dim|informative)", re.I)
ATK = re.compile(r"attack", re.I)

# ⛔⛔ CSV phu THIEU tap. Ngay 10/11/2026 attack.csv, defense.csv, gate_attack.csv
# chi co 3/5 tap trong khi script lap `for ds in DATASETS` voi DATASETS co 5 tap: ba
# tep ay la hien vat CU, sinh ra truoc khi TON-IoT va CIC-IoT-2023 duoc them vao, va
# khong cong nao thay vi cong do DO MOI (mtime) chu khong do DO PHU. Mot bang in 3
# tap trong mot bai tu khai "five corpora" la mot lo hong phan bien mo ngay ra.
# ⇒ [[feedback-cong-cham-nham-hien-vat]] · [[feedback-bang-hinh-go-tay-khong-cap-nhat]]
PHU_IT = {
    "harm_bytype.csv": (["CICIDS", "TON-IoT"],
                        "chi hai tap co nhan DA LOP (`Attack Type`, `type`); "
                        "exp_harm_bytype.py lap dung hai tap ay"),
}

# ⛔ Cot that su co the vuot [-1, 1]. Moi muc phai co LY DO, va cong IN RA chung
# moi lan chay de mot mien tru khong con dung van bi nhin thay.
# ⛔⛔ O RONG duoc phep, CHI o nhung cho khai duoi day, kem ly do. `exp_leakage.py`
# de trong `f1/p2/p3_trung` khi nua tap do duoi 200 hang: in mot con so tren 0 hang
# hay tren 20 hang la BIA, con in rong la noi "khong do duoc". Nhung rong KHONG
# duoc la cua sau: moi o rong khac van la loi, va mot muc khai khong con o rong nao
# cung la loi, vi no thanh mot cho mo khong ai canh.
# ⇒ [[feedback-kiem-0-don-vi-khong-phai-sach]] · [[feedback-dau-xac-nhan-phai-tu-mat-hieu-luc]]
O_RONG_CHO_PHEP = {
    ("leakage.csv", "f1_trung"): "nua tap co ban sao duoi 200 hang: khong do duoc",
    ("leakage.csv", "p2_trung"): "nhu tren",
    ("leakage.csv", "p3_trung"): "nhu tren",
    ("pooled_reader.csv", "p_rand"): "doi chung nhieu chi co nghia o che do `pooled` "
                                     "(co sibling bi giu lai de thu); hang `single` "
                                     "de trong, khong dien so gia vao",
}


def _ban_do_csv():
    """Danh sach CSV cua du an, doc tu `check_freshness.MAP`, khong dem tay."""
    import importlib.util
    sp = importlib.util.spec_from_file_location(
        "_cf", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "check_freshness.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return dict(m.MAP)


MIEN_TRU = {
    "p1_fidelity_retention": "ty so giu lai, >1 khi surrogate vuot mo hinh goc",
    "J_over_chance": "Jaccard chia cho muc tinh co, khong co tran tren",
    "year": "nam cong bo trong field_audit",
    # rerun.csv: ba cot nay la THAM SO cua phep do, khong phai ket qua do
    "shap_nsamples": "so mau KernelSHAP cua tung ngan sach (rerun.csv)",
    "lime_nsamples": "so mau LIME cua tung ngan sach (rerun.csv)",
    "n_flows": "so luong do tu-nhat-quan tren (rerun.csv)",
}

def main():
    HS = ho_so()
    tep = sorted(f for f in os.listdir(RES) if f.endswith(".csv"))

    n_o = n_nhan = 0
    xau_dem, xau_khoang, xau_tron, xau_std, mien = [], [], [], [], []
    rong_thay = set()

    for f in tep:
        hang = doc(f)
        if not hang:
            xau_tron.append(f"{f}: 0 hang")
            continue
        for c in hang[0]:
            if c is None:
                continue
            gt = [so(h.get(c)) for h in hang]
            if all(v is None for v in gt):
                n_nhan += 1
                continue
            if any(v is None for v in gt):
                rong = [i for i, v in enumerate(gt)
                        if v is None and str(hang[i].get(c) or "").strip() == ""]
                if (f, c) in O_RONG_CHO_PHEP and len(rong) == sum(
                        1 for v in gt if v is None):
                    rong_thay.add((f, c))
                    gt = [v for v in gt if v is not None]
                    if not gt:
                        n_nhan += 1
                        continue
                else:
                    # ⛔ Mot cot VUA co so VUA co chu la trieu chung that, khong phai cot nhan.
                    xau_tron += [f"{f}:{c} hang {i}: {hang[i].get(c)!r}"
                                 for i, v in enumerate(gt) if v is None][:3]
                    continue
            for i, x in enumerate(gt):
                n_o += 1
                if math.isnan(x):
                    xau_tron.append(f"{f}:{c} hang {i}: nan")
                    continue
                if c.endswith("_std"):
                    if x < 0:
                        xau_std.append(f"{f}:{c} hang {i} = {x}")
                    continue
                if c in MIEN_TRU:
                    mien.append(f"{f}:{c}")
                    continue
                if DEM.match(c):
                    # Tran theo CHINH tap cua hang do neu hang khai `dataset`.
                    r = HS.get(str(hang[i].get("dataset", "*")).strip(), HS["*"])
                    gh = r["feat"] if FEAT.search(c) else (r["atk"] if ATK.search(c) else r["rows"])
                    if x < 0 or x != int(x) or x > gh:
                        xau_dem.append(f"{f}:{c} hang {i} = {x:g} (tran {int(gh)})")
                    continue
                if not (-1.0 - 1e-9 <= x <= 1.0 + 1e-9):
                    xau_khoang.append(f"{f}:{c} hang {i} = {x:g}")

    # ⛔ In so o DA DOC: "0 o xau" tren 0 o khong phan biet duoc sach voi khong doc
    # duoc gi. ⇒ [[feedback-kiem-0-don-vi-khong-phai-sach]]
    # ⛔⛔ Truoc 11/11/2026 dong nay la `len(tep) == 24`, mot so DEM GAI CUNG. Them
    # `exp_rerun.py` la cong do ngay, va no do VI MOT LY DO DUNG nhung thong bao thi
    # vo nghia ("25/24 CSV"). So CSV cua du an co DUNG MOT nguon su that:
    # `check_freshness.MAP`. Noi vao do thi no khong bao gio lech nua.
    # ⇒ [[feedback-so-headline-mot-cho-o]]
    can = len(_ban_do_csv())
    dat("H0", n_o > 0 and len(tep) == can,
        f"doc {n_o} o so + {n_nhan} cot nhan tren {len(tep)}/{can} CSV "
        f"(ky vong lay tu check_freshness.MAP)")
    dat("H1", not xau_dem,
        f"cot DEM trong tran lay tu dataset_profile.csv: {len(xau_dem)} o vo ly"
        + (("; ⛔ " + "; ".join(xau_dem[:6])) if xau_dem else ""))
    dat("H2", not xau_khoang,
        f"cot do khong mien tru nam trong [-1, 1]: {len(xau_khoang)} o ngoai"
        + (("; ⛔ " + "; ".join(xau_khoang[:6])) if xau_khoang else ""))
    dat("H3", not xau_tron,
        f"khong cot nao TRON so voi chu, khong o nan: {len(xau_tron)} o xau"
        + (("; ⛔ " + "; ".join(xau_tron[:6])) if xau_tron else ""))
    dat("H4", not xau_std, f"cot `_std` khong am: {len(xau_std)} o am"
        + (("; ⛔ " + "; ".join(xau_std[:6])) if xau_std else ""))
    # ⛔ Mien tru phai HIEN RA moi lan chay, khong thi no thanh cua sau im lang.
    # ⛔⛔ Truoc 11/11/2026 dong nay so `len(set(mien))` voi `len(MIEN_TRU)`, ma `mien`
    # giu cap `tep:cot`. Mot ten cot co o HAI tep (`n_flows` trong rerun.csv va
    # prop2_topk.csv) la cong do ngay, du khong mien tru nao chet. Phai so TEN COT.
    # ⇒ [[feedback-cong-phu-dem-khoa-hay-dem-gia-tri]]
    ten_mien = {x.split(":", 1)[1] for x in mien}
    chet_rong = sorted(k for k in O_RONG_CHO_PHEP if k not in rong_thay)
    dat("H5", ten_mien == set(MIEN_TRU) and not chet_rong,
        "mien tru dung: " + ", ".join(f"{k} ({v})" for k, v in MIEN_TRU.items())
        + f" | thay {len(ten_mien)}/{len(MIEN_TRU)} cot mien tru trong du lieu"
        + f"; o rong khai {len(rong_thay)}/{len(O_RONG_CHO_PHEP)} con doi tuong"
        + (f"; ⛔ KHAI O RONG DA CHET: {chet_rong}" if chet_rong else "")
        + (f"; ⛔ mien tru CHET: {sorted(set(MIEN_TRU) - ten_mien)}"
           if set(MIEN_TRU) - ten_mien else ""))

    # ── H6: do phu tap du lieu ───────────────────────────────────────────────
    import data as _d
    DS = list(_d.DATASETS)
    thieu, n_kiem, mien_phu = [], 0, []
    for f in tep:
        hang = doc(f)
        if not hang or "dataset" not in hang[0]:
            continue
        n_kiem += 1
        co = {str(h["dataset"]).strip() for h in hang}
        if f in PHU_IT:
            can, ly_do = PHU_IT[f]
            mien_phu.append(f"{f} ({ly_do})")
            if set(can) != co:
                thieu.append(f"{f}: khai {sorted(can)} ma CSV co {sorted(co)}")
            continue
        v = [x for x in DS if x not in co]
        if v:
            thieu.append(f"{f}: co {len(co)}/{len(DS)}, THIEU {v}")
    dat("H6", not thieu and n_kiem > 0,
        f"kiem do phu tren {n_kiem} CSV co cot `dataset`, chuan {len(DS)} tap tu "
        f"data.DATASETS; {len(thieu)} CSV phu thieu"
        + (("; ⛔ " + "; ".join(thieu[:6])) if thieu else "")
        + ("; mien tru: " + "; ".join(mien_phu) if mien_phu else "")
        + ("; ⛔ KIEM 0 CSV, khong ket luan duoc gi" if n_kiem == 0 else ""))

    if loi:
        sys.exit(f"\n{len(loi)}/{len(da_cham)} cong DO: "
                 + ", ".join(d.split()[0] for d in loi))
    print(f"\n  => {len(da_cham)}/{len(da_cham)} cong XANH")


if __name__ == "__main__":
    main()
