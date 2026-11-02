---
id: T521
title: E13.5 — Canonical panic strategy (abort vs unwind), FFI no-unwind barrier & drop cleanup specification (SPEC-54)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T213]
priority: 170
status: todo
attempts: 0
paths: [spec/SPEC-54-panic-unwinding.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md, spec/SPEC-12-drop.md]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-12-drop.md, 0229, tasks/0351, tasks/0700]
covers: [REQ-FFI-004, REQ-FFI-010, REQ-FFI-019, REQ-FFI-023, REQ-FFI-041, REQ-FFI-061, REQ-FFI-093, REQ-ABI-096, REQ-FFI-125, REQ-ABI-105]
---
# T521 — E13.5 — Canonical panic strategy (abort vs unwind), FFI no-unwind barrier & drop cleanup specification (SPEC-54)

## Goal
Specify Axiom's per-profile panic strategy (`--panic abort|unwind`), deterministic `Drop` cleanup guarantees across stack unwinding, `catch_unwind`, `@no_panic` verification, and the mandatory no-unwind abort barrier across `extern "C"` FFI boundaries in `spec/SPEC-54-panic-unwinding.md` (`AXS-PAN-*` rule IDs).

## Scope
- Write `spec/SPEC-54-panic-unwinding.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-PAN-NNN` rules.
- Specify `--panic abort` (default in `freestanding`/`kernel` profiles) vs `--panic unwind` (hosted recovery at thread/task boundaries via `std.panic.catch_unwind`).
- Specify the strict FFI boundary invariant (`REQ-FFI-004`, `REQ-FFI-010`, `REQ-FFI-019`, `REQ-FFI-023`, `REQ-ABI-096`, `REQ-ABI-105`): an Axiom panic must NEVER unwind across an `extern "C"` boundary by default; reaching an `extern "C"` frame boundary during unwinding triggers an immediate deterministic abort (or explicit error-code adapter when declared).
- Specify `Drop` cleanup order during unwinding (reverse declaration order of live initialized locals, double-panic immediate abort) and `@no_panic` call-graph verification.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md`, and cross-reference `spec/SPEC-12-drop.md`.

## Acceptance
- [ ] `spec/SPEC-54-panic-unwinding.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-PAN-NNN` rules, positive/negative canonical Axiom examples, and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T521-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or std implementation (handled by `T522`–`T523`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:04:00 created by T213 (P13 phase planning)
