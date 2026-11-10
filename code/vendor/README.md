# Vendored house plotting module

`plot-assets/` is a byte-for-byte copy of the in-house figure module that `code/plots.py`
imports. It is vendored here so that figure regeneration works from a clean clone; before
this, `plots.py` raised `ModuleNotFoundError: No module named 'agentra_plot'` for anyone
outside the author's machine, while the paper claimed the figures could be rebuilt.

`VENDOR.sha256` records the digest of each copied file. `code/cong_bo_style.py` verifies the
copy against it, and, when the author's canonical directory is present, also checks that the
copy has not drifted from it. Two copies of a style module are two sources of truth, so the
drift check is the thing that keeps them one.

To render against the canonical copy instead of this one:

```bash
AGENTRA_PLOT_ASSETS=/path/to/canonical/assets python code/plots.py
```

`agentra_plot.save()` needs `pillow`, and its print-readiness audit shells out to
`measure_plot.py`, which needs `PyMuPDF`. Both are pinned in `requirements.txt`.
