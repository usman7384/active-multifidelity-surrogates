"""Split mf_lhs's final test error: low GP alone vs low GP + correction, and how big the true bias is."""
import datetime, glob, json, os, sys
import numpy as np
sys.path.insert(0, r"D:\Projects\active-multifidelity-surrogates")
os.chdir(r"D:\Projects\active-multifidelity-surrogates")
from amfs.design_space import lhs_cases
from amfs.models import MultiFidelityGP, table
from amfs.oracle import Oracle


def main():
    cfg = json.load(open("results/mf_lhs_seed0.json"))["config"]
    orc = Oracle("cache", cfg["fidelities"], 4, log=lambda *_: None)
    a = datetime.datetime(2026, 10, 28, 0, 22, 22).timestamp()
    new_high = [json.load(open(f))["case"] for f in glob.glob("cache/*.json")
                if os.path.getmtime(f) > a and json.load(open(f))["numerics"].get("nz") == 12]
    init = lhs_cases(60, seed=0)
    low_cases = init + sum((lhs_cases(100, seed=r + 1) for r in range(5)), [])
    evals = orc.query(low_cases, "low") + orc.query(init[:10] + new_high, "high")
    test = orc.query(lhs_cases(40, seed=12345), "high")
    Xt, yt = table(test, "high")
    test_low = orc.query(lhs_cases(40, seed=12345), "low")       # coarse runs at the test cases (cheap)
    Xtl, ytl = table(test_low, "low")
    print("runs", {f: sum(e.fidelity == f for e in evals) for f in ("low", "high")})

    mf = MultiFidelityGP(seed=0, iters=200, restarts=2).fit(evals)
    mu_l, sd_l = mf.low.predict(Xt)
    mu, sd = mf.predict(Xt)
    mu_d, _ = mf.delta.predict(Xt)
    rm = lambda e: float(np.sqrt(np.mean(e ** 2)))
    cov = lambda m, s: float(np.mean(np.abs(m - yt) <= 1.96 * s))
    print(f"rho {mf.rho:.3f}")
    print(f"low GP alone      rmse {rm(mu_l - yt):.3f}  cov {cov(mu_l, sd_l):.2f}")
    print(f"MF (low + delta)  rmse {rm(mu - yt):.3f}  cov {cov(mu, sd):.2f}")
    print(f"delta's mean correction  rms {rm(mu_d + (mf.rho - 1) * mu_l):.3f}")
    # the true bias at the test cases, where both meshes reached the same reduction
    key = lambda X: [tuple(np.round(r, 9)) for r in X]
    lo = dict(zip(key(Xtl), ytl))
    pairs = [(lo[k], y, k) for k, y in zip(key(Xt), yt) if k in lo]
    b = np.array([y - l for l, y, _ in pairs])
    print(f"true fine-minus-coarse bias at test rows: rms {rm(b):.3f}, mean {b.mean():+.3f}, max |{np.abs(b).max():.3f}| (n={len(b)})")
    idx = [list(key(Xt)).index(k) for _, _, k in pairs]
    pred_corr = (mu - mu_l)[idx]
    print(f"correction predicted vs true bias: rmse {rm(pred_corr - b):.3f}, corr {np.corrcoef(pred_corr, b)[0, 1]:.2f}")
    print(f"low GP error vs coarse truth at test rows (interpolation only): rmse {rm(mu_l[idx] - np.array([l for l, _, _ in pairs])):.3f}")


if __name__ == '__main__':
    main()
