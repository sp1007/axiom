---
id: T550
title: E14.1 — Canonical Comptime 2.0, partial evaluation, specialization & const-vs-static specification (SPEC-60)
phase: P14-comptime-2-0-reflection-genera
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T214]
priority: 170
status: todo
attempts: 0
paths: [spec/SPEC-60-comptime-2-0.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-04-core-extensibility.md, 0102, 0140, tasks/0340, tasks/0346, tasks/0509, tasks/0514]
covers: [REQ-CTM-001, REQ-CTM-002, REQ-CTM-003, REQ-CTM-004, REQ-CTM-005, REQ-CTM-006, REQ-CTM-007, REQ-CTM-012, REQ-CTM-013, REQ-CTM-014, REQ-CTM-015, REQ-CTM-016, REQ-CTM-017, REQ-CTM-018, REQ-CTM-023, REQ-CTM-024, REQ-CTM-025, REQ-CTM-026, REQ-CTM-027, REQ-CTM-028, REQ-CTM-029, REQ-CTM-030, REQ-CTM-031, REQ-CTM-032, REQ-CTM-033, REQ-CTM-034, REQ-CTM-035, REQ-CTM-036, REQ-CTM-037, REQ-CTM-038, REQ-CORE-683, REQ-CORE-684, REQ-CORE-685, REQ-CORE-686, REQ-CORE-687, REQ-CORE-688, REQ-CORE-689, REQ-CORE-690, REQ-CORE-691, REQ-CORE-692, REQ-CORE-693, REQ-CORE-694, REQ-CORE-695, REQ-CORE-696, REQ-CORE-697, REQ-CORE-2130, REQ-CORE-2131, REQ-CORE-2132, REQ-CORE-2133, REQ-CORE-2134, REQ-CORE-2135, REQ-CORE-2136, REQ-CORE-2137, REQ-CORE-2138, REQ-CORE-2139, REQ-CORE-2140, REQ-CORE-2141, REQ-CORE-2142, REQ-CORE-2214, REQ-CORE-2215, REQ-CORE-2216, REQ-CORE-2217, REQ-CORE-2218, REQ-CORE-2219, REQ-CORE-2220, REQ-CORE-2221, REQ-CORE-2222, REQ-CORE-2223, REQ-CORE-2224, REQ-CORE-2225, REQ-CORE-2226, REQ-CORE-2227, REQ-CORE-2228, REQ-CORE-2229, REQ-CORE-2230, REQ-CORE-2231, REQ-CORE-2232, REQ-CORE-2233, REQ-CORE-2234, REQ-CORE-2235, REQ-CORE-2236, REQ-CORE-2237, REQ-CORE-2238, REQ-CORE-2239, REQ-CORE-2240, REQ-CORE-2241, REQ-CORE-2242, REQ-CORE-2243]
---
# T550 — E14.1 — Canonical Comptime 2.0, partial evaluation, specialization & const-vs-static specification (SPEC-60)

## Goal
Consolidate the full Comptime 2.0 execution model, value lifting and resource no-escape contract, partial evaluation and specialization rules, and the semantic boundary between `const`, `static`, and TLS initialization into canonical `spec/SPEC-60-comptime-2-0.md` (`AXS-CTM-*` rule IDs).

## Scope
- Write `spec/SPEC-60-comptime-2-0.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-CTM-NNN` rules.
- Specify the unified semantic principle: `const`, `comptime`, and runtime are evaluation modes of the same Axiom language using identical type, ownership, capability, and `Drop` semantics (`ACOMP2-20..35`, `COMPTIME-20..30`).
- Specify `comptime fn`, `comptime { ... }` blocks, `comptime` parameters, sandboxed authority by default, explicit external comptime capabilities (`env`, `fs`, `time`, tool inputs tracked as build dependencies), and the prohibition on comptime resource handles or raw pointers escaping into runtime values (`AX_CTM_RESOURCE_ESCAPE`).
- Specify partial evaluation, comptime specialization of generic/constant/closure arguments, cross-compilation host-vs-target separation, and dependency-tracked comptime cache identity.
- Specify the semantic distinction and initialization rules for `const` (compile-time value without mandatory storage identity), `static` (program/module-lifetime storage with deterministic initialization), and TLS (`AGLOBAL-20..150`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-60-comptime-2-0.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-CTM-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T550-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or library implementation (handled by `T551`–`T554`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:20:00 created by T214 (P14 phase planning)
