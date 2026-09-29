# BOOTSTRAP-424 — CONCURRENCY, THREAD, ATOMIC & ASYNC EXECUTION MODEL

Axiom cần một concurrency model **native, ít abstraction bắt buộc, không GC, không runtime scheduler bắt buộc**, nhưng vẫn đủ để xây server, GUI, game, compiler, AI runtime và ứng dụng đa lõi.

Nguyên tắc lớn:

> **Thread là primitive; task/async là abstraction; synchronization là explicit; compiler không biến mọi chương trình thành runtime-managed concurrency.**

---

## 424.1 — Mục tiêu

Axiom phải hỗ trợ đồng thời:

```text
OS threads
atomics
mutex/locks
channels
parallel loops
async I/O
coroutines/tasks
thread pools
structured concurrency
CPU/GPU parallelism
```

nhưng các tầng trên phải **xây được trên tầng thấp hơn**.

Kiến trúc:

```text
Application
    │
    ├── async/task
    ├── parallel
    ├── channels
    └── synchronization
            │
            ▼
       Axiom concurrency
            │
      ┌─────┴─────┐
      ▼           ▼
   Threads      Atomics
      │           │
      └─────┬─────┘
            ▼
        OS / CPU
```

---

# 424.2 — OS Thread là primitive

Thread native là primitive cấp thấp:

```text
thread := spawn(fn)
```

Conceptually:

```text
spawn(function, arguments)
```

tạo một execution context độc lập.

Không yêu cầu runtime VM.

---

# 424.3 — Thread lifecycle

Thread có trạng thái:

```text
Created
Running
Finished
Joined
Detached
```

Không có trạng thái GC-managed.

---

# 424.4 — Spawn

Một thread có thể được tạo:

```text
t := thread.spawn(work)
```

Arguments truyền vào thread phải được xử lý theo ownership semantics.

Ví dụ:

```text
data := create_data()

t := spawn(move data {
    process(data)
})
```

Ownership chuyển sang thread.

---

# 424.5 — Thread entry

Thread entry phải có ABI xác định:

```text
fn() -> void
```

hoặc một callable tương đương.

Runtime wrapper nếu cần phải cực nhỏ.

---

# 424.6 — Join

```text
t.join()
```

đợi thread hoàn thành.

Sau join:

```text
thread result
```

có thể được lấy về nếu API hỗ trợ result.

---

# 424.7 — Detach

```text
t.detach()
```

chuyển lifecycle management sang OS/runtime.

Sau detach, caller không còn quyền join.

Thread tiếp tục chạy độc lập.

---

# 424.8 — Thread ownership

Thread handle là resource.

Do đó:

```text
t := spawn(...)
u := t
```

nếu thread handle là owning type thì mặc định là move, không copy.

Điều này sử dụng trực tiếp BOOTSTRAP-423.

---

# 424.9 — Thread destructor

Axiom **không được âm thầm detach thread khi owner biến mất**, vì đây có thể là bug rất khó phát hiện.

Khuyến nghị:

```text
drop(Thread)
```

yêu cầu thread đã:

```text
joined
detached
```

Nếu chưa:

```text
runtime diagnostic / panic / explicit policy
```

API phải chọn một behavior deterministic.

---

# 424.10 — Thread-local storage

Axiom hỗ trợ:

```text
thread_local<T>
```

Mỗi thread có instance riêng.

Ví dụ:

```text
thread_local counter: i32
```

Không cần mutex cho truy cập local instance.

Compiler có thể map trực tiếp xuống TLS của target ABI.

---

# 424.11 — Atomic types

Core phải có atomic primitive:

```text
AtomicBool
AtomicI8
AtomicI16
AtomicI32
AtomicI64
AtomicU8
AtomicU16
AtomicU32
AtomicU64
AtomicUsize
AtomicIsize
```

Target có thể hỗ trợ thêm:

```text
AtomicPtr
```

---

# 424.12 — Atomic operations

Tối thiểu:

```text
load
store
exchange
compare_exchange
fetch_add
fetch_sub
fetch_and
fetch_or
fetch_xor
```

Operations nào hardware không hỗ trợ trực tiếp thì compiler/runtime có thể lower xuống fallback phù hợp.

---

# 424.13 — Memory ordering

Axiom phải hỗ trợ:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Không nên tạo một memory-ordering model riêng khác CPU/OS vì sẽ làm FFI và optimizer phức tạp.

---

# 424.14 — Default atomic ordering

Default nên là:

```text
SeqCst
```

nếu API cho phép bỏ argument ordering.

Lý do:

- dễ hiểu;
- an toàn hơn cho người mới;
- compiler vẫn có thể tối ưu trong giới hạn semantics.

Code hiệu năng cao có thể explicit:

```text
Relaxed
Acquire
Release
```

---

# 424.15 — Mutex

Primitive:

```text
Mutex<T>
```

hoặc:

```text
mutex.lock()
mutex.unlock()
```

Nhưng nên ưu tiên guard-based API:

```text
with mutex.lock() {
    ...
}
```

để unlock deterministic.

---

# 424.16 — Mutex guard

Conceptual:

```text
guard := mutex.lock()
...
```

`guard` là resource.

Khi scope kết thúc:

```text
drop(guard)
```

→ unlock.

Đây là ứng dụng trực tiếp của deterministic destruction.

---

# 424.17 — Không tự động lock

Axiom không tự động chèn mutex khi programmer truy cập shared memory.

Ví dụ:

```text
counter += 1
```

không biến thành:

```text
lock
read
add
write
unlock
```

Compiler không được tự ý thay đổi concurrency semantics.

---

# 424.18 — RWLock

Hỗ trợ:

```text
RwLock<T>
```

với:

```text
read()
write()
```

Cho phép nhiều reader hoặc một writer.

---

# 424.19 — Semaphore

Primitive:

```text
Semaphore
```

operations:

```text
acquire()
release()
```

Phù hợp:

- resource pools;
- bounded concurrency;
- producer/consumer.

---

# 424.20 — Condition variable

```text
Condition
```

phải hỗ trợ:

```text
wait(mutex)
notify_one()
notify_all()
```

Semantics gần OS primitive để tránh runtime overhead.

---

# 424.21 — Spinlock

Library primitive:

```text
SpinLock
```

dành cho critical sections cực ngắn.

Compiler không tự động thay mutex bằng spinlock.

---

# 424.22 — Channels

Axiom hỗ trợ channel:

```text
Channel<T>
```

Conceptual:

```text
tx.send(value)
rx.receive()
```

Channel có thể:

```text
unbounded
bounded
single-producer
multi-producer
single-consumer
multi-consumer
```

nhưng đây là library implementations, không cần tất cả vào core.

---

# 424.23 — Message passing

Channel cung cấp model:

```text
Thread A
   │
   │ move(value)
   ▼
 Channel
   │
   ▼
Thread B
```

Ownership transfer rất rõ ràng.

Không cần shared mutable memory.

---

# 424.24 — Send capability

Một type có thể được phép transfer giữa threads nếu:

```text
Send
```

Ví dụ:

```text
i32       → Send
String    → Send
Mutex<T>  → Send nếu T phù hợp
```

Raw pointers hoặc resource đặc biệt có thể không `Send`.

---

# 424.25 — Share capability

`Share` biểu thị rằng value có thể được safely shared giữa execution contexts.

Ví dụ conceptually:

```text
Share
```

không đồng nghĩa với:

```text
mutable without synchronization
```

Một object immutable có thể `Share`, trong khi mutable shared state vẫn cần synchronization.

---

# 424.26 — Auto derivation

Compiler có thể tự suy luận:

```text
struct Point {
    x: i32
    y: i32
}
```

→ `Send + Share`.

Nếu field không có capability:

```text
struct X {
    handle: NonShareableHandle
}
```

thì `X` không tự động `Share`.

---

# 424.27 — Data race model

Axiom phải định nghĩa:

> Concurrent unsynchronized conflicting memory access trong safe code là không hợp lệ.

Trong `unsafe`, programmer chịu trách nhiệm.

Compiler không được silently assume race-free nếu semantics không cho phép assumption đó.

---

# 424.28 — Shared mutable state

Có ba con đường:

```text
Atomic<T>
Mutex<T>
unsafe raw memory
```

Không có implicit fourth mechanism.

Ví dụ:

```text
counter.fetch_add(1, Relaxed)
```

hoặc:

```text
mutex.lock()
counter += 1
```

---

# 424.29 — Lock-free

Axiom không yêu cầu mọi atomic type đều lock-free.

Có capability/query:

```text
is_lock_free<T>()
```

để library/compiler quyết định.

---

# 424.30 — Wait-free

Không phải core guarantee.

Wait-free algorithms thuộc library/algorithm layer.

---

# 424.31 — Task abstraction

Task là execution unit **nhẹ hơn OS thread**.

Conceptually:

```text
task.spawn(work)
```

có thể chạy trên:

```text
thread pool
executor
current thread
custom scheduler
```

Task không nhất thiết tương đương thread.

---

# 424.32 — Async không phải thread

Đây là invariant quan trọng:

```text
async function
```

không có nghĩa:

```text
spawn new OS thread
```

Async có thể chạy:

```text
single thread
```

hoặc:

```text
multi-thread executor
```

---

# 424.33 — Async function

Syntax sẽ được khóa ở language syntax task, nhưng semantic:

```text
async fn read(...)
```

tạo một asynchronous computation.

Nó không chạy cho tới khi:

```text
await
```

hoặc được executor schedule.

---

# 424.34 — Future

Async computation được biểu diễn bằng một state object:

```text
Future<T>
```

Conceptually:

```text
Future<T>:
    Pending
    Ready(T)
```

Compiler có thể generate state machine.

---

# 424.35 — Stackless async

Axiom ưu tiên **stackless coroutine/state-machine lowering**.

Ví dụ:

```text
async fn load() {
    a := await read()
    b := await parse(a)
    return b
}
```

Compiler có thể lower thành:

```text
State0
  ↓
read pending
  ↓
State1
  ↓
parse pending
  ↓
State2
  ↓
return
```

Không cần một stack riêng cho mỗi async task.

---

# 424.36 — Zero-cost completed path

Nếu async operation hoàn thành ngay:

```text
await ready_value
```

compiler nên cho phép path:

```text
call
check ready
continue
```

không tạo heap allocation.

---

# 424.37 — Future allocation

Future không được mặc định heap allocate.

Compiler có thể đặt state machine:

```text
stack
```

nếu không escape.

Nếu task được schedule lâu dài:

```text
heap
```

có thể cần.

Escape analysis từ 423 có thể tối ưu trường hợp này.

---

# 424.38 — Executor

Executor là abstraction:

```text
Executor {
    spawn(task)
    run()
    ...
}
```

Không bắt buộc một global executor duy nhất.

Có thể có:

```text
SingleThreadExecutor
ThreadPoolExecutor
IOExecutor
GameExecutor
CustomExecutor
```

---

# 424.39 — Scheduler

Scheduler quyết định:

```text
which task runs
when it runs
on which worker
```

Không thuộc language semantics.

Đây là runtime/library policy.

---

# 424.40 — Async I/O

Axiom không tạo một async I/O abstraction độc lập với OS ở compiler core.

Library có thể map:

```text
Windows IOCP
Linux io_uring/epoll
BSD kqueue
Apple APIs
WASM host async
```

vào cùng `Future` abstraction.

---

# 424.41 — Blocking vs async

API phải phân biệt rõ:

```text
read()
```

và:

```text
async read()
```

Compiler không tự chuyển blocking call thành async.

---

# 424.42 — Cancellation

Future/task phải có cancellation semantics.

Conceptual:

```text
task.cancel()
```

Nhưng cancellation không có nghĩa:

```text
forcefully kill CPU execution
```

Thay vào đó:

```text
cancellation requested
        ↓
task reaches cancellation point
        ↓
cleanup
        ↓
cancelled
```

---

# 424.43 — Cleanup khi cancellation

Nếu task sở hữu resource:

```text
File
MutexGuard
Buffer
Socket
```

cancellation phải chạy cleanup theo BOOTSTRAP-423.

Do đó:

```text
cancel
 ↓
drop locals
 ↓
release resource
```

---

# 424.44 — Structured concurrency

Axiom nên hỗ trợ structured concurrency ở library level.

Concept:

```text
scope {
    spawn task A
    spawn task B
}
```

scope không kết thúc cho tới khi policy hoàn thành:

```text
join
cancel
propagate error
```

Điều này giảm orphan tasks.

---

# 424.45 — Detached task

Detached task vẫn được phép.

Nhưng phải explicit:

```text
detach(task)
```

Không nên có implicit background task.

---

# 424.46 — Error propagation

Task có thể return:

```text
Result<T, E>
```

hoặc panic/error tùy runtime model.

Structured task scope có thể:

```text
propagate first error
cancel siblings
wait cleanup
```

---

# 424.47 — Parallel execution

Axiom phải hỗ trợ parallel loops/library:

```text
parallel for item in data {
    process(item)
}
```

Compiler/runtime có thể lower thành thread pool.

Nhưng đây không phải requirement cho mọi `for`.

Ordinary:

```text
for
```

vẫn sequential.

---

# 424.48 — Work stealing

Thread pool implementation có thể dùng:

```text
work stealing
```

nhưng đây là runtime implementation, không phải language semantic.

---

# 424.49 — Thread pool

Pool:

```text
ThreadPool
```

cho phép:

```text
submit(task)
```

và reuse worker threads.

Không tạo OS thread cho mỗi task.

---

# 424.50 — CPU affinity

API hệ thống có thể hỗ trợ:

```text
thread.set_affinity(cpu_mask)
```

nhưng compiler không tự chọn affinity.

---

# 424.51 — NUMA

Core language không cần NUMA type system.

Runtime/library có thể cung cấp:

```text
numa.allocate(node)
numa.bind(thread, node)
```

nếu target hỗ trợ.

---

# 424.52 — False sharing

Compiler không thể tự giải quyết mọi false sharing.

Axiom type system/layout phải hỗ trợ:

```text
@align(cache_line)
```

hoặc tương đương để programmer/library kiểm soát layout.

---

# 424.53 — GPU/CPU concurrency boundary

GPU execution không nên giả lập bằng OS threads.

Axiom architecture:

```text
CPU
 │
 ├── thread
 ├── task
 └── async
      │
      ▼
   GPU runtime
      │
      ├── kernel
      ├── stream
      └── event
```

GPU model sẽ được thiết kế riêng ở accelerator/GPU task.

---

# 424.54 — Synchronization ABI

Primitive synchronization phải có ABI/library boundary rõ:

```text
Atomic
Mutex
Semaphore
Condition
Thread
```

Compiler intrinsic chỉ được dùng khi cần optimization hoặc target-specific instruction.

---

# 424.55 — Compiler atomics

Compiler IR cần:

```text
AtomicLoad
AtomicStore
AtomicRMW
AtomicCAS
Fence
```

Machine backend map xuống:

```text
x86 LOCK
ARM atomic instructions
WASM atomics
```

hoặc runtime fallback.

---

# 424.56 — Memory fences

IR:

```text
Fence(ordering)
```

cho phép optimizer biết synchronization boundary.

Optimizer **không được reorder memory operations qua fence trái semantics**.

---

# 424.57 — Synchronization and optimizer

Compiler có thể reorder ordinary memory accesses nếu không phá:

```text
single-thread semantics
atomic semantics
happens-before guarantees
```

Đây là requirement bắt buộc.

---

# 424.58 — Atomic visibility

Nếu:

```text
Thread A
x.store(1, Release)

Thread B
x.load(Acquire)
```

và B quan sát giá trị tương ứng, các writes trước Release có thể được observed theo Acquire semantics.

Axiom sử dụng memory model chuẩn thay vì tự phát minh.

---

# 424.59 — Safe shared immutable data

Một immutable value có thể share:

```text
data: Share
```

nhiều thread đọc đồng thời.

Không cần:

```text
Mutex
```

nếu thực sự immutable theo semantics.

---

# 424.60 — Mutable object transfer

Ownership transfer:

```text
Thread A
   │
   │ move(data)
   ▼
Thread B
```

sau transfer, A không được tiếp tục dùng owner.

Đây là điểm mà BOOTSTRAP-423 ownership model trở thành concurrency primitive.

---

# 424.61 — No implicit data cloning

Khi spawn:

```text
spawn(data)
```

Axiom không tự động deep-copy data lớn để tránh race.

Programmer/compiler phải xác định:

```text
move
copy
share
```

---

# 424.62 — Async ownership

Future có thể own captured values:

```text
async fn foo(data: Data) {
    await something()
    use(data)
}
```

State machine phải giữ `data` xuyên qua suspension point.

Compiler phải lower lifetime chính xác.

---

# 424.63 — Async capture

Nếu future escape:

```text
future := foo(data)
```

thì mọi captured owned value phải được chuyển vào future state.

Không được giữ dangling stack references.

---

# 424.64 — Borrow across await

Đây là trường hợp nguy hiểm.

Axiom không yêu cầu Rust-style lifetime machinery toàn hệ thống, nhưng compiler phải reject hoặc require unsafe khi:

```text
borrow stack value
      ↓
await
      ↓
borrow used
```

nếu future có thể suspend và stack owner không còn hợp lệ.

Đây là **async safety rule bắt buộc**, không phải full borrow checker.

---

# 424.65 — Stackful coroutine

Axiom core không yêu cầu stackful coroutine.

Nếu cần:

```text
Fiber
CoroutineStack
```

có thể là library/runtime feature.

Stackless async vẫn là default.

---

# 424.66 — Why stackless default

Stackless state machines:

```text
small
allocatable
movable
cache-friendly
```

và phù hợp với:

```text
async I/O
millions of tasks
```

mà không cần stack lớn cho mỗi task.

---

# 424.67 — Why thread remains available

Async không thay thế thread.

Thread phù hợp:

```text
CPU-heavy work
blocking legacy APIs
OS integration
dedicated workers
real-time-ish workloads
```

Async phù hợp:

```text
I/O-heavy workloads
many concurrent operations
```

Hai model cùng tồn tại.

---

# 424.68 — Blocking inside async

Không cấm compiler-level, nhưng library/runtime có thể diagnostic:

```text
blocking call inside async context
```

nếu API metadata đánh dấu blocking.

Có thể yêu cầu:

```text
spawn_blocking(...)
```

để chuyển operation sang worker pool.

---

# 424.69 — Real-time mode

Axiom phải cho phép runtime không allocation:

```text
no_gc
no_hidden_alloc
no_scheduler
no_exception
```

cho workloads cần deterministic latency.

---

# 424.70 — Freestanding mode

Freestanding program có thể dùng:

```text
atomic
interrupt
spinlock
```

mà không cần OS thread API.

Concurrency primitives được compile trực tiếp xuống CPU.

---

# 424.71 — Embedded mode

Embedded target có thể:

```text
disable OS threads
enable interrupts
enable atomics
```

Scheduler là optional.

---

# 424.72 — No mandatory runtime

Một Axiom program chỉ dùng:

```text
main
integer
struct
loop
```

không cần:

```text
thread runtime
async runtime
GC
scheduler
```

Binary vẫn native tối giản.

---

# 424.73 — Runtime layering

Kiến trúc:

```text
Axiom Core
    │
    ├── atomics
    │
    └── memory ordering
          │
          ▼
Axiom Standard Library
    │
    ├── Thread
    ├── Mutex
    ├── Channel
    ├── Future
    └── Executor
          │
          ▼
Platform Layer
    │
    ├── Windows
    ├── Linux
    ├── macOS
    ├── Android
    ├── iOS
    └── WASM
```

---

# 424.74 — Concurrency syntax principle

Core syntax nên cực nhỏ.

Không cần:

```text
thread keyword
actor keyword
channel keyword
future keyword
lock keyword
```

cho mọi abstraction.

Có thể dùng functions/types:

```text
spawn(...)
Thread
Mutex<T>
Channel<T>
Future<T>
```

và chỉ cần một keyword quan trọng:

```text
async
await
```

---

# 424.75 — `async/await` compiler lowering

Source:

```text
async fn fetch() -> Data {
    a := await read()
    b := await parse(a)
    return b
}
```

IR:

```text
FutureState {
    state
    a
    b
    ...
}

poll():
    switch state {
        0 → start read
        1 → resume after read
        2 → resume after parse
        3 → ready
    }
```

Backend compile thành native machine code.

Không cần interpreter.

---

# 424.76 — Poll interface

Conceptual:

```text
poll(future, context) -> Poll<T>
```

với:

```text
Pending
Ready(value)
```

Executor gọi poll khi có progress.

---

# 424.77 — Waker/event notification

Async I/O cần mechanism:

```text
Pending
   ↓
OS event
   ↓
wake
   ↓
executor schedules future
```

`Waker` là runtime/library abstraction.

---

# 424.78 — Cancellation safety

Một Future bị cancel phải không làm leak:

```text
socket
buffer
file
mutex guard
```

Compiler-generated cleanup + explicit resource ownership xử lý phần này.

---

# 424.79 — Concurrency panic

Nếu thread panic:

```text
Thread A panic
```

thread đó cleanup local owned resources.

Process có tiếp tục hay không tùy runtime policy.

Không mặc định biến thành process-wide crash nếu không cần.

---

# 424.80 — Panic propagation through join

Nếu joined thread failed:

```text
result := t.join()
```

có thể trả:

```text
Success
ThreadError/Panic
```

thay vì silently swallowing failure.

---

# 424.81 — Detached panic

Detached thread không có joiner.

Runtime policy có thể:

```text
log
terminate process
ignore
custom handler
```

Đây là runtime configuration, không phải ownership semantics.

---

# 424.82 — Concurrency error model

Concurrency APIs ưu tiên:

```text
Result<T,E>
Option<T>
Future<T>
```

thay vì exception-based synchronization.

---

# 424.83 — Lock ordering

Compiler không bắt buộc global lock-order analysis.

Library/tooling có thể hỗ trợ annotations:

```text
@lock_rank(10)
```

ở advanced layer.

Core tránh overdesign.

---

# 424.84 — Deadlocks

Deadlock không phải memory safety violation.

Compiler không cần đảm bảo mọi chương trình không deadlock.

Tooling/debugger có thể cung cấp detection/profiling.

---

# 424.85 — Race detector

Không nằm trong production language semantics.

Có thể có compiler mode:

```text
-race
```

instrument memory accesses/locks để dynamic race detection.

Đây là tooling feature.

---

# 424.86 — Thread sanitizer-style mode

Optional instrumentation:

```text
load/store
atomic
lock/unlock
thread creation
join
```

được instrument.

Không ảnh hưởng binary release nếu disabled.

---

# 424.87 — Deterministic testing

Concurrency test framework có thể hỗ trợ scheduler:

```text
deterministic executor
```

để reproduce interleavings.

Đây là testing infrastructure.

---

# 424.88 — Performance requirement

Concurrency primitives phải ưu tiên:

```text
zero abstraction penalty
```

khi compiler có thể inline.

Ví dụ:

```text
AtomicI32.fetch_add
```

có thể compile trực tiếp thành một instruction.

Mutex wrapper có thể inline xuống native primitive.

---

# 424.89 — No mandatory heap allocation

Các primitive:

```text
Atomic
Mutex
Semaphore
SpinLock
Thread handle
```

không được yêu cầu heap allocation chỉ vì được dùng.

Async task/future chỉ allocate khi lifetime/escape cần.

---

# 424.90 — Inline synchronization

Compiler nên inline:

```text
lock()
unlock()
atomic_load()
atomic_store()
```

khi type/API và target cho phép.

---

# 424.91 — Native OS integration

Thread abstraction phải map trực tiếp:

```text
Axiom Thread
      ↓
Windows thread
Linux pthread/clone-like mechanism
Apple thread
WASM worker/host equivalent
```

Implementation có thể thay đổi, semantics giữ ổn định.

---

# 424.92 — ABI interaction

Function passed to thread phải có callable ABI rõ.

Closure:

```text
spawn(|| work())
```

có thể lower thành:

```text
function pointer
+
environment pointer
```

phù hợp ABI từ BOOTSTRAP-421.

---

# 424.93 — Closure ownership

Nếu closure chạy async/thread:

```text
captured values
```

phải được phân loại:

```text
copy
move
share
```

Không được implicit capture raw stack references qua thread boundary.

---

# 424.94 — Thread boundary rule

Một value crossing thread boundary phải thỏa:

```text
Send
```

hoặc được explicitly marked:

```text
unsafe
```

Không có implicit unsafe crossing.

---

# 424.95 — Share boundary rule

Nếu data được share giữa threads:

```text
Share
```

và mutable access phải đi qua synchronization hoặc atomic semantics.

---

# 424.96 — Minimal concurrency core

Cuối cùng core compiler chỉ cần hiểu:

```text
Thread boundary
Atomic
Memory ordering
Async state machine
```

Các thứ như:

```text
ThreadPool
Mutex
Channel
Executor
Scheduler
```

có thể nằm ở standard library/runtime.

Điều này giữ compiler nhỏ nhưng không làm ngôn ngữ nghèo.

---

# 424.97 — Compiler IR requirements

Concurrency IR:

```text
Spawn
Join
AtomicLoad
AtomicStore
AtomicRMW
AtomicCAS
Fence
Suspend
Resume
AsyncCreate
AsyncPoll
AsyncComplete
```

Synchronization abstractions cao hơn lower xuống các primitive này.

---

# 424.98 — Final architecture

```text
                       AXIOM CONCURRENCY
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
          THREAD            ATOMIC            ASYNC
             │                │                │
          spawn/join       ordering          Future
          detach           CAS               await
          TLS              RMW               poll
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                       Synchronization
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
           Mutex            Channel         Executor
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                            OS/CPU
```

---

# 424.99 — Hard invariants

BOOTSTRAP-424 khóa:

1. Thread là native primitive.
2. Thread không phải GC-managed object.
3. Thread ownership dùng model 423.
4. Move được dùng để transfer data sang thread.
5. `Send` biểu diễn khả năng transfer.
6. `Share` biểu diễn khả năng shared access.
7. Shared mutable state phải explicit synchronization/atomic.
8. Atomic memory ordering tuân theo model chuẩn.
9. Mutex/lock không được implicit.
10. Channel là explicit message-passing abstraction.
11. Async không đồng nghĩa với thread.
12. Async mặc định dùng stackless state-machine lowering.
13. Async không bắt buộc heap allocation.
14. Executor/scheduler không thuộc language core.
15. Cancellation phải cleanup resource.
16. Borrow qua suspension point phải được compiler xử lý an toàn hoặc explicit unsafe.
17. Parallelism không được implicit trong ordinary sequential code.
18. Freestanding mode không cần async/thread runtime.
19. Production binary không có concurrency runtime nếu program không dùng.
20. Atomic/lock primitives phải có đường native zero-cost khi target hỗ trợ.

---

# 424.100 — Kết luận

Mô hình concurrency của Axiom cuối cùng là:

```text
             SIMPLE SOURCE
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
    Thread      Atomic     Async
       │          │          │
       │          │       state machine
       │          │          │
       └──────────┼──────────┘
                  ▼
           Native machine code
```

Không có một “Axiom runtime khổng lồ” đứng giữa application và OS.

Đặc biệt, kiến trúc này cho phép cùng một compiler tạo ra:

```text
tiny embedded binary
        │
        ├── native CLI
        ├── high-performance server
        ├── desktop GUI
        ├── game
        ├── compiler
        ├── async server
        └── CPU/GPU compute runtime
```

mà không phải mang theo toàn bộ concurrency infrastructure.

---

# BOOTSTRAP-425 — ERROR HANDLING, PANIC, RESULT, EXCEPTION & FAILURE MODEL

Task kế tiếp sẽ khóa một phần rất quan trọng còn thiếu của Axiom:

```text
425.1   error-handling goals
425.2   Result<T,E>
425.3   Option<T>
425.4   error propagation
425.5   ?
425.6   panic
425.7   abort
425.8   unwind
425.9   exception ABI
425.10  try/catch
425.11  error values
425.12  error interfaces
425.13  typed errors
425.14  error composition
425.15  error conversion
425.16  implicit propagation
425.17  error context
425.18  allocation-free errors
425.19  zero-cost success path
425.20  FFI errors
...
```

Đây sẽ quyết định Axiom có thể vừa **xử lý lỗi sạch như ngôn ngữ hiện đại**, vừa giữ được binary nhỏ và performance gần native hay không.