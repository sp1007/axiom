# BOOTSTRAP-574 — COMPILER SYMBOLIC EXECUTION 2.0
## ABSTRACT INTERPRETATION, PATH CONSTRAINTS, SYMBOLIC VALUES, RANGE PROOF, SAFETY PROOF & BUG FINDING

**Trạng thái: COMPLETED / LOCKED**

`574` xây dựng tầng **Symbolic Analysis / Proof Engine** trên nền `571 Dataflow + 572 Static Analysis + 573 Effect System`.

Mục tiêu không phải biến Axiom thành theorem-proving language. Mục tiêu là dùng symbolic reasoning **có giới hạn** để chứng minh những property thực dụng của compiler:

- bounds;
- nullability;
- arithmetic safety;
- initialization;
- unreachable code;
- switch/match conditions;
- division-by-zero;
- shift validity;
- array/slice access;
- một số resource properties;
- một số security flows.

---

# 574.1. Architecture

```text
                         MIR + CFG
                            │
                            ▼
                    571 Dataflow Facts
                            │
                            ▼
                   572 Static Analysis
                            │
                            ▼
                    573 Effect Summary
                            │
                            ▼
                  Symbolic Analysis Engine
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
 Abstract Values       Path Constraints      Memory Model
        │                   │                   │
        ├─ Constant         ├─ Equality        ├─ Regions
        ├─ Range            ├─ Inequality      ├─ Alias
        ├─ Nullability      ├─ Boolean         └─ Loads/Stores
        ├─ Bitmask          └─ Relations
        └─ Congruence
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    Proof / Counterexample
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
           Proven         Possible        Unknown
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                   Diagnostic Engine 569
```

---

# 574.2. Không phải theorem prover

Symbolic engine chỉ phải chứng minh các property nằm trong supported abstract domains.

Không yêu cầu chứng minh mọi mệnh đề toán học.

---

# 574.3. Abstract state

Mỗi program point có:

```text
AbstractState {
    values
    memory
    path_constraints
    effects
    resources
    provenance
}
```

---

# 574.4. Symbolic value

Một value có thể biểu diễn:

```text
Concrete(42)
Symbolic(x)
Range(0..100)
Unknown
```

---

# 574.5. Symbolic expression

Canonical expression tree:

```text
Add
Sub
Mul
Div
Mod
And
Or
Xor
Shl
Shr
Neg
Compare
Select
```

---

# 574.6. Expression normalization

Equivalent expressions phải canonicalize khi có thể.

Ví dụ:

```text
x + 0
```

→ `x`.

---

# 574.7. Constant propagation

Nếu expression chắc chắn constant, engine collapse thành constant.

---

# 574.8. Range domain

Range:

```text
[min, max]
```

có thể có inclusive/exclusive boundaries.

---

# 574.9. Integer range

Range phải respect bit width và signedness.

---

# 574.10. Overflow semantics

Symbolic engine phải tuân thủ chính xác semantics của từng arithmetic operation.

Không được tự giả định mọi integer operation là mathematical integer.

---

# 574.11. Wrapping arithmetic

Nếu operation wrapping, proof engine phải model modulo arithmetic.

---

# 574.12. Checked arithmetic

Nếu operation checked, overflow tạo failure path.

---

# 574.13. Saturating arithmetic

Saturating operation phải preserve saturation semantics.

---

# 574.14. Floating point

Float symbolic reasoning phải conservative hơn integer reasoning.

---

# 574.15. NaN

Floating-point domain phải có trạng thái NaN khi cần.

---

# 574.16. Infinity

`+∞/-∞` phải được model khi analysis hỗ trợ.

---

# 574.17. Negative zero

IEEE semantics phải được preserve khi relevant.

---

# 574.18. Bitmask domain

Engine có thể track known bits:

```text
known_zero
known_one
unknown_bits
```

---

# 574.19. Congruence domain

Integer có thể track:

```text
x ≡ r (mod m)
```

để hỗ trợ alignment/index proofs.

---

# 574.20. Nullability domain

Re-use:

```text
DefinitelyNull
DefinitelyNonNull
MaybeNull
Unknown
```

từ `572`.

---

# 574.21. Initialization domain

Re-use initialization facts từ `572`.

---

# 574.22. Resource domain

Re-use resource states từ `572`.

---

# 574.23. Alias domain

Re-use alias facts từ `571/572`.

---

# 574.24. Path constraint

Path condition mô tả điều kiện để execution tới program point.

---

# 574.25. Constraint types

Hỗ trợ tối thiểu:

```text
x == y
x != y
x < y
x <= y
x > y
x >= y
x ∈ range
boolean predicates
```

---

# 574.26. Boolean constraints

Engine track boolean expressions khi chúng có thể giúp refinement.

---

# 574.27. Branch refinement

```text
if x > 10
```

trên true branch:

```text
x ∈ [11, MAX]
```

nếu integer semantics phù hợp.

---

# 574.28. False branch

False branch:

```text
x <= 10
```

---

# 574.29. Compound condition

```text
if x > 0 && x < 10
```

→ intersection của constraints.

---

# 574.30. OR condition

OR tạo disjunction nếu engine budget cho phép.

---

# 574.31. Disjunction budget

Engine phải giới hạn số path/disjunct.

---

# 574.32. Path explosion

Không được enumerate vô hạn paths.

---

# 574.33. State merging

Khi paths trở nên tương đương, engine merge chúng.

---

# 574.34. Widening

Loop analysis dùng widening khi cần để đảm bảo convergence.

---

# 574.35. Narrowing

Có thể dùng bounded narrowing sau widening để lấy precision.

---

# 574.36. Fixed point

Loops phải đạt fixed point hoặc conservative approximation.

---

# 574.37. Loop invariants

Engine có thể infer simple invariants.

Ví dụ:

```text
0 <= i
i < n
```

---

# 574.38. Loop induction

Recognize induction variables:

```text
i = i + 1
```

---

# 574.39. Bounds proof

Array access:

```text
a[i]
```

được chứng minh safe nếu:

```text
0 <= i < length(a)
```

được suy ra.

---

# 574.40. Bounds failure

Nếu:

```text
i >= length(a)
```

được chứng minh → definite out-of-bounds.

---

# 574.41. Potential bounds failure

Nếu chỉ có possibility → warning/potential finding.

---

# 574.42. Runtime bounds check

Nếu runtime semantics có bounds check, optimizer có thể eliminate check khi proof đạt required confidence.

---

# 574.43. Proof provenance

Mọi optimization proof phải lưu provenance nội bộ:

```text
Fact A
+
Fact B
+
Constraint C
→
Proof P
```

---

# 574.44. Proof object

Proof object không nhất thiết phải lưu trong release binary.

---

# 574.45. Proof lifetime

Proof chỉ hợp lệ với MIR snapshot và target/config tương ứng.

---

# 574.46. Proof cache

Proof có thể cache nếu inputs identity không đổi.

---

# 574.47. Proof invalidation

MIR/semantic/dataflow change phải invalidate proof liên quan.

---

# 574.48. Arithmetic proof

Engine phải detect:

```text
division by zero
modulo by zero
invalid shift
overflow
underflow
```

theo semantics.

---

# 574.49. Division proof

Nếu denominator proven nonzero → safe.

---

# 574.50. Division unknown

Nếu denominator unknown → không được claim safe.

---

# 574.51. Shift proof

Shift amount phải nằm trong legal range.

---

# 574.52. Constant shift

Constant invalid shift → compile diagnostic.

---

# 574.53. Symbolic shift

Symbolic shift chỉ được prove safe khi constraint đủ mạnh.

---

# 574.54. Alignment proof

Pointer/reference alignment có thể được chứng minh bằng congruence/alignment facts.

---

# 574.55. Pointer safety

Raw pointer reasoning phải conservative.

---

# 574.56. Pointer provenance

Symbolic engine không được phá vỡ pointer provenance semantics.

---

# 574.57. Memory regions

Symbolic memory model sử dụng abstract regions:

```text
Stack
Heap
Global
TLS
External
Unknown
```

---

# 574.58. Memory load

Load tạo symbolic value từ region nếu value fact có thể xác định.

---

# 574.59. Memory store

Store cập nhật abstract memory state.

---

# 574.60. Memory merge

Conflicting stores tạo joined abstract state.

---

# 574.61. Alias-aware store

Store chỉ invalidate loads ở regions có thể alias.

---

# 574.62. Memory SSA integration

Engine dùng Memory SSA từ `571` để tránh full-memory invalidation không cần thiết.

---

# 574.63. Immutable memory

Immutable data cho phép symbolic state mạnh hơn.

---

# 574.64. Constant global

Constant global có thể inline vào symbolic state nếu semantics cho phép.

---

# 574.65. Volatile

Volatile access không được symbolic-fold như ordinary memory.

---

# 574.66. Atomic

Atomic access phải giữ synchronization semantics.

---

# 574.67. External calls

Unknown external call invalidate các facts mà effect summary cho phép mutate.

---

# 574.68. Effect integration

`573 EffectSummary` quyết định symbolic state nào có thể bị invalidated bởi call.

---

# 574.69. Pure call

Pure call có thể được symbolic-evaluate nếu body/value model available.

---

# 574.70. Read-only call

Read-only call có thể giữ write-related facts.

---

# 574.71. Unknown call

Unknown call phải conservative.

---

# 574.72. Function summary

Symbolic engine có thể sử dụng summaries:

```text
f(x) :
    requires C
    returns R
    effects E
```

---

# 574.73. Preconditions

Precondition có thể trở thành path constraint khi function contract trusted/verified.

---

# 574.74. Postconditions

Postcondition có thể refine return-value state.

---

# 574.75. Contract provenance

Contract phải phân biệt:

```text
CompilerProven
VerifiedContract
TrustedContract
UncheckedAssumption
```

---

# 574.76. Unchecked assumption

Không được dùng cho hard optimizer proof nếu policy không cho phép.

---

# 574.77. Function summaries

Summary có thể chứa symbolic relations:

```text
return >= 0
return == x + y
```

nếu được infer/prove.

---

# 574.78. Interprocedural symbolic analysis

Caller có thể import summary thay vì inline callee symbolic execution.

---

# 574.79. Context sensitivity

Hỗ trợ bounded call-site/context sensitivity.

---

# 574.80. Context budget

Giới hạn số context để tránh explosion.

---

# 574.81. Recursion

Recursive symbolic analysis dùng widening/fixed-point.

---

# 574.82. SCC

Recursive SCC được xử lý đồng bộ.

---

# 574.83. Whole-program

Whole-program mode có thể tận dụng closed-world call graph.

---

# 574.84. Open-world

Dynamic libraries/FFI làm summary conservative.

---

# 574.85. Security analysis

Taint facts từ `572` có thể được refined bằng symbolic predicates.

---

# 574.86. Path-sensitive taint

Ví dụ sanitizer condition có thể được chứng minh theo branch.

---

# 574.87. Security sink proof

Nếu tainted data chắc chắn reaches sink → finding confidence cao.

---

# 574.88. Security unknown

Incomplete path analysis → finding phải được đánh dấu potential/unknown.

---

# 574.89. Secret path

Secret flow có thể được refined bằng branch/assignment constraints.

---

# 574.90. Capability proof

Symbolic predicates có thể chứng minh capability presence/absence trong một số trường hợp.

---

# 574.91. Unreachable state

Nếu path constraints mâu thuẫn:

```text
x > 10
x < 5
```

path là unreachable.

---

# 574.92. Contradiction engine

Engine phải detect ít nhất contradiction của supported domains.

---

# 574.93. Unsat ≠ theorem proving

Chỉ cần domain-specific contradiction engine, không bắt buộc general-purpose SAT/SMT solver.

---

# 574.94. Optional solver

Axiom có thể cung cấp optional external/internal solver integration cho deep analysis.

---

# 574.95. Compiler dependency rule

Core native compiler không được phụ thuộc bắt buộc vào external SMT solver.

---

# 574.96. Solver boundary

Nếu solver không available → analyzer fallback conservative.

---

# 574.97. Solver result trust

Solver result phải bind với exact query/input snapshot.

---

# 574.98. Solver timeout

Timeout → Unknown.

---

# 574.99. Solver crash

Solver failure → Unknown + diagnostic telemetry, không làm compiler semantic result sai.

---

# 574.100. Counterexample

Khi proof thất bại nhưng violation path cụ thể tồn tại, engine có thể produce abstract counterexample.

---

# 574.101. Counterexample representation

```text
input constraints
→ branch decisions
→ operations
→ failing condition
```

---

# 574.102. Counterexample không nhất thiết executable

Abstract counterexample phải được ghi rõ nếu chưa concretized.

---

# 574.103. Concrete witness

Nếu engine có thể instantiate symbolic values, có thể produce concrete witness cho testing.

---

# 574.104. Test generation

Witness có thể được chuyển thành regression test input.

---

# 574.105. Fuzzing integration

Symbolic engine có thể seed fuzzer với hard-to-reach branch constraints.

---

# 574.106. Coverage guidance

Symbolic branch constraints có thể hướng coverage engine tới chưa-covered paths.

---

# 574.107. Path prioritization

Ưu tiên:

```text
safety-critical
newly changed
high-risk
uncovered
```

---

# 574.108. No arbitrary path search

Engine phải có bounded exploration.

---

# 574.109. Exploration budgets

Các budget:

```text
max_states
max_depth
max_constraints
max_solver_time
max_memory
```

---

# 574.110. Budget determinism

Cùng budget + snapshot phải cho deterministic analysis outcome.

---

# 574.111. Approximation levels

```text
fast
standard
precise
audit
```

---

# 574.112. Fast

Chủ yếu dùng existing dataflow facts.

---

# 574.113. Standard

Bounded symbolic refinement.

---

# 574.114. Precise

Path-sensitive analysis sâu hơn.

---

# 574.115. Audit

Whole-program + optional solver.

---

# 574.116. IDE mode

IDE ưu tiên latency.

---

# 574.117. CI mode

CI ưu tiên coverage/proof completeness.

---

# 574.118. Release mode

Release optimization dùng only proofs đạt required soundness.

---

# 574.119. Debug mode

Có thể giữ proof provenance/debug analysis data.

---

# 574.120. Optimizer interface

Optimizer query:

```text
can_prove(condition)?
```

không tự chạy logic riêng.

---

# 574.121. Proof API

```text
prove(condition) -> ProofResult
```

với:

```text
Proven
Disproven
Unknown
```

---

# 574.122. ProofResult

```text
ProofResult {
    status
    facts
    provenance
    cost
}
```

---

# 574.123. Optimization guard

Transformation yêu cầu proof phải fail-closed.

---

# 574.124. Fail-closed

Nếu proof `Unknown` → không áp dụng optimization phụ thuộc proof.

---

# 574.125. Safety checker

Safety checker cũng fail-closed.

---

# 574.126. Diagnostic checker

Diagnostic may report potential violation khi policy yêu cầu.

---

# 574.127. Proof composition

Proof có thể compose:

```text
P1 ∧ P2 → P3
```

---

# 574.128. Proof invalidation

Một input fact invalidated phải invalidate dependent proofs.

---

# 574.129. Proof DAG

Proof dependencies được lưu dưới dạng DAG.

---

# 574.130. Proof canonicalization

Equivalent proof facts phải canonicalize để cache hiệu quả.

---

# 574.131. Incremental proof

Source change chỉ invalidate affected proof nodes.

---

# 574.132. Parallel proof

Independent proof goals có thể chạy song song.

---

# 574.133. Deterministic proof output

Proof canonical representation không phụ thuộc scheduling.

---

# 574.134. Memory budget

Abstract states phải compact.

---

# 574.135. State interning

Repeated symbolic expressions/states có thể intern.

---

# 574.136. Hash-consing

Có thể dùng hash-consing cho expression DAG.

---

# 574.137. Expression DAG

Common symbolic subexpressions được share thay vì duplicate.

---

# 574.138. Canonical algebra

Chỉ áp dụng algebraic transformations đã chứng minh phù hợp với type/overflow/FP semantics.

---

# 574.139. Không tự giả định toán học

Ví dụ:

```text
x / x = 1
```

không hợp lệ khi `x == 0` có thể xảy ra.

---

# 574.140. Floating-point algebra

Không tự áp dụng real-number algebra cho IEEE floating point.

---

# 574.141. Integer algebra

Integer identities phải xét overflow semantics.

---

# 574.142. Signedness

Signed/unsigned comparisons phải preserve exact semantics.

---

# 574.143. Comparison normalization

Canonicalize comparison direction khi không thay đổi overflow/NaN semantics.

---

# 574.144. Pattern matching

Match patterns trở thành path constraints.

---

# 574.145. Enum discriminants

Known discriminant cho phép eliminate impossible branches.

---

# 574.146. Exhaustiveness

`430/429` type/match semantics vẫn là authority; `574` chỉ bổ sung unreachable-state proofs.

---

# 574.147. Struct invariants

Analyzer có thể track known field relationships.

---

# 574.148. Array lengths

Fixed-size array length là symbolic constant.

---

# 574.149. Slice lengths

Slice length là symbolic variable có range.

---

# 574.150. String length

String byte length có thể được track khi operations hỗ trợ.

---

# 574.151. UTF-8

Symbolic engine không được nhầm byte length với character count.

---

# 574.152. Unicode

Character validity chỉ được prove nếu operation semantics cung cấp đủ facts.

---

# 574.153. Resource proofs

Engine có thể prove:

```text
resource consumed exactly once
cleanup occurs on all normal exits
```

khi MIR/resource state đủ.

---

# 574.154. Double release proof

Known duplicate release → definite violation.

---

# 574.155. Leak analysis

Resource created but no cleanup/escape có thể trở thành leak finding.

---

# 574.156. Intentional leak

Explicit leak operation tạo provenance và không bị report như accidental leak.

---

# 574.157. Async resources

Await/suspend boundaries phải preserve resource facts.

---

# 574.158. Cancellation

Cancellation paths phải được symbolic modeled.

---

# 574.159. Panic cleanup

Panic path phải đi qua cleanup graph theo runtime semantics.

---

# 574.160. Concurrency

Symbolic engine sử dụng concurrency facts từ `572`.

---

# 574.161. Race proof

Symbolic predicates có thể giảm candidate race paths nhưng không thay thế race analysis.

---

# 574.162. Deadlock proof

Lock-order constraints có thể được symbolic refined.

---

# 574.163. Atomic reasoning

Atomic semantics không được simplify thành ordinary memory operations.

---

# 574.164. Effect-aware exploration

Pure paths có thể ưu tiên symbolic folding.

---

# 574.165. External effect barrier

External unknown effect tạo barrier cho symbolic assumptions.

---

# 574.166. IO-dependent predicates

Không được constant-fold dựa trên unknown external state.

---

# 574.167. Time-dependent behavior

Time/random/system state phải giữ symbolic unknown.

---

# 574.168. Environment

Environment-dependent values không được coi constant trừ khi build explicitly captures them.

---

# 574.169. Compile-time execution

Comptime expressions có thể được concrete-evaluate thay vì symbolic nếu deterministic.

---

# 574.170. Const proof

Const evaluator `431` là authority cho compile-time execution.

---

# 574.171. Cross-phase contract

`574` không duplicate const evaluator semantics.

---

# 574.172. Diagnostics

Mọi safety finding đi qua `569`.

---

# 574.173. Diagnostic confidence

Diagnostic có metadata:

```text
proof_level
analysis_profile
```

---

# 574.174. Proof levels

Canonical:

```text
Exact
Proven
HighConfidence
Potential
Unknown
```

---

# 574.175. Compiler errors

Chỉ `Exact/Proven` có thể trở thành hard semantic error nếu language rule yêu cầu.

---

# 574.176. Warnings

`Potential/HighConfidence` có thể warning tùy policy.

---

# 574.177. Unknown

Unknown không được biến thành false-positive hard error.

---

# 574.178. IDE integration

IDE có thể request proof cho selection/range/function.

---

# 574.179. Hover

Hover có thể hiển thị:

```text
x: Range<0..127>
```

nếu analysis available.

---

# 574.180. AI integration

AI semantic engine có thể query:

```text
prove(index < length)
why is this branch unreachable?
which assumption makes this access safe?
```

---

# 574.181. AI authority

AI không được tự tạo proof.

---

# 574.182. AI explanation

AI chỉ giải thích proof graph/result đã có.

---

# 574.183. Cache

Symbolic result cache key:

```text
MIRIdentity
AnalysisProfile
Target
FeatureSet
Goal
AnalyzerVersion
```

---

# 574.184. Cache independence

Cache hit/miss không được thay đổi semantic result.

---

# 574.185. Remote execution

Deep analysis có thể chạy distributed qua `567/568`.

---

# 574.186. Remote solver

Optional solver execution phải được sandbox/trust-boundary kiểm soát.

---

# 574.187. Result verification

Critical optimization proof có thể được independently checked bằng lightweight proof verifier.

---

# 574.188. Proof checker

Compiler nên có lightweight verifier cho proof objects quan trọng.

---

# 574.189. Proof checker không solver

Verifier không cần full symbolic solver.

---

# 574.190. Miscompilation defense

Nếu proof verifier reject proof → optimization không được áp dụng.

---

# 574.191. Differential testing

So sánh:

```text
optimized
vs
unoptimized
```

trên generated programs.

---

# 574.192. Symbolic fuzzing

Fuzz expressions, branches, loops, memory and integer edge cases.

---

# 574.193. Solver differential

Nếu optional solver được dùng, compare với internal abstract domain.

---

# 574.194. Known corpus

Corpus phải chứa:

```text
overflow
NaN
zero division
shift boundary
array boundary
aliasing
loops
recursion
panic
async
FFI
```

---

# 574.195. Performance

Common proofs phải chạy trong compiler hot path với low overhead.

---

# 574.196. Deep analysis isolation

Expensive symbolic execution không được làm compilation baseline chậm đáng kể.

---

# 574.197. Determinism

Cùng:

```text
MIR
target
profile
budget
analyzer version
```

→ cùng canonical proof results.

---

# 574.198. Soundness

Mọi transformation dựa trên symbolic proof chỉ được thực hiện khi proof engine cung cấp property đủ mạnh cho transformation đó.

---

# 574.199. Architecture invariant

`574` không trở thành một semantic authority riêng biệt. Nó là **proof/refinement layer** dùng facts từ:

```text
571 Dataflow
572 Static Analysis
573 Effect System
```

và trả kết quả về optimizer, analyzer, diagnostics, IDE và AI.

---

# 574.200. FINAL HARD INVARIANT

> **Axiom Symbolic Execution 2.0 phải là một proof engine có giới hạn, deterministic, incremental và fail-closed. Nó được phép dùng abstract interpretation, symbolic values, path constraints và optional solver để chứng minh các property thực dụng, nhưng không được biến compiler thành theorem prover bắt buộc. `Unknown` luôn khác `Proven`; timeout, thiếu metadata, external effects, floating-point uncertainty hoặc path explosion phải dẫn đến approximation/conservative result. Mọi optimization dựa trên proof phải có provenance và chỉ được áp dụng khi proof đủ mạnh cho transformation đó.**

**BOOTSTRAP-574: LOCKED.**

---

# NEXT — BOOTSTRAP-575

## COMPILER OPTIMIZATION SAFETY & TRANSFORMATION VERIFIER 2.0
### PROOF-CARRYING OPTIMIZATION, TRANSFORMATION CONTRACTS, PRE/POST CONDITIONS, MEMORY/ALIAS VALIDATION, SEMANTIC EQUIVALENCE & MISCOMPILATION PREVENTION

`575` sẽ nối trực tiếp `574` với `553 Optimization Framework 2.0`:

```text
                  MIR
                   │
             Optimization Pass
                   │
          ┌────────┴────────┐
          ▼                 ▼
   Transformation       Proof Goal
          │                 │
          └────────┬────────┘
                   ▼
             Proof Engine 574
                   │
             ┌─────┴─────┐
             ▼           ▼
          Proven       Unknown
             │           │
             ▼           ▼
          APPLY         REJECT
             │
             ▼
        Transformation
             │
             ▼
       Verifier / Checker
             │
             ▼
        Verified MIR
```

Trọng tâm `575` sẽ là tạo **hàng rào cuối cùng giữa optimizer và miscompilation**: mỗi optimization quan trọng phải khai báo transformation contract, preconditions, preserved properties và postconditions; verifier kiểm tra chúng trước khi native codegen tiếp tục.

**BOOTSTRAP-575: NEXT.**