---
id: T624
title: E15.7 — Canonical performance contract, benchmark suite & compile-time/code-size budget specification (SPEC-76)
phase: P15-optimizer-2-0
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T215, T600]
priority: 118
status: done
attempts: 1
paths: [spec/SPEC-76-performance-contract.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-20-selfhost.md, spec/SPEC-70-optir-ssa-memoryssa.md, 0074, tasks/0355, tasks/0366, tasks/0408, tasks/0595, tasks/0706]
covers: [REQ-OPT-292, REQ-OPT-293, REQ-OPT-294, REQ-OPT-295, REQ-OPT-334, REQ-OPT-381, REQ-OPT-382]
started: 2026-11-03 05:41:29
finished: 2026-11-03 05:55:23
---
# T624 — E15.7 — Canonical performance contract, benchmark suite & compile-time/code-size budget specification (SPEC-76)

## Goal
Consolidate the canonical specification for Axiom's runtime performance contract, canonical benchmark suite, compile-time and binary code-size/working-set budgets, optimization profiles (`-O0`, `-O1`, `-O2`, `-Os`/`-Oz`), and CI regression gates into `spec/SPEC-76-performance-contract.md` (`AXS-PERF-*` rule IDs).

## Scope
- Write `spec/SPEC-76-performance-contract.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-PERF-NNN` rules.
- Specify optimization level contracts (`-O0` fast compile + debuggability, `-O1` balanced local + linear-scan regalloc, `-O2` full `OptIR` + loop/inline/vectorize, `-Os`/`-Oz` code-sharing and dead stripping — `REQ-OPT-292..295`, `REQ-OPT-334`) and the invariant that all optimization profiles preserve identical core language semantics (`0074`, `tasks/0706`).
- Specify binary footprint metrics (`REQ-OPT-381`, `REQ-OPT-382`): on-disk image bytes, mapped `.text`/`.rdata`/`.data`/`.bss` working set, startup latency, and zero-monolithic-runtime overhead.
- Specify the canonical benchmark corpus (`tools/bench`), `--time-passes` / `--size-report` machine-readable JSON telemetry, and hard CI regression budgets (compile time, self-compile speed, runtime throughput, and binary size).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-76-performance-contract.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-PERF-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T624-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of telemetry flags and benchmark harness (`T625`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:44:00 created by T215 (P15 phase planning)
- 2026-11-03 05:41:29 started (attempt 1) 
- 2026-11-03 05:55:23 accepted by QA -> done
