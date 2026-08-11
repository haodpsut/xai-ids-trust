"""Does groundedness actually predict analyst harm? The test Proposition 2 never had.

Proposition 2 asserts a monotone link: worse groundedness (lower seed-agreement P3) forces more
explanation-driven harm. The proof sketch closed by asserting the trend was visible in our own
results, naming CICIDS as the dataset with "worse groundedness on hard attacks". That was false
in our own table -- CICIDS has the HIGHEST P3 of the five -- and no correlation was ever computed.

This script computes it, across all three outcome measures the paper uses, for both auditors.
A negative Spearman rho supports the proposition (less groundedness, more harm); a positive rho
contradicts it. n=5 datasets, so the exact permutation p-value is over 120 orderings and is
computed exhaustively rather than approximated -- at this n a normal approximation is meaningless.

Reads multiseed.csv (P3 with its across-seed dispersion) and harm.csv / auditor_control.csv.
No models are trained here; this is an analysis of results already produced and released.
"""
import csv
import itertools
import os

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def rank(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    for pos, i in enumerate(order):
        r[i] = pos + 1.0
    return r


def spearman(x, y):
    rx, ry = rank(x), rank(y)
    n = len(x)
    d2 = sum((a - b) ** 2 for a, b in zip(rx, ry))
    return 1 - 6 * d2 / (n * (n * n - 1))


def perm_p(x, y):
    """Two-sided exact permutation p-value for Spearman rho at small n."""
    obs = abs(spearman(x, y))
    perms = list(itertools.permutations(y))
    hit = sum(1 for p in perms if abs(spearman(x, list(p))) >= obs - 1e-12)
    return hit / len(perms)


def col(path, key, val_col, filt=None):
    out = {}
    with open(os.path.join(R, path)) as f:
        for r in csv.DictReader(f):
            if filt and any(r[k] != v for k, v in filt.items()):
                continue
            out[r[key]] = float(r[val_col])
    return out


def main():
    p3 = col("multiseed.csv", "dataset", "p3_seed_agree_mean")
    ds = list(p3)
    tests = [
        ("action_divergence", "logistic",
         col("harm.csv", "dataset", "action_divergence", {"auditor": "logistic"})),
        ("action_divergence", "rf",
         col("harm.csv", "dataset", "action_divergence", {"auditor": "rf"})),
        ("suppression_rate", "rf",
         col("harm.csv", "dataset", "suppression_rate", {"auditor": "rf"})),
        ("p_cross", "rf",
         col("auditor_control.csv", "dataset", "p_cross", {"auditor": "rf"})),
        ("p_excess", "rf",
         col("auditor_control.csv", "dataset", "p_excess", {"auditor": "rf"})),
    ]
    rows = []
    x = [p3[d] for d in ds]
    for measure, aud, m in tests:
        y = [m[d] for d in ds]
        rho = spearman(x, y)
        p = perm_p(x, y)
        rows.append({
            "outcome": measure, "auditor": aud, "n_datasets": len(ds),
            "spearman_rho_vs_p3": round(rho, 3), "exact_perm_p": round(p, 3),
            "sign_predicted_by_prop2": "negative",
            "supports_prop2": "yes" if rho < 0 else "no",
        })
        print("  P3 vs %-18s [%-8s]  rho = %+0.3f  (exact p = %.3f)  -> %s"
              % (measure, aud, rho, p, "supports" if rho < 0 else "CONTRADICTS"))

    print("\n  P3 by dataset: " + "  ".join("%s=%.3f" % (d, p3[d]) for d in ds))
    hi = max(ds, key=lambda d: p3[d])
    print("  highest groundedness: %s (%.3f) -- the dataset the proof sketch named as the WORST"
          % (hi, p3[hi]))

    with open(os.path.join(R, "prop2_test.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote results/prop2_test.csv (%d tests)" % len(rows))


if __name__ == "__main__":
    main()
