---
id: T1000
title: E23.1 Canonical language conformance, semantic trace & compiler qualification specification (SPEC-140)
phase: P23-v1-0-conformance-freeze-releas
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T223, T311, T312, T313, T314, T315, T316, T317, T318, T319, T320, T321, T322]
priority: 230
status: todo
attempts: 0
paths: [spec/SPEC-140-conformance-suite-compiler-qualification.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [0017, 0145, 0150, tasks/0602, tasks/0603, tasks/0418, tasks/0423]
covers: [REQ-CORE-3133, REQ-CORE-3134, REQ-CORE-3136, REQ-TST-112]
---
# T1000 — E23.1 Canonical language conformance, semantic trace & compiler qualification specification (SPEC-140)

## Goal
Consolidate the canonical specification for Axiom's three-tier conformance model, six-state test classification, multi-layer semantic trace verification, compiler qualification matrix (`Q0`–`Q4`), and `.axcert` certification into `spec/SPEC-140-conformance-suite-compiler-qualification.md` (`AXS-CNF-*` rule IDs).

## Scope
- Write `spec/SPEC-140-conformance-suite-compiler-qualification.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-CNF-NNN` rules (`0017 §1-10`, `0145 §XXVI.1-35`, `0150 §1-27, §44-46`, `tasks/0602 §1-68`, `tasks/0603 §8-27`).
- Specify the three conformance layers (`Language Conformance`, `Compiler Conformance`, `Target Conformance`), four conformance profiles (`Core Conforming`, `Hosted Conforming`, `Native Conforming`, `Full Toolchain Conforming`), and six-state test outcome classification (`PASS`, `FAIL`, `UNSUPPORTED`, `IMPLEMENTATION_DEFINED`, `TARGET_DEFINED`, `CONDITIONAL`; `REQ-CORE-3133`, `tasks/0602 §1, §3`).
- Specify multi-layer semantic conformance checking (`Source` → `Expected Semantics` → `Expected MIR Property` → `Expected Result`): verifying post-statement variable usability, assignment types, `Copy`/`Move` transitions, initialization state, ownership/capability states, `Verified MIR` invariants (`NoUseAfterMove`, `NoInvalidCapability`, `NoDataRace`, `NoInvalidDrop`), `UNDEFINED_UNSAFE` Oracle reporting, and observable runtime behavior (`REQ-CORE-3134`, `0017 §1-6`, `0150 §4, §9-13`, `tasks/0602 §2, §6-8`).
- Specify the differential qualification hierarchy (`Formal Semantic Rule` → `Reference Interpreter` → `Differential Compiler`) across `-O0`/`-O1`/`-O2`/`-O3`/`-Os`/`-Oz`, `NoLTO`/`ThinLTO`/`FullLTO`, `CleanBuild`/`IncrementalBuild`, `ColdCache`/`WarmCache`, and three-stage self-hosting bootstrap convergence (`stage1` → `stage2` → `stage3` + Diverse Double-Compiling; `ACONF-01..25`, `0150 §11, §20-26`, `tasks/0602 §33-50, §67`).
- Specify the Compiler Qualification Matrix (`Q0 Experimental` .. `Q4 Self-Hosting Qualified`; `REQ-CORE-3136`), `.axcert` qualification certificates (`tasks/0602 §51-54`), `ConformanceDB` / `SpecRuleDB` / `QualificationDB` schemas (`tasks/0602 §57`), and `axiomc conformance`, `axiomc qualify`, and `axiomc cert` CLI subcommands (`REQ-TST-112`, `tasks/0602 §58-59`).
- Update `spec/INDEX.md`, `spec/diagnostics.md` (registering `AX_CNF_*` diagnostic codes), and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-140-conformance-suite-compiler-qualification.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-CNF-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T1000-report.md` with exact `## Files changed`.

## Out of scope
- Compiler and driver implementation of the conformance engine, qualification runner, and `.axcert` tooling (`T1001`–`T1002`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P23 (`P23-v1-0-conformance-freeze-releas`), depends on `T223` and all P11–P22 phase gates (`T311`–`T322`).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T1000/build` and `python tools/axtest.py --compiler build-snap-T1000/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 11:15:00 created by T223 (P23 phase planning)
