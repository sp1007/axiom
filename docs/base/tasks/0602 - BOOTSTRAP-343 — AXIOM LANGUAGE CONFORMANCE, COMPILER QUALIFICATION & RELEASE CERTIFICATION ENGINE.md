# BOOTSTRAP-343 — AXIOM LANGUAGE CONFORMANCE, COMPILER QUALIFICATION & RELEASE CERTIFICATION ENGINE

Sau 342, Axiom đã có khả năng đo **compiler performance**, **program performance**, **binary size** và phát hiện regression. Nhưng vẫn còn một câu hỏi nền tảng:

> **Làm thế nào chứng minh một phiên bản compiler Axiom thực sự tuân thủ specification, thay vì chỉ “pass test”?**

Đây là bước đặc biệt quan trọng khi Axiom tiến tới **self-hosting**. Một compiler nhanh nhưng hiểu sai semantics của language là nguy hiểm hơn compiler chậm.

343 xây dựng **Conformance Engine** — hệ thống biến specification của Axiom thành một bộ kiểm chứng máy có thể chạy tự động.

---

# 1. Mục tiêu

343 phải đảm bảo:

```text
Axiom Specification
        ↓
Machine-readable semantic rules
        ↓
Conformance tests
        ↓
Compiler execution
        ↓
Observed behavior
        ↓
Expected semantic behavior
```

và phân loại:

```text
PASS
FAIL
UNSUPPORTED
IMPLEMENTATION_DEFINED
TARGET_DEFINED
CONDITIONAL
```

Không dùng khái niệm đơn giản:

```text
test passed = compiler correct
```

---

# 2. Conformance khác Testing

Testing:

> “Chương trình này có hoạt động không?”

Conformance:

> “Compiler có thực hiện đúng semantics mà specification yêu cầu không?”

Ví dụ:

```text
let x: i32 = 1;
let y = x;
```

Test có thể kiểm tra output.

Conformance phải kiểm tra thêm:

- `x` còn usable không;
- type của `y`;
- Copy/Move semantics;
- initialization state;
- ownership state;
- generated MIR;
- observable behavior.

---

# 3. Ba tầng conformance

Axiom dùng:

```text
Language Conformance
Compiler Conformance
Target Conformance
```

### Language Conformance

Syntax + semantics.

### Compiler Conformance

Compiler implementation có tuân specification không.

### Target Conformance

Backend có giữ semantics trên target cụ thể không.

---

# 4. Conformance oracle

Oracle hierarchy:

```text
Formal Semantic Rule
        ↓
Reference Interpreter
        ↓
Executable Semantic Model
        ↓
Expected Diagnostic
        ↓
Differential Compiler
        ↓
Runtime Observation
```

Formal semantics có quyền cao nhất.

---

# 5. Reference Interpreter

317 đã cung cấp reference interpreter.

343 biến nó thành một oracle chính thức:

```text
Source
  ↓
Reference Interpreter
  ↓
Semantic Trace
```

Compiler:

```text
Source
  ↓
Axiom Compiler
  ↓
Executable
  ↓
Observed Trace
```

Sau đó:

```text
Compare(reference, compiler)
```

---

# 6. Semantic Trace

Không chỉ so sánh stdout.

Trace có thể chứa:

```text
Value
Type
Move
Copy
Drop
Panic
Return
Capability
Task
Synchronization
```

Ví dụ:

```text
Trace:
    create x
    move x → y
    drop y
```

---

# 7. Observable semantics

Không phải mọi compiler-internal detail đều phải giống nhau.

Ví dụ:

```text
x = 1 + 2
```

compiler có thể:

```text
ADD
```

hoặc:

```text
constant 3
```

Conformance chỉ yêu cầu:

```text
observable behavior == specification
```

---

# 8. Internal conformance

Tuy nhiên Axiom có thể có các **implementation invariants** riêng.

Ví dụ:

```text
Verified MIR
```

phải thỏa:

```text
NoUseAfterMove
NoInvalidCapability
NoDataRace
NoInvalidDrop
```

Đây là:

```text
Compiler Internal Conformance
```

khác với language semantics.

---

# 9. Test classification

Mỗi test phải khai báo:

```text
ConformanceTest {
    id
    category
    source
    expected
    targets
    diagnostics
    semantic_properties
}
```

---

# 10. Test categories

Core:

```text
Syntax
NameResolution
Types
Generics
Traits
Inference
Values
Copy
Move
Drop
Ownership
Capability
Views
PatternMatching
ControlFlow
Errors
Comptime
Concurrency
Async
GPU
FFI
ABI
Modules
Visibility
```

---

# 11. Negative conformance tests

Đây là phần rất quan trọng.

Không chỉ:

```text
valid program → compile
```

mà:

```text
invalid program → reject
```

Ví dụ:

```text
let x = make();
drop(x);
use(x);
```

Expected:

```text
compile error
```

---

# 12. Diagnostic conformance

Không yêu cầu text diagnostic giống tuyệt đối.

Thay vào đó kiểm tra:

```text
DiagnosticCode
Severity
PrimarySpan
RelevantSpan
SemanticCause
```

Ví dụ:

```text
EOWN001
UseAfterMove
```

Text có thể thay đổi.

Semantic diagnostic code không được tùy tiện thay đổi.

---

# 13. Diagnostic stability

Compiler version mới có thể cải thiện:

```text
"invalid value"
```

thành:

```text
"value was moved here and later used here"
```

vẫn conform nếu semantic diagnostic classification tương đương.

---

# 14. Specification-linked tests

Mỗi test phải liên kết tới specification rule:

```text
Test:
    OWN-MOVE-017

Spec:
    ownership/move.md#move-after-transfer
```

Do đó có thể hỏi:

```text
axiom conformance explain OWN-MOVE-017
```

---

# 15. Specification coverage

343 phải đo:

```text
SpecRuleCoverage
```

Ví dụ:

```text
Ownership:
    94 / 96 rules tested

Async:
    72 / 72

GPU:
    31 / 44
```

---

# 16. Không chấp nhận “test coverage” đơn thuần

Code coverage:

```text
85%
```

không có nghĩa language coverage tốt.

Axiom cần:

```text
SemanticCoverage
SpecCoverage
DiagnosticCoverage
TargetCoverage
OptimizationCoverage
```

---

# 17. Semantic coverage

Coverage phải bao gồm các trạng thái:

```text
Owned
Moved
PartiallyMoved
Dropped
View
MutView
Escaped
Send
Share
Await
Panic
FFI
Unsafe
```

---

# 18. State-transition coverage

Ví dụ ownership:

```text
Owned → Moved
Owned → Dropped
Owned → PartiallyMoved
PartiallyMoved → Dropped
```

Tất cả transition quan trọng phải có test.

---

# 19. Type-system coverage

Không chỉ test từng type.

Phải test combinations:

```text
Generic + Trait
Generic + Const
Trait + AssociatedType
Enum + Pattern
Option + Generic
Closure + Capture
```

---

# 20. Trait solver conformance

Test:

```text
candidate selection
ambiguity
coherence
orphan rules
associated types
generic constraints
recursive bounds
```

và đặc biệt:

```text
same program
different compiler optimization
```

phải cho cùng semantic result.

---

# 21. Ownership conformance matrix

Tạo matrix:

```text
Operation × TypeKind × Context
```

Ví dụ:

```text
Move × CopyType
Move × DropType
Move × View
Move × MutView
Move × Generic
Move × Closure
Move × Async
Move × Thread
```

---

# 22. Capability conformance matrix

Tương tự:

```text
Read × Read
Read × Write
Write × Write
Move × Read
Move × Write
```

với:

```text
DISJOINT
SAME
CONTAINS
OVERLAPS
UNKNOWN
```

---

# 23. Async conformance

Kiểm tra:

```text
await
poll
Pending
Ready
wake
cancel
drop Future
Send Future
view across await
guard across await
```

---

# 24. Concurrency conformance

Dùng litmus tests:

```text
Atomic
Acquire
Release
AcqRel
SeqCst
Mutex
Channel
Thread start
Thread join
```

Compiler phải tuân memory model.

---

# 25. GPU conformance

GPU test có hai oracle:

```text
CPU Reference
GPU Execution
```

So sánh:

```text
values
errors
bounds
synchronization
```

Không yêu cầu instruction-level equality.

---

# 26. FFI conformance

Test các contract:

```text
ownership
nullability
alignment
layout
allocator
panic
callback
threading
async
```

---

# 27. ABI conformance

Đặc biệt quan trọng.

Test:

```text
integer passing
float passing
aggregate passing
return values
struct layout
enum layout
calling convention
variadic
symbol visibility
```

trên từng target ABI.

---

# 28. Target conformance matrix

Ví dụ:

```text
                x86_64   AArch64   WASM
Windows           ✓
Linux             ✓        ✓
macOS             ✓        ✓
Android                    ✓
Browser                              ✓
```

Mỗi cell có:

```text
Core
Std
ABI
FFI
Concurrency
Async
GPU
```

---

# 29. Implementation-defined behavior

Specification có thể cho phép:

```text
implementation-defined
```

Compiler phải ghi rõ:

```text
ImplementationChoice
```

Ví dụ:

```text
enum layout
calling convention
optimization
```

không được vô tình biến implementation detail thành language guarantee.

---

# 30. Target-defined behavior

Một số thứ phụ thuộc target:

```text
usize width
alignment
atomic support
SIMD
endianness
ABI
```

Test phải parameterize theo `TargetSpec`.

---

# 31. Undefined behavior

Axiom cố tình hạn chế UB trong safe language.

Nếu có UB ở:

```text
unsafe
FFI
hardware
foreign code
```

phải được phân loại rõ:

```text
UnsafePreconditionViolation
ForeignContractViolation
TargetHardwareViolation
```

Không được mơ hồ hóa thành:

```text
undefined compiler behavior
```

---

# 32. Unsafe conformance

Unsafe không miễn verification.

Test:

```text
unsafe pointer
pointer provenance
alignment
lifetime
raw access
volatile
MMIO
```

Compiler phải giữ các invariant còn lại.

---

# 33. Optimization conformance

Mỗi chương trình phải giữ semantics:

```text
O0 == O1 == O2 == O3 == Os
```

ở mức observable behavior.

---

# 34. Optimization differential

341 đã có differential fuzzing.

343 biến nó thành conformance suite ổn định:

```text
ConformanceTest
 ×
OptimizationLevel
 ×
Target
```

---

# 35. LTO conformance

Test:

```text
NoLTO
ThinLTO
FullLTO
```

phải cùng semantics.

---

# 36. Incremental conformance

Một chương trình build:

```text
CleanBuild
```

và:

```text
IncrementalBuild
```

phải tạo ra semantic-equivalent artifact.

Không nhất thiết byte-identical nếu debug/layout policy khác.

---

# 37. Cache conformance

Cache hit không được thay đổi semantics.

Test:

```text
ColdCache
WarmCache
RemoteCache
```

phải tương đương.

---

# 38. Comptime conformance

Test:

```text
comptime execution
reflection
generated declarations
filesystem capability
sandbox
reproducibility
cache
```

---

# 39. Comptime determinism

Với reproducible mode:

```text
same source
same inputs
same compiler
same target
```

phải tạo cùng semantic output.

---

# 40. Package conformance

Package resolver phải đảm bảo:

```text
lockfile
dependency versions
features
targets
.artifact
.axif
```

được resolve đúng specification.

---

# 41. Component conformance

Test:

```text
load
validate
initialize
service discovery
capability negotiation
quiesce
unload
hot reload
state migration
```

---

# 42. Binary conformance

Executable phải được kiểm tra:

```text
entry
segments
relocations
imports
exports
ABI
startup
runtime dependencies
```

---

# 43. Object writer conformance

Round-trip:

```text
Axiom Object
 ↓
Object Parser
 ↓
Normalized Representation
```

phải giữ:

```text
sections
symbols
relocations
visibility
alignment
```

---

# 44. Linker conformance

Test:

```text
static
dynamic
PIE
shared
plugin
component
```

và platform-specific loader semantics.

---

# 45. Self-host conformance

Đây là một milestone rất quan trọng.

Sau khi compiler Axiom có thể tự compile compiler:

```text
Compiler A
    ↓ compile
Compiler B
```

sau đó:

```text
Compiler B
    ↓ compile
Compiler C
```

So sánh:

```text
A semantic output
B semantic output
C semantic output
```

---

# 46. Bootstrap trust chain

Định nghĩa:

```text
Bootstrap Compiler
        ↓
Stage 1 Axiom Compiler
        ↓
Stage 2 Axiom Compiler
        ↓
Self-host Compiler
```

Mỗi stage phải pass conformance suite.

---

# 47. Trusting Trust defense

Đặc biệt với self-hosting, phải có:

```text
Diverse Bootstrap
```

Ví dụ:

```text
Reference Interpreter
Bootstrap Compiler
Self-host Compiler
```

cùng kiểm tra semantics.

---

# 48. Compiler qualification

Compiler release không chỉ:

```text
build succeeded
```

mà phải pass:

```text
Qualification Matrix
```

gồm:

```text
Language
Compiler
Target
ABI
Runtime
FFI
Optimization
Incremental
Reproducibility
Security
Performance
```

---

# 49. Qualification levels

Định nghĩa:

```text
Q0 Experimental
Q1 Development
Q2 Target Qualified
Q3 Release Qualified
Q4 Self-Hosting Qualified
```

Đây là **trạng thái chứng nhận**, không phải chất lượng tuyệt đối.

---

# 50. Release candidate

Một compiler release candidate cần:

```text
Spec conformance
No known critical compiler bugs
Fuzz regression clean
Sanitizer regression clean
ABI compatibility clean
Reproducibility clean
Performance within policy
Binary-size within policy
```

---

# 51. Conformance certificate

Compiler có thể phát hành:

```text
.axcert
```

chứa:

```text
compiler version
language edition
spec version
target matrix
test suite fingerprint
test results
fuzz corpus fingerprint
toolchain fingerprint
```

---

# 52. Certificate không phải security proof

`.axcert` chỉ nói:

> Compiler đã pass qualification suite X dưới environment Y.

Không được hiểu:

> Compiler không có bug.

---

# 53. Test suite versioning

Conformance suite có version riêng:

```text
Axiom Conformance Suite 1.4
```

và fingerprint:

```text
ConformanceSuiteFingerprint
```

---

# 54. Specification versioning

Test phải liên kết:

```text
LanguageEdition
SpecRevision
SemanticRuleFingerprint
```

Do đó specification thay đổi thì biết chính xác test nào bị ảnh hưởng.

---

# 55. Edition compatibility

Ví dụ:

```text
Axiom 1.0
Axiom 1.1
Axiom 2.0
```

Compiler có thể support nhiều editions.

Conformance matrix:

```text
Compiler × Edition × Target
```

---

# 56. Feature-gated conformance

Experimental feature:

```text
@feature("xyz")
```

có test suite riêng.

Không được để experimental feature làm thay đổi semantics của Core ngoài contract.

---

# 57. Conformance database

Thêm:

```text
ConformanceDB
SpecRuleDB
ConformanceTestDB
SemanticTraceDB
DiagnosticConformanceDB
TargetConformanceDB
AbiConformanceDB
EditionDB
QualificationDB
CertificateDB
BootstrapDB
```

---

# 58. CLI

```text
axiom conformance run
axiom conformance list
axiom conformance explain
axiom conformance coverage
axiom conformance diff
axiom conformance target
axiom conformance diagnostics
axiom conformance semantic
```

Qualification:

```text
axiom qualify
axiom qualify target
axiom qualify release
axiom qualify bootstrap
```

Certificate:

```text
axiom cert generate
axiom cert inspect
axiom cert verify
```

---

# 59. AI-readable conformance

Ví dụ:

```text
axiom conformance explain OWN-017
```

trả:

```text
Rule:
    A moved value cannot be read.

Test:
    OWN-017-USE-AFTER-MOVE

Compiler:
    FAIL

Observed:
    read accepted

Expected:
    diagnostic EOWN001

Affected:
    ownership verifier

First introduced:
    compiler commit ...
```

Đây sẽ cực kỳ hữu ích cho agent tự sửa compiler.

---

# 60. Automatic regression generation

Khi một bug được phát hiện:

```text
Bug
 ↓
Minimized program
 ↓
Conformance test
 ↓
Spec rule association
 ↓
Regression suite
```

341 fuzzing tìm bug.

343 biến bug thành **permanent semantic contract**.

---

# 61. Compiler differential qualification

Có thể chạy:

```text
Reference Interpreter
Bootstrap Compiler
Self-host Compiler
Release Compiler
```

với cùng corpus.

Nếu:

```text
Reference = A = B = C
```

confidence tăng mạnh.

---

# 62. Conformance fuzzing

Không chỉ corpus cố định.

343 kết hợp 341:

```text
Conformance Generator
        ↓
Valid / Invalid Programs
        ↓
Reference
        ↓
Compiler
        ↓
Semantic Compare
```

Fuzz failure trở thành conformance candidate.

---

# 63. Conformance minimization

Khi failure:

```text
large program
```

341 minimizer tạo:

```text
minimal semantic counterexample
```

343 lưu nó cùng spec rule.

---

# 64. Specification gap detection

Nếu compiler và reference khác nhau nhưng specification không đủ rõ:

```text
Compiler ≠ Reference
Spec ambiguous
```

không được tự động sửa compiler.

Phải tạo:

```text
SpecificationAmbiguity
```

để language design quyết định.

---

# 65. Đây là điểm rất quan trọng cho Axiom

343 tạo ra vòng:

```text
Specification
     ↓
Machine-readable rule
     ↓
Reference semantics
     ↓
Compiler
     ↓
Conformance
     ↓
Fuzz
     ↓
Bug
     ↓
Minimal counterexample
     ↓
Specification refinement
     ↓
New conformance test
```

Do đó specification không còn là tài liệu tĩnh.

Nó trở thành **executable language contract**.

---

# 66. Implementation tree

```text
compiler/
└── conformance/
    ├── spec/
    ├── rules/
    ├── tests/
    ├── generators/
    ├── oracle/
    ├── reference/
    ├── semantic_trace/
    ├── diagnostics/
    ├── target/
    ├── abi/
    ├── ffi/
    ├── comptime/
    ├── async/
    ├── concurrency/
    ├── gpu/
    ├── optimization/
    ├── incremental/
    ├── package/
    ├── component/
    ├── binary/
    ├── bootstrap/
    ├── qualification/
    ├── certificate/
    └── reporting/
```

---

# 67. Invariants

```text
ACONF-01
Every normative language rule must be traceable to conformance coverage.

ACONF-02
Conformance must distinguish language semantics from implementation details.

ACONF-03
Negative tests must verify required rejection.

ACONF-04
Diagnostics are compared semantically, not by exact prose.

ACONF-05
Reference semantics have precedence over implementation behavior.

ACONF-06
Optimization levels must preserve observable semantics.

ACONF-07
Incremental and clean compilation must be semantically equivalent.

ACONF-08
Cache hits must not change semantics.

ACONF-09
Target-defined behavior must be explicitly classified.

ACONF-10
Implementation-defined behavior must be explicitly recorded.

ACONF-11
Unsafe boundaries must retain their specified contracts.

ACONF-12
FFI behavior must be validated against its explicit contract.

ACONF-13
ABI conformance must be target-specific.

ACONF-14
GPU execution must be checked against the defined GPU semantics.

ACONF-15
Comptime must obey the same language semantic model.

ACONF-16
Generated code must re-enter conformance-relevant compiler verification.

ACONF-17
Fuzz-discovered semantic bugs should become permanent regression tests.

ACONF-18
Conformance tests must identify the specification rule they validate.

ACONF-19
Conformance suite versions must be fingerprinted.

ACONF-20
Compiler qualification must identify the exact compiler, target and suite.

ACONF-21
A qualification certificate is evidence of testing, not proof of absence of bugs.

ACONF-22
Self-hosted compilers must pass the same conformance suite as bootstrap compilers.

ACONF-23
Reference/compiler disagreement must not silently redefine language semantics.

ACONF-24
Ambiguous specification behavior must be escalated as specification ambiguity.

ACONF-25
No optimization or implementation shortcut may bypass semantic conformance.
```

---

# 68. Definition of Done

BOOTSTRAP-343 hoàn thành khi Axiom có:

- machine-readable conformance rules;
- specification-linked tests;
- reference-interpreter oracle;
- semantic trace comparison;
- positive/negative conformance;
- diagnostic conformance;
- ownership/capability state coverage;
- type/trait solver coverage;
- async/concurrency coverage;
- GPU coverage;
- FFI/ABI coverage;
- comptime coverage;
- optimization differential conformance;
- incremental-build conformance;
- cache conformance;
- package/component conformance;
- object/linker conformance;
- target matrix;
- edition matrix;
- semantic coverage;
- specification coverage;
- conformance fuzzing;
- automatic minimization;
- fuzz → regression conversion;
- compiler qualification;
- bootstrap qualification;
- self-host qualification;
- conformance certificates;
- AI-readable failure reports;
- specification ambiguity detection.

---

## Kiến trúc sau 343

Ba hệ thống quan trọng nhất hiện tại tạo thành một chuỗi rất mạnh:

```text
341 FUZZING
    │
    │ tìm lỗi
    ▼
342 PERFORMANCE
    │
    │ tìm regression
    ▼
343 CONFORMANCE
    │
    │ xác định semantics đúng
    ▼
315 FORMAL SPEC
    │
    ▼
317 REFERENCE INTERPRETER
    │
    ▼
318 TRANSLATION VALIDATION
    │
    ▼
319 VERIFIED PASSES
    │
    ▼
SELF-HOSTING
```

Điểm đặc biệt của thiết kế này là **Axiom không phụ thuộc vào niềm tin rằng compiler “có vẻ đúng”**.

Mỗi phiên bản compiler sẽ có thể trả lời được bốn câu hỏi độc lập:

1. **Có đúng specification không?** → 343  
2. **Có tạo code đúng semantics không?** → 318/319  
3. **Có bug ẩn nào chưa phát hiện không?** → 341  
4. **Có bị chậm/to hơn trước không?** → 342  

Đây là nền tảng rất quan trọng để bước sang giai đoạn **release-grade/self-hosting compiler**.