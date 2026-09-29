Tiếp tục.

# BOOTSTRAP-051 — Surface Syntax & Language Ergonomics Audit & Freeze

Sau 050, phần semantic của Axiom đã khá rõ. Bây giờ cần làm một việc rất quan trọng: **không để semantic mạnh biến thành syntax phức tạp**.

Nguyên tắc:

> **Một semantic concept chỉ nên có một cách biểu đạt chính trong source code.**

Và:

> **Syntax phải phản ánh cách programmer tư duy, không phản ánh cách compiler thực hiện.**

---

# 1. Syntax philosophy

Axiom nên có cảm giác:

```text
C/C++        → familiar
Rust         → safety concepts
Swift/Kotlin → readable
Go           → simple syntax
Zig          → explicit systems control
```

nhưng **không copy nguyên xi bất kỳ ngôn ngữ nào**.

Mục tiêu là:

```text
high-level readability
        +
systems-level control
        +
minimal ceremony
```

---

# 2. Một declaration cơ bản

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Đây là syntax canonical.

Không cần:

```text
func
function
return_type trước tên
```

---

# 3. Return expression

```axiom
fn square(x: i32) -> i32 {
    x * x
}
```

Không bắt buộc:

```axiom
return x * x
```

Nhưng `return` vẫn tồn tại cho early return:

```axiom
fn f(x: i32) -> i32 {
    if x < 0 {
        return 0
    }

    x
}
```

---

# 4. Semicolon

Đề xuất:

> **Semicolon không bắt buộc ở cuối statement.**

Ví dụ:

```axiom
let x = 10
let y = 20

x + y
```

Có thể cho phép `;` trong trường hợp nhiều expression trên một dòng, nhưng không khuyến khích.

---

# 5. Block

Block:

```axiom
{
    ...
}
```

là expression.

```axiom
let x = {
    let a = 10
    a * 2
}
```

---

# 6. `let` và `var`

Giữ quyết định:

```axiom
let x = 10
var y = 20

y = 30
```

Ý nghĩa:

- `let`: binding immutable;
- `var`: binding mutable.

Không dùng:

```text
const
mut
```

cho local mutability.

---

# 7. `const`

`const` dành cho compile-time value:

```axiom
const MAX_SIZE: usize = 1024
```

Do đó:

```text
let = immutable runtime binding
const = compile-time value
comptime = compile-time execution
```

Rất rõ.

---

# 8. `comptime`

```axiom
comptime {
    ...
}
```

hoặc:

```axiom
comptime fn factorial(n: usize) -> usize {
    if n <= 1 { 1 }
    else { n * factorial(n - 1) }
}
```

---

# 9. Type syntax

Canonical:

```axiom
let x: i32
let y: Vec<f32>
let z: Option<String>
```

Generic:

```axiom
Map<String, User>
```

---

# 10. Function type

```axiom
fn(i32, i32) -> i32
```

Ví dụ:

```axiom
let f: fn(i32) -> i32 = square
```

---

# 11. Closure

```axiom
let f = |x| x * 2
```

Multiple arguments:

```axiom
let add = |a, b| a + b
```

Block:

```axiom
let f = |x| {
    let y = x * 2
    y + 1
}
```

---

# 12. Explicit move capture

Chỉ khi cần:

```axiom
let f = move |x| {
    use(data, x)
}
```

Không bắt programmer khai báo capture mode thông thường.

Compiler tự suy luận.

---

# 13. Struct

Canonical:

```axiom
struct User {
    id: u64
    name: String
}
```

Khởi tạo:

```axiom
let user = User {
    id: 42
    name: "Alice"
}
```

---

# 14. Field shorthand

Có thể:

```axiom
let id = 42
let name = "Alice"

let user = User { id, name }
```

---

# 15. Tuple

```axiom
let p = (10, 20)
```

Truy cập:

```axiom
p.0
p.1
```

---

# 16. Enum

```axiom
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

Option:

```axiom
enum Option<T> {
    Some(T)
    None
}
```

---

# 17. Enum variant namespace

Canonical:

```axiom
Option::Some(10)
Option::None
```

Compiler có thể cho phép contextual shorthand:

```axiom
Some(10)
None
```

khi không ambiguous.

---

# 18. Match

```axiom
match value {
    Some(x) => x
    None => 0
}
```

Không cần `case`.

---

# 19. Multiple patterns

```axiom
match x {
    0 | 1 => ...
    2..=10 => ...
    _ => ...
}
```

---

# 20. `if`

```axiom
if x > 10 {
    ...
} else {
    ...
}
```

Không implicit truthiness.

Sai:

```axiom
if x {
}
```

nếu `x` không phải `bool`.

---

# 21. `if` expression

```axiom
let max = if a > b { a } else { b }
```

---

# 22. `if let`

```axiom
if let Some(x) = value {
    ...
}
```

---

# 23. Loop

```axiom
loop {
    ...
}
```

---

# 24. While

```axiom
while condition {
    ...
}
```

---

# 25. For

```axiom
for x in values {
    ...
}
```

Range:

```axiom
for i in 0..<n {
    ...
}
```

Inclusive:

```axiom
for i in 0..=n {
    ...
}
```

---

# 26. Break value

```axiom
let result = loop {
    if ready {
        break value
    }
}
```

---

# 27. Labels

Chỉ cần khi nested control flow:

```axiom
'outer: loop {
    loop {
        break 'outer
    }
}
```

Không cần goto trong safe Core.

---

# 28. Struct methods

Theo quyết định trước:

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: view<Vec2>) -> f32 {
    sqrt(self.x * self.x + self.y * self.y)
}
```

Call:

```axiom
v.length()
```

---

# 29. Mutable method

```axiom
fn normalize(self: mut_view<Vec2>) {
    ...
}
```

Call:

```axiom
v.normalize()
```

---

# 30. Consuming method

```axiom
fn into_string(self: Vec2) -> String {
    ...
}
```

Call:

```axiom
let s = v.into_string()
```

`v` sau đó không còn usable.

---

# 31. Không có `self` magic riêng

Về semantic:

```text
self
```

chỉ là receiver parameter có syntax đặc biệt.

Compiler HIR vẫn biểu diễn:

```text
receiver: parameter 0
```

---

# 32. Trait

```axiom
trait Drawable {
    fn draw(self: view<Self>)
}
```

Implementation:

```axiom
impl Drawable for Circle {
    fn draw(self: view<Circle>) {
        ...
    }
}
```

---

# 33. Default method

```axiom
trait Printable {
    fn print(self: view<Self>) {
        ...
    }
}
```

Override:

```axiom
impl Printable for User {
    fn print(self: view<User>) {
        ...
    }
}
```

Không cần:

```text
override
virtual
final
```

---

# 34. Explicit trait call

Khi ambiguity:

```axiom
Drawable::draw(x)
```

hoặc:

```axiom
Printable::print(x)
```

---

# 35. Generic

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

Multiple constraints:

```axiom
fn f<T: Clone + Debug>(x: T) {
    ...
}
```

---

# 36. Where clause?

Không nên đưa `where` vào v1 nếu không thực sự cần.

Thay:

```text
fn f<T>(...) where T: A + B
```

bằng:

```axiom
fn f<T: A + B>(...)
```

Canonical syntax đơn giản hơn.

Nếu sau này constraint quá dài, có thể bổ sung `where`.

**Chưa freeze `where` cho v1.**

---

# 37. Associated type

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self::Item>
}
```

---

# 38. Associated constant

```axiom
trait Numeric {
    const ZERO: Self
}
```

---

# 39. `Self`

Trong trait:

```text
Self
```

là type đang implement trait.

Không dùng `self` làm type.

---

# 40. Type alias

```axiom
type UserId = u64
```

Không tạo type mới.

---

# 41. Newtype

```axiom
struct UserId(u64)
```

tạo nominal type mới.

Đây là cách canonical.

---

# 42. Tuple struct

```axiom
struct Vec2(f32, f32)
```

được phép.

---

# 43. Newtype + transparent ABI

```axiom
@repr(transparent)
struct UserId(u64)
```

dùng khi ABI contract cần representation tương ứng.

---

# 44. View syntax

Đây là một phần rất quan trọng.

Canonical:

```axiom
view<T>
mut_view<T>
```

Ví dụ:

```axiom
fn print(data: view<String>)
fn sort(data: mut_view<[i32]>)
```

---

# 45. Slice syntax

Nên có sugar:

```axiom
view<T>
```

cho single object và:

```axiom
view<[T]>
```

cho contiguous sequence.

Ví dụ:

```axiom
fn sum(x: view<[i32]>) -> i32
```

Đề xuất **không tạo một kiểu `Slice<T>` Core riêng**.

`view<[T]>` là capability trên sequence.

---

# 46. Mutable slice

```axiom
fn fill(x: mut_view<[u8]>, value: u8)
```

---

# 47. Owner → view

Call:

```axiom
print(name)
```

nếu parameter là:

```axiom
view<String>
```

được phép implicit ephemeral conversion.

---

# 48. Binding view

Không implicit:

```axiom
let v = name
```

nếu mục tiêu là lưu view.

Phải explicit:

```axiom
let v = view(name)
```

hoặc:

```axiom
let v = mut_view(buffer)
```

---

# 49. Tại sao?

Để nhìn source là biết:

```text
own value
```

hay:

```text
non-owning capability
```

mà không cần hiểu compiler inference.

---

# 50. Không có `&T` và `&mut T`

Axiom Core v1 **không dùng**:

```text
&T
&mut T
```

cho safe access.

Canonical là:

```text
view<T>
mut_view<T>
```

---

# 51. Raw pointer

Unsafe/system:

```axiom
*const T
*mut T
```

Deref:

```axiom
*p
```

Field:

```axiom
p->field
```

---

# 52. Address-of

Không dùng `&x` để tránh collision với view semantics.

System-level:

```axiom
unsafe {
    let p = address_of(x)
}
```

---

# 53. Cast

Nên có một syntax thống nhất:

```axiom
x as u64
```

Nhưng semantic cast phải phân biệt:

```text
numeric conversion
pointer conversion
representation cast
```

---

# 54. Bitcast

Không nên dùng:

```text
as
```

cho bit reinterpretation.

Đề xuất:

```axiom
bitcast<T>(x)
```

hoặc compiler intrinsic.

Ví dụ:

```axiom
let bits = bitcast<u32>(float)
```

---

# 55. Numeric narrowing

Không implicit:

```axiom
let x: u8 = some_u32
```

Phải:

```axiom
let x = some_u32 as u8
```

và semantics của conversion phải rõ.

---

# 56. Arithmetic

```axiom
a + b
a - b
a * b
a / b
a % b
```

---

# 57. Comparison

```axiom
a == b
a != b
a < b
a <= b
a > b
a >= b
```

---

# 58. Logical

```axiom
a && b
a || b
!a
```

Chỉ `bool`.

Short-circuit semantics cố định.

---

# 59. Bit operations

```axiom
a & b
a | b
a ^ b
a << b
a >> b
```

Không overloading mơ hồ ngoài trait semantics.

---

# 60. Assignment

```axiom
x = value
```

Compound:

```axiom
x += value
x -= value
x *= value
```

---

# 61. Indexing

```axiom
a[i]
```

Compiler/library protocol:

```text
Index
IndexMut
```

---

# 62. Optional chaining?

Không nên thêm hàng loạt syntax như:

```text
?.
??=
```

Core có thể dùng:

```axiom
match
if let
Option methods
```

Nhưng `?` đã có cho Result/Option propagation.

---

# 63. `?`

Canonical:

```axiom
let user = load_user(id)?
```

Nó propagate:

```text
Result
Option
```

theo protocol/compiler semantics đã freeze.

---

# 64. Không `try/catch`

Core không có:

```text
try
catch
throw
finally
```

---

# 65. Panic

```axiom
panic("invalid state")
```

là library/compiler intrinsic boundary.

Không phải exception.

---

# 66. Unsafe

Block:

```axiom
unsafe {
    ...
}
```

Function:

```axiom
unsafe fn read_register(...) -> u32 {
    ...
}
```

---

# 67. Unsafe syntax không lan truyền vô hạn

Gọi unsafe function từ safe function:

```axiom
unsafe {
    read_register(...)
}
```

để boundary rõ ràng.

---

# 68. Attributes

Canonical:

```axiom
@repr(C)
struct Header {
    ...
}
```

```axiom
@export("foo")
fn foo() { ... }
```

```axiom
@kernel
fn add(...) { ... }
```

---

# 69. Không biến attributes thành second language

Không:

```text
@something(complex programming language here)
```

Attribute arguments phải là typed/configuration values.

---

# 70. Modules

```axiom
module graphics
```

Import:

```axiom
import axiom.text::String
import app.graphics::Renderer
```

---

# 71. Namespace qualification

```axiom
app::graphics::Renderer
```

Member:

```axiom
renderer.draw()
```

Phân biệt:

```text
::
namespace/type qualification
.
member/method
```

---

# 72. Visibility

```axiom
pub struct User
```

```axiom
pub fn create_user(...)
```

Không có quá nhiều modifier trong Core v1.

---

# 73. Export

```axiom
@export("create_user")
pub fn create_user(...)
```

`pub` và `@export` khác nhau.

---

# 74. Static

Không cần keyword `static` cho mọi thứ.

Ví dụ compile-time:

```axiom
const X = 10
```

Runtime global:

```axiom
static COUNTER: Atomic<u64> = ...
```

chỉ khi thực sự cần storage identity program-lifetime.

---

# 75. Initialization

Không có arbitrary global constructor magic.

Nếu:

```axiom
static X = expensive()
```

thì phải có semantic rule rõ ràng; tốt nhất v1 giới hạn static initializer thành compile-time evaluable hoặc explicit runtime initialization.

Đề xuất:

> **Không có implicit arbitrary global runtime initialization trong Core v1.**

---

# 76. `init`

Nếu application cần initialization:

```axiom
fn main() {
    let app = App.init()?
    ...
}
```

explicit.

---

# 77. Destruction

Không có:

```text
destructor
finalize
```

syntax.

Dùng `Drop`.

---

# 78. Async

```axiom
async fn fetch() -> Result<Data, Error> {
    ...
}
```

Await:

```axiom
let data = fetch().await?
```

---

# 79. Spawn

Không phải keyword.

```axiom
async::spawn(task)
```

library/runtime API.

---

# 80. GPU

```axiom
@kernel
fn add(
    a: view<[f32]>,
    b: view<[f32]>,
    out: mut_view<[f32]>
) {
    ...
}
```

Không tạo ngôn ngữ GPU riêng.

---

# 81. Comptime vs macro

Không có macro syntax trong Core v1.

Không:

```text
macro_rules
proc_macro
```

Comptime + typed generation + `@derive` là đủ cho v1.

---

# 82. Comments

Đề xuất:

```axiom
// comment
```

và:

```axiom
/*
   block comment
*/
```

Documentation:

```axiom
/// Documentation
```

---

# 83. String literals

UTF-8:

```axiom
let s = "Xin chào"
```

Byte string:

```axiom
let b = b"raw bytes"
```

---

# 84. Raw string

```axiom
let path = r"C:\Users\..."
```

Raw multiline có thể bổ sung nhưng không cần làm phức tạp v1.

---

# 85. Character

Không nên gọi `char` nếu semantic là Unicode scalar value gây nhầm với byte.

Đề xuất:

```text
char
```

= Unicode scalar value.

Byte:

```text
u8
```

---

# 86. String interpolation

Đây là một feature đáng có vì ergonomics.

Đề xuất:

```axiom
let s = "Hello {name}"
```

Compiler lower xuống formatting protocol.

Không tạo runtime magic.

---

# 87. Format specification

Có thể:

```axiom
"{value:.2f}"
```

nhưng formatter implementation thuộc library.

---

# 88. No implicit null

Không có:

```text
null
nil
nullptr
```

Safe absence:

```axiom
Option<T>
```

---

# 89. Boolean conversion

Không:

```axiom
if 1
if pointer
if string
```

Chỉ:

```axiom
if condition: bool
```

---

# 90. Ownership visibility

Axiom không nên bắt programmer viết:

```text
borrow
borrow_mut
lifetime
'a
```

trong normal safe code.

---

# 91. Move syntax

Move mặc định:

```axiom
let b = a
```

nếu `a` là non-Copy owning value.

Không cần:

```text
move(a)
```

trừ khi cần force semantics trong một context đặc biệt.

---

# 92. Clone

Explicit:

```axiom
let b = a.clone()
```

Đây là tín hiệu rõ ràng về potentially expensive duplication.

---

# 93. Copy

Nếu type `Copy`:

```axiom
let b = a
```

tạo value độc lập.

Không cần `.copy()`.

---

# 94. Drop explicit

```axiom
drop(resource)
```

nếu muốn release sớm.

Không dùng:

```text
delete
free
```

cho ordinary ownership.

---

# 95. Collection mutation

```axiom
var xs = Vec.new()
xs.push(10)
```

Method resolution chuyển thành mutable receiver.

Không cần:

```text
&mut xs
```

---

# 96. Iteration

```axiom
for x in xs {
    ...
}
```

Compiler/library xử lý ownership.

Không cần `iter()` cho mọi trường hợp.

Nếu muốn view:

```axiom
for x in xs.view() {
    ...
}
```

---

# 97. Explicit view API

Đây là một API hữu ích:

```axiom
xs.view()
xs.mut_view()
```

nhưng semantic type vẫn là:

```text
view<[T]>
mut_view<[T]>
```

---

# 98. Pattern ownership

Ví dụ:

```axiom
match user {
    User { id, name } => ...
}
```

ownership follows pattern semantics.

Không có implicit clone chỉ để pattern matching.

---

# 99. Exhaustiveness

Compiler phải báo:

```text
non-exhaustive match
```

và:

```text
unreachable pattern
```

---

# 100. Surface syntax freeze principle

Đến đây, tôi đề xuất freeze một rule lớn:

> **Axiom v1 không thêm syntax mới chỉ để cung cấp một optimization hoặc implementation technique.**

Ví dụ không tạo:

```text
@stack
@heap
@noalloc
@restrict
@pure
@borrow
@lifetime
```

chỉ vì compiler có các khái niệm tương ứng.

---

# BOOTSTRAP-051 — Frozen Syntax Invariants

```text
ASYNTAX-20   Functions use `fn name(args) -> Return`.
ASYNTAX-21   Blocks are expressions.
ASYNTAX-22   Final block expression may provide its value.
ASYNTAX-23   `return` remains available for explicit early return.
ASYNTAX-24   Statement semicolons are not required at line/block boundaries.
ASYNTAX-25   `let` creates immutable bindings.
ASYNTAX-26   `var` creates mutable bindings.
ASYNTAX-27   `const` denotes compile-time values.
ASYNTAX-28   `comptime` denotes compile-time execution.
ASYNTAX-29   Type annotations use `name: Type`.
ASYNTAX-30   Generic arguments use `Type<Args>`.
ASYNTAX-31   Function types use `fn(Args) -> Return`.
ASYNTAX-32   Closures use `|args| expression`.
ASYNTAX-33   `move` closure capture is explicit only when required.
ASYNTAX-34   Structs are the primary aggregate declaration.
ASYNTAX-35   Struct literals use `Type { fields }`.
ASYNTAX-36   Tuple values use `(a, b, ...)`.
ASYNTAX-37   Enums represent algebraic variants.
ASYNTAX-38   Qualified enum variants use `Type::Variant`.
ASYNTAX-39   Contextual variant shorthand may be used when unambiguous.
ASYNTAX-40   `match` is exhaustive.
ASYNTAX-41   `if` conditions require bool.
ASYNTAX-42   `if` is an expression.
ASYNTAX-43   `if let` is supported.
ASYNTAX-44   `loop`, `while`, and `for` are Core control constructs.
ASYNTAX-45   Range iteration uses `..` and `..=`.
ASYNTAX-46   Loop expressions may return values through `break`.
ASYNTAX-47   Labeled control flow is explicit.
ASYNTAX-48   Methods are receiver syntax over functions.
ASYNTAX-49   Receiver is the first semantic parameter.
ASYNTAX-50   Receiver modes are owning, `view`, or `mut_view`.
ASYNTAX-51   Traits define behavior contracts.
ASYNTAX-52   Trait implementations provide override semantics.
ASYNTAX-53   No class inheritance syntax exists in Core v1.
ASYNTAX-54   Generic constraints use `T: Trait`.
ASYNTAX-55   Multiple simple constraints use `T: A + B`.
ASYNTAX-56   A `where` clause is not required by Core v1.
ASYNTAX-57   Associated types use `type`.
ASYNTAX-58   Associated constants use `const`.
ASYNTAX-59   `Self` denotes the implementing type in trait context.
ASYNTAX-60   Type aliases do not create nominal types.
ASYNTAX-61   Tuple/newtypes use struct syntax.
ASYNTAX-62   `@repr(transparent)` may establish representation contracts.
ASYNTAX-63   Safe views use `view<T>` and `mut_view<T>`.
ASYNTAX-64   Safe Core does not use general `&T`/`&mut T` reference syntax.
ASYNTAX-65   Raw pointers use `*const T` and `*mut T`.
ASYNTAX-66   Raw pointer operations are unsafe/system-level.
ASYNTAX-67   `address_of` is unsafe/system-level.
ASYNTAX-68   Numeric conversion uses `as`.
ASYNTAX-69   Bit reinterpretation is distinct from numeric conversion.
ASYNTAX-70   Indexing uses `x[i]`.
ASYNTAX-71   Boolean operators require boolean operands.
ASYNTAX-72   Boolean short-circuit semantics are deterministic.
ASYNTAX-73   `?` propagates Result/Option failure.
ASYNTAX-74   Core v1 has no exception/catch/throw syntax.
ASYNTAX-75   Panic is distinct from recoverable Result failure.
ASYNTAX-76   `unsafe {}` marks unsafe operation boundaries.
ASYNTAX-77   `unsafe fn` marks functions requiring unsafe caller obligations.
ASYNTAX-78   Attributes use `@name(...)`.
ASYNTAX-79   Attributes are typed compiler metadata, not a second programming language.
ASYNTAX-80   Modules use namespace qualification with `::`.
ASYNTAX-81   Member and method access uses `.`.
ASYNTAX-82   Visibility uses `pub`.
ASYNTAX-83   Native symbol export uses explicit `@export`.
ASYNTAX-84   Runtime globals use explicit static storage semantics.
ASYNTAX-85   Arbitrary implicit global runtime initialization is not Core v1.
ASYNTAX-86   Destruction is represented by Drop rather than destructor syntax.
ASYNTAX-87   Async functions use `async fn`.
ASYNTAX-88   Suspension uses `.await`.
ASYNTAX-89   Async scheduling is library/runtime functionality.
ASYNTAX-90   GPU kernels use `@kernel`.
ASYNTAX-91   GPU kernels remain Axiom functions.
ASYNTAX-92   Core v1 has no general macro language.
ASYNTAX-93   Typed generation and comptime provide compile-time metaprogramming.
ASYNTAX-94   Strings are UTF-8 text values.
ASYNTAX-95   Byte strings are distinct from text strings.
ASYNTAX-96   Character values represent Unicode scalar values.
ASYNTAX-97   Safe Core has no null value.
ASYNTAX-98   Optional absence uses `Option<T>`.
ASYNTAX-99   Ownership transfer is normally implicit through value semantics.
ASYNTAX-100  Explicit cloning uses `clone()`.
ASYNTAX-101  Explicit early destruction uses `drop(...)`.
ASYNTAX-102  Iteration integrates with ownership/capability semantics.
ASYNTAX-103  Pattern matching does not implicitly clone values.
ASYNTAX-104  Exhaustiveness is compiler-checked.
ASYNTAX-105  Syntax does not expose compiler implementation details unnecessarily.
ASYNTAX-106  Optimization mechanisms do not automatically create source syntax.
ASYNTAX-107  Lifetime/borrow annotations are not required in normal safe code.
ASYNTAX-108  Allocator selection is not mandatory syntax.
ASYNTAX-109  Heap placement is not mandatory syntax.
ASYNTAX-110  Purity is not mandatory source annotation.
ASYNTAX-111  Alias restriction is not mandatory source annotation.
ASYNTAX-112  Runtime metadata is not implied by syntax.
ASYNTAX-113  Dynamic dispatch requires explicit `dyn Trait`.
ASYNTAX-114  Static generic dispatch is the default.
ASYNTAX-115  Surface syntax must remain deterministic for humans and AI tooling.
ASYNTAX-116  One semantic concept should have one canonical source representation.
ASYNTAX-117  Syntax sugar must lower to existing semantic constructs.
ASYNTAX-118  Syntax sugar cannot bypass ownership verification.
ASYNTAX-119  Syntax sugar cannot bypass capability verification.
ASYNTAX-120  Syntax sugar cannot bypass concurrency verification.
```

---

## Một điểm tôi muốn giữ rất chặt

Sau 051, **không nên tiếp tục bổ sung feature theo kiểu “ngôn ngữ còn thiếu X”**.

Chúng ta đã có gần đủ các mảnh lớn. Giai đoạn tiếp theo nên chuyển sang **kiểm tra tính nhất quán toàn hệ thống**.

### BOOTSTRAP-052 — Axiom Semantic Consistency & Feature Interaction Audit

Đây sẽ là một audit đặc biệt, không thêm feature mới. Ta sẽ lấy các tổ hợp dễ gây lỗi nhất:

```text
Ownership × Drop
Ownership × async
Ownership × GPU
Ownership × FFI

view × Vec relocation
view × await
view × thread
view × GPU

Generic × Drop
Generic × Send/Share
Generic × dyn Trait
Generic × FFI

Comptime × ownership
Comptime × reflection
Comptime × generated code

Trait × method resolution
Trait × specialization
Trait × ABI

Panic × Drop
Panic × async
Panic × thread
Panic × FFI

Allocation × stable address
Allocation × capability
Allocation × arena
Allocation × GPU

Atomic × view
Atomic × volatile
Atomic × GPU

FFI × ownership
FFI × allocator
FFI × callbacks
FFI × async
```

Đây mới là bước có khả năng phát hiện **mâu thuẫn ẩn giữa các spec đã freeze**. Nếu 052 không tìm thấy contradiction nghiêm trọng, lúc đó chúng ta có thể chuyển sang thiết kế **compiler architecture thực thi được** thay vì tiếp tục mở rộng ngôn ngữ.