# BOOTSTRAP-338 — AXIOM PROFILING, TELEMETRY & PERFORMANCE ANALYSIS ENGINE

Sau 337, Axiom đã có source-level debugging và symbolication đủ sâu. Bước tiếp theo là xây dựng **profiling architecture thống nhất**, để compiler không chỉ biết chương trình *đúng*, mà còn biết chương trình *chậm ở đâu và vì sao*.

Mục tiêu:

> **Profile data phải quay ngược được về semantic source, MIR, machine code và optimization decision; đồng thời có thể tái sử dụng để PGO mà không biến profiling thành một phần của semantics.**

---

## 1. Ba loại profiling

Axiom phân biệt rõ:

```text
Instrumentation Profiling
Sampling Profiling
Hardware Performance Profiling
```

### Instrumentation

Compiler chèn measurement.

Ưu điểm:

- chính xác
- function/block coverage tốt

Nhược điểm:

- overhead cao

### Sampling

Lấy mẫu PC/stack định kỳ.

Ưu điểm:

- overhead thấp
- phù hợp production

### Hardware

Dùng CPU PMU/GPU performance counters.

Ví dụ:

- cycles
- instructions
- branch misses
- cache misses
- TLB misses
- stalls
- vector utilization

---

# 2. Profile không phải semantics

Ví dụ:

```text
foo() = 40%
bar() = 30%
baz() = 30%
```

thay đổi profile không được thay đổi:

```text
program meaning
```

Nó chỉ thay đổi optimization decisions.

---

# 3. Profile artifact

Tách:

```text
program.axbin
program.axprof
```

Profile artifact có:

```text
ProfileFingerprint
BinaryBuildId
Target
CPUFeatures
SamplingMode
SchemaVersion
```

---

# 4. Profile identity

Profile chỉ hợp lệ nếu xác định được:

```text
BinaryBuildId
Target
CompilerProfileSchema
InstrumentationLayout
```

Không được lấy profile của binary A áp dụng mù quáng cho binary B.

---

# 5. Function identity

Function được nhận dạng bằng semantic identity:

```text
PackageId
ModuleId
FunctionId
GenericInstanceId
```

không chỉ bằng tên:

```text
foo
```

---

# 6. Machine address mapping

Sampling:

```text
PC = 0x123456
```

phải map:

```text
PC
 ↓
BinaryBuildId
 ↓
MachineFunction
 ↓
InlineChain
 ↓
MIR
 ↓
HIR
 ↓
Source
```

---

# 7. Inline-aware profiling

Ví dụ:

```text
foo()
 └── inline bar()
      └── inline baz()
```

Sampling phải có thể phân biệt:

```text
foo → bar → baz
```

thay vì dồn toàn bộ sample vào `foo`.

---

# 8. Call graph profile

Profile graph:

```text
A
├── B 70%
└── C 30%
```

Compiler có thể dùng để:

- inline
- function ordering
- devirtualization
- specialization
- cold splitting

---

# 9. Basic-block profiling

Instrumentation có thể đo:

```text
BlockId
ExecutionCount
```

Ví dụ:

```text
entry = 1,000,000
if.true = 900,000
if.false = 100,000
```

---

# 10. Edge profiling

Không chỉ block.

```text
BasicBlock A
   ├── B = 90%
   └── C = 10%
```

Compiler lưu:

```text
ControlFlowEdgeId
ExecutionCount
```

---

# 11. Branch probability

Profile có thể sinh:

```text
BranchProbability {
    true_probability
    false_probability
}
```

Optimizer dùng để:

- layout
- branch inversion
- code duplication
- if-conversion
- loop optimization

---

# 12. Loop profiling

Compiler thu:

```text
iteration_count
trip_count_distribution
exit_probability
hotness
```

Ví dụ:

```text
loop:
  average = 1024
  p50 = 512
  p99 = 4096
```

Thông tin này hữu ích hơn một con số trung bình đơn thuần.

---

# 13. Value profiling

Có thể profile giá trị runtime:

```text
x:
  0 → 70%
  1 → 20%
  other → 10%
```

Ứng dụng:

- switch optimization
- devirtualization
- specialization
- branch prediction

Nhưng phải giới hạn overhead/privacy.

---

# 14. Indirect-call profiling

Ví dụ:

```text
call f(x)
```

runtime:

```text
foo = 90%
bar = 9%
baz = 1%
```

Compiler có thể tạo:

```text
if target == foo
    direct_call foo
else
    indirect_call
```

nếu semantics/ABI cho phép.

---

# 15. Trait dispatch profiling

Đặc biệt hữu ích với:

```text
dyn Trait
```

Profile:

```text
Renderer.draw:
    VulkanRenderer 96%
    SoftwareRenderer 4%
```

Optimizer có thể dùng speculative devirtualization.

---

# 16. Async profiling

Async profiler phải phân biệt:

```text
CPU execution
Waiting
Suspended
Ready queue
Executor overhead
```

Không được coi:

```text
await 5 seconds
```

là CPU function chạy 5 giây.

---

# 17. Async timeline

Ví dụ:

```text
Task A
CPU ────┐
        │ await
        └────────────── resume ── CPU

Task B
     CPU ───────── CPU
```

Profiler hiển thị logical task timeline.

---

# 18. Await latency

Có thể đo:

```text
poll_duration
time_to_ready
queue_wait
wake_to_poll
```

Giúp phát hiện:

- executor bottleneck
- excessive wakeups
- inefficient async API

---

# 19. Thread profiling

Mỗi thread:

```text
ThreadId
CPUTime
WaitTime
RunnableTime
BlockedTime
```

Có thể phân tích:

```text
CPU utilization
lock contention
scheduler overhead
```

---

# 20. Lock contention

Axiom sync library cung cấp instrumentation hooks.

Ví dụ:

```text
Mutex #17
acquire count = 1.2M
contention = 38%
avg wait = 4.2 us
```

Profiler không thay đổi semantics.

---

# 21. Channel profiling

Theo dõi:

```text
send_count
receive_count
queue_depth
blocked_sender
blocked_receiver
```

Giúp phát hiện channel bottleneck.

---

# 22. Allocation profiling

Compiler/runtime instrumentation có thể ghi:

```text
allocation_count
bytes_allocated
bytes_freed
peak_live_bytes
allocation_site
```

Quan trọng:

> Allocation profiling không có nghĩa Axiom bắt buộc có GC/runtime.

Runtime-free program có thể không có allocator profiler nếu không dùng allocator instrumentation.

---

# 23. Allocation lifetime

Có thể thống kê:

```text
allocation lifetime
```

Ví dụ:

```text
< 1 us      70%
1–10 us     20%
> 1 ms      10%
```

Dùng để phát hiện:

- allocator overhead
- fragmentation
- arena opportunities

---

# 24. Storage-domain profiling

Axiom có storage model:

```text
STACK
REGISTER
INLINE
DYNAMIC
STATIC
TLS
DEVICE
EXTERNAL
```

Profiler có thể cho biết:

```text
dynamic allocations
stack usage
device transfers
```

---

# 25. Stack usage

Compiler có thể tính static stack frame size.

Runtime profiler bổ sung:

```text
peak_stack_usage
```

Đặc biệt quan trọng cho:

- embedded
- kernel
- fiber
- WASM

---

# 26. Cache profiling

Hardware counters có thể map:

```text
L1D miss
L2 miss
LLC miss
ITLB miss
DTLB miss
```

về function/source.

---

# 27. Memory bandwidth

Có thể profile:

```text
bytes read
bytes written
bandwidth
```

và xác định:

```text
compute-bound
memory-bound
```

---

# 28. Vectorization analysis

Profiler kết hợp compiler metadata:

```text
loop
  vectorized = yes
  width = 8
  utilization = 73%
```

Nếu không vectorize:

```text
reason = dependency
```

hoặc:

```text
reason = insufficient_trip_count
```

---

# 29. GPU profiling

GPU profiler phải có:

```text
KernelId
LaunchId
Device
Grid
Block
RegisterUsage
SharedMemory
Occupancy
ExecutionTime
MemoryTransfer
```

---

# 30. GPU kernel timeline

```text
Host
 ├── launch A
 ├── launch B
 └── wait

GPU
 ├──── A ────┐
              ├── B ───
```

Profiler phải ghép host/device timeline.

---

# 31. GPU memory transfers

Phân biệt:

```text
Host → Device
Device → Host
Device → Device
Unified Memory
```

Không gộp tất cả thành “GPU time”.

---

# 32. GPU occupancy

Backend cung cấp target-specific metrics:

```text
occupancy
register pressure
shared memory usage
warp efficiency
```

Không biến chúng thành Core semantics.

---

# 33. FFI profiling

Foreign call:

```text
Axiom → C → OS
```

profiler phải giữ boundary.

Ví dụ:

```text
foo()
  31%
  └── libc.read()
       24%
```

---

# 34. System-call profiling

Platform profiler có thể ghi:

```text
syscall
latency
count
```

nhưng chỉ khi target capability cho phép.

---

# 35. IO profiling

Filesystem/network:

```text
read
write
connect
send
receive
```

phân biệt:

```text
CPU time
IO wait
kernel time
```

---

# 36. Timeline model

Axiom profiler có unified event model:

```text
ProfileEvent {
    timestamp
    duration
    domain
    entity
    thread/task/device
    source_location
}
```

Domain:

```text
CPU
Thread
Async
GPU
IO
Lock
Allocation
FFI
```

---

# 37. Sampling frequency

Không hard-code.

Ví dụ:

```text
100 Hz
1 kHz
10 kHz
```

Target/backend quyết định giới hạn.

---

# 38. Adaptive sampling

Profiler có thể tăng sampling khi:

```text
hot region
```

và giảm khi:

```text
cold region
```

để giảm overhead.

---

# 39. Sampling overhead

Profiler phải báo:

```text
estimated overhead
```

Ví dụ:

```text
sampling = 1.8%
instrumentation = 7.2%
```

Không được che giấu overhead.

---

# 40. Instrumentation modes

```text
Function
BasicBlock
Edge
Memory
Allocation
Lock
Async
GPU
```

User bật theo nhu cầu.

---

# 41. Low-overhead production profiling

Production profile nên ưu tiên:

```text
sampling
hardware counters
low-cost tracepoints
```

không yêu cầu full instrumentation.

---

# 42. Profile aggregation

Raw events có thể cực lớn.

Pipeline:

```text
Raw Events
 ↓
Local Aggregation
 ↓
Compressed Profile
 ↓
Profile Artifact
```

---

# 43. Profile compression

Có thể dùng:

- delta timestamps
- symbol IDs
- varints
- dictionary encoding
- run-length encoding

Không ảnh hưởng semantics.

---

# 44. Profile privacy

Profile có thể chứa:

- source paths
- function names
- values
- runtime behavior

Do đó policy:

```text
Public
Internal
Private
Sensitive
```

---

# 45. Value profiling privacy

Không mặc định thu toàn bộ runtime values.

Default:

```text
off
```

Chỉ bật explicit.

---

# 46. Profile merge

Hai profile:

```text
run A
run B
```

có thể merge nếu:

```text
same binary identity
compatible schema
compatible target/profile model
```

Ví dụ:

```text
P = P1 + P2
```

---

# 47. Profile weighting

Production profile có thể:

```text
90% traffic desktop
10% mobile
```

Profile merge hỗ trợ weight.

---

# 48. PGO artifact

Profiler xuất:

```text
program.axpgo
```

Compiler đọc:

```text
ProfileDB
```

và biến thành:

```text
OptimizationFacts
```

---

# 49. Profile → optimization boundary

Rất quan trọng:

```text
ProfileData
   ↓
ValidatedProfile
   ↓
OptimizationFacts
```

Optimizer không đọc raw profiler event trực tiếp.

---

# 50. Stale profile

Nếu source/binary thay đổi:

```text
ProfileBuildId != CurrentBuildId
```

không được coi profile là chính xác tuyệt đối.

Compiler có thể:

```text
reject
```

hoặc:

```text
degrade to heuristic
```

theo policy.

---

# 51. Profile remapping

Một số thay đổi nhỏ có thể remap:

```text
source changes
```

dựa trên semantic function identity.

Ví dụ:

```text
same FunctionId
same control-flow region fingerprint
```

→ profile có thể tái sử dụng một phần.

---

# 52. Profile confidence

Mỗi optimization fact có:

```text
confidence
```

ví dụ:

```text
foo hotness = 0.98 confidence
```

Compiler dùng confidence để tránh overfitting.

---

# 53. Optimization feedback

Compiler có thể ghi:

```text
inline foo into bar
reason:
  hot call
  size cost = 12
  speed benefit = estimated 8%
```

---

# 54. Optimization report

CLI:

```text
axiom optimize explain
```

Ví dụ:

```text
foo:
  inline: yes
  reason: hot callsite
  profile count: 4,182,221
  estimated code growth: 24 bytes
```

---

# 55. Missed optimization

Compiler phải giải thích:

```text
why not vectorized?
why not inline?
why not devirtualize?
why not eliminate allocation?
```

Ví dụ:

```text
Loop L42 not vectorized:
  dependency between load/store
  proof = UNKNOWN
```

---

# 56. Profile-guided allocation optimization

Profile có thể chỉ ra:

```text
Box<Foo>
allocation_count = 20M
escape = never
```

Optimizer có thể:

```text
stack/register promote
```

nếu semantic proof cho phép.

---

# 57. Profile-guided async optimization

Ví dụ:

```text
Future F
poll count = 4.2M
average state count = 2
```

Compiler có thể tối ưu:

- ready path
- state layout
- await fusion
- polling overhead

---

# 58. Profile-guided scheduler optimization

Runtime executor có thể học:

```text
task latency
queue depth
worker affinity
```

Nhưng những adaptive decisions phải nằm ở runtime policy, không thay đổi Axiom semantics.

---

# 59. Deterministic profiling mode

Testing cần:

```text
deterministic profile
```

Ví dụ deterministic executor + deterministic sampling simulation.

Dùng để regression tests.

---

# 60. Performance regression detection

CI có thể so sánh:

```text
baseline.axprof
current.axprof
```

và phát hiện:

```text
+18% CPU
+35% allocation
-20% throughput
```

Đây là tooling, không phải compiler correctness.

---

# 61. Profile schema

```text id="f2f3t4"
ProfileSchema {
    version
    event_types
    entity_identity
    target_model
    counter_model
}
```

Schema version độc lập với language version.

---

# 62. Hardware counter abstraction

Compiler/Profiler không hard-code Intel.

Interface:

```text id="t0xy27"
HardwareCounterProvider {
    enumerate()
    configure()
    start()
    stop()
    read()
}
```

Backend:

```text
x86 PMU
ARM PMU
Apple performance counters
GPU counters
```

---

# 63. Profiler DB

CompilerDB additions:

```text id="e6p6cw"
ProfileDB
ProfileSchemaDB
ProfileMappingDB
ProfileValidationDB
ProfileMergeDB
OptimizationFeedbackDB
PerformanceRegressionDB
HardwareCounterDB
```

---

# 64. APIs

```text id="2h5wqk"
start_profile()
stop_profile()

collect_samples()
collect_instrumentation()

map_profile_to_source()
map_profile_to_mir()

validate_profile()
merge_profiles()

generate_pgo_profile()
apply_pgo_profile()

analyze_hotspots()
analyze_cache()
analyze_allocations()
analyze_locks()
analyze_async()
analyze_gpu()

explain_optimization()
explain_missed_optimization()

compare_profiles()
detect_regression()
```

---

# 65. CLI

```text id="0o4v4v"
axiom profile run
axiom profile report
axiom profile hotspots
axiom profile timeline
axiom profile memory
axiom profile locks
axiom profile async
axiom profile gpu
axiom profile merge
axiom profile validate

axiom pgo generate
axiom pgo apply
axiom pgo explain

axiom perf diff
axiom perf regression
```

---

# 66. Profile report

Một report nên có:

```text id="2ctq6x"
CPU:
  82% foo
  11% bar
   4% runtime

Memory:
  2.1 GB allocated
  peak 310 MB

Locks:
  Mutex #4 = 28% contention

Async:
  average poll = 1.8 us

GPU:
  kernel A = 73%
```

---

# 67. Source-level hotspot

Ví dụ:

```text id="q1x1b7"
foo.ax:182
```

Compiler hiển thị:

```text
CPU samples: 21.4%
L1 miss: 8.2%
allocation: 0
vectorized: no
```

---

# 68. Optimization feedback loop

Toàn bộ architecture:

```text
Program
 ↓
Compile
 ↓
Run
 ↓
Profile
 ↓
Profile Validation
 ↓
Optimization Facts
 ↓
PGO
 ↓
Compile
 ↓
Measure Again
```

---

# 69. Không được tạo vòng phụ thuộc sai

Profile không được trở thành:

```text
source semantic dependency
```

Tức:

```text
source → semantics
profile → optimization
```

không phải:

```text
source → semantics → profile → semantics
```

---

# 70. Profile-guided reproducibility

PGO build reproducible nếu:

```text
source
compiler
target
profile artifact
optimization policy
```

giống nhau.

Profile artifact phải được fingerprint.

---

# 71. Profile artifact và `.axif`

`.axif` có thể chứa:

```text
OPTIMIZATION_SUMMARY
```

nhưng raw production profile không nên nhét mặc định vào `.axif`.

Có thể tham chiếu:

```text
ProfileFingerprint
```

---

# 72. Security

Hardware counters/profile data có thể gây:

- information leakage
- source path leakage
- runtime behavior leakage

Security policy phải có:

```text
allow_profile
allow_values
allow_source_paths
allow_hardware_counters
```

---

# 73. Implementation tree

```text id="g1k8p3"
compiler/
└── profiler/
    ├── model/
    ├── sampling/
    ├── instrumentation/
    ├── hardware/
    ├── cpu/
    ├── gpu/
    ├── async/
    ├── memory/
    ├── allocation/
    ├── synchronization/
    ├── ffi/
    ├── mapping/
    ├── aggregation/
    ├── compression/
    ├── validation/
    ├── merge/
    ├── pgo/
    ├── feedback/
    ├── regression/
    └── report/
```

---

# 74. Invariants

```text
APROF-01
Profiling must never alter language semantics.

APROF-02
Profile artifacts must identify the binary and target they describe.

APROF-03
Raw profile data must pass validation before influencing optimization.

APROF-04
Stale profiles must never be treated as exact current execution facts.

APROF-05
Profile data may influence optimization but cannot establish semantic truth.

APROF-06
Profile mapping must preserve source and machine provenance.

APROF-07
Inline call stacks must be represented correctly.

APROF-08
Async waiting time must not be misclassified as CPU execution time.

APROF-09
GPU execution and host execution must remain distinguishable.

APROF-10
Allocation profiling must remain optional.

APROF-11
Runtime-free programs must not require profiling runtime support.

APROF-12
Hardware counter availability must be target-specific.

APROF-13
Unknown hardware metrics must not invalidate semantic compilation.

APROF-14
Profile merge requires compatible identities and schemas.

APROF-15
Profile weighting must be explicit.

APROF-16
Value profiling must be opt-in where privacy requires it.

APROF-17
Optimization feedback must identify the reason for each optimization decision.

APROF-18
Missed optimization reports must distinguish unknown proof from known impossibility.

APROF-19
PGO must never bypass verifier requirements.

APROF-20
Profile-guided transformations must remain legal under ordinary compiler proof rules.

APROF-21
Profile artifacts must be independently fingerprintable.

APROF-22
Profiling overhead must be measurable.

APROF-23
Performance reports must distinguish CPU, waiting, synchronization, IO and GPU time.

APROF-24
Profile data must not become an implicit source-language dependency.

APROF-25
A clean build without profile data must remain semantically equivalent to a PGO build.
```

---

# 75. Definition of Done

BOOTSTRAP-338 hoàn thành khi Axiom có:

- Sampling profiler.
- Instrumentation profiler.
- Hardware-counter abstraction.
- CPU profiling.
- GPU profiling.
- Async profiling.
- Thread profiling.
- Lock profiling.
- Channel profiling.
- Allocation profiling.
- Memory-bandwidth profiling.
- Cache/TLB profiling.
- Call graph profiling.
- Basic-block profiling.
- Edge profiling.
- Loop profiling.
- Value profiling.
- Indirect-call profiling.
- Trait-dispatch profiling.
- Unified timeline.
- Host/device timeline.
- Profile artifact format.
- Profile fingerprinting.
- Profile validation.
- Profile merge.
- Profile weighting.
- Profile remapping.
- Profile confidence.
- PGO generation.
- PGO application.
- Optimization feedback.
- Missed-optimization explanations.
- Performance regression detection.
- Source-level hotspot mapping.
- MIR-level hotspot mapping.
- Machine-level hotspot mapping.
- Debugger integration.
- `.axif` integration.
- Incremental build integration.
- Whole-program optimizer integration.
- Binary-layout integration.
- Security/privacy policy.
- AI-readable performance reports.

## Nguyên tắc khóa

> **Axiom profiler không chỉ trả lời “hàm nào chậm”; nó phải trả lời được “source → MIR → machine → hardware behavior → optimization decision” một cách liên tục.**

Và vòng lặp cuối cùng của compiler sẽ trở thành:

```text
         ┌──────────────────────┐
         │                      ▼
Source → Compile → Native → Run → Profile
  ▲                               │
  │                               ▼
  └──── Semantic/Optimization ← PGO
```

Trong đó **Profile chỉ ảnh hưởng cách compiler tối ưu, không bao giờ được phép thay đổi ý nghĩa của chương trình**.