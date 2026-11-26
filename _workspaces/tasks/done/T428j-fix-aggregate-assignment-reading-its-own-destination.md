---
id: T428j
title: Fix — an aggregate assigned to a place it reads (`arr = [arr[2], arr[0], arr[1]]`) is built in the destination and reads overwritten values
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: []
priority: 20
status: done
attempts: 1
timeout_min: 240
paths: [tests/run/agg_self_assign]
locks: [compiler/mir/builder.ax]
spec: [spec/SPEC-03-core-semantics.md]
covers: [REQ-EXP-007, REQ-EXP-102, REQ-MIR-006]
started: 2026-11-26 10:41:15
finished: 2026-11-26 17:03:30
---
# T428j — Evaluate every operand of an aggregate before writing the destination

## Why
`_workspaces/reports/T428a-qa.md` defect 5 (synchronous code, HEAD 9135f012, interp and native identical):
```
let mut arr: [3]i64 = [1i64, 2i64, 3i64];
arr = [arr[2], arr[0], arr[1]];        // expected 3,1,2 ; got 3,3,3
let mut pair = Pair { a: 7i64, b: 8i64 };
pair = Pair { a: pair.b, b: pair.a };  // expected 8,7 ; got 8,8
```
The MIR builder constructs the aggregate field by field directly in the destination place, so later operands read
fields already overwritten. Axiom evaluates all operands left to right before the assignment takes effect
(REQ-EXP-007, REQ-EXP-102). Because the oracle and native run the same MIR, both are wrong; no test caught it.

## Scope
1. In `compiler/mir/builder.ax`: when an array/struct/tuple/enum-payload aggregate (including nested aggregates and
   array-repeat forms) is assigned to a place, evaluate the operands into temporaries (or build into a fresh temporary
   and move it) whenever any operand may read the destination place or a place overlapping it (conservative test:
   the operand mentions the destination's base local, or any deref when the destination is reached through a
   pointer). Keep in-place construction when no operand can alias (no regression of `tests/opt*` codegen goldens;
   if a golden changes, explain why in the report).
2. Check the same for compound forms that build an aggregate into a place: `let` re-binding is not affected, but
   field assignment of an aggregate (`s.inner = Inner { a: s.inner.b, b: s.inner.a }`) and `*p = S { .. (*p).x .. }`
   are. Async bodies use the same builder; one test inside an `async fn`.
3. Tests `tests/run/agg_self_assign/` (`modes: interp native`, exact `// stdout:`): array rotate, struct swap, tuple
   swap `t = (t.1, t.0)`, nested field case, pointer case, enum payload `e = E.V(match e { .. })` reading `e`, and
   one in an `async fn` across an `.await`; each fails on HEAD (shown in the report).

## Acceptance
- [ ] New tests pass in interp, native and native-O1, WEAK-NATIVE 0; they fail on HEAD.
- [ ] `tests/run/**`, `tests/mir/**`, `tests/opt*/**`, `tests/diff/**` pass.
- [ ] Normal gate including the selfhost groups of `compiler/mir`; stage-2 fixed point holds.
      Report `_workspaces/reports/T428j-report.md` with an exact `## Files changed`.

## Log
- 2026-11-26 created by architect (`_workspaces/reports/unblock-T428a.md`, triage of T428a-qa.md defect 5)
- 2026-11-26 10:41:15 started (attempt 1) T428j-impl
- 2026-11-26 17:03:30 accepted by QA -> done
