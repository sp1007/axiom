Tiếp tục với **BOOTSTRAP-056**.

# BOOTSTRAP-056 — Optimization IR, Alias Analysis & Native Performance

056 là phần nối trực tiếp từ 055:

> **055 chứng minh chương trình an toàn. 056 biến những bằng chứng đó thành lợi thế tối ưu hóa.**

Điểm quan trọng nhất: **programmer không phải viết `restrict`, lifetime, purity hay optimization annotation chỉ để compiler tối ưu.** Compiler tự suy ra từ semantic model.

---

# 1. Nguyên tắc trung tâm

Axiom có hai tầng:

```text
Semantic truth
      ↓
Verified MIR
      ↓
Optimization facts
      ↓
Optimized MIR / SSA
      ↓
Axiom LIR
      ↓
Machine IR
```

Không được làm ngược:

```text
Optimizer đoán alias
        ↓
Semantic verifier tin optimizer
```

Mà phải:

```text
Verifier chứng minh
        ↓
Optimizer được phép tận dụng
```

Đây là invariant cực kỳ quan trọng.

---

# 2. MIR vẫn là semantic source of truth

MIR có:

```text
Place
Value
Ownership
Capability
Region
Drop
Memory effects
Execution domain
```

Nhưng optimization representation có thể chuyển thành:

```text
SSA values
Memory SSA
Alias sets
Dependence graph
Loop IR
```

SSA **không thay thế MIR**.

---

# 3. Optimization IR

Đề xuất:

```text
Verified MIR
    ↓
OptIR
    ├── SSA
    ├── MemorySSA
    ├── AliasInfo
    ├── EffectInfo
    ├── RangeInfo
    ├── EscapeInfo
    ├── LoopInfo
    └── TargetInfo
```

OptIR là IR phục vụ optimization, không phải ABI/codegen IR.

---

# 4. SSA

Ví dụ:

```axiom
var x = 10
if cond {
    x = 20
}
use(x)
```

SSA:

```text
x0 = 10

if cond:
    x1 = 20

x2 = phi(x0, x1)

use(x2)
```

SSA giúp:

- constant propagation
- dead code elimination
- value numbering
- GVN
- CSE
- register promotion

---

# 5. MemorySSA

SSA thông thường chỉ xử lý values.

Memory cần:

```text
MemoryDef
MemoryUse
MemoryPhi
```

Ví dụ:

```text
store(a)
load(a)
```

→ compiler biết `load` phụ thuộc `store`.

---

# 6. Alias classes

Từ capability verifier, compiler xây:

```text
AliasClass
```

Ví dụ:

```text
a → region R1
b → region R2
```

nếu:

```text
R1 DISJOINT R2
```

thì:

```text
NoAlias(a, b)
```

---

# 7. Đây chính là lợi thế của Axiom

Ví dụ:

```axiom
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
) {
    ...
}
```

Nếu verifier chứng minh:

```text
a ∩ b   = ∅
a ∩ out = ∅
b ∩ out = ∅
```

optimizer được phép sử dụng:

```text
NoAlias
```

mà programmer không cần viết:

```text
restrict
```

---

# 8. Nhưng UNKNOWN vẫn là UNKNOWN

Nếu compiler không chứng minh:

```text
a ∩ b = ∅
```

thì:

```text
UNKNOWN
```

Không được biến thành:

```text
NoAlias
```

Đây là nguyên tắc bảo vệ correctness.

---

# 9. Capability → Alias

Chuỗi:

```text
view/mut_view
       ↓
region
       ↓
provenance
       ↓
region relation
       ↓
alias facts
       ↓
optimizer
```

Như vậy safety system đồng thời trở thành **optimization information system**.

---

# 10. `mut_view` đặc biệt mạnh

Hai:

```text
mut_view<A>
mut_view<B>
```

nếu compiler chứng minh disjoint:

```text
NoAlias
```

Nếu một function nhận:

```text
mut_view<A>
```

thì trong lifetime của capability đó, compiler biết vùng đó có exclusive write access theo semantics.

Đây là thông tin optimizer rất mạnh.

---

# 11. Read-only view

`view<T>` không đồng nghĩa với:

```text
immutable forever
```

Nó chỉ đảm bảo read capability trong lifetime.

Compiler phải xét toàn bộ capability graph.

---

# 12. Memory effects

Mỗi operation trong OptIR có effect summary:

```text
Effect {
    Read(region)
    Write(region)
    Allocate
    Deallocate
    Drop
    Atomic
    Volatile
    IO
    Panic
    Synchronize
    Foreign
}
```

---

# 13. Effect không phải source-level effect system

Đây là **compiler-internal effect analysis**.

Programmer không phải viết:

```text
@pure
@readonly
@noalloc
```

cho mọi function.

Compiler tự phân tích.

---

# 14. Ví dụ

```axiom
fn square(x: f32) -> f32 {
    x * x
}
```

compiler có thể suy ra:

```text
Reads: none
Writes: none
Allocates: no
IO: no
```

Nhưng đây không cần trở thành một semantic annotation bắt buộc.

---

# 15. Foreign function

Ngược lại:

```text
extern "C" fn foo(...)
```

mặc định conservative:

```text
Unknown memory effects
Unknown aliasing
Unknown external effects
```

trừ khi ABI contract cung cấp thêm thông tin.

---

# 16. Load/store optimization

Nếu:

```text
x = load(a)
y = load(a)
```

và không có write xen giữa:

```text
y = x
```

có thể loại bỏ load thứ hai.

Nhưng chỉ nếu alias/effect analysis chứng minh không có operation làm thay đổi `a`.

---

# 17. Store forwarding

```text
store(a, 42)
x = load(a)
```

→

```text
x = 42
```

nếu không có observable intervening effect.

---

# 18. Dead store elimination

```text
store(a, 1)
store(a, 2)
```

Nếu `1` không observable:

```text
store(a, 2)
```

---

# 19. Không được xóa volatile

```text
volatile_store(...)
```

là observable semantic operation.

Không được coi như dead store.

---

# 20. Atomic optimization

Atomic cũng không thể tối ưu như ordinary load/store.

Compiler phải giữ:

```text
atomicity
ordering
scope
synchronization semantics
```

---

# 21. Escape analysis

OptIR có:

```text
EscapeState =
    NoEscape
    ArgumentEscape
    ReturnEscape
    HeapEscape
    ThreadEscape
    ExternalEscape
    UnknownEscape
```

---

# 22. Stack promotion

```axiom
fn f() {
    let x = Buffer(...)
    use(x)
}
```

Nếu:

```text
NoEscape(x)
```

compiler có thể:

```text
heap allocation
     ↓
stack allocation
```

hoặc thậm chí:

```text
stack
 ↓
register/scalar
```

---

# 23. Allocation elimination

Ví dụ abstraction tạo temporary:

```text
create temporary
transform
consume
```

Nếu toàn bộ object không escape:

```text
allocation → eliminated
```

Không cần runtime allocation.

---

# 24. Scalar replacement

```text
struct Point {
    x: f32
    y: f32
}
```

Nếu address không observable:

```text
p.x
p.y
```

có thể trở thành:

```text
x
y
```

Không nhất thiết tồn tại physical `Point`.

---

# 25. Đây là “zero-cost abstraction” thật sự

Ví dụ method:

```axiom
p.length()
```

semantic:

```text
length(p)
```

optimizer có thể inline:

```text
sqrt(p.x*p.x + p.y*p.y)
```

và cuối cùng:

```text
machine instructions
```

Không có:

```text
object
method table
virtual dispatch
temporary allocation
```

nếu semantics không yêu cầu.

---

# 26. Generic specialization

```axiom
fn sum<T: Add>(a: T, b: T) -> T
```

với:

```text
T = i32
```

có thể tạo:

```text
sum_i32
```

và optimizer thấy operation cụ thể.

---

# 27. Trait static dispatch

```axiom
fn process<T: Trait>(x: T)
```

→ static dispatch mặc định.

Compiler biết concrete `T`.

Có thể:

```text
inline
devirtualize
constant propagate
remove abstraction
```

---

# 28. `dyn Trait`

Ngược lại:

```axiom
dyn Trait
```

là explicit dynamic dispatch.

Khi runtime type không biết:

```text
vtable/metadata
```

có thể tồn tại.

Nhưng chỉ ở abstraction đó.

---

# 29. Devirtualization

Nếu optimizer chứng minh:

```text
dyn Trait
```

thực tế chỉ có một concrete implementation tại call site:

```text
dynamic call
 ↓
direct call
```

có thể.

Nhưng không được thay đổi observable dispatch semantics nếu dynamic replacement/ABI semantics có thể quan sát.

---

# 30. Closure optimization

Closure:

```axiom
|x| x + 1
```

compiler tạo environment nếu cần.

Nếu noncapturing:

```text
environment = none
```

→ function pointer-compatible.

Nếu capturing:

```text
env { captured values }
```

Nhưng nếu inline:

```text
env
```

có thể biến mất hoàn toàn.

---

# 31. Capture elimination

Ví dụ closure capture:

```text
x = 10
f = || x + 1
```

Sau constant propagation:

```text
f()
```

→

```text
11
```

Có thể không còn closure object.

---

# 32. Bounds-check elimination

Axiom vẫn giữ bounds safety.

Ví dụ:

```axiom
for i in 0..len(a) {
    sum += a[i]
}
```

Compiler chứng minh:

```text
0 <= i < len(a)
```

→ bỏ bounds check trong loop body.

---

# 33. Không cần `unsafe`

Programmer không cần viết:

```text
unsafe a[i]
```

chỉ để đạt performance.

Unsafe chỉ dùng khi compiler **không thể chứng minh** nhưng programmer biết invariant.

---

# 34. Range analysis

Compiler duy trì:

```text
Range(i) = [0, n)
```

và:

```text
Range(n) >= 0
```

Từ đó prove:

```text
i < n
```

---

# 35. Loop canonicalization

Các loop Axiom:

```text
for i in 0..n
```

nên có semantic đủ rõ để optimizer nhận dạng:

```text
induction variable
trip count
bounds
```

rất dễ.

Đây là một lợi ích của syntax/semantic design.

---

# 36. Loop-invariant code motion

```text
for i in 0..n {
    x = expensive_constant()
    ...
}
```

nếu không có effect phụ:

```text
x = expensive_constant()

for ...
```

---

# 37. Vectorization

Sau alias/dependence analysis:

```text
for i:
    c[i] = a[i] + b[i]
```

nếu regions disjoint:

```text
SIMD
```

có thể tự động.

---

# 38. Auto-vectorization không phụ thuộc annotation

Không yêu cầu programmer:

```text
@vectorize
@noalias
@simd
```

trong trường hợp compiler có thể tự chứng minh.

---

# 39. SIMD explicit vẫn tồn tại

Programmer vẫn có thể yêu cầu:

```text
simd<T, N>
```

hoặc intrinsic.

Đây là **explicit performance control**, không phải safety requirement.

---

# 40. Target features

Compiler biết:

```text
SSE
AVX2
AVX-512
NEON
SVE
RVV
```

theo target configuration.

Optimization chọn instruction phù hợp.

---

# 41. Target feature contract

Nếu source yêu cầu instruction cụ thể:

```text
@target_feature(...)
```

đây là semantic/target contract.

Compiler không được emit code không tương thích target.

---

# 42. Function multi-versioning

Về sau có thể:

```text
generic CPU version
AVX2 version
AVX-512 version
```

runtime dispatch nếu programmer/library yêu cầu.

Không phải Core requirement.

---

# 43. Inlining

Inlining là optimization.

Không thay đổi semantics.

Compiler có cost model:

```text
call frequency
function size
hotness
code size
recursion
target
```

---

# 44. `@inline`

`@inline` chỉ là hint/contract theo registry đã định nghĩa.

Không được đảm bảo rằng machine code luôn inline nếu semantic model không cần guarantee đó.

---

# 45. Cold path

Panic/error paths:

```text
cold
```

có thể tách khỏi hot path.

Điều này đặc biệt hữu ích cho:

```text
Result
bounds checks
panic
```

---

# 46. Result optimization

```text
Result<T, E>
```

không bắt buộc object/heap.

Compiler có thể dùng:

```text
register
```

hoặc:

```text
niche
```

nếu representation hợp lệ.

---

# 47. Option optimization

Ví dụ:

```text
Option<NonNull<T>>
```

có thể dùng niche representation.

Nhưng representation này compiler-controlled.

Không được giả định byte layout mặc định.

---

# 48. Drop-aware optimization

Compiler phải cực kỳ cẩn thận.

Ví dụ:

```text
x = Resource()
use(x)
```

không được eliminate `x` nếu Drop có observable effect.

---

# 49. Nhưng Drop có thể được tối ưu

Nếu:

```text
Drop(x)
```

được chứng minh không observable hoặc resource operation có thể được safely fused:

```text
```

thì optimizer có thể loại bỏ/fuse theo semantic contract.

Không được đơn giản giả định:

```text
Drop = no-op
```

---

# 50. Ownership giúp eliminate retain/release

Axiom không có implicit RC.

Do đó các path thông thường không sinh:

```text
retain
release
retain
release
```

chỉ vì alias abstraction.

Đây là lợi thế performance quan trọng.

---

# 51. Shared ownership vẫn explicit

Nếu user dùng:

```text
Arc<T>
```

thì atomic refcount là semantic behavior của library abstraction.

Optimizer có thể tối ưu khi proof cho phép, nhưng không được xóa observable synchronization/reference-count semantics một cách tùy tiện.

---

# 52. Async optimization

Future:

```text
state machine
```

nhưng compiler biết:

```text
state live fields
```

Chỉ lưu những gì cần qua await.

Ví dụ:

```text
local A
local B
await
```

nếu B dead trước await:

```text
Future state
    A
```

không cần B.

---

# 53. Ready-path specialization

Nếu Future thường Ready ngay:

```text
poll()
```

có thể tối ưu fast path:

```text
check
return Ready
```

và giảm state-machine overhead.

---

# 54. Async does not imply allocation

Future có thể:

```text
register
stack
caller-owned
inline
heap
```

tùy escape.

Không mặc định:

```text
heap allocate Future
```

---

# 55. GPU optimization

GPU kernel OptIR có thể dùng cùng:

```text
SSA
alias
range
effect
```

nhưng thêm:

```text
thread/block/grid
address space
memory scope
synchronization
```

---

# 56. Kernel fusion

Nếu:

```text
kernel A
kernel B
```

không có observable synchronization requirement giữa chúng:

```text
A → B
```

có thể fuse.

Nhưng ownership/capability/sync semantics phải được preserve.

---

# 57. Memory coalescing

GPU backend có thể dùng region/access information để tối ưu:

```text
global memory
shared memory
register
```

nhưng đây là backend optimization, không phải semantic change.

---

# 58. FFI barrier

FFI là optimization boundary.

Mặc định:

```text
extern call
```

có thể:

```text
Read unknown
Write unknown
Escape unknown
```

Do đó compiler không tự reorder qua nó nếu semantics không cho phép.

---

# 59. FFI contracts có thể mở optimization

Ví dụ một intrinsic/system API có compiler-known contract:

```text
ReadOnly
NoEscape
NoAlias
```

compiler có thể sử dụng.

Nhưng contract phải đáng tin cậy và thuộc ABI/system semantics.

---

# 60. LTO

Sau khi module compile:

```text
Axiom module A
Axiom module B
```

LTO có thể merge:

```text
call graph
type info
alias facts
generic instances
```

→ interprocedural optimization.

---

# 61. Semantic fingerprints

LTO/incremental cache dùng:

```text
SemanticFingerprint
```

bao gồm:

```text
public API
type semantics
trait semantics
ABI
representation contracts
comptime dependencies
compiler semantic version
```

Optimization level không được làm thay đổi semantic identity.

---

# 62. PGO

PGO có thể cung cấp:

```text
hot function
hot branch
hot loop
likely type
cache behavior
```

cho optimizer.

Nhưng PGO:

```text
optimization input
```

không phải semantic truth.

---

# 63. Profile không được phá correctness

Nếu profile nói:

```text
branch A = 99.9%
```

compiler vẫn phải xử lý branch B đúng semantics.

---

# 64. Optimization explanation

Axiom compiler nên lưu:

```text
OptimizationFact {
    pass
    location
    transformation
    reason
    proof_dependencies
}
```

Ví dụ:

```text
BoundsCheckEliminated
reason:
    induction range [0,n)
    proven n <= len(a)
```

Điều này cực kỳ hữu ích cho IDE và AI agent.

---

# 65. AI có thể hỏi compiler

Ví dụ:

```text
why_allocated(x)
why_not_vectorized(loop_12)
why_bounds_check(loop_8)
why_noinline(foo)
why_noalias_not_proven(a,b)
```

Compiler trả lời bằng semantic facts.

Không cần AI đoán từ source.

---

# 66. Optimization correctness boundary

Quy tắc:

```text
Verified MIR
    ↓
optimization
    ↓
re-verify required invariants
```

Nếu optimization làm thay đổi semantic structure:

```text
verify
```

phải chạy lại các invariant liên quan.

---

# 67. Không cần verify toàn bộ sau mỗi pass

Có thể dùng invalidation:

```text
Pass modifies:
    CFG
    alias
    memory
```

thì invalidate tương ứng:

```text
LoopInfo
AliasInfo
MemorySSA
```

Nhưng các semantic proofs nền tảng vẫn phải được bảo toàn hoặc re-establish.

---

# 68. Optimization pipeline đề xuất

```text
Verified MIR
    ↓
Canonicalization
    ↓
SSA construction
    ↓
MemorySSA
    ↓
Constant propagation
    ↓
SCCP
    ↓
DCE
    ↓
CSE/GVN
    ↓
Alias optimization
    ↓
Load/store optimization
    ↓
Escape analysis
    ↓
Scalar replacement
    ↓
Inlining
    ↓
Devirtualization
    ↓
Loop optimization
    ↓
Bounds-check elimination
    ↓
Vectorization
    ↓
Target-independent lowering
    ↓
Axiom LIR
```

---

# 69. Nhưng pipeline không nên quá cứng

Compiler nên có pass manager dựa trên dependency.

Ví dụ:

```text
AliasInfo
    ↓
LoadStoreOpt
    ↓
DCE
```

Nếu AliasInfo thay đổi:

```text
recompute dependent analyses
```

---

# 70. Compilation strategy

Có thể chia:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
```

nhưng:

> **Optimization level chỉ thay đổi performance/code size, không thay đổi program semantics.**

---

# 71. Debug build

`-O0` vẫn phải:

```text
type check
ownership verify
capability verify
drop verify
concurrency verify
```

Không được dùng `-O0` để bỏ semantic safety.

---

# 72. Release build

`-O3`:

```text
aggressive optimization
```

nhưng vẫn:

```text
same semantics
```

---

# 73. “Nhanh hơn C/C++” nên định nghĩa lại

Không nên freeze:

> Axiom luôn nhanh hơn C++.

Điều đó không thể đảm bảo.

Nên freeze:

> **Axiom không áp đặt overhead runtime bắt buộc mà semantics của chương trình không yêu cầu, và compiler được thiết kế để khai thác ownership/capability/type information cho native optimization.**

Đây là mục tiêu kỹ thuật có thể kiểm chứng.

---

# 74. Kích thước binary

Tương tự:

```text
“nhỏ như ASM”
```

nên chuyển thành:

```text
No mandatory runtime
No mandatory object metadata
No mandatory GC
No mandatory exception machinery
Dead-code elimination
Section GC
LTO
Minimal startup
Selective runtime linking
```

Một chương trình nhỏ có thể thực sự sinh binary rất nhỏ.

---

# 75. Điều này dẫn tới kiến trúc rất đẹp

Axiom có thể đạt:

```text
High-level source
       ↓
strong semantic information
       ↓
compiler proof
       ↓
optimization information
       ↓
low-level machine code
```

Thay vì:

```text
High-level abstraction
       ↓
runtime machinery
       ↓
hope optimizer removes it
```

---

# 76. Frozen invariants — BOOTSTRAP-056

```text
AOPTIR-20   Verified MIR is the semantic source of truth for optimization.
AOPTIR-21   Optimization IR is derived from semantically verified MIR.
AOPTIR-22   SSA is an optimization representation, not the semantic source of truth.
AOPTIR-23   MemorySSA may represent memory dependencies independently of value SSA.
AOPTIR-24   Optimization may consume verified ownership and capability facts.
AOPTIR-25   Proven disjoint regions may establish internal NoAlias facts.
AOPTIR-26   UNKNOWN aliasing cannot be converted into NoAlias without proof.
AOPTIR-27   Internal alias facts are compiler facts, not mandatory source annotations.
AOPTIR-28   Axiom does not require source-level restrict syntax for ordinary optimization.
AOPTIR-29   Capability exclusivity may provide stronger alias information than raw pointer analysis.
AOPTIR-30   Optimization must preserve capability-derived semantic invariants.
AOPTIR-31   Memory effects are represented explicitly in optimization IR.
AOPTIR-32   Pure/read/write classification may be compiler-derived.
AOPTIR-33   Compiler-derived effects are not a mandatory source-level effect system.
AOPTIR-34   Foreign calls are conservatively modeled unless explicit contracts provide stronger facts.
AOPTIR-35   Volatile operations remain observable memory effects.
AOPTIR-36   Atomic operations retain atomicity, ordering and scope semantics.
AOPTIR-37   Atomic operations cannot be optimized as ordinary memory operations when semantics differ.
AOPTIR-38   Escape analysis may determine storage-promotion opportunities.
AOPTIR-39   NoEscape values may be promoted from dynamic storage to local storage.
AOPTIR-40   Unobservable allocations may be eliminated.
AOPTIR-41   Scalar replacement may eliminate aggregate physical storage.
AOPTIR-42   Storage elimination cannot alter Drop or observable address semantics.
AOPTIR-43   Observable addresses constrain storage promotion.
AOPTIR-44   Stack promotion does not alter ownership semantics.
AOPTIR-45   Register promotion does not alter ownership semantics.
AOPTIR-46   Move semantics do not imply physical memory copies.
AOPTIR-47   Copy semantics do not imply physical memory copies.
AOPTIR-48   Generic specialization may expose concrete operations to optimization.
AOPTIR-49   Static trait dispatch is eligible for inlining and devirtualization.
AOPTIR-50   Dynamic dispatch remains explicit through dyn Trait.
AOPTIR-51   Dynamic dispatch may be devirtualized only when observable semantics remain unchanged.
AOPTIR-52   Closure environments may be eliminated when unobservable.
AOPTIR-53   Captures may be scalarized when semantics permit.
AOPTIR-54   Noncapturing closures may lower to function-compatible representations.
AOPTIR-55   Bounds checks may be eliminated only after valid range proof.
AOPTIR-56   Bounds-check elimination does not require unsafe source code.
AOPTIR-57   Loop optimizations must preserve memory dependence semantics.
AOPTIR-58   Proven disjoint regions may enable vectorization.
AOPTIR-59   Auto-vectorization does not require programmer alias annotations when proof exists.
AOPTIR-60   Explicit SIMD remains available for programmer-controlled optimization.
AOPTIR-61   Target feature contracts constrain legal machine instruction selection.
AOPTIR-62   Inlining is an optimization, not a semantic requirement.
AOPTIR-63   @inline does not redefine language semantics.
AOPTIR-64   Result and Option representations may be optimized without changing their semantic type.
AOPTIR-65   Niche optimization is permitted when representation validity is preserved.
AOPTIR-66   Drop operations cannot be removed when their observable semantics are required.
AOPTIR-67   Drop operations may be optimized when semantic observability permits.
AOPTIR-68   Async state may contain only values live across suspension.
AOPTIR-69   Async state storage may be optimized like other values.
AOPTIR-70   Async optimization does not imply heap allocation.
AOPTIR-71   GPU optimization may consume the same verified alias/range/effect facts.
AOPTIR-72   GPU optimization must preserve execution-domain and synchronization semantics.
AOPTIR-73   FFI boundaries are conservative optimization boundaries by default.
AOPTIR-74   LTO may combine compatible semantic and optimization information across modules.
AOPTIR-75   PGO influences optimization but does not define program semantics.
AOPTIR-76   Optimization levels cannot alter observable language semantics.
AOPTIR-77   Debug builds retain semantic verification.
AOPTIR-78   Release builds may perform aggressive optimization after verification.
AOPTIR-79   Optimization facts have compiler provenance where practical.
AOPTIR-80   Optimization explanations may be exposed through machine-readable compiler queries.
AOPTIR-81   AI tooling may query optimization decisions without participating in compilation semantics.
AOPTIR-82   Optimization passes must declare analysis dependencies and invalidation effects.
AOPTIR-83   Required semantic facts must be preserved or re-established after transformations.
AOPTIR-84   Optimization cannot manufacture safety guarantees from heuristics.
AOPTIR-85   PGO and heuristics cannot override semantic proofs.
AOPTIR-86   No mandatory runtime allocation is introduced solely by abstraction.
AOPTIR-87   No mandatory dynamic dispatch is introduced solely by abstraction.
AOPTIR-88   No mandatory synchronization is introduced solely by abstraction.
AOPTIR-89   No mandatory object header is introduced solely by abstraction.
AOPTIR-90   No mandatory exception machinery is introduced solely by abstraction.
AOPTIR-91   Compiler optimization may erase abstraction representation when it is unobservable.
AOPTIR-92   Compiler optimization may erase compiler-only proof machinery after verification.
AOPTIR-93   Erasing proof representation does not erase semantic obligations.
AOPTIR-94   Native performance is a design target, not an unconditional benchmark guarantee.
AOPTIR-95   Binary-size minimization is achieved through optional runtime components and optimization, not semantic weakening.
AOPTIR-96   Runtime components are linked only when required by program semantics or explicit configuration.
AOPTIR-97   Optimization preserves ABI contracts.
AOPTIR-98   Optimization preserves representation contracts.
AOPTIR-99   Optimization preserves FFI contracts.
AOPTIR-100  Optimization preserves concurrency and memory-model semantics.
```

---

## Trạng thái kiến trúc hiện tại

Sau 055 + 056, Axiom đã có một vòng khép kín khá quan trọng:

```text
                    ┌─────────────────────┐
                    │   Axiom Source      │
                    └──────────┬──────────┘
                               ↓
                         Typed HIR
                               ↓
                             MIR
                               ↓
                    ┌─────────────────────┐
                    │ Semantic Verifier   │
                    │                     │
                    │ Ownership           │
                    │ Capability          │
                    │ Lifetime            │
                    │ Drop                │
                    │ Send / Share        │
                    │ Async / GPU / FFI   │
                    └──────────┬──────────┘
                               ↓
                         Verified MIR
                               ↓
                    ┌─────────────────────┐
                    │     OptIR           │
                    │                     │
                    │ SSA                 │
                    │ MemorySSA           │
                    │ Alias              │
                    │ Effects             │
                    │ Escape              │
                    │ Range               │
                    │ Loop                │
                    └──────────┬──────────┘
                               ↓
                         Axiom LIR
                               ↓
                         Machine IR
                               ↓
                      Native machine code
```

Điểm đáng chú ý là **ownership/capability không chỉ tồn tại để làm safety**. Nó trở thành một trong những nguồn thông tin tối ưu hóa mạnh nhất của compiler.

### Nhiệm vụ tiếp theo: BOOTSTRAP-057

**Object representation → ABI lowering → calling convention → register/stack ABI → return-value ABI → aggregate passing → FFI ABI → native object representation.**

Đây sẽ là bước quyết định Axiom có thực sự đi từ:

```text
Verified/Optimized language
```

sang:

```text
PE/COFF
ELF
Mach-O
WASM
```

mà **không cần dựa lâu dài vào LLVM/C compiler** hay không.