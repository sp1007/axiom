---
id: T608
title: E15.2 — Alias analysis, escape analysis & allocation promotion conformance suite
phase: P15-optimizer-2-0
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T607]
priority: 101
status: todo
attempts: 0
paths: [tests/conformance/p15/e15_2_alias_escape]
spec: [spec/SPEC-71-alias-escape-promotion.md, 0226, tasks/0366, tasks/0395, tasks/0397, tasks/0615]
covers: [REQ-OPT-307, REQ-OPT-308, REQ-OPT-309, REQ-OPT-310, REQ-OPT-385, REQ-OPT-386]
---
# T608 — E15.2 — Alias analysis, escape analysis & allocation promotion conformance suite

## Goal
Certify E15.2 exit criteria with an end-to-end differential conformance suite covering capability-driven alias analysis, `MemorySSA` store-to-load/DSE optimization, escape analysis, closure capture promotion, and caller-allocated return-slot optimization.

## Scope
- Create differential conformance tests in `tests/conformance/p15/e15_2_alias_escape` verifying:
  - store-to-load forwarding and DSE with disjoint `mut_view<T>` and `view<T>` capabilities vs conservative raw-pointer `MayAlias` preservation;
  - stack/register promotion of non-escaping `Box`, closure environments (`REQ-OPT-385`, `REQ-OPT-386`), and temporary buffers (`REQ-OPT-307`, `REQ-OPT-309`);
  - preservation of stable-address observation (`address_of` / `@at`, `REQ-OPT-308`) and caller-allocated return slots (`REQ-OPT-310`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p15/e15_2_alias_escape` pass in `--interp` and native `-O0`/`-O1`/`-O2` modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T608-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T608/build` and `python tools/axtest.py --compiler build-snap-T608/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:39:00 created by T215 (P15 phase planning)
