# BOOTSTRAP-018 — CONCURRENCY CORE

Đây là phần quan trọng nhất để hoàn thiện triết lý:

> **Axiom phải bảo vệ safe code khỏi data race, nhưng không bắt lập trình viên mang theo một hệ thống lifetime/borrow annotation phức tạp.**

Ta giữ nguyên hướng đã chốt: **compiler chứng minh, programmer chỉ biểu đạt semantic intent ở những boundary cần thiết.**

---

# 1. Ba khái niệm phải tách biệt

Axiom không được gom tất cả thành “thread-safe”.

```text
Ownership
    ↓
Ai sở hữu value?

Send
    ↓
Ai được chuyển ownership sang execution domain khác?

Share
    ↓
Ai được đồng thời đọc/chia sẻ?

Synchronization
    ↓
Ai được phép truy cập mutable state đồng thời?
```

Ví dụ:

```text
T
├── Send
└── Share
```

không có nghĩa `T` tự nhiên mutable-safe.

---

# 2. `Send`

`Send` nghĩa:

> Một giá trị có thể chuyển ownership sang execution domain khác.

Ví dụ:

```axiom
let data = Buffer(...);

spawn(move {
    process(data);
});
```

`data` được move:

```text
Thread A
    │
    │ Move
    ▼
Thread B
```

Sau move:

```text
A: Moved
B: Owned
```

Không có hai owner.

---

# 3. `Send` không phải Copy

Rất quan trọng:

```text
Send ≠ Copy
```

Ví dụ một `Buffer` lớn có thể:

```text
!Copy
Send
```

Khi spawn:

```text
ownership descriptor
     ↓ move
new execution domain
```

Không cần copy toàn bộ buffer.

---

# 4. `Share`

`Share` nghĩa là:

> Giá trị có thể tồn tại và được truy cập/chia sẻ giữa nhiều execution domains theo semantic contract của nó.

Ví dụ immutable data:

```axiom
struct Config {
    host: String,
    port: u16,
}
```

Nếu `Config` và các thành phần của nó thỏa Share:

```text
Thread A ─┐
Thread B ─┼── read Config
Thread C ─┘
```

có thể an toàn.

Nhưng:

```text
Share ≠ mutable sharing
```

---

# 5. Vì sao cần cả Send và Share?

Có thể có:

```text
Send = yes
Share = no
```

Ví dụ:

```text
MutexGuard
```

hoặc một loại resource chỉ được chuyển sang thread khác nhưng không được nhiều thread cùng truy cập.

Ngược lại:

```text
Send = no
Share = yes
```

có thể xuất hiện ở những abstraction execution-domain-affine đặc biệt.

Do đó không gộp thành một trait `ThreadSafe`.

---

# 6. Spawn

Semantic model:

```axiom
spawn(move {
    work(data);
});
```

Compiler phân tích closure:

```text
capture(data)
    ↓
MOVE
    ↓
Send check
```

Nếu `data: !Send`:

```text
AX1701
value cannot cross execution domain
```

---

# 7. `spawn_local`

```axiom
spawn_local {
    use(local_state);
}
```

Không yêu cầu Send nếu scheduler đảm bảo task chạy cùng execution domain.

Nhưng ownership/lifetime vẫn phải hợp lệ.

```text
Send check
    ↓
không cần

Ownership check
    ↓
vẫn cần
```

---

# 8. Không có thread-safe marker thủ công

Không bắt programmer viết:

```text
unsafe impl Send for Foo
```

cho các type thông thường.

Compiler có thể derive semantic property:

```text
Foo
 ├── field A: Send
 ├── field B: Send
 └── field C: Send
       ↓
     Foo: Send
```

Nếu type chứa thành phần không Send:

```text
Foo: !Send
```

trừ khi abstraction đặc biệt có compiler-known semantics.

---

# 9. `Share` cũng compiler-derived

Ví dụ:

```text
struct Point {
    x: i32,
    y: i32,
}
```

Compiler có thể suy ra:

```text
Point: Send
Point: Share
```

Không cần runtime metadata.

---

# 10. Mutable sharing

Đây là boundary quan trọng.

Không cho:

```text
Thread A ── mut_view<T> ──┐
                          ├── same T
Thread B ── mut_view<T> ──┘
```

Compiler reject nếu không có synchronization abstraction.

Safe code:

```text
multiple READ
```

hoặc:

```text
one WRITE
```

theo capability model.

---

# 11. Mutex

`Mutex<T>` là library abstraction, nhưng compiler phải hiểu semantic capability của guard.

```axiom
let guard = mutex.lock();

guard.value();
```

Conceptually:

```text
Mutex<T>
    ↓ lock
MutexGuard<T>
    ↓
mut_view<T>
```

---

# 12. Guard là ownership-bearing capability

`MutexGuard<T>`:

```text
!Copy
Drop
```

Move guard:

```axiom
let g2 = g1;
```

có nghĩa:

```text
lock capability
g1 → g2
```

Không tạo thêm lock ownership.

---

# 13. Drop guard = unlock

Khi:

```axiom
{
    let guard = mutex.lock();
    use(guard);
}
```

compiler đảm bảo:

```text
scope exit
    ↓
Drop(guard)
    ↓
unlock
```

Không cần:

```axiom
mutex.unlock();
```

---

# 14. Nhưng unlock không phải memory deallocation

Giống Drop model:

```text
Drop(guard)
```

chỉ hoàn thành resource obligation:

```text
lock ownership released
```

Không có implication về heap.

---

# 15. Mutex không làm `T` trở thành Share

Ví dụ:

```text
Mutex<NonShareType>
```

vẫn có thể là một abstraction Shareable nếu Mutex bảo vệ truy cập đúng cách.

Điểm quan trọng:

```text
Mutex<T>
```

cung cấp **synchronized access**, chứ không biến:

```text
T
```

thành thread-safe type.

---

# 16. Vì vậy

Có thể có:

```text
T: !Share
Mutex<T>: Share
```

vì chỉ guard mới được phép truy cập T.

Đây là một điểm rất mạnh của type-level concurrency.

---

# 17. Read-write lock

```axiom
let guard = rwlock.read();
```

→ read capability.

```text
RwLock<T>
    ↓
ReadGuard<T>
    ↓
view<T>
```

Có thể có:

```text
Reader A
Reader B
Reader C
```

đồng thời.

---

# 18. Write lock

```axiom
let guard = rwlock.write();
```

→ exclusive capability.

```text
RwLock<T>
    ↓
WriteGuard<T>
    ↓
mut_view<T>
```

Không thể đồng thời có:

```text
ReadGuard
```

hoặc:

```text
WriteGuard khác
```

cho cùng protected region.

---

# 19. Capability verifier phải hiểu lock identity

Compiler-internal:

```text
SyncCapability {
    lock_id
    region
    access
    execution_domain
    validity
}
```

Ví dụ:

```text
lock #12
region = T
access = WRITE
```

---

# 20. Vì sao không chỉ dựa vào type checker?

Vì vấn đề là:

```text
MutexGuard<T>
```

chưa đủ để biết:

```text
guard A
guard B
```

cùng bảo vệ object nào.

Compiler cần semantic identity:

```text
LockId
```

và provenance.

---

# 21. Data race

Axiom safe code không được tạo:

```text
WRITE ──┐
        ├── same memory region
WRITE ──┘
```

hoặc:

```text
READ ───┐
        ├── same region
WRITE ──┘
```

nếu không có synchronization contract.

---

# 22. Atomic là abstraction riêng

Không biến:

```text
Atomic<i32>
```

thành:

```text
mut_view<i32>
```

Atomic operation có semantics riêng.

```axiom
counter.fetch_add(1, Ordering::Relaxed);
```

không phải:

```text
load
+
add
+
store
```

theo nghĩa concurrency semantics.

---

# 23. Atomic<T> không phải lock-free guarantee

```text
Atomic<u64>
```

chỉ nói operation có atomic semantics.

Target có thể:

```text
native atomic
```

hoặc:

```text
library/runtime fallback
```

nếu abstraction cho phép.

Nếu cần guarantee lock-free:

```text
LockFreeAtomic<T>
```

có thể là library/target-specific abstraction sau.

---

# 24. Memory ordering

Giữ đủ 5 ordering:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Đây là low-level API.

Không nên làm đơn giản hóa quá mức khiến Axiom không thể viết lock-free algorithms.

---

# 25. Nhưng API cấp cao có thể ẩn ordering

Ví dụ programmer bình thường không nhất thiết phải viết:

```axiom
atomic.store(x, Ordering::Release);
```

mỗi lần.

Library có thể cung cấp:

```axiom
OnceLock<T>
Channel<T>
AtomicFlag
```

với ordering được chọn sẵn.

Như vậy:

```text
Core atomic semantics = mạnh
High-level API = đơn giản
```

---

# 26. CAS

MIR có semantic operation:

```text
ATOMIC_CAS
```

với:

```text
success_order
failure_order
```

Verifier kiểm tra:

```text
failure != Release
failure != AcqRel
success >= failure
```

theo ordering rules.

---

# 27. Weak CAS

Cho phép:

```text
compare_exchange_weak
```

có thể fail dù giá trị vẫn bằng expected.

Do đó API loop pattern:

```axiom
loop {
    let old = atomic.load(...);

    match atomic.compare_exchange_weak(...) {
        Ok(_) => break,
        Err(_) => continue,
    }
}
```

là hợp lệ.

---

# 28. Atomic wait/notify

Nên hỗ trợ abstraction:

```axiom
atomic.wait(value);
atomic.notify_one();
atomic.notify_all();
```

Nhưng:

```text
wait
```

không có nghĩa:

```text
busy spin forever
```

Implementation có thể:

```text
spin
futex
park
kernel wait
```

tùy platform.

---

# 29. `notify` không đảm bảo predicate đúng

Ví dụ:

```axiom
while atomic.load(...) == 0 {
    atomic.wait(0);
}
```

không:

```axiom
if ...
    wait()
```

vì wake chỉ là:

```text
wake opportunity
```

không phải:

```text
predicate guaranteed true
```

---

# 30. Volatile hoàn toàn khác Atomic

Axiom phải giữ:

```text
Atomic
≠
Volatile
```

`volatile` dùng khi machine-level access phải được compiler giữ observable.

Ví dụ:

```text
MMIO
hardware register
device memory
```

Nhưng volatile không cung cấp synchronization.

---

# 31. Atomic + volatile có thể cùng tồn tại?

Ở low-level/system layer, có thể có operation mang cả semantics nếu target/API yêu cầu.

Nhưng compiler phải biểu diễn hai thuộc tính độc lập:

```text
atomic = synchronization semantics
volatile = observability semantics
```

---

# 32. Mutex implementation

Core không cần biết mutex implementation cụ thể.

Có thể:

```text
Mutex<T>
├── futex mutex
├── pthread mutex
├── SRWLock
├── spin mutex
└── adaptive mutex
```

Tất cả đều cung cấp cùng semantic abstraction:

```text
lock capability
```

---

# 33. Fairness

Không đưa fairness vào language semantics.

Không đảm bảo:

```text
FIFO
no starvation
priority fairness
```

đối với Mutex mặc định.

Đó là policy của implementation/library.

Có thể có:

```text
FairMutex
SpinMutex
AdaptiveMutex
```

---

# 34. Poisoning

Axiom **không đưa mutex poisoning vào Core semantics**.

Nếu thread panic:

```text
guard Drop
    ↓
unlock
```

Nếu panic abort:

```text
process ends
```

Nếu unwind:

```text
guard cleanup
```

Không tự động chuyển mutex sang trạng thái “poisoned”.

---

# 35. Condition variable

Model:

```axiom
let guard = mutex.lock();

while !predicate() {
    guard = condition.wait(guard);
}
```

`wait`:

```text
consume guard
    ↓
atomically unlock
    ↓
sleep
    ↓
wake
    ↓
reacquire
    ↓
new guard
```

---

# 36. `wait` không trả lại chính object guard

Semantically:

```text
old guard
    ↓ Move
wait
    ↓
new guard
```

Điều này giúp ownership model rất rõ.

---

# 37. Semaphore

Semaphore:

```axiom
let permit = semaphore.acquire();
```

trả:

```text
Permit
```

`Permit`:

```text
!Copy
Drop
```

Khi Drop:

```text
permit count++
```

---

# 38. Barrier

Barrier:

```axiom
barrier.wait();
```

là synchronization point.

Nhưng barrier không tạo:

```text
ownership transfer
```

nó chỉ đồng bộ execution.

---

# 39. Once

Các abstraction:

```text
Once
OnceLock<T>
Lazy<T>
```

nên nằm ở library/runtime.

Compiler có thể có intrinsic optimization nhưng semantics vẫn là library API.

---

# 40. Scheduler boundary

Scheduler không được làm semantic verifier.

```text
Compiler
   ↓
verified task
   ↓
Scheduler
```

Scheduler chỉ:

```text
READY
WAITING
RUNNING
COMPLETE
```

Không kiểm tra:

```text
ownership
trait
type
alias
```

những việc đó đã hoàn thành trước runtime.

---

# 41. Scheduler state

Conceptual:

```text
Scheduler {
    local_queue
    current_task
    worker
    wake_source
}
```

Không cần global scheduler.

---

# 42. Multi-worker scheduler

Mặc định có thể:

```text
Worker 0
 ├── local queue
 └── steal

Worker 1
 ├── local queue
 └── steal

Worker 2
 ├── local queue
 └── steal
```

Work stealing chỉ áp dụng task:

```text
Send
```

hoặc migration-safe tương ứng.

---

# 43. Local task

Task:

```text
!Send
```

không được steal.

Scheduler giữ:

```text
execution-domain affinity
```

---

# 44. Task metadata

Không nên:

```text
Task = giant object
```

MVP:

```text
Task {
    state
    future
    scheduler_link
    wake_state
}
```

và metadata nhỏ.

---

# 45. Intrusive scheduler structures

Để tránh allocation:

```text
Task
 └── scheduler_link
```

có thể được scheduler đưa trực tiếp vào queue.

Không cần:

```text
QueueNode heap allocation
```

mỗi lần wake.

Điều này phù hợp mục tiêu high-performance.

---

# 46. Wake

State:

```text
WAITING
```

wake:

```text
WAITING → READY
```

Nếu task đã:

```text
READY
```

wake lần nữa không tạo duplicate semantic execution.

Implementation có thể dùng atomic state.

---

# 47. Lost wakeup

Đây là invariant bắt buộc:

```text
register wait
+
check condition
+
transition WAITING
```

phải có synchronization protocol đảm bảo không có:

```text
event happens
    ↓
wake lost
    ↓
task sleeps forever
```

Scheduler/runtime chịu trách nhiệm.

---

# 48. Structured concurrency

Axiom nên ưu tiên:

```text
scope
 ├── task A
 ├── task B
 └── task C
```

scope exit:

```text
join/cancel/resolve children
```

thay vì mặc định detached task.

Detached phải explicit.

---

# 49. JoinHandle

`JoinHandle<T>` là capability quan sát task result.

Không nhất thiết sở hữu physical Task storage.

```text
JoinHandle
    ↓
logical task identity
```

Task có thể được scheduler lưu ở nơi khác.

---

# 50. Detached task

Nếu:

```axiom
spawn_detached(...);
```

thì programmer explicit rằng:

```text
parent scope
    ≠
child lifetime
```

Compiler không được âm thầm giả định child kết thúc cùng parent.

---

# 51. Thread API

Thread là OS execution resource:

```axiom
let handle = Thread.spawn(move {
    work(data);
});
```

`ThreadHandle` nhỏ:

```text
ThreadId
platform_handle
```

Không nhúng:

```text
scheduler
allocator
stack object
```

---

# 52. Thread stack

Stack có:

```text
reserved
committed
```

và policy target-specific.

Axiom source không phụ thuộc:

```text
stack = exactly 8MB
```

trừ khi programmer yêu cầu explicit system contract.

---

# 53. Thread join

```axiom
let result = handle.join();
```

trả:

```text
Result<T, ThreadError>
```

Nếu thread panic:

```text
join()
```

là boundary quan sát panic/error.

Không dùng exception propagation xuyên thread một cách implicit.

---

# 54. Thread spawn không bắt buộc heap allocation

Compiler/runtime có thể:

```text
allocate OS stack
```

vì OS thread inherently cần execution resource.

Nhưng closure capture có thể được đặt:

```text
directly into thread startup context
```

thay vì heap object trung gian.

---

# 55. TLS

Thread-local storage:

```axiom
@tls
static var errno: i32;
```

conceptual lifetime:

```text
program
  └── thread
       └── TLS instance
```

TLS resource Drop theo thread termination nếu target/runtime hỗ trợ deterministic TLS destruction.

---

# 56. Deadlock

Axiom **không hứa deadlock freedom** cho Mutex.

Ví dụ:

```text
Thread A:
lock(A)
lock(B)

Thread B:
lock(B)
lock(A)
```

vẫn có thể deadlock.

Đây là vấn đề algorithm/application.

Compiler không cần biến Core thành theorem prover.

---

# 57. Nhưng tooling có thể hỗ trợ

Sau này có thể có:

```text
@lock_order(A < B)
```

hoặc static analyzer.

Nhưng không đưa vào Core v1.

---

# 58. Lock capability + async

Đây là boundary cực kỳ quan trọng.

Không cho:

```axiom
let guard = mutex.lock();

await something();

use(guard);
```

đối với synchronous guard.

Vì:

```text
guard
 └── holds OS/sync lock
      ↓
task suspended
```

có thể block worker hoặc deadlock.

Compiler:

```text
AX1704
synchronous synchronization guard crosses await
```

---

# 59. Async mutex

Muốn làm:

```axiom
let guard = await mutex.lock_async();
```

phải dùng abstraction khác:

```text
AsyncMutex<T>
```

Guard của nó có semantics phù hợp scheduler.

Không overload:

```text
Mutex
```

thành một loại “tự biết async”.

---

# 60. Execution domain

Axiom nên thống nhất concept:

```text
ExecutionDomain
```

Ví dụ:

```text
CPU
Thread(id)
Fiber(id)
Task(id)
GPU
Device
```

Nhưng không nhất thiết runtime representation giống nhau.

Compiler dùng domain để kiểm tra:

```text
Send
Share
affinity
suspension
migration
```

---

# 61. Storage domain khác execution domain

Cực kỳ quan trọng:

```text
ExecutionDomain
    ≠
StorageDomain
```

Ví dụ:

```text
CPU Thread A
      │
      └── Device Memory
```

hoặc:

```text
Task A
      │
      └── Shared Arena
```

Do đó không dùng một enum duy nhất cho cả hai.

---

# 62. Atomic execution scope

CPU:

```text
thread
process
system
```

GPU có:

```text
lane
warp
workgroup
device
system
```

Không nhét GPU semantics vào CPU atomic Core.

Thay vào đó:

```text
AtomicOrdering
+
ExecutionScope
```

ở GPU/system layer.

---

# 63. Compiler concurrency facts

Semantic Facts Graph bổ sung:

```text
ConcurrencyFact {
    send
    share
    execution_domain
    synchronization
    lock_set
    atomic_access
    migration
}
```

Ownership checker và concurrency verifier phối hợp.

---

# 64. Ví dụ hoàn chỉnh

```axiom
struct Counter {
    value: Atomic<i64>,
}

fn worker(counter: view<Counter>) {
    counter.value.fetch_add(1, Ordering::Relaxed);
}

fn main() {
    let counter = Counter {
        value: Atomic::new(0),
    };

    spawn(worker(view(counter)));
}
```

Compiler phải kiểm tra:

```text
counter
   ↓
view
   ↓
cross execution domain
```

`view<Counter>` phải thỏa domain-sharing contract.

`Atomic` cung cấp concurrent mutation semantics.

Không cần:

```text
Mutex
```

---

# 65. Một ví dụ khác

```axiom
let mutex = Mutex::new(State::new());

spawn(move {
    let guard = mutex.lock();
    guard.update();
});
```

Ở đây:

```text
Mutex
   ↓
shared ownership/synchronization abstraction
   ↓
Guard
   ↓
mut access
```

Không cần biến `State` thành globally mutable.

---

# 66. Channel

Channel nên được coi là:

> **ownership-transfer boundary giữa execution domains.**

Ví dụ:

```axiom
let (tx, rx) = channel::<Buffer>();

spawn(move {
    tx.send(data);
});

let data = rx.recv()?;
```

`data`:

```text
producer ownership
    ↓ Move
channel
    ↓ Move
consumer ownership
```

Không copy payload.

---

# 67. Channel không đồng nghĩa Arc

Đây là điểm phải giữ rất rõ:

```text
Channel<T>
≠
Arc<T>
```

Channel truyền ownership.

Arc chia sẻ ownership.

---

# 68. SPSC optimization

Nếu compiler/library biết:

```text
one producer
one consumer
```

có thể chọn:

```text
lock-free ring buffer
```

và tránh:

```text
mutex
malloc
syscall
```

nhưng semantics Channel vẫn không thay đổi.

---

# 69. MPSC/MPMC

Các specialization:

```text
SPSC
MPSC
SPMC
MPMC
```

có thể cùng API conceptually nhưng implementation khác.

Axiom compiler có thể specialization khi usage đủ rõ.

---

# 70. Zero-copy channel

Nếu:

```text
send(Buffer)
```

thì ideal:

```text
Buffer ownership descriptor
        ↓
queue slot
        ↓
receiver
```

không:

```text
memcpy(buffer bytes)
```

Đây là một trong những lợi thế của ownership model.

---

# 71. Concurrency pipeline hoàn chỉnh

```text
Source
 ↓
Type/Trait
 ↓
Ownership
 ↓
Capability
 ↓
Async analysis
 ↓
Concurrency analysis
 ├── Send
 ├── Share
 ├── migration
 ├── lock capability
 ├── atomic legality
 └── execution domain
 ↓
Verified MIR
 ↓
Optimization
```

Sau bước này:

```text
runtime scheduler
```

chỉ thực thi những gì compiler đã chứng minh.

---

# 72. Diagnostics

Đề xuất:

```text
AX1701 value cannot cross execution domain
AX1702 value is not Send
AX1703 value is not Share
AX1704 synchronous guard crosses await
AX1705 mutable access conflicts with concurrent read
AX1706 mutable accesses conflict
AX1707 synchronization capability is invalid
AX1708 lock belongs to incompatible execution domain
AX1709 atomic operation has invalid memory ordering
AX1710 CAS failure ordering is invalid
AX1711 task migration violates execution-domain contract
AX1712 local task cannot be stolen
AX1713 condition wait requires valid guard
AX1714 permit has escaped semaphore lifetime
AX1715 concurrent access region is not proven safe
```

---

# 73. Invariants

```text
ACONCUR-25   Send Means Ownership Can Cross Execution Domains
ACONCUR-26   Share Means Concurrent Sharing Is Semantically Valid
ACONCUR-27   Send Does Not Imply Share
ACONCUR-28   Share Does Not Imply Mutable Sharing
ACONCUR-29   Ownership Transfer Across Domains Is A Move
ACONCUR-30   Cross-Domain Values Must Satisfy Send
ACONCUR-31   Compiler May Derive Send
ACONCUR-32   Compiler May Derive Share
ACONCUR-33   Safe Mutable Sharing Requires Synchronization
ACONCUR-34   Synchronization Is An Explicit Capability
ACONCUR-35   Mutex Guard Owns A Lock Capability
ACONCUR-36   Mutex Guard Is Not Copyable
ACONCUR-37   Guard Drop Releases Synchronization Capability
ACONCUR-38   Guard-Derived Access Cannot Outlive Guard
ACONCUR-39   Read Guards Permit Concurrent Reads
ACONCUR-40   Write Guards Provide Exclusive Access
ACONCUR-41   Synchronous Guards Cannot Cross Await
ACONCUR-42   Async Synchronization Uses Separate Abstractions
ACONCUR-43   Mutex Does Not Require T To Be Share
ACONCUR-44   Atomic Is Distinct From Ordinary Mutable Access
ACONCUR-45   Atomic Ordering Is Explicit At Low Level
ACONCUR-46   Atomic Is Distinct From Volatile
ACONCUR-47   Atomic Does Not Imply Lock-Free Execution
ACONCUR-48   CAS Ordering Is Verified
ACONCUR-49   Atomic Wait Does Not Imply Busy Waiting
ACONCUR-50   Notification Does Not Establish Predicate Truth
ACONCUR-51   Data Races Are Forbidden In Safe Code
ACONCUR-52   Unknown Overlap Cannot Be Assumed Safe
ACONCUR-53   Synchronization Capability Carries Region Identity
ACONCUR-54   Lock Identity Is Distinct From Type Identity
ACONCUR-55   Condition Wait Consumes And Reestablishes Guard Capability
ACONCUR-56   Semaphore Permit Is An Owning Capability
ACONCUR-57   Permit Drop Releases Permit
ACONCUR-58   Scheduler Executes Verified Tasks
ACONCUR-59   Scheduler Does Not Perform Semantic Verification
ACONCUR-60   Only Migratable Tasks May Be Stolen
ACONCUR-61   Local Tasks Preserve Execution-Domain Affinity
ACONCUR-62   Wake Is Idempotent At Scheduling Semantics
ACONCUR-63   Scheduler Must Prevent Lost Wakeups
ACONCUR-64   Structured Concurrency Is Preferred
ACONCUR-65   Detached Execution Is Explicit
ACONCUR-66   JoinHandle Is An Observation Capability
ACONCUR-67   Thread Is An Execution Resource
ACONCUR-68   ThreadHandle Does Not Own A Scheduler
ACONCUR-69   Thread Stack Is An Execution Resource
ACONCUR-70   Execution Domain Is Distinct From Storage Domain
ACONCUR-71   GPU Execution Scope Does Not Pollute CPU Atomic Semantics
ACONCUR-72   Channel Transfers Ownership
ACONCUR-73   Channel Does Not Imply Shared Ownership
ACONCUR-74   Channel Send Does Not Require Payload Copy
ACONCUR-75   Concurrent Semantics Are Preserved Through Optimization
```

---

# 74. BOOTSTRAP-018 gate

```text
Send derivation                         ✓
Share derivation                       ✓
spawn                                  ✓
spawn_local                            ✓
thread                                  ✓
ThreadHandle                            ✓
Mutex                                   ✓
MutexGuard                              ✓
RwLock                                  ✓
ReadGuard                               ✓
WriteGuard                              ✓
ConditionVariable                       ✓
Semaphore                               ✓
Barrier                                 ✓
Once/OnceLock                            ✓
Atomic                                   ✓
memory ordering                          ✓
CAS                                      ✓
atomic wait/notify                       ✓
volatile distinction                     ✓
scheduler boundary                       ✓
task migration                           ✓
structured concurrency                   ✓
detached execution                       ✓
join                                     ✓
channel ownership transfer               ✓
SPSC/MPSC/MPMC model                     ✓
zero-copy transfer                       ✓
data-race verification                   ✓
async/lock interaction                   ✓
execution/storage domain separation     ✓
```

---

## Điểm quan trọng nhất sau BOOTSTRAP-018

Bây giờ mô hình concurrency của Axiom có thể tóm gọn thành:

```text
                   VALUE
                     │
          ┌──────────┴──────────┐
          │                     │
       OWNERSHIP              SHARING
          │                     │
        Move                 Share
          │                     │
    cross-domain          concurrent read
          │                     │
        Send              Synchronization
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                  Mutex       Atomic      Channel
                    │           │           │
                  Guard       Atomic      Move
                    │           │           │
                mut_view    operation   ownership
```

Đây chính là cách tránh rơi vào hai cực:

```text
C/C++
→ programmer tự chịu quá nhiều concurrency invariants
```

và:

```text
Rust-style
→ programmer phải biểu đạt quá nhiều lifetime/borrow machinery
```

Axiom giữ **proof machinery ở compiler**, còn source code chỉ thể hiện những semantic boundary thực sự cần thiết.

### Bước kế tiếp

Phần semantic concurrency giờ đã khá đầy đủ. Tiếp theo hợp lý là **BOOTSTRAP-019 — Fiber + Scheduler thực thi thật**, trong đó ta sẽ chốt:

- Fiber stack/context
- context switch
- worker scheduler
- work stealing
- task state machine
- timer/wakeup
- I/O readiness
- cancellation
- Thread/Fiber/Task unified execution model
- và quan trọng nhất: **cái gì thuộc Core compiler, cái gì thuộc runtime, cái gì hoàn toàn chỉ là std library**.

Sau đó mới nên đi sâu vào **atomic lock-free algorithms, channels và memory ordering implementation** ở backend/runtime.