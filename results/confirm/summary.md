| Strategy | Seeds | Final CPU h | Final runs (low / high) | Final RMSE | Final cov95 | Final CRPS | RMSE @ 0.25 h | RMSE @ 0.5 h | RMSE @ 0.75 h | RMSE @ 1.0 h |
|---|---|---|---|---|---|---|---|---|---|---|
| `low_only` | 12 | 1.07 | 1683 / 0 | 0.258 ± 0.025 | 0.666 ± 0.014 | 0.110 ± 0.005 | 0.318 ± 0.027 | 0.261 ± 0.031 | 0.257 ± 0.028 | 0.251 ± 0.027 |
| `mf_lhs` | 12 | 1.06 | 1110 / 51 | 0.168 ± 0.043 | 0.933 ± 0.025 | 0.069 ± 0.013 | 0.793 ± 0.091 | 0.262 ± 0.063 | 0.222 ± 0.045 | 0.178 ± 0.057 |

Mean ± sd over seeds. "RMSE @ x h": the score of the last round at or below x solver CPU hours; – where a strategy's runs ended before x.

Paired by seed, `mf_lhs` against each strategy at matched solver cost (wins / seeds where both reached that cost, one-sided sign-test p):

| Against | CPU h | RMSE lower | p | Coverage closer to 0.95 | p |
|---|---|---|---|---|---|
| `low_only` | 0.25 | 0 / 12 | 1.000 | 11 / 12 | 0.003 |
| `low_only` | 0.5 | 7 / 12 | 0.387 | 12 / 12 | 0.000 |
| `low_only` | 0.75 | 9 / 12 | 0.073 | 12 / 12 | 0.000 |
| `low_only` | 1.0 | 11 / 12 | 0.003 | 12 / 12 | 0.000 |
