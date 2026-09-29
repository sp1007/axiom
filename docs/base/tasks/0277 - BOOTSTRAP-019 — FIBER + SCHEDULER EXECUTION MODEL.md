# BOOTSTRAP-019 — FIBER + SCHEDULER EXECUTION MODEL

Bây giờ ta chuyển từ **“concurrency semantics”** sang **“cơ chế thực thi”**.

Mục tiêu của phần này là chốt một nguyên tắc rất quan trọng:

> **Axiom compiler chỉ tạo ra computation đã được kiểm chứng. Runtime quyết định computation đó chạy ở đâu, khi nào và trên execution resource nào.**

Và cần tránh một sai lầm phổ biến: biến `async`, `task`, `fiber`, `thread` thành một hệ thống runtime khổng lồ.

---

# 1. Bốn abstraction phải tách biệt

Axiom có:

```text
Thread
Fiber
Task
Future
```

nhưng chúng **không phải bốn tên gọi cho cùng một thứ**.

```text
Thread
    = OS execution resource

Fiber
    = user-space stackful execution context

Task
    = schedulable unit of asynchronous computation

Future
    = stackless state machine representing computation
```

Quan hệ:

```text
Thread
 ├── Fiber A
 ├── Fiber B
 └── Task scheduler
       ├── Future A
       ├── Future B
       └── Future C
```

Một Task không nhất thiết có Fiber.

Một Future không nhất thiết có Thread riêng.

---

# 2. Future là computation, Task là scheduling identity

Ví dụ:

```axiom
async fn download() -> Result<Buffer, Error> {
    ...
}
```

gọi:

```axiom
let f = download();
```

tạo:

```text
Future
```

chứ chưa tạo:

```text
Thread
Task
Fiber
```

Nếu:

```axiom
spawn(f);
```

thì mới tạo:

```text
Task
```

để scheduler quản lý.

---

# 3. Fiber khác Future

Fiber có stack thật:

```text
Fiber
 ├── stack
 ├── SP
 ├── IP
 ├── callee-saved registers
 └── execution state
```

Future:

```text
Future
 ├── state
 ├── live locals
 ├── suspension point
 └── waker
```

Future không cần stack riêng.

---

# 4. Vì sao Axiom vẫn cần Fiber?

Vì có những workload mà stackful execution rất hữu ích:

```text
game scripting
legacy blocking code
coroutines
user-space scheduler
green threads
embedded runtime
high-performance server
```

Ví dụ:

```axiom
fiber_spawn {
    blocking_style_algorithm();
}
```

Có thể chạy trên user-space stack mà không cần OS thread cho mỗi computation.

---

# 5. Fiber không tự động migration

MVP:

```text
Fiber
    ↓
pinned execution domain
```

Một Fiber đang chạy trên Worker 2 không tự nhiên bị chuyển sang Worker 5.

Muốn migration phải có explicit contract.

Lý do:

- stack address có thể observable;
- native stack references;
- FFI;
- thread-local assumptions;
- unsafe code.

Do đó:

```text
Fiber migration = explicit capability
```

---

# 6. Fiber stack là storage contract

Khác với Future:

```text
Future
→ stack location có thể thay đổi nếu semantics cho phép
```

Fiber:

```text
Fiber
→ stack là execution resource identity
```

Vì vậy compiler biết:

```text
@fiber
```

hoặc runtime tạo Fiber abstraction thì stack lifetime trở thành observable contract.

---

# 7. Fiber context tối thiểu

Mỗi context switch không cần save toàn bộ CPU.

Conceptually:

```text
FiberContext {
    stack_pointer
    instruction_pointer
    callee_saved_registers
    platform_control_state
}
```

Target-specific.

x86-64:

```text
RSP
RIP
RBX
RBP
R12
R13
R14
R15
```

và các state khác nếu ABI/runtime yêu cầu.

Không nên hard-code danh sách này trong semantic compiler.

---

# 8. Context switch

MIR không cần biết:

```text
swap rsp
restore registers
ret
```

Compiler/runtime boundary:

```text
FiberSwitch(old, new)
```

sau đó target backend có intrinsic/system implementation.

Pipeline:

```text
Axiom
 ↓
FiberSwitch semantic operation
 ↓
target lowering
 ↓
x86_64 context switch
```

---

# 9. Context switch không phải syscall

Một lợi thế lớn của Fiber:

```text
Fiber A
   ↓
context switch
   ↓
Fiber B
```

có thể hoàn toàn user-space.

Không bắt buộc:

```text
kernel transition
```

Không bắt buộc allocation.

---

# 10. Fiber yield

```axiom
fiber.yield();
```

semantic:

```text
RUNNING
   ↓
READY
```

Scheduler sau đó chọn execution context khác.

Không phải:

```text
Thread.sleep()
```

và không nhất thiết gọi kernel.

---

# 11. Fiber state machine

MVP:

```text
NEW
 ↓
READY
 ↓
RUNNING
 ├──→ READY
 ├──→ WAITING
 └──→ COMPLETE
```

Cancellation:

```text
RUNNING/READY/WAITING
        ↓
CANCEL_REQUESTED
        ↓
cooperative checkpoint
        ↓
COMPLETE/CANCELLED
```

Không có:

```text
force_free_running_fiber()
```

---

# 12. Không được free stack khi Fiber còn chạy

Invariant cực kỳ quan trọng:

```text
Fiber stack lifetime
    ≥
Fiber execution lifetime
```

Không:

```text
cancel
 ↓
free stack
 ↓
Fiber vẫn đang chạy
```

Nếu cancellation là cooperative:

```text
request cancel
 ↓
Fiber reaches cancellation point
 ↓
cleanup
 ↓
stop
 ↓
stack reclaim
```

---

# 13. Fiber và Drop

Nếu Fiber đang chứa:

```text
resource A
resource B
resource C
```

khi Fiber kết thúc:

```text
Drop(C)
Drop(B)
Drop(A)
```

theo semantic initialization state.

Compiler không cần một “fiber GC”.

---

# 14. Fiber cancellation

Không nên có:

```axiom
fiber.kill()
```

với semantics “giết ngay lập tức”.

Điều đó phá vỡ:

```text
ownership
Drop
lock
capability
FFI
```

Thay vào đó:

```axiom
fiber.cancel();
```

chỉ request:

```text
cancel_requested = true
```

Fiber phải tự xử lý.

---

# 15. Cancellation point

Có thể là:

```text
await
channel.recv
mutex.lock_async
timer
explicit cancellation check
```

và runtime API:

```axiom
if cancellation_requested() {
    return Cancelled;
}
```

Compiler không cần ép mọi function thành cancellation-aware.

---

# 16. Scheduler

Scheduler quản lý:

```text
READY tasks/fibers
WAITING tasks/fibers
RUNNING execution contexts
```

Không quản lý:

```text
type checking
ownership
borrow
trait solving
```

những thứ đó đã xong lúc compile.

---

# 17. Worker model

Kiến trúc mặc định:

```text
               Scheduler
                   │
       ┌───────────┼───────────┐
       │           │           │
   Worker 0    Worker 1    Worker 2
       │           │           │
   local Q      local Q      local Q
```

Mỗi Worker có:

```text
local ready queue
current execution
worker state
```

---

# 18. Work stealing

Khi Worker 0 hết việc:

```text
Worker 0
    ↓
local queue empty
    ↓
steal Worker 1
```

Nhưng chỉ được steal computation có thể migrate:

```text
Send / migration-safe
```

Task local:

```text
!Send
```

không được steal.

---

# 19. Local queue

Fast path:

```text
push local
pop local
```

nên tránh global lock.

Một implementation tốt có thể dùng:

```text
owner push/pop
thief steal
```

theo work-stealing deque.

Nhưng đây là runtime implementation, không phải language semantics.

---

# 20. Global queue chỉ là fallback

Có thể:

```text
local queue
    ↓ empty
global injection queue
    ↓ empty
steal
    ↓ empty
wait
```

Global queue không phải semantic requirement.

---

# 21. Scheduler run loop

Conceptually:

```text
while !shutdown {
    task = local_pop();

    if task == none {
        task = steal();
    }

    if task == none {
        task = global_pop();
    }

    if task == none {
        wait_for_event();
        continue;
    }

    run(task);
}
```

---

# 22. Running task

Task có thể:

```text
RUNNING
```

sau đó:

### Future

```text
poll()
 ↓
Ready
```

hoặc:

```text
poll()
 ↓
Pending
```

### Fiber

```text
yield
 ↓
READY
```

hoặc:

```text
wait
 ↓
WAITING
```

---

# 23. Scheduler không spawn task khi wake

Sai:

```text
I/O event
 ↓
create new task
```

Đúng:

```text
WAITING task
 ↓
wake
 ↓
READY
```

Task identity được giữ nguyên.

Điều này tránh allocation/churn.

---

# 24. Waker

Future có:

```text
Waker
```

Waker không cần sở hữu Future.

Nó là:

```text
scheduling notification capability
```

Conceptually:

```text
Waker {
    task_identity
    scheduler_identity
}
```

implementation có thể nhỏ hơn.

---

# 25. Waker lifetime

Nếu external I/O giữ Waker:

```text
I/O subsystem
      ↓
   Waker
      ↓
   Task
```

scheduler phải đảm bảo task metadata vẫn valid cho tới khi registration bị unregister hoặc wake hoàn tất.

Đây là một trong các nơi lifetime của runtime cần được compiler/runtime implementation quản lý chặt.

---

# 26. Timer

Scheduler cần timer subsystem nhưng không nhất thiết một loại timer duy nhất.

Có thể:

```text
TimerWheel
MinHeap
OS timerfd
kqueue timer
IOCP timer
platform timer
```

Semantic API:

```axiom
sleep(duration);
```

hoặc:

```axiom
sleep_async(duration);
```

Implementation quyết định.

---

# 27. I/O readiness

Linux:

```text
epoll
io_uring
```

Darwin:

```text
kqueue
```

Windows:

```text
IOCP
```

Nhưng scheduler chỉ nhận abstraction:

```text
I/O completion/readiness event
```

Không để Future biết trực tiếp OS primitive.

---

# 28. Completion vs readiness

Phải giữ distinction:

```text
Readiness
    "resource can probably make progress"

Completion
    "operation has completed"
```

Ví dụ:

```text
epoll
→ readiness

IOCP
→ completion
```

Runtime adapter chuyển cả hai thành:

```text
wake capability
```

---

# 29. Async I/O buffer lifetime

Đây là nơi ownership model của Axiom phát huy mạnh.

Không:

```axiom
let buffer = local_buffer();

submit_async(buffer.view());

return;
```

nếu OS vẫn đang dùng buffer.

Compiler phải biết:

```text
I/O operation
    ↓
dependent capability
    ↓
buffer cannot die yet
```

---

# 30. Owned async I/O

API an toàn:

```axiom
let future = read_async(buffer);
let (buffer, n) = await future;
```

Ownership:

```text
caller
  ↓ Move
I/O operation
  ↓ completion
caller
```

Không cần lifetime annotation.

---

# 31. Async borrowed I/O

Có thể cho:

```axiom
await read_async_into(mut_view(buffer));
```

nhưng compiler phải chứng minh:

```text
buffer
    ≥
I/O operation lifetime
```

và không được cho capability escape bất hợp lệ.

---

# 32. Đây là lý do async phải tích hợp với capability checker

Pipeline:

```text
Capability
      +
Suspension
      +
I/O lifetime
```

Nếu chỉ type-check:

```text
mut_view<Buffer>
```

thì chưa đủ.

---

# 33. Future migration

Future có thể:

```text
Worker 0
   ↓ await
READY
   ↓ steal
Worker 2
   ↓ resume
```

chỉ khi future state:

```text
Send
```

nếu scheduler cho phép migration.

Nếu:

```text
!Send
```

thì:

```text
Worker affinity
```

được giữ.

---

# 34. Future không cần pinned API

Axiom vẫn giữ quyết định:

> Không có `Pin<T>` trong Core.

Compiler đã biết state machine và capability dependencies.

Stable address chỉ xuất hiện khi:

```text
storage contract
```

yêu cầu.

Ví dụ FFI/native self-referential abstraction có thể yêu cầu explicit stable storage.

---

# 35. Task storage

Task có thể được lưu:

```text
register
stack
inline
caller-owned
arena
heap
```

Compiler/runtime chọn tùy abstraction.

Không:

```text
Task = heap object
```

theo language semantics.

---

# 36. Khi nào bắt buộc dynamic storage?

Nếu scheduler cần:

```text
task outlives caller
```

thì phải có storage đủ lifetime.

Có thể là:

```text
runtime arena
```

hoặc:

```text
owned task allocation
```

nhưng đây là runtime policy.

Compiler vẫn có thể tối ưu một số trường hợp:

```text
spawn + join in same scope
```

thành caller-owned/stack-like representation nếu semantics cho phép.

---

# 37. Structured concurrency

Ví dụ API:

```axiom
scope {
    spawn(worker_a());
    spawn(worker_b());
}
```

Semantic:

```text
scope
 ├── child A
 └── child B
```

Scope không hoàn tất trước khi child lifecycle được resolve theo policy.

Đây là abstraction cực kỳ hữu ích để tránh task leak.

---

# 38. Structured cancellation

Nếu parent bị cancel:

```text
parent
 ├── child A
 ├── child B
 └── child C
```

có thể propagate:

```text
cancel request
 ↓
children
```

Nhưng cancellation vẫn cooperative.

---

# 39. Detached task

Nếu muốn:

```axiom
spawn_detached(worker());
```

thì explicit:

```text
parent
    ≠
child lifetime
```

Runtime phải giữ child sống độc lập.

Đây là nơi allocation có thể trở thành cần thiết.

---

# 40. Thread vs Worker

Không nên đồng nhất:

```text
Thread == Worker
```

Một Worker thường chạy trên một OS thread:

```text
Worker
   ↓
OS Thread
```

nhưng runtime có thể:

```text
1 thread
→ multiple workers sequentially
```

hoặc nhiều policy khác.

---

# 41. Thread affinity

System-level API có thể yêu cầu:

```axiom
thread_affine {
    ...
}
```

Ví dụ:

- OpenGL context
- GUI event loop
- OS UI objects
- TLS-dependent native API
- hardware context

Compiler/runtime phải bảo vệ execution-domain affinity.

---

# 42. Fiber + TLS

Fiber **không tự nhiên có TLS của riêng nó**.

TLS mặc định là:

```text
Thread-local
```

Nếu runtime muốn:

```text
Fiber-local storage
```

thì đó là abstraction riêng:

```text
FiberLocal<T>
```

Không nhập nhằng với TLS.

---

# 43. Fiber-local storage

Có thể:

```text
Thread
 ├── Fiber A → FiberLocal A
 └── Fiber B → FiberLocal B
```

Nhưng:

```text
FiberLocal
```

không phải machine TLS.

Nó là runtime lookup/state.

---

# 44. Fiber migration và local storage

Nếu Fiber được migrate:

```text
Fiber A
Worker 0
 ↓
Worker 1
```

Fiber-local state có thể migrate theo Fiber.

Thread-local state thì không.

Do đó:

```text
Fiber-local ≠ Thread-local
```

---

# 45. Scheduler abstraction

Nên định nghĩa semantic interface:

```text
Scheduler {
    spawn(Task)
    schedule(Task)
    wake(Task)
    cancel(Task)
    run()
    shutdown()
}
```

Nhưng đây là **library/runtime interface**, không phải Core keyword.

---

# 46. Compiler-facing runtime ABI

Compiler chỉ cần một số runtime hooks tối thiểu khi program sử dụng chúng.

Ví dụ:

```text
__axiom_task_spawn
__axiom_task_wake
__axiom_fiber_switch
__axiom_async_wait
```

Nhưng **không được link toàn bộ runtime**.

Runtime helper phải demand-driven.

---

# 47. Runtime-free program

Chương trình:

```axiom
fn main() -> i32 {
    return 42;
}
```

không được tự động kéo:

```text
scheduler
thread runtime
async runtime
allocator
reflection
```

vào executable.

---

# 48. Program có async

Nếu:

```axiom
async fn main_async() { ... }
```

runtime/executor chỉ được đưa vào nếu chương trình thực sự cần executor.

Có thể có:

```text
single-thread executor
multi-thread executor
io executor
custom executor
```

---

# 49. Custom executor

Axiom phải cho phép:

```axiom
my_executor.run(main_future);
```

thay vì:

```text
language bắt buộc global async runtime
```

Đây là điểm rất quan trọng để Axiom phù hợp:

- OS
- embedded
- game
- server
- HPC
- kernel
- bare-metal.

---

# 50. Freestanding

Một chương trình bare-metal có thể chỉ dùng:

```text
interrupt
scheduler
fiber
atomic
```

tự xây runtime của mình.

Không cần:

```text
std
allocator
OS
libc
```

nếu không dùng.

---

# 51. Runtime layering

Đề xuất chính thức:

```text
                 Axiom Core
                     │
        ┌────────────┴────────────┐
        │                         │
   compiler semantics        machine/ABI
        │
        ▼
   minimal runtime ABI
        │
 ┌──────┼─────────┐
 │      │         │
Thread Scheduler I/O
 │      │         │
 └──────┼─────────┘
        │
      std/runtime
```

Không có monolithic runtime.

---

# 52. Fiber runtime layout

MVP:

```text
runtime/fiber/
├── fiber.ax
├── context_x86_64.S / generated machine code
├── context_aarch64...
├── stack.ax
├── scheduler.ax
└── tests/
```

Nhưng về lâu dài không nên phụ thuộc assembler ngoài.

Context switch phải được Axiom machine encoder/codegen hỗ trợ hoặc được biểu diễn bằng compiler intrinsic/system function.

---

# 53. `@naked`

Context switch có thể cần:

```axiom
@naked
unsafe fn switch_context(...);
```

hoặc target-specific intrinsic.

`@naked`:

- không prologue/epilogue bình thường;
- ABI cực kỳ explicit;
- không dùng local compiler-generated frame tùy tiện.

Đây là system-level feature.

---

# 54. `@interrupt`

Tương tự:

```axiom
@interrupt
unsafe fn interrupt_handler(...);
```

Compiler phải dùng ABI/entry convention đặc biệt.

Không cho function bình thường giả dạng interrupt handler.

---

# 55. Scheduler shutdown

Shutdown phải xử lý:

```text
RUNNING
READY
WAITING
```

theo policy.

Không được:

```text
free everything
```

khi vẫn có external operation đang giữ capability.

Ví dụ:

```text
I/O request
 ↓
buffer
 ↓
task
```

shutdown phải resolve/cancel đúng lifecycle.

---

# 56. Cancellation + I/O

Nếu:

```text
task
 ↓
async read(buffer)
 ↓
cancel
```

không được lập tức:

```text
free(buffer)
```

nếu OS vẫn truy cập buffer.

Correct:

```text
cancel request
 ↓
I/O cancellation protocol
 ↓
operation no longer owns/uses buffer
 ↓
drop buffer
```

Đây là invariant cực kỳ quan trọng.

---

# 57. Scheduler và memory allocator

Scheduler không nên phụ thuộc allocator cho mọi operation.

Fast path:

```text
READY
 ↓
queue
 ↓
run
```

không cần allocation.

Task creation có thể allocate khi cần, nhưng runtime có thể:

```text
slab
pool
arena
intrusive nodes
```

---

# 58. Task recycling

Task storage có thể tái sử dụng:

```text
Task slot
 ↓ complete
recycle
 ↓
new task
```

Nhưng logical identity phải tránh ABA/stale handle.

Do đó nếu exposed handle:

```text
TaskId + generation
```

thay vì raw address.

---

# 59. ABA

Scheduler/channel/lock-free structures có thể gặp:

```text
A → B → A
```

và một CAS tưởng rằng value không đổi.

Runtime implementation phải có:

```text
generation
tagged pointer
epoch
hazard pointer
```

tùy algorithm.

Không đưa hazard pointer thành Core primitive.

---

# 60. Unified execution model

Sau BOOTSTRAP-019, semantic model:

```text
Execution
│
├── OS Thread
│     └── stack
│
├── Fiber
│     └── user stack
│
└── Task
      └── Future state machine
```

và:

```text
Scheduler
    ├── schedules Task
    └── may schedule Fiber
```

---

# 61. Quan hệ với ownership

Điểm đẹp nhất:

```text
Execution domain
       │
       ▼
Send / Share
       │
       ▼
Ownership + Capability
```

Không cần một hệ thống concurrency type riêng biệt khổng lồ.

---

# 62. Quan hệ với async

```text
async fn
   ↓
Future
   ↓
Task
   ↓
Scheduler
   ↓
Worker
   ↓
Thread
```

Mỗi tầng optional.

Có thể dừng ở bất kỳ tầng nào:

```text
Future.poll() trực tiếp
```

hoặc:

```text
Task → custom executor
```

hoặc:

```text
multi-thread scheduler
```

---

# 63. Quan hệ với Fiber

```text
blocking-style code
       ↓
Fiber
       ↓
Scheduler
       ↓
Worker Thread
```

Trong khi:

```text
async code
       ↓
Future
       ↓
Task
       ↓
Scheduler
```

Hai mô hình có thể coexist.

---

# 64. Không nên tự động chuyển Fiber ↔ Future

Không:

```text
mọi async = Fiber
```

và cũng không:

```text
mọi blocking function = Fiber
```

Nếu runtime muốn adapter:

```text
block_on(future)
run_in_fiber(fn)
```

thì đó là library abstraction.

---

# 65. Invariants BOOTSTRAP-019

```text
AFIBER-46   Fiber Is Stackful Execution Context
AFIBER-47   Future Is Stackless Computation State
AFIBER-48   Fiber Stack Is An Execution Resource
AFIBER-49   Fiber Stack Lifetime Covers Fiber Execution
AFIBER-50   Fiber Does Not Imply OS Thread
AFIBER-51   Fiber Context Contains Only Required Machine State
AFIBER-52   Context Switch Is A Target-Specific Operation
AFIBER-53   Fiber Migration Is Not Implicit
AFIBER-54   Fiber Cancellation Is Cooperative
AFIBER-55   Running Fiber Cannot Be Force-Freed
AFIBER-56   Fiber Drop Finalizes Initialized Resources
AFIBER-57   Fiber Yield Produces Scheduler-Visible Readiness

ASCHED-51   Scheduler Executes Verified Computation
ASCHED-52   Scheduler Does Not Perform Semantic Type Checking
ASCHED-53   Scheduler Does Not Perform Ownership Verification
ASCHED-54   Worker Owns A Local Ready Queue
ASCHED-55   Work Stealing Requires Migration-Safe Computation
ASCHED-56   Local Computation Preserves Execution Affinity
ASCHED-57   Wake Does Not Create Duplicate Task Identity
ASCHED-58   Wake Must Not Lose A Registered Waiter
ASCHED-59   Scheduler Does Not Require Global State
ASCHED-60   Scheduler Fast Paths Need Not Allocate
ASCHED-61   Task Storage Is Not Semantically Heap-Bound
ASCHED-62   Task Identity Is Distinct From Task Storage
ASCHED-63   JoinHandle Is Not Physical Task Ownership
ASCHED-64   Detached Execution Has Independent Lifetime
ASCHED-65   Structured Concurrency Binds Child Lifetime To Scope
ASCHED-66   Cancellation Does Not Imply Immediate Destruction
ASCHED-67   External Operations Must Release Resource Dependencies Before Destruction
ASCHED-68   Scheduler Shutdown Preserves Resource Lifetime Invariants
ASCHED-69   Runtime Policy Does Not Change Language Semantics
ASCHED-70   Custom Executors Are Permitted

AEXEC-20    Execution Domain Is Distinct From Storage Domain
AEXEC-21    Thread Is An OS Execution Resource
AEXEC-22    Fiber Is A User-Space Execution Context
AEXEC-23    Task Is A Schedulable Computation
AEXEC-24    Future Is A Computation State Machine
AEXEC-25    Execution Resources Are Optional
AEXEC-26    Runtime Is Not Monolithic
AEXEC-27    Runtime Components Are Demand-Driven
AEXEC-28    Thread-Local Storage Is Distinct From Fiber-Local Storage
AEXEC-29    Execution Affinity Is Explicit
AEXEC-30    Runtime Scheduling Does Not Change Ownership Semantics
```

---

# 66. BOOTSTRAP-019 Gate

Trước khi chuyển tiếp:

```text
Fiber context model                 ✓
Fiber stack lifetime                ✓
Context switch                     ✓
Fiber yield                        ✓
Fiber cancellation                 ✓
Thread/Fiber distinction           ✓
Future/Fiber distinction           ✓
Worker model                       ✓
Local queue                        ✓
Work stealing                      ✓
Task migration                     ✓
Wake/waker                         ✓
Timer abstraction                  ✓
I/O readiness boundary             ✓
I/O completion boundary            ✓
Async buffer lifetime              ✓
Structured concurrency             ✓
Detached task                      ✓
JoinHandle                         ✓
Custom executor                    ✓
Runtime-free program               ✓
Freestanding runtime               ✓
TLS/Fiber-local distinction        ✓
Scheduler shutdown                 ✓
```

---

# Kiến trúc thực thi Axiom lúc này

Ta đã có một mô hình khá sạch:

```text
                    AXIOM SOURCE
                          │
                          ▼
                Semantic Verification
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
    Ownership         Capability       Concurrency
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                    VERIFIED MIR
                          │
                          ▼
                    Native Code
                          │
             ┌────────────┼────────────┐
             │            │            │
          Thread        Fiber         Task
             │            │            │
             └────────────┼────────────┘
                          ▼
                      Scheduler
                          │
                 ┌────────┴────────┐
                 │                 │
               CPU/I/O          GPU/Device
```

Điểm đặc biệt là **không có “Axiom Runtime” khổng lồ nằm giữa compiler và chương trình**.

---

## Bước tiếp theo: BOOTSTRAP-020 — Channel + Lock-free Runtime Primitives

Phần tiếp theo nên đi sâu hơn vào tầng runtime thấp nhất:

1. **SPSC ring buffer**
2. **MPSC queue**
3. **MPMC queue**
4. ABA và generation/tagged pointers
5. memory reclamation
6. lock-free vs wait-free
7. cache line / false sharing
8. `Atomic` lowering trên x86-64/AArch64/RISC-V
9. futex/WaitOnAddress/ulock abstraction
10. Mutex fast path / slow path
11. Semaphore
12. scheduler queue
13. channel zero-copy
14. allocator interaction
15. và đặc biệt: **làm thế nào để Axiom đạt hiệu năng gần C/C++ mà không biến source language thành một mớ atomic/lifetime boilerplate**.