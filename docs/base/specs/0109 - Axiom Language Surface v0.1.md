Tiếp tục. Bây giờ tôi sẽ **đóng băng Surface Grammar v0.1**, nhưng tôi sẽ không chỉ liệt kê cú pháp. Tôi sẽ dùng nó để kiểm tra xem các quyết định trước đó có tạo ra một ngôn ngữ nhất quán hay không.

# Axiom Language Surface v0.1

## 1. Triết lý cú pháp

Axiom nên có 5 nguyên tắc:

1. **Cú pháp ít nhưng biểu đạt mạnh.**
2. **Semantic boundary phải nhìn thấy được.**
3. **Compiler implementation detail không xuất hiện trong source.**
4. **Không có cú pháp riêng cho những thứ chỉ là compiler optimization.**
5. **Một construct nên có một cách hiểu chính.**

Đặc biệt:

> Không cố làm Axiom “ngắn nhất có thể”.  
> Mục tiêu là **đọc nhanh, hiểu đúng, compiler dễ phân tích**.

---

# 2. Keywords v0.1

Tôi đề xuất bộ keyword ban đầu:

```text
as
async
await
break
const
continue
comptime
else
enum
false
fn
for
if
impl
import
in
let
match
module
pub
return
static
struct
trait
true
type
unsafe
use
var
while
```

Thêm:

```text
extern
where
```

nếu cần trong ABI/generic syntax.

Tổng cộng vẫn khá nhỏ.

---

# 3. Không có các keyword

Không cần:

```text
class
extends
implements
interface
virtual
override
abstract
protected
private
new
delete
this
self-destructor
try
catch
throw
finally
yield
```

Trong đó:

```text
self
```

vẫn cần dưới dạng **special identifier**, nhưng không nhất thiết phải là keyword lexical cứng.

---

# 4. `self`

Trong method:

```axiom
fn length(self: view<Self>) -> usize
```

hoặc:

```axiom
fn move_to(self: mut_view<Self>, x: f32)
```

`self` là parameter name đặc biệt được method-resolution hiểu.

Không có:

```text
this
```

---

# 5. Identifier

Đề xuất:

```text
identifier =
    letter
    { letter | digit | "_" }
```

Unicode identifiers có thể hỗ trợ sau khi compiler bootstrap ổn định.

V0.1 nên ưu tiên:

```text
A-Z
a-z
_
0-9
```

và UTF-8 source vẫn được hỗ trợ cho string/comments.

---

# 6. Naming convention

Không biến naming convention thành semantics.

Compiler không quan tâm:

```text
my_value
MyValue
MY_VALUE
```

Nhưng formatter/style tool có thể đưa ra convention.

---

# 7. Primitive types

```text
bool

i8 i16 i32 i64
u8 u16 u32 u64

isize usize

f32 f64

unit
never
```

Sau này:

```text
i128
u128
```

có thể thêm.

---

# 8. Type syntax

```axiom
i32
Vec<i32>
Option<Text>
Result<File, FileError>
Array<i32, 16>
```

Generic syntax thống nhất:

```text
Type<Arguments>
```

---

# 9. Function syntax

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Không cần:

```text
function
```

---

# 10. Return type

```text
-> Type
```

Ví dụ:

```axiom
fn open(path: Text) -> Result<File, FileError>
```

Nếu không trả value:

```axiom
fn close() {
    ...
}
```

semantic return:

```text
unit
```

---

# 11. Implicit return

Block expression:

```axiom
fn square(x: i32) -> i32 {
    x * x
}
```

Không cần:

```text
return x * x;
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

# 12. `let` và `var`

```axiom
let x = 10
var y = 20
```

`let` immutable.

`var` mutable.

Không có:

```text
mut x
```

để tránh hai cách biểu diễn mutation.

---

# 13. Explicit type annotation

```axiom
let x: i64 = 42
```

Inference:

```axiom
let x = 42
```

Literal mặc định:

```text
integer → i32
float   → f64
```

trừ khi contextual type xác định được.

---

# 14. Assignment

```axiom
var x = 10
x = 20
```

Assignment trả:

```text
unit
```

và **không phải expression value**.

Do đó không có:

```axiom
a = b = c
```

---

# 15. Compound assignment

```axiom
x += y
x -= y
x *= y
x /= y
x %= y
```

Đây là syntax sugar.

---

# 16. Không có `++` / `--`

Không cần:

```text
i++
++i
i--
--i
```

Dùng:

```axiom
i += 1
```

Compiler vẫn tối ưu thành increment machine instruction.

---

# 17. Numeric operators

```text
+
-
*
/
%
```

Bitwise:

```text
&
|
^
~
<<
>>
```

Comparison:

```text
==
!=
<
<=
>
>=
```

Boolean:

```text
!
&&
||
```

---

# 18. Overflow operators

Đã chốt:

```text
+   checked
+%  wrapping
+|  saturating
```

Tương tự:

```text
-   -%   -|
*   *%   *|
```

Điều này rất đẹp vì semantic intent nhìn ngay trong source.

---

# 19. Cast

Chỉ có một syntax:

```axiom
x as i64
```

Ví dụ:

```axiom
let y = x as i64
```

Không có:

```text
cast<T>()
static_cast
reinterpret_cast
```

trong surface language.

---

# 20. Nhưng bit reinterpretation khác numeric cast

Không dùng:

```axiom
x as f32
```

để biểu diễn bit reinterpretation.

Có API/intrinsic:

```axiom
bit_cast::<f32>(x)
```

với constraint representation.

---

# 21. Pointer/address cast

Đặc biệt:

```text
pointer != integer
```

Do đó:

```axiom
p as usize
```

không tự động hợp lệ.

Phải dùng system/unsafe API:

```text
addr_of(p)
ptr_from_addr(...)
```

---

# 22. Struct

```axiom
struct Vec2 {
    x: f32
    y: f32
}
```

Không cần dấu `;` giữa field.

---

# 23. Struct literal

```axiom
let p = Vec2 {
    x: 10.0,
    y: 20.0,
}
```

Trailing comma được phép.

---

# 24. Field shorthand

```axiom
fn make(x: f32, y: f32) -> Vec2 {
    Vec2 {
        x,
        y,
    }
}
```

---

# 25. Field access

```axiom
p.x
p.y
```

---

# 26. Không có constructor syntax

Không:

```text
new Vec2(...)
Vec2(...)
constructor(...)
```

Struct creation là:

```axiom
Vec2 {
    x,
    y,
}
```

Nếu cần invariant:

```axiom
Vec2.create(x, y)
```

chỉ là function/method.

---

# 27. Tuple

```axiom
let p = (10, 20)
```

Access:

```axiom
p.0
p.1
```

Tuple type:

```text
(i32, i32)
```

---

# 28. Unit

```text
()
```

type:

```text
unit
```

Function không trả value thực chất trả unit.

---

# 29. Array

```axiom
let a = [1, 2, 3, 4]
```

Type:

```text
Array<i32, 4>
```

Explicit:

```axiom
let a: Array<i32, 4> = [1, 2, 3, 4]
```

---

# 30. Repeated array

Có thể hỗ trợ:

```axiom
let a = [0; 1024]
```

semantic:

```text
Array<i32, 1024>
```

---

# 31. Indexing

```axiom
a[i]
```

Safe.

Bounds violation:

```text
panic
```

---

# 32. Slice/view syntax

Đây là một phần rất quan trọng:

```axiom
a[1..4]
```

→ `view<T>`

Các dạng:

```text
a[..]
a[..4]
a[1..]
a[1..4]
a[1..=4]
```

---

# 33. View explicit

```axiom
let v = view(a)
```

Mutable:

```axiom
let v = mut_view(a)
```

---

# 34. Tại sao không dùng `&T`?

Đây là chủ ý.

Không:

```text
&T
&mut T
```

vì Axiom không muốn programmer phải suy nghĩ theo mô hình reference/borrow.

Thay:

```text
view<T>
mut_view<T>
```

Ý nghĩa:

```text
view<T>
    read capability

mut_view<T>
    exclusive write capability
```

---

# 35. Ephemeral view

Nếu function:

```axiom
fn sum(a: view<i32>) -> i32
```

caller có thể:

```axiom
sum(array)
```

Compiler tạo ephemeral view.

Không cần:

```axiom
sum(view(array))
```

---

# 36. Nhưng lưu view phải explicit

```axiom
let v = view(array)
```

để compiler và programmer cùng thấy:

> Tôi đang tạo một non-owning capability có thể sống qua expression này.

Mutable:

```axiom
let v = mut_view(array)
```

---

# 37. Function parameter

Ba semantic modes:

```text
T
view<T>
mut_view<T>
```

Ví dụ:

```axiom
fn consume(x: File)
fn inspect(x: view<File>)
fn modify(x: mut_view<File>)
```

Không có:

```text
in
out
inout
borrow
borrow_mut
```

---

# 38. `T` parameter

Nếu `T: Copy`:

```axiom
fn f(x: T)
```

caller có thể copy.

Nếu `T: !Copy`:

```text
move
```

Compiler quản lý.

---

# 39. Method syntax

Function:

```axiom
fn length(self: view<Vec<T>>) -> usize
```

có thể gọi:

```axiom
v.length()
```

Semantically:

```axiom
length(view(v))
```

---

# 40. Không có method declaration riêng

Không cần:

```text
method
```

Tất cả đều:

```text
fn
```

Method syntax chỉ là resolver sugar.

---

# 41. Enum

```axiom
enum Option<T> {
    Some(T),
    None,
}
```

Enum là algebraic data type.

---

# 42. Enum payload

```axiom
enum Message {
    Quit,
    Text(Text),
    Move { x: i32, y: i32 },
}
```

---

# 43. Enum construction

```axiom
Message.Quit
Message.Text("hello")
Message.Move { x: 10, y: 20 }
```

Tôi đề xuất **qualified enum variants**.

Không đưa tất cả variant vào global namespace.

---

# 44. Match

```axiom
match message {
    Message.Quit => ...
    Message.Text(text) => ...
    Message.Move { x, y } => ...
}
```

Exhaustive.

---

# 45. Wildcard

```axiom
match value {
    Some(x) => x
    _ => 0
}
```

---

# 46. `if` là expression

```axiom
let x =
    if condition {
        10
    } else {
        20
    }
```

Hai branch phải compatible type.

---

# 47. `if` không có parentheses bắt buộc

```axiom
if x > 10 {
    ...
}
```

Không:

```text
if (x > 10)
```

dù parentheses vẫn có thể dùng trong expression.

---

# 48. `while`

```axiom
while condition {
    ...
}
```

---

# 49. `for`

```axiom
for x in items {
    ...
}
```

Compiler lower về iterator/range semantics.

---

# 50. Range

```text
0..10
```

→ half-open.

```text
0..=10
```

→ inclusive.

---

# 51. `break`

```axiom
while condition {
    if done {
        break
    }
}
```

Có thể sau này hỗ trợ:

```text
break value
```

nhưng **không cần v0.1**.

---

# 52. `continue`

```axiom
for x in items {
    if skip(x) {
        continue
    }

    process(x)
}
```

---

# 53. `return`

```axiom
return value
```

hoặc:

```axiom
return
```

Cleanup vẫn được compiler thực hiện.

---

# 54. `?`

```axiom
let file = File.open(path)?
```

và:

```axiom
let value = optional()?
```

chỉ hoạt động khi enclosing function có compatible propagation semantics.

---

# 55. Closure

```axiom
let add = |a, b| a + b
```

Typed:

```axiom
let add = |a: i32, b: i32| -> i32 {
    a + b
}
```

---

# 56. Capture inference

```axiom
let x = 10

let f = || x + 1
```

Compiler tự xác định capture.

Nếu chỉ đọc:

```text
READ capture
```

Nếu cần mutation:

```text
MUTABLE capture
```

Nếu ownership cần thiết:

```text
MOVE capture
```

---

# 57. Explicit move closure

```axiom
let f = move || consume(resource)
```

`move` ở đây có semantic ý nghĩa rõ ràng:

> closure lấy ownership của captured values.

---

# 58. Không có capture list syntax

Không cần:

```text
[a, &b, &mut c]
```

Compiler inference xử lý.

---

# 59. Async

```axiom
async fn fetch(url: Text) -> Result<Data, Error> {
    ...
}
```

Call:

```axiom
let data = fetch(url).await?
```

---

# 60. Async không phải thread

Không có:

```text
async spawn = new thread
```

`async` chỉ biểu diễn suspension.

Thread là library/system API.

---

# 61. Unsafe

```axiom
unsafe {
    ...
}
```

hoặc:

```axiom
unsafe fn read_register(addr: addr) -> u32 {
    ...
}
```

---

# 62. Raw pointer syntax

```text
*const T
*mut T
```

Ví dụ:

```axiom
unsafe fn read(p: *const u32) -> u32 {
    *p
}
```

Nhưng raw pointer operations chỉ trong unsafe/system context.

---

# 63. Không có implicit dereference magic

Tôi đề xuất không làm quá nhiều magic như Rust.

Nếu:

```text
view<T>
```

thì field/method resolution có thể tự xử lý semantic access.

Nhưng raw pointer:

```text
*T
```

phải explicit.

---

# 64. Trait

```axiom
trait Display {
    fn display(self: view<Self>) -> Text
}
```

---

# 65. Implementation

```axiom
impl Display for User {
    fn display(self: view<User>) -> Text {
        ...
    }
}
```

---

# 66. Inherent implementation

Không cần `class`.

```axiom
impl Vec2 {
    fn length(self: view<Vec2>) -> f32 {
        ...
    }
}
```

---

# 67. Extension function

```axiom
fn area(self: view<Rectangle>) -> f32 {
    ...
}
```

Nếu module được import, có thể:

```axiom
rect.area()
```

Method resolver vẫn theo rule:

```text
inherent
→ trait
→ imported extension
→ generic extension
```

---

# 68. Generic function

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

---

# 69. Multiple constraints

```axiom
fn process<T: Read + Send>(x: T) {
    ...
}
```

---

# 70. `where`

Khi constraint dài:

```axiom
fn process<T, E>(x: T) -> Result<T, E>
where
    T: Read + Send,
    E: From<ReadError>,
{
    ...
}
```

---

# 71. Associated type

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self.Item>
}
```

---

# 72. Static vs dynamic trait

Static:

```axiom
fn draw<T: Drawable>(x: view<T>) { ... }
```

Dynamic:

```axiom
fn draw(x: view<dyn Drawable>) { ... }
```

`dyn` phải nhìn thấy rõ vì nó có semantic/runtime cost.

---

# 73. `impl Trait`

```axiom
fn make_iterator() -> impl Iterator<Item = i32> {
    ...
}
```

Static.

Không heap bắt buộc.

---

# 74. Module

```axiom
module math.vector
```

---

# 75. Import

Tôi chốt syntax:

```axiom
import math.vector
import math.vector { Vector, dot }
import graphics.opengl as gl
```

---

# 76. Re-export

```axiom
pub use math.vector.Vector
```

---

# 77. Visibility

```axiom
pub fn api() {}

internal fn helper() {}

fn private_helper() {}
```

---

# 78. `type`

Alias:

```axiom
type UserId = u64
```

Newtype:

```axiom
struct UserId(u64)
```

---

# 79. Const

```axiom
const MAX_SIZE: usize = 1024
```

Không có runtime storage identity.

---

# 80. Static

```axiom
static VERSION: Text = "1.0"
```

Có storage identity.

Mutable:

```axiom
static mut COUNTER: Atomic<i64>
```

nhưng mutable global ordinary memory phải chịu concurrency/unsafe rules.

---

# 81. Comptime

```axiom
comptime fn factorial(n: usize) -> usize {
    if n == 0 {
        1
    } else {
        n * factorial(n - 1)
    }
}
```

Có thể:

```axiom
const VALUE = factorial(10)
```

---

# 82. Không có macro syntax

Không:

```text
macro_rules
#[derive]
proc_macro
```

ở v0.1.

Thay bằng:

```text
comptime
reflection
@derive
```

khi cần.

---

# 83. Attributes

Syntax:

```axiom
@repr(C)
struct Foo { ... }

@align(64)
struct CacheLine { ... }

@export("foo")
pub extern "C" fn foo() {}
```

---

# 84. Attribute phải có schema

Không cho:

```axiom
@whatever_magic_do_this
```

mà compiler không biết semantic contract.

Attribute namespace sau này có thể:

```text
@repr
@compiler
@target
@doc
@derive
```

---

# 85. `extern`

```axiom
extern "C" fn malloc(size: usize) -> *mut u8
```

hoặc:

```axiom
extern "C" {
    fn foo(x: i32) -> i32
}
```

V0.1 có thể chọn một syntax duy nhất để parser đơn giản hơn.

Tôi nghiêng về declaration:

```axiom
extern "C" fn foo(x: i32) -> i32
```

---

# 86. Entry point

Hosted:

```axiom
fn main() {
    ...
}
```

Freestanding:

```axiom
@entry
fn kernel_entry(...) -> never {
    ...
}
```

---

# 87. Comments

Line:

```text
// comment
```

Block:

```text
/* comment */
```

Nested block comment nên hỗ trợ.

Điều này giúp generator/formatter dễ hơn.

---

# 88. String literals

```axiom
"hello"
```

→ `Text`.

Bytes:

```axiom
b"hello"
```

→ `Bytes`.

Không implicit:

```text
Text ↔ Bytes
```

---

# 89. Escape

Hỗ trợ thông thường:

```text
\n
\r
\t
\\
\"
\xNN
\u{...}
```

---

# 90. String interpolation

```axiom
"Hello, {name}!"
```

Compiler có thể lower thành builder/format calls.

Không cần macro.

---

# 91. Boolean

```text
true
false
```

Không cho:

```text
if 1 { ... }
```

Boolean không phải integer.

---

# 92. Operator precedence

Tôi đề xuất gần C-family nhưng đơn giản hơn:

```text
highest
    field / call / index
    unary
    * / %
    + -
    << >>
    &
    ^
    |
    == != < <= > >=
    &&
    ||
    range
    assignment
lowest
```

`as` nằm gần unary/postfix theo grammar.

---

# 93. Không có ternary

Không:

```text
condition ? a : b
```

Dùng:

```axiom
if condition { a } else { b }
```

Axiom đã có expression `if`.

---

# 94. Không có comma operator

Dấu `,` chỉ phục vụ:

```text
arguments
tuple
array
struct fields
generic lists
```

Không có comma expression.

---

# 95. Không có pipeline operator trong Core

Không:

```text
x |> f |> g
```

v0.1.

Nếu ecosystem cần, có thể đưa vào library/comptime tooling sau này.

---

# 96. Statement termination

Tôi vẫn đề xuất:

> **Semicolon không bắt buộc.**

Ví dụ:

```axiom
let x = 10
let y = 20

if x < y {
    print(x)
}
```

Compiler dựa vào grammar để nhận biết statement boundary.

---

# 97. Nhưng semicolon vẫn hợp lệ

Để generator dễ sinh code:

```axiom
let x = 10;
let y = 20;
```

Formatter mặc định có thể loại bỏ.

Đây là lựa chọn thực dụng.

---

# 98. Newline không phải semantic tuyệt đối

Ví dụ:

```axiom
let x =
    foo(
        a,
        b
    )
```

không bị cắt ở newline.

Parser dùng token context để quyết định.

---

# 99. Grammar skeleton

Ở mức EBNF khái quát:

```text
Program         ::= { ModuleItem }

ModuleItem      ::= ModuleDecl
                  | ImportDecl
                  | UseDecl
                  | TypeDecl
                  | StructDecl
                  | EnumDecl
                  | TraitDecl
                  | ImplDecl
                  | FunctionDecl
                  | ConstDecl
                  | StaticDecl
                  | ExternDecl

FunctionDecl    ::= Attributes? Visibility?
                     "fn" Identifier GenericParams?
                     "(" Parameters? ")"
                     ReturnType?
                     WhereClause?
                     Block

StructDecl      ::= Attributes? Visibility?
                     "struct" Identifier GenericParams?
                     StructBody

EnumDecl        ::= Attributes? Visibility?
                     "enum" Identifier GenericParams?
                     EnumBody

TraitDecl       ::= Attributes? Visibility?
                     "trait" Identifier GenericParams?
                     TraitBody

ImplDecl        ::= "impl" GenericParams?
                     Type
                     ("for" Type)?
                     WhereClause?
                     ImplBody
```

Đây mới là skeleton; parser implementation sẽ dùng grammar chính thức riêng.

---

# 100. Expression grammar

Khung:

```text
Expr ::= Literal
       | Name
       | Path
       | UnaryExpr
       | BinaryExpr
       | CallExpr
       | MethodCallExpr
       | FieldExpr
       | IndexExpr
       | CastExpr
       | TupleExpr
       | ArrayExpr
       | StructExpr
       | BlockExpr
       | IfExpr
       | MatchExpr
       | ClosureExpr
       | AwaitExpr
       | RangeExpr
```

---

# 101. Một chương trình Axiom thực tế

Đây là test quan trọng:

```axiom
module app

import std.fs { File }
import std.text { Text }

enum AppError {
    File(FileError),
    InvalidInput,
}

struct Config {
    path: Text
}

fn load(config: view<Config>) -> Result<Text, AppError> {
    let file = File.open(config.path)
        .map_err(|e| AppError.File(e))?

    let text = file.read_text()?

    Ok(text)
}

fn main() -> Result<(), AppError> {
    let config = Config {
        path: "config.txt",
    }

    let text = load(config)?
    
    print(text)

    Ok(())
}
```

Tôi thấy syntax này đã khá ổn: không có class, không có constructor/destructor magic, không có lifetime annotation, không có borrow syntax.

---

# 102. Nhưng phát hiện một điểm cần chỉnh

Đoạn:

```axiom
File.open(...)
    .map_err(...)
```

đòi hỏi `Result.map_err`.

Đây là library API, hoàn toàn được.

Nhưng:

```axiom
File.open(config.path)?
```

với `config: view<Config>` và `config.path: Text` cần kiểm tra semantics.

Nếu `Text` là owning value !Copy thì field access từ view **không được move field ra khỏi owner**.

Đây là một ví dụ rất tốt cho việc grammar đã bắt đầu phát hiện semantic edge case.

Phải viết:

```axiom
File.open(config.path.clone())?
```

nếu cần sở hữu Text.

Hoặc API:

```axiom
File.open(view(config.path))?
```

nếu nhận view.

Đây chính là lý do **không nên chỉ hoàn thiện grammar rồi mới nghĩ ownership**.

---

# 103. Quy tắc field access từ `view<T>`

Ta cần đóng băng:

Nếu:

```text
x: view<T>
```

thì:

```text
x.field
```

mặc định tạo:

```text
view<FieldType>
```

nếu field được dùng trong read context.

Không được tạo owning `FieldType`.

Ví dụ:

```axiom
fn foo(x: view<User>) {
    print(x.name)
}
```

Nếu `name: Text`, `print` nhận `view<Text>` thì hợp lệ.

---

# 104. Muốn lấy ownership từ field?

Phải có owner:

```axiom
let user = User { ... }

let name = user.name
```

Nếu `Text: !Copy`, đây là partial move:

```text
user
 ├── name → MOVED
 └── remaining fields → OWNED
```

Đây là semantics đã chốt.

---

# 105. Điều này làm `view` cực kỳ mạnh

`view<T>` không phải “pointer đẹp hơn”.

Nó là:

> **read capability có provenance.**

Do đó:

```axiom
fn print_user(x: view<User>)
```

không thể vô tình lấy ownership.

---

# 106. Một điều chỉnh syntax tôi khuyến nghị

Không nên cho:

```axiom
view<User>
```

và:

```axiom
mut_view<User>
```

là generic type bình thường mà library user có thể implement tùy tiện.

Compiler phải biết đây là **intrinsic capability types**.

Vẫn có thể syntax như type bình thường, nhưng semantic identity compiler-owned.

---

# 107. Tương tự `never`

`never` compiler-known.

`Option`, `Result` có thể là ordinary enums nhưng compiler có knowledge về `?`.

Điều này giữ core nhỏ:

```text
compiler knows protocol
```

nhưng type vẫn có thể inspect/match bình thường.

---

# 108. Syntax boundary đã khá ổn

Ta có:

```text
VALUE
  let / var

DATA
  struct / enum / tuple / array

BEHAVIOR
  fn / impl / trait

ABSTRACTION
  generic / trait / impl Trait / dyn Trait

MEMORY CAPABILITY
  view / mut_view / unsafe / raw pointer

CONTROL FLOW
  if / while / for / match / return / break / continue

FAILURE
  Result / Option / ?

CONCURRENCY
  async / await
  library spawn/thread/channel

META
  const / comptime / attributes

MODULE
  module / import / use / pub / internal
```

Đây là một surface khá nhỏ nhưng đủ mạnh.

---

# 109. Invariants Surface mới

```text
ASURF-02  Syntax Exposes Semantic Boundaries
ASURF-03  Syntax Does Not Expose Compiler Lifetime Machinery
ASURF-04  let Is Immutable By Default
ASURF-05  var Explicitly Enables Mutation
ASURF-06  Assignment Produces Unit
ASURF-07  Arithmetic Overflow Semantics Are Explicit
ASURF-08  Numeric Conversion Is Explicit
ASURF-09  Pointer Conversion Is Explicit And Restricted
ASURF-10  Struct Is The Primary Aggregate Syntax
ASURF-11  Functions Are The Primary Behavior Syntax
ASURF-12  Methods Are Function Call Sugar
ASURF-13  Traits Define Behavioral Contracts
ASURF-14  Classes Are Not A Core Construct
ASURF-15  Inheritance Is Not A Core Construct
ASURF-16  View Types Represent Non-Owning Capabilities
ASURF-17  Mutable Views Represent Exclusive Mutation Capability
ASURF-18  Ownership Does Not Require Source-Level Lifetime Syntax
ASURF-19  if Is An Expression
ASURF-20  match Is Exhaustive
ASURF-21  Range Semantics Are Explicit
ASURF-22  Result And Option Are Value-Level Failure Models
ASURF-23  ? Is Explicit Failure Propagation
ASURF-24  Panic Is Not An Exception Syntax
ASURF-25  Async Is Explicit
ASURF-26  Async Does Not Imply Threads
ASURF-27  Unsafe Boundaries Are Explicit
ASURF-28  Raw Pointer Operations Are Explicit
ASURF-29  Text And Bytes Are Distinct
ASURF-30  String Interpolation Is Compile-Time/Library Lowerable
ASURF-31  Comptime Uses The Normal Type System
ASURF-32  Macros Are Not Core v0.1
ASURF-33  Attributes Have Defined Semantic Schemas
ASURF-34  Imports Are Semantic
ASURF-35  Wildcard Imports Are Not Core v0.1
ASURF-36  Public Visibility Is Explicit
ASURF-37  Linker Export Is Separate From Public Visibility
ASURF-38  Semicolons Are Optional Syntax
ASURF-39  Newline Does Not Artificially Restrict Expressions
ASURF-40  Syntax Is Deterministic
```

---

# 110. Và bây giờ có một bước cực kỳ quan trọng

**Không nên tiếp tục thêm feature.**

Chúng ta đã đi từ:

```text
Memory
→ Ownership
→ Resource
→ Error
→ Concurrency
→ Async
→ GPU
→ FFI
→ Module
→ Syntax
```

Đã đến lúc thực hiện **Consistency Pass**.

Tôi sẽ lấy một tập chương trình đại diện:

```text
01 hello world
02 struct
03 method
04 trait
05 generic
06 Vec
07 view
08 mut_view
09 partial move
10 Drop
11 Result/?
12 async
13 thread
14 channel
15 atomic
16 unsafe pointer
17 FFI C
18 comptime
19 GPU kernel
20 recursive data
21 graph/Handle
22 public package API
```

và với từng chương trình:

```text
Source
 ↓
AST
 ↓
HIR
 ↓
Type checking
 ↓
Ownership/view
 ↓
Concurrency
 ↓
Drop
 ↓
Verified MIR
```

để tìm **semantic contradiction** trước khi đóng băng `AXIOM-SPECIFICATION v0.1`.

Đây là bước tôi cho rằng quan trọng hơn việc thêm bất kỳ feature mới nào lúc này.