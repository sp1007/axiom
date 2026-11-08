---
id: T315
title: Phase P15 gate — Optimizer 2.0
phase: P15-optimizer-2-0
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T215, T063, T064, T600, T601, T602, T603, T604, T605, T606, T607, T608, T609, T610, T611, T612, T613, T614, T615, T616, T617, T618, T619, T620, T621, T622, T623, T624, T625, T626, T627, T628, T629]
priority: 315
status: done
attempts: 1
paths: [tests/conformance/p15, _workspaces/reports/phase-P15-review.md]
spec: [spec/ROADMAP.md, spec/SPEC-70-optir-ssa-memoryssa.md, spec/SPEC-71-alias-escape-promotion.md, spec/SPEC-72-loops-scev-bce.md, spec/SPEC-73-inlining-specialization-devirt.md, spec/SPEC-74-auto-vectorization.md, spec/SPEC-75-lto-wpo-section-gc-pgo.md, spec/SPEC-76-performance-contract.md, spec/SPEC-77-regalloc-machine-opt.md]
started: 2026-11-08 17:06:48
finished: 2026-11-08 17:46:15
---
# T315 — Phase P15 gate: Optimizer 2.0

## Goal
Certify that phase P15 meets the exit criteria of every epic (`E15.1`–`E15.8`) in `spec/ROADMAP.md` §3 (`differential green at -O2; benchmark targets met and tracked in CI`) and that all requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks (`e15_1_optir_ssa`, `e15_2_alias_escape`, `e15_3_loops_bce`, `e15_4_inline_specialize_devirt`, `e15_5_autovec`, `e15_6_lto_pgo_gc`, `e15_7_perf_contract`, `e15_8_regalloc_isel`).
- `reqcov.py --phase P15-optimizer-2-0`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p15` (index + missing cases added).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion demonstrated with commands and results in the QA report.
- [ ] Full suite green (gate rule: PASS or BLOCKED; only `xfail` entries for spec gaps with an ADR may remain); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T315-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T215 and all 32 phase P15 tasks (`T063`, `T064`, `T600`–`T629`).

## Log
- 2026-11-03 02:45:00 wired all P15 tasks (`T063`, `T064`, `T600`–`T629`) into `depends:` in T215
- 2026-11-08 17:06:48 started (attempt 1) T315-impl
- 2026-11-08 17:46:15 accepted by QA -> done
