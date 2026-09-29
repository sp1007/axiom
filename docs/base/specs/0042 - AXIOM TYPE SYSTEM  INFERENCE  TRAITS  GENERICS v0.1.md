Tiếp tục với phần **AXIOM TYPE INFERENCE + TRAIT RESOLUTION + GENERICS v0.1**. Tôi muốn xử lý phần này theo hướng **compiler có thể rất thông minh, nhưng source language vẫn đơn giản và quyết định phải deterministic**.

# AXIOM TYPE SYSTEM / INFERENCE / TRAITS / GENERICS v0.1

## 1. Nguyên tắc lớn

Axiom nên tránh hai cực:

```text
C/C++
→ quá nhiều implicit conversion + overload rules

Rust
→ type system mạnh nhưng ngày càng nhiều edge cases

Axiom
→ compiler inference mạnh
→ source syntax ít
→ resolution deterministic
```

Nguyên tắc:

> **Implicit inference được phép; implicit semantic conversion thì hạn chế.**

Ví dụ:

```axiom
let x = 10
```

compiler infer type.

Nhưng:

```axiom
let x: i64 = some_u32
```

không tự ý convert `u32 → i64` nếu conversion không được định nghĩa rõ.

---

# 2. Type identity

Hai type có representation giống nhau vẫn có thể khác type.

```axiom
type UserId = distinct u64
type ProductId = distinct u64
```

Khi đó:

```text
UserId != ProductId != u64
```

Không được:

```axiom
let p: ProductId = user_id
```

Điều này cực kỳ hữu ích để loại bug ID nhầm lẫn.

---

# 3. Alias khác distinct

Axiom có hai khái niệm:

```axiom
type UserId = u64
```

là alias.

```axiom
type UserId = distinct u64
```

là nominal newtype.

| | Alias | Distinct |
|---|---|---|
| Type identity | giống type gốc | type mới |
| ABI | như type gốc | compiler quyết định |
| Conversion | không cần | explicit |
| Dùng overload/trait | như type gốc | độc lập |
| Zero-cost | có | có thể |

---

# 4. Type inference

Mọi expression cuối cùng phải có **exactly one resolved type**.

Ví dụ:

```axiom
let x = 10
```

Literal ban đầu có type metavariable:

```text
T0 : IntegerLiteral
```

Nếu context không cung cấp thêm thông tin, Axiom phải có rule rõ ràng.

Tôi đề xuất:

> Integer literal không có context → `i32`.

Nhưng chỉ **literal**, không phải arbitrary integer expression.

Ví dụ:

```axiom
let x = 10        // i32
let y = 10u64     // u64
```

Có thể dùng suffix:

```text
10i8
10i16
10i32
10i64
10u8
10u16
10u32
10u64
10f32
10f64
```

---

# 5. Không có “guessing” type

Không nên:

```axiom
let x = []
```

rồi compiler đoán:

```text
Array<i32, 0>
```

Đây là ambiguity.

Phải có context:

```axiom
let x: Array<i32, 0> = []
```

hoặc constructor rõ ràng.

---

# 6. Generic inference

Ví dụ:

```axiom
fn max<T: Comparable>(a: T, b: T) -> T
```

Gọi:

```axiom
max(10, 20)
```

compiler suy ra:

```text
T = i32
```

Không cần:

```axiom
max<i32>(10, 20)
```

trừ khi ambiguity.

---

# 7. Generic inference không được dựa vào runtime

Đây là compile-time:

```text
Source
 ↓
type inference
 ↓
generic resolution
 ↓
specialization
 ↓
MIR
```

Runtime không cần biết `T` là gì nếu specialization đủ.

---

# 8. Generic specialization

Ví dụ:

```axiom
fn sum<T: Add>(a: T, b: T) -> T {
    a + b
}
```

Compiler có thể tạo:

```text
sum<i32>
sum<i64>
sum<f32>
...
```

Sau đó optimizer:

```text
inline
constant propagate
vectorize
eliminate abstraction
```

Mục tiêu:

```text
generic source
≈
hand-written specialized code
```

---

# 9. Không dùng C++ textual template substitution

Đây là điểm quan trọng.

Axiom:

```text
Generic Source
    ↓
Typed Generic HIR
    ↓
Constraint solving
    ↓
Instantiation
    ↓
Typed MIR
```

Không phải:

```text
text substitution
↓
parse lại
```

Điều này giúp diagnostics và compiler architecture sạch hơn.

---

# 10. Trait

Trait chỉ mô tả behavior.

```axiom
trait Add<Rhs, Output> {
    fn add(self: Self, rhs: Rhs) -> Output
}
```

Ví dụ:

```axiom
impl Add<i32, i32> for i32 {
    ...
}
```

Trait không phải inheritance.

---

# 11. Property ≠ Trait

Đây là quyết định nên giữ rất chặt.

```text
Copy
Drop
Send
Share
Sized
```

là **compiler-known semantic properties**.

Trong khi:

```text
Drawable
Iterator
Serialize
Hash
Comparable
```

là behavioral traits.

Không trộn hai hệ này.

---

# 12. Vì sao?

`Copy` ảnh hưởng trực tiếp ownership verifier.

```axiom
let b = a
```

Nếu `a: Copy`:

```text
COPY
```

Nếu không:

```text
MOVE
```

Nếu `Copy` chỉ là trait bình thường, ownership verifier sẽ phải phụ thuộc trait resolution ở mức semantic rất sâu.

Tách riêng giúp compiler deterministic hơn.

---

# 13. Trait constraints

Ví dụ:

```axiom
fn print<T: Display>(x: T) {
    ...
}
```

Compiler tạo constraint:

```text
T implements Display
```

Sau đó resolve implementation.

Nếu không có:

```text
AX_TRAIT_....
```

compile error.

---

# 14. Multiple constraints

```axiom
fn foo<T: Copy + Comparable + Send>(x: T)
```

nghĩa:

```text
T must satisfy:
    Copy
    Comparable
    Send
```

Không phải inheritance.

---

# 15. `where`

Tôi đề xuất hỗ trợ `where` để generic signature không biến thành một dòng quá dài:

```axiom
fn merge<A, B>(a: A, b: B) -> Result<A, B>
where
    A: Comparable
    B: Clone
{
    ...
}
```

Đây là syntax convenience, không thêm semantic concept.

---

# 16. Associated type

Tôi nghĩ Axiom nên có associated type ngay từ đầu.

Ví dụ:

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self::Item>
}
```

Sau đó:

```axiom
impl Iterator for Counter {
    type Item = i32
    ...
}
```

Điều này tốt hơn việc biến mọi thứ thành generic parameter.

---

# 17. Nhưng associated type phải được resolve compile-time

Ví dụ:

```axiom
T::Item
```

phải resolve thành một type cụ thể trước MIR.

Không có runtime lookup.

---

# 18. Trait implementation uniqueness

Axiom cần tránh ambiguity.

Ví dụ:

```axiom
impl Foo for A
impl Foo for A
```

→ lỗi.

Nhưng còn:

```axiom
impl<T: A> Foo for T
impl<T: B> Foo for T
```

nếu có type thỏa cả A và B?

Đây là vấn đề specialization/coherence.

Tôi đề xuất **không cho overlapping impl trong v0.1**.

---

# 19. Coherence rule

Axiom nên dùng orphan/coherence rule đơn giản:

Một `impl Trait for Type` chỉ hợp lệ nếu:

```text
Trait thuộc module/package hiện tại
OR
Type thuộc module/package hiện tại
```

Không cho:

```text
foreign Trait
+
foreign Type
```

Ví dụ library A định nghĩa:

```text
Trait X
```

library B định nghĩa:

```text
Type Y
```

library C không được tự tạo:

```text
impl X for Y
```

nếu cả X và Y đều foreign.

---

# 20. Tại sao?

Nếu cho phép tự do:

```text
Package A
Package B
Package C
Package D
```

mỗi package có thể thêm impl.

Cuối cùng compiler không biết implementation nào được chọn.

Coherence giúp:

```text
same program
→ same resolution
```

---

# 21. Method resolution

Axiom có:

```axiom
v.length()
```

Compiler tìm theo thứ tự:

```text
1. inherent function của type
2. trait implementation phù hợp
3. imported extension function
```

Nếu có nhiều candidate cùng mức:

```text
AMBIGUOUS
```

Không tự chọn “gần giống nhất”.

---

# 22. Inherent method

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: Vec2) -> f32 {
    ...
}
```

Gọi:

```axiom
v.length()
```

→ `length(v)`.

---

# 23. Extension function

Có thể module khác viết:

```axiom
fn length(self: view<Vec2>) -> f32
```

và import:

```axiom
import geometry.length
```

Sau đó:

```axiom
v.length()
```

được phép.

Nhưng extension phải được import rõ ràng.

Điều này tránh namespace pollution.

---

# 24. Không có “magical global extension methods”

Tôi khuyên:

```text
extension method
→ explicit import
```

Không import:

```text
→ không tồn tại trong method lookup
```

Compiler deterministic hơn.

---

# 25. Operator

Operator nên là syntax sugar cho intrinsic/trait.

Ví dụ:

```axiom
a + b
```

semantic:

```text
Add.add(a, b)
```

Nhưng compiler có thể special-case primitive:

```text
i32 + i32
→ INTEGER_ADD_CHECKED
```

Không nhất thiết tạo dynamic dispatch.

---

# 26. Operator overload

Cho phép user-defined operator nhưng phải cực kỳ hạn chế.

Ví dụ:

```axiom
impl Add<Vec2, Vec2> for Vec2 {
    fn add(self: Vec2, rhs: Vec2) -> Vec2 { ... }
}
```

Không cho operator tự sinh hàng loạt implicit conversion.

---

# 27. Không có conversion chain

Ví dụ:

```text
A → B
B → C
C → D
```

Axiom không nên tự tìm:

```text
A → B → C → D
```

để làm:

```axiom
foo(d)
```

Điều này là nguồn complexity rất lớn.

Nếu cần:

```axiom
foo(d)
```

phải có conversion trực tiếp hoặc programmer viết explicit conversion.

---

# 28. Coercion

Axiom chỉ nên có một số coercion **semantic-safe và local**.

Tôi đề xuất:

```text
T → view<T>
T → mut_view<T>
```

nhưng chỉ trong ephemeral argument context như đã khóa trước.

Ví dụ:

```axiom
fn sum(x: view<i32>) -> i32

sum(array)
```

Compiler tạo temporary view.

Nhưng:

```axiom
let v = array
```

không tự đổi thành view.

Muốn view:

```axiom
let v = view(array)
```

---

# 29. Không có implicit numeric widening?

Đây là chỗ tôi muốn sửa/khóa rõ hơn.

Để giữ language predictable:

```axiom
let x: i64 = i32_value
```

**không implicit convert**.

Phải:

```axiom
let x: i64 = i32_value as i64
```

Mặc dù `i32 → i64` thường an toàn.

Lý do: tránh expression type thay đổi theo context quá nhiều.

---

# 30. Nhưng literal được context-convert

Có ngoại lệ:

```axiom
let x: i64 = 10
```

hợp lệ.

Vì `10` chưa có concrete integer type trước khi context resolution.

Khác với:

```axiom
let y: i32 = some_i64
```

→ cần explicit conversion.

---

# 31. Generic numeric literals

Ví dụ:

```axiom
fn square<T: Mul<T, T>>(x: T) -> T {
    x * x
}

square(10)
```

Có thể ambiguity vì `10` chưa biết T.

Compiler cần giải constraint:

```text
T must satisfy Mul<T,T>
```

Nếu có nhiều candidate:

```text
ambiguous generic inference
```

Programmer có thể:

```axiom
square(10i64)
```

---

# 32. Không có “fallback to i32” nếu generic context chưa đủ

Ví dụ:

```axiom
fn foo<T>(x: T) {}

foo(10)
```

Có thể infer:

```text
T = i32
```

vì literal default rule.

Nhưng:

```axiom
fn foo<T: SomeTrait>(x: T) {}
```

nếu `i32` không satisfy hoặc nhiều resolution:

```text
error
```

Không thử random type.

---

# 33. Generic type variance

Tôi đề xuất **không đưa variance syntax vào Core v0.1**.

Không cần:

```text
in T
out T
```

Axiom không có class inheritance nên vấn đề covariance/contravariance giảm đáng kể.

`view<T>` có semantic rules riêng.

---

# 34. Function types

Function:

```text
fn(i32, i32) -> i32
```

là structural type.

Hai function signature giống nhau → cùng function type.

Closure type thì khác.

---

# 35. Closure không tự động là function pointer

```axiom
let f = |x| x + 1
```

`f` là closure value.

Compiler có thể:

```text
inline
```

hoặc nếu escape:

```text
environment + function pointer
```

Nếu cần function pointer:

```axiom
let f: fn(i32) -> i32 = ...
```

compiler kiểm tra closure không có incompatible environment hoặc tạo thunk phù hợp.

---

# 36. Generic function vs function value

```axiom
fn max<T>(a: T, b: T) -> T
```

không phải một runtime polymorphic function.

Khi dùng:

```axiom
let f = max
```

compiler phải biết specialization/context.

Nếu không đủ context:

```text
ambiguous generic function value
```

---

# 37. Static dispatch

Default:

```text
generic
+
trait constraint
```

→ static dispatch.

Ví dụ:

```axiom
fn draw<T: Drawable>(x: T) {
    x.draw()
}
```

Compiler specialize:

```text
draw<Circle>
draw<Square>
```

Không có vtable bắt buộc.

---

# 38. Dynamic dispatch

Chỉ khi programmer yêu cầu abstraction runtime.

Ví dụ conceptually:

```axiom
let x: dyn Drawable = circle
```

`dyn` sẽ là explicit type-erasure.

Representation có thể:

```text
data_ptr
dispatch_ptr
```

Nhưng đây là ABI detail.

Không có:

```text
vtable
```

ẩn trong mọi struct.

---

# 39. Dynamic dispatch phải có cost rõ ràng

Đây là nguyên tắc:

> **Nếu programmer yêu cầu runtime polymorphism, programmer chấp nhận dynamic dispatch cost.**

Compiler không được tự động biến static trait call thành dynamic chỉ vì tiện.

Ngược lại optimizer có thể devirtualize nếu chứng minh được.

---

# 40. Type erasure

`dyn Trait` không phải inheritance.

Nó là:

```text
concrete value
↓
type-erased interface
↓
runtime dispatch
```

Có thể có ownership semantics riêng:

```text
dyn Trait
dyn view<dyn Trait>
```

nhưng exact syntax có thể đóng sau.

---

# 41. Generic type

```axiom
struct Vec<T> {
    ...
}
```

Mỗi `Vec<T>` là một concrete specialization khi cần code generation.

Không cần runtime type parameter.

---

# 42. Generic layout

Compiler được phép:

```text
Vec<i32>
Vec<f32>
```

có layout tối ưu riêng.

Không phải một object layout universal.

Điều này rất tốt cho native performance.

---

# 43. Generic code bloat

Đây là một rủi ro thực tế.

Nếu:

```text
foo<T>
```

được instantiate 500 type:

```text
500 machine copies
```

binary có thể lớn.

Axiom nên cho compiler có freedom:

```text
monomorphize
```

hoặc:

```text
share code
```

nếu ABI/representation cho phép.

Nhưng semantic vẫn static.

---

# 44. Vì vậy Generic Code Generation nên có 3 tầng

```text
Generic HIR
   ↓
Specialized MIR
   ↓
Optimized specialized machine code
```

Compiler có thể quyết định:

```text
inline
specialize
merge identical bodies
outline
```

để cân bằng:

```text
performance
binary size
compile time
```

---

# 45. Typeclass-style ambiguity

Ví dụ:

```axiom
trait A {}
trait B {}

impl A for X {}
impl B for X {}
```

Không có vấn đề.

Nhưng:

```axiom
fn foo<T: A>(x: T)
fn foo<T: B>(x: T)
```

Tôi đề xuất:

> **Không cho overload function chỉ khác generic constraints trong v0.1.**

Nếu gọi:

```axiom
foo(x)
```

sẽ ambiguity rất khó hiểu.

---

# 46. Function overloading — quyết định quan trọng

Tôi đề xuất Axiom **không có C++-style arbitrary function overloading**.

Không:

```axiom
fn foo(i32)
fn foo(i64)
fn foo(String)
fn foo<T>(T)
```

rồi compiler làm overload ranking phức tạp.

Thay vào đó:

```axiom
foo_i32(...)
foo_i64(...)
foo_text(...)
```

hoặc generic/trait:

```axiom
foo<T: Foo>(x: T)
```

---

# 47. Nhưng method/trait vẫn có cùng tên

Điều này vẫn cho phép:

```axiom
x.draw()
```

vì method resolution có namespace/type context.

Đây là **controlled overloading**, không phải global overload set.

---

# 48. Tôi đánh giá đây là lựa chọn rất đáng giá

Nó loại bỏ rất nhiều thứ:

```text
implicit conversion ranking
promotion ranking
template partial ordering
SFINAE-style behavior
ADL-like surprises
constraint overload ambiguity
```

Compiler nhẹ về semantic complexity hơn, trong khi programmer vẫn có:

```text
generic
trait
method syntax
operator
```

---

# 49. Type resolution pipeline

Tôi đề xuất pipeline chính thức:

```text
AST
 │
 ▼
Name Resolution
 │
 ▼
Type Inference
 │
 ▼
Constraint Generation
 │
 ▼
Trait Resolution
 │
 ▼
Method / Operator Resolution
 │
 ▼
Coercion Resolution
 │
 ▼
Generic Instantiation
 │
 ▼
Typed HIR
```

Quan trọng:

> Không resolve trait trước khi có đủ type information.

---

# 50. Constraint solver

Compiler nội bộ có thể tạo:

```text
T0 = unknown
T0 : Drawable
T1 = T0
T2 = i32
```

Sau đó solve.

Ví dụ:

```axiom
let x = foo(a)
```

ban đầu:

```text
foo : fn<T>(T) -> T
a : i32
```

solve:

```text
T = i32
x : i32
```

---

# 51. Không để constraint solver vô hạn

Generic/trait system phải có termination guarantee.

Tôi đề xuất v0.1:

- no arbitrary recursive trait solver
- no overlapping impl
- no negative trait bounds
- no specialization rules phức tạp
- no compile-time trait execution.

Điều này giữ compiler predictable.

---

# 52. Negative bounds

Không cần:

```text
T: !Copy
```

ở v0.1.

Compiler-known property có thể được query internally:

```text
requires !Copy
```

nhưng source language chưa cần expose.

---

# 53. Auto properties

Compiler tự suy luận:

```text
struct Point {
    x: f32
    y: f32
}
```

→

```text
Copy
Sized
Send
Share
!Drop
```

nếu semantic conditions thỏa.

---

# 54. Drop propagation

```axiom
struct User {
    name: String
    age: i32
}
```

vì `String`:

```text
!Copy
Drop
```

nên:

```text
User
→ !Copy
→ Drop
```

Compiler derive.

Không cần programmer viết:

```text
impl Drop for User
```

nếu chỉ cần recursive destruction.

---

# 55. User-defined Drop

Nếu cần custom resource cleanup:

```axiom
impl Drop for File {
    ...
}
```

Compiler biết:

```text
File → Drop
```

và cấm:

```text
File → Copy
```

nếu Drop có destructive semantics.

---

# 56. `Send` propagation

Ví dụ:

```axiom
struct A {
    x: i32
    y: String
}
```

Nếu cả hai Send:

```text
A: Send
```

Nếu một field không Send:

```text
A: !Send
```

Compiler tự suy luận.

---

# 57. `Share`

Không đơn giản:

```text
all fields immutable
→ Share
```

Vì:

```text
Mutex<T>
```

có mutable interior synchronization nhưng vẫn có thể Share.

Do đó Share phải do type semantics quyết định.

---

# 58. `Sized`

Hầu hết type:

```text
Sized
```

Dynamic/unsized abstraction có thể tồn tại sau.

`dyn Trait` có thể là unsized semantic type:

```text
!Sized
```

nhưng phải nằm sau type-erasure layer.

---

# 59. Trait implementation và property

Không viết:

```axiom
impl Send for X
```

Send là compiler-known property.

Thay vào đó:

```text
X → Send
```

được compiler derive hoặc compiler intrinsic rule.

Điều này rất quan trọng để tránh programmer “fake” safety property.

---

# 60. Type system boundary

Tôi đề xuất đóng băng:

### Core semantic types

```text
bool
integer
float
tuple
array
struct
enum
function
closure
view
mut_view
Unit
Never
```

### Compiler-known properties

```text
Copy
Drop
Send
Share
Sized
```

### Behavioral traits

```text
user-defined
```

### Runtime polymorphism

```text
explicit dyn/type-erasure
```

### Conversion

```text
explicit
```

trừ literal resolution và safe temporary view coercion.

---

# 61. Bộ invariant mới

### ATSI-01
Every expression resolves to exactly one static type.

### ATSI-02
Inference cannot change observable ownership semantics.

### ATSI-03
Implicit semantic conversions are prohibited except explicitly defined safe coercions.

### ATSI-04
Numeric narrowing requires explicit conversion.

### ATSI-05
Literal typing is context-sensitive before concrete type assignment.

### ATSI-06
Generic constraints are resolved at compile time.

### ATSI-07
Generic specialization produces statically typed MIR.

### ATSI-08
Behavioral traits do not imply inheritance.

### ATSI-09
Semantic properties are distinct from behavioral traits.

### ATSI-10
Copy/Drop/Send/Share/Sized cannot be forged by ordinary trait implementation.

### ATSI-11
Overlapping trait implementations are prohibited in v0.1.

### ATSI-12
Coherence prevents foreign-trait/foreign-type orphan implementations.

### ATSI-13
Method resolution is deterministic.

### ATSI-14
Ambiguous method resolution is a compile error.

### ATSI-15
Extension methods require explicit import.

### ATSI-16
Arbitrary C++-style function overloading is not part of Core.

### ATSI-17
Trait dispatch is static by default.

### ATSI-18
Dynamic dispatch is explicit.

### ATSI-19
Generic code does not require runtime generic metadata.

### ATSI-20
Type aliases do not create new nominal types.

### ATSI-21
Distinct types create independent nominal identities.

### ATSI-22
Trait resolution terminates under the v0.1 rule set.

### ATSI-23
Type inference is deterministic and reproducible.

### ATSI-24
Compiler optimization cannot alter type-system semantics.

---

# 62. Một quyết định tôi đặc biệt muốn giữ

Axiom nên có triết lý:

```text
                IMPLICIT
                   │
          ┌────────┴────────┐
          │                 │
       Inference        Optimization
          │                 │
       allowed           allowed
          │                 │
          ▼                 ▼
       compiler          compiler
       decides           decides


                EXPLICIT
                   │
          ┌────────┴─────────┐
          │                  │
      Semantic risk      Runtime cost
          │                  │
      ownership          dynamic dispatch
      conversion         allocation
      unsafe              synchronization
      FFI                 stable address
```

Nói cách khác:

> **Axiom cho compiler quyền suy luận những gì không thay đổi semantics; nhưng bắt programmer nói rõ tại những điểm thay đổi ownership, representation, runtime behavior hoặc safety boundary.**

Đây là nguyên tắc có thể giúp Axiom vừa dễ viết vừa không biến thành một ngôn ngữ “magic”.

---

## Phần tiếp theo tôi đề xuất

Sau Type System, mảnh ghép rất đáng làm tiếp là:

**`AXIOM COLLECTIONS + ITERATOR + RANGE + STRING/TEXT + ERROR API v0.1`**

Nhưng trước khi đi vào library, tôi muốn khóa một vấn đề nền tảng hơn: **`struct` layout + field access + pattern matching + destructuring + generic layout + enum representation**.

Đây là chỗ quyết định Axiom có thực sự đạt được mục tiêu **“struct đơn giản nhưng hiệu năng kiểu C/C++”** hay không.