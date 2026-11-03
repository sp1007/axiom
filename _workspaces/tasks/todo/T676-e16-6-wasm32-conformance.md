---
id: T676
title: E16.6 — WASM32 structured CFG, linear memory ownership, .wasm validator & WASI conformance suite
phase: P16-targets-platforms
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T313, T675]
priority: 119
status: todo
attempts: 0
paths: [tests/conformance/p16/e16_6_wasm32]
spec: [spec/SPEC-86-wasm32-backend.md, tasks/0523, tasks/0784]
covers: [REQ-TGT-264, REQ-TGT-265, REQ-TGT-274, REQ-TGT-275, REQ-TGT-276, REQ-TGT-277, REQ-TGT-278, REQ-TGT-279, REQ-TGT-280, REQ-TGT-281, REQ-TGT-283, REQ-TGT-284]
---
# T676 — E16.6 — WASM32 structured CFG, linear memory ownership, .wasm validator & WASI conformance suite

## Goal
Certify the E16.6 exit criterion (`ROADMAP.md` §3): `wasm32` tier-2 target backend conformance across structured/irreducible CFGs, linear-memory shadow stack & capability preservation, `.wasm` binary module/archive emission, internal bytecode validation, and differential agreement with `--interp` and native `x86_64` (`AWASM-20..95`).

## Scope
- Create `tests/conformance/p16/e16_6_wasm32` covering:
  - Control-flow structuring & stackification tests: deeply nested loops with labeled `break`/`continue`, `match` `br_table` switches, early `?` returns with `Drop` cleanup, and irreducible state-machine CFGs.
  - Ownership, `view`/`mut_view`, and `Drop` tests on WASM linear memory: shadow-stack pointer restoration on function return, `memory.grow` heap reallocation without invalidating active views, `call_indirect` closures and `dyn` trait dispatch.
  - Internal WASM bytecode validator negative tests (proving type-mismatched operand stacks, unbalanced blocks, and unavailable WASM features are caught internally before emitting bytes).
  - Reproducible `.wasm` module and WASM object-archive dead-symbol stripping tests, plus WASI execution (`Xin chào thế giới`, args, file I/O) and differential comparison against `--interp`.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p16/e16_6_wasm32` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T676-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation changes (belong in `T674`–`T675`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin chào thế giới` for greeting strings.

## Log
- 2026-11-03 08:41:00 created by T216 (P16 phase planning)
