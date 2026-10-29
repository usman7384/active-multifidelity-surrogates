"""Scores on the fixed high-fidelity test set."""
from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm


def crps_gaussian(y, mu, sd) -> np.ndarray:
    z = (np.asarray(y) - mu) / sd
    return sd * (z * (2 * norm.cdf(z) - 1) + 2 * norm.pdf(z) - 1 / math.sqrt(math.pi))


def score(y: np.ndarray, mu: np.ndarray, sd: np.ndarray) -> dict:
    z = np.abs(y - mu) / sd
    return dict(rmse=float(np.sqrt(np.mean((mu - y) ** 2))),
                coverage95=float(np.mean(z <= 1.959964)),
                crps=float(np.mean(crps_gaussian(y, mu, sd))),
                mean_sd=float(np.mean(sd)),
                n_rows=int(len(y)))
