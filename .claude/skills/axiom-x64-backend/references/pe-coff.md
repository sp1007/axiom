# PE/COFF quick reference for axiom0 (x86-64)

Authoritative project docs: specs 0185 (COFF writer), 0186 (startup + hello.exe), 0187 (import
directory + IAT), 0188 (.pdata/.xdata). This file is a condensed field reference; verify details
against those docs and against `objdump -x`.

## Contents
1. COFF object (.obj) layout
2. COFF symbols and relocations
3. PE32+ image layout
4. Import directory recipe (ExitProcess)
5. Minimal image checklist

## 1. COFF object layout

```
IMAGE_FILE_HEADER (20 bytes)
  Machine              u16  0x8664 (AMD64)
  NumberOfSections     u16
  TimeDateStamp        u32  0 (determinism!)
  PointerToSymbolTable u32
  NumberOfSymbols      u32
  SizeOfOptionalHeader u16  0 for objects
  Characteristics      u16  0
Section headers (40 bytes each)
  Name[8]  (">8 chars" → "/<offset into string table>")
  VirtualSize u32 (0 in objects)   VirtualAddress u32 (0)
  SizeOfRawData u32   PointerToRawData u32
  PointerToRelocations u32   PointerToLinenumbers u32 (0)
  NumberOfRelocations u16    NumberOfLinenumbers u16 (0)
  Characteristics u32
Raw section data, then relocations per section (10 bytes each)
Symbol table (18 bytes per record) then string table (u32 total size incl. itself, then strings)
```

Section characteristics:
- `.text`  0x60500020 = CNT_CODE | ALIGN_16BYTES | MEM_EXECUTE | MEM_READ
- `.rdata` 0x40400040 = CNT_INITIALIZED_DATA | ALIGN_8BYTES | MEM_READ
- `.data`  0xC0400040 = CNT_INITIALIZED_DATA | ALIGN_8BYTES | MEM_READ | MEM_WRITE
- `.bss`   0xC0400080 = CNT_UNINITIALIZED_DATA | ALIGN_8BYTES | MEM_READ | MEM_WRITE
(ALIGN_nBYTES field is bits 20-23: 1→0x00100000 … 16→0x00500000; objects only.)

## 2. Symbols and relocations

Symbol record (18 bytes): `Name[8]` (or 4 zero bytes + u32 string-table offset), `Value u32`
(offset in section), `SectionNumber i16` (1-based; 0 = undefined/external, -1 absolute),
`Type u16` (0x20 = function), `StorageClass u8` (2 = EXTERNAL, 3 = STATIC), `NumberOfAuxSymbols u8`.

Relocation record (10 bytes): `VirtualAddress u32` (offset in section), `SymbolTableIndex u32`,
`Type u16`. AMD64 types: `ADDR64 0x0001`, `ADDR32 0x0002`, `ADDR32NB 0x0003` (RVA),
`REL32 0x0004` (target − (P + 4) with implicit addend stored in the field), `REL32_1..5`
(0x0005–0x0009: extra bytes after the field). COFF uses the **field contents as addend** — write
the addend into the section bytes.

## 3. PE32+ image layout

```
DOS header (64 bytes): "MZ", e_lfanew @0x3C → offset of "PE\0\0"
(optional DOS stub)
"PE\0\0"
IMAGE_FILE_HEADER: Machine 0x8664, SizeOfOptionalHeader 240,
  Characteristics 0x0022 (EXECUTABLE_IMAGE | LARGE_ADDRESS_AWARE)
IMAGE_OPTIONAL_HEADER64 (240 bytes with 16 data directories):
  Magic 0x20B, AddressOfEntryPoint (RVA), ImageBase 0x140000000,
  SectionAlignment 0x1000, FileAlignment 0x200,
  MajorOperatingSystemVersion 6, MajorSubsystemVersion 6,
  SizeOfImage (aligned to SectionAlignment), SizeOfHeaders (aligned to FileAlignment),
  Subsystem 3 (CONSOLE), DllCharacteristics 0x8160
    (HIGH_ENTROPY_VA|DYNAMIC_BASE|NX_COMPAT|TERMINAL_SERVER_AWARE) — DYNAMIC_BASE requires a
    .reloc section; bootstrap may clear DYNAMIC_BASE (0x0100 NX_COMPAT only) and use a fixed base,
  SizeOfStackReserve 0x100000, SizeOfStackCommit 0x1000, SizeOfHeapReserve 0x100000,
  SizeOfHeapCommit 0x1000, NumberOfRvaAndSizes 16
  DataDirectory[1] = Import Directory (RVA,size); [12] = IAT; [3] exception (.pdata); [5] base reloc
Section headers (VirtualAddress/VirtualSize now real; SizeOfRawData aligned to FileAlignment)
Sections
```

Checksum may be 0 for user executables. TimeDateStamp 0 for reproducibility.

SizeOfStackReserve is set by the linker option `--stack-reserve <bytes>` (default 0x100000; ADR-0003).
SizeOfStackCommit stays 0x1000, so the stack grows page by page through the guard page: any function
whose frame exceeds 4096 bytes must probe each page in order before moving RSP (inline loop emitted
by frame lowering; no CRT `__chkstk`). `tools/bootstrap.py` links axiomc with 64 MB (67108864).

## 4. Import directory recipe (kernel32!ExitProcess)

In an `.idata` (or `.rdata`) section:
```
IMAGE_IMPORT_DESCRIPTOR[kernel32]  (20 bytes)
  OriginalFirstThunk = RVA(ILT)  TimeDateStamp 0  ForwarderChain 0
  Name = RVA("KERNEL32.dll")      FirstThunk = RVA(IAT)
IMAGE_IMPORT_DESCRIPTOR null terminator (20 zero bytes)
ILT: u64 RVA(hint/name "ExitProcess"), u64 0
IAT: u64 RVA(hint/name "ExitProcess"), u64 0      ← loader overwrites with the address
Hint/Name: u16 hint (0 ok), "ExitProcess\0" (pad to even)
"KERNEL32.dll\0"
```
Call through the IAT: `call qword ptr [rip + disp32]` (`FF 15`), disp32 = RVA(IAT slot) −
RVA(next instruction). Keep RSP 16-aligned and 32 bytes of shadow space before the call.

Minimal startup (Windows):
```
axiom_start:
    sub  rsp, 40            ; 32 shadow + 8 to realign (entry RSP ≡ 8 mod 16)
    call main               ; E8 rel32
    mov  ecx, eax
    call [rip + IAT_ExitProcess]
    int3
```

## 5. Minimal image checklist

- Headers size / section raw pointers aligned to FileAlignment; RVAs aligned to SectionAlignment.
- `SizeOfImage` = last section VA + aligned VirtualSize.
- Entry point RVA inside an executable section.
- Import directory + IAT data directories filled; ILT and IAT both present.
- `objdump -x out.exe` shows the import of `ExitProcess`; running gives the expected `$?`.
- Deterministic: same input → byte-identical exe (no timestamps, sorted symbols).
