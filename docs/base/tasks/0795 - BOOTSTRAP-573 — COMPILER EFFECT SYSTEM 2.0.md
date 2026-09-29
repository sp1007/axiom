# BOOTSTRAP-573 — COMPILER EFFECT SYSTEM 2.0
## FUNCTION EFFECTS, SIDE-EFFECT ANALYSIS, PURITY, I/O, ALLOCATION, PANIC/THROW, CONCURRENCY EFFECTS & EFFECT-AWARE OPTIMIZATION

**Trạng thái: COMPLETED / LOCKED**

`573` chuẩn hóa **Effect System** dùng chung cho compiler, optimizer, static analyzer, concurrency engine, FFI, async runtime, IDE và AI semantic layer.

Mục tiêu là tránh tình trạng mỗi subsystem tự đoán side effect của function theo cách khác nhau.

---

## 573.1. Core architecture

```text
                    Function / Operation
                           │
                           ▼
                  Effect Inference Engine
                           │
                           ▼
                    Canonical Effect Set
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      Optimizer        Static Analysis    Concurrency
          │                │                │
          ├───────────────┼────────────────┤
          ▼                ▼                ▼
       FFI / ABI        Async/Runtime      IDE / AI
```

---

## 573.2. Effect là gì?

Effect mô tả **những observable hoặc semantically relevant actions** mà một function có thể gây ra ngoài việc tính toán giá trị trả về.

Ví dụ:

```text
fn add(a: i32, b: i32) -> i32
```

có thể có:

```text
Pure
```

Trong khi:

```text
fn save(path: String, data: Bytes) -> Result<>
```

có thể:

```text
ReadExternal
WriteExternal
IO
Error
```

---

## 573.3. Effect không phải return type

Một function có thể:

```text
Result<T>
```

nhưng vẫn có nhiều effects khác nhau.

---

## 573.4. Effect không phải exception

`Panic`, `Throw` và `ErrorReturn` là các effect/failure channels khác nhau.

---

## 573.5. Canonical effect representation

```text
EffectSet {
    memory
    allocation
    resource
    io
    control
    concurrency
    external
    security
}
```

---

# 573.6. Memory effects

Các trạng thái cơ bản:

```text
NoMemory
ReadMemory
WriteMemory
ReadWriteMemory
UnknownMemory
```

---

# 573.7. Allocation effects

```text
NoAllocate
Allocate
Deallocate
AllocateDeallocate
UnknownAllocation
```

---

# 573.8. Resource effects

```text
AcquireResource
ReleaseResource
ConsumeResource
TransferResource
UnknownResource
```

---

# 573.9. I/O effects

```text
NoIO
ReadIO
WriteIO
NetworkIO
FileIO
DeviceIO
ConsoleIO
UnknownIO
```

---

# 573.10. Control effects

```text
NoControlEscape
Panic
Throw
Abort
NonLocalReturn
UnknownControl
```

---

# 573.11. Concurrency effects

```text
NoConcurrency
AcquireLock
ReleaseLock
AtomicAccess
Block
Wake
Spawn
Join
Await
Cancel
Yield
UnknownConcurrency
```

---

# 573.12. External effects

```text
FFI
Syscall
Plugin
DynamicDispatch
ExternalProcess
UnknownExternal
```

---

# 573.13. Security effects

```text
AccessSecret
AccessCapability
ElevatePrivilege
CrossTrustBoundary
SecurityUnknown
```

---

# 573.14. Effect lattice

Effect inference sử dụng lattice:

```text
Pure
  ↓
ReadOnly
  ↓
ReadWrite
  ↓
External
  ↓
Unknown
```

Không phải mọi effect category đều dùng cùng một total ordering; mỗi category có lattice riêng.

---

# 573.15. Effect join

Nếu:

```text
A = ReadMemory
B = WriteMemory
```

thì:

```text
join(A,B) = ReadWriteMemory
```

---

# 573.16. Unknown propagation

`Unknown` không được tự động hạ xuống thành một effect cụ thể.

---

# 573.17. Effect inference

Compiler tự suy ra effects từ MIR.

---

# 573.18. Direct effects

Instruction trực tiếp tạo effect:

```text
load
store
alloc
free
syscall
atomic
lock
spawn
panic
```

được ghi nhận trực tiếp.

---

# 573.19. Transitive effects

Function call nhận effects từ callee summary.

---

# 573.20. Recursive functions

Recursive SCC được giải bằng fixed-point inference.

---

# 573.21. Function summary

Canonical summary:

```text
EffectSummary {
    direct_effects
    transitive_effects
    memory_regions
    resources
    synchronization
    failure
    external_calls
    confidence
}
```

---

# 573.22. Effect identity

Summary identity phụ thuộc:

```text
FunctionId
MIRIdentity
Target
FeatureSet
EffectAnalyzerVersion
```

---

# 573.23. Incremental effects

Function không thay đổi không cần infer lại effects.

---

# 573.24. Dependency invalidation

Nếu callee effect thay đổi, caller summaries phụ thuộc vào callee phải invalidate.

---

# 573.25. Effect inference không đổi semantics

Effect system chỉ mô tả semantics hiện có.

---

# 573.26. Purity

Function được đánh dấu `Pure` khi compiler chứng minh:

```text
no observable memory mutation
no external IO
no synchronization
no allocation with observable identity
no panic/throw unless explicitly modeled
no hidden external effects
```

---

# 573.27. Pure allocation

Allocation không nhất thiết làm function impure nếu allocation hoàn toàn local và không observable.

---

# 573.28. Escape-sensitive purity

Nếu allocated object escape → allocation trở thành observable và purity có thể mất.

---

# 573.29. Referential transparency

Compiler chỉ coi function referentially transparent khi effects và hidden state đều được chứng minh phù hợp.

---

# 573.30. Global reads

Đọc mutable global là effect.

---

# 573.31. Immutable global

Đọc immutable constant/global có thể không tạo memory effect observable.

---

# 573.32. TLS

TLS access là concurrency/execution-context effect nếu semantics yêu cầu.

---

# 573.33. Environment

Environment-variable access là external effect.

---

# 573.34. Time

Đọc system clock là observable external effect.

---

# 573.35. Randomness

Random source là observable external effect.

---

# 573.36. Entropy source

Hardware/system entropy phải được phân loại external/nondeterministic.

---

# 573.37. Determinism flag

Effect summary có thể chứa:

```text
Deterministic
ConditionallyDeterministic
Nondeterministic
Unknown
```

---

# 573.38. Logging

Logging là observable I/O/telemetry effect.

---

# 573.39. Debug logging

Debug-only logging phải được modeled theo compilation profile.

---

# 573.40. Allocation visibility

Allocation identity chỉ là observable khi có khả năng escape/compare/address/side effect.

---

# 573.41. Stack allocation

Stack allocation nội bộ thường không tạo observable allocation effect.

---

# 573.42. Heap allocation

Heap allocation mặc định là effect cho summary; optimizer có thể chứng minh allocation không observable và loại bỏ nó.

---

# 573.43. Deallocation

Destructor/drop có thể tạo arbitrary effects.

---

# 573.44. Drop effects

Drop implementation được infer như function effect bình thường.

---

# 573.45. Cleanup graph

Cleanup paths phải contribute effects vào summary.

---

# 573.46. Panic

`panic` là control/failure effect.

---

# 573.47. Panic-free

`NoPanic` chỉ được claim khi compiler chứng minh hoặc contract đáng tin cậy.

---

# 573.48. Throw

`Throw<T>` là typed control effect nếu exception model được bật.

---

# 573.49. Abort

Abort là terminal control effect.

---

# 573.50. Error return

`Result::Err` không tự động là effect; nó là ordinary value/control convention.

---

# 573.51. `try`

`try` propagation không tạo effect mới ngoài effects của underlying operation.

---

# 573.52. Async

Async function có effect `Await` nếu execution có suspension.

---

# 573.53. Awaited callee

Caller effect summary bao gồm effects của awaited callee.

---

# 573.54. Spawn

`spawn` tạo concurrency effect.

---

# 573.55. Join

`join` tạo synchronization effect.

---

# 573.56. Cancel

Cancellation propagation là concurrency/control effect.

---

# 573.57. Blocking

Blocking operation phải được đánh dấu `Block`.

---

# 573.58. Nonblocking

Compiler có thể dùng `NoBlock` cho scheduler/runtime optimization.

---

# 573.59. Lock effects

Lock acquire/release được track theo lock identity khi có thể.

---

# 573.60. Atomic effects

Atomic operations được phân biệt với ordinary memory writes.

---

# 573.61. Memory ordering

Effect metadata có thể chứa:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

---

# 573.62. Race analysis integration

`572` sử dụng canonical synchronization effects thay vì tự suy đoán từ source.

---

# 573.63. Alias integration

Memory read/write effects có thể tham chiếu abstract memory regions.

---

# 573.64. Region identity

Region có thể là:

```text
Local
Parameter
Global
Heap
TLS
Unknown
```

---

# 573.65. Parameter effects

Summary có thể biểu diễn:

```text
read(param0)
write(param1)
consume(param2)
```

---

# 573.66. Return effects

Function có thể trả ownership/resource.

---

# 573.67. Ownership transfer

Effect summary có thể mô tả:

```text
takes_ownership(param0)
returns_ownership
```

---

# 573.68. Borrow effect

Temporary/local borrow không nhất thiết trở thành public effect.

---

# 573.69. Escaping borrow

Nếu borrow escape function boundary, summary phải reflect lifetime/resource consequence.

---

# 573.70. FFI effect metadata

FFI declarations có thể cung cấp effect contract.

---

# 573.71. FFI trust

Compiler không tự tin vào FFI contract nếu function không được đánh dấu trusted/verified theo FFI rules.

---

# 573.72. Missing FFI summary

Mặc định:

```text
UnknownExternal
```

---

# 573.73. Syscalls

Syscall wrappers có thể có platform-specific summaries.

---

# 573.74. Platform-specific effects

Một function có thể có summary khác nhau theo target.

---

# 573.75. Conditional effects

Feature/target-dependent effect:

```text
if windows:
    WinAPI
if linux:
    Syscall
```

được giữ riêng trong target summary.

---

# 573.76. Dynamic dispatch

Dyn call effect là join của candidate implementations đã biết.

---

# 573.77. Open-world dynamic dispatch

Unknown implementation → `UnknownExternal` hoặc conservative effect.

---

# 573.78. Closed-world optimization

Closed-world build có thể resolve candidate set hoàn chỉnh.

---

# 573.79. Plugin boundary

Plugin invocation mặc định external/unknown.

---

# 573.80. Callback

Callback effect được modeled nếu function pointer signature/metadata chứa effect contract.

---

# 573.81. Function pointer

Effect contract là một phần của function type metadata khi cần.

---

# 573.82. Effect compatibility

Function passed as callback phải satisfy required effect bound.

---

# 573.83. Generic functions

Generic effect summary có thể phụ thuộc type parameter effects.

---

# 573.84. Effect constraints

Ví dụ conceptually:

```text
fn map<F: Fn(A)->B [Pure]>(...)
```

Compiler có thể yêu cầu callback không có forbidden effects.

---

# 573.85. Higher-order effects

Function accepting callbacks phải include callback effects trong summary nếu callback được invoke.

---

# 573.86. Conditional callback invocation

Nếu callback chỉ được invoke trên một branch, summary vẫn conservative nhưng có path-sensitive metadata nếu useful.

---

# 573.87. Effect polymorphism

Generic function có thể preserve caller-specific effect:

```text
effect(F)
```

---

# 573.88. Effect erasure

Runtime không bắt buộc phải carry effect metadata nếu compiler đã resolve statically.

---

# 573.89. Zero runtime overhead

Effect analysis phải hướng tới zero runtime overhead trong native optimized builds.

---

# 573.90. Effect-aware optimization

Optimizer có thể sử dụng:

```text
Pure
ReadOnly
NoPanic
NoAlloc
NoBlock
NoIO
```

để tối ưu.

---

# 573.91. Dead code elimination

Pure unused call có thể eliminate.

---

# 573.92. Impure call elimination

Impure call không được eliminate chỉ vì return value không dùng.

---

# 573.93. Common subexpression elimination

Pure expression có thể CSE nếu arguments và relevant state không đổi.

---

# 573.94. Read-only CSE

Read-only operation chỉ CSE khi memory dependencies chứng minh không thay đổi.

---

# 573.95. Store/load optimization

Effect regions kết hợp Memory SSA để eliminate redundant loads/stores.

---

# 573.96. Function reordering

Pure/readonly functions có thể reorder khi dependency graph cho phép.

---

# 573.97. Loop invariant code motion

Effect metadata giúp xác định operation có thể safely move khỏi loop.

---

# 573.98. Parallelization

Pure hoặc appropriately isolated operations có thể được candidate cho parallelization.

---

# 573.99. NoBlock optimization

Scheduler có thể ưu tiên nonblocking calls.

---

# 573.100. Async optimization

Compiler có thể loại bỏ unnecessary suspension khi effect/dataflow analysis chứng minh.

---

# 573.101. Panic optimization

`NoPanic` có thể loại bỏ một số exceptional cleanup paths khi semantics cho phép.

---

# 573.102. Exception table optimization

Known non-throwing functions có thể giảm unwind metadata.

---

# 573.103. Allocation optimization

`NoEscape` + local effect có thể enable stack promotion.

---

# 573.104. Allocation elimination

Nếu allocation/deallocation không observable, optimizer có thể eliminate.

---

# 573.105. Effect-aware inlining

Inlining heuristic dùng effect complexity cùng code size/cost model.

---

# 573.106. LTO

Whole-program LTO có thể refine summaries sau cross-module resolution.

---

# 573.107. Summary refinement

Initial conservative summary:

```text
Unknown
```

có thể refined thành precise effect sau body analysis.

---

# 573.108. No circular optimism

Caller không được assume callee purity chỉ vì caller itself được declared pure.

---

# 573.109. Trusted effect declaration

Explicit effect declarations có thể được compiler trust theo policy nhưng phải giữ provenance.

---

# 573.110. Verified effect declaration

Strongest declaration có thể yêu cầu compiler verify body.

---

# 573.111. Unsafe effect assertion

Unsafe/trusted assertion phải được đánh dấu rõ.

---

# 573.112. Effect mismatch

Nếu declared effect thấp hơn inferred effect:

```text
diagnostic
```

theo declaration policy.

---

# 573.113. Effect superset

Declaration có thể cho phép conservative superset nếu language rule hỗ trợ.

---

# 573.114. Effect annotations

Syntax effect annotation phải optional trong common code.

---

# 573.115. Inference-first design

Axiom không yêu cầu programmer annotate mọi function.

---

# 573.116. Explicit annotation

Annotation chủ yếu dùng cho:

```text
API contracts
FFI
security
optimization
generic constraints
```

---

# 573.117. Public API

Public library APIs có thể publish effect summary trong `.axsem`.

---

# 573.118. ABI

Effect metadata không bắt buộc thay đổi native calling convention.

---

# 573.119. ABI compatibility

Changing effects không tự động thay đổi machine ABI trừ khi effect-qualified function type là ABI-visible theo language contract.

---

# 573.120. Semantic metadata

Effect summaries được lưu trong semantic artifact.

---

# 573.121. AI semantic query

AI có thể query:

```text
what does this function modify?
can it allocate?
can it block?
can it panic?
does it access global state?
```

---

# 573.122. AI cannot invent effects

AI explanation phải lấy canonical effect summary.

---

# 573.123. IDE hover

IDE có thể hiển thị compact effect summary.

---

# 573.124. IDE filtering

Có thể tìm:

```text
all functions with IO
all blocking functions
all allocating functions
all functions touching global state
```

---

# 573.125. Static analysis integration

`572` consume effect summaries để giảm false positives.

---

# 573.126. Security integration

Security analyzer dùng external/IO/capability effects để xây trust-flow.

---

# 573.127. Build system integration

Build actions có thể biết package/compiler phase nào có external effects.

---

# 573.128. Compile-time purity

Comptime functions phải thỏa effect policy nghiêm ngặt hơn runtime functions.

---

# 573.129. Const evaluation

Const evaluator không được thực thi arbitrary runtime IO effects.

---

# 573.130. Compile-time filesystem

Nếu Axiom cho phép compile-time file access, nó phải là explicit build input/effect.

---

# 573.131. Reproducibility

Nondeterministic effects trong comptime phải bị cấm hoặc explicit external build input.

---

# 573.132. Cache correctness

Effect system không được dùng để cache một function nếu effect summary cho thấy observable state dependency.

---

# 573.133. Build cache

Pure deterministic compilation actions có thể được aggressively cached.

---

# 573.134. Runtime memoization

Memoization chỉ hợp lệ nếu function observable behavior phụ thuộc đầy đủ vào modeled inputs.

---

# 573.135. Hidden state

Unknown hidden state → không được classify Pure.

---

# 573.136. Volatile memory

Volatile access luôn được coi observable memory effect.

---

# 573.137. MMIO

Memory-mapped device IO phải được mark volatile/device effect.

---

# 573.138. Inline assembly

Inline assembly mặc định có conservative effect clobber set.

---

# 573.139. Assembly constraints

Explicit clobber declarations refine effect summary.

---

# 573.140. CPU instructions

Ordinary deterministic instructions không tạo external effect.

---

# 573.141. Hardware nondeterminism

Instructions đọc clock/counter/random hardware được phân loại tương ứng.

---

# 573.142. SIMD

SIMD computation không tạo effect chỉ vì dùng vector registers.

---

# 573.143. GPU

GPU dispatch là external/device/concurrency effect.

---

# 573.144. GPU synchronization

Device synchronization phải được represented trong effect graph.

---

# 573.145. Network

Network read/write là external IO.

---

# 573.146. File

File read/write là external IO.

---

# 573.147. Process

Process spawn/wait là external + concurrency/control effect.

---

# 573.148. Signals

Signal handlers có asynchronous external effect semantics.

---

# 573.149. Signal safety

Functions callable from signal contexts có thể yêu cầu restricted effect profile.

---

# 573.150. Reentrancy

Effect metadata có thể biểu diễn reentrancy restrictions.

---

# 573.151. Thread safety

Effect summary không tự chứng minh thread safety; race analysis `572` vẫn là authority.

---

# 573.152. No false safety

`ReadOnly` không đồng nghĩa `ThreadSafe`.

---

# 573.153. No false purity

`NoWriteMemory` không đồng nghĩa `Pure` nếu function có IO/time/randomness.

---

# 573.154. Effect dependency graph

Compiler lưu:

```text
Function A
   ↓ calls
Function B
   ↓ calls
Function C
```

và effect dependencies tương ứng.

---

# 573.155. SCC algorithm

Recursive call SCC effect được tính tới fixed point.

---

# 573.156. Monotonic inference

Inference phải monotonic:

```text
Unknown → less conservative → precise
```

không được oscillate.

---

# 573.157. Deterministic inference

Traversal order không được thay đổi canonical summary.

---

# 573.158. Parallel inference

Independent SCCs có thể analyze song song.

---

# 573.159. Deterministic parallelism

Parallel và serial inference phải cho cùng summary.

---

# 573.160. Incremental invalidation

Chỉ affected SCC/callers được recompute.

---

# 573.161. Versioning

Effect schema có version.

---

# 573.162. Backward compatibility

Older `.axsem` effect summaries phải được migrate hoặc reject rõ ràng.

---

# 573.163. Cross-target cache

Target-specific effect summaries không được nhầm với target-independent summaries.

---

# 573.164. Profile

Effect inference profile:

```text
fast
standard
precise
whole-program
security
```

---

# 573.165. Fast mode

Chỉ local/direct + shallow summaries.

---

# 573.166. Standard mode

Transitive interprocedural summaries.

---

# 573.167. Precise mode

Region/context-sensitive analysis.

---

# 573.168. Whole-program mode

Closed-world call graph và LTO information.

---

# 573.169. Security mode

Capability/taint/secret effects.

---

# 573.170. Analysis timeout

Timeout → conservative summary.

---

# 573.171. Cancellation

Cancelled analysis không publish result như complete.

---

# 573.172. Partial summary

Partial summary phải có `Incomplete` marker.

---

# 573.173. Cache identity

Effect cache key phải bao gồm analyzer/schema version.

---

# 573.174. Cache integrity

Corrupted/stale summary phải reject.

---

# 573.175. Remote execution

Effect inference có thể chạy remote theo `568`.

---

# 573.176. Hermeticity

Remote result chỉ cache nếu inputs đầy đủ và deterministic.

---

# 573.177. Remote verification

Security-critical effect summaries có thể require local verification.

---

# 573.178. Diagnostics

Effect mismatch đi qua diagnostic engine `569`.

---

# 573.179. Diagnostic provenance

Diagnostic phải chỉ rõ:

```text
declared effect
inferred effect
causing operation
callee chain
```

---

# 573.180. Explanation path

Ví dụ:

```text
foo()
 ↓
bar()
 ↓
open_file()
 ↓
FileIO
```

---

# 573.181. API impact

Thay đổi public function effect có thể được semantic diff engine `486`/`570` báo cáo.

---

# 573.182. Dependency impact

Adding `IO` effect có thể ảnh hưởng callers có effect restrictions.

---

# 573.183. Generic API impact

Effect constraints của generic API là một phần semantic API contract.

---

# 573.184. Testing

Mỗi primitive MIR operation phải có expected effect test.

---

# 573.185. Inference tests

Test direct, transitive, recursive và dynamic dispatch effects.

---

# 573.186. Optimization tests

Verify optimizer không eliminate/reorder operations với effects không phù hợp.

---

# 573.187. Differential tests

So sánh optimized và unoptimized observable behavior.

---

# 573.188. Fuzzing

Fuzz call graphs, recursive SCCs, FFI, inline asm và cleanup paths.

---

# 573.189. Effect lattice fuzzing

Verify lattice join/meet/idempotence properties.

---

# 573.190. Soundness tests

Known side effect phải không thể bị classify thành `Pure`.

---

# 573.191. Unknown tests

Missing metadata phải produce conservative `Unknown`.

---

# 573.192. Determinism tests

Cùng MIR snapshot phải produce byte-identical canonical effect summary.

---

# 573.193. Performance

Local effect inference phải O(number of relevant MIR operations + dependency edges) ở mức cơ bản.

---

# 573.194. Incremental performance

Small source change không được trigger whole-program analysis khi dependency graph chứng minh không cần.

---

# 573.195. Memory budget

Effect summaries phải compact và có thể intern/shared.

---

# 573.196. No runtime dependency

Effect metadata không yêu cầu runtime support trong native release builds.

---

# 573.197. No annotation burden

Programmer không bị buộc khai báo effects cho mọi function.

---

# 573.198. Single authority

Mọi compiler subsystem dùng cùng canonical `EffectSummary`.

---

# 573.199. Semantic boundary

Effect analysis không được trở thành một semantic type system thứ hai cạnh type checker.

---

# 573.200. FINAL HARD INVARIANT

> **Axiom Effect System phải là một hệ thống suy luận effect canonical, deterministic và conservative. Function effects được suy ra từ MIR và transitive call summaries; `Unknown` không bao giờ được coi là `Pure` hay `Safe`; declared effects không được tự tạo proof nếu chưa được xác minh theo policy. Effect metadata phải có thể được compiler, optimizer, static analyzer, concurrency engine, FFI, async runtime, IDE và AI dùng chung. Effect analysis không tạo runtime overhead bắt buộc và không làm Axiom thành một ngôn ngữ phải viết effect annotation ở mọi nơi.**

**BOOTSTRAP-573: LOCKED.**

---

# NEXT — BOOTSTRAP-574

## COMPILER SYMBOLIC EXECUTION 2.0 — ABSTRACT INTERPRETATION, PATH CONSTRAINTS, SMT-LIKE REASONING, CONSTANT/RANGE PROOF, SAFETY PROOFS & BUG FINDING

`574` sẽ xây tầng **Symbolic Execution / Abstract Interpretation nâng cao** phía trên:

```text
571 Dataflow
        +
572 Static Analysis
        +
573 Effect System
        ↓
574 Symbolic Analysis
```

Kiến trúc dự kiến:

```text
                    MIR + CFG
                       │
                       ▼
              Abstract State Engine
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Values       Memory       Effects
          │            │            │
          └────────────┼────────────┘
                       ▼
                Path Constraints
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Constant       Range       Predicate
        Proof         Proof        Proof
          │            │            │
          └────────────┼────────────┘
                       ▼
                Safety Properties
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
          Bounds      Null     Arithmetic
          Proof       Proof      Proof
```

Trọng tâm sẽ là **proof engine có giới hạn tài nguyên**, không biến Axiom compiler thành một theorem prover nặng. Nó phải tận dụng tối đa facts từ `571–573`, chỉ đi sâu symbolic execution khi việc đó thực sự giúp chứng minh một property hoặc tìm bug.

**BOOTSTRAP-574: NEXT.**