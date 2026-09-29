# BOOTSTRAP-225 — HIR → MIR SEMANTIC LOWERING

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là một trong những task quan trọng nhất của Axiom compiler.

Nếu HIR trả lời:

> “Chương trình này có ý nghĩa gì?”

thì MIR phải trả lời:

> “Chính xác máy thực thi chương trình này theo thứ tự semantic nào?”

Mục tiêu của 225 là tạo ra **một MIR đủ thấp để verifier và interpreter hiểu hoàn toàn, nhưng đủ cao để chưa phụ thuộc CPU/ABI/layout cụ thể**.

---

# 1. Vị trí MIR

Pipeline chính:

```text
Source
  ↓
Lossless Syntax
  ↓
AST
  ↓
Resolution
  ↓
Typed HIR
  ↓
────────────────────
HIR → MIR            ← BOOTSTRAP-225
────────────────────
  ↓
Raw MIR
  ↓
Ownership Verification
  ↓
Capability Verification
  ↓
Effect Verification
  ↓
Verified MIR
  ↓
Semantic Optimization
  ↓
OptIR
```

MIR **không phải machine IR**.

Nó chưa biết:

- register;
- stack offset;
- calling convention vật lý;
- x86 instruction;
- ARM instruction;
- ELF relocation;
- PE section.

---

# 2. Nguyên tắc trung tâm

Axiom MIR phải thỏa:

> **Một semantic operation trong source phải có representation xác định trong MIR.**

Không để các semantic quan trọng bị “ngầm hiểu” ở backend.

Ví dụ:

```axiom
a + b
```

không được xuống MIR như một opcode mơ hồ:

```text
ADD
```

mà phải biết:

```text
operator resolution
type
overflow semantics
trait implementation
evaluation order
```

sau đó mới có:

```text
BinaryOp(Add, a, b)
```

---

# 3. MIR không được phụ thuộc optimizer

Raw MIR phải có nghĩa **ngay cả khi không có optimization**.

Ví dụ:

```text
let x = expensive()
return x
```

MIR phải biểu diễn đầy đủ call và return.

Optimizer có thể loại bỏ/collapse sau đó.

---

# 4. MIR là semantic source of truth

Các tầng sau:

```text
Ownership
Capability
Effect
Async
Optimization
ABI
Codegen
```

đều đọc MIR.

Không được có:

```text
AST semantics
        ↘
         Backend tự hiểu
```

Mà phải:

```text
Typed HIR
    ↓
MIR
 ↓  ↓  ↓
Verifier / Interpreter / Optimizer / Debugger
```

---

# 5. MIR Function

Đề xuất:

```text
MIRFunction {
    id: FunctionId
    signature: MIRSignature
    locals: [Local]
    blocks: [BasicBlock]
    entry: BasicBlockId
    return_place: Place
    cleanup: CleanupInfo
    effects: EffectSet
    async_info: Option<AsyncInfo>
    gpu_info: Option<GpuInfo>
    source_map: MIRSourceMap
}
```

---

# 6. Local

```text
Local {
    id: LocalId
    type: TypeId
    mutable: bool
    storage_class: StorageClass
    source: SourceSpanId
}
```

Ví dụ:

```axiom
let mut x: i32 = 10
```

có thể tạo:

```text
Local %x : i32
mutable = true
```

---

# 7. Place

Place là khái niệm cực kỳ quan trọng.

```text
Place =
    Base
    + Projection*
```

Ví dụ:

```axiom
user.address.city
```

thành:

```text
%user
  .field(address)
  .field(city)
```

---

# 8. Place không phải địa chỉ

MIR:

```text
Place(%user.field(address))
```

không có nghĩa:

```text
memory address = 0x1234
```

Nó là **semantic storage location**.

Backend sau này có thể biến nó thành:

- register;
- stack slot;
- offset;
- memory;
- SSA value.

---

# 9. Projection

Core projections:

```text
Field(field_id)
Index(index_operand)
Deref(raw_pointer)
Downcast(enum_variant)
SliceRange(start, end)
```

Không phải projection nào cũng safe.

Ví dụ:

```text
Deref
```

có thể yêu cầu unsafe context.

---

# 10. Operand

```text
Operand =
    Copy(Place)
    Move(Place)
    Constant(ConstantValue)
```

Đây là điểm MIR bắt đầu mang ownership semantics rõ ràng.

---

# 11. Copy

```axiom
let b = a
```

Nếu `a: Copy`:

```text
% b = Copy(%a)
```

Không có nghĩa compiler phải emit machine `memcpy`.

---

# 12. Move

Nếu `a` không Copy:

```axiom
let b = a
```

thành:

```text
%b = Move(%a)
```

Ownership verifier đánh dấu:

```text
a → Moved
b → Owned
```

---

# 13. Constant

```text
Constant {
    type: TypeId
    value: ConstValue
}
```

Ví dụ:

```text
42 : i32
3.14 : f64
true : bool
```

String literals có thể tham chiếu constant/static data semantics.

---

# 14. RValue

RValue tạo ra giá trị mới.

Core:

```text
RValue =
    Use(Operand)
    UnaryOp
    BinaryOp
    Cast
    Bitcast
    Aggregate
    Tuple
    Array
    Enum
    MakeView
    MakeMutView
    CallResult
    FunctionReference
    Closure
    ComptimeValue
    Load
    AtomicLoad
```

---

# 15. Statement

```text
Statement =
    Assign(Place, RValue)
    StorageLive(Local)
    StorageDead(Local)
    Drop(Place)
    Nop
```

Các semantic operation đặc biệt có thể có instruction riêng.

---

# 16. Terminator

Mỗi BasicBlock kết thúc bằng đúng một terminator:

```text
Terminator =
    Goto(BasicBlockId)
    Branch(Condition, TrueBlock, FalseBlock)
    Switch(...)
    Return
    Unreachable
    Call(...)
    Panic(...)
    Throw?              // không có trong Core
    Await(...)
    Yield(...)
    Invoke(...)          // chỉ profile có unwind
```

---

# 17. Basic Block invariant

Mỗi block:

```text
Statements*
Terminator
```

Không có instruction sau terminator.

---

# 18. CFG

Ví dụ:

```axiom
if x > 0 {
    foo()
} else {
    bar()
}
```

MIR:

```text
BB0:
    %c = BinaryOp(Gt, %x, 0)
    Branch %c → BB1, BB2

BB1:
    Call foo
    Goto BB3

BB2:
    Call bar
    Goto BB3

BB3:
    Return
```

---

# 19. Evaluation order

Axiom đã chọn **deterministic evaluation order**.

MIR phải encode thứ tự đó.

Ví dụ:

```axiom
f(a(), b())
```

không được để backend tự chọn:

```text
a() then b()
```

hay:

```text
b() then a()
```

Nếu semantic order của Axiom là left-to-right thì MIR phải là:

```text
%a = Call a()
%b = Call b()
%r = Call f(%a, %b)
```

---

# 20. Function call

MIR:

```text
Call {
    callee
    args
    destination
    normal_target
    unwind_target?
}
```

Ví dụ:

```text
%result = Call add(%a, %b)
```

---

# 21. Call destination

Không nhất thiết function result phải tạo temporary vật lý.

MIR chỉ nói:

```text
destination = %result
```

Optimizer/ABI có thể dùng:

- register return;
- caller-allocated return;
- hidden return pointer;
- scalar replacement.

---

# 22. Method call

Source:

```axiom
x.length()
```

sau method resolution trở thành:

```text
Call length(x)
```

MIR **không cần giữ method syntax**.

---

# 23. Operator call

Source:

```axiom
a + b
```

sau trait resolution:

```text
Call <Add implementation>(a, b)
```

hoặc intrinsic semantic `BinaryOp`.

Điểm quyết định:

> MIR giữ **semantic operator**, không phụ thuộc việc implementation cuối cùng là function hay intrinsic.

---

# 24. Short-circuit

```axiom
a && b
```

không được lower thành:

```text
BinaryOp(AND, a, b)
```

vì `b` có thể có side effect và không luôn được evaluate.

Phải:

```text
evaluate a
Branch a → evaluate_b, false

evaluate_b
...
```

---

# 25. `||`

Tương tự:

```text
a || b
```

phải preserve:

```text
if a == true
    result = true
else
    evaluate b
```

---

# 26. If expression

```axiom
let x = if cond {
    a
} else {
    b
}
```

MIR:

```text
BB0:
    Branch cond → BB1, BB2

BB1:
    %tmp = a
    Goto BB3

BB2:
    %tmp = b
    Goto BB3

BB3:
    %x = Move(%tmp)
```

---

# 27. Block expression

```axiom
let x = {
    foo()
    bar()
    42
}
```

HIR có block expression.

MIR:

```text
Call foo
Call bar
Assign x = 42
```

Không cần runtime object cho block.

---

# 28. Temporary values

Compiler tạo temporaries khi semantic evaluation cần.

Ví dụ:

```axiom
foo(make(), calculate())
```

có thể:

```text
_tmp0 = Call make()
_tmp1 = Call calculate()
Call foo(_tmp0, _tmp1)
```

Ownership verifier theo dõi từng temporary.

---

# 29. Temporary lifetime

Temporary sống tới semantic point cuối cùng mà language yêu cầu.

Compiler có thể rút ngắn physical lifetime nếu không observable.

Không được rút ngắn semantic lifetime trước verifier.

---

# 30. Struct construction

```axiom
Point {
    x: 1
    y: 2
}
```

MIR:

```text
%p = Aggregate Point {
    x = 1,
    y = 2
}
```

Field order vật lý không nằm ở MIR semantic aggregate.

---

# 31. Struct field assignment

```axiom
p.x = 10
```

MIR:

```text
Assign(
    Place(%p.field(x)),
    Constant(10)
)
```

---

# 32. Tuple

```axiom
(a, b)
```

MIR:

```text
Aggregate Tuple {
    field0 = a
    field1 = b
}
```

---

# 33. Array

```axiom
[1, 2, 3, 4]
```

MIR:

```text
Aggregate Array<4,i32> {
    1,2,3,4
}
```

Bounds are semantic facts, not backend assumptions.

---

# 34. Indexing

```axiom
a[i]
```

MIR semantic form:

```text
IndexCheck(a, i)
IndexAccess(a, i)
```

hoặc một `Index` operation có attached bounds obligation.

Sau này bounds-check elimination có thể loại bỏ check khi proof tồn tại.

---

# 35. Slice

```axiom
a[start..end]
```

MIR:

```text
BoundsCheck(start)
BoundsCheck(end)
RangeCheck(start <= end)
MakeView(a, start, end)
```

---

# 36. View creation

```axiom
let v = view(x)
```

MIR:

```text
%v = MakeView(
    provenance = %x,
    region = Region(...)
)
```

Đây **không phải pointer allocation**.

---

# 37. Mutable view

```axiom
let v = mut_view(x)
```

MIR:

```text
%v = MakeMutView(
    provenance = %x,
    region = Region(...)
)
```

Capability verifier sẽ xác nhận exclusivity.

---

# 38. Ephemeral implicit view

Source:

```axiom
foo(x)
```

nếu parameter:

```text
view<T>
```

HIR có expected-view conversion.

MIR có:

```text
%view = MakeView(%x)
Call foo(%view)
```

Compiler có thể eliminate `%view` vật lý.

---

# 39. Move through call

```axiom
consume(x)
```

nếu parameter nhận ownership:

```text
Call consume(Move(%x))
```

Ownership verifier đánh dấu x moved.

---

# 40. Borrowing không xuất hiện như source-level syntax

Axiom không có:

```text
&x
&mut x
```

nhưng MIR vẫn có:

```text
MakeView
MakeMutView
```

Đây chính là nguyên tắc:

> **Compiler cần semantic machinery mà programmer không cần viết.**

---

# 41. Drop candidates

HIR/MIR lowering không nhất thiết chèn toàn bộ `Drop` ngay lập tức.

Có thể tạo:

```text
DropCandidate(Local/Place)
```

để Drop elaboration sau ownership verification quyết định chính xác:

```text
when
where
whether
```

drop xảy ra.

---

# 42. Drop elaboration

Pipeline:

```text
Raw MIR
 ↓
Ownership analysis
 ↓
Drop elaboration
 ↓
Verified MIR
```

Ví dụ:

```axiom
let a = make_a()
if cond {
    return
}
let b = make_b()
```

Compiler phải tạo cleanup path đúng cho:

```text
a
b
```

tùy control flow.

---

# 43. Partial move

```axiom
let x = User { a, b }

let y = x.a
```

Nếu partial move được phép:

```text
x.a → Moved
x.b → Owned
```

MIR:

```text
%y = Move(%x.field(a))
```

Không đánh dấu toàn bộ `%x` moved.

---

# 44. Custom Drop

Nếu `User` có user-defined Drop:

```text
partial move
```

có thể bị cấm theo frozen memory model.

MIR verifier phải biết:

```text
Drop(User)
```

và reject partial move.

---

# 45. Return

```axiom
return x
```

MIR:

```text
Assign(return_place, Move(%x))
Return
```

Nếu Copy:

```text
Assign(return_place, Copy(%x))
```

---

# 46. Early return

Cleanup phải xảy ra trước:

```text
Return
```

nếu resources đang live.

Ví dụ:

```text
Drop(b)
Drop(a)
Return
```

theo cleanup order.

---

# 47. `?`

Source:

```axiom
let x = foo()?
```

HIR desugaring thành control flow.

Ví dụ:

```text
r = foo()

Switch r:
    Ok(v)  → continue
    Err(e) → return Err(e)
```

Không có special runtime mechanism.

---

# 48. Match

`match` phải lower thành CFG/switch structure.

Ví dụ:

```axiom
match x {
    Some(v) => foo(v)
    None => bar()
}
```

MIR:

```text
SwitchVariant x:
    Some → BB1
    None → BB2
```

---

# 49. Exhaustiveness

Exhaustiveness đã được kiểm tra ở frontend/pattern phase.

MIR vẫn phải có fallback:

```text
Unreachable
```

nếu semantic model chứng minh không thể xảy ra.

---

# 50. Enum discriminant

MIR semantic operation:

```text
Discriminant(place)
```

Không nhất thiết biết physical byte layout.

Backend/layout phase quyết định representation.

---

# 51. Loop

```axiom
loop {
    foo()
}
```

MIR:

```text
BB_loop:
    Call foo
    Goto BB_loop
```

---

# 52. Break

`break` trở thành:

```text
Goto(loop_exit)
```

---

# 53. Continue

```text
Goto(loop_header)
```

---

# 54. While

```axiom
while cond {
    foo()
}
```

```text
BB_header:
    c = cond
    Branch c → BB_body, BB_exit

BB_body:
    foo()
    Goto BB_header

BB_exit:
    ...
```

---

# 55. For

Iterator syntax:

```axiom
for x in items {
    foo(x)
}
```

được lower về semantic iterator protocol:

```text
iterator = IntoIterator(items)

loop:
    next = iterator.next()
    match next:
        Some(x) → body
        None → exit
```

Sau đó optimizer có thể specialize/fuse.

---

# 56. Closure

```axiom
let offset = 10
let f = |x| x + offset
```

HIR đã xác định capture.

MIR tạo:

```text
ClosureEnv {
    offset
}
```

và:

```text
ClosureValue {
    function = closure_body
    environment = env
}
```

Representation chưa quyết định heap/stack/register.

---

# 57. Closure capture mode

Ownership semantics:

```text
Copy capture
Move capture
View capture
MutView capture
```

được explicit trong MIR metadata.

Verifier quyết định tính hợp lệ.

---

# 58. Non-capturing closure

Có thể lower thành:

```text
FunctionReference
```

không cần environment.

Compiler có thể convert thành function pointer nếu ABI context cho phép.

---

# 59. Async

Async không phải backend primitive.

Source:

```axiom
async fn foo() -> T
```

ban đầu tạo:

```text
AsyncFunction
```

Sau async lowering:

```text
FutureStateMachine
```

và cuối cùng trở thành ordinary MIR.

---

# 60. Await

`await` tạo suspension point:

```text
SuspensionPointId
```

MIR trước async lowering có thể có:

```text
Await(future)
```

sau lowering:

```text
poll future
if Pending:
    save live state
    suspend
if Ready:
    continue
```

---

# 61. Live-across-await

Verifier xác định:

```text
locals live across suspension
```

Chỉ những giá trị cần thiết mới trở thành state fields.

Ví dụ:

```text
a = ...
b = ...

await foo()

use(a)
```

`b` không còn live:

```text
b → StateFieldElided
```

---

# 62. Async state machine

Semantic representation:

```text
FutureState {
    state: StateId
    fields: [StateField]
}
```

Không yêu cầu heap.

Compiler có thể:

- inline;
- stack allocate;
- caller allocate;
- heap allocate nếu escape.

---

# 63. Panic

```axiom
panic("failed")
```

MIR:

```text
Panic {
    payload
}
```

Không phải ordinary function call có thể bị optimizer xóa tùy ý.

Effect system đánh dấu:

```text
Panic
```

---

# 64. Unreachable

```text
unreachable
```

MIR:

```text
Unreachable
```

Optimizer được phép dùng nó như semantic fact.

---

# 65. Volatile

System/unsafe layer:

```text
volatile_load(p)
volatile_store(p, x)
```

MIR:

```text
VolatileLoad
VolatileStore
```

Không được CSE/hoist/remove như ordinary memory access.

---

# 66. Atomic

```text
AtomicLoad
AtomicStore
AtomicRMW
AtomicCompareExchange
```

MIR phải giữ:

```text
ordering
scope
type
```

Ví dụ:

```text
AtomicLoad(
    place,
    Acquire
)
```

---

# 67. Synchronization

Mutex/channel/etc. có semantic effects.

Không nhất thiết mỗi library operation trở thành Core MIR opcode.

Nhưng effect metadata phải biểu diễn:

```text
Synchronize
```

khi compiler cần hiểu synchronization boundary.

---

# 68. Foreign call

```axiom
extern "C" fn printf(...)
```

MIR:

```text
ForeignCall
```

với:

```text
FfiContractId
```

Compiler không tự giả định foreign function pure.

---

# 69. Effect metadata

Mỗi call có thể mang:

```text
EffectSummary
```

ví dụ:

```text
Read
Write
Allocate
Drop
IO
Atomic
Synchronize
Panic
Foreign
```

Effect verifier/optimizer sử dụng thông tin này.

---

# 70. Allocation

MIR có semantic:

```text
Alloc(type, layout)
Dealloc(storage)
```

nhưng **không phải**:

```text
malloc()
free()
```

Backend/runtime quyết định implementation.

---

# 71. Allocation elimination

Raw MIR:

```text
Alloc
Store
Load
Dealloc
```

có thể sau optimization biến thành:

```text
SSA values
```

nếu address không escape.

---

# 72. Storage lifetime

MIR có:

```text
StorageLive
StorageDead
```

nhưng đây là semantic lifetime boundaries, không nhất thiết machine allocation.

---

# 73. Address-taking

Safe Axiom không có general address-taking.

System/unsafe:

```axiom
address_of(x)
```

MIR:

```text
AddressOf(Place(x))
```

Ngay lúc đó:

```text
EscapeInfo
StableAddressRequirement
```

có thể được kích hoạt.

---

# 74. Raw pointer dereference

```axiom
*p
```

unsafe:

```text
RawLoad(
    pointer = p,
    type = T
)
```

Verifier phải biết đây là unsafe-origin operation.

---

# 75. Pointer arithmetic

```text
PointerOffset(p, offset)
```

unsafe.

Không được biến integer arithmetic thành valid pointer tự động.

---

# 76. Bitcast

```axiom
bitcast<T>(x)
```

MIR:

```text
Bitcast {
    source_type
    target_type
}
```

Representation verifier kiểm tra validity.

---

# 77. Cast

```axiom
x as i64
```

MIR:

```text
Cast(
    source = x
    target = i64
    semantics = NumericCast
)
```

Không nhầm với Bitcast.

---

# 78. String

```axiom
"hello"
```

MIR có semantic constant string.

Không cần biết UTF-8 bytes nằm section nào.

---

# 79. Comptime

Comptime đã chạy trước production MIR nếu expression được yêu cầu compile-time.

Do đó runtime MIR chỉ chứa:

```text
MaterializedComptimeValue
```

không chứa compiler execution.

---

# 80. GPU MIR

GPU function tạo MIR với:

```text
GpuInfo {
    execution_domain
    storage_domains
    address_spaces
    kernel_kind
}
```

Sau đó GPU legality verifier kiểm tra.

Core MIR vẫn giữ semantic ownership/capability model.

---

# 81. GPU launch

Host-side:

```axiom
kernel<<<grid, block>>>(...)
```

không phải Core syntax bắt buộc.

Library call có thể lower thành:

```text
GpuLaunch {
    kernel
    arguments
    grid
    completion
}
```

và effect:

```text
Async
Device
```

---

# 82. Capability instruction family

MIR cần semantic capability operations:

```text
MakeView
MakeMutView
CapabilitySplit
CapabilityJoin
CapabilityEnd
```

Không nhất thiết tất cả xuất hiện từ source.

Verifier có thể elaborate chúng.

---

# 83. Region metadata

Capability:

```text
CapabilityInfo {
    id: CapabilityId
    owner: Place
    region: RegionId
    access: READ | WRITE
    provenance: ProvenanceId
    lifetime: LifetimeRange
}
```

MIR không dùng raw addresses để biểu diễn region.

---

# 84. Ownership state

MIR verifier state:

```text
Uninit
Owned
Moved
PartiallyMoved
Dropped
```

theo Place tree.

---

# 85. MIR không được tự suy ra unsafe safety

Nếu MIR chứa:

```text
RawLoad
```

không có nghĩa verifier bỏ qua.

Nó phải kiểm tra:

```text
unsafe boundary
trusted precondition
pointer provenance
alignment
initialization
access validity
```

theo frozen unsafe model.

---

# 86. Cleanup CFG

Một function có:

```text
normal exit
early return
panic
unwind
```

thì MIR cần cleanup graph.

Ví dụ:

```text
BB1
 │
 ├── normal → BB2
 │
 ├── return → Cleanup1
 │
 └── panic  → Cleanup2
```

---

# 87. Unwind profile

Nếu profile:

```text
panic = abort
```

không cần unwind cleanup path cho panic.

Nếu:

```text
panic = unwind
```

MIR phải chứa unwind edges.

Điều này giúp binary không phải mang unwind machinery nếu không dùng.

---

# 88. Drop order

Default:

```text
reverse initialization order
```

MIR Drop elaboration phải preserve semantic ordering.

Physical field layout có thể reorder.

Drop order **không được phụ thuộc physical field order**.

---

# 89. MIR source mapping

Mỗi instruction quan trọng:

```text
InstructionId
SourceSpanId
ExpansionOrigin
```

để debugger có thể:

```text
source
 ↕
HIR
 ↕
MIR
 ↕
machine
```

---

# 90. MIR debug levels

Có thể build:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
```

nhưng semantic MIR trước optimization phải giữ source mapping.

---

# 91. MIR validation

Ngay sau lowering:

```text
validate_mir_structure()
```

check:

```text
all blocks valid
all terminators valid
all locals typed
all places typed
all operands typed
CFG valid
dominance assumptions valid
no instruction after terminator
```

---

# 92. MIR type invariant

Mỗi `Place` có một type duy nhất:

```text
type_of(place) = T
```

Mỗi RValue assignment:

```text
type_of(rvalue) == type_of(destination)
```

hoặc có explicit conversion.

---

# 93. MIR dominance

Trước SSA, MIR có thể là mutable place-based IR.

Sau này SSA conversion cần:

```text
dominators
dominance frontier
```

Nhưng Raw MIR không cần SSA.

---

# 94. Tại sao không SSA ngay?

Vì ownership semantics dễ biểu diễn hơn với:

```text
Place
Move
Drop
Capability
```

trước SSA.

Nếu SSA hóa quá sớm, compiler phải giải quyết ownership + memory semantics cùng lúc.

Axiom chọn:

```text
Semantic MIR
→ verification
→ SSA/OptIR
```

đơn giản và chắc chắn hơn.

---

# 95. MIR interpreter

`ax-mir` phải có khả năng chạy:

```text
Raw MIR
```

hoặc tốt hơn:

```text
Verified MIR
```

để làm semantic oracle.

---

# 96. Reference interpreter

`ax-ref` có thể chạy AST/HIR-level semantics.

So sánh:

```text
ax-ref
    vs
ax-mir
```

giúp phát hiện lỗi HIR→MIR.

---

# 97. MIR differential testing

Một chương trình:

```text
source
```

được chạy:

```text
reference interpreter
MIR interpreter
native -O0
native -O2
native -Osize
WASM
```

Kết quả observable phải tương đương.

---

# 98. MIR canonical form

Để dễ test/incremental/cache:

```text
canonical MIR
```

phải deterministic.

Không phụ thuộc:

- hash map iteration;
- thread scheduling;
- allocation address;
- random IDs.

---

# 99. MIR fingerprint

```text
MIRFingerprint =
    semantic function identity
    + signature
    + normalized blocks
    + normalized operations
    + referenced type fingerprints
```

Không bao gồm:

```text
machine register assignment
stack offsets
instruction scheduling
```

---

# 100. Boundary 225

Sau BOOTSTRAP-225:

```text
Typed HIR
    ↓
Raw MIR
```

phải đảm bảo:

```text
✔ Evaluation order explicit
✔ Control flow explicit
✔ Type information explicit
✔ Move/Copy explicit
✔ Call semantics explicit
✔ Pattern branching explicit
✔ Drop candidates explicit
✔ View/mut_view creation explicit
✔ Async suspension points explicit
✔ Atomic/volatile semantics explicit
✔ FFI boundaries explicit
✔ Allocation semantics explicit
✔ Unsafe operations explicit
✔ Source mapping preserved
✔ No backend-specific assumptions
```

---

# 101. Frozen invariants

```text
AMIR-20
Every production Typed HIR function has a deterministic MIR representation.

AMIR-21
MIR is target-independent semantic IR.

AMIR-22
MIR preserves source evaluation order.

AMIR-23
Every basic block has exactly one terminator.

AMIR-24
Every MIR Place has a statically known semantic type.

AMIR-25
Move and Copy are distinct MIR operations.

AMIR-26
Copy semantics do not imply a physical memory copy.

AMIR-27
Move semantics do not imply a physical memory copy.

AMIR-28
Ownership-relevant operations are explicit in MIR.

AMIR-29
Implicit programmer syntax sugar is resolved before final MIR.

AMIR-30
Method calls have resolved semantic dispatch before production MIR.

AMIR-31
Operator semantics are resolved before production MIR.

AMIR-32
Short-circuit operators are represented as control flow, not ordinary eager binary operations.

AMIR-33
Pattern matching is represented as explicit control flow.

AMIR-34
Bounds safety obligations remain represented until proven unnecessary.

AMIR-35
View creation produces explicit capability metadata.

AMIR-36
Mutable view creation produces an exclusive capability obligation.

AMIR-37
Raw pointer operations remain explicitly unsafe in MIR.

AMIR-38
Pointer provenance is never reconstructed solely from integer values.

AMIR-39
Cast and bitcast remain distinct semantic operations.

AMIR-40
Atomic operations preserve atomic ordering semantics.

AMIR-41
Volatile operations are distinct from ordinary memory operations.

AMIR-42
Foreign calls carry an explicit FFI contract.

AMIR-43
External effects are not treated as pure without proof.

AMIR-44
Allocation is represented semantically and is not tied to malloc/free.

AMIR-45
Physical storage location is not encoded by ordinary MIR Place identity.

AMIR-46
Drop elaboration preserves deterministic destruction order.

AMIR-47
Partial moves remain field-sensitive where the type permits them.

AMIR-48
Custom Drop restrictions are preserved into MIR verification.

AMIR-49
Early exits preserve required cleanup semantics.

AMIR-50
Panic and unwind behavior are explicit according to the selected profile.

AMIR-51
Async suspension points are explicit and uniquely identified.

AMIR-52
Only values live across suspension become required future state.

AMIR-53
GPU execution/storage domains remain explicit.

AMIR-54
Comptime execution is not implicitly embedded in runtime MIR.

AMIR-55
MIR has deterministic source mappings.

AMIR-56
Raw MIR must structurally validate before ownership verification.

AMIR-57
MIR is executable by the MIR interpreter without native backend assumptions.

AMIR-58
Optimization cannot be required for MIR semantic correctness.

AMIR-59
MIR semantics are independent of optimization level.

AMIR-60
MIR fingerprints are deterministic.

AMIR-61
MIR is the semantic source of truth for subsequent compiler stages.

AMIR-62
No backend may reinterpret source semantics independently of MIR.

AMIR-63
Verified MIR is the only MIR form eligible for semantic optimization.

AMIR-64
MIR lowering must preserve observable behavior of the Typed HIR program.

AMIR-65
HIR→MIR translation is a compiler correctness boundary.
```

---

# 102. Implementation blueprint

Repository nên có:

```text
compiler/
├── hir/
├── mir/
│   ├── model/
│   │   ├── function
│   │   ├── block
│   │   ├── place
│   │   ├── operand
│   │   ├── rvalue
│   │   ├── statement
│   │   ├── terminator
│   │   └── constant
│   │
│   ├── lower/
│   │   ├── expression
│   │   ├── control_flow
│   │   ├── pattern
│   │   ├── call
│   │   ├── ownership
│   │   ├── capability
│   │   ├── async
│   │   └── cleanup
│   │
│   ├── validate/
│   ├── pretty/
│   ├── fingerprint/
│   └── interpreter/
│
├── verify/
├── opt/
└── codegen/
```

---

# 103. Thứ tự implementation thực tế

Không nên làm toàn bộ MIR một lần.

### Slice 1 — Arithmetic

```text
let
constant
binary op
return
```

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

→ MIR → interpreter → native.

---

### Slice 2 — Control flow

```text
if
while
loop
break
continue
```

---

### Slice 3 — Struct

```text
struct
field access
field assignment
construction
```

---

### Slice 4 — Ownership

```text
Move
Copy
Drop
early return
partial move
```

---

### Slice 5 — Capability

```text
view
mut_view
slice
index
```

---

### Slice 6 — Enum

```text
Option
Result
match
?
```

---

### Slice 7 — Generic/Trait

```text
generic
trait
method dispatch
operator
associated type
```

---

### Slice 8 — Closure

```text
capture
closure call
capture ownership
```

---

### Slice 9 — Async

```text
Future
await
state machine
```

---

### Slice 10 — System

```text
raw pointer
atomic
volatile
FFI
allocation
```

---

# 104. Gate trước Ownership Verifier

Compiler **không được** chuyển sang production ownership verification nếu MIR chưa pass:

```text
MIR structural validation
type validation
CFG validation
evaluation-order validation
dispatch validation
```

---

# 105. Gate trước Optimization

Chỉ:

```text
Verified MIR
```

mới được:

```text
SSA
MemorySSA
AliasInfo
EffectInfo
EscapeInfo
```

Điều này giữ đúng nguyên tắc đã đóng băng trước đó:

> **Optimizer không phải nơi phát hiện semantic invalidity.**

---

# 106. Gate trước Native Backend

Native backend chỉ nhận:

```text
Verified + Optimized + ABI-lowered representation
```

không nhận Raw MIR.

---

# 107. Milestone đặc biệt: “First Axiom Executable”

Đây là milestone rất đáng đặt.

Không cần chờ:

- ownership hoàn chỉnh;
- async;
- GPU;
- GUI;
- networking;
- self-hosting.

Chỉ cần:

```axiom
fn main() -> i32 {
    let a = 40
    let b = 2
    a + b
}
```

Compiler có thể:

```text
Source
 ↓
Lexer
 ↓
Parser
 ↓
AST
 ↓
Resolver
 ↓
TypeChecker
 ↓
HIR
 ↓
MIR
 ↓
MIR Interpreter
 ↓
42
```

Sau đó:

```text
MIR
 ↓
very simple backend
 ↓
native executable
 ↓
exit code 42
```

**Đây là vertical slice đầu tiên của Axiom.**

Không nên xây 50 subsystem rồi mới thử chạy chương trình đầu tiên.

---

# 108. Kiến trúc tổng thể sau 225

Axiom lúc này có cấu trúc cực kỳ rõ:

```text
                    ┌──────────────┐
                    │ Source       │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │ Typed HIR    │
                    └──────┬───────┘
                           ↓
                 ┌─────────────────────┐
                 │ Semantic MIR        │
                 │                     │
                 │ CFG                 │
                 │ Place               │
                 │ Move/Copy           │
                 │ Call                │
                 │ Drop                │
                 │ Capability          │
                 │ Async               │
                 │ Effects             │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ Verification       │
                 │                     │
                 │ Ownership           │
                 │ Capability          │
                 │ Effects             │
                 │ Concurrency         │
                 │ Async               │
                 │ GPU                 │
                 │ FFI                 │
                 └──────────┬──────────┘
                            ↓
                    ┌──────────────┐
                    │ Verified MIR │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │ OptIR        │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │ ABI MIR      │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │ Axiom LIR    │
                    └──────┬───────┘
                           ↓
                    Native Backend
```

Đây là một kiến trúc rất phù hợp với mục tiêu ban đầu của Axiom: **ngôn ngữ phía trên đơn giản, nhưng compiler phía dưới đủ thông minh để tự chứng minh ownership, aliasing, lifetime, allocation và tối ưu hóa mà không bắt programmer viết hàng loạt annotation.**

---

## BOOTSTRAP-226 — OWNERSHIP / INITIALIZATION / DROP VERIFIER

Bước tiếp theo sẽ khóa **“bộ não an toàn bộ nhớ”** của Axiom.

Nó sẽ đi sâu hơn 225 rất nhiều, đặc biệt vào:

```text
Place Tree
Definite Initialization
Move Paths
Partial Move
Copy
Clone
Drop
Drop Flags
Cleanup CFG
Early Return
Panic/Unwind
Loop Fixed Point
Branch Join
Maybe-Uninitialized
Conditional Initialization
Field-sensitive Ownership
Destructuring
Pattern Binding
Closure Capture
Async State
Capability Dependencies
Returned Ownership
Impossible Paths
Verifier State Lattice
```

Đây là nơi Axiom thực sự biến triết lý:

> **“Không có borrow checker syntax, nhưng compiler vẫn tự bảo đảm memory safety.”**

thành một **thuật toán compiler có thể implement được**, thay vì chỉ là một ý tưởng kiến trúc.