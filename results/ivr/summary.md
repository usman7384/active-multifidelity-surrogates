| Strategy | Seeds | Final CPU h | Final runs (low / high) | Final RMSE | Final cov95 | Final CRPS | RMSE @ 0.25 h | RMSE @ 0.5 h | RMSE @ 0.75 h | RMSE @ 1.0 h |
|---|---|---|---|---|---|---|---|---|---|---|
| `mf_ivr` | 8 | 1.08 | 1440 / 38 | 0.205 ± 0.055 | 0.883 ± 0.053 | 0.080 ± 0.019 | 0.582 ± 0.232 | 0.254 ± 0.035 | 0.230 ± 0.043 | 0.209 ± 0.052 |

Mean ± sd over seeds. "RMSE @ x h": the score of the last round at or below x solver CPU hours; – where a strategy's runs ended before x.
