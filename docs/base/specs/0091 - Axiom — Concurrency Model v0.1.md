Đúng, phần “tự chuyển” trước đó chưa được thực hiện đúng.

Về **monitor 3 phút**: hệ thống Automation hiện tại chỉ hỗ trợ lịch **một lần / ngày / tuần / tháng**, không hỗ trợ chu kỳ 3 phút hoặc custom interval. Vì vậy tôi **không thể tạo một monitor 3 phút thật sự** mà không giả vờ là đã tạo.

Còn phần quan trọng: **tôi sẽ tiếp tục thiết kế Axiom ngay bây giờ**, không chờ bạn gõ “tiếp tục”.

# Axiom — Concurrency Model v0.1

Mục tiêu lần này là giải quyết bài toán khó nhất:

> **Concurrency mạnh như C/C++, nhưng không cần GC, không cần borrow checker ở source code, không cần lifetime annotation, không cần runtime bắt buộc, và vẫn ngăn data race trong safe code.**

## 1. Nguyên tắc trung tâm

Axiom không nên có một hệ thống concurrency riêng biệt.

Thay vào đó:

```text
Ownership
    ↓
Capability
    ↓
Send / Share
    ↓
Thread / Channel / Async
    ↓
Atomics / Locks
```

Tức là concurrency chỉ là **một trường hợp đặc biệt của ownership + access control**.

Đây là điểm rất quan trọng.

Ví dụ:

```axiom
var data = Vec<i32>()

thread.spawn(move || {
    data.push(10)
})
```

Compiler thấy:

```text
data
 └── MOVE
      └── thread
```

Không cần programmer viết:

```text
'static
'a
Send<T>
Sync<T>
```

hay bất kỳ lifetime annotation nào.

Compiler tự chứng minh điều kiện cần thiết.

---

# 2. `Send` và `Share`

Tôi đề xuất giữ đúng hai khái niệm cực kỳ nhỏ:

```axiom
trait Send {}
trait Share {}
```

### `Send`

Một giá trị có thể **chuyển quyền sở hữu** sang execution context khác.

Ví dụ:

```axiom
let buffer = Vec<u8>.new()

thread.spawn(move || {
    process(buffer)
})
```

Sau `spawn`:

```text
caller:
    buffer = MOVED

thread:
    buffer = OWNED
```

Không còn alias ownership.

---

### `Share`

Một giá trị có thể được **đọc đồng thời** bởi nhiều execution context.

Ví dụ conceptually:

```axiom
let config = Arc.new(Config(...))

thread.spawn(move || {
    read_config(config)
})

thread.spawn(move || {
    read_config(config)
})
```

Ở đây:

```text
Arc<Config>
    ├── thread A → READ
    └── thread B → READ
```

`Config` cần thỏa:

```text
Share
```

---

# 3. `Send != Share`

Đây là invariant rất quan trọng.

Một type có thể:

```text
Send = yes
Share = no
```

Ví dụ một resource có ownership độc quyền.

Hoặc:

```text
Send = no
Share = yes
```

Một số loại handle hệ thống có thể đọc từ nhiều context nhưng không được chuyển ownership.

Vì vậy **không được gộp hai trait này thành một `ThreadSafe`**.

### Invariant

**ACON-01 — Send/Share Separation**

> `Send` biểu diễn khả năng chuyển ownership giữa execution contexts. `Share` biểu diễn khả năng chia sẻ quyền đọc an toàn.

---

# 4. `thread.spawn`

API có thể cực kỳ đơn giản:

```axiom
thread.spawn(|| {
    work()
})
```

Compiler tự phân tích capture.

Ví dụ:

```axiom
let x = Vec<i32>.new()

thread.spawn(|| {
    print(x)
})
```

Nếu closure chỉ đọc:

```text
capture x
    ↓
READ capability
```

Nhưng `x` là local của thread cha.

Nếu closure sống lâu hơn scope:

```text
closure escapes
    +
x local
    ↓
không hợp lệ
```

Compiler không cần bắt programmer viết lifetime.

---

## 5. `move` closure

Khi muốn chuyển ownership:

```axiom
let x = Vec<i32>.new()

thread.spawn(move || {
    consume(x)
})
```

Ý nghĩa:

```text
x ──MOVE──> closure ──MOVE──> thread
```

Sau đó:

```axiom
use(x) // compile error
```

Đây là một trong những chỗ `move` nên **hiển thị rõ trên source**.

Vì nó thay đổi ownership observable.

---

# 6. Channel

Channel là abstraction cực kỳ phù hợp với triết lý Axiom.

```axiom
let (tx, rx) = channel<i32>()

thread.spawn(move || {
    tx.send(42)
})

let x = rx.receive()?
```

Ownership:

```text
producer
   │
   │ MOVE / SEND
   ▼
 channel
   │
   │ RECEIVE
   ▼
consumer
```

Không cần shared mutable memory.

Compiler có thể biết:

```text
send(T)
```

yêu cầu:

```text
T: Send
```

---

# 7. Channel không cần runtime bắt buộc

Đây là điểm Axiom cần khác nhiều language.

Nếu chương trình không dùng:

```text
thread
channel
async
mutex
atomic
```

thì binary không được tự động kéo theo concurrency runtime.

Ví dụ:

```axiom
fn main() {
    println("hello")
}
```

Không cần:

```text
thread scheduler
channel runtime
async executor
GC
RC runtime
```

Runtime component linker chỉ lấy phần cần thiết.

---

# 8. Mutex

Mutex nên là library abstraction.

Conceptually:

```axiom
let mutex = Mutex.new(data)

{
    let guard = mutex.lock()?
    guard.value += 1
}
```

`guard` là một resource:

```text
lock()
  ↓
Guard OWNED
  ↓
scope exit
  ↓
Drop
  ↓
unlock()
```

Như vậy RAII/Drop đã có sẵn.

Không cần:

```axiom
defer mutex.unlock()
```

và cũng không cần programmer nhớ unlock.

---

# 9. Nhưng Drop của Mutex phải đặc biệt

Có một vấn đề:

> Nếu `Drop` không được phép fail, unlock cũng không được fail theo semantics thông thường.

Do đó:

```text
Mutex.lock() → Result<Guard, Error>
Guard.Drop() → guaranteed unlock
```

Nếu primitive OS có lỗi catastrophic khi unlock, đó không còn là ordinary recoverable error; nó trở thành platform/runtime invariant hoặc panic/trap tùy implementation.

Điều này giữ nguyên:

```text
Drop = guaranteed cleanup
close() = fallible operation
```

---

# 10. RwLock

Axiom có thể có:

```text
RwLock<T>
```

với:

```text
read() → ReadGuard<T>
write() → WriteGuard<T>
```

Semantics:

```text
ReadGuard
    READ capability

WriteGuard
    WRITE capability
```

Compiler không cần hiểu toàn bộ implementation của lock để đảm bảo source-level ownership.

Nhưng compiler có thể tận dụng type semantics.

---

# 11. Atomics

Atomics **phải thuộc Core semantic layer**, dù API có thể nằm ở Core Library.

Ví dụ:

```axiom
let counter = Atomic<i64>.new(0)

counter.fetch_add(1, Ordering.Relaxed)
```

Các ordering:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Không nên có implicit ordering.

---

# 12. Vì sao không dùng `atomic<T>` cho mọi thứ?

Vì atomic không giải quyết:

```text
invariant nhiều field
```

Ví dụ:

```text
balance
transaction_state
owner
```

Không thể biến toàn bộ thành vài atomic rồi mặc định an toàn.

Axiom cần phân biệt:

```text
Atomic state
```

và:

```text
Synchronized compound state
```

Compound state dùng:

```text
Mutex
RwLock
Channel
Actor
```

hoặc lock-free algorithm explicit.

---

# 13. Lock-free

Axiom **không nên cố đưa lock-free programming thành một abstraction an toàn hoàn toàn trong Core**.

Ví dụ CAS:

```axiom
atomic.compare_exchange(
    expected,
    desired,
    Ordering.AcqRel,
    Ordering.Acquire
)
```

Đây là primitive.

Nhưng một cấu trúc:

```text
lock-free queue
hazard pointers
epoch reclamation
ABA prevention
```

nên là library/system-level abstraction.

Compiler cung cấp:

```text
atomic
ownership
alignment
memory ordering
```

Còn algorithm chịu trách nhiệm invariant của nó.

Điều này cực kỳ quan trọng để Axiom không biến thành một ngôn ngữ quá phức tạp.

---

# 14. Memory ordering là semantic, không phải optimization hint

Compiler **không được** làm:

```text
Release → Relaxed
```

chỉ vì nghĩ rằng nhanh hơn.

Ordering là observable concurrency semantics.

Do đó:

```text
Atomics
   ↓
Verified MIR
   ↓
LIR
```

phải giữ chính xác ordering.

Backend chỉ được chọn instruction sequence tương đương.

---

# 15. `volatile` không phải atomic

Axiom phải khóa rõ:

```text
volatile ≠ atomic
```

`volatile` dùng cho:

```text
MMIO
device registers
memory-mapped hardware
external side effects
```

Atomic dùng cho:

```text
inter-thread synchronization
```

Ví dụ:

```axiom
unsafe {
    device.status.read_volatile()
}
```

không thể dùng volatile để thay mutex/atomic.

---

# 16. Async

Đây là phần rất đáng chú ý.

Axiom không nên biến:

```axiom
async fn download()
```

thành:

```text
runtime task object
+
heap allocation
+
executor
```

mặc định.

Thay vào đó:

```text
async function
      ↓
state machine
      ↓
Future-like concrete state
```

Compiler có thể biến:

```axiom
async fn foo() {
    let a = await get_a()
    let b = await get_b()
    process(a, b)
}
```

thành conceptually:

```text
State0
   ↓ await
State1 { a }
   ↓ await
State2 { a, b }
   ↓
return
```

Nếu compiler chứng minh state machine không cần heap:

```text
stack/register/inline
```

Nếu caller cần lưu lâu:

```text
heap/arena/etc.
```

Không có mandatory allocation.

---

# 17. `async` không đồng nghĩa với thread

Axiom phải khóa invariant:

```text
async != thread
```

`async` chỉ biểu diễn:

```text
may suspend
```

Thread biểu diễn:

```text
independent execution context
```

Do đó:

```axiom
async fn foo()
```

không tự tạo thread.

---

# 18. `await` và `mut_view`

Một quyết định quan trọng:

```axiom
async fn process(mut_view<Data> data) {
    await something()
    data.update()
}
```

Không nên cho phép `mut_view` sống qua `await` trong v0.1.

Vì `await` có thể:

```text
suspend
resume elsewhere
```

và capability mutable có thể tồn tại trong khoảng suspension.

Do đó:

```text
mut_view + await
        ↓
reject
```

trừ khi compiler chứng minh được một mô hình executor rất chặt chẽ.

V0.1 nên đơn giản và an toàn.

---

# 19. Read-only view qua await

`view<T>` cũng không mặc định được phép sống qua `await`.

Chỉ cho phép nếu compiler chứng minh:

```text
owner remains alive
+
storage remains stable
+
capability remains valid
+
no conflicting mutation
```

Nếu không chứng minh được:

```text
reject
```

Programmer không cần viết lifetime.

---

# 20. Async task ownership

Task phải **own state của chính nó**.

Conceptually:

```text
async closure
    ↓
captured state
    ↓
state machine
```

Nếu:

```axiom
let buffer = Buffer.new()

spawn(async move {
    await send(buffer)
})
```

thì:

```text
buffer
   ↓ MOVE
task state
```

Task có ownership.

Nếu task bị cancellation:

```text
task state
   ↓ Drop
resources released
```

Đây là lý do model ownership hiện tại rất mạnh: **async không cần một memory-management model mới**.

---

# 21. Cancellation

Cancellation không nên cưỡng chế phá task ở bất kỳ instruction nào.

Axiom dùng:

> **Cooperative cancellation**

Task kiểm tra cancellation tại suspension points hoặc explicit checkpoints.

```text
RUNNING
   ↓
CANCEL_REQUESTED
   ↓
next cancellation point
   ↓
CANCELLED
   ↓
Drop task state
```

Không được:

```text
force destructor halfway through arbitrary operation
```

Điều này tránh rất nhiều class bug.

---

# 22. Structured concurrency

Nên hỗ trợ ở library layer:

```text
scope.spawn(...)
scope.wait(...)
```

Concept:

```text
parent scope
 ├── child task A
 ├── child task B
 └── child task C
```

Khi scope kết thúc:

```text
children must finish
```

hoặc cancellation/join policy rõ ràng.

Detached task phải **explicit**:

```axiom
task.detach()
```

Không nên để:

```text
spawn()
```

mặc định tạo orphan background task.

---

# 23. Nhưng không ép structured concurrency toàn bộ language

Đây là abstraction library.

Low-level systems code vẫn có thể:

```text
thread.create()
thread.detach()
```

nếu programmer thực sự muốn.

Language core chỉ đảm bảo:

```text
ownership / Send / Share / memory safety
```

---

# 24. Lock-free memory reclamation

Đây là một trong những vấn đề khó nhất của Axiom.

Ví dụ:

```text
Thread A → đọc node
Thread B → remove node
Thread B → free node
Thread A → tiếp tục đọc
```

Ownership thông thường không giải quyết được ngay vì lock-free structure cần **deferred reclamation**.

Axiom không nên đưa:

```text
HazardPointer
Epoch
RCU
```

vào language core.

Thay vào đó:

```text
unsafe/system implementation
        +
safe library API
```

Library có thể cung cấp:

```text
Epoch<T>
Hazard<T>
AtomicShared<T>
```

Compiler vẫn kiểm tra phần ownership thông thường, còn library abstraction chịu trách nhiệm memory reclamation protocol.

---

# 25. Safe lock-free API

Mục tiêu:

```text
unsafe implementation
          ↓
safe abstraction
```

Ví dụ người dùng:

```axiom
queue.push(value)
queue.pop()
```

không cần biết hazard pointer.

Nhưng implementation:

```text
unsafe {
    atomic CAS
    pointer manipulation
    reclamation
}
```

Điều này phù hợp với triết lý:

> **Unsafe complexity should be concentrated, not spread across application code.**

---

# 26. Data-race safety invariant

Axiom v0.1 khóa:

### ACON-02

> Safe code cannot create a data race.

Định nghĩa:

```text
concurrent WRITE + READ
```

hoặc:

```text
concurrent WRITE + WRITE
```

trên cùng logical region mà không có synchronization hợp lệ → compile error.

READ + READ:

```text
OK
```

---

# 27. Ownership + concurrency unified

Cuối cùng ta có:

```text
                 OWNERSHIP
                     │
        ┌────────────┼────────────┐
        │            │            │
      READ         WRITE         MOVE
        │            │            │
     Share        exclusive      Send
        │            │            │
        └────────────┼────────────┘
                     │
             Concurrency Safety
```

Đây là một kiến trúc rất sạch.

Không cần:

```text
GC
borrow syntax
lifetime syntax
thread-safe object hierarchy
runtime memory manager
```

---

# 28. Bộ invariant concurrency

Tôi chốt thêm:

```text
ACON-01  Send/Share Separation
ACON-02  No Data Race in Safe Code
ACON-03  Ownership Transfer Across Contexts
ACON-04  Spawn Capture Verification
ACON-05  Borrowed Local Cannot Escape
ACON-06  Explicit Move Capture
ACON-07  Channel Requires Send
ACON-08  Shared Mutable State Requires Synchronization
ACON-09  Atomic Ordering Preservation
ACON-10  Volatile Is Not Atomic
ACON-11  Async Is Not Thread
ACON-12  Async State Owns Captures
ACON-13  No Mandatory Async Allocation
ACON-14  Await Is Suspension Boundary
ACON-15  Mutable Capability Cannot Cross Await in v0.1
ACON-16  Read Capability Across Await Requires Proof
ACON-17  Cancellation Is Cooperative
ACON-18  Cancellation Runs Resource Cleanup
ACON-19  Detached Execution Is Explicit
ACON-20  Structured Concurrency Is Library-Level
ACON-21  Lock-Free Is Library/System-Level
ACON-22  Memory Reclamation Is Not Core
ACON-23  Unsafe Does Not Erase Type/Ownership State
ACON-24  Synchronization Semantics Are Observable
ACON-25  No Mandatory Concurrency Runtime
ACON-26  Concurrency Abstractions Are Erasable
```

## Kết quả

Đến đây Axiom có một mô hình khá thống nhất:

```text
              Axiom Value
                   │
              Ownership
                   │
          ┌────────┴────────┐
          │                 │
       Capability        Transfer
          │                 │
    READ / WRITE          Send
          │                 │
       Share          Thread/Channel
          │
    Synchronization
          │
   Atomic / Mutex / RwLock
          │
       Async
          │
    State Machine
```

**Không có một “concurrency runtime” khổng lồ nằm bên dưới tất cả.**

---

### Tiếp tục tự động → topic kế tiếp

Phần tiếp theo cần khóa là **Atomic + Memory Ordering + Lock-free Memory Model**, bởi đây là nền móng để quyết định chính xác Axiom có thể đạt hiệu năng C/C++ đến mức nào mà vẫn giữ safe concurrency.

Tôi sẽ tiếp tục từ đó trong lượt kế tiếp thay vì chờ bạn gõ lại `tiếp tục`.