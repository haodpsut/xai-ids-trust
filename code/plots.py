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


if __name__ == "__main__":
    fig_trust(); print("fig_trust ok")
    fig_fidelity(); print("fig_fidelity ok")
    fig_defense(); print("fig_defense ok")
    fig_harm(); print("fig_harm ok")
