# BOOTSTRAP-141 — Interprocedural Analysis, Call Graph & Whole-Program Optimization

**Trạng thái: FROZEN / COMPLETED**

Đây là bước nâng optimizer từ **tối ưu từng function** lên **hiểu quan hệ giữa toàn bộ chương trình**.

Nguyên tắc trung tâm:

> **Compiler được phép nhìn xuyên abstraction boundary khi boundary không observable; compiler phải tôn trọng boundary khi nó là một phần của semantics/ABI.**

---

# 1. Vị trí trong pipeline

```text id="f7q2m1"
Verified MIR
      ↓
Local Analyses
      ↓
SSA + MemorySSA
      ↓
OptIR
      ↓
Call Graph
      ↓
Interprocedural Analysis
      ↓
Whole-Program Optimization
      ↓
Optimized OptIR
      ↓
ABI MIR
```

---

# 2. Call Graph

Axiom xây dựng:

```text id="q3n8v5"
CallGraph {
    Functions
    Calls
    DirectEdges
    IndirectEdges
    DynamicDispatchEdges
    FunctionPointerEdges
    ClosureEdges
    AsyncEdges
    GPUEdges
    FFIEdges
}
```

---

# 3. Direct call

```ax id="m4p8r2"
foo(x);
```

Nếu resolver biết chính xác:

```text id="k7q3n1"
foo → FunctionId #42
```

đây là direct edge.

---

# 4. Function pointer

```ax id="v6r2m9"
let f = choose_function();
f(x);
```

Call target có thể là:

```text id="n3q8p4"
{foo, bar}
```

CallGraph phải lưu **tập target có thể xảy ra**, không đoán một target duy nhất.

---

# 5. Closure

Closure:

```ax id="p5m7q2"
let f = |x| x + 1;
```

CallGraph liên kết closure:

```text id="r8n3k6"
caller
  ↓
closure body
```

Nếu closure không escape, nó có thể được inline/eliminate.

---

# 6. Dynamic dispatch

```ax id="x4q9m1"
dyn Trait
```

CallGraph ban đầu có:

```text id="c7m2v8"
call → {impl_A, impl_B, impl_C}
```

Nếu compiler chứng minh concrete type:

```text id="j5r8n3"
call → impl_B
```

có thể devirtualize.

---

# 7. FFI

```ax id="q2m6v9"
extern "C" fn external();
```

CallGraph đánh dấu:

```text id="v8p3r1"
ExternalUnknown
```

trừ khi FFI contract cung cấp effect/alias/ABI information.

---

# 8. Export boundary

```ax id="k4n7m2"
@export("foo")
fn foo(...)
```

được coi là externally reachable.

Do đó không thể dead-strip chỉ vì không thấy internal caller.

---

# 9. Public không đồng nghĩa reachable

```ax id="m8q3v5"
pub fn foo()
```

không nhất thiết có nghĩa native symbol phải tồn tại.

Chỉ:

```text id="r2n7k4"
@export
```

hoặc target/link configuration thích hợp mới tạo binary-level reachability.

---

# 10. CallGraph SCC

Recursion:

```text id="p6q2m8"
A → B
B → C
C → A
```

tạo một SCC:

```text id="x3m9r1"
SCC #7 = {A,B,C}
```

Interprocedural fixed-point analysis chạy theo SCC.

---

# 11. Recursive effects

Ví dụ:

```text id="n5v8q2"
A → B → C → A
```

Effect summary ban đầu:

```text id="k7m3p9"
Unknown
```

sau fixed-point:

```text id="q4r8n2"
Read(R1)
Write(R2)
Panic
```

được propagate tới cả SCC nếu cần.

---

# 12. Interprocedural Effect Summary

Function:

```text id="m3q7v1"
foo(x)
```

có thể có:

```text id="r8n4p2"
EffectSummary {
    Reads
    Writes
    Allocates
    Drops
    Atomics
    Volatile
    IO
    Synchronize
    Panic
    Foreign
    GPU
    Suspend
    ExternalState
}
```

---

# 13. Region-sensitive effects

Không chỉ:

```text id="x5p2m8"
WritesMemory
```

mà:

```text id="v7q3n1"
Writes(arg0.region)
Reads(arg1.region)
```

Điều này rất quan trọng cho alias optimization.

---

# 14. Effect propagation

```text id="k9m4r2"
foo → bar
```

Nếu `bar`:

```text id="p2q8n5"
Write(R2)
```

thì `foo` phải ít nhất có:

```text id="n6r3v7"
Write(R2)
```

hoặc conservative equivalent.

---

# 15. Pure function

Nếu compiler chứng minh:

```text id="x4m8q2"
foo = Pure
```

thì nhiều optimization trở nên khả thi:

```text id="c7p3n9"
CSE
DCE
constant folding
memoization-like reuse
loop hoisting
```

nhưng chỉ khi arguments và observable semantics phù hợp.

---

# 16. Pure không có nghĩa “không có code”

Ví dụ:

```text id="m8r2q5"
foo(x) = expensive calculation
```

vẫn có thể Pure.

Pure nghĩa:

> không có observable external effect ngoài giá trị/termination semantics được mô hình hóa.

---

# 17. Panic vẫn quan trọng

Một function:

```text id="q3n7m1"
foo(x)
```

có thể không ghi memory nhưng có:

```text id="r6p2v8"
Panic
```

Không được coi hoàn toàn side-effect-free nếu panic observable.

---

# 18. Result không phải Panic

```ax id="k8m4q2"
fn parse(x: Str) -> Result<Value, Error>
```

`Err` là giá trị trả về.

Không tự động thêm:

```text id="v3n7p5"
Panic
```

vào effect summary.

---

# 19. Interprocedural Escape Analysis

Ví dụ:

```ax id="p5q8m2"
fn create() -> Box<Data> {
    ...
}
```

Compiler cần biết:

```text id="x7r3n9"
allocation escapes via return
```

nhưng điều đó **không tự động có nghĩa heap allocation bắt buộc**.

ABI có thể dùng caller allocation/sret hoặc optimization khác.

---

# 20. Caller allocation xuyên function

```text id="m4n8q1"
create()
```

có thể được lower thành:

```text id="q6r2p7"
caller-provided storage
```

nếu semantics cho phép.

Ownership vẫn:

```text id="v3m9k5"
caller owns result
```

---

# 21. Return View

```ax id="x8q4m2"
fn first(x: view<Array<T>>) -> view<T>
```

Interprocedural verifier phải giữ provenance:

```text id="p5r7n1"
returned view
    ↓
derived from x
```

Không được coi là independent allocation.

---

# 22. NoEscape xuyên function

```ax id="m7q3v9"
fn sum(x: view<i32>) -> i32
```

Nếu compiler chứng minh `x` chỉ được đọc trong function:

```text id="k2r8p4"
NoEscape
```

có thể:

- inline;
- scalarize;
- vectorize;
- register-promote.

---

# 23. Escape summaries

Mỗi function có summary:

```text id="n4q7m2"
EscapeSummary {
    argument_escape
    return_escape
    heap_escape
    thread_escape
    external_escape
    unknown_escape
}
```

---

# 24. Send xuyên call graph

Nếu:

```text id="r8m3q5"
spawn(foo(x))
```

thì compiler truy tìm ownership của `x` xuyên call chain.

Nếu execution domain yêu cầu Send:

```text id="q2n7v4"
T: Send
```

phải được chứng minh.

---

# 25. Share xuyên call graph

Tương tự:

```text id="m5q8r2"
Arc<T>
```

không biến `T` thành mutable-safe tự động.

CallGraph/EffectInfo phải giữ thông tin synchronization.

---

# 26. Interprocedural Alias Summary

Một function có thể được mô tả:

```text id="x3v7n1"
foo(
    read arg0,
    write arg1
)
```

và:

```text id="p6m2q8"
arg0 NO_ALIAS arg1
```

nếu contract/proof cho phép.

---

# 27. Nhưng không tạo `restrict` giả

Compiler chỉ ghi:

```text id="k4r8m3"
NO_ALIAS
```

nếu đã có proof.

Không cho programmer khai báo tùy tiện:

```text id="q7n2v5"
@noalias
```

rồi compiler tin mù quáng trong safe code.

---

# 28. Generic function summaries

```ax id="m3q8r1"
fn process<T: Trait>(x: T)
```

có summary theo generic constraints.

Khi specialization:

```text id="v7n4p2"
process<MyType>
```

compiler refine summary.

---

# 29. Generic summary cache

```text id="x8m2q5"
GenericInstanceId
+
Type arguments
+
Trait obligations
+
Target
```

→ summary cache.

Điều này giảm compile time đáng kể.

---

# 30. Devirtualization

Có ba cấp:

```text id="r5q7n3"
1. Exact target
2. Small finite target set
3. Unknown target
```

Cấp 1:

```text id="m2v8p4"
direct call
```

Cấp 2 có thể dùng:

```text id="k6r3q9"
guarded dispatch
```

Cấp 3:

```text id="p8n4m1"
retain indirect call
```

---

# 31. Type-based devirtualization

Nếu:

```ax id="q3m7v2"
let x: ConcreteType = ...;
x.method();
```

compiler biết exact impl.

Không cần vtable.

---

# 32. Dyn Trait

Nếu:

```ax id="r8q2n5"
let x: dyn Trait = ...
```

thì dynamic representation vẫn được giữ.

Nhưng nếu whole-program analysis chứng minh:

```text id="m5v7k1"
only ImplA can reach this site
```

→ devirtualization.

---

# 33. Whole-program reachability

Root set:

```text id="x7n3q8"
Entry
Exports
FFI-visible symbols
Init/Fini
Interrupt handlers
Reflection-preserved symbols
Explicit Keep
```

Tất cả khác có thể được loại nếu không reachable.

---

# 34. Dead Function Elimination

Ví dụ:

```text id="p2m8r4"
foo()
bar()
unused()
```

nếu `unused()` không reachable:

```text id="q6v3n9"
unused() → removed
```

---

# 35. Dead Generic Instance Elimination

Nếu:

```text id="k4r7m2"
generic<T>
```

được instantiate:

```text id="n8q3p5"
T=A
T=B
```

thì specialization cho C không cần tồn tại.

---

# 36. Cross-module inlining

```text id="m7r2q8"
module A
   ↓
module B
```

nếu `.axmeta` + implementation artifacts cho phép LTO:

```text id="x5n8p3"
inline B.foo into A.bar
```

---

# 37. ABI boundary

Không được inline xuyên ABI boundary nếu điều đó làm thay đổi observable ABI contract.

Ví dụ:

```text id="q2m6r8"
extern "C"
```

có thể được optimize bên trong nhưng phải giữ externally visible ABI.

---

# 38. Exported function

```ax id="v3q7m1"
@export("foo")
fn foo(...)
```

Có thể được optimize body rất mạnh.

Nhưng:

```text id="r8n4p2"
symbol
calling convention
parameter ABI
return ABI
```

phải giữ.

---

# 39. Whole-program vs library compilation

Axiom không giả định luôn có toàn bộ source.

Có ba chế độ:

```text id="m5q2v8"
Local
Module/LTO
Whole Program
```

Compiler phải vẫn hoạt động khi external dependency chỉ có `.axmeta`.

---

# 40. `.axmeta`

Metadata nên chứa đủ summary:

```text id="x7r3n1"
Function
Type
Trait
ABI
Effect
Escape
Generic
Export
Target
FFI
```

nhưng không chứa toàn bộ implementation.

---

# 41. Incremental invalidation

Nếu `foo` body thay đổi:

```text id="p8m4q2"
foo effect summary
foo escape summary
foo alias summary
```

có thể thay đổi.

Compiler chỉ invalidate callers phụ thuộc vào summary đó.

---

# 42. Interface fingerprint

Mỗi function có:

```text id="k3q7v5"
InterfaceFingerprint
SemanticSummaryFingerprint
```

Thay đổi implementation nhưng giữ summary có thể tránh rebuild downstream.

---

# 43. Summary widening

Trong recursive/complex programs, nếu analysis không hội tụ đủ chính xác:

```text id="n5r2m8"
Precise
 ↓
LessPrecise
 ↓
Conservative
```

Ví dụ:

```text id="q7v3p1"
NoEscape
→ UnknownEscape
```

Nhưng không được:

```text id="m8r4k2"
UnknownEscape → NoEscape
```

không có proof mới.

---

# 44. Summary lattice

Các analysis nên có lattice riêng thay vì ép chung một lattice.

Ví dụ:

```text id="x2q8m5"
Effect lattice
Alias lattice
Escape lattice
Purity lattice
```

---

# 45. SCC fixed-point

```text id="p4n7r2"
repeat
    analyze SCC
    propagate summaries
until stable
```

Phải có termination guarantee.

---

# 46. Recursive inlining

Không inline vô hạn:

```text id="m8q3v6"
A → B → A
```

CostModel + recursion depth giới hạn.

---

# 47. Recursive optimization vẫn có thể mạnh

Compiler có thể:

- inline one side;
- specialize;
- tail-call optimize;
- constant-fold recursive base cases;
- eliminate unreachable branches.

---

# 48. Tail Call

Nếu ABI và Drop semantics cho phép:

```text id="q7r3m1"
return foo(x)
```

có thể thành:

```text id="x5m8n2"
tailcall foo(x)
```

Chỉ khi caller không còn cleanup obligations cần thực hiện.

---

# 49. Interprocedural constant propagation

```ax id="v2q6m9"
const CONFIG = 42;

fn foo() {
    return CONFIG;
}
```

có thể propagate `42` xuyên module nếu visibility/semantic contract cho phép.

---

# 50. Function cloning

Nếu call sites có đặc điểm khác nhau:

```text id="m4r8p2"
foo(x)
foo(constant)
```

compiler có thể clone:

```text id="q7n3v5"
foo.const42
foo.generic
```

---

# 51. Partial specialization

Ví dụ:

```ax id="x8m2q4"
foo<T>(x, mode)
```

với:

```text id="p5r7n1"
mode = FAST
```

có thể tạo specialized clone.

---

# 52. Context-sensitive analysis

Compiler có thể phân tích:

```text id="k3q8m6"
foo @ callsite #1
foo @ callsite #2
```

khác nhau.

Nhưng không để compile time bùng nổ.

Cost budget kiểm soát.

---

# 53. Function summaries không được thay semantics

Nếu summary nói:

```text id="r4n7p2"
Read(R1)
```

nhưng implementation thực tế sửa R1, compiler bug.

Summary phải được **derived**, không phải trusted annotation.

---

# 54. FFI contract

FFI có thể cung cấp:

```text id="m6q2v8"
reads(arg0)
writes(arg1)
noescape(arg0)
nothrow
```

nhưng các contract này phải thuộc unsafe/system boundary và được xác định rõ.

Safe code không được giả mạo.

---

# 55. Foreign unknown

Nếu không có contract:

```text id="x8r3m1"
extern_call()
```

compiler conservative:

```text id="q5m7n2"
may read/write reachable memory
may access external state
may panic/terminate depending ABI
```

---

# 56. Whole-program allocation elimination

Ví dụ:

```ax id="p3q8m6"
fn foo() {
    let x = Box::new(Data);
    bar(x);
}
```

Nếu interprocedural analysis chứng minh `bar`:

```text id="m7r2n4"
does not retain
does not expose address
does not expose identity
```

thì allocation có thể stack-promote/eliminate.

---

# 57. Cross-function scalarization

```text id="x4q9m2"
make_point()
    ↓
Point
    ↓
caller uses only x
```

compiler có thể biến thành:

```text id="n8m3p7"
return x scalar
```

mà không materialize struct.

---

# 58. But ABI matters

Nếu `make_point` là externally exported:

```text id="r6q2v8"
@export
```

thì externally visible ABI không thể bị thay đổi.

Nếu internal-only:

```text id="p4m7n1"
```

scalarization xuyên function có thể tự do hơn.

---

# 59. Async call graph

```ax id="k8q3m2"
spawn(worker());
```

CallGraph đánh dấu execution boundary:

```text id="m5r7p9"
caller
  ↓
spawn
  ↓
worker task
```

Escape/Send analysis phải đi xuyên boundary.

---

# 60. GPU call graph

Kernel:

```ax id="x2n8q4"
@kernel fn compute(...)
```

không được coi là ordinary CPU function.

CallGraph domain:

```text id="q7m3r5"
CPU → GPU Launch → Kernel
```

---

# 61. GPU host/device boundary

Compiler phải phân biệt:

```text id="p4r8m2"
host call
device kernel
transfer
event synchronization
```

Không được inline tùy tiện qua host/device boundary.

---

# 62. Concurrency boundary

```text id="m8q2v6"
thread::spawn(foo)
```

là execution-domain boundary.

Interprocedural analysis phải bảo toàn:

```text id="x5r7n3"
Send
Share
synchronization
```

---

# 63. Memory ordering xuyên function

Function:

```text id="q3m8p1"
publish()
```

nếu chứa Release store.

Caller:

```text id="v7r2m5"
consume()
```

có Acquire.

Optimizer không được reorder qua boundary làm mất happens-before.

---

# 64. Whole-program optimization ≠ whole-program assumption

Axiom có thể optimize toàn chương trình khi biết toàn bộ graph.

Nhưng:

```text id="n4q8m2"
external ABI
dynamic loading
plugins
reflection
FFI
```

có thể tạo unknown edges.

Unknown phải được bảo toàn.

---

# 65. Dynamic libraries

Nếu function exported từ shared library:

```text id="r6m3p8"
external caller may exist
```

→ root.

Nếu internal hidden:

```text id="x2q7n4"
```

→ dead-strip/inlining có thể mạnh hơn.

---

# 66. Reflection

Nếu runtime reflection được bật:

```text id="m8r4q1"
reflection-preserved symbol
```

phải trở thành reachability root hoặc metadata root.

Nếu compile-time reflection only:

```text id="q5n7m2"
```

thì sau generation có thể erase.

---

# 67. Whole-program analysis cache

Có thể cache:

```text id="v3m8q2"
CallGraphFingerprint
+
FunctionSemanticFingerprints
+
DependencyFingerprints
+
Target
+
OptimizationConfig
```

→ interprocedural summaries.

---

# 68. AI inspection

Đề xuất:

```text id="r7q2m5"
axc inspect callgraph foo
axc inspect effects foo --interprocedural
axc inspect escape foo --interprocedural
axc inspect aliases foo
axc inspect devirtualization foo
axc inspect reachable
```

AI có thể hỏi:

```text id="m4n8p1"
Why wasn't bar inlined?
```

Compiler trả:

```text id="x7q3m6"
Legal: yes
Profitable: no
Reason:
  estimated code growth = 87%
  caller is cold
```

---

# 69. Nguyên tắc quan trọng nhất

Interprocedural optimization có thể **rất mạnh**, nhưng chỉ vì compiler có thêm information.

Không cần bắt programmer thêm annotation.

Ví dụ programmer viết:

```ax id="k5r8m2"
fn sum(a: view<i32>, b: view<i32>) -> i32 {
    ...
}
```

Compiler có thể tự suy luận:

```text id="p3q7n1"
effects = Read
escape = NoEscape
panic = false
alias = ...
```

rồi tối ưu.

---

# 70. Các invariants đã khóa

### `AIP-20`
CallGraph represents semantic call relationships.

### `AIP-21`
Direct calls resolve to stable FunctionIds.

### `AIP-22`
Indirect calls retain all semantically possible targets.

### `AIP-23`
Dynamic dispatch remains explicit in call analysis.

### `AIP-24`
FFI calls are conservative without verified contracts.

### `AIP-25`
Exported symbols are reachability roots.

### `AIP-26`
`pub` alone does not imply native symbol reachability.

### `AIP-27`
Recursive SCCs use deterministic fixed-point analysis.

### `AIP-28`
Interprocedural effects are compiler-derived.

### `AIP-29`
Effect summaries may be region-sensitive.

### `AIP-30`
Effect summaries cannot weaken Verified MIR semantics.

### `AIP-31`
Interprocedural escape analysis is conservative.

### `AIP-32`
Unknown escape is never converted to NoEscape without proof.

### `AIP-33`
Returned capabilities preserve provenance across calls.

### `AIP-34`
Send requirements propagate across execution boundaries.

### `AIP-35`
Share requirements remain distinct from Send.

### `AIP-36`
Interprocedural alias facts require proof.

### `AIP-37`
Compiler-derived NoAlias cannot be fabricated by optimization.

### `AIP-38`
Unknown foreign calls remain conservative.

### `AIP-39`
Generic summaries are parameterized by semantic instantiation.

### `AIP-40`
Specialization preserves generic semantics.

### `AIP-41`
Devirtualization requires a proven target.

### `AIP-42`
Dynamic dispatch may remain dynamic when target cannot be proven.

### `AIP-43`
Dead-function elimination operates only from verified reachability.

### `AIP-44`
Dead generic instances may be removed when unreachable.

### `AIP-45`
Cross-module optimization respects ABI boundaries.

### `AIP-46`
Exported ABI remains stable under internal optimization.

### `AIP-47`
Internal functions may be scalarized across call boundaries.

### `AIP-48`
Caller allocation may replace returned dynamic storage when semantics permit.

### `AIP-49`
Observable allocation identity prevents elimination.

### `AIP-50`
Stable addresses prevent invalid promotion or relocation.

### `AIP-51`
Tail calls require ABI compatibility and completed cleanup.

### `AIP-52`
Async execution boundaries remain semantically visible.

### `AIP-53`
GPU execution boundaries remain semantically visible.

### `AIP-54`
Concurrency synchronization semantics remain preserved.

### `AIP-55`
Atomic ordering cannot be weakened by interprocedural optimization.

### `AIP-56`
Reflection-preserved symbols remain reachable.

### `AIP-57`
Dynamic loading prevents unsafe closed-world assumptions.

### `AIP-58`
Whole-program optimization may exploit closed-world knowledge only when closed-world assumptions are valid.

### `AIP-59`
Analysis summaries are incrementally invalidated.

### `AIP-60`
Interprocedural analyses are deterministic.

### `AIP-61`
Independent SCCs may be analyzed in parallel.

### `AIP-62`
Analysis fixed points have termination guarantees.

### `AIP-63`
Less precise analysis results remain conservative.

### `AIP-64`
Optimization cannot convert conservative facts into stronger facts without proof.

### `AIP-65`
Whole-program optimization preserves observable semantics.

### `AIP-66`
LTO may improve optimization but cannot change semantics.

### `AIP-67`
`.axmeta` provides sufficient information for downstream interprocedural reasoning within its declared contract.

### `AIP-68`
Optimization summaries are cacheable using semantic fingerprints.

### `AIP-69`
AI/compiler inspection can expose interprocedural reasoning.

### `AIP-70`
Verified MIR remains the ultimate semantic correctness boundary.

---

# Kiến trúc optimizer hiện tại

Axiom lúc này đã có một chuỗi khá hoàn chỉnh:

```text id="w8q3m2"
                  VERIFIED MIR
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Alias         Effect       Escape
          └────────────┼────────────┘
                       ▼
                SSA + MemorySSA
                       │
                     OptIR
                       │
                ┌──────┴──────┐
                │ PassManager │
                └──────┬──────┘
                       │
                 Local Optimize
                       │
                 Call Graph
                       │
             Interprocedural Analysis
                       │
              Whole Program Optimize
                       │
                 Optimized OptIR
```

Đây là nền tảng đủ mạnh để sau này Axiom có optimizer cạnh tranh với các compiler systems hiện đại mà **không bắt programmer phải viết hàng loạt annotation tối ưu hóa**.

---

# BOOTSTRAP-142 — Inlining, Specialization & Devirtualization Engine

Bước tiếp theo nên đi sâu vào **3 cơ chế tạo ra phần lớn “zero-cost abstraction” của Axiom**:

```text id="g5m8q2"
Generic
   ↓
Specialization
   ↓
Inlining
   ↓
Constant Propagation
   ↓
Devirtualization
   ↓
Dead Code Elimination
   ↓
Machine-level optimized code
```

Task này sẽ khóa cụ thể:

- heuristic inlining;
- always-inline/never-inline boundary;
- generic monomorphization;
- specialization;
- code sharing;
- trait devirtualization;
- closure elimination;
- function cloning;
- constant propagation xuyên abstraction;
- recursion;
- hot/cold decisions;
- code-size control;
- ABI boundaries;
- dynamic dispatch;
- PGO;
- tránh code bloat.

Đây sẽ là bước rất quan trọng để biến mục tiêu **“abstraction không phải trả giá runtime”** của Axiom thành một cơ chế compiler cụ thể.