Tiếp tục với **SCHEDULER-001 — Unified Scheduler Model**. Đây là điểm chúng ta gom `Thread + Fiber + Task + Future + Send/Share` thành một mô hình thực thi thống nhất.

# SCHEDULER-001

## 1. Nguyên tắc quan trọng nhất

Scheduler **không quản lý mọi thứ**.

Nó chỉ trả lời 3 câu hỏi:

```text
1. Cái gì đang READY?
2. Execution unit nào có thể chạy nó?
3. Khi nào cần đánh thức/chuyển nó?
```

Không để scheduler trở thành một "runtime object khổng lồ".

Kiến trúc:

```text
                     Scheduler
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
       Executor 0     Executor 1     Executor 2
          │              │              │
        Thread         Thread         Thread
          │              │              │
      ┌───┴───┐          │          ┌───┴───┐
      ↓       ↓          ↓          ↓       ↓
    Task    Task       Task        Fiber   Task
      │       │          │
    Future  Future     Future
```

---

# 2. `Executor` mới là đơn vị chạy

Tôi đề xuất thêm một khái niệm:

```text
ExecutionContext
```

thay vì để `Scheduler` trực tiếp chứa thread.

Conceptually:

```text
Scheduler
    ↓
ExecutionContext
    ↓
Thread / Fiber
    ↓
computation
```

Một `ExecutionContext` có:

```text
ExecutionContext
├── local ready queue
├── current task
├── local scheduler state
└── execution resource
```

Execution resource có thể là:

```text
OS Thread
Fiber
embedded execution loop
```

---

# 3. Scheduler toàn cục không nên có một queue duy nhất

Không nên:

```text
              GLOBAL QUEUE
          ┌─────────────────┐
          │ A B C D E F ... │
          └─────────────────┘
             ↙  ↓  ↘
           CPU0 CPU1 CPU2
```

vì mọi worker sẽ tranh chấp một queue.

Axiom nên dùng:

```text
CPU 0                  CPU 1                  CPU 2
┌─────────┐            ┌─────────┐            ┌─────────┐
│ local Q │            │ local Q │            │ local Q │
│ A B C   │            │ D E     │            │ F G     │
└─────────┘            └─────────┘            └─────────┘
      ↕                      ↕                      ↕
      └──────────── work stealing ──────────────────┘
```

---

# 4. Local queue là fast path

Khi:

```axiom
spawn(foo())
```

được gọi trên worker 2:

```text
Worker 2
   │
   └── enqueue local
          ↓
      Queue 2
```

Không cần global lock.

Worker tiếp tục lấy task từ local queue.

Đây là fast path quan trọng nhất.

---

# 5. Work stealing

Khi Worker 2 hết việc:

```text
Worker 2
   │
   ├── local queue empty
   │
   └── steal
          ↓
       Worker 0
```

Worker 2 lấy một batch/task từ Worker 0.

Điều này giúp:

- tận dụng CPU
- giảm global contention
- giữ locality
- scheduler scale theo số core.

---

# 6. Nhưng không phải mọi task đều steal được

Đây là nơi `Send` trở thành scheduler capability.

Ta có:

```text
Task
├── Local
└── Sendable
```

### Local task

```text
spawn_local(...)
```

chỉ chạy trên execution domain ban đầu.

### Sendable task

```text
spawn(...)
```

có thể migrate.

Scheduler:

```text
Local queue
    ↓
chỉ owner worker

Sendable queue
    ↓
có thể steal
```

Do đó scheduler không cần runtime check kiểu:

```text
if task.is_send ...
```

trong safe execution path nếu compiler/runtime metadata đã phân loại task.

---

# 7. `Share` không có nghĩa là task migratable

Điểm này cần giữ rất rõ:

```text
Send  = ownership migration
Share = concurrent access
```

Một object có thể:

```text
Share = yes
Send  = no
```

hoặc:

```text
Send = yes
Share = no
```

Ví dụ:

```text
Mutex<T>
```

có thể được chia sẻ giữa threads, nhưng bản thân một lock guard có thể không được gửi sang thread khác.

---

# 8. Scheduler không kiểm tra ownership

Đây là một quyết định quan trọng.

Không làm:

```text
Scheduler → ownership verifier
```

Compiler đã làm việc đó:

```text
Source
 ↓
Ownership
 ↓
Capability
 ↓
Send/Share verification
 ↓
Verified MIR
 ↓
Scheduler metadata
```

Scheduler chỉ nhận:

```text
VerifiedTask
```

Do đó runtime nhẹ hơn.

---

# 9. Task metadata

Conceptually:

```text
TaskHeader
├── state
├── flags
├── scheduler_link
├── generation/id
└── future pointer/storage
```

Không nên chứa:

```text
Mutex
allocator
large Result
stack
debug information
```

trừ khi task thực sự cần.

---

# 10. Task state

Tôi đề xuất bit-packed state:

```text
TaskState
    READY
    RUNNING
    WAITING
    COMPLETED
    CANCEL_REQUESTED
```

Không cần enum object.

Có thể là:

```text
u32 state_flags
```

và compiler/runtime tối ưu atomic state transition.

Ví dụ:

```text
READY | SENDABLE
```

hoặc:

```text
WAITING | HAS_RESULT
```

---

# 11. Scheduler queue phải intrusive

Thay vì:

```text
Queue<Node<Task*>>
```

có allocation cho Node:

```text
Task
 └── next
```

Task tự chứa queue linkage.

Ví dụ:

```text
Task
├── header
├── future
└── queue_next
```

Khi đưa vào queue:

```text
Task → next → Task → next → ...
```

Không cần allocation cho queue node.

Đây là một điểm rất hợp với mục tiêu Axiom.

---

# 12. Nhưng một Task không nên có quá nhiều queue pointers

Một task có thể cần:

```text
ready queue
wait queue
timer queue
join waiters
```

Nếu nhét tất cả:

```text
Task = 100+ bytes
```

thì mất lợi thế.

Giải pháp:

### Unioned scheduler linkage

Một task chỉ ở **một scheduler queue tại một thời điểm**:

```text
SchedulerLink
```

được reuse.

Ví dụ:

```text
Task
├── SchedulerLink
├── Future
└── Control
```

Khi WAITING:

```text
SchedulerLink → IO wait queue
```

Khi READY:

```text
SchedulerLink → ready queue
```

---

# 13. Timer không cần Timer Object cho mỗi task

Không nên:

```text
sleep(10ms)
 ↓
malloc(Timer)
```

Có thể dùng:

```text
TimerWheel
```

hoặc:

```text
min-heap
```

hoặc:

```text
calendar queue
```

Task chỉ giữ:

```text
wake_at
```

nếu cần.

---

# 14. Timer Wheel

Đối với server/networking, tôi thiên về:

```text
TimerWheel
```

Conceptually:

```text
slot 0 ─ tasks
slot 1 ─ tasks
slot 2 ─ tasks
...
slot N ─ tasks
```

`await sleep(10ms)`:

```text
Task
 ↓
timer wheel slot
 ↓
WAITING
```

Đến deadline:

```text
Timer
 ↓
READY
```

Không cần mỗi timer một heap allocation.

---

# 15. I/O readiness

Scheduler cũng không nên block toàn bộ worker.

Ví dụ:

```axiom
let data = await socket.read()
```

Pipeline:

```text
Future
 ↓
socket.read()
 ↓
OS async I/O registration
 ↓
Future = WAITING
 ↓
worker chạy Task khác
```

Khi OS báo ready:

```text
I/O event
 ↓
wake task
 ↓
READY queue
```

Platform backends:

```text
Windows → IOCP
Linux   → epoll/io_uring
Apple   → kqueue / appropriate APIs
Android → platform-specific mechanisms
```

Đây là std/platform runtime, không phải Core.

---

# 16. Waker

Task khi WAITING phải để lại một capability:

```text
WaitRegistration
```

conceptually:

```text
I/O subsystem
    │
    └── registration → Task
```

Khi event xảy ra:

```text
wake(Task)
```

`wake()` phải idempotent.

Nếu:

```text
wake()
wake()
wake()
```

thì không tạo:

```text
READY
READY
READY
```

ba lần.

Chỉ cần:

```text
WAITING → READY
```

một lần.

---

# 17. Lost wakeup

Đây là bug scheduler nghiêm trọng nhất.

Không được xảy ra:

```text
Task:
    kiểm tra event → chưa ready

I/O:
    event xảy ra
    wake()

Task:
    đăng ký wait

=> Task ngủ vĩnh viễn
```

Do đó transition:

```text
CHECK → REGISTER → COMMIT WAIT
```

phải atomic theo abstraction của event source.

Đây là trách nhiệm runtime primitive, không phải programmer.

---

# 18. `await` semantic

Compiler hạ:

```axiom
let x = foo().await
```

thành concept:

```text
poll foo

if Pending:
    save state
    register waker
    return control

if Ready:
    continue
```

Không cần scheduler lock trong compiler-generated Future.

---

# 19. Scheduler run loop

Conceptually:

```text
while scheduler.running:

    task = local_queue.pop()

    if task == none:
        task = steal()

    if task == none:
        task = wait_for_event()

    run(task)

    switch result:
        READY:
            enqueue(task)

        WAITING:
            register_wait(task)

        COMPLETE:
            finalize(task)
```

Đây là toàn bộ scheduler essence.

---

# 20. Scheduler không cần GC

Task lifecycle:

```text
CREATED
 ↓
READY
 ↓
RUNNING
 ↓
WAITING
 ↓
READY
 ↓
RUNNING
 ↓
COMPLETED
 ↓
RECLAIM
```

Reclaim dựa trên ownership:

```text
Scheduler owns task
```

Khi task complete:

```text
scheduler ownership
      ↓
drop task state
      ↓
return storage
```

Không cần tracing GC.

---

# 21. Task storage ownership

Tôi đề xuất:

```text
Scheduler
    owns Task
```

trong execution phase.

`JoinHandle` chỉ là capability.

```text
Scheduler ─────owns────→ Task
                         ↑
                         │ observe
                    JoinHandle
```

Điều này giải quyết rất nhiều lifetime complexity.

---

# 22. JoinHandle drop

Nếu:

```axiom
let h = spawn(foo())
```

rồi:

```text
drop(h)
```

thì task **không tự động bị kill**.

Task vẫn chạy nếu scheduler sở hữu nó.

Nếu muốn cancellation:

```axiom
h.cancel()
```

Nếu muốn detached:

```axiom
detach(h)
```

Như vậy semantics rõ.

---

# 23. Join waiter

Nếu nhiều người có quyền await task:

```text
Task
 ├── Join waiter A
 ├── Join waiter B
 └── ...
```

nhưng thông thường ta không cần cho phép nhiều consuming join handles.

Tôi đề xuất:

### `JoinHandle<T>`

một consuming result capability.

### `TaskRef<T>`

non-consuming observation:

```axiom
task.is_finished()
```

### `SharedTask<T>`

nếu cần nhiều consumer.

Đừng làm mọi Task mặc định multi-join vì sẽ làm control state phức tạp.

---

# 24. Scheduler shutdown

Không được:

```text
process exit
 ↓
free scheduler
 ↓
tasks still running
```

Scheduler phải có lifecycle:

```text
RUNNING
 ↓
SHUTDOWN_REQUESTED
 ↓
STOP_ACCEPTING
 ↓
DRAIN/CANCEL
 ↓
JOIN_WORKERS
 ↓
DESTROY
```

Có profile:

```text
graceful
cancel
abort
```

---

# 25. Structured concurrency

Scheduler hỗ trợ:

```axiom
scope {
    spawn(a())
    spawn(b())
}
```

Scope owns child task handles:

```text
Scope
 ├── child A
 └── child B
```

Khi scope kết thúc:

```text
wait A
wait B
```

hoặc cancellation nếu parent failed.

Điều này nên là std abstraction, nhưng compiler có thể cung cấp tối ưu hóa cho scope.

---

# 26. Priority

Không nên chỉ có một FIFO.

Task có thể có:

```text
Priority
```

nhưng priority scheduling không nên mặc định gây starvation.

Scheduler policy:

```text
interactive
normal
background
real_time
```

là runtime policy.

Core không biết chúng.

---

# 27. NUMA

Sau này server lớn có thể:

```text
NUMA node 0
 ├── worker 0
 └── worker 1

NUMA node 1
 ├── worker 2
 └── worker 3
```

Scheduler có thể ưu tiên:

```text
local task
↓
same NUMA node
↓
remote steal
```

Nhưng semantics không thay đổi.

Đây chính là lợi thế khi scheduler policy không bị đóng cứng vào language.

---

# 28. CPU affinity + scheduler affinity

Phân biệt:

```text
Thread affinity
```

với:

```text
Task affinity
```

Task có thể yêu cầu:

```text
same worker
same NUMA node
specific execution domain
```

Ví dụ GUI:

```text
UI task → UI thread
```

GPU:

```text
GPU submission task → GPU execution domain
```

Không cần biến tất cả thành `Send`.

---

# 29. Execution Domain

Tôi đề xuất khái niệm đã xuất hiện trong GPU model:

```text
ExecutionDomain
```

Các loại:

```text
CPU
CPUThread
CPUWorker
Fiber
GPU
Device
External
```

Scheduler chỉ chạy computation trên domain mà nó hợp lệ.

Ví dụ:

```text
UI state
ExecutionDomain = MainThread
```

thì không được steal sang worker.

---

# 30. Điều này kết nối GPU rất đẹp

Sau này:

```text
spawn_cpu(...)
spawn_gpu(...)
```

không nhất thiết là hai language primitives.

Chúng có thể là:

```text
ExecutionDomain
```

Ví dụ:

```text
submit(kernel)
```

trả:

```text
GpuEvent
```

Scheduler event model có thể dùng chung abstraction:

```text
CPU task
GPU completion
I/O completion
timer
```

đều có thể:

```text
wake(task)
```

Đây là một kiến trúc rất mạnh.

---

# 31. Scheduler event model thống nhất

Thay vì mỗi subsystem có cơ chế riêng:

```text
timer → special callback
IO → special callback
GPU → special callback
channel → special callback
```

ta có:

```text
External Event
      ↓
Wake Capability
      ↓
Task READY
```

Các nguồn:

```text
Timer
I/O
GPU
Channel
Mutex
Condition
User event
```

đều hội tụ về:

```text
wake(task)
```

---

# 32. Nhưng không biến mọi thứ thành callback

Future vẫn giữ state machine:

```text
event
 ↓
wake
 ↓
poll Future
```

không:

```text
event
 ↓
callback chain
```

Điều này giúp code vẫn tuyến tính:

```axiom
let data = socket.read().await
let result = process(data).await
```

thay vì callback hell.

---

# 33. Scheduler fast path

Mục tiêu:

```text
spawn local task
```

nên gần:

```text
create/inherit task state
↓
push local queue
```

không:

```text
mutex
malloc
syscall
global scheduler lock
```

Nếu task storage đã có sẵn từ pool/arena, fast path cực nhỏ.

---

# 34. Scheduler slow path

Chỉ khi cần:

```text
local queue empty
cross-worker wake
OS I/O
timer
new worker
task allocation
```

mới đi vào slow path.

Đây là pattern:

```text
HOT PATH
    ↓
lock-free / local / cache-friendly

COLD PATH
    ↓
OS/runtime complexity
```

---

# 35. Memory ordering

Scheduler là nơi dùng atomics nhiều.

Không nên đưa scheduler-specific memory ordering vào programmer API.

Runtime tự dùng:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

tùy queue/stealing algorithm.

Compiler đã có atomic model:

```text
AATOM-20..40
```

nên scheduler chỉ là consumer của semantics đó.

---

# 36. Queue implementation

MVP:

```text
LocalQueue
    owner → push/pop
    thieves → steal
```

Có thể dùng Chase-Lev style deque sau khi chứng minh correctness.

Nhưng specification không nên đóng đinh algorithm.

Chỉ định:

```text
SchedulerQueue {
    push_local
    pop_local
    steal
}
```

Implementation:

```text
lock-free deque
mutex queue
ring buffer
custom
```

đều được.

---

# 37. Determinism

Scheduler concurrency vốn không deterministic về execution order.

Nhưng Axiom compiler/build/test phải deterministic.

Do đó:

```text
compiler deterministic
≠
program scheduling deterministic
```

Test harness có thể có:

```text
DeterministicExecutor
```

để kiểm thử concurrency.

Ví dụ:

```text
virtual scheduler
virtual time
controlled wake ordering
```

Đây là công cụ cực kỳ quan trọng.

---

# 38. DeterministicExecutor

Cho test:

```axiom
let exec = TestExecutor()

exec.spawn(a())
exec.spawn(b())

exec.step()
exec.step()
```

Có thể tái hiện race.

Runtime production:

```text
WorkStealingExecutor
```

Test:

```text
DeterministicExecutor
```

cùng semantic Future.

Đây là lợi thế lớn cho compiler/harness.

---

# 39. Scheduler không được ảnh hưởng semantics

Hai scheduler:

```text
FIFO
```

và:

```text
WorkStealing
```

phải cho cùng observable result với chương trình hợp lệ.

Khác biệt chỉ được nằm ở:

```text
timing
ordering của concurrent events
```

trong phạm vi chương trình đã cho phép.

Nếu chương trình phụ thuộc vào race/data race:

```text
safe Axiom code
```

phải không cho phép race đó.

---

# 40. Invariants mới

Tôi đề xuất chốt:

```text
ASCHED-20
Scheduler Does Not Own Semantic Type Checking

ASCHED-21
Scheduler Operates On Verified Execution Units

ASCHED-22
Local Scheduling Is The Default Fast Path

ASCHED-23
Global Scheduler Lock Is Not Required By Language Semantics

ASCHED-24
Work Stealing Is An Implementation Strategy

ASCHED-25
Only Sendable Tasks May Migrate

ASCHED-26
Local Tasks Are Execution-Domain Affine

ASCHED-27
Task Queue Membership Requires Exclusive Scheduler Ownership

ASCHED-28
Scheduler Queue Nodes Need Not Be Separately Allocated

ASCHED-29
Wake Is Idempotent

ASCHED-30
Waiting State Must Not Lose Wake Events

ASCHED-31
Task Completion Releases Scheduler Ownership

ASCHED-32
JoinHandle Does Not Imply Task Ownership

ASCHED-33
Detached Execution Must Be Explicit

ASCHED-34
Cancellation Is Cooperative

ASCHED-35
Scheduler Does Not Require Garbage Collection

ASCHED-36
Scheduler Does Not Require A Global Runtime Lock

ASCHED-37
Scheduler Policy Is Not Language Semantics

ASCHED-38
Timer Events And I/O Events May Share Wake Semantics

ASCHED-39
External Completion Events May Wake Tasks

ASCHED-40
Scheduler May Use Platform-Specific I/O Engines

ASCHED-41
Scheduler May Be Single-Threaded

ASCHED-42
Scheduler May Be Multi-Threaded

ASCHED-43
Scheduler May Be Work-Stealing

ASCHED-44
Scheduler May Be Embedded Or User-Provided

ASCHED-45
Task Storage Is Independent Of Scheduling Policy

ASCHED-46
Scheduler Shutdown Must Resolve Worker Lifetime

ASCHED-47
Safe Scheduler Execution Preserves Ownership Guarantees

ASCHED-48
Scheduler Does Not Define Memory Allocation Semantics

ASCHED-49
Execution Domain Is Distinct From Storage Domain

ASCHED-50
Scheduler Does Not Implicitly Create OS Threads
```

---

# 41. Kiến trúc concurrency của Axiom lúc này

Ta đã có một mô hình rất sạch:

```text
                         PROGRAM
                            │
                      async / spawn
                            │
                            ▼
                         Future
                            │
                            ▼
                          Task
                            │
                     ┌──────┴──────┐
                     │             │
                  Sendable       Local
                     │             │
                     ▼             ▼
               Work stealing    Affine
                     │             │
                     └──────┬──────┘
                            ▼
                       Scheduler
                            │
              ┌─────────────┼─────────────┐
              ↓             ↓             ↓
           Thread        Fiber        Execution Domain
              │             │             │
              └─────────────┴─────────────┘
                            │
                         Machine
```

Và memory:

```text
Task
 ├── tiny control state
 ├── Future live state
 └── scheduler linkage

Thread
 ├── OS context
 ├── configurable stack
 └── TLS

Fiber
 ├── machine context
 └── explicit stack
```

**Không có GC. Không có `Pin`. Không có global runtime bắt buộc. Không có một scheduler lock bắt buộc. Không có task heap allocation bắt buộc.**

---

## Bước tiếp theo: CHANNEL-001

Mảnh tiếp theo nên là **Channel/Message Passing Model**, bởi vì channel là thứ nối trực tiếp:

```text
Send
Share
Task
Thread
Scheduler
Cancellation
Backpressure
```

Đặc biệt cần quyết định một vấn đề rất quan trọng cho Axiom:

> Khi `send(channel, value)` chuyển ownership của `value`, làm thế nào để channel có **zero-copy / bounded / lock-free fast path** mà vẫn giữ nguyên ownership verifier?

Đây cũng là chỗ chúng ta sẽ quyết định liệu Axiom có cần một primitive kiểu `Arc` trong Core hay hoàn toàn giữ shared ownership ở library.