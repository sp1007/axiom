---
id: T010
title: Lexer + `inspect --emit=tokens`
phase: P2-frontend
owner: axiom-frontend
reviewer: axiom-qa
depends: [T001, T009]
priority: 20
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/lex, tests/lex]
spec: [spec/SPEC-01-lexical.md, 0154, 0173, tasks/0385]
---
# T010 — Lexer + `inspect --emit=tokens`

## Goal
Implement the full lexical spec: tokens with spans, newline tokens where significant, trivia retained for tooling.

## Scope
- Token kinds per SPEC-01; literal decoding (value + suffix) with overflow diagnostics; string escapes; nested comments; newline significance flag.
- Targeted diagnostics + fix-its: AX_LEX_COLON_COLON, AX_LEX_COLON_EQ, unterminated string/comment, invalid escape, invalid digit for base, invalid UTF-8.
- `@at` is an ordinary attribute token sequence for the lexer (no special casing).
- Driver: `axiom0 inspect --emit=tokens file.ax` (stable text format documented in tests/lex/README.md).

## Acceptance
- [ ] Golden tests covering every token kind and literal form from 0152 §12 (1, 1u32, 1.0, 1e10, 0xff, 0b101, "a", b"..."), `1..2`, `p.0.1`, all operators by maximal munch.
- [ ] ui tests for each lexer diagnostic.
- [ ] Lexer never crashes on arbitrary bytes (quick random test in report).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T010-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
