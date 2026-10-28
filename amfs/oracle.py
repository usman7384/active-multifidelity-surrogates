"""The solver as an expensive oracle: cached, parallel, and it charges every call its real CPU time.

Adapted from forming-surrogates (surrogates/gp_bo/solver_calls.py). Two changes: a call names a *fidelity*
(a mesh resolution) instead of raw numerics, and every result carries its original solve time, so an
experiment's budget is counted in solver seconds even when the run is later read back from the cache.
That keeps budgets reproducible: a re-run of an experiment spends exactly the same "cost".

Cost is the worker process's CPU time (cpu_s), not wall time: wall time is inflated by anything else running
on the machine, which made early costs depend on what else was running. Cache entries from before this change
have no cpu_s and are solved again. Cache files are written atomically, so parallel experiments can share one.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .design_space import READ_AT, RUN_TO

# nz = elements through the half height, dh_frac = die travel per step (fraction of the half height)
DEFAULT_FIDELITIES = {"low": {"nz": 4, "dh_frac": 0.04}, "high": {"nz": 12}}   # chosen by scripts/fidelity_study.py


@dataclass
class Evaluation:
    case: dict
    fidelity: str
    y: np.ndarray            # inner-diameter change (%) at READ_AT; NaN where the run stopped early
    cost_s: float            # solver CPU seconds of the original solve
    stopped_early: bool
    cached: bool


def _key(case: dict, num: dict) -> str:
    return hashlib.sha1(json.dumps([case, num], sort_keys=True).encode()).hexdigest()[:16]


def _solve(job):
    from ringsim.solver import Numerics, RingCase, RingSolver
    case, num = job
    t0 = time.process_time()
    res = RingSolver(RingCase(**case, reduction=RUN_TO), Numerics(**num)).run()
    cpu_s = time.process_time() - t0
    return dict(case=case, numerics=num,
                reduction=np.asarray(res.curves["reduction"]).tolist(),
                id_change_pct=np.asarray(res.curves["id_change_pct"]).tolist(),
                stopped_early=bool(res.info["stopped_early"]), runtime_s=float(res.info["runtime_s"]),
                cpu_s=round(cpu_s, 3))


def _read(r: dict) -> np.ndarray:
    x, y = np.asarray(r["reduction"]), np.asarray(r["id_change_pct"])
    n = min(len(x), len(y))
    out = np.interp(READ_AT, x[:n], y[:n])
    out[np.asarray(READ_AT) > x[n - 1] + 1e-9] = np.nan
    return out


class Oracle:
    def __init__(self, cache_dir: str | Path = "cache", fidelities: dict | None = None, workers: int = 4,
                 log=print):
        self.cache = Path(cache_dir)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.fidelities = dict(fidelities or DEFAULT_FIDELITIES)
        self.workers, self.log = workers, log

    def query(self, cases: list[dict], fidelity: str) -> list[Evaluation]:
        """Solve each case at one fidelity (cached); results in input order."""
        num = dict(self.fidelities[fidelity])
        raw: list[dict | None] = [None] * len(cases)
        todo = []
        for i, c in enumerate(cases):
            f = self.cache / f"{_key(c, num)}.json"
            r = json.loads(f.read_text()) if f.exists() else {}
            if "cpu_s" in r:
                raw[i] = dict(r, cached=True)
            else:
                todo.append(i)
        if todo:
            w = max(1, min(self.workers, len(todo)))
            self.log(f"oracle: {len(todo)} {fidelity}-fidelity runs on {w} workers "
                     f"({len(cases) - len(todo)} cached)")
            with ProcessPoolExecutor(max_workers=w) as ex:
                for i, r in zip(todo, ex.map(_solve, [(cases[i], num) for i in todo])):
                    f = self.cache / f"{_key(cases[i], num)}.json"
                    tmp = f.with_suffix(f".{os.getpid()}.tmp")
                    tmp.write_text(json.dumps(r))
                    os.replace(tmp, f)                  # atomic: a parallel reader never sees half a file
                    raw[i] = dict(r, cached=False)
        return [Evaluation(case=r["case"], fidelity=fidelity, y=_read(r), cost_s=r["cpu_s"],
                           stopped_early=r["stopped_early"], cached=r["cached"]) for r in raw]
