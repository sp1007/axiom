# BOOTSTRAP-341 — AXIOM FUZZING, PROPERTY TESTING & AUTOMATED BUG DISCOVERY ENGINE

Sau 340, Axiom đã có một nền tảng rất mạnh để **phát hiện lỗi khi chương trình chạy**. Bước tiếp theo hợp lý là xây dựng hệ thống tự động **tạo ra chương trình/input có khả năng kích hoạt các lỗi đó**.

Mục tiêu của 341 không chỉ là fuzz application, mà đặc biệt là fuzz chính **compiler**:

> **Compiler phải có khả năng tự kiểm tra parser, type system, trait solver, comptime, MIR, verifier, optimizer, code generator, linker và semantic equivalence bằng hàng triệu chương trình được sinh tự động.**

Đây là một trong những thành phần quan trọng nhất để Axiom có thể trở thành compiler production-grade.

---

# 1. Ba đối tượng cần fuzz

Axiom phân biệt:

```text
Compiler Fuzzing
Program Fuzzing
Runtime/System Fuzzing
```

### Compiler Fuzzing

Tìm:

- compiler crash;
- ICE;
- nontermination;
- wrong diagnostic;
- wrong code generation;
- miscompilation;
- verifier bug;
- optimizer bug.

### Program Fuzzing

Tìm:

- panic;
- memory bug;
- race;
- FFI bug;
- parser/input bug;
- protocol bug.

### Runtime/System Fuzzing

Tìm:

- allocator bug;
- async executor bug;
- scheduler bug;
- synchronization bug;
- component loader bug;
- linker/object writer bug.

---

# 2. Compiler fuzzing là ưu tiên đặc biệt

Axiom compiler có pipeline rất dài:

```text
Source
 ↓
Lexer
 ↓
Parser
 ↓
Resolver
 ↓
HIR
 ↓
Type
 ↓
Trait
 ↓
Comptime
 ↓
MIR
 ↓
Verifier
 ↓
Optimizer
 ↓
LIR
 ↓
Machine
 ↓
Object
 ↓
Link
```

Bất kỳ stage nào cũng có thể được fuzz độc lập.

---

# 3. Fuzzing không được coi compiler crash là “bình thường”

Một compiler crash phải được phân loại:

```text
CompilerBug
InvalidInput
ResourceExhaustion
UnsupportedFeature
InternalInvariantViolation
```

Không được gom tất cả thành:

```text
compile failed
```

---

# 4. Compiler fuzzing pipeline

```text
Seed
 ↓
Generate
 ↓
Mutate
 ↓
Minimize
 ↓
Compile
 ↓
Validate
 ↓
Compare
 ↓
Classify
 ↓
Store
```

---

# 5. Source generator

Axiom cần generator có grammar-aware generation.

Không chỉ random text:

```text id="1f0a3f"
x9!@#q...
```

mà tạo:

```text
fn foo(x: i32) -> i32 {
    match x {
        0 => 1,
        _ => x + 1
    }
}
```

---

# 6. AST generator

Sau parser, có thể fuzz trực tiếp AST/HIR.

Ví dụ:

```text
AstGenerator
HirGenerator
MirGenerator
TypeGenerator
TraitConstraintGenerator
```

Điều này giúp bỏ qua parser khi kiểm tra backend.

---

# 7. Grammar-aware generation

Generator hiểu:

```text
expression
statement
pattern
type
generic
trait
impl
async
comptime
unsafe
FFI
GPU
```

và biết production nào hợp lệ.

---

# 8. Valid và invalid programs

Không chỉ tạo program hợp lệ.

Tỷ lệ configurable:

```text
Valid
InvalidSyntax
InvalidType
InvalidOwnership
InvalidCapability
InvalidTrait
InvalidComptime
InvalidConcurrency
InvalidFFI
InvalidGPU
```

Compiler phải xử lý tất cả mà không crash.

---

# 9. Mutation operators

Ví dụ:

```text
DeleteNode
DuplicateNode
SwapOperands
ChangeType
ChangeLiteral
ChangePattern
ChangeOwnershipOperation
InsertAwait
RemoveAwait
AddMove
RemoveMove
ChangeTraitBound
ChangeGenericArgument
```

---

# 10. Semantic-preserving mutations

Đặc biệt quan trọng.

Ví dụ:

```text
x + 0
```

thay bằng:

```text
x
```

hoặc:

```text
let y = x;
return y;
```

thay bằng:

```text
return x;
```

Nếu hai chương trình semantic-equivalent, compiler output phải tương thích về observable behavior.

---

# 11. Differential testing

Axiom có thể so sánh:

```text
Compiler A
Compiler B
Reference Interpreter
```

Ví dụ:

```text
Source
 ├── Reference Interpreter → Result A
 └── Native Compiler       → Result B
```

Nếu:

```text
A != B
```

→ potential miscompilation.

---

# 12. Reference interpreter

317 đã định nghĩa reference interpreter.

341 tận dụng nó làm oracle:

```text
Program
 ├── Interpreter
 └── Compiler → Native → Execute
```

Đây là một trong những phương pháp mạnh nhất để tìm compiler bug.

---

# 13. Interpreter phải là semantic oracle

Không so sánh:

```text
machine instructions
```

mà so sánh observable semantics:

```text
stdout
stderr
exit status
return value
panic class
observable IO
```

---

# 14. Deterministic test programs

Compiler fuzzing ưu tiên chương trình:

```text
deterministic
small
side-effect limited
```

để giảm false positives.

---

# 15. Optimization differential testing

Một chương trình được compile:

```text
-O0
-O1
-O2
-O3
-Os
```

phải cho cùng observable semantics.

Ví dụ:

```text
Result(O0)
=
Result(O3)
```

Nếu khác:

> potential optimizer bug.

---

# 16. Target differential testing

Có thể compile cùng source:

```text
x86_64
aarch64
wasm
```

và so sánh semantic result.

Không yêu cầu binary giống nhau.

---

# 17. Backend differential testing

Ví dụ cùng target:

```text
Axiom backend
LLVM bootstrap backend
```

Trong giai đoạn bootstrap, output semantics phải tương đương.

Sau self-host:

```text
Compiler v1
Compiler v2
```

cũng có thể so sánh.

---

# 18. Translation validation

318 đã có translation validation.

Fuzzer tạo:

```text
BeforeOptimization
AfterOptimization
```

và validator kiểm tra:

```text
Semantics(before)
==
Semantics(after)
```

Nếu fail:

```text
optimization bug
```

---

# 19. Pass-level differential testing

Mỗi optimization pass có thể fuzz:

```text
MIR_before
 ↓
Pass
 ↓
MIR_after
```

Sau đó interpreter chạy cả hai.

---

# 20. Randomized pass ordering

Nếu pass dependency cho phép:

```text
Pass A → Pass B
```

thì fuzzer có thể thử:

```text
A → B
B → A
```

nhưng chỉ với ordering hợp lệ.

Mục tiêu:

- tìm hidden pass assumptions;
- stale analysis;
- invalidation bug.

---

# 21. Analysis invalidation fuzzing

Một bug nguy hiểm:

```text
Pass modifies MIR
 ↓
Analysis cache không invalidate
 ↓
Pass sau dùng stale facts
```

341 phải fuzz:

```text
analysis dependency
invalidation
recompute
incremental reuse
```

---

# 22. Incremental compilation fuzzing

Build:

```text
Source v1
 ↓
Compile
```

sau đó mutation:

```text
Source v2
 ↓
Incremental compile
```

so sánh với:

```text
Clean build v2
```

Phải tương đương:

```text
Incremental(v2)
≈
Clean(v2)
```

---

# 23. Cache correctness fuzzing

Fuzz:

```text
cache hit
cache miss
partial cache
stale cache
remote cache
```

và kiểm tra kết quả.

---

# 24. Build graph fuzzing

Tạo dependency graph ngẫu nhiên:

```text
A
├── B
│   └── D
└── C
```

với:

- cycles;
- optional dependencies;
- target-specific dependencies;
- comptime dependencies;
- ABI boundaries.

Scheduler không được deadlock hoặc chạy sai dependency.

---

# 25. Parallel build differential testing

So sánh:

```text
--jobs=1
--jobs=2
--jobs=8
--distributed
```

Kết quả semantic/artifact phải phù hợp policy reproducibility.

---

# 26. Comptime fuzzing

Đây là vùng rất quan trọng.

Generator tạo:

```text
comptime fn
comptime {
    ...
}
```

với:

- recursion;
- generic;
- reflection;
- filesystem;
- generated declarations;
- target queries.

---

# 27. Comptime termination

Comptime có thể tạo:

```text
infinite recursion
```

Compiler phải phân biệt:

```text
UserComptimeLimit
CompilerResourceExhaustion
CompilerICE
```

---

# 28. Comptime sandbox fuzzing

Fuzz capability attempts:

```text
ReadSource
ReadFilesystem
Network
ExecuteTool
Environment
```

Kiểm tra:

> chương trình không thể vượt capability contract.

---

# 29. Type-system fuzzing

Generator tạo:

```text
nested generics
recursive types
trait bounds
associated types
const params
higher-order functions
```

Mục tiêu:

- solver crash;
- exponential behavior;
- incorrect type acceptance;
- incorrect rejection.

---

# 30. Trait solver fuzzing

Đặc biệt tạo:

```text
trait A<T>
trait B<T>: A<T>
impl ...
```

với:

- cycles;
- ambiguous candidates;
- overlapping impls;
- deep constraints.

Compiler phải:

```text
Proven
NotProven
Ambiguous
Error
```

chứ không:

```text
hang forever
```

---

# 31. Termination budget

Mỗi solver operation có:

```text
fuel
depth
node_budget
time_budget
```

Nếu vượt:

```text
SolverResourceLimit
```

không phải ICE.

---

# 32. Ownership fuzzing

Generator tạo:

```text
move
copy
clone
drop
view
mut_view
partial move
return
closure capture
await
spawn
```

và kiểm tra verifier.

---

# 33. Ownership mutation

Ví dụ:

```text
let y = x;
```

mutation:

```text
let y = move x;
```

hoặc:

```text
let y = view(x);
```

Mục tiêu kiểm tra state transition.

---

# 34. Capability fuzzing

Tạo:

```text
view
mut_view
nested view
field view
disjoint view
overlapping view
```

và xác nhận verifier.

---

# 35. Region solver fuzzing

Sinh các region relation:

```text
DISJOINT
SAME
CONTAINS
OVERLAPS
UNKNOWN
```

và kiểm tra conflict detection.

---

# 36. Concurrency fuzzing

Generate:

```text
thread
spawn
join
atomic
mutex
channel
async
await
```

sau đó chạy với scheduler randomized.

---

# 37. Schedule fuzzing

Cùng program:

```text
Schedule A
Schedule B
Schedule C
```

Nếu program không có intentional nondeterminism, race detector phải tìm được vi phạm.

---

# 38. Atomic memory-model fuzzing

Generate:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

với các thread.

Reference memory model kiểm tra allowed outcomes.

---

# 39. Litmus test generation

Tự động sinh các test:

```text
Store Buffering
Load Buffering
Message Passing
IRIW
```

và kiểm tra implementation.

Axiom không được vô tình có semantics khác với memory model đã định nghĩa.

---

# 40. Async fuzzing

Generate:

```text
Future
await
spawn
cancel
drop future
wake
poll
```

với random executor schedules.

---

# 41. Waker fuzzing

Fuzz:

```text
wake
wake_by_ref
clone
drop
double wake
wake after task completion
```

Mục tiêu phát hiện executor/library bugs.

---

# 42. Cancellation fuzzing

Randomly cancel:

```text
before await
during await
after ready
during nested task
```

Kiểm tra:

- Drop;
- resource cleanup;
- task state;
- no invalid access.

---

# 43. GPU fuzzing

Generate kernels:

```text
@kernel fn ...
```

với:

- arrays;
- views;
- shared memory;
- atomics;
- barriers.

Compile + run trên simulator/device khi có.

---

# 44. GPU differential testing

Có thể so sánh:

```text
CPU reference
      vs
GPU kernel
```

Ví dụ:

```text
CPU result == GPU result
```

cho deterministic kernels.

---

# 45. FFI fuzzing

Sinh boundary contracts:

```text
pointer
length
nullability
alignment
ownership
callbacks
variadic
```

và test adapter.

---

# 46. ABI fuzzing

Tạo random ABI-safe types:

```text
i32
f64
struct
enum
repr(C)
tuple
array
```

sau đó:

```text
Axiom → C
C → Axiom
```

so sánh values.

---

# 47. Object writer fuzzing

Random object structures:

```text
sections
symbols
relocations
alignment
visibility
```

Sau đó:

```text
write
 → parse
 → verify
```

phải round-trip.

---

# 48. Linker fuzzing

Tạo object graph:

```text
A.o
B.o
C.o
```

với:

- weak symbols;
- aliases;
- relocations;
- TLS;
- imports;
- exports.

Kiểm tra linker không crash.

---

# 49. Executable round-trip

Pipeline:

```text
Source
 → Object
 → Executable
 → Parser
```

kiểm tra:

```text
sections
symbols
relocations
entry
segments
```

không bị corruption.

---

# 50. Parser fuzzing

Classic:

```text
random bytes
```

nhưng parser phải đảm bảo:

```text
no buffer overflow
no infinite loop
no excessive memory
no ICE
```

---

# 51. Unicode fuzzing

Axiom UTF-8 mặc định.

Fuzz:

```text
UTF-8 valid
UTF-8 invalid
combining marks
large code points
normalization edge cases
identifiers
strings
source comments
```

---

# 52. Diagnostic fuzzing

Compiler phải tạo diagnostic ổn định ngay cả với source lỗi nặng.

Không được:

```text
parser crash
```

chỉ vì:

```text
unterminated string
```

---

# 53. Diagnostic stability

Fuzzer có thể kiểm tra:

```text
same source
same compiler
```

→ diagnostic ordering deterministic.

---

# 54. Resource exhaustion fuzzing

Không phải bug nếu compiler nói:

```text
CompilationResourceLimit
```

Bug là:

```text
memory corruption
hang
deadlock
stack overflow
```

---

# 55. Timeout engine

Mỗi fuzz case có:

```text
compile_timeout
execute_timeout
memory_limit
output_limit
```

---

# 56. Hang detection

Fuzzer cần phân biệt:

```text
slow
deadlock
infinite_loop
solver_nontermination
compiler_hang
```

Có heartbeat:

```text
Parser progress
Query progress
Pass progress
Codegen progress
```

---

# 57. Compiler heartbeat

Ví dụ:

```text
CompilationProgress {
    phase
    query
    source
    elapsed
}
```

Nếu đứng quá lâu:

```text
possible hang
```

---

# 58. Crash artifact

Mỗi failure lưu:

```text
FailureArtifact {
    source
    seed
    mutation_history
    compiler_version
    target
    optimization
    sanitizer
    environment
    stack
    diagnostic
}
```

---

# 59. Reproducer

Fuzzer phải tự tạo:

```text
repro/
├── program.ax
├── config.toml
├── compiler.json
└── README
```

với command:

```text
axiom fuzz reproduce failure.axfuzz
```

---

# 60. Automatic minimization

Input ban đầu:

```text
10,000 lines
```

Fuzzer giảm xuống:

```text
17 lines
```

mà vẫn crash.

---

# 61. Delta debugging

Minimizer thử:

```text
remove declaration
remove expression
remove statement
remove type
remove generic bound
```

theo AST/HIR thay vì chỉ xóa bytes.

---

# 62. Semantic minimization

Nếu failure vẫn tồn tại:

```text
same failure signature
```

thì tiếp tục giảm.

---

# 63. Failure signature

Ví dụ:

```text
FuzzFailureSignature {
    category
    compiler_phase
    diagnostic_code
    sanitizer_code
    crash_site
    MIRLocation
}
```

Dùng để deduplicate.

---

# 64. Corpus

Corpus gồm:

```text
SeedPrograms
RegressionPrograms
MinimizedFailures
InterestingPrograms
CoverageMaximizers
SemanticCornerCases
```

---

# 65. Coverage

Compiler fuzzing cần nhiều loại coverage:

```text
SourceCoverage
ASTCoverage
HIRCoverage
MIRCoverage
PassCoverage
BranchCoverage
QueryCoverage
TypeSolverCoverage
BackendCoverage
```

Không chỉ machine line coverage.

---

# 66. Semantic coverage

Đây là điểm rất phù hợp Axiom.

Ví dụ compiler report:

```text
Ownership:
  Move = 92%
  PartialMove = 48%
  View = 91%
  MutView = 77%
  Drop = 94%

Async:
  await = 82%
  cancellation = 41%

GPU:
  kernel = 32%
  barrier = 17%
```

---

# 67. Compiler phase coverage

```text
Parser              96%
Trait solver         91%
Ownership verifier   94%
MIR optimizer        88%
Instruction selector 83%
Object writer        79%
Linker               71%
```

Fuzzer ưu tiên vùng coverage thấp.

---

# 68. Mutation score

Fuzzer đo:

```text
mutation
→ new path?
→ new semantic state?
→ new failure?
```

Mutation không tạo gì mới thì giảm priority.

---

# 69. Corpus scheduling

Ưu tiên seed:

```text
high coverage
rare semantic feature
recent failure
deep compiler path
```

---

# 70. Parallel fuzzing

Fuzz workers:

```text
Worker 1
Worker 2
Worker 3
...
```

nhưng corpus merge phải deterministic.

---

# 71. Distributed fuzzing

Có thể chạy:

```text
local
CI
cloud
remote worker
```

với:

```text
CorpusFingerprint
CompilerFingerprint
TargetFingerprint
```

---

# 72. Differential compiler matrix

Axiom CI có thể chạy:

```text
Compiler N
Compiler N-1
Reference Interpreter
Debug Build
Release Build
```

và so sánh.

---

# 73. Bootstrap compiler differential

Trong quá trình self-host:

```text
Bootstrap compiler
        vs
Self-hosted compiler
```

compile cùng source.

So sánh:

```text
semantic behavior
ABI
diagnostics
```

---

# 74. Compiler bootstrap fuzzing

Một trong những test mạnh:

```text
Compiler A
 ↓
build Compiler B

Compiler B
 ↓
build Compiler C
```

Sau đó so sánh:

```text
B(C) semantic
C(C) semantic
```

để tìm self-hosting instability.

---

# 75. Metamorphic testing

Không cần biết exact answer.

Ví dụ:

```text
Program P
```

thêm dead code:

```text
Program P'
```

Kỳ vọng:

```text
observable behavior(P)
==
observable behavior(P')
```

---

# 76. Metamorphic relations

Axiom có thể định nghĩa:

```text
AddDeadCode
RenameLocal
ReorderIndependentDeclarations
InlineEquivalentFunction
RemoveRedundantCopy
AddUnreachableBranch
EquivalentPatternRewrite
```

---

# 77. ABI metamorphic testing

Thay đổi implementation private:

```text
private function body
```

không được làm thay đổi:

```text
public ABI
```

nếu contract không yêu cầu.

---

# 78. Incremental metamorphic testing

```text
Source A
```

→ thay đổi comment:

```text
Source B
```

Kỳ vọng:

```text
semantic fingerprint unchanged
```

và compiler không rebuild semantic layers không cần thiết.

---

# 79. Optimization metamorphic testing

```text
-O0
-O3
```

phải giữ:

```text
observable semantics
```

nhưng binary/performance có thể khác.

---

# 80. Sanitizer metamorphic testing

```text
normal build
sanitized build
```

với program hợp lệ:

```text
same observable result
```

Nếu sanitized build khác:

```text
potential sanitizer instrumentation bug
```

---

# 81. Fuzzer oracle hierarchy

Ưu tiên:

```text
1. Formal invariant
2. Reference interpreter
3. Differential compiler
4. Metamorphic relation
5. Sanitizer
6. Crash/hang detector
```

---

# 82. Oracle không đáng tin tuyệt đối

Reference interpreter cũng có thể có bug.

Do đó không dùng một oracle duy nhất cho mọi trường hợp.

Có thể cross-check:

```text
Interpreter
Compiler A
Compiler B
Formal validator
```

---

# 83. Compiler fuzzing security

Fuzz input có thể cố:

```text
memory exhaustion
stack exhaustion
pathological generics
comptime explosion
```

Compiler phải chạy trong sandbox.

---

# 84. Fuzz worker sandbox

Worker có:

```text
CPU limit
memory limit
filesystem sandbox
network disabled
process limit
time limit
```

đặc biệt khi fuzz comptime/build system.

---

# 85. Fuzz provenance

Mỗi failure có:

```text
SeedId
GeneratorVersion
MutationVersion
CompilerVersion
Target
SanitizerProfile
```

để reproduce chính xác.

---

# 86. Fuzzer versioning

Generator thay đổi có thể tạo corpus behavior khác.

Do đó:

```text
GeneratorFingerprint
MutationEngineFingerprint
```

được lưu.

---

# 87. Regression database

Mọi compiler bug đã sửa trở thành:

```text
RegressionTest
```

và không bị tự động xóa khỏi corpus.

---

# 88. Bug lifecycle

```text
Found
 ↓
Minimized
 ↓
Triaged
 ↓
Fixed
 ↓
Regression Added
 ↓
Verified
```

---

# 89. Automatic bisect

Nếu failure xuất hiện:

```text
commit N
```

fuzzer có thể binary-search:

```text
N/2
...
```

để tìm introducing change.

---

# 90. Compiler pass blame

Nếu failure chỉ xuất hiện:

```text
-O3
```

fuzzer có thể chạy:

```text
disable pass A
disable pass B
disable pass C
```

để tìm pass gây lỗi.

---

# 91. Optimization isolation

Pipeline:

```text
-O3
 ↓
Pass sequence
```

Fuzzer tạo reduced sequence:

```text
A → C → F
```

vẫn gây lỗi.

Đây là artifact cực kỳ giá trị cho compiler developer.

---

# 92. Miscompilation reducer

Nếu:

```text
O0 = 42
O3 = 43
```

fuzzer phải:

1. giảm source;
2. giảm optimization pass;
3. xác định MIR trước/sau;
4. xác định machine instruction;
5. tạo minimal reproducer.

---

# 93. Wrong-code diagnosis

Failure artifact:

```text
Expected:
42

Actual:
43

Last matching MIR:
block_17

First divergent MIR:
block_18

First divergent machine instruction:
0x1842
```

---

# 94. Compiler invariant testing

Mỗi compiler subsystem định nghĩa invariant:

```text
Parser invariant
Type invariant
MIR invariant
Ownership invariant
Capability invariant
ABI invariant
Layout invariant
Machine invariant
```

Fuzzer gọi verifier sau mỗi phase.

---

# 95. Phase checkpoint fuzzing

```text
Parse
 ↓ verify AST
Resolve
 ↓ verify HIR
Type
 ↓ verify Typed HIR
MIR
 ↓ verify MIR
Optimize
 ↓ verify MIR
Lower
 ↓ verify LIR
Machine
 ↓ verify machine IR
```

Bug được bắt gần nguồn hơn.

---

# 96. Internal compiler assertion

Không dùng:

```text
assert(false)
```

một cách vô nghĩa.

Thay vào đó:

```text
AXIOM-ICE-CAPABILITY-017
```

với:

```text
invariant
location
IR object
dependencies
```

---

# 97. AI-readable failure

Mỗi failure có JSON-like semantic representation:

```text
FuzzFailure {
    category: "Miscompilation",
    phase: "LoopVectorization",
    source_span: ...,
    expected: ...,
    actual: ...,
    invariant: ...,
    reproducer: ...
}
```

Điều này rất phù hợp workflow AI-agent của Axiom.

---

# 98. CLI

```text
axiom fuzz compiler
axiom fuzz program
axiom fuzz runtime

axiom fuzz corpus
axiom fuzz minimize
axiom fuzz reproduce
axiom fuzz bisect
axiom fuzz coverage
axiom fuzz semantic-coverage

axiom test differential
axiom test metamorphic
axiom test optimization
axiom test incremental
```

---

# 99. CompilerDB

Bổ sung:

```text
FuzzDB
GeneratorDB
MutationDB
CorpusDB
CoverageDB
SemanticCoverageDB
OracleDB
DifferentialDB
MetamorphicDB
FailureDB
MinimizationDB
RegressionDB
FuzzWorkerDB
FuzzSandboxDB
BisectDB
```

---

# 100. Implementation tree

```text
compiler/
└── fuzz/
    ├── model/
    ├── generator/
    │   ├── source/
    │   ├── ast/
    │   ├── hir/
    │   ├── mir/
    │   ├── type/
    │   ├── trait/
    │   ├── ownership/
    │   ├── concurrency/
    │   ├── async/
    │   ├── gpu/
    │   └── ffi/
    ├── mutation/
    ├── metamorphic/
    ├── differential/
    ├── oracle/
    ├── coverage/
    ├── semantic_coverage/
    ├── corpus/
    ├── minimizer/
    ├── reproducer/
    ├── bisect/
    ├── regression/
    ├── distributed/
    ├── sandbox/
    └── reporting/
```

---

# 101. Invariants

```text
AFUZZ-01
Every compiler input must be handled without memory unsafety.

AFUZZ-02
Invalid source must never cause an unexpected compiler crash.

AFUZZ-03
Compiler hangs must be distinguishable from valid long-running compilation.

AFUZZ-04
Fuzz workers must have resource limits.

AFUZZ-05
Compiler fuzzing must support deterministic reproduction.

AFUZZ-06
Every minimized failure must preserve its failure signature.

AFUZZ-07
Reference interpreter results must be compared at the semantic level.

AFUZZ-08
Optimization levels must preserve observable semantics.

AFUZZ-09
Incremental compilation must be equivalent to clean compilation.

AFUZZ-10
Parallel compilation must preserve semantic results.

AFUZZ-11
Cache reuse must not alter semantic results.

AFUZZ-12
Comptime sandbox boundaries must be fuzzable.

AFUZZ-13
Trait solver termination must be tested.

AFUZZ-14
Ownership and capability state transitions must be fuzzable.

AFUZZ-15
Concurrency schedules must be fuzzable.

AFUZZ-16
Async cancellation and wake behavior must be fuzzable.

AFUZZ-17
GPU kernels must be differentially testable against reference implementations where possible.

AFUZZ-18
FFI contracts must be fuzzable independently of application logic.

AFUZZ-19
Object writers must support structural round-trip testing.

AFUZZ-20
Linkers must be fuzzable using generated object graphs.

AFUZZ-21
Every fixed compiler bug should become a regression test.

AFUZZ-22
Fuzzer-generated programs must carry generator provenance.

AFUZZ-23
Coverage must include semantic/compiler-state coverage, not only source lines.

AFUZZ-24
Fuzzing must never silently suppress compiler invariant violations.

AFUZZ-25
Differential testing must tolerate legitimate target-specific representation differences.

AFUZZ-26
Metamorphic transformations must declare their semantic relation.

AFUZZ-27
Sanitized and unsanitized builds of valid programs must preserve observable semantics.

AFUZZ-28
Fuzzing infrastructure must remain optional for normal compiler builds.

AFUZZ-29
Distributed fuzzing workers must verify compiler and generator fingerprints.

AFUZZ-30
A minimized reproducer must be executable independently of the original fuzzing session.
```

---

# 102. Definition of Done

BOOTSTRAP-341 hoàn thành khi Axiom có:

- source fuzzing;
- AST/HIR/MIR fuzzing;
- type-system fuzzing;
- trait-solver fuzzing;
- ownership fuzzing;
- capability fuzzing;
- concurrency fuzzing;
- async fuzzing;
- GPU fuzzing;
- FFI fuzzing;
- parser/Unicode fuzzing;
- comptime fuzzing;
- object writer fuzzing;
- linker fuzzing;
- compiler crash detection;
- hang detection;
- resource exhaustion detection;
- reference-interpreter differential testing;
- compiler-vs-compiler differential testing;
- optimization differential testing;
- target differential testing;
- incremental-build differential testing;
- cache correctness testing;
- parallel-build testing;
- metamorphic testing;
- translation-validation fuzzing;
- pass-order fuzzing;
- analysis-invalidation fuzzing;
- coverage-guided generation;
- semantic coverage;
- corpus management;
- automatic minimization;
- automatic reproduction;
- automatic bisect;
- regression database;
- sanitizer integration;
- debugger/symbolication integration;
- AI-readable failure reports;
- deterministic distributed fuzzing;
- sandboxed fuzz workers.

---

## Kiến trúc tổng hợp sau 341

Đến đây Axiom bắt đầu có một vòng **tự kiểm tra compiler rất mạnh**:

```text
                  ┌──────────────────────┐
                  │    Axiom Compiler    │
                  └──────────┬───────────┘
                             │
                    generate / compile
                             │
                             ▼
                     Native Program
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
          Interpreter     Sanitizer       Runtime
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                       Semantic Oracle
                             │
                             ▼
                    Differential Testing
                             │
                             ▼
                     Failure / Success
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
             Minimize                  Coverage
                │                         │
                ▼                         ▼
           Reproducer                  New Seeds
                │                         │
                └────────────┬────────────┘
                             ▼
                       Regression DB
```

Điểm rất quan trọng:

**341 biến compiler thành một hệ thống có khả năng tự tìm lỗi của chính nó**, thay vì chỉ dựa vào hàng nghìn test viết tay.

Với mục tiêu cuối cùng là **Axiom tự host**, đây là nền tảng đặc biệt quan trọng: khi compiler chuyển từ bootstrap implementation sang compiler viết bằng chính Axiom, differential testing + reference interpreter + metamorphic testing + fuzzing sẽ là lớp bảo vệ chính chống **self-hosting regression và silent miscompilation**.