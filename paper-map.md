# Paper-to-material map

|Paper item|Material|Coverage|
|---|---|---|
|Section 3, Eqs. 1–2|[trajectory_gain](src/driftguard.py), [tests](tests/test_core.py)|Aggregate cost-rate integration, bin split at T; host supplies trajectories.|
|Section 3.2, Eq. 3|[KMV and fit_growth](src/driftguard.py)|Distinct hashes, union, linear/saturating growth. Request-cell matching is specified in [architecture](docs/architecture.md).|
|Point service-cost equation|[point_cost/adverse_costs](src/driftguard.py)|Composition and conservative fallback.|
|Section 3.3, Eqs. 5–7|[affine config](configs/affine.json), [analysis](scripts/analyze.py)|Affine gain calculation and sign reversal; threshold follows algebraically from Eq. 5.|
|Section 3.4, Eqs. 8–11|[BuildRecord/predict_candidate](src/driftguard.py)|Compatible donor selection and CPU/wall/segment scaling for nonempty output.|
|Section 3.5|[ResidenceCap](src/observations.py), [edge cases](tests/test_observations.py)|Point-arrival history, total-duration and age-conditioned horizons.|
|Section 4, Proposition 4.1|[Range](src/driftguard.py), [JSON example](examples/operations.json), [tests](tests/test_core.py)|Freeze/write/failure/retry/publication, tombstone precedence and identity preservation.|
|Section 4.3, Eq. 12|[architecture](docs/architecture.md)|Stopping and capacity integration contract; recurrence is manuscript analysis.|
|Table 1|[dispatch](src/driftguard.py)|Frozen, mandatory, support, reservation, robust minimum-gain branches.|
|Figure 1 and Table 2|[timeline](figures/timeline.pdf), [input](configs/residence_replay.json), [runner](examples/replay_residence.py), [results](results/residence_replay.csv)|Figure 1 aligns early and late publication with the same hotspot departure. Table 2 adds the long, extended, and same-window cases with modeled CPU costs.|
|Figure 2|[structure](figures/structure.pdf), [Range](src/driftguard.py)|The figure traces one key through the immutable merge inputs and retained D+.|
|Figure 3|[boundary/load figure](figures/boundary_load.pdf), [analytic CSV](results/figure3_analytic.csv), [load CSV](results/figure3_load.csv)|The analytic panel marks the zero crossing. The load panel uses the same offered-load scale for both systems. The analysis validates the analytic values and the 8-Mops/s table entries.|
|Tables 3–6|[result browser](results/browse.html), [schema](results/schema.md), [analysis](scripts/analyze.py)|System comparison summaries, ablations and cleanup. The historical CSV filenames retain their original numbers.|
|Section 6|[paper configuration](configs/paper.json)|Evaluation and estimator parameters.|
|Section 7.6 support counts|[support CSV](results/support.csv)|Bin-close support opportunity partition and attributed executions.|

Start with `examples/run.py` for state semantics, `tests/test_core.py` for executable edge cases, and `scripts/analyze.py` for paper result accounting. Code components do not implement the paper's complete native storage engine or native comparison systems.

Section 5.2 cost separation uses the [observable rules](src/observations.py) and [integration contract](docs/architecture.md). [test_analysis.py](tests/test_analysis.py) verifies that derived percentages follow the CSV values.
