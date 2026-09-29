Tiếp tục.

# Axiom — Async / Coroutine Model v0.1

Tôi sẽ chốt phần này theo hướng **async không kéo theo runtime bắt buộc**.

Mục tiêu:

```text
async/await
    ↓
compiler lowering
    ↓
concrete state machine
    ↓
executor bên ngoài
```

Không:

```text
async
 ↓
mandatory heap allocation
 ↓
mandatory scheduler
 ↓
mandatory runtime
```

---

## 1. `async` thực chất là gì?

Trong Axiom, `async` không phải một loại thread.

Nó là một **hàm có khả năng tạo suspension points**.

Ví dụ:

```axiom
async fn load_user(id: u64) -> Result<User, Error> {
    let data = await database.get(id)?
    let avatar = await download(data.avatar)?
    return User.from(data, avatar)
}
```

Compiler nhìn nó như:

```text
Normal function
      +
SUSPEND points
      ↓
State machine
```

---

# 2. Future không nhất thiết là object

Đây là quyết định rất quan trọng.

Không bắt buộc:

```text
Future object
 ├── vtable
 ├── refcount
 ├── heap allocation
 └── runtime metadata
```

Thay vào đó, mỗi `async fn` có thể tạo một **concrete anonymous state type**.

Conceptually:

```text
LoadUserState {
    state: u8
    id: u64
    data: ...
    avatar: ...
}
```

Nhưng đây chỉ là semantic representation.

Compiler có thể:

- đặt trên stack
- inline vào caller
- đặt trong task allocation
- đặt trong arena
- scalarize thành registers
- loại bỏ hoàn toàn state machine nếu không thực sự suspend.

---

# 3. `async fn` không nhất thiết trả về heap Future

Ví dụ:

```axiom
async fn foo() -> i32 {
    42
}
```

Nếu không có `await`, compiler có thể nhận ra:

```text
ASYNC
 ↓
NO SUSPENSION
 ↓
ordinary function
```

Không cần tạo state machine thật.

Đây là một ví dụ trực tiếp của:

> **Abstraction Erasure.**

---

# 4. Khi có `await`

Ví dụ:

```axiom
async fn foo() -> i32 {
    let a = await get_a()
    return a + 1
}
```

Compiler có thể tạo:

```text
State 0:
    call get_a()
    if ready → State 1
    if pending → suspend

State 1:
    a = result
    return a + 1
```

Conceptually:

```text
        ┌──────────────┐
        │    State 0   │
        └──────┬───────┘
               │
             await
          ┌────┴────┐
          │         │
       Ready      Pending
          │         │
          ▼         ▼
       State 1    Suspend
                    │
                    ▼
                  Resume
                    │
                    └──→ State 1
```

---

# 5. `await` là suspension boundary

Mỗi `await` có thể chia hàm thành nhiều vùng:

```text
Before await
      ↓
Suspend
      ↓
After await
```

Compiler phải xác định các local nào còn cần thiết sau suspension.

Ví dụ:

```axiom
async fn foo() {
    let a = expensive_value()
    let b = await something()
    use(b)
}
```

`a` không được sử dụng sau `await`.

Compiler có thể:

```text
a
 ↓
destroy/release trước await
```

thay vì lưu `a` vào state machine.

Đây là một optimization rất quan trọng.

---

# 6. Live-across-await analysis

Compiler cần một pass:

```text
Async Analysis
```

Input:

```text
MIR
```

Output:

```text
live across suspension
```

Ví dụ:

```text
a ──────────────┐
                │
await           │
                │
b ──────────────┘
```

Chỉ những value thực sự sống qua `await` mới trở thành state.

---

# 7. Async state machine và ownership

Đây là nơi mô hình ownership hiện tại phát huy tác dụng.

Ví dụ:

```axiom
async fn process() {
    let file = File.open("x")?
    let data = await read(file)?
    use(data)
}
```

`file` sống qua `await`.

Compiler chuyển ownership:

```text
local
  ↓
async state
  ↓
suspend
  ↓
resume
  ↓
drop
```

Nếu task bị cancellation:

```text
state
 ↓
Drop
 ↓
file released
```

Không cần cơ chế memory management riêng cho async.

---

# 8. Async state phải là một owner

Invariant:

> **Async state owns every resource that must survive suspension.**

Không cho phép:

```text
async state
    ↓
borrowed local
    ↓
suspend
```

nếu local có thể chết trước khi task resume.

Đây là lý do `view`/`mut_view` qua `await` bị hạn chế ở v0.1.

---

# 9. Executor hoàn toàn bên ngoài Core

Ví dụ:

```axiom
let task = load_user(42)

executor.run(task)
```

`executor` là library/platform.

Có thể có:

```text
std.async.current_thread
std.async.thread_pool
std.async.io
std.async.epoll
std.async.io_uring
std.async.iocp
std.async.kqueue
```

Nhưng Core chỉ biết:

```text
async
await
suspend/resume semantics
```

---

# 10. Một chương trình không dùng executor

Hoàn toàn hợp lệ:

```axiom
fn main() {
    let x = async_function()
    ...
}
```

Nếu không có polling/execution:

```text
không link async runtime
```

Tất nhiên async operation sẽ không tự chạy.

Điều này giống với việc tạo một thread handle nhưng không start nó: semantics rõ ràng.

---

# 11. Có nên có `Future` trait?

Có, nhưng nó nên là **library abstraction**, không phải language primitive.

Conceptually:

```axiom
trait Future {
    type Output

    fn poll(self: mut_view<Self>, cx: mut_view<Context>)
        -> Poll<Self.Output>
}
```

với:

```axiom
enum Poll<T> {
    Ready(T),
    Pending
}
```

Compiler có thể tạo implementation tương ứng cho async state machine.

Nhưng người dùng không cần nhìn thấy anonymous future type.

---

# 12. Compiler-generated Future

Ví dụ:

```axiom
async fn foo() -> i32 {
    ...
}
```

semantic equivalent:

```text
anonymous type FooFuture
    implements Future<Output = i32>
```

Tên type không nhất thiết xuất hiện trong source.

Compiler có thể gọi:

```text
__async_Foo_State
```

nhưng đây là implementation detail.

---

# 13. Vì sao không dùng dynamic Future?

Không nên mặc định:

```text
Box<dyn Future<Output=T>>
```

vì sẽ kéo theo:

- allocation
- dynamic dispatch
- indirect call
- runtime metadata

Trong khi async thường có thể biết concrete type tại compile time.

Default:

```text
async fn
 ↓
concrete future
 ↓
static dispatch
```

Dynamic async phải explicit:

```text
Box<dyn Future<...>>
```

---

# 14. Async allocation

Không có mandatory allocation.

Ví dụ:

```axiom
async fn foo() {
    await io()
}
```

Caller có thể:

```text
stack:
    FooFuture
```

Nếu cần spawn:

```axiom
executor.spawn(foo())
```

executor có thể đưa state vào:

```text
heap
```

hoặc:

```text
task arena
```

hoặc:

```text
intrusive task storage
```

Đây là executor's choice.

---

# 15. `spawn` khác `async`

Rất rõ:

```text
async
    = tạo computation có thể suspend

spawn
    = đưa computation vào execution context
```

Ví dụ:

```axiom
let future = foo()
```

chưa nhất thiết chạy `foo`.

Còn:

```axiom
executor.spawn(foo())
```

mới yêu cầu executor quản lý execution.

---

# 16. `await` không tự tạo thread

Ví dụ:

```axiom
async fn foo() {
    await network()
}
```

có thể chạy hoàn toàn trên:

```text
1 OS thread
```

với hàng nghìn task.

Hoặc:

```text
N OS threads
```

với thread pool.

Async semantics không phụ thuộc executor architecture.

---

# 17. Async + Send

Nếu future được chuyển sang execution context khác:

```text
future
   ↓ MOVE
thread
```

thì future phải thỏa:

```text
Send
```

Compiler kiểm tra **toàn bộ state machine**.

Ví dụ:

```axiom
async fn foo() {
    let x = NonSendResource()
    await something()
}
```

Nếu future được spawn sang thread khác:

```text
ERROR
```

vì state sau suspension chứa `x`.

---

# 18. `spawn_local`

Để hỗ trợ UI/event-loop/single-thread async:

```axiom
executor.spawn_local(foo())
```

không yêu cầu Future phải `Send` nếu executor đảm bảo task không migrate sang thread khác.

Như vậy:

```text
spawn
    → Send required

spawn_local
    → Send not required
```

Đây là một semantic distinction rất sạch.

---

# 19. `Share` của Future

Không nên tự động cho:

```text
Future: Share
```

Future thường là mutable state machine:

```text
poll()
 ↓
changes state
```

Do đó mặc định:

```text
Future
    !Share
```

trừ khi implementation/type cụ thể chứng minh được.

---

# 20. Poll phải exclusive

Một future bình thường không nên được poll đồng thời:

```text
Thread A → poll(future)
Thread B → poll(future)
```

Nếu cần shared execution, executor phải synchronization.

Về ownership:

```text
poll(&mut future)
```

semantic tương đương:

```text
poll(mut_view<Future>)
```

Do đó ownership model tự nhiên ngăn concurrent polling.

---

# 21. Waker

Executor cần một cơ chế đánh thức task.

Concept:

```text
Future
  ↓ Pending
Waker
  ↓
I/O event
  ↓
wake()
  ↓
executor schedules task
```

`Waker` là library/runtime abstraction.

Không cần compiler primitive.

---

# 22. Không để Waker chứa runtime magic trong type system

Có thể conceptually:

```axiom
trait Waker {
    fn wake(self)
}
```

hoặc một handle nhỏ.

Nhưng compiler không cần hiểu:

```text
epoll
io_uring
IOCP
kqueue
```

Tất cả nằm dưới executor/platform.

---

# 23. Cancellation

Tôi đề xuất API library:

```axiom
let token = CancellationToken.new()

executor.spawn_with(token, task())
```

Task:

```axiom
if token.is_cancelled() {
    return Err(Cancelled)
}
```

Hoặc cancellation được tích hợp vào executor/future polling.

Điểm quan trọng:

> Cancellation request không được tự ý phá execution giữa một instruction sequence.

---

# 24. Cancellation tại await

Một mô hình tự nhiên:

```text
RUNNING
   │
   │ await
   ▼
PENDING
   │
   ├── wake → RUNNING
   │
   └── cancel → DROP
```

Nếu task đang thực hiện một đoạn synchronous computation:

```text
RUNNING
```

thì cancellation không cần cưỡng chế dừng ngay.

---

# 25. Drop khi cancellation

Ví dụ:

```axiom
async fn foo() {
    let file = File.open(...)?
    await network()
    ...
}
```

Nếu cancellation xảy ra lúc suspended:

```text
FooFuture
 └── file
```

Task destruction:

```text
Drop FooFuture
      ↓
Drop file
```

Do đó:

**cancellation safety được kế thừa từ Drop.**

Đây là một lợi thế rất lớn của mô hình hiện tại.

---

# 26. Async + `?`

Ví dụ:

```axiom
async fn foo() -> Result<Data, Error> {
    let a = await load_a()?
    let b = await load_b(a)?
    Ok(b)
}
```

Compiler hạ:

```text
await
 ↓
poll
 ↓
Ready/ Pending
 ↓
Result
 ↓
error branch
 ↓
Drop required state
 ↓
return
```

Không cần exception runtime.

---

# 27. Async exception model

Axiom không có:

```text
throw
catch
finally
```

nên async không phải xử lý exception propagation.

Có:

```text
Result
Option
Panic
Trap
```

Panic mode:

```text
abort
```

hoặc:

```text
unwind
```

Nếu unwind được bật, state machine phải có drop metadata tương ứng.

---

# 28. Async stackless là default

Tôi đề xuất:

> **Axiom Core async = stackless coroutine.**

Tức là state machine.

Không cấp mỗi coroutine một stack mặc định.

Lợi ích:

- allocation nhỏ
- scheduler dễ
- stack memory thấp
- compiler tối ưu tốt
- state size có thể biết tại compile time
- không cần segmented stack runtime.

---

# 29. Stackful coroutine vẫn có thể tồn tại

Nhưng là library/system feature:

```text
Fiber
CoroutineStack
GreenThread
```

Có thể dùng:

```text
unsafe
custom stack
context switch
```

Như vậy Axiom vẫn viết được:

- game fibers
- scripting VM
- user-level scheduler
- high-performance networking
- coroutine-heavy runtime

mà không làm Core phức tạp.

---

# 30. Async state size

Compiler nên expose:

```axiom
size_of(...)
```

và tool:

```text
axiom dump-async
```

có thể hiển thị:

```text
Future: LoadUser
State size: 184 bytes

State 0: 48 bytes
State 1: 120 bytes
State 2: 64 bytes
```

Điều này cực kỳ hữu ích cho performance engineering.

---

# 31. State machine optimization

Compiler có thể:

```text
remove dead fields
merge states
scalar replace
reuse storage
pack discriminant
eliminate temporary
inline child future
fuse await chains
```

Nhưng:

> chỉ khi semantics không đổi.

Ví dụ future nested:

```text
foo()
  await bar()
      await baz()
```

có thể được flatten nếu compiler chứng minh an toàn.

---

# 32. Async recursion

Đây là trường hợp đặc biệt:

```axiom
async fn recurse() {
    await recurse()
}
```

Không thể tạo một state machine vô hạn kích thước.

Phải có indirection:

```text
Box<Future>
```

hoặc một executor/task allocation.

Compiler nên báo lỗi rõ nếu recursion không có finite representation.

Ví dụ:

```text
AX_ASYNC_0004:
recursive async computation requires indirection
```

Không cần programmer hiểu state-machine internals.

---

# 33. Async trait

Có thể:

```axiom
trait Downloader {
    async fn download(self: view<Self>) -> Result<Data, Error>
}
```

Compiler transform thành associated future hoặc equivalent hidden type.

Không cần dynamic allocation mặc định.

Với:

```text
dyn Downloader
```

dynamic async dispatch có thể cần:

```text
Box<dyn Future<...>>
```

hoặc ABI tương đương.

Điều này chỉ xảy ra khi programmer **chọn dynamic dispatch**.

---

# 34. Executor ABI

Không đưa executor vào language ABI.

Executor chỉ cần một contract kiểu:

```text
poll(task, context)
```

và:

```text
wake(task)
```

Compiler-generated future phải tuân theo library trait/ABI.

Điều này cho phép nhiều executor cạnh tranh:

```text
single-thread
thread-pool
epoll
io_uring
IOCP
game-loop
embedded
custom RTOS
```

---

# 35. Freestanding

Đây là điểm rất phù hợp với Axiom.

Một chương trình:

```axiom
@entry
fn main() {
    ...
}
```

có thể không có:

```text
std
allocator
thread
async
filesystem
network
```

Nếu programmer muốn async trên embedded:

```text
custom executor
```

được phép.

Không ép OS/runtime model.

---

# 36. Async invariants

Tôi chốt:

```text
AASY-01  Async Is Not Thread
AASY-02  Async Is Suspension Semantics
AASY-03  Async Uses Compiler State Machines
AASY-04  Async Does Not Require Heap Allocation
AASY-05  Async Does Not Require Executor
AASY-06  Executor Is Library/Platform Layer
AASY-07  Async State Owns Live-Across-Await Values
AASY-08  Dead Locals Are Not Preserved Across Await
AASY-09  Future Uses Static Dispatch By Default
AASY-10  Dynamic Future Is Explicit
AASY-11  Future Poll Requires Exclusive Mutable Access
AASY-12  spawn Requires Send
AASY-13  spawn_local Does Not Require Send
AASY-14  Future Share Is Not Assumed
AASY-15  Cancellation Is Cooperative
AASY-16  Cancellation Drops Task State
AASY-17  Await Is A Suspension Boundary
AASY-18  Mutable Views Cannot Cross Await in v0.1
AASY-19  Read Views Cross Await Only With Proven Safety
AASY-20  Async Recursion Requires Finite Indirection
AASY-21  Async Errors Use Result/Option
AASY-22  Async Panic Follows Global Panic Mode
AASY-23  Stackless Coroutine Is Core Async Model
AASY-24  Stackful Coroutine Is Library/System Feature
AASY-25  Executor Is Replaceable
AASY-26  Async Has No Mandatory Global Scheduler
AASY-27  State-Machine Optimization Is Semantics-Preserving
AASY-28  Async Resource Cleanup Is Deterministic
```

---

# 37. Bức tranh hoàn chỉnh lúc này

Axiom đã có thể mô hình hóa:

```text
                  Axiom
                    │
              Ownership
                    │
        ┌───────────┴───────────┐
        │                       │
     Sequential             Concurrent
                                │
                   ┌────────────┼────────────┐
                   │            │            │
                 Thread       Async       Channel
                   │            │            │
                 Send        Future         Send
                   │            │
                   │       State Machine
                   │            │
                   └──────┬─────┘
                          │
                   Synchronization
                          │
              ┌───────────┼───────────┐
              │           │           │
            Mutex       Atomic       RwLock
              │           │
              └─────┬─────┘
                    │
               Lock-free
                    │
          ┌─────────┼─────────┐
          │         │         │
        Epoch     Hazard   AtomicShared
```

Và **không có một runtime duy nhất** đứng dưới tất cả.

---

# Quyết định lớn đã hoàn tất

Tôi đánh giá đây là một trong những phần quan trọng nhất của Axiom và hiện mô hình đã khá kín:

### Language Core

```text
ownership
capability
Send
Share
async
await
atomic semantics
```

### Core Library

```text
Mutex
RwLock
Channel
Thread
Future
Waker
Cancellation
Arc
AtomicShared
```

### Runtime/Platform

```text
executor
thread pool
epoll
io_uring
IOCP
kqueue
TLS
fiber
```

### System layer

```text
raw pointer
custom scheduler
custom allocator
lock-free algorithms
hazard/epoch reclamation
MMIO
kernel primitives
```

Đây đúng với mục tiêu ban đầu của bạn: **ngôn ngữ không phải tối giản bằng cách cắt bỏ khả năng, mà core semantic nhỏ nhưng đủ mạnh; phần phức tạp được compiler và library gánh thay cho programmer.**

---

## Tiếp tục → FFI và C interop

Phần kế tiếp tôi sẽ xử lý **FFI/ABI/foreign memory**. Đây là nơi phải giải quyết rất kỹ:

```text
Axiom ownership
      ↕
C pointers
      ↕
extern memory
      ↕
callbacks
      ↕
struct layout
      ↕
variadic functions
      ↕
system ABI
```

đặc biệt là làm sao để **Axiom có thể gọi C gần như trực tiếp nhưng không biến toàn bộ C's memory unsafety thành safe Axiom**.