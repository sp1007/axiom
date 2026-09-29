# BOOTSTRAP-242 — AXIOM CONVERSION, COERCION & CALLABLE RESOLUTION ENGINE

**TRẠNG THÁI: FROZEN / COMPLETED**

Task này là phần hoàn thiện trực tiếp sau Type Inference. Mục tiêu là giải quyết một vấn đề rất quan trọng của Axiom:

> **Compiler phải tự tìm ra cách dùng type đúng trong context, nhưng không được tự ý biến đổi semantic của chương trình.**

Vì vậy cần phân biệt tuyệt đối:

```text
Coercion
Cast
Conversion
Bitcast
Operator Resolution
Method Resolution
Callable Resolution
```

---

# 1. Kiến trúc tổng thể

```text
                 Expression
                     │
                     ▼
                Type Inference
                     │
                     ▼
              Candidate Discovery
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
      Coercion      Trait      Generic
          │          │          │
          └──────────┼──────────┘
                     ▼
               Candidate Set
                     │
                     ▼
               Ranking/Selection
                     │
              ┌──────┴──────┐
              ▼             ▼
          Unique          Ambiguous
              │             │
              ▼             ▼
         Typed HIR        Diagnostic
```

---

# 2. Bốn loại biến đổi

Axiom v1 phân biệt:

```text
1. Coercion
2. Cast
3. Conversion
4. Bitcast
```

Đây không phải bốn tên cho cùng một cơ chế.

---

# 3. Coercion

Coercion là biến đổi **compiler tự chèn** khi semantic preservation được định nghĩa rõ.

Ví dụ:

```axiom
fn print(x: Str) { ... }

let s = "hello"
print(s)
```

Compiler có thể biểu diễn:

```text
StringLiteral
    ↓
Coerce
    ↓
Str
```

---

# 4. Coercion không tạo ownership mới

Ví dụ:

```axiom
fn read(x: view<u8>) { ... }

let buffer = ...
read(buffer)
```

Coercion:

```text
buffer
 ↓
ephemeral view<u8>
```

không tạo owner mới.

Capability verifier sau đó kiểm tra lifetime.

---

# 5. Coercion whitelist

Axiom **không có arbitrary implicit conversion**.

Core v1 chỉ có những coercion được specification định nghĩa.

Nhóm chính:

```text
T → view<T>
T → mut_view<T>       nếu context/proof hợp lệ
mut_view<T> → view<T>
Array<T,N> → view<T>
never → T
```

và các coercion semantic khác được explicitly frozen.

---

# 6. Coercion phải bảo toàn semantics

Compiler không được dùng coercion để:

```text
copy expensive object
allocate heap
invoke arbitrary user code
throw exception
perform I/O
```

trừ khi một coercion cụ thể được specification định nghĩa rõ như vậy.

Mục tiêu:

> implicit coercion phải gần như “không tồn tại” sau lowering.

---

# 7. Coercion vs From/Into

```axiom
let x: String = value.into()
```

là trait-based conversion.

Trong khi:

```axiom
print(string)
```

với `print(Str)` có thể dùng coercion.

Không được biến mọi `From<T>` thành implicit coercion.

---

# 8. Numeric literal không phải numeric coercion

```axiom
let x: i64 = 42
```

`42` được type-check trực tiếp thành `i64`.

Không phải:

```text
i32
 ↓
i64
```

Điều này tránh tạo implicit numeric conversion chain.

---

# 9. Numeric variable conversion

```axiom
let x: i32 = 42
let y: i64 = x
```

→ lỗi.

Phải:

```axiom
let y = x as i64
```

Semantic cast rõ ràng.

---

# 10. Cast

`as` là primitive explicit conversion.

```axiom
let x = value as u64
```

Compiler xác định một cast rule cụ thể.

Không chạy arbitrary trait resolution để giải thích `as`.

---

# 11. Cast có semantic contract

Ví dụ:

```text
i32 → i64
```

có semantics rõ.

Nhưng:

```text
f64 → i32
```

phải có defined behavior:

- truncation;
- saturation;
- checked trap;
- hoặc semantics khác được Core quy định.

Không được để behavior phụ thuộc backend.

---

# 12. Bitcast

Bitcast khác cast.

```text
CAST:
semantic value A
        ↓
semantic value B

BITCAST:
bits A
  ↓
bits B
```

Bitcast chỉ hợp lệ nếu representation contract cho phép.

---

# 13. Bitcast không được bypass validity

Ví dụ compiler không được cho:

```text
bitcast arbitrary bytes → valid User
```

chỉ vì `sizeof` bằng nhau.

Phải chứng minh representation hợp lệ.

---

# 14. Conversion trait

Standard library cung cấp:

```text
From<T>
Into<T>
TryFrom<T>
TryInto<T>
```

Conceptually:

```text
From<T>
    ↓
infallible semantic conversion

TryFrom<T>
    ↓
fallible semantic conversion
```

---

# 15. Không chain conversion tùy ý

Compiler không được biến:

```text
A → B → C → D
```

chỉ để làm:

```text
foo(D)
```

nếu programmer không yêu cầu.

Nếu cần:

```axiom
let d = a.to_b().to_c().to_d()
```

hoặc API tương đương.

---

# 16. Tại sao không cho implicit conversion chain?

Nếu cho:

```text
A → B
B → C
C → D
```

compiler sẽ phải giải graph.

Kết quả có thể:

```text
multiple paths
ambiguous path
unexpected allocation
unexpected function call
performance surprises
```

Điều này trái với triết lý Axiom.

---

# 17. Conversion cost

Axiom không dùng một hệ thống “conversion cost” vô hạn.

Thay vào đó candidate resolution dùng **finite ordered classes**.

Ví dụ:

```text
Class 0 = exact
Class 1 = canonical coercion
Class 2 = generic instantiation
```

Trait-based conversion không tự động chen vào candidate resolution trừ khi API/operation yêu cầu.

---

# 18. Exact match

Ví dụ:

```axiom
fn foo(x: i32)

foo(10)
```

`10` có thể infer trực tiếp thành `i32`.

→ exact.

---

# 19. Canonical coercion

```axiom
fn read(x: Str)

let s: String = ...
read(s)
```

→ owner-to-ephemeral-view coercion.

Candidate vẫn là một exact callable.

Coercion được materialize bên trong argument.

---

# 20. Coercion không làm thay đổi candidate identity

Ví dụ:

```text
foo(String)
foo(Str)
```

và argument:

```text
String
```

Nếu cả hai tồn tại trong một cơ chế candidate hợp lệ thì compiler không được giả định rằng `String → Str` tự động làm `foo(Str)` thắng.

Vì vậy Axiom tránh overload kiểu này ngay từ Core.

---

# 21. Function overload

Axiom v1 **không hỗ trợ arbitrary same-name overload**.

Do đó:

```axiom
fn foo(i32)
fn foo(f64)
```

không thể cùng tồn tại như hai ordinary functions chỉ dựa vào signature.

Điều này làm resolver cực kỳ deterministic.

---

# 22. Generic thay overload

Thay vì:

```text
foo(i32)
foo(f64)
foo(String)
```

dùng:

```axiom
fn foo<T: SomeTrait>(x: T)
```

hoặc các function có tên khác nhau nếu semantics thực sự khác.

---

# 23. Operator là trường hợp đặc biệt

Operator vẫn cần resolution:

```axiom
a + b
```

nhưng đây không phải arbitrary function overload.

Semantic model:

```text
a + b
 ↓
Add operation
 ↓
Trait Solver
 ↓
selected implementation
```

---

# 24. Operator resolution pipeline

```text
a + b
 │
 ├── infer type(a)
 ├── infer type(b)
 │
 ▼
Add<A,B>
 │
 ▼
Candidate trait implementations
 │
 ▼
Generic substitution
 │
 ▼
Trait solving
 │
 ▼
Result type
```

---

# 25. Operand type trước operator

Không được:

```text
+
 ↓
guess implementation
 ↓
infer operands
```

Mà:

```text
operands
 ↓
type constraints
 ↓
operator candidates
```

---

# 26. Binary operator

Conceptually:

```text
a + b
```

có semantic identity:

```text
Add::add(a, b)
```

nhưng Typed HIR nên lưu **Operator/Impl identity**, không nhất thiết rewrite source thành ordinary function call.

Điều này giúp diagnostics giữ được source semantics.

---

# 27. Arithmetic operator

Các operator như:

```text
+
-
*
/
%
```

có trait-based semantics hoặc compiler-known primitive semantics.

Primitive implementations được compiler biết trực tiếp.

---

# 28. Comparison

```text
a == b
a != b
a < b
a <= b
a > b
a >= b
```

được resolve thông qua equality/order contracts.

Kết quả comparison là:

```text
bool
```

trừ những operations đặc biệt được specification quy định.

---

# 29. Logical operators

```text
a && b
a || b
```

**không phải ordinary overloaded operators**.

Chúng có short-circuit semantics bắt buộc.

Compiler không được biến:

```text
a && b
```

thành arbitrary:

```text
Logical::and(a,b)
```

vì điều đó có thể làm mất evaluation order/short circuit.

---

# 30. Bitwise operators

```text
&
|
^
<<
>>
```

có numeric/bitwise semantic rules rõ ràng.

Không dùng pointer/reference semantics.

---

# 31. Unary operators

```text
-x
!x
~x
```

được type-check tương tự binary operator.

`!` trong boolean context phải rõ ràng.

---

# 32. Index operator

```axiom
x[i]
```

có semantic indexing protocol.

Compiler xác định:

```text
receiver type
index type
result type
```

sau đó resolve indexing implementation.

---

# 33. Index mutation

```axiom
x[i] = value
```

không đơn giản là:

```text
get(x[i])
set(...)
```

Compiler phải giữ write-capability semantics.

MIR phải thể hiện WRITE access tới vùng tương ứng.

---

# 34. Method resolution

Đây là phần phức tạp nhất.

Ví dụ:

```axiom
x.foo(a)
```

resolver sử dụng thứ tự đã frozen:

```text
1. Inherent method
2. Trait method
3. Imported extension
4. Generic extension
```

---

# 35. Inherent method

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: Vec2) -> f32 { ... }
```

`v.length()` được resolver nhận diện trực tiếp.

Không cần class/vtable.

---

# 36. Trait method

Nếu không có inherent method:

```text
Trait implementations
```

được tìm.

Ví dụ:

```axiom
trait Display {
    fn display(self: view<Self>) -> Str
}
```

`x.display()` có thể resolve qua trait impl.

---

# 37. Extension method

Ví dụ library:

```axiom
fn is_even(x: i32) -> bool
```

nếu được import theo extension mechanism:

```text
use math::IntegerExtensions
```

thì:

```axiom
x.is_even()
```

có thể được canonicalize thành:

```text
is_even(x)
```

Extension method vẫn là ordinary function.

---

# 38. Import là semantic requirement

Extension method không được tự động toàn hệ thống.

Nếu không import:

```text
x.is_even()
```

không tự nhiên tìm mọi package trên dependency graph.

Điều này tránh namespace pollution và compile-time explosion.

---

# 39. Generic extension

Generic extension được resolve cuối cùng:

```text
T: Trait
```

và chỉ khi candidate trước đó không resolve.

---

# 40. Method candidate filtering

Mỗi candidate phải pass:

```text
name
visibility
receiver compatibility
generic arity
argument count
type constraints
trait constraints
effect constraints
capability requirements
```

---

# 41. Receiver compatibility

Ví dụ method:

```text
fn read(self: view<T>)
```

receiver:

```text
T owner
```

có thể dùng owner→view coercion.

Method:

```text
fn modify(self: mut_view<T>)
```

yêu cầu mutable capability hợp lệ.

---

# 42. Method receiver không phải magic `this`

Axiom không có:

```text
this
self
```

như một object model bắt buộc.

`self` chỉ là tên parameter convention/cú pháp method sugar.

Semantic function vẫn là:

```text
fn length(receiver: Vec2)
```

---

# 43. Static dispatch

Nếu method/trait implementation được xác định statically:

```text
x.foo()
```

→ compiler biết chính xác `ImplId`.

Không cần runtime dispatch.

---

# 44. Dynamic dispatch

Chỉ khi programmer dùng:

```text
dyn Trait
```

mới tạo dynamic dispatch semantics.

Ví dụ:

```text
view<dyn Display>
```

hoặc dạng tương ứng.

Không có implicit boxing.

---

# 45. `dyn Trait` và coercion

Chuyển concrete type:

```text
T
```

thành:

```text
dyn Trait
```

không phải ordinary coercion vô điều kiện.

Nó phải thỏa:

```text
T: Trait
Trait object-safe
ABI representation available
required capability valid
```

và representation/runtime metadata contract.

---

# 46. Trait upcast

Nếu:

```text
ChildTrait: ParentTrait
```

upcast:

```text
dyn ChildTrait
    ↓
dyn ParentTrait
```

là explicit semantic operation theo rules đã frozen.

Không tự động downcast.

---

# 47. Downcast

Downcast từ:

```text
dyn Trait
```

về concrete type cần runtime type metadata.

Không được implicit.

API có thể cung cấp:

```text
downcast<T>()
```

với Result/Option semantics.

---

# 48. Generic callable resolution

Ví dụ:

```axiom
fn apply<T, U>(f: Fn(T) -> U, x: T) -> U
```

call:

```axiom
apply(f, value)
```

compiler giải:

```text
T = type(value)
U = result_type(f)
```

sau đó check callable compatibility.

---

# 49. Callable hierarchy không tồn tại

Axiom không tạo:

```text
Object
 ├── Function
 ├── Closure
 ├── Method
 └── Lambda
```

Thay vào đó:

```text
Function
Closure
FunctionPointer
dyn Fn
```

là semantic categories riêng.

---

# 50. Capturing closure

Capturing closure có environment type compiler-generated.

Ví dụ:

```axiom
let offset = 10
let f = |x| x + offset
```

compiler tạo anonymous semantic type.

Programmer không cần khai báo.

---

# 51. Closure coercion

Capturing closure không tự biến thành:

```text
fn(i32) -> i32
```

vì nó chứa state.

Noncapturing closure có thể decay thành function pointer khi context yêu cầu và ABI cho phép.

---

# 52. Generic closure

Generic function có thể nhận closure bằng static dispatch:

```axiom
fn map<I, F>(input: I, f: F)
where
    F: Fn(...)
```

→ monomorphization/specialization.

Không heap allocation mặc định.

---

# 53. Candidate ranking

Axiom dùng ranking deterministic:

```text
Rank 0:
Exact semantic match

Rank 1:
Canonical safe coercion

Rank 2:
Generic specialization after exact/coercion compatibility

Rank 3:
Trait-mediated candidate where operation explicitly requires trait resolution
```

Không có implicit arbitrary conversion rank.

---

# 54. Không dùng “chi phí runtime” để chọn

Compiler không được chọn candidate vì:

```text
“cái này có vẻ nhanh hơn”
```

Candidate selection phải là semantic phase.

Optimizer chỉ hoạt động sau đó.

---

# 55. Không phụ thuộc optimization

Ví dụ:

```text
-O0
-O2
-O3
-Osize
```

phải chọn cùng semantic candidate.

---

# 56. Ambiguous candidate

Nếu:

```text
Candidate A
Candidate B
```

đều có cùng semantic rank:

```text
AmbiguousCall
```

Không chọn:

```text
first discovered
shortest name
nearest file
latest import
```

---

# 57. Candidate identity

Mỗi candidate có:

```text
CandidateId
DeclarationId
ImplId
GenericSubstitution
ReceiverType
ArgumentTypes
ResultType
CoercionPlan
EffectSet
```

Compiler có thể giải thích tại sao candidate được/chưa được chọn.

---

# 58. Coercion plan

Ví dụ:

```text
foo(s)
```

với:

```text
s : String
foo : fn(Str)
```

Typed HIR:

```text
Call
 ├── FunctionId(foo)
 └── Coerce
       ├── source: String
       ├── target: Str
       └── kind: OwnerToEphemeralView
```

---

# 59. Không physicalize coercion quá sớm

Coercion là semantic operation.

Backend có thể loại bỏ hoàn toàn nó.

Ví dụ:

```text
String
 ↓
Str
```

có thể chỉ trở thành:

```text
pointer + length
```

hoặc thậm chí SSA values tương ứng.

---

# 60. Capability verifier nhận coercion facts

Coercion:

```text
Owner → view
```

phải tạo capability dependency:

```text
View
 └── provenance = Owner
```

Verifier kiểm tra lifetime.

---

# 61. Mutable coercion

```text
T
 ↓
mut_view<T>
```

chỉ hợp lệ nếu compiler chứng minh:

```text
exclusive WRITE capability
```

Không được coi mutable coercion là syntax convenience đơn thuần.

---

# 62. Mutable → immutable

```text
mut_view<T>
 ↓
view<T>
```

có thể tạo read capability mới theo frozen capability rules.

Sau đó `mut_view` không nhất thiết mất semantic existence nếu capability model cho phép tách thời điểm; nhưng overlapping WRITE phải không còn active trong context tương ứng.

---

# 63. Coercion và aliasing

Ví dụ:

```axiom
foo(view(a))
bar(mut_view(a))
```

Compiler không được giả định cả hai độc lập.

Capability analysis sau typing phát hiện conflict nếu lifetimes overlap.

---

# 64. Coercion và allocation

Một coercion Core không được ngầm:

```text
stack value
 ↓
heap allocation
 ↓
pointer
```

trừ khi target representation của abstraction bắt buộc và semantic contract nói rõ.

---

# 65. Conversion function có thể allocate

Điều này hoàn toàn hợp lệ:

```axiom
let bytes = string.to_bytes_owned()
```

nhưng đó là ordinary function call, không phải coercion.

Optimizer có thể eliminate allocation nếu chứng minh được.

---

# 66. `String → Str`

Đây là coercion canonical.

```text
String
   │
   └── ephemeral view
             │
             └── lifetime bounded by use
```

Không clone UTF-8 buffer.

---

# 67. `String → view<u8>`

Được phép theo frozen string model.

Semantic:

```text
String
 ↓
read-only byte view
```

UTF-8 validity của String vẫn được giữ.

---

# 68. `Bytes → Str`

Không implicit.

Vì `Bytes` có thể chứa invalid UTF-8.

Phải:

```text
validate
 ↓
Result<Str, Error>
```

hoặc explicit trusted unsafe contract.

---

# 69. Array → view

```axiom
let a: [4]i32 = ...
foo(a)
```

nếu:

```text
foo(view<i32>)
```

→ zero-copy view coercion.

---

# 70. Array → Vec

Không coercion.

Đây là khác semantic ownership/storage model.

Nếu muốn materialize:

```text
Vec::from(a)
```

hoặc API tương đương.

---

# 71. View return

```axiom
fn first(x: view<Array>) -> view<T>
```

return capability phải giữ provenance.

Compiler không được biến thành dangling view.

Ownership/capability verifier chịu trách nhiệm.

---

# 72. Coercion và generic inference

Quan trọng:

```axiom
fn read<T>(x: view<T>)
```

call:

```axiom
read(value)
```

Inference phải có thể suy:

```text
T = type(value)
```

sau đó áp dụng:

```text
value → view<T>
```

Không áp coercion trước khi biết T nếu coercion phụ thuộc T.

---

# 73. Bidirectional interaction

```text
Expected Parameter Type
        ↓
Generic Inference
        ↓
Source Type
        ↓
Coercion Check
```

đây là cách tránh ambiguity.

---

# 74. Operator result inference

Ví dụ:

```axiom
let x: f64 = a + b
```

expected result:

```text
f64
```

có thể constrain operator implementation.

Nhưng compiler vẫn phải xác định operand semantics một cách nhất quán.

---

# 75. No backtracking explosion

Candidate resolver không được brute-force:

```text
all generic types
×
all traits
×
all conversions
×
all operators
```

Thay vào đó:

```text
indexed candidates
→ constrained substitution
→ bounded trait solver
→ deterministic selection
```

---

# 76. Candidate indexing

Index chính:

```text
OperationId
ReceiverTypeConstructor
TraitId
MethodName
Arity
```

Ví dụ:

```text
Add + i32
```

không cần scan toàn bộ ImplDB.

---

# 77. Negative candidate facts

Nếu:

```text
T does not implement Trait
```

compiler có thể lưu internal negative fact.

Nhưng đây không phải general negative trait bounds trong source language.

---

# 78. Coherence

Nếu hai implementation conflict:

```text
impl Add for X
impl Add for X
```

đây là error tại impl/coherence phase.

Call resolver không được có nhiệm vụ chọn một trong hai.

---

# 79. Specialization

Axiom v1 không cho arbitrary overlapping specialization.

Nếu có:

```text
impl<T> Trait for T
impl Trait for i32
```

phải tuân theo specialization rules đã được Trait System frozen.

Nếu không chứng minh được unique selection:

→ compile error.

---

# 80. Effect-aware callable resolution

Callable type có effect contract.

Ví dụ:

```text
fn foo() -> i32
```

khác semantic contract với:

```text
fn foo() -> i32
    effects IO
```

Resolver phải đảm bảo context cho phép effect đó.

---

# 81. Async callable

```text
async fn foo()
```

không được coi như:

```text
fn foo()
```

ordinary callable.

Nó trả Future.

`.await` là operation riêng.

---

# 82. Unsafe callable

```text
unsafe fn read(...)
```

không được gọi từ safe context nếu không có:

```text
unsafe { ... }
```

Resolver/type checker phải giữ unsafe requirement.

---

# 83. Comptime callable

```text
comptime fn size<T>()
```

không phải ordinary runtime function.

Call context phải là comptime-valid context.

---

# 84. GPU callable

```text
@kernel fn add(...)
```

có execution-domain contract.

CPU ordinary call không tự biến thành GPU launch.

GPU launch là explicit operation.

---

# 85. FFI callable

```axiom
extern "C" fn ...
```

có ABI contract riêng.

Resolver phải giữ:

```text
ABI
representation
ownership
capability
error
effect
```

không được coi FFI function như ordinary safe Axiom function chỉ vì signature giống nhau.

---

# 86. Resolution output

Sau task 242, mọi callable expression production phải có:

```text
CallableResolution {
    declaration: DeclarationId
    impl: Option<ImplId>
    generic_instance: GenericInstanceId
    receiver_plan
    argument_coercions
    result_type
    effects
    safety_requirement
    execution_domain
    abi
}
```

---

# 87. Explain API

Compiler phải có khả năng:

```text
ax explain call foo
```

trả:

```text
Candidate A
    rejected:
        parameter 2 mismatch

Candidate B
    rejected:
        trait obligation not proven

Candidate C
    selected:
        exact receiver
        exact arguments
        generic substitution T=i32
```

Đây sẽ là một trong những tính năng cực kỳ hữu ích cho AI agent.

---

# 88. IDE hover

Khi hover:

```axiom
x.foo(a)
```

IDE có thể hiển thị:

```text
foo::<T=i32>
receiver: User
result: Str
dispatch: static
effects: pure
coercions: 1
```

Không cần AI tự phân tích source.

---

# 89. Compiler diagnostic

Ví dụ ambiguity:

```text
AMBIGUOUS_CALL

expression:
    value.convert()

candidate 1:
    Convert<A>

candidate 2:
    Convert<B>

reason:
    expected result type is unconstrained

help:
    provide an expected type or explicit generic argument
```

---

# 90. Semantic fingerprint

Resolution result phải tham gia semantic dependency.

Thay đổi:

```text
impl Trait for T
```

có thể invalidate:

```text
calls depending on that impl
```

chứ không cần recompile toàn package.

---

# 91. Cache

Cache key:

```text
CallableResolutionKey {
    Name/Operation
    ReceiverType
    ArgumentTypes
    ExpectedType
    GenericEnvironment
    TraitEnvironmentFingerprint
    ImportEnvironment
    FeatureSet
}
```

---

# 92. Determinism

Candidate selection không phụ thuộc:

```text
hash table iteration
thread scheduling
file ordering
import ordering
optimization level
machine target
```

ngoại trừ các target-specific semantic rules đã được explicit.

---

# 93. Performance

Resolver phải dùng:

```text
indexes
interned TypeId
canonical goals
memoized trait solving
bounded candidate sets
incremental invalidation
parallel independent resolution
```

Mục tiêu là compiler mạnh nhưng compile-time vẫn kiểm soát được.

---

# 94. Core syntax không tăng

Một quyết định quan trọng:

**Task 242 không thêm syntax mới vào Axiom Core.**

Các cơ chế đã có:

```text
as
view<T>
mut_view<T>
dyn Trait
generic arguments
traits
methods
operators
```

đã đủ.

Compiler resolver là phần phức tạp.

Đây chính xác là nguyên tắc:

> **Compiler Complexity Is Not Language Complexity.**

---

# 95. Formal resolution model

Có thể mô hình hóa:

```text
Resolve(Candidates, Context) → Unique(Candidate)
```

hoặc:

```text
Resolve(...) →
    NoCandidate
    Ambiguous(Set)
    Unique(Candidate)
    Error
```

Không có:

```text
BestGuess
```

trong semantic model.

---

# 96. Conversion formal model

```text
Coerce(S, T, Context)
```

chỉ trả:

```text
Allowed(Plan)
Denied
Ambiguous
```

không tự invoke arbitrary functions.

---

# 97. Cast formal model

```text
Cast(S, T)
```

là finite compiler-defined relation.

Nếu không có relation:

```text
InvalidCast
```

---

# 98. Bitcast formal model

```text
Bitcast(S, T, Representation)
```

yêu cầu:

```text
size compatible
alignment compatible
representation valid
```

và các invariant representation tương ứng.

---

# 99. Callable formal model

```text
Call(F, Args, Expected)
```

thực hiện:

```text
infer arguments
→ discover callable
→ instantiate generics
→ solve traits
→ compute coercion plan
→ validate effects/safety/domain
→ select unique callable
```

---

# 100. Invariants — FROZEN

```text
ACONVRES-20
Axiom distinguishes coercion, cast, conversion and bitcast.

ACONVRES-21
Implicit coercions are compiler-defined semantic relations.

ACONVRES-22
The compiler cannot invent arbitrary implicit conversions.

ACONVRES-23
Core coercions are finite and explicitly specified.

ACONVRES-24
Coercion cannot implicitly invoke arbitrary user code.

ACONVRES-25
Coercion cannot implicitly perform observable I/O.

ACONVRES-26
Coercion cannot implicitly introduce ownership.

ACONVRES-27
Canonical owner-to-ephemeral-view coercion is zero-copy semantically.

ACONVRES-28
Canonical Array-to-view coercion is zero-copy semantically.

ACONVRES-29
mut_view-to-view conversion follows capability rules.

ACONVRES-30
never may coerce into an expected value type.

ACONVRES-31
Numeric literals are typed directly using expected-type inference where possible.

ACONVRES-32
Unconstrained integer literals default to i32.

ACONVRES-33
Unconstrained floating literals default to f64.

ACONVRES-34
Ordinary numeric variables do not undergo implicit numeric widening.

ACONVRES-35
Explicit numeric conversion uses defined cast semantics.

ACONVRES-36
Cast is distinct from trait-based conversion.

ACONVRES-37
Bitcast preserves machine representation rather than semantic value.

ACONVRES-38
Bitcast requires a valid representation contract.

ACONVRES-39
Invalid bitcasts are rejected before code generation.

ACONVRES-40
Axiom does not support arbitrary implicit conversion chains.

ACONVRES-41
Trait-based From/Into conversion is not automatically an implicit coercion.

ACONVRES-42
TryFrom conversions remain explicitly fallible.

ACONVRES-43
Axiom v1 does not support arbitrary same-name function overloading.

ACONVRES-44
Generic programming is the primary static abstraction mechanism instead of arbitrary overload sets.

ACONVRES-45
Operator resolution occurs after operand typing.

ACONVRES-46
Operator candidate selection uses the canonical Trait Solver.

ACONVRES-47
Short-circuit logical operators retain intrinsic evaluation semantics.

ACONVRES-48
Indexing preserves capability and write semantics.

ACONVRES-49
Method resolution occurs after receiver typing.

ACONVRES-50
Inherent methods have priority over trait methods.

ACONVRES-51
Trait methods have priority over imported extension methods.

ACONVRES-52
Imported extension methods have priority over generic extensions.

ACONVRES-53
Extension methods remain ordinary functions semantically.

ACONVRES-54
Extension lookup is bounded by explicit imports and semantic scope.

ACONVRES-55
Method resolution never scans unrelated packages indiscriminately.

ACONVRES-56
Method candidate discovery is indexed.

ACONVRES-57
Method candidate resolution is deterministic.

ACONVRES-58
Receiver coercions are explicit in Typed HIR.

ACONVRES-59
Receiver capability requirements are verified independently.

ACONVRES-60
Static dispatch is the default.

ACONVRES-61
Dynamic dispatch requires explicit dyn Trait semantics.

ACONVRES-62
Concrete types do not acquire implicit vtables.

ACONVRES-63
Capturing closures are distinct from function pointers.

ACONVRES-64
Capturing closures do not implicitly decay to function pointers.

ACONVRES-65
Noncapturing closures may decay to function pointers when ABI-compatible.

ACONVRES-66
Callable resolution includes generic substitution.

ACONVRES-67
Callable resolution includes effect requirements.

ACONVRES-68
Callable resolution includes unsafe requirements.

ACONVRES-69
Callable resolution includes comptime requirements.

ACONVRES-70
Callable resolution includes execution-domain requirements.

ACONVRES-71
FFI callable resolution preserves ABI contracts.

ACONVRES-72
GPU callable resolution preserves execution and storage domain contracts.

ACONVRES-73
Candidate selection never depends on optimization level.

ACONVRES-74
Candidate selection never depends on implementation discovery order.

ACONVRES-75
Candidate selection never depends on hash iteration order.

ACONVRES-76
Ambiguous candidates produce diagnostics.

ACONVRES-77
No semantic resolver operation may use BestGuess behavior.

ACONVRES-78
Candidate sets are bounded before expensive trait solving.

ACONVRES-79
Trait solving uses canonical cached goals.

ACONVRES-80
Resolution is incrementally cacheable.

ACONVRES-81
Resolution cache keys include relevant semantic environment fingerprints.

ACONVRES-82
Coherence errors are resolved at implementation validation rather than call-site guessing.

ACONVRES-83
Unrestricted overlapping specialization is forbidden in Core v1.

ACONVRES-84
Coercion plans are materialized in Typed HIR.

ACONVRES-85
Coercion plans preserve source provenance.

ACONVRES-86
Capability verification receives coercion-derived provenance.

ACONVRES-87
Coercion does not guarantee physical allocation or physical representation.

ACONVRES-88
Optimizer may erase semantically zero-cost coercions.

ACONVRES-89
Conversion functions remain ordinary semantic calls.

ACONVRES-90
Conversion allocation is observable only when its semantic effects are observable.

ACONVRES-91
Operator result types participate in inference.

ACONVRES-92
Expected result types may constrain generic/operator resolution.

ACONVRES-93
Resolution does not perform unbounded backtracking.

ACONVRES-94
Resolution complexity is bounded by indexed candidate discovery and solver limits.

ACONVRES-95
Resolution diagnostics expose rejected candidate reasons when available.

ACONVRES-96
AI tooling consumes canonical resolution facts rather than implementing its own resolver.

ACONVRES-97
Generated/comptime code uses the same resolution semantics.

ACONVRES-98
Resolution semantics are independent of physical storage.

ACONVRES-99
Resolution semantics are independent of allocation strategy.

ACONVRES-100
Typed HIR contains a unique callable identity for every production call.
```

---

# Axiom hiện đã có một chuỗi semantic rất mạnh

```text
AST
 ↓
Name Resolution
 ↓
Trait Solver
 ↓
Type Inference
 ↓
Conversion / Coercion / Callable Resolution
 ↓
Typed HIR
 ↓
MIR
 ↓
Ownership Verification
 ↓
Capability Verification
 ↓
Effect Verification
 ↓
Optimization
```

Điểm đáng chú ý là **programmer gần như không phải viết thêm gì** để hỗ trợ compiler. Ví dụ:

```axiom
let users = ...
let first = users[0]
print(first)
```

compiler tự lo:

```text
generic inference
→ index resolution
→ element type
→ ownership
→ capability
→ view coercion
→ effect checking
→ MIR
→ alias analysis
```

nhưng source vẫn đơn giản.

---

## TASK TIẾP THEO

### **BOOTSTRAP-243 — AXIOM EXPRESSION SEMANTICS, EVALUATION ORDER & CONTROL-FLOW TYPING**

Phần tiếp theo cần khóa một vấn đề còn nền tảng hơn cả optimization:

> **Trong Axiom, chính xác expression được đánh giá theo thứ tự nào, side effect xảy ra lúc nào, và compiler được phép reorder đến đâu?**

Task 243 sẽ đóng băng:

```text
evaluation order
sequence points
argument evaluation
field/index evaluation
operator evaluation
short-circuit
assignment
destructuring assignment
if
match
loop
break/continue
return
panic
defer-like cleanup qua Drop
temporary lifetime
scope lifetime
early drop
expression side effects
observable behavior
```

Đây sẽ là nền trực tiếp cho **MIR Control Flow + Ownership/Drop Verification**, và đặc biệt quan trọng nếu mục tiêu của Axiom là vừa **đơn giản cho programmer** vừa cho optimizer quyền tối ưu rất mạnh.