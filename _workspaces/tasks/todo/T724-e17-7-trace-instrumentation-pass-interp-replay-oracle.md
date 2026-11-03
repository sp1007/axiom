---
id: T724
title: E17.7 Compiler trace instrumentation pass & host/syscall/scheduler non-determinism boundary capture
phase: P17-debugging-runtime-introspectio
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T217, T316, T723]
priority: 195
status: todo
attempts: 0
paths: [compiler/instrument/trace, compiler/interp/replay, tests/selfhost/debug/replay]
spec: [spec/SPEC-98-trace-replay.md, 0147, tasks/1058]
covers: [REQ-DBG-116, REQ-DBG-121]
---
# T724 — E17.7 Compiler trace instrumentation pass & host/syscall/scheduler non-determinism boundary capture

## Goal
Implement the compiler --trace instrumentation pass for non-deterministic boundary events and the MIR interpreter time-travel record/replay oracle.

## Scope
- Implement `compiler/instrument/trace` emitting boundary capture/replay hooks at host intrinsics, FFI calls, atomic/synchronization operations, and async task poll boundaries when `--trace` is enabled, with zero codegen impact when disabled (`0147 §20`).
- Implement `compiler/interp/replay` adding deterministic event recording, replay injection, checkpoint snapshots, `reverse-step`/`reverse-continue`, and memory `last-writer` provenance queries to the MIR interpreter oracle.
- Add selfhost unit tests in `tests/selfhost/debug/replay`.

## Acceptance
- [ ] `axiomc` with `--trace` instruments boundary events while builds without `--trace` are byte-identical to baseline builds.
- [ ] The MIR interpreter replay engine records and deterministically replays execution traces and supports `reverse-step` and `last-writer` queries in `tests/selfhost/debug/replay`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T724-report.md` with exact `## Files changed`.

## Out of scope
- Native `std.replay` runtime and `axiomc replay` CLI (`T725`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
