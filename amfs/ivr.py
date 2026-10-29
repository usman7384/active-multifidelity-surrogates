"""Integrated variance reduction: how much posterior variance a run would remove over a reference set."""
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
    """(covariance at R, noise variance) of the multi-fidelity correction."""
    if hasattr(delta, "gp"):
        return gp_cov(delta.gp, R[:, delta.dims]), delta.gp.noise * delta.gp.ysd ** 2
    A = delta._A(R)
    return delta.s ** 2 * A @ delta.P @ A.T, delta.s ** 2


class GreedyIVR:
    """Posterior covariance over [reference rows; candidate rows], downdated as runs are picked."""

    def __init__(self, S: np.ndarray, n_ref: int, n_cand: int, noise: float, n_read: int = 3):
        self.S = S
        self.nz = n_ref
        self.nc = n_cand
        self.noise = noise
        self.k = n_read

    def _idx(self, j):
        return self.nz + j + self.nc * np.arange(self.k)

    def reductions(self) -> np.ndarray:
        """Variance removed over the reference rows by a run at each candidate, given the picks so far."""
        idx = self.nz + np.arange(self.nc)[:, None] + self.nc * np.arange(self.k)[None, :]
        Scc = self.S[idx[:, :, None], idx[:, None, :]] + self.noise * np.eye(self.k)
        Szc = self.S[:self.nz][:, idx].transpose(1, 0, 2)
        L = np.linalg.cholesky(Scc + 1e-12 * np.eye(self.k))
        W = np.linalg.solve(L, Szc.transpose(0, 2, 1))
        return (W ** 2).sum((1, 2)) / self.nz

    def pick(self, j: int) -> None:
        i = self._idx(j)
        Sic = self.S[:, i].copy()
        Lc = np.linalg.cholesky(self.S[np.ix_(i, i)] + self.noise * np.eye(self.k))
        U = solve_triangular(Lc, Sic.T, lower=True)
        for a in range(0, len(self.S), 512):   # rank-k downdate in row blocks, in place
            self.S[a:a + 512] -= U[:, a:a + 512].T @ U
