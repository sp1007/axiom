# AXIOM LANGUAGE SPECIFICATION v0.1
# Part XVI — Async · Future · Coroutine · Cancellation

Mục tiêu của phần này:

> **Async là một control-flow abstraction, không phải một runtime model.**

Axiom không được rơi vào tình trạng:

```text
async
→ bắt buộc runtime
→ bắt buộc executor
→ bắt buộc heap
→ bắt buộc task object
→ bắt buộc scheduler
```

Thay vào đó:

```text
async source
    ↓
Future semantic
    ↓
state-machine lowering
    ↓
MIR
    ↓
optimizer
    ↓
native code
```

Executor chỉ xuất hiện nếu chương trình thực sự cần nó.

---

# 1. Async không phải thread

```axiom
async fn fetch() -> Result<Data, Error> {
    ...
}
```

không có nghĩa:

```text
new thread
```

và cũng không có nghĩa:

```text
spawn task
```

Nó chỉ định nghĩa một computation có thể **suspend và resume**.

---

# 2. Gọi async function không tự chạy computation

Ví dụ:

```axiom
let future = fetch()
```

semantic result là một `Future`.

Không nhất thiết request đã được thực thi.

Conceptually:

```text
fetch()
    ↓
Future<Output>
```

---

# 3. `.await` là suspension point

```axiom
let data = fetch().await?
```

`.await` nói:

> Nếu future chưa hoàn thành, computation hiện tại có thể suspend.

Nếu đã hoàn thành:

```text
Future
 ↓
Output
```

không cần suspension.

---

# 4. Async function được lowering thành state machine

Ví dụ:

```axiom
async fn compute() -> i32 {
    let a = load_a().await
    let b = load_b().await

    a + b
}
```

conceptually:

```text
State 0
  |
  | start load_a
  v
State 1
  |
  | await
  |
  +---- Pending ----> suspend
  |
  +---- Ready ------> a
                       |
                       v
                    State 2
                       |
                       | load_b
                       v
                    State 3
                       |
                       +---- Pending --> suspend
                       |
                       +---- Ready --> return a+b
```

Compiler có thể biểu diễn state machine hoàn toàn khác miễn semantics giống nhau.

---

# 5. Future là semantic abstraction

Axiom cần một khái niệm:

```text
Future<T>
```

nhưng không nhất thiết biến nó thành một runtime object.

Future có thể được:

- stack allocated
- embedded
- register/state scalarized
- heap allocated
- arena allocated
- statically optimized
- completely eliminated

tùy escape analysis.

---

# 6. Async không bắt buộc heap

Ví dụ:

```axiom
async fn add() -> i32 {
    1 + 2
}
```

có thể compile gần như:

```text
return 3
```

Không cần:

```text
malloc Future
```

---

# 7. Future có thể không tồn tại ở machine level

Nếu:

```axiom
let x = async_operation().await
```

và compiler chứng minh operation luôn synchronous/ready trong context đó, state machine có thể bị loại bỏ.

Do đó:

> Future là semantic abstraction, không phải bắt buộc runtime allocation.

---

# 8. Poll model

Một Future conceptually có operation:

```text
poll(context) -> Pending | Ready(T)
```

Nhưng `poll` không nhất thiết phải là public Core syntax.

Đây là implementation/runtime abstraction.

---

# 9. Waker

Khi Future chưa hoàn thành, nó cần cách báo:

```text
"hãy thử poll tôi lại"
```

Đây là responsibility của executor/runtime abstraction.

Không phải mọi async program đều cần một global waker runtime.

---

# 10. Executor không thuộc Core runtime bắt buộc

Axiom cho phép:

```text
std::async::Executor
```

hoặc executor của ứng dụng.

Core chỉ định nghĩa semantics của:

```text
async
await
Future
suspension
resume
```

Executor là library/system layer.

---

# 11. `async fn` không tự spawn

```axiom
async fn work() { ... }

work()
```

không tương đương:

```text
spawn(work)
```

Muốn chạy concurrent:

```axiom
spawn(work())
```

hoặc API tương ứng.

---

# 12. Sequential await

```axiom
let a = foo().await
let b = bar().await
```

không chạy `foo` và `bar` concurrently.

Semantics:

```text
foo
 ↓
await foo
 ↓
bar
 ↓
await bar
```

Nếu muốn concurrency:

```axiom
let fa = foo()
let fb = bar()

let a = fa.await
let b = fb.await
```

với Future semantics phù hợp.

---

# 13. Creating Future ≠ starting external operation

Điểm này phải rất rõ.

Axiom không yêu cầu mọi Future phải lazy hoặc eager ở mọi API.

Có hai loại abstraction có thể tồn tại:

```text
cold Future
hot operation
```

Nhưng semantics phải được API định nghĩa rõ.

Core language không tự giả định:

```text
Future creation
=
external operation started
```

---

# 14. Async state machine ownership

Ví dụ:

```axiom
async fn process() {
    let buffer = acquire_buffer()

    await_io().await

    use(buffer)
}
```

`buffer` sống qua await.

Compiler đưa ownership của `buffer` vào async state:

```text
State {
    buffer: Buffer
}
```

Nếu Future được heap allocate, state machine có thể nằm trên heap.

Nếu Future không escape, compiler có thể giữ trên stack.

---

# 15. Owned values được phép sống qua await

Đây là rule cốt lõi:

```text
Owned T
```

có thể sống qua `.await`.

Ví dụ:

```axiom
let data = load()
await_io().await
use(data)
```

hợp lệ nếu các type/operation khác hợp lệ.

---

# 16. `view<T>` không được sống qua await v0.1

Ví dụ:

```axiom
let v = view(data)

await_io().await

use(v)
```

→ compile error.

---

# 17. `mut_view<T>` cũng không được sống qua await

```axiom
let v = mut_view(data)

await_io().await

modify(v)
```

→ compile error.

Đây là một quyết định mạnh nhưng giúp async ownership model đơn giản hơn rất nhiều.

---

# 18. Vì sao không cho view qua await?

Nếu cho:

```text
view<T>
```

sống qua suspension, compiler phải chứng minh owner:

- không bị drop
- không bị relocate
- không bị mutable alias
- không bị thay đổi storage contract
- không bị transfer sang execution context khác

trong toàn bộ thời gian Future suspended.

Điều này rất dễ biến thành một phiên bản lifetime/borrow checker mà Axiom đang cố tránh ở source level.

Do đó v0.1:

> **Capability lifetime không cross suspension.**

---

# 19. Scoped workaround

Thay vì:

```axiom
let v = view(data)
await_io().await
use(v)
```

viết:

```axiom
{
    let v = view(data)
    use(v)
}

await_io().await

{
    let v = view(data)
    use(v)
}
```

Compiler dễ chứng minh hơn.

---

# 20. Mutable capability trước await

```axiom
{
    let v = mut_view(data)
    modify(v)
}

await_io().await
```

hợp lệ.

Capability đã kết thúc trước suspension.

---

# 21. Future ownership

Một Future có thể sở hữu dữ liệu:

```text
Future<T>
    owns
        Buffer
        State
        ...
```

Do đó Future có thể có:

```text
Move
Drop
Send
Share
```

properties tùy state machine.

---

# 22. Future có thể là non-Send

Ví dụ async state giữ resource chỉ hợp lệ trên một thread:

```text
Future<T>: !Send
```

Future đó không thể được đưa sang executor thread khác.

---

# 23. Send của Future

Điểm quan trọng:

> `Future: Send` phụ thuộc vào **state thực sự sống qua suspension**.

Không phải mọi local từng tồn tại trong function đều ảnh hưởng.

Ví dụ:

```axiom
async fn work() {
    {
        let local = ThreadLocalResource()
        use(local)
    }

    await_io().await
}
```

`local` đã chết trước await.

Nó không cần làm Future thành non-Send.

---

# 24. Compiler phân tích suspension-live state

Conceptually:

```text
all locals
    ↓
liveness analysis
    ↓
values live across await
    ↓
Send/Share analysis
```

Do đó compiler không áp dụng rule quá bảo thủ.

---

# 25. `spawn`

Conceptually:

```axiom
spawn(work())
```

có nghĩa:

```text
Future
 ↓
execution context
```

Nếu executor cho phép migration giữa threads:

```text
Future: Send
```

phải được thỏa.

---

# 26. `spawn_local`

Có thể có:

```axiom
spawn_local(work())
```

cho executor single-thread/local context.

Khi đó Future không nhất thiết `Send`.

Điều này tránh ép mọi async abstraction phải thread-safe.

---

# 27. Structured concurrency

Axiom nên ưu tiên API kiểu:

```text
scope
 ├── task A
 ├── task B
 └── task C
```

và scope kết thúc khi tasks hoàn thành/cancel theo policy.

Điều này giúp:

- ownership
- cleanup
- cancellation
- error propagation

dễ kiểm chứng.

---

# 28. Detached task

Nếu cần task sống độc lập:

```axiom
detach(task)
```

phải explicit.

Không có implicit background task.

---

# 29. Task ownership

Một spawned task conceptually sở hữu Future:

```text
spawn
 ↓
Task owns Future
```

Nếu caller không giữ Task handle, behavior phải theo API `detach`.

Không có hidden global task registry bắt buộc.

---

# 30. Cancellation

Cancellation trong Axiom là:

> **cooperative control flow**, không phải forced thread termination.

Executor có thể request:

```text
cancel
```

Future phải có cancellation-safe semantics.

---

# 31. Không có safe forced cancellation tại arbitrary instruction

Không được:

```text
kill task ngay giữa bất kỳ instruction nào
```

vì có thể cắt ngang:

- critical section
- resource update
- FFI operation
- invariant-sensitive mutation

Cancellation chỉ có hiệu lực tại cancellation-safe suspension/checkpoint.

---

# 32. Cancellation point

Ví dụ:

```axiom
await_io().await
```

có thể là cancellation point.

Future có thể bị cancelled khi đang pending.

Nhưng:

```text
normal synchronous code
```

không tự động bị thread-kill.

---

# 33. Dropping Future

Đây là quyết định quan trọng:

```axiom
let future = operation()
drop(future)
```

**không mặc định có nghĩa là hủy external operation.**

Vì Future có thể đã khởi động:

- network request
- GPU command
- OS I/O
- device operation

mà lifecycle của external operation độc lập với Future object.

Do đó:

> **Drop Future ≠ cancel external operation.**

---

# 34. Explicit cancellation handle

Nếu operation hỗ trợ cancellation:

```text
Operation
├── Future<Result>
└── CancellationHandle
```

có thể có:

```axiom
cancel(handle)
```

hoặc:

```axiom
operation.cancel()
```

Cancellation semantics phải được API định nghĩa rõ.

---

# 35. Future Drop

Nếu Future chưa hoàn thành:

```text
drop(future)
```

thì compiler phải cleanup state machine fields đang owned.

Ví dụ:

```text
Future
 ├── Buffer
 ├── Request
 └── State
```

Drop Future:

```text
Drop(Buffer)
Drop(Request)
Drop(State)
```

theo ownership/drop order.

---

# 36. Async Drop không thuộc Core v0.1

Không thêm:

```text
async fn drop(...)
```

hoặc:

```text
AsyncDrop
```

vào destruction mechanism mặc định.

Lý do:

```text
destruction
+
suspension
+
cancellation
+
partial initialization
```

tạo một lớp complexity rất lớn.

---

# 37. Async resource cleanup

Nếu resource cần async close:

```axiom
let resource = open().await?

resource.close().await?
```

phải explicit.

Không dựa vào destructor.

Tương tự nguyên tắc:

```text
Drop = guaranteed synchronous cleanup
close = fallible/async business operation
```

---

# 38. Drop không await

Destructor không được:

```text
await
```

vì Drop phải deterministic và không-suspend.

Điều này cũng giữ invariant:

> **Drop không tạo hidden scheduler dependency.**

---

# 39. Async + Result

Hoàn toàn độc lập:

```axiom
async fn fetch() -> Result<Data, Error>
```

`.await` trả về:

```text
Result<Data, Error>
```

rồi:

```axiom
let data = fetch().await?
```

`?` xử lý Result.

Không có exception runtime.

---

# 40. Async + panic

Nếu Future panic:

```text
Future
 ↓
panic
```

panic được quan sát tại task boundary hoặc theo panic strategy.

Nếu executor unwind:

```text
Future state cleanup
↓
unwind task
```

Nếu abort:

```text
process termination
```

---

# 41. Async panic không tự thành Result

Không biến:

```text
panic
```

thành:

```text
Result::Err
```

một cách implicit.

Nếu muốn recoverable error:

```axiom
Result<T, E>
```

---

# 42. Async function return ownership

```axiom
async fn make_buffer() -> Buffer {
    Buffer(...)
}
```

Future cuối cùng produce owned `Buffer`.

Không cần copy.

Ownership:

```text
state machine
 ↓
completion
 ↓
caller
```

---

# 43. Async recursive function

Naive:

```axiom
async fn recurse() {
    recurse().await
}
```

có thể tạo infinitely sized Future nếu representation yêu cầu inline recursive state.

Compiler phải phát hiện recursive future size problem.

---

# 44. Explicit indirection cho recursive async

Nếu cần:

```text
Box<Future>
```

hoặc executor/task indirection.

Điều này phù hợp quy tắc chung:

> Recursive value representation phải hữu hạn.

---

# 45. Async closure

Cho phép:

```axiom
let task = async || {
    ...
}
```

nếu grammar v0.1 hỗ trợ async closure.

Compiler tạo:

```text
closure environment
+
future state machine
```

Capture rules vẫn giống closure thường.

---

# 46. Async closure capture

Nếu:

```axiom
move async || {
    use(resource)
}
```

thì resource được move vào async closure/future.

Nếu không `move`, compiler chỉ cho phép capture mode nếu lifetime/capability semantics chứng minh được.

---

# 47. No implicit lifetime extension

Axiom không làm:

```text
reference
↓
"compiler cứ giữ owner sống lâu hơn"
```

một cách tùy tiện.

Compiler có thể extend physical storage lifetime để tối ưu, nhưng semantic owner/capability rules vẫn phải đúng.

---

# 48. Stable address và async

Không cần `Pin<T>` trong Core.

Nếu async state machine cần stable address vì implementation contract:

```text
storage contract
```

phải yêu cầu explicit stable storage.

Ví dụ conceptually:

```text
Box<Future>
```

có stable storage identity nếu Box contract yêu cầu.

---

# 49. Vì sao Axiom không cần `Pin`

Trong Axiom:

```text
Future
```

không expose trực tiếp invariant:

```text
"this object must never move"
```

cho programmer.

Compiler kiểm soát state-machine representation.

Nếu một implementation cần address stability, compiler/backend hoặc library storage abstraction chịu trách nhiệm.

Do đó:

```text
Pin
```

không cần trở thành Core type chỉ để phục vụ compiler implementation detail.

---

# 50. Khi address thực sự observable

Nếu programmer làm:

```text
raw_pointer = addr_of(future)
```

thì stable address trở thành explicit contract.

Từ đó compiler không được relocate storage nếu điều đó vi phạm contract.

Điều này hoàn toàn phù hợp:

```text
AMEM-21
AMEM-55
AMEM-61
```

---

# 51. Async FFI

Không tự giả định:

```text
extern "C" async fn
```

có ABI chuẩn.

Async ABI phụ thuộc runtime/executor convention.

Do đó v0.1:

> Async functions không được tự động trở thành C ABI functions.

Nếu FFI cần async:

```text
C callback
+
opaque operation handle
+
explicit polling/completion API
```

---

# 52. OS async I/O

Axiom standard library có thể wrap:

```text
epoll
io_uring
IOCP
kqueue
...
```

nhưng đây là implementation của executor/I/O library.

Language core chỉ biết:

```text
Future
await
suspend
resume
```

---

# 53. GPU async

GPU operation:

```text
launch(kernel)
```

có thể trả:

```text
GpuEvent
```

`GpuEvent` là synchronization/resource abstraction.

Nếu có async integration:

```text
await event
```

thì event phải giữ resource dependencies cần thiết.

Compiler không được đoán hidden GPU lifetime.

---

# 54. Async GPU ownership

Ví dụ:

```axiom
let buffer = DeviceBuffer(...)
let event = launch(buffer)

await event

use(buffer)
```

hợp lệ nếu event contract đảm bảo operation hoàn thành trước use.

Nếu:

```text
buffer
```

bị drop trước completion:

```text
launch(buffer)
drop(buffer)
```

API/ownership model phải ngăn điều đó.

---

# 55. Async + mutable capabilities

Không:

```text
mut_view<T>
 ↓
await
 ↓
mut_view<T>
```

v0.1.

Nhưng có:

```text
owned T
 ↓
await
 ↓
mut_view<T>
```

và compiler tạo capability mới sau await.

Đây là model rất sạch:

```text
ownership survives
capability does not
```

---

# 56. Async + concurrency

Async task không mặc định thread-safe.

Các properties:

```text
Future: Send
Future: !Send
```

được compiler xác định.

Nếu task chạy trên same-thread executor:

```text
spawn_local
```

không cần Send.

---

# 57. Async + Share

Một Future không mặc định Share.

Nếu nhiều execution contexts cùng truy cập:

```text
Future
```

phải có abstraction phù hợp.

Không tự biến Future thành thread-safe object.

---

# 58. Async critical section

Không cho:

```text
lock()
await
unlock()
```

với synchronous lock guard.

Rule đã freeze:

> **Synchronous lock guard không được sống qua suspension.**

Ví dụ:

```axiom
let guard = mutex.lock()

await operation()

use(guard)
```

→ compile error.

---

# 59. Async-aware lock

Nếu cần giữ logical lock qua async suspension, library phải cung cấp abstraction riêng:

```text
AsyncMutex
AsyncGuard
```

với semantics cancellation-aware.

Không tái sử dụng synchronous MutexGuard một cách nguy hiểm.

---

# 60. Cancellation và lock

Async cancellation không được làm:

```text
lock acquired
↓
task killed
↓
lock remains forever
```

Async synchronization primitive phải định nghĩa cancellation behavior.

Đây là responsibility của abstraction, không phải magic compiler.

---

# 61. Cancellation-safe resource

Mỗi async abstraction phải xác định:

```text
before suspension
after suspension
cancelled
dropped
completed
```

để tránh resource leak/inconsistent state.

Compiler bảo đảm ownership cleanup; library bảo đảm protocol semantics.

---

# 62. Future state machine và Drop

Conceptually:

```text
Future {
    state: State
    field_a: A
    field_b: B
}
```

Khi state thay đổi:

```text
State0
→ State1
```

fields không còn cần có thể được drop sớm.

Compiler có thể:

```text
drop field_a
```

ngay khi semantic lifetime kết thúc.

Không phải giữ tất cả state đến cuối Future.

---

# 63. Async optimization

Compiler có thể:

- state-machine minimization
- field liveness analysis
- stack allocation
- heap allocation elimination
- future fusion
- await elimination
- inlining
- devirtualization
- executor specialization
- coroutine splitting
- state compression

miễn semantics giữ nguyên.

---

# 64. Async không yêu cầu global runtime

Một program:

```axiom
fn main() {
    ...
}
```

không dùng async:

```text
không link async runtime
```

Program dùng async nhưng tự quản lý executor:

```text
chỉ link phần cần thiết
```

---

# 65. Runtime composition

Có thể có:

```text
program
├── Core
├── allocator
├── async executor
├── OS I/O
└── network
```

nhưng:

```text
program nhỏ
├── Core
└── startup
```

không kéo theo executor.

Đây là **capability-driven runtime composition**.

---

# 66. Async invariants

### AASYNC-20 — Async Is Control-Flow Abstraction

Async không phải thread.

### AASYNC-21 — Async Does Not Imply Thread Creation

### AASYNC-22 — Calling Async Function Produces Future Semantics

### AASYNC-23 — Await Is A Suspension Point

### AASYNC-24 — Future Does Not Require Heap Allocation

### AASYNC-25 — Executor Is Not Required By Language Core

### AASYNC-26 — Async State Is Ownership-Aware

### AASYNC-27 — Owned Values May Live Across Await

### AASYNC-28 — Ordinary Views Cannot Live Across Await In v0.1

### AASYNC-29 — Mutable Views Cannot Live Across Await In v0.1

### AASYNC-30 — Dropping Future Does Not Imply Cancellation Of External Operations

### AASYNC-31 — Future Drop Cleans Owned State

### AASYNC-32 — Drop Cannot Await

### AASYNC-33 — Async Cleanup Uses Explicit Async Operations

### AASYNC-34 — Cancellation Is Cooperative

### AASYNC-35 — Arbitrary Forced Task Termination Is Not Safe Core Semantics

### AASYNC-36 — Future Send Depends On Suspension-Live State

### AASYNC-37 — `spawn` May Require Send

### AASYNC-38 — Local Spawn Does Not Necessarily Require Send

### AASYNC-39 — Detached Execution Is Explicit

### AASYNC-40 — Structured Concurrency Is Library-Level

### AASYNC-41 — Sync Lock Guards Cannot Cross Await

### AASYNC-42 — Async Synchronization Requires Async-Aware Abstractions

### AASYNC-43 — Async Does Not Imply Pinning

### AASYNC-44 — Stable Address Is Explicit Storage Contract

### AASYNC-45 — Async ABI Is Not Implicitly C-Compatible

### AASYNC-46 — GPU Async Lifetime Must Be Explicit

### AASYNC-47 — Async Panic Preserves Panic Semantics

### AASYNC-48 — Async Result Preserves Result Semantics

### AASYNC-49 — Recursive Futures Must Have Finite Representation

### AASYNC-50 — Compiler May Optimize Away Future Machinery

---

# Quyết định quan trọng đã khóa

Có 3 quyết định tôi cho rằng đặc biệt phù hợp với mục tiêu Axiom:

### 1. Không có `Pin<T>` trong Core

Không biến implementation detail của coroutine thành một loại lifetime/storage bureaucracy cho programmer.

### 2. Không có `AsyncDrop`

```text
Drop = deterministic + synchronous + non-fallible
close/shutdown = explicit + có thể async + có thể Result
```

Rất sạch về mặt semantics.

### 3. `view`/`mut_view` không qua `.await`

Đây là trade-off có chủ ý:

```text
        Ownership
           │
           ▼
    ┌───────────────┐
    │   survives    │
    │    await      │
    └───────────────┘

        Capability
           │
           ▼
    ┌───────────────┐
    │ ends before   │
    │    await      │
    └───────────────┘
```

Nó giúp Axiom tránh việc programmer phải hiểu lifetime graph của async state machine.

---

# Part XVII — Concurrency · Threads · Tasks · Channels · Synchronization

Phần tiếp theo sẽ khóa **concurrency model hoàn chỉnh**, tách khỏi async:

```text
Thread
Task
Spawn
Join
Channel
Mutex
RwLock
Atomic
Send
Share
Structured concurrency
Detached task
Thread-local storage
Memory ordering
Data-race freedom
Cancellation
Thread termination
```

Điểm đặc biệt cần giải quyết là:

> **Axiom nên làm cho việc tạo thread/task đơn giản đến mức nào mà vẫn giữ được hiệu năng C/C++ và không biến compiler thành một runtime bắt buộc?**

Hướng hiện tại là:

```text
Core semantic:
    ownership
    Send
    Share
    atomic
    synchronization

Library:
    Thread
    Mutex
    RwLock
    Channel
    Executor
    Task
    ThreadPool
```

Tức là compiler biết **đủ để kiểm chứng safety**, nhưng không phải tự mang theo một scheduler/runtime khổng lồ.