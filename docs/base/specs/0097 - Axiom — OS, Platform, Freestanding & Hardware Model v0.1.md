Tiếp tục.

# Axiom — OS, Platform, Freestanding & Hardware Model v0.1

Đây là phần cần chốt rất kỹ vì mục tiêu của Axiom không chỉ là một application language, mà còn phải có khả năng đi xuống:

```text
Application
    ↓
OS API
    ↓
System programming
    ↓
Embedded
    ↓
Kernel
    ↓
Bare metal
    ↓
Firmware / bootloader
```

Nguyên tắc tôi đề xuất:

> **Core không biết Windows/Linux/macOS. System layer biết OS. Hardware layer biết CPU/device. Compiler biết target nhưng source semantics không phụ thuộc target.**

---

# 1. Ba tầng phải tách biệt

```text
┌────────────────────────────────────┐
│ Axiom Language Core                │
│ types / ownership / async / atomic │
└──────────────────┬─────────────────┘
                   │
┌──────────────────▼─────────────────┐
│ Axiom System Layer                 │
│ syscall / ABI / TLS / process      │
│ thread / mmap / virtual memory     │
└──────────────────┬─────────────────┘
                   │
┌──────────────────▼─────────────────┐
│ Platform / Target Layer            │
│ Linux / Windows / macOS / UEFI     │
│ ARM / x86 / RISC-V / WASM          │
└────────────────────────────────────┘
```

Core không được import:

```text
windows
linux
posix
darwin
android
```

---

# 2. Target không phải là language semantics

Ví dụ:

```text
x86-64 Linux
ARM64 Linux
x86-64 Windows
ARM64 Windows
```

đều phải hiểu cùng một Axiom source.

Khác biệt nằm ở:

```text
ABI
layout contract
syscall/API
calling convention
object format
startup
TLS
atomic lowering
unwind
```

---

# 3. Target triple

Compiler cần internal target descriptor:

```text
Architecture
OperatingSystem
Environment
ABI
ObjectFormat
Endianness
PointerWidth
FeatureSet
```

Ví dụ conceptually:

```text
x86_64-linux-gnu
x86_64-windows-msvc
aarch64-linux-gnu
aarch64-darwin
wasm32-wasi
riscv64-none
```

Nhưng đây là **compiler target identity**, không phải type system.

---

# 4. Không để `usize` phụ thuộc OS

`usize` phụ thuộc **target pointer width**, không phải OS.

Ví dụ:

```text
x86_64 Linux → 64 bit
x86_64 Windows → 64 bit
ARM64 Linux → 64 bit
ARM64 Windows → 64 bit
```

Đúng.

---

# 5. `isize/usize`

Định nghĩa:

```text
usize = unsigned integer capable of representing target address-space index
isize = signed counterpart
```

Không phải:

```text
usize = unsigned long
```

vì C ABI khác nhau giữa platform.

---

# 6. Pointer width và address

Axiom đã tách:

```text
Value
Address
Pointer
View
```

Điều này đặc biệt hữu ích cho OS.

Ví dụ:

```text
addr
```

là machine address representation.

Nhưng:

```text
*mut T
```

là pointer có provenance.

Không cho:

```text
pointer == integer
```

một cách implicit.

---

# 7. Syscall không phải Core

Không có:

```axiom
syscall(...)
```

trong Core.

System layer có:

```text
std.os.linux.syscall
std.os.windows.nt
...
```

và syscall raw có thể là:

```text
unsafe
```

nếu semantics không thể được kiểm chứng.

---

# 8. OS API không nên nằm trong language syntax

Không cần:

```text
if windows
if linux
```

trong Core language.

Build system có conditional compilation:

```text
@cfg(os = "linux")
```

hoặc module resolution:

```text
std.os.current
```

---

# 9. Conditional compilation

Cần có, nhưng phải hạn chế.

Ví dụ:

```axiom
@cfg(target_os = "linux")
fn sleep(...) { ... }

@cfg(target_os = "windows")
fn sleep(...) { ... }
```

Compiler loại bỏ declaration không phù hợp **trước type checking của target-specific branch**.

---

# 10. Nhưng `cfg` không được trở thành macro language

Không nên có:

```text
#ifdef
#if
#else
#define
```

kiểu C.

Axiom source tree nên vẫn là AST có cấu trúc.

```text
@cfg(...)
```

là attribute/compiler condition.

---

# 11. Platform module

Có thể:

```text
std/
 ├── os/
 │   ├── linux/
 │   ├── windows/
 │   ├── darwin/
 │   ├── android/
 │   └── ...
 └── system/
```

Application thường dùng abstraction:

```text
std.process
std.fs
std.net
std.thread
```

Platform implementation nằm dưới.

---

# 12. Freestanding

Axiom phải có profile:

```text
--profile=freestanding
```

Khi đó:

```text
no OS
no libc
no allocator
no threads
no filesystem
no runtime
```

nếu program không yêu cầu.

Ví dụ:

```axiom
@entry
fn boot() -> never {
    ...
}
```

---

# 13. `main` không phải mandatory

Hosted application:

```axiom
fn main() -> i32 {
    0
}
```

Freestanding:

```axiom
@entry
fn boot() -> never {
    loop {}
}
```

Kernel:

```axiom
@entry
fn kernel_main() -> never {
    ...
}
```

---

# 14. Entry point

`main()` là convention/library startup.

`@entry` là compiler/system semantic.

Ví dụ:

```text
ELF:
_start
 ↓
axiom startup
 ↓
main
```

Freestanding:

```text
reset_vector
 ↓
entry
```

Compiler không cần giả định libc.

---

# 15. Startup runtime cực nhỏ

Hosted:

```text
OS
 ↓
_start
 ↓
runtime startup
 ↓
main
 ↓
exit
```

Nhưng runtime startup chỉ link những thứ cần thiết.

---

# 16. Không hidden initialization

Không nên có:

```text
global constructor
module constructor
static object constructor
```

tự động chạy trước `main`.

Điều này rất quan trọng cho:

- deterministic startup
- tiny binaries
- embedded
- kernel
- static linking.

---

# 17. Static initialization

Cho phép:

```axiom
const MAX = 1024

static TABLE: [u8; 256] = ...
```

nếu compile-time initializer.

Runtime initialization phải explicit:

```axiom
fn init() -> Result<(), Error>
```

---

# 18. Thread-local storage

TLS là platform/compiler feature.

Ví dụ library:

```axiom
thread_local {
    var errno: i32
}
```

Compiler lower:

```text
FS/GS
TLS segment
OS TLS API
```

target-specific.

---

# 19. Process

Process API là library:

```axiom
let p = Process.spawn(...)
p.wait()?
```

Underlying:

```text
Linux → fork/clone/exec or equivalent
Windows → CreateProcess
```

Axiom semantics không phụ thuộc implementation.

---

# 20. Thread

Thread API:

```axiom
Thread.spawn(|| {
    work()
})
```

nhưng semantic rules đã được thiết kế:

```text
capture
 ↓
ownership
 ↓
Send
 ↓
thread
```

Do đó thread library không cần một ownership system riêng.

---

# 21. Thread entry

Không cần:

```text
extern "C"
thread_proc
void*
```

trong normal code.

Library/compiler adapter tạo platform-specific ABI.

---

# 22. OS handle

Windows/Linux đều có handle-like resources.

Axiom nên có abstraction:

```text
Resource<T>
```

hoặc concrete:

```text
File
Socket
Process
Thread
Mutex
```

Các resource:

```text
!Copy
Drop
explicit close()
```

---

# 23. File

Ví dụ:

```axiom
let file = File.open("a.txt", Read)?
let data = file.read_all()?
```

`file` ownership:

```text
scope
 ↓
File
 ↓
Drop
 ↓
close
```

Nếu `close()` cần báo lỗi:

```axiom
file.close()?
```

Drop vẫn là fallback cleanup.

---

# 24. OS error

Không dùng global:

```text
errno
```

làm language primitive.

API:

```text
Result<T, OsError>
```

Platform implementation có thể lấy:

```text
errno
GetLastError
NTSTATUS
```

và normalize thành Axiom error abstraction.

---

# 25. Nhưng không được mất native error

`OsError` nên có:

```text
kind
code
platform_code
```

để programmer có thể lấy raw platform error khi cần.

---

# 26. Dynamic library

Library API:

```axiom
let lib = DynamicLibrary.open("foo")?
let fn = lib.symbol("bar")?
```

Dynamic symbol loading không phải Core.

Function pointer ABI phải explicit.

---

# 27. Static library

Compiler/linker phải hỗ trợ:

```text
.a
.lib
```

và native Axiom object.

---

# 28. Shared library

Hỗ trợ:

```text
.so
.dll
.dylib
```

Compiler cần biết:

```text
visibility
symbol export
relocations
PIC/PIE
TLS
ABI
```

---

# 29. `@export`

Đã chốt:

```axiom
@export("my_function")
extern "C" fn my_function(...)
```

Nhưng:

```text
pub
```

không tự động có nghĩa:

```text
ELF exported symbol
```

Hai concepts khác nhau.

---

# 30. Static linking

Axiom nên ưu tiên:

```text
static linking
```

cho:

- freestanding
- embedded
- tiny tools
- deterministic deployment.

Nhưng không bắt buộc.

---

# 31. PIE

Hosted application có thể:

```text
PIE
non-PIE
```

compiler/linker target policy quyết định.

Source semantics không thay đổi.

---

# 32. Position-independent code

PIC là machine/backend concern.

Axiom source không cần:

```text
position_independent
```

trừ khi explicit target configuration.

---

# 33. WASM

WASM nên được coi là target:

```text
wasm32
wasm64 (nếu target hỗ trợ)
```

chứ không phải language mode riêng.

Axiom có thể compile:

```text
Axiom → WASM
```

với:

```text
linear memory
tables
imports
exports
```

---

# 34. WASM pointer

WASM32 có address width 32-bit.

Do đó:

```text
usize = u32
```

theo target.

Không được giả định:

```text
usize = 64
```

---

# 35. WASI

WASI là platform layer.

Không phải Core.

Pipeline:

```text
Axiom
 ↓
WASM
 ↓
WASI
```

hoặc:

```text
Axiom
 ↓
WASM
 ↓
custom host imports
```

---

# 36. Android

Android không cần language fork.

Target:

```text
aarch64-android
armv7-android
x86_64-android
```

Platform library:

```text
std.android
```

hoặc binding layer.

Native library:

```text
.so
```

ABI:

```text
AAPCS64
```

---

# 37. iOS

Tương tự:

```text
aarch64-ios
```

Axiom compiler tạo:

```text
Mach-O
```

Framework/static library integration là platform tooling.

Không đưa UIKit/Metal vào Core.

---

# 38. UEFI

UEFI là một target/system environment:

```text
Axiom
 ↓
freestanding
 ↓
UEFI ABI
 ↓
PE/COFF
```

Có thể viết:

```axiom
@entry
fn efi_main(...) -> Status {
    ...
}
```

thông qua system library.

---

# 39. Kernel

Kernel code cần:

```text
freestanding
no_std equivalent
no allocator unless explicit
no exceptions
no OS runtime
```

Nhưng Axiom không cần tạo “kernel language”.

---

# 40. Interrupt

Interrupt handler là system annotation:

```text
@interrupt
fn timer_handler(frame: InterruptFrame) {
    ...
}
```

Compiler/backend có thể cần:

- special prologue
- special epilogue
- register preservation
- interrupt return.

Đây là **target/system attribute**.

---

# 41. MMIO

Memory mapped I/O:

```axiom
let reg: volatile_view<u32> = ...
```

Tôi không khuyến nghị tạo `volatile_view` thành Core type.

Thay vào đó:

```text
volatile_load
volatile_store
```

system intrinsic.

---

# 42. Volatile vẫn không phải atomic

Đã chốt:

```text
volatile = observable memory access
atomic   = synchronization/atomicity
```

Ví dụ hardware register:

```axiom
unsafe {
    volatile_store(addr, value)
}
```

không tạo happens-before giữa CPU threads.

---

# 43. Interrupt và atomic

Hardware interrupt synchronization là platform concern.

Compiler không được giả định:

```text
volatile
```

có nghĩa:

```text
thread synchronization
```

---

# 44. Bare-metal allocator

Không có allocator mặc định.

Programmer có thể:

```text
StaticArena
PageAllocator
BuddyAllocator
Slab
```

từ library/system.

Do đó boot code có thể:

```text
0 heap allocation
```

---

# 45. Embedded profile

Nên có target profile:

```text
--profile=embedded
```

cho phép compiler enforce:

```text
no unwinding
no dynamic allocation
no floating point
no threads
no runtime
```

**nếu programmer chọn**.

Nhưng đây là constraints/build policy, không thay đổi Core semantics.

---

# 46. Interrupt-safe code

Một API có thể có effect:

```text
InterruptSafe
```

nhưng không nên tạo một type system khổng lồ.

Compiler có thể có internal effect:

```text
MayBlock
MayAllocate
MayPanic
MaySuspend
MayFFI
```

và system annotations sử dụng nó.

Đây là hướng rất đáng phát triển.

---

# 47. Effect system

Axiom đã có effects nội bộ.

Tôi đề xuất compiler effect set:

```text
ALLOC
BLOCK
SUSPEND
PANIC
FFI
IO
ATOMIC
SPAWN
GPU
UNSAFE
```

Nhưng:

> **Không biến toàn bộ effect system thành annotation bắt programmer viết.**

Compiler inference trước.

Chỉ explicit khi API contract cần.

---

# 48. Ví dụ

```axiom
async fn fetch() -> Result<Data, Error>
```

compiler biết:

```text
SUSPEND
IO
ALLOC?     // nếu implementation cần
```

Programmer không cần:

```text
async fn fetch() ![SUSPEND,IO,ALLOC]
```

---

# 49. Freestanding compiler checks

Nếu:

```text
--profile=freestanding
```

compiler có thể reject:

```text
File.open()
```

vì dependency:

```text
File
 ↓
OS
```

nhưng không reject:

```text
Vec<T>
```

nếu compiler có thể instantiate Vec với allocator explicit hoặc custom.

---

# 50. Capability-based platform access

Một hướng rất phù hợp với Axiom:

```text
Program capability
       ↓
required system component
       ↓
link only required implementation
```

Ví dụ chương trình chỉ dùng:

```text
write stdout
```

không cần link:

```text
filesystem
network
thread runtime
async runtime
```

---

# 51. Runtime dependency graph

Compiler/build system có thể tạo:

```text
main
 │
 ├── stdout
 │    └── os_write
 │
 └── exit
      └── os_exit
```

→ linker chỉ kéo những symbol cần.

Đây là một trong những cơ chế giúp binary nhỏ.

---

# 52. Native object formats

Axiom object writer cần hỗ trợ dần:

```text
ELF
PE/COFF
Mach-O
WASM
```

Không cần assembler.

Pipeline cuối:

```text
Machine IR
 ↓
Machine Encoder
 ↓
Object Writer
 ↓
Axiom Linker
 ↓
Native Executable
```

---

# 53. Linker

Đây là bước quan trọng cho mục tiêu self-hosting.

Ban đầu có thể:

```text
Axiom compiler
 ↓
Axiom object
 ↓
system linker
```

Nhưng cuối cùng:

```text
Axiom compiler
 ↓
Axiom object
 ↓
Axiom linker
 ↓
native executable
```

Không còn phụ thuộc:

```text
gcc
clang
MSVC linker
ld
lld
```

---

# 54. Nhưng không cần tự viết linker ngay

Đây là điểm chiến lược.

Thứ tự:

```text
Phase 1
Axiom → object → system linker

Phase 2
Axiom → object → Axiom linker

Phase 3
Axiom compiler self-hosted
 + Axiom linker
 + Axiom object writer
```

Nếu cố làm linker trước compiler optimizer, project sẽ bị phân tán.

---

# 55. Cross compilation

Một compiler Axiom duy nhất có thể:

```text
host = x86_64-linux
target = aarch64-linux
```

Backend target selection:

```text
TargetDescriptor
 ↓
ABI
 ↓
LIR lowering
 ↓
Machine encoder
 ↓
Object
```

Không cần target compiler riêng.

---

# 56. Target independence của frontend

Dependency graph phải giữ:

```text
frontend
   ↓
MIR
   ↓
LIR
   ↓
target
```

Không bao giờ:

```text
parser → x86
typechecker → linux
```

---

# 57. Điều này giúp compiler nhỏ hơn về kiến trúc

Một frontend duy nhất:

```text
Axiom semantics
```

nhiều backend:

```text
x86_64
aarch64
riscv64
wasm
...
```

---

# 58. Hardware-specific code

Nếu programmer thực sự cần:

```text
rdtsc
cpuid
mrs
msr
csr
in/out
```

thì:

```text
std.arch
```

hoặc:

```text
unsafe intrinsic
```

Không đưa vào Core.

---

# 59. Axiom Hardware Layer

Có thể tổ chức:

```text
std/
  arch/
    x86/
    arm/
    riscv/
  os/
    linux/
    windows/
    darwin/
  embedded/
  firmware/
```

Nhưng các module này chỉ được compile khi target phù hợp.

---

# 60. OS invariants

Chốt:

```text
AOS-01   Core Is OS Independent
AOS-02   Platform APIs Are Library/System Layer
AOS-03   Target Identity Is Compiler Metadata
AOS-04   usize Depends On Target Address Width
AOS-05   Pointer Is Not Integer
AOS-06   Syscalls Are Not Core Language Features
AOS-07   Conditional Compilation Is Structured
AOS-08   No C-Style Preprocessor
AOS-09   main Is Hosted Convention
AOS-10   @entry Supports Freestanding Systems
AOS-11   Startup Is Explicit And Minimal
AOS-12   No Hidden Global Constructors
AOS-13   Runtime Is Capability-Driven
AOS-14   TLS Is Target/Compiler Managed
AOS-15   OS Resources Are Explicit Owned Resources
AOS-16   Resource Drop Is Deterministic
AOS-17   OS Errors Use Result
AOS-18   Platform Error Codes Remain Accessible
AOS-19   Dynamic Loading Is Library-Level
AOS-20   Shared/Static Linking Are Explicit Build Choices
AOS-21   PIC/PIE Are Target Concerns
AOS-22   WASM Is A Target
AOS-23   WASI Is A Platform Layer
AOS-24   Android/iOS Are Platform Targets
AOS-25   UEFI Is A System Target
AOS-26   Kernel Code Uses Freestanding Profile
AOS-27   Interrupt Handlers Are Explicit System Contracts
AOS-28   MMIO Is Unsafe/System-Level
AOS-29   Volatile Is Not Synchronization
AOS-30   Bare Metal Has No Mandatory Allocator
AOS-31   Platform Effects Are Compiler-Tracked
AOS-32   Cross Compilation Uses One Semantic Frontend
AOS-33   Object Formats Are Backend Concerns
AOS-34   Final Axiom Toolchain Can Eliminate External Linker Dependency
AOS-35   Platform Abstractions Cannot Redefine Core Semantics
```

---

# 61. Một kiến trúc hoàn chỉnh đang hình thành

Hiện tại Axiom đã có thể nhìn thành:

```text
                         AXIOM
                           │
             ┌─────────────┴─────────────┐
             │                           │
          LANGUAGE                    COMPILER
             │                           │
   ┌─────────┼─────────┐          ┌──────┼───────┐
   │         │         │          │      │       │
 Types   Ownership  Concurrency  MIR   Oracle  Optimizer
   │         │         │          │      │       │
   └─────────┴─────────┘          └──────┼───────┘
                                         │
                                      ABI/LIR
                                         │
                         ┌───────────────┼───────────────┐
                         │               │               │
                        CPU             GPU          Accelerator
                         │               │               │
                       SIMD           Kernel           Kernel
                         │               │               │
                         └───────────────┼───────────────┘
                                         │
                                      TARGET
                                         │
                  ┌──────────┬───────────┼───────────┬─────────┐
                  │          │           │           │         │
                Linux     Windows      macOS       WASM    Bare Metal
```

Điểm quan trọng nhất:

**không có tầng nào phải biết quá nhiều về tầng bên dưới nó.**

---

# Tiếp tục → Build System, Package Manager & Dependency Model

Đây là phần tiếp theo rất đáng chốt vì mục tiêu của Axiom có một yêu cầu khá khác Rust/C++:

> **Axiom phải có thể tự build chính compiler, stdlib, application và cross-compile mà không biến dependency management thành một hệ thống phức tạp.**

Ta cần thiết kế:

```text
axiom.toml
axiom.lock
package
module
workspace
dependency
feature
build script
code generation
FFI binding
cross compilation
incremental compilation
cache
reproducible build
```

và đặc biệt phải quyết định **package manager có được phép chạy arbitrary code hay không**. Đây là chỗ rất dễ khiến một ngôn ngữ systems bị kéo theo hàng loạt vấn đề supply-chain và reproducibility.