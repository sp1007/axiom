# BOOTSTRAP-477 — SOURCE MAP, CODE COVERAGE, TEST COVERAGE & QUALITY ANALYSIS FOUNDATION

**Trạng thái: COMPLETED / LOCKED**

477 khóa hệ thống coverage và provenance giữa **source → compiler → executable → test/fuzz/profile → source**.

Nguyên tắc:

```text id="x5n1aa"
Uncovered
    ≠ Dead
    ≠ Unreachable
    ≠ Untestable
```

và:

```text id="q0f8zr"
High Coverage
    ≠
Correct Program
```

Coverage là **execution evidence**, không phải quality score.

---

## 477.1 — Coverage model

Axiom hỗ trợ:

```text
Function
Statement
Region
Branch
Condition
Line
```

Các loại coverage có thể được bật độc lập.

---

## 477.2 — Function coverage

Ghi nhận function đã được execute hay chưa.

Không coi function được gọi là đã kiểm thử đúng.

---

## 477.3 — Statement coverage

Map execution counter tới source statement.

---

## 477.4 — Region coverage

Một region là đoạn source có execution semantics tương đối đồng nhất.

Phù hợp hơn line coverage với compiler optimization.

---

## 477.5 — Branch coverage

Mỗi CFG branch có thể có counter riêng:

```text id="c5q2h7"
true
false
```

---

## 477.6 — Condition coverage

Với:

```text
if A && B
```

có thể track evaluation của `A`, `B` riêng biệt.

---

## 477.7 — Line coverage

Line coverage là presentation layer.

Không dùng line number làm identity của coverage node.

---

# 477.8 — Stable coverage identity

Coverage node phải có identity ổn định dựa trên:

```text id="k8a0s2"
FileId
FunctionId
semantic/source region
build identity
```

Line number chỉ là mapping.

---

## 477.9 — CFG integration

435/436 CFG cung cấp branch identity.

Coverage instrumentation nên được gắn ở MIR/low-level IR thay vì lexer/parser.

---

## 477.10 — Optimization

Coverage phải hoạt động với:

- inlining;
- dead-code elimination;
- constant folding;
- loop optimization;
- tail calls;
- vectorization.

---

# 477.11 — Inlining-aware coverage

Nếu `foo()` được inline vào `bar()`, coverage phải phân biệt:

```text id="v5w6ac"
foo [inlined]
bar
```

không làm mất provenance.

---

## 477.12 — Dead-code distinction

Compiler phải phân biệt:

```text id="h6e0t9"
never executed
```

với:

```text
provably unreachable
```

---

## 477.13 — Constant-folded branch

Nếu compiler chứng minh branch luôn true:

```text id="n5d0qd"
if comptime_condition
```

branch đã bị loại bỏ không được báo như runtime-uncovered branch.

---

# 477.14 — Generated code

Comptime/derive/code generation có thể tạo source/IR.

Coverage phải lưu provenance:

```text id="8c8m0k"
generated item
← generator
← originating source
```

---

## 477.15 — Comptime coverage

Compile-time execution có coverage riêng nếu cần.

Không trộn compile-time coverage với runtime coverage.

---

## 477.16 — Async coverage

Async state machine phải map ngược về:

```text id="z0d4fk"
async source
→ await
→ generated state
```

---

## 477.17 — Match coverage

Coverage có thể track từng `match` arm.

---

## 477.18 — Error-path coverage

Có thể track:

```text id="w7k6za"
Ok path
Err path
Some path
None path
panic path
```

---

# 477.19 — Unsafe coverage

445 unsafe blocks/sites có thể có coverage identity.

AI tooling có thể query:

```text id="x1f9bp"
unsafe site
→ covered?
→ tests?
→ execution count
```

---

## 477.20 — FFI coverage

451 FFI boundary có thể được instrument:

```text id="7u4b2m"
Axiom → foreign
foreign → Axiom
```

---

## 477.21 — Concurrency coverage

Coverage có thể ghi:

```text id="3l0w1e"
thread path
task path
actor path
message path
```

nhưng không tuyên bố rằng mọi interleaving đã được kiểm thử.

---

# 477.22 — GUI coverage

452 có thể track:

```text id="4q7w0m"
event
handler
control action
accessibility action
```

---

## 477.23 — Media coverage

461/462 có thể track pipeline nodes:

```text id="c7f2a8"
decode
filter
resample
render
encode
```

---

# 477.24 — GPU coverage

459/460 có thể track kernel dispatch và execution.

GPU coverage phụ thuộc platform/device instrumentation.

---

# 477.25 — Coverage counters

Counter có thể là:

```text id="3s5m8v"
u32
u64
atomic counter
sampling counter
```

---

## 477.26 — Counter overflow

Coverage counters phải có defined overflow behavior.

Wraparound không được tạo false “never executed” semantics.

---

# 477.27 — Thread safety

Concurrent instrumentation phải sử dụng thread-safe collection hoặc per-thread counters.

---

## 477.28 — Per-thread counters

Per-thread counters có thể giảm contention và merge sau test.

---

# 477.29 — Fork/process

Nếu application tạo child processes, coverage provenance phải phân biệt process.

---

## 477.30 — Test process

Test runner có thể merge coverage từ nhiều test processes.

---

# 477.31 — Coverage merge

Merge phải giữ:

```text id="g4jv9x"
test run
target
build identity
source identity
```

---

# 477.32 — Deterministic coverage

Với cùng deterministic test execution, logical coverage set phải giống nhau.

Execution counts có thể khác nếu concurrency/timing không deterministic.

---

## 477.33 — Coverage artifact

Concept:

```text id="t2k9qf"
CoverageArtifact {
    format_version
    build_id
    target
    files
    functions
    regions
    branches
    counters
    provenance
}
```

---

# 477.34 — Source mapping

Coverage phải map được:

```text id="4e7j2c"
machine counter
→ IR block
→ semantic node
→ source span
```

---

## 477.35 — Source changes

Khi source thay đổi, coverage identity phải được invalidated/recomputed theo semantic/build fingerprint.

---

## 477.36 — Incremental coverage

Không được reuse coverage cũ nếu region semantics đã thay đổi.

---

# 477.37 — Baseline

Có thể so sánh:

```text id="3g8q4v"
baseline coverage
vs
current coverage
```

---

## 477.38 — Coverage regression

Tool có thể báo:

```text id="v1h6ss"
new uncovered branch
new uncovered function
lost covered region
```

Đây là factual difference, không phải quality ranking.

---

# 477.39 — Test-to-source mapping

Test runner có thể liên kết:

```text id="z9s2mk"
test_id
→ executed coverage nodes
```

---

## 477.40 — Test provenance

Coverage report phải cho biết execution đến từ:

```text id="e8n1ks"
unit test
integration test
system test
fuzz
benchmark
manual run
```

---

# 477.41 — Fuzz coverage

435 fuzzing engine có thể sử dụng coverage feedback.

---

## 477.42 — Coverage-guided fuzzing

Fuzzer có thể ưu tiên input tạo:

```text id="x2q7vb"
new edge
new region
new state
```

---

## 477.43 — Fuzz corpus

Corpus entry có thể lưu coverage signature.

---

## 477.44 — Corpus minimization

Có thể giảm corpus trong khi giữ coverage set mục tiêu.

---

# 477.45 — Differential coverage

Hai compiler/build/test configurations có thể so sánh coverage.

---

## 477.46 — Optimization coverage

Có thể so sánh source coverage trước/sau optimization.

Không coi optimizer output khác nhau là lỗi nếu semantics giữ nguyên.

---

# 477.47 — Coverage vs correctness

Coverage không chứng minh:

- output đúng;
- race-free;
- memory-safe;
- security-safe;
- performance tốt.

---

# 477.48 — Coverage vs unreachable

Một region có thể không execute vì:

```text id="x5d8pv"
input absent
configuration
platform
feature flag
```

không có nghĩa nó dead.

---

## 477.49 — Platform-specific coverage

Coverage phải gắn target:

```text id="1j7v2p"
x86_64-windows
aarch64-linux
wasm
```

Không merge mù các target khác nhau.

---

# 477.50 — Feature-specific coverage

Build feature/configuration phải được ghi lại.

---

## 477.51 — Conditional compilation

`comptime if`/target conditional phải tạo provenance riêng.

---

# 477.52 — Coverage overhead

Instrumentation overhead phải đo bằng 450/476.

---

## 477.53 — Lightweight mode

Có thể dùng compact counters.

---

## 477.54 — Detailed mode

Có thể lưu richer source/CFG provenance.

---

# 477.55 — Realtime

`@realtime` code không được mặc định chèn instrumentation gây:

- allocation;
- lock;
- blocking;
- unbounded buffering.

Realtime coverage phải có specialized mode hoặc bị disable.

---

# 477.56 — Security

Coverage artifact có thể chứa source paths, symbol names và execution structure.

Phải coi là potentially sensitive.

---

## 477.57 — Privacy

Không tự động export coverage.

---

# 477.58 — AI API

AI có thể query:

```text id="s2k9w0"
uncovered_functions()
uncovered_branches()
unsafe_sites_without_execution()
ffi_boundaries_without_tests()
coverage_for(change)
tests_covering(symbol)
```

---

## 477.59 — Change impact

Compiler có thể tính:

```text id="m4z0pj"
changed symbols
→ affected coverage regions
→ relevant tests
```

---

# 477.60 — Quality analysis

477 cung cấp factual evidence:

```text id="z7c3mw"
what executed?
what did not?
which test executed it?
which branches were observed?
```

Không tạo một “quality score”.

---

# 477.61 — Test prioritization

Tooling có thể đề xuất test liên quan tới changed regions dựa trên dependency/coverage data.

Đây là execution optimization, không phải quality ranking.

---

# 477.62 — Coverage thresholds

Project có thể đặt threshold:

```text id="2q5x9v"
minimum branch coverage = X
```

Threshold là build/test policy do developer lựa chọn.

Compiler không mặc định áp đặt.

---

# 477.63 — Threshold failure

Nếu threshold không đạt:

```text id="5j8a2k"
test/CI failure
```

nhưng không được diễn giải thành universal quality verdict.

---

# 477.64 — Generated tests

Generated/comptime tests phải có provenance.

---

# 477.65 — Coverage export

Có thể export:

```text id="q4w7bn"
JSON
LCOV-like
HTML
machine-readable native format
```

Các format bên ngoài thuộc tooling layer.

---

# 477.66 — Debug information

Coverage có thể sử dụng 440 debug/source mapping nhưng không phụ thuộc full debug symbols nếu semantic mapping artifact tồn tại.

---

# 477.67 — Symbol stripping

Release executable có thể strip symbols; coverage tooling dùng separate metadata artifact.

---

# 477.68 — Coverage server

Không cần coverage server.

Local deterministic operation phải được hỗ trợ.

---

# 477.69 — Test isolation

Coverage collector phải không làm thay đổi ownership/concurrency semantics của application.

---

# 477.70 — Failure handling

Coverage collection failure phải được báo riêng với test failure.

---

# 477.71 — Hard invariants

1. Coverage là execution evidence.
2. Coverage không phải correctness proof.
3. Coverage không phải quality score.
4. Function coverage được hỗ trợ.
5. Statement coverage được hỗ trợ.
6. Region coverage được hỗ trợ.
7. Branch coverage được hỗ trợ.
8. Condition coverage được hỗ trợ.
9. Line coverage là presentation mapping.
10. Coverage identity không dựa riêng vào line number.
11. CFG integration là nền tảng branch coverage.
12. Optimization phải được hỗ trợ.
13. Inlining phải giữ provenance.
14. Dead code khác uncovered code.
15. Constant-folded branch không bị báo sai.
16. Generated code có provenance.
17. Comptime coverage tách runtime coverage.
18. Async state machine có source mapping.
19. Match arms có thể được track.
20. Result/Option paths có thể được track.
21. Panic/error paths có thể được track.
22. Unsafe sites có coverage identity.
23. FFI boundaries có thể được track.
24. Concurrency coverage không chứng minh mọi interleaving.
25. GUI event coverage có thể được track.
26. Media pipeline coverage có thể được track.
27. GPU dispatch coverage có thể được track.
28. Counter overflow có semantics.
29. Concurrent counters phải an toàn hoặc per-thread.
30. Multi-process coverage có process identity.
31. Coverage merge giữ provenance.
32. Deterministic execution có deterministic logical coverage.
33. Coverage artifact có version.
34. Coverage artifact có build identity.
35. Coverage artifact có target identity.
36. Coverage artifact có provenance.
37. Source changes invalidate affected coverage.
38. Incremental coverage không reuse stale semantics.
39. Baseline comparison được hỗ trợ.
40. Coverage regression là factual difference.
41. Test-to-source mapping được hỗ trợ.
42. Test provenance được lưu.
43. Fuzz coverage được hỗ trợ.
44. Coverage-guided fuzzing được hỗ trợ.
45. Corpus minimization có thể dùng coverage.
46. Differential coverage được hỗ trợ.
47. Platform coverage không merge mù.
48. Feature configuration được ghi.
49. Conditional compilation có provenance.
50. Coverage overhead phải benchmark được.
51. Realtime code không nhận instrumentation không an toàn.
52. Coverage artifact có privacy boundary.
53. Không automatic coverage upload.
54. AI có thể query uncovered regions.
55. AI có thể query test-to-region mapping.
56. AI có thể query changed-region impact.
57. AI không biến coverage thành quality verdict.
58. Threshold là project policy.
59. Threshold failure tách khỏi compiler correctness.
60. Generated tests có provenance.
61. Coverage export có machine-readable format.
62. Coverage không bắt buộc full debug symbols.
63. Coverage collector không thay đổi program semantics.
64. Collection failure được phân biệt test failure.
65. Coverage không yêu cầu GC.
66. Coverage không yêu cầu network.
67. Coverage không yêu cầu database.
68. Coverage không yêu cầu GUI.
69. Coverage runtime có thể được loại bỏ khỏi production build.
70. **Axiom coverage foundation phải tạo được đường truy nguyên đáng tin cậy từ execution → CFG/IR → semantic node → source/test, đồng thời giữ rõ giới hạn của coverage và không biến nó thành một thước đo chất lượng tổng hợp.**

**BOOTSTRAP-477 hoàn tất / LOCKED.**

---

# BOOTSTRAP-478 — STATIC ANALYSIS, LINT, DATAFLOW, DEAD-CODE, API USAGE & PROGRAM QUALITY ANALYSIS

478 chuyển từ câu hỏi:

> “Code nào đã chạy?”

sang:

> “Compiler có thể chứng minh hoặc phát hiện điều gì về code mà không cần chạy?”

Kiến trúc:

```text id="f0m8qk"
Source
  ↓
AST / HIR
  ↓
Type / Ownership / Effect
  ↓
CFG / MIR / Call Graph
  ↓
Static Analysis Engine
  │
  ├── Dataflow
  ├── Control Flow
  ├── Dead Code
  ├── Unreachable
  ├── API Usage
  ├── Resource Lifetime
  ├── Concurrency
  ├── Security
  ├── Performance
  └── Complexity
          ↓
     Diagnostics
          ↓
    LSP / CLI / AI
```

### 478.1 — Static analysis không phải type checker

Type checker xác định chương trình có phù hợp type system hay không.

Static analyzer tìm thêm các properties/patterns có thể suy ra từ program.

---

### 478.2 — Analysis levels

```text id="s3f2nm"
Syntax
Semantic
HIR
MIR
Interprocedural
Whole-program
```

Mỗi level có cost và precision khác nhau.

---

### 478.3 — Dataflow analysis

Core framework:

```text id="k7a5dr"
Program Point
      ↓
Abstract State
      ↓
Transfer Function
      ↓
Join
      ↓
Fixpoint
```

---

### 478.4 — Lattice

Analysis state có thể dùng finite/height-bounded lattice để đảm bảo termination.

---

### 478.5 — Fixpoint

Loop/recursive CFG phải được xử lý bằng fixpoint computation có giới hạn.

---

### 478.6 — Definite assignment

Compiler có thể xác định variable/field đã được initialize trước khi đọc.

---

### 478.7 — Unused variable

Có thể cảnh báo local không được sử dụng.

Severity configurable.

---

### 478.8 — Unused import

Module imports không được sử dụng có thể được báo.

---

### 478.9 — Unused function

Function private không có reference có thể được báo.

---

### 478.10 — Dead code

Dead code phải phân biệt:

```text
provably unreachable
unreferenced
feature-disabled
possibly dynamically reached
```

---

### 478.11 — Reachability

Call graph không được giả định complete khi có:

- dynamic dispatch;
- FFI;
- reflection;
- dynamic library loading;
- function pointers.

---

### 478.12 — Exhaustiveness

Match exhaustiveness từ 430 là compiler error/property, không chỉ lint.

---

### 478.13 — Constant condition

Analyzer có thể phát hiện condition luôn true/false khi compiler có đủ proof.

---

### 478.14 — Redundant branch

Có thể cảnh báo branch không tạo semantic difference.

---

### 478.15 — Nullability

Axiom không có implicit null.

Analyzer vẫn phải hiểu:

```text
Option<T>
raw pointer
nullable foreign pointer
```

và không trộn semantics của chúng.

---

### 478.16 — Bounds analysis

Analyzer có thể chứng minh:

```text
index < length
```

để hỗ trợ 430/437 bounds-check elimination.

---

### 478.17 — Bounds diagnostics

Nếu không chứng minh được safety, compiler có thể giữ runtime check thay vì báo lỗi.

---

### 478.18 — Ownership analysis

478 sử dụng 423 ownership state:

```text
Owned
Borrowed
Moved
Destroyed
```

nhưng không thay thế ownership checker.

---

### 478.19 — Resource leak

Analyzer có thể phát hiện resource owner không được giải phóng trên một số paths.

---

### 478.20 — Lock analysis

Có thể phát hiện một số pattern:

```text
lock A → lock B
lock B → lock A
```

nhưng không tuyên bố deadlock-free toàn chương trình nếu proof không đầy đủ.

---

### 478.21 — Double lock

Có thể cảnh báo recursive lock acquisition nếu mutex không hỗ trợ recursive semantics.

---

### 478.22 — Blocking analysis

Call graph có thể truy:

```text
blocking operation
→ caller
→ caller
```

---

### 478.23 — Realtime analysis

`@realtime` function không được gọi operation có:

```text
allocation
blocking
filesystem
network
panic
unbounded synchronization
```

nếu contract cấm.

---

### 478.24 — Effect propagation

Effects từ 425/461/475 có thể propagate qua call graph.

---

### 478.25 — `@no_alloc`

Analyzer/compiler có thể kiểm tra call graph và allocator paths.

---

### 478.26 — `@no_block`

Tương tự với blocking operations.

---

### 478.27 — `@no_panic`

Analyzer có thể xác minh hoặc report unknown paths.

Không được biến “không tìm thấy panic” thành absolute mathematical proof nếu analysis incomplete.

---

### 478.28 — FFI effects

Foreign functions phải được xem conservative nếu contract không rõ.

---

### 478.29 — Unsafe propagation

Analyzer có thể hiển thị:

```text id="7h3c4p"
safe API
 ↓
unsafe implementation
 ↓
raw pointer operation
```

---

### 478.30 — API usage analysis

Có thể kiểm tra:

```text id="f2p9ax"
deprecated API
wrong lifecycle
missing initialization
invalid call ordering
```

khi package cung cấp protocol metadata.

---

### 478.31 — State-machine analysis

API có thể định nghĩa states:

```text id="7r8d2m"
Created
Initialized
Started
Stopped
Closed
```

Analyzer phát hiện usage sai thứ tự khi protocol đủ static information.

---

### 478.32 — Resource lifetime

469 resource handles và 455 file/database handles có thể tích hợp state analysis.

---

### 478.33 — Async misuse

Analyzer có thể cảnh báo:

```text id="n9j2cw"
blocking call inside async task
```

nếu API được annotate.

---

### 478.34 — Actor misuse

Có thể kiểm tra ActorRef capabilities/lifecycle nhưng không giả định mọi actor state statically known.

---

### 478.35 — Data race analysis

Safe subset dựa trên 424 `Send`/`Share`/atomic/mutex.

Advanced race analysis là optional analyzer.

---

### 478.36 — Security analysis

Có thể phát hiện patterns như:

```text id="g2d4pv"
unvalidated external input
unsafe parser boundary
path construction
format-string misuse
secret logging
```

chỉ khi sufficient metadata/analysis exists.

---

### 478.37 — Taint analysis

Optional taint framework:

```text id="0xj4ae"
Source
 ↓
Propagation
 ↓
Sink
```

---

### 478.38 — Trust boundary

445 trust metadata có thể cung cấp source/sink:

```text id="q6p0ve"
network input
file input
FFI input
IPC input
```

---

### 478.39 — Secret flow

Sensitive values từ 470/475 có thể được đánh dấu.

Analyzer có thể phát hiện flow:

```text id="p4q6sa"
Secret
 ↓
Log
```

---

### 478.40 — Performance lint

Analyzer có thể tìm patterns như:

- allocation trong hot path;
- unnecessary clone;
- blocking IO;
- repeated conversion;
- excessive copying.

Đây là **diagnostic evidence**, không phải performance ranking.

---

### 478.41 — Complexity analysis

Có thể cung cấp metrics:

```text id="n4v2xp"
CFG complexity
loop nesting
call depth
generic instantiation count
```

Không biến chúng thành universal “code quality score”.

---

### 478.42 — Generic bloat

Compiler có thể phát hiện generic monomorphization explosion.

---

### 478.43 — Code-size analysis

Có thể liên kết với 450:

```text id="j7k4sv"
source symbol
→ generated code size
```

---

### 478.44 — Inlining analysis

Có thể phát hiện excessive/inhibited inlining dựa trên compiler decisions.

---

### 478.45 — API compatibility

447 API metadata cho phép analyzer phát hiện breaking changes.

---

### 478.46 — ABI compatibility

447/421 ABI metadata dùng để kiểm tra:

```text layout
calling convention
symbol
alignment
parameter
return
```

---

### 478.47 — Lint levels

Canonical:

```text id="f9c2vq"
allow
warn
deny
```

Project có thể override theo policy.

---

### 478.48 — Lint identity

Mỗi lint có stable ID:

```text id="v8x2mj"
AX-LINT-XXXX
```

---

### 478.49 — Diagnostic

Diagnostic phải có:

```text id="c3p8za"
code
severity
message
source span
related spans
explanation
fix-it if safe
```

---

### 478.50 — Fix-it safety

Automatic fix chỉ được đánh dấu safe nếu compiler có thể xác định transformation không thay đổi intended semantics trong phạm vi rule.

---

### 478.51 — Machine-readable analysis

JSON/schema output phải cho phép IDE/AI query.

---

### 478.52 — LSP

478 tích hợp:

```text id="v7k3qm"
diagnostics
code actions
quick fixes
symbol analysis
```

---

### 478.53 — AI analysis

AI có thể query:

```text id="w5m9qs"
why is this warning emitted?
what proof is missing?
which call introduces allocation?
which path reaches unsafe code?
which API contract is violated?
```

---

### 478.54 — Analysis confidence

Analyzer phải phân biệt:

```text id="r6y1cd"
Proven
Likely
Heuristic
Unknown
```

Không được trình bày heuristic như proof.

---

### 478.55 — False positives

Rule có thể cho phép suppression:

```text id="2p7xk8"
@allow(...)
```

hoặc local configuration.

---

### 478.56 — Suppression provenance

Suppression phải có source location và rule identity.

---

### 478.57 — Baseline

Project có thể lưu known warnings baseline.

---

### 478.58 — Incremental analysis

Analysis result cache theo semantic dependencies.

---

### 478.59 — Parallel analysis

Independent analysis queries có thể chạy parallel.

---

### 478.60 — Determinism

Cùng input/configuration phải tạo cùng diagnostics/order semantics.

---

### 478.61 — Whole-program analysis

Whole-program analysis là optional vì:

- dynamic libraries;
- FFI;
- plugins;
- runtime loading

có thể khiến complete knowledge impossible.

---

### 478.62 — Closed-world analysis

Tool có thể explicit chọn:

```text id="s9x3fd"
closed-world
```

khi toàn bộ call graph đã biết.

---

### 478.63 — Open-world analysis

Default library/API analysis phải chấp nhận external code.

---

### 478.64 — Incremental invalidation

Thay đổi function chỉ invalidate analysis phụ thuộc vào function đó khi dependency graph cho phép.

---

### 478.65 — Fuzzing analyzer

Static analyzer itself phải được fuzz:

```text id="u1w6rb"
parser
HIR
CFG
MIR
type metadata
malformed packages
```

---

### 478.66 — Analyzer termination

Analyzer phải có resource limits:

```text id="q3a8ne"
time
memory
recursion
iterations
```

---

### 478.67 — No compiler hang

Pathological program không được khiến compiler chạy vô hạn.

---

### 478.68 — Security

Untrusted package metadata không được khiến analyzer thực thi arbitrary external code.

---

### 478.69 — Build scripts

Static analyzer không được tự chạy build scripts để “hiểu” program nếu configuration không cho phép.

---

### 478.70 — Comptime

Analyzer phải phân biệt:

```text compile-time behavior
runtime behavior
```

---

### 478.71 — Generated artifacts

Analysis phải giữ provenance của generated HIR/MIR.

---

### 478.72 — Test integration

Test runner có thể yêu cầu:

```text id="5z8h0m"
check
lint
analyze
test
```

như các phase riêng.

---

### 478.73 — CI policy

CI có thể biến lint severity thành failure theo project configuration.

Compiler core không ép policy.

---

### 478.74 — Analysis profiles

Có thể có:

```text id="c5v9ks"
basic
standard
strict
security
performance
realtime
```

Đây là collection presets.

---

### 478.75 — Hard invariants

1. Static analysis khác type checking.
2. Analysis có nhiều abstraction levels.
3. Dataflow framework được hỗ trợ.
4. Fixpoint computation có giới hạn.
5. Definite assignment được hỗ trợ.
6. Unused-variable analysis được hỗ trợ.
7. Unused-import analysis được hỗ trợ.
8. Dead code phải phân biệt với unreachable.
9. Reachability phải tính đến dynamic dispatch.
10. FFI làm call graph open-world.
11. Function pointers làm call graph không hoàn toàn tĩnh.
12. Constant conditions có thể được phát hiện.
13. Bounds analysis được hỗ trợ.
14. Bounds analysis hỗ trợ optimizer nhưng không thay thế semantics.
15. Ownership analysis tích hợp 423.
16. Resource leak analysis được hỗ trợ.
17. Lock-order analysis được hỗ trợ ở mức có thể chứng minh.
18. Deadlock không được tuyên bố absent nếu analysis incomplete.
19. Blocking analysis được hỗ trợ.
20. Realtime effect analysis được hỗ trợ.
21. Effect propagation được hỗ trợ.
22. `@no_alloc` có thể được phân tích.
23. `@no_block` có thể được phân tích.
24. `@no_panic` có thể được phân tích.
25. FFI effect contracts được tôn trọng.
26. Unsafe propagation có thể được truy nguyên.
27. API protocol analysis được hỗ trợ khi metadata tồn tại.
28. Resource lifecycle analysis được hỗ trợ.
29. Async blocking misuse có thể được phát hiện.
30. Actor misuse analysis không giả định complete static knowledge.
31. Safe concurrency analysis được hỗ trợ.
32. Advanced race analysis là optional.
33. Security taint analysis có thể được hỗ trợ.
34. Trust boundaries từ 445 được tích hợp.
35. Secret flow analysis được hỗ trợ.
36. Performance lints là diagnostics, không phải ranking.
37. Complexity metrics không phải universal quality score.
38. Generic bloat có thể được phát hiện.
39. Code-size analysis tích hợp 450.
40. Inlining analysis có thể được expose.
41. API compatibility tích hợp 447.
42. ABI compatibility tích hợp 421/447.
43. Lint levels có `allow/warn/deny`.
44. Lint IDs ổn định.
45. Diagnostics machine-readable.
46. Safe fix-it phải có semantics contract.
47. AI có thể query analysis reasoning/evidence.
48. Analyzer phải phân biệt proof với heuristic.
49. False-positive suppression được hỗ trợ.
50. Suppression có provenance.
51. Warning baseline được hỗ trợ.
52. Analysis cache incremental.
53. Analysis có thể parallel.
54. Analysis deterministic.
55. Whole-program analysis là optional.
56. Closed-world analysis phải explicit.
57. Open-world analysis là cần thiết cho external code.
58. Incremental invalidation dựa trên dependencies.
59. Analyzer được fuzz.
60. Analyzer có resource limits.
61. Pathological input không được tạo infinite analysis.
62. Untrusted metadata không được chạy arbitrary code.
63. Build scripts không tự động được execute.
64. Comptime/runtime semantics được phân biệt.
65. Generated code có provenance.
66. Static analysis là phase riêng trong test pipeline.
67. CI policy là project configuration.
68. Analysis profiles là presets.
69. Static analysis không yêu cầu GC.
70. Static analysis không yêu cầu borrow checker ngoài semantics 423.
71. Static analysis không thay đổi program semantics.
72. **Axiom static-analysis foundation phải cung cấp bằng chứng có thể truy nguyên về control flow, dataflow, ownership, effects, resource lifetime, concurrency, security và performance mà không trình bày heuristic như proof và không biến các metrics/lint thành một “quality score” tổng hợp.**

**BOOTSTRAP-478 hoàn tất / LOCKED.**

---

# BOOTSTRAP-479 — CONTRACTS, ASSERTIONS, PRECONDITIONS, POSTCONDITIONS, INVARIANTS & DESIGN-BY-CONTRACT

479 sẽ xây lớp **program contracts** phía trên type system, ownership và static analysis:

```text
Function
   │
   ├── Preconditions
   ├── Body
   ├── Postconditions
   └── Invariants
          ↓
   Static Analysis
          ↓
   Runtime Verification
```

Phạm vi:

- `assert`;
- debug assertions;
- release assertions;
- `assume`;
- preconditions;
- postconditions;
- type invariants;
- struct invariants;
- module invariants;
- loop invariants;
- resource invariants;
- ownership/resource contracts;
- `@requires`;
- `@ensures`;
- `@invariant`;
- old/pre-state values;
- result/post-state references;
- panic vs Result khi contract fail;
- compile-time provable contracts;
- runtime contract checking;
- contract elimination;
- optimizer interaction;
- `assume` semantics và unsafe boundary;
- FFI pre/postconditions;
- concurrency contracts;
- realtime contracts;
- security contracts;
- contract inheritance không dùng class inheritance;
- trait contracts;
- generic contracts;
- contract specialization;
- contract violation diagnostics;
- source/IR mapping;
- AI-readable proof obligations;
- property-based testing integration;
- fuzzing integration;
- contract coverage integration với 477;
- contract evidence integration với 478;
- performance overhead measurement 450/476;
- deterministic contract behavior;
- no hidden production checks unless explicitly configured.

Nguyên tắc trung tâm:

```text id="u8r5mc"
Contract
    ≠
Type
    ≠
Assertion
    ≠
Assumption
    ≠
Proof
```

Đặc biệt `assume` sẽ được khóa rất chặt: nó **không kiểm tra điều kiện** mà nói với optimizer rằng điều kiện là đúng; nếu assumption sai, behavior có thể trở thành undefined/invalid theo contract. Vì vậy đây sẽ là một trong những điểm cần ranh giới rõ giữa **checked assertion**, **verified contract** và **unsafe optimization assumption**.