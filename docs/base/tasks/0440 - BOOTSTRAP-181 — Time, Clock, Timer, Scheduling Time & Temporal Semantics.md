# BOOTSTRAP-181 — Time, Clock, Timer, Scheduling Time & Temporal Semantics
**FROZEN / COMPLETED**

Đây là một phần tưởng nhỏ nhưng cực kỳ quan trọng với systems language. Axiom phải phân biệt rõ:

> **Thời điểm tuyệt đối ≠ khoảng thời gian ≠ thời gian đơn điệu ≠ lịch dân sự ≠ deadline ≠ timer.**

Nếu không tách chúng, rất dễ tạo bug trong timeout, scheduler, networking, distributed systems và logging.

---

## 181.1. Bốn khái niệm thời gian nền tảng

Axiom Core/Std phân biệt:

```text
Instant
Duration
WallClock
MonotonicClock
```

Trong đó:

```text
Instant
    = một thời điểm trên một timeline cụ thể

Duration
    = khoảng thời gian

WallClock
    = thời gian dân sự / hệ thống

MonotonicClock
    = đồng hồ chỉ dùng để đo khoảng cách thời gian
```

---

# 181.2. `Duration`

`Duration` biểu diễn:

```text
5 ns
10 us
20 ms
1 s
3 min
```

Không phải timestamp.

Ví dụ:

```ax
let timeout = 5.seconds;
```

---

## 181.3. Duration không phụ thuộc epoch

Không được coi:

```text
Duration(100)
```

là một timestamp.

Duration chỉ có ý nghĩa:

```text
elapsed time
delay
timeout
period
```

---

# 181.4. Độ phân giải

Duration semantic không nhất thiết bằng precision phần cứng.

Ví dụ:

```text
Duration = 1 ns
```

không có nghĩa OS có thể thực hiện timer chính xác 1 ns.

Do đó:

> **Representable precision ≠ observable clock precision ≠ scheduling precision.**

---

# 181.5. Overflow của Duration

Arithmetic phải được định nghĩa rõ:

```text
checked_add
wrapping_add
saturating_add
```

Không có signed-integer UB.

---

# 181.6. `Instant`

`Instant` là thời điểm trên một **monotonic timeline**.

Ví dụ:

```ax
let start = clock.now();
work();
let elapsed = clock.now() - start;
```

Đây là phép đo đúng.

---

# 181.7. Không dùng Wall Clock để đo elapsed time

Không nên:

```ax
let start = system_time();
work();
let elapsed = system_time() - start;
```

vì system clock có thể bị điều chỉnh.

Ví dụ:

```text
14:00:00
    ↓
NTP adjustment
    ↓
13:59:58
```

Elapsed time có thể trở nên âm hoặc sai.

---

# 181.8. Monotonic clock

Monotonic clock phải thỏa:

```text
t2 >= t1
```

theo timeline quan sát được của cùng clock.

Nó có thể không tương ứng trực tiếp với thời gian dân sự.

---

# 181.9. Wall Clock

Wall clock biểu diễn thời gian hệ thống/dân sự.

Ví dụ:

```text
2026-09-20 14:30:15 +07:00
```

Nó có thể:

- được chỉnh bởi NTP
- thay đổi timezone
- thay đổi DST
- nhảy tiến/lùi
- bị thay đổi thủ công

Do đó không dùng nó cho timeout chính xác.

---

# 181.10. `SystemTime`

Nên có abstraction kiểu:

```text
SystemTime
```

cho timestamp dân sự/OS.

Không để `Instant` và `SystemTime` là cùng một type.

---

# 181.11. Không implicit convert

Không cho:

```text
SystemTime → Instant
```

hoặc:

```text
Instant → SystemTime
```

một cách implicit.

Chuyển đổi cần clock/reference context.

---

# 181.12. Epoch

System timestamp thường dựa trên epoch.

Axiom có thể hỗ trợ:

```text
Unix epoch
```

ở platform/library layer.

Nhưng epoch không phải semantics duy nhất của `Instant`.

---

# 181.13. `DateTime`

`DateTime` là representation của civil time:

```text
year
month
day
hour
minute
second
subsecond
timezone/offset
```

Nó không phải monotonic instant.

---

# 181.14. Time zone

Time zone là dữ liệu/chính sách:

```text
UTC
Asia/Ho_Chi_Minh
America/New_York
...
```

Không nhúng timezone vào Core primitive.

---

# 181.15. UTC

UTC là một reference time scale quan trọng cho system/network APIs.

Axiom nên cung cấp:

```text
UtcDateTime
```

hoặc equivalent semantic type trong standard library.

---

# 181.16. Local time

Local civil time:

```text
LocalDateTime
```

không nhất thiết xác định được một instant duy nhất.

Ví dụ khi DST chuyển giờ:

```text
02:30
```

có thể:

- không tồn tại
- xuất hiện hai lần

Do đó conversion phải có policy.

---

# 181.17. Ambiguous local time

API nên trả:

```text
Result<Instant, TimeError>
```

hoặc một explicit resolution policy.

Không âm thầm chọn một instant.

---

# 181.18. Leap seconds

Axiom không nên để mỗi backend tự quyết semantics.

Time library phải có policy rõ ràng về:

```text
UTC leap seconds
smearing
POSIX-like time
TAI-like representations
```

Các profile khác nhau có thể tồn tại.

---

# 181.19. Core không cần calendar

Calendar:

```text
Gregorian
ISO week date
lunar calendar
locale calendar
```

là library/domain layer.

Core chỉ cần primitive temporal semantics tối thiểu.

---

# 181.20. Clock trait

Có thể thiết kế:

```ax
trait Clock {
    type Instant;

    fn now(self: view<Self>) -> Self::Instant;
}
```

nhưng `Clock` không nên là một global singleton bắt buộc.

---

# 181.21. Monotonic clock

Ví dụ:

```ax
let clock = MonotonicClock.system();
let start = clock.now();

work();

let elapsed = clock.now().elapsed_since(start);
```

---

# 181.22. System clock

```ax
let now = SystemClock.utc_now();
```

phục vụ:

```text
logging
timestamps
files
protocols
calendar
user-visible dates
```

---

# 181.23. Clock capability

Clock access có thể được coi là capability.

Điều này rất hữu ích cho test:

```text
Production
    → RealClock

Test
    → FakeClock
```

---

# 181.24. Không hidden global clock

Axiom không nên để:

```ax
now()
```

ngầm gọi global state trong mọi context nếu điều đó phá deterministic testing.

Standard library có thể cung cấp convenience API, nhưng semantic dependency vẫn phải có thể truy vấn.

---

# 181.25. Comptime time

Comptime time không mặc định được phép.

Nếu muốn:

```text
comptime → current time
```

phải dùng capability:

```text
Time
```

và kết quả phải tham gia build identity/cache như các external inputs khác.

---

# 181.26. Reproducible build

Build reproducible không được phụ thuộc vô tình vào:

```text
current time
timezone
random clock
environment clock
```

Nếu comptime dùng chúng, build identity phải ghi nhận dependency.

---

# 181.27. `sleep`

```ax
sleep(100.ms);
```

là blocking operation.

Không nhất thiết tạo một thread mới.

---

# 181.28. Async sleep

```ax
sleep_async(100.ms).await;
```

là suspension.

Executor có thể sử dụng:

```text
OS timer
timer wheel
heap
kernel event
```

mà không block thread.

---

# 181.29. Sleep semantics

`Sleep(duration)` nên có nghĩa:

> Không tiếp tục thực thi trước khi khoảng thời gian tối thiểu được đáp ứng.

Không guarantee:

```text
exactly duration
```

vì scheduler có thể chạy muộn.

---

# 181.30. Timer

Timer là resource/event abstraction:

```text
Timer
```

có thể:

```text
arm
cancel
reset
wait
```

---

# 181.31. Deadline

`Deadline` là:

```text
Instant + semantic clock domain
```

Ví dụ:

```ax
let deadline = clock.now() + 5.seconds;
```

---

# 181.32. Timeout

Timeout là policy:

```text
operation must complete before deadline
```

Không nên coi `Timeout` đơn giản là `Duration`.

---

# 181.33. Duration vs Deadline

Đây là distinction rất quan trọng:

```text
Duration:
    "5 seconds"

Deadline:
    "before this specific monotonic instant"
```

---

# 181.34. Vì sao deadline tốt hơn duration?

Nếu có nhiều tầng:

```text
HTTP
 └── TLS
      └── DNS
           └── socket
```

Nếu mỗi tầng nhận:

```text
5 seconds
```

có thể tổng cộng thành:

```text
20 seconds
```

Nếu truyền:

```text
Deadline
```

mỗi tầng biết còn bao nhiêu thời gian.

---

# 181.35. Deadline propagation

Ví dụ:

```ax
fn request(deadline: Deadline) -> Result<Response, Error>
```

bên trong:

```ax
dns.resolve(deadline)?;
connect(deadline)?;
send(deadline)?;
receive(deadline)?;
```

---

# 181.36. Remaining duration

```ax
let remaining = deadline.remaining(clock.now());
```

Có thể trả:

```text
Duration
```

hoặc `Expired`.

---

# 181.37. Expired deadline

Nếu:

```text
now >= deadline
```

deadline expired.

Không dùng floating-point comparison cho temporal semantics.

---

# 181.38. Timeout không cancel operation tự động

Đây là invariant rất quan trọng.

```ax
timeout(operation, 5.seconds)
```

không mặc định có nghĩa:

```text
operation bị kill
```

Nó chỉ có thể nghĩa:

```text
caller stops waiting
```

---

# 181.39. Timeout + cancellation

Muốn thực sự cancel:

```text
CancellationToken
+
Deadline
```

Ví dụ:

```ax
operation(deadline, cancellation)
```

---

# 181.40. I/O timeout

Socket operation có thể hỗ trợ:

```text
read_until(deadline)
write_until(deadline)
connect_until(deadline)
```

tránh mỗi API tự phát minh timeout semantics.

---

# 181.41. Timer cancellation

Timer cancellation phải có race semantics rõ ràng.

Nếu:

```text
cancel(timer)
```

đồng thời timer đã fire:

thì API phải phân biệt:

```text
Cancelled
Fired
AlreadyCompleted
```

không được giả định cancellation luôn thắng.

---

# 181.42. Timer event ownership

Timer event có thể trả:

```text
TimerEvent
```

và event phải có lifetime/ownership rõ ràng.

---

# 181.43. Repeating timer

Có:

```text
PeriodicTimer
```

nhưng phải định nghĩa:

```text
fixed-rate
```

hay:

```text
fixed-delay
```

---

# 181.44. Fixed-rate timer

Ví dụ:

```text
T0
T0 + P
T0 + 2P
T0 + 3P
```

Nếu task chạy chậm, ticks có thể bị trễ.

---

# 181.45. Fixed-delay timer

```text
execute
  ↓
wait P
  ↓
execute
```

Khoảng cách phụ thuộc execution time.

Hai semantics không được nhập làm một.

---

# 181.46. Missed ticks

Periodic timer phải có policy:

```text
skip
coalesce
catch-up
queue-all
```

Không nên để backend tự quyết.

---

# 181.47. Scheduler clock

Scheduler có thể dùng:

```text
MonotonicClock
```

cho:

```text
sleep
deadline
timeout
retry
backoff
```

không dùng wall clock.

---

# 181.48. Retry/backoff

Ví dụ:

```text
retry
  ├── attempt
  ├── wait Duration
  └── deadline
```

Randomized jitter là:

```text
Random effect
```

không phải clock semantics.

---

# 181.49. Backoff deadline

Nếu:

```text
deadline = T
```

thì:

```text
sleep(backoff)
```

phải clamp theo remaining time.

---

# 181.50. Scheduler fairness và time

Clock không guarantee scheduler fairness.

Ví dụ:

```text
sleep(0)
```

không đảm bảo:

```text
yield exactly once
```

Nó chỉ là scheduler hint/policy nếu API được định nghĩa như vậy.

---

# 181.51. `yield`

`yield()` khác `sleep()`.

```text
yield()
```

= relinquish execution opportunity.

```text
sleep(d)
```

= không runnable trong một khoảng thời gian tối thiểu.

---

# 181.52. Yield không phải memory fence

```text
yield()
```

không tạo:

```text
Acquire
Release
SeqCst
```

memory ordering.

---

# 181.53. Clock read không phải synchronization

```text
clock.now()
```

không tạo happens-before.

Đây là invariant quan trọng.

---

# 181.54. Time và concurrency

Ví dụ:

```ax
if clock.now() > deadline {
    ...
}
```

không đồng nghĩa dữ liệu được synchronized.

Time observation và memory synchronization là hai khái niệm độc lập.

---

# 181.55. Virtual clock

Testing cần:

```text
VirtualClock
```

có thể:

```text
advance(1.second)
```

mà không phải chờ real time.

---

# 181.56. Deterministic scheduler

Kết hợp:

```text
VirtualClock
+
DeterministicExecutor
```

cho phép test:

```text
timeouts
races
retry
deadlines
periodic tasks
```

nhanh và reproducible.

---

# 181.57. Virtual time không thay đổi semantics

Program sử dụng abstraction:

```text
Clock
```

không nên biết clock là:

```text
real
virtual
mock
```

trừ khi explicit API yêu cầu.

---

# 181.58. Time source injection

Một function có thể nhận:

```ax
fn retry(clock: view<Clock>, ...)
```

hoặc library có generic clock parameter.

Compiler có thể specialize bỏ abstraction.

---

# 181.59. Zero-cost clock abstraction

Nếu:

```ax
fn foo<C: Clock>(clock: view<C>)
```

và `C` là concrete:

compiler có thể:

```text
inline
devirtualize
constant-fold
```

mà không có runtime interface cost.

---

# 181.60. Dynamic clock

Nếu cần plugin:

```text
dyn Clock
```

thì dynamic dispatch explicit.

---

# 181.61. CPU cycle counter

System layer có thể expose:

```text
CycleCounter
```

nhưng không được giả định:

```text
cycles == nanoseconds
```

---

# 181.62. Performance counter

Hardware performance counters là:

```text
profiling/system capability
```

không phải clock semantic.

---

# 181.63. CPU timestamp counter

TSC có:

```text
core synchronization
frequency scaling
virtualization
serialization
```

nên API phải biểu diễn đúng limitations.

Không đưa TSC trực tiếp vào `Instant` semantics nếu backend chưa establish contract.

---

# 181.64. Clock quality

Clock metadata có thể mô tả:

```text
resolution
monotonicity
adjustability
source
uncertainty
```

Ví dụ:

```text
MonotonicClock
    monotonic = true
    adjustable = false
```

---

# 181.65. Clock adjustment

System clock có thể:

```text
step
slew
smear
```

Axiom không được assume nó luôn tăng đều.

---

# 181.66. Distributed systems

Hai machine:

```text
Machine A: Instant A
Machine B: Instant B
```

không thể assume:

```text
A.now() == B.now()
```

hoặc ordering tuyệt đối.

---

# 181.67. Distributed ordering

Nếu cần ordering giữa machines:

```text
logical clock
Lamport clock
vector clock
hybrid logical clock
```

là library/distributed-system abstractions.

Không trộn vào `Instant`.

---

# 181.68. Timestamp ≠ ordering proof

Timestamp:

```text
2026-09-20T10:00
```

không tự chứng minh event A xảy ra trước event B trong distributed system.

---

# 181.69. Logical clock

Có thể:

```text
LogicalTime
```

với operations:

```text
tick()
merge()
happens_before()
```

Đây là domain khác với physical clock.

---

# 181.70. Hybrid clocks

Distributed library có thể cung cấp:

```text
HybridTimestamp
```

kết hợp physical + logical time.

---

# 181.71. Time serialization

Wire protocol phải xác định:

```text
epoch
unit
endianness
precision
timezone
encoding
```

Không serialize raw memory representation của `DateTime` một cách mặc định.

---

# 181.72. Duration serialization

Protocol có thể dùng:

```text
integer nanoseconds
integer microseconds
fractional seconds
```

nhưng phải explicit.

---

# 181.73. File timestamps

Filesystem timestamps thuộc OS/platform semantics.

Có thể có:

```text
created
modified
accessed
changed
birth
```

không phải mọi platform đều cung cấp tất cả.

API nên biểu diễn capability/availability rõ ràng.

---

# 181.74. Timestamp precision

File timestamp:

```text
nanosecond
```

không có nghĩa filesystem thực sự quan sát được nanosecond.

Precision phải là metadata/contract.

---

# 181.75. Time zone database

TZ database:

```text
IANA tzdata
```

là external data dependency.

Version của timezone database có thể ảnh hưởng kết quả conversion.

---

# 181.76. Reproducible datetime

Nếu build tool format:

```text
local date/time
```

thì timezone/tzdata phải nằm trong build environment identity nếu kết quả ảnh hưởng artifact.

---

# 181.77. Formatting

Formatting:

```ax
format_datetime(time)
```

không nên mặc định dùng global locale/timezone.

Policy nên explicit.

---

# 181.78. Locale và time zone khác nhau

```text
Locale
    → formatting/language

TimeZone
    → temporal offset/rules
```

Không nhập thành một object duy nhất.

---

# 181.79. Calendar arithmetic

Không được coi:

```text
1 month == 30 days
```

Calendar arithmetic:

```text
add_months()
add_years()
```

khác Duration arithmetic.

---

# 181.80. Duration arithmetic vs calendar arithmetic

```text
Instant + 24.hours
```

khác:

```text
LocalDateTime + 1.day
```

trong các timezone có DST.

---

# 181.81. Date arithmetic

Calendar library phải định nghĩa policy khi:

```text
Jan 31 + 1 month
```

có thể thành:

```text
Feb 28
Feb 29
error
clamp
```

Không implicit.

---

# 181.82. Monotonic deadline representation

Internally:

```text
Deadline
{
    clock_domain
    instant
}
```

để không vô tình so sánh các clock khác nhau.

---

# 181.83. Không subtract khác clock domain

Không cho:

```text
Instant<MonotonicA>
-
Instant<SystemClock>
```

---

# 181.84. Generic clock domain

Có thể mô hình:

```text
Instant<C>
Duration
Deadline<C>
```

với:

```text
C = MonotonicClock
C = VirtualClock
```

Compiler generic system xử lý.

---

# 181.85. Clock conversion

Chuyển:

```text
MonotonicInstant
→ SystemTime
```

không luôn có semantic meaning cố định.

Nếu OS cung cấp correlation:

```text
ClockCorrelation
```

thì library mới cho phép.

---

# 181.86. Clock correlation

Có thể có:

```text
correlation {
    monotonic_anchor
    wall_clock_anchor
    uncertainty
}
```

để logging/telemetry.

---

# 181.87. Logging

Log entry có thể chứa:

```text
wall_time
monotonic_time
thread_id
task_id
```

vì chúng trả lời các câu hỏi khác nhau.

---

# 181.88. Tracing

Distributed tracing nên dùng:

```text
trace_id
span_id
monotonic duration
wall timestamp
```

tùy mục đích.

---

# 181.89. Timeouts trong async

`.await` không tự tạo timeout.

Phải explicit:

```ax
timeout(operation(), deadline)
```

hoặc:

```ax
operation(deadline).await
```

---

# 181.90. Timeout wrapper

Một timeout wrapper phải định nghĩa rõ:

```text
timeout expires
↓
caller receives Timeout
↓
underlying operation:
    cancelled?
    detached?
    continues?
```

Không được để implicit.

---

# 181.91. Cancellation + timeout

Thiết kế khuyến nghị:

```text
Deadline
+
CancellationToken
```

là hai inputs khác nhau.

Deadline:

```text
when
```

Cancellation:

```text
whether
```

---

# 181.92. Async I/O

In-flight I/O phải giữ storage capability đến completion/cancellation theo contract.

Ví dụ:

```text
buffer
  ↓
async_read
  ↓
Future
```

buffer không được bị Drop/relocate quá sớm.

Verifier đã có khả năng kiểm tra điều này.

---

# 181.93. GPU events

GPU event cũng có temporal semantics:

```text
launch
   ↓
GpuEvent
   ↓
wait
```

`GpuEvent` completion không đồng nghĩa CPU clock timestamp chính xác.

---

# 181.94. GPU timing

GPU timestamp:

```text
device timeline
```

khác:

```text
host monotonic timeline
```

Correlation phải explicit.

---

# 181.95. Timer + GPU

Có thể:

```text
CPU deadline
GPU event
```

nhưng không tự coi chúng là cùng clock domain.

---

# 181.96. Interrupt timing

Interrupt timestamp có thể dùng:

```text
monotonic counter
hardware counter
```

tùy target.

Không giả định mọi interrupt có `SystemTime`.

---

# 181.97. Real-time semantics

Nếu profile yêu cầu real-time:

```text
deadline
period
jitter
WCET
```

có thể trở thành analyzable metadata.

---

# 181.98. WCET

Worst-case execution time không thể tự suy ra chính xác cho mọi program.

Nếu cần:

```text
@wcet(...)
```

chỉ là contract/tooling input, không phải compiler tự đảm bảo nếu không có proof.

---

# 181.99. Temporal effects

Effect system có thể phân biệt:

```text
Time
Random
Environment
```

nếu cần finer-grained effect classes.

`clock.now()` là observable external state.

---

# 181.100. Time and optimization

Compiler không được:

```text
cache now()
```

qua một observable clock boundary nếu function semantics yêu cầu mỗi call quan sát clock.

---

# 181.101. Pure function

Một function:

```ax
fn add(a: i32, b: i32) -> i32
```

không có Time effect.

Nhưng:

```ax
fn now() -> SystemTime
```

có external/time effect.

---

# 181.102. Constant folding

```ax
const x = 2 + 3;
```

được compile-time.

Nhưng:

```ax
comptime x = current_time();
```

chỉ hợp lệ nếu Time capability được cấp.

---

# 181.103. Test isolation

Test framework nên có:

```text
RealClock
VirtualClock
FrozenClock
```

để kiểm tra temporal logic.

---

# 181.104. Frozen clock

`FrozenClock`:

```text
now() = constant
```

hữu ích cho deterministic unit tests.

---

# 181.105. Advancing clock

```ax
clock.advance(1.second);
```

chỉ hợp lệ với controllable clock.

---

# 181.106. Timer testing

Virtual executor:

```text
spawn(task)
clock.advance(10.ms)
executor.run_ready()
```

cho phép test async mà không sleep thật.

---

# 181.107. No busy waiting by default

API:

```text
sleep
wait
timer
condition
```

nên ưu tiên OS/runtime waiting.

Busy spin chỉ explicit:

```text
spin_wait()
```

hoặc low-level API.

---

# 181.108. Spin waiting

Spin wait có thể phù hợp:

```text
short critical latency
lock-free structures
real-time
```

nhưng compiler/runtime không tự thay blocking wait bằng spin.

---

# 181.109. CPU pause

Low-level:

```text
cpu_relax()
```

là architecture/system intrinsic.

Không phải time primitive.

---

# 181.110. Temporal memory ordering

Không có:

```text
sleep(1ms)
```

đảm bảo memory visibility.

Phải dùng:

```text
Atomic
Mutex
Channel
Join
```

để establish ordering.

---

# 181.111. Classic anti-pattern

Không coi:

```text
write_data();
sleep(10.ms);
read_data();
```

là synchronization.

Đây là **không hợp lệ về mặt thiết kế concurrency** nếu không có synchronization primitive.

---

# 181.112. Temporal API hierarchy

Kiến trúc nên là:

```text
std::time
├── Duration
├── Instant
├── Deadline
├── Timer
├── MonotonicClock
├── SystemClock
├── Date
├── DateTime
├── TimeZone
└── Calendar
```

---

# 181.113. Core vs std

Core chỉ cần semantic primitives cần thiết cho compiler/runtime:

```text
Duration
clock abstraction concepts
```

Phần lớn:

```text
Date
Calendar
Timezone
Formatting
Timer
VirtualClock
```

nằm ở standard library/runtime.

---

# 181.114. Runtime components

Time runtime component có thể là:

```text
TIME
TIMER
```

nhưng không bắt buộc.

Program freestanding có thể cung cấp clock backend riêng.

---

# 181.115. No mandatory OS clock

Embedded target có thể map:

```text
MonotonicClock
```

vào:

```text
hardware counter
```

hoặc không cung cấp nếu platform không hỗ trợ.

---

# 181.116. Capability error

Nếu program yêu cầu:

```text
SystemClock
```

trên target không có clock:

đó là compile/link/configuration error rõ ràng, không phải undefined behavior.

---

# 181.117. Time precision declaration

Target có thể expose:

```text
ClockInfo {
    resolution
    monotonic
    adjustable
}
```

để application/tooling biết giới hạn.

---

# 181.118. Monotonicity contract

Nếu một clock được khai báo monotonic:

compiler/runtime backend phải tôn trọng contract.

Không được silently map nó vào một source có thể lùi.

---

# 181.119. Virtualization

VM/container có thể thay đổi clock behavior.

Axiom semantics phải dựa trên clock contract, không dựa vào assumption rằng host hardware là bare metal.

---

# 181.120. Container time

Container có thể:

```text
share host clock
```

hoặc có virtualization.

Đây là platform behavior.

---

# 181.121. Time source failure

Clock read có thể fail trên một số embedded/device platforms.

API có thể:

```text
Result<Instant, ClockError>
```

nếu platform contract yêu cầu.

Hosted normal clock có thể có infallible wrapper.

---

# 181.122. Timer resource failure

Timer creation có thể fail:

```text
Timer::new(...)
    -> Result<Timer, TimerError>
```

tùy backend/resource limits.

---

# 181.123. No exception

Temporal errors vẫn dùng:

```text
Result
Option
panic
```

không dùng exception.

---

# 181.124. Temporal resource Drop

Timer Drop:

```text
cancel/disarm
```

nếu abstraction contract nói vậy.

Nhưng `Drop` không được âm thầm:

```text
kill unrelated task
```

---

# 181.125. Timer handle identity

Nếu timer có observable identity:

```text
TimerId
```

logical identity.

Không phụ thuộc memory address.

---

# 181.126. Temporal capability

Một `Deadline` có thể được coi là immutable value.

Một `Timer` là resource capability.

Đừng nhập hai khái niệm.

---

# 181.127. Temporal abstraction zero-cost

Nếu deadline:

```ax
let deadline = start + 5.seconds;
```

compiler có thể biểu diễn đơn giản bằng integer tick count.

Không bắt buộc heap/object/runtime.

---

# 181.128. Generic temporal code

```ax
fn wait<C: Clock>(
    clock: view<C>,
    deadline: Deadline<C>
) -> Result<(), Timeout>
```

có thể được specialize thành direct platform calls.

---

# 181.129. Time arithmetic

Các phép toán hợp lệ:

```text
Instant + Duration → Instant
Instant - Duration → Instant
Instant - Instant → Duration
```

nhưng:

```text
Instant + Instant
```

không hợp lệ.

---

# 181.130. Deadline arithmetic

```text
Deadline + Duration → Deadline
Deadline - Deadline → Duration
```

chỉ trong cùng clock domain.

---

# 181.131. Duration comparison

Duration có thể:

```text
< > <= >= == !=
```

vì cùng semantic dimension.

---

# 181.132. Unit-safe durations

Nên cho phép:

```ax
1.ns
1.us
1.ms
1.s
1.min
1.h
```

và compiler normalize thành Duration.

Không để:

```text
sleep(1)
```

có unit mơ hồ.

---

# 181.133. Numeric conversion

```text
Duration → integer
```

phải explicit:

```text
as_nanos()
as_micros()
```

vì có thể overflow/truncate.

---

# 181.134. Floating durations

Không khuyến khích:

```text
Duration(0.1)
```

bằng float trong Core.

Duration nên có representation chính xác phù hợp.

---

# 181.135. Saturation

Khi chuyển:

```text
Duration → u64 nanoseconds
```

có thể cung cấp:

```text
checked
saturating
wrapping
```

giống numeric model.

---

# 181.136. Temporal dimension safety

Compiler nên ngăn:

```text
Distance + Duration
```

nếu các types khác nhau.

Không cần một “dimension type system” khổng lồ trong Core; library newtypes là đủ.

---

# 181.137. Date formatting

Formatting policy:

```text
locale
timezone
calendar
format
```

phải explicit hoặc đến từ một context object rõ ràng.

---

# 181.138. Time parsing

Parsing datetime:

```text
String → Result<DateTime, ParseError>
```

không tự assume timezone nếu input thiếu.

---

# 181.139. Missing timezone

Input:

```text
2026-09-20 12:00
```

là local/unspecified time, không tự biến thành UTC.

---

# 181.140. Timezone conversion

```text
Instant
    ↓
TimeZone
    ↓
LocalDateTime
```

là deterministic nếu timezone database version đã xác định.

---

# 181.141. DST ambiguity

API phải expose:

```text
Ambiguous
Invalid
Valid
```

hoặc policy rõ ràng.

---

# 181.142. Temporal metadata

`.axmeta` có thể chứa:

```text
ClockRequirements
TimerRequirements
TimeZoneDataDependency
TemporalEffects
```

khi cần.

---

# 181.143. AI inspection

Các API:

```text
axc inspect clocks foo
axc inspect timers foo
axc inspect deadlines foo
axc inspect blocking foo
axc inspect temporal-effects foo
```

---

# 181.144. Compiler diagnostic

Nếu code dùng wall clock cho API yêu cầu monotonic:

```text
E_CLOCK_DOMAIN_MISMATCH
```

Ví dụ:

```text
SystemTime cannot be used as a monotonic deadline.
Use MonotonicClock::now().
```

---

# 181.145. Clock-domain safety

Đây là một lợi ích rất lớn nếu compiler biết clock domain:

```text
Instant<Monotonic>
Instant<System>
Instant<Virtual>
```

Không thể vô tình trộn chúng.

---

# 181.146. Temporal contracts

Library có thể khai báo:

```text
requires MonotonicClock
requires Deadline<C>
```

và compiler kiểm tra qua type/trait system.

---

# 181.147. Async executor contract

Executor cần một clock:

```text
Executor<C>
```

để implement:

```text
sleep
deadline
timeout
timer
```

Nếu không có timer capability, executor vẫn có thể chạy Future không cần timer.

---

# 181.148. Runtime elimination

Một chương trình chỉ dùng:

```text
Instant
Duration
```

và platform clock trực tiếp có thể không cần full timer runtime.

---

# 181.149. Minimal runtime

Không dùng async:

```text
TIME
```

có thể vẫn cần nếu program gọi system clock.

Không gọi clock:

```text
TIME
```

có thể bị loại khỏi runtime.

---

# 181.150. Tổng hợp temporal model

```text
                         TIME
                          │
             ┌────────────┴────────────┐
             │                         │
       Monotonic Time              Civil Time
             │                         │
         Instant                    DateTime
             │                         │
       Duration/Deadline          TimeZone
             │                         │
       Timer / Timeout             Calendar
             │
        Scheduler / Async
```

---

# 181.151. Nguyên tắc vàng

Axiom khóa:

> **Use monotonic time to measure duration.**
>
> **Use wall/civil time to represent dates and timestamps.**
>
> **Use deadlines to propagate time budgets.**
>
> **Use cancellation to stop work.**
>
> **Use synchronization to order memory.**
>
> **Never use passage of time as a substitute for synchronization.**

Đây là một invariant cực kỳ đáng giữ.

---

# 181.152. Invariants

### Clock

- **ATIME-20** — `Duration` is distinct from `Instant`.
- **ATIME-21** — Monotonic time is distinct from civil/system time.
- **ATIME-22** — Monotonic clock values must not move backward within their contract.
- **ATIME-23** — Wall-clock adjustment does not invalidate monotonic-time semantics.
- **ATIME-24** — Clock domains are not implicitly interchangeable.
- **ATIME-25** — Clock reads do not establish memory synchronization.
- **ATIME-26** — Clock precision is distinct from representation precision.
- **ATIME-27** — Hardware timestamp counters are not automatically valid monotonic clocks.

### Duration / Deadline

- **ATIME-30** — `Instant - Instant` produces a `Duration` only within the same clock domain.
- **ATIME-31** — `Instant + Duration` preserves the clock domain.
- **ATIME-32** — `Deadline` represents a temporal boundary, not merely a duration.
- **ATIME-33** — Deadline propagation is preferred for nested timeout budgets.
- **ATIME-34** — Duration arithmetic has defined overflow semantics.
- **ATIME-35** — Temporal unit conversions are explicit where loss or overflow is possible.

### Timer / Scheduler

- **ATIMER-20** — Timer expiration does not imply exact scheduler execution time.
- **ATIMER-21** — Sleep specifies a minimum waiting interval, not exact wake time.
- **ATIMER-22** — `yield` is distinct from sleep.
- **ATIMER-23** — Yield/sleep do not establish memory ordering.
- **ATIMER-24** — Timer cancellation has defined race semantics.
- **ATIMER-25** — Periodic timers distinguish fixed-rate and fixed-delay behavior.
- **ATIMER-26** — Missed timer events follow an explicit policy.
- **ATIMER-27** — Async timers do not require one OS thread per timer.

### Timeout / Cancellation

- **ATIMEOUT-20** — Timeout and cancellation are distinct semantics.
- **ATIMEOUT-21** — Timeout does not implicitly kill an underlying operation.
- **ATIMEOUT-22** — Cancellation must use an explicit cancellation contract.
- **ATIMEOUT-23** — In-flight operations retain required storage/capabilities until completion or valid cancellation.
- **ATIMEOUT-24** — Deadline expiration is not itself a memory-synchronization event.

### Civil Time

- **ACIVILTIME-20** — Civil time is distinct from monotonic elapsed time.
- **ACIVILTIME-21** — Time-zone conversion is explicit.
- **ACIVILTIME-22** — Ambiguous/nonexistent local times cannot be silently resolved without policy.
- **ACIVILTIME-23** — Calendar arithmetic is distinct from duration arithmetic.
- **ACIVILTIME-24** — Time-zone database version may affect observable conversion results.
- **ACIVILTIME-25** — Serialization does not assume in-memory time representation.

### Testing / Reproducibility

- **ATIMETEST-20** — Clock dependencies can be replaced by deterministic clock implementations.
- **ATIMETEST-21** — Virtual time must not require real elapsed time.
- **ATIMETEST-22** — Deterministic executors may control virtual time.
- **ATIMETEST-23** — Comptime access to time is an explicit external capability.
- **ATIMETEST-24** — Time-dependent comptime inputs participate in build identity.

---

# BOOTSTRAP-181 hoàn tất

Bây giờ Axiom đã có một nền khá sạch cho:

```text
CPU
GPU
Thread
Task
Fiber
Async
IPC
Timer
Deadline
Cancellation
Ownership
Capability
Synchronization
```

và quan trọng nhất, chúng không chồng lấn semantics.

Kiến trúc hiện tại có thể tóm tắt:

```text
                    EXECUTION
                        │
          ┌─────────────┼─────────────┐
          │             │             │
       Process        Thread         GPU
          │             │
          │       ┌─────┴─────┐
          │      Fiber       Task
          │                    │
          │                  Future
          │                    │
          │                  Await
          │                    │
          └──────────┬─────────┘
                     │
                Synchronization
                     │
          ┌──────────┼──────────┐
        Mutex      Channel    Atomic
                     │
                 Ownership
                     │
                Capability
                     │
                   Time
                     │
       ┌─────────────┼─────────────┐
    Duration      Deadline      Clock
                                  │
                         ┌────────┴────────┐
                     Monotonic          Civil
```

### Task tiếp theo

**BOOTSTRAP-182 — Networking, Socket Model, Async I/O & Zero-Copy Network Stack**

Sẽ chốt phần còn thiếu rất lớn của systems language:

```text
Socket
TCP
UDP
Unix socket
IPv4/IPv6
DNS
TLS boundary
listen/accept/connect
async I/O
read/write buffers
scatter/gather I/O
zero-copy
sendfile/splice
io_uring
IOCP
epoll/kqueue
backpressure
network cancellation
connection ownership
socket capability
packet/raw socket
kernel/user buffer boundaries
```

Điểm đặc biệt của task 182 là phải thiết kế sao cho **cùng một API semantic** có thể hạ xuống Linux `io_uring/epoll`, Windows IOCP, macOS kqueue và embedded networking mà không biến Axiom thành một wrapper của riêng POSIX.