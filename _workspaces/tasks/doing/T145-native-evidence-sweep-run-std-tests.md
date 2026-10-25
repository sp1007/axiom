---
id: T145
title: Native-evidence sweep - smoke and assert-only run tests pin observable results; stale modes interp removed
phase: P10-selfhost
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T139, T146]
priority: 115
status: doing
attempts: 1
paths: [tests/run, tests/std]
spec: [spec/decisions/ADR-0034-oracle-independence.md, spec/SPEC-03-core-semantics.md, tasks/0361, tasks/0480]
covers: [REQ-TST-002, REQ-TST-012]
timeout_min: 240
started: 2026-10-25 17:29:20
agent: T145-impl
---
# T145 — Native-evidence sweep of run and std tests

## Goal
Every run test under the directories that carry the T086 independent subset proves something in its
native leg: it pins a value that a vacuous backend would not produce, and no test is restricted to
the interpreter without the accepted reason (ADR-0034 §3; audit OI-09).

Audit OI-09: 37 run tests have a unit `main` and no output (e.g. `tests/run/vars/compound.ax`,
`tests/run/comptime/table_u8_256.ax`, whose checks `return;` with exit 0); 2 are assert-only
(`tests/run/str/qa_hello_empty.ax`); 116 pass on exit 0; 9 `modes: interp` lack an accepted reason
(`run/basic/t117_panic.ax`, `run/basic/t117_qa_neg_i8_min.ax`, `run/fn/eval_order_panic1.ax`,
`run/fn/eval_order_panic2.ax`, `std/core/qa_hash_vectors.ax` (T134 removes it),
`std/alloc/qa_sort_interp.ax`, `std/arena/qa_arena_scale_interp.ax`, `run/basic/008-step-limit.ax`,
`run/basic/009-call-depth.ax`); the four panic tests already pass natively.

## Scope
- Convert every unit-`main` smoke test and assert-only test under `tests/run` and `tests/std` to pin
  an observable result computed by the program (non-zero exit derived from the checked values, or
  `stdout:`), with the expected value written by hand from the spec (never captured from compiler
  output). Early-return checks return distinct non-zero codes per check.
- `modes: interp`: removed where the native leg passes; kept only with the accepted reason
  "oracle-only check" in a comment (interpreter step/call-depth limit tests 008/009 qualify; a test
  that fails natively for a missing feature gets a follow-up instead). `qa_sort_interp.ax` /
  `qa_arena_scale_interp.ax`: native leg enabled or the reason recorded per axiom-testing.
- Using T139's `WEAK-NATIVE` report: zero weak entries under `tests/run/numeric`, `tests/run/drop`,
  `tests/run/ptr`, `tests/run/native_*` and `tests/std`; other directories reduced where cheap, the
  remaining count stated.
- A test that, once it checks something, fails natively or in interp is a real bug: listed in
  `## Follow-ups` (test, observations, diagnosis) with `xfail:` only if an ADR'd spec gap — the
  architect files the fix task, which T086 depends on.

## Acceptance
- [ ] `python tools/axtest.py --compiler build/axiom0.exe --verbose run/ std/` in `build-snap-T145`
      reports `WEAK-NATIVE 0` for the five directory groups above; the report lists the before/after
      counts and the full remaining weak list.
- [ ] `grep -rln "modes: interp$" tests/run tests/std` lists only files with an "oracle-only check"
      reason comment (report lists them).
- [ ] No unit-`main` test without an output or a non-zero pinned exit remains under `tests/run` and
      `tests/std` (script evidence in the report).
- [ ] Full suite passes in `build-snap-T145` (or each failure is a listed follow-up with a fix task
      filed by the architect).
- [ ] Report `_workspaces/reports/T145-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or std code changes (follow-ups); tests outside `tests/run` and `tests/std`.

## Notes
- After T139 (runner reports `WEAK-NATIVE`) and T146 (last task editing `tests/run` before it; T140 owns
  `tests/run/numeric`, T141 `tests/run/drop`). T086 depends on this task.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-25 17:29:20 started (attempt 1) T145-impl
