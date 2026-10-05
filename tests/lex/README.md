# Lexer tests

This directory contains golden tests for the lexer. `axtest` runs `axiom0 inspect --emit=tokens <file.ax>` and compares the output with `<file.ax.tokens>`.

## Token dump format

Each line in the dump represents one token or one comment trivia.

**Tokens:**
`Kind [start..end] [FLAGS...] [payload]`

- `Kind`: the canonical name of the token (e.g. `Ident`, `Int`, `KwLet`, `EqEq`, `Eof`).
- `start..end`: byte offset half-open range.
- `FLAGS...`: optional, space-separated list of flags:
  - `NL`: the token has `NL_BEFORE` set
  - `ERROR`: the token has `ERROR` set
  - `RAW`: the token has `RAW` set
  - `BYTE_FORM`: the token has `BYTE_FORM` set
- `payload`: optional, depends on the token kind:
  - `Int`: `<value> <suffix>` (suffix is omitted if `None`)
  - `Float`: `<suffix>`
  - `Ident`, `Label`: `<spelling>` (interned string, verbatim)
  - `Char`: `<Unicode scalar value as integer>`
  - `Str`, `ByteStr`: hexadecimal encoded bytes, lowercase, no spaces (e.g. `e1bebf` for `ế`)

**Comments:**
`Kind [start..end]`
- `Kind`: `LineComment`, `DocComment`, `BlockComment`.

Trivia comments are dumped after all tokens (including `Eof`), in source order.
