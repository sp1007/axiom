# BOOTSTRAP-229 — CONCURRENCY SEMANTICS & DATA-RACE VERIFIER

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là phần hoàn thiện mô hình concurrency của Axiom. Mục tiêu là tránh hai cực:

- kiểu C/C++: rất mạnh nhưng data race và memory ordering dễ trở thành nguồn lỗi;
- kiểu runtime-heavy: an toàn nhưng phải trả nhiều chi phí runtime.

Axiom dùng nguyên tắc:

> **Ownership quyết định ai sở hữu. Capability quyết định ai được truy cập. Effect quyết định đang làm gì. Concurrency quyết định các hành động đó có thể xảy ra đồng thời và được quan sát theo thứ tự nào.**

---

# 1. Mô hình concurrency chính thức

Axiom tách 6 trục:

```text
Execution Domain
    Thread
    Fiber
    Task
    GPU Kernel
    Interrupt/System Context

Storage Domain
    Local
    Shared
    Static
    TLS
    Device
    External

Ownership
    Move
    Send
    Share

Capability
    view<T>
    mut_view<T>

Effect
    Read
    Write
    Atomic
    Synchronize
    Blocking
    AsyncSuspend
    ...

Ordering
    Sequenced-Before
    Synchronizes-With
    Happens-Before
```

Không một trục nào thay thế trục khác.

---

# 2. `Send`

`Send` trả lời:

> Một ownership value có thể chuyển sang execution domain khác không?

Ví dụ:

```axiom
fn worker(data: Data) {
    ...
}

spawn(worker(data))
```

Nếu `Data: Send`:

```text
data
    ownership
       ↓ Move
another execution domain
```

hợp lệ.

---

# 3. `Send` không có nghĩa `Share`

Đây là invariant cực kỳ quan trọng:

```text
Send ≠ Share
```

Một type có thể:

```text
Send = true
Share = false
```

Ví dụ conceptual:

```text
FileHandle
```

có thể chuyển ownership sang thread khác nhưng không cho nhiều thread cùng sử dụng một handle.

---

# 4. `Share`

`Share` trả lời:

> Một giá trị có thể được truy cập đồng thời từ nhiều execution domain không?

Ví dụ immutable data:

```text
Arc<Config>
```

có thể:

```text
Thread A → READ
Thread B → READ
Thread C → READ
```

nếu `Config: Share`.

---

# 5. Share không cho phép arbitrary mutation

```text
Arc<T>
```

không biến:

```text
T
```

thành mutable concurrent object.

Muốn mutation phải có abstraction:

```text
Arc<Mutex<T>>
Arc<RwLock<T>>
Arc<Atomic<T>>
```

hoặc một concurrent data structure được chứng minh.

---

# 6. Compiler-derived Send/Share

Programmer không cần:

```text
unsafe impl Send
```

Axiom compiler tự suy luận.

Ví dụ:

```text
struct Point {
    x: f32
    y: f32
}
```

compiler có thể derive:

```text
Send
Share
```

vì các field đều thỏa.

---

# 7. Send propagation

Nếu:

```text
struct A {
    x: B
    y: C
}
```

thì:

```text
Send(A)
    =
Send(B) ∧ Send(C)
```

trừ khi type có contract đặc biệt.

---

# 8. Share propagation

Tương tự:

```text
Share(A)
    =
Share(B) ∧ Share(C)
```

nhưng `Share` không tự suy ra mutable safety.

---

# 9. Không cho programmer giả mạo

Không được:

```axiom
unsafe impl Send for UnsafeType
```

như một cách bypass verifier.

Nếu cần system-level implementation:

```text
@trusted
```

chỉ tồn tại trong compiler/system boundary và phải cung cấp semantic contract.

---

# 10. Execution domain

Mỗi concurrent computation có:

```text
ExecutionDomainId
```

ví dụ:

```text
Thread(4)
Task(91)
Fiber(12)
GPUKernel(33)
```

Compiler không nhất thiết biết runtime ID cụ thể, nhưng biết loại domain và migration policy.

---

# 11. Thread

Thread là execution domain có:

- stack riêng;
- TLS;
- scheduling bởi OS/runtime;
- có thể chạy song song vật lý.

Core không yêu cầu runtime thread implementation.

---

# 12. Task

Task là execution unit logic.

Task có thể:

```text
Thread A
    ↓
Task
    ↓ await
    ↓
Thread B
```

nếu executor cho phép migration.

Do đó task không mặc định gắn với một thread.

---

# 13. Fiber

Fiber là execution domain stackful.

Mặc định:

```text
Fiber = pinned
```

trừ khi runtime contract cho phép migration.

---

# 14. Future

Future stackless:

```text
Future<State>
```

có state machine.

Nếu future được migration:

```text
Future: Send
```

phải được chứng minh.

---

# 15. Task migration

Nếu:

```text
task: Send
```

thì:

```text
Thread A
   ↓
scheduler
   ↓
Thread B
```

được phép.

Nếu không:

```text
spawn
```

phải reject hoặc dùng local executor.

---

# 16. `spawn_local`

`spawn_local`:

```text
spawn_local(future)
```

không yêu cầu `Send` nếu executor bảo đảm:

```text
same execution domain
```

Nhưng `Share` vẫn không tự xuất hiện.

---

# 17. Structured concurrency

Axiom ưu tiên:

```text
scope
 ├── task A
 ├── task B
 └── task C
```

parent scope biết lifecycle của children.

Detach phải explicit:

```text
spawn_detached(...)
```

---

# 18. Detached task

Detached task có lifetime độc lập.

Compiler phải bảo đảm:

- mọi captured owned values được chuyển hợp lệ;
- không có view trỏ vào stack đã chết;
- không có capability phụ thuộc scope đã kết thúc.

---

# 19. View và concurrency

Một `view<T>`:

```text
read-only
non-owning
```

nhưng không vì vậy mà mặc nhiên `Send`.

Điều kiện:

```text
Send(view<T>)
```

phải phụ thuộc owner/provenance/storage domain.

---

# 20. View qua thread

Ví dụ:

```axiom
let v = view(buffer)

spawn(worker(v))
```

Compiler kiểm tra:

```text
owner(buffer)
lifetime(buffer)
Send(v)
```

Nếu buffer thuộc stack hiện tại:

```text
reject
```

nếu thread có thể sống lâu hơn scope.

---

# 21. Owned value qua thread

```axiom
let data = Data.load()

spawn(worker(data))
```

ownership chuyển:

```text
data
 ↓ Move
worker
```

Nếu:

```text
Data: Send
```

hợp lệ.

---

# 22. Mutable view qua thread

```axiom
spawn(worker(mut_view(data)))
```

không đơn giản chỉ cần `Send`.

Compiler phải chứng minh:

```text
exclusive capability
+
valid lifetime
+
destination execution domain
+
no conflicting capability
```

---

# 23. Hai mutable views

```text
let a = mut_view(buffer[0..100])
let b = mut_view(buffer[100..200])
```

Nếu compiler chứng minh:

```text
DISJOINT(a, b)
```

hai tasks có thể chạy song song.

---

# 24. Unknown overlap

```text
a = mut_view(buffer[x..y])
b = mut_view(buffer[z..w])
```

Nếu compiler không chứng minh disjoint:

```text
UNKNOWN
```

không được coi là disjoint.

---

# 25. Data race

Axiom định nghĩa data race khi tồn tại:

```text
concurrent conflicting accesses
```

và:

```text
at least one is WRITE
```

mà không có:

```text
happens-before
```

hoặc synchronization mechanism hợp lệ.

---

# 26. Read/Read

```text
Thread A: READ X
Thread B: READ X
```

→ không phải data race.

Nếu `X` hợp lệ `Share`.

---

# 27. Read/Write

```text
Thread A: READ X
Thread B: WRITE X
```

nếu đồng thời và không synchronization:

```text
REJECT
```

---

# 28. Write/Write

```text
Thread A: WRITE X
Thread B: WRITE X
```

→ conflict.

Nếu không atomic/synchronization:

```text
REJECT
```

---

# 29. Atomic khác ordinary memory

```text
Atomic<i32>
```

không phải:

```text
i32
```

với một vài annotation.

Nó là một semantic type khác.

---

# 30. Atomic không tạo `mut_view<T>`

Không được:

```text
let x: Atomic<i32>

mut_view(x as i32)
```

Atomic access phải đi qua atomic API.

Điều này ngăn compiler biến atomic operation thành ordinary memory access.

---

# 31. Atomicity và ordering là hai khái niệm

Ví dụ:

```text
Atomic(Relaxed)
```

có:

```text
atomicity
```

nhưng ordering yếu.

```text
Release
Acquire
```

thêm synchronization relation khi cặp operation phù hợp.

---

# 32. Memory order

Axiom hỗ trợ:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Không đưa `Consume` vào Core.

---

# 33. Sequenced-Before

Trong một execution domain:

```text
A
B
C
```

nếu source/control semantics yêu cầu:

```text
A SB B
B SB C
```

thì:

```text
A SB C
```

---

# 34. Synchronizes-With

Một số cặp operation tạo:

```text
Synchronizes-With
```

ví dụ:

```text
Release Store
      ↓
Acquire Load
```

khi load observes tương ứng release sequence theo atomic semantics.

---

# 35. Happens-Before

```text
HB =
transitive closure(
    Sequenced-Before
    ∪ Synchronizes-With
)
```

Đây là foundation của data-race verifier.

---

# 36. Mutex

```axiom
lock(m)
...
unlock(m)
```

unlock → lock tương ứng tạo synchronization.

Compiler hiểu:

```text
unlock
    ↓
Synchronizes-With
    ↓
subsequent lock
```

theo mutex contract.

---

# 37. Mutex guard

```axiom
let guard = mutex.lock()
```

`guard`:

```text
!Copy
Drop → unlock
```

Do đó:

```axiom
let a = guard
```

là Move.

---

# 38. Guard lifetime

Compiler đảm bảo:

```text
lock acquired
    ↓
protected capability valid
    ↓
guard dropped
    ↓
unlock
```

Không được unlock sớm khi capability còn được sử dụng.

---

# 39. RwLock

Có hai capability:

```text
ReadGuard
WriteGuard
```

Read:

```text
multiple readers
```

Write:

```text
exclusive
```

---

# 40. RwLock + await

Không cho:

```axiom
let guard = lock.read()
await something()
```

mặc định.

Lý do:

- guard có thể giữ resource quá lâu;
- task migration;
- deadlock;
- executor blocking.

Compiler reject nếu guard sống qua suspension, trừ explicit async-aware contract.

---

# 41. Async Mutex

Async mutex là type khác:

```text
AsyncMutex<T>
```

API:

```text
let guard = mutex.lock().await
```

Guard vẫn là ownership-bearing capability.

---

# 42. Semaphore

```text
let permit = semaphore.acquire()
```

`Permit`:

```text
!Copy
Drop → release
```

Đây là resource token, không phải memory ownership.

---

# 43. Channel

Channel là ownership boundary.

```axiom
sender.send(value)
```

semantic:

```text
value
 ↓ Move
channel
 ↓ Move
receiver
```

Không cần clone.

---

# 44. Channel synchronization

`send → receive` có synchronization semantics.

Điều này cho phép:

```text
producer writes data
      ↓
send
      ↓
receive
      ↓
consumer reads data
```

mà không cần thêm mutex cho transferred ownership.

---

# 45. Zero-copy channel

Compiler/runtime có thể:

```text
Move Buffer
```

thay vì:

```text
memcpy
```

nếu ABI/runtime cho phép.

---

# 46. Channel type specialization

Library có thể có:

```text
SPSC
MPSC
SPMC
MPMC
```

Core verifier không cần biết implementation chi tiết, chỉ cần synchronization contract.

---

# 47. Per-sender FIFO

Channel guarantee:

```text
send(A)
send(B)
```

từ cùng sender → receiver thấy:

```text
A
B
```

theo FIFO contract.

Không mặc định global ordering giữa nhiều sender.

---

# 48. Wait/Notify

`notify()` không có nghĩa:

```text
predicate == true
```

Chỉ có nghĩa:

```text
a waiter may become runnable
```

Do đó:

```text
wait(predicate)
```

phải recheck predicate.

---

# 49. Notification không phải publication

Một notification không tự tạo memory synchronization nếu API contract không quy định.

Đây là điểm phải giữ rất rõ:

```text
Wakeup ≠ Memory Visibility
```

---

# 50. Volatile

Volatile:

```text
volatile_read
volatile_write
```

dùng cho:

- MMIO;
- device registers;
- special memory.

Volatile không thay thế atomic.

```text
Volatile ≠ Synchronization
```

---

# 51. Atomic ≠ volatile

Atomic:

```text
thread synchronization
```

Volatile:

```text
observable machine memory access
```

Một operation có thể cần cả hai trong system layer nếu semantics yêu cầu.

---

# 52. Compiler fence

Compiler fence:

```text
ngăn compiler reorder
```

CPU fence:

```text
machine memory ordering
```

Hai khái niệm riêng.

---

# 53. `fence`

Axiom phải phân biệt:

```text
compiler_fence(...)
cpu_fence(...)
```

với atomic operation.

---

# 54. Lock-free

Axiom không tuyên bố:

```text
Atomic<T> = lock-free
```

Compiler/library có thể expose:

```text
is_lock_free<T>()
```

hoặc compile-time property.

---

# 55. Wait-free / lock-free / obstruction-free

Đây là implementation/algorithm properties:

```text
WaitFree
LockFree
ObstructionFree
Blocking
```

Không phải mặc định semantic guarantee.

---

# 56. Deadlock

Axiom không cố chứng minh mọi deadlock ở Core v1.

Compiler có thể cung cấp tooling:

```text
lock graph
wait graph
```

nhưng:

```text
deadlock-free
```

không phải invariant chung của safe code.

---

# 57. Vì sao?

Vì deadlock có thể phụ thuộc:

```text
runtime ordering
external callbacks
dynamic resource graph
distributed systems
```

Một verifier toàn cục sẽ quá đắt và hạn chế ngôn ngữ.

---

# 58. Nhưng compiler có thể phát hiện trường hợp đơn giản

Ví dụ static lock order:

```text
lock(A)
lock(B)

another:
lock(B)
lock(A)
```

Tooling có thể cảnh báo potential cycle.

Đây là diagnostic/tooling, không phải semantic rejection mặc định.

---

# 59. Safe code guarantee

Axiom safe code đảm bảo:

```text
NO_DATA_RACE
```

nhưng không đảm bảo:

```text
NO_DEADLOCK
NO_STARVATION
NO_LIVELOCK
```

---

# 60. Starvation

Scheduler/library policy quyết định.

Core không đảm bảo fairness mặc định.

---

# 61. Scheduler

Scheduler là library/runtime.

Core chỉ hiểu:

```text
spawn
await
yield
execution domain
Send
```

không chứa một scheduler cụ thể.

---

# 62. Deterministic executor

Testing runtime có thể cung cấp:

```text
DeterministicExecutor
```

cho phép replay scheduling.

Điều này cực kỳ hữu ích cho compiler conformance tests.

---

# 63. Data-race verifier architecture

```text
Verified MIR
      │
      ├── ExecutionDomain analysis
      │
      ├── Capability analysis
      │
      ├── Access classification
      │
      ├── Synchronization graph
      │
      ├── Happens-Before graph
      │
      └── Race analysis
```

---

# 64. Concurrent access record

Mỗi memory access:

```text
AccessEvent {
    region
    access: READ | WRITE
    execution_domain
    atomic_ordering?
    synchronization_scope?
    source_span
}
```

---

# 65. Race candidate

Hai accesses:

```text
A
B
```

là candidate nếu:

```text
MayAlias(A.region, B.region)
```

và:

```text
A.domain != B.domain
```

và:

```text
at least one WRITE
```

---

# 66. Eliminate bằng capability

Nếu:

```text
DISJOINT(A.region, B.region)
```

→ không race.

---

# 67. Eliminate bằng happens-before

Nếu:

```text
A HB B
```

→ không concurrent race.

---

# 68. Eliminate bằng atomic

Nếu cả hai là atomic accesses phù hợp:

```text
atomic ordering semantics
```

→ không phải ordinary data race.

Nhưng atomic ordering vẫn phải được kiểm tra cho algorithm correctness.

---

# 69. Atomic không chứng minh algorithm đúng

Ví dụ counter atomic có thể tránh race nhưng vẫn logic sai.

Axiom đảm bảo:

```text
memory safety
data-race freedom
ordering semantics
```

không chứng minh business algorithm.

---

# 70. Capability conflict matrix

```text
          READ    WRITE
READ       OK      CONFLICT
WRITE      CONFLICT CONFLICT
```

Trong cùng concurrent region nếu không có synchronization.

---

# 71. Atomic matrix

```text
Atomic READ
Atomic WRITE
Atomic RMW
```

được xử lý theo atomic ordering, không theo ordinary `mut_view`.

---

# 72. Shared immutable

```text
Arc<T>
```

nếu:

```text
T: Share
```

cho phép:

```text
view<T>
```

từ nhiều domains.

---

# 73. Shared mutable

Cách chuẩn:

```axiom
Arc<Mutex<T>>
```

semantic:

```text
Arc
  ownership sharing

Mutex
  synchronization

T
  ordinary mutable value
```

Không có magic concurrent object.

---

# 74. Atomic shared

```axiom
Arc<Atomic<u64>>
```

cho counter/flags.

Không tạo:

```text
mut_view<u64>
```

---

# 75. Concurrent collections

Ví dụ:

```text
ConcurrentHashMap
LockFreeQueue
WorkStealingDeque
```

là library abstractions.

Chúng cung cấp synchronization contracts cho compiler.

---

# 76. Work stealing

Scheduler:

```text
worker A deque
worker B steals task
```

chỉ được steal task nếu:

```text
Task: Send
```

hoặc scheduler contract chứng minh pinned execution.

---

# 77. Pinned task

Task có:

```text
ExecutionAffinity = ThreadLocal
```

không thể migration.

Do đó:

```text
Send
```

không nhất thiết required cho internal migration.

---

# 78. Thread-local storage

TLS:

```text
thread_local<T>
```

mỗi thread có storage identity riêng.

Do đó:

```text
TLS value
```

không phải shared memory giữa threads.

---

# 79. Static mutable state

Safe global mutable state không được tự nhiên tồn tại như C.

Phải dùng:

```text
Atomic
Mutex
RwLock
Once
```

hoặc explicit unsafe/system mechanism.

---

# 80. `static`

Immutable static:

```text
static CONFIG: Config = ...
```

nếu `Config: Share` có thể được read concurrent.

Mutable static:

```text
static mut
```

chỉ system/unsafe.

---

# 81. Thread start

Khi thread starts với owned value:

```text
parent
   ↓ Move
child
```

ownership transfer là synchronization boundary theo thread API contract.

---

# 82. Thread join

```text
join(thread)
```

tạo synchronization:

```text
child completion
      ↓
Synchronizes-With
      ↓
join return
```

Do đó parent có thể đọc kết quả đã được child hoàn thành.

---

# 83. Thread detach

Detach không tạo join synchronization.

Parent không được giả định child đã hoàn thành.

---

# 84. Cancellation

Cancellation không phải panic.

```text
Cancellation
```

là control-flow/resource protocol riêng.

---

# 85. Forced thread termination

Axiom không hỗ trợ safe forced termination.

Vì không thể đảm bảo:

- Drop;
- locks;
- invariants;
- external resources;
- capabilities.

Cancellation phải cooperative.

---

# 86. Cancellation token

Library abstraction:

```axiom
if token.cancelled() {
    return Err(Cancelled)
}
```

hoặc async cancellation contract.

---

# 87. Cancellation + Drop

Nếu Future bị drop:

```text
future state cleanup
```

nhưng external operation chỉ được cancel nếu operation contract quy định.

---

# 88. Parallel iterators

Parallel iterator explicit:

```text
parallel_iter(data)
```

Compiler/library tạo tasks.

Sequential:

```text
iter(data)
```

không tự động parallelize nếu observable ordering/side effects có thể thay đổi.

---

# 89. Parallel map

Nếu callback:

```text
Pure
```

hoặc side-effect-safe contract:

compiler có thể parallelize.

Nếu callback:

```text
IO
```

không được tự động reorder IO.

---

# 90. Parallel reduction

```text
sum()
```

không mặc định được reassociate floating-point operations.

Strict FP:

```text
(a + b) + c
```

khác:

```text
a + (b + c)
```

Parallel relaxed reduction phải explicit.

---

# 91. `Send` + closure

Closure capture được compiler phân tích.

```axiom
let x = large_buffer

spawn(|| use(x))
```

capture:

```text
Move
```

Nếu `x: Send`:

```text
valid
```

---

# 92. Closure capture view

```axiom
let v = view(local_buffer)

spawn(|| use(v))
```

Nếu lifetime local kết thúc trước task:

```text
reject
```

---

# 93. Closure capture shared

```axiom
let data = Arc.new(...)
spawn(|| read(data))
```

closure có shared ownership.

Compiler không tạo implicit clone của arbitrary value; `Arc` clone là explicit semantic operation nếu cần.

---

# 94. Async state + concurrency

Mỗi `.await` tạo:

```text
SuspensionPointId
```

Compiler kiểm tra mọi live value qua suspension:

```text
Send?
storage valid?
capability valid?
guard allowed?
```

---

# 95. View qua await

Mặc định:

```text
view<T>
mut_view<T>
```

không được sống qua `.await` nếu executor có thể migrate hoặc storage/capability contract không bảo đảm.

---

# 96. Owned value qua await

Owned value có thể sống qua await nếu:

```text
storage valid
```

và:

```text
Send
```

nếu future migration được phép.

---

# 97. Local executor

Nếu:

```text
spawn_local
```

future không cần `Send`.

Nhưng compiler vẫn kiểm tra:

```text
lifetime
ownership
capability
```

---

# 98. GPU concurrency

GPU execution domains cũng dùng:

```text
ownership
capability
synchronization
```

nhưng synchronization primitives khác CPU.

---

# 99. GPU barriers

```text
barrier()
```

tạo execution/memory ordering theo GPU scope.

Không được coi barrier GPU giống mutex CPU.

---

# 100. GPU memory scopes

Axiom hỗ trợ scope:

```text
Subgroup
Workgroup
Device
Queue
Host
```

tùy backend.

Compiler map semantic scope xuống target.

---

# 101. Host ↔ GPU

`GpuEvent` tạo synchronization boundary:

```text
GPU writes
    ↓
event completion
    ↓
host access
```

Compiler/runtime contract đảm bảo visibility.

---

# 102. DeviceBuffer

Ownership:

```text
Host owns handle
Device owns storage
```

không có nghĩa host có thể trực tiếp dereference device memory.

---

# 103. Unified memory

`UnifiedBuffer` có coherence contract riêng.

Compiler không assume mọi unified memory đều automatically coherent.

---

# 104. Distributed systems

Đây là boundary:

```text
Axiom Send
```

khác:

```text
Network message
```

Network transmission không phải memory synchronization.

Serialization phải explicit.

---

# 105. Cross-process

```text
Send
```

không có nghĩa object có thể gửi trực tiếp qua process boundary.

Cần:

```text
serialize
```

hoặc:

```text
shared memory contract
```

---

# 106. Shared memory

Typed shared memory cần:

```text
layout
initialization
lifetime
synchronization
process sharing
```

Raw pointer mapping không tự tạo Axiom capability.

---

# 107. Interrupt context

Interrupt/system handler có execution domain đặc biệt:

```text
InterruptContext
```

effect restrictions:

- không arbitrary blocking;
- không arbitrary allocation;
- chỉ allowed synchronization;
- hardware access explicit.

---

# 108. Signal context

Tương tự:

```text
SignalContext
```

không được gọi arbitrary application code.

Signal nên:

```text
signal
 ↓
atomic/event
 ↓
normal context
```

---

# 109. Data-race freedom theorem target

Axiom safe verified program phải thỏa:

> Không tồn tại hai conflicting ordinary memory accesses đến cùng một semantic region có thể xảy ra concurrent mà không có happens-before hoặc synchronization contract hợp lệ.

Đây là một trong những semantic guarantees quan trọng nhất của Axiom.

---

# 110. Nhưng không tuyên bố “mọi chương trình chạy đúng”

Safe code vẫn có thể:

- deadlock;
- starvation;
- livelock;
- logic race;
- protocol bug;
- distributed inconsistency.

Compiler chỉ đảm bảo các invariants thuộc language semantics.

---

# 111. Race verifier và unsafe

`unsafe` có thể tạo raw pointer và thiết lập precondition:

```text
raw memory
 ↓ unsafe contract
validated capability
 ↓
safe MIR
```

Sau boundary, verifier tiếp tục.

Không có:

```text
unsafe {
    disable_race_checker()
}
```

---

# 112. Unsafe contract

Ví dụ conceptual:

```text
unsafe fn split_buffer(
    p: *mut u8,
    n: usize
) -> (mut_view<u8>, mut_view<u8>)
```

contract phải establish:

```text
valid allocation
aligned
initialized
non-overlap
lifetime
```

Sau đó compiler có thể tiếp tục với hai capability disjoint.

---

# 113. Compiler facts

Race verifier tạo:

```text
ConcurrencyFacts {
    NoDataRace
    SendProof
    ShareProof
    HappensBefore
    SynchronizationEdges
    DisjointRegions
    ExecutionAffinity
    MigrationSafety
}
```

---

# 114. Optimizer sử dụng facts

Nếu compiler chứng minh:

```text
A NO_ALIAS B
A DOMAIN != B
No synchronization dependency
```

thì có thể:

```text
parallelize
vectorize
reorder
```

nếu effect semantics cho phép.

---

# 115. Compiler-generated parallelization

Axiom có thể có:

```text
parallel-for
```

hoặc library abstraction.

Compiler có thể tự parallelize loop chỉ khi:

```text
dependency analysis
+
effect analysis
+
capability analysis
+
cost model
```

đều cho phép.

Không biến mọi loop thành thread.

---

# 116. Cost model

Parallelization chỉ đáng làm khi:

```text
parallel benefit > scheduling/synchronization overhead
```

Compiler dùng:

- trip count;
- operation cost;
- target CPU;
- cache;
- vector width;
- thread count;
- profile data.

---

# 117. SIMD trước thread

Một optimization hierarchy hợp lý:

```text
Scalar
 ↓
Instruction simplification
 ↓
SIMD
 ↓
Task parallelism
 ↓
Thread parallelism
 ↓
Distributed execution
```

Không spawn thread nếu SIMD đủ.

---

# 118. Data locality

Concurrency verifier cung cấp safety.

Optimizer thêm:

```text
cache locality
false sharing
NUMA
affinity
```

để quyết định implementation.

---

# 119. False sharing

Hai regions semantic disjoint:

```text
A
B
```

vẫn có thể nằm cùng cache line.

Đây không phải correctness violation.

Là performance issue.

Compiler/library có thể hỗ trợ:

```text
@cache_align
```

hoặc allocator policies.

---

# 120. NUMA

NUMA là target/runtime property.

Không đưa vào ownership semantics.

Nhưng compiler có thể dùng:

```text
StorageDomain
Affinity
```

cho optimization.

---

# 121. Concurrency-aware memory effect

MIR access:

```text
MemoryEffect {
    region
    access
    domain
    atomicity
    ordering
}
```

đây là input cho:

```text
RaceVerifier
AliasAnalysis
MemorySSA
Optimizer
```

---

# 122. Synchronization graph

Compiler xây:

```text
Node:
    memory access
    atomic op
    lock/unlock
    send/receive
    spawn/join
    await/wake
    GPU event

Edge:
    SB
    SW
    HB
    dependency
```

---

# 123. Không cần runtime race checker

Điểm quan trọng:

```text
Axiom safe concurrency
```

được kiểm tra compile-time.

Không cần:

```text
runtime lock around every access
```

hay:

```text
GC
```

để đảm bảo memory safety.

---

# 124. Runtime overhead

Một `Mutex<T>` vẫn có runtime cost.

Nhưng:

```text
Send
Share
view
ownership proof
race verification
```

tự chúng không tạo runtime overhead.

---

# 125. Compile-time proof erasure

Sau verifier:

```text
SendProof
ShareProof
NoAliasProof
LifetimeProof
```

không cần tồn tại trong executable trừ khi runtime API cần chúng.

---

# 126. Dynamic checks chỉ khi semantic cần

Ví dụ runtime channel:

```text
capacity check
```

vẫn cần.

Nhưng không phải vì compiler không chứng minh ownership.

---

# 127. Concurrency error diagnostics

Ví dụ:

```text
AXC2407: conflicting concurrent access
```

Compiler phải chỉ rõ:

```text
write occurs here
read occurs here

Region:
    buffer[128..256]

Execution domains:
    Task A
    Task B

Synchronization:
    none

Reason:
    regions may overlap
```

---

# 128. Explain mode

```text
ax explain race <location>
```

có thể trả:

```text
Access A:
    WRITE buffer[0..n]

Access B:
    READ buffer[i..j]

Region relation:
    UNKNOWN

Execution:
    potentially concurrent

Synchronization:
    none

Conclusion:
    safe proof unavailable
```

---

# 129. AI-native benefit

AI agent không phải đoán:

> “Có thể thêm Mutex không?”

Compiler có thể trả:

```text
Required property:
    exclusive WRITE

Possible resolutions:
    transfer ownership
    establish disjoint regions
    synchronize with Mutex
    use Atomic abstraction
```

AI vẫn tự quyết định code; compiler chỉ cung cấp facts.

---

# 130. Concurrency invariants

```text
ACONCUR-140
Send and Share are distinct semantic properties.

ACONCUR-141
Send permits ownership transfer between compatible execution domains.

ACONCUR-142
Share permits concurrent shared access according to the type contract.

ACONCUR-143
Send does not imply Share.

ACONCUR-144
Share does not imply mutable concurrent access.

ACONCUR-145
Send and Share are compiler-derived by default.

ACONCUR-146
Programmer annotations cannot bypass concurrency verification.

ACONCUR-147
Safe code cannot contain an unverified ordinary-memory data race.

ACONCUR-148
Conflicting concurrent ordinary accesses require happens-before or valid synchronization.

ACONCUR-149
READ/READ concurrent accesses do not constitute a data race.

ACONCUR-150
READ/WRITE conflicting accesses are rejected unless synchronized or otherwise proven safe.

ACONCUR-151
WRITE/WRITE conflicting accesses are rejected unless synchronized or otherwise proven safe.

ACONCUR-152
UNKNOWN region overlap is never treated as DISJOINT.

ACONCUR-153
Disjoint region proofs may eliminate race candidates.

ACONCUR-154
Atomic memory is semantically distinct from ordinary memory.

ACONCUR-155
Atomic operations are not ordinary mutable capabilities.

ACONCUR-156
Atomicity and memory ordering are distinct properties.

ACONCUR-157
Relaxed atomic operations do not create stronger synchronization than specified.

ACONCUR-158
Acquire/Release synchronization is represented explicitly in the memory model.

ACONCUR-159
SeqCst operations participate in the global sequentially-consistent order.

ACONCUR-160
Volatile access is distinct from atomic synchronization.

ACONCUR-161
Compiler fences and CPU memory fences are distinct semantics.

ACONCUR-162
Mutex unlock/lock establishes the synchronization specified by its contract.

ACONCUR-163
Synchronization guards are ownership-bearing and non-Copy.

ACONCUR-164
Guard Drop performs the semantic release operation specified by its contract.

ACONCUR-165
Synchronous guards cannot cross await unless explicitly supported by contract.

ACONCUR-166
Async synchronization primitives are distinct from blocking primitives.

ACONCUR-167
Channel send/receive establishes the ownership and synchronization semantics specified by the channel contract.

ACONCUR-168
Channel ownership transfer does not imply serialization.

ACONCUR-169
Thread completion and join establish the specified synchronization relation.

ACONCUR-170
Detached execution provides no implicit completion synchronization.

ACONCUR-171
Task migration requires Send unless execution affinity explicitly prevents migration.

ACONCUR-172
spawn_local may avoid Send requirements only under a verified local-execution contract.

ACONCUR-173
Future state crossing await is checked for lifetime, capability, storage and migration safety.

ACONCUR-174
Views cannot outlive their provenance owner or storage contract.

ACONCUR-175
Mutable capabilities cannot be concurrently duplicated.

ACONCUR-176
Disjoint mutable capabilities may execute concurrently.

ACONCUR-177
Unsafe does not disable concurrency verification after a safe capability is re-established.

ACONCUR-178
Unsafe contracts may establish trusted preconditions for subsequent verification.

ACONCUR-179
Cancellation is distinct from panic and forced termination.

ACONCUR-180
Safe Axiom code does not support forced thread termination semantics.

ACONCUR-181
Structured concurrency is preferred but detached execution is explicit.

ACONCUR-182
Scheduler implementation is outside Core semantics.

ACONCUR-183
Fairness, starvation-freedom and deadlock-freedom are not general Core guarantees.

ACONCUR-184
Notification is distinct from memory publication.

ACONCUR-185
GPU synchronization uses execution-domain-specific semantics.

ACONCUR-186
Host/device synchronization must be explicit.

ACONCUR-187
Cross-process Send is distinct from serialization.

ACONCUR-188
Shared-memory access requires explicit layout, lifetime and synchronization contracts.

ACONCUR-189
Distributed communication is not automatically memory synchronization.

ACONCUR-190
Concurrency proofs are erased unless required by runtime semantics.

ACONCUR-191
Send/Share verification introduces no mandatory runtime overhead.

ACONCUR-192
Race analysis is part of the correctness boundary before optimization.

ACONCUR-193
Concurrency facts are available to optimization.

ACONCUR-194
Concurrency facts may enable vectorization and parallelization when semantic dependencies permit.

ACONCUR-195
Optimization may not invalidate established concurrency semantics.

ACONCUR-196
Concurrency verification is deterministic.

ACONCUR-197
Concurrency diagnostics expose conflicting accesses, regions, domains and synchronization state.

ACONCUR-198
AI-generated concurrency code is subject to the same verifier.

ACONCUR-199
The concurrency model composes with ownership, capability, effect, async and GPU semantics.
```

---

# 131. Semantic kernel hoàn chỉnh hơn

Axiom bây giờ có thể mô hình hóa một operation bằng 5 câu hỏi:

```text
                 OPERATION
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
   OWNERSHIP     CAPABILITY     EFFECT
   "ai có?"      "truy cập?"     "làm gì?"
        │            │            │
        └────────────┼────────────┘
                     ↓
                CONCURRENCY
                "khi nào?"
                     │
                     ↓
                  DOMAIN
                  "ở đâu?"
```

Đây là kiến trúc rất mạnh vì compiler có thể dùng cùng semantic facts cho:

- memory safety;
- race freedom;
- async;
- GPU;
- optimizer;
- vectorization;
- parallelization;
- FFI;
- AI diagnostics.

---

# 132. Pipeline verifier chính thức

Axiom verifier giờ được chốt thành:

```text
Typed MIR
   │
   ├── Initialization
   │
   ├── Ownership
   │
   ├── Drop
   │
   ├── Capability
   │
   ├── Region / Alias
   │
   ├── Effects
   │
   ├── Execution Domain
   │
   ├── Send / Share
   │
   ├── Synchronization
   │
   ├── Happens-Before
   │
   ├── Data-Race
   │
   ├── Async
   │
   ├── GPU
   │
   └── FFI
   │
   ▼
Verified MIR
```

**Verified MIR là correctness boundary.**

Sau điểm này optimizer được phép cực kỳ aggressive.

---

# 133. Điều này giải quyết một mục tiêu lớn ban đầu của Axiom

Bạn từng lo rằng:

> pointer/reference/borrow checker sẽ khiến lập trình viên phải quản lý quá nhiều thứ.

Kiến trúc hiện tại tránh điều đó.

Programmer chủ yếu viết:

```axiom
fn process(data: Data) -> Result<Output, Error> {
    ...
}
```

Compiler tự quản lý:

```text
ownership
lifetime
alias
region
Send
Share
race
drop
effect
storage
```

Programmer chỉ phải can thiệp khi **semantic boundary thực sự cần**:

```text
unsafe
atomic
Mutex
Channel
async
FFI
GPU
stable ABI
```

Đây chính xác là hướng:

> **Compiler Complexity Is Not Language Complexity.**

---

# TASK TIẾP THEO

## BOOTSTRAP-230 — MEMORY MODEL FORMALIZATION & MACHINE MEMORY ORDERING

Đây là task tiếp theo rất quan trọng.

229 đã nói **ai được chạy đồng thời và synchronization nào hợp lệ**.

230 sẽ formalize chính xác:

```text
Source execution
      ↓
Axiom Memory Model
      ↓
MIR Memory Events
      ↓
Atomic Ordering
      ↓
Compiler Reordering Rules
      ↓
CPU Memory Model
      ↓
Machine Instructions
```

Sẽ chốt:

- formal memory locations;
- semantic reads/writes;
- sequenced-before;
- synchronizes-with;
- happens-before;
- modification order;
- atomic read/write rules;
- Release/Acquire;
- SeqCst;
- fences;
- volatile;
- compiler barriers;
- CPU barriers;
- weak-memory architectures;
- x86;
- ARM64;
- RISC-V;
- GPU memory model mapping;
- compiler reordering legality;
- data-race-free guarantee;
- out-of-thin-air prevention;
- undefined behavior policy;
- interaction với `MemorySSA`;
- interaction với `AliasInfo`;
- interaction với optimizer;
- mapping xuống machine backend.

Đây sẽ là **formal foundation cuối cùng để Axiom có thể vừa an toàn như một language hiện đại vừa cho compiler tự do tối ưu ở mức gần C/C++/ASM**.