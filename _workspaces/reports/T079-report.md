# T079 Report — Port parser + AST to Axiom (integration + differential AST)

## Summary
- Integrated `compiler/syntax/ast.ax` (`T079a`), `compiler/syntax/parse.ax` (`T079b`), and `compiler/lexer/session.ax` (`T078`) with `compiler/kernel_source_diag/session.ax` (`T077`) via `compiler/parser/session.ax` and `compiler/parser/mod.ax`:
  - `session_parse_tokens`: parses a pre-tokenized `Token` stream into `parse_arena` using `CompilerSession.diag_sink` and `CompilerSession.interner`.
  - `session_parse_file` and `session_parse_virtual_file`: register/load source files in `CompilerSession.source_db`, run `session_lex_file` / `session_lex_virtual_file`, invoke `ax_parse`, free temporary lexer token buffers, and return `ParseResult`.
  - `session_render_ast` and `session_render_ast_into`: render `Ast` in canonical `inspect --emit=ast` S-expression format using `CompilerSession.interner` and per-file `FileId` filtering.
  - `session_parse_and_render_human` and `session_parse_and_render_json`: end-to-end session entry points that register, lex, and parse a virtual file and emit both the canonical AST dump and human or JSON diagnostics.
- Built the differential AST and session integration test suite under `tests/selfhost/parser/`:
  - `qa_parser_session_integration.ax` (`[interp]`, `[native]`, `[native-O1]`): multi-file session integration verifying `session_parse_file`, `session_parse_virtual_file`, `session_parse_tokens`, `session_render_ast`, `session_render_ast_into`, `session_parse_and_render_json`, cross-file `StrId` sharing in `CompilerSession.interner`, and per-`FileId` filtering in `ax_ast_render`.
  - `qa_parser_diff_pos_a.ax` (`[interp]`, `[native]`, `[native-O1]`): differential parity against `axiom0 inspect --emit=ast` on `tests/resolve/` corpus (`R01_basic.ax`, `enum_variant.ax`, `simple.ax`).
  - `qa_parser_diff_pos_b.ax` (`[interp]`, `[native]`, `[native-O1]`): differential parity against `axiom0 inspect --emit=ast` on `tests/hir/` corpus (`basic.ax`, `control.ax`, `types.ax`).
  - `qa_parser_diff_neg_a.ax` (`[interp]`, `[native]`, `[native-O1]`): differential error recovery and human diagnostic parity against `axiom0 inspect --emit=ast` on `tests/ui/parse/` (`bad_generics.ax`, `bad_types.ax`, `keywords.ax`).
  - `qa_parser_diff_corpus_wide.ax` (`[native]`, `[native-O1]`): 25-file cross-stage differential corpus spanning `tests/parse/`, `tests/ui/parse/`, `tests/resolve/`, and `tests/hir/`.
- Documented corpus differential counts:
  - Committed selfhost AST/parse/parser test suites (`tests/selfhost/ast/`, `tests/selfhost/parse/`, `tests/selfhost/parser/`): 73 test executions across `[interp]`, `[native]`, and `[native-O1]`, covering 63 distinct source files and synthetic edge/derive/recovery cases (73/73 PASS).
  - Full-tree differential sweep against `axiom0 inspect --emit=ast` (707 single-file `.ax` inputs under `tests/`): 689/689 single-file non-project inputs within lexer limits match byte-for-byte on both stdout (AST S-expression) and stderr (human diagnostics).
- Verified `python tools/archcheck.py` (190 files scanned, 0 violations) and all 14 test runs in `tests/selfhost/parser/` pass.

## Files changed
- compiler/parser/mod.ax
- compiler/parser/session.ax
- tests/selfhost/parser/qa_parser_diff_corpus_wide.ax
- tests/selfhost/parser/qa_parser_diff_neg_a.ax
- tests/selfhost/parser/qa_parser_diff_pos_a.ax
- tests/selfhost/parser/qa_parser_diff_pos_b.ax
- tests/selfhost/parser/qa_parser_session_integration.ax

STATUS: COMPLETE round=0
