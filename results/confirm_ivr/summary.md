| Strategy | Seeds | Final CPU h | Final runs (low / high) | Final RMSE | Final cov95 | Final CRPS | RMSE @ 0.25 h | RMSE @ 0.5 h | RMSE @ 0.75 h | RMSE @ 1.0 h |
|---|---|---|---|---|---|---|---|---|---|---|
| `mf_lhs` | 12 | 1.06 | 1110 / 51 | 0.168 ± 0.043 | 0.933 ± 0.025 | 0.069 ± 0.013 | 0.793 ± 0.091 | 0.262 ± 0.063 | 0.222 ± 0.045 | 0.178 ± 0.057 |
| `mf_ivr_floor` | 12 | 1.10 | 880 / 70 | 0.197 ± 0.058 | 0.918 ± 0.030 | 0.077 ± 0.017 | 0.793 ± 0.091 | 0.308 ± 0.115 | 0.253 ± 0.045 | 0.229 ± 0.055 |

Mean ± sd over seeds. "RMSE @ x h": the score of the last round at or below x solver CPU hours; – where a strategy's runs ended before x.

Paired by seed, `mf_lhs` against each strategy at matched solver cost (wins / seeds where both reached that cost, one-sided sign-test p):

| Against | CPU h | RMSE lower | p | Coverage closer to 0.95 | p |
|---|---|---|---|---|---|
| `mf_ivr_floor` | 0.25 | 0 / 12 | 1.000 | 0 / 12 | 1.000 |
| `mf_ivr_floor` | 0.5 | 7 / 12 | 0.387 | 6 / 12 | 0.613 |
| `mf_ivr_floor` | 0.75 | 9 / 12 | 0.073 | 7 / 12 | 0.387 |
| `mf_ivr_floor` | 1.0 | 10 / 12 | 0.019 | 6 / 12 | 0.613 |
