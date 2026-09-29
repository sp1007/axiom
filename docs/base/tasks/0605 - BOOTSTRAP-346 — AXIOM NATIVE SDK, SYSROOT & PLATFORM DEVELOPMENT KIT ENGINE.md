# BOOTSTRAP-346 — AXIOM NATIVE SDK, SYSROOT & PLATFORM DEVELOPMENT KIT ENGINE

Đây là bước tiếp theo hợp lý sau **345 — Language Evolution, Edition, Compatibility & Deprecation Engine**.

Mục tiêu của task này là giải quyết một vấn đề rất quan trọng còn thiếu trong kiến trúc Axiom:

> **Compiler đã biết cách tạo PE/ELF/Mach-O, nhưng lấy system headers, ABI definitions, startup objects, CRT, system libraries, frameworks, linker metadata và target SDK từ đâu?**

Axiom muốn cuối cùng **không phụ thuộc compiler bên thứ ba**, nhưng điều đó **không có nghĩa Axiom phải tự viết lại Windows, Linux, Darwin, Android SDK**. Axiom cần một lớp **Native SDK/Sysroot abstraction** rõ ràng.

---

# 1. Mục tiêu

`BOOTSTRAP-346` xây dựng hệ thống:

> **Axiom Native SDK + Sysroot + Platform Development Kit**

cho phép compiler xây dựng chương trình native mà không cần biết chi tiết riêng của từng OS.

Ví dụ:

```text
axiom build app.ax
        │
        ▼
TargetResolver
        │
        ├── x86_64-windows-msvc
        ├── x86_64-linux-gnu
        ├── aarch64-linux-gnu
        ├── arm64-macos
        ├── arm64-ios
        ├── arm64-android
        └── wasm32-wasi
        │
        ▼
PlatformSDK
        │
        ├── Sysroot
        ├── ABI
        ├── CRT
        ├── System APIs
        ├── Libraries
        ├── Frameworks
        ├── Startup Objects
        └── Linker Metadata
        │
        ▼
Axiom Linker
        │
        ▼
Native Binary
```

Compiler không được hard-code:

```text
C:\Windows...
/usr/include...
/System/Library/Frameworks...
```

thành logic ngôn ngữ.

---

# 2. Phân biệt Compiler / SDK / Sysroot

Đây là distinction bắt buộc.

## Compiler

Biết:

- Axiom semantics
- type system
- ownership
- MIR
- optimization
- machine code
- object format
- ABI rules
- linker

Compiler **không sở hữu toàn bộ OS API**.

---

## SDK

Biết:

- OS API
- system libraries
- headers/metadata
- frameworks
- ABI contracts
- startup model
- SDK version
- target capabilities

Ví dụ:

```text
Windows SDK
Linux Sysroot
Android NDK/Platform SDK
Apple SDK
WASI SDK
```

---

## Sysroot

Sysroot là **filesystem/metadata boundary của target system**.

Ví dụ:

```text
sysroot/
    include/
    lib/
    libexec/
    frameworks/
    usr/
    target.json
    abi.axsdk
```

Nhưng Axiom không bắt buộc sysroot phải giống Unix filesystem.

Sysroot về semantic level là:

> **một tập hợp tài nguyên platform được compiler/linker phép sử dụng.**

---

# 3. Không để C trở thành dependency ngầm

Một nguyên tắc rất quan trọng:

> **Axiom không được biến C headers thành semantic foundation.**

Ví dụ không nên có:

```text
Axiom
  ↓
C compiler
  ↓
C headers
  ↓
system ABI
```

Thay vào đó:

```text
Axiom
  ↓
Axiom Platform Contract
  ↓
Native SDK
  ↓
OS ABI
```

C compatibility chỉ là **một adapter**:

```text
Axiom
   │
   ├── Native Axiom ABI
   │
   ├── C ABI adapter
   │
   ├── C++ ABI adapter
   │
   └── Platform-specific ABI
```

Điều này rất quan trọng đối với mục tiêu self-hosting.

---

# 4. Native SDK Artifact

Định dạng SDK của Axiom nên có metadata machine-readable.

Ví dụ:

```text
Windows-x86_64-10.0.axsdk
Linux-x86_64-glibc-2.39.axsdk
macOS-arm64-15.axsdk
iOS-arm64-18.axsdk
Android-arm64-35.axsdk
```

Một SDK manifest:

```text
SdkManifest {
    sdk_id
    platform
    architecture
    abi
    os_version
    sdk_version

    sysroot
    libraries
    frameworks
    startup_objects

    crt
    linker_contract

    headers
    ffi_metadata

    capabilities

    minimum_os_version
    deployment_target

    fingerprint
}
```

---

# 5. SDK fingerprint

SDK phải có fingerprint.

```text
SdkFingerprint =
    hash(
        platform
        + architecture
        + ABI
        + OS version
        + SDK version
        + library ABI
        + startup objects
        + metadata
    )
```

Build artifact phải ghi lại:

```text
CompilerFingerprint
LanguageEdition
TargetTriple
SDKFingerprint
ABIRevision
```

Nhờ đó:

```text
same source
same compiler
same SDK
same configuration
        ↓
same semantic build
```

hoặc nếu khác SDK:

```text
SDK changed
    ↓
build invalidation
```

---

# 6. SDK không chỉ là headers

Một SDK hoàn chỉnh gồm nhiều lớp.

```text
Native SDK
│
├── Target Definition
├── ABI Contract
├── Type Layout
├── Calling Convention
├── System API
├── FFI Metadata
├── Startup
├── CRT
├── System Libraries
├── Frameworks
├── Linker Inputs
├── Runtime Contracts
├── Deployment Constraints
└── Debug/Tool Metadata
```

Ví dụ Windows:

```text
kernel32
user32
advapi32
ntdll
ucrt
vcruntime
ws2_32
```

macOS:

```text
Foundation
CoreFoundation
Metal
AppKit
UIKit
System frameworks
```

Linux:

```text
libc
libpthread
libdl
libm
libgcc_s / compiler runtime equivalent
kernel ABI
```

Axiom phải nhìn chúng như **platform components**, không phải các thư viện đặc biệt của compiler.

---

# 7. Platform Contract

Mỗi target có một `PlatformContract`.

Ví dụ:

```text
PlatformContract {
    target
    abi
    object_format
    executable_format

    pointer_width
    endianness

    calling_convention
    stack_alignment

    tls_model

    executable_entry
    dynamic_loader

    exception_model
    unwind_model

    atomic_capabilities

    page_size
    virtual_address_model

    syscall_model

    crt_model

    debug_format
}
```

Ví dụ:

```text
x86_64-linux-gnu
```

có thể có:

```text
object_format = ELF64
endianness = little
pointer_width = 64
calling_convention = SysV_AMD64
tls = ELF_TLS
loader = ld-linux-x86-64.so.2
```

Trong khi:

```text
x86_64-windows-msvc
```

có:

```text
object_format = PE64
calling_convention = Win64
loader = Windows Loader
tls = PE_TLS
```

---

# 8. Target Triple chưa đủ

Axiom không nên chỉ dùng:

```text
x86_64-linux
```

vì ABI có thể khác.

Nên có:

```text
TargetSpec {
    architecture
    vendor
    os
    environment
    abi
    object_format
    sdk
    deployment_target
    cpu_features
}
```

Ví dụ:

```text
x86_64-linux-gnu
x86_64-linux-musl
x86_64-windows-msvc
x86_64-windows-gnu
aarch64-linux-gnu
aarch64-android
arm64-apple-macos
arm64-apple-ios
wasm32-wasi
```

---

# 9. SDK Capability Model

SDK không chỉ cung cấp file.

Nó phải mô tả capability.

Ví dụ:

```text
Capability {
    filesystem
    networking
    threads
    processes
    virtual_memory
    shared_library
    gpu
    gui
    audio
    camera
    crypto
    sandbox
}
```

Compiler có thể kiểm tra:

```text
@requires(network)
fn connect(...)
```

và target không hỗ trợ:

```text
error AXSDK401:
target does not provide capability `network`
```

Điều này đặc biệt hữu ích cho cross compilation.

---

# 10. FFI Metadata thay cho header parsing

Axiom nên ưu tiên:

```text
SDK
  ↓
.axffi / .axif
  ↓
Axiom compiler
```

thay vì:

```text
SDK
  ↓
C header parser
  ↓
guess ABI
```

Ví dụ:

```text
extern "C" fn CreateFileW(
    name: *const u16,
    access: u32,
    ...
) -> Handle
```

metadata có thể chứa:

```text
Function {
    name
    abi
    calling_convention
    parameters
    return_type
    nullable_contract
    ownership
    thread_safety
    availability
    introduced
    deprecated
}
```

Compiler vì vậy biết nhiều hơn C compiler header parser thông thường.

---

# 11. API Availability

Platform API thường phụ thuộc OS version.

Axiom phải hỗ trợ:

```text
@available(windows >= 10.0)
fn new_api()
```

hoặc metadata tương đương.

Compiler biết:

```text
deployment_target = Windows 10
```

và có thể báo lỗi nếu chương trình gọi API chỉ tồn tại trên Windows 11.

Tương tự:

```text
@available(ios >= 18)
@available(macos >= 15)
@available(android >= 35)
```

Không nên biến đây thành runtime reflection.

---

# 12. Weak / Optional Platform APIs

Một số platform API có thể optional.

Axiom nên phân biệt:

```text
Required
Optional
WeakLinked
RuntimeResolved
```

Ví dụ:

```text
if platform.has("SomeNewAPI") {
    ...
}
```

Compiler có thể tạo binding đúng ABI.

Không nên bắt programmer tự thao tác symbol lookup trừ khi họ thực sự muốn.

---

# 13. CRT Model

CRT là một phần cực kỳ quan trọng.

Axiom phải hỗ trợ:

```text
CRT {
    none
    minimal
    system
    static
    dynamic
    axiom
}
```

Ví dụ chương trình freestanding:

```text
@freestanding
fn _start() -> never
```

có thể không cần CRT.

Hosted application:

```text
fn main() {
}
```

có thể sử dụng startup contract của target.

Compiler quyết định startup sequence.

---

# 14. Axiom Runtime và Platform SDK phải tách nhau

Đây là invariant quan trọng:

```text
Platform SDK != Axiom Runtime
```

Ví dụ:

```text
Windows SDK
      │
      ├── OS API
      ├── kernel ABI
      └── system libraries

Axiom Runtime
      │
      ├── panic
      ├── allocator
      ├── async
      ├── threading
      └── reflection
```

Chương trình:

```text
@freestanding
```

có thể dùng:

```text
Windows SDK
```

nhưng không dùng:

```text
Axiom Runtime
```

---

# 15. Startup Contract

Mỗi executable format cần startup abstraction.

```text
StartupContract {
    entry_symbol
    stack_initialization
    argc_argv
    environment
    tls_initialization
    runtime_initialization
    static_initialization
    exit_contract
}
```

Compiler có thể sinh:

```text
_start
main
WinMain
DllMain
JNI_OnLoad
WASM entry
```

theo target.

Programmer không cần biết chi tiết trừ khi viết low-level code.

---

# 16. Static và Dynamic Linking

SDK phải mô tả:

```text
Library {
    name
    kind
    abi
    architecture

    static_path
    dynamic_path
    import_library

    dependencies
    symbols
    version
}
```

Các loại:

```text
Static
Shared
Framework
ImportLibrary
System
Weak
DelayLoad
```

Ví dụ Windows:

```text
user32.lib
```

có thể là:

```text
kind = ImportLibrary
runtime = user32.dll
```

Axiom linker hiểu trực tiếp.

---

# 17. Framework abstraction

Apple và một số platform có framework model.

Không nên ép framework thành library giả.

```text
Framework {
    name
    version
    binary
    headers
    modules
    resources
    dependencies
}
```

Ví dụ:

```text
Foundation
Metal
UIKit
AppKit
```

Compiler/linker biết đây là platform component.

---

# 18. SDK Selection

CLI:

```bash
axiom sdk list
axiom sdk show
axiom sdk install
axiom sdk remove
axiom sdk select
axiom sdk verify
```

Build:

```bash
axiom build --target arm64-apple-ios
```

Compiler tự resolve:

```text
Target
  ↓
SDK requirement
  ↓
Installed SDK
  ↓
compatible SDK
```

Nếu không có:

```text
AXSDK001: required SDK is not installed
```

không được âm thầm dùng SDK khác.

---

# 19. SDK Lock

Project có thể khóa SDK:

```text
axiom.sdk.lock
```

Ví dụ:

```text
sdk:
    target: aarch64-android
    version: 35
    fingerprint: ...
```

CI sẽ không vô tình build bằng SDK mới.

---

# 20. SDK Resolution

Resolution nên giống package resolution nhưng có semantics khác.

```text
Project
  │
  ├── target
  ├── minimum_os
  ├── sdk_constraint
  └── abi_constraint
           │
           ▼
      SDK Resolver
           │
           ├── Installed SDKs
           ├── Compatibility
           ├── ABI
           └── Deployment Target
           │
           ▼
       Selected SDK
```

Không cho phép:

```text
SDK version 20
```

thay thế tự động:

```text
SDK version 18
```

nếu compatibility chưa được chứng minh.

---

# 21. SDK Import

Axiom có thể tạo metadata từ native SDK.

Nhưng import phải là **một bước biên dịch rõ ràng**:

```bash
axiom sdk import windows-sdk ...
```

sinh:

```text
windows.axsdk
windows.axffi
windows.axif
```

Sau đó compiler sử dụng artifact đã chuẩn hóa.

Điều này giúp:

- build nhanh
- reproducibility
- không parse header mỗi lần
- diagnostics tốt hơn
- ABI verification

---

# 22. Không phụ thuộc hệ điều hành đang chạy compiler

Ví dụ cross compile:

```text
Windows host
      ↓
Axiom compiler
      ↓
aarch64-linux SDK
      ↓
ELF
```

hoặc:

```text
Linux host
      ↓
Axiom compiler
      ↓
Windows SDK
      ↓
PE
```

Compiler không được giả định:

```text
host OS == target OS
```

---

# 23. SDK Bundle

Axiom nên hỗ trợ portable SDK:

```text
sdk/
    manifest.axsdk
    target/
    abi/
    ffi/
    sysroot/
    lib/
    framework/
    startup/
```

Có thể đặt trong:

```text
project/.axiom/sdk/
```

hoặc:

```text
~/.axiom/sdk/
```

CI có thể dùng bundle offline.

---

# 24. Hermetic SDK

Kết hợp với `BOOTSTRAP-331`:

```text
Hermetic Build
    ↓
Compiler
    ↓
Locked SDK
    ↓
Locked packages
    ↓
Locked target
```

Build không được đọc:

```text
random system headers
random /usr/lib
random PATH executable
```

trừ khi project khai báo rõ.

---

# 25. SDK provenance

Mỗi SDK phải ghi:

```text
source
publisher
version
fingerprint
creation_time
toolchain_origin
license
signature
```

Có thể verify:

```bash
axiom sdk verify windows-11
```

Kết quả:

```text
SDK integrity: PASS
ABI metadata: PASS
Manifest signature: PASS
Fingerprint: ...
```

---

# 26. Native dependency graph

SDK dependency phải trở thành một phần Build Graph:

```text
Application
   │
   ├── Axiom Package
   ├── Axiom Runtime
   ├── SDK
   │    ├── libc
   │    ├── system API
   │    └── startup
   │
   └── platform libraries
```

Compiler/linker biết chính xác binary phụ thuộc gì.

---

# 27. Binary dependency validation

Sau khi link:

```text
axiom inspect app.exe
```

có thể hiển thị:

```text
Executable: app.exe

Target:
    x86_64-windows

SDK:
    Windows 11 SDK
    fingerprint: ...

Dynamic Dependencies:
    kernel32.dll
    user32.dll
    ucrtbase.dll

Axiom Runtime:
    none

Third-party:
    none
```

Điều này rất phù hợp mục tiêu **binary nhỏ và dependency minh bạch**.

---

# 28. SDK và GPU

GPU SDK cũng đi qua cùng abstraction.

Ví dụ:

```text
GPU SDK
 ├── CUDA
 ├── Vulkan
 ├── Metal
 ├── DirectX
 └── ROCm
```

Axiom không hard-code chúng vào GPU semantic core.

Thay vào đó:

```text
GPU Core
    ↓
GPU ABI
    ↓
GPU SDK Adapter
```

Ví dụ:

```text
@kernel
fn add(...)
```

có thể lower tới:

```text
CUDA
Metal
SPIR-V
DXIL
```

tùy target.

---

# 29. SDK và WASM

WASM cũng được coi là target SDK.

Ví dụ:

```text
wasm32-bare
wasm32-wasi
wasm32-component
```

SDK cung cấp:

```text
WASI ABI
syscalls
component interfaces
runtime contracts
```

Axiom language semantics không cần biết WASI cụ thể.

---

# 30. SDK Database

Bổ sung vào `CompilerDB`:

```text
SdkDB
TargetSdkDB
SysrootDB
PlatformContractDB
AbiContractDB
SdkManifestDB
SdkFingerprintDB
SdkComponentDB
SdkLibraryDB
SdkFrameworkDB
SdkStartupDB
SdkAvailabilityDB
SdkCapabilityDB
SdkResolutionDB
SdkLockDB
SdkProvenanceDB
SdkImportDB
SdkCacheDB
```

Quan hệ:

```text
Target
   ↓
TargetSdk
   ↓
SdkManifest
   ↓
PlatformContract
   ↓
Sysroot
   ↓
Libraries / Frameworks / Startup
   ↓
ABI / FFI
```

---

# 31. Compiler pipeline integration

Pipeline hiện tại:

```text
Source
 ↓
Parser
 ↓
Resolver
 ↓
HIR
 ↓
Typed HIR
 ↓
MIR
 ↓
Verification
 ↓
Optimization
 ↓
ABI MIR
 ↓
LIR
 ↓
Machine Code
 ↓
Object
 ↓
Linker
 ↓
Executable
```

bổ sung:

```text
Target Resolver
      ↓
SDK Resolver
      ↓
Platform Contract
      ↓
ABI Contract
      ↓
FFI Metadata
      ↓
Link Inputs
```

được sử dụng xuyên suốt nhưng **không làm thay đổi semantic core của Axiom**.

---

# 32. SDK không được ảnh hưởng semantic core

Ví dụ:

```text
Option<T>
Result<T,E>
struct
enum
trait
ownership
view
mut_view
async
match
```

phải có semantics giống nhau trên:

```text
Windows
Linux
macOS
iOS
Android
WASM
```

Khác biệt platform chỉ xuất hiện ở:

```text
ABI
layout
FFI
system APIs
target capabilities
runtime
startup
```

---

# 33. Freestanding Profile

Axiom phải có profile:

```text
freestanding
```

Ví dụ:

```text
target = x86_64-unknown-none
runtime = none
sdk = none
crt = none
```

vẫn có thể compile:

```text
@entry
fn _start() {
    ...
}
```

Điều này rất quan trọng cho:

- kernel
- bootloader
- firmware
- embedded
- hypervisor
- bare-metal
- OS development

---

# 34. Hosted Profile

Ngược lại:

```text
hosted
```

có:

```text
OS
SDK
CRT
runtime
filesystem
threads
network
```

nhưng tất cả đều optional theo dependency.

Không có:

```text
monolithic Axiom runtime
```

---

# 35. Embedded SDK

Cùng hệ thống này có thể hỗ trợ:

```text
arm-none-eabi
riscv32
riscv64
```

SDK có:

```text
startup
linker script
memory map
interrupt vector
peripherals
ABI
device registers
```

Axiom có thể tạo:

```text
firmware.bin
firmware.elf
```

mà không cần C compiler.

---

# 36. Linker Script Contract

Một số target cần linker script.

Axiom không nên coi linker script là một file text ngẫu nhiên.

Có thể có:

```text
MemoryRegion
SectionPlacement
EntryPoint
SymbolDefinition
LoadAddress
VirtualAddress
Alignment
```

Semantic model:

```text
MemoryLayout {
    FLASH { origin, size }
    RAM   { origin, size }

    .text  -> FLASH
    .rodata -> FLASH
    .data  -> RAM AT FLASH
    .bss   -> RAM
}
```

Sau đó linker sinh script/object layout phù hợp target.

---

# 37. SDK-level ABI Verification

Trước khi link:

```text
Axiom FFI signature
        ↓
SDK ABI declaration
        ↓
verify
```

Kiểm tra:

- calling convention
- parameter layout
- return layout
- alignment
- size
- enum representation
- struct layout
- symbol
- linkage
- availability
- unwind
- TLS
- variadic ABI

Sai:

```text
AXSDKABI021:
FFI declaration does not match SDK ABI contract
```

---

# 38. Security boundary

SDK là một trust boundary.

Không được mặc định tin:

```text
downloaded SDK
```

Phải có:

```text
SDK provenance
signature
hash
manifest
ABI verification
```

Compiler không thực thi code SDK chỉ để hiểu metadata.

---

# 39. CLI hoàn chỉnh

```bash
axiom sdk list
axiom sdk show <sdk>
axiom sdk install <sdk>
axiom sdk remove <sdk>
axiom sdk select <sdk>
axiom sdk verify <sdk>
axiom sdk inspect <sdk>

axiom target list
axiom target show <target>
axiom target check <target>

axiom sysroot show <target>
axiom abi show <target>
axiom ffi inspect <library>
```

Build:

```bash
axiom build \
    --target aarch64-linux-gnu \
    --sdk linux-aarch64-2026
```

---

# 40. Machine-readable SDK contract

Một SDK tối thiểu có thể:

```text
SdkManifest {
    id: "linux-aarch64-gnu"
    version: "1"
    
    target {
        arch: aarch64
        os: linux
        abi: gnu
        object: elf64
    }

    deployment {
        minimum: "6.1"
    }

    crt {
        kind: system
    }

    libraries [
        libc,
        libm,
        libdl
    ]

    startup {
        entry: "_start"
    }

    capabilities [
        threads,
        filesystem,
        networking,
        virtual_memory
    ]
}
```

---

# 41. Invariants

### `ASDK-01`
Compiler target resolution must be independent from host OS.

### `ASDK-02`
SDK identity must include ABI-relevant configuration.

### `ASDK-03`
Compiler must never silently substitute an incompatible SDK.

### `ASDK-04`
SDK must be fingerprintable.

### `ASDK-05`
Build graph must record SDK dependency.

### `ASDK-06`
SDK metadata must be machine-readable.

### `ASDK-07`
SDK metadata must not require executing untrusted code.

### `ASDK-08`
Platform ABI must be explicitly represented.

### `ASDK-09`
FFI declarations must be checked against SDK ABI contracts.

### `ASDK-10`
SDK version must be independently versioned from Axiom language version.

### `ASDK-11`
Language semantics must not depend on a particular OS SDK.

### `ASDK-12`
Runtime and SDK must remain separate.

### `ASDK-13`
Freestanding targets must be able to use no SDK.

### `ASDK-14`
Hosted targets may use SDK without mandatory Axiom runtime.

### `ASDK-15`
Static and dynamic dependencies must be represented explicitly.

### `ASDK-16`
Frameworks are first-class platform components.

### `ASDK-17`
SDK availability constraints must be represented semantically.

### `ASDK-18`
Cross compilation must resolve target SDK independently of host.

### `ASDK-19`
SDK lock state must participate in reproducible builds.

### `ASDK-20`
SDK provenance must be inspectable.

### `ASDK-21`
SDK corruption or fingerprint mismatch must invalidate the build.

### `ASDK-22`
ABI mismatch must fail before unsafe binary emission.

### `ASDK-23`
System libraries must not be treated as Axiom packages.

### `ASDK-24`
C headers are adapters, not the semantic foundation of Axiom FFI.

### `ASDK-25`
SDK components must be individually addressable in the dependency graph.

### `ASDK-26`
Target deployment constraints must be validated.

### `ASDK-27`
Linker inputs must originate from resolved SDK/package dependencies.

### `ASDK-28`
Freestanding startup and hosted startup are distinct contracts.

### `ASDK-29`
GPU SDKs must integrate through the same target/SDK abstraction.

### `ASDK-30`
SDK resolution must be deterministic under a locked configuration.

---

# 42. Definition of Done

`BOOTSTRAP-346` chỉ hoàn thành khi Axiom có:

```text
✓ TargetSpec
✓ PlatformContract
✓ SDK manifest
✓ SDK fingerprint
✓ Sysroot abstraction
✓ SDK resolver
✓ SDK lock
✓ SDK provenance
✓ SDK component model
✓ System library model
✓ Framework model
✓ Startup contract
✓ CRT model
✓ FFI metadata integration
✓ ABI verification
✓ API availability
✓ Cross-target SDK selection
✓ Hermetic SDK mode
✓ Freestanding SDK-less mode
✓ Hosted SDK mode
✓ Embedded SDK model
✓ GPU SDK model
✓ WASM SDK model
✓ Linker SDK integration
✓ Binary dependency inspection
✓ SDK CLI
✓ CompilerDB integration
✓ Conformance tests
✓ Reproducible-build integration
```

---

# 43. Kiến trúc sau BOOTSTRAP-346

Axiom lúc này có một chuỗi rất rõ:

```text
Axiom Language
       │
       ▼
Language Edition
       │
       ▼
Compiler
       │
       ▼
Target Specification
       │
       ▼
Native SDK
       │
       ├── Platform ABI
       ├── Sysroot
       ├── FFI
       ├── CRT
       ├── Startup
       ├── System Libraries
       └── Frameworks
       │
       ▼
Axiom Linker
       │
       ▼
Native Binary
```

Điểm quan trọng nhất của task này là nó hoàn thiện một phần còn thiếu trong mục tiêu **“Axiom cuối cùng tự chủ về compiler/toolchain”**:

> **Axiom compiler không cần một C compiler để hiểu platform. Nó chỉ cần Platform SDK đã được chuẩn hóa thành semantic/ABI metadata và native binary components.**

Và từ đây, Axiom có thể tiến tới các task cấp cao hơn mà không còn phải quay lại giải quyết nền tảng SDK/target mỗi lần thêm một OS mới.