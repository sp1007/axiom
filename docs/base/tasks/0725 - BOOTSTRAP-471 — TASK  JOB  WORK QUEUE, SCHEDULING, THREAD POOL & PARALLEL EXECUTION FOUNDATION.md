# BOOTSTRAP-471 — TASK / JOB / WORK QUEUE, SCHEDULING, THREAD POOL & PARALLEL EXECUTION FOUNDATION

**Trạng thái: COMPLETED / LOCKED**

471 xây dựng lớp thực thi song song phía trên concurrency primitive của 424, nhưng không thay đổi semantics của thread/async.

Kiến trúc:

```text
Application
    │
    ├── Task
    ├── Job
    ├── Parallel Loop
    └── Task Group
          │
          ↓
      Scheduler
          │
     ┌────┴────┐
     ↓         ↓
 Work Queue   Executor
     │         │
     └────┬────┘
          ↓
       Workers
          ↓
      OS Threads
```

Nguyên tắc:

```text
Thread = execution resource
Task   = logical unit of work
Job    = schedulable work item
Future = eventual result
```

và:

```text
Task ≠ Thread
Async ≠ ThreadPool
Parallelism ≠ Implicit Parallelism
```

---

## 471.1 — Task

Task là đơn vị công việc logic có thể được scheduler thực thi.

Task không sở hữu OS thread.

---

## 471.2 — Job

Job là work item có thể enqueue:

```text
Job {
    execute
    priority
    cancellation
    metadata
}
```

---

## 471.3 — Future

Future biểu diễn kết quả chưa hoàn thành:

```text
Future<T>
```

States:

```text
Pending
Ready(T)
Failed(E)
Cancelled
```

---

## 471.4 — Task ownership

Task phải có owner/context rõ ràng.

Không tạo detached task ngầm.

---

## 471.5 — Task group

TaskGroup quản lý một tập task liên quan.

```text
group.spawn(...)
group.wait()
```

---

## 471.6 — Structured concurrency

Task group mặc định có structured lifetime:

```text
create group
    ↓
spawn children
    ↓
wait/cancel
    ↓
destroy group
```

Detached execution phải explicit.

---

# 471.7 — Scheduler

Scheduler quyết định job nào được thực thi và worker nào thực thi nó.

Scheduler là library/runtime component, không phải language primitive bắt buộc.

---

## 471.8 — Scheduler interface

Concept:

```text
submit(job)
cancel(job)
shutdown()
```

---

## 471.9 — Worker

Worker là execution context thường gắn với OS thread hoặc executor.

---

## 471.10 — Worker pool

ThreadPool chứa một tập worker.

```text
ThreadPool {
    workers
    queues
    policy
}
```

---

## 471.11 — No mandatory global pool

Axiom không tự tạo global thread pool.

Application phải chọn hoặc library phải document việc tạo pool.

---

# 471.12 — Work queue

Work queue có thể bounded hoặc unbounded.

---

## 471.13 — Bounded queue

Bounded queue có:

```text
capacity
full policy
```

Full policy có thể:

```text
Block
Reject
Drop
RunInline
```

Phải explicit.

---

## 471.14 — Unbounded queue

Unbounded queue là optional và vẫn phải chịu memory exhaustion.

---

## 471.15 — Queue ownership

Job chỉ được tồn tại trong một ownership state hợp lệ.

Không cho phép worker và queue cùng sở hữu job một cách không xác định.

---

# 471.16 — Queue ordering

Các queue có thể cung cấp:

```text
FIFO
LIFO
Priority
Deadline
```

Ordering là property của queue/scheduler.

---

## 471.17 — FIFO

FIFO phù hợp workload cần fairness đơn giản.

Không đảm bảo toàn hệ thống FIFO.

---

## 471.18 — Priority

Priority có numeric hoặc enum policy.

Không được giả định priority luôn đảm bảo latency.

---

## 471.19 — Deadline

Job có thể có deadline.

Scheduler chỉ best-effort nếu OS/runtime không cung cấp real-time guarantees.

---

# 471.20 — Work stealing

Thread pool có thể dùng local deque + stealing.

```text
Worker A → local deque
Worker B → local deque
Worker C → local deque

idle worker → steal
```

Đây là implementation strategy, không phải semantic guarantee.

---

## 471.21 — Fairness

Scheduler phải document fairness properties nếu có.

Không mặc định tuyên bố starvation-free.

---

## 471.22 — Starvation

Scheduler diagnostics có thể phát hiện job chờ quá lâu.

---

# 471.23 — CPU-bound jobs

CPU-bound jobs được phép chạy trên dedicated CPU worker pool.

---

## 471.24 — Blocking jobs

Blocking work phải được đánh dấu hoặc submit vào blocking executor.

Không chạy blocking operation tùy tiện trên executor async nhỏ.

---

## 471.25 — IO-bound jobs

IO-bound jobs tích hợp 454/424 async executor.

---

# 471.26 — Async integration

Async task có thể được poll bởi executor.

Không tự động tạo thread cho mỗi Future.

---

## 471.27 — Future polling

Executor chịu trách nhiệm:

```text
poll
→ Pending
→ wake
→ poll again
→ Ready
```

---

## 471.28 — Wake mechanism

Future có thể đăng ký wake handle.

Wake không được tạo busy-loop mặc định.

---

## 471.29 — Blocking-to-async bridge

Blocking operation có thể được chạy trên blocking pool.

---

# 471.30 — Cancellation

Cancellation là cooperative.

```text
CancellationToken
```

---

## 471.31 — Cancellation propagation

Parent cancellation truyền xuống child task theo task-group policy.

---

## 471.32 — Cancellation safety

Cancellation không được bỏ qua cleanup của 423.

---

## 471.33 — Non-cancellable region

Library có thể định nghĩa critical cleanup sections không bị cancellation giữa chừng.

---

# 471.34 — Task dependencies

Job có thể phụ thuộc job khác:

```text
A → B
A → C
B,C → D
```

---

## 471.35 — DAG scheduler

Scheduler có thể thực thi dependency graph:

```text
A
├── B
├── C
└── D
     ↑
    B,C
```

---

## 471.36 — Dependency failure

Nếu dependency thất bại, dependent job có policy:

```text
Cancel
Skip
Run
PropagateError
```

---

## 471.37 — Cycle detection

Explicit task DAG phải reject dependency cycle.

---

# 471.38 — Parallel loop

Library cung cấp:

```text
parallel_for
parallel_map
parallel_reduce
```

---

## 471.39 — Range partitioning

Parallel loop chia range thành chunks.

Partition strategy có thể:

```text
static
dynamic
guided
adaptive
```

---

## 471.40 — Grain size

Consumer có thể chỉ định grain size.

Scheduler có thể auto-tune nhưng phải có observable policy.

---

## 471.41 — Reduction

Parallel reduction phải định nghĩa associative requirement.

Floating-point reduction không mặc định deterministic bit-for-bit.

---

## 471.42 — Deterministic parallel reduction

Có thể cung cấp deterministic tree reduction khi application yêu cầu.

---

# 471.43 — Fork/join

Concept:

```text
fork(A)
fork(B)
join(A,B)
```

được library-level.

---

## 471.44 — Map/reduce

Map/reduce có thể reuse worker pool.

---

# 471.45 — Task-local state

Task-local storage khác TLS của OS thread.

```text
TaskLocal<T>
```

Một task có thể migrate giữa workers mà không làm thay đổi logical task-local state.

---

## 471.46 — TLS

TLS 424 vẫn gắn với OS thread.

Không được nhầm TLS với TaskLocal.

---

# 471.47 — Task context

Context có thể chứa:

```text
task_id
parent_id
cancellation
deadline
priority
trace_id
```

---

## 471.48 — Context propagation

Context propagation phải explicit/configurable.

Không copy toàn bộ application state vào mỗi task.

---

# 471.49 — Error propagation

Task failure trả về:

```text
Result<T,E>
```

---

## 471.50 — Child failure

TaskGroup có thể chọn policy:

```text
Ignore
Collect
CancelSiblings
FailFast
```

---

## 471.51 — Panic

Panic trong worker phải được bắt tại task boundary nếu scheduler hỗ trợ recovery.

Không để panic phá hỏng toàn bộ process một cách ngầm.

---

## 471.52 — Unrecoverable worker failure

Nếu worker/runtime không thể tiếp tục, scheduler phải có explicit failure policy.

---

# 471.53 — Result collection

Có thể collect:

```text
Vec<Result<T,E>>
```

nhưng collection phải tôn memory limits.

---

## 471.54 — Streaming results

Workload lớn có thể stream results thay vì giữ toàn bộ kết quả.

---

## 471.55 — Backpressure

Producer nhanh hơn consumer phải chịu backpressure.

---

# 471.56 — Shutdown

Scheduler states:

```text
Running
Draining
Stopping
Stopped
Failed
```

---

## 471.57 — Graceful shutdown

Graceful shutdown:

```text
stop accepting
→ drain/cancel
→ join workers
→ release resources
```

---

## 471.58 — Immediate shutdown

Immediate shutdown có thể cancel pending jobs.

Đang chạy job chỉ bị force terminate nếu execution mechanism hỗ trợ an toàn; Axiom không giả định arbitrary thread kill là safe.

---

## 471.59 — Worker join

Worker lifecycle tích hợp 424.

---

# 471.60 — CPU affinity

Worker có thể có affinity policy.

---

## 471.61 — NUMA

Scheduler có thể hỗ trợ NUMA-aware placement.

---

## 471.62 — Memory locality

Job metadata có thể khai báo locality hints.

Hints không phải correctness guarantees.

---

# 471.63 — Priority inversion

Scheduler/library có thể cung cấp priority-inheritance mechanisms khi sử dụng locks.

Không tự động áp dụng cho mọi queue.

---

## 471.64 — Deadlock

Scheduler không thể tự đảm bảo application không deadlock.

Diagnostic tooling có thể phát hiện các lock/task dependency patterns.

---

# 471.65 — Deterministic scheduler

Testing profile có thể dùng deterministic scheduler:

```textseed id="20wq4u"
virtual time
controlled worker count
```

---

## 471.66 — Race testing

Scheduler có thể randomize scheduling để tăng khả năng phát hiện race.

---

## 471.67 — Virtual time

Timer-driven tasks có thể chạy bằng virtual clock trong test.

---

# 471.68 — Realtime isolation

`@realtime` code của 461 không được mặc định submit vào ordinary worker pool.

Realtime scheduler phải là explicit subsystem.

---

## 471.69 — Realtime job constraints

Realtime jobs:

```textno allocation id="q6o0u1"
no blocking
no arbitrary locks
no filesystem
no network
```

theo 461.

---

# 471.70 — GPU task integration

GPU operations có thể được biểu diễn thành task/event dependencies:

```text id="c8p9w1"
Upload
   ↓
Kernel
   ↓
Download
```

Tích hợp 459.

---

## 471.71 — GPU completion

GPU completion event có thể wake CPU task.

---

## 471.72 — CPU/GPU dependency

Scheduler không được coi GPU operation như CPU execution.

---

# 471.73 — Resource integration

Resource loading 469 có thể submit jobs:

```text id="s0m3jk"
IO
→ decode
→ transform
→ GPU upload
```

---

## 471.74 — Media integration

462 có thể dùng task graph cho:

```text demux
→ decode
→ process
→ render
```

---

# 471.75 — Performance

Scheduler benchmark:

```text id="9e0wz7"
submit latency
queue latency
throughput
worker utilization
steal rate
context overhead
scaling
memory overhead
```

---

## 471.76 — Scheduler overhead

Job abstraction không được bắt buộc dùng cho tiny operations nếu direct call rẻ hơn.

---

## 471.77 — Inline execution

Scheduler có thể `run_inline` khi workload nhỏ.

---

## 471.78 — Adaptive execution

Parallel algorithms có thể chọn serial path dưới threshold.

Threshold phải là implementation policy, không thay đổi observable correctness.

---

# 471.79 — AI metadata

446 expose:

```text id="w4b1o6"
task graph
parent/child
dependencies
queue
worker
priority
deadline
cancellation
blocking
CPU/GPU
latency
```

---

## 471.80 — Explain scheduling

AI tooling có thể trả lời:

```textWhy is job X waiting?
```

với causes:

```text dependency
queue saturation
worker exhaustion
lock
IO
cancellation
priority
```

---

# 471.81 — Security

Untrusted task input vẫn phải được xử lý theo 445.

Scheduler không phải sandbox.

---

## 471.82 — Resource limits

Scheduler có thể giới hạn:

```text max workers
max queued jobs
max task duration
memory budget
```

---

# 471.83 — Testing

Tests phải bao gồm:

```text creation
submission
ordering
parallel execution
cancellation
failure
shutdown
dependency
backpressure
worker loss
```

---

## 471.84 — Stress

Stress tests với:

```text millions of jobs
worker churn
queue saturation
nested tasks
cancellation storms
```

---

## 471.85 — Fuzzing

Fuzz task dependency graphs, cancellation timing và scheduler events.

---

# 471.86 — Hard invariants

1. Task khác Thread.
2. Job khác Task.
3. Future biểu diễn eventual result.
4. Scheduler không phải language core.
5. Không có global thread pool bắt buộc.
6. OS thread lifecycle tuân 424.
7. Worker ownership explicit.
8. Queue ownership deterministic.
9. Queue ordering được document.
10. Bounded queue có full policy.
11. Unbounded queue chịu resource limits.
12. Priority không mặc định là realtime guarantee.
13. Deadline không mặc định là realtime guarantee.
14. Work stealing chỉ là implementation strategy.
15. Scheduler không tự tuyên bố starvation-free nếu không chứng minh.
16. Blocking job phải được phân biệt.
17. Blocking không mặc định chạy trên async executor.
18. Async không tự tạo OS thread cho mỗi task.
19. Future polling không busy-loop mặc định.
20. Wake mechanism explicit.
21. Cancellation cooperative.
22. Cancellation không bỏ qua cleanup.
23. Parent cancellation có propagation semantics.
24. Task dependencies explicit.
25. DAG cycle bị reject.
26. Dependency failure có policy.
27. Parallel loop là library abstraction.
28. Parallel reduction có floating-point semantics rõ ràng.
29. Deterministic reduction có thể được yêu cầu.
30. Fork/join không phải language primitive bắt buộc.
31. Task-local khác TLS.
32. Context propagation explicit.
33. Task error dùng Result.
34. Child failure có policy.
35. Panic boundary explicit.
36. Result collection không được vô hạn ngầm.
37. Streaming result hỗ trợ backpressure.
38. Scheduler shutdown có state.
39. Graceful shutdown được hỗ trợ.
40. Arbitrary thread kill không được coi là safe.
41. CPU affinity là hint/policy rõ ràng.
42. NUMA support là optional.
43. Memory locality hints không phải correctness guarantees.
44. Lock deadlock không được tự động coi là scheduler bug.
45. Deterministic scheduler hỗ trợ testing.
46. Virtual time hỗ trợ testing khi cần.
47. Scheduler randomization có thể hỗ trợ race testing.
48. Realtime code không mặc định chạy ordinary worker pool.
49. GPU task khác CPU task.
50. GPU completion có thể wake CPU task.
51. Resource loading có thể sử dụng scheduler.
52. Media pipeline có thể sử dụng scheduler.
53. Scheduler có benchmark.
54. Tiny work có thể chạy inline.
55. Parallel algorithms có serial fallback.
56. AI query được task graph.
57. AI query được queue/worker state.
58. AI query được scheduling delay causes.
59. Scheduler có resource limits.
60. Scheduler không phải sandbox.
61. Fuzzing scheduler được hỗ trợ.
62. Nested task execution không được tạo thread explosion mặc định.
63. Worker count configurable.
64. Scheduler policy không được thay đổi language semantics.
65. Scheduler không yêu cầu GC.
66. Scheduler không yêu cầu borrow checker.
67. Scheduler không yêu cầu GUI.
68. Scheduler không yêu cầu network.
69. Scheduler không yêu cầu database.
70. Scheduler có thể bị loại khỏi freestanding binary.
71. **Axiom task/job foundation phải cho phép xây dựng hệ thống parallel/async/high-throughput hiệu năng cao mà vẫn phân biệt rõ logical work với execution resource, không tạo hidden threads, hidden scheduler hoặc hidden parallelism.**

**BOOTSTRAP-471 hoàn tất.**

---

# BOOTSTRAP-472 — ACTOR, MESSAGE PASSING, CHANNELS, MAILBOX, STREAM PROCESSING & ISOLATED CONCURRENCY

472 tiếp tục từ 424 và 471 để xây dựng concurrency abstraction cấp cao hơn mà **không đưa shared mutable state trở thành mặc định**.

Kiến trúc:

```text
                    APPLICATION
                         │
              ┌──────────┴──────────┐
              ↓                     ↓
           Actor A               Actor B
              │                     │
          Mailbox A            Mailbox B
              │                     │
              └────── Message ──────┘
                         │
                    Scheduler
                         │
                    Thread/Task
```

Core distinction:

```text
Shared Memory
      ≠
Message Passing
      ≠
Actor
      ≠
Channel
      ≠
Stream
```

472 sẽ khóa:

- typed channels;
- bounded/unbounded channels;
- SPSC/MPSC/MPMC;
- synchronous/asynchronous channels;
- send/receive;
- select;
- timeout/deadline;
- cancellation;
- backpressure;
- channel closure;
- sender/receiver ownership;
- actor identity;
- actor mailbox;
- actor lifecycle;
- actor supervision;
- actor restart;
- actor state isolation;
- immutable messages;
- move-based messages;
- serialization boundaries;
- zero-copy intra-process messages;
- cross-process messages;
- IPC integration 454;
- network actor transport;
- ordering guarantees;
- per-sender ordering;
- global ordering distinction;
- priority messages;
- mailbox overflow;
- poison/error messages;
- request/response;
- ask/tell patterns;
- streaming;
- fan-in/fan-out;
- broadcast;
- pub/sub;
- dead-letter handling;
- shutdown/drain;
- failure propagation;
- supervision trees;
- actor/task integration 471;
- realtime isolation;
- GPU/media pipelines;
- AI-readable message/task graph;
- tracing;
- deterministic actor testing;
- fuzzing;
- security/trust boundaries;
- no mandatory actor runtime;
- no hidden serialization;
- no hidden network;
- no hidden threads.

Đặc biệt sẽ khóa nguyên tắc:

```text
Actor state
    ↓
private mutable state

Message
    ↓
owned immutable/movable data

Communication
    ↓
explicit mailbox/channel
```

Qua đó Axiom có thể hỗ trợ cả **low-level lock-free systems programming** lẫn **actor/message-oriented server, GUI, distributed và media pipelines**, nhưng không ép mọi chương trình phải sử dụng actor model.