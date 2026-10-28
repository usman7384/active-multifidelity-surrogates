| Strategy | Seeds | Final CPU h | Final runs (low / high) | Final RMSE | Final cov95 | Final CRPS | RMSE @ 0.25 h | RMSE @ 0.5 h | RMSE @ 0.75 h | RMSE @ 1.0 h |
|---|---|---|---|---|---|---|---|---|---|---|
| `random_lhs` | 8 | 1.05 | 0 / 125 | 0.484 ± 0.097 | 0.901 ± 0.032 | 0.215 ± 0.037 | 1.778 ± 0.353 | 0.921 ± 0.143 | 0.633 ± 0.049 | 0.520 ± 0.094 |
| `max_variance` | 8 | 1.07 | 0 / 110 | 0.839 ± 0.115 | 0.863 ± 0.052 | 0.409 ± 0.065 | 1.700 ± 0.283 | 1.075 ± 0.193 | 0.929 ± 0.154 | 0.866 ± 0.100 |
| `low_only` | 8 | 1.06 | 1675 / 0 | 0.257 ± 0.026 | 0.676 ± 0.048 | 0.110 ± 0.005 | 0.327 ± 0.035 | 0.266 ± 0.027 | 0.267 ± 0.025 | 0.260 ± 0.024 |
| `mf_lhs` | 8 | 1.10 | 1160 / 50 | 0.205 ± 0.044 | 0.911 ± 0.027 | 0.080 ± 0.012 | 0.730 ± 0.113 | 0.284 ± 0.064 | 0.229 ± 0.041 | 0.230 ± 0.035 |

Mean ± sd over seeds. "RMSE @ x h": the score of the last round at or below x solver CPU hours; – where a strategy's runs ended before x.

Paired by seed, `mf_lhs` against each strategy at matched solver cost (wins / seeds where both reached that cost, one-sided sign-test p):

| Against | CPU h | RMSE lower | p | Coverage closer to 0.95 | p |
|---|---|---|---|---|---|
| `random_lhs` | 0.25 | 8 / 8 | 0.004 | 5 / 8 | 0.363 |
| `random_lhs` | 0.5 | 8 / 8 | 0.004 | 3 / 8 | 0.855 |
| `random_lhs` | 0.75 | 8 / 8 | 0.004 | 3 / 8 | 0.855 |
| `random_lhs` | 1.0 | 8 / 8 | 0.004 | 4 / 8 | 0.637 |
| `max_variance` | 0.25 | 8 / 8 | 0.004 | 5 / 8 | 0.363 |
| `max_variance` | 0.5 | 8 / 8 | 0.004 | 5 / 8 | 0.363 |
| `max_variance` | 0.75 | 8 / 8 | 0.004 | 3 / 8 | 0.855 |
| `max_variance` | 1.0 | 8 / 8 | 0.004 | 6 / 8 | 0.145 |
| `low_only` | 0.25 | 0 / 8 | 1.000 | 7 / 8 | 0.035 |
| `low_only` | 0.5 | 3 / 8 | 0.855 | 8 / 8 | 0.004 |
| `low_only` | 0.75 | 7 / 8 | 0.035 | 8 / 8 | 0.004 |
| `low_only` | 1.0 | 6 / 8 | 0.145 | 8 / 8 | 0.004 |
