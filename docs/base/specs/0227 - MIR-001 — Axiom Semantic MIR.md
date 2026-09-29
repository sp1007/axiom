Tiếp tục với **MIR-001 — Semantic Middle Intermediate Representation**. Đây là một trong những phần quan trọng nhất của compiler Axiom, vì từ đây trở xuống compiler phải bắt đầu “nói chuyện” bằng semantics thay vì syntax.

# MIR-001 — Axiom Semantic MIR

## 1. Vai trò của MIR

MIR không phải AST tốt hơn.

MIR là nơi Axiom biểu diễn:

> **chương trình thực sự làm gì.**

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
Closure / Async analysis
  ↓
MIR
  ↓
Ownership / Capability / Concurrency verification
  ↓
Verified MIR
  ↓
Optimization
  ↓
ABI MIR
  ↓
LIR
```

AST/HIR quan tâm:

```text
"programmer viết gì?"
```

MIR quan tâm:

```text
"chương trình có semantics gì?"
```

---

# 2. MIR không chứa syntax sugar

Ví dụ source:

```text
v.length()
```

MIR không cần biết đây là method syntax.

Resolver đã biến nó thành:

```text
length(v)
```

sau trait/method resolution.

Tương tự:

```text
a ? b
```

hoặc:

```text
x?
```

sau này đều được hạ xuống control flow tương ứng.

---

# 3. MIR không chứa trait solving

Trait solver phải hoàn tất trước MIR verification.

Ví dụ:

```text
x + y
```

MIR không giữ:

```text
"hãy tìm impl Add"
```

mà giữ:

```text
CALL Add::add
```

hoặc direct concrete function nếu static dispatch.

Điều này cực kỳ quan trọng:

> **Optimizer không cần biết trait là gì.**

---

# 4. MIR cơ bản

MIR gồm:

```text
Function
 ├── Parameters
 ├── Locals
 ├── Blocks
 ├── Terminators
 └── Metadata
```

Ví dụ:

```text
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

có thể:

```text
fn add(a, b) -> i32 {
    block0:
        %t0 = add a, b
        return %t0
}
```

---

# 5. Block

Mỗi block có:

```text
Block {
    id
    instructions[]
    terminator
}
```

Một block chỉ có **một terminator**.

Ví dụ:

```text
block0:
    %x = const 10
    branch block1

block1:
    return %x
```

---

# 6. Terminator

Các terminator Core:

```text
return
branch
cond_branch
switch
call
invoke
unreachable
panic
trap
await
```

Có thể thêm:

```text
spawn
```

nhưng tôi đề xuất `spawn` ban đầu là instruction có terminator continuation bình thường, trừ khi ABI/runtime semantics yêu cầu khác.

---

# 7. Value và Place

Đây là quyết định rất quan trọng.

MIR phải phân biệt:

```text
Value
Place
```

### Value

Một giá trị đã được tính:

```text
42
%x
pointer
struct value
```

### Place

Một vị trí có thể chứa giá trị:

```text
x
obj.field
array[i]
*deref
```

Ví dụ:

```text
x.field = 10
```

không phải:

```text
field_value = 10
```

mà:

```text
place = projection(x, field)
store place, 10
```

---

# 8. Place expression

MIR có:

```text
Place =
    Local
    Deref
    Field
    Index
    Slice
    Downcast
```

Ví dụ:

```text
obj.a.b[i]
```

có thể là:

```text
Local(obj)
 → Field(a)
 → Field(b)
 → Index(i)
```

---

# 9. Vì sao Place quan trọng?

Ownership analysis không thể chỉ theo dõi biến.

Ví dụ:

```text
struct S {
    a: String
    b: String
}
```

Code:

```text
let x = s.a
```

phải hiểu:

```text
move s.a
```

chứ không phải:

```text
move s
```

Do đó MIR cần **projection-aware ownership**.

---

# 10. Partial move

Ví dụ:

```text
let a = s.a
use(s.b)
```

MIR:

```text
%a = move s.a
use(s.b)
```

Ownership state:

```text
s.a → MOVED
s.b → VALID
```

Không được coi toàn bộ `s` là moved.

---

# 11. Place tree

Compiler có thể duy trì:

```text
s
├── a   MOVED
├── b   VALID
└── c   VALID
```

Đây là semantic fact, không cần programmer biết.

---

# 12. Local

MIR locals:

```text
_local0
_local1
_return
_tmp0
```

Mỗi local có:

```text
Type
StorageClass
OwnershipState
DropState
```

nhưng OwnershipState chủ yếu nằm trong verifier/facts, không nhất thiết phải encode cứng vào mỗi instruction.

---

# 13. Không biến MIR thành borrow checker

Đây là nguyên tắc quan trọng.

MIR instruction không nên có:

```text
borrow_id = 123
lifetime = 'a
```

hoặc:

```text
borrow_region_foo
```

như Rust-style source semantics.

Thay vào đó:

```text
MIR
 +
Semantic Facts
```

verifier sử dụng:

```text
Ownership
Capability
Region
Provenance
```

---

# 14. Capability facts

Ví dụ:

```text
let v = view(x)
```

MIR:

```text
%v = make_view_read x
```

Facts engine ghi:

```text
Capability {
    id: C1
    owner: x
    region: Region(x)
    access: READ
}
```

Sau verification, nếu không cần nữa, metadata có thể bị erase.

---

# 15. `mut_view`

```text
let v = mut_view(x)
```

MIR:

```text
%v = make_view_write x
```

Facts:

```text
C2:
    owner = x
    region = Region(x)
    access = WRITE
    exclusive = true
```

Nếu tồn tại:

```text
view(x)
```

đồng thời:

```text
mut_view(x)
```

thì verifier phát hiện conflict.

---

# 16. Không cần runtime borrow object

Đây là điểm quan trọng.

```text
view<T>
```

không nhất thiết tạo runtime structure:

```text
struct View {
    ptr
    len
}
```

Nếu compiler biết:

```text
len
```

hoặc sử dụng trực tiếp slice representation:

```text
pointer + length
```

thì có thể optimize.

Trong nhiều trường hợp thậm chí:

```text
length → constant
```

và chỉ còn pointer.

---

# 17. MOVE

MIR:

```text
%x = move %place
```

Semantic:

```text
ownership(place) → x
place → moved
```

Không có nghĩa:

```text
memcpy
```

---

# 18. COPY

```text
%x = copy %place
```

Verifier kiểm tra:

```text
Type(place): Copy
```

Sau đó:

```text
%x
```

và source cùng tồn tại.

Optimizer có thể xóa physical copy.

---

# 19. LOAD

LOAD dùng khi cần đọc từ memory place:

```text
%x = load %place
```

Nhưng với aggregate lớn, MIR có thể tránh materialization.

Ví dụ:

```text
load field
```

thay vì:

```text
load entire struct
```

---

# 20. STORE

```text
store %place, %value
```

Verifier kiểm tra:

```text
place writable
capability valid
region valid
type compatible
```

---

# 21. DROP

```text
drop %place
```

nghĩa:

> kết thúc ownership/resource obligation.

Không nhất thiết:

```text
free(memory)
```

Drop implementation có thể:

```text
close(fd)
release refcount
deallocate resource
run user Drop
```

---

# 22. Drop elaboration

Source:

```text
{
    let a = A()
    let b = B()
}
```

MIR semantic ban đầu có thể chưa chứa toàn bộ Drop.

Sau Drop Elaboration:

```text
drop b
drop a
return
```

Reverse initialization order.

---

# 23. Early return

```text
fn f() {
    let a = A()
    if condition {
        return
    }
}
```

MIR phải biến thành:

```text
if condition:
    drop a
    return
```

Không được có đường thoát bỏ qua Drop.

---

# 24. Panic

Nếu:

```text
panic()
```

MIR:

```text
panic
```

hoặc:

```text
call panic_handler
```

tùy phase.

Nếu unwind profile:

```text
panic
 ↓
unwind edges
 ↓
cleanup blocks
```

Nếu abort:

```text
panic
 ↓
terminate
```

---

# 25. Result không phải control-flow exception

Ví dụ:

```text
let x = foo()?
```

MIR:

```text
%r = call foo()

switch %r:
    Ok(v)  → block_ok
    Err(e) → block_err

block_ok:
    %x = v

block_err:
    return Err(e)
```

Không có exception machinery.

---

# 26. `await`

Source:

```text
let x = foo().await
```

MIR semantic:

```text
%future = call foo()
%result = await %future
```

Sau async lowering:

```text
state machine
```

---

# 27. Async state machine

Ví dụ:

```text
async fn f() {
    let x = foo().await
    bar(x).await
}
```

Compiler tạo state:

```text
STATE_0
  call foo
  pending → STATE_1

STATE_1
  resume foo
  call bar
  pending → STATE_2

STATE_2
  resume bar
  complete
```

Nhưng đây là compiler-generated MIR.

Programmer không thấy.

---

# 28. View qua await

Nếu:

```text
let v = view(x)
await foo()
use(v)
```

compiler phải reject nếu capability có thể sống qua suspension mà storage không có contract phù hợp.

Nguyên tắc hiện tại:

> **ordinary view không được sống qua await.**

Owned value thì được.

---

# 29. ALLOC

MIR:

```text
%storage = alloc T
```

đây là **semantic allocation operation**, không phải:

```text
call malloc
```

Backend có thể biến thành:

```text
stack
arena
pool
heap
register
```

hoặc eliminate.

---

# 30. DEALLOC

Tương tự:

```text
dealloc %storage
```

không nhất thiết thành `free()`.

Ví dụ arena:

```text
drop object
```

có thể chỉ chạy destructor, còn memory giữ tới khi arena drop.

---

# 31. CALL

MIR call:

```text
%r = call @foo(%a, %b)
```

Metadata:

```text
callee
ABI
argument types
return type
calling convention
```

Trait đã resolve.

---

# 32. Direct vs indirect call

Direct:

```text
call @foo
```

Indirect:

```text
call %fnptr
```

Dynamic trait:

```text
call %vtable_slot
```

Nhưng dynamic dispatch phải được explicit source-level.

---

# 33. Devirtualization

Optimizer có thể:

```text
indirect call
      ↓
prove concrete type
      ↓
direct call
      ↓
inline
```

MIR không cần biết source ban đầu có `dyn Trait`.

---

# 34. BRANCH

```text
branch block3
```

Không có machine jump.

Backend sau này quyết định:

```text
jmp
je
jne
b.eq
...
```

---

# 35. SWITCH

Enum:

```text
match x {
    A => ...
    B => ...
    C => ...
}
```

MIR:

```text
switch_discriminant x
    0 → blockA
    1 → blockB
    2 → blockC
```

Optimizer có thể biến thành:

- jump table;
- binary tree;
- range check;
- direct branch.

---

# 36. `never`

Function:

```text
fn abort() -> never
```

MIR:

```text
call abort
unreachable
```

Compiler biết block sau call unreachable.

---

# 37. Atomic MIR

Không hạ atomic thành normal load/store.

Ví dụ:

```text
atomic_load p, Acquire
```

MIR:

```text
%v = atomic_load %p, Acquire
```

Optimizer phải preserve memory ordering.

---

# 38. Lock/Unlock

High-level:

```text
let guard = mutex.lock()
...
```

MIR có thể:

```text
%guard = lock %mutex
...
drop %guard
```

Drop elaboration biến:

```text
drop guard
```

thành semantic unlock.

Không nhất thiết phải có source-level:

```text
unlock
```

---

# 39. Channel

Channel:

```text
send(ch, value)
```

MIR:

```text
%r = channel_send %ch, move %value
```

Ownership verifier đảm bảo:

```text
value
```

không còn owned ở sender sau successful transfer.

Nếu send thất bại và `Result` trả ownership:

```text
Err(value)
```

ownership quay về caller.

---

# 40. Spawn

```text
spawn(task)
```

MIR:

```text
%handle = spawn move %task
```

Verifier kiểm tra task state:

```text
Send
```

nếu migration domain yêu cầu.

---

# 41. Execution Domain

MIR metadata có thể ghi:

```text
ExecutionDomain:
    CPU
    GPU
    Thread
    Fiber
    AsyncTask
```

Nhưng không phải mọi function đều phải có annotation.

Compiler suy luận từ context.

`@kernel` là explicit boundary.

---

# 42. Storage Domain

Tách riêng:

```text
ExecutionDomain
```

và:

```text
StorageDomain
```

Ví dụ:

```text
CPU thread
    ↓
DeviceBuffer
```

Execution = CPU.

Storage = GPU device memory.

Điều này rất quan trọng cho GPU/I/O/DMA.

---

# 43. MIR Type

MIR type system nên đơn giản hơn Typed HIR.

Ví dụ:

```text
Ty::I32
Ty::Struct(TypeId)
Ty::Enum(TypeId)
Ty::Array(Ty, N)
Ty::View(Ty)
Ty::MutView(Ty)
Ty::Ptr(...)
Ty::Fn(...)
Ty::DynTrait(...)
```

Generic type parameter nên đã được resolve/monomorphized trước codegen path.

---

# 44. MIR không cần toàn bộ type-level machinery

Không cần giữ:

```text
TraitSolver
GenericConstraintGraph
MethodLookup
```

trong MIR.

MIR chỉ giữ semantic result.

Đây làm optimizer nhanh và đơn giản hơn.

---

# 45. Semantic Facts Graph

MIR liên kết với:

```text
Facts {
    Ownership
    Capability
    Region
    Provenance
    Drop
    Send
    Share
    Suspension
    Unsafe
    ExecutionDomain
    StorageDomain
}
```

Ví dụ:

```text
Value #42
    owned_by = local #3

Capability #7
    provenance = local #3
    region = field #2
    access = READ
    valid_until = block #18
```

---

# 46. Nhưng Facts không phải runtime

Sau verification:

```text
Facts
  ↓
Optimization constraints
  ↓
erase
```

Nếu không còn observable semantic requirement.

---

# 47. Điều này giải quyết vấn đề bạn từng lo

Bạn từng lo:

> pointer/reference/borrow checker gây phiền phức cho programmer.

Axiom MIR có thể cực kỳ phức tạp:

```text
ownership graph
capability graph
region graph
escape graph
```

nhưng source vẫn đơn giản:

```text
let x = ...
foo(x)
```

**Compiler gánh complexity, programmer không gánh.**

---

# 48. MIR verifier

Tôi đề xuất một verifier chính:

```text
MIRVerifier
```

và các sub-verifier:

```text
OwnershipVerifier
CapabilityVerifier
DropVerifier
ConcurrencyVerifier
AsyncVerifier
UnsafeVerifier
ExecutionDomainVerifier
TypeVerifier
```

Chúng không nên là các hệ thống semantic hoàn toàn độc lập.

Chúng dùng chung:

```text
SemanticFactsEngine
```

---

# 49. Một instruction phải được verify theo nhiều dimension

Ví dụ:

```text
store p, x
```

có thể cần:

```text
Type:
    p : Place<T>
    x : T

Ownership:
    x valid

Capability:
    p has WRITE

Region:
    p valid

Concurrency:
    no conflicting access

ExecutionDomain:
    p accessible from current domain

Storage:
    storage still alive
```

Đây là lý do **Semantic Authority/Facts Engine** là một phần kiến trúc rất quan trọng.

---

# 50. MIR verifier không chạy sau optimization một lần duy nhất

Mỗi IR boundary cần verifier.

```text
HIR verifier
      ↓
MIR verifier
      ↓
Verified MIR
      ↓
optimization
      ↓
MIR verifier
      ↓
LIR verifier
      ↓
Machine verifier
      ↓
Object verifier
```

Optimization pass nào phá invariant:

> compiler bug, không phải “undefined behavior của chương trình”.

---

# 51. Optimization pass contract

Ví dụ:

```text
Pass: BoundsCheckElimination

Input:
    Verified MIR

Requires:
    RangeProof

Transforms:
    checked_index → unchecked_index

MustPreserve:
    MemorySafety
    TypeCorrectness
    CapabilityValidity

Output:
    Verified MIR
```

Điều này sau này cực kỳ hữu ích cho AI agent xây compiler.

---

# 52. MIR canonical form

Nên có một canonical MIR để:

- test;
- diff;
- cache;
- debug;
- AI phân tích;
- regression.

Ví dụ:

```text
fn add(i32, i32) -> i32
bb0:
    %2 = add %0, %1
    return %2
```

Không phụ thuộc memory address/compiler run.

---

# 53. Stable MIR serialization

Tôi đề xuất:

```text
.axmir
```

hoặc internal binary format:

```text
AXMIR
```

Không nhất thiết public API v1.

Nhưng compiler cần serialize được MIR cho:

- incremental compilation;
- cache;
- debugging;
- compiler testing.

---

# 54. MIR source mapping

Mỗi instruction có:

```text
SourceSpan
```

nhưng nhiều MIR instruction có thể map về cùng source expression.

Ví dụ:

```text
x?
```

có thể sinh 10 instructions.

Debugger vẫn phải hiểu:

```text
source line
```

không phải bắt programmer debug MIR.

---

# 55. MIR không target-specific

Không có:

```text
rax
rbx
xmm0
```

ở MIR.

Không có:

```text
mov
lea
cmp
```

MIR.

Những thứ đó thuộc Machine IR.

---

# 56. MIR cũng không có ABI register allocation

Ví dụ:

```text
return large_struct
```

MIR:

```text
return value
```

ABI lowering sau này quyết định:

```text
register
sret
stack
split
```

---

# 57. MIR → LIR

Sau semantic optimization:

```text
MIR
 ↓
ABI lowering
 ↓
LIR
```

LIR bắt đầu quan tâm:

```text
calling convention
aggregate layout
memory addressing abstraction
pointer representation
target-independent low-level operations
```

nhưng vẫn chưa có physical registers.

---

# 58. MIR instruction set đề xuất

Core:

```text
CONST
UNDEF
MOVE
COPY

LOAD
STORE

FIELD
INDEX
SLICE
DEREF

ALLOC
DEALLOC
DROP

ADD
SUB
MUL
DIV
REM

CMP
CAST
BITCAST

CALL
RETURN

BRANCH
COND_BRANCH
SWITCH

PANIC
TRAP
UNREACHABLE

AWAIT
SPAWN

ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
FENCE

LOCK
UNLOCK

CHANNEL_SEND
CHANNEL_RECV
```

Một số như `LOCK`, `CHANNEL_*` có thể được lower sớm hơn tùy runtime abstraction, nhưng semantic MIR giữ chúng đủ lâu để verifier hiểu semantics.

---

# 59. Đặc biệt: không quá nhiều instruction

Không nên biến MIR thành:

```text
300+ semantic opcodes
```

vì compiler sẽ trở nên khó duy trì.

Nguyên tắc:

> **MIR opcode chỉ tồn tại nếu optimizer/verifier cần hiểu semantic riêng của nó.**

Ví dụ `Vec.push` không cần MIR opcode.

Nó là function call/generic library code và optimizer có thể inline.

---

# 60. Frozen MIR architecture

Tôi đề xuất chốt:

```text
Axiom MIR
=
Control Flow
+
Typed Values
+
Places
+
Memory Operations
+
Ownership Operations
+
Resource Operations
+
Concurrency Operations
+
Suspension Operations
```

với semantics được kiểm soát bởi:

```text
Semantic Facts Engine
```

chứ không nhồi tất cả logic vào instruction.

---

# 61. Các invariant MIR

```text
AMIR-60 — MIR Represents Program Semantics

AMIR-61 — MIR Is Independent Of Source Syntax Sugar

AMIR-62 — Trait Resolution Completes Before MIR Verification

AMIR-63 — MIR Uses Explicit Places For Storage Access

AMIR-64 — Values And Places Are Distinct

AMIR-65 — Projection Is Ownership-Aware

AMIR-66 — Partial Moves Are Representable

AMIR-67 — MOVE Does Not Imply Physical Copy

AMIR-68 — COPY Is A Semantic Duplication Operation

AMIR-69 — DROP Represents Resource-Lifetime Completion

AMIR-70 — Drop Elaboration Preserves Deterministic Destruction

AMIR-71 — Capability Facts Are Separate From Runtime Objects

AMIR-72 — MIR Does Not Require Source-Level Lifetimes

AMIR-73 — MIR Does Not Require Borrow-Checker Syntax

AMIR-74 — Capability Validity Is Verified Before Optimization

AMIR-75 — Unknown Region Overlap Cannot Be Assumed Disjoint

AMIR-76 — Async Suspension Is Explicit In MIR

AMIR-77 — Await State Is Compiler-Generated

AMIR-78 — Atomic Operations Preserve Ordering Semantics

AMIR-79 — Volatile Operations Remain Observable

AMIR-80 — Execution And Storage Domains Are Distinct

AMIR-81 — MIR Is Target-Independent

AMIR-82 — ABI Lowering Occurs After Semantic Verification

AMIR-83 — MIR Contains No Physical Registers

AMIR-84 — MIR Contains No Target Instructions

AMIR-85 — Optimization Passes Must Preserve MIR Invariants

AMIR-86 — Every MIR Boundary Is Verifiable

AMIR-87 — Semantic Facts May Be Erased After Verification

AMIR-88 — Runtime Representation Is Not Implied By Semantic Opcode

AMIR-89 — MIR Serialization Must Be Deterministic

AMIR-90 — MIR Source Mapping Is Preserved

AMIR-91 — Compiler-Generated MIR Is Subject To The Same Verification

AMIR-92 — Safe MIR Cannot Represent Invalid Ownership State

AMIR-93 — Unsafe MIR Still Preserves Compiler-Tracked Facts

AMIR-94 — MIR Failure Is A Compiler Diagnostic Or ICE

AMIR-95 — MIR Opcode Exists Only When Its Semantic Distinction Is Required
```

---

# 62. Kiến trúc compiler hiện tại đã bắt đầu rất rõ

Ta hiện có:

```text
                    ┌──────────────┐
                    │    Source    │
                    └──────┬───────┘
                           ↓
                    Lexer / Parser
                           ↓
                         AST
                           ↓
                       Resolver
                           ↓
                         HIR
                           ↓
                     Typed HIR
                           ↓
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   Trait Solver       Async Analysis     Comptime
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ↓
                         MIR
                           ↓
                 Semantic Facts Engine
                           ↓
                    MIR Verification
                           ↓
                    Verified MIR
                           ↓
                     Optimization
                           ↓
                       ABI MIR
                           ↓
                         LIR
                           ↓
                    Target Legalization
                           ↓
                     Machine IR
                           ↓
                  Register Allocation
                           ↓
                    Machine Encoder
                           ↓
                       Object
                           ↓
                       Linker
```

Điểm quan trọng nhất:

> **Semantic Facts Engine nằm giữa frontend semantics và optimizer, nhưng không phải một “borrow checker” độc lập.**

Nó là nơi compiler hợp nhất ownership + capability + region + concurrency + async + execution/storage facts.

---

## Bước kế tiếp: `MIR-002 — Ownership & Capability Facts Engine`

Phần tiếp theo cần đi sâu hơn nữa, vì đây chính là **trái tim của ý tưởng “không borrow checker cho programmer nhưng compiler vẫn đảm bảo memory safety”**.

Ta sẽ thiết kế cụ thể:

```text
Fact
FactSet
FactGraph
OwnerId
ValueId
PlaceId
CapabilityId
RegionId
ProvenanceId
StorageId
LifetimePoint
AccessMode
Conflict
Disjointness
Escape
MoveState
DropState
```

và đặc biệt là **thuật toán compiler dùng để tự suy ra lifetime/alias mà không bắt người viết Axiom khai báo lifetime**.