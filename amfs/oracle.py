"""The solver behind a cache: every run is charged the CPU seconds of its original solve."""
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

# nz: elements through the half height; dh_frac: die travel per step
DEFAULT_FIDELITIES = {"low": {"nz": 4, "dh_frac": 0.04}, "high": {"nz": 12}}


@dataclass
class Evaluation:
    case: dict
    fidelity: str
    y: np.ndarray        # inner-diameter change (%) at READ_AT, NaN where the run stopped early
    cost_s: float        # solver CPU seconds
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
                stopped_early=bool(res.info["stopped_early"]),
                runtime_s=float(res.info["runtime_s"]),
                cpu_s=round(cpu_s, 3))


def _read(r: dict) -> np.ndarray:
    x, y = np.asarray(r["reduction"]), np.asarray(r["id_change_pct"])
    n = min(len(x), len(y))
    out = np.interp(READ_AT, x[:n], y[:n])
    out[np.asarray(READ_AT) > x[n - 1] + 1e-9] = np.nan
    return out


class Oracle:
    def __init__(self, cache_dir="cache", fidelities=None, workers: int = 4, log=print):
        self.cache = Path(cache_dir)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.fidelities = dict(fidelities or DEFAULT_FIDELITIES)
        self.workers = workers
        self.log = log

    def query(self, cases: list[dict], fidelity: str) -> list[Evaluation]:
        """Solve each case at one fidelity, reading from the cache where possible."""
        num = dict(self.fidelities[fidelity])
        raw = [None] * len(cases)
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
            self.log(f"oracle: {len(todo)} {fidelity} runs on {w} workers")
            jobs = [(cases[i], num) for i in todo]
            with ProcessPoolExecutor(max_workers=w) as ex:
                for i, r in zip(todo, ex.map(_solve, jobs)):
                    self._write(cases[i], num, r)
                    raw[i] = dict(r, cached=False)
        return [Evaluation(r["case"], fidelity, _read(r), r["cpu_s"], r["stopped_early"], r["cached"])
                for r in raw]

    def _write(self, case, num, r):
        f = self.cache / f"{_key(case, num)}.json"
        tmp = f.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(r))
        os.replace(tmp, f)   # atomic, so parallel experiments can share the cache
