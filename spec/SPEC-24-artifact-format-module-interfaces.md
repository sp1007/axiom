# SPEC-24 — Canonical Axiom Artifact Format & Module Interface Specification (`.axmi`)

- **Status**: draft (T764, 2026-11-03)
- **Owner**: `axiom-architect`
- **Consolidates**: `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-070..074`), `0164` (`specs/0164`, Axiom Linker v0.1), `0582` (`tasks/0582`, BOOTSTRAP-323 `.axif`/`.axmi` semantic interface & interprocedural summary artifact engine), `0591` (`tasks/0591`, BOOTSTRAP-332 artifact format, distribution & transport independence), `0739` (`tasks/0739`, BOOTSTRAP-493 package ABI, binary interface distribution, precompiled generics & module interface files), `0787` (`tasks/0787`, BOOTSTRAP-565 Compiler Artifact Format 2.0: section schema, versioning, compatibility & zero-copy compilation), `0803` (`tasks/0803`, BOOTSTRAP-581 Object File Writer 3.0)
- **Covers**: `REQ-CORE-3109`, `REQ-CORE-3110`, `REQ-CORE-3123`, `REQ-CORE-3124`, `REQ-LNK-434..633`, `REQ-LNK-3634..3784`
- **Related**: `spec/SPEC-21-query-engine-semantic-db.md`, `spec/SPEC-22-incremental-compilation.md`, `spec/SPEC-23-parallel-compilation.md`, `spec/SPEC-26-windows-artifact-kinds.md`, `spec/SPEC-75-lto-wpo-section-gc-pgo.md`, `spec/diagnostics.md`, `spec/invariants.md`

## Tóm tắt

SPEC-24 định nghĩa chuẩn định dạng thành phẩm biên dịch (artifact format), tệp giao diện mô-đun (`.axmi`), các phân đoạn метаdata nhúng trong tệp đối tượng (`.axmeta`, `.axmir`, `.axlto`), và mô hình `ObjectWriter` độc lập định dạng cho trình biên dịch tự thân `compiler/` (E18.4):
1. **Phân loại thành phẩm & tuần tự hóa nhị phân tất định không con trỏ (`AXS-ART-001`..`005`)**: Phân biệt rõ tệp nguồn (`.ax`), giao diện ngữ nghĩa mô-đun (`.axmi`), mẫu MIR/LTO (`.axmir`/`.axlto`), tệp đối tượng khả định vị (`.obj`/`.axobj`), thư viện tĩnh (`.lib`), ảnh liên kết (`.exe`/`.dll`), thông tin gỡ lỗi (`.axdbg`) và gói phân phối (`.axpkg`). Mọi thành phẩm có đầu mục chuẩn 64-byte (`ArtifactHeader`), bảng phân đoạn (`SectionDescriptor`), định danh nội dung 128-bit BLAKE3 (`ArtifactId`), không chứa con trỏ tiến trình hay dấu thời gian, độc lập phương thức truyền tải và kiểm tra biên/phiên bản lược đồ nghiêm ngặt.
2. **Tệp giao diện mô-đun `.axmi` cho biên dịch riêng rẽ không cần mã nguồn (`AXS-ART-010`..`014`)**: Ghi lại toàn bộ khai báo `pub`, bảng `TypeId` chuẩn hóa, `layout_of`/`AbiFingerprint`, bảng `Trait`/`impl`, tóm tắt quyền sở hữu/capability/hiệu ứng/panic/concurrency (`tasks/0582`), giá trị `const` đã tính và mẫu `Verified MIR` cho hàm tổng quát (`generic`) / `@inline` / `comptime fn` (`tasks/0739`), cho phép nạp trực tiếp vào `CompilerDB` mà không cần đọc lại tệp `.ax` gốc.
3. **Phân đoạn đối tượng nhúng (`.axmeta`, `.axmir`, `.axlto`) & `ObjectWriter` 3.0 (`AXS-ART-020`..`024`)**: Nhúng các phân đoạn không cấp phát bộ nhớ chạy (`IMAGE_SCN_LNK_INFO | IMAGE_SCN_MEM_DISCARDABLE`) vào `.obj`/`.lib`, xác thực dấu vân tay đích/ABI/checksum khi liên kết và tự động lược bỏ khỏi `.exe`/`.dll` cuối cùng.

---

## 1. Artifact Taxonomy, Canonical Container Header, Section Table & Binary Serialization

### `AXS-ART-001` — Artifact Family Taxonomy, Transport Independence & Source Authority

1. **Explicit artifact taxonomy (`REQ-CORE-3110`, `REQ-LNK-434..435`, `tasks/0582 §323.2`, `tasks/0591 §2–3`, `tasks/0787 §565.1–2`)**: The Axiom toolchain strictly distinguishes the role and representation of every artifact family:

   | Family / Extension | Canonical Kind | Semantic & Pipeline Role |
   |---|---|---|
   | `.ax` (corpus `.axm`) | `Source` | Authoritative UTF-8 source text (`SPEC-01`) |
   | `.axmi` (corpus `.axif`/`.axsem`) | `ModuleInterface` | Proven public declarations, types, traits, ABI/layout, capability/effect summaries, `const` values & generic MIR templates |
   | `.axmir` | `MirArtifact` | Standalone or embedded canonical `Verified MIR` bodies |
   | `.axlto` | `LtoSummary` | Interprocedural call graph, alias/escape/effect summaries, inline candidates & LTO MIR bitcode (`SPEC-75`) |
   | `.obj` / `.o` (corpus `.axo`/`.axobj`) | `RelocatableObject` | Machine code, data, symbols, relocations, unwind/debug sections & embedded `.axmeta`/`.axlto` sections (`SPEC-26`) |
   | `.lib` / `.a` (corpus `.axlib`) | `StaticArchive` | Deterministic COFF/ar archive of relocatable objects or short-import members (`SPEC-26`) |
   | `.exe` / `.dll` / `.so` / `.dylib` | `LinkedImage` | Final linked executable or dynamic shared library (`SPEC-26`) |
   | `.axdbg` / `.pdb` | `DebugArtifact` | Detached source mapping, line tables, variable locations & unwind references |
   | `.axpkg` | `PackageBundle` | Content-addressed package archive containing manifest, `.axmi`, native variants & provenance |

2. **Source authority invariant (`REQ-LNK-435`, `REQ-LNK-581..583`, `REQ-LNK-633 #1–2`)**: Artifacts transmit proven compiler facts and cached codegen outputs across compilations (`REQ-CORE-3109`), but NEVER replace source semantics as a competing source of truth. Purging cached artifacts never alters program semantics (`REQ-LNK-582`).
3. **Transport & extension independence (`REQ-CORE-3123..3124`, `tasks/0591 §1–3`, `REQ-LNK-633 #62–63`)**: Artifact semantics and content hashes are invariant across filesystem storage, HTTPS, Git, S3/object stores, LAN mirrors, and offline/air-gapped media. Filename extensions are never trusted as semantic authority; the reader validates the binary magic and `artifact_kind` header field before parsing.

### `AXS-ART-002` — Canonical `ArtifactHeader`, Magic Bytes & `ArtifactId` Identity

1. **Fixed 64-byte header (`REQ-LNK-436..438`, `REQ-LNK-443..445`, `0787 §565.3–5, §565.10–12`)**: Every standalone Axiom binary artifact (`.axmi`, `.axmir`, `.axlto`, `.axdbg`, `.axpkg`) and every embedded `.axmeta`/`.axlto` section payload begins with a 64-byte little-endian `ArtifactHeader`:

```axiom
struct Fingerprint128 {
    lo: u64,
    hi: u64
}

struct ArtifactId {
    content_hash: Fingerprint128,
    schema_id: u16,
    schema_version: u16
}

@repr(C)
struct ArtifactHeader {
    magic: [8]u8,                      // Family magic: "AXMI0001", "AXMIR001", "AXLTO001", "AXMETA01", "AXDBG001", "AXPKG001"
    format_family: u16,                // 1=AXMI, 2=AXMIR, 3=AXLTO, 4=AXMETA, 5=AXDBG, 6=AXPKG
    schema_version: u16,               // Monotonic schema version (v1 = 1)
    artifact_kind: u16,                // Matches format_family / sub-kind
    flags: u16,                        // Bit 0: little_endian (1), Bit 1: deterministic (1), Bit 2: has_lto, Bit 3: compressed
    target_fingerprint: Fingerprint128,// TargetDesc + ABI + CPU features digest (0 for target-neutral)
    interface_fingerprint: Fingerprint128, // Tier-2a InterfaceFingerprint (SPEC-22 AXS-INC-002)
    section_count: u32,                // Number of SectionDescriptor entries in SectionTable
    producer_version: u32,             // Compiler semantic + build version tag
    payload_offset: u64,               // Byte offset from start of artifact to payload
    payload_size: u64,                 // Total byte length of serialized section table + payload
    content_hash: Fingerprint128       // BLAKE3-128 over canonical header[0..48] + section table + uncompressed payload
}
```

2. **Hash agility & integrity check (`REQ-LNK-437..438`, `REQ-LNK-565`, `REQ-LNK-633 #5, #22`)**: `content_hash` defaults to 128-bit domain-prefixed BLAKE3 (`"AXIOM-ART-v1"`) over the canonical serialized bytes (`SPEC-22 AXS-INC-001`). Any magic mismatch, unsupported endianness (`flags & 1 == 0`), or `content_hash` mismatch is rejected immediately before dereferencing any section payload.

### `AXS-ART-003` — Canonical Pointer-Free Encoding, Scoped IDs & Bounds-Checked Offsets

1. **Zero pointers or host state (`REQ-LNK-439..440`, `REQ-LNK-530..533`, `REQ-LNK-633 #3–8`)**: Artifacts SHALL NEVER serialize raw host pointers, virtual addresses, arena addresses, OS handles, process IDs, wall-clock timestamps, or unremapped absolute host filesystem paths (`INV-DET-001`, `INV-DET-002`).
2. **Explicit ID scopes (`REQ-LNK-441..442`, `0787 §565.8–9`)**: All serialized index references (`FileId`, `StringId`, `SymbolId`, `TypeId`, `FunctionId`, `BlockId`, `InstructionId`, `SectionId`) carry an explicit scope domain (`ArtifactLocal`, `PackageLocal`, `WorkspaceLocal`, or `GlobalContentAddressed`) and are mapped through the artifact's `IDTable` and deduplicated `StringTable` (`REQ-LNK-456..457`).
3. **Relative offsets & checked bounds (`REQ-LNK-446..448`, `REQ-LNK-633 #9–10, #51–61`)**: Every offset is `relative_to_artifact` (or relative to its owning section base). The reader checks `offset <= total_size` and `offset + size <= total_size` using checked 64-bit arithmetic before every slice or table access.

### `AXS-ART-004` — Section Table, `SectionDescriptor`, Lazy Loading & Validated `MMAPABLE` Access

1. **Section table layout (`REQ-LNK-449..452`, `0787 §565.16–19`)**: Immediately following `ArtifactHeader`, an artifact stores an array of `section_count` 48-byte `SectionDescriptor` records sorted by ascending `(section_type, id)`:

```axiom
@repr(C)
struct SectionDescriptor {
    id: u32,
    section_type: u16,          // 1=Strings, 2=Symbols, 3=Types, 4=Traits, 5=Functions, 6=TypesLayout,
                                // 7=ConstValues, 8=GenericMir, 9=EffectsCapabilities, 10=LtoSummary,
                                // 11=Dependencies, 12=Provenance, 13=AIIndex, 14=DebugMap
    flags: u16,                 // 0x01=READ_ONLY, 0x02=MMAPABLE, 0x04=COMPRESSED, 0x08=DEDUPLICABLE,
                                // 0x10=OPTIONAL, 0x20=TARGET_SPECIFIC, 0x40=PUBLIC
    alignment: u32,             // Power-of-two byte alignment (1, 4, 8, 16)
    offset: u64,                // Byte offset relative to start of artifact
    compressed_size: u64,       // Stored byte size in artifact payload
    uncompressed_size: u64,     // Canonical uncompressed byte size
    checksum: Fingerprint128    // BLAKE3-128 of uncompressed section bytes
}
```

2. **Demand-driven lazy loading & `Mmap` vs `Buffered` equivalence (`REQ-LNK-453..455`, `REQ-LNK-499..501`, `REQ-LNK-535..537`, `REQ-LNK-555..562`, `REQ-LNK-572..577`, `REQ-LNK-633 #47–50, #114–115`)**:
   - `ArtifactReader` (`open`, `validate`, `section`, `symbols`, `dependencies`, `metadata`) validates `ArtifactHeader` and `SectionDescriptor[]` upfront (checking non-overlapping bounds and power-of-two alignments), but loads and verifies individual section payloads lazily on demand (`REQ-LNK-499`, `REQ-LNK-556`).
   - Sections marked `MMAPABLE` may be shared zero-copy across concurrent reader threads and `CompilerDB` snapshots (`REQ-LNK-574..575`) only after validating alignment, little-endian representation, schema version, and `checksum`; arbitrary byte buffers are never cast to native host structs without field validation (`REQ-LNK-455`). `MmapArtifactReader` and `BufferedArtifactReader` produce identical semantic results.
   - Optional section compression (`COMPRESSED`) never alters canonical `ArtifactId` or `checksum` (`REQ-LNK-536`).

### `AXS-ART-005` — Schema Evolution, Compatibility Matrix & Atomic Cache Publication

1. **Three-part version model & compatibility classes (`REQ-LNK-484..490`, `REQ-LNK-584..595`, `0787 §565.51–57, §565.151–162`)**:
   - Producer metadata distinguishes `compiler_semantic_version`, `artifact_schema_version`, and `compiler_impl_version`. Implementation-only compiler rebuilds that keep `compiler_semantic_version` and `artifact_schema_version` unchanged remain `Exact` compatible (`REQ-LNK-485`, `REQ-LNK-633 #165`).
   - Unknown section handling (`REQ-LNK-591..592`, `REQ-LNK-633 #13–14`): an unknown section without `OPTIONAL` (`0x10`) is rejected (`AX_LINK_ARTIFACT_SCHEMA_MISMATCH`); an unknown section with `OPTIONAL` is safely skipped for forward compatibility.
   - Schema migration (`Transformable`) is always an explicit out-of-place step (`old -> validator -> migrator -> new`) recording `source_artifact_hash`, `source_schema`, and `target_schema`; cached artifacts are never mutated in place (`REQ-LNK-488..491`).
2. **Atomic publication, content-addressed storage & Merkle chunking (`REQ-LNK-492..498`, `REQ-LNK-560..571`, `REQ-LNK-578..580`)**:
   - Every artifact write follows `write_temp -> validate -> compute_hash -> atomic_rename` (`SPEC-22 AXS-INC-022`), ensuring partial files from crashes never enter `ArtifactStore`.
   - Content-addressed stores (`cache/<xx>/<yy>/<hash>`) deduplicate identical artifacts and support Merkle-tree chunking (`REQ-LNK-495..498`) for partial remote fetch and deduplicated `SingleFlightLatch` downloads (`REQ-LNK-567..568`).

---

## 2. Module Interface Files (`.axmi`) & Source-Free Separate Compilation

### `AXS-ART-010` — `.axmi` Module Interface Contract & Source-Free `CompilerDB` Population

1. **Purpose & source-free compilation (`REQ-CORE-3109`, `REQ-LNK-458..465`, `REQ-LNK-506..507`, `REQ-LNK-540..541`, `tasks/0582 §323.1–12`, `tasks/0739 §493.1–25`, `T765`)**:
   - Compiling a module `M` with `--emit=axmi` (or as part of package/library compilation) produces `<module>.axmi` (`magic = "AXMI0001"`), the canonical binary module interface unifying corpus `.axif` and `.axsem`.
   - `.axmi` contains the complete public semantic surface of `M` required by downstream modules: exported declarations (`pub fn`, `pub struct`, `pub enum`, `pub union`, `pub trait`, `pub type`, `pub const`, `pub static`, `pub extern`, and `pub use` re-exports), canonical `TypeId` definitions, trait implementations, `layout_of` / `AbiFingerprint` records, ownership/capability/effect summaries, evaluated `const` values, and generic/`@inline`/`comptime` MIR templates.
   - Private non-inlined function bodies, private module-internal helper items, and local variable spans of non-template functions are stripped (`REQ-LNK-540`).
2. **Direct `CompilerDB` ingestion (`T765`)**: When a downstream compilation resolves `use M`, `CompilerDB` (`SPEC-21`) loads `M.axmi` and directly populates `module_def_map(M)`, `item_signature(def)`, `trait_solve`, `layout_of`, `const_eval`, and generic `mir_body` templates without reading, lexing, or parsing `M.ax`.

### `AXS-ART-011` — Canonical `TypeId` Table, Nominal Identity & Trait Coherence Summaries

1. **Self-contained type DAG (`REQ-LNK-459..461`, `tasks/0739 §493.8–12`, `T765`)**: The `.axmi` `Types` section serializes every exported and reachable type in topological order using canonical `SemanticKey = (PackageName, ModulePath, ItemNamespace, Disambiguator, CanonicalName, GenericArgs)` (`SPEC-21 AXS-QRY-003`). Nominal ADT identity (`struct`, `enum`, `union`) is preserved across compilation sessions (`REQ-LNK-460`).
2. **Generics, traits & `impl` tables (`REQ-LNK-511`, `tasks/0582 §323.6–8`, `tasks/0739 §493.11–14`)**: The `Traits` section records generic type/const parameters, `where` clauses, supertraits, associated types/constants, `dyn Trait` object-safety flags (`SPEC-63`), and all exported `impl Trait for Type` headers so downstream trait resolution and coherence checks succeed identically to source compilation.

### `AXS-ART-012` — Interprocedural Ownership, Capability, Effect, Panic & Concurrency Summaries

To verify callers across module boundaries without re-analyzing upstream function bodies (`REQ-CORE-3109`, `REQ-LNK-464`, `REQ-LNK-510`, `tasks/0582 §323.3–4, §323.9–16`, `T765`), every exported callable in the `.axmi` `EffectsCapabilities` / `Functions` section records a `FnContractSummary`:
1. **Ownership & capability flow**: Per-parameter passing mode (`Move`, `Copy`, `View`, `MutView`), returned capability provenance mask (identifying which input `view<T>` / `mut_view<T>` parameters or `'static` roots a returned view borrows from), and alias/exclusivity summary.
2. **Effects & safety profile**: Proven effect mask (`Pure`, `ReadsMem`, `WritesMem`, `Allocates`, `Blocking`, `OsIo`, `Ffi`, `Unsafe`), required authority capability tokens (`FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap` per `SPEC-53`), and panic contract (`NoPanic` vs `MayPanic` per `SPEC-54`).
3. **Concurrency, async & target features**: Auto-trait markers (`Send`, `Share` per `SPEC-30`) on exported ADTs and `async fn` future state machines (`SPEC-33`), plus `@target_feature` / `@multiversion` clone masks (`SPEC-44`).

### `AXS-ART-013` — Exported `const` Payloads & Generic / Inlineable Verified MIR Templates

1. **Evaluated constants (`REQ-LNK-513..514`, `tasks/0739 §493.15`)**: The `ConstValues` section stores canonical `ConstValue` payloads (`Int`, `Int128`, `Float`, `Bool`, `Char`, `Str`, `Aggregate`, `FnRef`) and their 128-bit digests for all exported `const` items and associated constants.
2. **Pre-verified MIR templates (`REQ-LNK-466..469`, `REQ-LNK-512`, `REQ-LNK-523`, `tasks/0739 §493.16–24`, `0787 §565.33–36, §565.90`, `T765`)**:
   - The `GenericMir` section serializes canonical **Verified MIR** bodies for exported generic functions (`fn f<T>(...)`), `@inline` functions, and `comptime fn` bodies.
   - Every MIR template MUST pass the MIR verifier (`INV-PIPE-002`) before serialization into `.axmi` and MUST pass structural/type/ownership verification upon deserialization before downstream monomorphization, inlining, or CTFE.
   - MIR schema version is checked strictly (`AXS-ART-005`); incompatible MIR versions emit `AX_LINK_ARTIFACT_SCHEMA_MISMATCH` and never silently reinterpret opcodes (`REQ-LNK-469`).

### `AXS-ART-014` — Artifact Freshness, Dependency Graph, AI Query Index & Semantic Diff

1. **Freshness & fine-grained invalidation (`REQ-LNK-480..483`, `REQ-LNK-502..515`, `0787 §565.47–50, §565.69–82`)**: `.axmi` records explicit `ArtifactDependency` edges (`SemanticInput`, `IRInput`, `LTOInput`, `NativeObject`, `Debug`, `Runtime`, `Resource`) and per-tier fingerprints (`InterfaceFingerprint`, `AbiFingerprint`, `BodyFingerprint`). `CompilerDB` classifies loaded artifacts as `Fresh`, `Stale`, `Unknown`, or `Invalid` (`REQ-LNK-505`), reusing `.axmi` when an upstream module undergoes an implementation-only edit (`InterfaceFingerprint` unchanged, `REQ-LNK-506..507`) while invalidating downstream consumers on `API`, `ABI`, `Layout`, `Effect`, `TraitImpl`, or `ConstValue` changes (`REQ-LNK-508..514`).
2. **AI query index & semantic diff (`REQ-LNK-542..547`, `0787 §565.109–114`)**: Optional `AIIndex` sections tag every entry with its provenance (`CompilerFact`, `DerivedFact`, `Heuristic`, `GeneratedDescription`); `SemanticTables` always win over `AIIndex` on any discrepancy (`REQ-LNK-544`). `axiom inspect --axmi` / `artifact diff` computes structured diffs across `API`, `ABI`, `Layout`, `Trait`, `Effect`, and `Dependency` dimensions.

---

## 3. Embedded Object/LTO Sections (`.axmeta`, `.axmir`, `.axlto`) & Object Writer 3.0

### `AXS-ART-020` — Format-Independent Object Model & Object Writer 3.0 Boundary

1. **Format-neutral `ObjectArtifact` model (`REQ-LNK-3634..3658`, `REQ-LNK-3718..3746`, `REQ-LNK-3758..3784`, `SPEC-04 AXS-EXT-070..074`, `tasks/0803 §581.1–25, §581.85–150, §581.200`, `T766`)**:
   - `compiler/obj/` constructs a target-format-independent `ObjectArtifact { header, sections, symbols, relocations, comdat_groups, imports, exports, tls, debug, unwind, metadata }` from encoded machine instructions, data, fixups, and frame/unwind records without leaking COFF/ELF/Mach-O/WASM format specifics into machine instruction encoding (`REQ-LNK-3635..3636`).
   - Canonical section kinds (`CODE`, `RODATA`, `DATA`, `BSS`, `TLS_DATA`, `TLS_BSS`, `UNWIND`, `DEBUG`, `RESOURCE`, `METADATA`, `LINKER_METADATA`), flags (`ALLOC`, `EXEC`, `WRITE`, `READONLY`, `TLS`, `DEBUG`, `MERGE`, `STRINGS`, `DISCARDABLE`), power-of-two alignments, COMDAT groups (`key`, `selection`, `members`), symbol bindings (`LOCAL`, `GLOBAL`, `WEAK`, `IMPORT`, `EXPORT`), and checked relocations (`S + A`, `S + A - P`) are serialized deterministically into PE/COFF (`.obj`), ELF64 (`.o`), Mach-O (`.o`), or WASM (`.wasm`) (`REQ-LNK-3659..3717`).
   - **No repair stage & no hidden linker (`REQ-LNK-3764`, `REQ-LNK-3779..3782`)**: `ObjectWriter` validates all section bounds, symbol indices, alignments, and relocation widths before serialization and NEVER repairs illegal instructions, unresolved virtual registers, or invalid frames.

### `AXS-ART-021` — Embedded COFF/Object Metadata & LTO Sections (`.axmeta`, `.axmir`, `.axlto`)

When compiling an Axiom module to a relocatable object (`.obj` / `.o`) or static archive (`.lib` / `.a`), `compiler/artifact/container` embeds non-alloc, discardable custom metadata sections (`SPEC-04 AXS-EXT-071`, `REQ-LNK-470..476`, `REQ-LNK-3731..3733`, `tasks/0787 §565.37–43`, `tasks/0803 §581.98–100`, `T766`):

| Section Name | Magic | COFF Section Characteristics | Payload Summary |
|---|---|---|---|
| `.axmeta` | `"AXMETA01"` | `IMAGE_SCN_LNK_INFO \| IMAGE_SCN_MEM_DISCARDABLE \| IMAGE_SCN_MEM_READ` (`0x42000200`) | Embedded `.axmi` summary: `ArtifactHeader`, `TargetFingerprint`, `InterfaceFingerprint`, `AbiFingerprint`, exported symbol/type/capability contracts |
| `.axlto` | `"AXLTO001"` | `IMAGE_SCN_LNK_INFO \| IMAGE_SCN_MEM_DISCARDABLE \| IMAGE_SCN_MEM_READ` (`0x42000200`) | Interprocedural LTO summary (`SPEC-75`): call graph, alias/escape/effect summaries, inline candidates, specialization keys & `Verified MIR` bitcode |
| `.axmir` | `"AXMIR001"` | `IMAGE_SCN_LNK_INFO \| IMAGE_SCN_MEM_DISCARDABLE \| IMAGE_SCN_MEM_READ` (`0x42000200`) | Optional standalone/embedded `Verified MIR` body table for whole-program verification or cross-module monomorphization |

### `AXS-ART-022` — Link-Time Validation, LTO Ingestion & Final Image Stripping

1. **Link-time verification (`REQ-LNK-521..525`, `REQ-LNK-3747..3754`, `T766`)**: Before symbol resolution and LTO, `compiler/link/` inspects every input `.obj` and extracted `.lib` member:
   - If the object contains `.axmeta` or `.axlto`, the container reader validates `ArtifactHeader` magic, `schema_version`, `TargetFingerprint`, `AbiFingerprint`, and BLAKE3 `content_hash`. Corrupt or mismatched sections are rejected with `AX_LINK_BAD_ARTIFACT`, `AX_LINK_ARTIFACT_SCHEMA_MISMATCH`, or `AX_LINK_ARTIFACT_TARGET_MISMATCH`.
   - Foreign C/system COFF `.obj` and `.lib` inputs that lack `.axmeta` are ingested directly through the standard COFF symbol/relocation pipeline without requiring conversion to `.axobj` (`REQ-LNK-476`).
2. **Mandatory stripping from final `.exe` / `.dll` (`T766`)**: After link-time verification and LTO optimization (`SPEC-75`), `LinkerCore` and `PeImageWriter` **strip** all non-alloc `.axmeta`, `.axlto`, and `.axmir` (`IMAGE_SCN_LNK_INFO` / `IMAGE_SCN_MEM_DISCARDABLE`) sections so they NEVER appear in the final `.exe` or `.dll` section table or mapped virtual memory.

### `AXS-ART-023` — Target, ABI, Toolchain, Profile & CPU-Variant Fingerprint Binding

Every `.axmi` and `.axmeta` container records `TargetFingerprint` (`arch`, `os`, `abi`, `endianness`, `pointer_width`, `cpu_feature_mask`, `object_format`), `AbiFingerprint` (`calling_convention`, `type_abi_version`, `platform_abi`), `StdlibFingerprint`, `ProfileFingerprint` (`opt_profile`, `safety_profile`, `panic_strategy`), and multi-version CPU variant metadata (`baseline`, `avx2`, `avx512`, `neon`, `sve`) (`REQ-LNK-462..463`, `REQ-LNK-596..612`, `0787 §565.29–30, §565.163–179`). Cross-compilation never leaks host CPU features into target cache keys (`REQ-LNK-612`), and machine artifacts are never reused across mismatched targets or ABIs (`REQ-LNK-463`, `REQ-LNK-633 #29–37`).

### `AXS-ART-024` — Standalone Package Bundles (`.axpkg`) & Detached Debug Artifacts (`.axdbg`)

1. **Package container (`.axpkg`, `REQ-LNK-479..481`, `REQ-LNK-526..529`, `REQ-LNK-617..622`)**: Bundles package manifest, `.axmi` interfaces, target-specific `.obj`/`.lib`/`.dll` variants, `Provenance { source_hashes, dependency_hashes, compiler_build_id, target, configuration }`, and trust states (`Untrusted`, `Validated`, `TrustedByBuild`, `Signed`). Cryptographic signatures never bypass structural or semantic validation (`REQ-LNK-527`, `REQ-LNK-633 #87–88`).
2. **Detached debug container (`.axdbg`, `REQ-LNK-477..478`, `REQ-LNK-517..518`, `REQ-LNK-625`)**: Binds source-to-machine mappings, line tables, and unwind references to the exact `CodegenFingerprint` / machine section hash while remaining removable from release binaries (`REQ-LNK-633 #41–43, #143`).

---

## 4. CLI Inspection, Diagnostics, Canonical Examples & Conformance Matrix

### `AXS-ART-050` — CLI Flags & Artifact Diagnostic Taxonomy

1. **CLI interface (`REQ-LNK-613..616`, `T765`, `T766`)**:
   - `axiom build --emit=axmi` (or `axiom compile --emit=axmi`) emits `<module>.axmi` alongside or independent of `.obj`/`.lib`/`.dll`.
   - `axiom inspect --axmi <file>` and `axiom inspect --artifact-sections <file>` (along with `axiom artifact info|sections|symbols|deps|validate|diff|hash`) emit deterministic human/JSON summaries of headers, `InterfaceFingerprint`, exported items, generic MIR templates, and `.axmeta`/`.axlto` sections without parsing source files (`REQ-LNK-633 #179`).
2. **Diagnostic codes (`spec/diagnostics.md` §11, `LINK` area)**:
   - `AX_LINK_BAD_ARTIFACT` (`error`, `T765`/`T766`): invalid magic, truncated header or section table, out-of-bounds offset/size, overlapping sections, or failed BLAKE3 `content_hash`/`checksum` in `.axmi`, `.axmeta`, `.axlto`, or `.axpkg`.
   - `AX_LINK_ARTIFACT_SCHEMA_MISMATCH` (`error`, `T765`/`T766`): unsupported `schema_version`, unknown non-optional section (`RequiredUnknown`), or incompatible MIR/LTO/interface schema version (`data.expected_version`, `data.found_version`).
   - `AX_LINK_ARTIFACT_TARGET_MISMATCH` (`error`, `T765`/`T766`): `TargetFingerprint`, endianness, pointer width, required CPU features, `AbiFingerprint`, or profile/panic strategy in `.axmi`/`.axmeta`/`.obj` conflicts with the active compilation target (`data.expected_target`, `data.found_target`).

### `AXS-ART-051` — Positive Canonical Examples (Source-Free Separate Compilation via `.axmi` + `.obj`)

```axiom
// === Step 1: Compile upstream `vecmath.ax` to `vecmath.axmi` + `vecmath.obj` ===
// Command: axiom build vecmath.ax --kind obj --emit=axmi -o vecmath.obj
// Afterwards, `vecmath.ax` is removed/hidden; only `vecmath.axmi` and `vecmath.obj` remain.
module vecmath

pub const SCALE_FACTOR: i32 = 4

@repr(C)
pub struct Pair {
    pub x: i32,
    pub y: i32
}

pub trait Metric {
    fn weight(self: view<Self>) -> i32
}

impl Metric for Pair {
    fn weight(self: view<Pair>) -> i32 {
        (self.x + self.y) * SCALE_FACTOR
    }
}

pub fn clamp_pair<T: Metric>(item: view<T>, floor: i32) -> i32 {
    let w = item.weight()
    if w < floor { floor } else { w }
}
```

```axiom
// === Step 2: Compile downstream `app.ax` using ONLY `vecmath.axmi` + `vecmath.obj` ===
// Command: axiom build app.ax vecmath.obj --axmi vecmath=vecmath.axmi -o app.exe
// `CompilerDB` loads `Pair`, `SCALE_FACTOR`, `impl Metric for Pair`, capability contracts,
// and the verified generic MIR template `clamp_pair<T>` directly from `vecmath.axmi`.
// `LinkerCore` verifies `.axmeta`/`.axlto` in `vecmath.obj` and strips them from `app.exe`.
module app

use vecmath
use vecmath.Metric

pub fn main() -> i32 {
    let p = vecmath.Pair { x: 3, y: 5 }
    let score = vecmath.clamp_pair(view(p), 10)
    if score == 32 {
        0
    } else {
        1
    }
}
```

### `AXS-ART-052` — Negative Canonical Examples (Corrupt Checksum, Schema & Target Mismatch)

```axiom
// === Negative Case 1: Corrupted `.axmi` or `.axmeta` payload bytes ===
// Flipping 1 byte in `vecmath.axmi` or in the `.axmeta` section of `vecmath.obj` invalidates
// the BLAKE3-128 `content_hash` / `SectionDescriptor.checksum`:
// Command: axiom build app.ax vecmath_corrupt.obj --axmi vecmath=vecmath_corrupt.axmi
// ERROR [AX_LINK_BAD_ARTIFACT]: artifact `vecmath_corrupt.axmi` failed integrity verification (BLAKE3 checksum mismatch)

// === Negative Case 2: Incompatible `.axmi` / `.axmeta` schema version ===
// Loading an artifact with `schema_version = 99` or an unknown required section:
// ERROR [AX_LINK_ARTIFACT_SCHEMA_MISMATCH]: artifact `vecmath_v99.axmi` has schema version 99, expected 1

// === Negative Case 3: Cross-target or ABI mismatch ===
// Consuming an `.axmi`/`.obj` built for a mismatched target/ABI or incompatible panic strategy:
// ERROR [AX_LINK_ARTIFACT_TARGET_MISMATCH]: artifact `vecmath_linux.obj` target `x86_64-linux` does not match active target `x86_64-windows`
```

### `AXS-ART-053` — E18.4 Implementation & Verification Matrix

| Task | Scope | Required Verification Target | Invariant ID |
|---|---|---|---|
| `T765` | `.axmi` binary serializer & loader in `compiler/artifact/axmi`, exported signatures/types/traits/capabilities/`const`/generic MIR templates, `CompilerDB` integration, `--emit=axmi` & `inspect --axmi` | `tests/run/artifact_axmi` | `INV-ART-001` |
| `T766` | Embedded `.axmeta`/`.axlto` non-alloc COFF sections & container reader/writer in `compiler/artifact/container`, schema/target/checksum validation, final `.exe`/`.dll` stripping | `tests/run/artifact_container` | `INV-ART-002` |
| `T767` | End-to-end E18.4 conformance: source-free separate compilation across generics/traits/capabilities/`const`, byte-identical `.axmi`/`.obj` emission, corruption/schema/target diagnostics | `tests/conformance/p18/e18_4_artifacts` | `INV-ART-003` |

---

## Sources

- `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-070..074`: artifact dimensions, custom `.axmeta` sections, symbols, relocations, linker contract)
- `docs/base/specs/0164 - AXIOM LINKER v0.1.md` (object model, section merging, symbol resolution)
- `docs/base/tasks/0582 - BOOTSTRAP-323 — AXIOM SEMANTIC INTERFACE (.axif) & INTERPROCEDURAL SUMMARY ARTIFACT ENGINE.md` (§323.1–§323.20, `REQ-CORE-3109`, `REQ-CORE-3110`)
- `docs/base/tasks/0591 - BOOTSTRAP-332 — AXIOM ARTIFACT FORMAT, DISTRIBUTION & REGISTRY PROTOCOL ENGINE.md` (§1–§12, `REQ-CORE-3123`, `REQ-CORE-3124`)
- `docs/base/tasks/0739 - BOOTSTRAP-493 — PACKAGE ABI, BINARY INTERFACE DISTRIBUTION, PRECOMPILED GENERICS, MODULE INTERFACE FILES & FAST BINARY CONSUMPTION.md` (§493.1–§493.30)
- `docs/base/tasks/0787 - BOOTSTRAP-565 — COMPILER ARTIFACT FORMAT 2.0 — AXIOM OBJECTLTOSEMANTICDEBUG PACKAGE, SECTION SCHEMA, VERSIONING, COMPATIBILITY & ZERO-COPY COMPILATION.md` (§565.1–§565.200, `REQ-LNK-434..633`)
- `docs/base/tasks/0803 - BOOTSTRAP-581 — OBJECT FILE WRITER 3.0.md` (§581.1–§581.200, `REQ-LNK-3634..3784`)
