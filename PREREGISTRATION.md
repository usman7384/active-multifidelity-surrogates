# Pre-registration: is mf_lhs more accurate than cheap runs alone?

Written and committed before any of the runs below were started. Nothing in this file, the code or the configs
changes after the commit that adds it; the analysis is `scripts/confirm.py`, committed with it.

## Why

On seeds 1-8 (`results/final`) `mf_lhs` had about 11% lower test RMSE than `low_only` at 1 CPU hour, winning
6 of 8 seeds. A sign test gives p = 0.15; a paired t-test and a Wilcoxon test give p of about 0.04, but those
tests were chosen after seeing the data, at one of several cost levels, and seed 1 was used to change the
design. So the accuracy claim is not established. This run tests it once, on fresh seeds, with everything
fixed in advance.

## Hypothesis

At 1.0 solver CPU hour, `mf_lhs` has lower held-out test RMSE than `low_only`.

## Design

- Strategies: `low_only` and `mf_lhs` only, with `configs/low_only.yaml` and `configs/mf_lhs.yaml` exactly as
  committed here (budget 3,600 CPU s, held-out test set of 100 runs, seed 777).
- Seeds: 9, 10, ..., 20 (12 seeds; none has been run before). The effect seen on seeds 1-8 (paired effect size
  about 0.73) gives about 80% power at this size.
- Run: `python scripts/sweep.py --configs low_only mf_lhs --seeds 9 ... 20 --parallel 2 --out results/confirm`.
- Every seed is run to completion and included. A run that crashes is re-run with the same seed and code; if it
  still fails it counts as a loss for `mf_lhs`.

## Primary endpoint and test

- For each seed, d = RMSE(`low_only`) - RMSE(`mf_lhs`), each RMSE taken at 1.0 CPU hour (the score of the
  last round at or below 1.0 h, as in `scripts/summarize.py`).
- One-sided Wilcoxon signed-rank test on the 12 values of d, alternative d > 0, alpha = 0.05.
- p < 0.05: the claim is supported on this problem. p >= 0.05: it is not shown; the README then says that
  `mf_lhs`'s established advantage over cheap runs is calibration, and any accuracy gain is too small to show
  at this budget.

## Secondary (reported, not used for the claim)

Sign test on the same d; mean and median relative RMSE gain; the same comparison at 0.75 h; 95% coverage of
both strategies and whether `mf_lhs` is closer to 0.95 per seed.
