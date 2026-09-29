# BOOTSTRAP-111 — Runtime Composition, Startup & Platform System Layer

**Trạng thái: FROZEN / COMPLETED**

Đây là task khóa ranh giới giữa **Axiom language/compiler** và **máy đang chạy chương trình**.

Nguyên tắc quan trọng nhất:

> **Axiom không có một “runtime” duy nhất. Axiom có một tập các runtime/system components tùy nhu cầu chương trình.**

Vì vậy:

```text
Program
  ↓
Compiler determines required capabilities
  ↓
Runtime Component Graph
  ↓
Platform Layer
  ↓
OS / Firmware / Hardware
```

---

# 1. Runtime không phải một khối

Không có:

```text
axiom-runtime.dll
    ├── allocator
    ├── thread
    ├── async
    ├── filesystem
    ├── networking
    ├── reflection
    └── everything else
```

Thay vào đó:

```text
Program
 ├── allocator
 ├── panic
 ├── TLS
 ├── thread
 └── filesystem
```

chỉ link những component thực sự cần.

Một chương trình freestanding có thể:

```text
Program
 └── startup
```

hoặc gần như:

```text
Program
 └── entry
```

---

# 2. Runtime Component Model

Định nghĩa:

```text
RuntimeComponent
{
    id
    dependencies[]
    initialization
    finalization
    target_support
    ABI
    required_capabilities
}
```

Các component chuẩn:

```text
STARTUP
ALLOCATOR
PANIC
UNWIND
TLS
THREAD
SYNC
ASYNC
IO
UNICODE
LOCALE
REFLECTION
GPU
RANDOM
TIME
PROCESS
ENVIRONMENT
```

Không phải component nào cũng là runtime.

Ví dụ:

```text
Unicode algorithms
```

có thể hoàn toàn là library code.

Vì vậy compiler/linker phải phân biệt:

```text
Runtime Component
Library
System Facility
```

---

# 3. Component dependency graph

Ví dụ:

```text
async filesystem application
```

có thể tạo:

```text
APP
 │
 ├── IO
 │    └── SYSTEM
 │
 ├── ASYNC
 │    └── THREAD
 │
 ├── ALLOCATOR
 │
 └── PANIC
```

Trong khi:

```text
freestanding DSP
```

chỉ:

```text
DSP
 │
 └── STARTUP
```

Compiler/linker phải tính closure:

```text
required components
       ↓
dependency closure
       ↓
link graph
```

---

# 4. Platform Profile

Axiom định nghĩa profile thay vì bắt programmer cấu hình hàng trăm flag.

## Hosted

```text
@profile(hosted)
```

Có OS process model.

Có thể sử dụng:

```text
filesystem
network
threads
environment
clock
dynamic loading
```

---

## Freestanding

```text
@profile(freestanding)
```

Không giả định:

```text
OS
libc
filesystem
process
heap
threads
```

Program phải tự chọn những gì cần.

---

## Kernel

```text
@profile(kernel)
```

Có:

```text
interrupt
privileged execution
physical/device memory
scheduler
drivers
```

nhưng không có user-space assumptions.

---

## Embedded

```text
@profile(embedded)
```

Ưu tiên:

```text
no OS
small binary
static memory
deterministic startup
hardware peripherals
```

---

## Device/GPU

```text
@profile(device)
@profile(gpu)
```

Execution domain được xác định rõ.

---

# 5. Startup ABI

Program không thực sự bắt đầu từ `main()`.

Trên native platform:

```text
OS loader
   ↓
platform entry
   ↓
Axiom startup
   ↓
runtime initialization
   ↓
main()
   ↓
exit
```

Do đó:

```text
main()
```

là **application-level entry**, không phải machine-level entry.

---

# 6. Startup layer

Startup component chịu trách nhiệm:

```text
Startup
├── establish execution environment
├── initialize required runtime components
├── construct main arguments
├── invoke main
├── translate result to process exit
└── perform required shutdown
```

Không được tự động làm:

```text
initialize every runtime component
```

---

# 7. `main`

Axiom có thể hỗ trợ:

```text
fn main()
```

và:

```text
fn main() -> Result<(), Error>
```

và platform-specific forms sau này.

Compiler/startup adapter chuyển chúng thành platform entry ABI.

Ví dụ:

```text
main() -> i32
```

→ process exit code.

---

# 8. Exit semantics

Phân biệt:

```text
return from main
process exit
abort
panic
trap
```

Ví dụ:

```text
return 0
```

không giống:

```text
abort()
```

và không giống:

```text
panic()
```

`main()` return:

```text
main result
    ↓
startup adapter
    ↓
process exit
```

---

# 9. Panic bootstrap

Panic model đã được khóa ở error architecture.

Runtime chỉ cung cấp policy:

```text
panic=abort
panic=unwind
panic=custom
```

Ví dụ minimal:

```text
panic=abort
```

có thể chỉ cần:

```text
panic(message)
    ↓
write diagnostic
    ↓
terminate
```

Không cần unwind engine.

---

# 10. Unwind là optional

Nếu binary không dùng:

```text
panic=unwind
```

thì linker có thể loại:

```text
unwind tables
unwind runtime
exception personality
```

Đây là một ví dụ trực tiếp của:

> **Semantic feature ≠ mandatory runtime cost.**

---

# 11. Allocator bootstrap

Không có allocator mặc định bắt buộc.

Các lựa chọn:

```text
NO_ALLOCATOR
SYSTEM_ALLOCATOR
AXIOM_ALLOCATOR
CUSTOM_ALLOCATOR
ARENA
POOL
STATIC_ONLY
```

Nếu chương trình chỉ dùng:

```text
stack
static
register
```

thì:

```text
allocator component = absent
```

---

# 12. Allocation API boundary

Runtime allocator không được trở thành semantic primitive.

Ví dụ:

```text
Box<T>
```

là library abstraction.

Nó có thể sử dụng:

```text
allocator.allocate()
```

nhưng compiler vẫn có quyền:

```text
Box<T>
    ↓
stack allocation
```

nếu storage identity không observable.

---

# 13. TLS

TLS component chỉ xuất hiện nếu chương trình sử dụng TLS.

```text
@tls
var state: State
```

Startup phải phối hợp với:

```text
platform TLS ABI
```

Thread creation phải tạo TLS state phù hợp.

Thread termination phải cleanup TLS resources nếu ABI/platform yêu cầu.

---

# 14. Thread startup

Khi:

```text
spawn(worker)
```

runtime thread component tạo:

```text
OS thread
   ↓
Axiom thread entry
   ↓
construct task state
   ↓
worker()
   ↓
cleanup
   ↓
thread exit
```

Không có:

```text
global thread registry
```

trừ khi thread runtime thực sự cần.

---

# 15. Thread runtime ≠ concurrency semantics

Điều này rất quan trọng.

Compiler đã định nghĩa:

```text
Send
Share
Atomic
Mutex
Channel
Memory ordering
```

Runtime chỉ hiện thực chúng.

Ví dụ:

```text
Mutex<T>
```

semantic contract thuộc Axiom/library.

Linux implementation có thể dùng:

```text
futex
```

Windows:

```text
WaitOnAddress
SRWLOCK
```

nhưng semantics vẫn giống nhau.

---

# 16. Async runtime

`async fn` bản thân **không tạo runtime**.

```text
async fn foo()
```

chỉ tạo:

```text
Future
```

Runtime executor chỉ xuất hiện khi chương trình yêu cầu:

```text
spawn(...)
block_on(...)
run_executor(...)
```

Do đó:

```text
async fn
```

không tự động kéo:

```text
Tokio-like runtime
```

vào binary.

---

# 17. Async executor component

Executor có thể gồm:

```text
Executor
├── scheduler
├── task queue
├── waker
├── timer
└── IO integration
```

Nhưng từng phần có thể độc lập.

Ví dụ:

```text
single-thread executor
```

không cần:

```text
thread pool
```

---

# 18. IO system layer

Axiom library:

```text
File
Socket
Process
Pipe
```

không trực tiếp phụ thuộc vào Linux/Windows syscall trong semantic layer.

Architecture:

```text
Axiom API
    ↓
Platform IO interface
    ↓
Linux implementation
Windows implementation
macOS implementation
...
    ↓
OS
```

---

# 19. System Layer

Định nghĩa một boundary:

```text
SystemLayer
```

với các capability:

```text
Memory
Process
Thread
File
Socket
Clock
Random
TLS
VirtualMemory
Device
Signal
```

Mỗi platform implement một backend.

---

# 20. Không ép POSIX

Axiom không nên lấy POSIX làm Core abstraction.

Ví dụ Windows không phải:

```text
Windows
  ↓
fake POSIX
```

mà:

```text
Axiom System API
 ├── Linux backend
 ├── Windows backend
 ├── macOS backend
 ├── Android backend
 └── iOS backend
```

Như vậy có thể khai thác native API tốt hơn.

---

# 21. Syscall

Syscall là system-layer operation:

```text
unsafe/system
```

Ví dụ conceptual:

```text
linux::syscall(...)
```

không thuộc safe Core.

Compiler có thể cung cấp:

```text
@syscall
```

cho declaration system-level.

---

# 22. libc

Axiom không phụ thuộc libc.

Nhưng có thể dùng:

```text
extern "C"
```

để gọi:

```text
malloc
printf
pthread_*
```

nếu chương trình yêu cầu.

Như vậy:

```text
Axiom
```

không đồng nghĩa:

```text
libc
```

---

# 23. CRT

Tương tự:

```text
MSVC CRT
glibc startup
musl
libSystem
```

đều là platform integrations.

Axiom có thể:

```text
use CRT
```

hoặc:

```text
no CRT
```

tùy binary.

---

# 24. Global initialization

Axiom **không có hidden global constructor model**.

Không tự động:

```text
static Foo x = Foo::new()
```

rồi sinh:

```text
global constructor registry
```

thay vào đó:

```text
const
static immutable
explicit init
lazy initialization
```

được dùng rõ ràng.

Điều này giúp:

- startup deterministic;
- binary nhỏ;
- tránh initialization-order fiasco;
- freestanding dễ hơn.

---

# 25. Static initialization

Compile-time constructible value:

```text
static TABLE: [u8; 256] = generate_table();
```

nếu `generate_table()` là comptime:

```text
comptime
    ↓
raw initialized data
```

không cần runtime initialization.

Đây là điểm rất mạnh của hệ comptime Axiom đã thiết kế.

---

# 26. Lazy initialization

Runtime lazy initialization là library abstraction:

```text
Lazy<T>
Once<T>
OnceCell<T>
```

không phải compiler runtime primitive.

---

# 27. Process environment

Hosted profile có:

```text
args()
env()
current_dir()
exit()
```

Nhưng chúng chỉ link system component tương ứng.

Freestanding:

```text
args() 
```

không tồn tại nếu platform không cung cấp process model.

---

# 28. Signals / faults

Phân biệt:

```text
panic
process signal
hardware fault
OS exception
```

Compiler không biến tất cả thành `Result`.

Ví dụ:

```text
divide by zero
page fault
illegal instruction
```

là platform/hardware behavior.

Nếu cần recover:

```text
system-level signal/exception handler
```

là explicit unsafe/system functionality.

---

# 29. Device/GPU runtime

GPU:

```text
@kernel
```

không tự động kéo toàn bộ GPU runtime.

Chương trình chỉ cần:

```text
GPU API
DeviceBuffer
GpuEvent
```

thì link:

```text
GPU runtime
```

cần thiết.

Driver vẫn là external platform facility.

---

# 30. Runtime composition algorithm

Compiler/linker thực hiện:

```text
1. Analyze program requirements
2. Collect explicitly requested runtime capabilities
3. Infer compiler-required components
4. Resolve component dependencies
5. Remove unused components
6. Select platform implementation
7. Generate startup
8. Link
```

Ví dụ:

```text
program
  ↓
uses Box
  ↓
ALLOCATOR

uses thread::spawn
  ↓
THREAD
  ↓
TLS

uses panic=abort
  ↓
PANIC_ABORT
```

Kết quả:

```text
STARTUP
ALLOCATOR
THREAD
TLS
PANIC_ABORT
```

Không có:

```text
ASYNC
IO
REFLECTION
UNICODE_RUNTIME
```

nếu không dùng.

---

# 31. Runtime manifests

Mỗi component có metadata:

```text
RuntimeManifest {
    component
    target
    dependencies
    init
    fini
    symbols
    ABI
    capabilities
}
```

Compiler/linker dùng metadata này để xây dependency graph.

---

# 32. Runtime versioning

Runtime component ABI phải có:

```text
ComponentId
ComponentVersion
SemanticABI
TargetABI
```

Nhưng chương trình static native có thể **embed component code trực tiếp**.

Không bắt buộc:

```text
AxiomRuntime.so
```

phải có mặt trên máy người dùng.

---

# 33. Static vs dynamic runtime

Có thể:

```text
static runtime
```

hoặc:

```text
shared runtime
```

nhưng static là lựa chọn quan trọng cho:

- embedded;
- portable binaries;
- deployment đơn giản;
- reproducibility.

Dynamic runtime chỉ dùng khi có lý do.

---

# 34. Minimal binary

Mục tiêu hợp lý:

```text
fn main() {
}
```

có thể compile thành:

```text
entry
return
```

với:

```text
STARTUP
```

ở mức tối thiểu.

Không nên mặc định kéo:

```text
allocator
thread
async
unicode
reflection
filesystem
network
```

---

# 35. Platform capability matrix

Axiom cần capability matrix:

| Capability | Hosted | Freestanding | Kernel | Embedded | GPU |
|---|---:|---:|---:|---:|---:|
| Stack | ✓ | ✓ | ✓ | ✓ | ✓ |
| Heap | optional | optional | optional | optional | device-specific |
| Process | ✓ | — | custom | — | — |
| Thread | ✓ | optional | custom | optional | GPU execution |
| TLS | ✓ | optional | custom | optional | device-specific |
| File | ✓ | platform | — | custom | — |
| Socket | ✓ | platform | custom | custom | — |
| Async | ✓ | optional | custom | optional | event model |
| GPU | optional | optional | optional | optional | ✓ |
| Reflection | optional | optional | optional | optional | restricted |

---

# 36. Compiler-generated runtime code

Compiler có thể generate:

```text
startup adapter
drop glue
panic adapter
async state machine
TLS adapter
GPU launch stub
FFI thunk
```

Nhưng chúng vẫn phải được biểu diễn như **ordinary generated artifacts**.

Không có “magic runtime” ngoài compiler graph.

---

# 37. Runtime code phải chịu verification

Generated startup/runtime adapters phải đi qua:

```text
HIR/MIR
 ↓
verification
 ↓
optimization
 ↓
ABI lowering
```

hoặc đối với target-specific startup code:

```text
trusted platform implementation
```

phải có contract rõ ràng.

Không được tạo một đường bypass compiler safety mà không có boundary.

---

# 38. Runtime boundary và unsafe

Platform layer có thể dùng:

```text
unsafe
```

rất nhiều.

Ví dụ:

```text
raw syscall
raw TLS access
OS handle
memory mapping
interrupt
MMIO
```

Nhưng unsafe chỉ nằm ở:

```text
System Layer
```

Safe library phía trên chuyển nó thành abstraction có contract.

Đây là nguyên tắc:

> **Unsafe should be concentrated, not eliminated.**

---

# 39. FFI integration

Runtime component có thể phụ thuộc external library:

```text
OpenSSL
CUDA
system libc
GPU driver
OS framework
```

nhưng dependency đó phải xuất hiện rõ trong artifact metadata.

Không có:

```text
compiler secretly links random library
```

---

# 40. Startup failure

Nếu runtime initialization thất bại:

```text
allocator init failed
TLS init failed
GPU initialization failed
```

không được biến thành một semantic exception bất ngờ.

Startup policy phải rõ:

```text
return error
panic
abort
platform failure
```

tùy component/profile.

---

# 41. Runtime component invariants

### `ARUNTIME-20`
Axiom has no mandatory monolithic runtime.

### `ARUNTIME-21`
Runtime components are independently linkable.

### `ARUNTIME-22`
Unused runtime components must not be linked solely because the language supports their features.

### `ARUNTIME-23`
Startup is distinct from application `main`.

### `ARUNTIME-24`
`main` is adapted to platform entry ABI by startup code.

### `ARUNTIME-25`
Freestanding programs do not implicitly require an operating system.

### `ARUNTIME-26`
Axiom does not require libc.

### `ARUNTIME-27`
Axiom does not require a C runtime.

### `ARUNTIME-28`
Allocator availability is independent from the language core.

### `ARUNTIME-29`
Async language support does not imply an executor.

### `ARUNTIME-30`
`async` does not imply threads.

### `ARUNTIME-31`
Thread support does not imply async support.

### `ARUNTIME-32`
TLS is an explicit runtime/platform facility.

### `ARUNTIME-33`
Global initialization is not implicitly registered through a hidden constructor system.

### `ARUNTIME-34`
Comptime initialization may eliminate runtime initialization.

### `ARUNTIME-35`
Runtime component dependency resolution is deterministic.

### `ARUNTIME-36`
Platform APIs are isolated behind the system layer.

### `ARUNTIME-37`
Axiom does not require POSIX as its fundamental system abstraction.

### `ARUNTIME-38`
OS-specific implementations may use native platform APIs.

### `ARUNTIME-39`
System calls are system-layer operations.

### `ARUNTIME-40`
Runtime-generated code cannot bypass semantic verification without an explicit trusted boundary.

### `ARUNTIME-41`
Runtime components have explicit ABI contracts.

### `ARUNTIME-42`
Static runtime composition is supported.

### `ARUNTIME-43`
Dynamic runtime composition is optional.

### `ARUNTIME-44`
Runtime components may be eliminated by dead-code/dead-section elimination.

### `ARUNTIME-45`
Platform faults are not implicitly converted into language-level `Result`.

### `ARUNTIME-46`
Panic policy determines required panic/unwind machinery.

### `ARUNTIME-47`
A freestanding program may contain no allocator.

### `ARUNTIME-48`
Axiom runtime components must not introduce hidden global state unless explicitly part of their contract.

### `ARUNTIME-49`
Runtime dependencies must be represented in the build/link graph.

### `ARUNTIME-50`
Axiom source semantics do not depend on a specific operating system.

### `ARUNTIME-51`
System-layer implementations may be platform-specific.

### `ARUNTIME-52`
GPU runtime is optional for CPU-only programs.

### `ARUNTIME-53`
Axiom can express programs with no general-purpose runtime.

### `ARUNTIME-54`
Startup, runtime, library, and system-layer responsibilities remain architecturally distinct.

### `ARUNTIME-55`
Runtime composition must not alter language semantics.

### `ARUNTIME-56`
Runtime selection is a build/link decision constrained by semantic requirements.

### `ARUNTIME-57`
Axiom can produce a minimal native executable without an implicit language-wide runtime dependency.

---

# 42. Kết quả BOOTSTRAP-111

Axiom bây giờ đã có đầy đủ:

```text
Language semantics
       ↓
Compiler
       ↓
Machine backend
       ↓
Object writer
       ↓
Linker
       ↓
Runtime composition
       ↓
Platform layer
       ↓
OS / firmware / hardware
```

Và đặc biệt đã giải quyết một mục tiêu quan trọng của Axiom:

```text
High-level language
       +
Safety
       +
Async
       +
Threads
       +
GPU
       +
Reflection
       +
Comptime
       ↓
KHÔNG đồng nghĩa
       ↓
Huge mandatory runtime
```

---

# BOOTSTRAP-112 — Bootstrap Compiler & Compiler Self-Construction

Đây là task tiếp theo và **rất quan trọng**.

Axiom hiện đã có kiến trúc language → executable, nhưng còn một câu hỏi lớn:

> **Compiler Axiom đầu tiên được xây bằng gì, và làm thế nào chuyển từ compiler bootstrap bên ngoài sang compiler tự biên dịch bằng chính Axiom?**

Mục tiêu:

```text
Stage 0
External implementation
    ↓
Stage 1
Axiom compiler using external backend
    ↓
Stage 2
Axiom compiler using own MIR/LIR
    ↓
Stage 3
Axiom compiler compiled by Axiom
    ↓
Stage 4
Self-hosted Axiom compiler
```

Task 112 sẽ khóa:

- bootstrap compiler architecture;
- compiler implementation language;
- Stage 0/1/2/3;
- tránh chicken-and-egg;
- temporary LLVM/Clang/LLD usage;
- transition sang own backend;
- compiler binary reproducibility;
- compiler self-build;
- compiler can compile itself;
- cross-compilation;
- compiler bootstrap seed;
- trusted seed;
- compiler correctness boundary;
- stage-by-stage artifact verification;
- self-hosted `axc`;
- eventual elimination của LLVM/Clang/GCC/LLD;
- **Axiom Compiler Self-Hosting Chain**.

Sau task này, Axiom sẽ không chỉ có **ngôn ngữ + compiler architecture + linker + runtime**, mà bắt đầu có con đường thực tế để **tự xây chính compiler của mình bằng Axiom**.