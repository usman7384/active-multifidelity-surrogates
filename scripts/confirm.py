"""The pre-registered analysis (PREREGISTRATION.md): mf_lhs against low_only at 1.0 CPU hour, seeds 9-20.

    python scripts/confirm.py results/confirm

Writes confirm.md and confirm.json next to the results.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize import _at  # noqa: E402

SEEDS = list(range(9, 21))
PRIMARY_H, SECONDARY_H, ALPHA = 1.0, 0.75, 0.05


def _load(folder: Path, name: str, seed: int):
    f = folder / f"{name}_seed{seed}.json"
    return json.loads(f.read_text())["history"] if f.exists() else None


def main(folder):
    folder = Path(folder)
    rows, missing = [], []
    for s in SEEDS:
        lo, mf = _load(folder, "low_only", s), _load(folder, "mf_lhs", s)
        if lo is None or mf is None:
            missing.append(s)
            continue
        rows.append(dict(seed=s, **{f"{k}_{n}": _at(h, k, x) for n, h in (("lo", lo), ("mf", mf))
                                    for k, x in (("rmse", PRIMARY_H), ("coverage95", PRIMARY_H))},
                         rmse_lo_075=_at(lo, "rmse", SECONDARY_H), rmse_mf_075=_at(mf, "rmse", SECONDARY_H)))
    d = np.array([r["rmse_lo"] - r["rmse_mf"] for r in rows])
    rel = np.array([(r["rmse_lo"] - r["rmse_mf"]) / r["rmse_lo"] for r in rows])
    d075 = np.array([r["rmse_lo_075"] - r["rmse_mf_075"] for r in rows])
    w = stats.wilcoxon(d, alternative="greater") if len(d) else None
    k = int((d > 0).sum())
    sign_p = float(stats.binomtest(k, len(d), 0.5, alternative="greater").pvalue) if len(d) else float("nan")
    cov_closer = int(sum(abs(r["coverage95_mf"] - 0.95) < abs(r["coverage95_lo"] - 0.95) for r in rows))
    out = dict(seeds=[r["seed"] for r in rows], missing=missing, d=d.tolist(),
               primary=dict(test="one-sided Wilcoxon signed-rank, d = RMSE(low_only) - RMSE(mf_lhs) at 1.0 h",
                            statistic=float(w.statistic) if w else None, p=float(w.pvalue) if w else None,
                            supported=bool(w and w.pvalue < ALPHA and not missing)),
               secondary=dict(sign_wins=k, sign_p=sign_p, mean_rel_gain=float(rel.mean()),
                              median_rel_gain=float(np.median(rel)),
                              wilcoxon_p_075=float(stats.wilcoxon(d075, alternative="greater").pvalue),
                              coverage_lo=float(np.mean([r["coverage95_lo"] for r in rows])),
                              coverage_mf=float(np.mean([r["coverage95_mf"] for r in rows])),
                              coverage_closer=cov_closer),
               rows=rows)
    lines = ["# Pre-registered confirmation: mf_lhs vs low_only at 1.0 CPU hour", "",
             f"Seeds analysed: {out['seeds']}" + (f"; MISSING: {missing}" if missing else ""), "",
             "| Seed | RMSE low_only | RMSE mf_lhs | d | cov95 low_only | cov95 mf_lhs |", "|---|---|---|---|---|---|"]
    lines += [f"| {r['seed']} | {r['rmse_lo']:.3f} | {r['rmse_mf']:.3f} | {r['rmse_lo'] - r['rmse_mf']:+.3f} | "
              f"{r['coverage95_lo']:.2f} | {r['coverage95_mf']:.2f} |" for r in rows]
    p = out["primary"]
    lines += ["", f"**Primary:** {p['test']}: p = {p['p']:.4f} -> "
                  f"{'supported (p < 0.05)' if p['supported'] else 'not shown (p >= 0.05)'}", "",
              f"Secondary: mf_lhs lower RMSE in {k} / {len(d)} seeds (sign test p = {sign_p:.3f}); mean relative "
              f"gain {rel.mean() * 100:+.1f}%, median {np.median(rel) * 100:+.1f}%; Wilcoxon at 0.75 h p = "
              f"{out['secondary']['wilcoxon_p_075']:.3f}; coverage low_only {out['secondary']['coverage_lo']:.2f}, "
              f"mf_lhs {out['secondary']['coverage_mf']:.2f}, mf_lhs closer to 0.95 in {cov_closer} / {len(rows)}."]
    (folder / "confirm.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (folder / "confirm.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/confirm")
