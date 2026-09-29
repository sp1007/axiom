# AXIOM LANGUAGE SPECIFICATION v0.1 — Part V
## Concurrency · Send · Share · Threads · Synchronization · Atomics

Mục tiêu của phần này:

> **Concurrency không phải một memory model thứ hai. Nó là ownership + capability + synchronization được mở rộng sang nhiều execution context.**

Axiom không tạo một hệ thống riêng biệt kiểu:

```text
borrow checker
+
thread checker
+
async checker
+
atomic checker
```

Mà dùng chung semantic model.

---

# 1. Execution context

Axiom phân biệt:

```text
Execution Context
```

với:

```text
Thread
Task
Future
Coroutine
GPU invocation
```

Một execution context có:

```text
local state
control flow
capabilities
owned values
```

---

# 2. Thread

Thread là execution context có scheduling độc lập bởi OS/runtime.

Ví dụ:

```axiom
let t = spawn(fn() {
    work()
})
```

`spawn` tạo execution context mới.

---

# 3. Task

Task là execution context được executor quản lý.

Ví dụ:

```axiom
spawn(async {
    work().await
})
```

Task không nhất thiết tương ứng với OS thread.

---

# 4. Thread ≠ async task

Axiom không cho phép suy luận:

```text
async = thread
```

hay:

```text
thread = async
```

Đây là hai abstraction độc lập.

---

# 5. `Send`

`Send` trả lời câu hỏi:

> Một owned value có thể transfer ownership sang execution context khác hay không?

Ví dụ:

```axiom
let buffer = make_buffer()

spawn(move || {
    consume(buffer)
})
```

Nếu `Buffer: Send`:

```text
buffer
→ ownership transfer
→ child context
```

hợp lệ.

---

# 6. `Send` không phải `Share`

Một type có thể:

```text
Send
```

nhưng không:

```text
Share
```

Ví dụ một mutable state object có thể chuyển sang thread khác nhưng không an toàn để nhiều thread cùng truy cập.

Do đó:

```text
Send != Share
```

---

# 7. `Share`

`Share` trả lời:

> Một value/capability có thể được truy cập đồng thời bởi nhiều execution contexts hay không?

Ví dụ:

```text
Arc<ImmutableData>
```

có thể `Share`.

Nhưng:

```text
Arc<MutableData>
```

không tự động trở thành `Share`.

---

# 8. Hai chiều khác nhau

```text
Send
    ownership transfer

Share
    concurrent access
```

Bảng:

| Type | Send | Share |
|---|---:|---:|
| immutable data | thường Có | thường Có |
| unique mutable state | thường Có | thường Không |
| Mutex<T> | Có | Có |
| Atomic<T> | Có | Có |
| raw pointer | không mặc định | không |
| thread-local resource | tùy contract | không mặc định |

Các property này được compiler/library xác định.

---

# 9. Auto derivation

Compiler có thể tự suy ra:

```text
Send<T>
Share<T>
```

từ các thành phần của type.

Ví dụ:

```axiom
struct Point {
    x: f32
    y: f32
}
```

có thể tự động:

```text
Point: Send + Share
```

nếu các field đều thỏa semantics.

---

# 10. Không phải trait implementation tùy ý

Programmer không được khai báo:

```text
unsafe impl Share for DangerousType
```

rồi compiler bỏ qua semantic requirements.

`Send`/`Share` là **compiler-known concurrency properties**.

Unsafe implementation có thể tồn tại ở system layer nhưng phải chịu explicit proof contract.

---

# 11. Spawn ownership

```axiom
let data = load()

spawn(move || {
    process(data)
})
```

`move` ở closure capture xác định ownership capture.

Sau spawn:

```text
data → MOVED
```

ở parent.

---

# 12. Spawn không tự copy

Nếu:

```text
T: !Copy
```

thì:

```axiom
spawn(move || use(data))
```

không clone `data`.

Ownership được transfer.

---

# 13. Spawn và Send

Nếu execution context mới có thể chạy độc lập:

```text
captured owned values
```

phải đáp ứng:

```text
T: Send
```

nếu ownership crosses execution boundary.

---

# 14. `spawn_local`

Nếu executor đảm bảo task chạy cùng execution context:

```axiom
spawn_local(async {
    use(state)
})
```

không nhất thiết yêu cầu `Send`.

Nhưng vẫn phải obey:

```text
ownership
capability
lifetime
aliasing
```

---

# 15. `spawn_local` không phá Share safety

`spawn_local` không có nghĩa:

```text
"mọi reference đều an toàn"
```

Nếu task có thể interleave với owner hoặc task khác, alias rules vẫn áp dụng.

---

# 16. Thread Join

```axiom
let t = spawn(move || work())

let result = t.join()
```

`join` tạo synchronization boundary.

Sau successful join:

```text
child execution
→ completed
→ ownership/result transferred
→ happens-before parent continuation
```

---

# 17. Join và panic

Nếu child panic:

```text
join()
```

có thể trả task failure representation.

Ví dụ conceptual:

```text
JoinHandle<T>
    join() -> Result<T, TaskError>
```

Không cần exception runtime.

---

# 18. Detached thread

Nếu API hỗ trợ:

```axiom
spawn_detached(...)
```

thì ownership/resources của task thuộc task lifecycle.

Parent không được giả định task đã hoàn thành.

Detach phải explicit.

---

# 19. Structured concurrency

Axiom khuyến khích library API kiểu:

```text
scope {
    spawn(...)
    spawn(...)
}
```

Trong đó:

```text
scope lifetime
    bounds child lifetime
```

Đây là library abstraction, không phải bắt buộc language syntax.

---

# 20. Why structured concurrency?

Nó giúp compiler chứng minh:

```text
child cannot outlive scope
```

và giảm nhu cầu:

```text
global ownership
manual lifetime bookkeeping
```

---

# 21. Channel

Channel là ownership-transfer abstraction.

Ví dụ:

```axiom
let (tx, rx) = channel<Message>()

spawn(move || {
    tx.send(message)
})

let message = rx.receive()?
```

`send` chuyển ownership của `Message`.

---

# 22. Channel không copy mặc định

Nếu:

```text
Message: !Copy
```

thì:

```text
tx.send(message)
```

→ Move.

Không implicit serialization/copy trừ khi channel type/API yêu cầu.

---

# 23. Channel synchronization

Successful:

```text
send
→ receive
```

có synchronization semantics theo channel contract.

Điều này có thể thiết lập:

```text
happens-before
```

giữa producer và consumer.

---

# 24. Mutex

`Mutex<T>` cung cấp exclusive access.

Conceptually:

```text
Mutex<T>
    └── locked
          └── mut_view<T>
```

Khi lock:

```axiom
let guard = mutex.lock()
```

`guard` là owning synchronization guard.

---

# 25. MutexGuard

`MutexGuard<T>`:

```text
!Copy
Drop
```

Drop guard:

```text
unlock
```

Do đó:

```axiom
{
    let guard = mutex.lock()
    modify(guard)
}
```

kết thúc scope:

```text
guard.Drop
→ mutex.unlock
```

---

# 26. Guard → capability

Conceptually:

```text
MutexGuard<T>
    ↓
mut_view<T>
```

Guard vẫn phải sống trong khi `mut_view` được sử dụng.

---

# 27. Guard và Drop dependency

Ví dụ:

```axiom
let guard = mutex.lock()
let v = mut_view(guard)
```

`v` phụ thuộc vào:

```text
guard
```

Không được:

```axiom
drop(guard)
use(v)
```

---

# 28. RwLock

`RwLock<T>` cung cấp:

```text
read lock  → view<T>
write lock → mut_view<T>
```

Có thể có:

```text
N readers
```

hoặc:

```text
1 writer
```

nhưng không đồng thời conflict.

---

# 29. Lock guards không Copy

```text
MutexGuard
RwLockReadGuard
RwLockWriteGuard
```

đều:

```text
!Copy
Drop
```

vì copy guard sẽ gây semantic ambiguity về unlock ownership.

---

# 30. Lock guard không được cross await

Ví dụ:

```axiom
let guard = mutex.lock()

do_async().await

use(guard)
```

→ reject trong v0.1.

### ACONC-29
**Synchronous lock guards cannot cross suspension.**

---

# 31. Vì sao?

Nếu lock giữ qua `.await`:

```text
thread/task
    ↓
lock held
    ↓
suspend
    ↓
executor runs another task
```

có thể gây:

```text
deadlock
starvation
executor blocking
```

Axiom không muốn language-level semantics biến điều này thành vấn đề khó đoán.

Nếu cần async synchronization:

```text
AsyncMutex<T>
```

là abstraction riêng.

---

# 32. AsyncMutex

Library có thể cung cấp:

```axiom
let guard = mutex.lock_async().await
```

Async guard có semantic contract riêng.

Nhưng nó vẫn phải obey:

```text
ownership
capability
cancellation
```

---

# 33. Synchronization là type property

Không nên định nghĩa:

```text
lock()
```

chỉ như một operation đơn lẻ.

Quan trọng là:

```text
type/abstraction
    → establishes synchronization contract
```

### ACONC-30
**Synchronization is a type/abstraction property, not merely a property of one operation.**

---

# 34. Atomic

Atomic là type-level memory abstraction:

```text
Atomic<T>
```

Chỉ một số T được hỗ trợ tùy target.

Ví dụ:

```axiom
let counter: Atomic<u64> = Atomic.new(0)
```

---

# 35. Atomic operations

Core semantic operations:

```text
load
store
swap
compare_exchange
compare_exchange_weak
fetch_add
fetch_sub
fetch_and
fetch_or
fetch_xor
```

tùy type/target.

---

# 36. Memory orderings

Axiom v0.1:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

là core atomic semantic vocabulary.

---

# 37. Relaxed

```text
atomic.load(Relaxed)
```

đảm bảo atomicity của operation nhưng không tạo đầy đủ ordering với ordinary memory.

---

# 38. Acquire

Acquire load tạo ordering cần thiết để observe writes được publish bằng compatible Release operation.

---

# 39. Release

Release store/RMW publish prior operations trước synchronization boundary.

---

# 40. AcqRel

Dùng cho read-modify-write cần cả hai chiều ordering.

---

# 41. SeqCst

Sequential consistency cung cấp ordering mạnh nhất trong Axiom atomic model.

Compiler không được biến:

```text
SeqCst
```

thành ordering yếu hơn.

---

# 42. Failure ordering

CAS có:

```text
success_order
failure_order
```

Failure ordering không được mạnh hơn semantic rules cho phép.

Ví dụ conceptual:

```axiom
atomic.compare_exchange(
    expected,
    desired,
    AcqRel,
    Acquire
)
```

---

# 43. Atomic ≠ volatile

Axiom phân biệt:

```text
Atomic
```

và:

```text
volatile
```

Atomic:

```text
concurrency synchronization
```

Volatile:

```text
observable memory access
```

đặc biệt cho:

```text
MMIO
device registers
hardware interaction
```

Volatile không tự tạo inter-thread synchronization.

---

# 44. Atomic ≠ lock-free

`Atomic<T>` không guarantee:

```text
lock-free
```

Target có thể implement bằng internal lock nếu hardware không hỗ trợ native atomic.

Library/compiler có thể cung cấp query:

```text
is_lock_free<T>()
```

---

# 45. Ordinary memory và Atomic memory

Một location không được đồng thời được truy cập bằng:

```text
ordinary mutable access
```

và:

```text
atomic access
```

theo cách tạo data race.

Ví dụ conceptual:

```text
Atomic<u32> x
```

không thể tạo:

```text
mut_view<u32>
```

để bypass atomic semantics.

---

# 46. Atomic view

`Atomic<T>` không chuyển implicit thành:

```text
mut_view<T>
```

vì như vậy programmer có thể bypass ordering.

Muốn truy cập:

```text
atomic.load(...)
atomic.store(...)
```

phải dùng atomic API.

---

# 47. Data race

Safe Axiom program không được có data race.

Data race là concurrent access mà:

```text
at least one access is write
+
no valid synchronization
+
same/overlapping memory region
```

Safe compiler phải reject hoặc abstraction phải establish synchronization.

---

# 48. Race với disjoint fields

```text
Thread A → user.name
Thread B → user.age
```

có thể an toàn nếu compiler/abstraction chứng minh regions:

```text
DISJOINT
```

Đây là lợi thế của capability region model.

---

# 49. Race với same field

```text
Thread A → user.age WRITE
Thread B → user.age WRITE
```

không hợp lệ nếu không có synchronization.

---

# 50. Shared immutable data

Nhiều execution contexts có thể:

```text
view<T>
```

cùng đọc một immutable region nếu:

```text
T: Share
```

Read/read không tạo race.

---

# 51. Shared mutable data

Muốn nhiều execution contexts mutate cùng logical object:

```text
Arc<Mutex<T>>
```

hoặc:

```text
Arc<RwLock<T>>
```

hoặc:

```text
Arc<Atomic<T>>
```

tùy semantics.

Không có implicit shared mutable reference.

---

# 52. `Arc<T>` không đủ

```text
Arc<T>
```

chỉ giải quyết:

```text
ownership sharing
```

Không tự giải quyết:

```text
mutable synchronization
```

Do đó:

```text
Arc<MutableT>
```

không mặc định cho phép concurrent mutation.

---

# 53. `Arc<Mutex<T>>`

Semantic layers:

```text
Arc
 ↓
shared ownership
 ↓
Mutex
 ↓
exclusive synchronization
 ↓
mut_view<T>
```

Mỗi abstraction giải quyết một vấn đề duy nhất.

Đúng với nguyên tắc:

> **One Semantic Question, One Mechanism.**

---

# 54. Send/Share và capabilities

Capability bản thân không tự trở thành Send.

Một:

```text
view<T>
```

chỉ có thể cross execution context nếu capability's underlying storage và access contract cho phép.

Compiler phải kiểm tra:

```text
owner/storage
provenance
region
execution lifetime
```

---

# 55. Không cho view escape owner

Ví dụ:

```axiom
fn bad() -> view<Data> {
    let x = Data(...)
    view(x)
}
```

→ reject.

Đây là ownership violation, không phải concurrency-specific rule.

---

# 56. Cross-thread view

Ví dụ:

```axiom
let v = view(shared_data)

spawn(move || {
    read(v)
})
```

Chỉ hợp lệ nếu:

```text
v
underlying storage
execution contract
```

đáp ứng Share/Send semantics.

---

# 57. `mut_view` cross-thread

`mut_view<T>` có exclusive access.

Nếu chuyển sang thread:

```axiom
spawn(move || {
    modify(v)
})
```

có thể hợp lệ nếu ownership/storage capability transfer được phép.

Nhưng:

```text
parent
    mut_view
+
child
    mut_view
```

không thể cùng tồn tại.

---

# 58. Send là ownership transfer

Nếu:

```text
T: Send
```

thì:

```text
owner A
   ↓ Move
owner B
```

Sau transfer:

```text
A cannot access T
B owns T
```

Không có hai owners.

---

# 59. Share là concurrent capability

Nếu:

```text
T: Share
```

thì có thể tạo:

```text
view<T>
```

cho nhiều contexts.

Nhưng `Share` không tự cho phép mutation.

---

# 60. Happens-before

Axiom concurrency model cần một quan hệ:

```text
A happens-before B
```

được thiết lập bởi synchronization primitives.

Ví dụ:

```text
unlock
    → lock
```

trên cùng synchronization object có contract phù hợp.

Hoặc:

```text
send
    → receive
```

hoặc:

```text
thread completion
    → join
```

---

# 61. Compiler optimization

Compiler được phép reorder ordinary memory operations nếu không phá:

```text
observable single-thread semantics
+
atomic ordering
+
synchronization happens-before
+
volatile semantics
+
FFI contracts
```

---

# 62. Atomic fence

Core atomic model có thể cung cấp:

```text
fence(ordering)
```

khi target/library cần explicit ordering.

Fence semantics phải được backend preserve.

---

# 63. ABA

Axiom Core không giải quyết ABA bằng magic.

ABA là vấn đề của:

```text
lock-free algorithm
memory reclamation
pointer reuse
```

Library/system layer chịu trách nhiệm.

Các kỹ thuật có thể gồm:

```text
generation
hazard pointers
epoch reclamation
tagged pointers
```

---

# 64. Memory reclamation

Không được giả định:

```text
Atomic pointer
→ safe reclamation
```

Atomic chỉ giải quyết atomic access/order.

Lifetime/reclamation vẫn thuộc ownership/storage abstraction.

---

# 65. Atomic pointer

Raw atomic pointer nếu được hỗ trợ:

```text
Atomic<*mut T>
```

vẫn là raw pointer semantics.

Nó không tự trở thành:

```text
owned
valid
dereferenceable
```

---

# 66. Unsafe lock-free structures

Lock-free data structures có thể dùng:

```text
unsafe
atomic
generation
reclamation
```

nhưng phải đóng gói thành safe abstraction trước khi expose cho ordinary safe code.

---

# 67. Cancellation

Axiom cancellation là cooperative.

Không có:

```text
kill_thread_now()
```

an toàn trong Core.

---

# 68. Future cancellation

Dropping suspended Future:

```text
drop(future)
```

giải phóng Future state và các owned values bên trong.

Nhưng:

> Nó không tự động cancel mọi external operation mà Future đã kích hoạt.

### AASYNC-30
**Dropping a Future does not imply cancellation of external operations.**

Ví dụ network request có thể cần:

```text
CancellationToken
AbortHandle
OS cancellation API
```

theo library contract.

---

# 69. Cancellation và Drop

Nếu Future bị drop:

```text
Future state
    ↓
owned resources
    ↓
Drop
```

được cleanup deterministic.

Nhưng external side effect có thể đã escape Future.

---

# 70. Panic trong thread

Thread panic không nhất thiết propagate trực tiếp vào parent.

Thông thường:

```text
child panic
    ↓
thread terminates
    ↓
JoinHandle
    ↓
join() → failure
```

Nếu profile `panic=abort`, process có thể terminate ngay.

---

# 71. Panic trong task

Async task có thể lưu panic state:

```text
TaskError
```

và expose qua:

```text
join
await
```

tùy executor contract.

---

# 72. Panic ≠ cancellation

Hai trạng thái khác nhau:

```text
PANIC
CANCELLATION
```

Panic:

```text
program invariant/failure
```

Cancellation:

```text
control request to stop work
```

Không được nhập hai semantics này thành một.

---

# 73. Deadlock

Axiom không cam kết compiler có thể phát hiện mọi deadlock.

Deadlock là property của dynamic execution.

Compiler chỉ có thể reject một số statically provable violations.

Library/tooling có thể cung cấp:

```text
lock-order analysis
deadlock detector
trace
```

---

# 74. Lock ordering

Core không bắt programmer khai báo:

```text
lock A before B
```

trừ khi library/system abstraction yêu cầu.

Tooling có thể phát hiện:

```text
A → B
B → A
```

potential cycle.

---

# 75. Thread safety invariant

### ACONC-20
Safe Axiom code cannot create data races.

### ACONC-21
Send permits ownership transfer across execution contexts.

### ACONC-22
Share permits safe concurrent read sharing when its contract is satisfied.

### ACONC-23
Send and Share are independent properties.

### ACONC-24
Cross-context ownership transfer is a Move.

### ACONC-25
Concurrent access requires valid synchronization or immutable sharing.

### ACONC-26
Synchronization establishes explicit happens-before relations.

### ACONC-27
Atomic ordering is preserved by optimization.

### ACONC-28
Atomic access cannot be bypassed through ordinary mutable capability.

### ACONC-29
Synchronous lock guards cannot cross suspension.

### ACONC-30
Synchronization is a type/abstraction property.

---

# 76. Một ví dụ đầy đủ

```axiom
struct Counter {
    value: u64
}

fn increment(counter: mut_view<Counter>) {
    counter.value = counter.value + 1
}
```

Single-thread:

```axiom
var counter = Counter { value: 0 }

increment(mut_view(counter))
increment(mut_view(counter))
```

Compiler có thể chứng minh mỗi `mut_view` là ephemeral và không overlap theo thời gian.

---

## Multi-thread

Không thể đơn giản:

```axiom
spawn(move || increment(mut_view(counter)))
spawn(move || increment(mut_view(counter)))
```

vì ownership/capability conflict.

Thay vào đó:

```axiom
let counter = Arc.new(Mutex.new(Counter { value: 0 }))
```

Conceptually:

```text
Arc
 ↓
shared ownership
 ↓
Mutex
 ↓
exclusive lock
 ↓
mut_view<Counter>
```

Mỗi thread lần lượt obtains exclusive capability.

---

# 77. Atomic version

Nếu counter chỉ cần atomic integer:

```axiom
let counter = Atomic.new(0u64)

counter.fetch_add(1, SeqCst)
```

Không cần:

```text
Mutex
Arc<Mutex>
mut_view
```

Đây là ví dụ rất rõ của:

> **One semantic question, one mechanism.**

---

# 78. Shared immutable version

Nếu data immutable:

```axiom
let data = Arc.new(load_data())

spawn(move || {
    inspect(view(data))
})
```

Có thể nhiều thread đọc đồng thời.

Không cần Mutex nếu không có mutation.

---

# 79. Không tạo "concurrency pointer type"

Axiom không cần thêm:

```text
ThreadRef<T>
SharedRef<T>
MutableThreadRef<T>
AsyncRef<T>
```

Ownership/capability model đã đủ để mô tả:

```text
who owns
who reads
who writes
where capability lives
whether transfer is allowed
whether synchronization exists
```

---

# 80. Kiến trúc cuối cùng

Memory + concurrency hiện có thể mô hình hóa rất gọn:

```text
                     VALUE
                       │
                ┌──────┴──────┐
                │             │
             OWNERSHIP    CAPABILITY
                │             │
             Move/Copy     view/mut_view
                │             │
                └──────┬──────┘
                       │
                  EXECUTION
                       │
          ┌────────────┼────────────┐
          │            │            │
        Thread        Task         GPU
          │            │            │
          └────────────┼────────────┘
                       │
                SYNCHRONIZATION
                       │
          ┌────────────┼────────────┐
          │            │            │
        Channel       Lock        Atomic
```

Không có hệ thống ownership riêng cho thread, async và GPU.

---

# 81. Freeze Part V

Các điểm nền tảng đã khóa:

```text
Send ≠ Share
Move ≠ Copy
Ownership ≠ Capability
Capability ≠ Synchronization
Atomic ≠ Volatile
Thread ≠ Task
Panic ≠ Cancellation
Arc ≠ Mutex
Mutex ≠ Atomic
```

Đây là một kiến trúc rất quan trọng vì nó ngăn Axiom rơi vào tình trạng "mỗi tính năng mới thêm một loại reference mới".

---

# AXIOM LANGUAGE SPECIFICATION v0.1 — Part VI

Phần kế tiếp nên chuyển sang **Async/Await + Future + Coroutine State Machine**, vì concurrency model hiện đã đủ nền.

Ta sẽ chốt cụ thể:

```text
async fn
Future
Poll
Pending / Ready
await
state-machine lowering
live-across-await
ownership across await
view/mut_view across await
Send across await
spawn / spawn_local
executor
waker
cancellation
drop Future
async recursion
async trait
dyn async
stack allocation vs heap allocation
```

và đặc biệt kiểm tra lại một câu hỏi hiệu năng rất quan trọng:

> **Axiom async có thể compile thành state machine gần như zero-cost, không bắt buộc heap allocation hay executor runtime hay không?**