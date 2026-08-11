"""The chance floor for top-k Jaccard agreement, and the conversion the paper was missing.

Two defects this fixes, both found by external review on 11/08/2026.

FIRST, the paper described J=0.15 in words as "explainers agree on 0.15 of the features they
show". That is not what Jaccard means. Jaccard divides by the UNION, so with k=5 and J=0.15 the
intersection is 2kJ/(1+J) = 1.30 features, and the fraction of the five features shown to the
analyst that both explainers agree on is 1.30/5 = 0.26. The paper understated its own overlap by
1.7x, in the abstract. `frac_shown` below is that conversion; it is exact, not an estimate.

SECOND, a Jaccard of 0.15 is only alarming relative to what two UNRELATED explainers would score.
That floor depends on the feature count: picking two independent uniform top-5 sets from 34
features collides more often than from 52. The paper reported 0.15 on datasets with 34-52
features and never said what chance was, so a reader could not tell a weak signal from none.

`E_J_random` is computed exactly, not simulated: with d features and top-k sets drawn uniformly
and independently, the intersection size i is hypergeometric, P(i) = C(k,i)C(d-k,k-i)/C(d,k),
and E[J] = sum_i P(i) * i/(2k-i). Note E[J] != E[i]/(2k-E[i]) -- Jensen bites here, which is why
the ratio-of-means shortcut is not used. The simulated column is a check on the closed form, not
a substitute for it: they must agree to within Monte-Carlo error or one of the two is wrong.
"""
import csv
import math
import os

import numpy as np

K = 5


def e_jaccard_random(d, k=K):
    """Exact E[J_k] for two independent uniform top-k sets out of d features."""
    tot = math.comb(d, k)
    e = 0.0
    for i in range(0, k + 1):
        if k - i > d - k:
            continue
        p = math.comb(k, i) * math.comb(d - k, k - i) / tot
        e += p * (i / (2 * k - i))
    return e


def e_inter_random(d, k=K):
    return k * k / d


def sim_jaccard_random(d, k=K, n=200000, seed=0):
    rng = np.random.default_rng(seed)
    a = np.argsort(rng.random((n, d)), axis=1)[:, :k]
    b = np.argsort(rng.random((n, d)), axis=1)[:, :k]
    inter = np.array([len(set(x) & set(y)) for x, y in zip(a, b)])
    return float(np.mean(inter / (2 * k - inter)))


def frac_shown(j, k=K):
    """Fraction of the k features shown that the two explanations agree on, given Jaccard j."""
    return (2 * j / (1 + j))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "results"), exist_ok=True)
    prof = {}
    with open(os.path.join(here, "results", "dataset_profile.csv")) as f:
        for r in csv.DictReader(f):
            prof[r["dataset"]] = int(r["n_features"])

    # the lowest cross-family pair the paper quotes, per dataset (tab:pairwise, appendix)
    observed = {"UNSW": 0.18, "CICIDS": 0.17, "5G-NIDD": 0.31, "TON-IoT": 0.15, "CIC-IoT-2023": 0.21}

    rows = []
    for ds, d in prof.items():
        ej = e_jaccard_random(d)
        sim = sim_jaccard_random(d)
        assert abs(ej - sim) < 0.005, "closed form and simulation disagree: %.4f vs %.4f" % (ej, sim)
        obs = observed[ds]
        rows.append({
            "dataset": ds, "n_features": d, "k": K,
            "E_inter_random": round(e_inter_random(d), 3),
            "E_J_random": round(ej, 3),
            "E_J_random_sim": round(sim, 3),
            "J_observed_min_crossfamily": obs,
            "J_over_chance": round(obs / ej, 2),
            "frac_shown_observed": round(frac_shown(obs), 3),
            "frac_shown_chance": round(frac_shown(ej), 3),
        })
        print("  %-14s d=%2d | chance J=%.3f (sim %.3f) | observed J=%.2f = %.2fx chance | "
              "agree on %.0f%% of the 5 shown (chance %.0f%%)"
              % (ds, d, ej, sim, obs, obs / ej, 100 * frac_shown(obs), 100 * frac_shown(ej)))

    with open(os.path.join(here, "results", "jaccard_floor.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote results/jaccard_floor.csv (%d datasets)" % len(rows))
    print("\nconversion check: J=0.15 with k=5 -> intersection %.2f of 5 -> %.0f%% of shown features"
          % (2 * K * 0.15 / 1.15, 100 * frac_shown(0.15)))


if __name__ == "__main__":
    main()
