"""Summarise a sweep: the headline figure over seeds and a table of final and matched-cost scores.

    python scripts/summarize.py results/sweep

Writes cost_curves.png (thin line per seed, thick line the median on a common cost grid), summary.md and
summary.json into the same folder. The median is taken only over the cost range every seed of that strategy
reached, so it never extrapolates.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ORDER = ["random_lhs", "max_variance", "low_only", "mf_lhs"]
COLORS = {"random_lhs": "#1f77b4", "max_variance": "#ff7f0e", "low_only": "#2ca02c", "mf_lhs": "#d62728"}
MATCHED_H = (0.25, 0.5, 0.75, 1.0)  # solver CPU hours at which strategies are compared head to head
REFERENCE = "mf_lhs"                 # the strategy every other one is compared against, seed by seed


def _curve(h, key):
    return np.array([p["cost_s"] / 3600 for p in h]), np.array([p[key] for p in h], float)


def _at(h, key, x):
    """Score at cost x: the last round at or below x (what the strategy had in hand when x was spent)."""
    c, v = _curve(h, key)
    i = np.searchsorted(c, x, side="right") - 1
    return float(v[i]) if i >= 0 and c[-1] >= x else np.nan


def main(folder):
    folder = Path(folder)
    runs = defaultdict(dict)
    for f in sorted(folder.glob("*_seed*.json")):
        r = json.loads(f.read_text())
        runs[r["name"]][r["seed"]] = r["history"]
    names = [n for n in ORDER if n in runs] + [n for n in runs if n not in ORDER]
    if not names:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6))
    for n in names:
        col = COLORS.get(n)
        hs = list(runs[n].values())
        for h in hs:
            for ax, key in ((ax1, "rmse"), (ax2, "coverage95")):
                ax.plot(*_curve(h, key), "-", color=col, lw=0.8, alpha=0.35)
        lo = max(_curve(h, "rmse")[0][0] for h in hs)
        hi = min(_curve(h, "rmse")[0][-1] for h in hs)
        if hi > lo:
            g = np.linspace(lo, hi, 40)
            for ax, key in ((ax1, "rmse"), (ax2, "coverage95")):
                med = np.nanmedian([[_at(h, key, x) for x in g] for h in hs], axis=0)
                ax.plot(g, med, "-", color=col, lw=2.2, label=f"{n} ({len(hs)} seeds)")
    ax1.set(xlabel="solver CPU hours (training runs)", ylabel="test RMSE, hole change (points)", yscale="log")
    ax2.axhline(0.95, color="k", lw=0.8, ls="--")
    ax2.set(xlabel="solver CPU hours (training runs)", ylabel="95% interval coverage", ylim=(0.5, 1.02))
    for ax in (ax1, ax2):
        ax.grid(alpha=0.3)
        ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(folder / "cost_curves.png", dpi=150)
    plt.close(fig)

    summary, lines = {}, []
    ms = lambda v: f"{np.nanmean(v):.3f} ± {np.nanstd(v):.3f}" if np.isfinite(v).any() else "–"
    lines += ["| Strategy | Seeds | Final CPU h | Final runs (low / high) | Final RMSE | Final cov95 | Final CRPS |"
              + "".join(f" RMSE @ {x} h |" for x in MATCHED_H),
              "|---|---|---|---|---|---|---|" + "---|" * len(MATCHED_H)]
    for n in names:
        hs = [runs[n][k] for k in sorted(runs[n])]
        fin = [h[-1] for h in hs]
        d = dict(seeds=sorted(runs[n]),
                 final_cost_h=[p["cost_s"] / 3600 for p in fin], final_rmse=[p["rmse"] for p in fin],
                 final_cov95=[p["coverage95"] for p in fin], final_crps=[p["crps"] for p in fin],
                 final_runs=[p["n_runs"] for p in fin],
                 matched={str(x): [_at(h, "rmse", x) for h in hs] for x in MATCHED_H},
                 matched_cov={str(x): [_at(h, "coverage95", x) for h in hs] for x in MATCHED_H})
        summary[n] = d
        runs_txt = f"{np.mean([r.get('low', 0) for r in d['final_runs']]):.0f} / " \
                   f"{np.mean([r.get('high', 0) for r in d['final_runs']]):.0f}"
        lines.append(f"| `{n}` | {len(hs)} | {np.mean(d['final_cost_h']):.2f} | {runs_txt} | "
                     f"{ms(np.array(d['final_rmse']))} | {ms(np.array(d['final_cov95']))} | "
                     f"{ms(np.array(d['final_crps']))} |"
                     + "".join(f" {ms(np.array(d['matched'][str(x)]))} |" for x in MATCHED_H))
    lines += ["", "Mean ± sd over seeds. \"RMSE @ x h\": the score of the last round at or below x solver CPU hours; "
              "– where a strategy's runs ended before x."]
    lines += _paired(runs, names)
    (folder / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (folder / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print("\n".join(lines))


def _paired(runs, names):
    """Seed-by-seed comparison against REFERENCE at matched cost: in how many seeds is REFERENCE's RMSE lower,
    and its coverage closer to 0.95; with a one-sided sign-test p-value (chance of that many wins or more if
    neither strategy were better)."""
    if REFERENCE not in runs:
        return []
    from math import comb
    sign_p = lambda k, n: sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n
    out = ["", f"Paired by seed, `{REFERENCE}` against each strategy at matched solver cost "
                "(wins / seeds where both reached that cost, one-sided sign-test p):", "",
           "| Against | CPU h | RMSE lower | p | Coverage closer to 0.95 | p |", "|---|---|---|---|---|---|"]
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
            out.append(f"| `{n}` | {x} | {w_rmse} / {m} | {sign_p(w_rmse, m):.3f} | {w_cov} / {m} | "
                       f"{sign_p(w_cov, m):.3f} |")
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/sweep")
