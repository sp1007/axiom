# BOOTSTRAP-280 — AXIOM HIR → MIR LOWERING & CONTROL-FLOW CONSTRUCTION
## FROZEN / COMPLETED

Đây là bước chuyển rất quan trọng:

```text
Typed HIR
    ↓
Semantic Lowering
    ↓
MIR + CFG
    ↓
Ownership / Capability / Drop Verification
```

Từ BOOTSTRAP-280 trở đi, compiler không còn chủ yếu “hiểu source code” nữa. Nó bắt đầu xây dựng một representation đủ chính xác để **chứng minh chương trình an toàn trước khi tối ưu**.

---

# 1. Mục tiêu

MIR phải:

- explicit control flow;
- explicit evaluation order;
- explicit temporaries;
- explicit Move/Copy;
- explicit Drop;
- explicit capability operations;
- explicit calls;
- explicit branches;
- explicit suspension points;
- không còn overload ambiguity;
- không còn generic inference;
- không còn name lookup;
- không phụ thuộc AST.

Nguyên tắc:

> **MIR không được suy đoán lại semantics mà HIR đã xác định.**

---

# 2. Pipeline

```text
AST
 ↓
Resolved HIR
 ↓
Typed HIR
 ↓
Semantic Elaboration
 ↓
MIR Builder
 ↓
CFG Construction
 ↓
Drop Elaboration
 ↓
Ownership/Capability Lowering
 ↓
MIR Validation
 ↓
Verified MIR
```

---

# 3. MIR là gì?

MIR = **Mid-level Intermediate Representation**.

Nó phải đủ thấp để:

- dataflow analysis;
- ownership verification;
- capability analysis;
- liveness;
- escape analysis;
- effect analysis;
- async lowering;
- GPU legality;
- optimization preparation

có thể hoạt động.

Nhưng chưa thấp đến:

- register allocation;
- instruction selection;
- machine ABI.

---

# 4. MIR function

Đề xuất:

```text
MirFunction {
    function_id: FunctionId
    signature: MirSignature
    locals: LocalTable
    blocks: BasicBlockTable
    entry: BasicBlockId
    return_local: LocalId
    scopes: ScopeTable
    suspension_points: SuspensionPointTable
    source_map: MirSourceMap
}
```

---

# 5. Basic Block

Mỗi BasicBlock:

```text
BasicBlock {
    id: BasicBlockId
    statements: [Statement]
    terminator: Terminator
}
```

Invariant:

> Một basic block luôn kết thúc bằng đúng một terminator.

---

# 6. Statement

Core:

```text
Statement =
    Assign(Place, RValue)
    StorageLive(LocalId)
    StorageDead(LocalId)
    Drop(Place)
    MakeView(...)
    MakeMutView(...)
    EndCapability(...)
    BeginUnsafe(...)
    EndUnsafe(...)
    Nop
```

Một số operation có thể được biểu diễn bằng `Assign`.

---

# 7. Terminator

```text
Terminator =
    Goto(BasicBlockId)

    SwitchInt {
        discr: Operand
        targets: ...
    }

    SwitchEnum {
        discr: Operand
        targets: ...
    }

    Call {
        target: FunctionId
        args: [...]
        destination: Place
        next: BasicBlockId
        unwind: optional BasicBlockId
    }

    Return

    Unreachable

    Panic

    Suspend {
        future: Operand
        resume: BasicBlockId
        suspend: BasicBlockId
    }
```

GPU/async/foreign operations có thể mở rộng terminator set khi cần.

---

# 8. RValue

```text
RValue =
    Use(Operand)
    UnaryOp(...)
    BinaryOp(...)
    Aggregate(...)
    Field(...)
    Index(...)
    Cast(...)
    Bitcast(...)
    MakeView(...)
    MakeMutView(...)
    Load(...)
    AtomicLoad(...)
    ComptimeValue(...)
```

---

# 9. Operand

```text
Operand =
    Copy(Place)
    Move(Place)
    Constant(ConstValue)
```

Đây là một quyết định cực kỳ quan trọng.

```text
Copy(x)
Move(x)
```

là semantic information cho verifier.

Không có nghĩa compiler phải phát ra machine copy/move.

---

# 10. Place

MIR Place:

```text
Place {
    base: LocalId
    projections: [Projection]
}
```

Projection:

```text
Projection =
    Field(FieldId)
    Index(LocalId)
    Deref
    Downcast(VariantId)
    Subslice(...)
```

Ví dụ:

```ax
user.address.city
```

có thể trở thành:

```text id="u7l5sd"
_local0
    .address
    .city
```

---

# 11. Place tree

Ownership verifier nhìn vào:

```text id="7p6jws"
x
├── field_a
├── field_b
└── field_c
```

Do đó:

```ax
consume(x.a)
use(x.b)
```

có thể hợp lệ nếu struct không có custom Drop restriction.

---

# 12. Lowering expression

Mỗi HIR expression được lower thành:

```text
lower_expr(expr) -> Operand / Place / ControlFlow
```

Nhưng không phải expression nào cũng trả về một `Operand`.

Ví dụ:

```text id="l5j95g"
if
match
loop
return
```

tạo CFG.

---

# 13. Expression destination

Để tránh temporary không cần thiết, MIR builder dùng:

```text
lower_expr_into(expr, destination: Place)
```

Ví dụ:

```ax
let x = foo()
```

thay vì:

```text
tmp0 = foo()
x = tmp0
```

có thể trực tiếp:

```text
Call foo → x
```

nếu semantics cho phép.

---

# 14. CFG của `if`

Source:

```ax
if cond {
    a()
} else {
    b()
}

c()
```

MIR:

```text
BB0:
    t0 = cond
    SwitchInt t0
        true  → BB1
        false → BB2

BB1:
    Call a()
    Goto BB3

BB2:
    Call b()
    Goto BB3

BB3:
    Call c()
    Return
```

---

# 15. `if` expression

```ax
let x = if cond {
    10
} else {
    20
}
```

MIR:

```text
BB0:
    t0 = cond
    SwitchInt t0
        true → BB1
        false → BB2

BB1:
    x = 10
    Goto BB3

BB2:
    x = 20
    Goto BB3

BB3:
    ...
```

Không cần phi node ở MIR.

SSA phi sẽ được tạo sau.

---

# 16. `match`

Source:

```ax
match value {
    Some(x) => foo(x),
    None => bar(),
}
```

MIR:

```text
BB0:
    discr = discriminant(value)
    SwitchEnum discr
        Some → BB1
        None → BB2

BB1:
    x = project(value, Some.0)
    Call foo(x)
    Goto BB3

BB2:
    Call bar()
    Goto BB3

BB3:
    ...
```

Pattern semantics đã được quyết định ở HIR.

---

# 17. Nested match

Compiler không được tạo CFG kiểu spaghetti.

Mỗi nested construct phải tạo:

```text
entry
body
exit
```

với explicit block IDs.

CFG builder quản lý:

```text
ControlFlowContext
LoopContext
MatchContext
CleanupContext
```

---

# 18. `loop`

Source:

```ax
loop {
    work()

    if done {
        break
    }
}
```

MIR:

```text
BB0:
    Goto BB1

BB1:
    Call work()
    t0 = done
    SwitchInt t0
        true  → BB2
        false → BB1

BB2:
    ...
```

---

# 19. `break`

`break` không trực tiếp “return”.

Nó target tới loop exit:

```text
LoopContext {
    loop_id
    header
    continue_target
    break_target
    result_destination?
}
```

---

# 20. `continue`

```text
continue
```

→:

```text
Goto(loop.continue_target)
```

Không cần semantic lookup nữa.

---

# 21. Loop expression

Axiom có thể hỗ trợ:

```ax
let x = loop {
    if condition {
        break 42
    }
}
```

MIR:

```text
result_temp

header:
    ...

break:
    result_temp = 42
    goto exit

exit:
    use result_temp
```

Ownership verifier phải xử lý mọi break path.

---

# 22. `while`

```ax
while cond {
    body()
}
```

→ canonical CFG:

```text
header
  ↓
condition
 ├── false → exit
 └── true  → body
               ↓
             header
```

---

# 23. `for`

`for` trước tiên được semantic-elaborated thành iterator behavior.

Ví dụ:

```ax
for x in values {
    process(x)
}
```

Conceptually:

```text
iterator = into_iter(values)

loop:
    result = next(iterator)

    match result {
        Some(x) → process(x)
        None → exit
    }
```

MIR không cần biết syntax `for`.

---

# 24. `return`

Source:

```ax
return value
```

Không được lower trực tiếp thành:

```text
Return
```

nếu còn cleanup.

Compiler tạo:

```text
return_path
    ↓
cleanup chain
    ↓
Return
```

---

# 25. Cleanup chain

Ví dụ:

```ax
fn foo() {
    let a = A()
    let b = B()

    return x
}
```

MIR semantic:

```text
return:
    Drop(b)
    Drop(a)
    Return
```

theo reverse initialization order.

---

# 26. Early return

```ax
{
    let a = A()

    if condition {
        return
    }

    work()
}
```

CFG:

```text
BB0
 ├── condition → BB1
 │                 ↓
 │              Drop(a)
 │                 ↓
 │              Return
 │
 └── BB2
      ↓
    work()
      ↓
    Drop(a)
      ↓
    Return
```

Mọi exit path đều phải cleanup chính xác.

---

# 27. `break` cũng cleanup

```ax
loop {
    let x = Resource()

    if done {
        break
    }
}
```

`break` phải đi qua cleanup của loop-body scope:

```text
done
 ↓
Drop(x)
 ↓
loop_exit
```

---

# 28. `continue` cũng cleanup

```ax
loop {
    let x = Resource()

    if skip {
        continue
    }

    work()
}
```

→

```text
skip
 ↓
Drop(x)
 ↓
loop_header
```

---

# 29. Drop elaboration architecture

Không hard-code Drop tại từng lowering rule.

Đề xuất:

```text
HIR
 ↓
CFG skeleton
 ↓
Scope map
 ↓
Drop elaborator
 ↓
cleanup CFG
```

Điều này tránh bug khi có:

- return;
- break;
- continue;
- panic;
- unwind;
- async suspension.

---

# 30. Drop ladder

Mỗi scope:

```text
ScopeId
 ├── owned locals
 ├── initialization order
 └── parent scope
```

Cleanup:

```text
current scope
 ↓
reverse initialized locals
 ↓
parent cleanup
 ↓
exit
```

---

# 31. Partial initialization

Ví dụ:

```ax
let x: Struct = ...
```

nếu constructor có thể fail giữa chừng, MIR phải thể hiện initialization state đủ để verifier biết field nào initialized.

Không được:

```text
Drop(x)
```

mù quáng nếu `x` chưa initialized.

---

# 32. Partial move

Ví dụ:

```ax
let x = Struct { a, b }

consume(x.a)
use(x.b)
```

MIR:

```text
Move(x.a)
Copy/Read(x.b)
```

Ownership state:

```text
x
├── a = Moved
└── b = Owned
```

Nếu Struct có custom Drop:

```text
partial move
```

bị reject theo rule đã frozen.

---

# 33. Move path

MIR verifier dùng MovePath:

```text
MovePath {
    root: Place
    children: [...]
}
```

Ví dụ:

```text
x
├── a
│   ├── p
│   └── q
└── b
```

cho phép field-sensitive ownership.

---

# 34. Capability lowering

Source:

```ax
view(x)
```

MIR:

```text
v = MakeView {
    owner: x
    region: x
    access: READ
}
```

Source:

```ax
mut_view(x)
```

→:

```text
v = MakeMutView {
    owner: x
    region: x
    access: WRITE
}
```

Verifier sau đó cấp CapabilityId.

---

# 35. Capability lifetime

MIR phải có điểm:

```text
EndCapability(v)
```

khi capability không còn được sử dụng.

Compiler có thể đặt cuối cùng semantic use thay vì lexical scope nếu an toàn.

Điều này rất quan trọng cho performance.

Ví dụ:

```ax
let v = view(x)
use(v)
expensive_work()
mutate(x)
```

Compiler có thể kết thúc capability sau `use(v)`:

```text
use(v)
EndCapability(v)

expensive_work()
mutate(x)
```

→ giảm thời gian lock/alias restriction.

---

# 36. Relocation barrier

Nếu:

```ax
let v = view(vec)
vec.push(x)
```

và `push` có thể relocate storage:

```text
live view
    ↓
relocation
```

không hợp lệ.

MIR:

```text
MakeView(v, vec)
Call Vec::push(vec)
```

Verifier thấy capability còn live → reject hoặc yêu cầu capability end trước đó.

---

# 37. Evaluation order

Source:

```ax
foo(a(), b())
```

MIR giữ thứ tự xác định:

```text
t0 = Call a()
t1 = Call b()
Call foo(t0, t1)
```

Optimizer chỉ được reorder nếu EffectInfo chứng minh observable semantics không đổi.

---

# 38. Temporaries

Temporary lifetime phải được xác định semantic.

Ví dụ:

```ax
foo(make_resource())
```

MIR có thể:

```text
t0 = Call make_resource()
Call foo(t0)
Drop(t0)
```

Nếu `foo` consumes `t0`:

```text
Call foo(Move(t0))
```

không Drop lần nữa.

---

# 39. Discarded value

```ax
foo()
```

nếu trả về owning resource nhưng không dùng:

```text
t0 = Call foo()
Drop(t0)
```

nếu semantic type yêu cầu Drop.

Không silently leak.

---

# 40. Calls

MIR call:

```text
Call {
    target: CallableTarget
    args
    destination?
    normal_target
    unwind_target?
}
```

Target có thể:

```text
Direct(FunctionId)
Indirect(FunctionValue)
Dynamic(DynDispatchId)
Foreign(FfiFunctionId)
Intrinsic(IntrinsicId)
```

---

# 41. Generic calls

Generic arguments đã được resolve ở HIR.

MIR chỉ giữ:

```text
FunctionId
GenericInstanceId
```

Không gọi Trait Solver ở MIR.

---

# 42. Dynamic dispatch

Nếu HIR đã xác định:

```text
dyn Trait
```

MIR giữ dynamic dispatch boundary:

```text
DynamicCall {
    trait_method
    receiver
    object
}
```

Backend sau này mới quyết định vtable representation.

---

# 43. No implicit virtual dispatch

MIR không được tự biến:

```text
Call concrete_fn
```

thành dynamic dispatch.

Ngược lại cũng vậy.

---

# 44. `?` lowering

Source:

```ax
let x = read()?
```

MIR:

```text
result = Call read()

SwitchEnum result
    Ok  → BB_ok
    Err → BB_err

BB_ok:
    x = extract Ok
    goto continuation

BB_err:
    e = extract Err
    cleanup current scope
    return propagated error
```

---

# 45. `panic`

Semantic panic:

```text
Panic(message)
```

được lower tùy profile:

```text
abort
unwind
custom panic handler
```

MIR semantics vẫn phải giữ panic boundary.

---

# 46. Unreachable

Sau:

```ax
panic()
```

control flow:

```text
Panic
```

terminates execution.

Compiler có thể:

```text
Unreachable
```

sau khi semantics đã được preserved.

---

# 47. Unsafe operations

Ví dụ:

```ax
unsafe {
    *p
}
```

MIR:

```text
LoadRawPointer {
    pointer: p
    contract: UnsafeBoundaryId
}
```

Không được biến unsafe operation thành ordinary safe Load mà mất provenance.

---

# 48. Raw pointer → view

Nếu unsafe code:

```ax
let v = unsafe { view_from_raw(p, len) }
```

MIR phải lưu contract:

```text
TrustedCapability {
    provenance
    region
    length
    alignment
    initialized
    alias_contract
}
```

Sau đó verifier tiếp tục kiểm tra downstream usage.

---

# 49. Atomic operations

Source:

```ax
atomic.load()
```

MIR:

```text
AtomicLoad {
    place
    ordering
    scope
}
```

Không biến thành ordinary Load.

Tương tự:

```text
AtomicStore
AtomicRmw
CompareExchange
```

---

# 50. Volatile

Volatile riêng biệt:

```text
VolatileLoad
VolatileStore
```

Không được optimizer đối xử như ordinary memory operation.

---

# 51. Synchronization

Mutex:

```ax
lock.acquire()
```

MIR có thể:

```text
Call MutexAcquire
```

nhưng semantic guard:

```text
guard
```

là ownership-bearing value.

Drop:

```text
Drop(guard)
```

→ unlock.

---

# 52. Async suspension

Source:

```ax
let x = foo().await
```

MIR trước async state-machine lowering:

```text
future = Call foo()

Suspend {
    future
    resume = BB_resume
}
```

Tại suspension:

```text
live locals
```

phải được xác định.

---

# 53. Live-across-await

Ví dụ:

```ax
let data = acquire()
let result = foo().await
use(data)
```

`data` sống qua await.

Verifier cần biết:

```text
data live across suspension
```

và kiểm tra:

- Send nếu task migration;
- storage stability;
- capability restrictions;
- sync guards.

---

# 54. View qua await

Nếu:

```ax
let v = view(x)
await foo()
use(v)
```

mặc định reject nếu `v` không có explicit contract cho phép sống qua suspension.

Lý do:

```text
x
 ↓
view
 ↓
await
 ↓
potential migration / mutation / relocation
```

Không cho compiler đoán.

---

# 55. Closure lowering

Closure:

```ax
let f = |x| x + offset
```

MIR conceptual:

```text
env.offset = offset

closure_function(env, x):
    return x + env.offset
```

Nếu compiler chứng minh closure non-escaping, environment có thể bị scalarized/eliminated sau này.

---

# 56. Closure capture semantics

HIR đã xác định:

```text
ByValue
ByView
ByMutView
```

MIR giữ semantic capture mode.

Verifier kiểm tra:

```text
capture lifetime
alias
ownership
Send
Share
```

---

# 57. No mandatory closure heap

MIR:

```text
ClosureEnv
```

không có nghĩa:

```text
malloc
```

Optimizer có thể:

```text
stack
register
inline
scalarize
```

hoặc eliminate hoàn toàn.

---

# 58. Comptime

Compile-time expression đã được evaluate.

MIR runtime chỉ nhận:

```text
Constant
```

nếu kết quả materialize vào runtime.

Ví dụ:

```ax
const N = comptime compute_size()
```

runtime không cần execute `compute_size()`.

---

# 59. GPU kernel

GPU MIR giữ domain metadata:

```text
ExecutionDomain::GPU
StorageDomain::Device
```

và các restrictions.

Host→device launch:

```text
GpuLaunch {
    kernel
    args
    grid
    block
    completion
}
```

Không biến thành CPU call.

---

# 60. CFG invariants

Mỗi MIR function:

```text
exactly one entry block
every block has one terminator
all referenced blocks exist
no invalid block edge
return blocks have compatible return state
no reachable malformed block
```

Unreachable blocks có thể tồn tại trong intermediate construction nhưng production MIR phải canonicalize chúng.

---

# 61. Dominance

MIR cần CFG analysis:

```text
Dominators
PostDominators
Predecessors
Successors
Reachability
LoopInfo
```

Nhưng **không nhất thiết phải xây SSA ngay ở 280**.

SSA là stage sau.

---

# 62. MIR source mapping

Mỗi instruction/terminator:

```text
MirSourceInfo {
    source_span
    hir_node
    expansion_origin?
}
```

Ví dụ:

```text
Drop(x)
```

có thể có source origin:

```text
implicit cleanup generated for scope exit
```

để diagnostics/debugger hiểu.

---

# 63. MIR validation

Ngay sau lowering phải chạy:

```text
validate_mir_structure()
validate_places()
validate_types()
validate_cfg()
validate_terminators()
validate_source_mapping()
```

Ownership/capability verifier là bước tiếp theo.

---

# 64. MIR builder architecture

```text id="qv3w4h"
MirBuilder {
    function
    current_block
    local_map
    scope_stack
    loop_stack
    match_stack
    cleanup_stack
    suspension_points
    source_map
}
```

Các context stack này không phải semantic runtime state; chỉ là compiler construction state.

---

# 65. Cleanup context

```text
CleanupContext {
    scope_id
    parent
    initialized_locals
    cleanup_block
}
```

Compiler có thể share cleanup blocks khi semantics cho phép, tránh CFG explosion.

---

# 66. Avoid CFG explosion

Ví dụ nhiều `return`:

```ax
if a { return 1 }
if b { return 2 }
if c { return 3 }
return 4
```

Không nhất thiết tạo toàn bộ cleanup chain duplicate.

Có thể tạo:

```text
cleanup_return
```

và truyền return value qua designated local.

---

# 67. Return slot

Function:

```ax
fn foo() -> LargeStruct
```

MIR:

```text
return_local: _ret
```

Các branch:

```text
_ret = value
goto cleanup_return
```

sau đó:

```text
cleanup
Return(_ret)
```

ABI lowering sau này quyết định:

- registers;
- hidden sret;
- caller allocation.

---

# 68. Caller allocation

MIR không ép:

```text
return value
```

phải tạo heap temporary.

Large value có thể được constructed trực tiếp vào destination:

```text
Call foo → destination
```

Đây là nền tảng cho:

> zero-copy / move-elision / caller-allocated returns.

---

# 69. Semantic Move elision

Source:

```ax
let x = make()
```

HIR semantic:

```text
result ownership transferred
```

MIR có thể:

```text
Call make → x
```

thay vì:

```text
tmp = make
Move(tmp) → x
```

Nếu observable semantics giống nhau.

---

# 70. MIR không phải optimizer

Không thực hiện:

```text
CSE
DCE
LICM
Inlining
Vectorization
Scalar replacement
```

ở đây.

Chỉ được thực hiện **semantic lowering simplifications** không thay đổi meaning.

---

# 71. MIR semantic canonicalization

Có thể:

```text
normalize trivial goto
remove empty blocks
canonicalize switch
merge equivalent cleanup paths
```

nếu không làm mất source mapping/semantic facts.

---

# 72. MIR type invariants

Mỗi:

```text
Place
Operand
RValue
Call
Return
Cast
```

phải type-check được.

Ví dụ:

```text
Assign(place: i32, value: f64)
```

không hợp lệ trừ khi HIR đã tạo Cast.

---

# 73. No implicit coercion in MIR

Nếu HIR:

```text
i32 → i64
```

không hợp lệ:

```text
MIR
```

không được tự thêm conversion.

Mọi semantic conversion phải xuất hiện trước MIR.

---

# 74. MIR ownership boundary

Sau BOOTSTRAP-280:

```text
Typed HIR
    ↓
MIR
```

MIR đã có:

```text
Copy
Move
Drop
StorageLive
StorageDead
MakeView
MakeMutView
```

để BOOTSTRAP-135/verification có đủ dữ liệu.

---

# 75. MIR capability boundary

Verifier có thể xây:

```text
CapabilityState {
    capability_id
    owner
    region
    access
    valid
    lifetime
}
```

từ MIR.

Không cần đọc AST.

---

# 76. MIR effect boundary

Mỗi instruction có thể được classify:

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
```

Effect analysis ở task sau sử dụng MIR này.

---

# 77. MIR → Verified MIR

Chính xác:

```text
HIR
 ↓
MIR
 ↓
Structural validation
 ↓
Ownership verification
 ↓
Capability verification
 ↓
Concurrency verification
 ↓
Async verification
 ↓
GPU verification
 ↓
Effect verification
 ↓
Verified MIR
```

**Chỉ Verified MIR mới được tối ưu.**

---

# 78. Vì sao phải có boundary này?

Đây là điểm tôi muốn giữ rất chặt trong thiết kế Axiom.

Nếu compiler:

```text
MIR
 ↓
Optimization
```

trước khi chứng minh ownership/capability, optimizer có thể vô tình làm phức tạp việc chứng minh:

- alias;
- lifetime;
- move;
- drop;
- races.

Axiom thay vào đó:

```text
MIR
 ↓
PROVE
 ↓
Verified MIR
 ↓
OPTIMIZE
```

Điều này phù hợp trực tiếp với mục tiêu **hiệu năng cao nhưng không bắt programmer viết borrow checker syntax**.

---

# 79. Performance implication

Verification không có nghĩa runtime overhead.

Các facts như:

```text
NO_ALIAS
NO_ESCAPE
KNOWN_RANGE
EXCLUSIVE_WRITE
IMMUTABLE
```

sau verification có thể feed optimizer.

Ví dụ:

```ax
fn add(a: view<f32>, b: view<f32>, out: mut_view<f32>)
```

nếu verifier chứng minh:

```text
a ∩ b = ∅
a ∩ out = ∅
b ∩ out = ∅
```

optimizer có thể internalize:

```text
NoAlias(a,b,out)
```

và vectorize.

Programmer không cần viết `restrict`.

---

# 80. Compiler complexity vs programmer complexity

Đây là một trong những điểm cốt lõi của Axiom:

```text
C/C++:
Programmer
   ↓
must communicate alias/lifetime intent manually
```

Axiom:

```text
Programmer
   ↓
simple ownership-oriented source
   ↓
Compiler
   ├── inference
   ├── ownership analysis
   ├── capability analysis
   ├── escape analysis
   ├── alias analysis
   └── verification
```

Compiler phức tạp hơn.

**Ngôn ngữ không nhất thiết phải phức tạp hơn.**

---

# 81. Implementation structure

```text
compiler/
└── mir/
    ├── mod.ax
    ├── mir_id.ax
    ├── function.ax
    ├── block.ax
    ├── statement.ax
    ├── terminator.ax
    ├── rvalue.ax
    ├── operand.ax
    ├── place.ax
    ├── projection.ax
    ├── local.ax
    ├── scope.ax
    ├── cfg.ax
    ├── dominator.ax
    ├── loop.ax
    ├── cleanup.ax
    ├── drop_lowering.ax
    ├── capability_lowering.ax
    ├── async.ax
    ├── closure.ax
    ├── pattern.ax
    ├── ffi.ax
    ├── gpu.ax
    ├── validation.ax
    ├── provenance.ax
    ├── builder.ax
    └── tests/
```

---

# 82. Implementation order

```text
1. MirId
2. Local
3. Place
4. Projection
5. Operand
6. RValue
7. Statement
8. Terminator
9. BasicBlock
10. CFG
11. MirFunction
12. MirBuilder
13. expression lowering
14. block lowering
15. if lowering
16. match lowering
17. loop lowering
18. for lowering
19. return/break/continue
20. call lowering
21. ? lowering
22. closure lowering
23. async lowering
24. unsafe lowering
25. atomic/volatile lowering
26. GPU/FFI lowering
27. scope construction
28. cleanup graph
29. drop elaboration
30. capability elaboration
31. MIR validation
32. CompilerDB integration
33. snapshots
34. CFG property tests
35. adversarial ownership/control-flow tests
```

---

# 83. Test: nested cleanup

Bắt buộc test:

```ax
fn test() {
    let a = A()

    {
        let b = B()

        if condition {
            return
        }

        work()
    }

    final()
}
```

Phải chứng minh:

```text
return:
    Drop(b)
    Drop(a)

normal inner exit:
    Drop(b)

function exit:
    Drop(a)
```

Không double-drop.

---

# 84. Test: break + continue

```ax
loop {
    let x = Resource()

    if skip {
        continue
    }

    if done {
        break
    }

    use(x)
}
```

Cả hai nhánh:

```text
continue → Drop(x) → header
break    → Drop(x) → exit
```

---

# 85. Test: partial move

```ax
let x = Pair { a, b }

consume(x.a)

use(x.b)
```

phải hợp lệ nếu type/Drop rules cho phép.

Nhưng:

```ax
consume(x.a)
consume(x)
```

phải bị verifier reject.

---

# 86. Test: capability relocation

```ax
let v = view(vec)

use(v)

vec.push(x)
```

Nếu capability đã hết live tại `use(v)`:

```text
valid
```

Nếu:

```ax
let v = view(vec)

vec.push(x)

use(v)
```

→ reject nếu push có thể relocate.

---

# 87. Test: await

```ax
let v = view(x)

foo().await

use(v)
```

→ reject mặc định nếu view không được phép sống qua suspension.

---

# 88. Test: evaluation order

Các side effects phải giữ đúng order:

```ax
foo(a(), b())
```

MIR snapshot phải chứng minh:

```text
a
then b
then foo
```

---

# 89. Frozen invariants — BOOTSTRAP-280

```text
AMIR-20
Every production MIR function has exactly one entry block.

AMIR-21
Every basic block has exactly one terminator.

AMIR-22
All MIR block references resolve to valid BasicBlockIds.

AMIR-23
MIR uses typed compiler identifiers.

AMIR-24
MIR places use semantic LocalIds and FieldIds.

AMIR-25
MIR operands distinguish Copy from Move.

AMIR-26
Semantic Copy does not imply physical machine copy.

AMIR-27
Semantic Move does not imply physical machine move.

AMIR-28
MIR does not perform overload resolution.

AMIR-29
MIR does not perform generic type inference.

AMIR-30
MIR does not perform name resolution.

AMIR-31
MIR does not invent implicit coercions.

AMIR-32
All semantic coercions are explicit before or within validated lowering.

AMIR-33
MIR preserves source evaluation order.

AMIR-34
MIR preserves semantic ownership operations.

AMIR-35
MIR preserves capability creation and destruction semantics.

AMIR-36
MIR contains sufficient information for ownership verification.

AMIR-37
MIR contains sufficient information for capability verification.

AMIR-38
MIR contains sufficient information for Drop verification.

AMIR-39
Every reachable control-flow path has valid cleanup semantics.

AMIR-40
Return paths pass through required cleanup.

AMIR-41
Break paths pass through required cleanup.

AMIR-42
Continue paths pass through required cleanup.

AMIR-43
Panic/unwind paths respect configured cleanup semantics.

AMIR-44
Moved values are not implicitly dropped.

AMIR-45
Partially moved values are represented at place granularity.

AMIR-46
Custom-Drop restrictions are preserved.

AMIR-47
Capability lifetimes are represented sufficiently for verification.

AMIR-48
Live capabilities block incompatible relocation.

AMIR-49
MIR preserves unsafe boundaries.

AMIR-50
Unsafe operations do not erase provenance contracts.

AMIR-51
Atomic operations remain distinct from ordinary loads/stores.

AMIR-52
Volatile operations remain distinct from ordinary loads/stores.

AMIR-53
Synchronization semantics are preserved.

AMIR-54
Async suspension points are explicit.

AMIR-55
Values live across suspension remain identifiable.

AMIR-56
Closure capture semantics are preserved.

AMIR-57
GPU execution/storage domains remain explicit.

AMIR-58
FFI boundaries remain explicit.

AMIR-59
Comptime evaluation does not become implicit runtime execution.

AMIR-60
MIR does not require heap allocation for high-level constructs.

AMIR-61
MIR does not require GC.

AMIR-62
MIR does not require object headers.

AMIR-63
MIR does not require a monolithic runtime.

AMIR-64
MIR supports caller-allocated result construction.

AMIR-65
MIR permits physical move/copy elimination.

AMIR-66
MIR does not perform machine register allocation.

AMIR-67
MIR does not perform target instruction selection.

AMIR-68
MIR does not encode final ABI register classification.

AMIR-69
MIR source provenance remains available.

AMIR-70
Generated cleanup retains source and semantic provenance.

AMIR-71
MIR CFG construction is deterministic.

AMIR-72
MIR construction is independent of worker completion order.

AMIR-73
MIR structural validation precedes semantic verification.

AMIR-74
Invalid MIR cannot enter optimization.

AMIR-75
Only Verified MIR may enter optimization.

AMIR-76
MIR transformations preserve semantic types.

AMIR-77
MIR transformations preserve ownership semantics.

AMIR-78
MIR transformations preserve capability semantics.

AMIR-79
MIR transformations preserve evaluation order.

AMIR-80
MIR transformations preserve externally observable effects.

AMIR-81
MIR is independent of physical storage strategy.

AMIR-82
MIR does not determine stack versus heap placement.

AMIR-83
MIR does not determine register allocation.

AMIR-84
MIR does not determine vector register usage.

AMIR-85
MIR is target-independent unless an explicit semantic execution domain requires target facts.

AMIR-86
MIR lowering consumes Typed HIR semantic facts.

AMIR-87
MIR lowering must not rediscover source-level semantic meaning.

AMIR-88
MIR ownership state is analyzed by the authoritative verifier.

AMIR-89
MIR capability state is analyzed by the authoritative verifier.

AMIR-90
MIR is the semantic executable boundary before verification and optimization.
```

---

## Trạng thái

**BOOTSTRAP-280 — FROZEN / COMPLETED.**

Kiến trúc hiện tại:

```text
                 SOURCE
                   │
                   ▼
              Typed HIR
                   │
                   ▼
        ┌─────────────────────┐
        │     MIR Builder     │
        │ CFG + Places        │
        │ Copy/Move           │
        │ Cleanup             │
        │ Capability ops      │
        └──────────┬──────────┘
                   ▼
                  MIR
                   │
          ┌────────┴────────┐
          │                 │
     Structural         Semantic
     Validation         Verification
          │                 │
          └────────┬────────┘
                   ▼
              Verified MIR
                   │
                   ▼
                 SSA
                   │
                   ▼
               MemorySSA
                   │
                   ▼
                OptIR
```

**Bước tiếp theo: BOOTSTRAP-281 — AXIOM OWNERSHIP / INITIALIZATION / MOVE ANALYSIS ENGINE.**

Đây sẽ là một trong những task cốt lõi nhất của Axiom: xây dựng **ownership state machine + MovePath + definite initialization + partial move + exactly-once Drop + cleanup verification** trên MIR. Đây cũng là nơi chúng ta hiện thực hóa đúng mục tiêu trước đây của bạn: **không bắt programmer viết borrow checker/lifetime syntax, nhưng compiler vẫn có thể chứng minh memory safety và đồng thời tận dụng các proof để tối ưu hiệu năng.**