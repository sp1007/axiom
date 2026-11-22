# E11.5 — Executor, Structured-Cancellation & Fiber Conformance Suite (`tests/conformance/p11/e11_5_executors`)

Governing specification: `spec/SPEC-34-executors-fibers.md` (Phase 11, Epic E11.5, Task `T424`, `REQ-ASY-165`).

Every `.ax` file is a generated bundle: the live std sources it needs (`std/async/*.ax`, `std/fiber/mod.ax`,
platform layer) followed by the test program from `src/<name>.axsrc`. Regenerate with
`python tests/conformance/p11/e11_5_executors/gen_tests.py`; `check_conformance_bundles.test` fails when a
bundle drifts from the live sources. Every test is `modes: interp native` (the runner adds `native-O1`) and
compares an exact `stdout:` line; a failed internal check prints `FAIL line <n>` and spins until the timeout.

| Test | Rules | What it proves |
|---|---|---|
| `cancel_tree_groups.ax` | AXS-EXEC-020/022/023 | Four-group cancellation tree (root, g1, g2, g2a) on the 4-worker `Executor`: a token cancels downwards only, cooperative children finish with their value, non-cooperative loopers survive a token cancel and end only on `cancel_all` / group `Drop`; zero leaked or double-dropped futures. |
| `sibling_failure_isolation.ax` | AXS-EXEC-020 item 2 | A panicking child cancels exactly its own group's siblings (1 panicked + 3 cancelled) and never a sibling group, parent group or child group's neighbours. |
| `cancel_race_linearizes.ax` | AXS-EXEC-023 item 2 | Completion-versus-cancel race (32 spawn/cancel pairs, varying delay): every outcome is `Completed(7)` or `Cancelled`, never `Panicked`/wrong, future dropped exactly once. |
| `local_cancel_drop_order.ax` | AXS-EXEC-016, REQ-ASY-060 | Deterministic `LocalExecutor`: strict FIFO polls, cancellation drops the future without another poll in wake order, dropping an unawaited `LocalTaskHandle` cancels its task. |
| `asyncmutex_cancel_wakes_next.ax` | AXS-EXEC-031 | `AsyncMutex` cancellation safety through real task cancellation: cancelled queued waiter, cancelled already-granted waiter, cancelled holder across `.await` — the lock always reaches the next waiter in FIFO order. |
| `spawn_affinity_vs_migration.ax` | AXS-EXEC-010..012, REQ-CONC-151 | `spawn` migrates (4 rendezvous tasks need 4 distinct worker threads, children of a worker are stolen: `steal_count() >= 1`); `spawn_local` is pinned (every poll of 48 on the owning thread, header records the owner, `spawn` records 0). |
| `channel_cancel_safety.ax` | AXS-EXEC-034 | Async channels: a cancelled receiver/sender never swallows or duplicates a message and never blocks the next waiter. |
| `fiber_switch_conformance.ax` | AXS-EXEC-050..053 | 1000 exact resume/yield switches with a stack-resident accumulator, three interleaved fibers, a 40-frame suspension, a dropped suspended fiber, `FiberScheduler` round robin. |
| `fiber_in_async_and_threads.ax` | AXS-EXEC-050..052 | A fiber resumed from a `LocalExecutor` task between polls, per-thread fibers on 4 OS threads, a main-thread fiber surviving other threads. |

Requirement traceability: `REQ-ASY-165` is covered by every test in the suite (see `// covers:` in each file); the
secondary requirements are listed in the `covers:` line of each bundle.
