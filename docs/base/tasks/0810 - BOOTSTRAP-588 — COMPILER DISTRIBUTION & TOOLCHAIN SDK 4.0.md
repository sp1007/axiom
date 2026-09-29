# BOOTSTRAP-588 — COMPILER DISTRIBUTION & TOOLCHAIN SDK 4.0
## MULTI-TARGET SDK, SYSROOT, TARGET ABI DATABASE, NATIVE LIBRARY/SDK IMPORT, CROSS-COMPILATION PACKS, TOOLCHAIN MANIFEST, INSTALLATION, VERSION SELECTION & OFFLINE DEVELOPMENT ENVIRONMENT

**Trạng thái: COMPLETED / LOCKED**

`588` biến compiler đã self-host ở `586–587` thành một **toolchain có thể phân phối và sử dụng độc lập**.

Mục tiêu:

```text
Installed Axiom SDK
        │
        ├── Compiler
        ├── Linker
        ├── Runtime
        ├── Stdlib
        ├── Target DB
        ├── Sysroots
        ├── Native SDKs
        ├── Debug tools
        └── Package metadata
                 │
                 ▼
        axiom build --target ...
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
      Windows   Linux    WASM
        │        │        │
        ▼        ▼        ▼
       EXE      ELF     .wasm
```

---

# 588.1. Toolchain definition

Một Axiom toolchain hoàn chỉnh gồm:

```text
Toolchain {
    compiler
    linker
    object_tools
    runtime
    stdlib
    target_database
    target_sdks
    sysroots
    debug_support
    package_metadata
}
```

---

# 588.2. Toolchain không đồng nghĩa compiler

Compiler chỉ là một thành phần.

Toolchain phải cung cấp toàn bộ environment cần để build target.

---

# 588.3. Toolchain identity

```text
ToolchainIdentity {
    compiler_version
    language_edition
    runtime_version
    stdlib_version
    target_db_version
    sdk_versions
}
```

---

# 588.4. Target identity

Mỗi target có canonical ID:

```text
x86_64-pc-windows
x86_64-unknown-linux
aarch64-apple-macos
aarch64-apple-ios
aarch64-linux-android
wasm32-unknown-axiom
```

Tên cụ thể có thể mở rộng nhưng phải canonical và machine-readable.

---

# 588.5. Target triple

Target triple được mở rộng thành target descriptor:

```text
TargetDescriptor {
    architecture
    vendor
    os
    environment
    abi
    object_format
    cpu_baseline
    features
    endianness
    pointer_width
}
```

---

# 588.6. Target database

Target DB là nguồn canonical cho:

- ISA;
- ABI;
- calling convention;
- object format;
- linker policy;
- startup;
- runtime;
- platform SDK;
- default CPU;
- feature set.

---

# 588.7. Target DB versioning

Target DB phải versioned độc lập với compiler.

---

# 588.8. Target DB compatibility

Compiler chỉ sử dụng target descriptor tương thích với backend/compiler version.

---

# 588.9. Target aliases

Có thể có aliases:

```text
windows-x64
linux-x64
linux-arm64
macos-arm64
ios-arm64
android-arm64
wasm
```

nhưng compiler phải canonicalize về target ID.

---

# 588.10. Target feature resolution

```text
target
  +
cpu
  +
features
       ↓
ResolvedTarget
```

---

# 588.11. CPU baseline

Mỗi target phải xác định baseline instruction set.

---

# 588.12. CPU tuning

Có thể chỉ định:

```text
--cpu=native
--cpu=generic
--cpu=<model>
```

`native` chỉ có ý nghĩa khi compiler đang chạy trên cùng host architecture.

---

# 588.13. CPU feature compatibility

Không được generate instruction vượt baseline nếu target không khai báo feature tương ứng.

---

# 588.14. Sysroot

Sysroot là logical root chứa target-specific development artifacts:

```text
sysroot/
 ├── include/
 ├── lib/
 ├── runtime/
 ├── crt/
 ├── startup/
 ├── metadata/
 └── target.json
```

---

# 588.15. Axiom-owned sysroot

Axiom runtime/core/stdlib phải có thể tồn tại hoàn toàn trong Axiom-managed sysroot.

---

# 588.16. Native platform sysroot

Platform SDK có thể cung cấp:

- OS headers;
- ABI metadata;
- native libraries;
- framework metadata;
- linker/import information.

---

# 588.17. External SDK boundary

External platform SDK không được coi là compiler dependency.

Nó là **target SDK input**.

---

# 588.18. SDK identity

```text
SDKIdentity {
    platform
    version
    architecture
    content_hash
    abi_hash
}
```

---

# 588.19. SDK provenance

Mỗi SDK phải có provenance:

```text
source
version
license
content_hash
installation_id
```

---

# 588.20. SDK licensing

Toolchain phải phân biệt:

```text
Axiom-owned
Open-source
Platform-provided
User-provided
Restricted
```

---

# 588.21. SDK redistribution

Axiom không tự động redistribute SDK có license hạn chế.

---

# 588.22. SDK discovery

Compiler có thể tìm SDK theo:

```text
AXIOM_SDK_ROOT
configured toolchain
project manifest
system installation
```

theo thứ tự policy rõ ràng.

---

# 588.23. No accidental host SDK

Compiler không được tự động lấy SDK của host nếu target khác.

---

# 588.24. Explicit SDK selection

Project có thể pin:

```text
target_sdk = "windows-11"
sdk_version = "..."
```

---

# 588.25. SDK lock

Lockfile phải pin SDK content hash khi reproducible build yêu cầu.

---

# 588.26. Offline SDK

Một SDK đầy đủ phải có thể được cài offline từ archive đã xác minh.

---

# 588.27. Offline toolchain

Offline development phải hỗ trợ:

```text
compiler
runtime
stdlib
target DB
SDK
package cache
debug metadata
```

mà không cần network.

---

# 588.28. Toolchain bundle

Canonical bundle:

```text
axiom-toolchain/
 ├── bin/
 ├── lib/
 ├── runtime/
 ├── targets/
 ├── sdk/
 ├── sysroot/
 ├── docs/
 └── manifest/
```

---

# 588.29. Toolchain manifest

```text
ToolchainManifest {
    schema_version
    toolchain_id
    compiler
    runtime
    stdlib
    targets[]
    sdks[]
    files[]
    hashes[]
}
```

---

# 588.30. File integrity

Mỗi file quan trọng phải có content hash.

---

# 588.31. Manifest hash

Manifest có canonical serialization.

---

# 588.32. Installation verification

Installer phải verify:

```text
archive signature
manifest
file hashes
toolchain compatibility
```

trước khi activation.

---

# 588.33. Atomic installation

Installation:

```text
download/archive
      ↓
verify
      ↓
extract staging
      ↓
validate
      ↓
atomic activate
```

---

# 588.34. Partial installation

Partial toolchain không được trở thành active toolchain.

---

# 588.35. Multiple toolchains

Có thể cài:

```text
Axiom 1.x
Axiom 2.x
Axiom nightly
```

song song.

---

# 588.36. Toolchain selector

Project phải có thể chọn toolchain:

```text
toolchain = "axiom-2.0"
```

---

# 588.37. Project-local toolchain

Project có thể pin toolchain trong manifest/lockfile.

---

# 588.38. Global toolchain

User có thể có default toolchain.

---

# 588.39. Selection precedence

Canonical:

```text
explicit CLI
    >
project pin
    >
workspace config
    >
environment
    >
global default
```

---

# 588.40. Toolchain mismatch

Compiler phải báo rõ:

```text
project requires X
installed Y
```

không tự động downgrade/upgrade.

---

# 588.41. Runtime compatibility

Compiler/runtime/stdlib ABI mismatch phải là hard error.

---

# 588.42. Compiler compatibility

Compiler có thể compile project cũ theo edition compatibility policy `484`.

---

# 588.43. Runtime profiles

Toolchain phải cung cấp:

```text
minimal
freestanding
hosted
full
```

---

# 588.44. Target runtime package

Runtime được chọn theo:

```text
target
profile
features
```

---

# 588.45. Runtime feature slicing

Nếu chương trình không sử dụng:

- async;
- networking;
- GUI;
- filesystem;

runtime không được link các component tương ứng nếu linker có thể loại bỏ chúng.

---

# 588.46. Static runtime

Axiom runtime mặc định có thể static-link.

---

# 588.47. Shared runtime

Có thể cung cấp shared runtime khi ABI policy cho phép.

---

# 588.48. Runtime ABI

Runtime public ABI phải follow `421` và `447`.

---

# 588.49. Stdlib packaging

Stdlib không phải một monolithic binary.

Có thể chia module/package để linker dead-strip phần không dùng.

---

# 588.50. Core package

`core` phải là package bootstrap-safe.

---

# 588.51. Alloc package

`alloc` chứa allocator abstractions và implementations.

---

# 588.52. Platform package

Platform APIs nằm trong target-specific layer.

---

# 588.53. Std package

`std` là hosted convenience layer.

---

# 588.54. Native library import

Axiom phải hỗ trợ import:

```text
static library
shared library
framework
system library
```

theo target.

---

# 588.55. Library descriptor

```text
NativeLibrary {
    name
    target
    abi
    linkage
    symbols
    headers
    metadata
    version
}
```

---

# 588.56. Symbol metadata

Native libraries có thể cung cấp:

```text
function
global
type
constant
calling convention
visibility
```

metadata.

---

# 588.57. C library interoperability

C ABI được mô tả bởi `451`.

Không cần C compiler để link C library đã có binary.

---

# 588.58. Header import

Axiom có thể có tool chuyển C header:

```text
C header
   ↓
Axiom FFI metadata
```

nhưng đây là tooling, không phải compiler dependency.

---

# 588.59. Generated FFI metadata

Metadata phải lưu:

```text
ABI
types
layout
calling convention
symbol
```

---

# 588.60. Header preprocessing

Nếu cần preprocess C headers, tool phải được tách khỏi Axiom compiler core.

---

# 588.61. Native SDK bindings

SDK bindings có thể được generated:

```text
Platform SDK
      ↓
Binding Generator
      ↓
Axiom API
```

---

# 588.62. Binding reproducibility

Generated bindings phải deterministic.

---

# 588.63. Binding versioning

Bindings phải pin SDK version.

---

# 588.64. Framework support

macOS/iOS framework có thể được mô tả như native package:

```text
Framework {
    headers
    dylib
    resources
    metadata
}
```

---

# 588.65. Android NDK-like integration

Android target có thể sử dụng platform/NDK native libraries khi ABI compatible.

Axiom vẫn tự generate object/link/image của phần Axiom.

---

# 588.66. Windows SDK integration

Windows target có thể consume Windows SDK metadata/libs mà không sử dụng MSVC linker.

---

# 588.67. Linux system integration

Linux target có thể link system libraries theo ABI và sysroot.

---

# 588.68. macOS SDK integration

macOS target phải pin SDK version và deployment target.

---

# 588.69. iOS SDK integration

iOS target phải pin:

```text
platform
deployment target
SDK
architecture
code-signing policy
```

---

# 588.70. WASM SDK

WASM target không dùng native sysroot.

Thay vào đó:

```text
WASM imports
WASI / host API
runtime metadata
```

---

# 588.71. WASI target

WASI được mô hình hóa như target runtime/API contract.

---

# 588.72. SDK target capabilities

Target DB phải expose:

```text
supports_dynamic_linking
supports_tls
supports_threads
supports_gui
supports_signing
supports_debug
supports_unwind
```

---

# 588.73. Unsupported feature diagnostics

Nếu project yêu cầu feature target không support:

```text
error:
target does not support <feature>
```

---

# 588.74. Cross compilation

Canonical:

```text
axiom build \
    --host=x86_64-linux \
    --target=aarch64-linux
```

Host compiler chạy x86-64.

Output là AArch64.

---

# 588.75. Build triples

Build system phân biệt:

```text
build
host
target
```

cho toolchain stages.

---

# 588.76. Canadian cross

Support đầy đủ:

```text
build = A
host  = B
target = C
```

---

# 588.77. Build tools

Build tools chạy trên `host`.

---

# 588.78. Target programs

Target programs chỉ được compile cho `target`.

---

# 588.79. Build-time code generation

Codegen tool chạy host-side nếu không được đánh dấu target executable.

---

# 588.80. Target execution

Cross build không được ngầm chạy target binary trên host.

---

# 588.81. Emulator integration

Nếu cần test target binary:

```text
target binary
     ↓
configured emulator/runtime
```

được khai báo explicit.

---

# 588.82. Target test runner

```text
TestRunner {
    native
    emulator
    remote
    wasm-runtime
}
```

---

# 588.83. Remote target testing

Có thể chạy test trên remote device/server.

---

# 588.84. SDK capability resolver

Build system phải resolve:

```text project requirement
       +
target capability
       +
SDK capability
```

---

# 588.85. Dependency resolution

Dependency graph phải phân biệt:

```text host dependency
target dependency
build dependency
dev dependency
```

---

# 588.86. Host/target dependency collision

Một package có thể được build hai lần nếu nó có host và target variants.

---

# 588.87. Artifact identity

Host và target artifact không được collision cache.

---

# 588.88. Toolchain cache

Cache key gồm:

```text compiler
target
SDK
runtime
features
optimization
source
```

---

# 588.89. SDK cache

SDK archive cache phải content-addressed.

---

# 588.90. Offline cache

Cache có thể được export thành:

```text
axiom-offline-cache.bundle
```

---

# 588.91. Offline project transfer

Có thể transfer:

```text project
+
lockfile
+
toolchain bundle
+
package cache
```

sang máy offline.

---

# 588.92. Air-gapped build

Axiom phải hỗ trợ build trong environment không có network.

---

# 588.93. Air-gap manifest

Manifest phải list toàn bộ required artifacts.

---

# 588.94. Missing artifact detection

Build phải fail trước compilation nếu dependency offline chưa đủ.

---

# 588.95. SDK integrity

SDK được verify trước khi compiler dùng metadata/libraries.

---

# 588.96. ABI database

Axiom cần canonical ABI database:

```text
ABI
 ├── calling convention
 ├── type layout
 ├── alignment
 ├── mangling
 ├── exception/unwind
 ├── TLS
 └── object/link rules
```

---

# 588.97. ABI version

ABI version phải explicit.

---

# 588.98. ABI compatibility

Binary compatibility chỉ được claim khi ABI contract tương thích.

---

# 588.99. ABI break

ABI-breaking change phải tăng ABI version.

---

# 588.100. Symbol mangling

Axiom symbol mangling phải versioned.

---

# 588.101. Stable external symbols

`extern "C"` hoặc equivalent phải bypass Axiom mangling khi ABI yêu cầu.

---

# 588.102. Native import validation

Linker phải verify:

```text symbol
ABI
architecture
relocation
calling convention
```

trước link.

---

# 588.103. Incompatible native library

Không được link chỉ vì symbol name trùng.

---

# 588.104. Library target verification

Static/shared library phải match target architecture/object format.

---

# 588.105. Fat libraries

Nếu library chứa nhiều architecture slices, linker phải select đúng slice.

---

# 588.106. Mach-O universal binaries

Universal binary có thể chứa:

```text x86_64
arm64
```

slices.

---

# 588.107. Universal binary construction

Axiom image tool có thể merge independently verified Mach-O slices.

---

# 588.108. Slice independence

Mỗi slice phải pass image verification riêng trước khi merge.

---

# 588.109. Universal binary ordering

Slice ordering phải deterministic.

---

# 588.110. Target SDK package layout

Canonical:

```text
sdk/
 └── <target>/
      ├── include/
      ├── lib/
      ├── frameworks/
      ├── metadata/
      ├── sysroot/
      └── manifest
```

---

# 588.111. Target runtime layout

```text
runtime/
 └── <target>/
      ├── core
      ├── alloc
      ├── std
      └── startup
```

---

# 588.112. Compiler target layout

```text
targets/
 ├── x86_64-linux
 ├── x86_64-windows
 ├── aarch64-linux
 ├── aarch64-macos
 ├── aarch64-ios
 └── wasm32
```

---

# 588.113. Target descriptor format

Descriptor phải machine-readable, versioned và deterministic.

---

# 588.114. Target extension

Adding a new target không được yêu cầu sửa parser/type system nếu backend abstractions đủ.

---

# 588.115. Target plugin

Target backend có thể được distributed separately nhưng phải follow compiler plugin/security policy.

---

# 588.116. Built-in targets

Core distribution nên có các target phổ biến.

---

# 588.117. Optional targets

Platform-specific SDKs có thể cài riêng.

---

# 588.118. Minimal compiler install

Compiler chỉ cần:

```text compiler
core target database
minimal runtime metadata
```

để compile basic programs.

---

# 588.119. Full developer install

Full installation có thêm:

```text LSP
formatter
debug integration
package manager
SDKs
docs
AI metadata
```

---

# 588.120. Toolchain components

CLI phải có thể query:

```text
axiom toolchain list
axiom target list
axiom sdk list
axiom runtime list
```

---

# 588.121. Machine-readable toolchain query

Tất cả phải hỗ trợ JSON hoặc canonical machine-readable format.

---

# 588.122. Toolchain environment

Có thể export:

```text
AXIOM_HOME
AXIOM_TOOLCHAIN
AXIOM_TARGET
AXIOM_SDK_ROOT
```

nhưng project configuration có precedence cao hơn environment.

---

# 588.123. No global mutation

Project build không được tự sửa global toolchain.

---

# 588.124. Toolchain isolation

Mỗi build có resolved immutable toolchain context.

---

# 588.125. Build context

```text
BuildContext {
    compiler
    target
    sdk
    runtime
    dependencies
    features
    environment
}
```

---

# 588.126. Build context hash

Build context có canonical hash.

---

# 588.127. Artifact cache

Artifact cache key phải include BuildContext hash.

---

# 588.128. SDK update

SDK update không được silently invalidate compatibility metadata.

---

# 588.129. SDK pinning

Project có thể pin exact SDK.

---

# 588.130. SDK range

Có thể yêu cầu:

```text
SDK >= X < Y
```

nhưng reproducible release nên pin exact version/hash.

---

# 588.131. Toolchain lockfile

Lockfile phải record:

```text
compiler
runtime
stdlib
SDK
native dependencies
package dependencies
```

---

# 588.132. Toolchain resolver

Resolver phải fail deterministically nếu không thể satisfy constraints.

---

# 588.133. Offline resolver

Resolver chỉ dùng local index/cache khi offline.

---

# 588.134. Package registry independence

Axiom compiler không phụ thuộc registry để compile core language.

---

# 588.135. Toolchain bootstrap independence

Toolchain SDK không phụ thuộc package registry để rebuild compiler.

---

# 588.136. Installer trust

Installer chỉ activate toolchain sau verification.

---

# 588.137. Toolchain signing

Official toolchains có thể signed.

---

# 588.138. Signature vs hash

Hash xác định content.

Signature xác định trusted publisher.

Hai khái niệm không được trộn.

---

# 588.139. Toolchain revocation

Compromised toolchain có thể revoked theo `587`.

---

# 588.140. Toolchain provenance

Toolchain manifest phải reference bootstrap verification report.

---

# 588.141. Compiler-to-SDK compatibility

Compiler phải reject SDK incompatible với target DB/ABI.

---

# 588.142. Runtime-to-SDK compatibility

Runtime platform layer phải match SDK ABI.

---

# 588.143. SDK-to-linker compatibility

Linker phải biết SDK relocation/import/export requirements.

---

# 588.144. SDK-to-image compatibility

Image builder phải biết target image requirements.

---

# 588.145. Platform signing

Signing tools có thể nằm ngoài compiler nhưng phải ở post-link boundary.

---

# 588.146. Signing SDK

iOS/Windows/macOS signing integration phải không làm compiler phụ thuộc proprietary compiler.

---

# 588.147. Signing boundary

```text
Compile
 ↓
Link
 ↓
Image
 ↓
Verify
 ↓
Sign
 ↓
Package
```

---

# 588.148. Package boundary

Installer/application packaging không được thay đổi executable semantics sau verification.

---

# 588.149. Package reproducibility

Packaging có deterministic mode.

---

# 588.150. Final toolchain architecture

```text id="final588"
                 Toolchain
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
   Compiler        Linker        Tools
       │             │
       └──────┬──────┘
              ▼
         Target DB
              │
       ┌──────┴──────┐
       ▼             ▼
     Sysroot        SDK
       │             │
       └──────┬──────┘
              ▼
         Runtime/Std
              │
              ▼
       Native Artifacts
              │
              ▼
       Verify / Sign / Package
```

---

# 588.151. FINAL HARD INVARIANTS

### Invariant 1 — target isolation

> Compiler không được dùng nhầm host ABI/SDK/runtime cho target.

### Invariant 2 — toolchain closure

> Một resolved toolchain phải xác định đầy đủ compiler, runtime, stdlib, target DB, SDK và native dependencies cần thiết.

### Invariant 3 — reproducibility

> Cùng source + toolchain identity + target + configuration phải tạo cùng semantic artifact và deterministic binary khi reproducible mode được bật.

### Invariant 4 — offline

> Toolchain đã được đóng gói đầy đủ phải build được project mà không cần network.

### Invariant 5 — external SDK

> Platform SDK là input của toolchain, không biến compiler thành frontend/backend phụ thuộc compiler của platform.

### Invariant 6 — native interoperability

> Axiom phải link được native libraries theo ABI mà không cần external compiler/linker.

### Invariant 7 — trust

> Chỉ toolchain đã pass verification mới được đánh dấu trusted.

### Invariant 8 — atomicity

> Toolchain installation/update không được để lại active installation ở trạng thái nửa cũ/nửa mới.

### Invariant 9 — ABI

> Mọi native artifact phải được kiểm tra architecture + ABI + object format trước khi link.

### Invariant 10 — self-contained compiler

> Compiler core không được phụ thuộc vào SDK hoặc runtime hosted không cần thiết để tự bootstrap.

---

# 588 — LOCKED

Sau `588`, Axiom có đủ ba tầng:

```text
586
SELF-HOSTING
      ↓
587
TRUSTED BOOTSTRAP
      ↓
588
DISTRIBUTABLE TOOLCHAIN
```

Tức là:

```text
Axiom source
    ↓
Axiom compiler tự xây
    ↓
compiler được kiểm chứng
    ↓
đóng gói thành SDK/toolchain
    ↓
cài trên máy khác
    ↓
cross-compile native target
    ↓
không cần GCC/Clang/MSVC/LLVM làm compiler
```

---

# NEXT — BOOTSTRAP-589

## NATIVE DEBUGGER & DEBUGGING TOOLCHAIN 4.0
### BREAKPOINTS, WATCHPOINTS, REGISTER/STACK INSPECTION, DWARF/CODEVIEW, SOURCE MAPS, SYMBOLS, UNWINDING, REMOTE DEBUGGING, CRASH DUMPS & AXIOM-AWARE DEBUG SEMANTICS

```text id="next589"
                 Axiom Program
                       │
                       ▼
                Native Executable
                       │
              ┌────────┴────────┐
              ▼                 ▼
          Debug Info         Runtime
              │                 │
              └────────┬────────┘
                       ▼
                  Debug Engine
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
    Breakpoints     Registers       Memory
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 Stack / Unwind
                       │
                       ▼
                Source Mapping
                       │
                       ▼
               Axiom Debugger
```

`589` sẽ đưa Axiom từ trạng thái **compiler/toolchain hoàn chỉnh** sang trạng thái **developer toolchain hoàn chỉnh**: có thể debug native code do chính Axiom sinh ra, hiểu struct/trait/generic/async/ownership/drop/closure/comptime và vẫn ánh xạ chính xác về source Axiom thay vì chỉ hiển thị machine code.