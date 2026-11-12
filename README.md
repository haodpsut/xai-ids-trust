# xai-ids-trust

Code and results for *"An evaluation framework for post-hoc explanations in machine-learning
intrusion detection: fidelity, determinacy, and groundedness."*

The study formalizes three necessary properties of interpretability-based trust in ML-IDS
(fidelity, determinacy, groundedness), measures them on **five** public NIDS datasets
(UNSW-NB15, the corrected CICIDS2017, 5G-NIDD, TON-IoT, CIC-IoT-2023) across five explainers
(gradient, input x gradient, integrated gradients, SHAP, LIME), tests an
explanation-manipulation attack (reported as inconclusive on tabular IDS), and builds a
per-alarm reliability gate.

## Setup

```bash
pip install -r requirements.txt      # pinned: see the file for exact versions
```

Python 3.9.6 produced every number in the paper. `environment.yml` builds the same
environment under conda; it installs `torch` through pip because no conda channel ships
PyTorch 2.8.0 for Python 3.9.

## Data

`data/` is not tracked in git: two of the five files exceed GitHub's 100 MB per-file limit,
and the datasets belong to their publishers. **See [DATA.md](DATA.md)** for the expected
layout, the publication of each dataset, and a SHA-256 manifest so you can confirm you have
the same bytes that produced the published numbers.

```bash
python code/cong_du_lieu.py          # checks presence, digests, and that pandas can read each file
```

## Experiments (code/)

`harness.py` holds the shared model and attribution code, `data.py` the loading pipeline.
The scripts behind the paper's headline numbers:

| Script | Produces |
|---|---|
| `exp_trust.py` | P1 fidelity / P2 determinacy / P3 groundedness |
| `exp_breadth.py` | P2 across 5 explainers incl. SHAP and LIME |
| `exp_fidelity_multi.py` | fidelity of three readable surrogate families |
| `exp_faith_5explainer.py` | faithfulness across the five explainers |
| `exp_multiseed.py` | multi-seed means and standard deviations |
| `exp_attack.py` | explanation-evasion attack (inconclusive) |
| `exp_defense.py` | per-alarm reliability gate (AUC) |
| `exp_defense_ablate.py` | gate signal ablation (not just OOD detection) |
| `exp_harm.py`, `exp_harm_bytype.py` | harm model, and harm per attack type |
| `exp_dataset_profile.py` | dataset profile table |
| `check_freshness.py` | asserts every results CSV is newer than the script that wrote it |

Committed outputs live in `code/results/` (32 CSV files); the table above lists the
scripts behind the headline numbers, and there are 29 `exp_*.py` in all, including the
controls and ablations. `check_freshness.py` returns 0 on the committed set and reports
32/32.

## Figures

`python code/plots.py` rebuilds the seven generated figures from `code/results/` alone, with no
raw data needed. The plotting style module it imports is vendored at
`code/vendor/plot-assets/`, and `plots.py` puts that directory on `sys.path` itself, so a clean
clone can render without further setup; set `AGENTRA_PLOT_ASSETS` to render against a different
copy. Checked on 2026-11-12 from a fresh `git clone` of this repository: all seven figures
rendered, exit status 0, and the 24 plotted values written to `code/_fig-values.csv` were
identical to the ones behind the submitted figures. The rendered PDFs are not byte-identical to
the committed ones, because a PDF records its creation time; the plotted values are what
reproduces.

The two schematic figures (`fig_framework`, `fig_threat`) are TikZ, not Python; their sources
are `paper/figs/*.tex` and they share `paper/figs/palette.tex`.

## What needs the raw data

Two checks read the five datasets, so from a clean clone without `data/` they report red, and
that red is the expected "you do not have the data" signal rather than a defect:

| Check | Without `data/` |
|---|---|
| `cong_du_lieu.py` | D1, D2, D4 red: 0/5 files present, so nothing to digest or read |
| `cong_tien_dinh.py` | T4 red: the three re-run scripts raise `FileNotFoundError` |

Everything else in this repository runs from the committed CSVs.

## Reproduction status

`exp_dataset_profile.py` was re-run on a second machine (Linux, Python 3.9.6, clean clone,
freshly installed pins) on 2026-11-10 and produced `results/dataset_profile.csv`
byte-identical to the committed file.
