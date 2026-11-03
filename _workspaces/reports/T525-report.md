# T525 — E13.6 — Canonical fixed-address declarations (`@at` / `@addr`) & address introspection specification (`SPEC-55`)

## Summary
- Authored `spec/SPEC-55-fixed-address-declarations.md` (`AXS-ADR-001`..`053`) starting with a Vietnamese `## Tóm tắt` section, finalizing `ADR-0001` §1–4 & §7 (`REQ-OWNER-003`, `REQ-OWNER-008`, `REQ-OWNER-001`..`005`) for Epic `E13.6` (`T526`–`T529`):
  - **Overlay vs Placement (`AXS-ADR-001`..`003`)**: Canonicalized `@at(<expr>)` and `@addr(<expr>)` on `static`, `static mut`, `let`, `fn`, and `extern fn`, distinguishing **Overlay** (no initializer or bodyless `extern fn`, binding the symbol directly to an existing MMIO/ROM/bootloader address with zero emitted storage) from **Placement** (initializer `= init` on `static`/`let` or body `{ ... }` on `fn`, emitting data or code into a pinned VMA section `.at.text.<name>`, `.at.data.<name>`, or `.at.rdata.<name>`).
  - **Ordinary-Syntax Usage & Automatic Volatile/MMIO Lowering (`AXS-ADR-004`..`005`)**: Specified that `unsafe` on the fixed-address declaration is the single trust boundary; subsequent uses use ordinary Axiom syntax (`UART0.ctrl = UartCtrl.ENABLE`, `while (UART0.status & TX_READY) == 0u32 {}`, `VECTORS[3]`, `rom_crc32(...)`, `view(UART0)` with `fixed` provenance). Fields of type `Volatile<T>`, `Mmio<T>`, `MmioRO<T>` (`AX_TYPE_MMIO_WRITE_READONLY`), and `MmioWO<T>` (`AX_TYPE_MMIO_READ_WRITEONLY`) automatically lower to exact-width (`1, 2, 4, 8` byte) non-tearing `MirStmtKind.VolatileLoad`/`VolatileStore` operations.
  - **`REQ-OWNER-008` Address Introspection, Dynamic Expressions & Round-Trip Identity (`AXS-ADR-010`..`014`)**: Specified `fn_addr(f) -> usize`, `static_addr(s) -> usize`, `addr_of(x) -> usize`, `address_of(v) -> *const T` (`address_of(v) as usize`), `address_of_mut(v) -> *mut T`, and `f as usize`, dynamic `base + offset` placement (`let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32` lowered via `__ax_addr_slot_<S>`), round-trip identities (`fn_addr(isr) == 0x2000_0000usize`, `static_addr(REG) == base + 0x100`), `fixed` provenance (`never moved, never dropped`), alignment checks (`AX_UNSAFE_AT_MISALIGNED` / `AX_UNSAFE_MISALIGNED_AT`), defined `@repr(C)`/primitive layout checks (`AX_UNSAFE_INVALID_AT_LAYOUT`), intra-module/linker overlap detection (`AX_UNSAFE_AT_OVERLAP`, `AX_LINK_AT_OVERLAP`), and profile gating (`AX_UNSAFE_AT_HOSTED`).
  - **Pipeline, COFF/ELF Symbols, Pinned Sections, `--format bin` & Oracle Device Model (`AXS-ADR-020`..`024`)**: Specified HIR `Placement` side-table entries, MIR `PlaceBase.FixedStatic(SymbolId)`, COFF `IMAGE_SYM_ABSOLUTE` (`SectionNumber = -1`) / ELF `SHN_ABS` symbols for overlays, `pinned_vma` sections for placements, freestanding `--format bin` (`ImageFormat.RawBinary`) flat image output, and the MIR oracle (`--interp`) sparse simulated address space (`FixedAddrMap`) with a scriptable UART/MMIO and vector-table device model.
- Updated `spec/INDEX.md` (§2 canonical documents, §4 `AXS-ADR-NNN` namespace, §5 topic table), `spec/diagnostics.md` (`AX_UNSAFE_AT_MISALIGNED`, `AX_UNSAFE_AT_OVERLAP`, `AX_LINK_AT_OVERLAP`, `AX_UNSAFE_AT_HOSTED`, `AX_UNSAFE_MISALIGNED_AT`, `AX_UNSAFE_INVALID_AT_LAYOUT`), and `spec/invariants.md` (`ADR` group `INV-ADR-001`..`004` for `T526`–`T529`).

## Files changed
- `spec/SPEC-55-fixed-address-declarations.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> `COVERAGE OK (0 gaps)`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`
- `python tools/gatecheck.py --no-run` -> `GATE PASS`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T525` -> `0 REFUSED`

STATUS: COMPLETE round=0
