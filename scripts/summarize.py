"""Summarise a sweep folder: cost_curves.png, summary.md and summary.json."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from math import comb
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ORDER = ["random_lhs", "max_variance", "low_only", "mf_lhs"]
COLORS = {"random_lhs": "#1f77b4", "max_variance": "#ff7f0e", "low_only": "#2ca02c", "mf_lhs": "#d62728"}
MATCHED_H = (0.25, 0.5, 0.75, 1.0)   # CPU hours at which strategies are compared
REFERENCE = "mf_lhs"


def _curve(h, key):
    return np.array([p["cost_s"] / 3600 for p in h]), np.array([p[key] for p in h], float)


def _at(h, key, x):
    """Score of the last round at or below cost x (CPU hours), NaN if the run ended before x."""
    c, v = _curve(h, key)
    i = np.searchsorted(c, x, side="right") - 1
    return float(v[i]) if i >= 0 and c[-1] >= x else np.nan


def _load(folder: Path) -> dict:
    runs = defaultdict(dict)
    for f in sorted(folder.glob("*_seed*.json")):
        r = json.loads(f.read_text())
        runs[r["name"]][r["seed"]] = r["history"]
    return runs


def _figure(runs, names, path: Path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6))
    panels = ((ax1, "rmse"), (ax2, "coverage95"))
    for n in names:
        col = COLORS.get(n)
        hs = list(runs[n].values())
        for h in hs:
            for ax, key in panels:
                ax.plot(*_curve(h, key), "-", color=col, lw=0.8, alpha=0.35)
        lo = max(_curve(h, "rmse")[0][0] for h in hs)
        hi = min(_curve(h, "rmse")[0][-1] for h in hs)
        if hi > lo:
            g = np.linspace(lo, hi, 40)
            for ax, key in panels:
                med = np.nanmedian([[_at(h, key, x) for x in g] for h in hs], axis=0)
                ax.plot(g, med, "-", color=col, lw=2.2, label=f"{n} ({len(hs)} seeds)")
    ax1.set(xlabel="solver CPU hours (training runs)", ylabel="test RMSE, hole change (points)", yscale="log")
    ax2.axhline(0.95, color="k", lw=0.8, ls="--")
    ax2.set(xlabel="solver CPU hours (training runs)", ylabel="95% interval coverage", ylim=(0.5, 1.02))
    for ax in (ax1, ax2):
        ax.grid(alpha=0.3)
        ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _mean_sd(v) -> str:
    v = np.array(v)
    return f"{np.nanmean(v):.3f} ± {np.nanstd(v):.3f}" if np.isfinite(v).any() else "–"


def _stats(hs, seeds) -> dict:
    fin = [h[-1] for h in hs]
    return dict(seeds=seeds,
                final_cost_h=[p["cost_s"] / 3600 for p in fin],
                final_rmse=[p["rmse"] for p in fin],
                final_cov95=[p["coverage95"] for p in fin],
                final_crps=[p["crps"] for p in fin],
                final_runs=[p["n_runs"] for p in fin],
                matched={str(x): [_at(h, "rmse", x) for h in hs] for x in MATCHED_H},
                matched_cov={str(x): [_at(h, "coverage95", x) for h in hs] for x in MATCHED_H})


def _row(n, d) -> str:
    low = np.mean([r.get("low", 0) for r in d["final_runs"]])
    high = np.mean([r.get("high", 0) for r in d["final_runs"]])
    cells = [f"`{n}`", str(len(d["seeds"])), f"{np.mean(d['final_cost_h']):.2f}", f"{low:.0f} / {high:.0f}",
             _mean_sd(d["final_rmse"]), _mean_sd(d["final_cov95"]), _mean_sd(d["final_crps"])]
    cells += [_mean_sd(d["matched"][str(x)]) for x in MATCHED_H]
    return "| " + " | ".join(cells) + " |"


def _table(runs, names, summary) -> list[str]:
    head = "| Strategy | Seeds | Final CPU h | Final runs (low / high) | Final RMSE | Final cov95 |"
    head += " Final CRPS |" + "".join(f" RMSE @ {x} h |" for x in MATCHED_H)
    lines = [head, "|---|---|---|---|---|---|---|" + "---|" * len(MATCHED_H)]
    for n in names:
        seeds = sorted(runs[n])
        d = _stats([runs[n][k] for k in seeds], seeds)
        summary[n] = d
        lines.append(_row(n, d))
    note = ("Mean ± sd over seeds. \"RMSE @ x h\": the score of the last round at or below x solver CPU "
            "hours; – where a strategy's runs ended before x.")
    return lines + ["", note]


def _sign_p(k, n) -> float:
    return sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n


def _paired(runs, names) -> list[str]:
    """Seed-by-seed wins of REFERENCE at matched cost, with a one-sided sign-test p."""
    if REFERENCE not in runs:
        return []
    intro = (f"Paired by seed, `{REFERENCE}` against each strategy at matched solver cost "
             "(wins / seeds where both reached that cost, one-sided sign-test p):")
    out = ["", intro, "", "| Against | CPU h | RMSE lower | p | Coverage closer to 0.95 | p |",
           "|---|---|---|---|---|---|"]
    ref = runs[REFERENCE]
    for n in names:
        if n == REFERENCE:
            continue
        seeds = sorted(set(ref) & set(runs[n]))
        for x in MATCHED_H:
            pairs = [(_at(ref[k], "rmse", x), _at(runs[n][k], "rmse", x),
                      _at(ref[k], "coverage95", x), _at(runs[n][k], "coverage95", x)) for k in seeds]
            pairs = [q for q in pairs if np.isfinite(q).all()]
            if not pairs:
                continue
            m = len(pairs)
            w_rmse = sum(a < b for a, b, _, _ in pairs)
            w_cov = sum(abs(c - 0.95) < abs(d - 0.95) for _, _, c, d in pairs)
            out.append(f"| `{n}` | {x} | {w_rmse} / {m} | {_sign_p(w_rmse, m):.3f} | "
                       f"{w_cov} / {m} | {_sign_p(w_cov, m):.3f} |")
    return out


def main(folder):
    folder = Path(folder)
    runs = _load(folder)
    names = [n for n in ORDER if n in runs] + [n for n in runs if n not in ORDER]
    if not names:
        return
    _figure(runs, names, folder / "cost_curves.png")
    summary = {}
    lines = _table(runs, names, summary) + _paired(runs, names)
    (folder / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (folder / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/sweep")
