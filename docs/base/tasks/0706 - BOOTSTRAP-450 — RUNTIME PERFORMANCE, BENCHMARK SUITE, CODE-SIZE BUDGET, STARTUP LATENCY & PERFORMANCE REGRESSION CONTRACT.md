# BOOTSTRAP-450 — RUNTIME PERFORMANCE, BENCHMARK SUITE, CODE-SIZE BUDGET, STARTUP LATENCY & PERFORMANCE REGRESSION CONTRACT

**Trạng thái: COMPLETED / LOCKED**

Task này thiết lập **hệ thống đo lường hiệu năng chính thức của Axiom**.

Mục tiêu không phải tuyên bố chung chung “Axiom nhanh”, mà phải có khả năng trả lời bằng số liệu:

```text
Axiom program
    ↓
compile time
code size
startup latency
runtime latency
throughput
memory usage
allocation behavior
binary dependencies
```

và xác định được overhead đến từ đâu.

---

## 450.1 — Performance dimensions

Axiom benchmark system theo dõi tối thiểu:

```text
compile_time
incremental_compile_time
runtime
latency
throughput
memory
allocation_count
allocation_bytes
binary_size
startup_time
```

---

## 450.2 — Compile-time performance

Compile time gồm:

```text
frontend
semantic
comptime
optimization
codegen
link
```

---

## 450.3 — Incremental compile performance

Phải đo riêng:

```text
cold build
warm build
small edit
API edit
large edit
dependency edit
```

---

## 450.4 — Runtime performance

Runtime benchmark đo workload thực tế thay vì chỉ đo micro-operation.

---

## 450.5 — Latency

Latency được đo ở percentile khi phù hợp:

```text
p50
p90
p95
p99
p99.9
```

---

## 450.6 — Throughput

Ví dụ:

```text
items/sec
requests/sec
MB/sec
operations/sec
```

---

## 450.7 — Memory

Theo dõi:

```text
peak RSS
heap bytes
stack usage
resident executable data
```

---

## 450.8 — Allocation

Đo:

```text
allocation count
allocation bytes
reallocation count
deallocation count
```

---

## 450.9 — Startup

Startup được đo từ OS process launch đến application-defined readiness point.

---

## 450.10 — Binary size

Phân biệt:

```text
text
rodata
data
bss
debug
metadata
imports
```

---

## 450.11 — Stripped size

Release benchmark phải có stripped artifact measurement.

---

## 450.12 — Debug size

Debug artifact size được đo riêng.

---

## 450.13 — Static dependency size

Tool phải có khả năng phân tích contribution của static libraries.

---

## 450.14 — Dynamic dependencies

Dynamic dependencies không được tính nhầm toàn bộ vào executable size.

---

## 450.15 — Runtime size

Axiom runtime contribution phải được đo riêng.

---

# 450.16 — Benchmark categories

Benchmark suite gồm:

```text
micro
algorithm
memory
IO
concurrency
async
FFI
startup
compile
code-size
real-world
```

---

## 450.17 — Microbenchmark

Dùng để kiểm tra một operation nhỏ.

Không được dùng microbenchmark đơn độc để kết luận overall performance.

---

## 450.18 — Algorithm benchmark

Bao gồm:

```text
sorting
hashing
parsing
compression
serialization
numeric computation
matrix operations
```

---

## 450.19 — Memory benchmark

Đo:

```text
allocation
copy
move
layout
cache behavior
```

---

## 450.20 — Concurrency benchmark

Đo:

```text
thread creation
mutex
atomic
channel
parallel workload
```

---

## 450.21 — Async benchmark

Đo riêng:

```text
task creation
polling
scheduling
I/O wait
wake-up
```

---

## 450.22 — FFI benchmark

So sánh overhead:

```text
Axiom → Axiom
Axiom → C ABI
C → Axiom
```

---

## 450.23 — Startup benchmark

Các executable nhỏ phải được benchmark riêng để phát hiện runtime startup overhead.

---

## 450.24 — Real-world benchmark

Suite phải có application-sized workloads.

---

# 450.25 — Reference implementations

Benchmark có thể có implementation tương ứng bằng:

```text
Axiom
C
C++
Rust
other relevant systems language
```

nhưng benchmark report **không được tự động biến kết quả thành ranking**.

Mục tiêu là xác định các đặc tính kỹ thuật.

---

## 450.26 — Same workload contract

Các implementation phải thực hiện cùng semantic workload.

---

## 450.27 — Input equivalence

Input phải được cố định hoặc reproducibly generated.

---

## 450.28 — Output equivalence

Kết quả phải được validate trước khi performance result được chấp nhận.

---

## 450.29 — Compiler configuration

Benchmark ghi:

```text
compiler
version
target
optimization
CPU features
LTO
PGO
```

---

## 450.30 — Hardware identity

Benchmark ghi:

```text
CPU
cores
RAM
OS
kernel/version
```

khi relevant.

---

## 450.31 — Thermal state

Long-running benchmark nên record thermal/throttling conditions khi platform cung cấp.

---

## 450.32 — Background load

Benchmark environment nên giảm background workload.

---

## 450.33 — Warm-up

JIT không phải Axiom requirement, nhưng benchmark runtime libraries/cache-sensitive workloads có thể cần warm-up methodology.

---

## 450.34 — Repetitions

Benchmark phải chạy đủ repetitions để estimate variance.

---

## 450.35 — Statistical reporting

Report:

```text
median
variance
min/max
percentiles
sample count
```

khi phù hợp.

---

## 450.36 — Outlier handling

Outlier handling phải được ghi rõ, không được silently discard measurements.

---

## 450.37 — Benchmark stability

Benchmark runner phát hiện excessive variance.

---

## 450.38 — Noise threshold

Benchmark có thể đánh dấu result:

```text
stable
noisy
invalid
```

---

## 450.39 — Regression threshold

Mỗi benchmark có configurable regression threshold.

---

## 450.40 — Performance regression

Regression xảy ra khi metric thay đổi vượt threshold theo statistical confidence/rule đã cấu hình.

---

## 450.41 — Regression ≠ correctness failure

Performance regression và correctness failure là hai loại kết quả riêng.

---

## 450.42 — Benchmark baseline

Baseline được lưu cùng:

```text
commit
compiler
target
configuration
hardware
```

---

## 450.43 — Historical trend

Benchmark system có thể giữ lịch sử:

```text
commit → metric
```

---

## 450.44 — Benchmark bisect

Có thể tìm commit gây regression bằng automated bisect.

---

## 450.45 — Compiler optimization regression

Phải phân biệt:

```text
source regression
compiler regression
library regression
runtime regression
platform regression
```

---

# 450.46 — Performance attribution

Khi benchmark thay đổi, tool cố gắng xác định:

```text
frontend
optimizer
codegen
runtime
library
linker
```

---

## 450.47 — Optimization report

Benchmark có thể liên kết với:

```text
inline decisions
vectorization
allocation elimination
bounds-check elimination
```

---

## 450.48 — Assembly correlation

Benchmark có thể lưu generated assembly/hash để correlate performance changes.

---

## 450.49 — Hardware-counter support

Optional support:

```text
cycles
instructions
branches
branch misses
cache misses
```

---

## 450.50 — Platform abstraction

Hardware counters là optional platform capability, không phải language semantic requirement.

---

# 450.51 — Binary-size budget

Project có thể đặt:

```text
max_text_size
max_binary_size
max_runtime_size
```

---

## 450.52 — Size regression

Exceeding configured budget có thể fail CI.

---

## 450.53 — Size attribution

Tool có thể report contribution theo:

```text
package
module
function
runtime capability
```

---

## 450.54 — Dead code impact

Unused code không nên contribute vào final static executable khi linker GC chứng minh unreachable.

---

## 450.55 — Generic bloat

Size analysis phải phát hiện generic specialization explosion.

---

## 450.56 — Inline bloat

Tool phải report code-size increase do inlining.

---

## 450.57 — Runtime capability bloat

Tool phải xác định capability nào kéo runtime code vào binary.

---

# 450.58 — Startup budget

Application có thể đặt startup budget.

---

## 450.59 — Static initialization

Global initialization phải explicit và analyzable.

---

## 450.60 — Initialization order

Axiom không cho phép hidden initialization-order dependency giữa modules.

---

## 450.61 — Lazy initialization

Library có thể dùng lazy initialization explicit.

---

## 450.62 — Startup allocations

Startup allocation count có thể được benchmark.

---

## 450.63 — Minimal executable

Một chương trình:

```text
fn main() -> i32 {
    42
}
```

phải có khả năng link với minimal runtime hoặc freestanding startup.

---

## 450.64 — Runtime-free executable

Freestanding program không được bị ép link standard runtime.

---

# 450.65 — Memory budget

Application có thể đặt:

```text
max_heap
max_stack
max_rss
```

cho test/runtime environment.

---

## 450.66 — Allocation budget

Benchmark có thể đặt:

```text
max_allocations
max_allocated_bytes
```

---

## 450.67 — Allocation-free contract

Function có thể được đánh dấu:

```text
@no_alloc
```

và benchmark/test runner có thể verify runtime behavior.

---

## 450.68 — Blocking-free contract

Tương tự:

```text
@no_block
```

có thể được runtime instrumentation kiểm chứng.

---

## 450.69 — Panic-free contract

```text
@no_panic
```

có thể được compiler và runtime test tooling kiểm chứng ở mức phù hợp.

---

# 450.70 — Benchmark reproducibility

Benchmark phải ghi exact:

```text
source
dependencies
compiler
target
flags
hardware
input
```

---

## 450.71 — Benchmark artifact

Result được serialize thành machine-readable format.

---

## 450.72 — Benchmark schema

Conceptual:

```text
benchmark_result {
    benchmark_id
    commit
    compiler
    target
    configuration
    environment
    input_hash
    samples
    metrics
}
```

---

## 450.73 — AI benchmark query

AI có thể hỏi:

```text
why regression?
what changed?
which function grew?
which benchmark failed?
```

---

## 450.74 — Performance context

AI nhận semantic + benchmark metadata thay vì chỉ raw numbers.

---

## 450.75 — Optimization experiment

Agent có thể tạo experiment:

```text
baseline
candidate
benchmark
compare
```

---

## 450.76 — Automated optimization loop

CI/AI có thể:

```text
measure
→ identify hotspot
→ inspect optimization report
→ modify
→ benchmark
```

nhưng compiler không tự thay đổi source.

---

# 450.77 — Benchmark correctness oracle

Mỗi benchmark phải có correctness check.

---

## 450.78 — Golden output

Deterministic workload có thể dùng expected output hash.

---

## 450.79 — Numeric tolerance

Floating-point benchmark dùng tolerance phù hợp semantics.

---

## 450.80 — Performance-only result forbidden

Không chấp nhận benchmark result nếu correctness validation fail.

---

# 450.81 — Benchmark isolation

Benchmark executable phải chạy độc lập khỏi test runner overhead nếu đo startup/runtime.

---

## 450.82 — Harness overhead

Harness overhead phải được loại khỏi measured region khi phù hợp.

---

## 450.83 — Measurement boundary

Benchmark xác định rõ:

```text
process startup
setup
measured workload
teardown
```

---

## 450.84 — Cold vs warm

Có thể đo:

```text
cold start
warm start
```

riêng.

---

## 450.85 — Disk cache

Compile benchmark phải phân biệt:

```text
cold cache
warm cache
incremental cache
```

---

# 450.86 — Compiler benchmark

Compiler benchmark đo:

```text
parse/sec
typecheck/sec
MIR/sec
codegen/sec
link/sec
```

khi useful.

---

## 450.87 — Peak compiler memory

Compiler phải expose peak memory metric.

---

## 450.88 — Parallel scaling

Build benchmark có thể đo:

```text
1 worker
2
4
8
...
```

---

## 450.89 — Scaling efficiency

Tool có thể tính scaling efficiency nhưng không biến nó thành ranking.

---

## 450.90 — Incremental benchmark matrix

Test:

```text
body edit
signature edit
struct layout edit
trait edit
dependency edit
```

---

# 450.91 — Code generation quality

Benchmark suite có thể inspect:

```text
instruction count
code size
register spills
vectorization
branches
```

---

## 450.92 — Instruction count

Instruction count là diagnostic, không phải universal runtime predictor.

---

## 450.93 — Spill count

Register spill được report.

---

## 450.94 — Vectorization report

Report:

```text
vectorized loops
SIMD width
reason not vectorized
```

---

## 450.95 — Bounds-check report

Report:

```text
eliminated
retained
reason
```

---

# 450.96 — Performance contracts

Library có thể document performance properties:

```text
O(n)
allocation-free
blocking-free
```

---

## 450.97 — Complexity vs actual performance

Big-O không thay thế benchmark.

---

## 450.98 — API performance metadata

Semantic metadata có thể chứa:

```text
complexity
allocations
blocking
panic
```

---

## 450.99 — Performance-sensitive API

Library authors có thể expose specialized fast paths.

---

## 450.100 — Explicit fast path

Fast path phải preserve semantic equivalence.

---

# 450.101 — Benchmark suite hierarchy

```text
tests/
benchmarks/
    compiler/
    runtime/
    std/
    language/
    native/
    cross-target/
    regression/
```

---

## 450.102 — Benchmark IDs

Stable benchmark IDs:

```text
BENCH-MEM-001
BENCH-VEC-001
```

---

## 450.103 — Benchmark versioning

Changing workload invalidates comparison with old benchmark versions unless migration metadata exists.

---

## 450.104 — Benchmark metadata

Mỗi benchmark ghi:

```text
purpose
input
expected output
measurement
environment
```

---

## 450.105 — Benchmark ownership

Benchmark itself phải được code-review như production test.

---

# 450.106 — Cross-target benchmark

Các target có benchmark riêng.

Không extrapolate Linux results sang Windows/macOS/iOS/Android/WASM.

---

## 450.107 — Target baseline

Baseline được lưu riêng theo target.

---

## 450.108 — CPU baseline

Different CPU models tạo baseline riêng.

---

## 450.109 — OS baseline

Different OS versions có thể tạo baseline riêng.

---

## 450.110 — Virtualized environments

VM/container results phải được đánh dấu.

---

# 450.111 — Regression classification

Regression report:

```text
compile-time
runtime
memory
binary-size
startup
allocation
codegen
```

---

## 450.112 — Improvement classification

Improvement cũng được record cùng schema, không tự động kết luận quality tổng thể.

---

## 450.113 — Tradeoff report

Ví dụ:

```text
runtime: -3%
binary: -12%
compile: +18%
```

để developer tự đánh giá tradeoff.

---

## 450.114 — No aggregate score

Axiom benchmark system không tạo một “performance score” tổng hợp mặc định.

---

## 450.115 — No hidden weighting

Không âm thầm gán trọng số giữa:

```text
speed
size
compile time
memory
```

---

# 450.116 — Performance CI tiers

CI có thể có:

```text
smoke
standard
extended
nightly
```

---

## 450.117 — Smoke benchmarks

Những benchmark nhỏ chạy mỗi commit.

---

## 450.118 — Extended benchmarks

Chạy theo schedule.

---

## 450.119 — Nightly stress

Workloads nặng/cross-target/fuzz-performance có thể chạy nightly.

---

## 450.120 — Release benchmark

Release candidate phải chạy canonical benchmark suite.

---

# 450.121 — Performance artifact retention

Giữ:

```text
result
binary
assembly
metadata
compiler config
```

theo retention policy.

---

## 450.122 — Artifact comparison

Có thể diff hai generated binaries:

```text
symbol
section
function
```

---

## 450.123 — Function-level size diff

Tool report:

```text
foo +120 bytes
bar -48 bytes
```

---

## 450.124 — Assembly diff

Có thể compare generated assembly giữa compiler revisions.

---

## 450.125 — Optimization diff

Có thể compare:

```text
inline decisions
vectorization
allocation elimination
```

---

# 450.126 — Performance debugging workflow

Canonical:

```text
benchmark regression
        ↓
identify metric
        ↓
compare compiler/source
        ↓
inspect IR diff
        ↓
inspect optimization remarks
        ↓
inspect assembly
        ↓
microbenchmark
        ↓
fix
        ↓
full benchmark
```

---

## 450.127 — Compiler bisect

Compiler regression có thể bisect compiler commits.

---

## 450.128 — Source bisect

Application regression có thể bisect source commits.

---

## 450.129 — Optimization pass bisect

Developer có thể disable pass để isolate regression.

---

## 450.130 — Reproducible optimization bug

Regression testcase phải có exact:

```text
source
compiler
target
flags
input
```

---

# 450.131 — Performance portability

Axiom không giả định optimization tốt trên một ISA sẽ tốt trên ISA khác.

---

## 450.132 — Backend-specific tuning

x86-64 và AArch64 có cost model riêng.

---

## 450.133 — WASM performance

WASM benchmark phải tách:

```text
Axiom code generation
WASM runtime
host environment
```

---

## 450.134 — Mobile performance

iOS/Android benchmark phải tách:

```text
CPU
thermal state
OS scheduling
```

---

# 450.135 — Energy

Optional mobile/embedded benchmark:

```text
energy
power
```

---

## 450.136 — Energy measurement

Không phải platform nào cũng cung cấp reliable measurement; result phải ghi measurement source.

---

# 450.137 — Startup minimality

Một chương trình console nhỏ không nên kéo:

```text
GUI
network
async runtime
filesystem
```

nếu không dùng.

---

## 450.138 — Runtime capability attribution

Startup/binary report phải show selected runtime capabilities.

---

## 450.139 — Runtime initialization graph

Có thể inspect:

```text
startup
→ allocator
→ TLS
→ runtime modules
→ main
```

---

## 450.140 — Runtime pruning

Unused runtime components phải bị loại bỏ khi static analysis cho phép.

---

# 450.141 — Benchmark security

Benchmark runner không được execute untrusted benchmark source trong privileged context mặc định.

---

## 450.142 — Benchmark isolation

Untrusted benchmarks có thể chạy sandbox/process isolation.

---

## 450.143 — Resource limits

Benchmark runner có thể giới hạn:

```text
CPU
memory
time
filesystem
network
```

---

# 450.144 — Benchmark schema stability

Machine-readable benchmark schema phải versioned.

---

## 450.145 — Result compatibility

Tool version mới vẫn phải đọc result schema cũ trong compatibility window nếu có thể.

---

## 450.146 — Human report

CLI có human-readable summary.

---

## 450.147 — Machine report

CLI có JSON/machine-readable output.

---

## 450.148 — CI integration

Exit code có thể signal:

```text
pass
fail
regression
invalid
```

---

## 450.149 — AI integration

AI agent có thể lấy:

```text
benchmark result
regression cause candidates
optimization diagnostics
artifact diff
```

---

# 450.150 — Hard invariants

1. Axiom phải có performance measurement framework.
2. Compile time được đo riêng.
3. Incremental compile time được đo riêng.
4. Runtime được đo riêng.
5. Latency được đo riêng.
6. Throughput được đo riêng.
7. Memory được đo riêng.
8. Allocation được đo riêng.
9. Binary size được đo riêng.
10. Startup được đo riêng.
11. Debug và stripped size được phân biệt.
12. Runtime contribution có thể được đo.
13. Static dependency contribution có thể được phân tích.
14. Dynamic dependency không được tính sai vào executable size.
15. Benchmark phải validate correctness trước khi chấp nhận performance result.
16. Input benchmark phải reproducible.
17. Compiler configuration phải được record.
18. Target phải được record.
19. Hardware environment phải được record khi relevant.
20. Benchmark variance phải được đo.
21. Outlier handling phải explicit.
22. Regression threshold phải configurable.
23. Baseline phải có identity.
24. Historical performance data có thể được giữ.
25. Compiler regression có thể bisect.
26. Source regression có thể bisect.
27. Optimization pass regression có thể isolate.
28. Benchmark workload version phải được xác định.
29. Cross-target results không được trộn lẫn.
30. CPU-specific baselines phải được phân biệt.
31. Microbenchmark không được coi là proof of overall performance.
32. Real-world workload phải tồn tại trong suite.
33. Binary-size budget có thể enforce.
34. Startup budget có thể enforce.
35. Memory budget có thể enforce.
36. Allocation budget có thể enforce.
37. `@no_alloc` có thể được kiểm chứng ở runtime/test tooling.
38. Performance metadata có thể tích hợp semantic metadata.
39. Optimization decisions có thể correlate với benchmark.
40. Assembly có thể được inspect.
41. Machine-level size diff có thể được inspect.
42. Function-level size diff có thể được inspect.
43. Optimization diff có thể được inspect.
44. PGO benchmark identity phải được record.
45. Performance result phải machine-readable.
46. Performance result phải human-readable.
47. CI có thể fail khi regression vượt threshold.
48. Build benchmark phân biệt cold/warm/incremental.
49. Harness overhead phải được xử lý rõ.
50. Startup benchmark có measurement boundary rõ.
51. Compiler benchmark có frontend/codegen/link metrics khi useful.
52. Parallel build scaling có thể được đo.
53. Benchmark system không tự tạo aggregate performance score.
54. Không có hidden weighting giữa speed/size/memory/compile time.
55. Tradeoff phải được report thay vì che giấu.
56. Hardware counters là optional.
57. Energy measurement là optional.
58. Benchmark security phải có isolation/resource limits khi cần.
59. AI tooling có thể query performance data.
60. AI tooling có thể query regression information.
61. Benchmark artifacts có thể được retained và compared.
62. Reproducibility là một phần của benchmark identity.
63. Performance result không được extrapolate giữa target mà không ghi rõ.
64. Axiom runtime overhead phải có thể phân biệt với library/application overhead.
65. **Axiom performance claims phải được chứng minh bằng reproducible measurements, không bằng một điểm số tổng hợp hay tuyên bố chung chung.**

**BOOTSTRAP-450 hoàn tất.**

---

# BOOTSTRAP-451 — FFI, C INTEROPERABILITY, NATIVE SDK, FOREIGN TYPES, CALLBACKS & ZERO-COST FOREIGN FUNCTION BOUNDARY

Task kế tiếp khóa **khả năng sống trong thế giới native hiện có**.

Axiom đã có:

```text
ABI
memory layout
calling convention
object format
linker
package system
```

Nhưng để thực sự thay thế/đứng cạnh C/C++, nó phải gọi được:

```text
OS APIs
C libraries
C-compatible SDKs
native dynamic libraries
callbacks
function pointers
foreign structs
foreign threads
```

mà không tạo một “FFI runtime” nặng.

Mục tiêu kiến trúc:

```text
Axiom
  │
  ├── native ABI
  │
  ├── C ABI
  │
  ├── platform ABI
  │
  └── custom foreign ABI
          ↓
      direct call
```

**Không có mandatory FFI VM, wrapper runtime hoặc C compiler trung gian.**

---

## 451.1 — FFI boundary

FFI là boundary giữa Axiom semantic model và foreign ABI.

---

## 451.2 — Explicit foreign declarations

Foreign function phải được khai báo explicit.

Conceptual:

```text
extern "c" fn printf(fmt: *const u8, ...) -> i32
```

---

## 451.3 — Foreign ABI

ABI phải explicit:

```text
extern "c"
extern "system"
extern "win64"
extern "sysv64"
```

hoặc target-specific equivalent.

---

## 451.4 — No implicit foreign ABI

Compiler không được đoán ABI từ function name.

---

## 451.5 — Foreign symbol name

Có thể khai báo:

```text
@link_name("printf")
```

---

## 451.6 — Name mangling

FFI exports/imports phải hỗ trợ no-mangle/stable native names.

---

## 451.7 — Foreign library declaration

Package có thể khai báo:

```text
requires native library X
```

---

## 451.8 — Static foreign library

Axiom linker consume archive/static library trực tiếp.

---

## 451.9 — Dynamic foreign library

Axiom executable có thể import dynamic library.

---

## 451.10 — Platform library

OS APIs được model như foreign ABI packages.

---

## 451.11 — C ABI

C ABI là interoperability target chính.

---

## 451.12 — C types

Mapping cơ bản:

```text
char
short
int
long
long long
float
double
void
pointer
```

phải target-aware vì kích thước một số C types phụ thuộc platform ABI.

---

## 451.13 — Fixed-width foreign types

Axiom nên ưu tiên wrappers:

```text
c_int
c_long
c_size_t
c_ssize_t
```

để tránh ambiguity.

---

## 451.14 — C struct

`@repr(C)` tạo layout tương thích với C ABI khi các field types cũng tương thích.

---

## 451.15 — C union

Foreign union phải có explicit representation.

---

## 451.16 — Bitfields

C bitfields không được giả định layout portable.

Importer phải target-specific.

---

## 451.17 — Packed C structs

Hỗ trợ explicit packed layout.

---

## 451.18 — Alignment

Foreign alignment phải match target ABI.

---

## 451.19 — Flexible array members

Có thể represent bằng explicit trailing storage/view abstraction.

---

## 451.20 — Opaque C types

C incomplete type được represent bằng opaque type.

---

## 451.21 — C enum

C enum phải được import theo ABI-relevant integer representation.

Không mặc định coi nó giống Axiom tagged enum.

---

## 451.22 — C strings

Axiom `String` không tự động tương đương `char*`.

---

## 451.23 — CString

`CString`/byte string API được dùng cho null-terminated strings.

---

## 451.24 — UTF-8 boundary

Foreign API không được mặc định assume UTF-8.

Encoding phải explicit.

---

## 451.25 — Raw pointer FFI

Foreign pointer được represent bằng raw pointer hoặc opaque handle.

---

## 451.26 — Ownership contract

FFI declaration có thể ghi:

```text
@owned
@borrowed
@consumes
@returns_owned
```

---

## 451.27 — Foreign allocation

Compiler không giả định foreign allocator tương thích với Axiom allocator.

---

## 451.28 — Foreign free

Foreign memory phải được release bằng đúng foreign deallocator.

---

## 451.29 — Allocator mismatch

`axiom_free()` trên memory từ `malloc()` là invalid nếu allocator contracts không tương thích.

---

## 451.30 — FFI safety

Foreign function mặc định là unsafe hoặc yêu cầu explicit safety contract nếu compiler không thể verify preconditions.

---

## 451.31 — Safe wrapper

Library có thể encapsulate unsafe FFI bằng safe API.

---

## 451.32 — FFI preconditions

Có thể khai báo:

```text
@safety(requires = "ptr != null")
```

---

## 451.33 — FFI postconditions

Có thể khai báo guarantees.

---

## 451.34 — FFI effects

Metadata:

```text
@allocates
@blocks
@panics
@io
```

có thể được khai báo.

---

## 451.35 — Unknown effects

Nếu không có contract, compiler dùng conservative assumptions.

---

## 451.36 — Variadic functions

C-style variadic functions được hỗ trợ tại ABI boundary.

---

## 451.37 — Variadic safety

Compiler không tự validate arbitrary C variadic type contracts.

---

## 451.38 — Typed variadic wrapper

Safe wrapper nên cung cấp typed interface.

---

## 451.39 — Function pointers

Foreign function pointers có explicit ABI type.

---

## 451.40 — Callback

Axiom function có thể được passed sang C callback nếu signature/ABI tương thích.

---

## 451.41 — Callback lifetime

Callback pointer không được sống lâu hơn code/environment mà nó trỏ tới.

---

## 451.42 — Capturing callback

Capturing closure cần stable environment lifetime.

Không được tự động pass closure có environment vào C API yêu cầu bare function pointer.

---

## 451.43 — Callback trampoline

Compiler/library có thể tạo trampoline:

```text
C callback
→ Axiom trampoline
→ closure environment
```

khi ABI mechanism hỗ trợ.

---

## 451.44 — Trampoline allocation

Trampoline/environment allocation phải explicit hoặc compiler-managed theo ABI/runtime capability.

---

## 451.45 — Callback thread

Foreign callback có thể chạy trên foreign-created thread.

---

## 451.46 — Thread attachment

Nếu runtime cần TLS/executor attachment, đây phải là explicit runtime boundary.

---

## 451.47 — Foreign thread safety

`Send`/`Share` contracts phải được xét khi callback crosses threads.

---

## 451.48 — Reentrancy

FFI callback có thể re-enter Axiom code.

Runtime phải hỗ trợ nếu API contract cho phép.

---

## 451.49 — Panic across FFI

Axiom panic không được tự động unwind qua C ABI.

---

## 451.50 — Panic boundary

Boundary phải:

```text
catch
convert
abort
```

tùy declared policy.

---

## 451.51 — Foreign exception

Foreign exception không được tự động trở thành Axiom `Result`.

---

## 451.52 — Foreign unwind

Nếu ABI hỗ trợ native unwind interop, phải explicit enable.

---

## 451.53 — Error-code APIs

C-style:

```text
return code
+ out parameter
```

có thể được wrapped thành:

```text
Result<T, E>
```

---

## 451.54 — `errno`

Platform error state có explicit wrapper.

---

## 451.55 — Windows error APIs

Win32-style error values được represent bằng target-specific types.

---

## 451.56 — Handle APIs

OS handles được represent như resource-owning types.

---

## 451.57 — Handle ownership

Wrapper có thể encode:

```text
owned handle
borrowed handle
invalid handle
```

---

## 451.58 — RAII-like cleanup

Axiom `drop` có thể close/release foreign resources deterministically.

---

## 451.59 — FFI destructor

Foreign cleanup function có thể được bound as destructor implementation.

---

## 451.60 — Foreign global variables

Foreign globals có explicit declaration.

---

## 451.61 — Thread-local foreign variables

TLS imports/exports phải target ABI compatible.

---

## 451.62 — Volatile foreign memory

MMIO/foreign shared state dùng explicit volatile operations.

---

## 451.63 — Atomic foreign memory

Atomic access chỉ được dùng khi foreign object alignment/atomicity contract phù hợp.

---

## 451.64 — Memory ordering

Foreign synchronization must be modeled explicitly.

---

## 451.65 — `repr(C)`

`@repr(C)` is layout contract, not safety guarantee.

---

## 451.66 — `repr(transparent)`

Axiom có thể hỗ trợ transparent wrappers:

```text
struct FileHandle(@repr(transparent) raw: usize)
```

để ABI-compatible wrapper.

---

## 451.67 — Transparent wrapper restriction

Transparent representation chỉ hợp lệ khi representation rules thỏa điều kiện compiler.

---

## 451.68 — Packed wrapper

Packed representation có thể gây unaligned accesses; access phải được xử lý đúng.

---

## 451.69 — Alignment diagnostics

Compiler phải reject invalid ABI alignment assumptions.

---

## 451.70 — ABI layout verification

Tool:

```text
axiom ffi-check
```

có thể verify:

```text
sizeof
alignof
offsetof
calling convention
symbol
```

---

## 451.71 — C header importer

Axiom ecosystem có thể có:

```text
axiom cimport header.h
```

tooling.

---

## 451.72 — C importer architecture

Importer:

```text
C header
 ↓
C parser
 ↓
ABI-aware semantic declarations
 ↓
Axiom FFI metadata
```

---

## 451.73 — C importer ≠ compiler core

C importer không phải dependency của Axiom compiler core.

---

## 451.74 — Generated bindings

Generated FFI declarations phải có provenance:

```text
header
version
target
generator
```

---

## 451.75 — Binding regeneration

Header/API changes phải invalidate generated bindings.

---

## 451.76 — SDK binding package

Platform bindings có thể được distributed as packages.

---

## 451.77 — Windows SDK

Windows APIs có thể được represented through generated Axiom bindings.

---

## 451.78 — POSIX APIs

POSIX declarations có thể được represented through ABI packages.

---

## 451.79 — Apple SDK

Apple frameworks can be exposed through FFI metadata/native dynamic frameworks.

---

## 451.80 — Android NDK

Android native APIs can be consumed through target-specific FFI packages.

---

## 451.81 — WASM imports

WASM foreign functions are explicit module imports.

---

## 451.82 — WASM host interface

Host functions phải có explicit import signatures.

---

## 451.83 — Native syscall

Raw syscall is unsafe and target-specific.

---

## 451.84 — Syscall wrappers

Standard library may expose typed safe wrappers.

---

## 451.85 — Inline assembly

Inline assembly là unsafe.

---

## 451.86 — Inline assembly syntax

Syntax phải có explicit:

```text
inputs
outputs
clobbers
memory effects
```

---

## 451.87 — Register constraints

Backend validates register constraints.

---

## 451.88 — ASM target restrictions

Inline asm phải target-specific.

---

## 451.89 — ASM optimizer barrier

Compiler must understand declared side effects/clobbers.

---

## 451.90 — ASM memory clobber

Memory clobber prevents invalid memory reordering.

---

## 451.91 — Native intrinsic

Compiler intrinsics có semantic definitions thay vì opaque assembly khi possible.

---

## 451.92 — SIMD FFI

Vector ABI phải match target ABI.

---

## 451.93 — Struct ABI verification

Foreign aggregate parameter/return classification phải dùng ABI engine 421.

---

## 451.94 — Hidden sret

Compiler tự generate hidden return storage khi foreign ABI yêu cầu.

---

## 451.95 — Variadic ABI

Backend phải implement platform-specific variadic rules.

---

## 451.96 — Long double

Platform-specific floating types phải có explicit representation.

---

## 451.97 — `size_t`

Mapping phải phụ thuộc target ABI.

---

## 451.98 — `wchar_t`

Không được assume universal size/encoding.

---

## 451.99 — C `bool`

Mapping phải theo target C ABI.

---

## 451.100 — C ABI compatibility test

Axiom phải có cross-compiled C fixtures để verify:

```text
call
return
struct
union
array
float
double
pointer
variadic
callback
```

---

# 451.101 — FFI golden tests

Mỗi supported ABI có golden tests.

---

## 451.102 — C compiler test fixture

C fixture chỉ được dùng để **validation interoperability**, không phải để compile production Axiom code.

---

## 451.103 — Third-party compiler boundary

Production build:

```text
Axiom source
→ Axiom compiler
→ Axiom object
→ Axiom linker
```

Validation có thể dùng external compiler để verify ABI expectations.

---

## 451.104 — Foreign binary testing

Axiom phải test gọi native libraries được build independently.

---

## 451.105 — Reverse direction

Foreign code phải có thể gọi Axiom exported C ABI functions.

---

## 451.106 — Exported Axiom library

Axiom có thể tạo:

```text
static library
dynamic library
```

cho C/native consumers.

---

## 451.107 — Stable export header

Tool có thể generate C-compatible declarations cho exported ABI.

---

## 451.108 — ABI documentation

Generated ABI docs có:

```text
function
symbol
parameters
returns
layout
ownership
threading
error behavior
```

---

## 451.109 — ABI ownership metadata

Generated declarations phải preserve ownership contracts where representable.

---

## 451.110 — Foreign symbol collision

Linker phải detect conflicting symbols according to object/link rules.

---

## 451.111 — Weak symbols

Backend có thể hỗ trợ weak symbols khi target object format hỗ trợ.

---

## 451.112 — TLS symbols

TLS import/export phải target-specific.

---

## 451.113 — Section attributes

FFI/native declarations có thể yêu cầu explicit linker sections khi supported.

---

## 451.114 — Calling convention attributes

Function declaration có thể override default calling convention.

---

## 451.115 — ABI mismatch diagnostic

Ví dụ conceptual:

```text
E451021
foreign function uses AAPCS64
current declaration uses SysV64
```

---

## 451.116 — Layout mismatch diagnostic

Compiler có thể báo:

```text
expected size: 24
declared size: 16
```

khi external metadata cung cấp expected layout.

---

## 451.117 — Symbol mismatch diagnostic

Missing/ambiguous native symbol phải có diagnostic.

---

## 451.118 — Library search

Package metadata controls native library search paths.

---

## 451.119 — No ambient linker magic

Compiler không âm thầm scan toàn hệ thống để tìm arbitrary library.

---

## 451.120 — Explicit native dependency

Native dependency phải xuất hiện trong package/build metadata.

---

## 451.121 — Link ordering

Native library ordering được build graph/linker kiểm soát.

---

## 451.122 — Static circular dependencies

Axiom linker phải hỗ trợ hoặc diagnostic rõ circular archive dependency patterns.

---

## 451.123 — Import/export visibility

Native exports phải explicit.

---

## 451.124 — Symbol visibility

Internal symbols có thể hidden để giảm collision/binary surface.

---

## 451.125 — FFI security boundary

Foreign calls là trust boundary.

---

## 451.126 — Safe wrapper trust

Safe wrapper phải enforce foreign API preconditions.

---

## 451.127 — Unsafe inventory

Tooling có thể list:

```text
all FFI declarations
all unsafe calls
all raw pointer boundaries
```

---

## 451.128 — AI FFI query

AI có thể hỏi:

```text
what does this foreign function own?
what ABI does it use?
can it block?
can it allocate?
can it panic?
```

---

## 451.129 — FFI semantic metadata

FFI declarations phải integrate với metadata system 446.

---

## 451.130 — FFI package metadata

Package metadata có:

```text
native libraries
target constraints
ABI
headers/source provenance
```

---

# 451.131 — FFI zero-cost principle

Một foreign function call trực tiếp phải compile thành native call tương ứng, không qua generic runtime dispatch nếu ABI không yêu cầu.

---

## 451.132 — Wrapper elimination

Thin Axiom wrapper quanh FFI call có thể inline hoàn toàn.

---

## 451.133 — Type conversion elimination

Transparent/representation-compatible wrappers có thể được erase.

---

## 451.134 — Handle wrapper elimination

Opaque handle wrapper không được tạo runtime object chỉ vì type safety.

---

## 451.135 — Error wrapper optimization

C error-code → `Result` wrapper có thể compile thành:

```text
call
test code
branch
```

không allocation.

---

## 451.136 — Callback overhead

Callback trampoline chỉ tồn tại khi ABI yêu cầu.

---

## 451.137 — FFI allocation rule

FFI boundary không tự động allocate.

---

## 451.138 — FFI exception rule

FFI boundary không tự động tạo exception object.

---

## 451.139 — FFI thread rule

FFI call không tự động tạo thread.

---

## 451.140 — FFI async rule

Blocking foreign function không tự động trở thành async function.

---

# 451.141 — FFI and async

Blocking C API có thể được wrapped bằng explicit thread-pool/executor strategy.

---

## 451.142 — FFI cancellation

Cancellation không được giả định foreign API hỗ trợ nếu API không có cancellation mechanism.

---

## 451.143 — FFI timeout

Timeout wrapper phải explicit.

---

## 451.144 — FFI resource cleanup

Foreign resources phải có deterministic cleanup khi wrapper owns them.

---

## 451.145 — FFI partial initialization

Foreign structures with initialization phases phải được model bằng explicit states/types khi cần.

---

## 451.146 — FFI nullable pointer

Nullable foreign pointer được represent:

```text
Option<*mut T>
```

hoặc dedicated nullable raw pointer abstraction theo ABI.

---

## 451.147 — No implicit null conversion

`null` không tự biến thành safe Axiom reference.

---

## 451.148 — Foreign callback lifetime

Compiler/library phải hỗ trợ explicit lifetime ownership contract, nhưng không yêu cầu Rust-style lifetime annotation cho mọi FFI API.

---

## 451.149 — FFI documentation generation

Tool có thể generate:

```text
C header
ABI manifest
documentation
```

từ Axiom declarations.

---

# 451.150 — Hard invariants

1. FFI là explicit language/toolchain boundary.
2. Foreign ABI phải explicit.
3. C ABI là first-class.
4. Axiom có thể import native functions.
5. Axiom có thể export native functions.
6. Static native libraries được hỗ trợ.
7. Dynamic native libraries được hỗ trợ.
8. Platform SDKs có thể được modeled bằng FFI packages.
9. Axiom không cần C compiler để compile Axiom production code.
10. C compiler chỉ có thể được dùng trong interoperability validation/tooling.
11. `@repr(C)` là layout contract.
12. `@repr(C)` không phải safety guarantee.
13. Foreign structs phải ABI-aware.
14. Foreign unions phải ABI-aware.
15. C enums không được tự động coi là Axiom tagged enums.
16. C integer types phải target-aware.
17. `size_t` phải target-aware.
18. `long` phải target-aware.
19. Foreign strings không mặc định UTF-8.
20. `String` không tự động tương đương `char*`.
21. CString/byte-string boundary phải explicit.
22. Foreign pointer được model bằng explicit pointer/handle.
23. Foreign allocation phải có ownership contract.
24. Axiom allocator không được tự động free foreign memory.
25. Foreign deallocator phải match allocator.
26. FFI functions không có verified contracts phải được xử lý conservative.
27. Safe wrappers có thể encapsulate unsafe FFI.
28. FFI preconditions/postconditions có thể machine-readable.
29. FFI effects có thể machine-readable.
30. Variadic functions được hỗ trợ ở ABI boundary.
31. Function pointers có ABI identity.
32. Callbacks được hỗ trợ.
33. Capturing closure không tự động tương đương bare C function pointer.
34. Callback environment lifetime phải được bảo đảm.
35. Callback trên foreign thread phải được hỗ trợ theo explicit runtime contract.
36. Reentrancy phải được xử lý rõ.
37. Panic không tự động unwind qua C ABI.
38. Foreign exception không tự động trở thành Result.
39. Foreign unwind phải explicit.
40. Error-code APIs có thể wrap thành Result.
41. OS handles có thể trở thành deterministic resource-owning types.
42. Foreign globals được hỗ trợ.
43. Foreign TLS được hỗ trợ.
44. Volatile foreign memory được hỗ trợ.
45. Foreign atomic memory phải respect alignment/atomicity contracts.
46. Inline assembly là unsafe.
47. Inline assembly phải khai báo inputs/outputs/clobbers/effects.
48. Native intrinsics được ưu tiên khi có semantic model.
49. FFI ABI verification tooling được hỗ trợ.
50. C header importer có thể tồn tại ngoài compiler core.
51. Generated bindings phải có provenance.
52. SDK bindings có thể phân phối như package.
53. Windows/POSIX/Apple/Android/WASM native interfaces đều có thể dùng chung FFI architecture.
54. Native library search phải explicit.
55. Ambient arbitrary linker discovery bị tránh.
56. Native dependencies phải xuất hiện trong build metadata.
57. Link ordering phải deterministic.
58. Symbol visibility phải kiểm soát được.
59. ABI mismatch phải có diagnostic.
60. Layout mismatch phải có diagnostic khi expected metadata available.
61. FFI metadata tích hợp semantic metadata 446.
62. AI có thể query FFI ownership/effects/ABI.
63. Thin FFI wrappers có thể inline.
64. Representation-compatible wrappers có thể bị erase.
65. FFI error wrappers có thể zero-allocation.
66. FFI call không tự tạo runtime dispatch.
67. FFI call không tự allocate.
68. FFI call không tự tạo thread.
69. FFI call không tự trở thành async.
70. Blocking foreign APIs phải được wrap explicit nếu muốn async.
71. FFI cancellation không được giả định.
72. FFI timeout không được implicit.
73. FFI resources phải cleanup deterministic nếu owned.
74. Nullable foreign pointers không được biến thành nullable safe references.
75. FFI exported API có thể generate C declarations.
76. Exported ABI có thể tạo static library.
77. Exported ABI có thể tạo dynamic library.
78. ABI documentation có thể generate tự động.
79. FFI security boundary phải được machine-readable.
80. **Axiom phải có khả năng gọi và được gọi bởi thế giới native hiện hữu với overhead tối thiểu, trong khi ownership, ABI, layout, lifetime và safety boundary vẫn được thể hiện rõ ràng trong semantic model.**

**BOOTSTRAP-451 hoàn tất.**

---

# BOOTSTRAP-452 — GUI, EVENT LOOP, WINDOWING, INPUT, RENDERING ABSTRACTION & NATIVE UI BOUNDARY

Task tiếp theo sẽ khóa **GUI architecture của Axiom**.

Điểm quan trọng: GUI **không được đưa vào core language/runtime bắt buộc**. Nó phải là một tầng library/platform có thể xây được hoàn toàn bằng Axiom:

```text
Axiom Core
    ↓
Standard Library
    ↓
Platform Window/Event API
    ↓
GUI Toolkit
    ↓
Renderer
```

Architecture sẽ phải giải quyết đồng thời:

```text
Windows
Linux
macOS
iOS
Android
WASM/Web
```

và phân biệt rõ:

```text
native widget UI
custom-rendered UI
GPU rendering
event loop
async
input
accessibility
text/layout
```

để sau này Axiom có thể xây **GUI kiểu WPF nhưng native/Axiom-first**, mà không biến GUI framework thành một phần bắt buộc của compiler/runtime.