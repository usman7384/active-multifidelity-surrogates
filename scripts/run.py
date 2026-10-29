"""Run one experiment: python scripts/run.py configs/mf_lhs.yaml --seed 1 --out results"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from amfs.loop import load_config, run_experiment  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--out", default="results")
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    if a.seed is not None:
        cfg["seed"] = a.seed
    run_experiment(cfg, a.out)


if __name__ == "__main__":
    main()
