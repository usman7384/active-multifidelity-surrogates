"""How the next batch of solver runs is chosen.

Each strategy proposes a list of (case, fidelity) pairs given the evaluations so far and the current model, and
says which model it is meant to be paired with.

RandomLHS        the baseline: more Latin-hypercube cases at one fidelity. High fidelity is what forming-surrogates
                 did; low fidelity is the "just use cheap runs" competitor the fidelity study says to beat.
MaxVariance      active learning, first version: from a candidate pool, take the cases where the current GP is
                 most unsure (mean predictive sd over the three read-out reductions), keeping a minimum spacing so
                 a batch does not pile up in one spot.
MultiFidelity    cost-aware active learning over case AND fidelity, paired with the multi-fidelity GP.
"""
from __future__ import annotations

import numpy as np

from .design_space import READ_AT, candidate_pool, lhs_cases, rows_for, to_case, to_unit


def _spaced(order, U, k: int, min_dist: float, taken=()) -> list[int]:
    """Greedy pick of up to k indices in `order`, each at least min_dist (unit box) from the others."""
    chosen = list(taken)
    out = []
    for i in order:
        if all(np.linalg.norm(U[i] - U[j]) >= min_dist for j in chosen):
            chosen.append(int(i))
            out.append(int(i))
        if len(out) == k:
            break
    return out


class RandomLHS:
    name = "random_lhs"
    model = "single_fidelity"

    def __init__(self, fidelity: str = "high"):
        self.fidelity = fidelity

    def propose(self, evals, model, batch: int, round_idx: int, seed: int):
        return [(c, self.fidelity) for c in lhs_cases(batch, seed=seed * 1000 + round_idx)]


class MaxVariance:
    name = "max_variance"
    model = "single_fidelity"
    fidelity = "high"

    def __init__(self, pool: int = 2048, min_dist: float = 0.15):
        self.pool, self.min_dist = pool, min_dist

    def propose(self, evals, model, batch: int, round_idx: int, seed: int):
        C = candidate_pool(self.pool, seed=seed * 1000 + round_idx)
        _, sd = model.predict(rows_for(C))
        score = sd.reshape(len(READ_AT), len(C)).mean(0)
        return [(to_case(C[i]), "high") for i in _spaced(np.argsort(-score), to_unit(C), batch, self.min_dist)]


class MultiFidelity:
    """Cost-aware max-variance over (case, fidelity), for the autoregressive multi-fidelity GP.

    The predictive variance splits into rho^2 * var_low + var_delta. A low run at x mainly removes the first part
    near x; a high run (always paired with a low run at the same case, to keep the design nested) mainly
    removes the second. Score each candidate for each fidelity by the variance it would remove per solver second:

        score_low(x)  = rho^2 * var_low(x)  / cost_low
        score_high(x) = var_delta(x)        / (cost_high + cost_low)

    averaged over the three read-out reductions, with costs taken as the mean observed so far. The batch is the
    best `batch` (case, fidelity) choices across both lists, spaced as in MaxVariance within each fidelity.
    This is a heuristic proxy, not an exact variance-reduction calculation: it treats each run as removing the
    variance at its own location and ignores how far that reduction spreads. Upgrade: integrated variance
    reduction over a reference set.
    """
    name = "multi_fidelity"
    model = "multi_fidelity"
    fidelity = "low"

    def __init__(self, pool: int = 2048, min_dist: float = 0.15):
        self.pool, self.min_dist = pool, min_dist

    def propose(self, evals, model, batch: int, round_idx: int, seed: int):
        C = candidate_pool(self.pool, seed=seed * 1000 + round_idx)
        rho, sd_l, sd_d = model.components(rows_for(C))
        n = len(C)
        v_low = (rho ** 2 * sd_l ** 2).reshape(len(READ_AT), n).mean(0)
        v_delta = (sd_d ** 2).reshape(len(READ_AT), n).mean(0)
        cost = {f: np.mean([e.cost_s for e in evals if e.fidelity == f] or [np.nan]) for f in ("low", "high")}
        c_low = cost["low"] if np.isfinite(cost["low"]) else 1.0
        c_high = cost["high"] if np.isfinite(cost["high"]) else 10.0 * c_low
        s_low, s_high = v_low / c_low, v_delta / (c_high + c_low)
        U = to_unit(C)
        cand = sorted([(s, i, "low") for i, s in enumerate(s_low)] + [(s, i, "high") for i, s in enumerate(s_high)],
                      reverse=True)
        picked = {"low": [], "high": []}
        out = []
        for s, i, f in cand:
            if all(np.linalg.norm(U[i] - U[j]) >= self.min_dist for j in picked[f]):
                picked[f].append(i)
                out.append((to_case(C[i]), f))
                if f == "high":
                    out.append((to_case(C[i]), "low"))      # nested design: the high case also gets a low run
            if len(picked["low"]) + len(picked["high"]) == batch:
                break
        return out


STRATEGIES = {s.name: s for s in (RandomLHS, MaxVariance, MultiFidelity)}
