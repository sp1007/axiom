Tiếp tục từ đó, tôi sẽ **đóng thiết kế Task/Future/Scheduler của Axiom** theo hướng: cực nhỏ, không heap bắt buộc, không `Pin`, không runtime toàn cục bắt buộc, và vẫn đủ mạnh cho server/game/GUI/HPC.

# ASYNC-TASK-001 — Axiom Task/Future/Scheduler Model

## 1. Chốt 3 khái niệm

Axiom phải phân biệt tuyệt đối:

```text
Future
  = computation state

Task
  = scheduled execution of a Future

TaskHandle
  = user-visible capability to interact with a Task
```

Không gộp chúng thành một object.

```text
async fn foo()
      │
      ▼
   Future
      │
   spawn()
      ▼
    Task
      │
      ▼
 TaskHandle
```

### Future

Future chỉ mô tả:

> "Tôi đang thực hiện computation nào và state hiện tại là gì?"

Nó **không có scheduler**.

### Task

Task bổ sung:

- scheduler state
- cancellation state
- join state
- wake state

### TaskHandle

Chỉ là capability để:

- await kết quả
- cancel
- kiểm tra trạng thái
- join

Không sở hữu toàn bộ Task.

---

# 2. Future state machine

Ví dụ:

```axiom
async fn foo(x: i32) -> i32 {
    let a = read_a().await
    let b = read_b().await
    x + a + b
}
```

Compiler có thể biến thành conceptually:

```text
FooFuture {
    state: 0 | 1 | 2,
    x: i32,
    a: i32,
    b: i32
}
```

Nhưng **không phải tất cả local đều tồn tại**.

Ví dụ:

```axiom
async fn foo() {
    let a = expensive();

    await something();

    use(a);
}
```

`a` sống qua `await` → phải được lưu.

Ngược lại:

```axiom
async fn foo() {
    let a = expensive();

    print(a);

    await something();
}
```

`a` chết trước suspension → compiler không cần đưa `a` vào Future.

Do đó:

> **Future size = state actually live across suspension points**, sau optimization.

---

# 3. Future không cần `Pin`

Đây là điểm tôi muốn chốt khác với Rust.

Axiom không đưa `Pin<T>` vào Core.

Lý do:

Future state machine của Axiom **không được phép mặc định dựa vào địa chỉ vật lý của chính nó**.

Compiler biết:

```text
Future
 ├── state
 ├── locals
 └── child futures
```

và có thể:

```text
move Future
```

mà không phá semantics.

Nếu một abstraction thực sự yêu cầu stable address:

```text
StableStorage<T>
PinnedStorage<T>
```

thì đó là **storage contract**, không phải thuộc tính mặc định của async.

Điều này khớp:

```text
AMEM-21 Stable Address Is An Explicit Storage Contract
```

---

# 4. `poll` là compiler/runtime boundary

Về mặt semantic, Future có một operation tương đương:

```text
poll(context) -> Poll<T>
```

nhưng tôi **không muốn bắt programmer implement `poll()` thông thường**.

Compiler sinh state machine.

Conceptually:

```text
Poll<T> =
    Pending
    Ready(T)
```

Compiler-generated:

```text
switch self.state {

    State0:
        ...
        return Pending

    State1:
        ...
        return Pending

    State2:
        return Ready(result)
}
```

Runtime scheduler chỉ cần biết:

```text
Pending
Ready
```

và wake mechanism.

---

# 5. Waker

Không nên biến `Waker` thành một object lớn.

Khái niệm tối thiểu:

```text
Waker
 └── capability → scheduler/task
```

Có thể representation là:

```text
(pointer, function pointer)
```

hoặc:

```text
(task index, scheduler id)
```

hoặc thậm chí một integer handle.

API cấp cao:

```axiom
context.wake()
```

Compiler/runtime quyết định representation.

---

# 6. Task Control Block

Đây là phần quan trọng nhất.

Tôi đề xuất conceptual layout:

```text
TaskControlBlock
├── task state
├── scheduling state
├── join state
├── cancellation state
├── wake state
└── future storage
```

Nhưng **không nhất thiết tất cả nằm trong một struct vật lý**.

Compiler/runtime có thể tách:

```text
Hot Task Data
Cold Task Data
Future Data
```

Ví dụ:

```text
HOT:
    state
    queue linkage
    scheduler state

COLD:
    cancellation
    join waiters
    diagnostics
```

Để scheduler chỉ chạm cache line nhỏ.

---

# 7. Task state machine

Tôi đề xuất:

```text
CREATED
   ↓
READY
   ↓
RUNNING
   ├────→ READY
   │
   ├────→ WAITING
   │          ↓
   │        READY
   │
   └────→ COMPLETED
              ↓
           RECLAIMED
```

Cancellation:

```text
RUNNING → CANCEL_REQUESTED
WAITING → CANCEL_REQUESTED
READY   → CANCEL_REQUESTED
```

Không có:

```text
FORCE_KILL
```

Axiom cancellation là cooperative.

---

# 8. `spawn`

Surface:

```axiom
let task = spawn(worker(x))
```

Semantics:

1. tạo Future
2. chuyển ownership của Future state vào Task
3. Task trở thành scheduler-owned
4. trả `TaskHandle`

Điểm rất quan trọng:

```text
spawn()
```

**không có nghĩa là tạo OS thread.**

Scheduler có thể chạy:

```text
1 thread
10 tasks
```

hoặc:

```text
8 threads
1,000,000 tasks
```

---

# 9. `spawn_local`

```axiom
spawn_local(worker())
```

không yêu cầu:

```text
Send
```

vì scheduler đảm bảo task không migrate khỏi execution domain của nó.

Ví dụ:

```text
GUI thread
    │
    ├── Task A
    ├── Task B
    └── Task C
```

Các task này có thể sử dụng state local của GUI thread.

Nhưng:

```axiom
spawn(worker())
```

có khả năng migrate → yêu cầu:

```text
Send
```

---

# 10. Work stealing

Đây là scheduler mặc định tôi đề xuất cho multi-thread async runtime.

```text
CPU 0                CPU 1                CPU 2
┌────────┐           ┌────────┐           ┌────────┐
│ Queue  │           │ Queue  │           │ Queue  │
│ A B C  │           │ D E    │           │ F      │
└────────┘           └────────┘           └────────┘
```

CPU 0 hết task:

```text
CPU 0
   │
   └── steal → CPU 1
```

Nhưng đây là **library/runtime**, không phải language primitive.

Axiom Core chỉ cần semantic:

```text
spawn
spawn_local
await
join
cancel
```

Scheduler implementation có thể là:

```text
single-thread
FIFO
priority
work-stealing
event-loop
embedded
RTOS
custom
```

---

# 11. Structured concurrency

Tôi muốn Axiom ưu tiên:

```axiom
async fn main() {
    let a = spawn(job_a())
    let b = spawn(job_b())

    let x = a.await
    let y = b.await
}
```

Task có parent relationship:

```text
Parent
 ├── Task A
 └── Task B
```

Khi scope kết thúc, compiler/runtime có thể đảm bảo child task không bị bỏ quên nếu API dùng structured task scope.

Ví dụ API tương lai:

```axiom
scope {
    spawn(...)
    spawn(...)
}
```

Semantic:

```text
enter scope
    ↓
spawn children
    ↓
wait/cancel children
    ↓
leave scope
```

Detached task phải explicit:

```axiom
detach(spawn(job()))
```

Không nên có kiểu:

```text
spawn(job()) // âm thầm detached
```

vì dễ tạo task sống lâu hơn owner.

---

# 12. `JoinHandle`

`JoinHandle<T>` nên là owning handle đối với **quyền quan sát kết quả**, không phải ownership của execution state theo nghĩa memory.

Conceptually:

```text
JoinHandle<T>
├── TaskId
└── result capability
```

```axiom
let task = spawn(foo())

let result = task.await
```

Sau khi await:

```text
JoinHandle consumed
Task result consumed
```

Nếu muốn chỉ quan sát:

```axiom
task.is_finished()
```

---

# 13. Task result không cần heap allocation

Ví dụ:

```axiom
async fn foo() -> i32 {
    42
}
```

Kết quả:

```text
i32
```

Không nên:

```text
malloc(Result)
```

Runtime có thể đặt result:

```text
TaskControlBlock
├── state
├── future
└── result: i32
```

hoặc caller-provided storage:

```text
caller
  ↓
result slot
```

hoặc register nếu task được inline/eliminate.

---

# 14. Task Pool

Để đạt mật độ task cao, runtime nên có:

```text
TaskPool<T>
```

conceptually:

```text
Pool
┌─────┬─────┬─────┬─────┬─────┐
│  0  │  1  │  2  │  3  │  4  │
└─────┴─────┴─────┴─────┴─────┘
```

Một task:

```text
TaskId = index + generation
```

Ví dụ:

```text
42:7
```

Trong đó:

```text
42 = slot
7  = generation
```

Task cũ:

```text
42:6
```

không thể nhầm với task mới:

```text
42:7
```

Điều này tái sử dụng nguyên tắc:

```text
AMEM-39 Generation Handles Can Prevent Stale Logical References
```

---

# 15. Nhưng đừng bắt mọi runtime phải dùng Pool

Đây là điểm quan trọng.

Axiom không quy định:

```text
Task = Pool allocation
```

Chỉ quy định semantic lifetime.

Có thể có:

### Embedded

```text
static TaskPool<64>
```

### Server

```text
dynamic work-stealing allocator
```

### Game engine

```text
frame/task arena
```

### OS/runtime

```text
heap task allocation
```

### Freestanding

```text
caller-provided task storage
```

---

# 16. Caller-provided task storage

Đây là một tính năng rất đáng có cho systems programming.

Conceptually:

```axiom
let storage = TaskStorage<1024>()

spawn_in(storage, worker())
```

Compiler/runtime không cần heap.

Ví dụ embedded:

```text
static memory
    ↓
Task storage
    ↓
Tasks
```

Điều này cực kỳ hữu ích cho:

- embedded
- kernel
- game
- real-time
- networking
- WASM
- GPU-adjacent systems

---

# 17. Cancellation

Không có:

```text
kill_thread()
```

đối với async task.

Có:

```axiom
task.cancel()
```

nhưng semantic là:

```text
cancel request
     ↓
future observes cancellation
     ↓
cleanup
     ↓
completed/cancelled
```

Không được tự ý phá stack/state của task đang chạy.

---

# 18. Cancellation không làm Drop async

Chúng ta đã chốt:

> Không có `AsyncDrop`.

Điều đó vẫn giữ.

Nếu:

```axiom
async fn foo() {
    let socket = ...
    await ...
}
```

cancel task:

```text
cancel request
      ↓
future exits
      ↓
normal Drop
```

Nếu resource cần asynchronous cleanup:

```axiom
await resource.close()
```

phải làm explicit trước khi kết thúc.

---

# 19. Task và view

Đây là nơi memory model của Axiom phát huy tác dụng.

Không cho:

```axiom
async fn foo(v: view<Data>) {
    await something()
    use(v)
}
```

nếu `v` phụ thuộc vào storage có thể kết thúc/di chuyển trước đó.

Quy tắc:

```text
view/mut_view
      +
await
      =
không được vượt qua suspension
```

trừ khi compiler chứng minh storage/provenance vẫn hợp lệ theo một storage contract phù hợp.

Đây là invariant đã có:

```text
AASYNC-29 / AASYNC-30
```

và nên giữ nguyên.

---

# 20. Future có thể chứa owned value qua await

Ví dụ:

```axiom
async fn foo() {
    let buffer = Buffer.alloc(4096)

    await socket.read()

    process(buffer)
}
```

`buffer` là owned value.

Compiler có thể biến:

```text
Future
┌──────────────────┐
│ state             │
│ buffer            │
└──────────────────┘
```

Không cần borrow checker syntax.

Đây chính là lợi thế của Axiom:

> Programmer không viết lifetime, nhưng compiler vẫn biết lifetime.

---

# 21. Kích thước task thực tế

Thay vì cố định 32 bytes, tôi đề xuất architecture mục tiêu:

```text
Minimum async task overhead:
    scheduler metadata
  + future live state
  + synchronization state only when required
```

Một future cực nhỏ:

```text
async fn ping() {
    await event()
}
```

có thể có:

```text
future state ≈ 1–few bytes
```

Task metadata có thể khoảng vài machine words.

Future phức tạp:

```text
async fn huge() {
    let a = ...
    let b = ...
    let c = ...
    await ...
}
```

thì task lớn hơn là **đúng**, vì state thực sự phải tồn tại.

Không nên gian lận bằng cách nói mọi task đều 32 bytes.

---

# 22. Small Task Optimization

Runtime có thể có:

```text
SmallFuture
LargeFuture
```

Ví dụ:

```text
             Future
               │
       ┌───────┴───────┐
       ↓               ↓
   Inline storage   External storage
```

Nếu Future ≤ threshold:

```text
Task
┌──────────────────────┐
│ control              │
│ future inline        │
└──────────────────────┘
```

Nếu lớn:

```text
Task
┌──────────────┐
│ control      │
│ future ptr ──┼──────→ large future
└──────────────┘
```

Nhưng đây là runtime optimization, không phải semantic requirement.

---

# 23. Stackful coroutine không phải Core

Axiom async mặc định:

```text
stackless coroutine
```

tức:

```text
Future state machine
```

Không tạo stack riêng.

Nếu ứng dụng cần fiber:

```axiom
Fiber.spawn(...)
```

thì đó là library/system abstraction:

```text
Fiber
 └── dedicated stack
```

Như vậy:

```text
async task ≠ fiber ≠ thread
```

rất rõ ràng.

---

# 24. Runtime profile

Axiom nên hỗ trợ ít nhất:

```text
Profile
├── freestanding
├── single_thread
├── threaded
├── async
└── custom
```

Một chương trình:

```axiom
fn main() {
    println("hello")
}
```

không được tự động kéo vào:

```text
scheduler
thread runtime
async runtime
```

Một chương trình:

```axiom
async fn main() { ... }
```

mới yêu cầu async executor.

---

# 25. Core không sở hữu scheduler

Kiến trúc:

```text
Axiom Core
    │
    ├── Future semantic model
    ├── async lowering
    ├── await
    └── Send/Share
          │
          ▼
Axiom Std
    │
    ├── Task
    ├── JoinHandle
    ├── Executor
    ├── Waker
    ├── Thread
    └── Channels
          │
          ▼
Platform
    ├── Windows
    ├── Linux
    ├── macOS
    ├── Android
    └── iOS
```

Điều này cực kỳ quan trọng để giữ mục tiêu:

> **No mandatory runtime.**

---

# 26. Bộ invariant mới

Tôi đề xuất bổ sung chính thức:

```text
AASYNC-51
Suspension Does Not Imply Allocation

AASYNC-52
Future Size Is Determined By Live State

AASYNC-53
Task Storage Is Runtime-Selectable

AASYNC-54
Non-Escaping Futures May Be Stack/Register Resident

AASYNC-55
Spawn Requires Persistent State

AASYNC-56
Async Task Does Not Imply OS Thread

AASYNC-57
Future Does Not Imply Scheduler Ownership

AASYNC-58
Task Handle Does Not Own Physical Task Storage

AASYNC-59
Task Cancellation Is Cooperative

AASYNC-60
Forced Destruction Cannot Invalidate Running Task State

AASYNC-61
Task Migration Requires Appropriate Send Capability

AASYNC-62
Local Task Execution Does Not Require Send

AASYNC-63
Structured Task Scope Must Resolve Child Lifetime

AASYNC-64
Detached Execution Must Be Explicit

AASYNC-65
Async State Must Not Contain Unproven Escaping Capabilities

AASYNC-66
Future Movement Must Preserve Semantics

AASYNC-67
Stable Address Is Not Implicitly Required By Future

AASYNC-68
Async Runtime Is Optional

AASYNC-69
Scheduler Policy Is Not Language Semantics

AASYNC-70
Task Allocation Is Not Language Semantics
```

---

# 27. Kiến trúc cuối cùng

Toàn bộ mô hình lúc này:

```text
                         Axiom Program
                              │
                         async fn
                              │
                              ▼
                       Future State Machine
                              │
                    ┌─────────┴─────────┐
                    │                   │
              await locally        spawn(...)
                    │                   │
                    │                   ▼
                    │                 Task
                    │                   │
                    │          ┌────────┼────────┐
                    │          │        │        │
                    │        Future   Control   Handle
                    │          │
                    │          ▼
                    │      Scheduler
                    │          │
                    │    ┌─────┼─────┐
                    │    ↓     ↓     ↓
                    │   CPU0  CPU1  CPU2
                    │
                    ▼
                 executor
```

Và storage:

```text
Future
  ↓
compiler chooses

register
stack
inline task
task pool
arena
heap
caller storage
```

**không có lựa chọn nào là bắt buộc.**

---

## Một điều tôi muốn chốt rất mạnh

Axiom không nên cố thắng Rust bằng câu:

> "Task của chúng tôi 32 bytes."

Mà nên thắng bằng kiến trúc:

> **Async computation has no inherent heap, thread, stack, scheduler, or fixed-size representation. The compiler preserves only the state that must survive suspension, while the runtime chooses how persistent tasks are stored and scheduled.**

Đó là nền tảng tốt hơn rất nhiều cho mục tiêu **high-performance + low-level control + programmer simplicity** của Axiom.

### Task kiến trúc tiếp theo

Sau `ASYNC-TASK-001`, mảnh còn thiếu trực tiếp là **THREAD-001 — OS Thread Model**: ta sẽ thiết kế `Thread`, thread stack, TLS, thread-local allocator, thread creation/join, affinity, priority, `spawn` vs `spawn_local`, và đặc biệt **cách Axiom tránh việc mỗi OS thread phải mang một runtime/context khổng lồ**.