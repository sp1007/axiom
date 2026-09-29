# BOOTSTRAP-288 — AXIOM SCALAR OPTIMIZATION ENGINE
## FROZEN / COMPLETED

### 1. Mục tiêu

Sau `287`, Axiom đã có **Pass Manager**. Bước tiếp theo là triển khai nhóm optimization đầu tiên có ảnh hưởng trực tiếp đến chất lượng machine code:

> **Scalar Optimization** — tối ưu các giá trị đơn, biểu thức, SSA values, control flow và phép tính mà không cần biết cụ thể CPU nào.

Đây là tầng nền cho:

```text
constant folding
constant propagation
SCCP
copy propagation
dead code elimination
dead store elimination
algebraic simplification
InstCombine
GVN
PRE
strength reduction
range simplification
branch simplification
```

Mục tiêu không phải tạo một optimizer “nhiều pass”, mà là:

> **Mỗi transform phải dựa trên semantic facts + proof, không được dựa trên giả định UB kiểu C/C++.**

---

# 2. Vị trí trong pipeline

```text
Verified MIR
      │
      ▼
OptIR
      │
      ▼
Canonicalization
      │
      ▼
SSA
      │
      ▼
Scalar Analysis
      │
      ▼
Scalar Optimization
      │
      ├── Constant Folding
      ├── SCCP
      ├── Copy Propagation
      ├── InstCombine
      ├── GVN
      ├── DCE
      ├── Branch Simplification
      └── Strength Reduction
      │
      ▼
Simplified OptIR
      │
      ▼
Memory / Loop / Vectorization
```

Scalar optimization phải chạy trước nhiều nhóm optimization cấp cao hơn.

---

# 3. Nguyên tắc quan trọng: Semantic Arithmetic

Axiom không được kế thừa tư duy:

```text
signed overflow = UB
```

của C/C++.

Ví dụ nếu Axiom định nghĩa:

```text
i32
```

có semantic overflow rõ ràng, optimizer phải tôn trọng semantic đó.

Các phép toán có thể có:

```text
checked_add
wrapping_add
saturating_add
```

hoặc semantic tương đương.

Do đó optimizer chỉ được biến:

```text
x + 0 → x
```

khi phép biến đổi đúng với **toàn bộ domain hợp lệ của kiểu và operation**.

---

# 4. ScalarValue

Scalar analysis cần một abstraction thống nhất:

```text
ScalarValue {
    type: TypeId

    lattice:
        Unknown
        Constant
        Range
        KnownBoolean
        KnownIntegerBits
        Overdefined
}
```

Ví dụ:

```text
x = 5
```

→

```text
Constant(5)
```

Trong khi:

```text
x = input()
```

→

```text
Unknown
```

Sau:

```text
if x < 10
```

branch-specific analysis có thể biết:

```text
true branch:
    x ∈ (-∞, 9]

false branch:
    x ∈ [10, +∞)
```

---

# 5. Scalar Lattice

```text
             Unknown
                │
                ▼
             Constant
                │
             Range/Fact
                │
                ▼
           Overdefined
```

Thực tế lattice không nhất thiết là một chuỗi tuyến tính; compiler cần hỗ trợ nhiều loại facts đồng thời.

Ví dụ:

```text
x = 4
```

có thể đồng thời có:

```text
Constant = 4
Range = [4,4]
KnownBits = exact
NonZero = true
```

---

# 6. Constant Folding

Compiler phải thực hiện:

```text
2 + 3 → 5
```

```text
4 * 0 → 0
```

nhưng phải kiểm tra semantic operation.

Ví dụ:

```text
checked_div(x, 0)
```

không được biến thành một constant bình thường nếu semantic là panic/trap.

---

# 7. Constant Evaluation

Constant evaluator phải dùng cùng semantic arithmetic với Axiom runtime.

```text
Runtime semantics
        ▲
        │
        └──── same semantic operation ──── Comptime
```

Không được có:

```text
comptime arithmetic
    ≠
runtime arithmetic
```

trừ khi operation được định nghĩa rõ là compile-time-only.

---

# 8. Constant Propagation

Ví dụ:

```text
let a = 10
let b = a + 20
return b
```

→

```text
return 30
```

Nhưng ownership/capability semantics vẫn phải được bảo toàn.

Đặc biệt:

```text
Move(x)
```

không thể bị biến thành `Copy(x)` chỉ vì giá trị cuối cùng giống nhau.

---

# 9. SCCP

Axiom sử dụng:

> **Sparse Conditional Constant Propagation**

để đồng thời suy luận:

```text
constant values
+
reachable blocks
```

Ví dụ:

```text
if false {
    foo()
} else {
    bar()
}
```

SCCP biết:

```text
true successor = unreachable
```

và có thể loại bỏ block.

---

# 10. Nhưng unreachable ≠ semantic erase tùy tiện

Nếu source chứa:

```text
if false {
    invalid_operation()
}
```

sau khi compiler đã chứng minh condition compile-time false, code unreachable có thể được loại bỏ.

Nhưng nếu:

```text
if runtime_condition {
    operation_that_may_panic()
}
```

thì không được xóa chỉ vì branch “có vẻ hiếm”.

Panic là observable effect.

---

# 11. Copy Propagation

Ví dụ:

```text
a = b
c = a
```

→

```text
c = b
```

nhưng chỉ khi việc thay thế không phá:

```text
Move
Drop
Capability
Storage
Address identity
```

Đặc biệt:

```text
Copy(x)
```

không được tự động đổi thành:

```text
Move(x)
```

---

# 12. InstCombine

Tạo một engine canonicalization:

```text
InstCombine {
    match
    prove
    rewrite
    validate
}
```

Ví dụ:

```text
x + 0 → x
x * 1 → x
x & all_ones → x
x | 0 → x
```

Nhưng mỗi rewrite phải có semantic proof.

Không được có một bảng rewrite đơn giản kiểu:

```text
pattern → replacement
```

mà không kiểm tra type/effect/overflow/panic.

---

# 13. Algebraic Simplification

Ví dụ:

```text
(x * 2) + (x * 2)
```

có thể thành:

```text
x * 4
```

nhưng chỉ nếu operation semantics cho phép.

Đối với floating point:

```text
(x + y) + z
```

không mặc định bằng:

```text
x + (y + z)
```

vì IEEE-754 rounding có thể khác.

Do đó floating-point optimization phải có rule riêng.

---

# 14. Floating Point Semantics

Axiom phải phân biệt:

```text
StrictFP
FastFP
```

hoặc semantic equivalent.

### Strict

Không được:

```text
reassociate
change rounding
ignore NaN/Inf behavior
```

nếu làm thay đổi observable semantics.

### Fast

Compiler có thể áp dụng một tập transform mạnh hơn nếu programmer đã chọn semantic profile cho phép.

Nhưng đây phải là **language/compiler semantic contract**, không phải optimizer tự suy diễn.

---

# 15. Boolean Simplification

Ví dụ:

```text
true && x → x
false && x → false
true || x → true
false || x → x
```

nhưng short-circuit evaluation phải được giữ.

Ví dụ:

```text
false && panic()
```

có thể loại bỏ RHS vì RHS không được evaluate.

Nhưng:

```text
foo() && bar()
```

không được biến thành một phép boolean bình thường nếu điều đó làm thay đổi evaluation order/effects.

---

# 16. Evaluation Order

Axiom đã có deterministic evaluation order.

Scalar optimizer phải coi nó là semantic constraint.

Ví dụ:

```text
f() + g()
```

nếu Axiom quy định `f()` trước `g()`, optimizer không được đảo thành:

```text
g() + f()
```

nếu hai call có observable effects hoặc panic behavior.

---

# 17. GVN

Global Value Numbering:

```text
a = x + y
b = x + y
```

có thể:

```text
b = a
```

nếu hai expression semantic-equivalent và không có effect làm kết quả thay đổi.

Compiler phải xét:

```text
memory invalidation
volatile
atomic
foreign calls
IO
synchronization
```

---

# 18. Memory-Aware GVN

Ví dụ:

```text
a = load(x)
foo()
b = load(x)
```

Không được mặc định:

```text
b = a
```

nếu:

```text
foo()
```

có thể ghi `x`.

Effect + Alias analysis phải cung cấp proof:

```text
NoWrite(foo, x)
```

thì mới được reuse.

Đây là nơi `283 + 282 + 285 + 286` bắt đầu trực tiếp phục vụ optimizer.

---

# 19. DCE

Dead Code Elimination chỉ được xóa instruction khi:

```text
result unused
AND
no observable effect
```

Ví dụ:

```text
x = a + b
```

không dùng `x` → có thể xóa.

Nhưng:

```text
x = may_panic()
```

không được xóa chỉ vì return value không dùng nếu panic là observable.

---

# 20. Observable Effect

Scalar optimizer phải sử dụng EffectSystem:

```text
ObservableEffect =
    IO
    Panic
    Volatile
    Atomic
    Synchronize
    Foreign
    Spawn
    Await
    GpuLaunch
    DeviceTransfer
    ...
```

Một phép tính local thuần túy có thể bị loại bỏ.

Một phép tính có observable effect thì không.

---

# 21. Dead Store

Ví dụ:

```text
x = 1
x = 2
use(x)
```

store đầu có thể bị loại bỏ nếu:

```text
NoObservableRead(x)
```

được chứng minh.

Nhưng:

```text
volatile_store(x, 1)
```

không được DSE.

---

# 22. Branch Simplification

Ví dụ:

```text
if true {
    A
} else {
    B
}
```

→

```text
A
```

Các transform:

```text
constant branch
empty branch
identical successors
branch threading
switch simplification
unreachable block removal
```

phải giữ cleanup/drop semantics.

---

# 23. Drop là Observable Semantic

Ví dụ:

```text
let x = Resource()
if condition {
    return
}
```

Không thể chỉ xóa variable `x` vì không dùng giá trị.

`Drop(x)` có thể:

```text
close resource
release lock
deallocate
perform observable action
```

Do đó DCE phải hỏi:

```text
DoesDropHaveObservableEffect?
```

Nếu không chứng minh được:

```text
do not remove
```

---

# 24. Strength Reduction

Ví dụ:

```text
x * 2
```

có thể chuyển thành shift nếu semantics tương đương.

Nhưng:

```text
x / 2
```

đặc biệt với signed integer phải xét rounding semantics.

Không được áp dụng các identity từ toán học thuần túy nếu chúng không đúng với machine semantics.

---

# 25. Range Simplification

Nếu compiler biết:

```text
0 <= x < 10
```

thì:

```text
if x < 20
```

có thể thành:

```text
true
```

Range facts đến từ:

```text
comparison
branch condition
array bounds
constant propagation
loop analysis
function contracts
```

Proof:

```text
ProvenRange(x, [0,9])
```

mới cho phép transform.

---

# 26. Branch-Sensitive Facts

Ví dụ:

```text
if x == 0 {
    ...
} else {
    ...
}
```

Trong true branch:

```text
x == 0
```

Trong false branch:

```text
x != 0
```

Các facts này phải tồn tại theo CFG path.

Không được đưa:

```text
x != 0
```

ra ngoài branch nếu chưa có proof dominance/path merge thích hợp.

---

# 27. Phi Simplification

SSA:

```text
x = φ(a, a)
```

→

```text
x = a
```

Nếu cùng value thực sự tương đương.

Tương tự:

```text
φ(unreachable, a)
```

→

```text
a
```

sau khi CFG proof xác nhận predecessor unreachable.

---

# 28. SCCP + Ownership

Một điểm riêng của Axiom:

```text
if condition {
    x = Move(a)
}
```

Nếu SCCP loại bỏ branch chứa `Move(a)`, ownership analysis phải được cập nhật.

Do đó transform không được chỉ sửa SSA.

Nó phải tạo semantic update:

```text
CFG changed
    ↓
Ownership facts invalidated
    ↓
re-analysis
```

Đây là lý do `287` yêu cầu explicit invalidation.

---

# 29. Scalar Optimization không được phá capability

Ví dụ:

```text
v = view(x)
use(v)
```

Optimizer có thể inline/eliminate `v`.

Nhưng semantic capability:

```text
READ capability(v)
```

vẫn phải được chứng minh tương đương.

Physical elimination:

```text
view object removed
```

không đồng nghĩa:

```text
capability semantics removed
```

nếu access vẫn tồn tại.

---

# 30. Scalar Optimization không được tạo alias mới

Transform:

```text
a = b
```

→

```text
a = optimized_value_of_b
```

không được làm thay đổi semantic alias relationship của các địa chỉ.

Đặc biệt không được biến:

```text
value
```

thành:

```text
reference
```

chỉ để optimization.

---

# 31. Scalar Optimization không được tạo allocation

Scalar pass có thể **eliminate** allocation nếu proof cho phép.

Nhưng không nên tự tạo heap allocation chỉ vì một transform tiện lợi.

Ví dụ:

```text
temporary value
```

nên ưu tiên:

```text
SSA/register/stack
```

thay vì:

```text
heap object
```

trừ khi representation contract yêu cầu.

---

# 32. Scalar Optimization và Function Calls

Call được phân loại:

```text
Direct
Generic
Closure
Dynamic
Foreign
Intrinsic
Unknown
```

Scalar optimizer có thể tận dụng:

```text
Pure
NoPanic
NoWrite
NoEscape
NoSuspend
```

nếu có proof.

Unknown call:

```text
conservative
```

---

# 33. Inlining

Inlining là optimization quan trọng nhưng **không nên nằm hoàn toàn trong Scalar Engine**.

Scalar engine chỉ cung cấp:

```text
post-inline simplification
```

Pass riêng:

```text
Inline
```

sẽ được xây ở tầng interprocedural optimization sau.

Sau inline:

```text
new constants
new branches
new effects
new alias facts
```

→ Scalar optimizer chạy lại.

---

# 34. Scalar Pipeline

Pipeline v1:

```text id="2f6j89"
Canonicalize
    ↓
SCCP
    ↓
InstCombine
    ↓
CopyPropagation
    ↓
GVN
    ↓
DCE
    ↓
SimplifyCFG
    ↓
SCCP
    ↓
InstCombine
    ↓
DCE
```

Lặp tới fixed point với budget.

Không cần ép mỗi pass chạy đúng một lần.

---

# 35. OptIR Scalar Analysis

```text id="k9f9s7"
ScalarAnalysis {
    constants
    ranges
    known_bits
    predicates
    reachable_blocks
    value_numbers
    poison_state
    fp_semantics
}
```

Axiom nên tránh khái niệm `poison` theo cách LLVM dùng nếu semantics Axiom không cần nó.

Thay vào đó nên biểu diễn rõ:

```text
Valid
Trap
Panic
UndefinedRepresentation
Unreachable
```

và không tạo một “giá trị ma” làm nguồn suy luận tùy tiện.

---

# 36. Trap / Panic Domain

Một expression có thể có:

```text
AlwaysReturns
MayPanic
AlwaysPanic
Unreachable
```

Ví dụ:

```text
1 / 0
```

nếu Axiom định nghĩa là panic:

```text
AlwaysPanic
```

Compiler có thể dùng fact này để simplify control flow:

```text
foo();
1 / 0;
bar();
```

→ `bar()` unreachable.

Nhưng vẫn phải giữ semantic panic.

---

# 37. Division Optimization

Ví dụ:

```text
x / 1 → x
```

có thể safe.

Nhưng:

```text
x / constant
```

→ multiplication by reciprocal

chỉ được làm khi:

- integer semantics tương đương, hoặc
- floating profile cho phép, hoặc
- target-specific transform có proof.

---

# 38. Integer Semantics

Optimizer cần biết:

```text
SignedOverflowMode
UnsignedOverflowMode
ShiftMode
DivisionMode
RemainderMode
```

Không hard-code semantics theo CPU.

Machine backend phải implement semantic contract của Axiom.

---

# 39. Fast Math

Nếu Axiom hỗ trợ fast-math, nên định nghĩa các flag/semantic capabilities ở cấp IR:

```text
FastMathMode {
    AllowReassociation
    AllowReciprocal
    IgnoreNaN
    IgnoreInf
    Approximate
}
```

Không nên dùng compiler global flag mơ hồ.

Mỗi operation/region phải biết contract.

---

# 40. Cost Model

Scalar transform thường rất rẻ, nhưng vẫn có cost:

```text
instruction_count
latency
throughput
register_pressure
code_size
```

Ví dụ:

```text
x * constant
```

có thể thành:

```text
shift + add + add
```

nhưng trên một CPU cụ thể:

```text
multiply
```

có thể nhanh hơn.

Vì vậy:

```text
legal transform
+
target cost
```

mới quyết định.

---

# 41. Target Independence

Scalar semantics không được phụ thuộc trực tiếp vào x86/ARM/RISC-V.

Thay vào đó:

```text
Scalar Optimization
       │
       ▼
Target Cost Model
       │
       ▼
Target decision
```

Điều này giữ compiler frontend/optimizer sạch.

---

# 42. Module Structure

```text id="7y4zjp"
compiler/optimization/scalar/
├── mod.ax
│
├── lattice/
│   ├── mod.ax
│   ├── scalar_value.ax
│   ├── constant.ax
│   ├── range.ax
│   ├── known_bits.ax
│   ├── predicate.ax
│   └── merge.ax
│
├── analysis/
│   ├── mod.ax
│   ├── scalar_analysis.ax
│   ├── reachable.ax
│   ├── value_number.ax
│   ├── range_analysis.ax
│   └── constant_analysis.ax
│
├── constant/
│   ├── mod.ax
│   ├── evaluator.ax
│   ├── folding.ax
│   └── semantics.ax
│
├── sccp/
│   ├── mod.ax
│   ├── sccp.ax
│   ├── lattice.ax
│   └── tests.ax
│
├── combine/
│   ├── mod.ax
│   ├── matcher.ax
│   ├── rewrite.ax
│   ├── integer.ax
│   ├── float.ax
│   ├── boolean.ax
│   └── casts.ax
│
├── propagation/
│   ├── mod.ax
│   ├── copy.ax
│   └── constant.ax
│
├── gvn/
│   ├── mod.ax
│   ├── gvn.ax
│   ├── expression_key.ax
│   └── memory_dependency.ax
│
├── dce/
│   ├── mod.ax
│   ├── dce.ax
│   └── observable.ax
│
├── cfg/
│   ├── mod.ax
│   ├── branch_simplify.ax
│   ├── phi_simplify.ax
│   ├── unreachable.ax
│   └── threading.ax
│
├── strength/
│   ├── mod.ax
│   ├── integer.ax
│   ├── division.ax
│   └── target_cost.ax
│
└── tests/
```

---

# 43. Implementation Order

```text
1. Scalar lattice
2. Constant representation
3. Constant evaluator
4. Constant folding
5. Reachability analysis
6. Predicate facts
7. Range facts
8. Known-bits analysis
9. SCCP
10. Copy propagation
11. InstCombine matcher
12. Integer simplification
13. Boolean simplification
14. Floating-point simplification
15. Cast simplification
16. Phi simplification
17. GVN
18. Memory-aware GVN
19. DCE
20. Dead-store interface
21. CFG simplification
22. Strength reduction
23. Scalar fixed-point pipeline
24. Cost model integration
25. Proof Gateway integration
26. Analysis invalidation
27. Parallel function execution
28. Optimization trace
29. Adversarial tests
```

---

# 44. Adversarial Tests

### Test 1 — Signed overflow

Compiler không được sử dụng giả định:

```text
x + 1 > x
```

trừ khi Axiom semantic contract chứng minh điều đó.

---

### Test 2 — Floating point

```text
(a + b) + c
```

không được tự động biến thành:

```text
a + (b + c)
```

trong strict FP.

---

### Test 3 — Panic

```text
let x = 1 / 0
```

Nếu semantics là panic:

```text
AlwaysPanic
```

không được biến thành:

```text
return arbitrary_value
```

---

### Test 4 — Effectful unused result

```text
foo(); // may panic
```

không được DCE chỉ vì return value không được sử dụng.

---

### Test 5 — Volatile

```text
volatile_load(p)
```

không được GVN.

---

### Test 6 — Atomic

Hai atomic operation không được reorder bằng scalar optimizer nếu phá memory-order semantics.

---

### Test 7 — Unknown foreign call

```text
foreign foo()
```

không contract.

Expected:

```text
GVN conservative
DCE conservative
```

---

### Test 8 — Capability

```text
v = view(x)
use(v)
```

Optimizer có thể eliminate temporary `v`, nhưng semantic READ capability phải vẫn đúng.

---

### Test 9 — Move

```text
b = move(a)
```

Copy propagation không được biến thành:

```text
b = copy(a)
```

---

### Test 10 — Drop

```text
let r = Resource()
unused(r)
```

không được DCE destructor nếu Drop observable.

---

### Test 11 — Branch ownership

Nếu SCCP loại bỏ một branch chứa:

```text
Move(x)
```

ownership facts phải được invalidate/recompute chính xác.

---

### Test 12 — Range

Chỉ khi có proof:

```text
0 <= x <= 9
```

mới được simplify:

```text
x < 10 → true
```

---

### Test 13 — Target cost

Nếu transform:

```text
mul → shift/add
```

làm code lớn hơn và chậm hơn trên target:

```text
skip transform
```

nhưng không coi transform là illegal.

---

### Test 14 — Determinism

Scalar optimization với:

```text
1 worker
8 workers
32 workers
```

phải cho cùng semantic result.

---

# 45. Frozen Invariants

### `ASCALAR-20..75`

```text
ASCALAR-20 — Scalar Optimization Operates Only On Verified OptIR
ASCALAR-21 — MIR Remains The Semantic Source Of Truth
ASCALAR-22 — Scalar Facts Are Revision-Bound
ASCALAR-23 — Unknown Is Never Treated As Constant
ASCALAR-24 — Unknown Is Never Treated As NoEffect
ASCALAR-25 — Constant Folding Uses Axiom Semantic Arithmetic
ASCALAR-26 — Compile-Time Arithmetic Matches Runtime Semantics
ASCALAR-27 — Integer Overflow Semantics Are Preserved
ASCALAR-28 — Division Semantics Are Preserved
ASCALAR-29 — Shift Semantics Are Preserved
ASCALAR-30 — Floating-Point Strict Semantics Are Preserved
ASCALAR-31 — Fast-Floating Semantics Require Explicit Contract
ASCALAR-32 — Evaluation Order Is Preserved
ASCALAR-33 — Short-Circuit Semantics Are Preserved
ASCALAR-34 — Panic Is Observable
ASCALAR-35 — Trap Semantics Are Preserved
ASCALAR-36 — Volatile Operations Are Never Treated As Ordinary Loads
ASCALAR-37 — Atomic Operations Preserve Atomic Semantics
ASCALAR-38 — Synchronization Effects Are Preserved
ASCALAR-39 — Foreign Calls Are Conservative Without Contracts
ASCALAR-40 — Drop Semantics Are Preserved
ASCALAR-41 — Move Semantics Cannot Be Replaced By Copy
ASCALAR-42 — Copy Semantics Cannot Be Replaced By Move
ASCALAR-43 — Capability Semantics Survive Scalar Elimination
ASCALAR-44 — Scalar Optimization Cannot Introduce Safe Aliasing
ASCALAR-45 — Scalar Optimization Cannot Introduce Ownership
ASCALAR-46 — Scalar Optimization Cannot Introduce Allocation Without Contract
ASCALAR-47 — Constant Propagation Preserves Ownership State
ASCALAR-48 — SCCP Preserves Reachability Semantics
ASCALAR-49 — Unreachable Blocks Are Removed Only After Proof
ASCALAR-50 — Branch Facts Are Path-Sensitive
ASCALAR-51 — Range Facts Require Valid Proof
ASCALAR-52 — Known-Bit Facts Require Valid Proof
ASCALAR-53 — GVN Requires Semantic Equivalence
ASCALAR-54 — GVN Respects Memory Invalidation
ASCALAR-55 — GVN Respects Effect Invalidation
ASCALAR-56 — DCE Requires Absence Of Observable Effects
ASCALAR-57 — Dead Store Elimination Requires Valid Memory Proof
ASCALAR-58 — Algebraic Rewrites Require Semantic Legality
ASCALAR-59 — Mathematical Equivalence Does Not Imply Machine Equivalence
ASCALAR-60 — Strength Reduction Requires Semantic Equivalence
ASCALAR-61 — Target Cost Cannot Override Legality
ASCALAR-62 — Cost Model Cannot Create Proofs
ASCALAR-63 — Scalar Passes Use OptimizationGateway
ASCALAR-64 — Scalar Passes Declare Analysis Invalidation
ASCALAR-65 — Stale Proofs Cannot Authorize Scalar Transforms
ASCALAR-66 — Failed Scalar Transforms Preserve The Last Valid IR
ASCALAR-67 — Scalar Passes Are Deterministic
ASCALAR-68 — Scalar Fixed-Point Pipelines Have Bounded Termination
ASCALAR-69 — Optimization Level Cannot Change Scalar Semantics
ASCALAR-70 — O0 Does Not Disable Semantic Verification
ASCALAR-71 — Scalar Optimization May Remove Physical Computation Without Removing Required Semantics
ASCALAR-72 — Scalar Optimization Must Preserve Source-Level Observable Behavior
ASCALAR-73 — Scalar Optimization Cannot Depend On C/C++ Undefined-Behavior Assumptions
ASCALAR-74 — Scalar Analysis Results Are Explainable
ASCALAR-75 — Scalar Optimization Is A Semantics-Preserving Transformation
```

---

# 46. Kết quả kiến trúc

Sau `288`, Axiom có tầng optimization đầu tiên:

```text
                    Verified MIR
                         │
                         ▼
                        OptIR
                         │
                         ▼
                Scalar Analysis
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
     Constant          Range            Alias
     Analysis          Analysis         Analysis
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                 Proof Gateway
                         │
                         ▼
              Scalar Transformations
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
       SCCP           GVN/DCE        InstCombine
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                  Simplified OptIR
                         │
                         ▼
                Next Optimization
```

Điểm đặc biệt của Axiom là scalar optimizer **không được phép sử dụng các “mẹo compiler” nguy hiểm dựa trên UB**. Nó phải dựa trên semantic contract thực sự của ngôn ngữ.

Điều này rất quan trọng đối với mục tiêu của Axiom: **hiệu năng cao như C/C++ nhưng semantics phải đủ rõ để compiler có thể tối ưu mạnh mà không biến chương trình thành một tập hợp các giả định khó đoán.**

**BOOTSTRAP-288 hoàn tất và được đóng băng.**