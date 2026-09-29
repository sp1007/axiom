Tiếp tục với **STDLIB-001 — Axiom Core / Runtime / Std Boundary**. Đây là phần rất quan trọng trước khi bắt đầu bootstrap compiler bằng chính Axiom.

# STDLIB-001 — CORE / RUNTIME / STD

## 1. Mục tiêu lớn

Axiom phải tránh mô hình:

```text
Program
   ↓
Huge Runtime
   ↓
GC / allocator / scheduler / reflection / libc...
```

Thay vào đó:

```text
                 ┌───────────────┐
                 │    Axiom      │
                 │    Program    │
                 └───────┬───────┘
                         │
             ┌───────────┴───────────┐
             │                       │
           Core                    Std
             │                       │
       language primitives      high-level APIs
             │                       │
             └──────────┬────────────┘
                        │
                 Optional Runtime
                        │
              ┌─────────┼─────────┐
              │         │         │
           Thread      Async     Alloc
              │         │         │
             OS       Executor   OS
```

Ba khái niệm phải **tách biệt hoàn toàn**:

```text
Core ≠ Runtime ≠ Std
```

---

# 2. `core`

`core` là tầng thấp nhất.

Nó phải có khả năng hoạt động trong:

```text
freestanding
bare metal
kernel
bootloader
embedded
GPU
OS process
```

Không được mặc định yêu cầu:

```text
OS
filesystem
network
thread
heap
dynamic loader
libc
```

---

# 3. Core chứa gì?

Ví dụ:

```text
core/
├── primitives
├── option
├── result
├── slice
├── string-basic
├── array
├── tuple
├── enum
├── numeric
├── traits
├── atomics
├── synchronization primitives interfaces
├── intrinsics
├── memory
├── ptr
├── simd
└── compiler-builtins
```

Nhưng phải cực kỳ cẩn thận:

> `core` không phải là "standard library thu nhỏ".

Nó là **semantic foundation**.

---

# 4. Compiler Builtins

Một số chức năng không thể hoặc không nên viết hoàn toàn bằng Axiom ban đầu.

Ví dụ:

```text
memcpy
memmove
memset
memcmp
integer division
128-bit arithmetic
atomic primitives
stack probing
floating-point helpers
```

Axiom compiler có thể lower trực tiếp:

```text
copy(...)
```

thành intrinsic hoặc machine instructions.

Nếu target không có instruction tương ứng:

```text
compiler builtin
```

được sinh ra.

---

# 5. Builtin không đồng nghĩa Runtime

Ví dụ:

```text
memcpy()
```

có thể là:

```text
inline machine instructions
```

hoặc:

```text
compiler-generated builtin
```

Nó không có nghĩa executable phải link:

```text
libaxiom-runtime.so
```

---

# 6. Core không được cấp phát heap

Đây là một nguyên tắc nên đóng băng:

> **Core không giả định tồn tại heap.**

Ví dụ:

```text
Array<T, N>
```

hoạt động bình thường.

Nhưng:

```text
Vec<T>
Box<T>
String
```

có thể cần allocator.

Allocator nằm ở tầng cao hơn.

---

# 7. `runtime`

Runtime là **optional execution support**.

Ví dụ:

```text
runtime/
├── allocator
├── panic
├── thread
├── tls
├── async
├── unwind
├── io
├── dynamic
└── startup
```

Mỗi thành phần độc lập.

Không có:

```text
monolithic runtime
```

---

# 8. Runtime Component Model

Thay vì:

```text
runtime = on/off
```

nên có:

```text
RuntimeRequirements {
    allocator
    threads
    tls
    async_executor
    unwind
    io
    startup
}
```

Ví dụ:

### Chương trình đơn giản

```text
allocator = false
threads = false
async = false
unwind = false
```

### Server

```text
allocator = true
threads = true
tls = true
io = true
async = true
```

Linker chỉ đưa phần cần thiết vào executable.

---

# 9. `std`

`std` là thư viện tiện ích cấp cao.

Ví dụ:

```text
std/
├── collections
├── string
├── filesystem
├── networking
├── process
├── thread
├── async
├── time
├── io
├── sync
├── random
├── unicode
├── path
└── environment
```

`std` có thể phụ thuộc:

```text
std
 ↓
runtime
 ↓
os
 ↓
sys
```

nhưng chiều ngược lại không được phép.

---

# 10. Dependency Direction

Đóng băng:

```text
Application
    ↓
Std
    ↓
Runtime
    ↓
OS / Sys
    ↓
Machine
```

và:

```text
Core
```

ở đáy.

Không cho:

```text
Core → Std
Core → Runtime
```

---

# 11. Freestanding

Axiom phải có profile:

```text
--freestanding
```

Khi đó:

```text
std = unavailable
runtime = none
```

hoặc chỉ những component explicit.

Ví dụ:

```text
@entry
fn _start() -> never {
    let x: u64 = 42;
    ...
}
```

có thể chạy mà không cần heap.

---

# 12. `no_std` không nên là một "chế độ đau khổ"

Axiom nên thiết kế sao cho:

```text
Core
```

đủ sạch để lập trình hệ thống trực tiếp.

Không nên để người dùng phải đấu với hàng loạt implicit dependency như:

```text
panic handler
allocator magic
runtime symbols
compiler runtime
```

Mỗi dependency phải có lý do rõ ràng.

---

# 13. Panic

Panic runtime là optional.

```text
panic = abort
```

thì:

```text
panic()
    ↓
trap/abort
```

Không cần unwind runtime.

Nếu:

```text
panic = unwind
```

thì linker thêm:

```text
unwind metadata
unwind runtime
```

nếu target/profile cần.

---

# 14. Allocator

Không có allocator mặc định trong Core.

Tầng runtime/std có:

```text
Allocator
```

interface.

Ví dụ:

```text
trait Allocator {
    fn allocate(...)
    fn deallocate(...)
    fn grow(...)
}
```

Nhưng API user-facing không nên buộc:

```text
Vec<T, GlobalAllocator>
```

trừ khi thực sự cần.

Đây là điểm đã thống nhất trước đó:

> allocator choice không phải generic parameter mặc định của collection.

---

# 15. Allocator Selection

Một chương trình có thể chọn:

```text
SystemAllocator
Arena
Pool
Slab
CustomAllocator
NoAllocator
```

Ví dụ:

```text
Buffer
```

có thể sử dụng allocator hiện hành.

Compiler không cần biết allocator cụ thể để type-check phần lớn chương trình.

---

# 16. Resource Lifetime

Một điểm cực kỳ quan trọng:

```text
memory lifetime
resource lifetime
```

không đồng nhất.

Ví dụ:

```text
File
```

Drop có thể:

```text
close(fd)
```

nhưng memory của object:

```text
```

có thể vẫn tồn tại hoặc được compiler tối ưu hoàn toàn.

Do đó:

```text
Drop ≠ free()
```

đã được đóng băng.

---

# 17. OS Layer

Giữa Runtime và syscall nên có:

```text
os/
├── linux
├── windows
├── darwin
├── android
└── wasi
```

Ví dụ:

```text
std::fs
   ↓
os::linux::fs
   ↓
sys::linux
   ↓
syscall
```

Người dùng bình thường dùng:

```text
std::fs
```

System programmer có thể dùng:

```text
os::linux
```

và cực thấp:

```text
sys::linux
```

---

# 18. `sys`

`sys` là tầng gần OS ABI.

Ví dụ Linux:

```text
sys::linux::read
sys::linux::write
sys::linux::mmap
sys::linux::futex
sys::linux::epoll
```

Không đảm bảo portable.

Đây là nơi chấp nhận:

```text
platform-specific
ABI-specific
unsafe
```

---

# 19. `std::fs`

Ngược lại:

```text
std::fs::File
```

có semantic API portable.

Ví dụ:

```text
let file = File.open(path)?;
let n = file.read(buffer)?;
```

Không để source application phải biết:

```text
Linux fd
Windows HANDLE
Darwin fd
```

---

# 20. Runtime và `std` không được tạo ABI dependency ngầm

Ví dụ `Vec<T>` không được phép ngầm yêu cầu:

```text
libstd.so
```

nếu implementation của nó có thể được:

```text
monomorphized
inlined
linked statically
```

Thậm chí:

```text
Vec<i32>
```

có thể hoàn toàn biến mất abstraction sau optimization.

---

# 21. Compiler Runtime

Cần phân biệt thêm:

```text
compiler-builtins
```

với:

```text
runtime
```

Compiler-builtins là các operation compiler có thể cần.

Runtime là execution infrastructure.

Ví dụ:

```text
integer_divide
```

→ compiler builtin.

Trong khi:

```text
thread_spawn
```

→ runtime/OS abstraction.

---

# 22. `core` API phải cực nhỏ

Không nên biến Core thành:

```text
"mọi thứ mà compiler thích"
```

Core chỉ chứa thứ có **semantic hoặc machine-level necessity**.

Một quy tắc tốt:

> Nếu có thể đưa thứ đó hoàn toàn vào library mà không làm compiler mất khả năng đảm bảo semantics, hãy để nó ở library.

Ví dụ:

```text
Vec
HashMap
StringBuilder
TCP
HTTP
JSON
```

không thuộc Core.

---

# 23. Nhưng compiler-known types thì khác

Một số thứ có semantic significance:

```text
Option
Result
view
mut_view
Future
dyn Trait
```

có thể có compiler-aware representation/lowering.

Nhưng không nhất thiết phải hard-code implementation library.

Ví dụ:

```text
Option<T>
```

vẫn là enum:

```text
enum Option<T> {
    Some(T),
    None
}
```

Compiler chỉ hiểu:

```text
enum semantics
niche optimization
pattern matching
```

không cần có:

```text
special Option runtime
```

---

# 24. `Future`

Tương tự:

```text
Future<T>
```

không phải runtime object bắt buộc.

Compiler tạo state machine:

```text
FutureState
```

Runtime chỉ cung cấp:

```text
Executor
Waker
Scheduler
```

nếu chương trình thực sự dùng async.

---

# 25. Thread

Thread abstraction cũng không nên nằm trong Core semantic type system.

Core biết:

```text
Send
Share
ExecutionDomain
```

Runtime/std cung cấp:

```text
Thread
ThreadHandle
spawn
join
```

---

# 26. Atomics

Atomic semantics thuộc compiler + machine backend:

```text
Atomic<T>
Acquire
Release
SeqCst
```

nhưng API có thể nằm ở Core/low-level library.

Không cần:

```text
atomic runtime daemon
```

---

# 27. Synchronization

`Mutex`, `RwLock`, `Semaphore` nên là library/runtime.

Compiler chỉ cần hiểu semantic facts cần thiết:

```text
LOCK
UNLOCK
WAIT
NOTIFY
```

trong MIR khi lowering các primitive có compiler-aware semantics.

Implementation có thể dùng:

```text
futex
SRWLock
pthread mutex
spinlock
```

tùy target.

---

# 28. Unicode

Không nên đưa toàn bộ Unicode database vào Core.

Ví dụ:

```text
u8
view<u8>
```

không cần Unicode runtime.

`std::unicode` mới chứa:

```text
grapheme
normalization
case mapping
Unicode tables
```

Nếu chương trình không dùng Unicode processing:

```text
Unicode data
```

không được link.

---

# 29. Reflection

Đây cũng là một ví dụ quan trọng.

Compile-time:

```text
comptime
```

không cần runtime metadata.

Runtime reflection:

```text
@emit_reflection
```

mới tạo metadata.

Do đó:

```text
reflection = off
```

là mặc định.

---

# 30. Compiler itself

Đây là lý do boundary này phải được chốt trước self-hosting.

Compiler Axiom cần:

```text
core
collections
string
filesystem
process
hashing
parallelism
```

Nhưng **compiler không nên bắt buộc phải kéo toàn bộ std**.

Kiến trúc:

```text
Axiom Compiler
    ↓
Core
    ↓
minimal runtime
    ↓
OS API
```

và chỉ dùng những phần std thực sự cần.

---

# 31. Self-hosted compiler profile

Ta có thể định nghĩa:

```text
profile.compiler
```

Ví dụ:

```toml
[profile.compiler]
panic = "abort"
runtime = ["allocator", "thread", "filesystem"]
reflection = false
async = false
```

Compiler có thể dùng:

```text
thread pool
filesystem
hash maps
```

nhưng executable compiler không cần:

```text
network
GUI
async executor
Unicode full runtime
```

nếu không sử dụng.

---

# 32. Bootstrap Core

Core phải là một trong những thư viện Axiom đầu tiên có thể viết bằng chính Axiom.

Bootstrap:

```text
Stage 0 compiler
       ↓
compile
       ↓
axiom/core
```

Sau đó:

```text
Stage 1 compiler
       ↓
uses Axiom core
```

Và cuối cùng:

```text
Axiom compiler
       ↓
Axiom source
       ↓
Axiom core
```

---

# 33. Không có "magic standard library"

Đây là nguyên tắc tôi rất khuyến nghị:

> **Std không được trở thành một phần thứ hai của compiler.**

Compiler chỉ biết:

```text
language semantics
intrinsics
ABI
target
```

Không biết:

```text
HashMap implementation
HTTP implementation
File abstraction implementation
```

trừ những interface compiler-specific thật sự cần thiết.

---

# 34. Runtime Component Discovery

Linker/driver có thể nhận metadata:

```text
RuntimeManifest
```

Ví dụ:

```text
RuntimeManifest {
    requires_allocator: true
    requires_threads: false
    requires_tls: false
    requires_unwind: false
    requires_async: false
}
```

Driver tổng hợp:

```text
Program
+
Compiler facts
+
Std dependencies
```

→

```text
RuntimeManifest
```

Sau đó linker chỉ đưa component cần thiết vào.

---

# 35. Một ví dụ hoàn chỉnh

### Freestanding

```text
@entry
fn _start() -> never {
    sys::linux::exit(42)
}
```

Dependency:

```text
Core
 └── sys::linux

Runtime:
    none

Std:
    none
```

Binary:

```text
ELF
 ├── .text
 └── minimal metadata
```

---

### Program thông thường

```text
fn main() {
    println("Hello");
}
```

Dependency:

```text
Core
Std::io
Runtime::startup
Runtime::allocator?   ← chỉ nếu cần
OS
```

---

### Server

```text
async fn main() {
    ...
}
```

Dependency có thể:

```text
Core
Std::net
Std::async
Runtime::allocator
Runtime::async
Runtime::io
Runtime::thread
TLS
OS
```

Nhưng vẫn không có:

```text
GC
```

nếu program không dùng.

---

# 36. Repository boundary

Đề xuất cuối:

```text
axiom/
├── compiler/
│
├── core/
│   ├── option.ax
│   ├── result.ax
│   ├── slice.ax
│   ├── numeric.ax
│   ├── atomic.ax
│   ├── intrinsics.ax
│   └── memory.ax
│
├── runtime/
│   ├── allocator/
│   ├── panic/
│   ├── thread/
│   ├── tls/
│   ├── async/
│   ├── unwind/
│   └── startup/
│
├── std/
│   ├── collections/
│   ├── io/
│   ├── fs/
│   ├── net/
│   ├── process/
│   ├── time/
│   ├── sync/
│   ├── thread/
│   ├── async/
│   ├── unicode/
│   └── path/
│
├── os/
│   ├── linux/
│   ├── windows/
│   ├── darwin/
│   ├── android/
│   └── wasi/
│
└── sys/
    ├── linux/
    ├── windows/
    ├── darwin/
    └── wasi/
```

---

# 37. Các invariant cần đóng băng

### ASTD-20 — Core Is Freestanding-Capable

### ASTD-21 — Core Does Not Require An OS

### ASTD-22 — Core Does Not Require A Heap

### ASTD-23 — Core Does Not Require A Monolithic Runtime

### ASTD-24 — Runtime Components Are Optional

### ASTD-25 — Std Depends Downward

### ASTD-26 — Core Does Not Depend On Std

### ASTD-27 — Core Does Not Depend On Runtime

### ASTD-28 — Runtime Does Not Depend On Application Code

### ASTD-29 — Std Does Not Define Language Semantics

### ASTD-30 — Compiler Builtins Are Distinct From Runtime

### ASTD-31 — Compiler Builtins Need Not Allocate

### ASTD-32 — Allocator Is Optional

### ASTD-33 — Panic Runtime Is Optional

### ASTD-34 — Unwind Runtime Is Optional

### ASTD-35 — Thread Runtime Is Optional

### ASTD-36 — Async Runtime Is Optional

### ASTD-37 — TLS Runtime Is Optional

### ASTD-38 — Reflection Metadata Is Optional

### ASTD-39 — Unicode Database Is Optional

### ASTD-40 — Runtime Components Are Demand Driven

### ASTD-41 — Std Dependencies Are Explicit

### ASTD-42 — OS Dependencies Are Explicit

### ASTD-43 — Sys APIs Are Platform Specific

### ASTD-44 — Std APIs Prefer Platform Independence

### ASTD-45 — No Implicit CRT Requirement

### ASTD-46 — No Implicit libc Requirement

### ASTD-47 — Freestanding Programs May Use No Std

### ASTD-48 — Freestanding Programs May Use No Runtime

### ASTD-49 — Resource Lifetime Is Independent Of Memory Lifetime

### ASTD-50 — Drop Does Not Imply Deallocation

### ASTD-51 — Compiler-Known Types Need Not Have Runtime Support

### ASTD-52 — Future Does Not Require Async Runtime

### ASTD-53 — Atomic Semantics Do Not Require Runtime

### ASTD-54 — Ownership Semantics Do Not Require Runtime

### ASTD-55 — Capability Verification Does Not Require Runtime Metadata

### ASTD-56 — Runtime Selection Is Derived From Program Requirements

### ASTD-57 — Runtime Selection Is Link-Time Configurable

### ASTD-58 — Unused Runtime Components Are Not Linked

### ASTD-59 — Std Is Not A Hidden Compiler Dependency

### ASTD-60 — Compiler Can Be Built With A Minimal Std/Runtime Profile

---

# 38. Boundary cuối cùng

Như vậy Axiom có thể đạt cấu trúc rất sạch:

```text
                    AXIOM LANGUAGE
                         │
               ┌─────────┴─────────┐
               │                   │
              CORE                COMPTIME
               │
        ┌──────┴──────┐
        │             │
    compiler      low-level APIs
        │
        └──────────────┐
                       │
                  OPTIONAL
                   RUNTIME
                       │
                 ┌─────┴─────┐
                 │           │
                STD          OS
                 │           │
                 └─────┬─────┘
                       │
                      SYS
                       │
                      ABI
                       │
                    MACHINE
```

Điểm quan trọng nhất là **không có tầng nào bắt buộc phải kéo toàn bộ tầng bên dưới vào executable**.

---

## Bước tiếp theo

Sau khi chốt boundary này, tôi sẽ chuyển sang **BOOTSTRAP-001 — Stage-0 Axiom Compiler**.

Ở đó chúng ta sẽ không tiếp tục thiết kế thêm tính năng ngôn ngữ, mà thiết kế **compiler thực sự đầu tiên**:

```text
Stage-0
   ↓
Lexer
   ↓
Parser
   ↓
Resolver
   ↓
Type checker
   ↓
Ownership checker
   ↓
MIR
   ↓
x86-64 backend
   ↓
Axiom Object Writer
   ↓
Axiom Linker
   ↓
ELF executable
```

và đặc biệt xác định **subset Axiom tối thiểu nhưng không làm sai semantic model**, để compiler đầu tiên có thể được viết bằng C rồi nhanh chóng chuyển sang **compiler-in-Axiom**.