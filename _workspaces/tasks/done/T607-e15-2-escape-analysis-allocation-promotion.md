---
id: T607
title: E15.2 — Escape analysis (NoEscape/ArgEscape/ReturnEscape/GlobalEscape) & stack/register allocation promotion
phase: P15-optimizer-2-0
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T606]
priority: 100
status: done
attempts: 1
paths: [compiler/opt/escape, tests/run/opt_escape]
spec: [spec/SPEC-71-alias-escape-promotion.md, 0131, 0162, 0165, tasks/0366, tasks/0397, tasks/0480]
covers: [REQ-OPT-042, REQ-OPT-043, REQ-OPT-044, REQ-OPT-045, REQ-OPT-046, REQ-OPT-335, REQ-OPT-336, REQ-OPT-345, REQ-OPT-346, REQ-OPT-357]
started: 2026-11-05 18:04:26
finished: 2026-11-06 06:37:06
---
# T607 — E15.2 — Escape analysis (NoEscape/ArgEscape/ReturnEscape/GlobalEscape) & stack/register allocation promotion

## Goal
Implement interprocedural-summary-aware escape analysis and automatic storage promotion (heap-to-stack and stack-to-register promotion for non-escaping allocations, closures, and bounded containers) in `compiler/opt/escape` per `spec/SPEC-71-alias-escape-promotion.md`.

## Scope
- Compute `EscapeInfo` (`NoEscape`, `ArgumentEscape`, `ReturnEscape`, `GlobalEscape` — `REQ-OPT-042..046`, `REQ-OPT-357`) over `OptIR` places, closure capture environments, `Box` allocations, and bounded collection buffers.
- Promote `NoEscape` heap allocations and closure environments to stack locals or SSA registers (`REQ-OPT-335`, `REQ-OPT-336`, `REQ-OPT-345`, `REQ-OPT-346`) while preserving deterministic `Drop` execution on scope exit.
- Respect address observability (`address_of`, `address_of_mut`, `@at`, FFI pointer escape, thread spawn escape) as hard barriers against storage promotion or relocation.

## Acceptance
- [ ] Differential run and `OptIR` dump tests in `tests/run/opt_escape` verify promotion of `NoEscape` `Box`/closure/buffer allocations to stack/registers, retention of escaping allocations, and exact `Drop` ordering parity between `--interp` and native `-O2`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T607-report.md` with exact `## Files changed`.

## Out of scope
- Loop optimizations (`E15.3`) and interprocedural inlining/devirtualization (`E15.4`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T607/build` and `python tools/axtest.py --compiler build-snap-T607/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:39:00 created by T215 (P15 phase planning)
- 2026-11-05 18:04:26 started (attempt 1) T607-impl
- 2026-11-06 06:37:06 accepted by QA -> done
