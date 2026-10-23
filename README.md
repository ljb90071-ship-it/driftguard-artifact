# DriftGuard: Pricing Residual Updates in Learned-Index Rebuilding

This companion repository provides executable reference components, a small range-transition example, paper result tables, and a guide connecting them to the manuscript. Start with the protocol example, then follow the cost model into the result summaries.

## Browse

- [Architecture and contracts](docs/architecture.md): layer precedence, publication, failure, and host integration.
- [Reference implementation](src/driftguard.py): exact range semantics, lower-bound validation, growth estimation, cost integration, candidate prediction, and dispatch.
- [Paper map](paper-map.md): equations, algorithm steps, figures, tables, and file locations.
- [Result tables](results/browse.html) and [field definitions](results/schema.md).
- [Experiment parameters](configs/paper.json) and [analytic example parameters](configs/affine.json).
- Figures: [serving timeline](figures/timeline.pdf), [execution substrate](figures/structure.pdf), [analytic boundary and offered load](figures/boundary_load.pdf).
- [Dependencies and attribution](docs/dependencies.md).

## Run the lightweight components

Python 3.10 or newer is sufficient; the executable code uses only the standard library. From this directory:

```text
python -B examples/run.py
python -B -m unittest discover -s tests -v
python -B scripts/analyze.py
python -B scripts/render_results.py
```

The example reads [operations.json](examples/operations.json), executes writes before and during construction, and prints the logical map, new base, and residual. It asserts that publication preserves the map and the identity of the active delta. A custom input file can be supplied as the first argument. Keys and values are integers; JSON null is a deletion tombstone.

The checked example output is available in [expected.json](examples/expected.json); derived aggregate comparisons are in [analysis.json](results/analysis.json). The example and analysis commands recompute these values and print JSON to the terminal; they do not overwrite the archived files. The renderer writes the HTML file.

The tests exercise state transitions, allocation failure and retry, stale tokens, rank correction, repeated-key cardinality, numerical integration, support thresholds, and mandatory dispatch. They run a serialized reference model, not a throughput benchmark.

`analyze.py` reads the archived aggregate CSVs, validates accounting identities and cross-table values, computes the twelve-cell geometric mean and selected comparisons, and writes JSON to standard output. `render_results.py` generates a static HTML view from the CSVs; an optional first argument changes the output path. These are result-analysis commands, not commands for rerunning the large-scale system experiments.

## Implementation boundary

The reference range uses Python dictionaries, sorted scans, and one mutex to expose the freeze/merge/publish contract. The paper's native B+tree layout, learned-segment builder, shared/exclusive latch implementation, worker pool, and bounded allocator belong to the system layer. Their integration contracts are described in the architecture document. Supplied functions implement the central semantics and cost calculations independently of that layout. The result archive contains paper-level aggregates, not per-request traces or per-run raw observations.
