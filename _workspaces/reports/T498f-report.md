# T498f report — index assignment into immutable bindings; operand spans

## Summary
1. **typeck (`compiler/types/typeck.ax`)**: the place-mutability walk of `check_stmt_assign` was moved into
   `tc_check_place_mutable(cx, place, view_code, recheck)` and extended:
   - `HIR_EXPR_INDEX` now continues to the base when the indexed value is a local array (`TY_ARRAY`),
     exactly like fields/tuple fields, so `a[0] = v`, `hs[0].n = v`, `m[i][j] = v` and every `op=` on an
     immutable `let` give `AX_TYPE_ASSIGN_IMMUTABLE` at the assigned place.
   - A range sub-slice used as a place (`a[0..2][1] = v`) is a projection: the walk continues to its base.
   - Index whose base is `view`/`mut_view` (slice views today; `view<[N]T>` once T571 lands): every view
     level is examined (AXS-SEM-047); any `view` level → error, all `mut_view` → OK, the binding is not
     checked (`let sub = v[1..3]; sub[0] = x` stays valid).
   - Raw pointers, `str` and user `Index` impls keep their existing rules (SEM-T24 unchanged).
   - Deferred binding: a projection write (`a[0] = 1`, also `s.f = 1`) into a non-`mut` binding is rejected even
     while it is uninitialised (a deferred `let` is initialised only by a whole assignment). Whole-binding
     deferred init (`let x: i32; x = 1`) is unchanged.
   - `mut_view(a[i])`, `mut_view(hs[i].n)`, `mut_view(s.f)` (projection operands of an explicit `mut_view`)
     were **accepted and executed** before this task (the MIR verifier only catches a whole binding
     `mut_view(x)`, as `AX_VERIFY_TYPE_MISMATCH`). They now report `AX_TYPE_ASSIGN_IMMUTABLE` for an
     immutable binding and `AX_CAP_CONFLICT_MUT` through a read-only `view` level (SPEC-03 AXS-SEM-047
     wording). In this mode raw-pointer derefs are not checked (unchanged behaviour): the compiler itself
     takes `mut_view((*thir).interner.arena)` with `thir: *const Thir` (compiler/verify, async_lower, interp);
     rejecting that would be a separate decision.
2. **builder (`compiler/mir/builder.ax`)**: `mb_build_expr_as_operand` (now a wrapper over
   `mb_build_expr_as_operand_raw`) and `mb_build_operand` stamp each COPY/MOVE operand with its own HIR
   expression span (`mb_operand_set_span`; an explicitly set location is kept, a stale one cleared). The own
   checker already prefers `op.location`, so a use of a moved/uninitialised place in a binary/compare
   operand or call argument is reported at that operand. Constants are untouched; MIR text dump unchanged
   (the dump does not print operand locations).

## Repros
- Architect repro 1 (`hs[0].n = 5u32`, `a[0] = 9u32` on immutable `let`): two `AX_TYPE_ASSIGN_IMMUTABLE`, at 5:5 and 7:5.
- Repro 2 (`let u = 1u32 + hs[i].n` after move): `AX_MOVE_USE_AFTER_MOVE` at 8:20 (the operand), was 8:13.
- SEM-T21 (writes through `mut_view<[3]i32>`): not affected by the walk (all `mut_view` levels pass); it still
  fails with `AX_TYPE_CANNOT_INDEX` because index auto-deref through `view<[N]T>` is T571 (todo).
- SEM-T23 (`v[0] = 9` on `view<[2]i32>`): now reports `AX_TYPE_ASSIGN_IMMUTABLE` (the spec'd code) in addition to
  the `AX_TYPE_CANNOT_INDEX` it reported before; the latter disappears with T571. Because of that extra
  T571-dependent diagnostic, the `view<[N]T>` / `mut_view<view<[N]T>>` ui cases were written with slice views
  (`view<[u32]>`, `through_view_slice.ax`, `mut_view_of_elem.ax`) instead; T571's ui tests should add the
  array-view variants.

## Sweep for code relying on the hole
Heuristic scan (index/field-of-index write whose root is a `let` without `mut` in the same fn) over
`compiler/`, `std/`, `tests/`: no hits in `compiler/` or `std/`; the test hits (`tests/run/slice/*`,
`tests/run/opt_bce/*`, `tests/conformance/p15/e15_3_loops_bce/*`, `tests/run/slice_inclusive/*`,
`tests/ui/slice/*`) all write through bindings of type `mut_view<[T]>` and stay valid. The stage-2 self-compile
found one hit of the stricter first draft (`mut_view` through `*const Thir`) which led to the raw-pointer
exception above. No file outside `paths:` needed a change.

## T498e follow-up (operand spans for indexed writes)
Not made exact by this change: in `tests/ui/own_index_moved` the error of an indexed *write* after a move is
reported at the store statement's location, which the builder gives the RHS span (e.g. `hs[0] = mk()` → col 13)
or the whole statement (col 5). An assignment destination is a place, not an operand, so operand spans do not
reach it. Suggested follow-up: give the final store/DROP of `HIR_STMT_ASSIGN` the span of `stmt.left` (or let
`own_do_assign` take a place span) and then tighten those tests to `file:line:col`. Indexed *reads* after a move
(`1u32 + hs[i].n`, call args, comparisons) are now exact.

## Tests
New ui tests (exact code + `stderr-contains file:line:col`):
- `tests/ui/assign_immutable_index/`: `elem_write`, `field_of_elem`, `nested_2d`, `compound` (`+=`, `<<=`),
  `deferred_let`, `through_view_slice` (write through `view<[u32]>` with a `mut` binding; range sub-slice of an
  immutable array), `mut_view_of_elem` (`AX_TYPE_ASSIGN_IMMUTABLE` ×3, `AX_CAP_CONFLICT_MUT` ×2),
  `accepted_writes` (compile-pass: `let mut` arrays, nested, compound, deferred-then-whole-init, writes through
  an immutable `mut_view<[T]>` binding and its sub-slice, field write through a `mut_view` element of an
  immutable array).
- `tests/ui/own_operand_span/`: `binary_rhs` (20:20), `binary_lhs` (20:13), `compare` (20:12), `call_arg` (24:20).

Results in `build-snap-T498f` (clang Release axiom0 → axiomc2, `-j 2`, `--exclude-requires axiom0-internal`,
baseline `_workspaces/baseline-failures.txt`):
- Build: `BUILD-AXIOMC OK`, FIXED-POINT (O1) OK `sha256(axiomc2_O1) == sha256(axiomc3_O1)`, STAGE0-GUARD OK.
- `ui/`: TOTAL 373 PASS 373 FAIL 0, BASELINE OK.
- `run/`: TOTAL 3133 PASS 3133 FAIL 0, BASELINE OK (WEAK-NATIVE 122 already there; none are tests of this task, all of which are ui).
- `selfhost/typeck` 8/8, `selfhost/mir/` 7/7, `selfhost/own` 10/10, BASELINE OK.

## Decisions
- `mut_view(projection)` of an immutable binding uses `AX_TYPE_ASSIGN_IMMUTABLE` (the same rule as writes,
  SPEC-02 AXS-GRM-041); through a `view` level it uses `AX_CAP_CONFLICT_MUT` as SPEC-03 AXS-SEM-047 says. A whole
  binding `mut_view(x)` keeps today's verifier diagnostic to avoid changing unrelated expectations.
- Deferred projection writes are rejected for fields too, not only indexes (same rule; no existing test relied on it).

## Follow-ups
1. Indexed write after move: point at the place (see T498e section above).
2. `mut_view(x)` of a whole immutable binding is reported only by the MIR verifier as `AX_VERIFY_TYPE_MISMATCH`;
   a typeck diagnostic (`AX_TYPE_ASSIGN_IMMUTABLE`) would be clearer.
3. `mut_view((*p).f)` with `p: *const T` is accepted (used in compiler/verify, compiler/mir/async_lower.ax,
   compiler/interp); decide whether that should need `*mut`.
4. T571: add `view<[N]T>` / `mut_view<view<[N]T>>` write and `mut_view(a[i])` ui cases once index auto-deref exists.

## Files changed
- compiler/types/typeck.ax
- compiler/mir/builder.ax
- tests/ui/assign_immutable_index/elem_write.ax
- tests/ui/assign_immutable_index/field_of_elem.ax
- tests/ui/assign_immutable_index/nested_2d.ax
- tests/ui/assign_immutable_index/compound.ax
- tests/ui/assign_immutable_index/deferred_let.ax
- tests/ui/assign_immutable_index/through_view_slice.ax
- tests/ui/assign_immutable_index/mut_view_of_elem.ax
- tests/ui/assign_immutable_index/accepted_writes.ax
- tests/ui/own_operand_span/binary_rhs.ax
- tests/ui/own_operand_span/binary_lhs.ax
- tests/ui/own_operand_span/compare.ax
- tests/ui/own_operand_span/call_arg.ax
- _workspaces/reports/T498f-report.md

STATUS: COMPLETE round=0
