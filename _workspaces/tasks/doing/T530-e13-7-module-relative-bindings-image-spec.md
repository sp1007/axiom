---
id: T530
title: E13.7 — Canonical module-relative bindings (@at(image("mod") + off), image_self()) specification (SPEC-56)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T525]
priority: 179
status: doing
attempts: 1
paths: [spec/SPEC-56-module-relative-bindings.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/decisions/ADR-0001-fixed-address-declarations.md, spec/SPEC-55-fixed-address-declarations.md, 0187, 0104, tasks/0336]
covers: [REQ-OWNER-005, REQ-ABI-032, REQ-ABI-033, REQ-ABI-095]
started: 2026-11-03 11:29:16
---
# T530 — E13.7 — Canonical module-relative bindings (@at(image("mod") + off), image_self()) specification (SPEC-56)

## Goal
Finalise `ADR-0001 §5–6` (`REQ-OWNER-005`) into canonical `spec/SPEC-56-module-relative-bindings.md` (`AXS-MOD-*` rule IDs), specifying `@at(image("mod") + offset)` and `@at(image_self() + offset)` load-time resolved overlays in the hosted profile, slot-based indirect dispatch, and DLL/EXE initialiser failure semantics.

## Scope
- Write `spec/SPEC-56-module-relative-bindings.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-MOD-NNN` rules.
- Specify `image("name") -> usize` and `image_self() -> usize` address expressions inside `@at(...)` / `@addr(...)` overlay declarations (`static`, `static mut`, `extern "C" fn`) in the `hosted` profile (`REQ-OWNER-005`).
- Specify the overlay-only restriction (never placement into a foreign module), alignment and `@repr(C)` layout verification, open-world optimization barriers across dynamically loaded module symbols (`REQ-ABI-095`), and the separation of dynamic linking from hot reload (`REQ-ABI-032`, `REQ-ABI-033`).
- Specify load-time slot resolution during module initialization (before any user code runs): Windows `GetModuleHandleW` lookup for `image("name")`, `__ImageBase` for `image_self()`, and deterministic init failure when a target module is not loaded in the process (`DllMain` returns `FALSE` in a DLL; startup panic in an EXE — never calling through an unresolved zero/null slot).
- Specify the oracle (`--interp`) simulated process module map for testing `image("mod") + offset` and `image_self() + offset` overlays.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-56-module-relative-bindings.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-MOD-NNN` rules, positive/negative canonical Axiom examples, and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T530-report.md` with exact `## Files changed`.

## Out of scope
- Compiler/linker implementation (handled by `T531`–`T532`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:06:00 created by T213 (P13 phase planning)
- 2026-11-03 11:29:16 started (attempt 1) 
