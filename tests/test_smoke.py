import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from amfs.design_space import READ_AT, case_array, lhs_cases, rows_for  # noqa: E402
from amfs.loop import load_config, run_experiment  # noqa: E402
from amfs.metrics import score  # noqa: E402
from amfs.oracle import Oracle  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def test_design_rows():
    X = rows_for(case_array(lhs_cases(5, seed=0)))
    assert X.shape == (5 * len(READ_AT), 5)


def test_score_perfect_prediction():
    y = np.array([1.0, 2.0, 3.0])
    s = score(y, y, np.ones(3))
    assert s["rmse"] == 0 and s["coverage95"] == 1.0


def test_oracle_charges_cost_and_caches(tmp_path):
    o = Oracle(tmp_path, {"high": {"nz": 4}}, workers=1, log=lambda *_: None)
    case = dict(od_id=2.0, h_id=2 / 3, mf=0.3, m=0.15)
    a = o.query([case], "high")[0]
    b = o.query([case], "high")[0]
    assert not a.cached and b.cached
    assert a.cost_s > 0 and b.cost_s == a.cost_s
    assert np.all(np.isfinite(a.y)) and a.y[-1] < a.y[0] < 5


def test_smoke_experiment(tmp_path):
    cfg = load_config(ROOT / "configs/smoke.yaml")
    cfg["cache_dir"] = str(tmp_path / "cache")
    out = run_experiment(cfg, tmp_path / "results", log=lambda *_: None)
    assert len(out["history"]) >= 1 and np.isfinite(out["history"][-1]["rmse"])
