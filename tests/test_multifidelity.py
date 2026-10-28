import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from amfs.loop import load_config, run_experiment  # noqa: E402
from amfs.models import HI5, LO5, MultiFidelityGP  # noqa: E402
from amfs.gp import fit_gp  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def _truth(X):
    u = (X - LO5) / (HI5 - LO5)
    return 10 * np.sin(2.5 * u[:, 2]) * (1 + u[:, 4]) + 3 * u[:, 0] - 2 * u[:, 1]


def _low(X):                       # cheap model: a smooth bias that grows with friction, like the fidelity study
    u = (X - LO5) / (HI5 - LO5)
    return _truth(X) - 1.5 * u[:, 2] ** 2


def test_mfgp_beats_high_only_with_few_high_points():
    rng = np.random.default_rng(0)
    Xl = LO5 + (HI5 - LO5) * rng.random((150, 5))
    Xh = Xl[:12]                                           # nested, as the strategy keeps it
    Xt = LO5 + (HI5 - LO5) * rng.random((200, 5))
    mf = MultiFidelityGP(iters=120, restarts=1).fit_arrays(Xl, _low(Xl), Xh, _truth(Xh))
    hi, _ = fit_gp(Xh, _truth(Xh), lo=LO5, hi=HI5, n_restarts=1, iters=120)
    rmse_mf = np.sqrt(np.mean((mf.predict(Xt)[0] - _truth(Xt)) ** 2))
    rmse_hi = np.sqrt(np.mean((hi.predict(Xt)[0] - _truth(Xt)) ** 2))
    rmse_lo = np.sqrt(np.mean((mf.low.predict(Xt)[0] - _truth(Xt)) ** 2))
    assert rmse_mf < 0.5 * rmse_hi and rmse_mf < rmse_lo, (rmse_mf, rmse_hi, rmse_lo)
    assert 0.8 < mf.rho < 1.2


def test_mfgp_falls_back_to_low_gp_without_high_rows():
    rng = np.random.default_rng(1)
    Xl = LO5 + (HI5 - LO5) * rng.random((40, 5))
    mf = MultiFidelityGP(iters=60, restarts=1).fit_arrays(Xl, _low(Xl), np.empty((0, 5)), np.empty(0))
    assert mf.delta is None and mf.rho == 1.0
    mu, sd = mf.predict(Xl[:5])
    assert np.all(np.isfinite(mu)) and np.all(sd > 0)


def test_multi_fidelity_experiment_smoke(tmp_path):
    cfg = load_config(ROOT / "configs/smoke_mf.yaml")
    cfg["cache_dir"] = str(tmp_path / "cache")
    out = run_experiment(cfg, tmp_path / "results", log=lambda *_: None)
    last = out["history"][-1]
    assert last["n_runs"]["low"] >= last["n_runs"]["high"] >= 3 and np.isfinite(last["rmse"])


def test_mf_lhs_experiment_smoke(tmp_path):
    cfg = load_config(ROOT / "configs/smoke_mf.yaml")
    cfg.update(name="smoke_mf_lhs", strategy="mf_lhs", strategy_args={"high_share": 0.3}, mf_model={"rho": 1.0, "delta": "linear"},
               cache_dir=str(tmp_path / "cache"))
    out = run_experiment(cfg, tmp_path / "results", log=lambda *_: None)
    first, last = out["history"][0], out["history"][-1]
    assert last["n_runs"]["high"] > first["n_runs"]["high"] and np.isfinite(last["rmse"])
