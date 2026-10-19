---
id: T152
title: Port closures and fn pointers parity - typing, capture lowering, closure symbols in the build path
phase: P10-selfhost
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: opus
depends: [T151]
priority: 117
status: todo
attempts: 0
paths: [compiler/types, compiler/typeck, compiler/mir, compiler/lir, compiler/own, compiler/driver/pipeline.ax, compiler/backend, tests/run/parity/closures, tests/selfhost]
spec: [spec/decisions/ADR-0035-axiomc-parity-symbols.md, spec/decisions/ADR-0034-oracle-independence.md, 0116]
covers: [REQ-OWN-017, REQ-BLD-030]
---
# T152 — Port closures and fn pointers parity

## Goal
Every closure and fn-pointer program of the corpus builds under axiomc into the same bytes as under
axiom0 and runs identically.

Confirmed defects (architect probe 2026-10-20):
1. Typing: `fp = |x: i32| x + 100` assigned to a fn-pointer variable, `call_fn(add_ten, 5)`,
   `apply_mut(accum, 4)`, `let f3: fn(i32) -> i32 = |n: i32| n - 4` are rejected with
   `AX_TYPE_MISMATCH` (`tests/run/closure/{fn_pointers,fn_traits,generic_fns,qa_fn_ptr_args}.ax`).
2. Build path: `--emit=obj` succeeds but the image fails to link — `AX_LINK_DUPLICATE_SYMBOL x`
   (`closure/capture_modes.ax`), `AX_LINK_UNDEFINED_SYMBOL __ax_fn_1073741825`
   (`closure/qa_move_capture.ax`, `native_p7/qa_closure_capture.ax`); the closure bodies are
   emitted under the wrong symbol (a capture's name) or not at all. Objects of `capture_modes`,
   `closure_types`, `qa_mixed_captures`, `syntax` also differ in `.text`.

## Scope
- Port divergences in closure typing (closure → fn pointer coercion, fn-pointer parameters, generic
  fns taking closures), capture lowering in MIR/LIR and closure symbol naming/emission in
  `compiler/driver/pipeline.ax` / `compiler/backend` so they equal axiom0 (`build.c` uses
  `inst->mangled_name` or `__ax_fn_<symbol>`). If axiom0's closure symbol scheme can collide with a
  user item, apply ADR-0034 §6 (`$` reserved form) in both compilers.

## Acceptance
- [ ] `tests/run/parity/closures/` (`modes: interp native`, values by hand): `captures.ax` (by-view,
      by-mut_view and move captures in three closures, each printing its result), `fn_ptr.ax` (closure
      and named fn passed as `fn(i32) -> i32`, reassigned fn-pointer variable, results printed), and a
      program with two closures in two functions that capture variables of the same name. Pass with
      axiom0 and are identical under the e2e oracle.
- [ ] `known_divergent.txt` shrinks by every entry that becomes identical — at least the 10 entries
      of the plan table (`tests/run/closure/*` 9, `native_p7/qa_closure_capture.ax`); no entry is
      added.
- [ ] Full suite passes in `build-snap-T152` with native legs; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T152-report.md` with exact `## Files changed` and the removed
      registry paths.

## Out of scope
- `dyn` closures / vtables (T058, post self-host).

## Notes
- After T151 (generic closures depend on generic instantiation).
- ADR-0035 §4: remove registry lines explicitly; adding is forbidden.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
