---
id: T165
title: Investigate — axiomc1 (built by axiom0) segfaults on `run --interp` of simple programs; locate the axiom0 miscompile or prove it harmless
phase: P10-selfhost
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T164, T166]
priority: 60
status: doing
attempts: 1
timeout_min: 300
paths: [_workspaces/investigations/T165]
spec: [spec/decisions/ADR-0043-cyclic-type-graphs-and-symbol-id-space.md, spec/SPEC-20-selfhost.md]
covers: [REQ-CORE-146]
started: 2026-11-19 07:40:38
agent: T165-impl
---
# T165 — Investigate: axiomc1 `run --interp` segfault

## Goal
Know why `axiomc1` (stage 1, compiled by the frozen axiom0) crashes on `run --interp` of simple programs while
`axiomc2` (compiled by axiomc1) works (T444 report, "other findings"). An axiom0 miscompile of the interpreter path
could also affect code axiomc1 runs while building axiomc2; the stage-2/3 fixed point only proves axiomc2 is stable.

## Scope
- Reproduce at HEAD with a rebuilt axiom0 (`tools/build_axiomc.py --force`); minimise the program and the crashing
  function (WinDbg/gdb backtrace or `--trace` output, address → symbol via the axiomc1 map/COFF symbols).
- Classify: (a) axiom0 miscompile (name the C function and the construct), (b) a bug in the Axiom interpreter that
  axiomc2 hides by different layout, (c) stack exhaustion with axiomc1's stack reserve, or (d) other.
- Decide the follow-up and write it in the report: (a) propose an AX0-FIX task (scope, files, repro); (b) a compiler
  fix task; (c) a bootstrap flag change; the architect creates it. No code change in this task.

## Acceptance
- [ ] `_workspaces/investigations/T165/` contains the minimal repro and the evidence (logs, backtrace).
- [ ] Report `_workspaces/reports/T165-report.md`: classification with evidence, impact on stage 2 (does axiomc1 use
      the faulty construct while compiling the bundle?), proposed follow-up task.

## Out of scope
- Editing `bootstrap/axiom0` (frozen; only an AX0-FIX task may), `compiler/`, `std/`, `docs/`.

## Notes
- Depends on T164 so the investigation runs on the axiom0 that will stay frozen (symbol-id fix in place).

## Log
- 2026-11-17 created by axiom-architect (T444 report "other findings"; ADR-0043 §4)
- 2026-11-19 architect (unblock T491): now depends on T166 AX0-FIX-11 — the axiomc1 interpreter crash is very likely
  the same axiom0 branch-fixup overflow (`exec_assign_binop`, 1076 fixups; T491 report). First step: re-run the
  repro with the T166 axiom0; if the crash is gone, record that as classification (a) with T166 as the fix and close.
- 2026-11-19 07:40:38 started (attempt 1) T165-impl
