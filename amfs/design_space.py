"""The input box and how cases are sampled from it."""
from __future__ import annotations

import numpy as np
from scipy.stats import qmc

CASE_KEYS = ("od_id", "h_id", "mf", "m")
CASE_LO = np.array([1.6, 0.4, 0.0, 0.05])
CASE_HI = np.array([2.4, 1.0, 1.0, 0.30])
READ_AT = (0.10, 0.20, 0.30)   # reductions at which each run is read
RUN_TO = 0.305                 # every run is pressed to just past the last read


def lhs_cases(n: int, seed: int) -> list[dict]:
    u = qmc.LatinHypercube(d=len(CASE_KEYS), seed=seed).random(n)
    return [to_case(row) for row in qmc.scale(u, CASE_LO, CASE_HI)]


def candidate_pool(n: int, seed: int) -> np.ndarray:
    u = qmc.Sobol(d=len(CASE_KEYS), scramble=True, seed=seed).random(n)
    return qmc.scale(u, CASE_LO, CASE_HI)


def to_case(row) -> dict:
    return {k: float(v) for k, v in zip(CASE_KEYS, row)}


def case_array(cases: list[dict]) -> np.ndarray:
    return np.array([[c[k] for k in CASE_KEYS] for c in cases], float)


def to_unit(X: np.ndarray) -> np.ndarray:
    return (np.asarray(X, float) - CASE_LO) / (CASE_HI - CASE_LO)


def rows_for(case_rows: np.ndarray) -> np.ndarray:
    """(n, 4) cases -> (3n, 5) model inputs, one row per read-out reduction."""
    case_rows = np.atleast_2d(case_rows)
    return np.vstack([np.column_stack([case_rows, np.full(len(case_rows), r)]) for r in READ_AT])
