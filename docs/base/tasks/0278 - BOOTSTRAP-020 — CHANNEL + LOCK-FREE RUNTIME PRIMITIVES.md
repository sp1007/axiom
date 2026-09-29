# BOOTSTRAP-020 — CHANNEL + LOCK-FREE RUNTIME PRIMITIVES

Phần này là tầng **runtime implementation**, nhưng nó phải được thiết kế sao cho khớp tuyệt đối với semantic model đã chốt.

Mục tiêu không phải biến Axiom thành “ngôn ngữ lock-free”. Ngược lại:

> **Programmer dùng abstraction cấp cao; runtime dùng lock-free machinery bên dưới khi có lợi; compiler có quyền tối ưu nhưng không được thay đổi concurrency semantics.**

---

# 1. Nguyên tắc kiến trúc

Ta chia thành 3 tầng:

```text
Axiom source
    │
    ▼
High-level concurrency API
    │
    ├── Channel
    ├── Mutex
    ├── RwLock
    ├── Semaphore
    ├── Scheduler
    └── Async I/O
    │
    ▼
Concurrency primitives
    │
    ├── Atomic
    ├── Wait/Notify
    ├── Ring buffer
    ├── Queue
    ├── Parking
    └── Memory reclamation
    │
    ▼
Target / OS
    ├── x86-64
    ├── AArch64
    ├── RISC-V
    └── OS wait primitives
```

Compiler không cần biết Channel là MPMC hay SPSC để type-check source.

Runtime có thể specialization.

---

# 2. Lock-free không phải mục tiêu tuyệt đối

Phải phân biệt:

```text
Lock-free
Wait-free
Obstruction-free
Blocking
```

### Lock-free

Hệ thống tổng thể luôn có ít nhất một thread tiến triển.

### Wait-free

Mỗi operation có upper bound về số bước.

### Obstruction-free

Một thread chạy một mình cuối cùng sẽ hoàn thành.

### Blocking

Có thể ngủ/chờ lock.

Axiom không nên hứa mọi primitive đều lock-free.

---

# 3. API semantics không phụ thuộc implementation

Ví dụ:

```axiom
tx.send(value);
```

có thể được thực hiện bằng:

```text
SPSC ring
```

hoặc:

```text
MPMC queue
```

hoặc:

```text
mutex + queue
```

nhưng semantics:

```text
ownership transfer
```

không thay đổi.

Đây là nguyên tắc:

> **Representation may vary; synchronization semantics may not.**

---

# 4. Channel trước hết là ownership boundary

```axiom
let (tx, rx) = channel::<Buffer>();
```

gửi:

```axiom
tx.send(buffer);
```

là:

```text
Sender
    │
    │ MOVE
    ▼
Channel
    │
    │ MOVE
    ▼
Receiver
```

Không có:

```text
COPY Buffer
```

trừ khi programmer thực sự gọi `clone()`.

---

# 5. Channel slot

Bounded channel:

```text
┌─────┬─────┬─────┬─────┬─────┐
│  T  │  T  │  T  │  T  │  T  │
└─────┴─────┴─────┴─────┴─────┘
  ↑                         ↑
 read                      write
```

Slot có thể chứa:

```text
Initialized<T>
```

hoặc:

```text
Uninitialized
```

Điều này rất quan trọng để tránh khởi tạo toàn bộ buffer.

---

# 6. Ring buffer không cần heap cho từng message

Sai:

```text
send()
  ↓
malloc Node
  ↓
queue
```

MVP bounded channel:

```text
Channel
 ├── ring storage
 ├── producer position
 ├── consumer position
 └── wait state
```

Một message:

```text
slot ownership
```

không phải heap node.

---

# 7. SPSC là trường hợp đặc biệt rất nhanh

Nếu biết:

```text
1 producer
1 consumer
```

có thể dùng:

```text
head
tail
```

và atomic ordering tối thiểu.

Conceptually:

```text
Producer:
    write slot
    publish tail

Consumer:
    observe tail
    read slot
    advance head
```

Không cần CAS trên mỗi operation.

---

# 8. Cache line

Một lỗi rất dễ làm runtime chậm dù algorithm đúng:

```text
Producer writes tail
Consumer writes head
```

Nếu:

```text
head
tail
```

nằm cùng cache line:

```text
CPU0 ⇄ cache line ⇄ CPU1
```

sẽ xảy ra false sharing.

Do đó runtime có thể:

```text
@align(cache_line_size)
```

hoặc target-specific cache padding.

Đây là **performance contract**, không phải semantic requirement của Channel.

---

# 9. `@align` và concurrency

Axiom đã có:

```text
@align(N)
```

Nhưng không nên mặc định mọi atomic/cache-sensitive object đều tự động align cực lớn.

Vì:

```text
memory footprint ↑
cache utilization ↓
```

Chỉ abstraction cần nó mới yêu cầu.

---

# 10. SPSC memory ordering

Không cần:

```text
SeqCst
```

cho mọi operation.

Producer:

```text
write data
    ↓
Release publish
```

Consumer:

```text
Acquire observe
    ↓
read data
```

Như vậy:

```text
data write
    happens-before
data read
```

khi consumer quan sát publication tương ứng.

---

# 11. Channel không dùng Relaxed tùy tiện

Có thể dùng Relaxed cho những counter không mang publication semantics.

Nhưng nếu:

```text
counter
```

đồng thời đại diện cho:

```text
"slot đã chứa dữ liệu hợp lệ"
```

thì ordering phải thể hiện publication.

Đây là lý do compiler/runtime phải phân biệt:

```text
counter
```

với:

```text
synchronization state
```

---

# 12. MPSC

Multiple producers:

```text
Producer A ─┐
Producer B ─┼──> Queue ──> Consumer
Producer C ─┘
```

Bây giờ nhiều writer cùng cập nhật queue position.

Có thể cần:

```text
CAS
```

hoặc algorithm reservation riêng.

Không nhất thiết phải dùng mutex.

---

# 13. FIFO semantics

Axiom nên định nghĩa:

> Mỗi Sender duy trì FIFO order của chính Sender đó.

Ví dụ:

```text
Sender A:
A1
A2
A3
```

receiver không được thấy:

```text
A2
A1
A3
```

nếu tất cả send hoàn thành theo thứ tự đó.

Nhưng giữa nhiều Sender:

```text
A1
B1
A2
B2
```

không có global ordering mặc định.

---

# 14. Vì sao không hứa global ordering?

Nếu hứa:

```text
A1
B1
A2
B2
```

thì runtime phải tạo synchronization point global.

Điều đó:

- giảm scalability;
- tăng contention;
- không cần thiết cho đa số message-passing.

Do đó chỉ giữ ordering thực sự có ý nghĩa.

---

# 15. MPMC

```text
Producer A ─┐
Producer B ─┤
Producer C ─┼──> MPMC Queue
Producer D ─┘          │
                       ├── Consumer 1
                       ├── Consumer 2
                       └── Consumer 3
```

Đây là primitive khó nhất.

MVP không cần tự phát minh algorithm ngay.

Có thể bắt đầu:

```text
bounded MPMC
```

với correctness-first implementation.

Sau đó tối ưu.

---

# 16. Quan trọng: correctness trước lock-free

Axiom compiler/runtime nên có:

```text
Reference Channel
    ↓
Correct
    ↓
Optimized Channel
```

Reference implementation có thể dùng mutex.

Sau đó:

```text
SPSC
MPSC
MPMC
```

được differential test với reference.

---

# 17. Đây là cách giảm rủi ro runtime

Ví dụ:

```text
send(x)
```

reference:

```text
lock
push
unlock
```

optimized:

```text
CAS/ring-buffer
```

Nếu observable behavior giống nhau:

```text
semantic equivalence
```

thì optimization hợp lệ.

---

# 18. Channel close

Channel có hai loại lifetime:

```text
Sender lifetime
Receiver lifetime
```

Nếu:

```text
strong_sender_count == 0
```

thì:

```text
channel → closing
```

Receiver phải:

```text
drain queued messages
```

sau đó:

```text
Closed
```

---

# 19. Send vào channel đã đóng

```axiom
tx.send(value)
```

trả:

```text
Err(SendError::Closed(value))
```

**value phải quay lại caller.**

Đây là điểm cực kỳ hợp với ownership:

```text
caller
   ↓ move
channel
   ↓ channel closed
caller ← ownership restored
```

Không làm mất resource.

---

# 20. Receive

```axiom
rx.recv()
```

có thể:

```text
Ok(value)
Err(Closed)
```

`try_recv()`:

```text
Value
Empty
Closed
```

---

# 21. Empty không giống Closed

```text
Empty
```

nghĩa:

```text
có thể sẽ có message sau
```

Trong khi:

```text
Closed
```

nghĩa:

```text
không còn message nào có thể xuất hiện
```

Đây là semantic distinction bắt buộc.

---

# 22. Async Channel

```axiom
let value = await rx.recv_async();
```

Nếu empty:

```text
RUNNING
   ↓
WAITING_RECEIVE
```

Khi sender gửi:

```text
WAITING_RECEIVE
   ↓
READY
```

Không spawn task mới.

---

# 23. Bounded send

Nếu channel đầy:

```text
WAITING_SEND
```

Sender vẫn giữ ownership của value.

Điều này cực kỳ quan trọng.

Không:

```text
full
 ↓
value disappears
```

---

# 24. Zero-copy `send`

Nếu:

```axiom
tx.send(buffer);
```

và `Buffer` là owning type:

```text
Buffer owner
    ↓ Move
Channel slot
```

Receiver:

```text
Channel slot
    ↓ Move
Buffer owner
```

Payload bytes không cần copy.

---

# 25. `send_with`

Có thể sau này:

```axiom
tx.send_with(|slot| {
    slot.write_header(...);
    slot.write_payload(...);
});
```

Mục tiêu:

```text
construct directly in channel slot
```

tránh:

```text
temporary Buffer
    ↓
copy/move
    ↓
queue
```

Đây là optimization/API nâng cao, không cần Core syntax.

---

# 26. Batch channel

High-throughput workload có thể cần:

```axiom
tx.send_batch(values);
rx.recv_batch(buffer);
```

Giảm:

```text
atomic operations
wakeups
cache transitions
```

Không thay đổi ownership semantics.

---

# 27. Wake strategy

Khi channel chuyển:

```text
EMPTY → NON_EMPTY
```

không nhất thiết wake tất cả.

Thường:

```text
notify_one
```

đủ.

Ngược lại khi channel:

```text
FULL → HAS_SPACE
```

wake một producer phù hợp.

---

# 28. Thundering herd

Không:

```text
one message
 ↓
wake 100 workers
```

vì:

```text
99 workers
→ wake
→ contend
→ sleep again
```

Runtime nên có:

```text
one waiter
```

hoặc controlled batching.

---

# 29. Wait queue

Waiters có thể dùng:

```text
intrusive wait node
```

thay vì:

```text
malloc WaitNode
```

mỗi lần wait.

Conceptual:

```text
Task
 └── WaitLink
       ↓
Channel wait queue
```

---

# 30. Nhưng Task không được free khi đang wait

Invariant:

```text
Task
 ↓ registered waiter
 ↓
cannot reclaim
```

cho tới khi:

```text
unregister
```

hoặc:

```text
wake
```

hoàn tất.

---

# 31. Mutex fast path

Mutex tốt không nên lập tức syscall.

Typical conceptual path:

```text
lock()
 ↓
atomic CAS
 ↓ success
critical section
```

Chỉ khi contention:

```text
CAS fail
 ↓
spin/adaptive
 ↓
park/wait
```

---

# 32. Mutex slow path

```text
fast path
    ↓ fail
spin
    ↓ still fail
enqueue waiter
    ↓
park
```

Unlock:

```text
unlock
 ↓
check waiter
 ↓
wake
```

---

# 33. Adaptive spinning

Trên multi-core:

```text
short contention
```

có thể spin một thời gian.

Nhưng không spin vô hạn.

Policy có thể dựa trên:

- CPU count;
- owner running state;
- contention history;
- platform.

Không đưa policy này vào language semantics.

---

# 34. Futex abstraction

Axiom runtime cần abstraction:

```text
wait_on(address, expected)
wake_one(address)
wake_all(address)
```

Linux có thể map sang futex.

Windows có thể map sang:

```text
WaitOnAddress
WakeByAddress...
```

Darwin có primitive khác.

Nhưng Axiom API không expose OS-specific implementation ở tầng portable.

---

# 35. Wait primitive không phải Mutex

Đừng thiết kế:

```text
futex = mutex
```

Futex chỉ là:

```text
sleep/wake primitive
```

Mutex semantics nằm ở abstraction phía trên.

---

# 36. Semaphore implementation

Fast path:

```text
CAS/decrement
```

nếu permit available.

Nếu:

```text
count == 0
```

thì waiter sleep.

Release:

```text
increment
 ↓
wake waiter
```

---

# 37. Permit ownership

```axiom
let permit = sem.acquire();
```

Compiler biết:

```text
permit: Drop + !Copy
```

Nếu:

```text
return permit;
```

ownership chuyển ra ngoài.

Nếu scope kết thúc:

```text
Drop(permit)
```

release.

---

# 38. Atomic lowering

Đây là nơi backend bắt đầu quan trọng.

Axiom MIR:

```text
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_CAS
ATOMIC_RMW
FENCE
```

↓

Target lowering.

Không nên biến atomic thành:

```text
CALL runtime_atomic(...)
```

nếu CPU hỗ trợ native instruction.

---

# 39. x86-64

Ví dụ:

```text
Atomic load
Atomic store
fetch_add
CAS
```

có thể được lower trực tiếp tùy size/alignment/order.

Compiler không cần expose assembly syntax cho programmer.

---

# 40. AArch64

AArch64 có atomic instruction families khác x86.

Compiler phải translate:

```text
Acquire
Release
AcqRel
SeqCst
```

thành instruction/fence sequence thích hợp.

Source semantics không thay đổi.

---

# 41. RISC-V

RISC-V có:

```text
A extension
```

và memory ordering qua acquire/release bits/fences.

Target feature:

```text
atomic support
```

phải nằm trong target description.

---

# 42. Lock-free width

Ví dụ target có thể hỗ trợ native:

```text
u8
u16
u32
u64
```

nhưng một loại khác có thể cần runtime fallback.

Do đó:

```text
Atomic<u64>
```

không tự động đồng nghĩa:

```text
lock-free
```

như đã chốt.

---

# 43. Lock-free query

Có thể cung cấp compile-time query:

```axiom
comptime {
    atomic_is_lock_free<u64>()
}
```

hoặc:

```text
target.atomic_lock_free(u64)
```

Để library specialization:

```text
if lock_free {
    ...
} else {
    ...
}
```

Không cần runtime branch nếu target đã biết.

---

# 44. Atomic alignment

Atomic:

```text
Atomic<u64>
```

phải được đặt tại alignment hợp lệ.

Nếu:

```text
@repr(packed)
struct X {
    a: Atomic<u64>,
}
```

thì compiler phải reject hoặc yêu cầu unsafe/system contract.

Không silently generate broken atomic access.

---

# 45. Memory order verifier

MIR:

```text
ATOMIC_CAS {
    success = AcqRel
    failure = Acquire
}
```

hợp lệ.

Nhưng:

```text
failure = Release
```

reject.

Verifier chạy trước optimization.

---

# 46. Compiler không được “tối ưu mất” atomic

Ví dụ:

```axiom
counter.fetch_add(1, Relaxed);
counter.fetch_add(1, Relaxed);
```

không được tự động biến thành:

```text
fetch_add(2)
```

nếu observable atomic modification order thay đổi.

Atomic operations là observable concurrency events.

---

# 47. Nhưng compiler có thể optimize xung quanh atomic

Ví dụ computation hoàn toàn độc lập:

```text
a = expensive();
atomic.store(x);
b = other();
```

có thể reorder `a`/`b` nếu không vi phạm:

```text
atomic ordering
memory dependencies
observable behavior
```

---

# 48. SeqCst

`SeqCst` phải được giữ semantics global ordering.

Không cho backend tự ý biến thành Relaxed/Acquire/Release chỉ vì “trông có vẻ đủ”.

Optimization chỉ được weaken nếu compiler chứng minh equivalence theo memory model.

MVP:

> **Không làm aggressive memory-order weakening.**

Đơn giản và an toàn hơn.

---

# 49. Compiler fences

Phân biệt:

```text
compiler_fence
```

và:

```text
fence
```

Compiler fence chủ yếu giới hạn compiler reordering.

Hardware fence ảnh hưởng machine execution ordering.

Không được gộp.

---

# 50. Volatile

MIR:

```text
LOAD {
    volatile = true
}
```

khác:

```text
ATOMIC_LOAD
```

Optimizer:

- không DCE volatile;
- không merge volatile accesses tùy tiện;
- không reorder nếu semantic contract cấm.

Nhưng volatile không tạo happens-before.

---

# 51. Lock-free queue và memory reclamation

Đây là phần khó nhất.

Một node có thể:

```text
Thread A → reading node
Thread B → removes node
Thread B → free(node)
Thread A → dereference
```

→ use-after-free.

Ownership compiler không tự giải quyết được nếu runtime đang dùng raw lock-free structures.

Do đó runtime cần reclamation strategy.

---

# 52. Ba chiến lược chính

```text
Hazard Pointers
Epoch-Based Reclamation
RCU
```

Ngoài ra:

```text
reference counting
tagged generations
object pools
```

tùy cấu trúc.

---

# 53. Hazard pointer

Thread announce:

```text
"I am using node X"
```

Node chỉ được reclaim khi không còn hazard pointer trỏ tới nó.

Ưu:

- precise reclamation.

Nhược:

- overhead;
- bookkeeping;
- cache traffic.

Không đưa vào Core.

---

# 54. Epoch-based reclamation

Threads/tasks tham gia epoch:

```text
Epoch 100
Epoch 101
Epoch 102
```

Node removed ở epoch 100 chỉ reclaim khi mọi participant đã đi qua vùng an toàn.

Ưu:

- fast common path.

Nhược:

- stalled participant có thể trì hoãn reclamation.

---

# 55. RCU

Read path:

```text
very cheap
```

Writer:

```text
update
publish
wait grace period
reclaim
```

Phù hợp:

- read-mostly structures;
- routing tables;
- configuration;
- immutable snapshots.

Có thể trở thành advanced std/runtime library.

---

# 56. Axiom không nên đưa reclamation vào ownership Core

Đây là quyết định quan trọng.

Không thêm:

```text
lifetime<'a>
borrow<'a>
hazard<'a>
epoch<'e>
```

vào source language.

Thay vào đó:

```text
unsafe runtime implementation
```

chịu trách nhiệm chứng minh abstraction.

Public API vẫn safe:

```axiom
map.get(key)
```

Compiler chỉ cần biết abstraction contract.

---

# 57. Unsafe boundary

Ví dụ implementation queue:

```text
unsafe fn dequeue_node(...)
```

có:

```text
/// SAFETY:
/// node remains protected by epoch registration.
```

Compiler không cần verify toàn bộ proof.

Nhưng khi unsafe code trả về:

```text
view<T>
```

thì capability verifier tiếp tục kiểm tra lifetime/provenance của capability được thiết lập.

---

# 58. Runtime primitive nên có reference implementation

Mỗi primitive:

```text
Channel
Mutex
Queue
Semaphore
Scheduler
```

nên có:

```text
reference implementation
optimized implementation
```

Ví dụ:

```text
ChannelRef
    mutex + VecDeque

ChannelFast
    lock-free ring/queue
```

Tests:

```text
same semantic test suite
```

---

# 59. Stress testing

Concurrency không thể chỉ test:

```text
1 + 1 = 2
```

Cần:

```text
stress
random scheduling
forced yield
random delays
many workers
many producers
many consumers
shutdown races
cancellation races
```

---

# 60. Deterministic scheduler

Axiom nên có:

```text
DeterministicScheduler
```

cho test.

Ví dụ:

```text
Task A
Task B
Task C
```

scheduler có thể cố ý chạy:

```text
A
B
A
C
B
A
...
```

theo seed.

Nhờ đó race logic có thể reproducible.

---

# 61. Concurrency fuzzing

Harness:

```text
axiom0 fuzz --concurrency
```

có thể random:

```text
yield
wake
steal
send
recv
cancel
lock
unlock
```

và record:

```text
seed
schedule
target
optimization level
```

Nếu crash:

```text
replay(seed)
```

---

# 62. Optimization differential

Một test phải chạy:

```text
-O0
-O1
-O2
-O3
```

và kiểm tra:

```text
observable result
```

đặc biệt với:

- atomics;
- channels;
- locks;
- async;
- scheduler;
- cancellation.

---

# 63. TSAN-like tool

Về lâu dài Axiom nên có:

```text
axiom test --race
```

hoặc:

```text
axiom run --sanitizer=thread
```

Nhưng đây là tooling/runtime instrumentation.

Không biến race detector thành semantic requirement.

---

# 64. Sanitizer architecture

Compiler có thể instrument:

```text
LOAD
STORE
ATOMIC
LOCK
UNLOCK
THREAD_START
THREAD_JOIN
```

và runtime shadow state.

Có thể hỗ trợ:

```text
AddressSanitizer
ThreadSanitizer
UBSan-like checks
```

nhưng thiết kế native cho Axiom.

---

# 65. Channel + ownership + async

Một ví dụ hoàn chỉnh:

```axiom
async fn worker(
    mut rx: Receiver<Buffer>
) -> Result<(), Error> {

    loop {
        let buffer = await rx.recv_async()?;
        process(buffer);
    }
}
```

Semantic chain:

```text
recv_async
   ↓
WAITING
   ↓
wake
   ↓
READY
   ↓
poll
   ↓
Ready(Buffer)
   ↓
ownership transferred
```

Không có:

```text
Arc<Mutex<Buffer>>
```

trừ khi application thực sự cần shared ownership.

---

# 66. Đây chính là lợi thế lớn của Axiom

Nhiều hệ thống concurrent hiện nay thường đi đến:

```text
Arc
 + Mutex
 + Vec
 + Task
 + Channel
 + lifetime constraints
```

Trong Axiom, nếu dữ liệu có thể chuyển ownership:

```text
Buffer
  ↓ Move
Channel
  ↓ Move
Worker
```

thì không cần shared mutable state.

Đây nên là **default architectural pattern**.

---

# 67. Shared state vẫn có

Khi thực sự cần:

```axiom
let state = Arc::new(Mutex::new(State::new()));
```

thì semantic chain rõ ràng:

```text
Arc
 ↓
shared ownership

Mutex
 ↓
synchronized mutable access

Guard
 ↓
mut_view<State>
```

Mỗi abstraction giải quyết đúng một vấn đề.

---

# 68. Không có “magic concurrent object”

Axiom không nên có một kiểu:

```text
Concurrent<T>
```

và để compiler tự đoán mọi thứ.

Thay vào đó:

```text
Arc
Mutex
RwLock
Atomic
Channel
```

mỗi loại có semantic contract riêng.

---

# 69. Invariants mới

```text
ACHAN-51   Channel Transfer Is Ownership Transfer
ACHAN-52   Failed Send Restores Ownership
ACHAN-53   Empty Is Distinct From Closed
ACHAN-54   Sender Lifetime Determines Closure
ACHAN-55   Receiver Drains Queued Values Before Final Closure
ACHAN-56   Per-Sender FIFO Is Preserved
ACHAN-57   Global Ordering Is Not Required
ACHAN-58   Bounded Channel Does Not Require Per-Message Allocation
ACHAN-59   Channel Waiting Preserves Value Ownership
ACHAN-60   Wake Does Not Create Duplicate Task Identity
ACHAN-61   Zero-Copy Transfer Is Permitted
ACHAN-62   Channel Does Not Imply Shared Ownership
ACHAN-63   Channel Implementations May Specialize By Topology

ALOCK-50   Lock Fast Path May Be Lock-Free
ALOCK-51   Lock Slow Path May Block
ALOCK-52   Blocking Strategy Is Runtime Policy
ALOCK-53   Wait Primitive Is Distinct From Mutex Semantics
ALOCK-54   Unlock Preserves Waiter Visibility
ALOCK-55   Semaphore Permit Is An Owning Capability
ALOCK-56   Permit Release Is Deterministic
ALOCK-57   Fairness Is Not Core Lock Semantics

AATOM-51   Atomic Operations Are Observable Concurrency Events
AATOM-52   Atomic Operations Cannot Be Removed As Dead Code
AATOM-53   Atomic Ordering Must Be Preserved
AATOM-54   Atomic Width Must Be Target-Valid
AATOM-55   Atomic Alignment Must Be Valid
AATOM-56   Lock-Free Is Not Implied By Atomic
AATOM-57   Volatile Is Distinct From Atomic
AATOM-58   Hardware Atomic Lowering Is Target-Specific
AATOM-59   Memory Ordering Is Verified Before Lowering
AATOM-60   SeqCst Semantics Cannot Be Silently Weakened

ARECLAIM-20   Lock-Free Reclamation Is A Runtime Concern
ARECLAIM-21   Hazard Protection Must Outlive Node Access
ARECLAIM-22   Epoch Protection Must Outlive Node Access
ARECLAIM-23   Reclamation Cannot Invalidate A Protected Node
ARECLAIM-24   Reclamation Mechanism Is Not A Core Ownership Primitive
ARECLAIM-25   Unsafe Runtime Code Must Establish Reclamation Preconditions
ARECLAIM-26   Safe Capabilities Cannot Outlive Their Provenance

ARUNTIME-50   Runtime Primitives Have Stable Semantic Contracts
ARUNTIME-51   Optimized Runtime Implementations Must Match Reference Semantics
ARUNTIME-52   Runtime Fast Paths Need Not Allocate
ARUNTIME-53   Scheduler Waiters Must Remain Valid Until Deregistration
ARUNTIME-54   Concurrency Failures Must Be Reproducible When Possible
ARUNTIME-55   Deterministic Scheduling Is A Testing Facility
ARUNTIME-56   Runtime Optimization Cannot Change Observable Synchronization
```

---

# 70. BOOTSTRAP-020 Gate

```text
SPSC channel                         ✓
MPSC model                           ✓
MPMC model                           ✓
bounded channel                      ✓
unbounded policy                     ✓
close semantics                      ✓
ownership restoration                ✓
zero-copy transfer                   ✓
FIFO semantics                       ✓
async channel                        ✓
wait queues                          ✓
mutex fast path                     ✓
mutex slow path                     ✓
semaphore                            ✓
wait/notify abstraction              ✓
atomic lowering contract             ✓
memory ordering                      ✓
volatile distinction                 ✓
lock-free distinction                ✓
memory reclamation boundary          ✓
hazard/epoch/RCU boundary            ✓
scheduler integration                ✓
deterministic scheduler              ✓
concurrency fuzzing                  ✓
-O0/O3 concurrency equivalence       ✓
sanitizer architecture               ✓
```

---

# Một quyết định kiến trúc rất quan trọng

Sau BOOTSTRAP-020, tôi đề xuất **không tiếp tục thêm nhiều primitive concurrency vào Core**.

Core concurrency của Axiom chỉ cần hiểu:

```text
Ownership
Capability
Send
Share
Atomic
Synchronization boundary
Execution domain
```

Còn:

```text
Channel
Mutex
RwLock
Semaphore
Barrier
Scheduler
Fiber
Thread pool
Work stealing
Hazard pointer
Epoch
RCU
```

nên nằm ở **runtime/std/system library**.

Điều này giữ đúng triết lý ban đầu:

> **Core đủ mạnh để compiler chứng minh chương trình an toàn; nhưng không biến mọi implementation technique thành ngôn ngữ.**

---

# Kiến trúc hiện tại đã khá hoàn chỉnh

Ta đang có:

```text
                 AXIOM LANGUAGE
                       │
       ┌───────────────┼────────────────┐
       │               │                │
   Ownership       Capability       Concurrency
       │               │                │
       │          view/mut_view     Send/Share
       │               │                │
       └───────────────┼────────────────┘
                       │
                 VERIFIED MIR
                       │
              ┌────────┴────────┐
              │                 │
           Async             Native
              │                 │
           Future             Code
              │
             Task
              │
          Scheduler
              │
       ┌──────┴──────┐
       │             │
    Thread         Fiber
       │             │
       └──────┬──────┘
              │
        OS / Hardware
```

Và dưới Scheduler:

```text
Channel
Mutex
RwLock
Semaphore
Atomic
Wait/Notify
I/O
Timer
```

đều có thể được tối ưu mạnh mà **không thay đổi source semantics**.

---

## Bước tiếp theo: BOOTSTRAP-021 — Memory Model + Data-Race Semantics

Đây là phần tôi nghĩ **cần làm ngay trước khi đi tiếp sang OS/IO**, vì nó quyết định nền móng concurrency của toàn Axiom.

Ta sẽ phải chốt thật kỹ:

- Axiom memory model chính xác là gì;
- happens-before;
- synchronizes-with;
- sequenced-before;
- atomic modification order;
- visibility;
- data race có thể xảy ra trong safe/unsafe thế nào;
- relaxed/acquire/release/seq_cst chính xác đến đâu;
- compiler được reorder cái gì;
- `view/mut_view` và atomics tương tác thế nào;
- `volatile`;
- FFI và foreign memory;
- signal/interrupt;
- GPU memory model có dùng chung model CPU hay không;
- và đặc biệt **Axiom có nên chọn memory model kiểu C++/Rust, hay thiết kế một model đơn giản hơn nhưng vẫn đủ mạnh cho lock-free programming**.

Đây là một trong những quyết định nền tảng cuối cùng của ngôn ngữ.