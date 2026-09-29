# BOOTSTRAP-123 — Formal Grammar, Syntax & Surface Language Specification

**Trạng thái: FROZEN / COMPLETED**

Mục tiêu của task này là khóa **hình thức bề mặt của Axiom** để parser, compiler, IDE và AI agent đều hiểu cùng một ngôn ngữ.

Nguyên tắc:

> **Syntax phải dễ đọc, dễ sinh bằng AI, dễ parse, ít ngoại lệ và không yêu cầu compiler đoán ý định của programmer.**

Không cố làm syntax “ngắn nhất có thể”. Ưu tiên:

1. rõ nghĩa;
2. nhất quán;
3. dễ parse;
4. dễ format;
5. dễ sinh bằng AI;
6. ít ambiguity;
7. không tạo hidden semantics.

---

# 1. Tổng thể syntax

Axiom sử dụng syntax kiểu C-family hiện đại nhưng bỏ nhiều legacy complexity:

```ax
package app;

import std::io::File;

struct User {
    id: u64,
    name: String,
}

impl User {
    fn new(id: u64, name: String) -> User {
        User { id, name }
    }

    fn greet(self: view<User>) {
        print("Hello ", self.name);
    }
}

fn main() {
    let user = User.new(1, "Axiom");
    user.greet();
}
```

Các đặc điểm:

- `{}` cho block;
- `;` kết thúc declaration/statement khi cần;
- trailing comma được phép trong danh sách;
- `//` và `/* */` comments;
- UTF-8;
- Unicode identifiers;
- không indentation-sensitive;
- không semicolon insertion;
- expression-oriented;
- `let` immutable;
- `var` mutable.

---

# 2. Không dùng automatic semicolon insertion

Axiom **không** dùng cơ chế kiểu JavaScript/Go để tự đoán semicolon.

Ví dụ:

```ax
let x = foo()
let y = bar()
```

được parser hiểu theo newline/token rules rõ ràng, nhưng declaration vẫn phải kết thúc syntactically.

Khuyến nghị canonical:

```ax
let x = foo();
let y = bar();
```

Điều này giúp:

- parser đơn giản;
- formatter deterministic;
- AI generation ổn định;
- copy/paste code ít tạo ambiguity.

---

# 3. Whitespace

Whitespace thông thường không mang semantic meaning.

```ax
let x = 1 + 2;
```

và:

```ax
let x=
    1+
    2;
```

cùng semantics.

Ngoại lệ:

- whitespace trong literal;
- Unicode identifiers;
- comments;
- token separation.

---

# 4. Comments

Line comment:

```ax
// comment
```

Block comment:

```ax
/*
    comment
*/
```

Nested block comments:

```ax
/*
    outer
    /*
        inner
    */
*/
```

**Được phép.**

Điều này giúp comment generated code và source transformation dễ hơn.

---

# 5. Identifier

Identifier ASCII cơ bản:

```text
[a-zA-Z_][a-zA-Z0-9_]*
```

Axiom cũng cho phép Unicode identifier theo Unicode XID:

```ax
struct Người {
    tên: String,
}
```

Nhưng compiler phải canonicalize/validate Unicode identifier theo một chuẩn xác định.

---

# 6. Unicode normalization

Identifier phải được xử lý theo normalization policy cố định.

Khuyến nghị:

> **NFC normalization + Unicode XID rules.**

Ví dụ hai spelling Unicode canonical-equivalent không được tạo hai declaration khác nhau.

---

# 7. Keyword set

Core keyword ban đầu:

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
fn
for
if
impl
import
in
let
loop
match
package
pub
return
struct
trait
unsafe
var
while
where
```

Các keyword tương lai có thể reserved từ đầu để tránh breaking syntax:

```text
actor
defer
macro
module
operator
throws
yield
```

nhưng không có semantic trong Core v0.1.

---

# 8. Declaration model

Declaration chính:

```text
package
import
struct
enum
trait
impl
fn
const
comptime
type
```

Có thể thêm:

```text
extern
```

cho FFI/system layer.

---

# 9. Package declaration

```ax
package my_app;
```

Subpackage:

```ax
package graphics.renderer;
```

Package identity vẫn được xác định bởi build/package system, không chỉ bởi source declaration.

---

# 10. Import

Canonical:

```ax
import std::io::File;
```

Multiple:

```ax
import std::io::{File, Stream, Socket};
```

Alias:

```ax
import graphics::Color as GColor;
```

Module alias:

```ax
import graphics::renderer as gfx;
```

Re-export:

```ax
pub use math::Vec3;
```

---

# 11. Import không phải runtime operation

```ax
import foo::bar;
```

chỉ ảnh hưởng:

- name resolution;
- dependency graph;
- metadata;
- compilation.

Không:

- execute code;
- allocate;
- initialize runtime object.

---

# 12. `struct`

Canonical:

```ax
struct Point {
    x: f32,
    y: f32,
}
```

Field declaration:

```text
name : Type
```

Trailing comma được phép.

---

# 13. Struct initializer

```ax
let p = Point {
    x: 10.0,
    y: 20.0,
};
```

Field shorthand:

```ax
let x = 10.0;
let y = 20.0;

let p = Point { x, y };
```

---

# 14. Struct update

Có thể hỗ trợ:

```ax
let p2 = Point {
    x: 100.0,
    ..p
};
```

Semantic rule:

- fields explicitly supplied được lấy trước;
- remaining fields move/copy từ `p`;
- không implicit clone.

---

# 15. Tuple

Tuple:

```ax
let p = (10, 20);
```

Type:

```ax
(i32, i32)
```

Unit:

```ax
()
```

Tuple indexing:

```ax
p.0
p.1
```

---

# 16. Array

Fixed-size array:

```ax
let a = [1, 2, 3, 4];
```

Type:

```ax
[i32; 4]
```

Repeated initializer:

```ax
let a = [0; 1024];
```

Array là value type.

---

# 17. Slice/view

Safe access surface:

```ax
view<T>
mut_view<T>
```

Ví dụ:

```ax
fn sum(values: view<i32>) -> i32 {
    ...
}
```

Programmer không cần viết raw pointer.

---

# 18. Enum

```ax
enum Color {
    Red,
    Green,
    Blue,
}
```

Payload:

```ax
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

---

# 19. Pattern

```ax
match value {
    Color::Red => ...
    Color::Green => ...
    Color::Blue => ...
}
```

Payload:

```ax
match result {
    Result::Ok(value) => ...
    Result::Err(error) => ...
}
```

---

# 20. Pattern grammar

Core patterns:

```text
_
identifier
literal
tuple
struct
enum variant
array
range
or-pattern
```

Ví dụ:

```ax
match x {
    0 => ...
    1..=10 => ...
    _ => ...
}
```

---

# 21. Binding trong pattern

```ax
match user {
    User { id, name } => ...
}
```

Mutable binding:

```ax
var User { id, name } = user;
```

Binding mode không được làm thay đổi ownership semantics âm thầm.

---

# 22. `if`

```ax
if x > 0 {
    positive();
} else {
    negative();
}
```

Condition bắt buộc là `bool`.

Không có:

```ax
if (x)
```

với `x: i32`.

Không có implicit truthiness.

---

# 23. `if` là expression

```ax
let result =
    if condition {
        10
    } else {
        20
    };
```

Hai branch phải có type tương thích theo type rules.

---

# 24. `loop`

```ax
loop {
    work();

    if done {
        break;
    }
}
```

`break` có thể trả value:

```ax
let result = loop {
    if ready {
        break value;
    }

    wait();
};
```

---

# 25. `while`

```ax
while condition {
    work();
}
```

---

# 26. `for`

```ax
for item in items {
    process(item);
}
```

Semantics dựa trên iterator protocol.

Compiler có thể tối ưu thành loop native.

---

# 27. `break` và `continue`

```ax
loop {
    if x < 0 {
        continue;
    }

    if done {
        break;
    }
}
```

Nested loop:

```ax
'outer: loop {
    loop {
        break 'outer;
    }
}
```

Label syntax:

```text
'label
```

---

# 28. Function

```ax
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Return type có thể bỏ nếu inferred trong contexts được phép, nhưng **khuyến nghị explicit return type cho public API**.

---

# 29. `return`

```ax
return value;
```

Early return:

```ax
if invalid {
    return Err(error);
}
```

Final expression:

```ax
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

---

# 30. `let` và `var`

Immutable:

```ax
let x = 10;
```

Mutable:

```ax
var x = 10;
x = 20;
```

Không dùng:

```ax
let mut x
```

vì Axiom chọn một keyword riêng cho mutable binding.

---

# 31. Shadowing

Cho phép:

```ax
let x = 10;
let x = x + 1;
```

Nhưng không được biến shadowing thành implicit mutation.

Hai declaration là hai bindings khác nhau.

Compiler/IDE phải phân biệt `DeclarationId`.

---

# 32. Type annotation

```ax
let x: i32 = 10;
```

Generic:

```ax
let x: Vec<i32> = Vec.new();
```

Nested:

```ax
let x: Option<Vec<String>>;
```

---

# 33. Type expression

Type grammar conceptually:

```text
Type
 ├── PrimitiveType
 ├── PathType
 ├── TupleType
 ├── ArrayType
 ├── ViewType
 ├── MutViewType
 ├── FunctionType
 └── NeverType
```

---

# 34. Function type

```ax
fn(i32, i32) -> i32
```

Ví dụ:

```ax
let f: fn(i32) -> i32 = square;
```

Capturing closure không tự động có cùng type với function pointer.

---

# 35. Generic declaration

```ax
fn max<T>(a: T, b: T) -> T
where
    T: Ord
{
    ...
}
```

Generic struct:

```ax
struct Box<T> {
    value: T,
}
```

---

# 36. Generic constraints

Canonical:

```ax
fn print<T>(value: T)
where
    T: Display
{
    ...
}
```

Có thể hỗ trợ inline form:

```ax
fn print<T: Display>(value: T) {
    ...
}
```

Hai forms cùng semantics.

---

# 37. Trait

```ax
trait Display {
    fn display(self: view<Self>) -> String;
}
```

Associated type:

```ax
trait Iterator {
    type Item;

    fn next(self: mut_view<Self>) -> Option<Self::Item>;
}
```

---

# 38. `impl`

Inherent:

```ax
impl Point {
    fn length(self: view<Point>) -> f32 {
        ...
    }
}
```

Trait implementation:

```ax
impl Display for Point {
    fn display(self: view<Point>) -> String {
        ...
    }
}
```

---

# 39. Method receiver

Axiom surface:

```ax
p.length();
p.translate(dx, dy);
```

Compiler resolution dựa trên semantic receiver:

```text
view<Self>
mut_view<Self>
Self
```

Ví dụ:

```ax
fn length(self: view<Point>) -> f32
```

---

# 40. Override

Không cần:

```ax
override
```

Trait implementation:

```ax
impl Trait for Type {
    fn method(...) {
        ...
    }
}
```

tự động override default trait method nếu signature tương thích.

---

# 41. Associated function

```ax
impl Vec3 {
    fn zero() -> Vec3 {
        Vec3 { x: 0, y: 0, z: 0 }
    }
}
```

Call:

```ax
let v = Vec3.zero();
```

Không có `static` keyword.

---

# 42. Path syntax

```text
module::type
module::function
Type::Variant
```

Ví dụ:

```ax
std::io::File.open(...)
Result::Ok(value)
```

---

# 43. Method syntax vs path syntax

```ax
user.greet();
```

là method call.

```ax
User.new(...);
```

là associated function.

```ax
std::io::File.open(...);
```

là path-qualified associated call nếu semantic declaration phù hợp.

---

# 44. Operators

Core operators:

```text
+
-
*
/
%
==
!=
<
<=
>
>=
&&
||
!
&
|
^
<<
>>
```

Assignment:

```text
=
+=
-=
*=
/=
%=
```

Index:

```text
x[i]
```

Range:

```text
a..b
a..=b
```

---

# 45. Không implicit numeric conversion

Không cho:

```ax
let x: i64 = 10_i32;
```

nếu không có conversion hợp lệ.

Explicit:

```ax
let x: i64 = 10_i32 as i64;
```

Điều này làm AI-generated code ít tạo bug âm thầm.

---

# 46. Cast syntax

```ax
x as i64
```

phân biệt:

```text
CAST
BITCAST
```

`as` không đồng nghĩa với arbitrary reinterpretation.

Bitcast là intrinsic/unsafe-level operation khi cần.

---

# 47. Literals

Integer:

```ax
42
0xff
0b1010
0o755
1_000_000
```

Unsigned suffix:

```ax
42u32
```

Signed:

```ax
42i64
```

Float:

```ax
3.14
3.14f32
1e-5
```

---

# 48. Boolean

```ax
true
false
```

Không có implicit integer→bool.

---

# 49. Character

Khuyến nghị:

```ax
'a'
'\n'
'\u{1F600}'
```

Character semantic là Unicode scalar value.

Byte literal riêng:

```ax
b'a'
```

---

# 50. String

Text literal:

```ax
"Hello, world"
```

Multiline:

```ax
"""
Hello
world
"""
```

Escape:

```ax
"\n"
"\t"
"\""
"\\"
"\u{1F600}"
```

String literal là text, không phải C string.

---

# 51. Byte string

```ax
b"GET / HTTP/1.1\r\n"
```

Type:

```text
bytes / byte sequence
```

không phải Unicode String.

---

# 52. Raw string

Cho regex/path/config:

```ax
r"C:\Users\test"
```

hoặc multiline raw form nếu grammar cần.

Raw string không làm thay đổi semantic type.

---

# 53. String interpolation

Khuyến nghị hỗ trợ:

```ax
let message = "Hello {name}, id={id}";
```

Parser phải phân biệt interpolation syntax rõ ràng.

Không sử dụng macro string magic.

Semantic lowering:

```text
format/display operations
```

có thể được compiler optimize.

---

# 54. `Option` / `Result`

Không có `null`.

```ax
let user: Option<User>;
```

Result:

```ax
fn read() -> Result<String, IoError>
```

---

# 55. `?`

```ax
fn load() -> Result<Data, Error> {
    let file = File.open(path)?;
    let data = file.read()?;
    Ok(parse(data)?)
}
```

`?` là syntax sugar compiler-known cho Result/Option-compatible propagation.

Không phải exception.

---

# 56. `unsafe`

Block:

```ax
unsafe {
    let p = address_of(x);
    ...
}
```

Function:

```ax
unsafe fn read_register(addr: usize) -> u32 {
    ...
}
```

Unsafe boundary rõ ràng.

---

# 57. `comptime`

Compile-time expression:

```ax
const SIZE: usize = comptime compute_size();
```

hoặc:

```ax
comptime {
    generate_types();
}
```

`comptime` không tạo runtime feature.

---

# 58. `const`

```ax
const MAX_SIZE: usize = 1024;
```

`const` là compile-time value.

Không phải mutable global.

---

# 59. Attribute syntax

Canonical:

```ax
@repr(C)
struct Point {
    ...
}
```

Multiple:

```ax
@inline
@target_feature("avx2")
fn dot(...) {
    ...
}
```

Attribute argument có:

```text
identifier
string
integer
boolean
path
list
```

tùy attribute schema.

---

# 60. Attribute không phải macro

Sai conceptual model:

```text
@something arbitrary code
```

Attribute là typed compiler metadata.

Compiler registry xác định:

```text
name
namespace
kind
arguments
targets
semantic strength
```

---

# 61. `extern`

FFI:

```ax
extern "C" {
    fn puts(text: *const u8) -> i32;
}
```

hoặc function-level:

```ax
extern "C" fn callback(...) {
    ...
}
```

Raw pointer chỉ xuất hiện ở FFI/system boundary.

---

# 62. `@export`

```ax
@export("axiom_main")
pub fn main() {
    ...
}
```

`pub` và external symbol visibility là hai concept khác nhau.

---

# 63. Visibility

v0.1 chỉ:

```ax
fn private_fn() {}
pub fn public_fn() {}
```

Struct:

```ax
pub struct User {
    pub id: u64,
    name: String,
}
```

Visibility của field độc lập với visibility của type.

---

# 64. Closure

```ax
let add = |a, b| a + b;
```

Typed:

```ax
let add = |a: i32, b: i32| -> i32 {
    a + b
};
```

Capture inferred.

---

# 65. Explicit move capture

```ax
let f = move |x| {
    use(data, x);
};
```

`move` ở đây là closure capture policy, không phải expression move operation.

---

# 66. Async

```ax
async fn fetch(url: String) -> Result<Data, Error> {
    let response = await http.get(url)?;
    response
}
```

Hoặc:

```ax
let data = fetch(url).await?;
```

Khuyến nghị surface syntax:

```text
expression.await
```

thay vì:

```text
await expression
```

để parser và precedence dễ quản lý.

---

# 67. Generic async

```ax
async fn load<T: Decode>(source: T) -> Result<Data, Error> {
    ...
}
```

Future type vẫn compiler-generated.

---

# 68. Match guard

Có thể hỗ trợ:

```ax
match x {
    n if n > 10 => large(n),
    n => small(n),
}
```

Guard được đánh giá sau pattern binding.

---

# 69. Range syntax

```ax
0..10
0..=10
..10
10..
..
```

Semantics phụ thuộc context.

Không overload range syntax thành unrelated operation.

---

# 70. Index syntax

```ax
array[i]
```

compiler resolves indexing protocol.

Unchecked access phải explicit unsafe/system API, ví dụ conceptually:

```ax
unsafe { array.get_unchecked(i) }
```

---

# 71. Operator overloading

Operator mapping qua traits:

```text
a + b
```

→ semantic operator trait resolution.

Nhưng:

```text
&&
||
```

không phải ordinary overload vì short-circuit semantics là compiler-defined.

---

# 72. Precedence

Axiom cần precedence cố định:

```text
highest
────────────────
postfix / call / index
unary
*
/
%
+
-
<< >>
< <= > >=
== !=
&
^
|
&&
||
..
..=
as
?
assignment
lowest
```

`as` và `?` cần được parser xử lý bằng grammar rõ ràng thay vì heuristic.

---

# 73. Call precedence

```ax
foo(a + b).bar()[i]
```

được parse:

```text
(((foo(a + b)).bar())[i])
```

Deterministic.

---

# 74. Blocks

Block:

```ax
{
    statement;
    expression
}
```

Block có thể là expression.

Ví dụ:

```ax
let x = {
    let a = 10;
    a * 2
};
```

---

# 75. Statement vs expression

Axiom cố tình giảm distinction.

Các expression:

```text
literal
path
call
method call
struct literal
array
tuple
if
match
loop
closure
comptime
unsafe
block
```

Statements:

```text
let
var
assignment
expression statement
return
break
continue
```

---

# 76. Expression statement

```ax
foo();
```

Nếu expression trả value nhưng value không dùng được:

compiler có thể cảnh báo nếu `#[must_use]`/`@must_use` contract.

---

# 77. No implicit discard for must-use

Ví dụ:

```ax
File.open(path);
```

nếu `Result<File, Error>` được `@must_use`:

```text
warning/error theo policy
```

Không silently discard.

---

# 78. Grammar formalization

Parser specification nên dùng EBNF-like notation:

```text
FunctionDecl :=
    Visibility? Attribute* "fn" Identifier
    GenericParams?
    "(" Parameters? ")"
    ReturnType?
    WhereClause?
    Block
```

Struct:

```text
StructDecl :=
    Visibility? Attribute*
    "struct" Identifier
    GenericParams?
    StructBody
```

---

# 79. Parser architecture

Không dùng parser magic tùy ý.

Pipeline:

```text
UTF-8
 ↓
Unicode validation
 ↓
Lexer
 ↓
Token stream
 ↓
Concrete Syntax Tree
 ↓
Parser
 ↓
AST
 ↓
Name resolution
```

---

# 80. CST và AST

Khuyến nghị giữ CST đủ thông tin để formatter/IDE:

```text
comments
whitespace
source spans
token identity
```

AST semantic có thể bỏ:

```text
parentheses
irrelevant whitespace
comments
```

trừ khi tooling cần SourceMap.

---

# 81. Error recovery

Parser không được dừng ở lỗi đầu tiên.

Ví dụ:

```ax
fn foo( {
let x =
struct Bar {
```

IDE mode cố gắng tạo partial CST/AST.

Compiler batch mode vẫn trả structured diagnostics.

---

# 82. Parser ambiguity policy

Không được resolve ambiguity bằng:

```text
"compiler đoán programmer muốn gì"
```

Nếu grammar cho phép hai parse hợp lệ:

```text
EGRAMMAR_AMBIGUOUS
```

hoặc grammar phải được sửa.

---

# 83. Lexer longest-match

Tokenization dùng deterministic longest-match.

Ví dụ:

```text
<=
>=
==
!=
&&
||
..
..=
+=
-=
```

được nhận diện trước token đơn tương ứng.

---

# 84. Numeric literal typing

Literal integer ban đầu là polymorphic compile-time numeric value trong giới hạn inference.

Ví dụ:

```ax
let x: i32 = 10;
let y: u64 = 10;
```

cùng literal source nhưng được contextualize thành type tương ứng.

Nhưng:

```ax
let x = 10;
```

phải có defaulting rule deterministic.

Khuyến nghị default:

```text
i32
```

nếu không có context.

---

# 85. Float default

```ax
let x = 1.0;
```

default:

```text
f64
```

trừ khi context xác định type khác.

---

# 86. No implicit string-to-anything

```ax
"123"
```

không tự động thành:

```text
integer
StringView
C string
bytes
```

Conversion phải explicit hoặc API-specific.

---

# 87. Type alias

```ax
type UserId = u64;
```

là alias, không tạo nominal type mới.

Do đó:

```text
UserId == u64
```

về type identity.

---

# 88. Newtype

Dùng struct tuple:

```ax
struct UserId(u64);
```

để tạo nominal type.

`UserId` khác `u64`.

Có thể:

```ax
@repr(transparent)
struct UserId(u64);
```

cho ABI-transparent wrapper.

---

# 89. Constructor policy

Không có constructor language primitive.

Struct literal:

```ax
User { id, name }
```

là primitive syntax.

Factory:

```ax
User.new(...)
```

chỉ là associated function.

Điều này giữ struct/function model nhất quán.

---

# 90. No class syntax

Không có:

```ax
class
extends
implements
virtual
protected
```

Core.

Mô hình:

```text
struct
+
impl
+
trait
+
generic
```

---

# 91. Dynamic dispatch syntax

Static:

```ax
fn draw<T: Drawable>(x: T)
```

Dynamic:

```ax
fn draw(x: dyn Drawable)
```

Dynamic dispatch phải được viết rõ.

Không có implicit boxing.

---

# 92. Trait object syntax

```ax
dyn Drawable
```

có thể đứng trong:

```ax
Box<dyn Drawable>
```

hoặc shared ownership type.

Không có hidden `Object`.

---

# 93. Raw pointers

Syntax:

```ax
*const T
*mut T
```

chỉ dành cho unsafe/system/FFI.

Dereference:

```ax
*p
```

field:

```ax
p->field
```

---

# 94. Không có `&T` / `&mut T`

Safe Core không dùng:

```text
&T
&mut T
```

thay vào đó:

```text
view<T>
mut_view<T>
```

Điều này làm ownership/capability semantics explicit hơn nhưng vẫn tránh lifetime syntax.

---

# 95. Explicit view creation

```ax
let v = view(x);
let m = mut_view(x);
```

Implicit conversion chỉ cho ephemeral argument:

```ax
fn read(v: view<Data>)

read(data);
```

Compiler không được âm thầm tạo escaping view.

---

# 96. Drop syntax

Explicit early drop:

```ax
drop(resource);
```

Không:

```text
delete
free
destruct
```

Language không đảm bảo physical deallocation.

---

# 97. Ownership syntax

Move chủ yếu được compiler suy ra:

```ax
let b = a;
```

Nếu `a` non-Copy → move.

Explicit clone:

```ax
let b = a.clone();
```

Không có:

```text
move a
```

trừ khi sau này có tooling annotation; Core v0.1 không cần.

---

# 98. Copy semantics

```ax
let b = a;
```

nếu `a: Copy`:

```text
a remains usable
```

Nếu non-Copy:

```text
a becomes moved
```

Đây là một trong những semantics quan trọng nhất của Axiom.

---

# 99. No implicit conversion chains

Không:

```ax
foo(i32)
```

với `foo(u64)` bằng chuỗi:

```text
i32 → i64 → u64
```

Compiler không tự tìm conversion chain.

---

# 100. AI-oriented syntax invariants

Axiom syntax phải đáp ứng:

### `ASYNTAX-20`
Every syntactically valid source has one parse.

### `ASYNTAX-21`
Parser never resolves semantic ambiguity by heuristic guessing.

### `ASYNTAX-22`
Whitespace is not semantically significant except token separation/literals.

### `ASYNTAX-23`
UTF-8 source is normative.

### `ASYNTAX-24`
Unicode identifiers follow deterministic XID rules.

### `ASYNTAX-25`
Identifier normalization is deterministic.

### `ASYNTAX-26`
Keywords cannot be ordinary identifiers unless explicitly escaped by a future reserved mechanism.

### `ASYNTAX-27`
No implicit semicolon insertion is part of the language semantics.

### `ASYNTAX-28`
Trailing commas are accepted in multiline collection/declaration forms.

### `ASYNTAX-29`
All operator precedence is explicitly specified.

### `ASYNTAX-30`
All operator associativity is explicitly specified.

### `ASYNTAX-31`
Numeric literal typing is deterministic.

### `ASYNTAX-32`
Implicit numeric conversion is prohibited.

### `ASYNTAX-33`
`null` is not part of safe Core syntax.

### `ASYNTAX-34`
Raw pointer syntax is restricted to unsafe/system contexts.

### `ASYNTAX-35`
Safe access syntax uses `view<T>` and `mut_view<T>`.

### `ASYNTAX-36`
Ownership transfer is inferred from type semantics rather than explicit move syntax.

### `ASYNTAX-37`
Clone is explicit.

### `ASYNTAX-38`
Dynamic dispatch is explicit.

### `ASYNTAX-39`
FFI ABI is explicit.

### `ASYNTAX-40`
Attributes are typed compiler metadata.

### `ASYNTAX-41`
Attributes cannot silently introduce arbitrary language semantics.

### `ASYNTAX-42`
Comptime syntax cannot bypass ordinary semantic verification.

### `ASYNTAX-43`
Async syntax does not imply execution or spawning.

### `ASYNTAX-44`
`await` represents suspension, not thread creation.

### `ASYNTAX-45`
`unsafe` explicitly marks machine-level responsibility boundaries.

### `ASYNTAX-46`
No class/inheritance syntax exists in Core v0.1.

### `ASYNTAX-47`
Structs are the primary user-defined aggregate syntax.

### `ASYNTAX-48`
Traits are the primary behavior abstraction syntax.

### `ASYNTAX-49`
Functions are the primary behavior primitive.

### `ASYNTAX-50`
Method syntax is syntactic sugar over function semantics.

### `ASYNTAX-51`
Constructor semantics are not a language primitive.

### `ASYNTAX-52`
Type aliases do not create nominal types.

### `ASYNTAX-53`
Newtypes are nominal types.

### `ASYNTAX-54`
Default layout is never inferred from surface syntax.

### `ASYNTAX-55`
Source syntax must preserve enough source-span information for exact diagnostics.

### `ASYNTAX-56`
The parser must support IDE error recovery without changing batch compiler semantics.

### `ASYNTAX-57`
Grammar changes require conformance-test updates.

---

# 101. Syntax mẫu hoàn chỉnh

Một chương trình Axiom tương đối thực tế:

```ax
package demo;

import std::io::File;
import std::fmt::Display;

struct User {
    id: u64,
    name: String,
}

impl User {
    fn new(id: u64, name: String) -> User {
        User { id, name }
    }

    fn greet(self: view<User>) {
        print("Hello {self.name}");
    }
}

impl Display for User {
    fn display(self: view<User>) -> String {
        "User({self.id}, {self.name})"
    }
}

fn find_user(id: u64) -> Result<User, Error> {
    if id == 0 {
        return Err(Error.InvalidId);
    }

    Ok(User.new(id, "Axiom"))
}

async fn load_user(id: u64) -> Result<User, Error> {
    let user = find_user(id)?;
    await something_async();
    Ok(user)
}

fn main() {
    let user = find_user(42)?;

    user.greet();

    match user.id {
        0 => print("invalid"),
        1..=100 => print("small"),
        _ => print("large"),
    }
}
```

Điểm quan trọng là programmer có thể đọc code này mà không cần biết:

- MIR;
- ownership dataflow;
- capability regions;
- register allocation;
- ABI classification;
- escape analysis;
- coroutine lowering.

Compiler biết những thứ đó, programmer không phải viết chúng.

---

# 102. Grammar architecture cuối cùng

Surface language hiện tại:

```text
                    Axiom Source
                         │
                 ┌───────▼────────┐
                 │ Unicode Lexer  │
                 └───────┬────────┘
                         ↓
                     Tokens
                         ↓
                 ┌───────▼────────┐
                 │     Parser     │
                 └───────┬────────┘
                         ↓
                       CST
                         ↓
                 ┌───────▼────────┐
                 │   AST Builder  │
                 └───────┬────────┘
                         ↓
                        AST
                         ↓
                   Name Resolver
                         ↓
                       HIR
```

Parser **không** chịu trách nhiệm:

- type checking;
- trait resolution;
- ownership;
- capability;
- overload resolution;
- ABI;
- optimization.

Điều này giữ compiler architecture sạch.

---

# 103. Một quyết định quan trọng: syntax không gánh semantics

Ví dụ:

```ax
user.greet();
```

Parser chỉ thấy:

```text
MethodCall(
    receiver = user,
    name = greet
)
```

Nó **không** quyết định:

- `greet` là inherent method;
- trait method;
- extension method;
- generic method;
- receiver là `view<User>`;
- có dynamic dispatch hay không.

Resolver/type checker quyết định sau.

Đây là cách giữ parser cực kỳ ổn định khi Axiom phát triển.

---

# 104. Trạng thái Axiom sau BOOTSTRAP-123

Các tầng lớn hiện đã khóa:

```text
Language semantics       ✓
Memory model             ✓
Ownership                ✓
Capability               ✓
Concurrency              ✓
Async                    ✓
GPU model                ✓
Comptime                 ✓
Type system              ✓
Traits/generics          ✓
Functions/closures       ✓
Error model              ✓
ABI                       ✓
LIR/backend              ✓
Object/linker            ✓
Runtime architecture     ✓
Bootstrap                ✓
Build/package            ✓
Testing/conformance      ✓
Surface syntax           ✓
```

Tức là Axiom hiện không còn chỉ là một tập ý tưởng. Ta đã có **một language architecture tương đối hoàn chỉnh từ source → native binary → validation**.

---

# BOOTSTRAP-124 — Standard Library Implementation Contract

Bước tiếp theo hợp lý không phải thêm một feature ngôn ngữ nữa.

Ta cần khóa **Standard Library thực sự sẽ được xây như thế nào**, bởi đây là nơi rất dễ làm hỏng những mục tiêu đã đặt ra:

```text
Axiom Core
     ↓
stdlib
     ↓
runtime components
     ↓
OS
```

Task 124 sẽ quyết định cụ thể:

- `core` package;
- `alloc`;
- `Vec`, `String`, `Box`;
- `Rc`, `Arc`;
- `Option`, `Result`;
- iterator;
- collections;
- text/Unicode;
- filesystem;
- networking;
- threads/sync;
- async;
- time/random;
- math/SIMD;
- serialization;
- crypto;
- logging;
- testing;
- OS;
- GPU/tensor;
- FFI;
- prelude;
- `no_std`-like/freestanding profile;
- **dependency graph của stdlib sao cho một chương trình `print("hello")` không vô tình kéo cả network/Unicode/async/GPU runtime vào binary.**