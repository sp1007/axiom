---
id: T318
title: Phase P18 gate — Compiler architecture 2.0
phase: P18-compiler-architecture-2-0
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T218, T067, T750, T751, T752, T753, T754, T755, T756, T757, T758, T759, T760, T761, T762, T763, T764, T765, T766, T767, T768, T769, T770, T771, T772, T773, T774, T775, T776]
priority: 318
status: done
attempts: 1
paths: [tests/conformance/p18, _workspaces/reports/phase-P18-review.md]
spec: [spec/ROADMAP.md, spec/SPEC-21-query-engine-semantic-db.md, spec/SPEC-22-incremental-compilation.md, spec/SPEC-23-parallel-compilation.md, spec/SPEC-24-artifact-format-module-interfaces.md, spec/SPEC-25-pass-contracts-proof-carrying-ir.md, spec/SPEC-26-windows-artifact-kinds.md, spec/SPEC-27-separate-compilation-linker-v2.md]
started: 2026-11-08 14:44:41
finished: 2026-11-08 15:09:34
---
# T318 — Phase P18 gate: Compiler architecture 2.0

## Goal
Certify that phase P18 meets the exit criteria of every epic (`E18.1`–`E18.7`) in `spec/ROADMAP.md` §3 and that all requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks (`no-op rebuild < 100 ms on the compiler itself; edit-one-private-fn rebuild re-typechecks only that module`, plus Windows `.lib`/`.dll` + import `.lib`, `.axmi` separate compilation, parallel determinism, and pass contract verification).
- `reqcov.py --phase P18-compiler-architecture-2-0`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p18` (index + missing cases added).
- Ask `axiom-architect` (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion demonstrated with commands and results in the QA report.
- [ ] Full suite green (gate rule: PASS or BLOCKED; only `xfail` entries for spec gaps with an ADR may remain); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T318-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T218 and all 28 P18 tasks (`T067`, `T750`–`T776`).

## Log
- 2026-11-03 03:01:45 updated by T218 (wired all P18 tasks T067, T750–T776 into depends)
- 2026-11-08 14:44:41 started (attempt 1) T318-impl
- 2026-11-08 15:09:34 accepted by QA -> done
