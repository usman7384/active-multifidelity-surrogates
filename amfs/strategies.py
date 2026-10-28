"""How the next batch of solver runs is chosen.

Each strategy proposes a list of (case, fidelity) pairs given the evaluations so far and the current model, and
says which model it is meant to be paired with.

RandomLHS        the baseline: more Latin-hypercube cases at one fidelity. High fidelity is what forming-surrogates
                 did; low fidelity is the "just use cheap runs" competitor the fidelity study says to beat.
MaxVariance      active learning, first version: from a candidate pool, take the cases where the current GP is
                 most unsure (mean predictive sd over the three read-out reductions), keeping a minimum spacing so
                 a batch does not pile up in one spot.
MultiFidelity    cost-aware active learning over case AND fidelity, paired with the multi-fidelity GP.
MultiFidelityLHS Latin-hypercube cheap runs plus a fixed share of solver time on fine runs, same GP.
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


class MultiFidelityLHS:
    """Multi-fidelity, second version: space-filling cheap runs plus a fixed share of solver time on fine runs.

    The first version lost to plain cheap runs for two reasons seen in its seed-0 run: picking cheap cases by
    variance put 82% of them near an edge of the box (58% for a Latin hypercube), and the variance score never
    judged a fine run worth its cost, so delta stayed fitted on the 10 initial fine runs. Here:

        low runs:  `batch` fresh Latin-hypercube cases per round, as low_only
        high runs: about `high_share` of the round's solver seconds, on cases of this round's low batch
                   (nested for free). high_pick = "random" takes the first of them (a random subset of a
                   Latin hypercube); "variance" takes those with the largest var_delta.

    "random" is the default: picking fine runs by var_delta put them in the hardest cases (fine-minus-coarse
    residual rms 0.43 against 0.19 for random cases), so the correction learned an unrepresentative bias and
    over-corrected everywhere else (offline correction study, seed 0).

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
    case (nested design) unless one is already in the batch. Unlike MultiFidelity (point-wise variance), a run
    at the edge of the box scores low: it removes variance only in the half-neighbourhood inside the box.

    `min_high_share`: a floor on the share of each round's CPU seconds spent on fine runs. Without it (seeds 1-8,
    results/ivr) the greedy rule under-bought fine runs in 5 of 8 seeds (19-35 against 49-69 in the 3 seeds that
    did best): while fine runs are few, the correction's own variance is poorly estimated, so its reductions look
    small. If the greedy batch ends below the floor, more fine runs are added, still in IVR order, until it holds.
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


STRATEGIES = {s.name: s for s in (RandomLHS, MaxVariance, MultiFidelity, MultiFidelityLHS, MultiFidelityIVR)}
