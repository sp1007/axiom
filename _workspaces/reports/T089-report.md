# T089 Report — E11.1 — Send and Share auto-trait derivation & negative impl solver

## Summary

Implemented the `Send` and `Share` marker auto-traits, automatic structural derivation, positive `unsafe impl` overrides, negative `impl !Send` / `impl !Share` opt-outs, and concurrency bound / safety diagnostics per `spec/SPEC-30-concurrency.md` §2 (`AXS-CONC-010..019`) and §6 (`AXS-CONC-050`, `AXS-CONC-052`):

1. **Standard library marker traits (`std/core/marker.ax`, `std/core/prelude.ax`)**:
   - Created `std/core/marker.ax` declaring `@lang("send") pub unsafe auto trait Send {}` and `@lang("share") pub unsafe auto trait Share {}` (`AXS-CONC-010..011`).
   - Updated `std/core/prelude.ax` documenting that `Send` (`SymbolId { v: 10007 }`) and `Share` (`SymbolId { v: 10008 }`) from `std.core.marker` are pre-populated in prelude scope (`AXS-CONC-010`).

2. **Surface syntax & HIR lowering (`compiler/syntax/ast.ax`, `compiler/syntax/parse.ax`, `compiler/hir/hir.ax`, `compiler/hir/lower.ax`)**:
   - Extended `AstItem` and `HirItem` with `pub is_auto: bool` and `pub is_negative: bool`.
   - Updated `parse_item`, `parse_trait_item`, and `parse_impl_item` in `compiler/syntax/parse.ax` to accept `[unsafe] [auto] trait`, `unsafe impl`, and negative trait implementations `impl[<G>] !Trait for Type {}` (`AXS-CONC-017..018`).
   - Propagated `is_unsafe`, `is_auto`, and `is_negative` on `ITEM_TRAIT` and `ITEM_IMPL` in `lower_item` and `clone_hir_item_shallow` (`compiler/hir/lower.ax`).

3. **Auto-trait structural solver, negative impls, and diagnostics (`compiler/traits/solver.ax`, `compiler/types/typeck.ax`, `compiler/diag/code.ax`)**:
   - Added diagnostic codes `AX_CONC_NOT_SEND` (`134u32`), `AX_CONC_NOT_SHARE` (`135u32`), and `AX_CONC_SAFE_SEND_SHARE_IMPL` (`136u32`) in `compiler/diag/code.ax` and wired human/JSON diagnostic rendering in `compiler/types/typeck.ax`.
   - Implemented `type_satisfies_auto_trait` in `compiler/traits/solver.ax` with coinductive cycle handling, exact `self_type` matching (`type_matches_impl_self_exact`), generic impl bound verification (`impl_bounds_satisfied`), negative `impl !Trait` priority (`AXS-CONC-017`), positive `unsafe impl` overrides (`AXS-CONC-018`), and built-in rules (`AXS-CONC-012..016`, `AXS-CONC-019`):
     - Primitives (`i8..usize`, `bool`, `char`, `str`, `()`, `!`, `fn(...) -> R`): `Send` and `Share`.
     - Raw pointers `*const T` and `*mut T`: `!Send` and `!Share`.
     - `view<T>`: `Send` iff `T: Share`; `Share` iff `T: Share`.
     - `mut_view<T>`: `Send` iff `T: Send`; never `Share`.
     - Arrays `[N]T`, slices `[T]`, tuples, structs, and enums: `Send`/`Share` iff all element/field/variant payload types are `Send`/`Share`.
     - Closures (`TY_CLOSURE`): `Send`/`Share` according to each capture's mode (`CAP_MOVE`/`CAP_COPY` vs `CAP_VIEW` vs `CAP_MUT_VIEW`) and captured type, with capture types resolved in `finalize_types` (`compiler/types/typeck.ax`).
     - Generic type parameters (`TY_PARAM`): satisfied only when the enclosing function or `impl` item's generic bounds or `where` clause (or supertraits thereof) declare `Send` or `Share`.
   - Implemented `check_send_share_impl_safety` emitting `AX_CONC_SAFE_SEND_SHARE_IMPL` (`AXS-CONC-052`) when a positive `impl Send` or `impl Share` (or any `unsafe trait` impl) omits `unsafe`.
   - Implemented `emit_conc_bound_diag` and `find_auto_trait_failure_reason` emitting `AX_CONC_NOT_SEND` / `AX_CONC_NOT_SHARE` (`AXS-CONC-050`) with a secondary `note:` identifying the offending field, enum variant, raw pointer, `view<T>`/`mut_view<T>`, closure capture, unconstrained type parameter, or explicit negative `impl`.

4. **Tests**:
   - Added 4 UI tests in `tests/ui/concurrency/send_share/` covering raw pointers, `view<T>`/`mut_view<T>` rules, structural derivation, negative impls, closures, unconstrained type parameters, and safe `impl Send`/`impl Share` rejection.
   - Added end-to-end execution test `tests/run/concurrency/send_share/auto_derive_and_unsafe_impl.ax` running in both interpreter and native (`-O0` and `-O1`) modes.
   - Extended `tests/selfhost/traits/qa_traits_solver_mono.ax.in` (assertions `67..77`) and regenerated the selfhost test bundles in `T089`'s scope.

## Files changed

- `_workspaces/reports/T089-report.md`
- `compiler/diag/code.ax`
- `compiler/hir/hir.ax`
- `compiler/hir/lower.ax`
- `compiler/syntax/ast.ax`
- `compiler/syntax/parse.ax`
- `compiler/traits/solver.ax`
- `compiler/types/typeck.ax`
- `std/core/marker.ax`
- `std/core/prelude.ax`
- `tests/run/concurrency/send_share/auto_derive_and_unsafe_impl.ax`
- `tests/selfhost/ast/qa_ast_derives.ax`
- `tests/selfhost/ast/qa_ast_exprs_a.ax`
- `tests/selfhost/ast/qa_ast_exprs_b.ax`
- `tests/selfhost/ast/qa_ast_items.ax`
- `tests/selfhost/ast/qa_ast_types_pats.ax`
- `tests/selfhost/cap/qa_own_cap.ax`
- `tests/selfhost/diag/qa_diag_codes.ax`
- `tests/selfhost/diag/qa_diag_emitter.ax`
- `tests/selfhost/diag/qa_diag_format_json.ax`
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
- `tests/selfhost/kernel_source_diag/qa_corpus_differential.ax`
- `tests/selfhost/kernel_source_diag/qa_session_integration.ax`
- `tests/selfhost/mir/qa_mir_builder_and_drop_a.ax`
- `tests/selfhost/mir/qa_mir_builder_and_drop_b.ax`
- `tests/selfhost/mir/qa_mir_builder_and_drop_c.ax`
- `tests/selfhost/mir/qa_mir_text_roundtrip.ax`
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
- `tests/selfhost/traits/qa_traits_solver_mono.ax.in`
- `tests/selfhost/typeck/qa_typeck_a.ax`
- `tests/selfhost/typeck/qa_typeck_b.ax`
- `tests/selfhost/typeck/qa_typeck_c.ax`
- `tests/selfhost/typeck_traits/qa_typeck_traits_a.ax`
- `tests/selfhost/typeck_traits/qa_typeck_traits_b.ax`
- `tests/selfhost/typeck_traits/qa_typeck_traits_c.ax`
- `tests/selfhost/verify/qa_verify_mir.ax`
- `tests/selfhost/verify/qa_verify_pipeline.ax`
- `tests/ui/concurrency/send_share/raw_ptr_not_send_or_share.ax`
- `tests/ui/concurrency/send_share/safe_impl_send_share_rejected.ax`
- `tests/ui/concurrency/send_share/structural_and_negative_impl.ax`
- `tests/ui/concurrency/send_share/view_and_mut_view_bounds.ax`

## Verification

- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T089` -> `snapshot D:\projects\compiler\new lang\build-snap-T089`
- `python tools/build_axiomc.py --out build-snap-T089/build` -> `BUILD-AXIOMC OK: D:\projects\compiler\new lang\build-snap-T089\build\axiomc2.exe (also D:\projects\compiler\new lang\build-snap-T089\build\axiomc.exe) size=10039296 sha256=384cb7fbcf912c19dd3d4af5b549066cb6f819e26131675d670cf486b235362d`
- `python tools/axtest.py --compiler build-snap-T089/build/axiomc.exe --root build-snap-T089 -j 1 --timeout-scale 3 ui/concurrency/send_share run/concurrency/send_share selfhost/traits selfhost/diag selfhost/typeck_traits selfhost/ast selfhost/hir ui/traits run/traits` -> `WEAK-NATIVE 0`, `TOTAL 54 PASS 54 FAIL 0 SKIP 0 XFAIL 0`
- `python tools/archcheck.py` -> `archcheck: 193 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T089` -> `0 REFUSED` lines.

STATUS: COMPLETE round=0
