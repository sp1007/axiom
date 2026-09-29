Tiếp tục với **SYNCHRONIZATION-001 — Synchronization Model**. Đây là phần cần khóa chặt trước khi đi sang atomics/memory ordering nâng cao, vì `MutexGuard → mut_view` chính là nơi ownership, capability, Drop và concurrency gặp nhau.

# SYNCHRONIZATION-001

## 1. Nguyên tắc cốt lõi

Axiom không coi mutex là một kiểu “con trỏ bảo vệ”.

Nó là:

> **Một synchronization object tạo ra quyền truy cập có giới hạn thời gian.**

Mô hình:

```text
Mutex<T>
   │
   │ lock
   ▼
MutexGuard<T>
   │
   │ access
   ▼
mut_view<T>
   │
   │ guard alive
   ▼
protected data
```

Khi guard bị Drop:

```text
MutexGuard<T>
   │
   ▼
unlock
```

Do đó programmer không cần:

```text
unlock()
```

trong code bình thường.

---

# 2. Mutex không cần chứa `T` theo nghĩa vật lý cố định

Semantic:

```axiom
Mutex<T>
```

nghĩa là:

```text
T
+
synchronization state
+
ownership/access protocol
```

Implementation có thể là:

```text
┌──────────────────┐
│ lock state       │
│ owner/wait state │
│ T                │
└──────────────────┘
```

nhưng compiler vẫn được phép optimize layout.

Không có object header bắt buộc.

---

# 3. API

MVP:

```axiom
let mutex = Mutex.new(value)

let guard = mutex.lock()
```

Read/write nên được tách rõ.

```axiom
let guard = mutex.read()
```

→ read capability.

```axiom
let guard = mutex.write()
```

→ exclusive mutable capability.

Tôi ưu tiên API này hơn:

```text
lock().read()
lock().write()
```

vì semantic access mode xuất hiện ngay tại operation.

---

# 4. Guard tự động unlock

Ví dụ:

```axiom
{
    let guard = mutex.write()
    guard.value += 1
}

// guard Drop
// mutex unlock
```

Compiler biết:

```text
scope exit
   ↓
Drop guard
   ↓
release synchronization ownership
```

Không cần `defer`.

---

# 5. Guard không phải `Copy`

```text
MutexGuard<T>
```

là resource capability.

Vì vậy:

```axiom
let a = mutex.write()
let b = a
```

là Move.

Sau đó:

```axiom
a.value
```

không hợp lệ.

Nếu cần truyền guard:

```axiom
fn process(g: MutexGuard<T>) { ... }

process(a)
```

ownership của guard được transfer.

---

# 6. Guard tạo view

Đây là điểm quan trọng nhất.

Ta muốn:

```axiom
let guard = mutex.write()
let data = guard.view_mut()
```

Semantic:

```text
Mutex
  │
  └── lock ownership
          │
          └── mut_view<T>
```

`mut_view<T>` **phụ thuộc vào guard**, không trực tiếp vào Mutex.

Do đó:

```axiom
{
    let guard = mutex.write()
    let v = guard.view_mut()

    use(v)
}
```

hợp lệ.

Nhưng:

```axiom
let v

{
    let guard = mutex.write()
    v = guard.view_mut()
}

use(v)
```

phải bị reject.

Không cần programmer viết:

```text
'a
```

hay lifetime annotation.

---

# 7. Đây không phải borrow checker kiểu Rust

Khác biệt kiến trúc rất quan trọng.

Rust thường biểu diễn dependency bằng lifetime syntax:

```rust
MutexGuard<'a, T>
```

Axiom không expose nó.

Compiler internal model:

```text
Capability
{
    provenance: GuardId
    region: Region
    access: READ | WRITE
    validity: GuardLifetime
}
```

Programmer chỉ thấy:

```axiom
mut_view<T>
```

Compiler tự biết:

```text
mut_view #17
depends_on
guard #9
```

---

# 8. Read lock

```axiom
let guard = mutex.read()
```

cho phép:

```text
view<T>
```

nhiều read guards có thể tồn tại:

```text
Mutex
 ├── Reader A
 │     └── view<T>
 ├── Reader B
 │     └── view<T>
 └── Reader C
       └── view<T>
```

Không được:

```text
Reader + Writer
```

đồng thời.

---

# 9. Write lock

```axiom
let guard = mutex.write()
```

chỉ có:

```text
one writer
```

và không có reader.

```text
Mutex
   │
   └── Writer
        └── mut_view<T>
```

Compiler/runtime đều phải giữ invariant này.

---

# 10. Guard không thể vượt qua `await`

Đây là rule cực quan trọng.

Không cho:

```axiom
let guard = mutex.write()

some_async_operation().await

guard.value += 1
```

vì lock có thể bị giữ trong toàn bộ thời gian suspension.

Hậu quả:

```text
Task WAITING
   │
   └── Mutex vẫn locked
          │
          └── Task khác chờ
```

có thể gây deadlock/starvation.

Axiom rule:

> **Synchronous synchronization guards cannot cross an async suspension point.**

Đã khớp invariant:

```text
ACONC-29
```

---

# 11. Nếu cần giữ lock qua await?

Không làm bằng cách phá rule.

Dùng async-aware synchronization:

```axiom
let guard = async_mutex.write().await
```

Đây là **một abstraction khác**.

Nó có thể:

```text
WAITING
 ↓
release execution
 ↓
wake
 ↓
acquire
 ↓
continue
```

Không giữ OS mutex trong lúc task suspended.

---

# 12. MutexGuard và Send

Mặc định:

```text
MutexGuard<T>
```

không nên tùy tiện Send.

Ví dụ:

```axiom
let guard = mutex.write()

spawn(fn() {
    use(guard)
})
```

có thể gây lock ownership migration giữa execution domains.

Thay vì đặt rule phức tạp, mặc định:

```text
MutexGuard<T> : !Send
```

trừ abstraction/platform cụ thể chứng minh được.

Programmer muốn transfer dữ liệu:

```axiom
let value = {
    let guard = mutex.write()
    guard.take()
}

spawn(fn() {
    use(value)
})
```

Ownership của `T` được transfer, không phải lock.

---

# 13. `Mutex<T>` có thể Send/Share

Nếu:

```text
T: Send
```

thì:

```text
Mutex<T>
```

có thể Send.

Nếu synchronization primitive được thiết kế thread-safe thì:

```text
Mutex<T>: Share
```

để nhiều thread có thể truy cập cùng mutex.

Đây là điểm:

```text
Send != Share
```

vẫn được giữ nguyên.

---

# 14. Mutex không biến T thành Share

Ví dụ:

```text
T
```

không thread-safe.

Nhưng:

```text
Mutex<T>
```

có thể Share.

Đây chính là mục tiêu:

```text
unsafe T
   ↓ protected by
Mutex<T>
   ↓
safe concurrent access
```

Compiler không cần `T: Share` để `Mutex<T>` được shared.

Nó cần `T` đáp ứng điều kiện phù hợp để move vào mutex và sử dụng qua guard.

---

# 15. RwLock

API:

```axiom
let guard = rwlock.read()
```

→ `view<T>`.

```axiom
let guard = rwlock.write()
```

→ `mut_view<T>`.

Mô hình:

```text
              RwLock<T>
             /         \
        read            write
         │                │
    many readers       one writer
         │                │
      view<T>         mut_view<T>
```

---

# 16. Condition variable

`Condition` không nên giữ data.

API concept:

```axiom
let guard = mutex.write()

while !condition {
    guard = cond.wait(guard)
}
```

Nhưng Axiom phải tránh API khiến programmer vô tình giữ một view trong lúc wait.

Semantics:

```text
wait(guard)
```

atomically:

```text
release mutex
      +
enqueue waiter
      +
suspend
```

khi wake:

```text
wake
 ↓
reacquire mutex
 ↓
return new guard
```

Do đó:

```text
MutexGuard trước wait
```

không tồn tại trong lúc task/thread ngủ.

---

# 17. `cond.wait` không trả lại cùng identity

Semantic model nên coi:

```text
guard2 = cond.wait(guard1)
```

là:

```text
consume guard1
release lock
wait
reacquire
produce guard2
```

Không nên coi đây là mutation của guard object.

Điều này rất hợp với ownership model.

---

# 18. Spurious wakeup

Condition variable phải cho phép:

```text
wake
```

không đồng nghĩa:

```text
condition == true
```

Vì vậy API/hướng dẫn phải dùng:

```axiom
while !ready {
    guard = cond.wait(guard)
}
```

không phải:

```axiom
if !ready {
    guard = cond.wait(guard)
}
```

Đây là semantic property của condition abstraction.

---

# 19. Semaphore

Semaphore là resource counter:

```text
Semaphore
    permits = N
```

Acquire:

```axiom
sem.acquire()
```

Release:

```axiom
sem.release()
```

Nhưng tôi đề xuất thêm RAII permit:

```axiom
let permit = sem.acquire()?
```

Drop:

```text
Permit Drop
    ↓
release()
```

Tương tự MutexGuard.

---

# 20. Permit không được Copy

```text
Permit
```

là ownership của một permit.

Do đó:

```text
Permit : !Copy
```

Move được.

Clone không tự động được.

Nếu cần nhiều permit:

```axiom
sem.acquire_n(4)?
```

trả về:

```text
PermitSet
```

hoặc explicit repeated acquire.

---

# 21. Barrier

Barrier là synchronization event:

```text
Barrier(N)
```

Mỗi participant:

```axiom
barrier.wait()
```

Khi đủ N:

```text
all wake
```

Barrier không tạo ownership transfer.

Không cần tích hợp sâu với type system ngoài synchronization effects.

---

# 22. Once

Cần một primitive rất hữu ích:

```axiom
Once
```

Ví dụ:

```axiom
static INIT: Once = Once.new()

INIT.call(|| {
    initialize()
})
```

Nhưng closure capture phải tuân ownership rules.

`Once` có thể là std/runtime abstraction.

---

# 23. `OnceLock<T>`

Sau đó:

```axiom
OnceLock<T>
```

cho phép lazy initialization:

```axiom
static CONFIG: OnceLock<Config>

let config = CONFIG.get_or_init(|| load_config())
```

Compiler không cần runtime reflection hay GC.

---

# 24. Mutex poisoning — không nên có

Rust có concept poisoning.

Axiom không nên đưa poisoning vào synchronization semantics Core.

Nếu thread panic:

```text
panic
 ↓
unwind/abort profile
```

Mutex phải có behavior rõ ràng.

Tôi đề xuất:

> **Mutex không bị “poison” bởi panic.**

Nếu unwind xảy ra khi guard sống:

```text
Drop guard
 ↓
unlock
```

Nếu abort:

```text
process terminates
```

Không tạo state:

```text
POISONED
```

trừ khi một library abstraction thực sự cần semantics đó.

Đơn giản hơn đáng kể.

---

# 25. Fairness

Không nên đưa:

```text
fair mutex
strict FIFO mutex
priority inheritance
```

vào language semantics.

Mutex contract chỉ cần:

```text
mutual exclusion
```

Fairness là implementation/platform policy.

Có thể có:

```text
FairMutex
SpinMutex
AdaptiveMutex
RwLock
```

như các library types.

---

# 26. Spin lock

Systems programming cần:

```text
SpinLock<T>
```

API tương tự Mutex:

```axiom
let guard = lock.lock()
```

và:

```text
guard.view()
guard.view_mut()
```

Nhưng:

```text
SpinLock
```

không được dùng qua await.

Compiler/runtime có thể không cần biết đây là spinlock; type contract đánh dấu synchronous guard.

---

# 27. Atomic

Sau synchronization primitives, cần phân biệt:

```text
Atomic<T>
```

với:

```text
Mutex<T>
```

Atomic cho phép:

```axiom
counter.fetch_add(1, Ordering::Relaxed)
```

Nhưng `Ordering` cần thiết kế riêng.

Không nên dùng C/C++ memory model nguyên xi.

Axiom nên có semantic levels:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

và compiler kiểm tra operation hợp lệ.

Phần này nên được thiết kế thành **ATOMIC-001** riêng ngay sau Synchronization.

---

# 28. Atomic không tạo `view`

Ví dụ:

```axiom
Atomic<i64>
```

không nên cho:

```text
mut_view<i64>
```

vì như vậy programmer có thể bypass atomic semantics.

Thay vào đó:

```axiom
atomic.load(...)
atomic.store(...)
atomic.fetch_add(...)
atomic.compare_exchange(...)
```

Atomic là access protocol riêng.

---

# 29. Lock-free structure

Điều này mở đường cho:

```text
Atomic
 ↓
CAS
 ↓
Lock-free queue
 ↓
Scheduler
 ↓
Channel
```

Như vậy Channel không cần là primitive.

Channel library có thể được implement trên:

```text
Atomic
+
parking/wake
+
ownership
```

---

# 30. Nhưng compiler phải hiểu lock guards

Đây là chỗ tôi đề xuất thêm **Synchronization Capability** vào internal verifier.

Capability hiện tại:

```text
Owner
view
mut_view
```

mở rộng:

```text
AccessCapability
├── Read
├── Write
├── Move
├── Drop
└── SyncGuard
```

Nhưng **SyncGuard không phải type mới cho programmer**.

Compiler internal:

```text
GuardCapability {
    lock_id
    access_mode
    region
    execution_domain
    valid_until
}
```

---

# 31. Quy tắc capability

Ví dụ:

```axiom
let g = mutex.write()
let v = g.view_mut()
```

Verifier:

```text
g:
    lock = M
    mode = WRITE
    valid = scope S

v:
    provenance = g
    region = M.value
    mode = WRITE
```

Nếu:

```axiom
drop(g)
```

thì compiler kiểm tra:

```text
live capability dependent on g?
```

Nếu có:

```text
ERROR:
cannot destroy synchronization guard while dependent mutable capability is live
```

---

# 32. Nhưng thường không cần programmer gọi `drop(g)`

Ví dụ:

```axiom
{
    let g = mutex.write()
    modify(g)
}
```

compiler tự:

```text
modify
 ↓
Drop(g)
 ↓
unlock
```

và tất cả dependent capabilities kết thúc trước Drop.

---

# 33. Field-level locking

Axiom đã có region analysis.

Do đó:

```axiom
struct State {
    a: i32
    b: i32
}
```

nếu abstraction cho phép lock riêng:

```text
Lock<State.a>
Lock<State.b>
```

compiler có thể chứng minh:

```text
region(a) DISJOINT region(b)
```

và cho phép concurrency.

Không cần programmer dùng `unsafe`.

---

# 34. Không tự động split Mutex

Tuy nhiên:

```text
Mutex<State>
```

không được compiler tự ý coi:

```text
Mutex<State.a>
Mutex<State.b>
```

trừ khi API/storage abstraction nói rõ.

Nếu không, một mutex vẫn là một synchronization region duy nhất.

Điều này tránh compiler semantics trở nên khó đoán.

---

# 35. Deadlock

Axiom không nên cố compile-time solve mọi deadlock.

Không thực tế.

Nhưng compiler có thể có diagnostics/tooling:

```text
lock-order analysis
```

optional.

Library có thể cung cấp:

```text
OrderedMutex
LockSet
```

hoặc static lock ranking sau này.

Core chỉ đảm bảo:

```text
memory safety
data-race safety
ownership correctness
```

Không đảm bảo:

```text
deadlock freedom
```

---

# 36. Synchronization và memory visibility

Lock/unlock phải có synchronization semantics.

Conceptually:

```text
unlock
   release
      ↓
lock
   acquire
      ↓
subsequent reads observe prior writes
```

Không được compiler reorder xuyên lock theo cách phá observable synchronization semantics.

Đây sẽ kết nối trực tiếp với ATOMIC-001.

---

# 37. Invariants

Chốt:

```text
ASYNC/SYNC-001
SYNCHRONIZATION-001

ASYNC-LOCK-20
Synchronous Guards Cannot Cross Await

ASYNC-LOCK-21
Guard Destruction Releases Its Synchronization Capability

ASYNC-LOCK-22
Guard Is Not Copyable

ASYNC-LOCK-23
Guard Move Transfers Synchronization Capability

ASYNC-LOCK-24
Guard-Derived Views Cannot Outlive Guard

ASYNC-LOCK-25
Read Guards Permit Concurrent Read Access

ASYNC-LOCK-26
Write Guard Excludes Conflicting Access

ASYNC-LOCK-27
Mutex<T> Does Not Require T: Share For Protected Access

ASYNC-LOCK-28
MutexGuard Does Not Imply Send

ASYNC-LOCK-29
Condition Wait Atomically Releases And Later Reacquires Lock

ASYNC-LOCK-30
Condition Wake Does Not Establish Predicate Truth

ASYNC-LOCK-31
Semaphore Permit Is An Owning Capability

ASYNC-LOCK-32
Semaphore Permit Is Not Copyable

ASYNC-LOCK-33
Synchronization Fairness Is Not Core Language Semantics

ASYNC-LOCK-34
Synchronization Does Not Require Heap Allocation By Language Semantics

ASYNC-LOCK-35
Synchronization Does Not Require Garbage Collection

ASYNC-LOCK-36
Synchronization Does Not Imply OS Thread Creation

ASYNC-LOCK-37
Mutex Poisoning Is Not Core Synchronization Semantics

ASYNC-LOCK-38
Atomic Access Is Distinct From Mutex-Protected Access

ASYNC-LOCK-39
Atomic Objects Do Not Expose Ordinary Mutable Views

ASYNC-LOCK-40
Synchronization Establishes Memory Visibility

ASYNC-LOCK-41
Deadlock Freedom Is Not Guaranteed By Core Synchronization

ASYNC-LOCK-42
Synchronization Capability Validity Is Verified Independently Of Optimization

ASYNC-LOCK-43
Dependent Capabilities Prevent Premature Guard Destruction

ASYNC-LOCK-44
Synchronization Regions Participate In Alias/Capability Analysis

ASYNC-LOCK-45
Lock Implementations Are Library/Runtime Strategies
```

---

# Kiến trúc concurrency hiện tại

Bây giờ stack đã khá hoàn chỉnh:

```text
                    OWNERSHIP
                        │
             ┌──────────┴──────────┐
             ↓                     ↓
           Send                   Share
             │                     │
             ↓                     ↓
         Channel                Mutex
             │                 ┌───┴───┐
             │                 ↓       ↓
             │              RwLock   Atomic
             │                 │
             │          ┌──────┴──────┐
             │          ↓             ↓
             │        view         mut_view
             │
             ↓
          Task/Future
             │
             ↓
         Scheduler
        ┌────┼────┐
        ↓    ↓    ↓
      Thread Fiber GPU
```

Và quan trọng nhất:

```text
Programmer:
    ownership + explicit synchronization

Compiler:
    lifetime
    capability
    alias
    escape
    Send/Share
    guard dependency

Runtime:
    scheduling
    wake
    lock implementation
    atomic implementation

Machine:
    actual memory ordering
    atomic instructions
    fences
    OS primitives
```

**Không đẩy complexity của compiler/runtime lên syntax của programmer.**

---

## Bước kế tiếp: ATOMIC-001

Bây giờ cần khóa **Axiom Memory Ordering Model**.

Đây có lẽ là một trong những phần quan trọng nhất của toàn bộ ngôn ngữ, vì mục tiêu của chúng ta là **C/C++-class performance nhưng không muốn programmer phải gánh toàn bộ sự khó hiểu của C++ memory model**.

Ta sẽ thiết kế:

```text
Atomic<T>
Ordering
Acquire / Release
CAS
fence
atomic wait/notify
lock-free guarantees
false sharing/alignment
volatile
device/GPU atomics
```

và đặc biệt quyết định **Axiom có giữ nguyên 5 memory order của C++/Rust hay đơn giản hóa chúng**, đồng thời không hy sinh khả năng viết lock-free runtime, scheduler và compiler backend.