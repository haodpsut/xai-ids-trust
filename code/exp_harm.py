"""
B1: a concrete SECURITY HARM from explanation under-determination, without needing a manipulation
attack to succeed.

Setup. On flows that are TRUE attacks and that the IDS correctly flags, the detector is right and
stable. We ask what happens at the ANALYST's decision, which is driven by the explanation. We
model an analyst who reads an explanation and decides escalate (treat as real attack) or suppress
(dismiss as false positive) via an auditor classifier trained to read attribution vectors; we use
two auditor families (logistic regression and random forest) so the harm is not an artifact of a
linear analyst.

For an ensemble of equally-accurate detectors (differ only by seed), we compute, per true-positive
attack flow, the analyst action induced by each model's explanation. The harm:
  - SUPPRESSION RATE: how often a real attack's explanation reads benign, so the analyst dismisses
    a true attack.
  - ACTION DIVERGENCE: fraction of true attacks on which equally-good models induce OPPOSITE
    analyst actions, so whether the attack is caught depends on which seed was deployed, an
    accident. Contrast with DETECTION agreement (all models correctly flag the attack), which is
    near 1: detection is grounded, the explanation-driven action is not.
"""
import numpy as np, torch, csv, os, warnings
warnings.filterwarnings("ignore")
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from harness import MLP, KAN, nparams, match_mlp, train, predict, saliency, flow_bao_dong
from data import load, DATASETS

K = 5


def attr(model, X):
    a = saliency(model, X)
    return a / (np.abs(a).sum(1, keepdims=True) + 1e-9)


def run(ds, auditor="logistic"):
    np.random.seed(0); torch.manual_seed(0)             # determinism for reproducible harm rates
    Xtr, ytr, Xte, yte, feats = load(ds)
    din = Xtr.shape[1]; h = match_mlp(din, nparams(KAN(din, 16, 4)))
    models = [train(MLP(din, h), Xtr, ytr, s) for s in range(K)]
    # analyst-as-auditor: reads an explanation -> escalate(1)/suppress(0). Trained on model-0
    # clean explanations to recover the true label (a competent analyst).
    A0 = attr(models[0], Xtr)
    if auditor == "logistic":
        g = LogisticRegression(max_iter=300).fit(A0, ytr)
    else:
        g = RandomForestClassifier(n_estimators=80, max_depth=8, random_state=0).fit(A0, ytr)

    # true-positive attack flows: ground-truth attack AND every model flags attack (detection agrees)
    preds = np.stack([predict(m, Xte) for m in models], 1)
    # ⛔ `tp` o day dung CA HAI vai: `Xte[tp]` va `int(tp.sum())`. Phai lay MAT NA,
    # khong thi `.sum()` cong CAC CHI SO lai: do la cach `n_true_attacks` ra
    # 47012435 thay vi 7851 ngay 10/11/2026. Truyen `du_doan=preds` de khong
    # chay lai 5 lan `predict` va de `preds` van la nguon duy nhat.
    tp = flow_bao_dong(None, Xte, yte, mat_na=True, du_doan=preds)
    Xtp = Xte[tp]
    # Dung CHINH ham quan the de dem, kheo co hai cong thuc cho cung mot dai luong.
    detection_agree = float(len(flow_bao_dong(None, Xte, yte, du_doan=preds))
                            / max((yte == 1).sum(), 1))

    # analyst action per model per flow: 1=escalate (reads attack), 0=suppress (reads benign)
    actions = np.stack([g.predict(attr(m, Xtp)) for m in models], 1)   # [n_tp, K]
    suppress_rate = float((actions == 0).mean())                        # true attacks dismissed
    unanimous_escalate = (actions == 1).all(1)
    unanimous_suppress = (actions == 0).all(1)
    divergent = ~(unanimous_escalate | unanimous_suppress)             # models split -> seed decides
    action_divergence = float(divergent.mean())
    # of the true attacks, how many would be MISSED by at least one deployed model's explanation?
    missed_by_some = float((actions == 0).any(1).mean())
    return dict(dataset=ds, auditor=auditor, n_true_attacks=int(tp.sum()),
                detection_agreement=round(detection_agree, 3),
                suppression_rate=round(suppress_rate, 3),
                action_divergence=round(action_divergence, 3),
                missed_by_some_model=round(missed_by_some, 3))


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = []
    for ds in DATASETS:
        for aud in ["logistic", "rf"]:
            r = run(ds, aud); rows.append(r)
            print(f"{ds} [{aud}]: detect-agree={r['detection_agreement']} | suppress-rate={r['suppression_rate']} "
                  f"| ACTION-DIVERGENCE={r['action_divergence']} | missed-by-some={r['missed_by_some_model']} "
                  f"(n={r['n_true_attacks']})")
    with open("results/harm.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("wrote results/harm.csv")
