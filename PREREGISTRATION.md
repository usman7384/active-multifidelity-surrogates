# Pre-registration

Each part was written and committed before its runs were started. Nothing in the code or configs it names
changed afterwards; the analysis is `scripts/confirm.py`, committed with it.

## Part 1: is mf_lhs more accurate than cheap runs alone?

On seeds 1-8 (`results/final`) `mf_lhs` had about 11% lower test RMSE than `low_only` at 1 CPU hour, winning
6 of 8 seeds (sign test p = 0.15). This run tests the claim once, on fresh seeds, with everything fixed in
advance.

**Hypothesis.** At 1.0 solver CPU hour, `mf_lhs` has lower held-out test RMSE than `low_only`.

**Design.**

- Strategies: `low_only` and `mf_lhs`, with `configs/low_only.yaml` and `configs/mf_lhs.yaml` as committed
  (budget 3,600 CPU s, held-out test set of 100 runs, seed 777).
- Seeds 9-20 (12 seeds, none run before). The effect on seeds 1-8 (paired effect size about 0.73) gives about
  80% power at this size.
- `python scripts/sweep.py --configs low_only mf_lhs --seeds 9 ... 20 --parallel 2 --out results/confirm`.
- Every seed is run to completion and included. A run that crashes is re-run with the same seed and code; if it
  still fails it counts as a loss for `mf_lhs`.

**Primary test.** For each seed, d = RMSE(`low_only`) − RMSE(`mf_lhs`) at 1.0 CPU hour (the score of the last
round at or below 1.0 h). One-sided Wilcoxon signed-rank test on the 12 values of d, alternative d > 0,
α = 0.05. p < 0.05: the claim is supported on this problem; otherwise it is not shown.

**Secondary (reported, not used for the claim).** Sign test; mean and median relative RMSE gain; the same
comparison at 0.75 h; 95% coverage of both and whether `mf_lhs` is closer to 0.95 per seed.

**Result.** [results/confirm/confirm.md](results/confirm/confirm.md).

---

## Part 2: does IVR with a fine-run floor beat mf_lhs?

`mf_ivr` on seeds 1-8 (`results/ivr_compare`) tied `mf_lhs` on average (RMSE 0.209 against 0.230 at 1 h,
5 of 8 seeds) with worse coverage (0.88 against 0.91). Its result tracked how many fine runs it bought: the
three seeds with 49-69 fine runs ended at RMSE 0.12-0.15, the five with 19-35 at 0.22-0.27.

**The change.** `MultiFidelityIVR(min_high_share=0.4)`: if a round's greedy batch spends less than 40% of its
CPU seconds on fine runs, fine runs are added in IVR order until it does. The 40% is fixed from seeds 1-8
only: between `mf_lhs`'s 30% and the roughly 50% the three good IVR seeds chose on their own. It is a floor;
IVR may buy more.

**Hypothesis.** At 1.0 solver CPU hour, `mf_ivr_floor` has lower held-out test RMSE than `mf_lhs`.

**Design.**

- `configs/mf_ivr_floor.yaml` as committed, on seeds 9-20. `mf_ivr` has never been run on these seeds, and the
  floor was chosen without looking at them.
- Comparator: the `mf_lhs` results recorded for seeds 9-20 in part 1 (`results/confirm`), copied to
  `results/confirm_ivr`. Same test set, budget and cache.
- `python scripts/sweep.py --configs mf_ivr_floor --seeds 9 ... 20 --parallel 2 --out results/confirm_ivr`,
  then `python scripts/confirm.py results/confirm_ivr --a mf_lhs --b mf_ivr_floor`.
- Every seed is run to completion and included. A run that crashes is re-run with the same seed and code; if it
  still fails it counts as a loss for `mf_ivr_floor`.

**Primary test.** For each seed, d = RMSE(`mf_lhs`) − RMSE(`mf_ivr_floor`) at 1.0 CPU hour. One-sided
Wilcoxon signed-rank test on the 12 values of d, alternative d > 0, α = 0.05. p < 0.05: IVR with the floor
is more accurate than the fixed design on this problem and becomes the recommended default; otherwise
`mf_lhs` stays the default.

**Secondary (reported, not used for the claim).** Sign test; mean and median relative gain; the same
comparison at 0.75 h; coverage of both and whether `mf_ivr_floor` is closer to 0.95 per seed; the number of
fine runs bought per seed; the comparison against `low_only` on the same seeds.

**Result.** [results/confirm_ivr/confirm.md](results/confirm_ivr/confirm.md).
