Tiếp tục.

# BOOTSTRAP-038 — Async / Future / Await / Cancellation Audit & Freeze

Mục tiêu của phần này là chốt một nguyên tắc rất quan trọng của Axiom:

> **Async là cơ chế tổ chức control flow, không phải một runtime bắt buộc và cũng không đồng nghĩa với thread.**

Điều này giúp Axiom có thể viết cả:

```text
bare-metal / kernel / CLI / game engine / GUI / server / GPU
```

mà không phải mang theo async runtime nếu chương trình không sử dụng.

---

# 1. Ba khái niệm phải tách biệt

Axiom phân biệt rõ:

```text
Thread
Fiber
Task
Future
```

| Khái niệm | Bản chất |
|---|---|
| Thread | OS execution resource |
| Fiber | user-space stackful execution context |
| Task | schedulable computation |
| Future | compiler-generated state machine |

Không có quan hệ:

```text
async = thread
```

và cũng không có:

```text
async = task
```

---

# 2. `async fn`

Ví dụ:

```axiom
async fn fetch(url: String) -> Result<Data, Error> {
    ...
}
```

Gọi:

```axiom
let future = fetch(url)
```

**không bắt đầu chạy asynchronous operation theo nghĩa scheduler.**

Nó tạo một `Future`.

---

# 3. `.await`

```axiom
let data = fetch(url).await?
```

`await` có nghĩa:

> Poll Future cho đến khi Ready, trong quá trình đó cho phép execution context nhường quyền.

Nó không có nghĩa:

```text
spawn thread
```

hay:

```text
spawn task
```

---

# 4. Future là state machine

Compiler biến:

```axiom
async fn foo() -> T {
    let a = await_a().await;
    let b = await_b(a).await;
    b
}
```

thành conceptually:

```text
State 0
   │
   ├── await_a → Pending
   │
   ↓
State 1
   │
   ├── await_b → Pending
   │
   ↓
State 2
   │
   ↓
Ready(T)
```

---

# 5. Future không phải object runtime bắt buộc

Không yêu cầu:

```text
heap allocation
vtable
reference counting
GC
runtime object header
```

Future có thể nằm:

```text
register
stack
inline
caller-owned storage
arena
heap
```

tùy compiler.

---

# 6. Future storage

Compiler phân tích:

```text
values live across await
```

chỉ những giá trị cần thiết mới nằm trong Future state.

Ví dụ:

```axiom
async fn foo() {
    let a = make_large_object();

    calculate(a);

    await something();

    use(a);
}
```

`a` phải sống qua suspension.

Nhưng:

```axiom
async fn foo() {
    let a = temporary();

    calculate(a);

    await something();
}
```

nếu `a` không được dùng sau await, compiler không cần đưa `a` vào Future state.

---

# 7. State-field liveness

Đây là optimization quan trọng:

```text
Future
 ├── state discriminator
 ├── live field A
 ├── live field B
 └── live field C
```

Compiler có thể loại bỏ field không cần thiết.

---

# 8. Future không tự heap allocate

Ví dụ:

```axiom
async fn add() -> i32 {
    1 + 2
}
```

Future có thể được tối ưu thành gần như zero-cost.

Không được có rule:

```text
async => heap
```

---

# 9. `.await` tạo Suspension Point

Mỗi:

```axiom
await expression
```

tạo:

```text
SuspensionPointId
```

ổn định trong compiler.

Điều này hữu ích cho:

- debug
- state-machine lowering
- incremental compilation
- profiling
- diagnostics.

---

# 10. Lowering

Async phải được lower trước backend:

```text
async AST
   ↓
Typed HIR
   ↓
async lowering
   ↓
ordinary MIR
```

Backend không cần biết:

```text
async
await
Future
```

---

# 11. Future ABI

Future layout mặc định:

```text
compiler-controlled
```

Không được coi là ABI ổn định.

Không được FFI trực tiếp:

```axiom
extern "C" fn foo() -> Future<T>
```

trừ khi có ABI contract cụ thể.

---

# 12. `Poll`

Core conceptual model:

```axiom
enum Poll<T> {
    Ready(T),
    Pending
}
```

Future:

```axiom
trait Future {
    fn poll(...) -> Poll<T>
}
```

Nhưng `Future` implementation cụ thể có thể là compiler-generated.

---

# 13. Waker

Khi Future trả:

```text
Pending
```

nó đăng ký một cách để được đánh thức.

Conceptually:

```text
Future
   ↓ Pending
Waker
   ↓
scheduler
   ↓
READY
```

---

# 14. Wake không đồng nghĩa chạy ngay

```text
wake()
```

chỉ có nghĩa:

> computation có thể cần được poll lại.

Scheduler quyết định khi nào chạy.

---

# 15. Wake idempotent

Nếu:

```text
wake()
wake()
wake()
```

ba lần liên tiếp, scheduler không được tạo ba task identity khác nhau.

Có thể:

```text
READY
```

chỉ một lần.

---

# 16. Không mất wakeup

Runtime phải đảm bảo:

```text
register wait
+
event
+
wake
```

không tạo race khiến Future vĩnh viễn Pending.

Đây là invariant runtime quan trọng hơn syntax.

---

# 17. Async không có executor mặc định

Axiom Core không chứa:

```text
global executor
global event loop
global async runtime
```

Có thể có:

```text
std::async
tokio-like runtime
GUI executor
game executor
embedded executor
custom executor
```

ở library/runtime layer.

---

# 18. `spawn`

Nếu library cung cấp:

```axiom
spawn(foo())
```

thì:

```text
spawn = scheduling abstraction
```

không phải Core async semantics.

---

# 19. `async fn` và `spawn` khác nhau

```axiom
let f = foo()
```

→ Future.

```axiom
spawn(foo())
```

→ scheduler nhận Future và biến nó thành Task.

Đây là hai tầng khác nhau.

---

# 20. Sequential async

```axiom
let a = foo().await;
let b = bar().await;
```

là sequential.

Không có nghĩa:

```text
foo
bar
```

chạy đồng thời.

---

# 21. Concurrent async

Muốn concurrency phải explicit:

```axiom
let a = spawn(foo());
let b = spawn(bar());

let x = a.join().await?;
let y = b.join().await?;
```

hoặc abstraction tương đương:

```axiom
join(foo(), bar()).await
```

---

# 22. Structured concurrency

Mặc định library nên ưu tiên:

```text
parent task
 ├── child A
 └── child B
```

và parent chịu trách nhiệm:

```text
join
cancel
observe failure
```

Detached task phải explicit.

---

# 23. Detached task

Nếu muốn task sống độc lập:

```text
detach(task)
```

Đây phải là hành động rõ ràng.

Không:

```text
spawn(...)
```

rồi tự động leak lifecycle.

---

# 24. `Send` khi Future migration

Một Future có thể chứa:

```text
non-Send state
```

Nếu scheduler có thể chuyển Future:

```text
worker A
    ↓
worker B
```

thì Future phải:

```text
Send
```

---

# 25. Local executor

Nếu:

```axiom
spawn_local(foo())
```

Future không cần `Send`, vì execution domain được giữ local.

Đây là cách hỗ trợ:

```text
GUI event loop
single-thread executor
local state
```

mà không cần clone dữ liệu.

---

# 26. Send của Future

Không đơn giản là:

```text
Future type => Send
```

Compiler phải xét:

```text
state fields live across await
```

Ví dụ:

```text
Future
 ├── Send field
 ├── Send field
 └── !Send field
```

Nếu `!Send field` sống qua suspension:

```text
Future !Send
```

Nếu field chết trước suspension:

```text
Future có thể vẫn Send
```

---

# 27. Đây là điểm rất quan trọng cho hiệu năng

Không cần programmer viết:

```text
Future<'a + Send>
```

hoặc lifetime annotations.

Compiler tự phân tích.

---

# 28. View qua await

Ví dụ:

```axiom
async fn foo(x: view<Data>) {
    await something().await;
    use(x);
}
```

Không được mặc định cho phép.

Vì owner của `x` có thể không còn hợp lệ trong thời gian suspended.

---

# 29. Rule

Một capability:

```text
view<T>
mut_view<T>
```

không được vượt qua `await` nếu compiler không chứng minh được storage contract.

---

# 30. Owned value thì khác

```axiom
async fn foo(data: Data) {
    await something().await;
    use(data);
}
```

`data` là owned state.

Compiler có thể đưa nó vào Future state.

Đây là pattern an toàn và hiệu quả.

---

# 31. Stable storage contract

Có thể cho phép view qua await nếu API explicitly đảm bảo:

```text
owner storage remains valid
```

Ví dụ một executor/storage abstraction đặc biệt.

Nhưng đây là **storage contract**, không phải mặc định.

---

# 32. Await không tự kéo dài lifetime

Đây là rule quan trọng:

```text
await
```

không có nghĩa:

```text
"mọi thứ đang tồn tại phải sống đến khi async fn kết thúc"
```

Chỉ giá trị thực sự cần sống qua suspension mới được giữ.

---

# 33. Drop trong Future

Nếu Future bị drop:

```text
Future
 ↓
Drop
 ↓
drop initialized state fields
```

theo ownership semantics bình thường.

---

# 34. Drop Future không tự cancel I/O

Ví dụ:

```text
Future
  ↓
OS async I/O đang chạy
```

Drop Future không được tự động giả định:

```text
OS operation stopped
```

---

# 35. Vì sao?

Có những operation:

```text
kernel
DMA
GPU
network
disk
```

có thể vẫn đang sử dụng resource.

Do đó cancellation phải explicit.

---

# 36. Cancellation

Nên có abstraction:

```text
CancellationToken
CancellationSource
```

ở library/runtime.

Không cần Core `cancel` keyword.

---

# 37. Cancellation cooperative

Cancellation request:

```text
cancel()
```

không cưỡng bức kill Future ở arbitrary instruction.

Future phải:

```text
observe cancellation
```

và kết thúc an toàn.

---

# 38. Cancellation ≠ panic

Ba trạng thái:

```text
Success
Failure
Cancellation
```

khác nhau.

Ví dụ:

```text
Result<T, E>
```

không nhất thiết encode cancellation.

Library có thể:

```text
Result<T, Error | Cancelled>
```

hoặc type riêng.

---

# 39. Cancellation ≠ Drop

```text
drop(future)
```

không có nghĩa:

```text
cancel external operation
```

Ngược lại:

```text
cancel(token)
```

cũng không nhất thiết ngay lập tức Drop Future.

---

# 40. Async cleanup

Không có:

```text
AsyncDrop
```

trong Core v1.

Lý do:

```text
Drop
```

không được `await`.

Nếu cleanup cần async:

```axiom
resource.close().await?
```

phải được gọi explicit trước khi resource bị Drop.

---

# 41. Ví dụ

```axiom
let connection = Connection.open().await?;

...
connection.close().await?;
```

Sau đó:

```text
Drop(connection)
```

chỉ là final synchronous cleanup.

---

# 42. Panic trong async

Async không tạo failure mechanism riêng.

```axiom
panic("bad state")
```

vẫn là panic.

Executor/runtime quyết định execution-domain policy.

---

# 43. `Result` trong async

```axiom
async fn load() -> Result<Data, Error> {
    let x = read().await?;
    Ok(x)
}
```

`?` vẫn là control-flow lowering bình thường.

Không cần exception machinery.

---

# 44. Async recursion

Một Future không được tự chứa vô hạn chính nó.

Ví dụ recursive async:

```axiom
async fn foo() {
    foo().await;
}
```

phải có indirection/finite representation.

Compiler diagnostic thay vì tạo type vô hạn.

---

# 45. Async traits

Trait:

```axiom
trait Service {
    async fn run(self) -> Result<Data, Error>;
}
```

Compiler có thể biểu diễn:

```text
associated Future type
```

hoặc equivalent compiler-generated representation.

---

# 46. Static async dispatch

Generic/static dispatch mặc định.

```text
T: Service
```

được monomorphize.

Không cần:

```text
heap + vtable
```

chỉ vì async.

---

# 47. Dynamic async dispatch

Nếu:

```text
dyn Service
```

thì dynamic Future representation phải explicit.

Có thể cần:

```text
dyn Future
```

hoặc boxed/erased future library type.

Nhưng đó là **chi phí do programmer chọn dynamic dispatch**.

---

# 48. Async FFI

Không expose compiler-generated Future ABI trực tiếp.

Thay vào đó:

```text
callback
poll handle
opaque context
explicit completion API
```

Ví dụ conceptually:

```text
start_async(...)
register_callback(...)
```

---

# 49. Async I/O ownership

Ví dụ:

```axiom
async fn read(file: File, buffer: Buffer)
```

Nếu OS đang sử dụng buffer:

```text
Buffer ownership
        ↓
in-flight operation
        ↓
completion
        ↓
ownership released
```

Compiler/runtime phải đảm bảo buffer không bị free sớm.

---

# 50. GPU async

GPU operation cũng tương tự:

```text
launch(kernel)
      ↓
GpuEvent
      ↓
device operation
      ↓
completion
```

Không được:

```text
drop(buffer)
```

khi GPU vẫn đang dùng buffer.

Điều này liên kết trực tiếp với GPU storage-domain rules.

---

# 51. Fiber + async

Axiom cho phép:

```text
Future
   ↓
run on Fiber
```

nhưng Future không trở thành Fiber.

Future:

```text
stackless
```

Fiber:

```text
stackful
```

---

# 52. Khi nào dùng Fiber?

Fiber phù hợp:

```text
legacy blocking-style code
game scripting
coroutines cần stack
user-space scheduling
```

Async Future phù hợp:

```text
massive I/O concurrency
network servers
event-driven systems
```

Cả hai có thể tồn tại trong cùng runtime.

---

# 53. Async không bắt buộc runtime

Chương trình:

```axiom
fn main() {
    ...
}
```

không sử dụng async:

```text
không Future runtime
không executor
không waker
```

Executable không mang chúng.

---

# 54. Runtime linking

Nếu chương trình dùng:

```text
async
spawn
network
```

compiler/linker chỉ đưa runtime components cần thiết vào.

Conceptually:

```text
Program
 ├── Future machinery
 ├── scheduler
 ├── I/O backend
 └── allocator
```

Nếu chương trình chỉ dùng:

```text
async fn
```

nhưng tự poll Future:

```text
scheduler có thể không cần
```

---

# 55. Async runtime không phải compiler requirement

Compiler chỉ cần:

```text
async lowering
Future representation
poll semantics
```

Executor là library/runtime.

---

# 56. Optimization

Các pass chính:

```text
StateFieldLiveness
StateFieldElision
FutureInlining
ReadyPathSpecialization
AwaitFusion
StateSwitchOptimization
CoroutineDCE
```

---

# 57. Ready path

Future:

```text
poll()
```

nếu luôn Ready:

```text
Ready(T)
```

compiler có thể inline/eliminate state machine nếu semantics cho phép.

Async syntax không nhất thiết tạo runtime overhead.

---

# 58. Await fusion

Nếu:

```text
await foo()
await bar()
```

compiler có thể tối ưu state transitions khi semantics cho phép.

Không được thay đổi:

- suspension behavior observable
- cancellation points
- scheduling semantics
- ordering.

---

# 59. Cancellation points

Không phải mọi instruction là cancellation point.

Cancellation phải có semantic boundary rõ ràng.

Ví dụ:

```text
await
explicit cancellation check
library operation
```

---

# 60. Blocking trong async

Core không cấm compiler-level function:

```text
blocking syscall
```

nhưng async runtime API phải biết đó là blocking operation.

Nếu scheduler worker bị block, đó là runtime policy issue.

Không biến mọi blocking operation thành magically non-blocking.

---

# 61. Async mutex

Không cho:

```text
MutexGuard
```

thông thường sống qua await.

Vì:

```text
worker A
lock held
await
worker B
```

có thể deadlock/starvation.

---

# 62. AsyncMutex

Runtime/library cung cấp:

```text
AsyncMutex
AsyncRwLock
```

có guard semantics riêng.

Đây là abstraction khác với synchronous `Mutex`.

---

# 63. Async channel

Channel có thể hỗ trợ:

```axiom
let x = rx.recv().await?;
tx.send(x).await?;
```

nhưng underlying channel semantics vẫn là:

```text
ownership transfer
```

không phải shared ownership.

---

# 64. Async channel wait

Khi:

```text
channel empty
```

Future:

```text
WAITING_RECEIVE
```

Không tạo task mới.

Event xảy ra:

```text
WAITING → READY
```

---

# 65. Async channel send

Khi:

```text
bounded channel full
```

Future:

```text
WAITING_SEND
```

Khi slot available:

```text
WAITING → READY
```

---

# 66. Lost wakeup

Channel + async phải đảm bảo:

```text
register waiter
check condition
transition waiting
```

được atomic về mặt synchronization semantics.

Đây là runtime invariant.

---

# 67. Async + ownership transfer

```axiom
tx.send(data).await
```

Nếu send thành công:

```text
data
```

đã Move.

Nếu channel closed:

```text
SendError<T>
```

phải trả ownership của `T`.

Điều này rất phù hợp với Axiom ownership model.

---

# 68. Async + view

Không được:

```axiom
tx.send(view(x))
```

rồi để view tồn tại vượt owner.

Channel không biến view thành owned data.

---

# 69. Async + Arc

Nếu muốn shared state:

```axiom
Arc<T>
```

vẫn phải explicit.

Async không tự động biến:

```text
T
```

thành shared object.

---

# 70. Async + Send/Share

Cần phân biệt:

```text
Future: Send
```

với:

```text
Future: Share
```

Một Future được migration không có nghĩa nhiều executor có thể poll đồng thời.

Thông thường Future polling là exclusive.

---

# 71. Future polling

Không được poll cùng một Future đồng thời từ nhiều execution domains trừ khi Future abstraction explicitly cho phép.

Đây là semantic invariant.

---

# 72. Waker ownership

Waker là capability để yêu cầu scheduler poll lại Future.

Không phải:

```text
ownership of Future
```

và cũng không phải:

```text
permission to mutate arbitrary Future state
```

---

# 73. Executor safety

Executor chỉ được schedule:

```text
verified task
```

Nó không tự thực hiện:

```text
ownership checking
type checking
race checking
```

Compiler/runtime-safe abstraction đã đảm bảo trước đó.

---

# 74. Async task identity

Một Future:

```text
Future A
```

và Task:

```text
Task A
```

không nhất thiết là cùng physical object.

Task là scheduler identity.

Future là computation state.

---

# 75. JoinHandle

`JoinHandle<T>` là:

> observation capability.

Không nhất thiết là:

> ownership của physical task storage.

Do đó:

```text
drop(handle)
```

không nhất thiết destroy task.

Task lifecycle phải theo scheduler policy.

---

# 76. Task cancellation

Library có thể:

```text
handle.cancel()
```

nhưng cancellation phải obey cooperative rules.

Không được tự do:

```text
free task memory
```

khi task đang chạy.

---

# 77. Structured task lifetime

Khuyến nghị runtime:

```text
scope
 ├── task A
 ├── task B
 └── task C
```

scope kết thúc:

```text
join/cancel/wait
```

theo policy.

Detached execution phải explicit.

---

# 78. Async stack usage

Future mặc định stackless nên:

```text
N tasks
```

không cần:

```text
N stacks
```

Đây là ưu điểm lớn so với Fiber.

---

# 79. Async và memory footprint

Compiler chỉ giữ:

```text
live state across await
```

Do đó một Future nhỏ có thể chỉ vài bytes/words.

Không được áp đặt:

```text
Future = large runtime object
```

---

# 80. Async và zero-cost abstraction

Mục tiêu:

```text
async syntax
      ↓
state machine
      ↓
ordinary MIR
      ↓
optimized machine code
```

Không cần runtime overhead nếu program không cần scheduling.

---

# 81. Invariants AASYNC

Các invariant cũ được giữ và freeze:

```text
AASYNC-75   Async is a control-flow abstraction.
AASYNC-76   Async does not imply thread creation.
AASYNC-77   Async does not imply task spawning.
AASYNC-78   Calling async produces a Future.
AASYNC-79   Future is a compiler-generated state machine.
AASYNC-80   Future does not require heap allocation.
AASYNC-81   Future storage is determined by storage analysis.
AASYNC-82   Future state contains only required live state.
AASYNC-83   Await creates a suspension point.
AASYNC-84   Suspension points have stable compiler identity.
AASYNC-85   Poll distinguishes Pending and Ready.
AASYNC-86   Wake is a scheduling notification.
AASYNC-87   Wake is semantically idempotent.
AASYNC-88   Scheduler is not required by Core.
AASYNC-89   Spawn is a scheduling abstraction.
AASYNC-90   Spawn migration requires Send.
AASYNC-91   Spawn-local does not require Send.
AASYNC-92   Future Send depends on migratable state.
AASYNC-93   Future state is ownership checked.
AASYNC-94   Future state is capability checked.
AASYNC-95   Borrowed capabilities cannot cross await without valid contract.
AASYNC-96   Await does not extend resource lifetime implicitly.
AASYNC-97   Future Drop drops initialized state.
AASYNC-98   Future Drop does not imply external operation cancellation.
AASYNC-99   Cancellation is explicit.
AASYNC-100  Drop cannot await.
AASYNC-101  Async cleanup must be explicit.
AASYNC-102  Async panic uses normal panic semantics.
AASYNC-103  Async Result uses normal Result semantics.
AASYNC-104  Async ? uses normal control flow.
AASYNC-105  Recursive futures require finite representation.
AASYNC-106  Async lowering produces ordinary MIR.
AASYNC-107  Backend does not require async knowledge.
AASYNC-108  Future layout is compiler controlled.
AASYNC-109  Future layout may reuse non-overlapping state storage.
AASYNC-110  Future state drops are field sensitive.
AASYNC-111  Async generic resolution occurs before concrete Future lowering.
AASYNC-112  Async trait dispatch is explicitly resolved.
AASYNC-113  Dynamic async dispatch requires explicit dynamic representation.
AASYNC-114  Async FFI requires explicit ABI.
AASYNC-115  Async does not imply runtime registry.
AASYNC-116  Async does not imply global executor.
AASYNC-117  Async optimization cannot change suspension semantics.
```

Bổ sung:

```text
AASYNC-118  Future polling is not concurrent unless explicitly permitted.

AASYNC-119  Future migration is governed by Send.

AASYNC-120  Local Future execution may remain execution-domain affine.

AASYNC-121  Await does not implicitly synchronize arbitrary memory.

AASYNC-122  Wake does not itself establish memory publication semantics.

AASYNC-123  Cancellation is cooperative.

AASYNC-124  Cancellation does not imply immediate resource destruction.

AASYNC-125  Dropping a Future does not imply cancellation of external operations.

AASYNC-126  Async cleanup cannot rely on Drop awaiting.

AASYNC-127  In-flight asynchronous operations must retain required storage.

AASYNC-128  Async I/O lifetime is ownership/capability checked.

AASYNC-129  GPU asynchronous operations obey device storage lifetime.

AASYNC-130  Synchronous guards cannot cross await unless their abstraction explicitly permits it.

AASYNC-131  Async-aware synchronization uses distinct abstractions.

AASYNC-132  Async channel operations preserve ownership-transfer semantics.

AASYNC-133  Failed async ownership transfer returns ownership where API semantics require it.

AASYNC-134  Async does not implicitly introduce shared ownership.

AASYNC-135  Task identity is distinct from Future representation.

AASYNC-136  JoinHandle is an observation capability.

AASYNC-137  Detached execution is explicit.

AASYNC-138  Executor scheduling cannot alter language ownership semantics.

AASYNC-139  Executor scheduling cannot alter type semantics.

AASYNC-140  Future state is not required to have stable physical layout.

AASYNC-141  Future state may be stack, inline, caller-owned, arena, or heap stored.

AASYNC-142  Future storage strategy is not part of ordinary Future semantic identity.

AASYNC-143  Async runtime components are independently linkable.

AASYNC-144  Programs not using async need not link async runtime components.

AASYNC-145  Ready-path optimization may eliminate Future machinery when semantics permit.

AASYNC-146  Async lowering preserves observable suspension points.

AASYNC-147  Async optimization cannot eliminate required cancellation/scheduling semantics.

AASYNC-148  Async FFI requires an explicit foreign completion contract.

AASYNC-149  Foreign async completion cannot outlive required Axiom storage.

AASYNC-150  Async semantics remain valid in freestanding environments when a suitable executor/polling model exists.
```

---

# Kết luận freeze

Mô hình Async của Axiom hiện tại có cấu trúc:

```text
                 ASYNC
                   │
                   ▼
                Future
                   │
              ┌────┴────┐
              │         │
           poll()     await
              │         │
              └────┬────┘
                   ▼
             ordinary MIR
                   │
                   ▼
             machine code
```

Runtime chỉ xuất hiện nếu chương trình cần:

```text
Future
  ↓
Executor
  ↓
Scheduler
  ↓
I/O / Timer / Wake
```

Còn:

```text
async fn
```

bản thân nó **không kéo theo heap, thread, GC, executor hay runtime monolithic**.

Đây là hướng khá phù hợp với mục tiêu ban đầu của Axiom: **ngôn ngữ có abstraction hiện đại nhưng abstraction phải có khả năng biến mất hoàn toàn sau compilation khi không còn ý nghĩa runtime.**

### Task kế tiếp

**BOOTSTRAP-039 — Concurrency Semantics Audit & Freeze**

Phần này sẽ không thiết kế lại Thread/Fiber/Channel/Mutex/Atomic từ đầu, mà sẽ gom và kiểm tra toàn bộ những gì đã thiết kế thành **một concurrency model thống nhất**: `Send`, `Share`, memory model, happens-before, atomic, Mutex/RwLock, Channel, scheduler, Fiber và data-race safety. Đây là bước quan trọng để đảm bảo các phần Async vừa chốt không mâu thuẫn với concurrency core.