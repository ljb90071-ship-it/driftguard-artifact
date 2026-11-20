# Result fields and populations

Headers encode units. The system CPU, latency, and memory tables report aggregates over five runs as specified in the paper. The replay table accounts for modeled CPU on a fixed input. System CSV filenames retain their original numbers for stable links.

|File|Population and fields|
|---|---|
|residence_replay.csv|Table 2 and Figure 1. Each row gives the observed age at dispatch, realized remaining hot time, two predicted horizons and their actions, local post-publication reads, installed entries, and the modeled CPU difference between waiting and building. The empty-delta prediction shares the remaining-time horizon.|
|table2_cycle.csv|Table 3. Twelve dataset/workload cells at 8 Mops/s. fresh_cpu_s and driftguard_cpu_s include drain and all admitted maintenance.|
|table3_ablation.csv|Table 4. books/Moving on one substrate. cycle_cpu_s; point_p99_us (microseconds); peak_gib (2^30 bytes).|
|table4_native.csv|Table 5. books/Moving with 16 foreground workers. HIRE+ follows the concurrent design in HIRE Section 5.8. CPU and point p99 at 8 Mops/s. stable_mops_s comes from the separate load sweep.|
|table5_cleanup.csv|Table 6. End-of-run CPU seconds. foreground_controller_cpu_s + maintenance_cpu_s + cleanup_cpu_s = total_cpu_s. The first two sum to the corresponding Table 4 online cycle.|
|figure3_analytic.csv|Equation 5, fixed post-publication residual penalty in microseconds/query. gain_cpu_ms and clean_gain_cpu_ms use CPU milliseconds. This is a calculation, not a latency measurement.|
|figure3_load.csv|books/Moving point-read p99 microseconds against offered millions of operations/s. hire_point_p99_us denotes HIRE+ in this sweep.|
|support.csv|150000 eligible bin-close range checks, each with a nonempty delta, no mandatory task and no frozen layer. Support categories partition opportunities. executed_voluntary counts executions attributed to their latest bin-close support state, summing to 1710.|

Table 3's geometric mean uses the twelve cell-wise ratios. Cleanup comparisons use the books/Moving endpoint totals in Table 6. The residual-entry error summaries in Section 7.6 use completed voluntary builds and a denominator floor of 1024 entries.

The 802-second EWMA diagnostic changes observation work and support rules together. Its 6-second difference from the cheap 808-second variant is a combined net comparison; no separate cleanup total is archived for that variant. Churn/Decoupled differences of 1-2 CPU seconds are approximately tied medians. No paired-run uncertainty is reconstructed from aggregates.

Table 6's component columns describe the run with median endpoint total. Components are summed within that run before taking the median total. Its online subtotal equals the Table 4 median in this comparison.

For the residence replay, `duration_cap_gain_cpu_ms` and `remaining_cap_gain_cpu_ms` are forecasts available at dispatch, using the same installed-state cost. `empty_delta_gain_cpu_ms` changes only that price under the remaining cap. `replayed_gain_cpu_ms` is the modeled net saving of a forced build on the full two-second offered stream. Each offered point request is counted once even if it moves to another range. Positive gain means building saves CPU relative to waiting.
