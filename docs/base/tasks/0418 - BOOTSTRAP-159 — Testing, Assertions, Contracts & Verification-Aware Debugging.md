# BOOTSTRAP-159 — Testing, Assertions, Contracts & Verification-Aware Debugging
**STATUS: FROZEN / COMPLETED**

> **Axiom phải có khả năng tự kiểm chứng từ source → semantic model → MIR → optimizer → machine code → native execution, và test infrastructure không được trở thành một phần bắt buộc của runtime.**

Đây là lớp rất quan trọng vì Axiom đang theo hướng compiler cực kỳ mạnh. Compiler càng tự động làm nhiều thứ thì càng cần một hệ thống chứng minh rằng:

```text
compiler optimization
≠
semantic change
```

---

# 1. Kiến trúc test tổng thể

Chốt:

```text id="3j6w8s"
                    Axiom Source
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Compile       Test       Inspect
             │           │
             ▼           ▼
          Semantic     Test Runner
          Pipeline         │
             │             │
             ▼             ▼
          Verified MIR   Execution
             │             │
             ▼             ▼
           OptIR        Oracle
             │             │
             └──────┬──────┘
                    ▼
                 Compare
                    │
                    ▼
                 Result
```

---

# 2. Test không chỉ là runtime test

Axiom test system có nhiều tầng:

```text id="d1q7z4"
1. Lexer tests
2. Parser tests
3. Resolver tests
4. Type tests
5. Trait tests
6. Comptime tests
7. HIR tests
8. MIR tests
9. Verification tests
10. Optimization tests
11. ABI tests
12. LIR tests
13. Machine-code tests
14. Object/linker tests
15. Native execution tests
16. Cross-target tests
17. Performance tests
18. Bootstrap tests
```

---

# 3. Unit test

Syntax có thể đơn giản:

```ax id="4r9wq2"
test "addition" {
    assert(2 + 3 == 5);
}
```

Test function được compiler nhận diện nhưng không tạo runtime framework cho production binary.

---

# 4. Test binary riêng

Lệnh:

```text id="v3x8m1"
axc test
```

compiler tạo test executable riêng.

Production build:

```text id="q7m2c9"
axc build
```

không kéo test harness vào binary.

---

# 5. Assertion

Core/library cung cấp:

```text id="j8p4s6"
assert
debug_assert
assert_eq
assert_ne
```

Tùy semantics/profile.

---

# 6. Assertion không phải optimizer hint

Ví dụ:

```ax id="n2f7k5"
assert(i < n);
x = a[i];
```

Compiler có thể sử dụng assertion như một semantic check.

Nếu assertion active:

```text id="p9c3w8"
failure → panic
```

Nếu profile explicitly loại bỏ `debug_assert`, semantics của profile đó phải quy định việc loại bỏ.

Không được optimizer tự ý xóa `assert`.

---

# 7. `debug_assert`

```text id="w4q8n2"
debug_assert(condition)
```

có thể bị loại bỏ trong release profile.

Nó khác:

```text id="h7m3c5"
assert(condition)
```

vì semantics profile khác nhau.

---

# 8. Compile-fail test

Một phần cực kỳ quan trọng với Axiom:

```text id="a9x2v6"
test invalid_move.ax
```

phải **không compile**.

Ví dụ:

```ax id="s6m1q8"
let a = Resource.open();
let b = a;
use(a);
```

Expected:

```text id="k3p7r4"
E_USE_AFTER_MOVE
```

---

# 9. Diagnostic snapshot

Test có thể kiểm tra:

```text id="f5n8c2"
diagnostic code
primary span
secondary span
semantic facts
```

không nhất thiết phụ thuộc chính xác từng câu chữ.

---

# 10. Stable diagnostic identity

Không nên test kiểu:

```text id="q7v3m1"
assert(error.message == "you cannot...")
```

vì compiler wording có thể thay đổi.

Nên:

```text id="c4x9p6"
E_CAPABILITY_CONFLICT
```

và span/structured facts.

---

# 11. Verification test

Có thể tạo MIR trực tiếp cho compiler test:

```text id="n6r2w8"
MIR
 ↓
Verifier
```

Ví dụ cố tình tạo:

```text id="p3k7c1"
Move(x)
Move(x)
```

Expected:

```text id="d8m4q5"
E_USE_AFTER_MOVE
```

---

# 12. MIR verifier độc lập

Rất nên có:

```text id="v2x8n4"
axverify
```

hoặc verifier library độc lập với optimizer.

Kiến trúc:

```text id="r5q1m7"
Compiler generates MIR
        ↓
Independent MIR verifier
        ↓
Verified MIR
```

Điều này tạo thêm một hàng rào chống compiler bug.

---

# 13. Optimizer không được là authority

Nguyên tắc frozen:

```text id="m8c3v6"
MIR semantics
    ↓
Verifier
    ↓
Optimization
```

không:

```text id="q4x7n2"
Optimizer
    ↓
defines semantics
```

---

# 14. Semantic interpreter

Axiom nên có một interpreter/reference executor:

```text id="w6p2r9"
Axiom Source
 ↓
MIR
 ↓
Semantic Interpreter
```

Nó ưu tiên:

```text id="z3m8c5"
correctness
simplicity
determinism
```

hơn performance.

---

# 15. Interpreter không phải compiler authority

Reference interpreter chỉ là:

```text id="j7x4q2"
oracle
```

cho test.

Specification vẫn là authority.

---

# 16. Optimization equivalence test

Một test rất quan trọng:

```text id="c8m3v7"
MIR
 ↓
Reference execution
```

so với:

```text id="p6x1q9"
Optimized MIR
 ↓
execution
```

Kết quả observable phải tương đương.

---

# 17. Không yêu cầu machine code giống nhau

Compiler không cần:

```text id="r4n8k2"
-O0 binary == -O3 binary
```

Chỉ cần:

```text id="u7m2x5"
observable behavior(O0)
=
observable behavior(O3)
```

---

# 18. Metamorphic testing

Ví dụ:

```ax id="h5q9c3"
x + 0
```

và:

```ax id="m7v2p8"
x
```

chỉ tương đương trong các semantics thích hợp.

Test generator có thể tạo transformations đã được chứng minh.

---

# 19. Không dùng metamorphic rule tùy tiện

Ví dụ floating-point:

```text id="d3x8n1"
(a + b) + c
```

không mặc định tương đương:

```text id="k6p4w7"
a + (b + c)
```

do FP semantics.

Test system phải hiểu semantic mode.

---

# 20. Property testing

Có thể:

```ax id="t2m8q5"
property "sort is ordered" {
    forall(xs) {
        let ys = sort(xs);
        assert(is_sorted(ys));
    }
}
```

Property test runner sinh dữ liệu.

---

# 21. Fuzzing

Compiler phải hỗ trợ fuzz:

```text id="g8x1c4"
source
parser
type checker
trait solver
comptime
MIR
verifier
optimizer
backend
linker
```

---

# 22. Compiler fuzzing pipeline

```text id="v5n2m8"
Random Source
    ↓
Lexer
    ↓
Parser
    ↓
Resolver
    ↓
Type
    ↓
MIR
    ↓
Verifier
    ↓
Optimizer
    ↓
Codegen
```

Compiler crash:

```text id="q3r7x1"
BUG
```

không phải user program failure.

---

# 23. ICE distinction

Phân biệt:

```text id="f6m9p2"
User error
Compiler diagnostic
Internal compiler error
Miscompilation
```

ICE không được biến thành:

```text id="z8c4w1"
E_USER_ERROR
```

---

# 24. Compiler crash report

Compiler nên tạo:

```text id="n4x7q3"
CompilerVersion
Target
SourceFingerprint
Query
Pass
IRFingerprint
CrashLocation
```

để reproducible.

---

# 25. Minimization

Khi fuzz tìm:

```text id="p7m2c9"
compiler crash
```

hệ thống tự giảm source:

```text id="r8v3x5"
10,000 lines
 ↓
1,000
 ↓
100
 ↓
20
 ↓
minimal reproducer
```

---

# 26. Optimization differential testing

Có thể compile cùng source:

```text id="h3q8m1"
-O0
-O1
-O2
-O3
-Os
-Oz
```

rồi chạy cùng input.

Expected:

```text id="j6v2c4"
same observable result
```

---

# 27. Target differential testing

Ví dụ:

```text id="a9k3w7"
x86-64
AArch64
RISC-V
WASM
```

cùng semantic test.

Kết quả phải tương đương trong phạm vi target semantics.

---

# 28. Cross-target không nhất thiết bit-identical

Ví dụ floating point hoặc system calls có thể có target-defined differences.

Test framework phải biết:

```text id="s4m8p2"
Defined
Target-defined
Implementation-defined
```

theo conformance model đã frozen.

---

# 29. ABI testing

ABI test cần kiểm:

```text id="c7x2n5"
argument passing
return passing
struct layout
alignment
calling convention
variadic ABI
sret
TLS
symbol naming
```

---

# 30. FFI ABI tests

Ví dụ:

```text id="v8q3m6"
Axiom
  ↕
C
```

test:

```text id="m1x7p4"
@repr(C)
extern "C"
```

với C ABI fixture.

---

# 31. Object file tests

Compiler test:

```text id="r5k9c2"
source
 ↓
.o
```

sau đó inspect:

```text id="w3m6x8"
sections
symbols
relocations
alignment
visibility
```

---

# 32. Linker tests

Test:

```text id="q8v2m5"
object A
object B
 ↓
link
```

kiểm:

```text id="n4x7c1"
symbol resolution
dead stripping
COMDAT
relocations
exports
imports
```

---

# 33. Binary golden tests

Có thể lưu:

```text id="p6m1x8"
expected object structure
```

thay vì toàn bộ binary bytes.

Điều này tránh golden test quá brittle.

---

# 34. Reproducible build test

Build hai lần:

```text id="a2c7m9"
Build A
Build B
```

Expected:

```text id="f8x3q5"
same output
```

trong reproducible mode.

---

# 35. Source path normalization

Không để:

```text id="v4m8k2"
/home/user/project/a.ax
```

làm binary khác:

```text id="s7q1c5"
/tmp/project/a.ax
```

trong reproducible artifact metadata.

---

# 36. Cache correctness test

Build:

```text id="x6n2p9"
source v1
 ↓
cache
```

sau đó:

```text id="j3m7c4"
source unchanged
 ↓
cache hit
```

binary phải semantic-equivalent.

---

# 37. Cache invalidation test

Thay đổi:

```text id="w8q5m1"
implementation only
```

không được rebuild dependency nếu interface fingerprint không đổi.

Ngược lại:

```text id="r2x9c6"
public type/trait/ABI
```

phải invalidate downstream cần thiết.

---

# 38. Ownership property tests

Generator tạo:

```text id="g4m7x2"
Move
Copy
Clone
Drop
partial move
reinitialization
```

và verifier phải luôn giữ invariant.

---

# 39. Capability property tests

Generator tạo:

```text id="n8c3p6"
view
view
mut_view
overlapping ranges
disjoint ranges
escape
return
drop owner
```

Expected:

```text id="q5x1m7"
valid / rejected
```

theo capability model.

---

# 40. Async verification tests

Test:

```text id="v7m2k9"
borrow/view across await
sync guard across await
Send future
non-Send future
spawn
spawn_local
cancel
```

---

# 41. Concurrency tests

Axiom cần deterministic scheduler test mode:

```text id="a3x8q1"
deterministic scheduler
```

để reproduce:

```text id="m6p4c9"
race
deadlock
ordering
channel behavior
```

---

# 42. Race detection

Safe Axiom về semantic phải reject data race.

Runtime sanitizer vẫn có thể tồn tại để phát hiện:

```text id="j8n2v5"
unsafe
FFI
foreign code
```

nhưng sanitizer không định nghĩa language semantics.

---

# 43. Atomic tests

Kiểm:

```text id="c5q9x3"
atomicity
ordering
happens-before
```

không chỉ final value.

---

# 44. Async scheduler + memory model

Test:

```text id="r7m3k8"
wake
publication
await
resume
```

để đảm bảo:

```text id="x1c6p4"
wake != memory fence
```

đã frozen.

---

# 45. GPU conformance

GPU tests:

```text id="q4n8m2"
kernel legality
address space
host/device transfer
atomic
barrier
race
GpuEvent
```

và CPU reference implementation có thể làm oracle cho nhiều thuật toán.

---

# 46. Comptime tests

Test:

```text id="s6x2p9"
const
comptime
reflection
generated declaration
filesystem capability
cache
reproducibility
```

---

# 47. Generated code test

Comptime generated HIR phải đi lại:

```text id="m3q7c5"
resolution
type checking
trait solving
ownership
verification
```

Test phải cố tình tạo generated invalid code.

Compiler phải reject.

---

# 48. Security/property test

Một số property:

```text id="n9x4k2"
no use-after-move
no double-drop
no dangling safe capability
no safe data race
no invalid initialized read
no invalid enum variant
no ABI contract violation
```

được test xuyên compiler.

---

# 49. Sanitizers

Axiom có thể cung cấp optional:

```text id="v2m7c8"
ASan-like
UBSan-like
TSan-like
MSan-like
```

nhưng tên/implementation có thể khác.

Điểm quan trọng:

> Sanitizer là debugging instrumentation, không phải semantics.

---

# 50. Ownership sanitizer

Một lợi thế của Axiom:

Compiler đã có ownership/capability model.

Có thể sinh instrumentation để debug:

```text id="p5x8m3"
allocation
owner
capability
move
drop
escape
```

trong debug build.

---

# 51. Allocation tracing

Optional:

```text id="g7q2c9"
axc run --trace-alloc
```

cho:

```text id="r3m8x1"
allocation count
size
lifetime
stack
arena
pool
```

Không tồn tại trong release binary nếu không yêu cầu.

---

# 52. Performance test

Test framework phải đo:

```text id="n6v2p5"
runtime
throughput
latency
binary size
code size
allocations
peak memory
cache behavior
vectorization
```

---

# 53. Performance regression

Không nên:

```text id="c8x3m7"
"program became 1% slower → compiler broken"
```

Thay vào đó:

```text id="q4n7p2"
benchmark
baseline
variance
confidence
target
compiler version
```

---

# 54. Benchmark stability

PGO/CPU frequency/noise cần được kiểm soát.

Test runner nên có:

```text id="m5x1c8"
warmup
iterations
outlier handling
confidence interval
machine metadata
```

---

# 55. Codegen inspection

Các test quan trọng có thể assert:

```text id="v7q3n9"
expected vectorization
expected no bounds check
expected no allocation
```

nhưng đây là **optimization regression tests**, không phải semantic conformance tests.

---

# 56. Ví dụ

Source:

```ax id="r8m2x4"
fn sum(a: view<i32>) -> i32 {
    var s = 0;

    for i in 0..a.len {
        s += a[i];
    }

    return s;
}
```

Semantic test:

```text id="j5c9q1"
result correct
```

Optimization test:

```text id="x3m7p8"
bounds check eliminated
vectorization available
```

Machine test:

```text id="n6q2v4"
expected SIMD instructions under target feature
```

Ba tầng test độc lập.

---

# 57. Không hard-code instruction trong semantic tests

Không nên test:

```text id="p4x8m2"
"compiler must emit AVX2 instruction X"
```

trong Core conformance.

Target backend test mới có thể kiểm.

---

# 58. Test artifact

Đề xuất:

```text id="w7c3m9"
.ax-test
```

hoặc test declarations trong `.ax`.

Metadata:

```text id="q2m8x5"
test kind
expected result
expected diagnostics
target constraints
optimization expectations
```

---

# 59. Test manifest

Ví dụ:

```text id="r6v1p3"
TestCase {
    name
    source
    kind
    targets
    expected
    diagnostics
    profile
    optimization_constraints
}
```

---

# 60. Test oracle hierarchy

Đóng băng thứ tự tin cậy:

```text id="k3x8m1"
Specification
    ↓
Conformance Rule
    ↓
Independent Verifier
    ↓
Reference Interpreter
    ↓
Native Execution
    ↓
Optimization Differential Test
    ↓
Performance Measurement
```

Performance **không bao giờ** override correctness.

---

# 61. Compiler trust boundary

Kiến trúc:

```text id="v5q2n8"
Source
 ↓
Compiler
 ↓
MIR
 ↓
Independent Verifier
 ↓
Optimization
 ↓
Independent/validation checks
 ↓
Machine
```

Mục tiêu là giảm “trusted computing base”.

---

# 62. Miscompilation detection

Nếu:

```text id="x7m3c9"
-O0 → 42
-O3 → 41
```

test runner phải báo:

```text id="n2p8v4"
MISCOMPILATION
```

không phải:

```text id="f6q1m7"
test failed
```

---

# 63. Reproducer

Mỗi miscompilation cần lưu:

```text id="c8m4x2"
source
compiler version
target
flags
profile
optimization pipeline
IR fingerprints
```

để replay.

---

# 64. Pass bisect

Compiler nên hỗ trợ:

```text id="q5x9m1"
axc build --stop-after=...
axc build --disable-pass=...
axc opt-bisect
```

để tìm pass gây lỗi.

---

# 65. Optimization provenance

Mỗi transformation có:

```text id="v3k7p8"
PassId
InputIR
OutputIR
Reason
LegalityProof
CostDecision
SourceOrigin
```

Ví dụ:

```text id="m8c2q5"
BoundsCheckElimination
Proof:
    i ∈ [0, len)
Cost:
    remove branch
```

---

# 66. AI debugging

Đây là nơi architecture Axiom đặc biệt hữu ích.

AI có thể hỏi:

```text id="j4x9p2"
axc inspect why foo
```

và nhận:

```text id="c6m3v8"
function foo
 ├── ownership: valid
 ├── capability: valid
 ├── alias: NO_ALIAS
 ├── bounds: proven
 ├── vectorization: rejected
 │    └── reason: loop-carried dependency
 └── allocation: eliminated
```

---

# 67. Không cần AI trong compiler

AI chỉ là:

```text id="r7m2x5"
external consumer
```

của compiler metadata.

Compiler semantics vẫn deterministic.

---

# 68. Test results machine-readable

```text id="n5q8c3"
TestEvent {
    test_id
    phase
    status
    diagnostic_codes
    target
    compiler_version
    duration
    artifact
    provenance
}
```

AI agent có thể đọc trực tiếp.

---

# 69. Parallel test execution

Các test độc lập có thể chạy song song.

Nhưng:

```text id="x3m7k1"
output ordering
```

phải deterministic.

Ví dụ sort theo:

```text id="p8c2v5"
TestId
```

trước khi emit final report.

---

# 70. Invariants

Đóng băng:

### `ATEST2-20`
Tests are separate from production runtime semantics.

### `ATEST2-21`
Unit tests execute through a dedicated test build.

### `ATEST2-22`
Production binaries do not include test harnesses unless explicitly requested.

### `ATEST2-23`
Assertions have explicit semantic/profile behavior.

### `ATEST2-24`
`debug_assert` may be disabled only by explicit build profile semantics.

### `ATEST2-25`
Assertions are not automatically treated as optimizer hints.

### `ATEST2-26`
Compile-fail tests are first-class conformance tests.

### `ATEST2-27`
Diagnostic tests use stable diagnostic identities.

### `ATEST2-28`
Diagnostic wording is not the semantic identity of an error.

### `ATEST2-29`
MIR verification tests can construct adversarial MIR.

### `ATEST2-30`
The verifier rejects invalid MIR before optimization.

### `ATEST2-31`
Optimization cannot become semantic authority.

### `ATEST2-32`
Reference interpretation may serve as a validation oracle.

### `ATEST2-33`
Reference interpretation does not replace the specification.

### `ATEST2-34`
Optimization equivalence tests compare observable semantics.

### `ATEST2-35`
Different optimization levels need not generate identical machine code.

### `ATEST2-36`
Different targets need not generate identical binaries.

### `ATEST2-37`
Target-defined behavior is tested according to target contracts.

### `ATEST2-38`
Metamorphic tests must use only semantics-valid transformations.

### `ATEST2-39`
Floating-point tests respect the configured FP semantics.

### `ATEST2-40`
Property testing may generate ordinary and adversarial inputs.

### `ATEST2-41`
Compiler fuzzing covers frontend, verifier, optimizer, backend and linker.

### `ATEST2-42`
Compiler ICE is distinct from user compilation failure.

### `ATEST2-43`
Compiler crashes produce reproducible diagnostic metadata.

### `ATEST2-44`
Fuzz failures are automatically minimizable where practical.

### `ATEST2-45`
Ownership and capability properties are directly testable.

### `ATEST2-46`
Async and concurrency semantics are testable under deterministic scheduling.

### `ATEST2-47`
GPU legality and synchronization are conformance-testable.

### `ATEST2-48`
Comptime-generated code re-enters ordinary semantic verification.

### `ATEST2-49`
Sanitizers are debugging instrumentation, not language semantics.

### `ATEST2-50`
Performance tests are distinct from correctness tests.

### `ATEST2-51`
Performance observations cannot override semantic correctness.

### `ATEST2-52`
Optimization regression tests may inspect IR and machine properties.

### `ATEST2-53`
Machine-code expectations remain target/backend-specific.

### `ATEST2-54`
Reproducible builds are testable through repeated independent builds.

### `ATEST2-55`
Cache correctness and invalidation are directly testable.

### `ATEST2-56`
Compiler transformations retain provenance.

### `ATEST2-57`
Optimization passes expose legality and profitability reasoning.

### `ATEST2-58`
Miscompilations must have reproducible artifacts.

### `ATEST2-59`
Optimization-pass bisecting is supported.

### `ATEST2-60`
Test events are machine-readable.

### `ATEST2-61`
Test execution may be parallel while final reporting remains deterministic.

### `ATEST2-62`
Cross-target testing is part of compiler conformance.

### `ATEST2-63`
ABI, object and linker behavior are independently testable.

### `ATEST2-64`
Independent verification reduces the compiler trusted computing base.

### `ATEST2-65`
No test mechanism may weaken ownership, capability or safety verification.

### `ATEST2-66`
Unsafe and FFI behavior is tested under explicit contracts.

### `ATEST2-67`
The test framework must remain usable during compiler bootstrap.

### `ATEST2-68`
Compiler tests must be capable of testing the compiler itself.

### `ATEST2-69`
AI tooling can consume structured test and optimization provenance.

### `ATEST2-70`
Test infrastructure must not become a mandatory production runtime dependency.

---

# Kiến trúc Axiom lúc này đã có một đặc điểm rất đáng giá

Ta không còn chỉ có:

```text
Source → Compiler → Binary
```

mà có **hai đường độc lập để kiểm chứng**:

```text
                    SOURCE
                       │
              ┌────────┴────────┐
              ▼                 ▼
        Compiler Pipeline    Reference Path
              │                 │
              ▼                 ▼
         Optimized Code     Semantic MIR
              │                 │
              ▼                 ▼
           Machine            Oracle
              │                 │
              └───────┬─────────┘
                      ▼
                   Compare
```

Cộng thêm:

```text
MIR
 ↓
Independent Verifier
```

Điều này đặc biệt quan trọng với tham vọng của Axiom về **aggressive optimization**. Compiler có thể rất “liều” về optimization, nhưng không được “liều” về semantics.

---

# BOOTSTRAP-160 — Debug Information, Source Mapping, Stack Traces & Developer Observability

Bước kế tiếp nên giải quyết **debug architecture từ source đến machine code**.

Đây không chỉ là chuyện tạo PDB/DWARF.

Axiom cần giữ được chuỗi:

```text
Source
 ↓
CST / AST
 ↓
HIR
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
Machine
 ↓
Object
 ↓
Executable
```

và khi chương trình crash tại machine instruction:

```text
PC
 ↓
machine instruction
 ↓
LIR
 ↓
OptIR
 ↓
MIR
 ↓
HIR
 ↓
source span
 ↓
original source
```

đồng thời vẫn phải cho phép **aggressive optimization, inlining, scalarization, closure elimination, async state-machine transformation, struct splitting và code folding** mà debugger không bị mất hoàn toàn khả năng giải thích chương trình.

Đây sẽ là bước đặt nền cho `axc debug`, stack trace, breakpoint, watch variable, optimized debugging và AI-assisted debugging.