"""Offline, part 2: is the problem WHERE the fine runs are? Train each correction on RANDOM fine runs
(random_lhs seed-0's training runs, Latin hypercube) instead of mf_lhs's variance-picked ones; score on the test set.
Reads the cache directly (old entries have no cpu_s, which the new oracle would re-solve)."""
import json, os, sys
import numpy as np
sys.path.insert(0, r"D:\Projects\active-multifidelity-surrogates")
os.chdir(r"D:\Projects\active-multifidelity-surrogates")
from amfs.design_space import lhs_cases, case_array, rows_for, READ_AT
from amfs.gp import NumpyGP
from amfs.oracle import _key, _read

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from study_1_variance_picked import VARIANTS, rm  # noqa: E402

HIGH = {"nz": 12}


def rows(cases):
    out = []
    for c in cases:
        r = json.load(open(f"cache/{_key(c, HIGH)}.json"))
        X = rows_for(case_array([c])); y = _read(r); k = np.isfinite(y)
        out.append((X[k], y[k]))
    return out


def main():
    lgp = NumpyGP.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lowgp.npz"))
    train = rows(lhs_cases(20, seed=0) + sum((lhs_cases(10, seed=r) for r in range(5)), []))
    test = rows(lhs_cases(40, seed=12345))
    Xt = np.vstack([x for x, _ in test]); yt = np.concatenate([y for _, y in test])
    mu_l, sd_l = lgp.predict(Xt)
    res = [(X, y - lgp.predict(X, include_noise=False)[0]) for X, y in train]
    allr = np.concatenate([r for _, r in res])
    print(f"random fine runs: {len(res)}, residual rms {rm(allr):.3f} (mf_lhs's variance-picked runs: about 0.43)")
    for n in (10, 20, 30, 50, 70):
        Xh = np.vstack([x for x, _ in res[:n]]); rh = np.concatenate([r for _, r in res[:n]])
        line = []
        for name, make in VARIANTS.items():
            mu_d, sd_d = make().fit(Xh, rh).predict(Xt)
            mu, sd = mu_l + mu_d, np.sqrt(sd_l ** 2 + sd_d ** 2)
            line.append(f"{name.split(' (')[0]}: {rm(mu - yt):.3f}/{np.mean(np.abs(mu - yt) <= 1.96 * sd):.2f}")
        print(f"n_high={n:2d}  " + "  ".join(line), flush=True)


if __name__ == "__main__":
    main()
