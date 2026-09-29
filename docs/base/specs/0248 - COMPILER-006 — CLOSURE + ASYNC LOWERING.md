Tiếp tục **COMPILER-006 — Closure + Async + State-Machine Lowering**.

Mục tiêu của phase này là chốt một nguyên tắc:

> **Closure và async là compile-time transformations. Không có closure runtime chung, không có async runtime bắt buộc, không có object header, không có allocation bắt buộc.**

---

# COMPILER-006 — CLOSURE + ASYNC LOWERING

## 1. Kiến trúc tổng quát

```text
Typed HIR
   │
   ├── Closure Capture Analysis
   │
   ├── Async Suspension Analysis
   │
   ├── State Layout Analysis
   │
   ▼
Verified HIR
   │
   ▼
MIR
   │
   ├── Closure Lowering
   │
   └── Async Lowering
   │
   ▼
Lowered MIR
   │
   ▼
MIR Optimization
```

Closure và async không phải hai hệ thống độc lập hoàn toàn.

Cả hai đều là:

> **Capture + State + Control Flow Transformation**

---

# 2. Closure không phải object

Source:

```axiom
let factor = 10;

let f = |x| x * factor;
```

Không tạo:

```text
ClosureObject
vtable
object header
heap allocation
```

Compiler tạo conceptually:

```text
ClosureType#1 {
    factor: i32
}
```

và function:

```text
ClosureType#1.call(self, x)
```

---

# 3. Closure environment

Closure environment là aggregate thông thường.

```text
ClosureEnv {
    capture_0: T
    capture_1: U
}
```

Không có hidden universal header.

Representation có thể là:

```text
registers
stack
inline aggregate
heap
```

tùy escape analysis.

---

# 4. Ba capture mode

Compiler chỉ cần ba semantic capture modes:

```text
READ
WRITE
MOVE
```

### READ

```axiom
let x = 10;
let f = || use(x);
```

→ closure giữ quyền đọc `x`.

### WRITE

```axiom
var x = 10;
let f = || {
    x = 20;
};
```

→ closure cần mutable access.

### MOVE

```axiom
let x = String(...);

let f = move || consume(x);
```

→ ownership chuyển vào closure.

---

# 5. `move` không có nghĩa heap

Ví dụ:

```axiom
let x = String(...);
let f = move || use(x);
```

`move` chỉ nói:

```text
ownership(x)
     ↓
closure environment
```

Không nói:

```text
heap allocation
```

Compiler có thể đặt closure:

```text
stack
register
inline
```

nếu không escape.

---

# 6. Closure escape analysis

Ví dụ:

```axiom
fn foo() {
    let x = 10;

    let f = |y| x + y;

    f(20);
}
```

Closure không escape.

Compiler có thể inline toàn bộ:

```text
return 30
```

Thậm chí closure type có thể biến mất hoàn toàn.

---

# 7. Closure escaping

```axiom
fn make() -> impl Callable {
    let x = 10;
    move || x
}
```

Closure phải chứa `x`.

Compiler cần storage sống sau return.

Có thể:

```text
caller-owned storage
heap-like dynamic storage
Box
other explicit storage abstraction
```

nhưng **không được tự động biến thành heap chỉ vì closure tồn tại** nếu ABI/storage strategy khác có thể đáp ứng.

---

# 8. Closure function identity

Mỗi closure expression có một anonymous semantic type:

```text
ClosureId
```

Ví dụ:

```axiom
let f = |x| x + 1;
let g = |x| x + 1;
```

`f` và `g` có:

```text
ClosureType#1
ClosureType#2
```

khác nhau.

Không structural-equate closure types.

---

# 9. Noncapturing closure

```axiom
let f = |x: i32| x + 1;
```

nếu không capture:

```text
environment size = 0
```

Compiler có thể cho phép:

```text
closure → function pointer
```

như đã chốt ở TYPE-001.

Không allocation.

---

# 10. Closure call

MIR trước lowering:

```text
CALL_CLOSURE {
    closure: f
    args: [x]
}
```

Sau lowering:

```text
CALL {
    function: ClosureFn#1
    hidden_env: &f
    args: [x]
}
```

Sau ABI lowering:

```text
register/stack arguments
```

---

# 11. Không cần Fn/FnMut/FnOnce trong Core syntax

Ta không nên thêm ba trait bắt buộc kiểu Rust vào ngôn ngữ.

Compiler semantic model chỉ cần:

```text
callable
capture mode
receiver access
```

Library có thể định nghĩa các callable abstractions.

Điều này giữ Core đơn giản.

---

# 12. Closure receiver

Conceptually:

```text
fn closure_call(env: Env, x: T) -> R
```

Nếu chỉ đọc:

```text
env: view<Env>
```

Nếu mutate:

```text
env: mut_view<Env>
```

Nếu consume:

```text
env: Env
```

Như vậy closure semantics tái sử dụng chính ownership model đã có.

---

# 13. Closure lifetime

Không có:

```text
'closure
```

Compiler biết environment dependencies.

Nếu closure chứa:

```text
READ capability → x
```

thì closure không thể outlive `x`.

Nếu muốn closure outlive:

```text
move
```

hoặc owner abstraction phù hợp.

---

# 14. Closure + Send

Ví dụ:

```axiom
Thread.spawn(move || work(data));
```

Closure type được compiler tổng hợp:

```text
Closure {
    data: T
}
```

Sau đó trait facts:

```text
Send(Closure)
```

được suy ra từ capture.

Nếu:

```text
!Send(data)
```

→ closure !Send.

---

# 15. Closure + Share

Nếu closure được concurrent-share:

```text
Share(Closure)
```

phụ thuộc các captured values.

Không có rule:

```text
Closure = always Send/Share
```

---

# 16. Async function

Source:

```axiom
async fn fetch() -> Result<Data, Error> {
    ...
}
```

Không trực tiếp chạy.

Semantic type:

```text
fn fetch() -> Future<Result<Data, Error>>
```

nhưng source signature vẫn có:

```text
async fn
```

để biểu diễn calling semantics.

---

# 17. Async call

```axiom
let future = fetch();
```

Không spawn.

Không thread.

Không executor.

Không syscall.

Chỉ tạo Future state machine.

---

# 18. Future là state machine

Compiler biến:

```axiom
async fn foo() -> T {
    let a = acquire();

    await work(a);

    use(a);

    return result;
}
```

thành conceptually:

```text
FutureFoo {
    state
    a
    ...
}
```

với:

```text
poll(self, context) -> Poll<T>
```

---

# 19. Future không bắt buộc heap

Future có thể:

```text
local variable
stack
inline struct
caller-owned storage
heap via Box
```

Nếu:

```axiom
let future = foo();
await future;
```

compiler có thể inline toàn bộ state machine.

---

# 20. State machine states

Ví dụ:

```text
START
  ↓
call work
  ↓
SUSPENDED_1
  ↓
resume
  ↓
use(a)
  ↓
COMPLETE
```

Future state:

```text
enum State {
    Start,
    Waiting1,
    Complete
}
```

Nhưng đây là **compiler representation**, không nhất thiết source-level enum.

---

# 21. Suspension point

Mỗi:

```axiom
await expr
```

tạo một:

```text
SuspensionPointId
```

Compiler xác định:

```text
values live across suspension
```

---

# 22. Chỉ capture những gì sống qua await

Ví dụ:

```axiom
async fn foo() {
    let a = compute();
    use(a);

    let b = compute();

    await work();

    use(b);
}
```

Future không cần giữ:

```text
a
```

qua suspension.

Chỉ:

```text
b
```

được state-machine field.

Đây là cực kỳ quan trọng để Future nhỏ.

---

# 23. Live-across-await analysis

Compiler thực hiện:

```text
Liveness
+
Ownership
+
Capability
```

để tìm:

```text
LiveAcrossSuspension
```

Ví dụ:

```text
a: dead before await
b: live across await
c: dead before await
```

Future state:

```text
{
    state,
    b
}
```

không phải:

```text
{
    state,
    a,
    b,
    c,
    all locals...
}
```

---

# 24. Borrowed capability across await

Đã chốt:

```text
view/mut_view
```

thông thường không được sống qua await.

Ví dụ:

```axiom
async fn foo(data: Buffer<i32>) {
    let v = view(data);

    await something();

    use(v);
}
```

→ reject.

---

# 25. Nhưng có một ngoại lệ cần thiết

Nếu capability thực sự có explicit storage contract cho phép suspension:

```text
stable shared storage
execution-domain-safe capability
```

thì compiler có thể cho phép.

Không hard-code:

```text
all views can never cross await
```

Mà rule chính xác là:

> Capability chỉ được cross suspension nếu provenance + storage + execution-domain contract chứng minh nó vẫn valid.

Điều này mở đường cho:

- Arc;
- pinned/stable storage abstraction;
- shared memory;
- GPU buffers;
- OS mappings.

---

# 26. Không cần `Pin` Core

Axiom đã quyết:

> Stable address là storage contract, không phải một Core type bắt buộc.

Vì vậy async state machine compiler tự đảm bảo state machine không bị relocation khi đang suspended nếu ABI/representation yêu cầu.

Library có thể cung cấp stable-storage abstractions.

---

# 27. Future ownership

Future itself là owning value.

```axiom
let f = foo();
```

`f` có ownership bình thường.

Có thể:

```text
MOVE
COPY nếu Future Copy
DROP
```

với điều kiện semantics của captured state cho phép.

---

# 28. Future Drop

Nếu Future chưa complete:

```text
drop(f);
```

compiler phải Drop tất cả state đang owned.

Ví dụ:

```text
Future {
    state = Waiting
    file = owned
}
```

Drop Future:

```text
DROP file
```

Không được bỏ qua cleanup.

---

# 29. Nhưng Drop Future không tự cancel OS operation

Đã frozen:

> dropping a Future does not imply cancellation of an external operation.

Ví dụ:

```text
Future
  ↓
OS I/O submitted
```

Drop Future không thể tự giả định:

```text
cancel syscall
```

Trừ khi abstraction explicitly defines cancellation.

---

# 30. Cancellation handle

Nếu cần cancellation:

```axiom
let op = async_read(...);

op.cancel();
```

hoặc:

```text
CancellationToken
```

là library semantics.

Không nhúng cancellation vào `Drop`.

---

# 31. Poll model

Future lowering conceptually:

```text
poll(self, context)
```

returns:

```text
Pending
Ready(value)
```

Nhưng `Poll<T>` có thể là library/compiler-known enum.

Compiler phải tối ưu enum representation mạnh.

---

# 32. Waker

Future không biết scheduler cụ thể.

Khi Pending:

```text
Waker
```

được lưu/registered.

Waker là runtime/library abstraction.

Core async semantics chỉ yêu cầu:

```text
Pending
→ eventually wake
→ poll again
```

---

# 33. Async runtime không bắt buộc

Program:

```axiom
fn main() {
    ...
}
```

không tự link:

```text
executor
reactor
async runtime
```

Chỉ khi dùng:

```axiom
spawn(...)
```

hoặc async executor library.

---

# 34. Single-future synchronous optimization

Nếu compiler thấy:

```axiom
async fn foo() -> i32 {
    let x = compute();
    await immediately_ready();
    x + 1
}
```

có thể optimize state machine.

Thậm chí nếu await operation known-ready:

```text
async overhead → eliminated
```

nếu semantics cho phép.

---

# 35. State layout

Compiler tạo:

```text
FutureLayout {
    fields
    states
    alignment
    drop_flags
}
```

Ví dụ:

```text
state: u8
b: Buffer
future_inner: InnerFuture
```

Nhưng physical layout compiler-controlled.

---

# 36. Partial initialization của Future

Đây là vấn đề khó.

Future có thể:

```text
START
```

chưa initialize toàn bộ fields.

Ví dụ:

```text
state = START
a initialized
b uninitialized
```

Nếu Future bị Drop trước khi reaching state:

```text
drop only initialized fields
```

Do đó Future cần **drop flags / state-derived initialization facts**.

Không nhất thiết phải lưu một bool cho từng field.

Compiler có thể derive:

```text
state → initialized fields
```

để giảm size.

---

# 37. State-derived drop

Ví dụ:

```text
State START:
    a initialized
    b uninitialized

State WAITING:
    a initialized
    b initialized
```

Drop:

```text
if START:
    drop a

if WAITING:
    drop b
    drop a
```

Compiler có thể optimize thành state switch.

---

# 38. State-machine representation

MIR:

```text
ASYNC_STATE {
    state_id
    fields
    suspension_points
}
```

Sau lowering thành ordinary MIR:

```text
LOAD state
SWITCH state

STATE_0:
    ...

STATE_1:
    ...

STATE_2:
    ...
```

Từ đây backend không cần biết async là gì.

Đây là **abstraction erasure** rất đẹp.

---

# 39. Async function return ABI

Source:

```axiom
async fn foo() -> T
```

source-level return:

```text
Future<T>
```

Không ABI trực tiếp:

```text
T
```

Future object được trả theo ordinary Axiom ABI.

Nếu compiler inline/optimize async call, Future có thể biến mất.

---

# 40. Async recursion

Ví dụ:

```axiom
async fn foo() {
    await foo();
}
```

Không thể tạo infinite-sized Future trực tiếp.

Compiler reject hoặc yêu cầu indirection:

```text
Box<Future>
```

tương tự recursive type.

Không tự động heap allocate recursion vì điều đó thay đổi semantics/performance.

---

# 41. Async recursion through explicit storage

```axiom
async fn foo() {
    let next = Box::new(foo());
    await next;
}
```

storage decision explicit.

---

# 42. Async trait methods

Trait:

```axiom
trait Service {
    async fn run(self);
}
```

Không nên biến async trait thành hidden dynamic runtime.

Static generic dispatch:

```text
Service::run<T>
```

monomorphize.

Dynamic:

```text
dyn Service
```

phải có explicit dynamic ABI cho async method.

---

# 43. Dynamic async dispatch

Một `dyn Trait` async method có thể cần:

```text
vtable slot
→ function returning Future
```

Future layout phải có ABI contract.

Không có universal runtime object.

---

# 44. Spawn

```axiom
spawn(foo());
```

`spawn` không phải Core instruction semantics về scheduler.

Compiler verifies:

```text
Future: Send
```

nếu scheduler có thể migrate task.

Sau đó library scheduler nhận:

```text
Future
```

---

# 45. `spawn_local`

```axiom
spawn_local(foo());
```

không yêu cầu Send nếu execution domain affine.

Nhưng Future vẫn phải satisfy local lifetime/storage rules.

---

# 46. Structured concurrency

Compiler/library design nên ưu tiên:

```text
scope {
    spawn(...)
}
```

và join children trước khi scope kết thúc.

Detached execution phải explicit:

```text
detach(...)
```

Không tự detach.

---

# 47. Async + ownership transfer

```axiom
let x = resource;

spawn(async move {
    use(x);
});
```

ownership:

```text
x
 ↓ MOVE
Future
 ↓ MOVE
Task
```

Không có copy.

---

# 48. Async + closure

Thực tế:

```axiom
async move |x| {
    await work(x);
}
```

nên được compiler xem là:

```text
Closure
+
Future state machine
```

Capture analysis trước:

```text
closure environment
```

sau đó async analysis xác định state sống qua await.

---

# 49. Generator/future abstraction

Không nên tạo một Core `Generator` riêng nếu không cần.

Async lowering đã có:

```text
state
suspend
resume
yield-like transition
```

Sau này generator có thể reuse machinery.

Do đó internal abstraction:

```text
CoroutineStateMachine
```

thay vì:

```text
AsyncCompiler
GeneratorCompiler
CoroutineCompiler
```

ba hệ thống khác nhau.

---

# 50. Coroutine state machine generic

Concept:

```text
Coroutine {
    state
    live_fields
    resume
    drop
}
```

Async:

```text
resume = poll
```

Generator:

```text
resume = next
```

Có thể reuse compiler infrastructure.

---

# 51. Yield chưa cần Core syntax v1

Không cần thêm:

```text
yield
```

vào core hiện tại chỉ để hỗ trợ generator.

Infrastructure có thể tồn tại nội bộ.

---

# 52. Closure optimization

Passes:

```text
ClosureElision
CaptureScalarization
CapturePromotion
ClosureInlining
EnvironmentSROA
```

Ví dụ:

```axiom
let factor = 10;
let f = |x| x * factor;
return f(3);
```

có thể thành:

```text
return 30;
```

Không closure runtime.

---

# 53. Async optimization

Passes:

```text
StateFieldLiveness
StateFieldElision
AwaitFusion
FutureInlining
ReadyPathSpecialization
StateSwitchOptimization
CoroutineDCE
```

Mục tiêu:

```text
small state
few branches
no unnecessary allocation
```

---

# 54. Async allocation optimization

Không:

```text
async → heap
```

mặc định.

Ví dụ:

```axiom
async fn foo() -> i32
```

caller:

```axiom
let f = foo();
await f;
```

Future có thể nằm hoàn toàn trên caller stack hoặc được scalarized.

Chỉ khi:

```text
Future escapes
spawned
stored dynamically
```

mới cần dynamic storage nếu abstraction yêu cầu.

---

# 55. Future size inspection

Tooling nên hỗ trợ:

```bash
axiom inspect --async foo
```

hiển thị:

```text
Future size: 48 bytes

state 0:
  x: i32

state 1:
  x: i32
  buffer: Buffer<u8>

state 2:
  result: i64
```

Rất hữu ích cho performance.

---

# 56. Closure inspection

Tương tự:

```bash
axiom inspect --closure foo
```

hiển thị:

```text
Closure #1
captures:
  x: READ
  buffer: MOVE

size: 24 bytes
alignment: 8
```

AI agent cũng có thể sử dụng JSON.

---

# 57. Async diagnostics

Namespace:

```text
AX16xx
```

Ví dụ:

```text
AX1601 invalid async state
AX1602 capability cannot cross await
AX1603 non-Send future used in migratable spawn
AX1604 invalid async capture
AX1605 recursive future has infinite size
AX1606 invalid future drop state
AX1607 future field may be uninitialized
AX1608 invalid suspension point
AX1609 detached task requires explicit detach
AX1610 synchronous guard crosses await
AX1611 async ABI mismatch
```

---

# 58. Closure diagnostics

```text
AX16xx
```

có thể cùng namespace nhưng nên phân biệt:

```text
AX1620 invalid closure capture
AX1621 closure capture requires mutable access
AX1622 closure capture would move value
AX1623 closure escapes borrowed storage
AX1624 closure is not Send
AX1625 closure is not Share
AX1626 invalid closure-to-function-pointer conversion
```

---

# 59. COMPILER-006 invariants

```text
ACLOS-20  Every Closure Has A Stable Semantic Identity
ACLOS-21  Closure Environment Contains Only Required Captures
ACLOS-22  Capture Mode Is READ, WRITE, Or MOVE
ACLOS-23  Capture Mode Is Compiler Verified
ACLOS-24  Closure Does Not Imply Heap Allocation
ACLOS-25  Noncapturing Closure May Convert To Function Pointer
ACLOS-26  Closure Lifetime Cannot Exceed Captured Provenance
ACLOS-27  Closure Send/Share Depends On Captured State
ACLOS-28  Closure Environment Uses Ordinary Ownership Semantics
ACLOS-29  Closure Dispatch Is Resolved Before ABI Lowering
ACLOS-30  Closure Elision May Remove Runtime Closure Representation

AASYNC-75  Async Functions Produce Owned Future State
AASYNC-76  Calling Async Does Not Imply Execution
AASYNC-77  Await Is A Suspension Boundary
AASYNC-78  Only Live State Crosses Suspension
AASYNC-79  Borrowed Capabilities Cannot Cross Invalid Suspension
AASYNC-80  Owned Values May Cross Suspension
AASYNC-81  Future State Layout Is Compiler Generated
AASYNC-82  Future Does Not Require Heap Allocation
AASYNC-83  Future Drop Cleans Only Initialized State
AASYNC-84  State-Derived Drop Is Correct
AASYNC-85  Dropping A Future Does Not Imply External Cancellation
AASYNC-86  Cancellation Is Explicit
AASYNC-87  Recursive Futures Require Finite Representation
AASYNC-88  Spawn Migration Requires Send
AASYNC-89  Local Spawn Does Not Require Cross-Domain Send
AASYNC-90  Detached Execution Is Explicit
AASYNC-91  Async Lowering Produces Ordinary MIR
AASYNC-92  Backend Does Not Require Async Semantics
AASYNC-93  Async Runtime Is Optional
AASYNC-94  Future Optimization May Eliminate State
AASYNC-95  Suspension State Is Deterministic
AASYNC-96  Future ABI Is Explicit
AASYNC-97  Async Trait Dispatch Does Not Imply Allocation
AASYNC-98  Async State Does Not Require Object Headers
AASYNC-99  Coroutine Infrastructure May Be Shared By Future-Like Abstractions
```

---

# 60. Ví dụ hoàn chỉnh

Source:

```axiom
async fn process(buffer: Buffer<u8>) -> Result<usize, Error> {
    let header = parse_header(view(buffer))?;

    let result = await read_more(buffer);

    return process_result(header, result);
}
```

Compiler phân tích:

### Trước await

```text
buffer       Owned
header       Owned
view(buffer) ephemeral
```

Sau khi `parse_header` hoàn thành:

```text
view(buffer)
```

dead.

### Tại await:

```text
buffer  LIVE
header  LIVE
```

Future state:

```text
State1 {
    buffer
    header
}
```

Không giữ view.

### Resume:

```text
buffer
header
result
```

### Complete:

```text
DROP result if needed
DROP header
DROP buffer
RETURN
```

Nếu `buffer` được consumed bởi `read_more`, ownership state thay đổi tương ứng và compiler cập nhật state machine.

---

# 61. Điều quan trọng nhất

Với thiết kế này, source-level async:

```axiom
async fn foo() { ... }
```

có thể cuối cùng trở thành:

```text
ordinary struct
+
ordinary function
+
ordinary switch
+
ordinary memory/register operations
```

Không còn:

```text
async runtime magic
```

ở backend.

Tương tự closure:

```text
closure
```

có thể cuối cùng trở thành:

```text
ordinary function
+
ordinary aggregate
```

hoặc thậm chí biến mất hoàn toàn.

Đây chính xác là **zero-cost abstraction** mà Axiom đang hướng tới.

---

# 62. Chuỗi compiler hiện tại

Đến đây:

```text
COMPILER-001
Lexer / Parser
        ↓
COMPILER-002
Resolver / HIR
        ↓
COMPILER-003
Type / Trait
        ↓
COMPILER-004
Ownership / Capability
        ↓
COMPILER-005
MIR
        ↓
COMPILER-006
Closure / Async / Coroutine lowering
```

Bước tiếp theo hợp lý là:

## **COMPILER-007 — Semantic MIR Optimization**

Đây là lúc bắt đầu giải quyết trực tiếp mục tiêu hiệu năng:

- constant propagation;
- SCCP;
- dead code;
- copy propagation;
- scalar replacement;
- aggregate optimization;
- alias-aware load/store optimization;
- escape analysis;
- allocation elimination;
- inlining;
- devirtualization;
- generic code dedup;
- loop optimization;
- vectorization preparation;
- tail-call optimization;
- panic-path optimization;
- Drop elimination;
- capability-proof erasure.

Đặc biệt, **COMPILER-007 sẽ là nơi quyết định Axiom có thực sự biến ownership/capability abstraction thành “zero-cost” hay không**.