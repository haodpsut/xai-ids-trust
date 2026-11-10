"""Cong: QUAN THE flow dung de do giai thich phai co DUNG MOT dinh nghia.

Vi sao can. Doc ngoai vong 1 (09/11/2026) bat duoc Table 4 lech Fig 5 toi 0,18 va
lech HAI CHIEU. Mo ma ra thi khong phai loi so, ma la HAI QUAN THE khac nhau:

    exp_trust.py :: p2_determinacy   idx = where(predict==1 & yte==1)[:1000]   # tan cong DA PHAT HIEN
    exp_trust.py :: p3_groundedness  sub = Xte[:1000]                          # 1000 flow DAU, ca lanh

⛔⛔ Do 10/11/2026 thi no KHONG CHI o mot cho: `exp_redundancy.py` lap y nguyen cap
loi ay (`p2_pairs` dung tan cong da phat hien, `p3_sets` dung `Xte[:1000]`). Nghia la
TRONG CUNG MOT TEP, P2 va P3 do tren hai tap flow khac nhau, roi bai dat chung canh
nhau trong cung mot bang.

Va goc re la bieu thuc chon quan the bi CHEP TAY o 13 tep, moi noi mot con so cat
(800, 1000, 1500, 2000, NSAMP). Mot dinh nghia bi chep 13 lan thi viec no phan ky
chi la van de thoi gian, khong phai mot su co. ⇒ Sua tan goc: MOT ham trong
harness.py, moi noi goi no.
⇒ [[feedback-mot-tham-so-dieu-khien-hai-thu]] · [[feedback-hai-duong-ong-so-phu-noi-vao-mot]]

Cong:
  Q1  harness.py co ham `flow_bao_dong` va no la cho DUY NHAT dinh nghia quan the
  Q2  khong tep exp_*.py nao con bieu thuc chon quan the CHEP TAY
  Q3  khong tep exp_*.py nao lay quan the bang cach cat `Xte[:N]`
  Q4  trong cung mot tep, P2 va P3 goi CUNG mot ham quan the
"""
import os
import re
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MA = os.path.join(GOC, "code")
HARNESS = os.path.join(MA, "harness.py")
TEN_HAM = "flow_bao_dong"

# Bieu thuc chep tay: `where((predict(...) == 1) & (yte == 1))` hoac bien the dung
# `.all(1)` cho nhieu mo hinh.
CHEP_TAY = re.compile(r"\(\s*(?:predict\([^)]*\)|[A-Za-z_][\w.]*\.predict\([^)]*\)|preds)\s*=="
                      r"\s*1\s*\)[^\n]*&[^\n]*\(\s*yte\s*==\s*1\s*\)"
                      r"|\(\s*yte\s*==\s*1\s*\)[^\n]*&[^\n]*\(\s*(?:preds|predict\([^)]*\))\s*==\s*1\s*\)")
CAT_XTE = re.compile(r"\bXte\s*\[\s*:\s*\d+\s*\]")


def cac_tep():
    return sorted(f for f in os.listdir(MA)
                  if f.startswith(("exp_", "field_")) and f.endswith(".py"))


def main():
    loi, da_cham = [], []

    def dat(ten, dung, td):
        da_cham.append(ten)
        print(f"  {ten} {td}" if dung else f"  ⛔ {ten} {td}")
        if not dung:
            loi.append(f"{ten} {td}")

    hn = open(HARNESS, encoding="utf-8").read() if os.path.exists(HARNESS) else ""
    m_ham = re.search(r"^def\s+" + TEN_HAM + r"\s*\(.*?(?=^def |\Z)", hn, re.M | re.S)
    # ⛔ Q1 phai kiem CAU TRUC cua ham, dung di tim lai bieu thuc chep-tay: trong
    # harness bien ten la `p` chu khong phai `preds`, nen bieu thuc kia khong khop
    # va Q1 bao do tren mot ham DA DUNG. Mot cong di tim dau CHINH TA thay vi dau
    # NGHIA thi bao do oan. ⇒ [[feedback-cong-kiem-ten-thay-vi-ban-chat]]
    than = m_ham.group(0) if m_ham else ""
    du = all(x in than for x in ("yte", "== 1", ".all(1)", "np.where"))
    dat("Q1", bool(m_ham) and du,
        f"harness.py co `{TEN_HAM}`: {'CO' if m_ham else 'KHONG'}; "
        f"than ham co du (yte==1, .all(1), np.where): {'CO' if du else 'KHONG'}")

    vp2, vp3 = {}, {}
    for f in cac_tep():
        t = open(os.path.join(MA, f), encoding="utf-8").read()
        t = "\n".join(re.sub(r"(?<!\\)#.*$", "", d) for d in t.split("\n"))
        n = len(CHEP_TAY.findall(t))
        if n:
            vp2[f] = n
        m = CAT_XTE.findall(t)
        if m:
            vp3[f] = len(m)
    dat("Q2", not vp2, f"{len(vp2)} tep con chep tay bieu thuc quan the"
        + (": " + ", ".join(f"{k}={v}" for k, v in sorted(vp2.items())) if vp2 else ""))
    dat("Q3", not vp3, f"{len(vp3)} tep con cat Xte[:N] de lay quan the"
        + (": " + ", ".join(f"{k}={v}" for k, v in sorted(vp3.items())) if vp3 else ""))

    # Q4 la cong KHAI BAO, khong phai cong bang nhau. Hai quan the KHAC nhau co the
    # dung: trong exp_trust.py, P2 hoi "ba cach giai thich CUNG mot mo hinh co dong y
    # nhau khong" nen quan the la flow mo hinh AY bao dong; P3 hoi "bon mo hinh tuong
    # duong co giai thich giong nhau khong" nen quan the phai la flow MOI BON cung
    # bao dong - va day dong thoi la cach sua diem 2(e) cua doc ngoai: mot phan
    # "bat dong giai thich" truoc day thuc ra la bat dong QUYET DINH.
    # Nen Q4 khong doi hai quan the bang nhau; no doi moi quan the PHAI den tu
    # `flow_bao_dong`, hoac duoc chon mot lan o chO GOI roi truyen vao.
    lech = []
    for f in cac_tep():
        t = open(os.path.join(MA, f), encoding="utf-8").read()
        than = {}
        for m in re.finditer(r"^def\s+(\w+)\s*\(([^)]*)\).*?(?=^def |\Z)", t, re.M | re.S):
            than[m.group(1)] = (m.group(2), m.group(0))
        p2 = [k for k in than if "p2" in k.lower()]
        p3 = [k for k in than if "p3" in k.lower()]
        if not (p2 and p3):
            continue
        for ten in p2 + p3:
            doi_so, body = than[ten]
            if TEN_HAM in body:
                continue                                   # tu goi ham chung
            if re.search(r"\b(Xm|sub|Xtp)\b", doi_so):
                continue                                   # nhan quan the tu cho goi
            lech.append(f"{f}::{ten} khong lay quan the tu `{TEN_HAM}` va cung "
                        f"khong nhan san (doi so: {doi_so.strip()[:40]})")
    dat("Q4", not lech, f"ham P2/P3 khong khai duoc nguon quan the: {len(lech)}"
        + ("; " + "; ".join(lech) if lech else ""))

    # ⛔⛔ Q5. Q1..Q4 deu XANH ngay 10/11/2026 trong khi HAI script VO: chung chi
    # kiem rang bieu thuc chep-tay da BIEN MAT, khong kiem rang thu thay vao la DUNG.
    # `flow_bao_dong` tra ve CHI SO; noi nao con dung ket qua nhu MAT NA (`tp & ...`,
    # `tp.sum()`, `~tp`) thi phai goi voi `mat_na=True`, khong thi `&` thanh phep AND
    # BIT tren so nguyen va nem ValueError ve hinh dang.
    # Mot cong kiem "da xoa cai cu" ma khong kiem "cai moi dung" la mot cong nua voi.
    # ⇒ [[feedback-cong-bat-sai-khong-bat-thieu]]
    sai_kieu, n_soi = [], 0
    for f in cac_tep():
        t = open(os.path.join(MA, f), encoding="utf-8").read()
        for m in re.finditer(r"^(\s*)(\w+)\s*=\s*" + TEN_HAM + r"\(([^\n]*)\)\s*(?:#[^\n]*)?$",
                             t, re.M):
            bien, doi_so = m.group(2), m.group(3)
            n_soi += 1
            la_mat_na = "mat_na=True" in doi_so
            # ⛔⛔ 10/11/2026 cua so soi tung la `sau.split("\n\n")[0]`, tuc chi tới
            # DONG TRONG dau tien. Trong exp_harm.py phep gan o dong 51 va
            # `int(tp.sum())` o dong 65, cach nhau mot dong trong, nen Q5 KHONG THAY
            # va bao xanh trong khi `n_true_attacks` ra 47012435 thay vi 7851: tong
            # cac chi so, khong phai so dem. Tam nhin cua cong phai bang tam SONG cua
            # bien, tuc het HAM chua no, khong phai het doan van.
            # ⇒ [[feedback-cong-kiem-ten-thay-vi-ban-chat]]
            truoc = t[:m.start()]
            dinh = list(re.finditer(r"(?m)^(\s*)def\s", truoc))
            thut_def = len(dinh[-1].group(1)) if dinh else -1
            dong_sau = t[m.end():].split("\n")
            giu = []
            for d in dong_sau:
                if d.strip() == "":
                    giu.append(d); continue
                if len(d) - len(d.lstrip()) <= thut_def:
                    break
                giu.append(d)
            khoi = "\n".join(giu)
            dung_mat_na = bool(re.search(r"\b" + bien + r"\s*[&|]|\b" + bien + r"\.sum\(\)|~\s*"
                                         + bien + r"\b", khoi))
            if dung_mat_na and not la_mat_na:
                sai_kieu.append(f"{f}: `{bien}` dung nhu MAT NA nhung goi khong co mat_na=True")
            if la_mat_na and re.search(r"\b" + bien + r"\s*\[", khoi):
                sai_kieu.append(f"{f}: `{bien}` la mat na nhung bi index truc tiep")
    # ⛔ Dem ca so cho DA SOI, kheo "0 cho sai" khong phan biet duoc "soi het va
    # sach" voi "khong soi duoc cho nao". ⇒ [[feedback-kiem-0-don-vi-khong-phai-sach]]
    td5 = f"soi {n_soi} cho goi `{TEN_HAM}` gan vao bien; {len(sai_kieu)} cho sai kieu"
    if sai_kieu:
        td5 += ": " + "; ".join(sai_kieu)
    dat("Q5", not sai_kieu and n_soi > 0, td5
        + ("; ⛔ SOI 0 CHO, khong ket luan duoc gi" if n_soi == 0 else ""))

    if loi:
        sys.exit(f"\n{len(loi)}/{len(da_cham)} cong DO: "
                 + ", ".join(d.split()[0] for d in loi))
    print(f"\n  => {len(da_cham)}/{len(da_cham)} cong XANH")


if __name__ == "__main__":
    main()
