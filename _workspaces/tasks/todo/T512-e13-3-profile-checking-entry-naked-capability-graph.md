---
id: T512
title: E13.3 — Profile checking (--profile freestanding|kernel|system|hosted), @entry/@naked/@section & runtime capability graph
phase: P13-low-level-systems-unsafe-frees
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T511]
priority: 161
status: todo
attempts: 0
paths: [compiler/driver, compiler/hir, compiler/types, tests/ui/freestanding]
spec: [spec/SPEC-52-freestanding-runtime-composition.md, 0143, 0097, tasks/0358, tasks/0359, tasks/0455]
covers: [REQ-ABI-102, REQ-ABI-031]
---
# T512 — E13.3 — Profile checking (--profile freestanding|kernel|system|hosted), @entry/@naked/@section & runtime capability graph

## Goal
Implement `--profile hosted|freestanding|kernel|system` CLI/manifest selection, `@entry` / `@panic_handler` / `@naked` / `@section` / `@used` semantic checking, interrupt-domain restrictions (`REQ-ABI-102`), and the compile-time runtime capability graph in `compiler/driver` and `compiler/types`.

## Scope
- Add `--profile hosted|freestanding|kernel|system` to `compiler/driver` and `axiom.toml` target configuration.
- Validate `@entry`, `@panic_handler`, `@naked`, `@section("...")`, `@used`, and `extern "interrupt"` fn attributes in `compiler/types`.
- Build the call-graph runtime capability verifier: reject implicit heap allocation, thread spawning, blocking OS calls, or `await` inside `extern "interrupt"` handlers (`REQ-ABI-102`) and reject hosted OS/runtime imports under `--profile freestanding`.

## Acceptance
- [ ] Positive and negative UI tests in `tests/ui/freestanding` verify `--profile freestanding` rejection of hosted OS modules, `extern "interrupt"` allocation/blocking rejection (`REQ-ABI-102`), and `@entry`/`@naked`/`@section` validation.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T512-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T512/build` and `python tools/axtest.py --compiler build-snap-T512/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:02:00 created by T213 (P13 phase planning)
