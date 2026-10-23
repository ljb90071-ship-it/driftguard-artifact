# Paper-to-material map

|Paper item|Material|Coverage|
|---|---|---|
|Section 3, Eqs. 1–2|[trajectory_gain](src/driftguard.py), [tests](tests/test_core.py)|Aggregate cost-rate integration, bin split at T; host supplies trajectories.|
|Section 3.2, Eq. 3|[KMV and fit_growth](src/driftguard.py)|Distinct hashes, union, linear/saturating growth. Request-cell matching is specified in [architecture](docs/architecture.md).|
|Point service-cost equation|[point_cost/adverse_costs](src/driftguard.py)|Composition and conservative fallback.|
|Section 3.3, Eqs. 5–7|[affine config](configs/affine.json), [analysis](scripts/analyze.py)|Affine gain calculation and sign reversal; threshold follows algebraically from Eq. 5.|
|Section 3.4, Eqs. 8–11|[BuildRecord/predict_candidate](src/driftguard.py)|Compatible donor selection and CPU/wall/segment scaling for nonempty output.|
|Section 4, Proposition 4.1|[Range](src/driftguard.py), [JSON example](examples/operations.json), [tests](tests/test_core.py)|Freeze/write/failure/retry/publication, tombstone precedence and identity preservation.|
|Section 4.3, Eq. 12|[architecture](docs/architecture.md)|Stopping and capacity integration contract; recurrence is manuscript analysis.|
|Table 1|[dispatch](src/driftguard.py)|Frozen, mandatory, support, reservation, robust minimum-gain branches.|
|Figure 1|[timeline](figures/timeline.pdf), [example runner](examples/run.py)|Serving-state illustration and one transition execution.|
|Figure 2|[structure](figures/structure.pdf), [Range](src/driftguard.py)|Immutable merge inputs and retained D+.|
|Figure 3|[boundary/load figure](figures/boundary_load.pdf), [analytic CSV](results/figure3_analytic.csv), [load CSV](results/figure3_load.csv)|Exact plotted values; analysis validates analytic panel and 8-Mops/s table cross-reference.|
|Tables 2–5|[result browser](results/browse.html), [schema](results/schema.md), [analysis](scripts/analyze.py)|All numerical table rows and units. Table 1 is procedural, not a numerical CSV.|
|Section 6|[paper configuration](configs/paper.json)|Evaluation and estimator parameters; these are not a launcher for native systems.|
|Section 7.5 support counts|[support CSV](results/support.csv)|Bin-close support opportunity partition and attributed executions; not dispatch-time support.|

Start with `examples/run.py` for state semantics, `tests/test_core.py` for executable edge cases, and `scripts/analyze.py` for paper result accounting. Code components do not implement the paper's complete native storage engine or native comparison systems.

Revised Section 3.4 residence cap and Section 5.2 cost separation: [observable rules](src/observations.py), [edge-case tests](tests/test_observations.py), and [integration contract](docs/architecture.md). [test_analysis.py](tests/test_analysis.py) verifies that derived percentages follow the CSV values.
