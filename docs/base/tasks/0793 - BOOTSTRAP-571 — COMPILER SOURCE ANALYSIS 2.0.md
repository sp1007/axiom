# BOOTSTRAP-571 — COMPILER SOURCE ANALYSIS 2.0
## CONTROL-FLOW GRAPH, DATAFLOW ENGINE, DEF-USE CHAINS, CONSTANT PROPAGATION, REACHABILITY, DEAD CODE & FLOW-SENSITIVE SEMANTICS

**Trạng thái: COMPLETED / LOCKED**

`571` xây dựng nền tảng **CFG + dataflow dùng chung** cho Axiom. Đây là infrastructure cấp compiler, không phải một optimization pass đơn lẻ.

Mục tiêu:

> **Mọi subsystem cần biết “giá trị/trạng thái nào có thể tồn tại tại vị trí này?” phải dùng chung một Dataflow Engine và cùng semantic facts, thay vì tự xây các CFG/dataflow implementation khác nhau.**

---

# 571.1. Vị trí trong compiler

```text id="5e0d6g"
AST
 ↓
HIR
 ↓
Type / Trait / Ownership
 ↓
MIR
 ↓
┌──────────────────────────────┐
│ SOURCE ANALYSIS 2.0          │
│                              │
│ CFG                          │
│ Dominators                   │
│ Postdominators               │
│ Def-Use                      │
│ Dataflow                     │
│ Reachability                 │
│ Constant Propagation         │
│ Liveness                     │
│ Flow Facts                   │
└──────────────┬───────────────┘
               │
       ┌───────┼────────┐
       ▼       ▼        ▼
 Optimization Analyzer IDE/AI
```

---

# 571.2. MIR là analysis authority

CFG và dataflow được xây trên MIR sau semantic lowering.

Không phân tích AST trực tiếp cho các optimization correctness-critical.

---

# 571.3. Analysis snapshot

Mọi analysis gắn với:

```text id="u4qkg0"
SemanticSnapshotId
MIRVersion
Target
OptimizationLevel
AnalysisConfig
```

---

# 571.4. CFG

Control Flow Graph:

```text id="zv1gzu"
Entry
  │
  ▼
Block A
 ├──────► Block B
 │
 └──────► Block C
              │
              ▼
           Block D
              │
              ▼
             Exit
```

---

# 571.5. Basic block

Basic block là sequence instruction với:

- một entry;
- không có branch vào giữa;
- terminator ở cuối.

---

# 571.6. Terminator

Core terminators:

```text id="31y0s2"
jump
branch
switch
return
throw/panic
unreachable
call-diverge
```

---

# 571.7. CFG node identity

Mỗi block có stable `BlockId` trong một MIR version.

---

# 571.8. CFG edge

```text id="8q7x8k"
Edge {
    from
    to
    kind
    condition
}
```

---

# 571.9. Edge kinds

```text id="bpp1v9"
Normal
True
False
SwitchCase
Default
Exceptional
Cleanup
AsyncResume
AsyncSuspend
```

---

# 571.10. Exceptional edges

Nếu target/runtime hỗ trợ unwind, CFG có thể biểu diễn exceptional control flow.

---

# 571.11. Cleanup edges

`defer`, destructor/drop hoặc cleanup semantics phải được biểu diễn explicit trong analysis CFG.

---

# 571.12. Async CFG

Async lowering có thể tạo state-machine CFG.

Analysis phải distinguish suspension edges.

---

# 571.13. Synthetic blocks

Compiler-generated cleanup blocks phải giữ provenance.

---

# 571.14. Entry block

Mỗi function có exactly một logical entry block.

---

# 571.15. Exit

Multiple return sites có thể được canonicalize về logical exit cho analysis.

---

# 571.16. Unreachable

Block sau unconditional terminator được đánh dấu unreachable.

---

# 571.17. Reachability

Forward reachability từ entry là canonical reachable analysis.

---

# 571.18. Dead blocks

Unreachable blocks không được coi là executable.

---

# 571.19. Dead code diagnostics

Dead-code analysis có thể tạo diagnostic `warning`, nhưng optimization semantics độc lập.

---

# 571.20. CFG normalization

CFG có thể được normalize trước dataflow.

---

# 571.21. CFG normalization không đổi semantics

Mọi transformation CFG phải semantics-preserving.

---

# 571.22. Critical edge

Engine phải có API phát hiện critical edges.

---

# 571.23. Critical-edge splitting

Pass có thể yêu cầu split critical edge.

---

# 571.24. Edge metadata

Original/source provenance phải survive edge transformations.

---

# 571.25. Dominator tree

Engine xây dominator tree.

---

# 571.26. Dominance

Block A dominates B nếu mọi path từ Entry tới B đi qua A.

---

# 571.27. Immediate dominator

Mỗi reachable block khác Entry có immediate dominator.

---

# 571.28. Dominance frontier

Engine expose dominance frontier cho SSA construction/optimization.

---

# 571.29. Postdominator

Engine hỗ trợ post-dominator analysis.

---

# 571.30. Immediate postdominator

Reachable blocks có immediate postdominator khi graph structure cho phép.

---

# 571.31. Unreachable dominance

Unreachable nodes không được tạo false dominance facts.

---

# 571.32. Loop detection

CFG engine expose natural/irreducible loop information.

---

# 571.33. Back edge

Back edge được xác định dựa trên dominance relation.

---

# 571.34. Loop header

Loop header là target của back edge theo normalized CFG.

---

# 571.35. Loop nesting

Loops có thể tạo nesting tree.

---

# 571.36. Irreducible CFG

Engine phải hỗ trợ irreducible control flow thay vì giả định mọi loop đều reducible.

---

# 571.37. Loop exits

Mỗi loop có thể query exit edges.

---

# 571.38. Loop preheader

Optimization pass có thể request canonical preheader.

---

# 571.39. CFG queries

API tối thiểu:

```text id="m8m1dq"
successors(block)
predecessors(block)
reachable(block)
dominates(a,b)
postdominates(a,b)
loop_of(block)
```

---

# 571.40. Immutable CFG view

Analysis clients mặc định nhận read-only CFG view.

---

# 571.41. CFG mutation

Mutation chỉ thông qua controlled transformation API.

---

# 571.42. CFG version

Mỗi mutation tạo mới CFG version hoặc invalidates dependent analyses.

---

# 571.43. Analysis invalidation

Pass phải khai báo analysis nào bị invalidated.

---

# 571.44. Analysis preservation

Pass có thể declare:

```text id="yupjzo"
preserves CFG
preserves Dominators
preserves Liveness
```

---

# 571.45. Incorrect preservation

Compiler debug mode phải detect pass khai báo preservation sai.

---

# 571.46. SSA relationship

MIR/LIR SSA facts được dataflow engine consume.

---

# 571.47. Def

Definition là instruction tạo/ghi giá trị.

---

# 571.48. Use

Use là instruction đọc giá trị.

---

# 571.49. Def-Use chain

```text id="4n3n8d"
Def(v)
 ↓
Use1
 ↓
Use2
```

---

# 571.50. Use-Def chain

Engine cũng support:

```text id="q8c8av"
Use → possible reaching Defs
```

---

# 571.51. SSA simplification

Trong SSA, mỗi SSA value có một canonical definition.

---

# 571.52. Phi

Phi nodes là merge definitions tại control-flow join.

---

# 571.53. Phi provenance

Phi phải retain incoming block/value mapping.

---

# 571.54. Memory SSA

Memory side effects có thể được biểu diễn bằng Memory SSA khi optimization cần.

---

# 571.55. Memory definitions

Stores/calls có thể tạo memory definitions.

---

# 571.56. Memory uses

Loads/calls có thể consume memory state.

---

# 571.57. Alias dependency

Memory SSA phải tôn trọng alias analysis hiện hành.

---

# 571.58. No unsafe assumption

Dataflow engine không được giả định non-aliasing nếu semantic model không chứng minh.

---

# 571.59. Dataflow lattice

Generic engine dựa trên lattice:

```text id="y4mrvw"
Bottom
  ↓
Facts
  ↓
Top
```

theo từng analysis.

---

# 571.60. Meet

Mỗi analysis định nghĩa meet operator.

---

# 571.61. Join

Nếu analysis cần join semantics, phải có deterministic operator.

---

# 571.62. Monotonicity

Dataflow transfer functions phải monotonic trong lattice của analysis.

---

# 571.63. Fixed point

Engine lặp đến fixed point.

---

# 571.64. Worklist

Worklist scheduler là implementation mặc định.

---

# 571.65. Reverse postorder

Forward analysis ưu tiên reverse-postorder traversal.

---

# 571.66. Backward analysis

Backward analysis ưu tiên reverse CFG traversal.

---

# 571.67. Convergence

Compiler phải detect pathological non-convergence.

---

# 571.68. Iteration limit

Có safety limit nhưng không được silently coi chưa hội tụ là valid result.

---

# 571.69. Widening

Các analysis có infinite domains phải hỗ trợ widening nếu cần.

---

# 571.70. Narrowing

Có thể hỗ trợ narrowing sau widening.

---

# 571.71. Sparse dataflow

SSA-compatible analyses ưu tiên sparse representation.

---

# 571.72. Dense dataflow

Dense bitset representation được dùng khi graph/value domain nhỏ hoặc dense analysis hiệu quả hơn.

---

# 571.73. Hybrid representation

Engine có thể chuyển sparse ↔ dense theo cost model.

---

# 571.74. Dataflow fact

Fact phải có canonical type.

---

# 571.75. Fact identity

Fact identity không phụ thuộc traversal order.

---

# 571.76. Deterministic fixed point

Cùng input graph phải tạo cùng final facts.

---

# 571.77. Constant propagation

Engine hỗ trợ constant propagation.

---

# 571.78. Constant domain

Tối thiểu:

```text id="t1n7d7"
Unknown
Constant(value)
Overdefined
```

---

# 571.79. Integer constants

Hỗ trợ fixed-width integer semantics của Axiom.

---

# 571.80. Boolean constants

`true/false` được propagate.

---

# 571.81. Enum constants

Known enum discriminant có thể propagate.

---

# 571.82. Pointer constants

Chỉ propagate nếu representation/target semantics chứng minh được.

---

# 571.83. Floating constants

Phải tôn trọng floating-point semantics và optimization flags.

---

# 571.84. NaN

NaN không được xử lý như ordinary numeric equality.

---

# 571.85. Signed zero

`+0` và `-0` phải preserve nếu floating semantics yêu cầu.

---

# 571.86. Overflow

Integer overflow semantics lấy từ Axiom type/operation rules.

---

# 571.87. Undefined overflow assumptions

Optimizer không được tự ý giả định overflow impossible nếu language không cho phép assumption đó.

---

# 571.88. Constant folding

Compile-time evaluator có thể fold expression.

---

# 571.89. Folding equivalence

Folded expression phải equivalent với runtime semantics.

---

# 571.90. Conditional propagation

Nếu condition known:

```text id="3y0kxn"
if true → unreachable false branch
```

---

# 571.91. Switch propagation

Known discriminant cho phép eliminate impossible cases.

---

# 571.92. Branch probability

Dataflow engine có thể expose branch probabilities từ profile.

---

# 571.93. Profile independence

Profile không được thay đổi semantic correctness.

---

# 571.94. Value range analysis

Engine có thể expose numeric ranges.

---

# 571.95. Range lattice

Ví dụ:

```text id="ap5dsp"
[min,max]
```

với bottom/unknown/overdefined.

---

# 571.96. Interval overflow

Range arithmetic phải kiểm soát integer overflow.

---

# 571.97. Nullability

Nếu Axiom type model có nullable values, dataflow có thể track:

```text id="n8qq54"
Null
NonNull
MaybeNull
```

---

# 571.98. Bounds facts

Array/slice index analysis có thể track known bounds.

---

# 571.99. Bounds safety

Bounds facts không được biến thành unchecked access nếu proof chưa đủ.

---

# 571.100. Initialization analysis

Engine track whether variable/value has been initialized.

---

# 571.101. Definite initialization

Use trước initialization phải được detect.

---

# 571.102. Partial initialization

Struct/aggregate có thể track field-level initialization.

---

# 571.103. Move state

Ownership model có thể expose flow facts:

```text id="t3xx6y"
Available
Moved
PartiallyMoved
Consumed
```

---

# 571.104. Move analysis

Move state phải phù hợp ownership rules `423`.

---

# 571.105. Drop state

Dataflow có thể track whether resource requires cleanup.

---

# 571.106. Double-drop

Compiler phải detect impossible/dangerous double cleanup khi semantics yêu cầu.

---

# 571.107. Defer flow

`defer` effects được đưa vào CFG cleanup model.

---

# 571.108. Resource flow

Resource state phải follow control-flow joins.

---

# 571.109. Join of ownership states

Ví dụ:

```text id="9x6r6a"
Available + Moved → MaybeMoved/ErrorState
```

theo ownership checker semantics.

---

# 571.110. No borrow checker dependency

Dataflow engine không yêu cầu Rust-style borrow checker.

---

# 571.111. Alias facts

Alias analysis có thể cung cấp:

```text id="1t6w0p"
NoAlias
MayAlias
MustAlias
Unknown
```

---

# 571.112. Alias analysis authority

Alias facts phải come from valid semantic/analysis proof.

---

# 571.113. Function summaries

Interprocedural analysis có thể dùng function summaries.

---

# 571.114. Summary

Summary có thể chứa:

```text id="qqk8gp"
reads
writes
returns
throws
allocates
frees
pure
noreturn
```

---

# 571.115. Purity

Pure function marking chỉ được sử dụng nếu compiler có proof/contract.

---

# 571.116. Noreturn

Noreturn functions tạo terminating CFG edges.

---

# 571.117. Side-effect summary

Optimizer không được remove call nếu side effects chưa chứng minh absent.

---

# 571.118. Call graph integration

Dataflow có thể query call graph.

---

# 571.119. Recursive functions

Interprocedural analysis phải support recursion.

---

# 571.120. SCC call analysis

Recursive call groups được phân tích bằng fixed point.

---

# 571.121. Context sensitivity

Engine có thể support:

```text id="0u3xid"
context-insensitive
limited context-sensitive
```

---

# 571.122. Complexity guard

Context sensitivity phải có budget.

---

# 571.123. Path sensitivity

Core engine hỗ trợ path facts ở mức bounded.

---

# 571.124. Path explosion

Không enumerate vô hạn paths.

---

# 571.125. Predicate facts

Conditions có thể tạo facts:

```text id="7l6q6h"
x == 0
x != 0
x < y
```

---

# 571.126. Branch refinement

True/false branch có thể refine facts.

---

# 571.127. Join

Conflicting path facts merge về conservative state.

---

# 571.128. Conservative analysis

Unknown phải được ưu tiên hơn unsafe assumption.

---

# 571.129. Dead code

Reachability + constant predicates có thể detect dead branches.

---

# 571.130. Dead variable

Liveness + def-use có thể detect unused values.

---

# 571.131. Dead store

Memory dataflow có thể detect overwritten stores khi alias proof đủ mạnh.

---

# 571.132. Dead call

Chỉ remove nếu call proven side-effect-free.

---

# 571.133. Dead allocation

Allocation removal phải xét destructor/resource semantics.

---

# 571.134. Dead cleanup

Cleanup không được remove nếu observable/resource semantics tồn tại.

---

# 571.135. Liveness

Backward analysis tính live values.

---

# 571.136. Live-in

Mỗi block có:

```text id="l3i7j7"
LiveIn
```

---

# 571.137. Live-out

Mỗi block có:

```text id="gqug0m"
LiveOut
```

---

# 571.138. Register allocation integration

Liveness được machine backend sử dụng.

---

# 571.139. Spill pressure

Liveness có thể feed register allocation cost model.

---

# 571.140. Interference

SSA liveness có thể tạo interference graph khi cần.

---

# 571.141. Memory liveness

Memory values có thể được track riêng.

---

# 571.142. Definite assignment

Language semantic checker có thể query initialization dataflow.

---

# 571.143. Uninitialized diagnostics

Diagnostic `569` nhận fact từ dataflow engine.

---

# 571.144. Flow-sensitive typing

Nếu type system có narrowing:

```text id="3gk6i8"
if x is T:
    x treated as T
```

fact được attach vào flow path.

---

# 571.145. Type refinement

Refinement phải được invalidate khi value có mutation/aliasing có thể thay đổi fact.

---

# 571.146. Mutation tracking

Assignment invalidates dependent value facts.

---

# 571.147. Function calls

Calls invalidate facts according to side-effect summary.

---

# 571.148. Unknown calls

Unknown external call phải conservatively invalidate affected facts.

---

# 571.149. Global state

Global mutation phải invalidate relevant global facts.

---

# 571.150. Thread interference

Concurrent shared state không được phân tích như single-threaded nếu synchronization proof không tồn tại.

---

# 571.151. Atomic flow

Atomic operations có semantic effects riêng.

---

# 571.152. Memory order

Dataflow optimization phải respect memory-order constraints.

---

# 571.153. Async suspension

Flow facts có thể thay đổi qua `await` nếu state có thể mutate concurrently.

---

# 571.154. Task boundary

Task spawn phải invalidate facts có thể escape/shared.

---

# 571.155. Actor boundary

Message send tạo ownership/dataflow boundary theo actor semantics.

---

# 571.156. Exception flow

Exceptional edges phải được đưa vào analyses yêu cầu them.

---

# 571.157. Panic flow

Panic/unwind có thể terminate path hoặc transfer tới cleanup/handler.

---

# 571.158. Error handling

`Result` pattern được phân tích như ordinary control flow.

---

# 571.159. Match analysis

Pattern matching có thể cung cấp exhaustiveness/reachability facts.

---

# 571.160. Exhaustiveness

Exhaustiveness checker sử dụng pattern-space facts.

---

# 571.161. Unreachable pattern

Pattern không bao giờ match có thể tạo warning.

---

# 571.162. Constant pattern

Known discriminants giúp simplify match.

---

# 571.163. Switch lowering

Pattern/match có thể lower thành switch CFG.

---

# 571.164. CFG ↔ source mapping

MIR block/instruction phải giữ source provenance.

---

# 571.165. Diagnostic span

Dataflow error phải map ngược về source span.

---

# 571.166. Explanation

Diagnostic có thể expose:

```text id="lhf0se"
definition
path
fact
conflict
```

---

# 571.167. IDE integration

IDE có thể query flow state tại source position.

---

# 571.168. AI integration

AI có thể query:

```text id="v2k9yr"
value state at location
possible values
reachable paths
why unreachable
why uninitialized
```

---

# 571.169. Flow query

Conceptual API:

```text id="b7v7s8"
flow_facts(function, location)
```

---

# 571.170. Analysis cache

Analysis result có thể cache theo:

```text id="8rps5q"
MIR identity
target
analysis kind
configuration
```

---

# 571.171. Dependency-aware invalidation

MIR mutation chỉ invalidate affected analysis results.

---

# 571.172. Query integration

Dataflow trở thành query kind trong Query Engine.

---

# 571.173. Parallel analysis

Independent functions có thể phân tích song song.

---

# 571.174. Function-level isolation

Intraprocedural analyses có thể execute độc lập.

---

# 571.175. Interprocedural scheduling

Call graph SCCs quyết định dependency order.

---

# 571.176. Deterministic parallel analysis

Parallel execution phải cho cùng final facts.

---

# 571.177. Memory efficiency

Bitsets, sparse maps và arena allocation được chọn theo domain size.

---

# 571.178. Large-function strategy

Function cực lớn không được tạo per-path object explosion.

---

# 571.179. Fact compression

Equivalent facts có thể intern/share.

---

# 571.180. Incremental block analysis

Chỉ block/region bị ảnh hưởng cần recompute khi có thể chứng minh.

---

# 571.181. Change frontier

Engine tính propagation frontier từ changed blocks.

---

# 571.182. Early convergence

Nếu new fact == old fact, propagation dừng.

---

# 571.183. Worklist priority

Worklist có thể ưu tiên:

```text id="n9b4d8"
changed blocks
loop headers
dominance frontier
```

---

# 571.184. Scheduling independence

Worklist ordering không được thay đổi fixed-point result.

---

# 571.185. Analysis composition

Một analysis có thể consume result của analysis khác.

---

# 571.186. Dependency declaration

Analysis phải khai báo required analyses.

---

# 571.187. Cyclic analysis dependencies

Cycle giữa analyses phải được explicit SCC/fixed-point model hoặc reject.

---

# 571.188. Analysis invalidation graph

Compiler duy trì dependency graph giữa analyses.

---

# 571.189. Analysis verification

Debug builds có thể recompute analysis bằng alternative algorithm để detect bugs.

---

# 571.190. Differential dataflow testing

Small CFGs được test bằng reference interpreter/naive implementation.

---

# 571.191. CFG fuzzing

Random CFG generation phải kiểm tra:

```text id="w3m6ra"
no crash
termination
dominance consistency
reachability consistency
```

---

# 571.192. Dataflow fuzzing

Random lattice/transfer tests kiểm tra convergence properties.

---

# 571.193. Semantic equivalence

Optimization using dataflow phải được checked against unoptimized execution.

---

# 571.194. Regression suite

Phải có regression tests cho:

- loops;
- branches;
- recursion;
- exceptions;
- cleanup;
- async;
- ownership;
- atomics.

---

# 571.195. Path explosion tests

Deep branching programs phải remain bounded.

---

# 571.196. Large CFG tests

Test functions có:

```text id="0c8m7d"
10
100
1,000
10,000+
```

basic blocks.

---

# 571.197. Performance

Dataflow engine phải scale gần tuyến tính theo graph/domain size đối với analyses thông thường.

---

# 571.198. Soundness

Optimization-critical analysis phải conservative khi không đủ proof.

---

# 571.199. Single dataflow authority

CFG, dominator, def-use, liveness và generic dataflow infrastructure phải được shared thay vì mỗi compiler subsystem tự triển khai một semantic approximation khác nhau.

---

# 571.200. FINAL HARD INVARIANT

> **Axiom Source Analysis 2.0 phải cung cấp một CFG/Dataflow authority dùng chung cho semantic checking, ownership/resource analysis, diagnostics, optimization, register allocation, IDE và AI tooling. Với cùng MIR snapshot, target và analysis configuration, mọi execution order hoặc parallel scheduling hợp lệ phải hội tụ về cùng reachability, dominance, def-use và dataflow facts. Khi không đủ bằng chứng, analysis phải conservative; tuyệt đối không được tạo optimization hoặc safety decision dựa trên một giả định không được chứng minh.**

**BOOTSTRAP-571: LOCKED.**

---

# NEXT — BOOTSTRAP-572

## COMPILER STATIC ANALYSIS 3.0 — NULLABILITY, INITIALIZATION, RESOURCE FLOW, ALIAS ANALYSIS, RACE ANALYSIS, UNREACHABLE STATES, SECURITY FLOWS & WHOLE-PROGRAM PROGRAM PROPERTIES

`572` sẽ xây tầng **static analyzer thực sự** trên nền `571`, thay vì tiếp tục nhồi thêm analysis vào type checker.

Kiến trúc:

```text id="s8m5a6"
                         MIR + CFG
                            │
                            ▼
                    Dataflow Engine 571
                            │
        ┌───────────────────┼────────────────────┐
        ▼                   ▼                    ▼
   Value Analysis      Memory Analysis      Resource Flow
        │                   │                    │
        ├── Range           ├── Alias            ├── Move
        ├── Nullability     ├── Memory SSA       ├── Drop
        ├── Init            ├── Escape           └── Lifetime
        └── Constants       └── Effects
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
          Race/Safety    Security Flow   Whole Program
              │             │             │
              └─────────────┼─────────────┘
                            ▼
                    Diagnostic Engine 569
```

`572` sẽ đặc biệt khóa ranh giới giữa **“compiler có proof”** và **“static analyzer chỉ phát hiện khả năng”** — rất quan trọng để Axiom có thể mạnh về safety/security mà không biến compiler thành một hệ thống borrow-checker nặng nề.

**BOOTSTRAP-572: NEXT.**