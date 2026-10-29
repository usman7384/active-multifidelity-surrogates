"""One experiment: a strategy spends a solver budget; the surrogate is refitted and scored each round."""
from __future__ import annotations

import json
import time
from pathlib import Path

import yaml

from .design_space import CASE_KEYS, lhs_cases
from .metrics import score
from .models import make_model, table
from .oracle import Oracle
from .strategies import STRATEGIES


def _key(case: dict, fidelity: str) -> tuple:
    return (fidelity,) + tuple(round(case[k], 12) for k in CASE_KEYS)


def _initial(cfg: dict, strategy, oracle: Oracle, seed: int) -> list:
    """Initial Latin-hypercube design; multi-fidelity: the first n_high low cases also run at high."""
    init = cfg["init"]
    s = seed * 1000
    if "n_low" in init:
        cases = lhs_cases(int(init["n_low"]), seed=s)
        return oracle.query(cases, "low") + oracle.query(cases[: int(init["n_high"])], "high")
    return oracle.query(lhs_cases(int(init["n_runs"]), seed=s), strategy.fidelity)


def load_config(path) -> dict:
    return yaml.safe_load(Path(path).read_text())


def run_experiment(cfg: dict, out_dir="results", log=print) -> dict:
    seed = int(cfg.get("seed", 0))
    oracle = Oracle(cfg.get("cache_dir", "cache"), cfg.get("fidelities"), cfg.get("workers", 4), log=log)
    strategy = STRATEGIES[cfg["strategy"]](**cfg.get("strategy_args", {}))
    name = cfg.get("name", strategy.name)

    test = oracle.query(lhs_cases(cfg["test"]["n_runs"], seed=cfg["test"]["seed"]), "high")
    Xt, yt = table(test, "high")

    evals = _initial(cfg, strategy, oracle, seed)
    history = []
    max_rounds = int(cfg.get("max_rounds", 1000))
    for rnd in range(max_rounds):
        model = make_model(strategy.model, getattr(strategy, "fidelity", "high"), seed, cfg.get("gp", {}),
                           cfg.get("mf_model")).fit(evals)
        mu, sd = model.predict(Xt)
        spent = float(sum(e.cost_s for e in evals))
        point = dict(round=rnd, cost_s=spent,
                     n_runs={f: sum(e.fidelity == f for e in evals) for f in oracle.fidelities},
                     n_stopped_early=sum(e.stopped_early for e in evals), **score(yt, mu, sd))
        if hasattr(model, "rho"):
            point["rho"] = model.rho
            point["delta"] = getattr(model, "delta_choice", None)
            point["delta_cv"] = model.info.get("delta_cv")
        history.append(point)
        log(f"[{name}] round {rnd}: {spent:.0f} s, rmse {point['rmse']:.3f}, cov95 {point['coverage95']:.2f}")
        if spent >= cfg["budget_s"] or rnd == max_rounds - 1:
            break
        seen = {_key(e.case, e.fidelity) for e in evals}
        batch = []
        for c, f in strategy.propose(evals, model, int(cfg["batch"]), rnd, seed):
            if _key(c, f) not in seen:
                seen.add(_key(c, f))
                batch.append((c, f))
        if not batch:
            log("nothing new proposed; stopping")
            break
        for fid in sorted({f for _, f in batch}):
            evals += oracle.query([c for c, f in batch if f == fid], fid)

    out = dict(name=name, strategy=strategy.name, model=strategy.model, seed=seed, cost_basis="cpu_s",
               config=cfg,
               test=dict(n_runs=len(test), n_rows=int(len(yt)), cost_s=float(sum(e.cost_s for e in test))),
               history=history, created=time.strftime("%Y-%m-%dT%H:%M:%S"))
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}_seed{seed}.json").write_text(json.dumps(out, indent=1))
    return out
