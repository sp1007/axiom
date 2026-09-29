# BOOTSTRAP-122 — Compiler Verification, Conformance & Adversarial Test Architecture

**Trạng thái: FROZEN / COMPLETED**

Mục tiêu của task này là biến Axiom từ một language specification thành một hệ thống có thể **chứng minh compiler đang thực hiện đúng specification**.

Nguyên tắc trung tâm:

> **Một semantic rule chưa có executable test thì chưa được coi là hoàn thiện.**

Và quan trọng hơn:

> **Compiler test phải kiểm tra semantic result, không chỉ kiểm tra compiler có crash hay chương trình có chạy.**

---

# 1. Verification architecture

Toàn bộ hệ thống test:

```text
                         Axiom Specification
                                  │
                                  ↓
                         Conformance Rules
                                  │
              ┌───────────────────┼───────────────────┐
              ↓                   ↓                   ↓
        Positive Tests       Negative Tests      Metamorphic Tests
              │                   │                   │
              └───────────────────┼───────────────────┘
                                  ↓
                         Compiler Test Runner
                                  │
          ┌───────────────────────┼────────────────────────┐
          ↓                       ↓                        ↓
     Frontend Tests          MIR Tests               Backend Tests
          │                       │                        │
          ↓                       ↓                        ↓
     Type/Traits            Verification             Machine Code
          │                       │                        │
          └───────────────────────┼────────────────────────┘
                                  ↓
                         Runtime Execution
                                  ↓
                         Oracle / Expected Result
```

---

# 2. Bốn loại correctness

Axiom phân biệt:

| Loại | Câu hỏi |
|---|---|
| Language correctness | Chương trình có đúng theo spec? |
| Compiler correctness | Compiler có giữ nguyên semantics? |
| Backend correctness | Machine code có tương đương semantic program? |
| Runtime/platform correctness | Runtime/system layer có thực hiện đúng contract? |

Không được dùng một loại test thay thế loại khác.

---

# 3. Test taxonomy

Axiom có các lớp:

```text
tests/
├── lexer/
├── parser/
├── resolver/
├── types/
├── traits/
├── comptime/
├── ownership/
├── capability/
├── async/
├── concurrency/
├── gpu/
├── ffi/
├── mir/
├── optimizer/
├── abi/
├── backend/
├── object/
├── linker/
├── runtime/
├── std/
├── diagnostics/
├── cross_target/
├── fuzz/
└── bootstrap/
```

---

# 4. Positive test

Chương trình hợp lệ:

```ax
fn add(a: i32, b: i32) -> i32 {
    a + b
}

fn main() {
    assert(add(2, 3) == 5);
}
```

Expected:

```text
compile = success
run = success
exit = 0
```

---

# 5. Negative test

Chương trình sai:

```ax
fn main() {
    let x: i32 = "hello";
}
```

Expected:

```text
compile = failure
diagnostic = ETYPE_MISMATCH
```

Không chỉ kiểm tra:

```text
compiler returned non-zero
```

mà phải kiểm tra **đúng semantic error**.

---

# 6. Diagnostic conformance

Negative test có thể chứa:

```text
// expect-error: ETYPE_MISMATCH
// expect-error-at: 4:17
```

Test runner xác nhận:

```text
error code
source location
primary span
relevant secondary spans
```

Không bắt buộc message wording phải bất biến.

---

# 7. Stable diagnostic codes

Diagnostic code là API compiler:

```text
ETYPE_MISMATCH
ETRAIT_NOT_IMPLEMENTED
EOWN_USE_AFTER_MOVE
EOWN_DOUBLE_DROP
ECAP_CONFLICT
ECAP_DANGLING
EASYNC_BORROW_ACROSS_AWAIT
EUNSAFE_PRECONDITION
```

Text message có thể cải thiện mà không phá test.

---

# 8. Snapshot diagnostics

Có thể có snapshot:

```text
tests/diagnostics/foo.stderr
```

nhưng snapshot không phải semantic oracle duy nhất.

Test vẫn phải kiểm tra:

```text
error code
severity
span
```

Snapshot chỉ kiểm tra presentation.

---

# 9. Semantic oracle

Có ba loại oracle:

```text
Compile Oracle
Execution Oracle
IR Oracle
```

Ví dụ:

```text
Compile Oracle:
    must compile

Execution Oracle:
    stdout = "42"

IR Oracle:
    function contains exactly one Drop
```

---

# 10. MIR conformance

Axiom phải có khả năng:

```bash
axc inspect mir test.ax
```

và:

```bash
axc inspect verified-mir test.ax
```

Test có thể assert:

```text
MOVE x
DROP y
MAKE_VIEW
DROP_CAPABILITY
```

---

# 11. Không test machine instruction quá sớm

Không nên viết:

```text
expect:
    mov rax, rbx
    add rax, rcx
```

cho semantic test.

Machine instruction phụ thuộc target/optimization.

Semantic test nên dừng ở:

```text
MIR / ABI MIR
```

Backend test mới kiểm tra instruction-level behavior.

---

# 12. Semantic equivalence test

Ví dụ:

```ax
let x = a + b;
```

và:

```ax
let x = add(a, b);
```

nếu language semantics quy định tương đương, có thể kiểm tra:

```text
Typed HIR semantic fingerprint
```

hoặc execution result.

---

# 13. Metamorphic testing

Đây là thành phần rất quan trọng.

Thay vì chỉ:

```text
input → expected output
```

ta test:

```text
program P
   ↓ transformation
program P'
   ↓
semantic result(P) == semantic result(P')
```

---

# 14. Ví dụ metamorphic optimization test

```ax
let x = 2 + 3;
```

Compiler:

```text
-O0
-O2
-O3
-Os
```

phải cho cùng observable semantics.

---

# 15. Optimization correctness

Test:

```text
Program
   ↓
-O0 executable
   ↓
observable result A

Program
   ↓
-O3 executable
   ↓
observable result B
```

phải:

```text
A == B
```

trừ những behavior explicitly unspecified.

---

# 16. Undefined behavior không được làm oracle

Axiom Core cố tình giảm UB.

Do đó test suite phải phân loại:

```text
Defined
Implementation-defined
Target-defined
Unspecified
Unsafe-contract-dependent
Invalid
```

Không dùng undefined behavior để kiểm tra compiler optimization.

---

# 17. Ownership conformance

Mỗi ownership rule cần positive + negative test.

Ví dụ:

```ax
let a = Buffer.new();
let b = a;
use(b);
```

positive.

Và:

```ax
let a = Buffer.new();
let b = a;
use(a);
```

negative:

```text
EOWN_USE_AFTER_MOVE
```

---

# 18. Partial move tests

```ax
struct User {
    id: i32,
    name: String,
}
```

Test:

```ax
let name = user.name;
use(user.id);
```

→ valid nếu User cho partial move.

Nhưng:

```ax
drop(user);
```

→ invalid nếu custom Drop hoặc toàn-object ownership không còn hợp lệ.

---

# 19. Drop exactly-once tests

Type test:

```ax
struct Tracker {
    ...
    fn drop(self) { counter += 1; }
}
```

Program tạo/move/return/branch.

Oracle:

```text
counter == number_of_owned_instances
```

Không được:

```text
double drop
leak semantic Drop
```

---

# 20. Capability tests

Ví dụ:

```ax
let a = view(x);
let b = view(x);
```

→ valid.

Nhưng:

```ax
let a = view(x);
let b = mut_view(x);
```

nếu cả hai sống đồng thời:

→ reject.

---

# 21. Last-use tests

Đây là test bắt buộc để bảo đảm Axiom không quá restrictive.

```ax
let v = view(x);
read(v);

mutate(x);
```

Nếu `v` không còn dùng:

```text
must compile
```

Test này rất quan trọng.

Nếu compiler chỉ dùng lexical scope:

```text
mutate(x)
```

sẽ bị reject sai.

---

# 22. Relocation tests

```ax
let v = view(vec);
vec.push(x);
use(v);
```

→ reject nếu `push` có thể relocate.

Nhưng:

```ax
let v = view(vec);
use(v);
vec.push(x);
```

→ compile.

---

# 23. Disjoint-region tests

```ax
fn f(a: mut_view<i32>, b: mut_view<i32>) {}

f(mut_view(x.a), mut_view(x.b));
```

phải compile nếu fields được chứng minh disjoint.

Đây là regression test cho field-sensitive capability analysis.

---

# 24. Unknown overlap tests

```ax
f(
    mut_view(array[i]),
    mut_view(array[j])
);
```

Nếu compiler không chứng minh `i != j`:

```text
must reject
```

Không được tự động assume disjoint.

---

# 25. Unsafe tests

Test unsafe phải kiểm tra cả hai phía:

```text
unsafe operation accepted
```

và:

```text
safe state after unsafe boundary still verified
```

Ví dụ unsafe tạo capability với invalid provenance phải không được âm thầm biến thành safe valid capability.

---

# 26. Trait solver tests

Mỗi trait solver feature cần:

```text
success
failure
ambiguity
cycle
overflow
coherence
specialization
associated-type normalization
```

---

# 27. Trait cycle test

```text
trait A: B {}
trait B: A {}
```

Expected:

```text
ETRAIT_CYCLE
```

Không:

```text
compiler hang
stack overflow
ICE
```

---

# 28. Trait ambiguity test

Hai implementation có thể cùng match:

```text
impl<T> Trait for Wrapper<T>
impl Trait for Wrapper<i32>
```

nếu specialization rules không cho phép:

```text
ETRAIT_OVERLAP
```

---

# 29. Trait solver termination fuzzing

Generate random:

```text
traits
generic types
where clauses
associated types
nested applications
```

Compiler phải luôn:

```text
success
diagnostic
or bounded solver failure
```

Không được treo.

---

# 30. Parser fuzzing

Input:

```text
random bytes
random Unicode
deep nesting
invalid UTF-8
large identifiers
large literals
```

Compiler phải:

```text
diagnostic
```

hoặc reject input.

Không:

```text
segmentation fault
memory corruption
infinite loop
```

---

# 31. Compiler crash taxonomy

Test runner phân biệt:

```text
USER_ERROR
UNSUPPORTED
COMPILER_ERROR
INTERNAL_COMPILER_ERROR
CRASH
TIMEOUT
OOM
```

Trong đó:

```text
ICE != user compile error
```

---

# 32. Compiler ICE

Compiler bug:

```text
ICE0001
```

phải tạo:

```text
compiler version
target
source fingerprint
compiler phase
query stack
repro command
```

Không expose internal stack trace cho ordinary user mặc định.

---

# 33. Fuzzing layers

Axiom fuzzing:

```text
Lexer fuzz
Parser fuzz
Resolver fuzz
Type fuzz
Trait fuzz
Comptime fuzz
MIR fuzz
Optimizer fuzz
Object writer fuzz
Linker fuzz
```

---

# 34. Differential compiler testing

Trong bootstrap:

```text
Axiom compiler
      ↓
reference backend
```

có thể so sánh với:

```text
LLVM/reference implementation
```

nhưng:

> **LLVM không phải semantic authority của Axiom.**

Nó chỉ là validation oracle trong bootstrap.

---

# 35. Differential execution

Cùng một Axiom program:

```text
Axiom → LLVM backend
Axiom → Axiom backend
```

chạy cùng test inputs.

So sánh observable result.

Nếu:

```text
result_A != result_B
```

→ compiler investigation.

---

# 36. Random program generation

Fuzzer tạo:

```text
valid AST
```

thay vì chỉ random bytes.

Ví dụ generator biết:

```text
Type
Expression
Statement
Pattern
Generic
Trait
Ownership
```

nên có thể tạo chương trình sâu hơn parser fuzz.

---

# 37. Typed fuzzing

Advanced generator:

```text
generate Type
   ↓
generate expression : Type
   ↓
generate valid program
```

Sau đó mutation có thể cố ý phá:

```text
ownership
trait bounds
capabilities
```

---

# 38. Mutation testing

Test suite được kiểm tra ngược.

Compiler developer cố tình thay:

```text
Copy → Move
```

hoặc:

```text
READ+WRITE conflict → allowed
```

Test suite phải fail.

Nếu mutation không làm test fail:

> coverage chưa đủ.

---

# 39. Specification coverage

Không chỉ:

```text
line coverage = 90%
```

Axiom cần:

```text
semantic rule coverage
```

Ví dụ:

```text
AOWN-82 → tests/ownership/copy_*.ax
ACAP-88 → tests/capability/relocation_*.ax
ATYPE-90 → tests/types/no_implicit_conversion_*.ax
```

---

# 40. Invariant-to-test mapping

Mỗi invariant:

```text
ATYPE-80
```

phải có metadata:

```text
tests:
    types/nominal_001.ax
    types/nominal_002.ax
```

Compiler repository có thể query:

```bash
axc test --invariant ATYPE-80
```

---

# 41. Test manifest

Ví dụ conceptually:

```text
test {
    name = "use-after-move";
    source = "ownership/use_after_move.ax";
    mode = compile_fail;

    expect_error = "EOWN_USE_AFTER_MOVE";
}
```

Không nên nhúng quá nhiều testing semantics vào source syntax.

---

# 42. Execution sandbox

Tests có thể:

```text
run executable
```

nhưng phải sandbox:

```text
filesystem
network
environment
process creation
time
randomness
```

nếu test không yêu cầu.

---

# 43. Deterministic tests

Test có nondeterminism phải explicit:

```text
requires:
    time
    random
    network
    threads
```

Test runner biết capability đó.

---

# 44. Concurrency testing

Concurrency test không thể chỉ chạy một lần.

Runner có:

```text
iterations
scheduler_seed
stress_level
timeout
```

Ví dụ:

```bash
axc test --stress concurrency --iterations 10000
```

---

# 45. Deterministic scheduler

Runtime test profile nên có:

```text
deterministic scheduler
```

cho:

```text
thread
fiber
async task
channel
mutex
atomic
```

Mục tiêu:

> biến nhiều race/interleaving thành reproducible test cases.

---

# 46. Race testing

Safe Axiom code:

```text
must never produce data race
```

Unsafe/system code:

```text
sanitizer / stress tooling
```

có thể phát hiện violations.

---

# 47. Memory sanitizer architecture

Axiom tooling có thể cung cấp:

```text
ASan-like
UBSan-like
TSan-like
```

nhưng semantics compiler không phụ thuộc sanitizer.

Sanitizer instrumentation là optional build profile.

---

# 48. Async tests

Phải test:

```text
await
multiple await
Future drop
cancellation
spawn
spawn_local
migration
Send
waker
channel
I/O
```

Đặc biệt:

```text
Drop(Future)
```

không được ngầm coi là external cancellation.

---

# 49. GPU tests

GPU test matrix:

```text
host compilation
kernel legality
host/device ownership
device capability
atomic
barrier
race
transfer
event
kernel failure
```

Có CPU reference implementation cho nhiều primitive để differential test.

---

# 50. FFI tests

Test:

```text
C ABI
System ABI
calling convention
struct layout
repr(C)
transparent
packed
alignment
pointer
string
callback
allocator ownership
panic boundary
```

---

# 51. ABI golden tests

Ví dụ:

```ax
@repr(C)
struct Point {
    x: f32,
    y: f32,
}
```

Golden metadata:

```text
size
alignment
field offsets
calling convention
return classification
```

chỉ cố định khi `repr` contract yêu cầu.

---

# 52. Không golden-test default layout

Không được test:

```text
default struct:
    offset x = 0
    offset y = 8
```

vĩnh viễn.

Compiler có quyền thay đổi layout mặc định.

Test chỉ kiểm tra semantic behavior.

---

# 53. Object writer tests

Object tests kiểm tra:

```text
sections
symbols
relocations
COMDAT
TLS
debug
unwind
```

Không cần execute.

---

# 54. Linker tests

Link tests:

```text
strong symbol
weak symbol
duplicate symbol
archive extraction
dead stripping
imports
exports
TLS
PIE/PIC
shared library
```

---

# 55. Binary reproducibility

Cùng:

```text
source
compiler
target
dependencies
configuration
```

phải tạo:

```text
same semantic build identity
```

và reproducible profile hướng tới:

```text
byte-identical artifact
```

---

# 56. Build graph tests

Test:

```text
dependency invalidation
interface fingerprint
implementation fingerprint
cache hit
cache miss
comptime dependency
target-specific dependency
feature resolution
offline mode
vendoring
```

---

# 57. Cache correctness

Quan trọng:

> Cache hit không được tạo kết quả khác cache miss.

Test:

```text
clean build → A
cached build → B
```

phải:

```text
semantic fingerprint(A) == semantic fingerprint(B)
```

và execution behavior equivalent.

---

# 58. Bootstrap tests

Ba compiler:

```text
axc1
axc2
axc3
```

Build:

```text
axc1 → axc2
axc2 → axc3
axc3 → axc4
```

Kiểm tra:

```text
compiler self-build
```

không drift semantics.

---

# 59. Three-way bootstrap

Mỗi release bootstrap test:

```text
Seed Compiler
      ↓
Compiler A
      ↓
Compiler B
      ↓
Compiler C
```

So sánh:

```text
compiler behavior
public metadata
test suite
```

và trong reproducible configuration:

```text
binary identity
```

nếu mục tiêu deterministic build đạt được.

---

# 60. Compiler determinism

Hai lần:

```text
axc build
```

với cùng input phải cho cùng semantic result.

Không phụ thuộc:

```text
thread scheduling
hash iteration order
filesystem ordering
memory addresses
```

---

# 61. Randomized compiler testing

Compiler có thể có internal randomized algorithms để tìm bug.

Nhưng seed phải:

```text
recorded
replayable
```

Ví dụ:

```text
AXC_TEST_SEED=12345
```

---

# 62. Regression database

Mọi compiler bug được sửa phải tạo:

```text
regression test
```

Ví dụ:

```text
bugs/
    000123/
        input.ax
        expected.json
        README
```

Không cho bug quay lại.

---

# 63. Minimization

Fuzzer failure phải được minimize:

```text
10 MB program
      ↓
120 KB
      ↓
3 KB
```

thành test case nhỏ nhất tái hiện lỗi.

Compiler nên có:

```bash
axc fuzz minimize crash.ax
```

---

# 64. Performance regression

Correctness chưa đủ.

Benchmarks:

```text
compile time
memory usage
incremental build
trait solving
MIR verification
optimization
codegen
linking
binary size
runtime performance
```

---

# 65. Performance budget

Không nên khóa absolute numbers quá sớm.

Thay vào đó:

```text
baseline
threshold
trend
```

Ví dụ:

```text
trait_solver benchmark
    regression threshold = +10%
```

---

# 66. Compile-time adversarial tests

Các chương trình cố tình gây:

```text
deep generic nesting
trait explosion
huge match
large comptime recursion
large AST
large Unicode identifiers
many imports
```

Compiler phải fail gracefully hoặc hoàn thành trong bounded resource policy.

---

# 67. Resource limits

Compiler driver có thể hỗ trợ:

```text
max_memory
max_time
max_trait_depth
max_comptime_steps
max_recursion
max_output_size
```

Khi vượt:

```text
structured diagnostic
```

Không crash.

---

# 68. Security tests

Compiler input được coi là untrusted.

Fuzz:

```text
malformed object
malformed axmeta
malformed package metadata
malformed archive
malformed debug info
malformed comptime output
```

Không được:

```text
arbitrary code execution
memory corruption
```

ngoài capability explicitly authorized.

---

# 69. Comptime testing

Comptime phải test:

```text
sandbox
capability restrictions
reproducibility
dependency tracking
cache
generated code
generated declaration verification
resource limits
```

Ví dụ generated code có ownership violation:

```text
must be rejected
```

Comptime không bypass compiler verifier.

---

# 70. Generated-code tests

Pipeline:

```text
comptime
 ↓
generated HIR
 ↓
normal resolution
 ↓
normal typing
 ↓
normal ownership
 ↓
normal verification
```

Không có:

```text
generated code = trusted
```

---

# 71. Reference interpreter

Axiom nên có một:

> **Semantic Reference Interpreter**

đơn giản, chậm, nhưng dễ kiểm chứng.

Pipeline:

```text
Typed HIR / MIR
      ↓
Reference Interpreter
      ↓
Expected semantic result
```

Backend optimized:

```text
MIR → native
```

so sánh với interpreter.

---

# 72. Vì sao cần reference interpreter

Nếu:

```text
native backend
```

và:

```text
reference interpreter
```

cùng sai theo cùng một bug compiler thì differential test khó phát hiện.

Do đó interpreter phải:

- đơn giản;
- ưu tiên readability;
- ít optimization;
- độc lập backend.

---

# 73. MIR verifier độc lập

Không chỉ compiler pass tự nói:

```text
"MIR tôi tạo ra hợp lệ."
```

Phải có verifier riêng:

```text
MIR
 ↓
Independent MIR Verifier
```

Kiểm tra:

```text
ownership
types
CFG
drop
capability
terminator
SSA constraints nếu có
```

---

# 74. Optimization validation

Mỗi optimization pass có:

```text
preconditions
transform
postconditions
```

Test framework:

```text
input MIR
 ↓
optimization
 ↓
verify MIR
 ↓
reference execution
```

Nếu pass tạo MIR invalid:

```text
compiler bug
```

---

# 75. Pass isolation

Có thể chạy:

```bash
axc test --opt-pass GVN
axc test --opt-pass LICM
axc test --opt-pass SROA
```

và:

```bash
axc inspect optir
```

Điều này rất hữu ích khi agent AI phát triển compiler.

---

# 76. Optimization explanation tests

Nếu compiler nói:

```text
bounds check eliminated
```

thì explanation phải có proof facts:

```text
index range:
    0 <= i < len

source:
    loop invariant #17
```

Test có thể kiểm tra explanation tồn tại nhưng không nên phụ thuộc wording.

---

# 77. Test levels

Axiom test runner có:

```text
unit
integration
semantic
conformance
compile-fail
execution
fuzz
stress
differential
bootstrap
```

---

# 78. Test selection

Có thể:

```bash
axc test
axc test types
axc test ownership
axc test --target x86_64-linux
axc test --target aarch64-linux
axc test --profile sanitizer
axc test --stress concurrency
```

---

# 79. Cross-target conformance

Một semantic test hợp lệ:

```text
x86-64
AArch64
RISC-V
WASM
```

phải cho cùng semantic result.

Target-specific test được đánh dấu riêng.

---

# 80. Target capability matrix

Test metadata:

```text
requires:
    atomic_128
    simd
    gpu
    tls
```

Nếu target không hỗ trợ:

```text
SKIPPED
```

không phải PASS và cũng không phải FAIL.

---

# 81. Test status

Chuẩn hóa:

```text
PASS
FAIL
XFAIL
XPASS
SKIP
TIMEOUT
CRASH
OOM
UNSUPPORTED
```

`XFAIL` phải có lý do và issue/reference.

---

# 82. Conformance tiers

Axiom test suite chia:

```text
Tier 0 — Lexer/parser
Tier 1 — Core semantics
Tier 2 — Ownership/capability
Tier 3 — Compiler IR
Tier 4 — Runtime
Tier 5 — Backend
Tier 6 — Cross-platform
Tier 7 — Full bootstrap
```

Một compiler bootstrap mới có thể chưa đạt Tier 7 nhưng không được tự tuyên bố full conformance.

---

# 83. Conformance declaration

Compiler build metadata có:

```text
language_edition
compiler_semantic_version
conformance_level
target
features
```

Ví dụ:

```text
Axiom 0.1
Core Conformance: 100%
Runtime Conformance: partial
GPU Conformance: unsupported
```

---

# 84. Specification traceability

Mỗi rule:

```text
ATYPE-90
```

liên kết:

```text
spec section
compiler implementation
unit tests
integration tests
negative tests
fuzz category
```

Conceptually:

```text
Spec Rule
   ↓
Implementation
   ↓
Tests
   ↓
CI
```

---

# 85. CI architecture

Mỗi commit:

```text
format
 ↓
unit
 ↓
semantic
 ↓
compile-fail
 ↓
MIR verification
 ↓
small backend suite
```

Nightly:

```text
full cross-target
fuzz
stress
differential
bootstrap
```

---

# 86. Presubmit vs nightly

Không nên chạy fuzz 12 giờ trên mỗi commit.

### Presubmit

```text
fast deterministic suite
```

### Nightly

```text
large fuzz
stress
cross-target
bootstrap
performance
```

### Release

```text
everything
```

---

# 87. AI-agent integration

Axiom compiler/test system nên expose:

```text
axc test --json
```

Output:

```json
{
  "status": "fail",
  "test": "ownership/use_after_move",
  "diagnostics": [
    {
      "code": "EOWN_USE_AFTER_MOVE",
      "span": "...",
      "phase": "ownership"
    }
  ]
}
```

Agent không phải parse human prose.

---

# 88. Machine-readable test events

```text
TestStarted
TestCompiled
TestExecuted
DiagnosticProduced
TestPassed
TestFailed
TestSkipped
CompilerCrashed
TestTimedOut
```

Có thể stream:

```text
JSONL
```

cho IDE/AI agent.

---

# 89. Test artifact

Mỗi failure nên giữ:

```text
source
compiler version
target
flags
environment
seed
diagnostics
IR snapshot nếu cần
binary nếu cần
stdout
stderr
exit code
```

để reproducible.

---

# 90. Golden artifact policy

Golden files được phép cho:

```text
AST
HIR
MIR
ABI
Object metadata
Diagnostics
```

nhưng phải tránh khóa implementation detail không semantic.

---

# 91. Semantic fingerprint

Test runner có thể so:

```text
semantic fingerprint
```

thay vì byte-for-byte IR.

Điều này giúp compiler tự do optimize.

---

# 92. Compiler correctness hierarchy

Axiom dùng:

```text
             Specification
                  │
                  ↓
        Reference Interpreter
                  │
                  ↓
             Verified MIR
                  │
                  ↓
          Optimized MIR
                  │
                  ↓
             ABI MIR
                  │
                  ↓
               LIR
                  │
                  ↓
            Machine Code
```

Mỗi boundary có verifier/test.

---

# 93. Miscompilation detection

Một miscompilation được định nghĩa:

```text
Defined Axiom program
        +
correct compilation
        ↓
observable behavior X

actual compiler
        ↓
observable behavior Y
```

với:

```text
X != Y
```

Đây là bug nghiêm trọng hơn ordinary diagnostic bug.

---

# 94. Compiler bug severity

Khuyến nghị:

```text
P0 — wrong-code / memory safety violation
P1 — wrong semantics
P2 — compiler crash / ICE
P3 — incorrect diagnostic
P4 — tooling/test infrastructure
P5 — performance regression
```

Không dùng severity để thay đổi language semantics.

---

# 95. Memory-safety differential testing

Đặc biệt cần test:

```text
optimized compiler
```

không biến safe program thành machine code có:

```text
use-after-free
double-free
out-of-bounds
data race
invalid capability
```

Đây là lý do Verified MIR phải là boundary trước optimization.

---

# 96. Formal verification scope

Axiom **không yêu cầu formal proof toàn bộ compiler** ở v0.1.

Thay vào đó:

```text
strong invariants
+
independent verifier
+
reference interpreter
+
differential testing
+
fuzzing
+
conformance suite
```

Đây là trade-off thực tế hơn để có compiler production.

---

# 97. Eventually formally verifiable components

Kiến trúc phải cho phép sau này formalize:

```text
MIR verifier
ownership checker
capability checker
Drop elaboration
selected optimizer passes
```

Nhưng không block v0.1.

---

# 98. Test naming convention

Ví dụ:

```text
ownership/
    move_basic_001.ax
    move_branch_002.ax
    partial_move_003.ax

capability/
    read_read_001.ax
    read_write_002.ax
    disjoint_fields_003.ax
    relocation_004.ax

traits/
    basic_impl_001.ax
    ambiguity_002.ax
    cycle_003.ax
```

Tên test không encode compiler implementation detail.

---

# 99. Core test requirement

Mỗi frozen invariant phải có:

```text
≥ 1 positive test
≥ 1 negative/adversarial test
```

nếu invariant có cả positive và negative semantics.

Một invariant chỉ mang tính architectural có thể có implementation test riêng.

---

# 100. Frozen invariants

### `ATEST-20`
Every normative semantic rule must have executable conformance coverage.

### `ATEST-21`
Positive and negative semantics must both be tested.

### `ATEST-22`
Diagnostics are validated by stable error codes and spans.

### `ATEST-23`
Diagnostic wording is not the primary semantic oracle.

### `ATEST-24`
Verified MIR has an independent verifier.

### `ATEST-25`
Optimization must preserve observable semantics.

### `ATEST-26`
Optimization correctness must be tested independently from frontend correctness.

### `ATEST-27`
Reference interpretation may serve as a semantic oracle.

### `ATEST-28`
Reference implementation is not semantic authority.

### `ATEST-29`
LLVM/external compilers are validation tools during bootstrap only.

### `ATEST-30`
Compiler fuzzing must never convert malformed input into an uncontrolled compiler crash.

### `ATEST-31`
Trait solver fuzzing must terminate.

### `ATEST-32`
Comptime-generated code must pass ordinary verification.

### `ATEST-33`
Unsafe code does not exempt generated or lowered code from structural verification.

### `ATEST-34`
Concurrency tests must support reproducible seeds.

### `ATEST-35`
Cross-target semantic tests must preserve target-independent semantics.

### `ATEST-36`
Target-specific behavior must be explicitly classified.

### `ATEST-37`
Cache hits and clean builds must be semantically equivalent.

### `ATEST-38`
Bootstrap stages must be independently testable.

### `ATEST-39`
Every compiler crash must be distinguishable from user compilation failure.

### `ATEST-40`
Every fixed compiler bug requires a regression test.

### `ATEST-41`
Fuzz failures must be minimizable and replayable.

### `ATEST-42`
Test execution must record sufficient metadata for reproduction.

### `ATEST-43`
Semantic tests must avoid unnecessary physical-layout assumptions.

### `ATEST-44`
Machine-code tests must not replace semantic-level tests.

### `ATEST-45`
Compiler nondeterminism must not affect semantic output.

### `ATEST-46`
Randomized testing must record its seed.

### `ATEST-47`
Resource-limit failures must produce controlled diagnostics.

### `ATEST-48`
Conformance status must be measurable per language feature and target.

### `ATEST-49`
The compiler must never silently accept an unverified MIR.

### `ATEST-50`
No optimization pass may bypass the verification boundary.

### `ATEST-51`
The test framework itself must distinguish PASS, FAIL, SKIP, UNSUPPORTED, CRASH, TIMEOUT and OOM.

### `ATEST-52`
Specification-to-test traceability must be machine-readable.

### `ATEST-53`
The test suite must be usable by automated AI agents without parsing human-only output.

### `ATEST-54`
Axiom correctness is defined by language semantics, not by agreement with an external compiler.

### `ATEST-55`
Wrong-code detection has higher priority than optimization performance.

---

# 101. Hoàn thành BOOTSTRAP-122

Chuỗi compiler architecture hiện tại đã trở thành:

```text
Source
  ↓
Lexer / Parser
  ↓
Resolver
  ↓
HIR
  ↓
Type / Trait
  ↓
Ownership / Capability / Lifetime
  ↓
Verified MIR
  ↓
Optimization
  ↓
ABI
  ↓
LIR
  ↓
Machine Backend
  ↓
Object
  ↓
Linker
  ↓
Native Binary
```

và song song:

```text
Specification
      ↓
Conformance Tests
      ↓
Independent Verification
      ↓
Reference Interpreter
      ↓
Fuzz / Differential / Stress
      ↓
Bootstrap Validation
```

Điểm quan trọng là **Verified MIR trở thành trust boundary của compiler**:

```text
                UNTRUSTED
                   │
                   ↓
              Typed HIR
                   │
                   ↓
          Ownership / Capability
                   │
                   ↓
            ┌─────────────┐
            │ VERIFIED MIR│
            └─────────────┘
                   │
                   ↓
                TRUSTED
                   │
          ┌────────┼────────┐
          ↓        ↓        ↓
       Optimize   ABI      Debug
          │
          ↓
        LIR
```

Sau task này, phần frontend/semantic correctness cơ bản đã khá đầy đủ. Bước hợp lý tiếp theo là **khóa trải nghiệm ngôn ngữ thực tế**: cú pháp cụ thể, grammar chính thức, lexical rules, operator precedence, literal syntax, declaration syntax, module syntax, generic syntax, pattern syntax, attribute syntax và quy tắc parsing không mơ hồ.

# BOOTSTRAP-123 — Formal Grammar, Syntax & Surface Language Specification

Task 123 sẽ biến những semantic rules đã đóng thành **grammar chính thức có thể dùng trực tiếp để viết parser**, đồng thời kiểm tra một mục tiêu rất quan trọng của Axiom:

> **Syntax phải đơn giản đối với programmer nhưng đủ giàu để compiler/AI hiểu chính xác mà không cần đoán ý định.**