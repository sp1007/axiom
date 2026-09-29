Tiếp tục.

# BOOTSTRAP-070 — Axiom Standard Concurrency & Synchronization Library

**Trạng thái: FROZEN**

Đến đây cần chuyển từ **concurrency semantics** đã freeze ở `BOOTSTRAP-039` sang **API/library model cụ thể**.

Mục tiêu không phải tạo một "concurrency runtime khổng lồ", mà là:

> **Axiom Core định nghĩa quy tắc. Library cung cấp công cụ. Runtime chỉ xuất hiện khi công cụ thực sự cần nó.**

---

# 1. Kiến trúc tổng thể

Concurrency của Axiom chia thành 4 lớp:

```text
                    CONCURRENCY
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    Execution        Ownership       Synchronization
        │                │                │
   Thread/Task        Move/Send        Atomic
   Fiber/Async        Share            Mutex
   GPU/Interrupt                       RwLock
                                       Channel
                         │
                         ▼
                    Scheduling
                         │
              ┌──────────┴──────────┐
              │                     │
          OS Threads            Executor
          / Kernel              / Runtime
```

Không có một `ConcurrencyManager` bắt buộc trong executable.

---

# 2. Thread

Thread là library/system abstraction, không phải primitive semantic lớn trong Core.

API conceptually:

```axiom
let thread = Thread.spawn(worker)?
thread.join()?
```

Closure truyền vào phải thỏa:

```text
Send
```

nếu execution có thể chuyển sang thread khác.

---

# 3. Thread không phải ownership

Ví dụ:

```axiom
let data = Vec<i32>()

Thread.spawn(|| {
    use(data)
})
```

semantic là:

```text
data
   │
   └── Move → new execution domain
```

Không copy `Vec`.

Nếu code sau đó vẫn dùng:

```axiom
use(data)
```

thì compiler reject vì ownership đã được chuyển.

---

# 4. `Send`

`Send` nghĩa:

> Một value có thể được chuyển quyền sở hữu sang execution domain khác.

Ví dụ:

```text
Vec<i32>      → Send
String        → Send
Box<T>        → phụ thuộc T
Rc<T>         → không Send
```

Compiler tự derive.

Programmer không được tùy tiện tuyên bố một type là `Send` nếu semantics thực tế không thỏa.

---

# 5. `Share`

`Share` hoàn toàn khác:

```text
Send  = transfer ownership
Share = concurrent shared access
```

Ví dụ:

```text
Arc<T>
```

cho phép shared ownership.

Nhưng:

```text
Arc<MyStruct>
```

**không tự biến `MyStruct` thành mutable thread-safe object.**

---

# 6. `Rc`

`Rc<T>` là shared ownership cho một execution domain không concurrent.

```axiom
let x = Rc.new(data)

let a = x.clone()
let b = x.clone()
```

Không cần atomic reference counting.

Do đó nhẹ hơn `Arc`.

`Rc<T>` mặc định không `Send`.

---

# 7. `Arc`

`Arc<T>` là shared ownership có atomic reference counting.

```axiom
let data = Arc.new(Vec<i32>())
```

Sau đó nhiều execution domain có thể sở hữu `Arc`.

Nhưng vẫn:

```text
Arc<T> ≠ mutable synchronization
```

Muốn mutate:

```axiom
Arc<Mutex<T>>
```

hoặc:

```axiom
Arc<RwLock<T>>
```

hoặc atomic abstraction thích hợp.

---

# 8. Reference counting không phải Core primitive

`Rc`/`Arc` nằm ở library.

Điều này giữ:

```text
Core
    ↓
không có hidden RC

Application
    ↓
chọn RC khi cần
```

Chương trình không dùng `Arc` không phải trả chi phí cho atomic reference counting.

---

# 9. Cycle

`Arc`/`Rc` không tự giải quyết cycle.

Ví dụ:

```text
A → B
↑   ↓
└───┘
```

có thể giữ reference count > 0 mãi mãi.

Library có thể cung cấp:

```text
Weak<T>
```

để phá cycle.

Không đưa cycle collector vào runtime Core.

---

# 10. `Mutex<T>`

`Mutex<T>` cung cấp exclusive synchronized access.

Conceptually:

```axiom
var lock = Mutex.new(data)

let guard = lock.lock()?
```

`guard` sở hữu capability truy cập protected data.

Khi:

```axiom
drop(guard)
```

lock được release.

Thông thường:

```text
MutexGuard<T>
    !Copy
    Drop
```

---

# 11. Guard không phải raw pointer

`MutexGuard<T>` không phải:

```text
*T
```

nó là:

```text
ownership + synchronization capability
```

Compiler biết:

```text
guard live
    ↓
protected access valid
```

và không cho capability vượt lifetime của guard.

---

# 12. `RwLock<T>`

Cho phép:

```text
many readers
OR
one writer
```

API:

```axiom
let r = lock.read()?
let w = lock.write()?
```

Read guard:

```text
can coexist with read guards
```

Write guard:

```text
exclusive
```

Đây chính là `view` / `mut_view` được kết hợp với synchronization.

---

# 13. Capability model của lock

Conceptually:

```text
Mutex<T>
    │
    └── lock()
          │
          ▼
      exclusive capability
          │
          ▼
       mut_view<T>
```

và:

```text
RwLock<T>
    │
    ├── read()
    │     ↓
    │   view<T>
    │
    └── write()
          ↓
       mut_view<T>
```

Compiler không nhất thiết expose conversion này trong syntax; đây là semantic model.

---

# 14. Guard lifetime

Ví dụ:

```axiom
let guard = mutex.lock()?
use(guard)
drop(guard)

other_operation()
```

Sau `drop(guard)`:

```text
protected capability ends
lock released
```

Compiler có thể xác định last-use và release sớm nếu semantics không thay đổi.

---

# 15. Không cho guard qua `await`

Ví dụ:

```axiom
let guard = mutex.lock()?
await something()
```

mặc định:

**reject**.

Lý do:

```text
lock held
   ↓
task suspension
   ↓
executor may run other work
   ↓
deadlock / starvation / incorrect scheduling
```

Nếu cần async lock:

```text
AsyncMutex<T>
AsyncRwLock<T>
```

là abstraction khác.

---

# 16. AsyncMutex

Ví dụ:

```axiom
let guard = mutex.lock_async().await?
```

hoặc API tương đương.

Guard của async mutex được thiết kế riêng để tương thích với async state machine.

Không dùng `MutexGuard` thông thường.

---

# 17. Semaphore

Semaphore quản lý số lượng permits.

```axiom
let permit = semaphore.acquire()?
```

Permit:

```text
!Copy
Drop → release
```

Ví dụ:

```text
Semaphore(4)

task 1 → permit
task 2 → permit
task 3 → permit
task 4 → permit
task 5 → wait
```

Khi một permit được Drop, task khác có thể tiến hành.

---

# 18. Permit là ownership token

Điểm này rất phù hợp với Axiom.

Không coi semaphore như một biến counter mà programmer phải tự tăng/giảm.

Thay vào đó:

```text
Permit
    ↓
ownership token
    ↓
Drop
    ↓
release
```

Compiler bảo đảm permit không bị double release vì nó là `!Copy`.

---

# 19. Condition variable

`Condvar` kết hợp với Mutex.

Pattern:

```text
lock
  ↓
check predicate
  ↓
wait
  ↓
unlock atomically
  ↓
sleep
  ↓
wake
  ↓
reacquire
  ↓
check predicate again
```

Wake không có nghĩa:

```text
predicate == true
```

Do đó API phải khuyến khích loop kiểm tra condition.

---

# 20. Channel

Channel là abstraction ownership-transfer.

```axiom
let (tx, rx) = Channel<i32>.bounded(1024)
```

Send:

```axiom
tx.send(value)?
```

Receive:

```axiom
let value = rx.recv()?
```

---

# 21. Channel send = Move

Nếu:

```axiom
tx.send(buffer)?
```

thì:

```text
buffer
  ↓
Move
  ↓
channel
  ↓
receiver
```

Không copy payload.

Đây là một trong những lợi thế lớn của ownership model.

---

# 22. Failed send

Nếu channel closed/full tùy API:

```axiom
tx.send(value)
```

thất bại thì ownership của `value` phải được trả lại:

```text
send(T)
   ↓ failure
Result<(), T>
```

conceptually.

Không được làm mất value.

---

# 23. Channel không bắt buộc allocation mỗi message

Implementation có thể dùng:

```text
SPSC → ring buffer
MPSC → specialized queue
SPMC → specialized queue
MPMC → concurrent queue
```

Có thể:

- inline storage;
- bounded ring;
- intrusive nodes;
- preallocated pool;
- custom allocator.

Không được thiết kế API bắt buộc:

```text
send()
→ heap allocation
```

---

# 24. Channel ordering

Channel mặc định đảm bảo:

```text
FIFO per sender
```

Không hứa global ordering trong MPSC/MPMC nếu semantics không yêu cầu.

Ví dụ:

```text
Sender A: A1 A2
Sender B: B1 B2
```

receiver có thể thấy:

```text
A1 A2 B1 B2
```

hoặc:

```text
A1 B1 A2 B2
```

nhưng không được đảo:

```text
A2 A1
```

trong stream của A.

---

# 25. Bounded vs unbounded

Nên phân biệt rõ:

```text
Channel.bounded(N)
Channel.unbounded()
```

`bounded` cung cấp backpressure.

`unbounded` có thể cần allocation tùy implementation.

Không nên để:

```text
Channel<T>()
```

có semantics capacity mơ hồ.

---

# 26. Async Channel

Async channel không tạo thread cho mỗi waiting task.

Mô hình:

```text
WAITING
   ↓
channel event
   ↓
READY
   ↓
executor schedules task
```

Scheduler chịu trách nhiệm scheduling.

Channel chỉ cung cấp synchronization/event semantics.

---

# 27. Atomic types

Library cung cấp:

```text
Atomic<bool>
Atomic<i32>
Atomic<i64>
Atomic<u32>
Atomic<u64>
Atomic<usize>
```

và target-supported types.

API:

```axiom
counter.load(Relaxed)
counter.store(value, Release)
counter.fetch_add(1, AcqRel)
```

---

# 28. Atomic không cần `Mutex`

Nếu bài toán phù hợp atomic:

```axiom
Atomic<u64>
```

thì không cần:

```text
Mutex<u64>
```

Compiler/backend có thể tạo instruction trực tiếp.

---

# 29. Atomic reference counting

`Arc` dùng atomic operations nội bộ.

Nhưng programmer không cần nhìn thấy:

```text
fetch_add
fetch_sub
```

trừ khi sử dụng Atomic API trực tiếp.

Abstraction có thể được optimizer inline.

---

# 30. Thread-local storage

Library/system cung cấp:

```text
TLS<T>
```

hoặc attribute:

```text
@tls
```

đã có trong attribute model.

TLS semantics:

```text
one logical instance per thread
```

không phải một global shared object.

---

# 31. Thread creation và closure capture

Ví dụ:

```axiom
let data = Vec<i32>()

Thread.spawn(move || {
    process(data)
})
```

`move` ép closure capture ownership.

Compiler có thể tự suy ra move nếu API yêu cầu ownership transfer, nhưng `move ||` vẫn hữu ích để biểu đạt intent rõ ràng.

---

# 32. Thread return value

Thread có thể trả:

```text
JoinHandle<T>
```

Ví dụ:

```axiom
let handle = Thread.spawn(|| compute())

let result = handle.join()?
```

`JoinHandle<T>` là observation capability.

Nó không phải ownership của thread execution state theo nghĩa programmer có thể tự thao tác arbitrary.

---

# 33. Join

Thread completion:

```text
worker complete
     ↓
Join
     ↓
synchronizes-with
```

Các writes trước thread completion được quan sát theo memory model khi join thành công.

---

# 34. Detached thread

Không nên mặc định detached.

Có:

```text
spawn
join
detach
```

với semantics rõ ràng.

Structured concurrency được ưu tiên.

Detached execution phải explicit vì lifetime của execution domain không còn nằm trong caller's scope.

---

# 35. Structured concurrency

API nên hỗ trợ abstraction kiểu:

```text
scope
 ├── task A
 ├── task B
 └── task C
        ↓
     scope exit
        ↓
   children resolved
```

Mục tiêu:

> child task không vô tình sống lâu hơn resource mà parent sở hữu.

Compiler/library có thể dùng ownership để enforce.

---

# 36. Task

Task khác Thread.

```text
Thread
    = OS/kernel execution resource

Task
    = schedulable unit of async/control-flow execution
```

Một executor có thể chạy:

```text
1000 tasks
```

trên:

```text
4 threads
```

---

# 37. `spawn`

`spawn(future)` yêu cầu future:

```text
Send
```

nếu executor cho phép migration giữa worker threads.

Nếu executor local:

```text
spawn_local(future)
```

không cần Send.

---

# 38. Task migration

Future state có thể:

```text
Worker A
   ↓
suspend
   ↓
Worker B
   ↓
resume
```

Chỉ được nếu state live across await thỏa `Send`.

Compiler kiểm tra:

```text
Future state
   ↓
Send?
```

Không cần programmer annotate lifetime.

---

# 39. Fiber

Fiber là execution abstraction stackful.

Khác Future:

```text
Future
    stackless state machine

Fiber
    stackful execution context
```

Fiber có thể có:

```text
Fiber.spawn(...)
Fiber.yield()
```

nhưng là library/runtime.

---

# 40. Fiber pinning

Fiber có thể bị pin vào execution worker nếu stack/context không thể migrate.

Do đó:

```text
Fiber migration
```

không phải mặc định guarantee.

Compiler/runtime phải biết execution contract.

---

# 41. No forced thread termination

Không hỗ trợ semantic:

```text
kill_thread()
```

theo kiểu cưỡng bức arbitrary.

Vì thread có thể đang giữ:

- lock;
- resource;
- invariant;
- FFI state;
- capability.

Cancellation phải cooperative.

---

# 42. Cancellation

Async task có:

```text
CancellationToken
CancellationHandle
```

hoặc abstraction tương đương.

Cancellation request:

```text
request cancellation
```

không có nghĩa:

```text
task instantly dies
```

Task tự quan sát cancellation point.

---

# 43. Cancellation ≠ Drop

Đặc biệt:

```text
drop(Future)
```

không mặc định có nghĩa:

```text
cancel external I/O
```

Nếu OS/network/GPU operation cần cancellation:

```text
explicit cancellation handle
```

phải được dùng.

---

# 44. Deadlock

Axiom Core không hứa:

> compiler sẽ chứng minh toàn bộ chương trình không deadlock.

Đây là vấn đề algorithm/runtime.

Tooling có thể cung cấp:

- lock-order analysis;
- race detector;
- deadlock detector;
- tracing.

Nhưng chúng không thay đổi language semantics.

---

# 45. Lock ordering

Standard library có thể hỗ trợ:

```text
lock(A)
lock(B)
```

nhưng không bắt buộc compiler hiểu toàn bộ global lock hierarchy.

Nếu sau này thêm static lock-order checking, nó sẽ là tooling/optional contract, không phá Core model.

---

# 46. Fairness

Không đảm bảo:

```text
Mutex
Semaphore
Channel
Scheduler
```

luôn fair.

Fairness là implementation policy.

API chỉ guarantee những gì cần cho correctness.

---

# 47. Spin lock

Có thể có:

```text
SpinLock<T>
```

ở low-level/system library.

Không phải replacement mặc định cho Mutex.

Phù hợp khi critical section cực ngắn và execution environment phù hợp.

---

# 48. Once / Lazy initialization

Nên có:

```text
Once<T>
Lazy<T>
```

library abstractions.

Ví dụ:

```axiom
let config = Lazy.init(|| load_config())
```

Implementation có thể dùng atomic state machine.

Không cần global runtime initializer framework.

---

# 49. Thread-safe initialization

`Once` phải đảm bảo publication semantics.

```text
initialize
    ↓
Release
    ↓
Acquire
    ↓
reader
```

Do đó các reader không thấy partially initialized state.

---

# 50. Concurrent collections

Standard library có thể cung cấp:

```text
ConcurrentQueue<T>
ConcurrentMap<K,V>
ConcurrentSet<T>
```

nhưng chúng không phải Core primitives.

Chúng xây trên:

```text
Atomic
Mutex/RwLock
Channel
Arc
```

và các specialized algorithms.

---

# 51. Lock-free data structures

Axiom phải cho phép viết:

```text
Treiber stack
Michael-Scott queue
ring buffer
RCU
hazard pointer
epoch reclamation
```

nhưng không đưa:

```text
HazardPtr<T>
Epoch<T>
RCU<T>
```

vào language Core.

Chúng là library/system abstractions.

---

# 52. Memory reclamation

Đây là nơi ownership model và concurrent algorithms cần tách biệt.

Một object có thể:

```text
logically removed
```

nhưng chưa thể:

```text
physically reclaimed
```

vì thread khác vẫn có thể đang quan sát.

Do đó:

```text
logical lifetime
≠
resource lifetime
≠
physical memory lifetime
```

đã freeze trước đó tiếp tục rất hữu ích.

---

# 53. Generation Handle

Đối với entity systems:

```text
Handle<T>
```

có thể dùng:

```text
index
generation
```

để tránh stale references.

Ví dụ:

```text
slot 42 generation 7
```

sau delete/reuse:

```text
slot 42 generation 8
```

handle cũ không còn resolve được.

Đây là logical identity, không phải pointer.

---

# 54. Executor

Executor không thuộc Core.

API conceptually:

```text
Executor.run(future)
Executor.spawn(future)
Executor.shutdown()
```

Một executable chỉ dùng async khi link executor cần thiết.

Chương trình sync:

```text
main()
```

không link async runtime.

---

# 55. Executor architecture

Có thể có:

```text
SingleThreadExecutor
ThreadPoolExecutor
WorkStealingExecutor
EmbeddedExecutor
DeterministicExecutor
GPUExecutor
```

Cùng một Future semantics.

Điều này cực kỳ quan trọng:

> **Async language semantics không phụ thuộc scheduler implementation.**

---

# 56. Work stealing

Thread pool có thể:

```text
Worker A
 [T1 T2 T3]

Worker B
 [T4]

Worker C
 [T5 T6]
```

Worker C có thể steal T3.

Nhưng chỉ Future/task thỏa execution migration contract mới được steal.

Compiler không cần biết thuật toán stealing cụ thể.

---

# 57. Runtime components

Runtime được chia:

```text
libaxiom_alloc
libaxiom_panic
libaxiom_thread
libaxiom_async
libaxiom_tls
libaxiom_unicode
...
```

Executable chỉ link thành phần cần thiết.

Ví dụ:

```text
tiny freestanding program
    ↓
no heap
no thread
no async
no panic runtime
```

có thể cực kỳ nhỏ.

---

# 58. Concurrency stack

Mô hình cuối:

```text
Axiom Core
│
├── Ownership
├── Capability
├── Send / Share
├── Memory Model
└── Async semantics
        │
        ▼
Core Library
│
├── Atomic
├── Mutex
├── RwLock
├── Semaphore
├── Condvar
├── Channel
├── Rc
└── Arc
        │
        ▼
Standard Library
│
├── Thread
├── Async IO
├── Executor
├── Task
├── Fiber
└── Cancellation
        │
        ▼
System / Runtime
│
├── OS thread
├── scheduler
├── TLS
├── futex/event
├── IOCP/epoll/kqueue
└── platform primitives
```

---

# Frozen Invariants — `ACLIB-20..100`

### Execution

- **ACLIB-20** Threads are library/system abstractions.
- **ACLIB-21** Tasks are library/runtime scheduling abstractions.
- **ACLIB-22** Futures are compiler-generated control-flow values.
- **ACLIB-23** Fibers are library/runtime execution abstractions.
- **ACLIB-24** Thread execution and task execution are distinct concepts.
- **ACLIB-25** Execution-domain migration is explicit in semantic contracts.
- **ACLIB-26** Scheduler implementation does not redefine language semantics.
- **ACLIB-27** Executor choice does not change Future semantics.

### Ownership

- **ACLIB-28** Thread transfer of owned values is Move.
- **ACLIB-29** Channel transfer of values is Move.
- **ACLIB-30** Send means ownership transfer across execution domains is valid.
- **ACLIB-31** Send does not imply shared access.
- **ACLIB-32** Share does not imply mutable sharing.
- **ACLIB-33** Compiler derives Send/Share properties.
- **ACLIB-34** Programmer cannot unsafely assert false Send/Share semantics.
- **ACLIB-35** `Rc<T>` is non-concurrent shared ownership.
- **ACLIB-36** `Arc<T>` is concurrent shared ownership.
- **ACLIB-37** Arc does not make arbitrary T thread-safe.
- **ACLIB-38** Reference counting is not an implicit language mechanism.
- **ACLIB-39** Reference-count cycles are not automatically collected.

### Locks

- **ACLIB-40** Mutex provides synchronized exclusive access.
- **ACLIB-41** Mutex guard is non-copyable.
- **ACLIB-42** Mutex guard Drop releases the lock.
- **ACLIB-43** Mutex guard cannot outlive the protected storage.
- **ACLIB-44** RwLock permits concurrent read access.
- **ACLIB-45** RwLock write access is exclusive.
- **ACLIB-46** Lock guards establish synchronization capabilities.
- **ACLIB-47** Ordinary lock guards cannot cross await by default.
- **ACLIB-48** Async locks are distinct abstractions.
- **ACLIB-49** Semaphore permits are ownership tokens.
- **ACLIB-50** Dropping a permit releases its permit.
- **ACLIB-51** Permit duplication is forbidden.
- **ACLIB-52** Condvar wake does not imply predicate truth.
- **ACLIB-53** Condition waiting preserves lock semantics.

### Atomics

- **ACLIB-54** Atomic types use the Core memory model.
- **ACLIB-55** Atomic access does not produce ordinary mutable capabilities.
- **ACLIB-56** Atomic ordering is explicit.
- **ACLIB-57** Atomic width support is target-dependent.
- **ACLIB-58** Lock-free status is not implied by atomicity.
- **ACLIB-59** Atomic wait/notify does not itself establish publication.
- **ACLIB-60** Atomic operations cannot be lowered into ordinary memory operations when semantics differ.

### Channels

- **ACLIB-61** Channel send transfers ownership.
- **ACLIB-62** Failed send returns ownership.
- **ACLIB-63** Channel payload transfer does not require copying.
- **ACLIB-64** Channel implementation need not allocate per message.
- **ACLIB-65** Bounded channels provide explicit capacity semantics.
- **ACLIB-66** Unbounded channels have explicit growth semantics.
- **ACLIB-67** Channel ordering is explicitly defined.
- **ACLIB-68** Per-sender FIFO may be guaranteed without global FIFO.
- **ACLIB-69** Async channels do not create one task per wake.
- **ACLIB-70** Channel synchronization follows the Core memory model.

### Async

- **ACLIB-71** `spawn` scheduling is distinct from Future creation.
- **ACLIB-72** Migratable spawned tasks require Send.
- **ACLIB-73** Local tasks need not be Send.
- **ACLIB-74** Future state determines migration safety.
- **ACLIB-75** Cancellation is cooperative.
- **ACLIB-76** Cancellation is distinct from Drop.
- **ACLIB-77** Dropping a Future does not automatically cancel external operations.
- **ACLIB-78** External cancellation requires an explicit cancellation contract.
- **ACLIB-79** Detached execution is explicit.
- **ACLIB-80** Structured concurrency is the preferred high-level model.
- **ACLIB-81** Sync lock guards cannot cross await unless explicitly designed for async execution.
- **ACLIB-82** Async executor is optional.
- **ACLIB-83** Programs not using async need not link async runtime.

### Runtime / performance

- **ACLIB-84** Concurrency abstractions do not imply a monolithic runtime.
- **ACLIB-85** Runtime components are independently linkable.
- **ACLIB-86** Unused concurrency runtime components are omitted.
- **ACLIB-87** Mutex/Channel/Atomic abstractions may be inlined or specialized.
- **ACLIB-88** Library abstractions do not imply heap allocation.
- **ACLIB-89** Library abstractions do not imply dynamic dispatch.
- **ACLIB-90** Library abstractions do not imply object headers.
- **ACLIB-91** Scheduler implementation is replaceable.
- **ACLIB-92** Executor implementation is replaceable.
- **ACLIB-93** OS synchronization primitives are platform implementations.
- **ACLIB-94** Deadlock freedom is not a universal Core guarantee.
- **ACLIB-95** Fairness is not a universal Core guarantee.
- **ACLIB-96** Lock-free/wait-free properties require explicit contracts.
- **ACLIB-97** Concurrent collection algorithms are library abstractions.
- **ACLIB-98** Memory reclamation schemes are library/system abstractions.
- **ACLIB-99** Concurrency libraries preserve Ownership, Capability and Memory Model invariants.
- **ACLIB-100** Concurrency abstraction overhead is not mandatory when semantics and optimization permit erasure.

---

# Một kết luận kiến trúc quan trọng

Sau `BOOTSTRAP-070`, Axiom có một mô hình khá đẹp:

```text
                    VALUE
                      │
                ┌─────┴─────┐
                │           │
              Move        Share
                │           │
              Send          │
                │           ▼
         Execution Domain  Arc
                │           │
                │       ┌───┴────┐
                │       │        │
                │    Mutex    RwLock
                │       │        │
                │       ▼        ▼
                │   mut_view   view
                │
                ▼
             Channel
                │
                ▼
          Ownership Move
```

Và quan trọng nhất:

**không có "concurrency object" đặc biệt trong ngôn ngữ.**

`Mutex`, `Channel`, `Arc`, `Semaphore`, `Executor` đều chỉ là các abstraction được xây trên nền:

```text
Ownership
+
Capability
+
Send/Share
+
Memory Model
+
Async semantics
```

Đây chính là cách giữ Axiom vừa **mạnh ở systems programming**, vừa không biến compiler/runtime thành một hệ thống khổng lồ bắt buộc mọi chương trình phải mang theo.

### Tiếp theo

`BOOTSTRAP-071` nên chốt **Axiom I/O, File, Network, Process, OS Handle và Resource Model**. Đây là phần sẽ giải quyết một vấn đề rất thực tế: làm thế nào `File`, `Socket`, `Process`, `GPU resource`, `OS handle` dùng chung **Move + Drop + Result + async + FFI** mà không cần GC và không làm API trở nên phiền phức.