# BOOTSTRAP-139 — SSA, MemorySSA & Unified Dataflow Optimization IR

**Trạng thái: FROZEN / COMPLETED**

Đây là bước biến toàn bộ thông tin đã có thành một IR tối ưu hóa thực sự mạnh.

Mục tiêu:

> **MIR biểu diễn chương trình đúng về mặt semantics; OptIR biểu diễn chương trình theo cách thuận lợi nhất cho optimizer.**

Không nên cố biến MIR thành SSA ngay từ đầu, vì MIR còn phải thể hiện rõ ownership, Drop, capability, suspension, storage và control flow.

---

# 1. Kiến trúc

Pipeline chính thức:

```text
Typed HIR
    ↓
MIR
    ↓
Structural Verification
    ↓
Ownership / Init / Drop
    ↓
Capability
    ↓
Concurrency / Async / GPU / FFI
    ↓
Verified MIR
    ↓
AliasInfo
    ↓
EffectInfo
    ↓
EscapeInfo
    ↓
RangeInfo
    ↓
SSA Construction
    ↓
MemorySSA Construction
    ↓
OptIR
```

---

# 2. MIR và OptIR có vai trò khác nhau

### MIR

Là:

> **Semantic execution model**

Nó phải dễ kiểm chứng.

### OptIR

Là:

> **Optimization model**

Nó phải dễ:

- SSA;
- constant propagation;
- CSE/GVN;
- LICM;
- vectorization;
- loop optimization;
- memory optimization;
- scalar replacement.

---

# 3. Không được tối ưu trực tiếp trên MIR

Nguyên tắc:

```text
Verified MIR
     ↓
   lower
     ↓
   OptIR
```

Optimizer không được tự sửa semantic MIR rồi coi đó là semantics mới.

---

# 4. SSA

Mỗi SSA value chỉ có một definition:

```text id="a8s2v7"
%x1 = add %a, %b
%x2 = mul %x1, %c
```

Không có:

```text
%x = ...
%x = ...
```

---

# 5. Phi node

Ví dụ:

```ax id="k4m7p2"
if cond {
    x = 10;
} else {
    x = 20;
}

use(x);
```

OptIR:

```text id="r9q3x1"
bb1:
    branch cond → bb2, bb3

bb2:
    x1 = 10
    goto bb4

bb3:
    x2 = 20
    goto bb4

bb4:
    x3 = phi(x1, x2)
    use(x3)
```

---

# 6. Ownership không nằm trong SSA value

SSA:

```text id="v6p2n9"
%x1
```

không tự mang semantic:

```text
Owned
Moved
Drop
```

Ownership vẫn thuộc:

```text id="m8q4r1"
MIR / verification metadata
```

Đây là distinction quan trọng.

---

# 7. SSA value không phải ownership object

Ví dụ:

```ax id="f3q7m1"
let b = a;
```

nếu `a` move:

```text id="w5n8k2"
ownership(a) → ownership(b)
```

SSA construction không được biến nó thành semantic copy.

---

# 8. Copy

Nếu:

```ax id="s6m2p8"
let b = a;
```

và `a: Copy`:

```text id="r4x9n1"
%b = %a
```

SSA có thể reuse physical register.

Không cần memcpy.

---

# 9. Aggregate SSA

Struct:

```ax id="k7m3q8"
Point {
    x: f32,
    y: f32
}
```

có thể:

```text id="n2v6r4"
%px
%py
```

thay vì một memory object.

Đây là:

> **Scalar Replacement of Aggregates — SROA**

---

# 10. Field-sensitive SSA

Ví dụ:

```ax id="j4p8x2"
p.x += 1;
use(p.y);
```

optimizer có thể giữ:

```text id="c7m1q5"
px1 = px0 + 1
py1 = py0
```

mà không cần materialize toàn bộ `Point`.

---

# 11. Nhưng Drop phải được giữ

Nếu struct có Drop:

```text id="f8q2m5"
struct Resource {
    ...
    drop(...)
}
```

optimizer không thể đơn giản scalarize rồi quên destruction semantics.

Phải preserve:

```text id="r3n7k1"
Drop(Resource)
```

hoặc chứng minh destructor tương đương/trivial.

---

# 12. MemorySSA

SSA giải quyết:

```text id="m5q8x1"
register/data values
```

MemorySSA giải quyết:

```text id="p2r7k4"
memory state
```

Ví dụ:

```text id="v8n3m6"
store A
load A
store B
load A
```

MemorySSA biết load nào phụ thuộc store nào.

---

# 13. Memory versions

Ví dụ:

```text id="q6m2v9"
Memory0
   ↓ store A
Memory1
   ↓ store B
Memory2
```

Load có thể tham chiếu:

```text id="w4p8n1"
Load A @ Memory1
```

---

# 14. Không dùng một memory version cho toàn bộ memory nếu không cần

AliasInfo cho phép partition:

```text id="t3k7m2"
Memory
 ├── R1
 ├── R2
 └── R3
```

Nếu:

```text id="c9v5q1"
R1 NO_ALIAS R2
```

store R1 không cần invalidate load R2.

---

# 15. MemorySSA + AliasInfo

Đây là một trong những điểm quan trọng nhất:

```text id="m7x2q8"
MemorySSA
    +
AliasInfo
```

cho phép compiler trả lời:

> Store này có thực sự clobber load kia không?

---

# 16. Ví dụ

```ax id="p5k8r2"
a.x = 10;
print(b.y);
```

Nếu compiler chứng minh:

```text id="n3v6m1"
a.x DISJOINT b.y
```

thì:

```text id="z8q4x7"
store(a.x)
```

không clobber:

```text id="j2m9p5"
load(b.y)
```

---

# 17. UNKNOWN

Nếu:

```text id="h7r3q1"
Alias(a.x, b.y) = UNKNOWN
```

MemorySSA phải conservative.

Không được giả định:

```text id="b6m2v8"
NO_CLOBBER
```

---

# 18. MUST_ALIAS

Nếu:

```text id="c4p9n2"
R1 MUST_ALIAS R2
```

store vào R1 có thể xác định chính xác clobber load R2.

Điều này hỗ trợ:

- load forwarding;
- store-to-load forwarding;
- redundant load elimination.

---

# 19. Partial alias

Nếu:

```text id="x8q3m6"
R1 PARTIAL_ALIAS R2
```

compiler không thể coi chúng là hoàn toàn độc lập.

Nhưng có thể sử dụng field/range information để refine.

---

# 20. Load elimination

```ax id="g7m2q4"
let a = x.value;
let b = x.value;
```

nếu không có intervening write:

```text id="r5n8k1"
b = a
```

không cần load lần hai.

---

# 21. Write invalidation

```ax id="v4q9m2"
a = x.value;
x.value = 10;
b = x.value;
```

MemorySSA:

```text id="p8k3r7"
Load(x.value)
    ↓
Store(x.value)
    ↓
Load(x.value)
```

Hai load không thể merge.

---

# 22. Function calls

Unknown call:

```text id="n6m1q8"
foo()
```

có thể tạo:

```text id="q3v7r2"
MemoryClobber
```

Nhưng effect summary + alias analysis có thể thu hẹp.

Ví dụ:

```text id="f8k2m5"
foo writes R2
```

thì load từ R1 vẫn hợp lệ nếu:

```text id="r1q6n9"
R1 DISJOINT R2
```

---

# 23. Pure call

Nếu:

```text id="m5p9x2"
foo = PURE
```

và không có observable identity:

```text id="q7k3r8"
foo(x)
foo(x)
```

có thể CSE.

---

# 24. Read-only call

Nếu:

```text id="h2n8m4"
foo = READ(R)
```

thì nó không invalidate regions khác.

---

# 25. Atomic MemorySSA

Atomic:

```ax id="w3q7m1"
x.fetch_add(1, Relaxed)
```

không được biến thành ordinary:

```text id="p8r2n6"
load
add
store
```

Atomicity phải được giữ.

---

# 26. Atomic ordering

MemorySSA metadata:

```text id="m4v9q2"
AtomicOp {
    location
    ordering
    scope
}
```

Ordering:

```text id="x7n3k8"
Relaxed
Acquire
Release
AcqRel
SeqCst
```

---

# 27. Volatile MemorySSA

Volatile:

```text id="c5m8q1"
VolatileLoad
VolatileStore
```

là observable.

Không được DCE/CSE như ordinary load/store.

---

# 28. Compiler fence

Compiler fence tạo optimization barrier thích hợp.

Nhưng không nhất thiết là memory clobber giống CPU fence.

Do đó IR phải phân biệt:

```text id="a8q4m2"
CompilerBarrier
CpuFence
MemoryAccess
```

---

# 29. Global memory

Global:

```ax id="v2n7k5"
static mut counter: i32;
```

được biểu diễn trong MemorySSA như region có external visibility.

Unknown external call có thể clobber.

---

# 30. Thread-local memory

TLS có identity riêng:

```text id="p6m3q8"
TLSRegion
```

không được coi là ordinary global memory.

---

# 31. Heap memory

Heap allocation:

```text id="k9r4v1"
Allocation A
```

nếu NoEscape và unique:

```text id="t7m2q5"
MemorySSA region A
```

có thể scalarize/eliminate.

---

# 32. Allocation identity

Nếu allocation identity observable:

```text id="c3q8m6"
Allocation A ≠ Allocation B
```

optimizer phải giữ distinction.

---

# 33. Dead allocation

```ax id="w5n2p9"
let x = Box::new(42);
```

Nếu:

```text id="r7m4q1"
NoEscape
NoAddressObservation
NoIdentityObservation
TrivialDrop
```

toàn bộ allocation có thể bị eliminate.

---

# 34. Stack memory

Stack slots cũng có MemorySSA identity khi address-sensitive.

Nhưng nếu scalarizable:

```text id="j8q3m6"
stack slot → SSA
```

---

# 35. Memory-to-register promotion

Ví dụ:

```ax id="n4p7r2"
var x = 0;
x += 1;
x += 2;
return x;
```

có thể:

```text id="g6m2q8"
x0 = 0
x1 = x0 + 1
x2 = x1 + 2
return x2
```

Không cần stack memory.

---

# 36. Address escape ngăn promotion

Nếu:

```ax id="p3q8m1"
external(address_of(x))
```

thì stack slot có thể cần giữ.

MemorySSA phải preserve addressable memory.

---

# 37. Capability metadata

OptIR không nhất thiết phải giữ toàn bộ compiler-only capability objects.

Nhưng có thể giữ:

```text id="m7q2n5"
AliasClass
RegionId
ProvenanceId
```

nếu cần optimization.

---

# 38. Capability ≠ MemorySSA region

Một capability:

```text id="x4n8q2"
view<T>
```

là semantic access right.

MemorySSA region:

```text id="k6m3p9"
```

là optimizer memory identity.

Có thể map:

```text id="v1q7r4"
Capability Region
       ↓
Alias/Memory Region
```

nhưng không đồng nhất chúng.

---

# 39. SSA + capability

Khi capability chỉ tồn tại compiler-side:

```text id="a5r9m2"
view<T>
```

có thể erase khỏi generated machine code.

Nhưng alias information derived từ nó vẫn có thể tồn tại trong OptIR.

---

# 40. Move + SSA

Move:

```ax id="f2m7q4"
let b = a;
```

với non-Copy:

```text id="n8r3p1"
a → moved
b → owner
```

SSA:

```text id="q5m9x2"
%b = %a
```

Ownership state vẫn ghi:

```text id="w7k4n6"
a = MOVED
```

---

# 41. Partial move + SSA

```ax id="j3q8m5"
let y = x.field;
```

nếu field move:

```text id="p6n2r9"
x.field = MOVED
x.other = VALID
```

OptIR có thể scalarize:

```text id="r4m7q1"
x.field
x.other
```

nhưng Drop semantics vẫn phải giữ.

---

# 42. Phi và ownership

Một value có thể có nhiều ownership states trên các CFG paths.

Verifier phải resolve trước khi OptIR.

Ví dụ:

```text id="c8q3m5"
path A → Owned
path B → Owned
join → Owned
```

Nếu:

```text id="v2m7r9"
path A → Moved
path B → Owned
```

thì use sau join phải bị reject nếu không reinitialize.

OptIR không giải quyết lỗi này.

---

# 43. Drop + SSA

Drop flags có thể được biểu diễn tạm:

```text id="h5n8q2"
drop_flag
```

Nếu compiler chứng minh object luôn initialized:

```text id="r3m7p1"
drop_flag = constant true
```

có thể simplify.

Nếu partial move:

```text id="q8v2m6"
drop_flag(field)
```

có thể cần field-sensitive flags.

---

# 44. Async state

Future state machine được tạo trước hoặc trong lowering vào OptIR.

Mỗi state field có:

```text id="x7m4q2"
SSA value
Memory field
Liveness
```

Chỉ các values live across await trở thành persistent state.

---

# 45. Await boundary

`await` tạo control-flow split:

```text id="k5q8m3"
Ready
Pending
Resume
```

SSA phi/state reconstruction phải preserve.

Không được xem `await` như ordinary function call.

---

# 46. GPU OptIR

GPU có memory spaces:

```text id="n2r7v5"
Host
Device
Shared
Local
Private
Constant
```

MemorySSA phải phân biệt address spaces.

---

# 47. GPU shared memory

Hai threads có thể access:

```text id="p4m8q2"
SharedRegion
```

Alias analysis và synchronization semantics cùng tham gia.

Không được coi:

```text id="r6n3v9"
shared write
```

là ordinary private write.

---

# 48. Vector values

SSA phải hỗ trợ:

```text id="m7q2x4"
<VectorType>
```

ví dụ:

```text id="c8n5r1"
<4 x f32>
```

Auto-vectorization có thể tạo vector SSA.

---

# 49. Predicates

SIMD/GPU có thể cần:

```text id="v3m9q6"
Predicate SSA
```

để biểu diễn masked operations.

---

# 50. Memory dependencies

OptIR instruction có:

```text id="k2r7m4"
DataOperands
MemoryOperands
ControlDependencies
Effect
```

Optimizer phải tôn trọng cả ba.

---

# 51. Effect tokens

Không nên biến mọi side effect thành một global `effect token`.

Ví dụ:

```text id="p8m3q5"
IO
Memory
Atomic
Volatile
```

có dependency domain khác nhau.

Do đó OptIR dùng explicit effect/memory classes.

---

# 52. IO ordering

Hai:

```text id="r5q9n2"
print("A")
print("B")
```

không được reorder thành:

```text id="m7x3p8"
B
A
```

chỉ vì data dependencies không tồn tại.

IO effect tạo ordering requirement.

---

# 53. Time

```ax id="v4n8q2"
a = now();
b = now();
```

Không được CSE mặc định:

```text id="j6m2r9"
b = a
```

vì TIME effect.

---

# 54. Random

Tương tự:

```ax id="c3q7m1"
a = random();
b = random();
```

không thể merge nếu random semantics observable.

---

# 55. External state

Environment/process/device state tạo MemorySSA-like external effect domains.

Không phải tất cả external state đều biểu diễn như ordinary memory.

---

# 56. Dominance

SSA construction dùng CFG dominance:

```text id="x7q2m4"
DominatorTree
```

để đặt phi nodes.

OptIR giữ:

```text id="n5r8p1"
DominatorTree
PostDominatorTree
LoopInfo
```

---

# 57. Dominance và Drop

Cleanup blocks có thể có:

```text id="m4q9v2"
Drop
```

và SSA construction phải tránh tạo use sau semantic lifetime.

---

# 58. Loop SSA

Ví dụ:

```ax id="k8m3p5"
var i = 0;
while i < n {
    use(i);
    i += 1;
}
```

SSA:

```text id="q2r7n6"
i0 = 0

loop:
    i1 = phi(i0, i2)
    use(i1)
    i2 = i1 + 1
    branch ...
```

---

# 59. RangeInfo

SSA value có thể có:

```text id="v6m2q9"
RangeInfo(i1) = [0,n]
```

giúp:

- bounds check elimination;
- loop optimization;
- alias range reasoning;
- vectorization.

---

# 60. Alias classes

OptIR có thể assign:

```text id="p4q8m1"
AliasClass 17
AliasClass 21
```

Hai memory accesses cùng alias class chưa chắc MUST_ALIAS, nhưng compiler có thể giảm search space.

---

# 61. Memory clobber

Unknown call:

```text id="r7m3q5"
CALL foo
```

có:

```text id="k2n8v4"
MemoryClobber(AllReachable)
```

Nếu summary chính xác:

```text id="x6q1m9"
MemoryClobber(R2)
```

---

# 62. MemoryPhi

Khi control flow merge:

```text id="m8r4q2"
Memory1 → branch A
Memory2 → branch B
```

có:

```text id="p3n7v6"
MemoryPhi(Memory1, Memory2)
```

Load sau merge tham chiếu đúng memory state.

---

# 63. MemorySSA không phải runtime memory

`MemorySSA` chỉ là compiler representation.

Không tạo runtime metadata.

---

# 64. SSA không yêu cầu heap

SSA có thể đại diện:

```text id="q5m8r1"
register
stack
heap
device
global
```

nó không quyết định storage.

---

# 65. OptIR representation

Đề xuất:

```text id="r2v7m4"
OptFunction {
    FunctionId
    Blocks
    SSAValues
    MemorySSA
    AliasInfo
    EffectInfo
    EscapeInfo
    RangeInfo
    LoopInfo
    DominatorInfo
    TargetInfo
    DebugInfo
}
```

---

# 66. SSA value

```text id="n6q3m8"
SSAValue {
    ValueId
    TypeId
    Def
    Uses
    Range
    FastMathFlags?
    DebugOrigin
}
```

---

# 67. Memory access

```text id="x4m9p2"
MemoryAccess {
    AccessId
    Kind
    Region
    AliasClass
    DefiningMemory
    Effects
    Ordering
    Volatile
    SourceOrigin
}
```

---

# 68. Memory region

```text id="k7q2r5"
MemoryRegion {
    RegionId
    StorageIdentity
    AddressSpace
    Size
    Alignment
    Provenance
    Escape
}
```

---

# 69. MemoryRegion không phải source region

Source:

```text id="c5m8q1"
user.name
```

có semantic region.

OptIR có thể map nó thành:

```text id="p2r7v4"
MemoryRegion #42
```

nhưng optimizer không cần giữ source syntax.

---

# 70. Verification boundary

Một nguyên tắc tuyệt đối:

```text id="m8q3v6"
MIR verifier
      ↓
 correctness
```

Sau đó:

```text id="r5n7p2"
OptIR
```

chỉ được transform khi pass chứng minh preconditions.

---

# 71. Opt pass contract

Mỗi optimization pass phải khai báo:

```text id="q4m8x1"
requires:
    SSA
    MemorySSA
    AliasInfo

preserves:
    types
    effects
    ownership semantics
    observable ordering

invalidates:
    selected analyses
```

---

# 72. Analysis invalidation

Ví dụ Store-to-Load Forwarding thay đổi memory:

```text id="n7r3m5"
AliasInfo
RangeInfo
MemorySSA
```

có thể cần update/invalidate.

Không dùng stale facts.

---

# 73. Analysis dependency graph

```text id="p8q2m6"
CFG
 │
 ├── DominatorTree
 │
 ├── LoopInfo
 │
 └── SSA
       │
       └── MemorySSA
              │
              ├── Alias
              └── Effect
```

Các analysis có dependency rõ ràng.

---

# 74. Incremental optimization

Nếu một function thay đổi:

```text id="m3r7q9"
OptIR(foo)
```

được invalidated.

Function độc lập không cần rebuild.

---

# 75. Parallel optimization

Functions độc lập có thể optimize song song.

LTO chỉ tạo thêm interprocedural opportunities.

---

# 76. Debug provenance

Mỗi SSA value:

```text id="q6m2r8"
SourceOrigin
```

có thể truy ngược:

```text id="v3n7p1"
source
 → HIR
 → MIR
 → Verified MIR
 → SSA
 → Machine
```

---

# 77. AI inspection

CLI:

```text id="r8m4q2"
axc inspect ssa foo
axc inspect memory foo
axc inspect alias foo
axc inspect effects foo
axc inspect escape foo
```

AI có thể yêu cầu compiler cung cấp representation thay vì tự đoán từ source.

---

# 78. Optimization legality

Ví dụ CSE:

```text id="p7m2q5"
CanMerge(load1, load2)
```

chỉ true nếu:

```text id="x4r8n1"
same semantic value
AND
no clobber
AND
effects compatible
AND
volatile = false
AND
atomic semantics preserved
```

---

# 79. Vectorization legality

Compiler cần:

```text id="m8q3v6"
NoAlias
Range
Effect
Alignment
Overflow semantics
FP semantics
```

Không phải chỉ nhìn loop syntax.

---

# 80. Đây là điểm Axiom đạt “compiler hiểu nhiều hơn programmer”

Programmer chỉ viết:

```ax id="k7m4p2"
for i in 0..n {
    out[i] = a[i] + b[i];
}
```

Compiler có thể tự suy luận:

```text id="v2q8m5"
ownership
capability
regions
alias
effects
escape
ranges
SSA
MemorySSA
vectorization legality
```

Nếu chứng minh được:

```text id="r6n3q1"
out ⊥ a
out ⊥ b
a ⊥ b
```

thì vectorization có thể diễn ra mà programmer không cần `restrict`.

---

# 81. Invariants

### `AOPTIR-20`
Verified MIR is the semantic source for OptIR construction.

### `AOPTIR-21`
OptIR is distinct from semantic MIR.

### `AOPTIR-22`
SSA values have a single logical definition.

### `AOPTIR-23`
SSA construction does not redefine ownership semantics.

### `AOPTIR-24`
Move semantics remain distinct from physical copying.

### `AOPTIR-25`
Copy semantics remain distinct from physical copying.

### `AOPTIR-26`
Drop semantics remain preserved through SSA transformation.

### `AOPTIR-27`
Partial ownership states cannot be silently erased by scalarization.

### `AOPTIR-28`
MemorySSA models semantic memory dependencies for optimization.

### `AOPTIR-29`
MemorySSA is compiler representation only.

### `AOPTIR-30`
MemorySSA does not introduce runtime metadata.

### `AOPTIR-31`
AliasInfo refines MemorySSA clobber relationships.

### `AOPTIR-32`
Unknown aliasing is never treated as no-alias.

### `AOPTIR-33`
Memory accesses retain storage-domain identity.

### `AOPTIR-34`
CPU and GPU address spaces remain distinct where required.

### `AOPTIR-35`
Atomic operations retain atomic semantics.

### `AOPTIR-36`
Atomic memory ordering is preserved.

### `AOPTIR-37`
Volatile operations remain observable.

### `AOPTIR-38`
Compiler barriers and CPU fences remain distinct.

### `AOPTIR-39`
Observable IO ordering is preserved.

### `AOPTIR-40`
External-state effects prevent invalid common-subexpression elimination.

### `AOPTIR-41`
Pure calls may be eliminated or merged only when all observable semantics permit.

### `AOPTIR-42`
Read effects invalidate only overlapping or otherwise affected regions.

### `AOPTIR-43`
Write effects invalidate dependent memory facts.

### `AOPTIR-44`
Unknown calls conservatively invalidate potentially affected memory.

### `AOPTIR-45`
Effect summaries may refine call-side memory clobbers.

### `AOPTIR-46`
Alias information may refine call-side memory clobbers.

### `AOPTIR-47`
Escape information may enable memory-to-register promotion.

### `AOPTIR-48`
Observable addresses prevent invalid storage promotion.

### `AOPTIR-49`
Observable allocation identity prevents invalid allocation elimination.

### `AOPTIR-50`
SSA does not imply register allocation.

### `AOPTIR-51`
MemorySSA does not imply physical memory.

### `AOPTIR-52`
SSA construction supports aggregate scalarization.

### `AOPTIR-53`
Scalar replacement must preserve Drop semantics.

### `AOPTIR-54`
SSA supports vector and predicate values.

### `AOPTIR-55`
Async suspension boundaries remain explicit until correctly lowered.

### `AOPTIR-56`
Only values live across suspension become persistent async state.

### `AOPTIR-57`
GPU memory spaces are represented distinctly.

### `AOPTIR-58`
MemoryPhi represents control-flow memory merges.

### `AOPTIR-59`
Phi construction respects dominance.

### `AOPTIR-60`
Optimization passes declare analysis dependencies and invalidations.

### `AOPTIR-61`
Stale analysis facts may not be consumed after invalidation.

### `AOPTIR-62`
Optimization transformations require explicit legality conditions.

### `AOPTIR-63`
Optimization cannot weaken Verified MIR safety properties.

### `AOPTIR-64`
Optimization failure only reduces optimization opportunities.

### `AOPTIR-65`
OptIR transformations preserve observable semantics.

### `AOPTIR-66`
OptIR retains sufficient source provenance for diagnostics/debugging.

### `AOPTIR-67`
SSA and MemorySSA are incrementally recomputable.

### `AOPTIR-68`
Independent functions may be optimized in parallel.

### `AOPTIR-69`
Analysis results are deterministic.

### `AOPTIR-70`
AI/compiler inspection can expose SSA and MemorySSA explanations.

### `AOPTIR-71`
Alias classes are optimization facts, not source-level ownership declarations.

### `AOPTIR-72`
Capability metadata may be erased after its optimization-relevant facts are materialized.

### `AOPTIR-73`
No optimization pass may manufacture a safety proof.

### `AOPTIR-74`
Verified MIR remains the correctness boundary.

### `AOPTIR-75`
Physical representation changes cannot alter semantic ownership, capability, effect, or Drop behavior.

---

# Một quyết định kiến trúc rất quan trọng đã được khóa

Axiom hiện không cố làm một IR duy nhất “ôm tất cả”.

Thay vào đó:

```text
                 HIR
                  │
          source semantics
                  │
                  ▼
                 MIR
          semantic execution
                  │
          ┌───────┴────────┐
          │    VERIFY      │
          └───────┬────────┘
                  ▼
             Verified MIR
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
     Alias      Effect     Escape
       └──────────┼──────────┘
                  ▼
             SSA + MemorySSA
                  │
                  ▼
                OptIR
                  │
                  ▼
             ABI MIR
```

Đây là kiến trúc tốt hơn việc cố nhồi ownership, borrow, optimization và machine representation vào cùng một IR.

---

# BOOTSTRAP-140 — Optimization Pass Manager & Legality Framework

Bước tiếp theo nên khóa **cơ chế điều phối toàn bộ optimizer**, thay vì tiếp tục thêm từng optimization riêng lẻ.

Trọng tâm:

```text
OptIR
 │
 ├── Simplification
 ├── SCCP
 ├── GVN/CSE
 ├── DCE
 ├── SROA
 ├── InstCombine
 ├── CFG Simplification
 ├── Inlining
 ├── Devirtualization
 ├── Loop Optimization
 ├── LICM
 ├── Bounds Elimination
 ├── Vectorization
 ├── Specialization
 ├── Allocation Optimization
 ├── Async Optimization
 └── GPU Optimization
        ↓
      ABI MIR
```

Nhưng phần quan trọng nhất của **BOOTSTRAP-140** sẽ không phải danh sách pass.

Nó sẽ khóa:

> **mỗi optimization phải có precondition, legality proof, preserved analyses, invalidated analyses và rollback/failure semantics.**

Như vậy compiler có thể tối ưu rất mạnh mà vẫn giữ nguyên nguyên tắc:

**“Không chứng minh được → không tối ưu; không phải đoán.”**