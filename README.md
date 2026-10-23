# DriftGuard: Pricing Residual Updates in Learned-Index Rebuilding

DriftGuard prices the residual updates left by an index rebuild, connecting
rebuild timing to the work that remains after publication. Explore the
freeze/merge/publish protocol and cost calculations through a range-transition
example, checks and paper result tables.

## Navigate

- [Architecture and contracts](docs/architecture.md): layer precedence, publication, failure and host integration.
- [Implementation](src/driftguard.py): range semantics, lower-bound validation, growth estimation, cost integration, candidate prediction and dispatch.
- [Paper map](paper-map.md): equations, algorithms, figures and tables.
- [Result tables](results/browse.html) and [field definitions](results/schema.md).
- [Experiment parameters](configs/paper.json) and [analytic example parameters](configs/affine.json).
- Figures: [serving timeline](figures/timeline.pdf), [execution substrate](figures/structure.pdf), and [analytic boundary and offered load](figures/boundary_load.pdf).
- [Dependencies and attribution](docs/dependencies.md).

## Run

Use Python 3.10 or later and its standard library. Run from the repository root:

```text
python -B examples/run.py
python -B -m unittest discover -s tests -v
python -B scripts/analyze.py
python -B scripts/render_results.py
```

The example reads [operations.json](examples/operations.json), executes writes
before and during construction, and prints the logical map, new base and residual.
It checks that publication preserves the map and active-delta identity. Supply a
custom input file as the first argument; keys and values are integers, and JSON
null denotes a deletion tombstone. The implementation represents layers with
Python dictionaries, sorted scans and one mutex. The [architecture guide](docs/architecture.md)
explains its integration with index storage, latches and allocation.

[expected.json](examples/expected.json) contains the example output. Tests cover
state transitions, allocation retry, stale tokens, rank correction, repeated-key
cardinality, numerical integration, support thresholds and mandatory dispatch.

## Analyze and browse results

`analyze.py` reads aggregate CSV tables, validates accounting identities and
cross-table values, computes the twelve-cell geometric mean and selected
comparisons, and prints JSON. [analysis.json](results/analysis.json) contains the
derived comparisons. The CSV [schema](results/schema.md) defines units and
aggregation over runs.

`render_results.py` creates the static HTML result view from those CSVs; its
optional first argument selects the output path. Example and analysis commands
print to the terminal, while the renderer writes the HTML file.
