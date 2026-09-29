Tiếp tục.

# BOOTSTRAP-039 — Concurrency Semantics Audit & Freeze

Mục tiêu lần này là **hợp nhất toàn bộ concurrency model** đã thiết kế thành một semantics duy nhất.

Axiom không nên có:

```text
Thread rules
Fiber rules
Async rules
Channel rules
Atomic rules
Mutex rules
```

rời rạc.

Tất cả phải quy về một mô hình chung:

```text
Execution Domain
        │
        ├── Ownership
        ├── Capability
        ├── Synchronization
        └── Memory Ordering
```

---

# 1. Nguyên tắc cốt lõi

Axiom phân biệt:

```text
Execution Domain
Storage Domain
Memory Region
Capability
```

Đây là 4 khái niệm khác nhau.

### Execution Domain

Nơi code đang chạy:

```text
Thread
Fiber
Task
GPU execution domain
interrupt context
...
```

### Storage Domain

Nơi dữ liệu tồn tại:

```text
Local
Shared
Device
External
Static
TLS
...
```

Một thread không nhất thiết đồng nghĩa với một storage domain.

---

# 2. Execution Domain

Mỗi computation thuộc một execution domain.

Ví dụ:

```text
CPU Thread A
CPU Thread B
Fiber X
Task Y
GPU Kernel Z
```

Compiler/runtime theo dõi việc computation có thể:

```text
stay
move
share
```

giữa các domain.

---

# 3. `Send`

`Send` trả lời đúng **một câu hỏi**:

> Ownership của giá trị này có thể được chuyển sang execution domain khác không?

Ví dụ:

```axiom
let x = Data(...)
thread.spawn(move x)
```

Nếu `Data: Send`:

```text
Domain A
   │ Move
   ▼
Domain B
```

hợp lệ.

---

# 4. `Send` không có nghĩa Share

Một type có thể:

```text
Send
!Share
```

Ví dụ một resource có thể được chuyển sang thread khác nhưng không được đồng thời sử dụng từ hai thread.

Đây là distinction rất quan trọng.

---

# 5. `Share`

`Share` trả lời:

> Giá trị có thể được truy cập đồng thời từ nhiều execution domains theo semantics của type hay không?

Ví dụ:

```text
ImmutableData
```

có thể:

```text
Share
```

nhưng không nhất thiết:

```text
Send
```

trong mọi abstraction đặc biệt.

---

# 6. `Share` không có nghĩa mutable sharing

Đây là rule bắt buộc:

```text
Share
≠
Concurrent mutable access
```

Một immutable `Arc<T>` có thể được share.

Mutable shared state phải thông qua:

```text
Mutex
RwLock
Atomic
ConcurrentCollection
```

hoặc abstraction có synchronization tương đương.

---

# 7. Compiler derive

Programmer không cần viết:

```text
impl Send for Foo
impl Share for Foo
```

nếu compiler có thể xác định.

Ví dụ:

```axiom
struct Foo {
    a: i32
    b: String
}
```

compiler tự suy ra property dựa trên semantic properties của fields.

---

# 8. Không được user tự assert sai

Không cho:

```axiom
unsafe impl Send for Foo
```

trong Core v1 chỉ để ép compiler tin.

Nếu cần một abstraction đặc biệt:

```text
unsafe boundary
+
compiler-known contract
```

phải được kiểm soát ở system/library layer.

---

# 9. Ownership transfer giữa domain

Channel:

```axiom
tx.send(value)
```

là:

```text
Move
```

không phải:

```text
Copy
```

Do đó:

```text
Domain A
   value
     │
    Move
     ▼
Domain B
```

Không tạo shared ownership.

---

# 10. Channel không phải Arc

Đây là distinction nên giữ cực rõ:

```text
Channel<T>
```

= transfer ownership.

```text
Arc<T>
```

= shared ownership.

Hai abstraction phục vụ hai vấn đề khác nhau.

---

# 11. Zero-copy transfer

Nếu:

```text
T = 4 MB Buffer
```

channel không nên mặc định copy 4 MB.

Có thể:

```text
descriptor/ownership
        ↓
destination
```

payload vẫn ở cùng storage nếu semantics cho phép.

---

# 12. Capability khi chuyển domain

Nếu một value có:

```text
ownership
```

thì Move transfer ownership.

Nếu có:

```text
view<T>
```

thì không được coi việc gửi view như gửi ownership.

View phải chứng minh storage vẫn hợp lệ ở destination.

Do đó:

```text
send(view)
```

thường bị reject hoặc chỉ hợp lệ với explicit shared-storage contract.

---

# 13. `mut_view`

`mut_view<T>` là exclusive write capability.

Không được:

```text
Thread A → mut_view
Thread B → copy mut_view
```

Compiler phải reject nếu hai capability có thể cùng tồn tại.

---

# 14. `view`

`view<T>` là READ capability.

Có thể duplicate:

```text
view A
   ├── reader 1
   ├── reader 2
   └── reader 3
```

nhưng không được:

```text
view + mut_view
```

trên cùng region đồng thời.

---

# 15. Region

Compiler theo dõi region:

```text
A
B
A.field1
A.field2
```

Ví dụ:

```axiom
struct Data {
    x: i32
    y: i32
}
```

Có thể:

```text
mut_view<Data.x>
mut_view<Data.y>
```

đồng thời vì:

```text
DISJOINT
```

Nhưng:

```text
mut_view<Data>
mut_view<Data.x>
```

xung đột:

```text
CONTAINS
```

---

# 16. Unknown overlap

Nếu compiler không chứng minh:

```text
DISJOINT
```

thì không được giả định chúng không overlap trong safe code.

```text
UNKNOWN
```

→ reject hoặc yêu cầu abstraction chứng minh.

Đây là điểm giúp optimizer có alias guarantees mà không cần programmer viết `restrict`.

---

# 17. Synchronization

Synchronization trả lời:

> Khi nào operation ở execution domain này được phép quan sát effect từ execution domain khác?

Axiom sử dụng:

```text
sequenced-before
synchronizes-with
happens-before
```

---

# 18. Happens-before

Định nghĩa:

```text
sequenced-before
        +
synchronizes-with
        ↓
happens-before
```

và quan hệ này có tính transitive.

---

# 19. Không copy toàn bộ C++ memory model

Axiom không cần hàng loạt semantics obscure của C++.

Mục tiêu:

```text
simple enough to reason about
strong enough for native optimization
```

---

# 20. Atomic

`Atomic<T>` là type riêng.

Không:

```text
Atomic<T>
    ↓
mut_view<T>
```

vì atomic access và ordinary mutable access có semantics khác nhau.

---

# 21. Atomicity ≠ Ordering

Axiom tách:

```text
Atomicity
Ordering
Visibility
```

Một operation có thể atomic nhưng không tạo synchronization.

---

# 22. Memory orders

Giữ 5 mức:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Không đưa `consume` vào Core.

---

# 23. Relaxed

`Relaxed` đảm bảo:

```text
atomicity
modification order
```

nhưng không tự tạo publication ordering cho các memory operations khác.

---

# 24. Release

Release đảm bảo các operation trước nó theo program order không bị quan sát như xảy ra sau publication point khi Acquire synchronization tương ứng được thiết lập.

Ví dụ:

```axiom
data.value = 42
ready.store(true, Release)
```

---

# 25. Acquire

```axiom
if ready.load(Acquire) {
    use(data)
}
```

nếu load quan sát publication phù hợp, các write trước Release được publish cho phía Acquire.

---

# 26. AcqRel

Cho read-modify-write:

```text
Acquire + Release
```

trên cùng operation.

---

# 27. SeqCst

`SeqCst` thêm một total order cho các SeqCst operations, nhất quán với happens-before.

Đây là mode dễ reasoning nhất nhưng không nên mặc định mọi atomic operation đều dùng nó.

---

# 28. Atomic modification order

Mỗi atomic object có modification order riêng.

Ví dụ:

```text
A.store(1)
A.store(2)
A.store(3)
```

không thể tạo một lịch modification order mâu thuẫn.

---

# 29. Atomic load không nhất thiết thấy giá trị "mới nhất"

Với:

```text
Relaxed
```

không được diễn giải:

```text
load = latest global value
```

mà phải tuân theo atomic modification order và memory model.

---

# 30. Mutex

`Mutex<T>` là synchronization abstraction.

```axiom
let guard = mutex.lock()
```

guard sở hữu access capability.

---

# 31. Guard

Guard:

```text
!Copy
Move
Drop
```

Drop:

```text
guard
 ↓
unlock
```

---

# 32. Guard → view

Read lock:

```text
Mutex<T>
   ↓
ReadGuard
   ↓
view<T>
```

Write lock:

```text
Mutex<T>
   ↓
WriteGuard
   ↓
mut_view<T>
```

---

# 33. Guard lifetime

View lấy từ guard không được sống lâu hơn guard.

```text
Guard
  │
  └── view
```

Nếu:

```text
drop(guard)
```

trong khi view còn live:

```text
reject
```

---

# 34. Read locks

Có thể:

```text
ReadGuard A
ReadGuard B
ReadGuard C
```

đồng thời.

Tất cả chỉ tạo:

```text
READ
```

capability.

---

# 35. Write lock

Chỉ một:

```text
WRITE
```

capability.

Không được đồng thời:

```text
READ
WRITE
```

trên cùng protected region.

---

# 36. Mutex và Send

Không nên mặc định:

```text
Mutex<T>: Send
```

chỉ dựa vào T.

Semantics phụ thuộc implementation/storage contract.

Compiler/library trait solver quyết định dựa trên abstraction.

---

# 37. Mutex và Share

Một pattern hợp lệ:

```text
Arc<Mutex<T>>
```

cho phép:

```text
Arc
 ↓
shared access
 ↓
Mutex
 ↓
exclusive guard
 ↓
T
```

`T` không cần tự `Share` để được bảo vệ bởi Mutex, nếu Mutex abstraction đảm bảo synchronization.

---

# 38. Atomic không cần Mutex

Ví dụ:

```axiom
Atomic<u64>
```

có thể được Share trực tiếp.

Nhưng không tạo:

```text
mut_view<u64>
```

thông thường.

---

# 39. Volatile

`volatile` hoàn toàn khác:

```text
volatile
≠
atomic
≠
synchronization
```

Volatile dành cho:

- MMIO
- hardware registers
- externally observable memory

Nó không tạo happens-before.

---

# 40. `volatile` không sửa data race

Nếu hai threads cùng access volatile memory mà không có synchronization:

```text
volatile
```

không biến nó thành thread-safe.

---

# 41. Fence

Có thể có:

```text
fence(order)
compiler_fence(order)
```

nhưng đây là low-level primitives.

Không nên dùng chúng để xây API application-level.

---

# 42. Atomic wait/notify

Axiom hỗ trợ semantic:

```text
wait
notify_one
notify_all
```

Nhưng implementation có thể:

```text
spin
park
futex
OS primitive
```

Không quy định implementation.

---

# 43. Notify không phải publication

```text
notify()
```

không tự tạo:

```text
Release
```

hoặc:

```text
Acquire
```

Publication phải đến từ synchronization operation phù hợp.

---

# 44. Thread start

Khi:

```text
Thread A
    |
    | spawn
    ▼
Thread B
```

các operation trước thread start được happens-before child start theo thread-start synchronization semantics.

---

# 45. Thread join

Khi:

```text
Thread B
    |
    | complete
    ▼
Thread A
    |
    | join
```

completion synchronizes với successful join observation.

---

# 46. Panic + join

Nếu child panic:

```text
join()
```

quan sát được panic.

Không có exception tự động bay qua thread boundary.

---

# 47. Channel synchronization

Successful:

```text
send(value)
```

và corresponding:

```text
recv()
```

có synchronization semantics đủ để ownership transfer và publication semantics được định nghĩa rõ.

---

# 48. Failed send

Nếu channel closed:

```text
send(value)
```

→:

```text
SendError<T>
```

`T` được trả lại cho sender.

Không leak ownership.

---

# 49. Channel ordering

Mỗi sender:

```text
A → m1
A → m2
```

giữ FIFO theo sender.

Nhưng:

```text
A → m1
B → m2
```

không có global order bắt buộc nếu channel là multi-producer.

---

# 50. Bounded channel

Primitive ưu tiên:

```text
bounded ring buffer
```

vì:

- predictable memory
- no per-message allocation
- backpressure
- cache locality.

---

# 51. Unbounded channel

Có thể có ở library:

```text
UnboundedChannel<T>
```

nhưng đây là policy, không phải Core synchronization primitive.

---

# 52. Channel wait states

Async channel:

```text
WAITING_SEND
WAITING_RECEIVE
```

không tạo task mới.

Chỉ:

```text
WAITING → READY
```

khi điều kiện thay đổi.

---

# 53. Wait node

Runtime có thể dùng:

```text
intrusive WaitLink
```

để tránh allocation.

Task không được reclaim khi còn registration sống.

---

# 54. Semaphore

Semaphore:

```text
acquire()
```

→ `Permit`.

Permit:

```text
!Copy
Drop => release
```

Đây là cùng philosophy:

> synchronization capability là resource có ownership.

---

# 55. Condition variable

```text
wait(guard)
```

phải atomically:

```text
release lock
+
enter waiting state
```

sau đó khi wake:

```text
reacquire
```

và trả guard mới.

---

# 56. Wake không đảm bảo predicate

Sau:

```text
wake()
```

predicate có thể vẫn false.

Do đó pattern:

```text
while !condition {
    wait()
}
```

vẫn là semantic rule.

---

# 57. Barrier / Once

Các abstraction:

```text
Barrier
Once
OnceLock
```

là library synchronization primitives.

Không cần Core keywords.

---

# 58. Deadlock

Axiom Core **không đảm bảo deadlock freedom**.

Ví dụ:

```text
lock A
lock B

thread 2:
lock B
lock A
```

có thể deadlock.

Compiler không nên cố giải quyết mọi deadlock bằng static analysis.

---

# 59. Fairness

Không freeze:

```text
FIFO fairness
strong fairness
priority fairness
```

ở Core semantics.

Đây là scheduler/lock implementation policy.

---

# 60. Lock-free

Không đồng nghĩa:

```text
fast
```

Phân biệt:

```text
obstruction-free
lock-free
wait-free
blocking
```

API semantics không phụ thuộc implementation class.

---

# 61. Atomic CAS

CAS:

```text
compare_exchange(expected, desired)
```

có:

```text
success_order
failure_order
```

Failure order không được là:

```text
Release
AcqRel
```

theo semantics đã chọn.

---

# 62. Weak CAS

Có:

```text
weak CAS
```

cho phép spurious failure.

Strong CAS:

```text
strong CAS
```

không được fail chỉ vì spurious failure.

---

# 63. Atomic width

`Atomic<T>` chỉ hợp lệ nếu target hỗ trợ alignment/width tương ứng.

Ví dụ:

```text
Atomic<u64>
```

không mặc định có nghĩa:

```text
hardware lock-free
```

---

# 64. Lock-free property

Có thể expose compile-time query:

```text
is_lock_free<T>()
```

hoặc compiler metadata tương đương.

Nhưng:

```text
Atomic<T>
```

không tự hứa lock-free.

---

# 65. False sharing

Library/system có thể:

```text
@align(cache_line)
```

hoặc abstraction tương đương.

Đây là storage/performance contract, không phải synchronization semantics.

---

# 66. Scheduler

Scheduler không chịu trách nhiệm semantic verification.

Nó nhận:

```text
verified task
```

và quản lý:

```text
READY
WAITING
RUNNING
COMPLETE
```

---

# 67. Work stealing

Default runtime có thể:

```text
Worker A local queue
Worker B local queue
Worker C local queue
```

Worker idle:

```text
steal
```

nhưng chỉ steal task:

```text
Send
```

nếu migration được phép.

---

# 68. Local task

Task có:

```text
!Send
```

thì scheduler phải giữ execution-domain affinity.

Không được tự ý migrate.

---

# 69. Scheduler không được thay đổi ownership

Scheduler:

```text
move task
```

không có nghĩa:

```text
copy task
```

Task state vẫn obey ownership semantics.

---

# 70. Fiber

Fiber là:

```text
stackful execution context
```

khác Future:

```text
stackless state machine
```

Fiber mặc định pinned.

Migration không implicit.

---

# 71. Fiber stack

Fiber có explicit stack storage contract.

Trong suốt lifetime:

```text
stack address stable
```

nếu API yêu cầu address stability.

---

# 72. Fiber cancellation

Không được:

```text
free running fiber stack
```

Cancellation cooperative.

Sau khi fiber dừng an toàn:

```text
Drop initialized resources
release stack
```

---

# 73. Fiber context

Context tối thiểu:

```text
SP
IP
callee-saved registers
platform control state
```

Không nhét:

```text
scheduler
allocator
TLS object
```

vào context structure.

---

# 74. Thread-local vs Fiber-local

Hai semantics khác nhau:

```text
Thread TLS
Fiber-local storage
```

không được đánh đồng.

Fiber-local có thể được library/runtime implement.

---

# 75. Data race

Đây là một trong những invariant quan trọng nhất:

> Safe Axiom code không được có data race.

Nếu compiler có thể chứng minh:

```text
WRITE A
WRITE B
```

không cùng region → hợp lệ.

Nếu:

```text
WRITE
READ
```

có thể concurrent và không có synchronization → reject trong safe model khi compiler có đủ information; unsafe/system abstractions phải establish explicit contracts.

---

# 76. Không dùng "data race = UB" như C/C++

Axiom không muốn safe programmer phải sống với:

```text
"compiler có thể làm bất kỳ thứ gì vì race là UB"
```

Thay vào đó:

```text
safe code
 ↓
race impossible / rejected
```

Unsafe code có thể expose machine behavior ngoài guarantees.

---

# 77. Unsafe không tắt verifier

Đây là nguyên tắc đã freeze:

```text
unsafe
```

không nghĩa:

```text
compiler stop checking everything
```

Unsafe cho phép programmer establish precondition mà compiler không chứng minh được.

Sau boundary:

```text
safe verification resumes
```

với contract đã established.

---

# 78. FFI

Foreign call:

```text
extern "C"
```

không tự động tạo synchronization.

Nếu C code sửa shared memory:

```text
Axiom compiler
```

không được tự đoán rằng foreign function tạo happens-before.

Phải có explicit contract.

---

# 79. Interrupt/signal

Interrupt context là execution domain đặc biệt.

Shared memory với interrupt handler cần system-level synchronization contract.

Không đưa toàn bộ interrupt semantics vào Core application model.

---

# 80. GPU

GPU memory model là extension theo execution domain.

Không nhét:

```text
warp
wavefront
block
subgroup
```

vào CPU Core semantics.

GPU layer xây trên:

```text
ownership
capability
atomic
ordering
storage domain
```

và bổ sung scoped semantics.

---

# 81. Unified memory

Unified memory không có nghĩa:

```text
automatic synchronization
```

CPU/GPU vẫn cần synchronization.

---

# 82. Async và memory model

`await`:

```text
KHÔNG tự động = full memory fence
```

Fiber switch cũng vậy.

Scheduler synchronization chỉ tạo happens-before khi abstraction thực sự định nghĩa synchronization edge.

---

# 83. Wake và memory model

```text
wake()
```

chỉ là scheduling notification.

Publication phải dựa trên:

```text
atomic ordering
mutex
channel
other synchronization primitive
```

---

# 84. Compiler optimization

Compiler có thể:

```text
reorder
hoist
sink
inline
vectorize
eliminate
```

nếu không thay đổi semantics theo memory model.

---

# 85. Atomic optimization

Compiler không được biến:

```text
Acquire
```

thành:

```text
Relaxed
```

nếu observable memory semantics thay đổi.

---

# 86. Ordinary memory

Compiler có quyền reorder ordinary memory operations mạnh hơn atomic operations.

Nhưng chỉ trong giới hạn:

```text
happens-before
data-race-free semantics
observable behavior
```

---

# 87. Deterministic scheduler

Runtime nên có:

```text
DeterministicExecutor
```

cho test.

Ví dụ có thể kiểm soát:

```text
task order
wake order
timer
```

giúp reproduce race/concurrency bugs.

---

# 88. Concurrency testing

Axiom runtime nên hướng tới:

```text
stress tests
random scheduler
deterministic scheduler
litmus tests
race instrumentation
sanitizer
```

nhưng đây là tooling/runtime, không phải language semantics.

---

# 89. Sanitizer

Có thể có:

```text
-race
-asan
-tsan-like
```

ở toolchain.

Instrumentation không thay đổi production semantics.

---

# 90. Memory reclamation

Lock-free structures có thể cần:

```text
Hazard Pointer
Epoch Based Reclamation
RCU
Generation Handle
Pool
Quarantine
```

Không đưa:

```text
epoch lifetime annotations
hazard annotations
```

vào language.

---

# 91. Vì sao?

Nếu programmer phải viết:

```text
epoch<'a>
hazard<'b>
```

Axiom lại rơi vào đúng vấn đề mà chúng ta đang tránh:

> compiler implementation complexity trở thành programmer complexity.

Runtime/library phải gánh phần đó.

---

# 92. Ownership + reclamation

Ví dụ lock-free node:

```text
logical identity
        +
reclamation protocol
```

khác với:

```text
raw pointer
```

Safe API nên expose:

```text
Handle<T>
```

nếu phù hợp.

---

# 93. Generation Handle

Ví dụ:

```text
slot = 42
generation = 7
```

handle:

```text
Handle<Entity>
```

Nếu slot bị recycle:

```text
generation = 8
```

handle cũ không còn hợp lệ.

Đây là logical identity, không phải pointer.

---

# 94. Shared ownership

`Arc<T>`:

```text
shared ownership
```

nhưng:

```text
Arc<T> ≠ concurrent mutable access
```

Để mutable:

```text
Arc<Mutex<T>>
Arc<RwLock<T>>
Arc<Atomic<T>>
```

---

# 95. Rc

`Rc<T>`:

```text
single execution domain
non-atomic reference counting
```

không dùng cho concurrent sharing.

---

# 96. Arc

`Arc<T>`:

```text
atomic reference count
```

nhưng T vẫn phải thỏa requirements phù hợp với cách truy cập.

Arc không biến arbitrary `T` thành thread-safe mutable state.

---

# 97. Reference count overflow

Không cho:

```text
wraparound
```

silent.

Overflow phải:

```text
abort
panic
error
```

theo library policy.

---

# 98. Cycles

`Arc`/`Rc` không tự giải quyết cycle:

```text
A → B
B → A
```

Nếu cần:

```text
Weak
```

hoặc arena/GC-like application structure.

GC không được đưa vào Core chỉ để giải quyết cycle.

---

# 99. Concurrency API layering

Kiến trúc runtime:

```text
Axiom language semantics
          │
          ▼
safe concurrency abstractions
          │
          ▼
lock-free / blocking primitives
          │
          ▼
OS / CPU / GPU
```

Ví dụ:

```text
Channel
  ↓
RingBuffer / Mutex / Atomic
  ↓
CAS / futex / OS
```

---

# 100. Một nguyên tắc rất quan trọng

Từ toàn bộ concurrency model, Axiom có thể freeze thành:

> **Ownership controls who may possess a value.  
> Capability controls who may access a region.  
> Synchronization controls when concurrent accesses are ordered.  
> Execution domains control where computation runs.**

Đây là bốn trục độc lập.

---

# 101. Không để `Send` gánh quá nhiều nghĩa

Sai:

```text
Send = thread safe
```

Đúng:

```text
Send = ownership transfer across execution domains is valid
```

---

# 102. Không để `Share` gánh quá nhiều nghĩa

Sai:

```text
Share = mutable thread safe
```

Đúng:

```text
Share = concurrent shared observation/access is semantically valid
```

Cách mutate phải được abstraction xác định.

---

# 103. Không để Atomic gánh ownership

Sai:

```text
Atomic = shared ownership
```

Đúng:

```text
Atomic = synchronized machine-level access to one value
```

Ownership vẫn do outer type quyết định.

---

# 104. Không để Mutex gánh storage

Sai:

```text
Mutex = heap object
```

Mutex storage có thể:

```text
stack
static
inline
heap
shared memory
```

tùy abstraction.

---

# 105. Không để async gánh scheduling

Sai:

```text
async = executor
```

Đúng:

```text
async = state-machine/control-flow abstraction
executor = runtime policy
```

---

# 106. Không để Channel gánh allocation

Sai:

```text
channel = heap queue
```

Đúng:

```text
Channel semantic
    ↓
implementation may be
    ├── inline ring
    ├── fixed buffer
    ├── pool
    ├── heap queue
    └── specialized lock-free structure
```

---

# 107. Không để Fiber gánh scheduler

Fiber chỉ là execution context.

Scheduler là abstraction khác.

---

# 108. Không để scheduler gánh correctness

Scheduler không sửa:

```text
ownership bug
race bug
lifetime bug
type bug
```

Compiler/runtime-safe primitives phải đảm bảo semantics trước.

---

# 109. Concurrency model hoàn chỉnh

Toàn bộ hệ thống:

```text
                         Axiom Concurrency
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
    Execution Domain       Ownership            Synchronization
          │                     │                     │
   ┌──────┼──────┐         Send / Move       ┌────────┼────────┐
   │      │      │                           │        │        │
 Thread  Fiber  Task                       Mutex   Atomic  Channel
                  │
                Future
                  │
                await
```

Và capability chạy xuyên suốt:

```text
Owner
  ↓
view / mut_view
  ↓
synchronization guard
  ↓
execution domain
```

---

# 110. Invariants ACONCUR — Freeze

Các invariant concurrency trước đây được hợp nhất thành bộ sau:

```text
ACONCUR-20   Execution domains are distinct from storage domains.
ACONCUR-21   Thread is an execution resource.
ACONCUR-22   Fiber is a stackful execution context.
ACONCUR-23   Task is a schedulable computation.
ACONCUR-24   Future is a stackless computation state machine.

ACONCUR-25   Send permits ownership transfer across execution domains.
ACONCUR-26   Send does not imply Share.
ACONCUR-27   Share does not imply mutable concurrent access.
ACONCUR-28   Cross-domain ownership transfer is Move.
ACONCUR-29   Compiler derives Send where semantics permit.
ACONCUR-30   Compiler derives Share where semantics permit.
ACONCUR-31   Programmer cannot unsafely assert false Send/Share semantics.
ACONCUR-32   Shared mutable access requires synchronization.

ACONCUR-33   view is a read capability.
ACONCUR-34   mut_view is an exclusive write capability.
ACONCUR-35   Capabilities cannot outlive valid provenance.
ACONCUR-36   Conflicting mutable capabilities are forbidden in safe code.
ACONCUR-37   Unknown overlap cannot be assumed disjoint.
ACONCUR-38   Disjoint regions may be accessed independently.
ACONCUR-39   Synchronization does not transfer ownership.
ACONCUR-40   Ownership transfer does not itself imply arbitrary synchronization.

ACONCUR-41   Happens-before is formed from sequenced-before and synchronizes-with.
ACONCUR-42   Synchronization edges are defined by explicit synchronization primitives.
ACONCUR-43   Await is not inherently a full memory fence.
ACONCUR-44   Fiber switching is not inherently a full memory fence.
ACONCUR-45   Wake is not inherently a publication barrier.
ACONCUR-46   FFI does not implicitly create synchronization.

ACONCUR-47   Atomic values have semantics distinct from ordinary mutable values.
ACONCUR-48   Atomicity is distinct from memory ordering.
ACONCUR-49   Relaxed provides atomicity without general publication ordering.
ACONCUR-50   Acquire orders subsequent operations.
ACONCUR-51   Release orders preceding operations.
ACONCUR-52   AcqRel combines Acquire and Release semantics.
ACONCUR-53   SeqCst provides a single total order consistent with happens-before.
ACONCUR-54   Consume is not part of Core v1.
ACONCUR-55   Atomic modification order is defined per atomic object.
ACONCUR-56   Atomic does not imply lock-free implementation.
ACONCUR-57   Atomic alignment and width must be target-valid.
ACONCUR-58   Volatile is distinct from Atomic.
ACONCUR-59   Volatile does not establish synchronization.
ACONCUR-60   Atomic wait/notify does not itself define publication semantics.

ACONCUR-61   Mutex provides synchronized protected access.
ACONCUR-62   Mutex guards are ownership-bearing capabilities.
ACONCUR-63   Mutex guards are not Copy.
ACONCUR-64   Guard Drop releases the synchronization capability.
ACONCUR-65   Guard-derived views cannot outlive their guards.
ACONCUR-66   Concurrent read guards may coexist.
ACONCUR-67   Write guards are exclusive.
ACONCUR-68   Synchronous guards cannot cross await by default.
ACONCUR-69   Async synchronization uses distinct abstractions.
ACONCUR-70   Mutex does not imply heap allocation.
ACONCUR-71   Mutex does not itself imply shared ownership.

ACONCUR-72   Channel is an ownership-transfer boundary.
ACONCUR-73   Channel send moves ownership.
ACONCUR-74   Channel does not imply shared ownership.
ACONCUR-75   Failed channel send returns ownership where specified.
ACONCUR-76   Bounded channels provide explicit backpressure.
ACONCUR-77   Channel ordering is at least per-sender FIFO where specified.
ACONCUR-78   Global ordering is not implied for concurrent senders.
ACONCUR-79   Channel waiting does not create duplicate task identities.
ACONCUR-80   Channel wakeups must not lose registered waiters.
ACONCUR-81   Channel implementation need not allocate per message.

ACONCUR-82   Semaphore permits are ownership-bearing capabilities.
ACONCUR-83   Permit Drop releases the acquired permit.
ACONCUR-84   Condition waiting releases and later reacquires synchronization according to its contract.
ACONCUR-85   Wake does not imply that the waited predicate is true.
ACONCUR-86   Deadlock freedom is not guaranteed by Core.
ACONCUR-87   Fairness is not a Core synchronization guarantee.

ACONCUR-88   Scheduler executes verified computations.
ACONCUR-89   Scheduler does not replace semantic verification.
ACONCUR-90   Only migration-safe tasks may be migrated.
ACONCUR-91   Local tasks preserve execution-domain affinity.
ACONCUR-92   Work stealing is a runtime policy.
ACONCUR-93   Scheduler shutdown preserves resource lifetime.

ACONCUR-94   Fiber migration is not implicit.
ACONCUR-95   Fiber stack lifetime covers active execution.
ACONCUR-96   Running Fiber storage cannot be reclaimed prematurely.
ACONCUR-97   Fiber cancellation is cooperative.
ACONCUR-98   Fiber context does not inherently contain scheduler state.

ACONCUR-99   Safe code cannot contain data races.
ACONCUR-100  Unsafe does not disable all compiler verification.
ACONCUR-101  Unsafe operations may establish trusted semantic preconditions.
ACONCUR-102  Safe verification resumes after an unsafe boundary for established contracts.

ACONCUR-103  Lock-free is an implementation property, not an API semantic requirement.
ACONCUR-104  Wait-free, lock-free, obstruction-free, and blocking are distinct implementation classes.
ACONCUR-105  Lock-free reclamation is a runtime/library concern.
ACONCUR-106  Hazard/epoch metadata is not programmer lifetime syntax.
ACONCUR-107  RCU and reclamation protocols are library/runtime abstractions.
ACONCUR-108  Generation handles represent logical identity, not memory addresses.

ACONCUR-109  Arc provides explicit shared ownership.
ACONCUR-110  Rc is restricted to appropriate non-concurrent domains.
ACONCUR-111  Arc does not make arbitrary mutable state thread-safe.
ACONCUR-112  Reference counting is not implicit in the language.
ACONCUR-113  Reference-count overflow cannot silently wrap.
ACONCUR-114  Cyclic ownership is not automatically reclaimed.

ACONCUR-115  Deterministic executors are valid testing implementations.
ACONCUR-116  Concurrency stress testing is tooling/runtime infrastructure.
ACONCUR-117  Sanitizers do not redefine production semantics.

ACONCUR-118  Compiler optimization must preserve the Axiom memory model.
ACONCUR-119  Atomic ordering cannot be weakened when observable semantics change.
ACONCUR-120  Synchronization primitives may hide target-specific memory orders.
ACONCUR-121  Low-level atomic APIs expose explicit ordering.
ACONCUR-122  High-level synchronization APIs may encapsulate ordering.

ACONCUR-123  GPU synchronization extends the model by execution/storage scope.
ACONCUR-124  GPU unified memory does not imply automatic synchronization.
ACONCUR-125  Device operations must preserve storage lifetime.
ACONCUR-126  CPU and GPU memory models remain explicitly distinguishable.

ACONCUR-127  Async task migration follows Send semantics.
ACONCUR-128  Future state is ownership and capability checked.
ACONCUR-129  Async channel operations preserve ownership-transfer semantics.
ACONCUR-130  Async synchronization is not equivalent to synchronous locking.

ACONCUR-131  Concurrency abstractions do not imply mandatory runtime components.
ACONCUR-132  Runtime components are independently linkable.
ACONCUR-133  Programs need only the concurrency machinery they actually use.
ACONCUR-134  Freestanding programs may omit scheduler/thread/async runtime.
```

---

## Architecture đã freeze

Điểm quan trọng nhất của BOOTSTRAP-039 là Axiom giờ có thể diễn đạt concurrency bằng **4 trục đơn giản**:

```text
             ┌─────────────────────┐
             │   EXECUTION DOMAIN  │
             │ Thread/Fiber/Task   │
             └──────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │      OWNERSHIP      │
             │ Move / Send / Share │
             └──────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │     CAPABILITY      │
             │ view / mut_view     │
             └──────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │   SYNCHRONIZATION   │
             │ Atomic/Mutex/Chan   │
             └──────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │   MEMORY ORDERING   │
             │ HB / Acquire/...    │
             └─────────────────────┘
```

Điều này khá quan trọng đối với mục tiêu của Axiom: **không đưa thread/async/lock/pointer/lifetime thành những cơ chế ngôn ngữ riêng biệt đầy rẫy annotation**. Compiler xử lý phần phức tạp; programmer chỉ phải thể hiện những semantic boundary thực sự quan trọng.

### Tiếp theo: BOOTSTRAP-040

Phần tiếp theo sẽ là **GPU / Device Execution Model Audit & Freeze**: `@kernel`, CPU↔GPU ownership, `DeviceBuffer`, `DeviceView`, address spaces, GPU async event, kernel legality, atomic scope, unified memory và đặc biệt là **làm thế nào để GPU programming không phá vỡ ownership/capability model hiện tại**.