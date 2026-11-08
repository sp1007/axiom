# SPEC-115 — Canonical Axiom Dynamic Components, Plugin Discovery, Cross-Boundary Ownership/Capability Handles & Hot-Reload State Migration Specification

- **Status**: draft (T870, 2026-11-08)
- **Owner**: axiom-architect
- **Phase**: P20 (E20.7 — Dynamic Components, Plugins & Hot-Reload)
- **Rules**: `AXS-COMP-001` .. `AXS-COMP-055`
- **Covers**: `REQ-ECO-8734`
- **Consolidates**: `0104 (§20–§22, §54 AABI-68..69)`; `tasks/0583 (§324.6, §324.21)`; `tasks/0584 (§325.1–§325.32, BOOTSTRAP-325)`; `tasks/0739 (§493.1–§493.25)`; `tasks/0856 (§1–§45, §119–§134, §351, BOOTSTRAP-623)`; `spec/SPEC-114-abi-stability-versioning-binary-compat.md` (`AXS-ABI-001..053`); `spec/SPEC-89-artifact-library-matrix.md` (`AXS-ARTM-001..035`).
- **Consumers**: `compiler/component/interface`, `compiler/component/verify`, `std/component/loader`, `std/component/hot_reload`, `tests/run/component_interface`, `tests/run/component_hot_reload`, `tests/conformance/p20/e20_7_dynamic_components_hot_reload`, `T871`–`T873`.

---

## Tóm tắt

Đặc tả `SPEC-115` chuẩn hóa kiến trúc thành phần động (Axiom Dynamic Component Model), hệ thống khám phá và thương lượng plugin (Plugin Discovery & Negotiation), ranh giới cô lập sở hữu/năng quyền/bộ cấp phát bộ nhớ (Cross-Boundary Ownership, Capability & Allocator Isolation), và giao thức nạp lại nóng chuyển giao trạng thái có hoàn tác giao dịch (Deterministic State-Migrating Hot-Reload Protocol) cho ngôn ngữ Axiom (`REQ-ECO-8734`) thuộc phân hệ `E20.7` (Phase `P20`):

1. **Mô hình Component vượt trên C ABI thuần túy (`AXS-COMP-001`..`AXS-COMP-006`, `REQ-ECO-8734`)**:
   - Phân biệt rành mạch giữa Thư viện nguồn (`Library`), Thư viện liên kết động (`Dynamic Library`), Plugin được khám phá động (`Plugin`), và Thành phần giao kết (`Component` mang hợp đồng ABI, năng quyền và chu kỳ sống tường minh).
   - Khai báo giao diện thành phần `@component_interface` và điểm vào nhị phân duy nhất `@plugin_export fn axiom_component_entry()`.
   - Nhúng trực tiếp phân đoạn siêu dữ liệu `.axcomp` vào nhị phân thực thi (`PE .dll`, `ELF .so`, `Mach-O .dylib`, `WASM reactor`), chứa định danh logic `ComponentId` (không phụ thuộc tên tệp OS), phiên bản SemVer 2.0, băm nhị phân `AbiFingerprint` (BLAKE3-128), bảng định danh kiểu dữ liệu, hàm băm lược đồ trạng thái `StateSchemaId`, và bản kê khai năng quyền (`CapabilityManifest`).
   - Thiết kế phi áp đặt (Zero Mandatory Runtime): ứng dụng Axiom thuần túy biên dịch tĩnh không mang bất kỳ overhead hay thư viện nạp động bắt buộc nào.
2. **Khám phá động, thương lượng phiên bản và năng quyền tại thời điểm nạp (`AXS-COMP-010`..`AXS-COMP-015`, `REQ-ECO-8734`)**:
   - Máy chủ ứng dụng (`Host`) duyệt siêu dữ liệu `.axcomp` trước khi thực thi bất kỳ dòng mã máy nào của component.
   - Kiểm tra đối chiếu kép: `AbiFingerprint` và `TargetTriple` phải khớp chính xác tuyệt đối; dải phiên bản SemVer phải thỏa mãn ràng buộc của host (`AX_COMP_ABI_MISMATCH`).
   - Ranh giới năng quyền không có đặc quyền ngầm định (No Ambient Privilege): component phải liệt kê rõ năng quyền cần thiết (`fs.read`, `net.connect`, v.v.), và host cấp phát tường minh qua `CapabilityGrant`. Năng quyền không được phê chuẩn sẽ bị từ chối trước khi nạp (`AX_COMP_CAPABILITY_DENIED`).
   - Gắn kết giao diện an toàn kiểu định danh `acquire_interface<T>()` thông qua bảng hàm vtable ổn định của Stable Axiom ABI (`SPEC-114`).
3. **Cô lập sở hữu, bộ cấp phát bộ nhớ và an toàn Epoch Lease (`AXS-COMP-020`..`AXS-COMP-025`, `REQ-ECO-8734`)**:
   - Cấm hoàn toàn con trỏ thô không bảo vệ (`*T`, `*mut T`) vượt qua ranh giới `@component_interface` (`AX_COMP_RAW_POINTER_ESCAPE`).
   - Tránh sụp đổ bộ nhớ do lẫn lộn heap: Mọi khối nhớ heap chuyển giao qua biên giới phải được bao gói trong `ComponentBox<T>`, liên kết chặt chẽ với bảng hàm giải phóng của bộ cấp phát gốc (`Originating Allocator VTable`).
   - Quản lý tài nguyên dài hạn bằng bảng tay cầm thế hệ `ComponentHandle<T>` (`index: u32, generation: u32`), phát hiện truy cập sau khi giải phóng hoặc sau nạp lại (`AX_COMP_STALE_HANDLE`).
   - Theo dõi mượn an toàn bằng hợp đồng thuê thời kỳ `ComponentLease`: tuyệt đối ngăn chặn việc dỡ bỏ nhị phân (`unload`) khi còn bất kỳ tham chiếu `view`/`mut_view`, tác vụ nền, callback hay luồng xử lý nào đang giữ lease của epoch đó (`AX_COMP_UNLOAD_ACTIVE_LEASES`).
4. **Giao thức nạp lại nóng 5 pha & hoàn tác giao dịch (`AXS-COMP-030`..`AXS-COMP-037`, `REQ-ECO-8734`)**:
   - Quy trình nạp lại nóng xác định: `Quiesce` (chặn gọi mới, xả cạn lease đang hoạt động) → `ExportState` (chụp trạng thái định kiểu `@hot_reload_state`) → `LoadNewEpoch` (nạp nhị phân mới vào không gian địa chỉ riêng, xác thực manifest) → `MigrateState` (thực thi hàm chuyển đổi lược đồ trạng thái `migrate_state`) → `Resume` (hoán đổi con trỏ vtable nguyên tử, kích hoạt lại dịch vụ).
   - Bảo đảm tính giao dịch (Transactional Rollback): Nếu manifest không khớp, cấp phát thất bại, hoặc hàm di chuyển trạng thái trả về lỗi, hệ thống hủy bỏ quá trình nâng cấp và kích hoạt lại ngay lập tức epoch cũ với trạng thái nguyên vẹn.

---

## 1. Axiom Dynamic Component Model Architecture

### `AXS-COMP-001` — Component vs Library vs Plugin Separation

Axiom defines a strict, non-fungible ontological hierarchy for reusable and dynamic code artifacts (`0104 §20–§22`, `tasks/0584 §325.2–§325.3`, `tasks/0856 §4–§7`, `REQ-ECO-8734`):

```
+---------------------------------------------------------------------------------------+
| 1. Library (Source / Precompiled Compilation Unit)                                    |
| - Pure reusable code and types; compiled directly into the binary.                   |
| - Consumed via standard Axiom module imports (`import std.math.matrix`).              |
| - Boundary: Internal Axiom ABI (Tier 1) or Package Interface ABI (Tier 2).           |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| 2. Dynamic Library (Operating System Deployment Container)                             |
| - Native shared image (`.dll` on Windows, `.so` on Linux, `.dylib` on macOS).         |
| - Emits dynamic symbols via standard platform linkers (`SPEC-89`).                   |
| - Zero inherent knowledge of Axiom lifetimes, ownership, or capabilities.             |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| 3. Dynamic Plugin (Discovered Extensibility Unit)                                     |
| - A dynamic library packaged for runtime discovery in an application extension dir.  |
| - Exposes a well-known entry point for host introspection (`axiom_component_entry`). |
| - Provides runtime hooks and extension point implementations.                         |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| 4. Dynamic Component (Canonical Axiom Extensibility Boundary)                         |
| - A Dynamic Plugin enriched with an embedded `.axcomp` manifest contract.             |
| - Enforces Stable Axiom ABI (Tier 3, `SPEC-114`), explicit capability manifests,     |
|   originating allocator pairings (`ComponentBox<T>`), generational handle safety     |
|   (`ComponentHandle<T>`), and epoch-leased unload guards (`ComponentLease`).         |
+---------------------------------------------------------------------------------------+
```

1. **Not Every Shared Library is a Component**: A raw C `.dll` or `.so` is not an Axiom Component. Loading arbitrary shared libraries via raw platform loaders (`LoadLibraryW`, `dlopen`) is an `unsafe extern` operation governed by `SPEC-50` (`AXS-UNS-030..036`).
2. **Component Contract Guarantee**: An Axiom Dynamic Component MUST satisfy four invariant pillars:
   - **Contracted ABI**: All exposed dispatch tables adhere to the Stable Axiom ABI (`SPEC-114`).
   - **Declared Capabilities**: All host system capabilities required for execution (`fs`, `net`, `gpu`, `alloc`, `concurrency`) MUST be statically listed in the `.axcomp` descriptor.
   - **Memory & Allocator Isolation**: Cross-boundary allocations MUST carry an explicit destruction hook routed back to the component's originating allocator.
   - **Guarded Lifecycle**: The component cannot be unloaded while any active borrow, stack frame, spawned task, or registered callback holds an unreleased epoch lease.

[0104 §20–§22; tasks/0584 §325.2–§325.3; tasks/0856 §4–§7; SPEC-114 AXS-ABI-001; REQ-ECO-8734]

---

### `AXS-COMP-002` — Component Identity & Logical Naming

Component identity is decoupled from OS-specific filesystem paths and artifact filenames (`tasks/0584 §325.4`, `tasks/0856 §8–§10`, `REQ-ECO-8734`):

1. **`ComponentId` Coordinate**: Every dynamic component possesses a globally unique, dot-separated nominal identifier defined by the schema:
   ```
   ComponentId = "<vendor>.<namespace>.<name>"
   ```
   *Example*: `"com.acme.image.codec"`, `"org.axiom.plugin.sql_analyzer"`.
2. **Canonical Manifest Identity**: The `ComponentId` is declared in the source manifest via the `@component_manifest` attribute and embedded directly into the `.axcomp` binary section.
3. **Artifact Independence**: The host application identifies, selects, and tracks components by `ComponentId` and `SemanticVersion`, never by physical file names (e.g., `libcodec_v2.dll` vs `libcodec.so`). Renaming or moving the dynamic library file MUST NOT alter the runtime identity of the component.
4. **Namespace Shadowing & Collision Rejection**: A host runtime MUST reject duplicate registrations of the identical `(ComponentId, SemanticVersion)` pair within the same process context (`AX_COMP_DUPLICATE_REGISTRATION`).

[tasks/0584 §325.4; tasks/0856 §8–§10; REQ-ECO-8734]

---

### `AXS-COMP-003` — `@component_interface` Declaration & Stable VTable Lowering

Axiom establishes component boundaries using the `@component_interface` attribute applied to traits or public module interfaces (`0104 §20–§22`, `tasks/0584 §325.14–§325.15`, `tasks/0856 §13–§15`, `REQ-ECO-8734`):

1. **Interface Declaration**:
   ```axiom
   @component_interface(version = "1.2.0")
   pub trait ImageCodec {
       fn decode(input: view<u8>) -> Result<DecodedImage, CodecError>
       fn encode(image: view<DecodedImage>) -> Result<ComponentBox<u8>, CodecError>
       fn get_supported_formats() -> StableView<CodecFormat>
   }
   ```
2. **Compiler Lowering to Stable VTable**:
   When lowering a `@component_interface`, the compiler (`compiler/component/interface`) generates a deterministic Stable Axiom ABI vtable structure adhering to `SPEC-114`:
   ```axiom
   @repr(C)
   pub struct ImageCodecVTable {
       pub abi_version: u32,
       pub vtable_size: u32,
       pub interface_fingerprint: u128,
       pub decode: extern "C" fn(ctx: *mut (), input_ptr: *const u8, input_len: usize, out_result: *mut Result<DecodedImage, CodecError>) -> u32,
       pub encode: extern "C" fn(ctx: *mut (), image: *const DecodedImage, out_result: *mut Result<ComponentBox<u8>, CodecError>) -> u32,
       pub get_supported_formats: extern "C" fn(ctx: *const (), out_formats: *mut StableView<CodecFormat>) -> u32,
   }
   ```
3. **Internal Representation Encapsulation**: A `@component_interface` vtable MUST NOT expose internal compiler vtable pointers, non-repr-C fat pointers, or closure environments. The first parameter is always an opaque context pointer (`ctx: *mut ()`), followed by C-compatible scalar, view, or box arguments.
4. **Interface Fingerprinting**: The compiler computes a 128-bit BLAKE3 `InterfaceFingerprint` encompassing all method signatures, parameter passing modes, and return types. The host runtime verifies this hash at load time before invoking any method.

[0104 §20–§22; tasks/0584 §325.14–§325.15; tasks/0856 §13–§15; SPEC-114 AXS-ABI-010..017; REQ-ECO-8734]

---

### `AXS-COMP-004` — `@plugin_export` Entry Point & Manifest Hook

Every dynamic component binary MUST expose exactly one primary dynamic symbol entry point using the `@plugin_export` attribute (`0104 §21`, `tasks/0584 §325.31–§325.32`, `tasks/0856 §19–§21`, `REQ-ECO-8734`):

1. **Standard Symbol Name**: The entry point symbol is uniformly mangled across all platforms as `axiom_component_entry`.
2. **Signature Contract**:
   ```axiom
   @repr(C)
   pub struct ComponentHostContext {
       pub host_abi_version: u32,
       pub host_context_size: u32,
       pub host_fingerprint: u128,
       pub allocator: *const AllocatorVTable,
       pub logger: extern "C" fn(level: u32, msg_ptr: *const u8, msg_len: usize),
       pub acquire_host_service: extern "C" fn(service_id_ptr: *const u8, service_id_len: usize, out_vtable: *mut *const ()) -> u32,
   }

   @plugin_export
   pub extern "C" fn axiom_component_entry(
       host_ctx: *const ComponentHostContext,
       out_descriptor: *mut *const ComponentDescriptor
   ) -> u32
   ```
3. **Execution Safety**: Calling `axiom_component_entry` MUST perform zero heavy initialization, worker thread spawning, or resource allocation. Its sole function is to validate the host ABI version and return a pointer to the component's static, immutable `ComponentDescriptor`.
4. **Single-Entry Mandate**: Exposing multiple differing entry points or omitting `axiom_component_entry` in a `--kind cdylib` component build results in compilation error `AX_COMP_MISSING_ENTRY_POINT`.

[0104 §21; tasks/0584 §325.31–§325.32; tasks/0856 §19–§21; REQ-ECO-8734]

---

### `AXS-COMP-005` — The Embedded `.axcomp` Component Manifest Section

The compiler automatically emits an immutable binary metadata section named `.axcomp` into every dynamic component artifact (`tasks/0584 §325.5`, `tasks/0856 §20–§22`, `REQ-ECO-8734`):

1. **Section Placement**:
   - Windows PE/COFF: `.axcomp` section with flags `IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_MEM_READ` (`0x4000_0040`).
   - Linux / BSD ELF: `.axcomp` section with flags `SHF_ALLOC` (`0x2`).
   - macOS Mach-O: `__DATA_CONST,__axcomp` section.
   - WASM: Custom section named `"axiom.component"`.
2. **Binary Layout of `.axcomp` Header**:
   ```
   +0x00: Magic (4 bytes) = 0x504D4F43 ("COMP" ASCII)
   +0x04: FormatVersion (2 bytes) = 0x0001
   +0x06: HeaderSize (2 bytes) = 0x0080 (128 bytes)
   +0x08: ComponentIdOffset (4 bytes) + ComponentIdLength (4 bytes)
   +0x10: SemVerMajor (4 bytes) + SemVerMinor (4 bytes) + SemVerPatch (4 bytes) + SemVerPrereleaseOffset (4 bytes)
   +0x20: AbiFingerprint (16 bytes, BLAKE3-128 physical layout hash)
   +0x30: TargetTripleFingerprint (16 bytes, target CPU/OS/arch hash)
   +0x40: StateSchemaId (16 bytes, hash of serializable state types)
   +0x50: CapabilityCount (4 bytes) + CapabilityTableOffset (4 bytes)
   +0x58: ExportedInterfaceCount (4 bytes) + ExportedInterfaceTableOffset (4 bytes)
   +0x60: Reserved (32 bytes, zero-padded for future extensions)
   ```
3. **Section Immutability**: The `.axcomp` section resides in read-only mapped memory. The host runtime inspects this section prior to invoking any executable code from the component.
4. **Header Verification**: Corrupt magic, unrecognized format versions, or header length overflows cause the host loader to reject the component immediately with `AX_COMP_CORRUPT_MANIFEST`.

[tasks/0584 §325.5; tasks/0856 §20–§22; SPEC-89 AXS-ARTM-001..024; REQ-ECO-8734]

---

### `AXS-COMP-006` — Zero-Cost Ambient Architecture & Static Monolithic Freedom

Axiom enforces that dynamic component capabilities impose zero overhead on static applications (`tasks/0584 §325.1`, `tasks/0856 §1–§3, §5`, `REQ-ECO-8734`):

1. **No Mandatory Dynamic Loader**: An Axiom executable that does not import `std.component` or declare dynamic plugin extension points links without any component loader code, reflection structures, or dynamic linking stubs.
2. **Static Component Unification**: Any component implementing a `@component_interface` can be linked statically into a monolithic executable without code changes. In static mode:
   - The compiler elides `axiom_component_entry` and the `.axcomp` section.
   - Virtual calls across `@component_interface` vtables are subject to Whole Program Devirtualization and LTO (`SPEC-75 AXS-LTO-004..005`).
   - Generational handle table lookups optimize into direct struct indexing.
3. **No Garbage Collection or Managed VM**: The component architecture relies strictly on explicit ownership transfers, generational indexing, and epoch lease tracking. It NEVER introduces an ambient garbage collector, managed interpreter, or foreign scripting VM.

[tasks/0584 §325.1; tasks/0856 §1–§3, §5; SPEC-75 AXS-LTO-004..005; REQ-ECO-8734]

---

## 2. Dynamic Discovery, Version & Capability Negotiation

### `AXS-COMP-010` — Component Discovery Protocol & Pre-Flight Manifest Inspection

The component discovery subsystem enables safe enumeration and filtering of dynamically available components without executing foreign code (`tasks/0584 §325.6`, `tasks/0856 §40–§42`, `REQ-ECO-8734`):

1. **Discovery Directories**: The host runtime searches for dynamic component candidates within a configured ordered sequence of directories (e.g., `app_dir/components/`, `user_dir/plugins/`, or paths specified via `--component-path`).
2. **Pre-Flight Binary Inspection**:
   - Before calling OS dynamic linkers (`LoadLibraryW`, `dlopen`), the host loader (`std/component/loader`) opens the candidate binary file in read-only binary mode.
   - The loader parses the binary container headers (`PE32+`, `ELF64`, `Mach-O 64`, or WASM) and extracts the embedded `.axcomp` metadata section directly from disk.
   - **Zero Code Execution**: OS dynamic linkers invoke library initialization routines (`DllMain` on Windows, `.init_array` on ELF, `__mod_init_func` on Mach-O). By extracting `.axcomp` prior to dynamic loading, the host ensures that malicious, corrupt, or incompatible binaries cannot execute code during discovery.
3. **Pre-Flight Rejection**: If the `.axcomp` section is missing, corrupt, or indicates an incompatible target architecture or OS triple, the candidate is discarded with a structured diagnostic (`AX_COMP_MISSING_MANIFEST` or `AX_COMP_TARGET_MISMATCH`) without contaminating process memory.

```
Candidate File on Disk ("image_codec.dll")
       │
       ▼ (Read file headers without LoadLibrary/dlopen)
Parse Container (.axcomp section)
       │
       ├── Validate Magic ("COMP") & Schema Version
       ├── Extract ComponentId ("com.acme.image.codec")
       ├── Extract SemVer ("2.1.0")
       ├── Extract AbiFingerprint & StateSchemaId
       └── Extract Capability Manifest
       │
       ▼
Compatible? ──── NO ───► Discard Candidate (Zero execution)
       │
      YES
       ▼
Proceed to Load-Time Negotiation (AXS-COMP-011..013)
```

[tasks/0584 §325.6; tasks/0856 §40–§42; SPEC-89 AXS-ARTM-001..024; REQ-ECO-8734]

---

### `AXS-COMP-011` — Load-Time Version Negotiation & SemVer Matching

Dynamic component integration enforces semantic versioning compatibility at the boundary between host expectations and component capabilities (`tasks/0584 §325.7`, `tasks/0856 §10–§11`, `REQ-ECO-8734`):

1. **Host Version Constraint**: The host application requests components using a declarative SemVer 2.0 version constraint (`SPEC-111 AXS-PKG-005`):
   ```axiom
   let query = ComponentQuery {
       id: "com.acme.image.codec",
       version_requirement: SemVerReq.parse("^2.1.0"),
   }
   ```
2. **Evaluation Rules**:
   - Caret (`^`) constraints permit additive non-breaking updates: `^2.1.0` matches `>=2.1.0, <3.0.0`.
   - Patch-level updates (e.g., `2.1.1` replacing `2.1.0`) are accepted automatically.
   - Major version shifts (e.g., `3.0.0` vs `^2.1.0`) are strictly rejected.
   - Pre-release versions (e.g., `2.2.0-rc.1`) NEVER match stable requirement constraints unless explicitly permitted by the host configuration (`allow_prerelease = true`).
3. **Mismatched Version Diagnostic**: If the discovered component satisfies the nominal `ComponentId` but falls outside the requested version range, the loader rejects the component with diagnostic code `AX_COMP_VERSION_INCOMPATIBLE`.

[tasks/0584 §325.7; tasks/0856 §10–§11; SPEC-111 AXS-PKG-005; REQ-ECO-8734]

---

### `AXS-COMP-012` — Load-Time `AbiFingerprint` & Target Verification

SemVer compatibility is a necessary but insufficient condition for in-process dynamic loading. Physical binary layout agreement is mandatory (`tasks/0584 §325.7`, `tasks/0856 §12–§15`, `REQ-ECO-8734`):

1. **Dual Fingerprint Validation**: Before invoking `axiom_component_entry`, the host loader validates two hardware-level fingerprints embedded within the `.axcomp` header:
   - **`TargetTripleFingerprint`**: BLAKE3-128 hash of the compilation target architecture, operating system, vendor, and ABI profile (`x86_64-windows-msvc`, `aarch64-linux-gnu`, etc.).
   - **`AbiFingerprint`**: BLAKE3-128 hash of the Stable Axiom ABI layout table (`SPEC-114 AXS-ABI-023`).
2. **Absolute Fingerprint Agreement**:
   - The host runtime computes its own expected `AbiFingerprint` for each requested `@component_interface`.
   - If the component's embedded `AbiFingerprint` differs by even one bit from the host's expected fingerprint, the load sequence MUST abort immediately with diagnostic code `AX_COMP_ABI_MISMATCH`.
3. **No Unsafe Type Punning**: The host MUST NOT attempt to coerce or re-interpret mismatched struct fields or calling conventions. This rule prevents silent stack corruption, register mismatching, and catastrophic undefined behavior.

[tasks/0584 §325.7; tasks/0856 §12–§15; SPEC-114 AXS-ABI-020..026; REQ-ECO-8734]

---

### `AXS-COMP-013` — Explicit Capability Manifest & No Ambient Privilege

Axiom dynamic components operate under a strict Capability-Based Security Model (`tasks/0584 §325.8–§325.9`, `tasks/0856 §31–§34`, `REQ-ECO-8734`):

1. **Declared Required Capabilities**: Every dynamic component declares the exact set of host system capabilities it requires in its source manifest:
   ```axiom
   @component_manifest {
       id: "com.acme.image.codec",
       version: "2.1.0",
       capabilities: [
           Capability.HeapAllocation,
           Capability.FileSystemRead(path = "assets/textures"),
           Capability.Concurrency(max_threads = 4),
       ],
   }
   ```
2. **No Ambient System Access**: A dynamic component is granted ZERO ambient operating system privileges:
   - It cannot open raw file descriptors without an explicit `fs` capability grant.
   - It cannot initiate network sockets without an explicit `net` capability grant.
   - It cannot launch background worker threads without an explicit `concurrency` capability grant.
3. **Load-Time Host Grant Policy**:
   - The host application maintains an active `CapabilityGrant` policy defining what capabilities may be extended to plugins.
   - During load negotiation, the host verifies that all required capabilities in the component's manifest are satisfied by the host's grant:
     ```
     RequiredCapabilities ⊆ GrantedCapabilities
     ```
   - If a component requests an ungranted capability (e.g., requesting `Capability.NetworkConnect` when the host only grants read-only filesystem access), the loader MUST refuse to load the component, emitting diagnostic code `AX_COMP_CAPABILITY_DENIED`.

[tasks/0584 §325.8–§325.9; tasks/0856 §31–§34; REQ-ECO-8734]

---

### `AXS-COMP-014` — Capability Attenuation & Runtime Revocation

The host application retains authoritative control over all capabilities delegated to dynamic components throughout their execution lifecycle (`tasks/0584 §325.8`, `tasks/0856 §35–§36`, `REQ-ECO-8734`):

1. **Capability Attenuation (Restriction)**:
   - The host may attenuate (restrict) a granted capability before passing it to the component.
   - *Example*: A component requests `Capability.FileSystemRead(path = "*")`; the host attenuates this to `Capability.FileSystemRead(path = "workspace/cache")`.
   - Attenuation operates monotonically: a component cannot amplify, escalate, or regain broader privileges than granted by the host context.
2. **Capability Revocation**:
   - The host may revoke capabilities dynamically when transitioning a component into a maintenance or shutdown state.
   - Attempting to invoke a revoked capability interface returns an error result (`ComponentError.CapabilityRevoked`) rather than trapping or crashing the host process.
3. **Context-Confined Handles**: All capability tokens provided to the component are bound to the component's private `ComponentHostContext` and cannot be shared or leaked to other dynamic components.

[tasks/0584 §325.8; tasks/0856 §35–§36; REQ-ECO-8734]

---

### `AXS-COMP-015` — Type-Safe Interface Acquisition & VTable Binding

The dynamic component runtime exposes a type-safe mechanism for acquiring interface dispatch tables (`0104 §20–§22`, `tasks/0584 §325.31–§325.32`, `tasks/0856 §19–§21`, `REQ-ECO-8734`):

1. **Generic Acquisition API**:
   The host acquires an interface from a loaded component through the `acquire_interface<T>()` method provided by `std.component`:
   ```axiom
   let codec_res = component.acquire_interface<ImageCodec>()
   match codec_res {
       Result.Ok(codec) => {
           // Type-safe dispatch through stable vtable
           let img = codec.decode(raw_bytes)
       }
       Result.Err(err) => {
           // Interface missing, ABI mismatch, or version incompatible
       }
   }
   ```
2. **Type Identity Validation**:
   - Internally, `acquire_interface<T>()` transmits the 128-bit `InterfaceFingerprint` of `T` to the component's descriptor table.
   - The component verifies that it exports an interface matching that fingerprint.
   - If found, the component returns the typed vtable pointer paired with the component instance context.
3. **No Unchecked Function Pointers**: Client code NEVER performs unchecked `unsafe_cast` on raw symbol addresses returned from `dlsym` or `GetProcAddress`. Every interface acquisition is verified by the compiler and runtime.

[0104 §20–§22; tasks/0584 §325.31–§325.32; tasks/0856 §19–§21; SPEC-114 AXS-ABI-010..017; REQ-ECO-8734]

---

## 3. Ownership, Allocator & Memory Isolation Across Component Boundaries

### `AXS-COMP-020` — Prohibition of Raw Cross-Boundary Pointer Escapes

Axiom establishes strict compile-time isolation rules for all data crossing dynamic component boundaries (`0104 §21`, `tasks/0584 §325.9–§325.11`, `tasks/0856 §16–§17`, `REQ-ECO-8734`):

1. **Raw Pointer Prohibition**:
   - Safe `@component_interface` declarations MUST NOT accept or return raw pointers (`*T`, `*const T`, `*mut T`).
   - Declaring a raw pointer parameter or return type in a `@component_interface` without an explicit `unsafe extern` clause results in compile-time rejection with diagnostic code `AX_COMP_RAW_POINTER_ESCAPE`.
2. **Permitted Cross-Boundary Types**:
   Only verified Stable Axiom ABI types (`SPEC-114 §2`) are valid across a `@component_interface`:
   - Primitive fixed-width scalars: `i8..i64`, `u8..u64`, `f32`, `f64`, `bool`.
   - Stable structs annotated with `@repr(C)` and extensible size/version headers (`SPEC-114 AXS-ABI-011`).
   - Stable tagged enums annotated with explicit discriminant representations (`@repr(u8..u64)`).
   - Generational handles: `ComponentHandle<T>`.
   - Originating-allocator owned boxes: `ComponentBox<T>`.
   - Epoch-leased borrowed slices: `StableView<T>` and `StableStr`.
   - Extensible error results: `Result<T, ComponentError>`.
3. **Internal Memory Escape Prevention**:
   The compiler's boundary verifier (`compiler/component/verify`) tracks provenance and rejects any attempt to pass unleased stack addresses, internal string buffers, or compiler-managed collections (`Array<T>`, `Map<K, V>`) directly across component boundaries.

[0104 §21; tasks/0584 §325.9–§325.11; tasks/0856 §16–§17; SPEC-114 AXS-ABI-010..017; REQ-ECO-8734]

---

### `AXS-COMP-021` — Allocator Boundary Isolation & `ComponentBox<T>`

Dynamic components may link distinct C runtimes, embedded memory managers, or custom platform allocators. Mixed deallocation across dynamic boundaries is a primary cause of heap corruption (`0104 §23`, `tasks/0584 §325.10`, `tasks/0856 §16`, `REQ-ECO-8734`):

1. **The Mixed-Allocator Hazard**:
   If dynamic component $A$ allocates memory on its heap and hands a raw pointer to host $H$, calling $H$'s `free()` on that pointer causes catastrophic memory corruption or crash if $A$ and $H$ use different heaps (e.g., Windows MSVCRT vs UCRT, or custom jemalloc vs mimalloc).
2. **Canonical `ComponentBox<T>` Abstraction**:
   Every heap-allocated object transferred across a dynamic component boundary MUST be encapsulated within a `ComponentBox<T>`:
   ```axiom
   @repr(C)
   pub struct ComponentBox<T> {
       pub ptr: *mut T,
       pub allocator_vtable: *const AllocatorVTable,
       pub epoch_token: u64,
   }

   @repr(C)
   pub struct AllocatorVTable {
       pub deallocate: extern "C" fn(ctx: *mut (), ptr: *mut (), size: usize, align: usize),
       pub reallocate: extern "C" fn(ctx: *mut (), ptr: *mut (), old_size: usize, new_size: usize, align: usize) -> *mut (),
   }
   ```
3. **Originating Allocator Routing**:
   - When a `ComponentBox<T>` is dropped by the recipient (host or peer component), its destructor DOES NOT call the local default allocator.
   - It routes deallocation directly to `allocator_vtable.deallocate()`, ensuring that memory is reclaimed within the heap of the component that originally allocated it.
4. **Cross-Allocator Safety Enforcement**:
   Attempting to deallocate, reallocate, or transfer ownership of heap memory without passing through `ComponentBox<T>` triggers compilation error `AX_COMP_CROSS_ALLOCATOR_VIOLATION`.

[0104 §23; tasks/0584 §325.10; tasks/0856 §16; REQ-ECO-8734]

---

### `AXS-COMP-022` — Generational Handle Tables & `ComponentHandle<T>`

Long-lived stateful resources managed by a dynamic component (e.g., graphic textures, open databases, network sessions) are exposed to clients exclusively via generation-safe handles (`tasks/0584 §325.12`, `tasks/0856 §18`, `REQ-ECO-8734`):

1. **Handle Binary Structure**:
   ```axiom
   @repr(C)
   pub struct ComponentHandle<T> {
       pub index: u32,
       pub generation: u32,
       pub epoch_id: u32,
       pub _marker: PhantomData<T>,
   }
   ```
2. **Generational Slot Table**:
   - The component maintains an internal slot table:
     ```
     Slot[index] = { generation: u32, state: ResourceState, resource: *mut T }
     ```
   - When a resource is destroyed or invalidated, the slot's `generation` counter is incremented, and its state is set to `Vacant`.
3. **Use-After-Free & Dangling Handle Defense**:
   - Every interface call taking a `ComponentHandle<T>` validates:
     ```
     handle.index < table.capacity && table.slots[handle.index].generation == handle.generation
     ```
   - If a client attempts to use a stale handle (from a destroyed resource or an invalidated prior reload epoch), the component returns error `ComponentError.StaleHandle` or emits diagnostic `AX_COMP_STALE_HANDLE`.
   - Access to unmapped, freed, or reallocated memory is mathematically impossible.

[tasks/0584 §325.12; tasks/0856 §18; REQ-ECO-8734]

---

### `AXS-COMP-023` — Epoch-Leased `view` and `mut_view` References (`ComponentLease`)

Borrowed references (`view<T>`, `mut_view<T>`, `StableView<T>`, `StableStr`) crossing dynamic boundaries are bound to the component's execution epoch (`tasks/0584 §325.19–§325.21`, `tasks/0856 §28`, `REQ-ECO-8734`):

1. **The Dangling Code/Data Pointer Hazard**:
   If a host borrows a view of string data or internal buffers from a dynamic component, unloading that component while the view is still reachable causes immediate segmentation faults when the host attempts to dereference the unmapped virtual memory.
2. **Active Epoch Lease Tracking**:
   - Every dynamic component instance is associated with an active `EpochTracker`:
     ```axiom
     pub struct EpochTracker {
         pub epoch_id: u32,
         pub active_leases: AtomicU64,
         pub state: AtomicU32, // Active, Quiescing, Retired
     }
     ```
   - When a method on a `@component_interface` returns a borrowed `StableView<T>` or `StableStr`, it creates an ephemeral `ComponentLease` that atomically increments `active_leases`.
   - When the borrow terminates or goes out of scope, the lease drops and atomically decrements `active_leases`.
3. **Unload Lockout**:
   - The host runtime CANNOT physically unload (`FreeLibrary`, `dlclose`) a component epoch while `active_leases.load() > 0`.
   - Attempting to force an immediate unload while leases remain active results in rejection with diagnostic code `AX_COMP_UNLOAD_ACTIVE_LEASES`.

```
Component Memory Space (Epoch 1)
 ├── Code Segment (.text)
 ├── Static Data (.rdata / .data)
 └── Internal Buffers
         │
         │ (Return borrowed view<u8>)
         ▼
 Host Caller Context
  Holds: LeasedView<'a, u8>
  Holds: ComponentLease (Epoch 1 active_leases += 1)
         │
         ▼
 Host requests: component.unload()
  Runtime checks: active_leases == 0? ──── NO ───► REJECT AX_COMP_UNLOAD_ACTIVE_LEASES
                                                  (Deferred until borrow scope exits)
```

[tasks/0584 §325.19–§325.21; tasks/0856 §28; REQ-ECO-8734]

---

### `AXS-COMP-024` — In-Flight Task, Callback, Thread & GPU Liveness Guards

Component code execution extends beyond simple synchronous call frames into background asynchronous and hardware tasks (`tasks/0584 §325.27–§325.30`, `tasks/0856 §23–§28`, `REQ-ECO-8734`):

1. **Callback Registration Guards**:
   - Any callback registered by a dynamic component with the host (e.g., event listeners, log sinks) holds an epoch lease.
   - When the host initiates component shutdown, the host automatically deregisters or detaches all callbacks associated with that component before unmapping code.
2. **Asynchronous Task & Future Guards**:
   - If a component spawns an asynchronous task (`Future`) or enqueues work on a thread pool, the pending task holds an active `ComponentLease`.
   - The component cannot transition from `Quiescing` to `Unloaded` until all associated tasks complete or are safely cancelled.
3. **Worker Thread Join Requirement**:
   - If a component requested and was granted `Capability.Concurrency`, any worker thread spawned by the component MUST be cleanly terminated and joined prior to unloading.
   - A component cannot exit shutdown while an active OS thread has its instruction pointer within the component's module bounds.
4. **GPU Kernel Execution Fences**:
   - If a component dispatches GPU compute kernels or shader workloads containing component-owned bytecode/resources, the runtime MUST wait for the hardware completion fence (`GpuFence.wait()`) before proceeding with component code eviction.

[tasks/0584 §325.27–§325.30; tasks/0856 §23–§28; REQ-ECO-8734]

---

### `AXS-COMP-025` — Layout Isolation via `@opaque` Component Objects

Internal component implementation details MUST remain completely hidden from consuming clients (`0104 §20–§22`, `tasks/0584 §325.13`, `tasks/0856 §16–§18`, `REQ-ECO-8734`):

1. **Opaque Type Encapsulation**:
   Complex stateful structures defined within dynamic components are exposed as `@opaque` handle targets (`SPEC-114 AXS-ABI-013`):
   ```axiom
   @opaque
   pub struct DecoderSession
   ```
2. **Zero Client Layout Dependency**:
   - Consuming code knows only that `DecoderSession` is an incomplete nominal type.
   - The compiler forbids querying `size_of<DecoderSession>()` or `align_of<DecoderSession>()` outside the defining component.
   - Instantiating or passing `DecoderSession` by value triggers compile-time error `AX_ABI_OPAQUE_BY_VALUE`.
3. **Evolution Freedom**:
   Because clients interact with `DecoderSession` strictly via pointers (`*mut DecoderSession`), `ComponentBox<DecoderSession>`, or `ComponentHandle<DecoderSession>`, the component author may freely alter the internal struct layout, add or remove fields, and alter memory alignments between releases without breaking binary compatibility with existing host binaries.

[0104 §20–§22; tasks/0584 §325.13; tasks/0856 §16–§18; SPEC-114 AXS-ABI-013; REQ-ECO-8734]

---

## 4. Deterministic Hot-Reload & State Migration Protocol

### `AXS-COMP-030` — Hot-Reload Lifecycle State Machine & Epoch Transition Graph

Axiom hot-reload is an explicit, transactional, state-preserving runtime protocol, not a blind `dlclose + dlopen` reload (`0104 §54 AABI-68..69`, `tasks/0584 §325.22–§325.26`, `tasks/0856 §119–§134, §351`, `REQ-ECO-8734`):

```
       ┌────────────────────────────────────────────────────────┐
       │                                                        │
       ▼                                                        │
┌──────────────┐         ┌──────────────┐         ┌───────────┐ │
│ Active(Ep N) │ ──────► │  Quiescing   │ ──────► │ Exporting │ │
└──────────────┘         └──────────────┘         └───────────┘ │
                                                        │       │ (Rollback on failure)
                                                        ▼       │
┌──────────────┐         ┌──────────────┐         ┌───────────┐ │
│ Active(Ep N+1)│ ◄────── │  Migrating   │ ◄────── │  Staging  │ │
└──────────────┘ (Commit) └──────────────┘         └───────────┘ │
       │                                                │       │
       │                                                └───────┘
       ▼
┌──────────────┐
│ Retired(Ep N)│ ──────► (Drain active leases) ──────► Unloaded(Ep N)
└──────────────┘
```

1. **Epoch Numbering**: Every component instance possesses a strictly monotonically increasing epoch counter (`epoch_id: u32`). The initial load begins at Epoch 1; each successful reload advances the epoch by 1.
2. **Opt-In Reloadability**: Hot-reload is strictly opt-in (`tasks/0856 §3495`). A component must explicitly declare `@hot_reloadable` and export the required lifecycle hooks (`quiesce`, `export_state`, `migrate_state`, `resume`). Components that do not declare reloadability cannot be hot-swapped while running.
3. **Coexistence During Transition**: During the reload sequence, Epoch $N$ and candidate Epoch $N+1$ reside simultaneously in host process memory. Epoch $N$ is never unloaded until Epoch $N+1$ is fully validated and active.

[0104 §54; tasks/0584 §325.22–§325.26; tasks/0856 §119–§134, §351; REQ-ECO-8734]

---

### `AXS-COMP-031` — Phase 1: Quiescence Protocol (`Quiesce`)

Before mutating code or state, the host brings the running component into a deterministic quiescence state (`tasks/0584 §325.23`, `tasks/0856 §27`, `REQ-ECO-8734`):

1. **Operation Gating**:
   - The host runtime sets the component state to `ComponentStatus.Quiescing`.
   - New incoming method invocations on the component are intercepted by the host dispatcher:
     - Non-blocking callers receive `Result.Err(ComponentError.ComponentQuiescing)`.
     - Blocking/queued callers are suspended on a synchronization condition variable until reload finishes or aborts.
2. **Active Lease Draining**:
   - The host waits for active epoch leases (`active_leases`) to reach zero.
   - If active borrows, in-flight RPCs, or worker tasks do not drain within a configurable timeout (`quiesce_timeout_ms`), the host aborts the quiesce operation and returns the component to `ComponentStatus.Active` with diagnostic `AX_COMP_QUIESCE_TIMEOUT`.
3. **Callback Invalidation**:
   - All ephemeral event callbacks registered by Epoch $N$ with the host are detached and deactivated to prevent re-entrant execution during migration.

[tasks/0584 §325.23; tasks/0856 §27; REQ-ECO-8734]

---

### `AXS-COMP-032` — Phase 2: State Export & Typed Schema Snapshot (`ExportState`)

Once quiescent, the active epoch exports its transferable runtime state (`tasks/0584 §325.24–§325.25`, `tasks/0856 §120–§129`, `REQ-ECO-8734`):

1. **State Declaration (`@hot_reload_state`)**:
   State intended to survive hot-reload is explicitly annotated in the component source:
   ```axiom
   @hot_reload_state(schema_version = 2)
   pub struct SessionState {
       pub active_users: u32,
       pub total_processed_bytes: u64,
       pub cache_token: u64,
   }
   ```
2. **Deterministic Schema Fingerprinting**:
   The compiler computes a 128-bit `StateSchemaId` (BLAKE3 hash of all field names, types, layouts, and `schema_version`). This ID is embedded into the `.axcomp` manifest.
3. **Export Execution**:
   - The host calls the component's exported export hook:
     ```axiom
     export_state: extern "C" fn(ctx: *mut (), out_snapshot: *mut ComponentStateSnapshot) -> u32
     ```
   - The component packages its live state into a `ComponentStateSnapshot` containing the `StateSchemaId`, payload pointer, byte size, and deallocation vtable.
   - Raw pointers to functions, code trampolines, OS thread handles, or internal unmapped caches MUST NOT be included in transferable state.

[tasks/0584 §325.24–§325.25; tasks/0856 §120–§129; REQ-ECO-8734]

---

### `AXS-COMP-033` — Phase 3: Epoch Staging & Manifest Verification (`LoadNewEpoch`)

The host stages the candidate component binary without perturbing the running system (`tasks/0584 §325.22`, `tasks/0856 §131`, `REQ-ECO-8734`):

1. **Isolated Binary Loading**:
   - The host loads candidate library binary (Epoch $N+1$) into a distinct address space via the OS dynamic loader.
   - It parses `.axcomp` and calls `axiom_component_entry` to acquire the candidate `ComponentDescriptor`.
2. **Pre-Migration Gate Verification**:
   The host evaluates the candidate descriptor against four gating criteria:
   - **Identity**: `candidate.component_id == active.component_id`.
   - **ABI Compatibility**: `candidate.abi_fingerprint == host.expected_abi_fingerprint`.
   - **SemVer Alignment**: `candidate.version` satisfies host version requirements.
   - **Capability Policy**: `candidate.capabilities ⊆ host.granted_capabilities`.
3. **Pre-Migration Failure**:
   If any check fails, the host unmaps Epoch $N+1$ immediately. Epoch $N$ is untouched, has not released its memory, and is immediately un-quiesced.

[tasks/0584 §325.22; tasks/0856 §131; REQ-ECO-8734]

---

### `AXS-COMP-034` — Phase 4: State Schema Verification & Migration (`MigrateState`)

When schema differences exist between epochs, a deterministic migration function transforms the data (`tasks/0584 §325.24–§325.25`, `tasks/0856 §129`, `REQ-ECO-8734`):

1. **Schema Identity Fast Path**:
   If `candidate.state_schema_id == active.state_schema_id`, no transformation is required. The snapshot memory is adopted directly by Epoch $N+1$.
2. **Explicit Migration Function**:
   If schema IDs differ, Epoch $N+1$ MUST provide a registered migration function:
   ```axiom
   @hot_reload_migration(from_version = 1, to_version = 2)
   pub fn migrate_session_v1_to_v2(
       old_state: view<SessionStateV1>
   ) -> Result<SessionState, MigrationError> {
       return Result.Ok(SessionState {
           active_users: old_state.active_users,
           total_processed_bytes: old_state.total_processed_bytes,
           cache_token: 0, // Initialized default for new field
       })
   }
   ```
3. **Migration Failure Handling**:
   - If the candidate component lacks a migration path for the incoming `StateSchemaId`, or if `migrate_session` returns `Result.Err`, the reload fails with diagnostic `AX_COMP_HOT_RELOAD_MIGRATION_FAILED`.
   - The candidate Epoch $N+1$ is unloaded, and transactional rollback initiates.

[tasks/0584 §325.24–§325.25; tasks/0856 §129; REQ-ECO-8734]

---

### `AXS-COMP-035` — Phase 5: Atomic Resume & Activation (`Resume`)

Commit and resumption occurs via an atomic pointer switch (`tasks/0584 §325.22`, `tasks/0856 §131`, `REQ-ECO-8734`):

1. **Atomic Pointer Swap**:
   - The host updates its active component dispatch pointer using an atomic store with release memory semantics (`atomic_store_explicit(&active_component, new_component, memory_order_release)`).
   - From this instant, all new invocations route to Epoch $N+1$.
2. **Generational Handle Epoch Advance**:
   - The component's internal generational handle tables advance their epoch token to $N+1$.
   - Any valid resources migrated into Epoch $N+1$ retain their logical indices with new epoch tokens.
3. **Operation Resumption**:
   - The host transitions component status to `ComponentStatus.Active`.
   - Suspended/queued callers are unblocked and execute against Epoch $N+1$.
   - Re-registration of event callbacks and background workers resumes.

[tasks/0584 §325.22; tasks/0856 §131; REQ-ECO-8734]

---

### `AXS-COMP-036` — Transactional Rollback Guarantee

Axiom hot-reload is fully transactional: either the new epoch completely succeeds, or the old epoch remains running with zero state loss (`tasks/0856 §130–§132`, `REQ-ECO-8734`):

```
       Candidate Epoch N+1 Staging / Migration
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
   [ SUCCESS ]                       [ FAILURE ]
   - Atomic pointer swap             - Unmap candidate Epoch N+1
   - Epoch N+1 becomes Active        - Epoch N unquiesces
   - Epoch N becomes Retired         - Re-enable Epoch N callbacks
   - Commit complete                 - Unblock queued operations on Epoch N
                                     - ZERO state corruption or downtime
```

1. **Atomicity Guarantee**: If a crash, assertion, memory allocation failure, schema mismatch, or migration rejection occurs anywhere between `Quiesce` and `Resume`:
   - The host catches the failure.
   - Candidate Epoch $N+1$ is unmapped and evicted.
   - The original state snapshot remains in Epoch $N$.
   - Epoch $N$ is commanded to resume execution (`resume_state`).
   - The component returns to `ComponentStatus.Active` under Epoch $N$.
2. **Error Telemetry**: The host records a structured audit event detailing why hot-reload aborted, preserving system availability and diagnostic visibility.

[tasks/0856 §130–§132; REQ-ECO-8734]

---

### `AXS-COMP-037` — Physical Unload Safety & Deferred Retirement (`UnloadOldEpoch`)

Retiring an old epoch requires careful coordination with outstanding borrows (`tasks/0584 §325.19–§325.21`, `tasks/0856 §28`, `REQ-ECO-8734`):

1. **The `Retired` State**:
   Following a successful hot-reload, Epoch $N$ transitions to `ComponentStatus.Retired`. It receives zero new calls, but its code segment remains mapped in memory.
2. **Deferred Unload**:
   - The host monitors the `active_leases` counter on Epoch $N$.
   - If any thread holds a stack frame or borrow into Epoch $N$, Epoch $N$ remains resident in memory.
   - When and only when `active_leases.load() == 0`, the host runtime executes physical unmapping (`FreeLibrary` / `dlclose`).
3. **No Code Unmapping Under Live Stacks**: Physical unmapping of dynamic libraries while any thread's instruction pointer resides within that library's address range is an invariant violation strictly prevented by the epoch lease runtime.

[tasks/0584 §325.19–§325.21; tasks/0856 §28; REQ-ECO-8734]

---

## 5. Standard Library Component Subsystem (`std.component`)

### `AXS-COMP-040` — `std.component.loader` Architecture & Interfaces

The standard library module `std.component.loader` provides high-level abstractions for host-side component lifecycle management (`tasks/0584 §325.6–§325.8`, `tasks/0856 §25`, `REQ-ECO-8734`):

```axiom
package std.component.loader

import std.fs.path.Path
import std.string.String
import std.semver.SemanticVersion
import std.semver.SemVerReq
import std.component.handle.ComponentBox

pub struct ComponentHost {
    pub granted_capabilities: CapabilityMask,
    pub search_paths: Array<Path>,
}

pub struct Component {
    pub id: String,
    pub version: SemanticVersion,
    pub epoch_id: u32,
    pub descriptor: *const ComponentDescriptor,
    pub host_context: *mut ComponentHostContext,
}

impl ComponentHost {
    pub fn new(granted_caps: CapabilityMask) -> ComponentHost {
        return ComponentHost {
            granted_capabilities: granted_caps,
            search_paths: Array.new(),
        }
    }

    pub fn add_search_path(self: mut_view<ComponentHost>, path: Path) {
        self.search_paths.push(path)
    }

    pub fn discover(self: view<ComponentHost>, query: ComponentQuery) -> Result<Array<DiscoveredComponent>, ComponentError> {
        // Reads .axcomp from disk without loading dynamic library code (AXS-COMP-010)
    }

    pub fn load(self: mut_view<ComponentHost>, candidate: view<DiscoveredComponent>) -> Result<Component, ComponentError> {
        // Negotiates version, ABI fingerprint, and capabilities before calling axiom_component_entry
    }
}

impl Component {
    pub fn acquire_interface<T>(self: view<Component>) -> Result<T, ComponentError> {
        // Type-safe lookup by InterfaceFingerprint (AXS-COMP-015)
    }

    pub fn unload(self: mut_view<Component>) -> Result<(), ComponentError> {
        // Enforces active_leases == 0 before physical unmapping (AXS-COMP-023)
    }
}
```

[tasks/0584 §325.6–§325.8; tasks/0856 §25; REQ-ECO-8734]

---

### `AXS-COMP-041` — `std.component.handle` & Cross-Boundary Ownership

The `std.component.handle` module defines generational indexing structures and memory-safe cross-boundary boxes (`tasks/0584 §325.10–§325.12`, `tasks/0856 §16–§18`, `REQ-ECO-8734`):

```axiom
package std.component.handle

@repr(C)
pub struct ComponentHandle<T> {
    pub index: u32,
    pub generation: u32,
    pub epoch_id: u32,
}

pub struct ComponentHandleTable<T> {
    pub slots: Array<HandleSlot<T>>,
    pub free_list: Array<u32>,
    pub current_epoch: u32,
}

pub struct HandleSlot<T> {
    pub generation: u32,
    pub item: Option<T>,
}

impl<T> ComponentHandleTable<T> {
    pub fn new(epoch_id: u32) -> ComponentHandleTable<T> {
        return ComponentHandleTable {
            slots: Array.new(),
            free_list: Array.new(),
            current_epoch: epoch_id,
        }
    }

    pub fn insert(self: mut_view<ComponentHandleTable<T>>, val: T) -> ComponentHandle<T> {
        if self.free_list.is_empty() {
            let idx = self.slots.len() as u32
            self.slots.push(HandleSlot { generation: 1, item: Option.Some(val) })
            return ComponentHandle { index: idx, generation: 1, epoch_id: self.current_epoch }
        }
        let idx = self.free_list.pop().unwrap()
        let slot = self.slots.get_mut(idx as usize)
        slot.generation = slot.generation + 1
        slot.item = Option.Some(val)
        return ComponentHandle { index: idx, generation: slot.generation, epoch_id: self.current_epoch }
    }

    pub fn get(self: view<ComponentHandleTable<T>>, handle: ComponentHandle<T>) -> Result<view<T>, ComponentError> {
        if (handle.index as usize) >= self.slots.len() {
            return Result.Err(ComponentError.StaleHandle)
        }
        let slot = self.slots.get(handle.index as usize)
        if slot.generation != handle.generation || handle.epoch_id != self.current_epoch {
            return Result.Err(ComponentError.StaleHandle)
        }
        return match slot.item {
            Option.Some(item) => Result.Ok(item.as_view()),
            Option.None => Result.Err(ComponentError.StaleHandle),
        }
    }

    pub fn release(self: mut_view<ComponentHandleTable<T>>, handle: ComponentHandle<T>) -> Result<T, ComponentError> {
        if (handle.index as usize) >= self.slots.len() {
            return Result.Err(ComponentError.StaleHandle)
        }
        let slot = self.slots.get_mut(handle.index as usize)
        if slot.generation != handle.generation || handle.epoch_id != self.current_epoch {
            return Result.Err(ComponentError.StaleHandle)
        }
        let val = slot.item.take().unwrap()
        slot.generation = slot.generation + 1
        self.free_list.push(handle.index)
        return Result.Ok(val)
    }
}
```

[tasks/0584 §325.10–§325.12; tasks/0856 §16–§18; REQ-ECO-8734]

---

### `AXS-COMP-042` — `std.component.lease` & Epoch Tracking

The `std.component.lease` module enforces lifetime lease guarantees across dynamic code boundaries (`tasks/0584 §325.19–§325.21`, `tasks/0856 §28`, `REQ-ECO-8734`):

```axiom
package std.component.lease

import std.sync.atomic.AtomicU64
import std.sync.atomic.AtomicU32

pub struct EpochTracker {
    pub epoch_id: u32,
    pub active_leases: AtomicU64,
    pub state: AtomicU32,
}

pub struct EpochLease {
    pub tracker: *const EpochTracker,
    pub epoch_id: u32,
}

impl EpochTracker {
    pub fn new(epoch_id: u32) -> EpochTracker {
        return EpochTracker {
            epoch_id: epoch_id,
            active_leases: AtomicU64.new(0),
            state: AtomicU32.new(1), // 1 = Active
        }
    }

    pub fn acquire_lease(self: view<EpochTracker>) -> Result<EpochLease, ComponentError> {
        let current_state = self.state.load()
        if current_state != 1 {
            return Result.Err(ComponentError.ComponentQuiescing)
        }
        self.active_leases.fetch_add(1)
        return Result.Ok(EpochLease { tracker: self as *const EpochTracker, epoch_id: self.epoch_id })
    }
}

impl Drop for EpochLease {
    fn drop(self: mut_view<EpochLease>) {
        let tracker = unsafe { &*self.tracker }
        tracker.active_leases.fetch_sub(1)
    }
}
```

[tasks/0584 §325.19–§325.21; tasks/0856 §28; REQ-ECO-8734]

---

### `AXS-COMP-043` — `std.component.hot_reload` Transactional Manager

The `std.component.hot_reload` module orchestrates multi-epoch state migration with automatic rollback (`tasks/0584 §325.22–§325.26`, `tasks/0856 §119–§134`, `REQ-ECO-8734`):

```axiom
package std.component.hot_reload

import std.component.loader.Component
import std.component.loader.ComponentHost
import std.fs.path.Path

pub struct HotReloadManager {
    pub host: ComponentHost,
    pub active_component: Component,
    pub quiesce_timeout_ms: u64,
}

impl HotReloadManager {
    pub fn new(host: ComponentHost, initial_component: Component) -> HotReloadManager {
        return HotReloadManager {
            host: host,
            active_component: initial_component,
            quiesce_timeout_ms: 5000,
        }
    }

    pub fn reload(self: mut_view<HotReloadManager>, new_binary_path: Path) -> Result<u32, HotReloadError> {
        // Step 1: Quiesce active epoch
        let quiesce_res = self.active_component.quiesce(self.quiesce_timeout_ms)
        if quiesce_res.is_err() {
            return Result.Err(HotReloadError.QuiesceTimeout)
        }

        // Step 2: Export live state snapshot
        let snapshot_res = self.active_component.export_state()
        if snapshot_res.is_err() {
            self.active_component.resume()
            return Result.Err(HotReloadError.StateExportFailed)
        }
        let state_snapshot = snapshot_res.unwrap()

        // Step 3: Load and validate candidate binary
        let candidate_res = self.host.stage_candidate(new_binary_path)
        if candidate_res.is_err() {
            self.active_component.resume()
            return Result.Err(HotReloadError.CandidateValidationFailed)
        }
        let candidate = candidate_res.unwrap()

        // Step 4: Migrate state into candidate
        let migrate_res = candidate.migrate_state(state_snapshot)
        if migrate_res.is_err() {
            // Transactional rollback: discard candidate, resume active epoch
            candidate.evict()
            self.active_component.resume()
            return Result.Err(HotReloadError.MigrationFailed)
        }

        // Step 5: Atomic commit
        let old_epoch = self.active_component.epoch_id
        let new_epoch = candidate.epoch_id
        self.active_component.retire()
        self.active_component = candidate
        self.active_component.resume()

        return Result.Ok(new_epoch)
    }
}
```

[tasks/0584 §325.22–§325.26; tasks/0856 §119–§134; REQ-ECO-8734]

---

## 6. Diagnostics, Conformance & Canonical Examples

### `AXS-COMP-050` — Diagnostics Taxonomy

Dynamic component, boundary verification, and hot-reload operations emit structured diagnostic codes in the `COMP` area (`spec/diagnostics.md`, `ADR-0011`):

| Code | Severity | Stage | Description |
|---|---|---|---|
| `AX_COMP_MISSING_ENTRY_POINT` | Error | Semantic | Dynamic component binary is missing the mandatory `@plugin_export fn axiom_component_entry` entry point (`AXS-COMP-004`). |
| `AX_COMP_MISSING_MANIFEST` | Error | Driver/Loader | The `.axcomp` binary section was not found within the inspected dynamic library image (`AXS-COMP-005`). |
| `AX_COMP_CORRUPT_MANIFEST` | Error | Driver/Loader | The `.axcomp` section header contains invalid magic, an unknown version, or out-of-bounds offsets (`AXS-COMP-005`). |
| `AX_COMP_DUPLICATE_REGISTRATION` | Error | Loader | Duplicate registration of the identical `(ComponentId, SemanticVersion)` pair within the same process context (`AXS-COMP-002`). |
| `AX_COMP_TARGET_MISMATCH` | Error | Loader | The component target triple hash does not match the host executable target triple (`AXS-COMP-012`). |
| `AX_COMP_VERSION_INCOMPATIBLE` | Error | Loader | Discovered component version does not satisfy the host SemVer requirement query (`AXS-COMP-011`). |
| `AX_COMP_ABI_MISMATCH` | Error | Loader | Component `AbiFingerprint` differs from the host expected interface layout hash (`AXS-COMP-012`). |
| `AX_COMP_CAPABILITY_DENIED` | Error | Loader | Component manifest requests capabilities not granted by the host `CapabilityGrant` policy (`AXS-COMP-013`). |
| `AX_COMP_RAW_POINTER_ESCAPE` | Error | Semantic | Safe `@component_interface` declaration accepts or returns a raw pointer (`*T`, `*mut T`) (`AXS-COMP-020`). |
| `AX_COMP_CROSS_ALLOCATOR_VIOLATION` | Error | Semantic/Runtime | Owned heap allocation crossed a dynamic boundary without an originating allocator binding (`ComponentBox<T>`) (`AXS-COMP-021`). |
| `AX_COMP_STALE_HANDLE` | Error | Runtime | Access attempted using a `ComponentHandle` whose generation or epoch token has been invalidated (`AXS-COMP-022`). |
| `AX_COMP_UNLOAD_ACTIVE_LEASES` | Error | Runtime | Physical library unload attempted while active epoch leases, borrows, tasks, or callbacks remain live (`AXS-COMP-023`). |
| `AX_COMP_QUIESCE_TIMEOUT` | Error | Runtime | Hot-reload quiescence failed because active operations did not drain within the timeout limit (`AXS-COMP-031`). |
| `AX_COMP_HOT_RELOAD_SCHEMA_MISMATCH` | Error | Runtime | Hot-reload state snapshot schema version cannot be parsed by candidate component (`AXS-COMP-034`). |
| `AX_COMP_HOT_RELOAD_MIGRATION_FAILED` | Error | Runtime | Hot-reload migration hook returned an error; transactional rollback executed to previous epoch (`AXS-COMP-034`, `AXS-COMP-036`). |

[spec/diagnostics.md; ADR-0011; REQ-ECO-8734]

---

### `AXS-COMP-051` — Canonical Examples: Component Interface & Export

```axiom
// Positive Example: Defining a dynamic component interface and plugin export

package examples.image_plugin

import std.component.handle.ComponentBox
import std.component.handle.ComponentHandle
import std.view.StableView
import std.view.StableStr

@component_interface(version = "1.0.0")
pub trait FilterPlugin {
    fn apply_filter(image_data: mut_view<u8>, width: u32, height: u32) -> Result<(), FilterError>
    fn get_filter_name() -> StableStr
}

@repr(C)
pub struct SepiaFilter {
    pub intensity: f32,
}

impl FilterPlugin for SepiaFilter {
    fn apply_filter(self: view<SepiaFilter>, image_data: mut_view<u8>, width: u32, height: u32) -> Result<(), FilterError> {
        let total_pixels = (width * height) as usize
        let mut idx = 0 as usize
        while idx < total_pixels {
            let r = image_data[idx * 4] as f32
            let g = image_data[idx * 4 + 1] as f32
            let b = image_data[idx * 4 + 2] as f32
            image_data[idx * 4] = ((r * 0.393) + (g * 0.769) + (b * 0.189)) as u8
            image_data[idx * 4 + 1] = ((r * 0.349) + (g * 0.686) + (b * 0.168)) as u8
            image_data[idx * 4 + 2] = ((r * 0.272) + (g * 0.534) + (b * 0.131)) as u8
            idx = idx + 1
        }
        return Result.Ok(())
    }

    fn get_filter_name(self: view<SepiaFilter>) -> StableStr {
        return StableStr.from_literal("SepiaTone")
    }
}

@component_manifest {
    id: "org.axiom.filter.sepia",
    version: "1.0.0",
    capabilities: [
        Capability.HeapAllocation,
    ],
}

@plugin_export
pub extern "C" fn axiom_component_entry(
    host_ctx: *const ComponentHostContext,
    out_desc: *mut *const ComponentDescriptor
) -> u32 {
    unsafe {
        *out_desc = &SEPIA_DESCRIPTOR
    }
    return 0
}
```

---

### `AXS-COMP-052` — Canonical Examples: Cross-Boundary Ownership & Generational Handles

```axiom
// Positive Example: Generational handle usage across component boundary

package examples.renderer_host

import std.component.loader.ComponentHost
import std.component.loader.Component
import std.component.handle.ComponentHandle

pub fn main() -> i32 {
    let mut host = ComponentHost.new(CapabilityMask.all())
    let comp_res = host.load_by_id("com.acme.gpu_renderer", "^1.0.0")
    let comp = comp_res.unwrap()

    let renderer = comp.acquire_interface<GpuRenderer>().unwrap()

    // Create a GPU texture resource: returns generational ComponentHandle<Texture>
    let tex_res = renderer.create_texture(1920, 1080, TextureFormat.Rgba8)
    let tex_handle = tex_res.unwrap()

    // Pass handle across boundary safely
    renderer.bind_texture(tex_handle, 0)
    renderer.render_scene()

    // Destroy texture resource
    renderer.destroy_texture(tex_handle)

    // Access after destruction: detects stale generation and returns error (AXS-COMP-022)
    let bad_call = renderer.bind_texture(tex_handle, 0)
    assert(bad_call.is_err())

    comp.unload().unwrap()
    return 0
}
```

---

### `AXS-COMP-053` — Canonical Examples: Hot-Reload & State Migration

```axiom
// Positive Example: Schema migration from v1 to v2 during live hot-reload

package examples.counter_plugin

// Version 1 State
@hot_reload_state(schema_version = 1)
pub struct CounterStateV1 {
    pub count: u32,
}

// Version 2 State (Adds total_resets field)
@hot_reload_state(schema_version = 2)
pub struct CounterStateV2 {
    pub count: u32,
    pub total_resets: u32,
}

@hot_reload_migration(from_version = 1, to_version = 2)
pub fn migrate_counter_state(
    old_state: view<CounterStateV1>
) -> Result<CounterStateV2, MigrationError> {
    return Result.Ok(CounterStateV2 {
        count: old_state.count,
        total_resets: 0, // Deterministic initialization for new field
    })
}
```

---

### `AXS-COMP-054` — Canonical Negative Examples: Boundary Violation Rejection

```axiom
// Negative Example 1: Raw pointer escape across safe @component_interface (AXS-COMP-020)
@component_interface(version = "1.0.0")
pub trait BadInterface {
    // REJECTED: AX_COMP_RAW_POINTER_ESCAPE (raw pointer *mut u8 in safe component interface)
    fn process_raw(data: *mut u8, len: usize) -> bool
}

// Negative Example 2: Missing originating allocator on cross-boundary owned buffer (AXS-COMP-021)
@component_interface(version = "1.0.0")
pub trait BadAllocationInterface {
    // REJECTED: AX_COMP_CROSS_ALLOCATOR_VIOLATION (Array<u8> lacks originating allocator vtable)
    fn produce_buffer() -> Array<u8>
}
```

---

### `AXS-COMP-055` — Conformance Suite Coverage & Invariants Mapping

Compliance with `SPEC-115` is verified by the conformance test suite `tests/conformance/p20/e20_7_dynamic_components_hot_reload` (`T873`), validating the three canonical invariants:

| Invariant | Title | Verified By | Since |
|---|---|---|---|
| `INV-COMP-001` | `@component_interface` & `@plugin_export` boundary verification, cross-boundary ownership/allocator isolation (`ComponentBox<T>`, generational `ComponentHandle<T>`), and embedded `.axcomp` manifest emission | `tests/run/component_interface` | `T871` |
| `INV-COMP-002` | `std.component` dynamic plugin loader, load-time ABI/capability negotiation, generational handle tables, epoch lease safety guards, and transactional hot-reload runtime | `tests/run/component_hot_reload` | `T872` |
| `INV-COMP-003` | End-to-end E20.7 dynamic components, plugin discovery, capability isolation, and hot-reload state migration conformance suite | `tests/conformance/p20/e20_7_dynamic_components_hot_reload` | `T873` |

---

## Sources

- `0104 (§20–§22, §54 AABI-41..70)`: Dynamic trait boundaries, plugin ABI, function tables, allocator boundaries, and ABI invariants.
- `tasks/0583 (§324.6, §324.21, BOOTSTRAP-324)`: Binary compatibility engine, extensible struct headers, dynamic linking.
- `tasks/0584 (§325.1–§325.32, BOOTSTRAP-325)`: Axiom dynamic linking, plugin discovery, hot-reload, component contract, lifecycle, capability boundaries, allocator boundaries, epoch leases, state migration, and typed symbol resolution.
- `tasks/0739 (§493.1–§493.25, BOOTSTRAP-493)`: Precompiled package distribution, verified MIR templates, ABI verification gates.
- `tasks/0856 (§1–§45, §119–§134, §351, BOOTSTRAP-623)`: Native application plugin, extension, module, hot-reload, package discovery, dependency isolation, quiescence, transactional rollback, capability attenuation, and extension runtime.
- `spec/SPEC-114-abi-stability-versioning-binary-compat.md`: Three ABI tiers, Stable Axiom ABI type system, `AbiFingerprint` calculation, symbol versioning, dynamic linker fallback, `axiomc abi-check`.
- `spec/SPEC-89-artifact-library-matrix.md`: Dynamic library matrix, PE `.dll`, ELF `.so`, Mach-O `.dylib`, WASM reactor, section layout, and dynamic symbol export control.
- `spec/requirements/CATALOG.md`: `REQ-ECO-8734` (dynamic components, plugins, hot-reloading, safe dependency isolation across module boundaries).
