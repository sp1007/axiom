---
id: T422e
title: Fix — an `AsyncMutexGuard` held across `.await` is rejected (AX_ASYNC_GUARD_ACROSS_AWAIT, keyed on the type name, wrong "drop flag" message); SPEC-34 AXS-EXEC-031 allows it
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T422c]
priority: 16
status: todo
attempts: 0
timeout_min: 480
paths: [compiler/verify/verifier.ax, tests/run/async_guard_across_await, tests/ui/async_guard_across_await, tests/std/async/structured]
locks: []
spec: [spec/SPEC-34-executors-fibers.md]
covers: [REQ-TST-072]
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
