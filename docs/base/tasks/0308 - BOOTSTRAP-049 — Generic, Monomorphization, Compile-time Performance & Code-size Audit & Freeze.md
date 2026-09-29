Tiếp tục.

# BOOTSTRAP-049 — Generic, Monomorphization, Compile-time Performance & Code-size Audit & Freeze

Đây là phần rất quan trọng với mục tiêu của Axiom: **generic mạnh nhưng không biến compiler thành C++ template hell và binary thành một đống code nhân bản**.

Nguyên tắc trung tâm:

> **Generic là abstraction ở compile-time; specialization chỉ được tạo khi cần; compiler phải chủ động kiểm soát duplication.**

---

# 1. Mục tiêu

Axiom cần đạt đồng thời:

```text
Generic abstraction mạnh
        +
Static dispatch
        +
Zero-cost abstraction
        +
Binary nhỏ
        +
Compile nhanh
        +
Incremental compilation
```

Không nên chọn một trong số đó để hy sinh hoàn toàn.

---

# 2. Generic không phải runtime mechanism

Ví dụ:

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

`T` không nhất thiết tồn tại trong binary.

Compiler tạo specialization:

```text
max<i32>
max<f64>
max<MyType>
```

chỉ khi cần.

---

# 3. Monomorphization là mặc định cho performance-critical generic

Static generic:

```text
Generic HIR
    ↓
constraint solving
    ↓
specialization
    ↓
typed concrete MIR
```

Sau đó backend có thể inline/vectorize/devirtualize.

---

# 4. Nhưng không phải specialization mù quáng

Nếu:

```text
foo<u32>
foo<u64>
foo<i32>
foo<i64>
```

có machine implementation tương đương, compiler có thể chia sẻ implementation.

Ví dụ conceptually:

```text
foo<u32> ─┐
foo<i32> ─┼──→ shared machine body
foo<u64> ─┤
foo<i64> ─┘
```

nếu không có observable representation difference.

---

# 5. Semantic specialization ≠ machine specialization

Đây là distinction cần khóa.

```text
Generic specialization
        ↓
semantic concrete type
        ↓
representation analysis
        ↓
machine implementation sharing
```

Hai type khác nhau về semantic identity vẫn có thể dùng cùng machine body.

---

# 6. Không merge khi semantic behavior khác

Ví dụ:

```axiom
struct Meter(u32)
struct Second(u32)
```

có thể cùng representation:

```text
u32
```

nhưng:

```text
Meter != Second
```

Compiler không được biến chúng thành cùng semantic type.

Chỉ có thể share machine implementation ở tầng thấp hơn.

---

# 7. Generic identity

Mỗi specialization có identity:

```text
GenericDefId
+
TypeArguments
+
ConstArguments
+
RelevantTargetConfig
```

Ví dụ:

```text
Vec<i32>
```

khác:

```text
Vec<f64>
```

về specialization identity.

---

# 8. Nhưng cache identity phải canonical

Compiler không được tạo:

```text
Vec<i32>#1
Vec<i32>#2
Vec<i32>#3
```

chỉ vì nó được yêu cầu từ nhiều module.

Phải canonicalize:

```text
Vec<i32>
      ↓
SpecializationId X
```

và mọi caller dùng lại X.

---

# 9. Cross-module generic

Module A:

```axiom
pub fn sort<T: Ord>(mut_view<T> data)
```

Module B:

```axiom
sort(xs)
```

Compiler không cần compile toàn bộ source của A mỗi lần.

Public semantic metadata phải đủ để instantiate generic.

---

# 10. Generic metadata

Artifact/interface metadata cần chứa:

```text
GenericDef
Type parameters
Const parameters
Trait constraints
Associated types
Required capabilities
Send/Share properties
ABI-relevant information
Comptime dependencies
```

Không cần lưu toàn bộ implementation nếu compiler không cần.

---

# 11. Incremental compilation

Thay đổi:

```text
private implementation
```

không nên làm rebuild mọi generic caller nếu semantic public interface không thay đổi.

---

# 12. Nhưng implementation changes có thể ảnh hưởng optimization

Đây là chỗ cần phân biệt:

```text
semantic dependency
```

và:

```text
optimization dependency
```

Ví dụ thay đổi implementation có thể làm:

```text
inline
→ không inline
```

nhưng không được làm semantic fingerprint thay đổi nếu public semantics không đổi.

---

# 13. Hai loại fingerprint

Đề xuất:

```text
SemanticFingerprint
OptimizationFingerprint
```

### SemanticFingerprint

Ảnh hưởng:

- type checking;
- trait solving;
- ABI;
- ownership;
- layout contracts;
- generated declarations.

### OptimizationFingerprint

Ảnh hưởng:

- inline;
- vectorization;
- specialization;
- LTO;
- machine optimization.

---

# 14. Compile cache

Cache key:

```text
CompilerSemanticVersion
Target
Features
OptimizationProfile
GenericDefinition
TypeArguments
ConstArguments
RelevantDependencies
ComptimeInputs
```

---

# 15. Không cache dựa trên source text đơn thuần

Hai source khác nhau nhưng semantic equivalent có thể vẫn có IR tương tự.

Tuy nhiên v1 nên ưu tiên:

```text
stable semantic fingerprint
```

thay vì cố chứng minh semantic equivalence quá sâu.

---

# 16. Trait specialization

Ví dụ:

```axiom
fn process<T: Fast>(x: T)
```

và:

```axiom
fn process<T: General>(x: T)
```

Không nên cho phép arbitrary overlapping specialization trong v1.

Đã freeze:

> Arbitrary specialization không thuộc Core v1.

Điều này giúp trait solver deterministic.

---

# 17. Không tạo template-instantiation explosion

Compiler phải deduplicate:

```text
same GenericDef
+
same canonical arguments
=
same specialization
```

---

# 18. Const generics

V1 chỉ nên hỗ trợ const parameter đơn giản:

```axiom
struct Array<T, const N: usize> {
    ...
}
```

Ví dụ:

```text
Array<f32, 4>
Array<f32, 8>
```

là hai specialization.

---

# 19. Không mở dependent types

Không nên để:

```axiom
Array<T, some_arbitrary_type_level_expression>
```

trở thành một hệ theorem proving.

V1:

```text
integer
bool
```

là đủ.

---

# 20. Generic code phải được type-check trước specialization

Quy trình:

```text
parse
 ↓
resolve
 ↓
generic type-check
 ↓
constraints
 ↓
instantiate
 ↓
concrete verification
```

Không chờ tới machine code mới phát hiện lỗi generic.

---

# 21. Ownership trong generic

Ví dụ:

```axiom
fn consume<T>(x: T) {
    ...
}
```

Compiler vẫn phải biết:

```text
T : Copy?
T : Drop?
T : Send?
T : Share?
```

Không được coi generic value như một opaque C `void*`.

---

# 22. Capability trong generic

```axiom
fn fill<T>(mut_view<T> x, value: T)
```

phải giữ nguyên capability semantics sau specialization.

Generic không phải escape hatch khỏi verifier.

---

# 23. Generic async

```axiom
async fn load<T>(...) -> Result<T, Error>
```

Future specialization phải chứa chính xác state cần thiết.

Không tạo một generic boxed runtime object mặc định.

---

# 24. Generic GPU

```axiom
@kernel
fn map<T: Numeric>(...)
```

Compiler specialize cho GPU target.

Nhưng GPU legality vẫn được verify sau specialization.

---

# 25. Generic FFI

Không được:

```axiom
@export("foo")
fn foo<T>(...)
```

và giả định C ABI hiểu generic.

Muốn export:

```text
generic
 ↓
concrete specialization
 ↓
ABI classification
 ↓
export
```

---

# 26. Dynamic dispatch là alternative cho monomorphization

Khi code size quan trọng hơn static specialization:

```axiom
dyn Trait
```

cho phép:

```text
one implementation
+
runtime dispatch
```

Nhưng dynamic dispatch phải explicit.

---

# 27. Không implicit boxing để tránh generic explosion

Axiom không nên tự động:

```text
T
 ↓
Box<dyn Trait>
```

chỉ để giải quyết compilation.

---

# 28. Code-size optimization hierarchy

Compiler có thể áp dụng:

```text
1. Dead code elimination
2. Specialization deduplication
3. Generic body sharing
4. Inlining heuristics
5. Identical code folding
6. Cold-code outlining
7. LTO
```

---

# 29. Inlining không phải mặc định vô hạn

Generic:

```text
small function
```

có thể inline.

Generic:

```text
huge function
```

không nên inline chỉ vì nó monomorphized.

---

# 30. `@inline`

`@inline` vẫn là optimization hint.

Không được hiểu là:

```text
must physically inline
```

---

# 31. `@noinline`

Tương tự:

```text
@noinline
```

là compiler constraint/hint tùy strength đã định nghĩa, nhưng semantic behavior vẫn không thay đổi.

---

# 32. LTO

Axiom nên hỗ trợ:

```text
no-lto
thin-lto
full-lto
```

nhưng semantic result phải giống nhau.

---

# 33. LTO không được thay đổi ABI semantics

LTO có thể:

```text
remove function
inline function
merge function
specialize function
```

nhưng không được phá:

- `@export`;
- FFI;
- dynamic symbol lookup;
- externally observable ABI.

---

# 34. Public generic API

Ví dụ:

```axiom
pub fn map<T, U, F: Fn(T) -> U>(...)
```

metadata phải đủ để downstream compiler instantiate.

Không cần expose compiler-internal machine code.

---

# 35. Generic body serialization

Compiler artifact có thể chứa:

```text
Generic HIR
or
typed generic MIR
```

tùy optimization pipeline.

Khuyến nghị:

> **Serialize canonical semantic IR thay vì AST source.**

---

# 36. Vì sao không serialize AST?

AST chứa quá nhiều thứ compiler đã giải quyết:

```text
imports
names
syntax sugar
source formatting
```

Trong khi downstream cần semantic information.

---

# 37. Generic cache pipeline

```text
Source
 ↓
AST
 ↓
HIR
 ↓
Typed Generic HIR
 ↓
SemanticFingerprint
 ↓
Cache
 ↓
Specialization
 ↓
MIR
```

---

# 38. Parallel specialization

Các specialization độc lập:

```text
Vec<i32>
Vec<f64>
HashMap<String, X>
...
```

có thể compile song song.

Deterministic result phải giống serial compilation.

---

# 39. Specialization priority

Compiler không được để thread scheduling quyết định:

```text
SpecializationId
```

Identity phải deterministic.

---

# 40. Deterministic IDs

Không dùng:

```text
memory address
thread ID
hash-map iteration order
```

để tạo semantic specialization identity.

---

# 41. Generic diagnostics

Compiler phải báo được:

```text
Generic:
    foo<T>

Instantiation:
    foo<MyType>

Failure:
    MyType does not implement Trait X

Constraint:
    T: X
```

AI agent sẽ hưởng lợi rất nhiều từ cấu trúc này.

---

# 42. Error chain

Không nên tạo error kiểu:

```text
template instantiation failed
```

khổng lồ hàng nghìn dòng.

Nên có semantic chain:

```text
EGEN_...
  declaration
  instantiated arguments
  failed constraint
  source span
```

---

# 43. Recursive generics

Compiler phải phát hiện:

```text
T → Foo<T> → Foo<Foo<T>> → ...
```

khi specialization không hội tụ.

---

# 44. Specialization depth

Có giới hạn compiler để chống pathological compile:

```text
max specialization depth
max trait resolution depth
max comptime evaluation
```

Nhưng diagnostics phải chỉ ra nguyên nhân.

---

# 45. No arbitrary compile-time code duplication

Comptime-generated declarations cũng phải deduplicate theo semantic identity.

---

# 46. Derive

Ví dụ:

```axiom
@derive(Debug, Eq, Hash)
struct User { ... }
```

compiler-generated implementations phải được coi như declarations bình thường.

Không tạo duplicate impl nếu derive được yêu cầu nhiều lần.

---

# 47. Generic closures

Closure type identity:

```text
closure expression ID
+
capture type
```

Compiler có thể share machine code nếu semantic environment/layout cho phép.

---

# 48. Function values

Noncapturing closure:

```text
fn pointer
```

có thể dùng chung code với function-equivalent implementation.

Capturing closure:

```text
code + environment
```

vẫn không cần heap.

---

# 49. Generic Drop

Một generic type:

```axiom
struct Container<T> {
    value: T
}
```

Drop behavior phụ thuộc `T`.

Compiler phải specialize/drop-elaborate chính xác.

---

# 50. Generic layout

```text
Container<i32>
Container<f64>
Container<MyType>
```

có thể có layout khác nhau.

Không được giả định generic representation đồng nhất.

---

# 51. ABI specialization

ABI classification xảy ra sau concrete representation analysis:

```text
Generic
 ↓
Specialization
 ↓
Layout
 ↓
ABI
```

Không ngược lại.

---

# 52. Generic code and optimization legality

Compiler chỉ được:

```text
vectorize
alias-eliminate
reorder
scalarize
```

sau khi ownership/capability/memory semantics đã được xác nhận.

---

# 53. Không dùng generic như runtime reflection

`T` không tự động tồn tại runtime.

Muốn runtime type metadata:

```text
explicit reflection/materialization
```

---

# 54. Type erasure

Nếu abstraction không cần runtime:

```text
trait
generic
closure
```

có thể bị erase hoàn toàn.

---

# 55. Shared machine implementation

Đề xuất thêm compiler pass:

```text
Generic Implementation Sharing
```

Input:

```text
specialized MIR
```

Output:

```text
shared implementation groups
```

Chỉ share khi:

- calling convention compatible;
- layout compatible;
- behavior identical;
- required alignment compatible;
- target features compatible;
- debug/exception semantics có thể giữ nguyên.

---

# 56. Target feature

Không được share:

```text
AVX2 implementation
```

với:

```text
SSE-only target
```

nếu semantics/performance contract yêu cầu instruction unavailable.

---

# 57. Debug information

Generic specialization phải map được:

```text
source generic function
        ↓
specialized function
        ↓
machine instruction
```

Debugger có thể hiển thị:

```text
foo<i32>
```

thay vì chỉ:

```text
foo.123
```

---

# 58. Mangling

Tên machine symbol có thể encode:

```text
foo$<T=i32>
```

nhưng mangling không phải semantic identity.

Đã freeze từ Module/Name resolution:

> declaration identity độc lập với source spelling/mangling.

---

# 59. Symbol visibility

Generic specialization nội bộ không nên trở thành public symbol chỉ vì linker nhìn thấy nó.

Chỉ:

```text
@export
```

hoặc ABI contract thích hợp mới tạo externally observable symbol.

---

# 60. Weak/COMDAT-like handling

Object writer/linker nên hỗ trợ semantic tương đương:

```text
one canonical specialization
+
deduplicate equivalent generated instances
```

tùy target object format.

---

# 61. Cross-package generic

Nếu package A cung cấp:

```text
Vec<T>
```

package B và C cùng instantiate:

```text
Vec<i32>
```

linker/build system phải tránh duplicate code nếu ABI/link model cho phép.

---

# 62. Nhưng không phụ thuộc linker magic

Compiler nên canonicalize trước.

Linker deduplication chỉ là lớp bổ sung.

---

# 63. Compile-time budget

Axiom nên có configurable limits:

```text
max_trait_depth
max_specialization_depth
max_comptime_steps
max_generated_declarations
```

Không phải semantic differences giữa normal/release.

---

# 64. Release vs debug

Debug có thể:

```text
-O0
```

Release:

```text
-O2/O3
```

nhưng generic semantics giống hệt.

---

# 65. Optimization correctness

Một generic optimization chỉ hợp lệ nếu:

```text
observable semantics(original)
==
observable semantics(optimized)
```

bao gồm:

- ownership;
- Drop;
- panic;
- atomic ordering;
- synchronization;
- volatile;
- FFI;
- observable address.

---

# 66. Address observability

Ví dụ generic abstraction:

```axiom
fn foo<T>(x: T)
```

compiler có thể scalarize `x`.

Nhưng nếu:

```axiom
address_of(x)
```

được dùng trong unsafe/system contract:

storage/address identity trở thành observable.

→ optimization bị giới hạn.

---

# 67. Generic allocation

Không được giả định:

```text
T
```

luôn heap allocated.

Generic type có thể:

```text
register
stack
inline
heap
arena
```

theo storage semantics.

---

# 68. Generic recursion and allocation

Recursive generic data:

```axiom
struct Node<T> {
    value: T,
    next: Option<Box<Node<T>>>
}
```

`Box` cung cấp finite indirection.

Compiler không cần special-case generic recursion.

---

# 69. Generic + `dyn Trait`

Có thể dùng:

```axiom
fn process<T: Trait>(x: T)
```

→ static.

Hoặc:

```axiom
fn process(x: dyn Trait)
```

→ dynamic.

Hai cơ chế rõ ràng.

---

# 70. Không có “magic heuristic” đổi static thành dynamic

Compiler có thể machine-optimize implementation, nhưng không được thay đổi semantic dispatch model nếu điều đó ảnh hưởng observable behavior.

---

# 71. Code-size profile

Có thể cung cấp build policy:

```text
optimize = speed
optimize = size
optimize = balanced
```

Compiler điều chỉnh:

```text
inline
specialization
LTO
outlining
function merging
```

---

# 72. Nhưng không thay đổi source semantics

`optimize=size` không được biến:

```text
static dispatch
```

thành:

```text
dynamic dispatch
```

nếu semantics observable khác.

---

# 73. Generic sharing là optimization

Đây là điểm quan trọng:

```text
Monomorphization
```

là semantic lowering strategy.

```text
Machine implementation sharing
```

là optimization.

Không trộn hai khái niệm.

---

# 74. Pipeline cuối

Từ đây generic pipeline nên là:

```text
Generic Source
      ↓
Resolution
      ↓
Generic Type Checking
      ↓
Trait Constraint Solving
      ↓
Generic Semantic HIR
      ↓
Canonical Generic Fingerprint
      ↓
Specialization Request
      ↓
Concrete Type/Const Arguments
      ↓
Concrete Typed HIR
      ↓
Ownership/Capability/Send/Share Verification
      ↓
MIR
      ↓
Drop Elaboration
      ↓
Semantic Optimization
      ↓
Representation/Layout
      ↓
ABI
      ↓
Machine Optimization
      ↓
Implementation Sharing
      ↓
Object
```

---

# 75. Kết luận kiến trúc

Tôi đề xuất **freeze** hướng generic của Axiom như sau:

> **Axiom sử dụng static generic specialization làm đường mặc định cho zero-cost abstraction, nhưng compiler không bị buộc phải tạo một machine implementation riêng cho mỗi semantic specialization.**

Điều này cho phép:

```text
Rust/C++ style generic expressiveness
              +
AOT native code
              +
aggressive optimization
              +
code deduplication
              +
incremental compilation
```

mà không cần đưa runtime generic metadata vào binary.

---

# BOOTSTRAP-049 — Invariants

```text
AGEN-101  Generic abstraction is compile-time by default.
AGEN-102  Generic parameters do not imply runtime type metadata.
AGEN-103  Static generic dispatch is the default.
AGEN-104  Monomorphization occurs only for required concrete instantiations.
AGEN-105  Canonically identical generic instantiations share specialization identity.
AGEN-106  Specialization identity is independent of machine symbol spelling.
AGEN-107  Generic semantic identity includes generic declaration and canonical arguments.
AGEN-108  Const generic identity includes canonical const arguments.
AGEN-109  Generic semantic verification occurs before machine lowering.
AGEN-110  Generic ownership semantics remain valid after specialization.
AGEN-111  Generic capability semantics remain valid after specialization.
AGEN-112  Generic Send/Share properties remain valid after specialization.
AGEN-113  Generic Drop semantics remain valid after specialization.
AGEN-114  Generic layout is not assumed uniform across type arguments.
AGEN-115  ABI classification occurs after concrete representation analysis.
AGEN-116  Generic FFI export requires concrete ABI-specialized declarations.
AGEN-117  Generic GPU kernels are specialized before GPU lowering.
AGEN-118  Generic async state machines are specialized before final lowering.
AGEN-119  Generic closures preserve capture semantics after specialization.
AGEN-120  Arbitrary overlapping specialization is rejected in Core v1.
AGEN-121  Arbitrary specialization is not required by Core v1.
AGEN-122  Negative trait bounds are not required for generic resolution v1.
AGEN-123  Trait solving is deterministic.
AGEN-124  Specialization IDs are deterministic.
AGEN-125  Parallel specialization cannot alter semantic results.
AGEN-126  Compiler scheduling cannot determine semantic identity.
AGEN-127  Generic cache keys include relevant semantic dependencies.
AGEN-128  Generic cache keys include relevant comptime inputs.
AGEN-129  Semantic and optimization dependencies are distinct.
AGEN-130  Semantic fingerprints are distinct from optimization fingerprints.
AGEN-131  Private implementation changes need not invalidate downstream semantic checking when public semantics remain unchanged.
AGEN-132  Optimization invalidation may occur without semantic invalidation.
AGEN-133  Generic implementation sharing is an optimization, not a semantic type merge.
AGEN-134  Distinct nominal types remain distinct even when machine representations are identical.
AGEN-135  Machine implementation sharing requires compatible representation and ABI semantics.
AGEN-136  Target-feature incompatibility prevents unsafe implementation sharing.
AGEN-137  LTO cannot change observable language semantics.
AGEN-138  LTO cannot invalidate explicit exports.
AGEN-139  LTO cannot invalidate FFI contracts.
AGEN-140  Dynamic dispatch is explicit and is not an implicit generic fallback.
AGEN-141  Generic specialization does not imply heap allocation.
AGEN-142  Generic specialization does not imply object headers.
AGEN-143  Generic specialization does not imply runtime reflection.
AGEN-144  Generic code does not bypass ownership or capability verification.
AGEN-145  Generic code does not bypass concurrency verification.
AGEN-146  Generic code does not bypass GPU legality verification.
AGEN-147  Generic code does not bypass FFI verification.
AGEN-148  Generic recursive instantiation must terminate or produce a diagnostic.
AGEN-149  Compiler resource limits cannot silently alter program semantics.
AGEN-150  Generic diagnostics expose declaration, instantiated arguments and failed constraints.
AGEN-151  Generated generic declarations use canonical semantic identity.
AGEN-152  Derived generic implementations are deduplicated.
AGEN-153  Cross-package generic instantiations are canonicalized where compatible.
AGEN-154  Link-time deduplication is supplemental to compiler specialization deduplication.
AGEN-155  Debug metadata preserves generic source-to-specialization mapping.
AGEN-156  Symbol mangling does not define generic semantic identity.
AGEN-157  External visibility does not follow merely from generic instantiation.
AGEN-158  Code-size optimization cannot silently replace explicit dispatch semantics.
AGEN-159  Optimization level cannot change generic semantic behavior.
AGEN-160  Generic abstractions may be fully erased when unobservable.
```

---

## Trạng thái sau 049

Axiom hiện đã có một đặc tính rất đáng giá:

```text
                    Axiom
                      │
        ┌─────────────┴─────────────┐
        │                           │
   Programmer sees             Compiler sees
        │                           │
 simple ownership             ownership graph
 simple views                 capability graph
 traits                       trait constraints
 async/await                  state machine
 generic<T>                   specialization graph
 Vec/Box/etc.                 storage semantics
        │                           │
        └──────────→ MIR ←──────────┘
                         │
                   optimization
                         │
                 representation
                         │
                       ABI
                         │
                    machine code
```

Tức là **độ phức tạp được đẩy vào compiler chứ không đẩy sang cú pháp/lập trình viên** — đúng hướng mà chúng ta đã thống nhất.

### BOOTSTRAP-050 tiếp theo

Phần tiếp theo nên khóa **Axiom Execution & Optimization Model**:

```text
BOOTSTRAP-050
CPU execution
+
instruction selection
+
alias analysis
+
escape analysis
+
inlining
+
vectorization
+
loop optimization
+
LTO
+
PGO
+
cache/locality optimization
+
branch optimization
+
atomic optimization
+
SIMD
+
zero-cost abstraction verification
```

Đây sẽ là phần quyết định liệu mục tiêu **“nhanh bằng hoặc hơn C/C++ trong các workload phù hợp”** có được biến thành các invariant/compiler requirements cụ thể hay chỉ là khẩu hiệu.