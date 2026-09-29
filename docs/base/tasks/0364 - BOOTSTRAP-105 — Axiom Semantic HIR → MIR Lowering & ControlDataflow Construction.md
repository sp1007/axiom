# BOOTSTRAP-105 — Axiom Semantic HIR → MIR Lowering & Control/Dataflow Construction
**FROZEN / COMPLETED**

Đây là bước chuyển từ **“compiler đã hiểu chương trình”** sang **“compiler có một biểu diễn đủ chính xác để kiểm chứng và tối ưu chương trình”**.

Mục tiêu của MIR Axiom:

> **MIR phải đủ thấp để ownership, capability, Drop, async, concurrency và control-flow có thể kiểm chứng; nhưng chưa được phụ thuộc vào CPU, ABI hay machine instruction.**

---

# 1. Vị trí của MIR

Pipeline sau khi hoàn thành 105:

```text
Source
  ↓
AST
  ↓
HIR
  ↓
Typed HIR
  ↓
Semantic Elaboration
  ↓
MIR
  ↓
Verification
  ↓
Semantic Optimization
  ↓
ABI MIR
  ↓
Axiom LIR
  ↓
Machine IR
```

MIR là **semantic execution IR**, không phải machine IR.

---

# 2. MIR phải biểu diễn điều gì?

MIR phải biểu diễn rõ:

```text
value
ownership
move/copy
place
read/write
capability
control flow
call
return
drop
allocation
panic
atomic
synchronization
suspension
FFI
GPU execution
```

Nhưng không biểu diễn:

```text
x86 register
ARM register
stack frame layout
calling convention cụ thể
instruction encoding
physical address
```

---

# 3. Một MIR instruction không được làm mờ semantic

Không nên có instruction kiểu:

```text
MAGIC_CALL
```

mà compiler phải đoán bên trong nó làm gì.

Mỗi operation phải có effect rõ ràng.

Ví dụ:

```text
CALL
LOAD
STORE
MOVE
COPY
DROP
ALLOC
DEALLOC
ATOMIC_LOAD
ATOMIC_STORE
...
```

---

# 4. MIR là typed

Mỗi operand/place/value trong MIR đều có `TypeId`.

Ví dụ:

```text
%1 : i32
%2 : view<i32>
%3 : Buffer
```

MIR không cần type inference lần nữa.

---

# 5. MIR không dùng source-level syntax

Ví dụ:

```axiom
a.foo(x)?
```

không còn là một node syntax duy nhất.

Sau elaboration có thể thành:

```text
%a = ...
%x = ...

%r = CALL FunctionId#42(%a, %x)

SWITCH_RESULT %r
    Ok → ...
    Err → RETURN ...
```

---

# 6. Basic Block

MIR sử dụng CFG:

```text
Function
 ├── BasicBlock 0
 ├── BasicBlock 1
 ├── BasicBlock 2
 └── BasicBlock 3
```

Mỗi block:

```text
Block:
    statements*
    terminator
```

Một block chỉ có **một terminator**.

---

# 7. Terminator

Các terminator Core:

```text
Goto
Branch
Switch
Return
Unreachable
Call
Panic
Suspend
```

Có thể có:

```text
Invoke
```

nếu unwind profile được bật.

---

# 8. `Call` là terminator hay instruction?

Axiom nên biểu diễn call theo hai phần semantic:

```text
Call instruction
```

và continuation:

```text
Call {
    callee
    args
    destination
    normal_target
    unwind_target?
}
```

Lý do:

Call có thể:

- return bình thường
- panic
- unwind
- foreign failure

Do đó CFG phải nhìn thấy các cạnh này.

---

# 9. Ví dụ MIR đơn giản

Source:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

MIR:

```text
bb0:
    %0 = Copy(a)
    %1 = Copy(b)
    %2 = Add(%0, %1)
    Return(%2)
```

Không cần:

```text
load register
mov eax
add eax
ret
```

vì đó là backend.

---

# 10. `Place`

Một trong những abstraction quan trọng nhất:

```text
Place
```

đại diện cho **vị trí có thể đọc/ghi**.

Ví dụ:

```text
x
x.field
x.field.subfield
array[i]
buffer[index]
```

Conceptually:

```text
Place {
    base: LocalId
    projections: Projection*
}
```

---

# 11. Projection

Projection có thể gồm:

```text
Field(FieldId)
Index(LocalId)
Deref
Downcast(VariantId)
Slice
```

Ví dụ:

```axiom
particle.position.x
```

thành:

```text
Place(
    particle
    → Field(position)
    → Field(x)
)
```

---

# 12. Không dùng pointer làm abstraction chính

Đây là điểm quan trọng đối với triết lý Axiom.

MIR không nên biến mọi thứ thành:

```text
pointer + offset
```

ngay từ đầu.

Thay vào đó:

```text
Place
```

giữ semantic identity.

Sau này backend mới quyết định:

```text
register
stack offset
address
vector lane
memory
```

---

# 13. Operand

Operand cơ bản:

```text
Copy(Place)
Move(Place)
Constant(ConstantId)
```

Ví dụ:

```text
%1 = Copy(x)
%2 = Move(buffer)
%3 = Constant(42)
```

---

# 14. Copy

```text
Copy(x)
```

yêu cầu:

```text
x : Copy
```

và **không thay đổi ownership state của x**.

---

# 15. Move

```text
Move(x)
```

là semantic ownership transition:

```text
Owned(x)
    ↓
Moved(x)
```

Không có nghĩa:

```text
memcpy
```

hay:

```text
physical relocation
```

---

# 16. Assignment

MIR:

```text
Assign(
    destination: Place,
    rvalue: RValue
)
```

Ví dụ:

```text
x = y
```

nếu `y` non-Copy:

```text
Assign(x, Move(y))
```

---

# 17. RValue

Các nhóm chính:

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
AddressOf
FunctionValue
Closure
```

Có thể mở rộng sau.

---

# 18. Aggregate

Struct:

```axiom
Point {
    x: 10,
    y: 20
}
```

MIR conceptually:

```text
%p = Aggregate Point {
    x = 10,
    y = 20
}
```

Ownership của từng field được theo dõi riêng.

---

# 19. Partial move

Ví dụ:

```axiom
let p = make_particle();
let x = p.position;
```

Nếu `Particle` cho phép partial move:

```text
p.position → Moved
p.velocity → Owned
```

Compiler vẫn có thể drop `velocity`.

---

# 20. Custom Drop

Nếu `Particle` có user-defined Drop:

```text
partial move
```

bị hạn chế theo frozen ownership rules.

Lý do là compiler phải đảm bảo Drop invariant của toàn object.

---

# 21. `StorageLive` / `StorageDead`

MIR có semantic storage lifetime:

```text
StorageLive(x)
...
StorageDead(x)
```

Nhưng đây **không phải**:

```text
malloc
free
```

Nó biểu diễn:

> khoảng thời gian local tồn tại về mặt semantic.

Optimizer có thể thay đổi physical storage.

---

# 22. Drop

```text
Drop(place)
```

có nghĩa:

> thực hiện ownership cleanup cần thiết tại thời điểm này.

Không đảm bảo:

```text
free(memory)
```

---

# 23. Drop elaboration

Source:

```axiom
fn f() {
    let a = A();
    let b = B();

    work();
}
```

MIR conceptually:

```text
bb0:
    StorageLive(a)
    a = A()

    StorageLive(b)
    b = B()

    Call(work)

    Drop(b)
    Drop(a)

    StorageDead(b)
    StorageDead(a)

    Return
```

---

# 24. Early return

```axiom
fn f() {
    let a = A();

    if condition {
        return;
    }

    use(a);
}
```

Compiler phải tạo cleanup path:

```text
bb_return:
    Drop(a)
    Return
```

Không để resource leak chỉ vì control-flow branch.

---

# 25. `match`

Source:

```axiom
match x {
    A => f(),
    B(v) => g(v),
}
```

MIR không giữ nguyên `match`.

Nó thành CFG/decision tree:

```text
bb0:
    SwitchVariant(x)
       A → bb1
       B → bb2

bb1:
    Call(f)
    Goto(bb3)

bb2:
    %v = ...
    Call(g, %v)
    Goto(bb3)

bb3:
    ...
```

---

# 26. Pattern ownership

Pattern matching không chỉ kiểm tra variant.

Ví dụ:

```axiom
match value {
    Some(x) => use(x),
    None => ...
}
```

`x` có thể là:

```text
Move
Copy
view
```

tùy semantics/type.

MIR phải thể hiện rõ lựa chọn đó.

---

# 27. `if`

Source:

```axiom
if condition {
    a()
} else {
    b()
}
```

MIR:

```text
bb0:
    Branch(condition, bb1, bb2)

bb1:
    Call(a)
    Goto(bb3)

bb2:
    Call(b)
    Goto(bb3)

bb3:
    ...
```

---

# 28. `loop`

```axiom
loop {
    work();
}
```

CFG:

```text
bb_loop:
    Call(work)
    Goto(bb_loop)
```

---

# 29. `break value`

Source:

```axiom
let x = loop {
    if done {
        break value;
    }
};
```

MIR dùng loop exit block:

```text
bb_loop:
    ...
    Branch(done, bb_exit, bb_loop)

bb_exit:
    %x = ...
```

---

# 30. `for`

`for` đã được HIR canonicalize thành iterator semantics.

MIR chỉ còn logic tương đương:

```text
iterator creation
loop
next()
match Option
body
```

Optimizer sau đó có thể specialize iterator.

---

# 31. `?`

`?` phải biến mất trước MIR canonicalization hoàn tất.

Ví dụ:

```axiom
let x = foo()?;
```

thành:

```text
%r = Call(foo)

SwitchResult(%r):
    Ok(v)  → continue
    Err(e) → cleanup + Return(Err(e))
```

---

# 32. `view`

Source:

```axiom
sum(data)
```

nếu `sum` yêu cầu:

```text
view<i32>
```

MIR:

```text
%v = MakeView(data)
Call(sum, %v)
```

Capability metadata:

```text
owner
region
READ
lifetime
```

được gắn với `%v`.

---

# 33. `mut_view`

```text
%v = MakeMutView(data)
Call(sort, %v)
```

Verifier kiểm tra:

```text
WRITE capability
exclusive
region valid
owner alive
```

---

# 34. Capability không nhất thiết trở thành runtime object

Đây là điểm rất quan trọng.

MIR có:

```text
CapabilityId
```

nhưng backend có thể erase toàn bộ capability metadata sau verification.

Nếu ABI yêu cầu:

```text
pointer + length
```

thì chỉ representation cần thiết còn lại.

Nếu compiler biết length compile-time:

```text
pointer
```

có thể đủ.

---

# 35. Capability lifetime

MIR phải biểu diễn:

```text
CreateCapability
UseCapability
EndCapability
```

nhưng `EndCapability` chủ yếu là semantic marker cho verifier.

Không nhất thiết có machine instruction.

---

# 36. Relocation

MIR phải cho verifier biết khi nào storage có thể relocate.

Ví dụ:

```text
Vec::push()
```

có thể realloc.

Nếu:

```text
view(data)
```

đang live:

```text
relocation forbidden
```

Hoặc API phải bảo đảm operation không relocate.

---

# 37. Allocation

MIR:

```text
ALLOC
DEALLOC
```

là **semantic storage operations**.

Không:

```text
malloc()
free()
```

---

# 38. Allocation metadata

Ví dụ:

```text
Alloc {
    type
    size
    align
    storage_domain
    allocator
    ownership
}
```

`allocator` có thể là semantic allocator identity.

Không bắt buộc là libc malloc.

---

# 39. Allocation elimination

MIR vẫn có:

```text
ALLOC
```

sau semantic elaboration.

Optimizer có thể chứng minh:

```text
does not escape
address not observed
lifetime local
```

→ loại bỏ allocation.

Do đó semantic correctness không phụ thuộc optimizer.

---

# 40. Function call

MIR call giữ:

```text
FunctionId
args
result
effects
continuations
```

Không giữ ABI register mapping.

---

# 41. Dynamic dispatch

Nếu source:

```axiom
x.draw()
```

với:

```text
dyn Drawable
```

MIR có thể:

```text
DynCall {
    receiver
    TraitId
    MethodId
    metadata
}
```

Dynamic dispatch là explicit semantic operation.

---

# 42. Closure lowering

Source:

```axiom
let f = |x| x + captured;
```

HIR đã xác định capture.

MIR tạo:

```text
ClosureEnv {
    captured
}
```

và:

```text
Closure {
    code = FunctionId#...
    env = ...
}
```

Không yêu cầu heap.

---

# 43. Closure optimization

Optimizer có thể biến:

```text
closure env
```

thành:

```text
SSA values
```

hoặc inline toàn bộ closure.

---

# 44. Async lowering

`async fn` cuối cùng phải trở thành state machine.

Ví dụ conceptually:

```text
FutureState {
    state
    live_value_1
    live_value_2
}
```

MIR:

```text
state = 0

switch state:
    0 → begin
    1 → resume_after_await_1
    2 → resume_after_await_2
```

---

# 45. Suspension

MIR có:

```text
Suspend(SuspensionPointId)
```

Mỗi suspension point có ID ổn định.

Verifier dùng nó để kiểm tra:

```text
values live across await
capabilities
guards
Send
storage validity
```

---

# 46. Chỉ state cần thiết mới sống qua await

Ví dụ:

```axiom
async fn f() {
    let a = huge();
    let b = small();

    await io();

    use(b);
}
```

Compiler không cần giữ `a` trong Future nếu `a` không live sau await.

Đây là nền tảng cho:

```text
StateFieldLiveness
StateFieldElision
```

sau này.

---

# 47. Await không phải thread switch

MIR:

```text
Suspend
```

không có nghĩa:

```text
spawn thread
```

hay:

```text
lock
```

hay:

```text
memory fence
```

Đúng với nguyên tắc:

> **Async is control-flow abstraction, not thread.**

---

# 48. Panic

MIR phải có semantic panic edge.

```text
Panic {
    payload
    policy
}
```

Nếu panic abort:

```text
→ process termination
```

Nếu unwind:

```text
→ cleanup CFG
```

---

# 49. Unwind

Nếu compiler profile hỗ trợ unwind:

```text
Call
 ├── normal
 └── unwind
```

Unwind path phải chạy Drop đúng ownership state.

---

# 50. Atomic

MIR có operations riêng:

```text
AtomicLoad
AtomicStore
AtomicRmw
CompareExchange
Fence
```

kèm:

```text
Ordering
Scope
```

Không biến atomic thành ordinary Load/Store.

---

# 51. Volatile

Tương tự:

```text
VolatileLoad
VolatileStore
```

không được coi là atomic.

Và:

```text
volatile != synchronization
```

---

# 52. Synchronization

MIR cần semantic effects cho:

```text
MutexLock
MutexUnlock
ChannelSend
ChannelReceive
ThreadStart
ThreadJoin
SemaphoreAcquire
SemaphoreRelease
```

Một số có thể được library intrinsic/compiler recognized operation.

---

# 53. Không hard-code mọi synchronization primitive vào Core MIR

MIR cần biểu diễn **effect/ordering semantics**, nhưng không cần có instruction cho mọi thư viện.

Ví dụ một custom lock có thể lower thành:

```text
Atomic
```

hoặc:

```text
ForeignCall
```

nếu semantic contract rõ ràng.

---

# 54. FFI

MIR:

```text
ForeignCall {
    abi
    symbol
    args
    result
    effects
}
```

Verifier biết:

```text
foreign
unsafe boundary
aliasing conservative
may_read
may_write
may_panic
may_block
```

theo contract.

---

# 55. GPU

GPU operations được biểu diễn riêng:

```text
KernelLaunch
DeviceAlloc
DeviceFree
DeviceCopy
GpuWait
GpuAtomic
```

Execution domain:

```text
CPU
GPU
Device
```

được giữ trong semantic metadata.

---

# 56. CPU/GPU capability không tự xuyên qua

Không cho:

```text
CPU view
→ GPU view
```

mà không có semantic transfer/storage operation.

Ví dụ:

```text
Host Buffer
    ↓ DeviceCopy
Device Buffer
    ↓
DeviceView
```

---

# 57. MIR Effects

Mỗi operation có effect summary.

Ví dụ:

```text
Read
Write
Move
Drop
Allocate
Deallocate
Atomic
Volatile
IO
Panic
Synchronize
Foreign
Suspend
GPU
```

Điều này rất hữu ích cho optimizer.

---

# 58. Effect không đồng nghĩa effect system ở source

Axiom v0.1 **không cần bắt programmer viết**:

```text
fn foo() effects(Read, Write, IO)
```

Compiler tự suy ra effect.

MIR giữ effect metadata cho compiler.

---

# 59. Ownership state trên CFG

Verifier sẽ chạy:

```text
bb0
 ↓
bb1 ──→ bb3
 ↓
bb2 ──→ bb3
```

và merge ownership state.

Ví dụ:

```text
x = Owned
```

ở cả hai path → `Owned`.

Nhưng:

```text
path A: x = Moved
path B: x = Owned
```

merge phải xử lý rõ ràng, không được “đoán”.

---

# 60. Definite initialization

MIR phải cho phép verifier chứng minh:

```text
READ(x)
```

chỉ xảy ra sau:

```text
INIT(x)
```

Các trạng thái:

```text
UNINIT
INIT
MOVED
PARTIAL
DROPPED
```

được theo dõi.

---

# 61. Drop state

Verifier phải phân biệt:

```text
initialized
moved
partially moved
dropped
```

để không tạo:

```text
double drop
drop uninitialized
drop moved value
```

---

# 62. Phi values

MIR ban đầu có thể dùng:

```text
Block parameters
```

thay vì explicit `Phi`.

Ví dụ:

```text
bb3(x)
```

từ:

```text
bb1 → bb3(v1)
bb2 → bb3(v2)
```

Cách này thuận lợi cho CFG và ownership reasoning.

Sau đó SSA construction có thể biến thành phi nodes trong OptIR.

**Khuyến nghị:** MIR **không cần SSA**.

---

# 63. Tại sao MIR không SSA?

Vì semantic verification dễ hơn nếu MIR giữ:

```text
Place
Assign
Move
Drop
Capability
```

SSA là representation tối ưu hóa.

Do đó:

```text
MIR = semantic mutable place-based IR
OptIR = SSA-based optimization IR
```

Đây là phân chia rất sạch.

---

# 64. MIR → OptIR

Sau verification:

```text
Verified MIR
      ↓
SSA construction
      ↓
MemorySSA
      ↓
AliasInfo
      ↓
EffectInfo
      ↓
RangeInfo
      ↓
EscapeInfo
      ↓
OptIR
```

Điều này khớp hoàn toàn với BOOTSTRAP-056 đã frozen.

---

# 65. MIR source provenance

Mỗi MIR instruction nên có:

```text
SourceSpanId
OriginNodeId
```

Ví dụ:

```text
InstructionId #182
Origin = HIR expression #42
Source = file.ax:128:14
```

Nhờ vậy debugger/AI có thể hỏi:

```text
instruction này từ đâu?
```

---

# 66. MIR deterministic

Cùng:

```text
Typed HIR
```

phải sinh ra MIR semantic tương đương.

Không phụ thuộc:

```text
-O0
-O2
CPU register pressure
```

---

# 67. MIR không được tối ưu quá sớm

Không nên ngay tại HIR→MIR:

```text
constant folding
dead code elimination
register allocation
loop vectorization
```

trừ những canonicalization bắt buộc để tạo semantic MIR.

Lý do:

> giữ MIR dễ kiểm chứng.

---

# 68. Canonicalization bắt buộc

Có thể thực hiện:

```text
method → function call
for → iterator CFG
? → Result CFG
if let → match
destructuring → projections
closure → closure env
async → suspension/state representation
```

Nhưng không làm optimization-dependent transformations.

---

# 69. Semantic boundaries

Sau BOOTSTRAP-105:

```text
HIR
```

là source-oriented.

```text
MIR
```

là execution-oriented.

```text
OptIR
```

là optimization-oriented.

```text
LIR
```

là machine-lowering-oriented.

Mỗi tầng có một trách nhiệm riêng.

---

# 70. MIR data model đề xuất

```text
MirFunction {
    function_id
    signature
    locals
    blocks
    capabilities
    effects
    async_info?
    gpu_info?
    ffi_info?
    source_map
}
```

```text
MirBlock {
    block_id
    parameters
    statements
    terminator
}
```

```text
MirStatement {
    StorageLive
    StorageDead
    Assign
    Drop
    CapabilityBegin
    CapabilityEnd
    ...
}
```

```text
MirOperand {
    Copy
    Move
    Constant
}
```

```text
MirPlace {
    Local
    Projection*
}
```

---

# 71. MIR verification boundary

MIR được xem là:

```text
Unverified MIR
```

ngay sau lowering.

Sau BOOTSTRAP-055 verifier:

```text
Verified MIR
```

với các invariant:

```text
type valid
ownership valid
initialization valid
drop valid
capability valid
alias valid
Send/Share valid
async valid
GPU valid
FFI valid
```

Chỉ **Verified MIR** mới được phép đưa vào optimizer.

---

# 72. Đây là một security boundary

Không được:

```text
HIR
 ↓
MIR
 ↓
optimizer
```

mà bỏ verifier.

Vì optimizer có thể giả định:

```text
no use-after-free
no invalid capability
no double drop
no safe data race
```

Nếu MIR chưa được verify, những giả định đó không hợp lệ.

---

# 73. MIR invariants — `AMIR-20..`

### `AMIR-20`
Every MIR value has a resolved TypeId.

### `AMIR-21`
Every MIR place has a resolved semantic type.

### `AMIR-22`
Every basic block has exactly one terminator.

### `AMIR-23`
Every CFG edge is explicit.

### `AMIR-24`
MIR does not depend on target machine registers.

### `AMIR-25`
MIR does not encode target-specific ABI details.

### `AMIR-26`
MIR ownership operations are explicit.

### `AMIR-27`
Move is an ownership transition, not a physical-copy instruction.

### `AMIR-28`
Copy requires semantic Copy capability/property.

### `AMIR-29`
Clone is never implicitly inserted by MIR lowering.

### `AMIR-30`
Place represents semantic storage locations independently of physical addresses.

### `AMIR-31`
Projection preserves semantic field/index/variant identity.

### `AMIR-32`
StorageLive/StorageDead are semantic lifetime markers, not mandatory allocator operations.

### `AMIR-33`
Drop is explicit after drop elaboration.

### `AMIR-34`
Every normal control-flow exit executes required cleanup.

### `AMIR-35`
Every panic/unwind path executes required cleanup according to the selected panic profile.

### `AMIR-36`
Uninitialized values cannot be read.

### `AMIR-37`
Moved values cannot be read or moved again unless legally reinitialized.

### `AMIR-38`
Double Drop is invalid.

### `AMIR-39`
Partial-move semantics follow the type's Drop contract.

### `AMIR-40`
Capability creation is explicit in semantic MIR.

### `AMIR-41`
Capability validity is independently verifiable.

### `AMIR-42`
A live capability prevents invalid owner destruction or relocation.

### `AMIR-43`
Unknown aliasing is never converted to proven disjointness.

### `AMIR-44`
`view` and `mut_view` retain their semantic access modes until verification completes.

### `AMIR-45`
After verification, capability metadata may be erased when not required by ABI/runtime semantics.

### `AMIR-46`
Allocation operations represent semantic storage acquisition, not a mandatory allocator implementation.

### `AMIR-47`
MIR allocation does not imply heap allocation.

### `AMIR-48`
Function return does not imply heap allocation.

### `AMIR-49`
Call effects are represented explicitly.

### `AMIR-50`
Foreign calls retain their ABI and effect contracts.

### `AMIR-51`
Atomic operations remain distinct from ordinary memory operations.

### `AMIR-52`
Volatile operations remain distinct from atomic operations.

### `AMIR-53`
Synchronization semantics are preserved through lowering.

### `AMIR-54`
Await/suspension is explicit and is not implicitly a thread switch or memory fence.

### `AMIR-55`
Values live across suspension are explicitly represented in async state.

### `AMIR-56`
Async state does not contain values that are proven dead before suspension.

### `AMIR-57`
GPU execution/storage domains remain explicit until target-specific lowering.

### `AMIR-58`
Host/device transfers are explicit semantic operations.

### `AMIR-59`
Generated/comptime-produced code enters MIR through the same verification pipeline.

### `AMIR-60`
MIR lowering is deterministic.

### `AMIR-61`
MIR semantic meaning is independent of optimization level.

### `AMIR-62`
MIR semantic meaning is independent of physical storage strategy.

### `AMIR-63`
MIR does not perform register allocation.

### `AMIR-64`
MIR does not perform instruction selection.

### `AMIR-65`
MIR retains source provenance for semantic diagnostics and debugging.

### `AMIR-66`
Unverified MIR cannot enter optimization.

### `AMIR-67`
Verified MIR is the semantic source for later optimization.

### `AMIR-68`
MIR transformations must preserve observable semantics.

### `AMIR-69`
MIR does not introduce hidden runtime services absent from source semantics or explicit library contracts.

### `AMIR-70`
The compiler may erase semantic constructs only after their required verification obligations are discharged.

---

# 74. Kiến trúc sau 105

Axiom hiện đã có một pipeline rất rõ:

```text
                    SOURCE
                       │
                       ▼
              ┌─────────────────┐
              │     FRONTEND    │
              │ Lexer / Parser  │
              │ Resolution      │
              └────────┬────────┘
                       ▼
                     HIR
                       │
                       ▼
              ┌─────────────────┐
              │ TYPE / SEMANTIC │
              │ inference       │
              │ trait solving   │
              │ ownership       │
              │ capability      │
              └────────┬────────┘
                       ▼
                FULLY TYPED HIR
                       │
                       ▼
              ┌─────────────────┐
              │      MIR        │
              │ semantic CFG    │
              │ places          │
              │ move/drop       │
              │ capability      │
              │ async/GPU/FFI   │
              └────────┬────────┘
                       ▼
                MIR VERIFICATION
                       │
                       ▼
                VERIFIED MIR
                       │
                       ▼
              ┌─────────────────┐
              │     OPT IR      │
              │ SSA / MemorySSA │
              │ alias / escape  │
              │ optimization    │
              └─────────────────┘
```

Đây là một architecture khá mạnh mà vẫn giữ được một nguyên tắc quan trọng của Axiom:

> **Source language không cần phơi bày sự phức tạp mà compiler có thể tự quản lý.**

---

# BOOTSTRAP-106 — Axiom Semantic Verification Engine

Bước tiếp theo nên khóa **Verifier**, vì bây giờ đã có MIR hoàn chỉnh nhưng chưa định nghĩa hết cách compiler chứng minh MIR an toàn trước khi cho optimizer sử dụng.

Đây sẽ là một trong những module quan trọng nhất của toàn bộ Axiom:

```text
MIR
 ↓
CFG construction
 ↓
Definite Initialization
 ↓
Ownership Dataflow
 ↓
Drop Verification
 ↓
Capability / Provenance Analysis
 ↓
Alias / Region Analysis
 ↓
Escape Analysis
 ↓
Send / Share Verification
 ↓
Async Suspension Verification
 ↓
Concurrency Verification
 ↓
GPU Legality
 ↓
FFI Safety
 ↓
Comptime Safety
 ↓
Verified MIR
```

Đặc biệt ở **BOOTSTRAP-106** cần khóa một câu hỏi lớn:

> **Làm thế nào để Axiom có được phần lớn lợi ích của Rust borrow checker — use-after-free, invalid aliasing, data race, lifetime safety — nhưng programmer gần như không phải viết borrow/lifetime annotation?**

Và đồng thời phải tránh biến compiler thành một hệ thống quá nặng khiến thời gian compile và trải nghiệm AI-agent trở nên tệ.