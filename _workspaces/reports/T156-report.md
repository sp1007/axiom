# T156 Report — Dump and Diagnostic Parity, Extended E2E Oracle Dump Comparison, and Empty Divergence Registry

## Summary

1. **Resolved Dump Parity (`compiler/resolve/resolver.ax`)**:
   - Removed the extra `EXPR_TUPLE` walk from `resolve_expr` in `compiler/resolve/resolver.ax` (matching `bootstrap/axiom0/src/resolve/resolve.c:662`, which does not resolve `AST_EXPR_TUPLE` children in `resolve_expr`). Previously, `resolver.ax` walked `EXPR_TUPLE` and resolved paths inside tuple expressions (`(x as i32, ...)`), attaching `@Sym(2)` to builtin type `PathSegment` nodes (`(PathSegment @Sym(2) "i32")`) where `axiom0` prints `(PathSegment "i32")`.
   - Result: **0 `inspect --emit=resolved` diffs** across the entire 539-program corpus (`539/539` identical).

2. **THIR Dump Parity & Type Interning Order Parity (`compiler/types/typeck.ax`)**:
   - Ported `axiom0`'s exact type interning order and THIR dump behavior from `bootstrap/axiom0/src/types/typeck.c` into `compiler/types/typeck.ax`:
     - `pre_find_method_types` before `find_method` in `desugar_for` and `check_expr_method_call` (`typeck.c:916-921`), ensuring `subst_type_by_name` interns inherent `impl` method parameter/return types during candidate search in the exact same order as `axiom0`.
     - `lookup_path_type` / `lookup_path_type_by_name`: stopped pre-interning `TY_SLICE` when parsing `[T]` inside `view<[T]>` / `mut_view<[T]>` before the enclosing `TY_VIEW` / `TY_MUT_VIEW` is interned (`typeck.c:722`), and added a fallback parameter-name lookup across `(*cx.current_fn).params` when `path.symbol.v == 0` so function parameters inside `EXPR_TUPLE` remain resolved in typeck (`qa_own_mir_diff_diag_verify_mir.ax` Seam 4).
     - `evaluate_const_item`, `eval_array_len_expr`, and `eval_const_expr_int`: aligned `const` item body typechecking and array length evaluation with `typeck.c:568,690`, guarded `sym_constmap_insert` on `ok && eval_err == 0u32 && sym_v != 0u32` (`qa_backend_diff_mi_mc_b.ax`), and implemented trap-free 64-bit two's-complement wrapping arithmetic helpers (`tc_wrapping_add_u64`, `tc_wrapping_neg_u64`, `tc_wrapping_sub_u64`, `tc_wrapping_mul_u64`) so signed `i64` overflow in `eval_const_expr_int` does not trap under `axiom0`'s runtime overflow check (`qa_interp_opt_diff_comptime_b.ax`).
     - `register_item_sig`, `build_item_generic_param_args`, `check_item_body`, `typeck_pass1a`, and `typeck_pass1b_and_2`: aligned generic parameter registration, closure item skipping, and pass ordering with `typeck.c`, and deferred `AX_TYPE_STORED_VIEW_ESCAPE` / `AX_TYPE_STORED_VIEW_SELF_REF` emission solely to `compiler/verify/verifier.ax` (`qa_own_mir_diff_diag_cap_ptr.ax`).
     - Removed an obsolete `if needs_prelude:` `.replace(...)` workaround in `tests/selfhost/backend/gen_backend_tests.py` now that `compiler/mir/builder.ax` emits `StorageDead` identically to `axiom0` (`qa_backend_diff_lir_b.ax`).
     - `resolve_deep_ty` and `finalize_types`: aligned `TY_FN`/`TY_VIEW`/`TY_MUT_VIEW`/`TY_PTR` deep resolution during `finalize_types` with `typeck.c:5330-5385`, followed by in-place resolution of `TY_TUPLE`/`TY_ARRAY`/`TY_SLICE` inner types and deduplication so `compiler/verify/verifier.ax` sees resolved concrete element/field `TypeId`s without shifting `thir.interner.len` (`type#N` numbering).
     - `td_expr` (`HIR_EXPR_CALL`): matched `axiom0`'s `emit_thir` printing of inferred generic callee `TY_FN` signatures.
   - Result: **0 `inspect --emit=thir` diffs** across the entire 539-program corpus (`539/539` identical), and **0 `type#N` numbering diffs** in `mir`/`lir` dumps across all corpus programs.

3. **MIR `StorageDead` Parity (`compiler/mir/builder.ax`)**:
   - Implemented `mb_emit_storage_dead` in `compiler/mir/builder.ax` (lines 942–975) to emit `MIR_STMT_STORAGE_DEAD` (`StorageDead(_N);`) after `address_of` / `address_of_mut` on drop-needing locals, matching `bootstrap/axiom0/src/mir/build/builder.c:2380-2385`.
   - Result: **0 `inspect --emit=mir|lir|mi|mc` diffs** across all 539 corpus programs (`539/539` identical).

4. **Diagnostic Message Text Parity (`compiler/types/typeck.ax`, `compiler/hir/lower.ax`, `tests/run/parity/diag/`)**:
   - Ported `axiom0`'s exact diagnostic message table (`TC_DIAG_MSG_DATA` / `TC_DIAG_MSG_OFF`, `tc_alloc_diag_msg`, `fix_unsatisfied_bound_msgs`) into `compiler/types/typeck.ax` for all typeck diagnostic codes (`44..=99` and `133` `AX_TYPE_UNKNOWN_INTRINSIC`), replacing the generic `"type error"` placeholder with `axiom0`'s exact message strings (`"unreachable statement"`, `"cannot index into a value of this type"`, `"callee is not a function"`, `"mismatched types"`, etc.).
   - Updated `LOWER_NOT_SUPPORTED_MSG` in `compiler/hir/lower.ax` to `"construct parsed but not lowered by this build yet (AXD-014)"` (matching `bootstrap/axiom0/src/hir/lower.c:15`).
   - Added 3 UI tests (plus `.test` exact-stderr manifests) under `tests/run/parity/diag/`:
     - `tests/run/parity/diag/unreachable_stmt.ax` + `unreachable_stmt.test` (`AX_TYPE_UNREACHABLE`: `warning[AX_TYPE_UNREACHABLE]: unreachable statement`)
     - `tests/run/parity/diag/cannot_index.ax` + `cannot_index.test` (`AX_TYPE_CANNOT_INDEX`: `error[AX_TYPE_CANNOT_INDEX]: cannot index into a value of this type`)
     - `tests/run/parity/diag/not_callable.ax` + `not_callable.test` (`AX_TYPE_NOT_CALLABLE`: `error[AX_TYPE_NOT_CALLABLE]: callee is not a function`)

5. **Driver `inspect` Error-Case & Object-Emission Parity (`compiler/driver/pipeline.ax`, `bootstrap/axiom0/src/driver/emit_{mir,lir,mi,mc,obj}.c`)**:
   - **Error-case `inspect` parity (4 programs: `tests/driver/error.ax`, `tests/run/parity/traits/qa_self_missing_member.ax`, `tests/run/parity/diag/cannot_index.ax`, `tests/run/parity/diag/not_callable.ax`)**:
     - In `compiler/driver/pipeline.ax` (`driver_execute_inspect_ctx`, `EMIT_HIR`), when `!ok && (ctx.hir.items as usize) == 0 && (ctx.ast.items as usize) != 0`, invoked `pipeline_stage_hir(mut_view(*ctx))` before `session_render_hir_into(...)`, matching `bootstrap/axiom0/src/driver/pipeline.c:807`.
     - In `bootstrap/axiom0/src/driver/emit_{mir,lir,mi,mc,obj}.c`, captured `int rc = ax_pipeline_run(&st, AX_STAGE_TYPECK);` on the `.ax` path and returned `rc` immediately when `rc != AX_EXIT_OK` (matching `emit_thir.c:385-386` and `compiler/driver/pipeline.ax`).
   - **Closure & indirect-call `inspect --emit=obj` parity (16 programs: 15 closure programs + `tests/run/native_p7/qa_fn_ptr.ax`)**:
     - In `bootstrap/axiom0/src/driver/emit_obj.c` (`run_emit_obj`), guarded `item->fn.name.v != 0` before calling `ax_interner_get(&st.interner, item->fn.name)` and formatted `"__ax_fn_%u"` for anonymous closure functions (matching `build.c:505-510` and `lir/lower.c:127`).
     - In `compiler/driver/pipeline.ax` (`driver_emit_objmodel`), changed `if is_build_mode && fname_id_v == 0u32` to `if fname_id_v == 0u32` so anonymous closure functions receive `"__ax_fn_%u"` in both `build` and `inspect --emit=obj`.
     - In `bootstrap/axiom0/src/driver/emit_obj.c` (`encode_mi_to_sec`, `case AX_X64_MI_CALL:`), added `else if (inst->op_count > 0 && inst->ops[0].kind == AX_X64_OP_REG) { ax_x64_call_r(sec, inst->ops[0].reg); }` (matching `build.c:169-171` and `compiler/target/x64/frame.ax:693-695`).

6. **Extended E2E Oracle (`tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py`)**:
   - Extended `check_program` in `tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py` so a program is counted as `equal` only if, in addition to `build -o x.exe`, `build --emit=obj -o x.obj` at `-O0`/`-O1`, and executable run checks, every `inspect --emit=<stage>` in `INSPECT_STAGES` (`tokens`, `ast`, `resolved`, `hir`, `thir`, `mir`, `lir`, `mi`, `mc`, `obj`) has identical exit code, stdout, and stderr between `axiom0` and `axiomc`.
   - Final `AXIOMC-E2E` result across all 539 corpus programs:
     `AXIOMC-E2E programs=539 equal=539 known_divergent=0 built=2132 rejected=20 obj_equal=1068 exe_equal=1064 run_equal=533 images=533 same_behaviour=533`

## Removed Registry Paths
- `tests/selfhost/obj_link_driver/known_divergent.txt` was already emptied in `T153` and remains at `0` entries (comment header only; `0` entries added, `known_divergent=0`).

## Files changed
- bootstrap/axiom0/src/driver/emit_lir.c
- bootstrap/axiom0/src/driver/emit_mc.c
- bootstrap/axiom0/src/driver/emit_mi.c
- bootstrap/axiom0/src/driver/emit_mir.c
- bootstrap/axiom0/src/driver/emit_obj.c
- compiler/driver/pipeline.ax
- compiler/hir/lower.ax
- compiler/mir/builder.ax
- compiler/resolve/resolver.ax
- compiler/types/typeck.ax
- tests/run/parity/diag/cannot_index.ax
- tests/run/parity/diag/cannot_index.test
- tests/run/parity/diag/not_callable.ax
- tests/run/parity/diag/not_callable.test
- tests/run/parity/diag/unreachable_stmt.ax
- tests/run/parity/diag/unreachable_stmt.test
- tests/selfhost/backend/gen_backend_tests.py
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
- tests/selfhost/hir/qa_hir_corpus.ax
- tests/selfhost/hir/qa_hir_desugar_and_drop.ax
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
- tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
- tests/selfhost/opt/qa_opt_pipeline.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax
- tests/selfhost/resolve/qa_resolve_corpus_neg_a.ax
- tests/selfhost/resolve/qa_resolve_corpus_neg_b.ax
- tests/selfhost/resolve/qa_resolve_corpus_neg_c.ax
- tests/selfhost/resolve/qa_resolve_corpus_pos.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_a.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_b.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_c.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_d.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_a.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_b.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_c.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_a.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_b.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_multifile_modules_a.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_multifile_modules_b.ax
- tests/selfhost/traits/qa_traits_solver_mono.ax
- tests/selfhost/typeck/qa_typeck_a.ax
- tests/selfhost/typeck/qa_typeck_b.ax
- tests/selfhost/typeck/qa_typeck_c.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_a.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_b.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_c.ax
- tests/selfhost/verify/qa_verify_pipeline.ax

## Verification
- `cmake --build build-snap-T156/build`: `0` warnings (Clang `-O3`).
- `cmake -S build-snap-T156/bootstrap/axiom0 -B build-snap-T156/build-gcc -G Ninja -DCMAKE_C_COMPILER=gcc && cmake --build build-snap-T156/build-gcc`: `0` warnings (GCC 16.1.0).
- `python tools/archcheck.py`: `archcheck: 192 files scanned, 0 violations`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T156`: `0 REFUSED` lines (95 staged files including `_workspaces/reports/T156-report.md`).
- `python tools/axtest.py --compiler build-snap-T156/build/axiom0.exe -j 1 bundles_current axiomc_e2e`: `WEAK-NATIVE 0`, `TOTAL 35 PASS 35 FAIL 0 SKIP 0 XFAIL 0` (`AXIOMC-E2E programs=539 equal=539 known_divergent=0 built=2132 rejected=20 obj_equal=1068 exe_equal=1064 run_equal=533 images=533 same_behaviour=533`).
- `python tools/axtest.py --compiler build-snap-T156/build/axiom0.exe -j 1`: `WEAK-NATIVE 165`, `TOTAL 2902 PASS 2902 FAIL 0 SKIP 0 XFAIL 0`.

STATUS: COMPLETE round=0
