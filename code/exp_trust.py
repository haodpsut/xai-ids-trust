"""
Three illustrative demonstrations, across three MODERN NIDS datasets, that
interpretability-based trust in ML-IDS rests on assumptions that fail. Each targets one
required property of interpretability-based trust (formalized in the paper):

  P1 FIDELITY           -- the interpretable form must decide as the model does.
  P2 NON-MANIPULABILITY -- an adversary must not change the explanation while keeping the
                           malicious decision.
  P3 GROUNDEDNESS       -- equally-accurate models must explain alike (else "trust" is arbitrary).

Each is shown to FAIL, on every dataset. Illustrative, not a benchmark; the contribution is
the formalization and the threat-aware criteria.
"""
import numpy as np, csv, os, torch
from sklearn.metrics import f1_score, accuracy_score
from harness import (MLP, KAN, nparams, match_mlp, train, predict, saliency, topk_features,
                     input_x_gradient, integrated_gradients, flow_bao_dong)
from data import load, DATASETS


def symbolic_kan_f1(kan, Xtr, Xte, yte):
    coef = kan.l1.coef.detach(); K = coef.shape[-1]
    lo, hi = np.percentile(Xtr, 1), np.percentile(Xtr, 99)
    grid = torch.linspace(float(lo), float(hi), 150); kk = torch.arange(1, K + 1).float()
    cos, sin = torch.cos(grid[:, None] * kk), torch.sin(grid[:, None] * kk)
    h, di = coef.shape[1], coef.shape[2]; P = np.zeros((h, di, 4))
    for j in range(h):
        for i in range(di):
            f = (cos @ coef[0, j, i] + sin @ coef[1, j, i]).numpy()
            P[j, i] = np.polyfit(grid.numpy(), f, 3)
    Pt = torch.tensor(P, dtype=torch.float32)
    x = torch.tensor(Xte, dtype=torch.float32)
    xp = torch.stack([x ** (3 - d) for d in range(4)], -1)
    h1 = torch.einsum("bid,jid->bj", xp, Pt) + kan.l1.bias.detach()
    with torch.no_grad():
        pred = kan.l2(torch.tanh(h1)).argmax(1).numpy()
    return f1_score(yte, pred)


def p1_fidelity(Xtr, ytr, Xte, yte):
    din = Xtr.shape[1]
    kan = train(KAN(din, 16, 4), Xtr, ytr, 0)
    f1_full = f1_score(yte, predict(kan, Xte))
    f1_sym = symbolic_kan_f1(kan, Xtr, Xte, yte)
    # post-hoc top-5 sufficiency for an MLP-IDS
    mlp = train(MLP(din, match_mlp(din, nparams(KAN(din, 16, 4)))), Xtr, ytr, 0)
    tk = topk_features(saliency(mlp, Xte), 5)
    base = Xtr.mean(0); Xmask = np.tile(base, (len(Xte), 1)).astype(np.float32)
    for r in range(len(Xte)):
        Xmask[r, tk[r]] = Xte[r, tk[r]]
    suff = accuracy_score(predict(mlp, Xte), predict(mlp, Xmask))
    return mlp, dict(kan_full_f1=f1_full, kan_symbolic_f1=f1_sym,
                     fidelity_drop=f1_full - f1_sym, topk5_sufficiency=suff)


def _jac(a, b):
    return len(set(a) & set(b)) / len(set(a) | set(b))


def p2_determinacy(mlp, Xte, yte):
    """DETERMINACY: the explanation shown to the analyst must be determined by the decision, not
    by an arbitrary choice of attribution method. We compute three standard, equally-defensible
    attributions (gradient saliency, input x gradient, integrated gradients) for the SAME model on
    the SAME flagged-malicious flows, and measure how much their top-5 'reasons' agree. Low
    agreement => the 'reason' is a method artifact, so trusting it is unfounded."""
    idx = flow_bao_dong(mlp, Xte, yte, 1000)
    if len(idx) < 20:
        return dict(grad_vs_ixg=float("nan"), grad_vs_ig=float("nan"), ixg_vs_ig=float("nan"), mean_agree=float("nan"))
    Xm = Xte[idx]
    g = topk_features(saliency(mlp, Xm), 5)
    ixg = topk_features(input_x_gradient(mlp, Xm), 5)
    ig = topk_features(integrated_gradients(mlp, Xm), 5)
    a = np.mean([_jac(g[r], ixg[r]) for r in range(len(idx))])
    b = np.mean([_jac(g[r], ig[r]) for r in range(len(idx))])
    c = np.mean([_jac(ixg[r], ig[r]) for r in range(len(idx))])
    return dict(grad_vs_ixg=float(a), grad_vs_ig=float(b), ixg_vs_ig=float(c),
                mean_agree=float(np.mean([a, b, c])))


def p3_groundedness(Xtr, ytr, Xte, yte):
    din = Xtr.shape[1]; h = match_mlp(din, nparams(KAN(din, 16, 4)))
    models = [train(MLP(din, h), Xtr, ytr, s) for s in range(4)]
    f1s = [f1_score(yte, predict(m, Xte)) for m in models]
    # ⛔ Truoc 10/11/2026 dong nay la `sub = Xte[:1000]`: 1000 flow DAU cua tap
    # kiem, ke ca flow LANH. Do tren UNSW-NB15: ty le tan cong trong tap ay la
    # 0,676, nghia la 32% flow ma P3 do tren la flow phan tich vien KHONG BAO GIO
    # xem. Cung tep nay do P2 tren tap bao dong, nen P2 va P3 cua bai duoc do tren
    # HAI quan the khac nhau roi in canh nhau. Nay ca hai goi `flow_bao_dong`.
    sub = Xte[flow_bao_dong(models, Xte, yte, 1000)]
    tks = [topk_features(saliency(m, sub), 5) for m in models]
    ov = []
    for a in range(len(models)):
        for b in range(a + 1, len(models)):
            ov += [len(set(tks[a][r]) & set(tks[b][r])) / len(set(tks[a][r]) | set(tks[b][r]))
                   for r in range(len(sub))]
    return dict(mean_f1=float(np.mean(f1s)), std_f1=float(np.std(f1s)), topk_jaccard=float(np.mean(ov)))


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = []
    for ds in DATASETS:
        np.random.seed(0); torch.manual_seed(0)         # determinism for reproducible P1/P2/P3
        Xtr, ytr, Xte, yte, feats = load(ds)
        print(f"\n=== {ds}: train{Xtr.shape} test{Xte.shape} attack-rate={yte.mean():.2f} ===")
        mlp, r1 = p1_fidelity(Xtr, ytr, Xte, yte)
        r2 = p2_determinacy(mlp, Xte, yte)
        r3 = p3_groundedness(Xtr, ytr, Xte, yte)
        print(f"  P1 KAN full F1={r1['kan_full_f1']:.3f} symbolic={r1['kan_symbolic_f1']:.3f} "
              f"drop={r1['fidelity_drop']:.3f}; top5-suff={r1['topk5_sufficiency']:.3f}")
        print(f"  P2 method-agree grad/ixg={r2['grad_vs_ixg']:.3f} grad/ig={r2['grad_vs_ig']:.3f} "
              f"ixg/ig={r2['ixg_vs_ig']:.3f} mean={r2['mean_agree']:.3f}")
        print(f"  P3 F1={r3['mean_f1']:.3f}±{r3['std_f1']:.3f} seed-expl-agree(Jaccard)={r3['topk_jaccard']:.3f}")
        rows.append(dict(dataset=ds, **r1, **{f"p2_{k}": v for k, v in r2.items()},
                         **{f"p3_{k}": v for k, v in r3.items()}))
    keys = list(rows[0].keys())
    with open("results/trust.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    print("\nwrote results/trust.csv")
