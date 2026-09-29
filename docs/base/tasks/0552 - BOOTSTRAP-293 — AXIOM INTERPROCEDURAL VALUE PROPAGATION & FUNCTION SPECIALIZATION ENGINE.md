# BOOTSTRAP-293 — AXIOM INTERPROCEDURAL VALUE PROPAGATION & FUNCTION SPECIALIZATION ENGINE
## FROZEN / COMPLETED

### 1. Mục tiêu

`292` đã tạo khả năng:

```text
Call
 ↓
Inline / Specialize
 ↓
Caller context
```

Nhưng nếu chỉ inline từng callsite, compiler vẫn bỏ lỡ một lớp tối ưu quan trọng:

> **Compiler phải có khả năng truyền các fact đã biết xuyên qua function boundary mà không nhất thiết phải inline toàn bộ function.**

Ví dụ:

```text
fn process(x: i32, mode: bool) -> i32 {
    if mode {
        x * 2
    } else {
        x + 1
    }
}

fn main() {
    process(value, true)
}
```

Không nhất thiết phải copy toàn bộ `process` vào caller.

Compiler có thể tạo:

```text
process_true(x)
```

với invariant:

```text
mode == true
```

sau đó:

```text
if mode
```

được loại bỏ.

Đây là **interprocedural specialization**, nằm giữa:

```text
interprocedural analysis
```

và:

```text
inlining
```

---

# 2. Semantic boundary

`293` **không thay đổi semantics của function**.

Nó tạo một phiên bản chuyên biệt:

```text
Original:
    F(T1, T2, T3)

Specialized:
    F_spec(T1, constant, T3)
```

và chứng minh:

```text
F_spec(T1, T3) ≡ F(T1, constant, T3)
```

trong phạm vi contract đã chứng minh.

---

# 3. Pipeline

```text
Semantic Summary
      ↓
Call Graph
      ↓
Value / Type Facts
      ↓
Specialization Candidate
      ↓
Legality Proof
      ↓
Specialization Plan
      ↓
Clone Function
      ↓
Substitute Known Facts
      ↓
Simplify
      ↓
Re-analyze
      ↓
Cost Model
      ↓
Publish Specialized Version
      ↓
Call-site Rewrite
```

Sau đó `288`, `289`, `290`, `291`, `292` tiếp tục tối ưu.

---

# 4. Function Specialization Key

```text
SpecializationKey {
    function
    type_arguments
    constant_arguments
    known_ranges
    known_enum_variants
    known_trait_targets
    known_capabilities
    target_features
}
```

Không phải mọi fact đều được đưa vào key.

Chỉ những fact có giá trị đủ lớn và có semantic stability mới được dùng.

---

# 5. Constant Specialization

Ví dụ:

```text
fn calculate(x: i32, mode: i32) -> i32 {
    if mode == 0 {
        x + 1
    } else if mode == 1 {
        x * 2
    } else {
        x * 4
    }
}
```

Call:

```text
calculate(x, 1)
```

Specialized:

```text
calculate_mode_1(x)
```

Sau specialization:

```text
x * 2
```

---

# 6. Range Specialization

Compiler có thể biết:

```text
0 <= x < 16
```

thông qua `RangeInfo`.

Function:

```text
fn lookup(x: usize) {
    table[x]
}
```

Nếu specialization chứng minh:

```text
x < 16
```

thì bounds check có thể được loại bỏ.

Quan trọng:

> Range specialization không được tự tạo fact. Nó chỉ sử dụng range proof đã tồn tại.

---

# 7. Enum Variant Specialization

Ví dụ:

```text
enum State {
    Idle,
    Running,
    Finished
}
```

Function:

```text
fn process(s: State) {
    match s {
        Idle => A,
        Running => B,
        Finished => C,
    }
}
```

Nếu caller đã biết:

```text
s == Running
```

specialized function chỉ còn:

```text
B
```

---

# 8. Option / Result Specialization

Ví dụ:

```text
fn process(x: Option<T>) {
    match x {
        Some(v) => use(v),
        None => fallback(),
    }
}
```

Nếu caller chứng minh:

```text
x = Some(v)
```

thì specialization có thể loại:

```text
None branch
```

nhưng vẫn phải bảo toàn ownership của `v`.

---

# 9. Type Specialization

Generic:

```text
fn process<T>(x: T)
```

với:

```text
T = f32
```

có thể tạo:

```text
process_f32
```

Compiler biết chính xác:

```text
size
alignment
layout
Copy
Drop
traits
operators
ABI
```

---

# 10. Trait Target Specialization

Ví dụ:

```text
fn execute<T: Compute>(x: T) {
    x.compute()
}
```

Nếu specialization biết:

```text
T = Matrix
```

và implementation:

```text
Matrix.compute
```

là duy nhất, call có thể trở thành direct target.

Sau đó:

```text
devirtualization
→ inlining
→ scalar optimization
```

---

# 11. Capability Specialization

Đây là điểm quan trọng đối với thiết kế Axiom.

Ví dụ:

```text
fn sum(data: view<f32>) -> f32
```

Compiler có thể biết:

```text
region = R
access = READ
```

và function không ghi vào `R`.

Fact này có thể truyền vào optimizer.

Nhưng compiler **không được biến `view` thành mutable capability** chỉ để tối ưu.

---

# 12. Alias Specialization

Nếu caller chứng minh:

```text
a region DISJOINT b
```

thì specialized function có thể nhận:

```text
NoAlias(a, b)
```

ở mức compiler-internal.

Không cần programmer viết:

```text
restrict
```

---

# 13. Capability Facts ≠ ABI Arguments

Không nhất thiết phải thêm parameter machine-level:

```text
noalias_flag
range_flag
```

Các fact có thể tồn tại hoàn toàn trong:

```text
ProofDB
OptIR
AliasInfo
RangeInfo
```

và biến mất trước code generation.

---

# 14. Effect Specialization

Ví dụ:

```text
fn process(x, mode) {
    if mode == 0 {
        pure_path()
    } else {
        io_path()
    }
}
```

Nếu:

```text
mode == 0
```

specialized version không còn:

```text
IO
```

nhưng điều này phải được **derive lại từ body**, không được đơn giản xóa effect khỏi summary bằng assumption.

---

# 15. Panic Specialization

Ví dụ:

```text
fn get(x: usize) {
    if x >= 10 {
        panic()
    }
    table[x]
}
```

Nếu specialization có proof:

```text
x < 10
```

thì panic branch có thể biến mất.

Sau đó bounds check cũng có thể biến mất.

Pipeline:

```text
Range Proof
 ↓
Specialization
 ↓
SCCP
 ↓
Bounds Elimination
```

---

# 16. Drop Specialization

Không được specialization làm mất Drop chỉ vì branch trở nên unreachable.

Ví dụ:

```text
fn f<T>(x: T) {
    ...
}
```

với:

```text
T: Drop
```

specialized version vẫn phải giữ cleanup cần thiết.

Chỉ `Drop` elimination engine mới được quyết định rằng physical destructor work không observable.

---

# 17. Function Cloning

Specialization tạo:

```text
OriginalFunction
```

và:

```text
SpecializedFunction
```

Hai function có:

```text
semantic identity khác nhau
```

nhưng:

```text
origin_function
specialization_key
```

được lưu để compiler/debugger biết quan hệ.

---

# 18. Không được Clone vô hạn

Ví dụ:

```text
f(1)
f(2)
f(3)
...
f(1000000)
```

không được tạo một triệu function.

Có:

```text
SpecializationBudget {
    max_instances
    max_code_growth
    max_constant_dimensions
    max_depth
}
```

---

# 19. Specialization Cache

Key:

```text
SpecializationKey
+
SemanticFingerprint
+
TargetProfile
+
FeatureSet
```

Nếu đã tạo:

```text
f<i32, true>
```

thì call khác có thể tái sử dụng.

---

# 20. Cross-Module Specialization

Package A:

```text
library.ax
```

export:

```text
fn process<T>(...)
```

Package B:

```text
app.ax
```

gọi:

```text
process<MyType>(...)
```

`.axmeta` có thể cung cấp:

```text
type constraints
trait facts
effect summary
ownership summary
capability summary
ABI
specialization metadata
```

Nếu body được phép truy cập, compiler có thể specialize.

Nếu chỉ có interface:

```text
semantic optimization bị giới hạn
```

nhưng correctness không bị ảnh hưởng.

---

# 21. LTO

Ở LTO:

```text
Module A
Module B
Module C
       ↓
Whole Program Semantic Graph
       ↓
Specialization
```

Compiler có thể nhìn thấy nhiều constant/type facts hơn.

Nhưng LTO chỉ tăng optimization opportunity.

Không được thay đổi semantics.

---

# 22. PGO

PGO có thể cho biết:

```text
f(mode=0) 95%
f(mode=1) 5%
```

Compiler có thể specialize:

```text
f_mode_0
```

và giữ generic:

```text
f
```

cho các trường hợp còn lại.

PGO chỉ quyết định:

```text
profitability
```

không quyết định:

```text
legality
```

---

# 23. Guarded Specialization

Nếu fact chưa chắc chắn tại compile time:

```text
x < 16
```

compiler có thể tạo:

```text
if x < 16 {
    specialized_path(x)
} else {
    generic_path(x)
}
```

Đây là:

```text
RuntimeGuardedSpecialization
```

---

# 24. Guard Correctness

Guard phải được chứng minh:

```text
guard == specialization_precondition
```

Không được dùng heuristic kiểu:

```text
probably true
```

để bỏ generic fallback.

---

# 25. Guard Cost

Runtime guard chỉ đáng làm nếu:

```text
expected optimization benefit
>
guard cost
```

Cost model tính:

```text
branch
code size
instruction cache
branch predictability
specialized speedup
profile probability
```

---

# 26. Multi-Versioning

Một function có thể có:

```text
f_generic
f_small
f_large
f_avx2
f_avx512
```

và dispatcher chọn version.

Nhưng target feature dispatch phải phân biệt:

```text
CPU feature
```

với:

```text
semantic specialization
```

---

# 27. CPU Feature Specialization

Ví dụ:

```text
@target("avx2")
```

có thể tạo version SIMD.

Nhưng Axiom không được coi:

```text
AVX2 available
```

là fact semantic của chương trình.

Nó là:

```text
TargetFeatureFact
```

---

# 28. GPU Specialization

GPU kernel:

```text
@kernel fn process<T>(...)
```

có thể specialize theo:

```text
T
workgroup size
device capability
layout
vector width
```

nhưng:

```text
Host
Device
Shared
Local
```

storage domains vẫn phải được kiểm tra riêng.

---

# 29. Async Specialization

Ví dụ:

```text
async fn process(mode: bool) {
    if mode {
        await A()
    } else {
        await B()
    }
}
```

Nếu:

```text
mode == true
```

specialized Future chỉ chứa:

```text
await A()
```

Nhưng compiler phải tạo lại:

```text
SuspensionPoint
StateField
Drop
Send
```

facts.

Không được chỉ xóa branch trong representation đã lower mà bỏ qua state-machine semantics.

---

# 30. Closure Specialization

Closure:

```text
|x| x + constant
```

với:

```text
constant = 10
```

có thể specialize thành:

```text
|x| x + 10
```

Sau đó `292` có thể inline và `288` fold tiếp.

---

# 31. Specialization Pipeline với các Engine trước

Ví dụ:

```text
fn process(x, mode) {
    if mode == 0 {
        out[x] = x * 2
    } else {
        out[x] = x * 3
    }
}
```

Call:

```text
process(x, 0)
```

Pipeline:

```text
293 Specialization
        ↓
mode = 0
        ↓
288 Scalar
        ↓
branch eliminated
        ↓
289 Memory
        ↓
Memory facts
        ↓
290 Loop
        ↓
291 Vectorization Preparation
        ↓
292 Inline / Clone
        ↓
SIMD backend
```

Đây là lý do `293` nên tồn tại như một engine riêng.

---

# 32. Interprocedural Constant Propagation

Ngoài specialization, engine duy trì:

```text
ArgumentValueFact
```

cho callsite:

```text
Constant
Range
EnumVariant
TypeKnown
Nullability
Capability
```

Không phải tất cả đều tạo specialized function.

Có thể chỉ truyền fact vào analysis.

---

# 33. Value Fact Lattice

```text
ValueFact =
    Unknown
    Constant(value)
    Range(range)
    KnownVariant(variant)
    KnownType(type)
    KnownBool
    Overdefined
```

`Unknown` và `Overdefined` phải phân biệt.

---

# 34. Must / May

Ví dụ caller:

```text
mode = 0 hoặc 1
```

thì:

```text
mode ∈ {0,1}
```

không được biến thành:

```text
mode == 0
```

Compiler chỉ được truyền:

```text
KnownSet {0,1}
```

nếu analysis hỗ trợ.

---

# 35. Recursive Interprocedural Propagation

Call graph:

```text
A → B → C → A
```

phải xử lý SCC.

Facts phải đạt fixed point:

```text
F0
 ↓
F1
 ↓
F2
 ...
 ↓
FixedPoint
```

Không được phụ thuộc thứ tự traversal.

---

# 36. Incremental Compilation

Nếu:

```text
fn helper(x, mode)
```

thay đổi implementation nhưng public semantic fingerprint không đổi ở phần liên quan, compiler phải invalidate đúng specialization phụ thuộc.

Không được rebuild toàn bộ chương trình chỉ vì một source edit nhỏ.

---

# 37. Specialization Fingerprint

```text
SpecializationFingerprint {
    source_function_semantic_fingerprint
    specialization_key
    relevant_proofs
    target_features
    compiler_semantic_version
}
```

Không dùng machine code hash làm semantic identity.

---

# 38. Proof Dependency

Specialized function chỉ hợp lệ nếu:

```text
SpecializationProof
```

chứa:

```text
Precondition
SourceFacts
ProofDependencies
Target
Revision
```

Ví dụ:

```text
Precondition:
    mode == 0

Proof:
    caller argument is constant 0
```

Nếu caller thay đổi:

```text
mode = 1
```

proof bị invalid.

---

# 39. OptimizationGateway

Mọi specialization phải đi qua:

```text
OptimizationGateway
```

trình tự:

```text
Candidate
 ↓
Proof Validation
 ↓
Cost Decision
 ↓
Clone
 ↓
Substitution
 ↓
Reverification
 ↓
Publish
```

Không được tạo một specialized function “tạm đúng” rồi cho optimizer dùng trước khi verification.

---

# 40. Semantic Reverification

Sau specialization:

```text
Original
```

và:

```text
Specialized
```

phải cùng thỏa:

```text
Ownership
Capability
Effect
Panic
Drop
Async
GPU
FFI
ABI
```

contracts tương ứng.

Đây là điểm khác biệt quan trọng giữa Axiom và một optimizer pattern-rewrite đơn giản.

---

# 41. Module Structure

```text id="p8k4m2"
compiler/optimization/specialize/
├── mod.ax
├── candidate/
│   ├── candidate.ax
│   ├── key.ax
│   └── legality.ax
│
├── facts/
│   ├── value_fact.ax
│   ├── constant.ax
│   ├── range.ax
│   ├── enum_variant.ax
│   ├── type_fact.ax
│   ├── capability_fact.ax
│   └── target_fact.ax
│
├── propagation/
│   ├── interprocedural.ax
│   ├── callsite.ax
│   ├── summary.ax
│   ├── lattice.ax
│   └── scc.ax
│
├── clone/
│   ├── function_clone.ax
│   ├── substitution.ax
│   ├── local_remap.ax
│   ├── capability_remap.ax
│   ├── ownership_remap.ax
│   └── source_map.ax
│
├── guard/
│   ├── guard.ax
│   ├── precondition.ax
│   ├── fallback.ax
│   └── cost.ax
│
├── multiversion/
│   ├── mod.ax
│   ├── target_features.ax
│   ├── dispatcher.ax
│   └── selection.ax
│
├── cache/
│   ├── key.ax
│   ├── fingerprint.ax
│   └── store.ax
│
├── proof/
│   ├── specialization_proof.ax
│   └── dependency.ax
│
└── tests/
```

---

# 42. Implementation Order

```text
1. ValueFact model
2. Interprocedural value propagation
3. SCC fixed-point propagation
4. Callsite fact extraction
5. SpecializationKey
6. Candidate generation
7. Legality proof
8. Function cloning
9. Argument substitution
10. Constant substitution
11. Type substitution
12. Enum-variant specialization
13. Range specialization
14. Trait-target specialization
15. Capability fact propagation
16. Effect fact propagation
17. Panic specialization
18. Drop-safe specialization
19. Reverification
20. Specialization cache
21. Cost model
22. Budget
23. Guarded specialization
24. Fallback generation
25. Function multi-versioning
26. PGO integration
27. CPU-feature specialization
28. GPU specialization
29. Async specialization
30. Closure specialization
31. LTO integration
32. OptimizationGateway integration
33. diagnostics / optimization remarks
34. incremental invalidation
35. adversarial tests
```

---

# 43. Adversarial Tests

### Test 1 — Constant branch

```text
f(x, 0)
```

phải có thể specialize và loại branch.

### Test 2 — Unknown argument

```text
f(x, mode)
```

không được giả định `mode == 0`.

### Test 3 — Range

Proof:

```text
x < 16
```

cho phép specialized bounds elimination.

### Test 4 — Enum

Known variant phải loại branch không reachable.

### Test 5 — Ownership

Specialization không được tạo thêm ownership.

### Test 6 — Drop

Specialization không được bỏ destructor semantics.

### Test 7 — Capability

Không được biến `view` thành `mut_view`.

### Test 8 — Alias

Chỉ proven `DISJOINT` mới được tạo internal `NO_ALIAS`.

### Test 9 — Panic

Known-safe range có thể loại panic branch.

### Test 10 — Recursive SCC

Không được specialization vô hạn.

### Test 11 — Code explosion

Million callsites không được tạo million clones nếu budget không cho phép.

### Test 12 — Guard

Specialized path phải có fallback chính xác.

### Test 13 — Async

Specialized Future phải giữ đúng suspension semantics.

### Test 14 — GPU

Specialization không được đưa host-only operation vào kernel.

### Test 15 — Cross-module

`.axmeta` thiếu body → chỉ được dùng published facts, không được giả định implementation.

---

# 44. Frozen Invariants

### `ASPEC-20..95`

```text
ASPEC-20 — Specialization Preserves Function Semantics
ASPEC-21 — Specialization Requires A Proven Precondition
ASPEC-22 — Unknown Facts Cannot Become Known Facts
ASPEC-23 — May Facts Cannot Become Must Facts
ASPEC-24 — Constant Specialization Requires Proven Constants
ASPEC-25 — Range Specialization Requires Proven Ranges
ASPEC-26 — Enum Specialization Requires Proven Variant
ASPEC-27 — Type Specialization Requires Proven Type Identity
ASPEC-28 — Trait Specialization Requires Proven Concrete Target
ASPEC-29 — Capability Facts Must Preserve Provenance
ASPEC-30 — Specialization Must Not Invent Ownership
ASPEC-31 — Specialization Must Preserve Move Semantics
ASPEC-32 — Specialization Must Preserve Drop Semantics
ASPEC-33 — Specialization Must Preserve Initialization
ASPEC-34 — Specialization Must Preserve Capability Semantics
ASPEC-35 — Specialization Must Not Create Safe Aliasing
ASPEC-36 — Internal NoAlias Requires A Valid Proof
ASPEC-37 — Effect Specialization Must Be Re-derived From Specialized IR
ASPEC-38 — Panic Specialization Must Preserve Panic Semantics
ASPEC-39 — Bounds Elimination Requires Valid Range Proof
ASPEC-40 — Specialization Must Preserve Evaluation Order
ASPEC-41 — Specialization Must Preserve Atomic Semantics
ASPEC-42 — Specialization Must Preserve Volatile Semantics
ASPEC-43 — Specialization Must Preserve Synchronization
ASPEC-44 — Specialization Must Preserve FFI Contracts
ASPEC-45 — Specialization Must Preserve Stable-Address Contracts
ASPEC-46 — Async Specialization Must Preserve Suspension Semantics
ASPEC-47 — Async Specialization Must Preserve Future State Semantics
ASPEC-48 — GPU Specialization Must Preserve Execution Domains
ASPEC-49 — GPU Specialization Must Preserve Storage Domains
ASPEC-50 — Target Features Are Not Semantic Facts
ASPEC-51 — Specialization Identity Is Distinct From Type Identity
ASPEC-52 — Code Sharing Must Not Merge Semantic Types
ASPEC-53 — Recursive Specialization Is SCC-Bounded
ASPEC-54 — Specialization Growth Is Budgeted
ASPEC-55 — Specialization Count Is Budgeted
ASPEC-56 — Specialization Cache Keys Are Semantic
ASPEC-57 — Specialization Cache Must Include Relevant Proof Dependencies
ASPEC-58 — Stale Specialization Proofs Cannot Authorize Optimization
ASPEC-59 — Specialization Must Pass Through OptimizationGateway
ASPEC-60 — Specialized IR Must Be Reverified
ASPEC-61 — Failed Specialization Must Preserve Original Valid Code
ASPEC-62 — Guarded Specialization Requires A Correct Fallback
ASPEC-63 — Guard Preconditions Must Equal Specialization Preconditions
ASPEC-64 — Runtime Guards Cannot Assume Unproven Facts
ASPEC-65 — PGO Affects Profitability, Not Legality
ASPEC-66 — LTO May Refine Facts But Cannot Violate Published Contracts
ASPEC-67 — Cross-Module Specialization Uses Published Semantic Facts
ASPEC-68 — Incremental Invalidation Must Follow Proof Dependencies
ASPEC-69 — Specialization Must Be Deterministic
ASPEC-70 — Specialization Must Preserve Source Provenance
ASPEC-71 — Specialization Must Preserve Debug Mapping
ASPEC-72 — Specialized Functions Must Record Their Origin
ASPEC-73 — Specialization Must Not Accidentally Become Runtime Reflection
ASPEC-74 — Comptime Specialization Remains Distinct From Runtime Specialization
ASPEC-75 — Closure Specialization Must Preserve Capture Semantics
ASPEC-76 — Allocation Elimination After Specialization Requires Independent Escape Proof
ASPEC-77 — Specialization Must Not Depend On Undefined Behavior
ASPEC-78 — Cost Model Cannot Override Semantic Legality
ASPEC-79 — Code-Size Limits Must Be Respected
ASPEC-80 — Compile-Time Limits Must Be Respected
ASPEC-81 — Specialized Versions May Coexist With Generic Versions
ASPEC-82 — Specialized Version Selection Must Preserve Semantics
ASPEC-83 — Multi-Version Dispatch Must Respect Target Contracts
ASPEC-84 — Semantic Fingerprint And Codegen Fingerprint Remain Distinct
ASPEC-85 — Specialization Must Integrate With Interprocedural Summaries
ASPEC-86 — Specialization Must Integrate With Alias Analysis
ASPEC-87 — Specialization Must Integrate With MemorySSA
ASPEC-88 — Specialization Must Integrate With Loop Analysis
ASPEC-89 — Specialization Must Integrate With Vectorization
ASPEC-90 — Specialization Must Integrate With Inlining
ASPEC-91 — Proof Dependencies Must Be Explicit
ASPEC-92 — Rejected Specialization Must Not Affect Correctness
ASPEC-93 — Optimization Results Must Not Depend On Worker Count
ASPEC-94 — Optimization Results Must Not Depend On Cache Presence
ASPEC-95 — Specialization Is An Optimization Mechanism, Never A Semantic Requirement
```

---

## 45. Vị trí của Axiom sau BOOTSTRAP-293

Chuỗi compiler hiện đã có khả năng đi khá sâu:

```text
                 Semantic Facts
                      │
                      ▼
              Interprocedural
                 Analysis
                      │
             ┌────────┴────────┐
             ▼                 ▼
       Specialization       Inlining
             │                 │
             └────────┬────────┘
                      ▼
                   Scalar
                      │
                      ▼
                   Memory
                      │
                      ▼
                    Loop
                      │
                      ▼
                Vectorization
                      │
                      ▼
                 Native SIMD
```

Điểm quan trọng nhất của `293` là **compiler không còn phải chọn giữa “generic nhưng chậm” và “copy toàn bộ code”**.

Nó có thể giữ abstraction ở source level, sau đó chỉ chuyên biệt hóa đúng phần compiler chứng minh được có lợi.

**BOOTSTRAP-293 hoàn tất và được đóng băng.**