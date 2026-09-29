# BOOTSTRAP-205 — Time, Scheduling, Real-Time, Timers & Temporal Semantics

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu:

> **Axiom phải có mô hình thời gian chính xác, hiệu năng cao và không gây nhầm lẫn giữa đo thời gian, lịch thực thi, timeout, wall-clock, logical time và distributed time.**

Đây là tầng nền cho:

- async
- networking
- GUI
- game engine
- audio/video
- real-time
- distributed systems
- database
- profiling
- embedded
- scheduling

---

# 205.1. Không có một `Time` duy nhất

Axiom phân biệt:

```text
Instant
Duration
Deadline
WallClock
MonotonicClock
LogicalClock
VirtualClock
```

Không cho phép trộn chúng tùy tiện.

---

# 205.2. `Duration`

`Duration` là khoảng thời gian:

```axiom
Duration
```

Ví dụ:

```axiom
10.ms
2.s
500.us
```

Nó không biểu diễn một thời điểm.

---

# 205.3. `Instant`

`Instant` là một điểm trên một monotonic timeline.

```axiom
Instant
```

Phép toán hợp lệ:

```text
Instant + Duration → Instant
Instant - Duration → Instant
Instant - Instant → Duration
```

Không cho:

```text
Instant + Instant
```

---

# 205.4. Monotonic clock

Clock dùng cho:

- timeout
- benchmark
- scheduling
- latency
- elapsed time

phải là monotonic.

```text
t2 >= t1
```

theo cùng clock domain.

---

# 205.5. Wall clock

Wall clock biểu diễn thời gian lịch:

```text
DateTime
```

Có thể thay đổi bởi:

- NTP
- user adjustment
- timezone
- daylight saving
- OS correction

Không dùng wall clock để đo elapsed duration.

---

# 205.6. Không implicit conversion

Không cho:

```text
WallTime → Instant
```

hoặc ngược lại nếu không có clock context.

---

# 205.7. Date và time-of-day

Phân biệt:

```text
Date
TimeOfDay
DateTime
Duration
Instant
```

---

# 205.8. Time zone

Timezone là dữ liệu/phần library:

```text
TimeZone
```

Không đưa timezone database vào Core.

---

# 205.9. UTC

UTC là một representation/standard time scale.

Không đồng nhất:

```text
UTC timestamp
```

với:

```text
monotonic Instant
```

---

# 205.10. Leap seconds

Calendar/time library phải xử lý leap-second policy explicit.

Monotonic scheduler không phụ thuộc calendar semantics.

---

# 205.11. Deadline

`Deadline` biểu diễn thời điểm hết hạn:

```text
Deadline
```

Thường được xây từ:

```text
Instant + Duration
```

---

# 205.12. Timeout

Timeout là policy:

```text
timeout = 500.ms
```

Deadline là state:

```text
deadline = ...
```

Có thể chuyển:

```text
Timeout → Deadline
```

tại một thời điểm cụ thể.

---

# 205.13. Timeout propagation

RPC/request context nên truyền:

```text
Deadline
```

thay vì mỗi tầng tự cộng thêm timeout.

Ví dụ:

```text
Client deadline
      ↓
RPC
      ↓
Database
      ↓
Storage
```

---

# 205.14. Remaining time

API:

```text
deadline.remaining()
```

trả:

```text
Duration
```

hoặc zero/expired state.

---

# 205.15. Cancellation và timeout

Hai khái niệm khác nhau:

```text
Cancellation
Timeout
```

Timeout có thể **gây ra** cancellation nhưng không đồng nghĩa với cancellation.

---

# 205.16. Sleep

```text
sleep(duration)
```

là scheduler operation.

Không đảm bảo thread thức dậy chính xác sau đúng duration.

Nó chỉ đảm bảo:

```text
not before requested wake condition
```

trong phạm vi scheduler/OS semantics.

---

# 205.17. Sleep accuracy

Độ chính xác phụ thuộc:

- OS
- timer resolution
- scheduler
- power state
- CPU load

Không đưa accuracy giả tạo vào Core.

---

# 205.18. Yield

```text
yield()
```

nhường execution opportunity.

Không đảm bảo task/thread khác chắc chắn được chạy.

---

# 205.19. Timer

Timer là resource/scheduler object:

```text
Timer
```

có thể:

```text
one-shot
periodic
deadline-based
```

---

# 205.20. One-shot timer

```text
Timer.after(100.ms)
```

phát một completion/event.

---

# 205.21. Periodic timer

```text
Timer.every(1.s)
```

nhưng phải định nghĩa drift policy.

---

# 205.22. Periodic scheduling

Có hai semantics:

```text
fixed-delay
fixed-rate
```

### Fixed delay

```text
execute
 ↓
wait 1s
 ↓
execute
```

### Fixed rate

```text
T0
T1 = T0 + 1s
T2 = T0 + 2s
...
```

Axiom phải phân biệt.

---

# 205.23. Timer drift

Timer periodic không được mặc định cộng:

```text
now + period
```

nếu muốn fixed-rate.

Scheduler phải giữ logical schedule:

```text
next_deadline += period
```

---

# 205.24. Missed ticks

Nếu task chạy quá lâu:

```text
T0
task = 3s
period = 1s
```

scheduler cần policy:

```text
Skip
CatchUp
Coalesce
Delay
```

Không implicit chọn semantics cho application.

---

# 205.25. Timer cancellation

Timer có ownership.

```text
cancel(timer)
```

hoặc Drop có thể cancel theo contract.

Không được để callback chạy sau khi lifetime contract đã kết thúc.

---

# 205.26. Timer callback lifetime

Callback phải giữ mọi captured values sống đủ lâu.

Compiler ownership analysis áp dụng bình thường.

---

# 205.27. Timer callback + async

Timer có thể trả:

```text
Future
```

thay vì callback.

Đây là abstraction phù hợp với Axiom async model.

---

# 205.28. Timer wheel

Runtime có thể dùng:

```text
TimerWheel
```

để giảm chi phí quản lý hàng triệu timers.

Implementation detail, không phải language semantic.

---

# 205.29. Priority queue timers

Scheduler có thể dùng:

```text
min-heap
calendar queue
timer wheel
hierarchical wheel
```

tùy workload.

---

# 205.30. Scheduler

Scheduler là library/runtime component:

```text
Scheduler
```

Không phải Core primitive.

---

# 205.31. Scheduler responsibilities

Scheduler quyết định:

```text
which task runs
when it runs
where it runs
```

nhưng không thay đổi semantic ownership.

---

# 205.32. Task

Task là execution unit:

```text
Task<T>
```

đã có từ async model.

Task có thể:

```text
Ready
Running
Waiting
Completed
Cancelled
Failed
```

---

# 205.33. Scheduler queue

Task queue có ownership:

```text
Task
 ↓ move
SchedulerQueue
```

Scheduler sở hữu task cho tới khi completion/transfer.

---

# 205.34. Task migration

Task có thể chuyển worker:

```text
Worker A
 ↓
Worker B
```

nếu task là migratable.

Các giá trị live across suspension phải thỏa `Send`.

---

# 205.35. Pinned task

Một task có thể yêu cầu:

```text
PinnedExecution
```

nếu library/runtime cần thread affinity hoặc external resource affinity.

Không tạo `Pin<T>` Core.

---

# 205.36. Worker pool

Runtime có thể:

```text
N workers
M tasks
```

với work stealing.

---

# 205.37. Work stealing

Task chỉ được steal nếu execution contract cho phép.

Task chứa:

- thread-local state
- non-Send resource
- OS affinity

có thể không migratable.

---

# 205.38. CPU affinity

API hệ thống:

```text
CpuAffinity
```

là platform/system abstraction.

Không implicit pin mọi task vào CPU.

---

# 205.39. NUMA

Axiom nên expose library/system API:

```text
NumaNode
NumaPolicy
```

cho high-performance workloads.

Không đưa NUMA vào Core type system.

---

# 205.40. NUMA-aware allocation

Allocator có thể chọn:

```text
local node
preferred node
interleaved
replicated
```

nhưng storage policy không thay đổi ownership semantics.

---

# 205.41. Priority

Task có thể có:

```text
Priority
```

nhưng priority là scheduling policy.

Không đảm bảo execution deadline.

---

# 205.42. Priority inversion

Synchronization library/runtime nên hỗ trợ:

```text
priority inheritance
priority ceiling
```

trên platform phù hợp.

---

# 205.43. Real-time scheduling

Axiom hỗ trợ profile:

```text
RealTime
```

nhưng không biến toàn bộ language thành hard-real-time language.

---

# 205.44. Hard real-time

Hard real-time yêu cầu application/runtime contract:

```text
bounded execution
bounded allocation
bounded locking
bounded interrupt latency
```

Compiler không thể tự đảm bảo toàn bộ chỉ bằng type system.

---

# 205.45. Real-time allocation

Trong RT profile:

```text
heap allocation
```

có thể bị cấm hoặc yêu cầu preallocated allocator.

Compiler có thể kiểm tra effect:

```text
Allocate
```

---

# 205.46. Real-time blocking

API blocking có thể bị đánh dấu:

```text
@blocking
```

và RT profile reject.

---

# 205.47. Effects + scheduling

Effect system đã có thể biểu diễn:

```text
IO
Blocking
Allocate
Synchronize
```

Scheduler/RT checker tận dụng chúng.

---

# 205.48. Deadline scheduling

Có thể hỗ trợ:

```text
DeadlineTask
```

library abstraction.

Scheduler có thể dùng:

```text
EDF
```

hoặc platform-specific policy.

---

# 205.49. Periodic real-time tasks

Có:

```text
Period
Deadline
Budget
```

nhưng đây là scheduler contract, không phải ownership primitive.

---

# 205.50. CPU budget

Task có thể có execution budget:

```text
CpuBudget
```

Scheduler theo dõi best-effort hoặc hard constraint tùy profile.

---

# 205.51. Preemption

Thread/task preemption là runtime/OS behavior.

Compiler phải đảm bảo semantic correctness khi execution bị preempt.

---

# 205.52. Cooperative scheduling

Async Future thường:

```text
await
```

là cooperative suspension.

---

# 205.53. Blocking async task

Blocking operation trong async worker có thể:

- bị cấm
- chạy blocking pool
- được compiler/runtime annotate

tùy runtime policy.

---

# 205.54. No hidden blocking

Axiom không được âm thầm biến:

```text
async fn
```

thành một blocking OS call mà programmer không thể nhận biết về semantics.

Effect/tooling phải expose blocking behavior.

---

# 205.55. Event loop

Event loop là scheduler specialization:

```text
EventLoop
```

có thể xử lý:

```text
IO
timer
GUI event
signals
tasks
```

---

# 205.56. GUI event loop

GUI có thể dùng event loop riêng nhưng semantics async vẫn thống nhất.

Không tạo một async language thứ hai.

---

# 205.57. Game loop

Game framework có:

```text
FrameLoop
```

với:

```text
Update
Render
Present
```

và fixed timestep option.

---

# 205.58. Fixed timestep

Physics có thể dùng:

```text
fixed_dt
```

độc lập với render FPS.

---

# 205.59. Variable timestep

Rendering/UI có thể dùng:

```text
delta_time
```

nhưng physics không nên mặc định phụ thuộc frame rate.

---

# 205.60. Audio clock

Audio có clock domain riêng:

```text
AudioSampleClock
```

không đồng nhất trực tiếp với wall clock.

---

# 205.61. GPU clock

GPU timestamps:

```text
GpuTimestamp
```

có domain riêng.

Không trực tiếp so sánh:

```text
CPU Instant
```

với:

```text
GPU Timestamp
```

nếu chưa có calibration/translation.

---

# 205.62. GPU synchronization

Có:

```text
GpuEvent
Fence
Semaphore
TimestampQuery
```

đã tương thích với graphics architecture.

---

# 205.63. Cross-domain timing

CPU↔GPU timing cần:

```text
ClockCalibration
```

nếu muốn latency measurement chính xác.

---

# 205.64. Profiling clock

Profiler có thể dùng high-resolution monotonic clock.

Compiler/Profiler không được dùng wall clock để đo CPU duration.

---

# 205.65. Benchmark

Benchmark framework phải:

```text
warmup
measure
statistics
outlier handling
```

và tránh optimizer loại bỏ computation không quan sát được.

---

# 205.66. Time-dependent optimization

Compiler không được tự giả định:

```text
sleep()
```

là pure.

Time là external effect.

---

# 205.67. Comptime time

`comptime` mặc định không được đọc current wall clock.

Nếu cho phép:

```text
ReadTime
```

thì nó trở thành explicit build input và ảnh hưởng build identity.

---

# 205.68. Reproducible builds

Build reproducible phải disable hoặc control:

```text
current time
random
environment
network
```

theo comptime capability model.

---

# 205.69. Virtual clock

Testing framework có:

```text
VirtualClock
```

cho phép:

```text
advance(1.s)
```

mà không cần chờ thật.

---

# 205.70. Deterministic scheduler

Có:

```text
DeterministicScheduler
```

để test race/timing.

Scheduler lựa chọn task theo deterministic policy.

---

# 205.71. Logical distributed time

Distributed system có:

```text
LamportClock
VectorClock
HLC
```

và chúng không phải `Instant`.

---

# 205.72. Clock domain

Mỗi timestamp nên xác định clock domain:

```text
ClockDomain
```

Ví dụ:

```text
MonotonicCPU
WallUTC
GPU
Audio
Logical
Virtual
```

---

# 205.73. Clock conversion

Chỉ cho conversion nếu có contract:

```text
GPU timestamp
 + calibration
 → CPU timeline estimate
```

Không cho implicit cast.

---

# 205.74. Time overflow

`Duration` và timestamp arithmetic phải có semantics rõ:

```text
checked
saturating
wrapping
```

theo numeric model.

Không C-style undefined overflow.

---

# 205.75. Timer resource ownership

Timer là resource.

Nếu timer bị Drop/cancel:

```text
future callback
```

không được giữ dangling captures.

---

# 205.76. Deadline propagation + cancellation

Một request context có thể chứa:

```text
CancellationToken
Deadline
TraceContext
```

để network/storage/actor layers cùng sử dụng.

---

# 205.77. Deadline inheritance

Child operation mặc định nhận:

```text
min(parent_deadline, child_requested_deadline)
```

nếu API chọn hierarchical deadline semantics.

Không tự động kéo dài deadline.

---

# 205.78. Scheduler fairness

Axiom không đặt một fairness guarantee toàn hệ thống.

Scheduler có thể cung cấp:

```text
FIFO
priority
fair
work-stealing
deadline
```

theo policy.

---

# 205.79. Starvation

Fairness/starvation là scheduler contract.

Không phải compiler correctness invariant.

---

# 205.80. Priority starvation

Nếu priority scheduler có thể starve low-priority tasks, runtime phải document semantics.

---

# 205.81. Timer storm

Runtime nên có protection/policy cho hàng triệu timers:

```text
coalescing
timer wheel
batch wakeup
```

nhưng không thay đổi requested semantic deadlines.

---

# 205.82. Power-aware timers

Mobile/embedded runtime có thể coalesce timers để tiết kiệm năng lượng.

Exact timing profile phải explicit.

---

# 205.83. High-resolution timing

High-resolution clock có thể yêu cầu platform capability.

Không đảm bảo mọi target có nanosecond accuracy.

---

# 205.84. Time resolution

Phân biệt:

```text
representation resolution
clock resolution
measurement accuracy
scheduler resolution
```

Không đánh đồng chúng.

---

# 205.85. Real-time interrupts

Interrupt handler là execution domain đặc biệt:

```text
Interrupt
```

Có restrictions:

- không arbitrary blocking
- không allocation nếu profile cấm
- execution bounded
- synchronization đặc biệt

---

# 205.86. Interrupt-safe code

Có thể có compiler/profile contract:

```text
@interrupt
```

Compiler kiểm tra:

```text
no blocking
no forbidden allocation
no async
no unsafe external operations
```

theo target.

---

# 205.87. Signal execution

Đã có signal model.

Signal handler không được chạy arbitrary application code nếu platform không đảm bảo signal safety.

---

# 205.88. Temporal effects

Effect system có thể bổ sung:

```text
Blocking
TimingSensitive
RealtimeUnsafe
```

nhưng chỉ khi compiler cần cho profile/tooling.

Không biến mọi function thành effect soup.

---

# 205.89. Scheduling diagnostics

CompilerDB nên có:

```text
ax explain scheduling
ax explain blocking
ax explain realtime
```

Ví dụ:

```text
Function may block because:
  File.read()
    → OS I/O
    → Blocking
```

---

# 205.90. Async diagnostics

Compiler có thể chỉ:

```text
Value X lives across await
X is not Send
Task cannot migrate
```

đã phù hợp với async verification.

---

# 205.91. Temporal ownership

Không tạo lifetime kiểu:

```text
'1
'2
```

cho time.

Temporal validity được biểu diễn qua:

```text
Deadline
Cancellation
Capability
Task lifetime
Resource lifetime
```

---

# 205.92. Timer + resource lifetime

Ví dụ conceptual:

```axiom
let timer = Timer.after(5.s, callback)
```

Compiler/runtime phải đảm bảo callback environment sống đến khi timer hoàn tất/cancel.

---

# 205.93. Scheduler + Drop

Task completion phải chạy cleanup đúng ownership semantics.

Nếu task cancelled:

```text
state fields
```

được Drop đúng quy tắc.

---

# 205.94. Scheduler + panic

Panic của một task:

```text
TaskFailed
```

không mặc định kill toàn process nếu runtime profile không yêu cầu.

Structured concurrency có thể propagate failure tới parent.

---

# 205.95. Scheduler + shutdown

Runtime shutdown phải có thứ tự:

```text
stop accepting work
 ↓
cancel/complete tasks according to policy
 ↓
drain events
 ↓
close resources
 ↓
thread shutdown
 ↓
process exit
```

---

# 205.96. Process exit

Phân biệt:

```text
return from main
process_exit
abort
panic
```

đã có runtime model.

Time/scheduler không được giữ process sống vô hạn nếu không còn required runtime work.

---

# 205.97. Sleep in freestanding

Freestanding profile có thể không có clock/timer.

API không tồn tại nếu target capability không hỗ trợ.

---

# 205.98. Embedded time

Embedded target có thể cung cấp:

```text
HardwareTimer
RTC
CycleCounter
```

qua platform/system layer.

---

# 205.99. Time source abstraction

Standard library nên có trait tương tự:

```axiom
trait Clock {
    fn now(self) -> Instant;
}
```

nhưng không expose một global mutable clock.

Testing có thể inject:

```text
VirtualClock
```

---

# 205.100. Temporal invariants — `ATIME`

### `ATIME-20`
`Duration`, `Instant`, `Deadline`, wall time and logical time shall remain distinct semantic types.

### `ATIME-21`
Monotonic time shall be used for elapsed-time measurement and timeout semantics.

### `ATIME-22`
Wall-clock time shall not be used as a monotonic elapsed-time source.

### `ATIME-23`
No implicit conversion shall exist between unrelated clock domains.

### `ATIME-24`
`Instant - Instant` shall produce a duration within the same clock domain.

### `ATIME-25`
`Instant + Duration` shall produce an instant in the same clock domain.

### `ATIME-26`
Deadline semantics shall be explicit.

### `ATIME-27`
Timeout shall remain distinct from cancellation.

### `ATIME-28`
Sleep shall not promise exact wakeup timing beyond its declared scheduler/platform contract.

### `ATIME-29`
Periodic timers shall explicitly define fixed-rate or fixed-delay semantics.

### `ATIME-30`
Periodic timer drift policy shall be explicit.

### `ATIME-31`
Missed periodic ticks shall obey an explicit policy.

### `ATIME-32`
Timer cancellation shall preserve callback/resource lifetime safety.

### `ATIME-33`
Timer callbacks shall not outlive captured resources.

### `ATIME-34`
Scheduler queues shall own queued tasks according to normal ownership semantics.

### `ATIME-35`
Task migration shall require the appropriate `Send` guarantees.

### `ATIME-36`
Pinned execution shall remain an execution/storage contract rather than a new Core pointer model.

### `ATIME-37`
Scheduler policy shall remain separate from language semantics.

### `ATIME-38`
Priority shall not imply a universal execution guarantee.

### `ATIME-39`
Real-time guarantees shall be profile/platform/application contracts.

### `ATIME-40`
Real-time profiles may prohibit unbounded allocation, blocking or synchronization.

### `ATIME-41`
Blocking operations shall remain visible to the effect/tooling system where relevant.

### `ATIME-42`
Async code shall not silently acquire hidden blocking semantics.

### `ATIME-43`
Event loops shall reuse Axiom async/task semantics.

### `ATIME-44`
Game fixed-timestep scheduling shall remain distinct from rendering frame timing.

### `ATIME-45`
Audio clocks shall remain distinct from CPU wall/monotonic clocks.

### `ATIME-46`
GPU timestamps shall remain distinct from CPU timestamps unless explicitly calibrated.

### `ATIME-47`
Comptime time access shall require explicit capability.

### `ATIME-48`
Comptime time inputs shall participate in build identity.

### `ATIME-49`
Reproducible builds shall control or prohibit nondeterministic time inputs.

### `ATIME-50`
Virtual clocks shall be supported for deterministic testing.

### `ATIME-51`
Deterministic schedulers shall be supported for concurrency testing.

### `ATIME-52`
Logical clocks shall remain distinct from physical time.

### `ATIME-53`
Distributed clock synchronization shall not be assumed perfect.

### `ATIME-54`
Clock conversion shall require an explicit calibration/contract.

### `ATIME-55`
Timestamp arithmetic shall have defined overflow behavior.

### `ATIME-56`
Interrupt execution shall remain a distinct execution domain.

### `ATIME-57`
Interrupt handlers shall obey target-specific safety and blocking restrictions.

### `ATIME-58`
Signal execution shall respect platform signal-safety constraints.

### `ATIME-59`
Temporal behavior shall not introduce a separate ownership/lifetime system.

### `ATIME-60`
Task cancellation shall execute normal ownership cleanup.

### `ATIME-61`
Task failure shall remain distinct from process failure unless runtime policy propagates it.

### `ATIME-62`
Scheduler shutdown shall have explicit task/resource shutdown semantics.

### `ATIME-63`
Freestanding targets need not provide a wall clock or scheduler.

### `ATIME-64`
Hardware timers shall remain platform/system abstractions.

### `ATIME-65`
Time sources shall be injectable for deterministic testing.

### `ATIME-66`
Temporal APIs shall not require garbage collection.

### `ATIME-67`
Temporal APIs shall not require a monolithic runtime.

### `ATIME-68`
Timer and scheduler implementations shall be free to optimize representation without changing temporal semantics.

### `ATIME-69`
Compiler diagnostics shall expose relevant blocking, deadline, task migration and real-time restrictions.

### `ATIME-70`
Time semantics shall remain consistent across CPU, GPU, async, GUI, networking, storage and distributed layers.

---

# Kiến trúc thời gian cuối cùng

```text
                         TIME
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   Physical Time      Scheduling       Logical Time
        │                 │                 │
   ┌────┴────┐       ┌────┴────┐       ┌────┴────┐
   │         │       │         │       │         │
Wall      Monotonic  Timer    Task   Lamport    Vector
Clock       Clock    Queue    Queue    HLC       Clock
   │         │         │       │
Calendar   Timeout    Sleep   Async
Timezone   Deadline   Event   Worker
```

Điểm mấu chốt:

```text
Duration
   ≠
Instant
   ≠
Deadline
   ≠
WallClock
   ≠
LogicalClock
   ≠
Scheduler
```

Nhờ vậy Axiom tránh được một lỗi thiết kế phổ biến: tạo một API `Time.now()` rồi dùng cùng một khái niệm cho benchmark, timeout, calendar, distributed consensus, animation và real-time.

---

# BOOTSTRAP-206 — Networking, Protocol Stack, Sockets, HTTP, QUIC & Zero-Copy I/O

**TRẠNG THÁI: NEXT**

Đây là bước hợp lý tiếp theo.

Axiom hiện đã có:

```text
184  OS resources
192  FFI
199  Graphics/GPU
203  Storage
204  Distributed systems
205  Time/Scheduling
```

Nhưng networking vẫn cần được khóa thành một kiến trúc hoàn chỉnh.

Phạm vi 206:

```text
Network
 │
 ├── Address / Endpoint
 ├── Socket
 ├── TCP
 ├── UDP
 ├── QUIC
 ├── TLS
 ├── DNS
 ├── HTTP/1.1
 ├── HTTP/2
 ├── HTTP/3
 ├── WebSocket
 ├── Unix Domain Socket
 ├── Zero-copy
 ├── Scatter/Gather
 ├── io_uring / IOCP / kqueue / epoll
 ├── Async network I/O
 ├── Backpressure
 ├── Connection Pool
 ├── Framing
 ├── Serialization
 ├── RPC
 ├── Streaming
 ├── Multicast
 ├── RDMA
 ├── Kernel bypass
 └── Network security
```

Đặc biệt sẽ phải chốt một điểm quan trọng:

> **Axiom Network API phải cho phép code cấp cao viết HTTP/RPC đơn giản, nhưng đồng thời cho phép code cấp thấp đi thẳng tới zero-copy buffers, scatter/gather, io_uring/IOCP, RDMA hoặc kernel-bypass mà không phá vỡ ownership/capability model.**

Kiến trúc dự kiến sẽ nối trực tiếp:

```text
Axiom Buffer
    ↓
view / mut_view
    ↓
Async I/O
    ↓
Socket
    ↓
Kernel I/O
    ↓
Network
```

và tránh tạo một tầng `ByteBuffer`/`Stream` nặng bắt buộc cho mọi ứng dụng.