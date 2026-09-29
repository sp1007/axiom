# BOOTSTRAP-360 — Axiom Async/Await Lowering & Coroutine State Machine Engine

Sau `BOOTSTRAP-359`, cleanup semantics đã đủ nền tảng để xử lý async một cách thống nhất. Task này đóng băng **cách `async/await` được compiler biến thành state machine**, nhưng không biến executor/runtime thành một phần bắt buộc của Core.

Mục tiêu chính:

> `async/await` phải là một phép biến đổi control-flow + storage của compiler, không phải một runtime object model.

---

## 1. Nguyên tắc nền tảng

Axiom giữ nguyên:

```text
async fn ≠ thread
async fn ≠ spawn
async fn ≠ task
async fn ≠ heap allocation
async fn ≠ runtime scheduler
```

`async fn` chỉ mô tả:

> Một computation có thể tạm dừng và tiếp tục.

Ví dụ:

```axiom
async fn load() -> Data {
    let a = await read_a();
    let b = await read_b();

    combine(a, b)
}
```

Không có nghĩa compiler tự tạo thread.

---

# 2. Semantic model

Một:

```axiom
async fn f(...) -> T
```

có semantic return:

```text
Future<T>
```

Nhưng `Future<T>` không nhất thiết là object runtime.

Compiler có thể biến nó thành:

```text
StateMachine_f
```

với:

```text
state
captured arguments
live locals
suspension metadata
```

Nếu optimizer chứng minh computation không thực sự suspend, toàn bộ state machine có thể được loại bỏ.

---

# 3. Future là structural type

Không dùng:

```text
interface Future
virtual poll()
vtable
heap object
```

làm mặc định.

Future concrete được compiler sinh:

```text
Future_f
```

và:

```text
Future_f : Future
```

là quan hệ semantic/compiler-level.

Static dispatch mặc định.

Dynamic future chỉ xuất hiện khi programmer yêu cầu abstraction phù hợp.

---

# 4. Async lowering

Pipeline:

```text
Async HIR
   ↓
Await discovery
   ↓
Suspension-point analysis
   ↓
Live-across-await analysis
   ↓
Future state layout
   ↓
State-machine construction
   ↓
Cleanup integration
   ↓
Poll function generation
   ↓
Async verification
   ↓
Ordinary MIR
```

Điểm quan trọng:

> Backend cuối cùng không cần hiểu `async`.

---

# 5. Suspension Point

Mỗi:

```axiom
await future
```

được compiler gán:

```text
SuspensionPointId
```

Ví dụ:

```axiom
async fn f() {
    let a = await get_a();
    let b = await get_b(a);

    use(a, b);
}
```

có:

```text
SP0 = await get_a()
SP1 = await get_b(a)
```

Mỗi suspension point là một boundary mà compiler phải phân tích:

- local nào còn sống;
- capability nào còn sống;
- resource nào phải tồn tại;
- state nào phải lưu;
- execution/storage domain;
- Send requirement.

---

# 6. Live-across-await

Đây là phân tích quan trọng nhất.

Ví dụ:

```axiom
async fn f() {
    let a = create_a();
    let b = create_b();

    use(b);

    await work();

    use(a);
}
```

Sau `await`:

```text
a = LIVE
b = DEAD
```

Future state chỉ cần:

```text
State {
    a
}
```

không cần:

```text
b
```

---

# 7. Không lưu toàn bộ local

Không được triển khai đơn giản kiểu:

```text
Future {
    every local variable
}
```

vì sẽ làm Future phình to.

Compiler phải tính:

```text
LiveAcrossAwait(LocalId, SuspensionPointId)
```

và chỉ materialize những local cần thiết.

---

# 8. State Machine

Ví dụ:

```axiom
async fn f() -> i32 {
    let a = await get_a();
    let b = await get_b();

    a + b
}
```

có thể trở thành conceptually:

```text
State 0:
    start get_a
    if Pending → state = 1
    if Ready(a) → continue

State 1:
    poll get_a
    if Pending → Pending
    if Ready(a) → state = 2

State 2:
    poll get_b
    if Pending → state = 3
    if Ready(b) → compute

State 3:
    poll get_b
    if Pending → Pending
    if Ready(b) → compute

State Done:
    Ready(a + b)
```

Implementation thực tế có thể tối ưu khác, nhưng semantic state transitions phải tương đương.

---

# 9. Future Poll model

Core semantic primitive:

```text
Poll<T> =
    Ready(T)
    Pending
```

`Pending` không có nghĩa computation thất bại.

Nó có nghĩa:

> computation chưa thể tiếp tục tại thời điểm poll hiện tại.

---

# 10. Waker

Waker không thuộc semantic computation của `Future`.

Nó thuộc scheduling/executor abstraction.

Future chỉ có thể nói:

```text
Pending
```

và đăng ký cơ chế đánh thức theo executor contract.

Do đó:

```text
Future
   ↓
Poll
   ↓
Executor
   ↓
Waker
```

không phải:

```text
Future → spawn thread
```

---

# 11. `await` semantics

`await`:

1. evaluate operand đúng một lần;
2. poll Future;
3. nếu Ready → tiếp tục;
4. nếu Pending → lưu state cần thiết;
5. return Pending từ outer Future;
6. khi được poll lại → resume đúng suspension point.

Evaluation order vẫn tuân theo Core:

```text
left-to-right
exactly-once
```

---

# 12. Await không spawn

Ví dụ:

```axiom
let a = await f();
```

chỉ chờ `f`.

Không có:

```text
thread
task
executor registration
```

trừ khi library API làm điều đó.

---

# 13. Sequential vs concurrent

Hai đoạn:

```axiom
let a = await f();
let b = await g();
```

là tuần tự.

Nếu muốn chạy đồng thời:

```axiom
let fa = f();
let fb = g();

let (a, b) = await join(fa, fb);
```

`join` là abstraction library/compiler có thể optimize.

Đây là nguyên tắc:

> `async` tạo khả năng suspension; nó không tự tạo concurrency.

---

# 14. Future Ownership

Future là một owning value nếu chứa state/resource.

Do đó:

```axiom
let f = operation();
```

có ownership semantics bình thường.

Move:

```axiom
let g = f;
```

làm:

```text
f = Moved
g = Owned
```

Không có hidden reference counting.

---

# 15. Drop Future

Nếu:

```axiom
let f = operation();
drop(f);
```

Future state phải được cleanup theo `BOOTSTRAP-359`.

Ví dụ Future chứa:

```text
buffer
socket_state
child_future
```

thì các resource này được drop theo ownership semantics.

Nhưng:

> Drop Future không mặc định có nghĩa external I/O operation đã bị cancel.

Cancellation phải do operation/executor contract quy định.

---

# 16. Cancellation

Axiom không cho phép:

```text
force kill async computation
```

một cách tùy tiện.

Cancellation mặc định cooperative.

Ví dụ library có:

```axiom
CancellationToken
```

hoặc:

```axiom
cancel(handle)
```

thì Future phải kiểm tra cancellation tại các boundary thích hợp.

Core không cần scheduler-specific cancellation protocol.

---

# 17. Cleanup qua await

Đây là phần `BOOTSTRAP-359` cung cấp trực tiếp.

Ví dụ:

```axiom
async fn f() {
    let resource = acquire();

    defer {
        release(resource);
    }

    await work();

    use(resource);
}
```

`resource` sống qua await nên trở thành Future state.

Conceptual:

```text
Future {
    state
    resource
}
```

Khi Future hoàn thành hoặc bị drop:

```text
CleanupGraph
    ↓
release(resource)
```

Không tạo một hệ thống cleanup thứ hai cho async.

---

# 18. View không được tùy tiện vượt qua await

Ví dụ:

```axiom
async fn f(data: view<u8>) {
    await work();
    process(data);
}
```

Không được mặc định chấp nhận.

Vì `data` có thể tham chiếu storage không còn valid trong thời gian Future sống.

Compiler phải kiểm tra:

```text
view(data)
    ↓
await
    ↓
live
```

Nếu không có execution/storage contract chứng minh validity:

```text
ERROR
```

---

# 19. Owned value qua await

Ngược lại:

```axiom
async fn f(data: Buffer) {
    await work();
    process(data);
}
```

có thể hợp lệ vì Future sở hữu `data`.

Compiler đưa:

```text
data
```

vào state machine nếu cần.

---

# 20. `mut_view` qua await

Đây là trường hợp nguy hiểm hơn.

```axiom
async fn f(data: mut_view<u8>) {
    await work();
    modify(data);
}
```

không được cho phép mặc định.

Lý do không chỉ lifetime mà còn:

- exclusive capability;
- Future có thể được giữ lâu;
- Future có thể migrate;
- owner có thể bị truy cập ở nơi khác.

Chỉ cho phép nếu execution/storage contract chứng minh capability vẫn hợp lệ.

---

# 21. Send của Future

Một Future có:

```text
Send
```

chỉ khi **toàn bộ state có thể tồn tại qua suspension** thỏa `Send`.

Ví dụ:

```text
Future {
    String       → Send
    i32          → Send
    Rc<T>        → !Send
}
```

Nếu `Rc<T>` chỉ sống trước await:

```text
Rc<T>
  ↓
dead before await
```

thì nó không nhất thiết làm Future !Send.

Đây là lý do live-across-await analysis rất quan trọng.

---

# 22. Future `Share`

Future chỉ `Share` nếu state cho phép concurrent observation theo semantics của `Share`.

Không suy ra:

```text
Send ⇒ Share
```

và cũng không:

```text
Share ⇒ Send
```

---

# 23. `spawn`

`spawn` thuộc runtime/library.

Ví dụ:

```axiom
spawn(f());
```

API có thể yêu cầu:

```text
Future: Send + 'static-equivalent storage
```

nhưng Axiom không dùng lifetime syntax kiểu:

```text
Future + 'static
```

thay vào đó compiler kiểm tra semantic escape/storage contract.

---

# 24. `spawn_local`

Executor local có thể cung cấp:

```axiom
spawn_local(f());
```

Future không cần `Send` nếu executor đảm bảo nó không migrate sang execution domain khác.

Đây là ví dụ:

> Compiler kiểm tra capability; executor cung cấp execution policy.

---

# 25. Future migration

Nếu Future có thể migrate giữa worker threads:

```text
Future state
    ↓
Worker A
    ↓
Pending
    ↓
Worker B
```

mọi state live across await phải thỏa execution-domain requirements.

Nếu Future chứa:

```text
thread-local capability
```

thì Future có thể bị đánh dấu:

```text
PinnedExecution
```

hoặc `!Send`.

Không cần programmer viết lifetime.

---

# 26. Async recursion

Không cho:

```axiom
async fn f() {
    await f();
}
```

theo cách tạo Future vô hạn về kích thước.

Compiler phải phát hiện recursive Future layout.

Muốn recursion phải có finite indirection:

```text
Box<Future>
```

hoặc abstraction tương đương.

Điều này là vấn đề **size/layout**, không phải ownership hack.

---

# 27. Async closure

Closure:

```axiom
let f = async |x| {
    await work(x);
    process(x);
};
```

được xử lý:

```text
Closure
    ↓
capture analysis
    ↓
async lowering
    ↓
Future state
```

Không tạo:

```text
Closure runtime object + Future runtime object
```

trừ khi representation thực sự cần.

---

# 28. Async generic

Ví dụ:

```axiom
async fn map<T, U>(
    x: T,
    f: fn(T) -> U
) -> U {
    await work();
    f(x)
}
```

Future layout phụ thuộc specialization.

Compiler có thể:

```text
map<i32, f32>
map<MyType, MyType>
```

tạo các state layouts khác nhau.

Không cần universal boxed state machine.

---

# 29. Async trait

Trait:

```axiom
trait Service {
    async fn run(self);
}
```

Static dispatch:

```text
impl Service for Server
```

có thể tạo concrete Future type.

Dynamic:

```text
dyn Service
```

lại là vấn đề object safety/DynSafe và dynamic Future representation.

Không để async tự động biến mọi Future thành heap box.

---

# 30. State Layout

CompilerDB cần:

```text
AsyncStateLayout {
    FutureType
    StateDiscriminant
    fields
    field_types
    field_sources
    suspension_points
    cleanup_metadata
    alignment
    size
}
```

Field nào xuất hiện phải có lý do:

```text
LiveAcrossAwait
Captured
PendingOperation
CleanupDependency
```

Không được thêm field chỉ vì implementation tiện.

---

# 31. State Discriminant

Compiler cần semantic state:

```text
START
SUSPENDED_0
SUSPENDED_1
...
COMPLETED
PANICKED
```

Nhưng physical representation có thể tối ưu.

Ví dụ niche optimization có thể encode state trong một field nếu hợp lệ.

State number không phải ABI bắt buộc.

---

# 32. State Transition Verification

Mỗi transition phải chứng minh:

```text
old state
   ↓
poll
   ↓
Ready/Pending
   ↓
new state
```

và:

- ownership đúng;
- capability đúng;
- cleanup obligations đúng;
- no double initialization;
- no use-after-move;
- no invalid state.

---

# 33. Await Boundary là một Compiler Barrier Semantic

Trước:

```text
await
```

compiler không được tùy tiện di chuyển operation qua boundary nếu làm thay đổi:

- observable side effect;
- ownership;
- synchronization;
- timing-sensitive semantics;
- resource lifetime;
- panic behavior.

Optimizer vẫn có thể thực hiện motion nếu chứng minh semantic equivalence.

---

# 34. Await Fusion

Nếu:

```axiom
let x = await ready_future();
```

compiler chứng minh Future luôn `Ready`:

```text
await
```

có thể được loại bỏ.

Ví dụ:

```text
async fn f() {
    let x = await immediate(42);
    return x;
}
```

có thể lower thành computation bình thường.

Không bắt buộc tạo state machine runtime.

---

# 35. Ready Path Specialization

Một Future có:

```text
fast Ready path
slow Pending path
```

compiler có thể tạo:

```text
poll_fast
poll_slow
```

hoặc branch specialization.

Mục tiêu là giảm overhead của async trong trường hợp I/O đã sẵn sàng.

---

# 36. State Field Elimination

Ví dụ:

```axiom
let temp = calculate();
await io();
```

nếu `temp` không được dùng sau await:

```text
temp
 ↓
dead before await
```

thì không lưu vào Future.

Nếu compiler có thể recompute rẻ hơn lưu:

```text
recompute vs spill
```

đó là optimization decision, nhưng semantic requirement vẫn chỉ là:

```text
temp not required across await
```

---

# 37. Future Size Optimization

Future size rất quan trọng.

Compiler nên có các pass:

```text
AsyncStateFieldLiveness
AsyncStateFieldElimination
AsyncStatePacking
AsyncStateReuse
AsyncStateScalarReplacement
```

Có thể tái sử dụng storage của các local có lifetime không overlap.

---

# 38. Async + Stack

Không phải Future luôn heap.

Có thể:

```text
caller stack
registers
inline aggregate
arena
heap
```

tùy escape analysis.

Ví dụ:

```axiom
let f = local_async();
await f;
```

nếu Future không escape:

```text
stack/register
```

hoàn toàn có thể.

---

# 39. Async + Heap

Heap chỉ cần khi abstraction yêu cầu escape.

Ví dụ:

```axiom
spawn(f());
```

executor có thể cần lưu Future lâu hơn caller.

Compiler/runtime có thể chọn heap/arena/slab.

Nhưng Core không quy định:

```text
async => heap allocation
```

---

# 40. Async FFI

Không tự động biến:

```text
extern fn async_operation(...)
```

thành Axiom Future.

FFI phải khai báo contract:

```text
callback
poll handle
completion event
opaque operation
```

Ví dụ:

```text
C API
    ↓
opaque handle
    ↓
Axiom Future wrapper
```

là library abstraction.

---

# 41. Async ABI

Axiom ABI của:

```axiom
async fn f() -> T
```

không phải target ABI của một hàm C bình thường.

Compiler trước tiên lower:

```text
async fn
    ↓
concrete Future
    ↓
poll(state)
```

sau đó mới ABI-lower.

Điều này giữ ABI logic rõ ràng.

---

# 42. Async Error Handling

```axiom
async fn f() -> Result<T, E>
```

không tạo exception.

`Result` vẫn là algebraic value.

```axiom
let x = await operation()?;
```

được lower thành:

```text
poll operation
    ↓
Ready(Ok)
    ↓
continue

Ready(Err)
    ↓
cleanup
    ↓
return Err
```

`?` và async cùng dùng CleanupGraph.

---

# 43. Async Panic

Nếu:

```text
panic = abort
```

panic có thể kết thúc process theo profile.

Nếu:

```text
panic = unwind
```

Future state phải unwind đúng cleanup path.

Không có một async-specific panic model.

---

# 44. Async Debugging

Compiler phải giữ mapping:

```text
SuspensionPointId
        ↓
source await
        ↓
Future state
        ↓
MIR
        ↓
machine code
```

Debugger có thể hiển thị:

```text
Future f
State: waiting at line 27
```

mà không cần programmer biết state-machine implementation.

---

# 45. CompilerDB additions

Thêm:

```text
AsyncDB
AsyncFunctionDB
AsyncBodyDB
AwaitDB
SuspensionPointDB
AsyncStateDB
AsyncStateLayoutDB
AsyncStateFieldDB
AsyncTransitionDB
AsyncPollDB
FutureTypeDB
FutureLayoutDB
FutureSendShareDB
AsyncCleanupDB
AsyncCancellationDB
AsyncSpawnDB
AsyncFfiDB
AsyncOptimizationDB
```

Các query chính:

```text
async_info(FunctionId)
await_points(FunctionId)
live_across_await(FunctionId, SuspensionPointId)
future_state_layout(FunctionId)
future_state_fields(FunctionId)
future_transitions(FunctionId)
future_send(FunctionId)
future_share(FunctionId)
async_cleanup(FunctionId)
lower_async(FunctionId)
verify_async(FunctionId)
```

---

# 46. MIR additions

Pre-lowering MIR:

```text
AWAIT future
SUSPEND SuspensionPointId
```

Sau async lowering:

```text
SWITCH state
POLL future
IF Pending
SAVE state
RETURN Pending

IF Ready
LOAD state
CONTINUE
```

Backend cuối cùng chỉ thấy ordinary MIR.

---

# 47. Verification invariants

Đóng băng:

```text
AASYNC-01
async fn does not imply thread creation.

AASYNC-02
async fn does not imply task spawning.

AASYNC-03
async execution is represented by a Future computation.

AASYNC-04
await evaluates its operand exactly once.

AASYNC-05
await resumes at exactly the corresponding suspension point.

AASYNC-06
only values live across await become persistent state.

AASYNC-07
dead-before-await locals are not required in future state.

AASYNC-08
future state obeys normal ownership semantics.

AASYNC-09
moved values cannot be used after suspension.

AASYNC-10
invalid views cannot cross await.

AASYNC-11
mutable capabilities cannot cross await without a valid execution/storage contract.

AASYNC-12
Future Send is derived from state that may survive suspension.

AASYNC-13
Future Share is derived independently from Send.

AASYNC-14
spawn is a runtime/library operation, not Core async semantics.

AASYNC-15
spawn requires the execution contract necessary for migration.

AASYNC-16
spawn_local may avoid Send requirements when executor guarantees locality.

AASYNC-17
Future destruction uses the common Cleanup Engine.

AASYNC-18
dropping a Future does not imply cancellation of external operations.

AASYNC-19
cancellation is cooperative unless an explicit execution contract states otherwise.

AASYNC-20
recursive Future layout must remain finite.

AASYNC-21
async closures use ordinary closure capture semantics.

AASYNC-22
async generic functions preserve generic ownership semantics.

AASYNC-23
async trait implementations preserve static dispatch by default.

AASYNC-24
dynamic async dispatch is explicit.

AASYNC-25
async lowering introduces no mandatory heap allocation.

AASYNC-26
async lowering introduces no mandatory runtime dependency.

AASYNC-27
state-machine layout is compiler-controlled unless an ABI contract says otherwise.

AASYNC-28
state transitions preserve ownership, capability and cleanup invariants.

AASYNC-29
optimization cannot change observable suspension semantics.

AASYNC-30
async lowering produces ordinary verified MIR before backend optimization.
```

---

## 48. Kiến trúc sau BOOTSTRAP-360

Axiom hiện có chuỗi rất sạch:

```text
Source
  │
  ├── Ownership
  ├── Capability
  ├── Control Flow
  ├── Drop/Defer
  └── Async
          │
          ↓
      Semantic MIR
          │
          ↓
     Cleanup Elaboration
          │
          ↓
    Async State Lowering
          │
          ↓
      Verified MIR
          │
          ↓
       Optimizer
          │
          ↓
       Machine IR
```

Điểm đáng chú ý là **async không cần thêm một “hệ thống bộ nhớ” mới**. Nó tái sử dụng hoàn toàn:

- Ownership;
- Capability;
- Escape analysis;
- Storage lifetime;
- Cleanup Graph;
- Send/Share;
- ABI;
- MIR.

Đây chính là kiểu thiết kế giúp Axiom giữ được ngôn ngữ tương đối đơn giản ở phía programmer nhưng compiler vẫn đủ khả năng thực hiện những tối ưu rất sâu.