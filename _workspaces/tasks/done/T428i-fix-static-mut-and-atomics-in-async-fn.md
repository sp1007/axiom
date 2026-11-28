---
id: T428i
title: Fix — `static mut` acts as a private copy and atomic operations crash inside an `async fn` (async lowering)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T428a]
priority: 28
status: done
attempts: 1
timeout_min: 300
paths: [tests/run/async/statics_atomics_in_async]
locks: [compiler/mir/async_lower.ax]
spec: [spec/SPEC-33-async.md, spec/SPEC-31-atomics.md]
covers: [REQ-ASY-082, REQ-MIR-144]
started: 2026-11-28 22:01:25
finished: 2026-11-29 01:40:29
---
# T428i — Statics and atomics keep their meaning across async lowering

## Why
`_workspaces/reports/T428a-report.md` "Pre-existing defects" 2-3, confirmed by `T428a-qa.md` defects 2-3 (identical on
HEAD 9135f012, all modes):
- A `static mut` used in an `async fn` behaves like a poll-frame copy: a store made by another function during a
  suspension is not seen (expected `1211 1211`, got `1010 201`). Likely cause: the `poll` copy of every source local
  gets kind `TEMP`, so a `STATIC` place becomes an ordinary local that is saved/restored.
- An `AtomicI64` local used across `.await`: oracle `AX_UNSAFE_INTERP_UB null pointer dereference`, native exit 139.
  Likely cause: `remap_stmt` does not rename the locals of `MIR_STMT_ATOMIC` and the liveness scan ignores it.
REQ-ASY-082 (AASYNC-38): async lowering must preserve synchronization semantics across suspension points.

## Scope
1. In `compiler/mir/async_lower.ax`: static places are never copied into the poll frame or the state (every access
   stays an access to the static); every MIR statement kind with local operands (atomics, volatile, intrinsic calls —
   audit the full statement enum, list it in the report) is renamed by `remap_stmt` and counted by the liveness scan.
2. Tests `tests/run/async/statics_atomics_in_async/` (`modes: interp native`, exact `// stdout:`): `static mut` written
   by another task during a suspension and read after it; an atomic local and an atomic reached through a pointer used
   before and after several awaits (load/store/fetch_add/compare_exchange); the same inside a spawned task under
   `LocalExecutor`. Each case that fails on HEAD is shown failing in the report.

## Acceptance
- [ ] New tests pass in interp, native and native-O1, WEAK-NATIVE 0; they fail on HEAD.
- [ ] `tests/run/async/**`, `tests/mir/async/**`, `tests/std/async/**`, `tests/conformance/p11/**`, `tests/run/atomics/**` pass.
- [ ] Normal gate including the selfhost groups of `compiler/mir`. Report `_workspaces/reports/T428i-report.md` with an
      exact `## Files changed`.

## Log
- 2026-11-26 created by architect (`_workspaces/reports/unblock-T428a.md`, triage of T428a-qa.md defects 2-3)
- 2026-11-28 22:01:25 started (attempt 1) axiom-semantics
- 2026-11-29 01:40:29 accepted by QA -> done
