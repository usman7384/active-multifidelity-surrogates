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

## Open decisions (next steps)

1. **Fidelity gap.** On the standard ring at mf = 0.3, a coarse run (nz = 4) costs 10 s and a fine run
   (nz = 12) 21 s, and they agree within 0.03 points. That gap is too small for multi-fidelity to pay off. The
   low fidelity needs to be much cheaper (larger time steps via `dh_frac`, or nz = 3) or the high fidelity more
   expensive (nz = 16-24), and the gap should be measured at high friction, where the meshes disagree more.
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
