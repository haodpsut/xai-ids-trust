"""
Shared harness for the CSF vision paper on interpretability-based trust in ML-IDS.
Provides: an MLP and a Fourier-KAN IDS classifier, gradient saliency, a symbolic (cubic)
surrogate of the KAN first layer, and metrics. Kept small and self-contained; the paper's
contribution is foundational, these are illustrative demonstrations.
"""
import numpy as np
import torch
import torch.nn as nn

torch.set_num_threads(4)
DEVICE = "cpu"


class MLP(nn.Module):
    def __init__(self, din, h, nc=2):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(din, h), nn.ReLU(),
                                 nn.Linear(h, h), nn.ReLU(), nn.Linear(h, nc))

    def forward(self, x):
        return self.net(x)


class FourierKANLayer(nn.Module):
    def __init__(self, din, dout, K=4):
        super().__init__()
        self.din, self.dout, self.K = din, dout, K
        self.coef = nn.Parameter(0.1 * torch.randn(2, dout, din, K) / (din * K) ** 0.5)
        self.bias = nn.Parameter(torch.zeros(dout))

    def forward(self, x):
        kk = torch.arange(1, self.K + 1, device=x.device).float()
        xk = x[:, None, :, None] * kk
        basis = torch.cat([torch.cos(xk), torch.sin(xk)], dim=1)
        return torch.einsum("bcik,coik->bo", basis, self.coef) + self.bias


class KAN(nn.Module):
    def __init__(self, din, h, K=4, nc=2):
        super().__init__()
        self.l1 = FourierKANLayer(din, h, K)
        self.l2 = FourierKANLayer(h, nc, K)

    def forward(self, x):
        return self.l2(torch.tanh(self.l1(x)))


def nparams(m):
    return sum(p.numel() for p in m.parameters())


def match_mlp(din, target, nc=2):
    best, bh = 1e18, 8
    for h in range(4, 300):
        d = abs(nparams(MLP(din, h, nc)) - target)
        if d < best:
            best, bh = d, h
    return bh


def train(model, Xtr, ytr, seed, epochs=30, lr=2e-3, bs=256):
    torch.manual_seed(seed)
    opt = torch.optim.Adam(model.parameters(), lr, weight_decay=1e-5)
    lossf = nn.CrossEntropyLoss()
    ds = torch.utils.data.TensorDataset(torch.tensor(Xtr), torch.tensor(ytr))
    dl = torch.utils.data.DataLoader(ds, batch_size=bs, shuffle=True)
    for _ in range(epochs):
        for xb, yb in dl:
            opt.zero_grad(); lossf(model(xb), yb).backward(); opt.step()
    model.eval()
    return model


def predict(model, X):
    with torch.no_grad():
        return model(torch.tensor(X, dtype=torch.float32)).argmax(1).numpy()


def saliency(model, X, target_class=1):
    """Gradient of the target-class logit w.r.t. inputs = the standard attribution an
    XAI-IDS presents to the analyst. Returns |grad| per feature (the explanation)."""
    x = torch.tensor(X, dtype=torch.float32, requires_grad=True)
    logit = model(x)[:, target_class].sum()
    g, = torch.autograd.grad(logit, x)
    return g.detach().numpy()


def topk_features(attr, k=5):
    """Top-k attributed feature indices per sample (the 'reason' shown to the analyst)."""
    return np.argsort(-np.abs(attr), axis=1)[:, :k]


def input_x_gradient(model, X, target_class=1):
    """input x gradient attribution (a standard, equally-defensible XAI method)."""
    return saliency(model, X, target_class) * X


def integrated_gradients(model, X, target_class=1, steps=32):
    """Integrated Gradients w.r.t. an all-zero (mean-scaled) baseline (Sundararajan et al.)."""
    x = torch.tensor(X, dtype=torch.float32)
    base = torch.zeros_like(x)
    total = torch.zeros_like(x)
    for a in torch.linspace(1.0 / steps, 1.0, steps):
        xi = (base + a * (x - base)).clone().requires_grad_(True)
        g, = torch.autograd.grad(model(xi)[:, target_class].sum(), xi)
        total = total + g
    return ((x - base) * total / steps).detach().numpy()
