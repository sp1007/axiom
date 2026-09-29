# BOOTSTRAP-764 — AXTIME

**Title:** Native Time, Clock, Duration, Calendar, Time Zone, Timer & Temporal Runtime 5.0  
**Namespace:** `AXTIME`  
**Phase:** Axiom Civilization Runtime / Native Temporal Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXTIME` là temporal foundation của Axiom.

Nó chuẩn hóa:

- monotonic time;
- wall-clock time;
- calendar time;
- duration;
- deadline;
- timeout;
- timer;
- time zone;
- UTC;
- local time;
- date;
- calendar arithmetic;
- clock synchronization metadata;
- temporal formatting/parsing;
- recurring timers;
- virtual time;
- deterministic time trong simulation.

Mục tiêu lớn nhất:

> **Không để application nhầm thời điểm thực tế với khoảng thời gian đo được.**

---

# 2. Ba lớp thời gian bắt buộc

```text id="time3"
┌──────────────────────┐
│ MONOTONIC TIME       │
│ duration / timeout   │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│ WALL-CLOCK TIME      │
│ UTC / civil instant  │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│ CALENDAR / LOCAL     │
│ date / timezone      │
└──────────────────────┘
```

---

# 3. Monotonic time

Monotonic clock chỉ được dùng cho:

```text id="mono"
duration
timeout
deadline
benchmark
latency
scheduler timing
```

Không đại diện cho ngày tháng thực tế.

---

# 4. Wall-clock time

Wall clock biểu diễn:

```text id="wall"
Instant
```

có thể map tới:

```text UTC
```

Wall clock có thể jump do:

- NTP;
- administrator adjustment;
- virtualization;
- RTC correction.

Do đó không dùng trực tiếp để tính duration.

---

# 5. Calendar time

Calendar time biểu diễn:

```text id="calendar"
year
month
day
hour
minute
second
```

kết hợp timezone/calendar rules.

---

# 6. Instant

Canonical absolute temporal point:

```text id="instant"
instant {
    seconds
    subsecond
}
```

Baseline resolution:

```text nanosecond
```

nhưng platform precision có thể thấp hơn.

---

# 7. Duration

```text id="duration"
duration {
    signed_nanoseconds
}
```

Có thể biểu diễn:

```text id="durationexamples"
1ns
1us
1ms
1s
1m
1h
1d
```

Duration không có timezone.

---

# 8. Duration overflow

Arithmetic:

```text id="overflow"
duration + duration
```

phải phát hiện overflow.

Không wrap silently trong safe/default arithmetic.

---

# 9. Deadline

```text id="deadline"
deadline {
    clock_id
    timestamp
}
```

Deadline gắn với clock domain.

---

# 10. Timeout

Timeout là duration:

```text id="timeout"
5s
```

Deadline là temporal point:

```text id="deadline2"
now + 5s
```

Không đánh đồng hai khái niệm.

---

# 11. Clock abstraction

```text id="clock"
clock {
    clock_id
    kind
    resolution
    stability
    source
}
```

Kinds:

```text id="clocktypes"
MONOTONIC
WALL
VIRTUAL
CPU
PROCESS
THREAD
```

---

# 12. Clock capabilities

Platform có thể không hỗ trợ mọi clock.

API phải expose:

```text id="clockcaps"
resolution
precision
adjustability
monotonicity
suspend_behavior
```

---

# 13. Suspend behavior

Monotonic clocks có thể:

```text id="suspend"
include_suspend
exclude_suspend
```

Platform-specific.

Semantics phải explicit.

---

# 14. Sleep clock

Timer cần chỉ định clock:

```text id="sleepclock"
MONOTONIC
MONOTONIC_INCLUDE_SUSPEND
WALL
VIRTUAL
```

Không mặc định dựa vào wall clock cho timeout.

---

# 15. Current time API

```text id="nowapi"
time_now()
monotonic_now()
wall_now()
```

---

# 16. Clock read cost

Hot path:

```text id="clockfast"
monotonic_now()
```

phải được tối ưu bằng platform mechanism:

- vDSO;
- hardware counter;
- kernel fast path;
- mapped clock page;

nếu platform hỗ trợ.

Axiom không yêu cầu syscall cho mỗi clock read.

---

# 17. Clock calibration

Runtime có thể maintain:

```text id="calibration"
monotonic → wall-clock mapping
```

nhưng mapping không được giả định bất biến vô thời hạn.

---

# 18. Clock adjustment

Khi wall clock thay đổi:

```text id="adjust"
wall clock
   ↕
adjusted
```

monotonic clock vẫn tiếp tục tiến lên.

---

# 19. Leap seconds

Axiom phải có explicit policy.

Canonical internal `Instant` không nên phụ thuộc vào local civil representation.

Calendar conversion chịu trách nhiệm leap-second policy.

---

# 20. UTC

UTC là canonical global civil reference.

API:

```text id="utc"
instant_to_utc()
utc_now()
```

---

# 21. Local time

Local time:

```text id="local"
instant
 ↓
timezone
 ↓
civil_datetime
```

Không lưu local datetime như authoritative timestamp nếu timezone context bị mất.

---

# 22. Civil datetime

```text id="civil"
civil_datetime {
    year
    month
    day
    hour
    minute
    second
    nanosecond
}
```

Không có timezone intrinsic.

---

# 23. Zoned datetime

```text id="zoned"
zoned_datetime {
    instant
    timezone
    offset
    civil
}
```

---

# 24. Time zone

```text id="timezone"
timezone {
    zone_id
    database_version
}
```

Ví dụ:

```text id="tzexample"
Asia/Ho_Chi_Minh
UTC
America/New_York
Europe/London
```

---

# 25. Time zone database

Timezone rules là data, không phải hardcoded compiler logic.

Runtime có thể ship:

```text id="tzdb"
AXTZDB
```

với version rõ ràng.

---

# 26. Time zone versioning

Một conversion phải có khả năng xác định:

```text id="tzversion"
timezone
database_version
```

vì historical rules có thể thay đổi trong future database revisions.

---

# 27. DST

Daylight saving transitions phải được xử lý bởi timezone database.

Không viết:

```text id="bad_dst"
offset = +1h
```

thủ công trong application.

---

# 28. Ambiguous local time

Khi DST rollback tạo hai local times giống nhau:

```text id="ambiguous"
2026-11-01 01:30
```

conversion phải trả ambiguity hoặc yêu cầu explicit policy.

---

# 29. Nonexistent local time

Khi DST spring-forward bỏ qua một khoảng local time:

```text id="nonexistent"
local datetime
```

phải báo:

```text id="nonexist2"
NONEXISTENT_LOCAL_TIME
```

hoặc áp dụng explicit resolution policy.

---

# 30. Calendar

Baseline calendar:

```text id="caltypes"
GREGORIAN
```

Architecture cho phép mở rộng calendar khác.

Không hardcode mọi calendar operation vào `Instant`.

---

# 31. Date arithmetic

```text id="datearith"
date + 1 day
```

khác:

```text id="durationarith"
instant + 24h
```

vì timezone/DST có thể làm hai phép này khác nhau.

---

# 32. Month arithmetic

Ví dụ:

```text id="month"
January 31 + 1 month
```

không được silently wrap sang một ngày bất ngờ.

Policy explicit:

```text id="monthpolicy"
CLAMP
REJECT
ROLL
```

---

# 33. Year/month/day units

Calendar units:

```text id="calunits"
YEAR
MONTH
WEEK
DAY
```

không phải `Duration`.

---

# 34. Duration units

Duration:

```text id="durunits"
NANOSECOND
MICROSECOND
MILLISECOND
SECOND
```

có thể mở rộng thành larger fixed units.

---

# 35. Timer

```text id="timer"
timer {
    timer_id
    clock
    deadline
    interval
    mode
}
```

---

# 36. Timer modes

```text id="timermodes"
ONE_SHOT
FIXED_DELAY
FIXED_RATE
CRON_LIKE
```

---

# 37. One-shot

```text id="oneshot"
now + duration
      ↓
fire once
```

---

# 38. Fixed delay

```text id="fixeddelay"
callback ends
      ↓
wait interval
      ↓
next execution
```

---

# 39. Fixed rate

```text id="fixedrate"
T0
T0 + interval
T0 + 2*interval
T0 + 3*interval
```

Không drift theo callback duration nếu scheduler có khả năng.

---

# 40. Timer overrun

Nếu callback mất quá lâu:

```text id="overrun"
T0
 │
 ├── expected T1
 │
 └── callback still running
```

Policy:

```text id="overrunpolicy"
SKIP
COALESCE
QUEUE
CATCH_UP_LIMITED
```

---

# 41. No timer explosion

Không cho:

```text id="timerexplosion"
10000 missed periods
```

tạo 10000 callbacks ngay lập tức mặc định.

Catch-up phải bounded.

---

# 42. Timer cancellation

```text id="cancel"
timer_cancel()
```

Sau cancel, callback không được bắt đầu nếu cancellation đã thắng race theo defined synchronization semantics.

---

# 43. Timer callback context

Timer callback chạy trong:

```text id="timertask"
AXTASK
```

hoặc scheduler context.

Timer không tạo hidden OS thread cho mỗi timer.

---

# 44. Timer scaling

Hàng triệu timers cần data structure phù hợp:

```text id="timerscale"
hierarchical timing wheel
timer heap
calendar queue
```

Implementation choice.

Không yêu cầu một global sorted list.

---

# 45. Timer resolution

Timer precision không đồng nghĩa timer accuracy.

API expose:

```text id="precision"
requested
effective
resolution
```

---

# 46. Timer jitter

Observability có thể đo:

```text id="jitter"
scheduled_time
actual_fire_time
jitter
```

AXTIME không tự coi jitter là error.

---

# 47. Scheduler integration

```text id="sched"
AXTIME
   ↓
deadline
   ↓
AXTASK
   ↓
scheduler
```

AXTIME sở hữu temporal semantics, scheduler sở hữu execution.

---

# 48. Async integration

`AXASYNC` có thể dùng:

```text id="async"
await sleep(5ms)
await timeout(operation, 2s)
```

AXTIME cung cấp duration/deadline.

---

# 49. Timeout combinator

Native primitive:

```text id="timeoutapi"
with_timeout(deadline, operation)
```

Semantics:

- deadline propagation;
- cancellation;
- timeout result.

Execution/cancellation ownership vẫn thuộc AXASYNC/AXTASK.

---

# 50. Deadline propagation

Request context:

```text id="deadlineprop"
deadline
 ↓
IPC
 ↓
network
 ↓
database
```

Mỗi layer có thể derive remaining time.

---

# 51. Remaining time

```text id="remaining"
remaining(deadline)
```

Nếu deadline passed:

```text id="expired"
TIME_EXPIRED
```

---

# 52. Deadline comparison

Deadline chỉ so sánh trực tiếp khi thuộc cùng clock domain.

Không so sánh arbitrary clock timestamps.

---

# 53. CPU/process/thread time

AXTIME có thể expose:

```text id="cpuc"
cpu_time()
process_cpu_time()
thread_cpu_time()
```

Đây là resource accounting clocks, không phải wall time.

---

# 54. Benchmark clock

Benchmark API:

```text id="bench"
measure(monotonic_clock, operation)
```

Không dùng wall clock để benchmark.

---

# 55. Calendar parsing

Parser phải phân biệt:

```text id="parse"
Instant
Date
LocalDateTime
ZonedDateTime
Duration
```

Không đoán type mơ hồ từ string nếu ambiguity có thể gây sai.

---

# 56. ISO 8601

Interoperability format baseline:

```text id="iso"
ISO-8601 / RFC-compatible representations
```

Canonical internal representation vẫn typed native values.

---

# 57. Formatting

```text id="format"
format_instant()
format_date()
format_duration()
format_zoned_datetime()
```

Locale/timezone explicit.

---

# 58. Parsing errors

```text id="parseerr"
TIME_PARSE_INVALID
TIMEZONE_UNKNOWN
OFFSET_INVALID
DATE_INVALID
AMBIGUOUS_LOCAL_TIME
NONEXISTENT_LOCAL_TIME
```

---

# 59. Locale

Locale formatting không được làm thay đổi underlying instant.

```text id="locale"
instant
 ↓
timezone
 ↓
locale
 ↓
formatted text
```

---

# 60. Internationalization boundary

Localization formatting thuộc internationalization layer nếu Axiom xây subsystem riêng.

AXTIME cung cấp temporal data.

---

# 61. Serialization

Native binary:

```text id="serialize"
Instant → fixed-width/compact representation
Duration → signed integer
```

Không serialize local timezone-adjusted strings làm canonical representation.

---

# 62. ABI stability

Temporal ABI phải xác định:

```text id="abi"
width
signedness
precision
epoch
endianness
serialization
```

---

# 63. Epoch

Axiom canonical instant epoch phải được cố định.

Đề xuất:

```text id="epoch"
Unix epoch
1970-01-01T00:00:00Z
```

với signed range đủ rộng.

---

# 64. Range

Không chỉ hỗ trợ 32-bit Unix timestamps.

Internal instant nên đủ rộng để biểu diễn:

```text id="range"
historical
modern
far-future
```

trong practical native range.

---

# 65. Nanosecond storage

Canonical:

```text id="nano"
signed 128-bit total nanoseconds
```

có thể là semantic model.

Implementation có thể tối ưu thành pair:

```text id="pair"
seconds
nanoseconds
```

nếu ABI giữ semantics tương đương.

---

# 66. Leap-second representation

Axiom phải có policy explicit cho:

```text id="leap"
23:59:60
```

Không để parser/compiler tự suy đoán.

---

# 67. Virtual time

Simulation:

```text id="virtual"
virtual_clock {
    current
    rate
    paused
}
```

---

# 68. Deterministic simulation

Trong test:

```text id="sim"
clock.now()
```

có thể trả deterministic value.

Không gọi hardware clock.

---

# 69. Virtual timer

Virtual clock advancement:

```text id="virtualtimer"
advance(1s)
    ↓
due timers
    ↓
deterministic execution
```

---

# 70. Replay

AXDIAGNOSTICS/AXOBSERVABILITY replay có thể dùng:

```text id="replay"
recorded clock
```

để tái tạo temporal sequence.

---

# 71. Time injection

Application có thể nhận:

```text id="clockinject"
Clock
```

interface thay vì hardcoding global clock.

Giúp testing.

---

# 72. Global clock

Axiom vẫn cung cấp global system clocks:

```text id="globalclock"
monotonic_now()
wall_now()
```

nhưng testable code có thể inject clock.

---

# 73. Clock permissions

Reading public system time thường không cần privileged capability.

Changing system clock:

```text id="setclock"
```

là privileged operation thuộc platform/system security.

AXTIME không tự grant permission.

---

# 74. Time synchronization

AXTIME có thể expose metadata:

```text id="sync"
clock_sync_status {
    synchronized
    source
    offset_estimate
    uncertainty
}
```

Actual synchronization mechanism thuộc platform/network/time-service layer.

---

# 75. Uncertainty

Distributed applications có thể cần:

```text id="uncertainty"
instant
uncertainty
```

để không giả định precision cao hơn clock thực tế.

---

# 76. Clock quality

```text id="quality"
clock_quality {
    resolution
    precision
    uncertainty
    stability
}
```

---

# 77. Security timestamp

AXAUDIT có thể dùng:

```text id="auditclock"
wall timestamp
monotonic timestamp
```

nhưng AXAUDIT sở hữu event semantics.

---

# 78. Logging integration

AXLOGGING sử dụng:

```text id="loggingtime"
wall time
monotonic time
```

AXTIME sở hữu clock primitives.

---

# 79. Observability integration

AXOBSERVABILITY sử dụng:

```text id="obs_time"
monotonic duration
wall timestamp
```

để latency và time-series không nhầm clock semantics.

---

# 80. Configuration integration

AXCONFIG có thể sử dụng:

```text id="configtime"
duration
deadline
TTL
```

Ví dụ:

```text id="ttl"
remote_source.ttl = 30m
```

---

# 81. Native API — clocks

```text id="timeapi1"
clock_get()
clock_info()

monotonic_now()
wall_now()
cpu_now()
process_cpu_now()
thread_cpu_now()
```

---

# 82. Native API — duration

```text id="timeapi2"
duration_from_ns()
duration_from_us()
duration_from_ms()
duration_from_s()

duration_add()
duration_sub()
duration_mul()
duration_div()

duration_compare()
duration_is_zero()
duration_is_negative()
```

---

# 83. Native API — deadlines

```text id="timeapi3"
deadline_after()
deadline_now()
deadline_remaining()
deadline_expired()
deadline_compare()
```

---

# 84. Native API — timers

```text id="timeapi4"
timer_create()
timer_start()
timer_cancel()
timer_pause()
timer_resume()
timer_reset()
timer_get_state()
timer_get_stats()
```

---

# 85. Native API — calendar

```text id="timeapi5"
date_create()
datetime_create()
datetime_to_instant()
instant_to_datetime()

date_add()
date_diff()
month_add()
year_add()
```

---

# 86. Native API — timezone

```text id="timeapi6"
timezone_get()
timezone_load()
timezone_version()
timezone_convert()
timezone_offset()
```

---

# 87. Native API — formatting

```text id="timeapi7"
time_parse()
time_format()
duration_parse()
duration_format()
```

---

# 88. Native API — virtual clock

```text id="timeapi8"
virtual_clock_create()
virtual_clock_set()
virtual_clock_advance()
virtual_clock_pause()
virtual_clock_resume()
virtual_clock_destroy()
```

---

# 89. Native ABI

```text id="timeabi"
AXTIME_ABI_1
```

Core types:

```text id="timetypes"
Instant
Duration
Date
Time
DateTime
ZonedDateTime
TimeZone
Deadline
Clock
Timer
```

---

# 90. Error model

```text id="timeerrors"
TIME_INVALID
TIME_OVERFLOW
TIME_UNDERFLOW
TIME_CLOCK_UNAVAILABLE
TIME_CLOCK_INVALID
TIME_DEADLINE_EXPIRED
TIME_TIMER_INVALID
TIME_TIMER_CANCELLED
TIME_TIMER_OVERFLOW
TIME_TIMEZONE_UNKNOWN
TIME_TIMEZONE_VERSION
TIME_AMBIGUOUS_LOCAL
TIME_NONEXISTENT_LOCAL
TIME_DATE_INVALID
TIME_PARSE_INVALID
TIME_FORMAT_INVALID
TIME_UNSUPPORTED_CALENDAR
TIME_UNSUPPORTED_PRECISION
TIME_VIRTUAL_CLOCK_INVALID
TIME_PERMISSION_DENIED
```

---

# 91. Performance

Hot path:

```text id="timeperf"
monotonic_now()
deadline_remaining()
duration_compare()
```

phải tránh heap allocation.

---

# 92. Timer allocation

Timer creation có thể allocate runtime resources.

Nhưng:

```text id="timerhot"
timer_check()
deadline_remaining()
```

không được yêu cầu allocation.

---

# 93. Timer scheduler

Không tạo OS thread cho mỗi timer.

```text id="timerthread"
100000 timers
      ↓
shared scheduler
```

---

# 94. High-resolution timers

Platform-specific high resolution timer được expose capability.

Không hứa accuracy mà hardware/platform không hỗ trợ.

---

# 95. Power efficiency

Timer subsystem có thể coalesce timers:

```text id="coalesce"
T1 = 1000ms
T2 = 1002ms
T3 = 1005ms
```

thành wake-up gần nhau nếu application cho phép.

Policy:

```text id="coalescepolicy"
STRICT
RELAXED
POWER_SAVING
```

---

# 96. Real-time mode

Real-time profile có thể disable timer coalescing.

Nhưng scheduler/OS capability quyết định guarantee thực tế.

---

# 97. Timer affinity

Timer có thể chỉ định execution context:

```text id="affinity"
task
scheduler
CPU affinity
```

AXTIME chỉ giữ temporal request; AXTASK/AXPROCESS thực thi.

---

# 98. Cancellation race

Semantics:

```text id="cancelrace"
cancel()
```

trả về trạng thái:

```text id="cancelresult"
CANCELLED
ALREADY_FIRED
RUNNING
COMPLETED
```

để caller biết cancellation đã thắng hay chưa.

---

# 99. Periodic timer state

```text id="timerstate"
CREATED
ARMED
FIRING
PAUSED
CANCELLED
COMPLETED
```

---

# 100. Canonical flow — timeout

```text id="flowtimeout"
operation
   ↓
monotonic_now()
   ↓
deadline = now + timeout
   ↓
AXASYNC
   ↓
operation
   ↓
deadline_remaining()
   ↓
complete / timeout
```

---

# 101. Canonical flow — scheduling

```text id="flowschedule"
timer
 ↓
deadline
 ↓
AXTASK
 ↓
scheduler
 ↓
task runnable
 ↓
callback
```

---

# 102. Canonical flow — local datetime

```text id="flowlocal"
Instant
  ↓
TimeZone
  ↓
Calendar
  ↓
CivilDateTime
```

---

# 103. Canonical flow — local → instant

```text id="flowinstant"
CivilDateTime
    ↓
TimeZone
    ↓
resolve ambiguity
    ↓
Instant
```

---

# 104. Canonical flow — observability

```text id="flowobs"
start = monotonic_now()
operation
end = monotonic_now()

duration = end - start
```

Không dùng wall clock.

---

# 105. Canonical flow — logging

```text id="flowlog"
wall_now()
+
monotonic_now()
+
record
```

---

# 106. Canonical flow — configuration TTL

```text id="flowttl"
source
 ↓
expires_at = monotonic/deadline semantics
 ↓
check
 ↓
expired
```

Nếu TTL là elapsed-time concept, không dùng local calendar arithmetic.

---

# 107. Canonical flow — simulation

```text id="flowsim"
virtual clock
    ↓
advance()
    ↓
due timers
    ↓
deterministic task execution
```

---

# 108. Time API ergonomics

Axiom nên cho phép:

```text id="ergonomic"
5.seconds
100.milliseconds
2.hours
```

với compiler literal support.

Nhưng:

```text id="explicit"
5.seconds
```

là `Duration`, không phải integer.

---

# 109. Deadline ergonomics

```text id="ergodeadline"
deadline.after(5.seconds)
```

rõ nghĩa hơn:

```text id="baddeadline"
now + 5
```

---

# 110. Compile-time duration

Compiler có thể constant-fold:

```text id="constduration"
5.seconds + 500.milliseconds
```

thành một constant duration.

---

# 111. Type safety

Không cho implicit:

```text id="notype"
Duration → integer
```

nếu conversion có thể gây mất semantic information.

Explicit conversion:

```text id="explicitconv"
duration.to_milliseconds()
```

---

# 112. Calendar safety

Không cho:

```text id="calendarbad"
local_datetime - local_datetime
```

nếu timezone ambiguity chưa được resolve.

---

# 113. Serialization safety

Không serialize:

```text id="unsafe"
local time string
```

rồi coi nó là absolute instant.

Timezone/offset context phải được bảo toàn.

---

# 114. AI integration

AI tooling có thể:

- giải thích timezone conversion;
- phát hiện wall-clock/monotonic misuse;
- phân tích timeout;
- generate date/time code;
- tìm timer leaks;
- kiểm tra calendar edge cases.

AI không được tự thay đổi system clock.

---

# 115. Compiler diagnostics

Compiler có thể cảnh báo:

```text id="warn"
wall_clock used for duration measurement
```

hoặc:

```text id="warn2"
implicit local-time conversion without timezone
```

nếu type system/compiler có đủ thông tin.

---

# 116. Static analysis

Axiom analyzer nên phát hiện:

```text id="static"
now_wall() - previous_wall()
```

và khuyến nghị monotonic clock cho elapsed-time measurement.

Đây là safety/performance correctness feature, không phải runtime overhead.

---

# 117. Deterministic tests

Test framework có thể inject:

```text id="testclock"
VirtualClock
```

để test:

- timeout;
- retry;
- expiration;
- periodic tasks;
- DST;
- calendar arithmetic.

---

# 118. No GC requirement

AXTIME không yêu cầu garbage collection.

Immutable timezone/database structures có thể dùng:

- static storage;
- reference counting;
- arena;
- epoch reclamation.

---

# 119. Concurrency

Clock reads phải thread-safe.

Timer operations phải xác định race semantics.

Timezone database loading phải immutable sau publication hoặc versioned.

---

# 120. Timezone database update

Update:

```text id="tzupdate"
TZDB N
 ↓
validate
 ↓
TZDB N+1
 ↓
publish
```

Existing zoned values giữ timezone/database identity cần thiết cho deterministic interpretation.

---

# 121. Historical reproducibility

Một historical timestamp conversion nên có khả năng ghi:

```text id="history"
timezone_id
timezone_database_version
```

nếu application yêu cầu reproducibility.

---

# 122. Distributed systems

Axiom không cố biến wall clock thành globally exact.

Distributed correlation dùng:

```text id="dist"
IDs
logical relationships
monotonic local durations
clock uncertainty
```

---

# 123. Network deadlines

Network operation có thể nhận:

```text id="netdeadline"
absolute deadline
```

thay vì mỗi layer tự cộng timeout mới.

Tránh timeout multiplication.

---

# 124. IPC deadlines

AXIPC có thể truyền deadline metadata.

Receiver không được kéo dài deadline một cách vô thức.

---

# 125. Storage deadlines

AXSTORAGE có thể sử dụng same deadline abstraction.

---

# 126. Resource expiration

Các subsystem có thể dùng:

```text id="expiration"
Deadline
```

cho:

- cache;
- leases;
- sessions;
- temporary resources.

Expiration semantics phải xác định clock domain.

---

# 127. Lease semantics

Lease:

```text id="lease"
lease {
    acquired
    expires
    renewal
}
```

Elapsed-time lease nên dựa trên monotonic clock.

---

# 128. Sleep

API:

```text id="sleep"
sleep(duration)
sleep_until(deadline)
```

`duration` là elapsed time.

---

# 129. Sleep cancellation

```text id="sleepcancel"
sleep_until(deadline, cancellation_token)
```

Cancellation thuộc AXASYNC/AXTASK.

---

# 130. Scheduler fairness

AXTIME không định nghĩa scheduler fairness.

Nó chỉ cung cấp temporal events/deadlines.

---

# 131. Performance metrics

AXOBSERVABILITY có thể collect:

```text id="timemetrics"
timer_count
timer_fires
timer_cancellations
timer_overruns
timer_jitter
clock_read_latency
clock_adjustments
timezone_loads
```

---

# 132. Diagnostics

AXDIAGNOSTICS có thể capture:

```text id="timediag"
clock source
clock quality
active timers
timer queue
deadline
timezone version
```

---

# 133. Logging

AXLOGGING có thể ghi:

```text id="timelog"
clock_adjustment
timezone_reload
timer_failure
```

nhưng AXTIME không tự biến chúng thành audit events.

---

# 134. Security

Changing:

```text id="settime"
system wall clock
```

phải qua platform security / AXSECURITY.

Reading time không tự cấp privilege.

---

# 135. Clock tampering

AXTIME có thể report:

```text id="clocktamper"
clock_adjusted
clock_source_changed
clock_jump
```

nhưng không tự kết luận đây là security attack.

---

# 136. Error recovery

Clock source failure:

```text id="clockfail"
primary clock
 ↓
fallback clock
```

nếu platform hỗ trợ.

Transition phải expose metadata.

---

# 137. No silent semantic degradation

Nếu requested precision không supported:

```text id="precisionfail"
```

API phải expose effective precision.

Không tuyên bố nanosecond accuracy khi platform chỉ đảm bảo microsecond.

---

# 138. Native platform mapping

Windows:

```text id="winclock"
QPC / system time facilities
```

Linux:

```text id="linuxclock"
clock_gettime family
```

macOS/iOS:

```text id="appleclock"
mach/clock facilities
```

WASM:

```text id="wasmclock"
host-provided clocks
```

Đây là backend implementation; AXTIME API giữ cùng semantic model.

---

# 139. Platform abstraction

Compiler/runtime không expose OS clock APIs trực tiếp cho portable Axiom application.

Application dùng:

```text id="portable"
AXTIME
```

Platform-specific code có thể access lower-level facilities qua appropriate unsafe/native interfaces.

---

# 140. Formal invariants

```text id="timeinv"
TIME-INV-01
Monotonic clock phải không giảm trong cùng clock domain.

TIME-INV-02
Wall clock không được giả định monotonic.

TIME-INV-03
Duration không phụ thuộc timezone.

TIME-INV-04
Deadline phải gắn với clock domain.

TIME-INV-05
Deadline thuộc khác clock domain không được so sánh trực tiếp.

TIME-INV-06
Timeout phải có duration semantics rõ ràng.

TIME-INV-07
Elapsed-time measurement phải sử dụng monotonic clock.

TIME-INV-08
Calendar datetime không được tự động coi là absolute instant.

TIME-INV-09
Local datetime conversion phải xác định timezone.

TIME-INV-10
Ambiguous local time phải được phát hiện hoặc resolve bằng explicit policy.

TIME-INV-11
Nonexistent local time phải được phát hiện hoặc resolve bằng explicit policy.

TIME-INV-12
Timezone rules phải có version identity.

TIME-INV-13
Timezone conversion không được hardcode một offset cố định thay cho timezone rules.

TIME-INV-14
Duration arithmetic phải detect overflow.

TIME-INV-15
Instant arithmetic phải detect overflow.

TIME-INV-16
Timer phải có bounded resource usage.

TIME-INV-17
Timer cancellation phải có defined race semantics.

TIME-INV-18
Timer periodic catch-up phải bounded.

TIME-INV-19
Timer không được tạo hidden OS thread cho mỗi timer.

TIME-INV-20
Timer callback phải có execution context rõ ràng.

TIME-INV-21
Timer precision không được tuyên bố cao hơn platform capability.

TIME-INV-22
Timer jitter không được bị coi là zero mặc định.

TIME-INV-23
Monotonic clock phải độc lập với wall-clock adjustment.

TIME-INV-24
Wall-clock adjustment không được làm thay đổi monotonic duration semantics.

TIME-INV-25
Virtual clock phải tách khỏi physical system clock.

TIME-INV-26
Deterministic simulation không được đọc hardware clock ngoài explicit escape hatch.

TIME-INV-27
Calendar arithmetic phải phân biệt calendar units và fixed durations.

TIME-INV-28
Month/year arithmetic phải có explicit end-of-month semantics.

TIME-INV-29
Serialization của Instant phải bảo toàn absolute temporal meaning.

TIME-INV-30
Serialization của ZonedDateTime phải bảo toàn timezone/offset context cần thiết.

TIME-INV-31
Clock precision/uncertainty phải có thể được expose khi platform cung cấp.

TIME-INV-32
System clock modification phải chịu platform security controls.

TIME-INV-33
AXTIME không được tự cấp quyền thay đổi system clock.

TIME-INV-34
Distributed systems không được giả định wall clocks globally exact.

TIME-INV-35
Network/IPC deadline propagation không được tự động kéo dài deadline.

TIME-INV-36
AXTIME không được sở hữu scheduler execution semantics.

TIME-INV-37
AXTIME không được sở hữu audit semantics.

TIME-INV-38
AXTIME không được yêu cầu garbage collector để bảo đảm temporal correctness.

TIME-INV-39
AI tooling không được tự thay đổi authoritative system clock.

TIME-INV-40
Mọi temporal API phải phân biệt rõ monotonic, wall-clock và calendar semantics.
```

---

# 141. Definition of Done

`AXTIME 5.0` được freeze khi Axiom có:

- monotonic clock;
- wall clock;
- UTC;
- instant;
- duration;
- deadline;
- timeout;
- clock metadata;
- clock quality;
- clock calibration;
- suspend-aware semantics;
- timer;
- one-shot timer;
- fixed-delay timer;
- fixed-rate timer;
- bounded catch-up;
- timer cancellation;
- timer coalescing;
- high-resolution capability;
- CPU/process/thread clocks;
- benchmark clock;
- Gregorian calendar;
- civil date/time;
- zoned datetime;
- timezone;
- timezone database;
- timezone versioning;
- DST handling;
- ambiguous local-time handling;
- nonexistent local-time handling;
- date arithmetic;
- month/year arithmetic;
- ISO-compatible parsing/formatting;
- native binary representation;
- virtual clock;
- deterministic timer simulation;
- replay support;
- deadline propagation;
- sleep;
- timeout integration;
- AXTASK integration;
- AXASYNC integration;
- AXNETWORK integration;
- AXIPC integration;
- AXSTORAGE integration;
- AXOBSERVABILITY integration;
- AXLOGGING integration;
- AXAUDIT integration;
- AXDIAGNOSTICS integration;
- compiler temporal literals;
- compiler misuse diagnostics;
- native ABI;
- native APIs;
- 40 invariants.

**AXTIME 5.0 → FROZEN.**

---

# BOOTSTRAP-765 — AXRANDOM

**Native Randomness, Pseudorandom Generators, Entropy Sources, Secure Randomness, Seeds & Deterministic Random Runtime 5.0**

Module tiếp theo sẽ chuẩn hóa một vấn đề tương tự `AXTIME`: Axiom phải phân biệt hoàn toàn:

```text
RANDOMNESS
    ≠
SECURE RANDOMNESS
    ≠
PSEUDORANDOMNESS
    ≠
DETERMINISTIC RANDOMNESS
```

và tránh lỗi kiến trúc nguy hiểm như dùng một PRNG thông thường cho:

```text
keys
tokens
nonces
security identifiers
```

Trong khi `AXCRYPTO`/`AXSECURITY` cần entropy và secure random source có semantics riêng. `AXRANDOM` sẽ cung cấp primitive thống nhất, còn security-sensitive consumers sẽ bị giới hạn bởi capability/profile thích hợp.