# BOOTSTRAP-120 — Semantic Type System & Trait Solver Implementation Contract

**Trạng thái: FROZEN / COMPLETED**

Mục tiêu của task này là khóa type system đủ mạnh để xây Axiom thật, nhưng **không biến Axiom thành một theorem prover**.

Nguyên tắc:

> **Type system phải giải quyết các vấn đề lập trình thực tế; những gì không cần để compile chương trình thì không đưa vào type system.**

---

# 1. Type system architecture

Pipeline:

```text
AST Type Syntax
      ↓
Name Resolution
      ↓
Type Construction
      ↓
Type Inference
      ↓
Constraint Generation
      ↓
Trait Solving
      ↓
Associated Item Resolution
      ↓
Type Normalization
      ↓
Type Checking
      ↓
Typed HIR
```

---

# 2. Type categories

Axiom v0.1 có các nhóm:

```text
Primitive
Struct
Enum
Tuple
Array
Function
Closure
Trait
Dyn Trait
Generic Parameter
Type Alias
Newtype
View
MutView
Raw Pointer
Never
Unit
```

---

# 3. Nominal vs structural typing

Axiom chọn:

> **Nominal typing cho user-defined types.**

Ví dụ:

```ax id="4k2f7u"
struct Meter(f64);
struct Second(f64);
```

Hai type này khác nhau dù representation giống nhau.

```text id="c2w2v7"
Meter ≠ Second
```

Điều này ngăn nhiều lỗi đơn vị/semantic.

---

# 4. Type alias

```ax id="g4f4de"
type UserId = u64;
```

là alias:

```text id="c6j3pn"
UserId == u64
```

Không tạo type identity mới.

Nếu cần type mới:

```ax id="m6y6ph"
struct UserId(u64);
```

---

# 5. Newtype

Newtype:

```ax id="2g8j6y"
struct UserId(u64);
```

có:

```text id="2c7k3m"
distinct type identity
```

nhưng có thể:

```text id="b5klk4"
@repr(transparent)
```

để có ABI representation tương thích khi cần.

---

# 6. Type identity

Compiler không so sánh type bằng source string.

```text id="w9osqy"
TypeId
```

là identity chính.

TypeDB canonicalizes:

```text id="1s9p9p"
Vec<i32>
Vec<i32>
Vec<i32>
```

thành cùng semantic type.

---

# 7. Type interning

TypeDB dùng interning:

```text id="w8nqkp"
TypeId = intern(TypeStructure)
```

Ví dụ:

```text id="2evkz6"
Vec<i32>
```

có một canonical TypeId trong CompilerDB revision.

Lợi ích:

- nhanh equality;
- giảm memory;
- cache trait solver;
- cache generic instantiation;
- incremental compilation.

---

# 8. Primitive types

Core:

```text id="m86z4h"
bool
i8 i16 i32 i64
u8 u16 u32 u64
isize usize
f32 f64
unit
never
```

Type identity target-independent về mặt semantics.

Physical representation do target quyết định.

---

# 9. Type properties

Compiler không coi mọi property là trait lookup bình thường.

Các property nền:

```text id="q8h6yt"
Copy
Drop
Send
Share
Sized
FFI-safe
GPU-legal
```

được compiler derive/verify theo semantic rules.

Một số có thể biểu diễn bằng trait-like interfaces ở stdlib, nhưng compiler vẫn có intrinsic knowledge khi cần.

---

# 10. Copy

`Copy` là semantic property:

> duplication không tạo thêm ownership obligation.

Ví dụ:

```ax id="n2bgq7"
struct Point {
    x: f32,
    y: f32,
}
```

có thể được derive:

```ax id="d3bqxs"
@derive(Copy)
```

nếu mọi field thỏa điều kiện.

---

# 11. Copy không đồng nghĩa bitwise copy

Đây là invariant:

```text id="g1kh7q"
semantic Copy
≠
memcpy-safe
```

Một type có thể có representation phức tạp nhưng vẫn có Copy semantics được định nghĩa.

Ngược lại, một type có thể bitwise movable nhưng không được coi là `Copy`.

---

# 12. Drop

Type có Drop obligation:

```text id="y9n4qy"
Drop(T) = true
```

thì:

```text id="9c7f0a"
Copy(T) = false
```

trừ khi specification trong tương lai định nghĩa một semantic đặc biệt khác.

v0.1 không có ngoại lệ.

---

# 13. Send

`Send<T>`:

> ownership của `T` có thể được chuyển sang execution domain khác theo concurrency model.

Compiler derive recursively.

Ví dụ:

```text id="g9u3qz"
struct A {
    x: i32,
}
```

`A` có thể Send.

Nhưng:

```text id="s5j3hr"
Rc<T>
```

không tự động Send.

---

# 14. Share

`Share<T>`:

> `T` có thể được shared-access giữa execution domains theo contract của type.

Không đồng nghĩa mutable thread safety.

Ví dụ:

```text id="f2l1aq"
Arc<T>
```

có thể quản lý shared ownership, nhưng `T` bên trong vẫn phải đáp ứng access/synchronization requirements tương ứng.

---

# 15. Send và Share độc lập

Các tổ hợp hợp lệ:

```text id="3p4h6e"
Send
!Share

Share
!Send

Send + Share

!Send + !Share
```

Compiler không suy luận một property từ property kia nếu specification không cho phép.

---

# 16. Sized

`Sized<T>` cho biết type có kích thước compile-time xác định trong execution context tương ứng.

Các type như:

```text id="ynb3vn"
dyn Trait
Str
```

có thể là dynamically sized semantic categories.

Nhưng chúng không nhất thiết phải mang runtime object header.

---

# 17. View types

```text id="yxwwqi"
view<T>
mut_view<T>
```

không phải ordinary ownership types.

Compiler xem chúng như capability-bearing types.

Properties quan trọng:

```text id="9hmb1g"
non-owning
provenance-bearing
lifetime-constrained
```

---

# 18. View covariance

Không đưa vào v0.1 một hệ thống variance tổng quát quá phức tạp.

Quy tắc:

> `view<T>` và `mut_view<T>` được kiểm soát bởi capability conversion rules, không bởi một hệ thống variance tự do.

Ví dụ owner → read view được compiler tạo trong context hợp lệ.

---

# 19. Function types

```ax id="h9d1ku"
fn(i32, i32) -> i32
```

là type của callable không capture environment.

Capturing closure là distinct compiler-generated type.

---

# 20. Closure types

Mỗi closure expression tạo một anonymous semantic type:

```text id="38xjwm"
ClosureTypeId
```

Hai closure:

```ax id="w7d4yp"
|x| x + 1
|x| x + 1
```

không mặc định cùng type.

---

# 21. Closure coercion

Noncapturing closure có thể chuyển thành:

```text id="2u3xhe"
fn(...)
```

nếu signature tương thích.

Capturing closure không được tự động mất environment.

---

# 22. Trait model

Trait:

```ax id="xgk7bo"
trait Ord {
    fn compare(...);
}
```

là compile-time behavior contract.

Trait không mặc định là runtime interface.

---

# 23. Trait implementation

```ax id="z8y6c2"
impl Ord for MyType {
    ...
}
```

Compiler tạo semantic:

```text id="82l9n4"
ImplId
TraitId
SelfType
AssociatedItems
WhereConstraints
```

---

# 24. Trait candidate

Trait solver không tìm kiếm vô hạn.

Candidate sources:

```text id="t3ey7n"
1. inherent facts
2. explicit impls
3. builtin/compiler facts
4. where constraints
5. supertraits
6. generic constraints
```

Không có arbitrary runtime reflection.

---

# 25. Trait goal

Mỗi query có dạng conceptually:

```text id="8djg1x"
Goal:
    Type T implements Trait X
```

hoặc:

```text id="7m6y4x"
Goal:
    AssociatedType(T, X::Item) == U
```

---

# 26. Solver result

Chỉ có bốn trạng thái chính:

```text id="xzhk69"
Proven
NotProven
Ambiguous
Error
```

`Ambiguous` không được tự động coi là false.

---

# 27. Trait solver algorithm

Khuyến nghị v0.1:

```text id="c7o8t1"
canonicalize goal
        ↓
lookup cache
        ↓
collect candidates
        ↓
unify candidate
        ↓
solve where-constraints
        ↓
normalize associated items
        ↓
prove candidate
        ↓
select unique result
```

Không dùng theorem proving tổng quát.

---

# 28. Unification

Type variables:

```text id="0t4w9h"
T0
T1
...
```

có thể được unify.

Ví dụ:

```text id="11ex0s"
Vec<T0>
=
Vec<i32>
```

→

```text id="8r7h2g"
T0 = i32
```

---

# 29. Occurs check

Không cho:

```text id="5w8j0r"
T = Vec<T>
```

vì tạo infinite type.

Compiler phải reject deterministic.

---

# 30. Type normalization

Ví dụ:

```text id="zq2m4r"
<T as Iterator>::Item
```

phải được normalize nếu compiler chứng minh được associated type.

Ví dụ:

```text id="c6x3s8"
Iterator for Vec<i32>
Item = i32
```

thì:

```text id="8pp1k2"
<T as Iterator>::Item
```

→ `i32`.

---

# 31. Associated types

Axiom hỗ trợ:

```ax id="x2e7n3"
trait Iterator {
    type Item;
}
```

Implementation:

```ax id="a5n7cx"
impl Iterator for MyIter {
    type Item = i32;
}
```

---

# 32. Associated constants

```ax id="0dfn4s"
trait Numeric {
    const ZERO: Self;
}
```

Associated constant resolution phải deterministic.

---

# 33. Associated functions

```ax id="tq2x8h"
trait Factory {
    fn create() -> Self;
}
```

Có thể gọi:

```ax id="xg2q6c"
MyType::create()
```

nếu resolution xác định được implementation.

---

# 34. Supertraits

```ax id="q6m8za"
trait Ordered: Comparable {
    ...
}
```

Impl `Ordered` phải satisfy `Comparable`.

Compiler tạo implication:

```text id="k3x6a0"
Ordered(T)
→ Comparable(T)
```

---

# 35. Trait cycles

Ví dụ:

```text id="pq5k6v"
A: B
B: A
```

phải phát hiện cycle.

Không để solver recurse vô hạn.

Diagnostic:

```text id="4g0b1a"
ETRAIT_CYCLE
```

---

# 36. Solver recursion limit

Axiom không cho phép trait solver recurse vô hạn.

Có:

```text id="q2f1yv"
maximum depth
query budget
```

Nếu vượt:

```text id="f4o2ct"
ETRAIT_OVERFLOW
```

Đây là compiler error, không phải compiler crash.

---

# 37. Solver memoization

Query:

```text id="n2a9q5"
(T, Trait, Environment)
```

được canonicalize và cache.

Ví dụ:

```text id="w1v2sm"
Vec<i32>: Clone
```

được query một lần rồi reuse.

---

# 38. Parallel trait solving

Các independent goals:

```text id="7q2e6g"
T: Clone
U: Send
V: Ord
```

có thể solve song song.

CompilerDB query engine quản lý synchronization.

---

# 39. Coherence

Axiom cần đảm bảo một trait implementation không trở nên ambiguous tùy package import order.

Nguyên tắc:

> **Một `(Trait, Type)` pair phải có implementation resolution deterministic trong một coherent dependency universe.**

---

# 40. Orphan rule

v0.1 dùng quy tắc đơn giản:

Một package chỉ được implement trait cho type nếu package đó sở hữu ít nhất một trong:

```text id="j0i8n8"
trait
type
```

Ví dụ package A:

```text
trait MyTrait {}
```

package B không thể tùy ý:

```text id="f0h2bx"
impl MyTrait for ExternalType
```

nếu B không sở hữu trait hoặc type.

---

# 41. Vì sao cần orphan rule

Nếu không:

```text id="0b5lmy"
Package A → impl Trait X for Type Y
Package B → impl Trait X for Type Y
```

thì package composition có thể thay đổi semantics của program.

Axiom không cho phép điều này.

---

# 42. Specialization

Không có arbitrary specialization trong v0.1.

Không cho phép:

```ax id="5d8x9a"
impl<T> Trait for T
impl Trait for i32
```

nếu overlap không được compiler chứng minh hợp lệ theo specialization rules.

---

# 43. Recommended specialization model

Nếu cần specialization:

```text id="2i9x7c"
default impl
    ↓
explicit more-specific impl
```

nhưng phải có hierarchy/compiler proof rõ ràng.

Không dùng “compiler tự chọn implementation cụ thể hơn”.

---

# 44. Generic dispatch

Mặc định:

```text id="12e1fr"
static dispatch
```

Compiler có thể:

```text id="2z4s1k"
monomorphize
specialize
devirtualize
```

---

# 45. Generic code sharing

Không bắt buộc mỗi generic instance tạo một binary copy.

Compiler có thể:

```text id="7o0t8m"
share code
```

khi ABI/representation cho phép.

Do đó:

```text id="3q3rpx"
generic abstraction
```

không đồng nghĩa binary bloat.

---

# 46. `dyn Trait`

Dynamic dispatch explicit:

```ax id="x6o9j2"
dyn Drawable
```

Semantic type có:

```text id="t5h6ba"
TraitId
```

Representation có thể:

```text id="6j9k9d"
data pointer + vtable
```

nhưng đây là representation detail.

---

# 47. Object safety

Không phải trait nào cũng có thể dùng:

```text id="6v1x3e"
dyn Trait
```

Compiler phải kiểm tra object safety.

Các trường hợp generic method/self-return khó biểu diễn dynamic dispatch phải bị reject hoặc yêu cầu explicit alternative.

---

# 48. Dynamic dispatch overhead

Axiom không tự động biến:

```ax id="8n1a4p"
fn draw<T: Drawable>(x: view<T>)
```

thành vtable call.

Static generic dispatch giữ direct target nếu possible.

`dyn Drawable` mới yêu cầu dynamic dispatch.

---

# 49. Operators

Operator resolution đi qua trait/compiler builtin.

Ví dụ:

```ax id="w0e1os"
a + b
```

→ candidate `Add`.

Nhưng primitive arithmetic có thể được compiler lower trực tiếp mà không cần materialize trait call.

---

# 50. Type properties và solver

Một query như:

```text id="s1h4zq"
IsCopy(T)
```

không nhất thiết đi qua ordinary user trait machinery.

Compiler có thể có:

```text id="9c5a5f"
BuiltinPropertyQuery
```

Điều này tránh recursive trait complexity.

---

# 51. Copy derivation

Struct:

```ax id="7g6f3j"
struct Pair<T> {
    a: T,
    b: T,
}
```

Copy iff:

```text id="r4x6hz"
Copy(T)
```

và không có Drop violation.

---

# 52. Drop derivation

Derived Drop recursively follows fields.

```text id="i6s7qp"
Drop(Pair<T>) =
    Drop(T)
```

Custom Drop changes rules:

```text id="2h9h1x"
partial move restrictions
```

---

# 53. Send derivation

```text id="v4o2t0"
Send(Pair<T>) =
    Send(T)
```

nếu tất cả components cần thiết đều Send.

Compiler phải tính cả hidden state của:

- closures;
- futures;
- trait objects;
- storage handles.

---

# 54. Share derivation

Tương tự:

```text id="9kg6zn"
Share(Pair<T>) =
    Share(T)
```

nhưng shared mutable semantics vẫn do capability/synchronization contract.

---

# 55. GPU legality

`GpuLegal<T>` không đơn giản là Send.

Một type có thể:

```text id="w0m0o9"
Send = true
GPU legal = false
```

Ví dụ type chứa:

```text id="f6r4i3"
File
Socket
OS handle
```

---

# 56. FFI safety

`FFISafe<T>` là property riêng.

Ví dụ:

```text id="m2t7cw"
u32 → FFI-safe
```

nhưng:

```text id="n8q6a0"
Vec<u32> → not automatically FFI-safe
```

---

# 57. Type checking

Type checker kiểm tra:

```text id="w0y2j9"
assignment
call arguments
return
operator
field
index
pattern
match
generic instantiation
trait bounds
casts
closures
async
FFI
```

---

# 58. No implicit conversion graph

Đây là quyết định quan trọng.

Compiler **không** tìm đường:

```text id="6sx7lh"
A → B → C → D
```

để làm call compile.

Chỉ conversion được specification cho phép.

Điều này giúp:

- diagnostics tốt;
- compile nhanh;
- overload deterministic;
- AI dễ suy luận.

---

# 59. Type mismatch diagnostic

Ví dụ:

```ax id="ph9z9h"
fn foo(x: i32) {}
foo("hello");
```

Diagnostic nên structured:

```text id="5s0c8v"
ETYPE_MISMATCH

expected: i32
found: Str

at argument #1
required by: foo(i32)
```

Compiler có thể thêm machine-readable JSON.

---

# 60. Trait diagnostic

Ví dụ:

```ax id="w8fj78"
sort(items)
```

nếu `T: Ord` thiếu:

```text id="1xk9n4"
ETRAIT_NOT_IMPLEMENTED

required:
    T: Ord

because:
    sort<T: Ord>(...)
```

Không chỉ báo:

```text
"trait bound not satisfied"
```

một cách mơ hồ.

---

# 61. Error provenance

Mỗi constraint phải giữ:

```text id="f4r5u2"
SourceSpan
origin
parent constraint
```

Ví dụ:

```text id="5ow8c4"
T: Clone
```

đến từ function generic nào, argument nào, associated type nào.

---

# 62. AI-friendly trait explanation

Compiler có thể trả:

```text id="g3n8qk"
Goal:
    Vec<MyType>: Sortable

Required:
    MyType: Ord

Known:
    MyType: Clone
    MyType: Send

Missing:
    MyType: Ord

Candidate impls:
    none
```

Điều này cực kỳ phù hợp mục tiêu AI-assisted development.

---

# 63. Type inference philosophy

Axiom cho phép inference ở nơi **an toàn và dễ dự đoán**.

Ví dụ:

```ax id="a2k1ct"
let x = Vec<i32>();
```

hoặc:

```ax id="p8v3yk"
let x = 10;
```

Nhưng không cố inference mọi thứ như một theorem prover.

---

# 64. Explicit type escape hatch

Programmer có thể luôn viết:

```ax id="p3w8ns"
let x: MyType = expression;
```

để giới hạn inference.

Diagnostics có thể đề xuất insertion.

---

# 65. Generic inference

Call:

```ax id="2kq2la"
identity(42)
```

có thể infer:

```text id="7b2p4x"
T = i32
```

nếu literal/context đủ xác định.

---

# 66. Ambiguous inference

Nếu:

```ax id="5w2k0d"
foo()
```

có nhiều possible generic instances:

```text id="t3v7gd"
ETYPE_INFERENCE_AMBIGUOUS
```

Compiler không tự chọn dựa trên arbitrary default nếu không có language rule.

---

# 67. Default literal types

Để tránh ambiguity vô ích, Axiom có default literal policy.

Ví dụ integer literal không có contextual type có thể mặc định:

```text id="8q7gak"
i32
```

trừ khi value không fit hoặc context chỉ rõ type khác.

Floating literal:

```text id="2g1j3b"
f64
```

Đây là defaulting rule, không phải implicit conversion.

---

# 68. Trait solver termination

Trait solver phải có:

```text id="0m1q4d"
depth limit
query cycle detection
memoization
candidate limit where necessary
```

Một program làm solver quá phức tạp phải nhận diagnostic.

Compiler không được:

```text id="xk3s7e"
hang indefinitely
```

---

# 69. No general dependent types

v0.1 không hỗ trợ:

```text id="a4q1fh"
type-level arbitrary arithmetic
proof types
dependent pattern indices
```

Const generic chỉ giới hạn scalar types được specification cho phép.

---

# 70. Type-level computation

Compile-time computation có thể tạo type information qua:

```text id="0k9m6g"
comptime
derive
const parameters
```

nhưng kết quả phải trở thành compiler-known type structure.

Không biến Axiom thành dependent theorem language.

---

# 71. Trait solver cache key

Conceptually:

```text id="v2u6t5"
TraitQueryKey {
    Goal
    ParamEnvironment
    CompilerSemanticVersion
}
```

Generic inference state phải canonicalize.

Cache không được phụ thuộc source formatting.

---

# 72. Incremental invalidation

Nếu implementation private thay đổi nhưng public trait contract không đổi:

```text id="8m3q0x"
downstream trait resolution
```

không nhất thiết phải invalidate toàn bộ.

Public semantic fingerprint quyết định dependency invalidation.

---

# 73. Parallelism

Có thể parallelize:

```text id="0f8d9r"
type checking independent functions
trait queries
generic instantiations
```

nhưng deterministic result bắt buộc.

---

# 74. Trait solver architecture

Chốt:

```text id="m0x4p9"
TraitSolver
│
├── GoalCanonicalizer
├── QueryCache
├── CandidateIndex
├── Unifier
├── ConstraintEngine
├── AssociatedTypeNormalizer
├── CycleDetector
├── CoherenceChecker
├── SpecializationChecker
└── DiagnosticExplainer
```

Không có theorem prover tổng quát.

---

# 75. Type engine architecture

```text id="5f2h4j"
TypeEngine
│
├── TypeInterner
├── TypeUnifier
├── TypeNormalizer
├── LiteralTyper
├── GenericSubstituter
├── TypePropertyEngine
├── TraitSolver
├── CoherenceChecker
└── TypeDiagnostics
```

---

# 76. Type property engine

Một interface thống nhất:

```text id="t5o5sf"
query_property(TypeId, Property)
```

Properties:

```text id="7m7f2v"
Copy
Drop
Send
Share
Sized
FFISafe
GPULegal
```

Kết quả:

```text id="6p7f0g"
Proven
Disproven
Unknown
Error
```

`Unknown` khác `Disproven`.

---

# 77. Why `Unknown` matters

Compiler có thể chưa đủ information vì generic:

```ax id="h1w5d2"
fn foo<T>(x: T) {
    ...
}
```

Tại definition site:

```text id="z9q1f4"
Copy(T) = Unknown
```

Không được coi là false.

Nếu code cần Copy:

```ax id="5g6x4p"
fn foo<T: Copy>(...)
```

constraint giải quyết được.

---

# 78. Generic property constraints

Programmer có thể yêu cầu:

```ax id="8q8qj2"
fn duplicate<T: Copy>(x: T) -> (T, T)
```

hoặc:

```ax id="5m0q0c"
fn transfer<T: Send>(x: T)
```

Những property này dùng cùng trait-bound syntax.

Compiler có builtin knowledge về semantics.

---

# 79. Trait implementation ownership

Axiom giữ coherence xuyên package graph.

Dependency resolution phải hoàn thành trước coherence checking.

Không có “import thêm package là method resolution ngẫu nhiên đổi”.

---

# 80. Type system boundary

Type system **không chịu trách nhiệm** cho:

```text id="2x4b3d"
physical layout
register allocation
instruction selection
allocation strategy
cache locality
```

Những việc này thuộc later compiler stages.

---

# 81. Type system cũng không chịu trách nhiệm hoàn toàn cho ownership

Type system nói:

```text id="j3g7n2"
T
Copy(T)
Drop(T)
Send(T)
```

Ownership verifier mới quyết định:

```text id="x1f5h9"
local x = MOVED
capability active
drop conflict
partial move
```

Đây là separation rất quan trọng.

---

# 82. Final semantic pipeline

Sau task 120:

```text id="s1q5lw"
AST
 ↓
Resolution
 ↓
HIR
 ↓
Type inference
 ↓
Trait solving
 ↓
Type normalization
 ↓
Typed HIR
 ↓
Ownership / Capability analysis
 ↓
MIR
```

Không còn unresolved type/trait semantics trước khi MIR chính thức.

---

# 83. Invariants chính

### `ATYPE-80`
User-defined types are nominal.

### `ATYPE-81`
Type aliases do not create new nominal identity.

### `ATYPE-82`
Newtypes create distinct semantic identity.

### `ATYPE-83`
Types are canonicalized through TypeDB.

### `ATYPE-84`
Trait resolution is deterministic.

### `ATYPE-85`
Trait ambiguity is never resolved by implementation accident.

### `ATYPE-86`
Trait solver terminates through cycle detection and bounded recursion.

### `ATYPE-87`
Trait queries are memoizable.

### `ATYPE-88`
Independent trait queries may execute in parallel.

### `ATYPE-89`
Unknown is distinct from false.

### `ATYPE-90`
No implicit conversion chain is used for type checking.

### `ATYPE-91`
Copy is a semantic property.

### `ATYPE-92`
Drop and Copy are mutually incompatible in Core v0.1.

### `ATYPE-93`
Send and Share are independent properties.

### `ATYPE-94`
FFI-safe and GPU-legal are independent properties.

### `ATYPE-95`
Generic abstraction does not imply dynamic dispatch.

### `ATYPE-96`
Dynamic dispatch is explicit.

### `ATYPE-97`
Associated types are normalized deterministically.

### `ATYPE-98`
Coherence is independent of import order.

### `ATYPE-99`
Orphan rules prevent uncontrolled foreign implementations.

### `ATYPE-100`
Arbitrary overlapping specialization is not permitted.

### `ATYPE-101`
Type checking does not depend on physical representation.

### `ATYPE-102`
Trait solving does not require runtime reflection.

### `ATYPE-103`
Type diagnostics preserve constraint provenance.

### `ATYPE-104`
Type errors are structured and machine-readable.

### `ATYPE-105`
Type inference must remain bounded and deterministic.

### `ATYPE-106`
Axiom does not require general dependent type theory.

### `ATYPE-107`
The compiler may optimize generic representations without changing type semantics.

---

# BOOTSTRAP-120 hoàn tất

Axiom giờ đã có ba lớp semantic cực kỳ quan trọng:

```text
┌──────────────────────────────┐
│ Surface Syntax               │
│ BOOTSTRAP-118               │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ AST / HIR                    │
│ BOOTSTRAP-119               │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Type / Trait System          │
│ BOOTSTRAP-120               │
└──────────────┬───────────────┘
               ↓
        Typed HIR
```

Và từ đây, compiler bắt đầu đi vào phần khó nhất về **correctness**:

# BOOTSTRAP-121 — Ownership, Capability & Lifetime Inference Engine

Task tiếp theo sẽ thiết kế **engine mà Axiom dùng để đạt được điều Rust muốn đạt được nhưng không bắt programmer viết borrow/lifetime syntax**.

Nó sẽ khóa:

```text
OwnershipState
CapabilityState
PlaceTree
Region
Provenance
Lifetime inference
Escape analysis
Move analysis
Partial move
Drop analysis
View validity
mut_view exclusivity
Alias analysis
Relocation barriers
Closure captures
Async suspension
Send/Share
FFI escape
GPU storage
Unsafe trusted boundaries
```

Đặc biệt sẽ thiết kế thuật toán để compiler có thể tự suy luận:

```ax
fn process(data: view<Data>) { ... }

fn main() {
    var x = Data::new();

    process(x);

    x.modify();
}
```

mà programmer **không cần** viết lifetime, borrow hoặc pointer annotation.

Đây sẽ là một trong những thành phần cốt lõi nhất của Axiom, vì nó quyết định liệu mục tiêu **“safety mạnh nhưng syntax đơn giản hơn Rust”** có thực sự khả thi hay không.