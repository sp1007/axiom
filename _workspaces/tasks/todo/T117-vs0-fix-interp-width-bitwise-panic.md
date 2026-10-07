---
id: T117
title: VS0 fix: interpreter width-exact arithmetic, bitwise/shift/unary, panic stderr, verified MIR
phase: P3-semantic-core
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T116]
priority: 12
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/interp, tests/run/basic, bootstrap/axiom0/src/driver/cmd_run.c, tests/conformance/vs0]
locks: [bootstrap/axiom0/src/driver/pipeline.c, bootstrap/axiom0/src/diag/codes/DRIVER.def, bootstrap/axiom0/src/mir/parse.c, bootstrap/axiom0/src/mir/build/builder.c]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-00-bootstrap.md, spec/decisions/ADR-0012-core-execution-semantics-and-milestones.md, spec/decisions/ADR-0016-vs0-gate-fix-tasks.md]
covers: [REQ-EXP-021]
started: 2026-10-07 21:12:10
unblocks: 2
---
# T117 — VS0 fix: interpreter width-exact arithmetic, bitwise/shift/unary, panic stderr, verified MIR

## Goal
The MIR interpreter is a faithful semantic oracle for every integer type of the bootstrap subset,
so the VS0 gate (T022) passes in interp mode. Fix task created by the T022 unblock (ADR-0016);
bugs I1–I5 of `_workspaces/reports/T022-report.md`.

## Scope
- I1 `interp.c` ~164–195: values carry their type width and signedness (i8…i64, u8…u64, bool);
  arithmetic, comparison, division and remainder are exact per SPEC-03 for every width, computed
  without host-C undefined or implementation-defined behaviour (X-HOST-SEM: no signed overflow, no
  over-wide shifts, no `%` on negative operands relying on the host).
- I2: `& | ^ << >>` implemented (arithmetic `>>` for signed, logical for unsigned); shift amount
  range checked (AXS-SEM shift rule); no default branch that silently returns 0 — an unknown op is
  an ICE.
- I3: UNARY_OP rvalues (`-` checked, `!`, `~`) implemented; `arith_sub_overflow` must not crash.
- I4 ~75–83: a panic writes exactly `panic: <msg>\n` to stderr and exits with the SPEC-03 panic
  exit code (AXS-SEM-071) — not an `AX_DRIVER_INTERP_PANIC` diagnostic.
- I5: the interpreter executes the MIR bodies built once and verified by the pipeline (no
  per-call rebuild from THIR); `pipeline.c` passes the verified bodies to the interpreter.
- Run tests in `tests/run/basic` for each width class, bitwise ops, shifts, unary ops and the panic
  stderr format (with `// native-after:` marks per ADR-0005 §1).

## Acceptance
- [ ] New `tests/run/basic` tests pass in interp mode.
- [ ] In a snapshot with T022's suite present (and T114/T115 done), every vs0 run test passes in
      interp mode, in particular arith_*, div_*, cmp_unsigned_order, lit_u64_max, bits_*, shift_*,
      sem_t06–t09, rem_*, fp10_overflow_panics, call_panic_in_callee, short_circuit_*_skips_panic.
- [ ] Throughput stays ≥ 10 million MIR steps/s in Release on the T021 loop benchmark (recorded).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T117-report.md` with exact `## Files changed`.

## Out of scope
- MIR builder (T116), parser (T114), typeck (T115).
- Casts/intrinsics (MS-P5), floats.

## Notes
- T116 adds `AX_MIR_TERM_ASSERT` dispatch to the interpreter; keep it and make the in-interpreter
  checks agree with the MIR asserts (the oracle double-checks, it must not disagree).

## Log
- 2026-10-07 20:54:37 started (attempt 1) T117-impl
- 2026-10-07 21:10:45 block: XPASS on tests/conformance/vs0 but not in paths to remove xfail
- 2026-10-07 21:11:20 unblocked (cycle 1) 
- 2026-10-07 21:12:10 started (attempt 1) T117-impl
- 2026-10-07 21:39:49 block: boolean literal bug in builder/parse; need path locks for builder.c/parse.c to fix it
- 2026-10-07 21:41:19 unblocked (cycle 2) 
