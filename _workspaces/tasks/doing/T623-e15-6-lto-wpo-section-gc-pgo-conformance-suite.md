---
id: T623
title: E15.6 — LTO, whole-program optimization, section GC & PGO conformance suite
phase: P15-optimizer-2-0
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T622]
priority: 117
status: doing
attempts: 1
paths: [tests/conformance/p15/e15_6_lto_pgo_gc]
spec: [spec/SPEC-75-lto-wpo-section-gc-pgo.md, tasks/0355, tasks/0408, tasks/0409, tasks/0410]
covers: [REQ-OPT-246, REQ-OPT-247, REQ-OPT-248, REQ-OPT-249, REQ-OPT-250]
started: 2026-11-08 03:24:43
agent: T623-impl
---
# T623 — E15.6 — LTO, whole-program optimization, section GC & PGO conformance suite

## Goal
Certify E15.6 exit criteria with an end-to-end differential conformance suite covering multi-module `--lto`, whole-program dead-code/data section GC, safe `ICF`, and `--pgo-gen` / `--pgo-use` determinism and safety boundaries.

## Scope
- Create differential conformance tests in `tests/conformance/p15/e15_6_lto_pgo_gc` verifying:
  - multi-module `--lto` inlining, specialization, and generic deduplication with exact `--interp` vs native equivalence;
  - section GC stripping of unreferenced functions/tables while preserving `@export`, FFI, and address-compared functions under `ICF`;
  - `--pgo-gen` → training run → `--pgo-use` round-trip determinism, stale-profile resilience, and strict preservation of security, atomic, `volatile`, and FFI contracts (`REQ-OPT-246..250`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p15/e15_6_lto_pgo_gc` pass in `--interp` and native `-O0`/`-O2`/`--lto`/`--pgo-use` modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T623-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T623/build` and `python tools/axtest.py --compiler build-snap-T623/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:43:00 created by T215 (P15 phase planning)
- 2026-11-08 03:24:43 started (attempt 1) T623-impl
