# BOOTSTRAP-134 — MIR Semantic Model, Places, Values & Memory Operations

**Trạng thái: FROZEN / COMPLETED**

MIR là **semantic execution IR** của Axiom. Đây là ranh giới cực kỳ quan trọng:

> **HIR mô tả chương trình theo cấu trúc ngôn ngữ; MIR mô tả chính xác chương trình phải làm gì; OptIR mới được phép biến đổi cách thực hiện để tối ưu.**

Do đó MIR không phải “LLVM IR phiên bản đơn giản”.

---

# 1. Vị trí của MIR

Pipeline chuẩn:

```text
Source
  ↓
CST
  ↓
AST
  ↓
Resolution
  ↓
Typed HIR
  ↓
Pattern / Expression lowering
  ↓
MIR
  ↓
Ownership + Capability + Drop + Concurrency verification
  ↓
Verified MIR
  ↓
OptIR
  ↓
ABI MIR
  ↓
Axiom LIR
  ↓
Machine IR
```

Quy tắc:

```text
MIR = Semantic Truth
OptIR = Optimization Representation
```

Không được để optimizer trở thành nơi “sửa” semantic sai của MIR.

---

# 2. MIR không chứa syntax

MIR không còn cần biết:

```text
if
for
match
method syntax
operator syntax
destructuring syntax
```

Ví dụ:

```ax
if x > 10 {
    foo()
} else {
    bar()
}
```

được hạ xuống control flow:

```text
bb0:
    t0 = load x
    t1 = gt t0, 10
    branch t1 -> bb1, bb2

bb1:
    call foo
    goto bb3

bb2:
    call bar
    goto bb3

bb3:
    ...
```

---

# 3. MIR Function

Mỗi function MIR:

```text
MIRFunction {
    FunctionId
    Signature
    Parameters
    Locals
    BasicBlocks
    ReturnPlace
    CleanupInfo
    AsyncInfo?
    GpuInfo?
    FfiInfo?
}
```

---

# 4. Local

MIR local:

```text
Local {
    LocalId
    TypeId
    Mutability
    StorageClass
    SourceOrigin
}
```

Bao gồm:

- parameters;
- local variables;
- temporaries;
- compiler-generated locals;
- async state fields;
- pattern bindings.

---

# 5. Stable LocalId

Không dùng tên string để xác định local.

```text
LocalId
```

là identity semantic.

Tên:

```text
x
```

chỉ là source/debug metadata.

Điều này rất quan trọng cho:

- incremental compilation;
- IDE;
- AI tooling;
- refactoring;
- diagnostics.

---

# 6. Place

Khái niệm trung tâm của MIR:

```text
Place
```

Một Place biểu diễn **nơi chứa một giá trị có thể được đọc, ghi, move hoặc drop**.

Ví dụ:

```ax
user.name
```

là một Place.

```ax
user.name = "A";
```

target assignment là Place.

---

# 7. Place structure

```text
Place {
    Base: PlaceBase
    Projections: [Projection]
}
```

Base có thể:

```text
Local(LocalId)
Static(DeclarationId)
Argument(LocalId)
Return
```

Projection:

```text
Field(FieldId)
TupleField(index)
Index(LocalId)
ConstantIndex(...)
Deref
Downcast(VariantId)
Subslice(...)
```

---

# 8. Ví dụ Place

```ax
user.address.city
```

MIR semantic:

```text
Place(
    Local(user)
    .Field(address)
    .Field(city)
)
```

Không phụ thuộc offset vật lý.

---

# 9. FieldId thay vì offset

MIR tuyệt đối không encode:

```text
offset = 24
```

để biểu diễn field.

Nó dùng:

```text
FieldId
```

Layout phase sau đó mới quyết định offset.

---

# 10. Place ≠ Value

Đây là distinction bắt buộc.

```text
Place
    ↓ read
Value
```

Ví dụ:

```ax
user.name
```

là Place.

```ax
let x = user.name;
```

thực hiện:

```text
read Place
→ Value
→ initialize x
```

---

# 11. Operand

MIR operand:

```text
Operand =
    Copy(Place)
  | Move(Place)
  | Constant(ConstValue)
```

Đây là semantic distinction.

---

# 12. Copy

```text
Copy(place)
```

nghĩa:

> Lấy giá trị theo Copy semantics mà không consume ownership.

Không có nghĩa compiler bắt buộc emit machine copy.

Ví dụ:

```ax
let a = x;
```

với `x: i32` có thể cuối cùng chỉ dùng cùng register.

---

# 13. Move

```text
Move(place)
```

nghĩa:

> Chuyển ownership semantic từ source sang destination.

Không có nghĩa machine-level `memcpy`.

Compiler có thể:

```text
register transfer
pointer transfer
SSA rename
memory elision
```

miễn semantic đúng.

---

# 14. Clone

Clone không phải Operand primitive.

```ax
let y = x.clone();
```

được biểu diễn bằng call:

```text
t = call Clone::clone(x)
```

Điều này giữ nguyên nguyên tắc:

> expensive duplication phải explicit.

---

# 15. RValue

RValue tạo ra value mới:

```text
RValue =
    Use(Operand)
    BinaryOp(...)
    UnaryOp(...)
    Aggregate(...)
    Cast(...)
    Bitcast(...)
    MakeView(...)
    MakeMutView(...)
    Load(...)
    Call(...)
    Discriminant(...)
    Len(...)
    AddressOf(...)
    AtomicLoad(...)
    ...
```

---

# 16. Assignment

MIR assignment:

```text
Assign(
    destination: Place,
    source: RValue
)
```

Ví dụ:

```ax
x = y + 1;
```

→

```text
t0 = Copy(y)
t1 = add(t0, 1)
Assign(x, t1)
```

---

# 17. Assignment không phải expression value

Theo BOOTSTRAP-132:

```text
x = y
```

không tạo ra một value để tiếp tục chain.

MIR cũng giữ semantic này.

---

# 18. Evaluation order

HIR:

```ax
foo(a(), b(), c())
```

MIR phải preserve:

```text
t0 = call a()
t1 = call b()
t2 = call c()
t3 = call foo(t0,t1,t2)
```

Không được tùy ý reorder trước khi effect analysis chứng minh an toàn.

---

# 19. BasicBlock

MIR control flow sử dụng:

```text
BasicBlock {
    BasicBlockId
    Statements[]
    Terminator
}
```

Mỗi block có:

```text
zero or more statements
exactly one terminator
```

---

# 20. Terminator

Các terminator Core:

```text
Goto
Branch
Switch
Return
Unreachable
Call
Panic
DropAndGoto
Await
```

Có thể thêm:

```text
Invoke
Suspend
Resume
```

tùy panic/async lowering stage.

---

# 21. CFG

MIR tạo Control Flow Graph:

```text
        bb0
       /   \
     bb1   bb2
       \   /
        bb3
```

CFG là cơ sở cho:

- ownership analysis;
- definite initialization;
- drop analysis;
- liveness;
- reachability;
- async analysis;
- optimization.

---

# 22. Terminator `Call`

Call có thể tạo normal edge và cleanup edge.

Conceptually:

```text
call foo()
    normal → bb_success
    failure → cleanup
```

Nhưng failure semantics phụ thuộc panic profile.

---

# 23. Panic = control flow

`panic` không phải magic external event.

Semantic MIR:

```text
Panic {
    payload
    PanicPolicy
}
```

`panic=abort`:

```text
Panic → terminate
```

`panic=unwind`:

```text
Panic → cleanup graph → unwind
```

---

# 24. Return

```ax
return value;
```

MIR:

```text
t0 = ...
Assign(return_place, t0)
cleanup
Return
```

Return không được bypass Drop.

---

# 25. Cleanup graph

MIR có cleanup paths.

Ví dụ:

```text
bb0
 │
 ├── normal → bb1
 │
 └── panic → cleanup0
                  ↓
               cleanup1
                  ↓
               unwind
```

Cleanup là semantic obligation.

---

# 26. Drop

MIR statement:

```text
Drop(place)
```

nghĩa:

> thực hiện semantic destruction của value đang owned tại Place.

Không nhất thiết:

```text
free()
```

---

# 27. Drop glue

Compiler tạo:

```text
DropGlue(TypeId)
```

Nếu type trivial:

```text
DropGlue(T) = no-op
```

Optimizer có thể loại bỏ.

Nếu có nested fields:

```text
Drop(User)
    ↓
Drop(name)
    ↓
Drop(buffer)
```

---

# 28. Drop flags

Partial move cần semantic state.

Ví dụ:

```text
User {
    name: String,
    id: u64
}
```

sau:

```text
move user.name
```

MIR verifier biết:

```text
user.name = MOVED
user.id   = INIT
```

Không nhất thiết phải tạo runtime boolean.

---

# 29. Drop flag optimization

Compiler có thể chứng minh:

```text
name always moved
```

→ không cần runtime drop flag.

Hoặc:

```text
name may/may not be moved
```

→ chỉ khi cần mới materialize flag/control state.

---

# 30. Initialization state

MIR verifier theo dõi:

```text
UNINIT
INIT
MOVED
PARTIAL
DROPPED
```

ở granular place tree.

Ví dụ:

```text
user
├── id    INIT
└── name  MOVED
```

---

# 31. StorageLive / StorageDead

MIR có thể có:

```text
StorageLive(local)
StorageDead(local)
```

Nhưng đây là semantic storage lifetime, không phải bắt buộc stack allocation.

Compiler có thể:

```text
register
stack
SSA
eliminate
```

---

# 32. Storage lifetime ≠ physical memory lifetime

Ví dụ:

```text
StorageLive(x)
...
StorageDead(x)
```

không nói:

```text
malloc
free
```

Nó chỉ nói:

> semantic lifetime của local đã bắt đầu/kết thúc.

---

# 33. Temporary lifetime

Expression:

```ax
foo(make_string())
```

MIR tạo temporary nếu cần.

Compiler phải đảm bảo temporary sống đủ lâu để call hoàn thành.

Sau đó:

```text
Drop(temp)
```

nếu cần.

---

# 34. Aggregate

Struct construction:

```ax
User {
    id: 10,
    name: s
}
```

MIR:

```text
t0 = Move(s)
t1 = Aggregate User {
    id: 10,
    name: t0
}
```

---

# 35. Aggregate không yêu cầu physical construction

Optimizer có thể scalarize:

```text
User.id
User.name
```

thành các SSA values.

MIR semantic aggregate vẫn tồn tại.

---

# 36. Enum construction

```ax
Some(value)
```

MIR:

```text
Aggregate EnumVariant(
    Option::Some,
    value
)
```

Không hard-code discriminant integer.

---

# 37. Enum discriminant

Pattern:

```ax
match x {
    Some(v) => ...
    None => ...
}
```

MIR có thể:

```text
t0 = Discriminant(x)

switch t0 {
    Some → ...
    None → ...
}
```

Optimizer/backend quyết định representation.

---

# 38. Downcast

Sau khi biết:

```text
x is Some
```

Place:

```text
x.Some.value
```

có thể biểu diễn:

```text
Downcast(Some)
.Field(value)
```

Verifier phải biết downcast chỉ hợp lệ khi variant đã được chứng minh.

---

# 39. Index

```ax
array[i]
```

MIR:

```text
bounds_check(array, i)
index(array, i)
```

hoặc semantic equivalent.

Bounds check có thể bị optimizer loại nếu RangeInfo chứng minh:

```text
0 <= i < len
```

---

# 40. Index không được unchecked trong safe MIR

Safe code không được hạ trực tiếp:

```text
raw_address = base + i
```

để bỏ bounds check.

Nếu compiler chưa chứng minh an toàn:

```text
check remains
```

---

# 41. Slice/view index

`view<T>` có semantic:

```text
provenance
region
length
access
```

Index phải giữ capability validity.

---

# 42. View construction

```ax
let r = view(x);
```

MIR:

```text
MakeView {
    source: Place(x)
    region: R
    access: READ
}
```

Verifier kiểm tra:

```text
owner alive
region valid
```

---

# 43. `mut_view`

```ax
let r = mut_view(x);
```

MIR:

```text
MakeMutView {
    source: Place(x)
    region: R
    access: WRITE
}
```

Capability phải exclusive.

---

# 44. Capability không nhất thiết tồn tại ở machine code

MIR verifier cần capability metadata.

Sau khi verified:

```text
CapabilityId
RegionId
```

có thể hoàn toàn biến mất.

Nếu representation không observable:

```text
view<T>
```

có thể trở thành:

```text
pointer + length
```

hoặc chỉ:

```text
pointer
```

nếu length compile-time known.

---

# 45. Load

MIR có:

```text
Load(place)
```

nhưng semantic Load phải giữ:

```text
type
memory effect
volatile?
atomic?
```

Không dùng một `Load` generic để che khuất atomic semantics.

---

# 46. Store

```text
Store(place, value)
```

là observable memory write.

Optimizer không được loại bỏ nếu:

- volatile;
- foreign-visible;
- synchronization-sensitive;
- externally observable.

---

# 47. AtomicLoad

Distinct:

```text
AtomicLoad(place, Ordering)
```

với:

```text
Load(place)
```

Ví dụ:

```text
AtomicLoad(x, Acquire)
```

không được biến thành ordinary load.

---

# 48. AtomicStore

```text
AtomicStore(
    place,
    value,
    Ordering
)
```

giữ:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

theo semantics đã frozen.

---

# 49. Volatile

Distinct:

```text
VolatileLoad
VolatileStore
```

Volatile không phải synchronization.

Không được coi:

```text
volatile == atomic
```

---

# 50. Memory effects

MIR operation có effect summary:

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

EffectInfo sau này dùng cho optimization.

---

# 51. Call

MIR call:

```text
Call {
    callee
    args[]
    destination?
    effects
    normal_target
    cleanup_target?
}
```

ABI chưa cần physical register.

---

# 52. Method call

Sau HIR resolution:

```ax
x.length()
```

MIR chỉ còn semantic callee:

```text
Call length(x)
```

Không còn method lookup.

---

# 53. Trait static dispatch

```ax
fn f<T: Add>(x: T)
```

sau monomorphization/resolution có thể:

```text
Call GenericInstanceId(...)
```

---

# 54. Dynamic dispatch

`dyn Trait` giữ dynamic dispatch semantic:

```text
DynCall {
    receiver
    TraitId
    MethodId
}
```

ABI lowering sau đó mới quyết định vtable representation.

---

# 55. Function pointer

Function pointer:

```text
CallIndirect(function_value, args)
```

khác dynamic trait dispatch về semantic identity.

---

# 56. Closure

Closure call:

```text
CallClosure {
    closure
    args
}
```

Closure environment là ordinary compiler-generated aggregate.

Không có hidden universal closure runtime.

---

# 57. Unsafe raw pointer

Raw pointer operation:

```text
LoadRawPointer
StoreRawPointer
PointerOffset
PointerCast
```

chỉ xuất hiện trong MIR khi source đã đi qua unsafe boundary.

Verifier vẫn kiểm tra trusted preconditions.

---

# 58. Pointer → capability

Unsafe code có thể:

```text
raw pointer
    ↓ unsafe contract
safe view
```

MIR:

```text
UnsafeAssume(...)
MakeView(...)
```

Verifier không coi mọi pointer là safe.

---

# 59. Integer → pointer

Không được implicit:

```text
u64 → *mut T
```

trong safe MIR.

Unsafe intrinsic/system operation phải explicit.

Provenance không được tự suy ra từ integer.

---

# 60. AddressOf

Compiler internal:

```text
AddressOf(place)
```

chỉ hợp lệ khi semantic contract yêu cầu address.

Điều này cho phép optimizer biết:

```text
address escapes?
```

và quyết định có thể scalarize/stack-promote hay không.

---

# 61. Stable address

Nếu:

```ax
address_of(x)
```

được expose ra code có thể observe, storage relocation có thể trở thành observable.

Verifier đánh dấu:

```text
StableAddressRequired
```

Sau đó optimizer không được:

```text
stack → register
move allocation
```

nếu làm invalid address contract.

---

# 62. Escape information

MIR ghi nhận:

```text
NoEscape
ArgumentEscape
ReturnEscape
HeapEscape
ThreadEscape
ExternalEscape
UnknownEscape
```

Escape analysis sau này dùng nó.

---

# 63. Memory operation và ownership

Ví dụ:

```ax
let y = move x;
```

không phải:

```text
Load(x)
Store(y)
```

đơn giản.

Nó là:

```text
Move(x)
Initialize(y)
```

Ownership verifier theo dõi semantic transition.

---

# 64. Memory operation và Copy

```ax
let y = x;
```

nếu Copy:

```text
Copy(x)
Initialize(y)
```

Physical implementation có thể hoàn toàn không copy.

---

# 65. `memcpy`

Nếu programmer yêu cầu raw byte copy:

```text
memcpy
```

thì đây là system/unsafe operation.

Nó không tự động tạo semantic `Copy<T>`.

Đây là distinction rất quan trọng.

---

# 66. Bitcast

```ax
bitcast<T>(x)
```

MIR:

```text
Bitcast {
    source
    target_type
}
```

Verifier kiểm tra:

```text
size
alignment
valid representation
```

---

# 67. Cast

```ax
x as i64
```

MIR:

```text
Cast {
    source
    target_type
    CastKind
}
```

`CAST` và `BITCAST` không được nhập thành một operation.

---

# 68. Constant

MIR constant:

```text
Constant(ConstValue)
```

ConstValue có semantic type.

Ví dụ:

```text
Integer
Float
Bool
Char
StringConstant
AggregateConstant
FunctionRef
TypeMetadata
```

tùy context.

---

# 69. Compile-time evaluation

Nếu:

```ax
const X = expensive_comptime_calculation();
```

MIR của comptime execution được chạy trong Comptime VM.

Runtime MIR không được tự động phụ thuộc vào compiler execution side effects.

---

# 70. Async

`await` được biểu diễn rõ:

```text
Await {
    future
    suspension_point
    resume_target
}
```

Lowering sau đó có thể biến thành state machine.

---

# 71. Live state qua await

Trước await:

```text
x
y
future
```

Compiler xác định:

```text
x → dead
y → live
future → live
```

Chỉ state cần thiết mới trở thành coroutine state.

---

# 72. Capability qua await

Nếu:

```text
mut_view<T>
```

đang live qua suspension:

```text
await
```

verifier kiểm tra rule async đã frozen.

Mặc định:

```text
reject
```

nếu capability không có contract cho phép.

---

# 73. Thread migration

MIR không giả định:

```text
async = thread
```

Future có thể:

```text
same thread
different thread
```

Send verification xảy ra trước scheduler/runtime.

---

# 74. GPU MIR

GPU operation cũng không được biến CPU/GPU thành một semantics hỗn loạn.

MIR có domain:

```text
ExecutionDomain
StorageDomain
```

Ví dụ:

```text
LaunchKernel
CopyHostToDevice
CopyDeviceToHost
GpuWait
```

được biểu diễn explicit.

---

# 75. GPU capability

`DeviceView<T>` có domain:

```text
DEVICE
```

không tự biến thành:

```text
Host view<T>
```

Cross-domain operation phải explicit.

---

# 76. FFI

MIR:

```text
ForeignCall {
    ABI
    symbol
    args
    returns
    effects
    safety_contract
}
```

Foreign call mặc định conservative:

```text
Read
Write
External
```

nếu compiler không có contract đầy đủ.

---

# 77. FFI memory ownership

Foreign function:

```text
extern "C" fn foo(...)
```

không tự cho compiler biết:

```text
who owns returned pointer?
who frees it?
does it retain pointer?
does it mutate?
```

Phải có explicit FFI contract/wrapper.

---

# 78. MIR verifier boundary

Pipeline:

```text
Typed HIR
    ↓
MIR construction
    ↓
MIR structural validation
    ↓
Ownership verification
    ↓
Capability verification
    ↓
Drop verification
    ↓
Concurrency verification
    ↓
Async/GPU/FFI verification
    ↓
Verified MIR
```

---

# 79. Structural MIR verifier

Trước semantic verifier phải kiểm tra:

- mọi block có terminator;
- mọi LocalId tồn tại;
- mọi FieldId thuộc type tương ứng;
- mọi VariantId hợp lệ;
- mọi projection hợp lệ;
- CFG target tồn tại;
- type assignment đúng;
- call signature đúng;
- return type đúng.

---

# 80. Semantic verifier

Sau đó:

```text
ownership
capability
initialization
drop
send/share
async
GPU
FFI
```

---

# 81. MIR không được tự sửa lỗi

Verifier không được:

```text
detect invalid move
→ silently insert clone
```

hoặc:

```text
invalid alias
→ silently add lock
```

Nếu semantic program invalid:

```text
reject
```

---

# 82. MIR canonicalization

Trước verification có thể canonicalize:

```text
temporary naming
constant normalization
CFG cleanup
projection normalization
```

nhưng không được thay đổi semantics.

---

# 83. MIR determinism

Cùng source + cùng compiler semantic configuration:

```text
MIR semantic graph
```

phải deterministic.

Parallel compilation không được làm thay đổi semantic result.

---

# 84. MIR fingerprints

MIR có fingerprint cho incremental compilation:

```text
FunctionId
+
generic args
+
semantic body
+
dependencies
```

Implementation-only change chỉ invalidate các dependents cần thiết.

---

# 85. MIR serialization

Có thể emit:

```text
.axmir
```

cho debugging/research.

Không nhất thiết là public stable format.

Mục đích:

- compiler debugging;
- AI inspection;
- regression tests;
- optimizer research.

---

# 86. AI inspection

CLI:

```text
axc inspect mir file.ax
axc inspect verified-mir file.ax
```

Có thể hỏi:

```text
Why is this value moved?
Why can't this view live across await?
Why is this allocation not eliminated?
Why can't these regions be considered disjoint?
```

Đây là một trong những điểm Axiom có thể vượt các compiler truyền thống về developer experience.

---

# 87. MIR semantic invariant

MIR phải thỏa:

```text
Every operation has an unambiguous semantic meaning.
```

Không được có instruction kiểu:

```text
MAGIC
UNKNOWN
DO_WHATEVER
```

trong Verified MIR.

---

# 88. Optimizer boundary

Chỉ:

```text
Verified MIR
```

được đưa vào:

```text
SSA / MemorySSA / OptIR
```

Optimizer không phải safety verifier.

Nếu optimizer phát hiện semantic invariant bị phá:

```text
compiler bug
```

không phải:

```text
program undefined behavior
```

---

# 89. MIR vs Undefined Behavior

Axiom safe program không được dựa vào UB kiểu C để compiler tự do.

Do đó:

```text
invalid safe MIR
→ compiler error/internal compiler bug
```

Raw unsafe contracts vẫn có các preconditions rõ ràng.

---

# 90. MIR core data model

Tổng hợp:

```text
MIRFunction
 ├── Signature
 ├── Locals
 ├── BasicBlocks
 │    ├── Statements
 │    │    ├── Assign
 │    │    ├── StorageLive
 │    │    ├── StorageDead
 │    │    ├── Drop
 │    │    └── Capability ops
 │    │
 │    └── Terminator
 │         ├── Goto
 │         ├── Branch
 │         ├── Switch
 │         ├── Call
 │         ├── Return
 │         ├── Panic
 │         ├── Await
 │         └── Unreachable
 │
 └── Metadata
```

---

# 91. RValue model

```text
RValue
 ├── Use
 ├── UnaryOp
 ├── BinaryOp
 ├── Aggregate
 ├── Cast
 ├── Bitcast
 ├── MakeView
 ├── MakeMutView
 ├── Load
 ├── AtomicLoad
 ├── VolatileLoad
 ├── Discriminant
 ├── Len
 ├── AddressOf
 ├── CallResult
 └── Intrinsic
```

Intrinsic chỉ dành cho compiler/system primitives đã được định nghĩa.

---

# 92. Place model

```text
Place
 ├── Local
 ├── Static
 │
 └── Projection*
      ├── Field
      ├── TupleField
      ├── Index
      ├── ConstantIndex
      ├── Deref
      ├── Downcast
      └── Subslice
```

Đây là model đủ mạnh để biểu diễn cả high-level code lẫn systems code mà không cần programmer viết pointer/reference trong safe Core.

---

# 93. Tại sao model này phù hợp mục tiêu Axiom?

Nó cho phép:

```text
Programmer
    ↓
simple value-oriented syntax
    ↓
Compiler
    ↓
ownership analysis
capability analysis
alias analysis
escape analysis
drop analysis
    ↓
efficient machine code
```

Tức là đúng triết lý:

> **Compiler phức tạp hơn programmer, không phải ngược lại.**

---

# 94. Các invariant chính

### `AMIR-20`
MIR is the semantic execution representation of Axiom.

### `AMIR-21`
MIR semantics are independent of physical machine representation.

### `AMIR-22`
MIR uses stable semantic identities rather than source strings.

### `AMIR-23`
Place and Value are distinct semantic concepts.

### `AMIR-24`
Every readable/writable storage location is represented by a Place.

### `AMIR-25`
Place projections use semantic FieldId/VariantId information.

### `AMIR-26`
Physical field offsets do not appear in semantic MIR.

### `AMIR-27`
Copy and Move are semantically distinct.

### `AMIR-28`
Move does not imply physical copying.

### `AMIR-29`
Copy does not require physical copying.

### `AMIR-30`
Clone is explicit and never implicit.

### `AMIR-31`
MIR preserves source evaluation order.

### `AMIR-32`
Every basic block has exactly one terminator.

### `AMIR-33`
Every CFG target is valid.

### `AMIR-34`
Every MIR operation is type-correct.

### `AMIR-35`
Return paths perform required cleanup.

### `AMIR-36`
Drop semantics are deterministic.

### `AMIR-37`
Partial move state is represented at place granularity.

### `AMIR-38`
Moved places cannot be consumed again without reinitialization.

### `AMIR-39`
Uninitialized places cannot be read.

### `AMIR-40`
Double drop is invalid.

### `AMIR-41`
Storage lifetime is distinct from physical allocation lifetime.

### `AMIR-42`
Safe view creation requires valid ownership provenance.

### `AMIR-43`
Mutable capabilities are exclusive.

### `AMIR-44`
Capability metadata may be erased after verification when unobservable.

### `AMIR-45`
Atomic operations remain distinct from ordinary memory operations.

### `AMIR-46`
Volatile operations remain distinct from atomic operations.

### `AMIR-47`
Raw pointer operations are explicit unsafe/system operations.

### `AMIR-48`
Integer-to-pointer conversion cannot create safe provenance.

### `AMIR-49`
Address-taking creates observable storage constraints when externally observable.

### `AMIR-50`
Escape information is explicitly represented or derivable.

### `AMIR-51`
Enum semantics do not depend on physical discriminant representation.

### `AMIR-52`
Pattern lowering preserves ownership and Drop semantics.

### `AMIR-53`
Call operations preserve their declared semantic effects.

### `AMIR-54`
Foreign calls have explicit ABI semantics.

### `AMIR-55`
Unknown foreign effects are treated conservatively.

### `AMIR-56`
Await is an explicit suspension boundary.

### `AMIR-57`
Values crossing await satisfy async storage/Send requirements.

### `AMIR-58`
GPU execution and storage domains remain explicit.

### `AMIR-59`
Cross-domain GPU operations are explicit.

### `AMIR-60`
Invalid MIR is rejected before optimization.

### `AMIR-61`
Verified MIR is the only input to semantic optimization.

### `AMIR-62`
Optimization cannot redefine MIR semantics.

### `AMIR-63`
MIR semantics are deterministic.

### `AMIR-64`
MIR supports incremental compilation.

### `AMIR-65`
MIR can be inspected independently of machine code.

### `AMIR-66`
MIR diagnostics preserve source provenance.

### `AMIR-67`
MIR verification is independent from optimization level.

### `AMIR-68`
Safe semantic violations cannot be delegated to runtime UB.

### `AMIR-69`
Compiler-generated MIR must pass the same verifier as source-derived MIR.

### `AMIR-70`
No unverified semantic operation may reach code generation.

---

# Chuỗi kiến trúc hiện tại

Axiom hiện đã đi khá sâu:

```text
123 Syntax
124 Standard Library
125 Compiler DB
126 Lexer
127–129 Type System
130 Traits
131 Name Resolution
132 Expressions / Control Flow
133 Patterns
134 MIR
        ↓
135 ?
```

## BOOTSTRAP-135 — Ownership, Initialization & Drop Verification Engine

Đây là task tiếp theo và là một **mốc rất quan trọng**.

Ta sẽ thiết kế verifier thực sự vận hành trên MIR:

```text
MIR
 │
 ├── Definite Initialization
 ├── Move Analysis
 ├── Partial Move
 ├── Copy Analysis
 ├── Drop Analysis
 ├── Cleanup Paths
 ├── Capability Lifetime
 ├── Alias/Overlap
 ├── Escape Analysis
 └── Verification State
        ↓
   VERIFIED MIR
```

Đặc biệt sẽ giải quyết dứt điểm câu hỏi trước đây của Axiom:

> **Làm thế nào để có ownership + memory safety + deterministic destruction mà programmer không phải viết borrow checker/lifetime/reference phức tạp?**

Đây sẽ là phần biến triết lý **“compiler quản lý lifetime, programmer quản lý ownership”** thành thuật toán compiler cụ thể.