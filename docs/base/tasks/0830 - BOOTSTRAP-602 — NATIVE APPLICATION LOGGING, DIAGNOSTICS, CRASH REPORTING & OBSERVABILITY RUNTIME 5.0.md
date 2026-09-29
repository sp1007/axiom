Tiếp nối đúng chuỗi Axiom, đây là **BOOTSTRAP-602**.  

:::writing{variant="document" id="58321" title="BOOTSTRAP-602 — NATIVE APPLICATION LOGGING, DIAGNOSTICS, CRASH REPORTING & OBSERVABILITY RUNTIME 5.0"}

# BOOTSTRAP-602 — NATIVE APPLICATION LOGGING, DIAGNOSTICS, CRASH REPORTING & OBSERVABILITY RUNTIME 5.0

**Status:** Architecture / Implementation Specification  
**Layer:** Native Runtime / Bootstrap  
**Depends on:** BOOTSTRAP-600, BOOTSTRAP-601  
**Primary concern:** Logging, diagnostics, tracing, fault capture, crash reporting, observability  
**Non-goals:** Application state persistence, configuration management, telemetry SaaS, remote monitoring service

---

## 602.0 — Mục tiêu

BOOTSTRAP-602 định nghĩa subsystem diagnostics/observability native của Axiom.

Subsystem này phải cung cấp:

1. Structured logging.
2. Diagnostic events.
3. Runtime diagnostics.
4. Lightweight tracing.
5. Correlation/context propagation.
6. Assertion and panic diagnostics.
7. Unhandled exception/fault capture.
8. Crash artifact generation.
9. Stack trace capture.
10. Symbolization.
11. Emergency crash buffer.
12. Health/status diagnostics.
13. Runtime performance counters.
14. Integration với BOOTSTRAP-600 state/runtime lifecycle.
15. Integration với BOOTSTRAP-601 configuration/deployment.
16. Local-first operation.
17. Deterministic machine-readable output.
18. Bounded memory usage.
19. Minimal disabled-path overhead.
20. Không phụ thuộc third-party logging/crash framework.

Thiết kế phải phù hợp với mục tiêu Axiom:

> Diagnostics phải mạnh khi cần nhưng gần như biến mất khỏi executable khi ứng dụng không sử dụng chúng.

---

# 602.1 — Nguyên tắc kiến trúc

Subsystem tuân theo các nguyên tắc:

```text
Application
    ↓
Diagnostic API
    ↓
Diagnostic Core
    ├── Logger
    ├── Event Registry
    ├── Context
    ├── Tracer
    ├── Health
    └── Fault Manager
             ↓
      Platform Diagnostics
             ↓
      Output / Crash Artifacts
```

Không được để application phụ thuộc trực tiếp vào:

- Windows Event API
- POSIX syslog
- Android logging
- Apple logging framework
- debugger-specific APIs
- third-party logger
- third-party crash reporter.

Platform layer chỉ nằm dưới abstraction.

---

# 602.2 — Ranh giới với BOOTSTRAP-600

BOOTSTRAP-600 quản lý:

```text
application state
runtime lifecycle
checkpoint
restore
state identity
state metadata
```

BOOTSTRAP-602 quản lý:

```text
what happened
when it happened
where it happened
why it failed
diagnostic evidence
runtime health
execution trace
crash evidence
```

Ví dụ:

```text
State:
    current_document = 42

Diagnostic:
    ERROR document parser failed
```

Không được trộn hai khái niệm.

---

# 602.3 — Ranh giới với BOOTSTRAP-601

BOOTSTRAP-601 quản lý:

```text
configuration
profiles
environment
deployment
secrets
configuration fingerprint
```

BOOTSTRAP-602 chỉ tham chiếu:

```text
config_fingerprint
profile_id
deployment_id
build_id
```

Không được ghi secret vào log.

Không được serialize toàn bộ configuration snapshot vào crash report mặc định.

---

# 602.4 — Diagnostic levels

Axiom định nghĩa:

```text
TRACE
DEBUG
INFO
NOTICE
WARN
ERROR
FATAL
```

Thứ tự:

```text
TRACE < DEBUG < INFO < NOTICE < WARN < ERROR < FATAL
```

Mỗi logger có threshold.

Ví dụ:

```axiom
log.debug("parser", "token accepted")
```

Nếu threshold là `INFO`, compiler/runtime phải loại bỏ tối đa chi phí không cần thiết.

---

# 602.5 — Compile-time elimination

Axiom hỗ trợ:

```axiom
diagnostics.level = info
```

Compiler có thể loại bỏ:

```text
TRACE
DEBUG
```

khỏi binary nếu không cần runtime override.

Ví dụ:

```axiom
log.debug("network", expensive_debug_value())
```

Không được phép gọi:

```text
expensive_debug_value()
```

nếu DEBUG đã bị compile-time elimination.

---

# 602.6 — Lazy diagnostic arguments

API nên hỗ trợ:

```axiom
log.debug("parser") {
    "token={token} ast={dump_ast(ast)}"
}
```

Closure/block chỉ được thực thi khi event enabled.

Compiler có thể lower thành:

```text
if logger.enabled(DEBUG):
    evaluate block
```

---

# 602.7 — Structured event

Mỗi diagnostic event gồm:

```text
timestamp
monotonic_time
severity
category
event_id
message
fields
thread_id
process_id
context_id
trace_id
span_id
source_location
```

Các field tùy chọn phải được encode compact.

---

# 602.8 — Event ID

Mỗi event có thể có ID:

```axiom
log.error(
    event = EVT_PARSER_FAILED,
    ...
)
```

Event ID phải deterministic.

Không dùng random UUID làm event definition.

---

# 602.9 — Event definition

Ví dụ:

```axiom
event ParserFailed = 0x120001
```

Compiler tạo metadata:

```text
event_id
name
category
severity
source module
```

Metadata có thể được strip trong release build.

---

# 602.10 — Event categories

Category là string hoặc compile-time symbol:

```text
core
memory
io
network
graphics
parser
compiler
application
security
database
```

Khuyến nghị dùng interned IDs thay vì heap string.

---

# 602.11 — Message model

Axiom hỗ trợ:

```axiom
log.info("server", "Listening on {port}")
```

nhưng runtime ưu tiên structured representation:

```text
event = SERVER_STARTED
fields:
    port = 8080
```

Message text là presentation layer.

---

# 602.12 — Structured logging format

Diagnostic record canonical:

```text
{
    timestamp,
    severity,
    event,
    category,
    fields,
    source,
    thread,
    process,
    context,
    trace
}
```

JSON không phải internal representation bắt buộc.

JSON chỉ là output encoder.

---

# 602.13 — Binary internal event

Internal event nên dùng binary layout:

```text
Header
    timestamp
    severity
    event_id
    flags
    payload_size

Context
    thread_id
    process_id
    trace_id
    span_id

Payload
```

Mục tiêu:

- cache-friendly
- append-only
- không allocation
- dễ serialize
- crash-safe hơn text.

---

# 602.14 — Event ownership

Diagnostic event sau khi commit vào queue phải độc lập với lifetime của application object.

Không lưu raw pointer tới object trong event.

Ví dụ không hợp lệ:

```text
event.field = pointer_to_local_string
```

nếu event được xử lý asynchronous.

---

# 602.15 — Field types

Các field primitive được hỗ trợ:

```text
bool
i8/i16/i32/i64
u8/u16/u32/u64
f32/f64
char
string
bytes
enum
duration
timestamp
path
UUID-like ID
source location
```

---

# 602.16 — No arbitrary object serialization

Không tự động serialize object graph khi logging.

Điều này tránh:

- recursion
- allocation lớn
- deadlock
- secret leakage
- crash trong crash handler.

Application phải explicit:

```axiom
log.debug("user", user.id)
```

---

# 602.17 — Logger

Logger là lightweight handle:

```axiom
let log = Logger("network")
```

Handle không sở hữu global resource.

Có thể copy.

---

# 602.18 — Logger hierarchy

Có thể:

```text
app
app.http
app.http.client
app.http.server
```

Threshold inheritance:

```text
app = INFO
app.http = DEBUG
```

---

# 602.19 — Logger lookup

Logger lookup không được yêu cầu global lock trên mỗi event.

Có thể dùng:

```text
immutable logger table
atomic configuration pointer
```

---

# 602.20 — Runtime logger configuration

Threshold có thể thay đổi runtime:

```axiom
diagnostics.set_level("network", DEBUG)
```

Update phải atomic.

Existing events không bị corrupt.

---

# 602.21 — Sinks

Native sinks:

```text
ConsoleSink
FileSink
DebuggerSink
SystemSink
MemorySink
NullSink
CustomSink
```

---

# 602.22 — Console sink

Console sink hỗ trợ:

```text
human readable
JSON
compact
colored terminal
plain terminal
```

Color phải tự động disable khi output không phải terminal.

---

# 602.23 — File sink

File sink hỗ trợ:

```text
append
rotation
size limit
time rotation
retention count
flush policy
```

---

# 602.24 — Log rotation

Ví dụ:

```text
app.log
app.log.1
app.log.2
app.log.3
```

Rotation phải atomic ở mức platform phù hợp.

Không truncate file hiện tại trước khi file mới sẵn sàng.

---

# 602.25 — Crash-safe file handling

File logger không được là dependency bắt buộc của crash handler.

Crash handler chỉ sử dụng:

```text
emergency buffer
```

và minimal OS write primitive.

---

# 602.26 — Memory sink

Memory sink dùng cho:

- testing
- diagnostics UI
- crash context
- embedded systems.

---

# 602.27 — Ring buffer

Diagnostic core phải hỗ trợ bounded ring buffer.

Ví dụ:

```text
capacity = N events
```

Khi đầy:

```text
drop oldest
```

hoặc policy configurable:

```text
drop_oldest
drop_newest
block
```

Default:

```text
drop_oldest
```

---

# 602.28 — Emergency ring buffer

Ngoài normal ring buffer có:

```text
EmergencyDiagnosticBuffer
```

Đặc điểm:

- preallocated
- bounded
- no heap allocation
- no locks nếu có thể
- usable during fatal failure.

---

# 602.29 — Crash buffer

Crash buffer giữ các event gần nhất:

```text
last N diagnostic events
```

Khi crash:

```text
crash report
    +
    recent diagnostic events
```

Điều này rất quan trọng để biết chuyện gì xảy ra ngay trước fault.

---

# 602.30 — Producer path

Normal event path:

```text
application
   ↓
enabled?
   ↓
encode
   ↓
ring buffer
   ↓
worker
   ↓
sink
```

Không được:

```text
application
   ↓
format string
   ↓
filesystem
```

trên hot path mặc định.

---

# 602.31 — Async logger

Logger mặc định có thể asynchronous.

Producer chỉ cần:

```text
encode → enqueue
```

Consumer xử lý sink.

---

# 602.32 — Synchronous mode

Application có thể yêu cầu:

```axiom
diagnostics.mode = sync
```

Dùng cho:

- startup debugging
- deterministic tests
- crash reproduction.

---

# 602.33 — Flush

API:

```axiom
log.flush()
```

Semantics:

> mọi event đã enqueue trước thời điểm flush phải được chuyển đến sink hoặc báo lỗi.

---

# 602.34 — Flush timeout

Có thể:

```axiom
log.flush(timeout = 100.ms)
```

Không được block vô hạn.

---

# 602.35 — Shutdown

Shutdown sequence:

```text
stop producers
↓
flush
↓
close sinks
↓
release resources
```

Crash handler không phụ thuộc shutdown thành công.

---

# 602.36 — Backpressure

Logger không được làm application chết chỉ vì sink chậm.

Default:

```text
bounded queue
drop policy
```

---

# 602.37 — Dropped-event accounting

Nếu events bị drop:

```text
diagnostics.dropped_events
```

phải được cập nhật.

Có event:

```text
DiagnosticEventsDropped
```

nhưng event này phải tránh tạo infinite recursion.

---

# 602.38 — Recursive logging protection

Nếu logger phát hiện:

```text
logger → sink → logger
```

phải ngăn recursion.

Trong failure path:

```text
disable normal logging
use emergency output
```

---

# 602.39 — Diagnostic context

Context chứa metadata implicit:

```text
request_id
user_operation
component
trace_id
span_id
```

Ví dụ:

```axiom
with diagnostic.context(request_id):
    process_request()
```

---

# 602.40 — Context propagation

Context được propagate qua:

```text
function calls
async tasks
thread execution
request handlers
```

nhưng không nhất thiết phải propagate qua process boundary.

---

# 602.41 — Context implementation

Không dùng global mutable dictionary.

Ưu tiên:

```text
immutable context frame
thread/task-local pointer
```

---

# 602.42 — Context allocation

Hot-path context nên tránh heap allocation.

Small context có thể dùng inline storage.

---

# 602.43 — Context lifetime

Context phải tự động restore:

```text
push
execute
pop
```

Nếu panic xảy ra, runtime vẫn phải restore context khi unwinding khả dụng.

---

# 602.44 — Correlation ID

Native API:

```axiom
let id = DiagnosticId.new()
```

ID phải đủ để phân biệt request/process/session trong phạm vi thiết kế.

---

# 602.45 — Trace ID

Trace ID có dạng opaque:

```text
TraceId
```

Application không phụ thuộc representation.

---

# 602.46 — Span

Tracing tối giản:

```axiom
let span = trace.begin("compile")
...
span.end()
```

Span chứa:

```text
trace_id
span_id
parent_id
start
duration
name
status
```

---

# 602.47 — Span overhead

Nếu tracing disabled:

```text
begin()
end()
```

phải có overhead cực thấp.

Compiler có thể loại bỏ span metadata trong static build.

---

# 602.48 — Span nesting

Cho phép:

```text
compile
 ├── parse
 ├── semantic
 └── codegen
```

---

# 602.49 — Span attributes

Chỉ cho phép primitive bounded fields.

Không tự động dump object graph.

---

# 602.50 — Span events

Span có thể chứa diagnostic event references thay vì copy toàn bộ event.

---

# 602.51 — Trace sampling

Sampling là optional.

Các mode:

```text
off
always
ratio
adaptive
error-only
```

Core runtime chỉ cần primitive sampling API.

---

# 602.52 — No telemetry requirement

Tracing không đồng nghĩa với gửi dữ liệu lên Internet.

Axiom runtime không được mặc định upload telemetry.

---

# 602.53 — Local-first observability

Default:

```text
local only
```

Remote exporter phải do application/deployment explicit enable.

---

# 602.54 — Health subsystem

Native health state:

```text
starting
ready
degraded
stopping
stopped
failed
```

---

# 602.55 — Health indicators

Component có thể publish:

```axiom
health.register("database", ...)
```

---

# 602.56 — Health snapshot

Snapshot:

```text
timestamp
overall_state
components[]
diagnostic counters
```

---

# 602.57 — Liveness vs readiness

Tách:

```text
liveness
readiness
```

Liveness:

> process còn hoạt động.

Readiness:

> process có khả năng nhận workload.

---

# 602.58 — Health check isolation

Health check không được tự gây deadlock với subsystem đang kiểm tra.

Timeout bắt buộc.

---

# 602.59 — Runtime counters

Built-in counters:

```text
threads
tasks
allocations
bytes allocated
diagnostic events
dropped events
exceptions
panics
crashes
startup duration
uptime
```

---

# 602.60 — Counter implementation

Counter nên dùng atomic primitive.

Không dùng mutex cho counter hot path.

---

# 602.61 — Metrics distinction

Metrics chỉ là counters/gauges/histograms tối giản.

Không biến BOOTSTRAP-602 thành full metrics platform.

---

# 602.62 — Histogram

Optional native histogram:

```text
count
sum
min
max
buckets
```

Bucket configuration phải bounded.

---

# 602.63 — Assertion

Axiom hỗ trợ:

```axiom
assert(condition)
```

và:

```axiom
debug_assert(condition)
```

---

# 602.64 — Assertion failure

Failure phải tạo diagnostic:

```text
ASSERTION_FAILED
```

bao gồm:

```text
source
condition
function
thread
context
```

---

# 602.65 — Panic

Native:

```axiom
panic("message")
```

Panic không đồng nghĩa OS crash.

Runtime có thể:

```text
unwind
recover
terminate
```

tùy policy.

---

# 602.66 — Panic payload

Payload phải bounded.

Không được cho phép arbitrary huge object serialization.

---

# 602.67 — Panic handler

Application có thể đăng ký:

```axiom
panic.handler(...)
```

Nhưng handler không được làm mất emergency crash capture.

---

# 602.68 — Unhandled panic

Unhandled panic:

```text
capture diagnostics
capture stack
write crash artifact
terminate process
```

---

# 602.69 — Native fault

Native runtime phải nhận diện platform fault khi khả dụng:

```text
access violation
illegal instruction
divide-by-zero
abort
stack overflow
bus error
```

Danh sách chính xác phụ thuộc target.

---

# 602.70 — Platform fault abstraction

Canonical type:

```text
FaultKind
```

Ví dụ:

```text
AccessViolation
IllegalInstruction
StackOverflow
Abort
Signal
Unknown
```

---

# 602.71 — Windows fault integration

Windows backend có thể map:

```text
SEH
unhandled exception
minidump facilities
debugger
```

vào native abstraction.

Không expose SEH types lên core API.

---

# 602.72 — Unix fault integration

POSIX-like backend hỗ trợ signal-based fault capture.

Signal handler phải sử dụng async-signal-safe operations.

---

# 602.73 — Apple platforms

Apple backend cung cấp platform-compatible crash artifact abstraction.

Không đưa Apple-specific APIs vào language core.

---

# 602.74 — Android

Android backend có thể integrate native process fault mechanisms.

Core diagnostics API vẫn giữ platform-neutral.

---

# 602.75 — WASM

WASM không có native process crash semantics giống desktop.

WASM backend phải map:

```text
trap
unhandled exception
host failure
```

thành:

```text
FaultKind
```

nếu host API cho phép.

---

# 602.76 — Signal handler restrictions

Crash handler không được:

```text
allocate heap
lock arbitrary mutex
invoke arbitrary application code
perform complex formatting
access potentially corrupted global state
```

---

# 602.77 — Two-stage crash capture

Stage 1:

```text
minimal fault capture
```

Stage 2:

```text
safe post-fault processing
```

Nếu process vẫn sống đủ lâu, stage 2 enrich artifact.

---

# 602.78 — Crash capture order

Canonical sequence:

```text
detect fault
↓
disable recursive diagnostics
↓
capture fault metadata
↓
capture register state
↓
capture stack pointer / instruction pointer
↓
copy emergency events
↓
generate minimal crash artifact
↓
invoke platform crash writer
↓
terminate
```

---

# 602.79 — Crash recursion guard

Global atomic:

```text
crash_in_progress
```

Nếu fault thứ hai xảy ra:

```text
minimal emergency termination
```

Không cố tạo crash report thứ hai.

---

# 602.80 — Register capture

Platform layer có thể capture:

```text
instruction pointer
stack pointer
frame/base pointer
general registers
flags
```

Representation canonical:

```text
CpuContext
```

---

# 602.81 — Stack capture

Stack capture phải bounded:

```text
max_frames
max_bytes
```

---

# 602.82 — Stack walking

Stack walker có implementation theo target.

Core chỉ nhận:

```text
Frame[]
```

---

# 602.83 — Frame

Frame:

```text
address
module
symbol
source
line
column
offset
```

---

# 602.84 — Symbolization

Symbolization có thể diễn ra:

```text
runtime
post-process
external diagnostic tool
```

Release runtime nên ưu tiên post-process để giảm binary size.

---

# 602.85 — Symbol metadata

Build system phải tạo mapping:

```text
build_id
module
code address
symbol
source location
```

---

# 602.86 — Build ID

Mỗi executable có:

```text
BuildId
```

Build ID phải đủ để map crash artifact tới binary/symbol package.

---

# 602.87 — Source location

Compiler tự động encode:

```text
file
line
column
function
module
```

nếu diagnostics metadata enabled.

---

# 602.88 — Release metadata

Release build có thể strip source path.

Thay bằng:

```text
source_id
```

để tránh leak filesystem structure.

---

# 602.89 — Reproducible symbolization

Build system nên hỗ trợ:

```text
same source
same compiler
same flags
same dependencies
→ same symbol mapping
```

---

# 602.90 — Crash artifact

Canonical artifact:

```text
.axcrash
```

hoặc equivalent platform-specific container.

---

# 602.91 — Crash artifact structure

```text
Header
Manifest
Process
Build
Fault
CPU
Threads
Stack
Modules
Diagnostics
Context
State reference
Configuration reference
Environment summary
```

---

# 602.92 — Crash manifest

Manifest:

```text
format_version
runtime_version
compiler_version
build_id
platform
architecture
timestamp
crash_id
```

---

# 602.93 — Crash ID

Mỗi crash instance có unique opaque ID.

Crash ID không chứa secret.

---

# 602.94 — Process information

Artifact có thể chứa:

```text
process_id
parent_process_id
uptime
executable
command identity
```

Nhưng privacy policy có thể disable sensitive fields.

---

# 602.95 — Thread information

Crash report có:

```text
thread_id
thread_name
state
stack
```

---

# 602.96 — All-thread capture

Optional.

Default crash report chỉ cần:

```text
faulting thread
selected active threads
```

để giới hạn artifact size.

---

# 602.97 — Module list

Module:

```text
name
base address
size
build id
version
```

Không bắt buộc dump toàn bộ binary.

---

# 602.98 — Loaded library identification

Dynamic libraries được nhận diện bằng:

```text
module ID
build ID
version
```

---

# 602.99 — External library privacy

Không tự động upload external binary.

Crash report chỉ chứa metadata.

---

# 602.100 — Diagnostic snapshot

Crash report tham chiếu:

```text
last N diagnostic events
```

thay vì toàn bộ runtime history.

---

# 602.101 — State integration

Nếu BOOTSTRAP-600 có state checkpoint gần nhất:

```text
state_checkpoint_id
state_version
```

có thể được ghi vào crash artifact.

Không serialize application state mặc định.

---

# 602.102 — Config integration

BOOTSTRAP-601 cung cấp:

```text
config_schema_version
config_fingerprint
profile_id
deployment_id
```

Crash report có thể chứa các identifier này.

---

# 602.103 — Secret isolation

Tuyệt đối không đưa vào crash artifact:

```text
password
token
private key
secret config value
credential
session secret
```

---

# 602.104 — Secret type awareness

Nếu field có type:

```text
Secret<T>
```

diagnostic encoder phải output:

```text
<redacted>
```

---

# 602.105 — Redaction

Application có thể đánh dấu:

```axiom
@private
@secret
```

field diagnostic.

---

# 602.106 — Automatic redaction

Known secret types phải được redacted tự động.

Không phụ thuộc developer nhớ gọi `redact()`.

---

# 602.107 — Path privacy

Absolute filesystem path có thể được canonicalize thành:

```text
source_id
relative_path
```

---

# 602.108 — Environment privacy

Crash report không dump toàn bộ environment variables.

Chỉ các field allowlisted.

---

# 602.109 — Command-line privacy

CLI arguments có thể chứa secret.

Runtime phải hỗ trợ:

```text
argument redaction
```

hoặc disable capture.

---

# 602.110 — Privacy policy

Diagnostic policy:

```text
strict
standard
debug
```

`strict` tối thiểu dữ liệu.

---

# 602.111 — Local artifact policy

Default:

```text
write locally
```

Không upload.

---

# 602.112 — Remote exporter

Remote exporter là optional application/deployment layer.

API:

```axiom
diagnostics.exporter(...)
```

---

# 602.113 — Exporter isolation

Exporter không được chạy trong crash signal handler.

---

# 602.114 — Retry

Remote diagnostic upload nếu có phải có:

```text
bounded retry
timeout
backoff
disk quota
```

---

# 602.115 — Offline behavior

Nếu remote endpoint unavailable:

```text
application continues
```

trừ khi application explicitly yêu cầu fail-fast.

---

# 602.116 — Diagnostic persistence

Normal logs có retention policy.

Crash artifacts có retention riêng.

---

# 602.117 — Disk quota

Diagnostic subsystem phải giới hạn:

```text
max log disk usage
max crash artifact usage
max individual artifact size
```

---

# 602.118 — Startup recovery

Startup scan có thể phát hiện:

```text
previous crash artifact
```

và publish:

```text
PreviousCrashDetected
```

---

# 602.119 — Crash marker

Runtime có thể dùng:

```text
clean_shutdown marker
```

Nếu marker không tồn tại:

```text
unclean termination
```

Không được kết luận chắc chắn đó là crash.

---

# 602.120 — Startup diagnostics

Startup event:

```text
PROCESS_START
RUNTIME_INITIALIZED
CONFIG_LOADED
STATE_RESTORED
APPLICATION_READY
```

---

# 602.121 — Shutdown diagnostics

Events:

```text
SHUTDOWN_REQUESTED
SHUTDOWN_STARTED
SHUTDOWN_COMPLETED
```

---

# 602.122 — Lifecycle correlation

Mỗi process có:

```text
process_instance_id
```

để liên kết diagnostics trong một lifetime.

---

# 602.123 — Session identity

Nếu application cần:

```text
session_id
```

nhưng runtime không tự gán semantic meaning.

---

# 602.124 — Diagnostic clock

Event cần:

```text
wall clock
monotonic clock
```

Wall clock để hiển thị.

Monotonic để duration/order.

---

# 602.125 — Clock correction

Wall-clock adjustment không được làm sai duration.

Duration luôn dựa monotonic clock.

---

# 602.126 — Timestamp precision

Canonical internal timestamp:

```text
nanoseconds hoặc platform-native equivalent
```

Output precision phụ thuộc platform.

---

# 602.127 — Event ordering

Event ordering trong cùng producer:

```text
FIFO
```

Global ordering chỉ guaranteed nếu sink/backend hỗ trợ.

---

# 602.128 — Thread identity

Thread ID là opaque native type:

```text
ThreadId
```

Không assume numeric semantics trên mọi platform.

---

# 602.129 — Process identity

Process ID cũng opaque:

```text
ProcessId
```

---

# 602.130 — Diagnostic API

Core API tối thiểu:

```axiom
log.trace(...)
log.debug(...)
log.info(...)
log.notice(...)
log.warn(...)
log.error(...)
log.fatal(...)

log.enabled(...)
log.flush(...)

panic(...)
assert(...)
debug_assert(...)

trace.begin(...)
health.status(...)
```

---

# 602.131 — Compile-time event API

Khuyến nghị:

```axiom
log.error(
    EVT_CONNECTION_FAILED,
    host = host,
    port = port
)
```

thay vì chỉ:

```axiom
log.error("connection failed")
```

---

# 602.132 — Dynamic message API

Dynamic strings vẫn được hỗ trợ.

Compiler ưu tiên optimized structured path khi event schema known.

---

# 602.133 — Event schema

Optional:

```axiom
event ConnectionFailed {
    host: string
    port: u16
    reason: ErrorCode
}
```

Compiler sinh encoder.

---

# 602.134 — Generated event metadata

Compiler có thể generate:

```text
event table
field schema
severity
category
source
```

---

# 602.135 — Event schema compatibility

Event schema version:

```text
schema_id
schema_version
```

---

# 602.136 — Binary compatibility

Diagnostic binary format phải versioned.

Reader phải reject unknown incompatible version rõ ràng.

---

# 602.137 — Forward compatibility

Reader có thể skip unknown fields.

---

# 602.138 — Backward compatibility

New runtime không được phá artifact format cũ nếu decoder hỗ trợ version đó.

---

# 602.139 — Diagnostic serialization

Serializers:

```text
text
JSON
binary
compact
```

đều dùng cùng canonical event model.

---

# 602.140 — Deterministic serialization

Binary artifact serialization phải deterministic khi input metadata giống nhau.

---

# 602.141 — Hashing

Diagnostic artifact có thể có:

```text
content_hash
```

để phát hiện corruption/duplicate.

---

# 602.142 — Compression

Compression là optional.

Không nén trong signal handler.

---

# 602.143 — Integrity

Crash artifact có thể chứa checksum.

Nếu encryption được application bật:

```text
diagnostic artifact encryption
```

phải là optional.

---

# 602.144 — Key handling

Crash subsystem không tự quản lý long-lived encryption secrets.

Key phải đến từ deployment/security subsystem.

---

# 602.145 — Debugger integration

Khi debugger attached:

```text
DebuggerSink
```

có thể emit diagnostic events trực tiếp.

---

# 602.146 — Break-on-error

Optional:

```axiom
diagnostics.break_on(ERROR)
```

chỉ nên enabled trong debug/development.

---

# 602.147 — Release safety

Release build mặc định:

```text
break_on_error = false
```

---

# 602.148 — Debug diagnostic console

Optional native API:

```text
diagnostics.inspect()
```

cho tooling.

Không phải production UI requirement.

---

# 602.149 — Runtime command interface

Tooling có thể yêu cầu:

```text
get health
get counters
get logger levels
flush logs
capture snapshot
```

Transport không thuộc core.

---

# 602.150 — Diagnostic snapshot

Snapshot có:

```text
runtime state
health
counters
recent events
active spans
thread summary
```

Snapshot bounded.

---

# 602.151 — Snapshot consistency

Snapshot không cần stop-the-world.

Các counters có thể là point-in-time approximate.

---

# 602.152 — Deadlock diagnostics

Runtime có thể phát hiện:

```text
lock wait
thread stall
```

nhưng đây là diagnostic enhancement, không phải correctness requirement.

---

# 602.153 — Thread dump

API:

```axiom
diagnostics.capture_threads()
```

Output:

```text
thread
state
stack
current span
```

---

# 602.154 — Hang detection

Optional watchdog:

```text
heartbeat
timeout
diagnostic capture
```

Watchdog không tự kill application mặc định.

---

# 602.155 — Watchdog policy

Các mode:

```text
disabled
diagnose
terminate
```

Default:

```text
disabled
```

---

# 602.156 — Resource exhaustion

Diagnostics phải xử lý:

```text
OOM
stack exhaustion
file descriptor exhaustion
thread exhaustion
```

---

# 602.157 — OOM behavior

OOM handler không được giả định còn heap.

Phải sử dụng:

```text
preallocated emergency memory
```

nếu enabled.

---

# 602.158 — Emergency memory pool

Runtime reserve:

```text
emergency diagnostic memory
```

size compile/deployment configurable.

---

# 602.159 — Stack overflow

Stack overflow path phải tránh normal stack-heavy diagnostics.

Chỉ thực hiện minimal capture.

---

# 602.160 — Diagnostic allocation budget

Normal diagnostic operation có configurable allocation budget.

---

# 602.161 — Zero-allocation mode

Embedded/performance-critical application có thể chọn:

```text
diagnostics.zero_alloc = true
```

Trong mode này event payload phải bounded/preallocated.

---

# 602.162 — Static configuration

For tiny binaries:

```text
compile-time diagnostics
```

có thể loại bỏ:

```text
tracing
health
file sink
crash symbolization
remote exporter
```

nếu không dùng.

---

# 602.163 — Linker dead stripping

Mỗi optional subsystem phải có độc lập symbol boundary để linker loại bỏ.

---

# 602.164 — Minimal runtime profile

Axiom định nghĩa profile:

```text
diagnostics=minimal
```

bao gồm:

```text
panic
assert
emergency crash capture
```

---

# 602.165 — Standard profile

```text
diagnostics=standard
```

bao gồm:

```text
logging
health
counters
stack traces
crash artifacts
```

---

# 602.166 — Full profile

```text
diagnostics=full
```

thêm:

```text
tracing
runtime inspection
advanced metrics
watchdog
```

---

# 602.167 — Application overrides

Application có thể enable feature.

Nhưng deployment policy có thể disable feature để giảm overhead.

---

# 602.168 — Build feature matrix

Compiler output phải expose:

```text
diagnostics_logging
diagnostics_trace
diagnostics_crash
diagnostics_health
diagnostics_metrics
```

để tooling biết binary capabilities.

---

# 602.169 — ABI stability

Public diagnostic types phải có ABI-stable representation nếu exported từ library ABI.

---

# 602.170 — Library boundary

Axiom library có thể emit diagnostics mà không biết application sink.

Runtime global diagnostic service cung cấp sink.

---

# 602.171 — Library isolation

Library không được thay đổi global logging policy tùy tiện.

---

# 602.172 — Plugin/module diagnostics

Dynamic module có thể register:

```text
module_id
event definitions
diagnostic source
```

---

# 602.173 — Module unload

Không giữ pointer tới unloaded module metadata.

---

# 602.174 — Source mapping

Dynamic module stack frame phải map bằng:

```text
module build ID
offset
```

---

# 602.175 — Error correlation

Native `Error` có thể chứa:

```text
error_code
message
source
cause
diagnostic_id
```

---

# 602.176 — Error chain

Errors có thể có:

```text
cause
```

nhưng chain phải bounded để tránh recursive explosion.

---

# 602.177 — Error vs log

Error object:

> kết quả nghiệp vụ/kỹ thuật.

Log event:

> record về việc xảy ra.

Không tự động log mọi error.

---

# 602.178 — Error propagation

Error propagation không được phụ thuộc logger.

Application vẫn hoạt động khi diagnostics disabled.

---

# 602.179 — Fatal error semantics

`fatal` là diagnostic severity.

Nó không tự động có nghĩa:

```text
terminate process
```

Trừ khi policy định nghĩa.

---

# 602.180 — Termination policy

Có thể cấu hình:

```text
fatal_action = continue
fatal_action = shutdown
fatal_action = terminate
```

Default tùy application profile, không hard-code semantics vào logger.

---

# 602.181 — Crash report naming

Tên artifact deterministic theo:

```text
timestamp
process_instance_id
crash_id
```

Không dùng user-controlled path components trực tiếp.

---

# 602.182 — Crash artifact atomicity

Ghi artifact:

```text
temporary
↓
flush
↓
fsync nếu policy yêu cầu
↓
rename
```

---

# 602.183 — Corrupt artifact handling

Startup scanner phải bỏ qua artifact corrupt và log diagnostic bounded.

Không được crash vì crash report corrupt.

---

# 602.184 — Artifact size limits

Default giới hạn:

```text
events
threads
frames
modules
fields
bytes
```

tất cả đều bounded.

---

# 602.185 — Sensitive data scanning

Runtime không nên chạy expensive heuristic scanning trên mọi log event.

Security relies primarily on:

```text
typed Secret
explicit redaction
allowlists
```

---

# 602.186 — Audit events

Security-sensitive application có thể dùng:

```text
audit(...)
```

Audit event semantics khác ordinary debug logging.

Audit có:

```text
durability requirement
integrity requirement
retention requirement
```

---

# 602.187 — Audit isolation

Audit log không được tự động bị drop giống debug logs nếu policy yêu cầu durable delivery.

---

# 602.188 — Audit API

```axiom
audit.record(
    event = USER_LOGIN,
    ...
)
```

---

# 602.189 — Audit vs diagnostics

Diagnostics:

```text
debugging/operations
```

Audit:

```text
accountability/security record
```

---

# 602.190 — Testing API

Runtime phải cung cấp fault injection:

```axiom
diagnostics.test.inject(...)
```

chỉ available trong test/debug builds.

---

# 602.191 — Fault injection targets

Có thể inject:

```text
panic
assert failure
sink failure
queue full
file write failure
symbolization failure
health timeout
```

---

# 602.192 — Crash testing

Test harness phải có cách tạo controlled crash.

Không được dựa vào undefined application behavior.

---

# 602.193 — Golden artifact tests

Crash artifacts có canonical fixtures.

Test:

```text
decode
schema
required fields
redaction
version
```

---

# 602.194 — Deterministic diagnostic tests

Clock/random/process-specific fields có thể được dependency-injected trong test.

---

# 602.195 — Performance tests

Benchmark:

```text
disabled logging
enabled logging
queued logging
sync logging
context creation
span creation
stack capture
```

---

# 602.196 — Required performance target

Disabled event:

```text
near-zero branch/constant overhead
```

Không được thực hiện:

```text
heap allocation
string formatting
system call
```

---

# 602.197 — Hot-path guarantee

Normal application hot path phải không bị global diagnostic mutex.

---

# 602.198 — Crash-path guarantee

Crash handler phải có bounded execution.

Không cố thu thập infinite diagnostic data.

---

# 602.199 — Failure containment

Nếu diagnostics subsystem hỏng:

```text
application functionality continues
```

trừ trường hợp application explicitly declares diagnostics as mandatory.

---

# 602.200 — No diagnostics recursion

Diagnostic subsystem không được phụ thuộc vào chính nó để báo lỗi nội bộ.

Internal failure path:

```text
minimal emergency writer
```

---

# 602.201 — Platform abstraction

Compiler/runtime source tree:

```text
runtime/diagnostics/
    core/
    logging/
    tracing/
    crash/
    health/
    serialization/
    platform/
        windows/
        linux/
        macos/
        ios/
        android/
        wasm/
```

---

# 602.202 — Core interfaces

Core interfaces:

```text
DiagnosticSink
DiagnosticEncoder
DiagnosticContext
DiagnosticBuffer
CrashHandler
StackWalker
SymbolProvider
HealthProvider
```

---

# 602.203 — Platform interfaces

Platform:

```text
PlatformCrashCapture
PlatformThreadInfo
PlatformModuleEnumerator
PlatformDebugger
PlatformSignalHandler
PlatformFileWriter
```

---

# 602.204 — No platform leakage

Platform implementation types không được xuất hiện trong portable application API.

---

# 602.205 — Initialization phases

Initialization:

```text
EARLY
CORE
FULL
READY
SHUTDOWN
```

---

# 602.206 — EARLY phase

EARLY chỉ có:

```text
emergency buffer
minimal stderr/debug output
crash handler bootstrap
```

---

# 602.207 — CORE phase

CORE thêm:

```text
logger
event registry
context
```

---

# 602.208 — FULL phase

FULL thêm:

```text
file sinks
tracing
health
metrics
symbol services
```

---

# 602.209 — READY phase

Application có thể sử dụng toàn bộ enabled diagnostics.

---

# 602.210 — Shutdown phase

Không cho phép tạo new background diagnostic worker.

Pending events được drain bounded.

---

# 602.211 — Startup failure

Nếu diagnostics initialization fail:

```text
application may fallback to emergency sink
```

Không mặc định terminate application.

---

# 602.212 — Crash-before-init

Nếu application crash trước FULL initialization:

```text
minimal crash artifact
```

vẫn phải có khả năng được tạo nếu platform cho phép.

---

# 602.213 — Crash-after-shutdown

Nếu fault xảy ra sau normal shutdown:

```text
minimal emergency handler
```

không cố restart diagnostics.

---

# 602.214 — Versioning

BOOTSTRAP-602 artifact schema:

```text
AXDIAG-1
AXCRASH-1
```

Tên chỉ là canonical identifiers; exact wire magic phải được frozen trong implementation spec.

---

# 602.215 — Format header

Binary artifact header:

```text
magic
version
endianness
architecture
flags
header_size
artifact_size
```

---

# 602.216 — Unknown fields

Decoder phải skip unknown fields nếu field length được biết.

---

# 602.217 — Corruption detection

Decoder phải kiểm tra:

```text
bounds
length
offset
integer overflow
recursion depth
```

---

# 602.218 — Untrusted artifact handling

Crash/log files phải được xem là untrusted input.

Parser không được:

```text
execute embedded code
load arbitrary plugin
follow arbitrary filesystem path
```

---

# 602.219 — Diagnostic viewer

Axiom tooling có thể cung cấp:

```text
axiom diag inspect crash.axcrash
```

Output:

```text
summary
fault
stack
modules
events
config fingerprint
state checkpoint
```

---

# 602.220 — Symbol server

Symbol resolution service có thể tồn tại trong tooling.

Không phải runtime dependency.

---

# 602.221 — Offline symbolization

CLI phải hỗ trợ:

```text
binary
symbols
crash artifact
```

→ human-readable stack.

---

# 602.222 — Build artifact relationship

Build system phải preserve:

```text
executable
build-id
symbol artifact
source mapping
```

relationship.

---

# 602.223 — Compiler-generated diagnostic metadata

Compiler có thể emit:

```text
function ID
source location
inline call chain
module ID
```

---

# 602.224 — Inlining

Stack symbolizer phải hỗ trợ inline frames khi debug metadata tồn tại.

---

# 602.225 — Optimized builds

Release optimization không được làm crash reporting unusable.

At minimum:

```text
instruction address
module
build id
```

phải còn.

---

# 602.226 — Stripped binary

Stripped executable vẫn phải có stable build ID.

---

# 602.227 — Crash deduplication

Tooling có thể tạo:

```text
crash_signature
```

từ:

```text
fault kind
module
instruction offset
top stack frames
```

Không dùng timestamp trong signature.

---

# 602.228 — Diagnostic fingerprint

Normal diagnostic snapshot có fingerprint tùy chọn để grouping.

---

# 602.229 — No predictive claims

Crash subsystem chỉ ghi evidence.

Không tự kết luận:

```text
root cause
bug owner
responsibility
```

Root-cause analysis thuộc tooling/human analysis.

---

# 602.230 — Diagnostic recommendations

Runtime có thể report:

```text
possible resource exhaustion
```

chỉ khi dựa trên deterministic threshold.

Không tạo speculative diagnosis trong core runtime.

---

# 602.231 — Runtime invariant violations

Internal invariant failure phải emit:

```text
RUNTIME_INVARIANT_FAILED
```

và chuyển sang fatal path nếu invariant không thể tiếp tục.

---

# 602.232 — Security invariant

Diagnostics không được bypass security boundary.

Ví dụ:

```text
secret → logger
```

phải bị type/policy layer ngăn chặn.

---

# 602.233 — Capability model

Optional diagnostic capabilities:

```text
diagnostic.log
diagnostic.trace
diagnostic.health
diagnostic.crash
diagnostic.inspect
```

Deployment policy có thể disable từng capability.

---

# 602.234 — Sandboxed targets

Trong sandbox:

```text
file sink
process enumeration
module enumeration
signal capture
```

có thể unavailable.

API phải report capability absence thay vì crash.

---

# 602.235 — Embedded targets

Embedded target có thể chỉ hỗ trợ:

```text
UART sink
memory ring
minimal fault record
```

---

# 602.236 — No mandatory filesystem

Diagnostics core không được yêu cầu filesystem.

---

# 602.237 — No mandatory threads

Diagnostics core không được yêu cầu background thread.

Nếu async sink enabled thì mới tạo worker.

---

# 602.238 — No mandatory heap

Minimal diagnostics phải hoạt động với:

```text
preallocated buffers
```

---

# 602.239 — CPU overhead budget

Normal logging overhead phải bounded theo event payload.

Disabled logging phải O(1).

---

# 602.240 — Memory budget

Runtime diagnostic memory:

```text
fixed baseline
+
configured bounded buffers
```

Không tăng vô hạn theo runtime lifetime.

---

# 602.241 — Backpressure observability

Expose:

```text
queue_depth
queue_capacity
dropped_events
sink_errors
flush_latency
```

---

# 602.242 — Sink health

Sink có status:

```text
healthy
degraded
failed
disabled
```

---

# 602.243 — Sink isolation

Một sink fail không được làm sink khác fail.

Ví dụ:

```text
file sink failed
→ console sink continues
```

---

# 602.244 — Sink lifecycle

```text
create
initialize
active
draining
closed
failed
```

---

# 602.245 — Custom sink API

Custom sink phải implement:

```text
write(event)
flush()
close()
```

và có thể hỗ trợ batch.

---

# 602.246 — Custom sink safety

Custom sink không được chạy trong emergency crash handler.

---

# 602.247 — Batch encoding

Async worker có thể batch nhiều events để giảm syscall.

---

# 602.248 — File batching

File sink có thể buffer:

```text
N events
hoặc
T milliseconds
```

trước flush.

---

# 602.249 — Durability policy

File/audit sink có:

```text
buffered
flush
durable
```

policy.

---

# 602.250 — Durability cost

`durable` có thể yêu cầu expensive OS synchronization.

Application phải explicit chọn.

---

# 602.251 — Logging macros/syntax

Compiler có thể cung cấp syntax sugar:

```axiom
@log(INFO, "server started")
```

nhưng semantics phải tương đương native API.

---

# 602.252 — Source location injection

Compiler tự động thêm:

```text
__source_file
__source_line
__source_column
__function
```

nếu event schema yêu cầu.

---

# 602.253 — Function identity

Function ID nên ổn định trong cùng build.

Tên human-readable có thể được strip.

---

# 602.254 — Module identity

Module ID phải stable trong build artifact.

---

# 602.255 — Thread-local logger state

Hot-path logger có thể cache:

```text
threshold
thread context
sink pointer
```

và refresh bằng generation counter.

---

# 602.256 — Configuration generation

Khi logger config thay đổi:

```text
generation++
```

Thread cache refresh lazily.

Không broadcast lock tới toàn bộ threads.

---

# 602.257 — Dynamic threshold consistency

Event có thể race với threshold update.

Semantics:

> Event sử dụng threshold snapshot tại thời điểm kiểm tra.

Không cần global total ordering.

---

# 602.258 — Context consistency

Context snapshot được gắn tại event creation.

Sau đó context thay đổi không ảnh hưởng event cũ.

---

# 602.259 — Trace consistency

Span ID được gắn khi event tạo.

---

# 602.260 — Diagnostic API thread safety

Public diagnostic APIs phải document:

```text
thread-safe
thread-local
single-thread-only
```

Không để behavior ngầm.

---

# 602.261 — Reentrancy

Normal logger nên reentrant ở mức cần thiết.

Crash handler không yêu cầu full reentrancy.

---

# 602.262 — Allocator independence

Diagnostics không được phụ thuộc application allocator trong emergency path.

---

# 602.263 — Allocator failure

Nếu normal diagnostic allocation fail:

```text
fallback emergency buffer
```

---

# 602.264 — Error handling inside logger

Logger API không nên throw/panic vì sink failure.

Thay vào đó:

```text
record sink failure counter
fallback sink
```

---

# 602.265 — Logger error policy

Application có thể query:

```axiom
log.status()
```

---

# 602.266 — Fatal sink failure

Nếu audit durability bắt buộc mà sink fail:

```text
application-defined policy
```

không hard-code terminate.

---

# 602.267 — Diagnostic bootstrap logging

Compiler/runtime itself có thể emit:

```text
runtime events
```

với reserved category:

```text
axiom.runtime
```

---

# 602.268 — Reserved event namespace

Runtime events dùng ID range riêng.

Application không được collision.

---

# 602.269 — Event ID allocation

Canonical layout:

```text
namespace
module
event
```

Exact bit allocation phải được freeze trong ABI specification.

---

# 602.270 — Event registry

Registry phải hỗ trợ:

```text
lookup event ID
lookup metadata
```

Không yêu cầu runtime reflection đầy đủ.

---

# 602.271 — Reflection stripping

Nếu application không dùng diagnostics tooling:

```text
event names
field names
source strings
```

có thể strip.

---

# 602.272 — Compile-time schema validation

Compiler kiểm tra:

```text
field types
event IDs
duplicate IDs
invalid severity
invalid category
```

---

# 602.273 — Runtime schema validation

Decoder kiểm tra artifact schema.

Không tin metadata từ input.

---

# 602.274 — Diagnostic ABI

ABI-level structures phải có:

```text
size
version
flags
```

để extension an toàn.

---

# 602.275 — Extension mechanism

Future diagnostics fields thêm vào cuối structure hoặc tagged fields.

Không thay đổi semantic của existing fields.

---

# 602.276 — No dependency inversion failure

Application không cần import platform diagnostics module để dùng:

```text
log.info()
```

---

# 602.277 — Core package layout

Đề xuất:

```text
std.diagnostics
std.logging
std.trace
std.health
std.crash
```

Có thể được compiler/runtime special-case để dead-strip.

---

# 602.278 — Minimal import

Application chỉ:

```axiom
import std.logging
```

không kéo toàn bộ diagnostics stack nếu linker có thể loại bỏ.

---

# 602.279 — Runtime global instance

Có một logical diagnostic service:

```text
DiagnosticRuntime
```

nhưng implementation có thể partition theo subsystem.

---

# 602.280 — Dependency direction

```text
Language
  ↓
Compiler
  ↓
Runtime Core
  ↓
Diagnostics Core
  ↓
Platform
```

Không cho:

```text
Platform → Application
```

---

# 602.281 — Compiler integration

Compiler phải hỗ trợ:

```text
diagnostic metadata emission
source mapping
event schema generation
build ID
feature stripping
```

---

# 602.282 — Linker integration

Linker phải preserve:

```text
build ID
diagnostic sections
unwind metadata
```

khi enabled.

---

# 602.283 — Object format

Native object sections có thể có:

```text
.axom.diag
.axom.unwind
.axom.events
.axom.source
```

Tên cuối cùng thuộc object format specification.

---

# 602.284 — Unwind metadata

Crash stack capture phụ thuộc target unwind metadata.

Compiler phải emit khi crash diagnostics enabled.

---

# 602.285 — Exception model integration

Nếu Axiom exception/unwind model tồn tại:

```text
panic
error
exception
```

phải cung cấp diagnostic integration hooks.

---

# 602.286 — No mandatory exceptions

Diagnostics không ép language phải sử dụng exception model.

---

# 602.287 — Async integration

Task runtime phải propagate:

```text
diagnostic context
trace context
```

khi task được spawn.

---

# 602.288 — Task cancellation diagnostics

Cancellation có thể tạo event:

```text
TASK_CANCELLED
```

nhưng không tự động log mọi cancellation.

---

# 602.289 — Scheduler diagnostics

Optional counters:

```text
tasks_created
tasks_completed
tasks_cancelled
queue_depth
scheduler_latency
```

---

# 602.290 — Thread diagnostics

Runtime counters:

```text
threads_created
threads_active
thread_cpu_time
```

nếu platform hỗ trợ.

---

# 602.291 — Memory diagnostics

Optional:

```text
heap_used
heap_committed
allocation_count
peak_usage
```

Không bắt buộc mỗi allocation phải emit log.

---

# 602.292 — Allocation tracing

Allocation tracing chỉ bật explicit.

Không được làm allocator chậm mặc định.

---

# 602.293 — I/O diagnostics

Counters:

```text
bytes_read
bytes_written
operations
errors
```

---

# 602.294 — Network diagnostics

Optional counters:

```text
connections
bytes_sent
bytes_received
timeouts
retries
```

---

# 602.295 — GPU diagnostics

Nếu Axiom GPU runtime được dùng:

```text
device
queue
kernel
memory
synchronization
```

có thể được trace.

Không đưa GPU-specific details vào core diagnostics ABI.

---

# 602.296 — Diagnostic namespace

Recommended namespaces:

```text
axiom.runtime
axiom.memory
axiom.thread
axiom.io
axiom.network
axiom.gpu
axiom.compiler
application.*
```

---

# 602.297 — User-defined namespaces

Application namespace không được collision với reserved `axiom.*`.

---

# 602.298 — Severity policy

Severity là semantic hint, không phải automatic action.

Ví dụ:

```text
ERROR != crash
FATAL != necessarily process exit
```

---

# 602.299 — Diagnostic correctness

Diagnostics phải không làm thay đổi business semantics ngoại trừ explicit instrumentation effects.

---

# 602.300 — Observable side effects

Logging có side effects:

```text
I/O
timing
allocation
```

Do đó compiler không được reorder event theo cách làm mất semantic ordering trong cùng execution context.

---

# 602.301 — Optimization boundary

Compiler có thể optimize diagnostics chỉ khi vẫn bảo toàn:

```text
enabled/disabled semantics
event ordering
field correctness
```

---

# 602.302 — Constant-folding

Nếu compiler biết:

```text
DEBUG disabled
```

có thể constant-fold entire diagnostic call.

---

# 602.303 — Link-time optimization

LTO có thể eliminate:

```text
unused event schemas
unused encoders
unused sinks
```

---

# 602.304 — Binary size target

Minimal profile phải có binary-size overhead nhỏ và bounded.

Exact numerical budget sẽ được benchmark/freeze sau prototype.

---

# 602.305 — Startup target

Diagnostics initialization phải không tạo startup latency đáng kể khi disabled.

---

# 602.306 — Shutdown target

Shutdown drain phải bounded.

Application không được treo vô hạn chỉ vì logger worker.

---

# 602.307 — Diagnostic worker crash

Nếu logger worker crash:

```text
main application must not automatically crash
```

Worker failure chuyển thành sink failure.

---

# 602.308 — Worker recovery

Optional sink restart.

Không retry vô hạn.

---

# 602.309 — File corruption recovery

Nếu log file corrupt/unwritable:

```text
fallback console/emergency sink
```

---

# 602.310 — Disk-full behavior

Disk full:

```text
drop or fallback
```

không được làm application chết mặc định.

---

# 602.311 — Permission failure

Permission failure tương tự:

```text
sink failed
fallback
```

---

# 602.312 — Crash disk-full behavior

Crash artifact không được giả định filesystem writable.

Emergency output có thể:

```text
stderr
debugger
platform crash facility
```

---

# 602.313 — Crash artifact fallback

Fallback hierarchy:

```text
configured crash file
→ emergency file
→ stderr/debugger
→ platform crash mechanism
```

---

# 602.314 — Platform crash facility

Runtime có thể delegate platform-native crash artifact generation.

Axiom metadata vẫn phải được liên kết nếu có thể.

---

# 602.315 — Core dump integration

Unix-like targets có thể dùng core dump.

Axiom crash metadata có thể được emitted alongside core dump.

---

# 602.316 — Windows dump integration

Windows target có thể tạo minidump/full dump tùy policy.

---

# 602.317 — Dump size policy

Dump generation phải có:

```text
minimal
standard
full
```

policy nếu platform hỗ trợ.

---

# 602.318 — Memory privacy

Full memory dump có nguy cơ chứa secrets.

Default policy không tự động enable full memory dump.

---

# 602.319 — Crash dump consent

Deployment configuration phải explicit cho dump level.

---

# 602.320 — User-facing crash message

Runtime có thể hiển thị:

```text
Application encountered an unexpected error.
Crash report saved to ...
```

Không hiển thị secret/internal data.

---

# 602.321 — Headless mode

Server/service:

```text
no UI
```

crash report vẫn hoạt động.

---

# 602.322 — GUI mode

GUI application có thể register:

```text
CrashNotificationHandler
```

Nhưng handler không chạy trong unsafe crash phase.

---

# 602.323 — Service mode

Service có thể emit:

```text
startup
ready
stop
restart
```

diagnostic events.

---

# 602.324 — Restart integration

Crash subsystem không tự restart process.

Supervisor/deployment layer chịu trách nhiệm.

---

# 602.325 — Child process diagnostics

Parent có thể associate child:

```text
parent_process_instance_id
child_process_instance_id
```

---

# 602.326 — Process tree

Optional diagnostic metadata.

Không scan process tree mặc định vì privacy/cost.

---

# 602.327 — Environment fingerprint

Optional non-secret fingerprint:

```text
OS version
architecture
runtime version
CPU feature set
```

---

# 602.328 — Hardware metadata

Có thể capture:

```text
CPU family
logical CPU count
memory capacity
GPU identity
```

nhưng phải tuân privacy/deployment policy.

---

# 602.329 — OS metadata

Canonical:

```text
platform
platform_version
architecture
abi
```

---

# 602.330 — Runtime metadata

```text
axiom_runtime_version
compiler_version
standard_library_version
```

---

# 602.331 — Application metadata

Application có thể khai báo:

```axiom
application.name
application.version
application.channel
```

---

# 602.332 — Deployment metadata

BOOTSTRAP-601 supplies:

```text
deployment_id
environment
profile
config_fingerprint
```

---

# 602.333 — Build provenance

Crash artifact có thể chứa:

```text
compiler build
source revision
build profile
feature set
```

Source revision có thể được redacted.

---

# 602.334 — Reproducibility

Diagnostic data phải đủ để tooling xác định binary/symbol version.

---

# 602.335 — Source revision privacy

Không bắt buộc expose repository URL.

---

# 602.336 — Diagnostic policy inheritance

Policy resolution:

```text
compile-time
→ deployment
→ runtime
```

runtime cannot enable compile-stripped subsystem.

---

# 602.337 — Configuration interaction

BOOTSTRAP-601 config có thể control:

```text
logging level
sink
rotation
crash artifact path
retention
privacy mode
```

---

# 602.338 — Configuration immutability

Resolved config snapshot immutable.

Runtime diagnostic subsystem observes configuration generation.

---

# 602.339 — Dynamic reconfiguration

Supported settings can update atomically.

Unsafe settings require restart.

---

# 602.340 — Immutable diagnostic identity

These should not change during process lifetime:

```text
process_instance_id
build_id
```

---

# 602.341 — Mutable diagnostic state

These may change:

```text
threshold
sink enabled
sampling
health state
counters
```

---

# 602.342 — Health registration lifetime

Health component registration must be tied to module/component lifetime.

Unloaded component must unregister.

---

# 602.343 — Health deadlock protection

Health callback timeout.

No arbitrary blocking operation in health callback.

---

# 602.344 — Diagnostic callback isolation

User callbacks run outside crash handler.

---

# 602.345 — Crash callbacks

Only pre-registered minimal callbacks may run during crash capture, and preferably none.

---

# 602.346 — Async callback safety

Callbacks must not assume arbitrary thread-local state during fatal fault.

---

# 602.347 — API documentation requirement

Every public diagnostics API must specify:

```text
allocation behavior
blocking behavior
thread safety
panic behavior
failure behavior
```

---

# 602.348 — ABI documentation

Exported ABI types must document:

```text
size
alignment
ownership
lifetime
version
```

---

# 602.349 — Ownership model

Diagnostic events passed to sink are owned by runtime unless explicitly borrowed with documented lifetime.

---

# 602.350 — Borrowing

Diagnostics API should avoid exposing complex reference/borrow semantics to application developers.

Prefer value/opaque handles.

---

# 602.351 — Pointer exposure

Raw pointers are not part of normal diagnostics API.

Platform internals may use them.

---

# 602.352 — Handle model

Opaque handles:

```text
LoggerHandle
TraceHandle
SinkHandle
CrashContext
```

---

# 602.353 — Handle invalidation

Invalid handle usage must return defined error or no-op according to API contract.

No use-after-free.

---

# 602.354 — Resource ownership

Runtime owns:

```text
global sinks
buffers
worker threads
crash state
```

Application owns optional custom sink objects according to registration contract.

---

# 602.355 — Diagnostics in libraries

Libraries should never initialize their own independent global logging infrastructure.

---

# 602.356 — Library logger identity

Library:

```text
Logger("library.name")
```

uses application diagnostic runtime.

---

# 602.357 — Multi-runtime process

If supported, process should still avoid duplicate crash handlers.

Multiple Axiom runtime instances must coordinate.

---

# 602.358 — Runtime singleton policy

Logical diagnostics service is process-scoped.

---

# 602.359 — Dynamic runtime loading

If runtime loaded/unloaded dynamically, diagnostics service lifetime must outlive registered modules.

---

# 602.360 — Fork semantics

On fork-capable targets, child process must reinitialize unsafe diagnostic state before using async logging.

---

# 602.361 — Exec semantics

After exec:

```text
new process_instance_id
```

---

# 602.362 — Crash after fork

Child crash handler must not rely on parent worker thread state.

---

# 602.363 — Signal mask interaction

Diagnostics signal installation must coexist with application signal policy.

---

# 602.364 — Signal chaining

If platform permits:

```text
Axiom handler
→ previous handler
```

according to explicit policy.

---

# 602.365 — Signal ownership

Runtime must document which signals/faults it owns.

---

# 602.366 — Debugger precedence

When debugger attached, policy may:

```text
break
capture
delegate
```

---

# 602.367 — Production debugger

Production runtime must not assume debugger exists.

---

# 602.368 — Panic recovery

Recoverable panic path must preserve diagnostic context.

---

# 602.369 — Stack unwinding diagnostics

If unwinding:

```text
panic
→ capture stack
→ unwind
→ recovery
```

Diagnostic event should preserve original panic location.

---

# 602.370 — Nested panic

Panic during panic handler:

```text
terminate via emergency path
```

---

# 602.371 — Error context

Error chain should support:

```text
operation
source
cause
diagnostic ID
```

---

# 602.372 — Cause cycle

Error cause cycle must be impossible or detected.

---

# 602.373 — Maximum error depth

Decoder/formatter uses bounded depth.

---

# 602.374 — Human formatting

Diagnostic CLI should present:

```text
ERROR [NET-1203] Connection failed
  host: ...
  reason: ...
  at: module:function(file:line)
```

---

# 602.375 — Machine formatting

JSON output should preserve typed fields:

```json
{
  "severity": "error",
  "event_id": 1203,
  "fields": {
    "port": 443
  }
}
```

Exact JSON schema will be frozen separately.

---

# 602.376 — Binary format efficiency

Binary event format should avoid repeated:

```text
field names
category names
module names
```

through intern tables where beneficial.

---

# 602.377 — String interning

Interning must be bounded.

Never allow unbounded attacker-controlled string table.

---

# 602.378 — Attacker-controlled logging

Application may log user input.

Therefore:

```text
max string length
max field count
max event size
```

must be enforced.

---

# 602.379 — Log injection

Human text sinks must escape:

```text
newline
control characters
terminal escape sequences
```

when configured for security-safe output.

---

# 602.380 — Terminal safety

Color/control output only enabled when explicitly safe.

---

# 602.381 — File name safety

User-provided category/event names must never become arbitrary file paths.

---

# 602.382 — Resource exhaustion defense

Every diagnostic path must have bounded resource consumption.

---

# 602.383 — Event rate limiting

Optional:

```text
max events/sec/category
```

---

# 602.384 — Rate limit algorithm

A simple token bucket or equivalent bounded algorithm is sufficient.

---

# 602.385 — Rate-limit diagnostics

Dropped due to rate limit:

```text
rate_limited_events
```

counter.

---

# 602.386 — Burst handling

Short bursts should be tolerated within configured bucket.

---

# 602.387 — Sampling vs rate limit

Sampling chooses events statistically/policy-wise.

Rate limiting enforces resource bound.

They are separate mechanisms.

---

# 602.388 — Error prioritization

Errors should not necessarily be dropped because debug traffic is high.

Separate priority queues may be supported.

---

# 602.389 — Queue architecture

Possible:

```text
high priority ring
normal ring
```

High priority bounded separately.

---

# 602.390 — Fatal path priority

Fatal event should use emergency buffer directly.

---

# 602.391 — Logger ordering

If multiple queues are used, exact cross-priority ordering is not guaranteed unless timestamp/sequence number is included.

---

# 602.392 — Sequence number

Each process may maintain monotonically increasing:

```text
event_sequence
```

for diagnostics ordering.

---

# 602.393 — Atomic sequence

Use atomic increment only if multi-thread global ordering is needed.

Otherwise thread-local sequence may be sufficient.

---

# 602.394 — Global ordering semantics

Global event sequence gives total order of enqueue operations, not necessarily wall-clock execution order.

---

# 602.395 — Clock and sequence

Crash artifact should prefer:

```text
sequence + monotonic timestamp
```

for reconstruction.

---

# 602.396 — Trace/span clock

Span duration uses monotonic clock.

---

# 602.397 — Health timestamps

Health transitions include monotonic duration and wall timestamp where available.

---

# 602.398 — Diagnostic state machine

Global state:

```text
UNINITIALIZED
EARLY
RUNNING
DEGRADED
SHUTTING_DOWN
STOPPED
CRASHING
```

---

# 602.399 — State transition invariants

Illegal transitions must be rejected or ignored safely.

---

# 602.400 — Degraded state

Diagnostics enters DEGRADED if:

```text
sink unavailable
worker failed
disk unavailable
```

Application continues.

---

# 602.401 — Crash state

Once:

```text
CRASHING
```

normal diagnostic APIs are disabled or redirected.

---

# 602.402 — Emergency writer

Emergency writer supports only:

```text
fixed buffer
minimal formatting
platform write
```

---

# 602.403 — Emergency formatting

Allowed primitives:

```text
integer
hex
enum
fixed string
address
```

---

# 602.404 — Emergency string limits

All strings bounded.

---

# 602.405 — Address formatting

Pointer/address formatting must not dereference memory.

---

# 602.406 — Memory probing

Crash handler must not attempt arbitrary memory probing.

---

# 602.407 — Stack probing

Only platform-safe stack capture mechanism.

---

# 602.408 — CPU context integrity

CPU context must be captured as close to fault as practical.

---

# 602.409 — Fault address

If platform supplies:

```text
fault_address
```

capture it.

---

# 602.410 — Instruction address

Capture:

```text
instruction_pointer
```

---

# 602.411 — Access type

Where available:

```text
read
write
execute
unknown
```

---

# 602.412 — Crash reason

Canonical:

```text
fault_kind
fault_code
platform_code
```

---

# 602.413 — Platform code preservation

Unknown platform-specific error code must remain available as numeric value.

---

# 602.414 — Cross-platform normalization

Normalization must not erase important platform-specific information.

---

# 602.415 — Crash artifact privacy levels

```text
minimal
standard
diagnostic
```

---

# 602.416 — Minimal crash artifact

Contains:

```text
build
platform
fault
instruction pointer
stack
```

---

# 602.417 — Standard crash artifact

Adds:

```text
threads
modules
recent events
runtime counters
```

---

# 602.418 — Diagnostic crash artifact

Adds optional:

```text
health
trace spans
expanded metadata
```

subject to privacy policy.

---

# 602.419 — Full memory dump separation

Full memory dump is independent of `.axcrash`.

---

# 602.420 — Crash report retention

Retention inherited from BOOTSTRAP-601 deployment policy unless explicitly overridden.

---

# 602.421 — Crash report cleanup

Cleanup runs outside crash handler.

---

# 602.422 — Startup cleanup

Old artifacts cleaned according to:

```text
age
count
size
```

limits.

---

# 602.423 — Correlation across restart

Previous crash ID may be referenced in startup diagnostics.

---

# 602.424 — Crash loop detection

Deployment layer may detect repeated crash artifacts.

Runtime itself only reports evidence.

---

# 602.425 — No auto-remediation

Diagnostics subsystem does not automatically change application configuration in response to crashes.

---

# 602.426 — Health state persistence

Health state normally process-local.

Persistent health history belongs to deployment/monitoring layer.

---

# 602.427 — Diagnostic history

Runtime history bounded by ring buffers.

---

# 602.428 — Long-term history

Not part of core runtime.

---

# 602.429 — Remote monitoring boundary

Remote monitoring belongs to external application/infrastructure layer.

---

# 602.430 — No vendor lock-in

Diagnostic formats must be documented and locally decodable.

---

# 602.431 — Open artifact design

`.axcrash` must be parseable without proprietary service.

---

# 602.432 — CLI tooling

Minimum tooling:

```text
axiom diag inspect
axiom diag symbols
axiom diag decode
axiom diag validate
```

---

# 602.433 — Artifact validation

```text
axiom diag validate file.axcrash
```

must check schema and bounds.

---

# 602.434 — Artifact conversion

Tooling may convert:

```text
.axcrash → JSON
.axcrash → text
.axcrash → symbolized report
```

---

# 602.435 — Event export

```text
axiom diag export-log
```

may convert binary logs into JSON/text.

---

# 602.436 — Toolchain independence

Diagnostic tools are built by Axiom toolchain and do not require third-party logging frameworks.

---

# 602.437 — Compiler self-diagnostics

Axiom compiler itself should use BOOTSTRAP-602 once runtime is mature.

---

# 602.438 — Bootstrap compiler compatibility

Early compiler stages may use a minimal subset:

```text
stderr
emergency diagnostics
```

until full runtime exists.

---

# 602.439 — Self-hosting transition

After Axiom compiler self-hosting:

```text
compiler diagnostics
→ Axiom diagnostics runtime
```

where practical.

---

# 602.440 — Compiler-specific events

Compiler categories:

```text
parse
semantic
type
borrow/memory
IR
optimization
codegen
link
```

depending on final language architecture.

---

# 602.441 — Diagnostic IDs in compiler

Compiler diagnostics IDs should be stable enough for tooling.

---

# 602.442 — User error vs internal compiler error

Separate:

```text
USER_DIAGNOSTIC
INTERNAL_ERROR
```

---

# 602.443 — Internal compiler crash

Compiler crash should produce:

```text
compiler build
source file
phase
stack
diagnostics
```

without leaking unrelated environment secrets.

---

# 602.444 — Build server integration

Build daemon may expose:

```text
health
build spans
cache statistics
worker diagnostics
```

---

# 602.445 — Cache diagnostics

Compiler cache metrics:

```text
hit
miss
invalidated
reused
```

---

# 602.446 — Diagnostic event persistence

Compiler build logs may be deterministic enough for CI analysis.

---

# 602.447 — CI mode

CI diagnostics:

```text
plain
machine-readable
no ANSI
bounded logs
```

---

# 602.448 — Exit codes

Diagnostic subsystem does not redefine process exit codes.

Application/tool defines exit semantics.

---

# 602.449 — Error reporting separation

Console output is presentation.

Underlying event remains structured.

---

# 602.450 — Internationalization

Diagnostic event IDs are stable.

Human-readable message localization can be separate.

---

# 602.451 — Message localization

Event schema must not depend on English message text.

---

# 602.452 — Localization key

Optional:

```text
message_key
```

---

# 602.453 — Developer diagnostics

Debug build can include:

```text
full source names
full function names
```

---

# 602.454 — Production diagnostics

Production can include:

```text
stable IDs
redacted metadata
```

---

# 602.455 — Build profiles

Recommended:

```text
debug
release
release-diagnostic
embedded
minimal
```

---

# 602.456 — Release-diagnostic

Optimized binary + diagnostic metadata.

Useful for production crash analysis.

---

# 602.457 — Embedded profile

No assumptions:

```text
filesystem
threads
dynamic allocation
```

---

# 602.458 — Minimal profile

Only:

```text
panic
assert
emergency crash
```

---

# 602.459 — Diagnostics feature discovery

Application/tool can query:

```axiom
diagnostics.capabilities()
```

---

# 602.460 — Capability flags

Example:

```text
LOGGING
TRACING
CRASH_CAPTURE
STACK_TRACE
SYMBOLIZATION
HEALTH
METRICS
FILE_SINK
DEBUGGER
```

---

# 602.461 — Capability stability

Capabilities are versioned.

Unknown capability bits must be ignored safely.

---

# 602.462 — Security hardening

Diagnostics parser/tooling must defend against:

```text
integer overflow
buffer overflow
path traversal
zip bombs if compressed
malicious symbols
```

---

# 602.463 — Symbol file trust

Symbol files are treated as untrusted input.

---

# 602.464 — Symbolization sandbox

Optional external symbolization tool can run isolated from application process.

---

# 602.465 — Runtime attack surface

Keep crash parser out of normal process hot path.

---

# 602.466 — Diagnostics as optional attack surface

If application doesn't need diagnostics:

```text
strip it
```

---

# 602.467 — Static linking

Static executable can include only selected diagnostics modules.

---

# 602.468 — Dynamic linking

Runtime diagnostic library can be dynamically linked where platform policy permits.

Core language must not require it.

---

# 602.469 — Third-party library policy

No third-party library may be mandatory for:

```text
logging
crash capture
stack walking
artifact generation
```

---

# 602.470 — OS-native API policy

OS-native APIs may be used behind platform adapters.

---

# 602.471 — Compiler runtime dependency

Compiler-generated diagnostic code may call intrinsic runtime primitives.

---

# 602.472 — Intrinsics

Possible compiler intrinsics:

```text
__source_location
__function_id
__build_id
__thread_id
__stack_trace
```

---

# 602.473 — Intrinsic stability

Intrinsics not explicitly public may remain compiler-private.

---

# 602.474 — Diagnostics metadata section

Executable may contain a compact metadata section.

Loader/runtime reads only if enabled.

---

# 602.475 — Metadata stripping

Release binary can remove human-readable metadata while retaining minimal unwind/build ID.

---

# 602.476 — Build artifact packaging

Recommended:

```text
app.exe
app.sym
app.diag
```

where:

```text
.sym = symbols
.diag = optional diagnostic metadata
```

Exact extension not yet ABI-frozen.

---

# 602.477 — Symbol package identity

Symbol package must include:

```text
build_id
architecture
platform
```

---

# 602.478 — Mismatch detection

Tooling must reject symbols whose build ID doesn't match crash artifact.

---

# 602.479 — Diagnostic tool errors

Tooling should clearly report:

```text
symbol mismatch
unsupported format
corrupt artifact
missing metadata
```

---

# 602.480 — Crash report completeness

A crash report is considered valid if it contains:

```text
artifact version
build identity
fault identity
at least one diagnostic location or fault address
```

when available.

---

# 602.481 — Graceful degradation

Unavailable information must be represented as:

```text
unknown
unavailable
not_captured
```

Never fabricate.

---

# 602.482 — No fake stack frames

Symbolizer must never invent function names.

---

# 602.483 — Source location confidence

Tooling should distinguish:

```text
exact
approximate
unknown
```

if mapping precision varies.

---

# 602.484 — Crash report annotations

Post-processing tools may add annotations without modifying original raw artifact.

---

# 602.485 — Immutable raw artifact

Original crash artifact should remain immutable.

---

# 602.486 — Derived report

Human-readable report is a derived artifact.

---

# 602.487 — Chain of custody

Optional hash of raw artifact can be included in derived report.

---

# 602.488 — Diagnostic timestamps

All timestamps must indicate timezone/UTC semantics where serialized.

---

# 602.489 — Canonical time

Internal canonical wall timestamp should be UTC-based.

---

# 602.490 — Locale independence

Binary diagnostics must not depend on locale.

---

# 602.491 — Number formatting

Machine output uses locale-independent representation.

---

# 602.492 — Unicode

Diagnostics text is UTF-8 by default.

Invalid UTF-8 must be safely encoded.

---

# 602.493 — Invalid string handling

Malformed UTF-8 should not crash logger.

Use replacement/escaped bytes according to encoder policy.

---

# 602.494 — Binary field handling

Binary payloads use:

```text
length + bytes
```

with maximum size.

---

# 602.495 — Large payloads

Large payloads require explicit blob/reference API.

---

# 602.496 — Blob diagnostics

Optional:

```axiom
diagnostics.attach_blob(...)
```

Blob is bounded and separately retained.

---

# 602.497 — No implicit file reads

Logger never reads arbitrary application files to serialize objects.

---

# 602.498 — Diagnostic context serialization

Only explicitly registered context fields are serialized.

---

# 602.499 — Context limits

Limits:

```text
max fields
max bytes
max nesting
```

---

# 602.500 — Core completion invariant

BOOTSTRAP-602 is complete only when:

```text
logging
+ structured events
+ context
+ tracing
+ health
+ counters
+ panic/assert
+ native fault capture
+ emergency buffer
+ stack capture
+ symbol mapping
+ crash artifacts
+ privacy/redaction
+ configuration integration
+ state/checkpoint correlation
+ platform abstraction
+ deterministic versioned format
+ bounded resource usage
+ testing/fault injection
```

đã có architecture và implementation contract.

---

# 602.501 — Required implementation phases

Implementation phải chia thành:

### Phase 1 — Emergency diagnostics

```text
emergency buffer
panic
assert
minimal fault capture
stderr/debugger
```

### Phase 2 — Structured logging

```text
events
severity
logger
ring buffer
console sink
```

### Phase 3 — Persistent logging

```text
file sink
rotation
retention
serialization
```

### Phase 4 — Crash artifacts

```text
stack
CPU context
modules
build ID
.axcrash
```

### Phase 5 — Runtime observability

```text
context
trace
health
counters
```

### Phase 6 — Toolchain

```text
diag inspect
diag decode
symbolizer
artifact validator
```

### Phase 7 — Advanced optimization

```text
compile-time stripping
LTO elimination
zero-allocation mode
sampling
rate limiting
```

---

# 602.502 — Required test matrix

Mỗi target phải test:

```text
logging disabled
logging enabled
queue full
sink failure
disk full
permission failure
flush
shutdown
panic
assert
nested panic
native fault
stack capture
symbol mismatch
corrupt artifact
secret redaction
Unicode
large fields
multithreading
async tasks
startup crash
shutdown crash
```

---

# 602.503 — Cross-platform test matrix

Targets:

```text
Windows x64
Linux x64
Linux ARM64
macOS ARM64
iOS ARM64
Android ARM64
WASM
```

Platform không hỗ trợ feature phải pass bằng:

```text
capability unavailable
```

không phải runtime crash.

---

# 602.504 — Performance acceptance

Benchmarks phải chứng minh:

1. Disabled logs gần như không có overhead.
2. Enabled async logging không serialize toàn application.
3. Ring buffer bounded.
4. No unbounded allocation.
5. Crash path không phụ thuộc normal heap.
6. Diagnostics có thể được linker loại bỏ.
7. Minimal profile có footprint nhỏ.

Exact numerical thresholds được freeze sau benchmark prototype thực tế thay vì áp đặt số tùy ý trước khi có implementation.

---

# 602.505 — Correctness acceptance

Phải chứng minh:

```text
no diagnostic event corruption
no crash-handler recursion
no secret leakage through typed Secret
no invalid artifact parsing
no symbol/build mismatch acceptance
no unbounded resource growth
```

---

# 602.506 — Developer experience acceptance

Developer có thể viết:

```axiom
fn connect(host: string) -> Result<Connection> {
    log.debug("network", "connecting to {host}")

    let span = trace.begin("connect")

    ...
}
```

mà không phải:

```text
import platform-specific logger
configure third-party logger
manage thread-safe queue
format JSON manually
implement crash handler
```

---

# 602.507 — Production usage acceptance

Một native application release phải có khả năng:

```text
start
log
run
report health
crash
produce artifact
restart
inspect previous crash
```

mà không cần cloud service.

---

# 602.508 — Architecture invariant

BOOTSTRAP-602 không được trở thành:

```text
mandatory heavyweight runtime
```

Nó phải là:

```text
capability-based
modular
dead-strippable
bounded
local-first
platform-adapted
```

---

# 602.509 — Final API principle

Application developer chủ yếu nhìn thấy:

```axiom
log.info(...)
log.warn(...)
log.error(...)

trace.begin(...)
health.status(...)

panic(...)
assert(...)

diagnostics.snapshot(...)
```

Phần còn lại thuộc compiler/runtime/tooling.

---

# 602.510 — Final design principle

Axiom diagnostics phải đạt trạng thái:

> **When everything is working, diagnostics are cheap. When something goes wrong, diagnostics become extremely rich without requiring the application to have predicted the failure.**

Đây là nguyên tắc trung tâm của BOOTSTRAP-602.

---

## BOOTSTRAP-602 — Completion Criteria

Task được xem là hoàn thành ở cấp architecture khi:

- Diagnostic API đã được định nghĩa.
- Structured event model đã được định nghĩa.
- Logging pipeline đã được định nghĩa.
- Ring buffer/emergency buffer đã được định nghĩa.
- Context/tracing model đã được định nghĩa.
- Health/counter model đã được định nghĩa.
- Panic/assert/fault model đã được định nghĩa.
- Cross-platform crash abstraction đã được định nghĩa.
- Stack/unwind/symbol model đã được định nghĩa.
- `.axcrash` concept và versioning đã được định nghĩa.
- Privacy/redaction boundary đã được định nghĩa.
- BOOTSTRAP-600/601 integration đã được định nghĩa.
- Compiler/linker integration đã được định nghĩa.
- Dead stripping và minimal runtime profile đã được định nghĩa.
- Resource/security limits đã được định nghĩa.
- Testing/fault injection đã được định nghĩa.
- Implementation phases đã được định nghĩa.
- Không có dependency bắt buộc vào third-party logging/crash framework.

**Task completion: BOOTSTRAP-602 — Native Application Logging, Diagnostics, Crash Reporting & Observability Runtime 5.0**

**Next task: BOOTSTRAP-603 — Native Application Security Boundary, Capability System, Permissions & Trusted Runtime 5.0**

:::