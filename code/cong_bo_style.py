"""Cong bo style: ban sao `code/vendor/plot-assets` phai la ban sao THAT, va khong LECH.

Vi sao can. Truoc 10/11/2026, `code/plots.py` import `agentra_plot` tu mot duong dan
NGOAI kho, nen tu clone sach no nem `ModuleNotFoundError` trong khi bai hua
"running python plots.py rebuilds every figure". Nay module da nam trong kho.

⛔ Nhung dua mot bo style vao kho tao ra BAN SAO THU HAI cua mot thu da co ban chuan.
Hai ban sao la hai nguon su that, va cai trong kho se muc trong im lang khi ban chuan
duoc sua. Cong nay la thu giu chung thanh MOT.
⇒ [[feedback-dia-chi-cong-bo-va-dia-chi-that-phan-ky]] · [[feedback-hinh-co-bo-style-nha-roi]]

Cong:
  S1  ca 3 tep co mat trong code/vendor/plot-assets
  S2  bam tung tep khop VENDOR.sha256
  S3  neu ban CHUAN co tren may nay: ban trong kho KHONG LECH khoi no
      (vang ban chuan thi bao RO rang la khong kiem duoc, khong im lang cho qua)
  S4  plots.py that su import duoc tu ban trong kho, KHONG nho duong dan ngoai
"""
import hashlib
import os
import re
import subprocess
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAN_SAO = os.path.join(GOC, "code", "vendor", "plot-assets")
KE = os.path.join(GOC, "code", "vendor", "VENDOR.sha256")
# Ban chuan cua nha. Chi co tren may Hao; tren may khac thi S3 bao khong kiem duoc.
CHUAN = os.environ.get("AGENTRA_PLOT_CANON", os.path.join(
    GOC, "..", "..", "my-skills", "ALL-FIGURES", "0-SKILLS", "plot-figure-dph", "assets"))


def bam(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


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

    if not os.path.exists(KE):
        sys.exit(f"⛔ khong co {os.path.relpath(KE, GOC)}: cong dang MU")
    ke = {}
    for dong in open(KE, encoding="utf-8"):
        dong = dong.strip()
        if dong and not dong.startswith("#"):
            b, _, t = dong.partition("  ")
            ke[t.strip()] = b.strip()

    thieu = [t for t in ke if not os.path.exists(os.path.join(BAN_SAO, t))]
    dat("S1", not thieu, f"{len(ke) - len(thieu)}/{len(ke)} tep trong ban sao"
        + (f"; THIEU: {thieu}" if thieu else ""))

    lech = [f"{t}: ke {m[:12]}... that {bam(os.path.join(BAN_SAO, t))[:12]}..."
            for t, m in ke.items()
            if os.path.exists(os.path.join(BAN_SAO, t))
            and bam(os.path.join(BAN_SAO, t)) != m]
    dat("S2", not lech, f"bam khop VENDOR.sha256: {lech or 'khop het'}")

    # ⛔ S3 khong duoc im lang khi vang ban chuan. Mot cong "khong kiem duoc" phai
    # NOI RA, vi im lang se bi doc thanh "da kiem va dat".
    if not os.path.isdir(CHUAN):
        print(f"  S3 ⚠ KHONG KIEM DUOC: khong thay ban chuan tai\n"
              f"       {os.path.normpath(CHUAN)}\n"
              f"       Day KHONG phai dau xanh. Tren may co ban chuan thi phai chay lai.")
        da_cham.append("S3")
    else:
        # ⛔ Phai doi CA HAI ben ton tai truoc khi bam. Ban dau chi kiem ben CHUAN,
        # nen thieu tep o ban SAO lam S3 nem FileNotFoundError va giet ca cong.
        pk, vang = [], []
        for t in ke:
            a, b = os.path.join(BAN_SAO, t), os.path.join(CHUAN, t)
            if not os.path.exists(b):
                vang.append(t)
            elif not os.path.exists(a):
                pk.append(f"{t}: ban sao KHONG CO TEP")
            elif bam(a) != bam(b):
                pk.append(f"{t}: ban sao {bam(a)[:12]}... chuan {bam(b)[:12]}...")
        dat("S3", not pk and not vang,
            f"ban sao khong lech khoi ban chuan ({len(ke) - len(vang)} tep so duoc)"
            + (f"; LECH: {pk}" if pk else "")
            + (f"; chuan THIEU: {vang}" if vang else ""))

    # ⛔ S4: "tep co mat" khong phai "import duoc". Chay THAT trong tien trinh rieng,
    # va bo moi duong dan ngoai de chung minh no khong dua vao may Hao.
    ma = """
import os, sys
sys.path.insert(0, os.path.join(%r, "code", "vendor", "plot-assets"))
import agentra_plot as ap
ap.use_style()
assert hasattr(ap, "save") and hasattr(ap, "headline")
print("OK", ap.INK)
""" % GOC
    mt = {k: v for k, v in os.environ.items() if k != "AGENTRA_PLOT_ASSETS"}
    r = subprocess.run([sys.executable, "-c", ma], capture_output=True, text=True, env=mt)
    dat("S4", r.returncode == 0,
        "import agentra_plot tu ban trong kho: "
        + ("OK, use_style() chay" if r.returncode == 0
           else f"⛔ {(r.stderr or r.stdout).strip().splitlines()[-1][:90]}"))

    # Va kiem plots.py KHONG con tro ra ngoai kho
    pt = open(os.path.join(GOC, "code", "plots.py"), encoding="utf-8").read()
    ra_ngoai = re.search(r'ASSETS\s*=\s*os\.environ\.get\([^)]*"\.\.\s*"', pt, re.S)
    dat("S5", not ra_ngoai and 'os.path.join(\n    os.path.dirname(__file__), "vendor"' in pt
        or 'os.path.dirname(__file__), "vendor", "plot-assets"' in pt,
        "plots.py mac dinh tro vao ban TRONG kho")

    if loi:
        print()
        for d in loi:
            print("  ⛔", d)
        sys.exit(f"\n{len(loi)}/{len(da_cham)} cong DO")
    print(f"\n  => {len(da_cham)}/{len(da_cham)} cong XANH")


if __name__ == "__main__":
    main()
