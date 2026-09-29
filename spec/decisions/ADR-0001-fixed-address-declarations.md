# ADR-0001 — Declarations placed at fixed memory addresses (`@at`)

Status: **Accepted (owner requirement REQ-OWNER-003)** — surface design below is the baseline;
details are finalised by the E13.6 spec task, which may refine syntax but not drop capabilities.
Date: 2026-09-29. Revisit: syntax details only.

## Context

The project owner requires: *in low-level programming, variables, arrays, structs, functions, … can
be declared directly at a memory address and then used normally, provided the declaration is
correct.*

The normative corpus covers MMIO only through raw pointers, `Mmio<T>`, `map_mmio(addr, size)` →
`mut_view<u8>`, `volatile_load/store` (0071 §31-32, 0044, 0097 AOS-26..30, tasks/0328) and
`@section("…")` for code placement. It has **no declaration form** that binds a named object or
function to an absolute address, so every access goes through pointer casts and explicit volatile
calls. That is exactly the friction the owner wants removed, while keeping Axiom's rule
"Safe code describes intent; unsafe code may describe the machine" (tasks/0339).

## Decision

### 1. Two placement kinds, one attribute

```axiom
// (a) Overlay: the object already exists at that address (device registers, ROM tables,
//     bootloader hand-off data). No storage is emitted; the symbol IS the address.
@at(0x4000_1000)
unsafe static UART0: UartRegs

// (b) Placement: we define the object/code and the image must place it at that address
//     (vector tables, reset handlers, firmware headers). Storage/code is emitted into a
//     section the linker pins at that address.
@at(0x0000_0000)
unsafe static VECTORS: [48]fn() = [reset, nmi, hard_fault, ...]

@at(0x0800_0100)
unsafe fn reset() -> never { ... }

// Calling a routine that already exists at an absolute address (ROM/BIOS/firmware):
@at(0xFFFF_0400)
unsafe extern "C" fn rom_crc32(data: *const u8, len: usize) -> u32
```

Rule: **no initializer / `extern fn` = overlay; initializer or body = placement.** Works for
`static`, `static mut`, arrays, structs, tuples, enums with defined layout, and functions.

### 2. "Use normally" after a correct declaration

The `unsafe` on the declaration is the single trust point: the programmer asserts that the
address, size, alignment, layout and access rules are correct. Afterwards uses are ordinary Axiom:

```axiom
UART0.ctrl = UartCtrl.ENABLE          // field store
while UART0.status & TX_READY == 0 {} // field load
VECTORS[3]                            // array indexing (bounds-checked as usual)
let crc = rom_crc32(buf.ptr(), buf.len())   // normal call through the declared ABI
let regs = view(UART0)                // views work; region = the fixed object
```

Register semantics come from the **declared field types**, not from call-site ceremony: fields of
type `Volatile<T>` / `Mmio<T>` (read-only `MmioRO<T>`, write-only `MmioWO<T>`) lower every normal
read/write to a volatile access of exactly that width; plain fields are ordinary memory. So
`UART0.data = b` is a single volatile store when `data: Mmio<u8>`.

### 3. Compile-time checks (a "correct declaration")

- Address is a compile-time constant (`const`/comptime expression) of the target's pointer width.
- Address alignment ≥ type alignment; the type has a defined layout (`@repr(C)` or primitive/array
  of such) — no layout-unspecified Axiom structs at fixed addresses.
- No two `@at` objects overlap (compiler within a module, linker across the image); placement
  addresses must fall inside a memory region of the target/board description when one is given.
- Allowed only in `freestanding`/`kernel`/`system` profiles by default; in the hosted profile it is
  an error (`AX_ADDR_HOSTED`) unless the address lies in a region declared as mapped (future).
- Ownership: fixed-address objects are statics — never moved, never dropped; views of them have
  static lifetime and a `fixed` provenance. `static mut` fixed objects follow the concurrency rules
  (data race = compile error in safe code): accessing them requires either the single-threaded
  freestanding profile, `Volatile`/`Mmio` field types, atomics, or an `unsafe` block.
- Functions at fixed addresses must declare an ABI when called from outside Axiom
  (`extern "C"`, `"system"`, `"interrupt"` when specified); placement functions get normal
  prologues unless `@naked` (future, E13.x).

### 4. Pipeline representation

- HIR/THIR: `Placement { kind: Overlay | Place, address: ConstExpr, region: Option<RegionName> }`
  on static and function items.
- MIR: fixed objects are places rooted at a `FixedStatic(SymbolId)` base with provenance `fixed`;
  `Volatile`/`Mmio` field accesses lower to `volatile_load/store` MIR operations.
- Object model: absolute symbols (COFF `IMAGE_SYM_ABSOLUTE` / section −1, ELF `SHN_ABS`) for
  overlays; per-object pinned sections with a required VMA for placements.
- Linker: honours pinned addresses, detects overlaps, emits raw binary / ELF with program headers at
  those addresses for freestanding images; hosted PE/ELF reject placement outside allowed regions.
- Oracle (MIR interpreter): simulated address space; overlays map to simulated memory or to
  test-harness device models, so programs using `@at` stay testable without hardware.

## Consequences

- New roadmap epic **E13.6 Fixed-address declarations** (P13), implemented in axiomc after
  self-hosting (ROADMAP R7).
- Core extension points must exist from day one (T003a / SPEC-04): placement on items, `fixed`
  provenance, absolute symbols, pinned sections, volatile MIR ops. axiom0 parses `@at` and reports
  `AX_ADDR_UNSUPPORTED_STAGE0`, never crashes.
- Grammar (T001) must admit `@at(...)` with `static`, `static mut`, `extern fn`, `fn` items.

## Sources

Owner requirement 2026-09-29; 0071 §4, §31-32; 0044; 0097 (AOS-26..30); tasks/0328; tasks/0339;
tasks/0476 217.75-77 (attributes); 0072 (unions / reinterpretation).
