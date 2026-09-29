# BOOTSTRAP-403 — Testing, Verification, Debugging, Profiling & Diagnostics

Sau `402`, bước tiếp theo nên khóa **quality/observability model của Axiom**.

Một ngôn ngữ hệ thống hiệu năng cao nhưng không có testing, verifier, debugger và profiler được thiết kế cùng compiler sẽ rất khó đạt mục tiêu thực tế. Đặc biệt Axiom đã có ownership, capability, concurrency, GPU, async, comptime và build graph; tất cả cần được quan sát và kiểm chứng thống nhất.

Mục tiêu:

> **Một chương trình Axiom phải có thể được kiểm tra từ source → semantic model → MIR → machine code → runtime behavior, với cùng một hệ thống identity và provenance.**

---

## 1. Ba tầng kiểm chứng

Axiom phân biệt rõ:

```text
Static Verification
        │
        ▼
Compile-time Validation
        │
        ▼
Runtime Verification
```

### Static Verification

Compiler chứng minh được:

- type correctness
- ownership
- capability
- lifetime
- alias
- data race
- effect
- pattern exhaustiveness
- ABI
- GPU legality

### Compile-time Validation

Ví dụ:

```axiom
assert comptime size_of::<Header>() == 64
```

### Runtime Verification

Dùng khi property phụ thuộc dữ liệu runtime:

```text
bounds
protocol state
external input
FFI contracts
dynamic invariants
```

---

# 2. Test không phải một cơ chế riêng biệt

Axiom test engine phải dùng chung:

```text
CompilerDB
BuildGraph
Comptime
Runtime
Diagnostics
Coverage
Profiler
```

Một test cũng là một BuildGraph node.

```text
source
   ↓
compile
   ↓
test executable
   ↓
run
   ↓
test result
```

---

# 3. Test function

Cú pháp cơ bản:

```axiom
@test
fn test_add() {
    assert(add(2, 3) == 5)
}
```

Compiler nhận biết `@test`.

Không cần runtime test framework bắt buộc.

---

# 4. Test assertion

Core:

```axiom
assert(condition)
```

Có thể có:

```axiom
assert_eq(a, b)
assert_ne(a, b)
assert_true(x)
assert_false(x)
```

Nhưng các hàm này nên thuộc test library/compiler intrinsic, không cần nhúng nhiều runtime vào executable release.

---

# 5. Test executable

Compiler tạo test binary:

```text
my_project.tests.exe
```

Test runner chịu trách nhiệm:

```text
discover
schedule
run
capture
report
```

Release binary không chứa test machinery.

---

# 6. Test isolation

Test mặc định phải có isolation semantics rõ ràng.

Test có thể:

```text
pure
filesystem
network
GPU
thread
process
```

Compiler/runner biết capability mà test yêu cầu.

Ví dụ:

```axiom
@test(requires = [filesystem])
```

---

# 7. Parallel tests

Các test độc lập có thể chạy song song.

Nhưng:

```text
test A
test B
```

không được phụ thuộc execution order trừ khi dependency được khai báo.

Test runner phải phát hiện:

```text
shared mutable global
filesystem collision
port collision
resource conflict
```

hoặc yêu cầu isolation.

---

# 8. Property testing

Axiom nên hỗ trợ property test ở library/tooling layer:

```axiom
@property_test
fn reverse_twice(x: Array<i32>) {
    assert(reverse(reverse(x)) == x)
}
```

Generator:

```text
Generator<T>
```

Shrinker:

```text
Shrinker<T>
```

Compiler không cần biết toàn bộ thuật toán property testing.

---

# 9. Fuzz testing

Fuzz là một execution mode:

```text
axiom fuzz
```

Input:

```text
bytes
structured values
protocol packets
images
files
```

Fuzzer có thể dùng:

```text
coverage feedback
mutation
generation
corpus
minimization
```

---

# 10. Deterministic replay

Đặc biệt quan trọng với concurrency/network/GPU.

Test run có:

```text
RunSeed
ExecutionTrace
InputSnapshot
Configuration
```

Một failure phải có khả năng:

```text
record
→ replay
```

trong deterministic profile khi backend cho phép.

---

# 11. Snapshot testing

Output có thể được snapshot:

```text
@test_snapshot
fn render_scene() -> Image
```

Snapshot phải có canonicalization policy.

Không được để:

```text
timestamp
pointer address
random UUID
thread ID
```

làm snapshot thay đổi vô nghĩa.

---

# 12. Golden tests

Compiler cần đặc biệt hỗ trợ golden tests:

```text
source
→ AST
→ HIR
→ MIR
→ diagnostics
→ machine output
```

Ví dụ compiler test:

```text
tests/
    parser/
    resolver/
    typecheck/
    ownership/
    mir/
    codegen/
    linker/
```

---

# 13. Compiler semantic tests

Axiom compiler phải test từng semantic invariant.

Ví dụ:

```text
move_then_use.ax
```

expected:

```text
EOWN-...
use of moved value
```

Không chỉ kiểm tra “compiler fail”.

Phải kiểm tra:

```text
diagnostic identity
source span
error category
suggested fix
```

---

# 14. Compile-fail tests

Ví dụ:

```axiom
fn f() {
    let a = Resource()
    let b = a
    use(a)
}
```

Expected:

```text
error: use of moved value `a`
```

Test harness phải xác nhận compiler phát hiện đúng lỗi.

---

# 15. Diagnostic architecture

Diagnostic không chỉ là string.

Định nghĩa:

```text
Diagnostic {
    code
    severity
    message
    primary_span
    secondary_spans
    notes
    help
    suggestions
    provenance
}
```

Ví dụ:

```text
EOWN-001
```

thay vì:

```text
"something went wrong"
```

---

# 16. Diagnostic severity

Core:

```text
error
warning
note
help
```

Compiler internal:

```text
ICE
```

ICE = Internal Compiler Error.

ICE phải khác semantic error.

---

# 17. Stable diagnostic codes

Diagnostic code phải stable theo semantic category.

Ví dụ:

```text
E001
```

không đủ tốt.

Nên:

```text
EOWN-001
ETYPE-014
EASYNC-003
EGPU-007
EABI-002
```

AI agent có thể dựa vào code để sửa lỗi chính xác hơn.

---

# 18. Machine-readable diagnostics

Ngoài human output:

```text
axiom check
```

có thể:

```text
--format=json
```

Output:

```text
{
    code,
    severity,
    file,
    span,
    message,
    suggestions
}
```

IDE và AI agent không phải parse text.

---

# 19. Structured fix-it

Compiler có thể cung cấp edit:

```text
replace:
    source span X
with:
    "mut_view(x)"
```

Nhưng compiler chỉ đưa suggestion nếu transformation được chứng minh an toàn.

Không tự động sửa semantic code mơ hồ.

---

# 20. Source provenance

Mọi diagnostic phải có provenance:

```text
Source
→ GeneratedSource
→ Macro/comptime
→ HIR
→ MIR
```

Nếu lỗi nằm trong generated code:

```text
generated by:
schema_codegen
input:
schema.json
```

IDE có thể quay về source generator.

---

# 21. Debug information

Axiom cần một debug model thống nhất:

```text
Source
 ↕
AST
 ↕
HIR
 ↕
MIR
 ↕
LIR
 ↕
Machine
```

Debugger không chỉ biết:

```text
machine address → source line
```

mà compiler có thể biết:

```text
machine location
→ MIR value
→ source variable
→ source expression
```

---

# 22. Debug build

Debug profile có thể giữ:

```text
variable locations
type metadata
inline mappings
source mappings
async state
closure state
```

Release profile có thể strip phần lớn metadata.

---

# 23. Optimized debugging

Axiom không nên yêu cầu:

```text
-O0
```

mới debug được.

Compiler nên hỗ trợ:

```text
optimized + debug information
```

với trạng thái:

```text
optimized_out
merged
inlined
split
materialized
```

Debugger phải phản ánh sự thật thay vì giả vờ mọi source variable luôn tồn tại.

---

# 24. Breakpoint model

Breakpoint có thể đặt tại:

```text
source line
function
expression
MIR location
machine address
```

Ví dụ:

```text
break foo
break file.ax:42
```

Compiler cung cấp mapping tương ứng.

---

# 25. Async debugging

Async function không được debug như function stack bình thường.

Debugger cần hiểu:

```text
Future
Task
State
SuspensionPoint
Wake
Resume
```

Có thể hiển thị:

```text
Task #42
  Future: download()
  State: AwaitSocket
  Suspended at: foo.ax:83
```

---

# 26. Coroutine state

Compiler tạo metadata:

```text
AsyncDebugInfo {
    future
    state
    suspension_points
    live_values
}
```

Metadata có thể bị strip khỏi release.

---

# 27. Thread debugging

Debugger phải biết:

```text
Thread
Task
Executor
Lock
Mutex
Channel
Atomic
```

Nếu task đang chờ mutex, debugger có thể biểu diễn dependency:

```text
Task A
  waiting Mutex M

Task B
  owns Mutex M
```

---

# 28. Race diagnostics

Axiom safe code vốn phải ngăn data race.

Nhưng unsafe/FFI có thể phá assumption.

Runtime race instrumentation có thể cung cấp:

```text
ThreadSanitizer-like mode
```

nhưng được tích hợp với Axiom semantic model.

Compiler biết:

```text
MemoryRegion
Capability
Atomic
Synchronization
```

thay vì chỉ instrument raw addresses.

---

# 29. Sanitizer architecture

Không nên hard-code một sanitizer.

Define:

```text
Sanitizer
```

và backend:

```text
Address
Bounds
UseAfterFree
Thread
Integer
Float
UndefinedBehavior
MemoryInit
FFI
```

Không phải sanitizer nào cũng áp dụng cho mọi target.

---

# 30. Sanitizer không thay thế safety

Ví dụ:

```text
safe Axiom
```

không cần AddressSanitizer để chứng minh ownership.

Sanitizer dùng cho:

- unsafe
- FFI
- compiler bugs
- runtime assumptions
- testing.

---

# 31. Coverage

Coverage layer:

```text
source coverage
branch coverage
function coverage
MIR coverage
```

Compiler instrumentation phải được sinh từ semantic graph.

Không nên chỉ dùng text line instrumentation.

---

# 32. Profiling

Axiom cần profiling API/toolchain thống nhất:

```text
CPU
Memory
Allocation
Lock
Async
I/O
GPU
Network
```

Compiler có thể sinh instrumentation.

---

# 33. Sampling profiler

Release executable nên hỗ trợ profiling mà không cần recompilation trong nhiều trường hợp.

Compiler phải giữ đủ:

```text
symbol
inline
source
machine mapping
```

nếu debug/profiling metadata được phát hành.

---

# 34. Instrumentation profiler

Khi cần chi tiết hơn:

```text
@profile
fn process(...)
```

Compiler chèn instrumentation.

Có thể:

```text
@profile(category = "parser")
```

Nhưng instrumentation phải có overhead rõ ràng.

---

# 35. Allocation profiler

Vì Axiom nhấn mạnh performance, allocator event cần có metadata:

```text
allocation size
alignment
allocation site
deallocation site
lifetime
storage strategy
```

Compiler có thể phát hiện:

```text
allocation hot spot
short-lived allocation
unnecessary allocation
```

---

# 36. Memory lifetime profiling

Compiler đã có lifetime analysis.

Do đó profiler có thể kết hợp:

```text
semantic lifetime
+
physical allocation lifetime
```

Ví dụ:

```text
Buffer<T>
semantic lifetime: 2 ms
physical heap lifetime: 2 ms
```

hoặc:

```text
semantic object
→ scalarized
→ no physical allocation
```

Đây là lợi thế lớn của Axiom.

---

# 37. Performance diagnostics

Compiler có thể đưa warning:

```text
WPERF-001:
allocation inside hot loop
```

hoặc:

```text
WPERF-002:
view prevents buffer relocation
```

hoặc:

```text
WPERF-003:
dynamic dispatch prevents specialization
```

Nhưng **không được biến mọi optimization heuristic thành warning mặc định**.

---

# 38. Optimization remarks

Compiler có thể xuất:

```text
optimization report
```

Ví dụ:

```text
loop vectorized
loop not vectorized: possible alias
function inlined
allocation eliminated
constant folded
kernel fused
```

AI agent có thể đọc report machine-readable.

---

# 39. Compiler Explorer mode

Axiom nên có command:

```text
axiom emit
```

cho phép:

```text
AST
HIR
Typed HIR
MIR
LIR
assembly
object
```

Ví dụ:

```text
axiom emit --mir foo.ax
axiom emit --asm foo.ax
```

Đây là công cụ cực kỳ quan trọng cho compiler development và performance work.

---

# 40. Semantic explanation

Một tính năng đặc biệt nên có:

```text
axiom explain
```

Ví dụ:

```text
axiom explain ownership foo.ax:42
```

Compiler có thể trả:

```text
value `x`
owner: local x
moved into: y
read attempted at: line 42
```

Hoặc:

```text
axiom explain race foo.ax:82
```

cho biết:

```text
WRITE region R
READ region R
no happens-before relation
```

Đây chính là điểm Axiom có thể **AI-friendly hơn C/C++ rất nhiều**.

---

# 41. Compiler verification trace

Compiler có thể xuất semantic trace:

```text
OwnershipProof
CapabilityProof
EffectProof
RaceProof
AbiProof
```

Không nhất thiết expose toàn bộ mặc định.

Chỉ khi:

```text
--explain
--verify
--debug-compiler
```

---

# 42. Test result model

Test result không phải string.

```text
TestResult {
    test_id
    status
    duration
    stdout
    stderr
    diagnostics
    coverage
    artifacts
    seed
    trace
}
```

Status:

```text
passed
failed
skipped
ignored
timeout
crashed
cancelled
```

---

# 43. Crash diagnostics

Nếu executable crash:

```text
signal/exception
stack
thread
task
registers
memory context
source mapping
```

được gom thành crash report.

Không cần runtime khổng lồ để làm điều này; debugger/crash reporter là tooling ngoài chương trình.

---

# 44. Panic/trap

Core đã có panic/trap profile.

Tooling phải hiểu cả hai.

Ví dụ:

```text
panic
→ source location
→ stack
→ task/thread
```

Freestanding:

```text
trap
→ machine exception
```

Debugger vẫn có thể map về source.

---

# 45. Benchmark

Benchmark là test category riêng:

```axiom
@benchmark
fn matrix_mul() { ... }
```

Runner thu:

```text
wall time
CPU time
iterations
allocation
memory
cache/perf counters nếu target hỗ trợ
```

Không nên chỉ đo một lần.

---

# 46. Benchmark correctness

Benchmark function phải được compiler ngăn dead-code elimination làm sai kết quả.

Ví dụ API:

```text
black_box(value)
```

Compiler intrinsic.

Nó có semantic contract phù hợp benchmark.

---

# 47. Benchmark reproducibility

Benchmark report phải lưu:

```text
compiler
target
CPU
features
profile
source fingerprint
dependency fingerprint
dataset
iterations
warmup
```

Không tuyên bố performance giữa hai máy khác nhau là trực tiếp tương đương.

---

# 48. CompilerDB bổ sung

```text
TestDB
TestCaseDB
TestResultDB
TestDependencyDB
TestIsolationDB
PropertyTestDB
FuzzTestDB
FuzzCorpusDB
ReplayDB
SnapshotDB
GoldenTestDB

DiagnosticDB
DiagnosticCodeDB
DiagnosticSpanDB
DiagnosticSuggestionDB
DiagnosticProvenanceDB

DebugInfoDB
SourceMapDB
VariableLocationDB
AsyncDebugDB
ThreadDebugDB

SanitizerDB
InstrumentationDB
CoverageDB

ProfilerDB
ProfileSessionDB
ProfileEventDB
AllocationProfileDB
PerformanceDiagnosticDB
OptimizationRemarkDB

BenchmarkDB
BenchmarkResultDB

CrashReportDB
VerificationTraceDB
CompilerExplanationDB
```

---

# 49. MIR/Tooling IR

Không nên tạo một runtime debug IR hoàn toàn tách biệt.

MIR giữ semantic identity:

```text
ValueId
BlockId
RegionId
CapabilityId
TaskId
EffectId
```

Tooling metadata map chúng sang:

```text
source
machine
runtime event
```

Do đó:

```text
source → MIR → machine → profiler
```

vẫn giữ được identity.

---

# 50. Verification pipeline

Toàn bộ compiler/tooling architecture:

```text
Source
  │
  ▼
AST
  │
  ▼
HIR
  │
  ▼
Typed HIR
  │
  ├── ownership proof
  ├── capability proof
  ├── effect proof
  ├── concurrency proof
  ├── ABI proof
  └── GPU proof
  │
  ▼
MIR
  │
  ├── optimization
  ├── instrumentation
  ├── sanitizer
  └── debug mapping
  │
  ▼
LIR
  │
  ▼
Machine
  │
  ├── debugger
  ├── profiler
  ├── coverage
  └── crash mapping
```

Điểm quan trọng:

> **Testing, debugging và profiling không được phá semantic model của compiler.**

Chúng chỉ quan sát hoặc instrument model đó.

---

# 51. Invariants — ATEST-01 → ATEST-30

**ATEST-01** — Test case phải có identity deterministic.

**ATEST-02** — Test dependency phải được biểu diễn trong BuildGraph.

**ATEST-03** — Test isolation phải được xác định rõ.

**ATEST-04** — Parallel test execution không được thay đổi semantic result.

**ATEST-05** — Test cancellation không được corrupt artifact/cache.

**ATEST-06** — Property test generator phải có reproducible seed khi deterministic mode bật.

**ATEST-07** — Fuzz failure phải có replayable input khi backend hỗ trợ.

**ATEST-08** — Snapshot test phải canonicalize nondeterministic data theo policy.

**ATEST-09** — Compile-fail test phải kiểm tra semantic diagnostic identity.

**ATEST-10** — Golden test phải xác định rõ compiler representation đang được kiểm tra.

**ATEST-11** — Diagnostic phải có stable code.

**ATEST-12** — Diagnostic span phải map được về source hoặc provenance.

**ATEST-13** — Compiler error và ICE phải phân biệt.

**ATEST-14** — Machine-readable diagnostic không được mất semantic information so với human diagnostic.

**ATEST-15** — Suggested fix không được được đánh dấu safe nếu compiler không chứng minh transformation hợp lệ.

**ATEST-16** — Debug mapping không được giả mạo biến đã bị optimize away.

**ATEST-17** — Async debug state phải map được suspension point về source.

**ATEST-18** — Thread/task identity phải phân biệt.

**ATEST-19** — Sanitizer instrumentation không được thay đổi program semantics ngoài behavior được khai báo.

**ATEST-20** — Sanitizer không thay thế static safety verification.

**ATEST-21** — Coverage phải map từ executed artifact về semantic/source identity.

**ATEST-22** — Optimization remarks phải phản ánh transformation thực tế.

**ATEST-23** — Profiler event phải có timestamp/order semantics được định nghĩa.

**ATEST-24** — Allocation profiling phải phân biệt semantic allocation với physical allocation.

**ATEST-25** — Benchmark phải chống dead-code elimination theo contract.

**ATEST-26** — Benchmark result phải chứa environment metadata cần thiết để diễn giải.

**ATEST-27** — Crash report phải giữ source/machine provenance khi metadata tồn tại.

**ATEST-28** — Verification trace phải tham chiếu proof identity hợp lệ.

**ATEST-29** — `axiom explain` không được tự tạo một semantic interpretation khác với compiler.

**ATEST-30** — Mọi tooling observation phải dựa trên cùng semantic identity model với compiler.

---

## Kết quả kiến trúc của BOOTSTRAP-403

Sau task này, Axiom có một nguyên tắc rất mạnh:

```text
                 ┌───────────────┐
                 │  Source Code  │
                 └───────┬───────┘
                         │
                    CompilerDB
                         │
             ┌───────────┴───────────┐
             │                       │
        Verification              Build
             │                       │
             ▼                       ▼
          Proofs                  Artifact
             │                       │
             └───────────┬───────────┘
                         │
                        MIR
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Debug       Profile     Test
             │           │           │
             └───────────┼───────────┘
                         ▼
                   Machine Code
```

Điểm khác biệt quan trọng so với nhiều toolchain truyền thống là **compiler không chỉ tạo machine code**. Nó tạo một **semantic knowledge graph** đủ để compiler, debugger, profiler, test runner, IDE và AI agent cùng hiểu một chương trình theo cùng một mô hình.