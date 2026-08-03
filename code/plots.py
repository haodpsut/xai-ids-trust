"""House-style figure for the CSF paper: the three necessary properties of interpretability-based
trust, each shown failing across three modern NIDS datasets. agentra_plot, print-ready gated."""
import csv, os, sys
import numpy as np

ASSETS = os.environ.get("AGENTRA_PLOT_ASSETS", os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "my-skills", "ALL-FIGURES",
    "0-SKILLS", "plot-figure-dph", "assets"))
sys.path.insert(0, os.path.abspath(ASSETS))
import agentra_plot as ap  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

ap.use_style()
HERE = os.path.dirname(__file__)
FIG = os.path.abspath(os.path.join(HERE, "..", "paper", "figs"))
os.makedirs(FIG, exist_ok=True)


def row():
    with open(os.path.join(HERE, "results", "trust.csv")) as f:
        return {r["dataset"]: r for r in csv.DictReader(f)}


def fig_trust():
    d = row()
    ds = ["UNSW", "CICIDS", "5G-NIDD"]
    # Three panels: P1 fidelity retention, P2 method-agreement, P3 seed-agreement.
    # For a trust signal, each SHOULD be ~1.0 (perfect). We plot the achieved value vs the 1.0 line.
    p1 = [1 - float(d[k]["fidelity_drop"]) for k in ds]       # fidelity retention of interpretable form
    p2 = [(float(d[k]["p2_grad_vs_ixg"]) + float(d[k]["p2_grad_vs_ig"]) + float(d[k]["p2_ixg_vs_ig"])) / 3 for k in ds]
    p3 = [float(d[k]["p3_topk_jaccard"]) for k in ds]
    labels = ["P1 fidelity\n(surrogate=model?)", "P2 determinacy\n(method-agnostic?)", "P3 groundedness\n(model-agnostic?)"]
    series = [p1, p2, p3]
    x = np.arange(len(labels)); w = 0.24
    styd = {"UNSW": (ap.INK, "///"), "CICIDS": (ap.WARM, "\\\\\\"), "5G-NIDD": (ap.AGREEN, "...")}
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    for i, k in enumerate(ds):
        vals = [series[p][i] for p in range(3)]
        c, h = styd[k]
        ax.bar(x + (i - 1) * w, vals, w, facecolor="white", edgecolor=c, linewidth=1.0, hatch=h, label=k)
    ax.axhline(1.0, color=ap.GRAY, ls=":", lw=0.9)
    ax.text(2.32, 1.01, "trust needs 1.0", fontsize=7, color=ap.GRAY, ha="right", va="bottom")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("agreement / retention"); ax.set_ylim(0, 1.12)
    ax.legend(fontsize=7, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.02), columnspacing=1.0, handlelength=1.3, frameon=False)
    fig.tight_layout(rect=[0,0,1,0.93]); ap.save(fig, os.path.join(FIG, "fig_trust"))


def fig_fidelity():
    """The interpretable surrogate's detection F1 vs the deployed KAN-IDS, per dataset:
    interpretability is bought by giving up detection, most starkly on CICIDS2017."""
    d = row()
    ds = ["UNSW", "CICIDS", "5G-NIDD"]
    full = [float(d[k]["kan_full_f1"]) for k in ds]
    sym = [float(d[k]["kan_symbolic_f1"]) for k in ds]
    x = np.arange(len(ds)); w = 0.36
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    ax.bar(x - w / 2, full, w, facecolor="white", edgecolor=ap.INK, linewidth=1.0,
           hatch="///", label="deployed model")
    ax.bar(x + w / 2, sym, w, facecolor="white", edgecolor=ap.WARM, linewidth=1.0,
           hatch="...", label="interpretable surrogate")
    for i in range(len(ds)):
        ax.annotate("", xy=(x[i] + w / 2, sym[i]), xytext=(x[i] - w / 2, full[i]),
                    arrowprops=dict(arrowstyle="->", color=ap.GRAY, lw=0.7))
    ax.set_xticks(x); ax.set_xticklabels(ds)
    ax.set_ylabel("detection $F_1$"); ax.set_ylim(0, 1.08)
    ax.legend(fontsize=7, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.02), frameon=False)
    fig.tight_layout(rect=[0,0,1,0.93]); ap.save(fig, os.path.join(FIG, "fig_fidelity"))


def fig_defense():
    """Reliability-gate detector AUC per dataset, full detector vs the OOD-only baseline:
    the gate predicts explanation reliability and is not reducible to out-of-distribution."""
    import os as _os
    with open(_os.path.join(HERE, "results", "defense_ablate.csv")) as f:
        d = {r["dataset"]: r for r in csv.DictReader(f)}
    ds = ["UNSW", "CICIDS", "5G-NIDD"]
    full = [float(d[k]["full_auc"]) for k in ds]
    ood = [float(d[k]["ood_only"]) for k in ds]
    x = np.arange(len(ds)); w = 0.36
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    ax.bar(x - w / 2, full, w, facecolor="white", edgecolor=ap.AGREEN, linewidth=1.0,
           hatch="///", label="full reliability gate")
    ax.bar(x + w / 2, ood, w, facecolor="white", edgecolor=ap.GRAY, linewidth=1.0,
           hatch="...", label="OOD-only baseline")
    ax.axhline(0.5, color=ap.WARM, ls=":", lw=0.9)
    ax.text(2.35, 0.505, "chance", fontsize=7, color=ap.WARM, ha="right", va="bottom")
    ax.set_xticks(x); ax.set_xticklabels(ds)
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
    ds = ["UNSW", "CICIDS", "5G-NIDD"]
    detect = [float(d[k]["detection_agreement"]) for k in ds]
    diverge = [float(d[k]["action_divergence"]) for k in ds]
    x = np.arange(len(ds)); w = 0.36
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    ax.bar(x - w / 2, detect, w, facecolor="white", edgecolor=ap.INK, linewidth=1.0,
           hatch="///", label="detection agreement")
    ax.bar(x + w / 2, diverge, w, facecolor="white", edgecolor=ap.WARM, linewidth=1.0,
           hatch="...", label="action divergence")
    ax.set_xticks(x); ax.set_xticklabels(ds)
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
    ds = ["UNSW", "CICIDS", "5G-NIDD"]
    M = np.array([[float(d[k][p]) for k in ds] for p in pairs])
    cmap = LinearSegmentedColormap.from_list("wag", ["#FFFFFF", ap.AGREEN])
    fig, ax = plt.subplots(figsize=(3.5, 3.4))
    im = ax.imshow(M, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(3)); ax.set_xticklabels(ds, fontsize=7)
    ax.set_yticks(range(len(pairs))); ax.set_yticklabels(plab, fontsize=7)
    ax.grid(False); ax.tick_params(length=0)
    for i in range(len(pairs)):
        for j in range(3):
            ax.text(j, i, f"{M[i,j]:.2f}", ha="center", va="center", fontsize=7,
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
    ds = ["UNSW", "CICIDS", "5G-NIDD"]
    styd = {"UNSW": (ap.INK, "o", "-"), "CICIDS": (ap.WARM, "s", "--"), "5G-NIDD": (ap.AGREEN, "^", "-.")}
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
    """HORIZONTAL BAR sorted: action divergence by attack type (TON-IoT). Serious threats top."""
    import os as _os
    with open(_os.path.join(HERE, "results", "harm_bytype.csv")) as f:
        rows = [r for r in csv.DictReader(f) if r["dataset"] == "TON-IoT"]
    rows.sort(key=lambda r: float(r["action_divergence"]))
    labs = [r["attack_type"] for r in rows]; vals = [float(r["action_divergence"]) for r in rows]
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    for i, v in enumerate(vals):
        c = ap.WARM if v >= 0.5 else ap.GRAY
        ax.barh(i, v, color="white", edgecolor=c, linewidth=1.0, hatch="///" if v >= 0.5 else "...")
    ax.set_yticks(range(len(labs))); ax.set_yticklabels(labs, fontsize=7)
    ax.set_xlabel("action divergence"); ax.set_xlim(0, 1.05)
    ap.headline(ax, "serious threats (scanning,\nbackdoor, ransomware) worst", loc="lower right")
    fig.tight_layout(); ap.save(fig, os.path.join(FIG, "fig_harmtype"))


if __name__ == "__main__":
    fig_trust(); print("fig_trust ok")
    fig_fidelity(); print("fig_fidelity ok")
    fig_defense(); print("fig_defense ok")
    fig_harm(); print("fig_harm ok")
    fig_pairwise_heat(); print("fig_pairwise_heat ok")
    fig_robust(); print("fig_robust ok")
    fig_harmtype(); print("fig_harmtype ok")
