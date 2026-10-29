"""Paired test of B against A at 1 CPU hour: python scripts/confirm.py results/confirm --a X --b Y"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize import _at  # noqa: E402

SEEDS = list(range(9, 21))
PRIMARY_H = 1.0
SECONDARY_H = 0.75
ALPHA = 0.05


def _load(folder: Path, name: str, seed: int):
    f = folder / f"{name}_seed{seed}.json"
    return json.loads(f.read_text())["history"] if f.exists() else None


def _row(seed, lo, mf) -> dict:
    return dict(seed=seed,
                rmse_lo=_at(lo, "rmse", PRIMARY_H), coverage95_lo=_at(lo, "coverage95", PRIMARY_H),
                rmse_mf=_at(mf, "rmse", PRIMARY_H), coverage95_mf=_at(mf, "coverage95", PRIMARY_H),
                rmse_lo_075=_at(lo, "rmse", SECONDARY_H), rmse_mf_075=_at(mf, "rmse", SECONDARY_H))


def _analyse(rows, missing, a, b) -> dict:
    d = np.array([r["rmse_lo"] - r["rmse_mf"] for r in rows])
    rel = np.array([(r["rmse_lo"] - r["rmse_mf"]) / r["rmse_lo"] for r in rows])
    d075 = np.array([r["rmse_lo_075"] - r["rmse_mf_075"] for r in rows])
    w = stats.wilcoxon(d, alternative="greater") if len(d) else None
    k = int((d > 0).sum())
    sign_p = float("nan")
    if len(d):
        sign_p = float(stats.binomtest(k, len(d), 0.5, alternative="greater").pvalue)
    closer = int(sum(abs(r["coverage95_mf"] - 0.95) < abs(r["coverage95_lo"] - 0.95) for r in rows))
    primary = dict(test=f"one-sided Wilcoxon signed-rank, d = RMSE({a}) - RMSE({b}) at 1.0 h",
                   statistic=float(w.statistic) if w else None, p=float(w.pvalue) if w else None,
                   supported=bool(w and w.pvalue < ALPHA and not missing))
    secondary = dict(sign_wins=k, sign_p=sign_p, mean_rel_gain=float(rel.mean()),
                     median_rel_gain=float(np.median(rel)),
                     wilcoxon_p_075=float(stats.wilcoxon(d075, alternative="greater").pvalue),
                     coverage_lo=float(np.mean([r["coverage95_lo"] for r in rows])),
                     coverage_mf=float(np.mean([r["coverage95_mf"] for r in rows])),
                     coverage_closer=closer)
    return dict(a=a, b=b, seeds=[r["seed"] for r in rows], missing=missing, d=d.tolist(),
                primary=primary, secondary=secondary, rows=rows)


def _report(out) -> list[str]:
    a, b, rows, missing = out["a"], out["b"], out["rows"], out["missing"]
    p, s = out["primary"], out["secondary"]
    seeds_line = f"Seeds analysed: {out['seeds']}" + (f"; MISSING: {missing}" if missing else "")
    lines = [f"# Pre-registered confirmation: {b} vs {a} at 1.0 CPU hour", "", seeds_line, "",
             f"| Seed | RMSE {a} | RMSE {b} | d | cov95 {a} | cov95 {b} |", "|---|---|---|---|---|---|"]
    for r in rows:
        d = r["rmse_lo"] - r["rmse_mf"]
        lines.append(f"| {r['seed']} | {r['rmse_lo']:.3f} | {r['rmse_mf']:.3f} | {d:+.3f} | "
                     f"{r['coverage95_lo']:.2f} | {r['coverage95_mf']:.2f} |")
    verdict = "supported (p < 0.05)" if p["supported"] else "not shown (p >= 0.05)"
    n = len(rows)
    lines += ["", f"**Primary:** {p['test']}: p = {p['p']:.4f} -> {verdict}", "",
              f"Secondary: {b} lower RMSE in {s['sign_wins']} / {n} seeds (sign test p = {s['sign_p']:.3f}); "
              f"mean relative gain {s['mean_rel_gain'] * 100:+.1f}%, "
              f"median {s['median_rel_gain'] * 100:+.1f}%; "
              f"Wilcoxon at 0.75 h p = {s['wilcoxon_p_075']:.3f}; coverage {a} {s['coverage_lo']:.2f}, "
              f"{b} {s['coverage_mf']:.2f}, {b} closer to 0.95 in {s['coverage_closer']} / {n}."]
    return lines


def main(folder, a: str = "low_only", b: str = "mf_lhs", seeds=SEEDS):
    folder = Path(folder)
    rows, missing = [], []
    for s in seeds:
        lo, mf = _load(folder, a, s), _load(folder, b, s)
        if lo is None or mf is None:
            missing.append(s)
        else:
            rows.append(_row(s, lo, mf))
    out = _analyse(rows, missing, a, b)
    lines = _report(out)
    (folder / "confirm.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (folder / "confirm.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?", default="results/confirm")
    ap.add_argument("--a", default="low_only")
    ap.add_argument("--b", default="mf_lhs")
    args = ap.parse_args()
    main(args.folder, args.a, args.b)
