# BOOTSTRAP-118 — Axiom Grammar & Surface Syntax v0.1

**Trạng thái: FROZEN / COMPLETED**

Mục tiêu của task này là khóa thứ mà lập trình viên thực sự nhìn thấy:

```text
Source
  ↓
Lexer
  ↓
Tokens
  ↓
Parser
  ↓
AST
```

Nguyên tắc:

> **Syntax phải đơn giản hơn C++/Rust ở chỗ người lập trình thường xuyên phải suy nghĩ, nhưng không được làm mất sức mạnh của semantic model.**

---

# 1. Syntax philosophy

Axiom chọn:

- `{}` cho block;
- `()` cho parameter/call/tuple;
- `[]` cho array/index;
- `:` cho type annotation;
- `->` cho return type;
- `::` cho module/type path;
- `.` cho member/method;
- `<>` cho generic arguments;
- `@` cho attributes;
- `?` cho error propagation;
- `|...|` cho closure;
- không dùng lifetime syntax;
- không dùng `&T`, `&mut T`;
- không dùng class syntax.

Ví dụ:

```ax
fn distance(a: view<Point>, b: view<Point>) -> f32 {
    let dx = a.x - b.x;
    let dy = a.y - b.y;
    sqrt(dx * dx + dy * dy)
}
```

---

# 2. Source file

Một source file gồm:

```text
attributes
module declaration
imports
declarations
```

Ví dụ:

```ax
@cfg(target_os = "windows")

import std::math::sqrt;
import std::io::println;

struct Point {
    x: f32,
    y: f32,
}

fn main() {
    println("hello");
}
```

Không có requirement bắt buộc filename phải trùng module name.

Filesystem mapping thuộc build system.

---

# 3. Comments

Hai dạng:

```ax
// line comment
```

và:

```ax
/*
   block comment
*/
```

Documentation:

```ax
/// Calculate distance between two points.
fn distance(...) -> f32 {
    ...
}
```

Documentation được lexer/parser giữ dưới dạng metadata.

---

# 4. Identifier

Identifier cơ bản:

```text
identifier ::= identifier_start identifier_continue*
```

Cho phép Unicode identifier theo lexical specification.

Không cho identifier bắt đầu bằng số.

Ví dụ:

```ax
value
_value
Point2
điểm
```

hợp lệ nếu thỏa lexical normalization rules.

---

# 5. Keywords

Bộ keyword v0.1:

```text
fn
struct
enum
trait
impl
type
const
comptime

let
var

if
else
match
loop
while
for
in
break
continue
return

async
await

import
pub
use

unsafe

true
false

self
Self

as
where
dyn
move
```

`use` được dành cho re-export/namespace manipulation theo module model.

Không thêm keyword chỉ để dự phòng tương lai.

---

# 6. Literal

Core literals:

```ax
123
123u32
123i64

1.5
1.5f32

true
false

"hello"
'c'
```

Character literal có semantic type rõ ràng, không phải integer disguise.

---

# 7. String literals

String literal mặc định là UTF-8 text literal.

```ax
let s = "Xin chào";
```

Raw string được hỗ trợ:

```ax
let s = r#"hello "world""#;
```

Escape:

```ax
\n
\r
\t
\\
\"
\u{...}
```

String literal compile-time không đồng nghĩa heap allocation runtime.

Compiler có thể đặt literal ở read-only static storage.

---

# 8. Byte literals

Để phân biệt text với binary:

```ax
let x = b"hello";
```

Semantic result là byte sequence, không phải Unicode string.

---

# 9. Type syntax

Primitive:

```ax
i32
u64
f32
bool
```

Generic:

```ax
Vec<i32>
Result<Value, Error>
```

Array:

```ax
[i32; 16]
```

Tuple:

```ax
(i32, f32)
```

Function:

```ax
fn(i32, i32) -> i32
```

View:

```ax
view<T>
mut_view<T>
```

Dynamic trait:

```ax
dyn Drawable
```

---

# 10. Không có pointer/reference syntax trong safe Core

Không có:

```text
&T
&mut T
T*
T&&
'a
```

thay vào đó:

```ax
view<T>
mut_view<T>
```

Raw pointer:

```ax
*const T
*mut T
```

chỉ hợp lệ trong unsafe/system contexts.

---

# 11. Generic syntax

```ax
fn max<T: Ord>(a: T, b: T) -> T {
    ...
}
```

Nhiều constraints:

```ax
fn sort<T: Ord + Clone>(items: mut_view<T>) {
    ...
}
```

`where`:

```ax
fn process<T, E>(value: T) -> Result<T, E>
where
    T: Clone + Send,
    E: Error,
{
    ...
}
```

Khuyến nghị:

- dùng inline constraint cho constraint ngắn;
- `where` cho constraint dài.

---

# 12. Struct syntax

```ax
struct Point {
    x: f32,
    y: f32,
}
```

Tuple struct:

```ax
struct UserId(u64);
```

Unit struct:

```ax
struct Marker;
```

Không có class.

---

# 13. Enum syntax

```ax
enum Option<T> {
    Some(T),
    None,
}
```

Struct-like variant:

```ax
enum Event {
    Click { x: i32, y: i32 },
    Quit,
}
```

---

# 14. Trait syntax

```ax
trait Drawable {
    fn draw(self: view<Self>);
}
```

Associated type:

```ax
trait Iterator {
    type Item;

    fn next(self: mut_view<Self>) -> Option<Self::Item>;
}
```

Associated constant:

```ax
trait Numeric {
    const ZERO: Self;
}
```

---

# 15. Impl syntax

Inherent implementation:

```ax
impl Point {
    fn length(self: view<Self>) -> f32 {
        ...
    }
}
```

Trait implementation:

```ax
impl Drawable for Point {
    fn draw(self: view<Self>) {
        ...
    }
}
```

Không cần:

```text
override
virtual
public method
private method
```

Method semantics đến từ receiver + visibility.

---

# 16. Method receiver syntax

Axiom giữ receiver explicit.

### Read

```ax
fn length(self: view<Self>) -> f32
```

### Mutate

```ax
fn normalize(self: mut_view<Self>) {
    ...
}
```

### Consume

```ax
fn into_bytes(self: Self) -> Bytes {
    ...
}
```

Điều này cực kỳ rõ ràng với compiler nhưng vẫn dễ đọc với programmer.

---

# 17. Method call

```ax
point.length();
point.normalize();
value.into_bytes();
```

Semantic lowering:

```ax
length(point)
normalize(point)
into_bytes(value)
```

---

# 18. Extension methods

Không có special extension syntax.

Chỉ cần function có receiver đầu tiên:

```ax
fn clamp(self: view<f32>, min: f32, max: f32) -> f32 {
    ...
}
```

Sau khi import namespace phù hợp:

```ax
x.clamp(0.0, 1.0);
```

Đây là một điểm rất mạnh của Axiom:

> **Method syntax không yêu cầu class.**

---

# 19. Variables

Immutable:

```ax
let x = 10;
```

Mutable:

```ax
var x = 10;
x = 20;
```

Explicit type:

```ax
let x: i32 = 10;
```

Không có:

```text
mut x
```

riêng biệt.

---

# 20. Assignment

```ax
x = value;
x.field = value;
x[index] = value;
```

Assignment yêu cầu writable capability.

Compiler không coi assignment syntax là quyền tự động vượt qua ownership rules.

---

# 21. Function syntax

```ax
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

No-return:

```ax
fn log(message: Str) {
    ...
}
```

tương đương return `unit`.

---

# 22. Named arguments

**Không đưa vào Core v0.1.**

Lý do:

- tăng parser complexity;
- làm overload/resolution phức tạp;
- không cần thiết cho semantic model.

Có thể thêm ở library/tooling layer trong edition tương lai nếu thực sự cần.

---

# 23. Default parameters

**Không có trong Core v0.1.**

Thay vào đó dùng:

```ax
fn foo(config: Config)
```

và helper:

```ax
fn foo_default() {
    foo(Config.default());
}
```

Giữ call semantics đơn giản.

---

# 24. Overloading

Axiom cho phép compile-time overload resolution nhưng không cho phép conversion chains tùy tiện.

Ví dụ:

```ax
fn print(x: i32)
fn print(x: f32)
fn print(x: Str)
```

Compiler chọn theo exact type/resolution rules.

Không tự động:

```text
i32 → f32 → SomeType → ...
```

để tìm overload.

---

# 25. Operators

Operators được biểu diễn bằng compiler-known trait operations.

Ví dụ:

```ax
a + b
```

conceptually:

```ax
Add::add(a, b)
```

Nhưng primitive operators như:

```text
&&
||
==
!=
=
```

có semantics compiler-defined.

Short-circuit:

```ax
a && b
a || b
```

không được biến thành ordinary eager function call.

---

# 26. Operator precedence

Khóa theo nhóm:

```text
highest
    ()
    []
    .
    ?

    unary: ! - + ~
    
    * / %
    
    + -
    
    << >>
    
    < <= > >=
    
    == !=
    
    &
    
    ^
    
    |
    
    &&
    
    ||
    
    .. ..=
    
    =
lowest
```

Assignment right-associative.

Các operator khác mặc định left-associative.

---

# 27. `?`

Error propagation:

```ax
fn load() -> Result<Data, Error> {
    let file = open("data.bin")?;
    let data = read(file)?;
    Ok(data)
}
```

Parser coi `?` là postfix operator.

Semantic lowering vẫn phải tạo cleanup chính xác.

---

# 28. If expression

```ax
let max = if a > b {
    a
} else {
    b
};
```

Hai branch phải compatible về result type.

---

# 29. `if let`

```ax
if let Some(x) = value {
    use(x);
}
```

Đây chỉ là syntactic sugar cho pattern matching.

---

# 30. Match

```ax
match value {
    Some(x) => use(x),
    None => fallback(),
}
```

Có thể dùng block:

```ax
match value {
    Some(x) => {
        process(x);
    }

    None => {
        fallback();
    }
}
```

Trailing comma được phép.

---

# 31. Pattern syntax

Core patterns:

```text
identifier
_
literal
tuple
struct
enum variant
array
range
```

Ví dụ:

```ax
match point {
    Point { x: 0, y } => ...
    Point { x, y } => ...
}
```

---

# 32. Binding shorthand

```ax
Point { x, y }
```

tương đương binding field cùng tên.

Có thể rename:

```ax
Point { x: px, y: py }
```

---

# 33. Move trong pattern

Pattern không mặc định clone.

Nếu pattern consume value:

```ax
match value {
    Some(x) => consume(x),
    None => ...
}
```

ownership analysis quyết định state.

---

# 34. Loops

Infinite:

```ax
loop {
    ...
}
```

While:

```ax
while condition {
    ...
}
```

For:

```ax
for item in items {
    ...
}
```

---

# 35. Loop value

```ax
let result = loop {
    if ready() {
        break value;
    }
};
```

`break value` trả result của loop.

---

# 36. Ranges

```ax
0..10
0..=10
```

Range là value abstraction, không phải magic loop syntax.

---

# 37. `for`

`for` semantic dựa trên iterator protocol.

Conceptually:

```ax
let it = items.into_iter();

loop {
    match it.next() {
        Some(x) => body(x),
        None => break,
    }
}
```

Compiler được phép lower/specialize trực tiếp.

---

# 38. Closures

Syntax:

```ax
|x| x + 1
```

Multiple:

```ax
|x, y| x + y
```

Typed:

```ax
|x: i32| -> i32 {
    x * 2
}
```

---

# 39. Move closure

```ax
move |x| {
    use(value);
    x
}
```

`move` ép capture ownership semantics phù hợp.

Không phải “move toàn bộ memory”; compiler vẫn tối ưu environment.

---

# 40. Async syntax

```ax
async fn fetch() -> Result<Data, Error> {
    let x = await read();
    Ok(x)
}
```

Hoặc expression:

```ax
let future = async {
    ...
};
```

`await` chỉ hợp lệ trong async context phù hợp.

---

# 41. Spawn

**Không phải Core keyword.**

Ví dụ library:

```ax
let handle = thread::spawn(|| work());
```

hoặc:

```ax
let task = async::spawn(fetch());
```

Điều này giữ:

```text
async ≠ executor
async ≠ thread
```

---

# 42. Comptime syntax

Expression:

```ax
const SIZE: usize = 1024;
```

Compile-time execution:

```ax
comptime {
    generate_tables();
}
```

Comptime function:

```ax
comptime fn factorial(n: usize) -> usize {
    if n == 0 {
        1
    } else {
        n * factorial(n - 1)
    }
}
```

---

# 43. Unsafe syntax

Block:

```ax
unsafe {
    *ptr = value;
}
```

Function:

```ax
unsafe fn read_raw(ptr: *const u8) -> u8 {
    *ptr
}
```

Unsafe không lan truyền toàn chương trình.

---

# 44. Raw pointer syntax

```ax
*const T
*mut T
```

Dereference:

```ax
*p
```

Field access:

```ax
p->field
```

Pointer arithmetic nằm trong unsafe/system API.

---

# 45. Address-taking

Không dùng:

```text
&x
```

trong Core.

Dùng explicit system operation:

```ax
address_of(x)
```

nếu API cần raw pointer.

Điều này tránh nhầm lẫn giữa:

```text
reference
address
borrow
view
```

---

# 46. Import

```ax
import std::io::File;
```

Nhiều:

```ax
import std::io::{File, Stream};
```

Alias:

```ax
import graphics::Color as GColor;
```

Module alias:

```ax
import graphics::renderer as gfx;
```

---

# 47. Re-export

```ax
pub use math::Vec3;
```

`use` ở đây là namespace operation, không phải runtime operation.

---

# 48. Visibility

```ax
fn private_fn() {}

pub fn public_fn() {}
```

Struct fields:

```ax
pub struct User {
    pub id: u64,
    name: String,
}
```

Field không ghi `pub` là private.

---

# 49. Attributes

Ví dụ:

```ax
@repr(C)
struct Header {
    ...
}
```

```ax
@inline
fn add(...) -> i32 { ... }
```

```ax
@kernel
fn add_vectors(...) { ... }
```

```ax
@export("my_function")
pub fn foo() {}
```

---

# 50. Attribute grammar

General:

```text
@identifier
@identifier(...)
@path::identifier(...)
```

Compiler quyết định attribute hợp lệ.

Không có arbitrary runtime attribute semantics.

---

# 51. FFI syntax

Ví dụ:

```ax
extern "C" {
    fn puts(s: *const u8) -> i32;
}
```

Foreign declarations phải tuân thủ FFI contract.

Wrapper safe:

```ax
pub fn print(s: Str) {
    unsafe {
        ...
    }
}
```

---

# 52. C ABI export

```ax
@export("ax_add")
extern "C" fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

`extern` và `@export` có semantics khác nhau:

- `extern`: calling/ABI contract;
- `@export`: symbol visibility/export.

---

# 53. Semicolon rules

Axiom **không bỏ semicolon hoàn toàn**.

Quy tắc:

### Statement

```ax
let x = 10;
x = 20;
foo();
```

dùng `;`.

### Block expression

```ax
let x = {
    10
};
```

expression cuối block **không cần semicolon**.

Điều này giúp parser phân biệt:

```ax
{
    foo();
    bar()
}
```

với:

```ax
{
    foo();
    bar();
}
```

mà không tạo quá nhiều ambiguity.

---

# 54. Trailing comma

Được phép trong:

```ax
function arguments
parameters
struct fields
enum variants
generic arguments
generic parameters
tuple
array
imports
patterns
```

Ví dụ:

```ax
struct Config {
    width: usize,
    height: usize,
}
```

Formatter sẽ chuẩn hóa.

---

# 55. Empty tuple / unit

```ax
()
```

là `unit`.

Function:

```ax
fn foo() {}
```

có return type:

```text
unit
```

nếu không khai báo return type.

---

# 56. Tuple

```ax
let p = (10, 20);
```

Single tuple:

```ax
(x,)
```

để phân biệt với grouping:

```ax
(x)
```

---

# 57. Array

```ax
let a = [1, 2, 3];
```

Fixed-size type:

```ax
[i32; 3]
```

Array literal phải có kích thước compile-time xác định.

Dynamic collection dùng `Vec`.

---

# 58. Indexing

```ax
a[i]
```

được kiểm tra bounds trong safe semantics.

Unchecked:

```ax
unsafe {
    a.get_unchecked(i)
}
```

nên là library/system API thay vì syntax mới.

---

# 59. Field access

```ax
point.x
```

Tuple:

```ax
point.0
```

Không dùng dynamic field names trong Core.

---

# 60. Type casts

Semantic conversion:

```ax
x as i64
```

Bit reinterpretation:

```ax
bitcast::<u32>(x)
```

Hai operation không được hợp nhất.

---

# 61. `as` semantics

`as` chỉ thực hiện conversion được specification cho phép.

Không phải:

```text
"hãy thử mọi conversion cho đến khi compile"
```

Invalid conversion → compile error.

---

# 62. Generic turbofish

Axiom **không bắt buộc dùng `::<>` kiểu Rust**.

Có thể viết:

```ax
foo<i32>(x)
```

Parser phải xử lý ambiguity bằng grammar/context rõ ràng.

Path:

```ax
std::mem::size_of::<T>()
```

có thể vẫn cần cú pháp rõ ràng.

Khuyến nghị v0.1:

```ax
size_of<T>()
```

cho generic function calls.

Ví dụ:

```ax
let n = size_of<MyStruct>();
```

Điều này giúp syntax nhẹ hơn Rust.

---

# 63. Generic type construction

```ax
Vec<i32>
Result<Data, Error>
Option<String>
```

không có distinction syntax phức tạp giữa type-level và value-level generic arguments ở v0.1.

---

# 64. Const generic

v0.1:

```ax
Array<T, 16>
```

được phép với const parameter loại scalar được hỗ trợ.

Ví dụ:

```ax
struct Matrix<T, const N: usize> {
    data: [T; N],
}
```

Nhưng syntax `const` generic parameter cần được khóa rõ trong parser/type grammar.

---

# 65. Không có macro syntax v0.1

Không có:

```text
macro_rules
proc_macro
#
$
```

Core.

Thay thế bằng:

```text
comptime
@derive
typed generation
```

Điều này giúp language có một semantic pipeline duy nhất.

---

# 66. `derive`

```ax
@derive(Copy, Clone, Debug)
struct Point {
    x: f32,
    y: f32,
}
```

`@derive` là compiler-known typed generation.

Generated declarations quay lại compiler pipeline bình thường.

---

# 67. Syntax không encode ownership bureaucracy

Đây là quyết định rất quan trọng.

Không xuất hiện:

```text
<'a>
&T
&mut T
'a
where T: 'a
```

trong code thông thường.

Programmer viết:

```ax
fn process(data: view<Data>) { ... }
```

và compiler tự phân tích provenance/lifetime.

---

# 68. Nhưng semantic ownership vẫn rõ

Ví dụ:

```ax
fn consume(data: Data) { ... }

fn inspect(data: view<Data>) { ... }

fn modify(data: mut_view<Data>) { ... }
```

Ba API nhìn vào là hiểu ngay:

```text
Data       → consume ownership
view<Data> → read access
mut_view   → write access
```

Đây là điểm Axiom khác đáng kể với C++/Rust.

---

# 69. API example hoàn chỉnh

```ax
struct User {
    id: u64,
    name: String,
}

impl User {
    fn rename(self: mut_view<Self>, name: String) {
        self.name = name;
    }

    fn id(self: view<Self>) -> u64 {
        self.id
    }
}

fn update(user: mut_view<User>) {
    user.rename("Axiom");
}

fn main() {
    var user = User {
        id: 42,
        name: "Alice",
    };

    update(user);

    println(user.id());
}
```

Không có:

```text
class
this
&
&mut
lifetime
new
delete
```

nhưng compiler vẫn có đủ semantic information để verify ownership/capability.

---

# 70. Syntax complexity budget

Axiom v0.1 **không cố giảm số ký tự bằng mọi giá**.

Ưu tiên:

```text
readability
predictability
parser determinism
IDE friendliness
AI friendliness
diagnostic quality
```

hơn là “ít ký tự nhất”.

---

# 71. AI-friendly syntax

Syntax phải có đặc điểm:

```text
one construct → one obvious interpretation
```

Tránh những ambiguity kiểu:

```text
C++ < > >> parsing
macro expansion altering grammar
implicit conversion chains
operator overloading with arbitrary syntax
context-dependent lifetime syntax
```

AST phải dễ map ngược:

```text
source
→ AST
→ HIR
→ diagnostic
```

---

# 72. Parser architecture

Khuyến nghị:

```text
Lexer
  ↓
Token Stream
  ↓
Parser
  ↓
Lossless Syntax Tree
  ↓
AST
```

**Lossless Syntax Tree** giữ:

- comments;
- whitespace/trivia;
- exact token spans;
- malformed syntax;
- source structure.

AST semantic thì sạch hơn.

Điều này rất tốt cho IDE/formatter/code actions.

---

# 73. Error recovery

Parser không nên dừng ngay tại lỗi đầu tiên.

Ví dụ:

```ax
fn foo(
    x: i32
    y: i32
) {
```

parser cố recover để báo thêm lỗi.

Nhưng AST lỗi không được đi vào semantic compiler như code hợp lệ.

---

# 74. Parser diagnostics

Stable codes:

```text
EPARSE_UNEXPECTED_TOKEN
EPARSE_EXPECTED_TOKEN
EPARSE_UNCLOSED_DELIMITER
EPARSE_INVALID_LITERAL
EPARSE_INVALID_ATTRIBUTE
EPARSE_INVALID_PATTERN
EPARSE_INVALID_TYPE
```

Message text có thể thay đổi.

Diagnostic identity không.

---

# 75. Formatter

Axiom sẽ có formatter chính thức:

```text
ax fmt
```

Formatter không được thay đổi semantics.

Style mặc định:

- 4 spaces;
- braces same line;
- trailing commas trong multiline;
- UTF-8;
- một declaration/block structure rõ ràng.

---

# 76. Syntax versioning

Syntax thuộc **language edition**, không phụ thuộc package version.

Ví dụ:

```text
edition = "2026"
```

Một package mới có thể dùng syntax edition mới trong khi dependency cũ vẫn compile theo edition cũ.

Semantic compatibility phải được compiler xử lý rõ ràng.

---

# 77. Reserved future syntax

Chỉ reserve những token thực sự cần.

Không nên reserve hàng trăm keyword “cho tương lai”.

Lý do:

> Axiom ưu tiên khả năng tiến hóa thông qua edition và contextual grammar hơn là khóa trước cả ngôn ngữ.

---

# 78. Grammar architecture

Parser grammar được chia:

```text
SourceFile
Declaration
Type
Pattern
Expression
Statement
Block
Attribute
Path
Generic
Parameter
```

Không tạo một grammar khổng lồ duy nhất.

---

# 79. AST principle

AST không chứa implementation details như:

```text
LLVM Value
register
stack slot
pointer address
Drop glue
```

AST chỉ biểu diễn source semantics.

---

# 80. AST → HIR boundary

AST giữ syntax:

```ax
p.length()
```

HIR nên chuyển thành semantic method resolution:

```text
MethodCall {
    receiver: p,
    FunctionId: length,
    ...
}
```

Sau HIR, compiler không còn phải giải thích syntax method nữa.

---

# 81. Surface sugar

Các syntax sugar:

```text
method call
if let
for
?
async
closure shorthand
```

được normalize trước hoặc trong HIR.

Mục tiêu:

```text
AST expressive
HIR canonical
MIR explicit
```

---

# 82. Canonical HIR

Một semantic construct chỉ nên có một canonical HIR representation.

Ví dụ:

```text
x.y()
```

và:

```text
y(x)
```

nếu cùng resolve tới function semantics phù hợp thì HIR có thể dùng cùng representation.

Điều này cực kỳ hữu ích cho compiler và AI tooling.

---

# 83. Surface syntax đã khóa

Axiom v0.1 chính thức có:

```text
struct
enum
trait
impl
fn
let
var
if
match
loop
while
for
break
continue
return
closure
async
await
comptime
const
unsafe
import
pub
use
generic
where
dyn
attributes
```

và **không có class/inheritance/lifetime/borrow syntax/macro language/exception syntax**.

---

# 84. Invariants

### `AGRAM-20`
Source is UTF-8.

### `AGRAM-21`
Parsing is deterministic.

### `AGRAM-22`
Evaluation order is deterministic left-to-right.

### `AGRAM-23`
Safe Core has no programmer-written lifetime syntax.

### `AGRAM-24`
Safe Core has no general reference syntax.

### `AGRAM-25`
Raw pointers are explicitly unsafe/system constructs.

### `AGRAM-26`
Types are explicit at semantic boundaries.

### `AGRAM-27`
Implicit numeric narrowing is forbidden.

### `AGRAM-28`
Implicit Clone is forbidden.

### `AGRAM-29`
Implicit dynamic dispatch is forbidden.

### `AGRAM-30`
Implicit heap allocation is not represented by surface syntax.

### `AGRAM-31`
Method syntax is syntactic sugar over function semantics.

### `AGRAM-32`
Struct is the primary aggregate construct.

### `AGRAM-33`
Class inheritance is not part of Core v0.1.

### `AGRAM-34`
Pattern matching is exhaustive where required.

### `AGRAM-35`
`?` preserves ownership and cleanup semantics.

### `AGRAM-36`
`async` does not imply execution.

### `AGRAM-37`
`await` represents suspension.

### `AGRAM-38`
`unsafe` marks explicit unsafe boundaries.

### `AGRAM-39`
Attributes are typed compiler metadata.

### `AGRAM-40`
Macros do not introduce a second semantic language in Core v0.1.

### `AGRAM-41`
Comptime-generated declarations re-enter ordinary semantic analysis.

### `AGRAM-42`
AST preserves source structure independently from semantic HIR.

### `AGRAM-43`
HIR uses canonical semantic representations.

### `AGRAM-44`
Formatter transformations preserve semantics.

### `AGRAM-45`
Parser recovery cannot silently manufacture valid semantics.

### `AGRAM-46`
Diagnostic identities are stable independently from wording.

### `AGRAM-47`
Syntax edition is independent of package version.

### `AGRAM-48`
Surface syntax must not expose compiler implementation details.

### `AGRAM-49`
Axiom syntax must remain compatible with lossless parsing and IDE tooling.

### `AGRAM-50`
Every surface construct has exactly one defined semantic interpretation.

---

# 85. Kết quả của BOOTSTRAP-118

Đến đây pipeline frontend đã khá rõ:

```text
UTF-8 Source
    ↓
Lexer
    ↓
Lossless Syntax Tree
    ↓
AST
    ↓
Name Resolution
    ↓
HIR
    ↓
Type / Trait Resolution
    ↓
Typed HIR
    ↓
MIR
```

Và quan trọng hơn, **syntax không còn quyết định architecture**. Syntax chỉ là lớp biểu đạt phía trên semantic model đã khóa.

---

# BOOTSTRAP-119 — Formal AST / HIR Semantic Contract

Task tiếp theo sẽ khóa **cấu trúc dữ liệu compiler thực sự phải tạo ra từ syntax**.

Đây là bước rất quan trọng trước khi bắt đầu code compiler.

Chúng ta sẽ thiết kế cụ thể:

```text
SyntaxNode
Token
SourceSpan
AST node kinds

Declaration
Expression
Pattern
TypeSyntax
Statement

HIR Declaration
HIR Expression
HIR Place
HIR Pattern
HIR Type

Name Resolution
DeclarationId
TypeId
FunctionId
FieldId
VariantId

Desugaring
method → function
for → iterator loop
? → match
if let → match
closure → environment
async → Future construction
```

và đặc biệt:

> **AST có thể phản ánh cách programmer viết code, nhưng HIR phải phản ánh cách compiler hiểu code.**

Sau BOOTSTRAP-119, chúng ta sẽ có đủ nền móng để chuyển từ việc “thiết kế Axiom” sang **thiết kế compiler implementation từng subsystem một**.