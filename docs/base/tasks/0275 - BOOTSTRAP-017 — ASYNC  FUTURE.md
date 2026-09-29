Tiếp tục với **BOOTSTRAP-017 — Async / Future / State Machine**.

Đây là phần cần thiết để hoàn thiện mô hình execution của Axiom. Mục tiêu là **async không trở thành một runtime đặc biệt**, và `async/await` cuối cùng biến thành ordinary state machine + scheduler library.

# BOOTSTRAP-017 — ASYNC / FUTURE

## 1. Nguyên tắc lõi

> **Async là control-flow abstraction, không phải thread.**

Axiom phân biệt:

```text
Thread   = OS execution resource
Fiber    = stackful user-space execution context
Task     = schedulable computation
Future   = state machine
Async    = syntax/control-flow abstraction
```

Không được nhập tất cả thành một khái niệm.

---

# 2. `async fn`

Ví dụ:

```axiom
async fn download(url: String) -> Result<Data, Error> {
    let response = await http_get(url)?;
    return await response.read()?;
}
```

Gọi:

```axiom
let f = download(url);
```

**không chạy function ngay**.

Nó tạo một Future.

Conceptually:

```text
download(url)
        ↓
Future< Result<Data, Error> >
```

---

# 3. `async` không đồng nghĩa spawn

Đây là nguyên tắc rất quan trọng:

```axiom
let f = download(url);
```

không có nghĩa:

```text
new thread
new task
scheduler.spawn()
```

Muốn chạy concurrent:

```axiom
spawn(download(url));
```

hoặc executor tương ứng.

---

# 4. Future là state machine

Ví dụ:

```axiom
async fn foo() -> i32 {
    let a = await get_a();
    let b = await get_b();

    return a + b;
}
```

Compiler có thể tạo:

```text
FutureState {
    state: StateId,

    a: i32,
    b: i32,
    future_a: ...,
    future_b: ...
}
```

với states:

```text
START
  ↓
WAIT_A
  ↓
WAIT_B
  ↓
DONE
```

Nhưng đây là compiler-generated representation.

---

# 5. Future không phải object runtime bắt buộc

Không định nghĩa:

```text
Future = heap object + vtable + refcount
```

Đúng là:

```text
Future = semantic state machine
```

Storage có thể:

```text
register
stack
inline
caller-owned
heap
arena
```

tùy escape/storage analysis.

---

# 6. Future type là anonymous concrete type

Mỗi:

```axiom
async fn foo(...)
```

có một compiler-generated Future type.

Conceptually:

```text
FutureType#42
```

Không cần runtime name.

---

# 7. Future chứa gì?

Chỉ lưu state cần thiết để tiếp tục sau suspension.

Ví dụ:

```axiom
async fn foo() {
    let x = calculate();
    await bar(x);
    use(x);
}
```

`x` sống qua `await`.

→ phải nằm trong Future state.

Nếu:

```axiom
let temporary = calculate();
use(temporary);
await bar();
```

và `temporary` không còn dùng sau await:

→ không cần đưa vào Future.

---

# 8. State-field liveness

Compiler pass:

```text
StateFieldLiveness
```

tính:

```text
value live across suspension?
```

Chỉ những value cần thiết mới được materialize vào state machine.

Đây là yếu tố quan trọng để async không tạo object khổng lồ.

---

# 9. `.await`

Semantics:

```text
await future
```

conceptually:

```text
poll(future)
```

Nếu:

```text
READY(value)
```

→ tiếp tục.

Nếu:

```text
PENDING(waker)
```

→ lưu state và suspend.

---

# 10. Future poll model

Compiler/library interface conceptually:

```text
enum Poll<T> {
    Ready(T),
    Pending,
}
```

Executor:

```text
loop {
    match future.poll(context) {
        Ready(value) => complete(value),
        Pending => wait_for_wake(),
    }
}
```

Đây là execution model.

Executor không cần biết source async semantics.

---

# 11. Waker

Future khi Pending cần cách báo executor:

```text
Waker
```

Conceptually:

```text
future
  ↓
Pending
  ↓
register waker
  ↓
I/O/event completes
  ↓
wake()
  ↓
task → READY
```

`wake()` phải idempotent về mặt scheduling.

Nhiều wake:

```text
wake()
wake()
wake()
```

không được tạo ra trạng thái scheduler sai.

---

# 12. Scheduler không nằm trong Core

Axiom Core không có:

```text
global executor
global event loop
global async runtime
```

Có thể có:

```text
std::async
runtime::executor
tokio-like library
embedded executor
GUI executor
```

nhưng tất cả là library/runtime profile.

---

# 13. `spawn`

Ví dụ:

```axiom
spawn(download(url));
```

`spawn` là API scheduler.

Semantics:

```text
Future
  ↓
Task
  ↓
Scheduler
```

Không phải language primitive bắt buộc.

---

# 14. Task

Task là:

```text
Future + scheduling metadata
```

Conceptually:

```text
Task {
    future_state
    scheduler_link
    wake_state
}
```

Metadata phải nhỏ.

Không nhúng:

```text
large allocator
large scheduler
thread
stack
```

vào mỗi Task.

---

# 15. Future migration

Task có thể chuyển worker/thread khác nếu Future state thỏa:

```text
Send
```

Ví dụ:

```axiom
spawn(async move {
    process(data).await;
});
```

Compiler kiểm tra state live qua suspension.

Nếu state chứa non-Send:

```text
spawn(...)
```

→ reject.

---

# 16. `spawn_local`

Nếu không muốn migration:

```axiom
spawn_local(async {
    use(local_state).await;
});
```

Future không cần Send để chạy trên execution domain affine.

Nhưng lifetime vẫn phải hợp lệ.

---

# 17. Send của Future

Không đơn giản:

```text
Send(Future)
iff Send(all values anywhere)
```

Chính xác hơn:

> Future phải Send nếu state có thể được di chuyển qua execution domain và mọi state có thể tồn tại tại điểm migration đều đáp ứng Send.

Compiler có thể tính:

```text
FutureSendAnalysis
```

dựa trên:

```text
state fields
suspension points
execution domain
```

---

# 18. View không được qua await mặc định

Ví dụ:

```axiom
async fn bad(x: view<Data>) {
    await something();
    use(x);
}
```

Nếu `x` là borrowed capability phụ thuộc storage không có contract phù hợp:

```text
reject
```

Vì giữa hai điểm:

```text
before await
after await
```

Future có thể bị:

- suspend
- migrate
- move
- store lâu hơn stack frame

---

# 19. Tại sao không có lifetime annotation?

Không bắt programmer viết:

```text
Future<'a>
```

hay:

```text
async fn foo<'a>(...)
```

Compiler tự phân tích:

```text
owner
provenance
capability
suspension
escape
```

Nếu chứng minh được hợp lệ → compile.

Không chứng minh được → diagnostic.

---

# 20. Exception: explicit storage contract

Có thể có trường hợp view sống qua await hợp lệ.

Ví dụ resource có:

```text
stable storage
execution-domain affinity
```

và API explicitly bảo đảm.

Khi đó compiler có thể cho phép.

Nhưng đây không phải default.

---

# 21. Stable address không đồng nghĩa Pin

Axiom không đưa:

```text
Pin<T>
```

vào Core.

Nếu một Future hoặc resource cần stable address:

```text
storage contract
```

phải nói rõ.

Ví dụ:

```text
StableStorage<T>
```

là một abstraction storage, không phải language-wide lifetime machinery.

---

# 22. Future move

Future có thể move trước khi bắt đầu:

```text
Future
 ↓ Move
Task storage
```

Điều này không có nghĩa:

```text
physical memcpy
```

như ownership model đã định nghĩa.

Compiler có thể:

- caller allocate
- construct directly in task
- eliminate temporary

---

# 23. Future Drop

Nếu Future bị drop khi chưa hoàn thành:

```text
drop(future)
```

thì compiler phải Drop các state fields đã initialized.

Nhưng:

> **Drop Future không mặc định có nghĩa là cancel external operation.**

Ví dụ:

```text
OS I/O
network request
GPU command
```

có thể vẫn đang chạy.

---

# 24. Cancellation là abstraction riêng

Nếu muốn cancel:

```text
CancellationToken
CancellationHandle
```

hoặc tương ứng.

Ví dụ:

```axiom
let token = CancellationToken();

spawn(async move {
    process(token).await;
});
```

Cancellation phải được cooperative.

---

# 25. Không force-kill Future

Không có:

```text
kill(future)
```

theo nghĩa cưỡng ép giải phóng khi external operation vẫn đang sử dụng buffer.

Cancellation phải đảm bảo:

```text
external operation
↓
stop/cancel acknowledged
↓
resource safe
↓
Future can drop
```

---

# 26. Async Drop không có

Không cho:

```text
async drop(x)
```

vì Drop:

- deterministic
- non-fallible
- synchronous

Nếu cleanup cần await:

```axiom
await resource.close();
```

phải được gọi explicit trước khi resource bị Drop.

---

# 27. Ví dụ

```axiom
let file = open_async(...).await?;

file.close().await?;
```

Sau đó:

```text
Drop(file)
```

chỉ là final synchronous cleanup.

---

# 28. `?` trong async

Ví dụ:

```axiom
async fn foo() -> Result<Data, Error> {
    let x = await get()?;
    return Ok(x);
}
```

`?` vẫn là:

```text
CFG branch
```

không phải exception.

Nếu `get()` trả Err:

```text
cleanup
↓
Future Ready(Err(...))
```

---

# 29. Panic trong async

```axiom
async fn foo() {
    panic();
}
```

Future hoàn thành theo panic profile:

```text
panic=abort
```

hoặc:

```text
panic=unwind
```

Không có một async exception system riêng.

---

# 30. Async recursion

Ví dụ:

```axiom
async fn f() {
    await f();
}
```

Future type vô hạn nếu biểu diễn trực tiếp:

```text
Future<F>
  contains Future<F>
      contains Future<F>
          ...
```

Compiler phải reject hoặc yêu cầu indirection.

Ví dụ conceptual:

```text
Box<Future>
```

hoặc explicit dynamic abstraction.

---

# 31. Async state machine lowering

Pipeline:

```text
Typed HIR
    ↓
Async Analysis
    ↓
Suspension Point Analysis
    ↓
State Field Liveness
    ↓
Future Layout
    ↓
State Machine
    ↓
MIR
```

Sau đó backend không cần biết:

```text
async
await
Future
```

nếu đã lower hoàn toàn.

---

# 32. MIR representation

Có thể dùng:

```text
AWAIT future, suspension_id
```

ở semantic MIR trước lowering.

Sau lowering:

```text
SWITCH state
...
POLL future
...
STORE state
RETURN Pending
...
```

---

# 33. Suspension point

Mỗi:

```text
await
```

có:

```text
SuspensionPointId
```

Ví dụ:

```text
Await #0
Await #1
Await #2
```

Compiler dùng để tính:

- state
- live variables
- Drop
- Send
- capability validity
- debug mapping

---

# 34. Future state

Conceptually:

```text
enum State {
    Start,
    Await0 {
        x: X,
        future: F0,
    },
    Await1 {
        x: X,
        y: Y,
        future: F1,
    },
    Done,
}
```

Đây chỉ là conceptual model.

Compiler có thể encode state bằng:

```text
integer tag
```

và flat fields.

---

# 35. Future layout optimization

Compiler có thể reuse storage:

```text
State A uses field 0
State B uses same field 0
```

nếu lifetimes không overlap.

Ví dụ:

```text
state-field interference graph
```

→ compact Future.

---

# 36. Drop across states

Ví dụ:

```axiom
async fn foo() {
    let a = ResourceA();
    await x();
    let b = ResourceB();
    await y();
}
```

Nếu Future bị drop ở state sau `await y`:

```text
Drop(b)
Drop(a)
```

theo initialization/destruction semantics.

Nếu drop ở state giữa:

```text
Drop(a)
```

chỉ những fields đang initialized.

---

# 37. Partial initialization trong Future

Future state có thể:

```text
a = initialized
b = uninitialized
```

Do đó Future Drop cần field-sensitive initialization.

Đây là lý do ownership checker phải tích hợp với async lowering.

---

# 38. Await và ownership

Ví dụ:

```axiom
let s = String(...);

await foo();

use(s);
```

`s` sống qua await.

Compiler đưa `s` vào Future state.

Không cần programmer viết:

```text
move s into future
```

Compiler tự lower.

---

# 39. Await và Move

Ví dụ:

```axiom
let s = String(...);

await foo(s);
```

Nếu `foo` consumes `s`:

```text
s → Moved
```

sau đó `s` không cần nằm trong Future state.

Compiler phải phân tích điều này.

---

# 40. Await và capability

Ví dụ:

```axiom
let view = view(buffer);

await foo();

use(view);
```

Capability analysis:

```text
view live across suspension
```

→ kiểm tra storage/execution-domain contract.

Không chỉ dựa trên type.

---

# 41. Async closure

Axiom có thể:

```axiom
let f = async |x| {
    await process(x);
};
```

Compiler xử lý:

```text
async closure
↓
closure environment
+
Future state machine
```

Không tạo hai abstraction runtime bắt buộc.

---

# 42. Async + generic

```axiom
async fn process<T: Send>(x: T) -> T {
    await work();
    return x;
}
```

Generic instantiation:

```text
process<i32>
process<MyType>
```

Sau đó async lowering.

Ordering nên là:

```text
Generic resolution
 ↓
Async analysis
 ↓
Concrete Future
```

để Future layout biết `T` thực sự là gì.

---

# 43. Async + trait

```axiom
async fn process<T: Worker>(x: T) {
    await x.work();
}
```

Static dispatch:

```text
Worker implementation
↓
concrete call
↓
async state machine
```

Nếu `dyn Worker`:

```text
dynamic call
↓
Future returned by trait method
```

phải có explicit dynamic semantics.

---

# 44. Async trait methods

Ví dụ:

```axiom
trait Worker {
    async fn work(self) -> Result<(), Error>;
}
```

Compiler có thể biểu diễn method return bằng anonymous Future associated with implementation.

Không cần expose một concrete Future type name.

Conceptually:

```text
Worker::work
    → associated Future type
```

Trait solver phải biết equality/normalization cần thiết.

---

# 45. Không runtime Future registry

Không:

```text
FutureRegistry
AsyncObjectRegistry
GlobalExecutor
```

trong Core.

Future là ordinary generated type.

---

# 46. Async FFI

Không cho Axiom Future tự động đi qua C ABI.

FFI dùng:

```text
extern callback
opaque handle
poll function
completion callback
```

Ví dụ conceptually:

```text
start_async(...)
poll(handle, ...)
cancel(handle)
destroy(handle)
```

ABI explicit.

---

# 47. Async I/O

Đã thống nhất:

```text
read_async(buffer)
```

nên đảm bảo buffer validity.

Một hướng tốt:

```axiom
let (buffer, n) = await read_async(buffer);
```

Ownership:

```text
buffer
 ↓ Move
OS operation
 ↓ completion
buffer returned
```

Không cần giữ borrowed pointer không rõ lifetime qua await.

---

# 48. Readiness vs completion

Async không đồng nghĩa một cơ chế OS.

Axiom abstraction phải phân biệt:

```text
Readiness:
epoll
kqueue
poll

Completion:
IOCP
io_uring
...
```

Future chỉ thấy:

```text
Pending / Ready
```

runtime adapter xử lý backend.

---

# 49. Worker-backed async

Một library có thể implement:

```text
await blocking_operation()
```

bằng thread pool.

Điều này vẫn hợp lệ vì:

```text
async abstraction
≠
OS nonblocking guarantee
```

API/documentation phải phân biệt.

---

# 50. Optimization

Các pass riêng:

```text
StateFieldLiveness
StateFieldElision
StateSwitchOptimization
AwaitFusion
FutureInlining
ReadyPathSpecialization
CoroutineDCE
SuspensionPointSimplification
```

Ví dụ Future đã Ready ngay:

```text
await ready_future()
```

có thể trở thành direct path.

---

# 51. Allocation elimination

Ví dụ:

```axiom
async fn foo() -> i32 {
    return await bar();
}
```

Nếu Future không escape:

```text
foo future
↓
caller-owned
```

không cần heap.

Compiler có thể:

```text
inline future
```

hoặc scalarize state machine.

---

# 52. Async overhead mục tiêu

Axiom không hứa:

```text
async luôn zero-cost
```

nhưng semantics cho phép:

```text
No mandatory allocation
No mandatory thread
No mandatory scheduler
No mandatory heap
No mandatory object header
```

Compiler/runtime tốt có thể khiến simple async path rất nhẹ.

---

# 53. Diagnostics

Đề xuất:

```text id="h4ntx5"
AX1601 await used outside async context
AX1602 future is not Send
AX1603 borrowed capability crosses await
AX1604 synchronous guard crosses await
AX1605 async recursion requires finite indirection
AX1606 async FFI type is not ABI compatible
AX1607 future state contains invalid value
AX1608 future cancellation contract violated
AX1609 async operation may outlive its buffer
AX1610 invalid async trait method
AX1611 async task requires incompatible execution domain
AX1612 future cannot migrate across execution domain
```

---

# 54. Invariants

```text id="jyn9dz"
AASYNC-75  Async Is A Control-Flow Abstraction
AASYNC-76  Async Does Not Imply Thread Creation
AASYNC-77  Async Does Not Imply Task Spawning
AASYNC-78  Calling Async Produces A Future
AASYNC-79  Future Is A Compiler-Generated State Machine
AASYNC-80  Future Does Not Require Heap Allocation
AASYNC-81  Future Storage Is Determined By Storage Analysis
AASYNC-82  Future State Contains Only Required Live State
AASYNC-83  Await Creates A Suspension Point
AASYNC-84  Suspension Points Have Stable Compiler Identity
AASYNC-85  Polling Distinguishes Pending And Ready
AASYNC-86  Wake Is Scheduling Notification
AASYNC-87  Wake Is Semantically Idempotent
AASYNC-88  Scheduler Is Not Required By Core
AASYNC-89  Spawn Is A Scheduling Abstraction
AASYNC-90  Spawn Migration Requires Send
AASYNC-91  Spawn Local Does Not Require Send
AASYNC-92  Future Send Depends On Migratable State
AASYNC-93  Future State Is Ownership Checked
AASYNC-94  Future State Is Capability Checked
AASYNC-95  Borrowed Capabilities Cannot Cross Await Without Valid Contract
AASYNC-96  Await Does Not Extend Resource Lifetime Implicitly
AASYNC-97  Future Drop Drops Initialized State
AASYNC-98  Future Drop Does Not Imply External Operation Cancellation
AASYNC-99  Cancellation Is Explicit
AASYNC-100 Drop Cannot Await
AASYNC-101 Async Cleanup Must Be Explicit
AASYNC-102 Async Panic Uses Normal Panic Semantics
AASYNC-103 Async Result Uses Normal Result Semantics
AASYNC-104 Async Question Mark Uses Normal Control Flow
AASYNC-105 Recursive Futures Require Finite Representation
AASYNC-106 Async Lowering Produces Ordinary MIR
AASYNC-107 Backend Does Not Require Async Knowledge
AASYNC-108 Future Layout Is Compiler Controlled
AASYNC-109 Future Layout May Reuse Non-Overlapping State Storage
AASYNC-110 Future State Drops Are Field Sensitive
AASYNC-111 Async Generic Resolution Occurs Before Concrete Future Lowering
AASYNC-112 Async Trait Dispatch Is Explicitly Resolved
AASYNC-113 Dynamic Async Dispatch Requires Explicit Dynamic Representation
AASYNC-114 Async FFI Requires Explicit ABI
AASYNC-115 Async Does Not Imply Runtime Registry
AASYNC-116 Async Does Not Imply Global Executor
AASYNC-117 Async Optimization Cannot Change Suspension Semantics
```

---

# 55. BOOTSTRAP-017 gate

```text id="8cc7wz"
async fn                         ✓
Future type                      ✓
await                            ✓
Suspension points                ✓
Future state machine             ✓
Poll model                       ✓
Pending/Ready                    ✓
Waker                            ✓
Future ownership                 ✓
Future Drop                      ✓
Future Send analysis             ✓
Future + view                    ✓
Future + mut_view                ✓
Future + generic                 ✓
Future + trait                   ✓
Async closure                    ✓
Async recursion checking        ✓
Cancellation model               ✓
Async FFI model                  ✓
No mandatory heap               ✓
No mandatory executor            ✓
MIR lowering                     ✓
Interpreter execution            ✓
Native execution                ✓
O0/O2 equivalence                ✓
```

---

# Một điểm kiến trúc rất đáng giữ

Sau BOOT-017, mô hình execution của Axiom khá đẹp:

```text
                 COMPUTATION
                      │
        ┌─────────────┼─────────────┐
        │             │             │
      normal        async         comptime
        │             │             │
      value        Future         value
        │             │             │
        │         state machine    │
        │             │             │
        └─────────────┼─────────────┘
                      ↓
                    MIR
                      ↓
               native machine
```

Còn scheduler nằm **bên ngoài**:

```text
Future
  ↓
Task
  ↓
Scheduler
  ↓
Thread / Fiber / Execution Resource
```

Điều này rất phù hợp với mục tiêu ban đầu của Axiom: **không làm Core phình to chỉ vì muốn hỗ trợ concurrency hiện đại**.

### Bước tiếp theo

Sau Async, phần semantic execution lớn gần như đã đủ. Bước tiếp theo nên là:

**BOOTSTRAP-018 — Concurrency Core: Thread + Send/Share + Mutex/RwLock + Atomics + Scheduler boundary**

Đây sẽ là lúc chốt một vấn đề rất quan trọng: **Axiom bảo đảm data-race safety thế nào mà không biến thành Rust với borrow checker/lifetime syntax**, đồng thời vẫn cho phép code lock-free, atomic và low-level ở mức gần C/C++.