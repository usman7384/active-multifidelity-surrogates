"""Surrogates fitted on whatever the oracle has returned so far.

SingleFidelityGP: the forming-surrogates GP (amfs/gp.py), fitted on one fidelity's rows (high by default).
MultiFidelityGP:  autoregressive two-level GP, f_high = rho * f_low + delta.
"""
from __future__ import annotations

import numpy as np

from .design_space import CASE_HI, CASE_LO, READ_AT, case_array, rows_for
from .gp import NumpyGP, fit_gp as _fit_gp, to_unit

MAX_FIT_ROWS = 1000      # hyper-parameters are learned on at most this many rows; the posterior uses all rows


def fit_gp(X, y, *, lo, hi, seed: int = 0, **kw):
    """amfs/gp.py's fit, made affordable for thousands of rows, applied the same way to every strategy.

    Up to MAX_FIT_ROWS rows: the plain exact fit. Above: the hyper-parameters (length scales, signal and noise
    variance, mean) are fitted on a random MAX_FIT_ROWS-row subsample, then the exact posterior is conditioned
    on every row with them. Hyper-parameters settle long before the data stop helping the posterior, and the
    fit's cost grows with the cube of its row count, so this keeps a refit to about a minute at any size.
    Exact Cholesky throughout (GPyTorch's default switches to approximate conjugate gradients above 800 rows).
    """
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
    for _ in range(6):                    # all rows: add jitter only if near-duplicate rows break the Cholesky
        try:
            full = NumpyGP(Xu=to_unit(X, lo, hi), y=y, ls=gp.ls, outputscale=gp.outputscale, noise=noise,
                           mean=gp.mean, lo=lo, hi=hi, names=gp.names)
            break
        except np.linalg.LinAlgError:
            noise *= 10
    info = dict(info, n_train=int(len(y)), n_hyper_fit=int(len(sub)), noise_used=float(noise))
    return full, info

LO5 = np.r_[CASE_LO, min(READ_AT)]
HI5 = np.r_[CASE_HI, max(READ_AT)]


def table(evals, fidelity: str | None = None) -> tuple[np.ndarray, np.ndarray]:
    """(X, y) training rows from evaluations, optionally one fidelity only; NaN rows (stopped runs) dropped."""
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
        self.fidelity, self.seed, self.iters, self.restarts = fidelity, seed, iters, restarts
        self.gp = None

    def fit(self, evals) -> "SingleFidelityGP":
        X, y = table(evals, self.fidelity)
        self.gp, self.info = fit_gp(X, y, lo=LO5, hi=HI5, seed=self.seed, n_restarts=self.restarts,
                                    iters=self.iters)
        return self

    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        return self.gp.predict(X)


class MultiFidelityGP:
    """Autoregressive two-level GP (Kennedy and O'Hagan, 2000):

        f_high(x) = rho * f_low(x) + delta(x)

    1. A GP on every low-fidelity row (cheap, many) gives mu_low, sd_low.
    2. rho by least squares of y_high on mu_low at the high-fidelity rows (with an intercept, which delta's
       constant mean then absorbs). A first version: the joint maximum-likelihood fit of rho is a later upgrade.
    3. A second GP, delta, on the residuals y_high - rho * mu_low(x) at the high rows (few, smooth: the fidelity
       study shows the coarse error is a slowly varying bias that grows with friction).

    Prediction: mean rho * mu_low + mu_delta, variance rho^2 * sd_low^2 + sd_delta^2. The low GP's uncertainty
    at the high rows is ignored when fitting delta, which is reasonable once the low data are dense there; the
    strategy keeps the design nested (every high run also gets a low run) so they are.
    With fewer than MIN_HIGH_ROWS high rows, rho = 1 and delta is skipped (the prediction is the low GP).

    Options: `rho` = "fit" (least squares, as above) or a fixed number; `delta` = "gp" (a GP on the input
    columns `delta_dims`, od_id h_id mf m reduction = 0..4) or "linear" (LinearDelta). The offline correction
    study on the cached seed-0 data found that with 20-30 random fine runs a linear delta (rho = 1) beats both
    a GP delta and no delta: test RMSE about 0.13 against 0.16-0.24, coverage about 0.98. A GP delta on all five
    inputs needs about 70 fine runs to win, and chases fold-over jumps when the fine runs sit in hard cases.
    """
    name = "mfgp_autoregressive"
    MIN_HIGH_ROWS = 4

    def __init__(self, seed: int = 0, iters: int = 300, restarts: int = 3, rho="fit", delta: str = "gp",
                 delta_dims=(0, 1, 2, 3, 4)):
        self.seed, self.iters, self.restarts = seed, iters, restarts
        self.rho_mode, self.delta_kind, self.dims = rho, delta, list(delta_dims)
        self.low = self.delta = None
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
            if self.delta_kind == "linear":
                self.delta = LinearDelta().fit(Xh, r)
            else:
                self.delta = _Columns(self.dims, *fit_gp(Xh[:, self.dims], r, **dict(
                    kw, lo=LO5[self.dims], hi=HI5[self.dims], names=tuple(map(str, self.dims)))))
                self.info["delta"] = self.delta.info
        self.info["rho"] = self.rho
        return self

    def components(self, X: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
        """(rho, sd_low, sd_delta) at X: the two parts of the predictive uncertainty, for the strategy.
        Latent only (no noise term): a new run cannot remove the noise floor, so it must not count as reducible."""
        _, sd_l = self.low.predict(X, include_noise=False)
        sd_d = self.delta.predict(X, include_noise=False)[1] if self.delta is not None else np.zeros(len(X))
        return self.rho, sd_l, sd_d

    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        mu_l, sd_l = self.low.predict(X)
        if self.delta is None:
            return mu_l, sd_l
        mu_d, sd_d = self.delta.predict(X)
        return self.rho * mu_l + mu_d, np.sqrt(self.rho ** 2 * sd_l ** 2 + sd_d ** 2)


class _Columns:
    """A GP fitted on some input columns, called with all five."""
    def __init__(self, dims, gp, info):
        self.dims, self.gp, self.info = dims, gp, info

    def predict(self, X, include_noise: bool = True):
        return self.gp.predict(X[:, self.dims], include_noise=include_noise)


class LinearDelta:
    """delta(x) = w0 + w1 mf + w2 r + w3 mf r (unit-box friction mf and reduction r), by least squares.
    The fidelity study's coarse bias is a smooth function of friction and reduction, so four numbers capture it;
    the uncertainty is the residual sd (constant)."""
    MF, RED = 2, 4

    def _A(self, X):
        u = (X - LO5) / (HI5 - LO5)
        return np.column_stack([np.ones(len(X)), u[:, self.MF], u[:, self.RED], u[:, self.MF] * u[:, self.RED]])

    def __init__(self, robust: bool = True):
        self.robust = robust

    def fit(self, X, r):
        A = self._A(X)
        wts = np.ones(len(r))
        for _ in range(30 if self.robust else 1):         # Huber IRLS (c = 1.345 robust sd); 1 pass = least squares
            sw = np.sqrt(wts)
            self.w = np.linalg.lstsq(A * sw[:, None], r * sw, rcond=None)[0]
            e = r - A @ self.w
            scale = 1.4826 * np.median(np.abs(e - np.median(e))) + 1e-9
            wts = np.minimum(1.0, 1.345 * scale / np.maximum(np.abs(e), 1e-12))
        e = r - A @ self.w
        dof = np.sqrt(len(r) / max(1, len(r) - A.shape[1]))
        # robust: the spread of the typical residual, so a fold-over outlier does not widen every interval
        spread = 1.4826 * np.median(np.abs(e - np.median(e))) if self.robust else np.std(e)
        self.s = float(spread * dof)
        return self

    def predict(self, X, include_noise: bool = True):
        return self._A(X) @ self.w, np.full(len(X), self.s)


def make_model(kind: str, fidelity: str, seed: int, gp_args: dict, mf_args: dict | None = None):
    if kind == "multi_fidelity":
        return MultiFidelityGP(seed=seed, **gp_args, **(mf_args or {}))
    return SingleFidelityGP(fidelity=fidelity, seed=seed, **gp_args)
