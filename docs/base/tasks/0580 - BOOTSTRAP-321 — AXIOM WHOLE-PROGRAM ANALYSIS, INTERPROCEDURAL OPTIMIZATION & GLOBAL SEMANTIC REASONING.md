# BOOTSTRAP-321 — AXIOM WHOLE-PROGRAM ANALYSIS, INTERPROCEDURAL OPTIMIZATION & GLOBAL SEMANTIC REASONING

Sau 320, Axiom đã có **Optimization Orchestrator** có thể lựa chọn pass theo từng function. Nhưng compiler vẫn còn một giới hạn lớn:

> Nhiều optimization quan trọng không thể quyết định chính xác nếu chỉ nhìn từng function độc lập.

Ví dụ:

```text
fn foo(x: ...) -> ...
fn bar() {
    foo(...)
}
```

Muốn biết `foo()` có thể inline, allocation có thể loại bỏ, argument có alias hay không, object có escape hay không, một function có thực sự cần dynamic dispatch hay không… compiler phải nhìn **qua ranh giới function/module/package**.

BOOTSTRAP-321 xây dựng tầng **Whole-Program / Interprocedural Semantic Reasoning**.

---

# 321.1. Mục tiêu

Mở rộng:

```text
Function Analysis
```

thành:

```text
Function
   ↓
Call Graph
   ↓
SCC / Recursion Graph
   ↓
Module Graph
   ↓
Package Graph
   ↓
Whole Program
```

Nhưng vẫn phải giữ:

- correctness
- incremental compilation
- separate compilation
- FFI safety
- dynamic boundary
- deterministic behavior
- compilation scalability

---

# 321.2. Không phải mọi chương trình đều cần Whole-Program Analysis

Đây là nguyên tắc quan trọng.

Axiom phải hỗ trợ:

```text
Fast Separate Compilation
```

và:

```text
Deep Whole-Program Optimization
```

Do đó có các mức:

```text
Local
Function
Module
Package
LTO
Whole Program
```

Compiler chỉ nâng mức khi có lợi ích.

---

# 321.3. Program Semantic Graph

Xây dựng:

```text
ProgramGraph
```

bao gồm:

```text
Declaration
Function
Type
Trait
GenericInstance
Global
Static
FFI Symbol
Exported Symbol
Dynamic Boundary
```

Các edge:

```text
Calls
References
Reads
Writes
Creates
Drops
Allocates
Escapes
Implements
Dispatches
Exports
Imports
Spawns
Awaits
LaunchesGPU
```

---

# 321.4. Call Graph

Call graph không chỉ đơn giản:

```text
foo → bar
```

mà phải hỗ trợ:

```text
DirectCall
GenericCall
TraitCall
DynDispatch
FunctionPointer
ClosureCall
FFI
ReflectionBoundary
RuntimeCall
```

Ví dụ:

```text
foo()
  ↓
bar()
```

là:

```text
DirectCall
```

nhưng:

```text
dyn Trait
```

là:

```text
DynamicCall
```

---

# 321.5. Call Graph Confidence

Một edge có trạng thái:

```text
Proven
Possible
Unknown
External
```

Ví dụ:

```text
foo → bar
```

direct call:

```text
Proven
```

Còn:

```text
dyn Trait.method()
```

có thể:

```text
Possible:
    ImplA.method
    ImplB.method
    ImplC.method
```

Không được biến:

```text
Possible
```

thành:

```text
Proven
```

chỉ vì optimizer muốn inline.

---

# 321.6. Strongly Connected Components

Recursive functions:

```text
foo → bar
bar → baz
baz → foo
```

tạo:

```text
SCC {
    foo
    bar
    baz
}
```

Interprocedural analysis chạy theo SCC.

Điều này giúp xử lý:

- recursion
- mutual recursion
- recursive generics
- recursive async structures

---

# 321.7. Interprocedural Fact

Một function có thể xuất ra summary:

```text
FunctionSummary {
    inputs
    outputs

    reads
    writes

    effects

    allocations
    deallocations

    escapes

    aliases

    ownership_transfer

    panic_behavior

    synchronization

    async_behavior

    gpu_behavior
}
```

Ví dụ:

```text
fn length(v: view<T>) -> usize
```

summary:

```text
reads:
    v

writes:
    none

allocates:
    none

panic:
    none

effects:
    pure
```

---

# 321.8. Function Summary là Semantic Contract

Summary không chỉ là optimization metadata.

Nó phải được xem như:

```text
VerifiedSemanticSummary
```

và được tạo bởi:

```text
Verifier
```

chứ không phải optimizer tự đoán.

---

# 321.9. Effect Summary

Ví dụ:

```text
fn save(x: Data) -> Result<()> 
```

summary:

```text
Effects:
    IO
    FileSystem
    Allocation
```

Compiler có thể dùng summary để tránh những optimization không hợp lệ.

Ví dụ:

```text
foo()
foo()
```

không thể CSE nếu `foo()` có observable IO.

---

# 321.10. Memory Summary

Function có thể khai báo/được chứng minh:

```text
Reads(region A)
Writes(region B)
```

Nếu:

```text
A DISJOINT B
```

compiler có thể tối ưu mạnh hơn.

Nhưng nếu:

```text
UNKNOWN
```

→ conservative.

---

# 321.11. Ownership Summary

Function có thể:

```text
Consume
BorrowRead
BorrowWrite
ReturnOwned
Share
Send
```

Ví dụ:

```text
fn consume(x: Buffer) -> usize
```

summary:

```text
input x:
    Move

output:
    value

x after call:
    Moved
```

---

# 321.12. Escape Summary

Function có thể trả:

```text
NoEscape
ArgumentEscape
ReturnEscape
HeapEscape
ThreadEscape
ExternalEscape
Unknown
```

Ví dụ:

```text
fn sum(x: view<i32>) -> i32
```

có thể chứng minh:

```text
NoEscape
```

Điều này cho phép caller tối ưu storage.

---

# 321.13. Allocation Elimination xuyên Function

Ví dụ:

```text
fn make() -> Box<Point> {
    Box::new(Point(...))
}

fn foo() {
    let p = make()
    use(p)
}
```

Nếu whole-program analysis chứng minh:

```text
address not exposed
no escape
identity unobservable
```

thì:

```text
Box allocation
```

có thể biến thành:

```text
stack/register/scalar
```

hoặc bị loại bỏ hoàn toàn.

Đây là một trong những lợi ích lớn nhất của interprocedural optimization.

---

# 321.14. Interprocedural Alias Analysis

Ví dụ:

```text
fn f(a: mut_view<i32>, b: mut_view<i32>) {
    ...
}

fn g(x, y) {
    f(x, y)
}
```

Nếu caller chứng minh:

```text
x DISJOINT y
```

thì thông tin đó có thể truyền vào `f`.

Ngược lại:

```text
UNKNOWN
```

không được giả định disjoint.

---

# 321.15. Context-Sensitive Analysis

Một function có thể được gọi nhiều nơi:

```text
foo(a)
foo(b)
foo(c)
```

Nếu summary chung quá conservative, compiler có thể tạo:

```text
ContextSummary
```

theo call site.

Ví dụ:

```text
foo<T>
```

với:

```text
T = i32
```

và:

```text
T = f64
```

có thể có semantic/codegen facts khác nhau.

---

# 321.16. Context Sensitivity Budget

Context-sensitive analysis có thể rất đắt.

Do đó:

```text
ContextBudget {
    max_contexts
    max_depth
    max_compile_time
}
```

Compiler chỉ mở rộng context khi ROI đủ lớn.

---

# 321.17. Function Cloning

Nếu một function có hai context rất khác nhau:

```text
foo(x)
```

compiler có thể tạo:

```text
foo.specialized.contextA
foo.specialized.contextB
```

nhưng phải tránh code explosion.

---

# 321.18. Interprocedural Constant Propagation

Ví dụ:

```text
fn f(x: i32) -> i32 {
    if x == 10 {
        return 20
    }
    return 30
}

fn main() {
    f(10)
}
```

Whole-program reasoning biết:

```text
x = 10
```

→ có thể loại:

```text
x != 10
```

và sau đó:

```text
f(10) → 20
```

---

# 321.19. Devirtualization

Axiom có:

```text
dyn Trait
```

nhưng dynamic dispatch chỉ cần khi runtime target thực sự không biết.

Nếu compiler chứng minh:

```text
dyn Trait object
```

chỉ có một concrete implementation reachable:

```text
ImplA
```

thì:

```text
dyn dispatch
```

→

```text
direct call
```

Sau đó có thể inline.

Nhưng nếu có:

```text
FFI
plugin
reflection
dynamic loading
```

thì boundary phải được bảo vệ.

---

# 321.20. Trait Reachability

Whole-program analysis xây:

```text
TraitImplementationGraph
```

để biết:

```text
Trait T
 ├── Impl A
 ├── Impl B
 └── Impl C
```

implementation nào thực sự reachable.

Điều này giúp:

- devirtualization
- vtable elimination
- dead impl elimination
- code-size reduction

---

# 321.21. Closure Analysis

Closure có thể được phân tích xuyên function:

```text
fn make() {
    let x = ...
    return || x
}
```

Compiler xác định:

```text
capture mode
capture size
escape
heap requirement
Send
Share
```

Nếu closure không escape:

```text
closure environment
```

có thể scalarize.

---

# 321.22. Async Interprocedural Analysis

Ví dụ:

```text
async fn foo() {
    await bar()
}
```

Compiler cần biết:

```text
bar()
```

có:

- suspension
- allocation
- blocking
- cancellation
- Send requirement

hay không.

Summary:

```text
AsyncSummary {
    may_suspend
    suspension_count
    state_size
    allocation
    blocking
    send
    share
}
```

---

# 321.23. Async State Optimization xuyên Function

Nếu:

```text
foo()
```

await:

```text
bar()
```

và `bar()` thực tế:

```text
immediately_ready
no_suspend
```

compiler có thể loại bỏ một phần state machine.

Đây là cơ sở cho:

```text
AwaitFusion
ReadyPathSpecialization
FutureInlining
```

mạnh hơn.

---

# 321.24. Concurrency Summary

Function summary phải ghi:

```text
spawns_thread
spawns_task
sends_channel
receives_channel
locks
atomics
synchronizes
migrates_task
```

Điều này ngăn optimizer vô tình reorder synchronization.

---

# 321.25. GPU Interprocedural Analysis

Kernel gọi helper:

```text
@kernel
fn compute() {
    helper()
}
```

Compiler cần biết helper có:

```text
GPU legal
allocation
host call
IO
blocking
unsupported pointer
```

hay không.

Nếu helper không GPU-safe:

```text
compile error
```

hoặc specialization thành GPU implementation.

---

# 321.26. FFI Summary

FFI function không được coi là:

```text
unknown black box
```

hoàn toàn nếu có contract.

Ví dụ:

```text
extern "C" fn memcpy(...)
```

có thể có contract:

```text
reads
writes
no allocation
no panic
no synchronization
```

Nhưng nếu không có contract:

```text
ExternalUnknown
```

→ conservative.

---

# 321.27. Global State Analysis

Compiler cần phân tích:

```text
static
TLS
global mutable
device global
external global
```

để biết function nào:

```text
reads global
writes global
```

Ví dụ:

```text
const GLOBAL: i32
```

có thể propagate.

Nhưng:

```text
static mut GLOBAL
```

phải được xử lý theo synchronization/unsafe semantics.

---

# 321.28. Whole-Program Reachability

Root set:

```text
Entry
Exports
FFI
Reflection
Dynamic Boundaries
Runtime Roots
GPU Entry
Test Roots
```

Sau đó:

```text
Reachability
```

được tính.

Unreachable:

```text
function
generic instance
trait impl
global
metadata
```

có thể loại bỏ nếu không có semantic side effect.

---

# 321.29. Constructor/Initializer Analysis

Static initialization có thể tạo observable behavior.

Không được coi:

```text
global init
```

là dead chỉ vì không có direct call.

Root analysis phải bao gồm:

```text
InitializationGraph
```

và thứ tự initialization.

---

# 321.30. Whole-Program Drop Analysis

Compiler có thể biết object lifetime xuyên function.

Ví dụ:

```text
create()
    ↓
pass()
    ↓
consume()
```

Nếu ownership chuyển thẳng:

```text
create → consume
```

thì intermediate storage có thể được tối ưu.

Nhưng Drop order phải giữ nguyên observable semantics.

---

# 321.31. Whole-Program Capability Analysis

Capability graph:

```text
Owner
 ↓
view
 ↓
call
 ↓
return
```

Compiler có thể xác định chính xác:

- capability escape
- alias
- lifetime
- mutation
- relocation constraints

Điều này giúp mạnh hơn rất nhiều so với local alias analysis.

---

# 321.32. Separate Compilation Summary

Để package A compile độc lập package B, compiler lưu:

```text
.axif
```

interface chứa:

```text
public types
traits
functions
ABI
effects
ownership
capabilities
generic constraints
FFI contracts
semantic summaries
optimization summaries
```

Như vậy package B không cần source của A.

---

# 321.33. Semantic Summary Stability

Summary phải có fingerprint:

```text
SummaryFingerprint
```

Nếu implementation thay đổi nhưng public semantic summary không đổi:

```text
consumer
```

không nhất thiết phải rebuild.

Nếu:

```text
ownership
ABI
effect
trait
repr
```

thay đổi:

```text
invalidate
```

---

# 321.34. Incremental Whole-Program Analysis

Compiler graph:

```text
Package A
   ↓
Package B
   ↓
Package C
```

Nếu A thay đổi internal implementation nhưng summary không đổi:

```text
B/C
```

không cần reanalyze.

Nếu summary đổi:

```text
A → B → C
```

invalidation truyền theo dependency graph.

---

# 321.35. Interprocedural Proof

Summary không phải heuristic.

Ví dụ:

```text
NoAllocation(foo)
```

phải có provenance:

```text
AllocationAnalysis
    ↓
all callees analyzed
    ↓
no allocation path
    ↓
certificate
```

Nếu có:

```text
Unknown FFI
```

thì không được kết luận:

```text
NoAllocation
```

---

# 321.36. Global Semantic Fixpoint

Một số facts cần fixed point:

```text
foo summary
depends on bar summary
bar summary
depends on foo summary
```

Compiler chạy:

```text
Initial summaries
       ↓
SCC iteration
       ↓
Refine
       ↓
Refine
       ↓
Fixed point
```

Nếu không đạt proof:

```text
Unknown
```

không phải đoán.

---

# 321.37. Summary Widening

Để tránh phân tích vô hạn:

```text
Precise
 ↓
Precise
 ↓
...
```

compiler có widening.

Ví dụ:

```text
Region A
Region B
Region C
...
```

có thể eventually:

```text
Unknown
```

hoặc:

```text
MayAlias
```

nhưng không được widening thành một fact mạnh hơn.

---

# 321.38. Interprocedural Optimization Pipeline

Sau 321, pipeline tổng quát:

```text
Local Analysis
      ↓
Function Summary
      ↓
Call Graph
      ↓
SCC Analysis
      ↓
Interprocedural Facts
      ↓
Whole-Program Planner
      ↓
Specialization / Devirtualization
      ↓
Inlining
      ↓
Global Optimization
      ↓
Local Re-optimization
```

---

# 321.39. CompilerDB Integration

Thêm:

```text
ProgramDB
CallGraphDB
SummaryDB
ReachabilityDB
WholeProgramDB
```

vào kiến trúc:

```text
CompilerDB
 ├── SourceDB
 ├── TypeDB
 ├── TraitDB
 ├── HIRDB
 ├── MIRDB
 ├── CorrectnessDB
 ├── PassDB
 ├── OptimizationDB
 ├── ProgramDB
 ├── CallGraphDB
 ├── SummaryDB
 └── ReachabilityDB
```

---

# 321.40. API

```text
build_call_graph()
```

```text
compute_reachability()
```

```text
compute_function_summary()
```

```text
compute_program_summary()
```

```text
query_effect_summary()
```

```text
query_memory_summary()
```

```text
query_escape_summary()
```

```text
query_ownership_summary()
```

```text
query_async_summary()
```

```text
query_gpu_summary()
```

```text
query_trait_reachability()
```

```text
specialize_function()
```

```text
devirtualize_call()
```

```text
analyze_scc()
```

```text
invalidate_program_summary()
```

```text
explain_global_optimization()
```

---

# 321.41. Implementation Tree

```text
compiler/interprocedural/
├── graph/
│   ├── call_graph.ax
│   ├── reference_graph.ax
│   ├── initialization_graph.ax
│   └── dependency_graph.ax
│
├── scc/
│   ├── scc.ax
│   ├── solver.ax
│   └── widening.ax
│
├── summary/
│   ├── function_summary.ax
│   ├── memory_summary.ax
│   ├── effect_summary.ax
│   ├── ownership_summary.ax
│   ├── escape_summary.ax
│   ├── async_summary.ax
│   ├── concurrency_summary.ax
│   └── gpu_summary.ax
│
├── reachability/
│   ├── roots.ax
│   ├── reachable.ax
│   └── dead_code.ax
│
├── specialization/
│   ├── context.ax
│   ├── cloning.ax
│   ├── devirtualization.ax
│   └── generic_specialization.ax
│
├── global/
│   ├── global_state.ax
│   ├── global_drop.ax
│   └── global_effects.ax
│
└── database/
    ├── program_db.ax
    ├── summary_db.ax
    ├── call_graph_db.ax
    └── reachability_db.ax
```

---

# 321.42. Invariants

```text
AIP-20  Interprocedural facts are derived from verified semantic information.

AIP-21  Unknown call targets are never treated as known direct calls.

AIP-22  Unknown external behavior is never treated as pure or side-effect free.

AIP-23  Function summaries are semantic artifacts, not merely optimization hints.

AIP-24  Summary facts have provenance and fingerprints.

AIP-25  Recursive SCC analysis terminates.

AIP-26  Widening may lose precision but may never invent stronger facts.

AIP-27  Whole-program optimization cannot violate separate-compilation contracts.

AIP-28  Dynamic boundaries remain reachable unless explicitly proven otherwise.

AIP-29  FFI boundaries remain conservative without explicit contracts.

AIP-30  Reflection/dynamic loading roots participate in reachability.

AIP-31  Global initialization participates in reachability and effect analysis.

AIP-32  Drop semantics remain observable where specified.

AIP-33  Ownership and capability summaries preserve their original provenance.

AIP-34  Context-sensitive analysis is bounded by explicit resource budgets.

AIP-35  Function cloning must obey code-size and compile-time budgets.

AIP-36  Devirtualization requires proof of target uniqueness or an equivalent valid guard.

AIP-37  Interprocedural optimization preserves async semantics.

AIP-38  Interprocedural optimization preserves synchronization semantics.

AIP-39  GPU call graphs obey GPU legality rules.

AIP-40  Whole-program optimization remains semantically equivalent to the reference model.

AIP-41  Incremental invalidation must not reuse stale summaries.

AIP-42  Whole-program analysis is optional; correctness does not depend on its presence.

AIP-43  Optimization must degrade to conservative behavior when global proof is unavailable.
```

---

# 321.43. Definition of Done

BOOTSTRAP-321 hoàn thành khi:

1. Có Program Semantic Graph.
2. Có Call Graph.
3. Có SCC analysis.
4. Có Function Summary.
5. Có verified Effect Summary.
6. Có Memory Summary.
7. Có Ownership Summary.
8. Có Escape Summary.
9. Có Async Summary.
10. Có Concurrency Summary.
11. Có GPU Summary.
12. Có FFI Summary.
13. Có global-state analysis.
14. Có initialization graph.
15. Có whole-program reachability.
16. Có generic specialization planning.
17. Có function cloning.
18. Có devirtualization.
19. Có context-sensitive analysis.
20. Có bounded widening.
21. Có incremental summary fingerprints.
22. Có separate-compilation `.axif` semantic summaries.
23. Có LTO integration.
24. Có whole-program dead-code elimination.
25. Có cross-function allocation elimination.
26. Có cross-function capability/alias reasoning.
27. Có differential validation với ARI.
28. Có AI explanation cho global optimization.
29. Có benchmark chứng minh whole-program optimization không làm compile time tăng vô hạn.
30. Có end-to-end:

```text
Source
   ↓
Local Semantics
   ↓
Function Summaries
   ↓
Call Graph
   ↓
SCC Fixpoint
   ↓
Global Facts
   ↓
Optimization Planner
   ↓
Specialization
   ↓
Inlining / Devirtualization
   ↓
Local Re-optimization
   ↓
Translation Validation
   ↓
Codegen
```

---

## Nguyên tắc đóng băng của 321

> **Axiom phải có khả năng nhìn toàn chương trình khi điều đó tạo ra lợi ích, nhưng không được biến whole-program analysis thành điều kiện bắt buộc để compiler hoạt động.**

Điều này giữ được cả hai mục tiêu:

```text
Separate compilation
        +
Deep optimization
```

và đặc biệt phù hợp với mục tiêu của Axiom là **hiệu năng cao nhưng compiler phải tự động làm phần phức tạp thay cho programmer**.