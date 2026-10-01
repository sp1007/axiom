---
id: T002
title: Spec INDEX, invariants catalogue, diagnostic code taxonomy
phase: P0-foundation
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T001]
priority: 11
status: todo
attempts: 0
paths: [spec/INDEX.md, spec/invariants.md, spec/diagnostics.md]
spec: [0151, 0153, 0171, 0172, tasks/0260, tasks/0262, 0146, tasks/0360]
---
# T002 — Spec INDEX, invariants catalogue, diagnostic code taxonomy

## Goal
Give every agent a map of the canonical spec set and a single registry of invariants and diagnostic codes.

## Scope
- spec/INDEX.md: list of canonical specs (planned and existing), which docs/base files each consolidates, status (draft/frozen).
- spec/invariants.md: the architecture/semantic invariants that code must preserve (AKERNEL-*, ABOOT-*, verifier boundary, layer rules, determinism), each with ID, statement, source, how it is tested.
- spec/diagnostics.md: code taxonomy AX_<AREA>_<NAME> with the **fixed area list** LEX, PARSE, NAME, TYPE, TRAIT, PAT, MOVE, INIT, CAP, DROP, UNSAFE, CONST, VERIFY, FFI, LINK, IO, DRIVER, ICE — one registry file per area (`bootstrap/axiom0/src/diag/codes/<AREA>.def`, created by T009; board tasks lock these files by name, ADR-0005 §2), a code's prefix names its file, a new area needs an edit of this spec first; severity policy, JSON output schema, fix-it model; seed list of codes needed by milestones P1–P4.
- Each invariant in spec/invariants.md has a machine-readable `verify:` field (`tests/<dir>` or `tools/<tool>`), checked by `tools/gatecheck.py` (T022) — an invariant must not be only a comment (0264 §23-24).

## Acceptance
- [ ] Three files exist and cross-reference; every diagnostic code in the seed list has a one-line meaning and example.
- [ ] Invariants each name a verification method (test dir or tool).
- [ ] The area list in spec/diagnostics.md is exactly the list in Scope (later tasks name these files in `locks:`).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T002-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- ADRs: reserve the number with `python .claude/skills/axiom-tasks/scripts/taskctl.py adr-next <slug>` (never pick one by listing the directory) and list the ADR file in the report.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
