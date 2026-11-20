# Range transitions and decision contracts

## State and authority

A range is `(B, F, D)`: base B, optional frozen delta F, active delta D. Reads resolve D, F, then B. A tombstone terminates lookup as absent; it must not fall through to an older value. Each key occupies at most one entry in each layer. `Range.write` returns whether an entry was newly added to the active delta, exposing the distinction between total writes and current-delta growth.

`freeze()` moves the active object into F and creates an empty D+. Only one F may exist. `construct(token)` captures immutable B/F inputs and merges them outside the mutex. Frozen values override base values and tombstones remove output keys. Writes during this operation continue into D+. `publish(token, candidate)` checks the generation, installs B', drops F, and keeps the same D+ object. The candidate argument must be the output of `construct` for that token. Internal layer dictionaries are implementation state, not caller mutation interfaces.

An allocation failure during construction leaves `(B,F,D+)` searchable. Retry uses the same token and captured immutable layers. A stale token cannot publish after a later freeze. Logical scans merge all three layers; their half-open interval is `[low, high)`.

The reference mutex serializes readers and writers. `construct` copies its input dictionaries under that mutex, and `publish` copies the candidate under it; these are O(n) reference operations. The paper host uses immutable buffers and a constant-size descriptor swap at publication, so reference lock duration is not a model of its critical-path cost. The paper host instead uses shared/exclusive range latches and fixed fences. Multi-range scans acquire all intersected range latches in key order. Memory reservation precedes freezing; a write that cannot reserve releases its latch, joins a FIFO queue, and requests a global capacity sweep. Reclaim retired objects first, then prioritize nonempty ranges by reclaimable bytes; try each once per sweep, retaining one protected candidate slot. A complete sweep unable to fit a request returns resource exhaustion without changing the map. This allocator/queue is a host contract rather than part of the dictionary reference range.

## Forecasting and cost units

All callable costs use CPU seconds. `trajectory_gain` accepts aggregate service rates in CPU seconds per wall second, evaluates 100-ms midpoint bins, and splits the interval at publication. The published callback receives age since freeze. To model Fresh, the host instead evaluates the newly empty publication state at age `t-T`. Foreground interference belongs in construction service cost; worker CPU and completed-candidate probes are charged once through `build_cpu_s`.

`affine_gain` implements Equation 5 with a constant publication penalty. Its assumptions are `0<T<H` and constant query rate, old/base service costs, and post-publication residual cost. It is distinct from continuing-growth trajectory integration. The analytic configuration records only the reported sum C_b + E = 0.035 CPU seconds; the analysis passes this combined charge once without inferring a worker/interference split.

KMV stores the smallest distinct normalized 64-bit hashes. Union retains the smallest k hashes from both samples. Below k distinct hashes the count is exact; otherwise the estimate is `(k-1)/h_k`. `fit_growth` selects the lower squared-error fit between a nonnegative through-origin linear model and saturation models at powers of two from 2^10 to 2^24. Hash collisions are possible; this is an estimator, not a key-membership structure.

Point composition is request-weighted, independent of write-key KMV. The host selects requests with probability 1/256 and matches 100-ms age and log2 occupancy bins with at least 64 observations per logical hit/miss class, within the paper's history and query/write ratio rules. `point_cost` combines terminating-delta and fall-through costs. `adverse_costs` handles missing composition by minimizing no-action cost and maximizing action cost. Missing path-cost evidence prevents voluntary execution.

`predict_candidate` implements the nonempty-output equations using the latest 128 compatible records, four-donor minimum, and nearest eight eligible records. The caller supplies a single builder/rank-error/foreground-worker stratum. Future output segment count is a donor target, not a current input feature. An empty-output candidate requires the host's separate measured empty-build case. This executable predictor does not substitute a small trained model for a full build.

`dispatch` exposes the seven-step decision in Table 1. Frozen work finishes/retries first. Mandatory capacity maintenance ignores negative economic gain and missing forecast support but still needs reservation. Voluntary work first requires 0 <= T < H; a candidate publishing at or after the horizon is rejected. It then needs the minimum envelope gain to exceed measurement cost. Host code refreshes estimates immediately before calling this decision.

## Accounting

Online cycle CPU includes foreground/controller work plus admitted maintenance and drain. Canonical cleanup is a separate endpoint charge. Candidate probes occur in the controller column but enter the decision once with construction CPU. Peak GiB excludes driver arrays and common correctness-oracle storage. Native-system comparisons use their own layouts; matched-substrate ablations share the storage mechanism. Neither can be inferred by timing the Python example.

## Observable residence and class-conditioned costs

`src/observations.py` implements the Section 3.5 residence rules. Each closed 100-ms bin supplies the local and global point-arrival counts. Hot means at least twice the global mean, with zero traffic treated as cold. Two consecutive contrary bins confirm a change from the start of the first bin. The detector keeps eight completed intervals, expiring each 64 seconds after exit.

`conditioned_horizon` uses the age at the end of the last observed hot bin. It retains completed intervals at least that long, subtracts the observed age from each, and takes the median when at least two remain. It then subtracts the delay from that bin to dispatch, including a first unconfirmed cold bin. A cold range or insufficient history uses only the configuration and capacity caps. The total-duration comparison uses `horizon`, which takes the median of all retained durations. Table 2 uses both predictors on the same dispatch state. The whole-workload matched policies share the total-duration cap.

The replay counts offers independently of completion. Off-range offers are common to both arms. Within each case, the reference evaluates the same stream against keeping the old range and taking the candidate. It checks the active delta's identity at publication and checks the logical map at drain. Costs come from the replay input, including the entire transition charge and the additional probe after publication.

`class_point_cost` accepts one logical class at a time. A tombstone termination is a logical miss. The denominator and termination count must be from the same class, age, occupancy and layer cell; base cost is conditional on fall-through. Aggregate cost uses each class's own request rate.

Structural CPU cells use worker-idle observations with matching operation class, layer presence, base-size/occupancy and scan-length bins. Active-worker observations only estimate `max(0, active - structural)` interference, stratified by worker count and matched query/write ratio. The construction trajectory adds structural plus residual once; worker CPU is separately charged. `interference_residual` exposes this arithmetic, not a native sampling pipeline.

## Policy admission and scheduling

All policies share mandatory precedence, reservations, worker quota and ties (earliest eligibility, then range ID). Gain-based policies rank their own positive gain/worker-CPU scores. Size uses selected threshold 65536 and descending entry count, without a profitability or horizon test. Size does not collect the policy-specific growth sketches or composition forecasts; logical membership, capacity accounting and measurements common to the host remain charged. The gain-based `dispatch` function is not Size's admission implementation.

Bin-close support describes an opportunity. At dispatch the host recomputes support and gain from current cells. `support.csv` attributes execution to the earlier bin-close label; it does not report dispatch support fractions.
