"""Cong du lieu: `data/` co DU 5 bo, va DUNG tung byte nhung bo da sinh ra so cua bai.

Vi sao can. `data/` khong theo git (hai tep vuot tran cung 100 MB cua GitHub), nen
nguoi doc phai tu tai ve. Khong co cong nay thi mot tep khac ban, khac phien ban cleaned,
hay tai thieu mot nua se KHONG lo ra o buoc nao ca: `data.load` van chay, so van ra,
chi la ra SO KHAC. Do la ca xau nhat: hong mà van xanh.
⇒ [[feedback-dung-lai-bang-cong-cu-cua-noi-nhan]] · [[feedback-cong-khong-so-hai-nguon]]

Cong:
  D1  ca 5 tep co mat
  D2  sha256 tung tep khop `data-manifest.sha256`
  D3  ban ke va `code/data.py` noi cung mot bo duong dan (khong he tham chieu thu hai)
  D4  doc duoc THAT: pandas nap duoc 1 dong cua tung tep, ke ca hai tep .parquet
"""
import hashlib
import os
import re
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(GOC, "data")
KE = os.path.join(GOC, "data-manifest.sha256")
NGUON = os.path.join(GOC, "code", "data.py")


def doc_ban_ke():
    if not os.path.exists(KE):
        return None
    d = {}
    for dong in open(KE, encoding="utf-8"):
        dong = dong.strip()
        if not dong or dong.startswith("#"):
            continue
        bam, _, duong = dong.partition("  ")
        d[duong.strip()] = bam.strip()
    return d


def bam(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 22)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def duong_trong_data_py():
    """Bo duong dan ma data.py THAT SU doc, boc tu nguon chu khong go lai."""
    tex = open(NGUON, encoding="utf-8").read()
    return sorted(set(re.findall(r'\{BASE\}/([^"\')]+)', tex)))


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

    ke = doc_ban_ke()
    if ke is None:
        sys.exit(f"⛔ khong co {os.path.relpath(KE, GOC)}: cong dang MU")

    thieu = [k for k in ke if not os.path.exists(os.path.join(DATA, k))]
    dat("D1", not thieu, f"{len(ke) - len(thieu)}/{len(ke)} tep co mat"
        + (f"; THIEU: {thieu}" if thieu else ""))

    lech = []
    for k, mong in ke.items():
        p = os.path.join(DATA, k)
        if not os.path.exists(p):
            continue
        that = bam(p)
        if that != mong:
            lech.append(f"{k}: mong {mong[:12]}... that {that[:12]}...")
    # ⛔⛔ KIEM 0 DON VI KHONG PHAI SACH. Tu clone sach (chua co data/), ban dau D2 in
    # "sha256 khop 0/0 tep da doc" va duoc tinh la XANH. Mot cong da kiem KHONG CAI GI
    # ma vao cot xanh thi no la cong mu. ⇒ [[feedback-kiem-0-don-vi-khong-phai-sach]]
    da_doc = len(ke) - len(thieu)
    dat("D2", not lech and da_doc > 0,
        f"sha256 khop {da_doc - len(lech)}/{da_doc} tep da doc"
        + ("; ⛔ KIEM 0 TEP, khong ket luan duoc gi" if da_doc == 0 else "")
        + (f"; LECH: {lech}" if lech else ""))

    # ⛔ Ban ke la HE THAM CHIEU THU HAI ben canh data.py. Hai cai phan ky thi ban ke
    # bao xanh cho nhung tep ma code khong he doc. Phai so hai chieu.
    tu_ma = set(duong_trong_data_py())
    tu_ke = set(ke)
    chi_ma = sorted(tu_ma - tu_ke)
    chi_ke = sorted(tu_ke - tu_ma)
    dat("D3", not chi_ma and not chi_ke,
        f"data.py doc {len(tu_ma)} duong, ban ke co {len(tu_ke)}"
        + (f"; CHI data.py: {chi_ma}" if chi_ma else "")
        + (f"; CHI ban ke: {chi_ke}" if chi_ke else ""))

    # ⛔ "Bam dung" KHONG phai "doc duoc". Tep .parquet dung bam ma thieu pyarrow thi
    # van nem ImportError. Da vap dung ca nay tren sol1 ngay 10/11/2026.
    khong_doc = []
    try:
        import pandas as pd
    except Exception as e:
        khong_doc.append(f"import pandas: {type(e).__name__}")
        pd = None
    if pd is not None:
        for k in ke:
            p = os.path.join(DATA, k)
            if not os.path.exists(p):
                continue
            try:
                if k.endswith(".parquet"):
                    pd.read_parquet(p).head(1)
                else:
                    pd.read_csv(p, nrows=5, low_memory=False)
            except Exception as e:
                khong_doc.append(f"{k}: {type(e).__name__}")
    dat("D4", not khong_doc and da_doc > 0, f"pandas doc thu {da_doc} tep"
        + ("; ⛔ KIEM 0 TEP, khong ket luan duoc gi" if da_doc == 0 else "")
        + (f"; KHONG DOC DUOC: {khong_doc}" if khong_doc else ""))

    if loi:
        # `dat` da in tung loi ngay luc xay ra, nen o day chi tong ket, khong in lai.
        sys.exit(f"\n{len(loi)}/{len(da_cham)} cong DO: {', '.join(d.split()[0] for d in loi)}")
    print(f"\n  => {len(da_cham)}/{len(da_cham)} cong XANH")


if __name__ == "__main__":
    main()
