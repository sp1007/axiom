# T078 Report — Port lexer to Axiom (integration + differential tokens)

## Summary
- Integrated `compiler/lex` (`token.ax`, `scanner.ax`) with `compiler/kernel_source_diag/session.ax` (`CompilerSession`, `SourceDatabase`, `StrInterner`, `DiagSink`, `DiagBuffer`) via `compiler/lexer/session.ax` and `compiler/lexer/mod.ax`:
  - `session_lex_file` and `session_lex_virtual_file`: register source text in `CompilerSession.source_db`, tokenize into `LexResult` while interning identifiers in `CompilerSession.interner` and reporting lexical diagnostics to `CompilerSession.diag_sink`.
  - `session_render_tokens` and `session_render_tokens_into`: render `LexResult` token streams in canonical `inspect --emit=tokens` format using the session's `StrInterner`.
  - `session_lex_and_render_human` and `session_lex_and_render_json`: end-to-end session helpers that lex a file and render both the token stream and human/JSON diagnostics.
- Built the differential corpus test suite under `tests/selfhost/lexer/` verifying 100% byte-for-byte parity against `axiom0 inspect --emit=tokens` across all 38 lexical corpus files:
  - `qa_lexer_corpus_pos_a.ax` (`tests/lex/L01`..`L08` — 8 positive corpus files)
  - `qa_lexer_corpus_pos_b.ax` (`tests/lex/L09`..`L15` — 7 positive corpus files)
  - `qa_lexer_corpus_neg_a.ax` (`tests/ui/lex/E01`..`E12` — 12 negative UI corpus files, verifying both token streams and human diagnostic output)
  - `qa_lexer_corpus_neg_b.ax` (`tests/ui/lex/E13`..`E23` — 11 negative UI corpus files, verifying both token streams and human diagnostic output)
  - `qa_lexer_session_integration.ax` (multi-file session integration verifying shared `StrId` interning across files, comment capture, `LineCol` resolution on token spans, and JSON diagnostic rendering with `MachineApplicable` fixes for `::` and `:=`).
- Verified all 15 test runs in `tests/selfhost/lexer/` (`[interp]`, `[native]`, `[native-O1]`) and all 57 total selfhost test runs pass with 0 architectural violations (`archcheck.py` clean).

## Files changed
- compiler/lexer/mod.ax
- compiler/lexer/session.ax
- tests/selfhost/lexer/qa_lexer_corpus_neg_a.ax
- tests/selfhost/lexer/qa_lexer_corpus_neg_b.ax
- tests/selfhost/lexer/qa_lexer_corpus_pos_a.ax
- tests/selfhost/lexer/qa_lexer_corpus_pos_b.ax
- tests/selfhost/lexer/qa_lexer_session_integration.ax

STATUS: COMPLETE round=0
