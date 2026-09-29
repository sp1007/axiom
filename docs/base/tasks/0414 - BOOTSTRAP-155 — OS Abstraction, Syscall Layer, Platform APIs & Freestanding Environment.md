# BOOTSTRAP-155 — OS Abstraction, Syscall Layer, Platform APIs & Freestanding Environment
**STATUS: FROZEN / COMPLETED**

> **Axiom không lấy POSIX làm “hệ điều hành trừu tượng” của ngôn ngữ. Axiom định nghĩa một System Contract độc lập, sau đó ánh xạ contract đó xuống Windows, Linux, Darwin, Android, WASM, embedded hoặc kernel.**

Đây là quyết định quan trọng để Axiom không bị khóa vào mô hình Unix.

---

# 1. Ba tầng hệ thống

```text id="os01"
Axiom Application
        ↓
Axiom System API
        ↓
Platform Adapter
        ↓
┌────────┬────────┬────────┬──────────┐
Windows  Linux   Darwin   Android   WASM ...
```

Không:

```text
Axiom
 ↓
POSIX
 ↓
everything
```

POSIX chỉ là **một interoperability layer**.

---

# 2. System Contract

Tầng hệ thống định nghĩa semantic operations:

```text id="os02"
File
Directory
Process
Thread
VirtualMemory
Socket
Clock
Random
Environment
Library
Signal
Console
Device
```

Ví dụ:

```ax id="os03"
std::os::File
std::os::Process
std::os::Memory
std::os::Thread
```

API semantic không nhất thiết giống Windows/Linux API.

---

# 3. Platform Adapter

Ví dụ:

```text id="os04"
std::os::File
      ↓
PlatformFile
      ├── Windows → HANDLE
      ├── Linux   → fd
      ├── Darwin  → fd
      └── WASM    → host capability
```

Axiom application không phải biết handle thực tế là gì.

---

# 4. Handle

OS resources nên được biểu diễn bằng **logical/resource handles**, không dùng pointer làm identity.

Ví dụ:

```text id="os05"
FileHandle
ProcessHandle
SocketHandle
LibraryHandle
DeviceHandle
```

Handle:

```text id="os06"
≠ raw pointer
≠ memory capability
```

Nó biểu diễn identity của resource bên ngoài.

---

# 5. Resource ownership

Ví dụ:

```text id="os07"
let file = File.open(...)?;
```

`file` sở hữu resource handle.

Khi lifetime kết thúc:

```text id="os08"
Drop(file)
 ↓
close/release
```

Không cần:

```text id="os09"
delete
free
close
```

ở mọi call site.

---

# 6. OS handle không phải memory owner

Ví dụ:

```text id="os10"
FileHandle
```

không đồng nghĩa:

```text id="os11"
owns file contents
```

Resource identity và memory ownership là hai thứ khác nhau.

---

# 7. Syscall layer

Axiom cần có low-level:

```text id="os12"
std::sys
```

hoặc system-layer tương đương.

Ví dụ:

```text id="os13"
sys_read
sys_write
sys_mmap
sys_exit
```

nhưng đây không phải API application-level.

---

# 8. Syscall không phải Core primitive

Compiler chỉ cần hỗ trợ:

```text id="os14"
extern
unsafe
ABI
calling convention
```

System package cung cấp syscall declarations.

Nhờ vậy:

```text id="os15"
Core compiler
```

không phải biết:

```text Linux syscall #60
Windows NT syscall ...
```

---

# 9. Direct syscall

Freestanding/system code có thể:

```text id="os16"
Axiom
 ↓
System ABI
 ↓
syscall instruction
```

không cần:

```text id="os17"
libc
POSIX
CRT
```

---

# 10. Windows

Windows adapter có thể sử dụng:

```text id="os18"
Win32
NT
NTDLL
Kernel APIs
```

tùy profile.

Không ép mọi ứng dụng xuống syscall trực tiếp.

---

# 11. Linux

Linux adapter có thể hỗ trợ:

```text id="os19"
Linux syscall
libc/POSIX compatibility
```

tách biệt.

Ứng dụng có thể chọn:

```text id="os20"
direct system layer
```

hoặc:

```text id="os21"
POSIX compatibility layer
```

---

# 12. Darwin

macOS/iOS:

```text id="os22"
Axiom System API
 ↓
Darwin adapter
 ↓
Mach / BSD / system frameworks
```

Framework API có thể được bind thông qua FFI.

---

# 13. Android

Android cần phân biệt:

```text id="os23"
Android runtime/application model
Linux kernel
NDK
JNI
```

Axiom không nên giả định Android = Linux desktop.

Target descriptor có:

```text id="os24"
Android
```

riêng.

---

# 14. iOS

Tương tự:

```text id="os25"
iOS
```

là target riêng với:

- application lifecycle;
- sandbox;
- signing;
- frameworks;
- ABI;
- platform restrictions.

---

# 15. WASM

WASM không có OS syscall theo kiểu native.

Do đó:

```text id="os26"
std::os
 ↓
WASM host contract
```

Ví dụ host cung cấp:

```text id="os27"
filesystem
clock
network
console
```

thông qua host imports.

---

# 16. Freestanding

Axiom phải hỗ trợ:

```text id="os28"
@freestanding
```

hoặc build profile tương đương.

Khi đó:

```text id="os29"
no OS
no libc
no std::os
no allocator
no thread runtime
```

nếu program không cần.

---

# 17. Minimal freestanding

Ví dụ conceptual:

```ax id="os30"
@entry
fn start() -> never {
    loop {}
}
```

Compiler có thể tạo:

```text id="os31"
ELF/PE/Mach-O/firmware
```

mà không kéo theo application runtime.

---

# 18. Kernel profile

Axiom có thể biên dịch kernel:

```text id="os32"
@profile(kernel)
```

với:

```text id="os33"
no OS
no libc
custom allocator
custom interrupt handling
custom scheduler
```

---

# 19. Embedded

Embedded profile:

```text id="os34"
@profile(embedded)
```

cho phép:

```text id="os35"
static memory
custom linker script
memory-mapped IO
interrupts
DMA
device registers
```

với unsafe/system APIs.

---

# 20. Memory-mapped I/O

Ví dụ hardware:

```text id="os36"
MMIO address
 ↓
volatile load/store
```

Axiom không được tối ưu bỏ access.

```text
volatile ≠ atomic
volatile ≠ synchronization
```

vẫn giữ nguyên.

---

# 21. Virtual memory

System layer nên cung cấp:

```text id="os37"
reserve
commit
protect
map
unmap
remap
```

nhưng semantics của:

```text id="os38"
std::os::VirtualMemory
```

độc lập với Windows/Linux.

---

# 22. Memory protection

Các quyền:

```text id="os39"
READ
WRITE
EXECUTE
```

được biểu diễn rõ.

Không được mặc định:

```text id="os40"
RWX
```

cho executable memory.

---

# 23. Allocation và VirtualMemory

Phải phân biệt:

```text id="os41"
Allocator
VirtualMemory
```

Allocator quản lý object allocations.

VirtualMemory quản lý:

```text address space
pages
protection
mapping
```

Đây là hai tầng khác nhau.

---

# 24. Physical memory

Kernel/embedded có thể cần:

```text id="os42"
physical address
DMA
device memory
```

Đây là system/unsafe domain.

Không được đưa physical address vào safe memory model.

---

# 25. Device memory

Đã frozen GPU model:

```text id="os43"
DEVICE storage domain
```

System API có thể map:

```text id="os44"
OS/device allocation
 ↓
DeviceBuffer
```

nhưng foreign device memory không tự động trở thành ordinary heap.

---

# 26. Filesystem

Semantic API:

```text id="os45"
File
Directory
Path
Metadata
```

Path phải là type riêng, không chỉ raw string nếu cần semantic validation.

---

# 27. Path và encoding

Axiom nên tránh giả định:

```text id="os46"
all OS paths = UTF-8 strings
```

Windows có UTF-16/native path representation.

Do đó:

```text id="os47"
Path
```

là semantic path.

Conversion sang native representation do platform adapter thực hiện.

---

# 28. Environment

```text id="os48"
Environment
```

có thể cung cấp:

```text
get variable
set variable
arguments
current directory
```

nhưng tất cả đều là:

```text
ExternalState
```

trong Effect model.

---

# 29. Process

Process API:

```text id="os49"
spawn
wait
exit
kill
environment
stdin/stdout/stderr
```

Process handle là owning resource.

---

# 30. Process ownership

Ví dụ:

```text id="os50"
let p = Process.spawn(...)?;
```

`p` sở hữu **handle**, không nhất thiết sở hữu process lifetime theo nghĩa OS process vẫn tồn tại khi handle bị drop.

Do đó cần phân biệt:

```text id="os51"
Handle lifetime
Process lifetime
```

---

# 31. Detached process

Nếu muốn process tiếp tục độc lập:

```text id="os52"
p.detach()
```

đây là explicit semantic operation.

Không để Drop tự động giết process.

---

# 32. Thread

System thread:

```text id="os53"
Thread.spawn(fn)
```

có:

```text Send
```

requirement như concurrency model.

---

# 33. Thread handle

```text id="os54"
JoinHandle<T>
```

là observation capability.

Drop handle không nhất thiết đồng nghĩa:

```text kill thread
```

đã frozen theo concurrency model.

---

# 34. TLS

TLS là runtime/system storage:

```text id="os55"
ThreadLocal<T>
```

Compiler biết TLS storage class.

Platform backend quyết định:

```text ELF TLS
PE TLS
Mach-O TLS
```

---

# 35. Clock

Clock phải phân biệt:

```text id="os56"
MonotonicClock
WallClock
CPUClock
```

Không dùng một `now()` mơ hồ.

---

# 36. Time effects

```text id="os57"
now()
```

là external observable state.

Compiler không được constant-fold thành:

```text compile-time constant
```

trừ khi caller explicit dùng comptime clock capability.

---

# 37. Random

Tương tự:

```text id="os58"
Random
SecureRandom
```

phải là external state.

Không được tối ưu bỏ call vì “return value không được dùng” nếu call có observable effect.

---

# 38. Signals / faults

Phải phân biệt:

```text id="os59"
OS Signal
Hardware Fault
Axiom Panic
Result Error
```

Ví dụ:

```text
SIGSEGV ≠ panic()
```

về semantic origin.

---

# 39. Fault handling

System layer có thể expose:

```text id="os60"
signal handlers
exception handlers
fault handlers
```

nhưng unsafe/system.

Không để safe application tùy ý biến arbitrary hardware fault thành normal `Result`.

---

# 40. Console

Console là:

```text id="os61"
IO
```

không phải intrinsic compiler.

`print()` nếu tồn tại nên nằm trong std.

---

# 41. Networking

System abstraction:

```text id="os62"
Socket
Tcp
Udp
Listener
Address
```

Platform adapter:

```text id="os63"
Windows sockets
Linux sockets
Darwin sockets
WASM host
```

---

# 42. Blocking

System APIs cần mô tả:

```text id="os64"
Blocking
NonBlocking
Async
```

Không để compiler tự suy luận:

```text syscall = nonblocking
```

---

# 43. Async system calls

Async API:

```text id="os65"
File.read_async(...)
Socket.recv_async(...)
```

là library/runtime layer.

Core chỉ hiểu:

```text async
await
Future
```

---

# 44. OS event integration

Executor có thể tích hợp:

```text id="os66"
IOCP
epoll
kqueue
io_uring
WASM host events
```

nhưng đó là runtime policy.

Axiom language không cần biết tên từng mechanism.

---

# 45. Dynamic libraries

System layer:

```text id="os67"
load_library
lookup_symbol
```

đã được FFI model hóa.

Platform adapter chịu trách nhiệm:

```text LoadLibrary
dlopen
dyld
WASM imports
```

---

# 46. GUI

GUI không nên nằm trong OS Core.

Có thể:

```text id="os68"
std::ui
```

phụ thuộc:

```text Windows
Cocoa
Wayland
X11
Android
iOS
```

qua platform packages.

---

# 47. OS capabilities

System APIs nên có capability-oriented model:

```text id="os69"
FileCapability
NetworkCapability
ProcessCapability
DeviceCapability
```

nhưng không nhất thiết mỗi API phải tạo một type capability riêng.

Mục tiêu là:

> API chỉ có thể thực hiện những hành động mà program/profile đã được cấp quyền.

Đặc biệt hữu ích cho WASM/sandboxed environments.

---

# 48. Sandbox

Axiom không giả định process luôn có toàn quyền.

Platform có thể trả:

```text id="os70"
PermissionDenied
Unavailable
Unsupported
```

thay vì compiler cố đoán.

---

# 49. System API availability

Compile-time target checks:

```text id="os71"
@cfg(target_os = "windows")
```

cho API không tồn tại trên target.

Nếu runtime-dependent:

```text id="os72"
Result<..., Unsupported>
```

tùy semantics.

---

# 50. `std::os` không phải abstraction leak

Application nên viết:

```ax id="os73"
let file = File.open(path)?;
```

thay vì:

```text
if windows:
    CreateFile
else:
    open
```

trừ khi cần platform-specific functionality.

---

# 51. Escape hatch

Khi cần native API:

```ax id="os74"
@cfg(target_os = "windows")
unsafe {
    win32_call(...)
}
```

FFI/system layer cho phép.

---

# 52. System contracts và compiler

Compiler cần hiểu một số property:

```text id="os75"
TLS
atomic
volatile
calling convention
memory barriers
interrupt entry
```

nhưng không cần hiểu API business logic.

---

# 53. Interrupts

Embedded/kernel profile có:

```text id="os76"
@interrupt
fn timer_irq(...)
```

Compiler phải tạo target-specific ABI.

Interrupt handler là linker/codegen root.

Không bị dead-strip.

---

# 54. ISR constraints

Interrupt handler có thể có restrictions:

```text id="os77"
no blocking
no arbitrary allocation
specific register preservation
specific ABI
```

Compiler verifier phải kiểm tra những contract này.

---

# 55. DMA

DMA buffer:

```text id="os78"
CPU
 ↓
Device
```

có shared external storage semantics.

Không được coi DMA transfer là ordinary memory copy nếu hardware semantics khác.

---

# 56. Cache coherence

DMA có thể cần:

```text id="os79"
flush
invalidate
barrier
```

đây là explicit system/device operations.

Compiler không tự xóa chúng như ordinary memory operations.

---

# 57. Memory barriers

Phân biệt:

```text id="os80"
compiler barrier
CPU fence
device fence
atomic ordering
```

đã phù hợp với memory model.

---

# 58. Freestanding `std`

Freestanding không nhất thiết:

```text no std
```

Mà:

```text id="os81"
std::core
std::mem
std::sync primitives
```

có thể vẫn tồn tại.

Chỉ các phần cần OS/runtime bị loại bỏ.

---

# 59. Profile matrix

Axiom nên có:

| Profile | OS | Runtime | Allocator | Threads |
|---|---|---|---|---|
| Hosted | Có | chọn | chọn | chọn |
| Freestanding | Không | tối thiểu | optional | optional |
| Kernel | Không | custom | custom | custom |
| Embedded | optional | minimal | static/custom | optional |
| GPU | host/device | GPU runtime optional | device-specific | GPU model |
| WASM | host | host-defined | optional | target-dependent |

---

# 60. Build target model

Target cuối cùng:

```text id="os82"
Target {
    arch
    os
    environment
    abi
    object_format
    runtime_profile
    cpu_features
    capabilities
}
```

Ví dụ:

```text id="os83"
x86_64-windows
x86_64-linux
aarch64-macos
aarch64-ios
aarch64-android
wasm32-wasi
riscv64-freestanding
```

---

# 61. WASI

WASI nên được xem là:

```text id="os84"
host/system capability ABI
```

không phải Core language semantics.

Axiom có thể target WASI thông qua adapter.

---

# 62. System package structure

Đề xuất:

```text id="os85"
std/
 ├── core/
 ├── alloc/
 ├── collections/
 ├── io/
 ├── fs/
 ├── net/
 ├── process/
 ├── thread/
 ├── sync/
 ├── async/
 ├── time/
 ├── random/
 ├── os/
 │    ├── windows/
 │    ├── linux/
 │    ├── darwin/
 │    ├── android/
 │    └── wasm/
 ├── gpu/
 └── ffi/
```

---

# 63. System backend

Compiler target backend:

```text id="os86"
TargetBackend
 ├── codegen
 ├── object
 ├── ABI
 └── system integration
```

Nhưng API-level platform implementation nằm ở std/system packages.

---

# 64. No libc requirement

Đây là invariant quan trọng:

```text id="os87"
Axiom executable
```

có thể:

```text
Axiom
 ↓
own startup
 ↓
own allocator
 ↓
own syscall/system ABI
 ↓
OS
```

mà không cần:

```text
libc
CRT
C compiler
```

nếu target/profile cho phép.

---

# 65. Nhưng libc vẫn được hỗ trợ

Application có thể chọn:

```text id="os88"
Axiom
 ↓
C ABI
 ↓
libc
```

Đây là interoperability, không phải requirement.

---

# 66. Runtime-free application

Ví dụ một utility nhỏ:

```text id="os89"
main
 ↓
write syscall
 ↓
exit
```

không cần:

```text
allocator
async
thread
reflection
unicode runtime
```

---

# 67. Security boundary

System API phải phân biệt:

```text id="os90"
safe system operation
unsafe system operation
privileged operation
```

Ví dụ:

```text
File.read()
```

có thể safe.

Nhưng:

```text
map arbitrary physical address
```

là unsafe/system.

---

# 68. Compiler-generated system startup

Compiler có thể sinh:

```text id="os91"
AxiomEntry
```

nhưng startup code phải là:

```text id="os92"
explicit compiler/runtime component
```

không phải hidden universal runtime.

---

# 69. Startup contract

```text id="os93"
OS Loader
 ↓
Platform Entry
 ↓
Axiom Startup
 ↓
TLS/runtime initialization
 ↓
main
 ↓
cleanup
 ↓
OS exit
```

Freestanding:

```text id="os94"
Entry
 ↓
user entry
```

có thể bỏ phần lớn startup.

---

# 70. Invariants

Đóng băng:

### `AOS-20`
Axiom system semantics are independent of POSIX.

### `AOS-21`
POSIX is a compatibility layer, not the fundamental OS model.

### `AOS-22`
System APIs are semantic abstractions over platform mechanisms.

### `AOS-23`
Platform adapters implement system contracts.

### `AOS-24`
OS resources have explicit ownership semantics.

### `AOS-25`
Resource handles are distinct from memory pointers.

### `AOS-26`
Handle lifetime and underlying OS resource lifetime are distinct when platform semantics require.

### `AOS-27`
Syscalls are system-layer functionality, not Core language primitives.

### `AOS-28`
Direct syscalls may be used in system/freestanding code.

### `AOS-29`
Direct system calls do not require libc or POSIX.

### `AOS-30`
Libc/POSIX interoperability remains supported through FFI.

### `AOS-31`
Windows, Linux, Darwin, Android and WASM are distinct target environments.

### `AOS-32`
Platform-specific APIs do not redefine Core language semantics.

### `AOS-33`
Freestanding programs may omit OS/runtime facilities.

### `AOS-34`
Kernel and embedded profiles may define custom runtime/system layers.

### `AOS-35`
Allocator and virtual memory are distinct abstractions.

### `AOS-36`
Physical memory access is unsafe/system-level.

### `AOS-37`
Device memory is distinct from ordinary host memory.

### `AOS-38`
MMIO uses explicit volatile semantics.

### `AOS-39`
Volatile is distinct from atomicity and synchronization.

### `AOS-40`
Memory protection is explicit at system boundaries.

### `AOS-41`
Filesystem paths are semantic system values and are not assumed to have one universal native encoding.

### `AOS-42`
Process handles do not implicitly imply process termination on Drop.

### `AOS-43`
Detached execution is explicit.

### `AOS-44`
Thread creation respects Send requirements.

### `AOS-45`
TLS is an explicit storage domain.

### `AOS-46`
Monotonic and wall clocks are distinct semantic sources.

### `AOS-47`
Time and random sources are external observable state.

### `AOS-48`
Signals, hardware faults, panic and Result errors are distinct mechanisms.

### `AOS-49`
System APIs may report unsupported/permission errors at runtime.

### `AOS-50`
Target-specific availability can be checked through target configuration.

### `AOS-51`
Async OS operations are library/runtime abstractions over system facilities.

### `AOS-52`
OS event mechanisms remain runtime/platform implementation details.

### `AOS-53`
Interrupt handlers are explicit compiler/linker roots.

### `AOS-54`
Interrupt ABI restrictions are verified.

### `AOS-55`
DMA and device synchronization remain explicit system semantics.

### `AOS-56`
Compiler barriers, CPU fences, device fences and atomic ordering remain distinct.

### `AOS-57`
Freestanding profiles may retain useful portions of std without requiring a monolithic runtime.

### `AOS-58`
System capability availability is explicit.

### `AOS-59`
Sandbox restrictions are represented as system/runtime conditions, not language UB.

### `AOS-60`
System dependencies do not become compiler dependencies.

### `AOS-61`
Platform adapters cannot bypass Axiom ownership/capability verification.

### `AOS-62`
Unsafe system operations may establish trusted machine-level preconditions.

### `AOS-63`
Safe verification resumes after established system contracts.

### `AOS-64`
Axiom can produce native programs without libc/CRT when the selected target/profile permits.

### `AOS-65`
Axiom can interoperate with libc/CRT when explicitly selected.

### `AOS-66`
System startup is a composable runtime component.

### `AOS-67`
No universal hidden startup/runtime code is required.

### `AOS-68`
System APIs remain separate from language Core semantics.

### `AOS-69`
Target-specific system implementation does not change source-level semantic meaning.

### `AOS-70`
The final compiler must support freestanding/native system targets without requiring a third-party compiler.

---

# Một quyết định lớn vừa được hoàn tất

Axiom giờ có đủ tầng để đi từ:

```text
Axiom source
```

đến:

```text
┌──────────────────────────────────┐
│        Axiom Application         │
├──────────────────────────────────┤
│            std                   │
├──────────────────────────────────┤
│       Axiom System Layer         │
├──────────────────────────────────┤
│         FFI / ABI                │
├──────────────────────────────────┤
│      Platform / OS ABI           │
├──────────────────────────────────┤
│ Windows / Linux / Darwin / etc.  │
└──────────────────────────────────┘
```

và đồng thời:

```text
Axiom
 ↓
own compiler
 ↓
own object writer
 ↓
own linker
 ↓
own startup/runtime components
 ↓
OS
```

**không cần C compiler để tồn tại.**

C vẫn có thể xuất hiện ở FFI boundary khi ứng dụng muốn dùng hệ sinh thái C.

---

# BOOTSTRAP-156 — Native Runtime Primitives, Allocator Architecture & `std::core`

Bước tiếp theo nên đi vào **implementation của phần runtime thấp nhất**, vì đây là nền móng để compiler bootstrap có thể bắt đầu tự viết standard library.

Sẽ chốt:

```text
Axiom Core
    ↓
Compiler Builtins
    ↓
std::core
    ↓
Allocator
    ↓
Memory primitives
    ↓
Panic
    ↓
Startup
```

đặc biệt:

- intrinsic nào thực sự cần compiler;
- intrinsic nào có thể viết bằng Axiom;
- `memcpy/memmove/memset`;
- atomic primitives;
- CPU intrinsics;
- bit operations;
- endian;
- alignment;
- uninitialized memory;
- allocator interface;
- `Box`;
- `Vec`;
- `String`;
- `Option/Result`;
- panic;
- abort;
- stack/heap primitives;
- runtime-free operation;
- và quan trọng nhất: **làm thế nào để `std::core` đủ mạnh nhưng không biến thành một “second language runtime”.**