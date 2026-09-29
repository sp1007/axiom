Tiếp tục với **BOOTSTRAP-064 — Axiom Surface Syntax & Grammar Freeze**.

Đây là lúc chuyển từ semantic architecture sang thứ mà lập trình viên thực sự nhìn thấy. Tôi sẽ giữ một nguyên tắc rất rõ:

> **Axiom không được trở thành “Rust với tên khác”.**

Semantics bên dưới có thể mạnh và compiler có thể rất phức tạp, nhưng surface syntax phải làm cho những thứ như ownership, capability, generic, trait, async… **dễ đọc và dễ sinh code**, đặc biệt với AI.

---

# BOOTSTRAP-064 — Surface Syntax & Grammar

## 1. Mục tiêu syntax

Axiom cần đạt đồng thời:

```text
C-like familiarity
+
modern type system
+
AI-friendly
+
ít punctuation noise
+
không có lifetime syntax
+
không có borrow syntax
+
không có class ceremony
+
không có macro syntax phức tạp
```

Ví dụ mục tiêu:

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: view<Vec2>) -> f32 {
    sqrt(self.x * self.x + self.y * self.y)
}

fn main() {
    let v = Vec2{ x: 3, y: 4 }
    print(v.length())
}
```

Không cần:

```text
class
public:
private:
&
&&
'lifetime
override
virtual
```

---

# 2. Declaration philosophy

Axiom có một grammar declaration thống nhất:

```text
keyword name [generic parameters] [constraints] [body]
```

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

```axiom
struct User {
    id: u64
    name: String
}
```

```axiom
trait Drawable {
    fn draw(self: view<Self>)
}
```

---

# 3. Statement vs expression

Axiom nên tiếp tục hướng expression-oriented nhưng **không cực đoan**.

```axiom
let x = if condition {
    10
} else {
    20
}
```

`if`, `match`, `loop` có thể tạo value.

---

# 4. Block

Block:

```axiom
{
    statement
    expression
}
```

Expression cuối block là giá trị:

```axiom
{
    let x = 10
    x + 20
}
```

→ `30`.

Nếu không có expression cuối:

```axiom
unit
```

---

# 5. Semicolon

Tôi đề xuất **semicolon optional ở cuối statement**.

```axiom
let x = 10
let y = 20
print(x + y)
```

thay vì bắt buộc:

```axiom
let x = 10;
let y = 20;
print(x + y);
```

Nhưng semicolon vẫn được phép khi cần phân tách rõ ràng.

---

# 6. Newline không phải semantic separator tuyệt đối

Ví dụ:

```axiom
let x =
    very_long_function(
        a,
        b
    )
```

phải hợp lệ.

Parser dùng token/context để xác định statement boundary.

---

# 7. Braces

Braces vẫn giữ:

```text
{}
```

cho block/struct/enum.

Không dùng indentation-sensitive grammar.

Điều này tốt cho:

- compiler;
- formatter;
- AI;
- generated code.

---

# 8. Comments

Hai loại:

```axiom
// single line
```

và:

```axiom
/*
   multi-line
*/
```

---

# 9. Documentation comments

```axiom
/// Opens a file.
pub fn open(path: Str) -> Result<File, IoError>
```

Compiler có thể đưa documentation vào metadata.

---

# 10. Identifiers

Identifier:

```text
[a-zA-Z_][a-zA-Z0-9_]*
```

nhưng Axiom dùng UTF-8 source.

Unicode identifiers có thể hỗ trợ ở mức Unicode XID thay vì chỉ ASCII.

Tuy nhiên:

> ASCII identifiers vẫn được khuyến nghị cho public API/tooling interoperability.

---

# 11. Case convention

Compiler không enforce naming convention.

Tooling có thể đề xuất:

```text
TypeName
function_name
CONSTANT_NAME
```

nhưng đây không phải semantics.

---

# 12. Keywords

Bộ keyword Core nên nhỏ.

Đề xuất:

```text
as
async
await
break
comptime
const
continue
else
enum
extern
false
fn
for
if
impl
import
in
let
loop
match
mod
pub
return
struct
trait
true
type
unsafe
var
while
```

---

# 13. Không reserve quá nhiều keyword

Những thứ như:

```text
class
interface
virtual
override
public
private
protected
new
delete
throw
catch
finally
```

không cần trong Core.

---

# 14. `type`

`type` dùng cho alias:

```axiom
type UserId = u64
```

Đây là alias, không tạo nominal type mới.

---

# 15. Newtype

Để tạo distinct type:

```axiom
struct UserId(u64)
```

Đây là tuple struct / single-field struct có nominal identity.

Ví dụ:

```axiom
let a: UserId = UserId(10)
```

Không tự động coi là `u64`.

---

# 16. Struct

Syntax:

```axiom
struct Point {
    x: f32
    y: f32
}
```

Field visibility:

```axiom
pub struct Point {
    pub x: f32
    pub y: f32
}
```

---

# 17. Struct constructor

Không cần compiler-generated named constructor đặc biệt.

Literal:

```axiom
Point {
    x: 1
    y: 2
}
```

Tuple struct:

```axiom
UserId(10)
```

---

# 18. Field shorthand

Có thể:

```axiom
let x = 10
let y = 20

let p = Point { x, y }
```

---

# 19. Struct update

Có thể hỗ trợ:

```axiom
let p2 = Point {
    x: 20
    ..p
}
```

Ownership semantics phải được áp dụng bình thường.

---

# 20. No class

Không có:

```text
class Foo
```

Thay vào đó:

```axiom
struct Foo {
    ...
}

impl Foo {
    ...
}
```

---

# 21. Inherent implementation

```axiom
impl Vec2 {
    fn length(self: view<Self>) -> f32 {
        ...
    }
}
```

---

# 22. Method syntax

Compiler hiểu:

```axiom
v.length()
```

như:

```axiom
length(v)
```

với receiver semantics đã freeze.

---

# 23. Receiver syntax

Ba dạng chính:

```axiom
self: view<Self>
self: mut_view<Self>
self: Self
```

Ví dụ:

```axiom
fn length(self: view<Self>) -> f32
fn normalize(self: mut_view<Self>)
fn consume(self: Self)
```

---

# 24. Có nên có shorthand `self`?

Tôi đề xuất **có**.

```axiom
fn length(self) -> f32
```

có nghĩa mặc định:

```text
view<Self>
```

nếu function không mutate/consume.

Compiler có thể infer receiver capability.

Nhưng nếu muốn rõ:

```axiom
fn normalize(mut self)
fn consume(move self)
```

---

# 25. Ownership syntax tối thiểu

Đây là điểm cần rất cẩn thận.

Không viết:

```text
'a
&'a
&mut
```

Nhưng khi semantics cần explicit, có:

```axiom
view<T>
mut_view<T>
```

Đây là semantic type, không phải punctuation.

---

# 26. Function parameters

```axiom
fn process(
    input: view<Data>,
    output: mut_view<Data>
)
```

rất rõ ràng.

---

# 27. Ephemeral implicit view

Đã freeze:

Nếu parameter yêu cầu:

```axiom
view<T>
```

thì:

```axiom
fn print_name(name: view<String>) {}

fn main() {
    let s = String("hello")
    print_name(s)
}
```

được implicit owner → ephemeral view.

Không tạo escaping alias.

---

# 28. Explicit stored view

Nếu muốn giữ capability:

```axiom
let v = view(s)
```

và:

```axiom
let mv = mut_view(s)
```

---

# 29. Why explicit here?

Vì:

```axiom
let v = s
```

phải luôn rõ:

> đang copy/move value hay tạo alias?

Do đó implicit view chỉ cho **call argument**, không cho arbitrary binding.

---

# 30. `let` và `var`

Đã freeze:

```axiom
let x = 10
```

immutable binding.

```axiom
var x = 10
x = 20
```

mutable binding.

---

# 31. Không cần `mut`

Tôi khuyên không dùng Rust-style:

```text
let mut x
```

mà:

```text
var x
```

AI đọc dễ hơn và semantic rõ hơn.

---

# 32. Mutable field

Có hai lựa chọn.

Tôi đề xuất:

```axiom
var user = User { ... }
user.name = "Bob"
```

Binding mutation được kiểm soát bởi capability verifier.

Không cần:

```text
mutable struct
```

---

# 33. Constants

```axiom
const MAX_SIZE: usize = 1024
```

`const` là compile-time value theo BOOTSTRAP-037.

---

# 34. Comptime

```axiom
comptime {
    generate(...)
}
```

và:

```axiom
comptime fn factorial(n: usize) -> usize {
    if n == 0 { 1 }
    else { n * factorial(n - 1) }
}
```

---

# 35. Function syntax

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Return type optional nếu inference rõ:

```axiom
fn add(a: i32, b: i32) {
    a + b
}
```

Tôi nghiêng về **cho phép inference**.

---

# 36. Explicit return vẫn có

```axiom
fn find(...) -> Result<Item, Error> {
    if ... {
        return Err(...)
    }

    Ok(item)
}
```

---

# 37. Generic function

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

---

# 38. Generic declaration

```axiom
struct Vec<T> {
    ...
}
```

---

# 39. Multiple constraints

```axiom
fn foo<T: Clone + Send + Share>(x: T) {
    ...
}
```

---

# 40. Where clause

Để tránh signature quá dài:

```axiom
fn foo<T>(x: T)
where
    T: Clone + Send
{
    ...
}
```

Có thể hỗ trợ nhưng không nên lạm dụng.

---

# 41. Trait

```axiom
trait Display {
    fn display(self: view<Self>) -> String
}
```

---

# 42. Trait associated type

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self::Item>
}
```

---

# 43. Impl trait

```axiom
impl Display for User {
    fn display(self: view<Self>) -> String {
        ...
    }
}
```

---

# 44. Default method

```axiom
trait Printable {
    fn print(self: view<Self>) {
        ...
    }
}
```

Concrete type override:

```axiom
impl Printable for User {
    fn print(self: view<Self>) {
        ...
    }
}
```

Không cần `override`.

---

# 45. Dynamic dispatch

Explicit:

```axiom
dyn Drawable
```

Ví dụ:

```axiom
fn render(x: view<dyn Drawable>) {
    x.draw()
}
```

Không implicit boxing.

---

# 46. `dyn` không phải object hierarchy

`dyn Trait` chỉ là explicit dynamic trait abstraction.

Không có:

```text
Object
```

root type.

---

# 47. Enum

```axiom
enum Color {
    Red
    Green
    Blue
}
```

---

# 48. Enum payload

```axiom
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

---

# 49. Match

```axiom
match value {
    Color.Red => ...
    Color.Green => ...
    Color.Blue => ...
}
```

Tôi đề xuất **qualified variant syntax**:

```text
Color.Red
```

thay vì:

```text
Color::Red
```

vì dễ đọc hơn.

---

# 50. Generic type separator

Tôi đề xuất:

```text
Vec<i32>
```

và namespace:

```text
std.fs.File
```

Không cần `::` trong ordinary source.

`::` có thể dành cho compiler/internal paths nếu thật sự cần, nhưng tốt hơn là loại khỏi public syntax.

---

# 51. Why dot namespace?

```axiom
std.fs.File
```

rất dễ parse và AI-friendly.

Method:

```axiom
file.read()
```

namespace:

```axiom
std.fs.File
```

không gây nhầm nhiều nếu resolver biết declaration kind.

---

# 52. Import

```axiom
import std.fs
```

Specific:

```axiom
import std.fs.File
```

Alias:

```axiom
import std.fs as fs
```

---

# 53. Use alias

Nếu cần:

```axiom
import very.long.package.name as foo
```

sau đó:

```axiom
foo.Bar
```

---

# 54. Operators

Các toán tử cơ bản:

```text
+ - * / %
== !=
< <= > >=
&& ||
!
=
+= -= *= /= %=
```

---

# 55. Bitwise

```text
& | ^ ~
<< >>
```

---

# 56. No implicit truthiness

Chỉ `bool` dùng trong:

```axiom
if condition
```

Không:

```axiom
if x
```

nếu `x` là integer.

---

# 57. Cast

```axiom
let x = value as i64
```

Narrowing phải explicit.

---

# 58. Bitcast

Không dùng `as` cho reinterpretation.

Ví dụ:

```axiom
bitcast<f32>(bits)
```

hoặc syntax tương đương.

Semantics khác hoàn toàn cast.

---

# 59. Indexing

```axiom
a[i]
```

compiler lower tới indexing protocol.

Safe default có bounds checking.

---

# 60. Unchecked indexing

System/unsafe:

```axiom
unsafe {
    a.get_unchecked(i)
}
```

không nên tạo syntax đặc biệt cho mọi unsafe operation.

---

# 61. Range

```axiom
0..10
0..=10
```

---

# 62. Slicing

```axiom
let x = view(a[2..8])
```

hoặc API:

```axiom
let x = a.view(2..8)
```

Tôi nghiêng về syntax:

```axiom
a[2..8]
```

trả capability/view theo context.

---

# 63. Assignment

```axiom
x = value
```

chỉ hợp lệ với mutable binding/capability.

---

# 64. Function call

```axiom
foo(a, b)
```

Argument evaluation left-to-right.

---

# 65. Named arguments

Không cần trong Core v1.

Giữ syntax đơn giản:

```axiom
foo(a, b, c)
```

---

# 66. Optional arguments

Không có default arguments Core v1.

Library có thể dùng:

```axiom
Config
```

hoặc builder-like API nếu cần.

---

# 67. Closures

Syntax:

```axiom
let f = |x| x * 2
```

---

# 68. Typed closure

```axiom
let f = |x: i32| -> i32 {
    x * 2
}
```

---

# 69. Move closure

Đã đề xuất:

```axiom
let f = move |x| {
    use(x)
}
```

Ép capture ownership.

---

# 70. Closure environment

Không xuất hiện trong source.

Compiler-generated struct.

---

# 71. Async

```axiom
async fn fetch(url: Str) -> Result<Data, Error> {
    ...
}
```

---

# 72. Await

```axiom
let data = fetch(url).await?
```

---

# 73. Spawn

```axiom
let task = spawn(fetch(url))
```

`spawn` là library API.

`async/await` là language syntax.

---

# 74. Thread

```axiom
let handle = thread.spawn(|| {
    work()
})
```

Không biến `thread` thành keyword.

---

# 75. Unsafe

```axiom
unsafe {
    *ptr
}
```

hoặc:

```axiom
unsafe fn read(ptr: *const u8) -> u8 {
    *ptr
}
```

---

# 76. Raw pointer

```axiom
*const T
*mut T
```

---

# 77. Pointer dereference

```axiom
*p
```

unsafe.

---

# 78. Pointer field access

Có thể:

```axiom
p->field
```

là syntax sugar cho:

```axiom
(*p).field
```

nhưng vẫn unsafe.

---

# 79. Address-of

Không dùng `&x` trong safe language.

System:

```axiom
unsafe {
    address_of(x)
}
```

---

# 80. Attributes

```axiom
@inline
fn foo() {}
```

```axiom
@repr(C)
struct CPoint {
    x: f32
    y: f32
}
```

---

# 81. Attribute arguments

```axiom
@export("foo")
fn foo_impl() {}
```

---

# 82. Multiple attributes

```axiom
@inline
@cold(false)
fn foo() {}
```

Nhưng chỉ attribute registry hợp lệ mới được compiler nhận.

---

# 83. FFI

```axiom
extern "C" fn puts(s: *const u8) -> i32
```

hoặc block:

```axiom
extern "C" {
    fn puts(s: *const u8) -> i32
}
```

---

# 84. `extern` không tự tạo safe wrapper

Foreign function direct call vẫn chịu FFI rules.

---

# 85. System ABI

```axiom
extern "system" fn ...
```

target-specific.

---

# 86. Module declaration

```axiom
module graphics.render
```

---

# 87. Visibility

```axiom
pub fn render() {}
```

Private mặc định.

---

# 88. Constants and statics

```axiom
const VERSION: Str = "1.0"
```

Static storage nếu cần:

```axiom
@static
var counter: Atomic<u64>
```

Nhưng `@static` cần được thống nhất với storage attributes; không nên để syntax tự phát triển ngoài registry.

---

# 89. Pattern syntax

Patterns:

```axiom
Some(x)
None
Ok(value)
Err(error)
```

Struct:

```axiom
Point { x, y }
```

Tuple:

```axiom
(a, b)
```

---

# 90. Wildcard

```axiom
_
```

---

# 91. Range pattern

```axiom
0..10
```

---

# 92. Guards

```axiom
match x {
    n if n > 10 => ...
    _ => ...
}
```

---

# 93. If-let

```axiom
if let Some(x) = value {
    print(x)
}
```

---

# 94. While-let

```axiom
while let Some(x) = iter.next() {
    process(x)
}
```

---

# 95. Loop

```axiom
loop {
    ...
}
```

Value:

```axiom
let result = loop {
    if done {
        break value
    }
}
```

---

# 96. For

```axiom
for item in items {
    process(item)
}
```

---

# 97. Labels

```axiom
'outer: loop {
    loop {
        break 'outer
    }
}
```

Tôi vẫn giữ label syntax vì nó rất hữu ích trong nested control flow.

---

# 98. Error propagation

```axiom
let x = foo()?
```

`?` hoạt động với `Result`/`Option` theo semantics đã freeze.

---

# 99. Một ví dụ hoàn chỉnh

```axiom
import std.fs
import std.io

struct User {
    id: u64
    name: String
}

impl User {
    fn rename(self: mut_view<Self>, name: String) {
        self.name = name
    }
}

fn load_user(path: Str) -> Result<User, IoError> {
    let file = File.open(path)?
    let text = file.read_to_string()?

    Ok(parse_user(text)?)
}

fn main() {
    let mut_user = load_user("user.json")?

    mut_user.rename(String("Axiom"))
    println(mut_user.name)
}
```

Tuy nhiên, theo syntax đã chọn ở trên, **không dùng `let mut_user`** vì `var` là mutable:

```axiom
var user = load_user("user.json")?
user.rename(String("Axiom"))
```

Điều này tạo một phong cách nhất quán:

```text
let = immutable
var = mutable
```

---

# 100. Frozen invariants — BOOTSTRAP-064

```text
ASYNTAX-20   Axiom surface syntax is distinct from semantic implementation.
ASYNTAX-21   Syntax must not expose compiler-internal ownership analysis.
ASYNTAX-22   Programmer-written lifetime annotations are not part of Core syntax.
ASYNTAX-23   Borrow-checker annotations are not part of Core syntax.
ASYNTAX-24   General T& and T&& references are not Core syntax.
ASYNTAX-25   view<T> is explicit capability syntax.
ASYNTAX-26   mut_view<T> is explicit mutable capability syntax.
ASYNTAX-27   Implicit owner-to-view conversion is restricted to permitted ephemeral call contexts.
ASYNTAX-28   Stored capabilities require explicit view construction.
ASYNTAX-29   let creates an immutable binding.
ASYNTAX-30   var creates a mutable binding.
ASYNTAX-31   Mutation requires appropriate verified capability.
ASYNTAX-32   Struct is the primary aggregate declaration.
ASYNTAX-33   Class is not a Core declaration.
ASYNTAX-34   Class inheritance is not Core syntax.
ASYNTAX-35   impl defines inherent or trait behavior.
ASYNTAX-36   Methods are syntax over functions.
ASYNTAX-37   Receiver semantics are explicit or compiler-inferable within defined rules.
ASYNTAX-38   Trait is the primary behavior/interface abstraction.
ASYNTAX-39   Trait inheritance is not class inheritance.
ASYNTAX-40   Default trait methods may be overridden without mandatory override syntax.
ASYNTAX-41   dyn explicitly requests dynamic trait abstraction.
ASYNTAX-42   Dynamic dispatch is not implicit.
ASYNTAX-43   Generic parameters use angle-bracket syntax.
ASYNTAX-44   Generic constraints may use + composition.
ASYNTAX-45   where clauses may express extended generic constraints.
ASYNTAX-46   Generic abstraction does not imply runtime generic metadata.
ASYNTAX-47   type aliases preserve underlying type identity.
ASYNTAX-48   Tuple/single-field structs can provide nominal newtypes.
ASYNTAX-49   Enum is the primary algebraic sum-type declaration.
ASYNTAX-50   Match is exhaustive for algebraic patterns.
ASYNTAX-51   Pattern matching does not implicitly clone values.
ASYNTAX-52   Pattern ownership follows normal ownership semantics.
ASYNTAX-53   if and match may be expressions.
ASYNTAX-54   Blocks evaluate to their final expression.
ASYNTAX-55   Statements may omit trailing semicolons.
ASYNTAX-56   Semicolons remain available where explicit separation is required.
ASYNTAX-57   Newline alone does not alter expression semantics where continuation is syntactically valid.
ASYNTAX-58   Axiom syntax is not indentation-sensitive.
ASYNTAX-59   Boolean conditions require bool semantics.
ASYNTAX-60   Integer and pointer truthiness is not implicit.
ASYNTAX-61   Numeric narrowing requires explicit conversion.
ASYNTAX-62   Cast and bitcast are semantically distinct.
ASYNTAX-63   Indexing follows collection/index semantics.
ASYNTAX-64   Safe indexing retains bounds-safety semantics.
ASYNTAX-65   Unchecked indexing requires an explicit unsafe/system abstraction.
ASYNTAX-66   Range syntax represents range values/patterns.
ASYNTAX-67   Closures use explicit closure syntax and inferred capture semantics.
ASYNTAX-68   move closures explicitly request ownership capture.
ASYNTAX-69   Closure environment representation is compiler-generated.
ASYNTAX-70   Noncapturing closures may decay to compatible function values.
ASYNTAX-71   async fn is explicit.
ASYNTAX-72   await is explicit.
ASYNTAX-73   async does not imply thread creation.
ASYNTAX-74   spawn is a library/runtime abstraction.
ASYNTAX-75   Thread creation is not a language keyword requirement.
ASYNTAX-76   unsafe blocks explicitly mark unsafe operations.
ASYNTAX-77   unsafe fn explicitly declares an unsafe callable boundary.
ASYNTAX-78   Raw pointer syntax is restricted to unsafe/system contexts.
ASYNTAX-79   Raw pointer dereference is unsafe.
ASYNTAX-80   Pointer arithmetic is unsafe/system-level.
ASYNTAX-81   Numeric address values are distinct from pointer values.
ASYNTAX-82   Attributes use @ syntax.
ASYNTAX-83   Attributes are registry-defined compiler metadata.
ASYNTAX-84   Unknown Core attributes are diagnostics.
ASYNTAX-85   extern explicitly identifies foreign ABI boundaries.
ASYNTAX-86   Foreign ABI selection is part of callable identity.
ASYNTAX-87   Module syntax defines namespace/module identity.
ASYNTAX-88   Import syntax represents compile-time dependency/name resolution.
ASYNTAX-89   Import does not imply runtime module execution.
ASYNTAX-90   pub controls source-level visibility.
ASYNTAX-91   @export controls external native symbol export.
ASYNTAX-92   pub does not imply native symbol export.
ASYNTAX-93   const represents compile-time values.
ASYNTAX-94   comptime represents compile-time execution.
ASYNTAX-95   Comptime uses ordinary Axiom syntax and semantics.
ASYNTAX-96   Generated declarations re-enter normal semantic verification.
ASYNTAX-97   Core syntax does not include an unrestricted macro language.
ASYNTAX-98   Core syntax does not include class/object hierarchy syntax.
ASYNTAX-99   Core syntax does not include exception hierarchy syntax.
ASYNTAX-100  Core syntax must remain readable by humans and machine-generated by AI.
```

---

# Một quyết định syntax tôi muốn đặc biệt giữ

Có một nguyên tắc rất đáng giá:

```text
Rust-like:
&T
&mut T
'a
T: Trait
let mut x
```

Axiom:

```text
view<T>
mut_view<T>
T: Trait
var x
```

Tức là **semantic concept được gọi bằng tên**, thay vì nhồi nhiều meaning vào punctuation.

Điều này có lợi cho AI:

```text
mut_view<Buffer>
```

gần như tự mô tả:

> mutable view vào Buffer.

Trong khi:

```text
&mut Buffer
```

phải học thêm cả hệ thống reference/lifetime semantics.

---

# Syntax tổng thể hiện tại

Axiom bắt đầu có một “ngôn ngữ hình thức” khá nhất quán:

```axiom
import std.fs

struct Buffer<T> {
    data: Vec<T>
}

trait Writable {
    fn write(self: mut_view<Self>, data: view<u8>) -> Result<usize, IoError>
}

impl Writable for File {
    fn write(
        self: mut_view<Self>,
        data: view<u8>
    ) -> Result<usize, IoError> {
        ...
    }
}

async fn download(url: Str) -> Result<Buffer<u8>, NetworkError> {
    let response = http.get(url).await?
    Ok(response.read().await?)
}

fn main() {
    var buffer = Buffer<u8> {
        data: Vec.new()
    }

    let result = download("https://example.com").await

    match result {
        Ok(data) => buffer.data.extend(data),
        Err(error) => println(error)
    }
}
```

Điểm đáng chú ý là **không có một dòng nào cần lifetime annotation, `&mut`, class, virtual, exception, GC syntax hay manual memory management** trong code ứng dụng thông thường.

Nhưng bên dưới compiler vẫn có thể thực hiện toàn bộ:

```text
ownership
capability
alias analysis
escape analysis
drop analysis
Send/Share
async state analysis
ABI lowering
optimization
register allocation
```

Đây chính là triết lý mà chúng ta đã xây từ đầu:

> **Compiler complexity is not programmer complexity.**

---

### Mốc tiếp theo: **BOOTSTRAP-065 — Axiom Lexical Specification & Complete EBNF Grammar**

064 đã freeze **surface syntax ở mức thiết kế**. Bước tiếp theo nên làm rất cụ thể: viết **grammar chính thức**, bao gồm tokenization, whitespace/newline rules, comment, identifier Unicode, integer/float/string/char literals, escape sequences, generic ambiguity, operator precedence/associativity, parser recovery và grammar EBNF cho toàn bộ Axiom Core.

Sau 065, chúng ta sẽ có thể lấy grammar đó để xây **lexer/parser thật**, thay vì tiếp tục thiết kế syntax bằng ví dụ rời rạc.