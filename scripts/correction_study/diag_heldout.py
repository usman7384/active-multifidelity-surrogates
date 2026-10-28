"""Why do low_only and mf_lhs stall at the same error on the held-out test set? Take mf_lhs seed 1's final data
apart: low GP alone, the linear correction, a GP correction, and the true coarse-minus-fine gap at the test
cases (cheap runs at the 100 test cases; diagnostic only, not charged to any experiment)."""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from amfs.design_space import lhs_cases  # noqa: E402
from amfs.loop import load_config  # noqa: E402
from amfs.models import MultiFidelityGP, table  # noqa: E402
from amfs.oracle import Oracle, _key  # noqa: E402

rm = lambda e: float(np.sqrt(np.mean(np.square(e))))
cov = lambda m, s, y: float(np.mean(np.abs(m - y) <= 1.96 * s))


def main(seed=1, rounds=7):
    cfg = load_config(ROOT / "configs/mf_lhs.yaml")
    orc = Oracle(ROOT / "cache", cfg["fidelities"], 4, log=print)
    s = seed * 1000
    lows = lhs_cases(60, seed=s) + sum((lhs_cases(200, seed=s + r + 1) for r in range(rounds)), [])
    hnum = cfg["fidelities"]["high"]
    highs = [c for c in lows if (ROOT / "cache" / f"{_key(c, hnum)}.json").exists()]
    evals = orc.query(lows, "low") + orc.query(highs, "high")
    tc = lhs_cases(cfg["test"]["n_runs"], seed=cfg["test"]["seed"])
    Xt, yt = table(orc.query(tc, "high"), "high")
    Xtl, ytl = table(orc.query(tc, "low"), "low")
    print(f"seed {seed}: {len(lows)} low, {len(highs)} high runs; test rows {len(yt)}")

    out = {}
    for name, args in (("linear (sweep)", dict(rho=1.0, delta="linear")), ("GP delta, all 5", dict(rho=1.0, delta="gp")),
                       ("auto (CV)", dict(rho=1.0, delta="auto"))):
        m = MultiFidelityGP(seed=seed, **cfg["gp"], **args).fit(evals)
        mu_l, sd_l = m.low.predict(Xt)
        mu, sd = m.predict(Xt)
        out[name] = (mu_l, sd_l, mu, sd)
        if name.startswith("auto"):
            print(f"   auto chose {m.delta_choice}, cv {m.info['delta_cv']}")
        print(f"{name:16s} MF rmse {rm(mu - yt):.3f} cov {cov(mu, sd, yt):.2f} | low GP alone rmse "
              f"{rm(mu_l - yt):.3f} cov {cov(mu_l, sd_l, yt):.2f}", flush=True)

    key = lambda X: [tuple(np.round(r, 9)) for r in X]
    lo = dict(zip(key(Xtl), ytl))
    idx = [i for i, k in enumerate(key(Xt)) if k in lo]
    b = np.array([yt[i] - lo[k] for i, k in enumerate(key(Xt)) if k in lo])
    mu_l, sd_l, mu, sd = out["linear (sweep)"]
    print(f"true fine-minus-coarse gap at test rows: rms {rm(b):.3f}, mean {b.mean():+.3f}, max {np.abs(b).max():.2f}")
    print(f"low GP vs coarse truth (interpolation error): rms {rm(mu_l[idx] - ytl[[key(Xtl).index(key(Xt)[i]) for i in idx]]):.3f}")
    corr = (mu - mu_l)[idx]
    print(f"linear correction vs true gap: rmse {rm(corr - b):.3f}, corr {np.corrcoef(corr, b)[0, 1]:.2f}")
    err = mu - yt
    big = np.argsort(-np.abs(err))[:8]
    print("largest MF errors (err, true gap, od_id h_id mf m red):")
    for i in big:
        g = yt[i] - lo.get(key(Xt)[i], np.nan)
        print(f"  {err[i]:+.2f}  gap {g:+.2f}  {np.round(Xt[i], 2).tolist()}")
    trim = np.abs(err) < np.quantile(np.abs(err), 0.95)
    print(f"MF rmse without the worst 5% of rows: {rm(err[trim]):.3f}; low GP alone: {rm((mu_l - yt)[trim]):.3f}")


if __name__ == "__main__":
    main()
