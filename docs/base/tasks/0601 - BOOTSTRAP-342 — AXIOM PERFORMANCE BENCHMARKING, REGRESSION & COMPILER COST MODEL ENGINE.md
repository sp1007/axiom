# BOOTSTRAP-342 — AXIOM PERFORMANCE BENCHMARKING, REGRESSION & COMPILER COST MODEL ENGINE

Sau 340–341, Axiom đã có khả năng **phát hiện lỗi runtime** và **tự tìm lỗi compiler**. Bước tiếp theo cần khóa một vấn đề khác rất quan trọng với mục tiêu của Axiom:

> **Không chỉ compile đúng — Axiom phải liên tục chứng minh rằng compiler và chương trình vẫn nhanh, nhỏ và tiết kiệm tài nguyên sau mỗi thay đổi.**

Đặc biệt, mục tiêu của Axiom là hiệu năng **≥ C/C++ trong các workload phù hợp**, binary nhỏ và compiler đủ nhanh. Vì vậy benchmark không thể chỉ là một thư mục test đơn giản; nó phải trở thành một phần chính thức của compiler/build infrastructure.

---

# 1. Ba loại performance cần đo

Axiom phân biệt:

```text
Compiler Performance
Program Performance
Artifact Performance
```

### Compiler Performance

Đo:

- parse;
- type checking;
- trait solving;
- comptime;
- MIR;
- verification;
- optimization;
- codegen;
- object writing;
- linking;
- incremental compilation;
- memory consumption.

### Program Performance

Đo:

- execution time;
- throughput;
- latency;
- allocations;
- memory;
- cache behavior;
- branch behavior;
- vectorization;
- parallel scaling;
- GPU execution.

### Artifact Performance

Đo:

- binary size;
- mapped size;
- startup time;
- relocation count;
- imported symbols;
- sections;
- page count;
- code size;
- data size.

---

# 2. Không có một “benchmark score”

Axiom không dùng một con số duy nhất để đánh giá compiler.

Ví dụ:

```text
BenchmarkResult {
    wall_time
    cpu_time
    cycles
    instructions
    memory_peak
    allocations
    binary_size
    startup_time
    throughput
    latency
}
```

Mỗi metric có ý nghĩa riêng.

---

# 3. Benchmark phải reproducible

Mỗi benchmark result phải gắn với:

```text
CompilerFingerprint
SourceFingerprint
TargetFingerprint
BuildFingerprint
CPUFingerprint
OSFingerprint
BenchmarkFingerprint
ConfigurationFingerprint
```

Nếu thiếu những thông tin này, kết quả không được coi là comparable.

---

# 4. Compiler benchmark model

Một compiler invocation:

```text
axiom build foo.ax
```

được phân rã:

```text
Parse
Resolve
TypeCheck
TraitSolve
Comptime
HIR
MIR
Verify
Optimize
Codegen
Object
Link
```

Mỗi phase có timing riêng.

---

# 5. Query-level profiling

CompilerDB đã có query engine.

342 bổ sung:

```text
QueryCost {
    query_id
    invocation_count
    total_time
    self_time
    cache_hits
    cache_misses
    memory
}
```

Ví dụ:

```text
TraitSolve:
    calls: 1,284,000
    total: 4.8 s
    cache hit: 72%
```

---

# 6. Compiler cost attribution

Nếu compilation từ:

```text
5s → 9s
```

Axiom phải trả lời:

> Tại sao?

Ví dụ:

```text
+2.8s TraitSolver
+0.7s Comptime
+0.4s MIR optimization
+0.1s Codegen
```

Không chỉ:

```text
Compilation slower by 80%
```

---

# 7. Critical path

Compiler có parallel build.

Do đó:

```text
sum(all task time)
```

không phản ánh compile latency.

Phải đo:

```text
CriticalPathTime
ParallelEfficiency
WorkerIdleTime
```

---

# 8. Incremental benchmark

Mỗi benchmark source có nhiều mutation:

```text
NoChange
CommentChange
PrivateBodyChange
PrivateTypeChange
PublicAPIChange
ABIChange
DependencyChange
TargetChange
```

Sau đó đo:

```text
RebuildTime
ReusedQueries
InvalidatedQueries
RecompiledNodes
```

---

# 9. Incremental efficiency

Ví dụ:

```text
Clean build = 10 s

comment change = 0.05 s
private change = 0.4 s
public API change = 3.1 s
```

Benchmark phải lưu các baseline này.

---

# 10. Cache efficiency

Đo:

```text
LocalCacheHit
LocalCacheMiss
RemoteCacheHit
RemoteCacheMiss
ProofCacheHit
CodegenCacheHit
LinkCacheHit
```

---

# 11. Memory benchmark

Compiler phải báo:

```text
PeakRSS
HeapAllocated
ArenaAllocated
MappedMemory
IRMemory
CacheMemory
```

và phân theo subsystem.

---

# 12. Memory regression

Ví dụ:

```text
Compiler v0.9
Peak = 1.8 GB

Compiler v0.10
Peak = 3.2 GB
```

Benchmark system phải phát hiện regression ngay cả khi compile time không thay đổi.

---

# 13. Compilation scalability

Test:

```text
1K LOC
10K LOC
100K LOC
1M LOC
10M LOC
```

để tìm:

```text
O(n)
O(n log n)
O(n²)
```

và pathological cases.

---

# 14. Solver scalability

Trait solver và type inference đặc biệt cần:

```text
Depth
GenericCount
ConstraintCount
CandidateCount
TypeSize
```

Benchmark phải tìm complexity explosion.

---

# 15. Comptime cost model

Đo:

```text
ComptimeExecutionTime
ComptimeMemory
GeneratedHIR
GeneratedMIR
GeneratedDeclarations
CacheReuse
```

Một comptime function không nên vô tình tạo compiler explosion.

---

# 16. Compiler resource budgets

Benchmark có thể đặt:

```text
--max-time
--max-memory
--max-comptime
--max-query-cost
```

để phát hiện regression.

---

# 17. Program benchmark format

Định nghĩa benchmark artifact:

```text
Benchmark {
    id
    name
    source
    workload
    input
    target
    repetitions
    warmup
    metrics
    expected_behavior
}
```

---

# 18. Warmup

Đặc biệt quan trọng với:

- CPU cache;
- JIT host tools;
- GPU;
- OS page cache.

Axiom benchmark runner hỗ trợ:

```text
WarmupRuns
MeasuredRuns
Cooldown
```

---

# 19. Statistical measurement

Không dùng một lần chạy.

Ví dụ:

```text
N = 30
```

tính:

```text
median
mean
min
max
p50
p90
p95
p99
standard deviation
```

---

# 20. Outlier handling

Không tự động vứt outlier.

Benchmark phải lưu:

```text
raw samples
```

và đánh dấu:

```text
thermal throttling
background load
scheduler anomaly
```

nếu phát hiện được.

---

# 21. CPU performance counters

Nếu target hỗ trợ:

```text
cycles
instructions
branches
branch_misses
cache_references
cache_misses
```

---

# 22. Derived metrics

Có thể tính:

```text
IPC
CPI
branch miss rate
cache miss rate
instructions / operation
cycles / operation
```

nhưng lưu cả raw counters.

---

# 23. Hardware normalization

Benchmark machine identity:

```text
CPU model
microarchitecture
cores
threads
frequency
RAM
NUMA
GPU
OS
kernel
```

được ghi vào result.

---

# 24. CPU frequency

Không được giả định:

```text
3.5 GHz
```

luôn cố định.

Runner ghi:

```text
nominal_frequency
observed_frequency
```

nếu platform hỗ trợ.

---

# 25. CPU affinity

Benchmark có thể yêu cầu:

```text
pin_to_cpu
pin_to_core
num_threads
```

để giảm scheduler noise.

---

# 26. NUMA

Server workload có thể cần:

```text
NUMA node
memory locality
CPU affinity
```

Axiom benchmark runner phải có optional NUMA configuration.

---

# 27. Program memory metrics

Đo:

```text
RSS
peak RSS
heap allocations
heap frees
allocation bytes
resident pages
```

Sanitizer build không được dùng để so sánh performance production.

---

# 28. Allocation benchmark

Axiom muốn allocator linh hoạt.

Do đó benchmark:

```text
general allocator
arena
pool
slab
stack
custom allocator
```

không nên bị trộn thành một metric.

---

# 29. Binary size benchmark

Sau linking:

```text
FileSize
MappedSize
TextSize
RodataSize
DataSize
BssSize
DebugSize
RelocationSize
MetadataSize
```

---

# 30. Binary-size regression

Ví dụ:

```text
v1:
binary = 820 KB

v2:
binary = 1.4 MB
```

hệ thống phải biết:

```text
+580 KB
```

đến từ:

```text
function
section
dependency
runtime component
metadata
```

---

# 31. Size attribution

Tận dụng 335/336:

```text
SizeContribution {
    symbol
    section
    package
    dependency
    root
    bytes
}
```

---

# 32. “Why binary grew?”

CLI:

```text
axiom size explain app.exe
```

Ví dụ:

```text
+120 KB  Unicode
+80 KB   HTTP
+42 KB   reflection
+31 KB   generic specialization
+18 KB   panic runtime
```

---

# 33. Startup benchmark

Native application cần:

```text
ProcessStart
 ↓
Loader
 ↓
RuntimeInit
 ↓
AxiomEntry
 ↓
UserMain
```

Đo từng đoạn.

---

# 34. Cold vs warm startup

Phân biệt:

```text
ColdStart
WarmStart
```

vì OS page cache ảnh hưởng rất lớn.

---

# 35. Dynamic loading benchmark

Đối với plugin/component:

```text
load time
relocation time
symbol resolution
initialization
first-call latency
```

---

# 36. FFI benchmark

Đo:

```text
Axiom → C
C → Axiom
Axiom → Component
Component → Axiom
```

để tránh abstraction overhead không cần thiết.

---

# 37. Trait dispatch benchmark

So sánh:

```text
static dispatch
dynamic dispatch
devirtualized dispatch
```

nhưng không coi dynamic dispatch là “chậm” mặc định.

Benchmark đo overhead thực tế.

---

# 38. Closure benchmark

Đo:

```text
noncapturing closure
capturing closure
boxed closure
inline closure
```

để xác nhận zero-cost abstraction.

---

# 39. Generic benchmark

So sánh:

```text
generic monomorphized
generic shared
dyn Trait
```

và:

```text
binary size
execution speed
compile time
```

---

# 40. Ownership abstraction benchmark

Một trong các benchmark quan trọng nhất:

```text
Vec
view
mut_view
Box
Arc
Mutex
```

để chứng minh compiler có thể erase abstraction khi semantics cho phép.

---

# 41. View overhead benchmark

Ví dụ:

```text
fn sum(x: view<i32>) -> i64
```

phải benchmark với equivalent raw loop.

Mục tiêu:

```text
same optimized machine behavior
```

khi semantics tương đương.

---

# 42. Async benchmark

Đo:

```text
Future creation
Future poll
await
wake
task spawn
task migration
cancellation
```

---

# 43. Async memory

Đo:

```text
Future state size
Task allocation
Task stack
Waker allocation
Executor queue
```

Đặc biệt kiểm tra compiler state-field elimination.

---

# 44. Concurrency scaling

Workload:

```text
1 thread
2
4
8
16
32
```

đo:

```text
throughput
latency
speedup
efficiency
```

---

# 45. Synchronization benchmark

Đo:

```text
Mutex
RwLock
Atomic
Channel
Semaphore
```

theo:

```text
uncontended
light contention
heavy contention
```

---

# 46. False-sharing benchmark

Compiler/runtime không nên vô tình tạo layout gây false sharing.

Benchmark:

```text
thread A → field A
thread B → field B
```

và so sánh layouts.

---

# 47. GPU benchmark

Đo riêng:

```text
kernel launch
host-device transfer
kernel execution
synchronization
memory bandwidth
occupancy
```

---

# 48. GPU compiler benchmark

Đo:

```text
kernel compilation
GPU lowering
register usage
shared memory
occupancy
```

---

# 49. Vectorization benchmark

Compiler phải ghi:

```text
vectorized
partially_vectorized
not_vectorized
reason
```

Ví dụ:

```text
Loop #12:
vectorized = false

Reason:
possible alias overlap
```

---

# 50. Optimization explanation

CLI:

```text
axiom optimize explain foo.ax
```

Ví dụ:

```text
Loop vectorized
  because:
    bounds proven
    regions DISJOINT
    trip count known

Allocation eliminated
  because:
    NoEscape
```

---

# 51. Performance provenance

Mỗi benchmark result có thể liên kết:

```text
Benchmark
 ↓
Function
 ↓
MIR
 ↓
Optimization
 ↓
Machine instructions
```

Do đó có thể hỏi:

> Tại sao phiên bản này nhanh hơn?

---

# 52. Optimization remarks

Compiler ghi:

```text
OptimizationRemark {
    pass
    source_span
    decision
    reason
    cost
    before
    after
}
```

Ví dụ:

```text
LoopVectorize:
  rejected

reason:
  unknown alias relationship
```

---

# 53. Cost model

Đây là phần quan trọng nhất của 342.

Compiler cần một abstraction:

```text
CostModel
```

cho:

- instruction;
- memory;
- branch;
- vector;
- call;
- allocation;
- synchronization;
- code size.

---

# 54. Cost không phải semantics

Cost model chỉ quyết định:

```text
nên tối ưu thế nào
```

Không quyết định:

```text
chương trình có hợp lệ hay không
```

---

# 55. Target-specific cost

Ví dụ:

```text
x86 AVX2
x86 AVX-512
ARM NEON
ARM SVE
WASM SIMD
```

có cost khác nhau.

Do đó:

```text
TargetCostModel
```

phải nằm trong TargetDB.

---

# 56. CPU microarchitecture cost

Có thể có:

```text
Generic x86-64
Zen
Core
Neoverse
Apple Silicon
```

Nhưng không được biến architecture-specific tuning thành language semantics.

---

# 57. Cost model versioning

Một thay đổi cost model có thể thay đổi generated code.

Vì vậy:

```text
CostModelFingerprint
```

phải tham gia:

```text
CodegenCache
ArtifactFingerprint
BenchmarkMetadata
```

---

# 58. PGO integration

322 đã đặt nền tảng PGO.

342 chuẩn hóa:

```text
Profile
 ↓
Profile validation
 ↓
Profile attribution
 ↓
Cost model
 ↓
Optimization
```

---

# 59. Profile quality

Profile phải ghi:

```text
sample_count
coverage
confidence
timestamp
target
binary_fingerprint
```

Compiler không được coi profile stale là sự thật tuyệt đối.

---

# 60. Profile-guided benchmark

Benchmark runner có thể:

```text
build instrumented
run workload
collect profile
build PGO
run benchmark
compare
```

---

# 61. Auto-tuning

Một compiler pass có thể có candidates:

```text
A
B
C
```

Benchmark engine chạy thử và chọn configuration theo policy.

Ví dụ:

```text
vector width
unroll factor
inlining threshold
```

---

# 62. Nhưng auto-tuning không được phá reproducibility

Có hai mode:

```text
DeterministicOptimization
AdaptiveOptimization
```

Adaptive phải lưu:

```text
decision
profile
hardware
cost-model version
```

để reproduce.

---

# 63. Benchmark regression policy

Mỗi benchmark có threshold:

```text
max slowdown = 3%
max binary growth = 2%
max compile regression = 5%
```

Nhưng threshold là **project policy**, không phải language semantics.

---

# 64. Statistical regression

Không báo regression chỉ vì:

```text
10.00 ms
→
10.05 ms
```

nếu variance:

```text
±0.3 ms
```

Benchmark engine phải có statistical test.

---

# 65. Regression classifications

```text
Improvement
Neutral
Noise
Regression
SevereRegression
Inconclusive
```

---

# 66. Không gộp các metric

Một thay đổi có thể:

```text
+5% speed
+12% binary size
```

Không được biến thành:

```text
Score = 0.83
```

trừ khi user/project tự định nghĩa objective.

---

# 67. Benchmark dashboard

Có thể hiển thị:

```text
Compile time
Runtime
Binary size
Memory
Startup
```

theo commit.

---

# 68. Historical tracking

```text
commit
compiler version
benchmark result
environment
```

để vẽ regression timeline.

---

# 69. Benchmark bisect

Nếu:

```text
v1 = fast
v20 = slow
```

hệ thống binary-search commit:

```text
v10
v15
v17
...
```

để tìm regression introduction.

---

# 70. Compiler performance flamegraph

Compiler có thể xuất:

```text
compile.perf
```

cho:

```text
Parse
TraitSolver
MIR
Optimization
Codegen
Link
```

---

# 71. Program profile

Tích hợp profiler 313:

```text
CPU profile
Memory profile
Async profile
GPU profile
Lock profile
```

---

# 72. Benchmark artifact

Định dạng:

```text
.axbench
```

có:

```text
benchmark identity
source fingerprint
target
compiler
configuration
raw measurements
statistics
profiles
artifacts
```

---

# 73. Machine-readable result

Ví dụ:

```text
BenchmarkResult {
    benchmark_id,
    compiler_fingerprint,
    target_fingerprint,
    samples,
    statistics,
    artifact_fingerprint,
    profile_fingerprint
}
```

AI-agent có thể đọc trực tiếp.

---

# 74. AI performance diagnosis

Compiler có thể xuất:

```text
PerformanceFinding {
    severity
    function
    source_span
    metric
    baseline
    current
    probable_cause
    evidence
}
```

Ví dụ:

```text
PerformanceFinding:
  function = process_packets
  slowdown = 18%

Evidence:
  vectorization rejected
  reason = unknown alias
  hot loop = 73% CPU time
```

---

# 75. AI không được tự sửa semantics

Performance agent chỉ được đề xuất:

```text
rewrite
annotation
algorithm
data layout
```

Không được tự thay đổi language semantics.

---

# 76. Benchmark-aware compiler testing

Mỗi compiler change có thể chạy:

```text
Correctness
Fuzz
Benchmark
BinarySize
Memory
```

trong CI.

---

# 77. Performance gate

Release compiler chỉ pass nếu policy yêu cầu:

```text
Correctness = pass
Fuzz = pass
Performance = within threshold
BinarySize = within threshold
```

---

# 78. Regression artifact

Khi fail:

```text
PerformanceRegression {
    baseline
    current
    benchmark
    statistical_evidence
    suspected_pass
    suspected_commit
}
```

---

# 79. Compiler DB

Bổ sung:

```text
BenchmarkDB
BenchmarkSuiteDB
BenchmarkRunnerDB
MeasurementDB
HardwareDB
PerformanceProfileDB
CostModelDB
OptimizationRemarkDB
RegressionDB
PerformanceHistoryDB
AutotuneDB
```

---

# 80. Implementation tree

```text
compiler/
└── performance/
    ├── benchmark/
    ├── runner/
    ├── measurement/
    ├── statistics/
    ├── hardware/
    ├── counters/
    ├── compiler_profile/
    ├── runtime_profile/
    ├── binary_size/
    ├── startup/
    ├── async/
    ├── concurrency/
    ├── gpu/
    ├── cost_model/
    ├── pgo/
    ├── autotune/
    ├── optimization_remarks/
    ├── regression/
    ├── bisect/
    ├── history/
    └── reporting/
```

---

# 81. Invariants

```text
APERF-01
Benchmark results must identify the compiler and target.

APERF-02
Raw measurements must be preserved.

APERF-03
Benchmark statistics must distinguish noise from regression.

APERF-04
Compiler and program performance must be measured separately.

APERF-05
Binary size must be independently measurable.

APERF-06
Compile-time phase attribution must be available.

APERF-07
Incremental compilation performance must be measurable.

APERF-08
Cache hits and misses must be observable.

APERF-09
Memory usage must be measurable independently from CPU time.

APERF-10
Optimization remarks must preserve source provenance.

APERF-11
Cost models must not alter language semantics.

APERF-12
Target-specific cost models must be versioned.

APERF-13
Adaptive optimization decisions must be reproducible when requested.

APERF-14
PGO data must identify the binary and target from which it originated.

APERF-15
Stale profile data must never be treated as guaranteed truth.

APERF-16
Performance optimization must preserve Verified MIR semantics.

APERF-17
Benchmark runner resource limits must be explicit.

APERF-18
Benchmark results from incompatible hardware must not be silently compared.

APERF-19
Binary-size attribution must identify contributing symbols/sections where possible.

APERF-20
Performance regressions must retain reproducible artifacts.

APERF-21
Benchmark policies are external configuration, not language semantics.

APERF-22
Auto-tuning must preserve correctness.

APERF-23
Auto-tuning decisions must be recordable.

APERF-24
Compiler performance diagnostics must be machine-readable.

APERF-25
Performance data must integrate with debugger, profiler, optimizer and build provenance systems.
```

---

# 82. Definition of Done

BOOTSTRAP-342 hoàn thành khi Axiom có:

- compiler phase benchmarking;
- query-level compiler profiling;
- incremental compilation benchmarking;
- cache benchmarking;
- compiler memory benchmarking;
- source-size scalability tests;
- trait-solver scalability tests;
- comptime benchmarking;
- runtime benchmarking;
- allocation benchmarking;
- concurrency scalability;
- async benchmarking;
- GPU benchmarking;
- FFI overhead benchmarking;
- startup benchmarking;
- binary-size benchmarking;
- size attribution;
- CPU hardware counters;
- statistical analysis;
- reproducible benchmark artifacts;
- historical performance tracking;
- regression detection;
- regression bisect;
- optimization remarks;
- target-aware cost models;
- PGO integration;
- profile validation;
- auto-tuning infrastructure;
- AI-readable performance findings;
- CI performance gates;
- `.axif`/build/artifact fingerprint integration.

---

## Kiến trúc quan trọng của 342

Axiom lúc này hình thành một vòng lặp hoàn chỉnh:

```text
                 ┌────────────────────┐
                 │  LANGUAGE / SOURCE │
                 └─────────┬──────────┘
                           ↓
                    ┌──────────────┐
                    │   COMPILER   │
                    └──────┬───────┘
                           ↓
              ┌────────────┴────────────┐
              ↓                         ↓
        Correctness                 Performance
              ↓                         ↓
       Fuzz / Verify              Benchmark
              ↓                         ↓
        Sanitizer                 Profiler
              ↓                         ↓
        Regression                Cost Model
              └────────────┬────────────┘
                           ↓
                    Optimization
                           ↓
                    New Compiler
                           │
                           └──────────→ repeat
```

Điểm quan trọng nhất là **performance trở thành một thuộc tính được kiểm chứng liên tục**, không phải một lời quảng cáo của ngôn ngữ.

Và với Axiom, compiler cuối cùng có thể biết khá chính xác:

> **“Đoạn code này chậm vì cái gì, compiler đã thử tối ưu gì, tại sao không tối ưu được, và thay đổi nào khiến nó chậm đi.”**

Đó là nền tảng cần thiết trước khi tiếp tục hoàn thiện các lớp deployment/platform cao hơn.