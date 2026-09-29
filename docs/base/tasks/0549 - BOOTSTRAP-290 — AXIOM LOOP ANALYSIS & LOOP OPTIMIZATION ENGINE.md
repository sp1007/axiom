# BOOTSTRAP-290 — AXIOM LOOP ANALYSIS & LOOP OPTIMIZATION ENGINE
## FROZEN / COMPLETED

### 1. Mục tiêu

Sau `288` (Scalar) và `289` (Memory), bước tiếp theo là tối ưu **vòng lặp** — nơi compiler có thể tạo ra chênh lệch hiệu năng rất lớn trong code số học, xử lý mảng, image/audio/video, AI/ML và systems code.

Mục tiêu:

> **Biến vòng lặp cấp cao thành machine-friendly loop mà không yêu cầu programmer viết các annotation tối ưu thủ công.**

Đặc biệt Axiom phải tận dụng các proof đã có:

```text
Ownership
Capability
Alias
Range
Effect
Escape
MemorySSA
Scalar facts
```

thay vì xây một hệ thống tối ưu loop tách biệt.

---

# 2. Vị trí trong pipeline

```text
Verified MIR
      ↓
OptIR
      ↓
SSA
      ↓
Scalar Analysis
      ↓
MemorySSA
      ↓
Alias / Capability
      ↓
Loop Analysis
      ↓
Loop Optimization
      │
      ├── Canonicalization
      ├── Induction Variable Analysis
      ├── Loop Simplification
      ├── LICM
      ├── Unswitching
      ├── Unrolling
      ├── Fusion
      ├── Peeling
      ├── Versioning
      └── Loop Distribution
      ↓
Vectorization / Target Optimization
```

`290` không thực hiện SIMD vectorization đầy đủ; nó chuẩn bị và biến đổi loop để `298`/các backend vectorizer có thể khai thác tốt hơn.

---

# 3. Nguyên tắc trung tâm

> **Loop optimization phải dựa trên semantic proof, không dựa trên giả định UB kiểu C/C++.**

Ví dụ:

```text
for i in 0..n {
    a[i] += b[i]
}
```

Compiler cần biết:

```text
i range
bounds
memory regions
alias relations
side effects
overflow semantics
iteration independence
```

rồi mới quyết định:

```text
unroll?
vectorize-ready?
parallelize?
hoist?
fuse?
```

---

# 4. Loop Representation

Tạo:

```text
Loop {
    id: LoopId

    header: BasicBlockId
    preheader: BasicBlockId
    latch: BasicBlockId

    exits: [BasicBlockId]
    backedges: [BasicBlockId]

    parent: Option<LoopId>
    children: [LoopId]

    depth: u32
}
```

Loop nesting:

```text
outer
├── inner
├── inner
└── inner
```

được biểu diễn bằng `LoopTree`.

---

# 5. Natural Loop

Từ CFG:

```text
header
   ↓
 body
   ↓
 latch
   │
   └────→ header
```

Compiler xác định:

```text
backedge: latch → header
```

và xây natural loop.

CFG restructuring phải bảo đảm:

```text
ownership facts
capability facts
MemorySSA
effect facts
```

được cập nhật.

---

# 6. Loop Canonical Form

Axiom đưa loop về canonical form khi có lợi:

```text
preheader
    ↓
header
    ↓
body
    ↓
latch
    └──→ header
```

Ví dụ:

```text
for i in 0..n
```

có thể canonicalize thành:

```text
i = 0
goto header

header:
    compare i,n
    branch body/exit

body:
    ...
    i = i + 1
    goto header

exit:
```

Nhưng canonicalization là IR transformation, **không phải yêu cầu programmer viết theo dạng này**.

---

# 7. Induction Variable

Compiler nhận diện:

```text
i = i + 1
```

hoặc:

```text
i += stride
```

và tạo:

```text
InductionVariable {
    value
    start
    step
    range
    recurrence
}
```

Hỗ trợ:

```text
i++
i--
i += c
i *= c
```

khi recurrence có thể chứng minh.

---

# 8. Derived Induction Variables

Ví dụ:

```text
i += 1
j = i * 4
```

Compiler có thể nhận ra:

```text
j
```

là derived induction variable.

Sau đó có thể biến:

```text
j = i * 4
```

thành recurrence:

```text
j += 4
```

nếu target cost model cho thấy lợi ích.

---

# 9. Loop Range Analysis

Compiler phải biết:

```text
0 <= i < n
```

từ loop semantics.

Thông tin này dùng cho:

```text
bounds-check elimination
alias analysis
vectorization
memory safety
```

Ví dụ:

```text
a[i]
```

nếu `i` nằm trong range hợp lệ thì bounds check có thể được loại bỏ.

---

# 10. Không được dùng Overflow UB

Axiom không được suy luận:

```text
i + 1 > i
```

chỉ vì `i` là integer.

Nếu arithmetic semantics cho phép wrapping:

```text
u32::MAX + 1
```

→ `0`.

Vì vậy loop analysis phải mang theo:

```text
ArithmeticMode
```

và chỉ sử dụng các biến đổi phù hợp với semantics.

---

# 11. Loop Invariant

Một expression được gọi là loop invariant nếu giá trị của nó không thay đổi giữa các iteration.

Ví dụ:

```text
for i in 0..n {
    x = a * b
    ...
}
```

Nếu `a`, `b` không thay đổi:

```text
x = a * b
```

có thể đưa ra ngoài loop.

---

# 12. LICM

Loop-Invariant Code Motion:

```text
for i in 0..n {
    x = a * b
    use(x)
}
```

→

```text
x = a * b

for i in 0..n {
    use(x)
}
```

nhưng chỉ khi operation:

```text
No observable effect
No required ordering
No new panic behavior
No invalid memory access
```

---

# 13. Hoisting Load

```text
for i in 0..n {
    x = load(a.constant_field)
}
```

có thể hoist nếu compiler chứng minh:

```text
NoWrite(region)
NoForeignWrite
NoAtomicConflict
NoVolatile
```

Trong trường hợp có mutation:

```text
a.field = ...
```

thì MemorySSA sẽ ngăn hoisting nếu dependency tồn tại.

---

# 14. Hoisting Allocation

Không được đơn giản:

```text
for ... {
    x = allocate()
}
```

→

```text
x = allocate()

for ... {
}
```

vì lifetime semantics có thể khác.

Chỉ được làm khi:

```text
allocation equivalence
lifetime equivalence
Drop equivalence
escape equivalence
address semantics
```

được chứng minh.

---

# 15. Loop-Invariant Drop

Drop là observable effect nếu destructor có effect.

Do đó:

```text
Drop(x)
```

không được coi là invariant rồi tùy tiện di chuyển.

Compiler phải giữ:

```text
Drop ordering
Drop exactly-once
Panic/unwind semantics
```

---

# 16. Loop Unswitching

Ví dụ:

```text
for i in 0..n {
    if flag {
        A
    } else {
        B
    }
}
```

Nếu `flag` invariant:

```text
if flag {
    for i in 0..n {
        A
    }
} else {
    for i in 0..n {
        B
    }
}
```

Điều này tăng code size.

Do đó cost model quyết định.

---

# 17. Loop Peeling

Ví dụ cần xử lý riêng iteration đầu:

```text
for i in 0..n {
    ...
}
```

Compiler có thể biến thành:

```text
first iteration
main loop
```

để:

- align memory
- simplify branch
- eliminate special case
- chuẩn bị vectorization

Chỉ thực hiện nếu semantics và cost model cho phép.

---

# 18. Loop Unrolling

Ví dụ:

```text
for i in 0..n {
    body(i)
}
```

có thể thành:

```text
body(i)
body(i+1)
body(i+2)
body(i+3)
```

kèm remainder loop.

Ví dụ:

```text
main loop
    ×4

remainder loop
    ×1
```

---

# 19. Unroll Factor

Không cố định:

```text
4
```

Compiler sử dụng:

```text
TargetInfo
TripCount
BodyCost
RegisterPressure
CodeSizeBudget
VectorWidth
BranchCost
```

để quyết định.

---

# 20. Full Unroll

Nếu:

```text
trip_count
```

là compile-time constant nhỏ:

```text
for i in 0..4
```

có thể full-unroll.

Sau đó `288` có thể tiếp tục:

```text
SCCP
InstCombine
DCE
```

và loại bỏ phần code dư thừa.

---

# 21. Runtime Trip Count

Nếu:

```text
n
```

không biết compile time:

```text
if n >= threshold
    optimized loop
else
    simple loop
```

có thể được tạo bằng loop versioning/dispatch nếu cost model cho phép.

---

# 22. Loop Versioning

Ví dụ compiler chưa biết:

```text
NoAlias(a,b)
```

có thể tạo:

```text
if proven_noalias_at_runtime {
    fast_loop
} else {
    safe_loop
}
```

Nhưng runtime check phải có semantic correctness.

Đặc biệt Axiom có capability/region proof mạnh nên versioning chỉ cần khi static proof không đủ.

---

# 23. Loop Fusion

Hai loop:

```text
for i in 0..n {
    a[i] = f(i)
}

for i in 0..n {
    b[i] = g(a[i])
}
```

có thể fusion:

```text
for i in 0..n {
    a[i] = f(i)
    b[i] = g(a[i])
}
```

Chỉ hợp lệ nếu:

```text
iteration dependencies
alias
effects
ordering
panic
Drop
observable behavior
```

đều được bảo toàn.

---

# 24. Loop Distribution

Ngược lại:

```text
for i in 0..n {
    A(i)
    B(i)
}
```

có thể thành:

```text
for i in 0..n {
    A(i)
}

for i in 0..n {
    B(i)
}
```

nếu giúp:

```text
vectorization
cache locality
parallelization
```

và semantic dependencies cho phép.

---

# 25. Không tự động Parallelize

Axiom không được biến:

```text
for
```

thành:

```text
parallel for
```

chỉ vì compiler thấy iterations có vẻ độc lập.

Parallel execution thay đổi:

```text
ordering
timing
synchronization
```

và có thể thay đổi observable behavior.

Parallelization cần semantic contract riêng, ví dụ:

```text
parallel for
```

hoặc library/compiler directive trong tầng cao hơn.

---

# 26. Reduction Recognition

Compiler có thể nhận diện:

```text
sum = sum + a[i]
```

là reduction.

Nhưng không tự ý reassociate floating-point:

```text
((a+b)+c)
```

thành:

```text
a+(b+c)
```

nếu strict FP.

Với explicit fast-math/relaxed arithmetic contract, optimizer có thể mở rộng phép biến đổi.

---

# 27. Integer Reduction

Với integer semantics:

```text
sum += a[i]
```

compiler phải tôn trọng:

```text
checked
wrapping
saturating
```

mode.

Không được assume mathematical integers nếu runtime semantics là wrapping.

---

# 28. Loop-Invariant Branch

```text
for i in 0..n {
    if mode == X {
        ...
    }
}
```

Nếu `mode` immutable trong loop:

```text
```

có thể:

```text
hoist branch
```

hoặc loop unswitch.

---

# 29. Loop Exit Analysis

Compiler xác định:

```text
must execute
may execute
never execute
```

đối với exit.

Điều này hỗ trợ:

```text
DCE
Drop placement
Panic analysis
LICM
unrolling
```

---

# 30. Infinite Loop

Axiom có:

```text
never
```

nên compiler phải phân biệt:

```text
finite loop
possibly infinite loop
proven infinite loop
```

Ví dụ:

```text
loop {
    work()
}
```

nếu không có reachable exit:

```text
return type
```

có thể là:

```text
never
```

nhưng effects của `work()` vẫn tồn tại.

Không được DCE toàn bộ loop chỉ vì nó không return.

---

# 31. Side Effects

Loop optimizer phải xem:

```text
EffectSummary
```

cho từng instruction/call.

Các barrier mạnh:

```text
IO
Volatile
Atomic
Synchronize
Foreign
Spawn
Block
Await
```

không thể bị reorder như arithmetic thuần.

---

# 32. Async Loop

Loop chứa:

```text
await
```

không được xử lý như synchronous loop.

Compiler phải tôn trọng:

```text
SuspensionPointId
Future state
live-across-await values
Send
capability lifetime
```

Đặc biệt không được LICM một giá trị qua `await` nếu điều đó thay đổi semantics.

---

# 33. Capability và Loop

Ví dụ:

```text
let v = mut_view(a)

for i in 0..n {
    v[i] += 1
}
```

Compiler có thể sử dụng:

```text
exclusive capability
```

để chứng minh không có conflicting access từ region khác.

Điều này là một lợi thế quan trọng của Axiom:

```text
Capability proof
       ↓
NoAlias
       ↓
Loop independence
       ↓
optimization
```

Programmer không cần viết `restrict`.

---

# 34. Loop-Carried Dependency

Compiler phải phân biệt:

```text
independent
```

và:

```text
loop-carried dependency
```

Ví dụ:

```text
a[i] = b[i]
```

có thể independent.

Nhưng:

```text
a[i] = a[i-1] + 1
```

có dependency giữa iterations.

Không được fusion/unroll/vectorize như independent loop nếu không có transformation đúng semantics.

---

# 35. Dependence Distance

Compiler có thể lưu:

```text
Dependence {
    source
    destination
    distance
    direction
    kind
}
```

Ví dụ:

```text
distance = 1
```

cho:

```text
a[i] → a[i+1]
```

Thông tin này hữu ích cho:

- unrolling
- scheduling
- vectorization preparation
- loop transformation.

---

# 36. Loop Cost Model

```text
LoopCost {
    trip_count
    estimated_iterations
    body_cost
    memory_cost
    branch_cost
    register_pressure
    code_size_growth
    vectorization_potential
    cache_behavior
    target_penalty
}
```

Legality:

```text
Proof
```

Cost:

```text
CostModel
```

Hai khái niệm tuyệt đối không được trộn.

---

# 37. Profile-Guided Loop Optimization

Nếu có PGO:

```text
hot loop
cold loop
trip count distribution
branch probability
```

thì loop optimizer có thể ưu tiên:

```text
unroll
peel
unswitch
fusion
```

cho hot loops.

Cold loops ưu tiên:

```text
code size
```

---

# 38. Cache Locality

Loop optimizer có thể sử dụng:

```text
stride
working-set estimate
access pattern
target cache characteristics
```

để lựa chọn transformation.

Ví dụ:

```text
row-major
```

có thể được ưu tiên hơn traversal gây cache miss.

Tuy nhiên compiler không được thay đổi semantic iteration order nếu order observable.

---

# 39. Loop Nest Optimization

Ví dụ:

```text
for i
    for j
        A[i][j]
```

compiler có thể phân tích:

```text
LoopNest {
    outer
    inner
    access_pattern
}
```

để chuẩn bị:

- interchange
- tiling
- fusion
- vectorization

nhưng loop interchange chỉ hợp lệ khi dependence analysis chứng minh.

---

# 40. Loop Interchange

```text
for i
    for j
        A[i][j]
```

→

```text
for j
    for i
        A[i][j]
```

không phải lúc nào cũng semantic-equivalent.

Đặc biệt:

```text
side effects
floating point
atomic
IO
Drop
iteration order
```

có thể làm phép đổi thứ tự không hợp lệ.

Vì vậy:

> **Performance benefit không bao giờ là proof of legality.**

---

# 41. Loop Tiling

Loop tiling:

```text
for ii
    for i in tile
        ...
```

được dành cho các workload lớn:

- matrix
- image
- tensor
- scientific computing

Nhưng task `290` chỉ định **analysis và legality framework**; implementation chuyên sâu target/tensor có thể nằm ở các task sau.

---

# 42. Loop Transformation Transaction

Mọi loop transformation sử dụng cơ chế của `287`:

```text
Snapshot
   ↓
Plan
   ↓
Check Proof
   ↓
Transform
   ↓
Rebuild/Update CFG
   ↓
Validate
   ↓
Commit
```

Nếu validation thất bại:

```text
Rollback
```

---

# 43. Analysis Invalidation

Transformation có thể invalidate:

```text
ScalarFacts
RangeFacts
MemorySSA
AliasInfo
LoopInfo
Dominators
PostDominators
EffectFacts
Proofs
```

Không được tiếp tục sử dụng fact cũ.

Orchestrator `286` quản lý dependency.

---

# 44. Module Structure

```text id="q2w7n4"
compiler/optimization/loop/
├── mod.ax
│
├── analysis/
│   ├── loop.ax
│   ├── loop_tree.ax
│   ├── natural_loop.ax
│   ├── dominator.ax
│   ├── post_dominator.ax
│   ├── backedge.ax
│   ├── trip_count.ax
│   ├── induction.ax
│   ├── recurrence.ax
│   ├── dependence.ax
│   └── access_pattern.ax
│
├── canonical/
│   ├── simplify.ax
│   ├── preheader.ax
│   ├── latch.ax
│   └── form.ax
│
├── invariant/
│   ├── invariant.ax
│   ├── licm.ax
│   └── safety.ax
│
├── transform/
│   ├── unswitch.ax
│   ├── peel.ax
│   ├── unroll.ax
│   ├── fuse.ax
│   ├── distribute.ax
│   ├── interchange.ax
│   ├── version.ax
│   └── tile.ax
│
├── reduction/
│   ├── detect.ax
│   ├── integer.ax
│   └── floating.ax
│
├── cost/
│   ├── model.ax
│   ├── target.ax
│   ├── pgo.ax
│   └── code_size.ax
│
├── legality/
│   ├── dependence.ax
│   ├── effects.ax
│   ├── memory.ax
│   ├── ownership.ax
│   ├── capability.ax
│   └── floating_point.ax
│
└── tests/
```

---

# 45. Implementation Order

```text
1. Loop/LoopTree representation
2. Dominator integration
3. Natural-loop discovery
4. Canonical loop form
5. Loop exit analysis
6. Induction-variable analysis
7. Trip-count analysis
8. Recurrence analysis
9. Loop range analysis
10. Dependence analysis
11. MemorySSA integration
12. Capability/alias integration
13. Effect integration
14. Loop-invariant analysis
15. LICM
16. Loop unswitching
17. Loop peeling
18. Loop unrolling
19. Loop fusion
20. Loop distribution
21. Loop versioning
22. Reduction recognition
23. Loop interchange legality
24. Loop tiling framework
25. Cost model
26. PGO integration
27. Async-loop restrictions
28. proof gateway integration
29. invalidation integration
30. adversarial/conformance tests
```

---

# 46. Adversarial Tests

### Test 1 — Loop-carried dependency

```text
for i in 1..n {
    a[i] = a[i-1] + 1
}
```

Không được coi iterations independent.

---

### Test 2 — NoAlias

```text
for i in 0..n {
    a[i] = b[i] + 1
}
```

với capability proof:

```text
NoAlias(a,b)
```

→ được phép dùng independence proof.

---

### Test 3 — Unknown alias

Nếu:

```text
Alias(a,b) = UNKNOWN
```

→ không được assume independent.

---

### Test 4 — Volatile

```text
for i in 0..n {
    volatile_store(x, i)
}
```

Không được LICM hoặc loại bỏ access.

---

### Test 5 — Atomic

Atomic operations phải giữ:

```text
atomicity
ordering
```

qua mọi loop transformation.

---

### Test 6 — Floating-point reduction

```text
sum += a[i]
```

Strict FP:

```text
```

không được tự ý reassociate.

---

### Test 7 — Wrapping integer

```text
u8 i
i += 1
```

Không được sử dụng mathematical overflow assumption để chứng minh loop property sai.

---

### Test 8 — Panic

```text
for i in 0..n {
    check(i)
}
```

nếu `check` có thể panic, LICM phải giữ panic behavior/order.

---

### Test 9 — Drop

```text
for i in 0..n {
    create_resource()
}
```

không được hoist allocation/drop ra ngoài nếu thay đổi số lần cleanup.

---

### Test 10 — Await

```text
for ... {
    await work()
}
```

Không được áp dụng synchronous loop transform làm thay đổi suspension behavior.

---

### Test 11 — Foreign call

```text
for ... {
    foreign_call()
}
```

Memory/effect dependency conservative nếu không có contract.

---

### Test 12 — Infinite loop

```text
loop {
    side_effect()
}
```

phải vẫn giữ `side_effect()`.

---

# 47. Frozen Invariants

### `ALOOP-20..90`

```text
ALOOP-20 — Loop Optimization Operates Only On Verified OptIR
ALOOP-21 — Loop Analysis Uses The Canonical CFG
ALOOP-22 — Loop Tree Is Derived From CFG
ALOOP-23 — Backedges Are Explicitly Identified
ALOOP-24 — Natural Loop Membership Is Deterministic
ALOOP-25 — Loop Nesting Is Explicit
ALOOP-26 — Canonicalization Preserves Semantics
ALOOP-27 — Preheaders Preserve Entry Semantics
ALOOP-28 — Latches Preserve Iteration Semantics
ALOOP-29 — Exit Semantics Are Preserved
ALOOP-30 — Induction Variables Require Proven Recurrence
ALOOP-31 — Derived Induction Variables Require Proven Relation
ALOOP-32 — Trip Count Analysis Is Conservative
ALOOP-33 — Unknown Trip Count Is Never Treated As Constant
ALOOP-34 — Integer Overflow Semantics Are Preserved
ALOOP-35 — Wrapping Arithmetic Cannot Be Treated As Mathematical Arithmetic
ALOOP-36 — Checked Arithmetic Semantics Are Preserved
ALOOP-37 — Saturating Arithmetic Semantics Are Preserved
ALOOP-38 — Loop Range Facts Require Proof
ALOOP-39 — Range Facts May Feed Bounds-Check Elimination
ALOOP-40 — Unknown Range Never Implies Safety
ALOOP-41 — Loop Dependence Analysis Is Explicit
ALOOP-42 — Loop-Carried Dependencies Must Be Preserved
ALOOP-43 — Unknown Dependence Is Not Treated As Independence
ALOOP-44 — MemorySSA Participates In Dependence Analysis
ALOOP-45 — Alias Proofs May Establish Iteration Independence
ALOOP-46 — Capability Proofs May Establish Iteration Independence
ALOOP-47 — Unknown Alias Never Implies Independence
ALOOP-48 — Loop-Invariant Code Motion Requires Invariance Proof
ALOOP-49 — LICM Must Preserve Memory Semantics
ALOOP-50 — LICM Must Preserve Effect Semantics
ALOOP-51 — LICM Must Preserve Panic Semantics
ALOOP-52 — LICM Must Preserve Drop Semantics
ALOOP-53 — LICM Must Preserve Capability Semantics
ALOOP-54 — Volatile Operations Are Not Freely Movable
ALOOP-55 — Atomic Operations Preserve Atomicity
ALOOP-56 — Atomic Ordering Must Be Preserved
ALOOP-57 — Synchronization Ordering Must Be Preserved
ALOOP-58 — Foreign Effects Are Conservative Without Contracts
ALOOP-59 — Await Boundaries Are Preserved
ALOOP-60 — Suspension Semantics Cannot Be Reordered Arbitrarily
ALOOP-61 — Loop Unswitching Requires Loop-Invariant Condition Proof
ALOOP-62 — Loop Unswitching Must Respect Code-Size Budget
ALOOP-63 — Loop Peeling Preserves Iteration Semantics
ALOOP-64 — Loop Unrolling Preserves Iteration Count
ALOOP-65 — Remainder Loops Preserve Complete Iteration Coverage
ALOOP-66 — Full Unrolling Requires Proven Finite Trip Count
ALOOP-67 — Loop Fusion Requires Dependence Compatibility
ALOOP-68 — Loop Distribution Requires Dependence Compatibility
ALOOP-69 — Loop Versioning Requires Valid Runtime Guards
ALOOP-70 — Runtime Guards Must Preserve Safe Semantics
ALOOP-71 — Loop Interchange Requires Dependence Proof
ALOOP-72 — Loop Tiling Requires Dependence Proof
ALOOP-73 — Reduction Recognition Requires Valid Reduction Proof
ALOOP-74 — Floating-Point Reduction Preserves Declared FP Contract
ALOOP-75 — Strict FP Does Not Permit Unproven Reassociation
ALOOP-76 — Fast FP Contracts May Explicitly Permit Relaxed Transformations
ALOOP-77 — Loop Transformations Cannot Introduce Data Races
ALOOP-78 — Loop Transformations Cannot Invent NoAlias
ALOOP-79 — Loop Transformations Cannot Invent Ownership
ALOOP-80 — Loop Transformations Cannot Extend Capability Lifetime Illegally
ALOOP-81 — Loop Transformations Preserve Exactly-Once Drop
ALOOP-82 — Loop Transformations Preserve Observable Evaluation Order
ALOOP-83 — Loop Transformations Preserve Panic/Trap Behavior
ALOOP-84 — Loop Transformations Declare Analysis Invalidation
ALOOP-85 — Stale Loop Proofs Cannot Authorize Transformations
ALOOP-86 — Loop Transforms Use OptimizationGateway
ALOOP-87 — Failed Loop Transformations Must Preserve Prior Valid IR
ALOOP-88 — Loop Cost Model Cannot Override Legality
ALOOP-89 — Loop Optimization Is Deterministic
ALOOP-90 — Loop Optimization Is Semantics-Preserving
```

---

## 48. Kết quả kiến trúc

Sau `290`, compiler đã có chuỗi khá mạnh:

```text
Ownership
    ↓
Capability
    ↓
Alias
    ↓
MemorySSA
    ↓
Scalar
    ↓
Memory Optimization
    ↓
Loop Analysis
    ↓
Loop Optimization
```

Điểm đáng chú ý là Axiom không cần biến ngôn ngữ thành một “annotation language” để đạt hiệu năng cao.

Programmer viết:

```text
for i in 0..n {
    out[i] = a[i] + b[i]
}
```

Compiler tự tìm:

```text
range proof
      ↓
bounds proof
      ↓
capability proof
      ↓
alias proof
      ↓
memory dependence proof
      ↓
loop independence
      ↓
unroll/vectorization-ready
```

Đây chính là hướng **“compiler hiểu nhiều hơn programmer phải viết”** mà Axiom đang theo đuổi.

**BOOTSTRAP-290 hoàn tất và được đóng băng.**