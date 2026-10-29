# active-multifidelity-surrogates

You have a simulator that is accurate but slow, and a version of it that is fast but a little off. You have one
hour of computer time to teach a model what the simulator would say for any input. How should you spend it?

This repository answers that for one metal-forming test, with code you can run and a result you can check.
It is a follow-up to [forming-surrogates](https://github.com/usman7384/forming-surrogates), which built the
model and the solver; here the solver is put in a loop and the ways of feeding it are compared.

![44-second explainer](media/explainer_short.gif)

Watch: the [44-second cut](media/explainer_short.mp4) or the [2½-minute version](media/explainer.mp4).
Read: the [one-page diagram](media/result_overview.png).

## The short answer

Mix them. Spend most of the hour on cheap runs to learn the shape of the response, and about a third of it on
accurate runs to learn how far off the cheap ones are. For the same hour this gave about 30% lower error than
cheap runs alone, 2.3x lower than accurate runs alone, and a model whose "95% sure" was right 94% of the time
(cheap runs alone: 67%). Letting the model choose where to run, instead of spreading runs evenly, did not help.

| Strategy | Runs in one CPU hour | Test error (RMSE) | "95% sure" right |
|---|---|---|---|
| accurate runs only (`random_lhs`) | 125 | 0.48 | 90% |
| accurate runs where the model is least sure (`max_variance`) | 110 | 0.84 | 86% |
| cheap runs only (`low_only`) | 1,675 | 0.26 | 68% |
| **mix, spread evenly (`mf_lhs`)** | 1,160 cheap + 50 accurate | **0.21** | **91%** |
| mix, model chooses (`mf_ivr`) | 1,440 cheap + 38 accurate | 0.21 | 88% |

Mean over 8 random seeds, scored on 100 held-out accurate runs. Full tables: [results/final/summary.md](results/final/summary.md),
[results/ivr_compare/summary.md](results/ivr_compare/summary.md). The headline claim (the mix beats cheap runs
alone) was then re-tested on 12 fresh seeds with the test fixed in advance: it held, p = 0.0005
([results/confirm/confirm.md](results/confirm/confirm.md)). The model-chooses variant was re-tested the same
way against the even spread and lost, 2 of 12 ([results/confirm_ivr/confirm.md](results/confirm_ivr/confirm.md)).

## Try it

```bash
git clone https://github.com/usman7384/active-multifidelity-surrogates
cd active-multifidelity-surrogates
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q                                      # two minutes; runs three tiny experiments
```

Then run one real experiment. This solves about 1,200 cheap and 50 accurate ring tests and refits the model
after every batch; it takes 15-20 minutes on four cores:

```bash
python scripts/run.py configs/mf_lhs.yaml --seed 1
```

It writes `results/mf_lhs_seed1.json`. Open it: `history` has one entry per round with the CPU seconds
spent so far, how many runs of each kind were solved, and the test error and coverage at that point. Every
solver call is cached in `cache/`, so running again is instant and other strategies reuse the same runs.

To compare strategies, run a sweep and summarise it:

```bash
python scripts/sweep.py --configs random_lhs low_only mf_lhs --seeds 1 2 3 --parallel 2 --out results/mine
python scripts/summarize.py results/mine
```

`summarize.py` writes `summary.md` (final scores per strategy, and each strategy against `mf_lhs` seed by seed
at matched cost), `summary.json`, and `cost_curves.png` (test error against CPU hours, one line per seed).

## How it works

**The test.** A metal ring is pressed between two plates and its inner diameter changes; by how much depends
on the ring's size and wall thickness, the friction with the plates, and the material. The solver
(`ringsim/`) simulates this. One "case" is a choice of those four inputs; one "run" presses the ring to 30% and
reads the diameter at 10, 20 and 30%, so it yields three training rows.

**Two fidelities.** The same solver on a fine mesh (34 CPU seconds per run, within 0.013 of a reference mesh)
or a coarse mesh with large time steps (2 seconds, off by about 0.1 on average and more on thick rings).
`scripts/fidelity_study.py` is how these two levels were chosen; its results are in `results/fidelity/`.

**The model** (`amfs/models.py`). A Gaussian process, which predicts a value and how unsure it is. For the mix,
the model is two of them: one fitted to all the cheap runs, and a correction fitted to the difference between
accurate and cheap results at the cases that have both. The correction is a straight line in friction and
reduction while accurate runs are few, and a GP once there are enough; which one is chosen by cross-validation
each round.

**The loop** (`amfs/loop.py`). Start from 60 cheap and 10 accurate runs spread evenly. Repeat: fit the model,
score it on the held-out test set, ask the strategy for the next batch, solve it, until the CPU budget is
spent. Costs are the solver's own CPU seconds, so a run read from the cache still counts what it cost to
solve.

**The strategies** (`amfs/strategies.py`). Each proposes the next batch of (case, fidelity):

- `random_lhs` and `low_only`: a fresh Latin hypercube each round, evenly spread, decided in advance. Fine mesh
  for the first, cheap for the second.
- `max_variance`: accurate runs where the model is least sure. Active learning in its simplest form; it keeps
  picking the corners of the input space and does badly.
- `mf_lhs`: a Latin-hypercube cheap batch, plus accurate runs on a random 30%-of-cost subset of it.
- `mf_ivr`: integrated variance reduction. For every candidate case and both meshes, how much of the model's
  total uncertainty one run would remove per CPU second; take the best, update, repeat (`amfs/ivr.py`).
  `min_high_share` forces a minimum share of accurate runs.

To add your own, write a class with `name`, `model` (`single_fidelity` or `multi_fidelity`) and a
`propose(evals, model, batch, round_idx, seed)` that returns a list of `(case, "low" | "high")`, register it in
`STRATEGIES`, and point a config at it.

**Scoring** (`amfs/metrics.py`). RMSE, the share of test rows inside the model's 95% interval ("coverage"),
and CRPS, on 100 accurate runs that were never used for anything else.

## How the claim was tested

Eight seeds gave the picture above but, for the mix against cheap runs alone, only a suggestive 6 of 8. Rather
than add seeds until it looked good, the test was written down and committed before running: which two
strategies, which twelve new seeds, which statistic, which threshold (commit `38791d6`). The result was
11 of 12, Wilcoxon p = 0.0005. The same was done for the model-chooses variant with a forced share of accurate
runs, against the even spread (commit `de44413`): 2 of 12, p = 0.99. `scripts/confirm.py` is the analysis; it
reads a results folder and compares two strategies seed by seed at one CPU hour.

## Repository map

```
amfs/           the loop, models, strategies, acquisition, metrics
configs/        one YAML per strategy; smoke_*.yaml are the tiny ones the tests use
scripts/        run.py (one experiment), sweep.py (many), summarize.py, confirm.py, fidelity_study.py
results/        final (8 seeds, 4 strategies), confirm and confirm_ivr (12 seeds each), ivr_compare, fidelity
media/          the videos, the GIF and the diagram
ringsim/        the ring solver, copied from forming-surrogates
tests/          smoke tests on tiny budgets
```

## What to keep in mind

- One problem, one solver, one mesh pair. The fine mesh is the reference, not the truth.
- No strategy reaches 95% coverage here (0.94 at best), so every interval is a little too narrow.
- The 30% share of accurate runs and the batch sizes were not tuned.
- CPU time was measured with two experiments sharing the machine, which inflates every strategy's cost
  similarly but not exactly.

Next: find out why the runs the model picks teach a worse correction than random ones (the likely cause is that
its most uncertain cases are the hardest ones); tune the accurate-run share; calibrate the intervals.

`ringsim/solver.py`, `amfs/gp.py` and `amfs/calibration.py` are copied unchanged from forming-surrogates. MIT licence.
