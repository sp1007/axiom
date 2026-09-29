Tiếp tục.

# BOOTSTRAP-046 — Fundamental Traits & Protocols Audit & Freeze

Đây là phần quyết định Axiom có thực sự đạt được mục tiêu:

> **Không cần class, không cần inheritance, nhưng vẫn có abstraction, extension và override mạnh.**

Tôi đề xuất Axiom dùng **struct + function + trait**, nhưng làm trait system đơn giản hơn mức Rust ở phần programmer-facing.

---

# 1. Ba tầng behavior

Axiom có 3 cách định nghĩa behavior:

```text
1. Inherent function
2. Trait implementation
3. Extension function
```

Ví dụ:

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: Vec2) -> f32 {
    sqrt(self.x * self.x + self.y * self.y)
}
```

Gọi:

```axiom
v.length()
```

chỉ là syntax sugar cho:

```axiom
length(v)
```

---

# 2. Inherent function

Đây là behavior thuộc trực tiếp type.

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: Vec2) -> f32 { ... }
fn normalize(self: Vec2) -> Vec2 { ... }
```

Không có `impl` bắt buộc nếu function nằm trong cùng type declaration/module theo quy ước của language.

Nếu cần mở rộng ở file khác:

```axiom
impl Vec2 {
    fn distance(self: Vec2, other: Vec2) -> f32 { ... }
}
```

Có thể hỗ trợ cả hai syntax; semantic vẫn là inherent function.

---

# 3. Trait

Trait chỉ định behavior contract.

```axiom
trait Printable {
    fn print(self: view<Self>)
}
```

Type implement:

```axiom
impl Printable for User {
    fn print(self: view<User>) {
        ...
    }
}
```

---

# 4. Trait không phải class interface

Trait không chứa:

- object identity;
- object header;
- mandatory vtable;
- inheritance state.

Trait chỉ mô tả behavior.

---

# 5. Static dispatch mặc định

```axiom
fn show<T: Printable>(x: view<T>) {
    x.print()
}
```

Compiler biết concrete `T`.

→ static dispatch.

Không có virtual call mặc định.

---

# 6. Dynamic dispatch explicit

Khi thực sự cần:

```axiom
fn show(x: dyn Printable) {
    x.print()
}
```

Lúc đó compiler tạo dynamic dispatch representation.

---

# 7. `dyn Trait` không implicit boxing

Ví dụ:

```axiom
let x: dyn Printable = user
```

không tự động có nghĩa:

```text
heap allocation
```

Compiler phải có representation phù hợp với semantic context; nếu API yêu cầu owned dynamic object thì storage abstraction phải nói rõ.

---

# 8. Default method

Trait có thể cung cấp implementation mặc định:

```axiom
trait Printable {
    fn print(self: view<Self>) {
        ...
    }
}
```

Type có thể dùng default.

---

# 9. Override

Nếu type muốn thay implementation:

```axiom
impl Printable for User {
    fn print(self: view<User>) {
        ...
    }
}
```

implementation này **thay default implementation**.

Không cần:

```text
override
```

---

# 10. Không có inheritance override

Axiom không có:

```text
class A
class B : A
override foo()
```

Thay vào đó:

```text
Trait
 ↓
default behavior
 ↓
concrete implementation
```

---

# 11. Đây chính là cơ chế override của Axiom

Ví dụ:

```axiom
trait Shape {
    fn area(self: view<Self>) -> f64
}

struct Circle { radius: f64 }
struct Rectangle { w: f64, h: f64 }

impl Shape for Circle {
    fn area(self: view<Circle>) -> f64 {
        ...
    }
}

impl Shape for Rectangle {
    fn area(self: view<Rectangle>) -> f64 {
        ...
    }
}
```

Không cần class hierarchy.

---

# 12. Extension function

Một function có first parameter là type có thể được gọi bằng method syntax nếu được import:

```axiom
fn clamp(self: f32, min: f32, max: f32) -> f32
```

sau khi import module:

```axiom
import math.clamp
```

có thể:

```axiom
x.clamp(0.0, 1.0)
```

---

# 13. Extension không override inherent function

Nếu đã có:

```axiom
fn length(self: Vec2)
```

mà module khác định nghĩa:

```axiom
fn length(self: Vec2)
```

thì không silently replace.

Compiler báo ambiguity/conflict.

---

# 14. Method resolution order

Freeze:

```text
1. Inherent methods
2. Trait implementations
3. Explicitly imported extension methods
4. Generic extension methods
```

---

# 15. Inherent luôn có priority

Điều này rất quan trọng để API predictable.

Nếu type có:

```axiom
fn size(self: Vec)
```

thì một extension:

```axiom
fn size(self: Vec)
```

không được hijack call.

---

# 16. Trait conflict

Nếu:

```axiom
trait A {
    fn foo(...)
}

trait B {
    fn foo(...)
}
```

và type implement cả hai:

```axiom
impl A for X
impl B for X
```

thì:

```axiom
x.foo()
```

→ ambiguity nếu compiler không có cách resolve rõ ràng.

---

# 17. Explicit trait qualification

Cho phép:

```axiom
A::foo(x)
B::foo(x)
```

để giải quyết ambiguity.

Đây là cách đơn giản hơn nhiều so với implicit magic.

---

# 18. Trait không cần inheritance

Không cần:

```text
trait B: A
```

cho v1 nếu chưa thực sự cần.

Nhưng trait constraints vẫn có thể:

```axiom
fn foo<T: A + B>(...)
```

---

# 19. Supertrait

Nếu cần semantic dependency:

```axiom
trait Ordered: Comparable
```

có thể hỗ trợ.

Nhưng đây là **trait constraint dependency**, không phải class inheritance.

---

# 20. Fundamental traits

Axiom nên có một nhóm trait chuẩn.

### Semantic traits

```text
Copy
Clone
Drop
Send
Share
```

### Comparison

```text
Eq
Ord
```

### Hash

```text
Hash
```

### Formatting

```text
Display
Debug
```

### Construction

```text
Default
```

### Iteration

```text
Iterator
IntoIterator
```

### Operators

```text
Add
Sub
Mul
Div
Rem
Neg

BitAnd
BitOr
BitXor
Shl
Shr
Not
```

---

# 21. `Copy`

`Copy` là semantic property.

```axiom
trait Copy {}
```

Nhưng programmer không nên implement tùy ý nếu type có Drop/resource semantics.

Compiler kiểm tra.

---

# 22. Copy không đồng nghĩa bitwise-copy

Đã freeze:

```text
bitwise copyability
    ≠
semantic Copy
```

Compiler có thể derive Copy khi hợp lệ.

---

# 23. `Clone`

`Clone` nghĩa:

> explicit duplication operation.

```axiom
trait Clone {
    fn clone(self: view<Self>) -> Self
}
```

Có thể tốn tài nguyên.

---

# 24. Copy vs Clone

Ví dụ:

```text
Copy
→ implicit value duplication

Clone
→ explicit potentially expensive duplication
```

Một type có thể:

```text
Copy + Clone
```

nhưng `Clone` không bắt buộc nếu không cần.

---

# 25. `Drop`

Drop là resource cleanup.

Không được đồng thời:

```text
Copy + Drop
```

---

# 26. Drop không trả Result

Đã freeze:

```text
Drop::drop()
```

không recoverable-fail.

Nếu cần:

```axiom
file.close() -> Result<(), IoError>
```

sau đó Drop chỉ fallback cleanup.

---

# 27. `Send`

`Send` biểu thị:

> ownership có thể chuyển execution domain.

Compiler nên **derive tự động**.

Không để programmer khai báo sai:

```axiom
unsafe impl Send for X
```

trong Core v1.

---

# 28. `Share`

`Share` biểu thị:

> value có thể được shared/concurrently accessed theo contract.

Cũng compiler-derived.

---

# 29. Send ≠ Share

Ví dụ:

```text
T: Send
T: !Share
```

hoàn toàn hợp lệ.

Ví dụ một resource có thể transfer sang thread mới nhưng không được concurrent share.

---

# 30. Share ≠ mutable sharing

Một object có thể:

```text
Share
```

chỉ vì concurrent read-safe.

Mutable shared access vẫn cần synchronization.

---

# 31. `Eq`

Semantic equality:

```axiom
trait Eq {
    fn eq(self: view<Self>, other: view<Self>) -> bool
}
```

Không mặc định đồng nghĩa bytewise equality.

---

# 32. Floating-point equality

`f32/f64` phải follow defined floating semantics.

Không dùng:

```text
memcmp(a,b)
```

để thay thế semantic equality.

---

# 33. `Ord`

Ordered comparison.

Không phải mọi `Eq` đều có total ordering.

Có thể cần:

```text
Ord
PartialOrd
```

---

# 34. Có nên có PartialEq/PartialOrd?

Tôi đề xuất **có**, nhưng programmer-facing API có thể đơn giản:

```text
Eq
PartialEq
Ord
PartialOrd
```

Lý do: floating point và một số mathematical types không có total ordering.

---

# 35. Hash

```axiom
trait Hash {
    fn hash(self: view<Self>, state: mut_view<Hasher>)
}
```

Invariant:

```text
a == b
⇒
hash(a) == hash(b)
```

nếu cả hai implement cùng hashing contract.

---

# 36. Display

User-facing formatting:

```axiom
trait Display {
    fn fmt(...)
}
```

---

# 37. Debug

Developer representation:

```axiom
trait Debug
```

khác Display.

---

# 38. Default

```axiom
trait Default {
    fn default() -> Self
}
```

Không phải mọi type đều phải Default.

---

# 39. Iterator

Core protocol:

```axiom
trait Iterator {
    type Item

    fn next(mut_view<Self>) -> Option<Self::Item>
}
```

---

# 40. `IntoIterator`

```axiom
trait IntoIterator {
    type Item
    type Iter: Iterator<Item = Self::Item>

    fn into_iter(self) -> Self::Iter
}
```

Điều này cho phép:

```axiom
for x in collection
```

---

# 41. Three iteration modes

API có thể hỗ trợ:

```text
consume
read
mutate
```

tương ứng ownership/capability semantics.

---

# 42. Index

```axiom
trait Index<I> {
    type Output

    fn index(self: view<Self>, index: I) -> view<Self::Output>
}
```

Compiler syntax:

```axiom
x[i]
```

---

# 43. IndexMut

```axiom
trait IndexMut<I> {
    fn index_mut(self: mut_view<Self>, index: I)
        -> mut_view<Self::Output>
}
```

Conceptually.

Compiler có thể lower trực tiếp.

---

# 44. Operators

Operator syntax là language syntax.

Semantics có thể trait-based:

```axiom
a + b
```

→ `Add::add(a,b)`.

---

# 45. Không overload tùy tiện

Operator resolution phải deterministic.

Không cho phép implicit conversion chain để tìm operator.

---

# 46. Numeric primitives

Primitive arithmetic có compiler intrinsic fast path.

Không nhất thiết phải instantiate generic trait machinery trong machine IR.

---

# 47. `Add<T>`

Có thể:

```axiom
trait Add<Rhs = Self> {
    type Output
    fn add(self: Self, rhs: Rhs) -> Self::Output
}
```

Default type parameter có thể hữu ích, nhưng nếu generic defaults làm language complexity tăng mạnh thì có thể freeze ở library/compiler level.

---

# 48. Operator return type

Không bắt buộc:

```text
T + T -> T
```

Có thể:

```text
Matrix + Matrix -> Matrix
Vector * Scalar -> Vector
```

---

# 49. Assignment operators

Có thể derive từ operator hoặc có trait riêng.

Không cần duplicate semantics nếu compiler có thể lower:

```text
x += y
```

thành appropriate mutation operation.

---

# 50. Equality operator

```text
==
!=
```

dùng Eq semantics.

---

# 51. Ordering operators

```text
<
<=
>
>=
```

dùng PartialOrd/Ord tùy type.

---

# 52. No inheritance-based polymorphism

Axiom polymorphism gồm:

```text
Generic
Trait
dyn Trait
```

Không có class inheritance.

---

# 53. Generic static polymorphism

Default:

```axiom
fn render<T: Renderable>(x: view<T>)
```

→ monomorphization.

---

# 54. Dynamic polymorphism

Explicit:

```axiom
fn render(x: dyn Renderable)
```

→ dynamic dispatch.

---

# 55. Generic vs dyn

Không tự động chuyển:

```text
T
```

thành:

```text
dyn Trait
```

nếu điều đó tạo allocation/dispatch semantics.

---

# 56. Object safety

Để `dyn Trait` hoạt động, trait phải satisfy object-safety rules.

Compiler diagnostic rõ ràng nếu không.

---

# 57. Associated type

Ví dụ Iterator:

```axiom
trait Iterator {
    type Item
}
```

giúp tránh generic explosion ở source syntax.

---

# 58. Associated constants

Có thể:

```axiom
trait Numeric {
    const ZERO: Self
}
```

Compile-time.

---

# 59. Associated functions

Có thể:

```axiom
trait Factory {
    fn create() -> Self
}
```

---

# 60. Trait implementation coherence

Axiom cần coherence rule để tránh:

```text
package A
impl Trait for X

package B
impl Trait for X
```

và chương trình không biết implementation nào đúng.

---

# 61. Orphan rule

Đề xuất:

> Package chỉ được implement trait cho type nếu package sở hữu trait hoặc type.

Đây là rule đơn giản và mạnh.

---

# 62. Blanket implementation

Có thể:

```axiom
impl<T: Display> Debug for T { ... }
```

nhưng cần coherence checking.

---

# 63. Arbitrary overlapping impl

Không cho phép trong v1.

Nếu hai impl có thể cùng match:

```text
compile error
```

---

# 64. Specialization

Không hỗ trợ arbitrary specialization ở v1.

Nếu cần optimization:

```text
compiler intrinsic
```

hoặc controlled specialization sau.

---

# 65. Why?

Nếu mở specialization quá sớm:

```text
trait solver
+
coherence
+
overlap
+
negative impl
+
specialization
```

sẽ khiến compiler complexity tăng rất mạnh.

---

# 66. Negative trait bounds

Không cần:

```text
T: !Trait
```

trong v1.

Có thể thêm sau nếu ecosystem thực sự cần.

---

# 67. Auto traits

`Send` / `Share` là compiler-derived semantic properties.

Không cần programmer viết:

```text
auto trait
```

syntax.

---

# 68. Trait derivation

Có thể:

```axiom
@derive(Eq, Clone, Debug)
struct Point { ... }
```

Compiler-generated implementation.

---

# 69. Derive không phải macro

Đã thống nhất:

> `@derive` là typed compiler-known generation.

Generated implementation quay lại normal type/trait checking.

---

# 70. AI friendliness

Trait system nên expose machine-readable facts:

```text
TYPE
TRAITS
REQUIRED
PROVIDED
IMPLEMENTATIONS
AMBIGUITIES
```

AI agent có thể hiểu API mà không cần đọc implementation.

---

# 71. Method resolution diagnostics

Nếu:

```axiom
x.foo()
```

ambiguous, compiler nên báo:

```text
E-METHOD-AMBIGUOUS
candidate 1: A::foo
candidate 2: B::foo
```

và đưa cách qualify.

---

# 72. No hidden extension imports

Extension method phải đến từ import scope rõ ràng.

Tránh “một package import làm hàng trăm method tự nhiên xuất hiện”.

---

# 73. Prelude

Axiom có thể có implicit prelude nhỏ:

```text
Option
Result
Copy
Clone
Drop
Eq
Ord
Iterator
```

nhưng prelude phải cực kỳ ổn định.

---

# 74. Prelude không chứa mọi thứ

Không tự động import:

```text
HashMap
File
Socket
Thread
HTTP
JSON
```

---

# 75. Fundamental protocol map

```text
                    Type
                      │
        ┌─────────────┼──────────────┐
        │             │              │
     Ownership     Equality       Behavior
        │             │              │
 Copy Clone Drop   Eq Ord       Trait / Function
 Send Share        Hash          Extension
```

---

# 76. Struct-only OOP hoàn chỉnh

Với toàn bộ thiết kế hiện tại:

```axiom
struct Player {
    hp: i32
}

fn damage(self: mut_view<Player>, amount: i32) {
    self.hp -= amount
}
```

gọi:

```axiom
player.damage(10)
```

Compiler hiểu:

```text
damage(mut_view(player), 10)
```

Không cần class.

---

# 77. “Override method” theo Axiom

Nếu behavior là intrinsic:

```text
function
```

không có override.

Nếu behavior cần polymorphism:

```text
trait
```

Ví dụ:

```axiom
trait Draw {
    fn draw(self: view<Self>)
}
```

Type implementation:

```axiom
impl Draw for Player {
    fn draw(...) { ... }
}
```

Đó chính là override contract.

---

# 78. Default implementation

```axiom
trait Draw {
    fn draw(self: view<Self>) {
        default_draw()
    }
}
```

Concrete type:

```axiom
impl Draw for Player {
    fn draw(...) {
        player_specific_draw()
    }
}
```

---

# 79. Không có “virtual” keyword

Static dispatch:

```text
T: Trait
```

Dynamic dispatch:

```text
dyn Trait
```

đủ rõ.

---

# 80. Fundamental principle

> **Function is behavior. Trait is behavior contract. dyn Trait is dynamic behavior.**

Không cần class.

---

# BOOTSTRAP-046 — Invariants

```text
ATRAIT-20   Functions are the fundamental behavior primitive.
ATRAIT-21   Methods are syntax sugar over functions.
ATRAIT-22   A method receiver is represented by the first semantic parameter.
ATRAIT-23   Structs do not require classes for behavior.
ATRAIT-24   Inherent functions have highest method-resolution priority.
ATRAIT-25   Traits define behavior contracts, not object inheritance.
ATRAIT-26   Traits do not require object headers.
ATRAIT-27   Traits do not require vtables for static dispatch.
ATRAIT-28   Static trait dispatch is the default.
ATRAIT-29   Dynamic dispatch requires explicit dyn Trait semantics.
ATRAIT-30   dyn Trait does not imply implicit heap allocation.
ATRAIT-31   Trait default methods may be replaced by concrete implementations.
ATRAIT-32   Default-method replacement does not require an override keyword.
ATRAIT-33   Trait implementation is the primary override mechanism.
ATRAIT-34   Class inheritance is not part of Core.
ATRAIT-35   Extension methods are ordinary functions with receiver-compatible parameters.
ATRAIT-36   Extension methods require explicit import visibility.
ATRAIT-37   Extension methods cannot silently override inherent methods.
ATRAIT-38   Method resolution is deterministic.
ATRAIT-39   Method resolution order is inherent, trait, imported extension, generic extension.
ATRAIT-40   Ambiguous method resolution is a compile-time error.
ATRAIT-41   Explicit trait qualification resolves trait-method ambiguity.
ATRAIT-42   Trait polymorphism does not require inheritance.
ATRAIT-43   Generic trait polymorphism uses static dispatch by default.
ATRAIT-44   dyn Trait uses explicit dynamic dispatch semantics.
ATRAIT-45   Object safety is required for dynamic trait values.
ATRAIT-46   Trait associated types are compile-time semantic entities.
ATRAIT-47   Trait associated constants are compile-time semantic entities unless explicitly materialized.
ATRAIT-48   Trait associated functions participate in normal trait resolution.
ATRAIT-49   Copy is a semantic value-duplication property.
ATRAIT-50   Copy is distinct from bitwise-copyability.
ATRAIT-51   Clone represents explicit potentially expensive duplication.
ATRAIT-52   A type with Drop semantics cannot implement Copy.
ATRAIT-53   Drop performs deterministic cleanup.
ATRAIT-54   Drop is non-fallible.
ATRAIT-55   Send represents transferable ownership across execution domains.
ATRAIT-56   Share represents valid concurrent shared access semantics.
ATRAIT-57   Send does not imply Share.
ATRAIT-58   Share does not imply mutable concurrent access.
ATRAIT-59   Send and Share are compiler-derived semantic properties.
ATRAIT-60   Programmer code cannot silently assert incorrect Send/Share semantics.
ATRAIT-61   Eq represents semantic equality.
ATRAIT-62   Semantic equality is distinct from bytewise equality.
ATRAIT-63   Floating-point equality follows defined numeric semantics.
ATRAIT-64   Partial ordering may differ from total ordering.
ATRAIT-65   Hash implementations must preserve equality/hash compatibility.
ATRAIT-66   Display and Debug represent distinct formatting contracts.
ATRAIT-67   Default is opt-in through trait implementation.
ATRAIT-68   Iterator is a fundamental library protocol.
ATRAIT-69   IntoIterator defines collection-to-iterator conversion.
ATRAIT-70   Iteration preserves explicit ownership/capability semantics.
ATRAIT-71   Index and IndexMut are library/compiler protocols.
ATRAIT-72   Operator syntax may lower to trait operations.
ATRAIT-73   Primitive arithmetic may use compiler intrinsic fast paths.
ATRAIT-74   Operator overload resolution is deterministic.
ATRAIT-75   Implicit conversion chains are not used to resolve operators.
ATRAIT-76   Trait implementation coherence is mandatory.
ATRAIT-77   The orphan rule prevents conflicting foreign trait/type implementations.
ATRAIT-78   Arbitrary overlapping implementations are rejected in Core v1.
ATRAIT-79   Arbitrary specialization is not part of Core v1.
ATRAIT-80   Negative trait bounds are not required by Core v1.
ATRAIT-81   Send/Share auto-properties need no source-level auto-trait syntax.
ATRAIT-82   @derive performs typed compiler-known trait generation.
ATRAIT-83   Generated trait implementations undergo normal semantic verification.
ATRAIT-84   Trait solver behavior is deterministic.
ATRAIT-85   Trait resolution results are available to downstream IR.
ATRAIT-86   Backend code generation does not perform trait solving.
ATRAIT-87   Method-resolution diagnostics identify competing candidates.
ATRAIT-88   Extension imports do not silently modify unrelated scopes.
ATRAIT-89   Prelude contains only a small set of fundamental definitions.
ATRAIT-90   Standard Library APIs are not implicitly imported through the language prelude.
ATRAIT-91   Trait abstractions can be fully erased under static dispatch.
ATRAIT-92   Dynamic dispatch is emitted only when its semantics are required.
ATRAIT-93   Trait abstraction does not imply runtime metadata.
ATRAIT-94   Trait behavior can be implemented independently of data representation.
ATRAIT-95   Struct data and trait behavior remain separate semantic concepts.
ATRAIT-96   Function implementation is not virtual unless dynamic dispatch is selected.
ATRAIT-97   Trait default implementation is not class inheritance.
ATRAIT-98   Override semantics are explicit through trait implementation.
ATRAIT-99   Method syntax does not change function ownership/capability semantics.
ATRAIT-100  Trait design must preserve zero-cost static abstraction opportunities.
```

## Một điểm quan trọng đã được giải quyết

Ý tưởng ban đầu của bạn:

> **“Chỉ cần struct, hàm nào có tham số đầu tiên là struct đó thì coi như method.”**

Hoàn toàn có thể trở thành nền tảng của Axiom.

Nhưng cần thêm một ranh giới:

```text
Function
    ↓
behavior cho một type

Trait
    ↓
behavior contract / polymorphism

dyn Trait
    ↓
runtime polymorphism
```

Vì vậy Axiom không cần `class`, `virtual`, `override`, `interface`, `abstract class` hay inheritance hierarchy.

Đồng thời compiler vẫn có đủ thông tin để **inline + specialize + devirtualize + erase abstraction**.

---

### Tiếp theo

Phần tiếp theo nên là **BOOTSTRAP-047 — Module/Namespace/Import + Name Resolution nâng cao**, nhưng phần package/build cơ bản đã freeze ở 042. Vì vậy trọng tâm lần này sẽ là **visibility, symbol identity, re-export, cyclic dependency, generic name lookup, trait namespace, extension namespace và đặc biệt cách AI có thể truy vấn API của Axiom mà không phải đọc cả source tree**.