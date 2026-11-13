---
id: T422c
title: std/async — converge on the SPEC-34 API shape (TaskGroup<T>.spawn, Timeout<F>, spawn(fut), generic TaskHandle<T> Future); remove compiler workarounds
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T421a, T444, T445, T446, T447, T448, T449, T422a, T422b]
priority: 30
status: todo
attempts: 0
timeout_min: 900
paths: [std/async, tests/std/async]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/SPEC-34-executors-fibers.md, spec/SPEC-33-async.md]
covers: [REQ-CONC-040, REQ-ASY-041, REQ-ASY-109]
---
# T422c — std/async: SPEC-34 API shape

## Goal
`std/async` exposes the API SPEC-34 specifies — generic `TaskGroup<T>` with `spawn(exec, fut)`, `Timeout<F: Future>`,
`spawn(fut)` / `spawn_local(fut)` without an explicit poll function, `impl<T> Future for TaskHandle<T>` — now that the
compiler gaps that forced the T421/T422 deviations are fixed (ADR-0042 §2).

## Scope
- Replace the deviations listed in `_workspaces/reports/T421-report.md` "Design decisions" and
  `_workspaces/reports/T422-report.md` "Deviations" 1–3, 7–10: non-generic `TaskGroup`/`Timeout`, `adopt(handle)`,
  explicit `poll_fn` arguments, `TaskHandle<T>` Future only for `i64`, free generic helpers that stood in for
  methods; keep the old names as thin deprecated wrappers only if a test outside `tests/std/async` uses them.
- Remove compiler workarounds made obsolete by T444 (`*mut u8` + cast fields, `waker_data`/`waker_vt` pairs if a
  `Waker` field now works), T445 (`mut_view(*cx)`), T422a (locals for `<` comparisons).
- Update every `tests/std/async/**` test to the spec API; add tests for two different `T` on two groups, a
  `Timeout<F>` over a user future, and `spawn(fut)` with a capture that needs drop.
- If a remaining compiler gap blocks one item, keep that deviation, write its minimal repro in the report, and the
  architect files it.

## Acceptance
- [ ] The SPEC-34 examples (canonical syntax) compile and run in interp/native/native-O1 with exact `// stdout:`.
- [ ] All `tests/std/async/**` pass; WEAK-NATIVE 0; `bundles_current`/`check_*_bundles` tests of the group pass.
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline.
- [ ] Report `_workspaces/reports/T422c-report.md` with a table "deviation -> resolved / kept (repro)" and exact
  `## Files changed`.

## Out of scope
- Unwinding-based panic capture (T536), `compiler/`, `docs/`.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §2; T421/T422 API deviations)
