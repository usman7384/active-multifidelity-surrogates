"""How the next batch of solver runs is chosen.

Each strategy proposes a list of (case, fidelity) pairs given the evaluations so far and the current model, and
says which model it is meant to be paired with.

RandomLHS         more Latin-hypercube cases at one fidelity (fine: random_lhs; cheap: low_only).
MaxVariance       active learning: fine runs where the current GP is most unsure, with a minimum spacing.
MultiFidelityLHS  Latin-hypercube cheap runs plus a fixed share of solver time on fine runs; multi-fidelity GP.
MultiFidelityIVR  active learning over case AND fidelity by integrated variance reduction per CPU second.
"""
from __future__ import annotations

import numpy as np

from .design_space import READ_AT, candidate_pool, case_array, lhs_cases, rows_for, to_case, to_unit


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
        # + 1: round 0 must not reuse the initial design's seed (same seed and size give the same cases)
        return [(c, self.fidelity) for c in lhs_cases(batch, seed=seed * 1000 + round_idx + 1)]


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


class MultiFidelityLHS:
    """Space-filling cheap runs plus a fixed share of solver time on fine runs.

        low runs:  `batch` fresh Latin-hypercube cases per round, as low_only
        high runs: about `high_share` of the round's solver seconds, on cases of this round's low batch
                   (nested for free). high_pick = "random" takes the first of them (a random subset of a
                   Latin hypercube); "variance" takes those with the largest var_delta.

    Random fine runs keep the correction representative: fine runs picked by variance sit in the hardest cases
    and teach the correction a bias the rest of the space does not have.

    n_high * (cost_high + cost_low) = high_share * round spend, with costs the mean observed so far; at least one.
    """
    name = "mf_lhs"
    model = "multi_fidelity"
    fidelity = "low"

    def __init__(self, high_share: float = 0.3, high_pick: str = "random"):
        self.high_share, self.high_pick = high_share, high_pick

    def propose(self, evals, model, batch: int, round_idx: int, seed: int):
        cases = lhs_cases(batch, seed=seed * 1000 + round_idx + 1)
        cost = {f: [e.cost_s for e in evals if e.fidelity == f] for f in ("low", "high")}
        c_low = float(np.mean(cost["low"])) if cost["low"] else 1.0
        c_high = float(np.mean(cost["high"])) if cost["high"] else 10.0 * c_low
        # spend on high = share * (low spend + high spend), with the high cases' low runs already in the batch
        n_high = max(1, int(round(self.high_share / (1 - self.high_share) * batch * c_low / c_high)))
        if self.high_pick == "random":
            top = range(n_high)
        else:
            _, _, sd_d = model.components(rows_for(case_array(cases)))
            v_delta = (sd_d ** 2).reshape(len(READ_AT), len(cases)).mean(0)
            top = np.argsort(-v_delta)[:n_high]
        return [(c, "low") for c in cases] + [(cases[i], "high") for i in top]


class MultiFidelityIVR:
    """Cost-aware integrated variance reduction over case AND fidelity, for the multi-fidelity GP (amfs/ivr.py).

    Each round spends about `round_s` solver CPU seconds. Picks are greedy: the (case, fidelity) that removes the
    most predictive variance per CPU second, averaged over a fixed reference set of `n_ref` cases (three rows
    each), from a fresh Sobol pool of `pool` cases. After each pick the posterior covariance is downdated, so
    later picks account for what earlier ones will teach. A fine pick also schedules the cheap run at the same
    case (nested design) unless one is already in the batch. A run at the edge of the box scores low: it removes
    variance only in the half-neighbourhood inside the box.

    `min_high_share`: a floor on the share of each round's CPU seconds spent on fine runs. While fine runs are
    few, the correction's own variance is poorly estimated and its reductions look small, so the greedy rule
    can under-buy fine runs. If the greedy batch ends below the floor, fine runs are added in IVR order until it
    holds. 0 disables the floor (mf_ivr); mf_ivr_floor uses 0.4.
    """
    name = "mf_ivr"
    model = "multi_fidelity"
    fidelity = "low"

    def __init__(self, pool: int = 1024, n_ref: int = 300, round_s: float = 600.0, min_high_share: float = 0.0):
        self.pool, self.n_ref, self.round_s, self.min_high_share = pool, n_ref, round_s, min_high_share

    def propose(self, evals, model, batch: int, round_idx: int, seed: int):
        from .ivr import GreedyIVR, delta_cov, gp_cov
        C = candidate_pool(self.pool, seed=seed * 1000 + 500 + round_idx)
        Z = candidate_pool(self.n_ref, seed=seed * 1000 + 999)          # fixed per seed: where accuracy matters
        R = np.vstack([rows_for(Z), rows_for(C)])
        nz, nc = len(READ_AT) * len(Z), len(C)
        low = GreedyIVR(gp_cov(model.low, R), nz, nc, model.low.noise * model.low.ysd ** 2)
        dlt = None
        if model.delta is not None:
            S_d, noise_d = delta_cov(model.delta, R)
            dlt = GreedyIVR(S_d, nz, nc, noise_d)
        cost = {f: [e.cost_s for e in evals if e.fidelity == f] for f in ("low", "high")}
        c_low = float(np.mean(cost["low"])) if cost["low"] else 1.0
        c_high = float(np.mean(cost["high"])) if cost["high"] else 10.0 * c_low
        rho2 = model.rho ** 2
        has_low, has_high = np.zeros(nc, bool), np.zeros(nc, bool)
        out, spent, spent_high = [], 0.0, 0.0

        def scores():
            r_low = rho2 * low.reductions()
            r_dlt = dlt.reductions() if dlt is not None else np.zeros(nc)
            s_low = np.where(has_low, -np.inf, r_low / c_low)
            extra = np.where(has_low, 0.0, c_low)
            s_high = np.where(has_high | (dlt is None), -np.inf,
                              (r_dlt + np.where(has_low, 0.0, r_low)) / (c_high + extra))
            return s_low, s_high

        def pick_low(j):
            nonlocal spent
            low.pick(j); has_low[j] = True; out.append((to_case(C[j]), "low")); spent += c_low

        def pick_high(j):
            nonlocal spent, spent_high
            if not has_low[j]:
                pick_low(j)                                           # nested design
            dlt.pick(j); has_high[j] = True; out.append((to_case(C[j]), "high")); spent += c_high; spent_high += c_high

        while spent < self.round_s and not has_low.all():
            s_low, s_high = scores()
            j_l, j_h = int(np.argmax(s_low)), int(np.argmax(s_high))
            if s_high[j_h] > s_low[j_l]:
                pick_high(j_h)
            else:
                pick_low(j_l)
        # the floor: top up with the fine runs IVR ranks highest until they are at least min_high_share of the round
        while dlt is not None and spent_high < self.min_high_share * spent and not has_high.all():
            pick_high(int(np.argmax(scores()[1])))
        return out


STRATEGIES = {s.name: s for s in (RandomLHS, MaxVariance, MultiFidelityLHS, MultiFidelityIVR)}
