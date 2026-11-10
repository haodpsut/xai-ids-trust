"""Chay lai HAI LAN trong hai tien trinh moi va doi chieu: so phai GIONG TUNG BYTE.

⛔⛔ Vi sao co tep nay. Ngay 10/11/2026, hai luot `exp_attack.py` lien nhau tren
CUNG mot may, CUNG mot ma, cho `analyst_benign_before` = 0,037 roi 0,014. Nguyen
nhan: `train()` goi `torch.manual_seed(seed)` nhung mo hinh da duoc DUNG XONG o
phia goi, nen trong so khoi tao lay tu RNG toan cuc chua gieo; `torch.initial_seed()`
do duoc la mot so khac nhau moi tien trinh. Truoc do toi da quy 21/24 CSV khong tai
lap duoc cho kien truc CPU va BLAS va con DO rang ghim luong khong chua duoc gi.
Quy sai nguon vi chua bao gio chay HAI LAN TREN CUNG MOT MAY.
⇒ [[feedback-do-loi-cho-ban-va-chua-tach-nguon]] · [[feedback-cong-xanh-lan-dau-khong-chung-minh-gi]]

Mot bo cong doi chieu ba noi, doi chieu bai voi CSV, doi chieu bam, ma khong co cong
nao chay lai lan thu hai thi no chung minh **nhat quan**, khong chung minh **tai lap**.
⇒ [[feedback-closed-loop-gates]] · [[feedback-qa-xanh-vi-khong-thu-dung-lai]]

T1  cau truc: tham so mo hinh khong duoc khoi tao ngau nhien trong `__init__`, vi
    nhu the `gieo_lai()` khong cach nao dat lai duoc.
T2  cau truc: `train()` phai gieo lai TRUOC vong hoc, va `gieo_lai` phai NEM khi co
    tham so khong phu.
T3  cau truc: moi bo uoc luong sklearn co ngau nhien phai co `random_state`.
T4  THUC CHAY: N script re nhat, hai luot moi tien trinh, CSV phai giong tung byte.
"""
import functools, builtins
builtins.print = functools.partial(builtins.print, flush=True)

import filecmp, os, re, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")

# Script re nhat co sinh CSV tu mo hinh. Khong lay exp_tree/exp_multiseed vi 1500s.
THU = ["exp_jaccard_floor.py", "exp_dataset_profile.py", "exp_attack.py",
       "exp_harm_bytype.py"]

NGAU_NHIEN_SKLEARN = ("RandomForestClassifier", "ExtraTreesClassifier",
                      "GradientBoostingClassifier", "DecisionTreeClassifier",
                      "KMeans", "MiniBatchKMeans", "MLPClassifier", "TSNE",
                      "SGDClassifier", "RandomizedSearchCV")

loi, da_cham = [], []


def dat(ten, ok, td):
    da_cham.append(ten)
    print(f"  {'' if ok else '⛔ '}{ten} {td}")
    if not ok:
        loi.append(f"{ten} {td}")


def doc(f):
    return open(os.path.join(HERE, f), encoding="utf-8").read()


def main():
    tat = "--tat" in sys.argv
    thu = sorted(f for f in os.listdir(HERE)
                 if f.startswith("exp_") and f.endswith(".py")) if tat else THU

    # ── T1 ────────────────────────────────────────────────────────────────────
    h = doc("harness.py")
    xau = []
    for m in re.finditer(r"nn\.Parameter\(([^\n]*)\)", h):
        if re.search(r"\brandn?\b|\brand\(|normal_|uniform_|kaiming|xavier", m.group(1)):
            dong = h[:m.start()].count("\n") + 1
            xau.append(f"harness.py:{dong} `{m.group(0)[:48]}`")
    n_ts = len(re.findall(r"nn\.Parameter\(", h))
    dat("T1", not xau,
        f"soi {n_ts} `nn.Parameter(`; "
        f"{len(xau)} cho khoi tao ngau nhien trong `__init__`"
        + (("; ⛔ " + "; ".join(xau)) if xau else ""))

    # ── T2 ────────────────────────────────────────────────────────────────────
    than = re.search(r"def train\([^)]*\):\n((?:    .*\n|\n)+)", h)
    co_gieo = bool(than) and "gieo_lai(model, seed)" in than.group(1).split("for ")[0]
    g = re.search(r"def gieo_lai\([^)]*\):\n((?:    .*\n|\n)+)", h)
    co_nem = bool(g) and "raise RuntimeError" in g.group(1) and "manual_seed" in g.group(1)
    dat("T2", co_gieo and co_nem,
        f"`train` gieo lai truoc vong hoc: {'CO' if co_gieo else 'KHONG'}; "
        f"`gieo_lai` nem khi co tham so khong phu: {'CO' if co_nem else 'KHONG'}")

    # ── T3 ────────────────────────────────────────────────────────────────────
    thieu, n_bo = [], 0
    for f in sorted(x for x in os.listdir(HERE) if x.endswith(".py")):
        t = doc(f)
        for ten in NGAU_NHIEN_SKLEARN:
            for m in re.finditer(re.escape(ten) + r"\(", t):
                # lay tron doi so bang cach dem ngoac
                i, sau, d = m.end(), "", 1
                while i < len(t) and d:
                    d += (t[i] == "(") - (t[i] == ")")
                    sau += t[i]; i += 1
                n_bo += 1
                if "random_state" not in sau:
                    thieu.append(f"{f}:{t[:m.start()].count(chr(10)) + 1} {ten}")
    dat("T3", not thieu and n_bo > 0,
        f"soi {n_bo} bo uoc luong sklearn co ngau nhien; {len(thieu)} cho thieu "
        f"`random_state`" + (("; ⛔ " + "; ".join(thieu[:6])) if thieu else "")
        + ("; ⛔ SOI 0 BO, khong ket luan duoc gi" if n_bo == 0 else ""))

    # ── T4: thuc chay ─────────────────────────────────────────────────────────
    # ⛔ Chup results/ ra ngoai TRUOC, phuc hoi du ket qua the nao: mot cong tu kiem
    # khong duoc de lai hien vat nua cu nua moi. ⇒ [[feedback-tu-kiem-ghi-de-phai-nguyen-tu]]
    import importlib.util
    sp = importlib.util.spec_from_file_location("_cf", os.path.join(HERE, "check_freshness.py"))
    cf = importlib.util.module_from_spec(sp); sp.loader.exec_module(cf)
    # ⛔ MAP la {csv: script} va MOT script co the sinh NHIEU CSV (exp_ablate_p2p3
    # sinh 2). Dao chieu bang dict comprehension thi mat bot CSV va cong se doi
    # chieu THIEU ma van bao xanh. ⇒ [[feedback-cong-bat-sai-khong-bat-thieu]]
    bd = {}
    for csv, sc in cf.MAP.items():
        bd.setdefault(sc, []).append(csv)

    tam = tempfile.mkdtemp(prefix="tiendinh-")
    chup = os.path.join(tam, "chup")
    shutil.copytree(RES, chup)
    # ⛔ Phai ghim luong GIONG chay_lai_tat.py, khong thi cong nay do mot moi truong
    # va bo so cua bai sinh ra trong moi truong khac. Doc truc tiep tu tep ay de
    # khong co HAI con so. ⇒ [[feedback-hai-duong-ong-so-phu-noi-vao-mot]]
    import importlib.util as _iu
    _sp = _iu.spec_from_file_location("_clt", os.path.join(HERE, "chay_lai_tat.py"))
    _m = _iu.module_from_spec(_sp); _sp.loader.exec_module(_m)
    mt = dict(os.environ, CUDA_VISIBLE_DEVICES="", PYTHONHASHSEED="0")
    for _k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
               "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
        mt[_k] = str(_m.LUONG)
    khac, chay, bo_qua = [], 0, []
    try:
        for s in thu:
            cs = sorted(bd.get(s, []))
            if not cs:
                bo_qua.append(s); continue
            ra = {}
            for luot in (1, 2):
                r = subprocess.run([sys.executable, s], cwd=HERE, env=mt,
                                   capture_output=True, text=True)
                if r.returncode != 0:
                    khac.append(f"{s} luot {luot} MA THOAT {r.returncode}: "
                                + (r.stderr.strip().split(chr(10))[-1][:90]))
                    break
                for c in cs:
                    d = os.path.join(tam, f"{c}.{luot}")
                    shutil.copyfile(os.path.join(RES, c), d)
                    ra.setdefault(c, []).append(d)
            else:
                chay += 1
                for c in cs:
                    if not filecmp.cmp(ra[c][0], ra[c][1], shallow=False):
                        khac.append(f"{c} HAI LUOT KHAC NHAU")
    finally:
        for f in os.listdir(chup):
            shutil.copyfile(os.path.join(chup, f), os.path.join(RES, f))
        shutil.rmtree(tam, ignore_errors=True)

    dat("T4", not khac and chay > 0,
        f"chay lai {chay} script x2 luot ({sum(len(bd.get(s, [])) for s in thu)} CSV), "
        f"moi luot mot tien trinh moi; "
        f"{len(khac)} script khong tai lap"
        + (("; ⛔ " + "; ".join(khac)) if khac else "")
        + (f"; bo qua {bo_qua} (khong biet CSV dau ra)" if bo_qua else "")
        + ("; ⛔ CHAY 0 SCRIPT, khong ket luan duoc gi" if chay == 0 else ""))

    if loi:
        sys.exit(f"\n{len(loi)}/{len(da_cham)} cong DO: "
                 + ", ".join(d.split()[0] for d in loi))
    print(f"\n  => {len(da_cham)}/{len(da_cham)} cong XANH")


if __name__ == "__main__":
    main()
