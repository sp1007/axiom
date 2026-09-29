Tiếp tục.

# BOOTSTRAP-054 — Axiom Compiler Semantic Core Data Model

Mục tiêu của 054 là biến kiến trúc compiler ở 053 thành **một data model có thể code được**.

Nguyên tắc:

> **Mọi semantic entity phải có identity ổn định; mọi phase dùng chung semantic database; IR chỉ chứa các ID/handle cần thiết thay vì sao chép type/declaration graph.**

Điều này đặc biệt quan trọng với Axiom vì compiler cần phục vụ đồng thời:
- compilation
- incremental build
- IDE
- debugger
- AI semantic tooling
- optimization explanation

---

# 1. Semantic Database

Compiler lấy một database trung tâm:

```text
CompilerDB
├── SourceDB
├── PackageDB
├── ModuleDB
├── DeclarationDB
├── TypeDB
├── TraitDB
├── ConstDB
├── GenericDB
├── HIRDB
├── MIRDB
├── LayoutDB
├── AbiDB
├── CodegenDB
├── DiagnosticDB
└── SourceMapDB
```

Không nên để mỗi compiler pass tự sở hữu một bản sao của toàn bộ semantic information.

---

# 2. ID system

Các object semantic không dùng pointer C++/Rust-style làm identity public nội bộ.

Dùng ID:

```text
PackageId
ModuleId
DeclarationId
TypeId
TraitId
FunctionId
FieldId
VariantId
GenericParamId
GenericInstanceId
LocalId
BasicBlockId
InstructionId
CapabilityId
RegionId
SuspensionPointId
SourceFileId
SourceSpanId
```

Có thể triển khai ban đầu bằng integer handle:

```text
u32 / u64
```

---

# 3. Vì sao không dùng raw pointer làm identity?

Nếu compiler dùng:

```text
*Node
```

làm identity thì:

- arena relocation khó
- incremental cache khó
- serialization khó
- parallel compiler khó
- AI semantic query khó
- debug provenance khó

ID tách:

```text
identity
```

khỏi:

```text
physical memory address
```

đúng với philosophy của Axiom.

---

# 4. Generational IDs

Đối với database có mutation/reuse, có thể dùng:

```text
Id {
    index
    generation
}
```

Ví dụ:

```text
TypeId {
    index: 42
    generation: 7
}
```

Tránh stale handle.

Đặc biệt hữu ích cho IDE/incremental compiler.

---

# 5. SourceDB

```text
SourceFile {
    id: SourceFileId
    path
    package
    content
    content_hash
}
```

Source span:

```text
SourceSpan {
    file: SourceFileId
    start: u32
    end: u32
}
```

Không lưu string source lặp lại trong mọi node.

---

# 6. PackageDB

```text
Package {
    id: PackageId
    name
    version
    source_identity
    dependencies
}
```

Package identity:

```text
PackageId
```

không đơn giản là package name.

---

# 7. ModuleDB

```text
Module {
    id: ModuleId
    package: PackageId
    parent: Option<ModuleId>
    name
    declarations
    imports
    visibility
}
```

Filesystem path chỉ là metadata/mapping.

---

# 8. DeclarationDB

Mọi declaration:

```text
Declaration {
    id: DeclarationId
    module: ModuleId
    name
    kind
    visibility
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
...
```

---

# 9. FunctionDB

```text
Function {
    declaration: DeclarationId
    parameters
    return_type: TypeId
    generics
    body
    attributes
    abi
}
```

Không cần tách method thành một loại semantic entity khác.

Method vẫn là function + receiver metadata.

---

# 10. Receiver

```text
Receiver {
    mode: ReceiverMode
    type: TypeId
}
```

`ReceiverMode`:

```text
Owning
View
MutView
```

Ví dụ:

```axiom
fn length(self: view<Vec<T>>) -> usize
```

về semantic vẫn là function.

---

# 11. StructDB

```text
StructDef {
    declaration: DeclarationId
    fields: [FieldId]
    generic_params
    repr_contract
}
```

Field:

```text
Field {
    id: FieldId
    parent: DeclarationId
    name
    type: TypeId
    visibility
}
```

---

# 12. EnumDB

```text
EnumDef {
    declaration: DeclarationId
    variants: [VariantId]
}
```

Variant:

```text
Variant {
    id: VariantId
    parent: DeclarationId
    name
    fields
    discriminant
}
```

Discriminant physical representation có thể chưa được quyết định tại semantic type stage.

---

# 13. TraitDB

```text
TraitDef {
    id: TraitId
    declaration: DeclarationId
    generic_params
    supertraits
    associated_types
    associated_consts
    associated_functions
}
```

Không có:

```text
parent_class
vtable
object_header
```

trong trait definition.

---

# 14. Trait implementation

```text
TraitImpl {
    trait: TraitId
    for_type: TypeId
    functions
    associated_types
    associated_consts
    source
}
```

Trait solver dùng entity này.

---

# 15. TypeDB

Đây là một trong những database quan trọng nhất.

```text
Type {
    kind
}
```

Kind:

```text
Primitive
Struct
Enum
Tuple
Array
Function
Closure
View
MutView
RawPointer
DynTrait
GenericParam
TypeAlias
Never
Unit
...
```

---

# 16. Type interning

Hai lần xuất hiện:

```text
Vec<i32>
```

phải có thể map về cùng:

```text
TypeId
```

trong cùng semantic universe.

Ví dụ:

```text
TypeId(100)
```

được intern.

Điều này giúp:

- equality nhanh
- cache
- trait solving
- generic substitution
- memory tiết kiệm.

---

# 17. Type identity

Nominal types:

```text
User
OtherPackage::User
```

khác nhau dù field giống hệt.

Structural types:

```text
(i32, f64)
```

có identity dựa trên cấu trúc.

---

# 18. Primitive type

```text
PrimitiveType {
    Bool
    I8
    I16
    I32
    I64
    U8
    U16
    U32
    U64
    Isize
    Usize
    F32
    F64
    Unit
    Never
}
```

---

# 19. Generic parameter type

```text
GenericParamType {
    id: GenericParamId
}
```

Ví dụ:

```axiom
fn identity<T>(x: T) -> T
```

`T` không phải runtime object.

---

# 20. Generic instance

```text
GenericInstance {
    declaration: DeclarationId
    substitutions: [TypeId | ConstValue]
}
```

Ví dụ:

```text
identity<i32>
```

→ `GenericInstanceId`.

---

# 21. Substitution

Compiler phải có một subsystem:

```text
Substitution
```

Ví dụ:

```text
T → i32
U → f64
```

Apply:

```text
Vec<T>
```

→

```text
Vec<i32>
```

Không mutate generic definition.

---

# 22. Type equality

Có ít nhất:

```text
SemanticEqual
RepresentationEqual
AbiCompatible
```

Đây là ba câu hỏi khác nhau.

Ví dụ hai types có thể:

```text
semantic distinct
```

nhưng:

```text
@repr(transparent)
```

lại có ABI representation tương đương.

---

# 23. Type properties

Compiler cần cache:

```text
TypeProperties {
    copy
    drop
    send
    share
    sized
    ffi_safe
    gpu_legal
}
```

Nhưng đây là **derived facts**, không phải fields programmer có thể tùy ý set.

---

# 24. Không nên lưu `is_copy = true` như sự thật bất biến

Vì generic:

```text
T
```

chưa biết.

Phải có:

```text
PropertyQuery(TypeId, Property)
```

và trait solver/semantic engine tính kết quả.

Sau đó cache.

---

# 25. Place

MIR `Place`:

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
Temporary(TemporaryId)
Argument(LocalId)
```

---

# 26. Projection

```text
Projection {
    Field(FieldId)
    Index(ValueId)
    Deref
    SliceRange(start, end)
}
```

Có thể mở rộng:

```text
Downcast(VariantId)
```

cho enum pattern lowering.

---

# 27. Value

MIR Value là SSA-like temporary/value reference:

```text
ValueId
```

nhưng semantic MIR không bắt buộc SSA.

Value có thể trỏ tới:

```text
Constant
Local
InstructionResult
Argument
```

---

# 28. Operand

```text
Operand =
    Copy(Place)
  | Move(Place)
  | Constant(ConstValue)
```

Đây là nơi ownership semantics xuất hiện trực tiếp.

---

# 29. RValue

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
    ...
```

---

# 30. Statement

```text
Statement =
    Assign(Place, RValue)
    StorageLive(LocalId)
    StorageDead(LocalId)
    Drop(Place)
    SetCapability(...)
    ...
```

Một số semantic operations có thể chỉ tồn tại trong Verified MIR hoặc verifier IR rồi bị erase.

---

# 31. Terminator

```text
Terminator =
    Goto(BasicBlockId)
    Branch(ValueId, ...)
    Switch(...)
    Call(...)
    Return(...)
    Panic(...)
    Suspend(...)
    Unreachable
```

---

# 32. MIR Function

```text
MirFunction {
    function: FunctionId
    locals
    blocks
    arguments
    return_type
    capabilities
    source_map
}
```

---

# 33. Local

```text
Local {
    id: LocalId
    type: TypeId
    mutability
    source_span
    storage_class
}
```

`storage_class` ở semantic MIR không nên trực tiếp nói:

```text
stack
heap
register
```

mà chỉ biểu diễn semantic requirement nếu có:

```text
Normal
StableAddress
Static
TLS
External
Device
...
```

---

# 34. OwnershipState

```text
OwnershipState =
    Uninit
    Init
    Moved
    PartiallyMoved
    Dropped
```

Verifier có thể giữ state riêng thay vì nhúng mutable state vào `Local`.

---

# 35. Ownership state theo Place

Đây là điểm quan trọng.

Không chỉ:

```text
Local x = Moved
```

mà:

```text
x.a = Moved
x.b = Init
```

Vì vậy ownership state phải hỗ trợ **place tree**.

---

# 36. Place tree

Ví dụ:

```text
x
├── a → MOVED
├── b → INIT
└── c
    ├── d → INIT
    └── e → MOVED
```

Đây là nền tảng partial move.

---

# 37. Capability

```text
Capability {
    id
    owner
    region
    access
    lifetime
    storage_domain
    execution_domain
}
```

Access:

```text
Read
Write
```

Có thể thêm:

```text
Move
```

ở compiler-internal level nếu cần, nhưng không phải user-facing capability.

---

# 38. Region

```text
Region =
    Whole(Place)
    Field(Place, FieldId)
    Index(Place, ValueId)
    Range(...)
    Subregion(...)
```

Region relation:

```text
Disjoint
Same
Contains
ContainedBy
Overlaps
Unknown
```

---

# 39. CapabilitySet

Verifier duy trì:

```text
CapabilitySet {
    active: Map<CapabilityId, Capability>
}
```

Tại mỗi CFG point có semantic state.

---

# 40. Capability lifetime

Không nhất thiết là timestamp.

Mô hình tốt hơn:

```text
CapabilityLiveRange {
    start_point
    end_points
}
```

được compiler tính từ dataflow.

---

# 41. CFG state

Tại mỗi BasicBlock:

```text
SemanticState {
    ownership
    capabilities
    initialized
    drops
}
```

Merge phải có luật deterministic.

---

# 42. Ownership merge

Ví dụ:

```text
branch A → INIT
branch B → MOVED
```

merge không thể tùy tiện chọn INIT.

Kết quả:

```text
invalid state for later use
```

hoặc trạng thái conservative tương ứng.

---

# 43. DropTree

```text
DropTree {
    scopes
    local drop obligations
    field drop obligations
}
```

Compiler xây tree từ lexical scopes + control-flow exits.

---

# 44. ConstValue

```text
ConstValue =
    Bool
    Integer
    Float
    Char
    String
    Tuple
    Struct
    Enum
    Array
    ...
```

ConstValue không phải runtime allocation.

---

# 45. ComptimeValue

Không nên tạo một type system riêng.

```text
ComptimeValue {
    semantic_type: TypeId
    value
    capabilities
}
```

Nó sử dụng cùng TypeDB.

---

# 46. Comptime capability

Compiler tracks:

```text
ReadSource
ReadMetadata
ReadFilesystem
WriteGenerated
ExecuteTool
Environment
Network
Time
Random
```

theo profile.

---

# 47. Generic constraints

```text
TraitRef {
    trait
    self_type
    args
}
```

Ví dụ:

```text
T: Add<U>
```

→

```text
TraitRef {
    trait: Add
    self_type: T
    args: [U]
}
```

---

# 48. Trait solver result

```text
TraitResult =
    Proven
    NotProven
    Ambiguous
    Error
```

Không nên chỉ dùng bool.

`Ambiguous` cực kỳ quan trọng cho deterministic diagnostics.

---

# 49. Trait candidate

Solver internal:

```text
Candidate {
    impl_id
    substitutions
    obligations
}
```

Solver chọn candidate duy nhất.

Nếu nhiều candidate hợp lệ:

```text
Ambiguous
```

---

# 50. Trait solver cache

Key:

```text
TraitQueryKey {
    trait_ref
    environment
}
```

Value:

```text
TraitResult
```

Memoization cần thiết vì generic code có thể tạo số lượng query rất lớn.

---

# 51. Const generic

V1:

```text
const N: usize
```

chỉ cho scalar constants được hỗ trợ.

Không mở rộng thành dependent type system.

---

# 52. LayoutDB

Layout được tính sau semantic verification.

```text
Layout {
    size
    align
    fields
    enum_layout
    niches
}
```

Nhưng default layout không trở thành source-level contract.

---

# 53. RepresentationContract

```text
RepresentationContract =
    Default
    C
    Transparent
    Packed
    Align(N)
```

Có thể kết hợp contract hợp lệ theo rules.

---

# 54. ABI DB

```text
AbiSignature {
    calling_convention
    parameters
    return
    aggregate_rules
    unwind_policy
}
```

ABI khác representation.

---

# 55. ExecutionDomain

```text
ExecutionDomain =
    HostCPU
    Thread
    Task
    Fiber
    GPU
    Interrupt
    Device
```

Không phải tất cả đều là runtime types.

---

# 56. StorageDomain

```text
StorageDomain =
    Local
    Static
    TLS
    Dynamic
    Arena
    Pool
    Device
    SharedDevice
    External
```

Đây là semantic categories.

---

# 57. Async state

```text
AsyncInfo {
    future_type
    suspension_points
    state_fields
}
```

Suspension:

```text
SuspensionPoint {
    id
    source_span
    live_locals
    live_capabilities
}
```

---

# 58. GPU information

```text
GpuInfo {
    kernel
    storage_domains
    execution_scope
    synchronization_requirements
    target
}
```

Không tạo GPU AST riêng.

---

# 59. FFI contract

```text
FfiContract {
    abi
    ownership
    representation
    calling_convention
    unwind
    synchronization
}
```

Ví dụ ownership:

```text
Borrowed
OwnedByAxiom
OwnedByForeign
Shared
HandleOnly
```

---

# 60. Diagnostic

Diagnostic nên là structured object:

```text
Diagnostic {
    code
    severity
    primary_span
    secondary_spans
    message
    notes
    machine_data
}
```

Ví dụ machine data:

```text
moved_from
move_site
use_site
type
capability
region
```

---

# 61. Diagnostic code

Ví dụ:

```text
AOWN-42
ACAP-17
ATRAIT-31
AFFI-08
AASYNC-22
```

Code là stable semantic identifier.

Message có thể thay đổi.

---

# 62. SourceMap

Mỗi MIR instruction có thể map:

```text
InstructionId
→ SourceSpan
```

và ngược lại:

```text
SourceSpan
→ [InstructionId]
```

Cho debug + AI tooling.

---

# 63. SemanticFingerprint

Đây là thành phần cực kỳ quan trọng cho incremental compilation.

```text
SemanticFingerprint {
    public_api
    types
    traits
    repr
    ABI
    comptime_dependencies
    relevant compiler semantics
}
```

---

# 64. Fingerprint không phải source hash

Hai source:

```text
implementation A
implementation B
```

có thể khác source hash nhưng cùng public semantic interface.

Downstream không nhất thiết phải rebuild toàn bộ.

---

# 65. Query architecture

Compiler database nên hỗ trợ:

```text
query type_of(expr)
query resolve(name)
query trait_impls(type)
query callers(function)
query callees(function)
query ownership_at(span)
query capability_at(span)
query allocation_reason(span)
query optimization_reason(span)
query abi_of(function)
```

---

# 66. Đây là điểm rất phù hợp với AI

AI agent không cần:

```text
grep toàn repository
```

để hỏi:

> Tại sao dòng này không compile?

Nó query semantic DB:

```text
explain_diagnostic(AOWN-42)
```

và nhận structured result.

---

# 67. Không cho AI sửa semantic DB trực tiếp

AI có thể:

```text
read/query
```

và đề xuất source changes.

Không:

```text
AI → mutate MIR → compiler accepts
```

Semantic compiler vẫn là authority.

---

# 68. Data model phải serialization-friendly

Các entity:

```text
Type
Trait
HIR
MIR
Diagnostic
Fingerprint
```

nên serialize được cho:

- incremental compilation
- compiler cache
- IDE
- AI tooling
- build daemon

---

# 69. Nhưng không freeze binary format

Internal serialization:

```text
versioned
compiler-owned
```

Không phải public ABI.

---

# 70. Memory ownership của chính compiler

Đây là một vấn đề implementation thực tế.

Compiler nên dùng:

```text
Arena / intern pool / immutable semantic objects
```

nhiều hơn raw heap allocation tùy tiện.

Vì compiler có rất nhiều object sống lâu.

---

# 71. Semantic objects nên immutable

Ví dụ:

```text
Type
TraitDef
Declaration
```

sau khi intern nên gần như immutable.

Thay đổi tạo revision/new query result thay vì mutate tùy tiện.

Điều này giúp:

- parallelism
- caching
- deterministic behavior
- thread safety.

---

# 72. Mutable state chỉ ở compiler transaction

Ví dụ parser đang xây AST có thể mutable.

Nhưng sau semantic insertion:

```text
AST
 ↓
intern
 ↓
immutable semantic DB
```

là mô hình tốt hơn.

---

# 73. Revision model

Compiler database có:

```text
RevisionId
```

Mỗi source change tạo revision mới.

Query có thể cache theo:

```text
Revision + QueryKey
```

---

# 74. Đây cũng giải quyết IDE

Khi user sửa một dòng:

```text
foo.ax line 42
```

compiler không cần rebuild toàn bộ semantic graph.

Chỉ invalidate các queries phụ thuộc.

---

# 75. Dependency graph

Mỗi query có dependency:

```text
TypeOf(expr)
    depends on
        ResolvedName
        GenericSubstitution
        TraitResolution
        ...
```

Nếu một dependency không đổi semantic:

```text
cache remains valid
```

---

# 76. Compiler database architecture

Có thể hình dung:

```text
                    CompilerDB
                        │
       ┌────────────────┼────────────────┐
       │                │                │
    SourceDB        SemanticDB        CacheDB
       │                │                │
       │       ┌────────┼────────┐       │
       │       │        │        │       │
       │     Type     Trait     MIR    Fingerprint
       │       │        │        │       │
       └───────┴────────┴────────┴───────┘
                        │
                        ▼
                     Queries
                        │
              ┌─────────┼─────────┐
              ▼         ▼         ▼
             IDE       AI      Compiler
```

---

# 77. 054 — điều đặc biệt quan trọng

Chúng ta **không nên bắt đầu code compiler bằng parser**.

Đó là cách dễ khiến project trở thành:

```text
parser đẹp
+
AST đẹp
+
không có semantic architecture
```

Thay vào đó nên implementation theo dependency:

```text
1. IDs / Arena / Interning
2. SourceDB
3. TypeDB
4. DeclarationDB
5. TraitDB
6. HIR
7. MIR
8. Verifiers
9. Comptime
10. Optimizer
11. LIR
12. Backend
```

---

# 78. Compiler implementation layers

Tôi đề xuất repository cuối cùng có cấu trúc logic:

```text
compiler/
├── base/
│   ├── ids
│   ├── arena
│   ├── interner
│   ├── hash
│   └── diagnostics
│
├── source/
│   ├── source_db
│   └── source_map
│
├── syntax/
│   ├── lexer
│   ├── parser
│   └── ast
│
├── semantic/
│   ├── package
│   ├── module
│   ├── declaration
│   ├── type
│   ├── trait
│   ├── generic
│   └── comptime
│
├── hir/
│
├── mir/
│
├── verify/
│   ├── ownership
│   ├── capability
│   ├── drop
│   ├── concurrency
│   ├── async
│   ├── gpu
│   └── ffi
│
├── optimize/
│
├── layout/
├── abi/
├── lir/
├── backend/
├── object/
├── linker/
└── driver/
```

Đây là architecture rất phù hợp với mục tiêu self-hosting sau này.

---

# 79. Frozen invariants — BOOTSTRAP-054

```text
ACOMP-81   Compiler semantic entities use explicit stable identities.
ACOMP-82   Source spelling is not semantic identity.
ACOMP-83   Package, module, declaration, type, trait and function identities are distinct.
ACOMP-84   Semantic identities are independent of physical memory addresses.
ACOMP-85   Compiler IR may reference semantic entities through IDs.
ACOMP-86   Semantic types are internable.
ACOMP-87   Equivalent interned type structures share TypeId within a semantic universe.
ACOMP-88   Nominal type identity remains distinct from structural representation.
ACOMP-89   Type aliases do not create new nominal type identity.
ACOMP-90   Newtypes create distinct nominal type identity.
ACOMP-91   Generic parameters are compile-time semantic entities.
ACOMP-92   Generic instances are identified independently from generic declarations.
ACOMP-93   Generic substitution does not mutate generic definitions.
ACOMP-94   Type properties such as Copy, Drop, Send and Share are compiler-derived.
ACOMP-95   Derived semantic properties cannot be silently asserted by programmer metadata.
ACOMP-96   MIR Place identity is distinct from MIR Value identity.
ACOMP-97   MIR projections represent field/index/deref/subregion access.
ACOMP-98   Ownership state may be tracked at Place granularity.
ACOMP-99   Partial move requires place-sensitive ownership state.
ACOMP-100  Ownership state is compiler semantic state, not ordinary runtime data.
ACOMP-101  Capability identity is distinct from ownership identity.
ACOMP-102  Capability provenance includes owner and region information.
ACOMP-103  Region relations are explicit compiler facts.
ACOMP-104  Capability state is tracked across control-flow paths.
ACOMP-105  Capability merge is conservative and deterministic.
ACOMP-106  Drop obligations are represented independently from physical allocation.
ACOMP-107  Trait references are explicit semantic query objects.
ACOMP-108  Trait solving can produce Proven, NotProven, Ambiguous or Error.
ACOMP-109  Trait resolution is memoizable.
ACOMP-110  Layout is computed separately from semantic type identity.
ACOMP-111  Representation contracts are explicit semantic metadata.
ACOMP-112  ABI information is distinct from source-level type semantics.
ACOMP-113  Execution domain is distinct from storage domain.
ACOMP-114  Async suspension points have stable compiler identities within compilation.
ACOMP-115  GPU semantics reuse common type and capability identity.
ACOMP-116  FFI contracts explicitly record ABI and ownership boundaries.
ACOMP-117  Comptime values use the ordinary Axiom type system.
ACOMP-118  Comptime does not introduce a second semantic type system.
ACOMP-119  Structured diagnostics contain stable machine-readable identifiers.
ACOMP-120  Diagnostics may expose machine-readable semantic evidence.
ACOMP-121  Source-to-MIR mappings are retained for debugging and tooling.
ACOMP-122  Semantic fingerprints represent relevant public semantics.
ACOMP-123  Semantic fingerprints are distinct from raw source hashes.
ACOMP-124  Incremental invalidation follows semantic dependencies.
ACOMP-125  Internal semantic objects should be serialization-friendly.
ACOMP-126  Internal serialization is versioned independently from public ABI.
ACOMP-127  Compiler semantic objects should be immutable after interning where practical.
ACOMP-128  Mutable compiler construction state is isolated from immutable semantic state.
ACOMP-129  Compiler queries are the primary access mechanism for shared semantic information.
ACOMP-130  IDE and AI tooling may consume compiler semantic queries.
ACOMP-131  AI tooling cannot directly mutate verified semantic state.
ACOMP-132  Semantic database queries are deterministic.
ACOMP-133  Compiler database revisions participate in incremental caching.
ACOMP-134  Physical compiler memory addresses are never semantic identity.
ACOMP-135  Compiler-owned arenas and intern pools may be used as implementation strategies.
ACOMP-136  Semantic database architecture must support parallel queries.
ACOMP-137  Semantic cache entries include relevant dependency fingerprints.
ACOMP-138  MIR data structures remain independent of target machine registers.
ACOMP-139  Layout and ABI data are unavailable to earlier semantic phases unless explicitly required.
ACOMP-140  Backend data structures cannot redefine semantic database facts.
```

---

# Một kết luận quan trọng sau 054

Đến đây, Axiom đã có một điểm khác biệt rất rõ so với nhiều dự án language mới:

**chúng ta đang thiết kế compiler như một semantic database + query engine**, thay vì chỉ là:

```text
lexer → parser → AST → codegen
```

Điều này đặc biệt phù hợp với mục tiêu của bạn về **AI-friendly language**.

AI có thể hỏi compiler:

```text
"Type của x là gì?"
"Vì sao x bị move?"
"Capability nào đang giữ vùng này?"
"Vì sao Vec không được realloc?"
"Vì sao Future này không Send?"
"Allocation này có thể eliminate không?"
"ABI của function này là gì?"
"Instruction nào tạo ra allocation?"
```

và compiler trả lời bằng **semantic facts**, thay vì bắt AI đọc hàng nghìn dòng source.

---

# BOOTSTRAP-055 — Verification Algorithms & Dataflow Engine

Bước tiếp theo nên đi thẳng vào phần khó nhất của Axiom:

> **Làm thế nào compiler thực sự chứng minh Ownership + Capability + Drop + Send/Share trên CFG?**

055 sẽ đặc tả:

```text
CFG dataflow
Ownership lattice
Place-tree state
Move analysis
Partial move
Drop analysis
Capability region analysis
Alias/conflict detection
Lifetime inference
Escape analysis
Send/Share derivation
Await boundary checking
Thread boundary checking
GPU boundary checking
FFI boundary checking
```

Đây chính là phần quyết định Axiom có thực sự đạt được mục tiêu:

> **“lập trình viên không phải viết borrow/lifetime, nhưng compiler vẫn đảm bảo memory safety và concurrency safety”**

hay không.