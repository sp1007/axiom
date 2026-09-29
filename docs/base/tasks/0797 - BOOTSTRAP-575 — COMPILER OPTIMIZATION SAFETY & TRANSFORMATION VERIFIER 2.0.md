# BOOTSTRAP-575 — COMPILER OPTIMIZATION SAFETY & TRANSFORMATION VERIFIER 2.0
## PROOF-CARRYING OPTIMIZATION, TRANSFORMATION CONTRACTS, SEMANTIC EQUIVALENCE, MEMORY/ALIAS VALIDATION & MISCOMPILATION PREVENTION

**Trạng thái: COMPLETED / LOCKED**

`575` tạo lớp kiểm chứng giữa **optimization framework 553**, **dataflow/static analysis 571–572**, **effect system 573** và **symbolic proof engine 574**.

Mục tiêu cốt lõi:

> Optimizer được phép rất mạnh, nhưng **không được biến một giả định chưa chứng minh thành machine code**.

---

# 575.1. Architecture

```text id="n4k7z2"
                         Input MIR
                            │
                            ▼
                    Optimization Pass
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
          Transformation          Proof Goals
              Candidate                │
                 │                     ▼
                 │              Proof Engine 574
                 │                     │
                 │              ┌──────┴──────┐
                 │              ▼             ▼
                 │           Proven        Unknown
                 │              │             │
                 └──────────────┤             │
                                ▼             ▼
                         Transformation    REJECT
                                │
                                ▼
                         Local Verifier
                                │
                                ▼
                         Global Verifier
                                │
                                ▼
                         Verified MIR
                                │
                                ▼
                        Later Optimization
```

---

# 575.2. Transformation contract

Mỗi optimization pass phải khai báo contract:

```text id="5y7t2d"
TransformationContract {
    pass_id
    input_requirements
    preconditions
    transformation
    preserved_properties
    introduced_effects
    invalidated_facts
    postconditions
    proof_requirements
}
```

---

# 575.3. Pass identity

Mỗi pass có stable:

```text id="1m6k8e"
PassId
PassVersion
```

---

# 575.4. Input requirements

Pass phải khai báo IR level yêu cầu:

```text id="h5k9d3"
HIR
MIR
SSA-MIR
LIR
MachineIR
```

---

# 575.5. Preconditions

Precondition mô tả điều kiện transformation được phép thực hiện.

---

# 575.6. Postconditions

Postcondition mô tả property phải đúng sau transformation.

---

# 575.7. Preserved properties

Pass phải khai báo properties không được thay đổi:

```text id="3x0z7r"
type
memory safety
resource semantics
observable effects
control behavior
ABI
```

tùy pass.

---

# 575.8. Invalidated facts

Optimization có thể invalidate:

```text id="k9p2wm"
CFG
dominators
liveness
alias
range
memory SSA
effect summaries
```

---

# 575.9. Analysis dependency

Pass manager phải biết chính xác analysis nào cần recompute.

---

# 575.10. No hidden invalidation

Pass không được âm thầm làm stale analysis result.

---

# 575.11. Semantic equivalence

Default optimization contract:

```text id="j5z8rq"
ObservableBehavior(before)
=
ObservableBehavior(after)
```

---

# 575.12. Observable behavior

Bao gồm:

```text id="0f6a5g"
return values
memory-visible effects
IO
exceptions/panic
resource effects
synchronization
volatile operations
atomic semantics
ABI-visible behavior
```

---

# 575.13. Undefined behavior

Nếu Axiom có unsafe/undefined domain, transformation chỉ được exploit UB theo rules đã khóa trong memory/safety model.

---

# 575.14. Defined program domain

Đối với program nằm trong defined semantic domain, optimizer phải preserve semantics.

---

# 575.15. Poison-like values

Axiom không được vô tình tạo ra implicit poison semantics chỉ để optimizer dễ hơn.

---

# 575.16. Invalid state

Nếu operation tạo invalid state theo language semantics, verifier phải recognize chính xác.

---

# 575.17. Transformation classes

```text id="7b6r4k"
Local
CFG
Scalar
Memory
Loop
Interprocedural
IPO/LTO
Machine
```

---

# 575.18. Local transformation

Ví dụ:

```text id="6m6d3b"
x + 0 → x
```

---

# 575.19. CFG transformation

Ví dụ:

```text id="y7k8o1"
remove unreachable block
```

---

# 575.20. Scalar transformation

Constant folding, algebraic simplification, strength reduction.

---

# 575.21. Memory transformation

Load/store forwarding, elimination, promotion.

---

# 575.22. Loop transformation

LICM, unrolling, peeling, vectorization.

---

# 575.23. IPO transformation

Inlining, specialization, devirtualization, function cloning.

---

# 575.24. Machine transformation

Instruction-level peephole, scheduling, register optimization.

---

# 575.25. Proof requirement

Mỗi transformation contract chỉ rõ proof level yêu cầu.

```text id="9d5r4a"
Exact
Proven
TrustedContract
```

---

# 575.26. Unknown

`Unknown` không thỏa proof requirement.

---

# 575.27. Fail closed

Không có proof → transformation không được apply.

---

# 575.28. Proof provenance

Proof phải reference:

```text id="t7q9d1"
MIR snapshot
analysis facts
constraints
proof engine version
```

---

# 575.29. Proof dependency DAG

Proof có thể phụ thuộc proof/facts khác.

---

# 575.30. Proof invalidation

Fact bị invalidate → proof phụ thuộc fact phải invalid.

---

# 575.31. Local proof

Transformation nhỏ có thể được verify locally.

---

# 575.32. Global proof

Transformation làm thay đổi cross-function semantics phải dùng global/interprocedural proof.

---

# 575.33. Structural verifier

Verifier trước tiên kiểm tra IR structural validity.

---

# 575.34. SSA verifier

Nếu IR ở SSA:

```text id="j8c1vf"
def-use
dominance
phi placement
```

phải hợp lệ.

---

# 575.35. CFG verifier

Mọi terminator phải có valid successor.

---

# 575.36. Block verifier

Không có malformed basic block.

---

# 575.37. Type verifier

Transformation không được tạo type-invalid MIR.

---

# 575.38. Layout verifier

Aggregate operations phải preserve layout contract.

---

# 575.39. ABI verifier

ABI-visible transformations phải preserve:

```text id="7s8a0h"
calling convention
argument order
return ABI
alignment
stack rules
register rules
```

---

# 575.40. Memory verifier

Load/store transformation phải preserve valid memory semantics.

---

# 575.41. Alias verifier

Không được biến `MayAlias` thành `NoAlias` nếu chưa có proof.

---

# 575.42. NoAlias proof

Có thể đến từ:

```text id="7q5y9e"
ownership
distinct allocations
range separation
type/layout guarantees
symbolic proof
```

---

# 575.43. Memory region verifier

Transformation phải track đúng region:

```text id="6t0r2e"
stack
heap
global
TLS
external
device
```

---

# 575.44. Volatile barrier

Volatile accesses không được reorder/eliminate như ordinary memory.

---

# 575.45. Atomic barrier

Atomic semantics phải preserve ordering.

---

# 575.46. Atomic transformation

Relaxing atomic ordering chỉ được phép khi contract/proof chứng minh semantic equivalence.

---

# 575.47. Synchronization verifier

Lock/channel/await/spawn behavior phải được preserve.

---

# 575.48. Effect verifier

Transformation không được loại bỏ observable effect.

---

# 575.49. Effect equivalence

Before/after effect summaries phải compatible.

---

# 575.50. Pure call elimination

Chỉ eliminate call nếu effect system chứng minh không có observable effect.

---

# 575.51. Read-only call

Read-only call không được coi pure nếu nó phụ thuộc mutable external state.

---

# 575.52. IO barrier

IO operation là observable.

---

# 575.53. Time barrier

Clock/time reads là observable.

---

# 575.54. Random barrier

Randomness không được constant-fold trừ khi semantics explicitly deterministic.

---

# 575.55. External barrier

Unknown external call là optimization barrier theo effect summary.

---

# 575.56. Panic preservation

Optimization không được biến:

```text id="z8m4p2"
may panic
```

thành:

```text id="x4c7dn"
cannot panic
```

mà không có proof.

---

# 575.57. Panic removal

Panic path chỉ có thể eliminate khi unreachable hoặc semantics chứng minh không thể xảy ra.

---

# 575.58. Exception preservation

Throw/unwind behavior phải được preserve.

---

# 575.59. Cleanup preservation

Destructor/drop/defer semantics là observable nếu chúng có effects.

---

# 575.60. Resource verifier

Resource state trước/sau transformation phải tương đương.

---

# 575.61. Move preservation

Transformation không được tạo thêm/loại bỏ move có semantic effect.

---

# 575.62. Drop preservation

Drop count/order phải preserve khi observable.

---

# 575.63. Allocation verifier

Allocation elimination chỉ hợp lệ khi allocation identity không observable.

---

# 575.64. Escape proof

Stack promotion yêu cầu proof object chứng minh object không escape theo relevant lifetime.

---

# 575.65. Heap-to-stack

Phải preserve alignment, lifetime, destructor và address-observability.

---

# 575.66. Stack-to-heap

Phải preserve lifetime/ownership semantics.

---

# 575.67. Pointer observability

Nếu address được exposed/compared/stored, allocation transformation khó hơn và cần proof bổ sung.

---

# 575.68. Bounds verifier

Bounds-check elimination yêu cầu:

```text id="p5x2w9"
0 <= index
index < length
```

hoặc proof tương đương.

---

# 575.69. Bounds proof source

Có thể đến từ:

```text id="4j2z8r"
range analysis
loop invariant
symbolic execution
constant propagation
```

---

# 575.70. Bounds proof snapshot

Proof phải reference exact MIR/analysis snapshot.

---

# 575.71. Null-check elimination

Chỉ eliminate null check nếu non-null được proven.

---

# 575.72. Null invalidation

Call/alias/mutation có thể invalidate non-null facts.

---

# 575.73. Arithmetic optimization

Integer algebra phải respect overflow mode.

---

# 575.74. Wrapping arithmetic

Optimizer không được dùng unbounded mathematical integer identities.

---

# 575.75. Checked arithmetic

Check elimination yêu cầu proof no-overflow.

---

# 575.76. Saturating arithmetic

Saturation behavior phải preserve.

---

# 575.77. Floating-point optimization

FP transformations phải respect configured floating-point semantics.

---

# 575.78. NaN preservation

Transformation không được loại bỏ NaN behavior nếu observable.

---

# 575.79. Signed-zero preservation

Relevant transformations phải preserve `-0/+0`.

---

# 575.80. Fast-math

Fast-math là explicit semantic mode, không phải optimizer tự bật.

---

# 575.81. Fast-math contract

Transformation chỉ được dùng relaxed FP identities trong fast-math domain.

---

# 575.82. Branch elimination

Branch chỉ được eliminate khi condition proven constant.

---

# 575.83. Branch simplification

Boolean algebra phải respect side effects trong operands.

---

# 575.84. Short-circuit semantics

Optimization phải preserve evaluation ordering/side effects.

---

# 575.85. Speculative execution

Speculative computation chỉ được move nếu effects và failure behavior cho phép.

---

# 575.86. Speculation barrier

Potential IO/panic/volatile/atomic effects có thể cấm speculation.

---

# 575.87. Code motion

Moving instruction phải chứng minh:

```text id="w3p9hf"
dependencies preserved
effects preserved
failure behavior preserved
```

---

# 575.88. LICM

Loop invariant code motion cần proof:

```text id="4k6zdp"
value invariant
memory dependency invariant
effects movable
```

---

# 575.89. Store motion

Store movement cần alias + ordering proof.

---

# 575.90. Load forwarding

Load forwarding cần proof source store dominates and no intervening clobber.

---

# 575.91. Dead store elimination

Store chỉ được eliminate nếu memory effect proven unobservable/overwritten.

---

# 575.92. Dead load elimination

Load có thể eliminate khi value unused và load không observable.

---

# 575.93. Volatile load

Volatile load không được DCE.

---

# 575.94. Atomic load

Atomic load elimination phải tuân atomic semantics.

---

# 575.95. Function inlining

Inlining phải preserve effect/failure/cleanup behavior.

---

# 575.96. Inlining proof

Structural verifier kiểm tra cloned body.

---

# 575.97. Devirtualization

Dynamic call → direct call chỉ khi target set proven.

---

# 575.98. Open-world restriction

Không devirtualize dựa trên incomplete implementation set.

---

# 575.99. Closed-world proof

Closed-world build phải bind target set identity.

---

# 575.100. Function specialization

Specialization phải preserve generic semantics.

---

# 575.101. Generic assumptions

Không specialize dựa trên runtime property chưa proven.

---

# 575.102. Constant specialization

Compile-time constant specialization yêu cầu immutable/known input.

---

# 575.103. Interprocedural transformations

IPO phải update function summaries.

---

# 575.104. Summary invalidation

Inlining/cloning/specialization có thể invalidate effect/analysis summaries.

---

# 575.105. Recompute policy

Pass manager quyết định reuse hay recompute dựa trên invalidation metadata.

---

# 575.106. Analysis preservation contract

Pass phải khai báo:

```text id="n4k2xz"
Preserves CFG?
Preserves Dominators?
Preserves SSA?
Preserves Alias?
Preserves Range?
Preserves Effects?
```

---

# 575.107. No stale analysis

Verifier có thể reject pass nếu pass metadata mâu thuẫn với actual IR mutation.

---

# 575.108. Transformation transaction

Mỗi pass nên operate transactionally:

```text id="0j9n3p"
snapshot
→ transform
→ verify
→ commit
```

---

# 575.109. Failed transformation

Verification failure → rollback.

---

# 575.110. Partial mutation

Failed pass không được để IR ở trạng thái half-mutated.

---

# 575.111. Pass isolation

Pass failure không corrupt compiler global state.

---

# 575.112. Parallel optimization

Independent functions có thể optimize song song.

---

# 575.113. Deterministic output

Parallel optimization phải produce canonical equivalent IR.

---

# 575.114. Transformation ordering

Pass ordering được điều khiển bởi pass manager/cost model.

---

# 575.115. Semantic invariance

Thay đổi pass ordering không được thay đổi defined program behavior.

---

# 575.116. Optimization budget

Pass manager có:

```text id="4f2j5w"
time
memory
code-size
compile-cost
```

budget.

---

# 575.117. Budget exhaustion

Hết budget → bỏ qua optimization, không giảm correctness.

---

# 575.118. Profile

Optimization profiles:

```text id="8y6x3c"
debug
balanced
speed
size
compile-fast
```

---

# 575.119. Debug profile

Ưu tiên debuggability và predictable transformations.

---

# 575.120. Size profile

Ưu tiên code-size reduction.

---

# 575.121. Speed profile

Ưu tiên runtime performance.

---

# 575.122. Compile-fast

Giảm expensive proof/transformations.

---

# 575.123. PGO

Profile-guided optimization có profile data identity.

---

# 575.124. PGO trust

Profile data chỉ ảnh hưởng heuristic/cost model, không thay đổi semantic proof requirement.

---

# 575.125. Profile mismatch

Mismatched profile phải được detect.

---

# 575.126. LTO

LTO có thể mở rộng proof scope.

---

# 575.127. Cross-module proof

Proof phải reference exact module/build snapshot.

---

# 575.128. Distributed optimization

Optimization có thể remote nhưng result phải verified trước commit.

---

# 575.129. Remote distrust

Remote worker result không được coi trusted chỉ vì worker nằm trong build cluster.

---

# 575.130. Proof-carrying result

Remote transformation có thể gửi:

```text id="2t7z8x"
transformed IR
+
proof metadata
+
analysis dependencies
```

---

# 575.131. Local verification

Coordinator/local compiler verifies critical transformation.

---

# 575.132. Artifact cache

Verified transformation result có thể cache.

---

# 575.133. Cache key

```text id="9f0q6m"
InputIRIdentity
PassId
PassVersion
Target
FeatureSet
OptimizationProfile
ProofEngineVersion
```

---

# 575.134. Cache trust

Cached result phải pass structural/semantic verification trước reuse nếu required.

---

# 575.135. Cache independence

Cache hit/miss không được thay đổi correctness.

---

# 575.136. Reproducibility

Same input/config must produce equivalent verified output.

---

# 575.137. Canonical IR

Equivalent transformations nên canonicalize để tăng cache hit.

---

# 575.138. Transformation ID

Mỗi applied transformation có stable event ID.

---

# 575.139. Optimization trace

Compiler debug mode có thể record:

```text id="7o3n2s"
pass
input
proof
transform
verification
result
```

---

# 575.140. AI explainability

AI có thể query:

```text id="3h9m5b"
why was this instruction removed?
why was bounds check eliminated?
why was this function inlined?
```

---

# 575.141. AI authority

AI chỉ đọc transformation/proof records.

---

# 575.142. AI cannot approve

AI explanation không thể authorize unsafe optimization.

---

# 575.143. Diagnostics

Verification failure đi qua `569`.

---

# 575.144. Internal compiler error

Malformed transformation contract/IR invariant failure có thể là compiler bug diagnostic.

---

# 575.145. User error separation

Compiler bug phải được phân biệt với user source error.

---

# 575.146. Miscompilation detector

Compiler có thể optionally run shadow verification trong debug/test builds.

---

# 575.147. Reference interpreter

Verified MIR có thể chạy trên reference interpreter.

---

# 575.148. Differential execution

Compare:

```text id="0v8q8r"
pre-optimization MIR
post-optimization MIR
```

trên generated inputs.

---

# 575.149. Symbolic differential

`574` có thể attempt prove equivalence cho local transformations.

---

# 575.150. Equivalence scope

Không yêu cầu general semantic equivalence theorem cho toàn compiler.

---

# 575.151. Local equivalence

Small transformations có thể được verified bằng symbolic normalization.

---

# 575.152. Structural equivalence

Một số transformations có equivalence proof bằng structural rules.

---

# 575.153. Memory equivalence

Memory transformations cần compare abstract memory effects.

---

# 575.154. Resource equivalence

Resource transformations cần compare ownership/drop effects.

---

# 575.155. Effect equivalence

Observable effect traces phải compatible.

---

# 575.156. Control-flow equivalence

Không nhất thiết giữ nguyên CFG; chỉ observable control behavior cần preserve.

---

# 575.157. Termination

Optimizer không được biến terminating defined computation thành nonterminating computation nếu semantics yêu cầu termination preservation.

---

# 575.158. Nontermination

Nếu language semantics cho phép nontermination, verifier phải respect semantic model.

---

# 575.159. Side-channel boundary

Performance/security side-channel properties không mặc định thuộc semantic equivalence.

---

# 575.160. Constant-time mode

Nếu Axiom có cryptographic constant-time contract, transformation verifier phải support additional contract.

---

# 575.161. Constant-time contract

Transformation không được introduce forbidden data-dependent timing trong constant-time region.

---

# 575.162. Security contract

Security-sensitive transformations có thể yêu cầu stronger proof.

---

# 575.163. Capability contract

Transformation phải preserve capability boundaries.

---

# 575.164. Sandbox contract

Không được optimize away sandbox enforcement.

---

# 575.165. FFI contract

FFI call semantics được coi opaque trừ khi verified metadata tồn tại.

---

# 575.166. Inline assembly

Inline asm transformation chỉ trong explicit constraints.

---

# 575.167. Register clobbers

Machine verifier phải validate asm clobber constraints.

---

# 575.168. Stack maps

Transformations affecting GC-like external runtime metadata, if any, phải update stack maps.

---

# 575.169. Unwind info

Changes to call/stack structure phải invalidate/rebuild unwind metadata.

---

# 575.170. Debug info

Transformation phải update debug mapping.

---

# 575.171. Source-level semantics

Debug info không được làm thay đổi runtime semantics.

---

# 575.172. Optimization remarks

Compiler có thể report:

```text id="m7y6gd"
applied
rejected
proof unavailable
cost too high
```

---

# 575.173. Rejection reason

Rejected optimization phải có machine-readable reason.

---

# 575.174. Proof failure reason

Phân biệt:

```text id="w3d8g2"
false
unknown
budget-exceeded
unsupported
invalidated
```

---

# 575.175. Unsupported proof

Unsupported không được xem là false.

---

# 575.176. False proof

`Disproven` nghĩa condition không đúng.

---

# 575.177. Unknown proof

Không đủ information.

---

# 575.178. Budget exceeded

Analysis bị giới hạn tài nguyên.

---

# 575.179. Unsupported

Proof domain chưa hỗ trợ property.

---

# 575.180. Verified optimization levels

```text id="2j6t4q"
Level 0 — structural
Level 1 — local semantic
Level 2 — memory/effect
Level 3 — interprocedural
Level 4 — whole-program
```

---

# 575.181. Release requirement

Critical optimizations phải đạt required verification level.

---

# 575.182. Debug requirement

Debug builds có thể enable stronger verification.

---

# 575.183. Compiler development

Compiler development builds nên chạy maximal verification.

---

# 575.184. Fuzzing

Optimization fuzzer generate:

```text id="x8q1c7"
MIR
contracts
analysis states
alias patterns
overflow cases
concurrency
```

---

# 575.185. Pass fuzzing

Mỗi optimization pass phải có independent fuzz harness.

---

# 575.186. Verifier fuzzing

Malformed IR phải không crash verifier.

---

# 575.187. Differential optimization testing

Random pass sequences phải compare reference/unoptimized behavior.

---

# 575.188. Translation validation

Mỗi optimized function có thể được translation-validated against input function trong testing/audit mode.

---

# 575.189. Miscompilation corpus

Mỗi discovered miscompile phải trở thành permanent regression test.

---

# 575.190. Proof regression

Mỗi proof bug phải có proof-level regression case.

---

# 575.191. Semantic regression

Mỗi semantic mismatch phải preserve minimized reproducer.

---

# 575.192. Performance regression

Verification overhead được benchmark riêng.

---

# 575.193. Zero mandatory runtime overhead

Verifier/proof metadata không bắt buộc tồn tại trong release runtime image.

---

# 575.194. Compile-time scalability

Cheap transformations phải tránh invoking deep symbolic proof unnecessarily.

---

# 575.195. Tiered verification

```text id="x8n7p0"
cheap structural check
      ↓
cheap dataflow proof
      ↓
symbolic proof
      ↓
optional deep verifier
```

---

# 575.196. Architecture boundary

`575` không trở thành optimizer mới.

Nó là **verification layer** được `553` gọi.

---

# 575.197. Single semantic authority

Semantic truth vẫn thuộc:

```text id="2b0v8k"
Type/Semantic Engine
MIR
Dataflow 571
Static Analysis 572
Effect System 573
Symbolic Engine 574
```

Verifier chỉ kiểm tra transformation có giữ các facts đó hay không.

---

# 575.198. No optimization by assumption

Mọi optimization có semantic consequence phải có:

```text id="q1r5cv"
contract
+
required proof
+
verification
```

---

# 575.199. Deterministic correctness

Cùng:

```text id="4l5x8b"
Input MIR
Target
FeatureSet
Optimization Profile
Pass Version
```

phải dẫn tới cùng canonical verification result bất kể cache hit, worker hay execution order.

---

# 575.200. FINAL HARD INVARIANT

> **Không một optimization nào được commit vào Axiom IR nếu nó vi phạm transformation contract hoặc không đạt proof level mà contract yêu cầu. `Unknown` luôn dẫn tới reject đối với transformation cần proof. Mọi transformation phải có khả năng rollback; mọi analysis fact bị invalidation phải được đánh dấu; memory, resource, effect, panic, atomic, synchronization, ABI và observable behavior phải được bảo toàn theo semantic contract. Proof phải gắn với exact IR/configuration snapshot và có thể được kiểm chứng độc lập.**

**BOOTSTRAP-575: LOCKED.**

---

# NEXT — BOOTSTRAP-576

## COMPILER OPTIMIZATION PASS LIBRARY 3.0
### SSA OPTIMIZATION, GVN, SCCP, DCE, COPY PROPAGATION, INSTCOMBINE, MEMORY OPTIMIZATION, LOOP OPTIMIZATION, VECTORIZATION, INLINING & SIZE/SPEED SPECIALIZATION

`576` sẽ chuyển từ **“framework + proof/verifier”** sang **bộ optimization passes cụ thể**.

Kiến trúc:

```text id="9h2x5k"
                         MIR
                          │
                 ┌────────┴────────┐
                 │ Analysis Facts  │
                 └────────┬────────┘
                          ▼
                    Pass Manager
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
     Scalar            Memory             Loop
     Passes             Passes            Passes
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                     IPO / LTO
                          │
                          ▼
                    Vectorization
                          │
                          ▼
                   Machine-oriented
                    optimization
                          │
                          ▼
                  575 Verification
                          │
                          ▼
                     Optimized MIR
```

`576` sẽ đặc biệt khóa **thứ tự và điều kiện áp dụng các pass**, tránh việc Axiom có hàng chục optimizer nhưng kết quả không ổn định hoặc compile quá chậm. Nó cũng sẽ nối trực tiếp với mục tiêu trước đây của Axiom: **runtime ≥ C/C++, binary nhỏ, nhưng compiler vẫn nhanh và predictable**.

**BOOTSTRAP-576: NEXT.**