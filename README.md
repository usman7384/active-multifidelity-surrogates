# active-multifidelity-surrogates

**How many solver runs does a calibrated surrogate actually need, and how much can you save by choosing them
well and mixing cheap and expensive meshes?**

A small, focused follow-up to [forming-surrogates](https://github.com/usman7384/forming-surrogates). That
project trained a Gaussian-process surrogate of the ring compression test on 460 solver runs from a fixed
Latin hypercube. Here the same solver and the same GP are put in a loop, and four ways of spending the same
solver budget (1 CPU hour) are compared on a held-out fine-mesh test set, over eight seeds each.

## Result

For the one-page version, see [media/result_overview.png](media/result_overview.png); for the 71-second
animated explainer, [media/explainer.mp4](media/explainer.mp4) (source in [media/explainer](media/explainer)).

![test error and coverage against solver CPU hours, eight seeds per strategy](results/final/cost_curves.png)

Thin lines: one seed each. Thick lines: the median over the eight seeds. Test set: 100 fine-mesh runs (274
rows) that were never looked at while the strategies were designed. Final scores, mean ± sd over seeds 1-8
([table](results/final/summary.md), [data](results/final/summary.json)):

| Strategy | How the next runs are chosen | CPU h | Runs (cheap / fine) | Test RMSE (points) | 95% coverage | CRPS |
|---|---|---|---|---|---|---|
| `random_lhs` | more Latin-hypercube cases, fine mesh (the forming-surrogates approach) | 1.05 | 0 / 125 | 0.484 ± 0.097 | 0.90 ± 0.03 | 0.215 |
| `max_variance` | fine-mesh cases where the current GP is most unsure | 1.07 | 0 / 110 | 0.839 ± 0.115 | 0.86 ± 0.05 | 0.409 |
| `low_only` | more Latin-hypercube cases, cheap mesh only | 1.06 | 1675 / 0 | 0.257 ± 0.026 | 0.68 ± 0.05 | 0.110 |
| **`mf_lhs`** | cheap Latin-hypercube cases plus ~30% of solver time on random fine cases; multi-fidelity GP | 1.10 | 1160 / 50 | **0.205 ± 0.044** | **0.91 ± 0.03** | **0.080** |

Paired by seed, `mf_lhs` against the other strategies at the same solver cost (one-sided sign test; with 8
seeds, 8/8 gives p = 0.004 and 7/8 gives p = 0.035):

| Against | at 0.5 CPU h | at 0.75 CPU h | at 1.0 CPU h |
|---|---|---|---|
| `random_lhs`, lower RMSE | 8 / 8 | 8 / 8 | 8 / 8 |
| `low_only`, lower RMSE | 3 / 8 | 7 / 8 | 6 / 8 (p = 0.15) |
| `low_only`, coverage closer to 0.95 | 8 / 8 | 8 / 8 | 8 / 8 |

What it shows:

- **Mixing meshes beats fine runs alone, clearly.** `mf_lhs` has lower error than `random_lhs` in every seed at
  every cost, by about 2.3x at 1 CPU hour, with the same coverage. Uncertainty-driven fine sampling
  (`max_variance`) is worse than random fine sampling.
- **Cheap runs alone become confidently wrong.** `low_only` stalls: its error stays near 0.26 from 0.5 to 1 CPU
  hour (900 to 1,900 cheap runs) while its coverage falls from 0.77 to 0.69. More cheap data makes the GP surer
  of the coarse mesh's answer, not the fine one. `mf_lhs` keeps coverage near 0.90 in all eight seeds
  (p = 0.004). This is the main result.
- **Mixing meshes is also more accurate than cheap runs alone, confirmed on fresh seeds.** On seeds 1-8 the
  gain was suggestive but not significant (6 of 8 at 1 h, p = 0.15), so a confirmation was pre-registered
  ([PREREGISTRATION.md](PREREGISTRATION.md), committed before any run) and run on twelve new seeds; see below.
  Below 0.5 CPU hours cheap runs alone are more accurate: `mf_lhs` pays up front for fine runs.
- **Nothing reaches 95% coverage on this test set.** The best strategies sit near 0.90, so every interval here
  is somewhat too narrow; `low_only`'s are far too narrow.

### Pre-registered confirmation: `mf_lhs` against `low_only`, seeds 9-20

Hypothesis, test and seeds were fixed and committed before the runs: one-sided Wilcoxon signed-rank on
d = RMSE(`low_only`) − RMSE(`mf_lhs`) at 1.0 CPU hour, twelve seeds never run before, α = 0.05, code frozen
([confirm.md](results/confirm/confirm.md), [data](results/confirm/confirm.json)). One restart, allowed by the
pre-registration: the first attempt ran out of memory when a third job shared the machine; it was rerun on the
same code and its logs are kept in `results/confirm/logs_crashed_oom_1601`.

| at 1.0 CPU h, seeds 9-20 | `low_only` | `mf_lhs` |
|---|---|---|
| Test RMSE, mean | 0.251 | 0.178 |
| 95% coverage, mean | 0.67 | 0.94 |

- **Primary: supported, p = 0.0005.** `mf_lhs` has lower RMSE in 11 of 12 seeds (sign test p = 0.003); mean
  relative gain 29.5%, median 34.7%. The one loss is seed 14 (0.290 against 0.255).
- At 0.75 CPU h the gain also holds (Wilcoxon p = 0.026). Coverage is closer to 0.95 in 12 of 12 seeds.

### Exploratory: integrated variance reduction (`mf_ivr`), seeds 1-8

`mf_ivr` (`amfs/ivr.py`) picks case and mesh greedily by the predictive variance a run removes, averaged over
a fixed reference set of 300 cases, per CPU second; the posterior covariance is downdated exactly after each
pick, so a batch accounts for what its earlier picks will teach. It decides for itself how many fine runs to
buy. Not pre-registered: seeds 1-8, the same as the main table, so read it as a lead, not a result
([summary](results/ivr_compare/summary.md)).

| at 1.0 CPU h, seeds 1-8 | `low_only` | `mf_lhs` | `mf_ivr` |
|---|---|---|---|
| Test RMSE, mean ± sd | 0.260 ± 0.024 | 0.230 ± 0.035 | 0.209 ± 0.052 |
| 95% coverage, final mean | 0.68 | 0.91 | 0.88 |
| Fine runs, final mean | 0 | 50 | 38 (19-69) |

- **Against `mf_lhs`: no clear difference.** Lower RMSE in 5 of 8 seeds at 1 h, and earlier on (0.25-0.5 h)
  it is better on average, since it does not pay for fine runs before they are worth it. Its coverage is
  worse (`mf_lhs` closer to 0.95 in 7 of 8).
- **Against `low_only`:** lower RMSE in 7 of 8 seeds at 0.75 and 1 h, coverage closer to 0.95 in 8 of 8.
- **It is less stable.** How many fine runs it buys varies 19-69 by seed, and that drives the result:
  the three seeds with 49-69 fine runs end at RMSE 0.12-0.15 and coverage 0.92-0.95, the five with 19-35
  end at 0.22-0.27, near `low_only`, with coverage 0.79-0.91. The variance it computes for the correction is
  itself uncertain while fine runs are few, so it under-buys them.
  A floor on the fine-run share is the obvious next fix; until then `mf_lhs` is the safer default.

## How it works

```
initial LHS runs -> fit GP -> score on test set -> strategy proposes a batch -> solve -> refit -> ...
                                                                    until the solver budget is spent
```

- **Oracle** (`amfs/oracle.py`): the ring solver behind a cache. Every call names a fidelity (a mesh
  resolution) and every result keeps the CPU time of its original solve, so budgets are counted in real solver
  CPU seconds and stay identical when a run is read back from the cache. CPU time, not wall time: wall time was
  inflated by other jobs on the machine during the pilot. Cache writes are atomic, so parallel experiments share
  one cache.
- **Data** (`amfs/design_space.py`): a case is (od_id, h_id, mf, m) in the forming-surrogates training box. Each
  run is pressed to 30.5% and read at 10, 20 and 30%, giving up to three rows of (od_id, h_id, mf, m, reduction)
  -> inner-diameter change. Runs that stop early (fold-over at high friction) give fewer rows.
- **Models** (`amfs/models.py`): the forming-surrogates GP (Matérn 5/2, ARD, exact). Above 1,000 rows its
  hyper-parameters are fitted on a random 1,000-row subsample and the posterior is conditioned on every row, so
  a refit stays about a minute at 5,000 rows; the rule is the same for every strategy. The multi-fidelity GP is
  autoregressive, f_high = rho * f_low + delta: a GP on all cheap rows plus a correction delta on the fine rows'
  residuals. `mf_lhs` uses rho = 1 and picks delta every round by 5-fold cross-validation over its fine runs:
  a Huber-fitted straight line in friction and reduction, or a GP on all five inputs. The line wins while fine
  runs are few, the GP once there are enough of them (about 30-60).
- **Scores** (`amfs/metrics.py`): RMSE, 95% coverage, CRPS and mean predictive sd on the fixed fine-mesh test
  set (its own seed; not charged to any budget).

## The fidelity pair

`scripts/fidelity_study.py` ran two rings at six frictions on eight numerics levels against nz = 16
([results](results/fidelity/fidelity_study.json), [figure](results/fidelity/fidelity_study.png)):

| Level | Seconds per run | RMSE vs nz16 (all) | RMSE at mf >= 0.6 | Runs stopped early (of 12) |
|---|---|---|---|---|
| **cheap: nz = 4, dh_frac = 0.04** | 2.3 | 0.105 | 0.165 | 1 |
| nz = 4 | 12.6 | 0.096 | 0.152 | 1 |
| nz = 8 | 24.0 | 0.020 | 0.026 | 3 |
| **fine: nz = 12** | 27.1 | 0.013 | 0.013 | 4 |
| nz = 16 (reference) | 70.9 | 0 | 0 | 5 |

The time step, not the mesh, is the cheap lever: 4x larger steps cut the coarse run from 12.6 s to 2.3 s for
almost no extra error. In the sweeps, on CPU time, a cheap run costs about 2 s and a fine run about 34 s. The
coarse-minus-fine gap is small at low friction and on thin rings, and reaches 1-2 points on thick rings near
fold-over at 30% reduction.

## How mf_lhs came about

Each step was diagnosed offline on cached runs, without new solves. The records are in
[results/pilot](results/pilot) ([correction_study.md](results/pilot/correction_study.md)) and the scripts in
`scripts/correction_study/`.

1. **`multi_fidelity`** (first version, `configs/multi_fidelity.yaml`, pilot only): choose case and mesh by
   predictive variance removed per solver second. It lost to cheap runs alone (RMSE 0.25 against 0.16 on the
   pilot test set). 82% of its cheap runs landed within 10% of a box edge (58% for a Latin hypercube), and it
   never judged a fine run worth its cost.
2. **Variance-picked fine runs, GP correction**: still worse than cheap runs alone. Variance put the fine runs in
   the hardest cases (residual 0.43 points rms, against 0.19 at random cases), so the correction learned an
   unrepresentative bias and over-corrected. Fine runs are now a random subset of each round's cheap batch.
3. **Random fine runs, least-squares line**: one fine run with a 2.6-point residual tilted the line; a Huber fit
   and a MAD-based interval width fixed it on the pilot data (seed 0: 0.236 to 0.115, coverage 0.95).
4. **Held-out check, cross-validated correction**: on the held-out test set with the full budget, the line
   stalled with `low_only` (seed 1: 0.233). The thick-ring gap the Huber fit treats as outliers is real and
   common there, and with 61 fine runs a GP correction resolves it (0.119, coverage 0.92). The choice between
   the two is now made each round by cross-validation over the fine runs. That is valid only because the fine
   runs are random; with the variance-picked runs of step 2 it disagreed with the test set.

The first five-seed sweep ([results/sweep](results/sweep)) used the pilot test set, a 6-round cap and step 3's
correction; it is kept as a record and superseded by `results/final`.

## Run

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q                                      # about 1 minute, includes three tiny experiments
python scripts/run.py configs/mf_lhs.yaml --seed 1       # one experiment, about 15-20 minutes on 4 workers
python scripts/sweep.py --configs random_lhs max_variance low_only mf_lhs --seeds 1 2 3 4 5 6 7 8 \
    --parallel 2 --out results/final                     # about 4 hours on 8 cores
python scripts/summarize.py results/final                # figure, table, paired tests (sweep.py runs it too)
```

The sweep is resumable (a finished strategy and seed is skipped), and seeds draw separate Latin hypercubes
(`seed * 1000 + round`).

## Caveats

- **One problem, one solver.** Every number is for the ring test on this solver and this mesh pair. The fine
  mesh is the reference, not the truth (it is within 0.013 points of nz = 16).
- **The accuracy gain over cheap runs holds at 0.75-1 CPU hour, not below.** It was confirmed on twelve
  pre-registered seeds (p = 0.0005), after being only suggestive on seeds 1-8. Its size differs between the two
  sets (12% on seeds 1-8, 30% on seeds 9-20), so treat it as roughly 10-35%, not a precise figure.
- **Seed 1 was looked at.** The held-out diagnosis in step 4 used seed 1's results on the held-out test set.
  Seeds 2-8 are untouched: on them alone, coverage is closer to 0.95 in 7 of 7 (p = 0.008) and RMSE lower in
  6 of 7 at 0.75 h (p = 0.06), 5 of 7 at 1 h.
- **Coverage is below 0.95 for every strategy** (0.90 at best), so no interval here is fully calibrated.
- **The fine-run share (30%) and the batch sizes were not tuned.** CPU time was measured with two experiments
  sharing the machine, which inflates every strategy's cost similarly but not exactly.

## Next steps

1. `mf_ivr` with a floor on the fine-run share, then a pre-registered comparison against `mf_lhs` on new seeds.
2. Tune the fine-run share on a validation set, and calibrate the intervals (all strategies sit near 0.90).
3. A decision-aware acquisition that targets rings near the spec boundary, where go/check/stop verdicts flip.

## Provenance

`ringsim/solver.py`, `amfs/gp.py` and `amfs/calibration.py` are copied unchanged from forming-surrogates
(commit `3a0bc31`); each file says so in its first line. `amfs/oracle.py` is adapted from
`surrogates/gp_bo/solver_calls.py`. Everything else is new. The solver is verified, not validated: see the
forming-surrogates README for what that means and what it does not cover.
