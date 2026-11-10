"""Cong: khoi "Environment" trong bai PHAI khop requirements.txt, va ca hai PHAI
phu het thu vien ma code/ that su import.

Vi sao can. Bai viet o phu luc Tai lap:
    "all pinned in requirements.txt"
    "After `pip install -r requirements.txt`, running `python <script>.py` ..."
Nhung den 09/11/2026 tep `requirements.txt` **KHONG TON TAI** trong kho, khong trong
cay lam viec, va `.gitignore` cung khong chan no. Bai bao nguoi doc chay mot lenh
tro vao mot tep chua bao gio duoc viet. Ban clone sach bat duoc dieu nay, cay lam
viec thi khong, vi khong ai go lenh ay bao gio.
⇒ [[feedback-clone-sach-bat-loi-diem-vao]] · [[feedback-van-xuoi-artifact-cung-la-tuyen-bo]]

Va bai ke 6 goi trong khi quet AST ra 8: thieu `matplotlib` va `pandas`.
⇒ Mot ban ke THIEU cung la mot ban ke SAI.

Cong:
  M1  requirements.txt TON TAI
  M2  moi goi ma code/ import deu co trong requirements.txt
  M3  requirements.txt khong ghim goi nao ma code/ KHONG dung (tru goi cong cu)
  M4  moi ban trong khoi "Environment" cua bai khop requirements.txt tung ky tu
  M5  environment.yml ghim CUNG ban voi requirements.txt
"""
import ast
import os
import re
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQ = os.path.join(GOC, "requirements.txt")
YML = os.path.join(GOC, "environment.yml")
NGUON = os.path.join(GOC, "paper", "main.tex")
MA = os.path.join(GOC, "code")
VENDOR = os.path.join(GOC, "code", "vendor", "plot-assets")

# module -> ten goi pip, cho nhung cho hai ten khac nhau
TEN_GOI = {"sklearn": "scikit-learn", "docx": "python-docx",
           "PIL": "pillow", "fitz": "PyMuPDF"}
# Goi chi dung cho CONG CU cua nha (sinh .docx), khong phai de chay thi nghiem.
CONG_CU = {"python-docx"}
# ⛔⛔ Goi KHONG xuat hien trong do thi import ma VAN bat buoc, vi thu vien khac nap
# chung BEN TRONG ham. Quet AST MU voi loai nay. Mien tru o M3 chi hop le vi M6
# chung minh bang cach CHAY THAT; bo pyarrow ra thi M6 do, khong phai im lang.
# ⇒ [[feedback-dieu-kien-can-dung-nhu-dieu-kien-du]]
LUC_CHAY = {"pyarrow": "pandas.read_parquet nap ben trong ham; data.py doc 2 tep .parquet"}
# Ten trong bai <-> ten trong requirements. Bai viet \texttt{numpy} 2.0.2 ...
TEN_BAI = ["numpy", "scipy", "scikit-learn", "torch", "shap", "lime",
           "matplotlib", "pandas", "pyarrow",
           "pillow", "PyMuPDF"]


def goi_ma_dung():
    """Quet AST toan bo code/ de biet ma THAT SU import gi."""
    thu_muc = [MA] + ([VENDOR] if os.path.isdir(VENDOR) else [])
    noi_bo = {f[:-3] for d in thu_muc for f in os.listdir(d) if f.endswith(".py")}
    ra = set()
    for d, f in sorted((d, f) for d in thu_muc for f in os.listdir(d) if f.endswith(".py")):
        t = ast.parse(open(os.path.join(d, f), encoding="utf-8").read())
        for n in ast.walk(t):
            if isinstance(n, ast.Import):
                ra |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
                ra.add(n.module.split(".")[0])
    ra -= noi_bo
    # Bo thu vien chuan: thu nhap, cai nao nhap duoc ma khong co o site-packages
    # thi coi la chuan. Danh sach cung se cu di, phep thu thi khong.
    import importlib.util
    chuan = set()
    for m in ra:
        s = importlib.util.find_spec(m) if m not in ("torch",) else None
        if s and s.origin and "site-packages" not in (s.origin or ""):
            chuan.add(m)
    return {TEN_GOI.get(m, m) for m in (ra - chuan)}


def ghim_tu_req():
    if not os.path.exists(REQ):
        return None
    d = {}
    for dong in open(REQ, encoding="utf-8"):
        dong = dong.split("#")[0].strip()
        m = re.match(r"^([A-Za-z0-9_.\-]+)==([^\s]+)$", dong)
        if m:
            d[m.group(1)] = m.group(2)
    return d


def ghim_tu_bai():
    tex = open(NGUON, encoding="utf-8").read()
    m = re.search(r"\\textbf\{Environment\.\}(.*?)\\textbf\{", tex, re.S)
    if not m:
        return None, None
    khoi = m.group(1)
    py = re.search(r"Python ([\d.]+)", khoi)
    d = {}
    for ten in TEN_BAI:
        mm = re.search(r"\\texttt\{" + re.escape(ten) + r"\}\s*([\d][\w.]*)", khoi)
        if mm:
            d[ten] = mm.group(1).rstrip(".")
    return (py.group(1) if py else None), d


def ghim_tu_yml():
    if not os.path.exists(YML):
        return None
    d = {}
    for dong in open(YML, encoding="utf-8"):
        dong = dong.split("#")[0].strip().lstrip("- ")
        m = re.match(r"^([A-Za-z0-9_.\-]+)[=]{1,2}([\d][\w.]*)$", dong)
        if m:
            d[m.group(1)] = m.group(2)
    return d


def main():
    loi, da_cham = [], []

    def dat(ten, dung, td):
        # ⛔⛔ In NGAY ca that bai, dung cho tới cuoi. Ban dau ham nay chi GOM loi vao
        # `loi` roi in o cuoi, nen khi mot cong sau no SAP thi moi loi da ghi BIEN MAT
        # cung tien trinh: ca tiem U1 ngay 10/11/2026 lam S1 do, S3 sap, va dau ra
        # KHONG he co dong nao noi S1 do. ⇒ [[feedback-cong-khong-doc-loi-that]]
        da_cham.append(ten)
        print(f"  {ten} {td}" if dung else f"  ⛔ {ten} {td}")
        if not dung:
            loi.append(f"{ten} {td}")

    req = ghim_tu_req()
    dat("M1", req is not None, f"requirements.txt {'co' if req else 'KHONG TON TAI'}")
    if req is None:
        print("\n  ⛔", loi[0])
        sys.exit("\n1 cong DO: khong cham tiep duoc")

    dung = goi_ma_dung()
    thieu = sorted(g for g in dung if g not in req and g not in CONG_CU)
    dat("M2", not thieu, f"ma import {len(dung)} goi, THIEU trong requirements: {thieu or 'khong'}")

    thua = sorted(g for g in req if g not in dung and g not in CONG_CU and g not in LUC_CHAY)
    dat("M3", not thua, f"requirements ghim {len(req)} goi, THUA (ma khong dung): {thua or 'khong'}")

    py_bai, bai = ghim_tu_bai()
    lech = sorted(f"{k}: bai {v} vs req {req.get(k, 'KHONG GHIM')}"
                  for k, v in (bai or {}).items() if req.get(k) != v)
    bai_thieu = sorted(g for g in req if g not in (bai or {}) and g not in CONG_CU)
    dat("M4", not lech and not bai_thieu,
        f"bai ke {len(bai or {})} goi; lech {lech or 'khong'}; "
        f"bai KHONG ke {bai_thieu or 'khong'}")

    yml = ghim_tu_yml()
    if yml is None:
        dat("M5", False, "environment.yml KHONG TON TAI")
    else:
        yl = sorted(f"{k}: yml {yml[k]} vs req {req[k]}"
                    for k in req if k in yml and yml[k] != req[k])
        # pytorch trong conda mang ten khac torch
        if "pytorch" in yml and req.get("torch") and yml["pytorch"] != req["torch"]:
            yl.append(f"pytorch: yml {yml['pytorch']} vs req torch {req['torch']}")
        # ⛔⛔ Ban dau M5 chi so cac goi CO MAT O CA HAI (`k in yml`), nen mot goi
        # VANG HAN khoi environment.yml thi cong KHONG THAY. Do la dung ca
        # "bat SAI ma khong bat THIEU": hom 10/11/2026 no bao "khop" trong khi yml
        # thieu ca `pillow` va `PyMuPDF`. ⇒ [[feedback-cong-bat-sai-khong-bat-thieu]]
        vang = sorted(k for k in req if k not in yml
                      and not (k == "torch" and "pytorch" in yml))
        if vang:
            yl.append(f"VANG HAN khoi environment.yml: {vang}")
        dat("M5", not yl, f"environment.yml khop requirements ({len(req)} goi): {yl or 'khop'}")

    # ⛔⛔ M6: cong DUY NHAT chay THAT. Bon cong tren chi doc van ban; chung da
    # BAO XANH suot trong khi moi truong khai cua bai KHONG NAP NOI 2/5 bo du lieu,
    # vi `pandas.read_parquet` can pyarrow ma khong ai `import pyarrow`.
    # Bat duoc 10/11/2026 bang cach CHAY tren sol1. ⇒ [[feedback-nap-duoc-khong-phai-chay-duoc]]
    thieu_engine = []
    try:
        import pandas as _pd
        from pandas.io.parquet import get_engine as _ge
        _ge("auto")
    except Exception as e:
        thieu_engine.append(f"{type(e).__name__}: {str(e).splitlines()[0][:70]}")
    # Va kiem ca duong THAT: neu data/ co mat thi doc thu 1 dong cua tung .parquet
    doc_that = []
    for t in ("data/unsw/UNSW_NB15_training-set.parquet",
              "data/ciciot2023/cic_iot_2023.parquet"):
        p = os.path.join(GOC, t)
        if not os.path.exists(p):
            doc_that.append(f"{os.path.basename(t)}: KHONG CO TEP (bo qua)")
            continue
        try:
            import pandas as _pd
            _pd.read_parquet(p).head(1)
            doc_that.append(f"{os.path.basename(t)}: doc OK")
        except Exception as e:
            doc_that.append(f"{os.path.basename(t)}: ⛔ {type(e).__name__}")
            thieu_engine.append(f"read_parquet({os.path.basename(t)}) that bai")
    # ⛔ Neu khong co tep nao de thu thi M6 KHONG duoc xanh: no da khong kiem gi.
    # Phep thu `get_engine("auto")` o tren van chay duoc ke ca khi vang tep, nen
    # dieu kien la "engine giai duoc" VA "co it nhat mot tep that su doc duoc".
    doc_ok = sum(1 for d in doc_that if "doc OK" in d)
    dat("M6", not thieu_engine and doc_ok > 0,
        f"pandas doc duoc .parquet ({doc_ok} tep): "
        + ("; ".join(doc_that) if doc_that else "khong co tep de thu")
        + ("; ⛔ KHONG doc duoc tep nao, khong ket luan duoc gi" if doc_ok == 0 else "")
        + (f" | LOI: {thieu_engine}" if thieu_engine else ""))

    if loi:
        # `dat` da in tung loi ngay luc xay ra, nen o day chi tong ket, khong in lai.
        sys.exit(f"\n{len(loi)}/{len(da_cham)} cong DO: {', '.join(d.split()[0] for d in loi)}")
    print(f"\n  => {len(da_cham)}/{len(da_cham)} cong XANH  (Python bai khai: {py_bai})")


if __name__ == "__main__":
    main()
