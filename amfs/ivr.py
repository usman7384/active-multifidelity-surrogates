"""Integrated variance reduction (IVR) for the multi-fidelity GP: which runs remove the most predictive variance,
averaged over a reference set of cases, per solver second.

A GP's posterior covariance does not depend on the observed values, so the effect of a run on the variance
everywhere is known before it is solved. For a candidate case c (its three read-out rows) and reference rows Z:

    reduction(c) = sum_z  S[z, c] (S[c, c] + noise I)^-1 S[c, z]

where S is the current posterior covariance. Picking c updates S exactly (a rank-3 downdate), so a batch is
built greedily without refitting: each pick sees the variance the earlier picks will remove.

The multi-fidelity GP's variance is rho^2 var_low + var_delta. A cheap run at c reduces the low part; a fine run
at c (always paired with a cheap run, to keep the design nested) reduces the delta part and the low part.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import solve_triangular

from .gp import matern52, to_unit


def gp_cov(gp, R: np.ndarray) -> np.ndarray:
    """Posterior latent covariance of a NumpyGP at rows R, in target units squared."""
    Ru = to_unit(R, gp.lo, gp.hi)
    v = solve_triangular(gp._L, matern52(gp.Xu, Ru, gp.ls, gp.outputscale), lower=True)
    return (matern52(Ru, Ru, gp.ls, gp.outputscale) - v.T @ v) * gp.ysd ** 2


def delta_cov(delta, R: np.ndarray):
    """(covariance at R, observation noise variance) of the multi-fidelity GP's correction."""
    if hasattr(delta, "gp"):                                      # GP correction on some input columns
        return gp_cov(delta.gp, R[:, delta.dims]), delta.gp.noise * delta.gp.ysd ** 2
    A = delta._A(R)                                               # linear correction: Bayesian weights
    return delta.s ** 2 * A @ delta.P @ A.T, delta.s ** 2


class GreedyIVR:
    """Posterior covariance over [reference rows; candidate rows], downdated as runs are picked."""

    def __init__(self, S: np.ndarray, n_ref: int, n_cand: int, noise: float, n_read: int = 3):
        self.S, self.nz, self.nc, self.noise, self.k = S, n_ref, n_cand, noise, n_read

    def _idx(self, j):
        return self.nz + j + self.nc * np.arange(self.k)               # rows_for stacks one block per reduction

    def reductions(self) -> np.ndarray:
        """Variance removed over the reference rows by a run at each candidate case, given the picks so far."""
        idx = self.nz + np.arange(self.nc)[:, None] + self.nc * np.arange(self.k)[None, :]   # (nc, k)
        Scc = self.S[idx[:, :, None], idx[:, None, :]] + self.noise * np.eye(self.k)         # (nc, k, k)
        Szc = self.S[:self.nz][:, idx].transpose(1, 0, 2)                                    # (nc, nz, k)
        L = np.linalg.cholesky(Scc + 1e-12 * np.eye(self.k))
        W = np.linalg.solve(L, Szc.transpose(0, 2, 1))                                       # (nc, k, nz)
        return (W ** 2).sum((1, 2)) / self.nz

    def pick(self, j: int) -> None:
        i = self._idx(j)
        Sic = self.S[:, i].copy()
        Lc = np.linalg.cholesky(self.S[np.ix_(i, i)] + self.noise * np.eye(self.k))
        U = solve_triangular(Lc, Sic.T, lower=True)               # (k, n): S -= U^T U, rank-k, in place
        for a in range(0, len(self.S), 512):                      # in row blocks: no n x n temporaries
            self.S[a:a + 512] -= U[:, a:a + 512].T @ U
