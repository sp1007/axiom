# BOOTSTRAP-327 — AXIOM OS / SYSTEM API INTEROP & PLATFORM ABSTRACTION ENGINE

Sau FFI-326, nhiệm vụ tiếp theo nên là giải quyết một vấn đề thực tế hơn: **Axiom sẽ tiếp xúc với Windows, Linux, macOS, iOS, Android, WASM và các API hệ điều hành như thế nào mà không làm Core phụ thuộc vào một OS cụ thể.**

Đây không phải là FFI mới. FFI-326 đã định nghĩa **cách gọi foreign code**. Task này định nghĩa **cách Axiom tổ chức và chuẩn hóa system API trên nhiều nền tảng**.

---

## 1. Mục tiêu

Axiom phải cho phép:

```axiom
file.open(...)
socket.connect(...)
thread.spawn(...)
process.spawn(...)
memory.map(...)
window.create(...)
gpu.create_device(...)
```

nhưng các API này phải nằm ở **library/platform layer**, không nhét vào Core language.

Kiến trúc:

```text
Axiom Core
    │
    ├── language semantics
    ├── ownership
    ├── capability
    ├── concurrency
    └── memory model
             │
             ▼
       Platform API
             │
      ┌──────┼─────────┐
      ▼      ▼         ▼
   Windows Linux    Apple
      │      │         │
    Win32   POSIX    Darwin
      │      │         │
      └──────┼─────────┘
             ▼
         Native OS
```

Core không biết `HANDLE`, `fd`, `HWND`, `pthread_t`, `mach_port_t`...

---

# 2. Platform API không phải OS abstraction giả tạo

Axiom không nên cố ép mọi OS thành một API giống hệt nhau.

Ví dụ:

```text
Windows process
Linux process
iOS process
WASM environment
```

không có cùng semantics.

Do đó:

> **Platform abstraction chỉ thống nhất semantic contract khi các nền tảng thực sự có semantic tương đương.**

Nếu không tương đương, API phải thể hiện khác biệt.

---

# 3. Platform capability model

Platform API phải mô hình hóa capability:

```text
Filesystem
Network
Process
Thread
Clock
Random
Environment
IPC
Window
Graphics
GPU
Audio
Camera
Microphone
Clipboard
Power
Device
```

Ví dụ một ứng dụng WASM có thể có:

```text
Filesystem = unavailable
Network = host-provided
Window = browser-provided
Clock = restricted
```

Trong khi native Linux:

```text
Filesystem = available
Process = available
RawSocket = available
```

---

# 4. Compile-time platform selection

Axiom cần:

```axiom
@cfg(os = "windows") {
    ...
}

@cfg(os = "linux") {
    ...
}

@cfg(os = "macos") {
    ...
}
```

và:

```axiom
@cfg(arch = "x86_64")
@cfg(arch = "aarch64")
```

Không nên tạo preprocessor kiểu C.

`@cfg` phải hoạt động trên declaration/HIR, không phải textual substitution.

---

# 5. Target profile

Compiler có:

```text
TargetTriple
```

nhưng Axiom nên bổ sung:

```text
PlatformProfile
```

Ví dụ:

```text
windows-x86_64-msvc
linux-x86_64-gnu
linux-aarch64
macos-aarch64
ios-aarch64
android-aarch64
wasm32
wasm64
freestanding-x86_64
```

Profile mô tả:

```text
OS
ABI
architecture
endianness
pointer width
atomic support
TLS
threads
filesystem
network
dynamic loading
GPU
GUI
exception model
```

---

# 6. Platform API là capability-gated

Ví dụ:

```axiom
fn read_file(path: Path) -> Result<Buffer, IoError>
```

không có nghĩa Core tự nhiên có filesystem.

Nó thuộc:

```text
Platform.Filesystem
```

Một `freestanding` binary có thể không link module này.

Điều này giúp giữ:

> **Không có monolithic runtime.**

---

# 7. System handle model

OS resource không nên trở thành raw pointer trong safe Axiom.

Ví dụ Windows:

```text
HANDLE
```

Linux:

```text
int fd
```

macOS:

```text
mach_port_t
```

được bọc thành:

```axiom
struct FileHandle { ... }
```

hoặc:

```axiom
extern type NativeFile;
```

với abstraction:

```text
File
Socket
Process
Thread
Event
Window
GpuDevice
```

---

# 8. Resource ownership

System resource phải tuân theo cùng ownership model.

Ví dụ:

```axiom
let file = File.open(path)?
```

`file` là owning value.

Khi scope kết thúc:

```text
File
 ↓
Drop
 ↓
close(fd)
```

Compiler không cần runtime GC.

---

# 9. Borrowed system handles

Không được copy arbitrary owning handle.

Ví dụ:

```axiom
let file = File.open(path)?

use(file)
```

`use()` có thể nhận:

```axiom
fn use(file: view<File>)
```

nếu chỉ cần đọc metadata.

Hoặc API system-level có thể expose:

```axiom
fn native_handle(file: view<File>) -> NativeHandle
```

nhưng native handle không trở thành ownership mới.

---

# 10. Stable handle vs physical address

Không dùng địa chỉ memory làm identity cho OS resource.

Ví dụ:

```text
File
Socket
Window
GPU object
Process
```

đều có:

```text
Logical Resource Identity
```

và có thể internally chứa:

```text
OS handle
generation
allocator state
component owner
```

Điều này tương thích trực tiếp với mô hình identity đã thiết kế trước.

---

# 11. Close semantics

System resource có:

```text
Drop
```

nhưng API cũng nên có:

```axiom
file.close() -> Result<(), IoError>
```

Phân biệt:

```text
close()
```

với:

```text
drop
```

vì close có thể thất bại.

Không được:

```text
Drop -> silently ignore important I/O failure
```

Nếu semantics OS yêu cầu báo lỗi khi close, programmer phải gọi `close()` explicit.

---

# 12. File API

API portable nên có semantic model:

```text
Path
File
FileOpenOptions
FileMetadata
FilePermissions
Directory
DirectoryEntry
```

nhưng không được giả định mọi OS hỗ trợ mọi feature.

Ví dụ:

```text
memory mapped file
direct I/O
file locking
async I/O
sparse files
extended attributes
```

được feature-gated.

---

# 13. Async I/O

Không xây một implementation async duy nhất.

Platform layer có thể dùng:

```text
Windows → IOCP
Linux → io_uring / epoll
macOS → kqueue
WASM → host/browser async
```

nhưng API semantic có thể là:

```axiom
async fn read(...)
```

Backend runtime quyết định implementation.

Core chỉ hiểu:

```text
Future
Poll
Await
```

---

# 14. Thread API

Platform API:

```axiom
Thread.spawn(...)
```

không được làm thay đổi semantic của Core concurrency.

Thread vẫn tuân:

```text
Send
Share
ownership
synchronization
```

Ví dụ:

```axiom
Thread.spawn(fn() {
    work(data)
})
```

Compiler kiểm tra capture của closure.

Nếu closure giữ giá trị không `Send`:

```text
compile error
```

Không đẩy trách nhiệm sang runtime.

---

# 15. Thread-local storage

Axiom cần semantic:

```text
Tls<T>
```

nhưng representation tùy OS.

Compiler có thể lower:

```text
Tls<T>
```

thành:

```text
Windows TLS
ELF TLS
Mach-O TLS
WASM TLS emulation/host
```

Không để programmer phải viết platform-specific TLS primitive trong code thông thường.

---

# 16. Process API

Process phải có ownership semantics:

```axiom
let p = Process.spawn(...)
```

`Process` là resource handle.

API:

```text
wait()
kill()
terminate()
id()
stdin()
stdout()
stderr()
```

`wait()` có thể consume hoặc borrow process tùy semantic.

Quan trọng:

```text
Process handle ≠ Process lifetime
```

OS process có thể tiếp tục tồn tại ngay cả khi một handle bị Drop.

---

# 17. IPC

IPC được phân loại:

```text
Pipe
UnixSocket
NamedPipe
SharedMemory
Event
Semaphore
MessageQueue
Socket
```

Axiom không nên ép tất cả thành một abstraction.

Các primitive có semantics khác nhau.

---

# 18. Shared memory

Đây là trường hợp đặc biệt quan trọng với memory model.

Ví dụ:

```text
SharedMemory<T>
```

không tự động biến thành:

```text
Share<T>
```

Shared memory chỉ nói rằng nhiều execution domain có thể truy cập cùng physical storage.

Compiler vẫn cần:

```text
ownership
capability
synchronization
atomicity
memory ordering
```

Do đó:

```text
SharedMemory<T>
+
mut_view<T>
```

không tự động an toàn.

---

# 19. Memory mapping

OS API:

```text
mmap
VirtualAlloc
MapViewOfFile
mach_vm_map
```

được wrap thành abstraction:

```axiom
MappedMemory
```

Nhưng phải phân biệt:

```text
owned memory
external memory
shared memory
device memory
file-backed memory
```

vì các storage domains khác nhau.

---

# 20. Virtual memory API

System programming cần low-level API:

```text
reserve
commit
decommit
protect
map
unmap
remap
```

nhưng đặt trong:

```text
system.memory
```

và nhiều API sẽ yêu cầu `unsafe`.

Ví dụ:

```axiom
unsafe {
    virtual_memory.protect(...)
}
```

Core memory model không cần biết `mprotect` tồn tại.

---

# 21. Atomics

Platform layer cung cấp capability information:

```text
AtomicSupport
LockFreeWidth
CacheLine
MemoryPageSize
```

Compiler dùng target information để optimize.

Nhưng semantics atomic vẫn thuộc Core concurrency model.

---

# 22. CPU feature detection

Axiom cần compile-time:

```text
@target_feature("avx2")
@target_feature("neon")
```

và runtime:

```text
cpu.features()
```

Compiler có thể tạo multi-versioning:

```text
foo.scalar()
foo.avx2()
foo.avx512()
```

và dispatch:

```text
CPU
 ↓
feature detection
 ↓
best valid implementation
```

Không được gọi code yêu cầu CPU feature mà target không hỗ trợ.

---

# 23. Platform-specific implementation

API:

```text
File
```

có thể có implementation:

```text
std/platform/windows/file.ax
std/platform/linux/file.ax
std/platform/macos/file.ax
std/platform/android/file.ax
```

Resolver chọn implementation bằng target profile.

Không compile tất cả rồi DCE nếu không cần thiết.

---

# 24. Platform API hierarchy

Nên tổ chức:

```text
std
├── core
├── alloc
├── collections
├── io
├── fs
├── net
├── process
├── thread
├── sync
├── time
├── crypto
├── compression
├── gpu
└── platform
    ├── windows
    ├── linux
    ├── macos
    ├── ios
    ├── android
    └── wasm
```

`platform.*` expose OS-specific API.

`std.fs`, `std.net`... là portable semantic API.

---

# 25. Không nên có "OS object hierarchy"

Không tạo:

```text
SystemObject
  ├── File
  ├── Socket
  ├── Process
  └── Window
```

đây lại biến Axiom thành OOP framework.

Thay vào đó:

```text
struct File
struct Socket
struct Process
struct Window
```

với functions/method syntax:

```text
file.read()
socket.send()
process.wait()
window.show()
```

hoàn toàn phù hợp với struct + first-parameter method model của Axiom.

---

# 26. Error normalization

Portable API có:

```axiom
enum IoErrorKind {
    NotFound,
    PermissionDenied,
    AlreadyExists,
    InvalidInput,
    WouldBlock,
    Interrupted,
    TimedOut,
    ConnectionRefused,
    ...
}
```

nhưng phải giữ:

```text
NativeError
```

để không mất thông tin OS.

Ví dụ:

```text
IoError {
    kind
    native_code
}
```

Portable code dùng `kind`.

Platform-specific code dùng `native_code`.

---

# 27. Time API

Phải phân biệt:

```text
Instant
Duration
SystemTime
MonotonicClock
WallClock
CPUTime
```

Không được dùng một `Time` type cho tất cả.

`Instant` dùng monotonic clock.

`SystemTime` có thể nhảy do NTP/user adjustment.

Điều này rất quan trọng cho correctness của timeout/deadline.

---

# 28. Randomness

Phân biệt:

```text
PseudoRandom
SecureRandom
HardwareRandom
OSRandom
```

Không để:

```axiom
random()
```

mập mờ về security.

Ví dụ:

```axiom
secure_random.fill(...)
```

phải route tới OS/hardware entropy source phù hợp.

---

# 29. Environment

Environment API:

```text
env.args()
env.get()
env.current_dir()
env.home_dir()
```

nhưng `Environment` là host capability.

Freestanding:

```text
Environment = unavailable
```

Compiler có thể loại bỏ hoàn toàn dependency nếu chương trình không sử dụng.

---

# 30. GUI / Windowing

Không đưa GUI vào Core.

Platform-independent layer có thể cung cấp:

```text
Window
Event
Display
Input
Clipboard
```

nhưng backend:

```text
Windows → Win32
macOS → Cocoa
iOS → UIKit
Linux → Wayland/X11
Android → Android NDK
WASM → Browser
```

Không giả định các feature tương đương.

---

# 31. GPU integration

GPU platform layer sử dụng model đã frozen:

```text
Host
Device
DeviceBuffer
DeviceView
GpuEvent
@kernel
```

Backend có thể:

```text
CUDA
HIP
Metal
Vulkan
DirectX
WebGPU
```

FFI-326 cung cấp foreign bindings.

Platform-327 cung cấp semantic API.

GPU compiler/runtime quyết định lowering.

---

# 32. WASM

WASM phải được xem là một platform profile thực sự, không phải "CPU khác".

Ví dụ:

```text
wasm32
```

có thể thiếu:

```text
OS process
raw filesystem
native threads
native dynamic linking
```

nhưng có:

```text
linear memory
host imports
WebAssembly modules
browser/host capabilities
```

Axiom compiler phải biết điều này từ `TargetProfile`.

---

# 33. Freestanding

Một chương trình:

```axiom
@freestanding
fn kernel_main(...) { ... }
```

không được tự động kéo:

```text
filesystem
thread runtime
async executor
network stack
Unicode runtime
dynamic loader
```

Binary dependency phải được xác định bởi capability graph.

---

# 34. Capability graph

Build system tạo:

```text
Application
    │
    ├── std.io
    │      └── OS
    │
    ├── std.net
    │      └── OS
    │
    └── std.alloc
           └── allocator
```

Nếu bỏ `std.net`:

```text
network backend
socket FFI
network runtime
```

không xuất hiện trong binary.

Đây là một phần quan trọng để đạt mục tiêu binary nhỏ.

---

# 35. Platform ABI manifest

`.axif` bổ sung:

```text
PLATFORM_CONTRACT
```

gồm:

```text
target
minimum_os_version
required_cpu_features
required_platform_capabilities
required_syscalls
required_runtime_components
required_dynamic_libraries
required_frameworks
```

Ví dụ:

```text
Windows >= 10
x86_64
AVX2
kernel32
user32
```

---

# 36. Platform API và security

Platform capability phải đi qua Security subsystem.

Ví dụ:

```text
filesystem.read
network.connect
process.spawn
device.camera
microphone
```

có thể yêu cầu capability/token.

Đặc biệt quan trọng với:

```text
WASM
sandbox
mobile
plugin
component
```

---

# 37. Compiler architecture

Thêm:

```text
compiler/platform/
    target_profile/
        target_profile.ax
        platform_profile.ax
        feature_db.ax

    capability/
        platform_capability.ax
        capability_graph.ax

    resolver/
        platform_resolver.ax
        cfg_resolver.ax
        backend_resolver.ax

    abi/
        system_abi.ax

    diagnostics/
        platform_diagnostics.ax
```

CompilerDB:

```text
TargetProfileDB
PlatformProfileDB
PlatformCapabilityDB
SystemApiDB
```

---

# 38. Build system integration

Build graph phải biết:

```text
source dependency
semantic dependency
platform dependency
foreign library dependency
system library dependency
framework dependency
runtime dependency
```

Ví dụ:

```text
app
 ↓
std.net
 ↓
linux socket backend
 ↓
libc / kernel ABI
```

hoặc:

```text
app
 ↓
std.window
 ↓
macOS backend
 ↓
AppKit
```

---

# 39. API chính

```text
resolve_platform_api()
resolve_platform_backend()
query_target_profile()
query_platform_capability()
check_platform_requirement()
resolve_system_library()
resolve_framework()
check_minimum_os()
check_cpu_features()
compute_platform_dependency_graph()
explain_platform_failure()
```

CLI:

```text
axiom target inspect
axiom platform inspect
axiom platform requirements
axiom platform deps
axiom platform check
axiom platform explain
```

---

# 40. Invariants

```text
APLATFORM-01
Core language semantics must not depend on a specific OS.

APLATFORM-02
OS APIs belong to libraries/platform layers.

APLATFORM-03
Platform APIs must preserve Axiom ownership semantics.

APLATFORM-04
OS resources are explicit owned or borrowed resources.

APLATFORM-05
Physical OS handles are never automatically Axiom ownership values.

APLATFORM-06
System resource destruction is deterministic.

APLATFORM-07
Fallible close operations are explicit.

APLATFORM-08
Platform capability requirements are part of the build graph.

APLATFORM-09
Unavailable platform capabilities are compile-time errors when statically known.

APLATFORM-10
@cfg is semantic selection, not textual preprocessing.

APLATFORM-11
Platform implementations may differ when OS semantics differ.

APLATFORM-12
Unknown platform behavior must not be silently normalized.

APLATFORM-13
Target-specific ABI is resolved through AbiDB.

APLATFORM-14
Foreign system APIs use FFI-326 contracts.

APLATFORM-15
Platform API must not force a monolithic runtime.

APLATFORM-16
Unused platform subsystems must be removable from final binaries.

APLATFORM-17
Freestanding builds must not depend on hosted OS APIs.

APLATFORM-18
WASM is a distinct platform profile.

APLATFORM-19
GPU APIs remain separate execution/storage domains.

APLATFORM-20
System calls crossing unsafe boundaries must preserve verifier contracts.

APLATFORM-21
Platform errors must preserve native error information.

APLATFORM-22
Monotonic and wall-clock semantics must remain distinct.

APLATFORM-23
System allocators must never cross ownership boundaries implicitly.

APLATFORM-24
Platform API dependencies participate in .axif fingerprints.

APLATFORM-25
Platform requirements participate in binary compatibility.

APLATFORM-26
Security capability requirements participate in platform resolution.

APLATFORM-27
Component/plugin platform requirements are validated before loading.

APLATFORM-28
Platform-specific code must not leak into portable semantic APIs.

APLATFORM-29
Compiler optimization may exploit target capabilities only when target contract proves availability.

APLATFORM-30
The same Axiom source must have deterministic semantic interpretation for a given target profile.
```

---

## Kết quả kiến trúc

Sau task này, Axiom có ba lớp interop rất rõ:

```text
                    AXIOM
                      │
             ┌────────┴────────┐
             │                 │
        Axiom Core         Library Layer
                               │
                    ┌──────────┴──────────┐
                    │                     │
             Platform API             FFI API
                    │                     │
             ┌──────┴──────┐       ┌──────┴──────┐
             │             │       │             │
          Windows        Linux    C/C++       Foreign
          macOS          WASM     OS API      Libraries
```

Trong đó:

- **Core** giữ semantic guarantees.
- **FFI-326** biết cách giao tiếp với foreign ABI.
- **Platform-327** biết API hệ điều hành nào tồn tại và semantic khác nhau ra sao.
- **Component-325** quản lý code/resource boundary động.
- **ABI-324** đảm bảo binary compatibility.

Đây là nền móng để Axiom có thể vừa là **systems language**, vừa viết ứng dụng native đa nền tảng mà không biến Core thành một đống OS-specific đặc biệt.