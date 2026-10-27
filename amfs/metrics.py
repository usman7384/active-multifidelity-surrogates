"""Scores at each checkpoint, on a fixed high-fidelity test set."""
from __future__ import annotations

import numpy as np

from .calibration import crps_gaussian


def score(y: np.ndarray, mu: np.ndarray, sd: np.ndarray) -> dict:
    z = np.abs(y - mu) / sd
    return dict(rmse=float(np.sqrt(np.mean((mu - y) ** 2))),
                coverage95=float(np.mean(z <= 1.959964)),
                crps=float(np.mean(crps_gaussian(y, mu, sd))),
                mean_sd=float(np.mean(sd)),
                n_rows=int(len(y)))
