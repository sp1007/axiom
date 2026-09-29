Tiếp tục. Tôi sẽ khóa tiếp **Axiom Type System v0.1**, tập trung vào chỗ dễ làm ngôn ngữ phình to nhất: **inference, conversion, generic, trait solver và numeric types**.

# Axiom Type System v0.1

Mục tiêu:

> **Type system đủ mạnh để compiler chứng minh an toàn, nhưng không biến Axiom thành một theorem prover.**

Tôi đề xuất 5 nguyên tắc:

1. Static typing.
2. Không có implicit user-defined conversion.
3. Inference mạnh nhưng deterministic.
4. Generic/trait resolution có giới hạn.
5. Không có general subtype hierarchy.

---

# 1. Không có class hierarchy

Ta đã khóa:

```text
struct = data
trait  = behavior
impl   = relationship
```

Không có:

```text
class
inheritance
base class
virtual method mặc định
Object
Any
```

Do đó type relation không phải:

```text
Dog <: Animal <: Object
```

mà chủ yếu là:

```text
Dog
 ├── implements Animal
 ├── implements Speak
 └── implements Clone
```

Đây giúp type solver đơn giản hơn rất nhiều.

---

# 2. Trait không phải subtype

Ví dụ:

```axiom
trait Drawable {
    fn draw(self: view<Self>);
}

struct Circle {
    radius: f32
}

impl Drawable for Circle {
    ...
}
```

`Circle` **không trở thành** `Drawable`.

Nó chỉ thỏa constraint:

```text
Circle : Drawable
```

Đây là distinction rất quan trọng.

---

# 3. Generic

Ví dụ:

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

Compiler resolve:

```text
T
↓
concrete type
↓
specialization
↓
machine code
```

Thông thường:

```text
max<i32>
max<i64>
max<f32>
```

có thể trở thành những implementation khác nhau.

---

# 4. Generic không phải runtime abstraction mặc định

Không tạo:

```text
type_info
generic metadata
```

chỉ vì function generic.

Ví dụ:

```axiom
fn add<T: Add>(a: T, b: T) -> T
```

có thể compile trực tiếp thành:

```text
ADD i64
```

hoặc:

```text
ADD f64
```

hoặc custom implementation.

---

# 5. Monomorphization là default

V0.1:

```text
generic source
     ↓
type resolution
     ↓
specialization
     ↓
concrete MIR
```

Đây là hướng phù hợp mục tiêu native performance.

Nhưng compiler **có quyền code-share** nếu có lợi:

```text
T = u32
T = u64
```

có thể chia sẻ machine implementation nếu representation/semantics cho phép.

Do đó:

> Monomorphization là semantic strategy? **Không.** Nó là compiler strategy.

---

# 6. Type inference

Axiom nên có inference, nhưng không nên theo kiểu:

```text
solver tìm mọi type universe có thể
```

Tôi đề xuất:

> **Bidirectional type inference.**

Hai hướng:

```text
expression → infer type
expected type → constrain expression
```

Ví dụ:

```axiom
let x = 10;
```

literal `10` chưa nhất thiết phải lập tức chọn `i32`.

Nhưng:

```axiom
let x: i64 = 10;
```

expected type truyền xuống literal.

---

# 7. Numeric literal là vấn đề lớn

Nếu:

```axiom
let x = 10;
```

thì type gì?

Tôi đề xuất:

```text
integer literal
↓
default integer type = i32
```

Nếu context rõ:

```axiom
let x: u64 = 10;
```

→ `u64`.

Tương tự:

```axiom
let x: f64 = 1.5;
```

→ `f64`.

---

# 8. Không implicit conversion giữa numeric types

Ví dụ:

```axiom
let x: i64 = 10;
let y: i32 = x;
```

→ compile error.

Không tự động:

```text
i64 → i32
```

vì có thể mất dữ liệu.

---

# 9. Widening conversion cũng nên explicit

Tôi nghiêng về:

```axiom
let x: i32 = 100;
let y: i64 = x as i64;
```

thay vì:

```text
i32 → i64
```

implicit.

Điều này làm semantics cực kỳ dễ hiểu.

---

# 10. Nhưng numeric literal là ngoại lệ

```axiom
let x: i64 = 123;
```

không cần:

```axiom
123 as i64
```

vì `123` là **literal polymorphism tại compile time**, không phải runtime conversion.

Compiler kiểm tra:

```text
123 ∈ range(i64)
```

rồi encode trực tiếp.

---

# 11. Literal overflow

```axiom
let x: u8 = 300;
```

→ compile error.

Không wrap thành:

```text
44
```

và không runtime panic.

Vì đây là compile-time constant.

---

# 12. Literal suffix

Có thể hỗ trợ:

```text
10i8
10i16
10i32
10i64

10u8
10u16
10u32
10u64

1.0f32
1.0f64
```

Điều này hữu ích cho low-level code và generic inference.

---

# 13. `as` là explicit conversion

Ví dụ:

```axiom
let x = a as i64;
```

Nhưng `as` phải có semantics cụ thể.

Không nên biến `as` thành “làm bất cứ thứ gì”.

---

# 14. Chia conversion thành các loại

Tôi đề xuất:

```text
numeric cast
bit cast
pointer cast
address cast
```

Ví dụ:

```axiom
x as i64
```

numeric conversion.

```axiom
bit_cast::<u32>(x)
```

same-bit reinterpretation.

```axiom
ptr_cast::<T>(p)
```

unsafe pointer conversion.

```axiom
addr_of(p)
```

address extraction.

Không có:

```text
transmute<T,U>
```

vạn năng.

---

# 15. Numeric cast semantics

Cần tránh ambiguity.

Tôi đề xuất:

```text
integer → larger integer
```

sign extension / zero extension theo source signedness.

```text
integer → smaller integer
```

**defined truncation** nếu dùng explicit cast.

Ví dụ:

```axiom
let x: u16 = 300;
let y = x as u8;
```

→ `44`.

Không cần runtime check vì programmer đã viết explicit narrowing.

Nếu muốn checked:

```axiom
x.to_u8()
```

→ `Option<u8>` / `Result`.

---

# 16. Float → integer

Explicit:

```axiom
x as i32
```

phải có semantics rõ ràng.

Tôi đề xuất:

- truncate toward zero;
- NaN / infinity / out-of-range → trap.

Nếu cần saturating:

```text
to_i32_sat()
```

library/intrinsic.

Không để phụ thuộc CPU instruction.

---

# 17. Integer → float

```axiom
x as f64
```

được phép explicit.

Có thể mất precision nhưng đó là semantics của conversion, không phải lỗi memory safety.

---

# 18. Bool không phải integer

Không cho:

```axiom
true as i32
```

trừ explicit conversion API nếu thực sự cần.

Và không cho:

```axiom
if 1 { ... }
```

Axiom tránh C-style truthiness.

Chỉ:

```text
bool
```

được dùng trong condition.

---

# 19. Pointer không phải integer

Không cho:

```axiom
let x: usize = p;
```

Muốn lấy địa chỉ:

```axiom
let a: addr = address_of(p);
```

Muốn chuyển address thành integer:

```text
explicit unsafe conversion
```

Điều này đã phù hợp memory model.

---

# 20. `addr` và `usize`

Ta giữ distinction:

```text
usize = số nguyên kích thước/index
addr  = machine address
```

Không alias hai loại này.

Đây là một quyết định tốt cho compiler.

---

# 21. Type alias

```axiom
type UserId = u64;
```

là **same type**.

Do đó:

```axiom
fn load(id: UserId)
```

thực chất nhận `u64`.

Nếu muốn type riêng:

```axiom
struct UserId(u64);
```

Đây là **newtype**.

---

# 22. Newtype rất quan trọng

Ví dụ:

```axiom
struct UserId(u64);
struct ProductId(u64);
```

Compiler không cho:

```axiom
let p: ProductId = user_id;
```

dù representation đều là `u64`.

Nhưng:

```text
@repr(transparent)
```

có thể cho ABI-compatible representation.

---

# 23. Newtype không cần runtime overhead

```text
UserId(u64)
```

có thể compile chính xác như:

```text
u64
```

vì:

```text
semantic distinction
≠
machine representation
```

Đây là một ví dụ rất đẹp của Abstraction Erasure.

---

# 24. Tuple

Tuple là anonymous product type:

```axiom
let p = (10, 20);
```

type:

```text
(i32, i32)
```

Tuple có value semantics bình thường.

Destructure:

```axiom
let (x, y) = p;
```

Ownership checker xử lý như pattern destructuring.

---

# 25. Unit

```text
()
```

type:

```text
unit
```

Không cần object.

Có thể là ZST.

Ví dụ:

```axiom
fn foo() -> () {}
```

và:

```axiom
fn foo() {}
```

nên tương đương về semantic return type.

---

# 26. Never

```text
never
```

là type của:

```text
panic()
trap()
unreachable()
infinite_loop()
```

Ví dụ:

```axiom
let x: i32 =
    if condition {
        10
    } else {
        panic()
    };
```

branch thứ hai có `never`, nên expression type là `i32`.

---

# 27. Không cần general covariance/contravariance trong v0.1

Tôi đề xuất **không expose variance system** cho programmer.

Vì Axiom không có general subtyping.

Với:

```text
view<T>
mut_view<T>
```

compiler xử lý capability/provenance riêng.

Không biến chúng thành một hệ variance generic phức tạp.

---

# 28. `view<T>` không phải subtype của `T`

```axiom
fn foo(x: view<i32>) {}
```

Gọi:

```axiom
let x = 10;
foo(x);
```

được phép vì có:

```text
implicit ephemeral owner → view
```

nhưng:

```text
view<i32> = i32
```

không phải type equality.

Đây là contextual conversion đặc biệt do memory model quy định.

---

# 29. `mut_view`

Tương tự:

```axiom
fn increment(x: mut_view<i32>) {
    *x += 1;
}
```

có thể gọi:

```axiom
var x = 10;
increment(x);
```

Compiler tạo capability.

Nhưng:

```axiom
let v = mut_view(x);
```

là explicit binding.

Điều này tránh việc reference syntax tràn ngập source code.

---

# 30. Function types

Ví dụ:

```axiom
fn(i32, i32) -> i32
```

là function type.

Named function:

```axiom
fn add(a: i32, b: i32) -> i32
```

có thể coerce thành function pointer khi không có environment.

---

# 31. Function pointer và closure khác nhau

```text
fn(i32) -> i32
```

≠

```text
closure(i32) -> i32
```

Closure có environment.

Ví dụ:

```axiom
let k = 10;

let f = |x| x + k;
```

Conceptually:

```text
struct ClosureEnv {
    k: i32
}

fn closure_call(env: view<ClosureEnv>, x: i32) -> i32
```

---

# 32. Nhưng programmer không cần khai báo closure type

Compiler tạo anonymous concrete type.

Điều này cho phép:

```text
zero-cost static dispatch
```

mà không cần:

```text
Box<dyn Fn>
```

trong trường hợp bình thường.

---

# 33. `dyn Trait`

Chỉ khi programmer muốn dynamic dispatch:

```axiom
let x: dyn Drawable = ...
```

mới có runtime dispatch.

Conceptually:

```text
data pointer
+
dispatch pointer
```

Không có object header bắt buộc.

---

# 34. `dyn Trait` là explicit runtime cost

Điều này rất quan trọng.

```text
T: Trait
```

→ static generic dispatch.

```text
dyn Trait
```

→ dynamic dispatch.

Không có compiler magic âm thầm biến static code thành virtual calls.

---

# 35. Opaque type

Tôi đề xuất hỗ trợ:

```axiom
fn make() -> impl Iterator<Item = i32> {
    ...
}
```

Nhưng cần phân biệt:

```text
impl Trait
```

và:

```text
dyn Trait
```

### `impl Trait`

Concrete hidden type.

```text
static dispatch
```

### `dyn Trait`

Erased runtime type.

```text
dynamic dispatch
```

---

# 36. Associated types

Trait:

```axiom
trait Iterator {
    type Item;
    fn next(self: mut_view<Self>) -> Option<Self.Item>;
}
```

Implementation:

```axiom
impl Iterator for Numbers {
    type Item = i32;
}
```

Compiler giải quyết:

```text
Numbers::Item = i32
```

tại compile time.

---

# 37. Associated types thay vì generic parameter ở nhiều nơi

Ví dụ:

```text
Iterator<Item = T>
```

thường dễ quản lý hơn:

```text
Iterator<T>
```

khi mỗi type có một canonical output type.

Nhưng không nên lạm dụng associated types.

---

# 38. Generic constraints

Ví dụ:

```axiom
fn sort<T: Ord>(a: mut_view<T>)
```

Constraint chỉ cần thiết khi body dùng behavior đó.

Compiler không cần:

```text
T: Sized + Copy + Clone + ...
```

nếu không sử dụng.

Đây là:

> **Generic Constraint Minimality.**

---

# 39. Trait solver không phải theorem prover

Solver chỉ cần xử lý:

```text
T: Trait
T == U
associated type equality
supertrait
impl matching
```

Không cần chứng minh các proposition toán học tùy ý.

---

# 40. Solver result

Mỗi query chỉ có:

```text
PROVEN
DISPROVEN
AMBIGUOUS
OVERFLOW
```

Ví dụ:

```text
T: Add
```

→ PROVEN.

Nếu có hai impl cạnh tranh:

```text
→ AMBIGUOUS
```

Compiler báo lỗi.

Nếu recursion quá sâu:

```text
→ OVERFLOW
```

không chạy vô hạn.

---

# 41. Generic recursion phải có giới hạn

Ví dụ pathological trait definitions có thể khiến solver loop.

Axiom compiler phải có:

```text
max solver depth
max normalization steps
memoization
cycle detection
```

Đây là compiler implementation detail, không phải source-language burden.

---

# 42. Coherence

Không cho:

```text
impl ForeignTrait for ForeignType
```

nếu cả trait và type đều đến từ package khác.

Ví dụ package A sở hữu:

```text
TraitA
```

package B sở hữu:

```text
TypeB
```

package C không được:

```text
impl TraitA for TypeB
```

nếu không có ownership authority.

---

# 43. Tại sao?

Nếu cho phép tự do:

```text
package A
package B
package C
```

có thể mỗi package tạo impl khác nhau.

Khi link:

```text
which implementation?
```

Không deterministic.

---

# 44. Blanket impl

Cho phép:

```axiom
impl<T: Foo> Bar for T {
    ...
}
```

nhưng coherence solver phải đảm bảo không overlap với implementation khác.

---

# 45. Không có programmer specialization v0.1

Không:

```text
impl<T> Foo for T
impl Foo for i32 // special case
```

nếu chúng overlap.

Có thể compiler nội bộ specialize:

```text
generic implementation
↓
known T = i32
↓
optimized implementation
```

nhưng source không được tạo ambiguity.

---

# 46. Operator overload

Có thể map:

```text
a + b
```

thành:

```text
Add::add(a, b)
```

về mặt semantic.

Nhưng compiler intrinsic cho primitive:

```text
i64 + i64
```

→ trực tiếp machine ADD.

Không cần dynamic dispatch.

---

# 47. Đây cũng là lý do operator không phải built-in-only

Custom type:

```axiom
struct Vec2 {
    x: f32
    y: f32
}
```

có thể:

```axiom
impl Add for Vec2 {
    fn add(a: Vec2, b: Vec2) -> Vec2 {
        Vec2 {
            x: a.x + b.x,
            y: a.y + b.y
        }
    }
}
```

Compiler inline hoàn toàn.

---

# 48. Không implicit conversion qua trait

Đây là invariant tôi muốn khóa:

> **Trait không tự tạo implicit conversion.**

Nếu:

```text
Meters
Feet
```

có:

```text
Convert<Feet>
```

thì:

```axiom
meters + feet
```

không tự động convert.

Phải:

```axiom
meters + feet.to_meters()
```

hoặc explicit conversion syntax.

---

# 49. Vì sao?

Nếu implicit conversion qua trait:

```text
a + b
```

có thể kích hoạt hàng chục candidate conversions.

Compiler trở nên:

```text
ambiguous
slow
hard to reason
```

và programmer không biết conversion nào xảy ra.

Axiom tránh điều đó.

---

# 50. Type inference cũng không chạy xuyên implicit conversions

Ví dụ:

```axiom
fn foo<T>(x: T) {}
foo(10);
```

→ `T = i32`.

Không tìm:

```text
i8
i16
i32
i64
u8
...
```

rồi conversion vòng quanh.

---

# 51. Generic inference ưu tiên exact match

Resolution:

```text
exact type
↓
literal contextual typing
↓
explicit conversion
```

Không có:

```text
implicit conversion search
```

---

# 52. Recursive types

Struct:

```axiom
struct Node {
    next: Node
}
```

không hợp lệ vì size vô hạn.

Nhưng:

```axiom
struct Node {
    next: Option<Box<Node>>
}
```

hợp lệ.

Compiler chỉ cần thấy:

```text
Node
 ↓
Box<Node>
```

là indirection break.

---

# 53. Recursive enum

Tương tự:

```axiom
enum Tree {
    Leaf(i32),
    Node(Box<Tree>, Box<Tree>)
}
```

hợp lệ.

ADT recursive vẫn zero-cost abstraction ngoài allocation semantics của Box.

---

# 54. `Option<T>` không cần null

Ví dụ:

```axiom
Option<Box<Node>>
```

compiler có thể niche-optimize:

```text
None = null pointer
Some = non-null pointer
```

nhưng đây là **representation optimization**.

Semantically:

```text
None != null pointer
```

và programmer không nhìn thấy null.

---

# 55. `Option<&T>` không tồn tại trong source model

Ta dùng:

```text
view<T>
```

thay vì reference type phổ biến.

Nếu cần optional view:

```text
Option<view<T>>
```

nhưng verifier phải đảm bảo capability lifetime.

---

# 56. Type identity

Type identity nên dựa trên:

```text
module identity
+
declaration identity
+
generic arguments
```

Không dựa trên machine representation.

Do đó:

```text
UserId
ProductId
```

có thể cùng là `u64` machine representation nhưng vẫn khác semantic type.

---

# 57. Generic type identity

```text
Vec<i32>
Vec<u32>
```

là khác type.

```text
Foo<A,B>
```

không bị coi giống:

```text
Foo<B,A>
```

trừ khi declaration semantics nói vậy.

---

# 58. Type aliases không tạo identity mới

```axiom
type Count = u64;
```

`Count == u64`.

Newtype:

```axiom
struct Count(u64);
```

`Count != u64`.

---

# 59. `const` generic

Tôi nghĩ Axiom nên có **generic compile-time values**, nhưng giới hạn.

Ví dụ:

```axiom
struct Array<T, const N: usize> {
    ...
}
```

cho phép:

```text
Array<i32, 4>
Array<i32, 16>
```

Đây cực kỳ hữu ích cho:

- SIMD;
- matrix;
- fixed arrays;
- buffers;
- embedded;
- GPU.

---

# 60. Nhưng không làm dependent type system

Không cho kiểu:

```text
Array<T, N + M * factorial(K)>
```

với một theorem engine.

Const generic expressions nên bắt đầu ở mức:

```text
integer constants
basic constant expressions
```

Ví dụ:

```text
N + 1
N * 4
```

nếu compiler evaluate được.

---

# 61. Type-level computation

Chỉ cho:

```text
compile-time constant evaluation
```

không phải general proof system.

Nguyên tắc:

> **Comptime có thể mạnh; type checker không phải theorem prover.**

---

# 62. Tổng quan type system

```text
                         Axiom Type
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
       Value Types        Callable           Traits
          │                  │                  │
   ┌──────┼──────┐       fn / closure      constraints
   │      │      │                          impl
 primitive struct enum                       │
   │      │      │                       generics
   └──────┼──────┘
          │
      Tuple/Array
          │
      Option/Result

Special semantic types:
    unit
    never
    view<T>
    mut_view<T>
    dyn Trait
```

---

# 63. Những thứ Axiom **không có**

Đây là phần quan trọng không kém:

```text
❌ class hierarchy
❌ Object
❌ Any
❌ null trong safe core
❌ implicit numeric conversion
❌ implicit user conversion
❌ implicit trait conversion
❌ unrestricted transmute
❌ unrestricted subtype system
❌ programmer lifetime annotations
❌ programmer borrow annotations
❌ theorem-prover type system
❌ unrestricted specialization
❌ runtime generic metadata mặc định
```

Điều này giúp compiler kernel nhỏ hơn đáng kể về mặt semantic complexity.

---

# 64. Nhưng compiler vẫn rất mạnh

Source:

```axiom
fn sum<T: Add + Zero>(a: view<T>) -> T {
    var result = T.zero();

    for x in a {
        result = result + x;
    }

    result
}
```

Compiler có thể:

```text
parse
 ↓
resolve
 ↓
infer T
 ↓
solve Add + Zero
 ↓
specialize T
 ↓
ownership/alias analysis
 ↓
bounds proof
 ↓
inline
 ↓
vectorize
 ↓
register allocation
 ↓
native machine code
```

Programmer không phải viết thêm:

```text
lifetime
borrow
noalias
inline
register
```

trừ khi thực sự muốn điều khiển implementation.

---

# 65. Tôi đề xuất khóa Type System v0.1 ở mức này

Các invariant chính:

```text
ATS-01  Static Typing
ATS-02  No General Subtyping
ATS-03  Struct Is Data
ATS-04  Trait Is Behavior
ATS-05  Explicit Dynamic Dispatch
ATS-06  Deterministic Type Inference
ATS-07  Bidirectional Inference
ATS-08  No Implicit User Conversion
ATS-09  No Implicit Numeric Conversion
ATS-10  Literal Contextual Typing
ATS-11  Explicit Narrowing
ATS-12  Explicit Representation Conversion
ATS-13  Newtype Type Identity
ATS-14  Alias Preserves Type Identity
ATS-15  Bounded Trait Solver
ATS-16  Coherence
ATS-17  No Source-Level Specialization
ATS-18  Generic Compile-Time Orientation
ATS-19  Generic Constraint Minimality
ATS-20  Associated Type Determinism
ATS-21  Function/Closure Distinction
ATS-22  View Is Not Owner
ATS-23  MutView Is Exclusive Capability
ATS-24  Recursive Types Require Finite Representation
ATS-25  Const Generics Are Bounded
ATS-26  No General Dependent Types
ATS-27  No Theorem-Prover Type Checking
ATS-28  Type Identity Independent Of Representation
ATS-29  Abstraction Erasure
ATS-30  Compiler Complexity Is Not Language Complexity
```

---

## Một quyết định quan trọng tiếp theo

Bây giờ Axiom đã có:

```text
Memory
Ownership
View
Type
Trait
Generic
Concurrency
Async
Effect
Execution
Optimization
ABI
```

Mảnh còn thiếu rất lớn là **Object/Runtime representation và data model thực tế**.

Tôi đề xuất tiếp theo đi vào:

### **Axiom Data Model & Collections v0.1**

Không chỉ `Vec/String/Map`, mà phải quyết định rất kỹ:

```text
Array
Vec
Slice/View
String/Text
Bytes
Option
Result
Tuple
Struct
Enum
Union
Bitset
SIMD Vector
Matrix
Map
Set
Deque
Iterator
Range
```

và đặc biệt câu hỏi quan trọng đối với mục tiêu của bạn:

> **Axiom có nên có một “universal container/object” nào đó không, hay hoàn toàn không cần?**

Tôi nghiêng khá mạnh về **không có universal object/container trong Core**, vì nó sẽ phá một phần mục tiêu **native + nhỏ + predictable + zero-cost**, nhưng phần này đáng phân tích trước khi khóa.