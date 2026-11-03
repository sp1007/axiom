# SPEC-53 — Canonical Safety Profiles, Capability-Based OS Authority, Secure Memory (`Secret<T>`) & Constant-Time Execution (`@constant_time`) Specification

Status: draft (T516, 2026-11-03)
Owner: axiom-architect
Consolidates: `specs/0124 (§1)`; `specs/0129 (§63)`; `specs/0177 (§1–28)`; `tasks/0342 (§1–100, ASEC-20..100)`; `tasks/0420 (§70, ASEC-31..33, ASEC-54..56)`; `tasks/0449 (§1–33, ASEC-20..44)`; `tasks/0451 (§192.39, AFFI-46..47)`; `tasks/0461 (§202.27–29, ANET-27..29)`; `tasks/0462 (§203.23–31, ASTORE-23..31)`; `tasks/0464 (§205.9, ATIME-32..33)`; `tasks/0465 (§206.17–18, ANET2-35..36)`; `tasks/0466 (§207.12, ADATA-34..35)`; `tasks/0467 (§208.1–100, ASEC2-20..75)`; `tasks/0703 (§445.1–200)`; `spec/SPEC-03-core-semantics.md`; `spec/SPEC-04-core-extensibility.md`; `spec/SPEC-10-ownership.md`; `spec/SPEC-11-capability.md`; `spec/SPEC-12-drop.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-51-raw-memory-volatile-mmio-layout.md`; `spec/SPEC-52-freestanding-runtime-composition.md`; `spec/SPEC-70-optir-ssa-memoryssa.md`.
Covers: `REQ-CAP-123`, `REQ-FFI-117`, `REQ-CAP-131`, `REQ-CAP-010` (and specifies the E13.4 contract for `T517`–`T520`: `REQ-ABI-046`, `REQ-FFI-124`, `REQ-CAP-135`, `REQ-CAP-136`, `REQ-CAP-137`, `REQ-CAP-138`, `REQ-CAP-139`, `REQ-CAP-141`, `REQ-OPT-353`).
Consumers: `compiler/driver/`, `compiler/hir/`, `compiler/sema/`, `compiler/types/`, `compiler/own/`, `compiler/mir/`, `compiler/verify/`, `compiler/opt/`, `compiler/lir/`, `compiler/target/x64/`, `std/security/`, `T517`–`T520`.

## Tóm tắt

Tài liệu `SPEC-53` chuẩn hóa kiến trúc hồ sơ an toàn (`--safety-profile safe|sandbox|system`), chính sách kiểm soát `unsafe` mức mô-đun/gói (`@forbid_unsafe`, `@allow_unsafe`), mô hình phân quyền tài nguyên hệ điều hành dựa trên capability (`FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap`), ranh giới FFI không tin cậy, bộ nhớ mật mã tự xóa (`Secret<T>`, `Zeroize`, `zeroize_memory`, `black_box`), và hợp đồng thực thi thời gian hằng (`@constant_time`, `@secret`, `ct_eq`, `ct_select`) cho phân hệ `E13.4` (Phase `P13`):
- **Phân tách ba tầng: An toàn bộ nhớ (`Memory Safety`), Quyền tài nguyên (`Resource Authority`), và Độ tin cậy nguồn (`Source Trust`) (`tasks/0342 ASEC-20..30`, `tasks/0449 ASEC-20..25`, `tasks/0703 §445.1–4`)**: Code Axiom an toàn (`safe`) bảo đảm không có UB bộ nhớ hay data race nhưng không tự động hàm ý có quyền truy cập hệ điều hành, và ngược lại khối `unsafe` chỉ mở khóa nghĩa vụ chứng minh mức máy chứ không tự động cấp quyền hệ điều hành hay vượt thoát sandbox (`ASEC-22`, `ASEC-40`).
- **Ba hồ sơ an toàn (`--safety-profile safe|sandbox|system`) và thuộc tính `@forbid_unsafe` / `@allow_unsafe` (`T517`)**: Hồ sơ `safe` và `sandbox` (hoặc mô-đun gắn `@forbid_unsafe`) cấm toàn bộ khối `unsafe`, khai báo `unsafe fn`, `unsafe trait`/`unsafe impl`, giải tham chiếu con trỏ thô, khối `extern`, `static mut`, và `@addr`/`@at` với mã chẩn đoán `AX_SEC_UNSAFE_FORBIDDEN`. Chính sách `@forbid_unsafe` có tính đơn điệu: mô-đun con không thể dùng `@allow_unsafe` để mở lại `unsafe` khi gói hoặc mô-đun cha đã khóa (`AX_SEC_CONFLICTING_SAFETY_POLICY`).
- **Phân biệt capability bộ nhớ (`view<T>`/`mut_view<T>`) với capability quyền hệ điều hành (`FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap`) và cấm quyền ngầm (`Ambient Authority`) trong `sandbox`/`comptime` (`REQ-CAP-010`, `REQ-CAP-123`, `REQ-CAP-131`, `REQ-FFI-117`, `T517`, `T519`)**: Mọi capability không sở hữu (`view<T>`, `mut_view<T>`) chỉ được phép truy cập dữ liệu thuộc về một chủ sở hữu đang tồn tại (`REQ-CAP-010`). Con trỏ thô (`*const T`, `*mut T`), địa chỉ số nguyên (`usize`), và địa chỉ bộ nhớ tuyến tính WASM (`REQ-FFI-124`) không mang provenance hay quyền sở hữu và không bao giờ tự chuyển đổi ngầm thành capability an toàn (`REQ-CAP-123`, `AX_SEC_CAPABILITY_FORGERY`). Trong hồ sơ `sandbox` và miền `comptime`, mọi thao tác I/O, mạng, biến môi trường, tiến trình, hoặc đồng hồ hệ thống không truyền tường minh token quyền (`FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap`) đều bị từ chối tại thời điểm biên dịch (`AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN`), đồng thời quyền `comptime` không bao giờ biến thành quyền `runtime` và ngược lại (`REQ-CAP-131`).
- **Bộ nhớ bí mật tự xóa (`Secret<T>`) và hợp đồng thời gian hằng (`@constant_time`) (`tasks/0467 ASEC2-20..75`, `REQ-OPT-353`, `T518`, `T519`)**: `Secret<T>` cấm `Copy` ngầm (`AX_SEC_SECRET_IMPLICIT_COPY`), ẩn nội dung khi định dạng `Debug`/`Display` (`"<secret>"`), và bắt buộc xóa bộ nhớ về `0` khi hủy (`Drop`) thông qua rào cản tối ưu hóa `zeroize_memory` không thể bị loại bỏ bởi Dead-Store Elimination (`REQ-OPT-353`). Trình kiểm định `@constant_time` trên MIR/LIR theo dõi lan truyền nhãn bí mật (`SECRET` taint) và từ chối mọi nhánh điều kiện (`if`/`match`/`while`), truy cập mảng/bộ nhớ phụ thuộc bí mật, hoặc lệnh máy có độ trễ biến thiên (`DIV`/`IDIV`/`REM`) trên dữ liệu bí mật (`AX_SEC_TIMING_LEAK`), đồng thời hạ cấp `ct_select` xuống lệnh `CMOVcc` / mặt nạ bit không rẽ nhánh trên x86-64.

---

## 1. Safety Profiles, `@forbid_unsafe` Policy & Trust Boundaries (`AXS-SEC-001`..`005`)

### AXS-SEC-001 — Orthogonal Security Layers: Language Safety, Resource Authority & Source Trust (`tasks/0342 ASEC-20..41`, `tasks/0449 ASEC-20..38`, `tasks/0703 §445.1–10`)

1. **Three Independent Dimensions**:
   - **Language Safety (`SAFE` vs `UNSAFE`)**: Statically verified memory, type, ownership, capability (`view<T>` / `mut_view<T>`), initialization, and concurrency invariants (`SPEC-50 AXS-UNS-001`).
   - **Resource Authority (`Capability Security`)**: What external operating-system, filesystem, network, environment, process, clock, or device operations a module or execution context is authorized to perform (`tasks/0342 §1–6`, `ASEC-23..29`).
   - **Source & Boundary Trust (`Trusted` vs `Untrusted`)**: Whether a package, foreign library (`FFI`), build script, plugin, or runtime input is trusted by the build/deployment policy (`tasks/0449 §1–4`, `ASEC-20..21`).
2. **Non-Equivalence Invariants (`ASEC-20..22`, `ASEC-40..41`)**:
   - Memory-safe code is not automatically sandboxed or free of logic/authority vulnerabilities (`ASEC-20`, `ASEC-22`).
   - Conversely, entering an `unsafe` block or `unsafe fn` only unlocks machine-level proof obligations (`SPEC-50 AXS-UNS-002`); `unsafe` NEVER grants operating-system privileges, never fabricates resource capability tokens, and never bypasses compiler `comptime` or runtime `sandbox` restrictions (`tasks/0342 ASEC-33, ASEC-40..41, ASEC-44`, `tasks/0449 ASEC-22`).
   - Security profiles constrain allowed language constructs and authority capabilities without forking Core language semantics (`tasks/0342 ASEC-78..79`, `tasks/0449 ASEC-36`, `tasks/0703 §445.123`).

### AXS-SEC-002 — Compilation Safety Profiles (`--safety-profile safe|sandbox|system`, `T517`)

Orthogonally to the target execution profile (`--profile hosted|freestanding|kernel|system` in `SPEC-52 AXS-FRE-002`), the compiler session carries a `SafetyProfile` selected via `--safety-profile <mode>` on the CLI or `safety_profile = "<mode>"` under `[package]` / `[security]` in `axiom.toml`. Any value outside `{safe, sandbox, system}` is rejected by the driver with `AX_DRIVER_INVALID_SAFETY_PROFILE` (exit code `2`):

| `--safety-profile` | `unsafe` / Raw Ptr Deref / `extern` / `@at` | Ambient OS I/O (`File.open(path)`, `TcpStream.connect(addr)`, `env.get`) | Capability-Token OS I/O (`FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap`) | Primary Use Case |
|---|---|---|---|---|
| `system` (default for `--profile kernel\|freestanding\|system`, and default in `hosted` unless restricted) | Allowed (governed by local `@forbid_unsafe` / `@allow_unsafe`) | Allowed in `hosted` (`SPEC-52`); forbidden in `freestanding`/`kernel` | Allowed | Kernels, drivers, FFI bindings, `std` internals, general systems & hosted apps |
| `safe` | **Forbidden** across user modules (`AX_SEC_UNSAFE_FORBIDDEN`) | Allowed in `hosted` via safe `std` APIs | Allowed | Application code, business logic, safe libraries requiring zero `unsafe` |
| `sandbox` | **Forbidden** across user modules (`AX_SEC_UNSAFE_FORBIDDEN`) | **Forbidden** (`AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN`, `REQ-CAP-131`) | **Required** (all external OS authority must pass explicit capability tokens) | Untrusted plugins, AI-generated code, hermetic tools, multi-tenant sandboxes |

[tasks/0342 §6, §86–93, ASEC-28..29, ASEC-78..82; tasks/0449 §6–7, §24–27, ASEC-23..27; tasks/0703 §445.190–196]

### AXS-SEC-003 — Module & Package Policy Attributes (`@forbid_unsafe`, `@allow_unsafe`, `T517`)

1. **Attribute Placement & Scope**:
   - `@forbid_unsafe` and `@allow_unsafe` may be attached to a `module` declaration (`@forbid_unsafe module app.auth`) or to an item (`fn`, `struct`, `enum`, `trait`, `impl`). Package-wide policy is configured via `forbid_unsafe = true` in `axiom.toml` or `--safety-profile safe|sandbox`.
2. **Constructs Forbidden Under `@forbid_unsafe` (`AX_SEC_UNSAFE_FORBIDDEN`)**:
   - Within the lexical scope of `@forbid_unsafe` or when `--safety-profile safe` / `--safety-profile sandbox` is active for the compilation unit, `compiler/sema/` rejects every occurrence of:
     1. `unsafe { ... }` blocks (`data.construct = "unsafe_block"`);
     2. `unsafe fn` declarations (`data.construct = "unsafe_fn"`);
     3. `unsafe trait` declarations and `unsafe impl` blocks (`data.construct = "unsafe_trait"` / `"unsafe_impl"`);
     4. Raw-pointer dereferences (`*p`, `p->field`, `(*p)[i]`), raw-pointer address-taking (`address_of`, `address_of_mut`), and pointer offset arithmetic (`ptr_add`, `ptr_sub`, `p + n`) (`data.construct = "raw_ptr_op"`);
     5. Foreign `extern "<abi>" { ... }` blocks and `@export` / `@no_mangle` foreign ABI declarations (`data.construct = "extern_block"`);
     6. Mutable global `static mut` declarations or accesses (`data.construct = "static_mut"`);
     7. Fixed or dynamic hardware address placement `@addr(<expr>)` / `@at(<expr>)` and `@naked` functions (`data.construct = "fixed_addr"` / `"naked_fn"`).
   - Safe calls to verified `std` APIs (whose internal implementation in `std/` encapsulates `unsafe` behind a safe signature per `tasks/0703 §445.160–162`) remain fully permitted in `@forbid_unsafe` user modules.
3. **Monotonic Non-Escalation Rule (`AX_SEC_CONFLICTING_SAFETY_POLICY`)**:
   - Security policy is monotonically restrictive (`tasks/0342 §88–89`, `ASEC-46`): if `--safety-profile safe|sandbox`, package manifest `forbid_unsafe = true`, or an enclosing module specifies `@forbid_unsafe`, an inner item or submodule annotated with `@allow_unsafe` is rejected with `AX_SEC_CONFLICTING_SAFETY_POLICY`. `@allow_unsafe` may only narrow a warning/lint policy in `--safety-profile system` when `forbid_unsafe` is not locked.

### AXS-SEC-004 — Non-Owning Capability Provenance vs Raw Pointers, Integer Addresses & WASM Linear Memory (`REQ-CAP-010`, `REQ-CAP-123`, `REQ-FFI-124`, `T517`, `T518`)

1. **Mandatory Owning Authority for Safe Capabilities (`0124 §1`, `SPEC-11 AXS-CAP-004`, `REQ-CAP-010`)**:
   - Every non-owning memory capability (`view<T>`, `mut_view<T>`, `view<[T]>`, `mut_view<[T]>`, `Str`) MUST derive its provenance from an existing, live owning authority (a stack local owner, a heap/arena owner, a static owner, or a lifetime-bounded resource handle such as `MappedRegion`, `PinnedPage`, or `IoBuf`) and is statically prevented from outliving that owner (`AX_CAP_OUTLIVES_OWNER`, `REQ-CAP-010`).
2. **No Implicit Capability Provenance on Raw Pointers or Integer Addresses (`tasks/0420 §70 ASEC-31..33`, `SPEC-50 AXS-UNS-010..011`, `REQ-CAP-123`)**:
   - Raw pointers (`*const T`, `*mut T`) and integer addresses (`usize`, `isize`, `PhysAddr`) carry **no** safe capability provenance and **no** ownership (`REQ-CAP-123`).
   - Implicitly coercing or casting `*const T`, `*mut T`, or `usize` to `view<T>`, `mut_view<T>`, `view<[T]>`, `mut_view<[T]>`, or any resource authority capability token (`FsCap`, `NetCap`, etc.) is unconditionally rejected at compile time with `AX_SEC_CAPABILITY_FORGERY` (or `AX_TYPE_MISMATCH` / `AX_TYPE_INVALID_CAST`).
   - Re-establishing a safe `view<T>` or `mut_view<T>` from a raw pointer requires an explicit `unsafe` boundary (`unsafe { view_from_raw(p) }` / `unsafe { mut_view_from_raw(p) }`, lowering to `MakeView` / `MakeMutView` per `SPEC-50 AXS-UNS-006`), which is itself forbidden under `@forbid_unsafe` and `--safety-profile safe|sandbox` (`AXS-SEC-003`).
3. **WASM Linear-Memory & Cross-Module Shared Memory Isolation (`tasks/0451 §192.39 AFFI-46..47`, `REQ-FFI-124`, `T518`)**:
   - Numerical offsets in WebAssembly linear memory (`u32` / `usize` offsets into `@addr_space(10)` WASM linear memory) do NOT automatically acquire safe Axiom pointer provenance (`REQ-FFI-124`) and must be bounds- and alignment-validated before constructing a scoped `view`/`mut_view`.
   - Cross-module or host-shared linear memory regions never implicitly satisfy `Send`, `Share`, or zero-copy serialization safety (`REQ-FFI-124`); concurrent access across host/guest boundaries requires explicit `Atomic<T>` synchronization or verified exclusive host-loan handles.

### AXS-SEC-005 — Untrusted FFI Boundaries, Conservative Provenance & Target-Specific Calling Conventions (`REQ-FFI-117`, `REQ-ABI-046`, `T516`, `T518`)

1. **FFI as an Explicit Untrusted Boundary (`tasks/0342 ASEC-58..64`, `tasks/0420 §70 ASEC-54..56`, `SPEC-50 AXS-UNS-030..036`, `REQ-FFI-117`)**:
   - Every `extern "<abi>"` function call and foreign callback boundary is an explicit **untrusted boundary** (`REQ-FFI-117`).
   - Unless an explicit, compiler-verified contract attribute (`@ffi_pure`, `@ffi_no_escape`, `@constant_time` on a verified intrinsic) is present, the compiler and optimizer (`SPEC-70`, `SPEC-71`) MUST conservatively assume that a foreign function call:
     1. May read and clobber any memory reachable through raw pointers or exposed addresses (`MemoryEffect.UnknownReadWrite`);
     2. May retain or alias raw pointers passed to it (whilst passing a safe `view<T>` / `mut_view<T>` across FFI is forbidden unless lowered to a scoped raw pointer whose lifetime does not escape the call);
     3. Returns raw pointers with `UntrustedForeign` provenance that have no proven alignment, initialization, bounds, or liveness until explicitly validated inside `unsafe`;
     4. Is **not** constant-time and therefore cannot be called on `Secret<T>` / `SECRET`-tainted operands inside a `@constant_time` context (`AX_SEC_TIMING_LEAK`, `tasks/0467 ASEC2-53`).
2. **Target-Specific Calling Conventions (`0129 §63`, `SPEC-50 AXS-UNS-032`, `REQ-ABI-046`, `T518`)**:
   - In addition to `"axiom"`, `"C"`, `"system"`, and `"interrupt"` (`SPEC-52 AXS-FRE-015`), the ABI table in `TargetDesc` supports target-specific calling convention strings when required by the target platform (`"win64"`, `"sysv64"`, `"stdcall"`, `"fastcall"`, `"vectorcall"`, `"aapcs"`, `"wasm"`, `REQ-ABI-046`). Calling conventions rejected on the active target triple emit `AX_FFI_UNKNOWN_ABI`.

---

## 2. Capability-Based OS Resource Authority, Ambient-Authority Ban & Zero-Copy Lifetime Guards (`AXS-SEC-010`..`014`)

### AXS-SEC-010 — Resource Authority Capabilities vs Memory Access Capabilities (`tasks/0342 ASEC-23..29, ASEC-52..57`, `tasks/0449 ASEC-23, §30`, `T517`, `T519`)

1. **Fundamental Distinction (`ASEC-23`, `ASEC-25..26`, `ASEC2-47`)**:
   - **Memory Access Capabilities (`view<T>`, `mut_view<T>`)**: Fine-grained, zero-cost compile-time capabilities granting read or exclusive read-write access to in-memory places owned by a live value (`SPEC-11 AXS-CAP-001..009`, `REQ-CAP-010`).
   - **Resource Authority Capabilities (`FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap`)**: Explicit, unforgeable value tokens in `std.security` (`std/security/cap.ax`) representing delegated authority to interact with external operating-system resources.
2. **Canonical Authority Token Types (`std.security`)**:
   ```axiom
   pub struct FsCap {
       root_path: String,
       perm: u32, // FS_PERM_READ = 1, FS_PERM_WRITE = 2, FS_PERM_CREATE = 4
   }

   pub struct NetCap {
       allowed_host: String,
       allowed_port: u16, // 0 = any port allowed by policy
       perm: u32,         // NET_PERM_CONNECT = 1, NET_PERM_BIND = 2
   }

   pub struct EnvCap {
       allowed_prefix: String,
       allow_write: bool,
   }

   pub struct ProcessCap {
       allowed_program: String,
   }

   pub struct ClockCap {
       allow_wall_clock: bool,
       allow_monotonic: bool,
   }
   ```
3. **Unforgeability & Ownership Discipline (`ASEC-52..57`, `REQ-CAP-123`)**:
   - All fields of `FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, and `ClockCap` are module-private to `std.security`. User code outside `std.security` cannot construct an authority token via a struct literal (`AX_NAME_PRIVATE_FIELD`) or cast a raw integer/handle into an authority token (`AX_SEC_CAPABILITY_FORGERY`, `REQ-CAP-123`).
   - Root authority tokens are obtained solely from the root environment entry point (`std.security.RootCaps` or `std.os.root_fs_cap()` in non-`sandbox` profiles, or injected by the host harness into `fn main(caps: SandboxCaps)`) and passed down the call graph as ordinary owned values or `view<FsCap>` / `view<NetCap>` capabilities (`ASEC-56..57`).
   - Dual API surface (`tasks/0342 §4–5`, `ASEC-28..29`): Hosted applications in `--safety-profile system` or `--safety-profile safe` may call convenient ambient APIs (`File.open(path)`), whereas capability-explicit APIs (`File.open_with(cap: view<FsCap>, rel_path: Str)`) work in **all** hosted profiles and are mandatory in `--safety-profile sandbox`.

### AXS-SEC-011 — Prohibition of Ambient OS Authority in `sandbox` and `comptime` Profiles & Comptime/Runtime Isolation (`REQ-CAP-131`, `T517`)

1. **Ambient-Authority Ban in `--safety-profile sandbox` (`REQ-CAP-131`, `tasks/0342 ASEC-29, ASEC-43..45`, `tasks/0449 ASEC-23..25`)**:
   - Under `--safety-profile sandbox`, any direct call to an ambient OS API that accesses the filesystem, network, process environment, child process execution, or non-deterministic wall clock without an explicit authority capability token parameter (`FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap`) — including `std.fs.File.open`, `std.fs.read_to_string`, `std.fs.write`, `std.net.TcpStream.connect`, `std.net.TcpListener.bind`, `std.net.UdpSocket.bind`, `std.env.get`, `std.env.args`, `std.process.Command.spawn`, `std.process.exit`, and direct `host.file_*` / `host.net_*` / `host.env_*` / `host.process_*` intrinsics outside `std.security` — is rejected at compile time by `compiler/sema/` with `AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN` (`data.operation`, `data.required_cap`, `data.profile = "sandbox"`).
2. **Ambient-Authority Ban in `comptime` Evaluation (`REQ-CAP-131`, `tasks/0342 ASEC-43..45, ASEC-87, ASEC-90`, `tasks/0449 ASEC-24..25`)**:
   - Compile-time evaluation (`const` initializers, `comptime` functions/blocks) executes inside a hermetic compiler sandbox (`ASEC-43..44`, `ASEC-87`). Any attempt during `comptime` evaluation to invoke ambient OS filesystem, network, subprocess, environment, or wall-clock operations is rejected at compile time with `AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN` (`data.profile = "comptime"`).
3. **Strict Separation Between `comptime` Authority and `runtime` Authority (`tasks/0449 §33 ASEC-24, ASEC-25`, `REQ-CAP-131`)**:
   - **Comptime authority NEVER becomes runtime authority (`ASEC-24`)**: A capability token or resource handle available to the build system or `comptime` context cannot be serialized, lifted, or embedded as a live runtime `FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap`, or OS handle in the emitted binary (`AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN`, `data.reason = "comptime_to_runtime_authority"`).
   - **Runtime authority NEVER becomes comptime authority (`ASEC-25`)**: Declaring or accepting a runtime capability parameter (`cap: view<FsCap>`) in a function does not grant the compiler's `comptime` evaluator permission to access the host OS during compilation (`AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN`, `data.reason = "runtime_to_comptime_authority"`).

### AXS-SEC-012 — Capability Attenuation & Path/Address Confinement (`std.security`, `T519`)

1. **Monotonic Attenuation (`tasks/0342 §52–56`, `T519`)**:
   - An authority capability token may be **attenuated** (restricted to a strictly smaller subset of paths, hosts/ports, keys, or permissions) to produce a derived token, but can never amplify its permissions beyond the parent token:
     - `FsCap.attenuate_subpath(self: view<FsCap>, sub_dir: Str, perm_mask: u32) -> Result<FsCap, SecurityError>`: resolves `sub_dir` relative to `self.root_path`, rejects any path containing `..` traversal, leading `/` or `\`, drive prefixes (`C:`), or NUL bytes with `SecurityError.PathTraversalDenied`, and masks permissions to `self.perm & perm_mask`.
     - `NetCap.attenuate_endpoint(self: view<NetCap>, host: Str, port: u16, perm_mask: u32) -> Result<NetCap, SecurityError>`: restricts connection/bind authority to `host:port` if permitted by `self` and masks `perm` to `self.perm & perm_mask`.
     - `EnvCap.attenuate_prefix(self: view<EnvCap>, prefix: Str) -> Result<EnvCap, SecurityError>`: narrows allowed environment variable lookup to keys starting with `prefix` (requiring `prefix.starts_with(self.allowed_prefix)`).

### AXS-SEC-013 — Zero-Copy I/O Scatter/Gather Non-Overlap, Memory Mapping, Buffer-Pool Pinning & Timer Callback Lifetimes (`REQ-CAP-135`, `REQ-CAP-136`, `REQ-CAP-137`, `REQ-CAP-138`, `REQ-CAP-139`, `T519`, `T520`)

1. **Zero-Copy Network/Storage I/O & Scatter/Gather Non-Overlap (`tasks/0461 ANET-27..29`, `tasks/0465 ANET2-35..36`, `REQ-CAP-135`, `REQ-CAP-139`)**:
   - Zero-copy views (`PacketView`, `IoSlice`, `IoSliceMut`) borrowed from a network or I/O buffer (`NetBuffer`, `IoBuf`) carry capability provenance tied to the backing buffer owner and MUST NOT outlive the backing storage (`AX_CAP_OUTLIVES_OWNER`, `REQ-CAP-139`).
   - Scatter/gather read (`read_vectored(bufs: mut_view<[IoSliceMut]>)`) and write (`write_vectored(bufs: view<[IoSlice]>)`) operations preserve buffer ownership semantics without silent reallocation or ownership transfer (`REQ-CAP-135`) and enforce **pairwise disjointness** across all mutable segment slices (`REQ-CAP-135`, `REQ-CAP-139`): constructing or submitting two `IoSliceMut` segments that overlap the same backing memory is rejected statically by the region checker (`AX_CAP_CONFLICT_MUT`) or dynamically at `IoVec` construction (`AX_CAP_IO_BUFFER_OVERLAP` / `SecurityError.OverlappingIoSegments`).
2. **Memory-Mapped Region Ownership & Exclusive Write Capability (`tasks/0462 ASTORE-23..25`, `REQ-CAP-136`)**:
   - `std.security.MappedRegion` (and `std.fs.MemoryMap`) owns an OS file/anonymous mapping and unmaps it deterministically in `impl Drop`.
   - Borrowing `map.as_view() -> view<[u8]>` or `map.as_mut_view() -> mut_view<[u8]>` binds the slice capability's provenance to the `MappedRegion` owner: the view cannot outlive `map` (`AX_CAP_OUTLIVES_OWNER`), `map` cannot be unmapped/moved/dropped while any view is live, and writable mappings enforce Axiom's single-writer (`mut_view`) exclusivity rule (`AX_CAP_CONFLICT_MUT`, `REQ-CAP-136`).
3. **Database Page Buffer-Pool Pin Lifetimes (`tasks/0462 ASTORE-29..31`, `REQ-CAP-137`, `T520`)**:
   - In page-cached storage (`BufferPool`, `PagePin<T>`), acquiring a page returns an RAII `PagePin<T>` guard whose `Drop` unpins the page. Any `view<T>` or `mut_view<T>` into page contents is borrowed from the `PagePin<T>` owner (`pin.page_view() -> view<T>`, `pin.page_mut_view() -> mut_view<T>`):
     - A page view cannot outlive its `PagePin<T>` (`AX_CAP_OUTLIVES_OWNER`), and `BufferPool.evict(...)` cannot invalidate or evict a page while its `PagePin<T>` (or any capability borrowed from it) is live (`REQ-CAP-137`).
4. **Timer Cancellation & Callback Capture Lifetime Safety (`tasks/0464 ATIME-32..33`, `REQ-CAP-138`, `T519`)**:
   - Registering a timer callback requires captured values to be owned (`move` capture satisfying `Send`) or scoped to a structured `TimerScope` that cancels and drains all pending timers before exiting scope, guaranteeing that timer callbacks never outlive captured capabilities or resources and that timer cancellation runs `Drop` on captured resources deterministically (`REQ-CAP-138`).

### AXS-SEC-014 — Compiler-Proven Zero-Copy Deserialization Contract (`REQ-CAP-141`, `tasks/0466 ADATA-34..35`, `T518`)

1. **Zero-Copy Decode Preconditions (`REQ-CAP-141`)**:
   - Constructing a borrowed typed value `view<T>` directly over an input byte slice `buf: view<[u8]>` via zero-copy deserialization (`std.security.zero_copy_decode<T>(buf: view<[u8]>) -> Result<view<T>, DecodeError>`) is permitted in safe code **if and only if**:
     1. **Representation Compatibility (`ZeroCopyPod` / `@repr(C)`)**: `T` is a fixed-layout `@repr(C)` or primitive type whose every bit pattern is valid (no `bool`, `char`, `enum` with invalid tags, capabilities, pointers, or padding sensitivity; `SPEC-50 AXS-UNS-013`);
     2. **Proven Bounds & Alignment**: `buf.len() >= size_of<T>()` and `(buf.as_ptr() as usize) % align_of<T>() == 0`;
     3. **Lifetime & Provenance Preservation**: The returned `view<T>` inherits the exact capability provenance and owner-outlives lifetime of `buf` (`REQ-CAP-141`), so `buf`'s backing owner cannot be mutated, reallocated, or dropped while the decoded `view<T>` is live (`AX_CAP_OUTLIVES_OWNER`).
   - Attempting zero-copy deserialization on a type `T` that lacks proven layout/bit-representation compatibility is rejected at compile time with `AX_CAP_ZERO_COPY_DESERIALIZE_UNPROVEN`.

---

## 3. Secure Memory (`Secret<T>`), Non-Elidable Zeroization & Constant-Time Execution (`@constant_time`) (`AXS-SEC-020`..`024`)

### AXS-SEC-020 — `Secret<T>` & `@secret` Type Contract: No Implicit `Copy`, Redacted Formatting & Explicit Exposure (`tasks/0467 §208.5–8, ASEC2-21..24, ASEC2-57..58`, `T518`, `T519`)

1. **`Secret<T>` Wrapper & `@secret` Attribute (`std/security/secret.ax`)**:
   - `std.security.Secret<T: Zeroize>` encapsulates sensitive cryptographic or authentication material (keys, nonces, plaintext secrets, intermediate state):
     ```axiom
     @secret
     pub struct Secret<T> {
         inner: T,
     }
     ```
   - Applying `@secret` to a struct or parameter marks its values with security classification `SecClass.Secret` in HIR/MIR (`tasks/0467 ASEC2-23`).
2. **Non-`Copy` & Explicit Cloning (`tasks/0467 §208.5, §208.7, ASEC2-22`, `AX_SEC_SECRET_IMPLICIT_COPY`)**:
   - `Secret<T>` is **never `Copy`**, even when the inner type `T` (`u64`, `[32]u8`) is `Copy`. Attempting to implicitly copy a `Secret<T>` binding after move emits `AX_MOVE_USE_AFTER_MOVE` / `AX_SEC_SECRET_IMPLICIT_COPY`, preventing accidental duplication of keys across stack frames or registers. Duplication requires an explicit `secret.clone_secret()` call.
3. **Redacted Formatting, Diagnostics & Controlled Access (`tasks/0467 ASEC2-24, ASEC2-57..58`, `AX_SEC_SECRET_EXPOSURE`)**:
   - `Display` and `Debug` implementations on `Secret<T>` unconditionally emit the literal string `"<secret>"` and never inspect `self.inner`.
   - Compiler diagnostics, MIR/const-eval trace dumps, and semantic query outputs redact the contents of `@secret` / `Secret<T>` values (`ASEC2-57..58`).
   - Accessing the raw inner value requires calling `secret.expose_secret() -> view<T>` or `secret.expose_secret_mut() -> mut_view<T>`, whose return values remain tainted as `SecClass.Secret` inside `@constant_time` analysis. Passing a `Secret<T>` directly to an unannotated `extern` FFI function or public formatting sink without explicit `declassify` is rejected with `AX_SEC_SECRET_EXPOSURE`.

### AXS-SEC-021 — `Zeroize` Trait, `zeroize_memory` & `black_box` Optimization-Proof Barriers (`REQ-OPT-353`, `tasks/0467 §208.9–10, ASEC2-25`, `tasks/0703 §445.111`, `T518`, `T519`)

1. **`Zeroize` Trait & Deterministic Scrubbing on `Drop`**:
   ```axiom
   pub trait Zeroize {
       fn zeroize(self: mut_view<Self>)
   }

   impl<T: Zeroize> Drop for Secret<T> {
       fn drop(self: mut_view<Secret<T>>) {
           self.inner.zeroize()
       }
   }
   ```
   - Built-in `Zeroize` implementations are provided for all integer primitives (`u8..u128`, `i8..i128`, `usize`, `isize`), `bool`, fixed-size arrays `[N]T` (`T: Zeroize`), and slices `mut_view<[T]>`.
2. **Compiler Intrinsic `zeroize_memory(ptr: *mut u8, len: usize)` & `black_box<T>(val: T) -> T` (`REQ-OPT-353`, `SPEC-70 AXS-OPT-021`, `T518`)**:
   - `std.security.zeroize_memory(ptr, len)` (and `Secret<T>.drop`) lowers in MIR to `MirStmtKind.SecureZero { ptr, len }` (or volatile byte-fill stores followed by `compiler_fence(Ordering.SeqCst)`), and in LIR to `LIR_INST_SECURE_ZERO` / `LIR_MEM_FLAG_VOLATILE` stores.
   - **Dead-Store Elimination Prohibition (`REQ-OPT-353`, `ASEC2-25`, `INV-PIPE-008`)**: Every optimization pass in `compiler/opt/` (`SROA`, `DSE`, `DCE`, `GVN`, `CSE`, `StoreSinking`, `LTO`) and every post-RA peephole pass in `compiler/target/x64/` MUST treat `zeroize_memory` / `SecureZero` as an **observable volatile side effect**. Even when the target stack slot or heap buffer becomes dead (`StorageDead` or `dealloc`) immediately after `zeroize_memory`, the zeroing stores MUST NOT be elided, narrowed, or reordered past the deallocation boundary (`REQ-OPT-353`).
   - `std.security.black_box<T>(val: T) -> T` lowers to an opaque optimization barrier (`MirRvalue.BlackBox` / `LIR_INST_BLACK_BOX`) that forces the compiler to treat `val` as both read and modified by an unknown opaque effect without constant-folding, range-narrowing, or branch-simplifying across the barrier.

### AXS-SEC-022 — Secret Taint Lattice (`PUBLIC`, `SECRET`, `UNKNOWN`) & Explicit `declassify` (`tasks/0467 §208.16–19, ASEC2-29..31`, `T518`)

1. **Three-Point Security Taint Lattice**:
   - Inside any `@constant_time` function or block, `compiler/mir/` assigns every MIR local and temporary a security taint classification from the lattice $\text{Public} \sqsubset \text{Secret}$ (with conservatively unannotated external/unknown inputs treated as $\text{Unknown} \equiv \text{Secret}$ per `ASEC2-29`):
     $$\text{join}(\tau_1, \tau_2) = \begin{cases} \text{Public} & \text{if } \tau_1 = \text{Public} \land \tau_2 = \text{Public} \\ \text{Secret} & \text{otherwise} \end{cases}$$
   - Any value of type `Secret<T>`, any parameter/local annotated with `@secret`, or any capability `view<T>` / `mut_view<T>` borrowed from a `Secret<T>` has initial taint $\text{Secret}$.
   - Every arithmetic, bitwise, shift, cast, SIMD, or `ct_select` / `ct_eq` operation with at least one $\text{Secret}$ operand propagates $\text{Secret}$ taint to its result (`ASEC2-30`).
2. **Explicit Declassification (`std.security.declassify<T>(val: T) -> T`, `ASEC2-31`)**:
   - Secret taint is never cleared implicitly (not even by hashing or comparison). Converting a $\text{Secret}$-tainted value (such as the final boolean verdict of an authentication tag check `ct_eq_bytes(computed_tag, expected_tag)`) into a $\text{Public}$ value so the caller can branch on the authentication outcome requires an explicit call to `std.security.declassify(verdict)` (`ASEC2-31`).

### AXS-SEC-023 — `@constant_time` Verification Contract: Prohibition of Secret-Dependent Branches, Memory Indexing & Variable-Latency Instructions (`AX_SEC_TIMING_LEAK`, `tasks/0467 §208.11–15, §208.24–25, ASEC2-26..28, ASEC2-33..35, ASEC2-65..67`, `T518`)

1. **`@constant_time` Attribute Scope (`AX_SEC_INVALID_CONSTANT_TIME_ATTR`)**:
   - `@constant_time` may be attached to a `fn` declaration (`@constant_time pub fn verify_mac(...) -> bool`). Attaching `@constant_time` to an `async fn`, a non-function item (`struct`, `enum`, `static`), or an unverified `extern` declaration is rejected with `AX_SEC_INVALID_CONSTANT_TIME_ATTR`.
2. **Three Forbidden Timing-Leak Channels (`AX_SEC_TIMING_LEAK`, `T518`)**:
   - The MIR/LIR constant-time verifier (`compiler/mir/ct_verify.ax` before optimization and `compiler/lir/ct_verify.ax` after instruction selection, `ASEC2-65..66`) inspects every `@constant_time` function and rejects any operation where a $\text{Secret}$-tainted value reaches:
     1. **Secret-Dependent Control Flow (`data.leak_kind = "secret_branch"`, `ASEC2-27`)**:
        - Branching on a $\text{Secret}$ condition in `if`, `match`, `while`, short-circuit `&&` / `||`, or `?` (`MirTerminator.Branch` / `SwitchInt` with $\text{taint}(\text{cond}) == \text{Secret}$), or calling through a $\text{Secret}$-tainted function pointer (`MirTerminator.Call` with secret callee).
        - Branching on $\text{Public}$ values (such as public buffer lengths or fixed round counters `for round in 0..10`) is **permitted** (`tasks/0467 §208.15`).
     2. **Secret-Dependent Memory Addressing / Table Indexing (`data.leak_kind = "secret_mem_index"`, `ASEC2-28`)**:
        - Indexing an array or slice with a $\text{Secret}$ index (`table[secret_idx]`, `PlaceElem.Index(idx)` with $\text{taint}(\text{idx}) == \text{Secret}$), performing pointer arithmetic with a $\text{Secret}$ offset (`ptr_add(p, secret_off)`), or executing SIMD `gather`/`scatter` with a $\text{Secret}$ index vector, which would leak secret bits through CPU cache lines.
     3. **Variable-Latency Machine Instructions & Non-Constant-Time Calls (`data.leak_kind = "variable_latency_op"`, `ASEC2-33`)**:
        - Applying integer division (`/`, `DIV`/`IDIV`), remainder (`%`, `REM`), floating-point operations, or calls to functions not themselves annotated `@constant_time` when any operand/argument is $\text{Secret}$-tainted.
3. **Optimizer & Backend Preservation (`ASEC2-34..36`, `ASEC2-67`, `T518`)**:
   - No MIR, OptIR, LIR, or x86-64 machine optimization pass may convert a branchless `ct_select` / bitwise expression inside a `@constant_time` function into a conditional jump (`Jcc`), early-exit comparison (`memcmp`), or lookup table (`ASEC2-34`, `ASEC2-67`).

### AXS-SEC-024 — Constant-Time Primitives (`ct_eq`, `ct_select`, `ct_swap_if`, `ct_copy_if`) & Branchless x86-64 `CMOVcc` Lowering (`tasks/0467 §208.20–23, ASEC2-32`, `T518`, `T519`)

1. **Standard Library Primitives (`std/security/ct.ax`, `T519`)**:
   - `@constant_time pub fn ct_select_u8(mask_bool: bool, a: u8, b: u8) -> u8` (and `ct_select_u16`, `ct_select_u32`, `ct_select_u64`, `ct_select_usize`): returns `a` if `mask_bool` is `true` and `b` if `false` without branching.
   - `@constant_time pub fn ct_eq_u8(a: u8, b: u8) -> bool` (and `ct_eq_u32`, `ct_eq_u64`, `ct_eq_bytes(a: view<[u8]>, b: view<[u8]>) -> bool`): compares inputs by XOR-accumulating all bytes (`diff = diff | (a[i] ^ b[i])`) over the full slice length without early exit, returning `false` immediately only when public lengths `a.len() != b.len()` differ.
   - `@constant_time pub fn ct_swap_if_u64(cond: bool, a: mut_view<u64>, b: mut_view<u64>)` and `@constant_time pub fn ct_copy_if_bytes(cond: bool, dst: mut_view<[u8]>, src: view<[u8]>)`: conditionally swaps or copies bytes using branchless bitwise masks (`mask = 0u64.wrapping_sub(cond as u64)`).
2. **Branchless LIR & x86-64 Lowering (`LIR_INST_CT_SELECT`, `CMOVNE`, `T518`)**:
   - `ct_select` lowers in LIR to a dedicated `LIR_INST_CT_SELECT(cond, if_true, if_false)` node (or branchless mask arithmetic for 8-bit values) that `compiler/target/x64/isel.ax` lowers directly to `TEST cond, cond` followed by `CMOVNE dst, if_true` (`0F 45`), never a basic-block diamond with `JE`/`JNE`.

---

## 4. Diagnostics, Canonical Examples & Requirement Traceability (`AXS-SEC-050`..`053`)

### AXS-SEC-050 — Diagnostic Codes Owned or Referenced by `SPEC-53`

| Code | Area | Sev | Delivering Task | Condition & Normative Rule |
|---|---|---|---|---|
| `AX_DRIVER_INVALID_SAFETY_PROFILE` | `DRIVER` | `error` | `T517` | Unknown `--safety-profile <mode>` or `axiom.toml` `safety_profile` value outside `{safe, sandbox, system}` (exit code `2`; `AXS-SEC-002`). |
| `AX_SEC_UNSAFE_FORBIDDEN` | `SEC` / `UNSAFE` | `error` | `T517` | `unsafe` block, `unsafe fn`, `unsafe trait`/`unsafe impl`, raw-pointer dereference/arithmetic, `extern` block, `static mut`, or `@addr`/`@at` used under `@forbid_unsafe` or `--safety-profile safe\|sandbox` (`AXS-SEC-003`). |
| `AX_SEC_CONFLICTING_SAFETY_POLICY` | `SEC` | `error` | `T517` | `@allow_unsafe` applied inside a scope already locked by `@forbid_unsafe` or `--safety-profile safe\|sandbox`, or invalid safety policy attribute syntax (`AXS-SEC-003`). |
| `AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN` | `SEC` | `error` | `T517` | Calling an ambient OS API (`std.fs`, `std.net`, `std.env`, `std.process`, `std.time`, `host.*`) in `--safety-profile sandbox` or `comptime` without an explicit authority capability token (`FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap`), or bridging `comptime` and `runtime` authority (`REQ-CAP-131`, `AXS-SEC-011`). |
| `AX_SEC_CAPABILITY_FORGERY` | `SEC` / `CAP` | `error` | `T517` | Implicitly converting or casting a raw pointer (`*const T`, `*mut T`), integer address (`usize`), or WASM linear-memory offset into a safe capability (`view<T>`, `mut_view<T>`) or authority token (`FsCap`, `NetCap`, etc.) without an explicit `unsafe` precondition boundary (`REQ-CAP-010`, `REQ-CAP-123`, `REQ-FFI-124`, `AXS-SEC-004`). |
| `AX_SEC_TIMING_LEAK` | `SEC` | `error` | `T518` | Secret-dependent branch (`if`/`match`/`while`/`&&`/`||`), secret-dependent memory/array indexing (`arr[secret]`), variable-latency instruction (`/` `DIV`/`IDIV`, `%` `REM`), or non-`@constant_time` call on `@secret` / `Secret<T>` data inside a `@constant_time` function (`AXS-SEC-023`). |
| `AX_SEC_SECRET_IMPLICIT_COPY` | `SEC` / `MOVE` | `error` | `T518` / `T519` | Attempting to implicitly `Copy` a `Secret<T>` value instead of moving or calling `clone_secret()` (`AXS-SEC-020`). |
| `AX_SEC_SECRET_EXPOSURE` | `SEC` | `error` | `T518` / `T519` | Passing `Secret<T>` across an untrusted FFI boundary or public sink without explicit `expose_secret()` / `declassify` (`REQ-FFI-117`, `AXS-SEC-005`, `AXS-SEC-020`). |
| `AX_SEC_INVALID_CONSTANT_TIME_ATTR` | `SEC` | `error` | `T518` | `@constant_time` or `@secret` applied to an invalid item (`async fn`, `extern fn` without body, or non-zeroizable type) (`AXS-SEC-020`, `AXS-SEC-023`). |
| `AX_CAP_ZERO_COPY_DESERIALIZE_UNPROVEN` | `CAP` | `error` | `T518` | Zero-copy deserialization requested for a type `T` lacking proven bit-validity, alignment, or `@repr(C)` layout (`REQ-CAP-141`, `AXS-SEC-014`). |
| `AX_CAP_IO_BUFFER_OVERLAP` | `CAP` | `error` | `T519` | Scatter/gather I/O vector constructed with overlapping mutable buffer slices (`REQ-CAP-135`, `REQ-CAP-139`, `AXS-SEC-013`). |

### AXS-SEC-051 — Canonical Positive Examples (`=` and `.` Syntax)

```axiom
// Compiled with: axiomc check --safety-profile sandbox auth_plugin.ax
@forbid_unsafe
module demo.sandbox_crypto

use std.security.FsCap
use std.security.Secret
use std.security.ct_eq_bytes
use std.security.ct_select_u64
use std.security.declassify
use std.core.result.Result

@constant_time
pub fn verify_tag_and_select(
    secret_tag: view<Secret<[32]u8>>,
    candidate_tag: view<[32]u8>,
    key_a: u64,
    key_b: u64,
) -> bool {
    let raw_secret = secret_tag.expose_secret()
    let eq_secret = ct_eq_bytes(raw_secret.as_slice(), candidate_tag)
    let chosen = ct_select_u64(eq_secret, key_a, key_b)
    let _ = chosen
    return declassify(eq_secret)
}

pub fn read_sandboxed_config(root_cap: view<FsCap>) -> Result<FsCap, i32> {
    // Attenuate capability to read-only access under "configs/app" (AXS-SEC-012):
    match root_cap.attenuate_subpath("configs/app", 1u32) {
        Result.Ok(sub_cap) => return Result.Ok(sub_cap),
        Result.Err(_) => return Result.Err(1),
    }
}
```

### AXS-SEC-052 — Canonical Negative Examples (`=` and `.` Syntax)

```axiom
// Compiled with: axiomc check --safety-profile sandbox bad_security.ax
@forbid_unsafe
module demo.bad_security

use std.fs.File
use std.security.Secret

// ERROR [AX_SEC_UNSAFE_FORBIDDEN]: `unsafe fn` is forbidden under `@forbid_unsafe` and `--safety-profile sandbox` (AXS-SEC-003)
pub unsafe fn raw_poke(p: *mut u32) {
    *p = 1u32
}

// ERROR [AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN]: ambient OS call `File.open` is forbidden in `--safety-profile sandbox`; pass an explicit `FsCap` token (`REQ-CAP-131`, AXS-SEC-011)
pub fn open_ambient() {
    let _ = File.open("/etc/passwd")
}

// ERROR [AX_SEC_CAPABILITY_FORGERY]: integer address `usize` has no capability provenance and cannot convert to `view<u32>` (`REQ-CAP-123`, AXS-SEC-004)
pub fn forge_view(addr: usize) -> view<u32> {
    return addr as view<u32>
}

@constant_time
pub fn leaky_crypto(secret_val: view<Secret<u64>>, table: view<[256]u8>) -> u64 {
    let s = *secret_val.expose_secret()
    // ERROR [AX_SEC_TIMING_LEAK]: secret-dependent branch in `@constant_time` function (AXS-SEC-023)
    if s == 0u64 {
        return 1u64
    }
    // ERROR [AX_SEC_TIMING_LEAK]: secret-dependent array indexing leaks via cache timing (AXS-SEC-023)
    let b = table[(s & 0xFFu64) as usize]
    // ERROR [AX_SEC_TIMING_LEAK]: hardware division `/` on secret operand has variable latency (AXS-SEC-023)
    return (s / 3u64) + (b as u64)
}
```

### AXS-SEC-053 — Requirement & Task Traceability Matrix (`T516`–`T520`)

| Requirement ID | Primary Rule(s) | Delivering Tasks | Verification Coverage |
|---|---|---|---|
| `REQ-CAP-010` | `AXS-SEC-004`, `AXS-SEC-010`, `AXS-SEC-013` | `T516`, `T517`, `T520` | Non-owning capability (`view<T>`/`mut_view<T>`) requires an existing live owning authority (`tests/ui/security_profiles`, `tests/conformance/p13/e13_4_security_profiles`). |
| `REQ-CAP-123` | `AXS-SEC-004`, `AXS-SEC-010`, `AXS-SEC-050` | `T516`, `T517`, `T520` | Raw pointers and integer addresses lack capability provenance/ownership and cannot implicitly convert to safe capabilities (`AX_SEC_CAPABILITY_FORGERY`). |
| `REQ-FFI-117` | `AXS-SEC-005`, `AXS-SEC-020`, `AXS-SEC-050` | `T516` | FFI boundaries are untrusted with conservative provenance and side-effect modeling unless explicit verified contracts exist. |
| `REQ-CAP-131` | `AXS-SEC-002`, `AXS-SEC-010`, `AXS-SEC-011`, `AXS-SEC-050` | `T516`, `T517`, `T520` | External OS authority requires explicit capability policies in `sandbox`/`comptime`; `comptime` and `runtime` authority never cross (`AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN`). |
| `REQ-ABI-046` | `AXS-SEC-005` | `T518` | Target-specific calling conventions (`stdcall`, `fastcall`, `vectorcall`, `wasm`, `aapcs`) in `TargetDesc`. |
| `REQ-FFI-124` | `AXS-SEC-004` | `T518` | WASM linear-memory addresses do not automatically acquire safe pointer provenance; cross-module shared memory does not imply `Send`/`Share`/serialization safety. |
| `REQ-CAP-141` | `AXS-SEC-014`, `AXS-SEC-050` | `T518` | Zero-copy deserialization requires compiler-proven provenance, lifetime, alignment, and `@repr(C)` layout (`AX_CAP_ZERO_COPY_DESERIALIZE_UNPROVEN`). |
| `REQ-OPT-353` | `AXS-SEC-021` | `T603`, `T518`, `T519` | `zeroize_memory` and `Secret<T>` drop scrubbing are observable volatile barriers never removed by Dead-Store Elimination (`tests/lir/constant_time`). |
| `REQ-CAP-135` | `AXS-SEC-013`, `AXS-SEC-050` | `T519` | Zero-copy network I/O and scatter/gather enforce capability non-overlap (`AX_CAP_IO_BUFFER_OVERLAP`) and preserve buffer ownership. |
| `REQ-CAP-136` | `AXS-SEC-013` | `T519` | `MappedRegion` explicit ownership/lifetime; mapped views cannot outlive mapping and writable mappings obey exclusive `mut_view` rules. |
| `REQ-CAP-137` | `AXS-SEC-013` | `T520` | Database buffer-pool `PagePin<T>` lifetimes prevent page eviction while a capability view is live (`tests/conformance/p13/e13_4_security_profiles`). |
| `REQ-CAP-138` | `AXS-SEC-013` | `T519` | Timer cancellation preserves callback resource safety; callbacks never outlive captured capabilities/resources. |
| `REQ-CAP-139` | `AXS-SEC-013`, `AXS-SEC-050` | `T519` | Zero-copy views into network buffers never outlive backing storage; scatter/gather enforces segment non-overlap. |
