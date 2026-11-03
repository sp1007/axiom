# SPEC-27 — Canonical Separate Compilation, Multi-Object `LinkIR` Linking, `COMDAT` Deduplication & Section GC Specification (Linker v2)

- **Status**: draft (T774, 2026-11-03)
- **Owner**: `axiom-architect`
- **Consolidates**: `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-070..074`), `spec/SPEC-24-artifact-format-module-interfaces.md`, `spec/SPEC-26-windows-artifact-kinds.md`, `spec/SPEC-75-lto-wpo-section-gc-pgo.md` (`AXS-LTO-014`, `AXS-LTO-020..022`), `0099` (`specs/0099`, Native Toolchain, Object Writer & Linker v0.1), `0164` (`specs/0164`, Axiom Linker v0.1), `0185` (`specs/0185`, PE/COFF Linker), `0217` (`specs/0217`, OBJECT/LINK-001), `0225` (`specs/0225` §31), `0236` (`specs/0236` §1–28), `0239` (`specs/0239`, LINKER-001), `0245` (`specs/0245` §3–27), `0256` (`specs/0256`, LINKER-002), `tasks/0369` (`BOOTSTRAP-110`), `tasks/0526` (`BOOTSTRAP-267`, Link-Time Codegen & Binary Size), `tasks/0786` (`BOOTSTRAP-564`, Compiler Linker 3.0), `tasks/0802` (`BOOTSTRAP-580`, Machine Code Encoding 4.0), `tasks/0803` (`BOOTSTRAP-581`, Object File Writer 3.0), `tasks/0804` (`BOOTSTRAP-582`, Native Linker 4.0)
- **Covers**: `REQ-LNK-001..056`, `REQ-LNK-122..160`, `REQ-LNK-227..433`, `REQ-LNK-3434..3633`, `REQ-LNK-3785..3993`, `REQ-CORE-592..601`, `REQ-CORE-2541..2643`
- **Related**: `spec/SPEC-21-query-engine-semantic-db.md`, `spec/SPEC-22-incremental-compilation.md`, `spec/SPEC-23-parallel-compilation.md`, `spec/SPEC-24-artifact-format-module-interfaces.md`, `spec/SPEC-26-windows-artifact-kinds.md`, `spec/SPEC-54-panic-unwinding.md`, `spec/SPEC-55-fixed-address-declarations.md`, `spec/SPEC-61-reflection-derive.md`, `spec/SPEC-63-dyn-trait-vtables.md`, `spec/SPEC-75-lto-wpo-section-gc-pgo.md`, `spec/diagnostics.md`, `spec/invariants.md`

## Tóm tắt

SPEC-27 định nghĩa hợp đồng biên dịch riêng rẽ (`.obj` + `.axmi` theo từng mô-đun), biểu diễn trung gian `LinkIR`, thuật toán phân giải ký hiệu đa đối tượng và kho lưu trữ `.lib` (`Strong` vs `Weak` vs `COMDAT`), chia nhỏ phân đoạn theo từng hàm/dữ liệu, và thu gom rác phân đoạn theo tập gốc khả đạt (`section GC`) cho trình liên kết tự thân `compiler/link/` (E18.6):
1. **Biên dịch riêng rẽ từng mô-đun & bàn giao mã hóa máy 4.0 (`AXS-LNK-001`..`005`)**: Mỗi mô-đun Axiom biên dịch độc lập thành cặp `<module>.obj` + `<module>.axmi` (với quy tắc mồ côi trait `REQ-LNK-122`, chuẩn hóa `TypeId` cho thực thể tổng quát `REQ-LNK-140`, tách biệt tính toán khung ngăn xếp với phát sinh prologue/epilogue `REQ-LNK-123..131` và bộ mã hóa lệnh máy tất định `Machine Code Encoding 4.0` `REQ-LNK-3434..3633`). Trình liên kết vận hành thuần túy trên hợp đồng đối tượng/ABI (`INV-LAYER-002`) và nạp danh sách `.obj`/`.lib` theo đúng thứ tự chuẩn hóa tất định.
2. **Mô hình `LinkIR`, phân giải ký hiệu `Strong`/`Weak`/`COMDAT` & chẩn đoán giải mã tên (`AXS-LNK-010`..`014`)**: Chuẩn hóa đầu vào COFF/ELF/Mach-O về `LinkIR`, hợp nhất bảng ký hiệu toàn cục, khử trùng lặp thực thể hàm tổng quát đơn hình hóa (`monomorphized generics`) và bảng phương thức ảo (`vtable`) qua `IMAGE_SCN_LNK_COMDAT`, trích xuất thành viên `.lib` theo điểm bất động, và phát sinh chẩn đoán có cấu trúc (`AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_UNDEFINED_SYMBOL`, `AX_LINK_ABI_MISMATCH`) kèm đường dẫn Axiom đã giải mã (`pkg.mod.fn<T>`) và vị trí nguồn (`Span`).
3. **Chia nhỏ phân đoạn, thu gom rác phân đoạn (`--gc-sections`), gộp mã an toàn (`Safe ICF`) & kiểm chứng ảnh cuối (`AXS-LNK-020`..`025`, `AXS-LNK-050`..`053`)**: Phát sinh mỗi hàm/dữ liệu vào phân đoạn riêng (`.text$<sym>`, `.rdata$<sym>`, `.data$<sym>`, `.bss$<sym>`), đánh dấu khả đạt từ tập gốc (`@entry`/`main`/`DllMain`, `@export`, `@used`, `@at` cố định địa chỉ, khởi tạo mô-đun, gốc phản xạ runtime) kèm liên kết nhân quả `.pdata`/`.xdata`, quét bỏ toàn bộ phân đoạn không tham chiếu trước khi bố cục địa chỉ (`VA`/`RVA`/`FileOffset`), kiểm tra tràn định vị lại và xác thực ảnh thực thi cuối cùng.

---

## 1. Separate Compilation Contract, Multi-Object Input Order & Machine Encoding Boundary

### `AXS-LNK-001` — Linker Semantic Firewall & Pure Object/ABI Boundary

1. **Absolute layer separation (`REQ-LNK-001..003`, `REQ-LNK-132`, `REQ-LNK-160`, `INV-LAYER-002`, `0164 §1–3`, `0239 §1`, `0256 §1`, `tasks/0786 §564.1–3`, `tasks/0804 §582.1–2`)**:
   - `compiler/link/` depends only on `objmodel`, `kernel`, and `diag`. It SHALL NEVER parse Axiom source files, invoke AST/HIR/THIR/MIR type checking, solve traits, or infer ownership, `view`/`mut_view` capabilities, or `Drop` liveness from machine bytes (`REQ-LNK-001`, `REQ-LNK-132`).
   - All language-level interprocedural optimizations run before object emission (or in `compiler/opt/lto` over verified `.axlto` MIR prior to codegen per `SPEC-75 AXS-LTO-003`). The linker consumes only explicit object-level facts: sections, symbols, relocations, COMDAT groups, unwind records, import/export descriptors, and embedded `.axmeta` source/ABI provenance (`REQ-LNK-002..003`).
2. **Self-contained native linking (`REQ-LNK-160`, `INV-BOOT-003`, `tasks/0804 §582.2, §582.194–196`)**: `compiler/link/` produces native executables (`.exe`), dynamic libraries (`.dll`), and static archives (`.lib`) directly in-process without invoking `link.exe`, `lld`, GNU `ld`, `gcc`, `clang`, or any external repair tool.

### `AXS-LNK-002` — Per-Module Separate Compilation Contract (`.obj` + `.axmi`) & Type/Coherence Invariants

1. **Per-module compilation unit (`0099`, `0164`, `0217`, `tasks/0369`, `SPEC-22`, `SPEC-24 AXS-ART-010`, `T067`)**:
   - In multi-module workspaces and package graphs, each Axiom module $M$ is compiled as an independent compilation unit producing `<module>.axmi` (binary semantic interface for downstream modules) and `<module>.obj` (relocatable COFF object containing machine sections, relocations, and `.axmeta` provenance).
   - When `M` has an unchanged `CodegenFingerprint` in `.axiom-cache` (`SPEC-22 AXS-INC-010..024`), the driver reuses the cached `<module>.obj` without re-running LIR lowering, register allocation, or machine encoding; editing a private function in $M_i$ re-typechecks and re-emits only $M_i\text{.obj}$ before re-linking (`T776`).
2. **Type-system and trait coherence invariants required for sound separate compilation (`REQ-LNK-122`, `REQ-LNK-140..146`, `0225 §31`, `0245 §3–27`)**:
   - **Orphan rule (`REQ-LNK-122`, `0225 §31`)**: `impl Trait for Type` is legal in module $M$ only if either `Trait` or `Type` is defined in the current package/module hierarchy, preventing two separately compiled `.obj` files from emitting conflicting trait implementations or vtables for the same `(Trait, Type)` pair.
   - **Canonical `TypeId` interning & nominal distinctness (`REQ-LNK-140..145`, `0245 §3–19`)**: Structurally identical generic instantiations intern to the exact same canonical `TypeId` (`REQ-LNK-140`, yielding identical mangled `COMDAT` keys across modules), `[N]T` array types of different compile-time lengths $N$ are distinct (`REQ-LNK-141`), nominal `struct` types and newtypes never implicitly convert even when layouts match (`REQ-LNK-142..143`), calling conventions (`Axiom`, `"C"`, `"system"`, `"interrupt"`) are part of canonical function-type identity (`REQ-LNK-144`), and closures with non-empty captures never coerce to bare `fn` pointers (`REQ-LNK-145`).
   - **Explicit public return types (`REQ-LNK-146`, `0245 §27`)**: Every `pub fn` declaration explicitly specifies its return type (defaulting to `()` when omitted) so `.axmi` interfaces and cross-object ABI fingerprints never depend on cross-module return-type inference.

### `AXS-LNK-003` — Deterministic Multi-Object & Archive Input Ordering and Foreign C Interop

1. **Canonical link input order (`REQ-LNK-030..039`, `REQ-LNK-050..055`, `REQ-LNK-135`, `REQ-LNK-150`, `0164 §24–33`, `tasks/0786 §564.4–6, §564.26–32`, `tasks/0804 §582.22–27`, `T067`)**:
   - The driver passes input `.obj` files to `compiler/link/` in a strict deterministic sequence: (a) workspace/package modules in topological module-graph order (ties broken by ascending canonical `ModulePath` ASCII order, independent of `--jobs N` worker completion order per `SPEC-23 AXS-PAR-024`), followed by (b) explicit positional `.obj` files in exact CLI order, and (c) static `.lib`/`.a` archives and import libraries in exact CLI / `@link` declaration order (`SPEC-26 AXS-WLIB-003`).
   - Archive member extraction is strictly demand-driven to a fixed point (`SPEC-26 AXS-WLIB-012`, `REQ-LNK-030`, `REQ-LNK-135`, `REQ-LNK-150`), with `--whole-archive` / group repetition supported when explicitly configured (`tasks/0804 §582.26–27`). Every extracted member retains its `(archive_path, member_name, member_offset, content_hash)` provenance for link maps and diagnostics (`tasks/0786 §564.32`).
2. **Foreign C/COFF object interop (`REQ-LNK-056`, `tasks/0786 §564.4`, `tasks/0804 §582.5–6`)**: Standard COFF `.obj` and `.lib` files produced by C/system toolchains are ingested directly into `LinkIR` alongside Axiom `.obj` files whenever their target architecture and ABI match (`AXS-LNK-005`).

### `AXS-LNK-004` — Machine Code Encoding 4.0 & Frame/Unwind Handoff to Object Writer

1. **Separation of Frame Layout from Prologue/Epilogue Generation (`REQ-LNK-123..131`, `0236 §1–28`)**:
   - `compiler/target/x64` separates `FrameLayout` computation from prologue/epilogue emission (`REQ-LNK-123`). Stack slots are allocated only for locals that escape to memory or spill (`REQ-LNK-125..126`); leaf functions requiring no stack storage, spills, or calls omit stack frame allocation and frame pointers (`REQ-LNK-124`, `REQ-LNK-130`).
   - Every non-leaf frame maintains 16-byte ABI stack alignment at call boundaries (`REQ-LNK-127`), never uses a red zone on Windows x64 (`REQ-LNK-128`), aligns and restores dynamic stack allocations (`REQ-LNK-129`), and emits deterministic callee-saved register save/restore sequences (`REQ-LNK-131`) paired with exact `.xdata` `UNWIND_INFO` and `.pdata` `RUNTIME_FUNCTION` records (`SPEC-54 AXS-PAN-020`).
2. **Machine Code Encoding 4.0 contract (`REQ-LNK-3434..3633`, `tasks/0802 §580.1–200`)**:
   - The ISA encoder is a pure deterministic function `(MachineInstruction, TargetDesc) -> EncodedInstruction` (`REQ-LNK-3434`) that selects the canonical shortest valid encoding (`REQ-LNK-3440`), enforces REX/VEX/EVEX register/operand legality (`REQ-LNK-3450`) and enabled target CPU feature gates (`REQ-LNK-3500`, `REQ-LNK-3600`), relaxes out-of-range short branches (`rel8`) to canonical `rel32` forms (`REQ-LNK-3480`), attaches source Machine IR provenance to every encoded instruction (`REQ-LNK-3534`), and hands off canonical fixup/relocation records (`REQ-LNK-3560`) to `ObjectWriter` (`SPEC-24 AXS-ART-020`) without invoking any external assembler (`REQ-LNK-3633`).

### `AXS-LNK-005` — Target, Architecture & Cross-Object ABI Validation

Before symbol merging, `compiler/link/` validates every input `.obj` and extracted `.lib` member (`REQ-LNK-144`, `REQ-LNK-148`, `0256 §4`, `tasks/0786 §564.169–170`, `tasks/0804 §582.162–170`, `T067`):
1. **Target header check**: COFF `Machine` (`IMAGE_FILE_MACHINE_AMD64 = 0x8664`), endianness, pointer width, and embedded `.axmeta` `TargetFingerprint` must match the active `LinkRequest.target`. Any mismatch emits `AX_LINK_ARTIFACT_TARGET_MISMATCH`.
2. **Cross-object symbol ABI check (`AX_LINK_ABI_MISMATCH`)**: When two Axiom `.obj` files carry `.axmeta` symbol descriptors for the same external symbol (e.g. a defining module and a referencing `extern` / cross-module declaration), the linker verifies that their calling conventions (`REQ-LNK-144`), parameter/return `AbiFingerprint`s, and symbol kinds (`Function` vs `Data` vs `TLS`) agree. Any discrepancy is rejected before layout with `AX_LINK_ABI_MISMATCH` (`data.symbol`, `data.expected_abi`, `data.found_abi`).

---

## 2. `LinkIR` Data Model, Symbol Resolution (`Strong` / `Weak` / `COMDAT`) & Demangled Diagnostics

### `AXS-LNK-010` — Format-Neutral `LinkIR` Intermediate Representation

`compiler/link/` normalizes all ingested COFF/ELF/Mach-O objects and archive members into `LinkIR` (`REQ-LNK-133`, `REQ-LNK-147`, `0256 §2–3`, `tasks/0786 §564.5–11, §564.33–36`, `tasks/0804 §582.3–7`):

```axiom
pub enum LinkSymBinding {
    Local,      // Object-local (IMAGE_SYM_CLASS_STATIC without global visibility)
    Global,     // Strong external definition or reference
    Weak,       // Weak external definition/fallback
    Comdat,     // Linkonce COMDAT definition (monomorphized generic, inline fn, vtable)
    Common,     // Tentative alignment/size-merged common block
    Absolute,   // Pinned constant/hardware address (IMAGE_SYM_ABSOLUTE, SPEC-55)
    Import      // Dynamic DLL import (__imp_<name> / short-import member, SPEC-26)
}

pub enum ComdatSelection {
    NoDuplicates,   // IMAGE_COMDAT_SELECT_NODUPLICATES (1)
    Any,            // IMAGE_COMDAT_SELECT_ANY (2): pick first in canonical link order
    SameSize,       // IMAGE_COMDAT_SELECT_SAME_SIZE (3): require equal byte size
    ExactMatch,     // IMAGE_COMDAT_SELECT_EXACT_MATCH (4): require byte-identical payload
    Associative,    // IMAGE_COMDAT_SELECT_ASSOCIATIVE (5): live iff leader section is live
    Largest         // IMAGE_COMDAT_SELECT_LARGEST (6): pick largest byte size
}

pub struct LinkSymbol {
    pub id: u32,
    pub mangled_name: Str,
    pub demangled_name: Str,        // Canonical Axiom path e.g. "math.vec.dot<f64>"
    pub binding: LinkSymBinding,
    pub kind: u8,                   // 1=Function, 2=Data, 3=RoData, 4=Bss, 5=Tls, 6=Abs
    pub defining_obj: u32,          // Object index (0 if undefined)
    pub defining_sec: u32,          // InputSectionId (0 if undefined/absolute/import)
    pub section_offset: u64,
    pub size: u64,
    pub align: u32,
    pub abi_fingerprint: u64,       // From .axmeta (0 for foreign C objects)
    pub def_span: Span,             // From .axmeta (Span.none() for foreign C objects)
    pub is_export: bool,
    pub is_used_root: bool
}
```

### `AXS-LNK-011` — Canonical Symbol Mangling, Demangling & `extern "C"` / `@export` Identity

1. **Deterministic Axiom mangling (`0164`, `tasks/0786`, `tasks/0804 §582.158–161`)**:
   - Ordinary Axiom functions, methods, statics, vtables, and monomorphized generic instances use canonical versioned mangling `_AX1_<pkg>_<module_path>_<item_name>$<canonical_type_args>` (with length-prefixed identifiers and canonical `TypeId` formatting per `REQ-LNK-140`).
   - `extern "C"` declarations, `@no_mangle` items, and `@export("custom_name")` exports bypass Axiom path mangling and use their exact unqualified or custom external symbol name (`tasks/0804 §582.160`, `SPEC-26 AXS-WLIB-004`).
2. **Lossless demangler (`T067`)**: `compiler/link/demangle` converts any `_AX1_...` symbol back into canonical dotted Axiom surface syntax (`pkg.module.Type.method<i32, view<u8>>`, never `::`) for diagnostics, link maps, and `inspect --emit=gc-sections`.

### `AXS-LNK-012` — Global Symbol Resolution Matrix (`Strong` vs `Weak` vs `Local` vs `Import`)

The symbol resolver merges symbols across all loaded `LinkModule` inputs in canonical order (`REQ-LNK-004..019`, `REQ-LNK-136`, `REQ-LNK-149`, `0164 §6–12`, `0239 §17`, `0256 §5–6`, `tasks/0786 §564.11–24`, `tasks/0804 §582.7–18`):
1. **`Local` isolation (`tasks/0786 §564.18`, `tasks/0804 §582.16`)**: `LinkSymBinding.Local` symbols are scoped strictly to their defining `LinkModule` and never collide with `Local` or `Global` symbols of the same name in other objects.
2. **`Strong` (`Global`) vs `Strong` (`Global`) (`REQ-LNK-010`, `REQ-LNK-136`, `REQ-LNK-149`)**: Two strong `Global` definitions of the same symbol name across input objects or extracted archive members are a hard link error (`AX_LINK_DUPLICATE_SYMBOL`). The linker NEVER silently picks one strong definition over another.
3. **`Strong` vs `Weak` (`0256 §6`, `tasks/0786 §564.14–15`, `tasks/0804 §582.10–12`)**: A single `Strong` definition overrides any number of `Weak` definitions of the same symbol. When only `Weak` definitions exist, the linker deterministically selects the first `Weak` definition in canonical input object order.
4. **Local definition vs archive/import (`AXS-WLIB-012`)**: A defined `Strong` or `Weak` symbol in an explicit `.obj` satisfies references before archive extraction; unextracted archive members defining that symbol are skipped.
5. **Unresolved references (`REQ-LNK-040`, `tasks/0786 §564.20`, `tasks/0804 §582.13`)**: Any symbol referenced by a reachable section that remains `Undefined` after fixed-point archive extraction and DLL import resolution is rejected with `AX_LINK_UNDEFINED_SYMBOL`.

### `AXS-LNK-013` — `COMDAT` Group Folding (`IMAGE_SCN_LNK_COMDAT`) for Generics, Vtables & Inline Templates

1. **Mandatory `COMDAT` emission for shared instantiations (`tasks/0526`, `tasks/0786 §564.53–56`, `tasks/0804 §582.19–21`, `SPEC-75 AXS-LTO-014, AXS-LTO-020`, `T775`)**:
   - When modules $M_1$ and $M_2$ are compiled separately (`--lto=off`) and both instantiate the same generic function `f<T>` (e.g. `std.vec.Vec.push<i32>`), inlineable template, or `dyn Trait` `.rdata` vtable (`SPEC-63`), each module emits the item's code/data section with COFF flag `IMAGE_SCN_LNK_COMDAT` (`0x00001000`) and a COMDAT symbol record keyed by the canonical mangled symbol name (`ComdatSelection.Any` or `ExactMatch`).
   - Associated `.pdata` and `.xdata` unwind subsections for `f<T>` are emitted in the same COMDAT group with `IMAGE_COMDAT_SELECT_ASSOCIATIVE` (`5`) referencing the leader `.text$<sym>` section index.
2. **Deterministic `COMDAT` folding (`tasks/0804 §582.19–21`, `T775`)**:
   - During symbol/section resolution, when multiple objects provide a `COMDAT` group with the same leader symbol key:
     - Under `Any`, the linker selects the leader section (and its `Associative` `.pdata`/`.xdata` children) from the lowest `defining_obj` in canonical link order and marks all duplicate COMDAT sections as `DiscardedComdat`.
     - Under `SameSize` or `ExactMatch`, the linker additionally verifies that duplicate sections have equal byte size or identical uncompressed bytes + relocations; a violation emits `AX_LINK_DUPLICATE_SYMBOL` (`data.reason = "comdat_mismatch"`).
   - All relocations targeting a discarded COMDAT copy are redirected to the surviving canonical representative section and symbol (`tasks/0804 §582.46`).

### `AXS-LNK-014` — Structured Linker Diagnostics Carrying Demangled Axiom Paths & Source Spans

Every linker error is a structured `Diagnostic` value (`AXD-001`, `AXD-050`, `REQ-LNK-040..049`, `tasks/0786 §564.165–170`, `tasks/0804 §582.165–170`, `T067`):
1. **`AX_LINK_DUPLICATE_SYMBOL`**: Reports `data.symbol` (raw symbol name), `data.demangled` (demangled Axiom path, e.g. `math.add`), `data.first_object`, `data.second_object`, and when `.axmeta` source span metadata is present, attaches the primary `Span` of the second definition and a secondary label pointing to the first definition's `Span`.
2. **`AX_LINK_UNDEFINED_SYMBOL`**: Reports `data.symbol`, `data.demangled`, `data.referencing_object`, `data.referencing_section`, `data.referencing_function` (demangled caller name), `data.searched_libraries`, and sets the primary `Span` to the call/reference site recorded in `.axmeta` (falling back to `Span.none()` per `AXD-051` only for foreign C objects lacking `.axmeta`).
3. **`AX_LINK_ABI_MISMATCH`**: Reports `data.symbol`, `data.demangled`, `data.expected_abi`, `data.found_abi`, `data.first_object`, and `data.second_object`, with primary and secondary spans from `.axmeta`.

---

## 3. Per-Item Section Emission, Root-Set Reachability Section GC, Unwind Association & Image Layout

### `AXS-LNK-020` — Per-Function & Per-Datum Section Subdivision (`-ffunction-sections` / `-fdata-sections` Equivalent)

1. **Default fine-grained section emission (`tasks/0526`, `tasks/0786 §564.33–43`, `tasks/0803 §581.26–45`, `tasks/0804 §582.32`, `SPEC-75 AXS-LTO-020`, `T775`)**:
   - `compiler/obj/` emits every function, constant table, vtable, and static variable into its own dedicated COFF subsection by default:
     - Functions: `.text$<mangled_sym>` (`IMAGE_SCN_CNT_CODE | IMAGE_SCN_MEM_EXECUTE | IMAGE_SCN_MEM_READ | IMAGE_SCN_LNK_COMDAT`)
     - Read-only constants & vtables: `.rdata$<mangled_sym>` (`IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_MEM_READ | IMAGE_SCN_LNK_COMDAT`)
     - Mutable initialized statics: `.data$<mangled_sym>` (`IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_WRITE | IMAGE_SCN_LNK_COMDAT`)
     - Zero-initialized statics: `.bss$<mangled_sym>` (`IMAGE_SCN_CNT_UNINITIALIZED_DATA | IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_WRITE | IMAGE_SCN_LNK_COMDAT`)
     - Unwind tables: `.pdata$<mangled_sym>` and `.xdata$<mangled_sym>` (`IMAGE_COMDAT_SELECT_ASSOCIATIVE` tied to `.text$<mangled_sym>`)
   - Explicit `@section("<custom>")` items (`SPEC-52 AXS-FRE-014`) are emitted into `<custom>` while preserving their per-item `InputSectionId` in `LinkIR`.

### `AXS-LNK-021` — Reachability Root Set (`@entry`, `@export`, `@used`, `@at`, Unwind & Reflection Roots)

When section garbage collection (`--gc-sections`, enabled by default for all `.exe` and `.dll` links; disabled for `--kind lib` static archives per `SPEC-26 AXS-WLIB-004`) constructs the reachability graph in `compiler/link/gc` (`REQ-LNK-134`, `REQ-LNK-152`, `REQ-LNK-157`, `tasks/0526`, `tasks/0786 §564.44–52`, `tasks/0804 §582.32–38`, `SPEC-75 AXS-LTO-005, AXS-LTO-021`, `T775`), the initial live worklist $R_{\text{root}}$ contains exactly:
1. **Entry point & startup roots (`REQ-LNK-157`, `tasks/0804 §582.150–151`)**: The image entry section (`mainCRTStartup` + `main` for hosted `.exe`; `@entry` function for freestanding images per `SPEC-52`; `_DllMainCRTStartup` for `.dll` per `SPEC-26 AXS-WLIB-022`).
2. **Binary exports (`REQ-LNK-134`, `tasks/0804 §582.149`)**: Every section defining an `@export` / `@export("...")` symbol (`LinkSymbol.is_export == true`).
3. **Explicit retention roots (`REQ-LNK-152`, `tasks/0786 §564.51`)**: Every section defining a `fn` or `static` annotated with `@used` (`SPEC-52 AXS-FRE-014`, `LinkSymbol.is_used_root == true`).
4. **Fixed-address hardware placement roots (`ADR-0001`, `SPEC-55 AXS-ADR-022`)**: Every section carrying a pinned VMA (`@at(addr)` / `@addr(addr)` placement declarations).
5. **Module initializers, TLS callbacks & runtime reflection roots (`tasks/0786 §564.45`, `tasks/0804 §582.37, §582.152–154`)**: Sections registered in module init/fini tables (`__ax_resolve_module_bindings` and package static initializers), PE `.tls` directory structures when `@thread_local` is used (`SPEC-32`), and runtime reflection descriptor tables for `@reflect(runtime)` types (`SPEC-61 AXS-RFL-002`).

### `AXS-LNK-022` — Deterministic Mark-Sweep Section GC & `.pdata`/`.xdata` Unwind Association

1. **Relocation-driven mark traversal (`tasks/0786 §564.46–50`, `tasks/0804 §582.34–40`, `T775`)**:
   - `compiler/link/gc` pops live `InputSectionId` nodes from a deterministic FIFO worklist in ascending `(object_index, section_index)` order.
   - For each relocation $r$ in a live section $S$, the target symbol $r\text{.symbol}$ is resolved to its surviving `defining_sec` $T$; if $T$ is not yet marked live, $T$ is marked `is_live = true` (`retention_reason = ReferencedBy(S, r.symbol)`) and pushed to the worklist.
   - **Forward unwind association (`tasks/0804 §582.38, §582.114, §582.180`)**: Marking a function code section `.text$<sym>` live automatically marks its `Associative` `.pdata$<sym>` and `.xdata$<sym>` unwind sections live (and recursively marks any personality/LSDA handler referenced by `.xdata$<sym>`). Conversely, `.pdata`/`.xdata` and `.axdbg`/debug sections NEVER reverse-root an otherwise unreferenced `.text$<sym>` section (`tasks/0804 §582.36`).
2. **Sweep & dangling-relocation invariant (`tasks/0804 §582.39–40`)**:
   - All `ALLOC` sections with `is_live == false` after worklist convergence (along with their associated `.pdata`/`.xdata` unwind entries) are swept before output section merging and address assignment.
   - Importing a single function from `std` or a multi-module library strips all unreferenced functions, unused generic instantiations, unreferenced `.rdata` constants/vtables, and unused runtime helpers from the final `.exe`/`.dll` (`T775`).
   - Post-GC invariant (`tasks/0804 §582.40`): zero live sections may retain a relocation targeting a swept section.

### `AXS-LNK-023` — Address-Safe Identical Code & Read-Only Data Folding (`Safe ICF`)

After section GC and before final address assignment (`REQ-LNK-151`, `tasks/0526`, `tasks/0786 §564.57–64`, `tasks/0804 §582.41–48`, `SPEC-75 AXS-LTO-022`):
1. **Code & `.rdata` equivalence**: Two live read-only sections (`.text$*` or `.rdata$*`) are in the same equivalence class iff their alignment, flags, raw byte payloads, and target-resolved relocation sequences are identical (up to recursive isomorphism). Writable `.data` and `.bss` sections are NEVER folded (`tasks/0786 §564.63`).
2. **Observable address identity preservation (`REQ-LNK-151`, `tasks/0804 §582.42, §582.44`)**: Under default `Safe ICF`, two distinct functions $f$ and $g$ are folded into the lowest-index canonical representative iff neither $f$ nor $g$ has its address observed by a non-call relocation (`address_taken == false`), or an explicit 5-byte `jmp representative` thunk preserves distinct function pointer addresses.

### `AXS-LNK-024` — Deterministic Section/Segment Layout, `W^X`, Branch Relaxation & Relocation Patching

1. **Output section merging & address spaces (`REQ-LNK-020..029`, `REQ-LNK-137..139`, `REQ-LNK-153..158`, `0164 §13–22`, `0185`, `0239 §20–32`, `tasks/0786 §564.36–43, §564.65–90`, `tasks/0804 §582.49–94`, `SPEC-26 AXS-WLIB-005`)**:
   - Surviving input sections are merged deterministically into canonical output sections (`.text`, `.rdata`, `.data`, `.bss`, `.pdata`, `.xdata`, `.idata`, `.edata`, `.tls`, `.reloc`) sorted by section kind and canonical input `(object_index, section_index)` order, padded with `0xCC` (`INT3`) in `.text` and `0x00` in data sections (`tasks/0786 §564.39`).
   - Output section alignment equals $\max(\text{input alignments}, \text{target policy alignment})$ (`tasks/0786 §564.38`). `VA`, `RVA` (`SectionAlignment = 0x1000`), and `FileOffset` (`FileAlignment = 0x200`) remain strictly distinct (`REQ-LNK-153`); `.bss` occupies `VirtualSize` without raw disk bytes (`tasks/0804 §582.58–59`).
   - **Mandatory `W^X` (`REQ-LNK-138`, `REQ-LNK-154`, `tasks/0804 §582.55–56`)**: No output section or segment may carry both `WRITE` and `EXECUTE` permissions.
2. **Checked relocation patching & no silent truncation (`REQ-LNK-020`, `REQ-LNK-137`, `REQ-LNK-155`, `tasks/0786 §564.65–69`, `tasks/0804 §582.67–74`, `T067`)**:
   - Static calls and data accesses within the image use direct RIP-relative (`IMAGE_REL_AMD64_REL32`, $S + A - P$) or 64-bit virtual address (`IMAGE_REL_AMD64_ADDR64`, $S + A$) relocations without unnecessary GOT/PLT indirection (`REQ-LNK-020`), while `.pdata`/`.xdata` entries use image-base-relative `ADDR32NB` ($S + A - \text{ImageBase}$) and section-relative `SECREL`/`SECTION` fixups.
   - Every patched displacement is range-checked against its target bit width (signed 32-bit `[-2^31, 2^31 - 1]` for `REL32`; unsigned 32-bit `< 2 GiB` for `ADDR32NB` / PE image size). Any overflow that cannot be relaxed emits `AX_LINK_RELOC_OUT_OF_RANGE` or `AX_LINK_IMAGE_TOO_LARGE` and NEVER truncates silently (`tasks/0804 §582.69–70`).

### `AXS-LNK-025` — Final Image Verifier & Reproducible Link Cache Contract

Before writing the output file to disk, `compiler/link/` runs the **Final Image Verifier** (`REQ-LNK-050`, `REQ-LNK-159..160`, `tasks/0786 §564.172–200`, `tasks/0804 §582.140–145, §582.172–199`):
1. Verifies that all PE/COFF headers, `SectionAlignment`/`FileAlignment` bounds, `W^X` flags, entry point `RVA` (inside `.text`), `.idata`/`.edata`/`.tls`/`.reloc` directories, and sorted `.pdata`/`.xdata` unwind ranges are structurally valid, that zero `.axmeta`/`.axmir`/`.axlto` sections remain (`SPEC-24 AXS-ART-022`), and that zero unresolved static relocations remain.
2. Identical input objects, archives, target configuration, and linker flags produce a byte-for-byte identical output binary (`TimeDateStamp = 0`, zero host paths, `INV-DET-001`, `INV-DET-002`).

---

## 4. CLI Flags, Diagnostics, Canonical Examples & Conformance Matrix

### `AXS-LNK-050` — CLI Flags & Linker v2 Diagnostic Summary

1. **CLI flags (`T067`, `T775`)**:
   - `--gc-sections` / `--no-gc-sections`: enables (default for `exe`/`dll`) or disables root-set reachability section garbage collection.
   - `axiom inspect --emit=link-map <inputs...>`: emits a deterministic report of resolved symbols, archive members extracted, output sections, `RVA`/`FileOffset`/`Size` layout, and `COMDAT` group selections.
   - `axiom inspect --emit=gc-sections <inputs...>`: emits a deterministic report listing every `Retained` section (with its `Root(kind)` or `ReferencedBy(caller_sec, symbol)` chain), every `FoldedComdat` section (with its selected representative), and every `DeadStripped` section.
2. **Diagnostics (`spec/diagnostics.md` §10.8 & §11, `LINK` area)**:
   - `AX_LINK_UNDEFINED_SYMBOL` (`E`, `T027`/`T067`): unresolved symbol after archive extraction and import resolution (`data.symbol`, `data.demangled`, `data.referencing_object`, `data.referencing_function`, primary call-site `Span`).
   - `AX_LINK_DUPLICATE_SYMBOL` (`E`, `T027`/`T067`): conflicting strong definitions or mismatched `ExactMatch`/`SameSize` COMDAT payloads across objects (`data.symbol`, `data.demangled`, `data.first_object`, `data.second_object`, primary/secondary `Span`s).
   - `AX_LINK_ABI_MISMATCH` (`E`, `T067`): cross-object calling convention, symbol kind, or `.axmeta` `AbiFingerprint` mismatch for the same external symbol (`data.symbol`, `data.demangled`, `data.expected_abi`, `data.found_abi`).
   - `AX_LINK_RELOC_OUT_OF_RANGE` (`E`, `T027`/`T067`), `AX_LINK_BAD_OBJECT` (`E`, `T027`/`T067`), `AX_LINK_IMAGE_TOO_LARGE` (`E`, `T027`/`T067`), `AX_LINK_BAD_ARCHIVE` (`E`, `T750`), `AX_LINK_LIBRARY_NOT_FOUND` (`E`, `T750`), `AX_LINK_DUPLICATE_EXPORT` (`E`, `T751`), `AX_LINK_AT_OVERLAP` (`E`, `T528`).

### `AXS-LNK-051` — Positive Canonical Examples (Separate Compilation, `COMDAT` Deduplication & Section GC)

```axiom
// === File 1: `util.ax` -> compiled to `util.axmi` + `util.obj` ===
module util

pub fn clamp_val<T: Ord + Copy>(v: view<T>, lo: T, hi: T) -> T {
    let cur = *v
    if cur < lo {
        lo
    } else if cur > hi {
        hi
    } else {
        cur
    }
}

pub fn live_scale(x: i32) -> i32 {
    let y = x * 2
    clamp_val(view(y), 0, 100)
}

// Unreferenced helper: emitted into `.text$_AX1_util_dead_heavy_helper`
// and swept by `--gc-sections` when linking `app.exe`.
pub fn dead_heavy_helper(x: i32) -> i32 {
    x * 999 + 77
}

// Explicit retention root: preserved by `--gc-sections` even without direct calls.
@used
pub static BUILD_COOKIE: u64 = 0x4158_494F_4D5F_3237u64
```

```axiom
// === File 2: `app.ax` -> compiled to `app.obj` using `util.axmi`, linked with `util.obj` ===
// Both `util.obj` and `app.obj` instantiate `util.clamp_val<i32>` in `IMAGE_SCN_LNK_COMDAT`
// sections; `compiler/link/gc` folds them to a single copy, keeps `live_scale` and
// `BUILD_COOKIE`, and strips `dead_heavy_helper` + its `.pdata`/`.xdata` unwind records.
module app

use util

pub fn main() -> i32 {
    let base = 18
    let a = util.clamp_val(view(base), 0, 100)
    let b = util.live_scale(a)
    if b == 36 {
        0
    } else {
        1
    }
}
```

### `AXS-LNK-052` — Negative Canonical Examples (Duplicate Strong Symbol, Demangled Undefined Symbol & ABI Mismatch)

```axiom
// === Negative Case 1: Duplicate strong symbol across separate `.obj` files ===
// `mod_a.obj` and `mod_b.obj` both define `@export("shared_gate") pub fn gate() -> i32`:
// ERROR [AX_LINK_DUPLICATE_SYMBOL]: duplicate strong symbol `shared_gate` (`mod_a.gate` in `mod_a.obj` vs `mod_b.gate` in `mod_b.obj`)

// === Negative Case 2: Undefined cross-object symbol with demangled Axiom path ===
// `app.ax` calls `extern "C" { fn missing_kernel_hook(x: i32) -> i32 }` with no defining `.obj`/`.lib`:
// ERROR [AX_LINK_UNDEFINED_SYMBOL]: undefined symbol `missing_kernel_hook` referenced by `app.main` in `app.obj`

// === Negative Case 3: Cross-object ABI / signature mismatch via `.axmeta` ===
// `provider.obj` defines `@no_mangle pub fn calc_crc(buf: view<u8>) -> u64` (Axiom ABI),
// while `consumer.obj` declares `extern "C" { fn calc_crc(ptr: *const u8) -> u32 }` (C ABI):
// ERROR [AX_LINK_ABI_MISMATCH]: ABI mismatch for symbol `calc_crc` between `consumer.obj` and `provider.obj`
```

### `AXS-LNK-053` — E18.6 Implementation & Conformance Matrix

| Task | Scope | Primary Verification Suite | Enforced Invariant |
|---|---|---|---|
| `T067` | Per-module separate compilation (`.obj` + `.axmi`), `LinkIR` multi-object & `.lib` archive linking, cross-object relocation patching (`ADDR64`, `REL32`, `.pdata`/`.xdata`), and demangled `AX_LINK_DUPLICATE_SYMBOL` / `AX_LINK_UNDEFINED_SYMBOL` / `AX_LINK_ABI_MISMATCH` diagnostics | `tests/link2` | `INV-LNK-001` |
| `T775` | Per-item section subdivision (`.text$<sym>`, `.rdata$<sym>`, `.data$<sym>`, `.bss$<sym>`), `IMAGE_SCN_LNK_COMDAT` generic/vtable deduplication, root-set mark-sweep section GC (`--gc-sections`), and `inspect --emit=link-map` / `--emit=gc-sections` | `tests/run/link_section_gc` | `INV-LNK-002` |
| `T776` | End-to-end E18.6 & P18 exit conformance: multi-module separate `.obj` + `.axmi` + `.lib` + `.dll` builds, `COMDAT` folding, dead-section stripping, single-module incremental `.obj` rebuilds, and `< 100 ms` compiler no-op rebuild | `tests/conformance/p18/e18_6_separate_compilation` | `INV-LNK-003` |

---

## Sources

- `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-070..074`: object model, COMDAT, symbols, relocations, linker contract)
- `spec/SPEC-24-artifact-format-module-interfaces.md` (`AXS-ART-010..024`: `.axmi`, `ObjectWriter` 3.0, `.axmeta`/`.axlto` sections)
- `spec/SPEC-26-windows-artifact-kinds.md` (`AXS-WLIB-001..032`: `--kind exe|obj|lib|dll`, COFF `.lib` archives, PE32+ `.dll`, short-import `.lib`)
- `spec/SPEC-75-lto-wpo-section-gc-pgo.md` (`AXS-LTO-014`, `AXS-LTO-020..022`: generic deduplication, section GC, safe ICF)
- `docs/base/specs/0099 - Axiom — Native Toolchain, Object Writer & Linker v0.1.md`
- `docs/base/specs/0164 - AXIOM LINKER v0.1.md` (`REQ-LNK-001..056`)
- `docs/base/specs/0185 - PE/COFF Linker.md`
- `docs/base/specs/0217 - OBJECTLINK-001 — Object Format & Native Linker.md`
- `docs/base/specs/0225` (§31, `REQ-LNK-122`), `0236` (§1–28, `REQ-LNK-123..131`), `0245` (§3–27, `REQ-LNK-140..146`)
- `docs/base/specs/0239 - 1. Nguyên tắc kiến trúc.md` (`REQ-LNK-132..139`)
- `docs/base/specs/0256 - LINKER-002 — AXIOM NATIVE LINKER.md` (`LinkIR`, `REQ-LNK-147..160`)
- `docs/base/tasks/0369 - BOOTSTRAP-110 — Object Writer, Linker & Native Binary Generation.md`
- `docs/base/tasks/0526 - BOOTSTRAP-267 — AXIOM LINK-TIME CODE GENERATION, LTO, WHOLE-PROGRAM OPTIMIZATION & BINARY SIZE.md` (`REQ-CORE-592..601`, `REQ-LNK-227`)
- `docs/base/tasks/0786 - BOOTSTRAP-564 — COMPILER LINKER 3.0 — WHOLE-PROGRAM LINKING, SYMBOL RESOLUTION, SECTION GC, ICF, RELAXATION, TLS, IMPORTEXPORT & FINAL IMAGE OPTIMIZAT.md` (`REQ-LNK-228..433`, `REQ-CORE-2541..2643`)
- `docs/base/tasks/0802 - BOOTSTRAP-580 — MACHINE CODE ENCODING 4.0.md` (`REQ-LNK-3434..3633`)
- `docs/base/tasks/0803 - BOOTSTRAP-581 — OBJECT FILE WRITER 3.0.md` (`REQ-LNK-3634..3784`)
- `docs/base/tasks/0804 - BOOTSTRAP-582 — NATIVE LINKER 4.0.md` (`REQ-LNK-3785..3993`)
