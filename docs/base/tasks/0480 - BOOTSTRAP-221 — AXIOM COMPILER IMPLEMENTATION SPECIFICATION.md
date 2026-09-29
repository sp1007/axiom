# BOOTSTRAP-221 — AXIOM COMPILER IMPLEMENTATION SPECIFICATION

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là bước biến toàn bộ thiết kế trước đó thành **implementation contract**.

Từ đây, agent không còn được tự do “thiết kế lại compiler” trong lúc code. Agent chỉ được implement theo contract; nếu phát hiện mâu thuẫn thật sự với semantic kernel thì phải tạo **Architecture Decision Request**, không tự ý sửa semantics.

---

# 1. Compiler implementation contract

Compiler Axiom được chia thành 5 tầng:

```text
┌────────────────────────────────────────────┐
│  FRONTEND                                  │
│  source → syntax → resolution → typed HIR │
├────────────────────────────────────────────┤
│  SEMANTIC CORE                             │
│  MIR → ownership → capability → effects   │
├────────────────────────────────────────────┤
│  EXECUTION / OPTIMIZATION                  │
│  interpreter → SSA → OptIR                │
├────────────────────────────────────────────┤
│  CODE GENERATION                            │
│  ABI → LIR → Machine IR → Object          │
├────────────────────────────────────────────┤
│  PLATFORM                                   │
│  Linker → Runtime → executable             │
└────────────────────────────────────────────┘
```

Dependency chỉ đi **từ trên xuống dưới** theo pipeline.

---

# 2. Repository implementation

Chuẩn hóa repository:

```text
axiom/
├── compiler/
│   ├── core/
│   ├── source/
│   ├── syntax/
│   ├── lexer/
│   ├── parser/
│   ├── ast/
│   ├── resolve/
│   ├── types/
│   ├── traits/
│   ├── hir/
│   ├── mir/
│   ├── verify/
│   │   ├── ownership/
│   │   ├── capability/
│   │   ├── effects/
│   │   ├── concurrency/
│   │   └── patterns/
│   ├── comptime/
│   ├── async/
│   ├── interpreter/
│   ├── opt/
│   ├── abi/
│   ├── lir/
│   ├── backend/
│   │   ├── x86_64/
│   │   ├── aarch64/
│   │   └── wasm/
│   ├── object/
│   ├── linker/
│   ├── runtime/
│   ├── diagnostics/
│   ├── source_map/
│   ├── query/
│   └── driver/
│
├── std/
├── runtime/
├── targets/
├── tests/
├── tools/
├── docs/
└── bootstrap/
```

---

# 3. `compiler/core`

Đây là module không được phụ thuộc frontend.

Nó chứa:

```text
Id
Span
Fingerprint
Revision
TargetId
Result
Diagnostic primitives
Arena
Interner
BitSet
IndexMap
```

Ví dụ:

```text id="v4e2y5"
struct TypeId(u32, u32)
struct FunctionId(u32, u32)
struct LocalId(u32, u32)
struct RevisionId(u64)
```

`core` không biết:

```text
AST
HIR
MIR
LLVM
```

---

# 4. `compiler/source`

API tối thiểu:

```text id="0d2kg2"
SourceFileId
SourceFile
SourceMap
LineMap
TextRange
SourceSpan
```

API:

```text id="7eww9y"
load_file(path)
set_file_content(id, text)
file_content(id)
span_text(span)
line_col(span)
```

Invariant:

```text id="xk0e7m"
mọi SourceSpan đều thuộc một SourceFile hợp lệ
```

---

# 5. `compiler/lexer`

API:

```text id="3g4gqf"
lex(file_id) -> TokenStream
```

Token:

```text id="nq9t7j"
Token {
    kind
    span
    raw_text
}
```

Trivia:

```text id="t8v2k9"
Whitespace
Newline
LineComment
BlockComment
```

Lexer **không** resolve identifier.

---

# 6. `compiler/syntax`

Lossless syntax tree:

```text id="q4z7wl"
SyntaxNodeId
SyntaxNode
SyntaxKind
SyntaxTree
```

Mục tiêu:

```text id="p6nhbr"
source
→ tokens
→ lossless syntax tree
```

Formatter và IDE có thể dùng trực tiếp.

---

# 7. `compiler/parser`

Parser API:

```text id="h6e5d1"
parse(file_id) -> SyntaxTree
```

Parser recovery phải tạo:

```text id="3g0x0a"
MissingToken
ErrorNode
MissingNode
```

Không panic vì user source sai.

---

# 8. `compiler/ast`

AST được xây từ syntax tree:

```text id="8e5p3r"
lower_ast(syntax_tree)
```

AST node:

```text id="4yzlku"
ExprId
StmtId
PatternId
TypeSyntaxId
DeclId
```

AST vẫn giữ `SourceSpan`.

---

# 9. `compiler/resolve`

Đây là module đầu tiên sử dụng `CompilerDB`.

API:

```text id="o6vujp"
resolve_module(module_id)
resolve_name(scope, name)
resolve_expr(expr_id)
resolve_function(function_id)
```

Output:

```text id="e9kjdr"
Resolution {
    Resolved(DeclarationId)
    Ambiguous(...)
    NotFound(...)
}
```

Không heuristic.

---

# 10. `compiler/types`

API trung tâm:

```text id="uh1sh6"
type_of(expr)
type_of_place(place)
unify(a, b)
coerce(a, b)
instantiate(type, substitutions)
```

Type enum:

```text id="cb7j91"
Primitive
Tuple
Array
Struct
Enum
Function
Closure
GenericParam
GenericInstance
TraitObject
View
MutView
Unit
Never
Error
```

`ErrorType` chỉ phục vụ recovery.

Không được để `ErrorType` trở thành bằng chứng type compatibility.

---

# 11. `compiler/traits`

Trait solver:

```text id="23gc7s"
solve(goal) -> SolverResult
```

Các trạng thái:

```text id="zq9m3w"
Proven
NotProven
Ambiguous
Error
```

Solver phải có:

```text id="d9m9w5"
candidate collection
unification
substitution
coherence
cycle detection
memoization
depth/resource limit
```

---

# 12. `compiler/hir`

HIR phải normalize:

- method call;
- extension method;
- implicit ephemeral view;
- desugared control flow;
- operator resolution;
- generic resolution;
- implicit conversions được phép.

Ví dụ:

```axiom id="e5b8d9"
p.length()
```

thành:

```text id="a3v4qx"
Call(
    FunctionId(length),
    [p]
)
```

---

# 13. `compiler/mir`

MIR API:

```text id="l0v5am"
lower_to_mir(function_id)
```

Core structs:

```text id="c4b8mz"
MirFunction
BasicBlock
Local
Place
Projection
Operand
RValue
Statement
Terminator
```

MIR không được chứa syntax-level ambiguity.

---

# 14. MIR validity checker

Trước ownership verifier phải có:

```text id="0m7v7j"
validate_mir(mir)
```

Kiểm tra:

```text id="d2d6pp"
block IDs valid
terminator exists
places valid
types consistent
CFG edges valid
locals defined
instructions structurally valid
```

Một MIR invalid không được đưa vào semantic verifier.

---

# 15. Ownership verifier

API:

```text id="xq2t6h"
verify_ownership(mir)
```

State:

```text id="y3q5ha"
OwnershipMap {
    Place → OwnershipState
}
```

Phân tích:

```text id="t9rypo"
forward dataflow
```

với merge:

```text id="50o2tc"
join(state_a, state_b)
```

phải conservative.

Nếu một branch:

```text id="q1x3d8"
Owned
```

và branch kia:

```text id="m9h4pf"
Moved
```

thì merge không được tự chọn `Owned`.

---

# 16. Capability verifier

API:

```text id="9gq9qk"
verify_capabilities(mir, ownership_facts)
```

Theo dõi:

```text id="2r0z6y"
CapabilityId
Provenance
Region
Access
Lifetime
StorageDomain
ExecutionDomain
```

Mỗi capability phải có origin.

Không có:

```text id="6m6jgy"
anonymous safe capability
```

---

# 17. Effect verifier

```text id="0x5p5j"
infer_effects(function)
```

Output:

```text id="s2cr1w"
EffectSet
```

Call graph có thể propagate effects.

Nhưng không được tự coi function là pure chỉ vì body hiện tại chưa thấy IO nếu FFI/indirect call chưa được chứng minh.

---

# 18. Pattern verifier

```text id="y3k7xk"
check_exhaustiveness(match_expr)
```

Phải output:

```text id="7t4o4x"
Exhaustive
MissingPatterns
UnreachableArms
```

---

# 19. `VerifiedMIR`

Không sử dụng:

```text id="qj8h7g"
bool verified
```

để đánh dấu.

Đây là một anti-pattern.

Thay vào đó:

```text id="t7m0wz"
struct VerifiedMir {
    mir: MirFunctionId
    proof: VerificationProofId
}
```

hoặc type-state tương đương.

Ý nghĩa:

```text id="8s3h6v"
Mir
    ≠
VerifiedMir
```

về mặt API.

---

# 20. VerificationProof

```text id="zq1k3m"
VerificationProof {
    ownership
    capabilities
    effects
    concurrency
    patterns
    async
    comptime
    ffi
    gpu
}
```

Không cần giữ toàn bộ proof graph nếu build profile không cần, nhưng compiler phải có cách tái tạo/explain.

---

# 21. Reference interpreter

API:

```text id="q7r5t2"
interpret(VerifiedMir, Input) -> ObservableResult
```

Không interpret AST trực tiếp trong production semantic tests.

AST interpreter chỉ có thể là convenience tool.

Reference authority:

```text id="t0f5jq"
Verified MIR
```

---

# 22. Runtime value model của interpreter

Interpreter value:

```text id="3gq1sn"
RuntimeValue =
    Scalar
    Aggregate
    Enum
    PointerModel
    ViewModel
    Function
    Closure
    Future
    Resource
```

Nó phải mô phỏng **semantic state**, không mô phỏng CPU instruction.

---

# 23. Comptime engine

API:

```text id="x7j9b4"
evaluate_comptime(expr, capabilities)
```

Compiler execution domain:

```text id="g4e1bz"
Compiler
```

Comptime output:

```text id="v7b2s9"
ConstValue
GeneratedDeclaration
GeneratedExpression
```

Sau generation:

```text id="m6s2p4"
generated code
→ normal resolution
→ type checking
→ verification
```

---

# 24. Async lowering

API:

```text id="c5f9yn"
lower_async(function)
```

Output:

```text id="2m7n5b"
FutureLayout
StateField[]
SuspensionPoint[]
PollFunction
```

Không generate scheduler.

---

# 25. `compiler/opt`

Pipeline:

```text id="k3e0r9"
VerifiedMIR
 ↓
SSA
 ↓
MemorySSA
 ↓
AliasAnalysis
 ↓
EffectAnalysis
 ↓
RangeAnalysis
 ↓
EscapeAnalysis
 ↓
LoopAnalysis
 ↓
OptIR
```

API:

```text id="l8y6dw"
optimize(verified_mir, target, profile)
```

---

# 26. Optimization pass contract

Mỗi pass:

```text id="7f6j5h"
Pass {
    name
    required_facts
    preconditions
    transform
    preserved_facts
    produced_facts
}
```

Ví dụ:

```text id="6y6q7v"
BoundsCheckElimination
```

requires:

```text id="g2g5a3"
RangeInfo
```

Nếu proof không tồn tại:

```text id="q0y1e3"
do nothing
```

Không speculative unsafe optimization.

---

# 27. Alias analysis

API:

```text id="w3q1l7"
alias(a, b) -> AliasRelation
```

Enum:

```text id="g4e0j7"
NO_ALIAS
MUST_ALIAS
PARTIAL_ALIAS
MAY_ALIAS
UNKNOWN
```

Chỉ:

```text id="s4e6wp"
NO_ALIAS
```

mới được dùng như internal restrict-equivalent fact.

---

# 28. Escape analysis

```text id="z5f4aa"
escape(local)
```

Output:

```text id="x1j5a6"
NoEscape
ArgumentEscape
ReturnEscape
HeapEscape
ThreadEscape
ExternalEscape
UnknownEscape
```

Dùng cho:

- stack promotion;
- allocation elimination;
- closure environment elimination.

---

# 29. ABI lowering

API:

```text id="8k5b6s"
lower_abi(function, target)
```

Output:

```text id="q7x9n2"
AbiFunction
```

Không cho backend tự tính ABI.

---

# 30. Axiom LIR

LIR phải có:

```text id="y9e0k7"
VirtualRegister
MachineOperand
MemoryOperand
CallConvention
SymbolRef
Constant
BasicBlock
```

LIR không còn generic Axiom ownership semantics, vì semantics đã verified.

Nhưng phải giữ provenance:

```text id="m6v8q2"
LIR instruction → MIR instruction → source span
```

---

# 31. Machine backend

Backend interface:

```text id="k5f7z2"
Backend {
    target()
    lower(lir)
    optimize(machine_ir)
    allocate_registers()
    encode()
}
```

Không backend nào được sửa:

```text id="j3r0v9"
ownership
capability
type correctness
```

Nếu backend phát hiện một impossible semantic state:

```text id="z2r5p4"
compiler bug
```

---

# 32. Object writer

Interface:

```text id="0k4w7p"
ObjectWriter.write(
    MachineImage,
    TargetSpec
) -> ObjectFile
```

Object model:

```text id="y1n8q4"
Section
Symbol
Relocation
TLS
Unwind
Debug
Metadata
Import
Export
```

---

# 33. Linker

API:

```text id="x5e2d9"
link(
    objects,
    libraries,
    target,
    profile
) -> Binary
```

Linker không type-check Axiom.

Nó xử lý:

```text id="q5h3s7"
symbols
sections
relocations
imports
exports
TLS
dead stripping
ICF
debug
security properties
```

---

# 34. Driver

`ax` là orchestration layer.

```text id="k7p5f1"
ax check
ax build
ax run
ax test
ax inspect
ax explain
ax query
```

Driver:

```text id="q2r9k5"
CLI
 ↓
Build configuration
 ↓
CompilerDB
 ↓
pipeline
 ↓
artifact
```

Không đặt semantic logic trong CLI.

---

# 35. Compiler pipeline API

Một compilation unit chuẩn:

```text id="0d5h9j"
compile(unit, options)
```

logic:

```text id="m5b7c1"
load sources
 ↓
parse
 ↓
resolve
 ↓
type
 ↓
HIR
 ↓
MIR
 ↓
verify
 ↓
comptime expansion
 ↓
pattern verification
 ↓
Verified MIR
 ↓
interpret/test if requested
 ↓
opt
 ↓
ABI
 ↓
LIR
 ↓
backend
 ↓
object
 ↓
link
```

Một số phase có thể lazy/query-driven thay vì chạy toàn bộ.

---

# 36. Compilation modes

Phải hỗ trợ:

```text id="g5w2w0"
check
debug
release
size
test
interpret
emit-mir
emit-optir
emit-lir
emit-object
link
```

Ví dụ:

```text id="k7q8h1"
ax check foo.ax
```

dừng sau Verified MIR.

---

# 37. `ax emit`

Để debug compiler:

```text id="q1m6v9"
ax emit ast
ax emit hir
ax emit mir
ax emit verified-mir
ax emit optir
ax emit lir
ax emit asm
ax emit obj
```

Đây sẽ cực kỳ hữu ích cho AI agent.

---

# 38. `ax explain`

Ví dụ:

```text id="t8z0p2"
ax explain move foo.ax:42
```

Output structured:

```text id="p4h8s7"
Fact
Proof
Source
Rule
Dependencies
Possible fixes
```

Tương tự:

```text id="r9d3v2"
ax explain allocation
ax explain alias
ax explain vectorization
ax explain await
ax explain send
ax explain trait
```

---

# 39. Compiler test structure

Mỗi feature:

```text id="2x7h0r"
tests/
└── ownership/
    ├── valid/
    ├── invalid/
    ├── diagnostics/
    └── regression/
```

Ví dụ:

```text id="2w0q0v"
ownership/
├── move_simple.ax
├── move_field.ax
├── move_branch.ax
├── move_loop.ax
├── use_after_move.ax
├── double_move.ax
└── drop_order.ax
```

---

# 40. Snapshot diagnostics

Diagnostic test:

```text id="d9q3m8"
source
expected diagnostic code
expected primary span
expected proof facts
```

Không snapshot toàn bộ wording nếu không cần.

Wording có thể thay đổi.

Semantic code phải ổn định:

```text id="a1e4q8"
AOWN-23
```

---

# 41. Golden MIR

MIR golden tests:

```text id="1q7z0p"
source
→ canonical MIR
```

MIR serialization phải canonical.

Không phụ thuộc:

```text id="e3y1k9"
hash-map ordering
thread ordering
memory addresses
```

---

# 42. Reference-vs-native test

Mọi program semantic test quan trọng:

```text id="9d5f4k"
ax-ref
      │
      ├── result
      │
native
      │
      └── result
```

So sánh:

```text id="w8p4q2"
ObservableResult
```

---

# 43. Compiler bootstrap implementation order

Không implement theo module tree một cách máy móc.

Thứ tự thực tế:

```text id="3e4y9r"
1. core
2. source
3. lexer
4. syntax
5. parser
6. AST
7. diagnostics
8. resolver
9. types
10. HIR
11. MIR
12. ownership
13. interpreter
14. LLVM bridge
15. native executable
```

Đây là **MVP compiler**.

---

# 44. MVP #1

Subset:

```text id="g8p2r6"
i32
bool
unit
functions
let
if
return
arithmetic
comparison
local variables
```

Chương trình:

```axiom id="wq0t8e"
fn main() -> i32 {
    let x = 10
    let y = 20
    x + y
}
```

→ executable.

---

# 45. MVP #2

Thêm:

```text id="8n0y2f"
struct
field access
arrays
indexing
enums
match
```

---

# 46. MVP #3

Thêm:

```text id="4h2p7x"
Move
Copy
Drop
view
mut_view
```

Đây là lúc Axiom bắt đầu chứng minh **memory model thật sự hoạt động**.

---

# 47. MVP #4

Thêm:

```text id="1v6r3q"
generic
trait
method
extension method
operator
```

---

# 48. MVP #5

Thêm:

```text id="y4h7z3"
comptime
async
Send
Share
atomic
sync
```

---

# 49. MVP #6

Thêm optimizer:

```text id="w7n2c5"
SSA
MemorySSA
alias
escape
range
loop
vectorization
```

---

# 50. MVP #7

Thay LLVM:

```text id="j8c3m1"
LLVM backend
     ↓
Axiom LIR
     ↓
Axiom x86-64 backend
```

---

# 51. MVP #8

Thay object/linker:

```text id="h2k8r4"
LLVM object writer
        ↓
Axiom ObjectWriter

LLD
 ↓
Axiom Linker
```

---

# 52. MVP #9

Compiler tự compile compiler:

```text id="b6q1s5"
stage0 compiler
      ↓
Axiom compiler
```

Sau đó:

```text id="q3y8k1"
Axiom compiler
      ↓
Axiom compiler
```

---

# 53. Quy tắc “không rewrite vô ích”

Khi một bootstrap component được thay thế:

```text id="f0k4z9"
LLVM backend
```

không được giữ song song mãi.

Phải có:

```text id="q4m7s3"
Bootstrap implementation
      ↓
Replacement implementation
      ↓
Conformance comparison
      ↓
Old dependency removable
```

Sau khi đạt gate:

```text id="z9c5w2"
remove bootstrap dependency
```

---

# 54. Architecture Decision Request

Nếu agent gặp:

```text id="3d0k5m"
spec conflict
```

không được tự sửa.

Tạo:

```text id="8x2m7v"
ADR {
    problem
    affected_specs
    current_rules
    conflict
    proposed_resolution
    compatibility_impact
    tests_affected
}
```

Chỉ architecture authority mới quyết định.

---

# 55. Agent task contract

Mỗi task compiler:

```text id="g7f1q3"
TASK
├── Preconditions
├── Specification references
├── Files allowed
├── API to implement
├── Invariants
├── Tests
├── Acceptance criteria
└── Next task
```

Agent hoàn thành:

```text id="r5x8n1"
Implementation
→ Tests
→ Verification
→ Commit
→ Task status
→ Continue
```

Không hỏi user nếu next task đã deterministic.

---

# 56. Dependency rule cho AI team

Agent frontend không được sửa optimizer.

Agent optimizer không được sửa semantic kernel.

Agent backend không được sửa ownership.

Nếu cần thay đổi:

```text id="z8p5r2"
ADR
```

được tạo.

Điều này cực kỳ quan trọng khi có nhiều agent chạy song song.

---

# 57. Definition of “implemented”

Không phải:

> file tồn tại.

Mà:

```text id="h4c7m1"
Specification mapped
+
API implemented
+
Positive tests
+
Negative tests
+
Integration tests
+
Invariant tests
+
Diagnostics
+
Deterministic output
+
No known semantic bypass
+
Committed
```

---

# 58. Implementation maturity

Mỗi module có:

```text id="r0m7p3"
DESIGNED
IMPLEMENTED
TESTED
CONFORMANT
FROZEN
```

Không gọi:

```text id="8p3k1x"
production-ready
```

chỉ vì compile được.

---

# 59. Một quy tắc rất quan trọng cho toàn bộ compiler

> **Compiler không được “fix” source bằng cách thay đổi semantics âm thầm.**

Ví dụ user viết:

```text id="e2q4m6"
ambiguous call
```

compiler không được chọn candidate “có vẻ đúng”.

Phải:

```text id="j7v1s4"
diagnose ambiguity
```

Tương tự:

```text id="x3k6q9"
unknown alias
```

không được biến thành:

```text id="u2z8m5"
NO_ALIAS
```

---

# 60. Axiom Compiler Implementation Contract hoàn chỉnh

Sau 221, architecture đã có ba mức:

```text id="3d5q7v"
LEVEL 1
Language Specification
        ↓
"What Axiom means"

LEVEL 2
Semantic Kernel
        ↓
"Formal rules"

LEVEL 3
Compiler Implementation Contract
        ↓
"Exactly how compiler represents and processes it"
```

Đây là điểm rất quan trọng:

**Từ đây agent có thể bắt đầu code mà không cần tiếp tục “phát minh compiler architecture”.**

---

# 61. Invariants của BOOTSTRAP-221

```text id="5v3k9m"
ACOMP-221-01
Every compiler subsystem has an explicit API boundary.

ACOMP-221-02
Compiler dependencies form a directed acyclic architecture.

ACOMP-221-03
Semantic identity is represented by typed stable IDs.

ACOMP-221-04
Semantic facts are immutable after publication within a revision.

ACOMP-221-05
Compiler phases exchange IDs and typed semantic facts rather than arbitrary mutable objects.

ACOMP-221-06
VerifiedMIR is a distinct compiler state from ordinary MIR.

ACOMP-221-07
No optimization pass may manufacture missing semantic proof.

ACOMP-221-08
No backend may reinterpret unresolved language semantics.

ACOMP-221-09
All persistent compiler artifacts contain explicit schema/version identity.

ACOMP-221-10
Every implementation phase requires positive and negative conformance tests.

ACOMP-221-11
Bootstrap dependencies must have an explicit replacement path.

ACOMP-221-12
AI agents may implement within contracts but may not silently modify semantic contracts.

ACOMP-221-13
Compiler bugs must be distinguishable from user diagnostics.

ACOMP-221-14
The compiler must be able to expose intermediate representations for inspection.

ACOMP-221-15
Source-to-machine provenance must remain recoverable.

ACOMP-221-16
Compiler output must be deterministic for identical semantic inputs.
```

---

# Trạng thái của Axiom hiện tại

Đến đây chuỗi kiến trúc đã đi từ:

```text
Ý tưởng ngôn ngữ
      ↓
Core semantics
      ↓
Memory model
      ↓
Ownership
      ↓
Capability
      ↓
Concurrency
      ↓
Async
      ↓
GPU
      ↓
Comptime
      ↓
Type/Trait
      ↓
MIR
      ↓
Verification
      ↓
Optimization
      ↓
ABI
      ↓
Backend
      ↓
Object/Linker
      ↓
Runtime
      ↓
Package/Build
      ↓
Formal Semantic Kernel
      ↓
CompilerDB
      ↓
Implementation Contract
```

**Axiom hiện không còn ở trạng thái “language design concept”. Nó đã có đủ kiến trúc để bước vào compiler engineering.**

---

# BOOTSTRAP-222 — tiếp theo

Bước tiếp theo nên đi vào phần **khó và dễ gây lỗi nhất của compiler**:

## **AXIOM-222 — FRONTEND IMPLEMENTATION: LEXER → LOSSLESS SYNTAX → AST → RESOLUTION**

Task này sẽ khóa cụ thể:

```text
Unicode/UTF-8
Token model
Keyword model
Identifier model
Numeric literals
String/byte literals
Comments/trivia
Newline semantics
Error recovery
Lossless syntax tree
AST schema
Scope tree
Module tree
Import resolution
Name resolution
Overload resolution
Method resolution
Generic name resolution
Visibility
Ambiguity handling
```

và quan trọng nhất:

```text
Source
 ↓
Tokens
 ↓
Lossless Syntax Tree
 ↓
AST
 ↓
Resolved AST
```

với **schema/enum/struct/API cụ thể đến mức agent có thể bắt đầu viết lexer và parser ngay**.

Sau 222 mới chuyển sang **Type System implementation contract**, rồi **Trait Solver**, rồi **HIR/MIR implementation contract**.