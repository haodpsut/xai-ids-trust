"""
Reviewer stress-test (tree ensembles + TreeSHAP). Tree ensembles dominate tabular NIDS, and
TreeSHAP is EXACT and deterministic, so a reviewer will ask: do the determinacy (P2) and
groundedness (P3) failures survive when we swap the neural detector for a random forest / gradient
boosting model explained by TreeSHAP? We answer honestly here.

  P2 determinacy (cross-METHOD): TreeSHAP is deterministic, so TreeSHAP-vs-TreeSHAP is trivially
     1.0. The real determinacy question is whether the top-k reasons agree across equally-defensible
     tree attributions: TreeSHAP vs. impurity (Gini) importance vs. permutation importance vs. LIME.
  P3 groundedness (cross-SEED): train several forests that differ only in seed (bootstrap + feature
     subsampling); do their TreeSHAP top-k agree?
  Faithfulness: comprehensiveness of the TreeSHAP top-5 (drop in attack-probability when removed).
  P1 fidelity: a readable global surrogate (depth-2 tree) of the ensemble vs. the ensemble.

Deterministic (seeded).
"""
import numpy as np, csv, os, warnings
warnings.filterwarnings("ignore")
import shap
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import f1_score, accuracy_score
from lime.lime_tabular import LimeTabularExplainer
from harness import flow_bao_dong
from data import load, DATASETS

K = 5
NSAMP = 200          # instances for per-instance attribution agreement
SEEDS = [0, 1, 2, 3]


def topk(v, k=K):
    return np.argsort(-np.abs(np.asarray(v)), axis=-1)[..., :k]


def jac(a, b):
    sa, sb = set(np.asarray(a).tolist()), set(np.asarray(b).tolist())
    return len(sa & sb) / len(sa | sb)


def treeshap_local(model, Xm):
    """Per-instance TreeSHAP attributions for the attack class."""
    expl = shap.TreeExplainer(model)
    sv = expl.shap_values(Xm, check_additivity=False)
    if isinstance(sv, list):                 # [class0, class1]
        sv = sv[1]
    elif np.asarray(sv).ndim == 3:           # (n, d, classes)
        sv = np.asarray(sv)[..., 1]
    return np.asarray(sv)


def build(ds, algo, seed):
    Xtr, ytr, Xte, yte, feats = load(ds, seed)
    if algo == "rf":
        m = RandomForestClassifier(n_estimators=200, max_depth=None, n_jobs=-1,
                                   random_state=seed, max_features="sqrt")
    else:
        m = GradientBoostingClassifier(n_estimators=150, max_depth=3, random_state=seed)
    m.fit(Xtr, ytr)
    return m, Xtr, ytr, Xte, yte, feats


def run(ds, algo):
    np.random.seed(0)
    m, Xtr, ytr, Xte, yte, feats = build(ds, algo, 0)
    f1_full = f1_score(yte, m.predict(Xte))
    tp = flow_bao_dong(m, Xte, yte, NSAMP)
    Xm = Xte[tp]

    # ---- P2 determinacy: agreement across equally-defensible tree attributions ----
    ts = topk(treeshap_local(m, Xm))                              # TreeSHAP (per-instance)
    gini = np.argsort(-m.feature_importances_)[:K]                # global impurity ranking
    perm = np.argsort(-permutation_importance(m, Xm, m.predict(Xm), n_repeats=5,
                                              random_state=0).importances_mean)[:K]
    lex = LimeTabularExplainer(Xtr[:1500], feature_names=[str(c) for c in feats],
                               discretize_continuous=False, mode="classification", random_state=0)
    lime_tk = np.zeros((len(Xm), K), int)
    proba = lambda X: m.predict_proba(np.asarray(X))
    for r in range(len(Xm)):
        e = lex.explain_instance(Xm[r], proba, num_features=K, labels=(1,), num_samples=800)
        lime_tk[r] = [i for i, _ in e.local_exp[1][:K]]
    # TreeSHAP(local) vs LIME(local): the two per-instance methods
    shap_vs_lime = float(np.mean([jac(ts[r], lime_tk[r]) for r in range(len(Xm))]))
    # TreeSHAP(local, majority set) vs the two GLOBAL rankings (gini, permutation)
    ts_global = np.argsort(-np.abs(treeshap_local(m, Xm)).mean(0))[:K]
    shap_vs_gini = jac(ts_global, gini)
    shap_vs_perm = jac(ts_global, perm)
    gini_vs_perm = jac(gini, perm)
    p2 = float(np.mean([shap_vs_lime, shap_vs_gini, shap_vs_perm, gini_vs_perm]))

    # ---- P3 groundedness: cross-seed TreeSHAP top-k on the SAME flows ----
    models = [build(ds, algo, s)[0] for s in SEEDS]
    f1s = [f1_score(yte, mm.predict(Xte)) for mm in models]
    tks = [topk(treeshap_local(mm, Xm)) for mm in models]
    ov = []
    for a in range(len(models)):
        for b in range(a + 1, len(models)):
            ov += [jac(tks[a][r], tks[b][r]) for r in range(len(Xm))]
    p3 = float(np.mean(ov))

    # ---- Faithfulness: comprehensiveness of TreeSHAP top-5 ----
    base = Xtr.mean(0)
    p0 = m.predict_proba(Xm)[:, 1]
    Xrm = Xm.copy()
    for r in range(len(Xm)):
        Xrm[r, ts[r]] = base[ts[r]]
    comp = float((p0 - m.predict_proba(Xrm)[:, 1]).mean())

    # ---- P1 fidelity: readable depth-2 surrogate of the ensemble ----
    sur = DecisionTreeClassifier(max_depth=2, random_state=0).fit(Xtr, m.predict(Xtr))
    agree = accuracy_score(m.predict(Xte), sur.predict(Xte))
    f1_sur = f1_score(yte, sur.predict(Xte))

    return dict(dataset=ds, algo=algo, f1=round(f1_full, 3),
                p2_determinacy=round(p2, 3), p3_groundedness=round(p3, 3),
                faith_comp=round(comp, 3), p1_surrogate_agree=round(agree, 3),
                p1_surrogate_f1=round(f1_sur, 3), f1_seed_std=round(float(np.std(f1s)), 4))


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = []
    for algo in ["rf", "gb"]:
        for ds in DATASETS:
            r = run(ds, algo); rows.append(r)
            print(f"{algo:3s} {r['dataset']:8s} | F1={r['f1']:.3f} (surrogate {r['p1_surrogate_f1']:.3f}, "
                  f"agree {r['p1_surrogate_agree']:.3f}) | P2-determinacy={r['p2_determinacy']:.3f} "
                  f"P3-groundedness={r['p3_groundedness']:.3f} | TreeSHAP-comp={r['faith_comp']:.3f}")
    with open("results/tree.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("\nwrote results/tree.csv")
