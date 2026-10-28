import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from amfs.design_space import CASE_HI, CASE_LO, candidate_pool, rows_for, to_unit  # noqa: E402
from amfs.ivr import GreedyIVR, gp_cov  # noqa: E402
from amfs.models import HI5, LO5, fit_gp  # noqa: E402
from amfs.oracle import Evaluation  # noqa: E402
from amfs.strategies import MaxVariance, MultiFidelityIVR  # noqa: E402
from amfs.models import MultiFidelityGP  # noqa: E402


def _f(X):
    u = (X - LO5) / (HI5 - LO5)
    return 4 * np.sin(3 * u[:, 2]) * (1 + u[:, 4]) + u[:, 0] - u[:, 1]


def _gp(n=60, seed=0):
    rng = np.random.default_rng(seed)
    X = rows_for(CASE_LO + (CASE_HI - CASE_LO) * rng.random((n, 4)))
    return fit_gp(X, _f(X), lo=LO5, hi=HI5, n_restarts=1, iters=60)[0]


def test_reduction_matches_the_downdated_variance():
    gp = _gp()
    Z, C = candidate_pool(32, seed=1), candidate_pool(16, seed=2)
    R = np.vstack([rows_for(Z), rows_for(C)])
    noise = gp.noise * gp.ysd ** 2
    g = GreedyIVR(gp_cov(gp, R), 3 * len(Z), len(C), noise)
    red = g.reductions()
    before = np.diag(g.S)[:3 * len(Z)].copy()
    j = int(np.argmax(red))
    g.pick(j)
    after = np.diag(g.S)[:3 * len(Z)]
    assert np.isclose(red[j], (before - after).mean(), rtol=1e-6)
    assert np.all(g.reductions() <= red + 1e-9)          # a pick never makes other runs more informative


def _evals(rng, n_low=80, n_high=12):
    C = CASE_LO + (CASE_HI - CASE_LO) * rng.random((n_low, 4))
    out = []
    for i, c in enumerate(C):
        case = dict(zip(("od_id", "h_id", "mf", "m"), c))
        X = rows_for(c[None])
        out.append(Evaluation(case, "low", _f(X) - 0.3 * X[:, 2], 2.0, False, False))
        if i < n_high:
            out.append(Evaluation(case, "high", _f(X), 30.0, False, False))
    return out


def test_ivr_buys_both_fidelities_and_avoids_edges():
    rng = np.random.default_rng(3)
    evals = _evals(rng)
    mf = MultiFidelityGP(iters=60, restarts=1, rho=1.0, delta="gp").fit(evals)
    picks = MultiFidelityIVR(pool=256, n_ref=64, round_s=200).propose(evals, mf, 0, 0, 0)
    fids = [f for _, f in picks]
    assert "low" in fids and sum(fids.count(f) * (2.0 if f == "low" else 30.0) for f in set(fids)) >= 200
    edge = lambda cases: np.mean([(np.minimum(u, 1 - u) < 0.1).any()
                                  for u in to_unit(np.array([[c[k] for k in ("od_id", "h_id", "mf", "m")]
                                                             for c in cases]))])
    ivr_low = [c for c, f in picks if f == "low"]
    sf = MultiFidelityGP(iters=60, restarts=1, rho=1.0, delta="gp").fit(evals)
    mv = [c for c, _ in MaxVariance(pool=256).propose(evals, type("M", (), {"predict": sf.predict})(),
                                                      len(ivr_low), 0, 0)]
    assert edge(ivr_low) < edge(mv), (edge(ivr_low), edge(mv))
