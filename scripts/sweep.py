"""Run every (config, seed) pair a few at a time: python scripts/sweep.py --configs a b --seeds 1 2"""
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


def _run(cfg_path: Path, seed: int, out: Path):
    log = out / "logs" / f"{cfg_path.stem}_seed{seed}.log"
    cmd = [sys.executable, "-u", "-W", "ignore", str(ROOT / "scripts/run.py"), str(cfg_path),
           "--seed", str(seed), "--out", str(out)]
    t0 = time.time()
    with open(log, "w") as fh:
        rc = subprocess.call(cmd, stdout=fh, stderr=subprocess.STDOUT, cwd=ROOT)
    return cfg_path.stem, seed, rc, time.time() - t0


def _keep_awake():
    """Ask Windows not to sleep while the sweep runs; a no-op elsewhere."""
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
    except (AttributeError, OSError):
        pass


def _stamp(msg: str):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


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
    _stamp("solving the test set")
    test = lhs_cases(c0["test"]["n_runs"], seed=c0["test"]["seed"])
    Oracle(ROOT / c0["cache_dir"], c0["fidelities"], 8).query(test, "high")

    jobs = [(c, s) for s in a.seeds for c in cfgs
            if not _done(out / f"{load_config(c)['name']}_seed{s}.json")]
    _stamp(f"{len(jobs)} experiments, {a.parallel} at a time")
    with ThreadPoolExecutor(a.parallel) as ex:
        futures = [ex.submit(_run, c, s, out) for c, s in jobs]
        for f in as_completed(futures):
            name, seed, rc, dt = f.result()
            _stamp(f"{name} seed {seed}: exit {rc}, {dt / 60:.0f} min")
            subprocess.call([sys.executable, str(ROOT / "scripts/summarize.py"), str(out)], cwd=ROOT)
    _stamp("sweep done")


if __name__ == "__main__":
    main()
