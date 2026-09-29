# BOOTSTRAP-760 — AXDIAGNOSTICS

**Title:** Native Diagnostics, Crash Analysis, Dump, Error Context, Runtime Health, Profiling & Failure Investigation Runtime 5.0  
**Namespace:** `AXDIAGNOSTICS`  
**Phase:** Axiom Civilization Runtime / Native Diagnostics & Observability Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXDIAGNOSTICS` là **technical observability & failure-analysis plane** của Axiom.

Nó chịu trách nhiệm trả lời:

```text
What failed?
Where did it fail?
What was the runtime doing?
What resources were involved?
What was the performance state?
How can the failure be reproduced?
```

Trong khi:

```text
AXAUDIT
    = What happened from an accountability/evidence perspective?

AXDIAGNOSTICS
    = What happened technically inside the runtime?
```

---

# 2. Architecture

```text
                         Axiom Runtime
                              │
             ┌────────────────┴────────────────┐
             │                                 │
          AXAUDIT                       AXDIAGNOSTICS
             │                                 │
     security evidence                  technical evidence
     provenance                         crash analysis
     accountability                     profiling
     tamper evidence                    runtime health
             │                           failure diagnosis
             │                                 │
             └────────────────┬────────────────┘
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
             AXPROCESS     AXMEMORY      AXTASK
                 │            │            │
                 └────────────┼────────────┘
                              ▼
                          AXSTORAGE
```

---

# 3. Strong boundary

## AXDIAGNOSTICS sở hữu

- runtime error context;
- crash capture;
- exception diagnostics;
- stack traces;
- register snapshots;
- thread execution snapshots;
- process diagnostics;
- memory diagnostics;
- resource diagnostics;
- health state;
- runtime counters;
- profiling;
- sampling;
- latency measurement;
- allocation diagnostics;
- deadlock diagnostics;
- async/task diagnostics;
- performance traces;
- diagnostic snapshots;
- dump generation;
- symbol/source mapping;
- failure reports;
- deterministic diagnostic replay.

## Không sở hữu

- security authorization;
- audit evidence;
- process lifecycle;
- memory allocation;
- scheduling;
- persistent storage;
- network transport;
- compiler itself.

---

# 4. Diagnostics ≠ Audit

Một crash có thể tạo:

```text
AXDIAGNOSTICS
    PROCESS_CRASH
    STACK
    REGISTERS
    MEMORY_CONTEXT
    THREAD_STATE
```

đồng thời tạo:

```text
AXAUDIT
    PROCESS_CRASHED
```

Hai record có mục đích khác nhau.

`AXAUDIT` không cần chứa raw diagnostic state.

---

# 5. Diagnostics ≠ logging

Application log:

```text
"loading configuration..."
```

không phải diagnostic state.

Diagnostic event có structured semantics:

```text
allocation_failure {
    allocator
    size
    process
    thread
    memory_budget
}
```

---

# 6. Diagnostic context

Core model:

```text
diagnostic_context {
    context_id
    timestamp
    monotonic_time
    process_id
    thread_id
    task_id
    module_id
    function_id
    source_location
    execution_state
    correlation_id
}
```

---

# 7. Error context

Axiom error object có thể giữ:

```text
error_context {
    error_code
    subsystem
    operation
    source_location
    cause
    native_code
    diagnostic_context
}
```

Không bắt buộc capture full stack cho mọi error.

---

# 8. Error hierarchy

Conceptual:

```text
error
 ├── IO_ERROR
 ├── MEMORY_ERROR
 ├── PROCESS_ERROR
 ├── IPC_ERROR
 ├── NETWORK_ERROR
 ├── STORAGE_ERROR
 ├── SECURITY_ERROR
 ├── DEVICE_ERROR
 ├── TASK_ERROR
 └── RUNTIME_ERROR
```

Subsystem vẫn giữ error taxonomy riêng.

`AXDIAGNOSTICS` chỉ cung cấp diagnostic envelope.

---

# 9. Cause chain

Error có thể có:

```text
cause
  ↓
cause
  ↓
root_cause
```

Không giới hạn bằng recursion vô hạn.

Có:

```text
max_cause_depth
```

---

# 10. Error propagation

Khi error đi qua task:

```text
operation
 ↓
error
 ↓
future
 ↓
task
 ↓
parent task
```

Diagnostic context phải có thể liên kết toàn chain.

---

# 11. Source location

Compiler có thể attach:

```text
file_id
line
column
function_id
instruction_offset
```

Build artifacts chứa source mapping riêng.

---

# 12. Debug symbols

Axiom binary có thể chứa hoặc tham chiếu:

```text
function symbols
line tables
type metadata
inline call information
module identity
build ID
```

Diagnostics không yêu cầu symbol data phải nằm trong executable.

---

# 13. Build identity

Mỗi native artifact nên có:

```text
build_id
compiler_version
target_triple
optimization_profile
source_revision
```

Build ID là primary identity để tìm symbols.

---

# 14. Crash record

```text
crash_record {
    crash_id
    process_id
    thread_id
    fault_class
    native_code
    instruction_pointer
    stack_pointer
    fault_address
    module
    timestamp
    dump_ref
    trace_ref
}
```

---

# 15. Fault classes

Baseline:

```text
ACCESS_VIOLATION
INVALID_INSTRUCTION
DIVIDE_ERROR
STACK_OVERFLOW
ILLEGAL_STATE
ASSERTION_FAILURE
EXPLICIT_PANIC
OUT_OF_MEMORY
RESOURCE_EXHAUSTION
DEVICE_FAULT
SYSTEM_EXCEPTION
```

Platform-specific faults được giữ dưới:

```text
native_fault_code
```

---

# 16. Crash boundary

Process crash không được làm crash diagnostics subsystem nếu có thể tránh.

Architecture:

```text
application
    │
    X crash
    │
    ▼
AXPROCESS
    │
    ▼
minimal crash capture
    │
    ▼
AXDIAGNOSTICS
```

---

# 17. Minimal crash path

Crash handler phải cực nhỏ:

```text
capture registers
capture fault metadata
capture stack bounds
capture process/thread IDs
write minimal crash record
```

Không:

- allocate arbitrary heap;
- perform network I/O;
- execute complex policy;
- acquire potentially deadlocked locks.

---

# 18. Crash-safe allocator

Diagnostics có reserved emergency memory:

```text
diagnostic_emergency_pool
```

dùng trong fatal paths.

---

# 19. Stack capture

Stack trace có thể ở:

```text
FAST
SAFE
FULL
```

profiles.

`FAST` dùng frame pointers/unwind metadata khi available.

`FULL` có thể dùng platform unwinding.

---

# 20. Stack unwinding

Axiom compiler phải emit unwind metadata cho supported targets.

Ví dụ:

```text
AXUNWIND_1
```

Metadata cho phép:

```text
instruction address
      ↓
frame
      ↓
caller
```

---

# 21. Async stack trace

Async task không có một native call stack liên tục.

Diagnostics phải reconstruct:

```text
task
 ↓
async state
 ↓
await point
 ↓
logical caller chain
```

Tách:

```text
physical stack
```

và:

```text
logical async stack
```

---

# 22. Task diagnostics

AXTASK cung cấp:

```text
task_id
parent_task
state
await_point
executor
worker
deadline
cancellation_state
```

AXDIAGNOSTICS tạo diagnostic view.

---

# 23. Deadlock diagnostics

Diagnostics có thể detect/observe:

```text
lock A → lock B
lock B → lock A
```

nhưng không tự thay đổi synchronization state.

---

# 24. Lock graph

```text
thread/task
    │
    ▼
wait
    │
    ▼
lock
    │
    ▼
owner
```

Graph có thể phát hiện cycles.

---

# 25. Wait diagnostics

Một blocked task/thread có:

```text
wait_reason
wait_object
wait_duration
wait_owner
```

nếu subsystem cung cấp metadata.

---

# 26. CPU profiling

AXDIAGNOSTICS hỗ trợ:

```text
sampling profiler
instrumentation profiler
counter profiler
```

Sampling là baseline để overhead thấp.

---

# 27. Sampling

Profiler có:

```text
sample_period
sample_frequency
target_process
target_threads
```

Không bắt buộc stop-world.

---

# 28. CPU sample

```text
cpu_sample {
    timestamp
    cpu
    process
    thread
    task
    instruction_pointer
    call_stack
}
```

---

# 29. Hardware counters

Nếu platform hỗ trợ:

```text
cycles
instructions
cache_miss
branch_miss
frontend_stall
backend_stall
```

AXDIAGNOSTICS chỉ cung cấp abstraction.

Không giả định mọi CPU có cùng counters.

---

# 30. GPU profiling

GPU diagnostics có:

```text
submission
queue
kernel
duration
memory_transfer
synchronization
```

AXGRAPHICS/AXCOMPUTE sở hữu actual GPU execution.

---

# 31. Memory diagnostics

Metrics:

```text
virtual_reserved
virtual_committed
resident
peak_resident
allocation_count
free_count
fragmentation
arena_usage
pool_usage
```

Nguồn chính từ AXMEMORY.

---

# 32. Allocation tracing

Optional:

```text
allocation_event {
    allocation_id
    size
    alignment
    allocator
    thread
    task
    source_location
}
```

Không bật mặc định cho production hot path.

---

# 33. Leak diagnostics

Vì Axiom không có mandatory GC, leak detection phải là diagnostics feature.

Có thể track:

```text
allocation
 ↓
owner/context
 ↓
release
```

Unreleased allocation khi shutdown/snapshot → candidate leak.

---

# 34. Ownership diagnostics

Nếu allocation API có owner metadata:

```text
allocation_owner
```

Diagnostics có thể hiển thị:

```text
who allocated?
where?
how long?
```

Không thay đổi memory semantics.

---

# 35. Use-after-free diagnostics

Debug allocator có thể dùng:

```text
poison
guard page
quarantine
generation
red zone
```

Các cơ chế backing thuộc AXMEMORY.

AXDIAGNOSTICS orchestrates/report chúng.

---

# 36. Memory corruption

Diagnostics có thể phát hiện:

```text
red-zone corruption
guard-page violation
invalid generation
checksum mismatch
```

và tạo structured report.

---

# 37. Heap snapshot

```text
heap_snapshot {
    process
    allocator_stats
    allocation_classes
    arena_stats
    fragmentation
}
```

Không nhất thiết capture mọi object bytes.

---

# 38. Full memory dump

Có thể yêu cầu:

```text
MINIDUMP
FULL_DUMP
CUSTOM_DUMP
```

Full dump là privileged/sensitive operation và phải chịu AXSECURITY.

---

# 39. Dump policy

```text
dump_policy {
    mode
    max_size
    include_heap
    include_stacks
    include_modules
    include_memory_ranges
    redact_sensitive
}
```

---

# 40. Sensitive memory

Dump có thể chứa:

- credentials;
- session keys;
- user data;
- application secrets.

Vì vậy dump generation phải:

```text
AXSECURITY
    +
redaction policy
```

---

# 41. Dump encryption

Nếu dump được lưu persistent:

```text
AXCRYPTO
```

có thể cung cấp encryption.

AXDIAGNOSTICS không tự implement crypto.

---

# 42. Dump format

Axiom native:

```text
AXDUMP_1
```

có:

```text
header
process metadata
module table
thread table
register blocks
stack blocks
memory regions
diagnostic events
symbol references
```

---

# 43. Module table

```text
module {
    module_id
    build_id
    base_address
    size
    path
    symbol_ref
}
```

---

# 44. ASLR

Diagnostics không assume module base address cố định.

Stack/module symbolization sử dụng runtime load addresses.

---

# 45. Symbolication

Flow:

```text
IP
 ↓
module + offset
 ↓
build_id
 ↓
symbol database
 ↓
function
 ↓
source location
```

---

# 46. Inlined functions

Symbolication nên hỗ trợ:

```text
inline frame
```

để stack trace phản ánh compiler optimization.

---

# 47. Optimized builds

Diagnostics phải hoạt động dù:

```text
-O2
-O3
LTO
function merging
inlining
```

Một số source locations có thể unavailable.

Không được giả tạo source location.

---

# 48. Runtime health

Core:

```text
health_state {
    subsystem
    state
    scoreless_status
    reason
    since
    metrics
}
```

Không dùng score/ranking.

States:

```text
HEALTHY
DEGRADED
FAILING
FAILED
RECOVERING
UNKNOWN
```

---

# 49. Health aggregation

System health:

```text
AXPROCESS
AXMEMORY
AXTASK
AXASYNC
AXNETWORK
AXSTORAGE
...
```

có thể aggregate.

Aggregation phải giữ source state, không che mất failure.

---

# 50. Health checks

```text
health_check {
    check_id
    subsystem
    interval
    timeout
    severity
}
```

Checks phải bounded.

---

# 51. Liveness vs readiness

Phân biệt:

```text
LIVENESS
```

process còn hoạt động;

```text
READINESS
```

process có thể nhận work.

Không đồng nhất hai khái niệm.

---

# 52. Dependency health

Service:

```text
SERVICE_A
   ↓
SERVICE_B
   ↓
DATABASE
```

Diagnostics có thể biểu diễn dependency graph.

Không tự restart service.

AXAPPLICATION/AXPROCESS/supervisor quyết định lifecycle.

---

# 53. Runtime counters

Subsystem có thể expose:

```text
counter
gauge
histogram
```

AXDIAGNOSTICS cung cấp common collection ABI.

---

# 54. Histograms

Ví dụ latency:

```text
0–1 us
1–10 us
10–100 us
...
```

Bucket configuration explicit.

---

# 55. High-resolution timing

Diagnostics có:

```text
monotonic_timestamp()
duration()
```

nhưng timing source implementation thuộc platform runtime.

---

# 56. Trace spans

Structured trace:

```text
span {
    span_id
    parent_span
    operation
    start
    end
    attributes
}
```

---

# 57. Trace context

Có thể truyền qua:

```text
AXTASK
AXIPC
AXNETWORK
AXASYNC
```

nhưng propagation phải explicit.

---

# 58. Trace ≠ audit

Trace:

```text
performance/correlation
```

Audit:

```text
accountability/security evidence
```

Không dùng trace làm security audit substitute.

---

# 59. Trace sampling

Trace có thể sampling:

```text
NONE
HEAD
TAIL
RATE
ERROR_ONLY
```

Security audit sampling rules không áp dụng vào trace.

---

# 60. Performance overhead profiles

```text
OFF
MINIMAL
NORMAL
DETAILED
DEBUG
```

Production mặc định nên hướng tới `MINIMAL`.

---

# 61. Diagnostics channels

```text
DIAGNOSTIC_EVENT
DIAGNOSTIC_TRACE
DIAGNOSTIC_METRIC
DIAGNOSTIC_DUMP
DIAGNOSTIC_PROFILE
```

Mỗi channel có lifecycle riêng.

---

# 62. Diagnostic session

```text
diagnostic_session {
    session_id
    target
    profile
    start_time
    end_time
    collectors
}
```

---

# 63. Collector

```text
collector {
    collector_id
    type
    target
    interval
    buffer
}
```

Ví dụ:

```text
CPU
MEMORY
TASK
IO
LOCK
NETWORK
GPU
```

---

# 64. Collector isolation

Một collector crash không được crash target application.

Collector chạy:

```text
out-of-process
```

khi cần isolation.

---

# 65. Snapshot

Diagnostic snapshot:

```text
diagnostic_snapshot {
    snapshot_id
    timestamp
    target
    process_state
    thread_state
    task_state
    memory_summary
    resource_summary
    active_traces
}
```

Snapshot không nhất thiết freeze process.

---

# 66. Consistency level

Snapshot có:

```text
BEST_EFFORT
COORDINATED
STOP_THE_WORLD
```

`STOP_THE_WORLD` chỉ explicit.

---

# 67. Runtime freeze

Diagnostics không tự freeze arbitrary process.

Nếu yêu cầu:

```text
PROCESS.SUSPEND
```

phải qua AXPROCESS + AXSECURITY.

---

# 68. Diagnostic trigger

Triggers:

```text
ON_CRASH
ON_EXCEPTION
ON_THRESHOLD
ON_LATENCY
ON_MEMORY_PRESSURE
ON_DEADLOCK
ON_MANUAL_REQUEST
```

---

# 69. Threshold trigger

Ví dụ:

```text
heap > limit
```

có thể trigger snapshot.

Diagnostics chỉ thu thập.

Không tự kill process.

---

# 70. Failure report

```text
failure_report {
    report_id
    failure_class
    summary
    process
    thread
    task
    stack
    modules
    relevant_metrics
    trace_refs
    dump_ref
    causal_events
}
```

---

# 71. Root cause boundary

AXDIAGNOSTICS có thể cung cấp:

```text
candidate_cause
```

nhưng không được biến heuristic thành fact.

Ví dụ:

```text
likely allocation exhaustion
```

phải được biểu diễn là diagnostic inference.

---

# 72. Diagnostic confidence

Nếu inference engine được sử dụng:

```text
diagnostic_finding {
    finding_type
    evidence[]
    inference
    confidence
}
```

`confidence` chỉ mô tả inference model, không phải security authority.

---

# 73. AI diagnostics

AI có thể:

- đọc crash report;
- giải thích stack;
- nhóm lỗi;
- tìm tương quan;
- đề xuất reproduction;
- phân tích performance;
- phát hiện regression;
- phân tích deadlock graph;
- tìm allocation hotspots.

AI không được:

- bypass AXSECURITY;
- đọc protected dump nếu chưa được phép;
- sửa runtime state;
- tự restart/kill process;
- tự disable diagnostics;
- xóa evidence.

---

# 74. Deterministic replay

Diagnostics hỗ trợ replay khi subsystem có replay support:

```text
input
+
scheduler decisions
+
timing model
+
I/O results
```

Không hứa bit-exact replay của arbitrary native hardware execution.

---

# 75. Crash reproduction

Diagnostic report có thể lưu:

```text
build_id
configuration
environment metadata
input reference
trace reference
```

Sensitive input phải được redacted theo policy.

---

# 76. Fault injection

Test-only API:

```text
diagnostic_inject_fault()
```

Các fault:

```text
OUT_OF_MEMORY
IO_ERROR
TIMEOUT
TASK_FAILURE
DEVICE_ERROR
CORRUPTION
SCHEDULING_DELAY
```

Không expose unrestricted production fault injection.

---

# 77. Deterministic fault IDs

Simulation:

```text
fault_id
scenario_id
seed
```

để reproduction.

---

# 78. Native APIs

Baseline:

```text
diagnostics_init()
diagnostics_shutdown()

diagnostics_get_error_context()
diagnostics_capture_stack()
diagnostics_capture_thread()
diagnostics_capture_process()

diagnostics_create_dump()
diagnostics_open_dump()
diagnostics_verify_dump()
diagnostics_close_dump()

diagnostics_symbolize()
diagnostics_resolve_source()

diagnostics_create_session()
diagnostics_start_session()
diagnostics_stop_session()

diagnostics_start_profiler()
diagnostics_stop_profiler()
diagnostics_sample_now()

diagnostics_start_trace()
diagnostics_stop_trace()

diagnostics_snapshot()
diagnostics_get_health()
diagnostics_run_health_check()

diagnostics_get_metrics()
diagnostics_get_counter()
diagnostics_get_histogram()

diagnostics_get_task_state()
diagnostics_get_lock_graph()
diagnostics_get_memory_stats()

diagnostics_create_report()
diagnostics_export_report()

diagnostics_simulate()
diagnostics_replay()
diagnostics_inject_fault()

diagnostics_get_stats()
diagnostics_get_capabilities()
```

---

# 79. Compiler ABI

Baseline:

```text
AXDIAGNOSTICS_ABI_1
```

Compiler emit:

```text
unwind metadata
source map
function metadata
inline metadata
build ID
type diagnostics metadata
```

---

# 80. Panic / fatal path

Axiom có thể có:

```text
panic()
fatal()
assert()
```

Semantics:

```text
panic
    ↓
capture diagnostic context
    ↓
optional unwind
    ↓
task/process policy
```

`fatal`:

```text
minimal capture
↓
process termination boundary
```

Không bắt buộc full heap allocation.

---

# 81. Assertions

Build profiles:

```text
RELEASE
CHECKED
DEBUG
```

Assertions có thể khác nhau.

Security invariants không được biến thành ordinary debug assertions.

---

# 82. Diagnostic metadata attributes

Compiler có thể hỗ trợ:

```text
@diagnostic_name
@trace
@profile
@no_trace
@capture_on_error
```

`@no_trace` không được vô hiệu hóa mandatory security audit.

---

# 83. No hidden runtime tax

Một function không dùng diagnostics:

```text
fn fast_math(...)
```

không nên tự động mang theo heavy tracing machinery.

Instrumentation phải:

```text
compile-time
or
explicit runtime profile
```

---

# 84. Hot-path instrumentation

Có thể sử dụng:

```text
branch-light counters
per-core counters
sampling
```

thay vì mutex-protected global counters.

---

# 85. Lock-free diagnostic event path

Baseline:

```text
producer
 ↓
per-core ring
 ↓
consumer
```

Không global lock trong normal event emission.

---

# 86. Memory bounds

Diagnostics phải có:

```text
max_event_size
max_buffer_size
max_dump_size
max_trace_duration
max_snapshot_size
```

Không được consume unlimited resources.

---

# 87. Backpressure

Diagnostic streams:

```text
BLOCK
DROP
SAMPLE
FAIL
```

Default operational telemetry có thể drop/sample.

Crash capture không được đơn giản drop vì buffer pressure.

---

# 88. Persistent storage

AXDIAGNOSTICS tạo artifact:

```text
dump
report
profile
trace
snapshot
```

Persistence semantics thuộc AXSTORAGE.

---

# 89. Security integration

Dump/read/profile privileged resources:

```text
AXSECURITY
```

phải authorize.

Ví dụ:

```text
PROCESS.DUMP
PROCESS.DEBUG
PROCESS.READ_MEMORY
DIAGNOSTICS.READ_SENSITIVE
```

---

# 90. Audit integration

Administrative diagnostic action:

```text
CREATE_DUMP
READ_SENSITIVE_DUMP
START_PROFILER
DEBUG_PROCESS
```

có thể phát audit event qua AXAUDIT.

AXDIAGNOSTICS không tự ghi security evidence semantics.

---

# 91. Canonical flow — crash

```text
application
    ↓
fault
    ↓
AXPROCESS crash boundary
    ↓
minimal capture
    ↓
AXDIAGNOSTICS
    ├── crash record
    ├── stack
    ├── registers
    ├── module map
    └── optional dump
           │
           ▼
       AXSTORAGE
```

Song song:

```text
AXAUDIT
    ↓
PROCESS_CRASHED
```

---

# 92. Canonical flow — performance

```text
diagnostic session
       ↓
CPU sampler
       ↓
per-core buffers
       ↓
symbolization
       ↓
profile
       ↓
report
```

---

# 93. Canonical flow — memory leak

```text
AXMEMORY
    ↓
allocation metadata
    ↓
AXDIAGNOSTICS
    ↓
snapshot
    ↓
unreleased allocation analysis
    ↓
failure/performance report
```

---

# 94. Canonical flow — deadlock

```text
AXSYNC
  ↓
wait/ownership metadata
  ↓
AXDIAGNOSTICS
  ↓
wait graph
  ↓
cycle detection
  ↓
diagnostic finding
```

Không tự unlock.

---

# 95. Canonical flow — async failure

```text
AXTASK
  ↓
task failure
  ↓
future/promise
  ↓
AXDIAGNOSTICS
  ├── physical stack
  ├── logical async stack
  ├── task ancestry
  └── await point
```

---

# 96. Canonical flow — dump security

```text
request dump
    ↓
AXSECURITY
    ├── PROCESS.DUMP
    ├── target authority
    └── sensitive-data policy
    ↓
AXDIAGNOSTICS
    ↓
dump generation
    ↓
optional redaction/encryption
    ↓
AXSTORAGE
```

---

# 97. Formal invariants

`AXDIAGNOSTICS 5.0` định nghĩa tối thiểu:

```text
DIAG-INV-01   Diagnostic event phải có stable event identity.
DIAG-INV-02   Diagnostic context phải có subsystem/source.
DIAG-INV-03   Error context phải giữ error code nguyên bản.
DIAG-INV-04   Cause chain phải có bounded depth.
DIAG-INV-05   Native error code không được bị mất khi normalize.
DIAG-INV-06   Source location chỉ được ghi khi compiler/runtime có evidence.
DIAG-INV-07   Build ID phải xác định artifact dùng để symbolization.
DIAG-INV-08   ASLR load address phải được xử lý khi symbol hóa.
DIAG-INV-09   Unwind metadata phải versioned.
DIAG-INV-10   Crash capture path không được phụ thuộc unrestricted heap allocation.
DIAG-INV-11   Crash handler không được phụ thuộc network availability.
DIAG-INV-12   Crash handler phải có bounded execution path.
DIAG-INV-13   Diagnostic emergency memory phải được reserve.
DIAG-INV-14   Partial dump không được tuyên bố là full dump.
DIAG-INV-15   Sensitive dump access phải qua AXSECURITY.
DIAG-INV-16   Diagnostic subsystem không được tự cấp privilege.
DIAG-INV-17   Diagnostics không được thay đổi security decision.
DIAG-INV-18   Diagnostics không được tự kill/restart process.
DIAG-INV-19   Physical stack và logical async stack phải được phân biệt.
DIAG-INV-20   Sampling profiler không được mặc định stop-the-world.
DIAG-INV-21   Hardware counters phải có capability metadata.
DIAG-INV-22   Diagnostic collectors phải có resource bounds.
DIAG-INV-23   Operational telemetry có thể drop/sample theo explicit policy.
DIAG-INV-24   Mandatory crash capture không được coi là ordinary droppable telemetry.
DIAG-INV-25   Diagnostic snapshot phải khai báo consistency level.
DIAG-INV-26   Snapshot không được ngầm hiểu là globally atomic nếu không có guarantee.
DIAG-INV-27   Memory statistics phải phân biệt virtual và resident memory.
DIAG-INV-28   Allocation diagnostics không được thay đổi ownership semantics.
DIAG-INV-29   Leak detection không được đồng nghĩa với memory reclamation.
DIAG-INV-30   Deadlock detection không được tự mutate synchronization state.
DIAG-INV-31   Trace không được thay thế security audit.
DIAG-INV-32   Diagnostic replay không được tự re-execute privileged actions.
DIAG-INV-33   Fault injection phải được giới hạn bởi test/simulation authority.
DIAG-INV-34   Diagnostic inference phải phân biệt evidence và hypothesis.
DIAG-INV-35   AI-generated diagnosis không được coi là authoritative runtime fact.
DIAG-INV-36   Diagnostic artifacts phải có format/version metadata.
DIAG-INV-37   Dump persistence phải tôn trọng storage và security policy.
DIAG-INV-38   Diagnostic buffer phải có bounded memory consumption.
DIAG-INV-39   Normal diagnostics path không được bắt buộc heap allocation cho mỗi event.
DIAG-INV-40   AI không được đọc, sửa, xóa hoặc export protected diagnostic data nếu không có authority.
```

---

# 98. Definition of Done

`AXDIAGNOSTICS 5.0` được freeze khi Axiom có đầy đủ:

- structured error context;
- cause chains;
- source locations;
- build IDs;
- symbol metadata;
- unwind metadata;
- crash capture;
- emergency crash memory;
- stack capture;
- register capture;
- async logical stack;
- process diagnostics;
- thread diagnostics;
- task diagnostics;
- deadlock/wait graph;
- memory diagnostics;
- allocation diagnostics;
- leak diagnostics;
- corruption diagnostics;
- heap snapshots;
- minidump/full dump;
- dump security;
- dump redaction;
- dump encryption integration;
- CPU profiler;
- hardware-counter profiler;
- GPU diagnostics integration;
- runtime health;
- liveness/readiness;
- dependency health;
- metrics;
- counters;
- histograms;
- tracing;
- diagnostic sessions;
- snapshots;
- consistency modes;
- failure reports;
- deterministic replay;
- fault injection;
- compiler diagnostics ABI;
- native APIs;
- AXSECURITY integration;
- AXAUDIT integration;
- AXSTORAGE integration;
- bounded resource usage;
- fast-path instrumentation;
- AI diagnostics boundary;
- 40 formal invariants.

**AXDIAGNOSTICS 5.0 → FROZEN.**

---

# BOOTSTRAP-761 — AXOBSERVABILITY

**Native Metrics, Tracing, Telemetry Pipeline, Runtime Monitoring, Health Aggregation & Observability Runtime 5.0**

Tầng tiếp theo sẽ tách tiếp một abstraction quan trọng:

```text
AXAUDIT
    = accountability/evidence

AXDIAGNOSTICS
    = failure/debug/performance investigation

AXOBSERVABILITY
    = continuous system-wide observation
```

Kiến trúc dự kiến:

```text
 AXPROCESS ─────┐
 AXTASK ────────┤
 AXASYNC ───────┤
 AXNETWORK ─────┤
 AXSTORAGE ─────┤
 AXCOMPUTE ─────┤
 AXGRAPHICS ────┤
 AXAUDIO ───────┤
 AXMEMORY ──────┤
                ▼
        ┌─────────────────┐
        │ AXOBSERVABILITY │
        │                 │
        │ metrics         │
        │ traces          │
        │ telemetry       │
        │ health          │
        │ aggregation     │
        │ exporters       │
        └────────┬────────┘
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
     console   GUI      remote
```

Điểm thiết kế quan trọng của `AXOBSERVABILITY` sẽ là **không biến Axiom thành một hệ thống telemetry nặng kiểu “mọi thứ đều phải serialize + allocate + network”**. Hot path vẫn phải giữ mục tiêu zero/minimal overhead, còn collection/export là các pipeline độc lập có thể bật/tắt và scale riêng.