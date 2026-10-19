---
id: T154
title: Backend parity - narrow-value sign/zero extension in x64 isel, -O1 LIR path, const-table .rdata layout (axiom0 + port where needed)
phase: P10-selfhost
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: opus
depends: [T146]
priority: 117
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/target/x64, bootstrap/axiom0/src/lir, bootstrap/axiom0/src/driver/build_native, compiler/target/x64, compiler/lir, compiler/opt, compiler/backend, compiler/driver/pipeline.ax, tests/run/parity/backend, tests/mc, tests/lir, tests/selfhost]
spec: [spec/SPEC-03-core-semantics.md, spec/decisions/ADR-0004-self-host-subset-additions.md, spec/decisions/ADR-0035-axiomc-parity-symbols.md, spec/decisions/ADR-0034-oracle-independence.md]
covers: [REQ-CORE-3181, REQ-BLD-030]
---
# T154 — Backend parity: narrow extension, -O1 path, const tables

## Goal
For the remaining backend-only divergences, decide from SPEC-03 / ADR-0004 which compiler is right,
fix the wrong one (both if both are wrong), and make the bytes identical.

Confirmed differences (architect probe 2026-10-20; MIR and LIR equal unless stated):
1. **Narrow-value extension**: `tests/run/array/array_basics.ax`, `qa_nested_arrays.ax`,
   `pattern/qa_destructure.ax` — `inspect --emit=mi` differs only in `shr rcx, 32` (axiom0) vs
   `sar rcx, 32` (axiomc) in the truncation/extension sequence (`emit_trunc` in
   `bootstrap/axiom0/src/target/x64/isel/isel.c` ~23-55, `isel_emit_trunc` and ~1506 in
   `compiler/target/x64/isel.ax`). One of them extends a value with the wrong signedness; a negative
   `i32` element or field shows which.
2. **-O1 path**: `tests/run/struct/simple.ax` — `-O1` MIR is equal, the -O1 object differs (axiom0
   keeps an extra `lea`/spill pair): LIR lowering or an LIR-level pass at -O1 in the port.
3. **Const tables (ADR-0004)**: `tests/run/comptime/{table_str,qa_table_struct_str}.ax`,
   `native_const/qa_table_str_empty_and_multitables.ax` — `.rdata` of equal size but different
   content (axiom0 emits zero-filled slots, axiomc writes the string bytes inline).

## Scope
- For each difference: an independent test (expected values derived by hand) that distinguishes the
  two behaviours, a statement in the report of which side was wrong and why (SPEC/ADR rule), and the
  fix — in axiom0 and the port when axiom0 is wrong (ADR-0034 §2), in the port only otherwise. For a
  difference where both encodings are correct, the port follows axiom0 (ADR-0035 §3).
- MC/LIR goldens touched are reviewed and explained, not blindly re-blessed.

## Acceptance
- [ ] `tests/run/parity/backend/` (`modes: interp native`, values by hand): `narrow_negative.ax`
      (arrays, struct fields and tuple destructuring of negative `i32`/`i16`/`i8` and large `u32`
      values, each printed), `const_table_str.ax` (const `[N]str` table and a table of structs with str
      fields: every element printed). Pass with axiom0 in both modes and at -O1, and are identical
      under the e2e oracle.
- [ ] `known_divergent.txt` shrinks by every entry that becomes identical — at least the 7 entries of
      the plan table (`array/{array_basics,qa_nested_arrays}.ax`, `comptime/{qa_table_struct_str,
      table_str}.ax`, `native_const/qa_table_str_empty_and_multitables.ax`,
      `pattern/qa_destructure.ax`, `struct/simple.ax`); no entry is added.
- [ ] Full suite passes in `build-snap-T154` with native legs; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T154-report.md` with exact `## Files changed`, the right/wrong
      verdict per difference, and the removed registry paths.

## Out of scope
- Register allocation or optimizer changes beyond parity (T063, T064 post self-host).

## Notes
- If an axiom0 change is needed the task is a lockstep fix (ADR-0034 §2); it may run in parallel with
  port-only tasks only when `paths` do not overlap (the scheduler checks).
- ADR-0035 §4: remove registry lines explicitly; adding is forbidden.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
