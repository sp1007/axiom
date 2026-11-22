# E11.5 — Executor & Fiber Benchmarks (`tests/perf/p11_executor`)

Task `T424`, `REQ-ASY-165`. Bundles are generated like `tests/conformance/p11/e11_5_executors` (live std sources +
`src/<name>.axsrc` + `src/_common.axsrc`; `gen_tests.py`, `check_perf_bundles.test`).

Each benchmark runs 5 rounds, takes the **median** wall time (monotonic clock), checks the workload result exactly
and asserts a deliberately generous upper bound (>= 10x the slowest observed MIR-interpreter figure, ~1000x native)
so a loaded machine cannot flake it. The observed figures are written to **stderr** as `BENCH <name> ops=..
median_total_ns=.. ns_per_op=..` (timings differ per run, and the runner compares stdout of the interpreter and the
native runs byte for byte, so they must not be on stdout). Stdout carries the deterministic `OK <name> <size>` line
(`stdout-contains`), and `stderr-contains: BENCH <name> ops=` proves the measurement ran in every mode.

| Benchmark | Measures |
|---|---|
| `spawn_poll_throughput` | Single-thread `LocalExecutor`: spawn + two polls + completion per task. |
| `steal_fanout_fanin` | 4-worker work-stealing `Executor`: fan out tasks through a `TaskGroup`, fan the results in; latency per task. |
| `channel_ping_pong` | Two tasks bouncing a value over two capacity-1 async channels; one op = one message. |
| `fiber_switch_overhead` | `Fiber` resume + yield round trip (two context switches). |

`results.csv` holds the committed numbers (native / native-O1 at a larger workload than the suite uses, interp at the
suite size). The suite sizes are small because the MIR interpreter needs about 1-60 ms per op.
