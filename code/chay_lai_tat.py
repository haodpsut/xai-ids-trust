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
    chi = [a for a in sys.argv[1:] if not a.startswith("-")]
    bd = ban_do()
    scripts = sorted(set(bd.values()))
    if chi:
        scripts = [s for s in scripts if any(c in s for c in chi)]
    print(f"######## BAT DAU {time.strftime('%Y-%m-%dT%H:%M:%S')} ########")
    print(f"  {len(bd)} CSV, {len(scripts)} script sinh")
    print(f"  python: {sys.version.split()[0]}")

    chup = RES + ".CHUP-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copytree(RES, chup)
    truoc = {f: bam(os.path.join(chup, f)) for f in sorted(os.listdir(chup))
             if f.endswith(".csv")}
    print(f"  da chup {len(truoc)} CSV ra {os.path.basename(chup)}\n")

    mt = dict(os.environ)
    mt["CUDA_VISIBLE_DEVICES"] = ""          # ⛔ xem docstring
    mt["PYTHONHASHSEED"] = "0"

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

    # ⛔ Phuc hoi ban chup du ket qua the nao: cay lam viec khong duoc doi.
    for f in os.listdir(RES):
        if f.endswith(".csv"):
            os.remove(os.path.join(RES, f))
    for f in os.listdir(chup):
        shutil.copy2(os.path.join(chup, f), os.path.join(RES, f))
    sau = {f: bam(os.path.join(RES, f)) for f in sorted(os.listdir(RES))
           if f.endswith(".csv")}
    assert sau == truoc, "⛔ KHONG PHUC HOI DUOC code/results/: dung dung tiep"
    shutil.rmtree(chup)
    print("     (da phuc hoi code/results/ nguyen ven, da doi chieu bam)")

    hong = [s for s, ma, _, _ in ket if ma != 0]
    print(f"\n######## XONG {time.strftime('%Y-%m-%dT%H:%M:%S')} ########")
    if hong or khac or mat:
        sys.exit(f"⛔ {len(hong)} script loi, {len(khac)} CSV khac, {len(mat)} CSV mat")
    print(f"  => {len(giong)}/{len(truoc)} CSV sinh lai GIONG TUNG BYTE, "
          f"{len(ket)} script chay sach")


if __name__ == "__main__":
    main()
