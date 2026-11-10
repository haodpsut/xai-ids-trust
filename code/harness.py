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
        self.coef = nn.Parameter(torch.empty(2, dout, din, K))
        self.bias = nn.Parameter(torch.empty(dout))
        self.reset_parameters()

    def reset_parameters(self):
        # ⛔ Phep khoi tao phai nam o MOT ham goi lai duoc, khong nam trong `__init__`.
        # Khong the thi `gieo_lai()` khong cach nao dat lai trong so cua lop nay, va
        # `nparams()`/`match_mlp()` (dung gan 300 MLP) da keo RNG toan cuc di truoc do.
        with torch.no_grad():
            self.coef.copy_(0.1 * torch.randn(2, self.dout, self.din, self.K)
                            / (self.din * self.K) ** 0.5)
            self.bias.zero_()

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


def gieo_lai(model, seed):
    """Gieo RNG roi KHOI TAO LAI moi tham so, nen trong so chi phu thuoc `seed`.

    ⛔⛔ Vi sao can. Truoc 10/11/2026 `train()` goi `torch.manual_seed(seed)` nhung
    mo hinh da duoc DUNG XONG tu truoc do o phia goi (`train(MLP(din, ...), ...)`),
    nen trong so khoi tao lay tu RNG toan cuc CHUA GIEO: `torch.initial_seed()` do
    duoc la mot so KHAC NHAU moi tien trinh. Hau qua: hai luot chay lien nhau cung
    mot ma cho `analyst_benign_before` = 0,037 roi 0,014; va toi da quy 21/24 CSV
    khong tai lap duoc cho kien truc CPU va BLAS, trong khi phan lon la do khoi tao
    chua gieo. Ghim luong khong chua duoc gi, va dung la no khong chua duoc gi.
    ⇒ [[feedback-do-loi-cho-ban-va-chua-tach-nguon]] · [[feedback-moi-truong-chay-la-phan-cua-hien-vat]]

    Va o day, trong `train`, chu khong o 23 tep goi: mot dinh nghia dat o cho ma
    moi duong di deu phai qua thi khong co duong di nao thieu no.
    ⇒ [[feedback-tu-khoa-khop-vao-ben-trong-tu-khac]]
    """
    torch.manual_seed(seed)
    phu = set()
    for m in model.modules():
        if hasattr(m, "reset_parameters"):
            m.reset_parameters()
            phu |= {id(p) for p in m.parameters(recurse=False)}
    # ⛔ Mot tham so khong module nao dat lai duoc thi van giu gia tri tu RNG chua
    # gieo, va ca ham nay thanh mot dam bao GIA. Phai NEM, khong duoc im lang.
    # ⇒ [[feedback-kiem-0-don-vi-khong-phai-sach]]
    sot = [n for n, p in model.named_parameters() if id(p) not in phu]
    if sot:
        raise RuntimeError(f"gieo_lai: {len(sot)} tham so khong gieo lai duoc: {sot[:5]}")
    return model


def train(model, Xtr, ytr, seed, epochs=30, lr=2e-3, bs=256):
    gieo_lai(model, seed)
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


def flow_bao_dong(mo_hinh, Xte, yte, n=None, mat_na=False, du_doan=None):
    """The one definition of the flow population every explanation measure runs on.

    Returns the indices of flows that are genuine attacks (`yte == 1`) and that every
    model in `mo_hinh` flags as attacks. That is exactly the set an analyst looks at
    when an alarm fires, which is the set this paper's argument is about.

    Accepts a single model or a list, and both the torch models in this file and the
    scikit-learn detectors used for the tree ensembles. `n` caps the sample; the cap
    is the caller's choice, the population is not.

    This exists because the same expression had been retyped in seventeen scripts
    with four different caps, and two of them had drifted to `Xte[:N]`, the first N
    test flows including benign ones. A definition copied seventeen times diverges
    eventually; that is a property of the copying, not an accident. One caller
    measured P2 on alarms and P3 on the first thousand flows, in the same file, and
    the paper printed both side by side.
    """
    if du_doan is not None:
        # Cho nhung noi co bo do RIENG (vi du exp_sparse_bydesign.py dung
        # `predict_sparse(kind, m, i, X)`), nen khong truyen mo hinh vao duoc. Dua
        # thang ma tran du doan [n, K] vao de VAN dung MOT dinh nghia quan the.
        p = np.asarray(du_doan)
        if p.ndim == 1:
            p = p[:, None]
    else:
        ds = mo_hinh if isinstance(mo_hinh, (list, tuple)) else [mo_hinh]
        cot = []
        for m in ds:
            if isinstance(m, torch.nn.Module):
                cot.append(predict(m, Xte))
            elif hasattr(m, "predict"):
                cot.append(np.asarray(m.predict(Xte)))
            else:
                raise TypeError(f"flow_bao_dong: khong biet du doan bang {type(m)!r}")
        p = np.stack(cot, 1)
    co = (np.asarray(yte) == 1) & (p == 1).all(1)
    if mat_na:
        # ⛔ Mot so noi can MAT NA boolean chu khong phai chi so, vi chung con AND
        # tiep voi dieu kien khac (`tp & (types == t)`) hoac goi `tp.sum()`. Dua chi
        # so vao nhung cho ay thi `&` tro thanh phep AND BIT tren so nguyen va nem
        # ValueError ve hinh dang - dung cai da xay ra ngay 10/11/2026 khi toi thay
        # may moc 4 cho dang mat na bang dang chi so ma khong doc tung cho.
        if n is not None:
            raise ValueError("flow_bao_dong: mat_na=True thi khong dung n")
        return co
    idx = np.where(co)[0]
    return idx if n is None else idx[:n]


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
