# BOOTSTRAP-473 — REACTIVE / DATAFLOW ENGINE, SIGNALS, EVENTS, OBSERVABLES & INCREMENTAL COMPUTATION

**Trạng thái: COMPLETED / LOCKED**

473 xây dựng lớp reactive/dataflow ở trên 471–472. Đây là **library/runtime capability**, không phải semantics bắt buộc của ngôn ngữ.

Mục tiêu:

```text
Source
  ↓
Signal / Event / Stream
  ↓
Transform
  ↓
Derived State
  ↓
Effect
```

Nguyên tắc quan trọng:

```text
Event    = something happened
Signal   = current value
Stream   = sequence over time
Computed = derived value
Effect   = explicit side effect
```

---

## 473.1 — Event

Event biểu diễn một occurrence:

```text
Event<T>
```

Ví dụ:

```text
MouseMoved
FileChanged
WindowResized
MessageReceived
```

Event không tự duy trì current value.

---

## 473.2 — Signal

Signal giữ current value:

```text
Signal<T>
```

Concept:

```text
value()
set(value)
subscribe(...)
```

---

## 473.3 — Read-only signal

Có thể expose:

```text
ReadSignal<T>
```

để consumer chỉ đọc.

---

## 473.4 — Writable signal

Writer phải có capability rõ ràng.

Không cho mọi subscriber mutation mặc định.

---

# 473.5 — Computed value

Computed value phụ thuộc signal khác:

```text
a ──┐
    ├──> c
b ──┘
```

Ví dụ:

```text
total = price * quantity
```

---

## 473.6 — Dependency tracking

Computed node phải biết dependencies thực tế.

---

## 473.7 — Explicit dependency

Implementation có thể hỗ trợ explicit dependency declaration khi implicit tracking không phù hợp.

---

## 473.8 — Invalidation

Khi source thay đổi:

```text
source changed
      ↓
computed invalidated
```

Không nhất thiết recompute ngay.

---

## 473.9 — Lazy computed

Computed có thể lazy:

```text
change
 ↓
invalidate
 ↓
read
 ↓
recompute
```

---

## 473.10 — Eager computed

Có thể recompute ngay sau commit.

Policy phải explicit.

---

# 473.11 — Dataflow graph

Mọi reactive computation được biểu diễn thành graph:

```text
A ──→ C ──→ E
B ──→ C
D ─────────→ E
```

---

## 473.12 — Node identity

Node có stable logical ID trong debug/tooling.

Không dùng memory address làm semantic identity.

---

## 473.13 — Edge identity

Dependency edges có thể được inspect.

---

## 473.14 — Topological evaluation

Acyclic graph được evaluate theo dependency order.

---

## 473.15 — Cycle detection

Graph cycle phải được phát hiện.

---

## 473.16 — Feedback loop

Feedback loop chỉ hợp lệ khi dùng explicit feedback primitive.

Ví dụ:

```text
Signal
  ↓
Transform
  ↓
Delay
  ↓
Signal
```

---

# 473.17 — Batch update

Nhiều changes có thể được commit thành một batch.

```text
begin_batch()
...
commit()
```

---

## 473.18 — Atomic propagation

Subscribers có thể chỉ nhìn thấy state sau commit.

---

## 473.19 — Intermediate-state suppression

Batch có thể ngăn consumer quan sát các intermediate states.

---

## 473.20 — Nested batches

Nested batch phải có semantics rõ ràng.

Mặc định inner batch không commit độc lập.

---

# 473.21 — Transactions

Reactive transaction khác database transaction.

Không được giả định durability.

---

## 473.22 — Transaction rollback

Nếu validation/effect preparation thất bại, state mutation có thể rollback khi abstraction hỗ trợ transactional state.

---

## 473.23 — Side effects

Effects không được thực hiện giữa lúc graph đang ở intermediate state nếu transaction semantics yêu cầu atomic propagation.

---

# 473.24 — Effect

Effect là explicit side effect:

```text
effect {
    save(state)
}
```

---

## 473.25 — Effect ordering

Effect ordering phải deterministic trong một graph transaction nếu dependencies xác định.

---

## 473.26 — Effect isolation

Effect không được tự động trở thành dependency của mọi node.

---

## 473.27 — Effect failure

Effect có thể trả:

```text
Result<T,E>
```

Failure policy phải explicit.

---

# 473.28 — Subscription

Subscription đại diện quan hệ:

```text
producer → consumer
```

---

## 473.29 — Subscription lifetime

Subscription phải có ownership/lifetime rõ ràng.

---

## 473.30 — Automatic unsubscribe

Khi owning subscription bị destroy, subscription được hủy.

---

## 473.31 — Weak subscription

Có thể hỗ trợ weak subscriptions để tránh giữ object sống vô hạn.

---

## 473.32 — Subscription cancellation

Subscription có thể cancel explicit.

---

# 473.33 — Observable

`Observable<T>` là abstraction sequence/value notification có subscription.

Không đồng nghĩa với Signal.

---

## 473.34 — Hot observable

Hot observable tồn tại độc lập với subscriber.

---

## 473.35 — Cold observable

Cold observable tạo computation/source riêng cho mỗi subscriber.

---

## 473.36 — Multicast

Một source có thể multicast tới nhiều consumers.

---

# 473.37 — Stream

`Stream<T>` biểu diễn sequence theo thời gian.

Tích hợp 472.

---

## 473.38 — Stream transformation

Các operation:

```text
map
filter
flat_map
scan
reduce
merge
zip
buffer
window
```

---

## 473.39 — Stream termination

```text
Complete
Error(E)
Cancelled
```

---

## 473.40 — Stream backpressure

Consumer chậm phải có defined behavior.

---

# 473.41 — Event ordering

Event source phải document ordering.

---

## 473.42 — Event timestamps

Event có thể có monotonic timestamp từ 424/465.

---

## 473.43 — Event sequence

Sequence number có thể dùng để detect dropped/reordered events.

---

# 473.44 — Debounce

Debounce giữ event cuối trong một khoảng thời gian.

---

## 473.45 — Throttle

Throttle giới hạn propagation frequency.

---

## 473.46 — Sample

Sample lấy state/event theo clock.

---

## 473.47 — Buffer

Buffer gom events thành batch.

---

## 473.48 — Window

Window chia stream theo:

```texttime id="s5t0v"
count
event boundary
```

---

# 473.49 — Scheduler integration

Reactive graph có thể dùng scheduler 471.

Không tự tạo scheduler.

---

## 473.50 — Scheduling mode

Có thể có:

```text id="9b70fj"
Immediate
Queued
Batched
Async
```

---

## 473.51 — Immediate mode

Recompute synchronously.

Phù hợp graph nhỏ nhưng có nguy cơ recursive propagation nếu cycle/feedback không được kiểm soát.

---

## 473.52 — Queued mode

Changes được enqueue.

---

## 473.53 — Async mode

Propagation có thể chạy trên executor.

---

# 473.54 — Thread safety

Signal có thể:

```textlocal-only id="m4f8ry"
Send
Share
```

tùy type.

---

## 473.55 — Cross-thread signal

Cross-thread mutation phải dùng synchronization/atomic/channel semantics.

Không có implicit data race protection.

---

# 473.56 — Actor integration

Actor có thể publish events và consume streams.

---

## 473.57 — Channel integration

Channel có thể trở thành stream source.

---

## 473.58 — Message-to-signal

Một message sequence có thể update signal.

---

# 473.59 — GUI integration

452/465 có thể map:

```text id="zv8rcb"
input
 ↓
event
 ↓
signal
 ↓
layout
 ↓
render
```

---

## 473.60 — UI binding

UI property có thể bind với Signal.

---

## 473.61 — Binding lifetime

Binding phải tự động terminate khi owner UI node bị destroy.

---

## 473.62 — Accessibility integration

466 semantic tree updates có thể consume reactive state.

---

# 473.63 — Application state

468 application/session state có thể được biểu diễn bằng Signals.

---

## 473.64 — Configuration integration

470 configuration updates có thể phát event.

Không được tự động biến toàn bộ configuration thành mutable reactive state.

---

# 473.65 — Resource hot reload

469 resource generation change có thể phát resource-changed event.

---

## 473.66 — Media integration

461/462 có thể dùng streams cho:

```text audio frames
video frames
timestamps
metadata
```

---

## 473.67 — GPU integration

459 GPU completion có thể là event source.

---

# 473.68 — Incremental computation

Reactive graph có thể được dùng cho incremental recomputation.

---

## 473.69 — Dirty propagation

Node chỉ được recompute khi dependency có khả năng ảnh hưởng kết quả.

---

## 473.70 — Structural equality

Computed node có thể so sánh old/new value để suppress unchanged notifications.

---

## 473.71 — Equality policy

Equality semantics phải explicit.

Không dùng deep equality ngầm cho mọi object.

---

## 473.72 — Change detection

Có thể hỗ trợ:

```text id="7l2w9d"
Always
Identity
Equality
Custom comparator
```

---

# 473.73 — Memoization

Computed values có thể cache result.

---

## 473.74 — Cache invalidation

Cache invalidation phải dựa trên dependency graph/generation.

---

## 473.75 — Memory limits

Reactive graph phải hỗ trợ giới hạn:

```textnodes id="9kh3y6"
subscriptions
queued events
buffered items
```

---

# 473.76 — Reentrancy

Effect/subscriber reentrancy phải có policy.

Mặc định không cho propagation tạo trạng thái graph không xác định.

---

## 473.77 — Recursive updates

Recursive signal updates phải detect hoặc giới hạn depth.

---

## 473.78 — Event storm

Runtime có thể detect excessive propagation/event storms.

Không tự động drop events nếu semantics yêu cầu reliable delivery.

---

# 473.79 — Cancellation

Reactive subscriptions tích hợp cancellation 424.

---

## 473.80 — Shutdown

Application shutdown phải hủy subscription graph theo ownership order.

---

# 473.81 — Realtime restriction

`@realtime` code không được dùng ordinary reactive engine nếu engine:

- allocate;
- lock;
- schedule unpredictably;
- perform blocking;
- create unbounded queues.

---

## 473.82 — Realtime reactive subset

Có thể cung cấp fixed-capacity realtime signal/stream:

```text id="e8w6c1"
preallocated
bounded
nonblocking
deterministic
```

Tích hợp 461.

---

# 473.83 — Deterministic testing

Reactive engine phải có deterministic scheduler/test mode.

---

## 473.84 — Virtual time

Debounce/throttle/timer operators phải có thể chạy với virtual clock.

---

## 473.85 — Event replay

Events có thể record và replay.

---

## 473.86 — Snapshot testing

Graph state có thể snapshot.

---

# 473.87 — Graph introspection

Tooling có thể query:

```text id="nd1z3y"
nodes
edges
dependencies
subscribers
queued events
dirty nodes
```

---

## 473.88 — Explain recomputation

AI tooling có thể hỏi:

```text id="qg8bkl"
Why was node X recomputed?
```

---

## 473.89 — Explain stale state

Có thể xác định:

```text id="flz0n4"
source changed
node invalidated
scheduler pending
dependency blocked
```

---

## 473.90 — Change impact

Tooling có thể tính dependency impact:

```text id="8x4c1j"
source X changed
→ affected nodes
→ affected effects
```

---

# 473.91 — Performance metrics

Theo dõi:

```text id="h4b6yr"
propagation latency
recompute count
event throughput
queue depth
allocation count
graph size
subscriber count
```

---

## 473.92 — Allocation control

Reactive engine không được âm thầm heap allocate cho mỗi event nếu configured realtime/performance mode không cho phép.

---

## 473.93 — Batch optimization

Compiler/library có thể fuse compatible operations.

Không thay đổi observable ordering/error semantics.

---

# 473.94 — Security

External events là untrusted input.

---

## 473.95 — Resource exhaustion

Input stream có thể gây event storm; engine cần quotas/backpressure.

---

## 473.96 — No arbitrary code execution

Event payload không được tự động interpreted as executable code.

---

# 473.97 — Hard invariants

1. Event khác Signal.
2. Signal khác Stream.
3. Stream khác Observable.
4. Computed khác Effect.
5. Reactive engine không thuộc language core.
6. Signal có current value.
7. Event không yêu cầu current value.
8. Computed có dependency graph.
9. Dependency graph có stable logical identities.
10. Acyclic graph được topologically evaluated.
11. Cycle phải được phát hiện.
12. Feedback loop phải explicit.
13. Lazy computation được hỗ trợ.
14. Eager computation được hỗ trợ.
15. Invalidation khác recomputation.
16. Batch update được hỗ trợ.
17. Atomic propagation được hỗ trợ.
18. Intermediate state có thể bị che trong transaction.
19. Reactive transaction khác database transaction.
20. Effect là explicit side effect.
21. Effect ordering phải xác định.
22. Effect failure dùng Result/policy rõ ràng.
23. Subscription có lifetime rõ ràng.
24. Subscription destruction phải unsubscribe.
25. Weak subscription được hỗ trợ.
26. Cancellation được hỗ trợ.
27. Observable hot/cold semantics phải phân biệt.
28. Multicast semantics explicit.
29. Stream có termination semantics.
30. Stream có backpressure.
31. Event ordering phải document.
32. Event timestamp có thể dùng monotonic clock.
33. Debounce được hỗ trợ.
34. Throttle được hỗ trợ.
35. Sampling được hỗ trợ.
36. Buffer/window được hỗ trợ.
37. Scheduler 471 được tái sử dụng.
38. Reactive engine không tạo hidden scheduler.
39. Immediate/queued/async scheduling phải phân biệt.
40. Cross-thread mutation phải synchronization rõ ràng.
41. Actor integration explicit.
42. Channel integration explicit.
43. GUI binding không tạo hidden global event bus.
44. UI binding có lifetime.
45. Accessibility có thể consume reactive state.
46. Resource hot reload có thể phát event.
47. Media streams có thể tích hợp.
48. GPU events có thể tích hợp.
49. Incremental computation có dirty propagation.
50. Change detection policy explicit.
51. Equality policy explicit.
52. Memoization có dependency-aware invalidation.
53. Reentrancy có semantics.
54. Recursive update được kiểm soát.
55. Event storm có resource limits.
56. Cancellation không bỏ qua cleanup.
57. Shutdown hủy graph theo ownership.
58. Realtime code không mặc định sử dụng ordinary reactive engine.
59. Realtime subset phải bounded/predictable.
60. Deterministic scheduler được hỗ trợ.
61. Virtual time được hỗ trợ.
62. Event replay được hỗ trợ.
63. Graph snapshot được hỗ trợ.
64. Graph introspection được hỗ trợ.
65. AI có thể query dependency graph.
66. AI có thể explain recomputation.
67. AI có thể phân tích change impact.
68. Performance metrics được expose.
69. Allocation behavior observable.
70. Security limits được hỗ trợ.
71. External event data được coi là untrusted.
72. Không tự động execute event payload.
73. Không yêu cầu GC.
74. Không yêu cầu borrow checker.
75. Không yêu cầu GUI.
76. Không yêu cầu network.
77. Không yêu cầu database.
78. Không yêu cầu actor runtime.
79. Không yêu cầu thread pool.
80. Không tạo hidden threads.
81. Không tạo hidden global mutable state.
82. **Axiom reactive/dataflow foundation phải biến event, state, stream, dependency và side effect thành các thành phần có lifecycle, ordering, scheduling và resource behavior quan sát được, để xây dựng GUI, editor, media và incremental systems mà không biến reactive programming thành “magic” khó tối ưu hoặc debug.**

**BOOTSTRAP-473 hoàn tất.**

---

# BOOTSTRAP-474 — TIME, CLOCK, TIMER, DEADLINE, SCHEDULING TIME & TEMPORAL SEMANTICS

474 chuẩn hóa toàn bộ khái niệm thời gian mà các subsystem 424, 461, 462, 468, 471 và 473 đang sử dụng.

Kiến trúc:

```text
                TIME FOUNDATION
                      │
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
   Monotonic       Wall Clock    Virtual Clock
        │             │             │
        ↓             ↓             ↓
    Duration       Date/Time      Testing
        │
   ┌────┼──────────────┐
   ↓    ↓              ↓
 Timer Deadline     Timeout
   │
   ↓
Scheduler / Async / Media / GUI
```

Các phân biệt bắt buộc:

```text
Instant
   ≠
Duration
   ≠
DateTime
   ≠
Timestamp
   ≠
Deadline
   ≠
Timeout
   ≠
Timer
   ≠
Frame Time
```

474 sẽ khóa:

- monotonic clock;
- wall clock;
- UTC;
- local timezone;
- timezone database;
- `Instant`;
- `Duration`;
- `Date`;
- `TimeOfDay`;
- `DateTime`;
- timestamp;
- epoch;
- clock resolution;
- clock precision;
- clock accuracy;
- clock monotonicity;
- timer;
- one-shot timer;
- periodic timer;
- deadline;
- timeout;
- cancellation;
- timer wheel/heap;
- high-resolution timers;
- sleep;
- yield;
- busy wait;
- virtual clock;
- deterministic time testing;
- media clock;
- audio clock;
- presentation clock;
- A/V synchronization;
- scheduler clock;
- distributed clock distinction;
- clock drift;
- leap second handling;
- daylight-saving transitions;
- timezone conversion;
- formatting/parsing;
- duration overflow;
- timestamp range;
- serialization;
- database timestamps;
- file timestamps;
- filesystem time precision;
- OS-specific clock mapping;
- CPU cycle counter;
- TSC;
- performance counters;
- realtime constraints;
- timer allocation behavior;
- timer cancellation races;
- timer coalescing;
- power-saving behavior;
- WASM/browser timing restrictions;
- mobile background timer restrictions;
- AI-readable temporal diagnostics.

Nguyên tắc nền tảng:

```text
Elapsed Time
    → Monotonic Clock

Human Calendar Time
    → Wall Clock / Time Zone

Scheduling
    → Deadline / Timer

Testing
    → Virtual Clock

Media
    → Media Clock
```

Đặc biệt **không được dùng wall-clock time để đo elapsed duration**, và không được dùng `Instant` để biểu diễn lịch/ngày tháng của con người.