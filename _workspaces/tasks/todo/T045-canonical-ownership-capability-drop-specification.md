---
id: T045
title: Canonical ownership / capability / drop specification
phase: P6-ownership
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T003, T003a]
priority: 10
status: todo
attempts: 0
paths: [spec/SPEC-10-ownership.md, spec/SPEC-11-capability.md, spec/SPEC-12-drop.md]
timeout_min: 300
spec: [0004, 0005, 0160, 0176, 0177, 0178, 0019, 0020, 0021, 0028, 0030, 0086, 0118, tasks/0394, tasks/0395, tasks/0674, tasks/0541, tasks/0270, 0263]
---
# T045 — Canonical ownership / capability / drop specification

## Goal
One precise, testable statement of Axiom's ownership model (ownership ≠ borrow checker), capabilities (view/mut_view, regions) and deterministic destruction.

## Scope
- Rules with IDs AXS-OWN/CAP/DROP-NNN: move/copy classification, place model, partial moves, init states, ephemeral vs stored views, region relations, conflicts, escape rules, drop order, drop flags, cleanup on every edge, panic interaction; a test matrix (rule → positive/negative example programs in canonical syntax).
- **Stored views** (ADR-0004 §3; tasks/0541 §96, tasks/0270 ACAP-43): a view held in a struct field — owner-outlives check, no self-reference; the same rule gives the arena-escape rule for arena-owned values (T073a). `Str` and slices are views, not bare pointer + length (0263 §39).
- Destructor form and `drop(x)` per ADR-0006 §1; drop glue of generic instances and `drop_in_place` (T054b, T061a).
- **What MIR must carry** (normative list for T018; 0263 §42, ABOOT-43..45): place projections for partial moves, drop flags, view/region annotations, storage markers, drop terminators.
- Every row of the test matrix is tagged with the task that must pass it: T046 (move/copy), T047 (init), T048 (capability, stored views), T048b (slices), T049 (drop), T050 (verifier), T054b (generic drop glue).

## Acceptance
- [ ] Three specs with test matrix; ADRs for contradictions among the sources.
- [ ] The "required of MIR" list exists and every test-matrix row carries its task tag.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T045-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Runs early, in parallel with P1/P2 (priority 10, ADR-0005 §5): T018 depends on it.
- ADRs: reserve the number with `python .claude/skills/axiom-tasks/scripts/taskctl.py adr-next <slug>` and list the ADR file in the report.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
