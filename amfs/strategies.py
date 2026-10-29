"""How the next batch of solver runs is chosen: each strategy proposes (case, fidelity) pairs."""
from __future__ import annotations

import numpy as np

from .design_space import READ_AT, candidate_pool, case_array, lhs_cases, rows_for, to_case, to_unit


def _spaced(order, U, k: int, min_dist: float) -> list[int]:
    """Up to k indices in order, each at least min_dist (unit box) from the others."""
    chosen = []
    for i in order:
        if all(np.linalg.norm(U[i] - U[j]) >= min_dist for j in chosen):
            chosen.append(int(i))
        if len(chosen) == k:
            break
    return chosen


def _mean_costs(evals) -> tuple[float, float]:
    low = [e.cost_s for e in evals if e.fidelity == "low"]
    high = [e.cost_s for e in evals if e.fidelity == "high"]
    c_low = float(np.mean(low)) if low else 1.0
    c_high = float(np.mean(high)) if high else 10.0 * c_low
    return c_low, c_high


class RandomLHS:
    """A fresh Latin hypercube each round at one fidelity."""
    name = "random_lhs"
    model = "single_fidelity"

    def __init__(self, fidelity: str = "high"):
        self.fidelity = fidelity

    def propose(self, evals, model, batch: int, round_idx: int, seed: int):
        cases = lhs_cases(batch, seed=seed * 1000 + round_idx + 1)
        return [(c, self.fidelity) for c in cases]


class MaxVariance:
    """Fine runs where the GP is most unsure, with a minimum spacing."""
    name = "max_variance"
    model = "single_fidelity"
    fidelity = "high"

    def __init__(self, pool: int = 2048, min_dist: float = 0.15):
        self.pool = pool
        self.min_dist = min_dist

    def propose(self, evals, model, batch: int, round_idx: int, seed: int):
        C = candidate_pool(self.pool, seed=seed * 1000 + round_idx)
        _, sd = model.predict(rows_for(C))
        score = sd.reshape(len(READ_AT), len(C)).mean(0)
        picks = _spaced(np.argsort(-score), to_unit(C), batch, self.min_dist)
        return [(to_case(C[i]), "high") for i in picks]


class MultiFidelityLHS:
    """Latin-hypercube cheap runs plus a fixed share of solver time on fine runs at some of them."""
    name = "mf_lhs"
    model = "multi_fidelity"
    fidelity = "low"

    def __init__(self, high_share: float = 0.3, high_pick: str = "random"):
        self.high_share = high_share
        self.high_pick = high_pick

    def propose(self, evals, model, batch: int, round_idx: int, seed: int):
        cases = lhs_cases(batch, seed=seed * 1000 + round_idx + 1)
        c_low, c_high = _mean_costs(evals)
        share = self.high_share / (1 - self.high_share)
        n_high = max(1, int(round(share * batch * c_low / c_high)))
        if self.high_pick == "random":
            top = range(n_high)
        else:
            _, _, sd_d = model.components(rows_for(case_array(cases)))
            v_delta = (sd_d ** 2).reshape(len(READ_AT), len(cases)).mean(0)
            top = np.argsort(-v_delta)[:n_high]
        return [(c, "low") for c in cases] + [(cases[i], "high") for i in top]


class MultiFidelityIVR:
    """Greedy integrated variance reduction per CPU second over case and fidelity (amfs/ivr.py).

    min_high_share is a floor on the share of each round's CPU seconds spent on fine runs.
    """
    name = "mf_ivr"
    model = "multi_fidelity"
    fidelity = "low"

    def __init__(self, pool: int = 1024, n_ref: int = 300, round_s: float = 600.0,
                 min_high_share: float = 0.0):
        self.pool = pool
        self.n_ref = n_ref
        self.round_s = round_s
        self.min_high_share = min_high_share

    def propose(self, evals, model, batch: int, round_idx: int, seed: int):
        from .ivr import GreedyIVR, delta_cov, gp_cov

        C = candidate_pool(self.pool, seed=seed * 1000 + 500 + round_idx)
        Z = candidate_pool(self.n_ref, seed=seed * 1000 + 999)
        R = np.vstack([rows_for(Z), rows_for(C)])
        nz, nc = len(READ_AT) * len(Z), len(C)
        low = GreedyIVR(gp_cov(model.low, R), nz, nc, model.low.noise * model.low.ysd ** 2)
        dlt = None
        if model.delta is not None:
            S_d, noise_d = delta_cov(model.delta, R)
            dlt = GreedyIVR(S_d, nz, nc, noise_d)
        c_low, c_high = _mean_costs(evals)
        rho2 = model.rho ** 2
        has_low = np.zeros(nc, bool)
        has_high = np.zeros(nc, bool)
        out = []
        spent = 0.0
        spent_high = 0.0

        def scores():
            r_low = rho2 * low.reductions()
            r_dlt = dlt.reductions() if dlt is not None else np.zeros(nc)
            s_low = np.where(has_low, -np.inf, r_low / c_low)
            extra = np.where(has_low, 0.0, c_low)
            gain_high = r_dlt + np.where(has_low, 0.0, r_low)
            s_high = np.where(has_high | (dlt is None), -np.inf, gain_high / (c_high + extra))
            return s_low, s_high

        def pick_low(j):
            nonlocal spent
            low.pick(j)
            has_low[j] = True
            out.append((to_case(C[j]), "low"))
            spent += c_low

        def pick_high(j):
            nonlocal spent, spent_high
            if not has_low[j]:
                pick_low(j)   # keep the design nested
            dlt.pick(j)
            has_high[j] = True
            out.append((to_case(C[j]), "high"))
            spent += c_high
            spent_high += c_high

        while spent < self.round_s and not has_low.all():
            s_low, s_high = scores()
            j_l, j_h = int(np.argmax(s_low)), int(np.argmax(s_high))
            if s_high[j_h] > s_low[j_l]:
                pick_high(j_h)
            else:
                pick_low(j_l)
        while dlt is not None and spent_high < self.min_high_share * spent and not has_high.all():
            pick_high(int(np.argmax(scores()[1])))
        return out


STRATEGIES = {s.name: s for s in (RandomLHS, MaxVariance, MultiFidelityLHS, MultiFidelityIVR)}
