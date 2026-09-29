# AXIOM LANGUAGE SPECIFICATION v0.1 — Part I
## Lexical Structure · Grammar · Names · Resolution · Types

Từ đây tôi chuyển từ **design discussion** sang **normative specification**. Các quy tắc dưới đây được xem là yêu cầu của Axiom v0.1, trừ khi một quy tắc sau này được đánh dấu là sửa đổi chính thức.

---

# 1. Specification conventions

Trong đặc tả:

- **MUST** — bắt buộc.
- **MUST NOT** — bị cấm.
- **SHOULD** — khuyến nghị, implementation có thể khác nếu không phá semantics.
- **MAY** — tùy implementation.
- **UNSPECIFIED** — compiler được tự do lựa chọn, nhưng không được tạo observable semantic difference.
- **IMPLEMENTATION-DEFINED** — compiler phải công bố lựa chọn.
- **TARGET-DEFINED** — phụ thuộc target ABI/architecture.

Một implementation conforming phải:

```text
parse đúng
→ resolve đúng
→ type-check đúng
→ ownership/capability-check đúng
→ tạo semantics đúng
```

Optimizer không được thay đổi semantics.

---

# 2. Lexical Structure

## 2.1 Source encoding

Axiom source MUST be UTF-8.

Unicode được hỗ trợ trong:

- comments;
- string/text literals;
- identifiers theo identifier rules.

Compiler MUST xử lý source theo Unicode normalization policy thống nhất.

Để tránh hai identifier nhìn giống nhau nhưng khác semantic identity, v0.1 nên dùng:

> **NFC normalization trước identifier comparison.**

Ví dụ:

```text
café
café
```

nếu sau NFC trở thành cùng chuỗi Unicode thì được coi là cùng identifier.

---

# 3. Whitespace

Whitespace gồm:

```text
space
tab
carriage return
line feed
```

Whitespace không có semantic meaning ngoại trừ việc phân tách lexical tokens khi cần.

Axiom **không dùng indentation để xác định block**.

Ví dụ:

```axiom
if x > 0 {
    foo()
}
```

và:

```axiom
if x > 0
{
foo()
}
```

có cùng semantics.

---

# 4. Comments

Hai loại:

```axiom
// comment
```

và:

```axiom
/*
    comment
*/
```

Block comment được phép **nested**:

```axiom
/*
    outer
    /*
        inner
    */
*/
```

Comments bị loại khỏi semantic program.

---

# 5. Identifier

Identifier thông thường:

```text
identifier_start identifier_continue*
```

Trong đó:

```text
identifier_start
    = Unicode XID_Start hoặc `_`

identifier_continue
    = Unicode XID_Continue hoặc `_`
```

Ví dụ hợp lệ:

```axiom
foo
foo2
_user
用户
điểm
Vector3
```

Tên bắt đầu bằng `_` vẫn là identifier bình thường.

---

# 6. Reserved keywords

v0.1:

```text
as
async
await
break
const
comptime
continue
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
trait
true
type
unsafe
use
var
while
extern
where
```

`self` là **special identifier**, không phải keyword thông thường.

Compiler SHOULD reserve additional future keywords only through a documented edition/version mechanism; v0.1 không nên có một tập "compiler magic keywords" không được công bố.

---

# 7. Names beginning with `_`

Axiom không tự động coi `_foo` là private.

Visibility được xác định bởi:

```axiom
pub
internal
```

hoặc default private.

Do đó:

```axiom
fn _helper() {}
```

vẫn là private chỉ vì `fn` mặc định private, không phải vì `_`.

---

# 8. Numeric literals

Integer:

```text
123
1_000_000
0xff
0b1010
0o755
```

Cho phép `_` giữa các chữ số.

Không được đặt `_` ở vị trí làm literal trở nên mơ hồ.

Floating:

```axiom
3.14
1.0
1e10
1.5e-3
```

v0.1:

```text
f32
f64
```

là floating-point types chính.

---

# 9. Literal typing

Integer literal ban đầu có trạng thái:

```text
UNRESOLVED_INTEGER_LITERAL
```

Type inference cố gắng resolve từ expected type.

Ví dụ:

```axiom
let x: u8 = 10
```

→ literal có type `u8`.

Nhưng:

```axiom
let x = 10
```

nếu không có constraint:

→ default `i32`.

Đây **không phải implicit numeric conversion**.

Ví dụ:

```axiom
let x: u8 = 300
```

→ compile error.

---

# 10. Boolean literals

```axiom
true
false
```

chỉ có type:

```text
bool
```

Không có truthiness.

Do đó:

```axiom
if 1 {
}
```

→ compile error.

Phải:

```axiom
if x != 0 {
}
```

---

# 11. String literals

```axiom
"hello"
```

là Text literal.

```axiom
b"hello"
```

là Bytes literal.

Đây là hai semantic types khác nhau.

Không có implicit:

```text
Text ↔ Bytes
```

conversion.

---

# 12. Escape sequences

String literal hỗ trợ các escape chuẩn:

```text
\n
\r
\t
\\
\"
\0
```

và Unicode escape theo syntax chính thức của compiler.

Invalid escape → compile error.

---

# 13. String interpolation

Ví dụ:

```axiom
"Hello, {name}"
```

được semantic hóa thành một operation tương đương interpolation/formatting.

Nó không tạo một string-template runtime primitive bắt buộc.

Compiler/library MAY lower thành:

```text
append literal
format value
append literal
```

hoặc tối ưu hoàn toàn.

### Rule

**String interpolation MUST preserve ordinary expression semantics of embedded expressions.**

---

# 14. Operators

Các toán tử v0.1:

```text
+
-
*
/
%
+%
-%
*%
+|
-|
*|

&
|
^
~
<<
>>

==
!=
<
<=
>
>=

!
&&
||

=
?
```

Range:

```text
..
..=
```

Member/index:

```text
.
[]
```

Call:

```text
()
```

---

# 15. Assignment

```axiom
x = value
```

assignment có type:

```text
()
```

Ví dụ:

```axiom
let x = 0
var y = 0

y = 10
```

Không cho:

```axiom
let x = (y = 10)
```

để sử dụng assignment như một giá trị khác `()`.

---

# 16. Không có `++` / `--`

v0.1 không có:

```text
x++
++x
x--
--x
```

Dùng:

```axiom
x = x + 1
```

hoặc API/operator phù hợp.

Điều này giảm một nhóm edge case evaluation-order không cần thiết.

---

# 17. Semicolon

`;` là optional statement separator.

Ví dụ cả hai:

```axiom
let x = 10
let y = 20
```

và:

```axiom
let x = 10;
let y = 20;
```

đều hợp lệ.

Nhưng parser MUST không dựa vào newline như một semantic boundary.

---

# 18. Grammar notation

Axiom grammar v0.1 dùng EBNF-like notation.

Ví dụ:

```text
function_decl =
    "fn" identifier "(" parameter_list? ")" return_type? block ;
```

Lexical grammar và syntactic grammar được tách riêng.

---

# 19. Compilation unit

Một source compilation unit có dạng:

```text
source_file =
    module_decl?
    item*
```

`module` declaration nếu xuất hiện phải ở vị trí được grammar cho phép.

Không có hidden declarations từ filename.

---

# 20. Module

```axiom
module math.vector
```

Module là semantic namespace.

File không tự động tạo semantic namespace riêng nếu package/module declaration xác định namespace khác.

---

# 21. Items

Core item forms:

```text
struct
enum
trait
impl
fn
const
static
type
import
use
```

và các attribute/extern forms tương ứng.

---

# 22. Functions

Canonical grammar:

```text
function =
    visibility?
    attributes*
    "fn"
    identifier
    generic_params?
    "(" parameter_list? ")"
    return_type?
    where_clause?
    block
```

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

---

# 23. Function body

Function body là block expression.

```axiom
fn square(x: i32) -> i32 {
    x * x
}
```

Expression cuối block là return value implicit.

Không cần:

```axiom
return x * x
```

trừ khi muốn early return.

---

# 24. Explicit return

```axiom
fn abs(x: i32) -> i32 {
    if x >= 0 {
        return x
    }

    -x
}
```

`return`:

1. kết thúc function;
2. đánh giá expression nếu có;
3. chạy cleanup cần thiết;
4. chuyển ownership của return value;
5. không tiếp tục execution trong function.

---

# 25. Block expression

```axiom
{
    let x = 10
    x + 1
}
```

có type `i32`.

Block không có final expression:

```axiom
{
    let x = 10
}
```

có type:

```text
()
```

---

# 26. `if`

Grammar:

```text
if_expr =
    "if" expression block
    ("else" (if_expr | block))?
```

Ví dụ:

```axiom
let x =
    if condition {
        10
    } else {
        20
    }
```

Hai nhánh phải có compatible type.

---

# 27. `if` không có `else`

Trong statement context:

```axiom
if condition {
    foo()
}
```

hợp lệ và có type `()`.

Trong value context:

```axiom
let x = if condition {
    10
}
```

branch còn lại là `()`, vì vậy expression này chỉ hợp lệ nếu expected type là `()` hoặc semantics tương ứng.

Không tự biến thành `Option`.

---

# 28. `match`

```axiom
match value {
    Pattern => expression
    Pattern => expression
}
```

`match` là expression.

Compiler MUST kiểm tra exhaustiveness.

Ví dụ:

```axiom
enum Result {
    Ok(i32),
    Error(i32)
}
```

thì:

```axiom
match result {
    Result.Ok(x) => x
    Result.Error(e) => 0
}
```

hợp lệ.

---

# 29. Exhaustiveness

Compiler MUST reject:

```axiom
match result {
    Result.Ok(x) => x
}
```

nếu `Result.Error` chưa được xử lý và không có wildcard.

---

# 30. Pattern binding

Pattern không được tự động biến một capability thành ownership.

Ví dụ với:

```axiom
let user = ...
let u = view(user)
```

match trên `u` chỉ tạo:

```text
read capabilities
```

không move owned fields ra khỏi `user`.

Đây là rule quan trọng để pattern matching không phá capability model.

---

# 31. `never`

Type:

```text
never
```

là bottom-like control-flow type.

Expression:

```axiom
panic("fatal")
```

có thể có type `never`.

`never` có thể được dùng ở nơi cần bất kỳ type nào vì expression không normal-return.

Ví dụ:

```axiom
fn get() -> i32 {
    if valid {
        42
    } else {
        panic("invalid")
    }
}
```

---

# 32. Unit

```text
()
```

là value duy nhất của type:

```text
()
```

Function:

```axiom
fn log(x: Text) {
    ...
}
```

tương đương:

```axiom
fn log(x: Text) -> () {
    ...
}
```

---

# 33. Primitive types

Core primitives:

```text
bool

i8
i16
i32
i64

u8
u16
u32
u64

isize
usize

f32
f64

()
never
```

`i128/u128` chưa thuộc v0.1 Core.

Có thể được bổ sung sau mà không cần thay đổi ownership architecture.

---

# 34. `isize` và `usize`

```text
usize
```

có width phù hợp với target pointer width.

Ví dụ:

```text
x86-64 → 64 bit
AArch64 → 64 bit
x86-32 → 32 bit
```

`usize` không đồng nghĩa với:

```text
u64
```

trên mọi target.

---

# 35. No implicit numeric promotion

Không có:

```text
u8 + u64
```

tự động biến `u8` thành `u64`.

Phải explicit:

```axiom
a as u64 + b
```

hoặc type inference phải khiến cả hai operand vốn đã cùng type.

---

# 36. Arithmetic semantics

Operators:

```text
+
-
*
```

là **checked arithmetic**.

Nếu overflow xảy ra trong safe code:

```text
panic/trap
```

tùy panic strategy/runtime profile.

Wrapping:

```text
+%
-%
*%
```

Saturating:

```text
+|
-|
*|
```

Debug và release không được đổi semantics.

---

# 37. Division

Integer division:

```text
/
```

division by zero là runtime failure được định nghĩa.

Không phải undefined behavior trong safe Axiom.

Overflow đặc biệt như signed minimum / `-1` cũng phải có semantics xác định.

---

# 38. Floating point

`f32`/`f64` tuân theo floating-point semantics được target profile định nghĩa.

Compiler không được tự động bật:

```text
fast-math
```

nếu nó làm thay đổi observable floating-point behavior.

Các optimization không thay đổi semantics vẫn được phép.

---

# 39. Arrays

```axiom
Array<T, N>
```

là fixed-size aggregate.

Ví dụ:

```axiom
let a = [1, 2, 3]
```

Compiler suy ra:

```text
Array<i32, 3>
```

Repeated form:

```axiom
let a = [0; 1024]
```

→ `Array<i32, 1024>` nếu literal được resolve thành `i32`.

Array có value semantics.

---

# 40. Array storage

Array không mặc định heap.

Compiler có thể đặt array:

```text
register
stack
inline in struct
static
heap
```

tùy semantics/escape/address observability.

---

# 41. Tuples

```axiom
let p = (10, 20)
```

type:

```text
(i32, i32)
```

Access:

```axiom
p.0
p.1
```

Tuple là value aggregate.

---

# 42. Struct

```axiom
struct Vec2 {
    x: f32
    y: f32
}
```

Struct không có implicit constructor.

Literal:

```axiom
Vec2 {
    x: 10.0,
    y: 20.0
}
```

---

# 43. Struct layout

Mặc định:

```text
UNSPECIFIED
```

Compiler có thể reorder/pack/pad fields.

Nếu cần stable layout:

```axiom
@repr(C)
struct Foo { ... }
```

hoặc representation attribute phù hợp.

---

# 44. Struct không phải class

Struct không có:

```text
object header
virtual table
implicit identity
GC metadata
```

Behavior được định nghĩa bằng function/impl/trait.

---

# 45. Methods

```axiom
impl Vec2 {
    fn length(self: view<Self>) -> f32 {
        ...
    }
}
```

method call:

```axiom
v.length()
```

chỉ là syntax sugar cho function call tương ứng.

Semantics không tạo một loại "method object".

---

# 46. Receiver modes

Đây là rule normative:

```text
self
```

= consume/move receiver.

```text
self: view<Self>
```

= read capability.

```text
self: mut_view<Self>
```

= exclusive write capability.

Không có implicit fourth receiver mode.

---

# 47. Field access

Nếu owner:

```axiom
let user = User(...)
let name = user.name
```

với field non-Copy:

→ ownership move của field.

Nếu:

```axiom
let user_view = view(user)
let name = user_view.name
```

→ tạo read capability.

Không được move field qua view.

---

# 48. Enum

```axiom
enum Message {
    Quit,
    Text(Text),
    Move { x: i32, y: i32 }
}
```

Enum là sum type.

Variant có thể chứa:

- no payload;
- tuple payload;
- named fields.

---

# 49. Enum representation

Mặc định compiler-controlled.

Compiler MAY dùng:

- discriminant;
- niche;
- tagged representation;
- optimized layout.

Nhưng semantics phải giữ nguyên.

---

# 50. `Option<T>`

`Option<T>` là ordinary enum:

```text
None
Some(T)
```

Compiler MAY optimize:

```text
Option<Box<T>>
Option<&raw-pointer-like representation>
```

bằng niche representation.

Optimization không được làm thay đổi semantic layout nếu layout không được public/ABI-constrained.

---

# 51. `Result<T,E>`

Ordinary enum:

```text
Ok(T)
Err(E)
```

Compiler-known cho `?`.

Không có hidden exception object.

---

# 52. Type identity

Các loại sau **không phải cùng một type identity** chỉ vì representation giống:

```axiom
type UserId = u64
```

là alias của `u64`.

Trong khi:

```axiom
struct UserId(u64)
```

là type mới.

Do đó:

```text
type alias
→ same identity

newtype
→ distinct identity
```

---

# 53. Generic type parameters

Ví dụ:

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    ...
}
```

`T` là compile-time type parameter.

Generic semantics không được phụ thuộc vào compiler specialization.

---

# 54. Generic bounds

```axiom
T: Ord + Copy
```

là conjunction:

```text
T implements Ord
AND
T implements Copy
```

Không có implicit trait inference kiểu "có vẻ hợp lý".

---

# 55. Trait

Trait là behavioral contract.

```axiom
trait Display {
    fn display(self: view<Self>) -> Text
}
```

Trait **không phải class**.

Trait không tự tạo:

```text
object header
vtable
heap allocation
```

Static trait use có thể compile thành direct call.

---

# 56. `impl`

```axiom
impl Display for User {
    ...
}
```

là semantic implementation relationship.

Compiler phải đảm bảo coherence.

---

# 57. Coherence

Allowed:

```text
local trait + foreign type
```

hoặc:

```text
foreign trait + local type
```

Không allowed:

```text
foreign trait + foreign type
```

Điều này ngăn hai package cùng định nghĩa những implementation xung đột.

---

# 58. Associated types

Cho phép:

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self.Item>
}
```

Associated type là compile-time relation.

Không phải runtime type field.

---

# 59. Không có GAT/HKT/dependent types

v0.1:

```text
GAT      ✗
HKT      ✗
dependent types ✗
```

Không phải vì compiler không thể làm.

Mà để giữ trait solver finite và predictable.

---

# 60. `impl Trait`

Ví dụ:

```axiom
fn make() -> impl Iterator {
    ...
}
```

nghĩa:

> return một concrete type cụ thể do compiler biết, nhưng API không expose identity của concrete type theo cách thông thường.

Đây là static abstraction.

Không dynamic dispatch.

---

# 61. `dyn Trait`

```axiom
fn print(x: view<dyn Display>) {
    ...
}
```

là dynamic dispatch.

Conceptual representation:

```text
data pointer
+
dispatch pointer
```

Không cần object header.

---

# 62. Object safety

Trait chỉ được dùng dưới:

```text
dyn Trait
```

nếu đáp ứng object-safety rules.

Trait solver/compiler MUST reject trait không object-safe.

Không tự động chuyển thành static dispatch.

---

# 63. Generic specialization

Compiler MAY internally làm:

```text
generic implementation
       ↓
specialized machine code
```

nhưng programmer không được viết specialization rules trong v0.1.

Semantics:

```text
generic program
=
same meaning
```

dù compiler chọn:

```text
generic code sharing
```

hay:

```text
monomorphized code
```

---

# 64. Type inference

Axiom có local type inference.

Ví dụ:

```axiom
let x = 10
let y = x + 20
```

→ `i32`.

Nhưng:

```axiom
let x = foo()
```

nếu `foo` có nhiều generic instantiations và không đủ context:

→ compile error.

Compiler không được đoán dựa trên "khả năng có vẻ hợp lý".

---

# 65. Conversion

Không có implicit conversion graph.

Các loại:

```text
semantic conversion
bit_cast
pointer cast
address cast
```

là khác nhau.

Ví dụ:

```axiom
x as u64
```

= semantic numeric conversion.

```axiom
bit_cast<u32>(x)
```

= reinterpretation của bit representation.

```text
ptr_cast
```

= pointer representation conversion, restricted/unsafe.

---

# 66. `bit_cast`

`bit_cast<T>(x)` chỉ hợp lệ khi compiler chứng minh:

```text
source representation
compatible
destination representation
```

về size/alignment/validity theo contract.

Không phải universal `transmute`.

---

# 67. Raw pointers

```text
*const T
*mut T
```

là machine-level types.

Không thuộc ordinary safe capability model cho đến khi được validate/chuyển thành capability theo unsafe contract.

Pointer arithmetic là unsafe/system-level.

---

# 68. Type checker invariant

Tại cuối Type Checking:

```text
Every expression has exactly one resolved semantic type
```

ngoại lệ:

```text
never
```

có thể participate trong coercion/control-flow typing.

Không còn:

```text
maybe this type
maybe that type
```

sau Type Checking.

---

# 69. Ownership checker invariant

Sau ownership analysis:

```text
Every owning place has a unique semantic ownership state.
Every capability has valid provenance.
Every access has a valid capability/ownership basis.
```

Các trạng thái:

```text
UNINIT
OWNED
PARTIAL
MOVED
DROPPED
```

không được mơ hồ.

---

# 70. Đây là điểm rất quan trọng cho compiler

Pipeline phải đảm bảo:

```text
AST
 ↓
HIR
 ↓
Name Resolution
 ↓
Type Resolution
 ↓
Ownership/Capability
```

sau đó **không quay ngược semantic decision**.

Optimizer chỉ được tối ưu representation.

---

# 71. Part I — Freeze result

Các phần đã được chuẩn hóa:

```text
✓ UTF-8
✓ Unicode identifiers
✓ lexical grammar
✓ keywords
✓ literals
✓ operators
✓ optional semicolons
✓ blocks
✓ if
✓ match
✓ never
✓ unit
✓ arrays
✓ tuples
✓ structs
✓ enums
✓ methods
✓ receiver semantics
✓ traits
✓ impl
✓ generics
✓ associated types
✓ impl Trait
✓ dyn Trait
✓ type identity
✓ numeric conversion
✓ raw pointer boundary
✓ type inference
```

Không có thay đổi kiến trúc so với Semantic Freeze.

---

# 72. Một điểm cần đánh dấu để xử lý ở Part II

Có một chi tiết **chưa nên tự tiện đóng băng trong Part I**:

### Operator overloading

Ta đã thống nhất:

```text
+ - * / % ...
```

có thể resolve qua traits.

Nhưng Part II cần quy định chính xác:

```text
x + y
```

được lowering thành gì?

Ví dụ:

```text
Add.add(x, y)
```

hay intrinsic operator trait khác.

Đồng thời phải giải quyết:

```text
primitive + primitive
user type + user type
mixed numeric types
assignment operators
comparison
indexing
call operator
```

Đây là semantic detail quan trọng, nên tôi sẽ xử lý trong **Part II: Expressions + Operators + Functions + Closures**, thay vì đoán ở đây.

---

# 73. Bước tiếp theo

**AXIOM LANGUAGE SPECIFICATION v0.1 — Part II**

Sẽ chuẩn hóa:

```text
Expressions
Operator resolution
Evaluation order
Calls
Method calls
Indexing
Field access
Ranges
match patterns
Ownership-producing expressions
Move expressions
Copy expressions
Clone
Closures
Capture inference
Function pointers
Generic calls
? propagation
panic
unsafe expressions
```

Đặc biệt tôi sẽ chốt **evaluation order** và **operator semantics** thật chặt, vì đây là hai thứ có thể ảnh hưởng trực tiếp đến:

```text
performance
side effects
ownership
Drop
async
optimizer freedom
```

và sau Part II sẽ chuyển tiếp sang **Part III: Ownership / Capability / Drop**, nơi chúng ta biến toàn bộ memory model hiện tại thành normative specification có thể trực tiếp dùng để viết compiler/verifier.