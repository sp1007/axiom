# BOOTSTRAP-273 — AXIOM COMPILER REPOSITORY & IMPLEMENTATION SPECIFICATION

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của task này là biến kiến trúc compiler thành **implementation contract** đủ chi tiết để AI agent có thể bắt đầu tạo source code mà không phải tự phát minh lại architecture.

---

# 1. Compiler implementation principle

Axiom compiler phải được xây theo nguyên tắc:

> **Semantic data structures are stable contracts; implementation containers are replaceable.**

Ví dụ:

```text
TypeId
FunctionId
ModuleId
Place
Capability
MIR
Diagnostic
```

là semantic contracts.

Còn:

```text
HashMap
Arena
Vec
RwLock
Cache implementation
```

chỉ là implementation detail.

---

# 2. Top-level compiler workspace

```text
axiom/
├── compiler/
│   ├── axc/
│   ├── common/
│   ├── source/
│   ├── syntax/
│   ├── lexer/
│   ├── parser/
│   ├── resolver/
│   ├── types/
│   ├── traits/
│   ├── consts/
│   ├── comptime/
│   ├── hir/
│   ├── mir/
│   ├── verify/
│   ├── effects/
│   ├── async/
│   ├── gpu/
│   ├── ffi/
│   ├── layout/
│   ├── abi/
│   ├── opt/
│   ├── lir/
│   ├── backend/
│   ├── object/
│   ├── linker/
│   ├── diagnostics/
│   ├── query/
│   ├── db/
│   └── tooling/
│
├── std/
├── core/
├── runtime/
├── targets/
├── tests/
├── docs/
└── tools/
```

---

# 3. Module dependency rule

Dependency direction:

```text
common
  ↓
source
  ↓
syntax
  ↓
lexer/parser
  ↓
resolver
  ↓
types/traits
  ↓
HIR
  ↓
MIR
  ↓
verify
  ↓
opt
  ↓
ABI/LIR
  ↓
backend
  ↓
object/linker
```

Không được có dependency ngược:

```text
parser → backend       ❌
types → LLVM            ❌
HIR → x86               ❌
MIR → ELF               ❌
Core semantics → GUI    ❌
```

---

# 4. `common`

Chứa primitive compiler infrastructure:

```text
Arena
InternTable
BitSet
IndexVec
SmallVec
StableMap
Fingerprint
Hash
Span
SourceId
Revision
TargetId
```

Không chứa language semantics.

---

# 5. ID architecture

Mọi semantic object quan trọng dùng typed ID:

```text
SourceFileId
PackageId
ModuleId
DeclarationId
FunctionId
StructId
EnumId
TraitId
ImplId
TypeId
FieldId
VariantId
GenericParamId
GenericInstanceId
LocalId
BasicBlockId
InstructionId
CapabilityId
RegionId
ClosureId
SuspensionPointId
DiagnosticId
```

Không dùng:

```text
u32
```

trực tiếp ở API semantic nếu có thể tránh.

---

# 6. ID representation

Bootstrap:

```text id="qk8p0d"
struct FunctionId(u32)
```

về sau có thể đổi representation mà không đổi semantic API.

---

# 7. Generational IDs

Các object có mutation/removal hoặc cache lâu dài có thể dùng:

```text
(index, generation)
```

để tránh stale handle.

---

# 8. Arena allocation

Compiler semantic objects ưu tiên arena/interning.

Ví dụ:

```text
TypeDB
 ├── TypeId(1)
 ├── TypeId(2)
 └── TypeId(3)
```

Không để mỗi query tạo hàng loạt heap object độc lập.

---

# 9. Interning

Các immutable semantic values nên intern:

```text
Type
Symbol
GenericArguments
ConstValue
Layout
EffectSet
```

Ví dụ:

```text
i32
i32
i32
```

đều có thể trỏ tới cùng:

```text
TypeId
```

---

# 10. CompilerDB

`CompilerDB` là semantic root:

```text
CompilerDB {
    SourceDB
    PackageDB
    ModuleDB
    SyntaxDB
    DeclarationDB
    TypeDB
    TraitDB
    ConstDB
    GenericDB
    ComptimeDB
    HIRDB
    MIRDB
    VerifyDB
    EffectDB
    LayoutDB
    AbiDB
    OptDB
    CodegenDB
    BuildDB
    DiagnosticDB
}
```

---

# 11. Query architecture

Mỗi query có:

```text
Input
Output
Dependencies
Fingerprint
Revision
```

Ví dụ:

```text
parse_file(SourceFileId)
    → SyntaxTree
```

```text
resolve_module(ModuleId)
    → ResolutionResult
```

```text
type_of(ExpressionId)
    → TypeId
```

---

# 12. Query purity

Semantic query nên có dạng:

```text
Input + CompilerDB state
        ↓
deterministic result
```

Không được phụ thuộc:

```text
wall clock
randomness
thread scheduling
unordered iteration
```

trừ khi đó là external capability đã được mô hình hóa.

---

# 13. Query dependency graph

Ví dụ:

```text
codegen(FunctionId)
    ↓
abi(FunctionInstance)
    ↓
layout(TypeId)
    ↓
type(Function)
    ↓
resolve(Function)
    ↓
parse(Module)
    ↓
source(File)
```

---

# 14. Incremental invalidation

Nếu sửa:

```text
fn foo()
```

thì không được compile lại toàn bộ package nếu không cần.

Query engine phải xác định:

```text
affected declarations
affected types
affected MIR
affected codegen
affected link units
```

---

# 15. Semantic fingerprint

Mỗi semantic entity quan trọng có thể có fingerprint:

```text
SemanticFingerprint {
    public_signature
    types
    traits
    effects
    repr
    abi
    comptime_dependencies
}
```

---

# 16. Source layer

```text
SourceFile {
    id
    path
    revision
    utf8_text
    line_index
}
```

Source không chứa AST.

---

# 17. SourceSpan

```text
SourceSpan {
    file: SourceFileId
    start: u32
    end: u32
}
```

Byte offset UTF-8.

---

# 18. Syntax layer

Lossless syntax tree:

```text
GreenNode
GreenToken
SyntaxNode
SyntaxToken
```

AST là semantic projection.

---

# 19. AST

AST không được trở thành database trung tâm.

Nó chỉ là:

```text
Syntax
 ↓
AST
 ↓
HIR
```

---

# 20. Resolver

Resolver tạo:

```text
Name → DeclarationId
```

Không resolve trực tiếp sang machine symbols.

---

# 21. Symbol identity

Compiler phân biệt:

```text
SourceName
DeclarationId
SymbolName
MangledName
MachineSymbol
```

Đây là năm khái niệm khác nhau.

---

# 22. TypeDB

TypeDB quản lý:

```text
PrimitiveType
StructType
EnumType
TupleType
ArrayType
ViewType
MutViewType
FunctionType
ClosureType
DynTraitType
PointerType
GenericParamType
GenericInstanceType
NeverType
UnitType
```

---

# 23. Type identity

Nominal:

```text
struct A(u64)
struct B(u64)
```

khác nhau dù representation giống nhau.

---

# 24. Type normalization

Các type generic/associated type phải được normalize trước khi kiểm tra tương thích.

---

# 25. TraitDB

Quản lý:

```text
Trait
Impl
AssociatedType
AssociatedConst
AssociatedFn
TraitGoal
SolverCache
ProofTree
```

---

# 26. Trait solver API

Conceptually:

```text
solve(goal) -> TraitResult
```

với:

```text
Proven
NotProven
Ambiguous
Error
```

Không để optimizer tự giải trait.

---

# 27. HIR

HIR phải:

- gần source semantics
- không phụ thuộc machine
- đã resolve name
- có type information
- có semantic IDs.

---

# 28. HIR không chứa register

Không có:

```text
xmm0
rax
sp
```

trong HIR.

---

# 29. MIR

MIR là semantic execution representation.

Ví dụ:

```text
BasicBlock {
    statements[]
    terminator
}
```

---

# 30. Place

```text
Place {
    base: PlaceBase
    projections: [Projection]
}
```

Projection:

```text
Field
Index
Deref
Downcast
Element
```

---

# 31. Operand

```text
Operand =
    Copy(Place)
  | Move(Place)
  | Constant(ConstValue)
```

---

# 32. RValue

Tối thiểu:

```text
Use
BinaryOp
UnaryOp
Aggregate
MakeView
MakeMutView
Cast
Bitcast
Load
AtomicLoad
```

và các operation semantic khác đã được đặc tả.

---

# 33. Terminator

```text
Goto
Branch
Switch
Return
Call
Drop
Assert
Panic
Unreachable
AwaitSuspend
Spawn
```

Async/GPU-specific information nên gắn metadata thay vì làm MIR phụ thuộc một target duy nhất.

---

# 34. Ownership state

Verifier dùng:

```text
Uninit
Owned
Moved
PartiallyMoved
Dropped
```

---

# 35. Capability state

```text
Capability {
    provenance
    region
    access
    lifetime
    storage_domain
    execution_domain
}
```

---

# 36. Region

```text
RegionRelation =
    DISJOINT
    SAME
    CONTAINS
    CONTAINED_BY
    OVERLAPS
    UNKNOWN
```

`UNKNOWN` tuyệt đối không được suy ra thành `DISJOINT`.

---

# 37. VerifyDB

Tách verifier khỏi MIR builder:

```text
MIR
 ↓
VerifyDB
 ↓
VerifiedMIR
```

`VerifiedMIR` là một semantic trust boundary.

---

# 38. VerifiedMIR không phải boolean

Không:

```text
verified = true
```

Mà nên là một typed semantic artifact:

```text
VerifiedMirBody {
    mir
    ownership_facts
    capability_facts
    effect_facts
    send_share_facts
    async_facts
    gpu_facts
}
```

---

# 39. Optimizer chỉ nhận VerifiedMIR

```text
Raw MIR → optimizer
```

**cấm.**

Chỉ:

```text
VerifiedMIR → OptIR
```

---

# 40. OptIR

OptIR chứa:

```text
SSA
MemorySSA
AliasInfo
EffectInfo
RangeInfo
EscapeInfo
LoopInfo
TargetInfo
```

---

# 41. AliasInfo

```text
AliasClass =
    NO_ALIAS
    MUST_ALIAS
    PARTIAL_ALIAS
    MAY_ALIAS
    UNKNOWN
```

---

# 42. `NO_ALIAS` chỉ từ proof

Không được:

```text
heuristic → NO_ALIAS
```

Chỉ:

```text
verified capability facts
+
proven disjointness
```

mới tạo được internal no-alias fact.

---

# 43. EffectDB

Effect set:

```text
Read
Write
Allocate
Deallocate
Drop
Atomic
Volatile
IO
Panic
Synchronize
Foreign
```

Có thể mở rộng sau.

---

# 44. LayoutDB

Layout độc lập type semantics:

```text
Layout {
    size
    alignment
    fields
    variants
    niches
    padding
    representation
}
```

---

# 45. ABI DB

ABI:

```text
AbiSignature {
    calling_convention
    params
    returns
    aggregate_rules
    sret
    alignment
    varargs
    unwind
    panic
}
```

---

# 46. LIR

Axiom LIR chỉ biểu diễn machine-independent operations:

```text
Load
Store
Add
Mul
Compare
Branch
Call
Return
Atomic
Vector
Address
Convert
```

Không có:

```text
RAX
X0
SP
V0
```

---

# 47. TargetBackend

```text
TargetBackend {
    target_spec()
    lower_abi()
    legalize()
    select()
    allocate()
    lower_frame()
    lower_atomic()
    lower_tls()
    schedule()
    verify()
    encode()
    emit_object()
}
```

---

# 48. Backend registry

```text
BackendRegistry
 ├── x86_64
 ├── arm64
 ├── riscv64
 └── wasm
```

Backend selection:

```text
TargetId
 ↓
TargetSpec
 ↓
BackendRegistry
 ↓
TargetBackend
```

---

# 49. LLVM adapter

LLVM là một backend adapter:

```text
LIR
 ↓
LLVMAdapter
 ↓
LLVM IR
```

Không được trở thành:

```text
LIR → LLVM everywhere
```

---

# 50. Object layer

Object model:

```text
AxiomObject {
    target
    sections
    symbols
    relocations
    imports
    exports
    tls
    unwind
    debug
    metadata
}
```

---

# 51. Linker layer

Linker nhận:

```text
AxiomObject[]
```

và:

```text
LinkConfig
```

trả:

```text
FinalBinary
```

---

# 52. Diagnostics

Semantic layer tạo structured diagnostic:

```text
Diagnostic {
    code
    severity
    primary_span
    secondary_spans
    message_key
    arguments
    notes
    proof
    fixes
}
```

Formatter mới biến nó thành text.

---

# 53. Diagnostic proof

Ví dụ use-after-move phải có:

```text
move_site
owner
use_site
reason
```

để IDE/AI có thể truy vấn trực tiếp.

---

# 54. Compiler API

CLI:

```text
ax check
ax build
ax run
ax test
```

không được chứa semantic implementation.

CLI chỉ orchestration.

---

# 55. `axc` API

Conceptual:

```text
Compiler {
    load_workspace()
    check()
    lower()
    verify()
    optimize()
    codegen()
    link()
}
```

---

# 56. Pipeline API

```text
compile(request)
    → CompilationResult
```

`CompilationResult` chứa:

```text
artifacts
diagnostics
statistics
semantic_fingerprint
codegen_fingerprint
```

---

# 57. Partial compilation

IDE có thể gọi:

```text
check_partial()
```

nhưng kết quả partial không được coi là:

```text
VerifiedMIR
```

---

# 58. Parallelism

Compiler nên parallelize ở query level:

```text
parse(file A)
parse(file B)
parse(file C)
```

đồng thời.

Trait goals độc lập cũng có thể chạy song song.

---

# 59. Determinism

Parallel execution:

```text
thread scheduling
```

không được làm thay đổi:

```text
semantic result
diagnostic identity
symbol resolution
trait selection
```

---

# 60. Stable iteration

Không để output phụ thuộc:

```text
HashMap iteration order
```

Khi kết quả observable cần ordering:

```text
sort by stable semantic ID/source position
```

---

# 61. Compiler memory model

Compiler có thể sử dụng:

```text
arena
reference
pointer
unsafe
parallel mutable structures
```

vì đây là implementation.

Không được nhầm:

> Axiom source language không bắt programmer quản lý pointer

với:

> Compiler không được dùng pointer.

---

# 62. Compiler concurrency

Compiler nên dùng:

```text
immutable query inputs
thread-local temporary state
parallel query execution
synchronized cache publication
```

---

# 63. Global compiler state

Không dùng hidden mutable globals cho semantic state.

Tất cả semantic state đi qua:

```text
CompilerDB
```

---

# 64. Cache layers

```text
Memory cache
      ↓
Local disk cache
      ↓
Shared/content-addressed cache
```

---

# 65. Cache key

Phải bao gồm tối thiểu:

```text
source fingerprint
semantic compiler version
target
ABI
features
dependencies
comptime inputs
profile
```

---

# 66. Codegen cache

Codegen cache có thể reuse nếu:

```text
SemanticFingerprint
+
CodegenFingerprint
+
TargetId
```

không đổi.

---

# 67. Dependency graph

Compiler phải phân biệt:

```text
source dependency
semantic dependency
codegen dependency
link dependency
runtime dependency
```

---

# 68. Example

Nếu thay implementation private:

```text
fn helper()
```

nhưng public semantic API không đổi, downstream package không nhất thiết phải re-typecheck.

---

# 69. Public API fingerprint

Bao gồm:

```text
public declarations
public types
public trait contracts
public ABI
repr
effects
```

---

# 70. Private fingerprint

Private changes chủ yếu invalidate:

```text
local MIR
codegen
```

không nhất thiết invalidate downstream semantic queries.

---

# 71. Build graph

```text
Workspace
 ↓
Packages
 ↓
Modules
 ↓
Declarations
 ↓
Generic Instances
 ↓
Codegen Units
 ↓
Objects
 ↓
Link
```

---

# 72. Codegen units

Không nhất thiết:

```text
1 function = 1 object
```

Có thể nhóm:

```text
module
generic instance group
LTO unit
```

---

# 73. Generic compilation

Initial strategy:

```text
generic source
 ↓
monomorphization
 ↓
specialized MIR
```

nhưng backend có thể code-share khi profitable.

---

# 74. Compiler source itself

Compiler implementation phải ưu tiên:

```text
explicit invariants
small functions
typed IDs
immutable semantic data
structured errors
```

hơn micro-optimization premature.

---

# 75. Implementation rule

Không tối ưu compiler trước khi có measurement:

```text
profile
→ identify bottleneck
→ optimize
→ benchmark
```

---

# 76. Compiler performance metrics

Theo dõi:

```text
parse time
resolve time
type-check time
trait solving
MIR construction
verification
optimization
codegen
link
peak memory
incremental reuse
cache hit rate
```

---

# 77. Compiler observability

`axc` nên có:

```text
--stats
--timings
--query-stats
--memory-stats
--incremental-stats
```

---

# 78. AI compiler interface

Compiler cung cấp:

```text
ax query
ax explain
ax context
ax inspect
```

Output machine-readable:

```text
JSON / structured protocol
```

---

# 79. Không dùng textual parsing làm AI interface chính

AI nên nhận:

```text
DeclarationId
TypeId
Proof
Effect
Capability
Diagnostic
```

trực tiếp.

---

# 80. Compiler implementation phases

### Phase A

```text
common
source
lexer
parser
syntax
```

### Phase B

```text
resolver
types
traits
HIR
```

### Phase C

```text
MIR
interpreter
verifier
```

### Phase D

```text
x86-64
LLVM bridge
native executable
```

### Phase E

```text
optimization
ABI
object
linker
```

### Phase F

```text
RV64
ARM64
WASM
```

### Phase G

```text
self-hosting
```

---

# 81. Minimum viable compiler

Không cần implement toàn bộ Axiom trước khi chạy được chương trình.

MVP:

```text
fn main() -> i32 {
    return 42
}
```

phải đi được:

```text
source
→ lexer
→ parser
→ resolver
→ type
→ HIR
→ MIR
→ verifier
→ LIR
→ x86
→ object
→ linker
→ executable
```

---

# 82. MVP #2

```text
struct Point {
    x: i32
    y: i32
}
```

---

# 83. MVP #3

```text
enum Option<T> {
    Some(T)
    None
}
```

---

# 84. MVP #4

```text
Move
Copy
Drop
view
mut_view
```

---

# 85. MVP #5

```text
generic
trait
closure
```

---

# 86. MVP #6

```text
async
atomic
thread
```

---

# 87. MVP #7

```text
comptime
FFI
GPU
```

---

# 88. Không nên code GPU trước khi CPU semantic pipeline ổn định.

GPU phải reuse:

```text
TypeDB
Ownership
Capability
MIR
Verification
Effect
```

---

# 89. Không nên code optimizer trước verifier

Thứ tự bắt buộc:

```text
semantic correctness
 ↓
verification
 ↓
optimization
```

---

# 90. Không nên code linker trước object contract

```text
LIR
 ↓
Machine IR
 ↓
Object
 ↓
Linker
```

---

# 91. Test directory

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
├── drop/
├── async/
├── concurrency/
├── gpu/
├── ffi/
├── mir/
├── verify/
├── opt/
├── abi/
├── backend/
├── object/
├── linker/
├── runtime/
├── differential/
└── bootstrap/
```

---

# 92. Every semantic invariant gets tests

Ví dụ:

```text
AOWN-20
```

phải map được tới test:

```text
tests/ownership/AOWN-20/
```

---

# 93. Spec-to-code traceability

Mỗi implementation module nên có:

```text
SPEC REFERENCES
```

Ví dụ:

```text
verify/ownership.rs

Implements:
BOOTSTRAP-135
AOWN-20..45
AVERIFY-20..95
```

---

# 94. Đây là điểm rất hữu ích cho AI agent.

Agent có thể truy ngược:

```text
implementation
→ invariant
→ specification
→ test
```

---

# 95. Task-to-code traceability

Task:

```text
BOOTSTRAP-263
```

phải biết:

```text
backend/riscv64/
tests/backend/riscv64/
docs/design/riscv64.md
```

---

# 96. No speculative implementation

Agent không được tạo:

```text
future feature
experimental syntax
```

và coi đó là Core.

Feature chưa frozen:

```text
feature flag / isolated module
```

---

# 97. Semantic versioning của compiler

Tách:

```text
Axiom Language Version
Semantic Compiler Version
Codegen Version
Backend Version
```

---

# 98. Thay đổi backend

Không nhất thiết tăng language version.

Ví dụ cải thiện x86 instruction selection chỉ thay:

```text
CodegenFingerprint
```

---

# 99. Thay đổi semantic

Ví dụ thay:

```text
ownership rule
```

phải thay:

```text
SemanticVersion
```

và invalidate semantic caches.

---

# 100. Compiler bootstrap architecture hoàn chỉnh

```text
                         AXC
                          │
                    ┌─────┴─────┐
                    │ CompilerDB│
                    └─────┬─────┘
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
             Syntax              Package
                │                   │
                └─────────┬─────────┘
                          ▼
                      Resolver
                          │
                    Types / Traits
                          │
                         HIR
                          │
                         MIR
                          │
                      Verification
                          │
                    ┌─────┴─────┐
                    ▼           ▼
                 Effects    Capabilities
                    │           │
                    └─────┬─────┘
                          ▼
                     Verified MIR
                          │
                         OptIR
                          │
                         ABI
                          │
                        Axiom LIR
                          │
              ┌───────────┼────────────┐
              ▼           ▼            ▼
            x86-64       ARM64        RV64
              │           │            │
              └───────────┼────────────┘
                          WASM
                            │
                       Machine IR
                            │
                       AxiomObject
                            │
                         Linker
                            │
                      Native Binary
```

---

# 101. Invariants

```text
ACOMP-273-20
Compiler semantic state is represented through CompilerDB.

ACOMP-273-21
Semantic entities use stable typed identifiers.

ACOMP-273-22
Semantic IDs are distinct from source names and machine symbols.

ACOMP-273-23
Semantic objects are immutable or revision-controlled where practical.

ACOMP-273-24
Compiler queries are deterministic for identical semantic inputs.

ACOMP-273-25
Incremental invalidation is dependency-driven.

ACOMP-273-26
Semantic fingerprints include all semantics relevant to downstream validity.

ACOMP-273-27
AST is not the authoritative semantic database.

ACOMP-273-28
HIR is target-independent.

ACOMP-273-29
MIR is the authoritative semantic execution representation before optimization.

ACOMP-273-30
Raw MIR cannot enter optimization.

ACOMP-273-31
Only Verified MIR may enter OptIR construction.

ACOMP-273-32
Verified MIR is a distinct trust-boundary artifact.

ACOMP-273-33
Ownership, capability, effect and concurrency facts are explicit compiler data.

ACOMP-273-34
UNKNOWN alias information must never be treated as NO_ALIAS.

ACOMP-273-35
Layout is separate from semantic type identity.

ACOMP-273-36
ABI lowering is separate from Core type semantics.

ACOMP-273-37
Axiom LIR is target-independent.

ACOMP-273-38
Target backends implement a common TargetBackend contract.

ACOMP-273-39
Object serialization is separate from instruction selection.

ACOMP-273-40
Linking is separate from semantic compilation.

ACOMP-273-41
LLVM integration is isolated behind an adapter.

ACOMP-273-42
LLVM representations must not leak into semantic compiler layers.

ACOMP-273-43
Compiler diagnostics are structured semantic data.

ACOMP-273-44
Human-readable diagnostics are a rendering of structured diagnostics.

ACOMP-273-45
AI tooling consumes structured compiler facts rather than textual diagnostics as its primary semantic interface.

ACOMP-273-46
Parallel compiler execution must preserve deterministic semantic results.

ACOMP-273-47
Compiler caches must include semantic dependencies.

ACOMP-273-48
Backend caches must include target and codegen identity.

ACOMP-273-49
Compiler implementation details must not introduce undocumented language semantics.

ACOMP-273-50
Bootstrap implementation modules must have traceable specification references.

ACOMP-273-51
Frozen semantic specifications cannot be silently modified by implementation agents.

ACOMP-273-52
Unspecified implementation choices may evolve without changing semantic contracts.

ACOMP-273-53
Compiler optimizations must be measurable before performance-driven restructuring.

ACOMP-273-54
Reference execution and MIR execution remain available for correctness testing.

ACOMP-273-55
Self-hosted Axiom compiler must implement the same CompilerDB semantic architecture.

ACOMP-273-56
The compiler must remain capable of building freestanding programs.

ACOMP-273-57
No monolithic runtime is implicitly linked by compiler architecture.

ACOMP-273-58
Compiler architecture must support native and WASM targets through the same semantic pipeline.

ACOMP-273-59
Adding a target backend must not require frontend semantic changes.

ACOMP-273-60
Compiler architecture is implementation infrastructure and does not become part of Axiom Core syntax merely because the compiler uses it.
```

---

## Kết quả của BOOTSTRAP-273

Đến đây chúng ta đã khóa được **cả semantic architecture lẫn implementation architecture**:

```text
SPEC
 ↓
CompilerDB
 ↓
Query
 ↓
Syntax
 ↓
Semantic
 ↓
HIR
 ↓
MIR
 ↓
Verification
 ↓
OptIR
 ↓
ABI
 ↓
LIR
 ↓
TargetBackend
 ↓
Machine/Object
 ↓
Linker
```

Và quan trọng hơn, **agent giờ đã có một architecture đủ ổn định để bắt đầu code compiler thật**, thay vì tiếp tục tự thiết kế lại compiler trong lúc implementation.

### Task kế tiếp: **BOOTSTRAP-274 — AXIOM COMPILER COMMON INFRASTRUCTURE & QUERY ENGINE**

Task 274 sẽ đi sâu xuống mức implementation thực sự:

- `Arena<T>`
- typed IDs
- interning
- `IndexVec`
- `StableMap`
- `Fingerprint`
- revision/invalidation
- query keys/values
- dependency tracking
- cycle detection
- incremental recomputation
- parallel query execution
- cancellation
- diagnostic propagation
- memory ownership của CompilerDB
- serialization/cache của query results
- deterministic hashing
- và API cụ thể của **CompilerDB + QueryEngine**.

Đây sẽ là lớp hạ tầng mà **toàn bộ compiler Axiom phía trên sẽ dùng chung**.