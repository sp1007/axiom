# BOOTSTRAP-130 — Trait System, Trait Solver & Polymorphism

**Trạng thái: FROZEN / COMPLETED**

Mục tiêu:

> Trait là cơ chế abstraction/polymorphism chính của Axiom, thay thế phần lớn nhu cầu về class inheritance mà không tạo object hierarchy, object header hoặc virtual dispatch bắt buộc.

Kiến trúc:

```text
Typed HIR
   │
   ├── Trait declarations
   ├── impl declarations
   ├── Generic constraints
   └── Trait obligations
            │
            ▼
       TraitDB / Solver
            │
       ┌────┼────────┐
       │    │        │
    Impl   Normalize  Object
   Select   Types     Safety
       │    │        │
       └────┼────────┘
            ▼
       Resolved HIR
            │
            ▼
           MIR
```

---

## 1. Trait không phải class

Axiom:

```ax
trait Display {
    fn display(self) -> String;
}
```

Type:

```ax
struct User {
    id: u64,
}
```

Implementation:

```ax
impl Display for User {
    fn display(self) -> String {
        ...
    }
}
```

Không có:

```text
base class
derived class
virtual method table mặc định
object header
```

Trait chỉ mô tả **behavioral contract**.

---

# 2. Một type có thể implement nhiều trait

```ax
impl Display for User { ... }
impl Clone for User { ... }
impl Serialize for User { ... }
impl Send for User { ... }
```

Không có giới hạn kiểu “single inheritance”.

---

# 3. Một trait có thể được implement cho nhiều type

```ax
trait Hash {
    fn hash(self) -> u64;
}

impl Hash for User { ... }
impl Hash for Product { ... }
impl Hash for Order { ... }
```

Trait là abstraction theo behavior.

---

# 4. Trait không tạo subtype

Nếu:

```ax
trait Animal { ... }
struct Dog { ... }
impl Animal for Dog { ... }
```

thì:

```text
Dog ≠ Animal
```

về type identity.

`Dog` không tự động trở thành subtype của `Animal`.

---

# 5. Generic static polymorphism

```ax
fn print<T: Display>(x: T) {
    ...
}
```

Mặc định:

```text
static dispatch
```

Compiler biết concrete `T` tại monomorphization.

---

# 6. Dynamic polymorphism phải explicit

```ax
fn print(x: dyn Display) {
    ...
}
```

mới yêu cầu dynamic dispatch.

Đây là nguyên tắc:

> **Polymorphism is explicit; implementation cost is not hidden.**

---

# 7. Trait obligation

Khi gặp:

```ax
fn sort<T: Ord>(x: T)
```

compiler tạo obligation:

```text
T: Ord
```

Trait solver phải chứng minh:

```text
Proven
```

Nếu không:

```text
NotProven
```

Nếu có nhiều khả năng chưa quyết định:

```text
Ambiguous
```

---

# 8. Trait solver không trả về boolean

Không dùng:

```text
implements(T, Trait) -> true/false
```

mà:

```text
TraitResult =
    Proven
    NotProven
    Ambiguous
    Error
```

`Ambiguous` rất quan trọng cho generic inference.

---

# 9. Trait goal

Internal representation:

```text
TraitGoal {
    trait: TraitId,
    self_type: TypeId,
    args: [TypeId...],
    environment: ParamEnv,
}
```

Ví dụ:

```text
T: Add<Rhs = i32>
```

được biểu diễn semantic, không bằng string matching.

---

# 10. Trait environment

Trong:

```ax
fn foo<T: Display>(x: T) {
    bar(x);
}
```

solver biết:

```text
Environment:
    T: Display
```

và có thể sử dụng fact đó khi giải obligation.

---

# 11. Impl candidate

Ví dụ:

```ax
impl Display for User
```

tạo candidate:

```text
ImplCandidate {
    trait: Display,
    self_pattern: User,
    constraints: [],
}
```

Generic impl:

```ax
impl<T: Display> Debug for Vec<T>
```

tạo candidate pattern:

```text
Debug(Vec<T>)
where T: Display
```

---

# 12. Candidate matching

Goal:

```text
Debug(Vec<User>)
```

Candidate:

```text
Debug(Vec<T>)
where T: Display
```

Unify:

```text
T = User
```

Sau đó solver phải prove:

```text
User: Display
```

Nếu proven → candidate valid.

---

# 13. Candidate filtering

Solver:

```text
Goal
 ↓
Collect candidates
 ↓
Unify
 ↓
Check where-clauses
 ↓
Check coherence
 ↓
Select unique candidate
```

Không chọn candidate chỉ vì “match gần nhất” theo heuristic không xác định.

---

# 14. Overlapping impl

Không cho hai impl ambiguity:

```ax
impl<T> Foo for Vec<T> { ... }
impl<T: Bar> Foo for Vec<T> { ... }
```

nếu compiler không có specialization rule đủ mạnh để xác định một candidate luôn thắng candidate kia.

---

# 15. Specialization

Axiom v0.1:

> **Không hỗ trợ arbitrary specialization.**

Chỉ hỗ trợ specialization nếu compiler có rule rõ ràng chứng minh:

```text
more-specific impl
```

luôn thắng:

```text
general impl
```

và không tạo semantic ambiguity.

---

# 16. Khuyến nghị specialization v1

Có thể dùng:

```ax
impl<T> Foo for Vec<T> { ... }

impl<T: Fast> Foo for Vec<T> specialized { ... }
```

nhưng `specialized` chỉ nên được mở khi specialization model hoàn chỉnh.

Không nên biến nó thành tính năng tự do ngay từ Core v0.1.

---

# 17. Coherence

Axiom phải đảm bảo một program không có hai implementation hợp lệ mâu thuẫn cho cùng:

```text
Trait + Type
```

trong cùng semantic universe.

---

# 18. Orphan rule

Khuyến nghị:

> Một impl phải sở hữu trait hoặc type liên quan.

Ví dụ package A định nghĩa:

```text
TraitA
```

package B định nghĩa:

```text
TypeB
```

package C không thể tùy tiện định nghĩa:

```ax
impl TraitA for TypeB
```

nếu C không sở hữu trait hoặc type.

Điều này ngăn dependency graph trở thành nguồn ambiguity.

---

# 19. Trait coherence xuyên package

Solver phải tính:

```text
PackageIdentity
Version
SourceIdentity
```

Không dùng chỉ tên trait/type.

Điều này phù hợp với package model đã frozen.

---

# 20. Default trait methods

Trait:

```ax
trait Printable {
    fn print(self) {
        ...
    }
}
```

Type có thể dùng default:

```ax
impl Printable for User {}
```

hoặc override:

```ax
impl Printable for User {
    fn print(self) {
        ...
    }
}
```

Không cần `override`.

---

# 21. Override không phải inheritance override

Đây là:

```text
trait method implementation selection
```

không phải:

```text
class virtual override
```

Vì vậy semantics đơn giản hơn.

---

# 22. Method resolution

Với:

```ax
x.print()
```

compiler tìm theo thứ tự đã frozen:

```text
1. inherent method
2. trait implementation
3. explicitly imported extension method
4. generic extension
```

Nếu có nhiều candidate ngang hàng:

```text
compile error
```

Không âm thầm chọn một candidate.

---

# 23. Trait associated type

```ax
trait Iterator {
    type Item;

    fn next(mut_view<Self>) -> Option<Self::Item>;
}
```

Implementation:

```ax
impl Iterator for Users {
    type Item = User;
}
```

Solver normalize:

```text
Users::Item
→ User
```

---

# 24. Associated constants

```ax
trait Numeric {
    const ZERO: Self;
}
```

Goal có thể yêu cầu:

```text
<T as Numeric>::ZERO
```

Const evaluation xử lý giá trị sau khi trait resolution xác định implementation.

---

# 25. Associated functions

```ax
trait FromBytes {
    fn from_bytes(x: view<u8>) -> Result<Self, Error>;
}
```

Không cần receiver.

---

# 26. Associated function ambiguity

Nếu:

```ax
T::from_bytes(...)
```

có nhiều trait cung cấp cùng associated function mà context không xác định trait:

```text
ambiguous associated item
```

Compiler không tự đoán.

Có thể disambiguate:

```ax
<T as FromBytes>::from_bytes(...)
```

---

# 27. Operator overloading

Operators được xây trên traits.

Ví dụ:

```text
a + b
```

có thể resolve thành:

```text
Add::add(a, b)
```

Nhưng parser/compiler vẫn coi:

```text
&&
||
?
```

là language-level control constructs khi semantics yêu cầu short-circuit/control flow.

---

# 28. Không biến mọi operator thành function call mù

Ví dụ:

```ax
a && b
```

không được evaluate `b` trước rồi gọi trait.

Short-circuit là semantic primitive.

---

# 29. Trait-based indexing

Có thể có:

```text
Index
IndexMut
```

để:

```ax
x[i]
x[i] = value
```

nhưng bounds checking vẫn là language/runtime semantic operation riêng.

Trait không được phép bypass safety.

---

# 30. Trait-based conversion

Axiom nên phân biệt:

```text
From
Into
TryFrom
TryInto
```

với compiler primitive `as`.

Ví dụ:

```ax
let x: UserId = UserId::from(raw);
```

là semantic conversion API.

Trong khi:

```ax
raw as u64
```

là language cast.

---

# 31. `as` không invoke arbitrary trait

Đây là quyết định quan trọng.

Không:

```text
as
→ tìm mọi From/Into
→ chọn candidate
```

Nếu không sẽ khiến cast có hidden behavior và trait resolution phức tạp.

---

# 32. Marker traits

Một số trait không có method:

```text
Send
Share
Copy
```

Compiler có thể derive/check chúng theo semantic rules.

---

# 33. User không được giả mạo auto property

Không cho programmer nói:

```ax
unsafe impl Send for T
```

nếu semantic model không cho phép.

Nếu type thật sự unsafe để Send mà programmer “assert” nó Send thì compiler mất trust boundary.

Unsafe chỉ được thiết lập preconditions machine-level đã định nghĩa, không được thay đổi sự thật của type properties.

---

# 34. Derived traits

Compiler có thể hỗ trợ:

```ax
@derive(Copy, Clone, Eq)
struct Point { ... }
```

`derive` tạo implementation typed.

Generated impl quay lại:

```text
normal resolution
→ type checking
→ trait checking
→ ownership verification
```

Không có bypass.

---

# 35. Auto traits

Một số properties có thể derive tự động:

```text
Send
Share
```

dựa trên các field.

Ví dụ:

```ax
struct A {
    x: i32,
}
```

nếu `i32: Send`, compiler có thể suy ra:

```text
A: Send
```

---

# 36. Negative properties

Có thể có:

```text
!Send
!Share
!Copy
```

nhưng khuyến nghị v0.1:

> `!Send` / `!Share` chủ yếu do compiler semantic rules hoặc type definition quyết định; không mở negative impl tùy tiện ngay từ đầu.

Giảm complexity solver.

---

# 37. Recursive trait obligations

Ví dụ:

```text
T: A
A<T>: B
B<T>: A
```

solver phải phát hiện cycle.

Không recurse vô hạn.

---

# 38. Trait solver cache

Key:

```text
Goal
+
ParamEnv
+
CompilerSemanticVersion
+
Relevant definitions
```

Result:

```text
Proven / NotProven / Ambiguous / Error
```

được memoize.

---

# 39. Canonical goals

Trước khi cache:

```text
T: Display
```

với generic variable IDs khác nhau phải canonicalize về cùng shape.

Ví dụ:

```text
?0: Display
```

Điều này làm cache solver hiệu quả hơn.

---

# 40. Solver depth

Trait recursion phải có giới hạn.

Khi vượt:

```text
ETRAIT_OVERFLOW
```

Không compiler stack overflow.

---

# 41. Solver termination

Axiom trait solver phải có:

```text
cycle detection
depth limit
candidate limit
memoization
canonicalization
```

để input adversarial không làm compiler chạy vô hạn.

---

# 42. Ambiguity

Ví dụ:

```ax
fn foo<T>() -> T {
    ...
}

let x = foo();
```

Không có expected type.

Compiler không được chọn arbitrary `T`.

→ `ETRAIT_AMBIGUOUS` hoặc `ETYPE_AMBIGUOUS`.

---

# 43. Trait solver và type inference phối hợp

Hai subsystem không nên gọi lẫn nhau vô hạn.

Mô hình:

```text
Type Inference
      │
      ├── creates type variables
      │
      ▼
Trait Solver
      │
      ├── produces constraints
      ▼
Type Normalization
      │
      ▼
Unification
      │
      └── repeat until fixed point
```

Có giới hạn iteration/fixed-point.

---

# 44. Fixed-point solving

Một function generic có thể tạo:

```text
T: Iterator
T::Item: Display
Vec<T::Item>: Clone
```

Solver normalize từng projection rồi giải tiếp.

Kết thúc khi:

```text
no new constraints
```

hoặc gặp:

```text
failure / ambiguity / overflow
```

---

# 45. Trait solver không codegen

Trait solver chỉ trả lời:

> Implementation nào được chọn?

Không sinh machine code.

Monomorphization/codegen là compiler backend concern.

---

# 46. Generic monomorphization

Sau trait resolution:

```ax
fn max<T: Ord>(a: T, b: T) -> T
```

với:

```text
max<i32>
max<f64>
```

có thể tạo concrete instances.

---

# 47. Generic deduplication

Nếu hai generic instances semantic identical:

```text
Vec<User>
```

ở nhiều modules:

compiler có thể canonicalize thành một:

```text
GenericInstanceId
```

và tránh compile duplicate.

---

# 48. Hybrid code sharing

Không phải generic nào cũng cần full monomorphization.

Compiler có thể:

```text
monomorphize
```

hoặc:

```text
share code
```

khi representation/semantics cho phép.

Đây là optimization, không phải source semantic.

---

# 49. Trait dispatch categories

Axiom có ba trường hợp:

```text
1. Static generic dispatch
2. Static concrete trait implementation
3. Explicit dynamic dispatch
```

Không có hidden fourth category “compiler tự biến thành virtual”.

---

# 50. Static trait call

```ax
fn draw<T: Draw>(x: T) {
    x.draw();
}
```

Compiler biết concrete `T` ở specialization.

Có thể inline:

```text
draw(User)
→ User::draw
```

và loại bỏ abstraction.

---

# 51. Concrete trait call

Nếu type đã known:

```ax
let x: User = ...;
x.draw();
```

compiler resolve trực tiếp:

```text
User::draw
```

Không cần vtable.

---

# 52. Dynamic trait call

```ax
let x: dyn Draw = ...;
x.draw();
```

lúc này dynamic dispatch là semantic requirement.

Representation có thể là:

```text
data
+
vtable
```

---

# 53. Dynamic dispatch không mặc định

Điều này cực kỳ quan trọng cho mục tiêu performance:

```text
Trait
≠
vtable
```

Chỉ:

```text
dyn Trait
```

mới yêu cầu dynamic dispatch.

---

# 54. Object safety

Trait muốn dùng:

```text
dyn Trait
```

phải đáp ứng object-safety rules.

Ví dụ method trả về `Self` thường cần restriction vì vtable không biết concrete size.

Trait checker phải reject hoặc yêu cầu constraint phù hợp.

---

# 55. Generic method trong dyn trait

Ví dụ:

```ax
trait Foo {
    fn convert<T>(self, x: T);
}
```

không thể trực tiếp tạo một vtable entry cho mọi `T`.

Do đó trait này không object-safe theo default model.

---

# 56. `Self` trong trait

`Self` là implicit type parameter của trait implementation.

Ví dụ:

```ax
trait Clone {
    fn clone(self) -> Self;
}
```

Trong:

```ax
impl Clone for User
```

`Self = User`.

---

# 57. Trait inheritance?

Axiom không cần class inheritance, nhưng trait refinement có giá trị:

```ax
trait Animal: Display + Send {
    ...
}
```

Điều này có nghĩa:

```text
Animal(T)
⇒ Display(T)
⇒ Send(T)
```

Đây là **trait bound composition**, không phải object inheritance.

---

# 58. Supertrait

Nếu:

```ax
trait Animal: Display
```

thì implementation `Animal for Dog` phải satisfy:

```text
Dog: Display
```

Trait solver kiểm tra tự động.

---

# 59. Trait diamond

```text
A
├── B
│   └── D
└── C
    └── D
```

Không có vấn đề kiểu virtual inheritance vì trait không chứa object state.

Nếu B/C cùng yêu cầu D, đó là cùng semantic obligation.

---

# 60. Trait state

Trait Core v0.1 **không có instance fields**.

Không:

```ax
trait Foo {
    value: i32;
}
```

State nằm trong struct/type.

Trait chỉ behavior/constraints.

Điều này giữ trait đơn giản và tránh multiple-inheritance state problems.

---

# 61. Trait constants không phải instance fields

```ax
trait Numeric {
    const ZERO: Self;
}
```

là associated constant, không phải hidden object state.

---

# 62. Extension methods

Một function:

```ax
fn clamp(x: i32, min: i32, max: i32) -> i32
```

có first parameter là receiver-compatible type có thể được gọi:

```ax
x.clamp(min, max)
```

nếu module extension được import.

Đây là syntax sugar, không mutation của type.

---

# 63. Extension method ambiguity

Nếu hai imported modules cùng có:

```text
clamp(i32, ...)
```

compiler phải báo ambiguity.

Không dựa vào import order.

---

# 64. Trait method ambiguity

Nếu:

```ax
trait A { fn foo(Self); }
trait B { fn foo(Self); }
```

và type implement cả hai:

```ax
x.foo()
```

có thể ambiguous.

Disambiguation:

```ax
<A>::foo(x)
<B>::foo(x)
```

hoặc equivalent explicit trait path.

---

# 65. Method lookup không làm thay đổi type identity

Method resolution chỉ chọn function:

```text
MethodCandidate
```

Không tạo subtype, wrapper type hoặc dynamic object.

---

# 66. Trait ABI

Trait implementation static không cần runtime metadata.

`dyn Trait` cần dynamic representation contract.

Do đó:

```text
Trait semantics
```

và:

```text
Trait object ABI
```

tách biệt.

---

# 67. Trait object lifetime/capability

```ax
view<dyn Display>
```

nếu được hỗ trợ, capability semantics vẫn áp dụng:

```text
read-only
non-owning
provenance
lifetime
```

Dynamic dispatch không được bypass ownership/capability verifier.

---

# 68. `dyn Trait` ownership

```ax
Box<dyn Display>
```

là owned dynamic object.

Compiler có thể cần:

```text
data pointer
vtable pointer
drop glue
```

nhưng tất cả chỉ tồn tại vì programmer đã chọn dynamic object.

---

# 69. No implicit boxing

Không:

```ax
fn f(x: dyn Display)
```

rồi compiler tự heap-box mọi concrete value.

Nếu dynamic representation yêu cầu storage, semantic API phải thể hiện storage/capability phù hợp.

---

# 70. Trait dispatch optimization

Ngay cả:

```ax
dyn Display
```

compiler vẫn có thể devirtualize nếu chứng minh concrete type:

```text
dyn Display
    ↓ proven concrete User
User::display
```

nhưng đây là optimization.

Semantics vẫn dynamic dispatch contract.

---

# 71. Trait solver + capability

Trait bound có thể chứa capability-sensitive types:

```ax
fn mutate<T>(x: mut_view<T>)
```

Trait solving không được giả định ownership/capability.

Verifier xử lý:

```text
CapabilityDB
```

sau type resolution.

---

# 72. Trait solver + Send/Share

Ví dụ:

```ax
spawn(fn() {
    use(x);
});
```

Compiler cần prove:

```text
x: Send
```

nhưng Send có thể là compiler-derived semantic property.

Không dùng trait solver như một escape hatch để bỏ qua concurrency verifier.

---

# 73. Trait solver + GPU

Một type dùng trong:

```ax
@kernel fn foo<T: GpuLegal>(...)
```

có thể có trait constraint.

Nhưng kernel legality vẫn là một verification phase riêng.

Trait `GpuLegal` không được tự động cấp quyền cho:

```text
file/socket/syscall
```

---

# 74. Trait solver + comptime

Comptime có thể query traits:

```ax
comptime {
    if implements<T, Serialize> {
        ...
    }
}
```

Nhưng kết quả phải deterministic và thuộc semantic compiler environment.

---

# 75. Compile-time trait reflection

Compiler API có thể expose:

```text
implements(Type, Trait)
associated_type(Type, Trait, Name)
methods(Trait)
impls(Trait)
```

cho comptime/reflection.

Runtime reflection không mặc định.

---

# 76. Trait metadata

`.axmeta` cần chứa đủ:

```text
TraitId
Trait signature
supertraits
associated types
associated constants
associated functions
default implementations metadata
coherence information
ABI/object-safety information
```

để downstream package không cần đọc source.

---

# 77. Trait solver incremental

Nếu implementation:

```ax
impl Display for User
```

thay đổi, compiler chỉ invalidate những query phụ thuộc vào implementation fingerprint liên quan.

Không rebuild toàn bộ trait universe.

---

# 78. Trait solver deterministic

Candidate ordering phải canonical:

```text
PackageIdentity
ModuleId
DeclarationId
ImplId
```

Không dựa vào:

```text
hash-map iteration order
thread scheduling
memory address
```

---

# 79. Trait solver parallelism

Các goal độc lập:

```text
T1: Display
T2: Clone
T3: Send
```

có thể solve song song.

Cache và canonicalization bảo đảm kết quả giống sequential execution.

---

# 80. Trait diagnostics

Diagnostic phải nói được:

```text
required:
    T: Display

because:
    foo<T>()

could not prove:
    User: Display

candidates considered:
    ...
```

Không chỉ:

```text
trait error
```

---

# 81. AI-readable trait explanation

Ví dụ:

```text
axc explain trait-call foo
```

có thể trả:

```json
{
  "goal": "User: Display",
  "result": "proven",
  "implementation": "package::UserDisplay",
  "constraints": [],
  "dispatch": "static"
}
```

Đây rất hữu ích cho agent.

---

# 82. Trait solver không được phụ thuộc source spelling

Sau resolution:

```text
Display
```

phải là:

```text
TraitId
```

Không tiếp tục lookup bằng string trong các phase sau.

---

# 83. Trait implementation visibility

Private impl có thể phục vụ private/internal compilation.

Public generic API cần metadata đủ để downstream solver biết những facts semantic nào được phép sử dụng.

Không expose private implementation details không thuộc public contract.

---

# 84. Sealed trait

Có thể hỗ trợ library pattern:

```ax
trait Sealed { ... }
```

với visibility restrictions để ngăn external implementation.

Không cần language primitive riêng trong v0.1.

---

# 85. Trait coherence và specialization

Ba trạng thái:

```text
Valid
Overlapping
Ambiguous
```

Compiler không được “chọn implementation đầu tiên”.

---

# 86. Trait solver failure classification

Nên phân biệt:

```text
NOT_PROVEN
AMBIGUOUS
OVERFLOW
COHERENCE_ERROR
OBJECT_SAFETY_ERROR
INTERNAL_ERROR
```

để diagnostics và AI tooling chính xác.

---

# 87. No hidden dynamic dispatch

Invariant cực quan trọng:

> Nếu source chỉ yêu cầu static generic dispatch, compiler không được thêm dynamic dispatch chỉ vì implementation convenience.

---

# 88. No hidden allocation

Trait abstraction không được tự tạo:

```text
heap allocation
object header
reference counting
runtime registry
```

trừ khi semantic type/API thực sự yêu cầu.

---

# 89. Trait zero-cost model

Ví dụ:

```ax
fn area<T: Shape>(x: T) -> f64 {
    x.area()
}
```

sau monomorphization có thể trở thành trực tiếp:

```text
call Circle::area
```

hoặc được inline hoàn toàn.

Trait abstraction biến mất nếu không observable.

---

# 90. Trait system hoàn chỉnh với struct-only OOP

Với hướng Axiom đã chọn:

```text
struct
+
function
+
trait
+
impl
+
generic
+
dyn Trait
```

đã đủ thay thế phần lớn:

```text
class
inheritance
interface
virtual method
extension method
generic constraint
```

mà không cần đưa class vào Core.

---

# 91. Semantic hierarchy

Axiom polymorphism có thể nhìn như:

```text
Concrete Type
     │
     ├── inherent functions
     │
     ├── trait implementations
     │
     ├── generic constraints
     │
     └── explicit dyn Trait
```

Không có:

```text
Object
  ↓
BaseClass
  ↓
DerivedClass
```

---

# 92. Trait invariants

### `ATRAIT-20`
Traits define behavior/contracts, not class inheritance.

### `ATRAIT-21`
Traits do not introduce implicit object headers.

### `ATRAIT-22`
Trait implementation does not create subtype identity.

### `ATRAIT-23`
Static generic dispatch is the default.

### `ATRAIT-24`
Dynamic dispatch requires explicit `dyn Trait`.

### `ATRAIT-25`
Trait obligations are represented semantically.

### `ATRAIT-26`
Trait solving returns Proven/NotProven/Ambiguous/Error.

### `ATRAIT-27`
Trait candidate selection is deterministic.

### `ATRAIT-28`
Trait solver uses canonical type identities.

### `ATRAIT-29`
Trait solving supports generic impl patterns.

### `ATRAIT-30`
Generic impl constraints must be proven before selection.

### `ATRAIT-31`
Ambiguous implementations are compile errors.

### `ATRAIT-32`
Coherence prevents conflicting implementations.

### `ATRAIT-33`
Orphan rules constrain external implementations.

### `ATRAIT-34`
Arbitrary specialization is not part of Core v0.1.

### `ATRAIT-35`
Supported specialization must have deterministic precedence.

### `ATRAIT-36`
Default trait methods may be overridden by concrete implementations.

### `ATRAIT-37`
Override does not imply class inheritance.

### `ATRAIT-38`
Associated types are semantic type projections.

### `ATRAIT-39`
Associated constants are compile-time semantic members.

### `ATRAIT-40`
Associated functions need not have receivers.

### `ATRAIT-41`
Operator traits do not override language-level short-circuit semantics.

### `ATRAIT-42`
Trait conversions are distinct from primitive `as` casts.

### `ATRAIT-43`
Trait marker properties cannot be unsafely fabricated.

### `ATRAIT-44`
Derived trait implementations re-enter normal compiler verification.

### `ATRAIT-45`
Trait cycles terminate through cycle detection.

### `ATRAIT-46`
Trait recursion has bounded evaluation.

### `ATRAIT-47`
Trait solving is memoized and incrementally invalidated.

### `ATRAIT-48`
Trait solving is deterministic under parallel execution.

### `ATRAIT-49`
Trait resolution does not generate machine code.

### `ATRAIT-50`
Generic monomorphization occurs after semantic trait resolution.

### `ATRAIT-51`
Equivalent generic instances may be canonicalized.

### `ATRAIT-52`
Trait abstraction introduces no mandatory runtime cost.

### `ATRAIT-53`
Static trait calls may be inlined/devirtualized.

### `ATRAIT-54`
Dynamic trait calls may use runtime dispatch representation.

### `ATRAIT-55`
Dynamic dispatch does not imply automatic heap allocation.

### `ATRAIT-56`
Implicit boxing for `dyn Trait` is forbidden.

### `ATRAIT-57`
Object safety is checked before forming dynamic trait objects.

### `ATRAIT-58`
Trait objects retain ownership/capability safety.

### `ATRAIT-59`
Trait solving does not bypass ownership verification.

### `ATRAIT-60`
Trait solving does not bypass concurrency verification.

### `ATRAIT-61`
Trait solving does not bypass GPU legality verification.

### `ATRAIT-62`
Trait solving may participate in comptime queries.

### `ATRAIT-63`
Comptime trait queries are deterministic under their capability model.

### `ATRAIT-64`
Trait metadata is available through `.axmeta`.

### `ATRAIT-65`
Trait diagnostics expose the selected candidate and failed constraints.

### `ATRAIT-66`
Trait identities do not depend on source strings after resolution.

### `ATRAIT-67`
Trait identities do not depend on process addresses.

### `ATRAIT-68`
Private implementation details do not silently become public semantic contracts.

### `ATRAIT-69`
Clean and incremental trait solving are semantically equivalent.

### `ATRAIT-70`
Trait solver failures cannot cause uncontrolled compiler crashes.

### `ATRAIT-71`
Trait diagnostics distinguish ambiguity from absence.

### `ATRAIT-72`
Trait resolution is complete before Verified MIR enters optimization.

### `ATRAIT-73`
No backend pass may introduce semantic trait dispatch not authorized by ABI lowering.

### `ATRAIT-74`
AI/IDE tooling can inspect trait goals and resolution decisions.

### `ATRAIT-75`
The trait system is sufficient to implement polymorphism without class inheritance.

---

# Kiến trúc Axiom hiện tại

Sau `BOOTSTRAP-129` và `130`, phần semantic type/polymorphism đã khá hoàn chỉnh:

```text
                     Source
                       │
                     Lexer
                       │
                      CST
                       │
                      AST
                       │
                 Name Resolution
                       │
                 Resolved HIR
                       │
          ┌────────────┼────────────┐
          │            │            │
        TypeDB       TraitDB      ConstDB
          │            │            │
          └────────────┼────────────┘
                       │
                 Typed / Resolved HIR
                       │
                ┌──────┴──────┐
                │             │
            Comptime       Generic
                │             │
                └──────┬──────┘
                       │
                      MIR
                       │
                   Verification
```

Điểm quan trọng nhất đã được khóa:

> **Axiom không cần class để có abstraction mạnh.**

Mô hình:

```text
struct     → data
fn         → behavior
trait      → contract
impl       → implementation
generic    → static polymorphism
dyn Trait  → explicit dynamic polymorphism
extension  → syntax convenience
```

và compiler có thể xóa phần lớn abstraction này trước khi tới machine code.

---

# BOOTSTRAP-131 — Name Resolution, Imports, Modules & Visibility

Task tiếp theo sẽ khóa phần **“tên nào thực sự trỏ tới declaration nào”**, bao gồm:

```text
package
  ↓
module
  ↓
scope
  ↓
import
  ↓
name resolution
  ↓
DeclarationId
```

đồng thời xử lý:

- lexical scope;
- shadowing;
- module path;
- `pub`;
- private/protected-style visibility nếu cần;
- re-export;
- import alias;
- glob import;
- cyclic modules;
- package boundary;
- prelude;
- extension-method visibility;
- trait visibility;
- macro/comptime-generated declarations;
- deterministic resolution;
- incremental invalidation;
- namespace collisions;
- AI-readable symbol lookup.

**BOOTSTRAP-131 là task kế tiếp.**