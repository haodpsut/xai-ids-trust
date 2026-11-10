"""
Pivot (a): explanation-space evasion of the HUMAN analyst (the security-specific attack).

Threat model. The attacker controls a malicious flow and wants its alarm DISMISSED. Classic
adversarial evasion flips the DETECTOR; we target the ANALYST instead: keep the detector firing
(the IDS still labels the flow an attack) but make the EXPLANATION the analyst sees resemble a
benign flow, so the analyst dismisses a true alarm as a false positive. This decouples detector
correctness from analyst trust, a harm that exists only because the explanation is trusted.

We model "an analyst who reasons from explanations" as an auditor classifier g trained to map an
attribution vector -> benign/attack (an analyst who has learned what benign explanations look
like). The attack succeeds on a flow if, after perturbation: (i) the IDS still predicts attack,
and (ii) g now reads the explanation as benign.

Attacker capability: we grant perturbation of all features (an upper bound; a real attacker
controls a subset, stated as a limitation). Budget is bounded in standardized units.
"""
import numpy as np, torch, csv, os
from sklearn.linear_model import LogisticRegression
from harness import MLP, nparams, match_mlp, train, predict, saliency, flow_bao_dong
from data import load, DATASETS
from harness import KAN  # for budget parity only


def attr_matrix(mlp, X):
    """Signed gradient saliency (the explanation vector), L1-normalized per sample."""
    a = saliency(mlp, X)
    return a / (np.abs(a).sum(1, keepdims=True) + 1e-9)


def run(ds, seed=0):
    Xtr, ytr, Xte, yte, feats = load(ds, seed)
    din = Xtr.shape[1]
    mlp = train(MLP(din, match_mlp(din, nparams(KAN(din, 16, 4)))), Xtr, ytr, 0)

    # analyst-as-auditor: learns benign-vs-attack from CLEAN explanations on training flows
    Atr = attr_matrix(mlp, Xtr)
    g = LogisticRegression(max_iter=300).fit(Atr, ytr)

    # benign explanation prototype (what a benign flow's reason looks like)
    benign_proto = torch.tensor(Atr[ytr == 0].mean(0), dtype=torch.float32)

    # target: malicious flows the IDS correctly flags as attack
    idx = flow_bao_dong(mlp, Xte, yte, 800)
    Xm = Xte[idx]
    A0 = attr_matrix(mlp, Xm)
    auditor0 = g.predict(A0)                      # analyst verdict BEFORE attack (should be attack=1)

    x0 = torch.tensor(Xm)
    delta = torch.zeros_like(x0, requires_grad=True)
    sd = torch.tensor(Xm.std(0) + 1e-6)
    opt = torch.optim.Adam([delta], lr=0.03)
    for _ in range(300):
        opt.zero_grad()
        x = x0 + delta
        logit = mlp(x)
        # (i) keep the IDS decision = attack (hard margin)
        keep = torch.relu(logit[:, 0] - logit[:, 1] + 3.0).sum()
        # (ii) make the (differentiable) saliency resemble the benign prototype
        gsig, = torch.autograd.grad(logit[:, 1].sum(), x, create_graph=True)
        sal = gsig / (gsig.abs().sum(1, keepdim=True) + 1e-9)
        align = ((sal - benign_proto) ** 2).sum()        # push explanation toward benign
        budget = ((delta / sd) ** 2).sum()
        (keep * 20.0 + align * 3.0 + budget * 0.01).backward()
        opt.step()

    Xadv = (x0 + delta).detach().numpy()
    still_attack = float((predict(mlp, Xadv) == 1).mean())     # detector still fires?
    A1 = attr_matrix(mlp, Xadv)
    auditor1 = g.predict(A1)                                   # analyst verdict AFTER attack
    # success = detector still says attack AND analyst now reads benign
    dismissed = float(((predict(mlp, Xadv) == 1) & (auditor1 == 0)).mean())
    l2 = float(np.sqrt(((Xadv - Xm) ** 2).sum(1)).mean())
    return dict(dataset=ds, still_attack=round(still_attack, 3),
                analyst_benign_before=round(float((auditor0 == 0).mean()), 3),
                analyst_benign_after=round(float((auditor1 == 0).mean()), 3),
                attack_success_dismissed=round(dismissed, 3),
                mean_l2_perturb=round(l2, 3))


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = []
    for ds in DATASETS:
        r = run(ds)
        rows.append(r)
        print(f"{ds}: IDS-still-attack={r['still_attack']} | analyst-benign {r['analyst_benign_before']}"
              f"->{r['analyst_benign_after']} | ATTACK-SUCCESS(true-alarm dismissed)={r['attack_success_dismissed']}"
              f" | L2={r['mean_l2_perturb']}")
    with open("results/attack.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("wrote results/attack.csv")
