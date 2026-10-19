---
id: T149
title: Port MIR builder parity - slice bounds and as-char checks, for-range step, field projection through deref, index temporaries
phase: P10-selfhost
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: opus
depends: [T146]
priority: 116
status: todo
attempts: 0
paths: [compiler/mir, compiler/hir, tests/run/parity/mir_builder, tests/selfhost]
spec: [spec/SPEC-03-core-semantics.md, spec/decisions/ADR-0035-axiomc-parity-symbols.md, spec/decisions/ADR-0034-oracle-independence.md, 0161]
covers: [REQ-EXP-035, REQ-MIR-058, REQ-BLD-030]
---
# T149 — Port MIR builder parity

## Goal
`compiler/mir/builder.ax` builds the same MIR as `bootstrap/axiom0/src/mir/build` for every corpus
program (modulo nothing), so the safety checks that axiom0 emits exist in axiomc's output and loops
and field accesses compute the right values.

Confirmed defects (architect probe 2026-10-20, `axiomc inspect --emit=mir` vs axiom0, type ids
normalised):
1. **Slice index bounds check missing**: `tests/run/slice/coerce.ax` — axiom0 has
   `assert(... "index out of bounds")` for `v2[2]` on a `view<[i32]>`, axiomc has none (also
   `slice/sum.ax`, `qa_slice_mutate*.ax`, `tests/programs/{sorting,tokenizer,expr_interp}.ax`: 52 vs 27,
   59 vs 39, 51 vs 49 asserts). A hidden miscompile: out-of-range slice access is UB in axiomc.
2. **`as char` validity check missing**: `tests/run/numeric/panic_char_{d800,110000}.ax`,
   `qa_panic_char_dfff.ax` exit 0 under axiomc instead of 101 `panic: invalid char value`;
   `cast_char.ax`, `qa_cast_char_edges.ax` lose the check silently.
3. **`for` over a range steps by 0**: `tests/run/for/test_range_standalone.ax` MIR has
   `_13 = copy _13 + const 0` where axiom0 has `+ const 1`; the axiomc image panics
   `arithmetic overflow`.
4. **Field projection through deref**: `tests/run/method/inherent_methods.ax` — `(*self).1` is
   built as `(*self).0` (`copy ((*_1)).0 + copy ((*_1)).0`).
5. **Index temporaries**: `tests/run/array/array_bounds.ax` and 8 others — axiomc copies the index
   into an extra temporary before the bounds compare (`_6 = copy _4; _7 = const 3; ...`), axiom0
   compares directly; bytes differ.

## Scope
- Fix the five defects in the port so its MIR equals axiom0's, statement by statement (temporaries
  numbered alike). axiom0 is the reference here (its checks follow SPEC-03 AXS-SEM rules); if the probe
  of a defect shows axiom0 itself violates SPEC-03, fix both (ADR-0034 §2) and say so in the report.
- Type-id numbering (`type#26` vs `type#29`) is T156's, not this task's; compare with ids normalised.

## Acceptance
- [ ] `tests/run/parity/mir_builder/` (`modes: interp native`, expected values derived by hand):
      `slice_oob.ax` (index past the end of a `view<[i32]>` → exit 101 + SPEC-03 panic line),
      `char_cast_invalid.ax` (`0xD800u32 as char` → exit 101), `for_range_sum.ax` (prints the sum of
      `10..20` = 145 and of an inclusive range), `self_field_sum.ax` (method summing `(*self).0` and
      `(*self).1` of a two-field struct with distinct values prints their sum). All pass with axiom0
      and are identical under the e2e oracle.
- [ ] For every program of the plan table assigned to T149, `axiomc inspect --emit=mir` equals
      axiom0's after replacing `type#<n>` by a placeholder (a check script or test in the report).
- [ ] `known_divergent.txt` shrinks by every entry that becomes identical — at least the 16
      sole-cause entries (`tests/run/array/{array_bounds,array_bounds_neg,qa_array_bounds_write,
      qa_nested_array_bounds}.ax`, `comptime/qa_table_u8_loop.ax`, `for/test_for_range.ax`,
      `for/test_range_standalone.ax`, `numeric/{cast_char,panic_char_110000,panic_char_d800,
      qa_cast_char_edges,qa_panic_char_dfff}.ax`, `slice/{coerce,qa_slice_mutate,qa_slice_mutate_2,
      sum}.ax`), unless a residual cause is shown (then the entry's line is updated and the cause
      named in the report's Follow-ups); no entry is added.
- [ ] Full suite passes in `build-snap-T149` with native legs; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T149-report.md` with exact `## Files changed` and the removed
      registry paths.

## Out of scope
- Type interning order and dump formatting (T156); typeck gaps (T150–T153).

## Notes
- ADR-0035 §3: `same-behaviour` entries hid defects 1, 2 and 4 — do not treat a passing run as
  parity.
- axiomc for probes: `python tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py <axiom0> <tmp> <root>`.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
