---
id: T806
title: E19.2 axiomc fmt CLI (--check, --stdin), AST equivalence verifier & LSP textDocument/formatting integration
phase: P19-developer-tooling
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T219, T752, T755, T756, T759, T802, T805]
priority: 196
status: todo
attempts: 0
paths: [compiler/fmt/verify, compiler/driver/fmt_cmd, tests/run/fmt_cli]
locks: [compiler/lsp/handlers/mod.ax]
spec: [spec/SPEC-101-canonical-formatter.md, spec/SPEC-100-lsp-server-ide-engine.md, tasks/0476, tasks/0374, tasks/0693, tasks/0695, tasks/0696]
covers: [REQ-TOOL-183, REQ-TOOL-298]
---
# T806 — E19.2 axiomc fmt CLI (--check, --stdin), AST equivalence verifier & LSP textDocument/formatting integration

## Goal
Implement the post-format AST equivalence verifier, the `axiomc fmt` CLI subcommand (`--check`, `--stdin`, workspace mode), and LSP `textDocument/formatting` & `rangeFormatting` integration per `spec/SPEC-101-canonical-formatter.md`.

## Scope
- Implement `compiler/fmt/verify` to re-lex and re-parse formatted output in `CompilerDB` (`REQ-TOOL-183`, `REQ-TOOL-298`) and assert structural AST equality and comment token conservation before writing any file.
- Implement `axiomc fmt` in `compiler/driver/fmt_cmd` supporting file/directory/workspace traversal (`axiom.toml`), `--check` (exit non-zero with unified diff when unformatted), and `--stdin`.
- Wire `textDocument/formatting` and `textDocument/rangeFormatting` in `compiler/lsp/handlers/mod.ax` to return minimal `TextEdit` arrays from the canonical formatter.

## Acceptance
- [ ] Run tests in `tests/run/fmt_cli` verify `axiomc fmt`, `axiomc fmt --check`, `axiomc fmt --stdin`, refusal on syntax errors without file mutation, AST equivalence guard, and LSP `textDocument/formatting` edits.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T806-report.md` with exact `## Files changed`.

## Out of scope
- Full-corpus formatter idempotence certification (`T807`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T806/build` and `python tools/axtest.py --compiler build-snap-T806/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
