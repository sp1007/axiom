# T445 Report — moves and drops through `mut_view` fields and receivers (FU-4, FU-6)

## Summary
Round 0, continuing the partial work of the previous (dead) agent: verified its implementation,
fixed one bug in it, and added one more run test.

### FU-4 — move out of a `mut_view` field, then re-assign (SPEC-12 AXS-DROP-003/007, SPEC-10 AXS-OWN-006)
Rule chosen (the only one the spec allows): SPEC-12 AXS-DROP-007 says a store through a
`view`/`mut_view` place drops the old value **drop-flag aware** ("an uninitialised or moved place is
not dropped, AXS-DROP-003"), and SPEC-10 AXS-OWN-006 allows re-initialising a MOVED place. So the
move out is accepted, and the drop on re-assignment is guarded by a dynamic drop flag.

- `compiler/mir/drop.ax`: "view drop flags". Drop elaboration collects every place that goes
  through at least one `Deref` of a `view`/`mut_view` (no raw-pointer deref, no dynamic index; key
  stops before the first `Downcast`) and that is moved out of or explicitly `drop()`ped somewhere in
  the body and needs drop. Each gets a `u8` flag local, set to 1 at bb0 (a view always points to an
  initialised value, SPEC-11 AXS-CAP-004), cleared on a move out of the place or any sub-place
  (prefix match), set again when the place, a prefix or a sub-place is assigned, and attached
  to `DROP(place)` terminators for the exact place (including drops produced while expanding a
  parent's drop into field drops, so `o.h = ...` after moving `o.h.inner` drops only the live
  fields). Flags are `u8` so they cannot be mistaken for the bool drop flags of locals checked by
  the MIR ownership verifier.
- `compiler/mir/builder.ax` (lock): `match` / `if let` / `while let` on a droppable place reached
  through a view deref now matches **in place** (`mb_build_match_scrutinee`) instead of first moving
  the whole place into a temporary (that eager move was the FU-4 bug: the binding came from the
  temporary while the field still looked initialised). A `while let` binding is dropped at the
  end of each iteration (before, a re-bound droppable binding was overwritten without a drop), and
  `while let` pushes its loop before matching so `break` cleanup sees the binding.
- Fixes to the previous agent's draft made this round:
  1. The collector registered every `DROP` terminator on a view place (it tested
     `terminator.expected`, always true for drops) instead of only explicit `drop(x)`
     (`terminator.drop_is_explicit`); that added a useless flag to every plain `self.f = v`.
  2. The draft also moved the drop of `match`/`if let` bindings to the end of the arm. That
     changes the drop scope of every match binding in the language (not part of FU-4/FU-6, no
     spec rule) and broke `std/async/structured/resource_governor_limits.ax` (its lease bound by
     `match l1 { Result.Ok(l) => true, .. }` must stay alive until the block ends). Reverted: match /
     if-let bindings keep the HEAD scope (end of the enclosing block). See follow-up 2.
  3. The FU-6 reborrow also fired for a temporary view receiver (`mut_view(*cx).waker()`, used
     throughout std/async), creating a second mut_view of `*cx` -> `AX_CAP_CONFLICT_MUT` in 90
     std/async results. The reborrow now applies only when the receiver names a place (`cx`,
     `self.cx`, `*p`); a temporary view is passed by value as before. Regression cases added to
     both FU-6 tests.

### FU-6 — method call on a `mut_view` parameter (SPEC-11 AXS-CAP-001/002/005)
`compiler/mir/builder.ax`: when the receiver is itself a `view`/`mut_view` and the method takes
`self: view<..>`/`mut_view<..>`, the receiver is reborrowed (deref the receiver view(s) down to the
self pointee, then take a fresh view of that place) instead of passing (= moving) the view local.
`cx.waker(); cx.waker(); cx.inspect()` on `cx: mut_view<Context>` now compiles and runs. A real
use after move (by-value `self` called twice; a `mut_view` explicitly moved into another binding
and then used) is still `AX_MOVE_USE_AFTER_MOVE`.

## Tests
- `tests/run/own_mut_view_fields/match_field_reinit_drop.ax` — FU-4 repro (`match self.guard {
  Some(g) => { self.guard = Some(g2) } }`), wildcard arm (old value IS dropped), `if let`,
  `while let`, clear via match.
- `tests/run/own_mut_view_fields/direct_and_conditional_reinit.ax` — direct field move, `*m`, nested
  field, sibling fields, conditional move, explicit `drop(self.f)` + double re-assignment,
  `self.f = transform(self.f)`.
- `tests/run/own_mut_view_fields/partial_move_parent_reassign.ax` (new this round) — move
  `o.h.inner` then assign `o.h`; move `p.a` then assign `*p` (only `b` dropped).
- `tests/run/own_mut_view_fields/reborrow_mut_view_receiver_run.ax` — FU-6 at run time (incl. a
  temporary-view receiver).
- `tests/ui/own_mut_view_receiver/reborrow_mut_view_receiver_ok.ax` — FU-6 positive compile
  (incl. temporary-view receivers `mut_view(*cx).waker()`, `view(*cx).inspect()`).
- `tests/ui/own_mut_view_receiver/by_value_param_use_after_move.ax`,
  `explicit_mut_view_move_uam.ax` — negative counterparts, `AX_MOVE_USE_AFTER_MOVE`.

Every run test has exact `// stdout:` and runs interp, native, native-O1.
Results in `build-snap-T445` (stage-2 `axiomc2.exe` built from this change set):
`--filter own_mut_view`: TOTAL 15 PASS 15 FAIL 0, WEAK-NATIVE 0.

Acceptance suites (`tests/run/own*`, `tests/ui/own*`, `tests/run/drop*`, `tests/std/async`, every
id containing `match`; 308 ids, `-j 2`, baseline file): TOTAL 308 PASS 308 FAIL 0, BASELINE OK
(log `_workspaces/T445_suites.log`, id list `_workspaces/T445_ids.txt`).
Task gate (`tools/taskgate.py --task T445 --compiler build/dir_stage2_O1/axiomc2.exe`, in the
snapshot): affected 169 ids / 326 results PASS 324 SKIP 2; smoke 30 ids / 49 results PASS 49;
archcheck clean; BASELINE OK; WEAK-NATIVE 0 in own tests; `TASKGATE T445 exit=0`
(log `_workspaces/T445_taskgate.log`). Stage-1 and stage-2 (O1) self-builds OK.

## Decisions / open questions
- FU-4 rule: accept the move out of a `mut_view` place and guard the re-assignment drop with a
  dynamic flag (SPEC-12 AXS-DROP-003/007 + SPEC-10 AXS-OWN-006), rather than rejecting the move.
- Follow-up (spec gap, for the architect): a function that moves out of a `mut_view` place and
  returns WITHOUT re-initialising it is still accepted, and the owner then drops the moved value
  again (double drop; e.g. `fn steal(h: mut_view<Holder>) -> Guard { let g = h.inner; g }`).
  SPEC-12 AXS-DROP-007 assumes the pointee of a view is always live, which implies the place must
  be re-initialised on every exit edge (or the move be rejected), but no rule or `AX_*` code says
  so. Not changed by this task (no flags existed before it either). Proposed: new SPEC-10 rule +
  diagnostic `AX_MOVE_OUT_OF_VIEW_NOT_REINIT` checked in `compiler/own/move.ax` at function exit
  (and on panic edges), with the drop-flag machinery here supplying the dynamic case.
- Follow-up 2 (spec gap): SPEC-12 AXS-DROP-001 ("dropped when an owned place goes out of scope")
  suggests a `match`/`if let` binding should be dropped at the end of its arm, but the compiler
  drops it at the end of the enclosing block and `resource_governor_limits.axsrc` (lines 144-149)
  depends on that. The architect should rule on the binding drop scope (ADR); if it becomes
  "end of arm", that std test must be updated in the same task.
- Follow-up 3 (suspected, not verified): a `match` arm with a guard appears to bind (move) before the
  guard is evaluated, so on guard failure the next arm may bind the same droppable payload again.
  Guard lowering is unchanged by this task; QA may want an adversarial test.

## Round 1 (QA `_workspaces/reports/T445-qa.md` round 0: F1, F2)

- **F1 fixed** (guarded arm on a mut_view place, double Drop): `compiler/mir/builder.ax` `match`
  lowering keeps the HEAD temporary scrutinee whenever any arm has a guard; in-place matching
  (FU-4) is used only for guard-free matches. The move checker therefore again reports the second
  by-move binding of the same payload (`AX_MOVE_USE_AFTER_MOVE`), exactly as for a local
  scrutinee. Guard lowering itself (bindings move before the guard runs) is unchanged and remains
  follow-up 3 (now confirmed by QA). Test: `tests/ui/own_mut_view_receiver/qa_guard_arm_view_place_move.ax`.
- **F2 fixed** (view receiver upgraded to mut_view): the reborrow keeps or weakens the
  capability: `compiler/mir/builder.ax` does not reborrow when the self parameter is `mut_view`
  and any receiver layer is a shared `view`; `compiler/types/typeck.ax` (lock)
  `check_expr_method_call` reports `AX_TYPE_MISMATCH` at the receiver for a `view<T>` receiver of
  a `self: mut_view<..>` method (same code as a free-function call `f(cx)` with these types;
  a `mut_view<Self>` whose `Self` is itself a view type is exempt, since that autorefs the view
  value). Test: `tests/ui/own_mut_view_receiver/qa_view_recv_mut_method.ax`.
- QA tests kept unchanged: `qa_adv_drop_paths.ax`, `qa_adv_reborrow_receivers.ax`,
  `qa_guard_arm_view_place_move.ax`, `qa_view_recv_mut_method.ax`.
- Snapshot stage-0 now configured Release (gcc); the earlier round-0 build had used Debug.
- Results (build-snap-T445, stage-2 axiomc2 sha256=d16d39a81448d6a5): `--no-cache --filter
  own_mut_view` TOTAL 23 PASS 23, WEAK-NATIVE 0.
- Acceptance suites (run/own, ui/own, run/drop, std/async, every `match` id; 316 ids, `-j 2`,
  baseline): TOTAL 316 PASS 316 FAIL 0, BASELINE OK (`_workspaces/T445_suites.log`).
- Task gate (taskgate.py, in the snapshot; affected set now includes the typeck change):
  affected 214 ids / 391 results PASS 389 SKIP 2; smoke 30 ids / 49 PASS; archcheck clean;
  BASELINE OK; WEAK-NATIVE 0 in own/changed tests; `TASKGATE T445 exit=0`
  (`_workspaces/T445_taskgate.log`).

## Files changed
- compiler/mir/builder.ax
- compiler/mir/drop.ax
- compiler/types/typeck.ax
- tests/run/own_mut_view_fields/match_field_reinit_drop.ax
- tests/run/own_mut_view_fields/direct_and_conditional_reinit.ax
- tests/run/own_mut_view_fields/partial_move_parent_reassign.ax
- tests/run/own_mut_view_fields/reborrow_mut_view_receiver_run.ax
- tests/ui/own_mut_view_receiver/reborrow_mut_view_receiver_ok.ax
- tests/ui/own_mut_view_receiver/by_value_param_use_after_move.ax
- tests/ui/own_mut_view_receiver/explicit_mut_view_move_uam.ax
- tests/run/own_mut_view_fields/qa_adv_drop_paths.ax
- tests/run/own_mut_view_fields/qa_adv_reborrow_receivers.ax
- tests/ui/own_mut_view_receiver/qa_guard_arm_view_place_move.ax
- tests/ui/own_mut_view_receiver/qa_view_recv_mut_method.ax
- _workspaces/reports/T445-report.md

STATUS: COMPLETE round=1
