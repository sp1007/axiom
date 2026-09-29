# BOOTSTRAP-162 — Diagnostics, Error Recovery, Compiler UX & AI-Native Compiler Interface
**STATUS: FROZEN / COMPLETED**

> **Compiler phải không chỉ phát hiện lỗi mà còn phải giải thích được nguyên nhân, bằng chứng, quan hệ nhân-quả và cách sửa; cùng một diagnostic phải phục vụ được programmer, IDE, CI và AI agent.**

Đây là bước đặc biệt quan trọng với Axiom vì chúng ta đã chọn triết lý:

> **Compiler làm phần việc phức tạp thay programmer.**

Khi compiler tự suy luận ownership, lifetime, alias, escape, specialization, vectorization, layout…, diagnostic phải giải thích được những suy luận đó.

---

# 1. Diagnostic không chỉ là text

Không thiết kế:

```text
error: something went wrong
```

mà:

```text
Diagnostic {
    Code
    Severity
    PrimarySpan
    SecondarySpans[]
    Message
    Explanation
    Causes[]
    Facts[]
    Suggestions[]
    RelatedDiagnostics[]
    Phase
    Origin
}
```

---

# 2. Stable error code

Mỗi lỗi semantic có mã ổn định:

```text
E_USE_AFTER_MOVE
E_UNINITIALIZED_READ
E_CAPABILITY_CONFLICT
E_CAPABILITY_LIFETIME
E_TRAIT_AMBIGUOUS
E_TYPE_MISMATCH
E_NONEXHAUSTIVE_MATCH
E_FFI_CONTRACT
E_CONSTANT_TIME_VIOLATION
```

Không dùng text làm API.

---

# 3. Severity

Core:

```text
Error
Warning
Note
Help
Info
```

Compiler có thể có internal severity nhưng public protocol ổn định.

---

# 4. Primary span

Một diagnostic phải chỉ rõ **vị trí chính gây lỗi**.

Ví dụ:

```ax
let y = x;
```

Nếu `x` đã moved:

```text
error[E_USE_AFTER_MOVE]
    x was moved here
                 ^^^
```

---

# 5. Secondary spans

Diagnostic phải chỉ được:

```text
move location
use location
owner declaration
capability creation
conflicting access
```

Ví dụ:

```text
x created here
   ↓
x moved here
   ↓
x used here ← error
```

---

# 6. Causal graph

Axiom nên lưu nguyên nhân dưới dạng graph:

```text
DiagnosticGraph
```

Ví dụ:

```text
x
 │
 ├── Move @ line 20
 │
 └── Use @ line 25
        │
        └── E_USE_AFTER_MOVE
```

Không chỉ text message.

---

# 7. Ownership diagnostics

Ví dụ:

```ax
fn consume(x: Buffer) {}

fn main() {
    let b = Buffer(...);
    consume(b);
    print(b);
}
```

Compiler không cần nói:

```text
borrow of moved value
```

theo kiểu Rust.

Nó nói theo semantic model Axiom:

```text
E_USE_AFTER_MOVE

`b` was transferred to `consume`.

Ownership:
    b → consume parameter

The value is no longer owned by this scope.

Use occurs here:
    print(b)

Possible fixes:
    • use `b` before calling `consume`
    • pass a read view if ownership is not required
    • create an explicit clone if duplication is intended
```

---

# 8. Compiler phải hiểu ý định API

Nếu:

```ax
fn consume(x: Buffer)
```

cần ownership.

Nếu programmer thực sự muốn đọc:

```ax
fn inspect(x: view<Buffer>)
```

compiler suggestion có thể chỉ ra semantic mismatch.

Compiler **không tự đổi source** nếu có nhiều cách đúng.

---

# 9. Capability diagnostics

Ví dụ:

```ax
let a = mut_view(buffer);
let b = mut_view(buffer);
```

Diagnostic:

```text
E_CAPABILITY_CONFLICT

Mutable capability `b` conflicts with existing mutable capability `a`.

Region:
    buffer[0..1024]

Existing capability:
    a
    WRITE
    lifetime: ...

Conflicting capability:
    b
    WRITE
```

---

# 10. Disjoint region explanation

Nếu:

```ax
let a = mut_view(buffer[0..512]);
let b = mut_view(buffer[512..1024]);
```

compiler có thể prove:

```text
DISJOINT
```

và không báo lỗi.

Nếu không prove được:

```text
UNKNOWN
```

thì không được giả định disjoint.

---

# 11. Lifetime explanation không dùng lifetime syntax

Axiom không bắt programmer viết:

```text
'a
```

Diagnostic thay bằng:

```text
Capability created here
        ↓
Capability stored here
        ↓
Owner destroyed here
        ↓
Capability would become invalid
```

---

# 12. Escape diagnostics

Ví dụ trả về view của local:

```ax
fn bad() -> view<i32> {
    let x = 10;
    return view(x);
}
```

Diagnostic:

```text
E_CAPABILITY_LIFETIME

Returned view refers to local storage `x`.

Owner lifetime:
    function scope

Required lifetime:
    returned value

The owner does not outlive the returned capability.
```

---

# 13. Stable address diagnostics

Nếu compiler không thể promote/relocate vì address observable:

```text
INFO_STORAGE_CONSTRAINT
```

Ví dụ:

```text
address of `x` is observable;
stack/register promotion is disabled.
```

Đây là optimization explanation, không phải error.

---

# 14. Initialization diagnostics

```text
E_UNINITIALIZED_READ
```

graph:

```text
x
 ├── declaration
 ├── path A → initialized
 └── path B → UNINIT
                   ↓
               read here
```

Compiler chỉ reject nếu không chứng minh được initialization trên **mọi reachable path**.

---

# 15. Partial move diagnostics

Ví dụ:

```ax
let x = obj.a;
use(obj);
```

Nếu `obj.a` moved nhưng `obj.b` còn sống:

```text
E_PARTIAL_MOVE_USE
```

Compiler hiển thị:

```text
obj
 ├── a → MOVED
 └── b → INIT
```

---

# 16. Drop diagnostics

Nếu custom Drop khiến partial move không hợp lệ:

```text
E_PARTIAL_MOVE_DROP
```

và giải thích:

```text
`T` has a user-defined Drop implementation.

Moving field `a` independently would prevent
the required complete Drop operation.

Possible fixes:
    • move the whole value
    • provide an explicit extraction operation
    • redesign ownership
```

---

# 17. Trait diagnostics

Không:

```text
trait bound not satisfied
```

một cách mơ hồ.

Ví dụ:

```text
E_TRAIT_NOT_IMPLEMENTED

Required:
    T: Hash

For:
    Packet

Candidate implementations:
    none

The obligation originates from:
    hash_map.insert(packet)
```

---

# 18. Ambiguous trait resolution

Nếu có nhiều candidates:

```text
E_TRAIT_AMBIGUOUS
```

Compiler hiển thị:

```text
Candidate A
Candidate B

Neither candidate is more specific.

Disambiguate using:
    TraitA::method(...)
or
    explicit type information
```

---

# 19. Generic diagnostics

Ví dụ:

```text
E_TYPE_MISMATCH

expected:
    T

found:
    String

Constraint chain:
    foo<T>
      ↓
    T: Numeric
      ↓
    String does not satisfy Numeric
```

---

# 20. Match diagnostics

Ví dụ:

```ax
match x {
    Some(v) => use(v),
}
```

Compiler:

```text
E_NONEXHAUSTIVE_MATCH

Missing constructor:
    None

Matched:
    Some(_)

Required constructors:
    Some
    None
```

Không chỉ nói “non-exhaustive”.

---

# 21. Unreachable pattern

```text
W_UNREACHABLE_PATTERN
```

Compiler phải chỉ rõ constructor trước đó đã bao phủ pattern này.

---

# 22. Type error recovery

Compiler không dừng ngay ở lỗi đầu tiên.

Ví dụ:

```text
source
 ↓
parse
 ↓
recover
 ↓
resolve
 ↓
type check
 ↓
diagnostics
```

Error sentinel:

```text
ErrorType
ErrorSymbol
```

nhưng:

> **Error sentinel không bao giờ được codegen.**

---

# 23. Parser recovery

Ví dụ thiếu `}`:

```ax
fn foo() {
    let x = 10;
```

Parser tạo recovery node và tiếp tục phân tích file/module để phát hiện thêm lỗi.

---

# 24. Không tạo “cascade errors” vô nghĩa

Nếu:

```text
missing type
```

dẫn đến 30 lỗi giả:

```text
unknown operator
unknown field
trait missing
...
```

compiler phải suppress diagnostics phụ thuộc vào một root error khi có thể.

---

# 25. Diagnostic dependency graph

Mỗi diagnostic có:

```text
CausedBy[]
```

Compiler có thể phân biệt:

```text
ROOT ERROR
DERIVED ERROR
```

để IDE chỉ hiển thị lỗi có ích.

---

# 26. Suggested fix

Suggestion phải có:

```text
TextEdit {
    File
    Range
    Replacement
}
```

Không chỉ:

```text
try changing this
```

---

# 27. Fix phải có confidence

Ví dụ:

```text
MachineApplicable
MaybeApplicable
Informational
```

IDE chỉ auto-apply khi compiler tuyên bố fix đủ an toàn.

---

# 28. Không tự ý sửa semantics

Compiler không được đề xuất:

```text
clone everything
```

chỉ để làm mất ownership error.

Suggestion phải phản ánh semantic intent.

---

# 29. Multiple fixes

Một lỗi có thể có:

```text
Fix A: Move before use
Fix B: Use view
Fix C: Clone
```

Compiler không chọn thay programmer nếu chúng có semantics khác nhau.

---

# 30. Human-readable diagnostic

Terminal:

```text
error[E_CAPABILITY_CONFLICT]: overlapping mutable access

  --> main.ax:24:13
   |
24 |     process(b)
   |             ^ mutable access conflicts with `a`
   |
note: `a` holds a mutable capability to this region
  --> main.ax:20:13
   |
20 |     let a = mut_view(buffer)
   |             ^^^^^^^^^^^^^^^^
   |
help: end `a` before creating the second mutable capability
```

---

# 31. Machine-readable diagnostic

Compiler đồng thời emit:

```json
{
  "code": "E_CAPABILITY_CONFLICT",
  "severity": "error",
  "primary_span": "...",
  "related": [],
  "facts": {
    "access": "WRITE",
    "region_relation": "OVERLAPS"
  }
}
```

Đây mới là API chính cho tooling.

---

# 32. Diagnostic protocol

Đề xuất:

```text
Axiom Diagnostic Protocol
```

có version:

```text
diagnostic_schema_version
```

để IDE/AI không phụ thuộc compiler text.

---

# 33. IDE integration

IDE có thể query:

```text
type_at(position)
definition_at(position)
references(symbol)
diagnostics(file)
completion(position)
hover(position)
signature(position)
ownership_at(position)
capability_at(position)
effects(function)
```

Tất cả dùng chung `CompilerDB`.

---

# 34. Không xây compiler server riêng biệt

CLI và IDE dùng cùng:

```text
CompilerDB
```

không có hai semantic engine khác nhau.

---

# 35. Incremental diagnostics

Nếu sửa một dòng:

```text
foo.ax
```

chỉ query bị ảnh hưởng được invalidated.

Không type-check lại toàn workspace nếu không cần.

---

# 36. Cancellation

IDE query:

```text
type_at(position)
```

có thể bị hủy khi user gõ tiếp.

CompilerDB phải hỗ trợ:

```text
CancellationToken
```

đã phù hợp với `ACDB`.

---

# 37. AI-native compiler API

Axiom nên coi AI như một **client của compiler**, không phải một thành phần semantic.

Ví dụ:

```text
axc query type
axc query symbol
axc query diagnostics
axc query ownership
axc query capability
axc query effects
axc query callgraph
axc query optimization
```

---

# 38. AI không đọc source thay compiler nếu compiler đã biết

Thay vì AI phải tự suy luận:

```text
"biến này có ownership gì?"
```

compiler trả:

```text
{
    "ownership": "Owned",
    "state": "Initialized",
    "drop": true
}
```

Điều này giảm hallucination.

---

# 39. `axc explain`

Đề xuất unified command:

```text
axc explain <query>
```

Ví dụ:

```text
axc explain E_USE_AFTER_MOVE
axc explain optimization foo
axc explain ownership x
axc explain capability x
axc explain trait Foo<T>
axc explain storage x
axc explain vectorization foo
```

---

# 40. Compiler reasoning graph

Compiler có thể expose:

```text
FactGraph
```

Ví dụ:

```text
buffer
 │
 ├─ ownership → local #3
 │
 ├─ capability #8
 │      ├─ READ
 │      └─ region [0,512)
 │
 ├─ capability #9
 │      └─ WRITE [512,1024)
 │
 └─ allocation #4
```

AI có thể consume trực tiếp.

---

# 41. Optimization explanation

Ví dụ:

```text
axc explain optimization foo
```

trả:

```text
Loop #2

Bounds checks:
    eliminated

Reason:
    ScalarEvolution proves:
        0 <= i < n

Alias:
    a and b proven disjoint

Vectorization:
    width = 8

Reason:
    no loop-carried dependency
    target supports SIMD width 8

Allocation:
    none

Reason:
    NoEscape
```

Đây chính là kiểu compiler transparency Axiom cần.

---

# 42. “Why not optimized?”

Một command cực kỳ hữu ích:

```text
axc explain why-not foo
```

Ví dụ:

```text
Vectorization rejected.

Reason:
    E_LOOP_DEPENDENCY

Dependency:
    store a[i]
       ↓
    load a[i-1]

Required transformation:
    dependency removal

No valid transformation found.
```

---

# 43. Optimization confidence

Compiler có thể phân biệt:

```text
PROVEN
DERIVED
HEURISTIC
PROFILE
UNKNOWN
```

AI không nên nhầm heuristic với proof.

---

# 44. Safety confidence

Tương tự:

```text
Semantic proof
Trusted unsafe contract
External contract
Unknown
```

Không gọi “likely safe”.

---

# 45. Compiler fact hierarchy

Giữ nguyên hierarchy:

```text
SEMANTIC PROOF
      ↓
VERIFIED FACT
      ↓
OPTIMIZATION FACT
      ↓
PROFILE OBSERVATION
      ↓
COST HEURISTIC
```

Diagnostic API phải preserve hierarchy này.

---

# 46. No AI semantic authority

AI có thể:

```text
suggest
explain
generate
refactor
```

nhưng không thể nói:

```text
"compiler, assume this is safe"
```

để bypass verifier.

---

# 47. AI-generated source

Nếu AI tạo:

```text
source
```

vẫn phải đi qua:

```text
lexer
parser
resolver
type
trait
MIR
verification
```

như source của người.

---

# 48. AI compiler loop

Architecture:

```text
AI
 ↓
Compiler Query
 ↓
Structured Diagnostic
 ↓
AI analyzes
 ↓
Source modification
 ↓
Compiler
```

Không:

```text
AI → directly modify MIR → executable
```

---

# 49. Stable IDs

AI API nên dùng:

```text
FunctionId
DeclarationId
TypeId
FieldId
RegionId
CapabilityId
DiagnosticId
```

thay vì tên text khi có thể.

---

# 50. Source spans

Tất cả AI actions phải trỏ về:

```text
SourceFileId
byte offset
length
```

để không sửa nhầm symbol cùng tên.

---

# 51. Compiler snapshots

AI/IDE có thể yêu cầu:

```text
snapshot
```

để thực hiện nhiều query trên cùng compiler revision.

Điều này tránh:

```text
query A
source changes
query B
```

sinh ra inconsistent result.

---

# 52. Structured compiler events

Build pipeline:

```text
BuildEvent {
    BuildId
    Phase
    Input
    Output
    Duration
    CacheHit
    Diagnostics
    Provenance
}
```

phù hợp với `ABUILD`.

---

# 53. Performance diagnostics

Compiler có thể expose:

```text
axc explain compile foo
```

Ví dụ:

```text
parse       2ms
resolve     4ms
typecheck   8ms
trait       5ms
MIR         3ms
verify      7ms
optimize    32ms
codegen     12ms
link        4ms
```

---

# 54. Cache diagnostics

Ví dụ:

```text
axc explain cache foo
```

```text
cache miss

invalidated by:
    dependency interface fingerprint changed

unchanged:
    source parser
    type definitions
    unrelated modules
```

Rất hữu ích cho AI agent.

---

# 55. Compiler crash vs user error

Phân biệt tuyệt đối:

```text
User diagnostic
Compiler internal error
Compiler bug
```

Ví dụ:

```text
ICE-VERIFY-001
```

không được hiển thị như programmer error.

---

# 56. ICE report

Compiler crash report nên có:

```text
compiler version
target
build profile
query
phase
source fingerprint
IR fingerprint
reproducer
```

nhưng phải tránh leak secret/source nếu không cần.

---

# 57. Minimal reproducer

Tooling có thể hỗ trợ:

```text
axc minimize-error
```

để giảm source tới testcase nhỏ nhất gây lỗi compiler.

Đây sẽ cực kỳ hữu ích khi Axiom compiler phát triển.

---

# 58. Diagnostic testing

Mỗi stable diagnostic code phải có test:

```text
positive
negative
span
message structure
fix
related spans
machine representation
```

Không test dựa hoàn toàn vào full text.

---

# 59. Localization

Diagnostic semantic payload không phụ thuộc ngôn ngữ.

Ví dụ:

```text
code = E_USE_AFTER_MOVE
facts = {...}
```

Text có thể được localization.

---

# 60. Human language

Compiler ban đầu:

```text
English
```

nhưng architecture cho phép:

```text
Vietnamese
English
...
```

mà không thay đổi diagnostic identity.

---

# 61. Terminal rendering

Renderer riêng:

```text
Diagnostic Model
       ↓
┌──────┼──────────┐
CLI   IDE       JSON/AI
```

Không để semantic compiler phụ thuộc terminal formatting.

---

# 62. JSON/JSONL

AI/CI thích hợp với:

```text
--diagnostic-format=json
--diagnostic-format=jsonl
```

JSONL đặc biệt tốt cho agent vì mỗi event một record.

---

# 63. LSP

Axiom IDE adapter có thể implement:

```text
LSP
```

nhưng LSP chỉ là transport/protocol layer.

Compiler semantic model vẫn là Axiom.

---

# 64. Build machine interface

CI có thể dùng:

```text
exit code
diagnostic code
source span
machine fix
```

thay vì parse terminal text.

---

# 65. AI task interface

Có thể thêm:

```text
axc task
```

trả:

```text
goal
affected files
diagnostics
dependencies
available compiler facts
suggested actions
```

AI agent không cần tự crawl compiler internals.

---

# 66. Compiler explainability không được làm chậm release

Detailed reasoning metadata có thể chỉ giữ trong:

```text
debug
developer
AI
diagnostic
```

profiles.

Release compiler có thể giảm metadata nhưng semantic result không thay đổi.

---

# 67. Determinism

Cùng source/config:

```text
diagnostic code
primary span
semantic facts
```

phải deterministic.

Ordering của diagnostics cũng phải deterministic.

---

# 68. Parallel diagnostics

Compiler có thể kiểm tra song song nhưng output phải được canonicalize:

```text
file
span
diagnostic code
```

để thứ tự không phụ thuộc thread scheduling.

---

# 69. Diagnostic fingerprint

Đề xuất:

```text
DiagnosticFingerprint {
    Code
    SourceSpan
    SemanticOrigin
    RelatedOrigins
}
```

Dùng cho incremental IDE và CI.

---

# 70. Invariants

Đóng băng:

### `ADIAG-20`
Diagnostics are structured semantic objects, not formatted text.

### `ADIAG-21`
Every stable compiler diagnostic has a machine-readable code.

### `ADIAG-22`
Diagnostic identity does not depend on human-readable wording.

### `ADIAG-23`
Diagnostics have precise source provenance.

### `ADIAG-24`
Diagnostics may contain primary and secondary source spans.

### `ADIAG-25`
Compiler may represent causal relationships between diagnostics.

### `ADIAG-26`
Root diagnostics are distinguishable from derived diagnostics.

### `ADIAG-27`
Error recovery must minimize cascading diagnostics.

### `ADIAG-28`
Parser recovery may continue analysis after recoverable syntax errors.

### `ADIAG-29`
Error symbols/types are never valid code-generation inputs.

### `ADIAG-30`
Suggested fixes are structured edits.

### `ADIAG-31`
Machine-applicable fixes are explicitly identified.

### `ADIAG-32`
Compiler must not silently change program semantics through automatic fixes.

### `ADIAG-33`
Ownership diagnostics explain semantic ownership transitions.

### `ADIAG-34`
Capability diagnostics expose conflicting access regions where available.

### `ADIAG-35`
Lifetime diagnostics do not require programmer-written lifetime syntax.

### `ADIAG-36`
Initialization diagnostics expose relevant control-flow paths where practical.

### `ADIAG-37`
Trait diagnostics expose relevant obligation and candidate information.

### `ADIAG-38`
Pattern diagnostics expose missing or unreachable constructors.

### `ADIAG-39`
Optimization diagnostics distinguish proof from heuristic reasoning.

### `ADIAG-40`
Compiler optimization explanations never constitute semantic authority.

### `ADIAG-41`
`why-not` analysis may explain failed optimization legality.

### `ADIAG-42`
Compiler reasoning can be represented as structured fact graphs.

### `ADIAG-43`
Semantic facts have stable identifiers where practical.

### `ADIAG-44`
AI tooling consumes compiler facts rather than replacing compiler semantics.

### `ADIAG-45`
AI-generated source is verified identically to human-written source.

### `ADIAG-46`
AI cannot bypass ownership, safety, type, or ABI verification.

### `ADIAG-47`
IDE and CLI use the same semantic CompilerDB.

### `ADIAG-48`
IDE queries are incremental and cancellable.

### `ADIAG-49`
Compiler snapshots provide consistent multi-query views.

### `ADIAG-50`
Build events are machine-readable.

### `ADIAG-51`
Cache behavior can be explained through structured dependency information.

### `ADIAG-52`
Compiler internal failures are distinguished from user diagnostics.

### `ADIAG-53`
Compiler crash reports preserve relevant compiler provenance.

### `ADIAG-54`
Diagnostic tests validate semantic identity rather than fragile formatted text.

### `ADIAG-55`
Diagnostic localization does not alter diagnostic identity.

### `ADIAG-56`
Terminal rendering is separate from semantic diagnostics.

### `ADIAG-57`
JSON/JSONL diagnostic output is supported.

### `ADIAG-58`
IDE integration may use LSP or another protocol without changing compiler semantics.

### `ADIAG-59`
Diagnostic ordering is deterministic.

### `ADIAG-60`
Parallel compilation must not make diagnostic semantics nondeterministic.

### `ADIAG-61`
Diagnostic fingerprints support incremental tooling.

### `ADIAG-62`
Detailed compiler reasoning is optional metadata and does not become mandatory runtime state.

### `ADIAG-63`
Performance diagnostics expose compiler phase and cache information.

### `ADIAG-64`
Optimization explanations may expose legality, profitability and cost separately.

### `ADIAG-65`
Safety facts are distinguished from optimization facts.

### `ADIAG-66`
Profile observations are distinguished from proofs.

### `ADIAG-67`
Compiler diagnostics never treat heuristic observations as semantic guarantees.

### `ADIAG-68`
Source-to-IR provenance remains available to developer tooling where metadata is retained.

### `ADIAG-69`
AI-facing compiler interfaces use structured semantic data whenever practical.

### `ADIAG-70`
Compiler UX must expose complexity generated by the compiler without transferring that complexity to the programmer.

---

# Một điểm rất quan trọng được khóa

Axiom bây giờ có ba lớp **“compiler transparency”**:

```text
                 AXIOM
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
   Safety       Optimize      Debug
       │           │           │
       ▼           ▼           ▼
 "Tại sao      "Tại sao      "Giá trị này
 không hợp     không tối     đang ở đâu?"
 lệ?"           ưu?"
       │           │           │
       └───────────┼───────────┘
                   ▼
             Fact / Proof Graph
```

Đây là một trong những đặc điểm đáng giữ của Axiom: **compiler không phải một hộp đen**.

---

# BOOTSTRAP-163 — Compiler Performance, Parallel Compilation & Incremental Build Engine

Bước tiếp theo là tối ưu **chính compiler Axiom**.

Ta đã thiết kế compiler có:

- query database,
- incremental compilation,
- generic solver,
- comptime,
- MIR verification,
- SSA/MemorySSA,
- interprocedural analysis,
- LTO,
- PGO,
- backend riêng,
- linker riêng.

Nếu không thiết kế compiler execution architecture tốt, chính Axiom compiler sẽ trở thành bottleneck.

Task này sẽ khóa:

```text
Source Graph
      ↓
Incremental Dependency Graph
      ↓
Parallel Query Scheduler
      ↓
Work Stealing
      ↓
Fine-Grained Caching
      ↓
Parallel Frontend
      ↓
Parallel Verification
      ↓
Parallel Optimization
      ↓
Parallel Codegen
      ↓
Parallel Object/Link
      ↓
Incremental Artifact Cache
```

với mục tiêu:

> **Axiom phải compile các project lớn nhanh, tận dụng toàn bộ CPU, nhưng vẫn deterministic, reproducible và không đánh đổi correctness để lấy tốc độ.**