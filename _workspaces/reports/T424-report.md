# T424 report

E11.5 executor benchmarks, fiber and structured-cancellation conformance suite (`REQ-ASY-165`). Tests only: no compiler or
std file was touched.

## Summary

Two new test trees, both generated from the live std sources in the same way as `tests/std/async/*` and `tests/std/fiber`
(`gen_tests.py` concatenates the std files verbatim with `src/<name>.axsrc`; a `check_*_bundles.test` fails when a bundle
drifts from `std/`):

- `tests/conformance/p11/e11_5_executors/` - 9 run tests (each `interp`, `native`, `native-O1`, exact `stdout:`) plus the
  bundle freshness check.
- `tests/perf/p11_executor/` - 4 benchmarks plus the freshness check, `results.csv` with the committed numbers.

Conformance tests (each proves something the T421-T423 unit tests do not):

| test | what it proves |
|---|---|
| `cancel_tree_groups` | 4-group cancellation tree on the 4-worker `Executor`: token cancel flows down only; cooperative children finish, non-cooperative loopers survive a token cancel and end on `cancel_all` / group `Drop`; zero leaked / double-dropped futures |
| `sibling_failure_isolation` | a panicking child cancels exactly its own group's siblings (1 panicked, 3 cancelled), never a sibling group, the parent or a child group's neighbours |
| `cancel_race_linearizes` | 32 spawn+cancel races at varying delay: each outcome is `Completed(7)` or `Cancelled`, never `Panicked`/wrong value, future dropped once |
| `local_cancel_drop_order` | deterministic `LocalExecutor`: FIFO polls, cancellation drops without another poll in wake order, dropping an unawaited `LocalTaskHandle` cancels |
| `asyncmutex_cancel_wakes_next` | `AsyncMutex` through real task cancellation (cancelled queued waiter, cancelled granted waiter, cancelled holder across `.await`): the lock always reaches the next waiter in FIFO order |
| `spawn_affinity_vs_migration` | `spawn` migrates (4 rendezvous tasks need 4 distinct worker threads, a worker's children are stolen, `steal_count() >= 1`); `spawn_local` is pinned (48 polls all on the owner thread, header records owner, `spawn` records 0) |
| `channel_cancel_safety` | cancelled receiver/sender never swallows or duplicates a message nor blocks the next waiter |
| `fiber_switch_conformance` | 1000 exact switches with a stack-resident accumulator, 3 interleaved fibers, 40-frame suspension, dropped suspended fiber, `FiberScheduler` round robin |
| `fiber_in_async_and_threads` | fiber resumed from a `LocalExecutor` task between polls, per-thread fibers on 4 OS threads, a main-thread fiber surviving other threads |

## Benchmark numbers

Median of 5 rounds, native (`axiomc2 build`, Windows x64, 4-core shared laptop under load from other agents). One op as
in `tests/perf/p11_executor/README.md`. Full table: `tests/perf/p11_executor/results.csv`.

| benchmark | size | native ns/op | native-O1 ns/op | interp ns/op (suite size) |
|---|---|---|---|---|
| `spawn_poll_throughput` (LocalExecutor spawn + 2 polls) | 20000 tasks | 1931 | 1282 | 11,350,977 (40 tasks) |
| `steal_fanout_fanin` (4 workers, TaskGroup fan-out/in, per task) | 1024 tasks | 63759 (21 steals) | 29493 (87 steals) | 56,773,081 (16 tasks) |
| `channel_ping_pong` (one message) | 10000 msgs | 1985 | 697 | 9,124,007 (40 msgs) |
| `fiber_switch_overhead` (resume + yield = 2 switches) | 200000 | 625 | 583 | 1,081,759 (300) |

Robustness: every benchmark checks its workload result exactly and asserts a bound >= 10x the slowest observed interpreter
figure (about 1000x native), so a loaded machine cannot flake it. Timings are written to **stderr**
(`stderr-contains: BENCH <name> ops=` proves the measurement ran in every mode) because the runner compares interp and
native stdout byte for byte (T139); stdout carries the deterministic `OK <name> <size>` line.

## Verification (all in `build-snap-T424`, axiomc2 built by `tools/build_axiomc.py`)

- `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal --no-cache -j 2 --filter conformance/p11/e11_5_executors`: TOTAL 28 PASS 28 FAIL 0, WEAK-NATIVE 0.
- same with `--filter perf/p11_executor`: TOTAL 13 PASS 13 FAIL 0, WEAK-NATIVE 0.
- `--filter p11` (whole P11 conformance + perf tree) run twice: TOTAL 157 PASS 157 both times (no flake).
- native-evidence spot proof: in the snapshot, `channel_cancel_safety.ax` expectation changed `... 9 6 0 1` -> `... 9 6 0 2`:
  interp, native and native-O1 all FAIL (`stdout differs at byte 31`); restored, 3/3 PASS.
- `python tools/archcheck.py`: 0 violations. `reqcov.py --strict`: COVERAGE OK (gaps: 0). `harness_check.py`: HARNESS OK.
- The full suite of the acceptance line was not run by me: the per-task gate scope (axiom-qa.md) replaces it; this task only
  adds files nobody references, so its affected set is its own tests.

## Design decisions

- Sizes are small because the MIR interpreter needs 1-60 ms per task/message; native sizes for the committed figures
  were measured with a scaled copy (same source, larger constants) built in a scratch directory.
- `check()` failure mode: a failed assertion prints `FAIL line <n>` and spins until the timeout (same scheme as the T422
  bundles; not `assert()`, so the exact-stdout comparison is the evidence natively).
- `str` literals cannot be turned into a pointer identically in interp and native, so `gen_tests.py` expands
  `eput("...")` into one `eput_byte(..)` per character for the benchmark stderr report.
- A racy `alive == 12` check (short steppers can already have finished and dropped) was removed from
  `sibling_failure_isolation`; the end-of-test `alive == 0` is the invariant.

## Follow-ups (for the architect; none blocks T424)

- `std/sys/windows/io.ax:144` (`let len = GetEnvironmentVariableW(...)`) emits `AX_NAME_SHADOW_MODULE` warning in every
  bundle that includes it (the perf bundles need it for `__ax_host_stdio`/`__ax_host_write` natively). Owner of std/sys:
  rename the local. The warning does not fail the runner (exit 0).
- Observation: `worker_pop_local` is LIFO and fairness only checks the global queue every 61 polls, so tasks that keep
  re-waking themselves (`Looper`) in one worker's local deque can only be reached by thieves; the suite stays within what
  the executor guarantees, but a livelock under many self-waking tasks on few workers is conceivable. Not a failing repro.
- `tests/std/async/*` bundles and these bundles embed std sources; a std edit requires regenerating both (the
  `check_*_bundles.test` files report it).

## Files changed
- tests/conformance/p11/e11_5_executors/README.md
- tests/conformance/p11/e11_5_executors/asyncmutex_cancel_wakes_next.ax
- tests/conformance/p11/e11_5_executors/cancel_race_linearizes.ax
- tests/conformance/p11/e11_5_executors/cancel_tree_groups.ax
- tests/conformance/p11/e11_5_executors/channel_cancel_safety.ax
- tests/conformance/p11/e11_5_executors/check_conformance_bundles.test
- tests/conformance/p11/e11_5_executors/fiber_in_async_and_threads.ax
- tests/conformance/p11/e11_5_executors/fiber_switch_conformance.ax
- tests/conformance/p11/e11_5_executors/gen_tests.py
- tests/conformance/p11/e11_5_executors/local_cancel_drop_order.ax
- tests/conformance/p11/e11_5_executors/sibling_failure_isolation.ax
- tests/conformance/p11/e11_5_executors/spawn_affinity_vs_migration.ax
- tests/conformance/p11/e11_5_executors/src/asyncmutex_cancel_wakes_next.axsrc
- tests/conformance/p11/e11_5_executors/src/cancel_race_linearizes.axsrc
- tests/conformance/p11/e11_5_executors/src/cancel_tree_groups.axsrc
- tests/conformance/p11/e11_5_executors/src/channel_cancel_safety.axsrc
- tests/conformance/p11/e11_5_executors/src/fiber_in_async_and_threads.axsrc
- tests/conformance/p11/e11_5_executors/src/fiber_switch_conformance.axsrc
- tests/conformance/p11/e11_5_executors/src/local_cancel_drop_order.axsrc
- tests/conformance/p11/e11_5_executors/src/sibling_failure_isolation.axsrc
- tests/conformance/p11/e11_5_executors/src/spawn_affinity_vs_migration.axsrc
- tests/perf/p11_executor/README.md
- tests/perf/p11_executor/channel_ping_pong.ax
- tests/perf/p11_executor/check_perf_bundles.test
- tests/perf/p11_executor/fiber_switch_overhead.ax
- tests/perf/p11_executor/gen_tests.py
- tests/perf/p11_executor/results.csv
- tests/perf/p11_executor/spawn_poll_throughput.ax
- tests/perf/p11_executor/src/_common.axsrc
- tests/perf/p11_executor/src/channel_ping_pong.axsrc
- tests/perf/p11_executor/src/fiber_switch_overhead.axsrc
- tests/perf/p11_executor/src/spawn_poll_throughput.axsrc
- tests/perf/p11_executor/src/steal_fanout_fanin.axsrc
- tests/perf/p11_executor/steal_fanout_fanin.ax

STATUS: COMPLETE round=0
