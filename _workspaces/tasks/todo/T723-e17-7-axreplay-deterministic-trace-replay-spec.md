---
id: T723
title: E17.7 Canonical AXREPLAY deterministic execution recording, event log & time-travel replay specification (SPEC-98)
phase: P17-debugging-runtime-introspectio
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T217, T316, T711]
priority: 194
status: todo
attempts: 0
paths: [spec/SPEC-98-trace-replay.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-95-debugger-contract-symbolication.md, 0147, tasks/1058, tasks/0694]
covers: [REQ-DBG-116, REQ-DBG-121]
---
# T723 — E17.7 Canonical AXREPLAY deterministic execution recording, event log & time-travel replay specification (SPEC-98)

## Goal
Consolidate the canonical specification for AXREPLAY deterministic execution recording, .axtrace event logs, state checkpoints, and time-travel debugging into spec/SPEC-98-trace-replay.md (AXS-RPLY-* rules).

## Scope
- Write `spec/SPEC-98-trace-replay.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-RPLY-NNN` rules.
- Specify the `AXREPLAY` determinism contract (`tasks/1058 §1–19`, `0147 §20`): zero runtime overhead when disabled, recording modes (`Minimal`, `Standard`, `Debug`, `Full`), and strict separation between deterministic pure computation and recorded non-deterministic boundary events.
- Specify the event classes and total logical ordering (`1058 §12–19`): thread/fiber/task schedule transitions, mutex/channel/atomic synchronization order, clock/monotonic timer reads, RNG outputs, filesystem/socket I/O completions, and FFI boundary return values.
- Specify the compact `.axtrace` binary container format, periodic memory/register snapshot checkpoints, divergence detection (`AXREPLAY_DIVERGENCE` diagnostic if replayed code mismatches recorded event sequence), and time-travel debugging queries (`reverse-step`, `reverse-next`, `reverse-continue`, and watchpoint `last-writer` provenance query).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-98-trace-replay.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-RPLY-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T723-report.md` with exact `## Files changed`.

## Out of scope
- Compiler trace instrumentation and `std.replay` implementation (`T724`, `T725`, `T726`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
