# BOOTSTRAP-322 — AXIOM PROFILE-GUIDED OPTIMIZATION, FEEDBACK ENGINE & AUTO-TUNING SYSTEM

Sau 320–321, Axiom đã có:

- pass orchestration,
- adaptive optimization,
- whole-program analysis,
- call graph,
- semantic summaries,
- specialization,
- devirtualization,
- LTO,
- correctness validation.

Nhưng compiler hiện vẫn chủ yếu dựa trên **ước lượng tĩnh**.

Bước tiếp theo là cho compiler học từ **hành vi thực tế của chương trình**:

> **Compiler có thể dùng dữ liệu runtime để biết phần nào thực sự nóng, branch nào thực sự thường xảy ra, allocation nào thực sự tốn chi phí, và từ đó chọn optimization phù hợp hơn.**

Đây là BOOTSTRAP-322.

---

# 322.1. Mục tiêu

Xây dựng pipeline:

```text
Source
   ↓
Static Analysis
   ↓
Initial Compilation
   ↓
Instrumented / Profile Build
   ↓
Program Execution
   ↓
Profile Collection
   ↓
ProfileDB
   ↓
Feedback Analysis
   ↓
Optimization Planner
   ↓
Optimized Compilation
   ↓
Validation
   ↓
Native Binary
```

Mục tiêu không phải biến Axiom thành một ngôn ngữ JIT.

PGO phải hoạt động tốt ngay cả với:

- native executable,
- embedded,
- server,
- desktop,
- CLI,
- GPU workload,
- cross-compilation,
- offline build.

---

# 322.2. Nguyên tắc quan trọng nhất

## Profile không phải semantic fact

Ví dụ profile nói:

```text
foo() được gọi 1.2 tỷ lần
```

đó là:

```text
PerformanceEvidence
```

không phải:

```text
SemanticFact
```

Profile không được phép chứng minh:

```text
NoAlias
NoPanic
NoEscape
Unreachable
Pure
```

Nó chỉ có thể ảnh hưởng đến:

```text
OptimizationDecision
```

---

# 322.3. Profile Model

Định nghĩa:

```text
ProfileRecord {
    program_fingerprint
    compiler_fingerprint
    target_fingerprint

    function_id
    call_site_id
    block_id
    instruction_id

    execution_count
    cycle_count
    sample_count

    branch_counts
    allocation_counts
    deallocation_counts

    synchronization_counts
    cache_metrics
    vector_metrics
}
```

Không phải target nào cũng cung cấp mọi metric.

---

# 322.4. Profile Types

Axiom hỗ trợ nhiều loại profile.

### Instrumentation Profile

Compiler chèn counter:

```text
foo_count++
branch_42++
```

Chính xác hơn nhưng overhead cao hơn.

### Sampling Profile

Profiler lấy sample:

```text
PC → function → source location
```

Overhead thấp.

### Hardware Profile

Dùng performance counters:

- CPU cycles
- branch misses
- cache misses
- instructions
- SIMD utilization
- memory bandwidth

### Allocation Profile

Theo dõi:

- allocation count
- allocation size
- lifetime
- allocator domain

### Lock Profile

Theo dõi:

- lock contention
- wait time
- acquisition count

### Async Profile

Theo dõi:

- task wake
- await latency
- executor queue time
- task migration

### GPU Profile

Theo dõi:

- kernel duration
- occupancy
- memory bandwidth
- transfer time
- synchronization stalls

---

# 322.5. Stable Profile Identity

Profile không được phụ thuộc đơn giản vào:

```text
instruction address
```

vì address thay đổi giữa các build.

Axiom dùng:

```text
StableProfileId
```

được tạo từ:

```text
PackageId
ModuleId
DeclarationId
FunctionId
SourceSpan
CallSiteId
SemanticFingerprint
```

Ví dụ:

```text
foo.axm:42:callsite-7
```

có thể giữ identity qua một số thay đổi machine layout.

---

# 322.6. Profile Fingerprint

Mỗi profile có:

```text
ProfileFingerprint
```

bao gồm:

```text
source semantic fingerprint
compiler semantic version
target
CPU feature assumptions
build profile
instrumentation schema
runtime profile schema
```

Nếu binary đã thay đổi quá nhiều:

```text
ProfileCompatibility = incompatible
```

Compiler không được âm thầm coi profile cũ là chính xác.

---

# 322.7. Profile Compatibility

Có 4 trạng thái:

```text
Exact
Compatible
Stale
Incompatible
```

### Exact

Binary/profile cùng semantic fingerprint.

### Compatible

Source có thay đổi nhỏ nhưng mapping vẫn xác định được.

### Stale

Profile cũ có thể hữu ích nhưng độ tin cậy giảm.

### Incompatible

Không được sử dụng.

---

# 322.8. Profile Confidence

Mỗi profile observation có:

```text
ProfileConfidence {
    sample_count
    coverage
    freshness
    mapping_quality
}
```

Ví dụ:

```text
foo() hotness:
    samples = 10,000,000
    coverage = 97%
    confidence = high
```

Trong khi:

```text
bar():
    samples = 3
    coverage = 2%
    confidence = low
```

Confidence chỉ ảnh hưởng optimization heuristic.

---

# 322.9. Branch Probability

Profile có thể cung cấp:

```text
BranchProfile {
    taken
    not_taken
}
```

Compiler suy ra:

```text
P(branch)
```

để tối ưu:

- block layout
- branch prediction
- code placement
- if-conversion
- outlining
- speculative optimization

Nhưng không được biến branch hiếm thành branch unreachable.

---

# 322.10. Call Frequency

Compiler biết:

```text
foo → bar
```

được gọi:

```text
10
```

hay:

```text
10,000,000
```

Điều này ảnh hưởng:

```text
Inlining
Specialization
Devirtualization
Code placement
Cold outlining
```

---

# 322.11. Hot/Cold Classification

Function/block được phân loại:

```text
Hot
Warm
Normal
Cold
VeryCold
Unknown
```

Đây là performance classification, không phải semantic property.

---

# 322.12. Hot Path Discovery

Ví dụ:

```text
main
 ↓
foo
 ↓
bar
 ↓
loop
```

profile có thể cho thấy:

```text
bar.loop
```

chiếm 87% runtime.

Compiler ưu tiên:

```text
LoopOptimization
Vectorization
Inlining
RegisterOptimization
CodeLayout
```

ở region đó.

---

# 322.13. Cold Code Outlining

Code ít chạy có thể được tách:

```text
hot function
   ├── hot path
   └── cold path
```

thành:

```text
foo.hot
foo.cold
```

Lợi ích:

- instruction cache
- binary locality
- branch prediction
- giảm code pressure

Semantic behavior không thay đổi.

---

# 322.14. PGO-Guided Inlining

Không còn chỉ:

```text
callee_size < threshold
```

mà:

```text
InlineScore =
    call_frequency
    × expected_benefit
    - code_size_cost
    - register_pressure_cost
```

Ví dụ:

```text
bar() = 20 instructions
```

nhưng được gọi:

```text
1 billion lần
```

có thể rất đáng inline.

Ngược lại:

```text
huge_function()
```

được gọi một lần có thể không inline.

---

# 322.15. PGO-Guided Specialization

Nếu runtime profile cho thấy:

```text
generic<T>
```

trong thực tế 99.9% là:

```text
T = i32
```

compiler có thể tạo specialization tối ưu cho `i32`.

Nhưng không được loại bỏ các trường hợp khác nếu chúng vẫn reachable.

---

# 322.16. Speculative Optimization

Axiom có thể hỗ trợ:

```text
if runtime_condition {
    optimized_path
} else {
    generic_path
}
```

Ví dụ:

```text
dynamic type
```

thường là:

```text
ImplA
```

compiler có thể tạo:

```text
if type == ImplA
    fast direct call
else
    dynamic dispatch
```

Điều kiện:

> Guard phải được compiler chứng minh đúng về semantics.

Profile chỉ quyết định **có đáng tạo fast path hay không**.

---

# 322.17. Guard Cost Model

Mỗi speculative optimization tính:

```text
GuardCost
FastPathBenefit
FallbackCost
CodeSizeCost
```

Nếu:

```text
expected_gain > total_cost
```

planner có thể chọn.

---

# 322.18. Allocation Feedback

Profile:

```text
AllocationSite {
    count
    total_bytes
    average_size
    lifetime
    escape_frequency
}
```

Compiler có thể phát hiện:

```text
allocation rất thường xuyên
lifetime rất ngắn
không escape
```

→ ưu tiên:

```text
ScalarReplacement
StackPromotion
ArenaCandidate
AllocationElimination
```

---

# 322.19. Allocator Feedback

Compiler có thể biết:

```text
general_heap
```

đang bị sử dụng nhiều cho object có pattern:

```text
same size
short lifetime
high frequency
```

Từ đó Standard Library/runtime có thể chọn:

```text
Pool
Slab
Arena
ThreadLocalPool
```

Nhưng compiler không tự ý thay đổi allocator semantics nếu allocator domain là observable.

---

# 322.20. Lock Contention Feedback

Ví dụ:

```text
Mutex A
```

có:

```text
10M acquisitions
80% wait
```

Compiler/runtime tooling có thể xác định hotspot.

Thông tin có thể hỗ trợ:

- lock specialization
- sharding
- optimistic path
- lock elision nếu target/semantics cho phép
- scheduler tuning

Không được tự động bỏ synchronization.

---

# 322.21. Async Feedback

Profile:

```text
Task A:
    wake = 10M
    average wait = 2us

Task B:
    wake = 100
```

Compiler/runtime có thể ưu tiên:

```text
FutureInlining
ReadyPathSpecialization
ExecutorScheduling
TaskLocalOptimization
```

---

# 322.22. GPU Feedback

GPU profile:

```text
Kernel:
    occupancy = 42%
    memory bandwidth = 90%
    register usage = high
```

Planner có thể thay đổi:

```text
block size
unrolling
register pressure
kernel fusion
memory layout
```

nhưng chỉ trong target contract.

---

# 322.23. Feedback Loop

Pipeline:

```text
                ┌──────────────┐
                │ Initial Build│
                └──────┬───────┘
                       ↓
                  Execute
                       ↓
                  ProfileDB
                       ↓
                FeedbackAnalyzer
                       ↓
              OptimizationPlanner
                       ↓
                  Recompile
                       ↓
                  Validate
                       ↓
                 New Binary
                       │
                       └──────→ Profile again
```

Có thể lặp nhiều generation.

---

# 322.24. Auto-Tuning

Axiom có thể thử nhiều optimization configurations:

```text
Configuration A
Configuration B
Configuration C
```

đo:

```text
runtime
binary size
memory
startup
energy
```

sau đó chọn configuration phù hợp objective.

Đây là **auto-tuning**, khác với correctness.

---

# 322.25. Auto-Tuning Không Được Tùy Tiện

Không nên brute-force hàng nghìn pipeline.

Có:

```text
TuningBudget {
    max_variants
    max_compile_time
    max_runtime
    max_binary_size
}
```

Ví dụ:

```text
max_variants = 8
```

---

# 322.26. Search Space

Các biến có thể tune:

```text
InliningThreshold
UnrollFactor
VectorWidth
BlockLayout
PrefetchDistance
RegisterPressureThreshold
SpecializationDepth
CodePlacement
```

Nhưng mỗi biến phải có:

```text
legal_range
target_constraints
cost_model
```

---

# 322.27. Multi-Objective Optimization

Không phải lúc nào runtime thấp nhất là mục tiêu duy nhất.

Compiler có thể tối ưu:

```text
Runtime
BinarySize
CompileTime
Memory
Energy
```

Ví dụ objective:

```text
minimize:
    runtime
    binary_size

subject_to:
    compile_time < 2 min
```

Không nên biến kết quả thành một "đánh giá tốt/xấu" cố định; đây là configuration policy của build.

---

# 322.28. Reproducible PGO

PGO có thể làm build không deterministic nếu xử lý sai.

Axiom phải lưu:

```text
ProfileID
ProfileFingerprint
CollectionEnvironment
Target
CompilerVersion
```

và reproducible build phải chỉ rõ:

```text
profile input
```

là một dependency của build.

---

# 322.29. Profile Merge

Nhiều workload:

```text
run A
run B
run C
```

có thể merge:

```text
ProfileMerge
```

nhưng phải xử lý:

- khác binary version
- khác target
- khác workload
- khác CPU feature
- khác input distribution

---

# 322.30. Weighted Profile

Ví dụ:

```text
Production A = 70%
Production B = 20%
Production C = 10%
```

compiler có thể dùng:

```text
WeightedProfile
```

để phản ánh workload thực tế.

---

# 322.31. Profile Poisoning

Profile là dữ liệu external.

Không được tin profile mù quáng.

Ví dụ attacker cung cấp profile giả để ép compiler:

```text
unsafe speculation
```

Điều này không được phép vì profile không có semantic authority.

Profile chỉ có thể:

```text
change optimization preference
```

không thể:

```text
change correctness assumptions
```

---

# 322.32. Profile Security

Profile có thể chứa thông tin nhạy cảm:

- API usage
- branch behavior
- workload frequency
- path information
- function names

Do đó:

```text
ProfileDB
```

phải có provenance và quyền truy cập phù hợp.

Không đưa dữ liệu nhạy cảm vào:

```text
compiler diagnostics
binary metadata
public package interface
```

một cách mặc định.

---

# 322.33. Profile-Aware Cache

Cache key:

```text
OptimizationCacheKey {
    semantic_fingerprint
    target
    optimization_profile
    profile_fingerprint
}
```

Profile khác:

```text
P1 != P2
```

→ không được reuse codegen artifact như thể giống nhau.

---

# 322.34. Profile Aging

Runtime behavior thay đổi theo thời gian.

Profile phải có:

```text
timestamp
generation
age
```

Compiler có thể giảm trọng số profile cũ:

```text
weight = decay(age)
```

nhưng điều này chỉ là planner heuristic.

---

# 322.35. Profile Explainability

AI/compiler UI có thể hỏi:

```text
Why was foo inlined?
```

Compiler trả:

```text
foo:
    call count = 82,100,000
    callee size = 14 instructions
    estimated code growth = 0.8%
    expected speed benefit = high
    profile confidence = high

Decision:
    inline
```

Hoặc:

```text
Why wasn't bar vectorized?
```

```text
Profile:
    loop is hot

Semantic blockers:
    alias proof unavailable

Therefore:
    vectorization rejected
```

Điểm quan trọng:

> Profile có thể làm compiler **ưu tiên** vectorization, nhưng không thể tạo alias proof.

---

# 322.36. Integration với 320

320:

```text
OptimizationPlanner
```

322 cung cấp:

```text
ProfileEvidence
```

Pipeline:

```text
Static Facts
       +
Profile Evidence
       ↓
OptimizationPlanner
       ↓
Candidate
       ↓
Semantic Proof
       ↓
Transformation
       ↓
Translation Validation
```

Thứ tự này phải giữ nguyên.

---

# 322.37. Integration với 321

321 cung cấp:

```text
FunctionSummary
CallGraph
Reachability
```

322 bổ sung:

```text
Hotness
CallFrequency
BranchProbability
RuntimeBehavior
```

Do đó planner có thể quyết định:

```text
hot + small + proven safe
        ↓
inline
```

hoặc:

```text
cold + large
        ↓
outline
```

---

# 322.38. Integration với 318–319

Một optimization cuối cùng vẫn phải đi qua:

```text
Profile
   ↓
Decision
   ↓
PassContract
   ↓
RequiredFacts
   ↓
Transformation
   ↓
Proof
   ↓
TranslationValidation
   ↓
Commit
```

Profile **không bao giờ được phép bỏ qua**:

- verifier
- semantic contract
- ownership checker
- capability checker
- effect checker
- concurrency checker
- ABI checker

---

# 322.39. ProfileDB

Thêm:

```text
ProfileDB
```

vào CompilerDB:

```text
CompilerDB
 ├── SourceDB
 ├── TypeDB
 ├── TraitDB
 ├── HIRDB
 ├── MIRDB
 ├── CorrectnessDB
 ├── PassDB
 ├── OptimizationDB
 ├── ProgramDB
 ├── SummaryDB
 ├── ReachabilityDB
 └── ProfileDB
```

---

# 322.40. API

```text
collect_profile()
```

```text
load_profile()
```

```text
merge_profiles()
```

```text
validate_profile()
```

```text
check_profile_compatibility()
```

```text
query_hotness()
```

```text
query_branch_probability()
```

```text
query_call_frequency()
```

```text
query_allocation_profile()
```

```text
query_lock_profile()
```

```text
query_async_profile()
```

```text
query_gpu_profile()
```

```text
compute_feedback()
```

```text
run_auto_tuning()
```

```text
explain_profile_decision()
```

```text
export_profile()
```

```text
import_profile()
```

---

# 322.41. Implementation Tree

```text
compiler/profile/
├── model/
│   ├── profile.ax
│   ├── record.ax
│   ├── identity.ax
│   └── fingerprint.ax
│
├── collect/
│   ├── instrumentation.ax
│   ├── sampling.ax
│   ├── hardware.ax
│   ├── allocation.ax
│   ├── synchronization.ax
│   ├── async.ax
│   └── gpu.ax
│
├── compatibility/
│   ├── matcher.ax
│   ├── migration.ax
│   └── aging.ax
│
├── analysis/
│   ├── hotness.ax
│   ├── branch.ax
│   ├── call.ax
│   ├── allocation.ax
│   ├── cache.ax
│   └── contention.ax
│
├── feedback/
│   ├── feedback.ax
│   ├── weighted.ax
│   └── confidence.ax
│
├── tuning/
│   ├── search.ax
│   ├── budget.ax
│   ├── candidate.ax
│   └── objective.ax
│
├── security/
│   ├── provenance.ax
│   ├── privacy.ax
│   └── poisoning.ax
│
└── database/
    └── profile_db.ax
```

---

# 322.42. Invariants

```text
APGO-20  Profile data is never a semantic proof.

APGO-21  Profile data may influence optimization decisions only.

APGO-22  Invalid or incompatible profiles cannot be consumed as valid feedback.

APGO-23  Profile identity must not depend solely on machine addresses.

APGO-24  Profile records have provenance.

APGO-25  Profile fingerprints participate in cache identity.

APGO-26  Stale profiles must be explicitly classified.

APGO-27  Profile confidence affects heuristics, never semantic legality.

APGO-28  Speculative optimization requires semantic guards.

APGO-29  A failed speculation must preserve the original semantics.

APGO-30  Profile-guided optimization cannot bypass PassContract.

APGO-31  Profile-guided optimization cannot bypass TranslationValidation.

APGO-32  Profile merging must respect compatibility constraints.

APGO-33  Auto-tuning operates only inside explicit resource budgets.

APGO-34  Auto-tuning cannot select semantically invalid configurations.

APGO-35  Reproducible builds record profile dependencies.

APGO-36  Profile poisoning cannot create new semantic permissions.

APGO-37  Profile-sensitive code generation is fingerprinted.

APGO-38  Profile data must not silently leak sensitive workload information.

APGO-39  Hardware-specific feedback cannot redefine language semantics.

APGO-40  GPU feedback obeys GPU legality contracts.

APGO-41  Async feedback cannot alter cancellation semantics.

APGO-42  Synchronization feedback cannot remove required synchronization.

APGO-43  Optimization remains valid when profile data is absent.

APGO-44  Incorrect profile data may reduce performance but must not make the program semantically invalid.
```

---

# 322.43. Definition of Done

BOOTSTRAP-322 hoàn thành khi:

1. Có `ProfileDB`.
2. Có stable profile identity.
3. Có profile fingerprint.
4. Có compatibility checker.
5. Có instrumentation profiling.
6. Có sampling profiling.
7. Có hardware-counter profiling.
8. Có branch profiling.
9. Có call-frequency profiling.
10. Có allocation profiling.
11. Có synchronization profiling.
12. Có async profiling.
13. Có GPU profiling.
14. Có hot/cold classification.
15. Có profile-guided inlining.
16. Có profile-guided specialization.
17. Có guarded speculative optimization.
18. Có allocation feedback.
19. Có code-layout feedback.
20. Có PGO-aware LTO.
21. Có profile merge.
22. Có profile aging.
23. Có profile security/provenance.
24. Có auto-tuning framework.
25. Có tuning budget.
26. Có deterministic/reproducible profile mode.
27. Có profile-aware optimization cache.
28. Có AI explanation API.
29. Có test chứng minh profile sai không thể tạo semantic bug.
30. Có end-to-end:

```text
Initial Build
      ↓
Profile Collection
      ↓
ProfileDB
      ↓
Compatibility Check
      ↓
Feedback Analysis
      ↓
Optimization Planner
      ↓
Semantic Proof
      ↓
Transformation
      ↓
Translation Validation
      ↓
Optimized Native Binary
```

---

## Nguyên tắc đóng băng của 322

> **Runtime feedback được phép nói với compiler “hãy tối ưu phần này trước”, nhưng tuyệt đối không được nói “hãy coi điều này là đúng”.**

Như vậy kiến trúc Axiom hiện có một đường rất rõ:

```text
318  Semantic Equivalence
        ↓
319  Pass Contracts & Proofs
        ↓
320  Adaptive Optimization Planner
        ↓
321  Whole-Program Reasoning
        ↓
322  Runtime Feedback / PGO / Auto-Tuning
```

Compiler có thể ngày càng **thông minh và tự thích nghi**, nhưng semantic authority vẫn nằm ở **AXSpec + verifier + reference semantics**, không nằm ở heuristic hay dữ liệu runtime.