---
id: T600
title: E15.1 — Canonical OptIR, SSA/MemorySSA & pass-legality specification (SPEC-70)
phase: P15-optimizer-2-0
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T215]
priority: 93
status: done
attempts: 1
paths: [spec/SPEC-70-optir-ssa-memoryssa.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-04-core-extensibility.md, 0161, 0162, 0165, tasks/0315, tasks/0366, tasks/0398, tasks/0399, tasks/0545, tasks/0546]
covers: [REQ-OPT-010, REQ-OPT-016, REQ-OPT-017, REQ-OPT-018, REQ-OPT-019, REQ-OPT-020, REQ-OPT-021, REQ-OPT-022, REQ-OPT-023, REQ-OPT-047, REQ-OPT-048, REQ-OPT-049, REQ-OPT-050, REQ-OPT-051, REQ-OPT-052, REQ-OPT-053, REQ-OPT-054, REQ-OPT-055, REQ-OPT-056, REQ-OPT-057, REQ-OPT-058, REQ-OPT-059, REQ-OPT-296, REQ-OPT-297, REQ-OPT-298, REQ-OPT-321, REQ-OPT-322, REQ-OPT-323, REQ-OPT-324, REQ-OPT-325, REQ-OPT-326, REQ-OPT-327, REQ-OPT-328, REQ-OPT-329, REQ-OPT-330, REQ-OPT-331, REQ-OPT-332, REQ-OPT-333, REQ-OPT-359, REQ-OPT-360, REQ-OPT-361, REQ-OPT-362]
started: 2026-11-03 03:25:30
finished: 2026-11-03 03:47:37
---
# T600 — E15.1 — Canonical OptIR, SSA/MemorySSA & pass-legality specification (SPEC-70)

## Goal
Consolidate the canonical specification for Axiom's Unified Dataflow Optimization IR (`OptIR`), SSA and `MemorySSA` representation, pass-manager legality contracts, and observable-behavior preservation rules into `spec/SPEC-70-optir-ssa-memoryssa.md` (`AXS-OPT-*` rule IDs).

## Scope
- Write `spec/SPEC-70-optir-ssa-memoryssa.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-OPT-NNN` rules.
- Specify the strict separation of roles between Verified MIR (authoritative semantic/ownership/capability/Drop model) and `OptIR` (value-based SSA + `MemorySSA` optimization model built exclusively from Verified MIR, `AOPT-20..40`, `BOOTSTRAP-139`).
- Specify `OptIR` SSA form (block parameters / phi nodes, dominance tree, dominance frontiers, aggregate SSA projection) and `MemorySSA` (`LiveOnEntry`, `MemoryDef`, `MemoryUse`, `MemoryPhi`, clobber queries integrated with `AliasInfo` and `EffectInfo`).
- Specify the optimization pass contract framework (`BOOTSTRAP-140`, `tasks/0545`, `tasks/0546`, `tasks/0797`): every pass declares required analyses, legality preconditions, preserved analyses, and postconditions verified before lowering to LIR; a failed proof leaves the IR unchanged rather than guessing.
- Specify observable behavior preservation (`0165 §1..13`, `AOPT-21..39`): return values, deterministic `Drop` ordering, checked arithmetic panic/trap vs wrapping arithmetic, I/O, atomics, `volatile`, FFI boundaries, and `black_box`.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-70-optir-ssa-memoryssa.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-OPT-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T600-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation of `OptIR`, pass manager, or scalar passes (`T601`–`T603`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:38:00 created by T215 (P15 phase planning)
- 2026-11-03 03:25:30 started (attempt 1) 
- 2026-11-03 03:47:37 accepted by QA -> done
