---
id: T528
title: E13.6 — COFF/PE absolute symbols, pinned VMA sections & freestanding raw-binary image writer for @at / @addr
phase: P13-low-level-systems-unsafe-frees
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T504, T513, T526]
priority: 177
status: todo
attempts: 0
paths: [compiler/lir, compiler/target/x64, compiler/obj, compiler/link, tests/link/fixed_addr]
spec: [spec/SPEC-55-fixed-address-declarations.md, spec/decisions/ADR-0001-fixed-address-declarations.md, 0071, 0097, tasks/0328]
covers: [REQ-OWNER-008, REQ-OWNER-003]
---
# T528 — E13.6 — COFF/PE absolute symbols, pinned VMA sections & freestanding raw-binary image writer for @at / @addr

## Goal
Emit COFF absolute symbols (`IMAGE_SYM_ABSOLUTE`) for `@at`/`@addr` overlays, pinned VMA sections for `@at`/`@addr` placements, cross-object linker overlap diagnostics, and freestanding raw-binary/PE images (`ADR-0001 §4`, `REQ-OWNER-003`, `REQ-OWNER-008`).

## Scope
- Emit `IMAGE_SYM_ABSOLUTE` (`SectionNumber = -1`) symbols in `compiler/obj` for constant `@at`/`@addr` overlays and emit per-item pinned sections with explicit VMA requirements for `@at`/`@addr` placements (`static` and `fn`).
- Lower dynamic `@addr(expr)` bindings (`let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32;`) and fixed-address function calls/loads/stores in `compiler/lir` and `compiler/target/x64`.
- Teach `compiler/link` to honour pinned section VMAs, detect cross-module address overlaps, emit `--format bin` raw binary freestanding images alongside PE images, and verify via `objdump` and runtime `addr_of`/`fn_addr`/`static_addr` checks that every placed item resides at its declared address.

## Acceptance
- [ ] Link, `objdump`, and native execution tests in `tests/link/fixed_addr` verify `IMAGE_SYM_ABSOLUTE` symbols, pinned VMA section placement, cross-object overlap rejection, raw binary output, and native `fn_addr(isr) == 0x2000_0000usize` / `static_addr` / `address_of` round-trip equality.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T528-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T528/build` and `python tools/axtest.py --compiler build-snap-T528/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:05:00 created by T213 (P13 phase planning)
