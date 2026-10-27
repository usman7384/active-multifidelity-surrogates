"""The headline figure: test error and 95% coverage against solver CPU time, one line per result file.

    python scripts/plot.py results/*.json --out results/cost_curves.png
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", default="results/cost_curves.png")
    a = ap.parse_args(argv)
    runs = defaultdict(list)
    for f in a.files:
        r = json.loads(Path(f).read_text())
        runs[r["name"]].append(r["history"])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    for name, hs in runs.items():
        for k, h in enumerate(hs):
            c = [p["cost_s"] / 3600 for p in h]
            kw = dict(label=name if k == 0 else None, alpha=0.9 if len(hs) == 1 else 0.6)
            ax1.plot(c, [p["rmse"] for p in h], "o-", ms=3, **kw)
            ax2.plot(c, [p["coverage95"] for p in h], "o-", ms=3, **kw)
    ax1.set(xlabel="solver CPU hours (training runs)", ylabel="test RMSE, hole change (points)", yscale="log")
    ax2.axhline(0.95, color="k", lw=0.8, ls="--")
    ax2.set(xlabel="solver CPU hours (training runs)", ylabel="95% interval coverage", ylim=(0, 1.02))
    for ax in (ax1, ax2):
        ax.grid(alpha=0.3)
        ax.legend(frameon=False)
    fig.tight_layout()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=150)
    print("wrote", a.out, "| files:", len(a.files), "| strategies:", ", ".join(runs))


if __name__ == "__main__":
    main()
