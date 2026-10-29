"""Compare mesh levels on two rings at six frictions: python scripts/fidelity_study.py"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from amfs.design_space import READ_AT  # noqa: E402
from amfs.oracle import Oracle  # noqa: E402

LEVELS = {
    "nz3": {"nz": 3}, "nz4": {"nz": 4}, "nz6": {"nz": 6}, "nz8": {"nz": 8}, "nz12": {"nz": 12},
    "nz4_dh2": {"nz": 4, "dh_frac": 0.02}, "nz4_dh4": {"nz": 4, "dh_frac": 0.04},
    "nz16": {"nz": 16},
}
REF = "nz16"
RINGS = {"standard 6:3:2": (2.0, 2 / 3), "thin 2.2:0.5": (2.2, 0.5)}
FRICTIONS = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
M = 0.15
SHOWN = {"nz4_dh4": "#c4572a", "nz4": "#d39e00", "nz8": "#2e8b57", "nz12": "#2f6fab"}


def _clean(v):
    return [None if not np.isfinite(x) else float(x) for x in v]


def _rows(cases, res) -> list[dict]:
    rows = []
    for i, c in enumerate(cases):
        ring = next(k for k, v in RINGS.items() if v == (c["od_id"], c["h_id"]))
        ref = res[REF][i]
        for lvl in LEVELS:
            e = res[lvl][i]
            rows.append(dict(ring=ring, mf=c["mf"], level=lvl, cost_s=e.cost_s,
                             stopped_early=e.stopped_early, y=_clean(e.y), err=_clean(e.y - ref.y)))
    return rows


def _summary(rows) -> dict:
    summary = {}
    for lvl in LEVELS:
        rs = [r for r in rows if r["level"] == lvl]
        errs = np.array([[np.nan if v is None else v for v in r["err"]] for r in rs], float)
        hi = np.array([r["mf"] >= 0.6 for r in rs])
        summary[lvl] = dict(numerics=LEVELS[lvl],
                            cost_s_mean=float(np.mean([r["cost_s"] for r in rs])),
                            rmse_all=float(np.sqrt(np.nanmean(errs ** 2))),
                            rmse_mf_ge_0p6=float(np.sqrt(np.nanmean(errs[hi] ** 2))),
                            max_abs=float(np.nanmax(np.abs(errs))),
                            n_missing_rows=int(np.isnan(errs).sum()),
                            n_stopped_early=int(sum(r["stopped_early"] for r in rs)))
    return summary


def _print(summary):
    print(f"{'level':9s} {'cost s':>7s} {'rmse':>7s} {'rmse mf>=.6':>11s} {'stopped':>7s}")
    for lvl, s in sorted(summary.items(), key=lambda kv: kv[1]["cost_s_mean"]):
        print(f"{lvl:9s} {s['cost_s_mean']:7.1f} {s['rmse_all']:7.3f} {s['rmse_mf_ge_0p6']:11.3f} "
              f"{s['n_stopped_early']:7d}")


def _plot(rows, summary, path: Path):
    fig, axs = plt.subplots(1, 3, figsize=(17, 4.8), gridspec_kw=dict(width_ratios=[1, 1, 0.9]))
    for ax, ring in zip(axs[:2], RINGS):
        for lvl, col in SHOWN.items():
            rs = [r for r in rows if r["level"] == lvl and r["ring"] == ring]
            mf = np.array([r["mf"] for r in rs])
            for k, ls, lab in ((1, "--", "20%"), (2, "-", "30%")):
                e = np.array([np.nan if r["err"][k] is None else r["err"][k] for r in rs], float)
                ax.plot(mf, e, ls, marker="o", ms=4, color=col,
                        label=f"{lvl} ({summary[lvl]['cost_s_mean']:.1f} s), {lab}")
        ref = [r for r in rows if r["level"] == REF and r["ring"] == ring]
        miss = [r["mf"] for r in ref if r["y"][2] is None]
        if miss:
            ax.plot(miss, [ax.get_ylim()[0]] * len(miss), "x", color="k", ms=8,
                    label=f"{REF} stopped before 30%")
        ax.axhline(0, color="k", lw=0.8)
        ax.set(title=f"{ring}: error vs {REF} (signed)", xlabel="friction mf",
               ylabel="hole change, low minus reference (points)")
        ax.grid(alpha=0.3)
    axs[0].legend(frameon=False, fontsize=8, ncol=2, loc="lower left")
    ax = axs[2]
    for lvl, s in summary.items():
        if lvl == REF:
            continue
        ax.plot(s["cost_s_mean"], s["rmse_mf_ge_0p6"], "o", color=SHOWN.get(lvl, "#5c6873"), ms=8)
        ax.annotate(lvl, (s["cost_s_mean"], s["rmse_mf_ge_0p6"]), (5, 4), textcoords="offset points",
                    fontsize=9)
    ax.set(title=f"Cost against error at mf >= 0.6 (reference {REF}: {summary[REF]['cost_s_mean']:.0f} s)",
           xlabel="mean solver seconds per run", ylabel="RMSE vs reference (points)", xscale="log")
    ax.set_xticks([2, 5, 10, 20, 30], ["2", "5", "10", "20", "30"])
    ax.minorticks_off()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/fidelity")
    ap.add_argument("--cache", default="cache")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    oracle = Oracle(a.cache, LEVELS, a.workers)
    cases = [dict(od_id=od, h_id=h, mf=mf, m=M) for od, h in RINGS.values() for mf in FRICTIONS]
    res = {lvl: oracle.query(cases, lvl) for lvl in LEVELS}
    rows = _rows(cases, res)
    summary = _summary(rows)
    data = dict(reference=REF, read_at=READ_AT, m=M, summary=summary, rows=rows)
    (out / "fidelity_study.json").write_text(json.dumps(data, indent=1))
    _print(summary)
    _plot(rows, summary, out / "fidelity_study.png")
    print("wrote", out)


if __name__ == "__main__":
    main()
