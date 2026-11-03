---
id: T772
title: E18.7 — Canonical Windows x64 static .lib, PE DLL & import library specification (SPEC-26)
phase: P18-compiler-architecture-2-0
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T218]
priority: 699
status: done
attempts: 1
paths: [spec/SPEC-26-windows-artifact-kinds.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-04-core-extensibility.md, spec/decisions/ADR-0001-fixed-address-declarations.md, spec/decisions/ADR-0034-oracle-independence-audit.md, 0104, 0164, 0185, 0186, 0187, 0217, tasks/0369, tasks/0563]
covers: [REQ-LNK-161, REQ-LNK-162, REQ-LNK-163, REQ-LNK-164, REQ-LNK-196, REQ-LNK-197, REQ-LNK-198, REQ-LNK-199, REQ-LNK-200, REQ-LNK-201, REQ-LNK-202, REQ-LNK-203, REQ-LNK-204, REQ-LNK-205, REQ-LNK-206, REQ-LNK-207, REQ-LNK-208, REQ-LNK-209, REQ-LNK-210, REQ-LNK-232, REQ-LNK-233, REQ-CORE-3087, REQ-CORE-3088]
started: 2026-11-03 12:06:54
finished: 2026-11-03 12:19:18
---
# T772 — E18.7 — Canonical Windows x64 static .lib, PE DLL & import library specification (SPEC-26)

## Goal
Consolidate the canonical specification for Axiom's Windows x64 library artifact kinds (`--kind exe|obj|lib|dll`, COFF `.lib` archives, PE32+ `.dll` with exports/relocations/`DllMain`, and short-import `.lib` generation/consumption, `REQ-OWNER-006`) into `spec/SPEC-26-windows-artifact-kinds.md` (`AXS-WLIB-*` rule IDs).

## Scope
- Write `spec/SPEC-26-windows-artifact-kinds.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-WLIB-NNN` rules.
- Specify driver artifact kind selection (`--kind exe|obj|lib|dll`, `--emit=obj` alias, `-l<name>`, `-L<dir>`, and `@link("name")` resolution order; `0164`, `0217`, `tasks/0369`).
- Specify deterministic COFF archive (`.lib`) layout (`!<arch>`, first/second linker symbol members, long-name table, zero timestamps/UIDs/GIDs) and fixed-point archive member extraction (`0185`).
- Specify PE32+ `.dll` emission (`0186`, `0187`, `tasks/0563`): `.edata` export directory from `@export`, generated `DllMain` initialiser running module init hooks (including `ADR-0001` §5–6 E13.7 module-relative binding hooks), `.reloc` base relocation blocks (`IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE`), and companion COFF short-import `.lib` generation + `__imp_<name>` consumption (`ADR-0034` §4 OI-07b).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-26-windows-artifact-kinds.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-WLIB-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T772-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation of COFF `.lib` and PE `.dll` (`T750`, `T751`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`), scheduled first in P18 (`priority: 699`) right after self-hosting per `REQ-OWNER-006`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 03:00:20 created by T218 (P18 phase planning)
- 2026-11-03 12:06:54 started (attempt 1) 
- 2026-11-03 12:19:18 accepted by QA -> done
