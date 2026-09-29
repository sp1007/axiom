# BOOTSTRAP-364 — Axiom Thread, Execution Domain & Native Threading Engine

Sau 363, memory model và race verification đã đủ nền tảng. Bước tiếp theo là định nghĩa **execution model**: thread thực sự là gì trong Axiom, compiler phân biệt CPU thread / task / worker / interrupt / GPU execution như thế nào, và cách một chương trình Axiom ánh xạ xuống OS threads mà **không ép toàn bộ ngôn ngữ phải phụ thuộc runtime**.

Mục tiêu quan trọng:

> `thread` là execution resource; `Future` là computation; `Task` là execution instance; synchronization là cơ chế phối hợp. Không trộn ba khái niệm này.

---

# 1. Execution Domain là abstraction nền tảng

Axiom cần một semantic khái niệm:

```text
ExecutionDomain
```

Các domain Core:

```text
CPU
GPU
DEVICE
INTERRUPT
COMPTIME
```

Library/runtime có thể bổ sung:

```text
IO_WORKER
BLOCKING_WORKER
REALTIME
EMBEDDED
DISTRIBUTED
```

Nhưng compiler phải hiểu domain cơ bản.

Ví dụ:

```text
CPU function
GPU kernel
interrupt handler
comptime function
```

không phải chỉ là function với một attribute khác nhau.

Chúng có **execution contract khác nhau**.

---

# 2. Thread là gì?

Thread là:

```text
independent execution context
+
stack/state
+
scheduler association
+
thread-local state
```

Nhưng:

> Thread không phải object bắt buộc phải được heap allocate bởi Axiom runtime.

Một native thread có thể do:

```text
OS
runtime
embedded scheduler
user scheduler
```

quản lý.

---

# 3. `spawn_thread`

Semantic API:

```axiom
let t = spawn_thread(worker)
```

không có nghĩa compiler phải gọi một runtime function cố định.

Compiler có thể lower thành:

```text
Axiom Thread ABI
        ↓
Windows CreateThread
Linux pthread/clone
macOS pthread
bare-metal startup
```

ở backend/runtime layer.

Core semantics vẫn giữ nguyên.

---

# 4. Thread function contract

Một thread entry function phải có contract:

```text
ThreadEntry {
    input ownership
    output result
    Send requirements
    panic policy
    execution domain
    stack requirements
    TLS requirements
}
```

Ví dụ:

```axiom
fn worker(data: Data) -> Result {
    ...
}
```

Nếu truyền ownership vào thread:

```text
Data : Send
```

phải được chứng minh.

---

# 5. Thread migration

Native OS thread thường không có semantic identity ổn định với CPU core.

Axiom phân biệt:

```text
ThreadIdentity
CPUCore
Worker
Task
```

Không được giả định:

```text
thread == core
```

hay:

```text
task == thread
```

---

# 6. CPU Affinity

Affinity là system-level property.

Ví dụ:

```axiom
thread.set_affinity(mask)
```

được xem là:

```text
ExecutionPlacementConstraint
```

chứ không thay đổi semantics của ownership.

Compiler không được dựa vào affinity để chứng minh:

```text
no data race
```

trừ khi execution contract thực sự bảo đảm exclusive execution.

---

# 7. Thread Local Storage

Axiom hỗ trợ:

```text
thread_local<T>
```

nhưng semantic identity là:

```text
(ThreadId, VariableId)
```

chứ không phải một global variable.

Ví dụ:

```axiom
thread_local var counter: i64 = 0
```

mỗi thread có một instance riêng.

Do đó:

```text
counter += 1
```

không cần synchronization giữa các threads.

---

# 8. TLS initialization

TLS initializer có ba loại:

```text
CONSTANT
COMPTIME
RUNTIME
```

Ưu tiên:

```text
constant/comptime
```

để tránh hidden runtime initialization.

Runtime TLS initialization chỉ chạy khi thread thực sự truy cập instance nếu platform cho phép lazy initialization.

---

# 9. Thread Handle

Thread handle là **logical identity**, không phải raw OS handle.

```text
ThreadHandle
```

có thể chứa:

```text
ThreadId
Generation
RuntimeHandle
```

nhưng representation không phải Core ABI.

Không cho phép programmer giả định:

```text
ThreadHandle == pointer
```

---

# 10. Thread Join

```axiom
let result = thread.join(t)
```

tạo synchronization:

```text
thread execution
       │
       ▼
completion
       │
       ▼
join
```

Theo 363:

```text
all relevant effects before completion
        HB
effects after successful join
```

---

# 11. Join ownership

Nếu thread trả:

```axiom
Data
```

thì ownership được chuyển qua join.

Không cần:

```text
Arc<Data>
```

nếu chỉ có một consumer.

Ví dụ:

```axiom
let t = spawn_thread(fn() -> Data {
    make_data()
})

let data = t.join()
```

Compiler có thể thực hiện:

```text
caller-provided result slot
```

thay vì heap allocation.

---

# 12. Thread Detach

Detach phải explicit:

```axiom
thread.detach(t)
```

Sau detach:

```text
caller no longer owns completion/result
```

nhưng thread vẫn chạy.

Không được có implicit detach khi handle bị drop.

Điều này tương tự Task semantics của 361.

---

# 13. Thread Handle Drop

Dropping:

```text
ThreadHandle
```

không mặc định:

```text
cancel thread
join thread
detach thread
```

Vì ba semantics khác nhau.

API phải yêu cầu programmer chọn.

Ví dụ:

```text
join()
detach()
cancel()
```

nếu platform hỗ trợ cancellation contract.

---

# 14. Thread cancellation

Axiom không cho phép arbitrary asynchronous thread kill trong safe Core.

Lý do:

```text
thread đang giữ lock
thread đang sở hữu resource
thread đang giữa transaction
thread đang cập nhật invariant
```

nếu bị kill tại bất kỳ instruction nào thì cleanup semantics có thể không bảo đảm được.

Do đó:

```text
cancellation = cooperative
```

là mặc định.

---

# 15. Cancellation Point

Thread có thể kiểm tra:

```axiom
cancel_token.is_cancelled()
```

hoặc library abstraction tương tự.

Compiler có thể tối ưu check nếu chứng minh token không thể bị cancel.

---

# 16. Blocking

Compiler cần phân biệt:

```text
BLOCKING
NON_BLOCKING
MAY_BLOCK
```

Ví dụ:

```text
file.read()
```

có thể blocking.

Trong async execution:

```text
await async_read()
```

không nhất thiết blocking OS thread.

---

# 17. Blocking thread

Runtime có thể cung cấp:

```text
spawn_blocking(...)
```

Semantics:

```text
blocking work
       ↓
dedicated worker pool
```

Điều này ngăn blocking syscall chiếm executor worker.

Compiler có thể ghi effect:

```text
Effect::MayBlock
```

vào function summary.

---

# 18. Thread-safe function

Axiom không nên có annotation kiểu:

```text
@thread_safe
```

để programmer tự tuyên bố.

Compiler nên suy ra từ:

```text
Send
Share
ownership
effects
synchronization
unsafe contracts
```

Ví dụ function:

```axiom
fn process(x: Data)
```

nếu `Data : Send`, function có thể chạy ở thread khác.

---

# 19. `Send` và `Share`

Hai auto traits tiếp tục giữ nguyên:

```text
Send
Share
```

### Send

Giá trị có thể chuyển ownership sang execution context khác.

### Share

Giá trị có thể được truy cập đồng thời theo contract của type.

Không được suy ra:

```text
Send => Share
```

hoặc:

```text
Share => Send
```

trừ khi trait logic của type chứng minh.

---

# 20. Execution capability

Compiler internal có:

```text
ExecutionCapability
```

Ví dụ:

```text
CPU_LOCAL
CPU_SHARED
GPU_DEVICE
GPU_KERNEL
INTERRUPT
COMPTIME
```

Function contract:

```text
ExecutionContract {
    allowed_domains
    required_capabilities
    forbidden_operations
}
```

---

# 21. GPU interaction

Ví dụ:

```axiom
@kernel
fn add(...)
```

có:

```text
ExecutionDomain = GPU
```

Do đó compiler biết:

```text
File I/O
Socket
OS syscall
blocking mutex
arbitrary host pointer
```

không hợp lệ.

Không cần đợi GPU backend mới phát hiện.

---

# 22. Interrupt domain

Interrupt handler là một execution domain đặc biệt.

Không được mặc định:

```text
sleep
await
blocking lock
allocate arbitrary heap
```

Interrupt-safe API cần contract:

```text
InterruptSafe
```

Compiler có thể kiểm tra call graph:

```text
interrupt handler
    ↓
called function
    ↓
called function
```

nếu một function có:

```text
MayBlock
MayAllocate
MayAwait
```

thì bị reject nếu contract không cho phép.

---

# 23. Real-time domain

Không cần Core primitive mới.

Runtime/library có thể định nghĩa:

```text
RealtimeExecutionContract
```

với:

```text
NoBlocking
NoUnboundedAllocation
BoundedExecution
NoUnexpectedSyscall
```

Compiler effect system có thể kiểm tra.

Đây là ví dụ sức mạnh của architecture:

> Không cần biến mọi execution policy thành syntax mới.

---

# 24. Worker

Worker không phải Thread.

Worker là:

```text
scheduler-managed execution resource
```

Một threadpool có thể:

```text
4 workers
8 OS threads
1000 tasks
```

Task được schedule lên worker.

Do đó:

```text
Task ≠ Thread
Worker ≠ Thread
```

---

# 25. CPU execution hierarchy

Mô hình:

```text
Process
 ├── Thread
 │    └── Execution Context
 │
 └── Thread
      └── Execution Context

Executor
 ├── Worker
 │    └── Thread
 │
 └── Worker
      └── Thread

Task
 └── Future
```

Một Task có thể chạy:

```text
worker A
   ↓
suspend
   ↓
worker B
```

nếu executor cho phép migration.

---

# 26. Thread affinity vs Task affinity

Hai khái niệm riêng:

```text
ThreadAffinity
TaskAffinity
```

Task affinity có thể yêu cầu:

```text
same worker
same CPU group
same NUMA node
same thread
```

nhưng chỉ khi executor hỗ trợ.

---

# 27. NUMA

Axiom không nên đưa NUMA vào basic language syntax.

Nhưng compiler/runtime cần metadata:

```text
MemoryDomain
ExecutionDomain
NUMANode
```

để library cấp cao có thể tối ưu:

```text
allocate_local(node)
run_on(node)
```

Memory model 363 vẫn áp dụng.

---

# 28. Thread Stack

Stack size là execution configuration.

```text
ThreadConfig {
    stack_size
    guard_size
    priority
    affinity
    name
}
```

Không đưa các field này vào Core semantic function type.

---

# 29. Stack growth

Axiom có thể hỗ trợ:

```text
fixed stack
growable stack
segmented stack
runtime-managed stack
```

nhưng function semantics không phụ thuộc implementation.

Compiler phải biết nếu một target:

```text
stack limit
```

có thể ảnh hưởng safety.

---

# 30. Thread stack allocation

Không bắt buộc heap.

Platform có thể:

```text
OS stack allocation
static stack
arena
runtime stack allocator
```

Axiom compiler chỉ yêu cầu:

```text
valid stack storage
```

---

# 31. Thread startup

Thread startup phải thiết lập:

```text
TLS
panic policy
stack
execution domain
runtime context
```

nhưng runtime context chỉ được tạo khi profile yêu cầu.

Một freestanding program có thể có:

```text
entry
 ↓
thread
 ↓
main
```

mà không link full Axiom runtime.

---

# 32. Main thread

`main` là một execution context đặc biệt:

```text
MainThread
```

nhưng semantics không khác biệt quá mức.

Program exit policy phải explicit:

```text
return from main
```

→ process termination.

Nếu còn detached threads:

```text
process exit
```

có thể terminate chúng theo OS semantics.

Compiler không được tự biến chúng thành joined threads.

---

# 33. Process vs Thread

Axiom phải phân biệt:

```text
Process
Thread
Task
Worker
Executor
```

Process thuộc OS/system layer.

Thread thuộc execution layer.

Task thuộc concurrency runtime.

Không nên tạo:

```text
class Thread
```

trong Core.

Đây là library/system resource.

---

# 34. Process spawning

System library có:

```text
spawn_process(...)
```

nhưng semantics ownership phải rõ:

```text
ProcessHandle
stdin
stdout
stderr
environment
working_directory
```

Không thuộc BOOTSTRAP-364 sâu hơn; chỉ xác định boundary.

---

# 35. CompilerDB additions

364 bổ sung:

```text
ExecutionDomainDB
ExecutionContextDB
ThreadDB
ThreadTypeDB
ThreadSpawnDB
ThreadJoinDB
ThreadDetachDB
ThreadCancellationDB
ThreadConfigDB
ThreadAffinityDB
ThreadLocalDB
ThreadStackDB
ThreadEntryDB
WorkerDB
WorkerPoolDB
BlockingDB
BlockingEffectDB
ExecutionCapabilityDB
ExecutionContractDB
ExecutionPlacementDB
TaskThreadRelationDB
TaskMigrationDB
ProcessDB
MainThreadDB
InterruptDB
RealtimeDB
NumaDB
```

---

# 36. MIR additions

Compiler MIR thêm:

```text
THREAD_SPAWN
THREAD_JOIN
THREAD_DETACH
THREAD_CANCEL_REQUEST

THREAD_LOCAL_GET
THREAD_LOCAL_SET

EXECUTION_DOMAIN_ENTER
EXECUTION_DOMAIN_EXIT

WORKER_SUBMIT
WORKER_YIELD

BLOCKING_CALL
NONBLOCKING_CALL

PROCESS_SPAWN
PROCESS_JOIN
```

Những operation này sau đó được target/runtime lowering.

---

# 37. Execution effect

Function summary mở rộng:

```text
ExecutionEffect {
    domains
    may_block
    may_spawn
    may_join
    may_detach
    may_migrate
    requires_tls
    requires_runtime
    interrupt_safe
    gpu_legal
}
```

Compiler có thể propagate xuyên call graph.

Ví dụ:

```text
fn interrupt_handler()
    ↓
read_device()
    ↓
syscall()
```

Nếu `syscall()` có:

```text
MayBlock
```

compiler phát hiện violation.

---

# 38. Runtime dependency minimization

Đây là phần rất quan trọng đối với mục tiêu binary nhỏ.

Nếu chương trình chỉ:

```axiom
fn main() {
    print("hello")
}
```

không nên tự động kéo vào:

```text
thread scheduler
async executor
GPU runtime
TLS subsystem
reflection
network
```

Runtime linking phải capability-driven:

```text
program requirements
        ↓
Runtime Feature Graph
        ↓
minimal runtime
```

---

# 39. Threading không đồng nghĩa runtime bắt buộc

Program:

```axiom
fn main() {
    spawn_thread(...)
}
```

chỉ cần thread runtime/platform adapter.

Program:

```text
single-thread freestanding
```

không cần thread subsystem.

Do đó:

```text
Thread support ≠ mandatory runtime
```

---

# 40. Thread ABI

Axiom cần một abstract ABI:

```text
AxiomThreadABI
```

bao gồm:

```text
entry pointer
argument storage
result storage
TLS initialization
stack setup
completion state
panic handling
```

Target backend map nó sang:

```text
Win32
POSIX
Mach
Linux syscall
embedded
custom RTOS
```

---

# 41. Native thread optimization

Compiler được phép tối ưu:

```text
spawn_thread(f)
join()
```

nếu toàn bộ execution graph chứng minh thread không cần concurrent execution.

Ví dụ:

```text
spawn
  ↓
immediately join
```

có thể trở thành:

```text
call f()
```

**nếu**:

- không observable thread identity;
- không có TLS dependency;
- không có synchronization observation;
- không có scheduling observation;
- không có external thread interaction.

Đây là một ví dụ rất mạnh của whole-program optimization.

---

# 42. Nhưng không được giả định thread vô nghĩa

Nếu:

```text
thread_id()
```

được quan sát,

hoặc:

```text
thread_local
```

được sử dụng,

hoặc có synchronization với thread khác,

thì thread creation là observable.

Không được loại.

---

# 43. Execution Identity

Compiler phải phân biệt:

```text
ExecutionIdentity
```

với:

```text
StorageIdentity
ValueIdentity
LogicalIdentity
```

Thread ID là execution identity.

Không dùng địa chỉ stack làm thread identity.

---

# 44. Safe thread API

Mô hình API library dự kiến:

```text
Thread
ThreadHandle
ThreadConfig
ThreadId
CancelToken
JoinResult
```

và:

```text
spawn_thread
join
detach
yield
sleep
current_thread
thread_local
```

Core compiler hiểu semantics của một số operation quan trọng; phần API cụ thể thuộc standard library.

---

# 45. Invariants

Đóng băng các invariant chính:

### `ATHREAD-01`
Thread is an execution resource, not a Future.

### `ATHREAD-02`
Future is computation, not execution.

### `ATHREAD-03`
Task is an owned execution instance of a Future.

### `ATHREAD-04`
Worker is scheduler resource, not semantic thread identity.

### `ATHREAD-05`
Thread creation is explicit.

### `ATHREAD-06`
Thread join establishes completion synchronization.

### `ATHREAD-07`
Thread result ownership is explicit.

### `ATHREAD-08`
Dropping a thread handle does not implicitly cancel or join.

### `ATHREAD-09`
Detach is explicit.

### `ATHREAD-10`
Asynchronous thread termination is not a safe primitive.

### `ATHREAD-11`
Cancellation is cooperative by default.

### `ATHREAD-12`
Send is required for ownership transfer between execution contexts.

### `ATHREAD-13`
Share does not imply Send.

### `ATHREAD-14`
Send does not imply Share.

### `ATHREAD-15`
Thread identity is distinct from CPU identity.

### `ATHREAD-16`
Thread identity is distinct from Task identity.

### `ATHREAD-17`
Thread-local storage is isolated by execution thread.

### `ATHREAD-18`
TLS does not require global synchronization.

### `ATHREAD-19`
Blocking is an explicit execution effect.

### `ATHREAD-20`
Async execution must not silently block an executor worker.

### `ATHREAD-21`
Interrupt execution has a restricted execution contract.

### `ATHREAD-22`
GPU execution has a distinct execution domain.

### `ATHREAD-23`
Execution-domain restrictions are compiler-verifiable.

### `ATHREAD-24`
Execution domain does not override memory safety.

### `ATHREAD-25`
Thread affinity does not establish memory safety.

### `ATHREAD-26`
NUMA placement does not alter language memory semantics.

### `ATHREAD-27`
Thread stack storage is implementation-defined.

### `ATHREAD-28`
Runtime support is capability-driven.

### `ATHREAD-29`
Thread support is not mandatory for single-thread programs.

### `ATHREAD-30`
Compiler may eliminate thread creation only when execution identity and synchronization semantics are unobservable.

---

## Kết quả của BOOTSTRAP-364

Đến đây Axiom có mô hình rất rõ:

```text
                  ┌──────── Future ────────┐
                  │      computation       │
                  └──────────┬─────────────┘
                             │
                           Task
                             │
                             ▼
                         Executor
                             │
                           Worker
                             │
                             ▼
                           Thread
                             │
                             ▼
                         CPU/OS
```

Trong khi memory side là:

```text
Ownership
    ↓
Capability
    ↓
Synchronization
    ↓
Happens-Before
    ↓
Memory Model
    ↓
Hardware
```

Hai trục này giao nhau tại **Execution Context + Memory Access**.

Đây là điểm quan trọng để Axiom vừa có concurrency hiện đại, vừa giữ được mục tiêu **native, runtime-optional, không GC, không borrow/lifetime syntax và không bắt programmer quản lý các chi tiết compiler có thể tự chứng minh**.