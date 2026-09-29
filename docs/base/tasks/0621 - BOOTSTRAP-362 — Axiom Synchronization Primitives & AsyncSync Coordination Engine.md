# BOOTSTRAP-362 — Axiom Synchronization Primitives & Async/Sync Coordination Engine

Sau `361`, executor và task model đã có. Bước tiếp theo là đóng băng **cách các task/thread/fiber phối hợp với nhau**.

Mục tiêu của task này:

> Axiom phải có một mô hình synchronization thống nhất cho thread, async task và các execution domain khác, nhưng không biến mọi synchronization primitive thành runtime bắt buộc.

---

## 1. Một mô hình thống nhất

Axiom phân biệt rõ:

```text
Ownership
    → ai sở hữu dữ liệu?

Capability
    → ai được truy cập dữ liệu?

Synchronization
    → khi nào access được phép xảy ra đồng thời?

Execution
    → code đang chạy ở đâu?
```

Do đó:

```text
Arc<T>
```

không tự làm `T` thread-safe.

```text
Mutex<T>
```

không tự tạo ownership chia sẻ.

```text
Atomic<T>
```

không phải lock.

Đây là các semantic primitive khác nhau.

---

# 2. Synchronization primitive taxonomy

Axiom standard library cung cấp:

```text
Atomic
Mutex
RwLock
Semaphore
Condvar
Barrier
Channel
Once
Event
WaitGroup
```

Async layer có:

```text
AsyncMutex
AsyncRwLock
AsyncSemaphore
AsyncEvent
AsyncChannel
```

Không nhất thiết mọi primitive đều nằm trong Core language.

---

# 3. Atomic

`Atomic<T>` là một type riêng.

Ví dụ:

```axiom
let x = Atomic<i32>(0);

x.store(10, Release);
let v = x.load(Acquire);
```

Không được:

```text
Atomic<T> → mut_view<T>
```

một cách trực tiếp.

Atomic access và ordinary memory access là hai semantic access modes khác nhau.

---

# 4. Atomic không phải lock

Atomic:

```text
one memory location
```

Lock:

```text
critical region
```

Ví dụ:

```axiom
counter.fetch_add(1, Relaxed);
```

không tương đương:

```axiom
let g = mutex.lock();
counter += 1;
```

Compiler không được biến đổi hai semantics này thành nhau nếu observable synchronization khác nhau.

---

# 5. Atomicity và ordering tách biệt

Axiom giữ:

```text
Atomicity
Memory Ordering
Visibility
Synchronization
```

là các khái niệm riêng.

Ordering:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Không có `Consume` trong Core v1.

---

# 6. Atomic<T> restrictions

Không phải mọi `T` đều atomic.

Compiler kiểm tra:

```text
AtomicLegal(T, target)
```

dựa trên:

- size;
- alignment;
- target ISA;
- representation;
- lock-free capability nếu API yêu cầu.

Một atomic có thể dùng hidden lock implementation nếu API chỉ yêu cầu atomic semantics.

---

# 7. Lock-free không phải semantic guarantee mặc định

Ví dụ:

```axiom
Atomic<u128>
```

có thể:

```text
hardware lock-free
```

hoặc:

```text
library fallback
```

Nếu programmer yêu cầu:

```axiom
require_lock_free(Atomic<u64>)
```

compiler/target phải chứng minh.

---

# 8. Mutex

Semantic:

```text
Mutex<T>
```

cho phép:

```text
at most one mutable capability
```

Ví dụ:

```axiom
let guard = mutex.lock();

guard.value += 1;
```

`guard` sở hữu capability vào protected region.

---

# 9. MutexGuard

`MutexGuard`:

```text
!Copy
Drop
```

Drop:

```text
unlock
```

Do đó:

```text
lock
 ↓
Guard
 ↓
scope exit
 ↓
Drop Guard
 ↓
unlock
```

hoàn toàn sử dụng `Cleanup Engine`.

Không cần:

```text
finally unlock
```

ở runtime.

---

# 10. Lock poisoning

Axiom **không nên bắt buộc poisoning semantics trong Core synchronization model**.

Nếu một thread panic khi giữ lock:

```text
panic
 ↓
Drop Guard
 ↓
unlock
```

Lock có thể:

```text
remain usable
```

hoặc library abstraction có thể cung cấp poisoned lock.

Poisoning là policy, không phải memory safety requirement.

---

# 11. RwLock

`RwLock<T>` cho:

```text
many readers
one writer
```

Conceptually:

```text
view<T>
```

tương ứng read capability.

```text
mut_view<T>
```

tương ứng write capability.

Compiler vẫn phải kiểm tra capability semantics.

---

# 12. RwLockGuard

Read:

```text
ReadGuard<T>
```

có thể tồn tại đồng thời nhiều bản.

Write:

```text
WriteGuard<T>
```

exclusive.

Cả hai:

```text
!Copy
Drop
```

và release lock khi cleanup.

---

# 13. Async Mutex

Không dùng:

```axiom
Mutex<T>
```

để chờ async.

Ví dụ:

```axiom
let guard = mutex.lock();
await network();
```

bị reject mặc định.

Async abstraction:

```axiom
let guard = await mutex.lock_async();
```

có thể suspend mà không giữ một OS thread blocked.

---

# 14. Async Mutex semantics

Khi lock đang bận:

```text
Task A
   ↓
lock
   ↓
Guard

Task B
   ↓
await lock
   ↓
Pending
```

Khi A unlock:

```text
unlock
 ↓
wake B
```

B không cần polling liên tục.

---

# 15. Async lock fairness

Core không bắt buộc fairness.

Implementation có thể:

```text
FIFO
LIFO
priority
fair
unfair
```

Nhưng nếu API công bố fairness guarantee thì đó là part của API contract.

Compiler không được giả định fairness nếu không được contract xác nhận.

---

# 16. Semaphore

Semaphore quản lý permits.

```axiom
let permit = semaphore.acquire();
```

`Permit`:

```text
!Copy
Drop → release
```

Ví dụ:

```text
Semaphore(4)
```

cho tối đa 4 logical users.

---

# 17. Async Semaphore

```axiom
let permit = await semaphore.acquire_async();
```

Nếu hết permit:

```text
Pending
```

Task được wake khi permit available.

Không block worker thread.

---

# 18. Condvar

Condition variable luôn phải đi với predicate.

Không được:

```axiom
condvar.wait();
use(data);
```

mà phải:

```axiom
while !ready(data) {
    condvar.wait();
}
use(data);
```

Vì wake-up không đảm bảo predicate đúng.

---

# 19. Spurious wakeups

Axiom cho phép implementation có spurious wakeups.

Do đó semantic:

```text
wake ≠ condition true
```

Compiler không được optimize away predicate check chỉ vì `wait()` vừa return.

---

# 20. Async Event

Async event:

```axiom
await event.wait();
```

là Future.

Event state:

```text
NOT_SET
SET
```

nhưng semantics của:

```text
set()
```

phải định nghĩa rõ:

- wake one;
- wake all;
- level-triggered;
- edge-triggered.

Không để API mơ hồ.

---

# 21. Channel

Channel là synchronization + ownership transfer.

```axiom
tx.send(value);
```

nếu thành công:

```text
producer
    ↓ Move
channel
```

receiver:

```axiom
let value = rx.receive();
```

→ ownership transfer:

```text
channel
    ↓ Move
consumer
```

Không copy mặc định.

---

# 22. Channel không cần shared mutable memory

Điều này rất quan trọng.

Thay vì:

```text
Arc<Mutex<Vec<T>>>
```

có thể:

```text
Channel<T>
```

với ownership transfer.

Do đó:

> Message passing có thể giảm nhu cầu shared mutable state.

---

# 23. Channel ordering

Mặc định:

```text
per-sender FIFO
```

Nhưng nhiều sender không có global total ordering.

Ví dụ:

```text
Sender A: A1 A2
Sender B: B1 B2
```

receiver có thể nhận:

```text
A1 B1 A2 B2
```

nhưng không được:

```text
A2 A1
```

nếu cùng sender.

---

# 24. Bounded Channel

```axiom
channel<T>(capacity: 1024)
```

Khi đầy:

```text
send
 ↓
Pending
```

hoặc synchronous API có thể:

```text
blocking
```

tùy abstraction.

Async sender:

```axiom
await tx.send(value);
```

sẽ suspend nếu cần.

---

# 25. Zero-copy send

Ví dụ:

```axiom
let buffer = Buffer(...);

await tx.send(buffer);
```

Sau khi send thành công:

```text
buffer = Moved
```

Consumer nhận ownership.

Không tạo bản copy chỉ để truyền thread.

---

# 26. Failed send

Nếu receiver đã chết:

```text
send
 ↓
Error(value)
```

Axiom nên cho phép trả ownership của `value` về caller.

Ví dụ semantic:

```text
Result<(), SendError<T>>
```

trong đó `SendError<T>` chứa lại `T`.

Điều này rất quan trọng để không làm mất ownership khi channel operation thất bại.

---

# 27. Receive cancellation

Ví dụ:

```axiom
let value = await rx.receive();
```

Future bị cancellation trước khi message đến.

Message không được tự động mất.

Channel vẫn sở hữu message nếu message đã được enqueue.

Đây là separation:

```text
Task cancellation
≠
Channel data cancellation
```

---

# 28. Select

Async library nên hỗ trợ:

```axiom
select {
    x = rx1.receive() => ...
    y = rx2.receive() => ...
}
```

Compiler có thể lower thành state machine.

Nhưng `select` không cần là Core syntax bắt buộc v1.

Có thể là library/comptime abstraction nếu compiler đủ khả năng optimize.

---

# 29. Race

Ví dụ:

```axiom
race {
    a = await request_a()
    b = await request_b()
}
```

Semantics phải định nghĩa:

```text
first completion
```

và các loser task:

```text
cancel
continue
detach
```

phải explicit.

Không được tự ý hủy external operation mà không có cancellation contract.

---

# 30. Barrier

Barrier:

```text
N participants
    ↓
wait
    ↓
all arrived
    ↓
release
```

không transfer ownership.

Nó chỉ synchronization event.

---

# 31. Once

`Once<T>` cung cấp initialization synchronization.

Ví dụ:

```axiom
global CONFIG: Once<Config>;
```

Các thread:

```text
get_or_init(...)
```

phải đảm bảo:

```text
exactly-once initialization
```

và publication của initialized value có proper happens-before.

---

# 32. WaitGroup

Một abstraction đơn giản:

```axiom
let group = WaitGroup();

group.add(3);

spawn(task1);
spawn(task2);
spawn(task3);

await group.wait();
```

Nhưng WaitGroup phải có ownership-safe API để tránh:

```text
add after wait
```

hoặc:

```text
forgotten decrement
```

Compiler không nhất thiết phải chứng minh mọi misuse nếu abstraction runtime quản lý counter.

---

# 33. Happens-before

Axiom memory model đóng băng:

```text
sequenced-before
        +
synchronizes-with
        ↓
happens-before
```

Ví dụ:

```text
Thread A:
write(data)
store(flag, Release)

Thread B:
load(flag, Acquire)
read(data)
```

Nếu Acquire đọc giá trị được publish bởi Release:

```text
write(data)
   HB
read(data)
```

---

# 34. Synchronizes-with sources

Bao gồm:

```text
Release → Acquire atomic
mutex unlock → lock
channel send → receive
thread start
thread completion → join
task completion → await
```

và các primitive có contract tương ứng.

---

# 35. Task completion synchronization

Nếu:

```axiom
let task = spawn(work());
let result = await task;
```

thì completion của task phải synchronize với observation của result.

Không cần programmer tự viết:

```text
fence()
```

---

# 36. Join thread

Thread:

```axiom
let t = thread.spawn(fn() {...});

t.join();
```

Thread completion:

```text
writes in thread
    ↓
join
    ↓
reads after join
```

có happens-before.

---

# 37. Atomics không tự synchronize ordinary access

Ví dụ:

```axiom
atomic.store(1, Relaxed);
```

không tự động tạo Release publication.

Compiler không được giả định:

```text
Relaxed ⇒ visibility ordering
```

---

# 38. Volatile

`volatile` là một semantic khác:

```text
volatile load/store
```

dành cho:

- MMIO;
- hardware registers;
- externally observable memory.

Volatile không phải:

```text
atomic
```

và không phải:

```text
synchronization
```

---

# 39. Compiler fence vs CPU fence

Phân biệt:

```text
compiler_fence()
```

và:

```text
cpu_fence()
```

Compiler fence điều khiển compiler reordering.

CPU fence điều khiển hardware memory ordering.

Không được gộp thành một API mơ hồ.

---

# 40. Data race

Safe Axiom không cho phép data race:

```text
concurrent WRITE
+
concurrent READ/WRITE
+
same memory region
+
no synchronization
```

→ chương trình không hợp lệ về safe semantics.

Nhưng compiler phải chứng minh điều này thông qua:

```text
ownership
capability
Send/Share
synchronization contracts
```

---

# 41. Shared mutable state

Ví dụ:

```axiom
let x = Arc(data);
```

không cho:

```axiom
thread1 → mut_view(x)
thread2 → mut_view(x)
```

nếu không có synchronization.

Phải:

```axiom
Arc<Mutex<T>>
```

hoặc:

```axiom
Arc<Atomic<T>>
```

hoặc abstraction tương đương.

---

# 42. Arc + immutable data

Ngược lại:

```axiom
Arc<Config>
```

có thể được share nếu:

```text
Config: Share
```

và chỉ read.

Không cần lock.

Đây là mô hình:

```text
shared ownership
+
immutable capability
```

---

# 43. Rc vs Arc

`Rc<T>`:

```text
single execution domain
non-atomic reference count
```

`Arc<T>`:

```text
multi-execution-domain
atomic reference count
```

Compiler không tự biến:

```text
Rc<T> → Arc<T>
```

vì semantic/performance khác nhau.

---

# 44. Reference-count cycle

Axiom không hứa GC cycle collection cho:

```text
Arc<A> → Arc<B> → Arc<A>
```

Nếu tạo cycle:

```text
memory leak
```

có thể xảy ra.

Đây là một **resource-management property**, không phải memory-safety violation.

Weak references hoặc arena/owner-tree abstractions dùng khi cần.

---

# 45. Hazard pointers / EBR / RCU

Không đưa vào Core.

Nhưng standard library/runtime có thể cung cấp:

```text
HazardPointer
EpochGuard
RCU
GenerationHandle
```

Chúng phải xây trên ownership/capability/atomic model hiện có.

Không được tạo memory semantics riêng.

---

# 46. Interrupt context

Execution domain:

```text
Interrupt
```

có thể có restrictions:

```text
no blocking
no allocation
limited locks
```

Đây là execution contract.

Ví dụ:

```axiom
@interrupt
fn timer_isr() {
    ...
}
```

Compiler có thể kiểm tra:

```text
MayBlock = false
```

và:

```text
no async await
```

trừ abstraction đặc biệt.

---

# 47. GPU synchronization

Task này cũng thống nhất GPU.

GPU:

```text
Atomic
Barrier
Fence
Event
```

phải mapping vào memory model GPU tương ứng.

Không được coi:

```text
CPU Mutex
```

và:

```text
GPU barrier
```

là cùng implementation.

Nhưng semantic principles vẫn là:

```text
access
ordering
visibility
execution domain
```

---

# 48. Synchronization contract

Mỗi primitive nên có compiler-readable contract:

```text
SyncContract {
    access_modes
    memory_order
    happens_before
    blocking
    async_safe
    execution_domains
    storage_domains
    wake_behavior
    cancellation_behavior
}
```

Compiler dùng contract này cho verification và optimization.

---

# 49. Ví dụ contract

`Mutex.unlock`:

```text
release protected region
synchronizes-with next successful lock
```

`Channel.send`:

```text
ownership transfer
synchronizes-with receive observation
wake waiting receiver
```

`Atomic.load(Acquire)`:

```text
acquire ordering
```

---

# 50. Không cho optimizer phá synchronization

Optimizer có thể loại bỏ synchronization **chỉ nếu chứng minh không observable**.

Ví dụ:

```axiom
let x = Atomic(42);
let y = x.load(Relaxed);
```

nếu `x` không escape:

```text
Atomic semantics
```

có thể được scalarized.

Nhưng:

```text
shared Atomic
```

đã escape sang thread:

→ không được tối ưu thành ordinary load/store.

---

# 51. Synchronization elision

Compiler có thể chứng minh:

```text
Mutex
    ↓
never shared
```

thì có thể eliminate lock nếu semantics không expose lock state hoặc fairness.

Tương tự:

```text
Arc
```

nếu ownership analysis chứng minh single-owner thực tế.

Nhưng chỉ được làm sau semantic verification.

---

# 52. False sharing

Đây là performance issue, không phải semantic issue.

Standard library/compiler có thể hỗ trợ:

```axiom
@cache_align
struct Counter { ... }
```

hoặc:

```text
@align_cache_line
```

nhưng không nên đưa false-sharing prevention vào ownership model.

---

# 53. Synchronization diagnostics

Ví dụ:

```text
error ASYNC-LOCK-001:
synchronous mutex guard is live across await

  21 | let guard = mutex.lock();
     |     ----- guard created here

  22 | await network();
     | ^^^^^^^^^^^^^^^ guard remains live

release the guard before awaiting or use an async-aware mutex
```

Compiler có đủ thông tin để đưa ra diagnostic chính xác vì guard là ownership-bearing value.

---

# 54. CompilerDB additions

Thêm:

```text
SyncDB
AtomicDB
AtomicOrderingDB
MutexDB
RwLockDB
SemaphoreDB
CondvarDB
BarrierDB
ChannelDB
EventDB
OnceDB
WaitGroupDB

SyncContractDB
HappensBeforeDB
SynchronizationEdgeDB
MemoryOrderDB
DataRaceDB
SyncVerificationDB
AsyncSyncDB
GpuSyncDB
```

Các query:

```text
sync_contract(OperationId)
synchronizes_with(OperationA, OperationB)
happens_before(OperationA, OperationB)
atomic_legality(TypeId, TargetId)
lock_guard(LockOperation)
channel_transfer(ChannelOperation)
async_sync_requirements(OperationId)
```

---

# 55. MIR synchronization operations

MIR chuẩn hóa:

```text
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS

LOCK
UNLOCK
WAIT
NOTIFY

CHANNEL_SEND
CHANNEL_RECEIVE

FENCE
COMPILER_FENCE
VOLATILE_LOAD
VOLATILE_STORE
```

Các operation này mang effect metadata:

```text
Read
Write
Atomic
Synchronize
Block
Wake
IO
Foreign
```

---

# 56. Verification invariants

Đóng băng:

```text
ASYNC-LOCK-01
Synchronous lock guards cannot cross await by default.

SYNC-01
Atomic access is distinct from ordinary memory access.

SYNC-02
Atomicity is distinct from memory ordering.

SYNC-03
Relaxed ordering does not imply Acquire/Release semantics.

SYNC-04
Mutex provides exclusive protected access.

SYNC-05
RwLock permits multiple readers or one writer.

SYNC-06
Synchronization guards are ownership-bearing and non-Copy.

SYNC-07
Guard destruction releases the associated synchronization resource.

SYNC-08
Async waiting must not block an ordinary async executor thread.

SYNC-09
Async synchronization uses explicit async-aware primitives.

SYNC-10
Waking a task does not imply immediate execution.

SYNC-11
Wake notification is idempotent.

SYNC-12
Synchronization primitives must prevent lost wakeups under their documented contract.

SYNC-13
Channel send transfers ownership when successful.

SYNC-14
Failed ownership transfer preserves ownership of the value.

SYNC-15
Channel ordering is explicitly defined.

SYNC-16
Cancellation does not implicitly rollback external side effects.

SYNC-17
Task completion synchronizes with valid result observation.

SYNC-18
Thread completion synchronizes with join.

SYNC-19
Volatile is distinct from atomicity and synchronization.

SYNC-20
Compiler fences are distinct from hardware fences.

SYNC-21
Safe programs cannot contain data races.

SYNC-22
Send does not imply Share.

SYNC-23
Share does not imply mutable thread-safe access.

SYNC-24
Arc does not make arbitrary T mutable or thread-safe.

SYNC-25
Rc is not implicitly promotable to Arc.

SYNC-26
Synchronization semantics are execution-domain aware.

SYNC-27
GPU synchronization uses GPU-specific implementations under the same semantic model.

SYNC-28
Synchronization contracts are compiler-readable.

SYNC-29
Optimizer cannot remove observable synchronization without proof.

SYNC-30
Programs not using synchronization primitives do not acquire synchronization runtime dependencies.
```

---

## 57. Kiến trúc concurrency hiện tại

Sau task này, phần concurrency của Axiom đã có cấu trúc khá hoàn chỉnh:

```text
                 CONCURRENCY
                      │
       ┌──────────────┼──────────────┐
       ↓              ↓              ↓
   Ownership      Capability    Synchronization
       │              │              │
     Move        view/mut_view      Atomic
     Send             │             Mutex
     Share            │             RwLock
       │              │             Channel
       └──────────────┼──────────────┘
                      ↓
                Execution Domain
                      │
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
      Thread         Task          GPU
        │             │
      spawn        Future
        │             │
      join         await
                      │
                   Executor
```

Điểm quan trọng nhất là **Axiom không cần một cơ chế “magic concurrency”**. Mọi thứ đều quy về bốn câu hỏi:

```text
Ai sở hữu?
Ai được truy cập?
Truy cập được sắp thứ tự thế nào?
Code đang chạy ở execution domain nào?
```

Đây là nền tảng đủ mạnh để compiler tự chứng minh phần lớn vấn đề concurrency mà không bắt programmer phải viết lifetime, borrow annotation hay synchronization annotation thủ công.