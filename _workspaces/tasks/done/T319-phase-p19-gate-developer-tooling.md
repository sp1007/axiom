---
id: T319
title: Phase P19 gate — Developer tooling
phase: P19-developer-tooling
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T219, T318, T800, T801, T802, T803, T804, T805, T806, T807, T808, T809, T810, T811, T812, T813, T814, T815, T816, T817, T818, T819]
priority: 319
status: done
attempts: 1
paths: [tests/conformance/p19, _workspaces/reports/phase-P19-review.md]
spec: [spec/ROADMAP.md, spec/SPEC-100-lsp-server-ide-engine.md, spec/SPEC-101-canonical-formatter.md, spec/SPEC-102-refactoring-engine-semantic-vcs.md, spec/SPEC-103-diagnostics-ux-ai-interface.md, spec/SPEC-104-docgen-test-framework-ux.md]
covers: [REQ-TOOL-297, REQ-TOOL-298, REQ-TST-112]
started: 2026-11-08 19:29:35
finished: 2026-11-08 19:59:35
---
# T319 — Phase P19 gate: Developer tooling

## Goal
Certify that phase P19 meets the exit criteria of every epic (`E19.1`–`E19.5`) in `spec/ROADMAP.md` §3 and that all
requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks (`tests/conformance/p19/e19_1_lsp_server` through `tests/conformance/p19/e19_5_docgen_test_ux`, including the VS Code extension using `axiomc lsp` and formatter idempotence over the whole corpus).
- `reqcov.py --phase P19-developer-tooling`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p19` (index + missing cases added).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion (`E19.1`–`E19.5`, including the VS Code extension using the LSP and formatter idempotence over the whole corpus) demonstrated with commands and results in the QA report.
- [ ] Full suite green (gate rule: PASS or BLOCKED; only `xfail` entries for spec gaps with an ADR may remain); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T319-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T219, the P18 gate T318, and every P19 task T800–T819.

## Log
- 2026-10-06 02:31:22 covers += REQ-TOOL-297, REQ-TOOL-298, REQ-TST-112 (metadata only)
- 2026-11-03 09:50:00 updated by T219 (wired T318 and all 20 P19 tasks T800–T819 into depends and SPEC-100..SPEC-104 into spec)
- 2026-11-08 19:29:35 started (attempt 1) T319-impl
- 2026-11-08 19:59:35 accepted by QA -> done
