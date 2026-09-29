Tiếp tục.

# Axiom — Concurrency, Threading & Parallelism v0.1

Sau khi đã có ownership, `view`, `mut_view`, `Send`, `Share`, atomic và async, ta có thể thiết kế concurrency mà **không cần biến ngôn ngữ thành một framework concurrency khổng lồ**.

Tôi đề xuất nguyên tắc:

> **Core cung cấp semantic primitives để compiler hiểu concurrency; library cung cấp scheduling, thread pool, channel, mutex và structured-concurrency API.**

Như vậy compiler vẫn có đủ thông tin để tối ưu và kiểm tra race, nhưng runtime không bị ép phình to.

---

# 1. Ba tầng concurrency

Axiom nên phân biệt rõ:

```text
                 Concurrency
                     │
        ┌────────────┼────────────┐
        │            │            │
     Parallel      Async        Shared State
        │            │            │
      threads       Future      atomic/lock
```

Chúng không phải ba cách viết khác nhau cho cùng một thứ.

### Parallelism

> nhiều computation chạy đồng thời.

### Async

> computation có thể tạm dừng và tiếp tục.

### Shared state

> nhiều execution context cùng truy cập state.

---

# 2. Thread không phải async

Ví dụ:

```axiom
let t = spawn(|| compute())
```

nghĩa:

> tạo execution context có thể chạy độc lập.

Còn:

```axiom
let f = async { compute().await }
```

nghĩa:

> tạo computation có khả năng suspension.

`async` không đảm bảo tạo thread.

---

# 3. `spawn` nên là library API

Tôi **không khuyến nghị** đưa:

```text
thread
spawn_thread
join_thread
```

thành hàng chục keyword.

Core chỉ cần compiler hiểu semantic operation:

```text
SPAWN
JOIN
SUSPEND
RESUME
```

Library cung cấp API:

```axiom
let handle = thread.spawn(|| work())
let result = handle.join()
```

Compiler lower thành semantic MIR tương ứng.

---

# 4. Nhưng `spawn` phải là compiler-known operation

Đây là điểm cân bằng.

Nếu `spawn()` chỉ là function bình thường:

```axiom
fn spawn<F>(f: F) ...
```

compiler khó biết chính xác closure đã vượt execution boundary.

Do đó trait/API có thể có **intrinsic semantic marker**.

Ví dụ:

```text
@concurrency.spawn
```

không nhất thiết programmer phải nhìn thấy.

Library declaration được compiler nhận diện.

---

# 5. Ownership là cơ chế truyền dữ liệu giữa thread

Ví dụ:

```axiom
var data = Vec<i32>.new()

let h = thread.spawn(move || {
    process(data)
})
```

`data` được move.

Sau đó thread hiện tại:

```text
data → MOVED
```

không thể sử dụng.

Không cần:

```text
'static
Send<'a>
lifetime annotations
```

---

# 6. Đây chính là điểm mạnh của Axiom

Programmer chỉ viết:

```text
move data
```

compiler tự chứng minh:

```text
ownership
lifetime
escape
Send
```

Thay vì programmer phải viết protocol quản lý lifetime.

---

# 7. `Send`

`Send` nghĩa:

> giá trị có thể chuyển ownership sang execution context khác.

Ví dụ:

```text
i32       → Send
Vec<T>    → Send nếu T: Send
File      → có thể Send nếu resource contract cho phép
Mutex<T>  → tùy abstraction
```

---

# 8. `Send` không có nghĩa thread-safe shared access

Đây là invariant cực quan trọng:

```text
Send ≠ Share
```

Ví dụ:

```text
Vec<i32>
```

có thể `Send`.

Nhưng không vì thế mà hai thread được cùng mutate một Vec.

---

# 9. `Share`

`Share` nghĩa:

> có thể cùng tồn tại ở nhiều execution contexts để đọc theo semantic contract.

Ví dụ:

```text
immutable data
Arc<T>
```

nếu `T: Share`.

---

# 10. Vì sao cần cả hai?

Ví dụ:

```text
Arc<Vec<i32>>
```

có thể:

```text
Send
Share
```

nhưng:

```text
Arc<MutableThing>
```

không tự động cho phép:

```text
thread A → write
thread B → write
```

---

# 11. Mutable sharing phải explicit

Ví dụ:

```axiom
let state = Arc.new(Mutex.new(State.new()))
```

sau đó:

```axiom
let guard = state.lock()
guard.update()
```

Compiler biết:

```text
shared ownership
+
synchronization
```

---

# 12. `Arc<T>` không làm T thread-safe

Đây là lỗi thiết kế cần tránh.

Sai:

```text
Arc<T> => T automatically Share
```

Đúng:

```text
Arc<T>
```

chỉ cung cấp shared ownership.

Tính hợp lệ của concurrent access phụ thuộc:

```text
T: Share
```

hoặc:

```text
T protected by synchronization
```

---

# 13. Mutex

`Mutex<T>` cung cấp exclusive access.

Conceptually:

```text
Mutex<T>
    ↓ lock
MutexGuard<T>
    ↓
mut_view<T>
```

Guard:

```text
!Copy
Drop
```

và Drop unlock mutex.

---

# 14. Đây là một abstraction rất đẹp

Thay vì:

```text
lock()
...
unlock()
```

programmer có:

```axiom
{
    let guard = mutex.lock()
    guard.update()
}
```

Scope kết thúc:

```text
guard Drop
    ↓
unlock
```

Không cần runtime GC.

---

# 15. RwLock

Tương tự:

```text
read()  → read guard → view<T>
write() → write guard → mut_view<T>
```

Nhiều read đồng thời.

Chỉ một write.

---

# 16. Compiler không cần biết implementation Mutex

Core chỉ cần biết:

```text
LOCK
UNLOCK
```

và synchronization semantics.

Mutex có thể được implement bằng:

- futex;
- OS mutex;
- spinlock;
- adaptive mutex;
- parking;
- custom lock.

---

# 17. Atomic

Đã chốt:

```axiom
Atomic<T>
```

là semantic type.

Ví dụ:

```axiom
let counter = Atomic<i64>.new(0)

counter.fetch_add(1, Ordering.Relaxed)
```

Không implicit atomicity.

---

# 18. Không có `volatile` thay cho atomic

Giữ nguyên:

```text
volatile != atomic
```

`volatile` dành cho:

- MMIO;
- hardware;
- memory-mapped device;
- special FFI/system cases.

Không dùng để synchronization.

---

# 19. Memory ordering

Đã chốt:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Không có:

```text
atomic_add(x)
```

mà compiler tự chọn ordering.

---

# 20. Channel

Channel nên hoàn toàn là library abstraction.

```axiom
let (tx, rx) = channel<i32>()

thread.spawn(move || {
    tx.send(42)
})

let x = rx.receive()?
```

Ownership rất tự nhiên:

```text
send(value)
```

→ value move sang channel.

---

# 21. Channel không copy mặc định

Nếu:

```axiom
struct BigObject { ... } // !Copy
```

thì:

```axiom
tx.send(object)
```

chuyển ownership.

Không cần:

```text
clone
mutex
shared_ptr
```

trừ khi programmer thực sự muốn chúng.

---

# 22. Channel có thể có nhiều implementation

```text
Channel<T>
├── bounded
├── unbounded
├── SPSC
├── MPSC
├── MPMC
├── synchronous
└── async
```

Tất cả library-level.

Compiler không cần biết implementation cụ thể, chỉ cần biết:

```text
cross-execution transfer
```

để áp dụng `Send`.

---

# 23. `spawn` và borrowed data

Ví dụ:

```axiom
fn foo() {
    var x = 10

    thread.spawn(|| {
        print(x)
    })
}
```

Nếu thread có thể sống lâu hơn `foo`, compiler phải từ chối nếu closure giữ view tới `x`.

Diagnostic:

```text
AX_CONC_0001

task may outlive its captured storage

captured:
    x

owner:
    foo::x

suggestion:
    move x into the task
    or use explicitly shared storage
```

Không cần báo:

```text
borrowed value does not live long enough
```

vì Axiom không muốn programmer học lifetime jargon.

---

# 24. `move` closure

Nếu muốn truyền ownership:

```axiom
thread.spawn(move || {
    process(x)
})
```

Compiler:

```text
x → MOVE
closure owns x
task owns closure
```

Rất rõ.

---

# 25. `spawn` phải yêu cầu Send

Conceptually:

```text
spawn<F>(f: F)
where
    F: Send
```

nhưng compiler có thể hiểu `spawn` trực tiếp.

---

# 26. `spawn_local`

Nếu executor đảm bảo task không rời thread:

```axiom
spawn_local(|| {
    ...
})
```

thì không cần `Send` cho mọi state.

Nhưng vẫn không được tạo dangling view.

---

# 27. Local execution ≠ unsafe

`spawn_local` vẫn phải an toàn.

Ví dụ local task có thể giữ:

```text
view<T>
```

nếu compiler chứng minh owner tồn tại đủ lâu.

Nếu task có thể outlive owner:

```text
ERROR
```

---

# 28. Structured concurrency

Tôi khuyến nghị **library-first**.

Ví dụ:

```axiom
scope(|s| {
    s.spawn(|| task_a())
    s.spawn(|| task_b())
})
```

Semantic:

```text
scope enter
   ├── task A
   └── task B
scope exit
   ↓
join/cancel according to policy
```

---

# 29. Vì sao structured concurrency tốt?

Nó tạo ownership tree:

```text
Scope
 ├── Task A
 │    └── resources
 └── Task B
      └── resources
```

Khi scope kết thúc:

```text
children must be resolved
```

Giảm detached task leak.

---

# 30. Detached task

Vẫn cần.

Ví dụ server/background task:

```axiom
let handle = executor.spawn(...)
handle.detach()
```

Nhưng `detach()` phải **explicit**.

Không tự động detach.

---

# 31. Vì sao?

Nếu:

```axiom
spawn(...)
```

tự động detach:

```text
function ends
task continues
resource graph escapes
```

rất khó reasoning.

Axiom nên ưu tiên:

```text
structured by default
detached by explicit choice
```

---

# 32. Join

```axiom
let handle = thread.spawn(...)
let result = handle.join()?
```

`join` có thể trả:

```text
Result<T, ThreadError>
```

Nếu thread panic:

```text
join → Err(Panic)
```

hoặc một typed failure.

---

# 33. Panic trong thread

Không được để panic phá toàn bộ process mặc định nếu thread model cho phép isolation.

Policy:

```text
panic=abort
```

→ process abort.

```text
panic=unwind
```

→ thread có thể unwind đến thread boundary.

Thread boundary converts:

```text
panic
```

thành:

```text
JoinError::Panic
```

nếu runtime policy cho phép.

---

# 34. Không có exception xuyên thread

Không cho:

```text
throw across thread
```

Panic là control-flow failure, không phải application error.

Application error:

```text
Result<T,E>
```

---

# 35. Cancellation

Thread cancellation không được forcibly interrupt arbitrary code.

Không có:

```text
kill_thread_now()
```

trong safe abstraction.

Thay vào đó:

```text
CancellationToken
```

và cooperative checking.

---

# 36. Async cancellation

Async task có thể:

```text
cancel requested
    ↓
task reaches cancellation point
    ↓
future dropped
    ↓
Drop resources
```

Không cưỡng ép dừng giữa instruction sequence.

---

# 37. Thread cancellation

Thread:

```text
token.cancel()
```

worker:

```axiom
while !token.is_cancelled() {
    work()
}
```

Nếu worker đang syscall/blocking operation:

```text
cancellation behavior
```

phụ thuộc resource/API.

Không compiler magic.

---

# 38. Thread-local storage

TLS nên là compiler/platform primitive, nhưng syntax có thể đơn giản:

```axiom
thread_static var errno: i32 = 0
```

Compiler lower thành:

```text
TLS section / OS TLS mechanism
```

Không cần runtime global.

---

# 39. `thread_static` khác static

```text
static counter
```

→ một storage location toàn process.

```text
thread_static counter
```

→ mỗi thread một storage instance.

---

# 40. Global mutable state

Không cấm tuyệt đối.

Nhưng:

```axiom
static var counter: i32 = 0
```

không tự động thread-safe.

Compiler có thể yêu cầu:

```text
unsafe
```

hoặc synchronization contract tùy semantic model đã chốt.

Tôi nghiêng về:

> **mutable global ordinary memory phải unsafe hoặc được bọc bằng safe synchronization abstraction.**

---

# 41. Parallel loop

Đây là phần nên có API rất đẹp.

Ví dụ:

```axiom
parallel_for(items, |item| {
    process(item)
})
```

Không nhất thiết là keyword.

Compiler/library có thể lower thành:

```text
work partition
→ thread pool
→ join
```

hoặc:

```text
SIMD
```

hoặc:

```text
GPU
```

tùy implementation.

---

# 42. Nhưng compiler cần hiểu parallelism

Nếu chỉ library generic:

```text
parallel_for(...)
```

compiler vẫn có thể inline và optimize.

Nếu library declaration có semantic annotation:

```text
@parallel_boundary
```

compiler biết closure crossing execution boundary.

---

# 43. Parallel loop và ownership

Ví dụ:

```axiom
parallel_for(mut_view(data), |x| {
    *x += 1
})
```

không tự động safe nếu các iteration có thể cùng truy cập vùng nhớ.

Compiler cần chứng minh partition:

```text
iteration 0 → region A
iteration 1 → region B
...
```

và:

```text
A ∩ B = ∅
```

---

# 44. Đây là nơi view model phát huy tác dụng

Axiom không cần:

```text
&mut [T]
```

và lifetime.

Compiler có:

```text
mut_view<T>
region
provenance
access mode
```

→ có thể chứng minh partition.

---

# 45. Nếu compiler không chứng minh được?

Có ba lựa chọn:

### Safe generic fallback

Dùng Mutex/Atomic.

### Sequential fallback

Library có thể chạy tuần tự.

### Explicit unsafe parallel contract

System programmer có thể assert partition.

Ví dụ một compiler contract trong system layer.

---

# 46. Không nên tự động biến unknown thành unsafe

Một chương trình safe nên không mất safety chỉ vì optimizer không đủ thông minh.

Do đó:

```text
cannot prove parallel independence
```

không có nghĩa:

```text
program invalid
```

Mà có thể:

```text
parallel optimization unavailable
```

hoặc API yêu cầu synchronization.

---

# 47. Work stealing

Không phải Core.

Library:

```text
ThreadPool
WorkQueue
WorkStealingPool
Executor
```

Compiler không cần biết algorithm.

---

# 48. Scheduler

Có thể có:

```text
Executor
```

cho async.

Và:

```text
ThreadPool
```

cho CPU parallelism.

Nhưng chúng không nhất thiết là một.

---

# 49. Unified executor?

Về sau có thể:

```text
Executor
├── OS thread
├── async task
├── GPU queue
└── accelerator
```

nhưng Core không cần biết.

---

# 50. Async vs parallel

Ví dụ:

```text
async fn download()
```

có thể chạy trên:

```text
1 thread
```

vẫn async.

Ví dụ:

```text
parallel_for(...)
```

có thể chạy:

```text
8 cores
```

nhưng hoàn toàn synchronous API.

---

# 51. Một API có thể kết hợp

```axiom
async fn process_all(items: view<Item>) -> Result<()> {
    parallel_for(items, |item| {
        process(item)
    })?
}
```

Async điều phối I/O.

Parallel xử lý CPU.

Không trộn hai semantic model.

---

# 52. `await` và lock

Một nguyên tắc tôi khuyến nghị:

> **Không cho `mut_view` hoặc exclusive synchronous lock guard sống qua `await`.**

Ví dụ:

```axiom
let guard = mutex.lock()
await something()
guard.update()
```

→ lỗi.

Lý do:

- giữ mutex trong thời gian suspension;
- có thể deadlock;
- executor thread có thể bị giữ;
- resource capability sống qua suspension.

---

# 53. Read-only capability qua await

Cũng không nên mặc định cho phép.

Chỉ cho phép nếu compiler chứng minh:

```text
owner survives await
region remains valid
no conflicting mutation
future migration satisfies Send/Share
```

Nếu không chứng minh:

```text
error
```

---

# 54. Async state machine

Đã chốt:

```text
async fn
 ↓
state machine
 ↓
Future
```

Chỉ lưu những gì live across await.

Ví dụ:

```axiom
async fn foo() {
    let a = huge_buffer()
    let b = calculate()
    
    await io()

    use(b)
}
```

Nếu `a` không còn được dùng:

```text
a
```

được Drop trước await.

Không nhét vào future state.

---

# 55. Đây là optimization rất quan trọng

Compiler:

```text
live-across-await analysis
```

→ giảm:

- future size;
- heap pressure;
- cache footprint;
- move/copy cost.

---

# 56. Async allocation

Không mặc định heap.

Compiler có thể:

```text
stack
inline
caller storage
arena
heap
```

tùy escape.

Chỉ `spawn` vào executor có thể yêu cầu ownership/storage phù hợp.

---

# 57. Async recursion

```axiom
async fn foo() {
    await foo()
}
```

không thể tạo finite concrete state type trực tiếp.

Cần explicit indirection:

```text
Box<Future>
```

hoặc compiler reject.

Không tự động tạo infinite heap abstraction.

---

# 58. Parallel runtime không bắt buộc

Một chương trình:

```axiom
fn main() {
    ...
}
```

không dùng:

- thread;
- async;
- atomic;
- mutex;

thì binary không link:

```text
thread runtime
async runtime
scheduler
```

---

# 59. Đây là điểm rất phù hợp mục tiêu Axiom

```text
No concurrency used
    ↓
zero concurrency runtime

Atomic used
    ↓
only atomic machine operations

Thread used
    ↓
thread support

Async used
    ↓
async/executor support if needed
```

Capability-driven runtime.

---

# 60. Compiler-level concurrency model

MIR cần semantic instructions:

```text
SPAWN
JOIN
SEND
RECEIVE
LOCK
UNLOCK
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
SUSPEND
RESUME
```

Nhưng sau optimization:

```text
SPAWN
```

có thể trở thành call tới library/runtime.

---

# 61. `SPAWN` không nhất thiết có runtime

Ví dụ compile-time biết:

```text
parallel_for with fixed N
```

có thể specialize thành:

```text
static worker calls
```

hoặc thậm chí sequential nếu target profile yêu cầu.

---

# 62. Memory ordering và happens-before

Axiom memory model phải định nghĩa:

```text
program order
+
atomic synchronization
+
mutex synchronization
+
channel ownership transfer
+
thread join
+
task synchronization
```

tạo thành:

```text
happens-before
```

---

# 63. Ownership transfer cũng là synchronization boundary

Nếu:

```text
thread A
    move x
       ↓
channel
       ↓
thread B
```

thì B nhận ownership sau transfer.

Không cần programmer tự viết memory fence.

Library/channel implementation phải đảm bảo synchronization semantics.

---

# 64. Join cũng là synchronization

```text
thread A
    writes result
       ↓
join
       ↓
thread B
    reads result
```

Sau `join`, B được phép observe kết quả theo thread synchronization semantics.

---

# 65. Mutex cũng vậy

```text
unlock(A)
    ↓
lock(B)
    ↓
B observes synchronized state
```

Không phải mọi memory access đều cần atomic.

---

# 66. Data race

Safe Axiom:

```text
concurrent conflicting ordinary accesses
```

phải bị loại bỏ hoặc synchronization.

Nếu compiler không thể chứng minh safe:

```text
compile error
```

không silently assume race impossible.

---

# 67. Unsafe concurrency

`unsafe` có thể dùng:

- custom lock;
- lock-free queue;
- hazard pointer;
- epoch reclamation;
- intrusive structure;
- custom scheduler.

Nhưng programmer phải đảm bảo invariant.

Compiler vẫn giữ:

- type;
- initialization;
- layout;
- basic control flow;
- ABI;
- representation checks.

---

# 68. Lock-free structures

Không đưa vào Core.

Library/system:

```text
AtomicStack
AtomicQueue
RingBuffer
SPSCQueue
MPMCQueue
```

Compiler chỉ cung cấp atomic primitives.

---

# 69. Memory reclamation

Không đưa:

```text
hazard pointer
epoch GC
RCU
```

vào language semantics.

Chúng là library algorithms.

Điều này giữ Core sạch.

---

# 70. Parallelism taxonomy

Axiom nên có các abstraction:

```text
Thread
Task
Future
Executor
ThreadPool
Channel
Mutex
RwLock
Atomic
Barrier
Semaphore
CancellationToken
Scope
```

Nhưng **tất cả trừ semantic primitive đều library-level**.

---

# 71. Core semantic primitives

Tôi chỉ giữ:

```text
ownership transfer
Send
Share
atomic memory model
suspension
spawn boundary
synchronization boundary
```

Compiler hiểu chúng.

Không biến:

```text
Mutex
Channel
ThreadPool
Executor
```

thành ngôn ngữ primitive.

---

# 72. `Send` và `Share` có thể là auto traits

Tôi đề xuất:

> `Send` và `Share` được compiler tự động suy luận theo cấu trúc type, nhưng programmer có thể cung cấp explicit implementation chỉ trong system/unsafe contexts.

Ví dụ:

```text
struct Packet {
    data: Vec<u8>
}
```

Nếu `Vec<u8>: Send`:

```text
Packet: Send
```

tự động.

---

# 73. Không cần viết

```axiom
impl Send for Packet {}
```

trong trường hợp thông thường.

Compiler tự suy ra.

---

# 74. Negative implementation

Có những type không nên Send.

Ví dụ resource bound to thread:

```text
GpuContext
WindowHandle
ThreadLocalHandle
```

Cần cơ chế:

```text
!Send
```

hoặc intrinsic type property.

Nhưng syntax này nên được thiết kế cùng trait auto-system, chưa cần mở rộng quá nhiều trong v0.1.

---

# 75. `Share` cũng tự suy ra

Ví dụ:

```text
struct Config {
    name: Text
    version: i32
}
```

nếu tất cả field Share:

```text
Config: Share
```

---

# 76. Mutable state

Một type chứa:

```text
mutating interior state
```

không tự nhiên trở thành Share.

Ví dụ:

```text
Cell<T>
```

có thể:

```text
!Share
```

nếu không synchronization.

---

# 77. Atomic interior mutation

```text
Atomic<i64>
```

có thể Share vì semantic operations đã synchronization-safe.

---

# 78. `Arc<Atomic<T>>`

Đây là kiểu rất nhẹ:

```axiom
let counter = Arc.new(Atomic<i64>.new(0))
```

nhiều thread:

```text
counter.load(...)
counter.fetch_add(...)
```

Không cần Mutex.

---

# 79. `Arc<Mutex<T>>`

Dùng khi cần complex mutable state:

```axiom
let state = Arc.new(Mutex.new(State.new()))
```

---

# 80. Không có implicit shared references

Axiom tránh kiểu:

```text
&state
```

để compiler đoán:

```text
shared ownership
```

Muốn shared:

```text
Arc
```

Muốn read capability:

```text
view
```

Muốn mutable exclusive capability:

```text
mut_view
```

Ba semantics khác nhau.

---

# 81. Đây là một điểm rất đẹp trong ngôn ngữ

Ta có:

```text
T
    ownership

view<T>
    temporary read capability

mut_view<T>
    temporary exclusive write capability

Arc<T>
    shared ownership

Atomic<T>
    synchronized shared state

Mutex<T>
    synchronized exclusive access
```

Không cần một hệ thống reference type khổng lồ.

---

# 82. Concurrency invariants

Đóng băng thêm:

```text id="h5t8v1"
ACON-27  Thread Execution Is Not Async Execution
ACON-28  Async Suspension Does Not Imply Thread Creation
ACON-29  Thread Creation Is A Library-Level API
ACON-30  Compiler Understands Execution-Boundary Semantics
ACON-31  Spawn Transfers Owned State
ACON-32  Spawn Requires Send For Migratable Execution
ACON-33  Send Does Not Imply Share
ACON-34  Share Does Not Imply Mutable Sharing
ACON-35  Shared Mutation Requires Synchronization
ACON-36  Arc Provides Shared Ownership, Not Automatic Mutation Safety
ACON-37  Mutex Provides Exclusive Synchronized Access
ACON-38  RwLock Provides Shared-Read/Exclusive-Write Access
ACON-39  Lock Guards Are Resource Types
ACON-40  Lock Guards Are Not Copyable
ACON-41  Drop Releases Lock Guards
ACON-42  Channel Transfer Moves Ownership
ACON-43  Channel Requires Send Across Execution Boundaries
ACON-44  Join Establishes Synchronization
ACON-45  Channel Transfer Establishes Required Synchronization
ACON-46  Synchronization Creates Happens-Before Relations
ACON-47  Safe Code Cannot Contain Data Races
ACON-48  Failure To Prove Parallel Independence Does Not Imply Unsafe
ACON-49  Parallel APIs May Fall Back To Sequential Execution
ACON-50  Structured Concurrency Is Preferred By Library Design
ACON-51  Detached Execution Requires Explicit Choice
ACON-52  Cancellation Is Cooperative
ACON-53  Forced Thread Termination Is Not A Safe Primitive
ACON-54  Mutable Lock Guards Cannot Cross Await
ACON-55  Async State Owns Values Live Across Await
ACON-56  Dead Values Are Released Before Suspension When Possible
ACON-57  Async Allocation Is Not Mandatory
ACON-58  Executor Is Not A Core Runtime Requirement
ACON-59  Thread Pool Is A Library Abstraction
ACON-60  Work Stealing Is A Library Implementation
ACON-61  Channels Are Library Abstractions
ACON-62  Mutex/RwLock Are Library Abstractions
ACON-63  Atomic Memory Semantics Are Core
ACON-64  Lock-Free Algorithms Are Library/System Abstractions
ACON-65  Memory Reclamation Is Not Core
ACON-66  Unsafe May Implement Custom Synchronization
ACON-67  Unsafe Does Not Disable Type And Initialization Verification
ACON-68  Send/Share Are Compiler-Known Semantic Properties
ACON-69  Send/Share Are Automatically Derived Where Sound
ACON-70  Thread-Local Storage Has Explicit Storage Semantics
ACON-71  Mutable Global State Is Not Implicitly Thread-Safe
ACON-72  Concurrency Runtime Components Are Capability-Driven
```

---

# 83. Quyết định quan trọng nhất của phần này

Tôi nghĩ Axiom **không nên có quá nhiều concurrency keyword**.

Surface có thể gần như chỉ cần:

```axiom
thread.spawn(...)
async fn ...
await ...
```

Còn:

```text
Mutex
RwLock
Channel
ThreadPool
Executor
Scope
Barrier
Semaphore
CancellationToken
```

là library.

Nhưng compiler vẫn hiểu semantic boundary thông qua intrinsic/trait contracts.

Đây chính xác là:

> **Compiler Complexity Is Not Language Complexity.**

Compiler có thể làm rất nhiều việc phía sau mà programmer không phải học thêm 30 keyword.

---

# 84. Kiến trúc concurrency hoàn chỉnh

```text
                         Axiom Concurrency
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
          THREAD              ASYNC            SHARED STATE
             │                  │                  │
          spawn              Future             Arc
          join               await              Atomic
          scope              executor           Mutex
             │                  │                RwLock
             └──────────────┬───┴────────────────┘
                            │
                       Ownership
                            │
                    Send / Share
                            │
                     Memory Model
                            │
                      Synchronization
```

Và runtime:

```text
Program
 │
 ├── no concurrency
 │     └── no concurrency runtime
 │
 ├── atomic only
 │     └── atomic machine support
 │
 ├── threads
 │     └── thread support
 │
 ├── async
 │     └── executor only if used
 │
 └── GPU
       └── GPU runtime only if used
```

Đây là mô hình rất phù hợp với mục tiêu **binary nhỏ + hiệu năng cao + không mandatory runtime**.

---

## Tiếp theo: Memory Allocation & Resource Runtime

Bây giờ chúng ta đã đi qua gần toàn bộ semantic surface lớn. Phần tiếp theo tôi muốn khóa sâu vào một thứ còn có ảnh hưởng trực tiếp hơn đến hiệu năng thực tế:

# **Allocator, Heap, Arena, Pool, Stack, Ownership và Memory Fragmentation**

Đặc biệt sẽ giải quyết dứt điểm vấn đề bạn đã nêu từ đầu:

> **“Mô hình bộ nhớ phẳng có hiệu năng cao hơn và tránh phân mảnh không?”**

Ta sẽ thiết kế Axiom sao cho:

```text
Stack
Heap
Arena
Pool
Slab
Static
TLS
External memory
GPU memory
```

đều có thể tồn tại mà **không ép programmer phải mang allocator/lifetime/reference type đi khắp chương trình**.

Và quan trọng nhất: tôi sẽ tách rõ **address-space model**, **storage model**, **allocation strategy** và **fragmentation model**, vì bốn thứ này thường bị trộn lẫn khi thiết kế language.