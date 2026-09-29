# BOOTSTRAP-761 — AXOBSERVABILITY

**Title:** Native Metrics, Tracing, Telemetry Pipeline, Runtime Monitoring, Health Aggregation & Observability Runtime 5.0  
**Namespace:** `AXOBSERVABILITY`  
**Phase:** Axiom Civilization Runtime / Native Observability & Telemetry Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXOBSERVABILITY` là **continuous observation plane** của Axiom.

Nó cung cấp một abstraction thống nhất cho:

- metrics;
- traces;
- runtime telemetry;
- health;
- counters;
- gauges;
- histograms;
- event streams;
- aggregation;
- sampling;
- exporters;
- dashboards;
- alerts;
- topology/dependency observation.

Phân biệt rõ:

```text
AXAUDIT
    = accountability / security evidence

AXDIAGNOSTICS
    = failure / crash / debugging / profiling

AXOBSERVABILITY
    = continuous operational observation
```

---

# 2. Kiến trúc

```text
AXPROCESS ───────┐
AXTASK ──────────┤
AXASYNC ─────────┤
AXNETWORK ───────┤
AXSTORAGE ───────┤
AXDATABASE ──────┤
AXCOMPUTE ───────┤
AXMEMORY ────────┤
AXGRAPHICS ──────┤
AXAUDIO ─────────┤
AXAPPLICATION ───┤
                  ▼
        ┌─────────────────────┐
        │ AXOBSERVABILITY     │
        │                     │
        │ metrics             │
        │ traces              │
        │ telemetry           │
        │ health              │
        │ aggregation         │
        │ sampling            │
        │ export              │
        └──────────┬──────────┘
                   │
          ┌────────┼─────────┐
          ▼        ▼         ▼
       local     GUI      remote
       console             sink
```

---

# 3. Strong boundary

## AXOBSERVABILITY sở hữu

- metric model;
- metric instruments;
- metric aggregation;
- tracing model;
- span lifecycle;
- trace context;
- telemetry pipeline;
- observation streams;
- health aggregation;
- topology metadata;
- sampling;
- batching;
- export;
- retention for transient telemetry;
- observability configuration;
- observability subscriptions;
- derived metrics;
- alert conditions;
- observability simulation.

## Không sở hữu

- security audit;
- crash dump;
- process lifecycle;
- scheduler;
- storage;
- network protocol;
- security authorization;
- application business logic.

---

# 4. Fundamental principle

Không phải mọi runtime operation đều phải:

```text
allocate
→ serialize
→ copy
→ lock
→ network
```

cho mỗi observation.

Baseline:

```text
producer
   ↓
cheap local observation
   ↓
per-core buffer/counter
   ↓
batch
   ↓
aggregate
   ↓
optional encode
   ↓
optional export
```

---

# 5. Observation model

```text
observation {
    observation_id
    type
    timestamp
    source
    resource
    dimensions
    value
    trace_context
}
```

---

# 6. Metric types

Baseline:

```text
COUNTER
GAUGE
HISTOGRAM
SUMMARY
UP_DOWN_COUNTER
OBSERVABLE_GAUGE
OBSERVABLE_COUNTER
```

---

# 7. Counter

Counter chỉ tăng:

```text
counter += delta
```

Không reset tùy ý trong một metric identity.

Process restart tạo observation epoch mới.

---

# 8. Gauge

Gauge biểu diễn state hiện tại:

```text
memory_usage
queue_depth
temperature
active_connections
```

Có thể tăng hoặc giảm.

---

# 9. Histogram

Histogram dùng cho:

```text
latency
size
duration
queue depth
allocation size
```

Canonical model:

```text
histogram {
    count
    sum
    min
    max
    buckets
}
```

---

# 10. Bucket configuration

Bucket boundaries phải explicit.

Không để exporter tự thay đổi semantic meaning của metric.

---

# 11. Summary

Summary có thể lưu:

```text
quantile approximation
count
sum
```

nhưng implementation-specific.

Histogram là baseline cho aggregation ổn định.

---

# 12. Metric identity

Metric không chỉ là tên.

```text
metric_identity {
    name
    namespace
    unit
    type
    schema_version
}
```

---

# 13. Dimensions

Metric có dimensions:

```text
dimensions {
    key
    value
}
```

Ví dụ:

```text
service = api
operation = read
device = gpu0
```

---

# 14. Cardinality control

Cardinality phải có giới hạn.

Không cho phép:

```text
user_id
request_id
random_uuid
```

trở thành metric dimension mặc định.

Đây là một nguyên nhân phổ biến làm telemetry phình memory.

---

# 15. Cardinality budget

Mỗi metric có:

```text
cardinality_limit
```

Khi vượt limit:

```text
DROP_NEW_SERIES
AGGREGATE_OTHER
REJECT
```

theo profile.

---

# 16. Metric registry

```text
metric_registry {
    registry_id
    metrics[]
    cardinality_budget
}
```

Registry có thể process-local hoặc system-level.

---

# 17. Static metric registration

Compiler/runtime có thể tạo metric descriptors tại compile time.

Không cần reflection.

---

# 18. Dynamic metrics

Dynamic registration được hỗ trợ nhưng có overhead cao hơn.

Production hot path nên dùng static descriptors khi có thể.

---

# 19. Metric update

Fast path:

```text
metric.increment(1)
```

nên có khả năng compile thành:

```text
atomic_add
```

hoặc local counter update.

---

# 20. Per-core aggregation

```text
CPU 0 → local counter
CPU 1 → local counter
CPU 2 → local counter
...
             ↓
        aggregation
```

Giảm contention global atomic.

---

# 21. Thread-local aggregation

Thread có thể có local metric state.

Flush định kỳ vào process/core aggregate.

---

# 22. NUMA

Large systems:

```text
NUMA node
 └── local metrics
       └── local aggregator
```

Global view được hợp nhất ở collection layer.

---

# 23. Trace model

```text
trace {
    trace_id
    root_span
    spans[]
}
```

---

# 24. Span

```text
span {
    span_id
    trace_id
    parent_span_id
    operation
    start_time
    end_time
    status
    attributes
    events
}
```

---

# 25. Span lifecycle

```text
CREATED
   ↓
ACTIVE
   ↓
ENDED
```

Một span không được end hai lần.

---

# 26. Span status

```text
OK
ERROR
UNSET
CANCELLED
TIMEOUT
```

Status không phải security decision.

---

# 27. Trace context

```text
trace_context {
    trace_id
    span_id
    trace_flags
    baggage_ref
}
```

Trace context có thể truyền qua:

```text
AXTASK
AXIPC
AXNETWORK
AXASYNC
```

---

# 28. Trace propagation

Propagation phải explicit.

Không tự động serialize toàn bộ thread state.

---

# 29. Baggage

Optional metadata:

```text
baggage {
    key
    value
}
```

Có giới hạn kích thước.

Sensitive data phải được chặn/redact.

---

# 30. Trace attributes

Attributes có typed values:

```text
BOOL
INTEGER
FLOAT
STRING
BYTES
ARRAY
```

Không dùng arbitrary object serialization.

---

# 31. Trace event

Span có thể chứa:

```text
span_event {
    timestamp
    name
    attributes
}
```

Ví dụ:

```text
cache_miss
retry
queue_full
```

---

# 32. Span links

Một span có thể liên kết với nhiều trace/span:

```text
span_link {
    trace_id
    span_id
    attributes
}
```

Useful cho:

- async fan-in;
- batch processing;
- message consumers.

---

# 33. Parent/child

Parent-child biểu diễn execution relationship.

Không suy luận ownership/security authority từ trace hierarchy.

---

# 34. Trace sampling

Baseline:

```text
ALWAYS
NEVER
PROBABILISTIC
RATE_LIMITED
ERROR_PRIORITY
TAIL
ADAPTIVE
```

---

# 35. Head sampling

Quyết định ở span đầu.

Nhanh, ít overhead.

---

# 36. Tail sampling

Quyết định sau khi trace đã có dữ liệu.

Có thể giữ:

```text
error traces
slow traces
rare traces
```

nhưng cần bounded buffering.

---

# 37. Adaptive sampling

Sampling rate có thể điều chỉnh dựa trên:

```text
traffic
error rate
latency
buffer pressure
```

Nhưng phải có bounds.

---

# 38. Sampling ≠ audit

Không áp dụng sampling policy của observability lên mandatory AXAUDIT events.

---

# 39. Telemetry event

Telemetry event là structured operational event:

```text
telemetry_event {
    timestamp
    source
    type
    severity
    dimensions
    payload
}
```

Không có security accountability semantics mặc định.

---

# 40. Telemetry channels

```text
RUNTIME
PERFORMANCE
RESOURCE
NETWORK
STORAGE
APPLICATION
DEVICE
USER_INTERFACE
```

---

# 41. Health model

```text
health_state {
    component
    state
    reason
    since
    dependencies
}
```

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

# 42. Health ≠ score

Axiom không dùng:

```text
health = 87/100
```

làm canonical health semantics.

State + evidence + metrics rõ ràng hơn.

---

# 43. Health check

```text
health_check {
    check_id
    target
    interval
    timeout
    dependencies
}
```

---

# 44. Liveness

Liveness trả lời:

```text
"Component còn phản hồi không?"
```

---

# 45. Readiness

Readiness trả lời:

```text
"Component có thể nhận workload không?"
```

Hai trạng thái được lưu riêng.

---

# 46. Dependency graph

```text
Application
    ↓
API
    ↓
Database
    ↓
Storage
```

AXOBSERVABILITY có thể biểu diễn graph.

---

# 47. Topology

```text
observation_node {
    node_id
    parent
    component
    process
    host
    resource
}
```

Topology là observation metadata, không phải authoritative resource registry.

---

# 48. Derived metrics

Có thể tạo:

```text
request_rate
error_rate
average_latency
queue_utilization
```

từ raw observations.

Derived metric phải ghi rõ source metrics và calculation version.

---

# 49. Derived metric reproducibility

```text
derived_metric {
    formula_id
    input_metrics
    version
}
```

Không để dashboard tự định nghĩa semantics khác nhau cho cùng metric.

---

# 50. Alert

AXOBSERVABILITY có condition engine đơn giản:

```text
alert_rule {
    rule_id
    expression
    duration
    cooldown
    severity
}
```

---

# 51. Alert expression

Có thể hỗ trợ:

```text
metric > threshold
metric < threshold
rate(metric)
ratio(metric_a, metric_b)
absence(metric)
```

Không cần biến thành full programming language.

---

# 52. Alert state

```text
INACTIVE
PENDING
FIRING
RESOLVED
UNKNOWN
```

---

# 53. Alert action boundary

Alert có thể phát:

```text
alert_event
```

nhưng không mặc định:

```text
kill_process()
grant_capability()
disable_security()
```

Administrative action phải đi qua appropriate subsystem + AXSECURITY.

---

# 54. Notification

Notification adapters:

```text
CONSOLE
GUI
LOCAL_IPC
REMOTE_EXPORT
```

External notification protocols thuộc appropriate transport subsystem.

---

# 55. Exporter

```text
observability_exporter {
    exporter_id
    format
    destination
    batch_size
    interval
    retry_policy
}
```

---

# 56. Export formats

Baseline:

```text
AXOBS_NATIVE
JSON
CBOR
BINARY
```

Native binary là canonical internal representation.

---

# 57. Export transport

AXOBSERVABILITY không implement network protocols.

Có thể dùng:

```text
AXSTREAM
AXNETWORK
AXIPC
```

---

# 58. Remote exporter

Remote delivery semantics:

```text
BEST_EFFORT
AT_LEAST_ONCE
```

Exactly-once không phải baseline.

---

# 59. Export batching

```text
observations
    ↓
batch
    ↓
encode
    ↓
compress
    ↓
send
```

Giảm syscall và network overhead.

---

# 60. Compression

Có thể dùng AXCODEC.

Compression optional.

Không compress các tiny local metrics nếu chi phí lớn hơn lợi ích.

---

# 61. Backpressure

Exporter có:

```text
BLOCK
BUFFER
DROP
SAMPLE
FAIL
```

Operational telemetry mặc định có thể drop/sample.

---

# 62. Critical observations

Một số operational observations có thể được đánh dấu:

```text
NON_DROPPABLE
```

nếu application/system profile yêu cầu.

Nhưng security accountability vẫn thuộc AXAUDIT.

---

# 63. Memory bounds

Mỗi collector/exporter có:

```text
max_buffer
max_batch
max_event_size
max_series
max_spans
```

---

# 64. Overflow

Khi buffer đầy:

```text
drop_count++
```

và chính `drop_count` trở thành metric để quan sát telemetry loss.

---

# 65. Telemetry about telemetry

AXOBSERVABILITY phải tự expose:

```text
events_dropped
events_exported
export_failures
buffer_usage
series_count
span_count
sampling_rate
```

Nếu không, operator không biết telemetry có bị mất.

---

# 66. Runtime resource metrics

Baseline integration:

```text
AXPROCESS
    cpu_time
    thread_count

AXMEMORY
    virtual_memory
    resident_memory
    allocations

AXTASK
    task_count
    runnable_tasks
    queue_depth

AXASYNC
    inflight_io
    completion_latency

AXNETWORK
    bytes_in/out
    connections

AXSTORAGE
    read/write latency
```

---

# 67. Compute metrics

AXCOMPUTE có thể cung cấp:

```text
cpu_utilization
gpu_utilization
queue_depth
scheduler_latency
task_wait
```

AXOBSERVABILITY chỉ collect/aggregate.

---

# 68. UI integration

AXDISPLAY/AXWINDOW/AXAPPLICATION có thể dùng AXOBSERVABILITY để hiển thị:

```text
FPS
frame time
input latency
GPU usage
memory
```

---

# 69. GUI dashboard

Axiom standard dashboard abstraction:

```text
dashboard {
    dashboard_id
    panels[]
    refresh_interval
}
```

Dashboard definition không phải GUI toolkit.

---

# 70. Panel

```text
panel {
    panel_id
    type
    metric_refs
    query
    display_config
}
```

Types:

```text
VALUE
TIMESERIES
HISTOGRAM
TABLE
TRACE
HEALTH
TOPOLOGY
```

---

# 71. Dashboard performance

Dashboard query không được đọc raw telemetry toàn bộ nếu pre-aggregated data có thể dùng.

---

# 72. Time-series aggregation

Aggregation windows:

```text
1s
10s
1m
5m
1h
```

Có thể cấu hình.

---

# 73. Retention

Observability retention khác audit retention.

Telemetry có thể:

```text
high resolution → short retention
low resolution → long retention
```

---

# 74. Downsampling

Ví dụ:

```text
1-second data
      ↓
1-minute aggregates
      ↓
1-hour aggregates
```

Raw data có thể expire.

---

# 75. Metric reset

Process restart phải tạo:

```text
observation_epoch
```

để phân biệt:

```text
counter reset
```

với:

```text
counter decrease
```

---

# 76. Clock handling

Metrics/time-series sử dụng:

```text
wall timestamp
monotonic duration
```

Duration không được tính bằng wall clock nếu clock có thể jump.

---

# 77. Trace clock

Distributed trace cần clock metadata.

Không giả định các machines có synchronized clocks hoàn hảo.

---

# 78. Clock skew

Trace viewer có thể biểu diễn:

```text
clock_uncertainty
```

nếu available.

Không tự sửa timeline thành một “sự thật” giả tạo.

---

# 79. Observation context

```text
observation_context {
    process
    thread
    task
    trace_context
    component
    resource
}
```

Context nên là lightweight.

---

# 80. Context propagation

AXTASK có thể propagate observation context qua await.

AXIPC/AXNETWORK có thể propagate trace context qua explicit protocol fields.

---

# 81. Context lifetime

Observation context không được giữ object graph lớn sống lâu hơn operation.

Compiler/runtime có thể dùng compact IDs.

---

# 82. No hidden allocation

```text
counter.increment()
span_start()
span_end()
```

không được bắt buộc heap allocation.

---

# 83. Span storage optimization

Small span:

```text
inline fixed metadata
```

Large attributes:

```text
side buffer
```

---

# 84. String optimization

Metric names và static labels nên intern/register một lần.

Không copy string ở mỗi metric update.

---

# 85. Static labels

```text
component = "AXNETWORK"
```

có thể nằm trong immutable descriptor.

Dynamic labels chịu cardinality budget.

---

# 86. Trace IDs

Trace IDs phải:

- unique enough;
- compact;
- generation-safe;
- cheap to create.

CSPRNG không bắt buộc cho operational trace identity nếu uniqueness mechanism đủ; security token identity không được dùng trace ID làm security credential.

---

# 87. Security boundary

Observability data cũng có thể sensitive.

Ví dụ:

```text
request path
tenant
resource name
performance data
```

Read/export phải qua AXSECURITY khi profile yêu cầu.

---

# 88. Security audit integration

Các hành động:

```text
OBSERVABILITY.CONFIGURE
OBSERVABILITY.READ_SENSITIVE
OBSERVABILITY.EXPORT
OBSERVABILITY.START_PROFILING
```

có thể tạo AXAUDIT events.

---

# 89. AI integration

AI có thể:

- phân tích metric;
- phát hiện anomaly;
- tìm performance regression;
- correlate traces;
- giải thích health degradation;
- đề xuất collector configuration;
- tạo diagnostic hypotheses.

AI không được:

- tự thay đổi security;
- tự kill/restart;
- tự tăng resource quota;
- tự disable monitoring;
- tự xóa telemetry cần retention.

---

# 90. Anomaly detection

AXOBSERVABILITY có thể cung cấp primitive:

```text
anomaly {
    metric
    interval
    observed
    baseline
    method
}
```

Baseline method phải explicit.

---

# 91. No magical AI truth

Anomaly detection chỉ là:

```text
observation + model
```

Không biến thành authoritative failure fact.

---

# 92. Simulation

Simulation hỗ trợ:

```text
metric generation
trace generation
clock
sampling
buffer overflow
export failure
network delay
collector failure
```

---

# 93. Deterministic telemetry simulation

Input:

```text
scenario
seed
clock
events
```

Output phải reproducible trong cùng runtime/profile.

---

# 94. Replay

Replay chỉ tái tạo observability stream:

```text
event
→ aggregation
→ visualization
```

Không tự execute original application operation.

---

# 95. Fault injection

Test-only:

```text
inject_export_failure()
inject_buffer_overflow()
inject_clock_skew()
inject_collector_delay()
inject_trace_drop()
```

---

# 96. Native API — metrics

```text id="obsapi1"
metric_registry_create()
metric_register()
metric_get()
metric_counter_create()
metric_gauge_create()
metric_histogram_create()

metric_increment()
metric_add()
metric_set()
metric_observe()

metric_snapshot()
metric_flush()
```

---

# 97. Native API — tracing

```text id="obsapi2"
trace_create()
trace_start()
trace_end()

span_create()
span_start()
span_set_attribute()
span_add_event()
span_add_link()
span_set_status()
span_end()

trace_context_get()
trace_context_set()
trace_context_inject()
trace_context_extract()
```

---

# 98. Native API — telemetry

```text id="obsapi3"
telemetry_emit()
telemetry_stream_create()
telemetry_stream_activate()
telemetry_stream_pause()
telemetry_stream_close()

telemetry_subscribe()
telemetry_unsubscribe()
```

---

# 99. Native API — health

```text id="obsapi4"
health_register()
health_set_state()
health_get_state()
health_check_create()
health_check_run()
health_get_dependencies()
health_get_topology()
```

---

# 100. Native API — exporter

```text id="obsapi5"
exporter_create()
exporter_configure()
exporter_start()
exporter_stop()
exporter_flush()
exporter_get_stats()
```

---

# 101. Native API — dashboards

```text id="obsapi6"
dashboard_create()
dashboard_add_panel()
dashboard_remove_panel()
dashboard_query()
dashboard_refresh()
dashboard_export()
```

---

# 102. Native API — alerts

```text id="obsapi7"
alert_rule_create()
alert_rule_activate()
alert_rule_deactivate()
alert_get_state()
alert_subscribe()
```

---

# 103. Native API — diagnostics integration

```text id="obsapi8"
observability_attach_diagnostics()
observability_start_profile()
observability_capture_snapshot()
observability_correlate_trace()
```

AXDIAGNOSTICS vẫn sở hữu diagnostic artifact.

---

# 104. Native API — simulation

```text id="obsapi9"
observability_simulate()
observability_replay()
observability_inject_fault()
```

---

# 105. ABI

```text id="obsabi1"
AXOBSERVABILITY_ABI_1
```

Opaque handles:

```text
metric_handle
metric_registry_handle
trace_handle
span_handle
telemetry_stream_handle
health_handle
exporter_handle
dashboard_handle
alert_handle
```

---

# 106. Error model

```text id="obserr"
OBS_INVALID_METRIC
OBS_INVALID_DIMENSION
OBS_CARDINALITY_LIMIT
OBS_BUFFER_FULL
OBS_EXPORT_FAILURE
OBS_SCHEMA_MISMATCH
OBS_INVALID_TRACE
OBS_SPAN_ALREADY_ENDED
OBS_TRACE_CONTEXT_INVALID
OBS_HEALTH_CHECK_FAILED
OBS_QUERY_INVALID
OBS_PERMISSION_DENIED
OBS_RESOURCE_LIMIT
OBS_UNSUPPORTED_EXPORT
OBS_SIMULATION_INVALID
OBS_REPLAY_INVALID
OBS_TIMEOUT
OBS_CANCELLED
```

---

# 107. Canonical flow — metric

```text id="obsflow1"
application
    ↓
metric.increment()
    ↓
per-core counter
    ↓
periodic aggregation
    ↓
time-series sample
    ↓
optional exporter
```

Không serialize/network trên hot path.

---

# 108. Canonical flow — trace

```text id="obsflow2"
request
   ↓
span_start
   ↓
AXTASK
   ↓
AXASYNC
   ↓
AXNETWORK
   ↓
span_end
   ↓
trace buffer
   ↓
sampling
   ↓
batch export
```

---

# 109. Canonical flow — health

```text id="obsflow3"
component
    ↓
health check
    ↓
health state
    ↓
dependency aggregation
    ↓
system topology
```

---

# 110. Canonical flow — telemetry pressure

```text id="obsflow4"
producers
    ↓
buffer
    ↓
capacity exceeded
    ↓
sampling/drop policy
    ↓
drop counter
    ↓
operator visibility
```

Telemetry loss itself phải observable.

---

# 111. Canonical flow — alert

```text id="obsflow5"
metric
  ↓
aggregation
  ↓
alert expression
  ↓
PENDING
  ↓
condition persists
  ↓
FIRING
  ↓
notification
```

Không tự thực hiện privileged remediation.

---

# 112. Canonical flow — remote export

```text id="obsflow6"
local observations
       ↓
aggregation
       ↓
batch
       ↓
AXCODEC
       ↓
AXSTREAM
       ↓
AXNETWORK
       ↓
remote sink
```

---

# 113. Canonical flow — AI analysis

```text id="obsflow7"
metrics
traces
health
   ↓
AXOBSERVABILITY
   ↓
authorized read
   ↓
AI analysis
   ↓
finding / hypothesis
```

AI output không trở thành runtime authority.

---

# 114. Formal invariants

`AXOBSERVABILITY 5.0` định nghĩa tối thiểu:

```text id="obsinv"
OBS-INV-01   Metric identity phải bao gồm name và semantic type.
OBS-INV-02   Metric unit phải ổn định trong một metric identity.
OBS-INV-03   Counter không được tùy ý giảm trong cùng observation epoch.
OBS-INV-04   Process restart phải có observation epoch mới.
OBS-INV-05   Gauge có thể tăng hoặc giảm.
OBS-INV-06   Histogram bucket boundaries phải explicit.
OBS-INV-07   Metric dimensions phải có bounded cardinality.
OBS-INV-08   Runtime không được tạo unbounded metric series.
OBS-INV-09   Static metric descriptors không cần dynamic reflection.
OBS-INV-10   Normal metric update không được bắt buộc heap allocation.
OBS-INV-11   Per-core aggregation không được làm thay đổi metric semantics.
OBS-INV-12   NUMA aggregation phải giữ metric identity.
OBS-INV-13   Trace ID không được dùng như security credential.
OBS-INV-14   Span ID phải unique trong trace scope.
OBS-INV-15   Span chỉ được kết thúc một lần.
OBS-INV-16   Physical execution và trace relationship không được đánh đồng.
OBS-INV-17   Trace context propagation phải explicit.
OBS-INV-18   Trace baggage phải có bounded size.
OBS-INV-19   Sensitive attributes phải tuân thủ redaction policy.
OBS-INV-20   Sampling không được áp dụng vào mandatory AXAUDIT events.
OBS-INV-21   Telemetry stream phải có bounded memory.
OBS-INV-22   Buffer overflow phải có explicit loss semantics.
OBS-INV-23   Telemetry loss phải được observable.
OBS-INV-24   Export failure không được âm thầm biến thành successful delivery.
OBS-INV-25   Remote delivery semantics phải explicit.
OBS-INV-26   Health phải phân biệt liveness và readiness.
OBS-INV-27   Health state phải giữ source reason.
OBS-INV-28   Health aggregation không được che mất component failure.
OBS-INV-29   Derived metric phải xác định input và calculation version.
OBS-INV-30   Alert không được mặc định thực hiện privileged action.
OBS-INV-31   Observability không được thay đổi security authority.
OBS-INV-32   Observability read/export sensitive data phải qua AXSECURITY.
OBS-INV-33   Audit actions phải được chuyển tới AXAUDIT khi policy yêu cầu.
OBS-INV-34   Dashboard không được thay đổi canonical metric semantics.
OBS-INV-35   Downsampling phải xác định rõ aggregation semantics.
OBS-INV-36   Monotonic duration không được tính từ wall-clock có thể jump.
OBS-INV-37   Replay không được re-execute application operations.
OBS-INV-38   Fault injection phải bị giới hạn bởi simulation/test authority.
OBS-INV-39   AI findings phải phân biệt observation và inference.
OBS-INV-40   AI không được tự thay đổi observability, security hoặc resource authority.
```

---

# 115. Definition of Done

`AXOBSERVABILITY 5.0` được freeze khi Axiom có:

- metric registry;
- counters;
- gauges;
- histograms;
- summaries;
- observable instruments;
- metric identity;
- dimensions;
- cardinality controls;
- per-core aggregation;
- thread-local aggregation;
- NUMA aggregation;
- trace model;
- span model;
- trace context;
- baggage;
- span events;
- span links;
- head sampling;
- tail sampling;
- adaptive sampling;
- telemetry events;
- telemetry streams;
- bounded buffers;
- backpressure;
- loss accounting;
- health states;
- liveness/readiness;
- dependency graph;
- topology;
- derived metrics;
- time-series aggregation;
- downsampling;
- alert conditions;
- notification abstraction;
- exporters;
- batching;
- remote delivery;
- dashboards;
- security integration;
- AXAUDIT integration;
- AXDIAGNOSTICS integration;
- AI analysis boundary;
- deterministic simulation;
- replay;
- fault injection;
- compiler metadata;
- native ABI;
- native APIs;
- performance fast path;
- 40 formal invariants.

**AXOBSERVABILITY 5.0 → FROZEN.**

---

# BOOTSTRAP-762 — AXCONFIG

**Native Configuration, Environment, Profiles, Feature Flags, Runtime Settings & Immutable Configuration Snapshot Runtime 5.0**

Tầng tiếp theo sẽ giải quyết một vấn đề rất cơ bản nhưng thường bị thiết kế rải rác trong application:

```text
configuration
environment
profiles
defaults
overrides
feature flags
runtime settings
secrets references
versioning
validation
hot reload
rollback
```

Kiến trúc dự kiến:

```text
          AXCONFIG
             │
     ┌───────┼────────┐
     ▼       ▼        ▼
 defaults  profiles  environment
     │       │        │
     └───────┼────────┘
             ▼
      configuration
          snapshot
             │
       ┌─────┼─────┐
       ▼     ▼     ▼
    process task application
```

Điểm quan trọng của `AXCONFIG` sẽ là **configuration snapshot bất biến**, để một process/task không thấy trạng thái cấu hình “nửa cũ nửa mới” khi hot reload; đồng thời configuration không được trở thành một cách ngầm để cấp security authority hoặc chứa plaintext secret.