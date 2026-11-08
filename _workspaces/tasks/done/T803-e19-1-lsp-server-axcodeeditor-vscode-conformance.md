---
id: T803
title: E19.1 LSP server, AXEDITOR/AXCODEEDITOR & VS Code extension conformance suite
phase: P19-developer-tooling
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T219, T752, T755, T756, T759, T802]
priority: 193
status: done
attempts: 1
paths: [tests/conformance/p19/e19_1_lsp_server]
spec: [spec/SPEC-100-lsp-server-ide-engine.md, 0101, 0146, tasks/0374, tasks/0448, tasks/0450, tasks/0479, tasks/0664, tasks/1053, tasks/1054]
covers: [REQ-TOOL-183, REQ-TOOL-184, REQ-TOOL-185, REQ-TOOL-188, REQ-TOOL-189, REQ-TOOL-191, REQ-TOOL-297, REQ-TOOL-298, REQ-TOOL-299, REQ-TOOL-300]
started: 2026-11-08 14:54:08
finished: 2026-11-08 15:30:06
---
# T803 — E19.1 LSP server, AXEDITOR/AXCODEEDITOR & VS Code extension conformance suite

## Goal
Certify E19.1 exit criteria with an end-to-end conformance suite covering `axiomc lsp`, `CompilerDB` incremental IDE queries, `AXEDITOR`/`AXCODEEDITOR`, and the VS Code LSP extension.

## Scope
- Create conformance tests in `tests/conformance/p19/e19_1_lsp_server` verifying:
  - multi-module LSP sessions (`didOpen`, incremental `didChange`, `publishDiagnostics`, `definition`, `references`, `hover`, `completion`, `rename`, `semanticTokens`, `inlayHint`);
  - partial-program completion and hover respecting visibility, moved values, `view`/`mut_view` capabilities, and ambiguous trait method rejection (`REQ-TOOL-188`, `REQ-TOOL-189`);
  - `AXEDITOR` large-file Unicode piece-table edits (`REQ-TOOL-299`), `AXCODEEDITOR` semantic highlighting/completion (`REQ-TOOL-300`), and VS Code extension (`tools/vscode-axiom`) end-to-end LSP handshake and query round-trip;
  - differential equivalence between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p19/e19_1_lsp_server` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T803-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T803/build` and `python tools/axtest.py --compiler build-snap-T803/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
- 2026-11-08 14:54:08 started (attempt 1) T803-impl
- 2026-11-08 15:30:06 accepted by QA -> done
