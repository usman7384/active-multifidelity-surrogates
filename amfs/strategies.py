"""How the next batch of solver runs is chosen.

Each strategy proposes a list of (case, fidelity) pairs given the evaluations so far and the current model.

RandomLHS        the baseline: more Latin-hypercube cases, all high fidelity. What forming-surrogates did.
MaxVariance      active learning, first version: from a candidate pool, take the cases where the current GP is
                 most unsure (mean predictive sd over the three read-out reductions), keeping a minimum spacing so
                 a batch does not pile up in one spot.
MultiFidelity    planned: choose case AND fidelity by uncertainty reduction per solver second (see docstring).
"""
from __future__ import annotations

import numpy as np

from .design_space import READ_AT, candidate_pool, lhs_cases, rows_for, to_case, to_unit


class RandomLHS:
    name = "random_lhs"
    fidelity = "high"

    def propose(self, evals, model, batch: int, round_idx: int, seed: int):
        return [(c, "high") for c in lhs_cases(batch, seed=seed * 1000 + round_idx)]


class MaxVariance:
    name = "max_variance"
    fidelity = "high"

    def __init__(self, pool: int = 2048, min_dist: float = 0.15):
        self.pool, self.min_dist = pool, min_dist

    def propose(self, evals, model, batch: int, round_idx: int, seed: int):
        C = candidate_pool(self.pool, seed=seed * 1000 + round_idx)
        _, sd = model.predict(rows_for(C))
        score = sd.reshape(len(READ_AT), len(C)).mean(0)
        U = to_unit(C)
        chosen: list[int] = []
        for i in np.argsort(-score):
            if all(np.linalg.norm(U[i] - U[j]) >= self.min_dist for j in chosen):
                chosen.append(int(i))
            if len(chosen) == batch:
                break
        return [(to_case(C[i]), "high") for i in chosen]


class MultiFidelity:
    """Planned. Score each (candidate, fidelity) by expected reduction in integrated predictive variance over a
    reference set, divided by that fidelity's mean solver cost so far; propose the best pairs. Low-fidelity runs
    are cheap and narrow the low GP; high-fidelity runs pin the correction. Needs MultiFidelityGP."""
    name = "multi_fidelity"

    def propose(self, evals, model, batch: int, round_idx: int, seed: int):
        raise NotImplementedError("next step: see the class docstring")


STRATEGIES = {s.name: s for s in (RandomLHS, MaxVariance, MultiFidelity)}
