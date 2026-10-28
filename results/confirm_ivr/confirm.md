# Pre-registered confirmation: mf_ivr_floor vs mf_lhs at 1.0 CPU hour

Seeds analysed: [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

| Seed | RMSE mf_lhs | RMSE mf_ivr_floor | d | cov95 mf_lhs | cov95 mf_ivr_floor |
|---|---|---|---|---|---|
| 9 | 0.172 | 0.257 | -0.084 | 0.92 | 0.89 |
| 10 | 0.126 | 0.284 | -0.158 | 0.97 | 0.89 |
| 11 | 0.112 | 0.150 | -0.038 | 0.96 | 0.95 |
| 12 | 0.162 | 0.252 | -0.090 | 0.96 | 0.91 |
| 13 | 0.110 | 0.261 | -0.151 | 0.93 | 0.86 |
| 14 | 0.290 | 0.281 | +0.009 | 0.89 | 0.92 |
| 15 | 0.161 | 0.176 | -0.014 | 0.93 | 0.95 |
| 16 | 0.149 | 0.169 | -0.020 | 0.95 | 0.94 |
| 17 | 0.195 | 0.199 | -0.005 | 0.97 | 0.95 |
| 18 | 0.250 | 0.143 | +0.107 | 0.92 | 0.92 |
| 19 | 0.147 | 0.297 | -0.149 | 0.93 | 0.89 |
| 20 | 0.260 | 0.276 | -0.015 | 0.89 | 0.89 |

**Primary:** one-sided Wilcoxon signed-rank, d = RMSE(mf_lhs) - RMSE(mf_ivr_floor) at 1.0 h: p = 0.9895 -> not shown (p >= 0.05)

Secondary: mf_ivr_floor lower RMSE in 2 / 12 seeds (sign test p = 0.997); mean relative gain -40.5%, median -23.5%; Wilcoxon at 0.75 h p = 0.912; coverage mf_lhs 0.94, mf_ivr_floor 0.91, mf_ivr_floor closer to 0.95 in 6 / 12.
