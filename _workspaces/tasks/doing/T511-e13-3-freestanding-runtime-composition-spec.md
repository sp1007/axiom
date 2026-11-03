---
id: T511
title: E13.3 — Canonical runtime composition, hosted vs freestanding profiles, @entry & capability graph specification (SPEC-52)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T213]
priority: 160
status: doing
attempts: 1
paths: [spec/SPEC-52-freestanding-runtime-composition.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-04-core-extensibility.md, 0143, 0097, tasks/0358, tasks/0359, tasks/0370, tasks/0455]
covers: [REQ-ABI-031, REQ-ABI-102]
started: 2026-11-03 10:00:49
---
# T511 — E13.3 — Canonical runtime composition, hosted vs freestanding profiles, @entry & capability graph specification (SPEC-52)

## Goal
Specify Axiom's modular runtime composition model, `hosted`, `freestanding`, `kernel`, and `system` profiles, `@entry` / `@panic_handler` / `@global_allocator` / `@naked` / `@section` / `@used` attributes, interrupt calling conventions, and the runtime capability graph in `spec/SPEC-52-freestanding-runtime-composition.md` (`AXS-FRE-*` rule IDs).

## Scope
- Write `spec/SPEC-52-freestanding-runtime-composition.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-FRE-NNN` rules.
- Specify compilation profiles (`--profile hosted|freestanding|kernel|system`): available standard library layers (`std.core` without OS/heap vs `std.alloc` vs full `std`), absence of implicit CRT/OS runtime dependencies in `freestanding`, and static initialization ordering rules.
- Specify `@entry`, `@panic_handler`, `@naked`, `@section("...")`, `@used`, `@no_mangle`, and hardware interrupt handler calling conventions (`extern "interrupt"`, prohibition of implicit heap allocation, blocking, or `await` inside interrupt handlers per `REQ-ABI-102`).
- Specify the compile-time runtime capability graph that tracks which runtime services (heap allocator, thread scheduler, async reactor, unwinder, OS I/O) are transitively required by a binary and rejects forbidden runtime services in `freestanding` and `kernel` profiles.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-52-freestanding-runtime-composition.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-FRE-NNN` rules, positive/negative canonical Axiom examples, and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T511-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or std implementation (handled by `T512`–`T514`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:02:00 created by T213 (P13 phase planning)
- 2026-11-03 10:00:49 started (attempt 1) 
