# BOOTSTRAP-306 — AXIOM RUNTIME COMPONENT SYSTEM & HOSTED/FREESTANDING RUNTIME BUILDER

## 1. Mục tiêu

Thiết kế **hệ thống Runtime Component** của Axiom sao cho:

- chương trình đơn giản có thể **không cần runtime**;
- chương trình hosted có thể dùng runtime đầy đủ;
- từng thành phần runtime được **link theo nhu cầu**, không kéo theo monolithic runtime;
- runtime không làm thay đổi semantic của Core Language;
- allocator, thread, async, panic, TLS, I/O... là các capability/component độc lập;
- compiler và linker có thể biết chính xác chương trình cần component nào;
- hỗ trợ:
  - freestanding/kernel/embedded;
  - native desktop/server;
  - multithread;
  - async;
  - GPU;
  - FFI;
  - WASM;
- tiến tới runtime được viết hoàn toàn bằng Axiom.

---

# 2. Nguyên tắc kiến trúc

### R-1 — Runtime không thuộc Core Language

Core Axiom phải có thể compile:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

thành executable mà **không cần Axiom runtime**.

Runtime chỉ xuất hiện khi semantic/library/API yêu cầu.

---

### R-2 — Capability-driven runtime

Không có:

```text
libaxiom-runtime.so
```

theo kiểu mọi chương trình đều phải link.

Thay vào đó:

```text
Program
  ├── Allocator
  ├── Panic
  ├── Thread
  ├── TLS
  ├── Async
  ├── IO
  └── Unicode
```

Chỉ component thực sự được sử dụng mới được đưa vào image.

---

### R-3 — Runtime component có dependency graph

Ví dụ:

```text
Async
 ├── Scheduler
 ├── Waker
 ├── Timer
 └── Thread
      └── TLS
```

nhưng:

```text
Allocator
```

không tự động kéo:

```text
Thread
Async
IO
```

---

# 3. Runtime Profile

Axiom định nghĩa các profile chuẩn:

```text
Freestanding
Hosted
Server
Async
GPU
Embedded
WASM
Kernel
```

Profile chỉ là **preset capability configuration**, không phải một semantic mode khác của ngôn ngữ.

Ví dụ:

```text
freestanding:
    allocator = none
    threads   = none
    async     = none
    io        = none
    panic     = abort

hosted:
    allocator = system
    threads   = enabled
    tls       = enabled
    io        = enabled
    panic     = configured

async:
    allocator = system
    threads   = enabled
    async     = enabled
    io        = enabled
```

---

# 4. Runtime Component ABI

Mỗi runtime component phải có ABI rõ ràng:

```text
RuntimeComponent {
    id
    version
    target
    dependencies
    provided_symbols
    required_symbols
    init
    shutdown
    capabilities
}
```

Ví dụ:

```text
allocator.system
    provides:
        alloc
        realloc
        dealloc
        alloc_aligned
```

---

# 5. Startup Model

Axiom không được mặc định giả định rằng chương trình luôn bắt đầu bằng một runtime lớn.

Compiler tạo:

```text
Entry
 ↓
Startup
 ↓
User Main
 ↓
Shutdown
```

Nhưng startup có thể tối giản thành:

```text
Entry
 ↓
main
 ↓
exit
```

với freestanding.

Hosted có thể:

```text
OS Entry
 ↓
Axiom Startup
 ↓
TLS Init
 ↓
Allocator Init
 ↓
Runtime Init
 ↓
main
 ↓
Runtime Shutdown
 ↓
OS Exit
```

---

# 6. Runtime Initialization Ordering

Component phải khai báo:

```text
requires_before(A, B)
```

hoặc dependency:

```text
B depends_on A
```

Compiler/build graph tạo DAG.

Không được phép:

```text
A → B → A
```

Nếu cycle tồn tại:

```text
runtime initialization cycle
```

là lỗi build.

---

# 7. Runtime ABI không được phụ thuộc implementation của compiler

Compiler phải có một interface ổn định:

```text
Runtime ABI
```

thay vì backend gọi trực tiếp vào một implementation cụ thể.

Ví dụ semantic operation:

```text
ALLOC(size, align)
PANIC(payload)
THREAD_SPAWN(...)
TLS_GET(...)
ASYNC_WAKE(...)
```

sau đó target/runtime lowering chọn implementation.

---

# 8. Allocator Component

Allocator API semantic:

```axiom
trait Allocator {
    fn allocate(...)
    fn resize(...)
    fn deallocate(...)
}
```

Các implementation:

```text
SystemAllocator
ArenaAllocator
PoolAllocator
SlabAllocator
StackAllocator
BumpAllocator
CustomAllocator
```

Compiler không được giả định:

```text
allocate == malloc
```

vì allocator có thể được:

- inline;
- static;
- arena;
- stack;
- custom;
- GPU/device.

---

# 9. Panic Component

Panic policy là runtime/build configuration:

```text
abort
unwind
custom
```

Core semantic vẫn có:

```text
panic
```

nhưng implementation có thể là:

```text
panic → process termination
```

hoặc:

```text
panic → unwind
```

Runtime unwind chỉ được link khi profile yêu cầu.

---

# 10. Thread Component

Thread runtime cung cấp:

```text
spawn
join
thread_id
thread_local
yield
sleep
```

Nhưng Core concurrency semantic vẫn được compiler kiểm tra độc lập.

Runtime không được biến:

```text
Send
Share
Atomic
Mutex
```

thành runtime-only semantics.

---

# 11. TLS Component

Thread-local storage phải có abstraction:

```text
TLS<T>
```

Compiler/backend có thể lower xuống:

- ELF TLS;
- PE TLS;
- Mach-O TLS;
- platform API;
- emulated TLS.

Không để user phải biết ABI TLS của từng OS.

---

# 12. Async Runtime

Async Core chỉ tạo:

```text
Future
Poll
Waker
```

Runtime cung cấp:

```text
Executor
Scheduler
Timer
IO reactor
Task storage
```

Có thể có:

```text
single_thread_executor
multi_thread_executor
io_executor
deterministic_executor
```

Không có async runtime mặc định nếu chương trình không dùng async.

---

# 13. I/O Component

I/O không thuộc runtime bắt buộc.

Các component:

```text
FileIO
SocketIO
ConsoleIO
AsyncIO
MemoryMappedIO
DeviceIO
```

FFI tới OS được đóng trong platform layer.

Ví dụ:

```text
Axiom File
      ↓
Axiom IO ABI
      ↓
Windows implementation
Linux implementation
macOS implementation
```

---

# 14. Unicode Component

Unicode processing không được tự động kéo vào mọi executable.

Tách:

```text
UTF8-Core
Unicode-Scalar
Unicode-Normalization
Unicode-Case
Unicode-Segmentation
```

Chương trình chỉ xử lý bytes có thể hoàn toàn không link Unicode database.

---

# 15. Runtime Component Discovery

Compiler phải xác định dependency bằng semantic analysis:

```text
Program
  ↓
Semantic requirements
  ↓
Runtime capability requirements
  ↓
Runtime dependency graph
  ↓
Component selection
  ↓
Dead component elimination
  ↓
Link
```

Ví dụ:

```axiom
fn main() {
    let x = Box<i32>(42)
}
```

có thể yêu cầu:

```text
allocator
```

nhưng:

```text
thread
async
unicode
reflection
```

không được tự động kéo vào.

---

# 16. Runtime-Free Verification

Compiler phải có mode:

```text
--runtime=none
```

Nếu chương trình vô tình yêu cầu runtime:

```text
error: runtime capability required

required component:
    allocator

required by:
    Box<i32>

suggestions:
    provide an allocator
    use static storage
    use an arena
```

Điều này đặc biệt quan trọng cho:

- kernel;
- embedded;
- bootloader;
- firmware;
- tiny CLI;
- freestanding;
- GPU.

---

# 17. Runtime Provider

Runtime component không nhất thiết phải do Axiom cung cấp.

ABI cho phép:

```text
Axiom Runtime
External Runtime
OS Runtime
User Runtime
Embedded Runtime
```

Ví dụ embedded:

```text
Axiom
  ↓
runtime ABI
  ↓
user-provided allocator
  ↓
MCU hardware
```

---

# 18. Runtime Component Override

Người dùng có thể thay implementation:

```text
allocator = MyAllocator
panic = MyPanic
scheduler = MyScheduler
```

Compiler vẫn kiểm tra ABI contract.

Không cho override làm thay đổi semantic contract của Core.

---

# 19. Runtime Metadata

Mỗi executable có thể chứa metadata:

```text
RuntimeManifest {
    components
    versions
    ABI
    target
    initialization_order
}
```

Nhưng metadata này:

- optional;
- có thể strip;
- không phải runtime object.

---

# 20. Static vs Dynamic Runtime

Hỗ trợ:

```text
static runtime
dynamic runtime
fully embedded runtime
no runtime
```

Ví dụ:

```text
app.exe
 ├── application
 ├── allocator
 ├── thread
 └── io
```

hoặc:

```text
app.exe
  ↓
axiom-runtime.dll
```

Dynamic runtime chỉ là deployment option, không phải semantic requirement.

---

# 21. Runtime Versioning

Runtime ABI phải có:

```text
major
minor
revision
```

Quy tắc:

```text
major change → incompatible
minor change → backward-compatible extension
revision     → bug/security compatible
```

Compiler phải kiểm tra compatibility trước link.

---

# 22. Runtime ↔ FFI

Runtime không được giả định rằng toàn bộ process đều thuộc Axiom.

Ví dụ:

```text
Axiom
  ↓
C library
  ↓
OS
```

hoặc:

```text
Axiom runtime
  ↓
foreign callback
  ↓
Axiom function
```

FFI boundary phải khai báo:

```text
ABI
calling convention
ownership
threading
unwind behavior
allocation domain
```

---

# 23. Runtime ↔ GPU

GPU runtime không được kéo vào CPU executable nếu không cần.

Các component:

```text
GPU Driver Interface
Device Runtime
Kernel Launcher
GPU Allocator
Event Runtime
```

CPU-only:

```text
no GPU component
```

GPU program:

```text
CPU runtime
+
GPU runtime
```

Kernel binary có thể được đóng gói riêng trong executable.

---

# 24. Runtime Build Pipeline

BOOTSTRAP-305 được mở rộng thành:

```text
Source
 ↓
Semantic Analysis
 ↓
Runtime Requirement Extraction
 ↓
Runtime Component Resolver
 ↓
Runtime Graph
 ↓
Component Compilation
 ↓
Object Generation
 ↓
Application Objects
 ↓
Runtime Objects
 ↓
Linker
 ↓
Executable
```

Runtime component cũng đi qua compiler pipeline bình thường.

---

# 25. Self-hosting Requirement

Runtime phải cuối cùng được viết bằng Axiom.

Không được thiết kế architecture mà:

```text
Axiom compiler
    permanently depends on
    C runtime
```

Bootstrap có thể sử dụng C/OS ABI tạm thời.

Final architecture:

```text
Axiom Compiler
     ↓
Axiom Runtime Components
     ↓
Axiom Object/Linker
     ↓
Native Executable
```

---

# 26. Runtime Component Interface

Đề xuất cấu trúc nội bộ:

```text
compiler/runtime/
    manifest/
    resolver/
    graph/
    abi/
    startup/
    shutdown/
    allocator/
    panic/
    unwind/
    thread/
    tls/
    async/
    io/
    unicode/
    gpu/
    reflection/
    platform/
    verification/
```

Không nhất thiết tất cả đều là runtime; nhiều phần sẽ là library/platform component.

---

# 27. Runtime Verifier

Runtime component cũng phải được kiểm tra:

```text
ABI compatibility
dependency validity
initialization order
shutdown order
symbol uniqueness
calling convention
allocator compatibility
FFI contracts
threading contracts
panic/unwind contracts
TLS contracts
target compatibility
```

Runtime không được trở thành “vùng miễn kiểm tra”.

---

# 28. Runtime Selection Algorithm

Compiler thực hiện:

```text
1. Collect required capabilities
2. Resolve provider for each capability
3. Build dependency DAG
4. Detect conflicts
5. Select target implementation
6. Remove unreachable components
7. Generate startup/shutdown graph
8. Verify ABI
9. Emit runtime objects
10. Link
```

Nếu có nhiều provider:

```text
SystemAllocator
MyAllocator
```

phải có resolution rule rõ ràng; không chọn ngẫu nhiên.

---

# 29. Runtime không được phá vỡ zero-cost abstraction

Ví dụ nếu compiler chứng minh:

```text
Vec<T>
```

không cần heap:

```text
stack/register representation
```

thì **không được vì Vec thuộc thư viện mà tự động link allocator**.

Tương tự:

```text
async fn
```

không tự động kéo scheduler nếu Future chỉ được tạo nhưng không spawn.

Đây là điểm rất quan trọng:

> **Runtime dependency phải dựa trên semantic necessity, không dựa trên tên type/library.**

---

# 30. Definition of Done

BOOTSTRAP-306 chỉ hoàn thành khi Axiom có thể:

### Runtime-free

```text
axiom build --runtime=none
```

tạo chương trình native không runtime.

### Hosted

```text
axiom build --profile=hosted
```

tự động chọn các component cần thiết.

### Async

```text
axiom build --profile=async
```

chỉ link async components cần thiết.

### Custom allocator

```text
allocator = MyAllocator
```

hoạt động qua Runtime ABI.

### Freestanding

Có thể build chương trình không phụ thuộc OS runtime.

### Cross-platform

Runtime resolver chọn implementation phù hợp:

```text
Windows
Linux
macOS
WASM
Embedded
GPU
```

### Self-host

Runtime architecture đủ độc lập để sau này:

```text
compiler + runtime + linker
```

đều có thể được implement bằng Axiom.

---

## Invariants mới

Đóng băng các invariant chính:

```text
ARUNTIME-20
Runtime is optional.

ARUNTIME-21
Core language semantics do not depend on runtime presence.

ARUNTIME-22
Runtime dependencies are capability-driven.

ARUNTIME-23
Unused runtime components must not be linked.

ARUNTIME-24
Runtime components form an acyclic dependency graph.

ARUNTIME-25
Runtime initialization order is deterministic.

ARUNTIME-26
Runtime shutdown order is deterministic.

ARUNTIME-27
Runtime ABI contracts are explicit.

ARUNTIME-28
Runtime components cannot bypass Core safety verification.

ARUNTIME-29
Runtime-free programs are a supported first-class target.

ARUNTIME-30
Allocator is not synonymous with heap.

ARUNTIME-31
Async requires executor only when execution is requested.

ARUNTIME-32
Thread support is not implicit in Send/Share semantics.

ARUNTIME-33
GPU runtime is optional.

ARUNTIME-34
Unicode runtime/data is optional.

ARUNTIME-35
FFI runtime boundaries require explicit ABI contracts.

ARUNTIME-36
Runtime provider replacement cannot alter Core semantics.

ARUNTIME-37
Runtime selection is deterministic.

ARUNTIME-38
Runtime version compatibility is verified before link.

ARUNTIME-39
Runtime component symbols obey normal linker rules.

ARUNTIME-40
Runtime components are ordinary compilable artifacts.

ARUNTIME-41
Final self-hosted Axiom does not require a permanent C/C++ runtime dependency.

ARUNTIME-42
Runtime elimination must preserve observable semantics.

ARUNTIME-43
Optimization may eliminate runtime operations proven unnecessary.

ARUNTIME-44
Runtime capability requirements are represented in the build graph.

ARUNTIME-45
Runtime configuration does not change language type/ownership semantics.
```

**Kết quả kiến trúc:** Axiom không có khái niệm “một runtime khổng lồ”. Thay vào đó là **một tập capability/runtime components có thể được compiler tự động chọn, loại bỏ và tối ưu**, từ đó vừa phù hợp với ứng dụng desktop/server vừa đủ khả năng chạy freestanding/kernel/embedded mà không phải hy sinh mô hình ngôn ngữ.