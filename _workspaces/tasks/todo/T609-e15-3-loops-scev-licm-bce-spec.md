---
id: T609
title: E15.3 — Canonical loop analysis, SCEV, LICM & bounds-check elimination specification (SPEC-72)
phase: P15-optimizer-2-0
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T215, T600]
priority: 102
status: todo
attempts: 0
paths: [spec/SPEC-72-loops-scev-bce.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-70-optir-ssa-memoryssa.md, 0113, 0165, tasks/0366, tasks/0402, tasks/0416, tasks/0426, tasks/0549]
covers: [REQ-OPT-001, REQ-OPT-026, REQ-OPT-125, REQ-OPT-126, REQ-OPT-127, REQ-OPT-128, REQ-OPT-129, REQ-OPT-130, REQ-OPT-131, REQ-OPT-132, REQ-OPT-133, REQ-OPT-134, REQ-OPT-135, REQ-OPT-136, REQ-OPT-137, REQ-OPT-138, REQ-OPT-139, REQ-OPT-140, REQ-OPT-141, REQ-OPT-142, REQ-OPT-311, REQ-OPT-367, REQ-OPT-368]
---
# T609 — E15.3 — Canonical loop analysis, SCEV, LICM & bounds-check elimination specification (SPEC-72)

## Goal
Consolidate the canonical specification for CFG loop discovery, loop canonicalization, Scalar Evolution (`SCEV`), range analysis, Bounds-Check Elimination (`BCE`), Loop-Invariant Code Motion (`LICM`), and loop transformations into `spec/SPEC-72-loops-scev-bce.md` (`AXS-LOOP-*` and `AXS-BCE-*` rule IDs).

## Scope
- Write `spec/SPEC-72-loops-scev-bce.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-LOOP-NNN` / `AXS-BCE-NNN` rules.
- Specify CFG natural loop discovery, preheader/latch/dedicated-exit canonicalization (`LoopSimplify` + `LCSSA`), and induction variable recognition (`REQ-OPT-125..128`).
- Specify Scalar Evolution (`SCEV`) under Axiom's checked vs wrapping integer overflow rules (`REQ-OPT-129`, `REQ-OPT-130`) and trip-count proof requirements (`REQ-OPT-131`, `REQ-OPT-132`).
- Specify range analysis (`RangeInfo`) and Bounds-Check Elimination (`BCE`) proofs (`REQ-OPT-001`, `REQ-OPT-026`, `REQ-OPT-133..142`, `REQ-OPT-311`): dominating guards, induction bounds (`0 <= i < len(a)`), disjoint half-open sub-range splits, and mandatory check retention whenever proof is `Unknown`.
- Specify legality rules for `LICM`, loop unrolling/peeling/unswitching/fusion, and iterator pipeline fusion (`tasks/0402`, `tasks/0426`, `tasks/0549`, `REQ-OPT-367`, `REQ-OPT-368`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-72-loops-scev-bce.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-LOOP-NNN` / `AXS-BCE-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T609-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation of SCEV/BCE/LICM/loop transforms (`T610`–`T611`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:40:00 created by T215 (P15 phase planning)
