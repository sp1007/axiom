# BOOTSTRAP-287 — AXIOM OPTIMIZATION PASS MANAGER & TRANSFORMATION PIPELINE
## FROZEN / COMPLETED

### 1. Mục tiêu

`BOOTSTRAP-286` đã tạo:

- Analysis Orchestrator
- Proof Dependency Graph
- Proof Store
- Optimization Gateway

Bước tiếp theo là xây **bộ máy điều phối optimization thực sự**.

Không nên bắt đầu bằng việc viết từng optimization pass riêng lẻ. Cần định nghĩa trước cách compiler:

```text
- đăng ký pass
- xác định dependency
- yêu cầu analysis/proof
- chạy pass
- kiểm tra kết quả
- invalidation
- lặp pipeline
- chọn pipeline theo target/profile
- chạy song song khi có thể
- kiểm soát compile-time
- debug/replay optimization
```

Nguyên tắc:

> **Optimization pass là một transformation có contract; Pass Manager là hệ thống quyết định transformation nào được chạy, theo thứ tự nào và với những proof nào.**

---

# 2. Pipeline tổng thể

Kiến trúc:

```text
Verified MIR
     │
     ▼
Analysis Orchestrator
     │
     ▼
Proof Engine
     │
     ▼
OptIR Construction
     │
     ▼
Optimization Pass Manager
     │
     ├── Canonicalization
     ├── Simplification
     ├── Scalar Optimization
     ├── Memory Optimization
     ├── Control Flow
     ├── Interprocedural
     ├── Loop Optimization
     ├── Vectorization
     ├── Specialization
     ├── Target Optimization
     └── Size Optimization
     │
     ▼
Optimized OptIR
     │
     ▼
Semantic Reverification
     │
     ▼
ABI Lowering
```

Điểm bắt buộc:

```text
Optimization
      ↓
Reverification
      ↓
Next optimization stage
```

Không cho phép một pass tạo ra IR “tin rằng đúng”.

---

# 3. OptIR là IR dành cho optimizer

MIR vẫn là semantic source of truth.

OptIR phục vụ optimization:

```text
Verified MIR
     ↓
   OptIR
```

OptIR có thể chứa:

```text
SSA
MemorySSA
AliasInfo
EffectInfo
RangeInfo
LoopInfo
EscapeInfo
TargetInfo
CostInfo
```

nhưng không được biến thành một semantic model độc lập.

Nguyên tắc:

> **OptIR được phép giàu thông tin hơn MIR nhưng không được định nghĩa semantics khác MIR.**

---

# 4. Optimization Pass

```text
OptimizationPass {
    pass_id: PassId
    name: Symbol

    scope:
        Instruction
        Block
        Function
        SCC
        Module
        Program

    required_analyses
    required_proofs

    preserves
    invalidates

    transform_contract
    cost_model

    run(input) -> PassResult
}
```

---

# 5. PassResult

```text
PassResult {
    changed: bool

    ir_revision

    preserved_analyses
    invalidated_analyses

    preserved_proofs
    invalidated_proofs

    new_facts
    new_proofs

    statistics
}
```

Một pass **không được** nói:

```text
"mọi analysis vẫn đúng"
```

nếu nó không chứng minh được điều đó.

---

# 6. Pass Dependency

Ví dụ:

```text
GVN
```

cần:

```text
SSA
MemorySSA
EffectInfo
AliasInfo
```

Pipeline manager phải resolve:

```text
GVN
 │
 ├── SSA
 ├── MemorySSA
 ├── Effect
 └── Alias
```

Không bắt programmer/compiler developer phải tự nhớ thứ tự mọi pass.

---

# 7. Pass Dependency Graph

Passes tạo thành DAG hoặc iterative regions:

```text
Canonicalize
     │
     ▼
SimplifyCFG
     │
     ▼
SROA
     │
     ▼
InstCombine
     │
     ▼
GVN
     │
     ▼
DCE
     │
     ▼
LoopSimplify
     │
     ▼
LICM
     │
     ▼
Vectorization
```

Một số optimization có thể tạo cơ hội cho optimization trước đó:

```text
Inline
  ↓
Constant Propagation
  ↓
DCE
  ↓
SimplifyCFG
  ↓
Inline opportunity
```

Do đó Pass Manager phải hỗ trợ:

```text
Pipeline
FixedPoint
Iteration
ConditionalPass
AdaptivePipeline
```

---

# 8. Fixed-Point Region

Ví dụ:

```text
repeat until stable:
    Inline
    ConstantFold
    InstCombine
    DCE
    SimplifyCFG
```

Điều kiện dừng:

```text
NoChange
MaxIterations
CostThreshold
CompileBudget
```

Không được loop vô hạn.

---

# 9. Pass Groups

Thay vì pipeline khổng lồ:

```text
PassGroup {
    name
    passes
    iteration_policy
    analysis_scope
}
```

Ví dụ:

```text
ScalarCleanup {
    SCCP
    InstCombine
    GVN
    DCE
}
```

```text
LoopOptimization {
    LoopSimplify
    LICM
    Induction
    Unroll
    Vectorize
}
```

---

# 10. Optimization Profiles

Axiom không nên có một pipeline duy nhất.

Các profile cơ bản:

```text
Debug
Development
Optimize
OptimizeSize
OptimizeSpeed
Freestanding
Embedded
GPU
LTO
PGO
```

Ví dụ:

```text
OptimizeSpeed
    → aggressive inlining
    → vectorization
    → loop optimization
```

Trong khi:

```text
OptimizeSize
    → conservative inlining
    → outlining
    → identical code folding
    → section elimination
```

Semantics phải giống nhau.

---

# 11. Cost Model

Optimization không chỉ là:

```text
if legal:
    transform
```

mà:

```text
if legal && profitable:
    transform
```

Tạo:

```text
CostModel {
    estimate_instruction_cost
    estimate_code_size
    estimate_register_pressure
    estimate_memory_cost
    estimate_branch_cost
    estimate_call_cost
    estimate_vector_cost
    estimate_cache_cost
}
```

Nhưng:

> Cost model quyết định **có nên tối ưu**, không quyết định **có được phép tối ưu**.

Legal:

```text
Proof
```

Profitable:

```text
CostModel
```

Hai khái niệm hoàn toàn khác nhau.

---

# 12. Transform Decision

```text
TransformCandidate
        │
        ▼
Legality Check
        │
   ┌────┴────┐
   │         │
 reject     valid
             │
             ▼
         Cost Model
             │
       ┌─────┴─────┐
       │           │
    unprofitable profitable
       │           │
     reject       apply
```

Không bao giờ:

```text
"profitable" → "legal"
```

---

# 13. Optimization Budget

Compiler cần giới hạn:

```text
compile_time
memory
IR_growth
code_size
optimization_iterations
inline_depth
specialization_count
```

```text
OptimizationBudget {
    max_compile_time
    max_memory
    max_ir_growth
    max_code_size_growth
    max_iterations
    max_inline_depth
    max_specializations
}
```

Budget chỉ ảnh hưởng mức optimization, không ảnh hưởng semantics.

---

# 14. Adaptive Optimization

Ví dụ:

```text
small function
    → aggressive inline

huge function
    → conservative

hot PGO function
    → aggressive

cold function
    → size optimization
```

Nguồn dữ liệu:

```text
static heuristics
target information
PGO
profile metadata
LTO information
code-size estimate
```

Không được sử dụng thông tin chưa xác thực để phá semantic correctness.

---

# 15. Function-Level Parallelism

Các function độc lập có thể optimize song song:

```text
Module
 ├── foo ──┐
 ├── bar ──┼── parallel
 ├── baz ──┤
 └── qux ──┘
```

Nhưng:

```text
Interprocedural
LTO
SCC
global optimization
```

có dependency toàn chương trình.

Pass Manager phải phân biệt:

```text
FunctionParallel
ModuleSerial
SCCParallel
ProgramSerial
```

---

# 16. Deterministic Optimization

Chạy:

```text
1 worker
8 workers
32 workers
```

không được tạo semantic khác nhau.

Trong phạm vi cùng:

```text
target
profile
compiler version
PGO data
LTO configuration
comptime inputs
```

compiler phải tạo cùng:

```text
semantic result
```

Binary byte-for-byte có thể phụ thuộc vào các lựa chọn backend/linker được phép nondeterministic, nhưng Axiom nên hướng tới deterministic binary khi bật reproducible mode.

---

# 17. Analysis Invalidation

Ví dụ pass:

```text
SimplifyCFG
```

thay đổi CFG.

Nó phải invalidate:

```text
Dominators
LoopInfo
PostDominators
Path-sensitive facts
```

nhưng có thể giữ:

```text
Type facts
Target features
```

Pass Manager dùng:

```text
PreservedAnalysisSet
InvalidatedAnalysisSet
```

để tránh recompute toàn bộ.

---

# 18. Proof Invalidation

Tương tự:

```text
LoopTransformation
```

có thể invalidate:

```text
BoundsProof
LoopIterationProof
CFGProof
```

nhưng giữ:

```text
TypeProof
SendProof
FfiContractProof
```

nếu dependencies không thay đổi.

---

# 19. Reverification Boundary

Sau nhóm optimization quan trọng:

```text
OptIR
  ↓
LowerToMIR
  ↓
Verifier
```

hoặc verifier trực tiếp trên OptIR nếu representation đủ semantic.

Mục tiêu:

```text
Optimization
   ↓
Verification
   ↓
Optimization
```

Không để một lỗi optimization lan truyền qua 20 pass rồi mới phát hiện.

---

# 20. Transactional Transformation

Một pass nên hoạt động theo transaction:

```text
snapshot
   ↓
plan transform
   ↓
check proofs
   ↓
apply
   ↓
validate
   ↓
commit
```

Nếu thất bại:

```text
rollback
```

IR trước transform vẫn hợp lệ.

Điều này đặc biệt quan trọng với:

- aggressive optimization
- parallel optimization
- speculative optimization
- LTO
- PGO

---

# 21. Optimization Replay

Compiler nên có khả năng ghi lại:

```text
OptimizationTrace {
    pass
    input_revision
    required_proofs
    decisions
    cost_estimate
    transform
    output_revision
}
```

Sau đó:

```text
axiomc --replay-opt trace.axopt
```

có thể tái hiện một optimization decision.

Điều này cực kỳ hữu ích để debug compiler.

---

# 22. Optimization Remarks

Ví dụ:

```text
INLINE foo → bar
reason:
    cost = 17
    threshold = 30
    hotness = high
```

Hoặc:

```text
VECTORIZE loop #42
rejected:
    missing NoAlias(a,out)
```

Hoặc:

```text
ALLOCATION ELIMINATION
rejected:
    ReturnEscape
```

AI có thể đọc các structured records này.

---

# 23. Pass Categories

Axiom nên chuẩn hóa category:

```text
Canonicalization
CFG
Scalar
Memory
Alias
ControlFlow
Inlining
Specialization
Interprocedural
Loop
Vectorization
SIMD
Concurrency
Async
GPU
Target
Size
LTO
PGO
DebugPreservation
```

Không ép mọi pass phải thuộc đúng một category; đây chủ yếu là metadata/tooling.

---

# 24. Pass Ordering

Pass ordering không được là một danh sách bất biến duy nhất.

Ví dụ:

```text
Inlining
    ↓
Constant Propagation
    ↓
DCE
```

có thể tốt hơn:

```text
Constant Propagation
    ↓
Inlining
```

trong một số trường hợp.

Pass Manager có thể dùng:

```text
static pipeline
+
target heuristics
+
profile information
+
cost model
```

nhưng phải giữ:

```text
legality invariant
```

---

# 25. No Semantic Optimization Mode

Axiom nên có:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
```

hoặc tên tương đương.

Nhưng:

```text
-O0
```

không có nghĩa:

```text
skip semantic verification
```

Mà:

```text
-O0:
    minimal optimization
    full semantic verification
```

Điều này rất quan trọng vì:

> **Safety và correctness không phải optimization.**

---

# 26. Optimization Level không được thay đổi ngôn ngữ

Không được có:

```text
-O3:
    program behaves differently
```

Do đó:

```text
optimization level
```

chỉ chọn implementation strategy.

---

# 27. Pass Plugin Model

Không nên cho arbitrary external plugins sửa OptIR trong Core v1.

Nếu sau này hỗ trợ:

```text
compiler plugin
```

thì plugin phải có:

```text
versioned pass ABI
proof contract
IR version
capability restrictions
determinism contract
```

Nhưng **không nằm trong Core compiler architecture v1**.

---

# 28. Module Tree

```text
compiler/optimization/
├── mod.ax
├── pass/
│   ├── mod.ax
│   ├── pass_id.ax
│   ├── pass.ax
│   ├── pass_contract.ax
│   ├── pass_scope.ax
│   ├── pass_result.ax
│   ├── pass_registry.ax
│   └── pass_metadata.ax
│
├── manager/
│   ├── mod.ax
│   ├── pass_manager.ax
│   ├── scheduler.ax
│   ├── dependency.ax
│   ├── fixed_point.ax
│   ├── parallel.ax
│   ├── budget.ax
│   └── cancellation.ax
│
├── pipeline/
│   ├── mod.ax
│   ├── pipeline.ax
│   ├── stage.ax
│   ├── profile.ax
│   ├── adaptive.ax
│   └── builder.ax
│
├── transform/
│   ├── mod.ax
│   ├── candidate.ax
│   ├── legality.ax
│   ├── transaction.ax
│   ├── commit.ax
│   └── rollback.ax
│
├── cost/
│   ├── mod.ax
│   ├── cost_model.ax
│   ├── instruction_cost.ax
│   ├── register_pressure.ax
│   ├── code_size.ax
│   └── target_cost.ax
│
├── trace/
│   ├── mod.ax
│   ├── optimization_trace.ax
│   ├── replay.ax
│   └── remarks.ax
│
└── tests/
```

---

# 29. Implementation Order

```text
1. PassId
2. Pass metadata
3. Pass contract
4. PassResult
5. Pass registry
6. Pass dependency graph
7. Pass scheduler
8. Analysis invalidation integration
9. Proof invalidation integration
10. Fixed-point execution
11. Transactional transform
12. Rollback
13. Cost model interface
14. Optimization budget
15. Optimization profiles
16. Adaptive pipeline
17. Parallel function scheduling
18. Deterministic scheduling
19. Optimization trace
20. Optimization replay
21. Optimization remarks
22. CompilerDB integration
23. LTO integration
24. PGO integration
25. adversarial tests
```

---

# 30. Adversarial Tests

### Test 1 — Illegal transform

Pass yêu cầu:

```text
NoAlias(a,b)
```

nhưng proof:

```text
UNKNOWN
```

Expected:

```text
transform = rejected
```

---

### Test 2 — Cost rejection

```text
legal = true
profitability = false
```

Expected:

```text
transform = skipped
```

Không phải compiler error.

---

### Test 3 — Stale proof

```text
proof revision = R10
IR revision = R11
```

Expected:

```text
proof rejected
reanalysis/replanning
```

---

### Test 4 — Rollback

Pass tạo IR không hợp lệ.

Expected:

```text
commit = false
IR = original valid IR
```

---

### Test 5 — Fixed point

```text
Pass A enables Pass B
Pass B enables Pass A
```

Expected:

```text
iterate
→ stable
```

Không infinite loop.

---

### Test 6 — Budget

Optimization đạt:

```text
max_iterations
```

Expected:

```text
stop optimization
```

nhưng program vẫn hợp lệ.

---

### Test 7 — Parallel determinism

```text
1 worker
16 workers
```

Expected semantic OptIR fingerprint giống nhau trong reproducible mode.

---

### Test 8 — Analysis invalidation

CFG thay đổi.

Expected:

```text
Dominator = invalid
LoopInfo = invalid
TypeInfo = preserved
```

Không recompute TypeInfo.

---

### Test 9 — Proof preservation

Một pass chỉ thay đổi instruction scheduling mà không thay đổi semantic dependencies.

Expected các proof không liên quan được giữ lại.

---

### Test 10 — O0

`-O0` vẫn phải:

```text
run semantic verifier
```

và không được biến chương trình không hợp lệ thành chương trình hợp lệ bằng cách bỏ verification.

---

# 31. Frozen Invariants

### `APASS-20..60`

```text
APASS-20 — Every Optimization Pass Has A Stable Pass Identity
APASS-21 — Every Pass Declares Its Scope
APASS-22 — Every Pass Declares Required Analyses
APASS-23 — Every Pass Declares Required Proofs
APASS-24 — Every Pass Declares Preservation And Invalidation
APASS-25 — Every Pass Produces A Structured PassResult
APASS-26 — Pass Ordering Is Controlled By PassManager
APASS-27 — Pass Dependencies Are Explicit
APASS-28 — Duplicate Pass Requirements Are Deduplicated
APASS-29 — Fixed-Point Pipelines Have Explicit Termination Rules
APASS-30 — Optimization Budget Cannot Affect Semantic Correctness
APASS-31 — Failed Optimization Preserves The Last Valid IR
APASS-32 — Optimization Transformations Are Transactional
APASS-33 — Invalid Transformations Cannot Be Committed
APASS-34 — Cost Models Cannot Authorize Illegal Transformations
APASS-35 — Legality Is Determined By Semantic Proofs
APASS-36 — Profitability Is Separate From Legality
APASS-37 — Optimization Level Cannot Change Language Semantics
APASS-38 — O0 Still Performs Required Semantic Verification
APASS-39 — Parallel Pass Execution Is Deterministic Where Required
APASS-40 — Worker Count Cannot Change Semantic Results
APASS-41 — Pass Cancellation Cannot Publish Partial Results
APASS-42 — Analysis Invalidation Is Explicit
APASS-43 — Proof Invalidation Is Explicit
APASS-44 — Preserved Analyses Require A Valid Preservation Contract
APASS-45 — Preserved Proofs Require Valid Dependency Preservation
APASS-46 — Stale Proofs Cannot Authorize Transforms
APASS-47 — Passes Cannot Fabricate Proofs
APASS-48 — Passes Cannot Bypass OptimizationGateway
APASS-49 — OptIR Cannot Redefine MIR Semantics
APASS-50 — Verified MIR Remains The Semantic Source Of Truth
APASS-51 — Optimization Does Not Weaken Ownership
APASS-52 — Optimization Does Not Weaken Capability Safety
APASS-53 — Optimization Does Not Weaken Effect Semantics
APASS-54 — Optimization Does Not Weaken Concurrency Semantics
APASS-55 — Optimization Does Not Weaken Async Semantics
APASS-56 — Optimization Does Not Weaken GPU Semantics
APASS-57 — Optimization Does Not Weaken FFI Contracts
APASS-58 — Every Optimization Stage Has A Validity Boundary
APASS-59 — Optimization Traces Preserve Decision Provenance
APASS-60 — Optimization Replay Uses Versioned Semantic Contracts
```

### `APIPE-20..45`

```text
APIPE-20 — Pipelines Are Explicit Compiler Objects
APIPE-21 — Pipelines May Contain Pass Groups
APIPE-22 — Pass Groups May Iterate To Fixed Point
APIPE-23 — Fixed-Point Iteration Has A Bounded Termination Policy
APIPE-24 — Pipelines Are Target-Aware
APIPE-25 — Pipelines Are Profile-Aware
APIPE-26 — Pipelines May Use PGO Information
APIPE-27 — Pipelines May Use LTO Information
APIPE-28 — Pipeline Decisions Cannot Override Legality Proofs
APIPE-29 — Pipeline Decisions Cannot Alter Program Semantics
APIPE-30 — Optimization Profiles Differ Only In Implementation Strategy
APIPE-31 — Adaptive Pipelines Preserve Semantic Determinism
APIPE-32 — Function-Independent Passes May Execute In Parallel
APIPE-33 — Cross-Function Passes Respect Call Dependencies
APIPE-34 — SCC Passes Respect SCC Boundaries
APIPE-35 — Program-Wide Passes Have Explicit Program Scope
APIPE-36 — Pipeline Construction Is Reproducible Under Fixed Configuration
APIPE-37 — Pipeline Budget Exhaustion Is Not A Compilation Error
APIPE-38 — Pipeline Cancellation Leaves A Valid Previous State
APIPE-39 — Pipeline Diagnostics Are Structured
APIPE-40 — Pipeline Decisions Are Explainable
APIPE-41 — Pipeline State Is Revision-Aware
APIPE-42 — Pipeline Caches Are Managed Through CompilerDB
APIPE-43 — Pipeline Replay Requires Matching Semantic Contracts
APIPE-44 — Pipeline Extensions Cannot Bypass Verification
APIPE-45 — PassManager Is The Authoritative Optimization Scheduler
```

---

# 32. Vị trí mới của compiler

Sau `286 + 287`, kiến trúc đã trở thành:

```text
                  VERIFIED MIR
                       │
                       ▼
             ┌──────────────────┐
             │ Analysis         │
             │ Orchestrator     │
             └────────┬─────────┘
                      │
                      ▼
                Proof Engine
                      │
                      ▼
                Optimization
                  Gateway
                      │
                      ▼
                    OptIR
                      │
                      ▼
              ┌───────────────┐
              │ Pass Manager  │
              └───────┬───────┘
                      │
          ┌───────────┼────────────┐
          ▼           ▼            ▼
       Scalar       Memory       Loop
          │           │            │
          └───────────┼────────────┘
                      ▼
                Optimized OptIR
                      │
                      ▼
                 Reverify
                      │
                      ▼
                 ABI Lowering
```

Điểm quan trọng nhất của `287` là Axiom giờ đã tách rất rõ ba câu hỏi:

```text
ANALYSIS:
    "Chương trình đang có tính chất gì?"

PROOF:
    "Compiler có đủ bằng chứng để tin tính chất đó không?"

OPTIMIZATION:
    "Có nên biến đổi chương trình dựa trên bằng chứng đó không?"
```

Ba tầng này **không được nhập làm một**.

**BOOTSTRAP-287 hoàn tất và được đóng băng.**