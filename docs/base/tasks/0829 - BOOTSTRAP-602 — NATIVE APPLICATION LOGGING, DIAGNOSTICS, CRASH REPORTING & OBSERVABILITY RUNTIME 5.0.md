Tiếp tục đúng chuỗi Axiom từ **BOOTSTRAP-602**. Task này hoàn thiện lớp observability/diagnostics native và liên kết trực tiếp với state, config, deployment của 600–601.

:::writing{variant="document" id="58321" title="BOOTSTRAP-602 — NATIVE APPLICATION LOGGING, DIAGNOSTICS, CRASH REPORTING & OBSERVABILITY RUNTIME 5.0"}

# BOOTSTRAP-602 — NATIVE APPLICATION LOGGING, DIAGNOSTICS, CRASH REPORTING & OBSERVABILITY RUNTIME 5.0

## 602.0. Mục tiêu

BOOTSTRAP-602 định nghĩa hệ thống:

- structured logging;
- diagnostics;
- tracing;
- metrics;
- health/status;
- crash handling;
- panic/fatal error reporting;
- native stack capture;
- crash artifact;
- minidump/core-dump abstraction;
- symbolization;
- diagnostic context;
- correlation ID;
- bounded diagnostic buffers;
- crash-safe emergency logging;
- log rotation;
- diagnostic redaction;
- build/config/state correlation;
- local và production observability.

Mục tiêu chính:

> Một ứng dụng Axiom native phải có khả năng tự quan sát, tự chẩn đoán và tạo artifact đủ để điều tra lỗi mà không bắt buộc phụ thuộc vào một logging/telemetry framework bên thứ ba.

BOOTSTRAP-602 không biến Axiom runtime thành một monitoring platform.

Nó chỉ cung cấp **primitive native, deterministic và composable** để application hoặc framework phía trên xây dựng hệ thống observability.

---

# 602.1. Nguyên tắc thiết kế

Hệ thống phải tuân thủ:

1. native-first;
2. zero/minimal dependency;
3. deterministic;
4. bounded memory;
5. thread-safe;
6. low overhead;
7. crash-safe ở mức có thể;
8. không ghi secret;
9. không block application khi logging bình thường;
10. không làm crash handler phụ thuộc vào allocator;
11. không yêu cầu network;
12. không yêu cầu daemon bên ngoài;
13. có thể disable hoàn toàn;
14. có thể compile-time eliminate log;
15. hỗ trợ Unicode UTF-8;
16. giữ nguyên build identity;
17. liên kết được với configuration fingerprint;
18. liên kết được với application state/checkpoint;
19. có thể symbolicate sau khi process đã chết.

---

# 602.2. Phạm vi

BOOTSTRAP-602 gồm:

```text
Logging
Diagnostics
Tracing
Metrics
Health
Crash handling
Panic/fatal handling
Stack capture
Crash artifacts
Symbolization metadata
Diagnostic context
Correlation
Redaction
Log sinks
Crash-safe emergency buffer
Runtime diagnostics API
```

Không gồm:

```text
Remote monitoring service
Cloud backend
Third-party APM
Distributed database
Analytics platform
Log search server
Dashboard UI
```

Các thành phần này có thể được xây dựng ở layer cao hơn.

---

# 602.3. Kiến trúc tổng thể

Runtime:

```text
Application
    │
    ├── Log API
    ├── Trace API
    ├── Metric API
    ├── Health API
    └── Diagnostic API
             │
             ▼
      Diagnostic Runtime
             │
      ┌──────┼─────────┐
      ▼      ▼         ▼
   Logger  Tracer   Metrics
      │      │         │
      └──────┼─────────┘
             ▼
      Diagnostic Context
             │
      ┌──────┼──────────────┐
      ▼      ▼              ▼
    Console File       Emergency Ring
             │
             ▼
       Crash Runtime
             │
      ┌──────┼─────────┐
      ▼      ▼         ▼
   Stack   Metadata   State
   Dump    Build ID   Snapshot
             │
             ▼
       Crash Artifact
```

---

# 602.4. Logging model

Axiom logging không phải string-printing đơn thuần.

Primitive chính:

```text
log(level, event, fields...)
```

Ví dụ:

```axiom
log.info("server.started",
    port = 8080,
    workers = 8)
```

Không yêu cầu format string runtime nếu compiler có thể tạo structured event trực tiếp.

---

# 602.5. Log levels

Core levels:

```text
trace
debug
info
notice
warn
error
fatal
```

Semantic:

```text
trace  = extremely detailed execution information
debug  = developer diagnostics
info   = normal lifecycle information
notice = significant normal state transition
warn   = abnormal but recoverable condition
error  = operation failed
fatal  = process cannot safely continue
```

---

# 602.6. Compile-time log filtering

Compiler/runtime phải cho phép:

```axiom
@log_level("info")
```

Khi build production:

```text
trace → removed
debug → removed
info  → retained
notice → retained
warn → retained
error → retained
fatal → retained
```

Code bị loại bỏ phải càng gần zero-cost càng tốt.

Không được evaluate argument nếu statement đã bị compile-time eliminated.

Ví dụ:

```axiom
debug(expensive_diagnostic())
```

Nếu `debug` bị disable:

```text
expensive_diagnostic()
```

không được thực thi.

---

# 602.7. Runtime log filtering

Compile-time filtering không thay thế runtime filtering.

Có thể cấu hình:

```text
default = info
network = debug
database = warn
graphics = error
```

Lookup category phải có overhead thấp.

---

# 602.8. Event identity

Mỗi structured event có:

```text
event_id
category
level
timestamp
thread_id
process_id
message
fields
context
```

`event_id` nên là stable identifier.

Ví dụ:

```text
APP.SERVER.STARTED
APP.DB.CONNECTION_FAILED
APP.CONFIG.RELOAD_FAILED
```

---

# 602.9. Event ID stability

Event ID không được phụ thuộc vào source line.

Không dùng:

```text
file + line
```

làm primary identity.

Cho phép source line là metadata phụ.

---

# 602.10. Structured fields

Fields có typed value:

```text
bool
integer
float
string
bytes
enum
duration
timestamp
UUID
path
IP
error
object
array
```

Ví dụ:

```axiom
log.error("db.connect.failed",
    host = host,
    port = port,
    error = err)
```

---

# 602.11. Không ép string hóa sớm

Runtime không nên biến:

```text
integer
duration
UUID
error
```

thành string ngay khi event được tạo.

Structured representation phải được giữ càng lâu càng tốt.

Điều này cho phép sink quyết định format.

---

# 602.12. Log sinks

Core sink interface:

```axiom
trait LogSink {
    fn write(event: LogEvent) -> Result
    fn flush() -> Result
    fn close() -> Result
}
```

Các sink native:

```text
ConsoleSink
FileSink
MemorySink
NullSink
DebugSink
```

---

# 602.13. Console sink

Console sink hỗ trợ:

```text
stdout
stderr
native debugger output
```

Fatal/error mặc định có thể ưu tiên `stderr`.

---

# 602.14. File sink

File sink phải hỗ trợ:

```text
append
create
truncate
rotation
size limit
retention
flush policy
```

---

# 602.15. Log rotation

Có thể rotate theo:

```text
size
time
startup
manual request
```

Ví dụ:

```text
app.log
app.log.1
app.log.2
app.log.3
```

---

# 602.16. Rotation atomicity

Rotation phải cố gắng đảm bảo:

```text
old file preserved
new file created
writer switched
```

Không được mất toàn bộ logging chỉ vì rotation thất bại.

---

# 602.17. Log failure policy

Nếu sink lỗi:

```text
application MUST NOT crash solely because logging failed
```

Trừ khi application tự cấu hình strict logging policy.

Default:

```text
log failure → diagnostic warning → continue
```

---

# 602.18. Asynchronous logging

Runtime có thể cung cấp:

```text
SyncLogger
AsyncLogger
```

Async logger:

```text
producer threads
       │
       ▼
bounded queue
       │
       ▼
writer thread
       │
       ▼
sink
```

---

# 602.19. Bounded logging queue

Queue phải có giới hạn.

Không được:

```text
unbounded allocation
```

khi logging tăng đột biến.

---

# 602.20. Queue overflow

Policy:

```text
DropNewest
DropOldest
DropDebugFirst
Block
FallbackSync
```

Default:

```text
DropDebugFirst
```

Production logging không được làm process chết vì queue đầy.

---

# 602.21. Logging backpressure

Application có thể chọn:

```axiom
logger.policy = .block
```

nhưng đây không phải default.

---

# 602.22. Emergency log buffer

Runtime phải có:

```text
EmergencyRingBuffer
```

Mục tiêu:

> giữ một lượng nhỏ diagnostic event gần nhất ngay cả khi normal logging path bị lỗi.

---

# 602.23. Emergency buffer properties

Emergency buffer:

- bounded;
- lock-minimized;
- preallocated;
- không phụ thuộc heap trong crash path;
- overwrite circular;
- thread-safe.

---

# 602.24. Crash-safe logging

Trong crash handler, runtime không được thực hiện operation có thể:

```text
allocate
deadlock
wait indefinitely
load arbitrary module
initialize complex runtime
```

Crash path phải sử dụng subset an toàn.

---

# 602.25. Crash handler

Runtime cài handler cho native fatal conditions.

Platform mapping:

```text
Windows → SEH / unhandled exception
Linux   → signals
macOS   → signals / Mach facilities
Android → platform-native crash facilities
iOS     → platform crash mechanisms
WASM    → runtime trap abstraction
```

Implementation cụ thể nằm trong platform backend.

---

# 602.26. Crash categories

Crash artifact phải phân biệt:

```text
panic
fatal error
unhandled exception
illegal instruction
access violation
stack overflow
abort
signal
assertion failure
runtime invariant violation
```

---

# 602.27. Panic

Axiom panic là explicit unrecoverable runtime condition.

Ví dụ:

```axiom
panic("internal invariant violated")
```

Panic phải:

1. ghi diagnostic;
2. capture context;
3. capture stack;
4. tạo crash artifact nếu khả thi;
5. terminate process theo policy.

---

# 602.28. Recoverable error không phải panic

Không được dùng panic cho normal error.

Ví dụ:

```axiom
file.read(path)
```

có thể trả:

```text
Result
```

thay vì panic.

---

# 602.29. Assertion

Có hai dạng:

```text
assert
debug_assert
```

`debug_assert` có thể compile-out ở production.

---

# 602.30. Fatal API

Primitive:

```axiom
fatal(error)
```

khác:

```axiom
return error
```

vì fatal biểu thị process không còn trạng thái an toàn để tiếp tục.

---

# 602.31. Crash artifact

Artifact chuẩn:

```text
.axcrash
```

Không bắt buộc là file duy nhất về mặt vật lý nhưng phải có logical schema thống nhất.

---

# 602.32. Crash artifact structure

```text
header
application
build
platform
process
thread
exception
stack
registers
modules
logs
diagnostic_context
configuration
state
environment
memory_summary
attachments
```

---

# 602.33. Crash artifact header

Header gồm:

```text
magic
version
endianness
architecture
timestamp
artifact_id
```

Ví dụ:

```text
AXCR
version = 1
arch = x86_64
```

---

# 602.34. Application identity

Crash artifact phải ghi:

```text
application_id
application_name
application_version
build_id
```

Các giá trị liên kết với BOOTSTRAP-601.

---

# 602.35. Configuration identity

Không ghi toàn bộ secret/config mặc định.

Artifact ghi:

```text
config_schema_version
config_fingerprint
profile
deployment_id
```

---

# 602.36. State identity

Liên kết BOOTSTRAP-600:

```text
state_schema_version
last_checkpoint_id
state_generation
checkpoint_timestamp
```

Không mặc định nhúng toàn bộ application state.

---

# 602.37. Crash context

Crash context:

```text
process_id
thread_id
main_thread_id
uptime
working_set
CPU usage
open diagnostic scopes
```

Các trường phụ thuộc platform.

---

# 602.38. Register capture

Nếu platform cho phép, crash artifact ghi:

```text
instruction pointer
stack pointer
frame pointer
general registers
flags/status
```

Architecture-specific backend.

---

# 602.39. Stack capture

Stack trace gồm:

```text
module
address
symbol
source
line
column
```

Nếu symbol chưa available:

```text
module + relative address
```

vẫn phải được lưu.

---

# 602.40. Stack depth

Runtime có giới hạn:

```text
MAX_STACK_FRAMES
```

để tránh crash handler chạy vô hạn.

---

# 602.41. Symbolization

Symbolization có thể thực hiện:

```text
at crash time
```

hoặc:

```text
post-process
```

Post-process được ưu tiên khi symbolization phức tạp.

---

# 602.42. Debug symbols

Build system phải có thể tạo:

```text
application binary
symbol artifact
debug metadata
```

Crash artifact chỉ cần giữ:

```text
build_id
module_id
addresses
```

sau đó symbolizer tra symbol artifact.

---

# 602.43. Build ID

Build ID phải ổn định theo binary.

Ví dụ:

```text
build_id = SHA-256(binary + relevant metadata)
```

Thuật toán chính xác có thể được thay đổi theo compiler policy nhưng identity phải collision-resistant.

---

# 602.44. Source mapping

Compiler debug metadata phải cho phép:

```text
machine address
→ function
→ source file
→ line
→ column
```

---

# 602.45. Inlining information

Symbol metadata nên lưu:

```text
inlined function chain
```

để stack trace phản ánh đúng source-level execution.

---

# 602.46. Module inventory

Crash artifact ghi danh sách module:

```text
module_id
name
base_address
size
build_id
version
path
```

Path có thể được redacted.

---

# 602.47. Diagnostic context

Axiom cung cấp context scope:

```axiom
with diagnostic.context(
    request_id = id,
    user_operation = "save")
{
    ...
}
```

Các log bên trong tự động inherit context.

---

# 602.48. Context inheritance

Context phải truyền qua:

```text
function call
task
async continuation
worker
thread
```

theo concurrency model của Axiom.

---

# 602.49. Context không được dùng global mutable state

Không dùng:

```text
global current_request_id
```

vì gây race và contamination giữa tasks.

---

# 602.50. Context storage

Context nên được gắn với execution context của Axiom.

Compiler/runtime có thể tối ưu:

```text
no active context → zero/near-zero overhead
```

---

# 602.51. Correlation ID

Runtime hỗ trợ:

```text
request_id
operation_id
trace_id
span_id
session_id
```

Tất cả là optional.

---

# 602.52. Trace

Trace primitive:

```axiom
with trace.span("database.query") {
    ...
}
```

Span chứa:

```text
trace_id
span_id
parent_span_id
start
duration
name
status
attributes
```

---

# 602.53. Tracing không bắt buộc network

Core tracing chỉ tạo local events.

Export sang OpenTelemetry hoặc backend khác là layer adapter.

---

# 602.54. Span overhead

Nếu tracing disabled:

```text
span creation → compile/runtime optimized no-op
```

Nếu enabled:

```text
bounded allocation
```

phải được ưu tiên.

---

# 602.55. Sampling

Runtime tracing hỗ trợ:

```text
Always
Never
Ratio
ParentBased
Custom
```

Default:

```text
Never
```

trong production nếu application không enable tracing.

---

# 602.56. Metrics

Primitive:

```axiom
counter
gauge
histogram
```

Ví dụ:

```axiom
metrics.counter("http.requests").inc()
metrics.gauge("workers.active").set(n)
metrics.histogram("request.duration").observe(dt)
```

---

# 602.57. Metric identity

Metric có:

```text
name
unit
description
type
labels
```

---

# 602.58. Cardinality protection

Runtime không được để metric labels tạo unbounded memory.

Ví dụ nguy hiểm:

```text
request_id as metric label
```

phải có policy hạn chế.

---

# 602.59. Metric storage

Default local metrics phải bounded.

Không được tạo vô hạn time-series.

---

# 602.60. Histogram

Histogram có bucket definition:

```text
fixed
explicit
exponential
```

Default nên là fixed bounded buckets.

---

# 602.61. Health subsystem

Runtime cung cấp:

```text
healthy
degraded
failed
starting
stopping
```

Application có thể expose:

```axiom
health.register("database", check_database)
```

---

# 602.62. Health không tự động network

Health API chỉ cung cấp local state.

HTTP endpoint là layer phía trên.

---

# 602.63. Diagnostic snapshot

Application có thể yêu cầu:

```axiom
diagnostics.snapshot()
```

Snapshot gồm:

```text
runtime status
threads/tasks
memory summary
recent logs
metrics
health
config identity
state identity
```

---

# 602.64. Snapshot bounded

Snapshot phải có giới hạn kích thước.

Không được dump toàn bộ process memory mặc định.

---

# 602.65. Runtime statistics

Có thể cung cấp:

```text
allocation count
allocation bytes
thread count
task count
open handles
I/O operations
GC count
```

Nhưng vì Axiom core không mặc định yêu cầu GC, `GC count` chỉ tồn tại nếu subsystem tương ứng được sử dụng.

---

# 602.66. Memory diagnostics

Runtime có thể expose:

```text
heap usage
arena usage
mapped memory
resident memory
peak memory
allocation failures
```

---

# 602.67. Allocation diagnostics

Debug build có thể track:

```text
allocation site
size
lifetime
owner
```

Production không bắt buộc.

---

# 602.68. Leak detection

Leak detector là optional diagnostic subsystem.

Không được biến leak detector thành runtime requirement.

---

# 602.69. Deadlock diagnostics

Debug runtime có thể track:

```text
lock owner
waiter
wait duration
dependency graph
```

Có thể phát hiện cycle.

---

# 602.70. Thread diagnostics

Snapshot thread:

```text
thread_id
name
state
CPU time
stack bounds
current task
```

---

# 602.71. Task diagnostics

Đối với Axiom task/async runtime:

```text
task_id
state
creation time
parent
executor
wait reason
```

---

# 602.72. Hung application detection

Runtime có thể phát hiện:

```text
no progress
```

nhưng không được tự động kết luận application deadlock.

Health layer có thể đặt watchdog.

---

# 602.73. Watchdog

Watchdog là optional.

```axiom
watchdog.start(
    timeout = 30s,
    policy = .diagnostic)
```

Default policy:

```text
diagnostic report
```

không tự terminate nếu chưa được cấu hình.

---

# 602.74. Crash loop detection

BOOTSTRAP-602 có thể ghi:

```text
previous_crash
crash_count
startup_after_crash
```

Dữ liệu persistence thực tế thuộc state/runtime layer của BOOTSTRAP-600.

---

# 602.75. Safe-mode hint

Nếu application crash liên tục, diagnostic artifact có thể ghi:

```text
recommended_safe_mode = true
```

Đây là metadata, không phải tự động thay đổi application behavior.

---

# 602.76. Environment capture

Artifact có thể ghi:

```text
OS
architecture
CPU features
runtime version
compiler version
application version
```

Không mặc định dump toàn bộ environment variables.

---

# 602.77. Environment redaction

Các field có thể chứa:

```text
TOKEN
PASSWORD
SECRET
KEY
COOKIE
AUTH
CREDENTIAL
```

phải bị redacted khi environment được capture.

---

# 602.78. Secret exclusion

`Secret<T>` từ BOOTSTRAP-601 không được serialize trực tiếp vào:

```text
log
trace
metric
crash artifact
```

---

# 602.79. Secret display

Nếu application cố log secret:

```axiom
log.info("config", password = secret)
```

runtime phải render:

```text
<redacted>
```

---

# 602.80. Sensitive annotation

Field có thể được đánh dấu:

```axiom
@secret
token: String
```

hoặc:

```axiom
@private
```

Diagnostic serializer phải tôn trọng metadata này.

---

# 602.81. Path privacy

Absolute filesystem paths có thể chứa thông tin nhạy cảm.

Runtime hỗ trợ:

```text
full
basename
relative
redacted
```

---

# 602.82. User data policy

Default crash artifact không được thu thập:

```text
arbitrary file contents
microphone data
camera data
clipboard
browser history
```

trừ khi application explicitly thêm attachment.

---

# 602.83. Diagnostic attachments

Application có thể thêm bounded attachment:

```axiom
crash.attach("query", query_summary)
```

Attachment phải khai báo:

```text
name
type
size
sensitivity
```

---

# 602.84. Attachment size limit

Runtime phải có:

```text
MAX_ATTACHMENT_SIZE
MAX_TOTAL_ATTACHMENTS
```

---

# 602.85. Binary attachments

Có thể attach:

```text
bytes
```

nhưng không được vượt giới hạn.

---

# 602.86. Diagnostic serialization

Crash artifact nên dùng binary format native:

```text
AXCR
```

Có thể có textual projection:

```text
.axcrash.json
```

cho tooling.

---

# 602.87. Binary format principles

Binary crash format phải:

- versioned;
- endian-aware;
- length-delimited;
- skip-unknown-field;
- corruption detectable;
- forward-compatible.

---

# 602.88. Checksum

Artifact có checksum:

```text
payload checksum
```

để phát hiện partial/corrupted writes.

---

# 602.89. Atomic artifact write

Crash artifact nên được ghi:

```text
temporary
→ fsync/flush policy
→ atomic rename
```

khi platform hỗ trợ.

---

# 602.90. Crash artifact filename

Default:

```text
<app>-<timestamp>-<process>-<artifact-id>.axcrash
```

Không được dùng secret hoặc user input trực tiếp trong filename.

---

# 602.91. Crash directory

Directory có thể lấy từ:

```text
deployment config
user data directory
system diagnostic directory
```

theo BOOTSTRAP-601.

---

# 602.92. Disk quota

Runtime phải giới hạn:

```text
max crash artifacts
max total bytes
```

---

# 602.93. Old artifact cleanup

Cleanup policy:

```text
age
count
total size
```

Không được xóa artifact đang được ghi.

---

# 602.94. Crash-safe allocator

Crash handler không được phụ thuộc allocator thông thường.

Runtime phải có emergency storage:

```text
static buffer
preallocated arena
fixed-size records
```

---

# 602.95. Crash-safe string

Crash path chỉ sử dụng bounded strings.

Không gọi formatter phức tạp nếu không cần.

---

# 602.96. Crash-safe locks

Crash handler không được lock mutex có khả năng đang bị thread chết giữ.

Ưu tiên:

```text
lock-free
try-lock
preallocated state
```

---

# 602.97. Reentrant crash handling

Nếu crash handler crash lần nữa:

```text
secondary failure
```

runtime phải fallback sang minimal termination path.

---

# 602.98. Crash recursion guard

Có global emergency state:

```text
NORMAL
HANDLING_CRASH
CRASH_HANDLER_FAILED
```

Nếu đã ở:

```text
HANDLING_CRASH
```

không được chạy crash pipeline lần hai.

---

# 602.99. Fatal logging

Fatal event phải cố gắng:

```text
write emergency event
capture stack
write artifact
flush
terminate
```

---

# 602.100. Flush policy

Logger hỗ trợ:

```text
manual
interval
severity-triggered
shutdown
fatal
```

Default:

```text
fatal → immediate flush
```

---

# 602.101. Shutdown diagnostics

Normal shutdown có thể ghi:

```text
application.stopping
application.stopped
```

và runtime summary.

---

# 602.102. Unexpected shutdown

Nếu process kết thúc mà không chạy shutdown:

```text
last emergency records
```

có thể được recover ở lần startup tiếp theo nếu storage mechanism cho phép.

---

# 602.103. Startup diagnostics

Runtime ghi:

```text
application.started
runtime.initialized
config.loaded
state.restored
```

nhưng các event này phải configurable.

---

# 602.104. Configuration linkage

Mỗi diagnostic session có:

```text
config_fingerprint
config_profile
deployment_id
```

để correlation với BOOTSTRAP-601.

---

# 602.105. State linkage

Mỗi diagnostic session có:

```text
state_generation
checkpoint_id
```

nếu state subsystem active.

---

# 602.106. Session ID

Runtime tạo:

```text
diagnostic_session_id
```

mỗi process startup.

Session ID không thay đổi trong lifetime process.

---

# 602.107. Boot ID

Nếu application restore từ checkpoint:

```text
boot_id
state_generation
checkpoint_id
```

được ghi riêng.

---

# 602.108. Process identity

Runtime exposes:

```axiom
runtime.process_id()
runtime.session_id()
runtime.build_id()
```

---

# 602.109. Time sources

Diagnostics cần hai loại clock:

```text
wall clock
monotonic clock
```

Wall clock dùng timestamp.

Monotonic dùng duration.

---

# 602.110. Timestamp correctness

Không dùng wall-clock subtraction để đo duration.

Ví dụ:

```text
start = monotonic.now()
...
duration = monotonic.now() - start
```

---

# 602.111. Clock correction

Wall clock có thể thay đổi do:

```text
NTP
manual adjustment
timezone
DST
```

Do đó event ordering chính xác phải dựa thêm vào monotonic sequence.

---

# 602.112. Event sequence

Mỗi process có thể có:

```text
diagnostic_sequence
```

để order events gần đúng.

---

# 602.113. Thread ordering

Events từ nhiều thread không đảm bảo global real-time order tuyệt đối.

Artifact phải giữ:

```text
timestamp
sequence
thread_id
```

để post-processing reconstruct.

---

# 602.114. Logger API

API tối thiểu:

```axiom
log.trace(event, ...)
log.debug(event, ...)
log.info(event, ...)
log.notice(event, ...)
log.warn(event, ...)
log.error(event, ...)
log.fatal(event, ...)
```

---

# 602.115. Generic logger

Có thể:

```axiom
log(level, event, fields)
```

để framework xây wrapper.

---

# 602.116. Category

Logger hỗ trợ:

```axiom
let log = Logger("network.http")
```

Category inheritance:

```text
network
network.http
network.http.client
```

---

# 602.117. Category configuration

Config:

```text
network = info
network.http = debug
network.http.parser = trace
```

---

# 602.118. Logger immutability

Logger handle có thể immutable.

Runtime configuration thay đổi thông qua logger registry.

---

# 602.119. Runtime log reload

BOOTSTRAP-601 config reload có thể thay đổi:

```text
log levels
sink configuration
rotation
```

Nhưng logger phải giữ consistency snapshot.

---

# 602.120. Sink reload

Sink replacement:

```text
new sink initialized
→ switch
→ old sink drained
→ old sink closed
```

Không được làm mất toàn bộ logger khi reload thất bại.

---

# 602.121. Log format

Built-in formats:

```text
text
json
binary
compact
```

---

# 602.122. Human-readable format

Ví dụ:

```text
2026-09-24T10:12:33.182Z INFO network.http request.completed
request_id=...
status=200
duration=12ms
```

---

# 602.123. JSON format

Structured sink có thể tạo:

```json
{
  "level": "info",
  "event": "request.completed",
  "duration_ms": 12
}
```

Field ordering không có semantic significance.

---

# 602.124. Binary logging

Binary event stream hữu ích cho:

```text
high-frequency diagnostics
low-overhead runtime tracing
```

---

# 602.125. Serialization errors

Nếu field serialization thất bại:

```text
<serialization-error>
```

không làm application crash.

---

# 602.126. Recursive object logging

Runtime phải giới hạn:

```text
max depth
max fields
max bytes
```

để tránh recursive object gây runaway logging.

---

# 602.127. Large value truncation

String/bytes lớn phải được truncate:

```text
prefix + truncation marker
```

---

# 602.128. Deterministic truncation

Cùng input và cùng policy phải tạo output deterministic.

---

# 602.129. Error object

`Error` diagnostic serialization nên có:

```text
error_code
message
cause
source
stack
metadata
```

---

# 602.130. Error chain

Error có thể chứa:

```text
cause
```

theo chain:

```text
high-level error
  ↓
database error
  ↓
OS error
```

Depth phải bounded.

---

# 602.131. Error code

Error code là stable machine-readable identity.

Không dùng message làm error identity.

---

# 602.132. Source location

Development diagnostic có:

```text
file
line
column
function
```

Production có thể chỉ giữ function/build address nếu debug metadata không được deploy.

---

# 602.133. Compiler integration

Compiler phải cung cấp intrinsic:

```text
current source location
current function
module identity
```

nếu cần.

---

# 602.134. Zero-cost source location

Nếu source location không được sử dụng:

```text
metadata → omitted
```

---

# 602.135. Compile-time event metadata

Compiler có thể encode:

```text
event ID
category
source location
format schema
```

vào readonly binary section.

---

# 602.136. Runtime registry

Event metadata registry có thể được generated bởi compiler.

Không yêu cầu dynamic registration.

---

# 602.137. Linker stripping

Nếu event không được sử dụng:

```text
unused metadata → dead-stripped
```

---

# 602.138. Diagnostics feature flags

Build flags:

```text
AX_DIAGNOSTICS
AX_LOGGING
AX_TRACING
AX_METRICS
AX_CRASH_REPORTING
AX_SYMBOLS
```

cho phép loại bỏ subsystem không cần thiết.

---

# 602.139. Minimal runtime

Ứng dụng nhỏ có thể build:

```text
logging = none
tracing = none
metrics = none
crash = minimal
```

Runtime không được kéo theo toàn bộ observability stack.

---

# 602.140. Static linking

Static executable phải có thể dead-strip:

```text
unused diagnostic sinks
unused encoders
unused metrics
unused tracing
```

---

# 602.141. Dynamic linking

Dynamic runtime cũng phải tránh global singleton bắt buộc giữa modules.

Mỗi process có một logical diagnostic runtime.

---

# 602.142. Library isolation

Library không được tự ý:

```text
replace application's logger
change global log level
install crash handler destructively
```

Library phải register/subordinate vào host runtime.

---

# 602.143. Crash handler ownership

Application runtime là owner chính.

Libraries có thể:

```text
register diagnostic callbacks
```

nhưng không override toàn bộ crash handler.

---

# 602.144. Callback safety

Diagnostic callback phải khai báo:

```text
normal
shutdown
crash-safe
```

Chỉ callback `crash-safe` mới được gọi trong crash path.

---

# 602.145. Crash callback timeout

Crash callback không được block vô hạn.

Crash handler có thể bỏ qua callback quá thời gian.

---

# 602.146. Plugin isolation

Dynamic plugins phải được coi là untrusted diagnostic source.

Một plugin crash không được làm crash handler recursively fail nếu runtime có thể tránh.

---

# 602.147. Diagnostic permissions

Application sandbox có thể không cho phép:

```text
write arbitrary paths
inspect other processes
read executable memory
```

Runtime phải graceful degrade.

---

# 602.148. Permission failure

Nếu crash artifact không thể ghi:

```text
emergency stderr/debug output
```

là fallback.

---

# 602.149. Platform fallback

Mỗi platform có backend:

```text
NativeCrashBackend
NativeStackBackend
NativeSymbolBackend
NativeFileBackend
```

Core API không phụ thuộc platform.

---

# 602.150. WASM

WASM không có native process crash semantics đầy đủ.

Runtime map:

```text
trap
unreachable
out-of-bounds
host exception
```

thành diagnostic event.

---

# 602.151. Mobile

Mobile backend phải tính đến:

```text
sandbox
limited storage
background termination
OS crash collection
```

Axiom runtime không giả định desktop filesystem.

---

# 602.152. iOS restrictions

Nếu platform không cho phép custom crash dump hoàn chỉnh:

```text
runtime diagnostic metadata
```

phải vẫn hoạt động trước termination khi khả thi.

---

# 602.153. Android restrictions

Runtime có thể tích hợp với native crash mechanisms nhưng core API vẫn platform-neutral.

---

# 602.154. Crash report privacy

Crash report phải có policy:

```text
minimal
standard
verbose
```

Default:

```text
standard
```

---

# 602.155. Privacy levels

`minimal`:

```text
build
platform
exception
stack
```

`standard` thêm:

```text
recent logs
diagnostic context
runtime statistics
```

`verbose` thêm các diagnostic attachments được application cho phép.

---

# 602.156. No implicit upload

Runtime không tự upload crash artifact.

Upload là responsibility của application/service layer.

---

# 602.157. Export API

```axiom
diagnostics.export(path)
```

có thể tạo artifact.

---

# 602.158. Diagnostic reader

Tooling phía ngoài runtime phải có thể:

```text
read .axcrash
validate
summarize
symbolize
export JSON
```

---

# 602.159. `ax crash`

Axiom toolchain nên cung cấp:

```text
ax crash inspect file.axcrash
ax crash symbols file.axcrash
ax crash report file.axcrash
```

---

# 602.160. Human crash report

Tool có thể tạo:

```text
Crash summary
Exception
Application
Build
Platform
Thread
Stack
Recent logs
State
Configuration identity
```

---

# 602.161. Machine crash report

JSON output phải giữ:

```text
stable field names
schema version
typed values
```

để AI/tooling xử lý.

---

# 602.162. AI diagnostic metadata

Axiom build artifacts có thể chứa:

```text
function signatures
module graph
type metadata
source mapping
error codes
event schemas
```

nếu build profile cho phép.

Mục tiêu là giúp AI/code tooling chẩn đoán lỗi chính xác mà không cần đọc toàn bộ binary.

---

# 602.163. AI crash summary

Tooling có thể xuất:

```text
machine-readable diagnostic bundle
```

nhưng runtime không được chứa AI model.

---

# 602.164. Deterministic diagnostics

Trong cùng execution scenario, diagnostics nên có:

```text
stable event IDs
stable error codes
stable schema
```

Timestamp và process-specific identifiers đương nhiên thay đổi.

---

# 602.165. Diagnostic schema version

Mỗi artifact:

```text
diagnostic_schema_version
```

để tooling tương thích nhiều compiler/runtime version.

---

# 602.166. Backward compatibility

Reader mới phải đọc artifact cũ.

Reader cũ có thể từ chối artifact mới nếu schema major không tương thích.

---

# 602.167. Forward compatibility

Unknown fields phải có thể skip nếu binary format hỗ trợ length-delimited records.

---

# 602.168. Corruption handling

Crash reader không được crash khi đọc crash artifact bị hỏng.

Nó phải báo:

```text
corrupt section
truncated section
invalid checksum
unsupported version
```

---

# 602.169. Log integrity

Nếu security profile yêu cầu, log sink có thể thêm:

```text
hash chain
signature
```

Đây là optional.

---

# 602.170. Tamper evidence

Security diagnostics có thể sử dụng:

```text
previous_event_hash
current_event_hash
```

để phát hiện sửa log.

---

# 602.171. Performance counters

Logger phải expose internal metrics:

```text
events_written
events_dropped
bytes_written
queue_depth
sink_errors
flush_count
```

---

# 602.172. Tracing counters

```text
spans_created
spans_sampled
spans_dropped
```

---

# 602.173. Crash counters

```text
panic_count
fatal_count
crash_count
artifact_write_failures
```

---

# 602.174. Health of diagnostics

Diagnostic subsystem tự có health:

```text
logger_healthy
sink_healthy
crash_storage_available
diagnostic_queue_usage
```

---

# 602.175. Avoid observability recursion

Diagnostics không được log vô hạn lỗi của chính logger.

Ví dụ:

```text
logger failed
→ logger logs logger failure
→ logger fails
→ infinite recursion
```

Không được phép.

---

# 602.176. Internal diagnostic channel

Runtime có:

```text
internal_diagnostic_channel
```

tách khỏi application logger.

---

# 602.177. Emergency fallback

Nếu toàn bộ logger unavailable:

```text
stderr
debugger
emergency buffer
```

là fallback.

---

# 602.178. No allocation requirement

Emergency fallback phải hoạt động với:

```text
allocator unavailable
```

trong phạm vi backend cho phép.

---

# 602.179. Thread-safe logger

Logger phải safe cho concurrent producers.

---

# 602.180. Lock contention

Hot path không nên sử dụng một global mutex duy nhất.

Thiết kế ưu tiên:

```text
thread-local buffer
MPSC queue
sharded state
atomic counters
```

---

# 602.181. Thread-local buffering

Thread có thể ghi event vào local buffer trước khi publish.

Điều này giảm contention.

---

# 602.182. Event pooling

High-throughput logging có thể dùng preallocated event pools.

Pool exhaustion phải có deterministic policy.

---

# 602.183. No hidden allocations

API documentation phải phân biệt:

```text
allocation-free
may allocate
crash-safe
blocking
```

---

# 602.184. API effect metadata

Compiler/runtime metadata có thể biểu diễn:

```text
@allocates
@blocks
@crash_safe
@throws
```

để AI và compiler hiểu cost.

---

# 602.185. Diagnostic cost visibility

Axiom muốn performance predictable.

Do đó API phải cho phép developer biết:

```text
log.info(...)
```

có thể:

```text
allocate?
block?
format?
```

tùy backend.

---

# 602.186. Fast path

Disabled log:

```text
branch
→ return
```

là mục tiêu.

---

# 602.187. Compile-time constants

Nếu level/category là compile-time constant:

```text
compiler can eliminate disabled event
```

---

# 602.188. Dynamic level

Nếu runtime-configured:

```text
if level_enabled(category, level)
    construct event
```

Không tạo event trước khi check.

---

# 602.189. Formatting order

Correct order:

```text
check enabled
→ create event
→ evaluate fields
→ serialize
→ enqueue
```

Không phải:

```text
evaluate everything
→ check enabled
```

---

# 602.190. Metric fast path

Counters nên dùng:

```text
atomic increment
```

hoặc thread-local aggregation khi phù hợp.

---

# 602.191. Histogram performance

Histogram hot path nên tránh allocation.

---

# 602.192. Trace span lifecycle

Span:

```text
begin
→ attributes
→ events
→ end
```

Nếu forgotten:

```text
runtime may auto-close on scope exit
```

nếu ngôn ngữ hỗ trợ deterministic scope cleanup.

---

# 602.193. Scope cleanup

Diagnostics phải tích hợp với deterministic cleanup của Axiom.

Không phụ thuộc GC finalizer.

---

# 602.194. Async span propagation

Span context phải được propagate qua Axiom task runtime.

---

# 602.195. Context cancellation

Nếu task bị cancel:

```text
span.status = cancelled
```

nếu tracing enabled.

---

# 602.196. Error correlation

Nếu Result/Error được trả về:

```text
trace
request
operation
```

có thể được gắn vào error metadata.

---

# 602.197. Error display

Developer-facing error có thể hiển thị:

```text
Error: DB_CONNECTION_FAILED
Operation: save_user
Trace: ...
Cause: timeout
```

---

# 602.198. Production error messages

Production error message không được tự động chứa:

```text
password
token
secret
full request body
```

---

# 602.199. Diagnostic policy inheritance

Application có:

```text
global diagnostic policy
module policy
logger policy
event policy
```

Precedence phải deterministic.

---

# 602.200. Default policy

Default:

```text
logging = info
tracing = off
metrics = on/minimal
crash reporting = on
verbose attachments = off
network export = off
```

---

# 602.201. Development profile

Development:

```text
debug logs = on
stack symbols = on
verbose diagnostics = on
```

---

# 602.202. Release profile

Release:

```text
debug logs = off
symbols externalized
standard crash artifact
minimal sensitive data
```

---

# 602.203. Shipping profile

Shipping có thể:

```text
logging = warn
tracing = off
metrics = minimal
crash reporting = standard
```

---

# 602.204. Server profile

Server có thể:

```text
structured logging
metrics
tracing
rotation
health
```

nhưng tất cả vẫn là configuration.

---

# 602.205. Embedded profile

Embedded có thể:

```text
binary diagnostics
small ring buffer
no filesystem
no dynamic allocation
```

---

# 602.206. Kernel/freestanding

Axiom freestanding target không được phụ thuộc vào full diagnostic runtime.

Có thể chỉ cung cấp:

```text
panic
serial diagnostic
fixed buffer
```

---

# 602.207. Runtime tiers

Định nghĩa:

```text
Tier 0 — none
Tier 1 — minimal
Tier 2 — standard
Tier 3 — full diagnostics
```

---

# 602.208. Tier 0

Chỉ còn:

```text
fatal termination
minimal platform reporting
```

---

# 602.209. Tier 1

Có:

```text
basic logging
panic
stack
basic crash artifact
```

---

# 602.210. Tier 2

Có:

```text
structured logs
metrics
health
tracing
crash artifact
```

---

# 602.211. Tier 3

Thêm:

```text
advanced memory diagnostics
deadlock diagnostics
verbose context
debug metadata
```

---

# 602.212. Runtime ABI

Public diagnostics ABI phải versioned.

Không expose internal logger structures trực tiếp.

---

# 602.213. ABI stability

Application compiled với runtime ABI vN phải xác định rõ compatibility.

---

# 602.214. FFI

C API projection có thể cung cấp:

```c
ax_log(...)
ax_panic(...)
ax_diag_snapshot(...)
```

nhưng không phải core language requirement.

---

# 602.215. Foreign library integration

C/C++ library có thể gửi diagnostic event vào Axiom logger qua adapter.

---

# 602.216. Native OS logging

Platform adapter có thể gửi:

```text
Windows Event Log
syslog
journald
Apple unified logging
Android log
```

nhưng đây là optional sink.

Core vẫn hoạt động không có chúng.

---

# 602.217. No mandatory daemon

Axiom runtime không yêu cầu:

```text
logging daemon
agent
collector
service
```

để application chạy.

---

# 602.218. Remote export

Remote export là plugin/adapter:

```text
HTTP
TCP
Unix socket
named pipe
```

Không nằm trong minimal runtime.

---

# 602.219. Network failure isolation

Remote exporter failure không được crash application.

---

# 602.220. Remote buffering

Nếu remote exporter có buffer:

```text
bounded
persistent optional
drop policy configurable
```

---

# 602.221. Security boundary

Diagnostic runtime phải coi:

```text
application data
user data
config
environment
```

là potentially sensitive.

---

# 602.222. Redaction pipeline

Trước khi event rời process:

```text
event
→ classify fields
→ redact
→ serialize
→ sink
```

---

# 602.223. Redaction precedence

Explicit:

```text
@secret
```

phải override generic formatter.

---

# 602.224. Redaction failure

Nếu không chắc field có an toàn:

```text
redact
```

thay vì expose.

---

# 602.225. Diagnostic configuration schema

BOOTSTRAP-601 phải cho phép cấu hình:

```text
logging
diagnostics
crash
metrics
tracing
retention
privacy
```

nhưng 602 định nghĩa semantics của các field đó.

---

# 602.226. Example configuration

```text
diagnostics:
  logging:
    level: info
    format: json
    sink: file

  crash:
    enabled: true
    directory: "${app.data}/crashes"
    max_count: 10

  tracing:
    enabled: false

  metrics:
    enabled: true
```

Syntax chỉ mang tính minh họa; AXCFG là format chuẩn của 601.

---

# 602.227. Runtime initialization

Initialization order:

```text
process
→ emergency diagnostics
→ platform diagnostics
→ config
→ logger
→ metrics
→ tracing
→ application
```

Crash reporting phải sẵn sàng càng sớm càng tốt.

---

# 602.228. Early startup crash

Nếu application crash trước logger hoàn chỉnh:

```text
emergency diagnostics
```

phải vẫn cố tạo artifact tối thiểu.

---

# 602.229. Late shutdown crash

Nếu crash trong shutdown:

```text
crash pipeline
```

vẫn hoạt động.

---

# 602.230. Initialization failure

Nếu diagnostic subsystem không initialize được:

```text
application may continue
```

trừ crash handler tối thiểu nếu platform bắt buộc.

---

# 602.231. Runtime invariant

Các invariant quan trọng:

```text
diagnostic subsystem must never be the sole reason normal application crashes
```

và:

```text
crash handler must not depend on the normal application lifecycle
```

---

# 602.232. Crash artifact completeness

Runtime phải cố gắng ghi theo thứ tự:

```text
header
identity
exception
thread
registers
stack
modules
emergency logs
context
state/config identity
```

Nếu bị terminate giữa chừng, artifact vẫn phải parse được nếu có thể.

---

# 602.233. Partial artifact

Reader phải hỗ trợ:

```text
complete
partial
truncated
```

artifact.

---

# 602.234. Crash artifact state machine

```text
CREATED
→ WRITING
→ FINALIZING
→ COMPLETE
```

hoặc:

```text
WRITING
→ PARTIAL
```

---

# 602.235. Crash finalization

Marker cuối:

```text
COMPLETE
```

được ghi sau checksum.

---

# 602.236. Artifact recovery

Startup có thể scan:

```text
*.axcrash.tmp
```

và đánh dấu partial.

---

# 602.237. Crash report lifecycle

```text
capture
→ local storage
→ optional processing
→ optional upload
→ retention cleanup
```

Runtime chỉ bắt buộc:

```text
capture + local storage
```

nếu platform cho phép.

---

# 602.238. Diagnostic state machine

Runtime:

```text
DISABLED
INITIALIZING
READY
DEGRADED
CRASHING
TERMINATING
```

---

# 602.239. DEGRADED mode

Ví dụ:

```text
file sink unavailable
```

Runtime chuyển:

```text
READY → DEGRADED
```

nhưng vẫn log qua emergency/console nếu có thể.

---

# 602.240. Crash transition

```text
READY
→ CRASHING
→ TERMINATING
```

Không quay về READY.

---

# 602.241. Thread safety invariant

Mọi public diagnostic API phải được phân loại:

```text
thread-safe
thread-confined
crash-safe
```

---

# 602.242. Async safety invariant

Không được capture một mutable async context đã hết lifetime.

---

# 602.243. Lifetime

Diagnostic context phải sống ít nhất bằng scope của execution context.

---

# 602.244. Context nesting

Cho phép:

```text
request
  └── database
       └── query
```

Child context override field cùng tên hoặc inherit tùy policy.

---

# 602.245. Context merge

Default:

```text
child overrides parent
```

Parent context không bị mutate.

---

# 602.246. Context size

Context phải có:

```text
MAX_FIELDS
MAX_BYTES
MAX_DEPTH
```

---

# 602.247. Context serialization

Chỉ fields marked/exportable mới được đưa vào external artifact nếu privacy policy yêu cầu.

---

# 602.248. Diagnostics and modules

Module có thể register:

```text
module_name
module_version
diagnostic categories
error codes
health checks
```

---

# 602.249. Module unload

Nếu dynamic module unload:

```text
diagnostic registrations
```

phải được deregister trước khi unload metadata.

---

# 602.250. No dangling diagnostic callbacks

Runtime phải đảm bảo callback không còn trỏ vào unloaded module.

---

# 602.251. Testability

Diagnostics subsystem phải có:

```text
MockSink
MemorySink
FakeClock
FakeCrashBackend
FakeSymbolBackend
```

---

# 602.252. Deterministic tests

Tests có thể inject:

```text
clock
process identity
thread identity
build identity
filesystem
```

để tạo artifact deterministic.

---

# 602.253. Crash testing

Test suite phải có simulated:

```text
panic
fatal
assert
exception
signal
stack failure
sink failure
disk full
permission denied
```

---

# 602.254. Crash fuzzing

Crash artifact reader phải được fuzz test với:

```text
random bytes
truncated records
invalid lengths
unknown fields
corrupt checksum
```

---

# 602.255. Log fuzzing

Structured serializer phải được fuzz với:

```text
nested values
huge strings
invalid UTF-8 bytes
recursive objects
large arrays
```

---

# 602.256. UTF-8

Axiom string mặc định UTF-8.

Diagnostics phải bảo toàn UTF-8.

Invalid external byte sequences phải được biểu diễn an toàn, không crash serializer.

---

# 602.257. Binary data

Binary field phải có explicit type:

```text
Bytes
```

không được giả định là UTF-8.

---

# 602.258. Unicode normalization

Runtime không tự normalize text unless explicitly requested.

---

# 602.259. Log injection

Text sink phải chống:

```text
newline injection
terminal control sequence
```

nếu security mode enabled.

---

# 602.260. Terminal safety

Console sink có thể escape:

```text
ANSI
control characters
```

---

# 602.261. File safety

Log filename phải reject:

```text
path traversal
NUL
invalid separators
```

---

# 602.262. Resource exhaustion

Mọi diagnostic input phải bounded:

```text
events
fields
bytes
attachments
depth
queue
files
```

---

# 602.263. Global limits

Runtime config:

```text
max_log_event_bytes
max_queue_bytes
max_context_bytes
max_crash_artifact_bytes
```

---

# 602.264. Per-event limits

Mỗi event có:

```text
max_fields
max_string_bytes
max_array_items
```

---

# 602.265. Graceful degradation

Nếu event vượt giới hạn:

```text
truncate
```

thay vì fail application.

---

# 602.266. Fatal event overflow

Fatal event phải được ưu tiên.

Nếu event quá lớn:

```text
minimal fatal representation
```

được ghi thay vì bỏ toàn bộ.

---

# 602.267. Crash artifact overflow

Nếu artifact vượt quota:

```text
drop low-priority sections
```

theo thứ tự:

```text
verbose attachments
metrics
traces
old logs
extended metadata
```

Stack/exception identity phải được ưu tiên.

---

# 602.268. Priority order

Crash artifact priority:

1. crash identity;
2. build identity;
3. exception;
4. thread;
5. registers;
6. stack;
7. modules;
8. emergency logs;
9. context;
10. state/config identity;
11. metrics;
12. optional attachments.

---

# 602.269. Logging semantics

Logging không phải transactional.

Một event có thể:

```text
dropped
truncated
reordered
```

theo policy.

---

# 602.270. Diagnostic guarantee levels

API documentation phân biệt:

```text
best-effort
at-least-local-attempt
fatal-required
```

Không được hứa delivery tuyệt đối nếu process crash.

---

# 602.271. Fatal guarantee

Runtime phải cố gắng ghi fatal diagnostic trước termination nhưng platform có thể ngăn cản.

---

# 602.272. Crash guarantee

Không platform nào được coi là đảm bảo 100%.

Spec phải dùng:

```text
best effort
```

và xác định fallback.

---

# 602.273. Performance target

Logging disabled:

```text
near-zero overhead
```

Counter:

```text
atomic fast path
```

Context:

```text
bounded
```

Crash handler:

```text
bounded work
```

---

# 602.274. Startup cost

Diagnostic initialization phải có:

```text
O(number_of_enabled_features)
```

chi phí.

Không scan toàn bộ filesystem khi startup trừ khi cleanup policy yêu cầu.

---

# 602.275. Memory target

Minimal diagnostic runtime phải có footprint nhỏ và compile/link dead-strip được.

Không có fixed large heap requirement cho mọi application.

---

# 602.276. No hidden threads

`AsyncLogger`, exporters hoặc watchdog chỉ tạo thread khi feature được enable.

---

# 602.277. No hidden network

Diagnostics không mở socket nếu network exporter không được enable.

---

# 602.278. No hidden persistence

Diagnostics không ghi disk ngoài:

```text
configured log sink
configured crash artifact
```

---

# 602.279. No implicit telemetry

Axiom runtime không gửi telemetry ra ngoài theo mặc định.

---

# 602.280. Application ownership

Application kiểm soát:

```text
what is logged
where it goes
retention
privacy
remote export
```

Runtime chỉ cung cấp safe primitive.

---

# 602.281. Framework ownership

Framework có thể xây:

```text
HTTP middleware
database tracing
GUI diagnostics
GPU diagnostics
```

trên primitive 602.

---

# 602.282. Compiler diagnostics linkage

Compiler error/runtime error có thể dùng cùng:

```text
error code
source location
build ID
module identity
```

---

# 602.283. Runtime error identity

Runtime error:

```text
AXE-XXXX
```

hoặc equivalent stable numeric identity.

Compiler có namespace riêng.

---

# 602.284. Error registry

Axiom standard library có registry machine-readable:

```text
error code
description
severity
recoverability
```

---

# 602.285. Recoverability metadata

Error có thể khai báo:

```text
recoverable
retryable
fatal
configuration
permission
resource
```

---

# 602.286. Retry metadata

Diagnostics có thể ghi:

```text
retryable = true
```

nhưng runtime không tự retry application operation.

---

# 602.287. Health and errors

Health check có thể map:

```text
error → degraded
fatal → failed
```

nhưng application vẫn quyết định policy.

---

# 602.288. Metrics and logs correlation

Metric event có thể reference:

```text
metric_id
```

Log không cần duplicate metric value unnecessarily.

---

# 602.289. Trace and logs correlation

Log trong active span tự động có:

```text
trace_id
span_id
```

nếu tracing enabled.

---

# 602.290. Metrics and traces

Metrics không cần chứa full trace ID mặc định để tránh cardinality explosion.

---

# 602.291. Correlation propagation

Axiom networking libraries phía trên có thể propagate:

```text
trace context
request ID
```

qua protocol-specific metadata.

---

# 602.292. Core neutrality

BOOTSTRAP-602 không định nghĩa HTTP-specific tracing headers.

---

# 602.293. Logging macros/intrinsics

Compiler có thể hỗ trợ:

```axiom
@log
@trace
@metric
```

annotation để giảm boilerplate.

---

# 602.294. Compiler-generated diagnostics

Compiler có thể tự generate events:

```text
runtime module loaded
allocator exhausted
task panic
```

nhưng chỉ khi build profile cho phép.

---

# 602.295. Runtime invariant diagnostics

Internal invariant violation phải tạo:

```text
fatal diagnostic
```

với:

```text
invariant ID
source location
build ID
```

---

# 602.296. No source-code leakage

Production binary không bắt buộc chứa toàn bộ source.

Debug metadata có thể externalize.

---

# 602.297. Symbol server

Symbol server/client không thuộc core runtime.

Toolchain có thể hỗ trợ:

```text
local symbol directory
remote symbol provider
```

ở layer tooling.

---

# 602.298. Reproducible diagnostics

Build reproducibility nên giữ:

```text
stable build ID
stable event schemas
stable symbol mapping
```

khi inputs giống nhau.

---

# 602.299. Reproducible crash analysis

Cùng:

```text
binary
symbols
crash addresses
```

phải cho phép tạo cùng logical stack trace.

---

# 602.300. End-to-end diagnostic flow

Normal:

```text
application
→ log/trace/metric
→ context
→ sink
```

Failure:

```text
application
→ exception/panic
→ crash handler
→ emergency buffer
→ stack/registers
→ state/config identity
→ crash artifact
→ terminate
```

---

# 602.301. Relationship with BOOTSTRAP-600

BOOTSTRAP-600 cung cấp:

```text
application state
session
checkpoint
recovery
```

BOOTSTRAP-602 chỉ tham chiếu:

```text
last checkpoint
state generation
```

Nó không sở hữu state.

---

# 602.302. Relationship with BOOTSTRAP-601

BOOTSTRAP-601 cung cấp:

```text
configuration
secrets
environment
deployment identity
```

BOOTSTRAP-602 chỉ consume:

```text
config fingerprint
profile
deployment ID
redaction metadata
```

Nó không sở hữu configuration.

---

# 602.303. Boundary invariant

Không được xảy ra:

```text
logger mutates config
logger mutates checkpoint
config reload destroys logger state
crash report modifies application state
```

---

# 602.304. Diagnostic transaction

Crash reporting không được tham gia application transaction.

---

# 602.305. Crash and checkpoint

Nếu checkpoint vừa hoàn tất trước crash:

```text
checkpoint_id
```

được ghi vào artifact.

Nếu checkpoint đang commit:

```text
checkpoint state
```

được ghi nếu biết được.

---

# 602.306. Crash during checkpoint

BOOTSTRAP-600 chịu trách nhiệm atomicity của checkpoint.

BOOTSTRAP-602 chỉ ghi:

```text
checkpoint operation active
```

nếu available.

---

# 602.307. Crash during config reload

Artifact có thể ghi:

```text
config_reload_in_progress = true
old_config_fingerprint
new_config_schema
```

nhưng không ghi secret.

---

# 602.308. Diagnostic snapshot consistency

Snapshot nên lấy:

```text
point-in-time metadata
```

nhưng không yêu cầu stop-the-world.

---

# 602.309. Partial consistency

Nếu các subsystem thay đổi trong lúc snapshot:

```text
snapshot_generation
```

giúp consumer biết snapshot không atomic toàn hệ thống.

---

# 602.310. Runtime status API

```axiom
runtime.diagnostics.status()
```

trả:

```text
enabled
state
queue_depth
dropped_events
sink_status
crash_storage
```

---

# 602.311. Logger status

```axiom
logger.status()
```

---

# 602.312. Crash status

```axiom
crash.status()
```

---

# 602.313. Trace status

```axiom
trace.status()
```

---

# 602.314. Metrics status

```axiom
metrics.status()
```

---

# 602.315. Health status

```axiom
health.status()
```

---

# 602.316. Unified status

```axiom
diagnostics.status()
```

có thể trả tất cả status trong một snapshot.

---

# 602.317. Status object

Status object phải immutable snapshot.

Không expose internal mutable runtime state.

---

# 602.318. Diagnostic command line

Axiom CLI có thể hỗ trợ:

```text
ax diag inspect
ax diag logs
ax diag metrics
ax diag health
ax diag crash
```

---

# 602.319. Running-process diagnostics

Nếu application hỗ trợ IPC diagnostic endpoint, CLI có thể attach.

Core runtime không bắt buộc IPC.

---

# 602.320. Secure diagnostic endpoint

Nếu enabled:

```text
authentication
authorization
local-only default
```

phải được áp dụng.

---

# 602.321. No unauthenticated remote diagnostics

Runtime không tự mở remote diagnostics endpoint.

---

# 602.322. Diagnostic command permissions

Sensitive commands:

```text
memory dump
thread dump
config inspection
```

phải yêu cầu explicit permission.

---

# 602.323. Memory dump

Full memory dump không phải default.

Đây là optional debugging feature.

---

# 602.324. Sensitive memory

Nếu memory dump enabled, warning phải nêu rằng nó có thể chứa:

```text
credentials
user data
keys
```

---

# 602.325. Production policy

Production default:

```text
no full memory dump
```

---

# 602.326. Stack-only dump

Đây là default safer diagnostic primitive.

---

# 602.327. Thread dump

Thread dump có thể được tạo mà không dump arbitrary memory.

---

# 602.328. Deadlock dump

Nếu enabled:

```text
lock graph
waiting threads
owners
```

---

# 602.329. Runtime profiler

Profiling là separate subsystem nhưng có thể consume diagnostic context.

Không biến profiler thành mandatory 602 component.

---

# 602.330. Sampling profiler integration

Nếu enabled, profiler có thể correlate:

```text
thread
task
span
module
```

---

# 602.331. Event bus

Không tạo một generic event bus khổng lồ trong core.

Logging/tracing/metrics nên có data path riêng.

---

# 602.332. Avoid abstraction overdesign

Không yêu cầu mọi diagnostic subsystem implement cùng một giant interface.

Mỗi subsystem có API nhỏ.

---

# 602.333. Core interfaces

Minimal interfaces:

```text
LogSink
CrashBackend
SymbolBackend
MetricExporter
TraceExporter
```

---

# 602.334. Exporter abstraction

Exporters phải tách khỏi producer API.

---

# 602.335. Export batching

Exporter có thể batch:

```text
logs
spans
metrics
```

nhưng core không bắt buộc.

---

# 602.336. Export failure

Exporter failure:

```text
retry
drop
fallback
```

theo bounded policy.

---

# 602.337. Retry limits

Không retry vô hạn.

---

# 602.338. Diagnostic shutdown

Shutdown sequence:

```text
stop accepting normal events
drain queues
flush sinks
finalize metrics
finalize traces
close files
release resources
```

Crash path bỏ qua normal shutdown sequence.

---

# 602.339. Shutdown timeout

Async diagnostic shutdown phải có timeout.

---

# 602.340. Forced shutdown

Nếu timeout:

```text
drop remaining diagnostic events
terminate subsystem
```

Không block application indefinitely.

---

# 602.341. Application termination

Application exit code có thể correlate với fatal diagnostic code.

---

# 602.342. Exit code

Crash handler phải giữ native exit semantics khi platform yêu cầu.

---

# 602.343. Panic exit

Axiom-defined panic có thể sử dụng reserved exit code khi platform cho phép.

---

# 602.344. Signal preservation

Nếu POSIX signal crash handler can safely re-raise signal sau khi artifact capture:

```text
original signal semantics preserved
```

là preferred.

---

# 602.345. Windows exception preservation

Windows backend phải cố gắng preserve exception code/context khi policy yêu cầu.

---

# 602.346. Debugger behavior

Nếu debugger attached:

```text
runtime may defer to debugger
```

theo debug policy.

Không được nuốt breakpoint/debug exception.

---

# 602.347. Debug build behavior

Development crash có thể:

```text
print
break
artifact
```

theo debugger state.

---

# 602.348. Production behavior

Production không break debugger nếu debugger không được attach.

---

# 602.349. Assertions

Assertion failure phải có:

```text
assertion expression
source location
message
```

nếu metadata available.

---

# 602.350. Assertion redaction

Expression output không được tự động dump arbitrary values nếu có risk sensitive data.

---

# 602.351. Diagnostic API stability

Public API phải tránh expose:

```text
platform structs
allocator internals
OS exception structs
```

trực tiếp.

---

# 602.352. Platform abstraction

Use:

```text
AxPlatformCrashInfo
AxPlatformStack
```

logical structures.

---

# 602.353. Architecture abstraction

Architecture-specific registers nằm trong tagged union:

```text
X86_64
ARM64
WASM
...
```

---

# 602.354. Unknown architecture

Reader phải giữ:

```text
raw architecture ID
```

nếu không hiểu architecture.

---

# 602.355. Crash artifact compression

Có thể nén artifact.

Default có thể:

```text
uncompressed
```

để crash path đơn giản.

Compression là post-process option.

---

# 602.356. Crash artifact encryption

Optional.

Nếu enabled:

```text
application-controlled key provider
```

không hard-code key trong runtime.

---

# 602.357. Encryption failure

Nếu encryption required nhưng không thể encrypt:

```text
artifact must not be written unencrypted
```

nếu security policy strict.

---

# 602.358. Privacy policy

Diagnostic privacy policy phải có:

```text
field classification
retention
export permission
```

---

# 602.359. Data classification

Fields có thể:

```text
Public
Internal
Sensitive
Secret
```

`Secret` luôn redacted khỏi ordinary diagnostics.

---

# 602.360. Runtime classification

Primitive:

```axiom
diagnostic.classify(value, .sensitive)
```

---

# 602.361. Serialization policy

Serializer nhận:

```text
value + classification + sink policy
```

---

# 602.362. Sink-specific policy

Một field có thể:

```text
visible in local debug
redacted in production file
never exported remotely
```

---

# 602.363. Audit logging

Audit log có thể dùng logger nhưng phải có:

```text
durability policy
tamper evidence optional
restricted access
```

Audit semantics thuộc higher-level security layer.

---

# 602.364. Diagnostic schema registry

Compiler/toolchain có thể export:

```text
events
metrics
error codes
fields
```

thành:

```text
.axdiag
```

schema artifact.

---

# 602.365. `.axdiag`

Logical contents:

```text
event schemas
metric schemas
error registry
trace metadata
redaction metadata
build identity
```

---

# 602.366. AI tooling

AI tooling có thể đọc:

```text
.axdiag
.axsym
.axcrash
```

để map:

```text
runtime failure
→ source
→ function
→ event
→ build
```

---

# 602.367. Compiler artifact graph

Diagnostic artifacts có thể reference:

```text
binary
symbols
source map
diagnostic schema
```

bằng `build_id`.

---

# 602.368. No source upload requirement

Runtime không yêu cầu source code để tạo crash artifact.

---

# 602.369. Offline debugging

Một `.axcrash` + matching symbols phải đủ để tạo stack report ở máy khác trong điều kiện metadata đầy đủ.

---

# 602.370. Crash reproducibility

Artifact không phải reproduction environment.

Nó chỉ là diagnostic evidence.

---

# 602.371. Diagnostic evidence hierarchy

Ưu tiên:

```text
exception
registers
stack
modules
build
logs
context
metrics
state/config identity
attachments
```

---

# 602.372. Minimal crash payload

Nếu storage cực kỳ hạn chế:

```text
magic
version
build_id
exception
instruction_pointer
stack
timestamp
```

là minimum viable artifact.

---

# 602.373. Embedded crash buffer

Embedded target có thể lưu:

```text
fixed binary crash record
```

vào reserved memory.

---

# 602.374. Restart recovery

Sau reboot, bootloader/application có thể đọc crash record nếu platform cho phép.

---

# 602.375. Persistent crash record ownership

Persistence implementation thuộc platform/state integration, không phải application state snapshot.

---

# 602.376. Crash record clearing

Sau khi successfully exported/processed:

```text
clear
```

theo platform policy.

---

# 602.377. Multiple crash records

Ring storage cho phép giữ nhiều crash nếu reboot loop xảy ra.

---

# 602.378. Crash storm

Nếu application crash liên tục:

```text
bounded retention
```

ngăn crash artifacts làm đầy storage.

---

# 602.379. Rate limiting

Crash artifact generation có thể rate-limit theo:

```text
time
count
storage
```

nhưng fatal diagnostic tối thiểu vẫn phải được cố gắng ghi.

---

# 602.380. Diagnostic storm

Logging storm cũng phải có:

```text
rate limit
sampling
drop
aggregation
```

---

# 602.381. Log sampling

Có thể sample repeated event:

```text
100000 identical warnings
```

thành:

```text
event repeated 100000 times
```

---

# 602.382. Deduplication

Deduplication key:

```text
event_id
selected fields
```

không dùng full arbitrary payload mặc định.

---

# 602.383. Aggregated warning

Runtime có thể ghi:

```text
event
count
first_seen
last_seen
```

---

# 602.384. No semantic mutation

Sampling/deduplication chỉ ảnh hưởng diagnostics, không ảnh hưởng application behavior.

---

# 602.385. Logging ordering under async

Async logger không đảm bảo global ordering tuyệt đối giữa producers.

Mỗi event giữ:

```text
producer sequence
timestamp
thread
```

---

# 602.386. Flush barrier

API:

```axiom
logger.flush()
```

phải cung cấp defined completion semantics.

---

# 602.387. Flush result

Có thể trả:

```text
success
partial
failed
timeout
```

---

# 602.388. Crash flush

Crash flush phải có bounded timeout/work.

---

# 602.389. No infinite flush

Fatal path không được chờ network exporter vô thời hạn.

---

# 602.390. Exporter isolation

Remote exporter phải nằm ngoài critical crash path.

---

# 602.391. Crash artifact first

Khi crash:

```text
local artifact
```

được ưu tiên hơn:

```text
remote upload
```

---

# 602.392. Post-crash uploader

Application startup có thể upload previous crash artifacts.

Đây là higher-level service.

---

# 602.393. Startup crash recovery

Nếu previous artifact tồn tại:

```text
startup diagnostics
```

có thể expose:

```text
previous_crash_available = true
```

---

# 602.394. User-facing recovery

Runtime không tự quyết định:

```text
restore
safe mode
reset config
```

Đó là application policy.

---

# 602.395. Diagnostic notification

Application có thể thông báo:

```text
previous crash detected
```

nhưng runtime không ép UI.

---

# 602.396. Test contract

Compiler/runtime CI phải kiểm tra:

```text
disabled logging generates no event path
enabled logging is thread-safe
crash handler does not allocate on emergency path
crash artifact is parseable
secret is redacted
config fingerprint is included
state checkpoint identity is included
```

---

# 602.397. Performance benchmarks

Benchmarks:

```text
disabled log
enabled log
async log
counter increment
span begin/end
context lookup
crash artifact creation
stack capture
```

---

# 602.398. Contention benchmarks

Test:

```text
1 thread
2
4
8
16
32+
```

để phát hiện global lock bottleneck.

---

# 602.399. Memory benchmarks

Measure:

```text
static footprint
runtime heap
queue memory
per-thread buffer
crash buffer
```

---

# 602.400. Binary size benchmarks

Build:

```text
diagnostics disabled
minimal
standard
full
```

và đo size contribution.

---

# 602.401. Dead-strip validation

CI phải chứng minh feature disabled không kéo dependency code vào binary nếu linker hỗ trợ dead stripping.

---

# 602.402. Security tests

Test:

```text
secret redaction
path traversal
log injection
attachment limit
artifact quota
corrupt artifact
unauthorized diagnostic endpoint
```

---

# 602.403. Crash tests

Native CI phải intentionally trigger:

```text
panic
assert
illegal instruction
access violation
stack overflow
abort
```

trong controlled test process.

---

# 602.404. Platform matrix

Tối thiểu:

```text
Windows x86_64
Windows ARM64
Linux x86_64
Linux ARM64
macOS x86_64
macOS ARM64
Android ARM64
iOS ARM64
WASM
```

Các backend không hỗ trợ đầy đủ phải khai báo capability.

---

# 602.405. Capability model

Runtime exposes:

```axiom
diagnostics.capabilities()
```

Ví dụ:

```text
stack_capture = true
register_capture = true
symbolization = false
file_artifact = true
memory_dump = false
```

---

# 602.406. Capability negotiation

Application không được assume platform capability.

---

# 602.407. Graceful unsupported operation

Ví dụ:

```axiom
diagnostics.capture_registers()
```

có thể trả:

```text
Unsupported
```

thay vì panic.

---

# 602.408. Native backend contract

Mỗi backend phải implement capability declaration.

---

# 602.409. Core fallback

Nếu backend unavailable:

```text
portable fallback
```

phải được sử dụng nếu có.

---

# 602.410. Portable stack fallback

Nếu native unwinder unavailable:

```text
frame-pointer walk
```

có thể được sử dụng nếu binary hỗ trợ.

---

# 602.411. Frame pointer policy

Compiler có thể giữ frame pointer trong diagnostic build để cải thiện stack capture.

---

# 602.412. Release unwind metadata

Release build có thể dùng compact unwind metadata thay frame pointer để giảm overhead.

---

# 602.413. Compiler requirement

Compiler phải hỗ trợ debug/unwind metadata đủ cho target backend.

---

# 602.414. No mandatory exceptions

Axiom không cần exception-based error model chỉ để diagnostics.

Diagnostics phải hoạt động với:

```text
Result
panic
native exception
```

---

# 602.415. Interop exceptions

Foreign exception có thể được map thành:

```text
external_exception
```

và capture native stack nếu possible.

---

# 602.416. Runtime boundary

Crossing FFI boundary phải preserve diagnostic context nếu adapter hỗ trợ.

---

# 602.417. FFI crash

Nếu foreign code crash:

```text
Axiom crash backend
```

cố capture native stack/module information.

---

# 602.418. Signal-safe subset

POSIX crash backend phải xác định rõ API nào signal-safe.

---

# 602.419. Windows safe subset

Windows crash backend phải xác định rõ API nào safe trong exception context.

---

# 602.420. No undefined promise

Spec không được tuyên bố toàn bộ Axiom standard library là crash-safe.

Chỉ API explicitly marked `@crash_safe` mới được gọi trong crash handler.

---

# 602.421. Crash-safe metadata

Compiler-generated static metadata là preferred crash-path source.

---

# 602.422. Crash-safe event

Runtime có primitive:

```axiom
crash_log(event_id, primitive_fields...)
```

chỉ nhận field types an toàn.

---

# 602.423. Crash-safe field types

Allowed:

```text
integer
enum
fixed string
address
pointer-as-address
timestamp
```

Dynamic object không được phép.

---

# 602.424. Crash-safe formatting

Không yêu cầu general-purpose formatter.

---

# 602.425. Emergency record

Emergency record fixed layout:

```text
sequence
timestamp
thread
event_id
severity
small fields
```

---

# 602.426. Emergency ring capacity

Capacity compile/config-time selectable:

```text
4 KiB
16 KiB
64 KiB
256 KiB
...
```

---

# 602.427. Small runtime target

Embedded target có thể chọn:

```text
4 KiB emergency buffer
```

mà vẫn conform.

---

# 602.428. Full server target

Server có thể chọn:

```text
256 KiB+
```

nhưng không có hardcoded requirement.

---

# 602.429. Diagnostic object lifetime

Diagnostic objects không được giữ reference tới stack values sau scope.

---

# 602.430. String ownership

Async logger phải copy/own string data nếu source lifetime không đủ dài.

---

# 602.431. Zero-copy option

Advanced API có thể cho caller cung cấp immutable owned buffer.

---

# 602.432. Borrowing avoidance

Core diagnostics API không yêu cầu user quản lý pointer/reference lifetime phức tạp.

Runtime tự đảm bảo ownership khi queueing.

---

# 602.433. Alignment with Axiom memory model

Diagnostics phải phù hợp memory model của Axiom nhưng không ép developer dùng explicit pointer/reference cho ordinary logging.

---

# 602.434. Struct-only model

Diagnostic data types là `struct`.

Ví dụ:

```axiom
struct LogEvent { ... }
struct TraceContext { ... }
struct CrashInfo { ... }
```

Không cần class hierarchy.

---

# 602.435. Trait-based sinks

Behavior mở rộng bằng trait:

```axiom
trait LogSink { ... }
trait CrashBackend { ... }
```

phù hợp với struct-only OOP direction.

---

# 602.436. Method convention

Methods của diagnostic structs là ordinary functions với receiver-first semantics theo Axiom core model.

---

# 602.437. Override

Platform backend có thể override default trait behavior bằng implementation specialization/override mechanism của Axiom.

---

# 602.438. No inheritance tree

Không cần:

```text
BaseLogger
AdvancedLogger
AsyncLoggerBase
...
```

class hierarchy.

---

# 602.439. Composition

Logger được compose từ:

```text
policy
sink
buffer
formatter
context provider
```

---

# 602.440. Data-oriented design

Hot-path diagnostic structures phải ưu tiên:

```text
compact
cache-friendly
contiguous
bounded
```

---

# 602.441. False sharing

Per-thread counters/buffers phải tránh false sharing nếu implementation có thể.

---

# 602.442. Cache locality

Event hot path nên giữ metadata immutable/read-only.

---

# 602.443. Atomic memory ordering

Runtime implementation phải dùng weakest correct ordering.

Không mặc định `seq_cst` cho mọi counter.

---

# 602.444. Lock-free claim

Runtime chỉ gọi API `lock_free` khi implementation thực sự thỏa property trên target.

---

# 602.445. Platform variation

Một target có thể fallback từ lock-free sang bounded mutex.

API semantics vẫn giữ.

---

# 602.446. Deterministic shutdown

Logger flush phải có defined completion state.

---

# 602.447. Resource ownership

Diagnostic runtime owner:

```text
application runtime
```

Sinks/resources được release ở shutdown hoặc process termination.

---

# 602.448. No finalizer dependency

Không dựa vào GC finalizer để flush logs.

---

# 602.449. Explicit lifecycle

```axiom
diagnostics.init()
diagnostics.start()
diagnostics.flush()
diagnostics.stop()
```

có thể được runtime gọi tự động.

---

# 602.450. Automatic lifecycle

Normal application không bắt buộc gọi manual init.

Compiler/runtime startup có thể initialize automatically nếu diagnostics enabled.

---

# 602.451. Manual lifecycle

Low-level/freestanding application có thể quản lý lifecycle explicit.

---

# 602.452. Reinitialization

Diagnostics subsystem không mặc định cho phép:

```text
stop → start
```

nhiều lần nếu platform resources không hỗ trợ.

---

# 602.453. Hot reload

Config changes có thể hot-reload policy/sinks.

Không yêu cầu reload toàn bộ diagnostic runtime.

---

# 602.454. Schema compatibility

Event schema changes:

```text
additive fields → compatible
remove fields → versioned
change type → breaking
```

---

# 602.455. Event schema evolution

Event ID không được reuse cho semantic khác.

---

# 602.456. Metric schema evolution

Metric name không được reuse cho unit/type khác.

---

# 602.457. Trace schema

Span names/attributes có thể evolve nhưng phải giữ semantics rõ ràng.

---

# 602.458. Documentation generation

Compiler/tooling có thể generate diagnostic docs từ annotations.

---

# 602.459. Source annotations

Ví dụ:

```axiom
@event("db.connection.failed")
fn connect(...) ...
```

Compiler có thể validate event schema.

---

# 602.460. Event field validation

Toolchain có thể reject:

```text
duplicate field
invalid type
invalid secret classification
```

---

# 602.461. Metric validation

Compiler/tooling có thể kiểm tra:

```text
unit
type
label definitions
```

---

# 602.462. Trace validation

Compiler/tooling có thể kiểm tra span attribute schema nếu declared.

---

# 602.463. Static diagnostic manifest

Build có thể tạo:

```text
application.axdiag
```

với toàn bộ static diagnostic schema.

---

# 602.464. Runtime manifest linkage

Crash artifact references:

```text
diag_manifest_id
```

nếu available.

---

# 602.465. Manifest ID

Có thể derive từ:

```text
build_id + diagnostic schema
```

---

# 602.466. Diagnostic artifact references

Artifact không duplicate static metadata quá mức.

Nó references build/symbol/diag manifests.

---

# 602.467. Offline bundle

Toolchain có thể tạo:

```text
.axbundle
```

gồm:

```text
crash
symbols
diag manifest
build manifest
```

---

# 602.468. AI debugging bundle

Bundle có thể được tối ưu để AI đọc:

```text
failure summary
stack
source mapping
relevant events
config identity
state identity
```

thay vì toàn bộ binary.

---

# 602.469. No automatic AI dependency

Runtime không phụ thuộc AI service.

---

# 602.470. Diagnostic extensibility

Third-party/framework code có thể add:

```text
custom event
custom metric
custom health check
custom attachment
```

nhưng không phá runtime invariants.

---

# 602.471. Extension isolation

Extension phải tuân:

```text
limits
privacy
lifecycle
thread safety
```

---

# 602.472. Extension metadata

Custom event namespace:

```text
vendor.module.event
```

để tránh collision.

---

# 602.473. Reserved namespaces

Axiom reserves:

```text
ax.*
axiom.*
runtime.*
compiler.*
```

---

# 602.474. Application namespaces

Application dùng:

```text
app.*
```

hoặc application-specific namespace.

---

# 602.475. Namespace validation

Tooling có thể reject event namespace collision.

---

# 602.476. Error namespace

Stable error codes cũng phải namespace.

---

# 602.477. Health namespace

Health checks có namespace tương tự.

---

# 602.478. Metric namespace

Metrics phải có application/module namespace để tránh collision.

---

# 602.479. Diagnostic API naming

Naming phải thống nhất:

```text
log.*
trace.*
metrics.*
health.*
diagnostics.*
crash.*
```

---

# 602.480. Standard library placement

Core language compiler không cần implement toàn bộ diagnostics semantics.

Standard runtime library cung cấp public API.

Compiler chỉ cung cấp:

```text
intrinsics
metadata
dead stripping
source mapping
unwind metadata
```

---

# 602.481. Runtime placement

Native runtime modules:

```text
runtime/diagnostics
runtime/log
runtime/crash
runtime/trace
runtime/metrics
```

---

# 602.482. Platform backend placement

```text
runtime/platform/windows/diagnostics
runtime/platform/linux/diagnostics
runtime/platform/macos/diagnostics
runtime/platform/android/diagnostics
runtime/platform/ios/diagnostics
runtime/platform/wasm/diagnostics
```

---

# 602.483. Compiler integration files

Compiler:

```text
compiler/diagnostics
compiler/debug-info
compiler/unwind
compiler/event-metadata
```

---

# 602.484. Tooling

CLI:

```text
tools/axdiag
tools/axcrash
tools/axsymbolize
```

có thể là một unified `ax diag`.

---

# 602.485. Build integration

Build profile:

```text
diagnostics = minimal|standard|full
symbols = embedded|external|none
```

---

# 602.486. Symbol packaging

Release packaging nên giữ:

```text
binary
symbols
manifest
```

tách biệt.

---

# 602.487. Build cache

Diagnostic metadata phải tham gia cache key khi nó ảnh hưởng binary.

---

# 602.488. Source unchanged

Nếu source và diagnostic build settings không đổi:

```text
cached compilation result
```

có thể reuse.

---

# 602.489. Build ID cache consistency

Cached binary phải giữ đúng build ID và diagnostic metadata.

---

# 602.490. ABI compatibility

Thay đổi diagnostic runtime ABI phải không âm thầm phá binary compatibility.

---

# 602.491. Runtime version

Artifact ghi:

```text
runtime_version
```

---

# 602.492. Compiler version

Artifact ghi:

```text
compiler_version
```

---

# 602.493. Language version

Artifact ghi:

```text
language_version
```

---

# 602.494. Standard library version

Artifact ghi:

```text
stdlib_version
```

---

# 602.495. Feature set

Artifact có thể ghi:

```text
feature_flags
```

nhưng không dump toàn bộ compiler configuration nếu không cần.

---

# 602.496. Reproduction hints

Crash report có thể ghi:

```text
optimization_level
debug_info_level
diagnostic_level
target_triple
```

---

# 602.497. No secret compiler flags

Build metadata phải redacted nếu compiler command chứa secret.

---

# 602.498. Command-line privacy

Runtime không tự ghi full process command line nếu platform policy cho rằng nó có thể chứa secret.

---

# 602.499. Environment privacy

Environment capture phải opt-in hoặc filtered.

---

# 602.500. Core invariant summary

BOOTSTRAP-602 phải bảo đảm:

```text
1. Logging is structured.
2. Disabled logging is near-zero cost.
3. Diagnostic memory is bounded.
4. Crash handling does not depend on normal application lifecycle.
5. Crash artifacts are versioned.
6. Stack/build identity are preserved.
7. Secrets are never emitted by default.
8. Config identity links to BOOTSTRAP-601.
9. State/checkpoint identity links to BOOTSTRAP-600.
10. No mandatory network service exists.
11. No mandatory third-party observability library exists.
12. Platform differences are isolated behind native backends.
13. Runtime can degrade gracefully.
14. Diagnostic failures do not normally crash the application.
15. Full observability can be stripped from minimal binaries.
```

---

# 602.501. Acceptance criteria

BOOTSTRAP-602 được coi là hoàn thành khi implementation có thể chứng minh:

### Logging

- [ ] structured events;
- [ ] levels;
- [ ] categories;
- [ ] compile-time elimination;
- [ ] runtime filtering;
- [ ] sync/async sinks;
- [ ] bounded queues;
- [ ] rotation;
- [ ] redaction.

### Diagnostics

- [ ] context;
- [ ] correlation IDs;
- [ ] metrics;
- [ ] tracing;
- [ ] health;
- [ ] snapshots;
- [ ] runtime statistics.

### Crash

- [ ] panic;
- [ ] fatal;
- [ ] native exception capture;
- [ ] stack capture;
- [ ] registers where supported;
- [ ] module inventory;
- [ ] crash artifact;
- [ ] emergency buffer;
- [ ] crash recursion guard.

### Tooling

- [ ] `.axcrash` reader;
- [ ] symbolization;
- [ ] build ID matching;
- [ ] diagnostic manifest;
- [ ] human-readable report;
- [ ] machine-readable report.

### Security

- [ ] secret redaction;
- [ ] bounded attachments;
- [ ] path safety;
- [ ] no implicit telemetry;
- [ ] no hidden network;
- [ ] privacy policies.

### Performance

- [ ] disabled log near-zero cost;
- [ ] bounded memory;
- [ ] no mandatory diagnostic thread;
- [ ] no mandatory heap;
- [ ] dead stripping;
- [ ] minimal runtime profile.

### Integration

- [ ] BOOTSTRAP-600 checkpoint linkage;
- [ ] BOOTSTRAP-601 config fingerprint linkage;
- [ ] deployment/build identity;
- [ ] native platform backends.

---

# 602.502. Reference implementation layering

Implementation nên chia:

```text
L0  Diagnostic primitives
L1  Logging
L2  Context
L3  Metrics
L4  Tracing
L5  Health
L6  Crash runtime
L7  Platform backends
L8  Symbolization
L9  Artifact tooling
L10 Export adapters
```

Không được để L0 phụ thuộc L9.

---

# 602.503. Dependency direction

Được phép:

```text
L9 → L8 → L7 → L6
              ↑
L5 → L4 → L3 → L2 → L1 → L0
```

Không được:

```text
core runtime → remote exporter
```

---

# 602.504. Minimal dependency graph

Minimal native application:

```text
Application
   ↓
Runtime Core
   ↓
Diagnostic primitives
   ↓
Platform backend
```

không kéo:

```text
network
JSON
HTTP
database
cloud SDK
```

nếu không dùng.

---

# 602.505. Architectural conclusion

BOOTSTRAP-602 biến diagnostics thành một **native runtime capability**, không phải một framework khổng lồ.

Thiết kế cuối cùng có ba đặc tính quan trọng:

```text
Fast when enabled
Almost free when disabled
Still useful when everything is failing
```

Đặc biệt, crash handling được thiết kế tách khỏi normal runtime lifecycle để bảo đảm rằng:

> hệ thống chẩn đoán vẫn còn khả năng hoạt động chính vào đúng thời điểm application không còn hoạt động bình thường.

---

# 602.506. Completion

**BOOTSTRAP-602 — NATIVE APPLICATION LOGGING, DIAGNOSTICS, CRASH REPORTING & OBSERVABILITY RUNTIME 5.0 — COMPLETE**

Đã hoàn thiện:

```text
Logging
Structured Events
Sinks
Async Logging
Emergency Buffer
Tracing
Metrics
Health
Diagnostic Context
Correlation
Crash Handling
Panic/Fatal
Stack Capture
Symbolization
Crash Artifact
Privacy/Redaction
Diagnostic Tooling
AI Diagnostic Metadata
Platform Backends
Performance Model
Security Model
Testing
Compiler Integration
BOOTSTRAP-600 Integration
BOOTSTRAP-601 Integration
```

**Task kế tiếp: `BOOTSTRAP-603`.**

:::