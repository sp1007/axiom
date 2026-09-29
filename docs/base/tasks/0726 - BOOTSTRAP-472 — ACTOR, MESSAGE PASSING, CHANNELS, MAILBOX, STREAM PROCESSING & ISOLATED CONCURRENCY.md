# BOOTSTRAP-472 — ACTOR, MESSAGE PASSING, CHANNELS, MAILBOX, STREAM PROCESSING & ISOLATED CONCURRENCY

**Trạng thái: COMPLETED / LOCKED**

472 xây dựng concurrency abstraction cấp cao trên 424 + 471, tập trung vào **message passing, isolated mutable state và streaming**, nhưng không biến Actor thành mô hình bắt buộc của Axiom.

Kiến trúc:

```text
Application
    │
    ├──────────────┐
    ↓              ↓
 Actor A         Actor B
    │              │
 Mailbox A      Mailbox B
    │              │
    └──── Message ─┘
           │
       Scheduler
           │
      Task / Thread
```

Nguyên tắc:

```text
Shared Memory
      ≠
Message Passing
      ≠
Channel
      ≠
Actor
      ≠
Stream
```

---

## 472.1 — Message

Message là một giá trị được truyền từ sender tới receiver.

Mặc định message phải có ownership rõ ràng.

---

## 472.2 — Move-based message

Message có thể được move qua channel:

```text
send(value)
```

Sau khi send thành công, sender không còn ownership của value.

---

## 472.3 — Copy message

Nếu `T` là Copy, message có thể được copy theo semantics của 423.

---

## 472.4 — Clone message

Clone phải explicit.

Không tự động deep-copy object graph.

---

## 472.5 — Immutable message

Message có thể được thiết kế immutable để dễ share.

---

## 472.6 — Message validity

Receiver chỉ nhận được message ở trạng thái hợp lệ theo type system/ownership rules.

---

# 472.7 — Channel

Canonical abstraction:

```text
Channel<T>
Sender<T>
Receiver<T>
```

---

## 472.8 — Channel split

Một channel tạo endpoint:

```text
sender
receiver
```

Ownership của endpoint explicit.

---

## 472.9 — SPSC

Single-producer/single-consumer channel có thể tối ưu lock-free/ring-buffer.

---

## 472.10 — MPSC

Multiple producers, one consumer.

---

## 472.11 — SPMC

Một producer, nhiều consumer nếu implementation hỗ trợ.

---

## 472.12 — MPMC

Multiple producers/multiple consumers.

Không mặc định lock-free.

---

# 472.13 — Bounded channel

Bounded channel có capacity:

```text
Channel<T>(capacity = N)
```

---

## 472.14 — Full policy

Khi đầy:

```text
Block
Reject
DropNewest
DropOldest
RunBackpressure
```

Phải explicit.

---

## 472.15 — Unbounded channel

Unbounded channel được phép nhưng phải chịu memory/resource limits.

---

## 472.16 — Zero-capacity channel

Có thể có rendezvous channel:

```text
capacity = 0
```

Send chỉ hoàn tất khi receiver đồng bộ.

---

# 472.17 — Send

Concept:

```text
send(value) -> Result<unit, SendError>
```

---

## 472.18 — Receive

```text
receive() -> Result<T, ReceiveError>
```

---

## 472.19 — Try send

Không blocking:

```text
try_send(value)
```

---

## 472.20 — Try receive

```text
try_receive()
```

---

## 472.21 — Async send/receive

Async channel operations tích hợp 424:

```text
send_async
receive_async
```

---

# 472.22 — Channel closure

Channel có trạng thái:

```text
Open
Closing
Closed
```

---

## 472.23 — Sender drop

Khi sender cuối cùng bị destroy, receiver có thể nhận `Closed`.

---

## 472.24 — Receiver drop

Khi receiver không còn tồn tại, sender nhận `Disconnected`.

---

## 472.25 — Drain

Channel có thể hỗ trợ:

```text
close()
drain()
```

để xử lý message còn tồn.

---

# 472.26 — Select

Nhiều channel có thể chờ bằng:

```text
select {
    msg = rx1.recv() => ...
    msg = rx2.recv() => ...
}
```

---

## 472.27 — Select fairness

Fairness policy phải được document.

Không giả định first-ready luôn công bằng.

---

## 472.28 — Select timeout

Có thể chọn timeout/deadline branch.

---

## 472.29 — Select cancellation

Select tích hợp `CancellationToken`.

---

# 472.30 — Ordering

Channel phải document ordering guarantee.

---

## 472.31 — Per-sender ordering

Channel có thể đảm bảo FIFO đối với một sender.

---

## 472.32 — Global ordering

MPMC channel không được tự động tuyên bố global FIFO nếu implementation không đảm bảo.

---

## 472.33 — Priority messages

Priority channel là abstraction riêng hoặc policy explicit.

---

# 472.34 — Backpressure

Producer phải có cách phản ứng khi consumer chậm.

Các cơ chế:

```text
block
await
reject
drop
buffer
```

---

## 472.35 — Streaming channel

Channel có thể được dùng như stream:

```text
Producer → Channel → Consumer
```

---

## 472.36 — Fan-in

Nhiều producers → một consumer.

---

## 472.37 — Fan-out

Một producer → nhiều consumers.

Distribution semantics phải explicit:

```text
work sharing
broadcast
```

---

## 472.38 — Broadcast

Broadcast tạo logical delivery tới nhiều subscribers.

Không được giả định zero-copy nếu receiver lifetime khác nhau.

---

# 472.39 — Actor

Actor là entity có:

```text
identity
private state
mailbox
behavior
lifecycle
```

---

## 472.40 — Actor state

Mutable actor state mặc định chỉ actor đó truy cập trực tiếp.

---

## 472.41 — Actor message

Actor interaction thông qua mailbox/message.

---

## 472.42 — Actor identity

Actor identity không được là memory address.

Concept:

```text
ActorId
```

---

## 472.43 — Actor reference

```text
ActorRef<TMessage>
```

là capability gửi message tới actor.

---

## 472.44 — Actor spawn

Actor có thể được tạo bởi scheduler:

```text
spawn_actor(...)
```

---

## 472.45 — Actor execution

Actor có thể chạy:

- một message mỗi lần;
- batch nhiều message;
- time-sliced processing.

Policy implementation-specific.

---

# 472.46 — Mailbox

Mailbox chứa messages chờ actor xử lý.

---

## 472.47 — Mailbox capacity

Mailbox có thể bounded/unbounded.

---

## 472.48 — Mailbox overflow

Overflow policy:

```text
BlockSender
Reject
Drop
DeadLetter
```

phải explicit.

---

## 472.49 — Mailbox ordering

Mailbox ordering phải được document.

---

## 472.50 — Mailbox priority

Priority mailbox là optional.

---

# 472.51 — Actor lifecycle

```text
Created
Starting
Running
Stopping
Stopped
Failed
```

---

## 472.52 — Actor initialization

Initialization có thể fail bằng `Result`.

---

## 472.53 — Actor shutdown

Shutdown phải xử lý:

```text
stop accepting
→ drain/cancel
→ cleanup
→ stopped
```

---

## 472.54 — Graceful stop

Graceful stop xử lý messages theo configured policy trước khi đóng.

---

## 472.55 — Immediate stop

Immediate stop có thể bỏ pending messages theo explicit policy.

---

# 472.56 — Actor failure

Actor failure không mặc định làm process crash.

---

## 472.57 — Supervision

Supervisor có thể quản lý child actors.

Policy:

```text
Restart
Stop
Escalate
Ignore
```

---

## 472.58 — Restart

Restart phải định nghĩa state semantics.

Không được tự động giả định state cũ còn nguyên.

---

## 472.59 — Restart backoff

Supervisor có thể dùng exponential backoff.

---

## 472.60 — Failure limit

Supervisor có thể giới hạn restart attempts/window.

---

# 472.61 — Supervision tree

```text
Supervisor
 ├── Actor A
 ├── Actor B
 └── Supervisor C
      ├── Actor D
      └── Actor E
```

---

## 472.62 — Failure isolation

Failure của actor không được làm hỏng actor khác trừ khi supervision policy yêu cầu.

---

# 472.63 — Request/response

ActorRef có thể hỗ trợ request/response:

```text
request(message) -> Future<Response>
```

---

## 472.64 — Ask pattern

Ask phải có timeout/cancellation semantics.

---

## 472.65 — Tell pattern

Fire-and-forget:

```text
tell(message)
```

phải có defined delivery/failure semantics.

---

## 472.66 — Delivery guarantee

Không mặc định tuyên bố:

```text
exactly once
```

Actor transport phải công bố semantics:

```text
at-most-once
at-least-once
local reliable
```

---

# 472.67 — Dead letters

Message không thể delivery có thể được đưa vào:

```text
DeadLetter
```

---

## 472.68 — Dead-letter observability

Dead letters phải có metadata để debug.

---

# 472.69 — Cross-thread messaging

Channel/ActorRef có thể chuyển giữa threads nếu type đáp ứng `Send`/`Share`.

---

## 472.70 — Cross-process messaging

454 IPC có thể làm transport cho message.

---

## 472.71 — Cross-machine messaging

Network transport có thể được dùng nhưng không thuộc actor core.

---

## 472.72 — Serialization boundary

Cross-process/machine message cần serialization trừ khi sử dụng shared-memory representation hợp lệ.

---

## 472.73 — Zero-copy local message

In-process message có thể zero-copy bằng move ownership.

---

## 472.74 — Shared-memory message

Shared-memory messaging cần explicit lifetime/synchronization.

---

# 472.75 — Stream processing

Stream abstraction:

```text
Stream<T>
```

có thể biểu diễn sequence bất đồng bộ.

---

## 472.76 — Stream operators

Library có thể cung cấp:

```text
map
filter
flat_map
buffer
batch
window
merge
zip
fold
```

---

## 472.77 — Streaming backpressure

Stream phải có defined backpressure semantics.

---

## 472.78 — Stream cancellation

Cancellation tích hợp 424.

---

## 472.79 — Stream errors

Stream có thể kết thúc bằng:

```text
Complete
Error(E)
Cancelled
```

---

# 472.80 — Realtime isolation

Actor/channel không được sử dụng tùy tiện trong `@realtime` callback.

Realtime channel phải:

- bounded;
- preallocated;
- non-blocking;
- predictable.

---

## 472.81 — Audio integration

461 có thể sử dụng SPSC channels/ring buffers cho audio producer-consumer.

---

## 472.82 — Media integration

462 có thể dùng channels giữa:

```text
demux → decode → process → encode
```

---

## 472.83 — GPU integration

459 có thể dùng message/event dependencies giữa CPU và GPU tasks.

---

# 472.84 — Scheduler integration

472 actors/channels dùng 471 scheduler nếu cần.

Actor không sở hữu scheduler mặc định.

---

## 472.85 — Worker affinity

Actor có thể có placement hint nhưng không được phụ thuộc vào một OS thread nếu semantics không yêu cầu.

---

## 472.86 — Actor migration

Actor có thể migrate giữa workers nếu implementation cho phép.

Actor state phải vẫn hợp lệ.

---

# 472.87 — Deterministic testing

Actor runtime có test scheduler:

```text
virtual time
controlled ordering
deterministic mailbox
```

---

## 472.88 — Message recording

Có thể record message stream để replay.

---

## 472.89 — Replay

Replay phải phân biệt:

```text
input messages
scheduler events
external IO
randomness
time
```

---

# 472.90 — Security

Message từ external boundary là untrusted.

---

## 472.91 — Capability-based actor reference

ActorRef có thể được xem là capability.

Không ai có ActorRef thì không gửi trực tiếp được tới actor đó.

---

## 472.92 — Message validation

Cross-boundary messages phải validate size/count/nesting.

---

## 472.93 — Resource limits

Actor system có thể giới hạn:

```text
actors
mailbox size
message size
messages/sec
memory
workers
```

---

# 472.94 — AI metadata

446 expose:

```text
ActorId
parent
supervisor
mailbox
message types
sender/receiver graph
task mapping
queue
state
failure
```

---

## 472.95 — Explain message delay

AI tooling có thể truy vấn:

```text
why message X is waiting
```

và nhận:

```text
mailbox full
actor busy
dependency
scheduler queue
backpressure
lock
IO
```

---

# 472.96 — Testing

Test:

```text
send/receive
close
disconnect
ordering
select
timeout
cancellation
backpressure
overflow
actor failure
restart
shutdown
```

---

## 472.97 — Stress testing

Stress:

```text
millions of messages
many actors
mailbox saturation
producer bursts
consumer stalls
actor restart storms
```

---

## 472.98 — Fuzzing

Fuzz:

- message contents;
- mailbox ordering;
- dependency graph;
- cancellation timing;
- actor failures;
- serialization boundaries.

---

# 472.99 — Performance

Benchmarks đo:

```text
send latency
receive latency
throughput
allocation count
copy count
queue contention
mailbox latency
actor scheduling overhead
```

---

## 472.100 — Copy-elision

Compiler/library có thể tối ưu message movement nhưng không được thay đổi ownership semantics.

---

# 472.101 — Hard invariants

1. Message có ownership rõ ràng.
2. Move message được hỗ trợ.
3. Copy message chỉ theo Copy semantics.
4. Clone phải explicit.
5. Channel là abstraction explicit.
6. SPSC được hỗ trợ.
7. MPSC được hỗ trợ.
8. MPMC có thể được hỗ trợ.
9. Lock-free không phải mặc định guarantee.
10. Bounded channel có capacity.
11. Full policy explicit.
12. Unbounded channel chịu resource limits.
13. Zero-capacity channel có rendezvous semantics.
14. Send có failure semantics.
15. Receive có failure semantics.
16. Async send/receive tích hợp 424.
17. Channel closure explicit.
18. Sender disconnect được phát hiện.
19. Receiver disconnect được phát hiện.
20. Drain semantics explicit.
21. Select được hỗ trợ.
22. Select timeout được hỗ trợ.
23. Select cancellation được hỗ trợ.
24. Ordering semantics phải document.
25. MPMC không được giả định global FIFO.
26. Backpressure là explicit.
27. Fan-in được hỗ trợ.
28. Fan-out được hỗ trợ.
29. Broadcast là abstraction riêng.
30. Actor có identity.
31. Actor identity không phải memory address.
32. Actor có private state.
33. Actor giao tiếp qua mailbox.
34. ActorRef là explicit capability.
35. Actor không mặc định sở hữu OS thread.
36. Actor scheduler là configurable.
37. Mailbox có capacity policy.
38. Mailbox overflow policy explicit.
39. Actor lifecycle explicit.
40. Actor shutdown có semantics.
41. Actor failure có isolation policy.
42. Supervision là explicit.
43. Restart semantics phải định nghĩa state.
44. Supervisor có thể giới hạn restart.
45. Request/response có timeout.
46. Fire-and-forget có delivery semantics.
47. Exactly-once không được giả định.
48. Dead letters có thể được hỗ trợ.
49. Cross-thread transfer tuân `Send`.
50. Cross-process transfer dùng explicit IPC.
51. Cross-machine transfer dùng explicit network transport.
52. Serialization chỉ xảy ra khi boundary yêu cầu.
53. Local zero-copy message được hỗ trợ khi ownership cho phép.
54. Shared memory synchronization phải explicit.
55. Stream là sequence abstraction.
56. Stream có backpressure.
57. Stream có cancellation.
58. Stream có error semantics.
59. Actor tích hợp scheduler 471.
60. Actor không tạo hidden global scheduler.
61. Actor migration không thay đổi semantics.
62. Realtime code không mặc định dùng actor/mailbox thường.
63. Realtime channels phải bounded/predictable nếu được hỗ trợ.
64. Audio integration tôn 461.
65. Media integration tôn 462.
66. GPU integration tôn 459.
67. Deterministic actor testing được hỗ trợ.
68. Message replay có external-event semantics.
69. Security boundary validate external messages.
70. Actor/message resource limits được hỗ trợ.
71. AI query được actor graph.
72. AI query được mailbox state.
73. AI query được message routes.
74. AI query được scheduling delay.
75. Performance benchmark đo copy/allocation/latency.
76. Fuzzing actor/channel được hỗ trợ.
77. Không yêu cầu GC.
78. Không yêu cầu borrow checker.
79. Không yêu cầu GUI.
80. Không yêu cầu network.
81. Không yêu cầu database.
82. Không yêu cầu global runtime.
83. Không tạo hidden serialization.
84. Không tạo hidden threads.
85. Không biến message passing thành shared mutable state ngầm.
86. **Axiom actor/message foundation phải cung cấp một mô hình concurrency có isolation, ownership, backpressure và failure semantics rõ ràng, đồng thời cho phép triển khai server, pipeline, streaming và distributed systems mà không ép mọi chương trình vào Actor Model.**

**BOOTSTRAP-472 hoàn tất.**

---

# BOOTSTRAP-473 — REACTIVE / DATAFLOW ENGINE, SIGNALS, EVENTS, OBSERVABLES & INCREMENTAL COMPUTATION

473 xây lớp **dataflow/reactive computation** phía trên 471 và 472.

Mục tiêu:

```text
Input
  ↓
Signal
  ↓
Transform
  ↓
Derived State
  ↓
Effect
```

với khả năng dùng cho:

- GUI;
- editor;
- media pipeline;
- telemetry;
- event processing;
- streaming;
- simulation;
- application state;
- incremental computation.

Kiến trúc:

```text
                 DATA SOURCES
                      │
          ┌───────────┼───────────┐
          ↓           ↓           ↓
       Signal       Event       Stream
          │           │           │
          └───────────┼───────────┘
                      ↓
                 Dataflow Graph
                      │
              ┌───────┴────────┐
              ↓                ↓
          Derived State       Effect
              │                │
              └───────┬────────┘
                      ↓
                  Scheduler
```

### 473 sẽ khóa

- Signal;
- Event;
- Stream;
- Observable;
- derived/computed values;
- dependency graph;
- invalidation;
- incremental recomputation;
- topological scheduling;
- batching;
- transactions;
- consistency boundaries;
- cycle detection;
- feedback loops;
- event ordering;
- debounce/throttle;
- sampling;
- buffering;
- backpressure;
- cancellation;
- subscription lifetime;
- automatic unsubscribe;
- weak subscriptions;
- state snapshots;
- event replay;
- hot/cold streams;
- multicast;
- fan-in/fan-out;
- error propagation;
- effect isolation;
- UI binding;
- input integration 465;
- accessibility update integration 466;
- application state 468;
- resource hot reload 469;
- actor/channel integration 472;
- parallel computation 471;
- realtime restrictions 461;
- GPU/dataflow integration 459;
- deterministic testing;
- time virtualization;
- graph visualization;
- AI-readable dependency graph;
- change-impact analysis;
- no hidden global event bus;
- no hidden threads;
- no mandatory runtime.

Đặc biệt sẽ khóa sự khác biệt:

```text
Event
 = something happened

Signal
 = current value that can change

Stream
 = sequence over time

Computed
 = value derived from dependencies

Effect
 = explicit side effect
```

và:

```text
Dependency Graph
      ↓
invalidate
      ↓
schedule
      ↓
recompute
      ↓
publish
```

Điểm quan trọng cho Axiom là **reactive programming không được trở thành một hệ thống magic**: compiler/runtime phải có thể biểu diễn dependency graph, lifetime subscription, scheduling và allocation behavior để optimizer, debugger và AI tooling có thể quan sát và phân tích.