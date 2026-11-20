# T488 report

## Summary
Merged all selfhost bundles that share an identical `(area, module_closure, modes)` triple so each shared module closure is compiled once instead of once per split file, while preserving 100% of assertions, `interp` vs `modes: native` coverage, and per-area affected-set mapping (`tools/affected_map.txt`).

### Key design choices (`spec/SPEC-20-selfhost.md`, `REQ-TST-072`)
1. **Step 1 compile-time measurement first** (on `build-snap-T488/build/axiomc2.exe`, built on post-T486+T493 HEAD with `--time-passes`, comparing `tests/selfhost/lir/qa_lir_from_ax_{a..e}.ax` separately vs 5-way merged):
   - **-O0 build:** separate sum `165.94 s` (run `7.25 s`) vs merged `35.40 s` (run `2.08 s`) → **ratio = `0.213`** (4.69× faster; threshold `<= 0.600`).
   - **-O1 build:** separate sum `186.03 s` (run `7.24 s`) vs merged `40.35 s` (run `2.71 s`) → **ratio = `0.217`** (4.61× faster; threshold `<= 0.600`).
   - **interp run:** merged passed `rc=0` in `115.50 s` (frontend `8.8 s` + run `106.4 s`), zero extra warnings.
2. **Module-isolated merge groups in `tests/selfhost/bundle_common.py`**:
   - Added `MergeGroup`, `split_header_and_body`, `assemble_merged_group`, `assemble_merged_template_bundle`, and extended `run_template_generator` to support `MergeGroup` alongside singletons.
   - Each merged member's original `module main` (or `module selfhost_*`) is placed verbatim in its own isolated `module __case_<orig_stem>` with `main` renamed to `pub fn __t488_run() -> i32`, avoiding all helper/const/struct name collisions with zero regex renaming of test internals.
   - A thin generated `module main` calls every `__case_<orig_stem>.__t488_run()` in order, prints `OK <orig_stem>\n` (or `FAIL <orig_stem>\n` on non-zero return), **continues after a failure**, and returns `0` iff every member returned `0`.
   - All original `// stdout:` lines of every member are concatenated in order with `// stdout: OK <orig_stem>\n` right after each member, preserving exact byte-for-byte stdout checking and `WEAK-NATIVE = 0`.
   - Added `extract_module_slice`, `extract_const_block_from_member`, `extract_blobs_from_member`, and `extract_ints_from_member` so golden-extracting custom generators (`backend`, `driver`, `interp_opt`, `own_mir_verify`) read goldens deterministically from `module __case_<orig_stem>` inside the merged bundle (falling back to the legacy split `.ax` path during the initial snapshot/accept migration).
   - Converted `tests/selfhost/interp/gen_interp_tests.py`'s `qa_check` from aborting `assert(false)` into a non-aborting failure counter (`__qa_check_cnt`) without modifying any assertion in `unit_main.ax.in` / `exec_a_main.ax.in` / `exec_b_main.ax.in`, so sibling members still execute after a failure.
3. **Scope of merge (152 → 58 selfhost bundles; 94 full compiles eliminated)**:
   - **31 merge groups** across 24 areas collapse **125 split bundles → 31 merged bundles** (27 distinct singletons remain untouched).
   - Total generated files in `tests/selfhost/generated-files.txt`: **154 → 60** (`bundles.py regen` wall time: `96 s` → `28 s`, 3.4× faster).
   - Updated the 3 selfhost oracle tests that referenced split bundle filenames (`qa_t441_hermetic_prelude_mir_bounds_oracle.py`, `qa_t442_obj_link_driver_bounds_oracle.py`, `qa_stage1_oracle_diff_diag.py`).
   - Verified `tools/affected_map.txt` (all selfhost targets are area directories; `MAP-CHECK OK`), `tests/smoke.list` (references only singletons/exec tests), and `_workspaces/baseline-failures.txt` (0 active entries) require no id remapping.

### Before / After Assertion Count Table (31 merged groups, 125 original bundles → 31 merged bundles, 0 mismatches)
Every `.ax.in` template and embedded golden blob was audited mechanically comparing HEAD's original bundle body against `module __case_<orig_stem>` in `build-snap-T488` (`const=` declared case-count constants, `chk=` `qa_check`/`__qa_check_cnt` calls, `ret=` non-zero error-return checks): **125/125 equal before and after, 0 mismatches**.

| # | Merged bundle (`tests/selfhost/...`) | Modes | Merge | Original bundles & verified equal before/after counts |
|---|---|---|---|---|
| 1 | `abi/qa_abi_classify_and_seam.ax` | `interp native` | 2 -> 1 | `qa_abi_boundary_seam` (unit/checks; const=0, chk=0, ret=32); `qa_abi_win64_classify` (unit/checks; const=0, chk=0, ret=50) |
| 2 | `ast/qa_ast_all.ax` | `interp native` | 5 -> 1 | `qa_ast_derives` (unit/checks; const=0, chk=0, ret=8); `qa_ast_exprs_a` (unit/checks; const=0, chk=0, ret=1); `qa_ast_exprs_b` (unit/checks; const=0, chk=0, ret=1); `qa_ast_items` (unit/checks; const=0, chk=0, ret=1); `qa_ast_types_pats` (unit/checks; const=0, chk=0, ret=2) |
| 3 | `backend/qa_backend_interp.ax` | `interp native` | 4 -> 1 | `qa_backend_unit` (unit/checks; const=4, chk=0, ret=12); `qa_backend_edge` (unit/checks; const=0, chk=0, ret=27); `qa_backend_diff_lir_a` (4 cases; const=4, chk=0, ret=0); `qa_backend_diff_mi_mc_a` (3 cases; const=3, chk=0, ret=0) |
| 4 | `backend/qa_backend_native.ax` | `native` | 2 -> 1 | `qa_backend_diff_lir_b` (69 cases; const=69, chk=0, ret=0); `qa_backend_diff_mi_mc_b` (66 cases; const=66, chk=0, ret=0) |
| 5 | `driver/qa_driver_full_interp.ax` | `interp native` | 2 -> 1 | `qa_driver_inspect_diff_a` (unit/checks; const=0, chk=0, ret=0); `qa_driver_commands_a` (unit/checks; const=0, chk=0, ret=7) |
| 6 | `driver/qa_driver_full_native.ax` | `native` | 2 -> 1 | `qa_driver_inspect_diff_b` (unit/checks; const=0, chk=0, ret=0); `qa_driver_commands_b` (unit/checks; const=0, chk=0, ret=9) |
| 7 | `driver/qa_driver_light.ax` | `interp native` | 2 -> 1 | `qa_driver_cli_and_project` (unit/checks; const=0, chk=0, ret=60); `qa_driver_boundary_edges` (unit/checks; const=0, chk=0, ret=11) |
| 8 | `drop/qa_drop_all.ax` | `interp native` | 11 -> 1 | `qa_drop_d01`..`qa_drop_d07`, `qa_drop_d09`..`qa_drop_d12` (11 × 1 case each; each const=1, chk=0, ret=2) |
| 9 | `encode/qa_encode_instructions_and_edges.ax` | `interp native` | 2 -> 1 | `qa_encode_edge_cases` (unit/checks; const=0, chk=0, ret=47); `qa_encode_instructions` (unit/checks; const=0, chk=0, ret=244) |
| 10 | `hir/qa_hir_all.ax` | `interp native` | 2 -> 1 | `qa_hir_corpus` (6 files; const=0, chk=0, ret=0); `qa_hir_desugar_and_drop` (4 cases; const=0, chk=0, ret=0) |
| 11 | `interp/qa_interp_all.ax` | `interp native` | 3 -> 1 | `qa_interp_unit` (unit/checks; const=0, chk=125, ret=0); `qa_interp_exec_a` (unit/checks; const=0, chk=18, ret=0); `qa_interp_exec_b` (unit/checks; const=0, chk=39, ret=0) |
| 12 | `interp_opt/qa_interp_opt_interp.ax` | `interp native` | 4 -> 1 | `qa_interp_opt_unit` (unit/checks; const=0, chk=0, ret=10); `qa_interp_opt_diff_mir_a` (2 cases; const=2, chk=0, ret=0); `qa_interp_opt_diff_comptime_a` (2 cases; const=2, chk=0, ret=0); `qa_interp_opt_diff_run_a` (2 cases; const=2, chk=0, ret=0) |
| 13 | `interp_opt/qa_interp_opt_native.ax` | `native` | 3 -> 1 | `qa_interp_opt_diff_mir_b` (22 cases; const=22, chk=0, ret=0); `qa_interp_opt_diff_comptime_b` (19 cases; const=19, chk=0, ret=0); `qa_interp_opt_diff_run_b` (24 cases; const=24, chk=0, ret=0) |
| 14 | `isel/qa_isel_all.ax` | `interp native` | 4 -> 1 | `qa_frame_layout_and_verify` (unit/checks; const=0, chk=0, ret=51); `qa_isel_diff_golden` (4 cases; const=0, chk=0, ret=0); `qa_isel_frame_seam_and_edge_cases` (unit/checks; const=0, chk=0, ret=21); `qa_isel_instructions_and_abi` (unit/checks; const=0, chk=0, ret=30) |
| 15 | `kernel_source_diag/qa_kernel_source_diag_all.ax` | `interp native` | 2 -> 1 | `qa_corpus_differential` (unit/checks; const=0, chk=0, ret=8); `qa_session_integration` (unit/checks; const=0, chk=0, ret=13) |
| 16 | `lex/qa_lex_all.ax` | `interp native` | 2 -> 1 | `qa_lex_differential` (unit/checks; const=0, chk=0, ret=2); `qa_lex_tokens` (unit/checks; const=0, chk=0, ret=49) |
| 17 | `lexer/qa_lexer_all.ax` | `interp native` | 5 -> 1 | `qa_lexer_corpus_neg_a` (12 files; ret=12); `qa_lexer_corpus_neg_b` (11 files; ret=11); `qa_lexer_corpus_pos_a` (8 files; ret=8); `qa_lexer_corpus_pos_b` (7 files; ret=7); `qa_lexer_session_integration` (unit/checks; ret=11) |
| 18 | `link/qa_pe_headers_and_linker_diff.ax` | `interp native` | 2 -> 1 | `qa_pe_headers_and_imports` (unit/checks; const=0, chk=0, ret=63); `qa_pe_linker_diff` (unit/checks; const=0, chk=0, ret=17) |
| 19 | `lir/qa_lir_from_ax.ax` | `interp native` | 5 -> 1 | `qa_lir_from_ax_a` (3 cases; ret=2); `qa_lir_from_ax_b` (3 cases; ret=2); `qa_lir_from_ax_c` (3 cases; ret=2); `qa_lir_from_ax_d` (2 cases; ret=2); `qa_lir_from_ax_e` (1 case; ret=2) |
| 20 | `lir/qa_lir_from_mir_and_seam.ax` | `interp native` | 2 -> 1 | `qa_lir_from_mir` (37 cases + ext; ret=8); `qa_lir_seam_edge` (unit/checks; ret=20) |
| 21 | `mir/qa_mir_builder_and_drop.ax` | `interp native` | 3 -> 1 | `qa_mir_builder_and_drop_a` (3 cases; ret=2); `qa_mir_builder_and_drop_b` (3 cases; ret=2); `qa_mir_builder_and_drop_c` (3 cases; ret=2) |
| 22 | `obj/qa_obj_all.ax` | `interp native` | 3 -> 1 | `qa_coff_edge_cases` (unit/checks; ret=23); `qa_coff_writer_diff` (unit/checks; ret=20); `qa_obj_model` (unit/checks; ret=54) |
| 23 | `own_mir_verify/qa_own_mir_diff_interp.ax` | `interp native` | 4 -> 1 | `qa_own_mir_diff_build_a` (2 cases; const=2); `qa_own_mir_diff_drop_a` (1 cases; const=1); `qa_own_mir_diff_diag_own_a` (2 ax + 0 mir; const=2, ret=11); `qa_own_mir_diff_diag_verify_mir` (0 ax + 21 mir; const=21, ret=11) |
| 24 | `own_mir_verify/qa_own_mir_diff_native.ax` | `native` | 5 -> 1 | `qa_own_mir_diff_build_b` (7 cases; const=7); `qa_own_mir_diff_drop_b` (9 cases; const=9); `qa_own_mir_diff_diag_own_b` (11 ax; const=11, ret=11); `qa_own_mir_diff_diag_init` (7 ax; const=7, ret=11); `qa_own_mir_diff_diag_cap_ptr` (8 ax; const=8, ret=11) |
| 25 | `parse/qa_parse_interp.ax` | `interp native` | 14 -> 1 | `qa_parse_corpus_a`..`j` (10 × 2 files; ret=2 each); `qa_parse_recovery_a`..`b` (2 × 5 files; ret=5 each); `qa_parse_terminator_a`..`b` (2 × 2 files; ret=2 each) |
| 26 | `parse/qa_parse_native.ax` | `native` | 5 -> 1 | `qa_parse_heavy_a`..`b` (2 × 4 files; ret=4 each); `qa_parse_qa_edge` (20 files; ret=20); `qa_parse_qa_tuple_struct` (5 files; ret=5); `qa_parse_terminator_heavy` (6 files; ret=6) |
| 27 | `parser/qa_parser_interp.ax` | `interp native` | 4 -> 1 | `qa_parser_diff_neg_a` (3 files; ret=3); `qa_parser_diff_pos_a` (3 files; ret=3); `qa_parser_diff_pos_b` (3 files; ret=3); `qa_parser_session_integration` (unit/checks; ret=10) |
| 28 | `resolve/qa_resolve_all.ax` | `interp native` | 4 -> 1 | `qa_resolve_corpus_neg_a`..`c` (3 × 5 files); `qa_resolve_corpus_pos` (5 files) |
| 29 | `resolve_hir/qa_resolve_hir_all.ax` | `interp native` | 11 -> 1 | `qa_resolve_hir_corpus_neg_a`..`c` (3 × 5 files); `neg_d` (6 files); `pos_a` (2 files); `pos_b` (5 files); `pos_c` (4 files); `wide_a` (5 files); `wide_b` (2 files); `multifile_modules_a`..`b` (2 × 3 cases; ret=1 each) |
| 30 | `typeck/qa_typeck_all.ax` | `interp native` | 3 -> 1 | `qa_typeck_a` (2 golden cases); `qa_typeck_b` (3 cases); `qa_typeck_c` (7 cases) |
| 31 | `typeck_traits/qa_typeck_traits_all.ax` | `interp native` | 3 -> 1 | `qa_typeck_traits_a` (2 pos cases); `qa_typeck_traits_b` (2 neg cases); `qa_typeck_traits_c` (3 neg cases) |

## Files changed
- tests/selfhost/abi/gen_abi_tests.py
- tests/selfhost/ast/gen_ast_tests.py
- tests/selfhost/backend/gen_backend_tests.py
- tests/selfhost/bundle_common.py
- tests/selfhost/bundle_common_selftest.py
- tests/selfhost/driver/gen_driver_tests.py
- tests/selfhost/drop/gen_drop_tests.py
- tests/selfhost/encode/gen_encode_tests.py
- tests/selfhost/hir/gen_hir_tests.py
- tests/selfhost/interp/gen_interp_tests.py
- tests/selfhost/interp_opt/gen_interp_opt_tests.py
- tests/selfhost/interp_opt/qa_t441_hermetic_prelude_mir_bounds_oracle.py
- tests/selfhost/isel/gen_isel_tests.py
- tests/selfhost/kernel_source_diag/gen_kernel_source_diag_tests.py
- tests/selfhost/lex/gen_lex_tests.py
- tests/selfhost/lexer/gen_lexer_tests.py
- tests/selfhost/link/gen_link_tests.py
- tests/selfhost/lir/gen_lir_tests.py
- tests/selfhost/mir/gen_mir_tests.py
- tests/selfhost/obj/gen_obj_tests.py
- tests/selfhost/obj_link_driver/qa_t442_obj_link_driver_bounds_oracle.py
- tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py
- tests/selfhost/parse/gen_parse_tests.py
- tests/selfhost/parser/gen_parser_tests.py
- tests/selfhost/resolve/gen_resolve_tests.py
- tests/selfhost/resolve_hir/gen_resolve_hir_tests.py
- tests/selfhost/stage1/qa_stage1_oracle_diff_diag.py
- tests/selfhost/typeck/gen_typeck_tests.py
- tests/selfhost/typeck_traits/gen_typeck_traits_tests.py

## Tests
All builds and test runs executed inside `build-snap-T488/` with stage-2 `build/axiomc2.exe` (`sha256=8ce0c3c2296e9e043b9aa27a560e05a382c9423987f327d5c790154260cb1ae1`, fixed-point verified `axiomc2 == axiomc3`):

1. **Snapshot regeneration + determinism check**:
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T488` → `bundles regenerated in build-snap-T488: 36 generator(s), 60 file(s), 125 retired, 28s`
   - `python .claude/skills/axiom-tasks/scripts/bundles.py check --root build-snap-T488` → `bundles check: 36 generator(s), 0 file(s), 27s` (exit 0; confirms deterministic extraction from the new merged bundles).
2. **`bundle_common` selftests**:
   - `python tests/selfhost/bundle_common_selftest.py` → `bundle_common selftest: 11 checks passed` + `bundle_common merge selftest: 5 checks passed` (exit 0).
   - `python tests/selfhost/bundle_common_selftest_qa.py` → `bundle_common qa selftest: 8 checks passed` (exit 0).
3. **All 31 merged bundles (`interp`, `native`, `native-O1`, `--no-cache`, `-j 2`)**:
   - `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --no-cache -j 2 --id-file build/merged_ids.txt --json` → `TOTAL 88 PASS 88 FAIL 0 SKIP 0 XFAIL 0`, `weak_native: 0`, serial `2189.6 s` (`36.49 min`), wall `~18.5 min` at `-j 2`.
4. **Mutation proof across all 31/31 merged groups (62/62 mutated builds & runs: `native` + `native-O1`)**:
   - Mutated one case/golden byte/check inside the first member of each of the 31 merged groups on a temporary copy under `build-snap-T488/build/tmp_mut_proof/` (leaving snapshot bundles untouched and deleting all temp artifacts afterward).
   - **31/31 PASS** at both `native` (`-O0`) and `native-O1` (`-O1`): every mutated run exited with `rc=1`, printed `FAIL <first_member>`, omitted `OK <first_member>`, and ran **100% of remaining siblings** (e.g., `10/10` siblings in `qa_drop_all`, `13/13` in `qa_parse_interp`, `10/10` in `qa_resolve_hir_all`, `4/4` in `qa_lir_from_ax`, `2/2` in `qa_interp_all`).
5. **Selfhost wall-time before/after on the same stage-2 compiler (`build-snap-T488/build/axiomc2.exe`)**:
   - Direct same-compiler A/B on `lir` (`qa_lir_from_ax_{a..e}.ax`, 5-way merge): `-O0` build `165.94 s → 35.40 s` (**4.69× faster**, ratio `0.213`), `-O1` build `186.03 s → 40.35 s` (**4.61× faster**, ratio `0.217`); `O0+O1` compile+run `366.46 s → 80.54 s` (**4.55× faster**).
   - Full selfhost suite after merge (`taskgate.py --task T488` ran all 107 selfhost test IDs — all 58 selfhost bundles across `interp`/`native`/`native-O1`, all 36 `bundles_current.test`, `fixedpoint.test`, `stage1_bootstrap.test`, `axiomc_e2e.test`, `qa_axiomc_cli_edges.test`, and all oracles — plus 30 smoke tests): **`3024.7 s` (`50.4 min`) wall at `-j 2`** (all 31 merged bundles covering 125 original split bundles: `36.49 min` serial / `18.5 min` wall at `-j 2`, down from `9.2 h` serial pre-merge / T486+T493+T488 combined).
6. **Full `taskgate.py --task T488` + harness checks**:
   - `python tools/taskgate.py --task T488 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T488.json` → **`TASKGATE T488 exit=0`** (`TOTAL 267 PASS 266 FAIL 0 SKIP 1 XFAIL 0`; `WEAK-NATIVE: 0 in the task's own/changed tests`; `Baseline: BASELINE OK`; `archcheck: clean (229 files scanned, 0 violations)`).
   - `python tools/axtest_affected.py --check-map` → `MAP-CHECK OK`.
   - `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`.
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T488` → verified 0 REFUSED.

## Spec deviations
none

## Follow-ups
- Note: `tests/smoke.list` currently reports a pre-existing unrelated issue (`group build_native has no pool entry`) on `axtest.py --smoke --check`; left untouched as out of scope for T488.

STATUS: COMPLETE round=0
