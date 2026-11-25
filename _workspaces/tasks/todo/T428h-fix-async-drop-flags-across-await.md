---
id: T428h
title: Fix — drop flags of `async fn` locals are not kept across `.await` (moved-out values dropped twice, uninitialised locals dropped)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T428a, T428b]
priority: 25
status: todo
attempts: 0
timeout_min: 300
paths: [tests/run/async/drop_flags_across_await]
locks: [compiler/mir/async_lower.ax, compiler/mir/drop.ax]
spec: [spec/SPEC-33-async.md, spec/SPEC-12-drop.md, spec/decisions/ADR-0050-async-address-observable-locals-in-place.md]
covers: [REQ-ASY-018, REQ-ASY-058]
---
# T428h — Drop flags are part of the async state

## Why
`_workspaces/reports/T428a-report.md` "Pre-existing defects" 1, confirmed by `T428a-qa.md` defect 1 (identical on HEAD
9135f012 and with T428a, interp, native, native-O1):
```
let g = Guard { .. }; let a = g.get();
if c { eat(g); }
Nap.await;          // end of scope: g dropped
```
prints `d1 d1` when `c` (double drop); the same unborrowed (`d2 d2`) and for a tuple field moved before the await
(`d3 d3 d4`). A deferred-init local (`let g: Guard; if c { g = ..; g.get() } .. .await`) with `c == false` is dropped
although never initialised (HEAD `d0`/`d1`; with T428a native reads the uninitialised in-place field: `d1441152`).
Cause (report): drop flags are poll-frame locals that are neither saved in the state nor kept in place; the resume
path re-arms them. SPEC-33 AXS-ASY-043 item 7 (last bullet, 2026-11-26) and AXS-ASY-044 require them to be state.

## Scope
1. In `compiler/mir/async_lower.ax` (and `compiler/mir/drop.ax` if the elaborated flags must be tagged) treat every
   drop flag whose local is live across a suspension as a live-across value: keep it in the state (in place or
   saved/restored with its local) so the resume path and the cancellation glue (AXS-ASY-044) see the value it had at
   suspension. Partial-move flags (per field) follow the same rule.
2. Tests `tests/run/async/drop_flags_across_await/` (`modes: interp native`, exact `// stdout:`): the four shapes above
   (whole move, unborrowed move, tuple-field move, deferred init with both branches), each also cancelled while
   suspended (dropped exactly once or not at all), and a loop that moves and re-initialises across awaits.
   Each case that fails on HEAD is shown failing in the report.

## Acceptance
- [ ] New tests pass in interp, native and native-O1, WEAK-NATIVE 0; they fail on HEAD.
- [ ] `tests/run/async/**`, `tests/mir/async/**`, `tests/std/async/**`, `tests/conformance/p11/**`, `tests/run/drop/**` pass.
- [ ] Normal gate including the selfhost groups of `compiler/mir`. Report `_workspaces/reports/T428h-report.md` with an
      exact `## Files changed`.

## Log
- 2026-11-26 created by architect (`_workspaces/reports/unblock-T428a.md`, triage of T428a-qa.md defect 1)
