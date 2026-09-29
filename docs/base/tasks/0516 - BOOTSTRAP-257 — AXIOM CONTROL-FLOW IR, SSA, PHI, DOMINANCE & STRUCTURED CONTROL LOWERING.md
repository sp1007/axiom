# BOOTSTRAP-257 — AXIOM CONTROL-FLOW IR, SSA, PHI, DOMINANCE & STRUCTURED CONTROL LOWERING

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là tầng biến control flow cấp ngôn ngữ thành một CFG đủ mạnh để compiler thực hiện:

- ownership verification
- Drop insertion
- capability analysis
- definite initialization
- async lowering
- loop optimization
- SSA
- MemorySSA
- vectorization
- register allocation

Nguyên tắc trung tâm:

> **Source control flow có cấu trúc; compiler IR có CFG tổng quát.**

Programmer không cần `goto`, nhưng compiler vẫn được phép có arbitrary CFG.

---

# 1. Hai tầng control flow

Axiom có:

```text
Source Control Flow
        ↓
Semantic CFG
        ↓
MIR CFG
        ↓
SSA / MemorySSA
        ↓
Machine CFG
```

Source:

```axiom
if condition {
    foo()
} else {
    bar()
}
```

không cần expose basic blocks.

Compiler có thể biểu diễn:

```text
BB0
 ├── true  → BB1
 └── false → BB2

BB1 ──→ BB3
BB2 ──→ BB3
```

---

# 2. BasicBlock

Mỗi BasicBlock gồm:

```text
BlockId
Parameters / PHI inputs
Statements*
Terminator
```

Terminator luôn kết thúc block.

---

# 3. Terminator

Core MIR hỗ trợ:

```text
Goto
Branch
Switch
Return
Unreachable
Panic
Call
Invoke
AwaitSuspend
```

và các dạng system/async/GPU mở rộng.

---

# 4. Không có fall-through semantic

Mỗi block phải có terminator.

Điều này làm CFG rõ ràng và dễ verify.

---

# 5. `if`

Source:

```axiom
if x > 0 {
    a()
} else {
    b()
}
```

semantic CFG:

```text
        BB0
         │
      condition
       /     \
    true     false
     ↓         ↓
   BB1       BB2
     │         │
     └────┬────┘
          ↓
        BB3
```

---

# 6. `if` là expression

```axiom
let x =
    if condition {
        10
    } else {
        20
    }
```

Compiler cần merge hai value.

Conceptual:

```text
BB1 → value 10
BB2 → value 20
       ↓
      BB3
```

SSA sẽ tạo:

```text
x = phi(10, 20)
```

---

# 7. PHI

PHI là compiler IR construct, **không phải Axiom source syntax**.

Nó biểu diễn:

> value nào được chọn phụ thuộc predecessor vừa đi qua.

---

# 8. PHI placement

PHI chỉ cần khi một SSA value có nhiều definitions từ các control-flow paths.

---

# 9. Dominance

Block `A` dominates `B` nếu mọi đường đi từ entry tới `B` đều đi qua `A`.

Compiler dùng dominance cho:

- SSA
- variable visibility
- code motion
- ownership
- initialization
- cleanup

---

# 10. Immediate Dominator

Mỗi block ngoài entry có immediate dominator:

```text
idom(B)
```

là dominator gần nhất của B.

Compiler xây:

```text
Dominator Tree
```

---

# 11. Post-dominance

Axiom cũng cần post-dominator analysis.

Đặc biệt hữu ích cho:

- cleanup
- return paths
- panic
- branch convergence
- control-dependent optimization

---

# 12. Ownership + dominance

Ví dụ:

```axiom
let x = make()

if condition {
    use(x)
}
```

`x` phải còn Owned/valid ở branch.

---

# 13. Drop + CFG

```axiom
let x = acquire()

if condition {
    return
}

use(x)
```

`return` không được bỏ qua Drop.

CFG phải có cleanup edge:

```text
return
  ↓
cleanup(x)
  ↓
exit
```

---

# 14. Multiple exits

Ví dụ:

```axiom
fn f() {
    let a = A()
    let b = B()

    if x {
        return
    }

    if y {
        return
    }

    use(a, b)
}
```

Compiler có thể canonicalize:

```text
return
   ↓
cleanup b
   ↓
cleanup a
   ↓
exit
```

---

# 15. Cleanup blocks

MIR có thể có:

```text
CleanupBlock
```

nhưng đây là implementation structure, không phải source concept.

---

# 16. Cleanup order

Theo frozen memory model:

> Drop theo reverse initialization order.

Ví dụ:

```text
a initialized
b initialized
c initialized
```

cleanup:

```text
drop c
drop b
drop a
```

---

# 17. Partial move

Compiler không thể drop moved field.

Ví dụ conceptual:

```text
p.x → moved
p.y → owned
```

cleanup chỉ drop `p.y`.

---

# 18. PHI + ownership

Ownership không thể chỉ là một scalar variable state.

Compiler phải track state theo CFG.

Ví dụ:

```text
BB1: x = A
     goto BB3

BB2: x = B
     goto BB3
```

Tại BB3:

```text
x = phi(A, B)
```

Ownership state:

```text
Owned(x)
```

vì mọi incoming path đều cung cấp ownership hợp lệ.

---

# 19. Một path moved

```text
BB1: x = A
     move x
     goto BB3

BB2: x = A
     goto BB3
```

BB3 không thể dùng `x` bình thường.

Verifier phải phát hiện trạng thái không hợp lệ.

---

# 20. Join semantics

Ownership dataflow join phải bảo thủ.

Ví dụ:

```text
Owned ⊔ Moved
```

không trở thành:

```text
Owned
```

mà phải trở thành trạng thái không cho phép unsafe use.

---

# 21. Initialization join

Tương tự:

```text
INIT ⊔ UNINIT
```

không được coi là INIT.

---

# 22. Capability join

Nếu một capability chỉ tồn tại trên một branch, successor không được giả định capability đó tồn tại trên tất cả paths.

---

# 23. Region facts

Compiler có thể giữ region facts nếu chúng valid trên tất cả incoming paths.

---

# 24. Loop

Source:

```axiom
loop {
    work()
}
```

CFG:

```text
       ┌──────────┐
       │  header  │
       └────┬─────┘
            ↓
          body
            │
            └──────→ header
```

---

# 25. Loop header

Loop header là điểm merge:

```text
entry
  ↓
header ← backedge
  ↓
body
```

Do đó PHI thường xuất hiện ở header.

---

# 26. Loop-carried value

Ví dụ:

```axiom
let mut x = 0

loop {
    x = x + 1

    if x >= 10 {
        break
    }
}
```

SSA conceptual:

```text
x0 = 0

header:
x1 = phi(x0, x2)

body:
x2 = x1 + 1
```

---

# 27. Loop condition

`while`:

```axiom
while condition {
    body()
}
```

canonicalize thành:

```text
header
   ↓
condition
 /       \
true     false
 ↓         ↓
body      exit
 ↓
header
```

---

# 28. `for`

Axiom `for` không có primitive iteration implementation riêng.

Nó lower qua iterator protocol:

```text
iterator = into_iter(collection)

loop:
    match iterator.next() {
        Some(x) => body
        None => exit
    }
```

Sau đó optimizer có thể eliminate abstraction.

---

# 29. `break`

`break` là edge tới loop exit.

```text
body
  │
  ├── normal → backedge
  │
  └── break → exit
```

---

# 30. `continue`

`continue` là edge về loop header hoặc canonical continue target.

---

# 31. Nested loops

Mỗi loop có:

```text
LoopId
Header
Body
ContinueTarget
BreakTarget
Exit
```

Resolver/parser không được nhầm `break` của inner loop với outer loop.

---

# 32. `break value`

Nếu Axiom hỗ trợ `break value` trong expression loop, compiler phải model loop result.

Ví dụ conceptual:

```text
loop {
    if ready {
        break value
    }
}
```

Loop exit nhận PHI của các break values.

---

# 33. `return`

`return value` semantic:

```text
evaluate value
↓
transfer ownership if necessary
↓
cleanup remaining locals
↓
function exit
```

---

# 34. Evaluation order

Return expression được evaluate **trước cleanup của enclosing locals**.

---

# 35. Ví dụ

```axiom
return make_result(x)
```

không được drop `x` trước khi result được tạo nếu semantics cần `x`.

---

# 36. `?`

Axiom:

```axiom
let x = foo()?
```

lower conceptual:

```text
tmp = foo()

switch tmp {
    Ok(v)  → continue
    Err(e) → return Err(e)
}
```

---

# 37. `?` ownership

Error value được move ra khỏi temporary/result theo ownership semantics.

Không implicit clone.

---

# 38. `?` + cleanup

Error path phải chạy cleanup:

```text
foo()
 ↓
Err
 ↓
cleanup locals
 ↓
return Err
```

---

# 39. `match`

`match` có thể lower thành:

```text
Switch
```

hoặc:

```text
decision tree
```

hoặc:

```text
conditional branches
```

depending on optimization.

---

# 40. Exhaustiveness trước lowering

Pattern exhaustiveness phải được verify trước khi CFG lowering thành machine-oriented representation.

---

# 41. Pattern guards

Guard được evaluate sau khi pattern match thành công.

---

# 42. Guard failure

Nếu guard false, control flow chuyển tới pattern candidate tiếp theo.

---

# 43. Match value ownership

Scrutinee ownership/capability được giữ theo semantics của pattern.

Không được implicitly clone chỉ vì nhiều pattern cần inspect.

---

# 44. Destructuring

Compiler có field-sensitive Place tree:

```text
value.a
value.b
value.c
```

---

# 45. Pattern move

Pattern có thể move field.

Ownership verifier nhận chính xác các Place đã consumed.

---

# 46. `panic`

Panic có semantic terminator:

```text
Panic(payload)
```

---

# 47. Panic profile

Runtime profile quyết định:

```text
abort
unwind
custom
```

nhưng source semantics vẫn phải xác định observable panic behavior.

---

# 48. Abort

Nếu profile abort:

```text
Panic
 ↓
runtime panic handler
 ↓
terminate
```

---

# 49. Unwind

Nếu profile unwind:

```text
Panic
 ↓
unwind edge
 ↓
cleanup
 ↓
caller unwind
```

---

# 50. Unwind cleanup

Ownership verifier phải đảm bảo resource cleanup chính xác trên unwind path.

---

# 51. `Unreachable`

Dùng cho:

```text
never-returning function
```

hoặc path compiler đã chứng minh unreachable.

---

# 52. Không được dùng unreachable để bỏ safety checking

Source:

```axiom
if impossible_condition {
    unsafe_invalid_code()
}
```

vẫn phải được semantic-check trong Complete Semantic Mode nếu code tồn tại trong configuration.

---

# 53. `@cfg`

Khác với runtime branch.

```axiom
@cfg(target_os = "windows")
fn foo() {}
```

Code không thỏa condition bị loại khỏi semantic program instance.

---

# 54. CFG simplification

Sau semantic checking:

```text
if true
```

có thể simplify.

---

# 55. Nhưng thứ tự

```text
parse
→ resolve
→ typecheck
→ ownership
→ verify
→ optimize
```

Không:

```text
constant-fold
→ bỏ code
→ không check code
```

---

# 56. SSA

Axiom dùng SSA ở OptIR.

Mỗi SSA value có một definition.

---

# 57. MIR không nhất thiết SSA

MIR giữ semantic places vì ownership/drop/capability cần place identity.

Do đó:

```text
MIR
→ SSA
```

là lowering sau verification.

---

# 58. Tại sao không SSA ngay?

Vì:

```text
x.field
x[i]
move x.a
drop x.b
```

cần place tree semantics.

SSA thuần value-level không đủ thuận tiện để biểu diễn ownership semantics.

---

# 59. OptIR SSA

Sau semantic verification:

```text
Place
↓
SSA values
```

với MemorySSA cho những storage locations vẫn memory-resident.

---

# 60. Promotable memory

Nếu address không escape:

```text
alloca x
load
store
```

có thể promote thành SSA.

---

# 61. Non-promotable memory

Nếu:

```text
volatile
atomic
FFI
escaped pointer
stable address
```

thì không thể tùy tiện promote.

---

# 62. PHI vs Memory PHI

SSA value:

```text
phi(v1, v2)
```

MemorySSA:

```text
MemoryPhi(M1, M2)
```

Hai khái niệm riêng.

---

# 63. MemorySSA

Theo dõi:

```text
MemoryDef
MemoryUse
MemoryPhi
```

---

# 64. MemoryDef

Ví dụ:

```text
store x = 5
```

tạo memory definition.

---

# 65. MemoryUse

```text
load x
```

uses current memory state.

---

# 66. MemoryPhi

Branch merge:

```text
       BB1 → store a
      /
entry
      \
       BB2 → store a

        ↓
       BB3
```

BB3 cần MemoryPhi.

---

# 67. Dominance + MemorySSA

MemorySSA dựa trên dominance để xác định memory definition gần nhất hợp lệ.

---

# 68. Critical edge

CFG edge:

```text
block with multiple successors
        ↓
block with multiple predecessors
```

là critical edge.

---

# 69. Critical-edge splitting

Optimizer có thể split:

```text
A → B
```

thành:

```text
A → EdgeBlock → B
```

để chèn:

- PHI-related operations
- instrumentation
- cleanup
- profiling

---

# 70. Không thay đổi semantics

Critical-edge splitting là semantic-preserving CFG transformation.

---

# 71. Loop canonicalization

Optimizer tạo canonical loop:

```text
preheader
header
body
latch
exit
```

---

# 72. Preheader

Nơi đặt loop-invariant computations.

---

# 73. Latch

Canonical backedge target.

---

# 74. Loop analysis

`LoopInfo` phải track:

```text
LoopId
Header
Latch
Exits
NestedLoops
TripCount
InductionVariables
```

khi chứng minh được.

---

# 75. Trip count

Không được giả định.

Có thể derive từ:

```text
range
bounds
constant
scalar evolution
```

---

# 76. Range-based loop

```axiom
for i in 0..n {
    use(a[i])
}
```

compiler có thể derive:

```text
0 <= i < n
```

và eliminate bounds check.

---

# 77. Overflow matters

Nếu induction variable có overflow semantics khác nhau, optimizer phải respect numeric model.

---

# 78. Không được áp dụng C-style UB assumption

Axiom đã định nghĩa integer overflow.

Optimizer phải dùng Axiom semantics.

---

# 79. Function call

MIR call:

```text
Call {
    callee
    args
    destination
    effects
}
```

---

# 80. Call may return

Normal call:

```text
caller → callee → continuation
```

---

# 81. Call may panic

Nếu panic profile unwind:

```text
call
 ├── normal continuation
 └── unwind cleanup
```

---

# 82. Call effects

Call carries:

```text
Read
Write
Allocate
Drop
Atomic
IO
Panic
Synchronize
Foreign
```

as applicable.

---

# 83. Pure call

Nếu compiler chứng minh:

```text
Pure
No Panic
No External Effect
```

có thể inline/CSE/remove khi result unused.

---

# 84. But `pure` is semantic fact

Không được tự gắn pure chỉ vì function “trông như pure”.

---

# 85. Async

`await` là special control-flow boundary.

```axiom
let x = future.await
```

conceptual:

```text
poll future

Ready(v)
    ↓
continue

Pending
    ↓
suspend
```

---

# 86. Suspension edge

MIR có:

```text
AwaitSuspend {
    future
    suspension_point
    resume
}
```

---

# 87. Await không phải function call bình thường

Nó có thể chia function execution thành nhiều resume segments.

---

# 88. Live values across await

Chỉ values còn cần sau await trở thành Future state fields.

---

# 89. Dead values

Nếu value không được dùng sau await:

→ không đưa vào state machine.

---

# 90. Capability across await

`view`/`mut_view` mặc định không được sống qua await trừ explicit storage/execution contract.

---

# 91. Async CFG

```text
        poll
       /    \
   Ready    Pending
     │         │
 continue   suspend
               │
            executor
               │
             resume
```

---

# 92. Cancellation

Cancellation không phải panic.

Compiler không được map:

```text
cancel
→ panic
```

về semantics.

---

# 93. Future Drop

Dropping Future chạy ordinary Drop semantics.

External operation cancellation cần explicit contract.

---

# 94. Spawn

`spawn(future)` tạo execution boundary.

Compiler checks:

```text
Future: Send
captured state
lifetime
effects
```

---

# 95. Structured concurrency

Task tree có thể được represented ở runtime layer.

Core CFG chỉ cần semantics của Future/control flow.

---

# 96. Closures

Closure invocation:

```text
call closure
```

có thể lower thành:

```text
static direct call
+
environment
```

hoặc dynamic dispatch nếu `dyn Fn`.

---

# 97. Closure + CFG

Closure body có CFG riêng.

Capture state được ownership verifier kiểm tra độc lập.

---

# 98. Recursion

Recursive function tạo call edge runtime.

CFG của function vẫn finite.

---

# 99. Tail call

Tail-call optimization được phép khi:

- ABI cho phép
- observable semantics preserved
- Drop obligations completed
- stack/unwind semantics preserved

---

# 100. Tail call không phải semantic guarantee mặc định

Axiom có thể có explicit tail-call attribute về sau.

---

# 101. GPU control flow

GPU CFG cũng dùng cùng semantic model.

Nhưng backend có thể cần:

```text
uniform branch
divergent branch
predication
reconvergence
```

---

# 102. GPU divergence

Compiler có thể transform branch thành predication nếu semantics preserved.

---

# 103. Barrier-sensitive CFG

GPU barrier là synchronization operation.

Compiler không được move code qua barrier nếu phá synchronization semantics.

---

# 104. Atomic-sensitive CFG

Atomic ordering restricts CFG motion.

---

# 105. Volatile-sensitive CFG

Volatile operations retain observable ordering requirements.

---

# 106. Exception/unwind edges

Axiom không có C++ exception model.

Nhưng `panic = unwind` vẫn tạo exceptional CFG edges nếu profile yêu cầu.

---

# 107. Cleanup graph

Compiler nên xây riêng:

```text
NormalCFG
CleanupCFG
```

hoặc một unified CFG có edge kinds:

```text
NORMAL
UNWIND
CLEANUP
SUSPEND
RESUME
```

Khuyến nghị:

> **Unified CFG + typed edge kinds.**

---

# 108. Vì sao?

Ownership/drop/capability cần nhìn toàn bộ control-flow graph.

Không nên có một CFG “thật” và một CFG cleanup hoàn toàn khác nhau.

---

# 109. Edge kind

Conceptual:

```text
CFGEdge {
    source
    target
    kind
}
```

`kind`:

```text
Normal
BranchTrue
BranchFalse
SwitchCase
Backedge
Break
Continue
Return
Unwind
Cleanup
Suspend
Resume
```

---

# 110. Dominance không phải mọi edge đều giống nhau

Đặc biệt unwind/suspend có semantics khác normal execution.

Analysis phải hiểu edge kind.

---

# 111. Definite initialization

Dataflow:

```text
IN[BB]
   ↓
transfer
   ↓
OUT[BB]
```

Join phải conservative.

---

# 112. Ownership

Tương tự:

```text
Owned
Moved
PartiallyMoved
Dropped
```

---

# 113. Capability

Track:

```text
CapabilityId
Provenance
Region
Access
Validity
```

---

# 114. Escape

Backward analysis cần CFG/post-dominance để xác định lifetime/escape.

---

# 115. Drop elaboration

Compiler pipeline:

```text
Typed MIR
 ↓
Ownership verification
 ↓
Drop elaboration
 ↓
Verified MIR
```

Drop insertion không được chạy trước khi ownership facts đầy đủ.

---

# 116. Drop elaboration example

Source:

```axiom
fn f() {
    let a = A()
    if condition {
        return
    }
    use(a)
}
```

MIR:

```text
entry
 ↓
a = A()
 ↓
branch
 ├── return → drop(a) → exit
 └── use(a) → drop(a) → exit
```

---

# 117. Drop flags

Compiler có thể cần internal drop flags cho partially initialized/moved aggregates.

Nhưng:

> **Drop flags không phải bắt buộc runtime field.**

---

# 118. Static analysis eliminates flags

Nếu compiler chứng minh state luôn initialized:

→ không cần physical drop flag.

---

# 119. Dynamic flag

Chỉ khi runtime state thực sự cần.

---

# 120. This is another zero-cost principle

Semantic complexity:

```text
partial initialization
```

không đồng nghĩa runtime overhead.

---

# 121. SSA construction

Axiom có thể dùng:

```text
Dominance Frontier
```

để place PHI nodes.

Hoặc dùng sealed-block SSA construction trong incremental compiler.

---

# 122. Recommendation

Compiler v1:

> **Use a robust sealed-block / dominance-aware SSA builder rather than forcing classical Cytron construction everywhere.**

Lý do:

- incremental compilation
- easier local construction
- better interaction with mutable MIR
- easier debug
- suitable for CompilerDB revisions.

---

# 123. SSA value identity

Mỗi SSA definition có:

```text
ValueId
TypeId
SourceSpan
DefBlock
DebugInfo
```

---

# 124. PHI incoming

```text
Phi {
    result
    incoming: [(BlockId, ValueId)]
}
```

---

# 125. PHI correctness

Mỗi predecessor phải cung cấp đúng semantic type.

---

# 126. PHI ownership

PHI không tạo physical copy.

Nó chỉ chọn incoming SSA value.

---

# 127. PHI Drop

Compiler không drop every incoming value independently.

Ownership is associated with semantic value/control-flow state.

---

# 128. This matters

Nếu:

```text
BB1 → A
BB2 → B
BB3 → phi(A,B)
```

thì chỉ value đã chọn tiếp tục sống.

Incoming alternatives không được double-drop.

---

# 129. SSA + Move

Move semantics được represented trước SSA.

SSA lowering không thay đổi ownership meaning.

---

# 130. Memory locations

Memory-resident objects remain represented through MemorySSA.

---

# 131. Alias + CFG

A store on one path can invalidate load assumptions on a merge.

Compiler uses MemorySSA + AliasInfo.

---

# 132. Example

```text
if cond {
    *p = 1
}

x = *p
```

Nếu compiler không biết `cond` false/true effect:

load after merge depends on possible store.

---

# 133. If `p` noalias

Alias facts narrow affected memory.

---

# 134. If `p` volatile

Load/store remains observable.

---

# 135. If `p` atomic

Memory ordering becomes part of dependency.

---

# 136. If FFI call occurs

Potential memory clobber depends on FFI contract.

---

# 137. CFG optimization

Allowed:

```text
block merge
block split
jump threading
branch folding
switch lowering
tail duplication
loop rotation
loop unswitching
if conversion
predication
```

only under semantic legality.

---

# 138. Jump threading

Can bypass known branches if condition proven.

---

# 139. Tail duplication

May duplicate pure/side-effectful code only if observable behavior and cost constraints permit.

---

# 140. Branch elimination

Only when condition is semantically proven.

---

# 141. Switch lowering

`match` can become:

```text
jump table
binary search
decision tree
bit test
conditional chain
```

---

# 142. Pattern semantics remain unchanged

Representation is backend concern.

---

# 143. CFG and debug info

Every transformed block/value must retain source provenance.

---

# 144. Debug stepping

Debugger should map optimized machine instructions back to:

```text
SourceSpan
HIR node
MIR instruction
SSA value
```

where possible.

---

# 145. AI tooling

`ax explain cfg` can expose:

```text
block
predecessors
successors
dominators
ownership state
capabilities
cleanup
effects
```

---

# 146. Example diagnostic

```text
AXCFG-E001

value `x` is moved on one control-flow path
but used after the paths merge.

Path A:
    x → Move

Path B:
    x remains Owned

At merge:
    ownership state is not uniformly valid.

Suggested fixes:
    move the use before the branch
    or explicitly clone `x`
```

---

# 147. Another diagnostic

```text
AXCFG-E002

`view<T>` remains live across a possible storage relocation.

Source:
    let v = view(buffer)

Potential relocation:
    buffer.push(...)

The compiler cannot prove that relocation is impossible.
```

---

# 148. CFG verification invariant

Compiler must verify:

```text
entry reachable
terminator exists
all successors valid
no malformed predecessor
```

---

# 149. Unreachable blocks

Can exist temporarily during transformations.

Before codegen:

→ either eliminate or mark proven unreachable.

---

# 150. No malformed CFG reaches backend

Backend receives structurally valid CFG only.

---

# 151. CFG normalization boundary

Recommended:

```text
Typed MIR
 ↓
CFG normalization
 ↓
Ownership/Capability verification
 ↓
Drop elaboration
 ↓
Verified MIR
 ↓
SSA
```

---

# 152. Important correction to earlier conceptual pipeline

Ownership verification should not depend on SSA.

Correct:

```text
MIR CFG
→ semantic dataflow
→ verification
→ SSA
```

not:

```text
source
→ SSA
→ ownership
```

---

# 153. Why?

SSA hides some semantic place relationships that ownership needs.

---

# 154. Compiler architecture

Add:

```text
CFGDB
DominanceDB
LoopDB
SSADB
CleanupDB
ControlFlowDB
```

---

# 155. IDs

```text
BlockId
EdgeId
PhiId
SsaValueId
LoopId
DomTreeNodeId
CleanupBlockId
SuspensionPointId
```

---

# 156. Core data structures

```text
BasicBlock {
    id
    statements
    terminator
}

CFGEdge {
    source
    target
    kind
}

FunctionCFG {
    entry
    blocks
    edges
    exits
}
```

---

# 157. Dominance

```text
DominatorTree {
    idom[]
    frontier[]
}
```

---

# 158. LoopInfo

```text
LoopInfo {
    header
    latches
    exits
    parent
    children
    depth
}
```

---

# 159. SSA

```text
SSAValue {
    id
    type
    definition
}

Phi {
    result
    incoming
}
```

---

# 160. MemorySSA

```text
MemoryDef
MemoryUse
MemoryPhi
```

---

# 161. Cleanup

```text
CleanupRegion {
    locals_to_drop
    capabilities_to_end
    outgoing_edges
}
```

---

# 162. Suspension

```text
SuspensionPoint {
    id
    live_values
    live_capabilities
    resume_block
    cancellation_contract
}
```

---

# 163. Verification order

Recommended:

```text
1. CFG structural verification
2. Definite initialization
3. Ownership
4. Capability
5. Drop
6. Escape
7. Send/Share
8. Await
9. GPU
10. FFI
11. Effect
12. Final Verified MIR
```

Một số analysis có thể chạy song song khi dependency graph cho phép.

---

# 164. Incremental compilation

Khi một block thay đổi:

CompilerDB không nhất thiết rebuild toàn function/backend.

Có thể invalidate:

```text
CFG
dominance
loop facts
ownership dataflow
SSA
optimization
```

theo dependency graph.

---

# 165. Determinism

Parallel analysis vẫn phải cho cùng:

```text
semantic result
diagnostic identity
CFG meaning
```

independent of worker scheduling.

---

# 166. Reference interpreter

`ax-ref` không cần dùng SSA.

Nó thực thi semantic control flow trực tiếp.

---

# 167. Differential testing

```text
ax-ref
   vs
ax-mir
   vs
SSA/OptIR
   vs
native
```

---

# 168. Async testing

Reference semantics:

```text
Ready
Pending
Resume
Cancel
Drop
```

phải match lowered state machine.

---

# 169. Panic testing

Test cả:

```text
normal return
early return
panic abort
panic unwind
```

---

# 170. Ownership adversarial tests

Đặc biệt:

```text
branch move
loop move
partial move
nested return
?
panic
unwind
await
closure
spawn
```

---

# 171. CFG + GPU tests

Test:

```text
divergence
barrier
atomic
return
discard
kernel exit
```

---

# 172. Frozen invariants

```text
ACFG-20
Every reachable basic block has exactly one terminator.

ACFG-21
Every CFG edge targets a valid basic block.

ACFG-22
CFG semantics are independent of physical instruction layout.

ACFG-23
Source structured control flow may lower to arbitrary compiler CFG.

ACFG-24
Compiler CFG need not expose goto to the programmer.

ACFG-25
Every source control-flow construct has deterministic semantic lowering.

ACFG-26
If-expressions merge values explicitly.

ACFG-27
PHI is an IR construct and not source-level syntax.

ACFG-28
PHI does not imply a physical copy.

ACFG-29
Ownership state is verified before SSA lowering.

ACFG-30
Initialization state is verified before SSA lowering.

ACFG-31
Capability state is verified before SSA lowering.

ACFG-32
MIR preserves semantic Place identity.

ACFG-33
SSA lowering may erase physical Place structure only after required semantic facts are established.

ACFG-34
Memory-resident values remain represented through MemorySSA where required.

ACFG-35
Dominance is deterministic.

ACFG-36
Every non-entry reachable block has a valid immediate dominator.

ACFG-37
Post-dominance is available for cleanup and control-dependent analysis.

ACFG-38
Ownership joins are conservative.

ACFG-39
INIT joined with UNINIT cannot become definitely initialized.

ACFG-40
OWNED joined with MOVED cannot become definitely owned.

ACFG-41
Capability facts at a merge must hold on all relevant incoming paths.

ACFG-42
Unknown capability validity is never treated as proven.

ACFG-43
Moved fields are not dropped.

ACFG-44
Uninitialized fields are not dropped.

ACFG-45
Cleanup executes on all required normal exits.

ACFG-46
Cleanup executes on required unwind exits.

ACFG-47
Cleanup ordering follows Axiom lifetime semantics.

ACFG-48
Return evaluates its return value before enclosing cleanup.

ACFG-49
Break performs required loop-scope cleanup.

ACFG-50
Continue performs required iteration-scope cleanup.

ACFG-51
`?` is lowered to deterministic branch control flow.

ACFG-52
`?` propagates ownership without implicit cloning.

ACFG-53
Match exhaustiveness is verified before final CFG lowering.

ACFG-54
Pattern ownership semantics are preserved through lowering.

ACFG-55
Loop backedges are explicit in CFG.

ACFG-56
Break targets the nearest valid enclosing loop.

ACFG-57
Continue targets the nearest valid enclosing loop continuation point.

ACFG-58
Loop-carried values require explicit SSA merge semantics after SSA lowering.

ACFG-59
Range-derived bounds facts may be used for optimization only after semantic verification.

ACFG-60
Integer overflow semantics constrain loop optimization.

ACFG-61
C-style undefined-overflow assumptions are forbidden.

ACFG-62
Panic is distinct from ordinary return.

ACFG-63
Panic abort and panic unwind are distinct execution profiles.

ACFG-64
Unwind edges are explicitly represented when required.

ACFG-65
Cleanup remains correct under panic unwind.

ACFG-66
Unreachable IR cannot be used to bypass semantic verification.

ACFG-67
`@cfg` configuration elimination occurs before semantic compilation of excluded program variants.

ACFG-68
Function calls carry their semantic effect information.

ACFG-69
Potential panic edges are represented according to function contract.

ACFG-70
Foreign calls are conservatively modeled unless contracts narrow their effects.

ACFG-71
Volatile operations remain observable across CFG optimization.

ACFG-72
Atomic ordering constrains CFG transformations.

ACFG-73
Synchronization operations constrain CFG transformations.

ACFG-74
GPU barriers constrain legal CFG transformations.

ACFG-75
Await introduces an explicit suspension boundary.

ACFG-76
Values live across await are explicitly represented in suspension state.

ACFG-77
Capabilities cannot silently outlive their provenance across await.

ACFG-78
Future Send requirements include complete suspension state.

ACFG-79
Cancellation is distinct from panic.

ACFG-80
Dropping a Future follows ordinary Drop semantics.

ACFG-81
Closure bodies have independent CFGs.

ACFG-82
Closure captures retain ordinary ownership semantics.

ACFG-83
GPU CFG obeys the same semantic ownership/capability foundation.

ACFG-84
Divergent GPU control flow cannot violate synchronization semantics.

ACFG-85
SSA construction preserves semantic behavior.

ACFG-86
MemorySSA preserves memory dependence semantics.

ACFG-87
MemoryPhi does not replace semantic ownership analysis.

ACFG-88
Critical-edge splitting preserves semantic behavior.

ACFG-89
Loop canonicalization preserves observable behavior.

ACFG-90
Jump threading requires semantic equivalence.

ACFG-91
Branch folding requires proven branch condition facts.

ACFG-92
Switch lowering preserves exhaustive pattern semantics.

ACFG-93
Tail-call optimization requires cleanup and ABI correctness.

ACFG-94
CFG transformations preserve source debug provenance.

ACFG-95
CFG transformations cannot manufacture ownership facts.

ACFG-96
CFG transformations cannot manufacture capability facts.

ACFG-97
CFG transformations cannot manufacture alias facts.

ACFG-98
CFG transformations cannot manufacture synchronization facts.

ACFG-99
CFG transformations cannot change observable external effects.

ACFG-100
CFG transformations are valid only after semantic verification or through separately verified semantic-preserving construction.

ACFG-101
Verified MIR is the semantic-to-optimization boundary.

ACFG-102
SSA is an optimization representation, not the language semantic model.

ACFG-103
MemorySSA is an optimization representation, not the language semantic model.

ACFG-104
Dominance information is derived from CFG structure.

ACFG-105
Loop information is derived from CFG structure.

ACFG-106
Parallel CFG analysis must be deterministic.

ACFG-107
Incremental CFG analysis must preserve semantic equivalence with full recomputation.

ACFG-108
Malformed CFG cannot reach code generation.

ACFG-109
Every optimization pass must preserve CFG validity.

ACFG-110
Every optimization pass must preserve cleanup correctness.

ACFG-111
Every optimization pass must preserve ownership correctness.

ACFG-112
Every optimization pass must preserve capability correctness.

ACFG-113
Every optimization pass must preserve atomic and synchronization semantics.

ACFG-114
Every optimization pass must preserve panic/unwind semantics.

ACFG-115
Every optimization pass must preserve async suspension semantics.

ACFG-116
Every optimization pass must preserve GPU synchronization semantics.

ACFG-117
Every optimization pass must preserve FFI semantics.

ACFG-118
CFG semantic behavior is independent of physical block ordering.

ACFG-119
CFG semantic behavior is independent of register allocation.

ACFG-120
CFG semantic behavior is independent of target instruction selection.

ACFG-121
CFG semantic behavior is independent of optimization level.

ACFG-122
Reference execution and MIR execution must agree on observable control flow behavior.

ACFG-123
Optimized execution must be observationally equivalent to Verified MIR.

ACFG-124
Native code generation must preserve CFG semantics.

ACFG-125
Axiom control-flow semantics are deterministic.
```

---

# Kiến trúc sau BOOTSTRAP-257

Axiom hiện có pipeline compiler lõi ngày càng rõ:

```text
                    SOURCE
                       │
                       ▼
                  Lossless AST
                       │
                       ▼
                     HIR
                       │
                       ▼
                 Typed HIR
                       │
                       ▼
                  Semantic MIR
                       │
              ┌────────┴────────┐
              │                 │
             CFG          Place/Memory
              │                 │
       ┌──────┼──────┐          │
       ▼      ▼      ▼          ▼
   Dominance Loop  Cleanup   Ownership
       │      │      │       Capability
       └──────┼──────┘       Initialization
              │                 │
              └────────┬────────┘
                       ▼
                 VERIFIED MIR
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
         SSA       MemorySSA    AliasInfo
          │            │            │
          └────────────┼────────────┘
                       ▼
                     OptIR
                       │
                       ▼
                  Axiom LIR
                       │
                       ▼
                 Machine Backend
```

Điểm quan trọng nhất ở đây là **MIR vẫn là “semantic truth”**, còn SSA/MemorySSA chỉ là representation phục vụ tối ưu hóa. Điều này giúp Axiom tránh bị khóa kiến trúc ngôn ngữ vào LLVM-style SSA quá sớm.

---

# BOOTSTRAP-258 — tiếp theo

Bước tiếp theo hợp lý là:

## **AXIOM CALLING CONVENTION, FUNCTION ABI, RETURN ABI, PARAMETER PASSING & CALL LOWERING**

Ta sẽ chốt từ:

```text
fn f(a: T, b: U) -> R
```

xuống:

```text
semantic function
      ↓
ABI classification
      ↓
parameter passing
      ↓
register / stack
      ↓
return value
      ↓
caller/callee saved registers
      ↓
variadic
      ↓
indirect return / sret
      ↓
tail call
      ↓
FFI
      ↓
Axiom ABI / C ABI
      ↓
machine CALL/RET
```

Đây là bước đặc biệt quan trọng vì nó sẽ quyết định **Axiom có thực sự đạt mục tiêu “struct/function abstraction nhưng không có overhead” hay không**.