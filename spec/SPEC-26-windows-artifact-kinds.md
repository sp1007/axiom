# SPEC-26 — Windows x64 Artifact Kinds: Static `.lib`, PE32+ `.dll`, and Import Libraries

- **Status:** draft (T772, 2026-11-03)
- **Owner:** `axiom-architect`
- **Consolidates:** `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-070..074`, `AXS-EXT-091`), `spec/SPEC-56-module-relative-bindings.md` (`AXS-MOD-012..013`), `spec/decisions/ADR-0001-fixed-address-declarations.md` (§5–§6), `spec/decisions/ADR-0034-oracle-independence.md` (§4 OI-07b), `spec/requirements/OWNER.md` (`REQ-OWNER-006`), `0104`, `0164`, `0185`, `0186`, `0187`, `0217`, `tasks/0356`, `tasks/0369`, `tasks/0562`, `tasks/0563`
- **Covers:** `REQ-OWNER-006`, `REQ-LNK-057`, `REQ-LNK-058`, `REQ-LNK-059`, `REQ-LNK-060`, `REQ-LNK-061`, `REQ-LNK-062`, `REQ-LNK-063`, `REQ-LNK-064`, `REQ-LNK-065`, `REQ-LNK-066`, `REQ-LNK-067`, `REQ-LNK-068`, `REQ-LNK-069`, `REQ-LNK-070`, `REQ-LNK-071`, `REQ-LNK-072`, `REQ-LNK-073`, `REQ-LNK-074`, `REQ-LNK-075`, `REQ-LNK-076`, `REQ-LNK-077`, `REQ-LNK-078`, `REQ-LNK-079`, `REQ-LNK-080`, `REQ-LNK-081`, `REQ-LNK-082`, `REQ-LNK-083`, `REQ-LNK-084`, `REQ-LNK-085`, `REQ-LNK-086`, `REQ-LNK-087`, `REQ-LNK-088`, `REQ-LNK-089`, `REQ-LNK-090`, `REQ-LNK-091`, `REQ-LNK-092`, `REQ-LNK-093`, `REQ-LNK-094`, `REQ-LNK-095`, `REQ-LNK-096`, `REQ-LNK-097`, `REQ-LNK-098`, `REQ-LNK-099`, `REQ-LNK-100`, `REQ-LNK-101`, `REQ-LNK-102`, `REQ-LNK-103`, `REQ-LNK-104`, `REQ-LNK-105`, `REQ-LNK-106`, `REQ-LNK-107`, `REQ-LNK-108`, `REQ-LNK-109`, `REQ-LNK-110`, `REQ-LNK-111`, `REQ-LNK-112`, `REQ-LNK-113`, `REQ-LNK-114`, `REQ-LNK-115`, `REQ-LNK-116`, `REQ-LNK-117`, `REQ-LNK-118`, `REQ-LNK-119`, `REQ-LNK-120`, `REQ-LNK-121`, `REQ-LNK-161`, `REQ-LNK-162`, `REQ-LNK-163`, `REQ-LNK-164`, `REQ-LNK-196`, `REQ-LNK-197`, `REQ-LNK-198`, `REQ-LNK-199`, `REQ-LNK-200`, `REQ-LNK-201`, `REQ-LNK-202`, `REQ-LNK-203`, `REQ-LNK-204`, `REQ-LNK-205`, `REQ-LNK-206`, `REQ-LNK-207`, `REQ-LNK-208`, `REQ-LNK-209`, `REQ-LNK-210`, `REQ-LNK-211`, `REQ-LNK-212`, `REQ-LNK-213`, `REQ-LNK-214`, `REQ-LNK-215`, `REQ-LNK-216`, `REQ-LNK-217`, `REQ-LNK-218`, `REQ-LNK-219`, `REQ-LNK-220`, `REQ-LNK-221`, `REQ-LNK-222`, `REQ-LNK-223`, `REQ-LNK-224`, `REQ-LNK-225`, `REQ-LNK-226`, `REQ-LNK-232`, `REQ-LNK-233`, `REQ-CORE-3087`, `REQ-CORE-3088`

## Tóm tắt

SPEC-26 quy định chuẩn kiến trúc và định dạng nhị phân cho toàn bộ các loại thành phẩm đầu ra (`ArtifactKind`) của trình biên dịch Axiom trên Windows x64 (`x86_64-pc-windows-msvc`):
1. **Lựa chọn thành phẩm và đường ống liên kết (`AXS-WLIB-001`..`005`):** cờ CLI `--kind exe|obj|lib|dll` (và bí danh tương thích `--emit=obj`), thuộc tính gói `kind` trong `axiom.toml`, quy tắc tìm kiếm thư viện tĩnh/nhập khẩu (`-l<name>`, `-L<dir>`, `@link("<name>")`), hợp đồng xuất ký hiệu `@export`, và sự tách biệt giữa `ObjectWriter`, `ArchiveWriter`, `LinkerCore` (`LinkedImage`) và `ImageWriter` (`PeImageWriter`).
2. **Thư viện tĩnh COFF `.lib` (`AXS-WLIB-010`..`012`):** định dạng lưu trữ `!<arch>\n` tất định (timestamp = `0`, UID/GID/mode = `0`), bảng ký hiệu liên kết thứ nhất (big-endian) và thứ hai (little-endian), bảng tên dài `//`, và thuật toán trích xuất thành viên theo nhu cầu tới điểm bất động (demand-driven fixed-point extraction).
3. **Thư viện liên kết động PE32+ `.dll` (`AXS-WLIB-020`..`023`):** đặc tả `IMAGE_FILE_DLL`, bảng xuất `.edata` (`IMAGE_EXPORT_DIRECTORY`) sắp xếp thứ tự từ điển, điểm vào `DllMain` tổng hợp kích hoạt `__ax_resolve_module_bindings()` (`SPEC-56`) và hàm khởi tạo mô-đun, cùng bảng định vị lại cơ sở `.reloc` (`IMAGE_REL_BASED_DIR64`, `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE`).
4. **Thư viện nhập khẩu ngắn COFF `.lib` và liên kết chéo `__imp_<name>` (`AXS-WLIB-030`..`032`):** phát sinh đồng thời tệp `.lib` nhập khẩu ngắn (`IMPORT_OBJECT_HEADER`, `Sig1 = 0x0000`, `Sig2 = 0xFFFF`) khi biên dịch `--kind dll`, tiêu thụ cả `.lib` nhập khẩu ngắn lẫn `.lib`/`.a` truyền thống trong `compiler/link/`, và phát sinh tham chiếu `__imp_<name>` chuẩn kèm đối tượng thời gian chạy khả liên kết (`ADR-0034` §4 OI-07b) để GNU `ld`/`gcc` liên kết trực tiếp đầu ra `--kind obj`.

---

## 1. Artifact Kinds, Driver Selection, Library Search & Linker Architecture

### AXS-WLIB-001 — Artifact Kind Model & Writer/Linker Separation

The compiler backend and driver distinguish four primary native artifact kinds (`SPEC-04 AXS-EXT-070`, `REQ-OWNER-006`, `REQ-LNK-196`, `REQ-CORE-3087`, `REQ-CORE-3088`):

```axiom
pub enum ArtifactKind {
    Executable, // --kind exe : PE32+ executable (.exe)
    Object,     // --kind obj : COFF relocatable object (.obj)
    StaticLib,  // --kind lib : COFF static archive (.lib)
    DynLib,     // --kind dll : PE32+ dynamic library (.dll) + companion import library (.lib)
}
```

1. **Object file != executable image (`REQ-LNK-196`, `REQ-LNK-220`):** A relocatable object (`ArtifactKind.Object`) contains machine code, section headers, symbol definitions/references, and explicit relocation records (`REQ-LNK-197`, `REQ-LNK-198`), whereas an executable or shared library (`Executable`, `DynLib`) is a fully linked loadable image. `ObjectWriter` (`compiler/obj/`) is an independent subsystem from `Linker` (`compiler/link/`).
2. **Linker core vs image serialization (`REQ-LNK-232`, `REQ-LNK-233`, `REQ-CORE-3087`, `REQ-CORE-3088`):** `LinkerCore` resolves symbols, extracts archive members, computes section layout, and produces a format-neutral `LinkedImage` containing resolved virtual addresses (`VA`), relative virtual addresses (`RVA`), file offsets (`FileOffset`), merged sections, import/export tables, unwind metadata, and base relocation entries. `ImageWriter` (`PeImageWriter` on Windows x64) serializes `LinkedImage` into either a `Pe32Plus` executable (`.exe`) or a `Pe32PlusDll` shared library (`.dll`) plus companion import `.lib`. Executable/image format selection is an explicit target/artifact policy decision, never hard-coded to a single fixed-address executable subtype.
3. **Self-contained native toolchain (`REQ-LNK-164`, `REQ-LNK-221..226`):** `compiler/obj/` and `compiler/link/` emit `.obj`, `.lib`, `.dll`, and `.exe` directly without invoking LLVM, Clang, GCC, `lld`, `link.exe`, `lib.exe`, or any external assembler/archiver.

### AXS-WLIB-002 — Driver CLI Flags, `axiom.toml` Target Kind, and Default Outputs

1. **CLI selection:** `axiom build` and `axiom compile` accept `--kind <exe|obj|lib|dll>` (default `exe`) and optional `--implib <path>` (override companion import `.lib` path when `--kind dll`). `--emit=obj` and `--emit obj` remain exact aliases for `--kind obj`.
2. **Package manifest selection:** `[package]` or `[[target]]` in `axiom.toml` may specify `kind = "exe" | "obj" | "lib" | "dll"`. An explicit CLI `--kind` flag overrides the manifest `kind`.
3. **Default output paths (when `-o <path>` is omitted):**
   - `Executable` (`--kind exe`): `<name>.exe`
   - `Object` (`--kind obj` / `--emit=obj`): `<name>.obj`
   - `StaticLib` (`--kind lib`): `<name>.lib`
   - `DynLib` (`--kind dll`): `<name>.dll` and companion import library `<stem>.lib` in the same directory (unless `--implib <path>` is given, in which case the companion import library is written to `<path>`).
4. **Invalid kind & command constraints:** Any `--kind` value outside `{exe, obj, lib, dll}` is rejected with `AX_DRIVER_INVALID_ARTIFACT_KIND` (exit code `2`). Passing `--kind obj|lib|dll` to `axiom run` is rejected with `AX_DRIVER_USAGE` (exit code `2`) because only `Executable` artifacts can be directly executed by the driver.

### AXS-WLIB-003 — Explicit Native Library Dependencies & Deterministic Search Order

Native libraries and system SDK libraries are explicit target inputs (`REQ-LNK-161`, `REQ-LNK-162`, `REQ-LNK-163`, `REQ-LNK-216`, `REQ-LNK-217`):
1. **Input channels:** The linker accepts (a) positional `.obj` and `.lib`/`.a` file paths on the CLI, (b) `-L<dir>` / `-L <dir>` library search directories in CLI order, (c) `-l<name>` / `-l <name>` library requests, and (d) source-level `@link("<name>")` attributes on `extern` declarations (`SPEC-04 AXS-EXT-091`).
2. **Deterministic search order for `-l<name>`:**
   - If `<name>` ends with `.lib` or `.a` (case-insensitive), the linker probes `<dir>/<name>` for each `-L<dir>` in exact CLI order (and direct path `<name>` if relative/absolute).
   - Otherwise, for each `-L<dir>` in exact CLI order, the linker probes:
     1. `<dir>/<name>.lib`
     2. `<dir>/lib<name>.lib`
     3. `<dir>/lib<name>.a`
   - If a matching file exists, it is opened as a COFF archive (static `.lib` or import `.lib`).
   - If no file matches in any `-L<dir>`:
     - For `@link("<dll>")` declarations or known Windows system DLL names (e.g. `kernel32`, `user32`, `ntdll`, `ws2_32`, `advapi32`, `bcrypt`), external symbols bound to that module are resolved via synthesized PE import directory entries against `<name>.dll` (`AXS-WLIB-031`).
     - For an explicit CLI `-l<name>` that matches neither a file in `-L` nor any resolved import symbol, the linker emits `AX_LINK_LIBRARY_NOT_FOUND` (`data.library = "<name>"`).

### AXS-WLIB-004 — Binary Export Visibility & `@export` Contract

1. **Module visibility != binary export (`REQ-LNK-210`, `REQ-LNK-211`):** `pub` controls visibility across Axiom modules only; a `pub fn` or `pub static` is **not** exported in a PE `.edata` table unless annotated with `@export`.
2. **`@export` attribute (`SPEC-04 AXS-EXT-073`, `REQ-FFI-042`):**
   - `@export` on a non-generic `fn` or `static` exports the item under its unqualified identifier name.
   - `@export("custom_name")` exports the item under `"custom_name"`.
   - Applying `@export` to a generic function or uninstantiated template is rejected with `AX_FFI_GENERIC_EXPORT`.
   - Two `@export` items in the same linked image that resolve to the same external export name are rejected with `AX_LINK_DUPLICATE_EXPORT` (`data.symbol`).
3. **Linker reachability roots (`REQ-LNK-203`, `REQ-LNK-204`):** Dead-section elimination (`--gc-sections` / unreachable section GC) seeds reachability from:
   - the image entry point (`mainCRTStartup` / `axiom_entry` for `Executable`; synthesized `_DllMainCRTStartup` for `DynLib`) when present, and
   - every symbol marked `@export` (`ObjSymbol.is_export == true`).
   In `StaticLib` (`--kind lib`), all defined module symbols are preserved in the emitted `.obj` member(s) so downstream links can extract them on demand.

### AXS-WLIB-005 — Linker Core & PE32+ Image Invariants

The Windows x64 object writer and linker satisfy all foundational invariants in `0185` (`REQ-LNK-057..072`), `0186` (`REQ-LNK-073..097`), `0187` (`REQ-LNK-098..121`), and `tasks/0369` (`REQ-LNK-196..226`):
- **Distinct address spaces (`REQ-LNK-062`, `REQ-LNK-082`):** `VA` (`ImageBase + RVA`), `RVA` (offset in loaded memory from `ImageBase`, aligned to `SectionAlignment = 0x1000`), and `FileOffset` (offset in disk file, aligned to `FileAlignment = 0x200`) are distinct types and never conflated.
- **Section layout before relocation (`REQ-LNK-120`, `REQ-LNK-206`, `REQ-LNK-207`):** All input/synthesized sections (`.text`, `.rdata`, `.data`, `.bss`, `.pdata`, `.xdata`, `.idata`, `.edata`, `.reloc`, `.tls`) are merged and assigned final RVAs before any instruction displacement or pointer relocation is patched.
- **W^X enforcement (`REQ-LNK-070`, `REQ-LNK-094`):** No section in an emitted `.exe` or `.dll` may have both `IMAGE_SCN_MEM_WRITE` and `IMAGE_SCN_MEM_EXECUTE` set simultaneously.
- **Zero CRT dependency (`REQ-LNK-073`, `REQ-LNK-089`, `REQ-LNK-214..215`):** Emitted `.exe` and `.dll` images depend directly on OS kernel/subsystem DLLs (`KERNEL32.dll`, etc.) and never require `msvcrt.dll`, `ucrtbase.dll`, or `vcruntime140.dll`.

---

## 2. Deterministic COFF Archive (`.lib`) Format & Fixed-Point Extraction

### AXS-WLIB-010 — COFF Archive Binary Layout & Zeroed Deterministic Metadata

A Windows static library (`--kind lib`) or import library (companion `.lib` of `--kind dll`) is a standard System V / Microsoft PE/COFF archive file (`REQ-LNK-218`, `REQ-LNK-219`, `INV-DET-002`):
1. **Archive signature:** The first 8 bytes of the file are the ASCII magic string `!<arch>\n` (`0x21 0x3C 0x61 0x72 0x63 0x68 0x3E 0x0A`).
2. **Member header (60 bytes, ASCII space-padded):** Every archive member is preceded by a 60-byte header at an even file offset:

   | Offset | Size | Field | Deterministic Value |
   |---|---|---|---|
   | `0` | `16` | `Name` | `"/               "` (1st/2nd linker member), `"//              "` (longnames), `"<name>/         "` (short member name $\le 15$ bytes), or `"/<dec_offset>   "` (offset into `//`) |
   | `16` | `12` | `Date` | `"0           "` (decimal `0`, padded with ASCII spaces `0x20`) |
   | `28` | `6` | `UID` | `"0     "` (ASCII `'0'` + 5 spaces; blank `"      "` for `//` allowed by COFF spec, canonicalized to `"0     "`) |
   | `34` | `6` | `GID` | `"0     "` |
   | `40` | `8` | `Mode` | `"0       "` (octal `0`, padded with spaces) |
   | `48` | `10` | `Size` | Decimal byte size of member body (excluding padding), left-aligned and padded with spaces |
   | `58` | `2` | `EndHeader` | `` `\n `` (`0x60 0x0A`) |

3. **Even-byte alignment:** If a member's `Size` is odd, a single `'\n'` (`0x0A`) pad byte is appended immediately after the member body so the next 60-byte member header begins at a 2-byte aligned file offset.

### AXS-WLIB-011 — First Linker Member, Second Linker Member, and Longnames Member (`//`)

Every `.lib` archive emitted by `compiler/obj/` (`ArchiveWriter`) contains the standard COFF archive index members in deterministic order:
1. **First Linker Member (`Name = "/               "`):**
   - `NumberOfSymbols`: 4-byte **big-endian** `u32` ($N$, total public/external symbols across all archive members).
   - `Offsets`: $N \times 4$-byte **big-endian** `u32` file offsets of the 60-byte member header defining each symbol.
   - `StringTable`: $N$ NUL-terminated ASCII symbol name strings in the same order as `Offsets`.
2. **Second Linker Member (`Name = "/               "`):**
   - `NumberOfMembers`: 4-byte **little-endian** `u32` ($M$, number of object/import members in the archive).
   - `Offsets`: $M \times 4$-byte **little-endian** `u32` file offsets of each object/import member header, in ascending member order.
   - `NumberOfSymbols`: 4-byte **little-endian** `u32` ($N$).
   - `Indices`: $N \times 2$-byte **little-endian** `u16` 1-based indices into the `Offsets` array (`1..M`).
   - `StringTable`: $N$ NUL-terminated ASCII symbol names sorted strictly in ascending lexicographical ASCII byte order (`strcmp` order).
3. **Longnames Member (`Name = "//              "`, emitted when any member name exceeds 15 bytes):**
   - Concatenation of NUL-terminated (`\0` or `/\0`) UTF-8/ASCII filenames; object member headers reference their entry as `"/<decimal_byte_offset>"`.
4. **Object/Import Members:** Ordered deterministically by canonical module compilation order (for `--kind lib`) or ascending lexicographical symbol name (for companion import `.lib`). All embedded COFF `.obj` headers have `TimeDateStamp = 0`.

### AXS-WLIB-012 — Demand-Driven Fixed-Point Archive Extraction

When `compiler/link/` consumes one or more `.lib`/`.a` archives (`REQ-LNK-199..202`, `REQ-LNK-205`):
1. **Initial state:** All explicit input `.obj` files are loaded unconditionally into the link unit, populating `DefinedSymbols` (all defined `IMAGE_SYM_CLASS_EXTERNAL` symbols) and `UndefinedSymbols` (all unresolved external references minus `DefinedSymbols`, plus entry point / `@export` roots).
2. **Fixed-point extraction loop:**
   - The linker scans candidate archive members across loaded archives in deterministic CLI order.
   - An unextracted archive member $m$ is extracted and added to the link unit **if and only if** $m$ defines at least one external symbol $s \in \text{UndefinedSymbols} \setminus \text{DefinedSymbols}$.
   - Extracting $m$ adds all of $m$'s defined external symbols to `DefinedSymbols`, removes them from `UndefinedSymbols`, and adds $m$'s own unresolved references to `UndefinedSymbols`.
   - The scan repeats until a full pass over all archives extracts zero new members (fixed point).
3. **Dead-member exclusion:** Archive members that define no symbol ever needed by the reachable symbol graph are **never** extracted; their sections, data, and transitive unresolved references do not enter the output image.
4. **Duplicate & corrupt archive diagnostics:**
   - If two input `.obj` files or two extracted archive members define the same strong external symbol (`IMAGE_SYM_CLASS_EXTERNAL`, non-weak/non-COMDAT), the linker emits `AX_LINK_DUPLICATE_SYMBOL` (`REQ-LNK-059`, `REQ-LNK-200`).
   - Weak/COMDAT linkonce symbols (`IMAGE_SCN_LNK_COMDAT` / generic monomorphizations, `REQ-LNK-201`, `REQ-LNK-205`) deduplicate deterministically by selecting the first definition in canonical link order.
   - An archive whose magic is not `!<arch>\n` or whose member headers/offsets exceed file bounds is rejected with `AX_LINK_BAD_ARCHIVE`.

---

## 3. PE32+ Dynamic Library (`.dll`) Emission: `.edata`, `DllMain`, and `.reloc`

### AXS-WLIB-020 — PE32+ `.dll` Headers & Image Characteristics

When `PeImageWriter` emits `ArtifactKind.DynLib` (`--kind dll`, `0186`, `tasks/0563`):
1. **COFF File Header (`Characteristics`):**
   `IMAGE_FILE_EXECUTABLE_IMAGE (0x0002) | IMAGE_FILE_LARGE_ADDRESS_AWARE (0x0020) | IMAGE_FILE_DEBUG_STRIPPED (0x0200) | IMAGE_FILE_DLL (0x2000)` (`0x2222`).
2. **PE32+ Optional Header (`Magic = 0x020B`):**
   - `ImageBase`: `0x0000000180000000` (`0x180000000`, standard Windows x64 DLL preferred load address; compared to `0x140000000` for `.exe`).
   - `SectionAlignment = 0x1000`, `FileAlignment = 0x200`, `Subsystem = IMAGE_SUBSYSTEM_WINDOWS_CUI (3)` (or `WINDOWS_GUI (2)`).
   - `DllCharacteristics`: `IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA (0x0020) | IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE (0x0040) | IMAGE_DLLCHARACTERISTICS_NX_COMPAT (0x0100)` (`0x0160`).
   - `AddressOfEntryPoint`: RVA of synthesized `_DllMainCRTStartup` (`AXS-WLIB-022`), or `0` only in freestanding raw DLL builds with no module bindings and no initializers.

### AXS-WLIB-021 — Export Directory Table (`.edata` / `DataDirectory[PE_DIR_EXPORT = 0]`)

Every `--kind dll` image with $E \ge 1$ `@export` symbols emits an Export Directory (`IMAGE_EXPORT_DIRECTORY`, 40 bytes) in `.edata` (or merged into `.rdata`) pointed to by `DataDirectory[0]` (`tasks/0563 §304.18`):

| Offset | Size | Field | Value |
|---|---|---|---|
| `0` | `4` | `Characteristics` | `0` |
| `4` | `4` | `TimeDateStamp` | `0` (deterministic, `INV-DET-002`) |
| `8` | `4` | `MajorVersion` / `MinorVersion` | `0` / `0` |
| `12` | `4` | `Name` | RVA of NUL-terminated ASCII DLL filename (e.g. `"mathlib.dll\0"`) |
| `16` | `4` | `Base` | `1` (starting ordinal number) |
| `20` | `4` | `NumberOfFunctions` | $E$ (`u32`) |
| `24` | `4` | `NumberOfNames` | $E$ (`u32`) |
| `28` | `4` | `AddressOfFunctions` | RVA of `ExportAddressTable` ($E \times \text{u32}$ RVAs of exported functions/data) |
| `32` | `4` | `AddressOfNames` | RVA of `NamePointerTable` ($E \times \text{u32}$ RVAs to NUL-terminated export name strings) |
| `36` | `4` | `AddressOfNameOrdinals` | RVA of `OrdinalTable` ($E \times \text{u16}$ 0-based indices `0..E-1` into `ExportAddressTable`) |

All exported symbols are sorted strictly in ascending ASCII byte order of their export name before populating `ExportAddressTable`, `NamePointerTable`, and `OrdinalTable`, enabling $O(\log E)$ binary search by `GetProcAddress`.

### AXS-WLIB-022 — Synthesized `DllMain` (`_DllMainCRTStartup`) & Module Initialization

A `--kind dll` build does not require `fn main()`. Instead, the compiler/linker synthesizes the PE entry point `_DllMainCRTStartup` using the Windows x64 ABI (`extern "system" fn(hinstDLL: usize, fdwReason: u32, lpvReserved: *mut u8) -> i32`, `ADR-0001 §5–§6`, `SPEC-56 AXS-MOD-012`):
1. **On `DLL_PROCESS_ATTACH` (`fdwReason == 1`):**
   - **Step 1 (Module-relative binding resolution):** If the DLL declares any `image("...")` bindings (`SPEC-56`), `_DllMainCRTStartup` calls `__ax_resolve_module_bindings()`. If `__ax_resolve_module_bindings()` returns `false` (`0`), `_DllMainCRTStartup` immediately returns `0` (`FALSE`) in `eax` without running any user initializers, causing `LoadLibraryA`/`LoadLibraryW` to fail cleanly.
   - **Step 2 (Module initializers & optional `@entry` hook):** Executes package/module static initializers in dependency order and, if the user defined an `@entry fn dll_init() -> bool` (or `fn(hinst: usize, reason: u32, reserved: *mut u8) -> i32`), invokes it. If the hook returns `false` / `0`, `_DllMainCRTStartup` returns `0` (`FALSE`).
   - **Step 3:** Returns `1` (`TRUE`).
2. **On `DLL_PROCESS_DETACH` (`fdwReason == 0`), `DLL_THREAD_ATTACH` (`2`), `DLL_THREAD_DETACH` (`3`):** Invokes the optional user `@entry` handler if it accepts `(usize, u32, *mut u8) -> i32`; otherwise returns `1` (`TRUE`).

### AXS-WLIB-023 — Base Relocation Table (`.reloc` / `DataDirectory[PE_DIR_BASERELOC = 5]`)

Because DLLs (and ASLR-enabled EXEs with `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE`) may be relocated by the OS loader when preferred `ImageBase` (`0x180000000`) is occupied (`tasks/0563 §304.19`):
1. **Relocation collection:** Every resolved 64-bit absolute virtual address (`IMAGE_REL_AMD64_ADDR64`) in `.text`, `.rdata`, or `.data` records a base relocation at its target `RVA` with type `IMAGE_REL_BASED_DIR64` (`10`). RIP-relative (`REL32`) and RVA-relative (`ADDR32NB`) relocations are position-independent within the image and do **not** emit `.reloc` entries.
2. **Page block encoding (`.reloc` section):** Base relocations are sorted by ascending `RVA` and grouped by 4 KiB page (`PageRVA = rva & 0xFFFFF000`):
   - `PageRVA` (`u32`): 4 KiB page base RVA.
   - `BlockSize` (`u32`): `8 + 2 * entry_count` (padded to a multiple of 4 bytes by appending a dummy `IMAGE_REL_BASED_ABSOLUTE = 0` `u16` entry when `entry_count` is odd).
   - `Entries` (`u16[entry_count]`): `(10 << 12) | (rva & 0x0FFF)` (`IMAGE_REL_BASED_DIR64`).
3. **Empty `.reloc` invariant:** If an image contains zero `ADDR64` relocations in `.dll` mode, `PeImageWriter` emits a single minimal dummy page block (`PageRVA = 0x1000`, `BlockSize = 12`, two `IMAGE_REL_BASED_ABSOLUTE (0)` entries) so the Windows loader always honours `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE` when rebasing.

---

## 4. COFF Short-Import Libraries & `__imp_<name>` Cross-Linking (`ADR-0034` §4 OI-07b)

### AXS-WLIB-030 — Companion Short-Import `.lib` Generation Alongside `--kind dll`

Whenever `PeImageWriter` emits `<name>.dll` (`--kind dll`), it simultaneously writes a companion COFF import library (`<stem>.lib` or `--implib <path>`) containing one **Short Import Object** member per exported symbol (`AXS-WLIB-010`, `AXS-WLIB-011`):
1. **`IMPORT_OBJECT_HEADER` (20 bytes):**

   | Offset | Size | Field | Value |
   |---|---|---|---|
   | `0` | `2` | `Sig1` | `IMAGE_FILE_MACHINE_UNKNOWN` (`0x0000`) |
   | `2` | `2` | `Sig2` | `IMPORT_OBJECT_HDR_SIG2` (`0xFFFF`) |
   | `4` | `2` | `Version` | `0` |
   | `6` | `2` | `Machine` | `IMAGE_FILE_MACHINE_AMD64` (`0x8664`) |
   | `8` | `4` | `TimeDateStamp` | `0` (deterministic) |
   | `12` | `4` | `SizeOfData` | `len(sym_name) + 1 + len(dll_name) + 1` (`u32`) |
   | `16` | `2` | `OrdinalOrHint` | Export hint index (`0..E-1`, `u16`) |
   | `18` | `2` | `Type` | `(IMPORT_OBJECT_NAME (2) << 2) | import_type`, where `import_type = IMPORT_OBJECT_CODE (0)` for `fn` and `IMPORT_OBJECT_DATA (1)` for `static` |

2. **Payload:** Immediately following the 20-byte header are two NUL-terminated ASCII strings: `<sym_name>\0<dll_filename>\0`.
3. **Archive symbol directory entries:**
   - For every exported function (`IMPORT_OBJECT_CODE`), the archive's First and Second Linker Members export **both** `<sym_name>` (thunk symbol) and `__imp_<sym_name>` (IAT slot symbol), both pointing to that member's file offset.
   - For every exported `static` data symbol (`IMPORT_OBJECT_DATA`), the archive's linker members export `__imp_<sym_name>`.

### AXS-WLIB-031 — Consuming Short-Import & Traditional COFF Import Libraries in `compiler/link/`

When `compiler/link/` inspects a candidate archive member in a `.lib`/`.a` file (`0187`, `REQ-LNK-098..121`):
1. **Short-import member detection (`Sig1 == 0x0000 && Sig2 == 0xFFFF`):**
   - If either `<sym_name>` or `__imp_<sym_name>` is currently in `UndefinedSymbols`, the linker extracts the short-import descriptor and registers `(dll_name, sym_name, hint)` in `.idata` (`IMAGE_IMPORT_DESCRIPTOR`, ILT `.idata$4`, Hint/Name `.idata$6`, IAT `.idata$5`).
   - The IAT slot defines both `__imp_<sym_name>` and internal alias `__IAT_<sym_name>`.
   - If `<sym_name>` itself is referenced as a call/jump target (`IMPORT_OBJECT_CODE`), the linker synthesizes the 6-byte indirect jump stub `FF 25 <disp32>` (`jmp qword ptr [rip + __imp_<sym_name>]`, `REQ-LNK-102`) in `.text` defining `<sym_name>`.
2. **Traditional COFF import member detection (`Machine == 0x8664`):**
   - Archives generated by GNU `dlltool`/`ar` or MSVC `lib.exe` with long `.idata$2`..`.idata$7` COFF object members are parsed as standard COFF objects; `__imp_<sym_name>` and thunk symbols participate directly in fixed-point extraction (`AXS-WLIB-012`).

### AXS-WLIB-032 — Standard `__imp_<name>` Naming & Linkable Runtime for GNU `ld` Cross-Linking (`ADR-0034` §4 OI-07b)

To satisfy `ADR-0034` §4 (`OI-07b`: cross-linking `--kind obj` / `--emit=obj` output with an independent system linker such as GNU `ld` / MinGW-w64 `gcc` or MSVC `link.exe`):
1. **Standard `__imp_<name>` import symbol convention:**
   - `compiler/obj/` and `compiler/link/` accept both `__imp_<name>` (standard PE/COFF ABI) and `__IAT_<name>` (legacy internal alias) as IAT slot references for imported symbol `<name>`.
   - When `compiler/obj/` emits a relocatable `.obj` (`--kind obj` / `--emit=obj`), any direct indirect-IAT reference emits the standard symbol name `__imp_<name>`, while regular `extern` function calls emit `IMAGE_REL_AMD64_REL32` against `<name>` (resolved either to a local definition or an import library's `<name>` thunk).
2. **Linkable runtime object (`axiom_rt.obj` / `libaxiom_rt.lib`):**
   - In `--kind exe` and `--kind dll`, `compiler/link/` synthesizes the startup entry (`mainCRTStartup` / `_DllMainCRTStartup`) and built-in host intrinsics (`__ax_host_print`, `__ax_host_print_int`, `axiom_panic`, etc.) directly into `.text` with `.idata` imports from `KERNEL32.dll` (`GetStdHandle`, `WriteFile`, `ExitProcess`, `GetCommandLineW`, `GetEnvironmentVariableW`, etc.).
   - For `--kind obj` (`--emit=obj`) cross-linking with GNU `ld` / `gcc`, the compiler driver or runtime archive provides the linkable runtime symbols (`__ax_host_print`, `__ax_host_print_int`, `axiom_panic`, and startup wrapper when `--nostartfiles` is used) referencing Win32 APIs via standard symbol names (`GetStdHandle`, `WriteFile`, `ExitProcess`, or `__imp_<FuncName>`) so `gcc app.obj axiom_rt.obj -lkernel32 -o app.exe` links cleanly without undefined internal `__IAT_*` symbols and executes with identical stdout and exit code (`INV-WLIB-003`).

---

## 5. Diagnostics, Canonical Examples & Verification Matrix

### AXS-WLIB-050 — Diagnostics Summary

| Code | Sev | Owner | Trigger |
|---|---|---|---|
| `AX_DRIVER_INVALID_ARTIFACT_KIND` | E | `T750` | `--kind <k>` or `axiom.toml` `kind` is not one of `exe`, `obj`, `lib`, `dll` (exit code `2`) |
| `AX_LINK_BAD_ARCHIVE` | E | `T750` | Input `.lib`/`.a` file lacks `!<arch>\n` magic, has truncated/corrupt 60-byte member headers, or invalid symbol directory offsets |
| `AX_LINK_LIBRARY_NOT_FOUND` | E | `T750` | Library requested via `-l<name>` or `@link("<name>")` cannot be found in any `-L<dir>` path or resolved import table (`data.library`) |
| `AX_LINK_DUPLICATE_EXPORT` | E | `T751` | Two `@export` items in the same linked image export the identical external symbol name (`data.symbol`) |
| `AX_LINK_DUPLICATE_SYMBOL` | E | `T750` | Two `.obj` files or extracted `.lib` members define the same strong external symbol (`data.symbol`) |
| `AX_LINK_UNDEFINED_SYMBOL` | E | `T750` | Referenced symbol remains unresolved after fixed-point archive extraction and import resolution (`data.symbol`) |
| `AX_FFI_GENERIC_EXPORT` | E | `T751` | `@export` applied to an uninstantiated generic function |

### AXS-WLIB-051 — Canonical Positive Example (Static `.lib`, PE `.dll` + Short-Import `.lib`, and `.exe` Consumer)

```axiom
// mathlib.ax — compiled with:
//   axiom build mathlib.ax --kind lib -o build/mathlib_static.lib
//   axiom build mathlib.ax --kind dll -o build/mathlib.dll
module mathlib

@export
pub fn add_i64(a: i64, b: i64) -> i64 {
    return a + b
}

@export("math_triple")
pub fn triple(x: i64) -> i64 {
    let two = add_i64(x, x)
    return add_i64(two, x)
}

// Not annotated with @export: visible inside Axiom modules via `pub`,
// but NEVER emitted into mathlib.dll's .edata export directory (REQ-LNK-210).
pub fn internal_helper(x: i64) -> i64 {
    return x + 1
}
```

```axiom
// app.ax — linked against mathlib.lib (either static archive or DLL companion import lib):
//   axiom build app.ax -L build -lmathlib -o build/app.exe
module app

@link("mathlib")
extern "C" {
    fn add_i64(a: i64, b: i64) -> i64
    fn math_triple(x: i64) -> i64
}

pub fn main() -> i32 {
    let s = add_i64(10, 32)
    let t = math_triple(s)
    if t == 126 {
        return 0
    }
    return 1
}
```

### AXS-WLIB-052 — Canonical Negative Examples

```axiom
// ERROR: AX_LINK_DUPLICATE_EXPORT (data.symbol = "compute")
@export("compute")
pub fn compute_v1(x: i64) -> i64 {
    return x + 1
}

@export("compute")
pub fn compute_v2(x: i64) -> i64 {
    return x + 2
}
```

```axiom
// ERROR: AX_FFI_GENERIC_EXPORT — generic functions cannot be exported without monomorphization
@export
pub fn identity<T>(x: T) -> T {
    return x
}
```

### AXS-WLIB-053 — E18.7 Implementation & Conformance Matrix

| Task | Scope | Enforced Invariant | Primary Verification Suite |
|---|---|---|---|
| `T750` | `--kind lib` COFF archive writer (`!<arch>\n`, 1st/2nd linker members, `//`, zero timestamps) + fixed-point `.lib` reader & `-l`/`-L` search in `compiler/link/` | `INV-WLIB-001` | `tests/link/lib` |
| `T751` | `--kind dll` PE32+ `.dll` writer (`.edata`, `_DllMainCRTStartup` calling `__ax_resolve_module_bindings()`, `.reloc` with `DYNAMIC_BASE`), companion short-import `.lib` writer/reader, and `__imp_<name>` support | `INV-WLIB-002` | `tests/link/dll` |
| `T773` | End-to-end conformance suite: static `.lib` dead-member exclusion, `.dll` + `.lib` import linking, `LoadLibraryA`/`GetProcAddress`, forced base relocation at non-preferred `ImageBase`, and `ADR-0034` §4 OI-07b GNU `ld` cross-linking of `--emit=obj` | `INV-WLIB-003` | `tests/conformance/p18/e18_7_windows_artifacts` |

## Sources

- `spec/SPEC-04-core-extensibility.md` (§8 `AXS-EXT-070..074`, §10 `AXS-EXT-091`)
- `spec/SPEC-56-module-relative-bindings.md` (`AXS-MOD-012..013`)
- `spec/decisions/ADR-0001-fixed-address-declarations.md` (§5–§6)
- `spec/decisions/ADR-0034-oracle-independence.md` (§4 `OI-07b`)
- `spec/requirements/OWNER.md` (`REQ-OWNER-006`)
- `docs/base/0104`, `0164`, `0185`, `0186`, `0187`, `0217`, `tasks/0356`, `tasks/0369`, `tasks/0562`, `tasks/0563`
