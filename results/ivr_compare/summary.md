| Strategy | Seeds | Final CPU h | Final runs (low / high) | Final RMSE | Final cov95 | Final CRPS | RMSE @ 0.25 h | RMSE @ 0.5 h | RMSE @ 0.75 h | RMSE @ 1.0 h |
|---|---|---|---|---|---|---|---|---|---|---|
| `low_only` | 8 | 1.06 | 1675 / 0 | 0.257 ± 0.026 | 0.676 ± 0.048 | 0.110 ± 0.005 | 0.327 ± 0.035 | 0.266 ± 0.027 | 0.267 ± 0.025 | 0.260 ± 0.024 |
| `mf_lhs` | 8 | 1.10 | 1160 / 50 | 0.205 ± 0.044 | 0.911 ± 0.027 | 0.080 ± 0.012 | 0.730 ± 0.113 | 0.284 ± 0.064 | 0.229 ± 0.041 | 0.230 ± 0.035 |
| `mf_ivr` | 8 | 1.08 | 1440 / 38 | 0.205 ± 0.055 | 0.883 ± 0.053 | 0.080 ± 0.019 | 0.582 ± 0.232 | 0.254 ± 0.035 | 0.230 ± 0.043 | 0.209 ± 0.052 |

Mean ± sd over seeds. "RMSE @ x h": the score of the last round at or below x solver CPU hours; – where a strategy's runs ended before x.

Paired by seed, `mf_lhs` against each strategy at matched solver cost (wins / seeds where both reached that cost, one-sided sign-test p):

| Against | CPU h | RMSE lower | p | Coverage closer to 0.95 | p |
|---|---|---|---|---|---|
| `low_only` | 0.25 | 0 / 8 | 1.000 | 7 / 8 | 0.035 |
| `low_only` | 0.5 | 3 / 8 | 0.855 | 8 / 8 | 0.004 |
| `low_only` | 0.75 | 7 / 8 | 0.035 | 8 / 8 | 0.004 |
| `low_only` | 1.0 | 6 / 8 | 0.145 | 8 / 8 | 0.004 |
| `mf_ivr` | 0.25 | 0 / 8 | 1.000 | 2 / 8 | 0.965 |
| `mf_ivr` | 0.5 | 3 / 8 | 0.855 | 4 / 8 | 0.637 |
| `mf_ivr` | 0.75 | 3 / 8 | 0.855 | 7 / 8 | 0.035 |
| `mf_ivr` | 1.0 | 3 / 8 | 0.855 | 7 / 8 | 0.035 |
