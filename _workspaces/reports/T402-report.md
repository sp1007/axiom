# T402 Report - E11.1 Compile-time Data-Race & Shared-Mutable-State Verifier

## Summary

Implemented the compile-time data-race and shared-mutable-state verifier (`E11.1`, `spec/SPEC-30-concurrency.md` sections 1-6, `0126` sections 47-50, `ACONCUR-150..198`):

1. **Diagnostic Codes & Formatting (`compiler/diag/code.ax`, `compiler/diag/format.ax`)**:
   - Added `AX_CONC_SHARED_MUT = 145u32`, `AX_CONC_VIEW_NOT_SHARE = 146u32`, `AX_CONC_UNSYNC_STATIC = 147u32`, `AX_CONC_GUARD_ESCAPE = 148u32`, and `AX_CONC_ATOMIC_MUT_VIEW = 149u32` with diagnostic code names, default messages, and `diag_buf_push_code_name` rendering.

2. **Disjoint Borrow & Constant/Split Slice Region Proofs (`compiler/own/cap.ax`, `compiler/verify/verifier.ax`)**:
   - Extended `own_region_relate_in_body` (`compiler/own/cap.ax`) and `verify_region_relate_in_body` (`compiler/verify/verifier.ax`) with MIR constant `usize` resolution (`cap_resolve_const_usize`, `verify_resolve_const_usize`) and root-local origin resolution (`cap_resolve_root_local`) across `subslice` (`MIR_RV_SUBSLICE`) and `IndexSlice` (`MIR_PROJ_SLICE`) projections.
   - Proves disjointness (`OWN_REGION_DISJOINT`) for non-overlapping constant sub-slices (`[a..b]` vs `[c..d]` where `b <= c` or `d <= a`) and complementary split sub-slices (`[..mid]` vs `[mid..]`), while conservatively treating unknown/runtime indices as `OWN_REGION_UNKNOWN` (which never suppresses conflict errors).
   - Added `cap_is_inline_call_arg_closure` so disjoint borrows captured across sibling closure arguments of structured-concurrency join calls (`scope.join`, `par_join`, `join`) are delegated to the concurrency verifier without false sequential double-borrow alarms.

3. **Compile-Time Concurrency & Data-Race Verifier (`compiler/own/unsafe.ax`)**:
   - Implemented `conc_verify_body`, `conc_check_call_concurrency`, `conc_type_is_share`, `conc_extract_region`, and `conc_region_relate` integrated into `unsafe_verify_body`:
     - **Shared Read (`view<T>`) Across Concurrent Contexts**: Permitted only when `T: Share`; emits `AX_CONC_VIEW_NOT_SHARE` with structured `conflict:` and `help:` notes when `T` contains unsynchronized interior mutability (`Cell`, `RefCell`, `UnsafeCell`, raw pointers) or an explicit negative `impl !Share for T`.
     - **Concurrent `READ/WRITE` and `WRITE/WRITE` Conflicts**: Rejects overlapping or `UNKNOWN`-overlap places (`SAME`, `PREFIX`, `CONTAINS`, `UNKNOWN`) across concurrent branches (`spawn`, `scope.spawn`, `par_join`/`join`, and sequentially spawned handles live before `.join()`), emitting `AX_CONC_SHARED_MUT` with place, region, and execution-domain notes.
     - **Disjoint Struct Fields & Constant/Split Sub-Slices**: Permits concurrent `mut_view` captures of provably disjoint struct fields (`p.a` vs `p.b`) and provably disjoint slice sub-ranges (`s[0..2]` vs `s[2..4]`, `s[..mid]` vs `s[mid..]`).
     - **Global Static Memory & `unsafe` Re-entry**: Rejects access to mutable static globals outside `unsafe` (`AX_CONC_UNSYNC_STATIC`) unless wrapped in `Mutex<T>`, `RwLock<T>`, or `Atomic*`. Tracks regions derived from `unsafe` globals or raw pointers (`from_unsafe_static`, `from_unsafe`) so that re-wrapping them into safe `view<T>` / `mut_view<T>` capabilities does not disable concurrency checks when shared across threads.
     - **Synchronization Wrapper Discipline**: Rejects `MutexGuard` / `RwLockReadGuard` / `RwLockWriteGuard` escaping across thread spawns (`AX_CONC_GUARD_ESCAPE`) and rejects creating `mut_view` into `Atomic*` storage (`AX_CONC_ATOMIC_MUT_VIEW`).

## Files changed
- `compiler/diag/code.ax`
- `compiler/diag/format.ax`
- `compiler/own/cap.ax`
- `compiler/own/unsafe.ax`
- `compiler/verify/verifier.ax`
- `tests/run/concurrency/disjoint/`
- `tests/selfhost/abi/qa_abi_boundary_seam.ax`
- `tests/selfhost/abi/qa_abi_lir_lower.ax`
- `tests/selfhost/abi/qa_abi_win64_classify.ax`
- `tests/selfhost/ast/qa_ast_derives.ax`
- `tests/selfhost/ast/qa_ast_exprs_a.ax`
- `tests/selfhost/ast/qa_ast_exprs_b.ax`
- `tests/selfhost/ast/qa_ast_items.ax`
- `tests/selfhost/ast/qa_ast_types_pats.ax`
- `tests/selfhost/backend/qa_backend_diff_lir_a.ax`
- `tests/selfhost/backend/qa_backend_diff_lir_b.ax`
- `tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax`
- `tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax`
- `tests/selfhost/backend/qa_backend_edge.ax`
- `tests/selfhost/backend/qa_backend_unit.ax`
- `tests/selfhost/cap/qa_own_cap.ax`
- `tests/selfhost/diag/qa_diag_codes.ax`
- `tests/selfhost/diag/qa_diag_emitter.ax`
- `tests/selfhost/diag/qa_diag_format_json.ax`
- `tests/selfhost/driver/qa_driver_boundary_edges.ax`
- `tests/selfhost/driver/qa_driver_cli_and_project.ax`
- `tests/selfhost/driver/qa_driver_commands_a.ax`
- `tests/selfhost/driver/qa_driver_commands_b.ax`
- `tests/selfhost/driver/qa_driver_inspect_diff_a.ax`
- `tests/selfhost/driver/qa_driver_inspect_diff_b.ax`
- `tests/selfhost/drop/qa_drop_d01.ax`
- `tests/selfhost/drop/qa_drop_d02.ax`
- `tests/selfhost/drop/qa_drop_d03.ax`
- `tests/selfhost/drop/qa_drop_d04.ax`
- `tests/selfhost/drop/qa_drop_d05.ax`
- `tests/selfhost/drop/qa_drop_d06.ax`
- `tests/selfhost/drop/qa_drop_d07.ax`
- `tests/selfhost/drop/qa_drop_d09.ax`
- `tests/selfhost/drop/qa_drop_d10.ax`
- `tests/selfhost/drop/qa_drop_d11.ax`
- `tests/selfhost/drop/qa_drop_d12.ax`
- `tests/selfhost/hir/qa_hir_corpus.ax`
- `tests/selfhost/hir/qa_hir_desugar_and_drop.ax`
- `tests/selfhost/interp/qa_interp_exec_a.ax`
- `tests/selfhost/interp/qa_interp_exec_b.ax`
- `tests/selfhost/interp/qa_interp_unit.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_unit.ax`
- `tests/selfhost/isel/qa_frame_layout_and_verify.ax`
- `tests/selfhost/isel/qa_isel_diff_golden.ax`
- `tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax`
- `tests/selfhost/isel/qa_isel_instructions_and_abi.ax`
- `tests/selfhost/kernel_source_diag/qa_corpus_differential.ax`
- `tests/selfhost/kernel_source_diag/qa_session_integration.ax`
- `tests/selfhost/lex/qa_lex_differential.ax`
- `tests/selfhost/lex/qa_lex_tokens.ax`
- `tests/selfhost/lex/u64_max_literal.ax`
- `tests/selfhost/lexer/qa_lexer_corpus_neg_a.ax`
- `tests/selfhost/lexer/qa_lexer_corpus_neg_b.ax`
- `tests/selfhost/lexer/qa_lexer_corpus_pos_a.ax`
- `tests/selfhost/lexer/qa_lexer_corpus_pos_b.ax`
- `tests/selfhost/lexer/qa_lexer_session_integration.ax`
- `tests/selfhost/link/qa_pe_headers_and_imports.ax`
- `tests/selfhost/link/qa_pe_linker_diff.ax`
- `tests/selfhost/link/qa_pe_local_symbols.ax`
- `tests/selfhost/lir/qa_lir_from_ax_a.ax`
- `tests/selfhost/lir/qa_lir_from_ax_b.ax`
- `tests/selfhost/lir/qa_lir_from_ax_c.ax`
- `tests/selfhost/lir/qa_lir_from_ax_d.ax`
- `tests/selfhost/lir/qa_lir_from_ax_e.ax`
- `tests/selfhost/lir/qa_lir_from_mir.ax`
- `tests/selfhost/lir/qa_lir_seam_edge.ax`
- `tests/selfhost/mir/qa_mir_builder_and_drop_a.ax`
- `tests/selfhost/mir/qa_mir_builder_and_drop_b.ax`
- `tests/selfhost/mir/qa_mir_builder_and_drop_c.ax`
- `tests/selfhost/mir/qa_mir_text_roundtrip.ax`
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax`
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax`
- `tests/selfhost/opt/qa_opt_pipeline.ax`
- `tests/selfhost/opt/qa_opt_unit.ax`
- `tests/selfhost/own/qa_own_init.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax`
- `tests/selfhost/parse/qa_parse_corpus_a.ax`
- `tests/selfhost/parse/qa_parse_corpus_b.ax`
- `tests/selfhost/parse/qa_parse_corpus_c.ax`
- `tests/selfhost/parse/qa_parse_corpus_d.ax`
- `tests/selfhost/parse/qa_parse_corpus_e.ax`
- `tests/selfhost/parse/qa_parse_corpus_f.ax`
- `tests/selfhost/parse/qa_parse_corpus_g.ax`
- `tests/selfhost/parse/qa_parse_corpus_h.ax`
- `tests/selfhost/parse/qa_parse_corpus_i.ax`
- `tests/selfhost/parse/qa_parse_corpus_j.ax`
- `tests/selfhost/parse/qa_parse_heavy_a.ax`
- `tests/selfhost/parse/qa_parse_heavy_b.ax`
- `tests/selfhost/parse/qa_parse_qa_edge.ax`
- `tests/selfhost/parse/qa_parse_qa_tuple_struct.ax`
- `tests/selfhost/parse/qa_parse_recovery_a.ax`
- `tests/selfhost/parse/qa_parse_recovery_b.ax`
- `tests/selfhost/parse/qa_parse_terminator_a.ax`
- `tests/selfhost/parse/qa_parse_terminator_b.ax`
- `tests/selfhost/parse/qa_parse_terminator_heavy.ax`
- `tests/selfhost/parser/qa_parser_diff_corpus_wide.ax`
- `tests/selfhost/parser/qa_parser_diff_neg_a.ax`
- `tests/selfhost/parser/qa_parser_diff_pos_a.ax`
- `tests/selfhost/parser/qa_parser_diff_pos_b.ax`
- `tests/selfhost/parser/qa_parser_session_integration.ax`
- `tests/selfhost/resolve/qa_resolve_corpus_neg_a.ax`
- `tests/selfhost/resolve/qa_resolve_corpus_neg_b.ax`
- `tests/selfhost/resolve/qa_resolve_corpus_neg_c.ax`
- `tests/selfhost/resolve/qa_resolve_corpus_pos.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_a.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_b.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_c.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_d.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_a.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_b.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_c.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_a.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_b.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_multifile_modules_a.ax`
- `tests/selfhost/resolve_hir/qa_resolve_hir_multifile_modules_b.ax`
- `tests/selfhost/traits/qa_traits_solver_mono.ax`
- `tests/selfhost/typeck/qa_typeck_a.ax`
- `tests/selfhost/typeck/qa_typeck_b.ax`
- `tests/selfhost/typeck/qa_typeck_c.ax`
- `tests/selfhost/typeck_traits/qa_typeck_traits_a.ax`
- `tests/selfhost/typeck_traits/qa_typeck_traits_b.ax`
- `tests/selfhost/typeck_traits/qa_typeck_traits_c.ax`
- `tests/selfhost/types/qa_types_exhaust.ax`
- `tests/selfhost/types/qa_types_layout.ax`
- `tests/selfhost/verify/qa_verify_mir.ax`
- `tests/selfhost/verify/qa_verify_pipeline.ax`
- `tests/ui/concurrency/data_race/`

## Verification

- `build-snap-T402/build/axiomc2.exe`: Stage-1 and Stage-2 self-host build succeeded (`BUILD-AXIOMC OK`, `size=6614016`, `sha256=7b92aaa3416b5cb88b8563d58b6e821b763b97988e6d263470fb04f1566eac5b`).
- `ui/concurrency/data_race` (4 tests) and `run/concurrency/disjoint` (2 tests): 6/6 PASS.
- `ui/concurrency/spawn_capture`, `run/concurrency/spawn_capture`, `ui/concurrency/send_share`, `run/concurrency/send_share`: 24/24 PASS.
- `conformance/p15/e15_2_alias_escape`, `selfhost/diag`, `selfhost/cap`, `selfhost/own`, `selfhost/verify`, `run/intrinsics/assert_false.ax`, `run/intrinsics/panic_abort.ax`, `ui/intrinsics/unknown_intrinsic.ax`: 77/77 PASS.
- `python tools/archcheck.py`: 0 violations.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.

STATUS: COMPLETE round=0
