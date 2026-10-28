| Strategy | Seeds | Final CPU h | Final runs (low / high) | Final RMSE | Final cov95 | Final CRPS | RMSE @ 0.25 h | RMSE @ 0.5 h | RMSE @ 1.0 h |
|---|---|---|---|---|---|---|---|---|---|
| `random_lhs` | 5 | 1.06 | 0 / 124 | 0.386 ± 0.081 | 0.935 ± 0.013 | 0.180 ± 0.037 | 1.521 ± 0.212 | 0.828 ± 0.233 | 0.434 ± 0.086 |
| `max_variance` | 5 | 1.05 | 0 / 106 | 0.608 ± 0.082 | 0.901 ± 0.058 | 0.313 ± 0.048 | 1.540 ± 0.108 | 0.873 ± 0.125 | 0.595 ± 0.110 |
| `low_only` | 5 | 0.43 | 600 / 0 | 0.171 ± 0.011 | 0.836 ± 0.044 | 0.091 ± 0.008 | 0.228 ± 0.033 | 0.181 ± 0.000 | – |
| `mf_lhs` | 5 | 0.62 | 560 / 28 | 0.136 ± 0.015 | 0.930 ± 0.035 | 0.068 ± 0.007 | 0.341 ± 0.129 | 0.167 ± 0.017 | – |

Mean ± sd over seeds. "RMSE @ x h": the score of the last round at or below x solver CPU hours; – where a strategy's runs ended before x.
