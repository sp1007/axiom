---
id: T166
title: AX0-FIX-11 branch-fixup capacity â€” axiom0 native emitter silently miscompiles functions with more than 1024 jumps or blocks
phase: P10-selfhost
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: opus
depends: []
priority: 0
status: todo
attempts: 0
timeout_min: 600
paths: [bootstrap/axiom0/src/driver/build_native, tests/run/parity/backend/many_branch_fixups.ax, tests/build_native, _workspaces/baseline-failures.txt]
locks: []
spec: [spec/SPEC-00-bootstrap.md, spec/SPEC-20-selfhost.md]
covers: [REQ-BOOT-003, REQ-BLD-028]
---
# T166 â€” AX0-FIX-11: branch-fixup capacity in the axiom0 native emitter

## Goal
axiom0 emits correct code for a function of any size. Today
`bootstrap/axiom0/src/driver/build_native/build.c` (~515-516) keeps per-function fixed arrays
`uint32_t bb_offsets[1024]` and `fixups[1024]` with no bounds check. A function with more than 1024 branch fixups
(JMP/JCC/ASSERT) or more than 1024 machine blocks writes past them: either axiom0's own stack is smashed (crash in
`ax_stage_build_native`) or, worse, overflowing `(fixup, target)` pairs overwrite `bb_offsets[]` and jumps are patched
to section offsets equal to block indices. That is a **silent miscompile in the bootstrap trust root**, hence
priority 0. axiomc's `exec_assign_binop` (`compiler/interp/interp.ax:2597`, 1076 fixups) is hit: 65 of its jumps
leave the function, so stage-1 `axiomc1` crashes (0xC0000005) in the oracle's const evaluation of any `const` with a
unary/binary initializer. Diagnosis and evidence (gdb, objdump): `_workspaces/reports/T491-report.md`. axiomc's own
backend has no such limit, so `axiomc2` is unaffected.

This is a frozen-axiom0 fix (ROADMAP R3, axiom-compiler skill "After self-host: axiom0 freeze"): the change is
limited to the defect; no new feature, no refactor of the emitter.

## Scope
- `build.c`: allocate `bb_offsets` with `mi_body->bb_count` entries and `fixups` as a growable array (or count
  JMP/JCC/ASSERT in a first pass and allocate exactly), free both after patching on every path (including error
  paths). Check `target < bb_count` when patching; an out-of-range target is an internal error (ICE diagnostic /
  `abort` with a message), never a silent patch.
- Audit every other fixed-capacity array and fixed-size buffer in `bootstrap/axiom0/src/driver/build_native/`
  (`name_buf[256]`, `formatted_msg[256]`, `obj_path[1024]`, any other) and list each one in the report with its
  verdict: bounded by construction (say why), truncation is harmless (say why), or fixed in this task. None may be
  left unchecked where an overflow or a silent truncation changes the emitted code or symbol names.
- Regression tests:
  - `tests/run/parity/backend/many_branch_fixups.ax` (`// test: run`): the T491 report repro scaled to about 1500
    `if`s (grouped 100 per nested `if x >= g { ... }` so each group stays readable), checking the computed sum â€”
    more than 1024 fixups and more than 1024 blocks in one function. Must fail (crash or wrong exit) with the
    unfixed axiom0; say in the report that you saw it fail first.
  - `tests/build_native/`: a stress test with more than 4096 jumps in one function (generated: a small checked-in
    generator plus the generated `.ax`, or a C driver `cdriver_*.c` in the existing `tests/**/cdriver_*.c` style that
    drives the emitter directly). Run in native and native-O1.
- Rebuild axiom0, rebuild stages 1-3 (`tools/bootstrap.py`), and remove the line
  `selfhost/obj_link_driver/axiomc_e2e.test ... T491` from `_workspaces/baseline-failures.txt` once it passes.
- Do not edit `compiler/` (axiomc has no such limit; `exec_assign_binop` stays as it is â€” splitting it would only
  hide the defect) and do not touch the two parity programs `const_table_str.ax` /
  `qa_narrow_const_repeat_and_print_int_edges.ax`.

## Acceptance
- [ ] `tests/run/parity/backend/many_branch_fixups.ax` passes in interp, native and native-O1 under axiom0 and
      under axiomc2 (same observable output and exit code; not exit-0-only â€” the program checks its sum).
- [ ] The >4096-jump stress test under `tests/build_native/` passes (native and native-O1 under axiom0).
- [ ] The report lists every fixed-capacity array/buffer in `bootstrap/axiom0/src/driver/build_native/` with its
      verdict; none is left unchecked where it can change emitted output.
- [ ] The stage 1-3 fixed point holds from the rebuilt axiom0 (`selfhost/fixedpoint` procedure; stage-2 and stage-3
      outputs byte-identical).
- [ ] With the rebuilt `axiomc1`: `selfhost/obj_link_driver/axiomc_e2e.test` passes;
      `axiomc1 inspect --emit=thir` and `axiomc1 build` succeed on `tests/run/comptime/scalar_const.ax`,
      `tests/run/parity/backend/const_table_str.ax` and
      `tests/run/parity/backend/qa_narrow_const_repeat_and_print_int_edges.ax`, with output identical to axiomc2.
- [ ] `selfhost/obj_link_driver/axiomc_e2e.test` removed from `_workspaces/baseline-failures.txt` in this commit.
- [ ] Byte-identical axiom0 output for every program that was below the old limits (spot-check: the run corpus
      objects/exes before and after on a sample of at least 30 programs, plus the axiomc bundle stage-1 object outside
      the affected functions) â€” the fix changes only functions that overflowed.
- [ ] Normal gate (`taskgate`); report `_workspaces/reports/T166-report.md` with an exact `## Files changed`.

## Log
- 2026-11-19 created by architect (unblock T491: root cause in frozen axiom0; supersedes T491)
