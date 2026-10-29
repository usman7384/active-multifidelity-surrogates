"""Surrogates: a single-fidelity GP and an autoregressive multi-fidelity GP, f_high = rho * f_low + delta."""
from __future__ import annotations

import numpy as np

from .design_space import CASE_HI, CASE_LO, READ_AT, case_array, rows_for
from .gp import NumpyGP, fit_gp as _fit_gp, to_unit

MAX_FIT_ROWS = 1000   # hyper-parameters are fitted on at most this many rows; the posterior uses all

LO5 = np.r_[CASE_LO, min(READ_AT)]
HI5 = np.r_[CASE_HI, max(READ_AT)]


def fit_gp(X, y, *, lo, hi, seed: int = 0, **kw):
    """Exact GP fit; above MAX_FIT_ROWS the hyper-parameters come from a random subsample."""
    import gpytorch
    X, y = np.asarray(X, float), np.asarray(y, float)
    sub = np.arange(len(y))
    if len(y) > MAX_FIT_ROWS:
        sub = np.sort(np.random.default_rng(seed).choice(len(y), MAX_FIT_ROWS, replace=False))
    with gpytorch.settings.max_cholesky_size(20000):
        gp, info = _fit_gp(X[sub], y[sub], lo=lo, hi=hi, seed=seed, **kw)
    if len(sub) == len(y):
        return gp, info
    noise = gp.noise
    for _ in range(6):   # more jitter only if near-duplicate rows break the Cholesky
        try:
            full = NumpyGP(Xu=to_unit(X, lo, hi), y=y, ls=gp.ls, outputscale=gp.outputscale,
                           noise=noise, mean=gp.mean, lo=lo, hi=hi, names=gp.names)
            break
        except np.linalg.LinAlgError:
            noise *= 10
    info = dict(info, n_train=int(len(y)), n_hyper_fit=int(len(sub)), noise_used=float(noise))
    return full, info


def table(evals, fidelity: str | None = None) -> tuple[np.ndarray, np.ndarray]:
    """(X, y) training rows from evaluations, one fidelity if given; NaN rows dropped."""
    ev = [e for e in evals if fidelity is None or e.fidelity == fidelity]
    if not ev:
        return np.empty((0, 5)), np.empty(0)
    X = rows_for(case_array([e.case for e in ev]))
    y = np.concatenate([[e.y[k] for e in ev] for k in range(len(READ_AT))])
    keep = np.isfinite(y)
    return X[keep], y[keep]


class SingleFidelityGP:
    name = "gp_single_fidelity"

    def __init__(self, fidelity: str = "high", seed: int = 0, iters: int = 300, restarts: int = 3):
        self.fidelity = fidelity
        self.seed = seed
        self.iters = iters
        self.restarts = restarts
        self.gp = None

    def fit(self, evals) -> "SingleFidelityGP":
        X, y = table(evals, self.fidelity)
        self.gp, self.info = fit_gp(X, y, lo=LO5, hi=HI5, seed=self.seed, n_restarts=self.restarts,
                                    iters=self.iters)
        return self

    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        return self.gp.predict(X)


class MultiFidelityGP:
    """A GP on the cheap rows plus a correction delta fitted to the fine rows' residuals.

    rho is "fit" (least squares) or a number. delta is "gp", "linear" (LinearDelta) or "auto",
    which picks between the two by cross-validation over the fine runs at every fit.
    """
    name = "mfgp_autoregressive"
    MIN_HIGH_ROWS = 4
    CV_FOLDS = 5
    CV_MIN_RUNS = 10

    def __init__(self, seed: int = 0, iters: int = 300, restarts: int = 3, rho="fit", delta: str = "gp",
                 delta_dims=(0, 1, 2, 3, 4)):
        self.seed = seed
        self.iters = iters
        self.restarts = restarts
        self.rho_mode = rho
        self.delta_kind = delta
        self.dims = list(delta_dims)
        self.low = None
        self.delta = None
        self.rho = 1.0

    def fit(self, evals) -> "MultiFidelityGP":
        return self.fit_arrays(*table(evals, "low"), *table(evals, "high"))

    def fit_arrays(self, Xl, yl, Xh, yh) -> "MultiFidelityGP":
        kw = dict(lo=LO5, hi=HI5, seed=self.seed, n_restarts=self.restarts, iters=self.iters)
        self.low, info_low = fit_gp(Xl, yl, **kw)
        self.info = dict(low=info_low, n_low=int(len(yl)), n_high=int(len(yh)))
        self.rho, self.delta = 1.0, None
        if len(yh) >= self.MIN_HIGH_ROWS:
            mu_l, _ = self.low.predict(Xh, include_noise=False)
            if self.rho_mode == "fit":
                A = np.column_stack([mu_l, np.ones_like(mu_l)])
                self.rho = float(np.linalg.lstsq(A, yh, rcond=None)[0][0])
            else:
                self.rho = float(self.rho_mode)
            r = yh - self.rho * mu_l
            kind = self.delta_kind if self.delta_kind != "auto" else self._choose(Xh, r, kw)
            self.delta = self._fit_delta(kind, Xh, r, kw)
            self.info["delta_kind"] = self.delta_choice = kind
            if kind == "gp":
                self.info["delta"] = self.delta.info
        self.info["rho"] = self.rho
        return self

    def _fit_delta(self, kind, X, r, kw):
        if kind == "linear":
            return LinearDelta().fit(X, r)
        d = self.dims
        gp, info = fit_gp(X[:, d], r, **dict(kw, lo=LO5[d], hi=HI5[d], names=tuple(map(str, d))))
        return _Columns(d, gp, info)

    def _choose(self, Xh, r, kw) -> str:
        """Cross-validated RMSE of each delta kind over the fine runs; the lower wins, ties to linear."""
        _, run = np.unique(np.round(Xh[:, :4], 9), axis=0, return_inverse=True)
        run = run.ravel()
        n_runs = run.max() + 1
        if n_runs < self.CV_MIN_RUNS:
            self.info["delta_cv"] = None
            return "linear"
        fold = np.random.default_rng(self.seed).permutation(n_runs) % self.CV_FOLDS
        err = {"linear": [], "gp": []}
        for k in range(self.CV_FOLDS):
            te = fold[run] == k
            for kind in err:
                delta = self._fit_delta(kind, Xh[~te], r[~te], dict(kw, n_restarts=1))
                err[kind].append(delta.predict(Xh[te])[0] - r[te])
        cv = {k: float(np.sqrt(np.mean(np.concatenate(v) ** 2))) for k, v in err.items()}
        self.info["delta_cv"] = cv
        return "gp" if cv["gp"] < cv["linear"] else "linear"

    def components(self, X: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
        """(rho, sd_low, sd_delta) at X, without noise: a run cannot remove the noise floor."""
        _, sd_l = self.low.predict(X, include_noise=False)
        if self.delta is None:
            return self.rho, sd_l, np.zeros(len(X))
        return self.rho, sd_l, self.delta.predict(X, include_noise=False)[1]

    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        mu_l, sd_l = self.low.predict(X)
        if self.delta is None:
            return mu_l, sd_l
        mu_d, sd_d = self.delta.predict(X)
        return self.rho * mu_l + mu_d, np.sqrt(self.rho ** 2 * sd_l ** 2 + sd_d ** 2)


class _Columns:
    """A GP fitted on some input columns, called with all five."""

    def __init__(self, dims, gp, info):
        self.dims = dims
        self.gp = gp
        self.info = info

    def predict(self, X, include_noise: bool = True):
        return self.gp.predict(X[:, self.dims], include_noise=include_noise)


class LinearDelta:
    """delta = w0 + w1 mf + w2 r + w3 mf r in the unit box, by Huber-weighted least squares."""
    MF, RED = 2, 4

    def _A(self, X):
        u = (X - LO5) / (HI5 - LO5)
        mf, red = u[:, self.MF], u[:, self.RED]
        return np.column_stack([np.ones(len(X)), mf, red, mf * red])

    def fit(self, X, r):
        A = self._A(X)
        wts = np.ones(len(r))
        for _ in range(30):
            sw = np.sqrt(wts)
            self.w = np.linalg.lstsq(A * sw[:, None], r * sw, rcond=None)[0]
            e = r - A @ self.w
            scale = 1.4826 * np.median(np.abs(e - np.median(e))) + 1e-9
            wts = np.minimum(1.0, 1.345 * scale / np.maximum(np.abs(e), 1e-12))
        e = r - A @ self.w
        self.P = np.linalg.pinv((A * wts[:, None]).T @ A)   # weight covariance over s^2, for IVR
        dof = np.sqrt(len(r) / max(1, len(r) - A.shape[1]))
        spread = 1.4826 * np.median(np.abs(e - np.median(e)))   # robust to fold-over outliers
        self.s = float(spread * dof)
        return self

    def predict(self, X, include_noise: bool = True):
        return self._A(X) @ self.w, np.full(len(X), self.s)


def make_model(kind: str, fidelity: str, seed: int, gp_args: dict, mf_args: dict | None = None):
    if kind == "multi_fidelity":
        return MultiFidelityGP(seed=seed, **gp_args, **(mf_args or {}))
    return SingleFidelityGP(fidelity=fidelity, seed=seed, **gp_args)
