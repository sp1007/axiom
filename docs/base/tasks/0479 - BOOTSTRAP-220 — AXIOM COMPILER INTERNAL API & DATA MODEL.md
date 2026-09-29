# BOOTSTRAP-220 — AXIOM COMPILER INTERNAL API & DATA MODEL

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là bước chuyển từ **semantic architecture** sang **compiler engineering architecture**.

Sau 220, một AI agent không còn phải tự hỏi:

> “`TypeId` nên là gì?”, “MIR Place biểu diễn thế nào?”, “CompilerDB lưu dữ liệu ở đâu?”, “các phase giao tiếp bằng object nào?”

Tất cả sẽ có contract rõ ràng.

---

# 1. Nguyên tắc trung tâm

Compiler Axiom phải có:

> **Immutable semantic facts + stable IDs + query-based access + explicit revisioning.**

Không để các subsystem truyền những object khổng lồ qua nhau.

Thay vào đó:

```text
FunctionId
    ↓
CompilerDB
    ↓
query(function)
    ↓
semantic fact
```

Ví dụ:

```text
type_of(expr_id)
layout_of(type_id)
trait_satisfies(goal)
mir_of(function_id)
ownership_of(place)
effects_of(function_id)
abi_of(function_id)
```

---

# 2. CompilerDB chính thức

Cấu trúc:

```text
CompilerDB
├── SourceDB
├── PackageDB
├── ModuleDB
├── SyntaxDB
├── DeclarationDB
├── TypeDB
├── TraitDB
├── ConstDB
├── GenericDB
├── ComptimeDB
├── HIRDB
├── MIRDB
├── VerificationDB
├── LayoutDB
├── AbiDB
├── OptDB
├── CodegenDB
├── BuildDB
├── DiagnosticDB
└── SourceMapDB
```

Nhưng đây không phải 20 database độc lập.

Chúng là **semantic query domains** nằm trong một compiler database thống nhất.

---

# 3. Stable IDs

Không dùng pointer C++/Rust trực tiếp làm identity semantic.

Chuẩn:

```text
PackageId
ModuleId
SourceFileId
DeclarationId
FunctionId
StructId
EnumId
TraitId
FieldId
VariantId
TypeId
GenericParamId
GenericInstanceId
ExprId
PatternId
LocalId
BasicBlockId
InstructionId
PlaceId
RegionId
CapabilityId
EffectId
SuspensionPointId
DiagnosticId
```

Mỗi ID có thể được biểu diễn nội bộ bằng integer.

Ví dụ:

```text
FunctionId(u32)
TypeId(u32)
LocalId(u32)
```

---

# 4. Không dùng raw index làm semantic identity

Ví dụ:

```text
Vec<Function>
```

với:

```text
FunctionId = index
```

có vấn đề khi delete/rebuild.

Axiom nên dùng:

```text
GenerationalId {
    index
    generation
}
```

hoặc equivalent stable-ID mechanism.

Mục tiêu:

```text
stale ID
   ↓
detected
```

thay vì:

```text
stale ID
   ↓
đọc nhầm object
```

---

# 5. Arena allocation

Compiler data có lifetime theo compilation session/revision.

Dùng arena/interner phù hợp cho:

```text
AST
HIR
MIR
Type
Trait
Syntax
Diagnostic
```

Không để mỗi node tự sở hữu toàn bộ subtree bằng heap allocations nhỏ lẻ.

Thay vào đó:

```text
ExprId
    ↓
ExprArena[ExprId]
```

Điều này giảm:

- fragmentation;
- allocator overhead;
- pointer chasing;
- cache misses.

---

# 6. Semantic objects immutable

Sau khi semantic fact được intern/publish:

```text
TypeId
DeclarationId
TraitId
```

không nên bị mutate tùy tiện.

Ví dụ:

```text
TypeId(42)
```

luôn đại diện cùng một semantic type trong compilation revision.

Nếu source thay đổi:

```text
revision N
    ↓
revision N+1
```

query mới có thể tạo fact mới.

---

# 7. Revision model

CompilerDB có:

```text
RevisionId
```

Ví dụ:

```text
R100
R101
R102
```

Khi user sửa một file:

```text
SourceDB.update(file)
        ↓
new Revision
```

Không invalidate toàn bộ compiler.

---

# 8. Query model

Mọi semantic computation ưu tiên dạng:

```text
query(input) -> output
```

Ví dụ:

```text
parse(SourceFileId)
resolve(ExprId)
type_of(ExprId)
layout_of(TypeId)
trait_solve(TraitGoal)
hir(FunctionId)
mir(FunctionId)
verify(FunctionId)
optimize(FunctionId)
abi(FunctionId)
codegen(FunctionId, TargetId)
```

---

# 9. Query dependency graph

Ví dụ:

```text
codegen(foo)
   ↓
abi(foo)
   ↓
layout(Point)
   ↓
type(Point)
```

CompilerDB ghi dependency:

```text
codegen(foo)
    depends on
abi(foo)

abi(foo)
    depends on
layout(Point)

layout(Point)
    depends on
type(Point)
```

Nếu `Point` thay đổi:

```text
Point
 ↓
layout
 ↓
ABI
 ↓
codegen
```

được invalidate chính xác.

---

# 10. Query purity

Semantic queries mặc định phải deterministic.

Ví dụ:

```text
type_of(expr)
```

không được:

```text
ghi file
network request
random
current time
```

Nếu cần external input:

```text
Comptime/Build capability
```

phải đi qua subsystem tương ứng.

---

# 11. Query cycle

Compiler phải phát hiện:

```text
query A
 ↓
query B
 ↓
query C
 ↓
query A
```

Không được stack overflow.

Kết quả:

```text
CycleDetected
```

hoặc semantic rule tương ứng.

Trait solver có cycle semantics riêng.

---

# 12. SourceDB

```text
SourceFile {
    id
    package
    path
    content
    content_hash
    revision
}
```

Không lưu source chỉ dưới dạng string đơn giản nếu muốn IDE tốt.

Cần:

```text
SourceId
TextRange
LineMap
Utf8BoundaryMap
```

---

# 13. SourceSpan

Chuẩn:

```text
SourceSpan {
    file: SourceFileId
    start: u32
    end: u32
}
```

Mọi semantic object quan trọng đều có provenance:

```text
ExprId → SourceSpan
TypeError → SourceSpan
MIR instruction → SourceSpan
Machine instruction → SourceSpan
```

---

# 14. Source mapping nhiều chiều

Axiom cần:

```text
Source
 ↕
AST
 ↕
HIR
 ↕
MIR
 ↕
OptIR
 ↕
LIR
 ↕
Machine Instruction
```

Không chỉ:

```text
machine → source
```

mà cả:

```text
source → machine
```

Điều này rất quan trọng cho debugger và AI.

---

# 15. DeclarationDB

Declaration:

```text
Declaration {
    id
    kind
    name
    module
    visibility
    attributes
    source_span
}
```

`kind`:

```text
Function
Struct
Enum
Trait
TypeAlias
Const
Static
Module
Extern
```

---

# 16. FunctionDB

```text
Function {
    id
    declaration
    generic_params
    parameters
    return_type
    body
    attributes
    effects
    async_info
    gpu_info
    abi_info
}
```

Không nhét MIR trực tiếp vào Function object.

MIR là query:

```text
mir(function_id)
```

---

# 17. TypeDB

Type representation:

```text
Type =
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
    Never
    Unit
    ErrorType
```

Mỗi semantic type được intern.

Ví dụ:

```text
i32
```

chỉ có một canonical `TypeId` trong revision.

---

# 18. Type interning

```text
intern(
    StructType {
        declaration = Point
    }
)
```

→

```text
TypeId(100)
```

Lần sau cùng semantic type:

```text
intern(Point)
```

→ `TypeId(100)`.

Điều này rất quan trọng cho:

- equality;
- hashing;
- generic cache;
- trait solver;
- layout cache.

---

# 19. GenericInstance

Ví dụ:

```text
Vec<i32>
```

không phải chỉ là string.

```text
GenericInstance {
    generic: Vec
    args: [
        Type(i32)
    ]
}
```

→

```text
GenericInstanceId
```

---

# 20. Place model

MIR Place:

```text
Place {
    base: PlaceBase
    projections: [Projection]
}
```

Base:

```text
Local(LocalId)
Static(DeclarationId)
Argument(LocalId)
```

Projection:

```text
Field(FieldId)
Index(LocalId / constant)
Deref
Downcast(VariantId)
Slice
```

---

# 21. Không encode ownership vào Place

Place chỉ nói:

> “đang truy cập semantic location nào?”

Ownership là analysis state:

```text
OwnershipState
```

Điều này giúp:

```text
same Place
+
different control-flow point
=
different ownership state
```

---

# 22. Operand

```text
Operand =
    Copy(Place)
    Move(Place)
    Constant(ConstValue)
```

Đây là một semantic distinction cực quan trọng.

Không dùng:

```text
Operand {
    place
    bool_is_move
}
```

nếu type system nội bộ có thể biểu diễn trực tiếp enum.

---

# 23. RValue

```text
RValue =
    Use(Operand)
    BinaryOp
    UnaryOp
    Aggregate
    MakeView
    MakeMutView
    Cast
    Bitcast
    Load
    AtomicLoad
    AtomicRmw
    FunctionRef
    Closure
    ...
```

Mỗi RValue có source provenance.

---

# 24. Statement

```text
Statement =
    Assign
    StorageLive
    StorageDead
    Drop
    CapabilityCreate
    CapabilityRelease
    Effect
```

Một số semantic event có thể được biểu diễn bằng annotations thay vì opcode nếu không cần runtime representation.

---

# 25. Terminator

```text
Terminator =
    Goto
    Branch
    Switch
    Call
    Return
    Panic
    Unreachable
    Await
```

Mỗi BasicBlock bắt buộc có đúng một terminator.

---

# 26. BasicBlock

```text
BasicBlock {
    id
    statements[]
    terminator
}
```

MIR function:

```text
MirFunction {
    function_id
    locals[]
    blocks[]
    entry_block
    return_local
    metadata
}
```

---

# 27. MIR Local

```text
Local {
    id
    type
    name?
    source_span
    flags
}
```

Flags:

```text
Parameter
Temporary
UserLocal
ReturnValue
CompilerGenerated
AddressTaken
AcrossAwait
```

---

# 28. Ownership state

Ownership verifier dùng:

```text
OwnershipState =
    Uninitialized
    Owned
    Moved
    PartiallyMoved
    Dropped
```

Nhưng state phải có **place tree**.

Ví dụ:

```text
p = PartiallyMoved
p.x = Moved
p.y = Owned
```

không chỉ một enum trên toàn object.

---

# 29. CapabilityDB

```text
Capability {
    id
    owner
    provenance
    region
    access
    lifetime
    storage_domain
    execution_domain
}
```

Compiler có thể query:

```text
capability_of(place, program_point)
```

---

# 30. RegionDB

Region không nhất thiết phải là object runtime.

```text
Region {
    id
    origin
    relation
}
```

Compiler suy ra:

```text
RegionRelation(A, B)
```

từ place/provenance.

---

# 31. EffectSet

Không cần tạo object heap cho từng effect.

Có thể dùng bitset:

```text
EffectSet = bitflags
```

Ví dụ:

```text
READ
WRITE
ALLOCATE
DEALLOCATE
DROP
ATOMIC
VOLATILE
IO
PANIC
SYNCHRONIZE
FOREIGN
```

Nhanh và dễ cache.

---

# 32. TraitGoal

```text
TraitGoal {
    self_type
    trait
    substitutions
}
```

Solver result:

```text
Proven
NotProven
Ambiguous
Error
```

Có memoization:

```text
TraitGoal → SolverResult
```

theo revision/fingerprint.

---

# 33. Layout model

`LayoutDB`:

```text
Layout {
    size
    alignment
    fields[]
    padding[]
    abi_class
    niches
}
```

Nhưng layout chỉ được query sau khi type semantics hoàn chỉnh.

```text
Type
 ↓
Layout
```

không ngược lại.

---

# 34. ABI model

```text
AbiSignature {
    calling_convention
    parameters[]
    return
    unwind
    variadic
    attributes
}
```

ABI lowering:

```text
Semantic Type
    ↓
Layout
    ↓
ABI Classification
    ↓
Physical ABI
```

---

# 35. TargetDB

```text
TargetId
```

trỏ tới:

```text
TargetSpec {
    architecture
    os
    environment
    abi
    object_format
    pointer_width
    endian
    cpu_features
    simd_features
    atomic_features
    tls
    unwind
    linker
}
```

Không để target-specific logic rải khắp frontend.

---

# 36. OptDB

Optimizer facts:

```text
AliasInfo
EffectInfo
RangeInfo
EscapeInfo
LoopInfo
MemorySSA
TargetInfo
```

được cache riêng.

Ví dụ:

```text
alias(place_a, place_b)
```

→

```text
NO_ALIAS
MUST_ALIAS
PARTIAL_ALIAS
MAY_ALIAS
UNKNOWN
```

---

# 37. Fingerprint system

Axiom cần ít nhất:

```text
SemanticFingerprint
AbiFingerprint
CodegenFingerprint
BuildFingerprint
PackageContentHash
```

Ví dụ:

```text
SemanticFingerprint
=
hash(
    public semantic API
    type definitions
    trait definitions
    repr contracts
    ABI contracts
    comptime dependencies
)
```

---

# 38. Vì sao phải tách fingerprints?

Một function đổi machine optimization:

```text
x86 instruction scheduling
```

không nhất thiết làm:

```text
SemanticFingerprint
```

thay đổi.

Nhưng:

```text
function signature
```

thay đổi:

```text
SemanticFingerprint
```

thay đổi.

Điều này giúp incremental compilation rất mạnh.

---

# 39. Diagnostic model

Diagnostic không chỉ là string.

```text
Diagnostic {
    id
    code
    severity
    primary_span
    secondary_spans[]
    message
    explanation
    proof
    suggestions[]
    related_symbols[]
}
```

Ví dụ:

```text
AOWN-23
```

có thể chứa:

```text
move site
use site
ownership state
relevant rule
```

---

# 40. Diagnostic proof

Đây là một phần đặc biệt quan trọng cho AI.

```text
ProofNode {
    fact
    source_span
    cause[]
}
```

Ví dụ:

```text
buffer is moved
    ↓
send(channel, buffer)
    ↓
channel.send consumes ownership
    ↓
buffer state = MOVED
    ↓
buffer[0] invalid
```

AI có thể đọc trực tiếp proof graph.

---

# 41. `.axdb`

Đề xuất `.axdb` là **compiler semantic snapshot**, không phải executable.

Có thể chứa:

```text
Declarations
Types
Traits
HIR
MIR
Source maps
Diagnostics
Fingerprints
ABI metadata
Optimization summaries
```

Dùng cho:

- IDE;
- LSP;
- AI;
- incremental compilation;
- debugging;
- compiler cache.

Không phải mọi build đều cần tạo `.axdb`.

---

# 42. Serialization rule

Compiler internal structures không được serialize tùy tiện.

Mỗi persistent format phải có:

```text
schema_version
compiler_semantic_version
target_version
fingerprint
```

Không đọc `.axdb` cũ bằng cách “cố đoán”.

Nếu incompatible:

```text
invalidate
```

---

# 43. Parallel compilation

CompilerDB query graph cho phép:

```text
foo()
bar()
baz()
```

phân tích song song nếu không có dependency.

Ví dụ:

```text
resolve(foo)
resolve(bar)
resolve(baz)
```

→ parallel.

Nhưng:

```text
resolve(foo)
    ↓
type(foo)
```

phải dependency-aware.

---

# 44. Deterministic parallelism

Parallel execution không được làm semantic result phụ thuộc scheduling.

Không được:

```text
thread A hoàn thành trước
→ declaration ID khác
```

IDs phải deterministic hoặc có canonicalization.

Nếu cần allocation IDs:

```text
local temporary IDs
      ↓
canonicalization
```

---

# 45. Compiler memory architecture

Không nên dùng một allocator cho mọi thứ.

Đề xuất:

```text
Short-lived
    bump arena

Semantic interned
    immutable arena

Large MIR/IR
    segmented arena

Caches
    hash tables

Persistent artifacts
    serialized storage
```

Mục tiêu:

- ít allocation;
- cache locality;
- dễ parallel;
- dễ release theo revision.

---

# 46. Revision garbage collection

Compiler không thể giữ mọi revision mãi.

Có:

```text
ActiveRevision
PinnedRevision
CacheRevision
DeadRevision
```

Khi revision không còn referenced:

```text
reclaim
```

nhưng immutable semantic objects được intern có thể được giữ trong global cache nếu hữu ích.

---

# 47. Compiler cache

Cache key phải chứa đủ:

```text
SourceFingerprint
SemanticCompilerVersion
Target
Features
ComptimeInputs
Dependencies
Profile
```

Không:

```text
hash(source)
```

đơn giản như vậy.

---

# 48. Cache safety

Cache hit không có nghĩa:

> “tin object cũ”.

Phải verify:

```text
CacheFingerprint == CurrentFingerprint
```

Nếu mismatch:

```text
recompute
```

Không heuristic.

---

# 49. Compiler API boundary

Các module không được truy cập database nội bộ tùy tiện.

Ví dụ:

```text
TypeChecker
```

được phép:

```text
db.type_of(...)
db.resolve(...)
db.trait_solve(...)
```

nhưng không:

```text
db.codegen_internal_mutable_state
```

Đây là cách giữ architecture sạch khi team nhiều AI agent cùng phát triển.

---

# 50. Public compiler interfaces

Các interface quan trọng:

```text
SourceProvider
PackageResolver
SyntaxProvider
NameResolver
TypeProvider
TraitSolver
HirProvider
MirProvider
Verifier
Interpreter
Optimizer
AbiLowerer
CodeGenerator
ObjectWriter
Linker
DiagnosticProvider
```

Mỗi interface có contract.

---

# 51. Không để trait/interface trở thành abstraction runtime

Đây là compiler architecture, không phải runtime architecture.

Ví dụ:

```text
TypeProvider
```

có thể là trait/interface trong implementation language.

Nhưng nó không tạo:

```text
Axiom runtime object
```

hoặc runtime overhead.

---

# 52. Query invalidation

Ví dụ:

```text
foo signature unchanged
foo body changed
```

thì:

```text
type_of(foo)
```

có thể vẫn valid.

Nhưng:

```text
mir(foo)
opt(foo)
codegen(foo)
```

invalidate.

Nếu:

```text
foo return type changed
```

thì caller dependencies cũng invalidate.

---

# 53. API cho AI agent

Compiler nên expose:

```text
ax inspect symbol
ax query type
ax query ownership
ax query effects
ax query trait
ax query cfg
ax explain move
ax explain capability
ax explain optimization
ax explain allocation
ax context
```

Output machine-readable:

```text
JSON / structured protocol
```

Không parse human error text.

---

# 54. AI agent không được sửa semantic database

AI có quyền:

```text
query
inspect
explain
propose patch
```

nhưng không:

```text
inject VerifiedMIR
mark ownership verified
assert trait proven
disable capability checker
```

AI sửa source:

```text
Source
 ↓
normal compiler pipeline
```

---

# 55. Compiler invariant quan trọng nhất của 220

> **Không một compiler subsystem nào được tạo ra “semantic fact” bằng cách tự ý bypass CompilerDB + Semantic Kernel.**

Ví dụ optimizer muốn biết:

```text
A và B có disjoint không?
```

phải query:

```text
alias_info(A, B)
```

không tự suy luận lại một phiên bản khác.

---

# 56. Data ownership giữa compiler phases

Nguyên tắc:

```text
SourceDB
    owns source

SyntaxDB
    owns syntax tree

DeclarationDB
    owns declarations

TypeDB
    owns canonical types

HIRDB
    owns HIR

MIRDB
    owns MIR

VerificationDB
    owns proof/facts

OptDB
    owns optimization facts

CodegenDB
    owns target artifacts
```

Không copy toàn bộ graph giữa phases.

Dùng IDs.

---

# 57. Compiler memory flow

Ví dụ function:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

sẽ đi:

```text
SourceFileId
   ↓
SyntaxNodeId
   ↓
DeclarationId
   ↓
FunctionId
   ↓
TypeId(i32)
   ↓
ExprId
   ↓
HIR
   ↓
MirFunction
   ↓
VerifiedMir
   ↓
OptFunction
   ↓
AbiFunction
   ↓
LirFunction
   ↓
MachineFunction
   ↓
ObjectSymbol
```

Không có phase nào cần copy toàn bộ source tree.

---

# 58. Compiler implementation language

Bootstrap implementation có thể dùng:

```text
Rust/C++/...
```

nhưng data model phải **mô phỏng semantics của Axiom**, không phụ thuộc semantics của implementation language.

Ví dụ không được vì Rust có borrow checker mà giả định:

```text
Axiom = Rust-like
```

hoặc vì C++ có pointer:

```text
Axiom place = C++ pointer
```

Compiler implementation chỉ là phương tiện.

---

# 59. Test API

Mỗi subsystem phải có test helpers.

Ví dụ:

```text
parse_ok(source)
parse_error(source)

type_ok(source)
type_error(source)

mir_of(source)
verify_ok(source)
verify_error(source)

interpret(source)
compile_native(source)
```

Test semantic nên viết từ source-level, không chỉ test internal object.

---

# 60. Internal invariant tests

Ngoài source tests:

```text
test_type_interning()
test_place_projection()
test_cfg_validity()
test_ownership_join()
test_region_relation()
test_trait_cache()
test_layout_determinism()
test_query_invalidation()
```

để bắt compiler bug sớm.

---

# 61. Fuzz boundary

Các boundary cần fuzz:

```text
lexer
parser
resolver
type checker
trait solver
HIR lowering
MIR lowering
ownership verifier
capability verifier
comptime
optimizer
object writer
linker
```

Đặc biệt:

> **Mọi fuzz-generated valid MIR phải không làm verifier crash.**

Invalid MIR có thể bị reject, nhưng không được gây memory corruption/crash bất kiểm soát.

---

# 62. Compiler crash model

Phân biệt:

```text
UserError
InternalInvariantViolation
CompilerBug
```

Ví dụ:

```text
type mismatch
```

→ UserError.

Nhưng:

```text
VerifiedMIR contains impossible ownership state
```

→ CompilerBug/ICE.

Không được biến compiler bug thành diagnostic giả cho user.

---

# 63. Performance requirements

Compiler phải tối ưu không chỉ executable mà chính compiler.

Mục tiêu:

```text
Parsing: linear-ish
Name resolution: near-linear
Type interning: amortized O(1)
Common queries: memoized
Trait solving: bounded/memoized
MIR construction: linear in HIR
CFG analyses: O(V+E) cho analysis phù hợp
```

Không hy sinh correctness để đạt complexity.

---

# 64. Axiom compiler architecture sau 220

```text
                    ┌───────────────┐
                    │   SourceDB    │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │  SyntaxDB     │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │ DeclarationDB │
                    └───────┬───────┘
                            │
             ┌──────────────▼──────────────┐
             │          CompilerDB         │
             │                             │
             │ TypeDB       TraitDB        │
             │ GenericDB    ConstDB        │
             │ HIRDB        MIRDB          │
             │ VerifyDB     LayoutDB       │
             │ AbiDB        OptDB          │
             │ CodegenDB    DiagnosticDB   │
             └──────────────┬──────────────┘
                            │
                       Query Graph
                            │
             ┌──────────────▼──────────────┐
             │      Semantic Kernel        │
             └──────────────┬──────────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        Interpreter     Verifier       Optimizer
                                            │
                                            ▼
                                          ABI
                                            │
                                            ▼
                                          LIR
                                            │
                                            ▼
                                       Backend
                                            │
                                      ┌─────┴─────┐
                                      ▼           ▼
                                   Object      Linker
```

---

# 65. Invariants của BOOTSTRAP-220

Khóa:

```text
ACDB-20
CompilerDB is the authoritative semantic query database.

ACDB-21
Semantic entities have stable typed IDs.

ACDB-22
Stale IDs are detectable and cannot silently resolve to unrelated entities.

ACDB-23
Canonical semantic types are interned.

ACDB-24
Semantic objects are immutable after publication within a revision.

ACDB-25
Compiler queries are deterministic unless explicitly effectful.

ACDB-26
Compiler phases communicate primarily through typed IDs and query results.

ACDB-27
No backend may directly reinterpret frontend syntax as semantic truth.

ACDB-28
Incremental invalidation follows recorded query dependencies.

ACDB-29
Semantic, ABI, codegen and build fingerprints are distinct.

ACDB-30
Compiler parallelism must not change semantic results.

ACDB-31
Source-to-machine provenance remains queryable.

ACDB-32
Diagnostics contain structured semantic identity, not only text.

ACDB-33
AI tooling may inspect and propose changes but cannot manufacture verified semantic facts.

ACDB-34
Persistent compiler caches require explicit version/fingerprint validation.

ACDB-35
Internal compiler crashes caused by impossible semantic states are compiler defects, not user errors.

ACDB-36
Compiler implementation data structures must not redefine Axiom language semantics.
```

---

# 66. Điểm rất quan trọng: Axiom đã đủ để bắt đầu code compiler

Sau 220, chúng ta đã khóa được ba tầng:

```text
                  LANGUAGE
                     │
                     ▼
             Semantic Kernel
                     │
                     ▼
               CompilerDB
                     │
                     ▼
             Compiler Pipeline
```

Nghĩa là từ đây **không còn cần tiếp tục thiết kế các abstraction cơ bản của compiler một cách vô hạn**.

Chúng ta có thể chuyển sang một phase mới:

> **đóng gói toàn bộ specification thành implementation contract.**

---

# BOOTSTRAP-221 — AXIOM COMPILER IMPLEMENTATION SPECIFICATION

Đây là task tiếp theo.

Nó sẽ tạo ra một specification cực kỳ thực dụng, ở mức agent có thể mở repository trống và bắt đầu implement:

```text
compiler/
├── core/
├── source/
├── syntax/
├── parser/
├── resolve/
├── types/
├── traits/
├── hir/
├── mir/
├── verify/
├── comptime/
├── interpreter/
├── opt/
├── abi/
├── lir/
├── backend/
├── object/
├── linker/
└── driver/
```

với **API, struct, enum, function, dependency, invariant, test và thứ tự implement cụ thể cho từng module**.

Đặc biệt 221 sẽ trả lời câu hỏi:

> **“Nếu ngày mai Antigravity được yêu cầu bắt đầu viết Axiom compiler, chính xác nó phải tạo file nào trước, class/struct/enum nào, API nào, test nào, và khi nào được phép chuyển sang module kế tiếp?”**

Sau 221, kiến trúc sẽ đủ gần với **một implementation blueprint hoàn chỉnh** để chuyển trực tiếp sang Genesis/Harness cho AI agent.