Tiếp tục **COMPILER-005 — MIR Design + Lowering + Semantic Verification**.

Đây là một trong những bước quan trọng nhất của Axiom. Tôi chốt kiến trúc theo hướng:

> **Axiom MIR không phải SSA thuần và cũng không phải AST-like IR. Nó là typed, CFG-based, SSA-assisted, place-based semantic IR.**

Điểm này giúp xử lý ownership, partial move, views, Drop, async, mutable memory và sau đó vẫn hạ rất tốt xuống LIR.

---

# COMPILER-005 — AXIOM MIR

## 1. Vai trò của MIR

Pipeline:

```text
Source
  ↓
AST
  ↓
HIR
  ↓
Typed HIR
  ↓
Ownership / Capability Verification
  ↓
Verified HIR
  ↓
MIR
  ↓
MIR Verification
  ↓
Semantic Optimization
  ↓
ABI MIR
  ↓
LIR
```

MIR là **semantic authority trước ABI**.

Nó phải biết:

- type;
- control flow;
- ownership consequences;
- Move/Copy;
- Drop;
- memory places;
- capability consequences;
- calls;
- async suspension;
- atomic operations;
- synchronization;
- allocation;
- panic/unwind edges.

Nhưng MIR **không biết**:

- physical register;
- x86 instruction;
- stack offset;
- ELF relocation;
- PE section;
- machine encoding.

---

# 2. Quyết định lớn: MIR không phải SSA thuần

Không nên làm:

```text
x1 = ...
x2 = ...
x3 = ...
```

cho mọi memory object.

Thay vào đó dùng:

```text
SSA values
+
Places
```

Ví dụ:

```axiom
var x = Foo();
x.a = 10;
x.b = 20;
```

MIR:

```text
x = ALLOC_LOCAL Foo

STORE x.a, 10
STORE x.b, 20
```

Trong khi các scalar tạm thời có thể là SSA:

```text
%1 = CONST 10
%2 = ADD %a, %b
```

---

# 3. Place model

Đây là khái niệm trung tâm.

```text
Place
```

là một vị trí semantic có thể chứa value.

Ví dụ:

```text
x
x.a
x.b
x.array[i]
*ptr
```

Mỗi Place được biểu diễn:

```text
Place {
    base: PlaceBase
    projections: [Projection]
}
```

Ví dụ:

```text
x.a.b
```

là:

```text
base = x
projection = Field(a)
projection = Field(b)
```

---

# 4. Projection

MIR hỗ trợ:

```text
Field
Index
Deref
Slice
Downcast
VariantField
```

Ví dụ:

```text
user.name
```

→

```text
Place {
    base = user
    projections = [
        Field(name)
    ]
}
```

---

# 5. Place không phải pointer

Điều này rất quan trọng.

```text
x.a
```

không có nghĩa compiler phải tạo địa chỉ.

Place chỉ nói:

> value semantic này nằm ở đâu trong aggregate/storage abstraction.

Backend sau đó có thể:

```text
register
stack
inline
memory
scalarized
```

---

# 6. SSA values

MIR vẫn sử dụng SSA cho **computed values**.

Ví dụ:

```axiom
let c = a + b;
```

MIR:

```text
%0 = LOAD a
%1 = LOAD b
%2 = ADD %0, %1
STORE c, %2
```

Hoặc nếu compiler chứng minh `c` chỉ là temporary:

```text
%2 = ADD %0, %1
```

không cần storage.

---

# 7. Tách Value và Place

MIR có hai thế giới:

```text
Value
Place
```

Value:

```text
%42
```

Place:

```text
x.a
```

Operations:

```text
PLACE → VALUE
LOAD

VALUE → PLACE
STORE
```

Điều này cực kỳ hữu ích cho ownership.

---

# 8. MOVE

```text
MOVE place
```

semantic:

```text
read ownership from place
invalidate ownership of place
produce owned value
```

Ví dụ:

```axiom
let b = a;
```

nếu `a` !Copy:

```text
%0 = MOVE a
STORE b, %0
```

---

# 9. COPY

Nếu `a: Copy`:

```text
%0 = COPY a
STORE b, %0
```

Không thay đổi ownership state của `a`.

---

# 10. BORROW_READ / BORROW_WRITE

MIR cần giữ capability semantics đủ lâu để verifier kiểm tra.

```text
%B = BORROW_READ place
```

và:

```text
%B = BORROW_WRITE place
```

Nhưng đây không phải machine pointer bắt buộc.

Sau capability verification, chúng có thể được lower thành:

```text
pointer
address
register
```

hoặc biến mất hoàn toàn.

---

# 11. Capability token

Một borrow tạo ra:

```text
CapabilityId
```

Ví dụ:

```text
%B = BORROW_READ x
```

`%B` đại diện cho capability.

Operations sử dụng:

```text
READ %B
```

hoặc:

```text
FIELD %B, field
```

Capability token không nhất thiết tồn tại runtime.

---

# 12. `view<T>` representation

Semantic MIR:

```text
%B = BORROW_READ x
```

Backend có thể biến thành:

```text
pointer + length
```

hoặc:

```text
pointer
```

hoặc thậm chí scalarize/eliminate nếu không cần.

MIR không được hard-code:

```text
view<T> = { ptr, len }
```

vì đó là ABI/storage decision.

---

# 13. `mut_view<T>`

```text
%B = BORROW_WRITE x
```

Verifier đảm bảo:

```text
no conflicting READ
no conflicting WRITE
valid provenance
valid owner
```

Sau đó backend mới quyết định representation.

---

# 14. DROP

MIR có explicit:

```text
DROP place
```

Ví dụ:

```axiom
let file = open()?;
```

exit:

```text
DROP file
RETURN
```

Drop elaboration xảy ra trước hoặc trong MIR construction, nhưng sau ownership verification.

---

# 15. Drop không phải `free`

```text
DROP x
```

semantic:

> kết thúc resource/ownership obligation.

Nó có thể lower thành:

```text
CALL File.close
```

hoặc:

```text
CALL destructor
```

hoặc:

```text
nothing
```

nếu compiler chứng minh Drop rỗng.

Không được đồng nhất:

```text
DROP == DEALLOC
```

---

# 16. DEALLOC

Nếu cần semantic storage release:

```text
DEALLOC storage
```

nhưng thường được suy ra từ resource/storage abstraction.

Ví dụ:

```text
DROP Box<T>
    ↓
destroy T
    ↓
release storage
```

MIR có thể biểu diễn:

```text
DROP box
```

và lower pass quyết định `DEALLOC`.

---

# 17. ALLOC

MIR có:

```text
ALLOC
```

nhưng nó biểu diễn **semantic storage requirement**, không nhất thiết:

```text
malloc()
```

Ví dụ:

```text
ALLOC {
    kind: Dynamic
    type: T
    alignment: ...
}
```

sau optimization có thể biến mất.

---

# 18. Local allocation

Source:

```axiom
let x = Foo();
```

không nhất thiết:

```text
ALLOC stack
```

MIR có thể:

```text
PLACE x
CALL Foo -> x
```

và storage placement do later optimization quyết định.

---

# 19. `CALL`

MIR call:

```text
CALL {
    callee: FunctionId
    args: [...]
    result: Value/Place
}
```

Trait resolution đã hoàn tất.

Không còn:

```text
"which trait implementation?"
```

trong MIR.

---

# 20. Dynamic dispatch

Nếu source:

```axiom
dyn Trait
```

MIR đã biết:

```text
CALL_DYN {
    object
    method_slot
}
```

hoặc canonical:

```text
CALL {
    dispatch: DynamicTrait
    ...
}
```

Sau ABI lowering mới thành:

```text
load vtable
load function pointer
indirect call
```

---

# 21. Closure call

Closure:

```axiom
f(x)
```

nếu closure type:

```text
Closure<F>
```

MIR:

```text
CALL_CLOSURE {
    environment
    function
    args
}
```

Sau đó ABI lowering quyết định:

```text
environment register
hidden parameter
stack argument
```

---

# 22. Branch

MIR basic block:

```text
BlockId
```

Terminator:

```text
BRANCH target
COND_BRANCH cond, true_bb, false_bb
SWITCH value, cases
RETURN
TRAP
UNREACHABLE
```

Mỗi basic block chỉ có **một terminator**.

---

# 23. Phi

Với SSA values:

```text
%3 = PHI {
    bb1: %1
    bb2: %2
}
```

Nhưng Place không cần biến thành SSA phi bằng mọi giá.

Ví dụ:

```axiom
var x = 0;

if c {
    x = 1;
} else {
    x = 2;
}
```

có thể giữ:

```text
STORE x, 1
STORE x, 2
```

sau đó Memory/Scalar optimization mới promote `x` nếu có lợi.

---

# 24. Đây là lựa chọn quan trọng

Không nên xây MIR theo kiểu:

> mọi local variable bắt buộc SSA.

Axiom có:

```text
Place-based semantic memory model
```

rồi optimizer có thể xây:

```text
Memory SSA
Scalar SSA
```

khi cần.

Điều này đơn giản hóa ownership và partial move rất nhiều.

---

# 25. Partial move trong MIR

Ví dụ:

```axiom
let name = user.name;
```

MIR:

```text
%0 = MOVE user.name
STORE name, %0
```

Ownership verifier biết:

```text
user.name = Moved
user.id = Owned
```

Không cần biến toàn bộ `user` thành moved.

---

# 26. Whole-object move

```axiom
let other = user;
```

MIR:

```text
%0 = MOVE user
STORE other, %0
```

Ownership:

```text
user = Moved
other = Owned
```

---

# 27. Reinitialization

Axiom phải cho phép:

```axiom
var x = Foo();

x = Bar();
```

nếu `x` đang Owned.

Compiler phải xử lý:

```text
DROP x
STORE x, Bar
```

nếu assignment thay thế resource.

---

# 28. Reinitialize moved value

Quan trọng hơn:

```axiom
var x = Foo();

consume(x);

x = Foo();
```

hợp lệ.

State:

```text
Owned
 ↓
Moved
 ↓
Owned
```

MIR:

```text
MOVE x
...
CALL Foo
STORE x
```

Không cần tạo một local mới.

---

# 29. Uninitialized state

MIR phải hỗ trợ:

```text
UNINIT place
```

Ví dụ compiler lowering:

```axiom
var x: T;

if condition {
    x = make();
} else {
    x = make_other();
}

use(x);
```

Verifier phải chứng minh:

```text
all incoming CFG paths initialize x
```

---

# 30. Maybe-uninitialized

Nếu:

```axiom
var x: T;

if condition {
    x = make();
}

use(x);
```

merge:

```text
x = MAYBE_UNINITIALIZED
```

→ compile error.

---

# 31. Initialization và ownership là cùng một dataflow family

Compiler không nên có:

```text
InitializationChecker
OwnershipChecker
MoveChecker
DropChecker
```

hoàn toàn độc lập.

Nên có:

```text
ValueStateAnalysis
```

với:

```text
InitState
OwnershipState
DropState
PartialMoveState
```

và các facts liên kết.

---

# 32. State của một Place

Ví dụ:

```text
PlaceState {
    initialization
    ownership
    drop_status
    moved_fields
    active_capabilities
}
```

Conceptually:

```text
x
├── initialized
├── owned
├── not dropped
└── capabilities = [...]
```

---

# 33. Capability trong MIR

Mỗi capability:

```text
Capability {
    id
    source_place
    provenance
    region
    access
    parent
    validity
}
```

Access:

```text
READ
WRITE
```

---

# 34. Capability tree

Ví dụ:

```text
view(user)
    │
    ├── view(user.name)
    │
    └── view(user.id)
```

Ta có:

```text
Capability#1
 ├── Capability#2
 └── Capability#3
```

Destroy parent capability phải xử lý children.

---

# 35. Region representation

Không cần symbolic theorem prover đầy đủ.

V1 dùng:

```text
Region {
    root_place
    projections
    index_constraints
}
```

Ví dụ:

```text
x.a
```

→ exact field region.

```text
x[i]
```

→ indexed region.

---

# 36. Region overlap algorithm

Theo thứ tự:

```text
1. Different roots
      → DISJOINT

2. Different fields of same struct
      → DISJOINT

3. Same projection
      → SAME

4. One projection prefixes another
      → CONTAINS / CONTAINED_BY

5. Proven index ranges disjoint
      → DISJOINT

6. Proven same index
      → SAME

7. Otherwise
      → UNKNOWN
```

Đủ mạnh cho v1 mà không cần SMT solver.

---

# 37. Runtime disjointness abstraction

Library intrinsic có thể cung cấp:

```text
split_mut
```

và compiler nhận một semantic fact:

```text
result0.region DISJOINT result1.region
```

Đây là **proof-producing API boundary**, không phải arbitrary unsafe promise.

---

# 38. Loop analysis

Loops là nơi ownership checker dễ sai.

Ví dụ:

```axiom
loop {
    let x = make();
    process(x);
}
```

Mỗi iteration phải:

```text
create x
use x
drop x
```

Không được carry ownership state của `x` sang iteration.

---

# 39. Loop-carried value

```axiom
var x = initial();

loop {
    x = step(x);
}
```

MIR cần:

```text
loop_header
    ↓
MOVE x
CALL step
STORE x
    ↓
loop_header
```

Ownership state sau back-edge phải converge.

---

# 40. Dataflow convergence

Ownership analysis phải là monotonic fixed-point analysis.

```text
initial state
   ↓
transfer
   ↓
merge
   ↓
repeat
```

đến khi:

```text
state == previous_state
```

Vì lattice hữu hạn/được giới hạn nên termination deterministic.

---

# 41. Không cần borrow-checker theorem prover

Đây là một chủ đích.

Axiom v1 không cần:

```text
SMT solver
dependent type solver
full symbolic lifetime theorem proving
```

Compiler sử dụng:

```text
CFG
path-sensitive facts
place projections
region relations
known semantic contracts
```

Nếu không chứng minh được → safe code reject.

---

# 42. `match` và Drop

Ví dụ:

```axiom
match get() {
    Some(x) => use(x),
    None => ...
}
```

Mỗi arm có cleanup graph riêng.

Khi merge:

```text
all moved fields
all dropped fields
all capabilities
```

được join.

---

# 43. `return`

Mọi:

```text
RETURN
```

đi qua CleanupGraph.

Ví dụ:

```text
RETURN value
```

semantic order:

```text
evaluate return value
↓
move return value
↓
drop remaining locals
↓
return
```

Đây là thứ phải chốt rõ.

---

# 44. Return value phải được bảo vệ khỏi Drop

Ví dụ:

```axiom
fn make() -> String {
    let x = String(...);
    return x;
}
```

Không được:

```text
MOVE x
DROP x
RETURN
```

Sau Move:

```text
x = Moved
```

nên cleanup bỏ qua `x`.

---

# 45. `?`

Ví dụ:

```axiom
let x = foo()?;
```

MIR:

```text
%r = CALL foo
SWITCH %r
    Ok(value) → continue
    Err(e)    → cleanup + return Err(e)
```

Cleanup graph xử lý resource.

Không có hidden exception machinery.

---

# 46. Panic

```axiom
panic("bad");
```

MIR:

```text
CALL panic
UNREACHABLE
```

vì:

```text
panic() -> never
```

Nếu panic profile = unwind:

```text
panic edge → cleanup graph
```

Nếu abort:

```text
no normal unwind machinery
```

---

# 47. Break/continue

Ví dụ:

```axiom
loop {
    let x = acquire();

    if done {
        break;
    }

    use(x);
}
```

`break` phải Drop `x`.

```text
break
 ↓
cleanup current loop scope
 ↓
loop_exit
```

`continue` cũng cleanup locals của iteration trước khi quay header.

---

# 48. Capability cleanup

Nếu:

```axiom
let v = view(x);
break;
```

compiler kết thúc capability trước khi owner scope kết thúc.

Capability không được sống sang block không còn provenance.

---

# 49. `await`

MIR có:

```text
AWAIT future
```

nhưng semantics chi tiết:

```text
CALL/POLL
 ↓
READY → continue
PENDING → suspend
```

Later async lowering biến nó thành state machine.

---

# 50. Critical async invariant

Trước `AWAIT` verifier phải đảm bảo:

```text
no synchronous borrowed capability requiring current stack frame
```

đang live qua suspension.

Owned values được phép trở thành state-machine fields.

---

# 51. Async lowering chưa làm ở COMPILER-005

Chỉ MIR representation.

Sau này:

```text
COMPILER-006 — Async/Closure/Control-Flow Lowering
```

sẽ biến:

```text
AWAIT
```

thành state machine.

Không nên nhồi toàn bộ async lowering vào MIR design ban đầu.

---

# 52. Atomic MIR

Không lower atomic thành ordinary Load/Store.

MIR:

```text
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
FENCE
```

với:

```text
ordering
scope
type
```

Ví dụ:

```text
ATOMIC_LOAD p, Acquire
```

---

# 53. Lock MIR

Synchronization semantic operations:

```text
LOCK
UNLOCK
WAIT
NOTIFY
```

Guard ownership vẫn được verifier xử lý.

Sau này backend/runtime mapping:

```text
futex
pthread
Windows SRW
custom spinlock
```

---

# 54. GPU MIR

`@kernel` function có ExecutionDomain:

```text
GPU
```

MIR verifier cấm:

```text
File
Socket
OS syscall
blocking mutex
host pointer
```

theo GPU rules đã frozen.

---

# 55. MIR execution domain

Mỗi function/call có fact:

```text
ExecutionDomain {
    CPU
    GPU
    Device
    Kernel
}
```

Không để GPU verifier và concurrency verifier tự phát minh model riêng.

---

# 56. MIR instruction set v1

Tôi chốt bộ semantic tối thiểu:

```text
CONST
UNINIT

COPY
MOVE

FIELD
INDEX
DEREF

BORROW_READ
BORROW_WRITE

LOAD
STORE

ALLOC
DEALLOC
DROP

ADD
SUB
MUL
DIV
REM

NEG
NOT

AND
OR
XOR
SHL
SHR
SAR

CMP
SELECT

CAST
BITCAST

CALL
CALL_INDIRECT
CALL_DYN
CALL_CLOSURE

BR
COND_BR
SWITCH
PHI

RETURN

PANIC
TRAP
UNREACHABLE

ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
FENCE

LOCK
UNLOCK
WAIT
NOTIFY

AWAIT
SPAWN
YIELD
```

Không thêm hàng trăm instruction vì optimization/target-specific behavior thuộc các tầng sau.

---

# 57. Arithmetic semantics

MIR phải lưu semantic mode:

```text
ADD
```

không đủ nếu overflow behavior khác nhau.

Ví dụ:

```text
ADD_CHECKED
ADD_WRAPPING
ADD_SATURATING
```

hoặc:

```text
ADD {
    overflow: Checked
}
```

Tôi chọn dạng thứ hai:

```text
BinaryOp {
    opcode: Add
    overflow: Checked
}
```

để tránh instruction explosion.

---

# 58. Division

MIR:

```text
DIV
REM
```

có semantic:

```text
signed/unsigned
zero-divisor behavior
overflow behavior
```

Target legalization mới quyết định:

```text
idiv
div
helper
sequence
```

---

# 59. Cast và bitcast

Phải tuyệt đối phân biệt:

```text
CAST
BITCAST
```

Ví dụ:

```axiom
x as u64
```

→ CAST.

Còn:

```text
bitcast<f32>(x)
```

→ BITCAST.

Không được để backend tự đoán.

---

# 60. MIR verifier

MIR sau lowering phải chạy verifier riêng:

```text
MIRVerifier
```

Kiểm tra:

```text
CFG validity
SSA validity
types
places
ownership consequences
capabilities
dominance
terminators
drop correctness
async legality
atomic legality
execution domain
```

---

# 61. Dominance

Nếu `%x` được dùng ở block:

```text
BB3
```

definition phải dominate use.

SSA verifier kiểm tra.

Place storage không chịu SSA dominance theo cách tương tự.

---

# 62. Type verification

Mỗi instruction có type contract.

Ví dụ:

```text
ADD
```

yêu cầu:

```text
numeric lhs
numeric rhs
compatible type
```

`STORE`:

```text
value.type == place.type
```

`FIELD`:

```text
place.type == struct
field belongs to struct
```

---

# 63. Ownership verification ở MIR

MIR verifier không nên **tái phát minh** toàn bộ ownership checker.

Nó xác minh:

> MIR đúng với OwnershipFacts đã được chứng minh.

Ví dụ:

```text
MOVE x
```

phải có:

```text
x is Owned
```

và sau đó:

```text
x = Moved
```

---

# 64. Capability verification ở MIR

Tương tự:

```text
LOAD through capability C
```

phải có:

```text
C.valid
C.access includes READ
```

`STORE` yêu cầu:

```text
WRITE
```

---

# 65. Sau semantic optimization

Ownership details có thể được erase.

Ví dụ:

```text
BORROW_READ x
LOAD x
END_CAPABILITY
```

có thể trở thành:

```text
LOAD x
```

nếu proof đã hoàn thành và không có runtime-observable consequence.

---

# 66. Đây là Abstraction Erasure

MIR ban đầu:

```text
ownership
capability
```

MIR sau verification/optimization:

```text
ordinary dataflow
```

LIR:

```text
register/memory
```

Machine IR:

```text
machine resources
```

Không có:

```text
borrow checker runtime
```

---

# 67. Semantic optimization

Sau MIR verification:

```text
Verified MIR
   ↓
MIR Optimization
```

Pass đầu tiên:

```text
constant folding
copy propagation
dead local elimination
dead store
scalar replacement
load/store forwarding
CFG simplify
branch folding
inlining
```

nhưng chỉ khi semantics giữ nguyên.

---

# 68. Ownership facts hỗ trợ optimization

Ví dụ:

```text
mut_view(a)
mut_view(b)
```

đã chứng minh:

```text
DISJOINT
```

optimizer có thể dùng:

```text
NoAlias
```

→ load/store reorder/vectorize tốt hơn.

Đây là một trong những nơi Axiom có khả năng vượt C ở mức **compiler information**, không phải vì CPU instruction khác.

---

# 69. Memory SSA sau này

Tôi không đưa Memory SSA thành semantic requirement.

Optimizer có thể xây:

```text
MemorySSA
```

trên Verified MIR.

Như vậy:

```text
Semantic MIR
```

vẫn đơn giản.

---

# 70. MIR → LIR boundary

Sau semantic optimization:

```text
MIR
 ↓
ABI Lowering
 ↓
LIR
```

Những thứ biến mất:

```text
Ownership
Capability
Trait constraints
Generic parameters
High-level enums
Pattern semantics
```

những thứ còn:

```text
values
memory
calls
control flow
atomics
ABI
```

---

# 71. Generic types

Không để:

```text
<T>
Trait obligations
```

xuống LIR.

Monomorphization trước:

```text
Vec<i32>
Vec<f64>
```

thành concrete functions/types.

---

# 72. Enum lowering

MIR vẫn có:

```text
SWITCH_ENUM
```

hoặc generic:

```text
SWITCH
```

sau layout lowering mới thành:

```text
tag load
compare
branch
```

hoặc niche optimization.

---

# 73. Option optimization

Ví dụ:

```text
Option<&T>
```

có thể dùng null niche.

Nhưng semantic MIR vẫn:

```text
Some
None
```

không hard-code null representation.

---

# 74. Struct layout

MIR:

```text
FIELD x.a
FIELD x.b
```

không assume offsets.

Layout phase:

```text
Type/Layout
 ↓
field offsets
 ↓
ABI lowering
```

---

# 75. MIR module structure

Tôi đề xuất:

```text
compiler/mir/
├── ir/
│   ├── module
│   ├── function
│   ├── block
│   ├── instruction
│   ├── value
│   ├── place
│   ├── projection
│   └── terminator
├── builder/
├── lowering/
├── verifier/
├── ownership/
├── capability/
├── cleanup/
├── analysis/
├── optimize/
├── printer/
└── serialization/
```

---

# 76. MIR IDs

Không dùng pointer identity.

```text
MirFunctionId
BasicBlockId
InstructionId
ValueId
PlaceId
CapabilityId
StorageId
```

đều stable internal IDs.

Điều này phù hợp toàn bộ kiến trúc compiler trước đó.

---

# 77. MIR serialization

Nên hỗ trợ:

```bash
axiom inspect --mir file.ax
```

Output human-readable.

Và:

```bash
axiom inspect --mir --format=json
```

cho AI/tooling.

Ví dụ:

```json
{
  "function": "foo",
  "blocks": [...],
  "instructions": [...]
}
```

Không phải source syntax; đây là compiler inspection format.

---

# 78. MIR diagnostics

Namespace:

```text
AX15xx
```

Ví dụ:

```text
AX1501 invalid MIR block
AX1502 invalid terminator
AX1503 type mismatch in MIR
AX1504 use before definition
AX1505 invalid place projection
AX1506 invalid move
AX1507 invalid drop
AX1508 invalid capability use
AX1509 invalid borrow region
AX1510 invalid atomic ordering
AX1511 invalid execution domain
AX1512 invalid async suspension
AX1513 unreachable MIR invariant
AX1599 internal MIR invariant failure
```

`AX1599` là compiler ICE territory, không phải user source error.

---

# 79. MIR invariant set

Chốt:

```text
AMIR-20   Every MIR Function Has A Valid CFG
AMIR-21   Every Basic Block Has One Terminator
AMIR-22   MIR Values Have Stable Identity
AMIR-23   MIR Places Have Stable Identity
AMIR-24   Every Instruction Has A Valid Semantic Type
AMIR-25   SSA Values Dominate Their Uses
AMIR-26   Places Are Not Required To Be SSA
AMIR-27   Place Projections Are Type Validated
AMIR-28   Move Consumes Ownership
AMIR-29   Copy Preserves Ownership
AMIR-30   Drop Applies Only To Valid Owned State
AMIR-31   Moved Fields Are Not Dropped
AMIR-32   Partial Move State Is Field Sensitive
AMIR-33   Capability Uses Require Valid Capabilities
AMIR-34   Read Operations Require Read Capability
AMIR-35   Write Operations Require Write Capability
AMIR-36   Capability Provenance Must Remain Valid
AMIR-37   Capability Lifetime Cannot Exceed Provenance
AMIR-38   Owner Destruction Cannot Precede Dependent Capability End
AMIR-39   Allocation Is Semantic Before Lowering
AMIR-40   Deallocation Is Distinct From Drop
AMIR-41   Calls Have Resolved Dispatch Semantics
AMIR-42   Trait Resolution Does Not Occur In MIR
AMIR-43   Generic Constraints Do Not Reach MIR
AMIR-44   Atomic Operations Preserve Explicit Ordering
AMIR-45   Volatile Operations Are Not Ordinary Memory Operations
AMIR-46   Async Suspension Preserves Required Owned State
AMIR-47   Invalid Borrowed Capabilities Cannot Cross Await
AMIR-48   Execution-Domain Rules Are Verified
AMIR-49   MIR Does Not Encode Physical Registers
AMIR-50   MIR Does Not Encode Object-File Semantics
AMIR-51   MIR Lowering Is Deterministic
AMIR-52   MIR Verification Is Independent Of Optimization Level
AMIR-53   Semantic Optimization Preserves Observable Semantics
AMIR-54   Ownership Proof Data May Be Erased After Verification
AMIR-55   Capability Proof Data May Be Erased After Verification
AMIR-56   MIR Does Not Require A Runtime Ownership System
AMIR-57   MIR Does Not Require A Garbage Collector
AMIR-58   MIR Does Not Require A Monolithic Runtime
AMIR-59   Return Cleanup Is Explicitly Represented
AMIR-60   Exceptional Control Flow Preserves Cleanup Semantics
```

---

# 80. Kiến trúc semantic core hiện tại

Ta đã đi được tới:

```text
                    Axiom Source
                         │
                         ▼
                    Lexer/Parser
                         │
                         ▼
                        AST
                         │
                         ▼
                  Name Resolution
                         │
                         ▼
                        HIR
                         │
                         ▼
               Type + Trait Solver
                         │
                         ▼
                    Typed HIR
                         │
                         ▼
          Ownership / Capability Checker
                         │
                         ▼
                  Verified HIR
                         │
                         ▼
                 Drop Elaboration
                         │
                         ▼
                        MIR
                         │
                         ▼
                  MIR Verification
                         │
                         ▼
                 MIR Optimization
                         │
                         ▼
                    ABI Lowering
                         │
                         ▼
                        LIR
                         │
                         ▼
                 Target Legalization
                         │
                         ▼
                   Machine IR
```

Đây là kiến trúc rất quan trọng vì nó đảm bảo:

> **Frontend chịu trách nhiệm chứng minh semantics; backend chỉ cần tối ưu semantics đã được chứng minh.**

---

# 81. Một quyết định kiến trúc rất đáng giữ

Tôi chốt nguyên tắc:

### Axiom MIR = Place-based semantic IR + SSA values

Không phải:

```text
Rust MIR clone
```

và cũng không phải:

```text
LLVM IR clone
```

Axiom MIR cần giữ được những thứ LLVM IR không nên biết:

```text
MOVE
PARTIAL MOVE
DROP
CAPABILITY
PROVENANCE
```

nhưng loại bỏ chúng càng sớm càng tốt sau khi proof hoàn tất.

Điều này tạo ra đường đi rất sạch:

```text
High-level proof
      ↓
Semantic MIR
      ↓
Proof erasure
      ↓
Low-level optimization
      ↓
Machine code
```

---

# 82. Bước tiếp theo

Frontend semantic core hiện đã đủ để chuyển sang phần **control-flow lowering và các abstraction đặc biệt**.

Task tiếp theo là:

## **COMPILER-006 — Closure + Async + Generator/State-Machine Lowering**

Trong đó cần chốt:

```text
Closure representation
Capture analysis
Fn/FnMut/FnOnce semantics
Closure environment layout
Non-capturing closure → function pointer
Async Future representation
Await lowering
State-machine generation
Suspension points
Future ownership
Send across await
Drop of partially initialized Future
Cancellation
Recursive async
Spawn
Generator-like control flow
```

Đặc biệt phải giải quyết một vấn đề rất quan trọng:

> **Làm thế nào để `async/await` của Axiom không biến thành một runtime-heavy abstraction, mà compiler có thể biến một async function thành một state machine nhỏ gọn gần như code C thủ công?**

Đó sẽ là phần tiếp theo.