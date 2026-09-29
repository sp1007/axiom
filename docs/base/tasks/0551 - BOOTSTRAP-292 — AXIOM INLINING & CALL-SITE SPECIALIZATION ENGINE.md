# BOOTSTRAP-292 — AXIOM INLINING & CALL-SITE SPECIALIZATION ENGINE
## FROZEN / COMPLETED

### 1. Mục tiêu

Sau `288` Scalar, `289` Memory, `290` Loop và `291` Vectorization, bottleneck lớn tiếp theo là **abstraction boundary của function call**.

Một chương trình Axiom có thể có:

```text
fn add(a: i32, b: i32) -> i32 {
    a + b
}

fn process(x: i32) -> i32 {
    add(x, 10)
}
```

Nếu giữ nguyên call:

```text
process
   ↓
call add
```

compiler có thể mất cơ hội:

```text
constant propagation
range analysis
branch elimination
loop optimization
vectorization
allocation elimination
devirtualization
```

Do đó `292` xây engine biến:

```text
Function Boundary
```

thành:

```text
Optimization Boundary
```

khi điều đó có lợi.

Nguyên tắc:

> **Function là abstraction semantic; call boundary không nhất thiết phải tồn tại trong machine code.**

---

# 2. Vị trí trong pipeline

```text id="v5j3s7"
Verified MIR
      ↓
Interprocedural Analysis
      ↓
Semantic Summary
      ↓
OptIR
      ↓
Scalar / Memory / Loop Analysis
      ↓
Inline Candidate Analysis
      ↓
Inlining
      ↓
Specialization
      ↓
Constant Propagation
      ↓
Devirtualization
      ↓
Loop / Vector Optimization
      ↓
Backend
```

Inlining không được làm thay đổi semantics.

---

# 3. Inlining không phải luôn luôn inline

Compiler phải phân biệt:

```text id="1v7k9a"
Legal to inline
```

và:

```text id="m3w5p2"
Worth inlining
```

Ví dụ:

```text id="7g2r4n"
small + hot
```

→ thường có lợi.

Nhưng:

```text id="p8x1d6"
huge + cold
```

→ có thể làm binary lớn hơn.

Do đó:

```text id="q9c4z7"
Legality
+
Cost
```

tách biệt hoàn toàn.

---

# 4. Inline Candidate

```text id="h2j8w5"
InlineCandidate {
    caller
    callsite
    callee
    dispatch_kind

    legality
    estimated_size
    estimated_growth
    hotness
    call_frequency

    semantic_summary
    required_proofs
}
```

---

# 5. Direct Call

Dễ nhất:

```text id="2r8m5k"
foo()
```

nếu `foo` được xác định chắc chắn:

```text id="6x1q8n"
DirectCall
```

thì có thể inline.

---

# 6. Generic Function

Ví dụ:

```text id="u7q0p3"
fn max<T: Ord>(a: T, b: T) -> T
```

call:

```text id="n4w9z2"
max<i32>(x, y)
```

compiler có:

```text id="g5c1r8"
GenericInstance
```

có thể specialize:

```text id="4j8m6v"
max_i32
```

rồi inline.

---

# 7. Monomorphization và Inlining

Không nên coi:

```text id="5f0p9c"
monomorphization
```

và:

```text id="y3k7w1"
inlining
```

là cùng một bước.

Pipeline:

```text id="q8m2r4"
Generic
 ↓
Instance
 ↓
Specialization
 ↓
Optimization
 ↓
Optional Inline
```

Một specialization có thể được tạo nhưng không inline.

---

# 8. Context-Sensitive Optimization

Trước inline:

```text id="7w3h2q"
fn abs(x) {
    if x < 0 { -x } else { x }
}
```

Call:

```text id="8v5m1n"
abs(10)
```

Sau inline:

```text id="r2k9x4"
if 10 < 0 {
    ...
} else {
    ...
}
```

`288` có thể biến toàn bộ thành:

```text id="c7p4s0"
10
```

Đây là lý do inlining thường tạo hiệu ứng lớn hơn chỉ việc bỏ một call instruction.

---

# 9. Inline Budget

```text id="0g6v8m"
InlineBudget {
    max_growth
    max_depth
    max_callee_size
    max_total_inline_size
    hot_bonus
    cold_penalty
    loop_bonus
    vectorization_bonus
}
```

Không dùng một ngưỡng cố định cho mọi chương trình.

---

# 10. Hotness

Nguồn thông tin:

```text id="s5j3r8"
StaticHeuristic
PGO
CallFrequency
LoopDepth
BranchProbability
```

Ví dụ:

```text id="h1k6p9"
hot call inside hot loop
```

có thể được ưu tiên inline.

---

# 11. Cold Call

Một function lớn nhưng chỉ gọi một lần ở error path:

```text id="v9q4n2"
cold
```

có thể không inline để giảm:

```text id="b7m2x5"
code size
instruction cache pressure
compile time
```

---

# 12. Recursive Function

Không được inline vô hạn:

```text id="3z7c1m"
f()
 ↓
f()
 ↓
f()
```

Cần:

```text id="6q8w4r"
InlineDepth
RecursionSCC
Budget
```

Có thể inline một số level nhỏ nếu cost model cho phép.

---

# 13. Mutual Recursion

```text id="k3n8p1"
A → B
B → A
```

phải được nhận diện thông qua SCC của call graph.

Không được tạo:

```text id="s5x2v9"
infinite expansion
```

---

# 14. Dynamic Dispatch

Ví dụ:

```text id="m6r0q8"
x.do_work()
```

nếu static type là:

```text id="v8p2c4"
dyn Trait
```

thì target có thể chưa biết.

Compiler thử:

```text id="e1y7s3"
devirtualization
```

nếu concrete target được chứng minh.

---

# 15. Devirtualization

Ví dụ:

```text id="q4h8w2"
let x: dyn Shape = concrete_shape(...)
x.area()
```

Nếu compiler chứng minh object luôn chứa:

```text id="p6c9r1"
Circle
```

thì:

```text id="j5z3m7"
dynamic call
```

→

```text id="b9x4q2"
direct call Circle.area
```

→ có thể inline.

---

# 16. Không cần Object Header

Điểm này phù hợp với Axiom.

Dynamic dispatch có thể sử dụng:

```text id="2x8n5c"
explicit dyn representation
```

nhưng ordinary structs không cần:

```text id="9q1w6p"
hidden object header
```

Static dispatch và generic dispatch vẫn có thể hoàn toàn zero-cost.

---

# 17. Trait Static Dispatch

```text id="s7m2q4"
fn process<T: Trait>(x: T)
```

với concrete:

```text id="f8k3n1"
process<MyType>(x)
```

có thể:

```text id="z4p7y9"
specialize
→ devirtualize
→ inline
```

Không cần runtime vtable.

---

# 18. Closure

Closure:

```text id="1q7m4z"
|x| x + offset
```

nếu capture environment nhỏ:

```text id="8v2k5r"
```

compiler có thể:

```text id="c4n6p1"
inline closure
```

và thậm chí loại bỏ environment hoàn toàn.

---

# 19. Closure Environment Elimination

Ví dụ:

```text id="y7h3q8"
let offset = 10

map(data, |x| x + offset)
```

Sau specialization/inlining:

```text id="4p9m2w"
x + 10
```

Không nhất thiết còn tồn tại:

```text id="s6k1v5"
ClosureObject
```

hay allocation.

---

# 20. Allocation Through Call

Ví dụ:

```text id="d3r8q0"
fn make() -> Box<T> {
    ...
}

let x = make()
```

Sau inline:

```text id="a6m2k7"
allocation
```

có thể được nhìn thấy bởi `289`.

Nếu:

```text id="j8q4w1"
NoEscape
```

thì allocation có thể bị loại bỏ.

Đây là một ví dụ rõ về pipeline liên kết:

```text id="x7p3m5"
Inlining
 ↓
Escape Analysis
 ↓
Memory Optimization
 ↓
Allocation Elimination
```

---

# 21. Caller Context

Inlining phải mang context của caller vào callee:

```text id="f1q8z6"
KnownConstants
KnownRanges
KnownTypes
KnownAliases
KnownEffects
KnownCapabilities
KnownStorage
```

Điều này cho phép specialization sâu hơn.

---

# 22. Context Specialization

Ví dụ:

```text id="k4m7n2"
fn process(x, mode) {
    if mode == 0 {
        A
    } else {
        B
    }
}
```

call:

```text id="v8p3q1"
process(x, 0)
```

Specialized version:

```text id="z6w5r9"
process_mode_0(x)
```

Sau đó `288` loại:

```text id="3g1x7m"
if mode == 0
```

---

# 23. Partial Specialization

Không cần specialize mọi argument.

Ví dụ:

```text id="y2c8m4"
f(x, constant)
```

chỉ specialize:

```text id="p7n1q5"
constant
```

Còn:

```text id="r4v6z0"
x
```

giữ dynamic.

Điều này hạn chế code explosion.

---

# 24. Constant Argument Specialization

Ví dụ:

```text id="h9k3w6"
fn copy_n<T>(src, dst, n)
```

call:

```text id="m4q8p2"
copy_n(src, dst, 16)
```

Compiler có thể tạo specialization:

```text id="a7z5c1"
copy_n_16
```

Sau đó loop optimizer/unroller có thể xử lý tốt hơn.

---

# 25. Type Specialization

Ví dụ:

```text id="b3r7x8"
fn process<T>(x: T)
```

với:

```text id="j1m5q9"
T = f32
```

compiler biết:

```text id="q6w2n4"
size
alignment
operations
Copy
Drop
traits
ABI
```

và có thể tạo machine-specialized body.

---

# 26. Trait Specialization

Nếu generic code:

```text id="s8p4k2"
x.operation()
```

với concrete `T`:

```text id="g3v7m1"
MyType
```

compiler có thể resolve implementation cụ thể.

Nếu implementation là:

```text id="n9q2w5"
small
```

→ inline tiếp.

---

# 27. Code Explosion

Specialization nguy hiểm vì:

```text id="2m7x4q"
1 generic function
×
1000 type instances
```

có thể tạo binary lớn.

Axiom cần:

```text id="h8k1p6"
SpecializationBudget
```

và:

```text id="r3v9z2"
CodeSharing
```

---

# 28. Hybrid Monomorphization

Không phải mọi generic function đều phải copy toàn bộ code.

Compiler có thể:

```text id="j5p8m3"
specialize hot/simple parts
```

nhưng:

```text id="q7x2n6"
share cold/common implementation
```

nếu representation/ABI cho phép.

---

# 29. Generic Code Sharing

Nếu hai instances có machine-equivalent behavior:

```text id="a8m4y1"
T = TypeA
T = TypeB
```

compiler có thể dùng chung implementation.

Nhưng semantic type identity vẫn khác.

Đây là:

```text id="u3k9p5"
code representation sharing
```

không phải:

```text id="e1q6w8"
type identity merging
```

---

# 30. ABI Boundary

Không inline xuyên qua ABI boundary nếu điều đó phá contract.

Ví dụ:

```text id="x8v2c7"
extern "C" fn foo(...)
```

có thể được inline nội bộ nếu compiler có body và ABI semantics cho phép.

Nhưng public/exported ABI phải vẫn giữ:

```text id="f4n7m1"
stable externally visible contract
```

---

# 31. Exported Function

Một function:

```text id="q9z3k5"
@export fn foo(...)
```

vẫn có thể có internal specialized/inlined copies.

Compiler không được loại bỏ symbol nếu external contract yêu cầu nó tồn tại.

---

# 32. FFI

Foreign call:

```text id="p6m1x8"
extern foo()
```

không có body:

```text id="w4k7r2"
cannot inline
```

Nếu có imported body/whole-program knowledge:

```text id="j8n3q5"
```

thì chỉ inline khi FFI contract cho phép và ABI semantics không thay đổi.

---

# 33. Panic Semantics

Inlining không được thay đổi:

```text id="v5r9k1"
whether panic can occur
```

hoặc observable panic order.

Ví dụ:

```text id="s3x7m4"
foo()
bar()
```

Nếu `foo` có thể panic:

```text id="a9q2p6"
```

thì compiler không được inline rồi reorder `bar()` trước panic một cách không hợp lệ.

---

# 34. Drop Semantics

Inlining phải bảo toàn:

```text id="y7m4q8"
Drop
Move
PartialMove
Cleanup
```

Ví dụ:

```text id="c2n6r1"
fn f(x: Resource) {
    ...
}
```

sau inline, Drop của `x` vẫn phải xuất hiện đúng semantic point.

---

# 35. Capability Semantics

Nếu callee nhận:

```text id="8k1q5z"
view<T>
```

hoặc:

```text id="0m7v3p"
mut_view<T>
```

Inlining không được biến capability thành unrestricted pointer access.

Proof:

```text id="r4x9n2"
Capability
```

phải được remap sang caller.

---

# 36. Ownership Remapping

Khi inline:

```text id="2w6p8m"
callee local
```

được nhập vào caller.

Compiler phải remap:

```text id="h5z1q7"
LocalId
Place
MovePath
CapabilityId
RegionId
DropScope
```

nhưng không được làm thay đổi ownership semantics.

---

# 37. MemorySSA Remapping

Inlining tạo thêm memory operations.

Do đó phải cập nhật:

```text id="v8k3m4"
MemoryDef
MemoryUse
MemoryPhi
```

Không được giữ MemorySSA cũ sau khi nó đã invalid.

---

# 38. Effect Summary

Nếu callee có:

```text id="n4p7x2"
Read
Write
Panic
```

thì sau inline các effects phải xuất hiện trong caller.

Nhưng nếu context cho phép chứng minh:

```text id="q6m1z9"
unreachable branch
```

thì scalar optimizer có thể loại bỏ effect không reachable.

---

# 39. Inlining và Vectorization

Đây là một mục tiêu rất quan trọng.

Trước:

```text id="w3j8p5"
for i in 0..n {
    out[i] = f(a[i])
}
```

nếu `f` là opaque call:

```text id="e9q4m2"
vectorization khó
```

Sau inline:

```text id="t7v1k6"
for i in 0..n {
    out[i] = complex_body(a[i])
}
```

→ `290/291` có thể nhận diện:

```text id="u8m3r5"
loop independence
vectorizable operations
```

Vì vậy `292` là một **enabler** cho SIMD chứ không chỉ tối ưu call overhead.

---

# 40. Inlining và GPU

GPU kernel thường cần aggressive specialization.

Ví dụ:

```text id="h2q6v8"
@kernel fn process(...) {
    helper(...)
}
```

Nếu `helper` nhỏ:

```text id="z5m1x3"
inline
```

giúp loại:

- function call
- abstraction boundary
- temporary
- dynamic dispatch

nhưng vẫn phải giữ GPU legality.

---

# 41. Async

Inlining `async fn` phức tạp hơn ordinary function.

Compiler phải bảo toàn:

```text id="x7n4q2"
Future state
SuspensionPointId
live-across-await
Drop
Send
storage
```

Không được biến:

```text id="p9m2k5"
await
```

thành ordinary synchronous execution.

---

# 42. Async Inlining

Có thể inline phần trước `await`:

```text id="a3v7r1"
async fn f() {
    small_work()
    await g()
}
```

nhưng state-machine transformation phải được cập nhật chính xác.

Do đó `292` chỉ cho phép inline khi:

```text id="q6w8n4"
AsyncLoweringInfo
```

có thể được remap hợp lệ.

---

# 43. Comptime

`comptime fn` là trường hợp đặc biệt.

Comptime call có thể được:

```text id="j1p5x8"
evaluated by Comptime VM
```

thay vì runtime inline.

Không được tạo runtime code chỉ vì inline optimization.

---

# 44. Compile-Time Specialization

Ví dụ:

```text id="c8m4r2"
comptime if T == f32
```

có thể resolve hoàn toàn trước runtime.

Kết quả HIR/MIR đã specialized trước khi OptIR.

Do đó optimizer không được nhầm:

```text id="w7n2q6"
comptime specialization
```

với:

```text id="k5p9x1"
runtime specialization
```

---

# 45. Inline Failure

Compiler không được coi inline failure là compilation error.

Ví dụ:

```text id="g4z8m2"
cannot prove safe
```

thì:

```text id="p6x1q7"
retain original call
```

Miễn semantics vẫn đúng.

---

# 46. Inline Transaction

Dùng cơ chế `287`:

```text id="6q3w9m"
Snapshot
 ↓
Candidate
 ↓
Proof validation
 ↓
Clone/remap callee IR
 ↓
Merge CFG
 ↓
Merge MemorySSA
 ↓
Merge ownership/capability facts
 ↓
Validate
 ↓
Commit
```

---

# 47. Call Graph Update

Sau inline:

```text id="j8m2p4"
Caller → Callee
```

không còn là runtime call tại callsite.

Call graph phải ghi nhận:

```text id="x3q7v1"
InlinedEdge
```

hoặc loại bỏ runtime edge nhưng giữ provenance để diagnostics/debug.

---

# 48. Debug Provenance

Nếu debugger dừng ở code đã inline:

```text id="v5n8k2"
machine instruction
```

phải có thể map:

```text id="r1q6z9"
machine
 ↓
inlined MIR
 ↓
callee source
 ↓
original caller callsite
```

Do đó inline stack phải được lưu trong SourceMap.

---

# 49. Optimization Trace

Compiler nên giải thích:

```text id="m4x7q2"
Why inline?
```

Ví dụ:

```text
Inline decision:
  callee size: 8
  call hotness: high
  estimated growth: +6
  vectorization benefit: high
  legality: proven
  decision: inline
```

Nếu từ chối:

```text
decision: reject
reason:
  code-size budget exceeded
```

---

# 50. Module Structure

```text id="k7p2m5"
compiler/optimization/inline/
├── mod.ax
│
├── candidate/
│   ├── candidate.ax
│   ├── legality.ax
│   ├── hotness.ax
│   └── context.ax
│
├── cost/
│   ├── model.ax
│   ├── budget.ax
│   ├── size.ax
│   ├── growth.ax
│   └── pgo.ax
│
├── transform/
│   ├── clone.ax
│   ├── remap.ax
│   ├── cfg_merge.ax
│   ├── local_remap.ax
│   ├── ownership_remap.ax
│   ├── capability_remap.ax
│   ├── memoryssa_remap.ax
│   └── source_map.ax
│
├── specialize/
│   ├── mod.ax
│   ├── generic.ax
│   ├── constant.ax
│   ├── type.ax
│   ├── trait.ax
│   ├── partial.ax
│   └── sharing.ax
│
├── devirtualize/
│   ├── mod.ax
│   ├── dyn_trait.ax
│   ├── trait_dispatch.ax
│   ├── closure.ax
│   └── target_set.ax
│
├── async/
│   ├── mod.ax
│   ├── future.ax
│   ├── suspension.ax
│   └── state_remap.ax
│
├── gpu/
│   ├── mod.ax
│   └── kernel.ax
│
└── tests/
```

---

# 51. Implementation Order

```text id="m8q3v1"
1. Inline candidate model
2. Call-site context extraction
3. Inline legality analysis
4. Callee cost estimation
5. Hotness integration
6. Inline budget
7. Callee IR cloning
8. Local/Place remapping
9. CFG merge
10. Ownership remapping
11. Capability remapping
12. Drop-scope remapping
13. MemorySSA remapping
14. Effect remapping
15. Source-map/inlined-stack remapping
16. Validation
17. Direct-call inlining
18. Generic specialization
19. Constant-argument specialization
20. Type specialization
21. Trait specialization
22. Partial specialization
23. Code sharing
24. Dynamic dispatch devirtualization
25. Closure specialization
26. Async restrictions
27. GPU restrictions
28. FFI restrictions
29. PGO integration
30. Pass Manager integration
31. Optimization trace
32. adversarial tests
```

---

# 52. Adversarial Tests

### Test 1 — Basic inline

```text
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Call must be safely inlineable.

---

### Test 2 — Constant propagation

```text
add(x, 10)
```

After inline, `288` phải có cơ hội propagate constant `10`.

---

### Test 3 — Panic

Callee có thể panic.

Inline không được làm mất hoặc đổi panic semantics.

---

### Test 4 — Drop

Callee nhận owning resource.

Drop phải vẫn exactly-once.

---

### Test 5 — Partial move

Callee partial-move một struct.

Remapping không được biến thành whole-object move.

---

### Test 6 — Capability

```text
fn f(x: mut_view<T>)
```

Inlining không được tạo mutable alias mới.

---

### Test 7 — Memory

Callee:

```text
store(x, 1)
```

Caller:

```text
load(x)
```

MemorySSA sau inline phải phản ánh dependency.

---

### Test 8 — Foreign call

Không có body → không inline.

---

### Test 9 — Dynamic dispatch

Concrete target proven → devirtualize.

Concrete target unknown → giữ dynamic dispatch.

---

### Test 10 — Recursion

Recursive function không được inline vô hạn.

---

### Test 11 — Generic explosion

1000 instantiations không được tạo code vô hạn vượt budget.

---

### Test 12 — Closure

Capturing closure nhỏ có thể inline và environment có thể bị loại bỏ.

---

### Test 13 — Async

Inline không được làm mất `await` hoặc thay đổi Future state.

---

### Test 14 — GPU

GPU-incompatible operation không được xuất hiện sau kernel inlining.

---

### Test 15 — ABI

`@export` symbol vẫn tồn tại dù body đã được inline ở các caller khác.

---

### Test 16 — Vectorization enabler

```text
for i in 0..n {
    out[i] = helper(a[i])
}
```

Inline `helper` phải mở đường cho vectorization nếu legality/profitability cho phép.

---

# 53. Frozen Invariants

### `AINLINE-20..95`

```text id="b5r8k2"
AINLINE-20 — Inlining Operates Only On Verified OptIR
AINLINE-21 — Inlining Is Semantics-Preserving
AINLINE-22 — Inline Legality Is Distinct From Inline Profitability
AINLINE-23 — Cost Model Cannot Override Legality
AINLINE-24 — Unknown Legality Is Not Treated As Legal
AINLINE-25 — Direct Calls May Be Inlined When Legal
AINLINE-26 — Foreign Calls Require Available Valid Body And ABI Contract
AINLINE-27 — Exported Symbols Must Preserve Their External Contract
AINLINE-28 — Generic Instantiation Is Distinct From Inlining
AINLINE-29 — Generic Specialization Is Distinct From Inlining
AINLINE-30 — Specialization May Occur Without Inlining
AINLINE-31 — Inlining May Occur Without Full Specialization
AINLINE-32 — Specialization Must Respect Code-Size Budgets
AINLINE-33 — Code Sharing May Reduce Specialization Explosion
AINLINE-34 — Type Identity Is Never Merged By Code Sharing
AINLINE-35 — Constant-Argument Specialization Requires Proven Constant Arguments
AINLINE-36 — Partial Specialization Must Preserve Unspecialized Semantics
AINLINE-37 — Recursive Inlining Is Explicitly Bounded
AINLINE-38 — Mutual Recursion Is SCC-Aware
AINLINE-39 — Inline Depth Is Bounded
AINLINE-40 — Inline Growth Is Budgeted
AINLINE-41 — Hotness May Affect Profitability But Not Legality
AINLINE-42 — PGO May Affect Inline Decisions But Not Semantics
AINLINE-43 — Caller Context May Refine Callee Optimization Facts
AINLINE-44 — Context Facts Must Remain Proven Facts
AINLINE-45 — Inlining Must Preserve Evaluation Order
AINLINE-46 — Inlining Must Preserve Panic Semantics
AINLINE-47 — Inlining Must Preserve Drop Semantics
AINLINE-48 — Inlining Must Preserve Move Semantics
AINLINE-49 — Inlining Must Preserve Partial-Move Semantics
AINLINE-50 — Inlining Must Preserve Initialization Semantics
AINLINE-51 — Inlining Must Preserve Ownership Semantics
AINLINE-52 — Inlining Must Preserve Capability Semantics
AINLINE-53 — Inlining Must Preserve Capability Provenance
AINLINE-54 — Inlining Must Not Create New Safe Aliasing
AINLINE-55 — Inlining Must Not Invent Ownership
AINLINE-56 — Inlining Must Not Extend Capability Lifetimes Illegally
AINLINE-57 — Inlining Must Preserve Effect Semantics
AINLINE-58 — Inlining Must Preserve Memory Dependencies
AINLINE-59 — MemorySSA Must Be Updated After Inlining
AINLINE-60 — Stale MemorySSA Must Not Be Used After Inlining
AINLINE-61 — Inlining Must Preserve Atomic Semantics
AINLINE-62 — Inlining Must Preserve Volatile Semantics
AINLINE-63 — Inlining Must Preserve Synchronization Semantics
AINLINE-64 — Inlining Must Preserve Foreign Effects
AINLINE-65 — Inlining Must Preserve Stable-Address Contracts
AINLINE-66 — Inlining Must Preserve Logical Identity
AINLINE-67 — Dynamic Dispatch Requires Valid Devirtualization Proof
AINLINE-68 — Unknown Dynamic Targets Must Remain Conservative
AINLINE-69 — Devirtualization Must Preserve Trait Semantics
AINLINE-70 — Closure Inlining Must Preserve Capture Semantics
AINLINE-71 — Closure Environment Elimination Requires Escape Proof
AINLINE-72 — Allocation Elimination After Inlining Requires Independent Escape Proof
AINLINE-73 — Async Inlining Must Preserve Suspension Semantics
AINLINE-74 — Async Inlining Must Preserve Future State Semantics
AINLINE-75 — Async Inlining Must Preserve Send Requirements
AINLINE-76 — GPU Inlining Must Preserve GPU Legality
AINLINE-77 — GPU Inlining Must Preserve Execution And Storage Domains
AINLINE-78 — Comptime Specialization Is Distinct From Runtime Specialization
AINLINE-79 — Comptime Code Must Not Accidentally Become Runtime Code
AINLINE-80 — ABI Contracts Must Be Preserved
AINLINE-81 — Inlined Code Retains Source Provenance
AINLINE-82 — Debug Information Must Preserve Inlined Call Stacks
AINLINE-83 — Call Graph State Must Reflect Inlined Edges
AINLINE-84 — Analysis Dependencies Must Be Invalidated After Relevant IR Changes
AINLINE-85 — Proofs Invalidated By Inlining Cannot Be Reused
AINLINE-86 — Inline Transformations Use OptimizationGateway
AINLINE-87 — Inline Transformations Are Transactional
AINLINE-88 — Failed Inline Transformations Preserve Prior Valid IR
AINLINE-89 — Inline Decisions Must Be Deterministic
AINLINE-90 — Inline Decisions Must Be Explainable
AINLINE-91 — Inline Optimization Must Respect Code-Size Constraints
AINLINE-92 — Inline Optimization Must Respect Compile-Time Budgets
AINLINE-93 — Inline Optimization Must Not Depend On Undefined Behavior
AINLINE-94 — Inline Optimization Must Preserve Axiom Observable Semantics
AINLINE-95 — Inlining Is A Zero-Cost Abstraction Enabler, Not A Semantic Requirement
```

---

## 54. Kết quả kiến trúc

Axiom hiện có một chuỗi tối ưu hóa rất quan trọng:

```text id="q8n4m2"
Function Abstraction
        │
        ▼
Interprocedural Summary
        │
        ▼
Inlining / Specialization
        │
        ├──────────────┐
        ▼              ▼
     Scalar         Escape
        │              │
        ▼              ▼
      Memory        Allocation
        │              │
        └──────┬───────┘
               ▼
             Loop
               │
               ▼
         Vectorization
               │
               ▼
          Native SIMD
```

Điều này giúp Axiom đạt một mục tiêu rất quan trọng:

> Programmer có thể viết abstraction, generic, trait, closure và function decomposition theo cách sạch sẽ; compiler có thể **xóa abstraction boundary khi chứng minh được rằng nó không cần tồn tại ở runtime**.

Vì vậy “zero-cost abstraction” trong Axiom không phải khẩu hiệu rằng mọi abstraction luôn miễn phí, mà là:

```text
Semantic abstraction
        ↓
Compiler proof
        ↓
Physical abstraction erased
```

khi không có observable behavior buộc nó phải tồn tại.

**BOOTSTRAP-292 hoàn tất và được đóng băng.**