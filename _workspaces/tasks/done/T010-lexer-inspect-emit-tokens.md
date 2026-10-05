---
id: T010
title: Lexer + `inspect --emit=tokens`
phase: P2-frontend
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T001, T009, T003a]
priority: 20
status: done
attempts: 1
paths: [bootstrap/axiom0/src/lex, tests/lex, tests/ui/lex, bootstrap/axiom0/src/driver/emit_tokens.c]
locks: [bootstrap/axiom0/src/diag/codes/LEX.def]
spec: [spec/SPEC-01-lexical.md, 0154, 0173, tasks/0385]
started: 2026-10-05 16:02:36
finished: 2026-10-05 16:29:29
covers: [REQ-GRM-001, REQ-GRM-002, REQ-OWNER-001, REQ-OWNER-002]
---
# T010 — Lexer + `inspect --emit=tokens`

## Goal
Implement the full lexical spec: tokens with spans, newline tokens where significant, trivia retained for tooling.

## Scope
- Token kinds per SPEC-01; literal decoding (value + suffix) with overflow diagnostics; string escapes; nested comments; newline significance flag.
- Targeted diagnostics + fix-its: AX_LEX_COLON_COLON, AX_LEX_COLON_EQ, unterminated string/comment, invalid escape, invalid digit for base, invalid UTF-8.
- `@at` is an ordinary attribute token sequence for the lexer (no special casing).
- Emitter `src/driver/emit_tokens.c`, registered through the T004 table: `axiom0 inspect --emit=tokens file.ax` (stable text format documented in tests/lex/README.md). The emitter runs source loading + lexing itself until the pipeline module exists (T016).

## Acceptance
- [ ] Golden test: string literal `"Xin chào thế giới"` lexes with correct byte span and decoded value (UTF-8 preserved; char count vs byte count checked).
- [ ] Golden tests covering every token kind and literal form from 0152 §12 (1, 1u32, 1.0, 1e10, 0xff, 0b101, "a", b"..."), `1..2`, `p.0.1`, all operators by maximal munch.
- [ ] Char literals `'a'`, `'ế'`, `'\u{1EBF}'` decode to their Unicode scalar value; string `"\u{1EBF}"` decodes to the UTF-8 bytes of `ế` (E1 BA BF); `\u{D800}` (surrogate), `\u{110000}`, `''` and `'ab'` are rejected with dedicated codes (e.g. AX_LEX_INVALID_UNICODE_ESCAPE, AX_LEX_BAD_CHAR_LITERAL).
- [ ] ui tests for each lexer diagnostic (under tests/ui/lex).
- [ ] Lexer never crashes on arbitrary bytes (quick random test in report).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T010-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-05 16:02:36 started (attempt 1) T010-impl
- 2026-10-05 16:29:29 accepted by QA -> done
- 2026-10-06 02:24:00 covers += REQ-GRM-001 (metadata only)
- 2026-10-06 02:24:21 covers += REQ-GRM-002, REQ-OWNER-001, REQ-OWNER-002 (metadata only)
