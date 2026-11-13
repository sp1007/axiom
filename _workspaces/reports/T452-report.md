# T452 report - E12.1 Oracle 128-bit evaluator, saturating/bit intrinsics & const folding

## Summary
- `compiler/interp/*`: the oracle evaluates `i128`/`u128` exactly as `(lo, hi)` u64 pairs (`InterpCtx.val_hi/val_ovf/rem_lo/rem_hi` carry the second word): checked `+ - *`, `/ %` (`division by zero`, `i128.MIN / -1` and `% -1` overflow), unary `-`/`~`, `& | ^`, shifts (panic when the amount is `< 0` or `>= 128`), all comparisons, `IntToInt` casts across `i8..i128`/`u8..u128`, `SatAdd/SatSub/SatMul`, `wrapping_add/sub/mul/neg`, `rotate_left/right`, `leading_zeros`, `trailing_zeros`, `count_ones`, `swap_bytes`, `reverse_bits`, and 128-bit print. 128-bit constants are read through `mir_const_int_hi`; the session const evaluator returns the high word through `const_val_set_int_hi`.
- `compiler/opt/const_fold.ax`: the -O1 folder folds binary and unary operations whose operands are both constants, 128-bit included: `+ - * / %`, `& | ^`, shifts, comparisons, unary `-` and `~`, `wrapping_add/sub/mul` and `saturating_add/sub/mul` (`MirBinOp.SatAdd/SatSub/SatMul`). It never folds an operation that must panic at run time (overflow, division by zero, bad shift stay as `assert` / the original rvalue).
- Correction (round 1, QA FINDING-2): the bit intrinsics `rotate_left/right`, `leading_zeros`, `trailing_zeros`, `count_ones`, `swap_bytes`, `reverse_bits` are NOT folded at -O1. The MIR builder expands them into shift/mask/arith sequences over temporaries (`mir-opt -O1` of `1u128.reverse_bits()` leaves about 40 statements) and the -O1 pipeline does not propagate constants through locals, so the folder never sees two constant operands. The results are correct (the oracle evaluates them, and QA's differential agreed with a Python big-int model); they are just not constant-folded. Follow-up (cheap options): either teach the MIR builder to emit a single `MirBinOp`/intrinsic node the folder can evaluate, or add local constant propagation before the fold pass; the interpreter already has all of these as `u128_*_raw` helpers that the folder could call.
- `compiler/mir/builder.ax`: `mb_intr_materialize` keeps a constant operand as-is instead of spilling it to a temp (so intrinsic calls on constants reach the folder).
- Cleanup in this round: `classify_int_ty` had a duplicated tail from an earlier attempt that silently changed `bool` from 1 bit to 8 bits; removed, original behaviour restored.
- `u128_neg_raw` (interp) and `opt_u128_neg_raw` (const_fold) were rewritten (see FU-T452-NEG below).

## Tests
- `tests/run/int128_interp/*.ax` (9 programs, interp, each with `native-after: T453`): arithmetic, negation carry (`neg_carry`), bit intrinsics, saturating ops, overflow/div-zero/shift panics (exit 101), REQ-OWNER-007 Pattern D.
- `tests/opt/int128/*.test` (3 manifests): `const_fold_int128` (folds 128-bit add/saturating/cmp/bitnot), `const_fold_no_fold_overflow` (runtime overflow/div-zero asserts survive -O1), `const_fold_neg_carry` (new: negation of a constant with low word 0 / non-zero / small, through `const` items so the unary op reaches the folder).
- `--filter int128` in `build-snap-T452` with the rebuilt O1 `axiomc2.exe`: TOTAL 53, PASS 34, FAIL 1, SKIP 18. The one failure is `typeck/int128/int128_literals_and_methods.test` (pre-existing, see below). `neg_carry` and `const_fold_neg_carry` pass.
- Targeted run (`--filter run/comptime --filter mir/int128 --filter opt/int128 --filter run/intrinsics --filter run/int128_interp`, `-j 2`): TOTAL 88, PASS 70, FAIL 0, SKIP 18, WEAK-NATIVE 0.
- `archcheck.py`: 229 files scanned, 0 violations. Round 0 ran only 10 of the 34 `selfhost/*/bundles_current.test` freshness checks and missed `lir`; round 1 ran all 34 (34/34 PASS, see Round 1).
- After my second round of edits the bundle generators' `--check` found 6 groups stale (backend, driver, interp, interp_opt, obj_link_driver, opt); all were regenerated. 48 bundle files were changed in round 0 (the task started with 46; the two `obj_link_driver` bundles were added) and 5 more `lir` bundles in round 1, 53 in total.

## Selfhost bundle verification (all 48 regenerated bundles compiled and run, serially, -j 1)
Each bundle was run with `tools/axtest.py -j 1` using the stage-2 `axiomc2.exe` built from the snapshot (both native modes, and interp where the bundle declares it). No bundle was skipped; the log is `bundles.log` in the scratchpad (`RESULT` and `HEADRESULT` lines).

- PASS: 31 of 48 bundles.
- FAIL, pre-existing (the same bundle taken from `git show HEAD:<path>` fails with the identical exit code in the same modes): 17 of 48.
- FAIL caused by T452: 0.

Pre-existing failing bundle ids (proof: the HEAD copy fails identically):
- driver/qa_driver_commands_b.ax - exit 33 (native, native-O1)
- driver/qa_driver_inspect_diff_b.ax - exit 42
- drop/qa_drop_d01.ax, d02, d03, d04, d05, d06, d07, d09, d10, d11, d12 - exit 300 (case 0, build pass; d01 first mismatch: expected `type#17`, actual `type#21` for the same aggregate type). For d01 it was also checked under `run --interp` with both the new stage-2 and the old main-tree `axiomc2.exe` built before any T452 edit: exit 44, same output.
- interp_opt/qa_interp_opt_diff_mir_b.ax - exit 312
- obj_link_driver/qa_obj_link_driver_diff.ax and qa_obj_link_driver_smoke.ax - exit 101
- own_mir_verify/qa_own_mir_diff_drop_b.ax - exit 301
(2 + 11 + 1 + 2 + 1 = 17.) These are in other tasks' areas and should become follow-ups for the architect.

Passing bundles (31): backend x6 (diff_lir_a/b, diff_mi_mc_a/b, edge, unit), driver commands_a and inspect_diff_a, interp x3, interp_opt x6 (comptime_a/b, diff_mir_a, diff_run_a/b, unit), mir x3, opt x2, own_mir_verify x8 (all but drop_b), verify x1.

## WEAK-NATIVE finding (pre-existing, generator-inherent)
12 weak native runs in total across 6 bundles (2 each): driver commands_a, commands_b, inspect_diff_a, inspect_diff_b and obj_link_driver diff, smoke. Cause: `tools/axtest.py::is_weak_native_evidence` flags a native run with no `stdout:`/`stderr:`/`*-contains` directive and exit 0 expected. The headers written by `tests/selfhost/driver/gen_driver_tests.py` (and the obj_link_driver generator) have none, and are the same at HEAD, so my regeneration did not introduce it. Follow-up for the architect: make those generators print an `OK ...` line and emit a `// stdout:` directive, then regenerate (not done here: it would require re-running every affected bundle). All other bundles show WEAK-NATIVE 0.

## Pre-existing failure outside T452's paths
`tests/typeck/int128/int128_literals_and_methods.test` (T451) fails with two `AX_TRAIT_UNSATISFIED_BOUND` errors at `inspect --emit=thir`. The main-tree `build/axiomc2.exe` built at 12:35 (before any T452 edit) fails identically; the failure is in typeck before MIR, so none of the T452 files can be involved. Probably a regression from a later change in `compiler/types`. Follow-up for the architect/QA.

## Open follow-up FU-T452-NEG (needs an architect task)
The neg_carry fix is a workaround, not a root-cause fix. Original form (both `u128_neg_raw` in `compiler/interp/interp.ax` and `opt_u128_neg_raw` in `compiler/opt/const_fold.ax`):

```
let nlo = w_add_u64(lo ^ 0xFFFFFFFFFFFFFFFFu64, 1u64);
let carry: u64 = if lo == 0u64 { 1u64 } else { 0u64 };
let nhi = w_add_u64(hi ^ 0xFFFFFFFFFFFFFFFFu64, carry);
```
- Symptom with the stage-2 O1 `axiomc2.exe` built (axiomc1 -> stage 2, -O1) from sources containing this form: `-(1i128 << 64)` (lo = 0, hi = 1) gave hi `0xFFFFFFFFFFFFFFFE` (carry lost); `-x` with lo != 0 was right; `0 - x` was right. Repro: `axiomc2 run --interp tests/run/int128_interp/neg_carry.ax` returned exit 1 (first check). In the -O1 folder `-TWO64` folded to 340282366920938463426481119284349108224 instead of 340282366920938463444927863358058659840 (`tests/opt/int128/const_fold_neg_carry.ax`, run on the old binary, sha256 starting 2fe382a0).
- A standalone 20-line copy of the same functions (a `Ctx` struct, the same `w_add_u64`) passes at O0, O1 and under `--interp`, so the failure only appears when the function is compiled as part of the compiler bundle, or through an interaction I could not isolate. The O0 stage-2 build timed out after 40 min (rc 143) on the loaded machine, so O0 was not compared.
- Replaced by `0 - x` semantics (low word `0 - lo`, borrow = `lo != 0`, high word `0 - hi - borrow`). Regression tests `neg_carry` (interp) and `const_fold_neg_carry` (fold) pass with the rebuilt stage-2 (sha256 starting a21aee32). Needs: bisect the O1 pipeline on the original form (candidates: an `if` expression feeding an add after `^` with an all-ones u64 constant, or the folder changes of this very task being applied while compiling the compiler).

## Round 1 (QA gate fix round)
- FINDING-1 fixed. My earlier staleness scan printed only the last line of each generator's `--check`, so it missed `selfhost/lir` (5 of its 7 bundles embed `mb_intr_materialize` from `compiler/mir/builder.ax`, line 55111). Regenerated `tests/selfhost/lir/qa_lir_from_ax_a..e.ax` (5 files). Then, without relying on any earlier list, ran `--check` of ALL 36 `tests/selfhost/*/gen_*.py` generators and counted `DIFFERS` per generator: 0 everywhere (ALL-UP-TO-DATE; lir now 7 up to date). All 34 `tests/selfhost/*/bundles_current.test` tests then pass through `axtest --filter bundles_current`: TOTAL 34, PASS 34, FAIL 0. `selfhost/lir/qa_lir_from_ax_a.ax` compile+run in all modes at `-j 1`: TOTAL 3 PASS 3 FAIL 0 SKIP 0, WEAK-NATIVE 0 (interp, native, native-O1; `-j 1`).
- FINDING-2: report text corrected above (bit intrinsics are not folded at -O1; results correct).
- FINDING-3 (native `saturating_add/sub/mul` wrong on u8..i64, e.g. `0u8.saturating_sub(1u8)` prints 1): pre-existing, present with the pre-T452 compiler, outside T452 (native codegen); not fixed here. For T453/the architect: T453 acceptance should include narrow-width native saturating checks.
- Spec gap for the architect: compile-time `1u128 << 128u128` reports `AX_CONST_OVERFLOW`, while SPEC-40 (lines 81, 491) names `AX_CONST_SHIFT_RANGE` (3104), which is not registered in any `diag/codes/*.def`; behaviour is the same with the old compiler, so it was not changed here.
- The 23 QA-written test files (`tests/run/int128_interp/qa_*`, `tests/opt/int128/qa_*`) belong to the QA change set (listed in `T452-qa.md`) and are not in this report's Files changed.

## Notes / decisions
- Bundle regeneration relies on each `gen_*_tests.py` reading `compiler/` from the working tree; all 48 files are generated output, never hand-edited.
- Pre-existing failures are not fixed here (outside paths/locks); each is proven pre-existing by running the HEAD copy of the bundle with the same compiler.
- Not done: LIR/x86-64 codegen of `i128`/`u128` (T453); every new run test carries `native-after: T453`.

## Files changed
- compiler/interp/frame.ax
- compiler/interp/interp.ax
- compiler/interp/value.ax
- compiler/interp_opt/session.ax
- compiler/mir/builder.ax
- compiler/opt/const_fold.ax
- tests/opt/int128/const_fold_int128.ax
- tests/opt/int128/const_fold_int128.test
- tests/opt/int128/const_fold_neg_carry.ax
- tests/opt/int128/const_fold_neg_carry.test
- tests/opt/int128/const_fold_no_fold_overflow.ax
- tests/opt/int128/const_fold_no_fold_overflow.test
- tests/run/int128_interp/arith_basic.ax
- tests/run/int128_interp/bit_intrinsics.ax
- tests/run/int128_interp/neg_carry.ax
- tests/run/int128_interp/panics_div_zero.ax
- tests/run/int128_interp/panics_overflow_add.ax
- tests/run/int128_interp/panics_overflow_div.ax
- tests/run/int128_interp/panics_shift.ax
- tests/run/int128_interp/pattern_d.ax
- tests/run/int128_interp/saturating.ax
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
- tests/selfhost/driver/qa_driver_commands_a.ax
- tests/selfhost/driver/qa_driver_commands_b.ax
- tests/selfhost/driver/qa_driver_inspect_diff_a.ax
- tests/selfhost/driver/qa_driver_inspect_diff_b.ax
- tests/selfhost/drop/qa_drop_d01.ax
- tests/selfhost/drop/qa_drop_d02.ax
- tests/selfhost/drop/qa_drop_d03.ax
- tests/selfhost/drop/qa_drop_d04.ax
- tests/selfhost/drop/qa_drop_d05.ax
- tests/selfhost/drop/qa_drop_d06.ax
- tests/selfhost/drop/qa_drop_d07.ax
- tests/selfhost/drop/qa_drop_d09.ax
- tests/selfhost/drop/qa_drop_d10.ax
- tests/selfhost/drop/qa_drop_d11.ax
- tests/selfhost/drop/qa_drop_d12.ax
- tests/selfhost/interp/qa_interp_exec_a.ax
- tests/selfhost/interp/qa_interp_exec_b.ax
- tests/selfhost/interp/qa_interp_unit.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_unit.ax
- tests/selfhost/lir/qa_lir_from_ax_a.ax
- tests/selfhost/lir/qa_lir_from_ax_b.ax
- tests/selfhost/lir/qa_lir_from_ax_c.ax
- tests/selfhost/lir/qa_lir_from_ax_d.ax
- tests/selfhost/lir/qa_lir_from_ax_e.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_a.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_b.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_c.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
- tests/selfhost/opt/qa_opt_pipeline.ax
- tests/selfhost/opt/qa_opt_unit.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax
- tests/selfhost/verify/qa_verify_pipeline.ax

STATUS: COMPLETE round=1
