# BOOTSTRAP-294 — AXIOM PREDICATION, CONTROL-FLOW IF-CONVERSION & BRANCH OPTIMIZATION ENGINE
## FROZEN / COMPLETED

### 1. Mục tiêu

Sau `288` Scalar, `290` Loop, `291` Vectorization Preparation, `292` Inlining và `293` Specialization, Axiom đã có đủ information để xử lý một vấn đề rất quan trọng:

> **Không phải control flow nào tối ưu nhất ở machine level cũng nên giữ nguyên dạng branch.**

Ví dụ source:

```text
if x < 10 {
    a = b
} else {
    a = c
}
```

có thể được biểu diễn ở machine level bằng:

```text
branch
```

nhưng trong một số trường hợp tốt hơn là:

```text
select(predicate, b, c)
```

hoặc:

```text
conditional move
```

hoặc:

```text
masked operation
```

hoặc trong vector code:

```text
mask + blend
```

`294` xây engine quyết định và thực hiện các biến đổi này.

---

# 2. Semantic boundary

Engine này **không thay đổi semantics của control flow**.

Nó chỉ chuyển đổi giữa các biểu diễn tương đương:

```text
Branch
   ↕
Select
   ↕
Predicated operation
   ↕
Mask
```

khi compiler chứng minh:

```text
observable behavior == unchanged
```

Đặc biệt:

> `if` trong Axiom không đồng nghĩa machine code bắt buộc phải có branch.

---

# 3. Pipeline

```text
Verified MIR
      ↓
OptIR
      ↓
CFG / Branch Analysis
      ↓
Predicate Analysis
      ↓
Branch Probability
      ↓
Speculation Safety
      ↓
If-Conversion
      ↓
Predicated IR
      ↓
Scalar / Memory Optimization
      ↓
Vectorization
      ↓
Target Lowering
```

---

# 4. Predicate Model

Compiler cần biểu diễn predicate độc lập với branch instruction:

```text
Predicate {
    condition
    operands
    truth_domain
    source
}
```

Ví dụ:

```text
x < 10
```

được biểu diễn thành semantic predicate:

```text
LT(x, 10)
```

chứ không phụ thuộc x86/ARM instruction.

---

# 5. Branch Information

```text
BranchInfo {
    branch_id
    condition
    true_block
    false_block
    probability
    frequency
    predictable
    side_effects
    speculation_cost
}
```

Nguồn probability:

```text
StaticAnalysis
PGO
LoopAnalysis
RangeAnalysis
```

---

# 6. Branch Probability Không Phải Semantics

Ví dụ PGO cho:

```text
if x == 0
```

thấy:

```text
99% false
1% true
```

Compiler có thể layout:

```text
hot path → fall-through
cold path → branch
```

nhưng không được biến:

```text
99%
```

thành:

```text
always false
```

---

# 7. If-Conversion

Ví dụ:

```text
if cond {
    x = a
} else {
    x = b
}
```

có thể thành:

```text
x = select(cond, a, b)
```

Điều kiện quan trọng:

```text
a
b
```

phải có semantics cho phép evaluate theo dạng select.

---

# 8. Short-Circuit Không Được Phá

Axiom:

```text
a && b
```

không đồng nghĩa:

```text
evaluate a
evaluate b
AND
```

vì `b` chỉ được evaluate khi `a == true`.

Ví dụ:

```text
false && dangerous()
```

không được biến thành:

```text
dangerous()
```

Do đó if-conversion phải hiểu:

```text
short-circuit semantics
```

---

# 9. Side Effects

Không được biến:

```text
if cond {
    io()
} else {
    pure()
}
```

thành:

```text
select(cond, io(), pure())
```

nếu điều này khiến `io()` được thực thi khi `cond == false`.

---

# 10. Panic

Tương tự:

```text
if cond {
    x
} else {
    panic()
}
```

không thể tùy tiện biến thành một biểu thức eager:

```text
select(cond, x, panic())
```

nếu `panic()` bị evaluate trước khi selection.

Compiler phải có:

```text
SpeculationSafety
```

proof.

---

# 11. Speculation Safety

Một expression chỉ được execute speculatively nếu compiler chứng minh việc evaluate nó ngoài original path không tạo observable semantic difference.

Phân loại:

```text
SpeculationClass =
    Safe
    Pure
    NoPanic
    NoFault
    NoIO
    NoSync
    NoForeign
    UnsafeToSpeculate
```

Không dùng heuristic thay cho proof.

---

# 12. Pure Expression

Ví dụ:

```text
a + b
```

với integer semantics thông thường có thể dễ dàng được if-convert.

Nhưng:

```text
foo()
```

phải xem effect summary của `foo`.

---

# 13. Memory Load

Load:

```text
x = a[i]
```

không mặc nhiên được coi là safe để speculate.

Compiler phải xét:

```text
bounds
provenance
alias
lifetime
volatile
atomic
foreign memory
fault semantics
```

Ví dụ `volatile` **không bao giờ** được đối xử như ordinary load.

---

# 14. Atomic

Atomic operation:

```text
atomic_load(x)
```

có thể có ordering semantics.

Không được tự ý biến:

```text
if cond {
    atomic_load(x)
}
```

thành eager:

```text
v = atomic_load(x)
select(cond, v, ...)
```

nếu làm thay đổi observable synchronization behavior.

---

# 15. Volatile

```text
volatile_load
volatile_store
```

là observable machine interaction.

Do đó:

```text
SpeculationClass = UnsafeToSpeculate
```

mặc định.

---

# 16. Synchronization

Các operation:

```text
lock
unlock
channel_send
channel_receive
fence
wait
notify
```

không được if-convert thành eager operations nếu semantics thay đổi.

---

# 17. Drop

Đây là một trường hợp đặc biệt.

```text
if cond {
    use(a)
} else {
    drop(a)
}
```

không thể đơn giản thành select nếu ownership state thay đổi.

If-conversion phải bảo toàn:

```text
Move
Drop
PartialMove
Capability
```

---

# 18. Ownership-Aware Predication

Compiler có thể biểu diễn:

```text
if cond {
    x = move(a)
} else {
    x = move(b)
}
```

thành semantic phi:

```text
x = phi(move(a), move(b))
```

nhưng ownership verifier phải hiểu rằng:

```text
exactly one
```

branch thực sự consumes ownership.

Không được tạo hai Move.

---

# 19. Capability-Aware Predication

Ví dụ:

```text
if cond {
    write(mut_view_a)
} else {
    write(mut_view_b)
}
```

Nếu:

```text
a
b
```

có thể overlap:

```text
UNKNOWN
```

thì compiler không được tự động coi chúng là independent.

---

# 20. Region Predicate

Compiler có thể có:

```text
if cond {
    access(R1)
} else {
    access(R2)
}
```

Nếu:

```text
R1 DISJOINT R2
```

thì nhiều biến đổi an toàn hơn.

Nhưng:

```text
UNKNOWN
```

không được suy ra:

```text
DISJOINT
```

---

# 21. Select Representation

Axiom OptIR cần có semantic operation:

```text
Select {
    condition
    true_value
    false_value
}
```

`Select` không có nghĩa:

```text
machine cmov
```

nó chỉ có nghĩa:

```text
value chosen by predicate
```

Backend sau này quyết định:

```text
branch
cmov
csel
blend
mask
predicated instruction
```

---

# 22. Predicated Memory Operation

Đối với vector/mask, cần representation:

```text
MaskedLoad {
    mask
    address
    passthrough
}

MaskedStore {
    mask
    address
    value
}
```

Nhưng đây là **semantic target-independent operation**, không phải AVX instruction.

---

# 23. Vector Mask

Ví dụ:

```text
if (x[i] > 0) {
    y[i] = x[i]
}
```

sau vectorization có thể:

```text
mask = x > 0
y = blend(mask, x, y)
```

hoặc:

```text
masked_store(mask, x)
```

`294` cung cấp control-flow transformation; `291` quyết định vector legality.

---

# 24. Branch Elimination

Các trường hợp:

```text
if true
if false
```

đã có thể xử lý ở scalar engine.

`294` mở rộng sang:

```text
constant-like predicate
provable predicate
range predicate
profile-guided layout
predication
```

---

# 25. Range-Based Branch Simplification

Ví dụ:

```text
if x < 10 {
    ...
}

if x >= 10 {
    ...
}
```

Nếu RangeInfo chứng minh:

```text
0 <= x < 10
```

branch thứ hai unreachable.

Engine phải gửi fact tới CFG simplifier.

---

# 26. Correlated Branches

Ví dụ:

```text
if x < 10 {
    ...
}

if x >= 10 {
    ...
}
```

hai branch có correlation.

Compiler không nên phân tích độc lập nếu có thể giữ predicate relation.

Cần:

```text
PredicateFacts
```

để truyền:

```text
x < 10
```

vào true branch và:

```text
x >= 10
```

vào false branch.

---

# 27. Predicate Simplification

Ví dụ:

```text
(x < 10) && (x < 20)
```

có thể trở thành:

```text
x < 10
```

nếu semantics của comparisons cho phép.

Tương tự:

```text
(x < 10) || (x >= 10)
```

có thể trở thành `true` nếu domain semantics chứng minh đầy đủ.

Không được áp dụng luật toán học sai với:

```text
NaN
overflow
poison-like values
```

Axiom không có C-style UB để optimizer lợi dụng.

---

# 28. Integer Semantics

Ví dụ signed integer:

```text
x + 1
```

Axiom phải biết chính xác đây là:

```text
checked
wrapping
saturating
```

mode nào.

Không được dùng:

```text
x + 1 > x
```

như một theorem chung nếu arithmetic mode cho phép wrap.

---

# 29. Floating-Point Predicate

Không được giả định:

```text
x == x
```

luôn true.

NaN phải được giữ đúng semantics.

Tương tự:

```text
x < y
```

phải giữ unordered/NaN semantics theo floating-point model của Axiom.

---

# 30. Signed Zero

Các biến đổi:

```text
x == 0
```

và:

```text
x > 0
```

không được coi đơn giản như integer comparison.

`+0` và `-0` có thể observable trong một số floating-point operations.

---

# 31. Strict FP

Trong strict FP:

```text
if x < y
```

phải giữ semantics chính xác.

Không được biến control flow thành algebraic simplification chỉ vì cost tốt hơn.

---

# 32. Fast FP

Nếu program/profile cho phép explicit fast-math semantics, compiler có thể dùng thêm transformations.

Nhưng:

```text
FastFP
```

phải là semantic contract rõ ràng.

Không được compiler tự bật vì `-O3`.

---

# 33. Branch Layout

Không phải mọi branch đều nên bị loại.

Đôi khi:

```text
branch
```

tốt hơn:

```text
cmov
```

vì branch highly predictable.

Cost model cần xem:

```text
branch_probability
misprediction_cost
instruction_cost
dependency_chain
register_pressure
code_size
target_uarch
```

---

# 34. If-Conversion Cost

```text
if cond {
    a = expensive()
} else {
    b = cheap()
}
```

Predication có thể khiến `expensive()` luôn chạy.

Do đó:

```text
semantic legality
```

có thể đúng nhưng:

```text
profitability
```

lại sai.

---

# 35. Branch vs Select

Compiler có thể lựa chọn:

```text
Branch
Select
CMOV
CSEL
Mask
```

theo target.

OptIR chỉ cần:

```text
semantic select
```

Target backend quyết định instruction sequence.

---

# 36. Tail Duplication

Một kỹ thuật quan trọng:

```text
      A
     / \
    B   C
     \ /
      D
```

có thể duplicate một phần `D` để giảm branch hoặc expose optimization.

Nhưng phải giới hạn code-size growth.

---

# 37. Jump Threading

Ví dụ:

```text
if cond1 {
    ...
}

if cond1 {
    A
} else {
    B
}
```

Nếu cùng predicate:

```text
cond1
```

compiler có thể thread CFG.

Nhưng ownership/capability facts phải được cập nhật.

---

# 38. Branch Folding

Nếu:

```text
A → B
A → C
```

và:

```text
B == C
```

có thể merge.

Không được merge nếu:

```text
Drop
Panic
IO
Atomic
Volatile
Synchronization
```

có observable ordering khác nhau.

---

# 39. Empty Branch

```text
if cond {
}
```

có thể loại bỏ nếu condition không có observable evaluation effect.

Nhưng nếu condition là:

```text
foo()
```

thì effect của `foo()` vẫn phải giữ.

---

# 40. Branch Prediction Metadata

OptIR có:

```text
BranchProbability
BranchFrequency
Hotness
```

nhưng đây là:

```text
optimization metadata
```

không phải semantic fact.

Nếu metadata mất:

```text
program remains correct
```

---

# 41. PGO

PGO có thể thay đổi:

```text
block layout
branch order
if-conversion profitability
tail duplication
```

nhưng không được thay đổi semantic result.

---

# 42. CPU Target

Target backend có thể báo:

```text
TargetBranchModel {
    branch_cost
    mispredict_cost
    cmov_cost
    predication_support
    vector_mask_support
}
```

Engine không hard-code x86/ARM.

---

# 43. GPU

GPU thường dùng:

```text
SIMT divergence
```

thay vì CPU-style branch prediction.

Do đó cùng một semantic predicate:

```text
if cond
```

có thể được lower thành:

```text
mask
```

hoặc:

```text
divergent control flow
```

tùy target.

Không được dùng CPU cost model cho GPU.

---

# 44. Async

Async state machine cũng có branch:

```text
switch(state)
```

Engine có thể simplify state transitions nếu proof cho phép.

Nhưng không được merge hai suspension states nếu chúng có:

```text
different live state
Drop behavior
Send requirements
observable ordering
```

---

# 45. Panic Paths

Compiler có thể layout:

```text
hot normal path
```

và:

```text
cold panic path
```

tách nhau.

Nhưng panic vẫn là semantic effect.

Do đó:

```text
cold
```

không có nghĩa:

```text
removable
```

---

# 46. Effect-Aware Speculation

Một operation chỉ được speculate nếu effect summary chứng minh:

```text
no new observable effect
```

Ví dụ:

```text
Read
```

có thể vẫn cần region/alias proof.

```text
IO
Foreign
Synchronize
Volatile
```

mặc định không speculate.

---

# 47. Memory Dependence

Nếu:

```text
if cond {
    store(A)
}
load(B)
```

muốn hoist:

```text
load(B)
```

ra ngoài branch, compiler cần:

```text
NoAlias(A, B)
```

hoặc MemorySSA chứng minh không conflict.

Không được dựa vào source syntax.

---

# 48. Capability Proof

Nếu:

```text
store(mut_view<A>)
load(view<B>)
```

và compiler có:

```text
A DISJOINT B
```

thì speculation có thể an toàn hơn.

Đây là nơi:

```text
282 Capability
289 Memory
294 Control Flow
```

kết hợp.

---

# 49. Proof Gateway

Mọi transformation:

```text
if-conversion
jump-threading
tail-duplication
predication
branch-folding
```

đều phải đi qua:

```text
OptimizationGateway
```

và khai báo:

```text
required proofs
preserved facts
invalidated analyses
```

---

# 50. IR Update

Sau CFG transformation phải cập nhật:

```text
SSA
MemorySSA
DominatorTree
PostDominatorTree
LoopTree
BranchInfo
EffectInfo
Ownership facts
Capability facts
SourceMap
```

Không được giữ analysis cũ nếu transformation invalidated nó.

---

# 51. Transactional Transformation

```text
Candidate
   ↓
Legality
   ↓
Cost
   ↓
Plan
   ↓
Apply
   ↓
Rebuild / Update CFG
   ↓
Reverify
   ↓
Commit
```

Nếu validation thất bại:

```text
rollback
```

---

# 52. Module Structure

```text
compiler/optimization/control/
├── mod.ax
│
├── predicate/
│   ├── mod.ax
│   ├── predicate.ax
│   ├── simplify.ax
│   ├── relation.ax
│   └── facts.ax
│
├── branch/
│   ├── mod.ax
│   ├── probability.ax
│   ├── frequency.ax
│   ├── layout.ax
│   ├── folding.ax
│   └── threading.ax
│
├── if_conversion/
│   ├── mod.ax
│   ├── legality.ax
│   ├── speculation.ax
│   ├── select.ax
│   ├── predication.ax
│   └── cost.ax
│
├── speculation/
│   ├── mod.ax
│   ├── effects.ax
│   ├── memory.ax
│   ├── panic.ax
│   ├── drop.ax
│   └── capability.ax
│
├── duplication/
│   ├── mod.ax
│   ├── tail_duplication.ax
│   └── cost.ax
│
├── gpu/
│   ├── mod.ax
│   ├── divergence.ax
│   └── mask.ax
│
├── async/
│   ├── mod.ax
│   └── state_simplify.ax
│
└── tests/
```

---

# 53. Implementation Order

```text
1. Predicate representation
2. Predicate relation engine
3. Branch probability model
4. Branch frequency model
5. Predicate simplification
6. Correlated predicate propagation
7. Branch folding
8. CFG threading
9. Branch layout
10. Speculation classification
11. Effect-aware speculation
12. Memory-aware speculation
13. Panic-aware speculation
14. Drop-aware speculation
15. Capability-aware speculation
16. Select IR
17. If-conversion legality
18. If-conversion cost model
19. Scalar select transformation
20. Predicated operation model
21. Vector mask integration
22. Tail duplication
23. Branch merging
24. CPU target cost integration
25. GPU divergence/mask integration
26. Async state simplification
27. SSA update
28. MemorySSA update
29. Loop update
30. Proof Gateway integration
31. Pass Manager integration
32. PGO integration
33. optimization remarks
34. adversarial tests
```

---

# 54. Adversarial Tests

### Test 1 — Simple select

```text
if cond {
    x = a
} else {
    x = b
}
```

→ có thể chuyển thành semantic `Select`.

### Test 2 — Side effect

```text
if cond {
    io()
}
```

không được eager-evaluate `io()`.

### Test 3 — Panic

```text
if cond {
    x
} else {
    panic()
}
```

panic chỉ xảy ra trên đúng path.

### Test 4 — Volatile

Không được speculate volatile load/store.

### Test 5 — Atomic

Không được thay đổi atomic ordering.

### Test 6 — Drop

Không được duplicate/drop resource sai số lần.

### Test 7 — Capability

Không được tạo alias mutable.

### Test 8 — Unknown alias

`UNKNOWN` không được coi là `NO_ALIAS`.

### Test 9 — NaN

Predicate floating-point phải giữ semantics.

### Test 10 — Signed zero

Không được biến đổi FP comparison sai.

### Test 11 — Wrapping integer

Không dùng algebraic theorem của mathematical integers khi Axiom đang wrapping.

### Test 12 — Short circuit

Không được evaluate RHS sớm.

### Test 13 — Branch prediction

PGO thay đổi layout nhưng không thay đổi result.

### Test 14 — Tail duplication

Code size budget phải được tôn trọng.

### Test 15 — GPU divergence

CPU branch heuristic không được áp dụng trực tiếp cho GPU.

### Test 16 — Async

Không được merge suspension states không tương đương.

---

# 55. Frozen Invariants

### `ACTRL-20..100`

```text
ACTRL-20 — Control-Flow Optimization Must Preserve Observable Semantics
ACTRL-21 — Predicate Representation Is Target Independent
ACTRL-22 — Branch Probability Is Optimization Metadata
ACTRL-23 — Branch Probability Is Not A Semantic Fact
ACTRL-24 — Unknown Predicate Facts Remain Unknown
ACTRL-25 — Correlated Predicates Must Preserve Path Conditions
ACTRL-26 — If-Conversion Requires Semantic Equivalence
ACTRL-27 — Select Does Not Imply Eager Evaluation Of Both Branches
ACTRL-28 — Speculation Requires A Valid Safety Proof
ACTRL-29 — Observable Effects Must Not Be Speculated Illegally
ACTRL-30 — IO Is Not Speculatively Executable By Default
ACTRL-31 — Foreign Calls Are Not Speculatively Executable By Default
ACTRL-32 — Synchronization Is Not Speculatively Executable By Default
ACTRL-33 — Volatile Operations Are Not Ordinary Speculative Operations
ACTRL-34 — Atomic Ordering Must Be Preserved
ACTRL-35 — Panic Semantics Must Be Preserved
ACTRL-36 — Drop Semantics Must Be Preserved
ACTRL-37 — Move Semantics Must Be Preserved
ACTRL-38 — Initialization Semantics Must Be Preserved
ACTRL-39 — Capability Provenance Must Be Preserved
ACTRL-40 — Control-Flow Optimization Must Not Create Safe Aliasing
ACTRL-41 — UNKNOWN Alias Must Not Become NO_ALIAS
ACTRL-42 — Memory Speculation Requires Valid Memory Proof
ACTRL-43 — Short-Circuit Evaluation Must Be Preserved
ACTRL-44 — Integer Overflow Semantics Must Be Preserved
ACTRL-45 — Wrapping Arithmetic Must Not Use Mathematical Integer Assumptions
ACTRL-46 — Checked Arithmetic Must Preserve Failure Semantics
ACTRL-47 — Saturating Arithmetic Must Preserve Saturation
ACTRL-48 — Floating-Point NaN Semantics Must Be Preserved
ACTRL-49 — Floating-Point Signed-Zero Semantics Must Be Preserved
ACTRL-50 — Strict-FP Transformations Must Preserve Strict Semantics
ACTRL-51 — Fast-FP Transformations Require Explicit Fast-FP Semantics
ACTRL-52 — Branch Layout May Depend On Profile Data
ACTRL-53 — Profile Data Cannot Change Program Semantics
ACTRL-54 — If-Conversion Legality Is Distinct From Profitability
ACTRL-55 — Cost Models Cannot Override Legality
ACTRL-56 — Conditional Execution Must Not Introduce Unwanted Effects
ACTRL-57 — Tail Duplication Is Code-Size Budgeted
ACTRL-58 — Jump Threading Must Preserve Path Conditions
ACTRL-59 — Branch Merging Must Preserve Effect Ordering
ACTRL-60 — CFG Transformations Must Update SSA
ACTRL-61 — CFG Transformations Must Update MemorySSA
ACTRL-62 — CFG Transformations Must Update Loop Information
ACTRL-63 — Invalidated Analyses Must Not Be Reused
ACTRL-64 — Proofs Invalidated By CFG Changes Cannot Authorize Later Transforms
ACTRL-65 — Transformations Must Use OptimizationGateway
ACTRL-66 — Transformations Are Transactional
ACTRL-67 — Failed Transformations Preserve Prior Valid IR
ACTRL-68 — GPU Control Flow Uses GPU-Specific Cost Models
ACTRL-69 — GPU Divergence Must Be Represented Explicitly
ACTRL-70 — GPU Masks Must Preserve Kernel Semantics
ACTRL-71 — Async State Transitions Must Preserve Suspension Semantics
ACTRL-72 — Async Drop State Must Be Preserved
ACTRL-73 — Async Send Requirements Must Be Preserved
ACTRL-74 — Control-Flow Optimization Must Preserve Execution Domains
ACTRL-75 — Control-Flow Optimization Must Preserve Storage Domains
ACTRL-76 — Panic Paths May Be Cold But Remain Semantic
ACTRL-77 — Cold Does Not Mean Removable
ACTRL-78 — Hot Does Not Mean Speculatively Safe
ACTRL-79 — Runtime Guards Require Correct Fallback Paths
ACTRL-80 — Runtime Guards Must Match Their Proven Preconditions
ACTRL-81 — Target Instruction Choice Is Separate From Semantic Control Flow
ACTRL-82 — Select Is Not An ISA Instruction
ACTRL-83 — Predication Is Not An ISA-Specific Semantic
ACTRL-84 — Target Backend Determines Final Branch/Select Encoding
ACTRL-85 — Worker Count Must Not Affect Transformation Semantics
ACTRL-86 — PGO Must Not Affect Correctness
ACTRL-87 — Debug Provenance Must Survive CFG Transformation
ACTRL-88 — Source Mapping Must Remain Bidirectional
ACTRL-89 — Optimization Decisions Must Be Explainable
ACTRL-90 — Control Optimization Must Not Depend On Undefined Behavior
ACTRL-91 — Branch Elimination Requires A Reachability Proof
ACTRL-92 — Unreachable Paths Must Be Proven, Not Guessed
ACTRL-93 — Effect Ordering Must Remain Observable-Equivalent
ACTRL-94 — Ownership Verification Remains Required After Transformation
ACTRL-95 — Capability Verification Remains Required After Transformation
ACTRL-96 — Reverification Is Required Before Publishing Transformed IR
ACTRL-97 — Optimization Cache Presence Must Not Affect Semantics
ACTRL-98 — Control-Flow Optimization Is Optional
ACTRL-99 — Failure To Optimize Never Constitutes A Compilation Error
ACTRL-100 — Control-Flow Optimization Is A Physical Representation Optimization, Not A Language Semantic
```

---

## 56. Kết quả

Axiom giờ có thêm một tầng quan trọng:

```text
Source:
    if / match / loop / async

        ↓

Semantic CFG

        ↓

Predicate Analysis

        ↓

┌─────────────────────────────┐
│ Branch                      │
│ Select                      │
│ Predication                 │
│ Mask                        │
│ Branch Layout               │
│ Jump Threading              │
│ Tail Duplication            │
└─────────────────────────────┘

        ↓

Target-independent OptIR

        ↓

CPU / GPU backend
```

Điểm quan trọng là **Axiom không ép programmer phải viết code “thân thiện với branch predictor” hay SIMD**. Programmer viết semantics rõ ràng; compiler quyết định representation vật lý dựa trên proof + target + profile.

**BOOTSTRAP-294 hoàn tất và được đóng băng.**