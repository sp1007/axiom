# AXIOM LANGUAGE SPECIFICATION v0.1
# Part XVII — Concurrency · Threads · Tasks · Channels · Synchronization

Mục tiêu của phần này:

> **Concurrency phải là một thuộc tính của chương trình và type system, không phải một runtime model bắt buộc.**

Axiom cần cho phép viết:

```axiom
let t = spawn(work)
t.join()?
```

nhưng đồng thời phải cho phép chương trình freestanding cực thấp:

```text
main
 └── machine code
```

mà không kéo theo:

- GC
- scheduler
- thread pool
- async runtime
- exception runtime
- object runtime

---

# 1. Ba khái niệm phải tách biệt

Axiom phân biệt:

```text
Thread
Task
Future
```

### Thread

Execution context do OS/hardware quản lý.

### Task

Logical unit of concurrent execution.

### Future

Computation có thể suspend/resume.

Quan hệ có thể là:

```text
Thread
 ├── Task A
 ├── Task B
 └── Task C
```

hoặc:

```text
Thread A
    └── Task A

Thread B
    └── Task B
```

Task không nhất thiết tương ứng 1:1 với thread.

---

# 2. Thread là library abstraction

Core compiler chỉ cần biết những semantic property như:

```text
Send
Share
ownership transfer
synchronization
atomicity
```

API thread thuộc library:

```axiom
let thread = Thread.spawn(work)
let result = thread.join()?
```

Không có primitive:

```text
thread_create()
```

bắt buộc trong language syntax.

---

# 3. Spawn là ownership boundary

Ví dụ:

```axiom
let data = Buffer(...)

let t = Thread.spawn(move || {
    process(data)
})
```

Sau `move`:

```text
caller
    data ──X

thread
    data ──ownership
```

Caller không còn được sử dụng `data`.

---

# 4. Không implicit shared mutable state

Không cho phép compiler âm thầm biến:

```axiom
var counter = 0
```

thành một object thread-safe để:

```text
thread A → counter
thread B → counter
```

Safe concurrency phải đi qua abstraction phù hợp:

```text
Atomic
Mutex
RwLock
Channel
```

---

# 5. `Send`

`Send` biểu thị:

> Ownership của value có thể chuyển sang execution context khác.

Ví dụ:

```axiom
spawn(move || use(buffer))
```

cần:

```text
Buffer: Send
```

nếu thread/task có thể chạy ở execution context khác.

---

# 6. `Send` không phải `Share`

Đây là distinction cực kỳ quan trọng.

```text
Send
    ownership transfer

Share
    concurrent shared access
```

Một type có thể:

```text
Send + !Share
```

hoặc:

```text
Share + Send
```

Không được suy luận:

```text
Send ⇒ Share
```

---

# 7. Ví dụ

```text
Buffer
    Send
    !Share
```

Có thể:

```text
thread A
    owns Buffer

       ↓ move

thread B
    owns Buffer
```

Nhưng không thể:

```text
thread A ─┐
          ├── shared mutable Buffer
thread B ─┘
```

nếu không có synchronization.

---

# 8. `Share`

`Share` biểu thị rằng một value có thể được truy cập đồng thời từ nhiều execution contexts theo contract của type.

Ví dụ conceptually:

```text
Arc<T>
```

có thể là:

```text
Send + Share
```

nếu `T` thỏa các yêu cầu tương ứng.

Nhưng:

```text
Arc<T>
```

không tự biến mutable access thành safe.

---

# 9. Immutable sharing

Mô hình phổ biến:

```text
Arc<T>
  ├── Thread A → view<T>
  ├── Thread B → view<T>
  └── Thread C → view<T>
```

Nếu `T` immutable/read-only:

```text
READ + READ
```

không conflict.

---

# 10. Shared mutation

Muốn:

```text
Thread A → WRITE
Thread B → WRITE
```

phải có synchronization abstraction.

Ví dụ:

```axiom
let counter = Atomic<i64>(0)
```

hoặc:

```axiom
let counter = Mutex.new(0)
```

---

# 11. Ordinary `mut_view` không vượt execution boundary

Không được tự động:

```text
let v = mut_view(data)

spawn(move || {
    modify(v)
})
```

trừ khi API/compiler có một abstraction đặc biệt chứng minh ownership/synchronization phù hợp.

`mut_view` là:

```text
exclusive write capability
```

không phải:

```text
thread-safe mutable reference
```

---

# 12. Thread spawn và closure capture

Ví dụ:

```axiom
let data = Buffer(...)

let thread = Thread.spawn(move || {
    process(data)
})
```

Compiler phân tích capture:

```text
closure
 └── data: Move
```

Sau đó kiểm tra:

```text
data: Send
```

---

# 13. Không cần programmer viết lifetime

Không có:

```text
'a
```

hoặc:

```text
thread: 'static
```

Axiom compiler tự kiểm tra:

```text
captured values
    ↓
ownership
    ↓
escape
    ↓
Send
```

---

# 14. Thread join

```axiom
let t = Thread.spawn(work)

let result = t.join()?
```

`join` tạo synchronization boundary.

Sau join:

```text
thread completion
        ↓
happens-before
        ↓
caller
```

theo contract của Thread API.

---

# 15. Join handle ownership

Handle thường là owning resource:

```text
ThreadHandle
```

Không phải Copy.

Ví dụ:

```axiom
let t = Thread.spawn(work)

let a = t
let b = t     // ERROR
```

nếu `ThreadHandle` là move-only.

---

# 16. Detached thread

Nếu muốn thread sống độc lập:

```axiom
Thread.detach(work)
```

hoặc:

```axiom
let t = Thread.spawn(work)
t.detach()
```

Phải explicit.

Không tự động detach khi programmer quên join.

---

# 17. Tại sao không implicit detach?

Nếu:

```axiom
Thread.spawn(work)
```

tự detach:

programmer dễ vô tình tạo:

```text
background thread
    ↓
owns resources
    ↓
program exits
```

và khó xác định lifecycle.

Axiom ưu tiên ownership rõ ràng.

---

# 18. Structured concurrency

Axiom library nên có:

```axiom
scope {
    let a = spawn(...)
    let b = spawn(...)
}
```

conceptually:

```text
scope
 ├── task A
 └── task B

scope cannot complete
until children resolved
```

Đây nên là abstraction chuẩn cho phần lớn concurrent code.

---

# 19. Detached execution là escape hatch

Structured concurrency:

```text
parent owns children
```

Detached:

```text
parent
   │
   X
   │
background task
```

Detached task phải có ownership model riêng.

---

# 20. Thread cancellation

Không có:

```axiom
thread.kill()
```

với semantics an toàn tùy ý.

Không thể an toàn để dừng một thread giữa:

```text
lock acquisition
resource update
FFI
critical invariant
```

---

# 21. Cooperative cancellation

Library có thể cung cấp:

```text
CancellationToken
CancellationSource
```

Ví dụ:

```axiom
while !token.is_cancelled() {
    work()
}
```

Hoặc cancellation qua channel/event.

---

# 22. Forced OS termination

System/unsafe API có thể expose OS-specific mechanism.

Nhưng:

```text
unsafe
```

không biến nó thành safe concurrency.

Programmer chịu trách nhiệm invariants.

---

# 23. Mutex

Mutex là library type:

```axiom
let lock = Mutex.new(value)
```

Conceptually:

```text
Mutex<T>
```

owns `T`.

---

# 24. Lock guard

```axiom
let guard = lock.lock()
```

guard sở hữu quyền truy cập trong critical section.

Conceptually:

```text
Mutex<T>
    │
    └── MutexGuard<T>
            │
            └── mut_view<T>
```

---

# 25. Guard không Copy

```text
MutexGuard<T>: !Copy
```

vì Copy guard có thể dẫn tới:

```text
guard A
guard B
```

cùng biểu diễn một lock ownership.

---

# 26. Guard Drop unlocks

```axiom
{
    let guard = lock.lock()
    modify(guard)
}
```

Khi scope kết thúc:

```text
Drop(guard)
    ↓
unlock
```

Đây là một trường hợp rất phù hợp với deterministic Drop.

---

# 27. Lock guard không qua await

Đã freeze:

```text
MutexGuard<T>
    ↓
cannot live across await
```

Ví dụ:

```axiom
let guard = mutex.lock()

do_io().await

use(guard)
```

→ compile error.

---

# 28. Vì sao?

Synchronous Mutex:

```text
thread holds OS/user lock
```

Nếu suspend:

```text
task suspended
lock remains held
```

có thể tạo:

```text
deadlock
starvation
priority inversion
```

Axiom không cho phép abstraction synchronous bị sử dụng như async lock.

---

# 29. AsyncMutex

Nếu cần:

```axiom
let guard = mutex.lock().await
```

phải dùng:

```text
AsyncMutex<T>
```

Đây là một type khác.

Không phải:

```text
Mutex<T>
```

với một overload đặc biệt.

---

# 30. RwLock

```text
RwLock<T>
```

cho:

```text
many readers
one writer
```

Read guard:

```text
ReadGuard<T>
    ↓
view<T>
```

Write guard:

```text
WriteGuard<T>
    ↓
mut_view<T>
```

---

# 31. Read guard

Nhiều read guards có thể tồn tại:

```text
RwLock
 ├── ReadGuard A
 ├── ReadGuard B
 └── ReadGuard C
```

vì:

```text
READ + READ = allowed
```

---

# 32. Write guard

Trong lúc:

```text
WriteGuard
```

tồn tại:

```text
new ReadGuard
new WriteGuard
```

không được acquire thành công theo lock semantics.

---

# 33. Locking không phải memory ordering

Axiom phải giữ distinction:

```text
Mutex
    synchronization abstraction

Atomic
    atomic memory operation

Fence
    memory ordering primitive
```

Không được xem chúng là cùng một cơ chế.

---

# 34. Atomic

Đã định nghĩa trong Part XVI:

```text
Atomic<T>
```

là type-level property.

Không được:

```text
view<Atomic<T>>
```

rồi coi nó là ordinary memory.

---

# 35. Channel

Channel là ownership-transfer abstraction.

Ví dụ:

```axiom
let (tx, rx) = channel<Data>()

spawn(move || {
    tx.send(data)
})

let data = rx.receive()?
```

Ownership:

```text
producer
   data
     ↓
   channel
     ↓
consumer
```

---

# 36. Channel không cần Copy

`send(data)` thường move:

```text
data
 ↓
channel
```

Sau:

```axiom
tx.send(data)
use(data) // ERROR
```

nếu send thành công/consumes ownership theo API.

---

# 37. Channel có thể truyền Copy

Nếu API nhận:

```axiom
send(view<T>)
```

thì semantics khác.

Nhưng một channel truyền owned `T` mặc định nên làm ownership transfer rõ ràng.

---

# 38. Bounded channel

Nên hỗ trợ:

```text
channel<T>(capacity)
```

với semantics:

```text
capacity > 0
```

Khi đầy:

```text
send
 ↓
Pending / block
```

tùy synchronous/asynchronous channel API.

---

# 39. Unbounded channel

Có thể tồn tại:

```text
unbounded_channel<T>()
```

nhưng allocation/backpressure semantics phải rõ.

Không giả định memory vô hạn.

---

# 40. Synchronous channel

Có thể có:

```text
sync_channel<T>(0)
```

Conceptually:

```text
send
    ↕
receive
```

Ownership transfer chỉ hoàn tất khi receiver nhận.

---

# 41. Channel synchronization

Successful send/receive có thể tạo happens-before theo channel contract.

Do đó:

```text
producer
    write(data)
       ↓
    send(data)
       ↓
    receive(data)
       ↓
consumer
    read(data)
```

safe.

---

# 42. Channel thay thế shared mutable state trong nhiều trường hợp

Thay vì:

```text
Arc<Mutex<State>>
```

có thể:

```text
owner thread
     ↓
 channel
     ↓
worker thread
```

Đây là design choice của library, không phải language restriction.

---

# 43. `Share` và Mutex

`Mutex<T>` có thể cung cấp:

```text
Send
Share
```

nếu semantics của implementation đáp ứng.

Nhưng `T` không nhất thiết phải `Share`, vì nó được bảo vệ bởi Mutex.

Ví dụ:

```text
Mutex<NonShareType>
```

có thể hợp lệ nếu chỉ một guard truy cập tại một thời điểm.

Đây là lý do `Share` phải là **type contract**, không phải property lan truyền đơn giản từ field.

---

# 44. Synchronization abstraction owns the proof boundary

Compiler không cần hiểu implementation bên trong của:

```text
Mutex
RwLock
Channel
Arc
```

để chứng minh toàn bộ algorithm.

Nó cần hiểu các semantic contracts:

```text
lock establishes exclusive access
unlock releases it

send transfers ownership
receive acquires ownership

atomic operation preserves ordering
```

---

# 45. Library synchronization contracts

Axiom cần một mechanism để standard library đánh dấu synchronization semantics.

Có thể dùng intrinsic traits/compiler-known traits:

```text
@sync
@acquire
@release
@atomic
```

Nhưng không nên expose quá nhiều annotation cho programmer.

Compiler nên biết standard synchronization types qua intrinsic semantic definitions.

---

# 46. Không biến mọi lock thành compiler primitive

Ví dụ:

```text
MyLock<T>
```

do user viết nên vẫn có thể hoạt động nếu implement đúng trait/protocol synchronization.

Nhưng compiler không thể tự tin rằng arbitrary:

```text
lock()
unlock()
```

là synchronization nếu không có contract.

Do đó cần một abstraction boundary.

---

# 47. `unsafe` synchronization

User có thể xây:

```text
SpinLock
MCSLock
TicketLock
RCU
HazardPointer
EpochGC
```

trong library/system layer.

Một số implementation có thể cần:

```text
unsafe
atomic
fence
raw pointer
```

Nhưng API safe bên ngoài phải khôi phục invariant.

---

# 48. Data-race freedom

Safe Axiom code phải đảm bảo:

```text
no concurrent conflicting ordinary memory accesses
```

trừ khi memory đó thuộc synchronization abstraction/atomic semantics.

Conflict:

```text
READ + WRITE
WRITE + WRITE
```

cùng vùng memory đồng thời.

---

# 49. Read/read

```text
READ + READ
```

safe nếu memory lifetime/provenance hợp lệ.

---

# 50. Atomic/ordinary interaction

Không được giả định:

```text
Atomic<T>
```

và:

```text
ordinary T
```

cùng storage có thể truy cập tùy ý.

Nếu một location được atomic access:

```text
ordinary mutable access
```

không được tự động coi là safe.

---

# 51. Volatile

Volatile không phải synchronization.

Ví dụ:

```text
volatile write
```

có ý nghĩa về observable machine/IO access.

Nó không tự tạo:

```text
happens-before
```

hoặc:

```text
data-race freedom
```

---

# 52. Thread-local storage

Axiom hỗ trợ:

```axiom
static thread_local counter: i32 = 0
```

conceptually:

```text
Thread A → counter_A
Thread B → counter_B
```

Không phải shared memory.

---

# 53. TLS lifetime

TLS có:

```text
per-thread storage identity
```

và lifetime gắn với thread/execution environment theo target contract.

Không được giả định TLS luôn có global process lifetime.

---

# 54. Global mutable state

```axiom
static var counter: i32 = 0
```

không tự động thread-safe.

Compiler phải reject unsafe concurrent access trong safe code.

Programmer cần:

```text
Atomic
Mutex
RwLock
```

hoặc synchronization abstraction phù hợp.

---

# 55. Static initialization

Không có hidden:

```text
constructor registry
```

để khởi tạo globals trước `main`.

Static initialization phải:

- compile-time constant
- hoặc explicit initialization mechanism

---

# 56. Thread startup

Hosted environment:

```text
OS
 ↓
Axiom startup
 ↓
main
```

Thread:

```text
OS thread
 ↓
Axiom thread entry
 ↓
closure/task
```

Startup wrapper tối thiểu và có thể được linker loại bỏ phần không dùng.

---

# 57. Thread stack

Thread stack size là execution/runtime property.

Ví dụ library:

```axiom
Thread.spawn_with_stack(size, work)
```

nếu target hỗ trợ.

Compiler không giả định mọi thread có cùng stack size.

---

# 58. Stack overflow

Stack overflow không nên trở thành undefined behavior trong safe code.

Target/runtime có thể:

- guard page
- trap
- OS signal
- explicit failure

Tùy profile.

---

# 59. CPU affinity

Không thuộc Core syntax.

Library/system API:

```text
Thread.set_affinity(...)
```

có thể target-specific.

---

# 60. Priority

Tương tự:

```text
Thread.set_priority(...)
```

là OS/runtime concern.

Không đưa vào Core language semantics.

---

# 61. Memory ordering

Concurrency primitives phải dùng memory model đã định nghĩa:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Không tạo một memory model thứ hai cho Thread/Mutex.

---

# 62. Happens-before

Các abstraction có thể thiết lập:

```text
spawn
join
send/receive
lock/unlock
atomic synchronization
future completion
```

nhưng mỗi API phải định nghĩa chính xác edge nào được tạo.

Compiler không được tự suy diễn mạnh hơn contract.

---

# 63. Spawn happens-before

Creation:

```text
parent
  writes X
  spawn(child)
```

Child phải thấy các writes được contract spawn công bố.

Conceptually:

```text
parent-before-spawn
        ↓
child-start
```

---

# 64. Join happens-before

```text
child
  writes X
  completes
      ↓
join
      ↓
parent reads X
```

completion → join synchronization.

---

# 65. Detached thread

Nếu detach:

```text
parent
    X
    │
    └── detached thread
```

parent không có implicit join synchronization.

Nếu cần synchronization:

```text
JoinHandle
Event
Channel
Atomic
```

phải explicit.

---

# 66. Thread panic

Nếu thread panic:

```text
Thread.join()
```

có thể trả:

```text
Result<T, ThreadError>
```

hoặc một thread-specific failure representation.

Panic không tự biến thành process-level Result.

---

# 67. Process abort

Nếu panic strategy:

```text
abort
```

thread panic có thể terminate process.

Đây là profile-level semantics.

---

# 68. Thread-local panic

Nếu unwind:

```text
thread
   panic
      ↓
cleanup owned values
      ↓
thread terminates
```

Nếu join handle tồn tại, caller có thể quan sát termination.

---

# 69. Concurrency và Drop

Một resource chỉ được Drop khi ownership kết thúc.

Ví dụ:

```text
Channel
  owns queued values
```

Khi channel bị Drop:

```text
queued values
    ↓
Drop
```

theo channel contract.

---

# 70. Closing channel

Channel nên có explicit:

```text
close()
```

hoặc Drop semantics định nghĩa sender/receiver disconnect.

Nhưng cần phân biệt:

```text
Drop sender
```

với:

```text
explicit protocol close
```

nếu protocol cần graceful shutdown.

---

# 71. Cancellation và channel

Cancellation không được làm mất ownership.

Ví dụ:

```text
send(data)
```

nếu operation pending rồi cancelled:

API phải quy định:

```text
data returned to caller
```

hoặc:

```text
channel owns data
```

Không được có ownership ambiguity.

---

# 72. Cancellation và Mutex

Nếu lock acquisition pending rồi cancellation:

```text
AsyncMutex.lock()
```

phải đảm bảo waiter cleanup.

Nếu lock đã acquired:

```text
Guard
```

phải Drop/unlock đúng.

---

# 73. Concurrency và FFI

FFI function không tự động được coi là thread-safe.

Ví dụ C API:

```text
extern "C" fn foo(...)
```

không cho compiler biết:

```text
Share
Send
reentrant
```

ABI contract phải khai báo semantics cần thiết.

---

# 74. C libraries

Wrapper nên tạo abstraction:

```text
struct CHandle {
    raw: *mut CThing
}
```

và định nghĩa:

```text
Send
Share
Drop
```

theo contract thực tế của C library.

Không đoán.

---

# 75. No implicit `Arc`

Axiom tuyệt đối không tự động:

```text
value
 ↓
Arc
```

chỉ vì compiler thấy nhiều threads.

Nếu cần shared ownership:

```axiom
let shared = Arc.new(data)
```

phải explicit.

---

# 76. No implicit locking

Không có:

```text
var x = ...
```

mà compiler âm thầm chuyển thành:

```text
Mutex<x>
```

Điều này phá predictability và performance model.

---

# 77. No hidden atomic promotion

Không có:

```text
i64
```

tự biến thành:

```text
Atomic<i64>
```

vì compiler phát hiện concurrency.

Atomicity là semantic property, không phải optimization tùy ý.

---

# 78. Compiler được phép optimize synchronization?

Có, nhưng chỉ nếu giữ nguyên semantics.

Ví dụ:

```text
lock
unlock
```

không thể bị loại bỏ nếu observable synchronization behavior thay đổi.

Compiler có thể:

- inline lock
- eliminate redundant local operations
- specialize uncontended path
- generate CPU instruction trực tiếp

nếu contract vẫn đúng.

---

# 79. Lock elision

Compiler/backend có thể phát hiện:

```text
lock
critical
unlock
```

và biết lock không observable trong execution context cụ thể.

Có thể eliminate nếu semantics cho phép.

Nhưng không được làm thay đổi synchronization observable behavior giữa threads.

---

# 80. False sharing

Không phải language safety issue.

Library/system có thể cung cấp:

```text
@align(cache_line)
```

hoặc padding.

Axiom không tự giả định cache line size.

---

# 81. NUMA

Không thuộc Core.

System library có thể cung cấp:

```text
NUMA allocation
CPU affinity
memory locality
```

Ownership model vẫn giữ nguyên.

---

# 82. Lock-free

Axiom không đánh đồng:

```text
Atomic
```

với:

```text
lock-free
```

Đã freeze:

```text
AATOM-29
AATOM-30
```

Lock-free capability phải query target/implementation.

---

# 83. Wait-free

Tương tự.

Một atomic operation có thể:

```text
atomic
but not lock-free
```

và:

```text
lock-free
but algorithm not wait-free
```

Đây là library/algorithm property.

---

# 84. Memory reclamation

Các thuật toán:

```text
Hazard Pointer
Epoch Based Reclamation
RCU
QSBR
```

không thuộc Core.

Chúng là advanced library/system abstractions.

Điều này rất quan trọng vì:

> synchronization ≠ memory reclamation.

---

# 85. Shared ownership

Core không có implicit reference counting.

Library có:

```text
Rc<T>
Arc<T>
Weak<T>
```

Semantics:

```text
Rc
    single-thread shared ownership

Arc
    multi-thread shared ownership
```

---

# 86. Weak references

`Weak<T>` không sở hữu object.

Nó cần:

```text
upgrade()
```

để lấy owning handle nếu object còn tồn tại.

Điều này giải quyết cyclic ownership:

```text
A → B
B → Weak<A>
```

---

# 87. Cyclic `Arc`

Không tự động garbage collect:

```text
Arc A → Arc B
Arc B → Arc A
```

cycle có thể leak logically.

Axiom không có GC để âm thầm sửa.

Programmer dùng:

```text
Weak
Handle
Arena
```

theo design.

---

# 88. Concurrency identity

Đây là nơi ba loại identity tiếp tục hữu ích:

```text
Value Identity
Storage Identity
Logical Identity
```

Concurrent systems nên ưu tiên:

```text
Handle<Entity>
```

thay vì:

```text
raw pointer
```

để giảm coupling với physical address.

---

# 89. Actor model

Actor không thuộc Core.

Nhưng library có thể implement:

```text
Actor
Mailbox
Message
```

trên:

```text
Task
Thread
Channel
```

Ownership model vẫn áp dụng.

---

# 90. Parallel loops

Axiom standard library có thể cung cấp:

```axiom
parallel_for(items, |item| {
    process(item)
})
```

Compiler/library phân tích:

```text
closure captures
Send
Share
```

và executor quyết định scheduling.

Không cần thêm:

```text
parallel for
```

vào grammar v0.1.

---

# 91. SIMD vs threads

Không trộn:

```text
SIMD
parallel execution
threads
GPU
```

Chúng là các execution strategies khác nhau.

Axiom semantic layer chỉ cần bảo đảm memory/access correctness.

---

# 92. Data parallelism

Library có thể map:

```text
map_parallel
reduce_parallel
```

trên worker pool.

Nếu operation thuần/độc lập, compiler có thể vectorize hoặc parallelize.

Nhưng automatic parallelization không được thay đổi observable behavior.

---

# 93. Deterministic execution

Concurrency vốn không deterministic về scheduling.

Axiom không yêu cầu:

```text
Thread A always before B
```

trừ khi synchronization tạo ordering.

Testing infrastructure có thể cung cấp:

```text
deterministic scheduler
```

để Oracle/test.

---

# 94. Race testing

Compiler correctness không phụ thuộc runtime race detector.

Tooling có thể cung cấp:

```text
race sanitizer
thread sanitizer
```

như optional diagnostic layer.

---

# 95. Deadlock

Compiler không thể tổng quát chứng minh mọi deadlock.

Axiom không cố tạo:

```text
global deadlock checker
```

cho Core v0.1.

Library/tooling có thể hỗ trợ:

```text
lock ordering annotations
deadlock detection
runtime diagnostics
```

---

# 96. Priority inversion

Đây là synchronization/runtime concern.

Mutex implementation có thể hỗ trợ:

```text
priority inheritance
priority ceiling
```

nếu target yêu cầu.

Không phải language semantic.

---

# 97. Reentrancy

Một function:

```text
foo()
```

không tự được coi là:

```text
reentrant
```

FFI/system APIs phải khai báo nếu reentrancy là một contract.

---

# 98. Interrupt context

Interrupt handlers là system-level function:

```axiom
@interrupt
fn handler(...)
```

nếu sau này hỗ trợ.

Không được sử dụng arbitrary:

```text
Mutex
heap
async
```

trong interrupt context trừ khi abstraction target cho phép.

Đây là target/profile concern.

---

# 99. Kernel/freestanding concurrency

Axiom phải cho phép:

```text
@freestanding
```

program tự quản:

```text
CPU
interrupt
scheduler
locks
memory
```

Không link standard thread runtime bắt buộc.

---

# 100. Core concurrency boundary

Cuối cùng mô hình nên là:

```text
             AXIOM CORE
                 │
      ┌──────────┼──────────┐
      │          │          │
   Ownership   Atomic     Send/Share
      │          │          │
      └──────────┼──────────┘
                 │
          Semantic safety
                 │
        ┌────────┴────────┐
        │                 │
      Library           System
        │                 │
 Thread / Task         OS / CPU
 Channel / Mutex      Scheduler
 Executor             Interrupt
 Arc / RwLock         TLS
```

Không:

```text
Core
 ↓
giấu một OS runtime
```

---

# 101. Bộ invariants chính thức

### ACONC-40 — Thread Is An Execution Context

### ACONC-41 — Task Is A Logical Execution Unit

### ACONC-42 — Future Is Distinct From Thread

### ACONC-43 — Thread Creation Is Not Implicit

### ACONC-44 — Task Creation Is Explicit

### ACONC-45 — Spawn Transfers Or Shares Ownership According To Explicit Contract

### ACONC-46 — Send Means Ownership Transfer Across Execution Contexts

### ACONC-47 — Send Does Not Imply Share

### ACONC-48 — Share Does Not Imply Mutable Access

### ACONC-49 — Ordinary Mutable State Is Not Implicitly Thread-Safe

### ACONC-50 — Shared Mutation Requires Synchronization Or Atomic Semantics

### ACONC-51 — Mutable Capability Does Not Imply Thread Safety

### ACONC-52 — Thread Join Establishes Completion Synchronization

### ACONC-53 — Detached Execution Is Explicit

### ACONC-54 — Safe Forced Thread Termination Is Not Core Semantics

### ACONC-55 — Cancellation Is Cooperative

### ACONC-56 — Mutex Guard Is Non-Copyable

### ACONC-57 — Mutex Guard Drop Releases Its Lock

### ACONC-58 — Synchronous Mutex Guards Cannot Cross Suspension

### ACONC-59 — Async Synchronization Uses Async-Aware Abstractions

### ACONC-60 — Read Guards Permit Concurrent Reads

### ACONC-61 — Write Guards Provide Exclusive Access

### ACONC-62 — Channel Send Transfers Ownership According To Its Type Contract

### ACONC-63 — Channel Synchronization Establishes Ordering Only According To Its Contract

### ACONC-64 — Atomicity Is Distinct From Locking

### ACONC-65 — Volatile Is Not Synchronization

### ACONC-66 — Atomic Is Not Necessarily Lock-Free

### ACONC-67 — Lock-Free Is Not Necessarily Wait-Free

### ACONC-68 — Memory Reclamation Is Distinct From Synchronization

### ACONC-69 — Shared Ownership Is Explicit

### ACONC-70 — Reference Counting Is Not Implicit

### ACONC-71 — Cyclic Shared Ownership Is Not Automatically Collected

### ACONC-72 — Weak References Do Not Own Their Targets

### ACONC-73 — Thread-Local Storage Has Per-Thread Storage Identity

### ACONC-74 — Global Mutable State Is Not Implicitly Synchronized

### ACONC-75 — Concurrency Does Not Imply A Global Runtime

### ACONC-76 — Synchronization Semantics Must Be Preserved By Optimization

### ACONC-77 — Safe Code Cannot Perform Conflicting Concurrent Ordinary Memory Access

### ACONC-78 — Spawn/Join Synchronization Must Be Explicitly Defined

### ACONC-79 — Cancellation Cannot Create Ownership Ambiguity

### ACONC-80 — Detached Execution Has No Implicit Join Guarantee

---

# Điểm rất quan trọng: Axiom đang hình thành một mô hình concurrency khá gọn

Không cần hàng chục loại reference/lifetime syntax.

Programmer chủ yếu phải hiểu:

```text
T
view<T>
mut_view<T>

Send
Share

Atomic<T>
Mutex<T>
RwLock<T>
Channel<T>
Arc<T>
```

và:

```text
move
spawn
join
await
```

Trong khi phần khó:

```text
alias analysis
escape analysis
capture analysis
Send analysis
Share analysis
suspension analysis
drop analysis
race verification
```

được compiler xử lý.

Đây chính xác là nguyên tắc:

> **Compiler Complexity Is Not Language Complexity.**

---

# Một điều cần khóa thêm về `Send` / `Share`

Tôi đề xuất **không cho programmer tùy tiện viết**:

```axiom
unsafe impl Send for T
```

như một cách “ép compiler tin”.

Nếu muốn override compiler proof, phải đi qua một boundary rõ ràng kiểu:

```axiom
unsafe impl Send for T {
    // explicit safety contract
}
```

và compiler vẫn phải kiểm tra những phần có thể kiểm tra.

Như vậy `unsafe` không trở thành:

```text
"tắt borrow checker"
```

mà là:

```text
"tôi chịu trách nhiệm cho invariant này"
```

Đúng với triết lý Axiom hiện tại.

---

# Phần tiếp theo

## Part XVIII — Unsafe · Raw Pointer · Provenance · Volatile · Intrinsics

Đây là phần **cực kỳ quan trọng đối với mục tiêu vượt C/C++ về usability nhưng vẫn giữ sức mạnh hệ thống**.

Ta sẽ khóa:

```text
unsafe
raw pointer
pointer arithmetic
address
provenance
null
unaligned access
volatile
atomic pointer
memory-mapped I/O
intrinsics
inline assembly
ABI escape hatch
FFI ownership
```

và đặc biệt phải giải quyết một vấn đề nền tảng:

> **Axiom làm thế nào để safe code cực kỳ đơn giản, nhưng khi xuống mức kernel/driver/allocator/compiler/runtime thì vẫn có toàn bộ sức mạnh mà C/C++ có — mà không biến `unsafe` thành một “vùng đất không luật”?**