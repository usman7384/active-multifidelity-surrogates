"""Run every (strategy, seed) pair, a few at a time, and refresh the summary after each one finishes.

    python scripts/sweep.py --configs random_lhs max_variance low_only mf_lhs --seeds 0 1 2 3 4 --parallel 2

Seed-major order: all strategies of seed 0 first, then seed 1, ..., so a sweep cut short still leaves complete
seeds. A pair whose result file already exists (on the CPU-time cost basis) is skipped, so a sweep can be resumed.
The fixed test set is solved once up front, so parallel experiments do not all solve it at the same time.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from amfs.design_space import lhs_cases  # noqa: E402
from amfs.loop import load_config  # noqa: E402
from amfs.oracle import Oracle  # noqa: E402


def _done(path: Path) -> bool:
    try:
        return json.loads(path.read_text()).get("cost_basis") == "cpu_s"
    except (OSError, ValueError):
        return False


def _run(cfg_path: Path, seed: int, out: Path) -> tuple[str, int, int, float]:
    log = out / "logs" / f"{cfg_path.stem}_seed{seed}.log"
    t0 = time.time()
    with open(log, "w") as fh:
        rc = subprocess.call([sys.executable, "-u", "-W", "ignore", str(ROOT / "scripts/run.py"), str(cfg_path),
                              "--seed", str(seed), "--out", str(out)], stdout=fh, stderr=subprocess.STDOUT,
                             cwd=ROOT)
    return cfg_path.stem, seed, rc, time.time() - t0


def _keep_awake():
    """Ask Windows not to idle-sleep while this process runs (released when it exits); a no-op elsewhere."""
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)   # ES_CONTINUOUS | SYSTEM_REQUIRED
    except (AttributeError, OSError):
        pass


def main(argv=None):
    _keep_awake()
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", nargs="+", required=True)
    ap.add_argument("--seeds", nargs="+", type=int, required=True)
    ap.add_argument("--parallel", type=int, default=2)
    ap.add_argument("--out", default="results/sweep")
    a = ap.parse_args(argv)
    out = ROOT / a.out
    (out / "logs").mkdir(parents=True, exist_ok=True)
    cfgs = [ROOT / "configs" / f"{c}.yaml" for c in a.configs]

    c0 = load_config(cfgs[0])
    print(time.strftime("%H:%M:%S"), "solving the test set", flush=True)
    Oracle(ROOT / c0["cache_dir"], c0["fidelities"], 8).query(
        lhs_cases(c0["test"]["n_runs"], seed=c0["test"]["seed"]), "high")

    jobs = [(c, s) for s in a.seeds for c in cfgs
            if not _done(out / f"{load_config(c)['name']}_seed{s}.json")]
    print(time.strftime("%H:%M:%S"), f"{len(jobs)} experiments, {a.parallel} at a time", flush=True)
    with ThreadPoolExecutor(a.parallel) as ex:
        futs = [ex.submit(_run, c, s, out) for c, s in jobs]
        for f in as_completed(futs):
            name, seed, rc, dt = f.result()
            print(time.strftime("%H:%M:%S"), f"{name} seed {seed}: exit {rc}, {dt / 60:.0f} min", flush=True)
            subprocess.call([sys.executable, str(ROOT / "scripts/summarize.py"), str(out)], cwd=ROOT)
    print(time.strftime("%H:%M:%S"), "sweep done", flush=True)


if __name__ == "__main__":
    main()
