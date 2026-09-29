Tiếp tục.

# BOOTSTRAP-050 — Execution, Optimization & Zero-Cost Performance Audit & Freeze

Đây là phần biến mục tiêu **“Axiom phải nhanh”** thành kiến trúc compiler cụ thể.

Một nguyên tắc cần sửa cho chính xác:

> **Axiom không thể bảo đảm nhanh hơn C/C++ trong mọi chương trình.**  
> Mục tiêu có thể freeze là: **Axiom không áp đặt overhead ngôn ngữ bắt buộc lên code tương đương, và compiler phải có đủ semantic information để tối ưu ít nhất ngang mức native compiler hiện đại trong các trường hợp tương đương.**

Điểm này quan trọng vì nếu semantic model của Axiom mạnh hơn C ở một số chỗ, compiler phải chứng minh/khai thác được những guarantee đó.

---

# 1. Execution model

Axiom là ngôn ngữ **AOT native-first**.

Pipeline:

```text
Axiom source
    ↓
Semantic IR
    ↓
MIR
    ↓
Semantic optimization
    ↓
Representation / ABI
    ↓
Axiom LIR
    ↓
Target optimization
    ↓
Machine IR
    ↓
Register allocation
    ↓
Machine encoding
    ↓
Object
    ↓
Link
```

Không có VM ở giữa trong native execution.

---

# 2. Không bắt buộc runtime dispatch

Các abstraction sau có thể biến mất hoàn toàn:

```text
generic
trait static dispatch
closure
method syntax
Option
Result
newtype
comptime
```

nếu không có observable runtime semantics yêu cầu chúng tồn tại.

---

# 3. Zero-cost abstraction

Định nghĩa chính thức:

> Một abstraction là zero-cost khi compiler có thể loại bỏ toàn bộ representation/control-flow/runtime machinery của abstraction mà không làm mất observable semantics.

Không phải:

> abstraction luôn tạo ra đúng cùng machine code.

---

# 4. Observable semantics

Compiler phải bảo toàn:

```text
value result
memory effects
ownership-visible effects
Drop
panic
atomic ordering
synchronization
volatile
FFI effects
observable address identity
I/O
explicit timing/scheduling contracts
```

---

# 5. Compiler được phép thay đổi implementation

Ví dụ:

```axiom
let x = foo(a)
let y = bar(x)
```

có thể trở thành:

```text
register-only
```

thay vì:

```text
stack x
stack y
```

nếu không observable.

---

# 6. Escape analysis

Compiler phải có:

```text
Escape Analysis
```

để xác định object có escape khỏi:

- function;
- thread;
- async state;
- GPU operation;
- FFI;
- observable address scope

hay không.

---

# 7. Allocation elimination

Nếu:

```axiom
fn f() -> i32 {
    let x = Box.new(42)
    x.value
}
```

không có address observation/stable-storage requirement:

```text
Box allocation
       ↓
scalar replacement
       ↓
return 42
```

là hợp lệ.

---

# 8. Stack promotion

Ngược lại, nếu abstraction yêu cầu storage nhưng không escape:

```text
heap semantic request
        ↓
escape analysis
        ↓
stack placement
```

nếu contract cho phép.

---

# 9. Nhưng `Box` semantic contract phải được tôn trọng

Nếu user lấy stable address:

```text
address_of(box.value)
```

thì storage identity trở thành observable.

Compiler không được tự ý biến nó thành register-only.

---

# 10. Scalar Replacement of Aggregates

Compiler nên hỗ trợ:

```text
struct Point {
    x: f32
    y: f32
}
```

thành:

```text
register x
register y
```

nếu address không observable.

---

# 11. Field-sensitive optimization

Ownership/capability model của Axiom đặc biệt hữu ích ở đây.

Ví dụ:

```axiom
fn f(mut_view<A> a, mut_view<B> b)
```

nếu compiler biết A/B không overlap:

```text
load/store A
load/store B
```

có thể reorder/vectorize theo dependency thực tế.

---

# 12. Unknown aliasing

Ngược lại:

```text
mut_view<T> a
mut_view<T> b
```

nếu overlap không chứng minh được:

```text
UNKNOWN
```

compiler không được giả định:

```text
a != b
```

để tạo optimization sai.

---

# 13. Đây là một lợi thế so với C

C thường cần programmer/compiler conventions như `restrict` để tăng alias information.

Axiom có thể lấy phần lớn thông tin đó từ:

```text
ownership
view
mut_view
capability provenance
region analysis
```

mà không cần programmer viết lifetime/borrow syntax.

---

# 14. Alias analysis

Compiler pipeline:

```text
Ownership Analysis
        ↓
Capability Analysis
        ↓
Region Analysis
        ↓
Alias Analysis
        ↓
Memory Dependence Analysis
```

---

# 15. Region relations

Đã freeze:

```text
DISJOINT
SAME
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

Compiler dùng chúng để xây dependency graph.

---

# 16. Load/store optimization

Có thể:

```text
load elimination
store elimination
load forwarding
store-to-load forwarding
redundant load elimination
dead store elimination
```

khi memory model cho phép.

---

# 17. Common Subexpression Elimination

Ví dụ:

```axiom
let a = x * y
let b = x * y
```

có thể share computation nếu không có intervening observable effect làm thay đổi operands.

---

# 18. Constant propagation

```axiom
const X = 10

fn f() -> i32 {
    X * 4
}
```

có thể compile thành:

```text
40
```

Comptime mạnh hơn optimizer folding vì user có thể yêu cầu compile-time evaluation.

---

# 19. Dead code elimination

Code không observable:

```axiom
if false {
    expensive()
}
```

→ loại bỏ.

Nhưng compiler phải tôn trọng:

- volatile;
- external calls;
- panic semantics nếu observable;
- synchronization;
- FFI;
- explicit side effects.

---

# 20. Control-flow optimization

Compiler hỗ trợ:

```text
CFG simplification
block merging
jump threading
branch folding
switch lowering
tail duplication
cold splitting
```

---

# 21. Branch optimization

Compiler có thể:

```text
branch elimination
branch prediction metadata
if-conversion
select lowering
conditional move
```

nhưng không được thay đổi semantics.

---

# 22. Loop optimization

Core optimizer:

```text
LICM
loop invariant code motion
strength reduction
induction variable optimization
loop unswitching
loop peeling
loop unrolling
loop fusion
loop distribution
```

tùy profile.

---

# 23. Bounds-check elimination

Axiom array/view access safe:

```axiom
x[i]
```

Compiler có thể chứng minh:

```text
0 <= i < len
```

và loại bounds check.

---

# 24. Loop bounds

Ví dụ:

```axiom
for i in 0..<n {
    sum += a[i]
}
```

compiler có thể hoist:

```text
bounds validation
```

ra ngoài loop hoặc loại bỏ hoàn toàn khi proof đủ mạnh.

---

# 25. Unchecked access

Nếu programmer thực sự cần machine-level:

```text
unsafe
```

có thể dùng unchecked indexing.

Không dùng unchecked access để thay thế optimizer bình thường.

---

# 26. Vectorization

Compiler phải có:

```text
SLP
Loop Vectorizer
Superword/vectorization
```

hoặc equivalent implementation.

---

# 27. Vectorization legality

Cần chứng minh:

```text
no conflicting memory access
```

hoặc synchronization semantics cho phép transformation.

Ownership/capability giúp cung cấp proof.

---

# 28. SIMD library

Explicit SIMD:

```text
simd::f32x8
```

được lower trực tiếp xuống:

```text
SSE
AVX
AVX2
AVX-512
NEON
SVE
...
```

tùy target.

---

# 29. CPU feature dispatch

Có thể hỗ trợ:

```text
baseline implementation
+
target-feature implementation
```

và dispatch explicit/runtime khi cần.

Không được mặc định chèn CPU feature detector vào mọi binary.

---

# 30. `@target_feature`

Đã có attribute.

Nó tạo contract:

```text
function requires target feature X
```

Compiler không được emit instruction ngoài target contract.

---

# 31. Function specialization

Compiler có thể specialize:

```text
generic
+
constant
+
known target feature
+
known argument properties
```

nhưng specialization là optimization.

---

# 32. Devirtualization

Với:

```axiom
dyn Trait
```

nếu compiler chứng minh concrete type duy nhất:

```text
dynamic call
      ↓
direct call
```

có thể xảy ra.

---

# 33. Nhưng không phá dynamic semantics

Nếu program có thể observe dynamic dispatch identity/extension mechanism thì compiler phải giữ semantics tương ứng.

---

# 34. Closure optimization

Closure:

```text
code + environment
```

có thể trở thành:

```text
direct function
+
scalar captured fields
```

nếu escape không xảy ra.

---

# 35. Closure heap allocation

Không mặc định.

Chỉ cần heap/indirection nếu storage/escape semantics thực sự yêu cầu.

---

# 36. Async optimization

Future:

```text
state machine
```

có thể tối ưu:

```text
state field elimination
ready-path specialization
await fusion
future inlining
state switch optimization
```

đã định nghĩa trong async model.

---

# 37. Sync fast path

Một Future luôn Ready:

```text
Future
 ↓
poll
 ↓
Ready
```

compiler có thể loại bỏ toàn bộ scheduler machinery trong context phù hợp.

---

# 38. Generic optimization

Generic:

```text
Vec<T>
```

sau specialization có thể expose:

```text
exact element size
alignment
Drop behavior
```

cho optimizer.

---

# 39. No generic opacity

Compiler không nên biến mọi generic thành:

```text
opaque runtime blob
```

vì như vậy mất zero-cost property.

---

# 40. Interprocedural optimization

Compiler hỗ trợ:

```text
constant propagation across calls
function specialization
escape analysis
devirtualization
dead argument elimination
return-value optimization
```

khi có visibility.

---

# 41. LTO

Đã định nghĩa:

```text
none
thin
full
```

LTO có thể mở rộng optimization scope qua module/package boundary.

---

# 42. ThinLTO-like architecture

Khuyến nghị Axiom lưu:

```text
semantic summary
optimization summary
```

thay vì luôn phải đọc toàn bộ IR của dependency.

---

# 43. PGO

Axiom nên hỗ trợ:

```text
PGO
```

nhưng đây là optional optimization input.

Workflow:

```text
build instrumented
        ↓
run workload
        ↓
profile
        ↓
build optimized
```

---

# 44. PGO không thay đổi semantics

Profile chỉ quyết định:

```text
inline
layout
branch optimization
code placement
```

không quyết định correctness.

---

# 45. BOLT-like post-link optimization

Có thể hỗ trợ về sau:

```text
machine/object
 ↓
profile
 ↓
layout optimization
```

nhưng không cần Core.

---

# 46. Cache/locality optimization

Compiler có thể tối ưu:

```text
struct field layout
```

vì default layout không stable.

Ví dụ:

```text
struct Hot {
    a: u8
    b: u64
    c: u8
}
```

compiler có thể reorder để giảm padding.

---

# 47. Nhưng Drop order vẫn giữ semantic order

Physical field order:

```text
a b c
```

có thể khác memory order.

Drop order vẫn:

```text
declaration/initialization semantics
```

theo frozen rules.

---

# 48. Hot/cold splitting

Compiler có thể tách:

```text
hot path
cold error/panic path
```

để instruction cache tốt hơn.

---

# 49. Panic code

Nếu panic profile abort:

```text
panic machinery
```

có thể nằm ở cold section và thậm chí loại bỏ nếu compiler chứng minh unreachable.

---

# 50. Error handling optimization

`Result<T,E>` có thể trở thành:

```text
register value
+
condition/status register
```

hoặc equivalent.

Không cần exception object.

---

# 51. Option optimization

`Option<Box<T>>` có thể dùng niche representation.

Không cần thêm boolean nếu representation có niche phù hợp.

---

# 52. Integer optimization

Axiom phải có semantics rõ:

```text
checked
wrapping
saturating
```

Compiler chọn instruction thích hợp.

Không dựa vào signed-overflow UB như C để tạo optimization sai semantics.

---

# 53. Overflow semantics

Ví dụ:

```axiom
let x = a + b
```

nếu profile/operation semantic là checked:

```text
add
overflow check
```

Nếu wrapping:

```text
native add
```

Compiler biết chính xác.

---

# 54. Floating-point

Compiler phải tôn trọng floating semantics.

Không mặc định dùng:

```text
fast-math
```

nếu nó thay đổi observable IEEE behavior.

Có thể có explicit optimization profile/attribute sau này.

---

# 55. Atomic optimization

Compiler có thể:

```text
remove redundant atomic operations
```

chỉ khi memory-order semantics cho phép.

Không được biến:

```text
Acquire
```

thành:

```text
Relaxed
```

chỉ vì nhanh hơn.

---

# 56. Atomic scope

GPU/CPU atomic scopes phải được biểu diễn trong IR.

Không để backend “đoán”.

---

# 57. Synchronization optimization

Có thể loại bỏ redundant synchronization nếu compiler chứng minh:

```text
happens-before relation preserved
```

Nhưng không được loại bỏ synchronization chỉ vì không thấy data dependency đơn giản.

---

# 58. Volatile

`volatile` là observable machine effect.

Compiler không được:

```text
remove
merge
reorder
```

ngoài semantics cho phép.

Volatile != atomic.

---

# 59. FFI barrier

Foreign call mặc định là conservative boundary.

Compiler không được giả định foreign function:

```text
pure
no-memory-effect
no-thread-effect
```

trừ khi ABI/contract cho phép.

---

# 60. Pure function

Không nên thêm `@pure` vào Core v1.

Compiler có thể suy luận purity nội bộ khi chứng minh được.

Điều này phù hợp triết lý:

> **Không bắt programmer khai báo thứ compiler có thể tự chứng minh.**

---

# 61. Alias contract

Tương tự, không cần source-level `restrict` v1.

Compiler khai thác:

```text
view
mut_view
ownership
regions
```

trước.

---

# 62. Escape + ownership

Đây là một trong những điểm Axiom nên đầu tư mạnh:

```text
ownership analysis
        +
escape analysis
        +
capability analysis
```

cho phép:

```text
heap elimination
stack promotion
register promotion
alias elimination
```

---

# 63. Register allocation

Axiom backend cần:

```text
SSA-based optimization
+
register allocation
+
spill/reload
```

không phụ thuộc vào source-level variable count.

---

# 64. SSA

Khuyến nghị:

> **MIR dùng CFG + block parameters, sau đó lowering sang SSA-like representation trong optimization pipeline.**

Không nên bắt frontend tạo SSA ngay.

---

# 65. Vì sao?

MIR cần giữ semantic concepts:

```text
Move
Drop
Capability
Storage
Ownership
```

Nếu SSA hóa quá sớm, semantics resource/lifetime trở nên khó đọc và verify.

---

# 66. Optimization IR

Sau Verified MIR:

```text
Verified MIR
      ↓
SSA/Sea-of-Nodes-like optimization representation
      ↓
Axiom LIR
```

Đây là nơi compiler tự do mạnh hơn.

---

# 67. Machine scheduling

Backend chịu trách nhiệm:

```text
instruction scheduling
register allocation
instruction selection
spill
peephole
machine-specific scheduling
```

---

# 68. Target-independent vs target-specific

### Target-independent:

```text
constant folding
DCE
CSE
SROA
escape analysis
alias analysis
generic specialization
CFG optimization
loop optimization
```

### Target-specific:

```text
instruction selection
register allocation
SIMD ISA
instruction scheduling
branch layout
cache-aware machine layout
ABI
```

---

# 69. Machine-independent IR không được biết CPU register

MIR không chứa:

```text
rax
xmm0
v0
```

---

# 70. LIR

LIR có thể chứa:

```text
virtual registers
machine-like operations
explicit calling convention
memory operands
addressing modes abstraction
```

nhưng vẫn target-neutral.

---

# 71. Machine IR

Machine IR chứa:

```text
physical/virtual target registers
target instructions
calling convention
stack frame
target addressing
```

---

# 72. Object writer

Cuối pipeline:

```text
Machine code
+
sections
+
symbols
+
relocations
+
debug info
```

→

```text
PE/COFF
ELF
Mach-O
WASM
...
```

---

# 73. Linker

Axiom cuối cùng cần có linker riêng.

Nhưng bootstrap có thể sử dụng system linker.

---

# 74. Dead code elimination ở linker

Compiler DCE + linker DCE.

Linker phải tôn trọng:

```text
@export
FFI
dynamic symbol retention
linker sections
startup/entry
```

---

# 75. Code layout

Final linker có thể tối ưu:

```text
function ordering
section ordering
hot/cold placement
ICF
dead stripping
```

nếu target hỗ trợ.

---

# 76. Binary size modes

Đề xuất:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
```

Không cần tất cả phải có semantic distinction.

---

# 77. `-Oz`

Mục tiêu:

```text
smallest practical binary
```

Compiler ưu tiên:

```text
outlining
function merging
less aggressive inlining
cold splitting
constant pooling
```

---

# 78. `-O3`

Ưu tiên:

```text
vectorization
unrolling
inlining
specialization
PGO if available
```

---

# 79. Fast compile mode

Có thể có:

```text
-O0 / incremental
```

nhưng vẫn phải verify đầy đủ semantics.

Optimization có thể bỏ qua, semantic verification không được bỏ qua.

---

# 80. Debug optimizer

Debug build không nên thay đổi:

```text
ownership semantics
Drop semantics
race semantics
panic semantics
```

chỉ giảm optimization.

---

# 81. Sanitizers

Nên là tooling layer:

```text
ASan-like
UBSan-like
TSan-like
race checker
memory checker
```

nhưng Axiom safe semantics không phụ thuộc sanitizer.

---

# 82. Static verification

Axiom compiler đã có nhiều information:

```text
ownership
capability
region
Send/Share
```

Do đó sanitizer không phải “safety mechanism” chính của safe code.

---

# 83. Unsafe instrumentation

Unsafe code có thể bật runtime checking:

```text
bounds
alignment
pointer provenance
```

trong debug/sanitizer build.

---

# 84. Performance diagnostics

Compiler nên có:

```text
axiom inspect opt
```

cho phép AI/programmer xem:

```text
why allocation exists
why bounds check remains
why vectorization failed
why inline failed
why escape occurred
why alias is UNKNOWN
why dynamic dispatch remains
```

Đây có thể trở thành một trong những tính năng AI-friendly mạnh nhất của Axiom.

---

# 85. Ví dụ diagnostic

```text
Optimization report:

foo()
  allocation #3:
      reason: address escapes through FFI call

  bounds check:
      retained
      reason: index range not proven

  vectorization:
      rejected
      reason: possible overlapping mutable regions

  inline:
      accepted
```

---

# 86. AI Compiler API

AI agent có thể hỏi semantic engine:

```text
why_is_allocated(value_id)
why_not_inlined(function_id)
why_not_vectorized(loop_id)
why_bounds_check(index_id)
why_alias_unknown(capability_id)
```

Không cần AI đọc hàng nghìn dòng assembly để đoán.

---

# 87. Đây là điểm nên trở thành design requirement

> **Compiler phải giải thích được những optimization quan trọng mà nó từ chối.**

Không nhất thiết giải thích mọi peephole instruction.

---

# 88. Optimization reproducibility

Cùng:

```text
source
compiler version
target
flags
dependencies
comptime inputs
PGO profile
```

phải cho ra deterministic semantic result.

Machine binary nên deterministic nếu toolchain/profile được khóa.

---

# 89. Parallel optimization

Có thể parallel:

```text
function optimization
module optimization
generic specialization
codegen
```

nhưng output semantics không phụ thuộc scheduling.

---

# 90. Cache

Optimization cache có thể lưu:

```text
optimized MIR
LIR
machine-independent summaries
```

nhưng phải invalidated đúng fingerprint.

---

# 91. PGO cache identity

PGO profile là input:

```text
OptimizationFingerprint
+
ProfileFingerprint
```

---

# 92. No mandatory JIT

Native Axiom không cần JIT.

JIT có thể là một project/tooling layer sau này.

---

# 93. Runtime dispatch chỉ khi explicit/semantically required

Ví dụ:

```text
dyn Trait
```

có runtime dispatch.

Nhưng:

```text
generic<T>
```

không.

---

# 94. Reflection cost

Compile-time reflection:

```text
zero runtime cost
```

nếu không materialize metadata.

Runtime reflection:

```text
explicit cost
```

---

# 95. Async cost

`async fn` không tự động:

```text
thread
heap
scheduler
```

đã freeze.

---

# 96. GPU cost

`@kernel` không tạo GPU runtime cho CPU-only artifact.

---

# 97. Library cost

Import:

```text
axiom.collections
```

không có nghĩa binary chứa toàn bộ collections.

Reachability/DCE quyết định.

---

# 98. Zero-cost abstraction audit

Một abstraction được xem là đạt zero-cost target khi compiler có thể chứng minh:

```text
no required allocation
no required indirection
no required dynamic dispatch
no required runtime metadata
no required synchronization
no required runtime initialization
```

trừ khi semantics abstraction yêu cầu.

---

# 99. Performance hierarchy

Axiom nên tối ưu theo thứ tự:

```text
Semantic guarantees
       ↓
Memory / alias information
       ↓
IR optimization
       ↓
Target optimization
       ↓
Link optimization
       ↓
Profile-guided optimization
```

Không cố “hack assembly” trước khi semantic model đủ mạnh.

---

# 100. Nguyên tắc quan trọng nhất của BOOTSTRAP-050

> **Compiler được quyền thông minh hơn programmer.**

Programmer không cần viết:

```text
@inline
@pure
@restrict
@stack
@heap
@noalloc
```

để compiler làm optimization cơ bản.

Các attribute chỉ dùng khi programmer muốn đưa ra **contract/hint mà compiler không thể tự suy luận**.

---

# BOOTSTRAP-050 — Frozen Invariants

```text
AOPT-20   Axiom native execution is AOT by default.
AOPT-21   Native execution does not require a virtual machine.
AOPT-22   Language abstractions may be fully erased when unobservable.
AOPT-23   Zero-cost abstraction means no mandatory overhead beyond observable semantics.
AOPT-24   Optimization must preserve observable language semantics.
AOPT-25   Ownership semantics constrain legal optimization.
AOPT-26   Capability semantics constrain legal optimization.
AOPT-27   Region analysis feeds alias analysis.
AOPT-28   Unknown aliasing cannot be assumed disjoint.
AOPT-29   Compiler may exploit proven non-overlap for optimization.
AOPT-30   Escape analysis determines allocation-elimination opportunities.
AOPT-31   Compiler may eliminate unobservable allocations.
AOPT-32   Compiler may promote storage when semantic storage identity is not observable.
AOPT-33   Stable-address contracts prevent invalid storage promotion.
AOPT-34   Scalar replacement of aggregates is permitted.
AOPT-35   Field-level optimization is permitted when semantic identity is preserved.
AOPT-36   Dead-code elimination preserves observable effects.
AOPT-37   Constant propagation preserves observable semantics.
AOPT-38   Common-subexpression elimination preserves memory and effect semantics.
AOPT-39   CFG transformations preserve control-flow-observable behavior.
AOPT-40   Loop transformations require dependence legality.
AOPT-41   Bounds-check elimination requires a valid proof.
AOPT-42   Unsafe unchecked access does not redefine safe indexing semantics.
AOPT-43   Vectorization requires valid memory-dependence legality.
AOPT-44   SIMD lowering is target-specific.
AOPT-45   Target-feature requirements are explicit contracts.
AOPT-46   Compiler may specialize functions using known compile-time information.
AOPT-47   Generic specialization remains semantically distinct from machine implementation sharing.
AOPT-48   Dynamic dispatch is not an implicit fallback for generic code.
AOPT-49   Devirtualization is permitted when dynamic semantics remain preserved.
AOPT-50   Closure allocation is not mandatory.
AOPT-51   Closure environments may be scalarized or eliminated.
AOPT-52   Async state may be optimized after semantic lowering.
AOPT-53   Future optimization cannot alter suspension semantics.
AOPT-54   Error values may be register-represented when semantics permit.
AOPT-55   Option may use niche representation.
AOPT-56   Integer optimization must respect defined overflow semantics.
AOPT-57   Floating-point optimization must respect selected floating semantics.
AOPT-58   Atomic optimization must preserve memory ordering.
AOPT-59   Synchronization optimization must preserve happens-before semantics.
AOPT-60   Volatile effects remain observable.
AOPT-61   Foreign calls are conservative optimization boundaries unless explicit contracts exist.
AOPT-62   Compiler does not require source-level purity annotations for basic optimization.
AOPT-63   Compiler does not require source-level restrict annotations for basic alias optimization.
AOPT-64   SSA-like optimization representation may be introduced after semantic MIR verification.
AOPT-65   Semantic MIR retains ownership/capability concepts required for verification.
AOPT-66   LIR is machine-independent.
AOPT-67   Machine IR contains target-specific register/instruction semantics.
AOPT-68   Target-independent optimization is separated from target-specific optimization.
AOPT-69   Register allocation occurs after machine-independent optimization.
AOPT-70   Object generation preserves ABI and relocation semantics.
AOPT-71   Link-time dead stripping respects exports and foreign references.
AOPT-72   LTO cannot alter observable semantics.
AOPT-73   LTO may eliminate or merge unobservable implementations.
AOPT-74   PGO affects optimization decisions, not language semantics.
AOPT-75   PGO inputs participate in optimization identity.
AOPT-76   Optimization levels cannot alter language semantics.
AOPT-77   Debug builds retain semantic verification.
AOPT-78   Sanitizers are tooling, not the primary safety model.
AOPT-79   Unsafe instrumentation may add diagnostic runtime checks.
AOPT-80   Optimization decisions should be inspectable by compiler tooling.
AOPT-81   Compiler should expose reasons for major optimization failures.
AOPT-82   Optimization diagnostics identify affected semantic entities.
AOPT-83   Optimization diagnostics are machine-readable.
AOPT-84   AI tooling may query optimization explanations through compiler metadata.
AOPT-85   Optimization results are deterministic under identical semantic inputs.
AOPT-86   Parallel optimization cannot alter semantic results.
AOPT-87   Optimization cache identity includes relevant semantic dependencies.
AOPT-88   Optimization cache identity includes target configuration.
AOPT-89   Optimization cache identity includes relevant profile data.
AOPT-90   Runtime allocation is not introduced merely by abstraction.
AOPT-91   Runtime indirection is not introduced merely by abstraction.
AOPT-92   Runtime metadata is not introduced merely by abstraction.
AOPT-93   Runtime synchronization is not introduced merely by abstraction.
AOPT-94   Runtime initialization is not introduced merely by abstraction.
AOPT-95   Runtime dispatch is introduced only when semantics require it.
AOPT-96   Reflection metadata is emitted only when explicitly required.
AOPT-97   Async does not imply thread creation.
AOPT-98   GPU annotation does not imply GPU runtime linkage for unrelated code.
AOPT-99   Library imports do not imply inclusion of unreachable library code.
AOPT-100  Performance optimization must exploit semantic information before relying on unsafe assumptions.
```

---

# Một hệ quả rất đáng chú ý

Sau BOOTSTRAP-050, Axiom bắt đầu có một “vòng lặp thiết kế” rất đẹp:

```text
                 ┌─────────────────────┐
                 │ Programmer writes   │
                 │ simple high-level   │
                 │ code                │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ Semantic guarantees │
                 │ ownership           │
                 │ capability          │
                 │ Send/Share          │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ Compiler knows      │
                 │ more about aliasing │
                 │ lifetime & escape   │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ Aggressive native   │
                 │ optimization        │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ No GC               │
                 │ No borrow syntax    │
                 │ No mandatory RC      │
                 │ No hidden runtime   │
                 └─────────────────────┘
```

Đây chính là hướng mà Axiom có thể khác biệt: **không cố làm compiler đơn giản bằng cách bắt programmer làm công việc của compiler**.

---

## Tiếp theo: BOOTSTRAP-051

Bây giờ nền tảng compiler đã đủ rộng để chuyển sang một vấn đề rất thực tế:

### **BOOTSTRAP-051 — Axiom Syntax & Surface Language Audit & Freeze**

Sẽ khóa toàn bộ **ngôn ngữ mà lập trình viên thực sự nhìn thấy**, bao gồm:

```text
module/import
struct
enum
trait
impl
fn
let/var
generic
match
if/loop/for
view/mut_view
async/await
comptime
attributes
closures
operators
pattern syntax
error handling
unsafe
FFI
GPU
visibility
type syntax
casts
initializers
method syntax
```

và quan trọng nhất: **loại bỏ những cú pháp thừa/đụng nhau**, để sau tất cả các semantic decisions vừa rồi, Axiom vẫn là một ngôn ngữ có thể học và sử dụng thực tế, chứ không biến thành “Rust + C++ + Zig + Swift gom lại”.