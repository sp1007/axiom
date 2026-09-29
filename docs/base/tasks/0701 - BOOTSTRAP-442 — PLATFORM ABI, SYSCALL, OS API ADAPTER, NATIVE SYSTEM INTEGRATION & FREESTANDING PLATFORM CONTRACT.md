# BOOTSTRAP-442 — PLATFORM ABI, SYSCALL, OS API ADAPTER, NATIVE SYSTEM INTEGRATION & FREESTANDING PLATFORM CONTRACT

**Trạng thái: COMPLETED / LOCKED**

BOOTSTRAP-441 đã xác định runtime là capability layer. 442 đi sâu hơn vào câu hỏi:

> **Axiom gọi trực tiếp operating system như thế nào mà không cần libc, C runtime hoặc compiler bên thứ ba?**

Kiến trúc khóa:

```text
Axiom source
    │
    ▼
Standard API
    │
    ▼
Platform abstraction
    │
    ├── Windows
    ├── Linux
    ├── macOS
    ├── iOS
    ├── Android
    ├── WASM
    └── Bare Metal
    │
    ▼
Native ABI / Syscall / OS framework
    │
    ▼
CPU / Kernel / Firmware
```

Điểm quan trọng:

```text
Language Core
    ≠
Standard Library
    ≠
Platform API
    ≠
Syscall
```

Không được trộn bốn tầng này thành một runtime monolithic.

---

## 442.1 — Platform ABI

Axiom định nghĩa:

```text
PlatformABI {
    os
    architecture
    object_format
    calling_convention
    syscall_abi
    native_api_abi
    tls_model
    exception_model
    executable_model
}
```

---

## 442.2 — Target Triple

Target được định danh bằng:

```text
architecture-vendor-os-environment
```

Ví dụ conceptual:

```text
x86_64-unknown-linux
x86_64-pc-windows
aarch64-apple-macos
aarch64-apple-ios
aarch64-linux-android
wasm32-unknown-wasm
```

Tên chính xác của triple có thể được chuẩn hóa sau.

---

## 442.3 — Target không chỉ là OS

Compiler phải phân biệt:

```text
CPU architecture
OS
ABI
environment
object format
CPU features
```

---

## 442.4 — Target descriptor

```text
Target {
    arch
    endian
    pointer_width
    os
    abi
    object_format
    features
}
```

---

## 442.5 — Native API

Native API là API của OS/framework.

Ví dụ:

```text
Windows API
POSIX/Linux APIs
Apple system frameworks
Android NDK interfaces
```

Axiom có thể bind trực tiếp qua ABI.

---

## 442.6 — Syscall

Syscall là tầng thấp hơn native API:

```text
user code
 ↓
syscall ABI
 ↓
kernel
```

---

## 442.7 — Không bắt buộc libc

Axiom có thể:

```text
Axiom
 ↓
native syscall
```

mà không cần:

```text
Axiom
 ↓
libc
 ↓
syscall
```

---

## 442.8 — libc vẫn được phép

Nếu người dùng muốn tương thích ecosystem C:

```text
extern "c"
```

có thể gọi libc bình thường.

Nhưng đây là **dependency của application**, không phải dependency của compiler.

---

## 442.9 — Syscall backend

Platform layer có:

```text
SyscallBackend {
    invoke(...)
}
```

nhưng implementation phụ thuộc OS/architecture.

---

## 442.10 — Syscall numbers

Không hard-code syscall number trong generic code.

Ví dụ:

```text
Linux x86_64
Linux AArch64
```

có syscall numbering khác nhau.

---

## 442.11 — Syscall wrapper

Wrapper cung cấp:

```text
raw_syscall(...)
```

ở unsafe/platform layer.

---

## 442.12 — Typed syscall API

Standard/platform library không expose raw syscall everywhere.

Ví dụ:

```text
File.open(...)
```

thay vì:

```text
syscall(2, ...)
```

---

## 442.13 — Raw syscall escape hatch

System/kernel developers có thể sử dụng:

```text
unsafe syscall(...)
```

---

## 442.14 — Syscall ABI safety

Raw syscall không được coi là safe chỉ vì compiler type-check được arguments.

Kernel contract vẫn thuộc platform ABI.

---

## 442.15 — Register-level syscall

Architecture backend chịu trách nhiệm:

```text
argument registers
syscall number register
return registers
clobbers
```

---

## 442.16 — Syscall machine lowering

Conceptual:

```text
syscall(id, a, b, c)
```

→ target-specific:

```text
move args → ABI registers
move syscall_id → designated register
syscall instruction
read result
```

---

## 442.17 — Syscall result

Raw result có thể là:

```text
isize
```

hoặc platform-specific signed machine word.

Standard wrapper chuyển thành:

```text
Result<T, Error>
```

---

## 442.18 — EINTR-style errors

Platform adapter chịu trách nhiệm quyết định:

```text
retry
return error
```

không để language core biết về POSIX-specific error semantics.

---

## 442.19 — Windows native calls

Windows backend có thể gọi native ABI trực tiếp.

Không yêu cầu:

```text
MSVC compiler
```

---

## 442.20 — Windows subsystem

Executable metadata có thể chọn:

```text
console
windows/gui
native subsystem
```

---

## 442.21 — Linux process startup

Linux native startup có thể đi:

```text
ELF entry
 ↓
Axiom startup
 ↓
main
```

không bắt buộc:

```text
_start → libc → main
```

---

## 442.22 — Linux syscall layer

Linux platform adapter cung cấp syscall wrappers trực tiếp khi phù hợp.

---

## 442.23 — macOS

Mach-O executable có platform-specific startup and system ABI.

Axiom backend phải emit đúng platform metadata.

---

## 442.24 — iOS

iOS target không được giả định giống macOS executable policy.

Platform restrictions được encode trong target profile.

---

## 442.25 — Android

Android native target dùng:

```text
AArch64
ELF
Android ABI
```

và platform APIs phù hợp.

---

## 442.26 — WASM

WASM không có native CPU syscall instruction.

Platform layer sử dụng:

```text
WASM imports
```

---

## 442.27 — WASI

WASI-like interfaces có thể được cung cấp như platform capability.

Không hard-code WASI vào language core.

---

## 442.28 — WASM host functions

Conceptual:

```text
extern "wasm"
```

hoặc generated imports.

Syntax có thể được chuẩn hóa sau.

---

## 442.29 — Bare metal

Bare-metal target:

```text
OS = none
```

---

## 442.30 — Bare-metal entry

```text
@entry
fn boot() -> never
```

có thể được platform linker sử dụng.

---

## 442.31 — Linker script

Embedded target có thể cung cấp memory layout:

```text
FLASH
RAM
STACK
MMIO
```

---

## 442.32 — Linker layout abstraction

Axiom linker hỗ trợ:

```text
MemoryRegion
SectionPlacement
SymbolAssignment
Alignment
LoadAddress
VirtualAddress
```

---

## 442.33 — Custom sections

Source/library có thể yêu cầu:

```text
@section(".text.fast")
```

hoặc tương đương attribute.

---

## 442.34 — Section placement

Platform configuration quyết định section cuối cùng nằm ở đâu.

---

## 442.35 — Interrupt vector table

Embedded backend có thể emit:

```text
.interrupt_vectors
```

hoặc target-specific equivalent.

---

## 442.36 — MMIO abstraction

MMIO address không được coi là ordinary memory trong compiler optimizer.

---

## 442.37 — Volatile

Hardware register access:

```text
volatile_load
volatile_store
```

---

## 442.38 — Volatile ≠ Atomic

Hai semantics độc lập:

```text
volatile
atomic
```

Không được thay thế lẫn nhau.

---

## 442.39 — Memory barriers

Platform layer có:

```text
fence
compiler_fence
hardware_fence
```

khi target cần.

---

## 442.40 — Interrupt critical section

Embedded library có thể cung cấp:

```text
critical_section()
```

với target-specific implementation.

---

## 442.41 — CPU privileged state

Privileged operations thuộc:

```text
unsafe
platform
```

không phải safe standard library.

---

## 442.42 — CPU instructions

Target intrinsics:

```text
intrinsic("...")
```

không được cho phép tùy ý trong safe code.

---

## 442.43 — ISA intrinsic

Có thể expose:

```text
x86_64::rdtsc()
aarch64::cntvct()
```

nhưng là platform-specific APIs.

---

## 442.44 — CPU feature requirements

Function có thể yêu cầu:

```text
@target_feature("avx2")
```

---

## 442.45 — Invalid CPU feature

Compiler có thể:

```text
compile error
```

nếu function yêu cầu feature mà target baseline không hỗ trợ.

---

## 442.46 — Runtime feature dispatch

Nếu muốn portable binary:

```text
if cpu_supports("avx2") {
    avx2_impl()
} else {
    baseline_impl()
}
```

---

## 442.47 — Feature isolation

Compiler phải bảo đảm machine instructions yêu cầu feature không xuất hiện trên baseline path.

---

## 442.48 — Architecture conditional compilation

```text
comptime if target.arch == x86_64 {
    ...
}
```

---

## 442.49 — OS conditional compilation

```text
comptime if target.os == windows {
    ...
}
```

---

## 442.50 — Platform module

Conceptual:

```text
platform.windows
platform.linux
platform.macos
platform.android
platform.ios
platform.wasm
platform.bare
```

---

## 442.51 — Public standard API

Application code ưu tiên:

```text
std.fs.File
std.net.TcpStream
std.thread.Thread
```

thay vì platform raw API.

---

## 442.52 — Platform escape hatch

Ứng dụng cần native functionality có thể:

```text
std.platform.windows
std.platform.posix
```

---

## 442.53 — No universal abstraction requirement

Nếu OS có feature đặc biệt không có counterpart trên OS khác:

```text
platform-specific API
```

được phép.

Không ép mọi OS vào abstraction thấp nhất.

---

## 442.54 — Native handle conversion

Ví dụ:

```text
File
 ↓
native_handle()
```

---

## 442.55 — Ownership contract

Native handle conversion phải khai báo:

```text
borrowed
owned
consumed
duplicated
```

---

## 442.56 — Handle duplication

Nếu OS hỗ trợ duplicate handle:

```text
duplicate()
```

tạo ownership độc lập.

---

## 442.57 — Handle inheritance

Process APIs phải explicit:

```text
inherit = true
```

không mặc định leak handles vào child.

---

## 442.58 — Environment access

Environment được xem là external mutable process state.

Không cache vô thời hạn nếu OS có thể thay đổi state.

---

## 442.59 — Current directory

Current directory là process state.

API phải phân biệt:

```text
get_current_dir()
set_current_dir()
```

---

## 442.60 — Working directory concurrency

Thay đổi process-wide working directory có thể ảnh hưởng threads.

API documentation phải phản ánh điều này.

---

## 442.61 — Process-wide state

Platform layer phải đánh dấu các API ảnh hưởng global/process state.

---

## 442.62 — File mapping

Memory-mapped file:

```text
map_file()
unmap()
```

là platform capability.

---

## 442.63 — Mapping lifetime

Mapped memory phải có lifetime explicit.

---

## 442.64 — Mapping permissions

Conceptual:

```text
Read
Write
Execute
```

không mặc định tất cả cùng bật.

---

## 442.65 — W^X

Platform/security profile có thể enforce:

```text
Writable XOR Executable
```

---

## 442.66 — Executable memory

Creating executable memory là privileged/unsafe capability.

---

## 442.67 — JIT

Nếu Axiom sau này có JIT:

```text
JIT memory
```

thuộc runtime/platform layer.

Không thuộc compiler core.

---

## 442.68 — Dynamic code generation

AOT compiler không yêu cầu runtime code generation.

---

## 442.69 — Shared library loading

Dynamic loader API là platform capability.

---

## 442.70 — Symbol lookup

Lookup trả về raw address + explicit type contract.

---

## 442.71 — FFI symbol typing

Compiler không thể tự biết native function ABI chỉ từ address.

Người dùng phải cung cấp declaration.

---

## 442.72 — ABI declaration

Ví dụ conceptual:

```text
extern "c" fn native_add(a: i32, b: i32) -> i32
```

---

## 442.73 — Variadic native API

ABI layer hỗ trợ:

```text
extern "c" fn printf(fmt: *const u8, ...) -> i32
```

nhưng safety/type checking hạn chế theo ABI.

---

## 442.74 — Native structs

`@repr(C)` đảm bảo C-compatible layout.

---

## 442.75 — Native unions

Platform/FFI layer hỗ trợ explicit union representation.

---

## 442.76 — Native bitfields

Bitfields không nên được giả định portable.

Platform-specific representation hoặc explicit packing required.

---

## 442.77 — Calling convention declaration

FFI có thể chỉ định:

```text
extern "c"
extern "system"
extern "win64"
```

---

## 442.78 — Name mangling

Native symbols có thể:

```text
@no_mangle
```

---

## 442.79 — Symbol export

Export explicit:

```text
@export
```

hoặc package ABI configuration.

---

## 442.80 — Symbol visibility

Platform linker hỗ trợ:

```text
public
hidden
local
weak
```

theo target.

---

## 442.81 — Weak symbols

Weak linking là platform/linker feature.

Không đưa vào language semantics mặc định.

---

## 442.82 — Dynamic symbol versioning

Linux-like symbol versioning có thể được backend hỗ trợ.

---

## 442.83 — ABI version

Native library export có:

```text
ABI version
```

khi compatibility cần.

---

## 442.84 — Package ABI

Axiom package semantic version không tự động đồng nghĩa native ABI compatibility.

---

## 442.85 — ABI compatibility check

Compiler/package manager có thể kiểm tra:

```text
type layout
calling convention
symbol signature
target
```

---

## 442.86 — ABI hash

Conceptual:

```text
ABIHash(
    exported_types,
    exported_functions,
    layouts,
    calling_conventions
)
```

---

## 442.87 — Native library metadata

`.axlib` hoặc equivalent metadata có thể chứa:

```text
target
ABI version
exports
dependencies
debug identity
compiler version
```

---

## 442.88 — Static library metadata

Archive có thể đi kèm semantic metadata:

```text
libfoo.a
libfoo.axmeta
```

---

## 442.89 — AI-readable ABI metadata

AI agent có thể query:

```text
library.exports()
library.required_symbols()
library.abi()
library.target()
```

---

## 442.90 — No source required

Agent có thể hiểu native library API từ metadata nếu source không available.

---

## 442.91 — Metadata authenticity

Metadata không được tự động coi là trusted executable code.

---

## 442.92 — Build provenance

Native artifact có thể lưu:

```text
compiler
source hash
dependency hashes
target
build mode
```

---

## 442.93 — Reproducible target

Target description phải là input của build hash.

---

## 442.94 — Syscall ABI versioning

OS syscall interfaces thay đổi theo platform/version.

Platform backend phải encode compatibility policy.

---

## 442.95 — Minimum OS version

Target configuration có:

```text
min_os_version
```

---

## 442.96 — API availability

Compiler/platform metadata có thể biết API nào yêu cầu OS version mới hơn.

---

## 442.97 — Availability diagnostics

Ví dụ:

```text
E442201 API requires Windows >= X
```

---

## 442.98 — Weak availability

Platform APIs có thể được runtime-detected khi OS cho phép.

---

## 442.99 — Deployment target

Deployment target là build configuration, không hard-code trong language.

---

## 442.100 — iOS deployment

iOS target có:

```text
deployment_version
architecture
framework availability
```

---

## 442.101 — Android API level

Android target có:

```text
api_level
```

---

## 442.102 — WASM feature level

WASM target có:

```text
wasm_features
```

ví dụ SIMD/threads/reference-types tùy compiler support.

---

## 442.103 — WASM imports

Imports là explicit dependency của artifact.

---

## 442.104 — WASM exports

Exports được khai báo explicit.

---

## 442.105 — WASM memory

Axiom WASM memory model map rõ:

```text
WASM linear memory
```

vào platform allocator/address model.

---

## 442.106 — WASM threads

Nếu enabled, compiler phải kiểm tra target host capabilities.

---

## 442.107 — WASM no-host mode

Pure compute module không được yêu cầu host imports.

---

## 442.108 — Native executable modes

Axiom hỗ trợ:

```text
executable
static library
dynamic library
object
WASM module
```

---

## 442.109 — Object-only build

```text
axiom build --emit=obj
```

không invoke linker.

---

## 442.110 — Link-only build

Có thể link existing Axiom/C/native objects bằng Axiom linker.

---

## 442.111 — Mixed native objects

Axiom linker có thể consume:

```text
Axiom object
C object
assembly object
```

nếu object format/ABI tương thích.

---

## 442.112 — Assembly interoperability

Axiom cho phép:

```text
extern
global asm
```

ở unsafe/platform layer.

---

## 442.113 — Inline assembly

Nếu được hỗ trợ:

```text
unsafe asm(...)
```

phải khai báo:

```text
inputs
outputs
clobbers
memory effects
```

---

## 442.114 — ASM register constraints

Target backend định nghĩa constraint model.

---

## 442.115 — ASM optimization barrier

Compiler phải hiểu:

```text
memory clobber
register clobber
side effects
```

để không reorder sai.

---

## 442.116 — No arbitrary machine code in safe code

Raw assembly là unsafe/platform-specific.

---

## 442.117 — Bootloader support

Bare-metal ecosystem có thể build:

```text
bootloader
kernel
firmware
```

nhưng không phải core language feature.

---

## 442.118 — Custom image format

Embedded linker có thể emit:

```text
raw binary
hex
firmware image
```

ngoài ELF/PE/Mach-O.

---

## 442.119 — Artifact conversion

Axiom toolchain có thể có:

```text
ELF
→ raw binary
ELF
→ Intel HEX
```

ở artifact tool layer.

---

## 442.120 — No external objcopy requirement

Các artifact conversion cơ bản nên do Axiom toolchain thực hiện.

---

## 442.121 — Platform testing matrix

Compiler CI phải test ít nhất:

```text
x86_64 Linux
x86_64 Windows
AArch64 Linux
AArch64 macOS
```

trong bootstrap phase.

Sau đó mở rộng:

```text
iOS
Android
WASM
embedded
```

---

## 442.122 — Syscall golden tests

Raw syscall lowering có expected:

```text
register
instruction
return convention
```

---

## 442.123 — Native API ABI tests

FFI tests phải kiểm tra:

```text
argument passing
return values
struct layout
alignment
calling convention
```

---

## 442.124 — Platform integration tests

Test thật trên target:

```text
file
socket
thread
process
clock
dynamic library
```

---

## 442.125 — Cross-target compile tests

Có thể compile platform API conditional code từ một host sang target khác.

---

## 442.126 — Host/target distinction

Compiler chạy trên:

```text
host
```

nhưng generate:

```text
target
```

Hai khái niệm phải luôn tách biệt.

---

## 442.127 — Build machine

```text
BuildMachine
HostMachine
TargetMachine
```

có thể khác nhau.

---

## 442.128 — Cross compiler

Axiom compiler là cross compiler native ngay từ kiến trúc.

---

## 442.129 — Canadian cross

Kiến trúc build phải đủ để hỗ trợ:

```text
build
host
target
```

khác nhau.

---

## 442.130 — Bootstrap compiler

Stage compiler có thể chạy trên host khác target output.

---

## 442.131 — Self-hosting implication

Axiom compiler sau này có thể:

```text
Axiom compiler trên Linux
→ Windows EXE
```

mà không cần cài MSVC.

---

## 442.132 — Toolchain independence

Cross compilation không được âm thầm gọi:

```text
gcc
clang
cl
link.exe
ld
```

để hoàn thành native artifact nếu mục tiêu là standalone Axiom toolchain.

---

## 442.133 — External linker escape hatch

Người dùng vẫn có thể chọn external linker:

```text
linker = external
```

nhưng đây không phải default Axiom-native path.

---

## 442.134 — External SDK

Apple/Android SDK có thể vẫn cần cho platform framework/signing/resource packaging.

Điều này khác với phụ thuộc compiler.

---

## 442.135 — iOS signing

iOS code signing/provisioning là platform deployment requirement.

Compiler không tự coi đây là language semantic.

---

## 442.136 — Android packaging

APK/AAB generation thuộc packaging/deployment layer.

---

## 442.137 — Resource packaging

Native artifact có thể kết hợp:

```text
binary
resources
manifest
icons
metadata
```

ở package/deployment phase.

---

## 442.138 — Platform SDK abstraction

SDK headers/interfaces có thể được chuyển thành Axiom declarations/metadata.

---

## 442.139 — Bindgen

Một tool có thể generate Axiom FFI declarations từ native headers.

Bindgen là toolchain utility, không phải compiler dependency.

---

## 442.140 — Generated FFI metadata

Generated declarations phải có provenance:

```text
source_header
sdk_version
target
generator_version
```

---

## 442.141 — ABI drift

Nếu SDK thay đổi layout/signature:

```text
ABI hash
```

phải thay đổi.

---

## 442.142 — Native library probing

Build system có thể test:

```text
library exists
symbol exists
ABI compatible
```

---

## 442.143 — No runtime probing for static dependencies

Static linking failures phải được phát hiện ở link time.

---

## 442.144 — Dynamic dependency declaration

Dynamic dependency manifest ghi:

```text
library
minimum_version
required_symbols
```

---

## 442.145 — Security policy

Dynamic library loading phải có explicit trust boundary.

---

## 442.146 — Sandboxed platforms

Platform API phải phản ánh sandbox restrictions.

Ví dụ:

```text
iOS
WASM sandbox
```

không được giả định unrestricted filesystem/process access.

---

## 442.147 — Capability-oriented APIs

Nơi có thể, API nên nhận explicit capability:

```text
FileHandle
NetworkSocket
ProcessHandle
```

thay vì hidden global authority.

---

## 442.148 — Security-sensitive APIs

Các API như:

```text
executable_memory
raw_syscall
process_injection
kernel_device
```

nếu tồn tại phải nằm trong explicit unsafe/platform layer.

---

## 442.149 — Sandboxed standard library

Standard library phải fail rõ ràng nếu platform capability unavailable.

---

## 442.150 — No fake portability

Axiom không giả vờ rằng mọi platform hỗ trợ mọi API.

Thay vào đó:

```text
compile-time unavailable
```

hoặc:

```text
runtime unsupported
```

được báo rõ ràng.

---

## 442.151 — Platform feature matrix

Compiler có machine-readable table:

```text
Feature
Target
Available
MinimumVersion
RequiredCapability
```

---

## 442.152 — AI platform query

Agent có thể hỏi:

```text
platform.supports("filesystem")
platform.supports("threads")
platform.supports("dynamic_library")
```

---

## 442.153 — Platform diagnostics

Ví dụ:

```text
E442301:
feature unavailable on target

required:
    filesystem

target:
    wasm32
```

---

## 442.154 — No accidental host API

Cross compilation không được resolve platform API của **host** thay cho **target**.

Đây là invariant cực kỳ quan trọng.

---

## 442.155 — Comptime target identity

Comptime luôn biết:

```text
target
```

chứ không mặc định host.

---

## 442.156 — Native endian

Platform ABI cung cấp endian.

---

## 442.157 — Pointer model

Target cung cấp:

```text
pointer_width
pointer_alignment
address_space_model
```

---

## 442.158 — Multiple address spaces

GPU/future heterogeneous targets có thể có:

```text
host
device
shared
constant
```

address spaces.

Không cần đưa tất cả vào core ngay.

---

## 442.159 — Address-space type

Nếu target cần, pointer type có thể mang address-space metadata.

---

## 442.160 — GPU isolation

GPU pointers không được tự động coi là CPU pointers.

---

## 442.161 — Platform ABI schema

Compiler internal:

```text
PlatformABI {
    target
    startup
    calling_convention
    syscall
    native_api
    tls
    unwind
    linker
    loader
}
```

---

## 442.162 — Platform backend interface

```text
PlatformBackend {
    startup()
    exit()
    thread()
    tls()
    file()
    socket()
    process()
    time()
    random()
    dynamic_library()
}
```

Không nhất thiết tất cả capability phải implemented.

---

## 442.163 — Capability interface

Mỗi capability có interface riêng:

```text
FileBackend
ThreadBackend
SocketBackend
ClockBackend
ProcessBackend
```

---

## 442.164 — Backend composition

Runtime build:

```text
Runtime
 ├── StartupBackend
 ├── AllocatorBackend
 ├── PanicBackend
 ├── FileBackend
 └── ThreadBackend
```

---

## 442.165 — Backend selection

Target configuration chọn backend.

---

## 442.166 — Backend fallback

Không tự động fallback sang slower/less-safe implementation nếu semantic contract thay đổi.

---

## 442.167 — Native zero-cost path

High-level API:

```text
File.read()
```

có thể inline/lower thành minimal platform calls.

---

## 442.168 — Wrapper elimination

Compiler/optimizer được phép loại wrapper abstraction khi semantics cho phép.

---

## 442.169 — No abstraction tax

Platform abstraction là compile-time architecture, không bắt buộc runtime virtual dispatch.

---

## 442.170 — Static dispatch

Platform selection mặc định static:

```text
target.os
→ concrete implementation
```

---

## 442.171 — Dynamic platform dispatch

Chỉ dùng nếu explicitly requested.

---

## 442.172 — Platform error type

Standard API:

```text
Error {
    kind
    code
    native_code
}
```

---

## 442.173 — Native code preservation

`native_code` có thể giữ OS-specific code.

---

## 442.174 — Error conversion

Platform errors chuyển thành standard errors tại boundary.

---

## 442.175 — Syscall restart semantics

Các syscall có restartable behavior phải được xử lý ở platform wrapper, không language core.

---

## 442.176 — Partial operations

Read/write APIs phải hỗ trợ partial completion:

```text
bytes_read
bytes_written
```

không assume full completion.

---

## 442.177 — Nonblocking operations

API phải phân biệt:

```text
WouldBlock
Interrupted
Completed
Error
```

---

## 442.178 — Async readiness

Async adapter chuyển native readiness event thành Future state.

---

## 442.179 — OS event handles

Platform-specific event primitives được wrap bằng owned resources.

---

## 442.180 — Platform scheduler

Executor có thể chọn native scheduler.

---

## 442.181 — No scheduler in synchronous app

Program không dùng async không link scheduler.

---

## 442.182 — Platform timer

Timer backend cung cấp monotonic timer primitives.

---

## 442.183 — High resolution time

Không guarantee precision cao hơn platform capability.

---

## 442.184 — CPU topology

Platform API có thể expose:

```text
logical_cpu_count
physical_cpu_count
NUMA nodes
cache topology
```

nếu available.

---

## 442.185 — CPU affinity

Explicit platform capability.

---

## 442.186 — NUMA

NUMA allocator/thread affinity thuộc advanced platform layer.

---

## 442.187 — Memory page API

Platform layer có:

```text
page_size
virtual_alloc
virtual_free
protect
```

khi supported.

---

## 442.188 — Virtual memory

Virtual memory API không phải heap allocator.

---

## 442.189 — Heap distinction

```text
VirtualMemory
    ≠
Allocator
```

---

## 442.190 — Large allocation optimization

Allocator có thể dùng virtual memory internally.

Đây là implementation detail.

---

## 442.191 — Shared memory

Explicit platform capability:

```text
SharedMemory
```

---

## 442.192 — Memory mapped IPC

Có thể xây IPC trên shared memory nhưng không thuộc language core.

---

## 442.193 — Named synchronization

Platform-specific named mutex/semaphore APIs.

---

## 442.194 — File locking

Explicit API:

```text
lock_shared
lock_exclusive
unlock
```

---

## 442.195 — Advisory vs mandatory locking

Platform semantics phải được documentation/metadata phân biệt.

---

## 442.196 — Process signals

Signal delivery là platform-specific.

---

## 442.197 — Child process status

Process handle có:

```text
wait
try_wait
kill
exit_code
```

theo platform capabilities.

---

## 442.198 — Process tree cleanup

Structured process groups có thể được standard library xây dựng.

---

## 442.199 — Terminal/TTY

Console capability có thể expose:

```text
Terminal
TTY
PTY
```

---

## 442.200 — Platform contract final

Axiom platform architecture:

```text
                  ┌──────────────┐
                  │ Axiom Core   │
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │ Core / Std   │
                  └──────┬───────┘
                         │
                ┌────────▼────────┐
                │ Platform Layer  │
                └────────┬────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Native API      Syscall        WASM Host
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                    OS / Firmware
```

---

# 442.201 — Hard invariants

1. Language core không biết syscall.
2. Language core không biết Windows/Linux API.
3. Standard library không được hard-code một OS.
4. Platform layer chịu trách nhiệm native integration.
5. Syscall là thấp hơn native API.
6. libc không phải compiler dependency.
7. libc vẫn được phép dùng qua FFI.
8. Axiom có thể gọi syscall trực tiếp khi platform cho phép.
9. Raw syscall thuộc unsafe/platform layer.
10. Syscall ABI phải target-specific.
11. Syscall numbering không được hard-code generic.
12. Host và target luôn được phân biệt.
13. Cross compilation không được vô tình dùng host platform API.
14. Target triple là input của compilation.
15. Minimum OS/API version là build configuration.
16. Platform availability phải machine-readable.
17. Unsupported platform capability phải báo rõ.
18. Không fake portability.
19. Platform abstraction mặc định static dispatch.
20. Không có hidden dynamic dispatch.
21. Native wrappers phải có thể bị optimizer loại bỏ.
22. Platform API không được tạo abstraction tax bắt buộc.
23. Native handles phải có ownership semantics.
24. Owned handle drop phải release resource.
25. Borrowed handle không được tự close.
26. Raw handle conversion phải explicit.
27. Volatile và atomic là hai semantics khác nhau.
28. MMIO phải dùng volatile semantics.
29. Executable memory là explicit capability.
30. W^X/security policy được platform profile kiểm soát.
31. Bare-metal không cần OS.
32. Bare-metal có custom entry.
33. Embedded hỗ trợ custom memory layout.
34. WASM không giả định native syscall.
35. WASM host imports phải explicit.
36. Pure WASM có thể không cần imports.
37. iOS/Android có deployment-specific constraints.
38. External SDK không đồng nghĩa compiler dependency.
39. Axiom compiler không cần MSVC/GCC/Clang để emit native code.
40. External linker chỉ là escape hatch.
41. Axiom linker có thể link Axiom/native objects trực tiếp.
42. `@repr(C)` là ABI boundary.
43. Native symbol typing phải explicit.
44. Dynamic library loading là platform capability.
45. ABI compatibility có thể được kiểm tra bằng metadata/hash.
46. Generated FFI bindings phải có provenance.
47. Runtime capabilities phải compose được.
48. Không link scheduler nếu không dùng async.
49. Không link allocator nếu program không allocate.
50. Không có hidden runtime thread.
51. Platform errors giữ native error code khi cần.
52. Partial I/O phải được biểu diễn chính xác.
53. Blocking và async semantics không được trộn.
54. Platform feature detection phải phân biệt compile-time và runtime.
55. CPU feature-specific code phải được cô lập khỏi baseline.
56. Virtual memory và heap allocator là hai abstraction khác nhau.
57. Platform layer có thể expose advanced OS features mà không làm phình language core.
58. AI tooling có thể query target/platform capability.
59. Platform metadata phải deterministic và versioned.
60. Axiom phải có đường đi từ **zero-runtime bare metal → native OS → WASM host** mà không thay đổi semantics của language core.

**BOOTSTRAP-442 hoàn tất.**

---

# BOOTSTRAP-443 — NATIVE LINKER, SYMBOL RESOLUTION, SECTION LAYOUT, RELOCATION, LTO & FINAL IMAGE CONSTRUCTION

Đây sẽ là bước đi sâu vào **Axiom Linker**, tức thành phần quyết định Axiom thực sự có thể thay thế toolchain native bên ngoài đến mức nào.

Trọng tâm:

```text
Object Files
   │
   ▼
Symbol Graph
   │
   ├── Resolution
   ├── Archive Extraction
   ├── COMDAT / Dedup
   ├── Weak / Strong
   ├── Section GC
   ├── LTO
   ├── Layout
   ├── Relocation
   ├── Relaxation
   └── Import / Export
   │
   ▼
Native Image
   │
   ├── PE
   ├── ELF
   ├── Mach-O
   └── WASM
```

## 443.1 — Linker là compiler component độc lập

```text
Frontend
    ≠
Codegen
    ≠
Object Writer
    ≠
Linker
```

Linker có thể được gọi độc lập trên object files.

## 443.2 — Link graph

Mỗi object trở thành node:

```text
Object A
Object B
Object C
```

Edges là symbol/reference dependencies.

## 443.3 — Root symbols

Link bắt đầu từ roots:

```text
entry
exported symbols
forced symbols
runtime roots
```

## 443.4 — Dead code elimination

Nếu function không reachable từ root:

```text
section GC
```

có thể loại bỏ.

## 443.5 — Function-level sections

Compiler ưu tiên granular sections để linker GC hiệu quả.

## 443.6 — Data-level sections

Data cũng có thể được tách granular khi kích thước/overhead hợp lý.

## 443.7 — Symbol table

Canonical:

```text
Symbol {
    name
    binding
    visibility
    section
    offset
    size
    type
    flags
}
```

## 443.8 — Symbol states

```text
Undefined
Defined
Common
Absolute
Imported
Weak
```

## 443.9 — Strong symbol

Hai strong definitions cùng symbol:

```text
link error
```

trừ khi explicit override mechanism của object format cho phép.

## 443.10 — Weak symbol

Weak definition có thể bị strong definition thay thế theo target ABI.

## 443.11 — Symbol aliases

Linker hỗ trợ alias nếu object format/target cho phép.

## 443.12 — Local symbols

Không tham gia global resolution.

## 443.13 — Global symbols

Được đưa vào global symbol namespace.

## 443.14 — Symbol namespace

Axiom mangling phải tránh collision giữa:

```text
package
module
type
generic instance
function
```

## 443.15 — Stable symbol mangling

Mangled name phải deterministic.

## 443.16 — ABI export name

FFI exports có thể bypass Axiom mangling.

## 443.17 — Generic symbols

Generic chưa monomorphized không được emit thành ordinary executable symbol nếu không cần.

## 443.18 — Monomorphized instance

```text
foo<i32>
foo<f64>
```

có InstanceKey riêng.

## 443.19 — Generic deduplication

Identical generated instances có thể được merge.

## 443.20 — COMDAT-like semantics

Backend hỗ trợ equivalent weak/dedup semantics theo target.

## 443.21 — Archive

Static library:

```text
libfoo.a
foo.lib
```

chứa nhiều object members.

## 443.22 — Lazy archive extraction

Chỉ extract member nếu symbol đang unresolved.

## 443.23 — Archive cycle

Linker phải handle archive dependency cycles deterministic.

## 443.24 — Whole-archive

Explicit option:

```text
--whole-archive
```

hoặc Axiom equivalent.

## 443.25 — Force symbol

User có thể mark symbol:

```text
--force-symbol
```

## 443.26 — Link order

Axiom linker phải deterministic và document rõ semantic của library order.

## 443.27 — Circular dependency

Nếu static archive cycle không resolve được:

```text
link diagnostic
```

không retry vô hạn.

## 443.28 — Section model

Canonical:

```text
.text
.rodata
.data
.bss
.tls
.debug
```

plus target-specific sections.

## 443.29 — Section flags

```text
R
W
X
ALLOC
TLS
MERGE
```

## 443.30 — W^X

Linker không tự tạo writable+executable section nếu không explicitly required.

## 443.31 — Section merging

Equivalent sections có thể merge.

## 443.32 — Alignment

Section layout tôn trọng maximum alignment của input sections.

## 443.33 — Padding

Padding được xác định deterministic.

## 443.34 — Virtual address

Linker assign VA theo target image layout.

## 443.35 — File offset

File offset độc lập virtual address.

## 443.36 — Loadable segment

ELF/Mach-O/PE backend map sections thành loadable segments.

## 443.37 — Segment permissions

Segments có:

```text
R
RW
RX
```

theo platform/security policy.

## 443.38 — Read-only relocation

Relocation vào read-only section có thể yêu cầu:

```text
dynamic relocation
copy
layout change
```

Linker phải xử lý explicit.

## 443.39 — Relocation processing

Pipeline:

```text
resolve
→ calculate
→ apply
→ validate
```

## 443.40 — Relocation overflow

Nếu relocation value không fit:

```text
link error
```

không silently truncate.

## 443.41 — Branch relaxation

Linker có thể thay:

```text
long branch
→ short branch
```

khi range cho phép.

## 443.42 — Relaxation correctness

Relaxation phải preserve:

```text
target address
instruction semantics
alignment
relocation
```

## 443.43 — GOT

ELF dynamic linking có thể dùng GOT.

## 443.44 — PLT

Dynamic calls có thể dùng PLT khi ABI yêu cầu.

## 443.45 — Import table

PE backend xây import structures.

## 443.46 — Export table

PE backend xây export structures.

## 443.47 — Mach-O dylib

Mach-O backend xử lý dylib load commands.

## 443.48 — ELF dynamic section

ELF dynamic executable/library có:

```text
.dynamic
```

và associated structures.

## 443.49 — PIE

Linker hỗ trợ PIE nếu target/platform yêu cầu.

## 443.50 — ASLR

Image layout phải tương thích ASLR policy.

## 443.51 — TLS layout

Linker xử lý TLS sections/model theo target.

## 443.52 — Thread-local symbols

TLS relocation phải target-specific.

## 443.53 — Init/fini

Runtime initialization entries được linker tổng hợp deterministic.

## 443.54 — Constructor ordering

Axiom ưu tiên explicit dependency order thay vì compiler/link-order accident.

## 443.55 — Global destructors

Nếu language/library cần global cleanup:

```text
explicit runtime registry
```

được dùng.

Không tạo destructor machinery nếu program không cần.

## 443.56 — Entry point

Linker xác định:

```text
entry RVA/VA
```

từ runtime configuration.

## 443.57 — Executable headers

Linker tự tạo native headers:

```text
ELF header
PE header
Mach-O header
```

## 443.58 — Program headers

ELF load segments được tạo trực tiếp.

## 443.59 — PE sections

PE section table được layout trực tiếp.

## 443.60 — Mach-O load commands

Mach-O load commands được tạo trực tiếp.

## 443.61 — Image base

Target policy xác định preferred image base.

## 443.62 — Relocatable image

Nếu cần ASLR/dynamic loading, relocation structures được giữ theo target.

## 443.63 — Static executable

Static image có thể resolve mọi required symbols tại link time.

## 443.64 — Dynamic executable

Dynamic dependencies được ghi vào image metadata.

## 443.65 — Library search

Search order phải deterministic.

## 443.66 — Native dependency

```text
libc
system framework
third-party .a/.so/.dll/.dylib
```

có thể được link nếu user khai báo.

## 443.67 — Axiom dependency

Axiom package metadata cho linker biết artifact target/ABI.

## 443.68 — Incompatible object

Linker phải reject object khi:

```text
architecture mismatch
ABI mismatch
object format mismatch
endianness mismatch
```

## 443.69 — Cross-architecture linking

Không tự động convert object architecture.

## 443.70 — LTO boundary

Axiom linker có thể nhận:

```text
native object
Axiom IR object
```

nếu LTO enabled.

## 443.71 — Thin LTO

Metadata-only summary cho phép incremental optimization.

## 443.72 — Full LTO

Có thể merge toàn bộ eligible functions.

## 443.73 — LTO determinism

Parallel LTO phải tạo deterministic output.

## 443.74 — Cross-module inlining

Link-time optimization có thể inline giữa modules.

## 443.75 — Cross-library optimization

Chỉ khi dependency được cung cấp ở optimization-compatible form.

## 443.76 — Native library barrier

Precompiled foreign library không thể bị Axiom optimizer nhìn xuyên nếu không có IR/metadata.

## 443.77 — ABI boundary optimization

FFI functions không được arbitrary inline nếu body unavailable.

## 443.78 — Internal visibility

Private symbols có thể được internalize sau resolution.

## 443.79 — Symbol GC

Sau internalization, unused symbols được remove.

## 443.80 — Data deduplication

Read-only identical constants có thể merge.

## 443.81 — String merging

Identical string literals có thể share storage nếu semantics cho phép.

## 443.82 — Function identical code folding

Identical functions có thể merge nếu compiler chứng minh semantics tương đương.

## 443.83 — Address identity

ICF không được merge functions nếu program có thể observe distinct function addresses theo language semantics.

## 443.84 — Constant address identity

Tương tự với global constants.

## 443.85 — Section ordering

Default deterministic ordering:

```text
startup
text
rodata
data
bss
tls
```

Target có thể override.

## 443.86 — Hot/cold partition

Compiler có thể mark:

```text
hot
cold
```

để linker layout tối ưu locality.

## 443.87 — Code locality

Hot code có thể đặt gần nhau.

## 443.88 — Data locality

Frequently-used data có thể group nếu profile-guided optimization được bật.

## 443.89 — Profile-guided layout

PGO là optional.

## 443.90 — PGO data

Profile artifact phải versioned và target-aware.

## 443.91 — Reproducibility

PGO builds chỉ deterministic nếu profile input cố định.

## 443.92 — Link map

Axiom linker có thể emit:

```text
.axiom.map
```

gồm:

```text
symbol
address
size
section
object
```

## 443.93 — Binary size analysis

Tool:

```text
axiom inspect size
```

có thể trả:

```text
text
rodata
data
bss
debug
runtime
dependency
```

## 443.94 — Dependency attribution

Linker metadata cho phép biết binary size đến từ package/module nào.

## 443.95 — AI binary analysis

AI tooling có thể query:

```text
binary.symbols()
binary.sections()
binary.dependencies()
binary.size_breakdown()
```

## 443.96 — Link diagnostics

Ví dụ:

```text
E443001 undefined symbol
E443002 duplicate symbol
E443003 relocation overflow
E443004 incompatible object
E443005 invalid relocation
```

## 443.97 — Diagnostic provenance

Undefined symbol phải liệt kê references:

```text
main.ax
 → foo()
 → missing_symbol
```

## 443.98 — Duplicate symbol provenance

Diagnostic phải chỉ rõ:

```text
object A defines
object B defines
```

## 443.99 — Relocation provenance

Relocation failure phải chỉ:

```text
object
section
symbol
offset
relocation type
```

## 443.100 — Linker trace

Debug option:

```text
--trace-symbol
--trace-object
```

hoặc Axiom equivalent.

## 443.101 — Symbol resolution trace

Có thể giải thích:

```text
requested
→ candidate
→ selected
→ rejected candidates
```

## 443.102 — Linker script

Advanced users có thể custom layout.

## 443.103 — Default linker script

Axiom cung cấp default target-specific layout.

## 443.104 — Script safety

Linker script không được execute arbitrary host code.

## 443.105 — Linker plugin boundary

Custom linker plugins là optional tooling.

Không phải compiler core dependency.

## 443.106 — Post-link validation

Sau image creation:

```text
validate headers
validate entry
validate relocations
validate segments
validate alignment
validate symbols
```

## 443.107 — ELF validation

Kiểm tra:

```text
ELF class
machine
entry
program headers
section bounds
```

## 443.108 — PE validation

Kiểm tra:

```text
machine
subsystem
entry RVA
section ranges
imports
exports
```

## 443.109 — Mach-O validation

Kiểm tra:

```text
CPU type
load commands
entry
segments
codesign-related metadata
```

## 443.110 — WASM validation

Kiểm tra:

```text
types
imports
exports
sections
function indices
memory
```

## 443.111 — Native image checksum

Nếu target format cần checksum/security metadata, linker tạo đúng format.

## 443.112 — Code signing boundary

Code signing không thuộc ordinary linking semantics.

---

## 443.113 — Signing input

Linker output trở thành input cho signing phase.

---

## 443.114 — Signing tool

Axiom có thể cung cấp signing integration nhưng signing credentials không nằm trong compiler.

---

## 443.115 — Reproducible unsigned artifact

Unsigned binary phải reproducible trước signing.

---

## 443.116 — Signing nondeterminism

Signature bytes có thể khác do certificate/timestamp; đây là deployment layer.

---

## 443.117 — Build ID

Final binary có deterministic/content-derived BuildId khi profile yêu cầu.

---

## 443.118 — Debug identity

BuildId liên kết với:

```text
debug artifact
crash symbolication
```

---

## 443.119 — Link cache

Link results có thể cache theo:

```text
object hashes
link configuration
target
linker version
```

---

## 443.120 — Partial relink

Nếu một object thay đổi:

```text
unchanged objects
```

được reuse ở mức phù hợp.

---

## 443.121 — Incremental linker

Linker có thể cache:

```text
symbol resolution
section layout
relocations
```

nhưng phải preserve deterministic output.

---

## 443.122 — Cache invalidation

Cache invalid khi:

```text
object changed
target changed
linker version changed
link config changed
dependency changed
```

---

## 443.123 — Linker parallelism

Independent object processing chạy song song.

Global layout/resolution vẫn deterministic.

---

## 443.124 — Memory usage

Linker phải hỗ trợ large projects mà không giữ mọi intermediate representation trong RAM nếu không cần.

---

## 443.125 — Streaming object reader

Object files có thể được đọc incremental.

---

## 443.126 — Streaming archive reader

Archive members không cần load toàn bộ vào RAM.

---

## 443.127 — Thin archive

Nếu target format hỗ trợ, thin archive có thể được dùng.

---

## 443.128 — Linker memory model

```text
Input objects
→ indexed metadata
→ demand-load contents
```

---

## 443.129 — Object index

Symbol index giúp tránh scan toàn bộ archive nhiều lần.

---

## 443.130 — Symbol graph cache

Incremental build cache giữ:

```text
object hash
symbol summary
dependency edges
```

---

## 443.131 — LTO memory budget

LTO có resource limit.

Nếu vượt limit:

```text
diagnostic/fallback policy
```

---

## 443.132 — Link-time optimization policy

Profiles:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
```

có thể điều chỉnh LTO.

---

## 443.133 — `-Oz`

Ưu tiên executable size.

---

## 443.134 — `-Os`

Cân bằng size/performance.

---

## 443.135 — `-O3`

Aggressive optimization.

---

## 443.136 — Debug link

Debug artifact generation được tích hợp sau final layout.

---

## 443.137 — Unwind link

Unwind metadata được merge/relocate cùng final image.

---

## 443.138 — Exception tables

Nếu panic/exception unwind enabled:

```text
personality
LSDA/equivalent
unwind tables
```

được link theo target.

---

## 443.139 — No exception runtime

Nếu program không sử dụng unwind:

```text
exception runtime
```

không được link.

---

## 443.140 — Runtime root discovery

Linker nhận runtime roots từ compiler manifest:

```text
panic
allocator
thread
async
io
```

---

## 443.141 — Runtime component GC

Unused runtime components được loại bỏ giống application code.

---

## 443.142 — Startup root

Startup symbol luôn root.

---

## 443.143 — Export root

Public dynamic-library exports luôn root.

---

## 443.144 — Reflection root

Compile-time reflection không tự tạo runtime root.

---

## 443.145 — Dynamic lookup root

Symbol được lookup bằng runtime string phải được mark explicit root.

---

## 443.146 — Plugin exports

Plugin API cần explicit export manifest để linker/loader biết symbols.

---

## 443.147 — Static initialization roots

Static constructors/registries phải được đánh dấu explicit.

---

## 443.148 — Link-time dead code safety

Compiler không được loại code có externally observable dynamic lookup nếu metadata đã đánh dấu root.

---

## 443.149 — Binary ABI manifest

Final native library có thể chứa:

```text
AxiomAbiManifest
```

với:

```text
target
ABI
exports
required symbols
version
```

---

## 443.150 — Final linker contract

```text
                Objects
                   │
                   ▼
            Object Reader
                   │
                   ▼
             Symbol Index
                   │
                   ▼
          Dependency Graph
                   │
          ┌────────┴────────┐
          ▼                 ▼
     Resolution          Archive
          │                 │
          └────────┬────────┘
                   ▼
              LTO / GC
                   │
                   ▼
             Section Layout
                   │
                   ▼
               Relocation
                   │
                   ▼
               Relaxation
                   │
                   ▼
             Image Builder
                   │
          ┌────────┼─────────┐
          ▼        ▼         ▼
        ELF       PE       Mach-O
                   │
                   ▼
             Final Artifact
```

---

# 443.151 — Hard invariants

1. Axiom linker là native linker độc lập.
2. Không cần GCC/Clang/MSVC để link native Axiom artifact.
3. Object reader độc lập object writer.
4. Symbol resolution deterministic.
5. Duplicate strong symbols là error.
6. Weak/strong semantics theo target ABI.
7. Archive extraction lazy mặc định.
8. Whole-archive là explicit.
9. Dead section elimination được hỗ trợ.
10. Function/data sections có thể granular.
11. Relocation overflow là error.
12. Không silently truncate relocation.
13. Branch relaxation phải preserve semantics.
14. Section alignment phải chính xác.
15. Segment permissions phải explicit.
16. W^X được tôn trọng.
17. TLS layout được target backend xử lý.
18. Entry point phải xác định rõ.
19. Host và target không được trộn.
20. Static và dynamic linking là hai mode riêng.
21. Native dependencies được kiểm tra ABI.
22. Axiom objects có metadata target/ABI.
23. Foreign objects được chấp nhận nếu ABI tương thích.
24. LTO là optional.
25. Precompiled foreign library là optimization boundary.
26. Axiom IR có thể đi qua linker LTO nếu được cung cấp.
27. Generic instances có deduplication strategy.
28. Address identity không được phá bởi ICF.
29. Identical constants chỉ merge khi semantics cho phép.
30. Linker có map/binary-size analysis.
31. Link diagnostics phải chỉ rõ provenance.
32. Incremental linking có content-hash invalidation.
33. Parallel linking phải deterministic.
34. Object/archive processing có thể streaming.
35. Runtime components được link theo capability.
36. Unused runtime code phải được loại bỏ.
37. Dynamic lookup symbols phải được đánh dấu roots.
38. Debug/unwind metadata được link đúng với final addresses.
39. BuildId phải liên kết chính xác với artifact/debug data.
40. Code signing là phase sau linking.
41. Unsigned artifact phải reproducible.
42. External linker chỉ là escape hatch.
43. Axiom linker phải tạo được executable tối thiểu từ object mà không cần toolchain C.
44. Linker phải hỗ trợ ELF/PE/Mach-O/WASM tương ứng với target backend.
45. Final image phải được post-link validate.
46. Linker không execute arbitrary host code.
47. Link scripts không được phá deterministic build mặc định.
48. ABI manifest phải machine-readable.
49. Link graph có thể được AI tooling truy vấn.
50. **Compiler → Object → Axiom Linker → Native Artifact** là native path chuẩn của Axiom.

**BOOTSTRAP-443 hoàn tất.**