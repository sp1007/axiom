# BOOTSTRAP-553 — COMPILER OPTIMIZATION FRAMEWORK 2.0, PASS MANAGER, COST MODEL, PGO, LTO, AUTOVECTORIZATION & WHOLE-PROGRAM OPTIMIZATION

**Trạng thái: COMPLETED / LOCKED**

`553` là tầng tối ưu hóa trung tâm của compiler. Mục tiêu là đạt hiệu năng native rất cao nhưng vẫn giữ các nguyên tắc đã khóa ở `423`, `430`, `437`, `438`, `450`, `476`, `479`, `552`.

Nguyên tắc cốt lõi:

> **Optimizer được phép rất aggressive, nhưng mọi transformation phải có semantic precondition, cost rationale và validation boundary rõ ràng.**

---

## 553.1. Optimization architecture

```text
                         Program
                            │
                            ▼
                           HIR
                            │
                            ▼
                           MIR
                            │
                  ┌─────────┴─────────┐
                  │                   │
              Analyses             Profiles
                  │                   │
                  └─────────┬─────────┘
                            ▼
                    Optimization Manager
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   Scalar Passes       Memory Passes       Loop Passes
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    Interprocedural
                            │
                    ┌───────┴───────┐
                    ▼               ▼
                  LTO              PGO
                    │               │
                    └───────┬───────┘
                            ▼
                     Target Optimization
                            │
                            ▼
                          LIR
                            │
                            ▼
                       Machine IR
```

---

# 553.2. Optimization ≠ code generation

Tách:

```text
Semantic Optimization
        ↓
MIR Optimization
        ↓
LIR Optimization
        ↓
Machine Optimization
```

Không để target-specific instruction details làm bẩn semantic optimizer.

---

# 553.3. Pass abstraction

Mỗi optimization pass có:

```text
Pass {
    id
    version
    required_analyses
    preserved_analyses
    invalidated_analyses
    transformation_kind
    cost_model
    validation_level
}
```

---

# 553.4. Analysis abstraction

Analysis:

```text
Analysis {
    id
    version
    input_ir
    dependencies
    result
}
```

Ví dụ:

```text
DominatorTree
LoopInfo
AliasInfo
RangeInfo
EscapeInfo
CallGraph
ProfileInfo
TargetInfo
```

---

# 553.5. Analysis invalidation

Pass phải khai báo analysis nào bị invalid.

Ví dụ:

```text
CFG simplification
→ invalidates DominatorTree
→ invalidates LoopInfo
```

Compiler không được dùng analysis cũ như thể vẫn còn đúng.

---

# 553.6. Preservation contract

Pass có thể nói:

```text
preserves:
    TypeInfo
    AliasInfo
```

nhưng không được tự ý khai báo preservation nếu transformation làm thay đổi assumptions.

---

# 553.7. Pass pipeline

Pipeline không hard-code toàn bộ.

Có thể biểu diễn:

```text
Pipeline {
    passes[]
    target
    optimization_level
    size_policy
    numeric_policy
    profile_policy
}
```

---

# 553.8. Optimization levels

Axiom định nghĩa semantics của level, không nhất thiết copy GCC/LLVM:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
```

Các level là **policy presets**, không phải semantic modes.

---

# 553.9. Semantic equivalence across levels

```text
-O0
-O1
-O2
-O3
```

phải bảo toàn cùng language semantics, ngoại trừ behavior vốn thuộc UB/unspecified contract.

---

# 553.10. Debug optimization

Debug build có thể optimize nhưng phải giữ debug mapping tốt nhất có thể.

```text
-O0 -g
-O1 -g
-O2 -g
```

đều hợp lệ.

---

# 553.11. Size optimization

`-Os` tối ưu code size với correctness không đổi.

`-Oz` có thể ưu tiên size mạnh hơn nữa.

---

# 553.12. Cost model

Mỗi transformation nên ước lượng:

```text
Cost {
    instruction_count
    latency
    throughput
    code_size
    register_pressure
    memory_traffic
    branch_cost
    compile_cost
}
```

---

# 553.13. Cost model không phải guarantee

Cost model chỉ là heuristic.

Không được biến:

```text
estimated faster
```

thành:

```text
guaranteed faster
```

---

# 553.14. Target-aware cost model

Cost phụ thuộc:

```text
CPU
ISA
microarchitecture profile
cache model
SIMD width
register count
instruction latency
```

---

# 553.15. Target feature set

Optimization context:

```text
TargetFeatures {
    architecture
    isa_extensions
    vector_widths
    atomic_features
    floating_features
}
```

---

# 553.16. CPU feature specialization

Compiler có thể tạo:

```text
generic implementation
SSE/AVX implementation
AVX2 implementation
AVX-512 implementation
```

nếu project cho phép multiversioning.

---

# 553.17. Runtime dispatch

Dispatch:

```text
CPU features
    ↓
feature selector
    ↓
specialized implementation
```

Không được sử dụng instruction không được target hỗ trợ.

---

# 553.18. Compile-time target specialization

`comptime` có thể chọn target-specific code:

```text
comptime if target.features.avx2 {
    ...
}
```

nhưng semantics phải rõ ràng.

---

# 553.19. Scalar optimization

Core scalar passes:

```text
constant folding
constant propagation
copy propagation
dead code elimination
dead store elimination
CSE
GVN
PRE
SCCP
CFG simplification
jump threading
value numbering
```

---

# 553.20. Sparse conditional constant propagation

SCCP có thể đồng thời reason:

```text
value lattice
reachable blocks
constant branches
```

---

# 553.21. Algebraic simplification

Ví dụ:

```text
x + 0 → x
x * 1 → x
```

chỉ hợp lệ theo type/numeric semantics.

Không áp dụng mù quáng cho floating-point hoặc overflow-sensitive operations.

---

# 553.22. Integer simplification

Optimizer phải biết distinction:

```text
checked
wrapping
saturating
```

---

# 553.23. Floating-point simplification

Strict FP phải preserve:

```text
NaN
signed zero
rounding
exception behavior where specified
```

---

# 553.24. Fast-math

Fast numeric mode có thể cho phép:

```text
reassociation
approximation
contraction
reciprocal transforms
```

chỉ khi policy cho phép.

---

# 553.25. CSE

Common subexpression elimination dựa trên purity/effects.

Không coi mọi function call là pure.

---

# 553.26. GVN

Global value numbering phải respect:

```text
memory dependencies
volatile
atomic
calls
aliasing
```

---

# 553.27. PRE

Partial redundancy elimination phải preserve evaluation order và side effects.

---

# 553.28. DCE

Dead code elimination tích hợp `552`.

Instruction được loại bỏ phải chứng minh không có observable effect.

---

# 553.29. Dead store elimination

Store chỉ được xóa nếu memory semantics cho phép.

---

# 553.30. CFG simplification

Các transformation:

```text
block merging
empty block elimination
branch folding
unreachable block removal
jump threading
```

---

# 553.31. Dominator infrastructure

Compiler cung cấp:

```text
DominatorTree
PostDominatorTree
DominanceFrontier
```

cho SSA/optimization.

---

# 553.32. SSA construction

MIR sử dụng SSA cho virtual values khi phù hợp.

```text
x1
x2
φ(x1,x2)
```

---

# 553.33. SSA destruction

Trước machine lowering:

```text
SSA
 ↓
parallel copies
 ↓
register allocation
```

---

# 553.34. Memory SSA

Memory operations có dependency graph:

```text
MemoryDef
MemoryUse
MemoryPhi
```

giúp memory optimization mạnh nhưng có kiểm soát.

---

# 553.35. Alias analysis

Các mức:

```text
NoAlias
MayAlias
MustAlias
Unknown
```

`Unknown` không được biến thành `NoAlias`.

---

# 553.36. Alias analysis sources

Evidence từ:

- type/layout;
- ownership;
- allocation identity;
- explicit contract;
- range analysis;
- escape analysis;
- FFI annotations.

---

# 553.37. Escape analysis

Phân loại:

```text
NoEscape
FunctionEscape
ThreadEscape
GlobalEscape
Unknown
```

---

# 553.38. Stack promotion

Nếu allocation:

```text
NoEscape
```

có thể promote từ heap → stack.

---

# 553.39. Allocation elimination

Nếu object chỉ tồn tại để truyền giữa local operations, compiler có thể eliminate physical allocation.

---

# 553.40. Scalar replacement

Aggregate có thể được phân rã thành SSA values.

---

# 553.41. Object identity boundary

Không được scalar-replace nếu physical identity observable.

---

# 553.42. Load/store forwarding

Store:

```text
*p = x
```

followed by:

```text
load(*p)
```

có thể forward `x` nếu no intervening invalidating effect.

---

# 553.43. Redundant load elimination

Chỉ khi alias/memory state đủ chắc chắn.

---

# 553.44. Memory coalescing

Adjacent loads/stores có thể combine nếu:

```text
alignment
endianness
volatile
atomicity
aliasing
```

cho phép.

---

# 553.45. Loop optimization framework

Loop passes:

```text
loop-invariant-code-motion
induction-variable
strength-reduction
unrolling
peeling
unswitching
fusion
fission
interchange
distribution
vectorization
```

---

# 553.46. Loop canonicalization

Chuẩn hóa:

```text
header
preheader
latch
exit
induction variables
```

để các pass khác dễ reason.

---

# 553.47. LICM

Loop-invariant computation có thể đưa ra ngoài loop nếu:

- pure;
- no trapping/panic semantic change;
- memory safe;
- dependencies stable.

---

# 553.48. Induction variable optimization

Ví dụ:

```text
i * 4
```

có thể lower thành increment nếu overflow semantics vẫn tương đương.

---

# 553.49. Strength reduction

Không áp dụng transformation số học nếu checked overflow có thể thay đổi behavior.

---

# 553.50. Loop unrolling

Unroll factor dựa trên:

```text
trip count
code size
register pressure
branch cost
profile
target
```

---

# 553.51. Full unrolling

Chỉ dùng khi trip count compile-time bounded và cost hợp lý.

---

# 553.52. Partial unrolling

Cho loop lớn/unknown trip count:

```text
main loop
remainder loop
```

---

# 553.53. Loop peeling

Peel iterations để expose alignment/bounds/vectorization opportunities.

---

# 553.54. Loop unswitching

Move invariant branch outside loop:

```text
if condition {
    loop A
} else {
    loop B
}
```

chỉ khi code-size/runtime tradeoff hợp lý.

---

# 553.55. Loop fusion

Hai loop:

```text
for ...
for ...
```

có thể merge nếu dependencies cho phép.

---

# 553.56. Loop fission

Một loop có thể split nếu cải thiện locality/vectorization và semantics được giữ.

---

# 553.57. Loop interchange

Cho nested loops, có thể đổi thứ tự nếu dependency hợp lệ.

---

# 553.58. Loop distribution

Tách statements để vectorize/localize tốt hơn.

---

# 553.59. Dependence analysis

Loop transformation cần:

```text
RAW
WAR
WAW
reduction
memory dependence
```

---

# 553.60. Reduction recognition

Nhận diện:

```text
sum
min
max
dot product
```

và vectorize khi numeric policy cho phép.

---

# 553.61. Autovectorization

Pipeline:

```text
Loop
 ↓
Dependence Analysis
 ↓
Memory/Alignment Analysis
 ↓
Cost Model
 ↓
Vector Plan
 ↓
Vector MIR
 ↓
Validation
```

---

# 553.62. Vector width

Compiler chọn width dựa trên target:

```text
scalar
128-bit
256-bit
512-bit
```

hoặc architecture tương ứng.

---

# 553.63. Vectorization legality

Phải kiểm tra:

```text
dependency
alias
alignment
trip count
masking
remainder
numeric semantics
```

---

# 553.64. Runtime alias checks

Nếu static proof không đủ, compiler có thể generate:

```text
if non_alias {
    vector_loop
} else {
    scalar_loop
}
```

---

# 553.65. Runtime bounds guards

Dynamic shape/range có thể dùng guard:

```text
if condition {
    optimized path
} else {
    fallback
}
```

---

# 553.66. Vector remainder

Hỗ trợ:

```text
masked tail
scalar epilogue
vector epilogue
```

theo target.

---

# 553.67. SIMD abstraction

Compiler và library dùng chung semantic vector model từ `458`.

---

# 553.68. SIMD intrinsics

Target-specific intrinsic:

```text
unsafe / target-feature constrained
```

và không được masquerade như portable operation.

---

# 553.69. Horizontal reductions

Vector reduction phải respect floating-point numeric policy.

---

# 553.70. Gather/scatter

Chỉ generate khi:

```text
target supports
cost model approves
memory semantics valid
```

---

# 553.71. Software pipelining

Có thể hỗ trợ ở machine optimization stage cho targets phù hợp.

---

# 553.72. Function optimization

Core function passes:

```text
inlining
outlining
specialization
cloning
devirtualization
constant argument propagation
dead argument elimination
```

---

# 553.73. Inlining model

Cost model xem:

```text
call overhead
callee size
caller size
hotness
code size
register pressure
recursion
```

---

# 553.74. Hot inlining

PGO hot callsites có thể được ưu tiên inline.

---

# 553.75. Cold inlining

Cold callsite thường tránh inline để giảm binary size.

---

# 553.76. Recursive inlining

Giới hạn depth và code-size budget.

---

# 553.77. Function cloning

Clone function khi known constant/profile facts giúp tối ưu mạnh.

---

# 553.78. Specialization

Ví dụ:

```text
fn process<T>(...)
```

có thể specialize theo concrete type/const argument.

---

# 553.79. Generic specialization control

Tránh code bloat bằng:

```text
instance sharing
specialization threshold
outlining
linker dedup
```

---

# 553.80. Devirtualization

`dyn Trait` call có thể chuyển thành direct call nếu concrete target được chứng minh.

---

# 553.81. Whole-program devirtualization

Chỉ trong closed-world build.

Open-world library build không được assume toàn bộ implementation set.

---

# 553.82. Interprocedural analysis

Các analysis:

```text
call graph
effect propagation
constant propagation
escape propagation
purity
no-panic
no-alloc
no-block
```

---

# 553.83. SCC analysis

Call graph strongly connected components giúp xử lý recursion/mutual recursion.

---

# 553.84. Interprocedural constant propagation

Function:

```text
f(42)
```

có thể specialize/propagate constant nếu cost hợp lý.

---

# 553.85. Effect-aware optimization

Compiler dùng metadata:

```text
@no_alloc
@no_block
@no_panic
```

nhưng phải phân biệt:

```text
declared
verified
inferred
unknown
```

---

# 553.86. Pure function optimization

Pure function có thể CSE/cache/fold nếu arguments tương đương.

---

# 553.87. Side-effect barrier

Các effect:

```text
IO
volatile
atomic
external call
unknown FFI
```

được xem là optimization barriers tùy contract.

---

# 553.88. LTO architecture

```text
Package/Object
      ↓
Semantic Metadata
      ↓
Merged IR Index
      ↓
Cross-module Analysis
      ↓
LTO Optimization
      ↓
Machine Code
```

---

# 553.89. Full LTO

Toàn bộ reachable program được đưa vào optimization graph.

---

# 553.90. Thin LTO-like mode

Có thể tối ưu incremental:

```text
summary
+
selective body import
```

để giảm compile time.

---

# 553.91. LTO summaries

Mỗi function có summary:

```text
size
effects
hotness
calls
allocations
alias properties
constants
```

---

# 553.92. Incremental LTO

Không invalidate toàn bộ program khi một function nhỏ thay đổi nếu dependency graph cho phép.

---

# 553.93. Link-time dead stripping

Unreachable code có thể bị loại bỏ.

Liên kết với linker GC `420`.

---

# 553.94. COMDAT / dedup

Identical or semantically mergeable code có thể deduplicate nếu ABI/ODR-like conditions hợp lệ.

---

# 553.95. PGO architecture

```text
Build Instrumented
       ↓
Run Workload
       ↓
Profile Artifact
       ↓
Validate Profile
       ↓
Merge Profiles
       ↓
Optimize Build
```

---

# 553.96. Profile identity

Profile:

```text
Profile {
    program_hash
    compiler_build
    target
    features
    workload_id
    config
    timestamp_range
}
```

---

# 553.97. Profile staleness

Profile phải có:

```text
Fresh
Compatible
Stale
Incompatible
Unknown
```

---

# 553.98. Profile mismatch

Nếu source semantic hash thay đổi lớn:

```text
profile = incompatible
```

không silently reuse.

---

# 553.99. Profile merging

Nhiều workloads:

```text
profile A
profile B
profile C
```

có thể merge nếu schema/target compatibility hợp lệ.

---

# 553.100. Profile weighting

Weights phải được khai báo.

Không mặc định workload A quan trọng hơn B nếu project chưa cấu hình.

---

# 553.101. Hotness

Profile cung cấp:

```text
function hotness
block hotness
edge frequency
callsite frequency
branch probability
```

---

# 553.102. Branch prediction optimization

Compiler có thể layout:

```text
hot path
cold path
```

dựa trên profile.

---

# 553.103. Hot/cold splitting

Cold code có thể tách khỏi hot path để giảm instruction-cache pressure.

---

# 553.104. Function layout

PGO có thể tối ưu:

```text
function ordering
basic-block ordering
```

---

# 553.105. Code layout

Mục tiêu:

```text
I-cache locality
branch locality
page locality
```

---

# 553.106. PGO + inlining

Hot callsites ưu tiên inline; cold large callees thường giữ outline.

---

# 553.107. PGO + vectorization

Loop hot có thể nhận vectorization budget cao hơn.

---

# 553.108. PGO + specialization

Hot type/branch distributions có thể trigger specialization.

---

# 553.109. PGO uncertainty

Profile sample không phải truth tuyệt đối.

Compiler ghi:

```text
confidence
sample_count
collection_method
```

---

# 553.110. Profile-guided deoptimization

Axiom **không bắt buộc JIT deoptimization**.

Native AOT optimization có thể generate guarded specialized paths + fallback.

---

# 553.111. Guarded specialization

```text
runtime condition
       │
   ┌───┴───┐
   ↓       ↓
 fast     generic
```

---

# 553.112. Feedback-directed optimization

Có thể dùng runtime profile để compile lại binary, nhưng đây là build/deployment feature, không phải hidden runtime.

---

# 553.113. Optimization cache

Cache key:

```text
OptimizationKey {
    semantic_hash
    compiler_build
    target
    features
    optimization_level
    numeric_policy
    profile_hash
}
```

---

# 553.114. Cache correctness

Optimization cache hit phải produce semantics equivalent với clean compilation.

---

# 553.115. Cache invalidation

Invalidate khi thay đổi:

```text
language semantics
type rules
ABI
target
optimization pass version
numeric policy
profile
```

---

# 553.116. Deterministic optimization

Cùng:

```text source
compiler
target
config
profile
```

phải tạo cùng semantic result.

---

# 553.117. Parallel optimization

Passes có thể chạy song song nếu dependencies không xung đột.

---

# 553.118. Deterministic parallelism

Parallel execution không được làm optimization result phụ thuộc thread scheduling.

---

# 553.119. Optimization budget

Mỗi compilation có:

```text
compile_time_budget
memory_budget
code_size_budget
optimization_iteration_budget
```

---

# 553.120. Optimization termination

Optimization pipeline phải có termination guarantee thực dụng:

```text
pass iteration limit
fixed-point detection
cost threshold
```

---

# 553.121. Fixed-point optimization

Pass group:

```text
canonicalize
→ simplify
→ DCE
```

có thể lặp tới fixed point.

---

# 553.122. Oscillation prevention

Nếu transformations tạo vòng:

```text
A → B → A
```

manager phải detect.

---

# 553.123. Profitability gate

Transformation chỉ thực hiện khi:

```text
Legal == true
```

và:

```text
Profitability == acceptable
```

---

# 553.124. Legality before profitability

Không được chọn transformation vì nhanh hơn nếu nó không semantic-safe.

---

# 553.125. Compile-time tradeoff

Một optimization chỉ tăng runtime 0.5% nhưng mất rất nhiều compile time có thể bị bỏ theo policy.

---

# 553.126. Code-size tradeoff

Compiler có thể chấp nhận runtime gain nếu code-size budget cho phép.

---

# 553.127. Multi-objective cost model

Cost model có vector:

```text
runtime
size
compile_time
memory
```

thay vì một universal score.

---

# 553.128. No universal optimization score

Compiler không xuất:

```text
optimization_score = 93
```

---

# 553.129. Policy-specific objective

Project có thể chọn:

```text
runtime-first
size-first
compile-time-first
balanced
```

---

# 553.130. Explainability

Mỗi important transformation có thể ghi:

```text
OptimizationDecision {
    pass
    location
    legality
    profitability
    evidence
    assumptions
}
```

---

# 553.131. Why optimized

AI/tooling query:

```text
why_optimized(symbol, region)
```

---

# 553.132. Why not optimized

Ví dụ:

```text
why_not_vectorized(loop)
```

trả:

```text
UnknownAlias
```

hoặc:

```text
TripCountTooSmall
```

hoặc:

```text
NumericPolicyStrict
```

---

# 553.133. No speculative explanation

Optimizer explanation phải lấy từ recorded evidence, không để AI tự suy diễn.

---

# 553.134. Missed optimization classification

```text
NotApplicable
Illegal
Unprofitable
InsufficientInformation
BudgetExceeded
UnsupportedTarget
DisabledByPolicy
Unknown
```

---

# 553.135. Optimization remarks

Compiler có thể xuất:

```text
optimization remarks
missed optimization remarks
analysis remarks
```

---

# 553.136. Source-level correlation

Remark:

```text
source
→ HIR
→ MIR
→ optimization
→ machine code
```

---

# 553.137. Assembly correlation

Tooling cho phép xem:

```text
source line
→ MIR instructions
→ machine instructions
```

kết hợp `440`, `476`.

---

# 553.138. Performance feedback loop

```text
Benchmark
 ↓
Profile
 ↓
Optimization
 ↓
Build
 ↓
Benchmark
 ↓
Compare
```

Không tự động tuyên bố optimization thành công nếu benchmark không chứng minh.

---

# 553.139. PGO benchmark integration

PGO workload phải có identity/provenance.

---

# 553.140. PGO poisoning defense

Profile artifact phải được verify hash/source/target compatibility.

Profile không đáng tin không được âm thầm ảnh hưởng security-sensitive optimization.

---

# 553.141. Security-sensitive optimization

Compiler phải cho phép policy disable transformations như:

```text
unsafe speculation
secret-dependent optimization
non-constant-time transformations
```

khi contract yêu cầu.

---

# 553.142. Constant-time interaction

Nếu function có:

```text
@constant_time
```

optimizer phải respect security constraints.

---

# 553.143. Speculation control

Target-specific speculative transforms phải respect security profile.

---

# 553.144. Sanitizer interaction

Sanitizer build có optimization policy riêng.

Không assume sanitizer instrumentation preserves exact production performance.

---

# 553.145. Debug interaction

Optimization có thể làm variable unavailable.

Debug metadata phải phản ánh trạng thái thực tế.

---

# 553.146. Exception/panic interaction

Optimization phải preserve:

```text
panic points
cleanup
unwind edges
```

khi observable.

---

# 553.147. Contract interaction

Proven contract có thể unlock optimization.

Runtime-checked contract chỉ cho phép optimization sau check hoặc guarded path.

---

# 553.148. Assume interaction

`assume` có thể cung cấp optimizer fact nhưng thuộc unsafe contract.

---

# 553.149. Ownership interaction

Move/drop semantics không được phá bởi optimization.

---

# 553.150. Drop elimination

Destructor chỉ được eliminate nếu compiler chứng minh resource destruction không observable trong context.

---

# 553.151. FFI boundary

Unknown foreign effects là conservative barrier.

---

# 553.152. FFI pure contract

Nếu foreign function có explicit verified/policy contract:

```text
@pure
@no_alloc
@no_block
```

optimizer có thể tận dụng trong phạm vi contract.

---

# 553.153. Async optimization

Async state machines có thể:

```text
remove states
merge states
eliminate allocations
inline futures
```

nếu semantics preserved.

---

# 553.154. Future allocation elimination

Nếu Future không escape:

```text
heap state
→ stack/register state
```

có thể thực hiện.

---

# 553.155. Actor optimization

Message passing không được optimize thành shared memory nếu observable semantics thay đổi.

---

# 553.156. Reactive optimization

Có thể fuse pure operators:

```text
map
→ filter
→ map
```

nhưng effect ordering phải giữ.

---

# 553.157. Workflow optimization

Pure workflow nodes có thể constant-fold/cache.

Irreversible side-effect nodes không được duplicate/eliminate tùy tiện.

---

# 553.158. Tensor graph optimization

`504` graph optimizer có thể dùng chung:

```text
cost model
alias analysis
memory planner
fusion framework
```

nhưng Tensor semantics vẫn giữ riêng.

---

# 553.159. GPU optimization

GPU backend có optimization pipeline riêng nhưng dùng common pass infrastructure khi abstraction phù hợp.

---

# 553.160. Cross-device optimization

Transfer elimination:

```text
CPU → GPU → CPU
```

chỉ được eliminate khi value/device/effect semantics cho phép.

---

# 553.161. Memory locality

Compiler có thể optimize:

```text
layout
prefetch
tiling
blocking
```

khi representation contract cho phép.

---

# 553.162. Prefetch

Software prefetch chỉ là optimization hint.

Không được xem là correctness requirement.

---

# 553.163. Cache-aware optimization

Cost model có thể sử dụng cache model nhưng phải ghi đây là heuristic.

---

# 553.164. NUMA optimization

Profile/runtime metadata có thể hỗ trợ locality.

Không assume NUMA topology cố định nếu target/runtime không đảm bảo.

---

# 553.165. Parallelization

Compiler có thể tự động parallelize **chỉ khi policy cho phép** và semantics xác định.

Axiom không tự động tạo threads trong ordinary code.

---

# 553.166. Explicit parallel constructs

`parallel_for`/task APIs từ `471` là preferred mechanism.

---

# 553.167. Auto-parallelization

Nếu bật:

```text
@parallelizable
```

compiler phải có legality proof về dependency/race semantics.

---

# 553.168. Reproducibility

Parallel floating-point reduction có thể thay đổi rounding.

Strict deterministic policy phải disable hoặc constrain transformation.

---

# 553.169. Vector + parallel interaction

Compiler có thể:

```text
parallel outer loop
vectorize inner loop
```

khi cost/dependency hợp lệ.

---

# 553.170. Register pressure

Cost model phải tính:

```text
live values
register classes
spill cost
```

---

# 553.171. Spill-aware optimization

Một transformation tăng arithmetic efficiency nhưng tạo nhiều spills có thể bị từ chối.

---

# 553.172. Machine-aware late optimization

Machine IR stage xử lý:

```text
peephole
instruction combining
copy coalescing
branch optimization
machine scheduling
```

---

# 553.173. Instruction combining

Ví dụ:

```text
compare
+
branch
```

→ target-specific fused instruction nếu semantics hợp lệ.

---

# 553.174. Address-mode folding

Separate arithmetic:

```text
base + index * scale
```

có thể fold vào target addressing mode.

---

# 553.175. Immediate folding

Constant operations có thể fold vào instruction immediate nếu range hợp lệ.

---

# 553.176. Copy coalescing

Virtual register copies được loại bỏ trước/đồng thời register allocation.

---

# 553.177. Register allocation feedback

Optimizer nhận:

```text
register pressure
spill estimates
```

để retry transformation.

---

# 553.178. Late vectorization

Một số target-specific vectorization có thể diễn ra sau generic vectorization.

Không duplicate incompatible transformations.

---

# 553.179. Optimization pipeline planning

Compiler chọn pipeline dựa trên:

```text
target
optimization level
size policy
profile
language contracts
build mode
```

---

# 553.180. Pass dependency graph

Pass manager xây DAG:

```text
AliasAnalysis
    ↓
LICM
    ↓
Vectorization
    ↓
Unrolling
```

---

# 553.181. Pass scheduling

Không chạy pass chỉ vì có trong danh sách.

Pass chỉ chạy nếu prerequisites satisfied.

---

# 553.182. Analysis reuse

Nếu analysis còn valid, reuse cache.

Nếu invalidated, recompute.

---

# 553.183. Parallel analysis

Independent analyses có thể chạy song song.

---

# 553.184. Optimization snapshots

Có thể lưu:

```text
MIR_before
MIR_after
```

cho debugging/forensics.

Không bật full snapshot mặc định cho production nếu binary/compile cost lớn.

---

# 553.185. Optimization debugging

Developer có thể:

```text
-stop-after=pass
-run-only=pass
-disable=pass
```

---

# 553.186. Optimization bisect integration

`552` có thể tự động tìm pass gây regression.

---

# 553.187. Pass verifier

Sau mỗi critical pass:

```text
IR
 ↓
Verifier
```

---

# 553.188. Lightweight vs deep verification

Developer build:

```text
light verifier
```

CI/nightly:

```text
deep translation validation
```

---

# 553.189. Proof-producing optimization

Critical passes có thể emit proof/evidence.

Không yêu cầu toàn bộ optimizer phải formalized.

---

# 553.190. Optimization correctness boundary

Mỗi pass phải thuộc một trong:

```text
Verified
Validated
Tested
Experimental
Disabled
```

---

# 553.191. Experimental pass

Experimental optimization không được silently enable trong stable production profile.

---

# 553.192. Pass quarantine

Nếu pass phát hiện miscompilation:

```text
Pass
 ↓
Quarantine
 ↓
Regression corpus
 ↓
Fix
 ↓
Revalidation
 ↓
Re-enable
```

---

# 553.193. Optimization regression

Phân biệt:

```text
wrong code
performance regression
code-size regression
compile-time regression
memory regression
```

---

# 553.194. Performance regression evidence

Không coi benchmark variance là compiler bug.

Phải có:

```text
baseline
repeated measurements
environment
workload identity
confidence/variance
```

theo `450/481`.

---

# 553.195. Optimization report

```text
OptimizationReport {
    source
    target
    profile
    passes
    transformations
    missed
    code_size_delta
    compile_time
    validation
}
```

---

# 553.196. AI optimization API

AI có thể query:

```text
optimization_pipeline()
why_optimized()
why_not_optimized()
show_hot_paths()
show_vectorization()
show_inlining()
show_alias_assumptions()
show_register_pressure()
show_code_size()
show_profile_usage()
```

---

# 553.197. AI cannot fabricate optimization reasons

Mọi explanation phải liên kết evidence.

Nếu evidence không tồn tại:

```text
Unknown
```

---

# 553.198. Optimization artifact identity

Optimized artifact phải record:

```text
compiler
target
features
optimization_level
optimization_pipeline_hash
profile_hash?
numeric_policy
security_policy
```

---

# 553.199. Final optimization contract

Axiom optimizer phải đạt:

```text
Semantic correctness
        +
Aggressive transformation
        +
Target awareness
        +
Profile awareness
        +
Cost awareness
        +
Determinism
        +
Explainability
        +
Validation
```

mà không biến optimization thành hidden runtime behavior.

---

# 553.200. Hard invariants

`BOOTSTRAP-553` khóa tối thiểu các invariant sau:

1. Optimization không thay đổi defined language semantics.
2. Mọi pass có stable identity.
3. Mọi pass có version.
4. Pass khai báo analysis dependencies.
5. Pass khai báo invalidation.
6. Analysis có identity/version.
7. Không sử dụng stale analysis.
8. Legality được kiểm tra trước profitability.
9. Cost model không phải correctness proof.
10. Cost model không phải performance guarantee.
11. Optimization level là policy.
12. Optimization level không thay đổi language semantics.
13. `-O0` vẫn phải đúng.
14. `-O3` vẫn phải đúng.
15. Size optimization vẫn phải đúng.
16. Scalar optimization phải respect numeric semantics.
17. Checked arithmetic không được biến thành wrapping.
18. Wrapping arithmetic không được biến thành checked.
19. Saturating arithmetic phải preserve saturation.
20. Strict FP phải preserve required FP semantics.
21. Fast-math chỉ hoạt động khi policy cho phép.
22. CSE phải respect effects.
23. GVN phải respect memory.
24. PRE phải preserve evaluation order.
25. DCE phải preserve observable effects.
26. Dead-store elimination phải preserve memory semantics.
27. CFG transformation phải preserve control behavior.
28. Dominator information phải được invalidate đúng.
29. SSA transformations phải preserve phi semantics.
30. Memory SSA phải preserve memory dependency.
31. Unknown alias không phải NoAlias.
32. Alias proof phải có provenance.
33. Escape analysis không được tự nhận certainty khi Unknown.
34. Stack promotion phải preserve lifetime.
35. Allocation elimination phải preserve observable identity.
36. Scalar replacement phải respect address observability.
37. Load forwarding phải respect aliasing.
38. Store elimination phải respect external visibility.
39. Volatile không được optimize như ordinary memory.
40. Atomic không được optimize như ordinary memory.
41. Fence transformations phải preserve synchronization.
42. Loop transformation phải respect dependencies.
43. LICM phải preserve observable behavior.
44. Strength reduction phải respect overflow.
45. Unrolling phải respect cleanup.
46. Loop peeling phải preserve iteration count.
47. Loop fusion phải respect dependencies.
48. Loop fission phải respect dependencies.
49. Loop interchange phải respect dependencies.
50. Loop distribution phải preserve semantics.
51. Reduction transformation phải respect numeric policy.
52. Vectorization phải validate dependency.
53. Vectorization phải validate aliasing.
54. Vectorization phải validate bounds.
55. Vectorization phải validate alignment assumptions.
56. Vectorization phải handle remainder correctly.
57. Vectorization phải respect FP policy.
58. Runtime guards phải có correct fallback.
59. SIMD instruction chỉ được emit khi target hỗ trợ.
60. Target-specific intrinsic phải có feature requirement.
61. Autovectorization phải có cost model.
62. Gather/scatter phải có target legality.
63. Inlining phải preserve argument evaluation.
64. Inlining phải preserve cleanup.
65. Inlining phải preserve panic/unwind semantics.
66. Recursive inlining phải bounded.
67. Function cloning phải preserve semantics.
68. Specialization phải preserve generic semantics.
69. Generic specialization phải kiểm soát code bloat.
70. Devirtualization phải có concrete-type evidence.
71. Open-world code không được assume closed-world.
72. Interprocedural analysis phải respect FFI.
73. Unknown FFI effects phải conservative.
74. Pure contract phải có provenance.
75. Effect propagation phải distinguish proven/declared/inferred/unknown.
76. LTO phải preserve module boundaries where required.
77. Full LTO chỉ được assume closed world khi build model cho phép.
78. Thin LTO phải preserve semantic equivalence.
79. Incremental LTO phải invalidate đúng dependency.
80. Link-time dead stripping phải preserve reachability.
81. Code dedup phải preserve ABI.
82. PGO profile phải có identity.
83. PGO profile phải có target identity.
84. PGO profile phải có program compatibility.
85. Stale profile phải được nhận diện.
86. Incompatible profile không được silently apply.
87. Profile merge phải kiểm tra compatibility.
88. Profile weights phải explicit.
89. Profile không phải semantic truth.
90. Profile uncertainty phải được ghi.
91. Hotness không phải guarantee.
92. PGO không được thay đổi language semantics.
93. PGO không được tạo hidden runtime dependency.
94. Guarded specialization phải có fallback.
95. Runtime dispatch phải kiểm tra CPU features.
96. Unsupported ISA không được emit.
97. Cost model phải tính code size.
98. Cost model phải tính register pressure khi cần.
99. Cost model phải tính compile cost.
100. Multi-objective optimization không được ép thành universal score.
101. Pass pipeline phải deterministic.
102. Parallel pass execution không được tạo nondeterminism.
103. Fixed-point iteration phải có termination mechanism.
104. Optimization oscillation phải được phát hiện.
105. Optimization budget phải được enforce.
106. Compile-time budget phải được respect.
107. Memory budget phải được respect.
108. Code-size budget phải được respect.
109. Optimization cache phải có semantic hash.
110. Optimization cache phải có compiler identity.
111. Optimization cache phải có target identity.
112. Optimization cache phải có pass pipeline identity.
113. Profile-dependent cache phải chứa profile identity.
114. Stale optimization cache phải invalidate.
115. Cache hit phải semantic-equivalent với clean build.
116. Every critical transformation phải có validation boundary.
117. MIR verifier phải chạy sau critical transformations.
118. Machine verifier phải chạy sau machine transformations.
119. Translation validation phải tích hợp `552`.
120. Miscompilation phải có khả năng bisect tới pass.
121. Optimization regression phải phân biệt wrong-code regression.
122. Performance regression phải dùng benchmark evidence.
123. Code-size regression phải dùng artifact evidence.
124. Compile-time regression phải dùng build benchmark.
125. Missed optimization không phải compiler correctness failure.
126. Missed optimization phải có classification.
127. `why_not_optimized` phải dựa trên evidence.
128. AI không được tự tạo optimization rationale.
129. Unknown phải được giữ nguyên.
130. Debug mapping phải được preserve tối đa có thể.
131. Optimized-out variable phải được biểu diễn trung thực.
132. Panic semantics phải được preserve.
133. Exception/unwind semantics phải được preserve.
134. Ownership/drop semantics phải được preserve.
135. `defer` semantics phải được preserve.
136. Contract semantics phải được preserve.
137. Proven contracts có thể unlock optimization.
138. Runtime-checked contracts phải retain check hoặc equivalent proof.
139. `assume` phải được distinguish khỏi verified fact.
140. Constant-time contracts phải được respect.
141. Security policy có thể disable transformations.
142. Sanitizer build phải có optimization policy riêng.
143. Async state transformation phải preserve state machine behavior.
144. Future allocation elimination phải preserve lifetime.
145. Actor optimization phải preserve message semantics.
146. Reactive fusion phải preserve effect order.
147. Workflow optimization phải preserve durable state/effects.
148. Tensor optimization phải preserve numerical contract.
149. GPU optimization phải preserve synchronization.
150. CPU↔GPU transfer optimization phải preserve device semantics.
151. Automatic parallelization không được mặc định bật.
152. Auto-parallelization phải có legality evidence.
153. Deterministic FP mode phải constrain reassociation.
154. NUMA optimization không được assume unavailable topology.
155. Prefetch không được trở thành correctness dependency.
156. Machine scheduling phải preserve dependencies.
157. Register allocation feedback phải được hỗ trợ.
158. Spill-sensitive transformations phải có cost awareness.
159. Instruction combining phải respect target semantics.
160. Address-mode folding phải respect addressing semantics.
161. Immediate folding phải respect range.
162. Cross-target optimization phải preserve target-independent semantics.
163. Target-specific optimization phải record target assumptions.
164. Build artifact phải record optimization configuration.
165. PGO artifact phải record workload provenance.
166. Optimization artifact phải be reproducible under deterministic inputs.
167. Experimental passes không được silently become stable.
168. Failed pass có thể bị quarantine.
169. Quarantined pass phải preserve regression testcase.
170. Optimization snapshot phải có provenance.
171. Optimization explanation phải có source mapping.
172. Optimization evidence phải queryable.
173. Optimization metadata phải integrate `446`.
174. Performance evidence phải integrate `450/481`.
175. Profiling evidence phải integrate `476`.
176. Contract evidence phải integrate `479`.
177. Static analysis evidence phải integrate `478`.
178. Security evidence phải integrate `549`.
179. Correctness evidence phải integrate `552`.
180. LTO phải integrate linker `420`.
181. Generic optimization phải integrate `426/430`.
182. Numeric optimization phải integrate `458`.
183. Concurrency optimization phải integrate `424/471/472`.
184. GPU optimization phải integrate `503/504/505`.
185. AI graph optimization phải reuse compatible optimization infrastructure.
186. Workflow optimization phải reuse compatible pass infrastructure.
187. No optimization pass may introduce GC.
188. No optimization pass may introduce mandatory VM execution.
189. No optimization pass may introduce hidden allocation.
190. No optimization pass may introduce hidden thread.
191. No optimization pass may introduce hidden network activity.
192. No optimization pass may introduce hidden telemetry.
193. No optimization pass may introduce compiler dependency in produced native artifact.
194. Production optimizer phải có native backend path.
195. Optimizer phải support freestanding targets.
196. Optimizer phải support cross compilation.
197. Optimizer phải support incremental compilation.
198. Optimizer phải support reproducible builds.
199. Optimization policy must remain inspectable.
200. **Final invariant:** Axiom phải có một optimization framework thống nhất, deterministic, target-aware, profile-aware và evidence-driven, có khả năng tối ưu từ scalar/MIR đến LTO/PGO/vector/machine code, nhưng mọi transformation semantics-sensitive đều phải có legality boundary và được nối với validation/forensics của `552`; optimizer không được đánh đổi correctness, reproducibility hoặc tính minh bạch để lấy một performance claim không có bằng chứng.

**BOOTSTRAP-553: LOCKED.**

---

# BOOTSTRAP-554 — COMPILER CACHE 3.0, SEMANTIC INCREMENTALITY, PRECOMPILED MODULES, GENERIC INSTANCE CACHE & CROSS-PROJECT ARTIFACT REUSE

Đây là task tiếp theo.

`487` đã định nghĩa build graph/cache ở cấp project. `553` lại tạo thêm rất nhiều cacheable state trong optimizer. Vì vậy `554` sẽ giải quyết bài toán:

> **Làm thế nào Axiom có thể compile rất nhanh, tái sử dụng code đã biên dịch khi source/dependency không thay đổi, nhưng không bao giờ reuse artifact khi semantic/ABI/target assumptions đã thay đổi?**

Kiến trúc dự kiến:

```text
                    Source / Package
                           │
                           ▼
                    Semantic Hashing
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
          AST Cache     HIR Cache     Type Cache
              │            │            │
              └────────────┼────────────┘
                           ▼
                       MIR Cache
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        Generic Cache   Opt Cache    Codegen Cache
              │            │            │
              └────────────┼────────────┘
                           ▼
                    Object Cache
                           │
                           ▼
                     Link Artifact
```

Trọng tâm sẽ là:

- semantic hash thay vì timestamp;
- declaration-level invalidation;
- function-level incremental compilation;
- module interface cache;
- precompiled module;
- precompiled generic instances;
- ABI fingerprint;
- layout fingerprint;
- target fingerprint;
- optimization fingerprint;
- profile fingerprint;
- cross-project cache;
- local/remote cache;
- cache poisoning defense;
- stale artifact detection;
- dependency-aware invalidation;
- cache eviction;
- deterministic cache;
- artifact provenance;
- compiler daemon;
- parallel incremental compilation;
- cold-build vs warm-build semantics;
- và đặc biệt **một source thay đổi 1 function không được khiến toàn bộ project bị rebuild nếu semantic dependency graph chứng minh phần còn lại không bị ảnh hưởng**.