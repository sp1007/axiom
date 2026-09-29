# BOOTSTRAP-217 — Axiom v1.0 Surface Syntax, Grammar & Canonical Language Form

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của 217 là khóa **hình thức mà lập trình viên và AI thực sự viết**, nhưng không để syntax làm thay đổi semantic model đã frozen.

Nguyên tắc trung tâm:

> **Syntax phải đơn giản hơn semantics bên dưới. Compiler chịu phần phức tạp mà programmer không cần viết.**

---

# 217.1. Syntax philosophy

Axiom ưu tiên:

```text
Readable
Predictable
Explicit at boundaries
Compact in ordinary code
Easy to parse
Easy for AI to generate
Easy for compiler to recover
```

Không theo mục tiêu:

```text
ít ký tự nhất
nhiều magic nhất
giống C nhất
giống Rust nhất
```

---

# 217.2. Canonical example

Một chương trình Axiom cơ bản:

```axiom
fn main() {
    let a = 10
    let b = 20
    let c = a + b

    print(c)
}
```

Không cần:

```text
;
&reference
lifetime
new
delete
```

---

# 217.3. Statement terminator

Axiom dùng **newline-sensitive statement termination** ở nơi không gây ambiguity.

Ví dụ:

```axiom
let x = 10
let y = 20
```

Không cần `;`.

` ; ` có thể tồn tại như explicit terminator trong machine-generated hoặc compact syntax, nhưng không phải bắt buộc trong canonical style.

---

# 217.4. Blocks

Block:

```axiom
{
    statement
    statement
}
```

Block là expression khi context yêu cầu value:

```axiom
let x = {
    let a = 10
    let b = 20
    a + b
}
```

Expression cuối block là giá trị.

---

# 217.5. Return

Explicit:

```axiom
return value
```

Implicit final expression:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

---

# 217.6. Function declaration

Canonical:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Không dùng:

```text
function
def
func
```

---

# 217.7. Unit return

```axiom
fn log(message: Str) {
    ...
}
```

tương đương semantic return:

```text
unit
```

---

# 217.8. Parameters

Parameter:

```axiom
name: Type
```

Không dùng:

```text
Type name
```

---

# 217.9. Mutable local

```axiom
let mut count = 0
```

Mutation:

```axiom
count += 1
```

---

# 217.10. Immutable default

```axiom
let x = 10
```

`x` immutable mặc định.

Điều này giúp compiler reasoning đơn giản hơn.

---

# 217.11. Assignment

```axiom
x = value
```

chỉ hợp lệ khi binding/storage capability cho phép mutation.

---

# 217.12. Shadowing

Cho phép:

```axiom
let x = 10
let x = x + 1
```

Đây là binding mới.

Không phải mutation.

---

# 217.13. Struct

```axiom
struct Point {
    x: f32
    y: f32
}
```

Khởi tạo:

```axiom
let p = Point {
    x: 10.0
    y: 20.0
}
```

---

# 217.14. Field access

```axiom
p.x
p.y
```

Compiler tự xử lý place/address/capability.

---

# 217.15. Struct update

Có thể hỗ trợ:

```axiom
let q = Point {
    x: 30.0
    ..p
}
```

Semantic ownership phải được áp dụng bình thường.

Nếu `p` non-Copy, các field được sử dụng phải tuân theo move/partial-move rules.

---

# 217.16. Tuple

```axiom
let p = (10, 20)
```

Access:

```axiom
p.0
p.1
```

Tuple là structural type.

---

# 217.17. Array

```axiom
let values = [1, 2, 3, 4]
```

Fixed-size array:

```text
[T; N]
```

có thể được viết canonical:

```axiom
[4]i32
```

### Quyết định syntax

Axiom dùng:

```axiom
[4]i32
```

cho fixed-size array.

Ví dụ:

```axiom
let pixels: [1024]u8
```

Điều này giúp `[]T` dành cho view/dynamic collection syntax không bị nhầm lẫn.

---

# 217.18. Dynamic collections

Không đưa collection syntax đặc biệt vào Core.

Ví dụ:

```axiom
let values: Vec<i32>
```

---

# 217.19. Generic syntax

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

Multiple constraints:

```axiom
fn process<T: Readable + Send>(value: T) {
    ...
}
```

---

# 217.20. Generic type declaration

```axiom
struct Box<T> {
    value: T
}
```

---

# 217.21. Where clauses

Để tránh function quá dài:

```axiom
fn process<T>(value: T) -> Result<()> 
where
    T: Send + Clone
{
    ...
}
```

`where` là canonical cho constraint phức tạp.

---

# 217.22. Type aliases

```axiom
type UserId = u64
```

Đây là alias, không tạo nominal type mới.

---

# 217.23. Newtype

Dùng tuple struct:

```axiom
struct UserId(u64)
```

`UserId` là type riêng.

---

# 217.24. Enum

```axiom
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

---

# 217.25. Enum variant

```axiom
Result::Ok(value)
```

Pattern:

```axiom
match result {
    Result::Ok(value) => use(value)
    Result::Err(error) => handle(error)
}
```

---

# 217.26. Option

```axiom
enum Option<T> {
    Some(T)
    None
}
```

Không có `null` trong safe Core.

---

# 217.27. Match

```axiom
match value {
    0 => zero()
    1 => one()
    _ => other()
}
```

`match` phải exhaustive.

---

# 217.28. If

```axiom
if condition {
    ...
} else {
    ...
}
```

`if` là expression:

```axiom
let result = if condition {
    10
} else {
    20
}
```

Hai nhánh phải có compatible type.

---

# 217.29. Else-if

```axiom
if a {
    ...
} else if b {
    ...
} else {
    ...
}
```

---

# 217.30. Loop

Infinite loop:

```axiom
loop {
    ...
}
```

---

# 217.31. While

```axiom
while condition {
    ...
}
```

---

# 217.32. For

Iterator-based:

```axiom
for item in items {
    process(item)
}
```

Không phải primitive pointer iteration.

---

# 217.33. Range

```axiom
for i in 0..10 {
    ...
}
```

Inclusive:

```axiom
for i in 0..=10 {
    ...
}
```

Range semantics đã frozen ở BOOTSTRAP-167.

---

# 217.34. Break

```axiom
break
```

Có value:

```axiom
let result = loop {
    if ready {
        break value
    }
}
```

---

# 217.35. Continue

```axiom
continue
```

---

# 217.36. Functions as values

Function pointer:

```axiom
let f: fn(i32) -> i32 = square
```

---

# 217.37. Closure

Canonical:

```axiom
let add = |x| x + offset
```

Multiple parameters:

```axiom
let add = |a, b| a + b
```

Typed:

```axiom
let add = |a: i32, b: i32| -> i32 {
    a + b
}
```

Capture mode do compiler inference.

---

# 217.38. Closure capture

Programmer không phải viết:

```text
move
borrow
lifetime
```

để capture thông thường.

Compiler xác định:

```text
Copy
Read capability
Mutable capability
Move ownership
```

dựa trên usage.

Nếu không thể chứng minh, compiler báo lỗi có explanation.

---

# 217.39. Methods

Định nghĩa:

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: Vec2) -> f32 {
    sqrt(self.x * self.x + self.y * self.y)
}
```

Call:

```axiom
v.length()
```

là syntax sugar cho:

```axiom
length(v)
```

---

# 217.40. Mutable method

```axiom
fn normalize(self: mut_view<Vec2>) {
    ...
}
```

Call:

```axiom
v.normalize()
```

Compiler tự tạo mutable capability cần thiết.

---

# 217.41. Read-only method

```axiom
fn length(self: view<Vec2>) -> f32
```

Có thể gọi trên owner thông qua ephemeral view conversion.

---

# 217.42. Owning method

```axiom
fn consume(self: Vec2) -> Result<()> {
    ...
}
```

Call:

```axiom
v.consume()
```

chuyển ownership của `v`.

Sau đó `v` không còn hợp lệ.

---

# 217.43. Trait

```axiom
trait Display {
    fn display(self: view<Self>) -> Str
}
```

Implementation:

```axiom
impl Display for Point {
    fn display(self: view<Self>) -> Str {
        ...
    }
}
```

---

# 217.44. Trait default method

```axiom
trait Area {
    fn area(self: view<Self>) -> f32

    fn double_area(self: view<Self>) -> f32 {
        self.area() * 2.0
    }
}
```

Concrete implementation có thể override.

---

# 217.45. Trait inheritance

Trait có thể yêu cầu trait khác:

```axiom
trait Printable: Display + Debug {
    ...
}
```

Đây là **trait constraint composition**, không phải class inheritance.

---

# 217.46. Associated type

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self::Item>
}
```

---

# 217.47. Associated constant

```axiom
trait Numeric {
    const ZERO: Self
}
```

---

# 217.48. Associated function

```axiom
trait Default {
    fn default() -> Self
}
```

---

# 217.49. Dynamic dispatch

Explicit:

```axiom
let shape: dyn Shape = circle
```

Không tự động biến mọi trait value thành dynamic object.

---

# 217.50. `dyn Trait` storage

Dynamic dispatch representation là compiler/library implementation detail trừ khi ABI contract yêu cầu.

Không có mandatory universal object header.

---

# 217.51. Views — syntax

Đây là phần rất quan trọng.

Axiom không dùng:

```text
&T
&mut T
```

Canonical:

```axiom
view<T>
mut_view<T>
```

---

# 217.52. View parameter

```axiom
fn print_point(p: view<Point>) {
    ...
}
```

---

# 217.53. Mutable view parameter

```axiom
fn move_point(p: mut_view<Point>) {
    p.x += 1.0
}
```

---

# 217.54. Ephemeral owner → view

Nếu function yêu cầu:

```axiom
fn length(p: view<Point>) -> f32
```

có thể:

```axiom
length(point)
```

Compiler tự tạo ephemeral capability.

Không tạo alias escape.

---

# 217.55. Explicit stored view

Khi muốn lưu capability:

```axiom
let p = view(point)
```

Đây là explicit vì lifetime/provenance trở thành semantic state.

---

# 217.56. Mutable view không implicit duplicate

```axiom
let a = mut_view(x)
let b = mut_view(x)
```

bị reject nếu overlap.

---

# 217.57. View return

```axiom
fn data(self: view<Buffer>) -> view<u8> {
    ...
}
```

Compiler phải chứng minh returned view vẫn thuộc provenance hợp lệ.

---

# 217.58. No reference operators

Không có safe syntax:

```text
&x
&mut x
*x
```

`&x` không phải cách lấy reference.

Raw address:

```axiom
address_of(x)
```

chỉ ở unsafe/system.

---

# 217.59. Raw pointers

```axiom
*const T
*mut T
```

Ví dụ:

```axiom
unsafe fn read(p: *const i32) -> i32 {
    *p
}
```

Raw dereference chỉ unsafe.

---

# 217.60. Pointer member access

Cho system code:

```axiom
unsafe {
    p->field
}
```

là syntax sugar cho raw dereference + field access.

---

# 217.61. Ownership transfer

```axiom
let b = a
```

Nếu `a` non-Copy → Move.

Không cần:

```text
move(a)
```

---

# 217.62. Explicit clone

```axiom
let b = a.clone()
```

Không có implicit deep clone.

---

# 217.63. Explicit copy

Copy types:

```axiom
let b = a
```

compiler thực hiện semantic Copy.

---

# 217.64. Explicit drop

```axiom
drop(resource)
```

cho phép kết thúc ownership sớm.

---

# 217.65. Error propagation

Canonical:

```axiom
let value = operation()?
```

Nếu lỗi, function return error phù hợp.

---

# 217.66. Result matching

```axiom
match operation() {
    Ok(value) => use(value)
    Err(error) => handle(error)
}
```

---

# 217.67. Panic

```axiom
panic("invalid state")
```

Panic không phải exception.

---

# 217.68. Assertions

```axiom
assert(x >= 0)
```

và:

```axiom
debug_assert(condition)
```

là library/compiler-supported primitives tùy profile.

---

# 217.69. Async

```axiom
async fn fetch(url: Str) -> Result<Data> {
    ...
}
```

Await:

```axiom
let data = fetch(url).await?
```

---

# 217.70. Spawn

`spawn` không thuộc semantic `async fn`.

Library/runtime:

```axiom
spawn(task)
```

Compiler kiểm tra `Send` theo execution contract.

---

# 217.71. Comptime

```axiom
const MAX: usize = 1024
```

Compile-time value.

---

# 217.72. Comptime execution

```axiom
comptime {
    generate_tables()
}
```

---

# 217.73. Comptime function

```axiom
comptime fn make_value() -> i32 {
    42
}
```

---

# 217.74. Compile-time reflection

Conceptual syntax:

```axiom
comptime {
    let fields = reflect(Point).fields()
}
```

Reflection API là compiler-provided capability/library interface.

---

# 217.75. Attributes

Axiom dùng:

```axiom
@attribute(...)
```

Ví dụ:

```axiom
@repr(C)
struct Header {
    ...
}
```

---

# 217.76. Attribute namespaces

Attributes được phân nhóm semantic:

```text
@repr(...)
@abi(...)
@target(...)
@cfg(...)
@derive(...)
@kernel
@unsafe(...)
@constant_time
```

Compiler phải biết attribute nào là normative.

---

# 217.77. Unknown attributes

Unknown attribute không được silently ignored trong production mode.

Compiler:

```text
warning/error
```

tùy namespace/registration.

Điều này tránh typo:

```axiom
@repr(Cc)
```

làm programmer tưởng đã có C ABI.

---

# 217.78. Visibility

Canonical:

```axiom
pub
pub(package)
pub(module)
private
```

Ví dụ:

```axiom
pub fn create() -> Widget
```

---

# 217.79. Modules

```axiom
module graphics::render
```

Import:

```axiom
use graphics::render::Renderer
```

---

# 217.80. Imports

Explicit:

```axiom
use math::sqrt
use collections::Vec
```

Glob import không phải canonical style.

---

# 217.81. Package/module distinction

```text
package
 └── modules
      └── declarations
```

Package không phải module.

---

# 217.82. Operators

Arithmetic:

```text
+ - * / %
```

Comparison:

```text
== != < <= > >=
```

Logical:

```text
&& || !
```

Bitwise:

```text
& | ^ << >>
```

Assignment:

```text
= += -= *= /= %= &= |= ^= <<= >>=
```

---

# 217.83. Short-circuit

`&&` và `||` short-circuit.

Đây là semantic rule, không phải generic operator call thông thường.

---

# 217.84. Operator overloading

Operator mapping qua traits.

Ví dụ:

```axiom
a + b
```

có thể resolve tới trait implementation.

Compiler vẫn giữ short-circuit semantics cho `&&`/`||`.

---

# 217.85. No implicit operator magic

Compiler không tự chọn một overload mơ hồ.

Nếu nhiều candidate hợp lệ:

```text
compile error
```

---

# 217.86. Indexing

```axiom
array[i]
```

Compiler/library resolution có thể dùng indexing protocol.

Bounds safety vẫn được kiểm tra.

---

# 217.87. Slice syntax

Canonical:

```axiom
array[a..b]
```

tạo view/slice theo library/compiler contract.

---

# 217.88. Member call resolution

Thứ tự frozen:

```text
1. Inherent function
2. Trait implementation
3. Imported extension
4. Generic extension
```

Ambiguous → compile error.

---

# 217.89. No implicit method inheritance

Nếu method không tồn tại trên type:

```text
compiler does not search arbitrary unrelated global functions
```

Chỉ extension methods được import/resolve theo rule.

---

# 217.90. Type inference

Axiom cho phép inference:

```axiom
let x = 42
let y = Vec<i32>::new()
```

nhưng không inference theo kiểu heuristic mơ hồ.

---

# 217.91. Numeric literals

```axiom
42
42u64
42i32
3.14
3.14f32
```

Suffix có thể chỉ rõ type.

---

# 217.92. Boolean

```axiom
true
false
```

---

# 217.93. Character

```axiom
'a'
```

là Unicode scalar value.

---

# 217.94. String

```axiom
"Hello"
```

là string literal UTF-8.

Raw strings:

```axiom
r"raw text"
```

---

# 217.95. Bytes

```axiom
b"raw bytes"
```

Không đồng nhất với Unicode String.

---

# 217.96. Escape sequences

Chuẩn hóa:

```text
\n
\r
\t
\\
\"
\u{...}
\x..
```

với validity rules rõ ràng.

---

# 217.97. Comments

Line:

```axiom
// comment
```

Block:

```axiom
/* comment */
```

Doc:

```axiom
/// documentation
```

---

# 217.98. Formatting

Canonical formatter:

```text
ax fmt
```

đảm bảo syntax normalization mà không thay đổi semantics.

---

# 217.99. Lossless syntax

Parser giữ:

```text
comments
whitespace
source spans
tokens
```

trong syntax representation để formatter/IDE/refactoring hoạt động tốt.

---

# 217.100. AI-friendly syntax constraint

Mỗi construct phải có grammar rõ ràng.

Không dùng context-sensitive magic nếu tránh được.

AI có thể sinh:

```text
AST
HIR
```

thông qua compiler API mà không cần tự đoán syntax recovery.

---

# 217.101. Error recovery

Parser có thể tạo:

```text
MissingToken
UnexpectedToken
IncompleteExpression
IncompleteType
IncompletePattern
```

nhưng production compiler không chấp nhận Partial Semantic State.

---

# 217.102. Grammar architecture

Frontend:

```text
Characters
 ↓
Tokens
 ↓
Lossless Syntax Tree
 ↓
AST
 ↓
Name Resolution
 ↓
HIR
```

Syntax tree không phải AST.

---

# 217.103. Lexical identifier

Identifier canonical:

```text
[a-zA-Z_][a-zA-Z0-9_]*
```

và Unicode identifiers có thể được hỗ trợ theo Unicode identifier specification.

Khuyến nghị canonical style vẫn ASCII cho API/compiler symbols.

---

# 217.104. Keywords

Core reserved keywords:

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
false
fn
for
if
impl
in
let
loop
match
module
mut
pub
return
struct
trait
true
type
unsafe
use
while
where
```

Các keyword của future features phải được reserve hoặc contextual hóa cẩn thận để tránh phá compatibility.

---

# 217.105. No keyword explosion

Tên subsystem như:

```text
tensor
gpu
http
sql
crypto
gui
```

không trở thành Core keywords.

Chúng thuộc libraries/platform profiles.

---

# 217.106. Generic parsing ambiguity

Parser không dựa vào semantic type resolution để xác định grammar cơ bản.

Ví dụ `<T>` phải có parse strategy deterministic.

---

# 217.107. Semicolon compatibility

Axiom parser có thể chấp nhận `;` trong compatibility mode:

```axiom
let x = 10;
let y = 20;
```

nhưng formatter canonical hóa về:

```axiom
let x = 10
let y = 20
```

---

# 217.108. Chaining

Cho phép:

```axiom
let result = value
    .map(...)
    .filter(...)
    .collect()
```

Formatter quyết định layout canonical.

---

# 217.109. Pipeline operator

**Không đưa `|>` vào Core v1.0.**

Lý do: method/function syntax hiện tại đã đủ để biểu diễn composition mà không thêm operator semantic mới.

Có thể xem xét ở future proposal nếu có bằng chứng thực tế.

---

# 217.110. Optional chaining

Không có `?.` theo kiểu nullable object.

`?` dành cho Result/Option propagation theo semantics đã định nghĩa.

---

# 217.111. Null coalescing

Không có:

```text
??
```

vì safe Core không có null.

---

# 217.112. Safe navigation

Option được xử lý bằng:

```axiom
match
if let
?
map
and_then
```

theo library/core syntax.

---

# 217.113. `if let`

Pattern binding tiện dụng:

```axiom
if let Some(value) = option {
    use(value)
}
```

---

# 217.114. `while let`

```axiom
while let Some(item) = iterator.next() {
    process(item)
}
```

---

# 217.115. Pattern binding

```axiom
let Point { x, y } = point
```

ownership/capability rules vẫn áp dụng.

---

# 217.116. Ignoring fields

```axiom
let Point { x, .. } = point
```

Compiler vẫn phải theo dõi ownership của các field còn lại.

---

# 217.117. Wildcard

```axiom
_
```

Không tạo binding.

---

# 217.118. Pattern OR

```axiom
match value {
    0 | 1 => small()
    _ => large()
}
```

---

# 217.119. Guard

Có thể:

```axiom
match value {
    x if x > 10 => large()
    _ => small()
}
```

Guard phải được kiểm tra theo exhaustiveness rules.

---

# 217.120. `defer`

**Không đưa `defer` vào Core v1.0.**

Cleanup đã được biểu diễn bằng deterministic Drop.

Nếu cần arbitrary scope-exit action:

```axiom
ScopeGuard
```

là library abstraction.

---

# 217.121. Exceptions

Không có:

```text
try
catch
throw
```

trong Core v1.0.

Recoverable failure:

```axiom
Result<T, E>
```

---

# 217.122. Ownership syntax principle

Programmer chỉ viết:

```axiom
let
let mut
view<T>
mut_view<T>
```

Compiler tự suy luận:

```text
Move
Copy
Drop
Capture
Lifetime
Escape
Alias
Send
Share
```

---

# 217.123. This is the key Axiom UX

Ví dụ:

```axiom
fn process(data: Data) {
    worker(data)
}
```

Compiler tự biết `data` bị move vào `worker`.

Không cần:

```text
move data
'a
'static
&data
&mut data
```

---

# 217.124. Programmer-visible error

Thay vì:

```text
borrowed value does not live long enough
```

Axiom hướng tới:

```text
error AOWN-042:
`data` is used after ownership was transferred to `worker`

transfer:
    worker(data)

later use:
    print(data)

help:
    pass a view if `worker` only needs read access
```

Compiler explanation sử dụng semantic facts.

---

# 217.125. Explicit escape hatch

Nếu programmer thực sự cần machine-level control:

```axiom
unsafe {
    ...
}
```

Không làm safe syntax phức tạp.

---

# 217.126. FFI syntax

```axiom
extern "C" {
    fn malloc(size: usize) -> *mut u8
}
```

FFI declarations phải có contract phù hợp.

---

# 217.127. Export

```axiom
@export("my_function")
pub fn function() {
    ...
}
```

Symbol identity khác semantic declaration identity.

---

# 217.128. Stable ABI

```axiom
@abi(stable)
pub fn api(...) -> ... {
    ...
}
```

Chỉ những declaration/type đáp ứng ABI contract mới hợp lệ.

---

# 217.129. GPU syntax

```axiom
@kernel
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
) {
    ...
}
```

Graphics shader:

```axiom
@compute
fn main(...) {
    ...
}
```

Các annotation này không tạo language riêng.

---

# 217.130. Target configuration

```axiom
@cfg(target.os == "windows")
```

hoặc tương đương canonical compiler condition syntax.

---

# 217.131. Derive

```axiom
@derive(Clone, Debug, Serialize)
struct User {
    ...
}
```

Generated code quay lại semantic pipeline bình thường.

---

# 217.132. No textual code-generation escape

`derive` không được phép âm thầm inject semantics ngoài verifier.

---

# 217.133. Attribute validation

Compiler phải biết:

```text
attribute owner
allowed targets
argument grammar
semantic effect
```

---

# 217.134. Canonical source layout

Khuyến nghị:

```text
module declaration

imports

public declarations

private declarations

implementations

tests
```

Formatter không bắt buộc thứ tự semantic.

---

# 217.135. Grammar formalization

Grammar v1.0 phải được mô tả bằng EBNF-like grammar.

Ví dụ:

```text
function_decl =
    attributes ,
    visibility ,
    "fn" ,
    identifier ,
    generic_params? ,
    "(" ,
    parameter_list? ,
    ")" ,
    return_type? ,
    where_clause? ,
    block ;
```

---

# 217.136. Expression grammar

Conceptual precedence:

```text
assignment
    ↓
logical-or
    ↓
logical-and
    ↓
bitwise
    ↓
equality
    ↓
comparison
    ↓
shift
    ↓
additive
    ↓
multiplicative
    ↓
unary
    ↓
postfix
    ↓
primary
```

---

# 217.137. Precedence must be fixed

Không để parser/compiler implementation tự chọn precedence.

Precedence là language specification.

---

# 217.138. Evaluation order

Parsing precedence không quyết định evaluation order.

Evaluation order được định nghĩa riêng ở semantic layer.

---

# 217.139. Macro ambiguity

Không có macro expansion stage chen giữa:

```text
AST
→
semantic compiler
```

ngoài typed generation/comptime đã quy định.

---

# 217.140. Canonical syntax invariants — `ASYNTAX`

### `ASYNTAX-20`
Axiom shall have one canonical surface syntax.

### `ASYNTAX-21`
Surface syntax shall not redefine semantic rules.

### `ASYNTAX-22`
Statement termination shall be deterministic.

### `ASYNTAX-23`
Blocks shall support expression semantics where specified.

### `ASYNTAX-24`
Function parameter syntax shall use `name: Type`.

### `ASYNTAX-25`
Bindings shall be immutable by default.

### `ASYNTAX-26`
Mutation shall require explicit mutable binding or capability.

### `ASYNTAX-27`
Structs shall be first-class aggregate declarations.

### `ASYNTAX-28`
Classes shall not be required by the language.

### `ASYNTAX-29`
Methods shall be syntactic sugar over functions.

### `ASYNTAX-30`
Trait implementations shall not require object headers.

### `ASYNTAX-31`
Generic constraints shall have deterministic parsing and resolution.

### `ASYNTAX-32`
`view<T>` shall represent read capability.

### `ASYNTAX-33`
`mut_view<T>` shall represent mutable capability.

### `ASYNTAX-34`
Safe Core shall not require general reference syntax.

### `ASYNTAX-35`
Raw pointer syntax shall remain unsafe/system-oriented.

### `ASYNTAX-36`
Ownership transfer shall be inferred from value semantics.

### `ASYNTAX-37`
Copy shall not require explicit syntax for Copy types.

### `ASYNTAX-38`
Clone shall remain explicit.

### `ASYNTAX-39`
Drop shall remain deterministic.

### `ASYNTAX-40`
`match` shall require exhaustive patterns in Complete Semantic Mode.

### `ASYNTAX-41`
Pattern matching shall respect ownership and capability state.

### `ASYNTAX-42`
`?` shall have deterministic Result/Option propagation semantics.

### `ASYNTAX-43`
Safe Core shall not provide implicit null semantics.

### `ASYNTAX-44`
Async and await syntax shall map to Future semantics.

### `ASYNTAX-45`
Comptime syntax shall map to compile-time execution semantics.

### `ASYNTAX-46`
Unsafe syntax shall establish an explicit semantic boundary.

### `ASYNTAX-47`
Attributes shall have explicitly defined semantic ownership.

### `ASYNTAX-48`
Unknown normative attributes shall not be silently ignored.

### `ASYNTAX-49`
FFI syntax shall explicitly identify foreign ABI.

### `ASYNTAX-50`
Stable ABI shall require explicit declaration.

### `ASYNTAX-51`
GPU entry points shall use explicit execution-domain annotations.

### `ASYNTAX-52`
GPU syntax shall not constitute a separate programming language.

### `ASYNTAX-53`
Library concepts shall not become Core keywords without semantic justification.

### `ASYNTAX-54`
Operator precedence shall be normative.

### `ASYNTAX-55`
Evaluation order shall be specified independently of precedence.

### `ASYNTAX-56`
Syntax recovery shall never weaken production semantic verification.

### `ASYNTAX-57`
Lossless source representation shall preserve source fidelity.

### `ASYNTAX-58`
Canonical formatting shall preserve semantics.

### `ASYNTAX-59`
Syntax shall be deterministic for machine parsing.

### `ASYNTAX-60`
Syntax shall be suitable for structured AI code generation.

### `ASYNTAX-61`
AI-generated syntax shall enter the same parser and semantic pipeline.

### `ASYNTAX-62`
The language shall avoid unnecessary context-sensitive grammar.

### `ASYNTAX-63`
General textual macros shall not be required by Core v1.0.

### `ASYNTAX-64`
Typed generation shall re-enter ordinary semantic verification.

### `ASYNTAX-65`
Future syntax shall not silently alter existing syntax meaning.

### `ASYNTAX-66`
Compatibility syntax shall not create semantic ambiguity.

### `ASYNTAX-67`
Every normative syntax construct shall have parser conformance tests.

### `ASYNTAX-68`
Every syntax construct shall have semantic lowering rules.

### `ASYNTAX-69`
Every syntax construct affecting ownership/capability shall have adversarial tests.

### `ASYNTAX-70`
Surface syntax shall remain independent of target machine architecture.

---

# 217.141. Axiom syntax hiện tại đã khá hoàn chỉnh

Một chương trình thực tế có thể trông như:

```axiom
module app

use std::io::print
use std::collections::Vec

struct Point {
    x: f32
    y: f32
}

trait Distance {
    fn distance(self: view<Self>, other: view<Self>) -> f32
}

impl Distance for Point {
    fn distance(self: view<Self>, other: view<Self>) -> f32 {
        let dx = self.x - other.x
        let dy = self.y - other.y
        sqrt(dx * dx + dy * dy)
    }
}

fn main() {
    let a = Point {
        x: 10.0
        y: 20.0
    }

    let b = Point {
        x: 20.0
        y: 30.0
    }

    print(a.distance(b))
}
```

Không có:

```text
class
this
new
delete
&
*
lifetime
borrow annotation
override
GC
```

nhưng compiler vẫn có đủ semantic machinery để tạo machine code hiệu năng cao.

---

# 217.142. Một quyết định quan trọng

Tôi đề xuất **không tiếp tục bổ sung syntax cho từng subsystem**.

Từ đây:

> **Nếu một subsystem mới có thể sử dụng syntax hiện tại + struct/trait/generic/comptime/attribute thì không được tạo syntax Core mới.**

Ví dụ:

```text
Tensor        → library
Database      → library
HTTP          → library
RPC           → library
ECS           → library
Units         → generic/comptime
Serialization → derive/comptime
GUI           → structs/traits/comptime
```

Điều này giữ Axiom có một surface language tương đối nhỏ dù ecosystem rất lớn.

---

# BOOTSTRAP-218 — Axiom Core Specification Implementation Blueprint

**TRẠNG THÁI: NEXT**

Bước tiếp theo nên là bước chuyển từ **“chúng ta đã thiết kế ngôn ngữ”** sang **“compiler phải được code theo thứ tự nào”**.

218 sẽ đóng thành một blueprint thực thi compiler:

```text
Phase 0   Bootstrap environment
Phase 1   Lexer
Phase 2   Lossless parser
Phase 3   AST
Phase 4   Name resolution
Phase 5   Type system
Phase 6   Trait solver
Phase 7   HIR
Phase 8   MIR
Phase 9   Ownership verifier
Phase 10  Capability verifier
Phase 11  Effect verifier
Phase 12  Async lowering
Phase 13  Comptime
Phase 14  Pattern/exhaustiveness
Phase 15  Verified MIR
Phase 16  Reference interpreter
Phase 17  OptIR
Phase 18  ABI lowering
Phase 19  Axiom LIR
Phase 20  Machine backend
Phase 21  Object writer
Phase 22  Linker
Phase 23  Runtime composition
Phase 24  Self-hosting
```

Quan trọng nhất, 218 sẽ xác định **MVP compiler phải làm được gì ở từng phase**, dependency giữa các phase, dữ liệu nào được phép đi qua boundary, test nào phải pass trước khi chuyển phase và **điểm nào có thể dùng LLVM/LLD trong bootstrap nhưng cuối cùng phải thay bằng compiler/linker native của Axiom**.