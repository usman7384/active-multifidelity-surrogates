# Pre-registered confirmation: mf_lhs vs low_only at 1.0 CPU hour

Seeds analysed: [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

| Seed | RMSE low_only | RMSE mf_lhs | d | cov95 low_only | cov95 mf_lhs |
|---|---|---|---|---|---|
| 9 | 0.212 | 0.172 | +0.039 | 0.66 | 0.92 |
| 10 | 0.216 | 0.126 | +0.089 | 0.69 | 0.97 |
| 11 | 0.254 | 0.112 | +0.142 | 0.68 | 0.96 |
| 12 | 0.270 | 0.162 | +0.108 | 0.69 | 0.96 |
| 13 | 0.261 | 0.110 | +0.151 | 0.68 | 0.93 |
| 14 | 0.255 | 0.290 | -0.034 | 0.65 | 0.89 |
| 15 | 0.252 | 0.161 | +0.091 | 0.66 | 0.93 |
| 16 | 0.224 | 0.149 | +0.075 | 0.68 | 0.95 |
| 17 | 0.237 | 0.195 | +0.043 | 0.65 | 0.97 |
| 18 | 0.295 | 0.250 | +0.045 | 0.70 | 0.92 |
| 19 | 0.234 | 0.147 | +0.087 | 0.63 | 0.93 |
| 20 | 0.301 | 0.260 | +0.041 | 0.69 | 0.89 |

**Primary:** one-sided Wilcoxon signed-rank, d = RMSE(low_only) - RMSE(mf_lhs) at 1.0 h: p = 0.0005 -> supported (p < 0.05)

Secondary: mf_lhs lower RMSE in 11 / 12 seeds (sign test p = 0.003); mean relative gain +29.5%, median +34.7%; Wilcoxon at 0.75 h p = 0.026; coverage low_only 0.67, mf_lhs 0.94, mf_lhs closer to 0.95 in 12 / 12.
