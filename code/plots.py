"""House-style figure for the CSF paper: the three necessary properties of interpretability-based
trust, each shown failing across three modern NIDS datasets. agentra_plot, print-ready gated."""
import csv, os, sys
import numpy as np

# The default is the copy vendored in this repository, so a clean clone can rebuild the
# figures. Before this, the default was a path outside the repository and `plots.py` raised
# ModuleNotFoundError for everyone but the author, while the paper promised otherwise.
# Set AGENTRA_PLOT_ASSETS to render against a different copy of the module.
ASSETS = os.environ.get("AGENTRA_PLOT_ASSETS", os.path.join(
    os.path.dirname(__file__), "vendor", "plot-assets"))
sys.path.insert(0, os.path.abspath(ASSETS))
import agentra_plot as ap  # noqa: E402
import matplotlib  # noqa: E402

# ⛔⛔ GHIM backend. Khong ghim thi hinh sinh o may co man hinh (backend MacOSX) va
# hinh sinh trong cong (ep Agg) khac nhau TUNG DIEM ANH du cung du lieu, va
# `cong_hinh.py` bao MOI hinh deu cu. Backend la mot phan cua hien vat.
# ⇒ [[feedback-moi-truong-chay-la-phan-cua-hien-vat]]
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def phong_that():
    """In ra PHONG THAT se duoc dung, vi matplotlib tut phong trong IM LANG.

    ⛔⛔⛔ Bat duoc 13/11/2026 khi chay cong tren sol1. Bo style nha doi
    `font.serif: Times New Roman, DejaVu Serif`. Mac CO Times New Roman, sol1 thi
    KHONG, nen sol1 ve bang DejaVu Serif. Hinh trong bai DA NOP nhung
    `TimesNewRomanPSMT` (do bang `pdffonts`), tuc hinh ay ve tren Mac va KHONG dung
    lai duoc tren chinh may ma bai khai la moi truong chay.

    Matplotlib KHONG in mot dong canh bao nao cho lan tut ay: da thu `-W all`, 0
    dong. Nen F1 cua `cong_hinh.py` bao do voi loi "CU (khac ban vua ve)", doc nhu
    la hinh cu, va nguoi doc se di tim sai cho hoan toan.

    Ghim backend da duoc lam tu truoc vi dung ly do nay. PHONG cung la phan cua
    hien vat y het backend, va no bi bo sot.
    ⇒ [[feedback-moi-truong-chay-la-phan-cua-hien-vat]]
    ⇒ [[feedback-khai-may-chay-truoc-khi-bao-so]]
    """
    from matplotlib import font_manager as fm
    muon = [x.strip() for x in plt.rcParams.get("font.serif", []) if x.strip()]
    if not muon:
        return None
    co = {f.name for f in fm.fontManager.ttflist}
    that = next((x for x in muon if x in co), None)
    if that != muon[0]:
        print(f"  ⛔ PHONG TUT: style doi {muon[0]!r} nhung may nay KHONG co; "
              f"se ve bang {that!r}. Hinh ve ra se KHAC hinh trong bai, va khac o "
              f"chu chu khong o so. Day la mot khac biet MOI TRUONG, khong phai "
              f"hinh cu.")
    else:
        print(f"  phong: {that!r} (dung cai style doi, khong tut)")
    return that

def hai_chu_so(v):
    """Round half up, exactly as the paper's tables do.

    This used to be f"{v:.2f}". Python rounds the binary value, so 0.745 prints as
    "0.74", while the tables (Decimal, ROUND_HALF_UP) print 0.75. The figure and the
    table read the same breadth.csv yet disagreed in 8 of 50 cells. Each was correct
    under its own rule; the defect was having two rules for one number.
    """
    from decimal import Decimal, ROUND_HALF_UP
    return str(Decimal(repr(float(v))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


ap.use_style()
HERE = os.path.dirname(__file__)
# `XAI_FIG_OUT` cho `cong_hinh.py` dung lai toan bo hinh vao thu muc tam roi so voi
# ban dang nam trong bai, ma khong dam vao ban that. Khong co bien nay thi ghi dung cho.
FIG = os.path.abspath(os.environ.get("XAI_FIG_OUT",
                                     os.path.join(HERE, "..", "paper", "figs")))
os.makedirs(FIG, exist_ok=True)

# ⛔⛔ So ghi cua hinh. Ngay 11/11/2026 doc ngoai vong 2 bat duoc Hinh 2 va Bang 4 in
# HAI con so khac nhau cho cung mot tinh chat (TON P2: 0,379 vs 0,468), vi hinh doc
# `trust.csv` con bang doc `multiseed.csv`. Khong cong nao thay, vi khong cong nao doc
# duoc thu mot hinh VE RA. Nay moi hinh ghi lai tung so cung XUAT XU vao
# `code/_fig-values.csv`, va `cong_hinh.py` doi chieu no voi kho claim cua bang.
# ⇒ [[feedback-doi-hien-vat-cho-may-doc-duoc]] · [[feedback-cong-khong-so-hai-nguon]]
SO_GHI = []


def ve_so(hinh, nhan, tap, gt, nguon_csv, cot):
    """Ghi lai mot con so hinh thuc su ve ra, kem tep va cot no den tu."""
    SO_GHI.append(dict(hinh=hinh, nhan=nhan, dataset=tap, gia_tri=f"{float(gt):.6f}",
                       nguon_csv=nguon_csv, cot=cot))
    return float(gt)


SHORT = {"5G-NIDD": "5G", "TON-IoT": "TON", "CIC-IoT-2023": "CIC23"}      # compact x-tick labels
def sl(ds):
    return [SHORT.get(k, k) for k in ds]


def row(tep="trust.csv"):
    with open(os.path.join(HERE, "results", tep)) as f:
        return {r["dataset"]: r for r in csv.DictReader(f)}


def fig_trust():
    # ⛔⛔ DOC `multiseed.csv`, DUNG ba cot ma Bang 4 doc. Truoc 11/11/2026 ham nay doc
    # `trust.csv` (mot hat, va P2 la trung binh ba cap TRONG HO gradient), nen hinh va
    # bang in hai con so khac nhau cho cung mot ten tinh chat: TON P2 0,379 vs 0,468,
    # 5G P3 0,620 vs 0,527. Moi con so phai co DUNG MOT cho o.
    # ⇒ [[feedback-so-headline-mot-cho-o]]
    d = row("multiseed.csv")
    ds = ["UNSW", "CICIDS", "5G-NIDD", "TON-IoT", "CIC-IoT-2023"]
    # Three panels: P1 fidelity retention, P2 method-agreement, P3 seed-agreement.
    # For a trust signal, each SHOULD be ~1.0 (perfect). We plot the achieved value vs the 1.0 line.
    p1, p2, p3 = [], [], []
    for k in ds:
        p1.append(1 - ve_so("fig_trust", "P1", k, d[k]["p1_fidelity_drop_mean"],
                            "multiseed.csv", "p1_fidelity_drop_mean"))
        p2.append(ve_so("fig_trust", "P2", k, d[k]["p2_method_agree_mean"],
                        "multiseed.csv", "p2_method_agree_mean"))
        p3.append(ve_so("fig_trust", "P3", k, d[k]["p3_seed_agree_mean"],
                        "multiseed.csv", "p3_seed_agree_mean"))
    labels = ["P1 fidelity\n(surrogate=model?)", "P2 determinacy\n(method-agnostic?)", "P3 groundedness\n(model-agnostic?)"]
    series = [p1, p2, p3]
    x = np.arange(len(labels)); w = 0.2
    styd = {"UNSW": (ap.INK, "///"), "CICIDS": (ap.WARM, "\\\\\\"), "5G-NIDD": (ap.AGREEN, "..."),
            "TON-IoT": (ap.GRAY, "xxx"), "CIC-IoT-2023": (ap.LIME, "++")}
    fig, ax = plt.subplots(figsize=(3.75, 2.7))
    for i, k in enumerate(ds):
        vals = [series[p][i] for p in range(3)]
        c, h = styd[k]
        ax.bar(x + (i - (len(ds) - 1) / 2) * w, vals, w, facecolor="white", edgecolor=c, linewidth=1.0, hatch=h, label=k)
    ax.axhline(1.0, color=ap.GRAY, ls=":", lw=0.9)
    ax.text(2.32, 1.01, "trust needs 1.0", fontsize=7, color=ap.GRAY, ha="right", va="bottom")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("agreement / retention"); ax.set_ylim(0, 1.12)
    ax.legend(fontsize=7, ncol=5, loc="lower center", bbox_to_anchor=(0.5, 1.02), columnspacing=0.8, handlelength=1.1, frameon=False)
    fig.tight_layout(rect=[0,0,1,0.93]); ap.save(fig, os.path.join(FIG, "fig_trust"))


def fig_fidelity():
    """Detection F1 the KAN-IDS gives up when its first layer is replaced by a cubic
    per-edge rendering, per dataset, mean and spread over seeds.

    ⛔⛔ Truoc 11/11/2026 ham nay ve HAI cot F1 doc tu `trust.csv` (MOT hat), trong
    khi Bang 5 in do TUT trung binh tren cac hat tu `multiseed.csv`. Hai cho noi ve
    cung mot thu ma lech nhau: TON-IoT tut 0,363 o hinh vs 0,599 o bang. Day la DUNG
    benh da chua cho `fig_trust`, nhung o day cong F3 khong phu toi vi hai ben ve
    danh nghia la hai dai luong khac (F1 vs do tut). Nay hinh ve DUNG dai luong cua
    bang, co thanh sai so, nen khong con hai con so cho mot ten.
    ⇒ [[feedback-so-headline-mot-cho-o]] · [[feedback-cong-cham-mot-hien-vat-khi-co-nhieu]]
    """
    d = row("multiseed.csv")
    ds = ["UNSW", "CICIDS", "5G-NIDD", "TON-IoT", "CIC-IoT-2023"]
    drop = [ve_so("fig_fidelity", "P1", k, d[k]["p1_fidelity_drop_mean"],
                  "multiseed.csv", "p1_fidelity_drop_mean") for k in ds]
    sd = [float(d[k]["p1_fidelity_drop_std"]) for k in ds]
    x = np.arange(len(ds))
    fig, ax = plt.subplots(figsize=(3.50, 2.45))
    ax.bar(x, drop, 0.52, facecolor="white", edgecolor=ap.WARM, linewidth=1.0, hatch="...")
    ax.errorbar(x, drop, yerr=sd, fmt="none", ecolor=ap.INK, elinewidth=0.8, capsize=2.5)
    ax.set_xticks(x); ax.set_xticklabels(sl(ds))
    ax.set_ylabel("detection $F_1$ given up")
    ax.set_ylim(0, max(a + b for a, b in zip(drop, sd)) * 1.25)
    ap.headline(ax, f"worst on {sl([ds[int(np.argmax(drop))]])[0]}", loc="upper right")
    fig.tight_layout(pad=0.9); ap.save(fig, os.path.join(FIG, "fig_fidelity"))


def fig_defense():
    """Reliability-gate detector AUC per dataset, full detector vs the OOD-only baseline:
    the gate predicts explanation reliability and is not reducible to out-of-distribution."""
    import os as _os
    with open(_os.path.join(HERE, "results", "defense_ablate.csv")) as f:
        d = {r["dataset"]: r for r in csv.DictReader(f)}
    ds = ["UNSW", "CICIDS", "5G-NIDD", "TON-IoT", "CIC-IoT-2023"]
    full = [float(d[k]["full_auc"]) for k in ds]
    ood = [float(d[k]["ood_only"]) for k in ds]
    x = np.arange(len(ds)); w = 0.36
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    ax.bar(x - w / 2, full, w, facecolor="white", edgecolor=ap.AGREEN, linewidth=1.0,
           hatch="///", label="full reliability gate")
    ax.bar(x + w / 2, ood, w, facecolor="white", edgecolor=ap.GRAY, linewidth=1.0,
           hatch="...", label="OOD-only baseline")
    ax.axhline(0.5, color=ap.WARM, ls=":", lw=0.9)
    ax.text(len(ds) - 0.6, 0.505, "chance", fontsize=7, color=ap.WARM, ha="right", va="bottom")
    ax.set_xticks(x); ax.set_xticklabels(sl(ds))
    ax.set_ylabel("reliability-detection AUC"); ax.set_ylim(0.4, 1.0)
    ax.legend(fontsize=7, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.02), frameon=False)
    fig.tight_layout(rect=[0,0,1,0.93]); ap.save(fig, os.path.join(FIG, "fig_defense"))


def fig_harm():
    """The security teeth: detection is stable (all models agree it's an attack), but the
    explanation-driven analyst action diverges, most on CICIDS. Uses the logistic auditor."""
    import os as _os
    with open(_os.path.join(HERE, "results", "harm.csv")) as f:
        rows = [r for r in csv.DictReader(f) if r["auditor"] == "logistic"]
    d = {r["dataset"]: r for r in rows}
    ds = ["UNSW", "CICIDS", "5G-NIDD", "TON-IoT", "CIC-IoT-2023"]
    detect = [float(d[k]["detection_agreement"]) for k in ds]
    diverge = [float(d[k]["action_divergence"]) for k in ds]
    x = np.arange(len(ds)); w = 0.36
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    ax.bar(x - w / 2, detect, w, facecolor="white", edgecolor=ap.INK, linewidth=1.0,
           hatch="///", label="detection agreement")
    ax.bar(x + w / 2, diverge, w, facecolor="white", edgecolor=ap.WARM, linewidth=1.0,
           hatch="...", label="action divergence")
    ax.set_xticks(x); ax.set_xticklabels(sl(ds))
    ax.set_ylabel("fraction of true attacks"); ax.set_ylim(0, 1.12)
    ax.legend(fontsize=7, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.02), frameon=False)
    fig.tight_layout(rect=[0, 0, 1, 0.93]); ap.save(fig, os.path.join(FIG, "fig_harm"))


def fig_pairwise_heat():
    """HEATMAP: top-5 agreement for all 10 explainer pairs x 3 datasets. Visualizes determinacy
    failure, most cells far below 1.0 (dark = agree, light = disagree)."""
    import os as _os
    from matplotlib.colors import LinearSegmentedColormap
    with open(_os.path.join(HERE, "results", "breadth.csv")) as f:
        d = {r["dataset"]: r for r in csv.DictReader(f)}
    pairs = ["grad_vs_ixg", "grad_vs_ig", "grad_vs_shap", "grad_vs_lime", "ixg_vs_ig",
             "ixg_vs_shap", "ixg_vs_lime", "ig_vs_shap", "ig_vs_lime", "shap_vs_lime"]
    plab = ["g-i", "g-ig", "g-s", "g-l", "i-ig", "i-s", "i-l", "ig-s", "ig-l", "s-l"]
    ds = ["UNSW", "CICIDS", "5G-NIDD", "TON-IoT", "CIC-IoT-2023"]
    M = np.array([[float(d[k][p]) for k in ds] for p in pairs])
    cmap = LinearSegmentedColormap.from_list("wag", ["#FFFFFF", ap.AGREEN])
    fig, ax = plt.subplots(figsize=(3.5, 3.4))
    im = ax.imshow(M, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(ds))); ax.set_xticklabels(sl(ds), fontsize=7)
    ax.set_yticks(range(len(pairs))); ax.set_yticklabels(plab, fontsize=7)
    ax.grid(False); ax.tick_params(length=0)
    for i in range(len(pairs)):
        for j in range(len(ds)):
            ax.text(j, i, hai_chu_so(M[i, j]), ha="center", va="center", fontsize=7,
                    color="white" if M[i, j] > 0.6 else ap.INK)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04); cb.ax.tick_params(labelsize=7, length=0)
    cb.set_label("top-5 agreement", fontsize=7)
    ax.set_ylabel("explainer pair", fontsize=8)
    fig.tight_layout(); ap.save(fig, os.path.join(FIG, "fig_pairwise_heat"))


def fig_robust():
    """LINE: determinacy vs top-k and groundedness vs ensemble size. Both stay flat/low ->
    failures are not artifacts of k or ensemble size."""
    import os as _os
    with open(_os.path.join(HERE, "results", "ablate_p2k.csv")) as f:
        k = {r["dataset"]: r for r in csv.DictReader(f)}
    with open(_os.path.join(HERE, "results", "ablate_p3E.csv")) as f:
        E = {r["dataset"]: r for r in csv.DictReader(f)}
    ds = ["UNSW", "CICIDS", "5G-NIDD", "TON-IoT", "CIC-IoT-2023"]
    styd = {"UNSW": (ap.INK, "o", "-"), "CICIDS": (ap.WARM, "s", "--"), "5G-NIDD": (ap.AGREEN, "^", "-."),
            "TON-IoT": (ap.GRAY, "D", ":"), "CIC-IoT-2023": (ap.LIME, "v", (0, (1, 1)))}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(3.5, 2.0), sharey=True)
    for dd in ds:
        c, m, ls = styd[dd]
        a1.plot([3, 5, 10], [float(k[dd][f"k{x}"]) for x in [3, 5, 10]], color=c, marker=m, ls=ls, ms=3, lw=1.1)
        a2.plot([4, 6, 10], [float(E[dd][f"E{x}"]) for x in [4, 6, 10]], color=c, marker=m, ls=ls, ms=3, lw=1.1, label=dd)
    a1.set_xlabel("top-$k$"); a1.set_ylabel("agreement"); a1.set_title("determinacy", fontsize=8)
    a2.set_xlabel("ensemble size"); a2.set_title("groundedness", fontsize=8)
    a1.set_ylim(0, 1); a1.axhline(1.0, color=ap.GRAY, ls=":", lw=0.8); a2.axhline(1.0, color=ap.GRAY, ls=":", lw=0.8)
    a2.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, 1.02), ncol=1, frameon=False)
    fig.tight_layout(); ap.save(fig, os.path.join(FIG, "fig_robust"))


def fig_harmtype():
    """HORIZONTAL BAR sorted: action divergence by attack type (CICIDS2017). High-volume DoS and
    port-scanning flows show the largest explanation-driven divergence."""
    import os as _os
    with open(_os.path.join(HERE, "results", "harm_bytype.csv")) as f:
        rows = [r for r in csv.DictReader(f) if r["dataset"] == "CICIDS"]
    rows.sort(key=lambda r: float(r["action_divergence"]))
    labs = [r["attack_type"] for r in rows]
    vals = [(ve_so("fig_harmtype", "action_divergence", "CICIDS:" + r["attack_type"],
                        r["action_divergence"], "harm_bytype.csv", "action_divergence"))
            for r in rows]
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    for i, v in enumerate(vals):
        c = ap.WARM if v >= 0.5 else ap.GRAY
        ax.barh(i, v, color="white", edgecolor=c, linewidth=1.0, hatch="///" if v >= 0.5 else "...")
    ax.set_yticks(range(len(labs))); ax.set_yticklabels(labs, fontsize=7)
    ax.set_xlabel("action divergence"); ax.set_xlim(0, 1.05)
    # ⛔⛔ Chu thich nay truoc day ghim cung chu "high-volume DoS and port scanning
    # worst". Du lieu doi thu tu (nay Brute Force dan dau) ma dong chu o nguyen, nen
    # hinh TU NOI NGUOC chinh cac cot cua no. Mot cau chu ve so lieu phai duoc SINH tu
    # so lieu. ⇒ [[feedback-bang-hinh-go-tay-khong-cap-nhat]]
    hai = [labs[-1], labs[-2]]
    ap.headline(ax, f"{hai[0]} and\n{hai[1]} worst", loc="lower right")
    fig.tight_layout(); ap.save(fig, os.path.join(FIG, "fig_harmtype"))


if __name__ == "__main__":
    phong_that()          # ⛔ in TRUOC khi ve: tut phong thi phai biet ngay
    fig_trust(); print("fig_trust ok")
    fig_fidelity(); print("fig_fidelity ok")
    fig_defense(); print("fig_defense ok")
    fig_harm(); print("fig_harm ok")
    fig_pairwise_heat(); print("fig_pairwise_heat ok")
    fig_robust(); print("fig_robust ok")
    fig_harmtype(); print("fig_harmtype ok")
    with open(os.path.join(HERE, "_fig-values.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(SO_GHI[0].keys()))
        w.writeheader(); w.writerows(SO_GHI)
    print(f"wrote code/_fig-values.csv ({len(SO_GHI)} so)")
