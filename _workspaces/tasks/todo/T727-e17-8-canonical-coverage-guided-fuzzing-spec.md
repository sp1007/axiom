---
id: T727
title: E17.8 — Canonical specification for coverage-guided and structure-aware fuzzing (SPEC-99)
phase: P17-debugging-runtime-introspectio
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T217, T316]
priority: 198
status: todo
attempts: 0
paths: [spec/SPEC-99-coverage-guided-fuzzing.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-99-coverage-guided-fuzzing.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-TST-013, REQ-CNF-006]
---
# T727 — E17.8 — Canonical specification for coverage-guided and structure-aware fuzzing (SPEC-99)

## Goal
Consolidate the canonical specification for coverage-guided, structure-aware fuzzing in Axiom into `spec/SPEC-99-coverage-guided-fuzzing.md` (`AXS-FUZZ-*` rule IDs).

## Scope
- Write `spec/SPEC-99-coverage-guided-fuzzing.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-FUZZ-NNN` rules.
- Specify compile-time edge coverage instrumentation (`-fsanitize-coverage=trace-pc-guard`) recording branch/edge visits into a shared-memory 64 KiB coverage bitmap without allocating heap memory inside instrumented code.
- Specify the multi-process crash-isolated fuzzing engine: coordinator process managing corpus generation, power schedules, and mutation queues, while isolated worker processes execute target harnesses.
- Specify `@derive(Arbitrary)` integration leveraging compile-time reflection (`TypeInfo` from P14) to generate recursive, typed, valid AST/protocol input structures from raw byte streams.
- Specify `axiom test --fuzz` CLI driver, corpus persistence format in `fuzz/corpus/`, deterministic crash artifact minimization, and automatic reproduction via `< 1.0s` unit regression tests.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-99-coverage-guided-fuzzing.md` exists with Vietnamese `## Tóm tắt`, numbered `AXS-FUZZ-NNN` rules, positive/negative examples, and diagnostic references.
- [ ] `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T727-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the fuzzing runtime or compiler passes (`T728`–`T730`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T727/build` and `python tools/axtest.py --compiler build-snap-T727/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:15:00 created by axiom-architect (ADR-0039 P17 coverage fuzzing expansion)
