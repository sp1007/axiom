# T434 Report — Baseline fix: derive-generated items leak into root-file dumps

## Summary & Root Cause
- **Confirmed root cause**: In `compiler/syntax/parse.ax`, `parse_synthetic_item` previously called `ax_lex_into(FileId { v: 0u32 }, text, ...)` when re-parsing `@derive(...)`-generated `impl` items.
- Because the generated `ItemImpl` items carried `span.file.v == 0u32`, all four dump renderers (`d_item` in `compiler/syntax/ast.ax`, `rd_item` in `compiler/resolve/resolver.ax`, `hd_item` in `compiler/hir/hir.ax`, and `td_item` in `compiler/types/typeck.ax`) skipped the `f_id != 0u32 && f_id != st.filter_file.v` filter for those items.
- Consequently, the two `@derive(Copy)` items (`Ordering` and `CasResult`) added to `std/core/prelude.ax` by T406 leaked into every root-file `--emit=ast`, `--emit=resolved`, `--emit=hir`, and `--emit=thir` dump.

## Fix
- Updated `parse_synthetic_item` and `expand_derives` in `compiler/syntax/parse.ax` to pass the `@derive` argument's `Span` (falling back to `(*item).span` if `file.v == 0u32`) into `ax_lex_into(FileId { v: source_span.file.v }, ...)` and collapse synthesized token offsets to a zero-length span `(source_span.file.v, source_span.start, source_span.start)` at the `@derive` site.
- Linking synthesized items immediately after the originating `item` via `link_item(item, synthetic_item)` preserves module attribution (`env.current_module` in `compiler/resolve/resolver.ax` and `current_mod` in `compiler/hir/lower.ax`), while `span.file.v == source_span.file.v` ensures all four dump renderers (`ast`, `resolved`, `hir`, `thir`) filter/include derived items strictly by the originating `FileId`.
- Collapsing token offsets to `source_span.start..source_span.start` prevents downstream `source_db_span_text` callers (`compiler/types/exhaust.ax`, `compiler/types/typeck.ax`, `compiler/mir/builder.ax`, `compiler/backend/session.ax`) from slicing synthetic byte offsets out of the real source file, and maps diagnostics on derived impls to the `@derive(...)` attribute location.

## Golden Adjustment (Unrelated to Keeping Leak)
- `tests/parse/async/async_fn_and_await.ast` (added in commit `abb00124` under T416, after T406) had accidentally captured the 12-line std prelude leak (`Ordering` and `CasResult` `impl Copy` items) at the bottom of the file even though `tests/parse/async/async_fn_and_await.ax` has no `@derive` attributes and no `Ordering`/`CasResult` declarations.
- Removed those 12 leaked lines so `tests/parse/async/async_fn_and_await.ast` matches `tests/parse/async/async_fn_and_await.ax` per `spec/SPEC-02-grammar.md` / `ADR-0041 §2 D1`:
```diff
-(ItemImpl
-  (Vis priv)
-  (TypePath
-    (PathSegment "Copy"))
-  (TypePath
-    (PathSegment "Ordering")))
-(ItemImpl
-  (Vis priv)
-  (TypePath
-    (PathSegment "Copy"))
-  (TypePath
-    (PathSegment "CasResult")))
```
- None of the 41 T434 goldens were modified.

## Regression Test & Baseline Cleanup
- Added `tests/parse/derive_local_only.ax` and `tests/parse/derive_local_only.ast`: root file uses `@derive(Copy, Eq)` on a struct and `@derive(Copy)` on an enum, verifying the AST dump includes its own derived `ItemImpl`s and none from `std/core/prelude.ax`.
- Removed all 41 `T434` entries from `_workspaces/baseline-failures.txt`.
- Regenerated all affected selfhost bundles using their `tests/selfhost/**/gen_*.py` scripts and verified zero `DIFFERS` and exit 0 across every `gen_*.py --check`.

## Build & Verification (`build-snap-T434`, `-j 1`)
- **Stage-1**: `axiomc1.exe` (`25878528` bytes, `sha256=0d35432094093c9c2544f6837781a14dae0d9466b180c9f6be25336855996ad1`); `parse/`, `resolve/`, `hir/`, `typeck/basic.ax`, `typeck/generic/generic_subst.ax`, and all `bundles_current.test`: `TOTAL 75 PASS 75 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- **Stage-2 (`--stage 2 --force`, O1)**: `axiomc2.exe` (`8015360` bytes, `sha256=c91508f93adf2a1dcb191e1ea9b418dac88f6d60883442adc850822a6e0cad37`, copied to `build/`).
- **Stage-2 test runs (`-j 1`, `--exclude-requires axiom0-internal`, `--baseline _workspaces/baseline-failures.txt`)**:
  - `parse/`, `resolve/`, `hir/`, `typeck/`, and all `bundles_current.test` (87 IDs): `TOTAL 87 PASS 85 FAIL 2 SKIP 0 XFAIL 0`, `BASELINE OK`, `WEAK-NATIVE 0`. All 41 `T434` IDs, `parse/derive_local_only.ax`, `parse/async/async_fn_and_await.ax`, and all 31 `bundles_current.test` passed; the only 2 failures (`typeck/async/async_basic_pos.ax` for `T432`, `typeck/int128/int128_literals_and_methods.test` for `T433`) are pre-existing baseline failures.
  - `ui/parse/`, `ui/resolve/`, `ui/hir/`, and `conformance/adversarial/parse_derive*` (43 IDs): `TOTAL 43 PASS 43 FAIL 0 SKIP 0 XFAIL 0`, `BASELINE OK`, `WEAK-NATIVE 0`.
  - Direct inspection of `tests/parse/derive_local_only.ax` via `axiomc2.exe inspect --emit=resolved|hir` confirmed only local items and their derived `ItemImpl`s appear, and diagnostics point to `derive_local_only.ax:4:15`.
- **Checks**:
  - `python tools/archcheck.py`: `archcheck: 229 files scanned, 0 violations`
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py validate`: `OK (694 tasks)`
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`

## Files changed
- _workspaces/baseline-failures.txt
- compiler/syntax/parse.ax
- tests/parse/async/async_fn_and_await.ast
- tests/parse/derive_local_only.ast
- tests/parse/derive_local_only.ax
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
- tests/selfhost/verify/qa_verify_pipeline.ax

STATUS: COMPLETE round=0
