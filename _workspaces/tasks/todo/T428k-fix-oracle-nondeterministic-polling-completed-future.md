---
id: T428k
title: Fix — oracle panics "polling a completed Future state machine" in some runs only (nondeterministic interpreter)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T428a]
priority: 30
status: todo
attempts: 0
timeout_min: 300
paths: [tests/run/async/oracle_determinism]
locks: [compiler/interp, compiler/mir/async_lower.ax]
spec: [spec/SPEC-33-async.md, spec/SPEC-34-executors-fibers.md]
covers: [REQ-ASY-060, REQ-ORC-006]
---
# T428k — The oracle must be deterministic

## Why
`_workspaces/reports/T428a-qa.md` defect 6 (HEAD 9135f012 and with T428a): an `async fn c_ret_tuple() -> (Guard, i64)`
followed by an async fn that passes a `Guard` to a nested async fn: `run --interp` prints
`panic: polling a completed Future state machine` in 2 of 6 runs of the minimal pair (always on the larger program);
native is always correct. The same input giving different oracle results means the interpreter reads something that
is not program state (uninitialised memory, a host address/hash order, or a stale value), which defeats its role as
the semantic oracle (REQ-ORC-006, REQ-ASY-060). The QA programs are in the T428a QA scratchpad (`adv/def*.ax`);
rebuild the repro from the description if they are gone.

## Scope
1. Reproduce (loop the program ≥ 50 times), find the nondeterministic read in `compiler/interp` (or in the MIR it
   runs: if `async_lower` emits a read of an uninitialised state field that native happens to tolerate, fix it there
   and say so), and fix the cause — no retry, no ignoring the state tag.
2. Add a determinism check to the oracle if cheap (e.g. poison freshly allocated interpreter memory with a fixed
   pattern so such reads fail the same way every run); document it in the report.
3. Tests `tests/run/async/oracle_determinism/` (`modes: interp native`, exact `// stdout:`): the minimal pair and the
   larger program; a `.test` that runs the interp leg 20 times and requires identical output.

## Acceptance
- [ ] 50 consecutive interp runs of each repro give the same, correct output; native unchanged; WEAK-NATIVE 0.
- [ ] `tests/run/async/**`, `tests/std/async/**`, `tests/conformance/p11/**`, `tests/interp/**` (if present) pass.
- [ ] Normal gate including the selfhost groups of `compiler/interp`. Report `_workspaces/reports/T428k-report.md` with
      an exact `## Files changed`.

## Log
- 2026-11-26 created by architect (`_workspaces/reports/unblock-T428a.md`, triage of T428a-qa.md defect 6)
