"""Surrogates fitted on whatever the oracle has returned so far.

SingleFidelityGP: the forming-surrogates GP (amfs/gp.py), fitted on one fidelity's rows (high by default).
MultiFidelityGP:  autoregressive two-level GP, f_high = rho * f_low + delta.
"""
from __future__ import annotations

import numpy as np

from .design_space import CASE_HI, CASE_LO, READ_AT, case_array, rows_for
from .gp import fit_gp

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
    """
    name = "mfgp_autoregressive"
    MIN_HIGH_ROWS = 4

    def __init__(self, seed: int = 0, iters: int = 300, restarts: int = 3):
        self.seed, self.iters, self.restarts = seed, iters, restarts
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
            A = np.column_stack([mu_l, np.ones_like(mu_l)])
            self.rho = float(np.linalg.lstsq(A, yh, rcond=None)[0][0])
            self.delta, self.info["delta"] = fit_gp(Xh, yh - self.rho * mu_l, **kw)
        self.info["rho"] = self.rho
        return self

    def components(self, X: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
        """(rho, sd_low, sd_delta) at X: the two parts of the predictive uncertainty, for the strategy."""
        _, sd_l = self.low.predict(X)
        sd_d = self.delta.predict(X)[1] if self.delta is not None else np.zeros(len(X))
        return self.rho, sd_l, sd_d

    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        mu_l, sd_l = self.low.predict(X)
        if self.delta is None:
            return mu_l, sd_l
        mu_d, sd_d = self.delta.predict(X)
        return self.rho * mu_l + mu_d, np.sqrt(self.rho ** 2 * sd_l ** 2 + sd_d ** 2)


def make_model(kind: str, fidelity: str, seed: int, gp_args: dict):
    if kind == "multi_fidelity":
        return MultiFidelityGP(seed=seed, **gp_args)
    return SingleFidelityGP(fidelity=fidelity, seed=seed, **gp_args)
