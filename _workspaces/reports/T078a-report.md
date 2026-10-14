# T078a Report — Port lexer scanner to Axiom

## Summary
- Ported the Stage-0 lexer (`bootstrap/axiom0/src/lex/`) to Axiom under `compiler/lex/` (`token.ax`, `scanner.ax`, `mod.ax`, total 1,493 LOC $\le$ 1,500 LOC budget):
  - `compiler/lex/token.ax`: Defines all 97 `TOK_*` token kind constants, 13 `SUFFIX_*` literal suffix constants, `TOK_FLAG_*` bitflags (`NL_BEFORE`, `ERROR`, `RAW`, `BYTE_FORM`), `COMMENT_*` kinds, `Token`, `Comment`, `LexResult`, packed keyword/token/suffix/message tables, and `ax_lex_render_tokens` matching `axiom0 inspect --emit=tokens` byte-for-byte.
  - `compiler/lex/scanner.ax`: Implements UTF-8 decoding/encoding (`ax_utf8_decode`, `ax_utf8_encode`), UTF-8 BOM skipping, line/doc/nested-block comment scanning, `NL_BEFORE` tracking, identifier & 40-keyword recognition, label vs char literal disambiguation, string/raw-string/byte-string/char/byte-char scanning with `\xHH` and `\u{...}` escapes, number scanning (`0x`, `0o`, `0b`, decimal, float, `_` separators, suffixes, unsigned 64-bit overflow check), punctuation scanning, and all 19 `AX_LEX_*` diagnostics with machine-applicable fixes for `AX_LEX_BAD_BASE_PREFIX`, `AX_LEX_COLON_COLON`, and `AX_LEX_COLON_EQ`.
  - `compiler/lex/mod.ax`: Module root re-exporting the public lexer surface.
- Added standalone selfhost verification tests in `tests/selfhost/lex/`:
  - `tests/selfhost/lex/qa_lex_tokens.ax`: Verifies comments, keywords, identifiers, labels, integer/float literals, char/byte/string/raw-string/byte-string literals, compound operators, and all 19 `AX_LEX_*` diagnostic codes across `[interp]`, `[native]`, and `[native-O1]`.
  - `tests/selfhost/lex/qa_lex_differential.ax`: Verifies byte-for-byte parity of `ax_lex_render_tokens` against `axiom0 inspect --emit=tokens` across `[interp]`, `[native]`, and `[native-O1]`.

## Files changed
- compiler/lex/mod.ax
- compiler/lex/scanner.ax
- compiler/lex/token.ax
- tests/selfhost/lex/qa_lex_differential.ax
- tests/selfhost/lex/qa_lex_tokens.ax

STATUS: COMPLETE round=0
