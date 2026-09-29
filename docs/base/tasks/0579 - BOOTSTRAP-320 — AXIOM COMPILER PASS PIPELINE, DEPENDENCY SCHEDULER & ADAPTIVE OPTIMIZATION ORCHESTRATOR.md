# BOOTSTRAP-320 — AXIOM COMPILER PASS PIPELINE, DEPENDENCY SCHEDULER & ADAPTIVE OPTIMIZATION ORCHESTRATOR

Sau 319, Axiom đã có cơ chế để **một pass chứng minh/khai báo điều kiện đúng của chính nó**. Bước tiếp theo là giải quyết câu hỏi ở cấp toàn compiler:

> **Hàng trăm analysis và optimization pass được lựa chọn, sắp xếp, lặp lại và dừng như thế nào để vừa nhanh, vừa tạo code tốt, vừa không chạy những thứ không cần thiết?**

320 xây dựng **Optimization Orchestrator**.

Điểm quan trọng: đây **không phải một danh sách pass cố định**. Compiler sẽ lập kế hoạch dựa trên:

- semantic facts hiện có
- facts mà optimization cần
- target
- code characteristics
- profile
- compile-time budget
- binary-size budget
- correctness contracts
- incremental cache
- PGO/runtime information nếu có

---

# 320.1. Mục tiêu

Pipeline mới:

```text
Input IR
   │
   ▼
Pass Planner
   │
   ├── Analysis Demand
   ├── Fact Dependencies
   ├── Target Features
   ├── Optimization Goals
   ├── Cost Model
   └── Validation Requirements
   │
   ▼
Pass Scheduler
   │
   ▼
Transformation
   │
   ▼
Proof / Validation
   │
   ▼
Fact Update
   │
   ▼
Next Decision
```

Không còn:

```text
run pass 1
run pass 2
run pass 3
...
run pass 100
```

một cách mù quáng.

---

# 320.2. Optimization Objective

Axiom không có một "best optimization" duy nhất.

Compiler phải tối ưu theo objective profile:

```text
OptimizationObjective {
    execution_speed
    binary_size
    compile_time
    memory_usage
    code_locality
    vectorization
    energy
    startup_time
}
```

Ví dụ:

```text
release
    speed = high
    size = medium
    compile_time = low
```

hoặc:

```text
size
    speed = medium
    size = maximum
```

hoặc:

```text
debug
    compile_time = maximum
    speed = low
```

---

# 320.3. Quan trọng: Objective Không Được Thay Đổi Semantics

Optimization profile chỉ thay đổi:

```text
implementation strategy
```

không thay đổi:

```text
language semantics
```

Do đó:

```text
-O0
-O2
-O3
-Os
-Osize
```

phải có cùng observable behavior trong phạm vi semantics của Axiom.

---

# 320.4. Pass Graph

Thay vì pass list:

```text
A → B → C → D
```

dùng:

```text
PassGraph
```

Mỗi node:

```text
PassNode {
    pass_id
    contract
    cost
    required_facts
    produced_facts
    invalidated_facts
}
```

Dependency:

```text
PassDependency {
    from
    to
    reason
}
```

---

# 320.5. Ví dụ

Vectorization yêu cầu:

```text
LoopInfo
NoAlias
RangeInfo
MemoryDependence
TargetSIMD
```

Compiler không nhất thiết chạy:

```text
LoopInfo
NoAlias
RangeInfo
MemoryDependence
```

tất cả từ đầu.

Thay vào đó:

```text
Vectorizer
    ↓ requires
FactPlanner
    ↓
find cheapest providers
```

Sau đó chỉ tính facts cần thiết.

---

# 320.6. Analysis Provider

Một fact có thể có nhiều provider.

Ví dụ:

```text
NoAlias(a,b)
```

có thể được chứng minh bởi:

```text
CapabilityAnalysis
TypeLayoutAnalysis
RegionAnalysis
InterproceduralAnalysis
FFI Contract
```

Planner chọn provider phù hợp.

Ví dụ:

```text
Provider A
cost = 1
precision = medium

Provider B
cost = 10
precision = high
```

Nếu optimization chỉ cần medium:

```text
→ chọn A
```

---

# 320.7. Precision Lattice

Analysis không chỉ:

```text
true / false
```

mà có thể có mức precision:

```text
Unknown
May
Likely
Proven
```

Tuy nhiên cần quy tắc nghiêm ngặt:

> `Likely` chỉ được dùng cho performance heuristic, không được dùng làm semantic proof.

Ví dụ:

```text
BranchLikelyTaken = 95%
```

được dùng cho:

```text
block layout
```

nhưng không được dùng cho:

```text
dead code elimination
```

---

# 320.8. Demand-Driven Optimization

Không phải function nào cũng cần mọi optimization.

Compiler phân loại:

```text
TinyFunction
SmallFunction
MediumFunction
LargeFunction
HotFunction
ColdFunction
VectorCandidate
AllocationHeavy
BranchHeavy
MemoryHeavy
AsyncFunction
GpuKernel
FFIBoundary
```

Sau đó chọn pipeline phù hợp.

Ví dụ function:

```text
fn add(a: i32, b: i32) -> i32
```

không cần chạy:

```text
LoopVectorization
ComplexAliasAnalysis
InterproceduralEscapeAnalysis
```

---

# 320.9. Function Classification

Thêm:

```text
FunctionProfile
```

bao gồm:

```text
instruction_count
basic_block_count
loop_count
call_count
memory_ops
branch_count
allocation_count
async
gpu
ffi
hotness
size
complexity
```

Nguồn:

- static analysis
- PGO
- user annotations
- build profile

---

# 320.10. Adaptive Pipeline

Pipeline có thể thay đổi theo function.

Ví dụ:

```text
foo()
```

được phát hiện:

```text
hot
loop-heavy
vectorizable
```

→ pipeline:

```text
Inlining
LoopCanonicalization
DependenceAnalysis
Vectorization
Unrolling
LICM
Scheduling
```

Trong khi:

```text
parse_error()
```

được phát hiện:

```text
cold
branch-heavy
```

→:

```text
BranchOptimization
CodeLayout
SizeOptimization
```

---

# 320.11. Inlining Decision

Inlining không nên chỉ dựa vào:

```text
function size < N
```

Mà sử dụng:

```text
InliningScore {
    hotness
    callee_size
    call_frequency
    constant_arguments
    specialization_gain
    vectorization_gain
    code_size_cost
    register_pressure_cost
    cache_cost
}
```

Ví dụ:

```text
foo → bar
```

Compiler có thể thấy:

```text
bar:
    5 instructions

but after inlining:
    constant propagation
    dead branch elimination
    vectorization
```

→ lợi ích tổng thể cao hơn.

---

# 320.12. Specialization Planner

Axiom có generics/monomorphization.

Không nên tạo mọi specialization một cách mù quáng.

Planner quyết định:

```text
Generic<T>
```

nên instantiate khi:

```text
used
beneficial
required by ABI
required by GPU
required by compile-time
```

Có thể tránh code bloat.

---

# 320.13. Monomorphization Budget

Compiler có:

```text
GenericExpansionBudget
```

dựa trên:

```text
max_instances
max_code_size
max_compile_time
```

Nếu generic tạo quá nhiều phiên bản:

```text
T = i8
T = i16
T = i32
T = i64
...
```

compiler có thể sử dụng:

- specialization
- shared implementation
- dynamic dispatch nếu API explicit
- outline function

nhưng không thay đổi semantic behavior.

---

# 320.14. Code Size Budget

Một optimization có thể tăng tốc nhưng làm binary lớn gấp đôi.

Planner phải biết:

```text
estimated_code_growth
```

Ví dụ:

```text
Inlining:
    speed gain = +8%
    code size = +22%
```

Nếu profile là:

```text
-Os
```

có thể reject.

Nếu:

```text
-O3
```

có thể accept.

---

# 320.15. Compile-Time Budget

Compiler cũng là một chương trình cần tối ưu.

Mỗi analysis có:

```text
estimated_cost
```

Ví dụ:

```text
CheapAliasAnalysis = 1
DeepInterproceduralAliasAnalysis = 100
```

Nếu function nhỏ:

```text
→ cheap analysis
```

Nếu hot kernel lớn:

```text
→ expensive analysis
```

---

# 320.16. Optimization ROI

Mỗi pass có:

```text
OptimizationBenefit
OptimizationCost
```

Compiler tính:

```text
ROI = benefit / cost
```

nhưng ROI chỉ là **planner heuristic**.

Nó không phải semantic proof.

---

# 320.17. Pass Iteration

Nhiều optimization tạo cơ hội cho optimization khác.

Ví dụ:

```text
Inlining
↓
ConstantPropagation
↓
DCE
↓
CFG Simplification
↓
NewInliningOpportunity
```

Pipeline cần fixed-point strategy.

```text
repeat
    choose profitable pass
until
    no profitable transformation
    or budget exhausted
```

Nhưng không được phép loop vô hạn.

---

# 320.18. Fixed-Point Guard

Mỗi optimization region có:

```text
IterationState {
    iteration
    IRFingerprint
    factFingerprint
    transformationCount
}
```

Nếu:

```text
IRFingerprint unchanged
```

→ dừng.

Nếu transformation cycle:

```text
A → B → A
```

→ phát hiện và dừng.

---

# 320.19. Pass Oscillation Prevention

Ví dụ:

```text
Pass A:
    transform X → Y

Pass B:
    transform Y → X
```

Không được:

```text
A
B
A
B
A
B
...
```

Planner lưu:

```text
TransformationHistory
```

và có cycle detector.

---

# 320.20. Target-Aware Planning

Cùng một Axiom source:

```text
foo()
```

target:

```text
x86-64
```

có thể chọn:

```text
AVX2
BMI2
FMA
```

trong khi:

```text
ARM64
```

chọn:

```text
NEON
SVE
```

và:

```text
RISC-V
```

pipeline khác.

Semantic IR không đổi.

---

# 320.21. CPU Feature Specialization

Compiler có thể tạo:

```text
foo.default
foo.avx2
foo.avx512
```

và dispatch nếu target/runtime contract cho phép.

Nhưng phải explicit trong ABI/runtime model.

Không được tự ý biến binary deterministic thành runtime CPU-dependent nếu profile không cho phép.

---

# 320.22. GPU Pipeline

GPU cũng dùng orchestrator:

```text
Kernel
 ↓
GPU legality
 ↓
Memory analysis
 ↓
Barrier analysis
 ↓
Kernel fusion candidate
 ↓
GPU vectorization
 ↓
Occupancy optimization
 ↓
GPU scheduling
```

Planner phải tính:

```text
occupancy
register pressure
shared memory
memory bandwidth
warp/wave utilization
```

---

# 320.23. Async Pipeline

Async function:

```text
async fn foo()
```

pipeline:

```text
AsyncAnalysis
 ↓
StateFieldLiveness
 ↓
StateFieldElision
 ↓
AwaitFusion
 ↓
FutureInlining
 ↓
StateSwitchOptimization
```

Không chạy các pass async trên function không async.

---

# 320.24. Memory Optimization Ordering

Memory optimizer phải tôn trọng:

```text
Ownership
Capability
Effect
Atomic
Volatile
FFI
```

Ví dụ:

```text
Load A
Load B
```

chỉ được reorder nếu dependency graph cho phép.

Planner không được coi:

```text
UNKNOWN alias
```

là:

```text
NO alias
```

---

# 320.25. PGO Integration

Nếu có Profile-Guided Optimization:

```text
Runtime Profile
      ↓
ProfileDB
      ↓
OptimizationPlanner
```

Profile có thể cung cấp:

```text
hotness
branch probability
call frequency
cache behavior
allocation frequency
```

Nhưng profile là:

> **Optimization evidence, not semantic evidence.**

Profile sai không được phép tạo ra semantic bug.

---

# 320.26. Profile Mismatch

Nếu source đã thay đổi:

```text
old profile
```

không được tin tuyệt đối.

Compiler đánh dấu:

```text
ProfileCompatibility {
    exact
    compatible
    stale
    incompatible
}
```

Profile stale chỉ được dùng khi policy cho phép.

---

# 320.27. Link-Time Optimization

Planner không chỉ hoạt động trong một function.

Các cấp:

```text
Function
Region
Module
Package
Whole Program
LTO
```

Ví dụ LTO có thể thấy:

```text
foo()
```

chỉ được gọi bởi:

```text
bar()
```

→ inlining.

Nhưng semantic contract vẫn giống 319.

---

# 320.28. Whole-Program Dead Code Elimination

Nếu symbol:

```text
foo
```

không reachable từ:

```text
entry
exports
FFI
reflection
dynamic loading
```

thì có thể loại bỏ.

Nhưng planner phải kiểm tra:

```text
@export
FFI
runtime lookup
reflection metadata
plugin boundary
```

trước khi kết luận unreachable.

---

# 320.29. Dynamic Boundary

Nếu:

```text
dyn Trait
```

hoặc:

```text
extern
```

hoặc:

```text
@export
```

thì planner phải tạo:

```text
DynamicBoundary
```

để tránh optimization làm mất symbol/behavior cần thiết.

---

# 320.30. Deterministic Optimization

Hai build giống nhau phải có:

```text
same source
same compiler
same target
same profile
same dependencies
same PGO data
```

→ cùng optimization decisions.

Randomized search nếu được dùng phải có deterministic seed trong reproducible mode.

---

# 320.31. Optimization Decision Log

Compiler lưu:

```text
OptimizationDecision {
    pass
    candidate
    decision
    reason
    required_facts
    estimated_cost
    estimated_benefit
}
```

Ví dụ:

```text
Inlining(foo → bar)

Decision: REJECT

Reason:
    estimated code growth = 14%
    expected execution benefit = 1.2%
    profile = -Os
```

Đây là **explanation**, không phải ranking.

---

# 320.32. AI Performance Interface

AI có thể hỏi:

```text
Why is this function slow?
```

Compiler trả:

```text
Hotness:
    82%

Missed opportunities:
    vectorization: no proof of disjoint memory
    inlining: code growth too high
    allocation elimination: storage identity observable

Applied:
    LICM
    GVN
    bounds-check elimination
```

AI không cần đoán compiler đang nghĩ gì.

---

# 320.33. Adaptive Compilation

Trong môi trường hỗ trợ JIT/recompilation về sau:

```text
initial compile
      ↓
runtime profile
      ↓
optimization planner
      ↓
recompile hot region
```

Nhưng đây không phải Core requirement.

Axiom compiler architecture chỉ cần đảm bảo planner có thể nhận dynamic profile.

---

# 320.34. Pass Database

Thêm:

```text
PassDB
```

vào CompilerDB:

```text
CompilerDB
 ├── SourceDB
 ├── TypeDB
 ├── HIRDB
 ├── MIRDB
 ├── CorrectnessDB
 ├── PassDB
 ├── OptimizationDB
 └── BuildDB
```

`PassDB` lưu:

- contracts
- pass metadata
- dependencies
- cost models
- target requirements
- validation strategies
- historical statistics

---

# 320.35. Implementation Tree

```text
compiler/optimization/
├── planner/
│   ├── planner.ax
│   ├── objective.ax
│   ├── budget.ax
│   ├── candidate.ax
│   └── decision.ax
│
├── scheduler/
│   ├── pass_graph.ax
│   ├── scheduler.ax
│   ├── dependency.ax
│   └── fixed_point.ax
│
├── analysis/
│   ├── provider.ax
│   ├── demand.ax
│   ├── precision.ax
│   └── profile.ax
│
├── cost/
│   ├── cost_model.ax
│   ├── benefit_model.ax
│   ├── size_model.ax
│   └── compile_time.ax
│
├── specialization/
│   ├── generic_planner.ax
│   ├── specialization.ax
│   └── monomorphization.ax
│
├── target/
│   ├── cpu.ax
│   ├── gpu.ax
│   ├── wasm.ax
│   └── abi.ax
│
├── pgo/
│   ├── profile_db.ax
│   ├── compatibility.ax
│   └── feedback.ax
│
└── explanation/
    ├── decision.ax
    └── performance.ax
```

---

# 320.36. Invariants

```text id="4nkg6v"
AOPT-20  Optimization never changes language semantics.

AOPT-21  Optimization objectives affect strategy, never semantics.

AOPT-22  A pass runs only when its required semantic facts are available.

AOPT-23  UNKNOWN is never sufficient for a semantic transformation.

AOPT-24  Performance heuristics cannot establish correctness facts.

AOPT-25  Pass dependencies are represented explicitly.

AOPT-26  Analysis is demand-driven whenever possible.

AOPT-27  Cached facts are reused only when fingerprints remain valid.

AOPT-28  Invalidated facts cannot be consumed.

AOPT-29  Optimization planning is deterministic under reproducible-build settings.

AOPT-30  Fixed-point optimization must terminate.

AOPT-31  Pass oscillation must be detected.

AOPT-32  Code-size constraints participate in optimization decisions.

AOPT-33  Compile-time cost participates in optimization decisions.

AOPT-34  Target features may affect implementation strategy but not semantics.

AOPT-35  PGO data is optimization evidence, never semantic proof.

AOPT-36  Stale profile data cannot silently become semantic information.

AOPT-37  Dynamic boundaries are preserved during dead-code analysis.

AOPT-38  FFI/export/reflection boundaries are optimization barriers unless explicitly contracted.

AOPT-39  GPU optimization obeys GPU memory and execution-domain contracts.

AOPT-40  Async optimization preserves suspension and cancellation semantics.

AOPT-41  Optimization decisions are explainable.

AOPT-42  Optimization failures degrade to valid unoptimized code, never invalid code.
```

---

# 320.37. Definition of Done

BOOTSTRAP-320 hoàn thành khi:

1. Có `PassGraph`.
2. Có `OptimizationPlanner`.
3. Có objective profiles.
4. Có optimization budgets.
5. Có demand-driven analysis.
6. Có fact-provider selection.
7. Có analysis precision model.
8. Có function classification.
9. Có adaptive per-function pipeline.
10. Có inlining planner.
11. Có generic specialization planner.
12. Có code-size budget.
13. Có compile-time budget.
14. Có fixed-point optimizer.
15. Có oscillation detection.
16. Có target-aware pipeline.
17. Có GPU pipeline planning.
18. Có async pipeline planning.
19. Có PGO integration.
20. Có LTO planning.
21. Có dynamic-boundary protection.
22. Có deterministic optimization.
23. Có optimization decision log.
24. Có AI explanation API.
25. Có benchmark-driven cost model.
26. Có regression tests cho planner.
27. Có end-to-end:

```text
Program
   ↓
Analyze
   ↓
Demand Facts
   ↓
Select Pass
   ↓
Transform
   ↓
Prove
   ↓
Validate
   ↓
Commit
   ↓
Re-plan
   ↓
Fixed Point
   ↓
Codegen
```

---

## Nguyên tắc đóng băng của 320

> **Axiom không có một “optimization pipeline” duy nhất. Axiom có một compiler optimization planner có khả năng tự xây pipeline phù hợp với từng chương trình, từng target và từng mục tiêu, nhưng mọi quyết định đều nằm dưới semantic contract và correctness system của 318–319.**

Như vậy, compiler càng lớn thì **logic điều phối càng thông minh**, trong khi ngôn ngữ Axiom và semantics vẫn giữ nguyên tính xác định.