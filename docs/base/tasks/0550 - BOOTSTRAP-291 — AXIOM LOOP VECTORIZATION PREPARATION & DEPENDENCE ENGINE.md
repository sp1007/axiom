# BOOTSTRAP-291 — AXIOM LOOP VECTORIZATION PREPARATION & DEPENDENCE ENGINE
## FROZEN / COMPLETED

### 1. Mục tiêu

Sau `290`, compiler đã có khả năng hiểu và biến đổi loop. Bước tiếp theo là xây dựng **cơ sở semantic để vectorize loop**.

Mục tiêu của `291` không phải viết SIMD instruction encoder — backend sẽ đảm nhiệm phần đó. Mục tiêu là trả lời chính xác:

> **Loop này có thể thực hiện nhiều iteration cùng lúc mà không làm thay đổi semantics của Axiom hay không?**

Pipeline:

```text
Loop
 ↓
Induction / Range
 ↓
Memory Access Analysis
 ↓
Alias / Capability Proof
 ↓
Dependence Analysis
 ↓
Reduction Analysis
 ↓
Vectorization Legality
 ↓
Vectorization Plan
 ↓
Target Vector Backend
```

---

# 2. Nguyên tắc quan trọng nhất

Axiom không nên yêu cầu programmer viết:

```text
#pragma vectorize
restrict
__attribute__((...))
```

cho trường hợp compiler có thể tự chứng minh.

Ví dụ:

```text
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
) {
    for i in 0..out.len() {
        out[i] = a[i] + b[i]
    }
}
```

Nếu capability/alias analysis chứng minh được:

```text
a ∩ out = ∅
b ∩ out = ∅
```

thì compiler có thể tự kết luận:

```text
iterations independent
```

và tạo vectorization plan.

---

# 3. Vectorization không phải là semantic layer mới

Không tạo kiểu:

```text
Vector<T>
```

chỉ để compiler vectorize scalar code.

Phải phân biệt:

```text
Axiom semantic type
```

với:

```text
Machine vector type
```

Ví dụ:

```text
f32
```

vẫn là:

```text
f32
```

cho programmer.

Backend có thể biến:

```text
4 × f32
```

thành:

```text
<4 x f32>
```

hoặc:

```text
128-bit SIMD register
```

tùy target.

---

# 4. Vectorization IR

Tạo một abstraction trung gian:

```text
VectorizationPlan {
    loop_id
    vector_width
    vector_type
    induction_strategy
    memory_strategy
    remainder_strategy
    reduction_strategy
    runtime_guards
    legality_proofs
    cost
}
```

Ví dụ:

```text
VectorWidth = 8
ElementType = f32
```

không có nghĩa target chắc chắn dùng vector 8.

Đó là **plan**, backend vẫn có quyền legalize theo ISA.

---

# 5. Vectorization Candidate

Loop candidate cần thỏa:

```text
Candidate {
    loop
    canonical
    finite_or_guarded
    analyzable_memory
    analyzable_control_flow
    analyzable_effects
}
```

Không phải loop nào cũng cần vectorize.

---

# 6. Vectorization Legality

Tách riêng:

```text
Legality
```

và:

```text
Profitability
```

Legality:

```text
Có được phép không?
```

Profitability:

```text
Có đáng làm không?
```

Không bao giờ:

```text
high_speedup_estimate
→ assume legal
```

---

# 7. Iteration Independence

Điều kiện cơ bản:

```text
Iteration(i)
```

không được có dependency không thể vectorize với:

```text
Iteration(j)
```

trong cùng vector group.

Compiler sử dụng:

```text
DependenceGraph
+
AliasInfo
+
CapabilityInfo
+
MemorySSA
```

để chứng minh.

---

# 8. Read/Read

```text
a[i]
b[i]
```

nếu chỉ đọc:

```text
READ + READ
```

thì không tạo write dependency.

Có thể vectorize.

---

# 9. Read/Write

```text
a[i] = b[i]
```

vẫn có thể vectorize nếu:

```text
a
```

và:

```text
b
```

được chứng minh disjoint, hoặc transformation vẫn bảo toàn dependency.

---

# 10. Potential Alias

Ví dụ:

```text
out[i] = out[i + 1] + 1
```

Không thể coi là independent một cách đơn giản.

Compiler phải phát hiện:

```text
write(i)
read(i+1)
```

có loop-carried dependency.

---

# 11. Dependence Distance

Dùng kết quả `290`:

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
a[i] = a[i-1] + 1
```

có:

```text
distance = 1
```

→ vectorization trực tiếp không hợp lệ.

---

# 12. Zero-Distance Dependence

Nếu:

```text
read(a[i])
write(a[i])
```

trong cùng iteration, đó không nhất thiết là loop-carried dependency.

Compiler phải phân biệt:

```text
same_iteration
```

với:

```text
cross_iteration
```

Đây là lý do dependence analysis không thể chỉ dựa trên alias.

---

# 13. Capability Proof

Ví dụ:

```text
a: view<f32>
b: view<f32>
out: mut_view<f32>
```

Compiler đã có:

```text
Capability
```

và:

```text
Region
```

Nếu:

```text
Region(a) ∩ Region(out) = ∅
Region(b) ∩ Region(out) = ∅
```

thì có thể tạo proof:

```text
IterationIndependentMemory
```

Đây là cách Axiom đạt hiệu quả tương tự việc programmer cung cấp alias contract, nhưng không cần `restrict`.

---

# 14. Runtime Alias Versioning

Nếu static proof không đủ nhưng compiler vẫn có thể kiểm tra:

```text
if ranges_do_not_overlap(a, b) {
    vector_loop
} else {
    scalar_loop
}
```

thì tạo:

```text
RuntimeAliasGuard
```

và hai version:

```text
FastVectorLoop
FallbackLoop
```

---

# 15. Runtime Guard phải an toàn

Guard không được tự thay đổi semantics.

Nó chỉ được chọn giữa:

```text
semantically equivalent implementations
```

Nếu guard không chứng minh được điều kiện:

```text
fallback
```

vẫn phải đúng.

---

# 16. Bounds Checks

Loop:

```text
for i in 0..n {
    out[i] = a[i] + b[i]
}
```

Nếu:

```text
len(out) >= n
len(a) >= n
len(b) >= n
```

và loop range chứng minh:

```text
0 <= i < n
```

thì vectorized loop không cần một bounds check cho từng scalar element.

Compiler có thể tạo:

```text
pre-loop validation
```

rồi vector body chạy với invariant bounds.

---

# 17. Vector Loop + Remainder

Nếu:

```text
n = 18
vector_width = 8
```

thì:

```text
vector iterations = 2
remainder = 2
```

Conceptually:

```text
for i in 0..16 step 8 {
    vector_body(i)
}

for i in 16..18 {
    scalar_body(i)
}
```

Remainder có thể được:

- scalar loop
- masked vector loop
- target-specific tail instruction

do backend quyết định.

---

# 18. Masked Vectorization

Loop:

```text
for i in 0..n {
    if condition(i) {
        a[i] = f(i)
    }
}
```

có thể vectorize bằng mask:

```text
mask = condition(vector_indices)

masked_store(a, mask, result)
```

nhưng chỉ khi semantics của:

```text
condition
f
store
```

cho phép.

---

# 19. Control Flow trong Vector Loop

Không phải branch nào cũng cản vectorization.

Compiler phân loại:

```text
Uniform
Varying
```

Ví dụ:

```text
if mode {
    ...
}
```

nếu `mode` invariant:

```text
Uniform
```

→ có thể hoist/unswitch.

Trong khi:

```text
if a[i] > 0
```

là:

```text
Varying
```

→ có thể cần mask.

---

# 20. Uniform Analysis

Tạo:

```text
Uniformity {
    Uniform
    Varying
    Unknown
}
```

Áp dụng cho:

- scalar values
- branches
- pointers/views
- indices
- calls
- masks

`Unknown` không được coi là `Uniform`.

---

# 21. Vectorizable Operations

Ban đầu ưu tiên:

```text
integer arithmetic
floating arithmetic
bitwise
comparisons
select
load
store
cast
```

Các operation phức tạp hơn cần target/library lowering.

---

# 22. Scalarization

Nếu một operation không có vector instruction:

```text
vector_operation
```

có thể được:

```text
scalarized
```

nhưng cost model quyết định có đáng hay không.

Không được coi:

```text
vectorizable = always faster
```

---

# 23. Function Calls

Loop:

```text
for i in 0..n {
    out[i] = f(a[i])
}
```

Có ba trường hợp:

### Case A

`f` có vector implementation.

→ vectorize.

### Case B

`f` có thể inline.

→ inline → vectorize.

### Case C

`f` không vectorizable.

→ có thể scalarize/cannot vectorize tùy cost.

---

# 24. Vector Function Specialization

Compiler có thể tạo:

```text
f_scalar(T)
f_vector(Vector<T>)
```

nhưng đây không phải API bắt programmer viết.

Đây là codegen specialization nội bộ.

---

# 25. Reduction

Ví dụ:

```text
sum = sum + a[i]
```

có thể biến thành:

```text
v0 = ...
v1 = ...
v2 = ...
v3 = ...

sum = reduce(v0 + v1 + v2 + v3)
```

Nhưng legality phụ thuộc arithmetic semantics.

---

# 26. Integer Reduction

Nếu integer operation là:

```text
wrapping
```

thì vector reduction phải có semantics tương đương wrapping.

Nếu:

```text
checked
```

thì compiler phải giữ overflow behavior.

Không được biến:

```text
checked addition
```

thành:

```text
wrapping SIMD addition
```

một cách âm thầm.

---

# 27. Floating Reduction

Strict floating point:

```text
sum += a[i]
```

không được tự động reassociate.

Ví dụ:

```text
((a+b)+c)+d
```

không mặc định tương đương:

```text
(a+b)+(c+d)
```

Do đó reduction vectorization cần:

```text
FPContract
```

và:

```text
reassociation permission
```

nếu muốn thay đổi thứ tự.

---

# 28. NaN / Infinity

Floating-point vectorization phải giữ semantics về:

```text
NaN
Infinity
signed zero
rounding
exceptions/traps nếu profile hỗ trợ
```

Target-specific fast math chỉ được dùng khi contract cho phép.

---

# 29. Memory Alignment

Compiler phân biệt:

```text
KnownAligned
KnownUnaligned
UnknownAlignment
```

Không được giả định:

```text
vector alignment
```

chỉ vì type có kích thước phù hợp.

Nếu không biết alignment:

```text
unaligned vector access
```

hoặc runtime alignment versioning có thể được dùng.

---

# 30. Alignment Versioning

Có thể tạo:

```text
if aligned(ptr) {
    aligned_vector_loop
} else {
    unaligned_vector_loop
}
```

chỉ khi target cho thấy aligned access thực sự có lợi.

---

# 31. Gather / Scatter

Ví dụ:

```text
out[i] = a[index[i]]
```

không phải contiguous load.

Có thể:

```text
gather
```

nhưng cost thường cao.

Compiler phải đưa vào cost model:

```text
GatherCost
ScatterCost
CachePenalty
```

không coi gather như load thông thường.

---

# 32. Strided Access

Ví dụ:

```text
a[i * 4]
```

có stride:

```text
4
```

Compiler lưu:

```text
MemoryAccessPattern {
    base
    stride
    element_size
    alignment
    contiguous
}
```

Điều này hỗ trợ:

- vectorization
- interleave
- target-specific loads
- cache analysis.

---

# 33. Interleaved Access

Ví dụ:

```text
a[2*i]
a[2*i+1]
```

có thể được nhận diện là:

```text
interleaved access
```

và backend có thể sử dụng:

```text
interleaved load/store
```

nếu ISA hỗ trợ.

---

# 34. Memory Layout không được tự thay đổi

Vectorizer không được thay đổi:

```text
struct layout
array layout
ABI layout
```

chỉ để vectorization dễ hơn.

Data-layout transformation là một optimization riêng và phải có semantic/ABI contract phù hợp.

---

# 35. Gather vs Data Reorganization

Compiler có thể cân nhắc:

```text
gather
```

hoặc:

```text
loop transformation
```

hoặc:

```text
temporary contiguous buffer
```

nhưng temporary allocation chỉ được tạo khi cost model và escape/lifetime semantics cho phép.

---

# 36. Vectorization và Ownership

Vectorization không được làm:

```text
Copy
```

thành:

```text
Move
```

hoặc ngược lại.

Ví dụ một loop:

```text
consume(resource[i])
```

nếu mỗi iteration thực hiện ownership transfer, vectorizer phải bảo toàn:

```text
exactly-once ownership transfer
```

Không được duplicate hoặc reorder ownership operations tùy tiện.

---

# 37. Vectorization và Drop

Loop:

```text
for i in ... {
    use(Resource(...))
}
```

có:

```text
Drop
```

thì vectorization phải bảo đảm:

```text
same number of constructions
same number of drops
same required ordering
```

Nếu không thể chứng minh:

```text
do not vectorize
```

---

# 38. Vectorization và Panic

Ví dụ:

```text
for i in ... {
    check(a[i])
}
```

Nếu `check` có thể panic, vectorization có thể thay đổi thứ tự phát hiện lỗi.

Do đó cần:

```text
PanicOrderContract
```

Nếu panic order observable:

```text
no unsafe reassociation/reordering
```

---

# 39. Vectorization và IO

```text
for i in ... {
    print(a[i])
}
```

Không được biến thành parallel/vector execution chỉ vì compiler nhận thấy loop.

IO là observable effect và iteration ordering phải được giữ.

---

# 40. Vectorization và Atomics

Atomic operations có:

```text
atomicity
ordering
scope
```

nên không thể coi là ordinary SIMD memory operation.

Một số target có vector atomic primitives, nhưng đây là target-specific legality.

---

# 41. Vectorization và Volatile

```text
volatile_load
volatile_store
```

không được vectorize thành một vector access nếu điều đó thay đổi số lượng hoặc ordering observable volatile operations.

---

# 42. Vectorization và GPU

Cùng framework có thể phục vụ GPU:

```text
CPU SIMD
GPU SIMD/SIMT
```

nhưng không được đồng nhất semantics.

GPU có:

```text
execution domain
storage domain
memory scope
barrier
```

riêng.

Vectorization analysis chỉ cung cấp các facts có thể dùng chung.

---

# 43. Vectorization Plan Example

Input:

```text
for i in 0..n {
    out[i] = a[i] + b[i]
}
```

Compiler có:

```text
NoAlias(a,out)
NoAlias(b,out)

0 <= i < n

a: contiguous
b: contiguous
out: contiguous

f32: vectorizable
addition: vectorizable

no side effects
no panic
no dependency
```

Plan:

```text
VectorizationPlan {
    width: target_preferred_width
    element: f32

    load_a: contiguous
    load_b: contiguous
    store_out: contiguous

    remainder: masked_or_scalar

    legality:
        NoAlias
        BoundsSafe
        NoLoopCarriedDependency
        NoObservableOrderingConflict
}
```

---

# 44. Cost Model

```text
VectorCost {
    scalar_cost
    vector_cost
    setup_cost
    remainder_cost
    mask_cost
    gather_cost
    alignment_cost
    register_pressure
    code_size_growth
    expected_trip_count
}
```

Vectorization chỉ được thực hiện khi:

```text
Legal == true
```

sau đó mới:

```text
Profitable == true
```

---

# 45. Target Abstraction

Không hard-code:

```text
SSE
AVX2
AVX-512
NEON
SVE
RVV
```

vào semantic vectorizer.

Target cung cấp:

```text
VectorTargetInfo {
    preferred_widths
    legal_widths
    supported_types
    masked_operations
    gather
    scatter
    reductions
    alignment_preferences
    instruction_costs
    register_count
}
```

Backend `x86-64`, `ARM64`, `RISC-V64` và các backend sau cung cấp implementation.

---

# 46. Scalable Vector

Đặc biệt với:

```text
ARM SVE
RISC-V RVV
```

vector width có thể không phải compile-time fixed theo kiểu AVX2.

Do đó abstraction không nên chỉ là:

```text
VectorWidth = 8
```

mà cần:

```text
FixedWidth(N)
ScalableWidth(MinElements)
```

Điều này giúp Axiom không khóa kiến trúc vào x86.

---

# 47. Vector-Length Agnostic Loop

Framework phải hỗ trợ:

```text
while remaining > 0 {
    vl = set_vector_length(remaining)
    process(vl)
}
```

cho target scalable-vector.

Semantic source vẫn là scalar loop.

---

# 48. Vectorization Gateway

Tất cả transformation phải yêu cầu proof:

```text
VectorizationProof {
    loop_independent
    memory_safe
    alias_safe
    arithmetic_safe
    effect_safe
    panic_safe
    ownership_safe
    capability_safe
}
```

Thiếu proof:

```text
UNKNOWN
```

→ fallback scalar.

---

# 49. Không cần `@vectorize` trong Core

Axiom có thể về sau hỗ trợ hint:

```text
@vectorize
```

nhưng đó chỉ nên là:

```text
optimization request
```

không phải:

```text
semantic guarantee
```

Compiler vẫn có quyền từ chối nếu không legal.

Ngược lại, compiler **không cần annotation** để tự vectorize code an toàn và có lợi.

---

# 50. Module Structure

```text
compiler/optimization/vector/
├── mod.ax
│
├── candidate/
│   ├── candidate.ax
│   ├── legality.ax
│   └── profitability.ax
│
├── analysis/
│   ├── dependence.ax
│   ├── uniformity.ax
│   ├── recurrence.ax
│   ├── memory_access.ax
│   ├── alignment.ax
│   ├── stride.ax
│   ├── reduction.ax
│   └── trip_count.ax
│
├── legality/
│   ├── alias.ax
│   ├── capability.ax
│   ├── ownership.ax
│   ├── effects.ax
│   ├── panic.ax
│   ├── atomic.ax
│   ├── volatile.ax
│   ├── floating_point.ax
│   └── control_flow.ax
│
├── plan/
│   ├── vector_plan.ax
│   ├── memory_plan.ax
│   ├── mask_plan.ax
│   ├── remainder.ax
│   ├── reduction.ax
│   └── runtime_guard.ax
│
├── target/
│   ├── target_vector.ax
│   ├── fixed_width.ax
│   ├── scalable_width.ax
│   ├── cost.ax
│   └── features.ax
│
├── transform/
│   ├── widen.ax
│   ├── mask.ax
│   ├── remainder.ax
│   ├── reduction.ax
│   └── versioning.ax
│
└── tests/
```

---

# 51. Implementation Order

```text
1. Vectorization candidate model
2. Uniformity analysis
3. Vector memory-access pattern model
4. Dependence integration
5. Capability/alias integration
6. Bounds/range integration
7. Arithmetic legality
8. Floating-point legality
9. Atomic/volatile legality
10. Panic/effect legality
11. Reduction recognition
12. Alignment analysis
13. Fixed-width target abstraction
14. Scalable-width target abstraction
15. Vector cost model
16. Basic vectorization plan
17. Remainder strategy
18. Mask strategy
19. Runtime alias versioning
20. Runtime alignment versioning
21. Vector reduction planning
22. Vector loop transformation
23. Proof Gateway integration
24. Pass Manager integration
25. Backend handoff
26. optimization diagnostics
27. adversarial tests
```

---

# 52. Adversarial Tests

### Test 1 — Independent arrays

```text
for i in 0..n {
    out[i] = a[i] + b[i]
}
```

Proven disjoint → vectorization candidate.

### Test 2 — Unknown alias

```text
a[i] = a[i] + b[i]
```

Không được assume `a`/`b` disjoint.

### Test 3 — Loop-carried dependency

```text
a[i] = a[i-1] + 1
```

Direct vectorization phải bị từ chối.

### Test 4 — Checked arithmetic

Vector transformation phải giữ overflow behavior.

### Test 5 — Wrapping arithmetic

Vector arithmetic phải tương đương wrapping scalar arithmetic.

### Test 6 — Strict floating point

Reduction không được reassociate.

### Test 7 — Volatile

Không vectorize volatile operations thành access có số lần khác.

### Test 8 — Atomic

Ordering phải được giữ.

### Test 9 — Panic

Không thay đổi observable panic ordering nếu profile yêu cầu giữ thứ tự.

### Test 10 — Drop

Số lần Drop phải chính xác.

### Test 11 — Bounds

Vector loop không được loại bounds check nếu proof không đủ.

### Test 12 — Runtime alias versioning

Fast loop chỉ được chọn khi runtime guard chứng minh điều kiện.

### Test 13 — Gather

Gather loop không được coi là contiguous loop.

### Test 14 — Scalable vector

SVE/RVV plan không được giả định fixed hardware vector width.

### Test 15 — Ownership

Vectorization không được duplicate/mất ownership transfer.

---

# 53. Frozen Invariants

### `AVEC-20..90`

```text
AVEC-20 — Vectorization Operates Only On Verified OptIR
AVEC-21 — Vectorization Is An Optimization, Not A Semantic Type System
AVEC-22 — Scalar Axiom Semantics Remain The Source Of Truth
AVEC-23 — Vectorization Legality Is Separate From Profitability
AVEC-24 — Unknown Legality Is Not Treated As Legal
AVEC-25 — Loop-Carried Dependencies Must Be Preserved
AVEC-26 — Same-Iteration Dependencies Are Distinguished From Cross-Iteration Dependencies
AVEC-27 — Dependence Analysis Integrates With MemorySSA
AVEC-28 — Dependence Analysis Integrates With Alias Analysis
AVEC-29 — Capability Proofs May Establish Iteration Independence
AVEC-30 — Unknown Alias Never Implies Vector Independence
AVEC-31 — Runtime Alias Guards Must Be Semantically Valid
AVEC-32 — Runtime Versioning Must Preserve A Correct Fallback
AVEC-33 — Bounds Proofs May Eliminate Per-Element Bounds Checks
AVEC-34 — Unknown Bounds Never Permit Unsafe Vector Access
AVEC-35 — Vectorization Preserves Ownership Semantics
AVEC-36 — Vectorization Preserves Move Semantics
AVEC-37 — Vectorization Preserves Copy Semantics
AVEC-38 — Vectorization Preserves Drop Semantics
AVEC-39 — Vectorization Preserves Capability Semantics
AVEC-40 — Vectorization Preserves Exactly-Once Cleanup
AVEC-41 — Vectorization Preserves Observable Effects
AVEC-42 — Vectorization Preserves Panic Semantics
AVEC-43 — Vectorization Preserves Required Evaluation Ordering
AVEC-44 — Volatile Operations Are Not Freely Vectorizable
AVEC-45 — Atomicity Must Be Preserved
AVEC-46 — Atomic Ordering Must Be Preserved
AVEC-47 — Synchronization Semantics Must Be Preserved
AVEC-48 — Foreign Effects Are Conservative Without Contracts
AVEC-49 — Integer Arithmetic Semantics Must Be Preserved
AVEC-50 — Wrapping Arithmetic Must Remain Wrapping
AVEC-51 — Checked Arithmetic Must Remain Checked
AVEC-52 — Saturating Arithmetic Must Remain Saturating
AVEC-53 — Strict Floating-Point Ordering Must Be Preserved
AVEC-54 — Floating-Point Reassociation Requires Explicit Semantic Permission
AVEC-55 — NaN Semantics Must Be Preserved
AVEC-56 — Signed-Zero Semantics Must Be Preserved Where Observable
AVEC-57 — Remainder Processing Must Cover Exactly The Original Iterations
AVEC-58 — Masked Vectorization Must Preserve Per-Element Semantics
AVEC-59 — Uniform And Varying Control Flow Must Be Distinguished
AVEC-60 — Unknown Uniformity Is Not Treated As Uniform
AVEC-61 — Gather Access Is Distinct From Contiguous Access
AVEC-62 — Scatter Access Is Distinct From Contiguous Store
AVEC-63 — Stride Must Be Explicitly Modeled
AVEC-64 — Alignment Must Be Proven Or Conservatively Handled
AVEC-65 — Alignment Versioning Requires Valid Runtime Guards
AVEC-66 — Fixed-Width And Scalable-Width Vectors Are Distinct Target Models
AVEC-67 — Semantic Vectorization Must Not Depend On A Specific ISA
AVEC-68 — Target Cost Must Not Override Semantic Legality
AVEC-69 — Vectorization Cannot Invent NoAlias
AVEC-70 — Vectorization Cannot Invent Ownership
AVEC-71 — Vectorization Cannot Invent Safe Capabilities
AVEC-72 — Vectorization Cannot Remove Required Synchronization
AVEC-73 — Vectorization Cannot Change Logical Identity
AVEC-74 — Vectorization Cannot Change Stable-Address Contracts
AVEC-75 — Temporary Storage Requires Valid Lifetime And Escape Proof
AVEC-76 — Vector Function Specialization Is An Internal Optimization
AVEC-77 — Scalar Fallback Must Remain Semantically Valid
AVEC-78 — Every Vector Transformation Uses OptimizationGateway
AVEC-79 — Vector Proofs Become Invalid After Relevant IR Changes
AVEC-80 — Vector Passes Declare Analysis Invalidation
AVEC-81 — Failed Vectorization Must Preserve The Prior Valid IR
AVEC-82 — Vectorization Decisions Must Be Deterministic
AVEC-83 — Vectorization Decisions Must Be Explainable
AVEC-84 — Vectorization Must Respect Code-Size Budget
AVEC-85 — Vectorization Must Respect Register-Pressure Constraints
AVEC-86 — Vectorization May Be Rejected Solely For Profitability
AVEC-87 — Rejection Of Vectorization Must Never Affect Correctness
AVEC-88 — CPU SIMD And GPU SIMT Are Distinct Execution Models
AVEC-89 — Vectorization Must Preserve Axiom Observable Semantics
AVEC-90 — Vectorization Is Semantics-Preserving
```

---

## 54. Kết quả

Sau `291`, Axiom có chuỗi:

```text
Scalar
   ↓
Memory
   ↓
Loop
   ↓
Dependence
   ↓
Capability / NoAlias
   ↓
Vectorization Plan
   ↓
CPU SIMD Backend
```

Điểm quan trọng là programmer chỉ cần viết code bình thường:

```text
for i in 0..n {
    out[i] = a[i] + b[i]
}
```

Trong khi compiler tự đi qua:

```text
Range proof
    ↓
Bounds proof
    ↓
Capability proof
    ↓
Alias proof
    ↓
Memory dependence
    ↓
Iteration independence
    ↓
Vector legality
    ↓
Target cost
    ↓
SIMD
```

Đây là một trong những phần thể hiện rõ nhất triết lý của Axiom:

> **Không bắt programmer viết “mật mã tối ưu hóa”; hãy để compiler chứng minh điều đó từ semantics của chương trình.**

**BOOTSTRAP-291 hoàn tất và được đóng băng.**