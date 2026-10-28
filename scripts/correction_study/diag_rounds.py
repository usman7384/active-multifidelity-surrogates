"""Which part moved when mf_lhs seed 0's error rose after round 3: the low GP or the linear correction?
Rebuilds each round's data from the cache (no new solves) and splits the test error."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from amfs.design_space import lhs_cases  # noqa: E402
from amfs.loop import load_config  # noqa: E402
from amfs.models import LinearDelta, fit_gp, HI5, LO5, table  # noqa: E402
from amfs.oracle import Oracle  # noqa: E402

rm = lambda e: float(np.sqrt(np.mean(np.square(e))))


def main(n_high_per_round=4, rounds=(3, 5)):
    cfg = load_config(ROOT / "configs/mf_lhs.yaml")
    orc = Oracle(ROOT / "cache", cfg["fidelities"], 4, log=lambda *_: None)
    Xt, yt = table(orc.query(lhs_cases(40, seed=12345), "high"), "high")
    init = lhs_cases(60, seed=0)
    for R in rounds:
        batches = [lhs_cases(100, seed=r + 1) for r in range(R)]
        low = orc.query(init + sum(batches, []), "low")
        high = orc.query(init[:10] + sum((b[:n_high_per_round] for b in batches), []), "high")
        Xl, yl = table(low, "low"); Xh, yh = table(high, "high")
        lgp, info = fit_gp(Xl, yl, lo=LO5, hi=HI5, n_restarts=2, iters=200)
        mu_l, sd_l = lgp.predict(Xt)
        r = yh - lgp.predict(Xh, include_noise=False)[0]
        big = np.argsort(-np.abs(r))[:3]
        print(f"round {R}: largest residuals {np.round(r[big], 2)} at (od_id h_id mf m red) {np.round(Xh[big], 2).tolist()}")
        for kind in ("ols", "huber"):
            d = LinearDelta(robust=kind == "huber").fit(Xh, r)
            mu_d, sd_d = d.predict(Xt)
            mu, sd = mu_l + mu_d, np.sqrt(sd_l ** 2 + sd_d ** 2)
            print(f"   {kind:5s} MF rmse {rm(mu - yt):.3f} cov {np.mean(np.abs(mu - yt) <= 1.96 * sd):.2f} "
                  f"w {np.round(d.w, 3)} s {d.s:.3f}")
        d = LinearDelta().fit(Xh, r)
        mu_d, sd_d = d.predict(Xt)
        mu, sd = mu_l + mu_d, np.sqrt(sd_l ** 2 + sd_d ** 2)
        print(f"round {R}: low runs {len(low)}, high runs {len(high)} | low GP alone rmse {rm(mu_l - yt):.3f} "
              f"cov {np.mean(np.abs(mu_l - yt) <= 1.96 * sd_l):.2f} | MF rmse {rm(mu - yt):.3f} "
              f"cov {np.mean(np.abs(mu - yt) <= 1.96 * sd):.2f} | residual rms {rm(r):.3f}, max {np.abs(r).max():.2f}, "
              f"w {np.round(d.w, 3)}, s {d.s:.3f} | low ls {np.round(list(info['lengthscales'].values()), 2)}",
              flush=True)


if __name__ == "__main__":
    main()
