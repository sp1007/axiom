# BOOTSTRAP-475 — LOGGING, TRACING, METRICS, TELEMETRY & OBSERVABILITY FOUNDATION

**Trạng thái: COMPLETED / LOCKED**

475 khóa observability cho Axiom compiler, runtime và application. Observability là **capability tùy chọn**, không phải hidden runtime behavior.

```text
Program / Compiler / Runtime
            │
     ┌──────┼──────┐
     ↓      ↓      ↓
    Log   Trace   Metric
     │      │      │
     └──────┼──────┘
            ↓
     Observability API
            │
       ┌────┴────┐
       ↓         ↓
    Local      Exporter
```

---

## 475.1 — Log

Log là record mô tả một sự kiện hoặc trạng thái đáng chú ý.

```text
LogRecord {
    timestamp
    level
    target
    message
    fields
    source
    context
}
```

---

## 475.2 — Log level

Canonical levels:

```text
Trace
Debug
Info
Warn
Error
```

`Fatal` không bắt buộc; panic/abort đã có semantics riêng.

---

## 475.3 — Structured logging

Log phải hỗ trợ fields có kiểu:

```text
user_id: 42
duration: 15ms
status: "ok"
```

thay vì chỉ nối chuỗi.

---

## 475.4 — Message formatting

Formatting có thể lazy.

Nếu level bị disable, formatter không nên thực hiện computation không cần thiết.

---

## 475.5 — Compile-time filtering

Có thể loại bỏ log level ngay khi compile:

```text
debug logging → no emitted code
```

nếu configuration cho phép.

---

## 475.6 — Runtime filtering

Có thể thay đổi filtering khi runtime.

Không được mặc định tạo hidden synchronization cho mọi log call.

---

# 475.7 — Logging target

Target/category cho phép phân nhóm:

```text
network
database
gui
audio
gpu
compiler
application
```

---

## 475.8 — Source location

Compiler có thể gắn:

```text
FileId
line
column
function
```

vào log metadata.

---

## 475.9 — Thread/task identity

Runtime logging có thể ghi:

```text
process_id
thread_id
task_id
```

khi capability được bật.

---

## 475.10 — Actor identity

472 actor system có thể thêm:

```text
ActorId
```

vào observability context.

---

# 475.11 — Trace

Trace mô tả một execution flow.

```text
Trace
 ├── Span A
 │    ├── Span B
 │    └── Span C
 └── Span D
```

---

## 475.12 — Span

Span biểu diễn một operation có thời gian bắt đầu/kết thúc.

```text
Span {
    trace_id
    span_id
    parent_id
    start
    end
    attributes
    status
}
```

---

## 475.13 — Trace identity

Trace ID phải là logical identifier, không phụ thuộc memory address.

---

## 475.14 — Span identity

Span ID cũng phải độc lập với pointer/address.

---

## 475.15 — Parent-child

Span có thể có parent span.

---

## 475.16 — Async context

Context phải có thể đi qua async suspension/resumption mà không phụ thuộc OS thread.

---

## 475.17 — Thread migration

Nếu task migrate thread, trace context vẫn giữ nguyên.

---

# 475.18 — Actor tracing

Actor message có thể tạo span:

```text
send
 ↓
queue wait
 ↓
dispatch
 ↓
handler
```

Giúp phân biệt **processing latency** và **mailbox latency**.

---

## 475.19 — Channel tracing

Channel có thể instrument send/receive.

Instrumentation phải optional.

---

## 475.20 — Network propagation

454 network layer có thể propagate trace context.

Không tự động gửi telemetry ra Internet.

---

# 475.21 — Metric

Metric là measurement được aggregate.

Canonical types:

```text
Counter
Gauge
Histogram
```

---

## 475.22 — Counter

Chỉ tăng hoặc reset theo lifecycle.

Ví dụ:

```text
requests_total
bytes_written
errors_total
```

---

## 475.23 — Gauge

Biểu diễn giá trị hiện tại:

```text
queue_depth
memory_used
active_connections
```

---

## 475.24 — Histogram

Đo phân bố:

```text
latency
request_size
frame_time
allocation_size
```

---

## 475.25 — Histogram buckets

Bucket configuration phải explicit.

---

## 475.26 — Quantiles

Quantile computation là aggregation policy, không phải semantics bắt buộc của histogram.

---

# 475.27 — Metric labels

Metrics có thể có dimensions:

```text
method
status
device
codec
target
```

---

## 475.28 — Cardinality

Runtime có thể giới hạn cardinality để tránh metric explosion.

---

## 475.29 — Dynamic labels

Dynamic arbitrary strings không nên được phép vô hạn trong production metric path.

---

# 475.30 — Context

Observability context có thể chứa:

```text
trace
span
request
actor
task
session
```

---

## 475.31 — Context propagation

Context truyền explicit hoặc qua well-defined execution context.

Không được tạo global mutable state bắt buộc.

---

## 475.32 — Context ownership

Context phải tuân ownership/thread-safety semantics của 423/424.

---

# 475.33 — Exporter

Exporter chuyển observability data tới sink.

```text
Console
File
Memory
IPC
Network
```

---

## 475.34 — Sink

Sink là destination thực tế.

Exporter và sink có thể tách abstraction.

---

## 475.35 — Console sink

Human-readable output.

---

## 475.36 — Structured sink

JSON/binary/other structured representation.

Schema phải versioned.

---

# 475.37 — Buffering

Observability pipeline có thể buffer records để giảm overhead.

---

## 475.38 — Bounded buffer

Production logging nên hỗ trợ bounded buffering.

---

## 475.39 — Buffer overflow

Policy phải explicit:

```text
DropNewest
DropOldest
Block
Reject
Flush
```

---

## 475.40 — Dropped record accounting

Nếu record bị drop, hệ thống nên cung cấp metric/counter cho số record bị mất.

---

# 475.41 — Async logging

Async logging có thể dùng 424/471.

Không tự tạo hidden worker thread.

---

## 475.42 — Synchronous logging

Synchronous sink phù hợp debugging đơn giản nhưng có thể block caller.

---

## 475.43 — Blocking metadata

API có thể khai báo effect:

```text
@blocking
```

cho sink có khả năng blocking.

---

# 475.44 — Realtime logging

`@realtime` không được gọi logging thông thường nếu logging có:

- allocation;
- lock;
- blocking;
- unbounded queue;
- filesystem/network IO.

---

## 475.45 — Realtime event buffer

Có thể cung cấp fixed-size realtime telemetry buffer.

```text
preallocated
bounded
lock-free/SPSC
```

nếu phù hợp.

---

## 475.46 — Deferred formatting

Realtime path chỉ ghi primitive event data; formatting thực hiện ngoài realtime thread.

---

# 475.47 — Sensitive data

Observability API phải hỗ trợ field classification:

```text
Public
Internal
Sensitive
Secret
```

---

## 475.48 — Secret redaction

Secret fields phải có khả năng bị redacted trước khi xuất.

---

## 475.49 — Passwords/tokens

Password, API key, private key, authentication token không được tự động đưa vào log.

---

## 475.50 — Memory safety

Logging không được giữ reference tới temporary data lâu hơn lifetime hợp lệ.

---

# 475.51 — Privacy

Application phải có khả năng disable hoặc filter observability data.

---

## 475.52 — No automatic upload

Axiom không được tự động upload logs/metrics/traces.

---

## 475.53 — No hidden telemetry

Compiler/runtime không được âm thầm gửi telemetry.

---

# 475.54 — Crash integration

440/425 có thể phát:

```text
panic
abort
unhandled error
```

thành diagnostic event.

---

## 475.55 — Crash context

Crash report có thể liên kết:

```text
trace_id
span_id
thread
task
actor
source location
```

nếu instrumentation được bật.

---

## 475.56 — Crash safety

Crash reporting không được giả định rằng heap/process state luôn còn nguyên.

---

# 475.57 — Performance instrumentation

450 có thể sử dụng tracing/metrics để đo:

```text
compile phase
optimization
codegen
link
startup
runtime
```

---

## 475.58 — Compiler tracing

Compiler có thể trace query:

```text
parse
resolve
type_check
const_eval
MIR
optimization
codegen
link
```

---

## 475.59 — Query timing

436 query engine có thể expose:

```text
query name
duration
cache hit
cache miss
dependency
```

---

# 475.60 — Allocation metrics

423/450 có thể expose:

```text
allocation_count
allocated_bytes
freed_bytes
peak_live_bytes
```

---

## 475.61 — Lock metrics

424/471 có thể expose:

```text
contention_count
wait_duration
hold_duration
```

Không được instrument mọi lock mặc định nếu binary-size/performance profile không cho phép.

---

# 475.62 — IO metrics

454/455 có thể expose:

```text
bytes_read
bytes_written
operations
latency
errors
```

---

## 475.63 — Database metrics

455 có thể expose:

```text
queries
transactions
cache_hits
lock_wait
commit_latency
```

---

# 475.64 — GUI metrics

452 có thể expose:

```text
frame_time
layout_time
render_time
input_latency
```

---

## 475.65 — Media metrics

461/462:

```text
audio_callback_time
buffer_underrun
decode_latency
encode_latency
dropped_frames
A/V drift
```

---

## 475.66 — GPU metrics

459/460:

```text
kernel_time
queue_wait
transfer_bytes
transfer_time
GPU memory
```

---

# 475.67 — Resource metrics

469:

```text
load_time
cache_hit
cache_miss
decode_time
GPU_upload_time
memory_usage
```

---

# 475.68 — Sampling

Tracing có thể sampling theo:

```text
probability
rate
duration
priority
```

---

## 475.69 — Head sampling

Decision ở trace start.

---

## 475.70 — Tail sampling

Decision sau khi trace hoàn thành.

Tail sampling thường cần buffering.

---

## 475.71 — Sampling determinism

Test mode có thể sử dụng deterministic sampling.

---

# 475.72 — Overhead measurement

Observability subsystem phải có benchmark đo:

```text
disabled overhead
enabled overhead
logging overhead
tracing overhead
metrics overhead
export overhead
```

---

## 475.73 — Zero-overhead disabled path

Khi compile-time disabled, compiler phải loại bỏ càng nhiều instrumentation code càng tốt.

---

# 475.74 — Binary size

Observability capability phải được link/prune theo usage.

Không kéo network exporter vào executable chỉ vì logging core được import.

---

# 475.75 — Build profiles

Có thể có:

```text
observability = off
observability = minimal
observability = debug
observability = full
```

---

# 475.76 — Deterministic test sink

Test suite có thể dùng in-memory sink để assert:

```text
events
fields
ordering
spans
metrics
```

---

## 475.77 — Replay

Recorded observability data có thể replay trong tooling.

Replay không được giả định là replay toàn bộ application execution.

---

# 475.78 — AI integration

446 expose observability graph:

```text
source
→ function
→ task
→ thread
→ actor
→ span
→ IO
→ resource
```

---

## 475.79 — Explain latency

AI tooling có thể phân rã latency:

```text
queue wait
+ scheduler wait
+ IO wait
+ computation
+ lock wait
+ GPU wait
```

---

## 475.80 — Explain performance regression

Tooling có thể so sánh two traces/metric snapshots và xác định **observed differences**, không tự động gán nguyên nhân khi dữ liệu chưa đủ.

---

# 475.81 — Security boundary

Network exporter phải coi endpoint/configuration là external resource.

---

## 475.82 — TLS

Network telemetry nếu sử dụng network/TLS phải đi qua 454.

Observability core không tự triển khai network stack riêng.

---

# 475.83 — Configuration

Observability configuration tích hợp 468/470.

Precedence phải deterministic.

---

## 475.84 — Environment configuration

Production configuration có thể đến từ environment/config file/CLI.

Không được để environment variable âm thầm bật external telemetry nếu application policy cấm.

---

# 475.85 — Testing

Test:

```text
log filtering
structured fields
trace nesting
async propagation
actor propagation
metric aggregation
sampling
buffer overflow
redaction
shutdown flush
```

---

## 475.86 — Concurrency testing

Test simultaneous writers/readers, sink failure, exporter shutdown và cancellation.

---

## 475.87 — Fuzzing

Fuzz:

```text
structured fields
formatters
serializers
trace context
metric labels
configuration
```

---

# 475.88 — Failure behavior

Observability failure **không được mặc định làm application failure**.

Ví dụ network telemetry unavailable:

```text
application continues
telemetry may drop
```

trừ khi application explicitly yêu cầu fail-closed semantics.

---

## 475.89 — Flush

Explicit:

```text
flush()
```

để đảm bảo pending observability data được gửi tới sink trong khả năng sink cho phép.

---

## 475.90 — Shutdown

468 application shutdown có thể yêu cầu flush observability.

Shutdown timeout phải được tôn trọng.

---

# 475.91 — Hard invariants

1. Log khác Trace.
2. Trace khác Metric.
3. Metric khác Profile.
4. Observability không thuộc language core.
5. Observability không phải hidden runtime behavior.
6. Structured logging được hỗ trợ.
7. Log levels có semantics rõ ràng.
8. Compile-time filtering được hỗ trợ.
9. Runtime filtering được hỗ trợ.
10. Disabled logging có thể bị compiler loại bỏ.
11. Log target/category được hỗ trợ.
12. Source location có thể được gắn.
13. Thread/task identity có thể được gắn.
14. Actor identity có thể được gắn.
15. Trace ID độc lập memory address.
16. Span ID độc lập memory address.
17. Async context được propagate.
18. Thread migration không phá trace context.
19. Parent-child spans được hỗ trợ.
20. Actor tracing được hỗ trợ.
21. Network trace propagation là explicit.
22. Metric Counter được hỗ trợ.
23. Gauge được hỗ trợ.
24. Histogram được hỗ trợ.
25. Metric labels được hỗ trợ.
26. Metric cardinality phải có kiểm soát.
27. Dynamic unbounded labels không được khuyến khích trong production.
28. Context không yêu cầu global mutable state.
29. Context tuân ownership/thread safety.
30. Exporter và sink là abstractions.
31. Console sink được hỗ trợ.
32. Structured sink được hỗ trợ.
33. Buffering là optional.
34. Bounded buffering được hỗ trợ.
35. Overflow policy phải explicit.
36. Dropped records có thể được đếm.
37. Async logging không tạo hidden thread.
38. Blocking sink phải có blocking semantics.
39. Realtime logging thường bị hạn chế.
40. Realtime telemetry buffer có thể preallocate.
41. Deferred formatting được hỗ trợ.
42. Sensitive fields có classification.
43. Secret redaction được hỗ trợ.
44. Password/token/private-key data không được tự động log.
45. Logging phải tuân lifetime của dữ liệu.
46. Privacy filtering được hỗ trợ.
47. Không automatic telemetry upload.
48. Không hidden network telemetry.
49. Crash context có thể liên kết trace/span.
50. Crash reporting không giả định process state luôn hợp lệ.
51. Compiler query tracing được hỗ trợ.
52. Build-phase timing được hỗ trợ.
53. Allocation metrics được hỗ trợ.
54. Lock contention metrics được hỗ trợ.
55. IO metrics được hỗ trợ.
56. Database metrics được hỗ trợ.
57. GUI metrics được hỗ trợ.
58. Audio/media metrics được hỗ trợ.
59. GPU metrics được hỗ trợ.
60. Resource metrics được hỗ trợ.
61. Trace sampling được hỗ trợ.
62. Sampling policy phải explicit.
63. Deterministic sampling có test mode.
64. Observability overhead phải benchmark được.
65. Disabled path phải tối ưu.
66. Binary size phải scale theo capability.
67. Build profiles có observability configuration.
68. Deterministic test sink được hỗ trợ.
69. Replay không được giả định là full execution replay.
70. AI có thể query observability graph.
71. AI có thể phân rã observed latency.
72. AI có thể so sánh telemetry snapshots.
73. AI không được tự suy diễn nguyên nhân khi evidence thiếu.
74. Network exporter sử dụng 454.
75. TLS exporter sử dụng 454.
76. Configuration tích hợp 468/470.
77. Observability failure không mặc định crash application.
78. Flush là explicit operation.
79. Shutdown flush có timeout semantics.
80. Observability có fuzzing.
81. Observability có concurrency testing.
82. Observability không yêu cầu GC.
83. Không yêu cầu borrow checker.
84. Không yêu cầu network.
85. Không yêu cầu database.
86. Không yêu cầu GUI.
87. Không yêu cầu actor runtime.
88. Không tạo hidden threads.
89. Không tạo hidden network connections.
90. **Axiom observability foundation phải cho phép quan sát compiler, runtime và application từ source đến task/thread/actor/IO/GPU/media/resource, nhưng khi disabled phải gần như biến mất khỏi executable và tuyệt đối không tạo telemetry hoặc runtime machinery ngầm.**

**BOOTSTRAP-475 hoàn tất.**

---

# BOOTSTRAP-476 — PROFILING, SAMPLING, PERFORMANCE COUNTERS, CPU/GPU PROFILER & HOT-PATH ANALYSIS

476 sẽ đi sâu hơn 450/475 vào **profiling thực sự**, vì telemetry cho biết *điều gì xảy ra*, còn profiler phải giúp xác định *thời gian/tài nguyên đang được tiêu thụ ở đâu*.

Kiến trúc:

```text
Execution
   │
   ├── CPU Samples
   ├── Hardware Counters
   ├── Allocation Samples
   ├── Lock/Wait Samples
   ├── IO Samples
   ├── GPU Samples
   └── Timeline Events
             │
             ↓
        Profile Session
             │
      ┌──────┼─────────┐
      ↓      ↓         ↓
   CallTree Timeline HotPath
      │      │         │
      └──────┼─────────┘
             ↓
      Source / IR / ASM
             ↓
       AI Analysis
```

476 sẽ khóa:

- sampling profiler;
- instrumentation profiler;
- call stacks;
- inline frame reconstruction;
- async stacks;
- thread/task/actor attribution;
- CPU time vs wall time;
- on-CPU/off-CPU time;
- scheduler wait;
- lock contention;
- allocation profiling;
- heap sampling;
- lifetime profiling;
- cache-miss counters;
- branch-miss counters;
- instruction counters;
- cycle counters;
- SIMD utilization;
- CPU frequency effects;
- hardware performance counters;
- platform counter abstraction;
- privilege restrictions;
- low-overhead profiling;
- high-detail profiling;
- statistical confidence;
- sample frequency;
- profiling bias;
- JIT exclusion because Axiom native compiler;
- GPU kernel profiling;
- GPU memory transfer;
- command queue stalls;
- frame-time profiling;
- audio realtime profiling;
- media pipeline profiling;
- compiler self-profiling;
- profile-guided optimization data;
- PGO integration;
- hot/cold function identification;
- source→HIR→MIR→machine correlation;
- disassembly correlation;
- optimization report correlation;
- profile diff;
- regression detection;
- deterministic benchmark integration;
- security/privacy;
- profile data serialization;
- symbol/debug information;
- release binaries with lightweight profiling;
- no mandatory profiler runtime;
- no hidden background profiler;
- AI queries such as:
  - `why is this function hot?`
  - `where is time spent?`
  - `which call path dominates?`
  - `which optimization was missed?`
  - `is the bottleneck CPU, memory, lock, IO or GPU?`

Đặc biệt 476 sẽ khóa một nguyên tắc quan trọng cho mục tiêu **Axiom ≥ C/C++ performance**:

```text
Profile
   ↓
Evidence
   ↓
Optimization hypothesis
   ↓
Compiler/Source change
   ↓
Benchmark
   ↓
Profile again
```

Profiler **không được tự động biến một measurement thành một “performance score” tổng hợp**; dữ liệu thô, methodology và target phải luôn được giữ lại để AI và developer có thể tự phân tích.