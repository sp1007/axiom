# BOOTSTRAP-474 — TIME, CLOCK, TIMER, DEADLINE, SCHEDULING TIME & TEMPORAL SEMANTICS

**Trạng thái: COMPLETED / LOCKED**

474 khóa semantics thời gian dùng chung cho concurrency, async, media, GUI, application lifecycle, storage và reactive system.

Nguyên tắc nền tảng:

```text
Instant
    ≠ Duration
    ≠ DateTime
    ≠ Timestamp
    ≠ Deadline
    ≠ Timeout
    ≠ Timer
    ≠ FrameTime
```

và:

```text
Elapsed Time       → Monotonic Clock
Human Calendar     → Wall Clock + TimeZone
Scheduling         → Deadline / Timer
Testing            → Virtual Clock
Media              → Media Clock
```

---

## 474.1 — Instant

`Instant` biểu diễn một điểm trên một monotonic timeline.

Nó dùng để đo khoảng thời gian, không biểu diễn ngày tháng của con người.

---

## 474.2 — Duration

```text
Duration
```

biểu diễn khoảng thời gian.

Ví dụ:

```text
5ms
200us
2s
3min
```

---

## 474.3 — Duration arithmetic

Hỗ trợ:

```text
add
subtract
multiply
divide
compare
```

Overflow phải có semantics rõ ràng.

---

## 474.4 — Checked duration

API checked trả `Option` hoặc `Result`.

---

## 474.5 — Saturating duration

API saturating không wrap silently.

---

# 474.6 — Monotonic clock

Monotonic clock phải đảm bảo:

```text
t2 >= t1
```

trong cùng timeline.

Không bị ảnh hưởng bởi user chỉnh system clock.

---

## 474.7 — Monotonic resolution

Clock phải expose resolution nếu platform cho phép.

Resolution khác accuracy.

---

## 474.8 — Clock precision

Precision mô tả độ chi tiết biểu diễn.

Không được quảng cáo precision như accuracy.

---

## 474.9 — Clock accuracy

Accuracy phụ thuộc OS/hardware và không phải language guarantee mặc định.

---

# 474.10 — Wall clock

Wall clock biểu diễn civil time.

Có thể bị thay đổi bởi:

- NTP;
- user adjustment;
- timezone changes;
- OS policy.

Không dùng wall clock để benchmark elapsed time.

---

## 474.11 — UTC

UTC là canonical global civil-time representation.

---

## 474.12 — Local time

Local time phụ thuộc timezone/location configuration.

Không phải unique instant nếu thiếu timezone/offset.

---

## 474.13 — OffsetDateTime

Kiểu:

```text
DateTime + UTC offset
```

giúp biểu diễn một civil timestamp có offset.

---

# 474.14 — Date

`Date` chỉ biểu diễn calendar date.

Ví dụ:

```text
2026-09-23
```

---

## 474.15 — TimeOfDay

```text
09:30:15.500
```

không tự chứa timezone.

---

## 474.16 — DateTime

`DateTime` phải phân biệt:

```text
LocalDateTime
OffsetDateTime
ZonedDateTime
```

---

# 474.17 — Time zone

Timezone được định danh bằng IANA-like zone identifier.

Ví dụ:

```text
Asia/Ho_Chi_Minh
```

---

## 474.18 — Timezone database

Timezone database là platform/data dependency, không phải compiler core.

---

## 474.19 — DST transition

Conversion phải xử lý:

```text
gap
overlap
```

khi timezone có daylight-saving rules.

---

## 474.20 — Ambiguous local time

Local datetime rơi vào overlap phải yêu cầu resolution policy hoặc trả ambiguity.

---

# 474.21 — Epoch timestamp

Timestamp có thể biểu diễn:

```text
seconds
milliseconds
microseconds
nanoseconds
```

từ một epoch xác định.

Unit phải explicit.

---

## 474.22 — Timestamp ≠ Instant

Timestamp là serialization/representation của time point.

`Instant` là semantic type.

---

## 474.23 — Timestamp range

Timestamp conversion phải kiểm tra overflow.

---

# 474.24 — Deadline

Deadline là một `Instant` mà operation phải hoàn thành trước hoặc tại đó.

```text
deadline: Instant
```

---

## 474.25 — Timeout

Timeout là một `Duration`.

```text
timeout: Duration
```

API có thể chuyển timeout thành deadline tại thời điểm bắt đầu operation.

---

## 474.26 — Deadline propagation

Network/IO/task operations có thể propagate deadline xuống child operation.

---

## 474.27 — Timeout propagation

Timeout không được tự động cộng dồn một cách không xác định.

---

# 474.28 — Timer

Timer tạo notification tại thời điểm xác định.

---

## 474.29 — One-shot timer

Chạy một lần:

```text
after(5s)
```

---

## 474.30 — Periodic timer

```text
every(1s)
```

---

## 474.31 — Periodic drift

Periodic timer phải định nghĩa:

```text
fixed-rate
fixed-delay
```

---

## 474.32 — Fixed-rate

Lịch dựa trên các mốc lý tưởng:

```text
T0
T0 + P
T0 + 2P
...
```

---

## 474.33 — Fixed-delay

Mốc tiếp theo tính từ khi callback/job trước hoàn thành.

---

# 474.34 — Timer cancellation

Cancel timer phải có semantics rõ ràng nếu callback đang chạy.

---

## 474.35 — Cancellation race

Có thể xảy ra:

```text
cancel
```

đồng thời với:

```text
timer fires
```

API phải document whether callback may still execute.

---

## 474.36 — Timer ownership

Timer handle phải có ownership/lifetime.

---

## 474.37 — Timer drop

Drop có thể cancel timer nếu API định nghĩa owner-cancels semantics.

Detached timers phải explicit.

---

# 474.38 — Sleep

```text
sleep(Duration)
```

không được đảm bảo wake chính xác tới nanosecond.

---

## 474.39 — Sleep semantics

Sleep đảm bảo **không chạy sớm hơn semantics được document**, nhưng actual wake có thể trễ do scheduler/OS.

---

## 474.40 — Yield

`yield()` nhường execution opportunity.

Không đảm bảo thread khác sẽ chạy ngay.

---

## 474.41 — Busy wait

Busy wait là explicit low-level operation.

Chỉ phù hợp khi caller chấp nhận CPU consumption.

---

# 474.42 — Timer backend

Platform có thể dùng:

```text
OS timer
timerfd
IOCP timer
kqueue
mach timers
browser timer
```

nhưng semantics phía trên phải thống nhất.

---

## 474.43 — Timer queue

Runtime/library có thể dùng:

```text
timer heap
timer wheel
calendar queue
```

---

## 474.44 — Timer coalescing

OS có thể coalesce timers vì power/performance.

Application có thể request precision class nếu platform hỗ trợ.

Không biến request thành hard realtime guarantee.

---

# 474.45 — High-resolution timer

High-resolution timers là capability của platform.

Không mặc định có ở mọi target.

---

# 474.46 — Scheduler integration

471 sử dụng:

```text
Instant
Deadline
Duration
```

để schedule jobs.

---

## 474.47 — Task timeout

Task có thể có deadline.

Timeout phải dẫn đến explicit cancellation/failure policy.

---

## 474.48 — Queue deadline

Scheduler có thể ưu tiên job gần deadline.

Đây là scheduling policy, không phải deadline guarantee.

---

# 474.49 — Async integration

424 Future/executor dùng monotonic clock cho timeout.

---

## 474.50 — Async timeout

Concept:

```text
with_timeout(future, 5s)
```

---

## 474.51 — Timeout failure

Timeout có thể trả:

```text
Err(Timeout)
```

thay vì panic.

---

# 474.52 — Reactive integration

473 debounce/throttle/window phải sử dụng explicit clock.

---

## 474.53 — Reactive virtual time

Test có thể inject:

```text
VirtualClock
```

---

## 474.54 — Virtual clock

Virtual clock có:

```text
now()
advance()
set()
```

với controlled semantics.

---

# 474.55 — Deterministic timer tests

Timer tests không được phụ thuộc real wall-clock nếu deterministic test mode được chọn.

---

## 474.56 — Timer ordering

Nếu nhiều timers cùng deadline, ordering phải được định nghĩa hoặc công khai là unspecified.

Không để consumer phụ thuộc accidental ordering.

---

# 474.57 — Media clock

461/462 có thể dùng media clock riêng.

Media clock có thể dựa trên:

```text
audio samples
video frame timestamps
external clock
system clock
```

---

## 474.58 — Media clock ≠ system clock

Media clock có thể drift so với system clock.

---

## 474.59 — Clock drift

A/V system có thể đo và điều chỉnh drift.

---

## 474.60 — Presentation timestamp

462 dùng PTS để xác định presentation time.

PTS unit/timebase phải explicit.

---

# 474.61 — Audio clock

Audio hardware clock có thể là master clock trong realtime playback.

---

## 474.62 — Frame time

Frame time là duration/index relation của media frame, không phải general-purpose wall clock.

---

# 474.63 — Distributed time

Remote machine clocks không được coi là cùng một monotonic timeline.

---

## 474.64 — Network timestamp

Network timestamp cần clock synchronization semantics nếu application cần so sánh giữa machines.

---

## 474.65 — Clock synchronization

NTP/PTP-like synchronization thuộc platform/network layer.

Không phải guarantee của `Instant`.

---

# 474.66 — File timestamps

455 filesystem timestamps phải preserve source precision khi platform cung cấp.

---

## 474.67 — Database timestamps

455 database timestamps phải document:

```text id="w4n9ae"
server time
client time
transaction time
logical time
```

---

# 474.68 — Serialization

Time types có canonical serialization.

Ví dụ:

```text
Duration → explicit integer + unit
Instant → target-defined monotonic serialization only for local/debug use
DateTime → ISO-like representation + offset/zone where required
```

Không serialize raw monotonic clock value để trao đổi giữa machines.

---

# 474.69 — Formatting

Time formatting tách khỏi semantic time representation.

Locale formatting tích hợp 464.

---

## 474.70 — Parsing

Parser phải phân biệt:

```text
date
time
datetime
duration
timestamp
timezone
```

---

# 474.71 — Leap seconds

Axiom phải document policy đối với leap seconds.

Civil-time implementation có thể sử dụng platform time model.

Không cho phép application giả định mọi POSIX timestamp đều encode leap seconds giống nhau.

---

# 474.72 — Monotonic persistence

`Instant` không được dùng làm persistent cross-reboot timestamp.

---

## 474.73 — Reboot

Monotonic timeline có thể reset sau reboot.

---

# 474.74 — CPU cycle counter

CPU cycle counter/TSC có thể được expose trong low-level performance APIs.

Không coi raw cycles là portable `Instant`.

---

## 474.75 — Performance counter

Performance counter thuộc benchmarking/performance layer 450.

---

# 474.76 — Realtime

Realtime systems có thể request timer precision nhưng:

```texttimer precision id="v0j7sy"
≠
scheduler guarantee
≠
deadline guarantee
```

---

## 474.77 — Realtime timer allocation

Realtime timer path phải hỗ trợ preallocated/fixed-capacity implementation nếu subsystem yêu cầu.

---

# 474.78 — Mobile

Mobile OS có thể suspend application.

Timer không được hứa callback execution trong thời gian app bị suspended.

---

# 474.79 — WASM/browser

Browser timer resolution/throttling/security policy được platform layer quản lý.

---

## 474.80 — Background restrictions

Application phải xử lý việc timer bị delayed/cancelled bởi platform.

---

# 474.81 — Time injection

APIs có thể nhận `Clock` abstraction:

```text
fn operation(clock: Clock)
```

giúp testing.

---

## 474.82 — Clock trait

Concept:

```text
trait Clock {
    fn now(self) -> Instant
}
```

---

## 474.83 — SystemClock

Production implementation.

---

## 474.84 — VirtualClock

Testing/simulation implementation.

---

# 474.85 — AI metadata

446 expose:

```text
clock source
clock type
deadline
timeout
timer
virtual/real time
timezone
timestamp unit
```

---

## 474.86 — Explain timeout

AI tooling có thể query:

```text
why did operation timeout?
```

và phân biệt:

```text
deadline exceeded
scheduler delay
IO delay
network delay
clock source
cancellation
```

---

# 474.87 — Security

Time-dependent security operations không được dùng wall-clock nếu cần chống clock manipulation.

---

## 474.88 — Expiration

Token/session expiration có thể cần wall-clock semantics.

Security-sensitive expiration phải document clock source và skew policy.

---

# 474.89 — Testing

Test:

```text
duration arithmetic
overflow
clock monotonicity
timezone
DST
timestamp conversion
timer cancellation
timer races
periodic scheduling
virtual time
```

---

## 474.90 — Fuzzing

Fuzz:

```text date parsing
duration parsing
timezone conversion
timestamp ranges
timer sequences
```

---

# 474.91 — Hard invariants

1. `Instant` khác `Duration`.
2. `Instant` khác `DateTime`.
3. `Duration` khác `Timeout`.
4. `Deadline` khác `Timeout`.
5. `Timer` khác `Deadline`.
6. `FrameTime` khác general-purpose time.
7. Elapsed time dùng monotonic clock.
8. Wall clock không dùng để benchmark elapsed time.
9. Wall clock có thể thay đổi.
10. Monotonic clock không phụ thuộc user clock adjustment.
11. Clock resolution khác accuracy.
12. Clock precision khác accuracy.
13. Accuracy không được ngầm đảm bảo.
14. UTC là global civil-time representation.
15. Local time cần timezone/offset context.
16. Date không chứa time-of-day.
17. TimeOfDay không chứa timezone mặc định.
18. Zoned time khác local datetime.
19. Timezone database là data/platform dependency.
20. DST gap phải được xử lý.
21. DST overlap phải được xử lý.
22. Ambiguous local time không được silently chọn nếu API yêu cầu exactness.
23. Timestamp unit phải explicit.
24. Timestamp khác semantic Instant.
25. Timestamp conversion kiểm tra overflow.
26. Deadline biểu diễn một point trên timeline.
27. Timeout biểu diễn duration.
28. Deadline có thể được propagate.
29. Timeout không được cộng dồn ngầm.
30. One-shot timer được hỗ trợ.
31. Periodic timer được hỗ trợ.
32. Fixed-rate khác fixed-delay.
33. Timer cancellation có semantics rõ ràng.
34. Cancellation race có semantics.
35. Timer lifetime có ownership.
36. Drop timer có documented behavior.
37. Sleep không đảm bảo exact wake time.
38. Yield không đảm bảo scheduler handoff.
39. Busy wait là explicit.
40. Timer backend là platform abstraction.
41. Timer coalescing không được coi là bug nếu platform policy cho phép.
42. High-resolution timer là capability.
43. Scheduler dùng monotonic deadlines.
44. Async timeout dùng monotonic time.
45. Timeout failure dùng Result/error semantics.
46. Reactive timing dùng explicit clock.
47. Virtual clock được hỗ trợ.
48. Deterministic timer test không phụ thuộc wall clock.
49. Equal-deadline ordering phải document.
50. Media clock khác system clock.
51. Audio clock có thể làm master clock.
52. Clock drift được mô hình hóa.
53. PTS/timebase explicit trong media.
54. Remote machine clocks không cùng một monotonic timeline.
55. Network synchronization là separate facility.
56. Filesystem timestamp precision được preserve khi có thể.
57. Database timestamp semantics phải document.
58. Raw monotonic values không dùng làm portable persistent timestamps.
59. Monotonic clock có thể reset sau reboot.
60. CPU cycles không phải portable Instant.
61. Performance counter thuộc performance layer.
62. Realtime timer precision khác realtime scheduling guarantee.
63. Realtime timer implementation có fixed-capacity option.
64. Mobile suspension không vi phạm timer semantics.
65. WASM timer throttling là platform behavior.
66. Clock injection được hỗ trợ.
67. VirtualClock phục vụ simulation/testing.
68. Time formatting tách khỏi time semantics.
69. Time parsing có typed result.
70. Leap-second policy phải document.
71. Security expiration clock source phải explicit.
72. Clock skew policy phải explicit khi cần.
73. AI có thể query clock source.
74. AI có thể query timeout cause.
75. Time subsystem có fuzz tests.
76. Time arithmetic có overflow tests.
77. Time subsystem không yêu cầu GUI.
78. Time subsystem không yêu cầu network.
79. Time subsystem không yêu cầu database.
80. Time subsystem không yêu cầu GC.
81. Time subsystem không tạo hidden threads.
82. **Axiom time foundation phải cung cấp một temporal model chính xác và nhất quán từ low-level monotonic timing đến civil time, scheduler deadlines, media clocks và deterministic virtual time, đồng thời ngăn việc dùng sai loại thời gian trong các ngữ cảnh khác nhau.**

**BOOTSTRAP-474 hoàn tất.**

---

# BOOTSTRAP-475 — LOGGING, TRACING, METRICS, TELEMETRY & OBSERVABILITY FOUNDATION

475 xây dựng observability foundation cho compiler, runtime và application nhưng **không biến logging thành hidden runtime behavior**.

Kiến trúc:

```text
Application / Compiler / Runtime
              │
      ┌───────┼────────┐
      ↓       ↓        ↓
    Logs    Traces   Metrics
      │       │        │
      └───────┼────────┘
              ↓
       Observability API
              │
       ┌──────┴───────┐
       ↓              ↓
   Local Output    External Sink
```

Các khái niệm phải tách:

```text
Log
  = event-oriented diagnostic record

Trace
  = distributed execution history

Span
  = timed operation inside trace

Metric
  = aggregated measurement

Profile
  = execution/resource sampling

Diagnostic
  = actionable compiler/runtime information
```

### 475 sẽ khóa:

- structured logging;
- log levels;
- categories/targets;
- fields;
- timestamps;
- source location;
- process/thread/task/actor IDs;
- trace/span IDs;
- correlation;
- context propagation;
- metrics counters/gauges/histograms;
- high-resolution timers;
- sampling;
- aggregation;
- exporters;
- console/file/network sinks;
- buffering;
- async logging;
- synchronous logging;
- backpressure;
- dropped-record semantics;
- realtime logging restrictions;
- zero-allocation logging path;
- sensitive data/redaction;
- secret handling;
- privacy;
- PII classification;
- sampling policies;
- tracing across async/task/actor boundaries;
- distributed trace propagation;
- network request correlation;
- storage/database operation correlation;
- GUI/media/GPU events;
- compiler build tracing;
- performance instrumentation 450;
- crash/panic integration 440/425;
- configurable observability policy 470;
- deterministic test sink;
- in-memory sink;
- replay;
- observability overhead measurement;
- compile-time disabled logging;
- dead-code elimination;
- binary-size impact;
- AI-readable logs/traces/metrics;
- explain performance regressions;
- no hidden telemetry;
- no automatic external upload;
- no mandatory telemetry service;
- no hidden network connection;
- no hidden background thread.

Nguyên tắc quan trọng:

```text
Observability Enabled
        ≠
Network Telemetry Enabled
```

và:

```text
Logging
   ≠
Tracing
   ≠
Metrics
   ≠
Profiling
```

Axiom phải cho phép một executable production cực nhỏ với observability gần như bằng zero khi disabled, nhưng khi bật instrumentation thì compiler/runtime có đủ metadata để truy ra:

```text
source
→ function
→ task
→ thread
→ actor
→ IO
→ GPU
→ media
→ resource
→ allocation
→ latency
```

mà không cần sửa đổi semantics của chương trình.