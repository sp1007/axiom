# SPEC-114 — Canonical Axiom ABI Stability Tiers, Versioned Symbol Contracts, AbiFingerprint/ApiFingerprint & Binary Compatibility Specification

- **Status**: draft (T866, 2026-11-08)
- **Owner**: axiom-architect
- **Phase**: P20 (E20.5 — ABI Stability, Versioning & Binary Compatibility)
- **Rules**: `AXS-ABI-001` .. `AXS-ABI-053`
- **Covers**: `REQ-ECO-8734`, `REQ-PKG-022`, `REQ-PKG-024`
- **Consolidates**: `0104 (§1–§22)`; `tasks/0452 (§193.1–§193.21, BOOTSTRAP-193)`; `tasks/0583 (§324.1–§324.22, BOOTSTRAP-324)`; `tasks/0739 (§493.1–§493.25, BOOTSTRAP-493)`; `tasks/0661 (§Goal, §5, §14, §18–§24)`; `tasks/1065 (§1, §50–§65, §112–§140, §199 PKG-INV-01..40)`; `spec/SPEC-24-artifact-format-module-interfaces.md` (`AXS-ART-002`, `AXS-ART-010..023`); `spec/SPEC-50-unsafe-ub-ffi.md` (`AXS-UNS-030..036`).
- **Consumers**: `compiler/abi/stability`, `compiler/abi/fingerprint`, `compiler/abi/compat_diff`, `compiler/driver/abi_cmd`, `tests/run/abi_stability`, `tests/run/abi_compat_diff`, `tests/conformance/p20/e20_5_abi_stability_compat`, `T867`–`T869`.

---

## Tóm tắt

Đặc tả `SPEC-114` chuẩn hóa kiến trúc ba tầng ABI của ngôn ngữ Axiom (`Internal Axiom ABI`, `Package Interface ABI`, `Stable Binary ABI`), bốn chiều tương thích (`Source`, `Semantic`, `ABI`, `Binary`), hệ thống kiểu nhị phân ổn định (`Stable Axiom ABI Type System`), bộ ba hàm băm định danh độc lập (`ApiFingerprint`, `SemanticFingerprint`, `AbiFingerprint`), cơ chế đánh số phiên bản ký hiệu liên kết (`@symbol_version`), và công cụ phân loại tương thích nhị phân / SemVer tự động `axiomc abi-check` (`REQ-ECO-8734`, `REQ-PKG-022`, `REQ-PKG-024`) cho phân hệ `E20.5` (Phase `P20`):

1. **Ba tầng ABI độc lập và nguyên tắc không khóa ABI ngầm định (`AXS-ABI-001`..`AXS-ABI-004`, `REQ-PKG-024`)**:
   - `Internal Axiom ABI` (`extern "axiom"`): Tầng mặc định cho mã nguồn nội bộ. Trình biên dịch có toàn quyền tái cấu trúc bố cục bộ nhớ (`layout`), sắp xếp lại trường, tối ưu hóa niche, tái sử dụng đệm đuôi (`tail padding`), gán thanh ghi tham số và nội tuyến hóa (`inlining`) tự do qua từng lần phát hành mà không bị trói buộc tính ổn định.
   - `Package Interface ABI` (`.axmeta` / `.axmi`): Giao diện ngữ nghĩa và mẫu MIR đã kiểm định (`Verified MIR`) cho biên dịch riêng rẽ không cần mã nguồn gốc (`tasks/0739`). Xác thực dấu vân tay phiên bản trình biên dịch, mục tiêu (`TargetFingerprint`) và ABI (`AbiFingerprint`) trước khi tiêu thụ.
   - `Stable Binary ABI` (`@abi(stable, version = "...")`, `@repr(C)`, `@repr(transparent)`): Hợp đồng nhị phân máy ổn định tường minh dành riêng cho thư viện liên kết động (`.dll`, `.so`, `.dylib`), hệ thống plugin và nạp lại nóng (`hot-reload`; `REQ-ECO-8734`). Từ chối ngầm định việc khóa ABI trên toàn bộ ngôn ngữ; từ khóa `pub` chỉ biểu thị tầm nhìn mã nguồn, không đồng nghĩa xuất ký hiệu nhị phân hay ổn định ABI.
2. **Hệ thống kiểu nhị phân ổn định & tường lửa biên giới (`AXS-ABI-010`..`AXS-ABI-020`, `REQ-ECO-8734`, `REQ-PKG-024`)**:
   - Quy định danh mục kiểu hợp lệ trên ranh giới `@abi(stable)`: số vô hướng độ rộng cố định (`i8..i64`, `u8..u64`, `f32`, `f64`, `bool`), cấu trúc ổn định mở rộng mang đầu mục phiên bản/kích thước (`size`/`version` header), enum có gắn thẻ với biểu diễn tường minh (`@repr(u8..u64)`), kiểu tay cầm mờ giấu kín nội bộ (`@opaque`), lát cắt mượn ổn định (`StableView<T>`, `StableStr`), và bộ đệm sở hữu gắn cặp tường minh với bảng hàm cấp phát (`AllocatorVTable`).
   - Cấm triệt để việc xuất generic dạng mẫu thô chưa monomorphize (`AX_FFI_GENERIC_EXPORT`).
   - Bắt buộc kiểm tra tại thời điểm biên dịch và từ chối các kiểu không ổn định (closure mang môi trường bắt giữ, ADT không có `@repr`, generic thô, chuỗi/lát cắt nội bộ) vượt qua ranh giới `@abi(stable)` bằng mã lỗi `AX_ABI_UNSTABLE_TYPE`.
3. **Bộ ba hàm băm độc lập `ApiFingerprint`, `SemanticFingerprint`, `AbiFingerprint` (`AXS-ABI-020`..`AXS-ABI-026`, `REQ-PKG-022`)**:
   - `ApiFingerprint` (BLAKE3-128): Băm chữ ký cú pháp công khai nguồn (`pub fn`, tham số, kiểu trả về, trường công khai). Bất biến trước sửa đổi thân hàm riêng tư, chú thích hoặc định dạng.
   - `SemanticFingerprint` (BLAKE3-128): Băm hợp đồng ngữ nghĩa công khai, bao gồm thân MIR của hàm `@inline`, hàm `comptime fn`, giá trị `const` đã tính, và tóm tắt hiệu ứng/năng quyền.
   - `AbiFingerprint` (BLAKE3-128): Băm bố cục vật lý nhị phân mục tiêu (kích thước, căn chỉnh, độ lệch offset từng trường, quy ước gọi hàm, phiên bản ký hiệu, thanh ghi ABI). Bất biến khi sửa thân hàm không nội tuyến, nhưng đổi giá trị ngay khi đổi bố cục bộ nhớ.
4. **Đánh số phiên bản ký hiệu & bộ phân loại SemVer tự động `axiomc abi-check` (`AXS-ABI-030`..`AXS-ABI-046`, `REQ-ECO-8734`, `REQ-PKG-022`)**:
   - Thuộc tính `@symbol_version("1.0")` cho phép nhiều phiên bản ABI của cùng một hàm cùng tồn tại trong một tệp `.dll`/`.so`, bảo đảm tương thích ngược cho các chương trình nhị phân cũ.
   - Công cụ `axiomc abi-check` so sánh hai tệp siêu dữ liệu `.axmeta` và phân loại thay đổi thành 3 cấp độ: `compatible` (bản vá triển khai), `minor-additive` (thêm xuất mới, nối thêm trường vào struct mở rộng có nâng phiên bản), và `major-breaking` (xóa ký hiệu, thay đổi kiểu/offset/căn chỉnh/năng quyền). Tự động từ chối bản dựng nếu phát hiện vi phạm SemVer (`AX_ABI_BREAKING_CHANGE`, `AX_ABI_SEMVER_MISMATCH`).

---

## 1. The Three ABI Tiers & Four Compatibility Dimensions

### `AXS-ABI-001` — The Three ABI Tiers Architecture

The Axiom compilation model strictly partitions binary and interface contracts into three explicit, non-overlapping tiers (`0104 §1–§7`, `tasks/0452 §193.2–§193.8`, `tasks/0583 §324.6`):

```
+-----------------------------------------------------------------------------------+
| Tier 1: Internal Axiom ABI (Default, Open-World Optimization)                      |
| - Pure Axiom modules, private interfaces, monolithic workspace builds             |
| - Layout reordering, niche packing, tail-padding reuse, aggressive register alloc |
| - Zero stability guarantee across compiler builds, commit hashes, or opt levels   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| Tier 2: Package Interface ABI (.axmeta / .axmi Semantic & Template Interface)    |
| - Separate compilation boundary, precompiled generic distribution (tasks/0739)    |
| - Proven pub signatures, canonical TypeIds, verified MIR templates for @inline   |
| - Validated via CompilerVersion + TargetFingerprint + AbiFingerprint verification |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| Tier 3: Stable Binary ABI (@abi(stable), @repr(C), @repr(transparent))            |
| - Dynamic shared libraries (.dll, .so, .dylib), plugins, hot-reload (REQ-ECO-8734)|
| - Fixed C/platform register calling conventions, deterministic struct/enum layout |
| - Versioned symbols (@symbol_version), extensible struct headers, opaque handles  |
+-----------------------------------------------------------------------------------+
```

1. **Tier 1 — Internal Axiom ABI (`extern "axiom"`, `Default`)**:
   - Applies by default to all functions, types, and modules unless explicitly annotated with `@abi(stable)`, `@repr(C)`, or `@repr(transparent)`.
   - The compiler retains total freedom to optimize data representation and machine code calling conventions:
     - Arbitrary struct field reordering to minimize padding and maximize cache-line packing.
     - Discriminant niche optimization (e.g., zero-cost `Option<NonNull<T>>` or `Option<bool>` packing).
     - Tail-padding reuse in composite hierarchies.
     - Custom calling conventions utilizing all available general-purpose and vector registers.
     - Whole-program LTO (`SPEC-75`), cross-module inlining, devirtualization, and dead-argument elimination.
   - **Zero cross-compiler stability**: Internal ABI representation is ephemeral. Binaries compiled with different compiler versions, differing optimization profiles (`debug` vs `release`), or different target CPU feature masks MUST NOT be linked together without separate compilation validation.

2. **Tier 2 — Package Interface ABI (`.axmeta` / `.axmi`)**:
   - The boundary across separate package and compilation units distributed as source or precompiled semantic packages (`SPEC-24 AXS-ART-010..023`, `tasks/0739 §493.1–§493.25`).
   - Serialized inside `.axmi` files and embedded `.axmeta` object sections.
   - Transmits proven high-level compiler facts:
     - Canonical nominal `TypeId` table and trait implementation coherence tables.
     - Full public function and method signatures with parameter passing modes (`Move`, `Copy`, `View`, `MutView`).
     - Interprocedural capability, ownership, effect, and panic summaries (`FnContractSummary`).
     - Evaluated `const` payloads and pre-verified MIR templates (`Verified MIR`) for generic definitions, `@inline` functions, and `comptime fn` bodies.
   - **Verification gate**: When consuming a package interface, the compiler validates `ArtifactHeader` magic, `schema_version`, `TargetFingerprint`, and `AbiFingerprint`. Mismatched compiler versions or targets trigger source recompilation or emit `AX_LINK_ARTIFACT_TARGET_MISMATCH`.

3. **Tier 3 — Stable Binary ABI (`@abi(stable)`, `@repr(C)`, `@repr(transparent)`)**:
   - Explicit opt-in contract designed for dynamic linking, native operating system plugins, hot-reload runtime component swapping, and cross-language interoperability (`REQ-ECO-8734`, `0104 §4–§7`, `tasks/0583 §324.6`).
   - Governed by frozen, deterministic machine-level rules:
     - Calling conventions adhere to standard platform C ABIs: Microsoft x64 (`Win64`) on Windows, System V AMD64 (`SysV64`) on Linux, AAPCS64 on ARM64 (`SPEC-50 AXS-UNS-036`).
     - Struct layout follows strict declaration order and platform natural alignment without reordering or compiler-internal niche exploitation.
     - Tagged unions enforce explicit integer discriminants (`@repr(u8)`..`@repr(u64)`).
     - Composite types support forward-compatible evolution via extensible `size`/`version` headers or complete encapsulation behind `@opaque` pointer handles.
     - Dynamic symbols carry explicit version decorations (`@symbol_version`).

[0104 §1–§7; tasks/0452 §193.2–§193.8; tasks/0583 §324.6; tasks/0739 §493.1–§493.5; SPEC-24 AXS-ART-010..023; SPEC-50 AXS-UNS-036; REQ-ECO-8734, REQ-PKG-024]

---

### `AXS-ABI-002` — The Four Compatibility Dimensions

System evolution across package releases, compiler upgrades, and dynamic updates is evaluated across four orthogonal compatibility dimensions (`tasks/0452 §193.4–§193.5`, `tasks/0583 §324.2`):

| Dimension | Scope | Definition | Failure Manifestation |
|---|---|---|---|
| **Source Compatibility** (`SourceComp`) | Source Text | Existing valid Axiom source code continues to compile against a new version without textual modifications or syntax errors. | Compile-time parse or type-checking error (`AX_TYPE_*`, `AX_NAME_*`). |
| **Semantic Compatibility** (`SemanticComp`) | Behavioral Contract | Observable program behavior conforms to established pre/postconditions, invariants, and effect bounds; bugs may be fixed, but behavioral contracts are not violated. | Logic regressions, unexpected panics, contract violations, deadlocks. |
| **ABI Compatibility** (`AbiComp`) | Compilation & Linkage | Downstream code compiled against version $V_1$ can link against object files or static libraries of version $V_2$ without recompiling $V_1$. | Link-time undefined symbols, relocation errors, or immediate runtime stack misalignment. |
| **Binary Compatibility** (`BinaryComp`) | Dynamic Execution | Pre-existing compiled shared libraries (`.dll`, `.so`) can be dropped in at runtime without recompiling or relinking client executables. | Hardware memory faults (GPF/AV), memory corruption, silent register clobbering, calling convention crash. |

#### Fundamental Non-Equivalence Laws (`tasks/0452 §193.4`, `tasks/0583 §324.2`)

1. **`SourceComp ≠ AbiComp`**:
   - Adding a private field to an internal struct preserves 100% source compatibility, but alters the struct's byte size and field offsets, breaking ABI compatibility for callers passing the struct by value.
   - Conversely, reordering function declarations in a file or altering private helper implementations preserves ABI compatibility while having no impact on source compatibility.
2. **`SemanticComp ≠ AbiComp`**:
   - Replacing a naive $O(N^2)$ sorting implementation with $O(N \log N)$ quicksort preserves ABI compatibility and source compatibility, but modifies runtime timing properties.
   - Tightening an effect contract from `ReadsMem` to `Pure` is semantically backward-compatible, but changing a calling convention breaks ABI compatibility even if semantics are identical.
3. **`AbiComp ≠ BinaryComp`**:
   - Rebuilding a client against an updated static `.lib` archive with an added struct field may succeed via recompilation (`AbiComp`), whereas replacing a dynamic `.dll` without updating the client will cause out-of-bounds reads if the client assumed the older byte size (`BinaryComp`).
   - True Binary Compatibility requires explicit runtime layout negotiation or stable handle indirection.

[tasks/0452 §193.4–§193.5; tasks/0583 §324.2; 0104 §2–§3; REQ-PKG-022]

---

### `AXS-ABI-003` — Explicit Opt-In Principle & Prohibition of Implicit ABI Freezing

1. **No Universal Implicit ABI Freeze (`0104 §1–§2`, `tasks/0452 §193.3`, `REQ-PKG-024`)**:
   - The Axiom language and toolchain explicitly reject the universal, unannotated freezing of compiler ABIs.
   - The compiler SHALL NOT compromise code generation efficiency, vectorization, register allocation, or struct layout optimization in internal modules in order to maintain unrequested binary stability.
2. **`pub` Is Visibility, Not Binary Export (`0104 §4`, `tasks/0452 §193.3`)**:
   - The `pub` keyword designates source-level and package-level visibility within the Axiom type system.
   - Declaring an item `pub` DOES NOT assign it a Stable Binary ABI, DOES NOT export it as a dynamic shared library symbol, and DOES NOT freeze its physical memory layout.
3. **Mandatory Explicit Annotation (`REQ-ECO-8734`, `REQ-PKG-024`)**:
   - An item participates in the Stable Binary ABI if and only if it is explicitly annotated with:
     - `@abi(stable)` or `@abi(stable, version = "<version>")`, OR
     - `@repr(C)` / `@repr(transparent)` combined with an explicit export annotation (`@export`, `@no_mangle`, or dynamic library root export).

[0104 §1–§4; tasks/0452 §193.3; tasks/0583 §324.6–§324.7; REQ-ECO-8734, REQ-PKG-024]

---

### `AXS-ABI-004` — The Stable ABI Firewall & Boundary Verification

1. **Boundary Firewall Definition**:
   - Every function, struct, enum, or type alias marked `@abi(stable)` forms a strict **ABI Firewall**.
   - The firewall establishes an immutable contract between independent compilation domains (such as an application host and a dynamic plugin).
2. **Compile-Time Boundary Type Checking (`T867`)**:
   - The semantic analyzer (`compiler/abi/stability`) strictly validates every type appearing in an `@abi(stable)` function signature (all parameter types and the return type) and every public field of an `@abi(stable)` composite type.
   - Every type across the firewall MUST satisfy the **Stable Axiom ABI Type System** (`AXS-ABI-010`..`AXS-ABI-016`).
   - If any parameter, return type, or reachable field violates the stable type contract, compilation is immediately aborted with `AX_ABI_UNSTABLE_TYPE` (`AXS-ABI-017`).

[0104 §6–§7; tasks/0452 §193.6–§193.8; tasks/0583 §324.8; REQ-ECO-8734]

---

## 2. The Stable Axiom ABI Type System

### `AXS-ABI-010` — Fixed-Width Scalars & Platform Pointer Widths

Only the following primitive scalar types are permitted directly across an `@abi(stable)` boundary (`0104 §8`, `tasks/0452 §193.8`, `tasks/0583 §324.5`):

| Type | Bit Width | Alignment (bytes) | Representation Contract | Passing & Return Classification |
|---|---|---|---|---|
| `i8`, `u8` | 8 | 1 | Two's-complement signed / unsigned integer | Low 8 bits of slot GPR (`AL`/`CL`/etc.) |
| `i16`, `u16` | 16 | 2 | Two's-complement signed / unsigned integer | Low 16 bits of slot GPR (`AX`/`CX`/etc.) |
| `i32`, `u32` | 32 | 4 | Two's-complement signed / unsigned integer | Low 32 bits of slot GPR (`EAX`/`ECX`/etc.) |
| `i64`, `u64` | 64 | 8 | Two's-complement signed / unsigned integer | 64-bit slot GPR (`RAX`/`RCX`/etc.) |
| `isize`, `usize` | Target pointer width | Target pointer align | Pointer-sized signed / unsigned integer (64-bit on x64/ARM64) | 64-bit slot GPR (`RAX`/`RCX`/etc.) |
| `f32` | 32 | 4 | IEEE-754 single-precision float | Low 32 bits of float register (`XMM0`) |
| `f64` | 64 | 8 | IEEE-754 double-precision float | Low 64 bits of float register (`XMM0`) |
| `bool` | 8 | 1 | Exact boolean: `0x00` = false, `0x01` = true; values `0x02..0xFF` are illegal and constitute undefined representation | Low 8 bits of slot GPR |
| `*const T`, `*mut T` | Target pointer width | Target pointer align | Raw machine pointer with strict provenance (`SPEC-50`); null (`0`) allowed | 64-bit slot GPR (`RAX`/`RCX`/etc.) |

1. **128-Bit Integer Handling (`i128`, `u128`)**:
   - `i128` and `u128` are fixed-width 16-byte integers (`SPEC-40`).
   - Across `@abi(stable)` boundaries, they are lowered strictly according to the platform C ABI: passed indirectly via caller-allocated 16-byte-aligned stack reference on `Win64`, or in register pairs (`RDX:RAX`) on `SysV64` (`SPEC-50 AXS-UNS-036`).
2. **Strict Boolean Invariant**:
   - Transmitting an integer value other than `0` or `1` into a `bool` slot over an `@abi(stable)` boundary is undefined behavior (`UB-05`). The callee is entitled to assume boolean values are normalized.

[0104 §8; tasks/0452 §193.8; tasks/0583 §324.5; SPEC-40; SPEC-50 AXS-UNS-036]

---

### `AXS-ABI-011` — `@abi(stable)` Structs & Extensible Struct Evolution (`size`/`version` Header)

1. **Deterministic C-Compatible Field Layout**:
   - A struct marked `@abi(stable)` (or `@repr(C)`) lays out fields in exact declaration order.
   - Field offsets and struct alignment follow platform C rules:
     $$\text{offset}_{i} = \text{align\_to}(\text{offset}_{i-1} + \text{sizeof}(F_{i-1}), \text{alignof}(F_i))$$
     $$\text{sizeof}(S) = \text{align\_to}(\text{offset}_N + \text{sizeof}(F_N), \text{alignof}(S))$$
   - Field reordering, automatic packing, and niche injection are strictly forbidden on `@abi(stable)` structs.

2. **The Extensible Struct Pattern (`tasks/0452 §193.15`, `tasks/0583 §324.9–§324.10`)**:
   - To support forward and backward binary compatibility across library upgrades without recompilation, an extensible struct MUST declare a canonical 8-byte `AbiHeader` as its initial fields:
     ```axiom
     @repr(C)
     struct AbiHeader {
         abi_version: u32,
         struct_size: u32
     }
     ```
   - Alternatively, a struct MAY inline these fields directly as its first two fields: `abi_version: u32`, `struct_size: u32`.
   - Omission of the version/size header on an extensible struct that evolves across package releases emits `AX_ABI_EXTENSIBLE_MISSING_HEADER`.

3. **Field Evolution & Trailing Append Rules (`tasks/0583 §324.10`, `REQ-PKG-022`)**:
   - **Append Only**: In subsequent minor releases ($V_{1.1}, V_{1.2}$), new fields MAY ONLY be added at the end of the struct. Modifying existing field offsets, inserting fields between existing fields, or prepending fields is a **breaking change** requiring a major version bump.
   - **Caller Responsibility**: Callers initializing the struct set `struct_size = size_of<S>()` and `abi_version = CURRENT_VERSION`.
   - **Callee Compatibility Check**: When a library receives an extensible struct from a caller:
     ```axiom
     fn read_extended_field(s: view<ExtensibleStruct>) -> u32 {
         // Field 'new_field' is located at byte offset 24 with size 4:
         if s.struct_size >= 28u32 && s.abi_version >= 2u32 {
             return s.new_field
         }
         return DEFAULT_VALUE
     }
     ```
   - If `s.struct_size < offset_of(field) + sizeof(field)`, the callee MUST NOT read or write the field; it falls back to documented default values.

[0104 §8–§9; tasks/0452 §193.15; tasks/0583 §324.9–§324.10; REQ-PKG-022]

---

### `AXS-ABI-012` — `@abi(stable)` Tagged Enums & Discriminant Representation

1. **Mandatory Explicit Representation (`0104 §8`, `tasks/0583 §324.19`)**:
   - An enum exported across an `@abi(stable)` boundary MUST carry an explicit representation attribute specifying its discriminant primitive type:
     - `@repr(u8)`, `@repr(u16)`, `@repr(u32)`, `@repr(u64)`, or their signed equivalents (`@repr(i8)`..`@repr(i64)`).
   - An enum lacking an explicit `@repr(...)` attribute is an internal ADT with compiler-chosen niche representation; exporting it across a stable boundary is rejected with `AX_ABI_UNSTABLE_TYPE`.

2. **Fieldless C-Compatible Enums**:
   - Fieldless enums (variants without payloads) lower directly to their underlying integer discriminant type.
   - Discriminant values are assigned contiguously starting from `0` unless explicitly initialized (`A = 10u32`).
   - Discriminant integer values are **permanent**: altering the numerical value of an existing variant or deleting a variant is a major breaking change (`AXS-ABI-040`).

3. **Tagged Unions with Payloads (`tasks/0583 §324.19–§324.20`)**:
   - Tagged enums with variant payloads lower to a canonical C-compatible layout:
     ```axiom
     // A tagged enum with explicit representation:
     @repr(u32)
     @abi(stable)
     enum StableResult {
         Ok(u64),
         Err(u32)
     }
     ```
   - Lowers physically to:
     ```axiom
     @repr(C)
     struct StableResultPhysical {
         tag: u32,
         payload: [8]u8  // Aligned to max(alignof(variant_payloads))
     }
     ```
   - Total size equals `align_to(sizeof(tag) + max(sizeof(payload_i)), max(alignof(tag), alignof(payload_i)))`.
   - The compiler guarantees that payload offsets do not shift across minor compiler versions.

4. **Extensible / Non-Exhaustive Enums (`@non_exhaustive`)**:
   - An enum intended to gain new variants in minor releases MUST be marked `@non_exhaustive`.
   - Callers compiling against a `@non_exhaustive` enum are required to supply a wildcard/fallback arm in all `match` statements.
   - Adding a variant to an enum NOT marked `@non_exhaustive` is a major breaking change because downstream exhaustive pattern matches would fail or experience unhandled states.

[0104 §8; tasks/0583 §324.19–§324.20; REQ-ECO-8734, REQ-PKG-022]

---

### `AXS-ABI-013` — `@opaque` Handle Types & Complete Encapsulation

1. **Opaque Type Model (`0104 §11–§12`, `tasks/0452 §193.16–§193.17`, `tasks/0739 §493.20`)**:
   - The strongest form of binary stability and data encapsulation is the `@opaque` handle pattern.
   - An opaque type hides its internal fields, layout, and size completely from downstream consumers:
     ```axiom
     // In public interface / header:
     @opaque
     struct EngineContext
     ```
   - The implementing library provides constructors, mutating functions, and destructors operating on pointers or typed handles:
     ```axiom
     pub fn engine_create() -> *mut EngineContext
     pub fn engine_step(ctx: *mut EngineContext, dt: f32) -> u32
     pub fn engine_destroy(ctx: *mut EngineContext)
     ```

2. **Isolation Guarantee (`REQ-ECO-8734`)**:
   - Because client code only passes pointers (`*mut EngineContext`) or typed token values, the internal struct definition inside the library can:
     - Add, remove, or reorder private fields.
     - Change field types and internal data structures.
     - Change alignment or overall byte size.
   - None of these internal modifications alter the `AbiFingerprint` of the public interface or require client recompilation.

3. **Compile-Time Restrictions on `@opaque` Types (`AX_ABI_OPAQUE_BY_VALUE`)**:
   - Outside the defining module, an `@opaque` type:
     - CANNOT be instantiated directly (`EngineContext { ... }` is an error).
     - CANNOT be queried for `size_of<EngineContext>()` or `align_of<EngineContext>()`.
     - CANNOT be stored in local variables by value (`let ctx: EngineContext` is an error).
     - CANNOT be passed or returned by value in function signatures.
   - Any attempt to use an `@opaque` type by value outside its defining module is rejected with `AX_ABI_OPAQUE_BY_VALUE` (`AXS-ABI-050`).

[0104 §11–§12; tasks/0452 §193.16–§193.17; tasks/0739 §493.20; REQ-ECO-8734]

---

### `AXS-ABI-014` — Stable Borrowed Views (`StableView<T>`, `StableStr`)

Standard Axiom fat pointers (`view<T>`, `mut_view<T>`, and `Str`) have compiler-internal layouts that include capability region IDs, provenance descriptors, and metadata that may vary across optimization profiles or compiler versions. To transmit borrowed memory across the `@abi(stable)` boundary, the standard library defines canonical stable view representations (`0104 §13–§14`, `tasks/0583 §324.18`):

1. **Canonical Stable Slice Layouts (`StableView<T>`, `StableMutView<T>`)**:
   ```axiom
   @repr(C)
   struct StableView<T> {
       ptr: *const T,
       len: usize
   }

   @repr(C)
   struct StableMutView<T> {
       ptr: *mut T,
       len: usize
   }
   ```
   - Exact 16-byte layout on 64-bit platforms: 8-byte pointer at offset 0, 8-byte length at offset 8.
   - Invariant: When `len > 0`, `ptr` MUST be non-null, properly aligned to `align_of<T>()`, and point to `len` initialized, live elements of type `T`.
   - `StableMutView<T>` guarantees exclusive access to the underlying memory range for the duration of the call.

2. **Canonical Stable String (`StableStr`)**:
   ```axiom
   @repr(C)
   struct StableStr {
       ptr: *const u8,
       len: usize
   }
   ```
   - Exact 16-byte layout on 64-bit platforms: pointer to UTF-8 bytes at offset 0, byte length at offset 8.
   - **UTF-8 Invariant**: `ptr[0..len]` MUST be valid UTF-8. A null terminator (`\0`) is NOT required (Axiom strings are length-delimited), but if present at `ptr[len]`, it does not violate validity.
   - Passing an unvalidated or non-UTF-8 byte sequence as `StableStr` across an `@abi(stable)` boundary is undefined behavior (`UB-05`).

3. **Zero-Cost Conversions**:
   - The compiler and standard library provide safe zero-cost bidirectional coercions between standard `view<[T]>` / `Str` and `StableView<T>` / `StableStr` within the same compilation unit:
     ```axiom
     let text: Str = "hello"
     let stable: StableStr = StableStr.from_str(text)
     let back: Str = stable.as_str()
     ```

[0104 §13–§14; tasks/0583 §324.18; SPEC-50 AXS-UNS-031]

---

### `AXS-ABI-015` — Explicit Allocator-Paired Owned Buffers & Cross-Heap Protection

1. **The Cross-Heap Deallocation Hazard (`0104 §12`, `tasks/0583 §324.15–§324.17`)**:
   - On modern operating systems (specifically Microsoft Windows dynamic link libraries), different DLLs or host modules may be linked against distinct C Runtime (CRT) instances, memory allocators, or private heap handles (`HeapCreate`).
   - Allocating memory in module $A$ (via `malloc` or `HeapAlloc`) and deallocating it in module $B$ (via `free` or a different heap handle) leads to heap corruption, access violations, or silent process termination.
   - Raw owned containers (`String`, `Vec<T>`, `Box<T>`) carry implicit allocators and MUST NOT be deallocated across dynamic shared library boundaries without an explicit allocator contract.

2. **Contract 1 — Module-Owned Deallocation Function**:
   - A library that returns owned heap allocations MUST export an explicit matching deallocation function:
     ```axiom
     pub fn create_buffer(size: usize) -> *mut u8
     pub fn free_buffer(ptr: *mut u8, size: usize)
     ```
   - The caller is forbidden from invoking the host system allocator directly on pointers returned by `create_buffer`.

3. **Contract 2 — Allocator-Paired Buffer (`StableBuffer<T>`, `tasks/0583 §324.16`)**:
   - Alternatively, self-describing owned containers carry a pointer to a canonical `AllocatorVTable`:
     ```axiom
     @repr(C)
     struct AllocatorVTable {
         alloc: fn(size: usize, align: usize) -> *mut u8,
         dealloc: fn(ptr: *mut u8, size: usize, align: usize),
         realloc: fn(ptr: *mut u8, old_size: usize, new_size: usize, align: usize) -> *mut u8
     }

     @repr(C)
     struct StableBuffer<T> {
         ptr: *mut T,
         len: usize,
         cap: usize,
         allocator: *const AllocatorVTable
     }
     ```
   - When dropped or reallocated, `StableBuffer<T>` dispatches through `allocator.dealloc(self.ptr as *mut u8, self.cap * size_of<T>(), align_of<T>())`.
   - This ensures memory is always returned to the exact allocator heap that created it, regardless of which module performs the drop.

[0104 §12; tasks/0583 §324.15–§324.17; SPEC-50; SPEC-52]

---

### `AXS-ABI-016` — Erased Generic Exports & Virtual Function Tables

1. **Generics Cannot Cross Dynamic Binary Boundaries Directly (`0104 §19–§20`, `tasks/0452 §193.9–§193.10`, `tasks/0583 §324.21–§324.22`)**:
   - Generic functions (`fn process<T>(item: T)`) and generic types rely on compile-time monomorphization: generating specialized machine code for each concrete substitution of type parameters.
   - In dynamic shared libraries (`.dll`, `.so`), code generation occurs prior to distribution. The dynamic linker has no access to compiler front-end semantic trees or monomorphization engines.
   - Exporting an unmonomorphized generic function as a dynamic symbol (`@abi(stable) fn f<T>(x: T)`) is **impossible at the binary level** and is rejected at compile time with `AX_FFI_GENERIC_EXPORT`.

2. **Strategy 1 — Explicit Monomorphization (`tasks/0583 §324.22`)**:
   - A library exports specialized, non-generic wrappers for common concrete types:
     ```axiom
     fn process_generic<T>(item: T) -> u32 { ... }

     @abi(stable, version = "1.0")
     pub fn process_u32(item: u32) -> u32 {
         return process_generic<u32>(item)
     }

     @abi(stable, version = "1.0")
     pub fn process_f64(item: f64) -> u32 {
         return process_generic<f64>(item)
     }
     ```

3. **Strategy 2 — Type Erasure via Stable VTable Dispatch (`0104 §20–§22`, `tasks/0452 §193.12–§193.13`)**:
   - For open-ended generic behavior, the library defines an explicit `@abi(stable)` virtual method table (vtable) and an opaque state pointer:
     ```axiom
     @repr(C)
     struct PluginVTable {
         context: *mut u8,
         on_init: fn(ctx: *mut u8) -> i32,
         on_event: fn(ctx: *mut u8, event_id: u32, data: *const u8) -> i32,
         on_destroy: fn(ctx: *mut u8)
     }

     @abi(stable, version = "1.0")
     pub fn register_plugin(vtable: *const PluginVTable) -> i32
     ```
   - Standard Axiom `dyn Trait` fat pointers have internal vtable layouts. Exposing dynamic behavior across an `@abi(stable)` boundary requires either a stable struct vtable as shown above or a trait explicitly annotated `@abi(stable)`.

[0104 §19–§22; tasks/0452 §193.9–§193.13; tasks/0583 §324.21–§324.22; REQ-ECO-8734]

---

### `AXS-ABI-017` — Compile-Time Rejection of Unstable Types across `@abi(stable)` Boundaries (`AX_ABI_UNSTABLE_TYPE`)

The compiler's boundary checker (`compiler/abi/stability`, `T867`) inspects all types appearing in an `@abi(stable)` export. The presence of any of the following types immediately halts compilation with error `AX_ABI_UNSTABLE_TYPE` (`REQ-ECO-8734`, `REQ-PKG-024`):

1. **Capturing Closures**:
   - Closures capturing local variables (`|x| x + local_var`) carry a compiler-synthesized, private environment struct whose layout and drop semantics are unversioned and variable.
   - Only non-capturing closures coercible to plain function pointers (`fn(...) -> R` or `extern "C" fn(...) -> R`) are permitted (`SPEC-50 AXS-UNS-034`).
2. **Unannotated / Unrepr'd ADTs**:
   - Structs, enums, or unions lacking `@repr(C)`, `@repr(transparent)`, or `@abi(stable)` utilize internal Axiom layout rules (subject to arbitrary field reordering and niche packing) and cannot cross the boundary.
3. **Uninstantiated Generic Type Parameters**:
   - Any bare type parameter `T` or unresolved compound generic type (`Vec<T>`, `Result<T, E>`) where `T` is not concretely known at compile time.
4. **Internal Fat Pointers**:
   - Bare Axiom `view<T>`, `mut_view<T>`, or `Str` fat pointers (must be replaced by `StableView<T>`, `StableMutView<T>`, or `StableStr`).
5. **Raw Slices by Value**:
   - Slices `[N]T` passed by value whose size $> 8$ bytes and which do not carry a stable struct wrapper.
6. **Internal Trait Objects (`dyn Trait`)**:
   - Unannotated `dyn Trait` fat pointers whose vtable layout is internal to `compiler/mir/` and unversioned (`SPEC-63`).
7. **Direct `String` / `Vec<T>` Ownership Transfers**:
   - Standard owned collection types whose deallocator is coupled to the caller's CRT or memory manager (must use `StableBuffer<T>` or explicit deallocation handles per `AXS-ABI-015`).

[0104 §6–§20; tasks/0452 §193.6–§193.18; tasks/0583 §324.5–§324.8; REQ-ECO-8734, REQ-PKG-024]

---

## 3. Fingerprinting Architecture: `ApiFingerprint`, `SemanticFingerprint`, and `AbiFingerprint`

### `AXS-ABI-020` — The Three Independent Fingerprint Domains

To cleanly separate syntactic evolution, inlining semantics, and physical binary layouts, Axiom computes three distinct 128-bit cryptographic digests for every module, package interface, and exported item (`tasks/0452 §193.20–§193.21`, `tasks/0583 §324.2`, `tasks/0739 §493.21–§493.23`, `REQ-PKG-022`):

```
+-----------------------------------------------------------------------------------+
| ApiFingerprint (128-bit BLAKE3)                                                   |
| - Domain: "AXIOM-API-v1\0"                                                        |
| - Inputs: Public item names, parameter names/types/order, return types, vis       |
| - Invariant under: Private bodies, formatting, comments, optimization flags       |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| SemanticFingerprint (128-bit BLAKE3)                                              |
| - Domain: "AXIOM-SEM-v1\0"                                                        |
| - Inputs: ApiFingerprint + @inline MIR bodies + comptime fn + const values + caps |
| - Invariant under: Non-inlined function bodies, formatting, comments              |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| AbiFingerprint (128-bit BLAKE3)                                                   |
| - Domain: "AXIOM-ABI-v1\0"                                                        |
| - Inputs: TargetFingerprint + CallConv + sizeof/alignof/offsets + symbol_versions  |
| - Invariant under: Function body modifications (that do not change layout/inlining)|
+-----------------------------------------------------------------------------------+
```

[tasks/0452 §193.20–§193.21; tasks/0583 §324.2; tasks/0739 §493.21–§493.23; REQ-PKG-022]

---

### `AXS-ABI-021` — Canonical Calculation of `ApiFingerprint`

1. **Domain Prefix & Algorithm**:
   - `ApiFingerprint` is computed using BLAKE3 initialized with the domain separation string `"AXIOM-API-v1\0"`.
2. **Canonical Input Serialization**:
   - For every exported item (`pub fn`, `pub struct`, `pub enum`, `pub trait`, `pub type`, `pub const`, `pub static`):
     - Item identifier string and module path.
     - Type signatures: fully-qualified parameter types and return type.
     - Parameter names and positional ordering.
     - For structs: public field names, public field types, and declaration order.
     - For enums: variant names, explicit discriminant expressions (if specified), and variant payload types.
     - For traits: method signatures, associated type names, and supertrait bounds.
3. **Invariance Properties**:
   - `ApiFingerprint` is **strictly invariant** across:
     - Changes to private function bodies, private types, or internal helper modules.
     - Source code formatting, indentation, and comments.
     - Changes to compiler optimization flags (`-O2`, `-O3`, `-Os`).
     - Changes to inlined function implementations.
4. **Invalidation**:
   - Any renaming of an exported item, addition/removal of a public parameter, modification of parameter or return types, or alteration of public field types immediately changes `ApiFingerprint`.

[tasks/0452 §193.21; tasks/0739 §493.23; REQ-PKG-022]

---

### `AXS-ABI-022` — Canonical Calculation of `SemanticFingerprint`

1. **Domain Prefix & Algorithm**:
   - `SemanticFingerprint` is computed using BLAKE3 initialized with the domain separation string `"AXIOM-SEM-v1\0"`.
2. **Canonical Input Serialization**:
   - Begins with the 16-byte `ApiFingerprint` of the item.
   - For `@inline`, `@inline(always)`, or generic functions: the normalized canonical `Verified MIR` body instructions, basic block CFG topology, local variable types, and branch targets (`SPEC-24 AXS-ART-013`).
   - For `comptime fn` items: the canonical MIR body and evaluate-time preconditions.
   - For `const` items: the evaluated canonical constant payload byte stream (`ConstValue`).
   - For callable items: the interprocedural contract summary (`FnContractSummary`), including capability provenance bitmasks, effect sets (`Pure`, `ReadsMem`, `WritesMem`, etc.), and panic contracts (`NoPanic` vs `MayPanic`).
3. **Invariance Properties**:
   - `SemanticFingerprint` is invariant across changes to private non-inlined functions.
4. **Invalidation**:
   - Changing the implementation of an `@inline` function or modifying a `comptime` constant immediately changes `SemanticFingerprint`, invalidating downstream compilation units that may have inlined that body or folded that constant.

[tasks/0452 §193.20; tasks/0739 §493.22; SPEC-24 AXS-ART-012..013; REQ-PKG-022]

---

### `AXS-ABI-023` — Canonical Calculation of `AbiFingerprint`

1. **Domain Prefix & Algorithm**:
   - `AbiFingerprint` is computed using BLAKE3 initialized with the domain separation string `"AXIOM-ABI-v1\0"`.
2. **Canonical Input Serialization**:
   - **Target Parameters**: `TargetFingerprint` digest (incorporating architecture, operating system, pointer width, endianness, and target CPU features; `SPEC-81`).
   - **Calling Conventions**: Assigned `CallConv` (e.g. `Win64`, `SysV64`, `AAPCS64`, `C`) and register class assignments for all parameter and return slots.
   - **Memory Layouts**: For every exported type reachable across the ABI:
     - `size_of<T>()` and `align_of<T>()` in bytes.
     - For structs: byte offset of every field, field alignments, and padding gaps.
     - For enums: discriminant integer type, numerical values of all discriminants, and payload byte offsets.
     - Extensible struct metadata: presence of `AbiHeader`, current declared version, and struct size.
   - **Symbol Information**: Exported linker symbol names, platform export attributes (`@no_mangle`, `@export`), and declared `@symbol_version` strings.
3. **Invariance Properties**:
   - `AbiFingerprint` is **strictly invariant** across:
     - Modifications to non-inlined function bodies (bug fixes, performance rewrites) that do not alter signatures.
     - Changes to private struct fields encapsulated behind `@opaque` pointer handles (`AXS-ABI-013`).
     - Compiler frontend refactorings that preserve identical physical layout and machine calling conventions.
4. **Invalidation**:
   - Any modification to field offsets, type sizes, alignment, calling conventions, or symbol version strings immediately changes `AbiFingerprint`.

[tasks/0452 §193.20; tasks/0583 §324.2; tasks/0739 §493.21; SPEC-24 AXS-ART-023; REQ-PKG-022, REQ-PKG-024]

---

### `AXS-ABI-024` — Storage in `.axmeta` and Relocatable Objects (`.obj`, `.lib`, `.dll`)

1. **Embedded `.axmeta` Representation (`SPEC-24 AXS-ART-021`, `T868`)**:
   - When compiling a module or package, the compiler records `ApiFingerprint`, `SemanticFingerprint`, and `AbiFingerprint` in the `ArtifactHeader` and the `TypesLayout` section of `.axmi` and embedded `.axmeta` records.
2. **Link-Time and Incremental Early Cutoff (`SPEC-22`, `SPEC-110`)**:
   - When compiling downstream modules:
     - If an upstream module changes but its `ApiFingerprint` and `SemanticFingerprint` are unchanged, downstream modules DO NOT need to be re-typechecked or recompiled.
     - If an upstream library is updated but its `AbiFingerprint` is unchanged, downstream relocatable object files DO NOT need to be re-linked against dynamic shared libraries.
3. **Source-Free Compatibility Validation**:
   - The `axiomc abi-check` utility can inspect precompiled `.axmeta` or `.dll` artifacts directly without access to source code or compiler frontend ASTs, enabling fast supply-chain and registry compatibility verification.

[SPEC-24 AXS-ART-021..023; SPEC-110; tasks/0739 §493.21–§493.25; REQ-PKG-022]

---

## 4. Symbol Versioning & Shared Library Contracts

### `AXS-ABI-030` — `@symbol_version` Attribute & Mangling Rules

1. **Motivation & Coexistence (`tasks/0452 §193.19`, `tasks/0583 §324.13`, `REQ-ECO-8734`)**:
   - In dynamic environments, a library author may wish to evolve a function signature or behavior while maintaining backward compatibility with existing binaries that link against an older signature.
   - The `@symbol_version` attribute associates an exported function with an explicit semantic version tag.
   - This allows multiple versions of the same logical function to coexist in a single `.dll` or `.so` binary:
     ```axiom
     // Legacy v1.0 version (retained for backward compatibility with v1.0 clients):
     @abi(stable)
     @symbol_version("1.0")
     pub fn parse_config(path: *const u8) -> u32 {
         return parse_config_v1(path)
     }

     // Modern v1.1 version (marked default for newly compiled clients):
     @abi(stable)
     @symbol_version("1.1", default = true)
     pub fn parse_config(path: *const u8, flags: u32) -> u32 {
         return parse_config_v2(path, flags)
     }
     ```

2. **Canonical Mangling Format (`T868`)**:
   - Internal object symbol mangling for versioned exports adheres to the deterministic scheme:
     $$\text{mangled\_name} = \text{"axiom\_" } + \text{package\_name} + \text{"\_"} + \text{module\_path} + \text{"\_"} + \text{ident} + \text{"@@"} + \text{version}$$
   - When `default = false`, a single `@` separator is used (`symbol@1.0`), denoting an un-aliased older version.
   - When `default = true`, the double `@@` separator is used (`symbol@@1.1`), designating the primary symbol bound during new linking passes.

3. **Validation & Uniqueness (`AX_ABI_SYMBOL_VERSION_DUPLICATE`)**:
   - Defining two functions with the exact same identifier, module path, and `@symbol_version` string within the same package is illegal and emits `AX_ABI_SYMBOL_VERSION_DUPLICATE` (`AXS-ABI-050`).
   - Exactly one implementation of a versioned symbol group MAY be marked `default = true`. Marking multiple implementations as default emits `AX_ABI_SYMBOL_VERSION_DUPLICATE`.

[tasks/0452 §193.19; tasks/0583 §324.13; REQ-ECO-8734]

---

### `AXS-ABI-031` — Platform Symbol Export Tables (Windows PE/COFF `.edata` vs ELF Symbol Versioning)

Axiom lowers `@symbol_version` contracts onto native operating system platform formats without external toolchain intervention (`SPEC-26`, `SPEC-27`, `SPEC-82`):

1. **Microsoft Windows PE/COFF Lowering (`.edata`, `SPEC-26`)**:
   - The Windows PE format does not natively support ELF-style version scripts within its import/export directory.
   - `compiler/link/` implements versioned symbol lowering using export aliases:
     - The default symbol (`default = true`) is exported under its unadorned name (`parse_config`).
     - Legacy and version-specific symbols are exported as explicit decorated export table entries: `parse_config_v1_0` and `parse_config_v1_1`.
     - In the `.axmeta` section, a redirect table maps `(parse_config, "1.0") -> parse_config_v1_0`.
     - Downstream Axiom PE loaders and client linkers bind directly to the decorated entry when linking against an explicit historical version.

2. **Linux / ELF Lowering (`.gnu.version`, `.gnu.version_d`, `SPEC-82`)**:
   - On ELF targets, `compiler/link/` emits standard GNU symbol versioning sections:
     - `.gnu.version`: Contains version index arrays matching dynamic symbol table entries (`.dynsym`).
     - `.gnu.version_d`: Contains version definition records declaring available version strings (`PKG_1.0`, `PKG_1.1`).
     - Standard dynamic linkers (`ld-linux.so`) automatically bind calling binaries to the exact matching version symbol.

3. **Darwin / Mach-O Lowering (`SPEC-84`)**:
   - On macOS/Darwin, symbol versions are lowered via Mach-O two-level namespace symbol stubs or explicit dynamic symbol aliases (`$parse_config$1.0`).

[SPEC-26; SPEC-27; SPEC-82; SPEC-84; tasks/0452 §193.19; tasks/0583 §324.13]

---

### `AXS-ABI-032` — Dynamic Linker Resolution & Hot-Reload Fallback

1. **Runtime Symbol Binding**:
   - When a host application dynamically loads a plugin or shared library (`host.dlopen` / `LoadLibraryW`), the runtime inspects the library's embedded `.axmeta` header:
     1. Validates that `TargetFingerprint` matches the running host architecture and OS.
     2. Queries the exported symbol version table for each requested entry point.
     3. Binds function pointers to the requested ABI version.
2. **Hot-Reload Component Swapping (`REQ-ECO-8734`)**:
   - In dynamic hot-reload systems (`E20.6`, `T870`–`T873`), state preservation across component reloads requires ABI agreement.
   - If the new library version retains an identical `AbiFingerprint` for its internal state structures (or encapsulates state behind `@opaque` handles), the runtime migrates the state buffer directly without serialization.
   - If `AbiFingerprint` changes but an extensible struct header is present (`AXS-ABI-011`), the hot-reload manager applies an automatic field expansion migration.

[tasks/0452 §193.19; tasks/0583 §324.13; REQ-ECO-8734]

---

## 5. SemVer Compatibility Classifier & `axiomc abi-check` CLI

### `AXS-ABI-040` — Three-Way Compatibility Classification (`compatible`, `minor-additive`, `major-breaking`)

Every change between a baseline `.axmeta` (version $V_1$) and a candidate `.axmeta` (version $V_2$) is deterministically classified into one of three categories (`tasks/0452 §193.14–§193.21`, `tasks/0583 §324.11`, `REQ-PKG-022`):

```
                        +---------------------------+
                        |   Baseline vs Candidate   |
                        |      .axmeta Diff         |
                        +---------------------------+
                                      |
            +-------------------------+-------------------------+
            |                         |                         |
            v                         v                         v
    [compatible]             [minor-additive]           [major-breaking]
  - Identical API & ABI    - New pub exports          - Removed pub symbols
  - Private bug fixes      - Extensible struct append - Modified field offsets
  - Non-inline body edits  - New @symbol_version      - Changed param types
  - Permitted in PATCH     - Permitted in MINOR       - REQUIRES MAJOR BUMP
```

#### Detailed Change Classification Matrix

| Change Type | `ApiFingerprint` | `SemanticFingerprint` | `AbiFingerprint` | Allowed SemVer Increment | Compatibility Class |
|---|---|---|---|---|---|
| **Private bug fix in non-inline function** | Unchanged | Unchanged | Unchanged | Patch (`0.0.x`) | `compatible` |
| **Private field modification behind `@opaque` handle** | Unchanged | Unchanged | Unchanged | Patch (`0.0.x`) | `compatible` |
| **Implementation change in `@inline` function** | Unchanged | **Changed** | Unchanged | Patch (`0.0.x`) / Minor | `compatible` (ABI identical) |
| **Adding a new `pub fn` export** | **Changed** | **Changed** | **Changed** | Minor (`0.x.0`) | `minor-additive` |
| **Adding a new `@opaque` type declaration** | **Changed** | **Changed** | **Changed** | Minor (`0.x.0`) | `minor-additive` |
| **Appending field to extensible `@abi(stable)` struct** | **Changed** | **Changed** | **Changed** | Minor (`0.x.0`) | `minor-additive` |
| **Adding a new `@symbol_version` (retaining older)** | **Changed** | **Changed** | **Changed** | Minor (`0.x.0`) | `minor-additive` |
| **Adding variant to `@non_exhaustive` enum** | **Changed** | **Changed** | **Changed** | Minor (`0.x.0`) | `minor-additive` |
| **Relaxing capability precondition** | **Changed** | **Changed** | Unchanged | Minor (`0.x.0`) | `minor-additive` |
| **Removing an exported `pub fn`** | **Changed** | **Changed** | **Changed** | Major (`x.0.0`) | `major-breaking` |
| **Modifying parameter types, order, or count** | **Changed** | **Changed** | **Changed** | Major (`x.0.0`) | `major-breaking` |
| **Changing function return type** | **Changed** | **Changed** | **Changed** | Major (`x.0.0`) | `major-breaking` |
| **Altering field offset, size, or alignment of struct** | **Changed** | **Changed** | **Changed** | Major (`x.0.0`) | `major-breaking` |
| **Adding field to non-extensible struct** | **Changed** | **Changed** | **Changed** | Major (`x.0.0`) | `major-breaking` |
| **Removing or renumbering enum variant** | **Changed** | **Changed** | **Changed** | Major (`x.0.0`) | `major-breaking` |
| **Adding variant to exhaustive (unannotated) enum** | **Changed** | **Changed** | **Changed** | Major (`x.0.0`) | `major-breaking` |
| **Changing calling convention (`Win64` $\to$ `SysV`)** | Unchanged | Unchanged | **Changed** | Major (`x.0.0`) | `major-breaking` |
| **Removing an existing `@symbol_version`** | **Changed** | **Changed** | **Changed** | Major (`x.0.0`) | `major-breaking` |
| **Tightening capability / effect bounds** | **Changed** | **Changed** | Unchanged | Major (`x.0.0`) | `major-breaking` |

[tasks/0452 §193.14–§193.21; tasks/0583 §324.11; REQ-PKG-022]

---

### `AXS-ABI-041` — The `axiomc abi-check` Command-Line Interface (`REQ-PKG-022`)

1. **CLI Syntax & Execution Modes (`T868`)**:
   The compiler driver provides a dedicated subcommand for inspecting and verifying binary interface compatibility:
   ```bash
   axiomc abi-check --old <base.axmeta> --new <cand.axmeta> [--semver <old_ver>:<new_ver>] [--json]
   ```
   - `--old <base.axmeta>`: Path to baseline package metadata or shared library binary containing `.axmeta`.
   - `--new <cand.axmeta>`: Path to candidate package metadata or shared library binary.
   - `--semver <old_ver>:<new_ver>`: (Optional) Enforces that the proposed version increment matches the detected change classification.
   - `--json`: Emits a structured JSON report detailing all discovered API/ABI differences.

2. **Exit Code & Diagnostics Contract**:
   - **Exit Code `0`**: The candidate is classified as `compatible` or `minor-additive` with a valid minor/major bump, or `major-breaking` when an explicit major SemVer increment was specified.
   - **Exit Code `1` (`AX_ABI_BREAKING_CHANGE`)**: A breaking ABI/API change was detected, but `--semver` indicated a patch or minor release (e.g. `--semver 1.1.0:1.2.0`).
   - **Exit Code `2` (`AX_ABI_SEMVER_MISMATCH`)**: An additive change was detected, but `--semver` indicated a patch release (e.g. `--semver 1.1.0:1.1.1`).
   - **Exit Code `3`**: Bad input files, missing `.axmeta` section, or target mismatch.

3. **Structured JSON Output Schema**:
   ```json
   {
     "status": "breaking",
     "old_version": "1.1.0",
     "new_version": "1.2.0",
     "target_fingerprint": "a4f1...9b2c",
     "classification": "major-breaking",
     "differences": [
       {
         "kind": "struct_field_offset_changed",
         "item": "my_pkg.RenderConfig",
         "field": "width",
         "old_offset": 8,
         "new_offset": 12,
         "severity": "breaking"
       },
       {
         "kind": "function_removed",
         "item": "my_pkg.legacy_init",
         "severity": "breaking"
       }
     ]
   }
   ```

[tasks/0452 §193.14–§193.21; tasks/0583 §324.11; REQ-PKG-022]

---

### `AXS-ABI-042` — CI / Registry Automated ABI Gate

1. **Package Registry Publishing Enforcement (`SPEC-112`)**:
   - The package registry publishing pipeline (`axiomc pkg publish`, `T860`) automatically runs `axiomc abi-check` against the previous published version of the package.
   - If a package author attempts to publish a new version $V_{1.2.0}$ containing a breaking ABI change relative to $V_{1.1.0}$, the publication is rejected by the registry server with diagnostic `AX_ABI_BREAKING_CHANGE`.
2. **Lockfile & Incremental Build Consistency**:
   - During local incremental builds, `CompilerDB` queries `AbiFingerprint` diffs to determine if downstream native object files must be relinked.

[SPEC-111; SPEC-112; REQ-PKG-022, REQ-PKG-024]

---

## 6. Diagnostics, Conformance & Canonical Examples

### `AXS-ABI-050` — Diagnostic Codes Owned by `SPEC-114`

| Code | Area | Sev | Emit Condition & Normative Rule |
|---|---|---|---|
| `AX_ABI_UNSTABLE_TYPE` | `FFI` | `error` | Attempting to pass or return an unstable type (capturing closure, unadorned/unrepr'd struct/enum, raw generic parameter, bare internal fat pointer/slice/string, internal trait object) across an `@abi(stable)` boundary (`AXS-ABI-004`, `AXS-ABI-017`). |
| `AX_ABI_EXTENSIBLE_MISSING_HEADER` | `FFI` | `error` | An `@abi(stable)` struct marked extensible or evolved with new fields is missing the mandatory `abi_version: u32, struct_size: u32` header fields (`AXS-ABI-011`). |
| `AX_ABI_OPAQUE_BY_VALUE` | `FFI` | `error` | An `@opaque` handle type is instantiated, queried for `size_of`/`align_of`, or passed/returned by value outside its defining module (`AXS-ABI-013`). |
| `AX_ABI_SYMBOL_VERSION_DUPLICATE` | `FFI` | `error` | Multiple exported functions within the same package define the same identifier, module path, and `@symbol_version` string, or multiple functions in a group are marked `default = true` (`AXS-ABI-030`). |
| `AX_ABI_BREAKING_CHANGE` | `FFI` | `error` | The `axiomc abi-check` tool detected a breaking ABI/API change (removed symbol, modified field layout/offsets, changed parameter types, altered calling convention) without an accompanying major SemVer bump (`AXS-ABI-040`, `AXS-ABI-041`). |
| `AX_ABI_SEMVER_MISMATCH` | `FFI` | `error` | The `axiomc abi-check` tool detected an additive ABI/API change across a version increment specified as a patch release (`AXS-ABI-040`, `AXS-ABI-041`). |

---

### `AXS-ABI-051` — Canonical Positive Examples (`=` and `.` Syntax)

#### Example 1 — Extensible Struct with `AbiHeader` and Stable View Usage

```axiom
module demo.abi_plugin

// Canonical 8-byte extensible struct header
@repr(C)
pub struct AbiHeader {
    abi_version: u32,
    struct_size: u32
}

// Extensible struct designed for forward/backward compatibility
@repr(C)
@abi(stable, version = "1.1")
pub struct PluginConfig {
    header: AbiHeader,
    flags: u32,
    timeout_ms: u32,
    // Field added in version 1.1 (appended at end):
    max_retries: u32
}

// Canonical stable view for borrowed string slices
@repr(C)
pub struct StableStr {
    ptr: *const u8,
    len: usize
}

@abi(stable, version = "1.1")
pub fn init_plugin(name: StableStr, cfg: view<PluginConfig>) -> i32 {
    let base_ok: bool = cfg.flags != 0u32
    if !base_ok {
        return -1
    }

    // Safely query extended field if present in client's struct:
    let retries: u32 = 0u32
    if cfg.header.struct_size >= 20u32 && cfg.header.abi_version >= 2u32 {
        retries = cfg.max_retries
    }

    return 0
}
```

#### Example 2 — Encapsulated State via `@opaque` Handle Pattern

```axiom
module demo.database_driver

// Opaque state handle: internal layout completely hidden from callers
@opaque
pub struct DbConnection

// Exported constructors, mutators, and destructors operating on pointers
@abi(stable, version = "1.0")
pub fn db_connect(uri: StableStr) -> *mut DbConnection {
    // Allocation and field initialization handled entirely inside the library
    let conn: *mut DbConnection = internal_allocate_db_conn(uri)
    return conn
}

@abi(stable, version = "1.0")
pub fn db_query(conn: *mut DbConnection, query: StableStr) -> u64 {
    if conn == null_mut<DbConnection>() {
        return 0u64
    }
    return internal_execute_query(conn, query)
}

@abi(stable, version = "1.0")
pub fn db_disconnect(conn: *mut DbConnection) {
    if conn != null_mut<DbConnection>() {
        internal_free_db_conn(conn)
    }
}
```

#### Example 3 — Allocator-Paired Buffer for Safe Cross-DLL Memory Ownership

```axiom
module demo.shared_buffer

@repr(C)
pub struct AllocatorVTable {
    alloc: fn(size: usize, align: usize) -> *mut u8,
    dealloc: fn(ptr: *mut u8, size: usize, align: usize),
    realloc: fn(ptr: *mut u8, old_size: usize, new_size: usize, align: usize) -> *mut u8
}

@repr(C)
@abi(stable, version = "1.0")
pub struct StableBuffer {
    ptr: *mut u8,
    len: usize,
    cap: usize,
    allocator: *const AllocatorVTable
}

@abi(stable, version = "1.0")
pub fn release_buffer(buf: mut_view<StableBuffer>) {
    if buf.ptr != null_mut<u8>() && buf.allocator != null<AllocatorVTable>() {
        let vtable: *const AllocatorVTable = buf.allocator
        (*vtable).dealloc(buf.ptr, buf.cap, 8usize)
        buf.ptr = null_mut<u8>()
        buf.len = 0usize
        buf.cap = 0usize
    }
}
```

#### Example 4 — Symbol Versioning Coexistence

```axiom
module demo.versioned_api

// Legacy v1.0 export
@abi(stable)
@symbol_version("1.0")
pub fn compute_hash(data: *const u8, len: usize) -> u32 {
    return legacy_crc32(data, len)
}

// Modern v2.0 export marked default for new linkers
@abi(stable)
@symbol_version("2.0", default = true)
pub fn compute_hash(data: *const u8, len: usize) -> u64 {
    return modern_blake3_64(data, len)
}
```

---

### `AXS-ABI-052` — Canonical Negative Examples (Compile-Time Rejection)

#### Example 1 — Rejection of Capturing Closure across `@abi(stable)` Boundary (`AX_ABI_UNSTABLE_TYPE`)

```axiom
module demo.invalid_closure

// ERROR: Capturing closure cannot cross @abi(stable) boundary
@abi(stable, version = "1.0")
pub fn register_callback(cb: |u32| -> u32) {
    // Compile error: AX_ABI_UNSTABLE_TYPE
    // Reason: Closure type contains an unversioned compiler-synthesized capture environment.
}
```

#### Example 2 — Rejection of Unannotated Struct (`AX_ABI_UNSTABLE_TYPE`)

```axiom
module demo.invalid_struct

// Unannotated struct: layout is internal and subject to field reordering
pub struct InternalPoint {
    x: f64,
    y: f64
}

// ERROR: Passing internal ADT across @abi(stable) boundary
@abi(stable, version = "1.0")
pub fn plot_point(pt: InternalPoint) {
    // Compile error: AX_ABI_UNSTABLE_TYPE
    // Reason: 'InternalPoint' lacks @repr(C) or @abi(stable) attribute.
}
```

#### Example 3 — Extensible Struct Missing Version/Size Header (`AX_ABI_EXTENSIBLE_MISSING_HEADER`)

```axiom
module demo.invalid_extensible

// Marked extensible, but first fields are NOT version/size header
@repr(C)
@abi(stable, extensible = true)
pub struct BrokenConfig {
    width: u32,
    height: u32
}
// Compile error: AX_ABI_EXTENSIBLE_MISSING_HEADER
// Reason: Extensible struct must begin with 'abi_version: u32, struct_size: u32' or 'AbiHeader'.
```

#### Example 4 — Instantiating `@opaque` Type by Value (`AX_ABI_OPAQUE_BY_VALUE`)

```axiom
module demo.invalid_opaque_usage

use demo.database_driver.DbConnection

pub fn bad_instantiation() {
    // ERROR: Attempting to instantiate an @opaque type by value
    let conn: DbConnection = DbConnection {}
    // Compile error: AX_ABI_OPAQUE_BY_VALUE
    // Reason: Opaque types have hidden layouts and can only be manipulated via pointers (*mut DbConnection).
}
```

#### Example 5 — Duplicate Symbol Version Definition (`AX_ABI_SYMBOL_VERSION_DUPLICATE`)

```axiom
module demo.invalid_symbol_version

@abi(stable)
@symbol_version("1.0", default = true)
pub fn process(x: u32) -> u32 {
    return x + 1u32
}

// ERROR: Duplicate symbol version "1.0" with multiple defaults
@abi(stable)
@symbol_version("1.0", default = true)
pub fn process(x: u32) -> u32 {
    return x + 2u32
}
// Compile error: AX_ABI_SYMBOL_VERSION_DUPLICATE
```

---

### `AXS-ABI-053` — Requirements Traceability Matrix

| Requirement | Description | Normative Rules | Implementation Tasks |
|---|---|---|---|
| `REQ-ECO-8734` | Axiom must enable dynamic plugins, hot-reloading, and safe dependency isolation across module boundaries. | `AXS-ABI-001` (Tier 3 Stable ABI), `AXS-ABI-004` (Firewall), `AXS-ABI-010`..`017` (Stable Type System, Opaque Handles, Views, Buffers), `AXS-ABI-030`..`032` (Symbol Versioning, Hot-Reload Fallback) | `T866`, `T867`, `T868`, `T869`, `T870`–`T873` |
| `REQ-PKG-022` | The build system must support reproducible builds, workspace dependency resolution, and semantic versioning of packages. | `AXS-ABI-002` (Compatibility Dimensions), `AXS-ABI-020`..`024` (`ApiFingerprint`, `SemanticFingerprint`, `AbiFingerprint`), `AXS-ABI-040`..`042` (SemVer Compatibility Classifier, `axiomc abi-check` CLI) | `T866`, `T867`, `T868`, `T869` |
| `REQ-PKG-024` | The ecosystem must support AXPACKAGE for deterministic, dependency-isolated package management without requiring runtime resolution. | `AXS-ABI-001` (Package Interface ABI `.axmeta`), `AXS-ABI-003` (No Universal ABI Freeze), `AXS-ABI-017` (Rejection of Unstable Types), `AXS-ABI-024` (Storage in `.axmeta`), `AXS-ABI-042` (Registry Publishing Gate) | `T866`, `T867`, `T868`, `T869` |

---

## Sources

- `0104` (`specs/0104`, Axiom — ABI Stability, FFI, Versioning & Binary Compatibility v0.1): §1–§7 (three ABI tiers, no universal stable ABI, explicit boundary); §8–§10 (`repr(C)`, `repr(transparent)`); §11–§12 (opaque types, handle FFI); §13–§15 (raw pointer ABI, string ABI, function pointers); §16–§17 (closure rejection); §18–§20 (trait ABI, static vs dynamic dispatch); §21–§22 (plugin ABI, function tables).
- `tasks/0452` (`tasks/0452`, BOOTSTRAP-193 — API Evolution, Axiom ABI, Versioning & Binary Compatibility): §193.1–§193.8 (three ABI tiers, source vs semantic vs ABI compatibility); §193.9–§193.13 (generic boundary, trait ABI); §193.14–§193.18 (struct evolution, opaque types, handles); §193.19 (symbol versioning); §193.20–§193.21 (`AbiFingerprint`, `ApiFingerprint`).
- `tasks/0583` (`tasks/0583`, BOOTSTRAP-324 — AXIOM ABI STABILITY, BINARY COMPATIBILITY & VERSIONED INTEROPERABILITY ENGINE): §324.1–§324.4 (compatibility matrix, ABI contract); §324.5–§324.8 (type classification, boundary firewall); §324.9–§324.10 (extensible struct, versioned ABI); §324.11–§324.14 (compatibility categories, symbol versioning, function compatibility); §324.15–§324.17 (ownership ABI, allocator ABI, cross-heap protection); §324.18–§324.20 (string ABI, enum ABI, Option/Result); §324.21–§324.22 (generic ABI, erased generic export).
- `tasks/0739` (`tasks/0739`, BOOTSTRAP-493 — PACKAGE ABI, BINARY INTERFACE DISTRIBUTION, PRECOMPILED GENERICS, MODULE INTERFACE FILES & FAST BINARY CONSUMPTION): §493.1–§493.10 (package interface, symbol identity, type identity); §493.18–§493.20 (layout metadata, private layout, opaque types); §493.21–§493.25 (`AbiFingerprint`, `SemanticFingerprint`, `ApiFingerprint`, compiler compatibility).
- `tasks/0661` (`tasks/0661`, BOOTSTRAP-402 — Package, Module, Workspace, Dependency & Reproducible Build Engine): §Goal, §5, §14, §18–§24 (package versioning, reproducible ABI metadata).
- `tasks/1065` (`tasks/1065`, BOOTSTRAP-800 — AXPACKAGE): §1, §50–§65, §112–§140, §199 (package ABI, reproducible distribution, interface verification).
- `spec/SPEC-24-artifact-format-module-interfaces.md`: `AXS-ART-002`, `AXS-ART-010..023` (canonical `ArtifactHeader`, `.axmi`, `.axmeta`, `TargetFingerprint`, `AbiFingerprint`).
- `spec/SPEC-50-unsafe-ub-ffi.md`: `AXS-UNS-030..036` (`@repr(C)`, `@repr(transparent)`, Win64/SysV ABI lowering, FFI safety).
- Requirements: `REQ-ECO-8734` (plugins, hot-reloading, isolation), `REQ-PKG-022` (reproducibility, SemVer), `REQ-PKG-024` (AXPACKAGE deterministic dependency isolation).
