---
id: T141
title: AX0-FIX-03 implicit Drop for structs with only scalar/pointer fields (axiom0 + port), remove std DropGlue workaround
phase: P10-selfhost
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T140]
priority: 0
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/mir/drop, bootstrap/axiom0/src/lir, bootstrap/axiom0/src/interp, bootstrap/axiom0/src/verify, compiler/mir, compiler/lir, compiler/interp, compiler/verify, compiler/types/typeck.ax, std/alloc, std/bytes, std/core/iter/adapters/vec_iter.ax, std/core/arena, std/env, std/io, std/process, std/text/string.ax, tests/run/drop, tests/run/mangle, tests/selfhost]
locks: [bootstrap/axiom0/src/types/typeck.c]
spec: [spec/SPEC-12-drop.md, spec/decisions/ADR-0032-unblock-t131-drop-destructors.md, spec/decisions/ADR-0034-oracle-independence.md, tasks/0485]
covers: [REQ-DRP-083, REQ-DRP-051, REQ-OBJ-004]
timeout_min: 300
---
# T141 — AX0-FIX-03: implicit Drop for structs with only scalar/pointer fields

## Goal
A type with a user `impl Drop` is dropped at every scope exit (SPEC-12 AXS-DROP-001..003) whatever
its fields are, in the interpreter and natively, in axiom0 **and** in the port under `compiler/`
(ADR-0034 §2). std no longer needs the `_glue: DropGlue` field workaround, and destructor symbols
cannot collide with user symbols.

Confirmed defect (audit OI-06): `struct Foo { x: i32 }`, `struct P { p: *mut u8 }` and
`struct G<T> { p: *mut T }` with `impl Drop` print nothing at scope end in both modes; explicit
`drop(f)` works. axiom0 has three separate `needs_drop` predicates
(`mir/build/builder.c` `type_needs_drop` ~172, `lir/lower.c` `lir_type_needs_drop` ~204,
`mir/drop/drop.c` `ax_type_needs_drop` ~12) that can disagree about user `impl Drop`; the port mirrors
them (`compiler/mir/builder.ax`, `compiler/lir/builder.ax`, `compiler/mir/drop.ax`,
`compiler/interp/interp.ax`). std works around it with a `_glue: DropGlue` field in 8 files
(`std/alloc/vec.ax:13`, `std/alloc/box.ax`, `std/bytes/byte_buf.ax:10`,
`std/core/iter/adapters/vec_iter.ax`, `std/env/env.ax`, `std/io/io.ax`, `std/process/process.ax`,
`std/text/string.ax`); `std/core/arena` (Arena) has no such field and never frees implicitly.

## Scope
- **One drop predicate:** a single "type needs drop" definition (user `impl Drop` ⇒ true; otherwise
  structural over fields/tuple/array/enum/closure captures/generic instances) used by the MIR builder,
  drop elaboration, the interpreter, the verifier's missing-drop check and LIR lowering; the other
  copies are deleted. Same in the port (one function in the ported module that owns it).
- **Mangling collision check (audit OI-14):** run/ui tests with a user `fn Foo_drop()` next to
  `impl Drop for Foo`, the same method name on two types, and generic instances `G<i32>`/`G<u32>`
  with `impl Drop`. If any of them mis-links, calls the wrong function or reports a duplicate symbol,
  apply ADR-0034 §6: destructor/drop-glue symbols use the reserved form `<Type>$drop` (`$` cannot
  occur in an Axiom identifier), in axiom0 and the port; ADR-0032's `T_drop` spelling is amended by
  ADR-0034.
- **Remove the workaround:** delete `_glue: DropGlue` (and the `DropGlue` helper if unused) from the
  8 std files; `Arena` gets the implicit free it lacked (its `impl Drop` now runs).
- Hand-written drop-order tests from SPEC-12 (expected `stdout:` written by hand, not captured):
  scalar-field, pointer-field, generic pointer-field, nested (droppable inside scalar-only outer),
  early `return`, `break` out of a loop, moved-out value not dropped, reassignment drops the old value.
- Selfhost drop bundles/goldens (`tests/selfhost/drop`, `gen_drop_tests.py`, `drop_oracle`) are
  regenerated from the fixed axiom0 and each change is explained.

## Acceptance
- [ ] `tests/run/drop/scalar_field_drop.ax`, `pointer_field_drop.ax`, `generic_pointer_drop.ax`,
      `nested_scalar_outer.ax`, `early_return_scalar.ax`, `loop_break_scalar.ax`,
      `moved_scalar_not_dropped.ax`, `reassign_scalar_drop.ax` (`modes: interp native`, hand-written
      `stdout:` drop order per SPEC-12) pass; they fail on the pre-fix compiler (report shows it).
- [ ] `tests/run/mangle/` collision tests pass in both modes (distinct behaviour, no
      `AX_LINK_DUPLICATE`); the report states whether ADR-0034 §6 renaming was needed.
- [ ] Exactly one needs-drop predicate remains in axiom0 (`grep` evidence in the report) and one in the
      port; a selfhost test built from the real `compiler/mir/drop.ax` (or a regenerated bundle with
      a freshness check) shows a scalar-field `impl Drop` type gets a drop.
- [ ] No `_glue: DropGlue` field remains under `std/`; `tests/std` passes in both modes; a test shows
      an `Arena` (or a type owning one) frees implicitly at scope end (host heap counter or printed
      destructor).
- [ ] Full suite passes in `build-snap-T141` with native legs (no new leaks reported by the verifier's
      missing-drop check); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T141-report.md` with exact `## Files changed` and the list of
      regenerated goldens/bundles with reasons.

## Out of scope
- Drop flags beyond what SPEC-12 already defines; `Copy`/`Drop` exclusivity rules (unchanged);
  general symbol mangling scheme changes beyond the destructor form (E20.5).

## Notes
- Ordered before T086 (ADR-0034 §5, overriding the audit's "before T087"): Stage-1 must measure the
  real memory behaviour of axiomc (ADR-0005 §7 budget) and must not be built on a std that carries a
  compiler workaround; any fix after T086 would force T086 to be re-run anyway.
- Runs after T140 (shared `mir/build`, `lir`, `tests/selfhost`); priority 0 runs alone.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale and is not evidence.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
- Parity registry (ADR-0035 §4, added 2026-10-20): the full suite runs `tests/selfhost/obj_link_driver/axiomc_e2e.test`,
  which fails on XPASS/IMPROVED. Remove (by explicit line deletion) every `known_divergent.txt` entry this task makes
  identical, update in place an entry that only improves, list the paths in the report; never add an entry (a newly
  divergent program is a regression of this task).

## Log
