---
id: T434
title: Baseline fix — derive-generated items of implicitly loaded std leak into root-file AST/resolve/HIR dumps
phase: P11-concurrency-async
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T452]
priority: 12
status: todo
attempts: 0
timeout_min: 900
paths: [compiler/syntax, compiler/parser, tests/parse, tests/resolve, tests/hir, tests/typeck/basic.ax, tests/typeck/basic.thir, tests/typeck/generic]
locks: [tests/selfhost, _workspaces/baseline-failures.txt]
spec: [spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md, spec/SPEC-61-reflection-derive.md, spec/SPEC-20-selfhost.md]
covers: [REQ-TST-072, REQ-CORE-935, REQ-BOOT-085]
---
# T434 — Baseline fix: derive-generated items leak into root-file dumps

## Goal
`axiomc2 inspect --emit=ast|resolved|hir` (and the typeck dumps) of a file show exactly that file's items again, so the
41 committed goldens listed for T434 in `_workspaces/baseline-failures.txt` pass unchanged.

## Scope
- Root cause (ADR-0041 §2 D1): T406 added `@derive(Copy)` items (`Ordering`, `CasResult`) to `std/core/prelude.ax`.
  Derive bodies are produced by re-parsing generated text in `compiler/syntax/parse.ax` (`format_derive` and the
  "Lexes and parses `text` (generated derive code)" helper); the resulting items are attributed to the main file, so
  the driver's `FileId` filter (`session_render_*_into(..., main_fid)`) prints two extra `ItemImpl (Copy)` items
  (209 bytes) in every dump. Confirm this, then make every synthesised item carry the `FileId` (and module) of the item
  that produced it. Check the resolve and HIR renderers use the same attribution.
- Do not re-bless the goldens for this leak: they are authoritative. Re-bless a golden only for a difference that the
  report shows is unrelated to the leak and correct per spec (quote the diff and the rule).
- Regenerate, with their generators, every `tests/selfhost/**` bundle that embeds an edited `compiler/` module, so all
  `bundles_current.test` checks pass.
- Remove the T434 lines from `_workspaces/baseline-failures.txt`.

## Acceptance
- [ ] Every id listed for T434 in `_workspaces/baseline-failures.txt` (41: `parse/*` 28, `resolve/*` 5, `hir/*` 6,
  `typeck/basic.ax`, `typeck/generic/generic_subst.ax`) passes under `axiomc2.exe` built in `build-snap-T434`.
- [ ] Regression test: a test in `tests/parse/` whose root file uses `@derive` itself and whose golden shows its own
  derived items and none from std.
- [ ] Complete suite (ADR-0041 §1): failing ids are a subset of the baseline after this task's removals; WEAK-NATIVE 0;
  `archcheck.py` clean; every `tests/selfhost/**/bundles_current.test` passes.
- [ ] The T434 lines are removed from `_workspaces/baseline-failures.txt` in this task's change set.
- [ ] Report `_workspaces/reports/T434-report.md` with exact `## Files changed`.

## Out of scope
- Changing `std/core/prelude.ax` (T432 owns prelude naming). Changing `bootstrap/axiom0` (frozen). `docs/`.

## Notes
- Build and test in the snapshot: `python tools/build_axiomc.py --out build-snap-T434/build`, then
  `python tools/axtest.py --compiler build-snap-T434/build/axiomc2.exe --exclude-requires axiom0-internal`.
- Canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-13 07:40:00 created by axiom-architect (ADR-0041, complete-suite baseline)
