# SPEC-61 — Canonical Compile-Time Reflection API, `@derive` Framework & Typed Code Generation Boundary Specification

Status: draft (T556, 2026-11-03)
Owner: axiom-architect
Consolidates: `specs/0102 (§1–68)`; `specs/0140 (Part XXI §1–48, AREFLECT-20..26, AGEN-20..25)`; `tasks/0296 (§1–100)`; `tasks/0343 (§1–100, AMETA-20..100)`; `tasks/0433 (§174.1–71, AREFLECT-20..30, AMETA-20..27, AZREFLECT-20..24)`; `tasks/0444 (§185.152, AREFLECT-20..22)`; `tasks/0509 (§1–183, COMPTIME-31..37, COMPTIME-58..67)`; `spec/SPEC-02-grammar.md`; `spec/SPEC-03-core-semantics.md`; `spec/SPEC-04-core-extensibility.md`; `spec/SPEC-10-ownership.md`; `spec/SPEC-11-capability.md`; `spec/SPEC-12-drop.md`; `spec/SPEC-30-concurrency.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-51-raw-memory-volatile-mmio-layout.md`; `spec/SPEC-53-safety-profiles-capability-security.md`; `spec/SPEC-60-comptime-2-0.md`.
Covers: `REQ-CTM-019`..`022`, `REQ-CTM-039`..`040`, `REQ-CORE-602`..`621` (and specifies the E14.2 contract for `T557`–`T560`: `REQ-CTM-043`, `REQ-CTM-045`, `REQ-CORE-622`..`682`, `REQ-CORE-2143`..`2149`, `REQ-CORE-2170`..`2179`).
Consumers: `compiler/hir/`, `compiler/sema/`, `compiler/types/`, `compiler/own/`, `compiler/mir/`, `compiler/interp/`, `std/reflect/`, `std/derive/`, `T557`–`T560`.

## Tóm tắt

Tài liệu `SPEC-61` chuẩn hóa mô hình phản chiếu tại thời điểm biên dịch (**Compile-Time Reflection**), khung dẫn xuất kiểu hóa **`@derive`**, và **ranh giới sinh mã có kiểu (`Typed Code Generation Boundary`)** cho phân hệ `E14.2` (Phase `P14`):
- **Phản chiếu tại thời điểm biên dịch là mô hình mặc định không chi phí runtime (`AMETA-20..29`, `AMETA-38..39`, `AREFLECT-20..21`, `AREFLECT-24`, `AREFLECT-28..30`, `AZREFLECT-20..24`, `REQ-CTM-039`, `REQ-CTM-043`, `REQ-CTM-045`, `REQ-CORE-602..611`, `REQ-CORE-620..621`)**: Phản chiếu kiểm tra thông tin ngữ nghĩa của trình biên dịch thông qua `type_info<T>() -> TypeInfo` (`StructInfo`, `EnumInfo`, `FieldInfo`, `VariantInfo`, `TraitInfo`, `AttributeInfo`, `StructLayout`) ngay trong `comptime`. Giá trị `Type` / `TypeInfo` chỉ tồn tại ở thời điểm biên dịch, không sinh đối tượng kiểu ở runtime, không gắn header RTTI vào object, và bị xóa bỏ hoàn toàn sau khi sinh mã trừ khi có yêu cầu xuất siêu dữ liệu runtime tường minh (`@reflect(runtime)`).
- **Bảo toàn phạm vi hiển thị (`visibility`), thứ tự khai báo tất định và hợp đồng truy vấn bố cục (`AMETA-30..37`, `AREFLECT-22..23`, `AREFLECT-26..27`, `COMPTIME-35`, `REQ-CTM-020..021`, `REQ-CORE-612..619`, `T557`)**: Phản chiếu tuân thủ nghiêm ngặt quy tắc `pub`/private của mô-đun và gói (`AX_REFLECT_PRIVATE_FIELD`), không bao giờ biến khai báo private thành API công khai ngầm. Danh sách trường và biến thể luôn được liệt kê theo đúng thứ tự khai báo nguồn tất định, tách biệt với bố cục vật lý trong bộ nhớ; các truy vấn `size_of<T>()`, `align_of<T>()`, `offset_of<T, F>()` tuân thủ hợp đồng `@repr` và chỉ khóa bố cục khi được quan sát tường minh (`AX_REFLECT_UNSPECIFIED_LAYOUT`).
- **Khung `@derive` có kiểu và ranh giới sinh mã nghiêm ngặt (`AMETA-40..77`, `AGEN-20..25`, `COMPTIME-31..34`, `COMPTIME-58..67`, `REQ-CTM-019`, `REQ-CTM-022`, `REQ-CTM-040`, `REQ-CORE-622..659`, `T558`)**: `@derive(Trait)` là cơ chế sinh khai báo ngữ nghĩa có kiểu (`typed HIR`), tuyệt đối không phải macro thay thế văn bản và cấm đột biến AST/HIR/MIR tùy ý. Mọi khai báo sinh ra đều mang truy vết nguồn gốc (`GenProvenanceId`) và bắt buộc đi qua toàn bộ quy trình phân giải tên, giải ràng buộc trait (`AX_DERIVE_FIELD_BOUND`), kiểm tra kiểu, ownership, capability, đồng thời (`Send`/`Share`), FFI/ABI, GPU và MIR verifier như mã nguồn thông thường.
- **Thư viện chuẩn `std.reflect` và dẫn xuất chuẩn không chi phí (`AMETA-78..100`, `REQ-CORE-660..682`, `T559`, `T560`)**: `std.reflect` và `std.derive` hiện thực hóa `@derive(Debug, Eq, Ord, Hash, Clone, Default, Serialize, Deserialize)` (kèm thuộc tính trường `@rename`, `@skip`, `@default`) chuyên biệt hóa trực tiếp thành mã truy cập từng trường mà không cần bảng RTTI lúc chạy.

---

## 1. Reflection & Metaprogramming Architecture: Six Distinct Mechanisms & Zero-Overhead Default (`AXS-RFL-001`..`004`)

### AXS-RFL-001 — Six Distinct Metaprogramming Concepts & Unified Comptime Foundation (`AMETA-20..23`, `AMETA-80..81`, `AMETA-100`, `REQ-CORE-602`..`605`, `REQ-CORE-662`..`663`, `REQ-CORE-682`)

1. **Six Distinct Mechanisms (`tasks/0343 §1–6`, `AMETA-20`, `AMETA-80..81`, `AMETA-100`, `REQ-CORE-602`, `REQ-CORE-662..663`, `REQ-CORE-682`)**:
   - Axiom strictly separates six compile-time mechanisms rather than conflating them into untyped macros:
     1. **Generic abstraction**: Parametric polymorphism (`fn f<T: Trait>(x: T)`) checked against trait bounds and specialized without source generation (`AMETA-20`, `AMETA-81`);
     2. **Comptime execution**: Execution of ordinary Axiom code during compilation under `SPEC-60` (`AMETA-21..23`, `REQ-CORE-603..605`);
     3. **Compile-time reflection**: Read-only structured introspection of compiler-known semantic entities (`AMETA-24`, `REQ-CORE-606`);
     4. **`@derive` synthesis**: Deterministic, reflection-driven synthesis of typed trait implementations (`AMETA-40`, `REQ-CORE-622`);
     5. **Typed declaration generation**: Structured construction of typed declarations via explicit compiler interfaces (`AMETA-54..55`, `AMETA-80`, `AMETA-89`);
     6. **Build-time source generation**: Managed build-graph file outputs compiled through the full ordinary compiler pipeline (`REQ-CTM-022`, `AMETA-55..56`, `AGEN-22`, `AGEN-24`).
2. **Ordinary Language Semantics (`AMETA-21..23`, `REQ-CORE-603..605`)**:
   - All compile-time reflection queries and `@derive` handlers execute within the unified Comptime 2.0 model (`SPEC-60 AXS-CTM-001`): they use the ordinary Axiom type system, ownership/capability rules, and sandboxed execution environment, never a second macro language (`AMETA-22..23`).

### AXS-RFL-002 — Compile-Time Reflection as Default vs Explicit Opt-In Runtime Metadata (`AMETA-24..28`, `AMETA-38..39`, `AMETA-85..87`, `AREFLECT-20..21`, `AREFLECT-24`, `AREFLECT-28..30`, `AZREFLECT-20..24`, `COMPTIME-36..37`, `REQ-CTM-039`, `REQ-CTM-043`, `REQ-CTM-045`, `REQ-CORE-606`..`610`, `REQ-CORE-620`..`621`, `REQ-CORE-667`..`669`, `REQ-CORE-2148`..`2149`)

1. **Compile-Time Reflection Is the Default (`AMETA-24..25`, `AMETA-27`, `AREFLECT-20..21`, `AZREFLECT-20..22`, `COMPTIME-36..37`, `REQ-CTM-043`, `REQ-CTM-045`, `REQ-CORE-606..607`, `REQ-CORE-609`, `REQ-CORE-2148..2149`)**:
   - Reflection inspects authoritative compiler semantic data (`CompilerDB` / HIR / `TypeTable`) rather than an independent database (`AMETA-24`, `AMETA-87`, `REQ-CORE-606`, `REQ-CORE-669`).
   - Compile-time reflection is the default reflection model (`AMETA-25`, `AREFLECT-20`, `REQ-CTM-043`, `REQ-CORE-607`): a compile-time `Type` / `TypeInfo` descriptor is purely a compile-time value (`AMETA-27`, `AREFLECT-21`, `COMPTIME-37`, `REQ-CORE-609`, `REQ-CORE-2149`) and is completely erased after code generation (`AZREFLECT-20`).
   - Serialization, formatting, hashing, comparison, and FFI binding code generated via compile-time reflection and `@derive` require **zero runtime reflection tables** (`AZREFLECT-22`).
2. **Optional, Explicit Runtime Reflection Without Object Headers (`AMETA-26`, `AMETA-28`, `AMETA-38..39`, `AMETA-85..86`, `AREFLECT-24`, `AREFLECT-28..30`, `AZREFLECT-21`, `AZREFLECT-24`, `REQ-CTM-039`, `REQ-CTM-045`, `REQ-CORE-608`, `REQ-CORE-610`, `REQ-CORE-620..621`, `REQ-CORE-667..668`)**:
   - Runtime reflection metadata (`RuntimeTypeInfo`) is never emitted by default (`AMETA-26`, `AREFLECT-28`, `AZREFLECT-21`, `REQ-CORE-608`) and incurs **zero mandatory binary size or runtime cost when unused** (`AMETA-39`, `AZREFLECT-24`, `REQ-CTM-045`, `REQ-CORE-621`).
   - Emitting runtime type descriptors into a binary requires explicit opt-in via `@reflect(runtime)` on the reflected declaration or an explicit `runtime_type_info<T>()` root (`AMETA-38`, `AREFLECT-24`, `AREFLECT-29`, `REQ-CTM-039`, `REQ-CORE-620`). Querying `runtime_type_info<T>()` on a type not opted into runtime metadata is rejected with `AX_REFLECT_RUNTIME_NOT_ENABLED`.
   - Even when runtime reflection is enabled for opted-in types, metadata lives in side-table `.rdata` descriptors; Axiom values NEVER carry hidden per-instance object headers or vtable pointers (`AMETA-28`, `REQ-CORE-610`). Unreferenced reflection metadata may be stripped by section GC / LTO (`AREFLECT-30`, `AMETA-26` of `0433`), and `.axmeta` package metadata is distinct from runtime binary metadata (`AMETA-85..86`, `REQ-CORE-667..668`).

### AXS-RFL-003 — Canonical Compile-Time Reflection Data Model (`TypeInfo`, `TypeKind`, `StructInfo`, `EnumInfo`, `FieldInfo`, `VariantInfo`, `TraitInfo`, `AttributeInfo`, `StructLayout`) (`AMETA-29`, `AMETA-37`, `AREFLECT-23..27`, `REQ-CORE-611`, `REQ-CORE-619`, `T557`, `T559`)

1. **Semantic Identity Over String Identity (`AREFLECT-23..25`, `AMETA-29`, `REQ-CORE-611`)**:
   - Reflection descriptors are keyed by canonical semantic `TypeId` and `DefId`, never by unhygienic raw string names (`AREFLECT-23`, `0140 AREFLECT-25`). Reflecting on a type never alters its semantic `TypeId` or language semantics (`AMETA-29`, `AREFLECT-24`, `REQ-CORE-611`).
2. **Canonical `std.reflect` Descriptor Types (`T557`, `T559`)**:
   - `TypeInfo`: `{ id: u64, name: Str, module_path: Str, kind: TypeKind, size: usize, align: usize, is_copy: bool, is_send: bool, is_share: bool, needs_drop: bool, attributes: view<[AttributeInfo]> }`.
   - `TypeKind`: tagged enum distinguishing `Primitive(PrimitiveKind)`, `Struct(StructInfo)`, `Enum(EnumInfo)`, `Tuple(view<[u64]>)`, `Array { elem: u64, len: usize }`, `Slice { elem: u64 }`, `View { inner: u64, is_mut: bool }`, `Pointer { pointee: u64, is_mut: bool }`, `Function { params: view<[u64]>, ret: u64, is_unsafe: bool, is_comptime: bool }`, and `Trait(TraitInfo)`.
   - `StructInfo`: `{ fields: view<[FieldInfo]>, repr: ReprKind, is_generic: bool, type_params: view<[u64]> }` and `FieldInfo`: `{ index: usize, name: Str, ty: u64, is_pub: bool, attributes: view<[AttributeInfo]> }`.
   - `EnumInfo`: `{ variants: view<[VariantInfo]>, repr: ReprKind, is_fieldless: bool }` and `VariantInfo`: `{ index: usize, name: Str, payload_types: view<[u64]>, discriminant: Option<i128>, attributes: view<[AttributeInfo]> }`.
   - `TraitInfo`: `{ id: u64, name: Str, methods: view<[Str]>, assoc_types: view<[Str]> }`, `AttributeInfo`: `{ name: Str, args: view<[Str]> }`, and `StructLayout`: `{ size: usize, align: usize, field_offsets: view<[usize]>, is_abi_stable: bool }`.

### AXS-RFL-004 — Compile-Time Reflection Intrinsics (`type_info<T>()`, `type_name<T>()`, `fields_of<T>()`, `variants_of<T>()`, `attributes_of<T>()`, `implements<T, Trait>()`) (`AMETA-35..36`, `REQ-CORE-617`..`618`, `T557`)

1. **Intrinsic Signatures & Evaluation (`compiler/sema/reflect.ax`, `compiler/interp/reflect.ax`, `T557`)**:
   - `comptime fn type_info<T>() -> TypeInfo`: returns the complete compile-time `TypeInfo` descriptor for `T`.
   - `comptime fn type_name<T>() -> Str`: returns the canonical qualified name of `T` (e.g. `"demo.User"`, `"Vec<i32>"`).
   - `comptime fn fields_of<T>() -> view<[FieldInfo]>`: returns the declaration-ordered fields of a struct `T` (or empty slice for non-structs), subject to visibility rules (`AXS-RFL-010`).
   - `comptime fn variants_of<T>() -> view<[VariantInfo]>`: returns the declaration-ordered semantic variants of an enum `T` (`AMETA-37`, `REQ-CORE-619`).
   - `comptime fn attributes_of<T>() -> view<[AttributeInfo]>`: returns the validated structured attributes attached to `T`.
   - `comptime fn implements<T, Trait>() -> bool`: queries the canonical trait solver (`compiler/traits/`) to determine whether concrete or constrained type `T` implements `Trait`.
2. **Trait & Generic Solver Authority (`AMETA-35..36`, `REQ-CORE-617..618`)**:
   - Trait reflection (`implements<T, Trait>()`, `TraitInfo`) delegates directly to the compiler's trait solver and coherence checker (`AMETA-35`, `REQ-CORE-617`), and generic reflection enforces all declared generic `where` bounds (`AMETA-36`, `REQ-CORE-618`). Reflection never bypasses trait solving or generic constraint verification.

---

## 2. Visibility, Encapsulation, Representation & Layout Query Contracts (`AXS-RFL-010`..`012`)

### AXS-RFL-010 — Visibility & Package Encapsulation in Reflection (`AMETA-33..34`, `AREFLECT-21..22`, `COMPTIME-35`, `REQ-CORE-615`..`616`, `REQ-CORE-2147`, `T557`)

1. **Reflection Is Never a Visibility Backdoor (`AMETA-33`, `AREFLECT-22`, `0140 AREFLECT-21`, `COMPTIME-35`, `REQ-CORE-615`, `REQ-CORE-2147`)**:
   - Compile-time reflection strictly obeys module and package privacy boundaries (`SPEC-60 AXS-CTM-004`). If a call site in module `M` is not permitted to access a non-`pub` field, variant, or item of type `T` defined in module `N != M`, then reflecting on `T`'s private fields (`fields_of<T>()`, `type_info<T>()`, or `offset_of<T, F>()`) from `M` is rejected at compile time with `AX_REFLECT_PRIVATE_FIELD`.
   - Same-module code (`M == N`) and `@derive(...)` handlers attached directly to `T`'s own declaration execute with the defining module's visibility authority and may inspect `T`'s private fields to synthesize trait implementations for `T`.
2. **No Silent Promotion of Private Declarations to Public API (`AMETA-34`, `AMETA-24` of `0433`, `REQ-CORE-616`)**:
   - Reflection and `@derive` cannot silently expose private types or private field accessors as part of a package's public API (`AMETA-34`, `REQ-CORE-616`), nor can `.axmeta` package metadata leak private implementation details across package boundaries (`0433 AMETA-24`).

### AXS-RFL-011 — Deterministic Declaration Order vs Physical Memory Layout (`AMETA-30..32`, `AMETA-37`, `AREFLECT-26..27`, `REQ-CTM-020`..`021`, `REQ-CORE-612`..`614`, `REQ-CORE-619`, `T557`)

1. **Deterministic Source Declaration Order (`AREFLECT-26..27`, `AMETA-37`, `REQ-CORE-619`)**:
   - `fields_of<T>()` and `StructInfo.fields` ALWAYS enumerate struct fields in their exact **source declaration order** (`index = 0, 1, ..., n - 1`), and `variants_of<T>()` / `EnumInfo.variants` ALWAYS enumerate enum variants in their exact **source declaration order** (`AREFLECT-26`).
   - Semantic declaration order and physical memory layout order are distinct concepts (`AREFLECT-27`): derived `Debug`, `Eq`, `Ord`, `Hash`, `Clone`, `Default`, and `Serialize`/`Deserialize` implementations iterate in deterministic semantic declaration order regardless of physical field layout.
   - Enum reflection observes semantic variants, payload types, and declared discriminants, never raw discriminant byte offsets or compiler niche encodings unless an explicit `@repr` contract applies (`AMETA-37`, `REQ-CORE-619`).
2. **Default Layout Freedom vs Explicit Representation Contracts (`AMETA-30`, `AMETA-32`, `0140 AREFLECT-22`, `REQ-CORE-612`, `REQ-CORE-614`)**:
   - Merely reflecting on a type's semantic fields (`fields_of<T>()`) or deriving `Debug`/`Eq`/`Hash`/`Serialize` does NOT create a physical representation or ABI stability contract (`AMETA-30`, `0140 AREFLECT-22`, `REQ-CORE-612`).
   - Default Axiom struct and enum layout remains compiler-controlled and non-stable across builds unless `@repr(C)`, `@repr(transparent)`, `@repr(packed)`, `@repr(u8..u64)`, or `@abi(stable)` is explicitly declared (`AMETA-32`, `REQ-CORE-614`, `SPEC-50 AXS-UNS-030`).

### AXS-RFL-012 — Layout Queries (`size_of<T>()`, `align_of<T>()`, `offset_of<T, F>()`) & Representation Observability (`AMETA-31..32`, `0140 AREFLECT-23`, `AZREFLECT-23`, `REQ-CTM-020`..`021`, `REQ-CORE-613`..`614`, `T557`)

1. **Representation-Contract Enforcement on Layout Queries (`AMETA-31`, `0140 AREFLECT-23`, `REQ-CORE-613`)**:
   - `size_of<T>() -> usize`, `align_of<T>() -> usize`, and `offset_of<T, F>() -> usize` (as well as `offset_of(T, field)` in `SPEC-51 AXS-MEM-020`) evaluate at compile time using the target's `TargetDesc` (`SPEC-60 AXS-CTM-013`) and obey the active `@repr` contract (`AMETA-31`, `0140 AREFLECT-23`, `REQ-CORE-613`).
   - Calling `offset_of` on a field of a type whose layout is not well-defined for field-offset introspection (such as an unmonomorphized generic type, an opaque `extern` type, a bitfield/non-addressable unit, or a type without deterministic layout) or naming a non-existent field is rejected with `AX_REFLECT_UNSPECIFIED_LAYOUT`.
2. **Observability & Optimizer Layout Consistency (`REQ-CTM-020`, `REQ-CTM-021`, `AZREFLECT-23`)**:
   - Querying `offset_of` or physical layout metadata makes that layout fact observable (`REQ-CTM-021`). Once a program or compilation unit observes the physical field offset of a struct `T`, the compiler and optimizer MUST NOT subsequently reorder or eliminate `T`'s physical fields in a way that invalidates the observed offset within that build (`REQ-CTM-020`).
   - Conversely, when physical layout metadata is NOT observed by `offset_of` or bound by `@repr(C)` / `@abi(stable)` / `@at`, compile-time reflection (`fields_of`, `@derive`) MUST NOT block SROA, dead-field elimination, or layout optimizations (`AZREFLECT-23`).

---

## 3. Typed `@derive` Framework & Code Generation Boundary (`AXS-RFL-020`..`024`)

### AXS-RFL-020 — Typed Semantic Generation Boundary: Prohibition of Textual Macros & Arbitrary IR Mutation (`AMETA-40..42`, `AMETA-50..56`, `AMETA-88..89`, `AMETA-93..97`, `AGEN-20..25`, `COMPTIME-31..34`, `REQ-CTM-019`, `REQ-CTM-022`, `REQ-CTM-040`, `REQ-CORE-622`..`624`, `REQ-CORE-632`..`638`, `REQ-CORE-670`..`671`, `REQ-CORE-675`..`679`, `REQ-CORE-2143`..`2146`, `T558`)

1. **`@derive` Is Typed Semantic Generation, Never Textual Macro Expansion (`REQ-CTM-019`, `AMETA-40`, `AMETA-53..54`, `AGEN-25`, `COMPTIME-33..34`, `REQ-CORE-622`, `REQ-CORE-635..636`, `REQ-CORE-2145..2146`)**:
   - `@derive(Trait1, Trait2, ...)` on a `struct` or `enum` is **typed semantic declaration synthesis**, not textual token substitution (`REQ-CTM-019`, `AMETA-40`, `AGEN-25`, `REQ-CORE-622`). Core v1.0 has no C-style preprocessor and does not use textual procedural macros as its foundational metaprogramming mechanism (`AMETA-53..54`, `COMPTIME-33..34`, `REQ-CORE-635..636`, `REQ-CORE-2145..2146`).
2. **Prohibition of Direct Compiler-State or Arbitrary AST/HIR/MIR Mutation (`AMETA-50..52`, `AMETA-88..89`, `AMETA-93..95`, `COMPTIME-32`, `REQ-CORE-632..634`, `REQ-CORE-670..671`, `REQ-CORE-675..677`, `REQ-CORE-2144`)**:
   - Reflection queries are strictly read-only views over compiler semantic state and can NEVER directly mutate `CompilerDB`, symbol tables, or type tables (`AMETA-88`, `REQ-CORE-670`).
   - Arbitrary in-place AST mutation (`AMETA-50`, `REQ-CORE-632`), arbitrary HIR mutation (`AMETA-51`, `REQ-CORE-633`), and direct MIR or machine-code mutation by user metaprogramming (`AMETA-52`, `COMPTIME-32`, `REQ-CORE-634`, `REQ-CORE-2144`) are forbidden in Core v1.0.
   - Untrusted packages cannot register arbitrary compiler plugins or mutate compiler internals (`AMETA-93..94`, `REQ-CORE-675..676`); typed generation occurs solely through explicit, versioned compiler generation interfaces (`AMETA-89`, `AMETA-95`, `REQ-CORE-671`, `REQ-CORE-677`).
3. **Distinction Between Typed Generation and Build-Time Source Generation (`REQ-CTM-022`, `AMETA-55..56`, `AGEN-22`, `AGEN-24`, `REQ-CORE-637..638`)**:
   - In-compiler typed generation (`@derive`) and build-time source file generation are distinct mechanisms (`AMETA-55`, `REQ-CORE-637`). Whenever a build step generates Axiom source files, those files are tracked as explicit build-graph inputs/outputs (`REQ-CTM-022`, `AGEN-22`) and compiled from scratch through the entire ordinary compiler pipeline (`AMETA-56`, `AGEN-24`, `REQ-CORE-638`).

### AXS-RFL-021 — Mandatory Full Semantic, Ownership, Capability, Concurrency, FFI & GPU Re-Verification (`AMETA-41..49`, `AMETA-82`, `AMETA-96..99`, `AGEN-20`, `COMPTIME-31`, `COMPTIME-63..67`, `REQ-CTM-040`, `REQ-CORE-623`..`631`, `REQ-CORE-664`, `REQ-CORE-678`..`681`, `REQ-CORE-2143`, `REQ-CORE-2175`..`2179`, `T558`)

1. **Generated Code Is Never Implicitly Trusted (`REQ-CTM-040`, `AMETA-41..43`, `AMETA-96..97`, `AGEN-20`, `COMPTIME-31`, `REQ-CORE-623..625`, `REQ-CORE-678..679`, `REQ-CORE-2143`)**:
   - Every declaration synthesized by `@derive`, comptime generation, or AI tooling is treated as an untrusted candidate declaration that MUST pass the complete ordinary compilation pipeline (`REQ-CTM-040`, `AGEN-20`, `AMETA-41..43`, `COMPTIME-31`, `REQ-CORE-623..625`, `REQ-CORE-2143`). Compiler semantic verification is unconditionally authoritative over both derived and AI-generated code (`AMETA-42`, `AMETA-96..97`, `REQ-CORE-624`, `REQ-CORE-678..679`).
2. **Full Pipeline Verification Checklist (`AMETA-44..49`, `AMETA-82`, `AMETA-98..99`, `COMPTIME-63..67`, `REQ-CORE-626..631`, `REQ-CORE-664`, `REQ-CORE-680..681`, `REQ-CORE-2175..2179`)**:
   - Every generated `impl` or item re-enters and must pass:
     1. **Name & generic resolution** (`COMPTIME-63`, `AMETA-82`, `REQ-CORE-664`, `REQ-CORE-2175`): resolving all paths and synthesizing generic `where` bounds (`impl<T: Trait> Trait for Boxed<T>`);
     2. **Trait & type checking** (`AMETA-44`, `COMPTIME-64`, `REQ-CORE-626`, `REQ-CORE-2176`): verifying every field/variant satisfies the derived trait's bounds and method signatures;
     3. **Ownership & `Drop` verification** (`AMETA-45`, `COMPTIME-65`, `REQ-CORE-627`, `REQ-CORE-2177`): enforcing move/`Copy` rules and rejecting illegal combinations such as `@derive(Copy)` on a type implementing `Drop` or containing a `!Copy` field;
     4. **Capability & effect verification** (`AMETA-46`, `COMPTIME-66`, `REQ-CORE-628`, `REQ-CORE-2178`): verifying `view<Self>` / `mut_view<Self>` non-aliasing and effect contracts;
     5. **Concurrency (`Send`/`Share`), GPU legality & FFI/ABI verification** (`AMETA-47..49`, `AMETA-98`, `COMPTIME-67`, `REQ-CORE-629..631`, `REQ-CORE-680`, `REQ-CORE-2179`), followed by **Verified MIR** checking (`INV-PIPE-002`) and dead-abstraction erasure (`AMETA-99`, `REQ-CORE-681`).

### AXS-RFL-022 — Generation Identity, Source Provenance (`GenProvenanceId`), Hygiene & Conflict/Cycle Diagnostics (`AMETA-57..60`, `AMETA-69..70`, `AMETA-90..92`, `AGEN-21`, `COMPTIME-58..62`, `REQ-CORE-639`..`642`, `REQ-CORE-651`..`652`, `REQ-CORE-672`..`674`, `REQ-CORE-2170`..`2174`, `T558`)

1. **Deterministic Semantic Identity & Provenance Mapping (`AMETA-57..60`, `AGEN-21`, `COMPTIME-58..60`, `REQ-CORE-639..642`, `REQ-CORE-2170..2172`)**:
   - Every generated declaration possesses a deterministic compiler `DefId` (`AMETA-57`, `AGEN-21`, `COMPTIME-58`, `REQ-CORE-639`, `REQ-CORE-2170`) and an explicit `GenProvenanceId` record `{ generator_kind, attr_span, target_def_id, field_or_variant_span }` (`AMETA-58..59`, `COMPTIME-59`, `REQ-CORE-640..641`, `REQ-CORE-2171`).
   - When a derived `impl` fails semantic checking because a field or variant payload of type `F` does not implement the required trait bound, `compiler/sema/derive_check.ax` emits `AX_DERIVE_FIELD_BOUND` with its primary span at the `@derive(...)` attribute and a secondary label pointing directly to the offending field or variant declaration (`AMETA-60`, `COMPTIME-60`, `REQ-CORE-642`, `REQ-CORE-2172`).
2. **Namespace Hygiene, Non-Overwrite & Conflict/Cycle Rejection (`AMETA-69..70`, `AMETA-90..92`, `COMPTIME-61..62`, `REQ-CORE-651..652`, `REQ-CORE-672..674`, `REQ-CORE-2173..2174`)**:
   - Generated declarations participate in ordinary namespace and trait coherence rules (`AMETA-90`, `REQ-CORE-672`), keep internal generated helpers private unless explicitly exported (`AMETA-92`, `REQ-CORE-674`), and NEVER silently overwrite existing user declarations or manual trait `impl`s (`AMETA-91`, `REQ-CORE-673`).
   - Duplicate `@derive(Trait, Trait)` entries on the same type, or a `@derive(Trait)` that collides with an explicit `impl Trait for T` (or a generated symbol collision), are deterministically rejected with `AX_DERIVE_CONFLICT` (`AMETA-69`, `COMPTIME-61`, `REQ-CORE-651`, `REQ-CORE-2173`).
   - Cyclic derive or generation dependencies are deterministically rejected with `AX_DERIVE_CYCLE` (`AMETA-70`, `COMPTIME-62`, `REQ-CORE-652`, `REQ-CORE-2174`).

### AXS-RFL-023 — Comptime Resource Limits, Incremental Dependency Tracking & Parallel Generation Determinism (`AMETA-61..68`, `AMETA-71..79`, `AMETA-83..84`, `AGEN-23`, `REQ-CORE-643`..`650`, `REQ-CORE-653`..`661`, `REQ-CORE-665`..`666`, `T558`, `T559`)

1. **Incremental Cache Identity & Public vs Private Fingerprints (`AMETA-61..65`, `AMETA-83..84`, `AGEN-23`, `REQ-CORE-643..647`, `REQ-CORE-665..666`)**:
   - Reflection queries and `@derive` expansions record fine-grained dependencies in the incremental build graph (`AMETA-61..62`, `REQ-CORE-643..644`). Generation cache keys (`AGEN-23`) include the target type's semantic fingerprint, attribute arguments, transitive comptime dependencies, and any authorized external comptime inputs (`AMETA-63..65`, `REQ-CORE-645..647`).
   - Generated public declarations (including `pub` derived trait implementations) are included in the package's public semantic fingerprint (`AMETA-83`, `REQ-CORE-665`), whereas private generated helpers do not invalidate downstream packages (`AMETA-84`, `REQ-CORE-666`).
2. **Parallel Determinism & Comptime Execution Discipline (`AMETA-66..68`, `AMETA-71..79`, `REQ-CORE-648..650`, `REQ-CORE-653..661`)**:
   - Independent `@derive` handlers may execute in parallel (`AMETA-67`, `REQ-CORE-649`) and MUST produce outputs semantically and byte-for-byte identical to deterministic serial execution (`AMETA-66`, `AMETA-68`, `REQ-CORE-648`, `REQ-CORE-650`).
   - All reflection and derive evaluation obeys `SPEC-60` resource budgets (`AMETA-71`), capability sandboxing (`AMETA-72..73`, `unsafe` never bypasses sandbox), structured panic diagnostics (`AMETA-74`), deterministic comptime `Drop` cleanup without runtime heap allocation (`AMETA-75..76`), erasure of comptime-only helpers (`AMETA-77`), and direct `.rdata` static data materialization without runtime initialization code (`AMETA-78..79`, `REQ-CORE-653..661`).

### AXS-RFL-024 — Standard Library `std.reflect` & Reflection-Driven `@derive(Debug, Eq, Ord, Hash, Clone, Default, Serialize, Deserialize)` (`T559`, `T560`)

1. **Canonical Derived Trait Set (`compiler/hir/derive.ax`, `std/reflect/`, `std/derive/`, `T558`, `T559`)**:
   - Axiom provides reflection-driven `@derive` handlers for `Copy`, `Clone`, `Eq` (`PartialEq`), `Ord` (`PartialOrd`), `Hash`, `Debug`, `Default`, `Serialize`, and `Deserialize` across structs, generic structs, fieldless enums, and payload enums.
   - Field and variant attributes inspected via `attributes_of<T>()` and `FieldInfo.attributes` / `VariantInfo.attributes` control derived behavior at compile time:
     - `@rename("wire_name")`: overrides the serialized/debug field or variant key name;
     - `@skip`: omits a field from `Serialize` / `Debug` (and uses `Default.default()` on `Deserialize`);
     - `@default(expr)`: supplies a fallback expression when a field is absent during `Deserialize` or `Default`.
   - Every derived method specializes at compile time into direct field-by-field or variant-match MIR operations with **zero runtime reflection table overhead** (`AZREFLECT-22`).

---

## 4. Diagnostic Taxonomy, Canonical Examples & Conformance Matrix (`AXS-RFL-050`..`052`)

### AXS-RFL-050 — Reflection & Derive Diagnostic Codes (`spec/diagnostics.md`, `T557`–`T558`)

In addition to `AX_TRAIT_UNKNOWN_DERIVE` (`spec/diagnostics.md §11`), self-hosted `axiomc` (`compiler/diag/code.ax`) defines the `REFLECT` (`AX_REFLECT_*`) and `DERIVE` (`AX_DERIVE_*`) diagnostic codes:

| Code | Sev | Task | Condition |
|---|---|---|---|
| `AX_REFLECT_PRIVATE_FIELD` | E | T557 | cross-module reflection (`fields_of<T>()`, `type_info<T>()`, `offset_of<T, F>()`) accesses private fields of `T` without defining-module or `@derive` authority (`AXS-RFL-010`, `AMETA-33..34`) |
| `AX_REFLECT_UNSPECIFIED_LAYOUT` | E | T557 | `offset_of` queried on a non-existent field or a type whose representation does not define a valid addressable field offset (`AXS-RFL-012`, `AMETA-31..32`) |
| `AX_REFLECT_RUNTIME_NOT_ENABLED` | E | T557 | `runtime_type_info<T>()` requested for a type `T` not explicitly opted into runtime reflection via `@reflect(runtime)` (`AXS-RFL-002`, `REQ-CTM-039`, `AMETA-26`, `AMETA-38`) |
| `AX_DERIVE_FIELD_BOUND` | E | T558 | `@derive(Trait)` applied to a struct or enum whose field or variant payload type does not implement `Trait`, carrying provenance spans for both `@derive` and the offending field/variant (`AXS-RFL-021..022`, `AMETA-44`, `AMETA-60`) |
| `AX_DERIVE_CONFLICT` | E | T558 | duplicate `@derive(Trait)` on the same type, or conflict between `@derive(Trait)` and an explicit `impl Trait for T` (`AXS-RFL-022`, `AMETA-69`, `AMETA-91`, `COMPTIME-61`) |
| `AX_DERIVE_CYCLE` | E | T558 | cyclic derive or compile-time declaration generation dependency (`AXS-RFL-022`, `AMETA-70`, `COMPTIME-62`) |
| `AX_DERIVE_UNSUPPORTED_ITEM` | E | T558 | `@derive(...)` attached to an unsupported declaration kind or illegal combination such as `@derive(Copy)` on a type implementing `Drop` (`AXS-RFL-021`, `AMETA-45`) |

### AXS-RFL-051 — Canonical Positive & Negative Examples (`axiom-syntax`: `=` and `.` only)

```axiom
module demo.reflect_derive

use std.reflect.type_info
use std.reflect.fields_of
use std.reflect.offset_of

@repr(C)
@derive(Debug, Clone, Eq, Ord, Hash, Default, Serialize, Deserialize)
pub struct PacketHeader {
    @rename("ver")
    pub version: u16,
    pub flags: u16,
    @default(0u32)
    pub seq: u32,
}

pub const HEADER_FIELD_COUNT: usize = comptime { fields_of<PacketHeader>().len() }
pub const SEQ_OFFSET: usize = comptime { offset_of<PacketHeader, "seq">() }

// Negative examples (rejected at compile time):
// struct NonEqHandle { raw: *mut u8 }
//
// @derive(Eq) //~ ERROR AX_DERIVE_FIELD_BOUND
// struct BadPacket {
//     handle: NonEqHandle, // secondary label: `NonEqHandle` does not implement `Eq`
// }
//
// @derive(Eq, Eq) //~ ERROR AX_DERIVE_CONFLICT
// struct DupDerive { x: i32 }
```

### AXS-RFL-052 — E14.2 Conformance Verification Matrix (`T557`–`T560`)

| Test ID | Verification Focus | Expected Outcome | Task |
|---|---|---|---|
| `RFL-T01` | `type_info<T>()`, `type_name<T>()`, `fields_of<T>()`, `variants_of<T>()`, `implements<T, Trait>()` | Evaluates at comptime in exact source declaration order with zero runtime RTTI emitted | T557, T560 |
| `RFL-T02` | Cross-module private field reflection vs same-module / `@derive` reflection | Cross-module rejected with `AX_REFLECT_PRIVATE_FIELD`; same-module and `@derive` accepted | T557, T560 |
| `RFL-T03` | `size_of<T>()`, `align_of<T>()`, `offset_of<T, F>()` on `@repr(C)` vs unspecified layout | `@repr(C)` returns exact target offsets; invalid layout/field rejected with `AX_REFLECT_UNSPECIFIED_LAYOUT` | T557, T560 |
| `RFL-T04` | Typed `@derive` re-verification, provenance diagnostics & conflict/cycle checks | Unsatisfied field bound emits `AX_DERIVE_FIELD_BOUND` with field span; conflicts emit `AX_DERIVE_CONFLICT` | T558, T560 |
| `RFL-T05` | `std.reflect` & `@derive(Debug, Eq, Ord, Hash, Clone, Default, Serialize, Deserialize)` with `@rename`/`@skip`/`@default` | Identical results in `--interp` and native x86-64 (`0 WEAK-NATIVE`) with zero runtime reflection overhead | T559, T560 |

---

## 5. Sources & Traceability

- **Corpus Specifications & Tasks**: `specs/0102 (§1–68)`; `specs/0140 (Part XXI §1–48, AREFLECT-20..26, AGEN-20..25)`; `tasks/0296 (§1–100)`; `tasks/0343 (§1–100, AMETA-20..100)`; `tasks/0433 (§174.1–71, AREFLECT-20..30, AMETA-20..27, AZREFLECT-20..24)`; `tasks/0444 (§185.152, AREFLECT-20..22)`; `tasks/0509 (§1–183, COMPTIME-31..37, COMPTIME-58..67)`.
- **Canonical Specs & ADRs**: `ADR-0007` (canonical `=` and `.` syntax); `ADR-0011` (diagnostic taxonomy); `spec/SPEC-04-core-extensibility.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-51-raw-memory-volatile-mmio-layout.md`; `spec/SPEC-60-comptime-2-0.md`.
- **Requirements Covered**: `REQ-CTM-019`..`022`, `REQ-CTM-039`..`040`, `REQ-CTM-043`, `REQ-CTM-045`, `REQ-CORE-602`..`682`, `REQ-CORE-2143`..`2149`, `REQ-CORE-2170`..`2179`.
