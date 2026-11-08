---
id: T817
title: E19.5 CompilerDB documentation extractor, HTML/JSON site renderer, search index & executable doc-test runner (axiomc doc)
phase: P19-developer-tooling
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T219, T752, T755, T756, T759, T805, T816]
priority: 207
status: doing
attempts: 1
paths: [compiler/docgen, compiler/driver/doc_cmd, tests/run/docgen]
spec: [spec/SPEC-104-docgen-test-framework-ux.md, spec/SPEC-21-query-engine-semantic-db.md, tasks/0361, tasks/0374, tasks/0418, tasks/0693, tasks/0695, tasks/0696]
covers: [REQ-TOOL-002, REQ-TOOL-187, REQ-TOOL-298]
started: 2026-11-08 17:25:07
agent: T817-impl
---
# T817 — E19.5 CompilerDB documentation extractor, HTML/JSON site renderer, search index & executable doc-test runner (axiomc doc)

## Goal
Implement the `CompilerDB`-backed documentation generator (`compiler/docgen`), deterministic HTML/JSON renderer, intra-doc link resolver, and executable doc-test runner (`axiomc doc`) per `spec/SPEC-104-docgen-test-framework-ux.md`.

## Scope
- Implement `compiler/docgen` querying `CompilerDB` (`REQ-TOOL-298`) to extract module/item `///` and `//!` documentation, canonical item signatures (`=`, `.`, `view`/`mut_view`, trait implementations, safety preconditions, and effect badges), and verified intra-doc `[module.Item]` cross-references.
- Implement deterministic static HTML site + JSON search index generation and the `axiomc doc --test` executable code-block harness in `compiler/driver/doc_cmd`, ensuring doc comments and doc-test flags never alter core language semantics or production binary payloads (`REQ-TOOL-002`, `REQ-TOOL-187`).

## Acceptance
- [ ] Run tests in `tests/run/docgen` verify `axiomc doc` HTML/JSON output determinism, broken intra-doc link diagnostics, `axiomc doc --test` execution of fenced Axiom examples, and byte-identical production binaries with vs without doc comments.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T817-report.md` with exact `## Files changed`.

## Out of scope
- Optimization pass replay/bisection and `axiomc test` runner (`T818`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T817/build` and `python tools/axtest.py --compiler build-snap-T817/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
- 2026-11-08 17:25:07 started (attempt 1) T817-impl
