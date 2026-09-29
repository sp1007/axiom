Tiếp tục với **OS-ABI-001**. Đây là lớp cuối cùng nối Axiom từ compiler/runtime xuống hệ điều hành.

# OS-ABI-001 — OS & Platform Layer

## 1. Quyết định nền tảng: Axiom không chọn “syscall hoặc libc” làm một con đường duy nhất

Tôi đề xuất **3 mức truy cập**:

```text
Application
    │
    ├── std::fs / std::net / std::thread
    │
    ├── os::linux / os::windows / os::darwin
    │
    └── sys::linux / sys::win32 / sys::darwin
                         │
                         ↓
                     OS ABI
```

Trong đó:

### Level 1 — Portable API

```text
std::fs
std::net
std::thread
std::time
```

Người dùng bình thường nên dùng tầng này.

### Level 2 — Platform API

```text
os::linux
os::windows
os::darwin
os::android
```

Dùng khi cần tính năng đặc thù hệ điều hành.

### Level 3 — Raw OS ABI

```text
sys::linux
sys::win32
sys::darwin
```

Dành cho systems programming.

---

# 2. Không nên để libc là một phần của Axiom Core

Ví dụ Linux:

```text
Axiom
 ↓
Core
 ↓
libc
```

không được là kiến trúc bắt buộc.

Thay vào đó:

```text
Axiom
 ↓
OS abstraction
 ├── libc ABI
 └── direct syscall ABI
```

cả hai đều hợp lệ.

Điều này cho phép:

```text
tiny binary
```

dùng direct syscall nếu cần, nhưng:

```text
normal desktop/server application
```

vẫn có thể dùng libc ecosystem.

---

# 3. Nhưng direct syscall không nên là API portable

Không nên viết:

```text
std::fs::open()
```

rồi compiler biến thành syscall Linux.

API semantics phải độc lập:

```text
std::fs::open
```

có contract của Axiom.

Implementation Linux có thể:

```text
open
 → libc
```

hoặc:

```text
open
 → syscall
```

tùy target/profile.

---

# 4. Vì sao không nên mặc định direct syscall?

Bởi vì syscall ABI có thể có nhiều vấn đề:

- khác OS;
- khác architecture;
- thay đổi implementation;
- cancellation semantics;
- signal interaction;
- thread-local behavior;
- ABI conventions;
- platform-specific features.

Do đó:

> **Direct syscall là capability hệ thống, không phải abstraction mặc định.**

---

# 5. Linux

Axiom Linux target:

```text
x86_64-linux
aarch64-linux
riscv64-linux
```

nên có:

```text
sys::linux
os::linux
```

Ví dụ:

```text
sys::linux::syscall(...)
```

là low-level unsafe/system API.

Còn:

```text
std::fs::File
```

là safe abstraction.

---

# 6. Windows

Windows phức tạp hơn vì không nên xây standard library trực tiếp trên NT syscall numbers.

Tầng:

```text
std
 ↓
os::windows
 ↓
Win32 ABI
 ↓
Windows
```

là lựa chọn mặc định.

Ví dụ:

```text
std::fs
 ↓
CreateFileW / ReadFile / WriteFile
```

thay vì:

```text
NtCreateFile
```

cho API thông thường.

Raw NT interface có thể tồn tại trong:

```text
sys::windows::nt
```

nhưng là advanced/system API.

---

# 7. macOS

Tương tự:

```text
std
 ↓
os::darwin
 ↓
Darwin ABI
 ↓
macOS
```

và có thể có:

```text
sys::darwin
```

cho low-level interface.

---

# 8. iOS

iOS nên là **target riêng**, không đơn giản coi là macOS nhỏ hơn.

Ví dụ:

```text
aarch64-ios
```

có platform policy riêng:

```text
sandbox
entitlements
code signing
UIKit/Metal ecosystem
```

Axiom compiler tạo Mach-O compatible binary nhưng deployment/signing là lớp platform/deployment.

---

# 9. Android

Android:

```text
aarch64-android
```

nên có:

```text
std
 ↓
os::android
 ↓
Bionic / Android NDK ABI
 ↓
Linux kernel
```

Không nên bắt người dùng Axiom biết chi tiết Bionic nếu họ chỉ dùng:

```text
std::fs
std::thread
std::net
```

---

# 10. WASM

WASM là trường hợp đặc biệt.

Không có:

```text
syscall
```

theo nghĩa CPU/OS thông thường.

Ta có:

```text
Axiom
 ↓
WASM backend
 ↓
WASM module
 ↓
WASI / browser / host
```

Do đó:

```text
std::fs
```

có implementation khác.

Compiler không được giả định:

```text
all targets = POSIX-like OS
```

---

# 11. UEFI

Axiom rất phù hợp với UEFI vì không cần runtime lớn.

Target:

```text
x86_64-uefi
aarch64-uefi
```

có thể:

```text
Axiom
 ↓
PE/COFF
 ↓
UEFI executable
```

với:

```text
freestanding
```

profile.

---

# 12. Bare metal

Cần hỗ trợ:

```text
target = bare-metal
```

Ví dụ:

```text
aarch64-none
riscv64-none
arm-none
x86_64-none
```

Không có:

```text
OS
libc
allocator
thread runtime
```

trừ khi người dùng tự cung cấp.

Entry point có thể:

```text
@entry
fn reset() {
}
```

---

# 13. Entry point nên explicit ở system layer

Bình thường:

```text
fn main()
```

Nhưng embedded:

```text
@entry
fn reset() {
}
```

Bootloader:

```text
@entry
fn boot(info: BootInfo) {
}
```

UEFI:

```text
@entry
fn efi_main(...) -> Status {
}
```

Không nên nhồi tất cả vào `main`.

---

# 14. Process model

Process không nên là Core primitive.

Std:

```text
std::process
```

Platform implementation:

```text
Linux → fork/exec/wait...
Windows → CreateProcess...
```

Axiom API nên cố gắng thống nhất semantics:

```text
Process.spawn(...)
Process.wait()
Process.kill(...)
```

nhưng không giả vờ rằng mọi OS có semantics giống nhau.

Những khác biệt observable phải được expose qua platform API.

---

# 15. Thread model đã có

Ta đã chốt:

```text
Thread
Fiber
Task
Future
```

OS layer chỉ cung cấp primitive:

```text
OS thread
TLS
sleep
yield
affinity
priority
```

Scheduler không thuộc OS layer.

Ví dụ:

```text
Thread.spawn(...)
```

có thể gọi:

```text
os::thread::create(...)
```

nhưng:

```text
async executor
```

là Axiom runtime/library.

---

# 16. TLS

TLS phải là primitive backend/runtime vì ABI rất phụ thuộc target.

Axiom semantics:

```text
static thread_local COUNTER: i32
```

compiler lower xuống:

```text
TLS storage
```

Linux/Windows/macOS có implementation khác nhau.

Programmer không cần biết:

```text
TLS model
initial-exec
local-exec
general-dynamic
```

trừ system-level API.

---

# 17. Virtual memory

Tôi đề xuất API:

```text
std::memory
```

cho abstraction thông thường.

Low-level:

```text
os::memory
```

có:

```text
reserve
commit
decommit
protect
map
unmap
```

Ví dụ:

```text
reserve(size)
commit(region, permissions)
protect(region, ReadOnly)
```

Điều này rất quan trọng cho:

- custom allocator;
- GC library nếu ai đó tự viết;
- JIT;
- game engine;
- VM;
- database;
- shared memory.

---

# 18. Memory protection phải phản ánh W^X

Platform layer nên hiểu:

```text
Read
Write
Execute
```

và mặc định không cho:

```text
RWX
```

trừ explicit unsafe/system request.

JIT cần:

```text
RW
 ↓
seal
 ↓
RX
```

thay vì giữ:

```text
RWX
```

---

# 19. File I/O

Std:

```text
File.open
File.read
File.write
```

không expose OS handle trực tiếp.

Nhưng phải có:

```text
File.raw_handle()
```

ở system API.

Raw handle là resource identity:

```text
OwnedHandle<T>
```

có Drop.

Điều này rất phù hợp với ownership model.

---

# 20. OS handle không phải memory pointer

Ví dụ Windows:

```text
HANDLE
```

Linux:

```text
fd
```

không nên biểu diễn bằng:

```text
*mut void
```

Chúng phải là type riêng.

Ví dụ:

```text
FileHandle
SocketHandle
ProcessHandle
ThreadHandle
```

Có thể bên dưới là:

```text
u32
isize
pointer
```

nhưng semantics khác nhau.

---

# 21. Handle nên hỗ trợ ownership

Ví dụ:

```text
let file = File.open(...);
```

`file` sở hữu OS resource.

Move:

```text
let f2 = file;
```

chuyển ownership.

Drop:

```text
drop(f2);
```

đóng resource.

Không cần:

```text
close()
```

cho trường hợp bình thường.

Nếu close có thể thất bại và người dùng cần biết:

```text
file.close() -> Result<(), Error>
```

phải được gọi explicit.

Điều này phù hợp với nguyên tắc:

> Drop không truyền recoverable error.

---

# 22. Socket

Socket cũng nên là resource-owning type:

```text
TcpSocket
UdpSocket
UnixSocket
```

Không phải raw integer trong safe API.

Low-level:

```text
RawSocket
```

nằm ở system layer.

---

# 23. Blocking vs nonblocking

Không nên để một `Socket` mơ hồ.

Semantics phải rõ:

```text
BlockingSocket
NonBlockingSocket
```

hoặc mode là property.

Đặc biệt async:

```text
async TcpStream
```

không nên tự tạo OS thread cho mỗi connection.

---

# 24. I/O readiness

Đây là cầu nối giữa OS và async scheduler.

Platform layer cung cấp:

```text
Poller
```

Linux:

```text
epoll
```

Windows:

```text
IOCP
```

BSD/macOS:

```text
kqueue
```

WASM:

```text
host/browser mechanism
```

Axiom scheduler chỉ cần abstraction:

```text
register
wait
wake
cancel
```

Không cần biết `epoll` hay `IOCP`.

---

# 25. Clock

Có ít nhất:

```text
Instant
Duration
SystemTime
```

Phải phân biệt:

```text
monotonic clock
```

và:

```text
wall clock
```

`Instant` dùng:

```text
timeout
benchmark
scheduler
```

`SystemTime` dùng:

```text
timestamp
file metadata
calendar time
```

Không được dùng wall clock cho timeout chính xác.

---

# 26. Signals / exceptions

Unix:

```text
SIGINT
SIGTERM
SIGSEGV
```

Windows:

```text
SEH
console events
```

không nên được ép vào một semantics giả tạo hoàn toàn giống nhau.

Platform API:

```text
os::signal
```

cung cấp phần portable.

Low-level:

```text
sys::signal
```

cho OS-specific.

---

# 27. Hardware exceptions

Không nên biến:

```text
divide by zero
page fault
illegal instruction
```

thành Axiom exception.

Đây là machine/OS fault.

Profile quyết định:

```text
trap
panic
OS exception
abort
```

Compiler semantics phải rõ.

---

# 28. Dynamic libraries

Axiom phải hỗ trợ:

```text
.so
.dll
.dylib
```

nhưng dynamic loading là OS abstraction.

Std:

```text
DynamicLibrary.open(...)
symbol(...)
close(...)
```

Raw API:

```text
os::dynamic_library
```

Cần chú ý ownership:

```text
LibraryHandle
```

giữ module sống trong thời gian symbol/function pointer còn được sử dụng.

Đây là một trường hợp rất quan trọng của capability/lifetime analysis.

---

# 29. Function pointer từ dynamic library

Không được cho phép:

```text
lib.close();
fn_ptr();
```

trong safe code.

Compiler phải hiểu:

```text
fn_ptr
    depends on
LibraryHandle
```

hoặc API phải trả abstraction bảo đảm lifetime.

Đây là ví dụ cực đẹp cho capability model của Axiom.

---

# 30. Environment

Environment variables:

```text
std::env
```

là OS interaction.

Comptime **không được tự động đọc environment**.

Nếu comptime muốn:

```text
ENV["BUILD_MODE"]
```

phải khai báo external input.

Điều này giữ:

```text
ACOMP-24
```

đã chốt trước đây.

---

# 31. Command line

Hosted program:

```text
fn main(args: Args)
```

hoặc:

```text
std::env::args()
```

Compiler/startup chuyển OS-provided arguments thành Axiom representation.

Không cần global runtime object.

---

# 32. Platform target description

Target không chỉ là:

```text
x86_64-linux
```

mà nên là cấu trúc:

```text
Target {
    architecture
    pointer_width
    endian
    os
    abi
    object_format
    calling_convention
    features
    tls_model
    page_size
    atomic_capabilities
    unwind_model
}
```

Ví dụ:

```text
x86_64-linux-gnu
x86_64-linux-musl
x86_64-windows-msvc
aarch64-linux
aarch64-apple-darwin
aarch64-apple-ios
wasm32-wasi
riscv64-linux
```

---

# 33. Target triple không được leak vào source semantics

Không nên:

```text
if target == x86_64:
```

trong Core semantics.

Có thể dùng:

```text
@cfg(target_os = "linux")
```

ở compile-time/platform layer.

Nhưng semantic core vẫn độc lập.

---

# 34. Conditional compilation

Nên có:

```text
@cfg(...)
```

thay vì macro preprocessor kiểu C.

Ví dụ:

```text
@cfg(os = "windows")
fn platform_name() -> String {
    ...
}
```

và:

```text
@cfg(os = "linux")
fn platform_name() -> String {
    ...
}
```

Compiler loại branch/function không phù hợp trước codegen.

---

# 35. Platform constants

Compiler nên expose target information qua comptime:

```text
target.os
target.arch
target.pointer_width
target.endian
target.features
```

Nhưng phải phân biệt:

```text
compile-time target information
```

với:

```text
runtime environment
```

---

# 36. CPU features

Đã có `target features`.

Ví dụ:

```text
@target_feature("avx2")
fn process(...) { ... }
```

Compiler có thể tạo:

```text
generic version
AVX2 version
AVX512 version
```

và dispatch runtime nếu programmer/library yêu cầu.

Không nên tự động giả định mọi CPU chạy binary đều có AVX2.

---

# 37. Platform layer không nên là một giant abstraction

Tránh:

```text
Platform {
    300 methods
}
```

Thay vào đó:

```text
os::fs
os::net
os::thread
os::memory
os::process
os::time
os::tls
os::dynamic
os::signal
```

Các capability độc lập.

---

# 38. Native application dependency graph

Ví dụ một chương trình:

```text
fn main() {
    print("Hello");
}
```

có thể:

```text
main
 ↓
stdout
 ↓
OS I/O
```

Không có:

```text
network
filesystem
thread
async
allocator
```

Một web server:

```text
main
 ↓
async executor
 ↓
network
 ↓
OS readiness
 ↓
threads
 ↓
TLS
 ↓
allocator
```

Runtime lớn hơn là **do application semantics**, không phải vì ngôn ngữ bắt buộc.

---

# 39. Tôi đề xuất thêm các invariant

### `AOS-20 — OS APIs Are Outside Core`

Core semantics không phụ thuộc hệ điều hành.

### `AOS-21 — Platform Implementations May Differ`

Cùng std API có thể dùng mechanism khác nhau trên từng OS.

### `AOS-22 — Direct OS ABI Is Explicit`

Raw syscall/OS ABI chỉ thuộc system layer.

### `AOS-23 — libc Is Optional`

Hosted Axiom không bắt buộc libc nếu target/profile không cần.

### `AOS-24 — OS Resources Are Owned Resources`

File/socket/process/thread handles có ownership semantics.

### `AOS-25 — Raw Handles Are Not Raw Pointers`

OS handles có type semantics riêng.

### `AOS-26 — Resource Drop Is Deterministic`

Owned OS resources được release deterministic.

### `AOS-27 — Recoverable Close Errors Are Explicit`

Drop không truyền recoverable cleanup error.

### `AOS-28 — Platform Async Uses Native Readiness`

Async I/O có thể sử dụng epoll/IOCP/kqueue/WASI host mechanisms.

### `AOS-29 — No Hidden Thread-per-Async-Operation`

Async abstraction không tự động tạo OS thread.

### `AOS-30 — Hosted and Freestanding Are Separate Profiles`

### `AOS-31 — OS Handles Cannot Outlive Their Owning Resource`

### `AOS-32 — Dynamic Symbols Cannot Outlive Their Module`

### `AOS-33 — W^X Is Default`

### `AOS-34 — Target Information Is Explicitly Available At Comptime`

### `AOS-35 — Runtime Environment Is Not Implicit Comptime Input`

### `AOS-36 — OS ABI Is Target-Specific`

### `AOS-37 — Platform Details Do Not Define Language Semantics`

### `AOS-38 — Raw OS Interfaces Are Unsafe/System-Level`

### `AOS-39 — OS Resource Identity Is Distinct From Memory Identity`

### `AOS-40 — Native Axiom Does Not Require Axiom OS Runtime`

---

# 40. Kiến trúc Axiom lúc này

Ta đã có một đường rất rõ:

```text
                   Axiom Language
                         │
              ┌──────────┴──────────┐
              │                     │
             Core                Comptime
              │
              ↓
             MIR
              ↓
             LIR
              ↓
       Machine Backend
              ↓
            Object
              ↓
           Linker
              │
              ↓
       ┌───────────────┐
       │   Executable  │
       └───────┬───────┘
               │
        OS / Platform ABI
               │
       ┌───────┼────────┐
       ↓       ↓        ↓
     Linux   Windows   Darwin
```

Trong khi runtime nằm **bên cạnh**, không nằm giữa compiler và mọi chương trình:

```text
                Axiom Program
                     │
           ┌─────────┴─────────┐
           │                   │
        Core semantics     Optional runtime
                               │
                ┌──────────────┼──────────────┐
                ↓              ↓              ↓
             Alloc           Thread         Async
                │              │              │
                └──────────────┼──────────────┘
                               ↓
                           OS ABI
```

Đây là một kiến trúc rất mạnh cho mục tiêu ban đầu của Axiom.

---

# Tiếp theo: `IO-ASYNC-001`

Bây giờ có một nút thắt lớn cần giải quyết trước khi thiết kế `std::net`, `std::fs`, HTTP, database...

Đó là:

**I/O model thống nhất của Axiom.**

Ta cần chốt:

```text
sync I/O
async I/O
blocking
non-blocking
readiness
completion
epoll
IOCP
kqueue
io_uring
WASI
file I/O
socket I/O
zero-copy
buffer ownership
DMA
```

Đặc biệt phải trả lời một câu rất quan trọng:

> **Axiom có nên dùng một I/O abstraction chung cho sync + async, hay tách hẳn hai mô hình?**

Tôi nghiêng về **một resource/buffer model chung nhưng hai execution API riêng**, vì nó khớp rất tốt với ownership + capability + async model mà chúng ta đã chốt.