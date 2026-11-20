# DriftGuard: Pricing Residual Updates in Learned-Index Rebuilding

Replay a rebuild against waiting on the same offered stream. Then inspect the published range state, the horizon estimates, and the cost of the two choices. The repository also includes the range protocol example and the system result tables from the paper.

## Browse

- [Architecture and contracts](docs/architecture.md): layer precedence, publication, failure, and host integration.
- [Reference implementation](src/driftguard.py): exact range semantics, lower-bound validation, growth estimation, cost integration, candidate prediction, and dispatch.
- [Paper map](paper-map.md): equations, algorithm steps, figures, tables, and file locations.
- [Result tables](results/browse.html) and [field definitions](results/schema.md).
- [Timestamped replay input](configs/residence_replay.json), [system comparison parameters](configs/paper.json), and [analytic example parameters](configs/affine.json).
- [Early and late dispatch](figures/timeline.pdf), [execution substrate](figures/structure.pdf), and [analytic boundary and offered load](figures/boundary_load.pdf).
- [Dependencies and attribution](docs/dependencies.md).

## Run the lightweight components

Python 3.10 or newer is sufficient; the executable code uses only the standard library. From this directory:

```text
python -B examples/run.py
python -B examples/replay_residence.py
python -B -m unittest discover -s tests -v
python -B scripts/analyze.py
python -B scripts/render_results.py
```

The example reads [operations.json](examples/operations.json), executes writes before and during construction, and prints the logical map, new base, and residual. It asserts that publication preserves the map and the identity of the active delta. A custom input file can be supplied as the first argument. Keys and values are integers; JSON null is a deletion tombstone.

The residence replay builds the history from closed observation bins, scores the same candidate under both horizon rules, and checks that both replayed paths serve the same values. It prices each executed operation using the cost inputs in the JSON. The table reports modeled CPU savings in milliseconds and includes the late departure, long episode, unexpected extension, and common-window empty-delta comparison. View the [replay results](results/residence_replay.csv), or pass an output path with the `--csv` option.

The example and analysis commands print JSON. Saved outputs are in [expected.json](examples/expected.json) and [analysis.json](results/analysis.json). Tests cover publication and retry, exact rank correction, cost calculations, admission, and the horizon when hot episodes reach or outlast recorded durations.

`analyze.py` validates the aggregate CSVs and computes the twelve-cell geometric mean and selected comparisons. `render_results.py` writes the HTML results view. Supply an output path as its first argument to save the page elsewhere.

## Implementation boundary

The reference range uses Python dictionaries, sorted scans, and one mutex to expose the freeze/merge/publish contract. The companion functions accept observations from the storage host according to the [integration contracts](docs/architecture.md). The result tables record system summaries and the separate fixed-cost replay.
