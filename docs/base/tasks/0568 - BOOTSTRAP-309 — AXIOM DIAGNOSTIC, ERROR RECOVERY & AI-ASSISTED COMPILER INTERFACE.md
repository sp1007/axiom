# BOOTSTRAP-309 — AXIOM DIAGNOSTIC, ERROR RECOVERY & AI-ASSISTED COMPILER INTERFACE

## 1. Mục tiêu

Thiết kế hệ thống **Diagnostic & Compiler Interaction** hoàn chỉnh cho Axiom.

Đây là thành phần đặc biệt quan trọng vì Axiom hướng tới:

- compiler mạnh;
- compiler tự suy luận nhiều thứ thay programmer;
- ownership/capability/effect/concurrency verification;
- comptime;
- generic/trait solver;
- incremental compilation;
- AI-assisted development.

Compiler không chỉ cần nói:

```text
error
```

mà phải có khả năng trả lời:

> **Điều gì sai → sai ở đâu → compiler biết gì → tại sao không thể chứng minh → cách sửa nào hợp lệ → sửa đó ảnh hưởng semantic gì.**

---

# 2. Nguyên tắc

### D-1 — Diagnostic là structured data trước khi là text

Mỗi diagnostic phải có semantic representation:

```text
Diagnostic {
    code
    severity
    primary_span
    secondary_spans
    message
    explanation
    notes
    causes
    suggestions
    related_symbols
    related_types
    related_capabilities
    related_effects
}
```

Text/JSON/IDE UI chỉ là các renderer khác nhau.

---

# 3. Severity

Tối thiểu:

```text
Hint
Info
Warning
Error
Fatal
```

`ICE` phải là một loại riêng về mặt compiler status, không được giả dạng user error.

```text
CompilerError
InternalCompilerError
```

---

# 4. Stable Diagnostic Code

Mỗi diagnostic có ID ổn định:

```text
EOWN001
ECAP014
ETRAIT021
EASYNC008
EGPU004
EFFI012
ECOMP007
EPKG021
EABI005
```

Không được dùng message text làm identity.

Điều này cho phép:

- IDE;
- test;
- AI;
- documentation;
- suppression;
- telemetry;

tham chiếu diagnostic ổn định.

---

# 5. Diagnostic Category

Diagnostic có category:

```text
Syntax
NameResolution
Type
Trait
Ownership
Capability
Effect
Concurrency
Async
GPU
Comptime
ABI
FFI
Package
Build
Link
Target
Internal
```

AI có thể query:

```text
diagnostic.category == Ownership
```

thay vì phải parse text.

---

# 6. Primary Span

Mỗi lỗi phải có một location chính xác:

```text
PrimarySpan {
    file
    start
    end
}
```

Không chỉ báo:

```text
line 42
```

mà phải có byte/character offsets để IDE có thể highlight chính xác.

---

# 7. Secondary Span

Ví dụ lỗi capability:

```text
let view = view(buffer)

drop(buffer)

use(view)
```

Diagnostic phải chỉ ra:

```text
PRIMARY:
    use(view)

SECONDARY:
    view created here

SECONDARY:
    owner dropped here
```

---

# 8. Explanation Graph

Diagnostic phức tạp nên có causal graph:

```text
Error
 │
 ├── capability used here
 │
 ├── capability originated here
 │
 └── owner invalidated here
```

Không chỉ là một chuỗi message.

Internal representation:

```text
DiagnosticCause {
    kind
    source
    relation
    explanation
}
```

---

# 9. Ownership Diagnostic

Ví dụ:

```text
let b = a
use(a)
```

Không nên chỉ:

```text
error: use of moved value
```

Compiler nên biết:

```text
EOWN001

`a` was moved here.

move destination:
    b

later use:
    use(a)

ownership state:
    a → Moved

valid alternatives:
    - use `b`
    - clone `a`
    - pass `a` by view if ownership is not required
```

Các suggestion này phải dựa trên semantic facts.

---

# 10. Không Suggest Sai Semantic

Compiler không được máy móc đề xuất:

```text
clone()
```

cho mọi lỗi Move.

Suggestion phải phân loại:

```text
safe semantic fix
possible semantic fix
performance-impacting fix
manual redesign required
```

Ví dụ Clone có thể tạo allocation/copy lớn.

AI/IDE phải biết đây không phải equivalent hoàn toàn về performance.

---

# 11. Capability Diagnostic

Ví dụ:

```text
E_CAP_004

cannot create `mut_view<T>`

conflicting capability:
    READ buffer

requested:
    WRITE buffer

overlap:
    UNKNOWN

reason:
    compiler cannot prove the regions are disjoint
```

Đây là điểm cực kỳ quan trọng:

> **UNKNOWN phải được giải thích là thiếu proof, không phải compiler “không hiểu code”.**

---

# 12. Region Explanation

Nếu conflict:

```text
a[0..100]
b[50..150]
```

compiler có thể hiển thị:

```text
region A:
    [0,100)

region B:
    [50,150)

relation:
    OVERLAPS
```

Nếu không chứng minh được:

```text
relation:
    UNKNOWN
```

---

# 13. Trait Solver Diagnostic

Trait failure phải hiển thị candidate reasoning:

```text
ETRAIT021

required:
    T: Comparable

candidates considered:
    Comparable for i32        ✓
    Comparable for String     ✓
    Comparable for MyType     ✗

MyType failed because:
    missing implementation:
        Comparable
```

Nếu ambiguous:

```text
candidate A
candidate B
```

được hiển thị riêng.

---

# 14. Generic Diagnostic

Ví dụ:

```text
foo<T: Numeric>(x)
```

gọi:

```text
foo(MyStruct)
```

Compiler phải hiển thị:

```text
T inferred as:
    MyStruct

required:
    Numeric<MyStruct>

not satisfied because:
    no Numeric implementation exists
```

Không chỉ:

```text
type mismatch
```

---

# 15. Type Mismatch

Diagnostic phải có:

```text
expected
found
inferred
conversion_available
```

Ví dụ:

```text
expected:
    i64

found:
    f64

implicit conversion:
    not allowed

possible explicit conversion:
    `x as i64`
```

Nhưng compiler không tự chèn cast nếu cast có thể làm thay đổi semantics.

---

# 16. Effect Diagnostic

Ví dụ function:

```text
@noalloc
fn process(...)
```

gọi:

```text
Vec.push(...)
```

nếu operation có thể allocate:

```text
EEFFECT003

function contract:
    NoAllocate

operation:
    Vec.push

possible effect:
    Allocate

reason:
    capacity may be exhausted
```

---

# 17. Async Diagnostic

Ví dụ view sống qua await:

```text
let v = view(buffer)

await something()

use(v)
```

Compiler:

```text
EASYNC008

capability `v` is live across suspension point #2

suspension:
    await something()

capability provenance:
    buffer

required property:
    storage must remain valid across suspension

suggestions:
    consume/copy the required data
    reacquire the view after await
    use an explicitly stable storage contract
```

Không cần bắt programmer viết lifetime annotation.

---

# 18. Send Diagnostic

Ví dụ task spawn yêu cầu `Send`:

```text
spawn(task)
```

Compiler:

```text
ECONC012

future is not Send

value captured across execution-domain boundary:
    LocalResource

reason:
    LocalResource is execution-domain local

boundary:
    spawn(...)
```

Phải trace được value từ capture → Future state → spawn.

---

# 19. GPU Diagnostic

Ví dụ host pointer truyền vào kernel:

```text
@kernel
fn process(p: view<i32>)
```

gọi bằng host storage.

Diagnostic:

```text
EGPU004

host storage cannot be passed directly to GPU kernel

required storage domain:
    Device
found:
    Host

possible solution:
    copy into DeviceBuffer<i32>
```

---

# 20. Comptime Diagnostic

Nếu comptime đọc file nhưng capability không được cấp:

```text
ECOMP007

comptime operation requires:
    ReadFilesystem

available capabilities:
    ReadSource
    ReadMetadata

operation:
    read_file("schema.json")
```

Đây phải là structured capability failure giống runtime/compiler capability model.

---

# 21. FFI Diagnostic

Ví dụ ABI mismatch:

```text
EFFI012

foreign function ABI mismatch

declared:
    C

provided:
    Axiom

required calling convention:
    cdecl
```

Nếu ownership mismatch:

```text
foreign function returns borrowed resource
but no valid provenance contract was declared
```

---

# 22. Package Diagnostic

Dựa trên BOOTSTRAP-308:

```text
EPKG021

dependency resolution failed

package:
    image

requirements:
    ^2.4

available:
    2.3.1
    3.0.0

no compatible version found
```

Dependency chain phải hiện:

```text
myapp
  └── renderer
       └── image
```

---

# 23. Error Recovery — Parser

Compiler phải tiếp tục parse sau syntax error để thu được nhiều diagnostic.

Ví dụ:

```text
fn foo( {
    let x =
    let y = 3
}
```

Không dừng ngay ở `{`.

Parser tạo error nodes:

```text
MissingToken
UnexpectedToken
MissingExpression
MalformedDeclaration
```

AST/HIR vẫn giữ source provenance.

---

# 24. Error Recovery Không Được Tạo Semantic Facts Giả

Đây là invariant quan trọng.

Error-recovered AST có thể tiếp tục để tìm lỗi khác, nhưng:

```text
ErrorNode
```

không được được coi là:

```text
valid type
valid ownership
valid ABI
valid capability
```

Nếu analysis phụ thuộc vào phần lỗi:

```text
Unknown/Error
```

phải propagate có kiểm soát.

---

# 25. Diagnostic Deduplication

Một lỗi gốc có thể tạo hàng chục lỗi cascade.

Ví dụ:

```text
missing type
    ↓
trait failure
    ↓
ownership failure
    ↓
ABI failure
```

Compiler phải xác định:

```text
root cause
derived diagnostics
```

và mặc định giảm noise.

---

# 26. Diagnostic Dependency Graph

Internal model:

```text
Diagnostic A
   ↓ causes
Diagnostic B
   ↓ causes
Diagnostic C
```

UI mặc định ưu tiên A.

AI protocol có thể lấy toàn bộ graph.

---

# 27. Suggestion Model

Suggestion không chỉ là text.

```text
Suggestion {
    applicability
    edits
    semantic_risk
    affected_symbols
}
```

Applicability:

```text
MachineApplicable
MaybeApplicable
RequiresUserDecision
Informational
```

---

# 28. Structured Source Edit

Ví dụ suggestion:

```text
replace:
    `a`

with:
    `b`
```

phải biểu diễn:

```text
TextEdit {
    file
    range
    replacement
}
```

IDE có thể apply trực tiếp.

---

# 29. Semantic Fix

Trong tương lai compiler có thể đề xuất:

```text
introduce clone
introduce view
move operation
add trait impl
make capability explicit
```

Nhưng chỉ khi compiler chứng minh edit vẫn type-check.

Không được generate patch “có vẻ đúng” rồi mặc định coi là valid.

---

# 30. Compiler Explain API

Compiler phải cung cấp:

```text
axiom explain <diagnostic>
```

Ví dụ:

```text
axiom explain EOWN001
```

trả về:

```text
ownership state transitions
place tree
moves
reinitializations
drop obligations
```

---

# 31. `explain` cho Optimization

Không chỉ diagnostic.

Ví dụ:

```text
axiom explain-opt function.foo
```

có thể trả lời:

```text
allocation eliminated:
    reason: object does not escape

vectorization:
    rejected

reason:
    memory regions are UNKNOWN-overlap
```

Điều này cực kỳ phù hợp với triết lý Axiom:

> compiler complexity được giữ trong compiler nhưng programmer/AI có thể yêu cầu compiler giải thích.

---

# 32. `explain` cho Ownership

```text
axiom explain-ownership variable
```

trả:

```text
Declared:
    Owned

Move:
    line 12

Reinitialized:
    line 17

Drop:
    line 22
```

---

# 33. `explain` cho Capability

```text
axiom explain-capability buffer
```

hiển thị:

```text
Owner:
    buffer

Capabilities:
    READ [0..100)
    WRITE [100..200)

proof:
    DISJOINT

origin:
    function argument

end:
    line 48
```

---

# 34. AI Compiler Protocol

Axiom nên có machine-readable protocol:

```text
axiom query
```

hoặc:

```text
axiom compiler --json
```

Output JSON structured.

Ví dụ:

```text
{
    "diagnostics": [...],
    "symbols": [...],
    "types": [...],
    "effects": [...],
    "ownership": [...],
    "capabilities": [...]
}
```

Không yêu cầu AI parse human-readable compiler output.

---

# 35. AI Query Operations

Protocol tối thiểu:

```text
get_diagnostics
get_symbol
get_type
get_signature
get_public_api
get_ownership
get_capabilities
get_effects
get_trait_candidates
get_dependency_graph
get_build_graph
explain
explain_optimization
explain_codegen
```

---

# 36. AI không được bypass Compiler

AI có thể hỏi:

```text
what type is x?
why does this fail?
what APIs are available?
```

nhưng compiler mới là authority.

AI-generated patch:

```text
AI
 ↓
source edit
 ↓
compiler
 ↓
verification
 ↓
accept/reject
```

Không có:

```text
AI says it's safe
→ compiler trusts AI
```

---

# 37. Compiler Snapshot

AI/IDE nên có thể request một semantic snapshot:

```text
CompilerSnapshot {
    source_revision
    package_graph
    modules
    symbols
    types
    diagnostics
    effects
    ownership
    capabilities
    target
}
```

Snapshot phải immutable.

Điều này tránh AI hỏi compiler ở giữa một revision không nhất quán.

---

# 38. Incremental Diagnostics

Khi user sửa một dòng:

```text
source revision N
        ↓
revision N+1
```

compiler chỉ recompute diagnostics/query bị invalidated.

Không parse/type-check toàn project nếu không cần.

---

# 39. Diagnostic Stability

Diagnostic code ổn định.

Message text có thể thay đổi giữa compiler versions.

Do đó test:

```text
expect diagnostic EOWN001
```

không nên phụ thuộc toàn bộ message.

Có thể test:

```text
code
primary span
related symbol
suggestion category
```

---

# 40. Compiler Error Budget

Trong interactive mode:

```text
max_errors = N
```

nhưng compiler phải ưu tiên:

1. root errors;
2. local errors;
3. dependent errors.

Không spam 500 lỗi cascade.

---

# 41. Warning System

Warning phải có ID:

```text
WUNUSED001
WPERF004
WABI003
WUNSAFE002
```

Có thể cấu hình:

```text
deny
warn
allow
```

Ví dụ:

```text
@warn(unused = deny)
```

hoặc package-level configuration.

---

# 42. Lint Architecture

Lint không được trộn với semantic correctness.

Phân biệt:

```text
Compiler Error
Compiler Warning
Lint
Style
Optimization Remark
```

Ví dụ:

```text
unused variable
```

có thể là warning/lint.

Trong khi:

```text
use-after-move
```

là semantic error.

---

# 43. Optimization Remark

Compiler có thể emit:

```text
Remark:
    allocation eliminated

Remark:
    function inlined

Remark:
    loop vectorized

Remark:
    bounds check eliminated
```

Nhưng phải có:

```text
reason
proof
affected code
```

khi khả thi.

---

# 44. Performance Diagnostic

Axiom có thể hỗ trợ:

```text
axiom explain-perf function.foo
```

trả:

```text
allocations:
    0

heap allocations:
    0

branches:
    ...

vectorization:
    enabled

inlining:
    yes

spill:
    2 slots

blocking:
    none
```

Đây là tooling, không phải language semantic.

---

# 45. Security Diagnostic

Compiler có thể báo:

```text
unsafe block
foreign call
raw pointer
volatile access
```

với source span.

Ví dụ:

```text
USAFE001

unsafe operation:
    raw pointer dereference

trusted assumption:
    pointer points to initialized T

safety contract:
    not documented
```

Không tự động cấm unsafe.

---

# 46. Diagnostic Serialization

Định dạng JSON phải ổn định schema:

```text
diagnostic_version
compiler_version
code
severity
spans
causes
suggestions
```

IDE không nên phải parse message text.

---

# 47. Human Renderer

Terminal renderer có thể:

```text
error[EOWN001]: use of moved value `buffer`

  --> src/main.axm:18:9
   |
12 | let b = buffer
   |         ------ value moved here
...
18 | use(buffer)
   |     ^^^^^^ value used after move
```

Nhưng đây chỉ là **presentation layer**.

---

# 48. IDE Integration

LSP hoặc Axiom-native protocol có thể expose:

```text
diagnostics
completion
hover
go_to_definition
rename
references
semantic_tokens
signature_help
code_actions
inlay_hints
```

Các chức năng phải lấy semantic information trực tiếp từ `CompilerDB`.

---

# 49. AI + Completion

AI-friendly completion không chỉ trả string.

Ví dụ:

```text
CompletionItem {
    symbol
    type
    effects
    ownership
    required_capabilities
    documentation
    availability
    target_conditions
}
```

AI có thể hiểu:

```text
foo()
```

có thể:

```text
Allocate
Block
Async
```

trước khi đề xuất sử dụng.

---

# 50. Definition of Done

BOOTSTRAP-309 hoàn thành khi Axiom có:

- structured diagnostics;
- stable diagnostic codes;
- precise source spans;
- causal diagnostic graph;
- ownership/capability/trait/effect explanations;
- parser error recovery;
- diagnostic deduplication;
- machine-applicable edits;
- optimization explanations;
- compiler JSON protocol;
- semantic snapshot;
- incremental diagnostics;
- AI query interface;
- IDE integration foundation;
- warning/lint separation;
- performance/security explanations.

---

# Invariants

```text id="d1a4b8"
ADIAG-20
Diagnostics are structured semantic objects before rendering.

ADIAG-21
Every user-facing diagnostic has a stable diagnostic code.

ADIAG-22
Primary source spans are precise and machine-addressable.

ADIAG-23
Related source spans preserve causal relationships.

ADIAG-24
Diagnostic explanations are derived from compiler facts, not guesses.

ADIAG-25
Compiler suggestions must not claim semantic equivalence without proof.

ADIAG-26
Error-recovery nodes never create false semantic facts.

ADIAG-27
Root-cause diagnostics take precedence over cascade diagnostics.

ADIAG-28
Ownership diagnostics expose relevant state transitions.

ADIAG-29
Capability diagnostics expose provenance and region reasoning when available.

ADIAG-30
Trait diagnostics expose relevant candidate/constraint failures.

ADIAG-31
Effect diagnostics expose the conflicting effect contract.

ADIAG-32
Async diagnostics identify suspension points affecting validity.

ADIAG-33
Concurrency diagnostics identify execution-domain boundaries.

ADIAG-34
GPU diagnostics identify storage/execution-domain mismatches.

ADIAG-35
Comptime diagnostics identify missing capabilities and external inputs.

ADIAG-36
FFI diagnostics identify ABI/ownership/contract mismatches.

ADIAG-37
Package diagnostics expose dependency chains.

ADIAG-38
Machine-readable diagnostics do not depend on human message text.

ADIAG-39
AI tooling cannot bypass compiler verification.

ADIAG-40
AI-generated edits must be revalidated by the compiler.

ADIAG-41
Optimization explanations expose legality/proof information where available.

ADIAG-42
Diagnostic generation participates in incremental compilation.

ADIAG-43
Compiler snapshots are revision-consistent.

ADIAG-44
Warnings/lints are distinct from semantic errors.

ADIAG-45
Unsafe diagnostics identify trusted assumptions where available.

ADIAG-46
Diagnostic rendering is independent of compiler semantic representation.

ADIAG-47
Compiler JSON protocol is versioned.

ADIAG-48
IDE and AI tooling use CompilerDB facts rather than reparsing compiler text.

ADIAG-49
No diagnostic system may weaken ownership, capability, concurrency, ABI, or comptime verification.

ADIAG-50
The diagnostic architecture must remain usable by the self-hosted Axiom compiler.
```