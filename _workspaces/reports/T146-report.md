# T146 report - AX0-FIX-04 statement terminator (AXS-GRM-011) enforced

## Summary
- axiom0 (`bootstrap/axiom0/src/syntax/parse.c`) and the port (`compiler/syntax/parse.ax`) now require a terminator
  after every statement, top-level item and trait/impl/extern member: `;`, a line break before the next token
  (newlines significant, AXS-GRM-010) or `}`/EOF. Anything else reports `AX_PARSE_EXPECTED_TERMINATOR` ("Expected a
  line break or ';'") at the next token and parsing continues at that token (nothing is skipped).
  Block-like expression statements (`if {}`, `loop {}`, `match {}`) have no exemption.
- Two further root causes of silent drops were fixed in both parsers, because the terminator check cannot work without them:
  1. `{` did not push newline mode ON (AXS-GRM-010). A block inside `(` or `[` (closure body or block in a call
     argument, `match` arms inside parentheses) ran with newlines ignored, so every statement after the first was
     dropped (a closure body `let a = x` / `let b = a` / `b` inside a call kept only `let a`). `parse_block` and the
     `match` body now push ON.
  2. After an expression statement or assignment whose `;` was already consumed, the old `sync_to_term` skipped the
     rest of the line: `{ x = 1; return true; }` lost `return true;`.
- Recovery rule (small refinement of the task text): when the statement/item already has a diagnostic, the rest of its
  line is skipped as before (reported, not silent) instead of adding a second error; a statement/item without an
  earlier diagnostic reports the terminator error and continues at the next token. This keeps the existing negative
  corpora byte-identical except where they contained exactly the silent-drop case. An item's `;` is left for
  `parse_item` (empty item) so AST dumps are unchanged.
- Derive fixes exposed by the stricter parsing (both parsers): `@derive(Hash)` generated `self.a.hash(state); self.b.hash(state);`
  on one line, so only the first field was ever hashed; with the tail restored the second call used a moved
  `mut_view` (AX_MOVE_USE_AFTER_MOVE). Generated text is now `self.f.hash(mut_view(*state));` (the std idiom).
  `expand_derives` (C) also no longer computes the struct name when there is no attribute / no name (pre-existing ICE
  on a bare `struct`, found by tools/fuzz.py seed 7 iteration 15; regression tests `bug_struct_no_name`, `bug_derive_no_name`).

## Sweep (std/, compiler/, tests/ built with the fixed parser)
Method: `inspect --emit=ast` over all 1266 tracked `.ax` files with the old and new axiom0 (diagnostics + AST hash),
plus an instrumented copy of the old parser that prints every place where `sync_to_term` skipped tokens without any
diagnostic (81 files, only 6 outside generated bundles; the same sites also appear inside 49 `tests/selfhost` bundles).
- Sources newly REJECTED by the stricter parser: `std/` 0, `compiler/` 0, `tests/`: `tests/parse/bug_p5.ax`
  (expected-negative test; golden `.ast` blessed, one more `StmtExpr(ExprError)` after the extra error) and one
  hidden case, the byte-encoded prelude stub `enum _O<T>{N}enum _R<T,E>{O}fn _p()->bool{true}` in
  `tests/selfhost/lir/qa_lir_from_ax_d.ax` and `_e.ax` (three items on one line; newlines inserted, length 47 -> 49).
  Outside my paths (not edited): scratch files in the repository root, `test_gen.ax` (one-line `fn identity..{ x } fn main()`,
  now rejected), `test_min.ax`, `test_derive_debug.ax`, `test_len.ax`, `test_ufcs.ax`; nothing references them.
- Sources changed by this task: std 0, compiler 1 (`compiler/syntax/parse.ax`, the port itself), tests 112
  (93 selfhost bundles embedding parse.ax, 2 lir stubs, corpus/golden refreshes, new tests).
- Behaviour-changing sites (code that was silently dropped and now executes; expected values re-derived by hand,
  nothing re-captured):
  - `compiler/types/typeck.ax` const evaluator: 15 lines `if op == BINOP_X { *out_val = ...; return true; }`
    (ADD, SUB, BITAND/OR/XOR, SHL, SHR, EQ..GE, LOGAND, LOGOR) lost `return true;` and fell through; plus 2 sites
    `if sv_eq(...) { found = true; break; }` lost `break;` (lines 2975, 3027). The typeck selfhost suites
    (embedding typeck.ax in 40+ bundles) pass with the restored code. typeck.ax itself needed no edit.
  - derive(Hash) with 2+ fields (axiom0 and port): only the first field was hashed. `tests/run/trait2/test_derive.ax`
    still passes; by hand hash(Point{10,20}) = 30 -> slot 2 (= hash of the equal p2), hash(p3 = {5,30}) = 35 -> slot 3.
  - `tests/run/intrinsics/ops_table.ax`: 2670 lines `if op(..) != k { bad = bad + 1; fail("i8", n); }` lost `fail(..)`
    (only `bad` was counted; exit code unchanged when all ops are right, now the failing op is also reported).
  - `tests/std/fs/qa_binary_file_buf.ax` (lines 255, 266: `CloseHandle(h); return -9;`; lines 586-612: the NUL-terminated
    path bytes `_qa_sort_dir_1` and `_qa_bin_buf_tmp.bin` were stored only for the first byte, so the files used the
    path `_` plus uninitialised heap) and `tests/std/fs/qa_unicode_paths.ax` (7 `close(..); return N;` checks).
    Both pass. Note: the three modes share a fixed file name and run in parallel (pre-existing race; seen once as
    exit 4 under heavy load, not reproducible alone or in 4 further runs).
  - `tests/selfhost/diag/qa_diag_emitter.ax` (7 byte-store lines), `tests/selfhost/kernel/qa_kernel_interner.ax`
    (3 lines storing "foo"/"bar"/"baz"), `tests/selfhost/link/qa_pe_headers_and_imports.ax` (10 failure checks
    `{ free..; return 7x; }` and 8 `coff_buf_free` lines): all pass with the full code.
- Pre-existing, not changed: `compiler/own/{init,mod,move,unsafe}.ax` and `compiler/own_mir_verify/{mod,session}.ax`
  contain `module compiler.own.move` etc. (reserved word `move`) and have parse errors before and after (identical
  diagnostics, my change adds none there). Two more pre-existing ICEs found by tools/fuzz.py (`comptime 'A'` seed 11
  iteration 60, `async 400` seed 12 iteration 272: the C parser takes a name from a non-identifier token) are not
  fixed here (out of scope); the port does not have them (separate token fields).

## Tests
- `tests/ui/parse/terminator_{two_stmts,if_stmt,loop_stmt,match_stmt,assign_stmt,items,members}.ax` (ui, exact line) and
  `terminator_span_*.test` (exact line/column/end of the span and the error count via `check --json`).
- `tests/run/parse/terminator_accepted.ax` (exit 88, hand-derived; includes `if c { return 5; }; return 6;` = 6 for
  `c == false`, a block inside call arguments, match arms on separate lines inside parentheses) and
  `terminator_one_line_items.ax` (exit 5). Both pass interp/native/native-O1 and FAIL with the old compiler.
- `tests/ui/parse/bug_struct_no_name.ax`, `bug_derive_no_name.{ax,test}` (fuzz ICE regressions).
- Selfhost parity (ADR-0034 section 2): `tests/selfhost/parse/qa_parse_terminator_{a,b}.ax` (interp + native) and
  `qa_parse_terminator_heavy.ax` (native only: heavy multi-case bundle, interp twins a and b) embed the real
  `compiler/syntax/parse.ax`, parse the same inputs and compare AST text and human diagnostics byte-for-byte with
  `axiom0 inspect --emit=ast`. A temporary 96-case differential (all negative corpora of tests/, the new inputs, 25
  random run programs; not committed) also matched with 0 mismatches.
- 93 selfhost bundles that embed `parse.ax` were patched by applying the old->new diff of `parse.ax` (the embedded
  copies are hunk-identical). Corpus blobs of `qa_parse_corpus_g` (bug_p5) and `qa_parse_qa_edge` (`qa_edge_2c/2k`
  derive Hash, `9e` `struct T u8;` is now an error - the harness flag for case 9 now expects an error, `4`/`5` changed
  cascade errors) were regenerated from `axiom0 inspect` (the method reproduces every other existing blob
  byte-identically with the old compiler). `qa_parse_qa_tuple_struct` and `qa_parser_session_integration` deliberately
  differ from axiom0 and were not regenerated.
- Parity registry (ADR-0035 section 4): `known_divergent.txt` not touched. The first full run's `axiomc_e2e` found one
  regression of mine (`terminator_accepted.ax` used a closure, closures are an existing axiomc gap); the test now uses
  a block expression, no entry was added.

## Spec deviations / questions
- Recovery after an erroneous statement/item (see Summary) skips the remaining tokens of its line after the
  earlier diagnostic instead of re-parsing them as the next statement; decided to keep existing diagnostics stable.
- Item-level `;` is not consumed by the terminator check (kept as an empty item) to leave AST dumps unchanged.

## Verification
- Build in `build-snap-T146/build`: gcc with `-Wall -Wextra -Wpedantic -Werror`, no warnings; `clang -fsyntax-only` clean;
  `tools/archcheck.py`: 190 files, 0 violations.
- First full suite in the snapshot: TOTAL 2638 PASS 2622 FAIL 16 = 6 lir (stub, fixed), `axiomc_e2e` (closure test,
  fixed), 9 TIMEOUTs on a machine loaded by parallel agents (10 s - 1200 s limits; `qa_parse_terminator_b` interp takes
  29 s alone, its timeout is now 300 s).
- Second full suite (after the fixes, snapshot `build-snap-T146`, -j8 with other agents active): TOTAL 2640 PASS 2631
  FAIL 9. All 9 are load effects, each passes when re-run on the same snapshot:
  `axiomc_e2e` (exit 0 alone and through `axtest`: `AXIOMC-E2E programs=485 equal=349 known_divergent=136`, registry
  untouched, no XPASS/IMPROVED) and 8 interp TIMEOUTs of long-running tests that do not depend on this change's
  logic except through the parser: `selfhost/backend/qa_backend_unit`, `selfhost/drop/qa_drop_d11` (1200 s limits),
  `selfhost/lex/qa_lex_differential` (10 s), `selfhost/lexer/qa_lexer_corpus_neg_{a,b}` (30 s),
  `selfhost/resolve/qa_resolve_corpus_{neg_c,pos}` (600 s). Re-run together in a quieter subset: 23 of 24 pass;
  `selfhost/typeck/qa_typeck_b` [interp] still exceeded 600 s with seven interp tests in parallel but PASSES alone
  (3/3 modes, 4 min 15 s). The first full run (before the lir stub and closure-test fixes) had the same timeout set
  plus the 7 real failures listed above, so no timeout is new. I did not start a third full suite (coordinator
  instruction); the QA gate should run the suite with a lower `-j` or `--timeout-scale 3`.

## Files changed
- bootstrap/axiom0/src/syntax/parse.c
- compiler/syntax/parse.ax
- tests/parse/bug_p5.ast
- tests/run/parse/terminator_accepted.ax
- tests/run/parse/terminator_one_line_items.ax
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
- tests/selfhost/typeck/qa_typeck_a.ax
- tests/selfhost/typeck/qa_typeck_b.ax
- tests/selfhost/typeck/qa_typeck_c.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_a.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_b.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_c.ax
- tests/selfhost/verify/qa_verify_pipeline.ax
- tests/ui/parse/bug_derive_no_name.ax
- tests/ui/parse/bug_derive_no_name.test
- tests/ui/parse/bug_struct_no_name.ax
- tests/ui/parse/terminator_assign_stmt.ax
- tests/ui/parse/terminator_if_stmt.ax
- tests/ui/parse/terminator_items.ax
- tests/ui/parse/terminator_loop_stmt.ax
- tests/ui/parse/terminator_match_stmt.ax
- tests/ui/parse/terminator_members.ax
- tests/ui/parse/terminator_span_if_stmt.test
- tests/ui/parse/terminator_span_items.test
- tests/ui/parse/terminator_span_loop_stmt.test
- tests/ui/parse/terminator_span_members.test
- tests/ui/parse/terminator_span_two_stmts.test
- tests/ui/parse/terminator_two_stmts.ax

STATUS: COMPLETE round=0
