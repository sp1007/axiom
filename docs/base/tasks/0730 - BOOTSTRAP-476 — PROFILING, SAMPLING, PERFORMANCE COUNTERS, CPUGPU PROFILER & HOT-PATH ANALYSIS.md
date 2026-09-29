# BOOTSTRAP-476 — PROFILING, SAMPLING, PERFORMANCE COUNTERS, CPU/GPU PROFILER & HOT-PATH ANALYSIS

**Trạng thái: COMPLETED / LOCKED**

476 hoàn thiện lớp profiling phía trên 450/475. Mục tiêu là biến hiệu năng thành một vòng lặp có bằng chứng:

```text
Execution
    ↓
Profile
    ↓
Evidence
    ↓
Optimization hypothesis
    ↓
Change
    ↓
Benchmark
    ↓
Profile again
```

Profiler **không phải** benchmark và cũng không phải telemetry service.

---

## 476.1 — Profiling model

Axiom hỗ trợ ba hình thức:

```text
Sampling
Instrumentation
Hardware-counter-assisted
```

Có thể kết hợp chúng.

---

## 476.2 — Sampling profiler

Profiler định kỳ lấy snapshot execution state:

```text
timestamp
thread
task
instruction pointer
call stack
```

Không cần instrument mọi function.

---

## 476.3 — Sampling overhead

Sampling frequency phải configurable.

Ví dụ:

```text
low
medium
high
custom
```

High-frequency sampling có overhead lớn hơn.

---

## 476.4 — Statistical nature

Sampling profile là measurement thống kê.

Không được diễn giải một sample đơn lẻ như exact execution time.

---

# 476.5 — Instrumentation profiler

Compiler/runtime có thể chèn:

```text
enter
exit
event
```

để đo chính xác từng invocation.

Phù hợp với function/hot-path cụ thể nhưng overhead cao hơn.

---

## 476.6 — Selective instrumentation

Cho phép instrument:

```text
function
module
package
attribute
```

thay vì toàn chương trình.

---

## 476.7 — Function profiling attribute

Có thể hỗ trợ:

```text
@profile
```

nhưng attribute chỉ là instrumentation request, không thay đổi semantics.

---

# 476.8 — Call stack

Profiler phải reconstruct call stack từ:

- frame pointer;
- unwind metadata;
- platform stack walking;
- debugger metadata.

---

## 476.9 — Optimized binaries

Inlining, tail call, frame elimination có thể làm call stack khác source-level call graph.

Profiler phải giữ distinction giữa:

```text
logical frame
physical frame
```

giống 440.

---

## 476.10 — Inline frame

Nếu `A()` inline `B()`, profile có thể ghi:

```text
A
 └── B [inlined]
```

---

# 476.11 — CPU time

CPU time đo thời gian thread thực sự chạy trên CPU.

---

## 476.12 — Wall time

Wall time bao gồm:

```text
CPU
+ IO wait
+ lock wait
+ scheduler wait
+ sleep
```

---

## 476.13 — On-CPU / Off-CPU

Profiler phải phân biệt:

```text
ON_CPU
OFF_CPU
```

để tránh kết luận sai rằng function “chậm” khi phần lớn thời gian nằm ở IO/lock.

---

# 476.14 — Scheduler attribution

471 có thể cung cấp:

```text
ready_wait
run_time
sleep
yield
preemption
```

---

## 476.15 — Lock contention

424/471 instrumentation có thể đo:

```text
lock_wait
lock_hold
contention_count
```

---

## 476.16 — Channel wait

472 có thể expose:

```text
send_wait
receive_wait
queue_wait
```

---

## 476.17 — Actor mailbox wait

Actor profiling có thể tách:

```text
message_wait
queue_wait
handler_time
```

---

# 476.18 — Allocation profiling

423/450 có thể sample allocations:

```text
allocation size
allocation site
lifetime
allocator
thread/task
```

---

## 476.19 — Allocation count

Profile có thể ghi:

```text
count
bytes
average size
peak
```

---

## 476.20 — Allocation lifetime

Nếu allocator/runtime hỗ trợ, profile có thể theo dõi:

```text
allocation
→ live
→ free
```

để phát hiện long-lived allocations.

---

# 476.21 — Heap profiling

Heap profiler là optional.

Không yêu cầu GC metadata vì Axiom không có GC mặc định.

---

## 476.22 — Arena profiling

423 arena allocator có thể expose:

```text
arena size
used
high-water mark
reset count
```

---

## 476.23 — Stack profiling

Profiler có thể đo stack usage/high-water mark khi platform hỗ trợ.

---

# 476.24 — Hardware performance counters

Axiom cung cấp abstraction cho CPU PMU:

```text
cycles
instructions
branches
branch_misses
cache_references
cache_misses
```

Danh sách thực tế phụ thuộc target.

---

## 476.25 — Counter availability

Không được giả định mọi CPU đều cung cấp cùng counter.

API phải expose capability.

---

## 476.26 — Counter permissions

OS/hypervisor có thể hạn chế performance counters.

Failure phải là `Result`, không phải crash.

---

# 476.27 — Counter multiplexing

Nếu hardware không đủ counter slots, profiler có thể multiplex.

Kết quả phải ghi rõ multiplexing đã xảy ra.

---

## 476.28 — Counter scaling

Nếu OS scales multiplexed measurements, profile phải giữ metadata về scaling.

---

# 476.29 — CPU frequency

Cycles không tương đương nanoseconds khi CPU frequency thay đổi.

Profiler phải lưu frequency information nếu có.

---

## 476.30 — Turbo/throttling

Benchmark/profile report phải có khả năng ghi nhận:

```text
frequency
thermal throttling
power state
```

nếu platform cung cấp.

---

# 476.31 — Cache profiling

Có thể đo:

```text
L1
L2
LLC
TLB
```

nhưng exact counters target-specific.

---

## 476.32 — Branch profiling

Có thể đo:

```text
branches
branch misses
```

để hỗ trợ branch optimization.

---

# 476.33 — SIMD profiling

Compiler/profile tooling có thể correlate:

```text
scalar instructions
vector instructions
vector width
```

với source/MIR.

---

## 476.34 — Vectorization report

Optimizer có thể ghi:

```text
vectorized
not_vectorized
reason
```

và profiler cung cấp runtime evidence.

---

# 476.35 — Memory bandwidth

Platform profiler có thể đo hoặc ước lượng:

```text
read bandwidth
write bandwidth
memory stalls
```

không coi mọi architecture có cùng counter semantics.

---

# 476.36 — Hot function

Function có thể được đánh dấu hot dựa trên profile data.

Đây là **observed property**, không phải quality score.

---

## 476.37 — Hot path

Hot path có thể được xây từ:

```text
sample count
edge frequency
execution trace
```

---

## 476.38 — Cold code

Cold functions có thể được dùng cho:

- code layout;
- cold section;
- optimization decisions;
- binary-size optimization.

---

# 476.39 — Profile-guided optimization

PGO pipeline:

```text
Build instrumented/profileable
        ↓
Run representative workload
        ↓
Collect profile
        ↓
Merge/validate profile
        ↓
Optimize production build
```

---

## 476.40 — PGO profile validity

Profile phải gắn:

```text
compiler version
target
CPU architecture
feature set
module/package identity
source/build fingerprint
```

---

## 476.41 — Stale profile

Profile không tương thích phải bị reject hoặc explicit override.

Không silently áp dụng profile cũ.

---

# 476.42 — Source correlation

Profile sample phải có thể map:

```text
machine instruction
→ MIR/LIR
→ HIR
→ function
→ source span
```

khi debug metadata có sẵn.

---

## 476.43 — Assembly correlation

Tooling có thể hiển thị:

```text
source line
↓
generated assembly
↓
sample count
```

---

## 476.44 — Optimization correlation

Có thể kết hợp 450 optimization report:

```text
function hot
    ↓
bounds checks remain
    ↓
vectorization failed
    ↓
register spill
```

Đây là evidence chain, không phải automatic conclusion.

---

# 476.45 — Async profiling

Async stack phải reconstruct logical execution:

```text
Task
 ↓
Future
 ↓
await
 ↓
resume
```

không chỉ physical OS stack.

---

## 476.46 — Await latency

Profiler có thể phân biệt:

```text
compute_before_await
await_wait
compute_after_await
```

---

# 476.47 — IO profiling

454:

```text
open
read
write
connect
accept
DNS
TLS
```

có thể được instrument.

---

## 476.48 — Storage profiling

455:

```text
read_at
write_at
fsync
mmap
page/cache
transaction
WAL
```

---

# 476.49 — Database profiling

Có thể liên kết:

```text
query
transaction
lock
storage
network
```

vào một execution trace.

---

# 476.50 — GPU profiling

459/460 cần profile:

```text
kernel execution
queue wait
synchronization
memory transfer
allocation
```

---

## 476.51 — GPU timestamp

GPU timestamp không mặc định đồng nhất với CPU monotonic clock.

Profiler phải giữ clock-domain metadata.

---

## 476.52 — CPU↔GPU correlation

Nếu platform cho phép calibration:

```text
CPU timeline
      ↕
GPU timeline
```

có thể được correlate.

Nếu không, giữ hai timeline độc lập.

---

# 476.53 — GPU memory

Profile:

```text
allocated
resident
transferred
freed
peak
```

---

## 476.54 — GPU stalls

Phân biệt:

```text
CPU waiting GPU
GPU waiting memory
GPU queue starvation
synchronization
```

khi dữ liệu đủ.

---

# 476.55 — GUI profiling

452 có thể expose:

```text
input
layout
paint
render
present
frame_wait
```

---

## 476.56 — Frame profile

Có thể tạo:

```text
Frame N
 ├── Input
 ├── Update
 ├── Layout
 ├── Render
 └── Present
```

---

# 476.57 — Audio realtime profiling

461:

```text
callback duration
buffer deadline
underrun
DSP node duration
```

---

## 476.58 — Realtime violation

Nếu callback vượt budget, profiler phải báo:

```text
deadline_missed
```

không tự động thay đổi scheduling.

---

# 476.59 — Media profiling

462:

```text
demux
decode
filter
GPU upload
render
encode
mux
```

có thể được biểu diễn trên một timeline.

---

# 476.60 — Compiler profiling

Compiler 436 có thể profile:

```text
lex
parse
resolve
typecheck
trait solve
comptime
MIR
optimization
codegen
link
```

---

## 476.61 — Incremental compilation

Profile phải phân biệt:

```text
cache_hit
cache_miss
recomputed_query
```

---

# 476.62 — Query profiling

436 query database có thể cung cấp dependency tree:

```text
Query A
 ├── Query B
 ├── Query C
 └── Query D
```

kèm thời gian/cache behavior.

---

# 476.63 — Profile session

Concept:

```text
ProfileSession {
    target
    start
    end
    mode
    sampling_rate
    counters
    filters
    metadata
}
```

---

## 476.64 — Profile modes

Canonical profiles:

```text
cpu-sample
cpu-instrument
hardware-counter
memory
io
async
gpu
media
compiler
full
```

`full` chỉ là collection preset, không phải guarantee mọi capability đều khả dụng.

---

# 476.65 — Profile data format

Profile artifact phải có:

```text
version
compiler/build identity
target
clock information
symbols
samples
events
counters
correlation metadata
```

---

## 476.66 — Deterministic profile metadata

Artifact identity và metadata serialization phải deterministic khi source/environment giống nhau.

Runtime sample values tự nhiên không deterministic.

---

# 476.67 — Profile merge

Nhiều runs có thể merge.

Tool phải giữ số lượng runs và provenance.

---

## 476.68 — Profile comparison

Có thể so sánh:

```text
baseline
vs
candidate
```

theo:

- function;
- call path;
- source;
- counter;
- memory;
- IO;
- GPU;
- frame.

Không tạo một aggregate score.

---

# 476.69 — Statistical reporting

Report phải có:

```text
sample_count
run_count
mean
variance
percentiles
confidence information where applicable
```

không biến sample distribution thành exact runtime claim.

---

# 476.70 — Representative workload

PGO/profile data phải ghi workload identity.

Profile từ workload A không mặc định đại diện workload B.

---

# 476.71 — Profiling bias

Sampling profiler phải document:

- sampling interval;
- timer source;
- stack-walk limitations;
- excluded regions;
- multiplexing;
- missing samples.

---

# 476.72 — Profiling self-overhead

Profiler phải có khả năng đo overhead của chính profiler.

---

## 476.73 — Low-overhead mode

Low-overhead mode ưu tiên sampling và compact buffers.

---

## 476.74 — High-detail mode

High-detail mode có thể sử dụng instrumentation và richer metadata.

---

# 476.75 — Buffering

Profile collector phải hỗ trợ bounded buffers.

---

## 476.76 — Overflow

Khi profile buffer đầy:

```text
drop
stop
overwrite
```

phải là policy rõ ràng.

---

# 476.77 — Security

Profile có thể chứa:

- function names;
- source paths;
- arguments nếu developer yêu cầu;
- memory addresses;
- timing;
- device information.

Vì vậy profile artifact có thể chứa sensitive information.

---

## 476.78 — Privacy

Không tự động export profile ra ngoài máy.

---

# 476.79 — Release profiling

Production binary có thể được build với lightweight profiling capability.

Không yêu cầu full debug build.

---

## 476.80 — Symbol stripping

Profile có thể hoạt động với stripped binary ở mức machine-address nếu symbol/debug artifacts tồn tại riêng.

---

# 476.81 — AI profiler API

AI có thể query:

```text
hot_functions()
hot_paths()
cpu_time(function)
wall_time(function)
off_cpu_reasons()
allocation_hotspots()
lock_contention()
io_wait()
gpu_wait()
vectorization()
cache_behavior()
```

---

## 476.82 — AI source correlation

AI có thể truy:

```text
profile sample
→ function
→ source
→ MIR
→ machine instruction
```

---

## 476.83 — AI optimization loop

Compiler tooling hỗ trợ:

```text
profile
→ identify observed hotspot
→ inspect source/IR
→ inspect optimization decisions
→ propose change
→ benchmark
→ profile
```

AI không được tự coi hotspot là bằng chứng rằng một thay đổi sẽ cải thiện toàn chương trình.

---

# 476.84 — Profiler ≠ benchmark

Benchmark trả lời:

```text
how much work/time?
```

Profiler trả lời:

```text
where is execution/resource time going?
```

Hai hệ thống phải có artifact và methodology riêng.

---

# 476.85 — Profiler ≠ tracing

Tracing ghi event/span timeline.

Profiling có thể sample execution state và hardware behavior.

Chúng có thể liên kết bằng common IDs nhưng không đồng nhất.

---

# 476.86 — Profiler ≠ telemetry

Profile data không tự động được gửi đến external service.

---

# 476.87 — Test profiler

Compiler test suite phải kiểm tra:

```text
source mapping
inlining
tail calls
async
threads
tasks
actors
FFI
panic/unwind
```

---

# 476.88 — Cross-target

Profiler abstraction phải hỗ trợ:

```text
x86-64
AArch64
WASM
```

với capability differences rõ ràng.

---

# 476.89 — WASM

Browser/WASM profiling capability phụ thuộc browser/runtime.

Không giả định native PMU.

---

# 476.90 — Freestanding

Freestanding target có thể không có profiler runtime.

Compiler vẫn có thể emit profiling instrumentation khi platform cung cấp mechanism.

---

# 476.91 — Hard invariants

1. Profiler khác benchmark.
2. Profiler khác tracing.
3. Profiler khác telemetry.
4. Sampling profiling được hỗ trợ.
5. Instrumentation profiling được hỗ trợ.
6. Hardware-counter profiling được hỗ trợ khi platform cho phép.
7. Sampling là statistical measurement.
8. Sample không được coi là exact execution time.
9. Sampling frequency configurable.
10. Sampling overhead measurable.
11. Call stack reconstruction được hỗ trợ.
12. Inline frames được biểu diễn.
13. Logical và physical frames được phân biệt.
14. CPU time khác wall time.
15. On-CPU khác off-CPU.
16. Scheduler wait có thể được attribution.
17. Lock contention có thể được attribution.
18. Channel wait có thể được attribution.
19. Actor mailbox wait có thể được attribution.
20. Allocation profiling được hỗ trợ.
21. Heap profiling không cần GC.
22. Arena profiling được hỗ trợ.
23. Stack usage profiling được hỗ trợ khi platform cho phép.
24. Hardware counters có capability discovery.
25. Counter permission failure trả Result.
26. Multiplexing phải được ghi metadata.
27. Counter scaling phải được ghi metadata.
28. CPU frequency effects phải được phân biệt với raw cycles.
29. Turbo/throttling metadata có thể được ghi.
30. Cache counters target-specific.
31. Branch counters target-specific.
32. SIMD usage có thể được profile.
33. Vectorization report có thể correlate với profile.
34. Memory bandwidth measurement không được giả định portable.
35. Hotness là observed property.
36. Coldness là observed property.
37. PGO được hỗ trợ.
38. PGO profile phải có build/target identity.
39. Stale profile không được silently dùng.
40. Source correlation được hỗ trợ.
41. MIR correlation được hỗ trợ.
42. Assembly correlation được hỗ trợ.
43. Optimization correlation được hỗ trợ.
44. Async logical stacks được hỗ trợ.
45. Await latency có thể được phân tách.
46. IO profiling được hỗ trợ.
47. Storage profiling được hỗ trợ.
48. Database profiling được hỗ trợ.
49. GPU profiling được hỗ trợ khi platform cho phép.
50. GPU clock domain phải được phân biệt.
51. CPU/GPU correlation chỉ được thực hiện khi calibration hợp lệ.
52. GPU memory profiling được hỗ trợ.
53. GPU stall attribution phải dựa trên available evidence.
54. GUI frame profiling được hỗ trợ.
55. Audio realtime profiling được hỗ trợ.
56. Media pipeline profiling được hỗ trợ.
57. Compiler profiling được hỗ trợ.
58. Incremental cache behavior được profile.
59. Query dependency timing được profile.
60. Profile session có explicit configuration.
61. Profile artifact có version.
62. Profile artifact có target identity.
63. Profile artifact có clock metadata.
64. Profile artifact có provenance.
65. Profile merge giữ run provenance.
66. Profile comparison không tạo aggregate score.
67. Statistical data phải giữ sample/run counts.
68. Representative workload phải được ghi.
69. Sampling bias phải được document.
70. Profiler self-overhead phải đo được.
71. Low-overhead mode được hỗ trợ.
72. High-detail mode được hỗ trợ.
73. Profile buffers có bounded mode.
74. Buffer overflow policy explicit.
75. Profile artifacts có security/privacy boundary.
76. Không automatic profile upload.
77. Release profiling có thể nhẹ hơn debug.
78. Stripped binary vẫn có thể profile ở mức phù hợp.
79. AI có thể query hotspot evidence.
80. AI có thể query source/IR/machine correlation.
81. AI không được biến profile evidence thành guarantee về optimization outcome.
82. Profiler không thay đổi program semantics.
83. Profiler không yêu cầu GC.
84. Profiler không yêu cầu global runtime.
85. Profiler không tạo hidden telemetry.
86. Profiler không tự tạo hidden network connection.
87. Profiler không tự tạo background thread ngoài capability explicitly requested.
88. Freestanding target có thể omit profiler runtime.
89. WASM/native capability differences phải explicit.
90. **Axiom profiling phải biến execution thành dữ liệu có thể truy nguyên từ source → IR → machine code → CPU/GPU/resource behavior, với methodology, provenance và limitations rõ ràng, để compiler và AI tối ưu dựa trên evidence thay vì phỏng đoán.**

**BOOTSTRAP-476 hoàn tất / LOCKED.**

---

# BOOTSTRAP-477 — SOURCE MAP, CODE COVERAGE, TEST COVERAGE & QUALITY ANALYSIS FOUNDATION

477 tiếp tục hoàn thiện vòng **compiler → test → profile → quality**.

```text id="z1n5hf"
Source
  ↓
Compiler
  ↓
Executable
  ↓
Test / Fuzz / Benchmark
  ↓
Coverage + Profile + Diagnostics
  ↓
Source / IR Correlation
  ↓
Quality Analysis
```

Phạm vi 477:

- line coverage;
- statement coverage;
- branch coverage;
- condition coverage;
- function coverage;
- region coverage;
- path coverage metadata;
- source→machine mapping;
- optimized-code coverage;
- inlining-aware coverage;
- generated-code coverage;
- macro/comptime/generated-source provenance;
- async state-machine coverage;
- match-arm coverage;
- panic/error-path coverage;
- Result/Option branch coverage;
- unsafe-site coverage;
- FFI boundary coverage;
- thread/concurrency coverage;
- actor/message coverage;
- GUI/input coverage;
- media/audio/GPU coverage;
- coverage counters;
- instrumentation vs sampling limitations;
- atomic/thread-safe counter collection;
- coverage overhead;
- low-overhead mode;
- deterministic test coverage;
- fuzz coverage guidance;
- corpus minimization;
- coverage-guided fuzzing;
- differential coverage;
- regression coverage;
- baseline comparison;
- uncovered-code analysis;
- dead-code distinction;
- generated-code distinction;
- test-to-source mapping;
- test provenance;
- coverage artifact format;
- privacy/security;
- no “coverage score” as a universal quality judgment;
- AI query:
  - which source regions have no tests?
  - which branches are untested?
  - which unsafe sites lack coverage?
  - which FFI boundary has no integration test?
  - which recent change reduced coverage?
  - which fuzz input reaches a target path?

Đặc biệt 477 sẽ khóa distinction:

```text id="n3m4w8"
Uncovered
    ≠
Dead
    ≠
Untestable
    ≠
Unreachable
```

và:

```text id="8k8mna"
High Coverage
    ≠
Correct Program
```

Coverage chỉ là **evidence về những execution paths đã được quan sát**, không phải một thước đo chất lượng tổng hợp của chương trình.