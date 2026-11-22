---
id: T422e
title: Fix — an `AsyncMutexGuard` held across `.await` is rejected (AX_ASYNC_GUARD_ACROSS_AWAIT, keyed on the type name, wrong "drop flag" message); SPEC-34 AXS-EXEC-031 allows it
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T422c, T498f]
priority: 16
status: done
attempts: 1
timeout_min: 480
paths: [compiler/verify/verifier.ax, compiler/types/typeck.ax, compiler/own/unsafe.ax, std/sync/mutex.ax, std/sync/rwlock.ax, tests/run/async_guard_across_await, tests/ui/async_guard_across_await, tests/ui/async/lock_guard_await, tests/std/sync, tests/conformance/p11/e11_3_threads_sync, tests/std/async/structured, tests/conformance/p11/e11_4_async/async_ui_guard_across_await.ax, tests/conformance/p11/e11_1_concurrency/ui_lock_guard_escape.ax, tests/ui/concurrency/data_race/guard_escape_and_atomic_mut_view.ax, tests/ui/concurrency/data_race/qa_arc_and_boundary_races.ax]
locks: []
spec: [spec/SPEC-34-executors-fibers.md]
covers: [REQ-TST-072]
started: 2026-11-22 17:33:31
unblocks: 1
finished: 2026-11-22 20:32:16
---
# T422e — async guard across `.await`

## Goal
Reported by T422c-impl (2026-11-22). Inside an `async fn`, a value of any type named `AsyncMutexGuard` that is held across an
`.await` is rejected with `AX_ASYNC_GUARD_ACROSS_AWAIT: drop flag local is not initialized in bb0`. SPEC-34 AXS-EXEC-031 and
§6.1 explicitly allow holding an `AsyncMutexGuard` across `.await` (only sync guards such as `MutexGuard` must not cross a
suspension point). The check is keyed on the type name: the same program with the struct renamed (`Held<T>`) compiles and runs.
The message text (drop flag) is also wrong.

Standalone repro (no std/async needed):
```
struct AsyncMutexGuard<T> { pub v: T }
impl<T> Drop for AsyncMutexGuard<T> { ... }
Ready: Future<Output = AsyncMutexGuard<i64>>
Pend: Future<Output = ()>, Pending once
async fn hold() -> i64 { let mut h = Ready { n: 5i64 }.await; Pend { done: false }.await; h.v }
```
Related: the `.lock()` spelling also gets `AX_CONC_GUARD_ESCAPE` on the receiver, suggesting a name-keyed check of the same
class as FU-E/T449.

## Scope
- Find the emitter (grep: `compiler/verify/verifier.ax`; possibly the async state-machine lowering or a concurrency checker)
  and determine why a guard held across a suspension point trips a drop-flag initialisation check. Fix the real cause: drop
  flags for locals that live across a suspension must be stored in the coroutine frame and initialised on entry.
- Guard-across-await policy must be type-based per SPEC-34 (sync guard types rejected, async guards allowed) — not keyed on a
  user-visible type name. If that needs a marker (trait/attribute) on std types, decide and record it (ADR if a design choice).
- Diagnostic text must describe the real problem.
- The `.lock()` / AX_CONC_GUARD_ESCAPE receiver issue: fix if it is the same root cause; otherwise record a precise follow-up.
- If the fix lives outside `paths` (e.g. `compiler/mir/builder.ax`, an async lowering module, `compiler/diag/*`), report
  BLOCKED naming the files so the orchestrator widens paths.
- Tests (interp, native, native-O1, exact `stdout:`): the repro; a renamed non-Drop guard; a Drop guard whose destructor must
  run exactly once after resume; a sync `MutexGuard` across `.await` still rejected (ui test).
- Remove the `// xfail: T422e …` marker T422c added in `tests/std/async/structured/spec34_local_executor_example.ax`
  (regenerate via its gen script) and confirm it passes.

## Acceptance
- New tests pass in three modes; the SPEC-34 §6.1 example passes; sync guards across await still rejected; taskgate clean.

## Log
- 2026-11-22 15:29:03 started (attempt 1) T422e-impl
- 2026-11-22 15:55:24 block: guard policy lives in compiler/types/typeck.ax (held by T498f, name-keyed tc_is_guard_struct) + std/sync guards need @no_suspend_hold + compiler/own/unsafe.ax name-keyed lock(); verifier message fix done

## Resume after unblock (orchestrator, 2026-11-22)
Attempt 1 (report _workspaces/reports/T422e-report.md) found two causes and fixed the message part in
compiler/verify/verifier.ax; its tests are already in the main tree, uncommitted — do not redo them.
Remaining, per SPEC-34 (marker @no_suspend_hold; AsyncMutexGuard unmarked, std.sync.MutexGuard marked — no ADR needed):
- compiler/types/typeck.ax: drop the name test (tc_sv_is_guard_name) so only the attribute marks a guard struct.
- std/sync/mutex.ax, std/sync/rwlock.ax: add @no_suspend_hold to MutexGuardImpl, RwLockReadGuardImpl, RwLockWriteGuardImpl;
  regenerate the bundles that embed them via tests/std/sync/gen_tests.py and tests/conformance/p11/e11_3_threads_sync/gen_tests.py.
- tests/ui/async/lock_guard_await: add the attribute to the locally declared guard structs.
- compiler/own/unsafe.ax: the .lock()/read()/write() name-keyed guard-escape rule (AX_CONC_GUARD_ESCAPE on AsyncMutex.lock()) — make it type/attribute based.
- Remove xfail: T422e from tests/std/async/structured/spec34_local_executor_example.ax (regenerate) and confirm §6.1 passes.
Depends on T498f (holds typeck.ax); T499b also needs typeck.ax — the board serialises them.
- 2026-11-22 15:55:48 unblocked (cycle 1)
- 2026-11-22 17:50 orchestrator: widened paths with 4 legacy mock-guard UI tests (`e11_4_async/async_ui_guard_across_await.ax`, `e11_1_concurrency/ui_lock_guard_escape.ax`, `data_race/guard_escape_and_atomic_mut_view.ax`, `data_race/qa_arc_and_boundary_races.ax`) so guard checks stay purely attribute-based (`@no_suspend_hold`, zero name heuristics); disjoint from all active tasks.
- 2026-11-22 17:33:31 started (attempt 1) t422e-impl
- 2026-11-22 20:32:16 accepted by QA -> done
