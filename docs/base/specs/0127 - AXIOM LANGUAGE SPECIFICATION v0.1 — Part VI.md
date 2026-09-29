# AXIOM LANGUAGE SPECIFICATION v0.1 — Part VI
## Async · Await · Future · Coroutine State Machine

Mục tiêu của Axiom async:

> **`async/await` là một control-flow abstraction, không phải runtime model.**

Một `async fn` không mặc định có:
- heap allocation
- OS thread
- scheduler
- event loop
- GC
- reference counting
- dynamic dispatch
- runtime object

Nếu compiler chứng minh một `async` function không cần suspension, nó có thể biến hoàn toàn thành function thông thường.

---

# 1. Mô hình tổng quát

Axiom phân biệt:

```text
async function
Future
executor
thread
```

Đây là bốn khái niệm khác nhau.

```text
async fn
    ↓ compile-time lowering
Future/state machine
    ↓
executor quyết định khi nào poll
```

Executor là library/runtime abstraction.

---

# 2. `async fn`

Ví dụ:

```axiom
async fn load_user(id: UserId) -> Result<User, Error> {
    let data = fetch(id).await?
    parse(data)
}
```

Về semantic:

```text
load_user(id)
```

không thực hiện toàn bộ function ngay.

Nó tạo một computation có khả năng:

```text
Pending
```

hoặc:

```text
Ready(User)
```

---

# 3. Future

Future là giá trị biểu diễn computation chưa hoàn tất.

Conceptually:

```text
Future<T>
```

có operation:

```text
poll() -> Poll<T>
```

với:

```text
enum Poll<T> {
    Pending,
    Ready(T),
}
```

Đây là semantic model; representation thực tế do compiler/library quyết định.

---

# 4. Future không bắt buộc heap

Ví dụ:

```axiom
let future = load_user(id)
```

compiler có thể lưu Future:

```text
register
stack
inline struct
caller-provided storage
heap
arena
```

tùy escape/lifetime.

Không có quy tắc:

```text
async => heap
```

---

# 5. Future không bắt buộc runtime

Một function:

```axiom
async fn foo() -> i32 {
    42
}
```

nếu không có suspension point, compiler có thể hạ thành computation tương đương function thông thường.

Ví dụ conceptual:

```text
async fn foo() -> i32
```

→

```text
fn foo() -> i32
```

nếu toàn bộ async abstraction không observable.

---

# 6. Nhưng semantic type vẫn phải nhất quán

Compiler không được thay đổi observable API chỉ vì implementation không cần suspension.

Nếu public API khai báo:

```text
async fn foo()
```

thì type-level contract của nó vẫn là async computation.

Việc erase async chỉ được phép ở nơi không làm thay đổi observable semantics.

---

# 7. State machine lowering

Ví dụ:

```axiom
async fn work() -> Result<i32, Error> {
    let a = step_a().await?
    let b = step_b(a).await?
    a + b
}
```

Compiler có thể tạo conceptual state machine:

```text
State::Start
State::WaitingA
State::WaitingB
State::Done
```

Không nhất thiết sinh enum runtime thật sự.

---

# 8. State machine

Conceptually:

```text
┌─────────┐
│  Start  │
└────┬────┘
     │
     ▼
┌────────────┐
│ Waiting A  │
└─────┬──────┘
      │ Ready
      ▼
┌────────────┐
│ Waiting B  │
└─────┬──────┘
      │ Ready
      ▼
┌─────────┐
│  Done   │
└─────────┘
```

Mỗi suspension point tương ứng với một state có thể resume.

---

# 9. Chỉ lưu state cần thiết

Đây là điểm cực kỳ quan trọng về hiệu năng.

Ví dụ:

```axiom
async fn foo() {
    let a = create_large_object()

    compute(a)

    let x = network().await

    use(x)
}
```

Nếu `a` không còn được sử dụng sau `.await`, compiler có thể:

```text
drop(a)
```

trước suspension.

Future state không cần chứa `a`.

---

# 10. Live-across-await analysis

Compiler thực hiện:

```text
live variable analysis
+
ownership analysis
+
drop analysis
```

để xác định:

```text
values_live_across_await
```

Chỉ các giá trị cần thiết mới trở thành state của Future.

---

# 11. Ví dụ

```axiom
async fn foo() {
    let huge = make_buffer()

    process(huge)

    network().await

    finish()
}
```

Nếu `huge` dead trước await:

```text
Future state
    không chứa huge
```

Điều này giảm đáng kể memory footprint.

---

# 12. Owned values qua await

Owned value có thể sống qua `.await`.

```axiom
async fn foo() {
    let data = make_data()

    wait().await

    process(data)
}
```

Compiler chuyển ownership của `data` vào Future state.

Conceptually:

```text
local owner
    ↓ suspension
Future state owner
    ↓ resume
local owner
```

Đây là ownership transfer nội bộ compiler.

---

# 13. Không có lifetime syntax

Programmer không viết:

```text
Future<'a>
```

hay:

```text
async<'a>
```

Axiom compiler tự tính dependency.

---

# 14. `view<T>` qua await

Trong v0.1:

```text
view<T>
```

không được sống qua `.await`.

Ví dụ:

```axiom
async fn bad(x: view<Data>) {
    use(x)
    wait().await
    use(x)
}
```

→ reject.

---

# 15. `mut_view<T>` qua await

Tương tự:

```text
mut_view<T>
```

không được sống qua `.await`.

```axiom
async fn bad(x: mut_view<Data>) {
    mutate(x)

    wait().await

    mutate(x)
}
```

→ reject.

---

# 16. Vì sao cấm cả read view?

Điểm này có chủ ý.

Nếu cho `view<T>` xuyên suspension:

```text
owner
   ↓
view
   ↓
await
```

thì owner/storage phải bị giữ sống trong toàn bộ Future lifetime.

Điều này làm tăng:
- lifetime coupling
- relocation constraints
- Send/Share complexity
- async state size

Axiom v0.1 chọn mô hình đơn giản:

> **Owned values được phép cross await; capabilities không.**

---

# 17. Có thể tạo view lại sau await

Ví dụ:

```axiom
async fn foo(data: Data) {
    wait().await

    let v = view(data)
    inspect(v)
}
```

Hợp lệ.

Capability chỉ tồn tại trong đoạn synchronous region hiện tại.

---

# 18. `mut_view` và Future state

Điều này đặc biệt giúp compiler tránh:

```text
Future
 ├── owner A
 └── mutable capability → A
```

qua nhiều suspension points.

Thay vào đó:

```text
Future owns A
     │
     ├── state 1: no capability
     │
     ├── resume
     │
     └── temporary mut_view(A)
```

---

# 19. Await là suspension boundary

`.await` là semantic boundary.

Compiler phải xử lý:

```text
drop
ownership
capabilities
panic
cancellation
Send
```

trước khi state machine được lower.

---

# 20. Cleanup trước suspension

Không cần giữ mọi local sống tới cuối function.

Ví dụ:

```axiom
async fn foo() {
    {
        let resource = acquire()
        use(resource)
    }

    await_work().await
}
```

`resource` được Drop trước suspension.

Future không cần chứa nó.

---

# 21. Cancellation

Future có thể bị drop khi đang Pending.

Ví dụ:

```text
Future
  ↓
Pending
  ↓
owner drops Future
```

Các owned values trong Future state phải được cleanup deterministic.

---

# 22. Cancellation không phải panic

```text
drop Future
```

không phải:

```text
panic
```

và cũng không phải:

```text
thread termination
```

Nó đơn giản là lifecycle termination của computation state.

---

# 23. External operation

Ví dụ:

```axiom
async fn request() {
    socket.read().await
}
```

Nếu Future bị drop:

```text
drop(future)
```

không mặc định guarantee:

```text
OS/network operation cancelled
```

External resource phải có cancellation contract riêng.

---

# 24. CancellationToken

Library có thể cung cấp:

```axiom
let token = CancellationToken.new()

request(token).await?
```

để external operation cooperatively cancel.

Đây là library abstraction, không phải Core async semantics.

---

# 25. Executor

Executor chịu trách nhiệm:

```text
poll futures
wake tasks
schedule tasks
manage task lifecycle
```

Axiom Core không yêu cầu một executor cụ thể.

---

# 26. Một chương trình async không nhất thiết có runtime lớn

Ví dụ embedded/freestanding:

```text
main
 ↓
poll one future
 ↓
hardware event
 ↓
poll again
```

Không cần:
- thread pool
- reactor
- networking runtime
- GC

nếu chương trình không dùng chúng.

---

# 27. Waker

Future Pending cần cơ chế báo:

```text
"hãy poll lại tôi"
```

Conceptually:

```text
Waker
```

Executor nhận wake notification và schedule Future.

Waker là library/runtime mechanism.

---

# 28. Waker không phải thread

Một wake:

```text
wake()
```

không có nghĩa:

```text
spawn thread
```

Executor có thể:
- poll ngay
- queue task
- wake event loop
- dispatch sang worker
- hardware callback

---

# 29. `await` không spawn

Đây là invariant quan trọng:

```text
await ≠ spawn
```

```axiom
let x = operation().await
```

không tạo execution context mới.

Nó chỉ:

```text
poll
→ Pending?
→ suspend
→ resume later
```

---

# 30. `spawn` mới tạo concurrent execution

```axiom
spawn(async {
    work().await
})
```

mới tạo task execution context.

---

# 31. Async và Send

Một Future có thể cần:

```text
Send
```

nếu nó có khả năng được migrate giữa execution contexts.

Nhưng không phải mọi async Future đều cần Send.

---

# 32. `spawn`

Nếu executor cho phép task chạy trên nhiều worker threads:

```axiom
spawn(future)
```

Future phải đáp ứng:

```text
Future: Send
```

và các values live across await cũng phải thỏa contract.

---

# 33. `spawn_local`

Nếu executor đảm bảo same-thread:

```axiom
spawn_local(future)
```

không yêu cầu Future phải `Send`.

Đây là lý do Axiom không gắn `Send` cố định vào mọi Future.

---

# 34. Send chỉ xét state thực sự tồn tại

Ví dụ:

```axiom
async fn foo() {
    let non_send = create()

    use(non_send)

    await_work().await
}
```

Nếu `non_send` chết trước await:

```text
Future state
    không chứa non_send
```

Future có thể không cần `Send` vì lý do đó.

---

# 35. Đây là một optimization nhưng cũng là semantic analysis

Compiler phải xác định:

```text
live-across-await set
```

trước khi kiểm tra cross-thread migration.

Không được bảo thủ kiểu:

```text
"đã từng tồn tại trong function → Future !Send"
```

---

# 36. Future không tự động `Share`

Một Future có thể chứa mutable state.

Do đó:

```text
Future<T>
```

không mặc định:

```text
Share
```

Nhiều executor task không được tự ý poll cùng một Future nếu abstraction không cho phép.

---

# 37. Poll độc quyền

Conceptually:

```text
poll(&mut Future)
```

có exclusive access.

Không được:

```text
thread A → poll(F)
thread B → poll(F)
```

đồng thời nếu Future không có synchronization abstraction.

---

# 38. Async recursion

Ví dụ:

```axiom
async fn recurse() {
    recurse().await
}
```

không thể tạo Future có kích thước vô hạn.

Compiler phải reject trực tiếp hoặc yêu cầu indirection hữu hạn.

Ví dụ library abstraction:

```text
Box<Future>
```

có thể cung cấp dynamic indirection.

---

# 39. Async state size

Compiler nên expose:

```text
axiom inspect async-state
```

ví dụ:

```text
Future: 176 bytes
states: 4
largest state: 112 bytes
```

Điều này cực kỳ hữu ích cho systems programming.

---

# 40. Heap allocation optimization

Compiler có thể:

```text
Future local
```

→ stack allocation.

Nếu Future không escape:

```text
Future allocation
```

có thể hoàn toàn biến mất.

---

# 41. Heap Future

Nếu Future cần stable dynamic lifetime:

```axiom
let task = spawn(future)
```

executor có thể đặt state trên heap.

Nhưng đây là:

```text
executor/storage strategy
```

không phải semantic requirement của async language.

---

# 42. Self-referential Future

Compiler-generated state machine không được để relocation phá invariant.

Nếu state machine chứa self-reference nội bộ, compiler phải:
- tránh self-reference bằng layout design,
- hoặc dùng stable storage,
- hoặc lower sang representation không cần self-reference.

Programmer không phải viết `Pin` trong Core v0.1.

---

# 43. Pin không phải Core primitive

Axiom không đưa:

```text
Pin<T>
```

vào language core.

Lý do:

```text
stable address
```

đã được xác định là một **storage contract**.

Nếu một async runtime cần stable task address, nó chịu trách nhiệm chọn storage strategy phù hợp.

---

# 44. Async trait

Trait có thể biểu diễn async behavior.

Conceptually:

```axiom
trait Service {
    async fn request(self: view<Self>) -> Result<Response, Error>
}
```

Compiler phải lower thành associated Future semantics.

---

# 45. Static async dispatch

Generic/static dispatch:

```axiom
fn run<S: Service>(service: S) async {
    service.request().await
}
```

có thể monomorphize.

Không cần virtual dispatch.

---

# 46. Dynamic async dispatch

Nếu:

```axiom
dyn Service
```

thì dynamic async dispatch cần runtime representation của Future.

Conceptually:

```text
dyn Service
   ↓
dispatch request
   ↓
dynamic Future
```

Đây là một trường hợp có thể cần allocation hoặc explicit dynamic storage, tùy implementation.

Không được giả định zero-allocation cho dynamic async dispatch.

---

# 47. `dyn Trait` + async

Đây là điểm quan trọng:

```text
static async
```

và:

```text
dynamic async
```

là hai cost model khác nhau.

Axiom không che giấu điều này.

---

# 48. Async error handling

```axiom
async fn foo() -> Result<Data, Error> {
    let a = first().await?
    let b = second(a).await?
    Ok(b)
}
```

`?` vẫn là ordinary control-flow lowering.

Conceptually:

```text
poll first
    ↓
Pending → return Pending
Ready(Err) → return Err
Ready(Ok) → continue
```

Không cần exception runtime.

---

# 49. Panic trong async

Nếu computation panic:

```text
Future
 ↓
PANIC
```

executor quyết định task-level handling theo runtime/profile.

Nếu `panic=abort`:

```text
process termination
```

có thể xảy ra.

---

# 50. Drop order trong Future

Khi Future hoàn thành:

```text
Future state
 ↓
result
 ↓
remaining owned state
 ↓
Drop
```

Khi Future bị cancel:

```text
Future state
 ↓
Drop all still-owned fields
```

theo ownership/drop semantics thông thường.

---

# 51. Async + lock

Đã freeze:

```text
MutexGuard
    cannot cross await
```

Nhưng:

```text
Mutex
```

có thể được giữ trong Future state vì chính Mutex không phải guard.

Ví dụ:

```axiom
async fn foo(m: Arc<Mutex<State>>) {
    let value = {
        let guard = m.lock()
        read(guard)
    }

    network().await

    use(value)
}
```

Đây là pattern hợp lệ.

Guard chết trước await.

---

# 52. Async mutex

Nếu cần giữ logical lock qua suspension:

```axiom
let guard = async_mutex.lock().await
```

thì phải dùng async-aware synchronization abstraction.

Nó không được sử dụng synchronous blocking primitive để chờ executor.

---

# 53. Blocking trong async

Axiom không cấm compiler-level function gọi blocking API, nhưng library/runtime có thể đánh dấu:

```text
blocking
```

và tooling cảnh báo:

```text
blocking operation inside async context
```

Một async runtime tốt có thể cung cấp:

```text
spawn_blocking(...)
```

để chuyển blocking work sang worker thread.

---

# 54. Async effect không phải type pollution

Axiom không cần tạo hàng loạt type:

```text
Async<T>
Awaitable<T>
Suspendable<T>
ThreadSafeAsync<T>
```

Core semantic model chỉ cần:

```text
Future<T>
```

và compiler-known lowering.

---

# 55. MIR lowering

Async được xử lý trước Verified MIR hoặc trong một dedicated lowering phase:

```text
Typed HIR
   ↓
async analysis
   ↓
Future state-machine MIR
   ↓
ownership verification
   ↓
Verified MIR
```

Điều này rất quan trọng.

Compiler không verify một abstraction "mơ hồ".

Nó verify state machine thực tế.

---

# 56. State-machine invariants

Compiler phải bảo đảm:

```text
State transition
    preserves ownership

Suspension
    preserves all live values

Resume
    restores valid local state

Drop
    cleans every owned field exactly once

Cancellation
    cannot double-drop

Await
    cannot resurrect moved values
```

---

# 57. Oracle

Semantic Oracle phải có:

```text
SUSPEND
RESUME
POLL
WAKE
TASK_CREATE
TASK_DROP
```

event.

Ví dụ trace:

```text
TASK_CREATE 1
POLL 1
SUSPEND 1
WAKE 1
POLL 1
RETURN 1
TASK_DROP 1
```

---

# 58. Deterministic async testing

Oracle có thể chạy:

```text
single-thread deterministic executor
```

để test logic mà không phụ thuộc timing thực tế.

Có thể kiểm tra:

```text
poll order
wake order
drop behavior
cancellation
panic
ownership
```

---

# 59. Race testing

Concurrency sanitizer/runtime tooling có thể inject scheduling points:

```text
yield
before atomic
after atomic
before lock
after lock
```

để tìm race/deadlock.

Đây là tooling, không thay đổi language semantics.

---

# 60. Async optimization

Compiler được phép:

```text
inline Future
eliminate states
merge states
remove dead locals
scalarize Future
stack allocate Future
eliminate Future allocation
fuse await chains
```

miễn là không thay đổi:

```text
observable ordering
side effects
cleanup
panic
atomic semantics
FFI behavior
```

---

# 61. State elimination

Ví dụ:

```axiom
async fn foo() {
    let x = 1
    bar().await
    x
}
```

Nếu `x` có thể được encode trực tiếp trong state transition, compiler không nhất thiết phải tạo field runtime có tên `x`.

---

# 62. Async function không nhất thiết chậm

Chi phí thực tế phụ thuộc:

```text
number of suspension points
state size
poll frequency
executor
allocation
dynamic dispatch
FFI
synchronization
```

Không có quy tắc:

```text
async = slow
```

---

# 63. Nhưng Axiom không hứa "zero-cost tuyệt đối"

Async abstraction có thể có observable cost khi thực sự cần:

```text
suspension
scheduling
dynamic task lifetime
cross-thread migration
dynamic dispatch
heap storage
```

Mục tiêu là:

> **Không trả chi phí cho semantics mà chương trình không sử dụng.**

---

# 64. Core async invariants

### AASYNC-20
`async` is a control-flow abstraction, not a thread.

### AASYNC-21
`await` is a suspension/resumption boundary.

### AASYNC-22
A Future does not inherently require heap allocation.

### AASYNC-23
A Future does not inherently require an executor.

### AASYNC-24
An executor is a library/runtime abstraction.

### AASYNC-25
Only values live across suspension become Future state.

### AASYNC-26
Owned values may cross suspension.

### AASYNC-27
`view<T>` cannot cross `.await` in v0.1.

### AASYNC-28
`mut_view<T>` cannot cross `.await` in v0.1.

### AASYNC-29
Future cancellation deterministically drops owned Future state.

### AASYNC-30
Dropping a Future does not imply cancellation of external operations.

### AASYNC-31
`spawn` may require Send depending on execution model.

### AASYNC-32
`spawn_local` does not require cross-thread Send.

### AASYNC-33
Future is not implicitly Share.

### AASYNC-34
Async recursion requires finite runtime representation.

### AASYNC-35
Async state lowering preserves ownership semantics.

### AASYNC-36
Async lowering preserves Drop semantics.

### AASYNC-37
Async lowering preserves panic semantics.

### AASYNC-38
Async lowering preserves synchronization semantics.

### AASYNC-39
Async optimization cannot alter observable suspension behavior where observable.

### AASYNC-40
Dynamic async dispatch is explicitly distinguishable from static async dispatch.

---

# 65. Câu hỏi hiệu năng quan trọng

Với những gì vừa khóa, câu trả lời là:

**Có.**

Axiom async có thể đạt mô hình rất gần zero-cost:

```text
async fn
    ↓
compile-time state machine
    ↓
ordinary machine code
```

với:

```text
heap allocation = optional
executor = optional
thread = optional
GC = none
reference counting = none
object header = none
```

Điều này phù hợp trực tiếp với mục tiêu ban đầu của Axiom.

---

# 66. Toàn bộ mô hình concurrency hiện tại

Ta đã có:

```text
                 OWNERSHIP
                     │
          ┌──────────┴──────────┐
          │                     │
       Send                  Capability
          │                     │
    execution transfer    view / mut_view
          │                     │
          └──────────┬──────────┘
                     │
              SYNCHRONIZATION
                     │
        ┌────────────┼────────────┐
        │            │            │
      Channel       Lock        Atomic
        │            │            │
        └────────────┼────────────┘
                     │
                 EXECUTION
                     │
          ┌──────────┴──────────┐
          │                     │
       Threads                Tasks
                                │
                              Future
                                │
                              await
                                │
                         state machine
```

Đây là một mô hình tương đối gọn mà vẫn đủ khả năng đi xuống tới systems programming.

---

# AXIOM LANGUAGE SPECIFICATION v0.1 — Part VII
## Atomic Memory Model · Memory Ordering · Fences · Lock-Free Semantics

Phần tiếp theo cần khóa sâu hơn **atomic memory model**, bởi đây là chỗ quyết định Axiom có thực sự phù hợp cho:

- OS/kernel
- lock-free data structures
- game engine
- database
- networking
- GPU
- high-performance runtime

hay không.

Ta sẽ chốt:

```text
Atomic<T>
MemoryOrder
Relaxed
Acquire
Release
AcqRel
SeqCst
CAS
weak CAS
fence
happens-before
synchronizes-with
modification order
atomic visibility
volatile
MMIO
false sharing
cache-line alignment
lock-free / wait-free
atomic pointer
memory reclamation
ABA
```

và quan trọng nhất: **thiết kế sao cho compiler được phép tối ưu mạnh như C/C++ nhưng semantic model của Axiom dễ hiểu và ít "undefined behavior" hơn.**