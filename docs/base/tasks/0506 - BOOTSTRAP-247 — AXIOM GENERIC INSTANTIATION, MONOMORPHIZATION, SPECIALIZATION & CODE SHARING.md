# BOOTSTRAP-247 — AXIOM GENERIC INSTANTIATION, MONOMORPHIZATION, SPECIALIZATION & CODE SHARING

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là tầng rất quan trọng vì Axiom muốn đồng thời đạt:

- abstraction cấp cao;
- static dispatch;
- tối ưu gần code viết thủ công;
- binary nhỏ;
- compile time hợp lý;
- không tạo hàng loạt bản sao generic không cần thiết.

Nguyên tắc trung tâm:

> **Generic là abstraction ở semantic level; compiler tự quyết định representation và mức độ specialization ở codegen level.**

Và:

> **Monomorphization là một kỹ thuật tối ưu, không phải semantic requirement.**

---

# 1. Generic không phải runtime feature

Ví dụ:

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

`T` tồn tại trong:

```text
source
→ type system
→ trait solver
→ HIR
→ MIR
```

nhưng không nhất thiết tồn tại trong machine code.

---

# 2. Generic instance

Khi có:

```axiom
let x = max(10, 20)
```

compiler tạo logical instance:

```text
max::<i32>
```

Nếu:

```axiom
let a = max(1.0, 2.0)
```

thì:

```text
max::<f64>
```

Hai instance có thể được compile riêng hoặc chia sẻ code tùy optimizer.

---

# 3. Generic instance identity

Một `GenericInstanceId` được xác định bởi semantic arguments:

```text
FunctionId
+
TypeArguments
+
ConstArguments
+
Relevant Capability/ABI parameters
```

Không dùng source text làm identity.

---

# 4. Type arguments

Ví dụ:

```axiom
Vec<i32>
Vec<f32>
Vec<String>
```

là ba semantic instantiations khác nhau.

Compiler interning giúp các instance giống nhau được dùng chung.

---

# 5. Const generic

Ví dụ:

```axiom
fn sum<const N: usize>(a: [N]i32) -> i32
```

có thể tạo:

```text
sum<4>
sum<16>
sum<1024>
```

Const argument là một phần của instance identity.

---

# 6. Generic substitution

Compiler thực hiện:

```text
Generic Function
       ↓
Substitution
       ↓
Concrete Type Environment
       ↓
Typed HIR / MIR
```

Ví dụ:

```text
T → i32
```

---

# 7. Substitution không sửa source AST

AST generic gốc vẫn immutable.

Compiler tạo semantic substitution environment:

```text
GenericEnv {
    T → i32
}
```

Điều này quan trọng cho incremental compilation.

---

# 8. Generic MIR

Có thể tồn tại:

```text
MIR< T >
```

trước khi specialize.

Ví dụ:

```text
%a = parameter<T>
%b = parameter<T>
%cmp = trait_call Ord::gt<T>
```

---

# 9. Trait resolution trước specialization

Với:

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

compiler phải chứng minh:

```text
T: Ord
```

trước khi coi generic body là hợp lệ.

---

# 10. Trait call

Generic MIR có thể chứa:

```text
TraitCall {
    Trait = Ord
    Method = gt
    Self = T
}
```

Sau specialization:

```text
Ord<i32>::gt
```

có thể được resolve thành concrete implementation.

---

# 11. Static dispatch mặc định

Axiom:

```axiom
fn process<T: Trait>(x: T)
```

không tạo dynamic dispatch.

Compiler biết type `T` tại compile time.

---

# 12. Monomorphization

Monomorphization là quá trình:

```text
generic definition
      ↓
concrete instance
      ↓
specialized MIR
```

Ví dụ:

```text
max<T>
 ↓
max<i32>
```

---

# 13. Nhưng monomorphization không bắt buộc

Compiler có thể giữ generic code dùng chung nếu specialization không mang lại lợi ích đủ lớn.

Do đó:

```text
Generic
   ├── specialized instance
   └── shared implementation
```

có thể cùng tồn tại.

---

# 14. Code sharing

Ví dụ:

```text
Vec<i32>::push
Vec<u32>::push
Vec<f32>::push
```

nếu machine representation và behavior tương thích, compiler có thể chia sẻ implementation.

---

# 15. Representation-equivalent sharing

Hai generic instances có thể share code nếu:

```text
machine representation compatible
+
calling convention compatible
+
semantic behavior equivalent
+
optimization assumptions compatible
```

---

# 16. Không share nếu semantics khác

Ví dụ:

```text
Vec<i32>
Vec<String>
```

không thể tùy tiện share code nếu lifecycle/drop/layout semantics khác nhau.

---

# 17. Type erasure nội bộ

Compiler có thể dùng internal representation:

```text
Generic Parameter
       ↓
Machine Representation Class
```

Ví dụ:

```text
Scalar32
Scalar64
PointerLike
Aggregate
```

nhưng đây chỉ là backend optimization.

Không biến Axiom type system thành runtime erased type system.

---

# 18. Generic semantic identity vẫn giữ nguyên

Dù backend share code:

```text
Foo<i32>
Foo<u32>
```

vẫn là hai semantic instances.

Code sharing không làm chúng thành cùng type.

---

# 19. Generic function cloning

Compiler có thể tạo:

```text
max::<i32>$specialized
max::<f64>$specialized
```

nhưng chỉ khi cần.

---

# 20. Specialization levels

Axiom nên có các mức:

```text
Level 0 — Generic shared
Level 1 — Representation specialized
Level 2 — Type specialized
Level 3 — Constant specialized
Level 4 — Profile-guided specialized
```

---

# 21. Generic shared implementation

Ví dụ compiler nhận thấy:

```text
T chỉ được dùng như opaque value
```

và không có type-specific optimization cần thiết.

Compiler có thể giữ một implementation dùng chung.

---

# 22. Representation specialization

Nếu:

```text
T = i32
U = u32
```

có cùng representation/ABI và semantic operation phù hợp, compiler có thể chia sẻ một số machine code.

---

# 23. Type specialization

Nếu:

```text
T = String
```

cần Drop/layout/trait behavior riêng:

→ tạo specialization riêng.

---

# 24. Constant specialization

Ví dụ:

```axiom
fn fill<const N: usize>(x: i32) -> [N]i32
```

với:

```text
N = 4
```

compiler có thể unroll hoàn toàn.

---

# 25. Generic specialization không được thay đổi semantics

Ví dụ:

```text
generic implementation
```

và:

```text
specialized implementation
```

phải có observable behavior tương đương.

---

# 26. Specialization legality

Một specialization chỉ được tạo nếu compiler có proof:

```text
same observable semantics
+
same ownership semantics
+
same capability semantics
+
same effect contract
+
same ABI contract
```

---

# 27. No arbitrary user specialization v1

Không cho programmer viết unrestricted:

```text
impl<T> Foo<T>
impl Foo<i32>
```

nếu hai implementation có thể overlap không kiểm soát.

Coherence rules từ BOOTSTRAP-240 vẫn áp dụng.

---

# 28. Compiler specialization khác semantic specialization

Compiler có thể tự specialize:

```text
generic implementation
```

mà không tạo thêm language semantics.

Đây là distinction rất quan trọng.

---

# 29. Specialization driven by optimizer

Ví dụ:

```axiom
fn dot<T: Numeric>(a: view<T>, b: view<T>) -> T
```

Với `T=f32`, optimizer có thể phát hiện:

```text
SIMD available
```

và tạo specialized implementation.

---

# 30. Generic + SIMD

Compiler có thể transform:

```text
scalar generic
```

thành:

```text
SIMD specialized
```

nếu semantics cho phép.

Không cần programmer tạo một generic type khác.

---

# 31. Generic + GPU

Một generic kernel:

```axiom
@kernel
fn add<T: Numeric>(...)
```

có thể specialize theo:

```text
T
target GPU
address space
layout
vector width
```

nhưng GPU legality phải được kiểm tra trước codegen.

---

# 32. Generic + target features

Một generic function có thể có variants:

```text
generic baseline
AVX2
AVX-512
NEON
SVE
```

Compiler có thể chọn multiversioning nếu target/runtime contract cho phép.

---

# 33. Target specialization không phải type specialization

Ví dụ:

```text
foo<i32>@x86
foo<i32>@arm64
```

khác target artifact nhưng cùng semantic generic instance.

Artifact identity vẫn chứa TargetSpec.

---

# 34. Generic dependency graph

Compiler xây:

```text
GenericInstantiationGraph
```

Ví dụ:

```text
main
 └── foo<i32>
      └── Vec<i32>::push
           └── allocate<T>
```

---

# 35. Reachability

Chỉ generic instances reachable từ production roots mới cần codegen.

```text
Source declarations
        ↓
semantic reachability
        ↓
instantiation graph
        ↓
codegen roots
```

---

# 36. Dead generic elimination

Nếu:

```text
fn unused<T>() { ... }
```

không có instance reachable:

→ không tạo machine code.

---

# 37. Generic declarations need not generate code

Đây là một lợi thế lớn so với mô hình compile đơn giản kiểu textual expansion.

Generic definition có thể chỉ tồn tại trong metadata cho đến khi được instantiate.

---

# 38. Incremental generic compilation

`GenericInstanceId` được cache.

Nếu:

```text
foo<i32>
```

không thay đổi semantic dependencies:

→ reuse compiled artifact.

---

# 39. Generic fingerprint

Một instance fingerprint nên chứa:

```text
Generic definition semantic fingerprint
+
type arguments
+
const arguments
+
trait resolution
+
relevant target facts
+
ABI
+
optimization contract
```

---

# 40. Không fingerprint bằng source text בלבד

Whitespace/comment thay đổi không được invalidate machine code.

---

# 41. Trait solver integration

Instantiation:

```text
foo<T: Trait>
```

phải lưu trait obligations:

```text
T: Trait
AssociatedType(T)
ConstConstraint
```

---

# 42. Associated type normalization

Ví dụ:

```axiom
fn first<I: Iterator>(x: I) -> I.Item
```

Khi:

```text
I = VecIter<i32>
```

compiler resolve:

```text
I.Item → i32
```

trước ABI lowering.

---

# 43. Generic projection cache

Các phép:

```text
<T as Trait>::Item
```

được normalize và cache.

Điều này tránh trait solver chạy lại liên tục.

---

# 44. Generic recursion

Ví dụ:

```text
foo<T>
 └── foo<Vec<T>>
```

có thể tạo infinite instantiation.

Compiler phải phát hiện growth/recursion.

---

# 45. Recursive generic instantiation

Rules:

```text
finite instantiation required
```

Nếu compiler không chứng minh được finite expansion:

→ diagnostic.

---

# 46. Generic recursion through traits

Trait solver và instantiation engine phải có recursion limits riêng.

Ví dụ:

```text
T → Wrapper<T> → Wrapper<Wrapper<T>> ...
```

không được vô hạn silently.

---

# 47. Generic depth limit

Compiler có configurable resource limit:

```text
max_generic_depth
max_trait_depth
max_instance_count
```

Overflow không biến thành incorrect program.

---

# 48. Error category

Phân biệt:

```text
TRAIT_OVERFLOW
GENERIC_INSTANTIATION_OVERFLOW
GENERIC_RECURSION
RESOURCE_LIMIT
```

---

# 49. Generic ABI

Generic internal ABI có thể thay đổi.

Stable ABI không được phụ thuộc vào:

```text
compiler-private generic layout
```

---

# 50. Public generic API

Một package có thể expose:

```axiom
pub fn sort<T: Ord>(...)
```

nhưng binary ABI của generic chưa phải stable ABI.

Consumer compiler có thể instantiate theo version-compatible metadata.

---

# 51. Binary generic metadata

`.axlib` nên chứa:

```text
generic definitions
trait requirements
layout metadata
semantic fingerprints
codegen summaries
```

đủ để compiler instantiate khi cần.

---

# 52. Precompiled generic instance

Package có thể cung cấp:

```text
foo<i32>
```

đã codegen.

Compiler có thể reuse nếu fingerprint tương thích.

---

# 53. Generic artifact cache

Cache key:

```text
PackageSemanticFingerprint
+
GenericInstanceFingerprint
+
TargetSpec
+
ABI
+
CompilerSemanticVersion
+
CodegenProfile
```

---

# 54. ABI-independent generic cache

Không được reuse machine code giữa ABI không tương thích.

Ví dụ:

```text
Windows x64
Linux x64
```

semantic generic instance có thể giống nhau nhưng native artifact không thể mặc định dùng chung.

---

# 55. Cross-target generic reuse

Có thể reuse:

```text
semantic MIR
typed HIR
generic analysis
```

nhưng không nhất thiết reuse machine code.

---

# 56. Generic analysis cache layers

Nên chia:

```text
Layer 1 — Generic semantic analysis
Layer 2 — Instantiation
Layer 3 — Target-independent optimization
Layer 4 — Target-specific optimization
Layer 5 — Machine code
```

---

# 57. Compile-time cost control

Monomorphization quá mức có thể làm compile chậm.

Compiler phải có heuristic dựa trên:

```text
instance count
body size
call frequency
optimization benefit
code size
compile cost
```

---

# 58. Size profile

Với:

```text
--profile size
```

compiler ưu tiên:

```text
code sharing
outline cold code
avoid unnecessary specialization
dead stripping
ICF
LTO
```

---

# 59. Speed profile

Với:

```text
--profile release
```

compiler có thể ưu tiên:

```text
specialization
inlining
vectorization
constant propagation
```

miễn binary-size tradeoff được profile cho phép.

---

# 60. Balanced default

Default profile nên cân bằng:

```text
performance
compile time
binary size
```

Không nên luôn specialize tối đa.

---

# 61. Hot/cold specialization

PGO có thể cho biết:

```text
foo<i32>
```

hot.

Compiler có thể specialize instance đó, trong khi instance hiếm dùng giữ shared implementation.

---

# 62. Cold generic code

Cold path có thể được outline/shared để giảm binary size.

---

# 63. Generic + exceptions

Axiom không có exception machinery Core, nên generic code không cần mang hidden exception tables chỉ vì generic.

Panic/unwind chỉ xuất hiện nếu profile yêu cầu.

---

# 64. Generic + Drop

Ví dụ:

```axiom
fn consume<T>(x: T) {
    ...
}
```

Nếu `T` có Drop:

compiler phải instantiate/drop-elaborate đúng semantics.

Nếu `T` trivially disposable:

Drop có thể disappear.

---

# 65. Generic + ownership

Generic code phải được kiểm tra ownership symbolically:

```text
T: Copy
T: Drop
T: Send
T: Share
```

được solver xác định.

---

# 66. Generic + capability

Ví dụ:

```axiom
fn read<T>(x: view<T>)
```

`view<T>` vẫn là capability type.

Generic substitution không làm mất provenance.

---

# 67. Generic mutable view

```axiom
fn modify<T>(x: mut_view<T>)
```

specialization không được biến mutable capability thành duplicable capability.

---

# 68. Generic alias analysis

Ví dụ:

```axiom
fn copy<T>(src: view<T>, dst: mut_view<T>)
```

compiler cần biết alias relation.

Nếu không chứng minh disjoint:

→ generic implementation không được giả định `NO_ALIAS`.

---

# 69. Generic + internal NoAlias

Khi caller cung cấp verified disjoint capabilities:

```text
view(src)
mut_view(dst)
```

compiler có thể truyền AliasInfo:

```text
NO_ALIAS
```

vào specialized MIR.

---

# 70. Generic + optimizer assumptions

Generic optimizer facts phải có provenance:

```text
Fact {
    source
    proof
    scope
}
```

Không được biến heuristic thành semantic fact.

---

# 71. Generic specialization and verification

Flow:

```text
Generic MIR
   ↓
Instantiation
   ↓
Substitution
   ↓
Trait normalization
   ↓
Ownership/capability verification
   ↓
Verified Instance MIR
   ↓
Optimization
```

Không được optimize trước khi instance được verified.

---

# 72. Generic + comptime

Const/comptime có thể giúp specialization:

```axiom
const N: usize = 16
```

compiler biết N tại compile time.

Nhưng comptime evaluation phải tuân theo sandbox/capability model.

---

# 73. Generic compile-time computation

Ví dụ:

```axiom
comptime fn make_table<const N: usize>() -> [N]u32
```

có thể materialize:

```text
constant data
```

mà không tạo runtime computation.

---

# 74. Generic metadata

Compiler metadata nên phân biệt:

```text
semantic generic declaration
instantiated semantic facts
optimized code artifact
machine artifact
```

---

# 75. Avoid textual template model

Axiom generic **không phải C preprocessor**.

Không có:

```text
copy source
replace T
parse again
```

thay vào đó:

```text
typed semantic substitution
```

---

# 76. Generic diagnostics

Nếu:

```axiom
max(file_a, file_b)
```

và `File` không implement `Ord`:

diagnostic nên giải thích:

```text
cannot instantiate max<File>

required:
    File: Ord

reason:
    max requires T: Ord
```

---

# 77. AI Explain API

```text
ax explain generic max<File>
```

có thể trả:

```text
Instantiation:
    max<T>

T:
    File

Unresolved obligation:
    File: Ord

No implementation found.
```

---

# 78. Generic ambiguity

Nếu nhiều trait impl candidates:

```text
Candidate A
Candidate B
```

solver trả:

```text
Ambiguous
```

không chọn dựa trên source order.

---

# 79. Generic and coherence

Instantiation không được tạo ra implementation mới.

Nó chỉ chọn implementation hợp lệ đã tồn tại theo coherence rules.

---

# 80. Specialization and coherence

Compiler optimization specialization không thay đổi trait coherence.

Ví dụ optimizer tạo:

```text
fast Foo<i32>
```

không có nghĩa source program có thêm:

```text
impl Trait for i32
```

---

# 81. Generic vtable

Generic static dispatch không cần vtable.

Dynamic `dyn Trait` mới cần runtime dispatch representation.

---

# 82. Generic + dyn

Có thể:

```axiom
fn process<T: Trait>(x: T)
```

và:

```axiom
fn process_dyn(x: dyn Trait)
```

Hai cơ chế khác nhau.

Không tự động chuyển generic thành dyn.

---

# 83. Devirtualization

Nếu generic code receives:

```text
dyn Trait
```

nhưng compiler chứng minh concrete dynamic target:

→ devirtualization có thể xảy ra.

Nhưng semantic dispatch vẫn là dynamic.

---

# 84. Generic inline

Inlining generic function là optimization phổ biến:

```text
caller
 ↓
foo<T>
 ↓
inline
```

sau đó generic abstraction biến mất.

---

# 85. Inline không bắt buộc

Không inline nếu:

```text
code size cost
compile time
recursion
ABI boundary
debug policy
```

không phù hợp.

---

# 86. Generic code sharing after inlining

Compiler có thể:

```text
specialize hot caller
share cold helper
```

thay vì một chiến lược duy nhất.

---

# 87. Identical Code Folding

Nếu hai instantiated functions có machine code tương đương và identity không observable:

```text
foo<i32>
bar<u32>
```

có thể ICF.

Không được merge nếu function address identity là observable.

---

# 88. Function pointer identity

Nếu programmer lấy:

```axiom
address_of_function(foo)
```

hoặc tương đương system-level API, compiler phải tôn trọng ABI/identity contract.

ICF chỉ được áp dụng nếu semantics cho phép.

---

# 89. Generic function address

Concrete generic instance có function identity riêng về semantic model, nhưng physical address có thể được shared nếu address identity không được yêu cầu.

---

# 90. Generic data

Generic static data:

```axiom
static<T> VALUE
```

nếu được hỗ trợ ở library/system layer phải có instance identity và storage semantics rõ ràng.

---

# 91. Generic associated constants

Compiler có thể materialize:

```text
Trait<T>::CONST
```

thành immediate hoặc constant data.

---

# 92. Generic layout

`size_of<T>()` có thể là compile-time value khi T known.

Compiler có thể specialize layout-dependent code.

---

# 93. Generic layout opacity

Nếu T chưa known:

```text
size_of<T>
align_of<T>
```

là generic facts.

Không giả định layout cụ thể.

---

# 94. Generic ABI lowering

ABI classification xảy ra **sau specialization** khi đủ information.

```text
Generic MIR
 ↓
Instantiation
 ↓
Layout
 ↓
ABI classification
 ↓
ABI MIR
```

---

# 95. Generic + FFI

Không được expose generic ABI trực tiếp qua:

```text
extern "C"
```

nếu representation chưa explicit.

Wrapper concrete:

```axiom
extern "C" fn max_i32(...)
```

có thể ổn định.

---

# 96. Generic + serialization

`@derive(Serialize)` trên generic type tạo implementation theo generic constraints.

Generated code re-enters:

```text
type
ownership
capability
effect
ABI
```

verification.

---

# 97. Generic + GPU

GPU generic instance fingerprint phải bao gồm:

```text
GPU target
shader profile
address-space assumptions
layout
supported features
```

---

# 98. Generic + async

Async generic:

```axiom
async fn fetch<T: Decoder>(...) -> Result<T>
```

Future instance phụ thuộc:

```text
T
Decoder
state layout
Send requirements
```

State machine được specialize sau semantic verification.

---

# 99. Generic + closure

```axiom
fn apply<F: Fn(i32) -> i32>(f: F)
```

closure type là generic argument.

Compiler có thể:

```text
instantiate F
→ inline closure
→ eliminate environment
```

để đạt zero-cost abstraction.

---

# 100. Generic + iterator

Đây là trường hợp quan trọng:

```axiom
xs.iter()
   .map(...)
   .filter(...)
   .collect()
```

Có thể tạo nhiều generic types.

Compiler không nhất thiết tạo machine function cho từng adapter.

LTO/inlining/fusion có thể biến cả pipeline thành một loop.

---

# 101. Iterator fusion

Generic abstraction:

```text
map
filter
fold
```

có thể compile thành:

```text
single loop
```

không allocation trung gian.

---

# 102. Generic recursion + inlining

Compiler phải có recursion budget để tránh compile explosion.

---

# 103. Generic instance explosion

Nếu một generic được dùng với:

```text
1000 types
```

không được mặc định tạo 1000 machine implementations.

Compiler phải áp dụng sharing heuristic.

---

# 104. Instantiation policy

Đề xuất:

```text
1. Semantic instance luôn tồn tại khi được yêu cầu.
2. Machine instance chỉ tạo khi codegen cần.
3. Codegen quyết định specialize/share.
4. Dead instances bị loại bỏ.
```

Đây là distinction rất quan trọng.

---

# 105. Lazy instantiation

Generic semantic instance nên được tạo lazy:

```text
declaration
   ↓
reference discovered
   ↓
instantiate
```

Không compile toàn bộ generic universe.

---

# 106. Parallel instantiation

Các instance độc lập có thể compile song song:

```text
foo<i32> ─┐
foo<f32> ─┼→ parallel
foo<u64> ─┘
```

CompilerDB đảm bảo deterministic result.

---

# 107. Deterministic instance identity

Parallel order không được ảnh hưởng:

```text
GenericInstanceId
diagnostic
symbol mangling
artifact fingerprint
```

---

# 108. Generic symbol mangling

Internal symbol:

```text
_ZN...foo$T_i32
```

chỉ là implementation detail.

Mangle phải deterministic.

Stable ABI dùng explicit exported symbol contract.

---

# 109. Generic cache invalidation

Nếu thay đổi:

```text
trait implementation
```

có thể invalidate tất cả generic instances phụ thuộc vào implementation đó.

Compiler dependency graph phải track dependency chính xác.

---

# 110. Fine-grained invalidation

Không invalidate toàn package nếu chỉ:

```text
foo<T>
```

thay đổi.

Chỉ các instances phụ thuộc trực tiếp/gián tiếp mới bị invalidated.

---

# 111. Generic semantic fingerprint

Nên track:

```text
definition fingerprint
trait obligations
associated type normalization
const evaluation
representation requirements
effects
ownership-relevant facts
```

---

# 112. Optimization fingerprint

Semantic fingerprint và codegen fingerprint tách biệt:

```text
SemanticFingerprint
CodegenFingerprint
```

Đúng với kiến trúc Axiom trước đó.

---

# 113. Debug generic instances

Debugger phải có thể hiển thị:

```text
foo<T>
T = MyType
```

và map machine instruction về:

```text
generic source
+
concrete instance
```

---

# 114. Error source mapping

Diagnostic:

```text
error in max<File>
```

phải link về:

```text
generic definition
call site
concrete substitution
```

---

# 115. Generic compile failure isolation

Nếu:

```text
foo<i32> ✓
foo<String> ✗
```

thì failure của `String` không làm semantic instance `i32` sai.

Build system có thể cache/reuse valid instance tùy dependency state.

---

# 116. Generic and build reproducibility

Instance generation order không được ảnh hưởng artifact.

---

# 117. Generic and deterministic codegen

Nếu tất cả inputs giống nhau:

```text
same source
same dependency
same target
same compiler semantics
same profile
same PGO
```

thì semantic artifact phải reproducible.

Machine binary reproducibility là mục tiêu khi toolchain/backend hỗ trợ deterministic output.

---

# 118. Generic optimization legality

Mỗi transform phải khai báo:

```text
Preconditions
Transformation
Preserved invariants
New facts
Validation
```

đúng BOOTSTRAP-107/188.

---

# 119. Generic translation validation

Ví dụ:

```text
generic implementation
```

→

```text
specialized implementation
```

compiler có thể dùng translation validation để kiểm tra transformation trong pipeline thích hợp.

---

# 120. Không biến specialization thành semantic fork

Đây là invariant rất quan trọng:

```text
One source semantics
       ↓
many possible implementations
```

không phải:

```text
one source
 ↓
different semantics per optimization
```

---

# 121. Generic runtime overhead

Static generic:

```text
fn apply<T>(...)
```

không có runtime type lookup mặc định.

Không:

```text
type id
reflection
vtable
boxing
```

nếu source semantics không yêu cầu.

---

# 122. Generic dynamic escape

Nếu programmer yêu cầu:

```text
dyn Trait
```

thì dynamic representation trở thành explicit semantic boundary.

---

# 123. Generic binary size strategy

Axiom compiler nên có ba chiến lược:

```text
Speed:
    specialize aggressively

Balanced:
    selective specialization + sharing

Size:
    maximize sharing + dead stripping
```

---

# 124. Profile không thay đổi language semantics

Ba profile trên chỉ thay đổi:

```text
implementation strategy
```

không thay đổi observable semantics.

---

# 125. Compiler flags

Có thể hỗ trợ:

```text
-generic-sharing
-generic-specialize
-generic-max-instances
```

nhưng đây là compiler tuning, không phải Core language feature.

---

# 126. User hints

Sau này có thể có optimization hints như:

```text
@inline
@noinline
@cold
@hot
```

nhưng chúng chỉ là optimization guidance.

Không được biến thành semantic requirement nếu không có explicit contract.

---

# 127. No user-written specialization syntax in Core v1

Điều này giữ type system/coherence đơn giản hơn.

Compiler đủ mạnh để tự làm specialization.

---

# 128. Generic implementation pipeline

Chuẩn:

```text
Generic Source
      ↓
Generic HIR
      ↓
Generic Typed HIR
      ↓
Generic MIR
      ↓
Instantiation Request
      ↓
Substitution
      ↓
Trait Normalization
      ↓
Concrete MIR
      ↓
Ownership/Capability Verification
      ↓
Verified MIR
      ↓
Specialization Decision
      ↓
OptIR
      ↓
Code Sharing / Cloning
      ↓
ABI Lowering
      ↓
Machine Code
```

---

# 129. Generic instance manager

CompilerDB nên có:

```text
GenericInstanceDB
```

quản lý:

```text
InstanceKey
InstanceState
Dependencies
TraitSolutions
LayoutFacts
CodegenDecision
Artifact
Fingerprint
```

---

# 130. Instance states

Đề xuất:

```text
Declared
Requested
Substituted
Normalized
Typed
Verified
Optimizing
Codegen
Emitted
Cached
Failed
```

---

# 131. No partial invalid instance enters codegen

Chỉ:

```text
Verified
```

mới được codegen.

---

# 132. Generic dependency cycle

Graph cycle hợp lệ nếu runtime recursion là function recursion:

```text
foo → bar → foo
```

nhưng **type/instance expansion** vô hạn phải bị chặn.

Phân biệt:

```text
call recursion
```

với:

```text
type instantiation recursion
```

---

# 133. Generic type recursion

Recursive data structures cần finite indirection/storage representation.

Ví dụ library:

```text
Box<Node>
```

cho phép:

```text
Node {
    next: Option<Box<Node>>
}
```

không phải infinite-size direct embedding.

---

# 134. Generic zero-cost principle

Một abstraction được coi là zero-cost nếu compiler có thể loại bỏ abstraction machinery và giữ lại implementation cần thiết.

Không có nghĩa mọi generic luôn zero instruction overhead.

---

# 135. Generic and optimization boundary

Semantic MIR:

```text
what program means
```

OptIR:

```text
how compiler chooses to implement it
```

Generic specialization thuộc về boundary này.

---

# 136. Generic and alias facts

Specialized generic instance có thể nhận thêm facts:

```text
T = i32
```

nhưng chỉ facts được chứng minh mới được đưa vào AliasInfo.

---

# 137. Generic and range analysis

Ví dụ:

```axiom
fn get<const N: usize>(a: [N]i32, i: usize)
```

với constant `N`:

compiler có thể prove bounds.

---

# 138. Generic and bounds-check elimination

Nếu:

```text
i < N
```

được proven:

→ bounds check có thể eliminate.

Nếu không:

→ giữ check.

Không suy luận dựa trên assumption.

---

# 139. Generic and vectorization

Concrete type/shape có thể unlock vectorization.

Compiler có thể specialize:

```text
map<T>
```

thành SIMD implementation khi legal.

---

# 140. Generic and binary compression

Binary-size profile có thể:

```text
share generic helpers
merge constants
ICF
section GC
outline cold paths
```

sau khi specialization.

---

# 141. Generic and LTO

LTO có quyền nhìn qua package/module boundary nếu ABI contract cho phép.

Điều này đặc biệt hữu ích với:

```text
generic → closure → iterator
```

pipeline.

---

# 142. Generic + closure + iterator

Ví dụ:

```axiom
let result =
    numbers
        .iter()
        .map(|x| x * 2)
        .filter(|x| *x > 10)
        .collect()
```

Semantic layers rất cao.

Machine output có thể chỉ còn:

```text
load
multiply
compare
branch
store
```

và một allocation cuối cho result.

---

# 143. No mandatory intermediate objects

Generic adapters không yêu cầu runtime object allocation.

---

# 144. Generic abstraction transparency

Debugger/tooling vẫn phải cho programmer thấy abstraction source-level, dù machine representation đã bị collapse.

---

# 145. Explain generic codegen

`ax explain` có thể trả:

```text
foo<Vec<i32>>

Instantiation:
    concrete

Specialization:
    enabled

Reason:
    hot call site
    T representation known
    vectorization available

Environment:
    no dynamic dispatch
    no heap allocation introduced
```

---

# 146. Compiler should explain sharing

Ví dụ:

```text
foo<i32>
foo<u32>
```

→

```text
shared machine implementation

Reason:
    ABI-equivalent representation
    no type-specific Drop
    no specialization benefit
```

---

# 147. Compiler should explain non-sharing

```text
foo<String>
```

→

```text
separate implementation

Reason:
    Drop semantics
    layout-dependent operations
```

---

# 148. AI-friendly generic context

`ax context` nên có:

```text
Generic definition
Current substitutions
Trait obligations
Normalized associated types
Ownership facts
Capability facts
Instantiation graph
Specialization decision
Codegen status
```

AI không phải đoán compiler state từ source.

---

# 149. Generic source remains canonical

Không generate source code cho mỗi instance.

Instances là semantic/compiler objects.

---

# 150. Generic generated code

Comptime/derive có thể generate declarations, nhưng generated declarations quay lại:

```text
Resolver
TypeChecker
TraitSolver
Verifier
```

trước instantiation.

---

# 151. Generic security

Compiler không được coi generic metadata từ package là trusted semantic truth.

`.axmeta/.axlib` phải được validate.

---

# 152. Generic binary compatibility

Generic machine artifacts chỉ reuse khi:

```text
semantic fingerprint compatible
ABI compatible
target compatible
codegen assumptions compatible
```

---

# 153. Compiler version

Semantic compiler version thay đổi có thể invalidate generic artifact nếu semantics thay đổi.

Codegen-only version change có thể chỉ invalidate machine artifact.

---

# 154. Generic cache hierarchy

```text
Source
 ↓
Generic Semantic Cache
 ↓
Instantiation Cache
 ↓
Verified MIR Cache
 ↓
OptIR Cache
 ↓
Machine Artifact Cache
```

---

# 155. Failure caching

Nếu một generic instance thất bại vì:

```text
T: Trait
```

không thỏa:

compiler có thể cache failure theo fingerprint.

---

# 156. Resource limit caching

Resource-limit failure cần phân biệt với semantic invalidity.

Không nên cache như “program invalid” nếu chỉ compiler budget quá thấp.

---

# 157. Generic diagnostics stability

Diagnostic IDs:

```text
EGENERIC001
EGENERIC002
...
```

nên ổn định.

---

# 158. Generic test matrix

Conformance tests cần cover:

```text
primitive
struct
enum
generic struct
nested generic
const generic
trait generic
associated type
closure generic
iterator generic
async generic
GPU generic
FFI wrapper
```

---

# 159. Adversarial tests

Đặc biệt:

```text
generic recursion
trait recursion
instance explosion
overlapping impl
ambiguous impl
partial move
Drop
Send/Share
view escape
mutable alias
const evaluation
```

---

# 160. Generic correctness oracle

Reference interpreter có thể execute concrete instances.

Semantic equivalence:

```text
Generic Interpreter
        vs
Specialized Native
```

phải giữ observable behavior.

---

# 161. Generic + unsafe

Unsafe generic:

```axiom
fn load<T>(p: *const T) -> T
```

không được tự động coi mọi T valid.

Representation/alignment/initialization requirements vẫn phải được establish.

---

# 162. Generic + FFI contract

Generic FFI wrappers cần concrete FfiSafe constraints khi crossing boundary.

---

# 163. Generic + resource types

Ví dụ:

```axiom
fn close<T: Close>(x: T)
```

trait abstraction không làm mất Drop/resource semantics.

---

# 164. Generic + synchronization

```axiom
fn spawn_with<T: Send>(x: T)
```

Send obligation được trait solver/derived-property system xác minh.

---

# 165. Generic + Share

`T: Share` không đồng nghĩa:

```text
T mutable
```

như semantics đã frozen.

---

# 166. Generic + atomic

`Atomic<T>` vẫn là distinct semantic type.

Generic algorithms không được coi atomic load/store như ordinary load/store.

---

# 167. Generic + volatile

Volatile operations giữ effect semantics.

Optimizer không được eliminate chỉ vì generic code trông “unused”.

---

# 168. Generic + external effects

Generic function gọi:

```text
File
Socket
Process
```

vẫn mang effect contract tương ứng.

Specialization không được xóa effect observable.

---

# 169. Generic + panic

Nếu generic operation có defined panic conditions, specialization phải preserve chúng.

---

# 170. Generic + numeric overflow

`T: Numeric` không cho phép optimizer tự đổi:

```text
checked
```

thành:

```text
wrapping
```

chỉ để vectorize.

---

# 171. Fast-math

Nếu generic numeric algorithm được compile dưới explicit fast-math profile/contract, đó là một semantic/optimization boundary đã được khai báo.

Không tự áp dụng.

---

# 172. Generic + deterministic FP

Strict FP generic code phải preserve required numerical semantics.

---

# 173. Generic + parallel algorithms

Generic parallel iterator/algorithm phải explicit.

Compiler không tự biến:

```text
fold
```

thành unordered parallel reduction nếu điều đó thay đổi observable FP semantics.

---

# 174. Generic + distributed

Distributed serialization/transport remains explicit.

`T: Send` không có nghĩa `T: Serializable`.

---

# 175. Generic + serialization

Có thể yêu cầu:

```text
T: Serialize
```

độc lập với:

```text
T: Send
```

---

# 176. Generic + persistence

Persistent representation không phụ thuộc memory representation trừ khi explicitly declared.

---

# 177. Generic + GUI

Widget generics không yêu cầu class/object runtime.

Compiler specialization có thể erase generic UI abstraction.

---

# 178. Generic + rendering

Generic render pipelines có thể specialize theo:

```text
VertexType
IndexType
ShaderType
Backend
```

nhưng backend ABI remains explicit.

---

# 179. Generic + AI/Tensor

Tensor generic:

```text
Tensor<T, Shape, Layout>
```

có thể compile-time specialize:

```text
dtype
shape
layout
device
```

và generate efficient kernels.

---

# 180. Generic + AD

AD transformation có thể tạo generic derivative instances:

```text
f<T>
 ↓
grad(f)<T>
```

generated code re-enters verifier.

---

# 181. Generic + scientific computing

Units:

```text
Quantity<f64, Meter>
Quantity<f64, Second>
```

có thể erase unit type tại runtime nếu không cần representation.

---

# 182. Generic type erasure

Nếu unit marker chỉ tồn tại compile time:

```text
Meter
Second
```

có thể zero-size.

---

# 183. Generic ZST

Zero-sized generic parameters không bắt buộc chiếm runtime storage.

---

# 184. Generic phantom state

Type-level state:

```text
Socket<Connected>
Socket<Closed>
```

có thể erase marker nếu không runtime-observable.

---

# 185. Generic state machine

Compiler có thể optimize type-state abstractions thành ordinary machine code.

---

# 186. Generic and object identity

Type-level generic parameters không tự tạo runtime object identity.

---

# 187. Generic layout contracts

Chỉ explicit:

```text
@repr(C)
@repr(transparent)
```

hoặc equivalent ABI contract mới expose layout.

---

# 188. Generic stable ABI

Stable ABI generic types phải có explicit representation strategy.

Nếu không:

```text
opaque ABI
```

hoặc concrete exported wrappers.

---

# 189. Generic compiler API

CompilerDB nên expose:

```text
instantiate(FunctionId, GenericArguments)
resolve_instance(GenericInstanceId)
get_instance_fingerprint(...)
get_specialization_plan(...)
get_codegen_status(...)
```

---

# 190. Generic specialization plan

Một object:

```text
SpecializationPlan {
    mode: Shared | Specialized | Hybrid
    reasons
    assumptions
    dependencies
}
```

---

# 191. Hybrid codegen

Đây là chiến lược mặc định nên hướng tới:

```text
                    Generic
                       │
              ┌────────┴────────┐
              ▼                 ▼
          Shared body      Specialized hot body
              │                 │
              └────────┬────────┘
                       ▼
                 Final binary
```

---

# 192. Why hybrid?

Vì hai mục tiêu:

```text
C/C++-class performance
```

và:

```text
small binary
```

thường xung đột nếu luôn monomorphize.

Hybrid cho compiler quyền lựa chọn.

---

# 193. Generic code-size estimator

Compiler có thể ước lượng:

```text
estimated instruction count
estimated register pressure
estimated code size
estimated compile cost
```

trước khi clone.

---

# 194. Specialization benefit score

Không expose như user-facing “score”; chỉ là compiler-internal decision metric.

Các yếu tố:

```text
constant propagation
branch elimination
vectorization
inlining
devirtualization
layout knowledge
```

---

# 195. Avoid user-facing ranking

Compiler không cần nói:

```text
specialization score = 87
```

mà nên explain bằng facts:

```text
specialized because:
- constant N known
- branch eliminated
- vectorization enabled
```

---

# 196. Generic and compile-time explosion

Compiler có thể giới hạn:

```text
instance count
instantiation depth
MIR size
specialization clones
```

để bảo vệ tài nguyên.

---

# 197. Explicit override

Core v1 không cần:

```text
@always_specialize
```

Nếu sau này cần, đây là optimization hint chứ không semantic mechanism.

---

# 198. Generic optimization does not bypass verifier

Pipeline bắt buộc:

```text
Instantiate
→ Verify
→ Optimize
```

không:

```text
Instantiate
→ Optimize
→ Hope verifier accepts
```

---

# 199. Generic semantics and machine semantics

Formal boundary:

```text
Generic Source
      ↓
Semantic Generic IR
      ↓
Concrete Verified MIR
```

Từ đây mọi specialization phải preserve verified semantics.

---

# 200. FROZEN INVARIANTS

```text
AGENERIC-20
Generic parameters are compile-time semantic parameters.

AGENERIC-21
Generic types do not imply runtime type information.

AGENERIC-22
Generic functions do not imply runtime dispatch.

AGENERIC-23
Static generic dispatch is the default.

AGENERIC-24
Generic instance identity is determined by semantic arguments.

AGENERIC-25
Type and const arguments participate in generic instance identity.

AGENERIC-26
Generic substitution is semantic substitution, not textual source rewriting.

AGENERIC-27
Generic source definitions remain immutable after instantiation.

AGENERIC-28
Generic MIR may exist before concrete instantiation.

AGENERIC-29
Trait obligations must be resolved according to the trait solver contract.

AGENERIC-30
Generic instances are instantiated lazily when required.

AGENERIC-31
Unreachable generic instances need not produce machine code.

AGENERIC-32
Monomorphization is an implementation strategy, not a semantic requirement.

AGENERIC-33
The compiler may retain shared generic implementations.

AGENERIC-34
The compiler may specialize generic implementations.

AGENERIC-35
The compiler may use hybrid specialization and code sharing.

AGENERIC-36
Specialization must preserve observable semantics.

AGENERIC-37
Specialization must preserve ownership semantics.

AGENERIC-38
Specialization must preserve capability semantics.

AGENERIC-39
Specialization must preserve effect semantics.

AGENERIC-40
Specialization must preserve ABI obligations where ABI is exposed.

AGENERIC-41
Representation-equivalent generic instances may share machine code when semantic conditions permit.

AGENERIC-42
Semantic type identity is never erased merely because machine code is shared.

AGENERIC-43
Code sharing is not semantic type unification.

AGENERIC-44
Type-specific Drop behavior prevents unsafe code sharing.

AGENERIC-45
Representation sharing requires compatible machine representation.

AGENERIC-46
Calling convention compatibility is required for callable code sharing.

AGENERIC-47
Observable function identity restricts identical-code folding.

AGENERIC-48
Generic function addresses are subject to the relevant identity and ABI contract.

AGENERIC-49
Generic specialization does not create new source-level trait implementations.

AGENERIC-50
Compiler specialization does not modify trait coherence.

AGENERIC-51
Unrestricted user specialization is not part of Core v1.

AGENERIC-52
Generic recursion and type-instantiation recursion are distinct concepts.

AGENERIC-53
Infinite generic type instantiation must be rejected.

AGENERIC-54
Generic resource limits are distinct from semantic invalidity.

AGENERIC-55
Trait-solver overflow and generic-instantiation overflow are distinct diagnostics.

AGENERIC-56
Generic instances may be compiled in parallel.

AGENERIC-57
Parallel compilation must produce deterministic semantic results.

AGENERIC-58
Generic instance identity must not depend on compilation order.

AGENERIC-59
Generic analysis must be incrementally cacheable.

AGENERIC-60
Generic cache identity includes semantic dependencies.

AGENERIC-61
Generic machine artifacts require compatible target and ABI.

AGENERIC-62
Semantic generic artifacts may be reused across targets when target-independent.

AGENERIC-63
Machine code cannot be reused across incompatible targets.

AGENERIC-64
Generic artifact fingerprints distinguish semantic and code-generation dependencies.

AGENERIC-65
Generic definitions need not emit machine code until instantiated.

AGENERIC-66
Only verified concrete MIR may enter optimization.

AGENERIC-67
Specialization occurs after semantic verification.

AGENERIC-68
Optimization facts must have compiler-verifiable provenance.

AGENERIC-69
Unknown aliasing must never become NO_ALIAS through generic specialization without proof.

AGENERIC-70
Generic ownership facts remain valid after specialization.

AGENERIC-71
Generic capability facts remain valid after specialization.

AGENERIC-72
Generic Send and Share obligations remain independently verified.

AGENERIC-73
Generic async instances obey Future and suspension verification.

AGENERIC-74
Generic GPU instances obey GPU legality verification.

AGENERIC-75
Generic comptime execution obeys comptime capability and sandbox rules.

AGENERIC-76
Generic FFI exposure requires explicit ABI and representation contracts.

AGENERIC-77
Generic serialization is distinct from memory representation.

AGENERIC-78
Generic persistent representation is distinct from in-memory representation.

AGENERIC-79
Generic numeric semantics cannot be weakened by optimization.

AGENERIC-80
Strict floating-point semantics must be preserved by generic specialization.

AGENERIC-81
Fast-math behavior requires explicit semantic/optimization permission.

AGENERIC-82
Generic parallelization cannot silently alter ordered observable semantics.

AGENERIC-83
Generic closure parameters use the ordinary closure ownership/capability model.

AGENERIC-84
Generic iterator pipelines may be fused and eliminated without changing semantics.

AGENERIC-85
Generic abstractions need not create runtime allocations.

AGENERIC-86
Generic abstractions need not create runtime type metadata.

AGENERIC-87
Generic abstractions need not create runtime dispatch.

AGENERIC-88
Generic compile-time-only parameters may be erased from runtime representation.

AGENERIC-89
Zero-sized generic parameters need not occupy runtime storage.

AGENERIC-90
Type-state generic abstractions may be erased when not runtime-observable.

AGENERIC-91
Generic layout remains opaque unless explicitly exposed by representation contracts.

AGENERIC-92
Generic stable ABI requires an explicit stable representation strategy.

AGENERIC-93
Compiler-private generic layouts must not leak into stable ABI.

AGENERIC-94
Generic specialization may use target CPU and GPU capabilities.

AGENERIC-95
Target specialization does not alter semantic generic identity.

AGENERIC-96
PGO may influence generic specialization decisions but cannot alter semantics.

AGENERIC-97
Optimization profiles may alter specialization and sharing strategy but not language semantics.

AGENERIC-98
Size-oriented compilation may prefer code sharing.

AGENERIC-99
Performance-oriented compilation may prefer selective specialization.

AGENERIC-100
No generic optimization may bypass semantic verification.
```

---

# Kiến trúc generic hoàn chỉnh

Sau BOOTSTRAP-247, phần generic của Axiom có thể được hình dung:

```text
                    GENERIC SOURCE
                          │
                          ▼
                   Generic HIR/MIR
                          │
                          ▼
                GenericInstanceDB
                          │
                ┌─────────┴─────────┐
                │                   │
          Type Arguments       Const Arguments
                │                   │
                └─────────┬─────────┘
                          ▼
                    Substitution
                          │
                          ▼
                  Trait Normalization
                          │
                          ▼
                 Concrete Verified MIR
                          │
                          ▼
                 Specialization Plan
                    /            \
                   /              \
              Shared            Specialized
                 │                  │
                 └────────┬─────────┘
                          ▼
                        OptIR
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          Inlining    Vectorization   Code Sharing
             │            │            │
             └────────────┼────────────┘
                          ▼
                      ABI MIR
                          ▼
                       LIR
                          ▼
                   Machine Code
```

Điểm quan trọng nhất của thiết kế này là **Axiom không bị khóa vào Rust-style “monomorphize everything” cũng không bị khóa vào Java/C#-style runtime generic dispatch**.

Compiler có toàn quyền chọn:

```text
generic shared
generic specialized
generic partially specialized
generic inlined
generic completely erased
generic code-shared
```

dựa trên bằng chứng và profile.

---

# TASK TIẾP THEO

## **BOOTSTRAP-248 — AXIOM PATTERN MATCHING, DESTRUCTURING & EXHAUSTIVENESS ENGINE**

Phần này sẽ hoàn thiện semantic của:

```axiom
match value {
    Pattern => expression
}
```

bao gồm:

```text
struct pattern
tuple pattern
enum pattern
Option
Result
literal pattern
range pattern
binding pattern
nested pattern
wildcard
OR-pattern
guard
refutable / irrefutable pattern
exhaustiveness
unreachable arm
ownership trong pattern
partial move trong pattern
view/mut_view trong pattern
Drop trong pattern
```

Đặc biệt cần giải quyết một vấn đề rất quan trọng đối với Axiom:

```axiom
match user {
    User { name, age } => ...
}
```

compiler phải biết chính xác:

- field nào được Move;
- field nào được Copy;
- field nào chỉ được View;
- field nào còn thuộc owner;
- sau `match` object còn usable ở mức nào;
- với enum, payload nào được initialize;
- arm nào unreachable;
- match có exhaustive hay không.

Và tất cả điều này phải kết nối trực tiếp với **BOOTSTRAP-135 Ownership/Drop Verifier + BOOTSTRAP-244 Place Model + BOOTSTRAP-247 Generic Instantiation**.