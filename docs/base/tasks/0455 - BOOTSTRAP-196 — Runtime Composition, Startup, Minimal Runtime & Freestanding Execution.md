# BOOTSTRAP-196 — Runtime Composition, Startup, Minimal Runtime & Freestanding Execution

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là phần hoàn thiện nguyên tắc:

> **Axiom không có “một runtime”; Axiom có một tập các runtime capability có thể được compose khi cần.**

---

## 196.1. Runtime không phải một khối duy nhất

Binary Axiom có thể gồm:

```text
Program
│
├── Startup
├── Allocator
├── Panic
├── Unwind
├── TLS
├── Thread
├── Async
├── Reflection
├── Unicode
├── IO
└── Platform
```

Nhưng mỗi thành phần là một dependency độc lập.

Ví dụ chương trình:

```axiom
fn main() {
    let x = 1 + 2;
}
```

không được tự động kéo theo:

```text
allocator
threads
async executor
reflection
filesystem
network
unicode tables
```

---

# 196.2. Runtime Capability Graph

Compiler/build system tạo:

```text
RuntimeGraph
```

Ví dụ:

```text
Program
 ├── Panic
 └── Startup
```

hoặc:

```text
Program
 ├── Startup
 ├── Allocator
 ├── Thread
 │    └── TLS
 └── IO
      └── Platform
```

Async:

```text
Program
 ├── Startup
 ├── AsyncExecutor
 │    ├── Thread
 │    └── Timer
 └── IO
```

Reflection:

```text
Program
 └── ReflectionRuntime
      └── Metadata
```

---

# 196.3. Runtime dependency graph không phải package graph

Phân biệt:

```text
PackageGraph
RuntimeGraph
LinkGraph
```

Ví dụ package:

```text
std
```

có thể chứa filesystem, network, process...

nhưng chương trình chỉ dùng:

```text
std::math
```

thì linker không được link toàn bộ `std`.

---

# 196.4. Startup là một capability

`Startup` chịu trách nhiệm:

```text
OS/loader
    ↓
initial machine state
    ↓
Axiom startup
    ↓
program entry
```

Không phải runtime monolith.

---

# 196.5. `main` không phải entry point vật lý

Source:

```axiom
fn main() {
    ...
}
```

không nhất thiết tương ứng trực tiếp với ELF/PE/Mach-O entry point.

Compiler tạo:

```text
OS entry
    ↓
Axiom startup
    ↓
main
```

Startup có thể thực hiện:

- stack setup nếu target yêu cầu
- TLS setup
- runtime component initialization
- argument/environment construction
- panic setup
- allocator setup
- gọi `main`
- process exit

Chỉ những bước cần thiết mới được link.

---

# 196.6. Startup profiles

Có ba profile chính:

### Hosted

```text
OS
 ↓
CRT/platform startup
 ↓
Axiom startup
 ↓
main
```

### Minimal

```text
OS
 ↓
Axiom startup
 ↓
main
```

### Freestanding

```text
firmware/kernel/bootloader
 ↓
Axiom entry
```

Không có giả định về process/OS.

---

# 196.7. `main` ABI

Axiom semantic:

```axiom
fn main()
```

hoặc:

```axiom
fn main() -> i32
```

Compiler quyết định mapping sang target.

Ví dụ:

```text
main() -> unit
        ↓
exit code 0
```

```text
main() -> i32
        ↓
OS process exit code
```

Có thể mở rộng:

```text
main() -> Result<(), E>
```

thông qua startup adapter, nhưng đây là library/profile policy chứ không phải Core requirement.

---

# 196.8. Startup và panic

Nếu chương trình có:

```axiom
panic(...)
```

compiler/linker chỉ link panic implementation nếu reachable.

Profile:

```text
panic = abort
```

có thể cực nhỏ:

```text
panic
 ↓
platform_abort
```

Profile unwind mới cần:

```text
unwind
personality
cleanup
unwind tables
```

---

# 196.9. Allocator bootstrap

Allocator không phải Core runtime bắt buộc.

Nếu chương trình không có dynamic allocation:

```text
Allocator = absent
```

Nếu dùng `Box`/`Vec`:

```text
Allocator
```

được đưa vào RuntimeGraph.

Allocator API semantic:

```text
allocate
deallocate
reallocate
```

nhưng implementation có thể là:

```text
system
arena
pool
slab
custom
embedded
GPU/device
```

---

# 196.10. Không có allocator global bắt buộc

Axiom không yêu cầu:

```text
global heap
```

cho mọi chương trình.

Một embedded application có thể:

```text
static memory
arena
stack
custom allocator
```

mà không có general-purpose heap.

---

# 196.11. Allocator initialization

Nếu allocator cần initialization:

```text
Startup
 ↓
AllocatorInit
 ↓
Program
```

Dependency graph đảm bảo ordering.

Không dùng global constructor magic.

---

# 196.12. TLS initialization

Nếu program sử dụng TLS:

```text
TLS
```

trở thành runtime capability.

Compiler/linker tạo target-specific TLS structures.

Không có TLS usage:

```text
TLS runtime component
```

được loại bỏ.

---

# 196.13. Thread runtime

Core semantics biết:

```text
Thread
Send
Share
Atomic
Mutex
```

nhưng OS thread implementation nằm ở:

```text
Runtime.Thread
```

Program không dùng thread:

```text
Thread runtime absent
```

---

# 196.14. Thread startup

Khi spawn:

```axiom
spawn(fn() { ... })
```

runtime tạo execution context.

Compiler chịu:

```text
Send verification
capture verification
ownership transfer
```

Runtime chịu:

```text
OS thread
stack
scheduler
join
```

Hai trách nhiệm không trộn.

---

# 196.15. Async runtime

`async fn` bản thân **không kéo executor vào binary**.

```axiom
async fn fetch() -> Result<Data, Error>
```

chỉ tạo Future.

Chỉ khi:

```axiom
executor.run(...)
```

hoặc:

```axiom
spawn(...)
```

được sử dụng thì Async runtime mới trở thành dependency.

---

# 196.16. Async runtime không phải Core

Core chỉ cần:

```text
Future
Poll
await
state machine
Waker contract
```

Runtime cung cấp:

```text
Executor
Timer
IO reactor
Worker pool
Task queue
```

Có thể có nhiều executor khác nhau.

---

# 196.17. Reflection runtime

Compile-time reflection không cần runtime.

Chỉ khi chương trình yêu cầu:

```text
runtime type information
dynamic inspection
serialization metadata
plugin discovery
```

thì:

```text
ReflectionRuntime
```

mới được link.

---

# 196.18. Unicode runtime

UTF-8 semantics thuộc library/type system.

Nhưng các bảng lớn:

```text
Unicode properties
normalization
case mapping
grapheme tables
```

không nên tự động vào binary.

Chỉ link dữ liệu/code được sử dụng.

---

# 196.19. IO runtime

`File`, `Socket`, `Process` đã có resource semantics.

Implementation:

```text
std::io
std::os
```

có thể kéo platform layer.

Nhưng chương trình thuần compute:

```text
IO = absent
```

---

# 196.20. Runtime composition

Build graph:

```text
Program
 │
 ├── uses Vec
 │      └── Allocator
 │
 ├── uses File
 │      └── IO
 │           └── Platform
 │
 └── uses Thread
        └── Thread
             └── TLS
```

Compiler/linker có thể derive:

```text
RequiredRuntimeCapabilities
```

---

# 196.21. Runtime capability reachability

Một runtime component chỉ được giữ nếu:

```text
Program/API
    ↓
reachable operation
    ↓
runtime dependency
```

Không được giữ vì:

```text
"std imported"
```

---

# 196.22. Runtime initialization ordering

Mỗi component có:

```text
requires
provides
init
shutdown
```

Ví dụ:

```text
TLS
 ↓
Thread
 ↓
AsyncExecutor
```

Build system tạo DAG.

Nếu cycle:

```text
A → B → A
```

thì build error, không dùng runtime initialization order ngẫu nhiên.

---

# 196.23. Shutdown

Không có universal:

```text
atexit everything
```

Thay vào đó resource ownership vẫn là cơ chế chính.

Process exit có thể bỏ qua cleanup theo OS semantics nếu profile abort/exit.

Nếu application yêu cầu graceful shutdown:

```text
main
 ↓
explicit cleanup
 ↓
exit
```

---

# 196.24. Global destructors

Axiom không có implicit C++-style:

```text
global object destructor registry
```

Global resource phải có semantic lifetime rõ ràng.

Nếu thật sự cần:

```text
@process_shutdown
```

thì đây là explicit runtime feature.

---

# 196.25. Static initialization

Static data:

```axiom
static X: T = constant;
```

nếu compile-time materializable:

```text
.rodata/.data
```

không cần runtime initialization.

Nếu cần runtime computation:

```text
runtime init
```

được biểu diễn explicit trong RuntimeGraph.

---

# 196.26. Zero-runtime programs

Axiom phải hỗ trợ:

```text
@freestanding
@no_runtime
```

conceptually.

Ví dụ:

```axiom
@entry
fn start() -> never {
    ...
}
```

có thể tạo:

```text
code
+
platform-required metadata
```

mà không link Axiom runtime.

---

# 196.27. Kernel/embedded

Một target có thể:

```text
Runtime = none
Allocator = custom
Panic = custom
Startup = custom
```

Ví dụ:

```text
bootloader
kernel
firmware
microcontroller
```

---

# 196.28. Runtime replacement

Application có thể thay:

```text
default allocator
default executor
default panic handler
```

nếu contract cho phép.

Ví dụ:

```text
allocator = mimalloc-like custom
executor = custom
panic = abort
```

Nhưng những component này vẫn phải tuân thủ Axiom semantic contracts.

---

# 196.29. Runtime ABI

Runtime component có ABI:

```text
RuntimeComponentABI
```

Ví dụ:

```text
Allocator ABI
Thread ABI
Async ABI
Panic ABI
TLS ABI
```

Runtime implementation có thể được thay thế mà application semantics không đổi nếu ABI contract tương thích.

---

# 196.30. Runtime versioning

Runtime version:

```text
runtime semantic version
runtime ABI version
target
```

không đồng nhất với:

```text
compiler version
```

Một binary static có thể không cần runtime version tại deployment.

---

# 196.31. Static runtime

Mặc định release native application ưu tiên:

```text
static runtime composition
```

để có:

- deployment đơn giản
- dead stripping
- reproducibility
- ít dependency

Dynamic runtime vẫn được phép khi cần.

---

# 196.32. Dynamic runtime

Nếu dùng:

```text
libaxiom-runtime.so
```

thì nó phải là explicit ABI dependency.

Không có cơ chế:

```text
binary secretly requires arbitrary runtime version
```

---

# 196.33. Runtime-free standard library

`std` không đồng nghĩa runtime.

Ví dụ:

```text
std::array
std::math
std::option
std::result
```

có thể hoàn toàn compile-time/static library.

Runtime chỉ xuất hiện khi API thực sự yêu cầu.

---

# 196.34. Compiler intrinsics

Một số runtime-like functionality có thể được lower trực tiếp:

```text
memcpy
memset
atomic
sqrt
trap
CPU intrinsic
```

Compiler có thể:

```text
inline
emit instruction
call platform
```

tùy target.

Không bắt buộc tồn tại function runtime thật.

---

# 196.35. Runtime elimination

Nếu compiler chứng minh:

```text
allocator call
```

không cần thiết:

```text
allocation elimination
```

có thể loại bỏ cả Allocator dependency.

Tương tự:

```text
unused panic path
unused async path
unused reflection
```

có thể biến mất.

---

# 196.36. Runtime profile

Axiom có profile:

```text
hosted
minimal
freestanding
kernel
embedded
wasm
gpu
```

Nhưng profile chỉ là preset.

Người dùng vẫn có thể compose capability trực tiếp.

---

# 196.37. Runtime diagnostics

Compiler có thể trả lời:

```text
ax runtime-tree
```

Ví dụ:

```text
Startup
 ├── Panic: abort
 ├── Allocator: system
 ├── TLS
 └── IO
      └── Linux
```

Hoặc:

```text
Startup
```

cho chương trình freestanding.

---

# 196.38. Runtime size analysis

Tooling:

```text
ax size --runtime
```

có thể báo:

```text
Startup       1.2 KB
Allocator     4.8 KB
Panic         0.3 KB
TLS           0.8 KB
IO           12.4 KB
```

Đây là tooling fact, không phải language semantic.

---

# 196.39. Runtime security

Runtime component phải khai báo authority:

```text
Allocator
Thread
Network
Filesystem
Process
Reflection
```

Security model 190 có thể dùng RuntimeGraph để xác định capability thực sự được đưa vào binary.

---

# 196.40. Runtime và package manager

Runtime component có thể nằm trong:

```text
std
runtime package
platform package
```

nhưng:

```text
package dependency
≠
runtime dependency
```

Linker chỉ lấy component thực sự cần.

---

# 196.41. Runtime và FFI

FFI không được tự động kéo toàn bộ runtime.

Ví dụ một C function:

```text
extern "C" fn memcpy(...)
```

có thể lower thành intrinsic trực tiếp.

Nếu foreign library cần thread/runtime:

```text
contract
```

phải thể hiện dependency.

---

# 196.42. Runtime và async FFI

Foreign async library có thể cung cấp:

```text
poll
callback
event handle
```

Axiom adapter chọn runtime integration tương ứng.

Không mặc định kéo Axiom executor vào.

---

# 196.43. Runtime và GPU

GPU runtime cũng optional.

Chương trình CPU-only:

```text
GPU runtime = absent
```

Chương trình GPU:

```text
Host GPU runtime
Device runtime
```

chỉ link khi cần.

---

# 196.44. Runtime composition algorithm

Conceptually:

```text
1. Compute reachable program effects.
2. Compute required runtime capabilities.
3. Build RuntimeGraph.
4. Resolve component dependencies.
5. Remove unreachable components.
6. Generate startup.
7. Link components.
8. Validate final runtime contract.
```

---

# 196.45. Không có hidden runtime dependency

Một function không được âm thầm biến:

```text
pure function
```

thành dependency:

```text
allocator
thread
IO
```

chỉ vì compiler implementation thuận tiện.

Nếu runtime dependency tồn tại và observable, nó phải được phản ánh trong semantic/effect/build model.

---

# 196.46. Runtime correctness

Runtime component phải được test như native library:

```text
unit
integration
ABI
stress
concurrency
target
bootstrap
```

Runtime bug không được coi là “ngoài compiler”.

---

# 196.47. Invariants — BOOTSTRAP-196

### `ART-20`
Axiom shall not require a monolithic runtime.

### `ART-21`
Runtime functionality shall be represented as composable capabilities/components.

### `ART-22`
Runtime dependencies shall be derived from reachable program requirements.

### `ART-23`
Unused runtime components shall be removable.

### `ART-24`
Runtime composition shall be distinct from package dependency resolution.

### `ART-25`
Host and target runtime environments shall remain distinct.

### `ART-26`
Startup shall be an explicit runtime/platform component.

### `ART-27`
`main` shall not be required to equal the physical OS entry point.

### `ART-28`
Allocator support shall be optional.

### `ART-29`
TLS support shall be optional.

### `ART-30`
Thread support shall be optional.

### `ART-31`
Async executor support shall be optional.

### `ART-32`
Reflection runtime support shall be optional.

### `ART-33`
Unicode data/code not required by a program shall be removable.

### `ART-34`
Freestanding programs shall be able to execute without the hosted Axiom runtime.

### `ART-35`
Runtime component initialization order shall be dependency-derived and deterministic.

### `ART-36`
Runtime initialization cycles shall be rejected.

### `ART-37`
Global constructor/destructor registries shall not be mandatory.

### `ART-38`
Static compile-time-initializable data shall not require runtime initialization.

### `ART-39`
Runtime replacement shall require compatibility with the relevant semantic/ABI contract.

### `ART-40`
Runtime components shall expose explicit ABI/version contracts when separately deployed.

### `ART-41`
Runtime capability composition shall participate in final binary reachability.

### `ART-42`
Compiler intrinsics may replace runtime calls when semantic contracts permit.

### `ART-43`
Runtime-free compilation shall not weaken Core language safety guarantees.

### `ART-44`
Runtime capability presence shall be inspectable by compiler tooling.

### `ART-45`
Runtime authority shall remain compatible with the Axiom security/capability model.

### `ART-46`
Async syntax shall not implicitly require an executor.

### `ART-47`
Thread-safe language semantics shall not require a thread runtime when no threads are used.

### `ART-48`
Axiom runtime composition shall support hosted, minimal, freestanding, kernel, embedded and specialized targets.

### `ART-49`
Static runtime composition shall not require dynamic runtime deployment.

### `ART-50`
Dynamic runtime dependencies shall be explicit and ABI-versioned.

---

# Kết luận BOOTSTRAP-196

Đến đây mô hình runtime của Axiom khá rõ:

```text
                 Axiom Program
                      │
              Reachability Analysis
                      │
                      ▼
               RuntimeGraph
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
   Startup        Allocator       Thread
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                 Native Image
```

Một chương trình nhỏ có thể chỉ là:

```text
Startup → main
```

Trong khi server:

```text
Startup
 ├── Allocator
 ├── TLS
 ├── Thread
 ├── Async
 ├── IO
 └── Network
```

Đây là cách Axiom vừa có **zero-cost/runtime-minimal philosophy**, vừa không biến việc lập trình ứng dụng thành quá thấp cấp.

---

# BOOTSTRAP-197 — Standard Library Architecture, `std` Layering & Zero-Cost Platform Abstractions

**TRẠNG THÁI: NEXT**

Sau 196, cần khóa một vấn đề cuối cùng ở tầng hệ sinh thái lõi:

> **Nếu Axiom không có monolithic runtime, thì Standard Library phải được tổ chức thế nào để vừa rất phong phú vừa không kéo hàng đống code vào binary?**

Mục tiêu không phải tạo một `std` khổng lồ.

Kiến trúc dự kiến:

```text
Axiom Core
   │
   ├── core
   │    ├── Option
   │    ├── Result
   │    ├── String primitives
   │    ├── Iterator
   │    ├── traits
   │    └── numeric primitives
   │
   ├── alloc
   │    ├── Box
   │    ├── Vec
   │    ├── Arc
   │    └── collections
   │
   ├── io
   │    ├── File
   │    ├── Stream
   │    └── Buffer
   │
   ├── sync
   │    ├── Mutex
   │    ├── Channel
   │    └── Atomic
   │
   ├── async
   │    ├── Future
   │    ├── Executor
   │    └── IO
   │
   ├── os
   │    ├── Windows
   │    ├── Linux
   │    ├── macOS
   │    └── Android/iOS
   │
   ├── gpu
   │
   ├── net
   │
   ├── process
   │
   └── reflection
```

Nhưng cần giải quyết sâu hơn:

- `core` có thực sự không được phụ thuộc allocator/runtime?
- `alloc` có phải một package riêng?
- `std` có phải facade hay package?
- platform API nằm ở đâu?
- POSIX abstraction có nên là một lớp riêng?
- filesystem/network có nên dùng trait abstraction?
- generic abstraction có gây code bloat không?
- khi nào compiler specialization được phép?
- `no_std`/freestanding nên thể hiện thế nào trong Axiom?
- standard library có phải một phần của language specification hay versioned external package?
- compiler intrinsic và std function phân chia thế nào?
- AI/IDE cần metadata gì từ std?
- làm sao để một `Vec` đơn giản không kéo toàn bộ collection ecosystem vào executable?

**BOOTSTRAP-197 sẽ chốt kiến trúc Standard Library và boundary giữa Core Language ↔ Core Library ↔ Allocation ↔ OS ↔ Runtime ↔ Platform, đồng thời giải quyết code-size và generic code-bloat.**