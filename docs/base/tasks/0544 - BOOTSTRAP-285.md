# BOOTSTRAP-285
# AXIOM INTERPROCEDURAL SEMANTIC ANALYSIS ENGINE
## FROZEN / COMPLETED

### 285.1. Mục tiêu

Sau khi đã có:

```text
281 Ownership / Initialization
282 Capability / View / Alias
283 Effect
284 Escape / Storage Lifetime
```

Axiom cần một tầng kết hợp chúng **giữa các function**.

Mục tiêu của 285 là biến các phân tích vốn hoạt động tốt ở cấp function thành một hệ thống có thể trả lời:

> **“Nếu function A gọi B, và B gọi C, compiler có thể suy ra chính xác những semantic facts nào của A mà không phân tích lại toàn bộ call tree mỗi lần?”**

Đây là nền móng cho:

- optimization liên hàm;
- inlining;
- devirtualization;
- allocation elimination;
- noalias;
- effect propagation;
- escape propagation;
- Drop propagation;
- Send/Share propagation;
- async analysis;
- GPU analysis;
- FFI;
- incremental compilation;
- LTO.

---

# 285.2. Nguyên tắc trung tâm

Axiom không được xây một loạt hệ thống riêng:

```text
OwnershipCallGraph
EffectCallGraph
EscapeCallGraph
CapabilityCallGraph
```

Thay vào đó:

```text
                 CompilerDB
                     │
                Call Graph
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
     Ownership    Capability   Effect
          ↓          ↓          ↓
       Escape ───────┴────── Analysis
                     │
                     ↓
             Semantic Summary
```

> **Một call graph, nhiều semantic analyses.**

---

# 285.3. Semantic Summary

Mỗi callable có một summary chuẩn:

```text
SemanticSummary {
    ownership: OwnershipSummary
    capability: CapabilitySummary
    effects: EffectSummary
    escape: EscapeSummary
    concurrency: ConcurrencySummary
    async: AsyncSummary
    gpu: GpuSummary
    ffi: FfiSummary
    panic: PanicSummary
}
```

Không phải function nào cũng cần mọi field.

Compiler chỉ materialize phần cần thiết.

---

# 285.4. Tách Summary khỏi MIR

MIR:

```text
function body
```

Summary:

```text
behavior observable to callers
```

Ví dụ:

```text
fn identity<T>(x: T) -> T
```

không cần caller biết từng MIR instruction.

Caller chỉ cần:

```text
Param0 → Return
```

---

# 285.5. Summary không phải ABI

Một summary:

```text
Param0 → Return
```

không nói:

```text
register RDI
stack offset 16
hidden sret pointer
```

Đó là việc của ABI.

Do đó:

```text
SemanticSummary
    ≠
ABI Signature
```

---

# 285.6. Summary không phải optimization result

Ví dụ compiler phát hiện:

```text
foo()
```

có thể inline.

Đó là optimization decision.

Summary vẫn mô tả:

```text
foo's semantic behavior
```

trước optimization.

---

# 285.7. CallGraph

CallGraph node:

```text
CallableId
```

Edge:

```text
CallEdge {
    caller
    callsite
    callee
    dispatch_kind
    target_set
}
```

Dispatch:

```text
Direct
Generic
FunctionPointer
Closure
TraitStatic
TraitDynamic
Foreign
Intrinsic
Unknown
```

---

# 285.8. Direct call

```text
foo() → bar()
```

CallGraph:

```text
foo ──direct──> bar
```

Summary propagation đơn giản.

---

# 285.9. Generic call

```text
foo<T>(x)
```

Compiler phải resolve:

```text
GenericInstanceId
```

trước khi sử dụng instantiated semantic facts.

Ví dụ:

```text
foo<i32>
foo<File>
```

có thể có Drop/Send/Effect khác nhau.

---

# 285.10. Dynamic dispatch

```text
dyn Trait
```

CallGraph không nhất thiết có một target.

Có thể:

```text
callsite
   ├── impl A
   ├── impl B
   └── impl C
```

Summary của dynamic call:

```text
union(all reachable target summaries)
```

nếu tập target biết được.

---

# 285.11. Unknown call

Nếu target không xác định:

```text
Unknown
```

Compiler dùng conservative summary.

Ví dụ:

```text
Foreign
UnknownEscape
UnknownAlias
UnknownEffect
```

Nhưng chỉ tại boundary cần thiết.

---

# 285.12. Call-site summary

Không chỉ lưu summary của callee.

Mỗi callsite có:

```text
CallSiteSummary {
    argument_mapping
    consumed_arguments
    returned_values
    capability_mapping
    region_mapping
    effects
    escape_relations
    panic_behavior
}
```

Điều này rất quan trọng cho generic và alias analysis.

---

# 285.13. Argument mapping

Ví dụ:

```text
foo(a, b)
```

callee:

```text
fn foo(x, y)
```

mapping:

```text
x → caller a
y → caller b
```

Region:

```text
callee Param0
      ↓
caller Region(a)
```

---

# 285.14. Ownership propagation

Nếu callee:

```text
consume(param0)
```

caller phải cập nhật:

```text
ownership(a) = Moved
```

Nhưng đây không phải compiler tự suy luận lại body.

Summary của callee cung cấp fact:

```text
Param0 consumed
```

---

# 285.15. Capability propagation

Nếu callee:

```text
Write(param0)
```

caller map:

```text
Write(caller_region(a))
```

Capability verifier vẫn kiểm tra caller capability.

---

# 285.16. Effect propagation

Ví dụ:

```text
foo()
```

gọi:

```text
bar()
```

và:

```text
bar → {Read, IO}
```

thì:

```text
foo → {Read, IO}
```

Nếu `bar` thay đổi effect:

```text
{Read}
→
{Read, IO}
```

các caller phụ thuộc sẽ được invalidate.

---

# 285.17. Escape propagation

Nếu:

```text
bar(param0) → Return
```

và:

```text
foo(x) {
    return bar(x)
}
```

compiler suy ra:

```text
x → Return
```

mà không cần phân tích toàn bộ implementation của `bar` mỗi lần.

---

# 285.18. Capability return

Nếu:

```text
bar(param0) → view(param0)
```

thì summary:

```text
ReturnCapability {
    source = Param0
    region = ...
}
```

Caller nhận provenance:

```text
caller_x → returned_view
```

Capability verifier tiếp tục kiểm tra lifetime.

---

# 285.19. Multiple return sources

Ví dụ:

```text
fn choose(a, b, condition) -> view<T>
```

có thể:

```text
return a
```

hoặc:

```text
return b
```

Summary:

```text
ReturnCapabilitySources = {
    Param0,
    Param1
}
```

Caller phải giữ cả hai provenance possibilities.

---

# 285.20. Conditional effects

Ví dụ:

```text
fn f(x) {
    if x {
        io()
    }
}
```

Summary:

```text
may_effect(IO)
```

không nhất thiết:

```text
always_effect(IO)
```

Do đó effect model cần distinguish:

```text
MayEffect
```

và path-sensitive facts khi cần.

---

# 285.21. Must / May summary

Axiom sử dụng hai loại semantic fact:

```text
Must
May
```

Ví dụ:

```text
MustConsume(param0)
MayPanic
MayIO
MustWrite(param1)
```

Điều này tránh việc conservative analysis làm mất precision.

---

# 285.22. Ownership Must/May

Ví dụ:

```text
fn f(x) {
    if condition {
        consume(x)
    }
}
```

Summary:

```text
MayConsume(param0)
```

không phải:

```text
MustConsume(param0)
```

Caller phải xử lý theo control-flow semantics.

---

# 285.23. Effect Must/May

Tương tự:

```text
MayPanic
```

không phải:

```text
MustPanic
```

Điều này quan trọng cho optimizer.

---

# 285.24. Escape Must/May

Ví dụ:

```text
if condition {
    global = x
}
```

summary:

```text
MayEscapeTo(Global)
```

Compiler không được biến thành:

```text
AlwaysGlobalEscape
```

nếu condition không luôn true.

---

# 285.25. Summary normalization

Summary phải canonical.

Ví dụ:

```text
Param0 → Return
Return ← Param0
```

phải được canonical thành cùng một semantic relation.

Điều này giúp:

- cache;
- fingerprint;
- incremental build;
- deterministic compiler output.

---

# 285.26. Call graph SCC

Call graph có thể:

```text
A → B
B → C
C → A
```

Compiler dùng:

```text
Strongly Connected Components
```

để phân tích recursion.

Pipeline:

```text
CallGraph
    ↓
SCC decomposition
    ↓
Condensation DAG
    ↓
Bottom-up processing
    ↓
Summary fixpoint
```

---

# 285.27. Summary fixpoint

Trong một SCC:

```text
A ↔ B
```

ban đầu:

```text
A = Bottom
B = Bottom
```

Mỗi vòng:

```text
A = transfer(B)
B = transfer(A)
```

cho đến:

```text
A[n] = A[n+1]
B[n] = B[n+1]
```

---

# 285.28. Monotonicity

Semantic summaries phải monotonic theo lattice.

Không được:

```text
iteration 1 = Write
iteration 2 = {}
```

trừ khi analysis có một refinement phase riêng được định nghĩa rõ.

Default fixpoint:

```text
summary[n] ⊆ summary[n+1]
```

cho may-facts.

---

# 285.29. Precision refinement

Sau conservative fixpoint, compiler có thể chạy refinement:

```text
initial conservative summary
        ↓
constant/path facts
        ↓
range facts
        ↓
alias facts
        ↓
dead-path elimination
        ↓
refined summary
```

Nhưng refinement phải bảo đảm soundness.

---

# 285.30. Interprocedural alias

Nếu:

```text
foo(a, b)
```

callee biết:

```text
Param0 DISJOINT Param1
```

caller có thể map:

```text
Region(a) DISJOINT Region(b)
```

nếu mapping/proof hợp lệ.

Đây là cách Axiom truyền internal `NO_ALIAS` ra caller mà không cần `restrict`.

---

# 285.31. NoAlias propagation

Chỉ propagate:

```text
NO_ALIAS
```

khi:

```text
callee proof
+
caller mapping
+
provenance compatibility
```

Nếu một trong ba không đủ:

```text
UNKNOWN
```

---

# 285.32. Effect + Alias

Ví dụ callee:

```text
Write(param0)
```

caller có:

```text
a
b
```

Nếu:

```text
a DISJOINT b
```

thì compiler biết:

```text
Write(a)
```

không invalidate:

```text
Read(b)
```

Đây là nền tảng cho optimization liên hàm.

---

# 285.33. Escape + Capability

Nếu callee:

```text
return view(param0)
```

caller nhận:

```text
CapabilityEscape
```

nhưng provenance vẫn:

```text
caller param0
```

Do đó view không được biến thành:

```text
unowned arbitrary pointer
```

---

# 285.34. Escape + Ownership

Nếu:

```text
consume(param0)
```

và:

```text
return param0
```

cùng path:

```text
```

thì summary phải phản ánh path semantics chính xác.

Không được tạo summary:

```text
Param0 consumed
Param0 returned
```

mà không có condition/path relation.

---

# 285.35. Drop propagation

Nếu callee nhận:

```text
T
```

và có:

```text
Drop(T)
```

summary phải chứa Drop obligations liên quan.

Caller không cần biết implementation destructor, nhưng phải biết semantic consequence.

---

# 285.36. Panic propagation

Ví dụ:

```text
A → B → C
```

nếu:

```text
C may_panic
```

thì:

```text
B may_panic
A may_panic
```

trừ khi caller chứng minh call unreachable.

---

# 285.37. Panic handling

Nếu caller:

```text
if false {
    B()
}
```

thì effect/panic summary không được propagate từ unreachable call.

Do đó call graph summary có thể cần:

```text
ReachabilityFacts
```

từ MIR.

---

# 285.38. Concurrency summary

Function có thể tạo:

```text
Spawn
Synchronize
Block
```

và truyền ownership sang thread.

Summary:

```text
ConcurrencySummary {
    may_spawn
    may_block
    synchronization
    transferred_arguments
}
```

---

# 285.39. Send propagation

Nếu:

```text
spawn(move || f(x))
```

thì interprocedural analysis cần biết:

```text
f
```

giữ `x` hay chỉ dùng local.

Kết hợp:

```text
EscapeSummary
+
OwnershipSummary
+
Send
```

để giảm conservative rejection.

---

# 285.40. Async summary

Async function có:

```text
AsyncSummary {
    may_suspend
    live_across_await
    returned_future
    captured_values
}
```

Caller biết:

```text
await foo()
```

có thể suspend.

Nhưng effect summary vẫn tách biệt:

```text
Await
```

---

# 285.41. GPU summary

GPU callable:

```text
GpuSummary {
    execution_domain
    storage_reads
    storage_writes
    atomics
    synchronization
    transfers
}
```

Host call:

```text
launch(kernel)
```

có thể lấy summary của kernel để kiểm tra transfer/synchronization.

---

# 285.42. FFI summary

FFI contract:

```text
FfiSummary {
    reads
    writes
    consumes
    returns
    escapes
    may_panic
    may_block
    effects
}
```

Không contract:

```text
Unknown/Foreign
```

---

# 285.43. Summary composition

Caller summary:

```text
CallerSummary =
    LocalEffects
    ∪
    MappedCalleeEffects
    ∪
    LocalEscape
    ∪
    MappedCalleeEscape
    ∪
    OwnershipEffects
    ∪
    ConcurrencyEffects
```

Tất cả phải map qua callsite.

---

# 285.44. Summary projection

Không phải caller nào cũng cần toàn bộ summary.

Ví dụ optimizer chỉ hỏi:

```text
may_write(foo)
```

Compiler không cần deserialize:

```text
GPU
FFI
Async
```

nếu không liên quan.

Query engine phải hỗ trợ projection:

```text
effect_summary(foo)
escape_summary(foo)
ownership_summary(foo)
```

---

# 285.45. Demand-driven analysis

Interprocedural analysis không nên luôn phân tích toàn bộ chương trình.

Ví dụ:

```text
compiler
```

chỉ cần:

```text
foo()
```

Compiler có thể truy xuất dependency closure cần thiết.

Điều này quan trọng cho IDE và incremental build.

---

# 285.46. Incremental invalidation

Nếu:

```text
C effect changes
```

thì:

```text
B
```

chỉ bị invalidate nếu summary của B phụ thuộc vào effect của C.

Sau đó:

```text
A
```

chỉ invalidate nếu B's summary thay đổi theo dependency relevant.

Không được rebuild toàn bộ call graph semantic state.

---

# 285.47. Semantic fingerprints

Mỗi summary có:

```text
SemanticSummaryFingerprint
```

Nếu function body thay đổi nhưng summary không đổi:

```text
caller semantic cache
```

có thể giữ nguyên.

Đây là một optimization cực kỳ quan trọng cho incremental compiler.

---

# 285.48. Ví dụ

Trước:

```text
fn add(x, y) {
    return x + y
}
```

summary:

```text
effects = {}
escape = NoEscape
panic = false
```

Sau khi implementation đổi:

```text
let z = x + y
return z
```

summary vẫn giống.

Caller không cần semantic reanalysis.

---

# 285.49. Summary fingerprint ≠ source hash

Hai implementation:

```text
A
B
```

có thể khác source hoàn toàn nhưng:

```text
SemanticSummaryFingerprint(A)
==
SemanticSummaryFingerprint(B)
```

Điều này cho phép cache theo semantic behavior.

---

# 285.50. Summary ABI independence

Cùng function:

```text
foo()
```

có summary giống nhau trên:

```text
x86-64
ARM64
RISC-V64
WASM
```

trừ khi semantics thật sự target-dependent.

ABI/register/layout không làm thay đổi summary.

---

# 285.51. Target-dependent semantics

Nếu một intrinsic thực sự phụ thuộc target:

```text
cpu_rdtsc()
```

thì summary phải mang:

```text
TargetCondition
```

thay vì giả vờ universal.

---

# 285.52. Summary caching

CompilerDB:

```text
SummaryDB
```

sử dụng QueryEngine:

```text
semantic_summary(FunctionId)
```

Dependencies tự động tracked.

Không tạo cache riêng trong từng optimizer.

---

# 285.53. Parallelism

Các SCC độc lập:

```text
SCC1
SCC2
SCC3
```

có thể phân tích song song.

Bên trong SCC:

```text
deterministic fixpoint
```

Kết quả phải độc lập số worker.

---

# 285.54. Summary serialization

Summary đủ ổn định có thể lưu trong:

```text
.axcache
.axmeta
```

Nhưng cache là untrusted.

Compiler phải:

```text
validate
version-check
fingerprint-check
target-check
dependency-check
```

trước khi sử dụng.

---

# 285.55. Cross-module analysis

Một module:

```text
math.ax
```

export:

```text
dot()
```

module khác:

```text
render.ax
```

có thể sử dụng:

```text
dot()
```

mà không cần body nếu `.axmeta` cung cấp semantic summary đủ cho contract.

---

# 285.56. Public semantic contract

Public API metadata có thể chứa:

```text
FunctionSignature
EffectSummary
EscapeSummary
OwnershipSummary
CapabilityContract
Send/Share
ABI
```

nhưng không nhất thiết chứa implementation MIR.

---

# 285.57. Private implementation

Compiler có thể giữ:

```text
private function body
```

chỉ trong package/compiler cache.

Public consumers chỉ cần semantic interface.

---

# 285.58. LTO

LTO có thể mở body và tính lại/refine summary.

Ví dụ:

```text
extern-like interface
```

có summary:

```text
Write(Unknown)
```

LTO thấy implementation thực tế:

```text
Write(param0.field2)
```

thì có thể refine.

Nhưng refinement phải không vi phạm ABI/semantic contract đã công bố.

---

# 285.59. Contract monotonicity

Nếu public contract đã nói:

```text
may IO
```

implementation mới có:

```text
no IO
```

có thể refine nội bộ.

Nhưng nếu public ABI/semantic contract yêu cầu:

```text
no IO
```

implementation mới thêm:

```text
IO
```

→ compile error.

---

# 285.60. AI interface

Compiler cung cấp:

```text
why_does_A_depend_on_B_effect()
why_does_A_escape()
why_is_param0_consumed()
why_is_alias_unknown()
why_is_call_not_pure()
```

Ví dụ:

```json id="d8q9t1"
{
  "caller": "foo",
  "callee": "bar",
  "dependency": "IO",
  "path": [
    "foo",
    "bar",
    "read_file"
  ]
}
```

AI có thể sửa source dựa trên facts thực tế thay vì đoán.

---

# 285.61. Diagnostic path

Compiler có thể hiển thị:

```text
foo()
 └─ bar(x)
     └─ baz(x)
         └─ external_call(x)

x:
    ThreadEscape

reason:
    baz passes x to external_call
```

Đây là một lợi thế lớn của Axiom so với diagnostics chỉ dựa trên type checker.

---

# 285.62. Security

Interprocedural analysis phải không được tin cache mù quáng.

Cache summary có thể bị:

- corrupt;
- stale;
- maliciously modified.

Do đó:

```text
.axcache
```

không phải trusted semantic authority.

Compiler phải xác minh fingerprint và dependency.

---

# 285.63. Unsafe boundaries

Một unsafe abstraction có thể cung cấp contract:

```text
unsafe fn make_view(...)
```

Interprocedural summary ghi:

```text
TrustedPrecondition
```

nhưng safe caller vẫn phải satisfy contract.

Không có:

```text
unsafe summary
→ disable verifier
```

---

# 285.64. Comptime

Comptime function có semantic summary riêng:

```text
CompileTimeSummary
```

Không được trộn:

```text
CompileTimeEffect
```

vào runtime `SemanticSummary`.

Generated declarations sau đó đi qua:

```text
normal resolution
type checking
ownership
capability
effect
escape
```

---

# 285.65. Data structure

Đề xuất:

```text id="y4hglk"
SemanticSummary {
    function: FunctionId

    ownership: OwnershipSummary
    capabilities: CapabilitySummary
    effects: EffectSummary
    escapes: EscapeSummary

    panic: PanicSummary
    concurrency: ConcurrencySummary
    async_info: AsyncSummary
    gpu: GpuSummary
    ffi: FfiSummary

    fingerprint: SemanticFingerprint
}
```

---

# 285.66. CallSite

```text id="8q8f8m"
CallSiteSemantic {
    callsite_id: InstructionId
    callee_set: TargetSet
    argument_map: ArgumentMap

    ownership_map
    capability_map
    region_map
    effect_map
    escape_map

    must_facts
    may_facts
}
```

---

# 285.67. Module architecture

```text id="08v14r"
compiler/
└── analysis/
    └── interprocedural/
        ├── mod.ax
        ├── call_graph.ax
        ├── call_edge.ax
        ├── target_set.ax
        ├── dispatch.ax
        ├── callsite.ax
        ├── argument_map.ax
        ├── semantic_summary.ax
        ├── summary_builder.ax
        ├── summary_normalize.ax
        ├── summary_fingerprint.ax
        ├── summary_projection.ax
        ├── ownership.ax
        ├── capability.ax
        ├── effect.ax
        ├── escape.ax
        ├── panic.ax
        ├── concurrency.ax
        ├── async.ax
        ├── gpu.ax
        ├── ffi.ax
        ├── scc.ax
        ├── fixpoint.ax
        ├── incremental.ax
        ├── parallel.ax
        ├── cross_module.ax
        ├── cache.ax
        ├── diagnostics.ax
        ├── query.ax
        └── tests/
```

---

# 285.68. Implementation order

```text
1. CallGraph
2. CallEdge
3. Dispatch classification
4. TargetSet
5. CallSite mapping
6. SemanticSummary
7. Summary normalization
8. Direct-call propagation
9. Generic instantiation mapping
10. Dynamic dispatch target sets
11. Ownership propagation
12. Capability propagation
13. Effect propagation
14. Escape propagation
15. Panic propagation
16. Concurrency propagation
17. Async propagation
18. GPU propagation
19. FFI propagation
20. SCC decomposition
21. Fixpoint engine
22. Summary fingerprint
23. CompilerDB integration
24. Incremental invalidation
25. Cross-module summaries
26. Persistent cache
27. Parallel deterministic execution
28. AI diagnostics
29. Adversarial tests
30. Fuzz/property tests
```

---

# 285.69. Adversarial tests

Bắt buộc:

```text
direct call
generic call
recursive call
mutual recursion
function pointer
closure
trait static dispatch
trait dynamic dispatch
unknown indirect call
FFI call
```

và:

```text
ownership transfer
view return
mut_view propagation
alias propagation
effect propagation
escape propagation
panic propagation
Drop propagation
Send propagation
async propagation
GPU propagation
```

Đặc biệt:

```text
A → B → C → D
```

với mỗi tầng thay đổi một semantic property.

---

# 285.70. Frozen invariants

```text
AIP-20
Interprocedural analysis operates on semantic MIR and verified semantic facts.

AIP-21
Axiom uses one authoritative call graph.

AIP-22
Ownership, Capability, Effect and Escape analyses share call graph infrastructure.

AIP-23
Interprocedural analysis does not redefine individual analysis semantics.

AIP-24
Semantic summaries represent caller-visible behavior.

AIP-25
Semantic summaries are distinct from ABI signatures.

AIP-26
Semantic summaries are distinct from optimization results.

AIP-27
Callsite argument mapping is explicit.

AIP-28
Region mapping is explicit.

AIP-29
Ownership facts propagate through verified call contracts.

AIP-30
Capability facts propagate through verified call contracts.

AIP-31
Effect facts propagate through verified call contracts.

AIP-32
Escape facts propagate through verified call contracts.

AIP-33
Panic behavior propagates through calls.

AIP-34
Concurrency behavior propagates through calls.

AIP-35
Async behavior propagates through calls.

AIP-36
GPU behavior propagates through calls.

AIP-37
FFI behavior propagates through explicit contracts.

AIP-38
Unknown calls remain conservative.

AIP-39
Dynamic dispatch uses the union of proven reachable targets.

AIP-40
Unknown dynamic targets are not assumed pure or nonescaping.

AIP-41
Generic calls use instantiated semantic mappings.

AIP-42
Must and May facts are represented distinctly.

AIP-43
Conditional ownership effects are not promoted to unconditional facts.

AIP-44
Conditional escape effects are not promoted to unconditional facts.

AIP-45
Conditional effects are not promoted to unconditional effects.

AIP-46
Call graph recursion is solved through SCC decomposition.

AIP-47
SCC fixpoints are deterministic.

AIP-48
Summary propagation is monotonic.

AIP-49
Summary normalization is canonical.

AIP-50
Summary fingerprints are deterministic.

AIP-51
Summary fingerprints are distinct from source hashes.

AIP-52
Summary fingerprints are distinct from machine-code fingerprints.

AIP-53
Unchanged semantic summaries permit incremental caller reuse.

AIP-54
Changed summaries invalidate only dependent queries.

AIP-55
Cross-module consumers may use verified semantic metadata without implementation MIR.

AIP-56
Persistent semantic cache is treated as untrusted data.

AIP-57
Cached summaries require dependency and fingerprint validation.

AIP-58
LTO may refine summaries when implementation is available.

AIP-59
LTO cannot violate published semantic contracts.

AIP-60
NoAlias facts propagate only when provenance and region mapping prove them valid.

AIP-61
Unknown alias is never refined to NoAlias without proof.

AIP-62
Returned capabilities preserve provenance across interprocedural boundaries.

AIP-63
Capability lifetime constraints propagate across calls.

AIP-64
Ownership transfer does not imply physical storage transfer.

AIP-65
ReturnEscape does not imply heap allocation.

AIP-66
AddressEscape preserves stable-storage requirements.

AIP-67
Drop semantics propagate through call summaries.

AIP-68
Observable Drop cannot be eliminated by summary optimization.

AIP-69
Panic effects remain observable unless proven unreachable.

AIP-70
Foreign calls remain conservative without contracts.

AIP-71
Unsafe contracts cannot bypass safe verification.

AIP-72
Comptime summaries are separate from runtime summaries.

AIP-73
Generated code re-enters normal semantic analysis.

AIP-74
Semantic summaries are independent of optimization level.

AIP-75
Semantic summaries are independent of target ABI where semantics are unchanged.

AIP-76
Interprocedural analysis is demand-driven where possible.

AIP-77
Interprocedural queries use CompilerDB query infrastructure.

AIP-78
Analysis subsystems do not maintain conflicting call graph caches.

AIP-79
Analysis results are deterministic across worker counts.

AIP-80
Parallel SCC processing preserves serial semantics.

AIP-81
AI tooling can query interprocedural dependency paths.

AIP-82
AI tooling cannot override semantic summaries.

AIP-83
Diagnostics preserve source provenance through call chains.

AIP-84
Summary construction is sound under conservative unknown boundaries.

AIP-85
Summary precision should be retained whenever proven.

AIP-86
The compiler must not collapse known caller/callee facts into Unknown unnecessarily.

AIP-87
Interprocedural optimization consumes summaries but cannot redefine semantic truth.

AIP-88
Escape optimization cannot invalidate capability provenance.

AIP-89
Capability optimization cannot invalidate ownership semantics.

AIP-90
Effect optimization cannot remove observable behavior.

AIP-91
Concurrency summaries cannot weaken Send/Share or synchronization guarantees.

AIP-92
Async summaries cannot permit invalid capabilities across suspension.

AIP-93
GPU summaries cannot bypass execution/storage-domain verification.

AIP-94
FFI summaries cannot create implicit ownership or lifetime guarantees.

AIP-95
Semantic summaries remain valid only while their dependency fingerprints remain valid.

AIP-96
Summary invalidation is dependency-driven.

AIP-97
Summary analysis participates in incremental compilation.

AIP-98
Summary analysis supports self-hosted compiler implementation.

AIP-99
Interprocedural semantic analysis is part of the compiler correctness boundary.

AIP-100
The Interprocedural Semantic Analysis Engine is frozen as Axiom's authoritative cross-function semantic propagation layer.
```

## Trạng thái chuỗi

```text
281  Ownership / Initialization / Move       FROZEN
282  Capability / View / Alias               FROZEN
283  Effect / Side Effects                   FROZEN
284  Escape / Storage Lifetime               FROZEN
285  Interprocedural Semantic Analysis       FROZEN
```

Task 285 hoàn tất. Theo cơ chế mới, **phản hồi kế tiếp sẽ chỉ đi vào đúng task kế tiếp**, không gộp nhiều task.