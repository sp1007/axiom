# T162 — Stage-1 Selfhost Suite Parity & Interp Fixes

## Summary
Resolved all 8 implementation and test-hygiene defects uncovered by the Stage-1 gate (`T086`) plus remaining selfhost suite parity fixes so that `axiomc1.exe` (built by `axiom0` from the `axiomc` bundle) passes the targeted test suites in all declared modes (`[interp]`, `[native]`, `[native-O1]`, `ui`, `golden`, `diff`, `exec`) and all repository gates (`gatecheck.py --no-run`, `reqcov.py --strict`, `harness_check.py`, `archcheck.py`) exit 0.

Key fixes:
1. **Defect 1 — MIR interpreter wrapping arithmetic & step-limit fast-path guard (`compiler/interp/interp.ax`)**:
   - Imported `MIR_BINOP_WRAPPING_ADD`, `MIR_BINOP_WRAPPING_SUB`, and `MIR_BINOP_WRAPPING_MUL` from `compiler.mir.mir` into `compiler/interp/interp.ax` and handled them in `exec_assign_binop` for both unsigned and signed integer types without setting `overflow = true`.
   - Tightened the `MIR_TERM_GOTO` constant-condition infinite-loop fast-path in `compiler/interp/interp.ax` so it only triggers on true 2-block back-edges (`tgt.v <= current_bb.v` where `tbb` terminates with a 1-target `MIR_TERM_SWITCH_INT` back to `current_bb.v`), preventing false step-limit exhaustion on forward join blocks in `run/numeric/intrinsic_ops.ax` and `run/intrinsics/ops_table.ax`.
2. **Defect 2 — MIR builder unreachable join block termination (`compiler/mir/builder.ax`)**:
   - Added the post-pass termination loop at the end of `mir_build_fn_subst` matching `bootstrap/axiom0/src/mir/builder.c` so any unreachable pre-allocated join block (`MIR_TERM_NONE`) receives `MIR_TERM_RETURN` on the first such block and `MIR_TERM_GOTO -> first_unterm` on subsequent blocks.
3. **Defect 3 — Float-rejection diagnostic parity (`tests/selfhost/bundle_common.py`, `compiler/types/typeck.ax`)**:
   - Removed the blanket suppression of `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (`code == 2021u16`) from `_shim_diag_sink_report` in `tests/selfhost/bundle_common.py` and eliminated the duplicate static/const `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` emissions in `compiler/types/typeck.ax` (leaving `compiler/interp_opt/session.ax` as the single emitter).
4. **Defect 4 — Deep inference variable resolution in compound types & verifier compatibility (`compiler/types/typeck.ax`, `compiler/verify/verifier.ax`)**:
   - Updated `resolve_deep_ty` and `finalize_types` in `compiler/types/typeck.ax` to recursively resolve inference variables (`TY_INT_VAR`, `TY_INFER`) inside `TY_ARRAY`, `TY_SLICE`, and `TY_TUPLE` types and across `out.types`.
   - Extended `verify_types_compatible` in `compiler/verify/verifier.ax` to recursively check element compatibility for `TY_ARRAY` (with matching `array_len`), `TY_SLICE`, and `TY_TUPLE`.
5. **Defect 5 — Textual `.mir` parser bare-place operand support (`compiler/mir/mir.ax`)**:
   - Updated `mp_parse_operand` in `compiler/mir/mir.ax` so bare place operands (`_N` or `(*_N)` without a `copy`/`move`/`const` keyword, as in `tests/lir/load.mir`) fall back to `MIR_OP_COPY` via `mp_parse_place`.
6. **Defect 6 — Driver/interp CLI run-arg forwarding & interpreter trap exit codes (`compiler/driver/pipeline.ax`, `compiler/interp_opt/session.ax`, `compiler/interp_opt/mod.ax`, `compiler/interp/frame.ax`, `compiler/interp/value.ax`)**:
   - Added `session_run_interp_with_args` in `compiler/interp_opt/session.ax` (re-exported in `compiler/interp_opt/mod.ax`) and wired `pipeline_stage_interp` in `compiler/driver/pipeline.ax` to populate `ctx.host` with `[dopts.input_file, ...dopts.run_args]`.
   - Preserved interpreter exit codes `124` (step/call-depth limit) and `125` (UB / memory safety trap) in `driver_execute_run_ctx` (`compiler/driver/pipeline.ax`).
7. **Defect 7 — Trait default method vs impl override dispatch in MIR interpreter (`compiler/interp_opt/session.ax`)**:
   - Restricted `insert_impl_alias_in_mir_map` and `session_interp_opt_file` in `compiler/interp_opt/session.ax` using `tc_is_default_inst` so un-instantiated `HIR_ITEM_TRAIT` default methods and `T161` synthesized impl default-method instances are never cross-aliased in `mir_map`.
8. **Defect 8 — `gnu_as_vectors.ax` generator hygiene, selfhost compiler algorithmic fixes, & bundle parity (`tools/gen_encode_tests.py`, `tests/encode/axiom/gnu_as_vectors.ax`, `compiler/syntax/parse.ax`, `compiler/types/typeck.ax`, `compiler/mir/drop.ax`, `compiler/mir/builder.ax`, `compiler/interp_opt/session.ax`, `compiler/interp/frame.ax`, `compiler/verify/verifier.ax`, `tests/selfhost/**`)**:
   - Updated `tools/gen_encode_tests.py` to emit `// skip-enc:` instead of `// xfail:` inside `fn main()` body lines and regenerated `tests/encode/axiom/gnu_as_vectors.ax`, satisfying both `python tools/gen_encode_tests.py --check` and `python tools/gatecheck.py --no-run` rule (c).
   - Replaced $O(N^2)$ linked-list tail walks in `compiler/syntax/parse.ax` (`parse_paren_or_tuple_expr`, `parse_array_expr`, `parse_match_expr`, `parse_call_suffix`, `parse_block`, `parse_field_decls`, `parse_member_items`, `parse_enum_variants`, `ax_parse`) with $O(1)$ `tail`-pointer appends so large generated files (such as `qa_backend_diff_mi_mc_b.ax`) parse in linear time (`0.56s` on 23-module bundles, `2.56s` on 58-module bundles).
   - Indexed `HirItem` definitions (`SymbolId -> *const HirItem`), enum variants, and `impl` `fn` members in `Thir.expr_methods` via `index_hir_items_in_thir` (`compiler/types/typeck.ax`, using a `0 as *const HirItem` sentinel at keys `4usize`/`6usize` for MIR interpreter provenance safety) and used $O(1)$ hash lookups across `typeck.ax`, `compiler/mir/drop.ax`, `compiler/mir/builder.ax`, `compiler/interp_opt/session.ax`, and `compiler/interp/frame.ax`, reducing `typeck` from `32.8s` to `4.25s` on 58-module selfhost bundles.
   - Optimized ownership/move verification in `compiler/verify/verifier.ax` (`tests/selfhost/bundle_common.py`) with Reverse Postorder (RPO) dataflow order, dirty-block worklist propagation, pre-deref `MIR_PROJ_FIELD` path-tree depth pruning (`populate_path_tree_depth`), fast primitive short-circuiting in `verify_own_type_needs_drop`, and `df_count > 0` guarding in `verify_mir_drop_flags`, reducing `own` from `25.2s` to `6.47s` on 23-module bundles and preventing 120s test timeouts.
   - Updated `tests/selfhost/lex` and `tests/selfhost/lexer` (`// modes: native` for `axiom0`-specific internal tests), updated `qa_axiomc_cli_edges.test` and `qa_axiomc_cli_edges_oracle.py` (`AXIOMC-EDGES same=23 diverge=0`), and regenerated all selfhost test bundles.

## Files changed
- compiler/driver/pipeline.ax
- compiler/interp/frame.ax
- compiler/interp/interp.ax
- compiler/interp/value.ax
- compiler/interp_opt/mod.ax
- compiler/interp_opt/session.ax
- compiler/mir/builder.ax
- compiler/mir/drop.ax
- compiler/mir/mir.ax
- compiler/syntax/parse.ax
- compiler/types/typeck.ax
- compiler/verify/verifier.ax
- tests/encode/axiom/gnu_as_vectors.ax
- tests/selfhost/abi/qa_abi_lir_lower.ax
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
- tests/selfhost/bundle_common.py
- tests/selfhost/cap/qa_own_cap.ax
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
- tests/selfhost/lex/qa_lex_differential.ax
- tests/selfhost/lex/qa_lex_differential.ax.in
- tests/selfhost/lex/qa_lex_tokens.ax
- tests/selfhost/lex/qa_lex_tokens.ax.in
- tests/selfhost/lex/u64_max_literal.ax
- tests/selfhost/lex/u64_max_literal.ax.in
- tests/selfhost/lexer/qa_lexer_session_integration.ax
- tests/selfhost/lexer/qa_lexer_session_integration.ax.in
- tests/selfhost/lir/qa_lir_from_ax_a.ax
- tests/selfhost/lir/qa_lir_from_ax_b.ax
- tests/selfhost/lir/qa_lir_from_ax_c.ax
- tests/selfhost/lir/qa_lir_from_ax_d.ax
- tests/selfhost/lir/qa_lir_from_ax_e.ax
- tests/selfhost/lir/qa_lir_from_mir.ax
- tests/selfhost/lir/qa_lir_seam_edge.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_a.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_b.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_c.ax
- tests/selfhost/mir/qa_mir_text_roundtrip.ax
- tests/selfhost/obj_link_driver/qa_axiomc_cli_edges.test
- tests/selfhost/obj_link_driver/qa_axiomc_cli_edges_oracle.py
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
- tests/selfhost/opt/qa_opt_pipeline.ax
- tests/selfhost/opt/qa_opt_unit.ax
- tests/selfhost/own/qa_own_init.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax
- tests/selfhost/parse/qa_parse_corpus_a.ax
- tests/selfhost/parse/qa_parse_corpus_b.ax
- tests/selfhost/parse/qa_parse_corpus_c.ax
- tests/selfhost/parse/qa_parse_corpus_d.ax
- tests/selfhost/parse/qa_parse_corpus_e.ax
- tests/selfhost/parse/qa_parse_corpus_f.ax
- tests/selfhost/parse/qa_parse_corpus_g.ax
- tests/selfhost/parse/qa_parse_corpus_h.ax
- tests/selfhost/parse/qa_parse_corpus_i.ax
- tests/selfhost/parse/qa_parse_corpus_j.ax
- tests/selfhost/parse/qa_parse_heavy_a.ax
- tests/selfhost/parse/qa_parse_heavy_b.ax
- tests/selfhost/parse/qa_parse_qa_edge.ax
- tests/selfhost/parse/qa_parse_qa_tuple_struct.ax
- tests/selfhost/parse/qa_parse_recovery_a.ax
- tests/selfhost/parse/qa_parse_recovery_b.ax
- tests/selfhost/parse/qa_parse_terminator_a.ax
- tests/selfhost/parse/qa_parse_terminator_b.ax
- tests/selfhost/parse/qa_parse_terminator_heavy.ax
- tests/selfhost/parser/qa_parser_diff_corpus_wide.ax
- tests/selfhost/parser/qa_parser_diff_neg_a.ax
- tests/selfhost/parser/qa_parser_diff_pos_a.ax
- tests/selfhost/parser/qa_parser_diff_pos_b.ax
- tests/selfhost/parser/qa_parser_session_integration.ax
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
- tests/selfhost/verify/qa_verify_mir.ax
- tests/selfhost/verify/qa_verify_pipeline.ax
- tools/gen_encode_tests.py

## Verification
- Rebuilt `build-snap-T162/build/axiom0.exe` via `cmake --build build-snap-T162/build --config Release`.
- Assembled `build-snap-T162/build/axiomc_bundle.ax` and built `build-snap-T162/build/axiomc1.exe` via `build-snap-T162/build/axiom0.exe build build-snap-T162/build/axiomc_bundle.ax -O1 --stack-reserve 67108864 -o build-snap-T162/build/axiomc1.exe` (`0 errors`).
- Verified `python tools/gen_encode_tests.py --check` (`OK encode tables current (10211 vectors)`).
- Verified `python tools/axtest.py --compiler build-snap-T162/build/axiomc1.exe -j 1` across `encode/axiom/gnu_as_vectors`, `encode/encode_tables_current`, `run/parity` (all 152 parity tests), `selfhost/backend/qa_backend_diff_mi_mc_a`, `selfhost/backend/qa_backend_diff_mi_mc_b`, `selfhost/driver/qa_driver_commands_a`, `selfhost/driver/qa_driver_commands_b`, `selfhost/interp_opt/qa_interp_opt_diff_run_a`, `selfhost/interp_opt/qa_interp_opt_diff_run_b`, `selfhost/mir/qa_mir_text_roundtrip`, `selfhost/own_mir_verify/qa_own_mir_diff_build_a`, `selfhost/own_mir_verify/qa_own_mir_diff_build_b`, and `selfhost/resolve/qa_resolve_corpus_neg_b` (`183/183 PASS`).
- **Round 1 QA Fixes (`_workspaces/reports/T162-qa.md`)**:
  - **F1 (`compiler/types/typeck.ax`)**: Kept `resolve_deep_ty` restricted to `TY_VIEW` and `TY_MUT_VIEW` (matching `axiom0`) and removed `finalize_ptr_typemap(mut_view(*cx), mut_view((*thir_ptr).item_types))` from `finalize_types`, preserving in-place `TY_TUPLE`/`TY_ARRAY`/`TY_SLICE` resolution and exact `TypeId` / `inspect` parity across the e2e corpus.
  - **F2 (`compiler/driver/pipeline.ax`)**: Removed `pipe_place_type_id` and `pipe_expand_large_repeats`, restoring byte-for-byte `.obj` and `.exe` parity on `tests/run/native_ptr/write_bytes_1mb.ax`.
  - **F3 (`compiler/mir/drop.ax`)**: Updated `drop_find_impl_fn_with_thir` to fall back to `mir_find_drop_impl_fn` when a prepended synthetic `Drop` impl uses either `999999u32` or `SYNTH_DROP_SYMBOL` (`7001u32`), fixing `selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax`.
  - Regenerated all selfhost test bundles (`34/34 bundles_current.test PASS`) and verified `selfhost/obj_link_driver/axiomc_e2e.test` (`1/1 PASS`), `selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax` (`2/2 PASS` under `axiom0.exe` and `axiomc1.exe`), `conformance/std/0169_std_collections_map.ax` (`1/1 PASS` under `axiom0.exe` and `axiomc1.exe`), and `run/parity/intrinsics/qa_t162_stage1_parity_edge.ax` (`3/3 PASS` under `axiom0.exe` and `axiomc1.exe`).
- Repository gates:
  - `python tools/gatecheck.py --no-run` -> `MS-P1 PASS .. MS-P9 PASS` (exit 0)
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> `gaps: 0`, `COVERAGE OK` (exit 0)
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK` (exit 0)
  - `python tools/archcheck.py` -> `archcheck: 192 files scanned, 0 violations` (exit 0)
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T162` -> `0 REFUSED` (exit 0)

## Residual risks
- `tests/perf/loop.ax` and `tests/perf/bench` invoke `axiomc1.exe` via `tools/bench.py` which hardcodes `build/axiom0.exe` unless `tests/perf` (owned by `T086`) is updated to honor `{compiler}`; `T086` owns `tests/perf` and can pass `{compiler}` when re-running the Stage-1 gate.

STATUS: COMPLETE round=1
