# Result fields and populations

CSV decimal points use `.`; headers encode units. Each row is an aggregate value indexed by its named dataset, workload, policy, or offered load. No CSV contains a raw run log. The CPU/latency/memory tables use medians over five runs as specified in the manuscript; their rows do not encode uncertainty intervals.

|File|Population and fields|
|---|---|
|table2_cycle.csv|Twelve dataset/workload cells at 8 Mops/s. fresh_cpu_s and driftguard_cpu_s are cycle CPU seconds including admitted maintenance and drain, excluding canonical cleanup.|
|table3_ablation.csv|books/Moving matched substrate. cycle_cpu_s; point_p99_us (microseconds); peak_gib (2^30 bytes).|
|table4_native.csv|books/Moving, 16 foreground workers. CPU and p99 at 8 Mops/s; stable_mops_s is millions of operations/s from a separate stability sweep, not the offered load used for the other columns.|
|table5_cleanup.csv|CPU seconds after workload execution: foreground_controller_cpu_s + maintenance_cpu_s + cleanup_cpu_s = total_cpu_s. First two columns equal the online cycle in Table 3.|
|figure3_analytic.csv|Equation 5, fixed post-publication residual penalty in microseconds/query. gain_cpu_ms and clean_gain_cpu_ms use CPU milliseconds. This is a calculation, not a latency measurement.|
|figure3_load.csv|books/Moving point-read p99 microseconds against offered millions of operations/s.|
|support.csv|150000 eligible bin-close range checks, each with a nonempty delta, no mandatory task and no frozen layer. Support categories partition opportunities. executed_voluntary counts executions attributed to their latest bin-close support state, summing to 1710.|

The geometric mean is taken over the twelve paired ratios in Table 2. It is not the ratio of two arithmetic means. Cleanup comparisons use Table 5 totals; do not combine that denominator with the twelve-cell online aggregate. Residual-entry error summaries in Section 7.5 are conditional on completed voluntary builds, with denominator floor 1024; they are not encoded as artificial raw error samples in this archive.

The 802-second EWMA diagnostic changes observation work and support rules together. Its 6-second difference from the cheap 808-second variant is a combined net comparison; no separate cleanup total is archived for that variant. Churn/Decoupled differences of 1-2 CPU seconds are approximately tied medians. No paired-run uncertainty is reconstructed from aggregates.

Table 5 component columns describe the run with median endpoint total; total is summed within that run. Its online subtotal also equals the Table 3 median in this comparison. Independently computed component medians need not add to a median total.
