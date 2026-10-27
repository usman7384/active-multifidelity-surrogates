# active-multifidelity-surrogates

**How many solver runs does a calibrated surrogate actually need, and how much can you save by choosing them
well and mixing cheap and expensive meshes?**

A small, focused follow-up to [forming-surrogates](https://github.com/usman7384/forming-surrogates). That
project trained a Gaussian-process surrogate of the ring compression test on 460 solver runs from a fixed
Latin hypercube. Here the same solver and the same GP are put in a loop, and three ways of spending a solver
budget are compared on one fixed test set:

| Strategy | How the next runs are chosen | Status |
|---|---|---|
| `random_lhs` | more Latin-hypercube cases, fine mesh (the forming-surrogates approach) | working |
| `max_variance` | cases where the current GP is most unsure, fine mesh | working, first version |
| `multi_fidelity` | case *and* mesh, by uncertainty reduction per solver second | planned |

The result this repo is built to produce is one figure: **test error and 95% coverage against solver CPU
hours**, one line per strategy, over several seeds.

## How it works

```
initial LHS runs -> fit GP -> score on test set -> strategy proposes a batch -> solve -> refit -> ...
                                                                  until the solver budget is spent
```

- **Oracle** (`amfs/oracle.py`): the ring solver behind a cache. Every call names a fidelity (a mesh resolution)
  and every result keeps the CPU time of its original solve, so budgets are counted in real solver seconds and
  stay identical when a run is read back from the cache.
- **Data** (`amfs/design_space.py`): a case is (od_id, h_id, mf, m) in the forming-surrogates training box. Each
  run is pressed to 30.5% and read at 10, 20 and 30%, giving up to three rows of (od_id, h_id, mf, m, reduction)
  -> inner-diameter change. Runs that stop early (fold-over at high friction) give fewer rows.
- **Model** (`amfs/models.py`): the forming-surrogates GP (Matérn 5/2, ARD, GPyTorch fit, numpy serving), fitted
  on fine-mesh rows. The multi-fidelity GP is specified in its docstring and not built yet.
- **Scores** (`amfs/metrics.py`): RMSE, 95% coverage, CRPS and mean predictive sd on a fixed fine-mesh test set
  of 40 runs (its own seed; not charged to any budget).

## Run

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q                                      # about 1.5 minutes, includes a tiny experiment
python scripts/run.py configs/random_lhs.yaml --seed 0
python scripts/run.py configs/max_variance.yaml --seed 0
python scripts/plot.py results/*.json --out results/cost_curves.png
```

A default experiment spends 3,600 solver seconds (about 170 fine-mesh runs); with 4 workers that is roughly
15-20 minutes plus the GP refits. Results land in `results/<name>_seed<k>.json`.

## The fidelity pair (decided)

`scripts/fidelity_study.py` ran two rings at six frictions on eight numerics levels against nz = 16
([results](results/fidelity/fidelity_study.json), [figure](results/fidelity/fidelity_study.png)):

| Level | Seconds per run | RMSE vs nz16 (all) | RMSE at mf >= 0.6 | Runs stopped early (of 12) |
|---|---|---|---|---|
| **low: nz = 4, dh_frac = 0.04** | 2.3 | 0.105 | 0.165 | 1 |
| nz = 4 | 12.6 | 0.096 | 0.152 | 1 |
| nz = 8 | 24.0 | 0.020 | 0.026 | 3 |
| **high: nz = 12** | 27.1 | 0.013 | 0.013 | 4 |
| nz = 16 (reference) | 70.9 | 0 | 0 | 5 |

- The time step, not the mesh, is the cheap lever: 4x larger steps cut the coarse run from 12.6 s to 2.3 s for
  almost no extra error. The pair is about 12x apart in cost.
- The coarse error is systematic: near zero at low friction, and a growing over-prediction of the shrink at high
  friction (up to 0.28 points). That is the kind of bias a correction GP can learn.
- Finer meshes fold over *earlier* (their small corner elements hit the collapse limit sooner), so at high
  friction the expensive runs reach 30% less often than the cheap ones.
- Every mesh error is small: the worst coarse error is about the lab gauge noise (0.3 points) and about 3x the
  GP's own error. Multi-fidelity has to beat "just use cheap runs" as well as "just use fine runs".

## Open decisions (next steps)

1. **Multi-fidelity model and strategy:** being built (`amfs/models.py`, `amfs/strategies.py`).
2. **Acquisition.** `max_variance` is the simplest active rule. Better: integrated variance reduction over a
   reference set, or a decision-aware score that targets rings near the spec boundary, where go/check/stop
   verdicts flip.
3. **Seeds.** Run every strategy over at least 5 seeds and report the spread, so differences are established
   rather than single-run noise.
4. **Bias check.** Active sampling concentrates data in hard regions; check coverage over the whole box, not only
   where the strategy sampled.

## Provenance

`ringsim/solver.py`, `amfs/gp.py` and `amfs/calibration.py` are copied unchanged from forming-surrogates
(commit `3a0bc31`); each file says so in its first line. `amfs/oracle.py` is adapted from
`surrogates/gp_bo/solver_calls.py`. Everything else is new. The solver is verified, not validated: see the
forming-surrogates README for what that means and what it does not cover.
