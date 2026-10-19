---
id: T156
title: Dump and diagnostic parity (resolved PathSegment, type interning order, message texts), oracle compares dumps, divergence registry empty
phase: P10-selfhost
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: opus
depends: [T147, T148, T149, T150, T151, T152, T153, T154, T155]
priority: 118
status: todo
attempts: 0
paths: [compiler/resolve, compiler/resolve_hir, compiler/types, compiler/typeck, compiler/typeck_traits, compiler/diag, compiler/hir, compiler/mir, tests/run/parity/diag, tests/selfhost]
spec: [spec/decisions/ADR-0035-axiomc-parity-symbols.md, spec/decisions/ADR-0034-oracle-independence.md]
covers: [REQ-BOOT-085, REQ-TST-089, REQ-BLD-030]
---
# T156 — Dump and diagnostic parity; registry empty

## Goal
`axiomc inspect --emit=<stage>` prints exactly what axiom0 prints for every stage and corpus
program, and axiomc's diagnostics are byte-identical (code, severity, span, message text;
ADR-0035 §3). The e2e oracle enforces it, and `known_divergent.txt` is empty when T086 starts.

Confirmed differences (architect probe 2026-10-20):
1. `resolved` dump: `(PathSegment @Sym(2) "i32")` vs axiom0 `(PathSegment "i32")` for builtin type
   segments (14 registry entries have `resolved` as first stage).
2. Type interning order: `type#29` vs `type#26` in `mir`/`lir` dumps (`tests/run/array/*`,
   `trait2/*`, …) — the port interns slice/array/fn types in a different order.
3. Diagnostic texts: axiomc prints generic texts (`type error`) where axiom0 prints specific ones
   (`unreachable statement`, `cannot index into a value of this type`); registry entry
   `tests/run/native_enum/01-simple.ax` differs only in that warning's text.

## Scope
- Port dump printing, interning order and the diagnostic message table so that the outputs equal
  axiom0's.
- Extend `tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py`: a program is `equal` only if, in
  addition to today's checks, every `inspect --emit=<stage>` output of `INSPECT_STAGES` is identical
  (exit code, stdout, stderr).
- Residuals: re-run the oracle; any entry still listed whose cause belongs to T147–T155 is fixed
  here if it lies in this task's paths, otherwise reported `STATUS: BLOCKED` with the entry list
  (the architect files the fix; the gate never passes with a non-empty registry).

## Acceptance
- [ ] `tests/run/parity/diag/`: ui tests for three diagnostics whose message text differed
      (unreachable statement warning, cannot-index error, one more from the probe) with expected
      stderr written from axiom0's message table; and the oracle's dump comparison covers them.
- [ ] `known_divergent.txt` contains only its comment header (0 entries) and
      `axiomc_e2e.test` prints `AXIOMC-E2E programs=<n> equal=<n> known_divergent=0` with the extended
      dump comparison.
- [ ] Full suite passes in `build-snap-T156` with native legs; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T156-report.md` with exact `## Files changed`, the final
      `AXIOMC-E2E` line and the removed registry paths.

## Out of scope
- New diagnostics or message rewording (both compilers keep axiom0's texts until after T087).

## Notes
- ADR-0035 §3 Revisit: if porting message texts proves out of proportion, the owner may relax the
  rule to code + severity + span; until then texts must match.
- ADR-0035 §4: remove registry lines explicitly; adding is forbidden.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
