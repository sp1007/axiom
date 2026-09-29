# BOOTSTRAP-763 — AXLOGGING

**Title:** Native Structured Logging, Log Records, Log Levels, Sinks, Filtering, Rotation & Application Log Runtime 5.0  
**Namespace:** `AXLOGGING`  
**Phase:** Axiom Civilization Runtime / Native Logging Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

## 1. Mục tiêu

`AXLOGGING` cung cấp logging native thống nhất cho Axiom:

- structured logs;
- text logs;
- log levels;
- categories;
- fields;
- correlation;
- filtering;
- sinks;
- batching;
- buffering;
- rotation;
- retention;
- console/file/GUI/remote output;
- runtime configuration;
- source/build metadata;
- low-overhead logging;
- compile-time elimination;
- security-aware redaction.

Mục tiêu cốt lõi:

> Logging phải **rẻ khi disabled, có cấu trúc khi enabled, bounded khi hệ thống quá tải và không bao giờ trở thành security backdoor**.

---

# 2. Ranh giới với các subsystem khác

```text
AXLOGGING
    │
    ├── human/application logs
    ├── structured records
    ├── filtering
    └── sinks

AXOBSERVABILITY
    │
    ├── metrics
    ├── traces
    ├── telemetry
    └── health

AXAUDIT
    │
    └── security/accountability evidence

AXDIAGNOSTICS
    │
    ├── crash
    ├── dump
    ├── profiler
    └── failure investigation
```

Một log message không tự động trở thành audit event.

Một metric không được encode thành log chỉ để tái sử dụng logging infrastructure.

---

# 3. Kiến trúc

```text id="logarch"
Application / Runtime
        │
        ▼
   AXLOGGING API
        │
        ├──────────────┐
        ▼              ▼
  compile/runtime   context
    filtering       correlation
        │              │
        └──────┬───────┘
               ▼
        Log Record Builder
               │
               ▼
        Per-core Buffer
               │
          ┌────┴────┐
          ▼         ▼
       filter     batch
          │         │
          └────┬────┘
               ▼
             Sinks
        ┌──────┼─────────┐
        ▼      ▼         ▼
     console  file      remote
        │      │         │
        ▼      ▼         ▼
      GUI   AXSTORAGE AXNETWORK
```

---

# 4. Log record

Canonical record:

```text id="logrecord"
log_record {
    timestamp
    monotonic_time
    level
    logger_id
    category_id
    message
    fields
    process_id
    thread_id
    task_id
    trace_context
    source_location
    build_id
    sequence
}
```

---

# 5. Structured-first

Axiom không thiết kế logging dựa trên:

```text
printf("x=%d y=%d", x, y)
```

làm canonical representation.

Canonical representation là:

```text id="structured"
{
    message: "position updated",
    x: 10,
    y: 20
}
```

Text formatting là output concern.

---

# 6. Message

Message là human-readable description.

Có thể là static string:

```text id="msgstatic"
"connection established"
```

hoặc formatted message.

Nhưng fields phải được lưu riêng khi chúng có semantic value.

---

# 7. Typed fields

Supported:

```text id="fieldtypes"
BOOL
I8..I64
U8..U64
F32
F64
STRING
BYTES
UUID
PATH
DURATION
SIZE
IP_ADDRESS
ENUM
TIMESTAMP
ARRAY
```

Không serialize arbitrary object graph trong hot path.

---

# 8. Field key

Field descriptor:

```text id="fieldkey"
log_field_key {
    key_id
    name
    type
}
```

Static keys được intern/register.

---

# 9. Logger

```text id="logger"
logger {
    logger_id
    name
    category
    level
    policy
}
```

Application có thể tạo logger riêng.

---

# 10. Logger hierarchy

Ví dụ:

```text id="hierarchy"
app
 ├── app.http
 ├── app.database
 └── app.ui
```

Parent policy có thể được kế thừa.

---

# 11. Log levels

Canonical:

```text id="levels"
TRACE
DEBUG
INFO
NOTICE
WARN
ERROR
FATAL
```

Không bắt buộc mọi application phải sử dụng toàn bộ levels.

---

# 12. Level semantics

### TRACE

Chi tiết execution rất thấp.

### DEBUG

Thông tin phục vụ development/investigation.

### INFO

Thông tin vận hành bình thường.

### NOTICE

Sự kiện đáng chú ý nhưng không phải lỗi.

### WARN

Điều kiện bất thường nhưng execution vẫn tiếp tục.

### ERROR

Operation thất bại hoặc subsystem gặp lỗi.

### FATAL

Condition khiến process/runtime không thể tiếp tục theo policy.

`FATAL` **không tự động có nghĩa là AXPROCESS phải terminate**.

---

# 13. Level filtering

Nếu logger level là:

```text
INFO
```

thì:

```text
TRACE
DEBUG
```

không được evaluate đầy đủ.

---

# 14. Compile-time elimination

Compiler có thể loại bỏ:

```text
trace(...)
debug(...)
```

khi build profile xác định chúng luôn disabled.

Ví dụ:

```text id="compilelog"
if @log_enabled(DEBUG, "network") {
    log_debug(...);
}
```

được constant-fold.

---

# 15. Lazy arguments

Nếu level chưa enabled:

```text id="lazy"
log_debug("state = {}", expensive_state())
```

không được evaluate `expensive_state()` nếu compiler/runtime có thể chứng minh logging disabled.

Đây là yêu cầu performance quan trọng.

---

# 16. Logging macro/function semantics

Axiom compiler có thể cung cấp intrinsic:

```text id="intrinsic"
log_trace()
log_debug()
log_info()
log_notice()
log_warn()
log_error()
log_fatal()
```

Đây không nhất thiết phải là preprocessor macros.

---

# 17. Source metadata

Compiler có thể emit:

```text id="sourcemeta"
file
module
function
line
column
source_id
build_id
```

vào static log descriptor.

Không cần lưu source string đầy đủ trong mỗi record.

---

# 18. Build ID

Log record có thể chứa:

```text id="buildid"
build_id
module_id
```

giúp correlate binary version với log.

---

# 19. Sequence

Mỗi logger/process có thể duy trì:

```text id="sequence"
sequence_number
```

giúp phát hiện:

- reorder;
- loss;
- duplicate.

Sequence không thay thế AXAUDIT tamper-evident sequence.

---

# 20. Timestamp

Record có:

```text id="timestamps"
wall_clock
monotonic_clock
```

Wall clock dùng correlation.

Monotonic clock dùng ordering/duration.

---

# 21. Ordering

Global ordering của log từ nhiều CPU/thread **không được giả định**.

Canonical ordering:

```text id="ordering"
source
+
sequence
+
timestamp
```

Collector có thể reconstruct best-effort ordering.

---

# 22. Correlation

Log có thể chứa:

```text id="correlation"
trace_id
span_id
request_id
operation_id
parent_event_id
```

Các IDs phải là correlation metadata, không phải credentials.

---

# 23. Task correlation

`AXTASK` có thể cung cấp task ID.

Log runtime có thể tự động lấy:

```text id="taskctx"
process_id
task_id
```

mà không cần application truyền mỗi lần.

---

# 24. Async correlation

Async continuation có thể giữ trace/log context.

```text id="asyncctx"
request
  ↓
task
  ↓
await
  ↓
resume
  ↓
same correlation
```

Không cần giữ toàn bộ task object trong log record.

---

# 25. Context

```text id="logcontext"
log_context {
    logger
    level
    fields
    trace_context
    task_context
}
```

Context nên lightweight và immutable/read-mostly.

---

# 26. Scoped fields

Có thể:

```text id="scope"
with log.scope(request_id, user_action) {
    ...
}
```

mọi log trong scope kế thừa fields.

Scope kết thúc thì context trở lại trạng thái trước đó.

---

# 27. Scope implementation

Không nên allocate map cho mỗi scope.

Có thể dùng:

```text id="scopeimpl"
stack frame
small inline array
immutable linked context
```

Implementation choice.

---

# 28. Sensitive fields

Field classification:

```text id="classification"
PUBLIC
INTERNAL
SENSITIVE
SECRET
```

`SECRET` không được ghi plaintext.

---

# 29. Redaction

Policy có thể:

```text id="redaction"
DROP
REDACT
HASH
TRUNCATE
```

Ví dụ:

```text
password → [REDACTED]
```

---

# 30. No secret logging

AXLOGGING không được tự động log:

```text id="nosecret"
password
private_key
access_token
session_secret
credential_material
```

dù caller yêu cầu raw serialization.

---

# 31. Object serialization

Default:

```text id="object"
log(value)
```

chỉ được serialize object nếu object có explicit logging representation.

Không gọi arbitrary object introspection trong production hot path.

---

# 32. Custom formatter

Type có thể khai báo:

```text id="formatter"
@log_format
```

Compiler/runtime biết cách format type.

---

# 33. Binary canonical representation

Internally:

```text id="binary"
log_record
    ↓
typed binary fields
```

Text formatting chỉ xảy ra ở sink.

---

# 34. Text sink

Console sink có thể render:

```text id="console"
2026-09-24 18:42:10 INFO network
connection established
```

nhưng underlying record vẫn structured.

---

# 35. JSON sink

JSON output:

```text id="json"
{
  "level": "INFO",
  "category": "network",
  "message": "connection established"
}
```

JSON là interoperability format, không phải internal canonical format.

---

# 36. Binary sink

Native binary sink ưu tiên:

- compactness;
- speed;
- typed data;
- low CPU.

---

# 37. Sink

```text id="sink"
log_sink {
    sink_id
    type
    filter
    formatter
    destination
    queue
    policy
}
```

---

# 38. Sink types

Baseline:

```text id="sinktypes"
CONSOLE
DEBUGGER
FILE
MEMORY
IPC
REMOTE
GUI
CUSTOM
```

---

# 39. Sink independence

Một sink failure không được làm crash logger subsystem.

Ví dụ:

```text id="sinkfail"
remote sink unavailable
        ↓
local console continues
```

---

# 40. Sink filtering

Mỗi sink có filter riêng.

Ví dụ:

```text id="sinkfilter"
console → INFO+
file    → DEBUG+
remote  → WARN+
```

---

# 41. Category filtering

Có thể:

```text id="catfilter"
network.* = DEBUG
database.* = INFO
ui.* = WARN
```

---

# 42. Field filtering

Sink có thể chọn fields.

Ví dụ remote sink không nhận:

```text id="fieldfilter"
sensitive_context
```

dù local sink có authority.

---

# 43. Log pipeline

```text id="pipeline"
application
   ↓
intrinsic
   ↓
compile filter
   ↓
record
   ↓
local buffer
   ↓
runtime filter
   ↓
batch
   ↓
sink
```

---

# 44. Fast path

Enabled logging vẫn phải tránh:

- global mutex;
- heap allocation;
- synchronous network;
- synchronous disk;
- expensive formatting.

---

# 45. Disabled path

Ideal:

```text id="disabled"
branch
```

hoặc compile-time eliminated.

Chi phí gần zero.

---

# 46. Per-core buffer

```text id="percore"
CPU0 → ring0
CPU1 → ring1
CPU2 → ring2
CPU3 → ring3
```

Collector merge sau.

---

# 47. Ring buffer

Ring buffer:

```text id="ring"
fixed capacity
lock-minimized
bounded
```

Không tự tăng vô hạn khi producer nhanh hơn consumer.

---

# 48. Buffer overflow

Policies:

```text id="overflow"
DROP_NEW
DROP_OLD
SAMPLE
BLOCK
SPILL
```

Default operational logging nên tránh block application indefinitely.

---

# 49. Loss accounting

Logger expose:

```text id="loss"
records_dropped
bytes_dropped
buffer_overflow
sink_failures
```

qua AXOBSERVABILITY.

---

# 50. FATAL handling

FATAL record phải được ưu tiên flush theo policy.

Nhưng crash path không được phụ thuộc vào network.

---

# 51. Crash-safe logging

Trong crash:

```text id="crashlog"
application fault
    ↓
emergency log buffer
    ↓
AXDIAGNOSTICS
```

Không cố:

```text network
→ DNS
→ TLS
→ remote server
```

trong crash handler.

---

# 52. Emergency buffer

Reserved memory:

```text id="emergency"
emergency_log_buffer
```

được tạo trước khi crash.

Không heap allocate trong fatal path nếu có thể.

---

# 53. File sink

File sink cần:

```text id="filesink"
path
max_size
rotation_policy
retention
flush_policy
encoding
```

---

# 54. Rotation

Policies:

```text id="rotation"
SIZE
TIME
SIZE_OR_TIME
MANUAL
```

---

# 55. Rotation safety

Không overwrite active file trước khi sink mở file mới thành công.

---

# 56. Retention

Retention:

```text id="retention"
max_files
max_bytes
max_age
```

Bounded.

---

# 57. Storage integration

AXLOGGING không tự implement filesystem.

File sink sử dụng:

```text id="storage"
AXSTORAGE
```

---

# 58. Remote logging

Remote sink:

```text id="remote"
AXLOGGING
   ↓
AXCODEC
   ↓
AXSTREAM
   ↓
AXNETWORK
```

Không embed network stack.

---

# 59. Remote delivery

Policies:

```text id="delivery"
BEST_EFFORT
BUFFERED
AT_LEAST_ONCE
```

Exactly-once không phải baseline.

---

# 60. Remote backpressure

Khi network chậm:

```text id="backpressure"
application
    ↓
local buffer
    ↓
remote queue full
    ↓
drop/sample/spill
```

Không block application vô thời hạn.

---

# 61. Console integration

Console output có thể đi qua:

```text id="consoleintegration"
AXSHELL
AXDISPLAY
AXWINDOW
```

nhưng logging core không phụ thuộc GUI.

---

# 62. GUI integration

GUI viewer có thể subscribe:

```text id="guiviewer"
AXLOGGING
    ↓
local IPC/event stream
    ↓
AXAPPLICATION
    ↓
GUI
```

GUI không đọc trực tiếp logger internals.

---

# 63. Log query

Baseline query:

```text id="query"
level
category
time_range
process
task
trace_id
text
field
```

Query engine phải bounded.

---

# 64. Query ≠ database

AXLOGGING không trở thành general-purpose database.

Long-term archival/query có thể giao cho:

```text id="querybackend"
AXSTORAGE
AXDATABASE
```

---

# 65. In-memory viewer

Development profile có thể giữ:

```text id="memory"
last N records
```

với bounded memory.

---

# 66. Log retention classes

```text id="retentionclass"
EPHEMERAL
SHORT
STANDARD
ARCHIVE_REFERENCE
```

AXAUDIT retention semantics không dùng lại ở đây.

---

# 67. Configuration

`AXCONFIG` quản lý:

```text id="logconfig"
logging.default_level
logging.category_levels
logging.sinks
logging.buffer_size
logging.rotation
logging.redaction
```

AXLOGGING không tự sở hữu configuration database.

---

# 68. Runtime reconfiguration

Có thể thay đổi:

```text id="runtimecfg"
log level
sink activation
filter
sampling
rotation
```

nếu setting được đánh dấu reloadable.

---

# 69. Atomic configuration

Logger phải chuyển:

```text id="atomiccfg"
configuration N
      ↓
configuration N+1
```

atomic.

Một record không được thấy nửa cấu hình cũ/nửa mới.

---

# 70. Log sampling

Operational logs có thể sampling:

```text id="sampling"
TRACE
DEBUG
INFO
```

khi volume quá cao.

`ERROR`/`FATAL` mặc định không sampling trừ khi explicit policy.

---

# 71. Burst protection

Có thể giới hạn:

```text id="burst"
max_records_per_second
burst_capacity
```

để một loop lỗi không làm ngập toàn bộ logger.

---

# 72. Duplicate suppression

Có thể detect:

```text id="dup"
same message
same category
same fields
```

trong cửa sổ thời gian.

Output:

```text id="suppressed"
repeat_count
first_seen
last_seen
```

---

# 73. Do not hide errors

Suppression phải tạo metadata về số record bị suppress.

Không được làm operator tưởng rằng lỗi chưa từng xảy ra.

---

# 74. Correlation với metrics

Logger có thể emit:

```text id="logmetric"
error_count
warn_count
drop_count
```

qua AXOBSERVABILITY.

Nhưng metric canonical không được phụ thuộc vào text parsing.

---

# 75. Correlation với traces

Log record có:

```text id="tracecorrelation"
trace_id
span_id
```

nếu context tồn tại.

Trace viewer có thể link tới logs.

---

# 76. Correlation với diagnostics

Crash/failure record có thể chứa:

```text id="diagcorrelation"
diagnostic_id
crash_id
```

AXDIAGNOSTICS sở hữu artifact.

---

# 77. Correlation với audit

Security action có thể có:

```text id="auditcorrelation"
audit_event_id
```

AXLOGGING không tạo audit semantics.

---

# 78. Security

Đọc log có thể yêu cầu:

```text id="logcaps"
LOG_READ
LOG_READ_SENSITIVE
LOG_EXPORT
LOG_CONFIGURE
LOG_DELETE
```

Authorization qua AXSECURITY.

---

# 79. Log deletion

Application không được tùy ý xóa security-relevant audit records.

AXLOGGING log retention có thể xóa operational logs theo policy.

Audit records thuộc AXAUDIT.

---

# 80. Tamper evidence

AXLOGGING không cần hash-chain tất cả log.

Nếu cần evidence:

```text id="evidence"
AXLOGGING
   ↓
AXAUDIT
```

hoặc export sang evidence subsystem.

---

# 81. Privacy

Log policy có thể:

- redact;
- hash;
- truncate;
- drop.

Hashing không biến dữ liệu thành vô hại trong mọi trường hợp.

---

# 82. Tenant isolation

Log record có thể chứa:

```text id="tenant"
tenant_id
```

nhưng tenant isolation enforced bởi AXSECURITY.

---

# 83. Multi-process

Mỗi process có local logger instance.

System collector có thể aggregate qua IPC.

Không cần global shared-memory logger bắt buộc.

---

# 84. Multi-thread

Threads chia sẻ immutable logger descriptors.

Producer state có thể per-thread/per-core.

---

# 85. NUMA

Large systems:

```text id="numalog"
NUMA0 → buffers
NUMA1 → buffers
NUMA2 → buffers
```

Collector aggregate locally trước khi global merge.

---

# 86. Async sinks

File/network sinks chạy background tasks:

```text id="asyncsink"
producer
 ↓
ring
 ↓
AXTASK
 ↓
sink
```

Application không chờ I/O trong normal logging call.

---

# 87. Sink failure recovery

Remote/file sink:

```text id="recover"
FAILED
 ↓
RETRY
 ↓
ACTIVE
```

Retry bounded.

Không retry vô hạn với growing memory.

---

# 88. Logger shutdown

Shutdown:

```text id="shutdown"
stop new records
 ↓
drain buffers
 ↓
flush sinks
 ↓
close sinks
```

Có timeout.

---

# 89. Process termination

Nếu termination bất thường, emergency buffer/diagnostic integration cố gắng giữ các records cuối cùng trong khả năng cho phép.

Không đảm bảo lossless logging trong crash.

---

# 90. Deterministic simulation

Simulation có thể inject:

```text id="sim"
buffer_full
sink_failure
disk_full
network_delay
rotation_failure
sampling
clock_change
```

---

# 91. Replay

Replay chỉ tái tạo:

```text id="replay"
log records
filtering
formatting
sink behavior
```

Không execute application side effects.

---

# 92. Compiler metadata

Compiler có thể emit:

```text id="compilerlog"
log_site_id
source_id
file
line
column
message_template_id
field_descriptor[]
build_id
```

---

# 93. Message templates

Thay vì lưu full template trong mỗi record:

```text id="template"
message_template_id
arguments
```

Runtime/sink có thể resolve template.

Giúp giảm kích thước.

---

# 94. Stable log site

Mỗi static log site có:

```text id="logsite"
log_site_id
```

stable trong cùng build.

Không dùng log_site_id làm persistent security identity.

---

# 95. Native API — initialization

```text id="api1"
logging_init()
logging_shutdown()

logger_create()
logger_destroy()
logger_get()
```

---

# 96. Native API — emission

```text id="api2"
log_trace()
log_debug()
log_info()
log_notice()
log_warn()
log_error()
log_fatal()
```

---

# 97. Native API — structured builder

```text id="api3"
log_begin()
log_set_field()
log_set_message()
log_set_context()
log_emit()
log_abort()
```

Builder phải có bounded lifetime.

---

# 98. Native API — scope

```text id="api4"
log_scope_begin()
log_scope_set_field()
log_scope_end()
log_context_current()
```

---

# 99. Native API — logger configuration

```text id="api5"
logger_set_level()
logger_get_level()

logger_set_filter()
logger_get_filter()

logger_enable()
logger_disable()
```

Các API này phải qua appropriate security/configuration controls khi global/admin scope.

---

# 100. Native API — sinks

```text id="api6"
sink_create()
sink_configure()
sink_start()
sink_stop()
sink_flush()
sink_get_stats()
```

---

# 101. Native API — file sink

```text id="api7"
file_sink_create()
file_sink_set_path()
file_sink_set_rotation()
file_sink_set_retention()
file_sink_flush()
```

---

# 102. Native API — remote sink

```text id="api8"
remote_sink_create()
remote_sink_set_endpoint()
remote_sink_set_policy()
remote_sink_start()
remote_sink_stop()
```

Credentials do not belong in logging API; use appropriate security/auth mechanisms.

---

# 103. Native API — query

```text id="api9"
log_query_create()
log_query_set_filter()
log_query_execute()
log_query_next()
log_query_close()
```

---

# 104. Native API — statistics

```text id="api10"
logging_stats()
logger_stats()
sink_stats()
buffer_stats()
```

---

# 105. Native API — simulation

```text id="api11"
logging_simulate()
logging_replay()
logging_inject_fault()
```

---

# 106. ABI

```text id="abi"
AXLOGGING_ABI_1
```

Opaque handles:

```text id="handles"
logger_handle
log_context_handle
log_record_handle
sink_handle
query_handle
```

---

# 107. Error model

```text id="errors"
LOG_INVALID_LEVEL
LOG_INVALID_CATEGORY
LOG_INVALID_FIELD
LOG_FIELD_TYPE_MISMATCH
LOG_BUFFER_FULL
LOG_SINK_FAILURE
LOG_SINK_NOT_FOUND
LOG_PERMISSION_DENIED
LOG_SENSITIVE_DATA
LOG_FORMAT_FAILURE
LOG_QUERY_INVALID
LOG_QUERY_TIMEOUT
LOG_ROTATION_FAILURE
LOG_STORAGE_FAILURE
LOG_REMOTE_FAILURE
LOG_RESOURCE_LIMIT
LOG_ALREADY_CLOSED
LOG_INVALID_CONTEXT
LOG_CONFIGURATION_INVALID
LOG_SHUTDOWN
```

---

# 108. Performance target

### Disabled

Mục tiêu:

```text id="perfdisabled"
near-zero overhead
```

### Enabled

Mục tiêu:

```text id="perfenabled"
no mandatory heap allocation
no synchronous I/O
no global lock
no network operation
```

trên producer path.

---

# 109. Small record optimization

Các records nhỏ nên fit trong fixed inline buffer.

Ví dụ:

```text id="smallrecord"
level
logger_id
template_id
timestamp
few fields
```

có thể emit mà không heap allocation.

---

# 110. Large record

Record vượt inline capacity:

```text id="largerecord"
inline
  ↓
bounded side buffer
```

Nếu không đủ capacity:

```text id="largefail"
truncate/drop
```

theo policy.

---

# 111. Formatting cost

Không format text nếu sink không yêu cầu text.

Ví dụ:

```text id="formatcost"
binary sink → no string formatting
JSON sink   → encode structured fields
console     → text formatting
```

---

# 112. Compile-time static metadata

Static descriptors nên nằm trong read-only binary section:

```text id="rodata"
.rodata
    log descriptors
    field descriptors
    templates
```

---

# 113. No reflection dependency

Logging không cần runtime reflection.

Compiler-generated descriptors là đủ.

---

# 114. AI support

AI tooling có thể:

- tìm log patterns;
- correlate errors;
- giải thích log;
- generate structured logging;
- đề xuất missing context;
- tìm repeated failures.

AI không được tự sửa security logs hoặc xóa logs.

---

# 115. AI-readable schema

Mỗi logger/category có thể expose:

```text id="aischema"
category
description
fields
field types
sensitivity
severity
```

giúp AI hiểu semantic log.

---

# 116. Logging style

Axiom khuyến nghị:

```text id="style"
log_info(
    "connection established",
    host = host,
    port = port,
    protocol = protocol
)
```

thay vì:

```text id="badstyle"
log_info(
    "connection established host=%s port=%d protocol=%s"
)
```

Structured fields giữ data riêng.

---

# 117. No implicit sensitive context

Không tự động attach toàn bộ:

```text id="implicit"
environment
headers
cookies
tokens
user objects
```

vào mọi log record.

Context phải explicit và policy-controlled.

---

# 118. Logging context size

Context phải bounded:

```text id="contextsize"
max_fields
max_bytes
max_depth
```

---

# 119. Recursive structures

Không serialize recursive object graphs.

Maximum nesting depth explicit.

---

# 120. Canonical startup flow

```text id="flowstart"
process start
    ↓
AXCONFIG
    ↓
logging schema/profile
    ↓
initialize logger
    ↓
create sinks
    ↓
activate
    ↓
application start
```

---

# 121. Canonical application flow

```text id="flowapp"
application
    ↓
log_info(...)
    ↓
compile/runtime level check
    ↓
record
    ↓
per-core buffer
    ↓
collector
    ↓
sink
```

---

# 122. Canonical remote flow

```text id="flowremote"
record
 ↓
buffer
 ↓
batch
 ↓
AXCODEC
 ↓
AXSTREAM
 ↓
AXNETWORK
 ↓
remote collector
```

---

# 123. Canonical crash flow

```text id="flowcrash"
fault
 ↓
AXDIAGNOSTICS
 ↓
emergency logging buffer
 ↓
diagnostic snapshot
 ↓
post-crash persistence
```

Không phụ thuộc remote logging.

---

# 124. Canonical security flow

```text id="flowsec"
application log
      ↓
AXLOGGING
      ↓
sensitive-field policy
      ↓
AXSECURITY
      ↓
authorized sink
```

Security evidence:

```text id="flowsec2"
security action
      ↓
AXAUDIT
```

không phải AXLOGGING.

---

# 125. Canonical configuration flow

```text id="flowcfg"
AXCONFIG snapshot
       ↓
logger profile
       ↓
atomic activation
       ↓
new logging behavior
```

Existing log records retain their own metadata.

---

# 126. Canonical overload flow

```text id="flowover"
producer rate ↑
       ↓
buffer pressure
       ↓
sampling/drop policy
       ↓
drop counter
       ↓
AXOBSERVABILITY
```

Application không bị block vô thời hạn chỉ vì logging overload.

---

# 127. Canonical file rotation

```text id="flowrotate"
active.log
   ↓
size/time threshold
   ↓
flush
   ↓
close
   ↓
rename/archive
   ↓
open new file
   ↓
resume
```

Nếu opening new file fail, policy quyết định fallback sink.

---

# 128. Canonical shutdown

```text id="flowshutdown"
shutdown requested
      ↓
stop new records
      ↓
drain
      ↓
flush
      ↓
close sinks
      ↓
shutdown logger
```

Timeout phải bounded.

---

# 129. Observability metrics

AXLOGGING expose:

```text id="metrics"
logs_emitted
logs_dropped
logs_sampled
logs_formatted
logs_bytes
buffer_usage
buffer_overflow
sink_failures
sink_latency
flush_count
rotation_count
rotation_failures
```

---

# 130. Health

AXOBSERVABILITY có thể lấy:

```text id="health"
logger health
sink health
buffer health
remote connectivity
```

AXLOGGING không sở hữu global health model.

---

# 131. Diagnostics

AXDIAGNOSTICS có thể correlate:

```text id="diag"
crash_id
diagnostic_id
build_id
last_log_sequence
```

để hỗ trợ failure analysis.

---

# 132. Storage failure

Nếu file sink hết disk:

```text id="diskfull"
file sink → FAILED
```

nhưng:

```text id="console"
console sink
```

vẫn có thể tiếp tục.

---

# 133. No logging recursion

Nếu logger sink itself produces a log:

```text id="recursion"
logger
 → sink
 → logger
 → sink
```

phải có recursion guard.

---

# 134. Sink isolation

Mỗi sink có bounded queue.

Một slow sink không được giữ global logger lock.

---

# 135. Deadlock prevention

Logging từ:

- allocator;
- scheduler;
- lock subsystem;
- filesystem;

không được phụ thuộc synchronously vào chính subsystem đang giữ lock.

Đặc biệt:

```text id="deadlock"
AXSTORAGE lock
    ↓
log_error()
    ↓
file sink
    ↓
AXSTORAGE
```

phải tránh.

---

# 136. Emergency fallback

Nếu normal logger unavailable:

```text id="fallback"
emergency buffer
→ debugger
→ stderr/console
```

theo platform capability.

---

# 137. Deterministic mode

Test builds có thể yêu cầu:

```text id="det"
stable timestamps
stable sequence
stable sampling seed
stable formatting
```

để regression testing.

---

# 138. Testing

Required test classes:

```text id="tests"
unit
concurrency
overflow
filtering
formatting
redaction
rotation
remote failure
crash path
configuration reload
schema compatibility
performance
deterministic replay
```

---

# 139. Security test

Phải kiểm tra rằng:

```text id="sectest"
secret field
→ no plaintext sink output
```

và:

```text id="sectest2"
unauthorized reader
→ denied
```

---

# 140. Performance test

Benchmark:

```text id="bench"
disabled log
enabled log
structured log
many threads
many CPUs
buffer pressure
sink failure
```

Không chỉ benchmark console output.

---

# 141. Formal invariants

```text id="loginv"
LOG-INV-01
Mọi log record phải có log level hợp lệ.

LOG-INV-02
Mọi logger phải có stable logger identity trong process lifetime.

LOG-INV-03
Structured fields phải giữ typed semantics.

LOG-INV-04
Field type mismatch phải bị phát hiện.

LOG-INV-05
Disabled log không được evaluate expensive arguments nếu compiler/runtime có thể tránh.

LOG-INV-06
Normal logging không được bắt buộc heap allocation.

LOG-INV-07
Normal logging không được bắt buộc synchronous disk I/O.

LOG-INV-08
Normal logging không được bắt buộc synchronous network I/O.

LOG-INV-09
Một sink failure không được làm hỏng các sink độc lập.

LOG-INV-10
Mỗi sink phải có bounded buffering.

LOG-INV-11
Buffer overflow phải có explicit policy.

LOG-INV-12
Dropped records phải được thống kê.

LOG-INV-13
Log ordering global không được giả định nếu có nhiều producer.

LOG-INV-14
Sequence number phải phân biệt được record source.

LOG-INV-15
Wall-clock không được dùng làm monotonic duration.

LOG-INV-16
Trace context nếu tồn tại phải được giữ chính xác.

LOG-INV-17
Trace ID không được sử dụng làm security credential.

LOG-INV-18
Sensitive field phải tuân thủ classification policy.

LOG-INV-19
Secret plaintext không được trở thành canonical log output.

LOG-INV-20
Logger không được tự động serialize arbitrary object graph.

LOG-INV-21
Recursive serialization phải bị giới hạn.

LOG-INV-22
Log context phải có bounded size.

LOG-INV-23
Scoped logging context phải có lifetime rõ ràng.

LOG-INV-24
Configuration reload phải atomic đối với logger behavior.

LOG-INV-25
Một record không được thấy mixed configuration state.

LOG-INV-26
Log level filtering phải xảy ra trước expensive formatting khi có thể.

LOG-INV-27
Sampling không được làm mất error/fatal mặc định nếu policy không cho phép.

LOG-INV-28
Suppressed duplicates phải được thống kê.

LOG-INV-29
File rotation không được overwrite active log trước khi replacement sẵn sàng.

LOG-INV-30
Retention phải có bounded storage policy.

LOG-INV-31
Remote logging không được bypass AXNETWORK/AXSTREAM security.

LOG-INV-32
Log access sensitive phải chịu AXSECURITY authorization.

LOG-INV-33
Security accountability phải được chuyển cho AXAUDIT.

LOG-INV-34
Crash logging không được phụ thuộc vào network availability.

LOG-INV-35
Emergency logging path không được yêu cầu unbounded allocation.

LOG-INV-36
Logging không được tạo recursion vô hạn khi sink phát sinh lỗi.

LOG-INV-37
Logging không được tạo deadlock thông qua sink dependency.

LOG-INV-38
Replay không được execute application side effects.

LOG-INV-39
AI không được tự xóa, sửa hoặc hạ security boundary của logging/audit.

LOG-INV-40
AXLOGGING không được trở thành nguồn authoritative của security, metrics hoặc diagnostic state.
```

---

# 142. Definition of Done

`AXLOGGING 5.0` được freeze khi Axiom có:

- structured log record;
- typed fields;
- logger hierarchy;
- categories;
- seven/eight standard severity levels;
- compile-time filtering;
- runtime filtering;
- lazy arguments;
- scoped context;
- trace correlation;
- task correlation;
- source metadata;
- build metadata;
- stable log-site IDs;
- per-core buffers;
- bounded queues;
- overflow policy;
- loss accounting;
- sampling;
- duplicate suppression;
- console sink;
- debugger sink;
- memory sink;
- file sink;
- remote sink;
- GUI integration;
- structured/binary output;
- text output;
- JSON interoperability;
- file rotation;
- retention;
- batching;
- remote backpressure;
- sink isolation;
- emergency buffer;
- crash integration;
- sensitive-data classification;
- redaction;
- AXSECURITY integration;
- AXAUDIT integration;
- AXOBSERVABILITY integration;
- AXDIAGNOSTICS integration;
- AXCONFIG integration;
- compiler metadata;
- AI metadata;
- deterministic simulation;
- replay;
- fault injection;
- native ABI;
- native APIs;
- 40 invariants.

**AXLOGGING 5.0 → FROZEN.**

---

# BOOTSTRAP-764 — AXTIME

**Native Time, Clock, Duration, Calendar, Time Zone, Timer & Temporal Runtime 5.0**

Đây là nền tảng nên được chuẩn hóa tiếp theo vì rất nhiều subsystem hiện đã phụ thuộc vào khái niệm thời gian:

```text
AXOBSERVABILITY
AXLOGGING
AXAUDIT
AXDIAGNOSTICS
AXCONFIG
AXTASK
AXASYNC
AXNETWORK
AXSTORAGE
```

`AXTIME` sẽ đặc biệt quan trọng để Axiom **không trộn lẫn 3 khái niệm khác nhau**:

```text
monotonic time
      ≠
wall-clock time
      ≠
calendar/local time
```

và để timer/timeout/deadline có semantics chính xác, không phụ thuộc sai vào việc người dùng chỉnh đồng hồ hệ thống.