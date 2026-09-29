Tiếp tục. Bây giờ chúng ta chốt **AXIOM MIR v0.1 + VERIFIED MIR CONTRACT**. Đây là mốc quan trọng nhất của compiler sau Typed HIR: từ đây backend, optimizer, Oracle và cả self-hosting đều có thể dựa trên một IR ổn định.

# AXIOM MIR v0.1

## 1. MIR phải giải quyết một vấn đề

Typed HIR vẫn gần source:

```text
if
match
method call
closure
for
async
ownership
view
```

Trong khi backend cần một mô hình gần machine hơn:

```text
basic blocks
branches
loads
stores
calls
allocations
drops
atomics
returns
```

Vì vậy:

```text
Typed HIR
    ↓
Ownership / Capability Analysis
    ↓
MIR
    ↓
Verified MIR
    ↓
Optimization
```

MIR là **semantic execution IR**, chưa phải machine IR.

---

# 2. Ba tầng IR

Tôi đề xuất giữ đúng ba tầng:

```text
HIR
 │
 │ source-oriented semantics
 ▼
MIR
 │
 │ target-neutral machine semantics
 ▼
LIR
 │
 │ target-specific lowering
 ▼
Machine IR
```

Không nên cố nhét tất cả vào một IR.

### HIR

Quan tâm:

```text
Type
Trait
Method
Pattern
Generic
Closure
Async
Ownership intent
```

### MIR

Quan tâm:

```text
Place
Value
Memory
Control flow
Call
Drop
Allocation
Atomic
Capability validity
```

### LIR

Quan tâm:

```text
Virtual register
Machine-independent instruction
Calling convention
Memory operands
Target constraints
```

---

# 3. MIR không phải SSA thuần túy

Axiom cần performance compiler mạnh, nhưng ownership/memory khiến **pure SSA** không phải representation thuận tiện nhất.

Do đó:

> **MIR là SSA-oriented, nhưng không bắt buộc pure SSA.**

Ví dụ:

```text
x = 10
x = 20
```

MIR có thể biểu diễn logical local:

```text
Local x
```

và optimizer sau đó có thể chuyển thành:

```text
x0 = 10
x1 = 20
```

Nếu cần.

Điều này giúp ownership analyzer và Drop dễ làm việc hơn.

---

# 4. MIR Basic Block

Cấu trúc:

```text
BasicBlock {
    id
    params
    instructions
    terminator
}
```

Ví dụ:

```text
bb0:
    v0 = CONST 10
    BRANCH condition, bb1, bb2

bb1:
    v1 = CONST 20
    JUMP bb3

bb2:
    v2 = CONST 30
    JUMP bb3

bb3:
    v3 = PHI(v1, v2)
    RETURN v3
```

MIR CFG phải rõ ràng, không dựa vào AST nesting.

---

# 5. Value và Place

Đây là distinction cực kỳ quan trọng.

## Value

Một giá trị:

```text
42
User(...)
pointer
enum
tuple
```

## Place

Một vị trí có thể chứa giá trị:

```text
x
x.field
array[i]
*deref
```

Ví dụ:

```axiom
x.name = "A"
```

MIR:

```text
p0 = FIELD_PLACE x, name
v0 = CONST "A"
STORE p0, v0
```

Không được coi `x.name` đơn giản là một temporary value.

Ownership và alias analysis cần Place.

---

# 6. Place Projection

MIR place:

```text
Place {
    base
    projections[]
}
```

Projection:

```text
Field(FieldId)
Index(ValueId)
Deref
Downcast(VariantId)
```

Ví dụ:

```text
user.address.city
```

thành:

```text
Place(
    user,
    Field(address),
    Field(city)
)
```

Điều này cho phép region analyzer biết chính xác vùng nhớ.

---

# 7. MIR Instruction Set v0.1

Core:

```text
CONST
COPY
MOVE

LOAD
STORE

FIELD_PLACE
INDEX_PLACE
DEREF_PLACE

AGGREGATE
EXTRACT
INSERT

CAST
BIT_CAST
CONVERT

VIEW
VIEW_MUT

ALLOC
DEALLOC

DROP
DROP_IF_OWNED

CALL
DYNAMIC_CALL

PHI

BOUNDS_CHECK

ENUM_TAG
ENUM_PAYLOAD

ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS

LOCK
UNLOCK

SPAWN
SEND
RECEIVE

SUSPEND
RESUME

PANIC
TRAP
```

Terminator:

```text
JUMP
BRANCH
SWITCH
RETURN
UNREACHABLE
```

---

# 8. Không có `ALLOCA`

Tôi đề xuất **không có `ALLOCA` trong MIR**.

Lý do:

`let` không đồng nghĩa stack allocation.

Ví dụ:

```axiom
let x = Vec2 { ... }
```

có thể trở thành:

```text
register
```

hoặc:

```text
stack
```

hoặc:

```text
inline field
```

Do đó:

```text
ALLOC
```

chỉ xuất hiện khi semantic storage operation thực sự tồn tại.

---

# 9. `ALLOC` không nhất thiết là heap

Ví dụ:

```text
ALLOC size=1024
```

chỉ có nghĩa:

> tạo một storage region với ownership/lifetime semantics tương ứng.

Lowering sau này quyết định:

```text
stack
heap
arena
pool
static
device
custom allocator
```

Điều này tiếp tục giữ nguyên nguyên tắc:

> Storage strategy không phải ordinary type semantics.

---

# 10. `DEALLOC`

MIR:

```text
DEALLOC allocation
```

không đồng nghĩa source-level:

```text
free()
```

Nó biểu diễn **memory lifetime ending**.

Allocator backend có thể:

```text
free
arena no-op
pool return
stack lifetime marker
```

---

# 11. Drop là instruction riêng

Không được biến Drop thành:

```text
CALL destructor
```

ngay từ đầu.

MIR phải giữ:

```text
DROP place
```

Ví dụ:

```text
DROP_IF_OWNED x
```

Sau đó Drop elaboration/backend có thể biến thành:

```text
CALL File.close_internal
DEALLOC ...
```

hoặc tối ưu hoàn toàn.

Lý do: verifier cần biết đây là **semantic destruction**, không phải một function call bình thường.

---

# 12. Move cũng phải là instruction riêng

```text
MOVE x
```

không phải:

```text
LOAD x
STORE y
```

ngay lập tức.

Semantic:

```text
x → MOVED
y → OWNED
```

Backend sau này có thể biến nó thành:

```text
register move
pointer move
memcpy
nothing
```

---

# 13. Copy cũng riêng

```text
COPY x
```

khác:

```text
MOVE x
```

và khác:

```text
CLONE x
```

`CLONE` thực tế thường chỉ là:

```text
CALL clone_method
```

nhưng semantic type system đã quyết định nó là explicit duplication.

---

# 14. View trong MIR

Ví dụ:

```axiom
let v = view(buffer)
```

MIR:

```text
v = VIEW buffer
```

và verifier có:

```text
CapabilityFact {
    owner: buffer
    region: buffer
    access: READ
}
```

Không nên chỉ encode:

```text
v = ptr(buffer)
```

vì như vậy verifier mất semantic capability.

---

# 15. `VIEW_MUT`

```text
v = VIEW_MUT buffer
```

Verifier phải chứng minh:

```text
no conflicting READ
no conflicting WRITE
valid owner
valid provenance
valid lifetime
```

Sau Verified MIR, capability metadata có thể được erase.

---

# 16. Capability không nhất thiết tồn tại runtime

Ví dụ:

```text
let v = view(array)
sum(v)
```

sau optimization có thể biến thành:

```text
pointer + length
```

hoặc thậm chí:

```text
direct loop over array
```

hoặc:

```text
no view object at all
```

Capability là **compile-time semantic concept**.

---

# 17. MIR verifier

Verified MIR là checkpoint bắt buộc.

```text
MIR
 │
 ▼
Verifier
 │
 ├── ownership
 ├── initialization
 ├── capability
 ├── region
 ├── drop
 ├── concurrency
 ├── atomic
 ├── type
 └── control flow
 │
 ▼
Verified MIR
```

Sau checkpoint:

> Optimizer được phép mạnh hơn, nhưng không được làm mất observable semantics.

---

# 18. Verified MIR invariants

Ví dụ verifier phải đảm bảo:

```text
VOWN-01
No read of moved place.

VOWN-02
No double move.

VOWN-03
No use of uninitialized place.

VOWN-04
No invalid partial ownership state.

VCAP-01
Every capability has valid provenance.

VCAP-02
No conflicting live capabilities.

VCAP-03
No capability outlives owner.

VCAP-04
No capability crosses forbidden suspension.

VDROP-01
Every required resource is dropped exactly once.

VDROP-02
Moved resources are not dropped.

VMEM-01
Every memory access has valid type/alignment/lifetime semantics.

VCTRL-01
Every reachable block has valid terminator.

VCTRL-02
All PHI inputs dominate correctly.

VTYPE-01
Every MIR value has canonical TypeId.
```

---

# 19. Ownership verification phải trước optimization

Không:

```text
MIR
 ↓
aggressive optimizer
 ↓
ownership verification
```

Mà:

```text
MIR
 ↓
semantic verification
 ↓
Verified MIR
 ↓
optimizer
```

Nếu optimizer được chạy trước semantic verification, bug compiler có thể che khuất violation.

---

# 20. Optimizer có verifier riêng

Sau optimization:

```text
Verified MIR
    ↓
Optimization
    ↓
Optimized MIR
    ↓
Lightweight semantic verifier
```

Không nhất thiết chạy full expensive analysis mỗi lần, nhưng phải kiểm tra invariants cần thiết.

---

# 21. HIR → MIR lowering

Ví dụ source:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

MIR:

```text
bb0:
    v0 = LOAD a
    v1 = LOAD b
    v2 = ADD_CHECKED v0, v1
    RETURN v2
```

Có thể sau này optimizer:

```text
v2 = ADD v0, v1
```

nếu semantics phù hợp.

---

# 22. Struct access

Source:

```axiom
let x = user.age
```

MIR:

```text
p0 = FIELD_PLACE user, age
v0 = LOAD p0
```

Nếu move:

```axiom
let age = user.age
```

MIR:

```text
p0 = FIELD_PLACE user, age
v0 = MOVE p0
```

Ownership state:

```text
user.age → MOVED
```

---

# 23. Assignment

Source:

```axiom
user.age = 20
```

MIR:

```text
p0 = FIELD_PLACE user, age
v0 = CONST 20
STORE p0, v0
```

Nếu field cũ có Drop:

```text
DROP p0
STORE p0, v0
```

hoặc lowering có thể dùng replacement semantics tương đương.

Điều này phải được specification hóa, không để backend tự đoán.

---

# 24. Bounds checking

Source:

```axiom
let x = a[i]
```

MIR:

```text
p0 = INDEX_PLACE a, i
BOUNDS_CHECK i, len(a)
v0 = LOAD p0
```

Optimizer có thể chứng minh:

```text
0 <= i < len(a)
```

và xóa:

```text
BOUNDS_CHECK
```

nhưng không được thay đổi semantics.

---

# 25. `if`

Source:

```axiom
if x > 0 {
    10
} else {
    20
}
```

MIR:

```text
bb0:
    v0 = LOAD x
    v1 = CONST 0
    v2 = CMP_GT v0, v1
    BRANCH v2, bb1, bb2

bb1:
    v3 = CONST 10
    JUMP bb3

bb2:
    v4 = CONST 20
    JUMP bb3

bb3:
    v5 = PHI(v3, v4)
    RETURN v5
```

---

# 26. `match`

Không giữ pattern matching ở MIR.

HIR:

```text
match x {
    A => ...
    B(v) => ...
}
```

MIR:

```text
tag = ENUM_TAG x
SWITCH tag
```

Sau đó:

```text
ENUM_PAYLOAD
```

để lấy payload.

---

# 27. `for`

`for` phải biến mất trước MIR.

Ví dụ:

```axiom
for x in items {
    process(x)
}
```

HIR lowering thành iterator protocol.

MIR cuối cùng chỉ còn:

```text
loop
CALL next
BRANCH
...
```

hoặc optimizer trực tiếp hạ thành index loop.

---

# 28. `?`

Source:

```axiom
let x = foo()?
```

MIR semantic:

```text
v0 = CALL foo
tag = RESULT_TAG v0
BRANCH tag, success, failure

success:
    x = RESULT_VALUE v0
    ...

failure:
    cleanup
    RETURN error
```

Do đó `?` không cần exception machinery.

---

# 29. Async

Async source:

```axiom
async fn f() {
    let x = get().await
    process(x)
}
```

trước MIR phải lower thành state machine:

```text
State0
State1
State2
```

MIR:

```text
SUSPEND
RESUME
```

và state machine representation.

Điều quan trọng:

> ownership analyzer chạy trước/đồng thời với async lowering đủ để xác định giá trị nào có thể sống qua suspension.

---

# 30. Atomic

Source:

```axiom
atomic.store(1, Release)
```

MIR:

```text
ATOMIC_STORE
    address
    value
    ordering=Release
```

Không hạ thành ordinary STORE ở MIR.

Optimizer/backend chịu trách nhiệm target-specific lowering.

---

# 31. Dynamic dispatch

Source:

```axiom
let x: dyn Display = ...
x.display()
```

MIR:

```text
DYNAMIC_CALL
    data
    dispatch
    method_slot
```

Trong static generic:

```axiom
fn print<T: Display>(x: T)
```

MIR có thể trực tiếp:

```text
CALL FunctionId
```

Sau monomorphization.

---

# 32. Generic

MIR không nên giữ generic abstraction quá lâu.

Ví dụ:

```text
fn max<T: Ord>(...)
```

sau monomorphization:

```text
max_i32
max_f64
...
```

hoặc specialization tương ứng.

Nhưng trước monomorphization, MIR vẫn có:

```text
TypeParam
TraitObligation
```

để compiler quản lý semantic instantiation.

---

# 33. Closure

Closure:

```axiom
let f = |x| x + a
```

MIR:

```text
closure_env = AGGREGATE { a }
closure_fn  = FunctionId(...)
```

Nếu capture `a` bằng value:

```text
MOVE a
```

Nếu read capture:

```text
VIEW a
```

Nhưng sau optimization closure có thể hoàn toàn biến mất.

---

# 34. MIR không chứa source-level ownership annotations

MIR không nên có:

```text
&'a
borrow<'a>
lifetime_token
```

Thay vào đó:

```text
MOVE
COPY
VIEW
VIEW_MUT
DROP
```

cùng verifier facts.

Đây là cách giữ MIR đơn giản.

---

# 35. Memory effects

Mỗi instruction nên có effect metadata nội bộ:

```text
ReadMemory
WriteMemory
Allocate
Deallocate
Atomic
Call
ControlFlow
```

Ví dụ:

```text
LOAD
    ReadMemory

STORE
    WriteMemory

CALL
    Unknown/Declared effects

ATOMIC_CAS
    AtomicRead + AtomicWrite
```

Optimizer dùng nó để reorder/inlining/alias analysis.

---

# 36. Call effect

Đây là một điểm cần chốt.

Axiom **không cần một effect-system ở source language v1.0**.

Nhưng compiler vẫn cần internal call effects.

Ví dụ:

```text
CallEffects {
    reads_memory
    writes_memory
    allocates
    may_panic
    may_suspend
    may_block
    atomic
}
```

Đây là **compiler metadata**, không phải programmer-facing type system.

Như vậy ta không làm ngôn ngữ phức tạp hơn.

---

# 37. `black_box`

Intrinsic:

```text
black_box(x)
```

có semantic value bình thường nhưng optimizer coi là barrier thích hợp.

Ví dụ benchmark:

```axiom
let x = compute()
black_box(x)
```

Optimizer không được đơn giản hóa `x` chỉ vì nó không thấy observable use theo mô hình thông thường.

---

# 38. MIR Debug Mapping

Mỗi MIR instruction cần có:

```text
InstrId
Span
Origin
```

Ví dụ:

```text
Instr 182
source span:
    main.ax:15:9-15:20

origin:
    MethodCall → FunctionId 42
```

Điều này rất quan trọng cho:

```text
debugger
profiler
compiler diagnostics
AI agent
Oracle
```

---

# 39. MIR Serialization

Tôi đề xuất có một canonical text format:

```text
axiom-mir 0.1

fn main() -> unit {
bb0:
    v0 = CONST 42 : i32
    CALL print(v0)
    RETURN
}
```

Và binary format:

```text
.amir
```

cho incremental compilation/debugging.

Canonical serialization phải deterministic.

Cùng semantic input:

```text
compiler A
compiler B
```

phải tạo cùng canonical MIR nếu các implementation option không ảnh hưởng semantics.

---

# 40. MIR Hash

Mỗi MIR function có:

```text
SemanticMIRHash
```

dùng cho:

```text
incremental compilation
cache
Oracle
reproducible build
cross-check compiler
```

Hash không được phụ thuộc:

```text
memory address
arena pointer
random ID
thread scheduling
```

---

# 41. Verified MIR là contract

Từ đây compiler module có dependency:

```text
frontend
   ↓
MIR
   ↓
verifier
   ↓
VerifiedMIR
   ↓
optimizer
```

Optimizer **không được nhận raw MIR**.

Chỉ:

```text
VerifiedMIR
```

Điều này tạo boundary cực sạch.

---

# 42. Repository

```text
compiler/mir/
├── value.ax
├── place.ax
├── instruction.ax
├── terminator.ax
├── block.ax
├── cfg.ax
├── builder.ax
├── lowering.ax
├── serialize.ax
├── hash.ax
└── tests/

compiler/verifier/
├── control_flow.ax
├── types.ax
├── ownership.ax
├── capability.ax
├── memory.ax
├── drop.ax
├── concurrency.ax
├── atomic.ax
├── verifier.ax
└── tests/
```

---

# 43. Milestone MIR-001

Không bắt đầu optimizer ngay.

Trước tiên phải làm một **MIR interpreter tối thiểu**.

Pipeline:

```text
Source
 ↓
Parser
 ↓
Resolver
 ↓
Typed HIR
 ↓
Ownership
 ↓
MIR
 ↓
Verifier
 ↓
MIR Interpreter
```

MIR interpreter này cực kỳ quan trọng cho Oracle/differential testing.

Test:

```text
const
local
move
copy
field
load/store
branch
loop
call
return
drop
array
bounds
enum
match
result/option
```

---

# 44. MIR-002 — Verified MIR

Test negative:

```text
invalid CFG
invalid PHI
use-after-move
double-drop
invalid capability
dangling view
invalid memory access
invalid atomic ordering
invalid return
```

Verifier phải reject trước interpreter/backend.

---

# 45. MIR-003 — Differential Execution

Khi có:

```text
Oracle
MIR Interpreter
Native Backend
```

chúng ta có:

```text
Program
  │
  ├── Oracle
  │
  ├── MIR Interpreter
  │
  └── Native executable
```

So sánh:

```text
return value
stdout
stderr
panic
trap
resource events
atomic events
```

Đây sẽ là **hệ thống chống compiler bug** quan trọng nhất của Axiom.

---

# 46. Sau MIR: Semantic Optimizer

Thứ tự tiếp theo tôi khuyến nghị:

```text
MIR-001
MIR representation

MIR-002
Verified MIR

MIR-003
MIR interpreter

MIR-004
Oracle differential testing

OPT-001
constant folding
dead code
copy propagation
CFG simplification

OPT-002
SROA
scalar replacement
aggregate elimination

OPT-003
inlining
devirtualization

OPT-004
bounds-check elimination

OPT-005
escape/allocation elimination

OPT-006
alias analysis

OPT-007
loop optimization
vectorization

LIR-001
Axiom LIR
```

---

## Một quyết định tôi muốn chốt ở đây

Axiom nên có **Verified MIR như “semantic firewall”**:

```text
              UNTRUSTED
                  │
                  ▼
Source ──► Typed HIR ──► MIR
                         │
                         ▼
                  ┌─────────────┐
                  │   VERIFIER  │
                  └──────┬──────┘
                         │
                    VERIFIED MIR
                         │
              ╔══════════╧══════════╗
              ▼                     ▼
          OPTIMIZER              ORACLE
              │
              ▼
             LIR
              │
              ▼
        Machine Backend
```

**Frontend chịu trách nhiệm hiểu ý định và kiểm tra semantic. Verifier chịu trách nhiệm chứng minh MIR hợp lệ. Optimizer được phép cực kỳ hung hãn sau firewall.**

Đây là nền tảng phù hợp với mục tiêu của Axiom: **ngôn ngữ không cần đơn giản hóa vì sợ compiler khó; compiler có thể phức tạp bên trong nhưng semantic boundary phải rõ ràng.**

### Bước kế tiếp

Sau MIR, phần đáng làm tiếp theo là **AXIOM OPTIMIZER v0.1** — nhưng trước khi tối ưu, ta nên chốt một thứ nền tảng hơn: **Axiom LIR v0.1 và target-independent calling/memory model**, để xác định chính xác MIR sẽ hạ xuống machine code như thế nào mà không bị khóa vào x86-64 quá sớm.