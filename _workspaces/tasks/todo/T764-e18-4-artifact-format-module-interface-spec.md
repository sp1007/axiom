---
id: T764
title: E18.4 — Canonical Axiom artifact format & module interface specification (SPEC-24)
phase: P18-compiler-architecture-2-0
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T752]
priority: 714
status: todo
attempts: 0
paths: [spec/SPEC-24-artifact-format-module-interfaces.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-04-core-extensibility.md, 0164, tasks/0582, tasks/0591, tasks/0739, tasks/0787, tasks/0803]
covers: [REQ-CORE-3109, REQ-CORE-3110, REQ-CORE-3123, REQ-CORE-3124, REQ-LNK-434, REQ-LNK-435, REQ-LNK-436, REQ-LNK-437, REQ-LNK-438, REQ-LNK-439, REQ-LNK-440, REQ-LNK-441, REQ-LNK-442, REQ-LNK-443, REQ-LNK-444, REQ-LNK-445, REQ-LNK-446, REQ-LNK-447, REQ-LNK-448, REQ-LNK-449, REQ-LNK-450, REQ-LNK-451, REQ-LNK-452, REQ-LNK-453, REQ-LNK-454, REQ-LNK-455, REQ-LNK-456, REQ-LNK-457, REQ-LNK-458, REQ-LNK-459, REQ-LNK-460, REQ-LNK-461, REQ-LNK-462, REQ-LNK-463, REQ-LNK-464, REQ-LNK-465, REQ-LNK-466, REQ-LNK-467, REQ-LNK-468, REQ-LNK-469, REQ-LNK-470, REQ-LNK-471, REQ-LNK-472, REQ-LNK-473, REQ-LNK-474, REQ-LNK-475, REQ-LNK-476, REQ-LNK-477, REQ-LNK-478, REQ-LNK-479, REQ-LNK-480, REQ-LNK-481, REQ-LNK-482, REQ-LNK-483, REQ-LNK-484, REQ-LNK-485, REQ-LNK-486, REQ-LNK-487, REQ-LNK-488, REQ-LNK-489, REQ-LNK-490, REQ-LNK-491, REQ-LNK-492, REQ-LNK-493, REQ-LNK-494, REQ-LNK-495, REQ-LNK-496, REQ-LNK-497, REQ-LNK-498, REQ-LNK-499, REQ-LNK-500, REQ-LNK-501, REQ-LNK-502, REQ-LNK-503]
---
# T764 — E18.4 — Canonical Axiom artifact format & module interface specification (SPEC-24)

## Goal
Consolidate the canonical specification for Axiom's module interface files (`.axmi`), embedded object/LTO/semantic package sections, and schema-versioned binary serialization contracts into `spec/SPEC-24-artifact-format-module-interfaces.md` (`AXS-ART-*` rule IDs).

## Scope
- Write `spec/SPEC-24-artifact-format-module-interfaces.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-ART-NNN` rules.
- Specify the `.axmi` module interface format (`tasks/0739`, `tasks/0787`): exported declarations, canonical `TypeId` tables, trait implementations, capability/ownership summaries (`tasks/0582`), `const` evaluable bodies, and generic MIR templates required for downstream separate compilation without re-parsing upstream source files.
- Specify custom COFF/object sections (`.axmeta`, `.axmir`, `.axlto`) and standalone package artifact containers (`tasks/0591`, `tasks/0787`, `tasks/0803`), including magic header, schema version, target/ABI descriptor, `InterfaceFingerprint`, and integrity checksum.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-24-artifact-format-module-interfaces.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-ART-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T764-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation of `.axmi` serialization and container sections (`T765`–`T766`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:58:55 created by T218 (P18 phase planning)
