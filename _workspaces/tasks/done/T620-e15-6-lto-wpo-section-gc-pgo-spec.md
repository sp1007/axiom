---
id: T620
title: E15.6 — Canonical LTO, whole-program optimization, section GC & PGO specification (SPEC-75)
phase: P15-optimizer-2-0
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T215, T613]
priority: 114
status: done
attempts: 1
paths: [spec/SPEC-75-lto-wpo-section-gc-pgo.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-04-core-extensibility.md, spec/SPEC-73-inlining-specialization-devirt.md, tasks/0355, tasks/0366, tasks/0408, tasks/0409, tasks/0410, tasks/0580, tasks/0581, tasks/0594, tasks/0595, tasks/0597]
covers: [REQ-OPT-223, REQ-OPT-224, REQ-OPT-225, REQ-OPT-226, REQ-OPT-227, REQ-OPT-228, REQ-OPT-229, REQ-OPT-230, REQ-OPT-231, REQ-OPT-232, REQ-OPT-233, REQ-OPT-234, REQ-OPT-235, REQ-OPT-257, REQ-OPT-258, REQ-OPT-259, REQ-OPT-260, REQ-OPT-261, REQ-OPT-262, REQ-OPT-263, REQ-OPT-264, REQ-OPT-265, REQ-OPT-266, REQ-OPT-267, REQ-OPT-268, REQ-OPT-269, REQ-OPT-270, REQ-OPT-319, REQ-OPT-320]
started: 2026-11-03 05:26:14
finished: 2026-11-03 05:41:14
---
# T620 — E15.6 — Canonical LTO, whole-program optimization, section GC & PGO specification (SPEC-75)

## Goal
Consolidate the canonical specification for Link-Time Optimization (`LTO`), whole-program closed-world reachability (`WPO`), linker section garbage collection (`COMDAT` / dead stripping) and Identical Code Folding (`ICF`), and Profile-Guided Optimization (`PGO`) into `spec/SPEC-75-lto-wpo-section-gc-pgo.md` (`AXS-LTO-*` and `AXS-PGO-*` rule IDs).

## Scope
- Write `spec/SPEC-75-lto-wpo-section-gc-pgo.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-LTO-NNN` / `AXS-PGO-NNN` rules.
- Specify the LTO and whole-program closed-world contract (`ALTO-20..58`, `tasks/0355`, `tasks/0409`): reachability roots (`main` / `@entry`, `@export` symbols, reflection-preserved items, FFI/dynamic-lookup roots), cross-module `OptIR` summaries, cross-module inlining/constant propagation/escape/devirtualization, and generic instance deduplication (`ALTO-30..33`).
- Specify linker section GC (`SPEC-04 AXS-EXT-071` `comdat`, per-function/per-data sectionreachability graph, dead code/data stripping, unused runtime component elimination) and Identical Code Folding (`ICF`) respecting observable function-pointer identity (`tasks/0410`, `tasks/0594`, `tasks/0595`).
- Specify the PGO contract (`tasks/0408`, `tasks/0581`, `tasks/0597`, `REQ-OPT-223..235`, `REQ-OPT-319`): `--pgo-gen` instrumentation and deterministic `--pgo-use=<profile>` consumption, profile provenance/confidence, stale-profile handling, and the hard invariant that profiles affect profitability only and never alter language semantics or fabricate safety/alias/devirtualization proofs.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-75-lto-wpo-section-gc-pgo.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-LTO-NNN` / `AXS-PGO-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T620-report.md` with exact `## Files changed`.

## Out of scope
- Compiler and linker implementation of LTO, section GC, ICF, and PGO (`T621`–`T622`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:43:00 created by T215 (P15 phase planning)
- 2026-11-03 05:26:14 started (attempt 1) 
- 2026-11-03 05:41:14 accepted by QA -> done
