# Correction study (seed-0 pilot data, offline, no new solves)

One-off diagnostics run on the cached pilot data; kept as the record behind the mf_lhs design. They read the
cache from the pilot run (timestamps and the pre-CPU-time cache format are hard-coded), so they are not
expected to rerun unchanged.

## Error split (diag_error_split.py)
```
runs {'low': 560, 'high': 31}
rho 0.976
low GP alone      rmse 0.156  cov 0.84
MF (low + delta)  rmse 0.243  cov 0.87
delta's mean correction  rms 0.283
true fine-minus-coarse bias at test rows: rms 0.141, mean +0.061, max |0.481| (n=111)
correction predicted vs true bias: rmse 0.235, corr 0.55
low GP error vs coarse truth at test rows (interpolation only): rmse 0.084

```

## Study 1: corrections trained on the variance-picked fine runs
```
low rows 1665, fine runs 31
variant                  test rmse  cov95  loro rmse
none (cheap GP only)         0.156   0.84      0.429
constant bias                0.150   1.00      0.437
linear in mf, red            0.176   1.00      0.449
GP on (mf, red)              0.531   0.86      0.813
GP on (mf, m, red)           0.278   0.97      0.579
GP on all 5 (current)        0.261   0.87      0.368

```

## Study 2: corrections trained on random fine runs (test RMSE / cov95)
```
random fine runs: 70, residual rms 0.194 (mf_lhs's variance-picked runs: about 0.43)
n_high=10  none: 0.156/0.84  constant bias: 0.171/0.95  linear in mf, red: 0.176/0.97  GP(mf,red): 0.238/0.86  GP(mf,m,red): 0.178/0.95  GP all 5: 0.229/0.86
n_high=20  none: 0.156/0.84  constant bias: 0.144/0.98  linear in mf, red: 0.132/0.98  GP(mf,red): 0.209/0.88  GP(mf,m,red): 0.161/0.95  GP all 5: 0.163/0.91
n_high=30  none: 0.156/0.84  constant bias: 0.140/0.98  linear in mf, red: 0.123/0.99  GP(mf,red): 0.238/0.85  GP(mf,m,red): 0.152/0.96  GP all 5: 0.142/0.97
n_high=50  none: 0.156/0.84  constant bias: 0.139/0.98  linear in mf, red: 0.122/0.99  GP(mf,red): 0.258/0.84  GP(mf,m,red): 0.152/0.96  GP all 5: 0.140/0.98
n_high=70  none: 0.156/0.84  constant bias: 0.141/0.99  linear in mf, red: 0.126/0.99  GP(mf,red): 0.184/0.86  GP(mf,m,red): 0.165/0.97  GP all 5: 0.107/0.99
```

## Study 3: outliers in the linear correction (scripts/correction_study/diag_rounds.py, mf_lhs seed 0)

mf_lhs seed 0's error rose from 0.179 (round 3) to 0.236 (round 5) while the low GP alone improved (0.178 -> 0.155).
Cause: one fine run with a 2.61-point residual (typical ~0.2); the three largest are all thick rings near fold-over
at 30% reduction. Least squares lets it tilt the whole correction. Huber IRLS plus a MAD-based interval width:
```
round 3: least squares rmse 0.179 cov 0.98 | Huber rmse 0.159 cov 0.94   (low GP alone 0.178 / 0.86)
round 5: least squares rmse 0.236 cov 0.98 | Huber rmse 0.115 cov 0.95   (low GP alone 0.155 / 0.85)
```
