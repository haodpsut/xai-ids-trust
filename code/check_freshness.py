#!/usr/bin/env python3
"""Freshness cua project: moi CSV phai MOI HON producer cua no, va moi hon data.py.

Vi sao co ban rieng thay vi de sweep dung --auto: --auto suy producer tu ten file, va o day suy
sai 18/19 lan roi BLOCK -- mot cong bao DANGEROUS gia tren mot bai hoan toan dung. Bang duoi day
khai tuong minh, doc ra tu chinh cac script (moi exp_*.py deu ghi duong dan results/<ten>.csv).

Ngoai producer rieng, MOI CSV con phu thuoc data.py (moi exp_*.py deu `import data`). CSV cu hon
data.py duoc bao STALE-DEP va KHONG tu dong BLOCK: mot thay doi THUAN CONG THEM vao data.py
(them mot nhanh dataset moi) khong lam hong ket qua cu. Ca 10/08/2026: data.py them nhanh TON-IoT
roi CIC-IoT-2023, duong nap UNSW/CICIDS/5G-NIDD khong doi mot dong -- 11 claim sinh truoc do van
hop le. Nguoi doc phai xac nhan bang `git diff code/data.py`, va cong in ra de bat ho lam viec do.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")

MAP = {
    "ablate_p2k.csv": "exp_ablate_p2p3.py",
    "ablate_p3E.csv": "exp_ablate_p2p3.py",
    "attack.csv": "exp_attack.py",
    "breadth.csv": "exp_breadth.py",
    "ceiling.csv": "exp_ceiling.py",
    "defense.csv": "exp_defense.py",
    "defense_ablate.csv": "exp_defense_ablate.py",
    "defense_transfer.csv": "exp_defense_transfer.py",
    "faith_5explainer.csv": "exp_faith_5explainer.py",
    "faithfulness.csv": "exp_faithfulness.py",
    "field_audit.csv": "field_audit.py",
    "fidelity_multi.csv": "exp_fidelity_multi.py",
    "gate_attack.csv": "exp_gate_attack.py",
    "harm.csv": "exp_harm.py",
    "harm_bytype.csv": "exp_harm_bytype.py",
    "multiseed.csv": "exp_multiseed.py",
    "redundancy.csv": "exp_redundancy.py",
    "tree.csv": "exp_tree.py",
    "trust.csv": "exp_trust.py",
}
SHARED = ["data.py"]


def mt(p):
    return os.path.getmtime(p) if os.path.exists(p) else None


def main():
    bad, dep, ok = [], [], 0
    for csv, script in sorted(MAP.items()):
        c = mt(os.path.join(RES, csv))
        s = mt(os.path.join(HERE, script))
        if c is None:
            bad.append("{:34s} THIEU FILE".format(csv))
            continue
        if s is None:
            bad.append("{:34s} thieu producer {}".format(csv, script))
            continue
        if c < s:
            bad.append("{:34s} cu hon {} ({:.0f} phut)".format(csv, script, (s - c) / 60))
            continue
        hit = False
        for sh in SHARED:
            t = mt(os.path.join(HERE, sh))
            if t and c < t:
                dep.append("{:34s} cu hon {} ({:.0f} phut)".format(csv, sh, (t - c) / 60))
                hit = True
                break
        if not hit:
            ok += 1
    for e in sorted(f for f in os.listdir(RES) if f.endswith(".csv") and f not in MAP):
        bad.append("{:34s} KHONG khai producer".format(e))

    for b in bad:
        print("STALE     " + b)
    for d in dep:
        print("STALE-DEP " + d)
    print()
    print("FRESH: {}/{} CSV moi hon producer VA moi hon data.py".format(ok, len(MAP)))
    if dep:
        print("{} CSV cu hon data.py. Xac nhan bang `git diff code/data.py`: neu thay doi la"
              .format(len(dep)))
        print("THUAN CONG THEM (them nhanh dataset moi) thi ket qua cu VAN HOP LE.")
        print("Ghi nhan 10/08/2026: da xac nhan, thuan cong them. Xem paper/paper-flow-state.md.")
    if bad:
        print("BLOCK: {} CSV that su oi hoac khong khai producer.".format(len(bad)))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
