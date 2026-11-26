# T428j report — evaluate every operand of an aggregate before writing the destination

## Summary
The oracle and the backend run an `Aggregate` / `Repeat` rvalue as a series of per-field stores into the destination.
Each store reads its operand only when that field is written. The MIR builder passed operands as places
(`_1 = aggregate([copy (_1).1, copy (_1).0])`), so a later operand read a field that had already been overwritten. This
gave `3,3,3` for `arr = [arr[2], arr[0], arr[1]]` and `8,8` for a struct swap. Only types without drop glue took this
path, because drop-needing assignments already go through a temporary (AXS-SEM-043).

Fix, in `compiler/mir/builder.ax` only: `mb_emit_assign` now calls `mb_spill_agg_overlaps` before it emits an
`Aggregate` or `Repeat` assignment. Each COPY/MOVE operand that may read memory the destination covers is first
copied or moved into a fresh temporary, left to right. The aggregate then reads that temporary. The operand array is
re-allocated, so the caller's array is not mutated. All aggregate sites go through `mb_emit_assign`: tuple, array,
array-repeat, struct, enum constructors, closures and async bodies (async lowering runs on the built MIR). So one hook
covers every form named in the scope.

## Design choices
- **Operand spill, not "build in a temp and move".** Only the operands that conflict are copied. A rotate of a 3-element
  array costs three scalar copies, not a whole-array copy plus a move. When no operand conflicts, the aggregate is still
  built in place with no extra statement. The golden test below shows this.
- **Overlap test (`mb_places_may_overlap`, conservative):**
  - Same root local: disjoint only when, after an identical prefix of field / deref / same-variant projections, the two
    places select different fields. So `t.l = Pair { a: t.r.b, .. }` is not spilled. An index, sub-slice, different
    downcast variants (shared storage) or one place being a prefix of the other counts as overlap.
  - Different roots, neither through a deref: disjoint.
  - Otherwise (a deref on either side) the places may alias, with two exceptions: a fresh temporary destination, or a
    temporary or constant source read without a deref. This covers `*p = S { a: (*p).b, .. }`, `s = S { a: (*p).b, .. }`
    with `p = address_of(s)`, `*p = S { a: s.b, .. }`, and mut_view destinations.
- **Known limitation, out of scope.** An operand place is still read when the aggregate executes, not when it is
  evaluated. An operand evaluated before a later call that mutates the same memory (`x = [y[0], f(mut_view(y))]`) reads
  the late value. This is a general place-operand timing issue and does not involve the destination. It is unchanged here
  and recorded as a possible follow-up.

## Tests (`tests/run/agg_self_assign/`, exact stdout, interp + native + native-O1)
- `array_rotate.ax`: whole local, an index destination in `[2][3]i64`, a field destination, a runtime index, a parameter
  destination, a repeat form `r = [r[1]; 3]`, and a no-overlap copy.
- `struct_swap.ax`: whole local, a field destination `o.inner = Pair { a: o.inner.b, .. }`, a nested aggregate reading
  the destination at both levels, out-of-order initialisers, and a four-field reverse.
- `tuple_swap.ax`: `t = (t.1, t.0)`, a 3-tuple rotate, and a tuple field destination.
- `pointer_dest.ax`: a store through a raw pointer reading through the same pointer, a store through a `mut_view`, a local
  store reading through a raw pointer to it, a raw-pointer store reading the local, and an array through a raw pointer.
- `enum_payload.ax`: `e = E.V(match e {..}, match e {..})`, an enum payload nested in a struct literal that also swaps
  the struct's fields, and a variant carrying a struct built from the destination's payload.
- `async_rotate.ax` (`async fn`, locals live across `.await`): rotate, swap and tuple after awaits, plus operands that
  suspend: `q = (pair.b, tick(pair.a).await, q.0)` and `pair = Pair { a: tick(pair.b).await, b: pair.a }`.
- `mir_spill_only_on_overlap.ax` + `.mir` (golden MIR): `swap` gets `_2 = copy (_1).1; _3 = copy (_1).0;` before the
  aggregate. `fresh` (distinct source) and `disjoint` (other field of the same local) are built in place with no new
  temporaries. This is the "no needless copy" evidence.

**On HEAD** (`_workspaces/T428j_head_tests.log`, HEAD 61acdeb compiler): all 19 entries fail. The six run tests fail in
interp, native and native-O1 with wrong values (e.g. `3 3 3`, `8 8`, `6 5 5 6`), and the golden shows no spill.
In `enum_payload.ax`, the first case (`match` operands go to temporaries) already passes on HEAD. The file fails on
its second, nested case. **With the fix:** 19/19 pass, `WEAK-NATIVE 0`.

## Verification (snapshot `build-snap-T428j`, HEAD e085e8e6 + this change set)
- `build_axiomc.py --stage 2`: `FIXED-POINT (O1) OK`, STAGE0-GUARD OK, axiomc2 sha256 b3c75f83..
  (`_workspaces/T428j_build3.log`).
- `taskgate.py --task T428j --changed @_workspaces/T428j_changed.txt -j 2` (`_workspaces/T428j_taskgate2.log`):
  `TOTAL 409 PASS 409 FAIL 0`, BASELINE OK, failing ids none, archcheck 252 files 0 violations, `TASKGATE T428j exit=0`.
  It includes the affected selfhost groups of `compiler/mir` (mir, drop, bundle checks of every bundle embedding
  `compiler.mir.builder`). WEAK-NATIVE 0 in own tests.
- Acceptance suites (`_workspaces/T428j_suite_*.log`):
  - `run/`: 3555 total, 3546 pass, 1 fail, 8 skip.
  - `mir/`: 128/128.
  - `opt`: 342 total, 340 pass, 2 fail.
  - `diff/`: 26/26.
- Earlier run on HEAD fb368ce, before T502 landed (`_workspaces/T428j_suites.log`): `run/` 3461/3461, `mir/` 128/128,
  `opt` 342/342.
- **The 2 failures predate this change.** They are `run/opt_lto/opt_lto_engine.test` and
  `selfhost/opt/qa_opt_pipeline.ax [interp]`, both `AX_UNSAFE_INTERP_UB: read of uninitialized memory` at
  `interner_intern_bytes` (`*(mids0 + slot)`). They fail identically with a compiler built from untouched HEAD e085e8e6
  (`build-head-T428j/build/axiomc2.exe`, sha256 1c5aec4c..). They passed on fb368ce, so T502's new oracle UB detector
  (or the interner map buffers that bundle reads) introduced them. They are not in `baseline-failures.txt` and need a
  follow-up task for the T502 owner.
- `tests/opt*` codegen goldens: no golden changed.

## Pre-existing defects found (not changed here)
1. A struct-like enum variant cannot be constructed at all: `let s = E.S { x: 5i64, y: 6i64 };` fails with
   `AX_VERIFY_TYPE_MISMATCH: enum aggregate variant field count mismatch`, also in a 2-variant enum, on HEAD. That case
   was removed from `enum_payload.ax`. Needs its own fix task.
2. The two T502-era failures above.
3. The place-operand timing limitation noted under Design choices.

## Files changed
- compiler/mir/builder.ax
- tests/run/agg_self_assign/array_rotate.ax
- tests/run/agg_self_assign/struct_swap.ax
- tests/run/agg_self_assign/tuple_swap.ax
- tests/run/agg_self_assign/pointer_dest.ax
- tests/run/agg_self_assign/enum_payload.ax
- tests/run/agg_self_assign/async_rotate.ax
- tests/run/agg_self_assign/mir_spill_only_on_overlap.ax
- tests/run/agg_self_assign/mir_spill_only_on_overlap.mir
- tests/run/agg_self_assign/qa_alias_ptr_fields.ax
- tests/run/agg_self_assign/qa_closure_nested_loop.ax
- tests/run/agg_self_assign/qa_drop_swap_once.ax

## Round 1
QA round 0 (`_workspaces/reports/T428j-qa.md`) returned one finding.

**F1, fixed.** `mb_places_may_overlap` treated two places with the same root that split at different fields as
disjoint, even when the rest of one place went through a pointer held in its field. Examples:
`*h.p = Pair { a: (*h.q).b, .. }` with `h.p == h.q`, and `o.v = Pair { a: (*o.p).b, .. }` with `o.p -> o.v`. Both
gave the wrong values (`2 2` and `4 4`).

The fix is in `compiler/mir/builder.ax`. When the two places split at different fields, they are now disjoint only if
neither place has a `DEREF` after the split; the new helper `mb_place_has_deref_from(place, start)` checks this.
Otherwise the pointer rule applies: the places may overlap, unless the destination is a fresh temporary reached
without a deref. QA's third shape was also added, as a regression test in my own `pointer_dest.ax` (new last line
`10 9`): same deref, then different fields, `(*pn).v = Pair { a: (*(*pn).q).b, .. }`, where `(*pn).q` points to
`(*pn).v`. That test fails on HEAD (`build-head-T428j`) in interp, native and native-O1. The no-overlap MIR golden
did not change.

**Verification** (snapshot on HEAD e085e8e6 plus the round-1 change set, including QA's 3 tests):
- Build: `build_axiomc.py --stage 2` gives `FIXED-POINT (O1) OK`, STAGE0-GUARD OK, axiomc2 sha256 53eb65ee..
  (`_workspaces/T428j_build_r1.log`).
- Task tests: `run/agg_self_assign` gives `TOTAL 28 PASS 28 FAIL 0`, `WEAK-NATIVE 0`. That is the 7 run files and
  QA's 3, each in interp, native and native-O1, plus the golden.
- Taskgate: `taskgate.py --task T428j --changed @_workspaces/T428j_changed.txt -j 2`
  (`_workspaces/T428j_taskgate_r1.log`) gives `TOTAL 416 PASS 416 FAIL 0`, BASELINE OK, failing ids none, archcheck
  clean (252 files), `TASKGATE T428j exit=0`. WEAK-NATIVE is 0 in own tests.
- Known failures: the two T502-era interp failures (`run/opt_lto/opt_lto_engine.test`,
  `selfhost/opt/qa_opt_pipeline.ax`) are unchanged and still fail on HEAD without this task, as QA item 7 confirmed.
  They are not in this taskgate's scope.

**QA follow-ups, not part of this task:** the late place-operand read (`q = Pair { a: q.b, b: touch(mut_view(q)) }`)
needs an architect decision or a fix task. Struct-like enum variant construction and the T502 interner UB need their
own tasks.

STATUS: COMPLETE round=1
