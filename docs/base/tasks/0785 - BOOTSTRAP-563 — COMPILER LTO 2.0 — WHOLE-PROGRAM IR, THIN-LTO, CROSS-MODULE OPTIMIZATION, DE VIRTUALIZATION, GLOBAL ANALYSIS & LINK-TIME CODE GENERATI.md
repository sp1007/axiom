# BOOTSTRAP-563 — COMPILER LTO 2.0 — WHOLE-PROGRAM IR, THIN-LTO, CROSS-MODULE OPTIMIZATION, DE VIRTUALIZATION, GLOBAL ANALYSIS & LINK-TIME CODE GENERATION

**Trạng thái: COMPLETED / LOCKED**

`BOOTSTRAP-563` khóa tầng tối ưu hóa **liên module/liên package** của Axiom.

Mục tiêu là cho phép compiler nhìn xuyên qua ranh giới module khi điều đó hợp lệ, nhưng **không biến mọi build thành một lần compile khổng lồ**, không phá ABI/dynamic library/FFI và không làm mất incremental compilation.

Nguyên tắc:

> **LTO là một optimization mode, không phải một semantic mode.**  
> Chương trình không có LTO phải có semantics tương đương chương trình có LTO.

---

# 563.1. Vấn đề

Không có LTO:

```text
A.ax
 ↓
A.o

B.ax
 ↓
B.o

C.ax
 ↓
C.o

        ↓
      Link
```

Compiler không thể dễ dàng biết:

```text
A.f() → B.g() → C.h()
```

để thực hiện:

- cross-module inlining;
- devirtualization;
- constant propagation;
- dead function elimination;
- interprocedural specialization;
- global escape analysis;
- cross-module vectorization;
- call graph optimization.

---

# 563.2. LTO architecture

```text id="w8k3p2"
                Source / Modules
                       │
                       ▼
              Semantic Compilation
                       │
                       ▼
              Module Optimization
                       │
                       ▼
             Optimization Summary
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Call Graph    Type Graph    Const Graph
          │            │            │
          └────────────┼────────────┘
                       ▼
                Whole Program IR
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
         Inlining   Devirt.   Specialize
             │         │         │
             └─────────┼─────────┘
                       ▼
              Global Optimization
                       │
                       ▼
                  MIR / LTO-MIR
                       │
                       ▼
                 Code Generation
                       │
                       ▼
                    Objects
                       │
                       ▼
                    Linker
```

---

# 563.3. Ba chế độ

Axiom định nghĩa:

```text
LTO = off
LTO = thin
LTO = full
```

### Off

Mỗi module tối ưu độc lập.

### Thin

Mỗi module vẫn có compilation unit riêng nhưng dùng summary của toàn chương trình.

### Full

Toàn bộ optimization IR được đưa vào một global optimization graph.

---

# 563.4. Semantic equivalence

Phải luôn có:

```text
Program(no LTO)
≡
Program(Thin LTO)
≡
Program(Full LTO)
```

trong cùng semantic contract.

---

# 563.5. LTO không thay đổi API

LTO không được thay đổi:

- type semantics;
- ownership;
- error semantics;
- memory model;
- ABI contract của symbol exported;
- FFI behavior.

---

# 563.6. LTO input

LTO có thể nhận:

```text
Source
Axiom semantic artifact
Axiom IR artifact
Axiom object + LTO metadata
```

---

# 563.7. LTO object metadata

Object có thể chứa:

```text
AXLTO section
```

chứa optimization summary.

Không bắt buộc chứa toàn bộ source.

---

# 563.8. LTO summary

```text id="m5q9v1"
LtoSummary {
    symbol_id
    linkage
    visibility
    function_size
    instruction_count
    call_edges[]
    type_dependencies[]
    constants[]
    effects
    attributes
    hotness
    coldness
    inline_cost
    specialization_candidates[]
    escape_summary
}
```

---

# 563.9. Summary không phải source of truth

LTO summary chỉ là cache/index.

Nếu summary mâu thuẫn với semantic artifact:

```text
summary → invalid
```

và compiler phải recompute.

---

# 563.10. Symbol identity

LTO dùng `SymbolId`/semantic identity từ `446`, không dùng tên string đơn thuần.

---

# 563.11. Cross-module call graph

```text id="q8x3m7"
A.foo
 │
 ├──→ B.bar
 │      └──→ C.baz
 │
 └──→ C.fast
```

Call graph phải lưu provenance.

---

# 563.12. Dynamic dispatch graph

Trait calls:

```text id="v6m2q9"
dyn Trait
    ↓
possible implementations
```

phải được phân tích theo visibility/linkage.

---

# 563.13. Closed-world assumption

Devirtualization chỉ được phép khi compiler có bằng chứng rằng tập implementation có thể được đóng.

Không được giả định closed-world một cách ngầm định.

---

# 563.14. Open-world boundary

Dynamic library / public ABI / FFI thường là open-world boundary.

Compiler phải coi external implementation có thể tồn tại.

---

# 563.15. Internal symbol

Internal/private symbol có thể được:

- inline;
- rename;
- eliminate;
- specialize;
- merge.

---

# 563.16. Public symbol

Public symbol chỉ được biến đổi nếu ABI/API contract vẫn đúng.

---

# 563.17. Exported symbol

Nếu exported symbol có external addressability, compiler không được eliminate chỉ vì không thấy caller trong current graph.

---

# 563.18. Address-taken analysis

Compiler phải phân biệt:

```text
called
address_taken
exported
externally_visible
```

---

# 563.19. Function pointer graph

Nếu function address được lấy:

```text
foo as fn()
```

LTO phải preserve khả năng gọi gián tiếp.

---

# 563.20. Whole-program roots

Root có thể gồm:

```text
main
exported symbols
FFI symbols
runtime callbacks
reflection roots
plugin ABI roots
dynamic loader roots
```

---

# 563.21. Root manifest

Build system có thể cung cấp explicit:

```text
@export_root
```

khi external system gọi symbol mà static analysis không biết.

---

# 563.22. LTO visibility lattice

```text
Private
Package
Public
Exported
Extern
Dynamic
Unknown
```

Optimization permission giảm dần theo exposure.

---

# 563.23. Inlining

Cross-module inlining phải sử dụng:

```text
inline cost
hotness
size budget
effect constraints
ABI
debug cost
```

---

# 563.24. Inline attributes

Axiom hỗ trợ:

```text
@inline
@inline(always)
@inline(never)
```

nhưng `always` là optimization request, không được biến thành semantic guarantee.

---

# 563.25. Inline safety

Không inline nếu làm sai:

- panic behavior;
- side effects;
- volatile semantics;
- atomic ordering;
- FFI boundary;
- security policy.

---

# 563.26. Cross-module constant propagation

Ví dụ:

```text
const MAX = 32
```

được truyền xuyên module nếu visibility/immutability cho phép.

---

# 563.27. Constant provenance

Mỗi propagated constant phải có nguồn:

```text
SymbolId
ValueHash
Snapshot
```

---

# 563.28. Global value numbering

LTO có thể hợp nhất expression tương đương nếu effects cho phép.

---

# 563.29. Interprocedural constant propagation

```text id="k7v3m9"
foo(x: i32) -> i32
```

nếu mọi caller truyền `5`, compiler có thể tạo specialization:

```text
foo.const5()
```

nhưng chỉ khi cost model cho phép.

---

# 563.30. Specialization

Specialization phải tạo symbol identity mới.

---

# 563.31. Generic specialization

LTO có thể tận dụng generic instances đã monomorphized.

---

# 563.32. Generic cross-module cache

Nếu cùng:

```text
T = Vec<i32>
```

đã compile, artifact có thể reuse nếu fingerprint khớp.

---

# 563.33. Dead function elimination

Một function chỉ được loại bỏ nếu không phải root và không có observable address/reference.

---

# 563.34. Dead global elimination

Tương tự với static/global data.

---

# 563.35. Dead type metadata

Semantic/debug metadata không được giữ lại chỉ vì compiler từng biết type đó, trừ khi target runtime/debug policy yêu cầu.

---

# 563.36. Whole-program DCE

Full LTO có thể loại bỏ entire unreachable subgraphs.

---

# 563.37. Thin-LTO DCE

Thin-LTO phải dùng summary để quyết định candidate elimination nhưng không được phụ thuộc vào task order.

---

# 563.38. Devirtualization

Các trường hợp:

```text
dyn Trait
sealed implementation
final-known implementation
unique implementation
```

có thể được chuyển thành direct call khi proof đủ mạnh.

---

# 563.39. Devirtualization evidence

Compiler phải lưu:

```text
reason
candidate_set
proof_state
```

---

# 563.40. Failed devirtualization

Không phải failure.

```text
Unknown
```

→ giữ indirect call.

---

# 563.41. Whole-program type analysis

Có thể phân tích:

```text
type creation
trait implementation
casts
dyn conversion
```

để thu hẹp target set.

---

# 563.42. Escape analysis

LTO cho phép nhìn allocation qua function boundary:

```text
foo()
 ↓
alloc
 ↓
bar()
```

và chứng minh object không escape.

---

# 563.43. Allocation elimination

Nếu proof đủ mạnh:

```text
heap allocation
```

có thể trở thành:

```text
stack/local/scalar
```

theo `423`.

---

# 563.44. Global scalar replacement

Struct xuyên module có thể được scalarize nếu ABI/observable address không bị phá.

---

# 563.45. Alias analysis

LTO có thể thu thập alias information từ nhiều module.

---

# 563.46. No false alias proof

Nếu external/FFI có thể alias, compiler phải giữ conservative assumption.

---

# 563.47. Interprocedural effect analysis

Function summary:

```text id="q5m8x2"
reads
writes
allocates
blocks
panics
throws/unwinds
performs_io
atomic
unsafe
```

---

# 563.48. Effect propagation

Caller summary phải phản ánh callee effects khi observable.

---

# 563.49. `no_alloc`

Cross-module call tới function không chứng minh được `no_alloc` không được tự suy ra là `no_alloc`.

---

# 563.50. `no_panic`

Tương tự.

---

# 563.51. `no_block`

Tương tự.

---

# 563.52. Realtime

`@realtime` không được suy luận từ “callee có vẻ nhanh”.

Phải có effect proof.

---

# 563.53. Memory effects

LTO phải phân biệt:

```text
read-none
read-local
read-global
write-local
write-global
volatile
atomic
unknown
```

---

# 563.54. Global variable optimization

Immutable globals có thể constant-fold.

Mutable globals phải preserve observable ordering.

---

# 563.55. Thread-visible globals

Không được optimize dựa trên single-thread assumption nếu object có thể được chia sẻ.

---

# 563.56. Atomic globals

Atomic operations phải preserve memory order.

---

# 563.57. Synchronization boundaries

Cross-module optimization không được reorder operations qua synchronization boundary trái semantics.

---

# 563.58. FFI boundary

Mặc định:

```text
Axiom → FFI
```

là optimization boundary.

---

# 563.59. FFI summary

User có thể cung cấp:

```text
@ffi(pure)
@ffi(readonly)
@ffi(noalloc)
@ffi(nothrow)
```

nhưng annotation phải được trust boundary kiểm soát.

---

# 563.60. Unannotated FFI

Mặc định conservative:

```text
unknown effects
unknown alias
unknown allocation
unknown panic
```

---

# 563.61. Dynamic library boundary

Full LTO không được xuyên dynamic library boundary nếu không có explicit whole-deployment contract.

---

# 563.62. Static library

Static library có thể tham gia LTO nếu chứa LTO metadata.

---

# 563.63. Mixed objects

Build có thể:

```text
Axiom LTO object
+
Axiom normal object
+
C object
```

---

# 563.64. Mixed-LTO boundary

Normal object được coi như opaque external module trừ metadata ABI/effect được cung cấp.

---

# 563.65. C ABI

Không được giả định C function pure hoặc non-alloc nếu không có declaration.

---

# 563.66. Linker integration

LTO orchestration:

```text id="m3q7v9"
Linker
  ↓
discover LTO objects
  ↓
invoke Axiom LTO engine
  ↓
generate optimized objects
  ↓
final link
```

---

# 563.67. Linker không tối ưu semantic IR

Axiom linker chỉ orchestrates LTO; semantic transformations thuộc compiler LTO engine.

---

# 563.68. LTO driver

```text id="x8n4m2"
axiom link --lto=thin ...
```

hoặc build profile:

```text
lto = "thin"
```

---

# 563.69. Full LTO memory

Full LTO có thể tiêu thụ rất nhiều RAM.

Compiler phải có resource budget.

---

# 563.70. Thin LTO memory

Thin-LTO tồn tại để giữ:

- memory thấp hơn;
- parallelism;
- incremental rebuild.

---

# 563.71. Thin-LTO architecture

```text id="q2v9m5"
Module summaries
      │
      ▼
Global index
      │
      ├── A optimization
      ├── B optimization
      ├── C optimization
      └── D optimization
             │
             ▼
      Parallel backend
```

---

# 563.72. Global index

```text
GlobalIndex {
    symbols
    call_graph
    type_graph
    summaries
    roots
    visibility
}
```

---

# 563.73. Thin-LTO import

Module A có thể import body của function B khi:

```text
benefit > import_cost
```

---

# 563.74. Import budget

Mỗi module có:

```text
instruction_budget
memory_budget
compile_time_budget
```

---

# 563.75. Import graph

Phải tránh tạo explosion:

```text
A imports B
B imports C
C imports D
...
```

---

# 563.76. Import cycle

Không phải semantic cycle error.

LTO phải xử lý bằng bounded import/fixpoint strategy.

---

# 563.77. Function summary version

Summary phải có schema version.

---

# 563.78. Summary invalidation

Invalidate khi thay đổi:

- function body;
- signature;
- relevant attributes;
- dependencies;
- target;
- ABI;
- optimization semantics.

---

# 563.79. Summary reuse

Nếu chỉ thay đổi unrelated module:

```text
A unchanged
B changed
```

summary của A có thể reuse nếu dependency fingerprint không đổi.

---

# 563.80. Dependency fingerprint

Summary phải chứa hash của các semantic facts mà nó phụ thuộc.

---

# 563.81. Fine-grained dependency

Không invalidate toàn bộ module chỉ vì một symbol thay đổi nếu dependency graph chứng minh không liên quan.

---

# 563.82. LTO cache

```text id="m9x4q2"
LtoCacheKey {
    semantic_hash
    dependency_hash
    target_fingerprint
    optimization_profile
    lto_mode
    compiler_build_id
}
```

---

# 563.83. Cache correctness

Cache hit phải tương đương recomputation.

---

# 563.84. Cross-target isolation

LTO summary target-dependent phải không được reuse giữa:

```text
x86-64
AArch64
WASM
```

---

# 563.85. Target-independent summaries

Có thể reuse nếu summary declaration chứng minh target-independent.

---

# 563.86. Profile-guided LTO

PGO data từ `553` có thể ảnh hưởng:

- inline;
- specialization;
- cloning;
- layout;
- cold splitting.

---

# 563.87. Profile provenance

PGO data phải gắn:

```text
binary_build_id
profile_id
target
collection_mode
```

---

# 563.88. Stale profile

Stale profile không được coi là exact truth.

---

# 563.89. Profile mismatch

Compiler phải báo:

```text
ProfileMismatch
```

và áp dụng policy explicit.

---

# 563.90. Call graph SCC

Recursive call graph phải được phân tích theo strongly connected components.

---

# 563.91. Recursive inlining

Compiler không được inline vô hạn.

---

# 563.92. Recursion budget

Có:

```text
max_inline_depth
max_inline_growth
```

---

# 563.93. Tail recursion

Có thể optimize thành loop khi semantics và ABI cho phép.

---

# 563.94. Cross-module tail call

Phải respect ABI/tail-call legality.

---

# 563.95. Function cloning

Một function có thể được clone theo caller/context.

---

# 563.96. Clone identity

Clone phải có deterministic derived identity.

---

# 563.97. Clone explosion

Compiler phải giới hạn:

```text
clone_count
code_growth
compile_cost
```

---

# 563.98. Constant specialization

```text
foo(x)
```

có thể tạo:

```text
foo_const_0
foo_const_1
```

nếu benefit đủ lớn.

---

# 563.99. Generic specialization + constant specialization

Hai cơ chế có thể phối hợp nhưng phải có global code-size budget.

---

# 563.100. Whole-program code-size budget

LTO phải obey budget của `450/553`.

---

# 563.101. Hot/cold partitioning

Functions/basic blocks có profile coldness có thể tách khỏi hot code.

---

# 563.102. Section placement

LTO có thể generate:

```text
.text.hot
.text
.text.unlikely
```

khi object format hỗ trợ.

---

# 563.103. Function ordering

Function order có thể tối ưu locality nhưng phải deterministic trong cùng profile.

---

# 563.104. Identical code folding

Nếu hai functions hoàn toàn equivalent và address identity không observable, có thể merge.

---

# 563.105. Address identity

Nếu:

```text
&foo != &bar
```

có thể observable, không được merge.

---

# 563.106. Global data merging

Tương tự với constants/data.

---

# 563.107. String merging

Chỉ merge nếu language semantics cho phép string identity không observable.

---

# 563.108. Vtable optimization

Nếu dyn trait table có implementation không dùng, entries có thể tối ưu theo ABI policy.

---

# 563.109. Vtable ABI

Không được thay đổi stable external vtable ABI chỉ vì LTO.

---

# 563.110. Trait devirtualization

Static trait dispatch đã monomorphized có thể inline trực tiếp.

---

# 563.111. Dynamic trait dispatch

Chỉ devirtualize khi target set đủ proof.

---

# 563.112. Enum optimization

LTO có thể biết variant impossible trong một context và simplify branch.

---

# 563.113. Impossible state

Chỉ loại bỏ branch nếu proof đến từ semantic invariants hoặc explicit contract.

Không dùng heuristic để biến Unknown thành impossible.

---

# 563.114. Contract integration

`479` contracts có thể cung cấp facts:

```text
x < 10
```

cho LTO.

---

# 563.115. Proof state

Chỉ:

```text
Proven
```

được phép dùng như compile-time fact không cần runtime check.

---

# 563.116. RuntimeChecked

Không được coi là compile-time proof.

---

# 563.117. Unknown

Không được optimize như false.

---

# 563.118. Interprocedural range analysis

Có thể truyền range:

```text
0 <= x < 100
```

qua function boundary nếu proof đủ mạnh.

---

# 563.119. Bounds-check elimination

Có thể loại bỏ bounds check khi LTO chứng minh index hợp lệ.

---

# 563.120. Bounds proof provenance

Phải truy được:

```text
index fact
array length fact
proof chain
```

---

# 563.121. Integer optimization

LTO không được tự giả định overflow semantics.

---

# 563.122. Overflow policy

Nếu Axiom dùng checked integer:

→ preserve trap/error semantics.

Nếu wrapping:

→ preserve wrapping.

---

# 563.123. Floating optimization

Không được thực hiện reassociation trái với strict FP mode.

---

# 563.124. Atomic optimization

Redundant atomic operations chỉ được loại bỏ khi memory model proof cho phép.

---

# 563.125. Volatile

Volatile operations là observable và không được eliminate/reorder trái contract.

---

# 563.126. I/O

I/O calls mặc định observable side effects.

---

# 563.127. Panic

Nếu callee có thể panic, removing/reordering call có thể thay đổi observable behavior.

---

# 563.128. Cleanup

LTO phải preserve deterministic cleanup/drop behavior.

---

# 563.129. Ownership

Ownership facts có thể được sử dụng để tối ưu nhưng không được thay đổi ownership semantics.

---

# 563.130. Drop elimination

Destructor/drop chỉ được eliminate khi compiler chứng minh object destruction không observable.

---

# 563.131. Drop fusion

Nested cleanup có thể được optimized nhưng thứ tự observable phải giữ nguyên.

---

# 563.132. Async functions

Async state machine có thể được tối ưu cross-module.

---

# 563.133. Async specialization

Compiler có thể loại bỏ state transitions không cần thiết nếu proof đủ mạnh.

---

# 563.134. Async ABI

Public async ABI không được thay đổi bởi optimization.

---

# 563.135. Closure optimization

Closure environment có thể:

- scalarize;
- stack-promote;
- inline;

nếu escape analysis chứng minh được.

---

# 563.136. Closure devirtualization

Indirect closure calls có thể trở thành direct call khi identity known.

---

# 563.137. Iterator fusion

Library/compiler optimization có thể fuse iterator chains.

Ví dụ:

```text
map → filter → reduce
```

thành một loop.

---

# 563.138. Fusion semantics

Fusion phải preserve:

- evaluation order;
- panic;
- side effects;
- allocation;
- overflow;
- iterator contract.

---

# 563.139. Whole-program vectorization

LTO có thể cung cấp loop facts từ caller/callee.

---

# 563.140. Cross-module alias proof

Vectorization chỉ được phép khi alias constraints đủ mạnh.

---

# 563.141. Parallel optimization

LTO tasks có thể chạy song song.

---

# 563.142. Deterministic merge

Kết quả phải độc lập worker order.

---

# 563.143. LTO scheduling

Task scheduler dùng `558`.

---

# 563.144. LTO query database

Global analysis có thể được model như compiler queries:

```text
Callers(Symbol)
Callees(Symbol)
Reachability(Symbol)
EffectSummary(Symbol)
TypeSet(Symbol)
InlineCandidate(Symbol)
```

---

# 563.145. Query identity

LTO query phải có snapshot + target + optimization context khi cần.

---

# 563.146. Snapshot isolation

LTO build phải dùng immutable semantic snapshot.

---

# 563.147. Concurrent editing

Editor thay đổi source không được làm LTO job dùng lẫn hai snapshots.

---

# 563.148. Cancellation

Nếu LTO bị cancel:

- không publish partial artifact;
- cache partial state chỉ nếu artifact có validity metadata.

---

# 563.149. Failure recovery

Một failed LTO optimization region không được làm mất khả năng clean rebuild.

---

# 563.150. Optimization fallback

Compiler có thể fallback:

```text
Full LTO
 ↓ failure/resource limit
Thin LTO
 ↓
No LTO
```

chỉ khi build policy cho phép và kết quả semantics tương đương.

---

# 563.151. Fallback identity

Artifact phải ghi nhận mode thực tế:

```text
actual_lto_mode
```

---

# 563.152. Reproducibility

Nếu policy yêu cầu exact reproducibility, fallback không được tự động xảy ra mà không thay đổi build identity.

---

# 563.153. Distributed LTO

Thin-LTO có thể phân phối module optimization qua remote execution.

---

# 563.154. Remote cache

Remote LTO artifacts phải verify provenance/hash/signature theo `487/550`.

---

# 563.155. Cache poisoning

LTO cache hit không được trust chỉ vì key match; artifact integrity phải được kiểm tra.

---

# 563.156. Security boundary

LTO metadata từ package dependency được coi là untrusted input.

---

# 563.157. Malformed LTO metadata

Không được crash compiler.

---

# 563.158. Resource exhaustion

LTO parser phải giới hạn:

```text
graph nodes
edges
summary size
recursion
memory
CPU
```

---

# 563.159. Package boundary

Package compilation có thể publish LTO summary mà không publish private source.

---

# 563.160. Privacy

Summary không được vô tình leak:

- private source;
- local paths;
- secrets;
- environment data.

---

# 563.161. Debug information

Cross-module inline phải preserve inline call stack:

```text
A.foo
 └── B.bar
      └── C.baz
```

---

# 563.162. Debug provenance

Debugger phải biết code hiện tại originate từ module nào.

---

# 563.163. Coverage

LTO transformation phải preserve source coverage mapping theo `477`.

---

# 563.164. Profiling

Generated code phải preserve source→IR→machine attribution theo `476/481`.

---

# 563.165. Sanitizer

LTO không được eliminate sanitizer checks khi sanitizer semantics yêu cầu giữ chúng.

---

# 563.166. Security instrumentation

CFI/stack protection/hardening phải được thực hiện ở appropriate phase sau optimization hoặc được chứng minh tương đương.

---

# 563.167. LTO + CFI

Devirtualization có thể reduce CFI edges nhưng phải update CFI metadata chính xác.

---

# 563.168. LTO + PGO

Profile-guided transformation phải giữ profile provenance.

---

# 563.169. LTO + correctness

Mỗi transformation quan trọng phải được đưa vào `552` translation validation khi có thể.

---

# 563.170. Optimization chain

```text id="x7m3q9"
Source
 ↓
Semantic IR
 ↓
Module MIR
 ↓
LTO Summary
 ↓
Global Graph
 ↓
Cross-module transforms
 ↓
Optimized MIR
 ↓
Machine Backend
```

---

# 563.171. Transformation records

Mỗi global transformation ghi:

```text
Transformation {
    id
    pass
    inputs
    outputs
    reason
    evidence
}
```

---

# 563.172. Why optimized

AI/debug API:

```text
why_inlined(foo)
why_devirtualized(bar)
why_specialized(baz)
why_eliminated(qux)
```

---

# 563.173. Why not optimized

Ví dụ:

```text
WhyNot {
    reason
    required_fact
    current_proof_state
    budget
}
```

---

# 563.174. Reason categories

```text
UnknownAlias
ExternalVisibility
CodeSize
CompileTime
NoBenefit
ABIConstraint
FeatureConstraint
EffectConstraint
AddressTaken
SecurityBoundary
```

---

# 563.175. No universal optimization score

Axiom không tạo một “LTO quality score”.

---

# 563.176. LTO report

Compiler có thể xuất:

```text
axiom lto-report
```

với:

- imported functions;
- inlined functions;
- devirtualized calls;
- eliminated symbols;
- specialization;
- code growth;
- compile time;
- memory.

---

# 563.177. Machine-readable LTO report

JSON schema stable.

---

# 563.178. LTO visualization

Tooling có thể render:

```text
module → symbol → call graph
```

nhưng visualization không phải compiler semantic authority.

---

# 563.179. Incremental LTO

Thay đổi:

```text
A.private_function
```

không được invalidate unrelated B/C nếu dependency graph chứng minh độc lập.

---

# 563.180. Public signature change

Có thể invalidate nhiều downstream summaries.

---

# 563.181. Private body change

Chỉ invalidate summaries phụ thuộc vào body facts.

---

# 563.182. Summary levels

Axiom có thể lưu:

```text
ABI summary
Semantic summary
Optimization summary
Profile summary
```

tách biệt.

---

# 563.183. ABI summary stability

ABI summary có lifetime khác optimization summary.

---

# 563.184. Semantic summary

Semantic summary có thể survive optimization-profile changes.

---

# 563.185. Optimization summary

Phụ thuộc optimization profile.

---

# 563.186. Profile summary

Phụ thuộc profile artifact/version.

---

# 563.187. Cross-edition

LTO không được merge semantic units với incompatible language editions nếu semantics khác.

---

# 563.188. Cross-compiler

LTO IR/summary phải có compiler/schema version.

---

# 563.189. Version mismatch

Không hiểu schema:

```text
reject / fallback
```

không parse đoán.

---

# 563.190. Long-term format

LTO artifact format phải versioned.

---

# 563.191. Native object compatibility

Object không có LTO section vẫn link bình thường.

---

# 563.192. LTO disabled

`--lto=off` phải disable cross-module optimization.

---

# 563.193. LTO default

Default mode được quyết định bởi build profile, không semantic language rule.

---

# 563.194. Release profile

Release profile có thể chọn:

```text
thin
```

hoặc:

```text
full
```

---

# 563.195. Debug profile

Debug có thể mặc định `off` hoặc `thin` để giảm latency.

---

# 563.196. Correctness gate

LTO artifact phải qua:

```text
MIR verifier
LTO verifier
Machine verifier
Object verifier
```

---

# 563.197. Differential validation

Các transformation nguy hiểm có thể được kiểm tra bằng `552`.

---

# 563.198. LTO stress suite

Phải có test cho:

- thousands of modules;
- giant call graph;
- recursive SCC;
- trait graph;
- generic graph;
- FFI;
- dynamic libraries;
- mixed objects;
- PGO;
- cache invalidation;
- parallel builds.

---

# 563.199. Acceptance criteria

Axiom LTO chỉ được coi hoàn thiện khi:

```text
Off
Thin
Full
```

đều:

1. preserve semantics;
2. preserve ABI;
3. support incremental cache;
4. deterministic;
5. parallelizable;
6. debuggable;
7. verifiable;
8. compatible with native linker.

---

# 563.200. HARD INVARIANTS

1. LTO không thay đổi language semantics.
2. LTO không thay đổi ownership semantics.
3. LTO không thay đổi memory model.
4. LTO không thay đổi panic semantics.
5. LTO không thay đổi error semantics.
6. LTO không tự tạo API mới.
7. LTO không phá ABI.
8. LTO không phá FFI.
9. LTO không phá dynamic-library boundary.
10. LTO phải phân biệt closed-world và open-world.
11. Public symbols phải được bảo vệ theo visibility.
12. Exported symbols phải được coi là roots nếu externally reachable.
13. FFI symbols phải được coi là roots khi contract yêu cầu.
14. Dynamic callbacks phải được coi là roots khi manifest yêu cầu.
15. Address-taken phải được phân tích riêng.
16. Function-pointer calls phải preserve.
17. Vtable ABI phải preserve.
18. Devirtualization cần proof.
19. Unknown không được coi là proven.
20. Inlining phải preserve observable behavior.
21. Inlining phải preserve panic behavior.
22. Inlining phải preserve cleanup.
23. Inlining phải preserve atomic behavior.
24. Inlining phải preserve volatile behavior.
25. Inlining phải preserve FFI behavior.
26. Inlining phải respect security boundaries.
27. Inlining phải respect realtime effects.
28. Constant propagation phải preserve semantics.
29. Constant propagation phải preserve overflow behavior.
30. Constant propagation phải preserve FP policy.
31. DCE không được loại bỏ observable code.
32. DCE không được loại bỏ roots.
33. DCE không được loại bỏ externally reachable symbols.
34. Global data elimination phải preserve address observability.
35. Identical code folding phải preserve address identity.
36. String merging phải preserve observable identity semantics.
37. Function cloning phải deterministic.
38. Clone explosion phải bounded.
39. Specialization phải deterministic.
40. Generic specialization phải preserve semantics.
41. Cross-module alias analysis phải conservative khi cần.
42. FFI mặc định là unknown effect.
43. Unannotated foreign functions không được coi là pure.
44. Unannotated foreign functions không được coi là no-alloc.
45. Unannotated foreign functions không được coi là no-panic.
46. Unannotated foreign functions không được coi là no-block.
47. Atomic operations không được reorder trái memory model.
48. Volatile operations không được eliminate.
49. I/O effects phải preserve.
50. Drop semantics phải preserve.
51. Cleanup order phải preserve.
52. Ownership facts không được biến thành runtime semantic changes.
53. Escape analysis phải conservative khi external alias tồn tại.
54. Allocation elimination cần proof.
55. Stack promotion phải preserve lifetime.
56. Scalar replacement phải preserve observable address.
57. Bounds-check elimination cần proof.
58. Contract proof state phải được preserve.
59. RuntimeChecked không phải compile-time proof.
60. Unknown không phải false.
61. Overflow semantics không được thay đổi.
62. Floating-point reassociation phải obey FP mode.
63. NaN semantics phải preserve.
64. Signed-zero semantics phải preserve.
65. Atomic ordering phải preserve.
66. Async state semantics phải preserve.
67. Closure semantics phải preserve.
68. Iterator fusion phải preserve evaluation order.
69. Iterator fusion phải preserve side effects.
70. Iterator fusion phải preserve panic.
71. Tail-call optimization phải obey ABI.
72. Recursive optimization phải bounded.
73. SCC analysis phải deterministic.
74. Call graph phải preserve provenance.
75. Symbol identity phải semantic, không chỉ textual.
76. LTO summary không phải source of truth.
77. Semantic DB là source of truth.
78. Summary conflict phải invalidate summary.
79. Summary schema phải versioned.
80. Summary dependency fingerprint phải explicit.
81. Summary invalidation phải dependency-aware.
82. Unrelated changes không được invalidate toàn bộ graph mặc định.
83. Public signature changes phải invalidate relevant consumers.
84. Private body changes chỉ invalidate dependent facts.
85. Target-dependent summaries không được reuse sai target.
86. ABI-dependent summaries không được reuse sai ABI.
87. Optimization-profile-dependent summaries không được reuse sai profile.
88. PGO summaries phải có provenance.
89. Stale PGO không được coi exact.
90. Cache key phải chứa semantic identity.
91. Cache key phải chứa relevant dependencies.
92. Cache key phải chứa target fingerprint.
93. Cache key phải chứa LTO mode.
94. Cache key phải chứa optimization profile.
95. Cache key phải chứa compiler build identity.
96. Cache hit phải tương đương recomputation.
97. Corrupted cache phải reject.
98. Untrusted cache phải verify.
99. Remote cache phải verify provenance.
100. LTO metadata phải coi là untrusted input.
101. Malformed metadata không được crash compiler.
102. Resource exhaustion phải bounded.
103. Graph size phải bounded.
104. Recursion phải bounded.
105. Import count phải bounded.
106. Import code growth phải bounded.
107. Full LTO memory phải budgeted.
108. Thin LTO phải support parallel execution.
109. Parallel LTO phải deterministic.
110. Worker order không được ảnh hưởng semantics.
111. Cache hit không được ảnh hưởng semantics.
112. Task scheduling không được ảnh hưởng semantics.
113. Remote execution không được ảnh hưởng semantics.
114. Thin LTO và full LTO phải semantic-equivalent.
115. No-LTO và LTO phải semantic-equivalent.
116. LTO fallback phải explicit trong artifact identity.
117. Reproducible mode không được silent fallback.
118. LTO cancellation không được publish partial invalid artifact.
119. Failed optimization không được corrupt clean build path.
120. Global index phải snapshot-consistent.
121. LTO phải sử dụng immutable semantic snapshot.
122. Editor changes không được contaminate running LTO.
123. Debug inline provenance phải preserve.
124. Coverage mapping phải preserve.
125. Profiling mapping phải preserve.
126. Sanitizer semantics phải preserve.
127. CFI metadata phải update sau devirtualization.
128. Security policy phải survive LTO.
129. Constant-time constraints phải survive LTO.
130. Realtime constraints phải survive LTO.
131. `no_alloc` effects phải survive LTO.
132. `no_block` effects phải survive LTO.
133. `no_panic` effects phải survive LTO.
134. Effect summaries phải provenance-rich.
135. Optimization decisions phải explainable.
136. `why_not_optimized` phải distinguish proof from heuristic.
137. Optimization evidence không được tự nhận là correctness proof.
138. Critical transformations phải integrate `552`.
139. Translation validation failures phải stop hoặc fallback theo explicit policy.
140. LTO verifier phải reject invalid global IR.
141. Global graph không được trở thành semantic source of truth.
142. LTO không được sửa parser semantics.
143. LTO không được sửa type semantics.
144. LTO không được sửa trait semantics.
145. LTO không được sửa ownership semantics.
146. LTO không được sửa concurrency semantics.
147. LTO không được sửa error semantics.
148. LTO không được sửa ABI declarations.
149. LTO không được bypass security policy.
150. LTO không được bypass compiler trust policy.
151. LTO phải integrate `430`.
152. LTO phải integrate `431`.
153. LTO phải integrate `436`.
154. LTO phải integrate `437`.
155. LTO phải integrate `450`.
156. LTO phải integrate `479`.
157. LTO phải integrate `487`.
158. LTO phải integrate `549`.
159. LTO phải integrate `552`.
160. LTO phải integrate `553`.
161. LTO phải integrate `554`.
162. LTO phải integrate `555`.
163. LTO phải integrate `558`.
164. LTO phải integrate `559`.
165. LTO phải integrate `561`.
166. LTO phải integrate `562`.
167. Static libraries phải hỗ trợ LTO metadata.
168. Normal objects phải coexist với LTO objects.
169. C objects phải coexist với LTO objects.
170. Dynamic libraries phải có explicit optimization boundary.
171. External symbols phải preserve.
172. ABI-stable public functions không được biến mất.
173. Symbol visibility phải preserve.
174. Relocation semantics phải preserve.
175. Linker phải remain independent of semantic optimization.
176. LTO-generated objects phải hợp lệ với linker.
177. Object debug sections phải remain consistent.
178. Object unwind sections phải remain consistent.
179. Function ordering phải deterministic.
180. Hot/cold partitioning phải deterministic.
181. Section placement phải deterministic.
182. Clone naming phải deterministic.
183. Summary serialization phải deterministic.
184. Global index serialization phải deterministic.
185. LTO reports phải machine-readable.
186. AI queries phải preserve snapshot identity.
187. AI queries phải preserve provenance.
188. AI explanations không được biến heuristic thành fact.
189. LTO visualization không phải semantic authority.
190. Package-private information không được leak qua public summary mặc định.
191. LTO artifact phải có compiler/schema provenance.
192. Incompatible summary schema phải reject/fallback.
193. Cross-edition optimization phải obey semantic compatibility.
194. Cross-target optimization phải obey target identity.
195. Cross-ABI optimization phải obey ABI identity.
196. Cross-profile optimization phải obey profile identity.
197. Incremental LTO phải preserve clean-build equivalence.
198. Distributed LTO phải preserve local-build equivalence.
199. Full LTO phải remain optional; Axiom không được biến LTO thành runtime requirement.
200. **Final invariant:** Axiom phải có khả năng tối ưu xuyên module/package bằng **No-LTO, Thin-LTO và Full-LTO**, trong đó mọi cross-module transformation đều dựa trên semantic facts + dependency provenance + proof/analysis state; cache, parallelism, PGO, devirtualization, specialization và LTO mode không được làm thay đổi semantics; ABI/FFI/dynamic boundaries phải được bảo vệ; và kết quả LTO phải tương đương một clean compilation theo cùng semantic contract.

**BOOTSTRAP-563: LOCKED.**

---

# NEXT — BOOTSTRAP-564

## COMPILER LINKER 3.0 — WHOLE-PROGRAM LINKING, SYMBOL RESOLUTION, SECTION GC, ICF, RELAXATION, TLS, IMPORT/EXPORT & FINAL IMAGE OPTIMIZATION

`563` đã đưa optimization xuyên module đến ngay trước linker. Bước tiếp theo cần khóa lại **linker ở mức whole-program/native image** để hoàn thiện chuỗi:

```text
Source
 ↓
Semantic
 ↓
MIR
 ↓
LTO
 ↓
Machine IR
 ↓
Machine Code
 ↓
Object
 ↓
┌─────────────────────────────┐
│        Axiom Linker 3.0     │
│                             │
│ Symbol Resolution           │
│ Archive Extraction          │
│ COMDAT/Weak                 │
│ Section GC                  │
│ ICF                         │
│ Layout                      │
│ TLS                         │
│ Imports / Exports           │
│ Relocations                 │
│ Relaxation                  │
│ PLT/GOT / IAT               │
│ PE/ELF/Mach-O policies      │
│ Final Image                 │
└──────────────┬──────────────┘
               ↓
        EXE / ELF / Mach-O
        DLL / SO / DYLIB
        Static Library
        WASM Module
```

Đặc biệt `564` sẽ giải quyết phần còn thiếu để mục tiêu **“binary nhỏ như ASM nhưng vẫn hỗ trợ executable/library native đầy đủ”** trở thành một contract cụ thể, thay vì chỉ phụ thuộc vào object writer `420`.