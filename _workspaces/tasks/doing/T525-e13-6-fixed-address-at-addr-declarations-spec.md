---
id: T525
title: E13.6 — Canonical fixed-address declarations (@at / @addr) & address introspection specification (SPEC-55)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T500, T506, T511]
priority: 174
status: doing
attempts: 1
paths: [spec/SPEC-55-fixed-address-declarations.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/decisions/ADR-0001-fixed-address-declarations.md, spec/SPEC-50-unsafe-ub-ffi.md, spec/SPEC-51-raw-memory-volatile-mmio-layout.md, spec/SPEC-52-freestanding-runtime-composition.md, 0071, 0044, 0097, tasks/0328]
covers: [REQ-OWNER-008, REQ-OWNER-003]
started: 2026-11-03 11:07:34
---
# T525 — E13.6 — Canonical fixed-address declarations (@at / @addr) & address introspection specification (SPEC-55)

## Goal
Finalise `ADR-0001` §1–4 & §7 (`REQ-OWNER-003`, `REQ-OWNER-008`) into canonical `spec/SPEC-55-fixed-address-declarations.md` (`AXS-ADR-*` rule IDs), specifying `@at(addr)` and `@addr(expr)` overlay and placement declarations for statics, arrays, structs, locals, and functions, ordinary-syntax MMIO register access, overlap/alignment verification, pinned linker sections, and the oracle simulated address space.

## Scope
- Write `spec/SPEC-55-fixed-address-declarations.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-ADR-NNN` rules.
- Specify `@at(<expr>)` and `@addr(<expr>)` placement kinds (`ADR-0001 §1`):
  - **Overlay** (no initializer on `static` / `static mut` / `let` or bodyless `extern fn`): binds the symbol to an existing memory/MMIO/ROM address without emitting storage.
  - **Placement** (initializer on `static` / `static mut` or body on `fn`): emits data/code into a pinned VMA section at that address (vector tables, reset handlers, firmware headers).
- Specify ordinary-syntax usage after an `unsafe` fixed-address declaration (`ADR-0001 §2`): direct field loads/stores (`UART0.ctrl = UartCtrl.ENABLE`), array indexing (`VECTORS[3]`), function calls (`rom_crc32(...)`), and `view`/`mut_view` creation with `fixed` provenance, where `Volatile<T>`/`Mmio<T>`/`MmioRO<T>`/`MmioWO<T>` fields automatically lower to exact-width volatile accesses.
- Specify **`REQ-OWNER-008`** address introspection (`fn_addr(f) -> usize`, `static_addr(s) -> usize`, `addr_of(place) -> usize`, `address_of(v) as usize`, `address_of_mut(v) as usize`, `fn as usize`), dynamic address expressions (`let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32;`), and round-trip address equality (`fn_addr(isr) == 0x2000_0000usize`).
- Specify compile-time alignment, `@repr(C)`/primitive layout, intra-module and linker-wide overlap detection, profile rules (`freestanding`/`kernel`/`system` vs `hosted` mapped regions), COFF `IMAGE_SYM_ABSOLUTE` / ELF `SHN_ABS` symbols, pinned sections, freestanding raw-binary output, and the oracle scriptable device model.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-55-fixed-address-declarations.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-ADR-NNN` rules, positive/negative canonical Axiom examples, and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T525-report.md` with exact `## Files changed`.

## Out of scope
- Compiler/linker implementation (handled by `T526`–`T528`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:05:00 created by T213 (P13 phase planning)
- 2026-11-03 11:07:34 started (attempt 1) 
