# BOOTSTRAP-142 — Inlining, Specialization & Devirtualization Engine

**Trạng thái: FROZEN / COMPLETED**

Đây là một trong những task quan trọng nhất đối với mục tiêu của Axiom:

> **Abstraction ở source-level phải có khả năng biến mất hoàn toàn ở machine-level khi không còn giá trị runtime.**

Axiom không nên bắt programmer lựa chọn giữa **code đẹp** và **performance**.

---

# 1. Vị trí trong compiler

```text id="b7m3q1"
Verified MIR
    ↓
OptIR
    ↓
CallGraph
    ↓
Interprocedural Analysis
    ↓
Inlining / Specialization / Devirtualization
    ↓
Constant Propagation
    ↓
SROA / GVN / DCE
    ↓
Optimized OptIR
```

Ba cơ chế trung tâm:

```text id="p4n8r2"
Generic specialization
        ↓
Devirtualization
        ↓
Inlining
        ↓
Constant propagation
        ↓
Dead code elimination
```

Thứ tự không bắt buộc tuyệt đối; Pass Manager có thể lập pipeline thích hợp.

---

# 2. Nguyên tắc thiết kế

Axiom phân biệt:

```text id="m8q3v5"
Legality
Profitability
Code-size impact
```

Ví dụ:

```text
Inlining:
    Legal = yes
    Profitable = no
```

→ Không inline.

---

# 3. Không có “zero-cost abstraction” bằng lời hứa

Axiom phải biến nó thành property có thể kiểm tra:

```text id="q6r2n8"
Abstraction
    ↓
semantic lowering
    ↓
specialization
    ↓
optimization
    ↓
machine representation
```

Nếu abstraction không còn observable behavior:

```text
→ có thể biến mất.
```

---

# 4. Generic mặc định static

Ví dụ:

```ax
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

Khi gọi:

```ax
max<i32>(a, b)
```

compiler có thể tạo:

```text id="v3m7q1"
max_i32
```

không cần runtime generic dispatch.

---

# 5. Monomorphization

Generic instance được canonicalize:

```text id="k8q4m2"
GenericInstanceId {
    FunctionId
    TypeArguments
    ConstArguments
    TraitEnvironment
    TargetFeatures
}
```

Hai instance semantic giống nhau có thể dùng chung implementation.

---

# 6. Không monomorphize mù quáng

Nếu:

```text id="r5n2p8"
foo<T>
```

được dùng với 1000 types, compiler không nhất thiết tạo 1000 bản machine code.

Có thể:

```text id="m7q3v1"
specialize hot cases
+
share cold/common implementation
```

---

# 7. Hybrid generic code generation

Axiom sử dụng mô hình:

```text id="x4p8n2"
Full specialization
        +
Representation sharing
        +
Late specialization
```

Mục tiêu:

- performance;
- binary size;
- compile time.

---

# 8. Specialization levels

### Level 0 — Generic

```text
T: Trait
```

### Level 1 — Representation specialization

Biết:

```text
size_of(T)
align_of(T)
calling convention
```

### Level 2 — Type specialization

Biết:

```text
T = i32
```

### Level 3 — Value specialization

Biết:

```text
mode = Fast
N = 16
```

### Level 4 — Profile specialization

Biết callsite hot/cold.

---

# 9. Constant specialization

Ví dụ:

```ax
fn process<const N: usize>(x: Array<f32, N>) { ... }
```

với:

```text id="j8m3q6"
N = 4
```

compiler có thể unroll/vectorize mạnh hơn.

---

# 10. Nhưng không để specialization bùng nổ

Compiler theo dõi:

```text id="q5r8m1"
SpecializationBudget
```

gồm:

```text
code size
compile time
number of instances
hotness
optimization gain
```

---

# 11. Function cloning

Ví dụ:

```ax
foo(x)
```

hai callsite:

```text
foo(constant)
foo(dynamic)
```

compiler có thể tạo:

```text id="v3q7m2"
foo.const
foo.generic
```

---

# 12. Clone chỉ khi có lợi ích

Nếu clone tạo:

```text
+2 KB code
```

nhưng chỉ tiết kiệm một instruction:

```text
→ thường không clone.
```

CostModel quyết định.

---

# 13. Inlining

Inlining biến:

```ax
foo(x)
```

thành body của `foo`.

Mục đích không chỉ giảm call overhead.

Lợi ích lớn hơn thường là:

```text id="m8r2q5"
Inlining
   ↓
Constant Propagation
   ↓
SCCP
   ↓
DCE
   ↓
SROA
   ↓
Vectorization
```

---

# 14. Inlining phải nhìn xuyên abstraction

Ví dụ:

```ax
fn square(x: f32) -> f32 {
    x * x
}
```

```ax
let y = square(a);
```

có thể trở thành:

```text
y = a * a
```

không có function call.

---

# 15. Method syntax không tạo runtime overhead

```ax
v.length()
```

semantic lowering:

```text
length(v)
```

sau đó inline như function bình thường.

Không có hidden class dispatch.

---

# 16. Trait static dispatch

```ax
fn draw<T: Drawable>(x: T)
```

mặc định:

```text id="p7n3r8"
static dispatch
```

Specialization biết concrete `T`.

Không cần vtable.

---

# 17. Dynamic dispatch

```ax
fn draw(x: dyn Drawable)
```

mới cần dynamic dispatch.

Representation có thể là:

```text
data pointer
+
vtable
```

hoặc target-specific equivalent.

---

# 18. Devirtualization

Nếu compiler chứng minh:

```text id="k4q8m2"
dyn Drawable
→ only Circle reachable
```

thì:

```text
virtual call
```

có thể thành:

```text
direct Circle::draw
```

---

# 19. Devirtualization levels

```text id="x7m2p5"
Exact target
Finite target set
Unknown target
```

Exact:

```text
direct call
```

Finite:

```text
guarded dispatch / jump table
```

Unknown:

```text
dynamic dispatch
```

---

# 20. Whole-program knowledge

Khi compile executable với closed-world information:

```text id="q8r3m1"
CallGraph complete
```

devirtualization có thể mạnh.

Khi compile shared library:

```text id="v5n7p2"
External callers unknown
```

phải conservative.

---

# 21. ABI boundary

Không được inline làm thay đổi:

```text id="m3q8r5"
extern "C"
@export
stable ABI
FFI-visible function
```

Body vẫn được optimize nội bộ.

ABI contract vẫn giữ.

---

# 22. Inline qua module

Nếu `.axmeta` và compiled artifact cung cấp đủ information:

```text id="r7n2m4"
Module A
    ↓
Module B
```

LTO có thể inline.

---

# 23. Visibility ảnh hưởng optimization

```text id="p8q3m6"
private
pub
@export
extern
```

có mức closed-world khác nhau.

`private` thường dễ tối ưu nhất.

`@export` phải coi external caller có thể tồn tại.

---

# 24. Always-inline

Axiom có thể có compiler/system attribute:

```text
@inline(always)
```

nhưng:

> **Always-inline không được override legality.**

Nếu recursive hoặc ABI impossible:

```text
→ không thể inline.
```

Compiler phải báo/ghi diagnostic phù hợp tùy contract.

---

# 25. Never-inline

```text
@inline(never)
```

có thể dùng cho:

- profiling;
- debugging;
- code-size;
- ABI/system boundary;
- hot patching.

Nhưng attribute phải được định nghĩa rõ là optimization constraint, không phải semantic behavior.

---

# 26. Inline cost

CostModel tính:

```text id="n5q8r2"
EstimatedInstructionGrowth
RegisterPressure
StackGrowth
CodeSize
CallFrequency
LoopDepth
Hotness
TargetCost
```

---

# 27. Hot call

```text id="m7r3q1"
hot caller
+
small callee
```

→ ưu tiên inline.

---

# 28. Cold call

```text id="x8q2m5"
cold caller
+
large callee
```

→ thường giữ call để giảm code size.

---

# 29. Loop-aware inlining

Function được gọi trong loop:

```ax
for x in data {
    process(x);
}
```

Inlining có thể mở ra vectorization.

CostModel phải tăng lợi ích nếu:

```text id="p4m8n2"
callee enables loop optimization
```

---

# 30. Recursive function

Không inline vô hạn.

Ví dụ:

```ax
fn fib(n) {
    ...
}
```

compiler có depth/budget.

Có thể inline vài tầng nếu profitable.

---

# 31. Mutual recursion

```text id="q7m3r8"
A → B → A
```

SCC-aware inliner tránh infinite expansion.

---

# 32. Closure

Closure:

```ax
let f = |x| x + 1;
```

nếu local/nonescaping:

```text id="v5n8q2"
closure allocation
→ eliminated
```

và:

```text
call closure
→ direct call
→ inline
```

---

# 33. Captured values

Nếu closure capture:

```ax
let a = 10;
let f = |x| x + a;
```

compiler có thể:

```text id="m3q7p1"
capture environment
→ scalarize
→ constant propagate
```

nếu `a` không thay đổi.

---

# 34. Closure identity

Nếu chương trình quan sát identity của closure:

```text id="x8r2m6"
```

compiler không được tùy tiện merge hai closure chỉ vì body giống nhau.

---

# 35. Function pointer conversion

Noncapturing closure:

```ax
let f = |x| x + 1;
```

có thể decay thành function pointer.

Nếu function pointer address/identity observable:

```text id="p7m4n2"
```

compiler phải giữ callable representation phù hợp.

---

# 36. Constant propagation

Sau inline:

```text id="k8q3m5"
foo(42)
```

có thể expose:

```text id="r2n7v1"
x = 42
```

→ constant propagation.

---

# 37. SCCP

Sparse Conditional Constant Propagation có thể phát hiện:

```ax
if false {
    expensive();
}
```

→ branch unreachable.

---

# 38. Nhưng panic vẫn observable

Nếu branch unreachable **theo proof**:

```text id="m4q8p2"
```

có thể loại.

Nếu chỉ profile nói:

```text id="x7n3r5"
branch = 0.001%
```

không được coi là unreachable.

---

# 39. Trait default method

```ax
trait Foo {
    fn run(self) { ... }
}
```

Nếu concrete implementation không override:

```text id="q3m8v1"
```

compiler có thể specialize/inlining default method.

---

# 40. Trait override

Nếu:

```ax
impl Foo for X {
    fn run(self) { ... }
}
```

call tới `X` dùng implementation đó.

Không cần `override` keyword.

---

# 41. Associated type specialization

Ví dụ:

```ax
trait Iterator {
    type Item;
}
```

Khi:

```text id="n5r2m7"
T = VecIterator<i32>
```

compiler normalize:

```text
Item = i32
```

rồi optimize như concrete type.

---

# 42. Generic associated constants

```ax
trait Buffer {
    const SIZE: usize;
}
```

nếu concrete implementation:

```text id="p8q4m2"
SIZE = 64
```

constant propagation có thể xuyên abstraction.

---

# 43. Operator traits

```ax
a + b
```

semantic resolution có thể thành trait function.

Sau specialization/inlining:

```text id="x7m3n8"
trait dispatch
→ concrete function
→ arithmetic instruction
```

---

# 44. Không có runtime trait machinery mặc định

Ví dụ:

```ax
a + b
```

không mặc định tạo:

```text
object
vtable
heap
dynamic dispatch
```

---

# 45. Generic bounds không tạo runtime checks

```ax
fn sort<T: Ord>(...)
```

`T: Ord` là compile-time obligation.

Không tạo:

```text id="q4n8m2"
runtime instanceof
runtime trait lookup
```

trừ `dyn Trait`.

---

# 46. Specialization và safety

Specialization không được bypass:

```text id="m7q3r5"
ownership
capability
Drop
Send
Share
GPU legality
FFI
```

Các specialization phải được kiểm chứng như code bình thường.

---

# 47. Specialized code không phải trusted code

Pipeline:

```text id="v2m8p4"
Generic semantics
      ↓
Specialization
      ↓
new MIR/OptIR
      ↓
verification
```

Generated semantic transformations phải re-enter appropriate verification boundary.

---

# 48. Code bloat control

Compiler theo dõi:

```text id="r5q3n8"
GenericInstanceCount
CloneCount
InlineGrowth
TextSizeEstimate
```

---

# 49. Code-size budget

Ví dụ policy nội bộ:

```text id="p8m2q6"
hot function:
    larger budget

cold function:
    small budget
```

Không hard-code một con số cho mọi target.

---

# 50. Template-like explosion tránh bằng sharing

Nếu:

```text id="x4n7m2"
Foo<A>
Foo<B>
Foo<C>
```

cùng representation và generated code:

```text id="q8m3r5"
```

có thể share machine implementation.

---

# 51. Representation sharing

Ví dụ các type:

```text id="m7q2p8"
Wrapper<i32>
Wrapper<u32>
```

có thể có machine-level implementation tương đương cho một số operations.

Compiler có thể dùng shared code nếu ABI/semantics cho phép.

---

# 52. Không merge khi semantics khác

Ví dụ:

```text id="r3n8m5"
Drop behavior
alignment
overflow semantics
trait dispatch
```

khác nhau.

Không được merge chỉ vì machine instructions hiện tại giống nhau.

---

# 53. Generic ABI specialization

Generic internal function:

```text id="v6q2m8"
fn foo<T>(x: T)
```

có thể được ABI-lowered khác nhau theo `T`.

Ví dụ:

```text
T = i32 → register
T = LargeStruct → sret/indirect
```

---

# 54. Inlining sau ABI hay trước ABI?

**Inlining chủ yếu xảy ra trên OptIR trước ABI lowering.**

Điều này cho compiler thấy:

```text id="p5r8m2"
semantic types
SSA
effects
alias
escape
generic structure
```

sau đó mới:

```text
ABI lowering
```

Một số late inline có thể tồn tại sau ABI nhưng không phải đường chính.

---

# 55. Devirtualization trước ABI

Tốt nhất:

```text id="m3q7n8"
dyn call
→ proven target
→ direct call
→ inline
→ optimize
→ ABI
```

giảm overhead tối đa.

---

# 56. Late devirtualization

Một số trường hợp chỉ biết target sau:

```text id="q8n4p1"
LTO
PGO
link-time visibility
```

có thể devirtualize ở late stage.

---

# 57. PGO

PGO có thể thay đổi:

```text id="x5m7r2"
inline profitability
clone profitability
devirtualization strategy
code layout
```

nhưng không thay đổi legality.

---

# 58. Guarded specialization

Nếu runtime condition có thể kiểm tra rẻ:

```text id="p3q8m6"
if condition:
    fast specialized version
else:
    generic version
```

được phép.

Điều kiện phải được kiểm chứng.

---

# 59. Ví dụ

Nếu:

```text id="n7m2r5"
length % 4 == 0
```

có thể dispatch:

```text
vectorized path
scalar remainder path
```

Runtime guard chỉ chọn implementation.

---

# 60. Function cloning + PGO

Một function có:

```text id="q4r8m1"
90% callsite A
10% callsite B
```

compiler có thể clone optimized version cho A.

---

# 61. Recursion + specialization

Ví dụ generic recursive function:

```text id="m8q3p7"
foo<T>
```

có thể specialize concrete `T` rồi inline một số tầng.

Termination budget vẫn bắt buộc.

---

# 62. Dynamic library

Trong shared library:

```text id="x7r2m5"
closed-world = false
```

do đó:

- conservative devirtualization;
- conservative reachability;
- exported functions preserved.

---

# 63. Executable

Trong fully linked executable:

```text id="p5n8q2"
closed-world = stronger
```

có thể:

- dead-strip;
- devirtualize;
- clone;
- inline;
- specialize mạnh hơn.

---

# 64. Plugins/dynamic loading

Nếu program sử dụng dynamic loading:

```text id="m3q7r8"
dlopen-like semantics
```

compiler không được giả định toàn bộ target set đã biết.

---

# 65. Reflection

Runtime reflection có thể làm một type/function reachable dù không có static call.

Do đó reflection metadata phải tạo reachability roots.

---

# 66. Compile-time reflection

Compile-time reflection:

```text id="v8m2q5"
comptime
```

có thể generate static calls/types.

Sau generation:

```text id="q4r7n1"
ordinary code
```

và optimizer hoạt động bình thường.

---

# 67. Optimization feedback

Mỗi inline decision:

```text id="p3m8q2"
InlineDecision {
    caller
    callee
    legal
    profitable
    estimated_growth
    estimated_benefit
    reason
}
```

---

# 68. AI inspection

```text id="x7q3m5"
axc inspect inline foo
axc inspect specialize foo
axc inspect devirtualize foo
```

Ví dụ:

```text
foo → bar

Inlining:
    legal: yes
    profitable: no
    reason: code growth 3.4 KiB
    callsite: cold
```

---

# 69. Không expose heuristic thành language semantics

Programmer không nên phải dựa vào:

```text id="m8r2q6"
“compiler chắc chắn sẽ inline”
```

Language semantics vẫn đúng nếu:

```text
-O0
-O2
-O3
```

khác nhau.

---

# 70. Attributes chỉ là optimization hints

Nếu Axiom hỗ trợ:

```text id="q4n7p2"
@inline(always)
@inline(never)
@cold
@hot
```

thì chúng phải được xem là **optimization constraints/hints**, không phải semantic constructs.

---

# 71. Một abstraction hoàn toàn có thể biến mất

Ví dụ:

```ax
struct Vec2 {
    x: f32,
    y: f32,
}

fn length(self: Vec2) -> f32 {
    sqrt(self.x * self.x + self.y * self.y)
}
```

Source có:

```text
struct
method
function call
```

OptIR có thể chỉ còn:

```text id="v6m2q8"
%x2 = mul %x, %x
%y2 = mul %y, %y
%s  = add %x2, %y2
%r  = sqrt %s
```

Machine code có thể không còn bất kỳ dấu vết nào của:

- `Vec2`;
- method;
- abstraction;
- function call.

Đó mới là **zero-cost abstraction thực tế**.

---

# 72. Nhưng abstraction có observable identity thì không biến mất

Nếu:

```text id="p8q3m6"
function pointer
dyn Trait
stable address
FFI ABI
reflection
allocation identity
```

được quan sát, compiler phải giữ representation cần thiết.

---

# 73. Đây là nguyên tắc “abstraction erasure”

Formalize:

```text id="m4r7q2"
An abstraction may be erased iff
its erasure preserves all observable semantics.
```

Không phải:

```text
“compiler thấy nó không cần”
```

mà là:

```text
proof of non-observability
```

---

# 74. Invariants

### `AINLINE-20`
Inlining preserves observable semantics.

### `AINLINE-21`
Inlining legality is independent from profitability.

### `AINLINE-22`
CostModel cannot override legality.

### `AINLINE-23`
Inlining cannot bypass verification.

### `AINLINE-24`
Recursive inlining has bounded expansion.

### `AINLINE-25`
Mutually recursive SCCs cannot cause unbounded inline expansion.

### `AINLINE-26`
Inlining preserves Drop semantics.

### `AINLINE-27`
Inlining preserves capability semantics.

### `AINLINE-28`
Inlining preserves ownership semantics.

### `AINLINE-29`
Inlining preserves atomic and synchronization semantics.

### `AINLINE-30`
Inlining preserves FFI-visible behavior.

### `AINLINE-31`
Inlining preserves ABI contracts at externally visible boundaries.

### `AINLINE-32`
`@inline(always)` cannot force an illegal transformation.

### `AINLINE-33`
`@inline(never)` is an optimization constraint, not a semantic distinction.

### `AINLINE-34`
Closure inlining preserves capture semantics.

### `AINLINE-35`
Closure elimination requires non-observable closure identity.

### `AINLINE-36`
Function-pointer identity prevents invalid function elimination.

### `ASPEC-20`
Generic specialization preserves generic semantics.

### `ASPEC-21`
Specialization is performed only after semantic generic resolution.

### `ASPEC-22`
Specialized instances have canonical identities.

### `ASPEC-23`
Specialization cannot bypass ownership verification.

### `ASPEC-24`
Specialization cannot fabricate trait obligations.

### `ASPEC-25`
Specialization cannot weaken safety.

### `ASPEC-26`
Specialization may refine representation.

### `ASPEC-27`
Specialization may refine effect summaries.

### `ASPEC-28`
Specialization may refine alias information only when proven.

### `ASPEC-29`
Specialization may exploit constant generic arguments.

### `ASPEC-30`
Specialization is bounded by compile-time and code-size budgets.

### `ASPEC-31`
Equivalent generic instances may share implementation when semantics permit.

### `ASPEC-32`
Code sharing cannot merge observably distinct identities.

### `ASPEC-33`
Generic specialization may be partial.

### `ASPEC-34`
Generic specialization may use profile information.

### `ASPEC-35`
PGO cannot alter specialization legality.

### `ADEvirt-20`
Static trait dispatch does not require runtime dispatch.

### `ADEvirt-21`
`dyn Trait` is explicitly dynamic.

### `ADEvirt-22`
Devirtualization requires a proven concrete target.

### `ADEvirt-23`
Finite target sets may use guarded or multi-target dispatch.

### `ADEvirt-24`
Unknown target sets remain dynamically dispatched.

### `ADEvirt-25`
Closed-world assumptions must be explicitly valid.

### `ADEvirt-26`
Exports prevent invalid closed-world assumptions.

### `ADEvirt-27`
Dynamic loading prevents unsafe whole-program assumptions.

### `ADEvirt-28`
Reflection-preserved entities remain reachable.

### `ADEvirt-29`
Successful devirtualization may enable inlining.

### `ADEvirt-30`
Devirtualization cannot alter externally observable dispatch semantics.

### `AABST-20`
Source-level abstraction may be erased when non-observability is proven.

### `AABST-21`
Abstraction erasure must preserve observable semantics.

### `AABST-22`
Compiler optimization is not part of language semantics.

### `AABST-23`
Different optimization levels must preserve semantics.

### `AABST-24`
Observable identity prevents invalid abstraction erasure.

### `AABST-25`
Observable address prevents invalid abstraction erasure.

### `AABST-26`
FFI boundaries prevent invalid ABI erasure.

### `AABST-27`
Reflection can prevent invalid reachability elimination.

### `AABST-28`
Optimization metadata must not create mandatory runtime overhead.

### `AABST-29`
AI/compiler inspection can explain abstraction-erasure decisions.

### `AABST-30`
Specialized/generated code re-enters appropriate verification boundaries.

---

# Kiến trúc Axiom sau BOOTSTRAP-142

Ta đã có một chuỗi rất quan trọng:

```text id="g8m3q2"
                    SOURCE
                      │
                     HIR
                      │
                     MIR
                      │
                VERIFICATION
                      │
                VERIFIED MIR
                      │
          ┌───────────┼───────────┐
          │           │           │
        Alias       Effect      Escape
          └───────────┼───────────┘
                      │
                SSA + MemorySSA
                      │
                    OptIR
                      │
               ┌──────┴──────┐
               │ Call Graph  │
               └──────┬──────┘
                      │
             Interprocedural
                      │
       ┌──────────────┼──────────────┐
       │              │              │
 Specialization    Inlining    Devirtualization
       └──────────────┼──────────────┘
                      │
               Constant Propagation
                      │
                Loop/Memory/Vector
                      │
               Optimized OptIR
                      │
                    ABI MIR
                      │
                    LIR
                      │
                   MACHINE
```

Điều đáng chú ý là **không một bước nào yêu cầu programmer viết hàng đống annotation để compiler biết phải làm gì**.

---

# BOOTSTRAP-143 — Loop Optimization, Scalar Evolution & Bounds-Check Elimination

Bước tiếp theo nên khóa **loop optimizer**, bởi đây là nơi Axiom có thể chuyển rất nhiều code high-level thành machine code cực mạnh.

Trọng tâm:

```text id="c4n8q2"
Loop Detection
      ↓
Loop Canonicalization
      ↓
Induction Variables
      ↓
Scalar Evolution
      ↓
Range Analysis
      ↓
Bounds-Check Elimination
      ↓
LICM
      ↓
Loop Unswitching
      ↓
Unrolling / Peeling
      ↓
Vectorization
      ↓
Target-aware optimization
```

Đặc biệt cần giải quyết một mục tiêu rất đáng giá cho Axiom:

```ax
for i in 0..n {
    out[i] = a[i] + b[i];
}
```

có thể tự động biến thành code không bounds-check, vectorized, register-efficient **mà programmer không cần pointer arithmetic, `unsafe`, `restrict`, hay annotation alias thủ công**, khi compiler có đủ proof.