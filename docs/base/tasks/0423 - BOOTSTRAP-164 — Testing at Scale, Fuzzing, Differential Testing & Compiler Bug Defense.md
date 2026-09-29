# BOOTSTRAP-164 — Testing at Scale, Fuzzing, Differential Testing & Compiler Bug Defense
**STATUS: FROZEN / COMPLETED**

> **Compiler càng mạnh thì hệ thống kiểm thử càng phải mạnh hơn. Axiom không chấp nhận nguyên tắc “compiler chạy được vài chương trình mẫu”. Mọi tầng từ parser → semantic → MIR → optimizer → backend → linker phải có cơ chế phát hiện sai lệch độc lập.**

Mục tiêu lớn nhất:

```text
Nếu hai compilation configuration có cùng semantics
→ kết quả quan sát được phải tương đương.
```

---

# 1. Testing architecture

Đóng khung thành:

```text
                    Axiom Specification
                           │
                           ▼
                    Conformance Tests
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
     Semantic Tests    Compiler Tests    Toolchain Tests
          │                │                │
          ▼                ▼                ▼
      MIR Oracle       IR Tests         Binary Tests
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                  Differential Testing
                           │
                           ▼
                       Fuzzing
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      Frontend          Optimizer        Backend
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                     Minimization
                           │
                           ▼
                   Regression Corpus
```

---

# 2. Test không chỉ chạy binary

Axiom có nhiều tầng oracle.

```text
Source
 ↓
Tokens
 ↓
CST
 ↓
AST
 ↓
HIR
 ↓
Typed HIR
 ↓
MIR
 ↓
Verified MIR
 ↓
OptIR
 ↓
ABI MIR
 ↓
LIR
 ↓
Machine IR
 ↓
Object
 ↓
Binary
```

Mỗi tầng có thể có test riêng.

Điều này rất quan trọng vì nếu chỉ test executable cuối cùng, một bug ở optimizer rất khó định vị.

---

# 3. Test taxonomy

Chốt các loại:

```text
Unit
Integration
Conformance
Negative
Diagnostic
Snapshot
Property
Metamorphic
Fuzz
Differential
Stress
Performance
ABI
Cross-target
Bootstrap
Reproducibility
Security
```

---

# 4. Positive tests

Ví dụ:

```ax
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

phải:

- parse được;
- resolve được;
- type-check được;
- MIR hợp lệ;
- verifier chấp nhận;
- codegen thành công.

---

# 5. Negative tests

Ví dụ:

```ax
let x = value;
use(x);
use(x);
```

nếu `value` là non-Copy owning type thì phải tạo:

```text
E_USE_AFTER_MOVE
```

Không được:

- compiler crash;
- ICE;
- silently clone;
- generate binary sai.

---

# 6. Diagnostic tests

Diagnostic được test bằng:

```text
code
primary span
secondary spans
causal relationships
suggestions
```

Không test bằng cách phụ thuộc toàn bộ wording.

Ví dụ:

```text
E_CAPABILITY_CONFLICT
```

ổn định ngay cả khi câu giải thích thay đổi.

---

# 7. Snapshot tests

Các representation có thể snapshot:

```text
AST
HIR
MIR
Verified MIR
OptIR
ABI MIR
LIR
Machine IR
Object
Diagnostics
```

Nhưng snapshot không phải semantic oracle duy nhất.

---

# 8. Semantic reference interpreter

Axiom cần một:

```text
Axiom Semantic Interpreter
```

không tối ưu.

Pipeline:

```text
Source
 ↓
Typed HIR
 ↓
Reference MIR
 ↓
Interpreter
 ↓
Observable Result
```

Interpreter ưu tiên:

- đơn giản;
- dễ audit;
- deterministic;
- semantic fidelity.

Không cần nhanh.

---

# 9. Interpreter không phải compiler authority

Điểm này quan trọng.

```text
Specification
     │
     ├── Compiler
     └── Reference Interpreter
```

Cả hai phải tuân specification.

Không dùng:

```text
compiler behavior = specification
```

để tránh compiler tự xác nhận chính mình.

---

# 10. Observable result

Differential testing không so sánh raw machine bytes.

Có thể so:

```text
stdout
stderr
exit code
returned values
file outputs
explicit external effects
panic behavior
allocation contracts khi observable
```

và các observable ABI effects.

---

# 11. Undefined behavior không tồn tại trong safe semantics

Axiom phải phân biệt:

```text
Defined
Implementation-defined
Target-defined
Unsafe-contract-dependent
Invalid program
```

Không lấy:

```text
"compiler làm gì đó"
```

làm expected result cho chương trình invalid.

---

# 12. Metamorphic testing

Đây là một trong những cơ chế quan trọng nhất.

Nếu:

```ax
x + 0
```

và compiler có phép biến đổi hợp lệ thành:

```ax
x
```

thì kết quả phải tương đương.

Test không cần biết machine code chính xác.

---

# 13. Core metamorphic relation

Ví dụ:

```text
Program P
    ↓
Transform(P)
```

Nếu transformation được specification chứng minh semantics-preserving:

```text
Observe(P) == Observe(Transform(P))
```

---

# 14. Metamorphic transformations

Có thể tự động sinh:

### Dead-code insertion

```ax
let unused = 123;
```

### Identity arithmetic

```ax
x + 0
x * 1
```

chỉ khi semantics của kiểu cho phép.

### Redundant branch

```ax
if true {
    A
} else {
    B
}
```

### Equivalent control flow

```ax
if condition {
    return x;
}
return y;
```

so với dạng `match`/block tương đương.

---

# 15. Nhưng transformation phải type-aware

Không được tạo metamorphic rule kiểu:

```text
x * 1 == x
```

một cách mù quáng cho floating-point nếu semantics/NaN/signed-zero có thể khác.

Metamorphic engine phải biết:

```text
Type
FP mode
Overflow mode
Effects
Atomicity
Volatile
```

---

# 16. Optimization differential testing

Một chương trình:

```text
P
```

compile:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
-LTO
-PGO
```

Sau đó:

```text
Observe(P-O0)
==
Observe(P-O3)
```

trong phạm vi semantics cho phép.

---

# 17. Target differential testing

Cùng source:

```text
P
```

compile:

```text
x86-64
AArch64
RISC-V
WASM
```

Nếu chương trình không target-dependent:

```text
ObservableResult(target1)
==
ObservableResult(target2)
```

---

# 18. Target-dependent semantics

Nếu chương trình sử dụng:

```ax
@target_feature
extern
SIMD intrinsic
platform API
```

thì test oracle phải biết target dependency.

Không yêu cầu hai target có behavior giống nhau nếu specification cho phép khác biệt.

---

# 19. Compiler-vs-interpreter differential test

Pipeline mạnh nhất:

```text
Generated Source
       │
       ├──────────────► Reference Interpreter
       │                       │
       │                       ▼
       │                    Result A
       │
       └──► axc -O3 ──► Binary ──► Result B
                                      │
                                      ▼
                              Compare A/B
```

Nếu:

```text
A != B
```

→ compiler bug candidate.

---

# 20. O0 vs optimized differential

Thêm oracle thứ hai:

```text
Reference Interpreter
        │
   ┌────┴────┐
   ▼         ▼
  O0         O3
   │         │
   └────┬────┘
        ▼
    compare
```

Điều này đặc biệt mạnh để bắt optimization miscompilation.

---

# 21. MIR differential

Có thể interpret:

```text
Verified MIR
```

trực tiếp.

So:

```text
HIR interpreter
     vs
MIR interpreter
     vs
native binary
```

giúp xác định tầng lỗi.

---

# 22. Optimization pass verification

Mỗi optimization:

```text
Input IR
   ↓
Pass
   ↓
Output IR
```

phải có legality contract.

Test:

```text
Interpret(Input)
==
Interpret(Output)
```

trên test corpus phù hợp.

---

# 23. Optimization validation modes

Có thể có:

```text
--verify-passes
--verify-ir
--verify-each-pass
```

Development compiler có thể bật mạnh.

Release compiler không nhất thiết chạy toàn bộ vì chi phí.

---

# 24. IR verifier

Sau **mọi** transformation quan trọng:

```text
OptIR
 ↓
IRVerifier
```

kiểm tra:

- SSA;
- dominance;
- type;
- MemorySSA;
- CFG;
- references;
- block termination;
- instruction legality.

---

# 25. Backend verification

Machine IR verifier kiểm tra:

```text
register classes
physical register constraints
instruction operands
flags
memory operands
calling convention
stack frame
ABI
```

trước machine encoding.

---

# 26. Object verifier

Object writer output được kiểm tra:

```text
sections
symbols
relocations
alignment
flags
COMDAT
imports
exports
TLS
debug references
unwind metadata
```

---

# 27. Linker verifier

Final executable kiểm tra:

```text
entry point
symbol resolution
relocations
section ranges
segment permissions
imports/exports
TLS
unwind
debug BuildId
```

---

# 28. Fuzzer architecture

Không chỉ một fuzzer.

```text
                Fuzz Engine
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
  Source Fuzz    IR Fuzz      Binary/Obj Fuzz
      │             │             │
      ▼             ▼             ▼
   Frontend      Optimizer      Linker
```

---

# 29. Source fuzzer

Sinh:

```text
identifiers
types
expressions
patterns
generics
traits
closures
async
comptime
unsafe
FFI
GPU
```

theo grammar/type constraints.

---

# 30. Grammar-aware fuzzing

Random bytes không đủ.

Cần AST generator:

```text
GenType
GenExpr
GenPattern
GenStmt
GenFunction
GenTrait
GenImpl
GenModule
```

để phần lớn test đi qua parser.

---

# 31. Type-aware fuzzing

Ví dụ generator biết:

```text
x : Vec<i32>
```

thì có thể sinh:

```ax
x.length()
x[0]
view(x)
```

thay vì hàng nghìn chương trình vô nghĩa.

---

# 32. Ownership-aware fuzzing

Generator phải tạo cả:

```text
valid Move
invalid Move
valid Copy
invalid use-after-move
partial move
reinitialize
drop
view
mut_view
```

Đây là nơi Axiom có lợi thế lớn vì semantic rules rất rõ.

---

# 33. Capability-aware fuzzing

Sinh:

```text
view<T>
mut_view<T>
disjoint regions
overlapping regions
escaping views
views across await
```

và kiểm tra verifier.

---

# 34. Concurrency fuzzing

Không chỉ random source.

Có:

```text
deterministic scheduler
```

để thử các interleaving.

Ví dụ:

```text
Thread A: store
Thread B: load
```

thử nhiều thứ tự theo memory model.

---

# 35. Race testing

Safe code:

```text
must never
```

tạo data race.

Unsafe code:

```text
may
```

nhưng compiler phải không biến unsafe contract thành safe proof sai.

---

# 36. Async fuzzing

Sinh:

```text
await
spawn
spawn_local
cancel
drop future
wake
poll
nested future
```

và kiểm tra:

- state machine;
- Send;
- live-across-await;
- cancellation;
- Drop.

---

# 37. GPU fuzzing

Sinh kernel:

```text
@kernel
fn ...
```

với:

- address spaces;
- views;
- atomics;
- barriers;
- host/device transfer;
- invalid host capability use.

Compile-time GPU legality phải được fuzz.

---

# 38. FFI fuzzing

Sinh declarations:

```ax
extern "C" fn ...
```

với các combination:

- scalar;
- struct;
- repr(C);
- pointer;
- nullable pointer;
- variadic;
- calling convention.

ABI classifier phải chịu được.

---

# 39. Comptime fuzzing

Comptime đặc biệt nguy hiểm vì có thể tác động compiler.

Fuzzer phải kiểm tra:

```text
sandbox
resource limits
recursion limits
memory limits
timeout
dependency tracking
determinism
```

---

# 40. Compiler crash fuzzing

Mọi:

```text
panic
segfault
assert failure
OOM
ICE
deadlock
timeout
```

đều là fuzz finding.

Phân biệt:

```text
user compile error
```

với:

```text
compiler defect
```

---

# 41. Timeout classification

Một chương trình fuzz có thể:

```text
compile forever
```

Đây không nhất thiết là semantic bug nhưng là compiler robustness bug.

Phân loại:

```text
CRASH
HANG
OOM
MISCOMPILE
WRONG_DIAGNOSTIC
NONDETERMINISM
```

---

# 42. Determinism fuzzer

Compile cùng source N lần:

```text
P
P
P
P
```

với cùng config.

Compare:

```text
diagnostics
IR
object
binary
```

trong reproducible mode.

---

# 43. Parallel-vs-serial test

Một test cực quan trọng:

```text
--jobs=1
```

so với:

```text
--jobs=all
```

Phải:

```text
semantic result == semantic result
```

và reproducible artifact nếu profile yêu cầu.

---

# 44. Cache-vs-clean test

```text
clean build
```

so với:

```text
incremental build
```

và:

```text
cache-hit build
```

phải tương đương.

Đây là invariant cực quan trọng cho compiler lớn.

---

# 45. Bootstrap differential

Compiler Axiom:

```text
axc1
```

compile compiler source:

```text
compiler.ax
```

thành:

```text
axc2
```

Sau đó:

```text
axc2
```

compile chính source đó thành:

```text
axc3
```

So sánh behavior:

```text
axc1
axc2
axc3
```

---

# 46. Three-stage bootstrap test

Đóng thành CI test:

```text
axc1 → axc2
axc2 → axc3
axc3 → axc4
```

Nếu:

```text
axc3 ≠ axc4
```

về semantic behavior → investigate.

Không nhất thiết binary byte-for-byte giống nhau.

---

# 47. Compiler self-hosting trust

Có thể thêm:

```text
Stage N compiler
    ↓
compile itself
    ↓
Stage N+1
    ↓
compile itself
```

để phát hiện:

- compiler bootstrap bug;
- nondeterminism;
- miscompilation;
- missing dependency.

---

# 48. Fuzz corpus

Mỗi bug được minimize thành:

```text
tests/regression/
```

Ví dụ:

```text
E_USE_AFTER_MOVE_001.ax
E_CAPABILITY_CONFLICT_017.ax
OPT_MISCOMPILE_0042.ax
ABI_AARCH64_008.ax
LINK_ELF_0019.ax
```

---

# 49. Regression forever

Một compiler bug đã sửa:

```text
must never disappear from test suite
```

Mỗi regression test trở thành permanent protection.

---

# 50. Automatic minimization

Fuzzer tìm:

```text
10,000-line program
```

nhưng bug thực tế chỉ cần:

```text
17 lines
```

Minimizer phải thử:

```text
remove statement
remove expression
remove declaration
remove type
remove generic
remove module
simplify literal
reduce nesting
```

cho đến khi vẫn reproduce.

---

# 51. Delta debugging

Có thể dùng:

```text
Program
 ↓
remove half
 ↓
still reproduces?
 ↓ yes
remove half again
```

sau đó AST-aware minimization.

---

# 52. Preserve failure class

Minimizer không chỉ giữ:

```text
compiler crash
```

mà giữ đúng:

```text
MISCOMPILE
```

nếu original là miscompilation.

Không được minimize thành một crash khác.

---

# 53. Semantic shrinking

Ví dụ:

```text
Vec<HashMap<String, Option<T>>>
```

có thể shrink thành:

```text
Vec<T>
```

nếu vẫn reproduce.

Đây là lý do AST/type-aware fuzzing tốt hơn byte fuzzing.

---

# 54. Fuzz seeds

Seed corpus lấy từ:

```text
language specification
standard library
real projects
regression corpus
hand-written edge cases
random generator
```

---

# 55. Coverage

Theo dõi coverage ở nhiều tầng:

```text
source syntax coverage
semantic rule coverage
MIR instruction coverage
optimization pass coverage
backend instruction coverage
diagnostic coverage
```

Không chỉ line coverage của compiler source.

---

# 56. Semantic coverage

Ví dụ:

```text
Move
Copy
PartialMove
Drop
View
MutView
Send
Share
Await
Unsafe
FFI
```

mỗi rule phải có positive + negative coverage.

---

# 57. Optimization coverage

Ví dụ vectorizer:

```text
vectorized
not-vectorized
unknown-alias
known-noalias
reduction
remainder
masked
strict-FP
atomic
volatile
```

đều phải có test.

---

# 58. Explainable optimization tests

Nếu test mong đợi vectorization:

```text
assert:
vectorizer decision = Vectorized
```

Nếu không vectorize:

```text
assert:
reason = LoopCarriedDependency
```

hoặc:

```text
UnknownAlias
```

Điều này rất hữu ích cho AI/compiler development.

---

# 59. Optimization remarks as test oracle

Có thể có:

```text
axc test --optimization-remarks
```

Ví dụ:

```text
PASS vectorize loop 3
REASON proven-independent-memory
WIDTH 8
```

---

# 60. Negative optimization tests

Không chỉ test compiler tối ưu thành công.

Phải test compiler **không tối ưu sai**.

Ví dụ:

```text
unknown alias
```

không được tự động biến thành:

```text
NO_ALIAS
```

---

# 61. Security regression corpus

Các lỗi:

```text
out-of-bounds
use-after-move
double-drop
invalid provenance
race
packed misalignment
integer overflow
FFI ABI mismatch
```

phải có regression tests.

---

# 62. Constant-time tests

Nếu Axiom có security contract:

```text
@constant_time
```

thì compiler test phải kiểm tra:

```text
secret-dependent branch
secret-dependent memory access
secret-dependent optimization
```

theo contract đã định nghĩa.

---

# 63. ABI conformance suite

Mỗi target ABI cần suite:

```text
integers
floats
structs
nested structs
arrays
enums
transparent newtypes
returns
sret
variadic
SIMD
alignment
TLS
```

---

# 64. FFI golden tests

Test Axiom ↔ C ABI với các compiler/platform reference implementation khi bootstrap.

Sau khi Axiom self-host:

```text
Axiom object
↔
external C ABI
```

vẫn phải pass.

---

# 65. Object/linker golden tests

Có binary fixtures:

```text
ELF
PE/COFF
Mach-O
WASM
```

với expected:

```text
sections
symbols
relocations
entry
imports
exports
```

Không phụ thuộc timestamp/random ordering.

---

# 66. Binary semantic test

Không chỉ byte comparison.

Ví dụ ELF relocation khác nhau nhưng loader behavior giống nhau vẫn có thể hợp lệ.

Do đó test:

```text
Object semantics
```

và riêng:

```text
Reproducible bytes
```

---

# 67. Reproducible-build test

Nếu bật:

```text
--reproducible
```

thì:

```text
build machine A
build machine B
```

với cùng inputs phải tạo artifact tương đương theo contract, và nơi contract yêu cầu thì byte-identical.

---

# 68. Cross-compiler differential testing

Trong bootstrap:

```text
Axiom compiler
LLVM/Clang reference
reference interpreter
```

có thể dùng để đối chiếu trong phạm vi semantics chung.

Không coi LLVM là specification.

---

# 69. Differential testing hierarchy

Chốt thứ tự tin cậy:

```text
Specification
     ↓
Reference semantic model
     ↓
Independent verifier
     ↓
Compiler
     ↓
Optimization
     ↓
Profile / heuristic
```

Compiler không được tự nâng behavior của mình thành specification.

---

# 70. Compiler bug triage

Mỗi failure phân loại:

```text
PARSER
RESOLVER
TYPE
TRAIT
COMPTIME
MIR
VERIFIER
ALIAS
EFFECT
ESCAPE
OPTIMIZER
ABI
LIR
BACKEND
OBJECT
LINKER
RUNTIME
TOOLING
```

---

# 71. Severity

Đề xuất:

```text
S0 — compiler produces incorrect/unsafe program
S1 — compiler crash or corrupted artifact
S2 — deterministic wrong diagnostic / severe performance regression
S3 — tooling/debugging defect
S4 — minor UX/test issue
```

S0 đặc biệt nghiêm trọng.

---

# 72. Miscompilation is highest-priority defect

Ví dụ:

```text
Source semantics = 42
Binary returns 41
```

đây không phải:

```text
optimization issue
```

mà là:

```text
compiler correctness failure
```

và phải chặn release nếu thuộc supported semantics.

---

# 73. Compiler correctness gate

Release compiler phải pass:

```text
conformance
regression
fuzz smoke
differential
ABI
cross-target
bootstrap
reproducibility
```

theo target/profile được công bố.

---

# 74. Continuous fuzzing

Không chỉ CI.

Có thể chạy:

```text
nightly source fuzz
nightly MIR fuzz
nightly optimizer fuzz
nightly backend fuzz
nightly linker fuzz
```

và tự động đưa minimized reproducer vào corpus.

---

# 75. Fuzz result artifact

Mỗi finding lưu:

```text
FuzzFinding {
    id
    seed
    minimized_source
    failure_class
    compiler_version
    target
    profile
    optimization
    stack_trace
    IR_snapshots
    diagnostic
    reproduction_command
}
```

---

# 76. AI-native bug investigation

Vì Axiom đã có compiler provenance, AI có thể nhận:

```text
axc explain failure BUG-00421
```

và lấy:

```text
source
→ HIR
→ MIR
→ verifier facts
→ optimization pass
→ transformed IR
→ machine
```

để tìm nơi semantics bị thay đổi.

---

# 77. Automatic bisection

Nếu:

```text
commit A = pass
commit B = fail
```

compiler CI có thể tự động:

```text
git bisect
```

và chạy minimized reproducer.

---

# 78. Optimization pass bisection

Không chỉ git commit.

Có thể disable từng pass:

```text
-O3
-O3 -fno-vectorize
-O3 -fno-sroa
-O3 -fno-gvn
```

để xác định pass gây lỗi.

Compiler developer không phải đoán.

---

# 79. Pass replay

Lưu:

```text
Input IR
Pass configuration
Target
```

để reproduce chính xác optimization failure.

Ví dụ:

```text
axc replay-opt bug-00421
```

---

# 80. Frozen invariants

### `ATEST2-20`
Every supported semantic rule has conformance coverage.

### `ATEST2-21`
Invalid programs must not silently compile as valid programs.

### `ATEST2-22`
Compiler diagnostics have stable machine-readable identities.

### `ATEST2-23`
Reference semantic execution is available for differential validation.

### `ATEST2-24`
Reference execution is independent from optimizing code generation.

### `ATEST2-25`
Compiler behavior is not itself the language specification.

### `ATEST2-26`
Metamorphic transformations may validate semantics-preserving compiler behavior.

### `ATEST2-27`
Metamorphic rules must respect type, effect, floating-point, atomic and observable semantics.

### `ATEST2-28`
Optimization output must preserve observable semantics.

### `ATEST2-29`
O0 and optimized builds must be semantically equivalent.

### `ATEST2-30`
Valid cross-target programs must preserve target-independent semantics.

### `ATEST2-31`
MIR has an independent structural verifier.

### `ATEST2-32`
Optimized IR has an independent verifier.

### `ATEST2-33`
Machine IR has an independent verifier.

### `ATEST2-34`
Object files have structural validation.

### `ATEST2-35`
Final binaries have structural/link validation.

### `ATEST2-36`
Source fuzzing is grammar-aware.

### `ATEST2-37`
Source fuzzing may be type-aware and ownership-aware.

### `ATEST2-38`
MIR fuzzing is supported independently from source fuzzing.

### `ATEST2-39`
Optimization passes are fuzzable independently.

### `ATEST2-40`
Backend and object/linker components are independently fuzzable.

### `ATEST2-41`
Compiler crashes are distinct from user compilation errors.

### `ATEST2-42`
Compiler hangs and resource exhaustion are testable failure classes.

### `ATEST2-43`
Miscompilation is explicitly detectable.

### `ATEST2-44`
Miscompilation has higher correctness severity than ordinary compiler diagnostics.

### `ATEST2-45`
Fuzz failures are automatically minimized where possible.

### `ATEST2-46`
Minimization preserves the original failure class.

### `ATEST2-47`
Every confirmed compiler bug becomes a regression test.

### `ATEST2-48`
Regression tests persist across compiler releases.

### `ATEST2-49`
Compiler reproducibility is continuously tested.

### `ATEST2-50`
Serial and parallel compilation must be semantically equivalent.

### `ATEST2-51`
Clean and incremental compilation must be semantically equivalent.

### `ATEST2-52`
Cached and uncached compilation must be semantically equivalent.

### `ATEST2-53`
Bootstrap stages must remain semantically compatible.

### `ATEST2-54`
Compiler nondeterminism is detectable.

### `ATEST2-55`
Optimization decisions can be tested independently from optimization results.

### `ATEST2-56`
Optimization remarks can serve as diagnostic/test evidence.

### `ATEST2-57`
Negative optimization tests verify that unsafe transformations are rejected.

### `ATEST2-58`
Ownership, capability and concurrency rules receive adversarial testing.

### `ATEST2-59`
Unsafe boundaries receive dedicated regression and fuzz coverage.

### `ATEST2-60`
Comptime sandbox and resource limits are fuzz-tested.

### `ATEST2-61`
Async state-machine transformations are differential-tested.

### `ATEST2-62`
GPU legality and generated kernels are independently tested.

### `ATEST2-63`
FFI and ABI behavior has target-specific conformance suites.

### `ATEST2-64`
Object and linker output has target-specific conformance suites.

### `ATEST2-65`
Security-sensitive compiler transformations have dedicated regression suites.

### `ATEST2-66`
Constant-time/security contracts are tested separately from ordinary optimization.

### `ATEST2-67`
Compiler failures can be traced across source, IR, optimization and machine provenance.

### `ATEST2-68`
Optimization failures can be isolated by pass replay/bisection.

### `ATEST2-69`
Compiler release gates include correctness, conformance and robustness validation.

### `ATEST2-70`
Fuzzing infrastructure is capable of continuously extending the regression corpus.

### `ATEST2-71`
Semantic test results are independent of worker scheduling.

### `ATEST2-72`
Semantic test results are independent of cache state.

### `ATEST2-73`
Semantic test results are independent of optimization level when the same semantics are requested.

### `ATEST2-74`
Compiler test infrastructure must not silently weaken language guarantees.

### `ATEST2-75`
AI tooling can consume structured compiler-test evidence.

### `ATEST2-76`
A compiler release cannot claim correctness beyond its tested target/profile scope.

### `ATEST2-77`
Reference models, verifiers and fuzzers are separate correctness defenses.

### `ATEST2-78`
No single compiler subsystem is trusted to validate itself completely.

### `ATEST2-79`
Confirmed miscompilation must preserve a reproducible minimal test case whenever feasible.

### `ATEST2-80`
Axiom compiler correctness is treated as a continuously tested property, not a one-time milestone.

---

# Trạng thái Axiom hiện tại

Sau BOOTSTRAP-164, kiến trúc đã có một đặc điểm rất quan trọng:

```text
                    ┌───────────────┐
                    │ Specification │
                    └───────┬───────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
        Reference Semantics       Conformance
                 │                     │
                 └──────────┬──────────┘
                            ▼
                      Compiler
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
           Verifier      Optimizer      Backend
              │             │             │
              └─────────────┼─────────────┘
                            ▼
                         Fuzzer
                            │
                            ▼
                       Regression
```

Điều này tạo thành **trust architecture** chứ không chỉ là test suite.

Đặc biệt, Axiom hiện đã tránh được một vấn đề rất phổ biến của compiler tự xây: **compiler vừa là implementation vừa vô tình trở thành specification**.

---

# BOOTSTRAP-165 — Standard Library Architecture & Core API Design

Bước tiếp theo nên chuyển từ compiler infrastructure sang **thiết kế API thực tế của Axiom Standard Library**, bởi vì đến thời điểm này semantic foundation đã đủ mạnh.

Mục tiêu:

```text
Axiom Core
    ↓
std::core
    ↓
std::alloc
    ↓
std::collections
    ↓
std::string
    ↓
std::io
    ↓
std::fs
    ↓
std::net
    ↓
std::sync
    ↓
std::thread
    ↓
std::async
    ↓
std::os
    ↓
std::gpu
    ↓
std::ffi
```

Task 165 sẽ đặc biệt giải quyết một vấn đề quan trọng: **làm sao Standard Library vừa đủ mạnh để xây application/game/AI/system software, nhưng không biến Axiom thành ngôn ngữ có một “runtime khổng lồ” và hàng đống abstraction bắt buộc.**