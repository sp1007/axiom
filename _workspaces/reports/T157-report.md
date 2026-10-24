# T157 report

## Summary
AX0-FIX-06: the capability checker of both compilers (`bootstrap/axiom0/src/own/cap/cap.c` and the
port `compiler/own/cap.ax`, changed in lockstep, ADR-0034 section 2) now accepts the valid programs of
SPEC-11 AXS-CAP-008/009 and still rejects owner-outlives violations (AXS-CAP-004) with byte-identical
diagnostics.

### HEAD behaviour (established first, fresh snapshot build)
| Program | axiom0 HEAD | axiomc HEAD |
| --- | --- | --- |
| `let mut b = S {}; let p: *mut S = unsafe { address_of_mut(b) };` (`impl Drop for S`) | accepted | `AX_CAP_OUTLIVES_OWNER` at the function's `{` |
| `let a = S { x: 1 }; let va: view<S> = view(a);` (`impl Drop for S`) | `AX_CAP_OUTLIVES_OWNER` at the function's `{` | same |
| outer `keep: view<D>` bound to an inner-block owner, used after the block | 3 errors (binding + inner drop + outer drop) | same 3, printed in a different order |

### Root cause
Both checkers run a forward dataflow on pre-elaboration MIR that records, per local, the capability
it holds; a capability ended only at the holder's `StorageDead` or reassignment. The owner-outlives
check fired at **every** `drop`/`move` of the owner while any holder was in the state.
- AXS-CAP-009 (both compilers): pre-elaboration MIR has no `StorageDead` for named view locals (nor for
  the `view(a)` temporary) before the scope-end `drop(a)`, so a view local that was dead long before
  was still "active" at the owner's drop.
- AXS-CAP-008 (axiomc only): `address_of_mut(b)` lowers to `_t = &mut b; _p = copy _t as *mut S`.
  axiom0's MIR builder emits `StorageDead(_t)` after the cast, axiomc's does not (a MIR-construction
  difference, T149's area, not changed here), so in axiomc the `&mut b` temporary stayed active until
  the scope-end `drop(b)`.

### Fix (same algorithm in both compilers)
1. New query `cap_local_used_from(body, bb, stmt, l)`: does some normal (non-unwind) CFG path from that
   position (inclusive) reach a use of local `l` before `l` is reassigned or its storage
   ends? It is a forward worklist search over the existing MIR. No new MIR facts were needed, and MIR
   construction is unchanged.
2. Owner-outlives on `drop`/`move` (AXS-CAP-004/009): reported only if the holder is still used after
   that point. A holder declared before its owner (lower local index) is not reported again, because
   the existing binding-time check (`dest < owner`) already reported it at `keep = view(a)`. So there
   is one diagnostic per violation, which also removes the order difference between the two
   compilers (only axiomc sorts its diagnostics).
3. Raw pointers (AXS-CAP-008): `_p = copy _t as T` ends `_t`'s capability at the cast when `_t` is not
   used again. The pointer never held one. This is applied in the dataflow pass too, so later
   `view(b)`/`mut_view(b)` do not conflict with a dead `address_of` temporary in axiomc.
4. Moves of droppable owners: the MIR builder writes `copy` for every use of a named local, and the
   checker has no types. A whole-local `copy _l` now counts as a move when the body drops `_l`
   (`cap_local_is_dropped`): a type that needs drop is never Copy. Without this, item 2 would have lost
   the HEAD rejection of "move a droppable owner while a view of it is still used". That rejection was
   only incidental at HEAD (reported at the function end); it is now reported at the move itself.

### Decisions (taken, not asked)
- Conflict checks (AXS-CAP-003) keep the scope-based extent (until `StorageDead`/reassignment), not
  last use. `tests/ui/cap/test_view_cap.ax`/`test_view_qa.ax` pin `let v1 = mut_view(a); let v2 =
  view(a);` with an unused `v1` as an error, and the task requires every existing expectation to stay
  the same. Liveness is used only for the owner-outlives check, which is what AXS-CAP-009 is about.
  Whether conflicts should become last-use based is a separate spec question for the architect (see
  Follow-ups).
- REPEAT rvalues: only the element operand counts as a use. The count is a `usize` and can never hold a
  capability. Both compilers do the same; the older `mir.ax` embedded in the hand-written bundles has no
  `repeat_count_op`.

## Regenerated bundles (ADR-0034 section 2)
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_*.ax` (11 files) via `gen_own_mir_verify_tests.py
  --axiom0 build-T157/axiom0.exe --oracle build-T157/tests/ct_selfhost_drop_cdriver_drop_oracle.exe`.
  The generator also gains the new ui fixture `tests/ui/cap/view_outlives_drop_owner.ax` in the
  `cap_ptr` group, so the port's rendered diagnostics are compared byte for byte with axiom0's
  (`CAP_PTR` is now 8 ax cases).
- `tests/selfhost/driver/qa_driver_{commands,inspect_diff}_{a,b}.ax` via `gen_driver_tests.py`.
- `tests/selfhost/interp_opt/qa_interp_opt_*.ax` (7 files) via `gen_interp_opt_tests.py`.
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_{diff,smoke}.ax` via `gen_obj_link_driver_tests.py`.
- `tests/selfhost/cap/qa_own_cap.ax` and `tests/selfhost/own/qa_own_init.ax` had no generator; they are
  now refreshed by the new `tests/selfhost/cap/refresh_cap_bundles.py`. It rewrites the embedded
  `// --- compiler/own/cap.ax ---` section, is idempotent and supports `--check`. Run on the HEAD
  `cap.ax` it reproduced both bundles byte for byte, so it encodes exactly the existing embedding.
- Each regenerated bundle differs from HEAD only in the `cap.ax` section (+364/-17 lines, the same
  numbers as the `cap.ax` diff; +363 in the two hand-written bundles, which drop `use` lines).

## Files changed
- bootstrap/axiom0/src/own/cap/cap.c
- compiler/own/cap.ax
- tests/run/parity/cap/raw_ptr_of_drop_local.ax
- tests/run/parity/cap/view_local_of_drop_owner.ax
- tests/ui/cap/view_outlives_drop_owner.ax
- tests/selfhost/cap/refresh_cap_bundles.py
- tests/selfhost/cap/qa_own_cap.ax
- tests/selfhost/own/qa_own_init.ax
- tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax
- tests/selfhost/driver/qa_driver_commands_a.ax
- tests/selfhost/driver/qa_driver_commands_b.ax
- tests/selfhost/driver/qa_driver_inspect_diff_a.ax
- tests/selfhost/driver/qa_driver_inspect_diff_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_unit.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
- _workspaces/reports/T157-report.md

## Tests
New tests (expected output written by hand):
- `tests/run/parity/cap/raw_ptr_of_drop_local.ax` (`modes: interp native`): `address_of_mut`/`address_of`
  on locals of a scalar-field and a fieldless `impl Drop` type, a field store and a whole-value raw
  store through the pointer (no destructor for the overwritten value, AXS-DROP-007), a read and a
  `view` of the owner, a move of the owner after taking a pointer, and the scope-end drops.
  stdout `2 2 3 D3 empty E 5 D5`.
- `tests/run/parity/cap/view_local_of_drop_owner.ax` (`modes: interp native`): `view<S>` and
  `mut_view<S>` locals on droppable owners at a function end, in a nested block, and before an early
  `return` (both branches). The destructor order is pinned:
  `1 3 D3 D1 4 5 D5 4 D4 D6 6 D8 D6 8`.
- `tests/ui/cap/view_outlives_drop_owner.ax`: the AXS-CAP-009 reject row with a droppable `D` and with
  `i32` (one `AX_CAP_OUTLIVES_OWNER` each, at `keep = view(a)`), a droppable owner moved while its view
  is still used (`AX_CAP_OUTLIVES_OWNER` at `let b = a;`), and the accepted twin where the view is dead
  before the move.

Probes with axiomc (the T085 bundle built by the snapshot axiom0): `check` output and exit code are
byte-identical to axiom0 for all 92 files in `tests/ui/{cap,own,slice,closure,ptr}`,
`tests/conformance/stress`, `tests/run/{parity/cap,drop,cap}`, except 6 files. Those 6 diverge
identically with HEAD axiomc, so the difference is not caused by T157: `ui/slice/overlapping_mut.ax`
and `qa_overlapping_mut_open.ax` (axiomc exits 127), and 4 `ui/closure/*` (closure-stage messages).
Both new run tests give the same stdout from axiom0 interp, axiom0 native and axiomc native.

Runs in `build-snap-T157`:
- gcc Debug build (`--clean-first`): 0 warnings. clang build (`build-T157-clang`): 0 warnings.
- `python tools/archcheck.py`: 192 files, 0 violations.
- Focused runs: `ui/ conformance/ run/parity run/drop run/cap run/ptr run/slice run/own` 737/737 PASS.
  `selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr selfhost/cap/ selfhost/own/` 8/8 PASS.
- `axiomc_e2e_oracle.py`: `OK`, `programs=490 equal=404 known_divergent=86`. No REGRESSION, no XPASS, and
  `known_divergent.txt` is unchanged: no entry was caused by these false positives.
- Full suite `python tools/axtest.py --compiler build/axiom0.exe -j 6 --timeout-scale 3`: TOTAL 2667,
  PASS 2666, FAIL 1. The one failure, `run/host/fs/metadata.ax [native]` (exit 1), is flaky and not
  related to T157. The test always uses the same file name `test_metadata.tmp` in the working
  directory, so its interp and native legs, run in parallel, race on it. Rerun alone
  (`run/host/fs/`): 12/12 PASS. This is the same leg-isolation problem T139 fixes for
  `tests/run/host/fs/dir.ax`.

## Spec deviations
None. AXS-CAP-009 is applied to the owner-outlives check. Conflict detection keeps its scope-based
extent, as pinned by the existing ui tests (see Decisions).

## Follow-ups
- Architect: say whether AXS-CAP-003 conflicts should also use the last-use extent of AXS-CAP-009.
  Today `let v1 = mut_view(a); let v2 = view(a);` with an unused `v1` is an error by test, which is
  stricter than the AXS-CAP-009 wording. If it should change, a task would update both checkers and the
  ui expectations.
- T149 (MIR construction): axiomc emits no `StorageDead` for the `address_of` temporary, while axiom0
  does. T157 no longer depends on it, but it is a MIR-text divergence.
- `tests/run/host/fs/metadata.ax`: give each leg its own temp-file name, as T139 does for `dir.ax`.
- Moves of non-Copy types that need no drop are still written as `copy` in MIR and are not seen as
  moves by the type-free capability checker (same as HEAD). A precise fix would pass Copy-ness from
  `own.c`/`init.ax` into the checker; that is outside this task's paths.

STATUS: COMPLETE round=0
