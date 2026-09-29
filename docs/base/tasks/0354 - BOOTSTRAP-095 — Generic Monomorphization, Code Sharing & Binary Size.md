# BOOTSTRAP-095 — Generic Monomorphization, Code Sharing & Binary Size

**Trạng thái: FROZEN**

Đây là bước quan trọng vì Axiom đang theo hướng:

> **Generic abstraction có thể đạt performance như code chuyên biệt, nhưng không được mặc định trả giá bằng code bloat.**

Nếu chỉ dùng monomorphization kiểu đơn giản:

```text
Vec<i32>
Vec<u32>
Vec<f32>
Vec<f64>
Vec<MyStruct>
Vec<BigStruct>
...
```

mỗi specialization có thể sinh một bản machine code riêng. Với một thư viện lớn, binary có thể phình rất nhanh.

Axiom vì vậy cần một generic engine kết hợp:

```text
Monomorphization
+
Specialization
+
Representation-aware sharing
+
Function merging
+
LTO
+
Incremental compilation
```

---

# 1. Mục tiêu

Axiom phải đạt đồng thời:

```text
Generic abstraction
        ↓
compile-time specialization
        ↓
static dispatch
        ↓
zero unnecessary runtime metadata
```

nhưng:

```text
generic instances
        ↓
không duplicate code nếu semantics + representation cho phép
```

---

# 2. Ba loại generic specialization

Axiom phân biệt:

### 2.1 Semantic specialization

```text
T = i32
```

Compiler biết chính xác semantics của `i32`.

### 2.2 Representation specialization

```text
T = struct Foo { ... }
```

Compiler cần biết:

```text
size
alignment
layout
calling convention
Drop
Copy
```

### 2.3 Behavioral specialization

Ví dụ:

```text
T: Copy
T: Send
T: SomeTrait
```

Compiler có thể tối ưu dựa trên các fact này.

Ba loại thông tin không được trộn thành một khái niệm "generic".

---

# 3. Generic definition

Ví dụ:

```text
fn sum<T: Add + Zero>(items: view<T>) -> T {
    var result = T.zero();

    for x in items {
        result = result + x;
    }

    result
}
```

Compiler trước tiên tạo:

```text
GenericFunction
    FunctionId
    TypeParams
    TraitConstraints
    Body
```

Chưa sinh machine code.

---

# 4. Generic instance

Khi gặp:

```text
sum<i32>(values)
```

compiler tạo:

```text
GenericInstance {
    function: sum,
    substitution: {
        T -> i32
    }
}
```

Instance có semantic identity riêng.

---

# 5. Không compile generic ngay lập tức

Compiler không nên:

```text
parse generic
→ immediately generate code
```

Mà:

```text
Source
 ↓
Generic Definition
 ↓
Usage Discovery
 ↓
Instance Request
 ↓
Semantic Specialization
 ↓
Optimization
 ↓
Codegen
```

Điều này rất quan trọng cho incremental compilation.

---

# 6. Unused generic không tạo code

```text
fn foo<T>(...)
fn bar<T>(...)
fn baz<T>(...)
```

Nếu chỉ:

```text
foo<i32>()
```

thì:

```text
bar
baz
```

không có machine code.

---

# 7. Generic instances là demand-driven

Compiler tạo instance khi có:

```text
direct call
trait requirement
export requirement
function pointer requirement
reflection/materialization requirement
FFI requirement
```

Không tạo tất cả tổ hợp type.

---

# 8. Monomorphization mặc định

Axiom vẫn chọn:

> **Static specialization là default.**

Ví dụ:

```text
fn max<T: Ord>(a: T, b: T) -> T
```

với:

```text
max<i32>
max<f64>
```

có thể sinh hai implementation chuyên biệt.

Lợi ích:

- inline;
- constant propagation;
- SIMD;
- devirtualization;
- representation-specific optimization.

---

# 9. Nhưng specialization không đồng nghĩa duplicate machine code

Ví dụ:

```text
fn identity<T>(x: T) -> T {
    x
}
```

`T = i32` và `T = u32` có thể có cùng machine-level behavior.

Compiler có thể chia sẻ code nếu:

```text
ABI compatible
+
representation compatible
+
semantic behavior identical
+
optimization requirements compatible
```

---

# 10. Generic Code Sharing

Đặt tên cơ chế:

> **Generic Code Sharing — GCS**

Pipeline:

```text
Generic Instances
      ↓
Representation Analysis
      ↓
Semantic Equivalence
      ↓
Code Sharing Candidate
      ↓
Shared Machine Body
```

Không share nếu việc share làm mất optimization quan trọng.

---

# 11. Ví dụ

```text
fn swap<T>(a: mut_view<T>, b: mut_view<T>)
```

Các type:

```text
u32
i32
f32
```

có thể có representation giống nhau.

Compiler có thể tạo một body machine-level shared nếu:

```text
size
alignment
move semantics
drop semantics
ABI
```

phù hợp.

---

# 12. Drop là yếu tố ngăn sharing

Ví dụ:

```text
swap<i32>
swap<String>
```

không thể đơn giản share cùng implementation vì:

```text
i32 → no Drop
String → Drop
```

Compiler phải bảo toàn cleanup semantics.

---

# 13. Copy cũng ảnh hưởng

```text
fn consume<T>(x: T)
```

với:

```text
T: Copy
```

khác về semantic behavior so với:

```text
T: !Copy
```

Generic optimizer phải biết property này.

---

# 14. Trait specialization

Ví dụ:

```text
fn process<T: Clone>(x: T) -> T {
    x.clone()
}
```

Nếu concrete type:

```text
T = SmallInt
```

và compiler biết `Clone` là trivial, có thể biến thành:

```text
copy
```

Nhưng không được giả định `Clone == Copy`.

---

# 15. No arbitrary specialization v1

Axiom **không** cho phép:

```text
impl<T> Trait for T
impl Foo for i32
impl Foo for T
```

với overlapping semantics tùy tiện.

Vẫn giữ:

```text
coherence
orphan rules
deterministic resolution
```

---

# 16. Specialization levels

Axiom chia specialization thành:

```text
Level 0
Generic semantic definition

Level 1
Concrete type substitution

Level 2
Trait/property specialization

Level 3
Representation specialization

Level 4
Constant specialization

Level 5
Target specialization

Level 6
Profile/PGO specialization
```

Không nhất thiết tất cả đều tạo một function body riêng.

---

# 17. Constant specialization

Ví dụ:

```text
fn sum<const N: usize>(a: [i32; N]) -> i32
```

với:

```text
sum<4>()
```

compiler biết:

```text
N = 4
```

có thể unroll.

Nhưng:

```text
N = 100000
```

không nên mặc định unroll toàn bộ.

Optimizer có cost model.

---

# 18. Generic const parameters

V1 giới hạn:

```text
int
bool
```

Ví dụ:

```text
Matrix<T, const ROWS: usize, const COLS: usize>
```

Không đưa arbitrary compile-time objects vào generic parameter ở Core v1.

---

# 19. Generic recursion

Ví dụ:

```text
fn foo<T>() {
    foo<Wrapper<T>>();
}
```

Compiler phải phát hiện specialization cycle:

```text
T
→ Wrapper<T>
→ Wrapper<Wrapper<T>>
→ ...
```

Nếu không có finite instance:

```text
compile error
```

---

# 20. Trait solver + generic engine

Generic specialization không được tự quyết định trait facts.

Luồng:

```text
Generic Instance
       ↓
Substitution
       ↓
Trait Solver
       ↓
Proven / Ambiguous / Error
       ↓
Specialization
```

Ví dụ:

```text
T: Add
```

không được coi là proven chỉ vì compiler "có vẻ biết".

---

# 21. Generic capability verification

Ví dụ:

```text
fn fill<T>(x: mut_view<T>) {
    ...
}
```

Compiler vẫn kiểm tra:

```text
ownership
capability
alias
Drop
Send
Share
```

sau substitution.

Không có:

> generic code được miễn safety verification.

---

# 22. Generic async

```text
async fn process<T: Send>(x: T) -> Result<T, E>
```

Mỗi concrete future instance có thể khác state layout.

Compiler:

```text
T substitution
→ liveness analysis
→ Future state layout
→ optimize
```

Chỉ state fields thực sự cần across await được giữ lại.

---

# 23. Generic closure

```text
fn apply<T, F>(x: T, f: F) -> T
where
    F: Fn(T) -> T
```

Nếu `F` là closure cụ thể:

```text
apply(x, |v| v * 2)
```

compiler có thể:

```text
specialize
→ inline closure
→ eliminate environment
→ inline apply
```

Kết quả có thể chỉ còn machine loop/arithmetic.

---

# 24. Generic GPU

```text
@kernel
fn add<T: Numeric>(
    a: view<T>,
    b: view<T>,
    out: mut_view<T>
)
```

Compiler specialization theo:

```text
T
target GPU
vector width
address space
numeric semantics
```

nhưng GPU legality phải được kiểm tra **sau specialization**.

---

# 25. Generic FFI

Generic function:

```text
fn foo<T>(x: T)
```

không tự động trở thành exported symbol.

Muốn:

```text
@export("foo_i32")
```

compiler phải materialize concrete instance:

```text
foo<i32>
```

và kiểm tra:

```text
C ABI
layout
calling convention
ownership
FFI-safe type
```

---

# 26. Generic function pointers

Ví dụ:

```text
let f = foo<i32>;
```

đây là explicit materialization của generic instance.

Compiler phải tạo callable concrete function.

---

# 27. `dyn Trait` và generic khác nhau

Generic:

```text
fn draw<T: Drawable>(x: T)
```

→ static specialization.

Dynamic:

```text
fn draw(x: dyn Drawable)
```

→ runtime dispatch.

Không compiler tự chuyển generic thành dynamic dispatch để tiết kiệm code.

Nếu cần code sharing, dùng **internal generic sharing**, không thay đổi source semantics.

---

# 28. Generic sharing không được thay đổi observable behavior

Compiler không được share:

```text
T = TypeA
T = TypeB
```

nếu:

- Drop khác;
- panic behavior khác;
- alignment khác;
- overflow semantics khác;
- ABI khác;
- specialization fact khác;
- FFI observable behavior khác.

---

# 29. Representation classes

Compiler có thể phân loại concrete types:

```text
RC-0
Zero-sized

RC-1
Integer/pointer scalar

RC-2
Float scalar

RC-3
Fixed-size homogeneous aggregate

RC-4
Aggregate with Drop

RC-5
Dynamic representation

RC-6
Opaque/foreign

RC-7
Special target representation
```

Đây là **compiler internal classification**, không phải programmer-facing type system.

---

# 30. Erased generic representation

Một generic function có thể được lowered thành dạng representation-erased:

```text
fn foo<T>(T)
```

→ internal:

```text
fn foo_erased(
    ptr,
    metadata
)
```

**chỉ khi semantics cho phép.**

Đây không phải dynamic dispatch mặc định.

---

# 31. Khi nào dùng erased code?

Ví dụ một algorithm:

```text
copy_bytes<T>
```

nếu semantics thực chất chỉ cần:

```text
size
alignment
```

compiler có thể tạo shared implementation.

Nhưng nếu code cần:

```text
T.drop()
T.clone()
trait dispatch
```

thì metadata/function pointers có thể cần thiết.

---

# 32. Code sharing và optimization tradeoff

Compiler không phải lúc nào cũng share.

Ví dụ:

```text
Vec<T>.push()
```

Nếu `T` cụ thể:

```text
i32
```

inlining có thể rất quan trọng.

Compiler có thể chọn duplicate.

Nếu:

```text
large generic function
```

được instantiate 100 type khác nhau, code sharing có thể có lợi.

---

# 33. Cost model

Quyết định:

```text
duplicate
vs
share
```

dựa trên:

```text
function size
hotness
inline probability
type representation
target
code size profile
LTO information
PGO
optimization level
```

---

# 34. Optimization profiles

### `debug`

Ưu tiên:

```text
fast compilation
good debugging
moderate optimization
```

### `release`

Ưu tiên:

```text
performance
reasonable binary size
```

### `size`

Ưu tiên:

```text
binary size
```

### `speed`

Ưu tiên:

```text
runtime performance
```

### `tiny`

Có thể ưu tiên cực mạnh:

```text
code sharing
outlining
function merging
dead stripping
```

---

# 35. Function Outlining

Nếu hai đoạn code khác generic instances giống nhau:

```text
foo<i32>
foo<u32>
```

compiler có thể outline common body:

```text
shared_helper()
```

Các specialization giữ phần type-specific.

---

# 36. Identical Code Folding

Linker có thể phát hiện:

```text
machine code A == machine code B
```

và merge.

Nhưng phải bảo toàn:

```text
function address identity
```

nếu address có thể quan sát.

Do đó Axiom cần phân biệt:

```text
function identity
vs
code identity
```

---

# 37. Function address observability

Nếu:

```text
let p = address_of_function(foo);
```

và semantics cho phép so sánh address:

compiler không được merge hai function nếu điều đó làm thay đổi observable behavior.

Nếu function identity không observable:

```text
foo == bar
```

thì merge có thể được phép.

---

# 38. COMDAT

Generic instances trong object file có thể dùng:

```text
COMDAT/linkonce
```

để linker deduplicate.

Ví dụ:

```text
module A → Vec<i32>::push
module B → Vec<i32>::push
```

Final linker giữ một implementation nếu ABI/code identity phù hợp.

---

# 39. Cross-module generic metadata

`.axmeta` cần lưu:

```text id="tdb42d"
GenericDefinition
GenericConstraints
InstanceFingerprint
RepresentationFacts
OptimizationSummary
ABI summary
```

Module khác không cần reparse source để hiểu generic API.

---

# 40. Generic fingerprint

Instance identity:

```text id="d9ewr0"
GenericFingerprint =
    GenericDefinitionFingerprint
    + TypeArguments
    + ConstArguments
    + TraitResolutionFacts
    + Target
    + Profile
    + SemanticCompilerVersion
```

Nếu fingerprint không đổi:

```text
reuse compiled instance
```

---

# 41. Incremental compilation

Ví dụ:

```text id="kzqq92"
Vec<T>
```

thay đổi implementation.

Compiler chỉ invalidate:

```text
Vec<T> instances
```

bị ảnh hưởng.

Không rebuild toàn bộ package nếu public semantic fingerprint không thay đổi.

---

# 42. Generic cache

Cache key không chỉ là:

```text id="9kmc2u"
Vec<i32>
```

mà:

```text id="5zqg4v"
Definition hash
+
substitution
+
target
+
optimization profile
+
relevant compiler semantic version
```

---

# 43. Cross-target cache

Không reuse machine code:

```text id="e4xq2k"
x86-64 → ARM64
```

Nhưng có thể reuse:

```text id="8m3t9a"
source semantic analysis
HIR
typed HIR
generic resolution
MIR
```

Tùy tầng.

---

# 44. Generic compilation pipeline

Frozen:

```text id="xg2p2x"
Generic Source
      ↓
Generic HIR
      ↓
Generic MIR
      ↓
Instance Substitution
      ↓
Trait Resolution
      ↓
Capability / Ownership Verification
      ↓
Representation Analysis
      ↓
Specialization
      ↓
Instance MIR
      ↓
Optimization
      ↓
Code Sharing Analysis
      ↓
ABI Lowering
      ↓
Machine Code
```

---

# 45. Không optimize trước semantic specialization một cách nguy hiểm

Ví dụ:

```text
T: Copy
```

chưa được giả định nếu trait solver chưa chứng minh.

Thứ tự:

```text
resolve facts
→ specialize
→ optimize
```

không:

```text
guess
→ optimize
→ hope
```

---

# 46. Generic specialization và ownership

Ví dụ:

```text
fn consume<T>(x: T) {
    ...
}
```

Với:

```text
T = i32
```

Move có thể trở thành register operation.

Với:

```text
T = File
```

phải preserve Drop semantics.

Compiler có thể optimize physical movement, nhưng semantic ownership transition vẫn tồn tại.

---

# 47. Generic specialization và capabilities

```text
fn process<T>(x: view<T>)
```

Compiler phải biết:

```text
T layout
T validity
region
access
```

nhưng `view<T>` capability semantics không biến mất trước khi verification hoàn thành.

Sau verification, capability metadata có thể erase.

---

# 48. Generic specialization và `Send`

Ví dụ:

```text
fn spawn_work<T: Send>(x: T)
```

Concrete:

```text
spawn_work<MyType>(x)
```

compiler phải prove:

```text
MyType: Send
```

Nếu không:

```text
compile error
```

Không runtime check.

---

# 49. Generic specialization và `Share`

Tương tự:

```text
T: Share
```

là compile-time semantic property.

Không tạo:

```text
if runtime_is_thread_safe(T)
```

---

# 50. Trait specialization không tạo runtime type metadata

Ví dụ:

```text
fn sort<T: Ord>(...)
```

Không cần runtime:

```text
TypeInfo<T>
```

nếu tất cả dispatch đều static.

Đây là một trong những nguồn binary/runtime efficiency quan trọng của Axiom.

---

# 51. Runtime type information

Nếu application thực sự cần:

```text
Type
```

thì explicit reflection metadata phải được materialize.

Ví dụ:

```text id="q9b2zr"
comptime {
    let t = type_of<User>();
}
```

không tạo runtime metadata.

Nếu:

```text
let t: RuntimeType = reflect<User>();
```

thì programmer đã yêu cầu metadata.

---

# 52. Generic debug information

Debug build cần mapping:

```text
machine code
→ generic instance
→ concrete type arguments
→ source
```

Ví dụ debugger phải hiển thị:

```text
Vec<User>::push
```

thay vì:

```text
generic_fn_4387
```

---

# 53. Symbol naming

Internal symbols phải deterministic:

```text id="s2brl7"
_ZN... 
```

hoặc Axiom mangling riêng.

Symbol identity phải encode đủ:

```text
package
module
function
generic args
ABI-relevant specialization
```

nhưng không nhất thiết encode mọi semantic detail nếu fingerprint metadata đã quản lý.

---

# 54. ABI generic instances

Internal:

```text
Vec<i32>
```

ABI có thể thay đổi theo target.

Không freeze representation generic type chỉ vì nó public.

Stable C ABI phải explicit:

```text
@repr(C)
```

---

# 55. Generic library distribution

Một package binary có thể cung cấp:

### Option A — Source generic

```text
.ax
```

Compiler specialize locally.

### Option B — Generic semantic metadata

```text
.axmeta
```

Compiler có semantic definition mà không cần source đầy đủ.

### Option C — Precompiled instances

```text
.axobj
```

Cho các specialization phổ biến.

Axiom nên hỗ trợ cả ba về lâu dài.

---

# 56. Precompiled generic instances

Ví dụ standard library có:

```text
Vec<i8>
Vec<i16>
Vec<i32>
Vec<i64>
Vec<f32>
Vec<f64>
```

có thể cung cấp optimized instances.

Nhưng compiler vẫn có quyền specialize local nếu cần.

---

# 57. Generic ABI cache

Nếu package đã build:

```text
Vec<MyType>
```

và ABI/layout/fingerprint không đổi:

compiler có thể reuse machine code.

Nếu optimizer profile khác:

```text
size
vs
speed
```

có thể cần bản khác.

---

# 58. ThinLTO-like architecture

Axiom không cần phụ thuộc LLVM/LTO lâu dài.

Compiler nội bộ có thể thực hiện:

```text
Module summaries
       ↓
Call graph
       ↓
Hotness
       ↓
Inline decisions
       ↓
Generic sharing
       ↓
Dead stripping
       ↓
Machine optimization
```

---

# 59. Whole-program specialization

Nếu:

```text
final executable
```

biết toàn bộ call graph:

```text
generic function
→ only one concrete type
```

compiler có thể specialize mạnh hơn.

Ví dụ:

```text
fn process<T>()
```

chỉ được gọi với:

```text
T = User
```

thì không cần giữ generic abstraction runtime.

---

# 60. Library boundary

Nếu library là shared library:

```text
libfoo.so
```

compiler không biết toàn bộ consumers.

Do đó generic functions cần một chiến lược:

```text
export source/metadata
hoặc
precompiled instances
hoặc
explicit ABI-erased interface
```

Không assume whole-program optimization.

---

# 61. Shared library và generic code

Generic API không nên mặc định trở thành stable binary ABI.

Ví dụ:

```text
pub fn sort<T: Ord>(...)
```

có thể thay đổi implementation mà không phá semantic API.

Consumer compile lại instance.

Stable ABI chỉ khi explicit export contract.

---

# 62. Generic virtual ABI

Không tạo "generic runtime".

Nếu cần dynamic interface:

```text
dyn Trait
```

thì đó là dynamic abstraction độc lập.

Generic engine không tự sinh vtable.

---

# 63. Code size budget

Compiler có thể cung cấp diagnostic:

```text id="f4t7k3"
generic code size report

Vec<T>::push
    instances: 42
    machine size: 18.2 KB
    shared: 11
    duplicated: 31
```

AI/IDE có thể sử dụng.

---

# 64. `#[inline]` equivalent

Axiom:

```text
@inline
@noinline
```

đã có.

Nhưng `@inline` là:

> optimization hint/contract phù hợp compiler policy,

không phải:

> bắt buộc textual expansion.

---

# 65. Generic `@inline`

```text
@inline
fn min<T: Ord>(...)
```

compiler có thể inline từng specialization.

Nhưng nếu code size trở nên quá lớn, profile/compiler policy có thể giới hạn nếu attribute chỉ là hint.

---

# 66. Exact semantic contract vs optimization hint

Attributes phân biệt:

```text id="u6d0r7"
@inline       → HINT
@repr(C)      → CONTRACT
@kernel       → SEMANTIC
```

Không để programmer nhầm ba loại.

---

# 67. Generic recursion + code size protection

Compiler phải có:

```text id="r8r0wm"
max generic instance depth
max specialization count
max compile-time budget
```

Nếu vượt:

```text
diagnostic
```

không crash compiler.

---

# 68. Deterministic specialization

Cùng:

```text
source
target
profile
dependencies
compiler semantic version
```

phải tạo cùng semantic specialization graph.

Compiler có thể thay đổi internal optimization heuristics theo compiler version, nhưng trong cùng compiler version không được phụ thuộc nondeterministic thread scheduling.

---

# 69. Parallel generic compilation

Các instance độc lập:

```text
Vec<i32>
Vec<f32>
HashMap<u64, User>
```

có thể compile song song.

Kết quả semantic phải giống serial compilation.

---

# 70. Generic explosion detection

Compiler nên cảnh báo:

```text
warning AXGEN-SIZE
generic function generated 127 concrete instances
```

nhưng không tự động thay đổi semantics.

Có thể đề xuất:

```text
dyn Trait
code sharing
@noinline
```

nhưng không tự sửa code.

---

# 71. Không tự động chuyển generic thành dynamic

Ví dụ:

```text
fn process<T: Trait>(...)
```

nhiều instances không có nghĩa compiler được phép biến thành:

```text
fn process(x: dyn Trait)
```

vì có thể thay đổi:

- performance;
- allocation;
- ABI;
- type identity;
- dispatch;
- object safety;
- lifetime/capability.

---

# 72. Generic code sharing là compiler internal

Programmer không viết:

```text
shared generic
erased generic
monomorphize
```

đây là backend/compiler decisions.

Source chỉ nói:

```text
fn foo<T>(...)
```

---

# 73. Frozen invariants

### Generic semantics

**AGEN2-20 — Generic Definitions Are Not Runtime Instances**

**AGEN2-21 — Generic Instances Are Created On Demand**

**AGEN2-22 — Unused Generic Instances Must Not Generate Required Runtime Code**

**AGEN2-23 — Generic Specialization Is Compile-Time**

**AGEN2-24 — Generic Dispatch Is Static By Default**

**AGEN2-25 — Dynamic Dispatch Is Not An Automatic Generic Optimization**

---

### Verification

**AGEN2-26 — Generic Instances Must Be Fully Type-Checked**

**AGEN2-27 — Generic Instances Must Be Fully Ownership-Verified**

**AGEN2-28 — Generic Instances Must Be Capability-Verified**

**AGEN2-29 — Generic Instances Must Resolve Required Trait Facts**

**AGEN2-30 — Generic Send/Share Properties Are Concrete-Type Facts**

---

### Specialization

**AGEN2-31 — Specialization May Depend On Representation**

**AGEN2-32 — Specialization May Depend On Compile-Time Constants**

**AGEN2-33 — Specialization May Depend On Proven Trait Facts**

**AGEN2-34 — Specialization Must Preserve Observable Semantics**

**AGEN2-35 — Arbitrary Overlapping Specialization Is Not Core v1**

---

### Code sharing

**AGEN2-36 — Generic Instances May Share Machine Code**

**AGEN2-37 — Code Sharing Requires ABI-Compatible Representation**

**AGEN2-38 — Code Sharing Must Preserve Drop Semantics**

**AGEN2-39 — Code Sharing Must Preserve Panic/Error Semantics**

**AGEN2-40 — Code Sharing Must Preserve Observable Function Identity**

**AGEN2-41 — Code Sharing Is An Optimization, Not A Source-Level Semantic**

**AGEN2-42 — Compiler May Prefer Duplication When Optimization Benefits Outweigh Size**

---

### Binary size

**AGEN2-43 — Monomorphization Must Not Imply Unbounded Code Duplication**

**AGEN2-44 — Link-Time Deduplication Is Permitted**

**AGEN2-45 — Function Outlining Is Permitted**

**AGEN2-46 — Identical Code Folding Must Respect Observable Identity**

**AGEN2-47 — Dead Generic Instances Must Be Eliminated**

**AGEN2-48 — Binary Size Optimization Must Not Change Semantics**

---

### Incremental compilation

**AGEN2-49 — Generic Instances Have Stable Semantic Fingerprints**

**AGEN2-50 — Generic Instance Caches Are Dependency-Aware**

**AGEN2-51 — Generic Changes Invalidate Only Affected Instances**

**AGEN2-52 — Target-Specific Machine Code Is Not Cross-Target Reusable**

**AGEN2-53 — Semantic Generic Analysis May Be Reused Across Targets**

---

### FFI / ABI

**AGEN2-54 — Generic Functions Are Not Automatically FFI Exports**

**AGEN2-55 — FFI Export Requires Concrete Generic Materialization**

**AGEN2-56 — Generic ABI Is Separate From Generic Semantics**

**AGEN2-57 — Stable Foreign ABI Requires Explicit Representation Contracts**

---

### Limits

**AGEN2-58 — Generic Specialization Depth Is Bounded**

**AGEN2-59 — Generic Instance Count Is Resource-Bounded**

**AGEN2-60 — Generic Compilation Budget Failure Is A Normal Diagnostic**

**AGEN2-61 — Parallel Generic Compilation Must Be Semantically Equivalent To Serial Compilation**

---

# 74. Kiến trúc compiler sau BOOTSTRAP-095

Pipeline generic hiện hoàn chỉnh hơn:

```text
Source
  ↓
Parser
  ↓
AST
  ↓
Resolver
  ↓
HIR
  ↓
Typed HIR
  ↓
Generic Definition
  ↓
Generic Instance Request
  ↓
Substitution
  ↓
Trait Solver
  ↓
Ownership / Capability Verification
  ↓
Representation Analysis
  ↓
Specialization
  ↓
MIR
  ↓
Semantic Optimization
  ↓
Generic Code Sharing
  ↓
ABI Lowering
  ↓
Axiom LIR
  ↓
Machine IR
  ↓
Codegen
  ↓
Object
  ↓
Link
```

---

# 75. Quyết định quan trọng nhất

Axiom **không chọn một cực**:

```text
100% monomorphization
```

cũng không:

```text
100% erased generics
```

mà dùng:

```text
              Generic
                 │
       ┌─────────┴─────────┐
       │                   │
 specialization       representation
       │                   │
       └─────────┬─────────┘
                 ↓
        optimization analysis
                 │
       ┌─────────┴─────────┐
       │                   │
   specialized          shared
      code                code
```

Compiler tự chọn implementation phù hợp.

Programmer vẫn viết generic code một lần.

---

# 76. Một ví dụ thể hiện toàn bộ triết lý

Source:

```text
fn sum<T: Add + Zero>(
    values: view<T>
) -> T {
    var result = T.zero();

    for x in values {
        result = result + x;
    }

    result
}
```

Application:

```text
let a = sum<int32>(ints);
let b = sum<float32>(floats);
```

Compiler có thể tạo:

```text
sum<i32>    → vectorized integer loop
sum<f32>    → SIMD floating loop
```

Nếu một generic khác:

```text
identity<i32>
identity<u32>
```

có cùng machine semantics:

```text
identity_shared
```

có thể được dùng chung.

Programmer không phải biết compiler đã làm gì.

---

# 77. Kết quả

Axiom hiện có một mô hình khá mạnh:

```text
Generic source
     ↓
Static semantics
     ↓
Concrete specialization
     ↓
Strong optimization
     ↓
Selective code sharing
     ↓
Small binary
```

Điều này phù hợp trực tiếp với mục tiêu ban đầu của Axiom:

> **Cú pháp abstraction cao cấp nhưng executable cuối cùng vẫn gần với code viết tay ở mức thấp.**

---

## Bước kiến trúc tiếp theo

Sau generic engine, còn một vấn đề rất lớn để đạt mục tiêu **native compiler độc lập, binary nhỏ và tốc độ C/C++**:

# **BOOTSTRAP-096 — Axiom Link-Time Architecture, Dead Stripping, LTO, PGO & Whole-Program Optimization**

Sẽ chốt:

```text
Object
→ Symbol Graph
→ Dependency Graph
→ Dead Code Elimination
→ Generic Dedup
→ Function Merging
→ LTO
→ PGO
→ Section GC
→ ICF
→ Code Layout
→ Hot/Cold Splitting
→ Binary Size Optimization
→ Final PE/ELF/Mach-O/WASM
```

và đặc biệt giải quyết một câu hỏi rất quan trọng:

> **Làm thế nào Axiom có thể vừa compile từng module rất nhanh, vừa có whole-program optimization đủ mạnh để binary cuối cùng đạt hiệu năng/kích thước rất gần native hand-written code?**