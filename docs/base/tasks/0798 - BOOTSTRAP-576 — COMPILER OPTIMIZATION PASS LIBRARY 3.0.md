# BOOTSTRAP-576 — COMPILER OPTIMIZATION PASS LIBRARY 3.0
## SSA, GVN, SCCP, DCE, COPY PROPAGATION, INSTCOMBINE, MEMORY OPTIMIZATION, LOOP OPTIMIZATION, VECTORIZATION, INLINING & SIZE/SPEED SPECIALIZATION

**Trạng thái: COMPLETED / LOCKED**

`576` định nghĩa **bộ optimization passes thực tế** của Axiom và cách chúng phối hợp với:

- `553` — Optimization Framework 2.0
- `571` — Dataflow Engine
- `572` — Static Analysis
- `573` — Effect System
- `574` — Symbolic Proof Engine
- `575` — Transformation Verifier

Mục tiêu:

> Có một optimizer mạnh nhưng **không biến compiler thành một hệ thống hàng nghìn pass chạy tuần tự**. Pass được tổ chức theo tầng, dùng chung analysis, chỉ chạy khi có lợi ích, và mọi transformation quan trọng đều đi qua verification.

---

# 576.1. Optimization pipeline

```text id="9f2m8v"
                    Input MIR
                       │
                       ▼
                Canonicalization
                       │
                       ▼
                SSA Normalization
                       │
                       ▼
              ┌────────┴────────┐
              ▼                 ▼
         Scalar Opt          Memory Opt
              │                 │
              └────────┬────────┘
                       ▼
                 CFG Simplify
                       │
                       ▼
                  Loop Opt
                       │
                       ▼
                 Vectorization
                       │
                       ▼
                Interprocedural
                       │
                       ▼
                    LTO
                       │
                       ▼
                Late Scalar Opt
                       │
                       ▼
                 Lowering Prep
                       │
                       ▼
               Machine-oriented Opt
                       │
                       ▼
                 575 Verifier
```

---

# 576.2. Pass categories

```text id="8t5j1c"
Canonical
Scalar
CFG
Memory
Loop
Vector
IPO
LTO
Size
Machine
Cleanup
```

---

# 576.3. Pass contract

Mỗi pass phải implement contract `575`.

```text id="5h8w3p"
Pass {
    id
    version
    prerequisites
    analyses_required
    analyses_preserved
    invalidation
    cost_model
    transform
}
```

---

# 576.4. Pass manager

Pass manager chịu trách nhiệm:

- ordering;
- dependency;
- invalidation;
- budget;
- verification;
- parallelism.

---

# 576.5. Không hard-code toàn bộ pipeline

Pipeline phải configurable theo target/profile.

---

# 576.6. Optimization profiles

```text id="2u9v4x"
-O0
-O1
-O2
-O3
-Os
-Oz
-Ofast
```

`Ofast` chỉ là profile nếu Axiom định nghĩa rõ semantic relaxation.

---

# 576.7. `-O0`

Minimal transformations, ưu tiên debug và compile speed.

---

# 576.8. `-O1`

Cheap scalar/CFG optimizations.

---

# 576.9. `-O2`

Default production optimization.

---

# 576.10. `-O3`

Aggressive loop/vector/IPO optimization.

---

# 576.11. `-Os`

Optimize code size.

---

# 576.12. `-Oz`

Aggressively minimize generated code size.

---

# 576.13. `-Ofast`

Chỉ được thay đổi floating-point/other semantics khi programmer explicitly accepts relaxed semantics.

---

# 576.14. Cost model

Pass phải estimate:

```text id="1x6k7d"
compile_cost
code_size_delta
runtime_cost_delta
register_pressure
memory_pressure
```

---

# 576.15. Profitability

Transformation không nên chạy chỉ vì technically possible.

---

# 576.16. Canonicalization

Các MIR patterns tương đương được đưa về canonical form.

---

# 576.17. CFG simplification

Loại:

- empty block;
- redundant branch;
- unreachable block;
- redundant jump.

---

# 576.18. Block merging

Merge basic blocks khi không phá debug/exception semantics.

---

# 576.19. Critical edge handling

Pass sử dụng API chuẩn của `571`.

---

# 576.20. Dominator maintenance

Pass có thể update dominator tree incremental hoặc request recompute.

---

# 576.21. SSA normalization

MIR SSA phải giữ:

```text id="c7q8m2"
single definition
valid dominance
valid phi
```

---

# 576.22. Phi simplification

Phi có cùng operands → simplify.

---

# 576.23. Trivial phi elimination

```text id="f5j8z1"
phi(x,x,x) → x
```

---

# 576.24. Copy propagation

```text id="h4s0n8"
x = y
use(x)
```

→ use `y` khi safe.

---

# 576.25. Copy folding

Copies giữa compatible SSA values có thể eliminate.

---

# 576.26. Constant folding

```text id="a5j6q0"
2 + 3 → 5
```

theo exact type semantics.

---

# 576.27. Constant propagation

Known constants propagate qua CFG.

---

# 576.28. SCCP

Sparse Conditional Constant Propagation kết hợp:

```text id="0p4g2n"
constant lattice
+
reachability
```

---

# 576.29. SCCP result

Một value có:

```text id="9r2m5v"
Constant
Overdefined
Unknown
```

---

# 576.30. SCCP branch folding

Known branch condition → eliminate impossible edge.

---

# 576.31. Dead code elimination

Dead SSA computations được remove nếu effects cho phép.

---

# 576.32. Dead call elimination

Chỉ khi `573` chứng minh call không có observable effects.

---

# 576.33. Dead store elimination

Dựa trên Memory SSA + alias/effect facts.

---

# 576.34. Aggressive DCE

Có thể chạy ở `O3`, nhưng phải qua 575.

---

# 576.35. Instruction combining

Recognize instruction patterns:

```text id="m0v7x3"
add/sub
compare
select
mask
shift
bit operations
```

---

# 576.36. Algebraic simplification

Chỉ dùng identity phù hợp overflow/FP semantics.

---

# 576.37. Strength reduction

Ví dụ:

```text id="6q2r8c"
multiply by power-of-two
→ shift
```

chỉ khi semantics tương đương.

---

# 576.38. Negation simplification

Normalize nested negation khi safe.

---

# 576.39. Comparison simplification

Dựa trên known ranges.

---

# 576.40. Select simplification

```text id="z5v4p9"
select(true,a,b) → a
```

---

# 576.41. Boolean simplification

Preserve short-circuit and effects.

---

# 576.42. GVN

Global Value Numbering nhận diện equivalent computations.

---

# 576.43. GVN key

Key gồm:

```text id="v3n8d2"
opcode
type
operands
relevant flags
memory version
```

---

# 576.44. Memory GVN

Memory-dependent expressions phải include Memory SSA state.

---

# 576.45. GVN + alias

Equivalent loads chỉ được merge khi memory state equivalent.

---

# 576.46. PRE

Partial Redundancy Elimination có thể được dùng ở higher optimization levels.

---

# 576.47. PRE safety

Không introduce speculative observable effects.

---

# 576.48. Load forwarding

Store → subsequent load forwarding khi Memory SSA chứng minh.

---

# 576.49. Store-to-load forwarding

Phải respect alias, volatile, atomic.

---

# 576.50. Load elimination

Redundant load elimination dựa trên unchanged memory region.

---

# 576.51. Store elimination

Overwritten store có thể eliminate khi store không observable.

---

# 576.52. Memory promotion

Local memory có thể promote vào SSA.

---

# 576.53. Mem2Reg

Stack-local scalar allocations có thể đưa vào SSA.

---

# 576.54. Aggregate promotion

Aggregate fields có thể promote nếu phân tích cho phép.

---

# 576.55. Scalar replacement

Struct/aggregate có thể split thành scalars.

---

# 576.56. SROA

Scalar Replacement of Aggregates phải preserve:

```text id="w9k2a7"
layout
alignment
address observability
volatile behavior
```

---

# 576.57. Escape analysis integration

SROA dùng escape facts từ `572`.

---

# 576.58. Allocation sinking

Allocation có thể move gần nơi sử dụng nếu lifetime/effects cho phép.

---

# 576.59. Allocation elimination

Chỉ khi 575 chứng minh allocation không observable.

---

# 576.60. Stack promotion

Heap allocation → stack chỉ khi no escape.

---

# 576.61. Stack lifetime

Promotion phải preserve destructor/drop lifetime.

---

# 576.62. CFG cleanup

Sau scalar passes, CFG simplify chạy lại.

---

# 576.63. Loop discovery

Loop analysis từ `571`.

---

# 576.64. Loop canonicalization

Normalize preheader/latch/exit structures.

---

# 576.65. Loop invariant code motion

LICM dùng:

```text id="m4j1w9"
dominators
alias
effects
symbolic proof
```

---

# 576.66. LICM memory

Load chỉ move nếu memory dependency invariant.

---

# 576.67. LICM effects

IO/volatile/synchronization operations không được move tùy tiện.

---

# 576.68. Loop unswitching

Invariant condition có thể tách loop.

---

# 576.69. Unswitch profitability

Chỉ thực hiện khi expected benefit > code-size cost.

---

# 576.70. Loop peeling

Peel iterations để simplify boundary conditions.

---

# 576.71. Loop rotation

Canonical loop shape để hỗ trợ later optimization.

---

# 576.72. Loop deletion

Loop có thể remove nếu trip count proven zero hoặc body unobservable.

---

# 576.73. Infinite loop

Không được loại bỏ loop chỉ vì compiler không thấy exit nếu loop có observable behavior.

---

# 576.74. Loop invariant detection

Dùng SSA + dependency graph.

---

# 576.75. Induction variable

Recognize:

```text id="x7g4p1"
i = i + stride
```

---

# 576.76. Induction simplification

Derived induction variables có thể eliminate.

---

# 576.77. Strength reduction in loops

Expensive repeated operations có thể convert sang incremental computation.

---

# 576.78. Loop bounds

Use symbolic range proof `574`.

---

# 576.79. Bounds-check elimination

Repeated array bounds checks có thể eliminate khi loop invariant proves safety.

---

# 576.80. Loop unrolling

Unroll factor phụ thuộc:

```text id="0y5j7p"
trip count
code size
register pressure
target
profile
```

---

# 576.81. Full unroll

Chỉ khi trip count small/known và profitable.

---

# 576.82. Partial unroll

Cho unknown trip count.

---

# 576.83. Runtime remainder

Partial unroll phải preserve remainder iterations.

---

# 576.84. Loop vectorization

Vectorizer kiểm tra:

```text id="8h3x0c"
dependencies
alias
alignment
trip count
effects
target ISA
```

---

# 576.85. Dependence analysis

Memory dependence là prerequisite.

---

# 576.86. Alias uncertainty

`MayAlias` có thể block vectorization hoặc require runtime versioning.

---

# 576.87. Runtime alias checks

Có thể generate runtime checks nếu profitable.

---

# 576.88. Runtime versioning

```text id="4m8n2z"
if no_alias:
    vector_loop
else:
    scalar_loop
```

---

# 576.89. Versioning correctness

Hai versions phải semantic-equivalent.

---

# 576.90. SIMD width

Target backend cung cấp legal vector widths.

---

# 576.91. CPU feature

Vectorization phụ thuộc target CPU feature set.

---

# 576.92. Multi-versioning

Có thể generate:

```text id="x1c6v7"
baseline
SSE/AVX-like
advanced vector
```

tùy target.

---

# 576.93. Runtime dispatch

Dispatch condition phải được compiler/ABI support.

---

# 576.94. CPU dispatch correctness

Mỗi version chỉ được execute khi target feature phù hợp.

---

# 576.95. Vector reduction

Support sum/min/max/reduction khi semantics cho phép.

---

# 576.96. Floating reduction

FP reassociation chỉ khi floating-point policy cho phép.

---

# 576.97. Gather/scatter

Có thể dùng nếu target ISA hỗ trợ và cost model cho phép.

---

# 576.98. Vectorization + effects

Loop có IO/synchronization effects thường không vectorize.

---

# 576.99. Interprocedural optimization

IPO gồm:

```text id="x3b9c1q"
inlining
devirtualization
constant propagation
specialization
dead function elimination
function cloning
```

---

# 576.100. Inlining

Inliner sử dụng cost model.

---

# 576.101. Inline threshold

Phụ thuộc:

```text id="7v2c9x"
caller hotness
callee size
effects
loop context
code-size profile
```

---

# 576.102. Hot/cold

PGO data có thể influence inlining profitability.

---

# 576.103. Recursive inlining

Bounded depth.

---

# 576.104. Never infinite inline

Recursive SCC phải có hard budget.

---

# 576.105. Always-inline

Explicit annotation có thể yêu cầu inlining nhưng compiler vẫn phải preserve correctness.

---

# 576.106. Never-inline

Explicit annotation có thể cấm inlining.

---

# 576.107. Devirtualization

Resolve dynamic dispatch khi target set proven.

---

# 576.108. Trait specialization

Generic/trait call có thể specialize nếu implementation known.

---

# 576.109. Function cloning

Clone function cho specialized input facts.

---

# 576.110. Constant specialization

Known parameter constants có thể tạo specialized version.

---

# 576.111. Clone budget

Không tạo explosion số function versions.

---

# 576.112. Dead function elimination

Unreachable internal functions có thể remove.

---

# 576.113. Public function preservation

Externally visible symbols không được remove nếu ABI contract yêu cầu.

---

# 576.114. Linkage

LTO phải respect symbol visibility/linkage.

---

# 576.115. Whole-program DCE

Closed-world build có thể remove unused private/export-unreachable code.

---

# 576.116. LTO

Link-time optimizer hoạt động trên cross-module IR.

---

# 576.117. LTO identity

Modules phải có compatible:

```text id="w0m5n2"
compiler version
IR version
ABI
target
optimization semantics
```

---

# 576.118. LTO cache

Unchanged module summaries được reuse.

---

# 576.119. Cross-module GVN

Chỉ khi memory/effect state có đủ proof.

---

# 576.120. Cross-module constant propagation

Public/internal visibility rules phải được respect.

---

# 576.121. Whole-program devirtualization

Closed-world assumption required.

---

# 576.122. Function import/export

LTO không được phá native symbol contract.

---

# 576.123. Thin-LTO-like mode

Axiom có thể support summary-driven LTO để giảm memory.

---

# 576.124. Summary index

Index chứa:

```text id="4g9p6y"
calls
effects
hotness
size
types
visibility
```

---

# 576.125. Distributed LTO

Summary analysis có thể phân tán theo `567/568`.

---

# 576.126. Size optimization

Size optimizer ưu tiên:

```text id="0s6c3q"
DCE
merge
tail merging
outlining
compact instruction selection
```

---

# 576.127. Tail merging

Common suffixes có thể share.

---

# 576.128. Function outlining

Cold/large code có thể tách thành helper.

---

# 576.129. Outlining correctness

Must preserve:

```text id="2y4n8b"
ABI
stack
cleanup
debug
effects
```

---

# 576.130. Identical Code Folding

ICF có thể merge functions khi semantic/linkage rules cho phép.

---

# 576.131. ICF safety

Function address identity phải được xem xét.

---

# 576.132. Address-sensitive functions

Nếu function address observable, aggressive ICF có thể bị cấm.

---

# 576.133. Tail call optimization

Tail call được áp dụng khi ABI/stack/effect semantics cho phép.

---

# 576.134. Tail recursion

Có thể lower thành loop nếu semantic equivalence chứng minh.

---

# 576.135. Peephole optimization

Late MIR/MachineIR peephole dùng target-specific rules.

---

# 576.136. Instruction combine

Combine instructions thành target idioms.

---

# 576.137. Target cost model

Target backend cung cấp latency/throughput/code-size estimates.

---

# 576.138. Register pressure

Pass phải account register pressure.

---

# 576.139. Spill awareness

Transformation làm tăng spill cost có thể bị reject.

---

# 576.140. Machine-aware loop optimization

Late loop decisions có thể consult target register/vector cost.

---

# 576.141. Instruction scheduling

Scheduling thuộc backend nhưng có thể nhận optimization metadata.

---

# 576.142. Branch optimization

Hot branches có thể được layout lại.

---

# 576.143. Basic-block layout

Optimize fall-through paths.

---

# 576.144. Branch probability

Profile data có thể guide layout.

---

# 576.145. Cold block placement

Cold blocks có thể đưa khỏi hot path.

---

# 576.146. Code alignment

Alignment optimization phải cost-aware.

---

# 576.147. I-cache awareness

Code layout có thể tối ưu instruction-cache locality.

---

# 576.148. Size/speed tradeoff

Mọi aggressive optimization phải consult profile.

---

# 576.149. PGO

PGO data không được trở thành semantic assumption.

---

# 576.150. PGO invalidation

Profile mismatch không được silently reuse.

---

# 576.151. Deoptimization

Axiom native compiler không yêu cầu JIT-style deoptimization.

---

# 576.152. Speculative optimization

Nếu speculative runtime check được tạo, fallback path phải tồn tại.

---

# 576.153. Guard elimination

Guards chỉ được remove khi symbolic proof chứng minh condition.

---

# 576.154. Guard hoisting

Guard có thể move nếu effect/control semantics cho phép.

---

# 576.155. Profile-guided specialization

Hot type/value patterns có thể tạo specialized version.

---

# 576.156. Specialization correctness

Generic fallback phải remain valid.

---

# 576.157. Compile-time specialization

Const/comptime values được xử lý bởi `431`.

---

# 576.158. Cross-feature specialization

CPU features, target features và generic type properties phải có explicit feature identity.

---

# 576.159. Pass interaction

Pass manager phải tránh oscillation:

```text id="0o8t5f"
A transforms X→Y
B transforms Y→X
```

---

# 576.160. Canonical form

Các pass phải converge về canonical representation.

---

# 576.161. Iteration budget

Optimization fixpoint loops có hard iteration limit.

---

# 576.162. No infinite optimization

Compiler phải terminate ngay cả khi pass profitability/canonicalization có bug.

---

# 576.163. Pass pipeline adaptivity

Pass manager có thể skip pass nếu analysis dự đoán không có opportunity.

---

# 576.164. Opportunity detection

Cheap analysis trước expensive pass.

---

# 576.165. Lazy analysis

Analysis chỉ compute khi pass yêu cầu.

---

# 576.166. Shared analysis

Các pass reuse `571/572/573/574` results.

---

# 576.167. Analysis cache

Không recompute cùng fact trong cùng snapshot.

---

# 576.168. Parallel passes

Independent functions/pass instances có thể chạy song song.

---

# 576.169. Determinism

Parallel optimization phải canonicalize output.

---

# 576.170. Transactional passes

```text id="8u5n4r"
snapshot
→ candidate
→ proof
→ verify
→ commit
```

---

# 576.171. Rollback

Failed verification → discard candidate.

---

# 576.172. Pass statistics

Record:

```text id="6k7x1q"
attempted
applied
rejected
cost
code-size delta
```

---

# 576.173. Rejection reasons

```text id="3j4w9e"
not-profitable
proof-failed
unsupported
budget
invalidated
```

---

# 576.174. Optimization remarks

Compiler có thể expose machine-readable optimization remarks.

---

# 576.175. IDE integration

IDE có thể query optimization remarks trong debug/profile builds.

---

# 576.176. AI integration

AI có thể hỏi:

```text id="j5z0h6"
why was this code not vectorized?
why was this function not inlined?
which proof prevented elimination?
```

---

# 576.177. AI explanation boundary

AI không được sửa optimization decision trực tiếp.

---

# 576.178. User control

Advanced users có thể configure pass profile.

---

# 576.179. Per-function attributes

Có thể support:

```text id="5m8x0k"
optimize(speed)
optimize(size)
noinline
alwaysinline
novector
```

nếu language ABI/spec cho phép.

---

# 576.180. Attribute semantics

Attributes là constraints/hints; không được làm invalid transformation hợp lệ.

---

# 576.181. Hard constraint

`noinline` là hard constraint nếu language định nghĩa.

---

# 576.182. Optimization hint

Speed/size preference là soft hint.

---

# 576.183. Debug preservation

Optimization phải maintain source mapping sufficiently.

---

# 576.184. Variable location

SSA optimization phải update debug variable locations.

---

# 576.185. Unwind preservation

Control-flow transformations phải preserve unwind correctness.

---

# 576.186. Panic paths

Optimization phải preserve panic/unwind behavior.

---

# 576.187. Async state machines

Optimization có thể simplify generated async state machine nhưng phải preserve suspension semantics.

---

# 576.188. Concurrency

Không được reorder operations across synchronization barriers mà không có proof.

---

# 576.189. Atomic optimization

Atomic operations chỉ được transform khi memory-order semantics preserved.

---

# 576.190. Security-sensitive code

Security contracts từ `575` có thể restrict optimization.

---

# 576.191. Constant-time

Constant-time regions có thể disable transformations gây data-dependent timing.

---

# 576.192. Benchmark suite

Optimization suite phải cover:

```text id="q4m9v6"
scalar
memory
loops
SIMD
IPO
LTO
size
debug
concurrency
FFI
```

---

# 576.193. Correctness corpus

Mỗi pass phải test:

```text id="0h3c7r"
positive
negative
boundary
overflow
alias
effect
panic
atomic
```

---

# 576.194. Differential testing

Compare optimized/unoptimized execution.

---

# 576.195. Translation validation

Critical passes có thể được translation-validated.

---

# 576.196. Fuzzing

Random MIR + random pass pipelines phải không produce semantic mismatch.

---

# 576.197. Performance regression

Mỗi pass có benchmark trước/sau.

---

# 576.198. Code-size regression

Binary size phải được tracked.

---

# 576.199. FINAL HARD INVARIANT

> **Axiom Optimization Pass Library phải là một hệ thống tầng hóa, demand-driven, cost-aware và deterministic. Không pass nào được tự tạo semantic assumptions; mọi transformation quan trọng phải sử dụng canonical analysis facts và proof/verification của `571–575`. Optimization có thể bị bỏ qua vì cost, budget, unsupported analysis hoặc thiếu proof mà không ảnh hưởng correctness. Cache, parallelism, PGO, LTO, target-specific optimization và speculative transformation chỉ được phép thay đổi cách tạo code, không được thay đổi defined observable behavior.**

# 576.200. LOCK

**BOOTSTRAP-576: LOCKED.**

---

# NEXT — BOOTSTRAP-577

## COMPILER REGISTER ALLOCATION 3.0
### SSA DESTRUCTION, LIVE-RANGE ANALYSIS, LINEAR SCAN, GRAPH/COLORING ALLOCATION, COALESCING, SPILLING, REMATERIALIZATION, CALL-CLOBBERED REGISTERS & TARGET-AWARE REGISTER ASSIGNMENT

`577` sẽ đi sâu vào phần cuối của backend trước machine instruction emission:

```text id="f2m6y8"
Optimized MIR
      │
      ▼
Machine IR
      │
      ▼
Liveness / Live Intervals
      │
      ▼
Register Allocation
      │
 ┌────┴─────────┐
 ▼              ▼
Registers      Spills
 │              │
 └──────┬───────┘
        ▼
   SSA Destruction
        │
        ▼
   Machine IR Final
        │
        ▼
 Prologue/Epilogue
        │
        ▼
 Instruction Scheduling
        │
        ▼
 Machine Encoding
```

Điểm quan trọng của `577` sẽ là **Axiom không nên chỉ có một register allocator**. Compiler cần allocator nhiều tầng:

```text
fast allocator
balanced allocator
aggressive allocator
size allocator
```

và tự chọn dựa trên function complexity, register pressure, optimization profile và target CPU — nhưng tất cả đều phải tạo ra machine code tương đương và được backend verifier kiểm tra.

**BOOTSTRAP-577: NEXT.**