# BOOTSTRAP-572 — COMPILER STATIC ANALYSIS 3.0
## NULLABILITY, INITIALIZATION, RESOURCE FLOW, ALIAS ANALYSIS, RACE ANALYSIS, UNREACHABLE STATES, SECURITY FLOWS & WHOLE-PROGRAM PROGRAM PROPERTIES

**Trạng thái: COMPLETED / LOCKED**

`572` xây tầng **Static Analysis** phía trên `571`. Đây là hệ thống phân tích chương trình độc lập với type checker nhưng sử dụng cùng MIR, CFG, Dataflow, ownership/resource facts và semantic database.

Mục tiêu quan trọng:

> **Axiom không cần một borrow checker nặng kiểu Rust để có static analysis mạnh. Compiler chỉ biến một property thành hard semantic error khi có proof đủ chắc chắn; các trường hợp chưa chứng minh được được phân loại thành warning/advisory thay vì giả vờ chắc chắn.**

---

# 572.1. Architecture

```text id="w7ks3x"
                         Source
                           │
                           ▼
                        HIR/MIR
                           │
                           ▼
                   CFG + Dataflow 571
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      Value Flow       Memory Flow      Resource Flow
          │                │                │
          ├─ Nullability   ├─ Alias         ├─ Move
          ├─ Init          ├─ Escape        ├─ Consume
          ├─ Range         ├─ Memory SSA    └─ Cleanup
          └─ Reachability └─ Effects
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                 Static Analysis Engine
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
        Safety          Security        Whole Program
                           │
                           ▼
                   Diagnostic Engine 569
```

---

# 572.2. Analysis classes

Mỗi property thuộc một trong:

```text id="p7a2z1"
Proven
Potential
Unknown
NotApplicable
```

---

# 572.3. Proven

Compiler có đủ facts để chứng minh property.

---

# 572.4. Potential

Có ít nhất một path có khả năng vi phạm.

---

# 572.5. Unknown

Không đủ information.

---

# 572.6. Không được đánh đồng

`Unknown != ProvenSafe`.

---

# 572.7. Safety policy

Compiler policy quyết định property nào là:

```text id="f7c9xq"
error
warning
info
ignored
```

---

# 572.8. Analysis profile

Có các profile:

```text id="3l5n0d"
minimal
standard
strict
security
audit
```

---

# 572.9. Minimal profile

Các analysis rẻ và chắc chắn.

---

# 572.10. Standard profile

Default production analysis.

---

# 572.11. Strict profile

Thêm analyses có cost cao hơn.

---

# 572.12. Security profile

Bật taint/security-flow analyses.

---

# 572.13. Audit profile

Whole-program analysis sâu.

---

# 572.14. Analysis configuration

Configuration là explicit build input nếu nó ảnh hưởng compiler diagnostics/semantics.

---

# 572.15. Compiler semantics

Static analysis không được âm thầm thay đổi language semantics.

---

# 572.16. Nullability

Nếu một type/value có trạng thái nullable, analyzer track:

```text id="5l2xgr"
DefinitelyNull
DefinitelyNonNull
MaybeNull
Unknown
```

---

# 572.17. Null dereference

Dereference `DefinitelyNull` → diagnostic.

---

# 572.18. Maybe-null

`MaybeNull` → warning/error tùy policy.

---

# 572.19. Non-null

`DefinitelyNonNull` cho phép optimizer/safety checker dùng fact.

---

# 572.20. Null refinement

```text id="4w7mnp"
if x != null {
    ...
}
```

refine branch thành `DefinitelyNonNull`.

---

# 572.21. Refinement invalidation

Mutation/aliasing/call có thể invalidate nullability fact.

---

# 572.22. Optional values

`Option<T>` được phân tích bằng pattern/control-flow facts.

---

# 572.23. Exhaustive option matching

Exhaustive handling giúp loại bỏ null/none states trong branch.

---

# 572.24. Nullability và raw pointer

Raw pointer không được coi là non-null chỉ vì type checker cho phép nó tồn tại.

---

# 572.25. Unsafe boundary

Unsafe operations phải explicit trong analysis provenance.

---

# 572.26. Initialization

Analyzer track:

```text id="2uk5f9"
Uninitialized
Initialized
MaybeInitialized
Moved
Invalid
```

---

# 572.27. Definite initialization

Use `Uninitialized` → hard diagnostic nếu language rule yêu cầu.

---

# 572.28. Partial initialization

Struct fields được track riêng nếu cần.

---

# 572.29. Aggregate initialization

Construction phải tạo initialization facts cho tất cả required fields.

---

# 572.30. Array initialization

Fixed-size arrays phải track initialized elements khi static proof khả thi.

---

# 572.31. Dynamic indexing

Dynamic index thường dẫn tới conservative `MaybeInitialized`.

---

# 572.32. Loop initialization

Analyzer phải xử lý loop fixed point.

---

# 572.33. Conditional initialization

```text id="tqf1jj"
if condition {
    x = value
}
use(x)
```

chỉ safe nếu condition coverage chứng minh initialization.

---

# 572.34. Match initialization

Match branches phải được merge chính xác.

---

# 572.35. Early return

Early return path được loại khỏi subsequent flow.

---

# 572.36. Panic path

Panic/unreachable path không được coi là continuing path.

---

# 572.37. Resource flow

Analyzer sử dụng ownership model `423`.

---

# 572.38. Resource states

```text id="2vv3q5"
Owned
Moved
BorrowedLocal
Consumed
Released
Escaped
Unknown
```

---

# 572.39. Move

Sau move:

```text id="cr4k4x"
state = Moved
```

---

# 572.40. Use-after-move

Use `Moved` → diagnostic.

---

# 572.41. Double consume

Consume `Consumed/Released` resource → diagnostic.

---

# 572.42. Cleanup

Cleanup path phải biết resource có cần drop hay không.

---

# 572.43. Conditional cleanup

Nếu resource chỉ initialized trên một branch, cleanup phải conditional tương ứng.

---

# 572.44. Scope exit

Resource cleanup tại scope exit phải được represented.

---

# 572.45. Defer

`defer` registration được track trong resource flow.

---

# 572.46. Defer order

Multiple defer actions giữ reverse-registration ordering theo language semantics.

---

# 572.47. Return + defer

Return value evaluation và cleanup ordering phải đúng với MIR.

---

# 572.48. Panic + defer

Panic path phải đi qua cleanup nếu configured unwind semantics yêu cầu.

---

# 572.49. Abort

Abort path không tạo normal cleanup guarantees ngoài những semantics explicitly defined.

---

# 572.50. Resource escape

Nếu resource escape scope, state chuyển `Escaped`.

---

# 572.51. Escape analysis

Escape analysis xác định:

```text id="5t4j8q"
stack-local
heap
caller-owned
global
thread-shared
unknown
```

---

# 572.52. Allocation optimization

Stack promotion chỉ được phép nếu escape analysis chứng minh an toàn.

---

# 572.53. Heap elimination

Heap allocation elimination phải preserve resource/destructor semantics.

---

# 572.54. Alias analysis

Core alias states:

```text id="u5j7oc"
NoAlias
MustAlias
MayAlias
Unknown
```

---

# 572.55. MustAlias

Hai references chắc chắn cùng memory location.

---

# 572.56. NoAlias

Không thể cùng memory location trong analysis model.

---

# 572.57. MayAlias

Có thể cùng location.

---

# 572.58. Unknown alias

Không đủ information.

---

# 572.59. Alias conservatism

Optimizer chỉ dùng `NoAlias`/`MustAlias` khi proof hợp lệ.

---

# 572.60. Field-sensitive alias

Analyzer nên phân biệt fields khi representation cho phép.

---

# 572.61. Array alias

Index khác nhau chỉ được coi `NoAlias` khi bounds/index analysis chứng minh.

---

# 572.62. Slice alias

Slices có thể overlap.

---

# 572.63. Raw pointer alias

Raw pointer mặc định conservative.

---

# 572.64. Address escape

Taking address có thể chuyển stack object thành escaped tùy lifetime model.

---

# 572.65. Memory SSA

Memory analysis dùng Memory SSA khi có lợi.

---

# 572.66. Memory clobber

Unknown call có thể clobber memory theo function effect summary.

---

# 572.67. Function effects

Function summary có thể chứa:

```text id="1xj3cz"
ReadSet
WriteSet
Allocate
Free
Throw
Panic
Synchronize
IO
```

---

# 572.68. Pure functions

Pure classification phải có proof hoặc explicit trusted contract.

---

# 572.69. External functions

Không có summary → conservative effects.

---

# 572.70. FFI

FFI boundary mặc định conservative trừ khi ABI metadata cung cấp effects.

---

# 572.71. Thread sharing

Data shared giữa threads được đánh dấu `Shared`.

---

# 572.72. Send/Share

Static analysis sử dụng semantic traits `Send`/`Share` hoặc tương đương đã định nghĩa trong concurrency model.

---

# 572.73. Race analysis

Race detector tĩnh tìm:

```text id="l1v2xm"
concurrent access
+
same memory
+
at least one write
+
insufficient synchronization
```

---

# 572.74. Definite race

Chỉ hard error khi concurrency model chứng minh race chắc chắn.

---

# 572.75. Potential race

Potential race → warning/advisory tùy profile.

---

# 572.76. Unknown synchronization

Unknown synchronization không được coi là proof of safety.

---

# 572.77. Atomic access

Atomic operations được model riêng.

---

# 572.78. Atomic ordering

Memory ordering phải được đưa vào race analysis.

---

# 572.79. Lockset

Analyzer có thể track held locks:

```text id="6n9z2b"
HeldLocks
```

---

# 572.80. Lock acquire

Acquire thêm lock vào lockset.

---

# 572.81. Lock release

Release loại lock khỏi lockset.

---

# 572.82. Double lock

Potential deadlock/reentrant lock behavior phải phụ thuộc lock semantics.

---

# 572.83. Lock ordering

Strict profile có thể kiểm tra lock-order cycles.

---

# 572.84. Deadlock cycle

```text id="4m7k0p"
Thread A: Lock X → Y
Thread B: Lock Y → X
```

được report là potential deadlock nếu concurrent paths có thể xảy ra.

---

# 572.85. False-positive policy

Deadlock analyzer phải phân biệt definite/potential/unknown.

---

# 572.86. Channel analysis

Channels được model như synchronization edges.

---

# 572.87. Send/receive

Send/receive có thể transfer ownership/dataflow facts.

---

# 572.88. Actor analysis

Actor mailbox boundaries được xem là concurrency isolation points.

---

# 572.89. Async race

Cross-await mutation phải được analysis theo task/interleaving model.

---

# 572.90. Await boundary

Facts không còn chắc chắn nếu shared state có thể mutate trong thời gian suspension.

---

# 572.91. Thread escape

Object escaping into another thread không được coi thread-local nữa.

---

# 572.92. Thread-local

TLS state được model separately.

---

# 572.93. Global analysis

Global mutable state được tracked ở whole-program profile.

---

# 572.94. Static initialization

Initialization ordering issues phải có analysis khi multiple modules involved.

---

# 572.95. Unreachable states

Analyzer dùng CFG + predicate facts để detect impossible states.

---

# 572.96. Unreachable branch

Branch proven unreachable → optional warning.

---

# 572.97. Unreachable match case

Case proven impossible → diagnostic.

---

# 572.98. Contradictory condition

```text id="t5k5cp"
x > 10 && x < 5
```

có thể tạo unreachable branch khi range proof đủ mạnh.

---

# 572.99. Assertion analysis

After:

```text id="v1o4py"
assert(x != null)
```

flow state được refined.

---

# 572.100. Assume

An explicit trusted `assume` may refine facts but must be marked unsafe/trusted according to language rules.

---

# 572.101. Assume provenance

All facts derived from `assume` retain provenance.

---

# 572.102. Taint analysis

Security profile hỗ trợ taint sources/sinks.

---

# 572.103. Taint state

```text id="e3j5mc"
Clean
Tainted
Sanitized
Unknown
```

---

# 572.104. Taint source

Examples:

```text id="f5m4s9"
network input
file input
environment
IPC
user input
```

---

# 572.105. Taint sink

Examples:

```text id="h8kjy1"
command execution
SQL execution
filesystem path
HTML output
unsafe FFI
```

---

# 572.106. Taint propagation

Assignments/calls propagate taint according to summaries.

---

# 572.107. Sanitizer

Explicit sanitizer function can clear specific taint categories.

---

# 572.108. Contextual sanitization

Sanitization is sink/context specific.

---

# 572.109. Taint categories

Không dùng một bit `tainted` duy nhất cho mọi security property.

Có thể có:

```text id="v7v6c0"
SQL
Command
Path
HTML
Network
Secret
```

---

# 572.110. Secret flow

Analyzer có thể track sensitive/secret data.

---

# 572.111. Secret sink

Logging, telemetry, external network và diagnostics có thể là sinks tùy policy.

---

# 572.112. Secret propagation

Secret labels propagate through ordinary dataflow.

---

# 572.113. Declassification

Explicit declassification policy required.

---

# 572.114. Capability flow

Security capabilities có thể được track qua function calls.

---

# 572.115. Privilege boundary

Crossing process/plugin/security boundary tạo analysis event.

---

# 572.116. Sandbox analysis

Code attempting unavailable capability có thể được detect statically khi capability set known.

---

# 572.117. Path traversal

Static analyzer có thể phát hiện known unsafe path composition khi facts đủ mạnh.

---

# 572.118. Injection analysis

Security analyzer phải dùng taint/context, không chỉ regex.

---

# 572.119. Integer safety

Range analysis có thể detect:

```text id="zgrb3m"
overflow
underflow
division by zero
shift overflow
```

---

# 572.120. Division by zero

Known zero divisor → definite error.

---

# 572.121. Potential zero

Potential zero → warning nếu operation không defined.

---

# 572.122. Shift analysis

Shift count ngoài range → diagnostic.

---

# 572.123. Bounds analysis

Array/slice accesses dùng range facts.

---

# 572.124. Definite out-of-bounds

Known invalid index → hard diagnostic.

---

# 572.125. Potential out-of-bounds

Unknown runtime index → không được tự động coi là error nếu runtime bounds checking đảm bảo safety.

---

# 572.126. Bounds-check elimination

Optimizer chỉ eliminate check khi analysis chứng minh bounds.

---

# 572.127. Checked runtime

Nếu language operation semantics là checked, static analysis không được thay đổi semantics thành unchecked chỉ vì heuristic.

---

# 572.128. Unsafe indexing

Explicit unchecked operation phải tạo safety boundary.

---

# 572.129. Pointer arithmetic

Pointer arithmetic thuộc unsafe/conservative analysis domain.

---

# 572.130. Use-after-free

Resource/memory analysis có thể detect definite use-after-free khi ownership facts đủ.

---

# 572.131. Double-free

Definite double-free → hard error.

---

# 572.132. Unknown free

External allocator semantics unknown → conservative.

---

# 572.133. Allocator identity

Allocation/free phải track allocator family khi necessary.

---

# 572.134. Cross-allocator free

Known mismatch → diagnostic.

---

# 572.135. FFI ownership

FFI metadata có thể declare:

```text id="9g0qkh"
takes ownership
borrows
returns ownership
```

---

# 572.136. Missing FFI ownership metadata

Unknown → conservative analysis, không tự suy diễn.

---

# 572.137. Whole-program mode

Whole-program analysis chạy trên complete call/module graph.

---

# 572.138. Closed world

Closed-world assumptions chỉ được dùng khi build explicitly declares closed world.

---

# 572.139. Open world

Dynamic libraries/plugins/FFI làm analyzer conservative.

---

# 572.140. Dynamic dispatch

Dyn trait calls có candidate set từ vtable/type metadata.

---

# 572.141. Dynamic dispatch unknown

Unknown implementations → conservative effects.

---

# 572.142. Call graph

Static analyzer sử dụng call graph từ semantic/compiler infrastructure.

---

# 572.143. Call graph SCC

Recursive components được fixed-point analyze.

---

# 572.144. Function summary

Summary:

```text id="k4a3t8"
inputs
outputs
reads
writes
allocations
resource effects
exceptions
locks
taint
```

---

# 572.145. Summary caching

Summary cache key:

```text id="n8t9p4"
FunctionSemanticId
MIRIdentity
Target
AnalysisProfile
```

---

# 572.146. Summary invalidation

Function body change invalidate affected summaries.

---

# 572.147. Summary reuse

Unchanged function summaries có thể reuse across incremental builds.

---

# 572.148. Interprocedural propagation

Caller analysis consume callee summary thay vì phân tích lại callee mỗi lần.

---

# 572.149. Context budget

Analyzer giới hạn interprocedural context depth.

---

# 572.150. Path budget

Path-sensitive analysis có maximum exploration budget.

---

# 572.151. State merging

Equivalent abstract states phải merge.

---

# 572.152. State canonicalization

Abstract state representation deterministic.

---

# 572.153. Analysis timeout

Analysis có thể timeout.

---

# 572.154. Timeout semantics

Timeout → `Unknown`, không → `Safe`.

---

# 572.155. Analysis cancellation

IDE/daemon request có thể cancel analysis.

---

# 572.156. Partial results

Partial results phải đánh dấu incomplete.

---

# 572.157. Security severity

Security findings có:

```text id="w6x8ay"
Definite
High-confidence
Potential
Informational
```

---

# 572.158. Không dùng score tùy tiện

Risk severity phải đến từ rule/policy đã định nghĩa, không từ AI tự chấm.

---

# 572.159. Diagnostic integration

Mọi finding đi qua `569`.

---

# 572.160. Causal explanation

Finding phải có:

```text id="s8c8x1"
source
flow path
sink
supporting facts
```

---

# 572.161. Flow path

Security diagnostic có thể show path:

```text id="j2j8q6"
Source
 ↓
assignment
 ↓
call
 ↓
sink
```

---

# 572.162. Path compression

Path dài có thể collapse intermediate nodes.

---

# 572.163. AI explanation

AI được phép giải thích flow graph nhưng compiler facts vẫn canonical.

---

# 572.164. AI query

AI có thể hỏi:

```text id="h1z4h8"
why unsafe?
what path?
what assumption?
what sanitizer?
```

---

# 572.165. Static analysis database

Analysis results có thể persist trong `.axsem`/analysis cache.

---

# 572.166. Provenance

Mỗi finding lưu analysis version/profile.

---

# 572.167. Analyzer version

Thay đổi analyzer algorithm có thể invalidate findings.

---

# 572.168. Semantic vs advisory cache

Compiler semantic cache và advisory analysis cache phải phân biệt.

---

# 572.169. Advisory cache

Stale advisory finding không được ảnh hưởng compilation correctness.

---

# 572.170. Incremental analysis

Chỉ recompute affected flow regions/functions.

---

# 572.171. Change propagation

Change → dependent summaries → affected callers.

---

# 572.172. SCC invalidation

Trong recursive SCC, một change có thể invalidate toàn SCC.

---

# 572.173. Parallel analysis

Independent functions có thể analyze song song.

---

# 572.174. Deterministic analysis

Parallel analysis phải tạo cùng findings như serial analysis.

---

# 572.175. Scheduler integration

`568` có thể schedule static-analysis actions.

---

# 572.176. Resource integration

Static analyzer phải declare memory/CPU estimate cho orchestrator.

---

# 572.177. Distributed analysis

Large whole-program analyses có thể chạy remote nếu analysis inputs hermetic.

---

# 572.178. Remote trust

Remote analyzer không phải semantic authority.

---

# 572.179. Verification

Critical findings có thể được recompute locally.

---

# 572.180. Cache integrity

Cached analysis result phải validate source/MIR/profile identity.

---

# 572.181. False-positive control

Analyzer phải cung cấp suppression mechanisms có provenance.

---

# 572.182. Local suppression

Source-level suppression chỉ suppress advisory analysis tương ứng.

---

# 572.183. Security suppression

Security suppression phải explicit và audit được.

---

# 572.184. Suppression expiry

Có thể support expiry/version constraints cho suppression.

---

# 572.185. Dead-code suppression

Dead-code warning không được suppress unrelated diagnostics.

---

# 572.186. Testing — reference interpreter

Critical analyses phải được test bằng reference semantics.

---

# 572.187. Differential analysis

So sánh optimized/unoptimized execution khi analysis dùng cho transformation.

---

# 572.188. Fuzzing

Fuzz:

```text id="5lq8gt"
CFG
loops
aliases
ownership
concurrency
taint
```

---

# 572.189. Race fuzzing

Generate concurrent programs với known synchronization/race outcomes.

---

# 572.190. Taint fuzzing

Generate source→sink paths và sanitizer combinations.

---

# 572.191. Soundness tests

Known violation phải luôn được phát hiện trong các analyses được cam kết sound.

---

# 572.192. Conservative tests

Unknown state không được biến thành safe state.

---

# 572.193. Regression suite

Mọi fixed bug phải trở thành permanent analysis test.

---

# 572.194. Performance

Standard profile phải phù hợp incremental IDE usage.

---

# 572.195. Deep audit

Security/whole-program profile có thể tốn nhiều tài nguyên hơn.

---

# 572.196. No mandatory heavy checker

Static analysis không được biến thành mandatory Rust-style borrow/lifetime checker.

---

# 572.197. Compiler safety boundary

Chỉ các properties mà Axiom language semantics yêu cầu mới trở thành compile-blocking errors.

---

# 572.198. Optimization boundary

Optimization chỉ dùng facts đã được chứng minh phù hợp với required soundness level.

---

# 572.199. Unified analysis authority

Nullability, initialization, resource, alias, race, taint và whole-program analysis đều dùng chung `571 Dataflow Engine`, shared semantic facts và `569 Diagnostic Engine`.

---

# 572.200. FINAL HARD INVARIANT

> **Axiom Static Analysis 3.0 phải phân biệt tuyệt đối giữa “đã chứng minh”, “có khả năng”, và “chưa biết”. Mọi analysis safety-critical phải conservative; timeout, thiếu metadata, dynamic dispatch, FFI hoặc open-world assumptions chỉ có thể làm giảm mức độ chắc chắn chứ không được biến thành proof giả. Static analysis không được biến Axiom thành một borrow-checker nặng; nó là một tầng phân tích độc lập, có thể incremental, parallel, cached và whole-program, nhưng semantic correctness vẫn thuộc compiler language rules và canonical semantic engine.**

**BOOTSTRAP-572: LOCKED.**

---

# NEXT — BOOTSTRAP-573

## COMPILER EFFECT SYSTEM 2.0 — FUNCTION EFFECTS, SIDE-EFFECT ANALYSIS, PURITY, IO, ALLOCATION, PANIC/THROW, CONCURRENCY EFFECTS & EFFECT-AWARE OPTIMIZATION

`573` sẽ chuẩn hóa một mảnh rất quan trọng đang được nhiều task sử dụng nhưng chưa có một contract thống nhất: **function effects**.

Hiện tại nhiều subsystem đã cần biết function:

```text
reads memory?
writes memory?
allocates?
frees?
does IO?
panics?
throws?
takes lock?
blocks?
spawns task?
touches global state?
```

`573` sẽ biến chúng thành một **Effect System thống nhất**, để:

```text
Function
   │
   ▼
Effect Summary
   ├── Pure
   ├── Read
   ├── Write
   ├── Allocate
   ├── Deallocate
   ├── IO
   ├── Panic
   ├── Throw
   ├── Synchronization
   ├── Spawn
   └── External/Unknown
```

được sử dụng chung bởi **optimizer, DCE, alias analysis, static analyzer, concurrency checker, FFI, async scheduler, IDE và AI semantic queries** mà không cần mỗi subsystem tự suy đoán side effects.

**BOOTSTRAP-573: NEXT.**