"""
F: an adaptive attack on the reliability gate (reviewer B2, false-reliable). The gate reads four
cheap signals (margin, attribution entropy, local fidelity, OOD distance) and passes an
explanation as reliable when they look right. An attacker who wants a MALICIOUS flow's
(unfaithful, unstable) explanation to be accepted can try to shape those signals. We take true
attacks whose real stability S(x) is LOW (bottom half) and whose explanation the gate would
correctly flag as unreliable, and perturb the input to push the gate's predicted-reliable
probability up while keeping the malicious decision. If the gate can be flipped to "reliable" on
genuinely-unreliable explanations, it is not robust: an adversary can launder a bad explanation
through it.
"""
import numpy as np, torch, csv, os, warnings
warnings.filterwarnings("ignore")
from sklearn.linear_model import LogisticRegression
from harness import MLP, KAN, nparams, match_mlp, train, predict, saliency, flow_bao_dong
from exp_defense import ground_truth_reliability, cheap_signals, K
from data import load, DATASETS


def run(ds):
    Xtr, ytr, Xte, yte, feats = load(ds); din = Xtr.shape[1]
    h = match_mlp(din, nparams(KAN(din, 16, 4)))
    models = [train(MLP(din, h), Xtr, ytr, s) for s in range(K)]
    f = models[0]
    # fit the gate on true attacks (as in exp_defense)
    idx = flow_bao_dong(f, Xte, yte, 2000)
    Xm = Xte[idx]
    rel = ground_truth_reliability(models, Xm)
    ythr = np.median(rel)
    S = cheap_signals(f, Xm, Xtr)
    gate = LogisticRegression(max_iter=500).fit(S, (rel > ythr).astype(int))
    # target: genuinely-unreliable true attacks the gate correctly rejects
    lowrel = np.where((rel <= ythr))[0][:400]
    Xa = Xm[lowrel]
    before_reliable = float((gate.predict(cheap_signals(f, Xa, Xtr)) == 1).mean())
    # adaptive perturbation: raise gate prob while keeping the malicious decision (margin term
    # is one of the gate's own inputs, so the attack partly games the gate by construction)
    x0 = torch.tensor(Xa); delta = torch.zeros_like(x0, requires_grad=True)
    sd = torch.tensor(Xa.std(0) + 1e-6)
    opt = torch.optim.Adam([delta], lr=0.03)
    w = torch.tensor(gate.coef_[0], dtype=torch.float32)
    for _ in range(200):
        opt.zero_grad(); x = x0 + delta
        logit = f(x)
        keep = torch.relu(logit[:, 0] - logit[:, 1] + 3.0).sum()          # keep attack decision
        # differentiable proxies for two gate inputs: margin and attribution entropy
        margin = (logit[:, 1] - logit[:, 0])
        g, = torch.autograd.grad(logit[:, 1].sum(), x, create_graph=True)
        p = g.abs() / (g.abs().sum(1, keepdim=True) + 1e-9)
        ent = -(p * (p + 1e-12).log()).sum(1)
        # ⛔ `-ent` o day la kappa = -H cua Proposition, va tu 11/11/2026 day DUNG
        # la dac trung so 1 ma `cheap_signals` tra ve. Truoc do `cheap_signals` tra
        # ve +H duoi ten `concentration`, nen cong duoc khop tren +H trong khi tan
        # cong day theo -H: mot trong hai thanh phan gradient day NGUOC huong, va
        # so tan cong bai bao la CHAN DUOI chu khong phai suc manh thuc.
        # ⇒ [[feedback-nhan-cot-giong-nhau-nghia-khac-nhau]]
        # gate weight sign tells us which direction is "more reliable"
        push = -(w[0] * margin + w[1] * (-ent)).sum()                     # raise gate score
        budget = ((delta / sd) ** 2).sum()
        (keep * 20 + push * 1.0 + budget * 0.02).backward(); opt.step()
    Xadv = (x0 + delta).detach().numpy()
    still = float((predict(f, Xadv) == 1).mean())
    after_reliable = float((gate.predict(cheap_signals(f, Xadv, Xtr)) == 1).mean())
    return dict(dataset=ds, still_attack=round(still, 3),
                reliable_before=round(before_reliable, 3),
                reliable_after=round(after_reliable, 3),
                attack_gain=round(after_reliable - before_reliable, 3))


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = [run(ds) for ds in DATASETS]
    with open("results/gate_attack.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    for r in rows:
        print(f"{r['dataset']}: still-attack={r['still_attack']} | gate-says-reliable "
              f"{r['reliable_before']}->{r['reliable_after']} (attack gain {r['attack_gain']})")
    print("wrote results/gate_attack.csv")
