"""Offline: which correction (delta) model works, on the cached mf_lhs seed-0 data? No new solves.

Low GP fitted once (saved). Each variant fits only the correction on the ~31 fine runs. Scored two ways:
  test   - against the 40-run fine test set (what the loop reports)
  loro   - leave-one-fine-RUN-out on the training fine runs (usable inside the loop, no test leak)
"""
import datetime, glob, json, os, sys
import numpy as np
sys.path.insert(0, r"D:\Projects\active-multifidelity-surrogates")
os.chdir(r"D:\Projects\active-multifidelity-surrogates")
from amfs.design_space import lhs_cases, READ_AT
from amfs.gp import NumpyGP, fit_gp
from amfs.models import HI5, LO5, table
from amfs.oracle import Oracle

SCR = os.path.dirname(os.path.abspath(__file__))
MF, RED, M = 2, 4, 3                         # column indices: od_id h_id mf m reduction
rm = lambda e: float(np.sqrt(np.mean(np.square(e))))


def data():
    cfg = json.load(open("results/mf_lhs_seed0.json"))["config"]
    orc = Oracle("cache", cfg["fidelities"], 4, log=lambda *_: None)
    a = datetime.datetime(2026, 10, 28, 0, 22, 22).timestamp()
    new_high = [json.load(open(f))["case"] for f in glob.glob("cache/*.json")
                if os.path.getmtime(f) > a and json.load(open(f))["numerics"].get("nz") == 12]
    init = lhs_cases(60, seed=0)
    low = orc.query(init + sum((lhs_cases(100, seed=r + 1) for r in range(5)), []), "low")
    high = orc.query(init[:10] + new_high, "high")
    test = orc.query(lhs_cases(40, seed=12345), "high")
    return low, high, test


class Delta:
    """One correction variant: fit(Xh, r) on residuals r = y_high - mu_low(Xh); predict(X) -> (mu, sd)."""
    def __init__(self, kind, dims=None):
        self.kind, self.dims = kind, dims

    def fit(self, X, r):
        if self.kind == "none":
            self.s = 0.0
        elif self.kind == "const":
            self.c, self.s = r.mean(), r.std()
        elif self.kind == "linear":                  # 1, mf, red, mf*red
            A = self._A(X)
            self.w = np.linalg.lstsq(A, r, rcond=None)[0]
            self.s = float(np.std(r - A @ self.w) * np.sqrt(len(r) / max(1, len(r) - A.shape[1])))
        else:
            d = self.dims
            self.gp, _ = fit_gp(X[:, d], r, lo=LO5[d], hi=HI5[d], names=tuple(map(str, d)), n_restarts=2, iters=200)
        return self

    def _A(self, X):
        u = (X - LO5) / (HI5 - LO5)
        return np.column_stack([np.ones(len(X)), u[:, MF], u[:, RED], u[:, MF] * u[:, RED]])

    def predict(self, X):
        n = len(X)
        if self.kind == "none":
            return np.zeros(n), np.zeros(n)
        if self.kind == "const":
            return np.full(n, self.c), np.full(n, self.s)
        if self.kind == "linear":
            return self._A(X) @ self.w, np.full(n, self.s)
        return self.gp.predict(X[:, self.dims])


VARIANTS = {
    "none (cheap GP only)": lambda: Delta("none"),
    "constant bias": lambda: Delta("const"),
    "linear in mf, red": lambda: Delta("linear"),
    "GP on (mf, red)": lambda: Delta("gp", [MF, RED]),
    "GP on (mf, m, red)": lambda: Delta("gp", [MF, M, RED]),
    "GP on all 5 (current)": lambda: Delta("gp", [0, 1, 2, 3, 4]),
}


def main():
    low, high, test = data()
    Xl, yl = table(low, "low")
    path = os.path.join(SCR, "lowgp.npz")
    if os.path.exists(path):
        lgp = NumpyGP.load(path)
    else:
        lgp, _ = fit_gp(Xl, yl, lo=LO5, hi=HI5, n_restarts=2, iters=200)
        lgp.save(path)
    print(f"low rows {len(yl)}, fine runs {len(high)}")

    # residuals per fine run (rho = 1), grouped by run for leave-one-run-out
    runs = []
    for e in high:
        X, y = table([e], "high")
        if len(y):
            runs.append((X, y - lgp.predict(X, include_noise=False)[0]))
    Xh = np.vstack([x for x, _ in runs]); rh = np.concatenate([r for _, r in runs])
    Xt, yt = table(test, "high")
    mu_l, sd_l = lgp.predict(Xt)

    print(f"{'variant':24s} {'test rmse':>9s} {'cov95':>6s} {'loro rmse':>10s}")
    for name, make in VARIANTS.items():
        d = make().fit(Xh, rh)
        mu_d, sd_d = d.predict(Xt)
        mu, sd = mu_l + mu_d, np.sqrt(sd_l ** 2 + sd_d ** 2)
        cov = float(np.mean(np.abs(mu - yt) <= 1.96 * sd))
        errs = []
        for i, (Xi, ri) in enumerate(runs):                 # leave one fine run out
            Xo = np.vstack([x for j, (x, _) in enumerate(runs) if j != i])
            ro = np.concatenate([r for j, (_, r) in enumerate(runs) if j != i])
            errs.append(make().fit(Xo, ro).predict(Xi)[0] - ri)
        print(f"{name:24s} {rm(mu - yt):9.3f} {cov:6.2f} {rm(np.concatenate(errs)):10.3f}", flush=True)


if __name__ == "__main__":
    main()
