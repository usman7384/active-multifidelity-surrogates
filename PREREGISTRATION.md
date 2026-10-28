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

---

# Part 2: does IVR with a fine-run floor beat mf_lhs?

Written and committed before the run below was started (28 October 2026). The code it tests is the commit that
adds this section; nothing in `amfs/`, `configs/mf_ivr_floor.yaml` or `scripts/confirm.py` changes afterwards.

## Why

`mf_ivr` (integrated variance reduction over case and fidelity, `amfs/ivr.py`) was run exploratorily on seeds
1-8 (`results/ivr`, `results/ivr_compare`). It tied `mf_lhs` on average (RMSE 0.209 against 0.230 at 1 h,
5 of 8 seeds) with worse coverage (0.88 against 0.91). Its results split by how many fine runs it bought: the
three seeds with 49-69 fine runs ended at RMSE 0.12-0.15 and coverage 0.92-0.95, the five with 19-35 at
0.22-0.27 near `low_only`. The diagnosis is that while fine runs are few, the correction's own variance is
poorly estimated, so the greedy rule under-buys them.

## The change

`MultiFidelityIVR(min_high_share=0.4)`: if a round's greedy batch spends less than 40% of its CPU seconds on
fine runs, fine runs are added in IVR order until it does. The 40% is fixed now, from seeds 1-8 only: between
`mf_lhs`'s 30% (which works) and the roughly 50% the three good IVR seeds chose on their own. It is a floor,
not a target; IVR may buy more.

## Hypothesis

At 1.0 solver CPU hour, `mf_ivr_floor` has lower held-out test RMSE than `mf_lhs`.

## Design

- Strategy: `configs/mf_ivr_floor.yaml` as committed here, run on seeds 9-20. `mf_ivr` has never been run on
  these seeds, and the floor was chosen without looking at them.
- Comparator: the `mf_lhs` results already recorded for seeds 9-20 in part 1 (`results/confirm`), copied to
  `results/confirm_ivr`. Same test set (100 runs, seed 777), same budget, same cache. Those numbers are known;
  the `mf_ivr_floor` numbers are not, and the floor was not chosen from them.
- Run: `python scripts/sweep.py --configs mf_ivr_floor --seeds 9 ... 20 --parallel 2 --out results/confirm_ivr`,
  then `python scripts/confirm.py results/confirm_ivr --a mf_lhs --b mf_ivr_floor`.
- Every seed is run to completion and included. A run that crashes is re-run with the same seed and code; if it
  still fails it counts as a loss for `mf_ivr_floor`.

## Primary endpoint and test

- For each seed, d = RMSE(`mf_lhs`) - RMSE(`mf_ivr_floor`) at 1.0 CPU hour (last round at or below 1.0 h).
- One-sided Wilcoxon signed-rank test on the 12 values of d, alternative d > 0, alpha = 0.05.
- p < 0.05: IVR with the floor is more accurate than the fixed design on this problem, and becomes the
  recommended default. p >= 0.05: not shown; `mf_lhs` stays the default and IVR stays a lead.

## Secondary (reported, not used for the claim)

Sign test; mean and median relative gain; the same comparison at 0.75 h; coverage of both and whether
`mf_ivr_floor` is closer to 0.95 per seed; the number of fine runs bought per seed; the comparison against
`low_only` on the same seeds (also recorded in part 1).
