"""Chay lai MOI thi nghiem va doi chieu tung CSV voi ban dang trong kho.

Day la chieu dong bo manh nhat: cong_dong_bo.py chung minh ba noi giong nhau, va
cong_bang_tu_csv.py chung minh so trong ban thao bang so trong CSV; con tep nay
chung minh **CSV that su la dau ra cua MA**, khong phai mot hien vat da roi khoi
duong ong tu bao gio. Khong co phep nay thi ca chuoi chi chung minh NHAT QUAN noi bo.
⇒ [[feedback-closed-loop-gates]] · [[feedback-qa-xanh-vi-khong-thu-dung-lai]]

⛔ An toan: chup `code/results/` ra ban sao TRUOC khi chay, doi chieu voi ban sao,
roi PHUC HOI ban sao du ket qua the nao. Nen cay lam viec khong bi doi, va mot lan
chay lai that bai nua duong khong de lai mot thu muc results nua cu nua moi.
⇒ [[feedback-tu-kiem-ghi-de-phai-nguyen-tu]]

⛔ Ep CPU bang CUDA_VISIBLE_DEVICES="": moi so trong bai sinh ra tren may KHONG co
CUDA (Mac), va bai tu khai "no GPU is required". Chay tren GPU la doi moi truong,
tuc doi dieu kien cua phep so. Them nua, hai GPU cua sol1 dang co nguoi dung.
⇒ [[feedback-moi-truong-chay-la-phan-cua-hien-vat]]
"""
# ⛔ Dong nay phai nam TRUOC moi lenh print. Khong co no thi Python DEM KHOI khi
# dau ra khong phai terminal, nen mot luot chay dai (do duoc: >61 phut) co log RONG
# suot thoi gian ay va khong ai biet no dang o script nao. Mot cong cu chay lau ma
# khong quan sat duoc thi khong phan biet duoc "dang chay" voi "treo".
import functools
import builtins
builtins.print = functools.partial(builtins.print, flush=True)

import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")

# So luong ghim cho moi lan chay. Bai PHAI khai dung con so nay.
LUONG = 40

# CSV -> script sinh ra no. Doc ra tu check_freshness.py de khong co BAN KE THU HAI.
def ban_do():
    import importlib.util
    p = os.path.join(HERE, "check_freshness.py")
    sp = importlib.util.spec_from_file_location("_cf", p)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return dict(m.MAP)


def bam(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    # ⛔ `--nhan`: GIU so moi thay vi phuc hoi ban chup. Chi dung khi da CO Y doi
    # cach do (vi du sua quan the flow, them nhieu seed) va muon nhan so moi lam so
    # cua bai. Mac dinh la KHONG nhan, vi cong cu nay truoc het la mot CONG DOI
    # CHIEU; mot cong tu y ghi len hien vat that la mot cong nguy hiem.
    nhan = "--nhan" in sys.argv
    chi = [a for a in sys.argv[1:] if not a.startswith("-")]
    bd = ban_do()
    scripts = sorted(set(bd.values()))
    if chi:
        scripts = [s for s in scripts if any(c in s for c in chi)]
    print(f"######## BAT DAU {time.strftime('%Y-%m-%dT%H:%M:%S')} ########")
    print(f"  {len(bd)} CSV, {len(scripts)} script sinh")
    print(f"  python: {sys.version.split()[0]}")
    print(f"  luong ghim: {LUONG} (OMP/MKL/OPENBLAS/VECLIB/NUMEXPR)")
    try:
        import torch as _t
        print(f"  torch: {_t.__version__}, luong torch mac dinh {_t.get_num_threads()}")
    except Exception as _e:
        print(f"  torch: khong nap duoc ({_e})")

    chup = RES + ".CHUP-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copytree(RES, chup)
    truoc = {f: bam(os.path.join(chup, f)) for f in sorted(os.listdir(chup))
             if f.endswith(".csv")}
    print(f"  da chup {len(truoc)} CSV ra {os.path.basename(chup)}\n")

    mt = dict(os.environ)
    mt["CUDA_VISIBLE_DEVICES"] = ""          # ⛔ xem docstring
    mt["PYTHONHASHSEED"] = "0"
    # ⛔⛔ So LUONG quyet dinh THU TU THU GON cua phep cong so thuc, nen no la PHAN
    # cua hien vat y nhu bao nhieu epoch. De mac dinh thi torch lay nua so nhan may
    # (sol1: 40 trong 80), tuc con so cua bai phu thuoc mot thong so KHONG AI KHAI.
    # Ghim thanh hang so co ten de bai khai duoc, va de doi may khong am tham doi so.
    # ⇒ [[feedback-moi-truong-chay-la-phan-cua-hien-vat]] · [[feedback-khai-may-chay-truoc-khi-bao-so]]
    for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
              "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
        mt[k] = str(LUONG)

    ket = []
    for s in scripts:
        t0 = time.time()
        r = subprocess.run([sys.executable, s], cwd=HERE, env=mt,
                           capture_output=True, text=True)
        dt = time.time() - t0
        ket.append((s, r.returncode, dt, (r.stderr or r.stdout).strip().splitlines()[-1][:90]
                    if r.returncode else ""))
        print(f"  {'✅' if r.returncode == 0 else '⛔'} {s:28s} {dt:7.1f}s"
              + (f"  {ket[-1][3]}" if r.returncode else ""))

    print("\n  ── doi chieu tung CSV voi ban chup ──")
    giong, khac, mat, moi = [], [], [], []
    for f, b in truoc.items():
        p = os.path.join(RES, f)
        if not os.path.exists(p):
            mat.append(f)
        elif bam(p) == b:
            giong.append(f)
        else:
            khac.append(f)
    for f in sorted(os.listdir(RES)):
        if f.endswith(".csv") and f not in truoc:
            moi.append(f)
    for f in khac:
        print(f"     ⛔ KHAC: {f}")
    for f in mat:
        print(f"     ⛔ MAT:  {f}")
    for f in moi:
        print(f"     ⚠ MOI:  {f}")
    print(f"     giong {len(giong)}/{len(truoc)}")

    # ⛔⛔ Da xay ra ngay 10/11/2026: `--nhan` NHAN so moi trong khi HAI script nem
    # ngoai le, nen `code/results/` thanh 12 tep MOI lan 12 tep CU. Dung cai ma
    # docstring cua tep nay tu nhan la ngan duoc. Mot che do "nhan" phai doi TOAN BO
    # dieu kien dung, kheo no bien mot lan chay that bai thanh mot hien vat nua doi.
    # ⇒ [[feedback-tu-kiem-ghi-de-phai-nguyen-tu]] · [[feedback-ca-tiem-sua-nua-tao-trang-thai-sai-khac]]
    hong_som = [x for x, ma, _, _ in ket if ma != 0]
    if nhan and (hong_som or mat):
        print(f"\n  ⛔ KHONG NHAN: {len(hong_som)} script loi"
              + (f" ({', '.join(hong_som)})" if hong_som else "")
              + (f", {len(mat)} CSV mat" if mat else "")
              + ". Phuc hoi ban chup.")
        nhan = False

    if nhan:
        # Ghi mot BAN GHI delta canh ban chup, roi GIU ban chup lai: no la bang
        # chung ve so CU, va khong co no thi khong ai dung lai duoc phep so nay.
        bg = os.path.join(chup, "DELTA.tsv")
        with open(bg, "w", encoding="utf-8") as fp:
            fp.write("tep\tcot\tkhoa\tcu\tmoi\n")
            import csv as _c
            for f in sorted(khac):
                try:
                    a = list(_c.DictReader(open(os.path.join(chup, f), encoding="utf-8")))
                    b = list(_c.DictReader(open(os.path.join(RES, f), encoding="utf-8")))
                except Exception:
                    continue
                k0 = (list(a[0].keys()) or [""])[0] if a else ""
                for ra, rb in zip(a, b):
                    for c in ra:
                        if ra[c] != rb.get(c):
                            fp.write(f"{f}\t{c}\t{ra.get(k0,'')}\t{ra[c]}\t{rb.get(c)}\n")
        n_dong = sum(1 for _ in open(bg, encoding="utf-8")) - 1
        print(f"     ⚠ DA NHAN so moi. Ban chup CU giu lai o {os.path.basename(chup)}/")
        print(f"       ban ghi delta: {os.path.basename(chup)}/DELTA.tsv, {n_dong} o doi")
    else:
        # ⛔⛔ GIU BAN LECH TRUOC KHI PHUC HOI. Ngay 11/11/2026 luot doi chieu bao
        # `harm_bytype.csv` KHAC, roi khoi nay phuc hoi ban chup va `rmtree` ban
        # chup, nen ban LECH bi xoa. Tam luot chay sau do deu giong het nhau, va
        # ket qua la toi co mot bang chung ve bat tai lap ma KHONG CON HIEN VAT de
        # diff: khong biet o nao doi, khong biet hang nao mat. Mot phep doi chieu
        # ma XOA chung cu cua chinh no thi lan sau cung bo tay y nhu lan nay.
        # ⇒ [[feedback-thu-hoach-truoc-khi-giet]] · [[feedback-log-tho-la-du-lieu]]
        if khac or mat:
            lech = chup + ".LECH"
            os.makedirs(lech, exist_ok=True)
            for f in khac:
                shutil.copy2(os.path.join(RES, f), os.path.join(lech, f))
            with open(os.path.join(lech, "DOC-TRUOC.txt"), "w", encoding="utf-8") as fh:
                fh.write("Ban SINH LAI cua cac CSV khac voi ban chup, giu lai de diff.\n"
                         f"Ban chup (ban GOC) o: {os.path.basename(chup)}/\n"
                         f"Thoi diem: {time.strftime('%Y-%m-%dT%H:%M:%S')}\n"
                         f"CSV khac: {khac}\nCSV mat: {mat}\n")
            print(f"     ⚠ da GIU {len(khac)} ban lech o {os.path.basename(lech)}/ "
                  f"de diff; ban chup goc KHONG bi xoa")

        for f in os.listdir(RES):
            if f.endswith(".csv"):
                os.remove(os.path.join(RES, f))
        for f in os.listdir(chup):
            if f.endswith(".csv"):
                shutil.copy2(os.path.join(chup, f), os.path.join(RES, f))
        sau = {f: bam(os.path.join(RES, f)) for f in sorted(os.listdir(RES))
               if f.endswith(".csv")}
        assert sau == truoc, "⛔ KHONG PHUC HOI DUOC code/results/: dung dung tiep"
        if khac or mat:
            print(f"     (da phuc hoi code/results/ nguyen ven; GIU LAI "
                  f"{os.path.basename(chup)}/ vi co CSV lech)")
        else:
            shutil.rmtree(chup)
            print("     (da phuc hoi code/results/ nguyen ven, da doi chieu bam)")

    hong = [s for s, ma, _, _ in ket if ma != 0]
    print(f"\n######## XONG {time.strftime('%Y-%m-%dT%H:%M:%S')} ########")
    if nhan and not hong and not mat:
        print(f"  => DA NHAN: {len(khac)} CSV doi, {len(giong)} giu nguyen, "
              f"{len(ket)} script chay sach")
        return
    if hong or khac or mat:
        sys.exit(f"⛔ {len(hong)} script loi, {len(khac)} CSV khac, {len(mat)} CSV mat")
    print(f"  => {len(giong)}/{len(truoc)} CSV sinh lai GIONG TUNG BYTE, "
          f"{len(ket)} script chay sach")


if __name__ == "__main__":
    main()
