Tiếp tục theo baseline đã đóng. Bước này là **COMPILER-001 — Lexer / Parser + Axiom v0.1 Syntax**.

Mục tiêu của bước này không phải làm cú pháp “nhiều tính năng”, mà tạo một nền cú pháp **ít quy tắc đặc biệt, dễ parse, dễ viết compiler và đặc biệt dễ để AI sinh code đúng**.

# COMPILER-001 — Lexer / Parser + Syntax v0.1

## 1. Nguyên tắc cú pháp

Tôi đề xuất đóng 7 nguyên tắc:

1. **Không có class/inheritance.**
2. **Không có automatic semicolon insertion (ASI).**
3. **Không có macro textual.**
4. **Không có cú pháp reference/lifetime kiểu Rust.**
5. **Block dùng `{}`.**
6. **Expression là first-class**, `if`, `match`, `loop` có thể trả giá trị.
7. **Cú pháp phải ánh xạ gần 1:1 sang HIR**, tránh parser tạo quá nhiều semantic đặc biệt.

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

```axiom
let x = 10;
let y = 20;

let z = if x < y {
    x + y
} else {
    x - y
};
```

Không có dấu `;` sau expression cuối block vì nó là **giá trị trả về**.

Nếu viết:

```axiom
fn test() -> i32 {
    let x = 10;
    x;
}
```

thì `x;` là statement và block trả `unit`, do đó không phù hợp với `-> i32`.

---

# 2. Source encoding

Axiom source:

```text
UTF-8
```

### BOM

UTF-8 BOM ở đầu file:

```text
EF BB BF
```

được chấp nhận và bỏ qua.

BOM xuất hiện ở vị trí khác → lexer error.

### Invalid UTF-8

Không cố “sửa” source.

```text
AX1001: invalid UTF-8 sequence
```

Compiler phải chỉ chính xác byte offset.

---

# 3. Unicode identifier

Tôi đề xuất **cho phép Unicode identifier**, vì Axiom đã xác định UTF-8 là native.

Ví dụ:

```axiom
let tên = "Axiom";
let điểm = 10;
```

Nhưng identifier phải tuân theo Unicode:

```text
XID_Start
XID_Continue
```

ASCII vẫn là trường hợp phổ biến:

```text
foo
foo2
my_value
```

### Normalization

Không silently normalize identifier.

Compiler yêu cầu identifier ở dạng NFC.

Ví dụ identifier không NFC:

```text
té
```

có thể bị từ chối nếu encoding không canonical.

Lý do: compiler không được biến hai source khác byte thành cùng symbol một cách âm thầm.

Diagnostics:

```text
AX1002: identifier is not NFC normalized
```

Sau này formatter có thể tự sửa.

### Unicode confusable

Không biến confusable thành compile error ở Core.

Ví dụ:

```text
foo
fοο
```

có thể khác nhau.

Thay vào đó:

```text
axiom lint
```

có thể cảnh báo.

Như vậy **language semantics không bị kéo vào security policy**.

---

# 4. Comments

Có hai loại:

```axiom
// comment
```

và:

```axiom
/*
    block comment
*/
```

Tôi đề xuất **nested block comment**.

```axiom
/*
    outer
    /*
        inner
    */
*/
```

Điều này cực kỳ hữu ích khi comment/debug code.

Lexer chỉ cần counter:

```text
depth += 1
depth -= 1
```

Không cần semantic parser.

---

# 5. Whitespace

Whitespace:

```text
space
tab
newline
CR
LF
CRLF
```

đều là separator.

Compiler normalize line ending về logical newline trong source manager.

Không có ý nghĩa indentation.

Ví dụ hai đoạn này giống nhau:

```axiom
if x {
    foo();
}
```

và:

```axiom
if x
{
    foo();
}
```

---

# 6. Semicolon

Đây là quyết định quan trọng.

Tôi đề xuất:

> **Không có automatic semicolon insertion.**

Semicolon dùng để kết thúc statement đơn giản.

```axiom
let x = 10;
var y = 20;

foo();
bar();

return x;
```

Các construct có block **không cần `;`**:

```axiom
if x {
    foo();
}

while x {
    bar();
}

fn foo() {
}

struct Vec2 {
}

enum Result<T, E> {
}

trait Display {
}

impl Display for Foo {
}
```

### Expression statement

```axiom
foo();
x + y;
```

### Block expression

Expression cuối cùng không có `;` là giá trị block:

```axiom
{
    let x = 10;
    x + 1
}
```

Có `;`:

```axiom
{
    let x = 10;
    x + 1;
}
```

→ `unit`.

Đây là quy tắc rất đơn giản nhưng cực kỳ quan trọng cho HIR.

---

# 7. Token categories

Lexer chỉ cần tạo một số nhóm token lớn:

```text
Identifier
Keyword
IntegerLiteral
FloatLiteral
StringLiteral
ByteStringLiteral
CharLiteral
Lifetime?       // KHÔNG CÓ
Operator
Punctuation
EOF
```

Tôi đặc biệt muốn:

> **Không có token lifetime.**

Axiom không expose lifetime syntax.

---

# 8. Keywords v0.1

Danh sách ban đầu:

```text
as
async
await
break
comptime
const
continue
dyn
else
enum
extern
false
fn
for
if
impl
in
let
loop
match
mod
move
mut
pub
return
self
Self
struct
trait
true
type
unsafe
use
var
while
```

Ngoài ra:

```text
where
```

nên được giữ ngay từ v0.1 vì generic constraints gần như chắc chắn cần nó.

---

# 9. Những từ KHÔNG phải keyword

Ví dụ:

```text
i32
u64
f32
f64
usize
String
Vec
Option
Result
Box
Arc
```

không phải keyword.

Primitive types vẫn được resolver/type system nhận biết.

Điều này giúp mở rộng language/library mà không phải biến mọi type thành reserved word.

---

# 10. Punctuation

```text
( )
[ ]
{ }

,
;
:
::

.
..

..=

@

#

?
```

`#` có thể dành cho syntax tương lai, nhưng tôi khuyên **không dùng trong v0.1** ngoài việc lexer nhận diện reserved token nếu cần.

Attributes sử dụng:

```axiom
@repr(C)
@inline
@export("foo")
```

không dùng:

```text
#[repr(C)]
```

Lý do: Axiom không cần sao chép Rust syntax chỉ vì quen mắt.

---

# 11. Operators

### Arithmetic

```text
+
-
*
/
%
```

### Comparison

```text
==
!=
<
<=
>
>=
```

### Logical

```text
&&
||
!
```

### Bitwise

```text
&
|
^
~
<<
>>
```

### Assignment

```text
=
+=
-=
*=
/=
%=
&=
|=
^=
<<=
>>=
```

### Other

```text
->    // return type
=>    // match arm / closure
?
::    // path
.
```

---

# 12. Không dùng `&` cho reference

Đây là một điểm tôi muốn đóng rất rõ.

Axiom **không có**:

```axiom
&T
&mut T
```

như Rust.

`&` chỉ là bitwise AND:

```axiom
a & b
```

Capability syntax:

```axiom
view<T>
mut_view<T>
```

Ví dụ:

```axiom
fn sum(data: view<i32>) -> i32 {
    ...
}
```

và:

```axiom
fn modify(data: mut_view<i32>) {
    ...
}
```

Điều này phù hợp với triết lý đã chốt:

> Programmer nói rõ **quyền truy cập**, không phải lifetime machinery.

---

# 13. Integer literals

Hỗ trợ:

```axiom
123
1_000_000

0xff
0xFF_FF

0b1010_0011

0o755
```

Không có octal kiểu C:

```text
0755
```

→ decimal `755`.

### Suffix

```axiom
10i32
10u64
10usize
10isize
```

Float:

```axiom
1.0
3.14
1e10
1.5e-4

1.0f32
1.0f64
```

Suffix là một phần literal token, lexer không tách thành identifier.

---

# 14. Không có implicit numeric magic ở lexer

Lexer chỉ ghi:

```text
IntegerLiteral("42")
```

Type inference xảy ra sau.

Ví dụ:

```axiom
let x = 42;
```

không phải lexer quyết định `i32`.

Đó là nhiệm vụ của Type System.

---

# 15. String

Tôi đề xuất:

```axiom
"hello"
```

là Unicode text literal.

Byte string:

```axiom
b"hello"
```

Raw string có thể hỗ trợ:

```axiom
r"hello\n"
```

nhưng tôi **không đưa raw-string delimiter phức tạp vào v0.1** kiểu:

```text
r###"..."###
```

Chưa cần thiết.

Escape cơ bản:

```text
\n
\r
\t
\\
\"
\0
\xNN
\u{NNNN}
```

Unicode escape dùng:

```text
\u{1F600}
```

thay vì các dạng giới hạn kiểu `\uXXXX`.

---

# 16. Character literal

Tôi không muốn vội đưa `char` vào frozen primitive types.

Vì vậy trong v0.1:

```axiom
'a'
```

có thể **chưa được hỗ trợ**.

Byte literal:

```axiom
b'a'
```

có thể trả `u8`.

Unicode character manipulation nên thuộc text/Unicode library trước.

Như vậy Core không bị mở rộng primitive type chỉ vì syntax.

---

# 17. Type syntax

Named type:

```axiom
i32
User
foo::Bar
```

Generic:

```axiom
Vec<i32>
Option<String>
Result<T, Error>
```

Tuple:

```axiom
(i32, f64)
```

Array:

```axiom
[i32; 16]
```

View:

```axiom
view<i32>
mut_view<i32>
```

Function type:

```axiom
fn(i32, i32) -> i32
```

Raw pointer:

```axiom
*const u8
*mut u8
```

Dynamic trait:

```axiom
dyn Display
```

Tuple một phần tử phải có comma:

```axiom
(i32,)
```

---

# 18. Generic syntax

```axiom
fn max<T>(a: T, b: T) -> T
where T: Ord
{
    ...
}
```

Struct:

```axiom
struct Vec<T> {
    data: Buffer<T>,
}
```

Impl:

```axiom
impl<T> Vec<T> {
    fn length(self) -> usize {
        ...
    }
}
```

Trait:

```axiom
trait Display {
    fn display(self, out: mut_view<Writer>);
}
```

Trait implementation:

```axiom
impl Display for User {
    fn display(self, out: mut_view<Writer>) {
        ...
    }
}
```

---

# 19. Receiver syntax

Axiom cho phép shorthand:

```axiom
fn length(self) -> usize
```

và:

```axiom
fn push(mut self, value: T)
```

`self` không phải magic object.

Parser/resolver biến nó thành receiver parameter.

Về semantic HIR:

```text
fn length(self: Vec<T>) -> usize
```

hoặc equivalent capability/ownership representation.

Có thể viết explicit:

```axiom
fn length(self: Self) -> usize
```

nhưng shorthand:

```axiom
self
mut self
```

là syntax tiện dụng.

Không có:

```axiom
&self
&mut self
```

---

# 20. Function declaration

Cơ bản:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Không return type:

```axiom
fn hello() {
    print("hello");
}
```

tương đương:

```text
-> unit
```

Generic:

```axiom
fn identity<T>(value: T) -> T {
    value
}
```

Attributes:

```axiom
@inline
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

---

# 21. Async / unsafe

```axiom
async fn fetch(url: String) -> Result<Data, Error> {
    ...
}
```

```axiom
unsafe fn read_register(addr: usize) -> u32 {
    ...
}
```

Có thể kết hợp:

```axiom
unsafe async fn ...
```

Parser cho phép modifier set, nhưng resolver kiểm tra tổ hợp hợp lệ.

---

# 22. Unsafe block

```axiom
unsafe {
    ...
}
```

Không có syntax:

```text
unsafe {
    // compiler turns everything off
}
```

Unsafe chỉ thay đổi **proof responsibility**.

Các kiểm tra type/CFG/IR vẫn tiếp tục.

---

# 23. Attributes

Syntax:

```axiom
@repr(C)
struct Foo {
    ...
}
```

```axiom
@export("foo")
fn foo() {
}
```

```axiom
@entry
fn main() {
}
```

```axiom
@kernel
fn add(...) {
}
```

```axiom
@derive(Debug, Clone)
struct User {
}
```

```axiom
@cfg(target.os == "linux")
fn linux_only() {
}
```

Parser chỉ cần một generic representation:

```text
Attribute {
    name: Path,
    arguments: AttributeArgs,
    span: Span
}
```

Semantic meaning thuộc compiler phase sau.

Đây là điểm rất quan trọng:

> Lexer/parser không được hard-code logic của từng attribute.

---

# 24. `if` là expression

```axiom
let result = if condition {
    10
} else {
    20
};
```

Không có `then`.

`else if` chỉ là nested expression:

```axiom
if a {
    1
} else if b {
    2
} else {
    3
}
```

---

# 25. Loop

```axiom
loop {
    work();

    if done {
        break;
    }
}
```

Có thể trả giá trị:

```axiom
let value = loop {
    if ready {
        break 42;
    }
};
```

`break expr` trả giá trị cho loop expression.

---

# 26. While

```axiom
while condition {
    work();
}
```

---

# 27. For

Vì Axiom có iterator/library abstraction, nên syntax:

```axiom
for item in items {
    process(item);
}
```

được hỗ trợ.

Nhưng parser không biến nó thành semantic iterator call ngay.

AST giữ:

```text
ForExpr {
    pattern
    iterable
    body
}
```

Desugaring xảy ra ở HIR.

Điều này giúp compiler giữ syntax sạch.

---

# 28. Match

```axiom
match value {
    Some(x) => x,
    None => 0,
}
```

Struct pattern:

```axiom
match point {
    Point { x, y } => x + y,
}
```

Tuple:

```axiom
match pair {
    (a, b) => a + b,
}
```

Wildcard:

```axiom
_ => 0,
```

Literal:

```axiom
0 => zero(),
1 => one(),
_ => other(),
```

Range:

```axiom
1..10 => foo(),
```

Inclusive:

```axiom
1..=10 => foo(),
```

Exhaustiveness không thuộc parser.

Parser chỉ tạo pattern AST.

---

# 29. Pattern v0.1

Tối thiểu:

```text
_
identifier
literal
tuple
struct
enum constructor
range
```

Ví dụ:

```axiom
Some(value)
Ok(value)
Err(error)
Point { x, y }
(a, b)
```

Pattern binding mặc định immutable.

Nếu cần mutable binding:

```axiom
mut x
```

---

# 30. Closures

Syntax:

```axiom
|x| x + 1
```

Nhiều parameter:

```axiom
|a, b| a + b
```

Mutable capture semantics do compiler suy luận.

Ví dụ:

```axiom
let factor = 10;

let f = |x| x * factor;
```

Không yêu cầu programmer viết:

```text
move
borrow
lifetime
```

`move` chỉ dùng khi programmer muốn **explicitly force ownership capture**:

```axiom
let f = move |x| x + value;
```

---

# 31. `let` và `var`

Immutable:

```axiom
let x = 10;
```

Mutable:

```axiom
var x = 10;
x = 20;
```

Typed:

```axiom
let x: i32 = 10;
```

Pattern:

```axiom
let Some(value) = result;
```

Việc pattern có exhaustive/irrefutable hay không do semantic checker xử lý.

---

# 32. `const`

```axiom
const MAX_SIZE: usize = 1024;
```

`const` là compile-time value.

Không đồng nghĩa với:

```text
runtime immutable global
```

Runtime global sau này có storage semantics riêng.

---

# 33. `comptime`

Expression/block:

```axiom
const SIZE: usize = comptime {
    size_of<MyStruct>()
};
```

Function:

```axiom
comptime fn make_value() -> usize {
    10 + 20
}
```

Parser chỉ nhận syntax.

Capability sandbox và ACOMP semantics thuộc Comptime phase.

---

# 34. `use` / module

```axiom
use std::io::File;
use std::collections::Vec;
```

Multiple:

```axiom
use std::io::{File, Reader, Writer};
```

Alias:

```axiom
use std::collections::Vec as Vector;
```

Module:

```axiom
pub mod io;
mod internal;
```

Inline module:

```axiom
mod math {
    pub fn add(a: i32, b: i32) -> i32 {
        a + b
    }
}
```

---

# 35. Expression precedence

Đóng precedence từ thấp → cao:

| Priority | Syntax |
|---|---|
| 1 | assignment |
| 2 | `||` |
| 3 | `&&` |
| 4 | `|` |
| 5 | `^` |
| 6 | `&` |
| 7 | `== !=` |
| 8 | `< <= > >=` |
| 9 | `<< >>` |
| 10 | `+ -` |
| 11 | `* / %` |
| 12 | unary `! ~ - +` |
| 13 | cast `as` |
| 14 | postfix `?` |
| 15 | call/index/member |
| 16 | path/primary |

Ví dụ:

```axiom
a + b * c
```

parse thành:

```text
a + (b * c)
```

---

# 36. Call / member / index

```axiom
foo(a, b)
```

```axiom
object.field
```

```axiom
object.method()
```

```axiom
array[index]
```

Chaining:

```axiom
foo(a)
    .bar()
    .value
```

---

# 37. `?`

`?` chỉ là Result/Option control-flow sugar.

```axiom
let file = open(path)?;
let data = file.read()?;
```

Parser tạo:

```text
TryExpr
```

HIR mới desugar thành control flow tương đương.

Không có exception semantics.

---

# 38. Cast

```axiom
let x = value as u64;
```

`as` dành cho semantic conversion.

Không dùng:

```axiom
reinterpret<T>(x)
```

để làm bitcast.

Bit reinterpretation sẽ là intrinsic/API riêng, có safety rules riêng.

---

# 39. Generic turbofish

Cần syntax rõ ràng:

```axiom
foo::<i32>(10);
```

Điều này đặc biệt hữu ích vì:

```text
<
>
```

cũng là comparison.

Parser phải hỗ trợ:

```axiom
foo::<Vec<i32>>();
```

Nested `>>` phải được parser xử lý theo grammar, không yêu cầu lexer tách thành:

```text
>
>
```

Một lexer tốt nhất coi:

```text
>>
```

là một operator token, parser có khả năng split trong generic context.

---

# 40. FFI syntax

Ví dụ:

```axiom
extern "C" {
    fn puts(s: *const u8) -> i32;
}
```

Export:

```axiom
@export("axiom_add")
extern "C" fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Parser giữ:

```text
ExternBlock
ExternFn
AbiName
```

ABI validation thuộc ABI phase.

---

# 41. AST

AST nên **không quá semantic**.

Cấu trúc chính:

```text
SourceFile
 ├── Attributes
 └── Item[]
```

Items:

```text
Function
Struct
Enum
Trait
Impl
TypeAlias
Const
ComptimeFn
Module
Use
ExternBlock
```

Expressions:

```text
Literal
Name
Path
Unary
Binary
Assign
Call
Index
Field
MethodCall
If
Match
Loop
While
For
Block
Closure
Return
Break
Continue
Try
Cast
Tuple
Array
StructInit
```

Patterns:

```text
Wildcard
Binding
Literal
Tuple
Struct
Enum
Range
```

Types:

```text
Named
Generic
Tuple
Array
Slice/View
Function
RawPointer
DynTrait
Never
Unit
```

---

# 42. Source Span là bắt buộc

Mọi AST node phải có:

```text
Span {
    file_id
    start
    end
}
```

Không dùng line/column làm identity chính.

Line/column được tính bởi SourceManager.

Lý do:

- UTF-8
- Unicode
- incremental compilation
- diagnostics
- IDE
- formatter
- debug mapping

đều thuận lợi hơn.

---

# 43. Token nên giữ raw text

Ví dụ:

```text
Token {
    kind
    span
    flags
}
```

Không cần copy toàn bộ string.

Identifier:

```text
Token {
    kind = Identifier,
    span = ...
}
```

Interning/resolution làm sau.

Lexer không nên biết symbol table.

---

# 44. Lexer architecture

```text
SourceManager
      ↓
UTF-8 decoder
      ↓
Lexer
      ↓
TokenStream
      ↓
Parser
      ↓
AST
```

Lexer không gọi resolver.

Parser không gọi type checker.

Đây là boundary rất quan trọng.

---

# 45. Lexer state machine

Không cần lexer generator phức tạp.

Một hand-written lexer là phù hợp.

Các state chính:

```text
Normal
Identifier
Number
String
ByteString
Char
Escape
LineComment
BlockComment
```

Lexer chạy O(n).

Không backtracking toàn source.

---

# 46. Parser

Tôi đề xuất:

### Recursive descent

cho declaration/control-flow:

```text
parse_item()
parse_function()
parse_struct()
parse_enum()
parse_trait()
parse_impl()
parse_statement()
parse_expression()
```

### Pratt parser

cho expression:

```text
parse_expr(min_binding_power)
```

Đây là lựa chọn rất phù hợp với Axiom.

Không cần parser generator.

---

# 47. Parser error recovery

Đừng dừng ở lỗi đầu tiên.

Ví dụ:

```axiom
fn foo() {
    let x = ;
    let y = 20;
}
```

Compiler nên báo:

```text
AX1101 expected expression
```

sau đó synchronize tại:

```text
;
}
```

và tiếp tục parse `let y`.

Synchronization points:

```text
;
}
,
)
]
EOF
```

và declaration keywords.

Mục tiêu:

> Một lần compile nên cho programmer nhiều lỗi độc lập nhất có thể mà không biến thành hàng trăm lỗi rác.

---

# 48. Lexer diagnostics

Đóng namespace:

```text
AX10xx
```

Ví dụ:

```text
AX1001 invalid UTF-8
AX1002 identifier is not NFC normalized
AX1003 unterminated block comment
AX1004 unterminated string
AX1005 invalid escape
AX1006 invalid numeric literal
AX1007 invalid character
```

Parser:

```text
AX11xx
```

Ví dụ:

```text
AX1101 expected expression
AX1102 expected `)`
AX1103 expected `}`
AX1104 expected type
AX1105 expected identifier
AX1106 unexpected token
```

Diagnostics machine-readable:

```json
{
    "code": "AX1102",
    "severity": "error",
    "message": "expected `)`",
    "file": "main.ax",
    "start": 124,
    "end": 125
}
```

---

# 49. Một chương trình Axiom hoàn chỉnh

Ví dụ baseline:

```axiom
@export("add")
extern "C" fn add(a: i32, b: i32) -> i32 {
    a + b
}

struct Vec2 {
    x: f32,
    y: f32,
}

impl Vec2 {
    fn length_sq(self) -> f32 {
        self.x * self.x + self.y * self.y
    }

    fn scale(mut self, factor: f32) {
        self.x *= factor;
        self.y *= factor;
    }
}

fn main() {
    let a = Vec2 {
        x: 3.0,
        y: 4.0,
    };

    let length = a.length_sq();

    if length > 20.0 {
        print("large");
    } else {
        print("small");
    }
}
```

Điều quan trọng là đoạn này không cần:

```text
class
this
new
delete
&
&mut
lifetime
override
virtual
```

nhưng vẫn có:

- aggregate
- methods
- static dispatch
- mutation
- ownership
- ABI
- FFI
- expression
- type inference.

---

# 50. AST → HIR boundary

COMPILER-001 phải kết thúc tại:

```text
Source
  ↓
Tokens
  ↓
AST
```

**Không** để AST trở thành semantic representation lâu dài.

Bước tiếp theo:

```text
AST
 ↓
Name Resolution
 ↓
Desugaring
 ↓
HIR
```

Ví dụ:

```axiom
v.length()
```

AST:

```text
MethodCall(
    receiver = v,
    name = length,
    args = []
)
```

HIR sau method resolution:

```text
Call(
    Function = Vec2::length,
    Args = [v]
)
```

Tương tự:

```axiom
for x in items {
    foo(x);
}
```

có thể biến thành HIR control flow tương ứng.

---

# 51. Những thứ cố tình KHÔNG đưa vào v0.1

Để giữ compiler khỏe:

```text
macro system
procedural macro
operator declaration syntax
custom syntax extensions
lifetime syntax
borrow syntax
class
inheritance
exceptions
defer
implicit conversions
implicit semicolon insertion
runtime reflection syntax
dependent types
HKTs
general metaprogramming
```

Đặc biệt:

> **Không thêm syntax chỉ để giải quyết vấn đề mà compiler có thể tự giải quyết.**

Đây chính là điểm khác biệt quan trọng của Axiom.

---

# 52. Bộ invariant của COMPILER-001

### Lexer

```text
ALEX-20  Source Is UTF-8
ALEX-21  Invalid UTF-8 Is A Diagnostic
ALEX-22  BOM Is Accepted Only At File Start
ALEX-23  Identifiers Follow Unicode XID Rules
ALEX-24  Identifiers Are NFC Normalized
ALEX-25  Lexer Does Not Perform Name Resolution
ALEX-26  Lexer Preserves Source Spans
ALEX-27  Numeric Literal Syntax Is Deterministic
ALEX-28  Comments Have No Semantic Meaning
ALEX-29  Nested Block Comments Are Supported
ALEX-30  Lexer Runs In Linear Time
ALEX-31  Lexer Does Not Perform Type Inference
ALEX-32  Lexer Does Not Perform Desugaring
```

### Parser

```text
APARSE-20  Parser Consumes Tokens Into AST
APARSE-21  Parser Does Not Perform Type Checking
APARSE-22  Parser Does Not Perform Ownership Checking
APARSE-23  Parser Does Not Perform Trait Resolution
APARSE-24  Parser Does Not Perform Comptime Evaluation
APARSE-25  Parser Preserves Source Spans
APARSE-26  Parser Uses Deterministic Grammar
APARSE-27  No Automatic Semicolon Insertion
APARSE-28  Block Expressions Have Explicit Value Semantics
APARSE-29  Parser Supports Error Recovery
APARSE-30  Parser Does Not Require Symbol Table
APARSE-31  Generic Syntax Is Unambiguous
APARSE-32  Attribute Syntax Is Generic
APARSE-33  Syntax Sugar Is Removed Before MIR
APARSE-34  AST Is Not The Semantic Authority
```

---

# 53. Kiến trúc compiler sau COMPILER-001

Sau khi đóng phần này, pipeline chính đã trở nên cụ thể:

```text
UTF-8 Source
     │
     ▼
┌─────────────┐
│   Lexer     │
└──────┬──────┘
       │ Tokens
       ▼
┌─────────────┐
│   Parser    │
│ Pratt + RD  │
└──────┬──────┘
       │ AST
       ▼
┌─────────────┐
│ Name        │
│ Resolution  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ AST→HIR     │
│ Desugar     │
└──────┬──────┘
       │ HIR
       ▼
┌─────────────┐
│ Type System │
│ + Traits    │
└──────┬──────┘
       │ Typed HIR
       ▼
┌─────────────┐
│ Ownership + │
│ Capability  │
└──────┬──────┘
       │
       ▼
      MIR
```

## Một quyết định rất đáng giữ

Tôi đặc biệt khuyến nghị **không làm cú pháp Axiom giống Rust 100%**, dù Axiom có nhiều ý tưởng tương đồng về ownership.

Axiom nên có một triết lý riêng:

> **Rust yêu cầu programmer diễn đạt nhiều thông tin để compiler chứng minh chương trình.  
> Axiom cố gắng để compiler tự suy luận phần lớn thông tin đó, programmer chỉ khai báo semantic boundary khi thật sự cần.**

Vì vậy cú pháp:

```axiom
view<T>
mut_view<T>
Box<T>
Arc<T>
unsafe
async
@kernel
extern
```

là những **boundary có ý nghĩa**, còn lifetime/borrow syntax không xuất hiện.

---

## Bước kế tiếp: COMPILER-002

Sau Lexer/Parser, bước hợp lý nhất là **AST → Resolver → HIR**, chứ chưa nhảy ngay vào Type System.

Ở đó cần đóng rất kỹ:

```text
Name resolution
Module graph
Scopes
Symbol identity
Generic parameters
Type namespace / value namespace
Method namespace
Import resolution
Visibility
Self/Self
Desugaring
HIR design
```

Đặc biệt phải giải quyết một vấn đề nền tảng của Axiom:

```axiom
v.length()
```

làm sao compiler xác định chính xác:

```text
inherent method
→ trait method
→ imported extension
→ generic extension
```

mà vẫn **không cần class/object model** và không tạo runtime overhead. Đây sẽ là phần **COMPILER-002**.