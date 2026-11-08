# SPEC-116 — Canonical Native SDK, Declarative `.axsdk` Sysroot Metadata, AXTOOLCHAIN Target Descriptor & Toolchain Distribution Specification

- **Status**: draft (T874, 2026-11-08)
- **Owner**: axiom-architect
- **Phase**: P20 (E20.6 — Native SDK, Declarative Sysroot Metadata, AXTOOLCHAIN Descriptor & Toolchain Distribution)
- **Rules**: `AXS-SDK-001` .. `AXS-SDK-055`
- **Covers**: `REQ-ECO-8736`, `REQ-PKG-022`
- **Consolidates**: `tasks/0605 (§1–§43, ASDK-01..30)`; `tasks/1034 (§1–§141, TOOLCHAIN-INV-01..40)`; `tasks/0661 (§5, §18–§21, §35)`; `tasks/0858 (§1–§25)`; `spec/SPEC-88-cross-compilation-platform-layer.md`; `spec/SPEC-110-build-graph-driver.md`; `spec/SPEC-111-package-manager-resolution-lockfiles.md`; `spec/SPEC-113-hermetic-builds-supply-chain-trust.md`; `spec/SPEC-114-abi-stability-versioning-binary-compat.md`.
- **Consumers**: `compiler/sdk/sysroot`, `compiler/sdk/toolchain`, `std/sdk/bundle`, `compiler/driver/sdk_cmd`, `tests/run/sdk_sysroot`, `tests/run/sdk_toolchain_cli`, `tests/conformance/p20/e20_6_sdk_toolchain_workspace`, `T875`, `T876`, `T877`.

---

## Tóm tắt

Đặc tả `SPEC-116` chuẩn hóa kiến trúc Bộ phát triển gốc (Native SDK — `.axsdk`), Siêu dữ liệu Sysroot khai báo thuần túy, Bộ mô tả chuỗi công cụ mục tiêu (`AXTOOLCHAIN`), Khóa dấu vân tay mật mã trong `axiom.lock`, và Hệ thống phân phối/quản trị tạo phẩm chuỗi công cụ kín (Hermetic Toolchain Distribution Runtime) cho ngôn ngữ Axiom (`REQ-ECO-8736`, `REQ-PKG-022`) thuộc phân hệ `E20.6` (Phase `P20`):

1. **Phân tách bản thể học giữa Trình biên dịch, Platform SDK và Sysroot (`AXS-SDK-001`..`AXS-SDK-009`)**:
   - Phân định rạch ròi ba thực thể: **Trình biên dịch** (`axiomc` — quản lý ngữ nghĩa ngôn ngữ, hệ thống kiểu, phân tích sở hữu, MIR, LIR, bộ phát mã máy), **Platform SDK** (`.axsdk` — chứa siêu dữ liệu ABI nền tảng, bảng búp syscall/nhập khẩu động, hợp đồng CRT/khởi động, và điều kiện phiên bản OS tối thiểu), và **Sysroot** (cấu trúc thư mục đĩa cách ly chứa SDK).
   - **Bảo đảm Native SDK phi ngôn ngữ C (C-Free Guarantee)**: Axiom không bao giờ biến các tệp tiêu đề C (`.h`) thành nền tảng ngữ nghĩa. Trình biên dịch không bao giờ phân tích cú pháp tiêu đề C, không bao giờ triệu gọi trình biên dịch C bên thứ ba (`cl.exe`, `gcc`, `clang`) để biên dịch mã Axiom, và không bao giờ gắn cứng (hard-code) các đường dẫn hệ thống chủ (`C:\Windows`, `C:\Program Files (x86)\Windows Kits`, `/usr/include`, `/Library/Developer/...`).
   - **Cấm ngầm định rơi về hệ thống chủ (Ambient Host Fallback Prohibition)**: Trong các cấu hình dựng kín (`--hermetic` hoặc mặc định của không gian làm việc), mọi hành vi dò tìm hoặc sử dụng đường dẫn môi trường máy chủ đều bị cấm tuyệt đối và báo lỗi `AX_SDK_HOST_FALLBACK_DENIED`.

2. **Bản kê khai `.axsdk` và Hợp đồng Sysroot khai báo thuần túy (`AXS-SDK-010`..`AXS-SDK-024`)**:
   - Tệp kê khai `sdk.toml` thuần khai báo: cấm hoàn toàn các đoạn mã lệnh hay kịch bản thực thi tùy ý trong quá trình nạp SDK.
   - Định nghĩa chính xác bộ ba đích (`target_triple`), phiên bản OS tối thiểu (`min_version`), cờ năng quyền nền tảng (`has_mmu`, `has_threads`, `has_tls`, `has_dynamic_loader`, `has_signals`).
   - Mô hình bảng búp nhập khẩu động (Dynamic Import Stubs) thay thế hoàn toàn thư viện liên kết C: định nghĩa ordinal PE DLL (`kernel32.dll`, `ntdll.dll`), bảng ký hiệu ELF (`libc.so.6`), bản mô tả văn bản Darwin (`.tbd`), và bảng búp Bionic Android mà không cần cài đặt Windows SDK, glibc headers hay Android NDK.
   - Hợp đồng khởi động CRT phân tách rõ ràng giữa cấu hình độc lập phần cứng (`freestanding` — không CRT, điểm vào `_start`) và cấu hình có hệ điều hành (`hosted` — hỗ trợ điểm vào `main`, `WinMain`, CRT init sections).
   - Ràng buộc phiên bản API tại thời điểm biên dịch thông qua thuộc tính `@available(os = ..., min_version = ...)`; ngăn chặn việc gọi API mới hơn phiên bản OS đích khi chưa có kiểm tra rẽ nhánh khả dụng (`AX_SDK_API_UNAVAILABLE`).

3. **Bộ mô tả chuỗi công cụ `AXTOOLCHAIN` trên 8 mục tiêu Tier-1 và Tier-2 (`AXS-SDK-025`..`AXS-SDK-034`)**:
   - Chuẩn hóa cấu hình dữ liệu và ABI cho 4 mục tiêu Tier-1 (`x86_64-windows` [LLP64, COFF/PE], `x86_64-linux` [LP64, ELF64], `aarch64-linux` [LP64, ELF64], `aarch64-macos` [LP64, Mach-O 64]) và 4 mục tiêu Tier-2 (`aarch64-windows` [LLP64, COFF/PE-ARM64], `aarch64-android` [LP64, ELF64], `wasm32` [ILP32, WASM/WASI], `riscv64-linux` [LP64, ELF64]).
   - Khai báo rõ ràng quy ước gọi hàm (`fastcall`, `SysV_AMD64`, `AAPCS64`, `Win64_ARM64`, `LP64D`), quy tắc dồn hàng/căn chỉnh bộ nhớ (`@repr(packed)`, `@align(N)`), mô hình SIMD (SSE2/AVX/NEON/RVV), và quy ước thanh ghi số thực (hard-float/soft-float).
   - Tích hợp trực tiếp bộ phát mã máy (`DirectEmission`) cho các định dạng COFF, ELF64, Mach-O 64, WASM và bộ liên kết gốc của Axiom (`AxiomLinker`), hỗ trợ gỡ lỗi DWARF 5, bảng mở ngăn xếp Windows `.pdata`/`.xdata` SEH, Mach-O Compact Unwind, và chữ ký số tái lập (`LC_CODE_SIGNATURE`, Authenticode stub).

4. **Dấu vân tay mật mã phân tách miền và Khóa tất định trong `axiom.lock` (`AXS-SDK-035`..`AXS-SDK-042`)**:
   - Hàm băm phân tách miền BLAKE3-256: `SdkFingerprint` (tính trên chuỗi định danh miền, bộ ba đích chuẩn hóa, bản kê khai chuẩn hóa, và gốc Merkle băm của toàn bộ tệp trong SDK) và `ToolchainFingerprint` (tính trên chuỗi định danh miền, cấu hình chuỗi công cụ, hàm băm nhị phân trình biên dịch và các bộ phát mã liên kết).
   - Khóa phiên bản trong `axiom.lock` dưới các mục `[sdk]` và `[toolchain]`. Khi bật chế độ dựng nghiêm ngặt (`--locked` hoặc `--frozen`), bất kỳ sự sai lệch nào giữa môi trường thực thi cục bộ và `axiom.lock` đều bị từ chối ngay lập tức với `AX_SDK_LOCK_MISMATCH`.
   - Kết hợp trực tiếp `SdkFingerprint` và `ToolchainFingerprint` vào khóa bộ nhớ đệm `CompilerDB`, bảo đảm không bao giờ tái sử dụng kết quả biên dịch khi SDK hoặc chuỗi công cụ bị thay đổi.

5. **Phân phối đóng gói kín, Bộ nhớ đệm phân tầng, Gương cục bộ cách ly & CLI (`AXS-SDK-043`..`AXS-SDK-055`)**:
   - Định dạng đóng gói lưu trữ định danh theo nội dung `.axsdk` và `.axtoolchain` (chuẩn nén Zstandard với đường dẫn POSIX chuẩn hóa, `mtime = 0`, chế độ tệp `0644`/`0755`, và gốc cây Merkle SHA-256).
   - Kiểm minh chữ ký số Ed25519 tích hợp `SPEC-113`, phát hiện và ngăn chặn tạo phẩm bị giả mạo hoặc chưa được ký số (`AX_SDK_SIGNATURE_INVALID`, `AX_SDK_BUNDLE_CORRUPT`).
   - Cây thư mục cài đặt bất biến cạnh nhau (`~/.axiom/sdks/<target>/<version>-<hash>/` và `~/.axiom/toolchains/<id>-<version>-<hash>/`) với quyền chỉ đọc sau khi giải nén nguyên tử.
   - Giao thức gương lưu trữ ngoại tuyến (`--mirror <path>`, `--offline`) cho phép biên dịch hoàn toàn biệt lập không mạng trong môi trường CI/CD hoặc bảo mật cao.
   - Giao diện dòng lệnh hoàn chỉnh: `axiomc sdk list|install|verify|inspect|pin` và `axiomc toolchain list|install|default|verify|pin` với các mã thoát tất định (`0` thành công, `2` tham số sai, `3` lệch hàm băm/khóa, `4` chữ ký số không hợp lệ, `5` lỗi mạng/gương).
   - **Cam kết tái lập hai máy (Two-Machine Reproducibility)**: Bảo đảm xây dựng không gian làm việc đa gói từ `axiom.lock` trên hai máy chủ độc lập hoàn toàn cho ra các tệp nhị phân đầu ra đồng nhất từng bit (`REQ-PKG-022`).

---

## 1. Architectural Distinction: Compiler, Platform SDK, and Sysroot

```
+---------------------------------------------------------------------------------------+
|                                    Axiom Architecture                                 |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|   +-------------------------------------------------------------------------------+   |
|   |                        Compiler Frontend & Middle-End                         |   |
|   |  - Parsing, Macro Expansion, Semantic Analysis, Borrow Checker                |   |
|   |  - Type Inference, Traits, Generic Monomorphization                          |   |
|   |  - High-Level IR (HIR), Mid-Level IR (MIR), Optimization Pipeline            |   |
|   +---------------------------------------+---------------------------------------+   |
|                                           |                                           |
|                                           v                                           |
|   +-------------------------------------------------------------------------------+   |
|   |                       Target Resolution & AXTOOLCHAIN                         |   |
|   |  - Target Triple (e.g. x86_64-windows, aarch64-macos, aarch64-linux)          |   |
|   |  - ABI Specification (SysV AMD64, Win64, AAPCS64, WASM32)                    |   |
|   |  - Calling Conventions, Alignment Rules, SIMD & Float ABI                     |   |
|   |  - Direct Object Writers (PE/COFF, ELF64, Mach-O 64, WASM)                    |   |
|   +---------------------------------------+---------------------------------------+   |
|                                           |                                           |
|                                           v                                           |
|   +-------------------------------------------------------------------------------+   |
|   |                          Platform SDK (.axsdk)                                |   |
|   |  - Purely Declarative Platform Contracts (sdk.toml)                           |   |
|   |  - Declarative Dynamic Import Stubs (kernel32, libc, libSystem)              |   |
|   |  - Startup & CRT Objects (crt0, crtbegin, _start contracts)                   |   |
|   |  - Platform Syscall Signatures, OS Availability Annotations                   |   |
|   |  - Target Precompiled std Modules (.axmeta)                                   |   |
|   +---------------------------------------+---------------------------------------+   |
|                                           |                                           |
|                                           v                                           |
|   +-------------------------------------------------------------------------------+   |
|   |                             Sysroot Directory                                 |   |
|   |  - Isolated On-Disk File Tree Housing SDK Artifacts                           |   |
|   |  - Content-Addressed, Cryptographically Verified, Hermetic Root               |   |
|   +-------------------------------------------------------------------------------+   |
|                                                                                       |
+---------------------------------------------------------------------------------------+
```

### `AXS-SDK-001` — Tripartite Separation of Concerns

The Axiom compilation and execution system enforces a strict, non-fungible separation of responsibilities among three architectural layers (`tasks/0605 §1–§2`, `tasks/1034 §1–§3`, `ASDK-01`, `ASDK-11`, `TOOLCHAIN-INV-02`, `REQ-ECO-8736`):
1. **Compiler (`axiomc`)**: Owns language semantics, grammar, type verification, borrow checking, ownership analysis, mid-level intermediate representation (`MIR`), target-independent optimizations, low-level intermediate representation (`LIR`), and direct machine code emission. The compiler engine is completely target-agnostic and platform-neutral.
2. **Platform SDK (`.axsdk`)**: Owns target platform contracts, system ABI constants, declarative dynamic import stubs (`kernel32.dll`, `libc.so.6`, `libSystem.B.dylib`), platform syscall signatures, C-runtime (`CRT`) startup contracts, deployment target version bounds, and target-specific precompiled standard library interfaces (`.axmeta`).
3. **Sysroot**: The physical or virtual file-system root containing the installed `.axsdk` platform artifacts, import libraries, startup object files, and metadata manifests for a specific target triple.

Under no circumstances may the compiler hard-code platform-specific system structures, OS syscall numbers, or library paths into its internal semantic tables.

### `AXS-SDK-002` — C-Free Native SDK Invariant

Axiom binaries are native programs generated without relying on C as an underlying semantic foundation or toolchain dependency (`tasks/0605 §3, §24`, `tasks/1034 §26–§28`, `ASDK-01`, `ASDK-24`, `TOOLCHAIN-INV-26`):
1. **No Ambient Host OS Path Probing**: The compiler shall never query or depend on host-specific SDK directories, such as:
   - Windows: `C:\Windows`, `C:\Program Files\Microsoft Visual Studio\*`, `C:\Program Files (x86)\Windows Kits\*`.
   - Linux: `/usr/include`, `/usr/lib`, `/usr/local/include`, `/lib64`.
   - macOS: `/Library/Developer/CommandLineTools`, `/Applications/Xcode.app`, `/System/Library/Frameworks`.
2. **No C Compiler Invocation**: The compiler shall never execute a third-party C compiler (`gcc`, `clang`, `cl.exe`, `tcc`) or assembler (`as`, `nasm`, `ml64.exe`) to compile Axiom source code, standard library packages, or startup glue.
3. **No C Preprocessor or Header Parsing**: The compiler does not parse C `.h` header files during standard compilation. All platform interfaces are declared via declarative `.axsdk` manifests or pure Axiom FFI modules.

```axiom
// POSITIVE: Canonical Axiom FFI declaration against declarative platform stub
package system.windows

@abi(system)
extern "system" {
    fn GetCurrentProcessId() -> u32
}

pub fn get_pid() -> u32 = {
    // Resolved via declarative import stub kernel32.dll in .axsdk
    GetCurrentProcessId()
}
```

```text
// NEGATIVE: Attempting to invoke C compiler or parse C headers at build time
// Build graph execution failure:
error[AX_SDK_HOST_FALLBACK_DENIED]: build script or module attempted to include host C header <windows.h>
  --> src/platform.ax:1:1
   |
 1 | #include <windows.h>
   | ^^^^^^^^^^^^^^^^^^^^ C headers cannot serve as Axiom semantic platform foundation
   |
   = help: declare platform interfaces via declarative .axsdk stubs or pure Axiom extern "system" signatures
```

### `AXS-SDK-003` — Headerless FFI & Declarative Platform Interface Boundary

Foreign Function Interface (`FFI`) declarations in Axiom interface directly with the target platform's machine ABI via declarative metadata rather than header discovery (`tasks/0605 §10`, `tasks/1034 §36`, `ASDK-09`, `ASDK-24`, `REQ-ECO-8736`):
1. The `.axsdk` provides machine-readable interface specifications containing:
   - Canonical symbol name and optional library-internal ordinal (e.g. for Windows PE).
   - Calling convention (`cdecl`, `stdcall`, `win64`, `sysv64`, `aapcs64`).
   - Strong parameter types, return type, and pointer nullability contracts.
   - Symbol introduction version, deprecation status, and weak linkage flags.
2. The compiler checks `extern` function signatures against the loaded `.axsdk` metadata tables. Any signature disagreement between the Axiom source code and the declarative platform contract is reported as a compile-time diagnostic.

### `AXS-SDK-004` — Ambient Host Path Fallback Prohibition

When building under hermetic mode (`--hermetic`) or within a deterministic workspace build, falling back to ambient host OS paths without an explicitly configured `--sysroot` or installed `.axsdk` is strictly prohibited (`tasks/0605 §2, §22`, `tasks/1034 §68–§69`, `ASDK-01`, `ASDK-18`, `REQ-PKG-022`):
1. If `--target <triple>` is specified and no compatible `.axsdk` is installed or provided via `--sysroot`, compilation fails immediately with diagnostic code `AX_SDK_HOST_FALLBACK_DENIED`.
2. The compiler must not attempt to "guess" or "auto-detect" libraries installed on the host operating system to satisfy target dependencies.
3. Every target dependency must resolve to an explicit artifact in the active sysroot.

```text
// Negative test diagnostic output:
error[AX_SDK_HOST_FALLBACK_DENIED]: hermetic build failed to locate target SDK for 'aarch64-apple-darwin'
  --> axiom.toml:8:1
   |
 8 | target = "aarch64-apple-darwin"
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ no installed .axsdk matches target triple
   |
   = note: fallback to host paths ('/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk') is forbidden under hermetic mode
   = help: install the target SDK via 'axiomc sdk install aarch64-apple-darwin' or pass an explicit '--sysroot <path>'
```

### `AXS-SDK-005` — Host Independence & Universal Cross-Compilation Invariance

The target platform SDK resolution and artifact emission pipeline is completely orthogonal to the host operating system executing `axiomc` (`tasks/0605 §22`, `tasks/1034 §6–§7`, `ASDK-01`, `ASDK-18`, `TOOLCHAIN-INV-02`, `TOOLCHAIN-INV-32`):
1. Compiling on `x86_64-windows` targeting `aarch64-linux` with SDK `linux-aarch64-6.6.axsdk` produces bit-for-bit identical binary output to compiling on `aarch64-macos` or `x86_64-linux` with the identical compiler version, SDK, and source inputs (`REQ-PKG-022`).
2. Target resolution uses normalized target triples:
   $$\text{NormalizedTriple} = \text{arch}-\text{vendor}-\text{os}-\text{abi}$$
3. The host environment provides CPU cycles, memory, and disk I/O only; it injects zero host-specific state into the target build graph.

### `AXS-SDK-006` — Freestanding vs Hosted Profile Separation

The platform SDK architecture enforces an unambiguous distinction between freestanding execution environments and hosted operating system environments (`tasks/0605 §13, §33–§34`, `tasks/1034 §31–§33`, `ASDK-13`, `ASDK-14`, `TOOLCHAIN-INV-31`):
1. **Freestanding Profile (`--profile freestanding` / `os = "none"`)**:
   - Requires no `.axsdk` or C runtime library.
   - Entry point is target-defined (typically `_start` or hardware reset vector).
   - Standard library access is restricted to `core` (no ambient I/O, threads, dynamic allocation, or OS syscalls without explicit capability tokens).
   - Platform contracts define raw CPU architecture, memory regions, and linker scripts (`AXS-SDK-022`).
2. **Hosted Profile (`--profile hosted`)**:
   - Requires an active `.axsdk` describing the target operating system.
   - Entry point follows the OS subsystem contract (`main`, `WinMain`, `_start`).
   - Links target startup objects and runtime dynamic stub tables.

```axiom
// POSITIVE: Freestanding kernel entry point requires no OS SDK or CRT
package kernel.entry

@freestanding
pub fn _start() -> never = {
    loop {}
}
```

### `AXS-SDK-007` — Runtime Decoupling & Modular Execution Composition

The Axiom language runtime (`std.runtime`) and the platform SDK (`.axsdk`) are architecturally decoupled (`tasks/0605 §14`, `tasks/1034 §29–§30, §45`, `ASDK-12`, `ASDK-14`, `TOOLCHAIN-INV-29`, `TOOLCHAIN-INV-30`):
1. Axiom binaries do not require a mandatory global C runtime (`msvcrt.dll`, `glibc`, `libSystem`) if direct syscalls or minimal startup routines are selected.
2. The Axiom runtime does not require a monolithic platform daemon or ambient shared library. All runtime features (garbage-free allocation, green fibers, async executor, panic handlers) link modularly according to package dependencies.
3. Hosted applications may consume platform SDK APIs without importing the entire Axiom standard runtime.

### `AXS-SDK-008` — Semantic Core Invariance Across SDK Versions

Platform SDKs provide external interfaces and operational parameters; they never alter the core semantic rules of the Axiom language (`tasks/0605 §32`, `ASDK-11`, `TOOLCHAIN-INV-04`, `REQ-ECO-8736`):
1. The type system, borrow checker, pattern matching exhaustiveness, lifetime rules, and safety invariants are identical across all targets and SDK versions.
2. Updating or switching an `.axsdk` from version `1.0` to `2.0` can change API availability or ABI struct offsets, but cannot alter language keywords, syntax rules, operator precedence, or expression semantics.

### `AXS-SDK-009` — Purely Declarative Manifest Authority (No Imperative Scripts)

All `.axsdk` definitions are strictly declarative (`tasks/0605 §4, §40`, `tasks/1034 §106–§108`, `ASDK-06`, `ASDK-07`, `TOOLCHAIN-INV-19`, `REQ-ECO-8736`):
1. An `.axsdk` bundle consists of declarative schema files (`sdk.toml`), binary interface definitions (`.axmeta`), import stubs, startup objects, and optional linker scripts.
2. An `.axsdk` shall never contain executable configuration scripts (`configure`, `setup.sh`, `install.bat`, `make`, `python`). Loading an SDK must never execute arbitrary code on the build host machine.
3. Manifest parsers reject unknown or malformed keys with diagnostic code `AX_SDK_CORRUPT_MANIFEST`.

---

## 2. Declarative `.axsdk` Manifest & Platform Sysroot Schema

### `AXS-SDK-010` — Declarative `.axsdk` Top-Level Manifest Schema (`sdk.toml`)

Every `.axsdk` distribution contains an authoritative declarative configuration file named `sdk.toml` located at the root of the sysroot directory (`tasks/0605 §4, §40`, `ASDK-06`, `REQ-ECO-8736`):

```toml
# Canonical sdk.toml format
[sdk]
manifest_version = "1.0.0"
name = "windows-x86_64-sdk"
version = "10.0.22621.0"
target = "x86_64-pc-windows-msvc"
description = "Canonical Native Windows SDK for x86_64"
vendor = "Axiom Foundation"

[target]
architecture = "x86_64"
vendor = "pc"
os = "windows"
abi = "msvc"
endianness = "little"
pointer_width = 64
data_model = "LLP64"

[os]
family = "windows"
min_version = "10.0.17763"
default_deployment_target = "10.0.19041"
subsystem = "console"

[capabilities]
has_mmu = true
has_threads = true
has_tls = true
has_dynamic_loader = true
has_signals = false
has_fork = false
has_posix_spawn = false

[crt]
model = "minimal"
startup_objects = ["crt/crt0.o"]
default_libraries = ["kernel32", "ntdll"]

[linker]
default_script = ""
entry_point = "main"
```

1. All keys are strictly validated against the formal schema.
2. Missing required fields (`sdk.name`, `sdk.version`, `sdk.target`, `target.architecture`, `target.os`) cause immediate loader rejection with `AX_SDK_CORRUPT_MANIFEST`.
3. Numeric versions must follow SemVer 2.0 (`X.Y.Z`) or standard OS dotted versions (`X.Y.Z.W`).

### `AXS-SDK-011` — Platform Identity, Target Triples & Minimum Deployment Targets

Target resolution determines OS platform parameters and ABI constraints from the `.axsdk` manifest (`tasks/0605 §7–§8`, `tasks/1034 §5`, `ASDK-02`, `ASDK-26`, `TOOLCHAIN-INV-03`):
1. The target triple is normalized into four canonical components:
   - Architecture: `x86_64`, `aarch64`, `wasm32`, `riscv64`.
   - Vendor: `pc`, `unknown`, `apple`, `linux`.
   - OS: `windows`, `linux`, `macos`, `android`, `wasi`, `none`.
   - Environment / ABI: `msvc`, `gnu`, `darwin`, `bionic`, `wasi`, `freestanding`.
2. The manifest declares `min_version` (the oldest operating system version this SDK supports) and `default_deployment_target` (the target version assumed when `--deployment-target` is omitted).
3. The compiler validates that the user-requested `--deployment-target` is $\ge$ `min_version`. If a deployment target older than `min_version` is requested, the compiler rejects the build with `AX_SDK_API_UNAVAILABLE`.

### `AXS-SDK-012` — Declarative Syscall & Dynamic Import Stub Schema

Platform dynamic libraries and system calls are defined in declarative stub files (`.axstub.toml` or `[imports]` tables) inside the SDK (`tasks/0605 §10, §16`, `ASDK-08`, `ASDK-09`, `REQ-ECO-8736`):

```toml
# Example: sysroot/stubs/kernel32.axstub.toml
[import_library]
name = "kernel32"
target_file = "kernel32.dll"
format = "pe_coff"

[[symbols]]
name = "ExitProcess"
ordinal = 412
calling_convention = "win64"
return_type = "void"
params = [{ name = "exit_code", type = "u32" }]
introduced = "10.0.0"
weak = false

[[symbols]]
name = "CreateThread"
ordinal = 250
calling_convention = "win64"
return_type = "usize"
params = [
    { name = "attr", type = "*const void", nullable = true },
    { name = "stack_size", type = "usize" },
    { name = "start_routine", type = "fn(usize) -> u32" },
    { name = "param", type = "usize" },
    { name = "flags", type = "u32" },
    { name = "thread_id", type = "*mut u32", nullable = true }
]
introduced = "10.0.0"
weak = false
```

1. The linker synthesizes binary import libraries (`.lib`, `.a`, `.tbd`) directly from these tables without executing platform-specific archivers.
2. Symbol ordinals, names, and calling conventions are validated at compile time.

### `AXS-SDK-013` — Executable Entry & CRT Startup Contracts

The `.axsdk` specifies the binary startup contract for hosted executables (`tasks/0605 §13, §15`, `tasks/1034 §40–§42`, `ASDK-28`, `TOOLCHAIN-INV-08`):
1. **Subsystems**:
   - `console`: Standard command-line application (entry `main`).
   - `windows`: GUI subsystem on Windows (entry `WinMain` or `wWinMain`).
   - `posix`: Standard POSIX process (entry `_start` or `main`).
   - `freestanding`: Raw bare-metal execution (entry `_start`).
   - `reactor`: WASM or shared library reactor (entry `_initialize`).
2. **Startup Hooks**:
   - `.init_array` / `.ctors`: ELF initialization function pointers executed prior to `main`.
   - `.CRT$XIA`..`.CRT$XIZ`: PE initialization tables for C and runtime initializers.
   - `mod_init_func`: Mach-O section holding pointer array for static initializers.
3. If an executable omits the required entry point, or provides an entry point signature incompatible with the subsystem, `AX_SDK_STARTUP_CONTRACT_MISMATCH` is emitted.

### `AXS-SDK-014` — Platform Memory, Page Alignment & TLS Models

The platform SDK defines memory boundaries and Thread Local Storage (`TLS`) architecture (`tasks/0605 §7`, `tasks/1034 §18, §28`, `TOOLCHAIN-INV-07`):
1. **Page Sizes**:
   - Standard x86_64 and Linux AArch64: 4096 bytes (`4 KiB`).
   - Apple Darwin AArch64: 16384 bytes (`16 KiB`).
   - Large/Huge pages: 2097152 bytes (`2 MiB`).
2. **TLS Model**:
   - Windows PE: Thread Environment Block (`TEB`) with `_tls_index` and `.tls` section.
   - Linux ELF: Initial-Exec (`IE`) or Local-Exec (`LE`) via thread register (`FS` on x86_64, `TPIDR_EL0` on AArch64).
   - Apple Darwin: `TLV` (Thread Local Variable) descriptors in `__DATA,__thread_vars`.
3. Object writers enforce section alignment matching the target platform contract.

### `AXS-SDK-015` — Compile-Time API Availability Gating (`@available`)

Axiom enforces operating system version constraints on platform functions at compile time (`tasks/0605 §11`, `ASDK-17`, `REQ-ECO-8736`):
1. Platform functions may declare version availability:
   ```axiom
   @available(os = "macos", min_version = "13.0")
   extern "system" {
       fn nw_connection_create() -> usize
   }
   ```
2. When the deployment target version is lower than the function's `min_version`, calling the function unconditionally is a compile-time error (`AX_SDK_API_UNAVAILABLE`).
3. Calling the function is permitted only if guarded by a runtime availability check (`std.os.is_available`):

```axiom
// POSITIVE: Guarded call to optional newer OS API
import std.os

pub fn try_init_network() -> bool = {
    if os.is_available("macos", "13.0") {
        let _ = nw_connection_create()
        true
    } else {
        false
    }
}
```

```text
// NEGATIVE: Unguarded call to API newer than deployment target
error[AX_SDK_API_UNAVAILABLE]: 'nw_connection_create' is only available on macOS 13.0 or newer
  --> src/net.ax:12:17
   |
12 |     let conn = nw_connection_create()
   |                ^^^^^^^^^^^^^^^^^^^^^^ function introduced in macOS 13.0, but target deployment version is 12.0
   |
   = help: wrap call in 'if std.os.is_available("macos", "13.0") { ... }' or increase deployment target
```

### `AXS-SDK-016` — Weak & Optional Platform API Binding Contracts

Platform APIs that may not exist on all target installations are marked with explicit linkage contracts (`tasks/0605 §12`, `ASDK-17`, `REQ-ECO-8736`):
1. **Linkage Classes**:
   - `Required`: Symbol must resolve at load time; loader aborts if missing.
   - `WeakLinked`: Symbol dynamically resolves to `0` (NULL pointer) if missing at load time on Mach-O and ELF without process termination.
   - `RuntimeResolved`: Symbol loaded on-demand via platform dynamic lookup (`GetProcAddress`, `dlsym`) with automated caching.
2. The compiler and linker synthesize trampolines for `WeakLinked` and `RuntimeResolved` symbols automatically, eliminating unsafe manual pointer loading.

### `AXS-SDK-017` — Apple Darwin Frameworks & Text-Based Stubs (`.tbd`)

For Apple Darwin targets (`aarch64-macos`, `x86_64-macos`), `.axsdk` provides declarative Framework layouts and text-based dynamic library stubs (`tasks/0605 §17`, `tasks/1034 §24, §55`, `ASDK-16`):
1. Text-based stub files (`.tbd`) describe exported Mach-O symbols, installation names (`install-name`), compatibility versions, and architecture slices:
   ```yaml
   --- !tapi-tbd
   tbd-version: 4
   targets: [arm64-macos]
   install-name: /System/Library/Frameworks/CoreFoundation.framework/CoreFoundation
   current-version: 1953.255
   compatibility-version: 150
   exports:
     - targets: [arm64-macos]
       symbols: [_CFRelease, _CFRetain, _CFArrayCreate]
   ...
   ```
2. The Axiom linker parses `.tbd` stubs directly, recording `LC_LOAD_DYLIB` load commands without requiring massive pre-compiled `.dylib` binaries.

### `AXS-SDK-018` — Windows Import Libraries, Ordinals & Forwarder Resolution

For Windows targets (`x86_64-windows`, `aarch64-windows`), `.axsdk` generates native COFF import libraries with forwarder support (`tasks/0605 §10, §16`, `tasks/1034 §22, §55`, `ASDK-15`):
1. Import definitions support:
   - Name-only imports (`hint` + ASCII name).
   - Ordinal-only imports (`IMPORT_ORDINAL`).
   - DLL forwarders (e.g. `NTDLL.RtlAllocateHeap` forwarded from `kernelbase.dll`).
2. The Axiom linker synthesizes Import Address Tables (`IAT`), Import Name Tables (`INT`), and `IMAGE_IMPORT_DESCRIPTOR` structures directly from `.axstub.toml` files.

### `AXS-SDK-019` — Linux Syscall Tables & Dynamic GLIBC/Musl Stubs

For Linux targets (`x86_64-linux`, `aarch64-linux`, `riscv64-linux`), `.axsdk` contains both raw syscall vectors and dynamic C library stubs (`tasks/0605 §7, §10`, `tasks/1034 §23`, `ASDK-08`):
1. **Syscall Table (`syscalls.toml`)**:
   - Maps platform-neutral syscall operations (`sys_read`, `sys_write`, `sys_openat`, `sys_exit`) to target architecture syscall numbers.
   - Used by `std.sys.linux` for pure freestanding or minimal static binaries with zero libc dependency.
2. **Dynamic Stubs**:
   - Declarative ELF dynamic symbol tables for `libc.so.6`, `libm.so.6`, `libpthread.so.0`, `libdl.so.2` with versioned symbols (e.g. `GLIBC_2.34`).
   - The linker records `DT_NEEDED` and `DT_VERNEED` entries without reading host `/lib64`.

### `AXS-SDK-020` — Android Bionic Multi-API Sysroots without NDK Dependency

For Android targets (`aarch64-android`), `.axsdk` encapsulates Bionic dynamic stubs across multiple API levels (`tasks/0605 §10`, `tasks/1034 §128`, `ASDK-10`, `REQ-ECO-8736`):
1. Stubs are cataloged by API level (`android-28`, `android-31`, `android-34`, `android-35`).
2. Selecting `--deployment-target android-34` automatically loads the API 34 stub catalog, linking against `libc.so`, `libm.so`, `liblog.so`, and `libdl.so` with proper Bionic symbol versioning.
3. Compilation succeeds on non-Android hosts without downloading the 4GB+ Google Android NDK bundle.

### `AXS-SDK-021` — WASM/WASI Capability Sysroot & Virtual Imports

For WebAssembly targets (`wasm32-unknown-wasi`), `.axsdk` defines virtual import namespaces (`tasks/0605 §29`, `tasks/1034 §25`, `ASDK-08`):
1. Maps capability-gated imports to `wasi_snapshot_preview1` or WASI Preview 2 component models:
   ```toml
   [wasi]
   standard = "preview1"
   
   [[imports]]
   module = "wasi_snapshot_preview1"
   name = "fd_write"
   signature = "(i32, i32, i32, i32) -> i32"
   ```
2. The WASM object emitter synthesizes the WASM import section directly from the `.axsdk` specification.

### `AXS-SDK-022` — Bare-Metal & Embedded Linker Script Contracts

For embedded targets (`--profile freestanding` on `riscv64` or `aarch64`), `.axsdk` provides declarative memory layout descriptors (`tasks/0605 §35–§36`, `tasks/1034 §130–§132`, `ASDK-28`):
1. Describes physical memory banks (`FLASH`, `SRAM`, `CCM`):
   ```toml
   [[memory_regions]]
   name = "FLASH"
   origin = 0x08000000
   length = 0x00100000  # 1 MiB
   access = "rx"

   [[memory_regions]]
   name = "RAM"
   origin = 0x20000000
   length = 0x00020000  # 128 KiB
   access = "rwx"
   ```
2. The Axiom linker lays out `.text`, `.rodata`, `.data`, and `.bss` according to these regions without requiring GNU `ld` scripts.

### `AXS-SDK-023` — Standard Library Precompiled Interface Integration

An `.axsdk` bundle includes target-specific precompiled interface definitions (`.axmeta`) for the Axiom standard library (`tasks/0605 §6`, `tasks/0661 §15`, `ASDK-05`, `REQ-ECO-8736`):
1. The `include/axmeta/std/` directory contains binary metadata artifacts describing:
   - Struct layouts, traits, inline functions, and type definitions for the target architecture.
   - Platform-conditional items resolved for the target's `@cfg` matrix (`SPEC-88`).
2. When compiling user code, `axiomc` loads these `.axmeta` interfaces directly, enabling sub-millisecond compilation start times without reparsing `std` source code.

### `AXS-SDK-024` — Canonical Sysroot On-Disk Directory Layout

The physical layout of an unpacked `.axsdk` directory is strictly standardized (`tasks/0605 §4`, `tasks/1034 §37–§38`, `ASDK-06`, `REQ-ECO-8736`):

```
sysroot/
├── sdk.toml               # Authoritative manifest
├── manifest.sha256        # Merkle tree checksum file
├── manifest.sig           # Ed25519 digital signature
├── include/
│   └── axmeta/            # Target precompiled .axmeta interfaces
│       ├── core.axmeta
│       ├── std.axmeta
│       └── sys.axmeta
├── stubs/                 # Dynamic import stub descriptors
│   ├── kernel32.axstub.toml
│   └── ntdll.axstub.toml
├── crt/                   # Startup object files
│   ├── crt0.o
│   └── crtbegin.o
├── lib/                   # Prebuilt static libraries and import archives
│   ├── kernel32.lib
│   └── libaxiom_rt.a
└── scripts/               # Declarative linker scripts for embedded
    └── memory.toml
```

Any modification, missing required directory, or unrecognized file outside this structure causes verification to fail with `AX_SDK_CORRUPT_MANIFEST`.

---

## 3. `AXTOOLCHAIN` Descriptors across Tier-1 and Tier-2 Targets

### `AXS-SDK-025` — `AXTOOLCHAIN` Top-Level Descriptor Schema (`toolchain.toml`)

An `AXTOOLCHAIN` package encapsulates the compiler drivers, object emission pipelines, internal linker capabilities, and target descriptors required to produce machine code for one or more targets (`tasks/1034 §4, §106–§108`, `TOOLCHAIN-INV-01`, `TOOLCHAIN-INV-19`, `REQ-ECO-8736`):

```toml
# Canonical toolchain.toml format
[toolchain]
id = "axiom-official-2026.11"
version = "0.2.0"
host = "x86_64-pc-windows-msvc"
channel = "stable"
description = "Official Axiom Native Toolchain Distribution"

[compiler]
binary = "bin/axiomc.exe"
version = "0.2.0"
features = ["native_codegen", "lto", "direct_emission"]

[targets.x86_64-pc-windows-msvc]
tier = 1
architecture = "x86_64"
data_model = "LLP64"
object_format = "coff"
executable_format = "pe64"
calling_convention = "win64"
endianness = "little"
pointer_width = 64
default_sdk = "windows-x86_64-10.0.22621"

[targets.aarch64-unknown-linux-gnu]
tier = 1
architecture = "aarch64"
data_model = "LP64"
object_format = "elf64"
executable_format = "elf64"
calling_convention = "aapcs64"
endianness = "little"
pointer_width = 64
default_sdk = "linux-aarch64-6.6"

[linker]
engine = "axiom_native"
supports_comdat_folding = true
supports_section_gc = true
supports_lto = true
```

1. Each supported target is declared in a dedicated `[targets.<triple>]` table.
2. Incompatible target combinations (e.g. attempting to emit PE64 using ELF pipeline) fail configuration validation with `AX_SDK_TOOLCHAIN_INCOMPATIBLE`.

### `AXS-SDK-026` — Architectural Baseline & Data Model Matrix Across 8 Targets

`AXTOOLCHAIN` standardizes architecture parameters across 4 Tier-1 targets and 4 Tier-2 targets (`tasks/1034 §8–§12`, `TOOLCHAIN-INV-03`, `REQ-ECO-8736`):

| Target Triple | Tier | Format | Pointer | Data Model | Endian | Default ABI | Stack Align |
|---|---|---|---|---|---|---|---|
| `x86_64-pc-windows-msvc` | 1 | COFF/PE | 64-bit | `LLP64` | Little | `win64` | 16 bytes |
| `x86_64-unknown-linux-gnu` | 1 | ELF64 | 64-bit | `LP64` | Little | `sysv64` | 16 bytes |
| `aarch64-unknown-linux-gnu`| 1 | ELF64 | 64-bit | `LP64` | Little | `aapcs64` | 16 bytes |
| `aarch64-apple-darwin` | 1 | Mach-O | 64-bit | `LP64` | Little | `darwin_arm64`| 16 bytes |
| `aarch64-pc-windows-msvc` | 2 | COFF/PE | 64-bit | `LLP64` | Little | `win64_arm64` | 16 bytes |
| `aarch64-linux-android` | 2 | ELF64 | 64-bit | `LP64` | Little | `aapcs64` | 16 bytes |
| `wasm32-unknown-wasi` | 2 | WASM | 32-bit | `ILP32` | Little | `wasm32` | 16 bytes |
| `riscv64-unknown-linux-gnu`| 2 | ELF64 | 64-bit | `LP64` | Little | `lp64d` | 16 bytes |

1. **`LLP64`**: `i32` is 32-bit, `i64` is 64-bit, `isize`/`usize` is 64-bit, C `long` is 32-bit.
2. **`LP64`**: `i32` is 32-bit, `i64` is 64-bit, `isize`/`usize` is 64-bit, C `long` is 64-bit.
3. **`ILP32`**: `i32` is 32-bit, `i64` is 64-bit, `isize`/`usize` is 32-bit, C `long` is 32-bit.

### `AXS-SDK-027` — ABI, Calling Conventions & Register Preservation Contracts

Every target descriptor defines exact register preservation and argument-passing rules (`tasks/1034 §13–§17`, `TOOLCHAIN-INV-04`, `TOOLCHAIN-INV-05`):
1. **`win64` (x86_64 Windows)**:
   - Arguments 1–4 passed in `RCX`, `RDX`, `R8`, `R9` (or `XMM0`–`XMM3` for float/SIMD).
   - Callee-save registers: `RBX`, `RBP`, `RDI`, `RSI`, `R12`–`R15`, `XMM6`–`XMM15`.
   - Shadow space: Mandatory 32-byte home space allocated on stack by caller.
2. **`sysv64` (x86_64 Linux/BSD)**:
   - Arguments 1–6 passed in `RDI`, `RSI`, `RDX`, `RCX`, `R8`, `R9`.
   - Float arguments 1–8 passed in `XMM0`–`XMM7`.
   - Callee-save registers: `RBX`, `RSP`, `RBP`, `R12`–`R15`.
   - Red zone: 128 bytes beyond stack pointer available for leaf functions.
3. **`aapcs64` / `darwin_arm64` (AArch64)**:
   - Arguments 1–8 passed in `X0`–`X7` (or `V0`–`V7`).
   - Callee-save registers: `X19`–`X28`, `SP`, `FP` (`X29`), `LR` (`X30`), `V8`–`V15` (lower 64-bits).
   - Platform-specific register: `X18` reserved for TEB on Windows ARM64; reserved for Apple platform thread context on Darwin.
4. **`lp64d` (RISC-V 64)**:
   - Arguments 1–8 passed in `a0`–`a7` (or `fa0`–`fa7`).
   - Callee-save registers: `s0`–`s11`, `fs0`–`fs11`.

### `AXS-SDK-028` — Struct Sizing, Packing & Alignment Invariants

Aggregates adhere strictly to target platform layout rules (`tasks/1034 §17–§18`, `TOOLCHAIN-INV-06`, `TOOLCHAIN-INV-07`):
1. **Natural Alignment**: Every primitive field is aligned to a multiple of its size ($\le 16$ bytes). Struct alignment is the maximum alignment of any field.
2. **Packed Structs (`@repr(packed)`)**: All fields aligned to 1 byte; no padding inserted. Accessing unaligned fields requires explicit unaligned load/store primitives to prevent hardware faults on strict-alignment architectures (`AArch64`, `RISC-V`).
3. **Explicit Alignment (`@align(N)`)**: Enforces minimum struct alignment of $N$ bytes (where $N$ is a power of two).

### `AXS-SDK-029` — SIMD Vector & Floating-Point ABI Contracts

`AXTOOLCHAIN` specifies the hardware vector and floating-point registers used for calling conventions (`tasks/1034 §19–§20`, `TOOLCHAIN-INV-15`):
1. **Floating-Point**:
   - `Hard-Float` (default on all tier-1/tier-2 targets): Floating-point parameters and return values are passed in hardware FPU registers (`XMM`, `V`, `fa`).
   - `Soft-Float` (opt-in for embedded freestanding): Floating-point values passed in general-purpose registers.
2. **SIMD Vectors (`std.simd.Vector<T, N>`)**:
   - Up to 128-bit vectors: Passed in SIMD registers (`XMM0`–`XMM7`, `V0`–`V7`).
   - Vectors exceeding register width (e.g. 256-bit AVX2 on baseline SSE2 target): Split across multiple registers or passed by read-only reference (`view`).

### `AXS-SDK-030` — Direct Machine Emission Pipelines (`DirectEmission`)

The compiler implements native binary emitters (`DirectEmission`) for all supported object formats (`tasks/1034 §21–§25, §49`, `TOOLCHAIN-INV-25`, `TOOLCHAIN-INV-28`):
1. **COFF Object Emitter**: Generates standard Microsoft COFF `.obj` files with `.text`, `.data`, `.rdata`, `.pdata`, `.xdata`, and symbol relocation tables.
2. **ELF64 Object Emitter**: Generates relocatable ELF `.o` files with section headers, `.symtab`, `.strtab`, `.rela.text`, and DWARF sections.
3. **Mach-O 64 Emitter**: Generates `MH_OBJECT` Mach-O `.o` files with `LC_SEGMENT_64`, `LC_BUILD_VERSION`, and relocation entries.
4. **WASM Emitter**: Generates binary `.wasm` modules with Type, Import, Function, Memory, Export, and Code sections.

External assemblers (`nasm`, `as`) are never required for compiling Axiom source code.

### `AXS-SDK-031` — Relocation & Position-Independence Models (Static, PIC, PIE)

Target pipelines support deterministic code relocation models (`tasks/1034 §26–§27`, `TOOLCHAIN-INV-08`):
1. **Static (`--reloc static`)**: Absolute 32-bit/64-bit addresses bound at link time. Standard for bare-metal kernels and freestanding targets.
2. **PIC (`Position Independent Code`, `--reloc pic`)**: Relative addressing via RIP-relative loads (x86_64) or `ADRP` + `ADD` (AArch64). Required for dynamic shared libraries (`.so`, `.dylib`, `.dll`).
3. **PIE (`Position Independent Executable`, `--reloc pie`)**: Executable binary capable of loading at an arbitrary randomized virtual address (ASLR). Mandatory default on Linux, macOS, and Android.

### `AXS-SDK-032` — Native Axiom Linker Integration & Toolchain Adapters

`AXTOOLCHAIN` configures the linking stage (`tasks/1034 §51–§58`, `TOOLCHAIN-INV-09`, `TOOLCHAIN-INV-27`):
1. **Native Linker (`AxiomLinker`)**:
   - Internal multi-format linker supporting COFF/PE, ELF64, Mach-O 64, and WASM.
   - Performs COMDAT deduplication, section garbage collection (`--gc-sections` / `/OPT:REF`), identical code folding (`ICF`), and deterministic import resolution.
2. **System Linker Adapter (`SystemLinkerAdapter`)**:
   - Optional interoperability bridge allowing delegation to system linkers (`link.exe`, `lld`, `ld64`) when integrating complex external C++ libraries.
   - The system linker adapter is never used in hermetic builds (`--hermetic`).

### `AXS-SDK-033` — Debug Metadata & Unwind Information Pipelines

`AXTOOLCHAIN` coordinates debug symbols and structured exception handling (`tasks/1034 §78–§79`, `TOOLCHAIN-INV-08`):
1. **DWARF 5**: Emitted for Linux, macOS, Android, WASM, and freestanding targets (`.debug_info`, `.debug_line`, `.debug_abbrev`, `.debug_str`).
2. **Windows SEH (`.pdata` / `.xdata`)**: Emitted for x86_64 and AArch64 Windows targets, describing function epilogues, prologues, stack frame offsets, and exception handler addresses.
3. **Mach-O Compact Unwind (`__LD,__compact_unwind`)**: Compact unwind encoding for Apple Darwin targets, falling back to DWARF CFI when complex frame layouts occur.

### `AXS-SDK-034` — Reproducible Platform Signing & Codesign Integration

Targets requiring code signatures integrate deterministic signing into the output pipeline (`tasks/1034 §136–§138`, `TOOLCHAIN-INV-37`, `REQ-PKG-022`):
1. **macOS Ad-Hoc Signing**: For `aarch64-apple-darwin`, the linker embeds an ad-hoc code signature (`LC_CODE_SIGNATURE`) with SHA-256 page hashes and designated requirements directly into the Mach-O binary.
2. **Windows Authenticode Stub**: The PE linker aligns PE checksum headers and reserves the Security Directory entry for post-build signing without modifying code section hashes.
3. Code signing executes reproducibly without querying ambient host certificates or timestamps.

---

## 4. Cryptographic `SdkFingerprint`, `ToolchainFingerprint` & `axiom.lock` Pinning

### `AXS-SDK-035` — Cryptographic Domain-Separated `SdkFingerprint` Specification

Every platform SDK possesses an immutable cryptographic fingerprint (`SdkFingerprint`) computed using BLAKE3-256 over a domain-separated canonical serialization (`tasks/0605 §5`, `ASDK-04`, `ASDK-21`, `REQ-ECO-8736`, `REQ-PKG-022`):

$$\text{SdkFingerprint} = \text{BLAKE3}\Big(\text{"AXIOM\_SDK\_FINGERPRINT\_V1\x00"} \mathbin{\Vert} \text{TargetTriple} \mathbin{\Vert} \text{CanonicalManifestBytes} \mathbin{\Vert} \text{FileMerkleRoot}\Big)$$

1. **Components**:
   - Domain separator: Constant UTF-8 byte string `b"AXIOM_SDK_FINGERPRINT_V1\x00"`.
   - `TargetTriple`: Normalized target triple string (e.g. `x86_64-pc-windows-msvc`).
   - `CanonicalManifestBytes`: Sorted, whitespace-normalized TOML serialization of `sdk.toml`.
   - `FileMerkleRoot`: 32-byte BLAKE3 Merkle root computed over all files in the sysroot (excluding signature and checksum files themselves), sorted lexicographically by normalized POSIX path:
     $$\text{EntryHash}_i = \text{BLAKE3}\Big(\text{Path}_i \mathbin{\Vert} \text{FileSize}_i \mathbin{\Vert} \text{FileBytes}_i\Big)$$
2. Any change to a stub file, CRT object, or manifest key produces a completely different `SdkFingerprint`.

### `AXS-SDK-036` — Cryptographic Domain-Separated `ToolchainFingerprint` Specification

An `AXTOOLCHAIN` instance computes an immutable fingerprint (`ToolchainFingerprint`) over its executable and target configuration payload (`tasks/1034 §61`, `TOOLCHAIN-INV-20`, `REQ-ECO-8736`):

$$\text{ToolchainFingerprint} = \text{BLAKE3}\Big(\text{"AXIOM\_TOOLCHAIN\_FINGERPRINT\_V1\x00"} \mathbin{\Vert} \text{ToolchainId} \mathbin{\Vert} \text{ToolchainVersion} \mathbin{\Vert} \text{CompilerBinaryHash} \mathbin{\Vert} \text{CanonicalDescriptorBytes}\Big)$$

1. **Components**:
   - Domain separator: Constant UTF-8 byte string `b"AXIOM_TOOLCHAIN_FINGERPRINT_V1\x00"`.
   - `ToolchainId`: Unique toolchain identifier string (e.g. `axiom-official-2026.11`).
   - `ToolchainVersion`: SemVer string (e.g. `0.2.0`).
   - `CompilerBinaryHash`: BLAKE3 hash of the `axiomc` compiler executable binary itself.
   - `CanonicalDescriptorBytes`: Sorted, canonical TOML serialization of `toolchain.toml`.
2. This fingerprint guarantees that any upgrade, patch, or substitution of compiler binaries invalidates the toolchain identity.

### `AXS-SDK-037` — Declarative `axiom.lock` `[sdk]` Schema & Pinning

Axiom workspace lockfiles (`axiom.lock`) contain deterministic pinning records for target SDKs (`tasks/0605 §19`, `ASDK-19`, `REQ-PKG-022`):

```toml
# In axiom.lock
[sdk."x86_64-pc-windows-msvc"]
version = "10.0.22621.0"
fingerprint = "blake3:9f83c1b2e5a7d6e4b8a2c1f0e4b7a9d8c2e1f4b7a9d8c2e1f4b7a9d8c2e1f4b7"
source = "registry+https://sdk.axiom-lang.org"

[sdk."aarch64-unknown-linux-gnu"]
version = "6.6.0"
fingerprint = "blake3:a2c4e6b8d0f1a3c5e7b9d1f3a5c7e9b1d3f5a7c9e1b3d5f7a9c1e3b5d7f9a1c3"
source = "registry+https://sdk.axiom-lang.org"
```

1. Each target triple used in the workspace has an explicit entry under `[sdk."<triple>"]`.
2. The lockfile pins the exact `fingerprint` and `version`.

### `AXS-SDK-038` — Declarative `axiom.lock` `[toolchain]` Schema & Pinning

Workspace lockfiles pin the compiler toolchain configuration used to generate the build (`tasks/1034 §66`, `TOOLCHAIN-INV-10`, `TOOLCHAIN-INV-12`, `REQ-PKG-022`):

```toml
# In axiom.lock
[toolchain]
id = "axiom-official-2026.11"
version = "0.2.0"
fingerprint = "blake3:b1c3d5e7f9a2c4e6b8d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f8a0c2e4"
channel = "stable"
```

1. The `[toolchain]` table records the compiler toolchain ID, SemVer, and cryptographic fingerprint.
2. Multiple developers or CI workers sharing `axiom.lock` are constrained to compile using the identical toolchain configuration.

### `AXS-SDK-039` — Strict Lockfile Verification under `--locked` & `--frozen`

When building with `--locked` (standard CI mode) or `--frozen` (air-gapped release mode), the driver verifies all pinned fingerprints prior to scheduling build tasks (`tasks/0605 §19, §30`, `ASDK-19`, `ASDK-30`, `REQ-PKG-022`):
1. The driver checks the active sysroot `SdkFingerprint` against the lockfile entry for the active target:
   $$\text{SdkFingerprint}_{\text{local}} \stackrel{?}{=} \text{SdkFingerprint}_{\text{lock}}$$
2. The driver checks the active `ToolchainFingerprint` against the lockfile entry:
   $$\text{ToolchainFingerprint}_{\text{local}} \stackrel{?}{=} \text{ToolchainFingerprint}_{\text{lock}}$$
3. If any fingerprint differs, the build is aborted immediately with diagnostic `AX_SDK_LOCK_MISMATCH`:

```text
error[AX_SDK_LOCK_MISMATCH]: local SDK fingerprint does not match axiom.lock
  --> axiom.lock:14:1
   |
14 | [sdk."x86_64-pc-windows-msvc"]
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ locked fingerprint mismatch
   |
   = expected: blake3:9f83c1b2e5a7d6e4b8a2c1f0e4b7a9d8c2e1f4b7a9d8c2e1f4b7a9d8c2e1f4b7
   = found:    blake3:7a4c9b2e1d0f8a3c5e7b9d1f3a5c7e9b1d3f5a7c9e1b3d5f7a9c1e3b5d7f9a1c
   = note: the target SDK has been modified or updated locally
   = help: run 'axiomc sdk pin' to update axiom.lock, or reinstall the canonical SDK
```

### `AXS-SDK-040` — Build Graph Query Key & Persistent Cache Integration

The build graph driver (`SPEC-110`) and persistent compilation database (`CompilerDB`) incorporate SDK and toolchain fingerprints into all cache keys (`tasks/0605 §5`, `ASDK-05`, `TOOLCHAIN-INV-20`, `REQ-PKG-022`):

$$\text{ActionCacheKey} = \text{BLAKE3}\Big(\text{PackageInputHash} \mathbin{\Vert} \text{SdkFingerprint} \mathbin{\Vert} \text{ToolchainFingerprint} \mathbin{\Vert} \text{BuildFlagsHash}\Big)$$

1. Upgrading or switching the target SDK automatically invalidates all affected compilation and link units without manual `axiomc clean`.
2. Cache hits are guaranteed to be semantically equivalent because changes in platform stubs or CRT startup objects alter `SdkFingerprint`.

### `AXS-SDK-041` — Multi-Target Workspace Pinning & Configuration Matrix

Axiom workspaces building multi-target configurations simultaneously (e.g. native desktop executable + WebAssembly frontend plugin) maintain independent SDK pins per target in `axiom.lock` (`tasks/0605 §8, §18`, `tasks/1034 §33`, `TOOLCHAIN-INV-33`):
1. Each target resolves its own sysroot independently.
2. Compiling target A cannot mutate or pollute the cache keys or sysroot resolution of target B.
3. The build graph partitions compile tasks by `(PackageId, TargetTriple)` pairs.

### `AXS-SDK-042` — On-Disk Fingerprint Introspection & Tamper Detection

The `axiomc sdk verify` and `axiomc toolchain verify` commands validate the physical integrity of installed components (`tasks/0605 §20, §38`, `tasks/1034 §71`, `ASDK-20`, `ASDK-21`):
1. Traverses all installed files and recomputes the Merkle tree hash.
2. Compares the result against the cryptographic digest recorded in `sdk.toml` / `toolchain.toml`.
3. If an adversary or faulty disk modified any binary file, import stub, or manifest entry, the command flags the exact modified files and exits with code 3.

---

## 5. Hermetic Distribution, Installation Cache, Offline Mirrors & CLI

### `AXS-SDK-043` — Content-Addressed Distribution Archive Layout (`.axsdk`, `.axtoolchain`)

Platform SDKs and toolchains are packaged into deterministic, content-addressed archives (`tasks/0605 §23`, `tasks/0858 §1–§5`, `tasks/1034 §63`, `REQ-ECO-8736`):
1. **Archive Formats**:
   - `.axsdk`: Zstandard-compressed tarball (`.tar.zst`) or deterministic zip container containing the complete sysroot payload.
   - `.axtoolchain`: Zstandard-compressed tarball containing the compiler binaries, runtime libraries, and default target descriptors.
2. **Determinism Constraints**:
   - Entries sorted in strict lexicographical order by normalized POSIX path.
   - All file timestamps normalized to UNIX epoch zero (`mtime = 0`, `1970-01-01T00:00:00Z`).
   - File modes standardized to `0644` for regular data files and `0755` for executable binaries and directories.
   - Owner UID/GID normalized to `0/0` (root/root).
3. Any path containing parent directory traversal (`..`), absolute paths, or NUL characters is rejected on extraction with `AX_SDK_BUNDLE_CORRUPT`.

### `AXS-SDK-044` — Ed25519 Archive Signing & Verification (`SPEC-113` Integration)

All official `.axsdk` and `.axtoolchain` archives carry an Ed25519 cryptographic signature generated by the official Axiom release infrastructure (`tasks/0605 §25`, `tasks/1034 §71, §103`, `SPEC-113`, `REQ-PKG-024`):
1. **Signature File (`<archive-name>.axsig`)**:
   Contains an Ed25519 signature over the SHA-256 Merkle root of the archive contents.
2. **Verification Policy**:
   - `axiomc` verifies the archive signature against the embedded Axiom root public keys or user-configured trusted signer keys in `axiom.toml` `[trust.policy]`.
   - Archives with missing signatures, unknown signers, or signature verification failures are rejected with `AX_SDK_SIGNATURE_INVALID`.

### `AXS-SDK-045` — Immutable Side-by-Side Local Installation Cache

Downloaded and installed SDKs and toolchains reside in an immutable, side-by-side local store (`tasks/0605 §23`, `tasks/1034 §64, §122`, `REQ-ECO-8736`):
1. **Default Cache Directory**:
   - User level: `~/.axiom/sdks/` and `~/.axiom/toolchains/`.
   - System/Global level (optional): `/opt/axiom/sdks/` or `C:\ProgramData\Axiom\sdks\`.
2. **Directory Layout**:
   ```
   ~/.axiom/
   ├── sdks/
   │   ├── x86_64-pc-windows-msvc/
   │   │   └── 10.0.22621.0-9f83c1b2e5a7d6e4/    # version + SdkFingerprint[:16]
   │   │       ├── sdk.toml
   │   │       ├── crt/
   │   │       └── stubs/
   │   └── aarch64-unknown-linux-gnu/
   │       └── 6.6.0-a2c4e6b8d0f1a3c5/
   └── toolchains/
       └── axiom-official-2026.11-0.2.0-b1c3d5e7f9a2c4e6/
           ├── toolchain.toml
           └── bin/
   ```
3. **Atomic Installation**:
   - The archive is extracted into a temporary sibling directory (`.tmp-<uuid>`).
   - Integrity and signature are verified in full.
   - The directory is atomically renamed into its final fingerprint-derived name.
   - File permissions are set to read-only (`0444` / `0555`) to prevent accidental modification.

### `AXS-SDK-046` — Air-Gapped Offline Mirror Protocol & Network Policy

Axiom supports completely offline and air-gapped development environments (`tasks/0605 §21, §24`, `tasks/0858 §12–§14`, `tasks/1034 §73`, `REQ-ECO-8736`):
1. **Offline Flag (`--offline`)**:
   When passed, `axiomc` disables all network socket creation. Any attempt to reach remote registries or servers fails immediately.
2. **Local Mirror Structure (`--mirror <path>`)**:
   ```
   <mirror-root>/
   ├── index.json             # Signed catalog of all available SDKs & toolchains
   ├── index.json.axsig       # Ed25519 signature of index.json
   ├── sdks/
   │   ├── windows-x86_64-10.0.22621.0.axsdk
   │   └── linux-aarch64-6.6.0.axsdk
   └── toolchains/
       └── axiom-official-2026.11-0.2.0-x86_64-windows.axtoolchain
   ```
3. `axiomc sdk install --mirror <path> --offline` installs target SDKs directly from the mirror directory with full signature and fingerprint verification.

### `AXS-SDK-047` — CLI: `axiomc sdk list` & `axiomc sdk inspect`

Commands for querying available and installed SDKs (`tasks/0605 §18, §39`, `REQ-ECO-8736`):

```bash
# List all locally installed SDKs
axiomc sdk list

# List all SDKs including available remote/mirror packages in JSON
axiomc sdk list --available --json

# Inspect detailed configuration of an installed SDK
axiomc sdk inspect x86_64-pc-windows-msvc@10.0.22621.0
```

Sample JSON output for `axiomc sdk inspect`:
```json
{
  "name": "windows-x86_64-sdk",
  "version": "10.0.22621.0",
  "target": "x86_64-pc-windows-msvc",
  "fingerprint": "blake3:9f83c1b2e5a7d6e4b8a2c1f0e4b7a9d8c2e1f4b7a9d8c2e1f4b7a9d8c2e1f4b7",
  "min_version": "10.0.17763",
  "default_deployment_target": "10.0.19041",
  "path": "/home/user/.axiom/sdks/x86_64-pc-windows-msvc/10.0.22621.0-9f83c1b2e5a7d6e4",
  "has_mmu": true,
  "has_threads": true
}
```

### `AXS-SDK-048` — CLI: `axiomc sdk install`

Command for downloading and installing target SDKs (`tasks/0605 §18`, `REQ-ECO-8736`):

```bash
# Install SDK for target triple
axiomc sdk install aarch64-unknown-linux-gnu

# Install specific version from offline mirror
axiomc sdk install x86_64-pc-windows-msvc@10.0.22621.0 --mirror /mnt/axiom-mirror --offline
```

1. Resolves target triple against installed catalog; if already installed with matching fingerprint, installation is a no-op.
2. Downloads or copies archive, validates Ed25519 signature, checks SHA-256 Merkle root, unpacks into side-by-side cache, and marks read-only.

### `AXS-SDK-049` — CLI: `axiomc sdk verify`

Command for verifying the integrity of installed SDKs (`tasks/0605 §18, §39`, `ASDK-21`):

```bash
# Verify integrity of specific target SDK
axiomc sdk verify x86_64-pc-windows-msvc

# Verify all installed SDKs
axiomc sdk verify --all
```

Returns exit code 0 if all files match their canonical Merkle tree digests; exits with code 3 if corruption or tampering is detected.

### `AXS-SDK-050` — CLI: `axiomc sdk pin`

Command for binding the current active target SDK into `axiom.lock` (`tasks/0605 §19`, `ASDK-19`, `REQ-PKG-022`):

```bash
# Pin current workspace target SDK into axiom.lock
axiomc sdk pin

# Pin specific target SDK
axiomc sdk pin --target aarch64-unknown-linux-gnu
```

Updates or creates the `[sdk."<triple>"]` section in `axiom.lock` with the active version and cryptographic `SdkFingerprint`.

### `AXS-SDK-051` — CLI: `axiomc toolchain list` & `axiomc toolchain default`

Commands for managing compiler toolchains (`tasks/1034 §64, §67`, `REQ-ECO-8736`):

```bash
# List installed toolchains
axiomc toolchain list

# Set default active toolchain
axiomc toolchain default axiom-official-2026.11@0.2.0
```

### `AXS-SDK-052` — CLI: `axiomc toolchain install`

Command for installing new toolchain packages (`tasks/1034 §64`, `REQ-ECO-8736`):

```bash
# Install toolchain from registry
axiomc toolchain install axiom-nightly-2026.11

# Install toolchain from local mirror
axiomc toolchain install axiom-official-2026.11@0.2.0 --mirror /opt/axiom-mirror --offline
```

### `AXS-SDK-053` — CLI: `axiomc toolchain verify` & `axiomc toolchain pin`

Commands for validating and locking toolchains (`tasks/1034 §66, §71`, `TOOLCHAIN-INV-10`, `REQ-PKG-022`):

```bash
# Verify binary integrity of installed toolchain
axiomc toolchain verify axiom-official-2026.11

# Pin active toolchain into axiom.lock
axiomc toolchain pin
```

### `AXS-SDK-054` — Deterministic CLI Exit Code & Machine-Readable Output Specification

All `axiomc sdk` and `axiomc toolchain` commands return deterministic exit codes (`tasks/0605 §39`, `tasks/1034 §114–§115`, `REQ-ECO-8736`):

| Exit Code | Classification | Meaning |
|---|---|---|
| `0` | Success | Operation completed successfully |
| `1` | General Error | Internal runtime failure or unexpected exception |
| `2` | Bad Usage / Args | Invalid command-line arguments, unknown flag, or malformed target triple |
| `3` | Verification Error | Merkle hash mismatch, corrupt manifest, or `axiom.lock` fingerprint divergence |
| `4` | Signature Error | Missing, untrusted, or cryptographically invalid Ed25519 signature |
| `5` | Network / IO Error | Connection refused, timeout, missing mirror path, or file read/write permission denied |

When `--json` is supplied, all diagnostic messages, progress updates, and results format as valid JSONL records on `stdout`, reserving `stderr` for unrecoverable crashes.

### `AXS-SDK-055` — Two-Machine Bit-for-Bit Workspace Reproducibility Contract (`REQ-PKG-022`)

Building a workspace from a canonical `axiom.lock` produces bit-for-bit identical binary artifacts across two independent machines (`tasks/0605 §5`, `tasks/1034 §62`, `REQ-PKG-022`):
1. **Environmental Invariance**:
   Two build machines executing `axiomc build --locked` with:
   - Distinct root installation paths (e.g. `/home/user_a/repo` vs `/data/ci_worker_b/build`).
   - Distinct host usernames and user IDs.
   - Distinct temporary directories (`TMPDIR`).
   - Distinct system timezones, locales, and environment variables.
   - Distinct wall-clock timestamps ($T_1 \ne T_2$).
   - Distinct multi-threading worker thread counts (`--jobs 4` vs `--jobs 16`).
   shall produce final output binaries with identical SHA-256 digests:
   $$\text{SHA256}(\text{Binary}_{\text{Machine A}}) = \text{SHA256}(\text{Binary}_{\text{Machine B}})$$
2. All debug information (`DWARF`, `PDB`), object timestamps, and section padding bytes are normalized to deterministic values.

---

## 6. Diagnostic Code Reference

The following diagnostic codes govern SDK loading, toolchain discovery, and lockfile verification (`spec/diagnostics.md`, `ASDK-21`, `ASDK-22`, `TOOLCHAIN-INV-16`, `TOOLCHAIN-INV-17`):

| Diagnostic Code | Severity | Task | Summary Description |
|---|---|---|---|
| `AX_SDK_MANIFEST_NOT_FOUND` | Error | T875 | The `sdk.toml` manifest was not found in the sysroot directory |
| `AX_SDK_CORRUPT_MANIFEST` | Error | T875 | The `sdk.toml` manifest contains syntax errors, unknown schema keys, or invalid types |
| `AX_SDK_FINGERPRINT_MISMATCH` | Error | T875/T876 | Computed `SdkFingerprint` does not match the manifest or `axiom.lock` |
| `AX_SDK_TOOLCHAIN_FINGERPRINT_MISMATCH` | Error | T875/T876 | Computed `ToolchainFingerprint` does not match active binary hash or `axiom.lock` |
| `AX_SDK_HOST_FALLBACK_DENIED` | Error | T875 | Hermetic build attempted fallback to ambient host OS paths without an installed SDK |
| `AX_SDK_API_UNAVAILABLE` | Error | T875 | Target platform function requires an OS version newer than target deployment version |
| `AX_SDK_IMPORT_STUB_NOT_FOUND` | Error | T875 | Required dynamic library or syscall stub was not found in the platform SDK |
| `AX_SDK_STARTUP_CONTRACT_MISMATCH` | Error | T875 | Entry point or subsystem contract is incompatible with target architecture / ABI |
| `AX_SDK_TOOLCHAIN_NOT_FOUND` | Error | T875/T876 | Requested `AXTOOLCHAIN` configuration or compiler component is not installed |
| `AX_SDK_TOOLCHAIN_INCOMPATIBLE` | Error | T875 | Selected toolchain components disagree on pointer width, endianness, or ABI format |
| `AX_SDK_LOCK_MISMATCH` | Error | T876 | Active SDK or toolchain fingerprint differs from `axiom.lock` under `--locked` |
| `AX_SDK_BUNDLE_CORRUPT` | Error | T876 | Distribution archive contains invalid headers, checksum mismatch, or path traversal |
| `AX_SDK_SIGNATURE_INVALID` | Error | T876 | Ed25519 signature verification failed for SDK or toolchain archive |

---

## 7. Formal Invariants & Verification Matrix

The invariants established by this specification are certified by tasks `T875`, `T876`, and `T877` in `spec/invariants.md`:

```
+-----------------------------------------------------------------------------------------------+
| Invariant ID | Title                                             | Since | Verification Path  |
+--------------+---------------------------------------------------+-------+--------------------+
| INV-SDK-001  | Declarative .axsdk loader & AXTOOLCHAIN registry  | T875  | tests/run/sdk_sysroot
| INV-SDK-002  | Hermetic bundle packager, lock pinning & CLI      | T876  | tests/run/sdk_toolchain_cli
| INV-SDK-003  | Two-machine reproducible workspace conformance    | T877  | tests/conformance/p20/e20_6_sdk_toolchain_workspace
+-----------------------------------------------------------------------------------------------+
```

---

## Sources

- `tasks/0605 - BOOTSTRAP-346 — AXIOM NATIVE SDK, SYSROOT & PLATFORM DEVELOPMENT KIT ENGINE.md` (§1–§43, `ASDK-01`..`ASDK-30`)
- `tasks/1034 - BOOTSTRAP-769 — AXTOOLCHAIN.md` (§1–§141, `TOOLCHAIN-INV-01`..`TOOLCHAIN-INV-40`)
- `tasks/0661 - BOOTSTRAP-402 — Package, Module, Workspace, Dependency & Reproducible Build Engine.md` (§5, §18–§21, §35)
- `tasks/0858 - BOOTSTRAP-625 — Native Application Package Registry, Repository, Dependency Resolution Service, Update Channel, Rollback & Distribution Runtime 5.0.md` (§1–§25)
- `spec/SPEC-88-cross-compilation-platform-layer.md`
- `spec/SPEC-110-build-graph-driver.md`
- `spec/SPEC-111-package-manager-resolution-lockfiles.md`
- `spec/SPEC-113-hermetic-builds-supply-chain-trust.md`
- `spec/SPEC-114-abi-stability-versioning-binary-compat.md`
- `spec/requirements/CATALOG.md` (`REQ-ECO-8736`, `REQ-PKG-022`)
