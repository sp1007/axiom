# BOOTSTRAP-560 — COMPILER IR OPTIMIZATION PIPELINE 3.0, SSA/MEMORY-SSA, ANALYSIS MANAGER, PASS DEPENDENCY, FIXPOINT OPTIMIZATION & VERIFIED TRANSFORMATION GRAPH

**Trạng thái: COMPLETED / LOCKED**

`560` khóa nền tảng tối ưu hóa IR thực sự của Axiom. `553` đã định nghĩa framework/pass manager/cost model; `560` định nghĩa **dữ liệu mà optimization engine phân tích, cách các analysis phụ thuộc nhau, cách transformation hợp lệ, cách invalidation xảy ra và cách hội tụ tới fixpoint**.

Mục tiêu:

> Optimization phải mạnh như compiler systems hiện đại nhưng có kiến trúc đủ rõ để compiler tự kiểm chứng, chạy song song và giải thích được vì sao một transformation được hoặc không được áp dụng.

---

## 560.1. Vị trí trong compiler

```text id="k7f5t1"
Source
  │
  ▼
AST → HIR → MIR
          │
          ▼
   ┌───────────────────┐
   │ Optimization IR   │
   │      Layer        │
   └─────────┬─────────┘
             │
             ▼
       Canonical MIR
             │
       ┌─────┴─────┐
       ▼           ▼
      SSA       Memory SSA
       │           │
       └─────┬─────┘
             ▼
       Analysis Manager
             │
             ▼
    Transformation Engine
             │
       ┌─────┼─────┐
       ▼     ▼     ▼
    Scalar Memory Loop
       │     │     │
       └─────┼─────┘
             ▼
       Vectorization
             │
             ▼
       Specialization
             │
             ▼
        Optimized MIR
             │
             ▼
       Machine Backend
```

---

# 560.2. Optimization IR phải giữ semantic identity

Optimization không được biến MIR thành một representation mất thông tin semantic cần thiết.

Mỗi optimized value phải có provenance về:

```text id="q9v7x8"
Source
HIR
MIR
Previous IR
```

---

# 560.3. IR identity

Mỗi entity có stable ID:

```text id="h8f3qk"
BlockId
ValueId
MemoryId
InstructionId
PhiId
LoopId
CallSiteId
```

---

# 560.4. SSA

SSA — Static Single Assignment — quy định mỗi logical value có một definition duy nhất trong SSA graph.

```text id="8k5j2n"
x0 = ...
x1 = ...
x2 = ...
```

---

# 560.5. SSA không phải source semantics

SSA chỉ là optimization representation.

Source variable có thể:

```text id="4d9z5r"
x = 1
x = 2
```

nhưng được lower thành nhiều SSA values.

---

# 560.6. Basic block

Mỗi block:

```text id="e4y0cm"
Block {
    id
    instructions[]
    terminator
}
```

---

# 560.7. Terminator

Mỗi block có đúng một control-flow terminator:

```text id="0t7t5e"
jump
branch
switch
return
panic
unreachable
invoke
```

---

# 560.8. CFG

Control-flow graph:

```text id="6g3s1h"
Block A
 ├──→ Block B
 └──→ Block C
          │
          ▼
       Block D
```

---

# 560.9. CFG invariants

CFG phải bảo đảm:

- edge hợp lệ;
- predecessor/successor nhất quán;
- entry duy nhất;
- unreachable blocks explicit;
- terminator hợp lệ.

---

# 560.10. Dominance

`A` dominates `B` nếu mọi path từ entry tới `B` đều đi qua `A`.

Dominance là nền tảng cho:

- SSA;
- code motion;
- loop analysis;
- control dependence.

---

# 560.11. Immediate dominator

Mỗi reachable block, ngoại trừ entry, có một immediate dominator.

---

# 560.12. Dominator tree

```text id="2n3f4v"
Entry
 ├── B1
 │    ├── B2
 │    └── B3
 └── B4
```

---

# 560.13. Post-dominance

Post-dominator tree được dùng cho:

- control dependence;
- branch simplification;
- speculation;
- structured cleanup.

---

# 560.14. Critical edges

Critical edge:

```text id="s1z7k0"
A → B
```

trong đó A có nhiều successors và B có nhiều predecessors.

Pass có thể split critical edge khi cần.

---

# 560.15. SSA construction

Default algorithm có thể dựa trên:

```text id="x4a9c2"
dominance frontier
```

hoặc optimized incremental SSA construction.

Implementation choice không thay đổi semantics.

---

# 560.16. Phi node

```text id="w2m6k1"
x3 = φ(x1 from B1, x2 from B2)
```

Phi không phải runtime instruction.

---

# 560.17. Phi lowering

Phi được lower sau khi optimization SSA hoàn thành.

---

# 560.18. SSA destruction

SSA destruction phải preserve semantics khi chuyển sang machine-oriented representation.

---

# 560.19. Parallel copy

Phi lowering sử dụng parallel-copy semantics trước khi register allocation.

---

# 560.20. Use-def chain

Mỗi SSA value phải có:

```text id="v8x4z0"
definition
uses[]
```

---

# 560.21. Def-use consistency

Mọi use phải tham chiếu definition hợp lệ.

---

# 560.22. Dominance of definitions

Trong SSA, definition phải dominate use, ngoại trừ các semantics đặc biệt của phi.

---

# 560.23. Memory SSA

SSA thông thường quản lý values.

Memory SSA quản lý **memory states**.

```text id="x5p2v6"
M0
 │
Store A
 │
M1
 │
Load
```

---

# 560.24. MemoryDef

Store/side effect tạo MemoryDef:

```text id="2f0b9w"
M1 = MemoryDef(M0, store p, x)
```

---

# 560.25. MemoryUse

Load tạo MemoryUse:

```text id="6s7m3q"
load p uses M1
```

---

# 560.26. MemoryPhi

Control-flow merge:

```text id="1v7k8n"
M3 = MemoryPhi(M1, M2)
```

---

# 560.27. Memory SSA purpose

Memory SSA hỗ trợ:

- load/store elimination;
- dead store elimination;
- alias-aware optimization;
- LICM;
- forwarding;
- dependence analysis.

---

# 560.28. Alias analysis

Phải trả lời:

```text id="1x4r5z"
MayAlias
NoAlias
MustAlias
Unknown
```

---

# 560.29. Unknown alias

Unknown không được tự động coi là NoAlias.

---

# 560.30. Alias hierarchy

Có thể kết hợp:

```text id="j4k1q9"
Type-based
Provenance-based
Local
Flow-sensitive
Context-sensitive
Interprocedural
```

---

# 560.31. Pointer provenance

Tuân thủ semantics đã khóa trong `445`.

Optimization không được suy luận alias trái với provenance model.

---

# 560.32. No-alias proof

Nếu compiler chứng minh:

```text id="8p1w5d"
p ≠ q
```

thì memory operations có thể reorder/eliminate theo memory model.

---

# 560.33. Unknown memory

Foreign call, inline assembly, volatile hoặc unsafe operation có thể tạo conservative memory barrier.

---

# 560.34. Volatile

Volatile access không được loại bỏ, merge hoặc reorder trái với contract.

---

# 560.35. Atomic

Atomic memory operation phải tuân thủ memory ordering của `424`.

---

# 560.36. Memory ordering

Optimization không được biến:

```text id="j6w3t2"
Acquire
Release
SeqCst
```

thành semantics yếu hơn nếu không chứng minh tương đương.

---

# 560.37. Range analysis

Compiler có thể biết:

```text id="3g9q1a"
0 ≤ x < 10
```

---

# 560.38. Range domain

Range analysis hỗ trợ:

```text id="p8r2m4"
interval
known bits
sign
alignment
congruence
```

---

# 560.39. Integer overflow

Phải phân biệt:

```text id="xq8y7v"
wrapping
checked
saturating
undefined-by-contract
```

theo type/operator semantics.

---

# 560.40. Overflow optimization

Không được assume overflow UB nếu Axiom expression semantics không quy định UB.

---

# 560.41. Constant propagation

```text id="w5j1e3"
x = 10
y = x + 2
→ y = 12
```

---

# 560.42. Sparse conditional constant propagation

Có thể kết hợp:

```text id="z8r6v2"
CFG reachability
+
constant lattice
```

---

# 560.43. Value lattice

Tối thiểu:

```text id="n0x4qp"
Unknown
Constant
Overdefined
```

---

# 560.44. Dead code

Nếu compiler chứng minh block không reachable:

```text id="4z7m1q"
remove
```

---

# 560.45. Dead instruction

Instruction không có observable effect và result không được dùng có thể eliminate.

---

# 560.46. Observable effects

Bao gồm:

- volatile;
- atomic;
- I/O;
- synchronization;
- external calls;
- panic;
- resource effects;
- explicitly observable stores.

---

# 560.47. Pure instruction

Pure instruction không có observable side effect ngoài value result.

---

# 560.48. Effect summary

Mỗi function có summary:

```text id="s7k2q1"
ReadsMemory
WritesMemory
Allocates
Blocks
Panics
Throws
PerformsIO
UsesAtomic
CallsForeign
```

liên kết với effect model.

---

# 560.49. Function attributes

Ví dụ:

```text id="v2q5c9"
@pure
@no_alloc
@no_block
@no_panic
```

chỉ được optimizer dùng nếu compiler semantics/contract chứng minh hợp lệ.

---

# 560.50. Call graph

```text id="n5z0h8"
main
 ├── foo
 │    └── bar
 └── baz
```

---

# 560.51. Recursive SCC

Call graph phải phân tích strongly connected components:

```text id="u8p1c3"
foo → bar
bar → foo
```

---

# 560.52. Interprocedural summary

Function có thể export summary:

```text id="e3k7v9"
arguments
returns
memory
effects
exceptions/panic
alias
allocation
```

---

# 560.53. Context sensitivity

Compiler có thể có:

- context-insensitive;
- call-site-sensitive;
- limited context-sensitive.

Không được để context explosion không kiểm soát.

---

# 560.54. Inlining

Inlining là transformation có điều kiện.

```text id="0w4y7s"
caller
 └── call foo()
```

→ body của `foo` được nhập vào caller.

---

# 560.55. Inline cost model

Chi phí gồm:

```text id="m1c9f5"
instruction growth
code size
register pressure
cache impact
branch impact
hotness
specialization opportunity
```

---

# 560.56. No mandatory inlining

Inlining là optimization, không phải semantic requirement.

---

# 560.57. Devirtualization

Nếu compiler chứng minh dynamic dispatch chỉ có một target:

```text id="q6h4v8"
dyn call
→ direct call
```

---

# 560.58. Trait-aware optimization

`426` trait metadata phải cung cấp:

```text id="e0y8u2"
candidate set
object safety
dispatch kind
specialization
```

---

# 560.59. Loop representation

Mỗi loop có:

```text id="a4j9k2"
header
latches
preheader
body
exits
nesting
```

---

# 560.60. Loop canonicalization

Optimization nên canonicalize:

- preheader;
- unique latch;
- dedicated exits.

---

# 560.61. Loop-invariant code motion

Expression không phụ thuộc loop iteration có thể move ra ngoài loop nếu effect/memory safety cho phép.

---

# 560.62. LICM memory requirement

Memory load chỉ được move nếu alias analysis chứng minh không có intervening write có thể thay đổi value.

---

# 560.63. Loop unswitching

Invariant condition:

```text id="4h8n2w"
for ...
    if invariant
```

có thể biến thành hai loop specialized.

---

# 560.64. Loop rotation

Có thể canonicalize loop để cải thiện branch layout.

---

# 560.65. Loop unrolling

Unrolling chịu:

```text id="5g6k1d"
code-size budget
register pressure
trip-count knowledge
hotness
```

---

# 560.66. Full unrolling

Chỉ khi cost model cho phép.

---

# 560.67. Partial unrolling

Được ưu tiên khi loop lớn/unknown trip count.

---

# 560.68. Loop vectorization

Vectorizer cần chứng minh:

```text id="2p8v7x"
memory dependence
alignment
trip count
operation legality
FP policy
```

---

# 560.69. Scalar fallback

Vectorized loop phải có fallback nếu runtime conditions cần thiết.

---

# 560.70. Runtime alias check

Compiler có thể generate:

```text id="g5m2x9"
if non-overlap:
    vector loop
else:
    scalar loop
```

nếu cost model có lợi.

---

# 560.71. SIMD semantics

Phải preserve:

- NaN;
- signed zero;
- rounding;
- overflow;
- trapping semantics nếu applicable.

---

# 560.72. Fast math

Aggressive floating-point transformations chỉ được bật khi policy cho phép.

---

# 560.73. Floating-point reassociation

Không mặc định biến:

```text id="z2p8m4"
(a+b)+c
```

thành:

```text id="8j6k1q"
a+(b+c)
```

nếu semantics yêu cầu strict FP.

---

# 560.74. Vector reduction

Reduction phải có numerical policy rõ ràng.

---

# 560.75. Common Subexpression Elimination

```text id="v3f5k2"
a+b
a+b
```

có thể share nếu operands/effects tương đương.

---

# 560.76. Global Value Numbering

Value identity có thể dựa trên semantic expression equivalence.

---

# 560.77. Load elimination

Hai loads có thể merge nếu memory state/alias proof cho phép.

---

# 560.78. Store-to-load forwarding

Store:

```text id="e9p4q7"
*p = x
```

sau đó load `*p` có thể replace bằng `x` nếu không có intervening write.

---

# 560.79. Dead Store Elimination

Store không observable có thể eliminate.

---

# 560.80. Partial redundancy elimination

Expression chỉ redundant trên một số paths có thể được hoist nếu cost/semantics cho phép.

---

# 560.81. Strength reduction

Ví dụ:

```text id="f7c2m5"
x * 2
→ x + x
```

chỉ khi target/cost/overflow semantics cho phép.

---

# 560.82. Instruction selection awareness

IR optimization có thể cân nhắc target machine cost nhưng không được hard-code ISA semantics vào generic MIR.

---

# 560.83. Target-independent vs target-dependent

```text id="p4m8z1"
Generic Optimization
        ↓
Target-aware Optimization
        ↓
Machine Optimization
```

---

# 560.84. Analysis Manager

```text id="k3x7n9"
AnalysisManager {
    get<T>()
    invalidate<T>()
    preserve<T>()
    require<T>()
}
```

---

# 560.85. Analysis result

```text id="b6q2m8"
AnalysisResult<T> {
    fingerprint
    IRVersion
    scope
    value
}
```

---

# 560.86. Analysis scope

Có thể là:

```text id="1w5d8c"
Module
Function
Loop
Block
Instruction
```

---

# 560.87. Analysis dependency

Analysis A có thể yêu cầu B.

```text id="r8v2k4"
AliasAnalysis
    ↓
MemoryDependence
    ↓
LoadElimination
```

---

# 560.88. Analysis dependency graph

Phải được explicit.

---

# 560.89. Analysis caching

Analysis result được memoize theo:

```text id="j9h3x5"
IR fingerprint
analysis kind
scope
configuration
target
```

---

# 560.90. Analysis invalidation

Transformation phải khai báo analysis nào bị invalidated.

---

# 560.91. Preservation contract

Ví dụ:

```text id="n5c8v1"
Transform T:
    preserves DominatorTree
    preserves LoopInfo
    invalidates MemorySSA
```

---

# 560.92. Conservative invalidation

Nếu pass không chứng minh preservation:

```text id="d4x7q2"
invalidate
```

---

# 560.93. No stale analysis

Optimizer tuyệt đối không được sử dụng analysis result không còn đúng.

---

# 560.94. Analysis verification

Debug/verification mode có thể recompute analysis để kiểm tra cached result.

---

# 560.95. Transformation contract

Mỗi transformation:

```text id="s6j2m9"
Preconditions
Transformation
Postconditions
PreservedAnalyses
Cost
ValidationPolicy
```

---

# 560.96. Preconditions

Ví dụ vectorization:

```text id="c8x4p7"
no forbidden dependence
legal types
legal target operation
```

---

# 560.97. Postconditions

Transformation phải tạo IR hợp lệ.

---

# 560.98. IR verifier

Sau critical transformations có thể chạy verifier:

```text id="v0m6z3"
verify_cfg
verify_ssa
verify_memory_ssa
verify_types
verify_effects
```

---

# 560.99. Transformation graph

```text id="h1q7v5"
MIR
 │
 ├── T1
 │    └── T2
 │         └── T4
 │
 └── T3
      └── T4
```

Mỗi transformation có provenance.

---

# 560.100. Transformation identity

```text id="k2p8n6"
TransformId {
    pass
    version
    input_fingerprint
    configuration
}
```

---

# 560.101. Transformation provenance

Optimizer phải biết:

```text id="y4r9c1"
instruction/value
    ← transformation
    ← previous value
    ← source semantic entity
```

---

# 560.102. Translation validation

`552` có thể validate:

```text id="m7x3p9"
IR_before
      ↓ T
IR_after
```

---

# 560.103. Validation level

Không phải transformation nào cũng cần SMT/formal proof.

Policy có thể:

```text id="z1v8k4"
None
Structural
Differential
TranslationValidated
ProofRequired
```

---

# 560.104. Critical transformation

Các transformation nhạy cảm:

- bounds elimination;
- alias-sensitive reorder;
- atomic reorder;
- overflow-sensitive optimization;
- ABI lowering;
- vectorization;
- unsafe memory transformation.

---

# 560.105. Proof artifact

Validation result:

```text id="c4n7x2"
ValidationEvidence {
    transform_id
    before_hash
    after_hash
    method
    status
    proof
}
```

---

# 560.106. Unknown validation

Solver timeout:

```text id="e8j5q1"
Unknown
```

không phải:

```text
Proven
```

---

# 560.107. Failed validation

Transformation bị rollback.

---

# 560.108. Transactional transformation

```text id="x9m3w6"
clone/transaction
→ transform
→ verify
→ validate
→ commit
```

---

# 560.109. Cheap transformation

Có thể mutate IR trực tiếp nếu framework có undo/logging hoặc verifier đủ mạnh.

---

# 560.110. Fixpoint optimization

Một pipeline có thể lặp:

```text id="q7f2m8"
canonicalize
→ optimize
→ canonicalize
→ optimize
→ ...
```

---

# 560.111. Fixpoint criterion

Không dựa trên số vòng lặp cố định duy nhất.

Có thể dừng khi:

```text id="m5c8x2"
IR fingerprint unchanged
```

hoặc không còn profitable transformation.

---

# 560.112. Maximum iterations

Mọi fixpoint loop phải có hard bound.

---

# 560.113. Oscillation detection

Nếu:

```text id="b4n8q6"
IR A → B → A
```

engine phải phát hiện.

---

# 560.114. Optimization oscillation

Phải ngăn:

```text id="f3j7k9"
T1 undo T2
T2 undo T1
```

---

# 560.115. Monotonic transformations

Nơi có thể, optimization nên dùng monotonic measure:

```text id="n8c4v2"
instruction count
redundancy
cost
```

nhưng không được giả định mọi optimization monotonic.

---

# 560.116. Profitability

Một transformation hợp lệ nhưng không có lợi có thể bị từ chối.

---

# 560.117. Cost model

Cost model nhận:

```text id="y6p1m8"
target
CPU features
hotness
code size
latency
throughput
register pressure
cache behavior
```

---

# 560.118. Multi-objective optimization

Không có universal “best”.

Policy xác định:

```text id="v9k2s5"
speed
size
compile_time
power
latency
```

---

# 560.119. Optimization profile

Ví dụ:

```text id="x3m7q1"
debug
balanced
speed
size
aggressive
custom
```

---

# 560.120. Profile determinism

Cùng:

```text source
target
profile
PGO data
compiler version
```

phải tạo cùng semantic result.

---

# 560.121. PGO

Profile data chỉ là optimization input.

Không được biến profile thành semantic truth.

---

# 560.122. Stale PGO

Profile mismatch phải được phát hiện.

---

# 560.123. PGO provenance

Mỗi profile:

```text id="a8v5c2"
program identity
build identity
target
collection mode
timestamp
hash
```

---

# 560.124. Speculative optimization

Có thể optimize dựa trên assumption nếu có fallback/guard.

---

# 560.125. Guard

```text id="q4m8z7"
if assumption:
    fast path
else:
    fallback
```

---

# 560.126. No unsafe speculation

Nếu assumption sai mà không có semantics-defined fallback:

```text id="j1x6p9"
transformation forbidden
```

---

# 560.127. Deoptimization

Axiom native compiler mặc định **không cần VM-style deoptimization**.

Nếu optimization cần runtime guard thì explicit guard/fallback được ưu tiên.

---

# 560.128. Escape analysis

Optimizer có thể chứng minh allocation không escape.

---

# 560.129. Allocation elimination

Nếu semantics/resource lifetime cho phép:

```text id="m8c3v6"
heap allocation
→ stack/value
```

---

# 560.130. Ownership integration

`423` ownership metadata giúp optimizer biết:

```text id="n5x1q7"
unique
shared
borrowed
moved
```

nhưng optimizer không được thay đổi ownership semantics.

---

# 560.131. Scalar replacement

Aggregate:

```text id="z6k2m4"
struct {a,b}
```

có thể scalarize thành:

```text id="p9v3c8"
a
b
```

nếu không cần materialized address.

---

# 560.132. SROA

Scalar Replacement of Aggregates phải preserve observable layout khi address escapes.

---

# 560.133. Stack promotion

Heap allocation có thể chuyển stack nếu lifetime/provenance chứng minh safe.

---

# 560.134. Bounds-check elimination

Ví dụ:

```text id="x7q2n5"
for i in 0..len(a):
    a[i]
```

có thể eliminate repeated bounds checks khi range proof đủ mạnh.

---

# 560.135. Contract integration

`479` contracts có thể cung cấp proof:

```text id="g5m9r2"
0 ≤ i < len(a)
```

---

# 560.136. Unknown proof

Unknown → retain runtime check.

---

# 560.137. Assumption

`assume` có semantics đặc biệt và phải được phân biệt với proven fact.

---

# 560.138. Security-sensitive assumptions

Security analysis `549` phải được preserve qua optimization.

---

# 560.139. Constant-time code

Optimization không được tự ý biến constant-time code thành timing-variable implementation khi policy yêu cầu constant-time.

---

# 560.140. Realtime code

`@realtime` code phải preserve restrictions:

```text id="r2m7x9"
no allocation
no blocking
no forbidden calls
```

---

# 560.141. Async optimization

Async state machine có thể optimize:

- state representation;
- polling;
- allocation;
- suspend/resume paths.

Nhưng không được thay đổi Future semantics.

---

# 560.142. Closure optimization

Closure environment có thể:

- scalarize;
- stack-promote;
- inline;
- eliminate.

---

# 560.143. Generic specialization

Monomorphized generic instances có thể specialize theo concrete types/constants.

---

# 560.144. Specialization cache

Specialized instance identity phải canonical.

---

# 560.145. Code duplication control

Specialization phải chịu code-size budget.

---

# 560.146. Whole-program optimization

Closed-world mode có thể:

- internalize symbols;
- eliminate unused functions;
- devirtualize;
- specialize;
- merge constants.

---

# 560.147. Dynamic library boundary

Symbol exported/externally visible không được eliminate nếu ABI yêu cầu giữ.

---

# 560.148. FFI boundary

Foreign function có unknown effects mặc định conservative.

---

# 560.149. Link-time optimization

LTO nhận canonical IR/object metadata thay vì reparse source.

---

# 560.150. Thin-LTO-like mode

Axiom có thể dùng summary-based cross-module optimization để giảm memory/compile time.

---

# 560.151. Function summaries

Summary phải fingerprintable.

---

# 560.152. Cross-module invalidation

Thay đổi private implementation chỉ invalidate consumers nếu exported summary thay đổi.

---

# 560.153. ABI summary

Public function optimization phải preserve ABI contract.

---

# 560.154. Internal ABI optimization

Internal-only functions có thể sử dụng calling convention tối ưu hơn nếu không escape.

---

# 560.155. Tail-call optimization

Có thể transform call → tail call nếu ABI/control-flow conditions cho phép.

---

# 560.156. Recursion optimization

Tail recursion có thể biến thành loop.

---

# 560.157. Branch optimization

Có thể:

- constant-fold branch;
- merge blocks;
- jump threading;
- branch inversion;
- block layout.

---

# 560.158. Jump threading

Chỉ khi không làm tăng observable behavior hoặc violate control-flow effects.

---

# 560.159. Block layout

Hot/cold layout có thể tối ưu instruction cache và branch prediction.

---

# 560.160. Hot/cold splitting

Cold path có thể tách khỏi hot path.

---

# 560.161. Exception/panic path

Panic/unwind paths có thể được cold-mark nhưng semantics phải preserve.

---

# 560.162. Code-size optimization

Các pass có thể ưu tiên:

```text id="s8f2k4"
size reduction
```

khi profile yêu cầu.

---

# 560.163. Identical Code Folding

Functions equivalent có thể merge nếu symbol/ABI semantics cho phép.

---

# 560.164. Constant merging

Read-only constants có thể merge nếu address identity không observable.

---

# 560.165. Address identity

Optimizer phải phân biệt:

```text id="m4x7q1"
value equality
address equality
object identity
```

---

# 560.166. Object identity

Nếu language semantics expose address identity, optimizer không được merge objects trái phép.

---

# 560.167. Memory lifetime

Optimization không được kéo dài/rút ngắn observable resource lifetime trái với `423`.

---

# 560.168. Destructor effects

`drop`/destructor có observable effect → không được eliminate tùy tiện.

---

# 560.169. Defer

`defer` cleanup phải remain semantically equivalent sau CFG transformation.

---

# 560.170. Panic

Code motion không được biến:

```text id="f8q3m6"
panic
```

thành behavior xảy ra ở thời điểm khác nếu thứ tự observable.

---

# 560.171. Evaluation order

Axiom expression evaluation order phải được encode trong MIR để optimizer biết transformation nào hợp lệ.

---

# 560.172. Effect barriers

Compiler có thể tạo explicit barrier:

```text id="j6r1x8"
EffectBarrier
```

khi cần ngăn reorder.

---

# 560.173. Optimization legality

Legality trước profitability.

```text id="z9p4k2"
if !legal:
    reject
else if !profitable:
    skip
else:
    apply
```

---

# 560.174. Transformation scheduling

Pass dependencies phải được khai báo.

---

# 560.175. Pass prerequisite

Ví dụ:

```text id="q7m2v5"
Vectorize
requires LoopInfo
requires ScalarEvolution
requires AliasAnalysis
```

---

# 560.176. Analysis prerequisite

Analysis Manager tự động materialize prerequisite analysis.

---

# 560.177. Pass invalidation

Pass commit phải gửi invalidation event.

---

# 560.178. Incremental analysis

Analysis có thể update incrementally nếu transformation cung cấp edit summary.

---

# 560.179. Full recompute fallback

Nếu incremental update không đáng tin cậy:

```text id="w5x8c1"
recompute
```

---

# 560.180. Analysis fingerprint

Analysis fingerprint phải thay đổi nếu semantic conclusion thay đổi.

---

# 560.181. Transformation fingerprint

Transformation output fingerprint phải thay đổi nếu IR semantic content thay đổi.

---

# 560.182. Canonicalization

Canonical forms giúp:

- CSE;
- cache;
- deterministic comparison;
- fixpoint detection.

---

# 560.183. Canonical operand ordering

Commutative operations có thể canonicalize operand ordering.

---

# 560.184. Do not canonicalize non-equivalent expressions

FP, overflow, side effects và evaluation order phải được tôn trọng.

---

# 560.185. Deterministic pass ordering

Cùng pipeline/configuration phải có cùng logical transformation order.

---

# 560.186. Parallel optimization

Independent functions có thể optimize song song.

---

# 560.187. Module-level synchronization

Cross-function transformations phải coordinate qua dependency graph.

---

# 560.188. Deterministic merge

Nếu hai worker produce independent transformations:

```text id="k8q2m6"
merge order
```

không được thay đổi semantics hoặc final canonical representation.

---

# 560.189. Race-free analysis

Analysis DB phải support concurrent reads và controlled publication.

---

# 560.190. Speculative analysis

Có thể precompute analysis cho hot functions nhưng không được ảnh hưởng semantics.

---

# 560.191. Compile-time budget

Optimization có budget:

```text id="m3x7q9"
time
memory
iterations
code growth
```

---

# 560.192. Budget exhaustion

Hết budget:

```text id="r5v1c8"
stop optimization
```

không phải compiler error, trừ policy yêu cầu.

---

# 560.193. Optimization report

Compiler có thể xuất:

```text id="c2n8f4"
why_applied
why_rejected
cost
analysis_evidence
transformation_chain
```

---

# 560.194. Example

```text id="g7p3m1"
BoundsCheckElimination
  status: applied
  proof: RangeAnalysis#812
  evidence:
      i ∈ [0,len-1]
  checks_removed: 4
```

---

# 560.195. AI explanation

AI có thể hỏi:

```text id="v6k1x9"
why_optimized(function)
why_not_vectorized(loop)
why_not_inlined(call)
show_proof(value)
show_dependencies(pass)
```

---

# 560.196. AI cannot mutate optimizer evidence

AI chỉ đọc/propose transformation; compiler vẫn là authority.

---

# 560.197. Optimization replay

Một optimization chain phải có khả năng replay khi forensic mode bật.

---

# 560.198. Miscompilation isolation

`552` phải có thể:

```text id="t4n8q2"
disable pass
→ rebuild
→ differential compare
```

---

# 560.199. Final optimization correctness chain

```text id="w8m2c5"
Source Semantics
      ↓
MIR
      ↓
Analysis Evidence
      ↓
Legal Transformation
      ↓
IR Verification
      ↓
Translation Validation
      ↓
Optimized MIR
      ↓
Machine Validation
```

---

# 560.200. HARD INVARIANTS

1. SSA là optimization representation, không phải source semantics.
2. Mỗi SSA value có một definition logic.
3. Mọi SSA use phải có definition hợp lệ.
4. Definition phải dominate use theo SSA rules.
5. Phi phải được xử lý theo CFG semantics.
6. Memory SSA phải tách khỏi value SSA.
7. MemoryDef phải biểu diễn memory-defining operation.
8. MemoryUse phải biểu diễn memory dependency.
9. MemoryPhi phải biểu diễn merge memory state.
10. Alias Unknown không được coi là NoAlias.
11. Optimization phải tuân thủ pointer provenance.
12. Volatile không được loại bỏ tùy tiện.
13. Atomic phải preserve memory ordering.
14. FP transformations phải respect numerical policy.
15. Integer transformations phải respect overflow semantics.
16. Observable effects không được eliminate.
17. Pure values có thể optimize mạnh hơn effectful operations.
18. Analysis result phải bind với IR version/fingerprint.
19. Stale analysis không được sử dụng.
20. Transformation phải khai báo preconditions.
21. Transformation phải khai báo postconditions.
22. Transformation phải khai báo preserved analyses.
23. Không chứng minh preservation → invalidate.
24. IR verifier phải phát hiện malformed IR.
25. CFG phải có terminator hợp lệ.
26. Predecessor/successor lists phải nhất quán.
27. Dominator tree phải nhất quán.
28. Loop information phải nhất quán.
29. Call graph phải xử lý recursion.
30. SCC recursion phải được hỗ trợ.
31. Function summaries phải fingerprintable.
32. Cross-module optimization phải preserve public ABI.
33. FFI boundary mặc định conservative.
34. Unknown foreign effects không được coi là pure.
35. Inlining phải preserve semantics.
36. Devirtualization phải có proof/correct candidate information.
37. Generic specialization phải canonical.
38. Specialization phải chịu code-size budget.
39. LICM phải preserve memory/effect semantics.
40. Loop transformations phải preserve termination semantics.
41. Vectorization phải prove required dependence conditions.
42. Vectorization phải respect target legality.
43. Vectorization phải respect FP policy.
44. Runtime guard phải có fallback.
45. Speculation không được tạo UB mới.
46. Bounds-check elimination phải dựa trên valid proof.
47. Unknown range không đủ để remove bounds check.
48. Contracts có thể supply optimization evidence.
49. Assumptions phải distinguish với proofs.
50. Security analysis evidence phải survive optimization.
51. Constant-time requirements phải survive optimization.
52. Realtime restrictions phải survive optimization.
53. Async semantics phải survive state-machine optimization.
54. Closure environment optimization phải preserve capture semantics.
55. Destructor effects phải preserve.
56. `defer` cleanup order phải preserve.
57. Panic behavior phải preserve.
58. Evaluation order phải được encode đủ trong IR.
59. Effect barriers phải được respect.
60. Allocation elimination phải preserve observable lifetime.
61. Stack promotion phải preserve ownership/provenance.
62. Scalar replacement phải preserve address observability.
63. Object identity phải được respect.
64. Address identity phải được phân biệt với value equality.
65. Dead-store elimination phải prove non-observability.
66. Load elimination phải prove memory equivalence.
67. Store-to-load forwarding phải prove no intervening conflicting write.
68. CSE phải prove expression/effect equivalence.
69. GVN không được merge non-equivalent values.
70. Constant propagation phải preserve overflow semantics.
71. DCE không được remove effectful instructions.
72. CFG simplification phải preserve reachable behavior.
73. Jump threading phải preserve side-effect order.
74. Block layout không được thay đổi semantics.
75. Hot/cold splitting phải preserve debug/unwind semantics.
76. Tail-call transformation phải satisfy ABI conditions.
77. Recursive-to-loop transformation phải preserve observable stack/resource behavior where exposed.
78. PGO chỉ là optimization input.
79. PGO mismatch phải detectable.
80. Optimization profile phải be part of relevant cache identity.
81. Target features phải be part of relevant optimization identity.
82. ABI phải be part of ABI-sensitive optimization identity.
83. LTO phải bind whole-program dependency state.
84. Internalization chỉ được áp dụng khi external visibility không yêu cầu.
85. ICF phải respect symbol/address identity.
86. Constant merging phải respect address observability.
87. Analysis dependencies phải explicit.
88. Pass dependencies phải explicit.
89. Analysis invalidation phải explicit.
90. Pass order phải deterministic.
91. Parallel pass execution phải deterministic về semantic output.
92. Worker assignment không được ảnh hưởng output.
93. Cache hit không được ảnh hưởng output.
94. Analysis cache không được trở thành semantic authority.
95. Transformation provenance phải được lưu.
96. Optimization evidence phải preserve uncertainty.
97. Translation validation phải phân biệt Proven/Validated/Unknown/Failed.
98. Solver timeout không được coi là proof.
99. Failed validation phải reject hoặc rollback transformation.
100. Critical transformations phải có stronger validation policy.
101. Optimization transaction phải publish atomically.
102. Malformed transformed IR không được commit.
103. Fixpoint optimization phải có termination bound.
104. Fixpoint oscillation phải detect được.
105. Fixpoint detection phải dựa trên semantic/canonical IR identity.
106. Optimization không được loop vô hạn.
107. Profitability không được override legality.
108. Legal nhưng unprofitable transformation có thể bị bỏ qua.
109. Cost model phải target-aware khi cần.
110. Cost model không được thay đổi semantics.
111. Code-size budget phải explicit.
112. Compile-time budget phải explicit.
113. Memory budget phải explicit.
114. Optimization budget exhaustion không mặc định là compiler error.
115. Incremental analysis có thể dùng edit summaries.
116. Incremental analysis phải fallback về recomputation khi uncertain.
117. Analysis fingerprint phải thay đổi khi conclusion thay đổi.
118. Transformation fingerprint phải phản ánh output semantics.
119. Canonicalization phải deterministic.
120. Commutative canonicalization không được áp dụng cho non-equivalent operations.
121. Floating-point reassociation không mặc định được phép.
122. Fast-math phải explicit.
123. SIMD lowering phải preserve scalar fallback semantics.
124. Vector reduction phải respect numerical policy.
125. Atomic transformation phải respect happens-before semantics.
126. Memory reordering phải được memory model cho phép.
127. Ownership metadata không được bị optimizer làm sai.
128. Move/drop semantics phải preserve.
129. Partial initialization semantics phải preserve.
130. Maybe-uninitialized state không được biến thành valid value.
131. Unsafe operations phải remain semantically valid.
132. Inline assembly phải được xem là effectful/conservative theo contract.
133. MMIO/volatile semantics không được optimize away.
134. Resource lifetime phải preserve.
135. File/network/process effects phải preserve.
136. `no_alloc` contract phải survive transformation.
137. `no_block` contract phải survive transformation.
138. `no_panic` contract phải survive transformation.
139. Realtime contract phải survive transformation.
140. Constant-time contract phải survive transformation.
141. Security taint/effect information phải survive transformation.
142. Provenance chain phải remain queryable.
143. Source→HIR→MIR→optimized MIR mapping phải remain available.
144. Debug source mapping phải survive transformations.
145. Unwind mapping phải survive control-flow transformations.
146. Async source mapping phải survive state-machine optimization.
147. Generic source mapping phải preserve specialization provenance.
148. Comptime-generated code phải preserve generation provenance.
149. LTO must preserve module provenance.
150. Machine backend must receive semantically valid optimized IR.
151. Backend assumptions must be represented explicitly.
152. Generic optimization must not silently assume a specific ISA.
153. Target optimization must not leak target assumptions into generic semantics.
154. Analysis cache identity must include all semantic inputs.
155. Pass cache identity must include all transformation inputs.
156. Cached analysis must be validated before reuse.
157. Cached transformation must be validated before reuse where required.
158. Remote optimization cache must be treated as untrusted until validated.
159. Corrupt optimization cache must be discarded.
160. Cache eviction must not affect correctness.
161. Query engine `559` remains semantic authority for optimization dependencies.
162. Scheduler `558` remains execution mechanism, not semantic authority.
163. Daemon `555` remains optional infrastructure.
164. Memory architecture `557` must not alter optimization semantics.
165. Semantic cache `554` must not become a second optimizer.
166. Correctness engine `552` must be able to inspect transformation provenance.
167. Optimization reports must be machine-readable.
168. AI explanations must cite actual analysis evidence.
169. AI must not fabricate optimization proofs.
170. AI suggestions must pass normal legality checks.
171. AI must not bypass compiler validation.
172. Analysis results must be snapshot-consistent.
173. Incremental optimization must be equivalent to clean optimization where the same inputs apply.
174. Cached optimization must be equivalent to recomputed optimization.
175. Parallel optimization must be equivalent to serial optimization.
176. Different worker counts must not alter semantic output.
177. Speculative optimization must not alter semantics if speculation is discarded.
178. Runtime guards must preserve fallback correctness.
179. Deoptimization is not mandatory for native Axiom.
180. Native Axiom optimization must not depend on a VM.
181. No GC assumption may be introduced by optimizer.
182. Ownership analysis may enable optimization but must not become a hidden runtime mechanism.
183. Optimizer must not introduce hidden allocation.
184. Optimizer must not introduce hidden blocking.
185. Optimizer must not introduce hidden synchronization.
186. Optimizer must not introduce hidden I/O.
187. Optimizer must not introduce hidden panic paths without semantic justification.
188. Optimization must preserve program termination behavior within language-defined semantics.
189. Optimization must preserve allowed concurrency behaviors.
190. Optimization must preserve allowed memory behaviors.
191. Optimization must preserve ABI behavior at public boundaries.
192. Optimization must preserve FFI contracts.
193. Optimization must preserve native artifact correctness.
194. Every critical transformation must be isolatable for miscompilation forensics.
195. Every critical transformation must be disableable for differential testing.
196. The optimizer must support transformation replay.
197. The optimizer must support transformation provenance queries.
198. The optimizer must support `why_applied` and `why_rejected`.
199. The optimizer must be capable of producing evidence consumable by `552`.
200. **Final invariant:** mọi optimization transformation của Axiom chỉ được phép thay đổi **representation và execution strategy**, không được thay đổi semantic behavior; legality phải được chứng minh trước profitability, analysis phải luôn tương ứng với IR hiện tại, và mọi cache/parallelism/speculation chỉ là implementation optimization chứ không phải nguồn semantics.

**BOOTSTRAP-560: LOCKED.**

---

# NEXT — BOOTSTRAP-561

## COMPILER CODE GENERATION 3.0 — INSTRUCTION SELECTION, GLOBAL ISel, MACHINE IR, REGISTER ALLOCATION, SCHEDULING, PROLOGUE/EPILOGUE & VERIFIED NATIVE LOWERING

`561` sẽ tiếp tục từ optimized MIR xuống machine code, khóa phần **native backend thực sự**:

```text id="t9c4m2"
Optimized MIR
     │
     ▼
Target Lowering
     │
     ▼
Machine IR
     │
     ├── Instruction Selection
     ├── Legalization
     ├── Addressing-mode formation
     ├── Register constraints
     ├── Calling-convention lowering
     │
     ▼
Register Allocation
     │
     ├── Live intervals
     ├── Spill / reload
     ├── Coalescing
     └── Register classes
     │
     ▼
Machine Scheduling
     │
     ├── latency
     ├── throughput
     ├── dependency
     └── resource pressure
     │
     ▼
Prologue / Epilogue
     │
     ▼
Machine Peephole
     │
     ▼
Relaxation / Fixups
     │
     ▼
Machine Encoder
     │
     ▼
Object File
```

Các điểm sẽ khóa sâu:

- Machine IR;
- target-independent vs target-specific lowering;
- instruction selection;
- legalization;
- pattern matching;
- addressing modes;
- register classes;
- register constraints;
- SSA → machine representation;
- physical register assignment;
- linear scan vs graph/coloring allocator;
- live intervals/live ranges;
- register coalescing;
- spilling/reloading;
- rematerialization;
- register pressure;
- calling convention lowering;
- prologue/epilogue;
- stack frame layout;
- callee/caller-saved registers;
- stack alignment;
- red zone;
- shadow space;
- tail calls;
- shrink wrapping;
- machine scheduling;
- instruction latency/throughput;
- CPU pipeline/resource model;
- peephole optimization;
- branch relaxation;
- literal pools;
- constant materialization;
- TLS addressing;
- PIC/PIE;
- GOT/PLT;
- Windows/ELF/Mach-O relocation constraints;
- debug/unwind preservation;
- machine-level translation validation;
- integration trực tiếp với `420`, `421`, `438`, `440`, `552`, `560`.

**NEXT TASK: BOOTSTRAP-561.**