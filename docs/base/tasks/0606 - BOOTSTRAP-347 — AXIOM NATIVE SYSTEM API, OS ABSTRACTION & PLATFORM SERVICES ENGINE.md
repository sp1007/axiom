# BOOTSTRAP-347 — AXIOM NATIVE SYSTEM API, OS ABSTRACTION & PLATFORM SERVICES ENGINE

Sau `346 — Native SDK, Sysroot & Platform Development Kit`, bước tiếp theo nên giải quyết **cách Axiom biến các API hệ điều hành thành một lớp API native thống nhất**, nhưng vẫn giữ được hiệu năng và khả năng truy cập toàn bộ sức mạnh riêng của từng OS.

Đây là lớp nằm giữa:

```text
Axiom Application
        │
        ▼
Axiom Standard Library
        │
        ▼
Platform Services
        │
        ▼
Native SDK / FFI / ABI
        │
        ▼
Operating System
```

Mục tiêu không phải tạo một abstraction kiểu Java/.NET che giấu OS, mà là:

> **Unified semantics, zero-cost platform abstraction, full native escape hatch.**

---

# 1. Vấn đề cần giải quyết

Hiện Axiom đã có:

- Native ABI
- FFI
- OS interop
- Platform SDK
- Sysroot
- System libraries
- Frameworks

Nhưng nếu không có lớp Platform Services, mỗi ứng dụng sẽ phải viết:

```text
Windows API
Linux API
macOS API
Android API
iOS API
WASM API
```

riêng biệt.

Ngược lại, nếu abstraction quá cao:

```text
Axiom
   ↓
UniversalOS
   ↓
GenericFile
   ↓
GenericSocket
   ↓
GenericThread
   ↓
OS
```

thì abstraction có thể:

- làm mất tính năng native
- tạo overhead
- ép mọi OS vào cùng một mô hình
- làm API nghèo hơn native API.

Axiom cần mô hình thứ ba.

---

# 2. Ba tầng API

Axiom nên chính thức hóa:

```text
Tier 0 — Native ABI
Tier 1 — Platform Services
Tier 2 — Cross-platform Standard Library
```

## Tier 0

Truy cập trực tiếp:

```text
Windows API
Linux syscall
POSIX
Darwin
Metal
DirectX
Vulkan
Android NDK APIs
```

qua SDK/FFI.

---

## Tier 1

Axiom cung cấp abstraction có semantic ổn định:

```text
File
Socket
Process
Thread
VirtualMemory
Clock
Environment
DynamicLibrary
Signal
Device
Window
```

Nhưng implementation là platform-specific.

---

## Tier 2

API tiện dụng cấp cao:

```text
Path
FileSystem
Http
Json
Collections
Unicode
ProcessBuilder
Async IO
```

Đây thuộc Standard Library.

---

# 3. Nguyên tắc Zero-Cost Platform Abstraction

Nếu programmer viết:

```text
file.read(buffer)
```

thì trên Linux có thể lower thành:

```text
read(...)
```

trên Windows:

```text
ReadFile(...)
```

Không được bắt buộc:

```text
virtual dispatch
object hierarchy
runtime reflection
heap allocation
```

chỉ vì dùng API cross-platform.

---

# 4. Platform Service Trait

Có thể dùng trait để mô tả capability:

```text
trait FileSystem {
    fn open(...)
    fn read(...)
    fn write(...)
    fn close(...)
}
```

nhưng implementation mặc định phải là static:

```text
LinuxFileSystem
WindowsFileSystem
DarwinFileSystem
```

Compiler biết target:

```text
@platform(linux)
impl FileSystem for LinuxFileSystem { ... }

@platform(windows)
impl FileSystem for WindowsFileSystem { ... }
```

và eliminate phần không dùng.

---

# 5. Không biến platform abstraction thành OOP

Không có:

```text
IFileSystem
IFile
IPlatform
IWindow
```

với object/vtable mặc định.

Thay vào đó:

```text
struct File { ... }

fn read(file: File, ...)
```

hoặc:

```text
impl File {
    fn read(...)
}
```

Method syntax vẫn chỉ là function dispatch.

---

# 6. Compile-Time Platform Selection

Axiom cần platform condition:

```text
@cfg(os = linux)
```

```text
@cfg(os = windows)
```

```text
@cfg(os = macos)
```

```text
@cfg(arch = aarch64)
```

```text
@cfg(feature = "gui")
```

Compiler loại bỏ code không phù hợp **trước code generation**.

---

# 7. Platform Capability

OS abstraction nên dựa trên capability thay vì OS name.

Ví dụ:

```text
@requires(filesystem)
fn load_config()
```

hoặc:

```text
@requires(network)
fn download()
```

Target:

```text
wasm32-bare
```

có thể không có filesystem.

Compiler báo:

```text
AXPLAT001:
required platform capability `filesystem` is unavailable
```

---

# 8. Capability Matrix

Platform manifest từ task 346 cung cấp:

```text
PlatformCapabilities {
    filesystem
    networking
    processes
    threads
    virtual_memory
    dynamic_loading
    gui
    gpu
    audio
    camera
    sensors
    ipc
    shared_memory
    signals
    timers
}
```

Platform Services consume metadata này.

---

# 9. File API

API semantic cơ bản:

```text
File
Path
OpenOptions
FileMetadata
FilePermissions
Directory
DirectoryEntry
```

Ví dụ:

```text
let file = File.open("data.bin")?
let n = file.read(buffer)?
file.write(data)?
```

Nhưng semantics không được giả định:

```text
Unix == Windows
```

Ví dụ:

- permissions
- symlink
- locking
- case sensitivity
- device files
- inode
- file identity

đều có platform-specific behavior.

---

# 10. File Identity

Không nên expose inode như universal identity.

Axiom có:

```text
FileId
```

semantic type.

Platform adapter map:

```text
Linux → dev + inode
Windows → volume + file ID
macOS → native file identity
```

Như vậy application có identity abstraction nhưng vẫn có native escape hatch.

---

# 11. Path Semantics

Không nên coi mọi path là UTF-8 string.

Axiom cần:

```text
Path
PathComponent
OsPath
```

Phân biệt:

```text
Unicode text
```

và:

```text
OS path representation
```

Windows có UTF-16 APIs; Unix có byte-oriented path semantics.

Không được làm mất thông tin chỉ để ép mọi thứ thành Unicode String.

---

# 12. Environment

API:

```text
Environment.get("HOME")
Environment.args()
Environment.current_dir()
Environment.executable_path()
```

nhưng implementation target-specific.

Compiler/runtime không được mặc định khởi tạo một global environment object.

---

# 13. Process API

Semantic model:

```text
Process
ProcessId
ExitStatus
ProcessBuilder
Stdio
```

Ví dụ:

```text
let child = Process.spawn(command)?
let status = child.wait()?
```

Các đặc tính OS-specific:

```text
signals
job objects
process groups
handles
sandbox
priority
affinity
```

phải được expose bằng extension/native API khi cần.

---

# 14. Thread API

Axiom Core đã có concurrency semantics.

Platform Services cung cấp:

```text
Thread.spawn(...)
Thread.current()
Thread.join()
Thread.id()
```

Nhưng:

```text
Thread
```

không được trở thành abstraction bắt buộc cho async.

Phân biệt:

```text
Thread
Task
Future
Fiber
Process
```

---

# 15. Thread Attributes

Native extensions:

```text
ThreadOptions {
    stack_size
    name
    priority
    affinity
}
```

Không phải target nào cũng hỗ trợ.

Nếu không hỗ trợ:

```text
unsupported
```

không được âm thầm giả lập bằng behavior khác.

---

# 16. Virtual Memory API

Đây là phần rất quan trọng với mục tiêu systems language.

Axiom nên có native abstraction:

```text
VirtualMemory.reserve(...)
VirtualMemory.commit(...)
VirtualMemory.decommit(...)
VirtualMemory.release(...)
VirtualMemory.protect(...)
VirtualMemory.map(...)
```

Semantic flags:

```text
Read
Write
Execute
Guard
NoAccess
```

Platform:

```text
Linux → mmap/mprotect
Windows → VirtualAlloc/VirtualProtect
Darwin → mach/vm APIs
```

Compiler không tự động biến đây thành allocator.

---

# 17. Memory Mapping

API:

```text
MemoryMap
MappedRegion
```

Ví dụ:

```text
let region = VirtualMemory.map(file, ...)?;
```

View semantics của Axiom có thể áp dụng:

```text
view<u8>
mut_view<u8>
```

nhưng mapping lifetime phải được verifier theo dõi.

---

# 18. Dynamic Libraries

Axiom đã có dynamic component architecture.

Platform Service:

```text
DynamicLibrary.open(...)
DynamicLibrary.symbol(...)
DynamicLibrary.close(...)
```

Native implementations:

```text
LoadLibrary / GetProcAddress
dlopen / dlsym
NSLookupSymbol / equivalent
```

Symbol lookup phải giữ ABI metadata nếu symbol được gọi như typed function.

---

# 19. Typed Symbol Resolution

Không nên:

```text
let p = library.symbol("foo")
unsafe_cast(p)
```

là đường duy nhất.

Có thể:

```text
let foo = library.symbol<fn(i32) -> i32>("foo")?
```

Compiler kiểm tra:

- calling convention
- ABI
- function type
- target architecture

nhưng programmer vẫn chịu trách nhiệm nếu ABI contract không đáng tin.

---

# 20. Clock / Time

Axiom phải phân biệt:

```text
Instant
Duration
SystemTime
MonotonicTime
```

Không được dùng một `DateTime` duy nhất.

Semantics:

```text
Instant
```

dùng interval/measurement.

```text
SystemTime
```

có thể jump vì NTP/user changes.

---

# 21. Timer

Platform Services:

```text
Timer
Sleep
Deadline
```

Nhưng:

```text
sleep(1ms)
```

không có nghĩa chính xác CPU sẽ thức sau đúng 1ms.

API phải mô tả:

```text
minimum delay
deadline
clock source
resolution
```

---

# 22. Synchronization Mapping

Core có:

```text
Mutex
RwLock
Semaphore
Condvar
Atomic
```

Platform Services có thể cung cấp optimized implementation.

Ví dụ:

```text
Mutex<T>
```

có thể lower:

```text
Linux → futex
Windows → SRWLOCK / WaitOnAddress
Darwin → os_unfair_lock / platform primitive
```

Không cần ép mọi platform sử dụng cùng implementation.

---

# 23. OS Synchronization vs Axiom Synchronization

Native primitive phải được gắn semantic contract.

Ví dụ:

```text
LinuxFutex
```

không được tự động coi là:

```text
Mutex<T>
```

cho đến khi implementation chứng minh:

```text
ownership
memory ordering
wake semantics
blocking behavior
```

phù hợp.

---

# 24. Event / Notification

Platform-specific event mechanisms:

```text
epoll
kqueue
IOCP
io_uring
eventfd
WaitOnAddress
```

có thể nằm dưới:

```text
Poller
CompletionPort
EventSource
```

nhưng không được ép chúng vào một abstraction quá nghèo.

Axiom có thể có:

```text
Poller
CompletionQueue
```

và native extensions.

---

# 25. Async I/O

Async layer dùng Platform Services:

```text
AsyncFile
AsyncSocket
AsyncProcess
```

Backend:

```text
Linux:
    io_uring
    epoll

Windows:
    IOCP

Darwin:
    kqueue
    dispatch
    platform APIs
```

Executor chọn backend phù hợp.

Core `Future` không biết backend nào.

---

# 26. Socket API

Semantic model:

```text
Socket
TcpSocket
UdpSocket
UnixSocket
IpAddress
Endpoint
```

Nhưng native-specific:

```text
SO_REUSEPORT
TCP_FASTOPEN
IOCP
epoll
BPF
Windows extensions
```

vẫn phải truy cập được.

---

# 27. Network abstraction không được quá cao

Không nên chỉ có:

```text
HttpClient
```

mà phải có tầng thấp:

```text
Socket
Tcp
Udp
RawSocket
```

và tầng cao:

```text
Http
WebSocket
Tls
```

để systems programmer không bị khóa trong abstraction.

---

# 28. OS Handle Model

Windows dùng:

```text
HANDLE
```

Unix dùng:

```text
fd
```

Axiom cần semantic:

```text
OsHandle
```

nhưng representation target-specific.

Ví dụ:

```text
Handle<T>
```

có thể encode resource type ở compile time.

```text
Handle<File>
Handle<Socket>
Handle<Process>
```

Giảm nhầm resource.

---

# 29. Handle Ownership

Handle phải có ownership semantics.

Ví dụ:

```text
OwnedHandle<T>
BorrowedHandle<T>
```

Nhưng không expose lifetime annotation.

Compiler kiểm soát:

```text
OwnedHandle
    ↓ move
new owner
```

và:

```text
BorrowedHandle
```

không được outlive owner.

---

# 30. OS Error Model

Không nên ép mọi OS error thành integer.

Axiom semantic:

```text
OsError {
    domain
    code
}
```

Ví dụ:

```text
Linux errno
Windows GetLastError
Darwin errno
WASI errno
```

Có thể có:

```text
OsErrorKind
```

nhưng không được mất native code.

Ví dụ:

```text
error.kind()
error.raw_code()
error.domain()
```

---

# 31. Error Domains

```text
ErrorDomain {
    Axiom
    POSIX
    Windows
    Darwin
    WASI
    Android
}
```

Điều này giúp library xử lý generic error nhưng application vẫn có thể inspect native error.

---

# 32. Signals / Interrupts

Unix signal và hardware interrupt không nên giả lập thành cùng abstraction.

Tách:

```text
OsSignal
HardwareInterrupt
Exception
Trap
```

Embedded:

```text
@interrupt
fn timer_interrupt(...)
```

OS:

```text
SignalHandler
```

Core semantics khác nhau.

---

# 33. GUI Platform Service

Axiom không nên đưa GUI framework vào Core.

Platform Services có:

```text
Window
WindowHandle
Display
Monitor
InputEvent
Cursor
Clipboard
```

Native implementations:

```text
Win32
Cocoa
UIKit
Wayland
X11
Android
WASM browser
```

GUI toolkit cấp cao nằm Standard Library hoặc package ecosystem.

---

# 34. GPU

Platform Services nối:

```text
GPU Core
     ↓
GPU Platform Service
     ↓
Metal / Vulkan / DirectX / CUDA / ...
```

Không được làm:

```text
GPU == graphics
```

GPU platform có thể phục vụ:

- compute
- graphics
- video
- ML
- DMA

---

# 35. Device API

Có semantic:

```text
Device
DeviceId
DeviceInfo
DeviceBuffer
```

nhưng platform/device-specific APIs vẫn được phép.

Ví dụ:

```text
@platform(nvidia)
CudaDevice
```

không cần ép thành generic `GpuDevice` nếu điều đó làm mất feature.

---

# 36. Platform Extension Mechanism

Một abstraction quan trọng:

```text
platform<T>
```

hoặc equivalent mechanism.

Ví dụ:

```text
platform.windows {
    ...
}
```

```text
platform.linux {
    ...
}
```

Compiler có thể loại bỏ block không phù hợp.

Mục tiêu:

```text
cross-platform core
+
native escape hatch
```

---

# 37. API Stability

Platform Services API phải có:

```text
semantic version
availability
deprecation
target constraints
ABI contract
```

Tích hợp trực tiếp với:

```text
BOOTSTRAP-345
BOOTSTRAP-346
```

Ví dụ:

```text
@since(axsdk = 12)
@deprecated(axsdk = 15)
```

---

# 38. Platform Adapter Architecture

Implementation:

```text
platform/
├── common/
│   ├── file
│   ├── socket
│   ├── process
│   ├── thread
│   └── time
│
├── windows/
│   ├── file
│   ├── socket
│   ├── process
│   └── thread
│
├── linux/
│   ├── file
│   ├── socket
│   ├── process
│   └── thread
│
├── darwin/
├── android/
├── ios/
└── wasi/
```

Common semantic layer:

```text
Platform API
```

native layer:

```text
Platform Adapter
```

---

# 39. Compiler Specialization

Ví dụ:

```text
fn read_file(...) {
    ...
}
```

có implementation generic.

Compiler biết:

```text
target = linux
```

và specialization:

```text
read_file_linux
```

được inline.

Kết quả cuối cùng có thể chỉ còn syscall/native function.

Không còn abstraction object.

---

# 40. Platform Dispatch

Mặc định:

```text
compile-time dispatch
```

Không:

```text
runtime OS detection
```

trừ khi programmer yêu cầu.

Ví dụ không được tự động sinh:

```text
if Windows ...
else Linux ...
```

khi target đã biết.

---

# 41. Cross-Platform API Design Rule

Một API chỉ được đưa vào Platform Services nếu có:

```text
semantic common denominator
```

Ví dụ:

```text
File.read()
```

có semantic chung.

Nhưng:

```text
Windows Job Object
```

không cần giả vờ tồn tại trên Linux.

Nó thuộc native extension.

---

# 42. Native Extension Rule

Mỗi service có:

```text
portable API
+
native API
```

Ví dụ:

```text
Socket
Socket.linux()
Socket.windows()
```

hoặc module:

```text
platform::linux::epoll
platform::windows::iocp
```

Điều này giữ cho Axiom vừa portable vừa không bị “lowest common denominator”.

---

# 43. Không tạo Runtime Dependency vô ích

Ví dụ chương trình chỉ dùng:

```text
VirtualMemory
```

không được tự động link:

```text
network runtime
async runtime
GUI runtime
reflection runtime
```

Dependency graph quyết định chính xác runtime component nào được link.

---

# 44. CompilerDB bổ sung

```text
PlatformServiceDB
PlatformAdapterDB
PlatformApiDB
PlatformCapabilityDB
PlatformHandleDB
PlatformErrorDB
PlatformClockDB
PlatformIoDB
PlatformNetworkDB
PlatformProcessDB
PlatformThreadDB
PlatformMemoryDB
PlatformSyncDB
PlatformGuiDB
PlatformDeviceDB
PlatformAvailabilityDB
PlatformDispatchDB
```

Quan hệ:

```text
SdkDB
  ↓
PlatformContractDB
  ↓
PlatformServiceDB
  ↓
PlatformAdapterDB
  ↓
StandardLibrary
```

---

# 45. Diagnostics

Ví dụ programmer dùng:

```text
File.open(...)
```

trên target:

```text
wasm32-bare
```

compiler:

```text
AXPLAT001

Platform service `filesystem` is unavailable
for target `wasm32-bare`.

Required capability:
    filesystem

Available capabilities:
    memory
    computation

Suggested alternatives:
    - use embedded storage
    - provide a platform adapter
    - select a WASI target
```

Diagnostic phải machine-readable.

---

# 46. Native API Escape Hatch

Axiom không được khóa programmer.

Ví dụ:

```text
import platform.windows;

unsafe {
    let h = windows::CreateFileW(...);
}
```

Hoặc typed FFI wrapper:

```text
windows::FileHandle
```

Tất cả vẫn đi qua SDK/ABI verification.

---

# 47. Security

Platform API phải phân biệt:

```text
Safe
Unsafe
Privileged
Capability-restricted
```

Ví dụ:

```text
VirtualMemory.executable()
```

có thể yêu cầu unsafe/system capability.

Không được vì abstraction mà biến một OS operation nguy hiểm thành safe API nếu invariants chưa đủ.

---

# 48. Invariants

### `APLAT-01`
Platform Services must not change Axiom language semantics.

### `APLAT-02`
Portable platform APIs must have explicitly defined cross-platform semantics.

### `APLAT-03`
Platform-specific functionality must remain directly accessible.

### `APLAT-04`
Default platform dispatch is compile-time.

### `APLAT-05`
Unused platform implementations must be eliminated.

### `APLAT-06`
Platform abstraction must not require dynamic dispatch by default.

### `APLAT-07`
Platform services must not require a monolithic runtime.

### `APLAT-08`
OS handles must obey Axiom ownership semantics.

### `APLAT-09`
Borrowed platform handles cannot outlive their owners.

### `APLAT-10`
OS errors must preserve native error identity.

### `APLAT-11`
Path semantics must not assume Unicode-only representation.

### `APLAT-12`
Virtual memory is distinct from general allocation.

### `APLAT-13`
Thread, task, fiber and process are distinct semantic entities.

### `APLAT-14`
Async platform backends must lower into the existing Future model.

### `APLAT-15`
Native synchronization primitives must satisfy Axiom memory-order semantics before being exposed as safe abstractions.

### `APLAT-16`
Unsupported platform capabilities must produce deterministic diagnostics.

### `APLAT-17`
Platform APIs must integrate with SDK availability metadata.

### `APLAT-18`
Platform API selection must be target-deterministic.

### `APLAT-19`
Cross-platform APIs must not silently emulate unsupported native behavior.

### `APLAT-20`
Native extensions must not require portable abstraction.

### `APLAT-21`
Platform-specific code must participate in normal ownership/capability verification.

### `APLAT-22`
Platform Services must integrate with FFI/ABI contracts.

### `APLAT-23`
Platform APIs must participate in package/build dependency graphs.

### `APLAT-24`
Unused platform dependencies must not enter the final binary.

### `APLAT-25`
Platform service implementations must be independently testable.

### `APLAT-26`
Platform-specific APIs must expose availability constraints.

### `APLAT-27`
Platform abstractions must preserve native performance characteristics.

### `APLAT-28`
Freestanding targets must be able to use only explicitly available services.

### `APLAT-29`
Platform Services must support native-only applications without forcing cross-platform abstractions.

### `APLAT-30`
Every Platform Service must have a defined semantic contract independent of its implementation.

---

# 49. Definition of Done

`BOOTSTRAP-347` hoàn thành khi có:

```text
✓ Platform Service architecture
✓ Portable platform API model
✓ Native platform extension model
✓ Compile-time platform dispatch
✓ Platform capability system
✓ File service
✓ Path service
✓ Process service
✓ Thread service
✓ Virtual memory service
✓ Dynamic library service
✓ Clock/time service
✓ Timer service
✓ Synchronization adapter
✓ Async I/O adapter
✓ Socket/network service
✓ OS handle model
✓ OS error model
✓ Availability/deployment model
✓ GUI platform foundation
✓ Device platform foundation
✓ GPU platform integration
✓ WASM platform integration
✓ Embedded platform integration
✓ Native escape hatch
✓ Platform diagnostics
✓ Platform API dependency tracking
✓ Runtime dependency minimization
✓ CompilerDB integration
✓ ABI/SDK integration
✓ Conformance tests
✓ Cross-platform tests
```

---

# 50. Kiến trúc Axiom sau 346 + 347

Ta bắt đầu có một cấu trúc rất đẹp:

```text
                         AXIOM PROGRAM
                              │
             ┌────────────────┴────────────────┐
             │                                 │
       Standard Library                 Native Extensions
             │                                 │
             ▼                                 ▼
     Platform Services                   Native Platform API
             │                                 │
             └──────────────┬──────────────────┘
                            ▼
                       SDK Contract
                            │
                 ┌──────────┴──────────┐
                 │                     │
              ABI/FFI               Sysroot
                 │                     │
                 └──────────┬──────────┘
                            ▼
                     Native Platform
                            │
              ┌─────────────┼─────────────┐
            Linux        Windows       Apple/Android
```

Điểm cốt lõi:

> **Axiom không phải “một ngôn ngữ portable bằng cách hạ OS xuống mẫu số chung”.**

Mà là:

> **Một semantic core thống nhất + platform abstraction zero-cost + native escape hatch hoàn chỉnh.**

Đây là điều rất quan trọng để Axiom vừa phù hợp cho application development, vừa không đánh mất mục tiêu ban đầu của bạn: **ngôn ngữ systems có hiệu năng cao, compiler mạnh, abstraction bị xóa sạch khi không cần thiết, nhưng programmer vẫn có thể xuống sát OS/machine khi muốn.**