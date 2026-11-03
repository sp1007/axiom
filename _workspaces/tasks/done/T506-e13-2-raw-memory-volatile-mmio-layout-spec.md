---
id: T506
title: E13.2 — Canonical raw memory, volatile, MMIO, unions, packed/aligned repr & address spaces specification (SPEC-51)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T213]
priority: 155
status: done
attempts: 1
paths: [spec/SPEC-51-raw-memory-volatile-mmio-layout.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-04-core-extensibility.md, spec/decisions/ADR-0001-fixed-address-declarations.md, 0067, 0072, tasks/0328, tasks/0515]
covers: [REQ-ABI-063, REQ-CORE-449, REQ-FFI-099, REQ-RES-136, REQ-CAP-130, REQ-CAP-152]
started: 2026-11-03 09:22:25
finished: 2026-11-03 09:44:20
---
# T506 — E13.2 — Canonical raw memory, volatile, MMIO, unions, packed/aligned repr & address spaces specification (SPEC-51)

## Goal
Specify raw memory access semantics, volatile load/store/fence guarantees, MMIO register wrappers (`Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, `MmioWO<T>`), untagged `union` types (`0072`), `@repr(packed)` / `@align(N)` layout rules, bitcast preconditions, and target address spaces in `spec/SPEC-51-raw-memory-volatile-mmio-layout.md` (`AXS-MEM-*` rule IDs).

## Scope
- Write `spec/SPEC-51-raw-memory-volatile-mmio-layout.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-MEM-NNN` rules.
- Specify `volatile_load`, `volatile_store`, `volatile_copy`, and hardware memory barriers: exact instruction width, non-elision, non-reordering across volatile accesses, and rejection of tearing on naturally aligned scalar/MMIO widths (`1`, `2`, `4`, `8` bytes).
- Specify `Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, and `MmioWO<T>` field wrappers that lower ordinary field reads/writes (`regs.ctrl = v`) to single-width volatile operations (`ADR-0001 §2`).
- Specify untagged `union` declarations (`0072`): `Copy`-only or `ManuallyDrop<T>` fields, `unsafe` field reads, safe field writes, `@repr(C)` layout, and pattern matching rules.
- Specify `@repr(packed)`, `@repr(packed(N))`, `@align(N)`, unaligned field projection rules (forbidding direct `view<T>`/`mut_view<T>` or aligned pointer creation to unaligned packed fields), bitcast validity, and explicit address-space qualifiers.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-51-raw-memory-volatile-mmio-layout.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-MEM-NNN` rules, positive/negative canonical Axiom examples, and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T506-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or std implementation (handled by `T507`–`T509`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:01:00 created by T213 (P13 phase planning)
- 2026-11-03 09:22:25 started (attempt 1) 
- 2026-11-03 09:44:20 accepted by QA -> done
