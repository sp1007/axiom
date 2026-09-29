# BOOTSTRAP-270 — AXIOM COMPILER DATA MODEL & CORE IR TYPES

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của task này là khóa **data model thực tế của compiler**. Sau task này, agent có thể bắt đầu định nghĩa các struct/enum/ID và database thật, thay vì chỉ có kiến trúc module.

Nguyên tắc trung tâm:

> **Compiler IR phải biểu diễn semantic facts bằng dữ liệu có cấu trúc, không bằng convention ngầm hoặc pointer tùy ý.**

---

# 1. Compiler data model tổng thể

```text
Source
  │
  ▼
Syntax
  │
  ▼
Declaration Graph
  │
  ▼
Type Graph
  │
  ▼
HIR
  │
  ▼
MIR
  │
  ├── Ownership
  ├── Capability
  ├── Effects
  ├── Regions
  └── Control Flow
  │
  ▼
Verified MIR
  │
  ├── Alias
  ├── MemorySSA
  ├── Escape
  ├── Range
  └── Loop
  │
  ▼
OptIR
  │
  ▼
ABI MIR
  │
  ▼
LIR
  │
  ▼
Machine IR
```

---

# 2. Quy tắc ID-first

Các semantic object lớn **không tham chiếu nhau bằng raw pointer**.

Ví dụ:

```text
TypeId
FunctionId
LocalId
BasicBlockId
InstructionId
```

thay vì:

```text
Type*
Function*
Block*
```

Compiler implementation có thể dùng pointer nội bộ để tối ưu, nhưng semantic identity vẫn là ID.

---

# 3. ID model

Core compiler foundation:

```text
struct TypeId {
    index: u32
    generation: u32
}
```

Tương tự:

```text
FileId
ModuleId
DeclarationId
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
ClosureId
SuspensionPointId
```

Không nhất thiết mọi ID đều cần generation nếu database bất biến theo revision.

---

# 4. Stable ID và ephemeral ID

Phân biệt:

```text
StableSemanticId
```

và:

```text
LocalCompilerId
```

Stable ID phục vụ:

- IDE
- diagnostics
- `.axmeta`
- incremental compilation
- AI tooling

Local ID phục vụ:

- temporary IR
- optimization pass
- register allocation.

---

# 5. SourceSpan

```text
struct SourceSpan {
    file: SourceFileId
    start: u32
    end: u32
}
```

Offset là UTF-8 byte offset.

Không lưu line/column trực tiếp trong semantic node.

---

# 6. Span không phải semantic identity

Hai node có cùng span vẫn có thể có semantic identity khác nhau.

---

# 7. Type model

Đây là một trong những cấu trúc quan trọng nhất:

```text
enum TypeKind {
    Unit
    Never
    Bool

    Int { signed: bool, bits: u16 }
    Float { bits: u16 }

    Array { element: TypeId, length: ConstValueId }
    Tuple { elements: TypeListId }

    Struct(StructTypeId)
    Enum(EnumTypeId)

    Function(FunctionTypeId)
    Closure(ClosureTypeId)

    View { element: TypeId }
    MutView { element: TypeId }

    RawPointer {
        mutable: bool
        element: TypeId
    }

    GenericParam(GenericParamId)
    GenericInstance(GenericInstanceId)

    DynTrait(DynTraitTypeId)

    Alias(TypeId)

    Error
}
```

---

# 8. `TypeId` là canonical identity

Compiler không tạo nhiều `TypeId` cho cùng một canonical type.

Ví dụ:

```text
i32
```

phải được intern thành một type identity duy nhất trong một semantic universe.

---

# 9. Type interning

```text
TypeDB
 ├── canonicalization
 ├── interning
 ├── normalization
 └── queries
```

---

# 10. Alias và newtype

Cần phân biệt:

```text
type UserId = u64
```

với:

```text
struct UserId(u64)
```

Alias:

```text
TypeAlias → underlying TypeId
```

Newtype:

```text
StructTypeId
```

là nominal type khác.

---

# 11. Generic instance

Ví dụ:

```text
Vec<i32>
```

được biểu diễn:

```text
GenericInstance {
    definition: DeclarationId
    arguments: [TypeId]
}
```

---

# 12. Generic arguments

Không chỉ type:

```text
enum GenericArg {
    Type(TypeId)
    Const(ConstValueId)
}
```

v1 chỉ cần const parameter đơn giản như integer/bool.

---

# 13. Function type

```text
struct FunctionType {
    params: TypeListId
    return_type: TypeId
    effects: EffectSetId
    calling_convention: CallingConvention
}
```

---

# 14. Effect là một phần callable semantics

Không được để effect là comment hoặc metadata tùy ý.

Ví dụ:

```text
fn read() -> Result<Data, Error>
```

có effect profile khác:

```text
fn pure_math() -> i32
```

---

# 15. Struct type

```text
struct StructType {
    declaration: DeclarationId
    fields: FieldListId
    generic_args: GenericArgsId
}
```

Không lưu physical offset tại đây.

---

# 16. Enum type

```text
struct EnumType {
    declaration: DeclarationId
    variants: VariantListId
    generic_args: GenericArgsId
}
```

Physical discriminant/layout thuộc `LayoutDB`.

---

# 17. Trait

```text
struct TraitDef {
    id: TraitId
    declaration: DeclarationId
    parameters: GenericParamListId
    supertraits: TraitListId
    items: TraitItemListId
}
```

---

# 18. Impl

```text
struct ImplDef {
    id: ImplId
    trait_id: Option<TraitId>
    self_type: TypePattern
    generics: GenericParamListId
    where_clause: ConstraintSetId
    items: ImplItemListId
}
```

---

# 19. Place — semantic memory location

Đây là object cực kỳ quan trọng của MIR:

```text
struct Place {
    base: PlaceBase
    projections: ProjectionListId
}
```

---

# 20. PlaceBase

```text
enum PlaceBase {
    Local(LocalId)
    Static(StaticId)
    Temporary(TemporaryId)
    Argument(u16)
}
```

---

# 21. Projection

```text
enum Projection {
    Field(FieldId)
    Index(LocalId)
    ConstantIndex(u32)
    Deref
    Downcast(VariantId)
    SliceRange(...)
}
```

---

# 22. Place không phải pointer

Ví dụ:

```text
user.address.street
```

compiler có thể biểu diễn:

```text
Local(user)
 → Field(address)
 → Field(street)
```

trước khi quyết định địa chỉ vật lý.

---

# 23. Operand

```text
enum Operand {
    Copy(Place)
    Move(Place)
    Constant(ConstValueId)
}
```

Đây là nơi semantic Copy/Move được thể hiện rõ ràng.

---

# 24. `Copy` không có nghĩa `memcpy`

`Copy` nghĩa:

> sử dụng giá trị mà không tiêu thụ ownership.

Backend mới quyết định có load/copy vật lý hay không.

---

# 25. RValue

```text
enum RValue {
    Use(Operand)

    BinaryOp {
        op: BinaryOperator
        left: Operand
        right: Operand
    }

    UnaryOp {
        op: UnaryOperator
        operand: Operand
    }

    Aggregate(AggregateValue)

    MakeView {
        source: Place
        mutable: bool
    }

    Cast {
        operand: Operand
        target: TypeId
        kind: CastKind
    }

    Bitcast {
        operand: Operand
        target: TypeId
    }

    Load(Place)

    AtomicLoad {
        place: Place
        ordering: AtomicOrdering
    }

    Closure(ClosureId)

    FunctionRef(FunctionId)

    CallResult(CallId)
}
```

---

# 26. Statement

```text
enum Statement {
    Assign {
        destination: Place
        value: RValue
    }

    StorageLive(LocalId)

    StorageDead(LocalId)

    Drop(Place)

    Deinit(Place)

    SetCapability(CapabilityId)

    EndCapability(CapabilityId)

    MemoryBarrier(BarrierKind)

    Nop
}
```

---

# 27. Terminator

```text
enum Terminator {
    Goto(BasicBlockId)

    SwitchInt {
        value: Operand
        targets: SwitchTargets
    }

    SwitchEnum {
        value: Operand
        targets: EnumTargets
    }

    Return

    Unreachable

    Panic(PanicInfo)

    Call {
        function: Operand
        args: OperandListId
        destination: Place
        target: BasicBlockId
        unwind: Option<BasicBlockId>
    }

    Await {
        future: Operand
        destination: Place
        resume: BasicBlockId
        suspend: BasicBlockId
    }
}
```

---

# 28. MIR BasicBlock

```text
struct BasicBlock {
    statements: StatementListId
    terminator: Terminator
}
```

CFG được biểu diễn bằng `BasicBlockId`.

---

# 29. MIRFunction

```text
struct MirFunction {
    function: FunctionId
    locals: LocalListId
    blocks: BasicBlockListId
    return_type: TypeId
    effects: EffectSetId
    ownership_facts: OwnershipFactsId
    capability_facts: CapabilityFactsId
}
```

---

# 30. Local

```text
struct Local {
    id: LocalId
    type: TypeId
    kind: LocalKind
    source_span: Option<SourceSpan>
}
```

---

# 31. LocalKind

```text
enum LocalKind {
    Argument
    UserLocal
    Temporary
    ReturnPlace
    CompilerGenerated
}
```

---

# 32. Ownership state

```text
enum OwnershipState {
    Uninit
    Owned
    Moved
    PartiallyMoved
    Dropped
}
```

---

# 33. Ownership tree

Không chỉ theo Local.

Ví dụ:

```text
x
├── a
├── b
└── c
```

có thể:

```text
x.a → Moved
x.b → Owned
x.c → Owned
```

---

# 34. OwnershipFact

```text
struct OwnershipFact {
    place: Place
    state: OwnershipState
    point: ProgramPoint
}
```

---

# 35. Capability

```text
struct Capability {
    id: CapabilityId
    provenance: ProvenanceId
    region: RegionId
    access: AccessMode
    lifetime: LifetimeFact
    storage_domain: StorageDomain
    execution_domain: ExecutionDomain
}
```

---

# 36. AccessMode

```text
enum AccessMode {
    Read
    Write
    Move
    Drop
}
```

---

# 37. Provenance

```text
struct Provenance {
    owner: ProvenanceOwner
    root_region: RegionId
    storage: StorageDomain
}
```

---

# 38. ProvenanceOwner

```text
enum ProvenanceOwner {
    Local(LocalId)
    Static(StaticId)
    Allocation(AllocationId)
    Foreign(ForeignMemoryId)
    Device(DeviceMemoryId)
}
```

---

# 39. Region

```text
struct Region {
    id: RegionId
    root: Place
    projection: RegionProjection
}
```

---

# 40. Region relation

```text
enum RegionRelation {
    Disjoint
    Same
    Contains
    ContainedBy
    Overlaps
    Unknown
}
```

**Unknown không bao giờ được coi là Disjoint.**

---

# 41. Capability conflict

Compiler có thể hỏi:

```text
conflicts(cap_a, cap_b)
```

Ví dụ:

```text
READ + READ       → no conflict
READ + WRITE      → conflict
WRITE + WRITE     → conflict
MOVE + anything   → depends on ownership state
```

---

# 42. View

Semantic representation:

```text
struct ViewValue {
    provenance: ProvenanceId
    region: RegionId
    access: Read
}
```

---

# 43. MutView

```text
struct MutViewValue {
    provenance: ProvenanceId
    region: RegionId
    access: Write
}
```

Không cần compiler coi chúng là pointer.

---

# 44. EffectSet

```text
enum Effect {
    Pure
    ReadMemory
    WriteMemory
    Allocate
    Deallocate
    Drop
    Atomic
    Volatile
    IO
    Panic
    Synchronize
    Foreign
    Comptime
    GPU
}
```

Một function có thể có nhiều effect.

---

# 45. EffectSet nên dùng bitset/interned representation

Ví dụ:

```text
EffectSet {
    bits: u64
}
```

Nếu số effect vượt quá 64, compiler có thể mở rộng representation.

---

# 46. AliasInfo

```text
enum AliasClass {
    NoAlias
    MustAlias
    PartialAlias
    MayAlias
    Unknown
}
```

---

# 47. AliasFact

```text
struct AliasFact {
    left: MemoryLocation
    right: MemoryLocation
    relation: AliasClass
    proof: AliasProof
}
```

---

# 48. AliasProof

Ví dụ:

```text
enum AliasProof {
    CapabilityDisjoint
    DifferentAllocation
    DifferentField
    RangeDisjoint
    ProvenanceDistinct
    Unknown
}
```

---

# 49. `NoAlias` chỉ được sinh khi có proof.

Không có:

```text
"compiler đoán rằng chắc không overlap"
```

---

# 50. EscapeInfo

```text
enum EscapeState {
    NoEscape
    ArgumentEscape
    ReturnEscape
    HeapEscape
    ThreadEscape
    ExternalEscape
    UnknownEscape
}
```

---

# 51. Escape fact

```text
struct EscapeFact {
    place: Place
    state: EscapeState
    point: ProgramPoint
}
```

---

# 52. RangeInfo

```text
struct IntegerRange {
    min: Bound
    max: Bound
}
```

Phục vụ:

```text
bounds-check elimination
overflow analysis
loop optimization
vectorization
```

---

# 53. Range proof

```text
RangeProof {
    source
    constraints
    derived_range
}
```

---

# 54. MemorySSA

Compiler cần semantic memory versions:

```text
MemoryDef
MemoryUse
MemoryPhi
```

Ví dụ:

```text
store x
load x
```

có dependency:

```text
MemoryDef → MemoryUse
```

---

# 55. MemorySSA không thay thế capability system

Hai hệ thống khác nhau:

```text
Capability → "được phép truy cập?"
MemorySSA  → "phụ thuộc memory state nào?"
```

---

# 56. Layout

`LayoutDB`:

```text
struct Layout {
    size: u64
    alignment: u64
    fields: FieldLayoutList
    representation: Representation
}
```

---

# 57. Representation

```text
enum Representation {
    Scalar
    Aggregate
    Enum
    PointerLike
    Vector
    Function
    Opaque
}
```

---

# 58. Layout phải có target context

```text
layout(TypeId, TargetId)
```

Không có:

```text
Type.layout
```

global duy nhất.

---

# 59. ABI signature

```text
struct AbiSignature {
    calling_convention: CallingConvention
    parameters: AbiParamList
    return_abi: AbiReturn
    stack_alignment: u32
    variadic: bool
}
```

---

# 60. ABI parameter

```text
enum AbiParam {
    Register(RegisterClass)
    Stack(StackSlot)
    Indirect
    Split(SplitAbiValue)
    Ignore
}
```

Đây là **physical ABI classification**, không phải source type semantics.

---

# 61. LIR

LIR cần abstraction đủ mạnh cho mọi target:

```text
enum LirInstruction {
    Move
    IntegerBinary
    FloatBinary
    Compare
    Select
    Load
    Store
    Atomic
    Address
    Call
    Return
    Branch
    Switch
    Vector
    Convert
    Trap
}
```

---

# 62. LIR không có register vật lý

Thay vào đó:

```text
VirtualValueId
```

hoặc virtual register:

```text
VReg
```

---

# 63. Nhưng LIR cũng không nên phụ thuộc vào “register machine”.

Đây là điểm WASM kiểm chứng.

Một LIR operation có thể được hạ xuống:

```text
x86 register
ARM register
RV register
WASM stack/local
```

---

# 64. MachineIR

MachineIR mới có:

```text
PhysicalRegister
MachineInstruction
MachineOperand
MachineMemoryOperand
MachineBlock
```

---

# 65. MachineRegister

```text
struct PhysicalRegister {
    class: RegisterClass
    number: u16
}
```

---

# 66. Register class

```text
Integer
Float
Vector
Predicate
Special
```

Target quyết định mapping.

---

# 67. WASM exception

WASM không phải register machine.

Backend có thể có:

```text
MachineValue =
    Local
    Stack
    Global
    Memory
    FunctionReference
```

---

# 68. Vì vậy `MachineIR` phải cho phép backend-specific machine value model.

Đây là refinement quan trọng của task 263.

Không nên ép:

```text
MachineIR = register-only
```

---

# 69. MachineIR contract mới

```text
MachineIR {
    target: TargetId
    blocks: MachineBlockList
    values: MachineValueTable
    metadata: MachineMetadata
}
```

`MachineValue` target-defined nhưng phải qua common interface.

---

# 70. Compiler semantic object graph

```text
FunctionId
   │
   ▼
MirFunction
   │
   ├── LocalId ──→ TypeId
   │
   ├── BasicBlockId
   │       │
   │       ├── Statement
   │       │       └── Place
   │       │             └── LocalId / FieldId
   │       │
   │       └── Terminator
   │
   ├── OwnershipFacts
   ├── CapabilityFacts
   └── EffectSet
```

---

# 71. Type graph

```text
TypeId
 │
 ├── StructType
 │      └── FieldId
 │             └── TypeId
 │
 ├── EnumType
 │      └── VariantId
 │             └── TypeId
 │
 ├── GenericInstance
 │      └── TypeId / ConstValueId
 │
 └── Trait relations
```

---

# 72. Memory graph

```text
Place
 │
 ├── Provenance
 │
 ├── Region
 │
 ├── Capability
 │
 ├── AliasInfo
 │
 ├── EscapeInfo
 │
 └── MemorySSA
```

Đây là một trong những core data graphs của compiler.

---

# 73. ProgramPoint

Ownership/capability/liveness không chỉ gắn với instruction.

```text
struct ProgramPoint {
    block: BasicBlockId
    position: u32
}
```

Có thể mở rộng thành:

```text
BeforeInstruction
AfterInstruction
Terminator
```

---

# 74. Dataflow state

```text
struct DataflowState {
    ownership: OwnershipStateMap
    capabilities: CapabilityMap
    initialization: InitStateMap
}
```

---

# 75. Nhưng không nên nhồi mọi analysis vào một state.

Mỗi analysis có state riêng:

```text
OwnershipState
CapabilityState
LivenessState
RangeState
EscapeState
```

---

# 76. Generic framework

```text
trait DataflowAnalysis {
    type State

    fn initial(...)
    fn transfer(...)
    fn join(...)
    fn equals(...)
}
```

---

# 77. Analysis result

```text
struct AnalysisResult<A> {
    states: ProgramPointMap<A::State>
    facts: FactSet
}
```

---

# 78. Diagnostic proof

Mỗi compiler fact quan trọng có thể giữ:

```text
ProofId
```

Ví dụ:

```text
NoAlias
  ↓
ProofId
  ├── capability A region
  ├── capability B region
  └── region relation = Disjoint
```

---

# 79. Đây là nền tảng cho `ax explain`.

Ví dụ:

```text
ax explain alias file.ax:120
```

có thể truy ngược proof graph.

---

# 80. Source provenance

Mỗi semantic object quan trọng nên có:

```text
SourceOrigin
```

có thể là:

```text
UserSource
Generated
Desugared
CompilerGenerated
Imported
Foreign
```

---

# 81. Generated code

Ví dụ closure:

```text
|x| x + 1
```

compiler tạo:

```text
ClosureId
```

nhưng source origin vẫn trỏ về expression gốc.

---

# 82. Debug mapping

```text
MachineInstruction
      ↓
LirInstruction
      ↓
MirInstruction
      ↓
HirNode
      ↓
SourceSpan
```

---

# 83. Không phải machine instruction nào cũng có một source span duy nhất.

Một source operation có thể sinh nhiều instruction.

Vì vậy mapping là:

```text
many-to-many
```

---

# 84. Semantic metadata không được embed trực tiếp vào machine instruction nếu không cần.

Dùng side tables:

```text
InstructionMetadata
DebugLocation
OptimizationRemark
ProofReference
```

---

# 85. Generic instances

Compiler phải phân biệt:

```text
GenericDefinition
```

và:

```text
GenericInstance
```

Ví dụ:

```text
max<T>
```

là definition.

```text
max<i32>
max<f64>
```

là instances.

---

# 86. Specialization cache

```text
GenericInstanceKey {
    definition
    type_args
    const_args
    target
    feature_set
    optimization_profile
}
```

---

# 87. Closure data

```text
struct ClosureInfo {
    id: ClosureId
    source: SourceSpan
    function: FunctionId
    captures: CaptureListId
    callable_traits: CallableTraitSet
    effects: EffectSetId
}
```

---

# 88. Capture

```text
struct Capture {
    place: Place
    mode: CaptureMode
    field: EnvironmentFieldId
}
```

---

# 89. Async

```text
struct AsyncInfo {
    function: FunctionId
    suspension_points: SuspensionPointListId
    state_fields: StateFieldListId
}
```

---

# 90. Suspension point

```text
struct SuspensionPoint {
    id: SuspensionPointId
    source: SourceSpan
    live_places: PlaceListId
    future_state: StateId
}
```

---

# 91. GPU

```text
struct GpuInfo {
    execution_domain: ExecutionDomain
    storage_requirements: StorageRequirementList
    kernel_kind: KernelKind
}
```

---

# 92. FFI

```text
struct FfiContract {
    abi: AbiKind
    representation: RepresentationContract
    ownership: OwnershipContract
    nullability: Nullability
    effects: EffectSetId
    send_share: SendShareContract
}
```

---

# 93. Compile-time value

```text
struct ConstValue {
    type: TypeId
    value: ConstPayload
}
```

---

# 94. ConstPayload

```text
Bool
Integer
Float
Char
String
Array
Tuple
Struct
Enum
```

Không nên có một `Any` runtime-like container.

---

# 95. Runtime value và compile-time value dùng chung semantic type system

Nhưng execution environment khác nhau:

```text
Runtime
Comptime
```

---

# 96. CompilerDB ownership

```text
CompilerDB
│
├── SourceDB
├── SyntaxDB
├── DeclarationDB
├── TypeDB
├── TraitDB
├── ConstDB
├── GenericDB
├── ClosureDB
├── ComptimeDB
├── HIRDB
├── MIRDB
├── VerificationDB
├── AnalysisDB
├── LayoutDB
├── AbiDB
├── CodegenDB
└── DiagnosticDB
```

---

# 97. Database không sở hữu semantic objects theo kiểu OO hierarchy.

Nó lưu:

```text
ID → immutable record
```

---

# 98. Ví dụ

```text
TypeDB[TypeId]
```

trả:

```text
TypeKind
```

---

# 99. Query

```text
type_of(ExpressionId)
```

không trực tiếp mutate TypeDB.

---

# 100. Derived facts

Những thứ như:

```text
is_copy(T)
is_drop(T)
is_send(T)
is_share(T)
layout(T,target)
abi(F,target)
```

là query/derived fact.

---

# 101. Không duplicate semantic truth

Không được có:

```text
Type.is_copy
TraitDB says Copy
Verifier says Copy
```

rồi ba nơi có thể mâu thuẫn.

Có một authority:

```text
Trait/Type semantic query
```

các subsystem khác consume kết quả.

---

# 102. Query layering

```text
is_copy(T)
   ↓
TraitDB / Type semantics

can_move(place)
   ↓
Ownership verifier

can_view(place)
   ↓
Capability verifier
```

---

# 103. Layout query

```text
layout(T, TargetId)
```

phụ thuộc:

```text
TypeDB
TargetSpec
ReprContract
```

nhưng không làm thay đổi TypeDB.

---

# 104. ABI query

```text
abi(function, TargetId)
```

phụ thuộc:

```text
Type
Layout
TargetSpec
CallingConvention
```

---

# 105. Codegen query

```text
codegen(function, TargetId, Profile)
```

phụ thuộc:

```text
Verified MIR
Optimization
ABI
TargetFeatures
```

---

# 106. Cache identity

Một query cache phải bao gồm tất cả semantic dependencies.

Ví dụ:

```text
CodegenKey {
    FunctionId
    SemanticFingerprint
    TargetId
    FeatureSet
    AbiVersion
    OptimizationProfile
    CodegenVersion
}
```

---

# 107. Semantic fingerprint

Không được đưa:

```text
timestamp
memory address
thread id
```

vào semantic fingerprint.

---

# 108. Determinism

Cùng:

```text
source
compiler semantic version
target
features
configuration
dependencies
```

phải tạo cùng semantic result.

---

# 109. Parallel compiler

Có thể xử lý:

```text
Function A
Function B
Function C
```

song song.

Nhưng không được để:

```text
thread scheduling
hash-map iteration order
```

thay đổi semantic identity.

---

# 110. Arena ownership

Compiler có thể dùng:

```text
Arena<Type>
Arena<MirInstruction>
Arena<BasicBlock>
```

nhưng semantic reference vẫn:

```text
TypeId
InstructionId
BasicBlockId
```

---

# 111. Vì vậy nếu arena relocate object thì semantic references vẫn hợp lệ.

---

# 112. Compiler unsafe implementation

Compiler implementation có thể:

```text
unsafe
custom allocator
packed structs
pointer arithmetic
```

nhưng:

> Unsafe implementation detail không được trở thành semantic assumption của IR.

---

# 113. Ví dụ không được:

```text
Place = *mut MachineAddress
```

---

# 114. Đúng:

```text
Place = Base + Projection
```

và address chỉ xuất hiện ở memory-lowering.

---

# 115. Đây là điểm cực kỳ quan trọng đối với Axiom.

Compiler có thể dùng pointer để **implement `Place`**, nhưng semantic model vẫn không phải pointer model.

---

# 116. IR layering hoàn chỉnh

```text
AST
 │
 ▼
HIR
 │
 ├── resolved names
 ├── types
 ├── traits
 └── effects
 │
 ▼
MIR
 │
 ├── Place
 ├── Operand
 ├── RValue
 ├── Statement
 └── Terminator
 │
 ▼
Verified MIR
 │
 ├── Ownership
 ├── Capability
 ├── Drop
 ├── Send/Share
 ├── Async
 ├── GPU
 └── FFI
 │
 ▼
OptIR
 │
 ├── SSA
 ├── MemorySSA
 ├── Alias
 ├── Range
 ├── Escape
 └── Loop
 │
 ▼
ABI MIR
 │
 ├── Layout
 ├── Calling convention
 ├── Aggregate ABI
 └── physical representation
 │
 ▼
LIR
 │
 └── target-independent machine operations
 │
 ▼
MachineIR
 │
 └── target-specific values/instructions
```

---

# 117. Một quyết định rất quan trọng: **MIR là semantic execution authority**

Không phải HIR.

Không phải OptIR.

Không phải MachineIR.

Nếu có tranh chấp:

```text
Source semantics
        ↓
      MIR
        ↓
 Verified MIR
```

là nguồn kiểm chứng.

---

# 118. OptIR không được trở thành semantic authority

OptIR chỉ là:

> representation tối ưu hóa dựa trên Verified MIR.

---

# 119. MachineIR cũng không được trở thành semantic authority

MachineIR là:

> realization của LIR.

---

# 120. Backend phải có reverse validation

Có thể kiểm tra:

```text
MIR semantics
    ≡
Machine behavior
```

thông qua differential/conformance/translation validation.

---

# 121. Data model cuối cùng

```text
                CompilerDB
                    │
       ┌────────────┴────────────┐
       │                         │
    Semantic                  Physical
       │                         │
       ▼                         ▼
     TypeDB                    LayoutDB
     TraitDB                   AbiDB
     HIRDB                     CodegenDB
     MIRDB                         │
       │                           ▼
   Verified MIR                  LIR
       │                           │
       ▼                           ▼
   Semantic Facts             MachineIR
       │                           │
       └───────────┬───────────────┘
                   ▼
               AxiomObject
```

---

# 122. Frozen invariants

```text
AIRD-20
Compiler semantic identities are represented by explicit IDs.

AIRD-21
Semantic objects must not depend on physical memory addresses for identity.

AIRD-22
Type identity is canonicalized through TypeDB.

AIRD-23
Type semantics are independent of target physical layout.

AIRD-24
Generic definitions and generic instances are distinct entities.

AIRD-25
Aliases and nominal newtypes have distinct semantic identities.

AIRD-26
Place represents semantic storage location independently of machine address.

AIRD-27
Place projections are field-sensitive.

AIRD-28
Operand Copy and Move preserve their semantic ownership meaning.

AIRD-29
Physical copying is not implied by semantic Copy.

AIRD-30
Physical movement is not implied by semantic Move.

AIRD-31
MIR explicitly represents ownership-consuming operations.

AIRD-32
MIR explicitly represents deterministic Drop operations.

AIRD-33
Capability state is represented independently from physical pointer representation.

AIRD-34
Capability provenance is explicit.

AIRD-35
Capability region and access mode are explicit.

AIRD-36
Unknown region overlap must never be treated as disjoint.

AIRD-37
Ownership facts are program-point sensitive.

AIRD-38
Capability facts are program-point sensitive.

AIRD-39
Effect information is part of callable semantic information.

AIRD-40
Alias facts require explicit proof or conservative classification.

AIRD-41
UNKNOWN alias must never become NO_ALIAS without a new proof.

AIRD-42
Escape analysis is distinct from ownership analysis.

AIRD-43
MemorySSA is distinct from capability verification.

AIRD-44
Layout is target-dependent.

AIRD-45
ABI classification is target-dependent.

AIRD-46
ABI classification does not alter source-level type identity.

AIRD-47
LIR must remain independent of physical register names.

AIRD-48
MachineIR may contain target-specific physical machine values.

AIRD-49
MachineIR must not become the semantic authority for source behavior.

AIRD-50
WASM stack/local execution must be representable without pretending it is a register machine.

AIRD-51
Closure state is represented explicitly in compiler data structures.

AIRD-52
Async suspension state is represented explicitly.

AIRD-53
GPU execution/storage domain information is explicit.

AIRD-54
FFI contracts are explicit semantic metadata.

AIRD-55
Generated compiler structures retain source provenance.

AIRD-56
Debug mappings may be many-to-many across compiler layers.

AIRD-57
Derived facts must not duplicate conflicting semantic authority.

AIRD-58
Compiler query results are cacheable only with complete dependency identity.

AIRD-59
Compiler semantic results are deterministic independent of parallel execution order.

AIRD-60
Compiler arenas may move physical objects without changing semantic IDs.

AIRD-61
Compiler implementation may use unsafe mechanisms without exposing them in semantic IR.

AIRD-62
Verified MIR is the semantic correctness boundary.

AIRD-63
OptIR is derived from Verified MIR.

AIRD-64
LIR is derived from ABI MIR.

AIRD-65
MachineIR is derived from LIR.

AIRD-66
No physical backend may directly reinterpret unverified MIR as machine code.

AIRD-67
Every semantic transformation must preserve source-observable behavior.

AIRD-68
Proof-relevant facts should be queryable by diagnostics and AI tooling.

AIRD-69
Semantic fingerprints must exclude nondeterministic implementation state.

AIRD-70
Adding a target must not require changing semantic IR types solely for target representation.
```

---

# 123. Kết quả của task 270

Bây giờ Axiom đã có **ba lớp data model rất rõ**:

### Semantic

```text
Type
Trait
HIR
MIR
Place
Ownership
Capability
Effect
```

### Optimization

```text
SSA
MemorySSA
Alias
Escape
Range
Loop
OptIR
```

### Physical

```text
Layout
ABI
LIR
MachineIR
Object
```

Điểm quan trọng nhất:

> **Không còn lý do để compiler phải đưa pointer/register/stack layout vào semantic Core của Axiom.**

Compiler có thể sử dụng chúng bên dưới, nhưng chúng chỉ xuất hiện khi cần hiện thực hóa chương trình.

---

## Task kế tiếp — **BOOTSTRAP-271: AXIOM COMPILER QUERY ENGINE, INCREMENTAL COMPILATION & PARALLEL SEMANTIC DATABASE**

Task 271 sẽ khóa cách `CompilerDB` thực sự hoạt động: **query dependency graph, revision, invalidation, memoization, parallel queries, cancellation, cycle detection, cache fingerprints và cách compiler có thể compile một project rất lớn mà không build lại toàn bộ**.