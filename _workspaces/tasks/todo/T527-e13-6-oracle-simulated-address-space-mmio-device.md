---
id: T527
title: E13.6 — Oracle simulated address space & scriptable MMIO/UART/vector-table device model for @at / @addr
phase: P13-low-level-systems-unsafe-frees
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T502, T526]
priority: 176
status: todo
attempts: 0
paths: [compiler/interp, tests/run/fixed_addr_oracle]
spec: [spec/SPEC-55-fixed-address-declarations.md, spec/decisions/ADR-0001-fixed-address-declarations.md, 0071, 0097, tasks/0328]
covers: [REQ-OWNER-008, REQ-OWNER-003]
---
# T527 — E13.6 — Oracle simulated address space & scriptable MMIO/UART/vector-table device model for @at / @addr

## Goal
Implement the MIR oracle (`--interp`) simulated physical/virtual address space and scriptable MMIO device model so freestanding and low-level programs using `@at` / `@addr` vector tables, ROM callbacks, and UART registers run deterministically under the oracle without hardware (`ADR-0001 §4`).

## Scope
- Add a sparse simulated address-space map to `compiler/interp` backing `@at` and `@addr` overlays and placements at their exact `usize` addresses.
- Verify that `fn_addr(f)`, `static_addr(s)`, `addr_of(v)`, and `address_of(v) as usize` return the exact declared or dynamically computed `@at`/`@addr` address (`fn_addr(isr) == 0x2000_0000usize`, `static_addr(REG) == base + 0x100`), and that calling a function pointer or `@at` function at that address dispatches to the placed/hooked function in `--interp`.
- Implement a deterministic MMIO device model (including a simulated UART status/tx/rx register block and interrupt vector table trigger) for `--interp` tests.

## Acceptance
- [ ] Oracle tests in `tests/run/fixed_addr_oracle` execute a simulated `@at` vector table, ROM function overlay, UART register polling/transmit loop (`UART0.status`, `UART0.data`), and dynamic `@addr(base + 0x100)` placement, verifying exact trace output and `REQ-OWNER-008` round-trip address equality.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T527-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T527/build` and `python tools/axtest.py --compiler build-snap-T527/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:05:00 created by T213 (P13 phase planning)
