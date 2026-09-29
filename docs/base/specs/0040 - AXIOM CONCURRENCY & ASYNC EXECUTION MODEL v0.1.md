Tiếp tục. Tôi nghĩ đây là lúc phải **đóng đinh mô hình concurrency/async ở mức thực thi**, vì nếu chỉ dừng ở `Send/Share + await` thì agent sau này rất dễ tự chế thêm các cơ chế phức tạp.

# AXIOM CONCURRENCY & ASYNC EXECUTION MODEL v0.1

## 1. Nguyên tắc lớn

Axiom không coi:

```text
thread
async
task
executor
```

là cùng một thứ.

Phân biệt:

```text
Thread  = execution resource
Task    = unit of work
Async   = suspension model
Executor = scheduling mechanism
Future  = suspended computation state
```

Đây là nền tảng.

---

# 2. Thread

Thread là execution context do OS hoặc platform cung cấp.

```text
Thread
├── stack
├── registers
├── execution state
└── thread-local storage
```

Axiom không cần quản lý lifetime bằng GC.

Ví dụ:

```axiom
fn worker(data: Data) {
    ...
}

let t = Thread.spawn(worker, data)
t.join()
```

Ownership:

```text
data
 ↓ MOVE
worker thread
```

Compiler kiểm tra `Send`.

---

# 3. `Send`

`Send` có nghĩa:

> Giá trị có thể chuyển quyền sở hữu sang execution context khác.

Ví dụ:

```text
Vec<i32>
```

thường có thể `Send`.

Nhưng:

```text
raw pointer
```

không nhất thiết `Send` trong safe code.

Điểm quan trọng:

```text
Send ≠ thread safe
```

---

# 4. `Share`

`Share` có nghĩa:

> Giá trị có thể được nhiều execution context cùng truy cập theo shared-access rules.

Ví dụ:

```text
Immutable configuration
```

có thể:

```text
Share
```

nhưng một:

```text
Mutex<T>
```

có thể cung cấp shared access an toàn dù `T` bên trong mutable.

Do đó:

> Không suy ra `Share` chỉ từ `immutable`.

---

# 5. `Send` và `Share` là property compiler-known

Không nên biến chúng thành trait bình thường.

```text
Copy
Drop
Send
Share
Sized
```

là **semantic properties**.

Còn:

```text
Drawable
Iterator
Serialize
```

là behavioral traits.

Điều này đã phù hợp với type-system model hiện tại.

---

# 6. Spawn

Tôi đề xuất semantics:

```axiom
let task = Thread.spawn(move worker(data))
```

`spawn`:

```text
1. tạo execution context
2. chuyển ownership captured values
3. kiểm tra Send
4. tạo TaskHandle
```

Closure environment về semantic:

```text
TaskEnv {
    data: OWNED
}
```

---

# 7. Không nên có implicit detached thread

Nếu:

```axiom
Thread.spawn(worker)
```

tạo thread nhưng programmer không giữ handle, rất dễ có lifecycle mơ hồ.

Tôi đề xuất:

```text
spawn → owned handle
detach → explicit
```

Ví dụ conceptually:

```axiom
let handle = Thread.spawn(worker)
...
handle.join()
```

Nếu thực sự muốn detached:

```axiom
handle.detach()
```

---

# 8. Vì sao?

Để tránh:

```text
main exits
 ↓
background thread?
 ↓
resource ownership?
 ↓
process termination?
```

Axiom không nên âm thầm quyết định.

Structured concurrency nên là default ở library layer.

---

# 9. Async không tạo thread

Ví dụ:

```axiom
async fn load() -> Result<Data, Error> {
    let a = await read_a()
    let b = await read_b()
    ...
}
```

Không có nghĩa:

```text
load()
 ↓
new OS thread
```

Nó là:

```text
state machine
```

---

# 10. Async lowering

Conceptual:

```text
async fn f() {
    A
    await B
    C
    await D
    E
}
```

thành:

```text
StateMachine {
    state: 0 | 1 | 2
    locals...
}
```

Ví dụ:

```text
STATE_0
  execute A
  start B
  suspend

STATE_1
  resume B
  execute C
  start D
  suspend

STATE_2
  resume D
  execute E
  return
```

Không cần heap nếu compiler có thể giữ state machine ở caller/stack.

---

# 11. Future

Tôi đề xuất semantic concept:

```text
Future<T>
```

nhưng **không nhất thiết là Core type**.

Core chỉ hiểu:

```text
async computation
suspension
resume
```

Stdlib định nghĩa Future/Task abstraction.

---

# 12. Await là semantic suspension point

```axiom
let x = await future
```

Compiler phải biết:

> Những local nào còn sống sau `await`?

Ví dụ:

```axiom
async fn f() {
    let a = expensive_data()
    await something()
    use(a)
}
```

`a` phải tồn tại qua suspension.

Compiler có thể đưa `a` vào state machine:

```text
FutureState {
    state
    a
}
```

---

# 13. Local variables không sống qua await nếu không cần

Ví dụ:

```axiom
async fn f() {
    {
        let temp = compute()
        use(temp)
    }

    await something()
}
```

`temp` chết trước `await`.

Compiler không cần đưa `temp` vào state machine.

Đây là một optimization rất quan trọng.

---

# 14. `mut_view` qua await

Tôi đề xuất **cấm trong v0.1 nếu chưa có chứng minh rất mạnh**:

```axiom
async fn f(x: mut_view<Data>) {
    await something()
    modify(x)
}
```

Nếu `x` giữ mutable capability xuyên suspension:

```text
x
 ↓
SUSPEND
 ↓
executor có thể chuyển task
 ↓
owner/context có thể thay đổi
```

rất khó đảm bảo an toàn.

Do đó:

> `mut_view` không được sống qua `await` trong safe async code v0.1.

---

# 15. `view<T>` qua await

Có thể cho phép **chỉ khi compiler chứng minh provenance vẫn hợp lệ**.

Ví dụ:

```axiom
async fn f(x: view<Data>) {
    await something()
    read(x)
}
```

Không tự động accept.

Compiler phải chứng minh:

```text
owner remains alive
storage identity remains valid
no relocation
no conflicting mutation
```

Nếu không chứng minh được:

```text
compile error
```

---

# 16. Nhưng có một cách đơn giản hơn

Programmer có thể copy dữ liệu cần thiết:

```axiom
let snapshot = copy_data(x)

await something()

use(snapshot)
```

Đây là trade-off rất hợp triết lý Axiom:

> Compiler cố chứng minh trường hợp zero-copy; nếu không chứng minh được, programmer có thể chủ động tạo owned value.

Không cần lifetime annotation.

---

# 17. Async task migration

Một task có thể:

```text
executor A
    ↓
SUSPEND
    ↓
executor B
    ↓
RESUME
```

Nếu cho phép migration:

```text
future state
```

phải `Send`.

Do đó:

```text
Send
```

được kiểm tra trên state sống qua suspension.

---

# 18. `spawn_local`

Nếu task không được migrate:

```axiom
spawn_local(task)
```

thì có thể relax `Send`.

Ví dụ:

```text
local task
    ↓
Executor thread X
    ↓
never migrates
```

Nhưng vẫn phải tuân thủ:

```text
ownership
alias
lifetime
```

---

# 19. Đây là khác biệt quan trọng

```text
spawn(task)
```

có thể yêu cầu:

```text
Send
```

còn:

```text
spawn_local(task)
```

không nhất thiết.

Nhưng:

```text
spawn_local
```

**không biến unsafe code thành safe**.

---

# 20. Cancellation

Tôi đề xuất:

> Cancellation trong Core không phải “kill execution”.

Không có:

```text
kill_thread()
kill_task()
```

trong safe model.

Thay vào đó:

```text
Cancellation requested
        ↓
task reaches cancellation point
        ↓
cleanup
        ↓
cancelled
```

---

# 21. Vì sao không kill task?

Một task có thể đang giữ:

```text
MutexGuard
File
GPU resource
network transaction
partial state
```

Nếu kill bất kỳ instruction nào:

```text
resource invariants
```

có thể vỡ.

Cooperative cancellation đơn giản và an toàn hơn.

---

# 22. Cancellation token

Stdlib có thể có:

```text
CancellationToken
```

Task kiểm tra:

```axiom
if token.cancelled() {
    return Err(Cancelled)
}
```

Hoặc async runtime có cancellation points.

Core chỉ cần hiểu cleanup/suspension semantics.

---

# 23. Mutex

Một mutex:

```text
Mutex<T>
```

không làm:

```text
T → Share
```

một cách trực tiếp.

Nó cung cấp:

```text
lock()
    ↓
MutexGuard<T>
```

Guard có:

```text
!Copy
Drop
```

Khi guard bị Drop:

```text
unlock
```

---

# 24. Guard và view

Conceptually:

```text
guard
 └── mut_view<T>
```

View không được sống lâu hơn guard.

Compiler provenance:

```text
view
 ↓
guard
 ↓
mutex
```

Nếu:

```axiom
let x = guard.view()
drop(guard)
use(x)
```

→ reject.

Đây là một ví dụ rất tốt cho capability analysis.

---

# 25. Read-write lock

Tương tự:

```text
RwLock<T>
```

có:

```text
read()  → ReadGuard<T>
write() → WriteGuard<T>
```

Nhiều `ReadGuard`:

```text
OK
```

`ReadGuard + WriteGuard`:

```text
CONFLICT
```

---

# 26. Atomics

Atomics không dùng mutex.

```axiom
counter.fetch_add(1, Relaxed)
```

Compiler lower trực tiếp xuống hardware nếu có.

Nếu architecture không hỗ trợ operation:

```text
compiler/runtime fallback
```

có thể dùng library implementation.

---

# 27. `volatile` khác atomic

Điều này cần giữ nguyên:

```text
volatile
```

dùng cho:

- MMIO
- hardware register
- memory mapped devices

Nó không đảm bảo:

```text
thread synchronization
```

Ngược lại:

```text
atomic
```

có memory ordering.

---

# 28. Memory ordering

Core semantic enum:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Có thể sau này thêm:

```text
Consume
```

nhưng tôi không đề xuất đưa `Consume` vào v0.1 vì semantics thực tế phức tạp và compiler support khó.

---

# 29. Data race

Safe Axiom:

```text
READ + READ
```

OK.

```text
READ + WRITE
```

không được nếu không có synchronization.

```text
WRITE + WRITE
```

không được nếu không có synchronization.

Nhưng:

```text
WRITE field A
WRITE field B
```

có thể chạy song song nếu compiler chứng minh:

```text
DISJOINT(A, B)
```

---

# 30. Ví dụ

```axiom
struct Image {
    pixels: Pixels
    metadata: Metadata
}
```

Task A:

```text
write image.pixels
```

Task B:

```text
write image.metadata
```

Nếu region analysis chứng minh:

```text
pixels ∩ metadata = ∅
```

→ safe.

Không cần lock toàn bộ `Image`.

Đây là một lợi thế lớn của Axiom so với các hệ thống quá coarse-grained.

---

# 31. Channel

Channel nên có ownership transfer semantics.

```axiom
tx.send(data)
```

semantic:

```text
data
 ↓ MOVE
channel
```

Receiver:

```axiom
let data = rx.receive()?
```

nhận ownership.

Không cần:

```text
clone
```

trừ khi programmer muốn.

---

# 32. Bounded channel

Nên có:

```text
Channel<T>
BoundedChannel<T>
```

với semantics:

```text
send
receive
close
```

Backpressure là library concern.

---

# 33. Shared state

Axiom không nên có một primitive:

```text
shared var x
```

với semantics mơ hồ.

Thay vào đó:

```text
Atomic<T>
Mutex<T>
RwLock<T>
Channel<T>
Arc<T>
```

làm rõ programmer đang chọn chiến lược nào.

---

# 34. `Arc<T>`

`Arc<T>`:

```text
shared ownership
```

nhưng:

```text
Arc<T> ≠ thread-safe mutable T
```

Ví dụ:

```text
Arc<Vec<T>>
```

cho shared immutable access có thể hợp lệ.

Nhưng:

```text
Arc<MutableData>
```

không tự động cho phép nhiều thread mutate.

---

# 35. `Arc<Mutex<T>>`

Đây mới là:

```text
shared ownership
+
synchronized mutation
```

Mặc dù Axiom không cần syntax đặc biệt.

Compiler biết:

```text
Arc
```

là ownership abstraction.

`Mutex` cung cấp synchronization capability.

---

# 36. Không implicit synchronization

Không được:

```text
x += 1
```

tự động biến thành atomic vì `x` được shared.

Nếu muốn atomic:

```axiom
x.fetch_add(1, Relaxed)
```

Explicit semantic boundary.

---

# 37. Scheduler

Executor có thể:

```text
single-thread
multi-thread
work-stealing
event-loop
embedded
custom
```

Core không quan tâm.

Async state machine chỉ cần:

```text
poll/resume
suspend
ready
pending
```

Conceptual model:

```text
Task
 ↓
poll
 ├── Ready(value)
 └── Pending(wakeup)
```

---

# 38. Không bắt buộc Future allocation

Một async task:

```text
async fn f()
```

không nhất thiết heap allocate.

Compiler có thể:

```text
caller owns state machine
```

nếu:

```text
non-escaping
```

Nếu task được đưa vào executor:

```text
executor may store it dynamically
```

đó là library choice.

---

# 39. Async state machine + ownership

Ví dụ:

```axiom
async fn f() {
    let file = File.open(...)?
    let data = await read(file)
    process(data)
}
```

`file` sống qua await.

Compiler tạo conceptual:

```text
FutureState {
    state
    file
}
```

`Drop` của future phải cleanup `file` nếu future bị cancelled/dropped.

Đây là lý do:

> **Async lowering phải diễn ra trước hoặc cùng ownership/drop elaboration cuối cùng.**

---

# 40. Pipeline cập nhật

Trước đây:

```text
HIR
 ↓
MIR
 ↓
ownership verification
 ↓
async lowering
```

Tôi đề xuất cụ thể hơn:

```text
AST
 ↓
HIR
 ↓
Typed HIR
 ↓
MIR
 ↓
Async/Closure lowering
 ↓
Ownership + Capability + Concurrency verification
 ↓
Drop elaboration
 ↓
Verified MIR
 ↓
Optimization
```

Nhưng cần giữ một nguyên tắc:

> Async lowering không được làm mất semantic provenance/ownership information.

---

# 41. Async state machine không phải “compiler magic black box”

Verified MIR nên vẫn có thể biểu diễn:

```text
SUSPEND
RESUME
```

và state ownership rõ ràng.

Sau verification:

```text
SUSPEND
```

mới được lower thành machine-level coroutine state.

---

# 42. Thread + async

Một chương trình có thể:

```text
Thread
 └── Executor
      ├── Task A
      ├── Task B
      └── Task C
```

hoặc:

```text
Thread A → Executor A
Thread B → Executor B
```

hoặc:

```text
single thread
 └── async tasks
```

Axiom semantics không ép architecture.

---

# 43. Structured concurrency

Tôi đề xuất library design ưu tiên:

```text
scope
 ├── task A
 ├── task B
 └── task C
```

scope kết thúc:

```text
wait/cancel children
cleanup
```

Detached task:

```text
explicit
```

Điều này giúp resource lifetime dễ chứng minh hơn.

---

# 44. Concurrency verifier

State của verifier nên mở rộng:

```text
VerifierState {
    locals
    ownership
    initialization
    regions
    active_views
    effects
    cleanup
    concurrency
    suspension
}
```

Concurrency state theo dõi:

```text
ExecutionContext
Transfer
SharedCapabilities
Synchronization
Suspension
```

---

# 45. Concurrency verification không cần một “borrow checker”

Đây là điểm tôi muốn giữ rất mạnh.

Không có:

```text
BorrowChecker
```

như một module semantic duy nhất.

Thay vào đó:

```text
Ownership
     +
Regions
     +
Capabilities
     +
Effects
     +
Send/Share
     +
Synchronization
     +
Suspension
```

→ tạo thành safety proof.

Đây chính là hướng phù hợp với Axiom.

---

# 46. Ví dụ hoàn chỉnh

```axiom
fn worker(data: Vec<i32>) {
    process(data)
}

fn main() {
    let data = load_data()

    let task = Thread.spawn(move worker(data))

    task.join()
}
```

Compiler reasoning:

```text
data
  OWNED
    ↓
MOVE
    ↓
worker environment
    ↓
Thread boundary
    ↓
requires Send
    ↓
PASS
```

Không có:

```text
GC
borrow annotation
lifetime annotation
manual free
```

---

# 47. Ví dụ bị reject

```axiom
fn main() {
    var data = Vec.new()

    let v = view(data)

    Thread.spawn(move || {
        use(v)
    })

    data.push(10)
}
```

Verifier thấy:

```text
v
 ↓
READ capability
 ↓
captured by spawned task
 ↓
escapes current context
```

Trong khi:

```text
data.push()
 ↓
MAY_RELOCATE
```

→ conflict.

Compiler reject.

Không cần programmer viết lifetime.

---

# 48. Ví dụ mutable conflict

```axiom
let a = mut_view(data)
let b = mut_view(data)
```

Nếu region overlap:

```text
WRITE + WRITE
```

→ reject.

Nhưng:

```axiom
let a = mut_view(data.left)
let b = mut_view(data.right)
```

nếu compiler chứng minh disjoint:

```text
WRITE(R1)
WRITE(R2)

R1 ∩ R2 = ∅
```

→ accept.

---

# 49. Invariants mới

Tôi đề xuất khóa:

### ACON-01
Safe code cannot create data races.

### ACON-02
`Send` permits ownership transfer across execution contexts.

### ACON-03
`Share` permits safe shared access under its type semantics.

### ACON-04
`Send != Share`.

### ACON-05
Thread creation does not imply async execution.

### ACON-06
Async does not imply thread creation.

### ACON-07
Async state surviving suspension remains valid.

### ACON-08
Safe `mut_view` cannot survive `await` in v0.1.

### ACON-09
View provenance cannot outlive its owner.

### ACON-10
Task migration requires appropriate `Send` properties.

### ACON-11
`spawn_local` may avoid migration-related `Send` requirements.

### ACON-12
Cancellation is cooperative.

### ACON-13
Safe code cannot arbitrarily kill an execution context.

### ACON-14
Atomic operations have explicit memory ordering.

### ACON-15
Volatile is not synchronization.

### ACON-16
Synchronization is explicit.

### ACON-17
Channels transfer ownership explicitly.

### ACON-18
Mutex/RwLock guards have deterministic release.

### ACON-19
Shared ownership does not imply mutable synchronization.

### ACON-20
Concurrency verification uses region/capability/effect information.

---

# 50. Một điểm quan trọng cần xem xét lại

Đến đây có một câu hỏi lớn hơn:

**Axiom có thực sự cần `async/await` trong Core syntax không?**

Có hai hướng.

### Hướng A — Core async

```axiom
async fn foo()
await x
```

Compiler hiểu trực tiếp.

Ưu điểm:

- tối ưu state machine tốt
- diagnostics tốt
- ownership qua suspension chính xác
- không cần macro

Nhược điểm:

- Core phức tạp hơn.

### Hướng B — async là library/compiler extension

Core chỉ có:

```text
suspend/resume
```

Stdlib cung cấp `async/await`.

Tôi nghiêng về **A**.

Lý do là `await` ảnh hưởng trực tiếp:

```text
ownership
Drop
lifetime
state layout
concurrency
```

Nếu cố đẩy nó hoàn toàn ra library, compiler sẽ mất rất nhiều thông tin quan trọng.

---

## Một nguyên tắc mới rất đáng đưa vào Axiom

Từ toàn bộ thiết kế hiện tại, tôi nghĩ có thể rút ra:

> **Axiom chỉ đưa vào Core những abstraction làm thay đổi cách compiler chứng minh chương trình an toàn hoặc cách compiler tạo machine code.**

Vì vậy:

```text
ownership      → Core
view           → Core
async/await    → Core
Send/Share     → Core semantic properties
atomic order   → Core semantic
Vec            → Library
Mutex          → Library
Executor       → Library
HTTP           → Platform/library
GUI            → Platform/library
```

Đây là một tiêu chí rất hữu ích để từ giờ trở đi **mỗi khi AI agent đề xuất thêm tính năng, nó phải tự quyết định Core hay Library dựa trên tiêu chí này**, thay vì cứ nhét tính năng vào ngôn ngữ.

Bước tiếp theo hợp lý nhất bây giờ là **AXIOM CONTROL FLOW + EXPRESSION SEMANTICS v0.1**: khóa chính xác `if/match/loop/return/break/continue`, evaluation order, assignment, short-circuit, `?`, `panic`, closure, `defer` có/không, và đặc biệt là **expression phải đồng thời mang TYPE + CATEGORY + OWNERSHIP + ACCESS + CONTROL**, để sau đó agent có thể dùng nó làm nền tảng viết parser → HIR → MIR mà không tự diễn giải khác nhau.