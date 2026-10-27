"""Surrogates fitted on whatever the oracle has returned so far.

SingleFidelityGP: the forming-surrogates GP (amfs/gp.py), fitted on high-fidelity rows only.
MultiFidelityGP:  not built yet; the plan is in its docstring.
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
    name = "gp_high_only"

    def __init__(self, seed: int = 0, iters: int = 300, restarts: int = 3):
        self.seed, self.iters, self.restarts = seed, iters, restarts
        self.gp = None

    def fit(self, evals) -> "SingleFidelityGP":
        X, y = table(evals, "high")
        self.gp, self.info = fit_gp(X, y, lo=LO5, hi=HI5, seed=self.seed, n_restarts=self.restarts,
                                    iters=self.iters)
        return self

    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        return self.gp.predict(X)


class MultiFidelityGP:
    """Autoregressive multi-fidelity GP (Kennedy and O'Hagan, 2000), planned next.

        f_high(x) = rho * f_low(x) + delta(x)

    Fit a GP to all low-fidelity rows (cheap, many), then a second GP delta to the residuals
    y_high - rho * mu_low(x) at the high-fidelity rows (few), with rho fitted jointly (or by least squares as a
    first version). Prediction: mean rho * mu_low + mu_delta, variance rho^2 * var_low + var_delta.
    Needs high-fidelity rows to be a subset of low-fidelity cases (nested design) for the simple version.
    """
    name = "mfgp_autoregressive"

    def fit(self, evals):
        raise NotImplementedError("next step: see the class docstring")

    def predict(self, X):
        raise NotImplementedError
