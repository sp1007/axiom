Tiếp tục với **SYNTAX-001 — Surface Language**.

Mục tiêu ở tầng này không phải làm syntax “lạ”, mà là:

> **Axiom phải có đủ sức mạnh của systems language hiện đại nhưng số lượng quy tắc mà lập trình viên phải nhớ phải thấp.**

Tôi sẽ ưu tiên syntax có **một cách viết chính**, hạn chế các trường hợp có nhiều syntax tương đương.

---

# SYNTAX-001 — Axiom Surface Language

## 1. Tổng thể

Một file Axiom đi theo cấu trúc:

```text
module declaration
imports

types
traits
implementations

constants
functions

tests / comptime items
```

Ví dụ:

```text
module app.main

import std.io
import std.fs.Path

struct User {
    id: u64
    name: String
}

impl User {
    fn greet(self) {
        println("Hello, " + self.name)
    }
}

fn main() -> Result<(), Error> {
    let user = User {
        id: 1,
        name: "Axiom"
    }

    user.greet()

    Ok(())
}
```

Không bắt buộc dấu `;` cuối statement.

Tôi đề xuất **newline/`}` kết thúc statement trong các context rõ ràng**, nhưng vẫn cho phép `;` khi cần phân tách trên cùng dòng.

---

# 2. Không dùng `class`

Axiom chỉ có:

```text
struct
enum
trait
```

Ví dụ:

```text
struct Vec2 {
    x: f32
    y: f32
}
```

Behavior:

```text
impl Vec2 {
    fn length(self) -> f32 {
        sqrt(self.x * self.x + self.y * self.y)
    }
}
```

Không có:

```text
class Vec2
```

Không có:

```text
public class
private class
```

---

# 3. `fn` là primitive behavior duy nhất

Function:

```text
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Return expression cuối cùng là giá trị trả về.

Không cần:

```text
return a + b
```

nhưng `return` vẫn tồn tại cho early return:

```text
fn test(x: i32) -> i32 {
    if x < 0 {
        return 0
    }

    x
}
```

---

# 4. Receiver method

Không tạo một syntax semantics riêng cho method.

```text
impl Vec2 {
    fn length(self) -> f32 {
        ...
    }
}
```

thực chất tương đương:

```text
fn length(self: Vec2) -> f32
```

Call:

```text
v.length()
```

được compiler resolve thành:

```text
length(v)
```

Đây là điểm rất mạnh của thiết kế struct + function.

---

# 5. `self`

Ba trường hợp chính:

```text
self: T
self: view<T>
self: mut_view<T>
```

Nhưng surface syntax nên ngắn:

```text
fn length(self) -> f32
fn inspect(self: view<Self>)
fn normalize(mut self)
```

Tôi đề xuất:

```text
self
view self
mut self
```

là syntax sugar.

Ví dụ:

```text
impl Vec2 {
    fn length(self) -> f32
    fn print(view self)
    fn normalize(mut self)
}
```

Compiler chuyển thành semantic types tương ứng.

---

# 6. Nhưng không để `&self`, `&mut self`

Đây là điểm tôi **không muốn Axiom sao chép Rust**.

Không:

```text
fn foo(&self)
fn foo(&mut self)
```

Thay bằng:

```text
fn foo(view self)
fn foo(mut self)
```

hoặc khi API cần explicit capability:

```text
fn foo(self: view<T>)
fn foo(self: mut_view<T>)
```

Nhìn vào code là biết ngay:

```text
view = đọc
mut = có quyền sửa
```

không cần học ký hiệu reference.

---

# 7. `let` và `var`

Immutable mặc định:

```text
let x = 10
```

Mutable:

```text
var x = 10
x = 20
```

Không:

```text
let mut x
```

Đây là một quyết định ergonomics quan trọng.

---

# 8. Shadowing

Cho phép:

```text
let value = read()
let value = parse(value)
let value = normalize(value)
```

Mỗi declaration tạo binding mới.

Điều này đặc biệt hữu ích với ownership.

Compiler biết:

```text
value₀
  ↓ move
value₁
  ↓ move
value₂
```

không cần programmer đặt tên:

```text
value2
value3
value4
```

---

# 9. Move không cần syntax

Nếu:

```text
let a = create()
let b = a
```

và type không Copy:

```text
a
```

được move sang `b`.

Không cần:

```text
move(a)
```

`move(...)` chỉ cần nếu muốn truyền ownership một cách explicit trong context đặc biệt.

Ví dụ API:

```text
send(move(buffer))
```

có thể tồn tại như syntax/documentation-level signal, nhưng semantics cơ bản vẫn là move.

---

# 10. Copy cũng không cần syntax

Nếu:

```text
let a: Vec2 = ...
let b = a
```

và `Vec2: Copy`:

```text
a
b
```

độc lập.

Không có:

```text
clone(a)
```

cho Copy.

`clone()` chỉ dành cho expensive/semantic duplication.

---

# 11. `view`

Đây là phần cần làm syntax cực đơn giản.

Thông thường:

```text
fn sum(data: view<i32>) -> i32
```

Call:

```text
sum(array)
```

compiler tạo ephemeral view.

Không cần:

```text
sum(&array)
```

---

# 12. Named view

Khi muốn giữ view trong một scope:

```text
let v = view(data)
```

Mutable:

```text
let v = mut_view(data)
```

Sau đó:

```text
process(v)
```

Điều này vẫn giữ nguyên quyết định:

> owner → view implicit chỉ trong ephemeral call.

Không có implicit escaping reference.

---

# 13. Không có `&` trong safe language

Tôi đề xuất:

```text
&
```

không có semantic role như Rust reference.

Nếu muốn địa chỉ machine-level:

```text
unsafe {
    addr = ptr_of(x)
}
```

Raw pointer:

```text
*const T
*mut T
```

chỉ system/unsafe.

Điều này loại bỏ một lượng lớn nhầm lẫn:

```text
&T
&mut T
&&T
&*x
```

---

# 14. Generics

Syntax:

```text
fn max<T>(a: T, b: T) -> T
```

Trait constraint:

```text
fn max<T: Ord>(a: T, b: T) -> T
```

Nhiều constraint:

```text
fn process<T: Readable + Comparable>(x: T)
```

Tôi **không khuyến khích** bắt buộc `where` cho trường hợp đơn giản.

---

# 15. `where` chỉ dành cho constraint phức tạp

Ví dụ:

```text
fn convert<A, B>(x: A) -> B
where
    A: Into<B>
{
    x.into()
}
```

Đây là syntax dễ đọc hơn:

```text
fn convert<A: Into<B>>(x: A) -> B
```

khi constraint phức tạp.

---

# 16. Associated type

```text
trait Iterator {
    type Item

    fn next(mut self) -> Option<Self.Item>
}
```

Implement:

```text
impl Iterator for Numbers {
    type Item = i32

    fn next(mut self) -> Option<i32> {
        ...
    }
}
```

Không cần syntax mới.

---

# 17. Trait inheritance không gọi là inheritance

Ví dụ:

```text
trait Ordered: Comparable {
    ...
}
```

nghĩa là:

```text
Ordered ⇒ Comparable
```

không phải object inheritance.

Không có:

```text
class Child : Parent
```

---

# 18. Override

Theo thiết kế TRAIT-001:

```text
trait Printable {
    fn print(self) {
        ...
    }
}
```

Type:

```text
impl Printable for User {
    fn print(self) {
        ...
    }
}
```

implementation tự động override default method.

Không cần:

```text
override fn print()
```

Tuy nhiên tooling có thể hỗ trợ annotation:

```text
@override
```

để bắt lỗi typo.

Nhưng **không phải semantic requirement**.

---

# 19. Enum

Algebraic data type:

```text
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

Option:

```text
enum Option<T> {
    Some(T)
    None
}
```

User enum:

```text
enum Shape {
    Point(Vec2)
    Circle {
        center: Vec2
        radius: f32
    }
    Rectangle {
        min: Vec2
        max: Vec2
    }
}
```

---

# 20. `match`

```text
match shape {
    Point(p) => draw_point(p)

    Circle { center, radius } =>
        draw_circle(center, radius)

    Rectangle { min, max } =>
        draw_rect(min, max)
}
```

Exhaustiveness bắt buộc.

Không có implicit fallthrough.

---

# 21. `if` là expression

```text
let x = if condition {
    10
} else {
    20
}
```

Không cần ternary operator:

```text
condition ? 10 : 20
```

Tôi đề xuất **không có ternary**.

Một cách viết duy nhất tốt hơn.

---

# 22. `match` thay thế switch

Không cần:

```text
switch
case
break
fallthrough
```

`match` xử lý cả:

- enum;
- integer;
- tuple;
- struct;
- ranges;
- guards.

Ví dụ:

```text
match code {
    0 => "ok"
    1..=10 => "small"
    _ => "other"
}
```

---

# 23. Pattern binding

```text
if let Some(user) = find_user(id) {
    user.greet()
}
```

Tôi đề xuất có `if let`.

Nó tránh:

```text
match result {
    Some(x) => ...
    None => {}
}
```

cho trường hợp chỉ quan tâm một branch.

---

# 24. `while let`

```text
while let Some(x) = iterator.next() {
    process(x)
}
```

Đây là syntax hợp lý vì nó vẫn là cùng một pattern system.

---

# 25. `for`

Không nên có nhiều kiểu `for`.

Chỉ:

```text
for x in collection {
    ...
}
```

Compiler gọi iterator protocol.

Range:

```text
for i in 0..10 {
    ...
}
```

Inclusive:

```text
for i in 0..=10 {
    ...
}
```

---

# 26. `loop`

```text
loop {
    ...
}
```

break:

```text
break
```

continue:

```text
continue
```

Có thể trả value:

```text
let result = loop {
    if done {
        break value
    }
}
```

---

# 27. Closures

Syntax:

```text
let add = |a, b| a + b
```

Block:

```text
let process = |x| {
    let y = transform(x)
    y * 2
}
```

Type inference.

Không cần khai báo capture list trong trường hợp bình thường.

Compiler tự xác định:

```text
capture by value
capture by read capability
capture by mutable capability
```

---

# 28. Explicit move closure

Khi cần capture ownership:

```text
let task = move |data| {
    process(data)
}
```

`move` ở đây có ý nghĩa rõ:

> capture ownership vào closure.

Đây là một trong số ít trường hợp nên có keyword `move`.

---

# 29. Operator overloading

Operator không được phép tùy ý định nghĩa semantics control flow.

Có thể:

```text
a + b
a == b
a < b
```

thông qua traits.

Ví dụ:

```text
trait Add<Rhs> {
    type Output

    fn add(self, rhs: Rhs) -> Self.Output
}
```

Nhưng không cho:

```text
custom && 
custom ||
custom ?
custom match
```

vì những operator này có control-flow semantics.

---

# 30. Assignment không overload

Không:

```text
a = b
```

là một trait call.

Assignment là language semantic operation.

Điều này giúp compiler ownership analysis dễ và deterministic.

---

# 31. Indexing

Có thể overload:

```text
array[i]
```

nhưng semantics nên chia:

```text
index
index_mut
```

và bounds checking thuộc container/type.

Compiler có thể loại bỏ bounds check khi chứng minh được.

---

# 32. Module

Ví dụ:

```text
module graphics.math
```

Import:

```text
import graphics.math.Vec2
```

hoặc:

```text
import graphics.math.*
```

Tôi khuyên **không dùng `use`**, vì `import` trực quan hơn.

---

# 33. Visibility

Chỉ cần:

```text
pub
```

và mặc định private.

```text
pub struct User {
    id: u64
    pub name: String
}
```

Không cần:

```text
public
protected
private
internal
```

---

# 34. Import alias

```text
import graphics.math.Vec2 as Vector
```

Không cần nhiều syntax alias khác.

---

# 35. Constants

```text
const MAX_SIZE: usize = 1024
```

Compile-time constant.

Comptime:

```text
comptime {
    ...
}
```

là compile-time execution.

Không trộn hai khái niệm.

---

# 36. Attributes

Một hệ thống attribute duy nhất:

```text
@repr(C)
@inline
@noinline
@cold
@align(64)
@packed
@kernel
@cfg(target_os = "linux")
```

Không nên có nhiều cơ chế:

```text
#[...]
[[...]]
__attribute__((...))
```

Axiom chỉ có:

```text
@attribute(...)
```

---

# 37. Unsafe

Block:

```text
unsafe {
    ...
}
```

Function:

```text
unsafe fn read_register(addr: usize) -> u32 {
    ...
}
```

Call:

```text
unsafe {
    read_register(addr)
}
```

Không có `unsafe` lan truyền vô hạn.

Chỉ operation cần unsafe mới yêu cầu boundary.

---

# 38. Async

Syntax:

```text
async fn load() -> Result<Data, Error> {
    let data = await read()
    data
}
```

Tôi đề xuất:

```text
await expression
```

thay vì:

```text
expression.await
```

Lý do: `await` là control-flow operation, không phải method.

Ví dụ:

```text
let x = await future
```

rất rõ.

---

# 39. Spawn

Không đưa scheduler vào syntax.

Library API:

```text
spawn(async_task())
```

hoặc:

```text
Thread.spawn(|| work())
```

`spawn` chỉ là library/runtime abstraction.

---

# 40. `defer` — chính thức loại khỏi Core

Sau khi xem toàn bộ model:

> **Axiom Core không có `defer`.**

Resource:

```text
let file = File.open(...)
```

Cleanup:

```text
Drop
```

Temporary action:

```text
let guard = ...
```

Cleanup logic:

```text
impl Drop for Guard
```

Nếu cần rollback/commit:

```text
transaction.commit()?
```

sau đó Drop chỉ đóng resource.

---

# 41. `try`

Cũng **không có `try/catch` trong Core**.

Chỉ:

```text
?
```

cho `Result`/`Option` propagation.

Ví dụ:

```text
let user = find_user(id)?
```

Với `Option`:

```text
fn get_name(id: Id) -> Option<String> {
    let user = find_user(id)?
    Some(user.name)
}
```

`?` có thể hoạt động với các type triển khai protocol phù hợp, nhưng Core v1 nên giới hạn rõ để tránh biến nó thành operator ma thuật.

---

# 42. Error propagation protocol

Tôi đề xuất trait/compiler protocol:

```text
trait Try {
    type Value
    type Residual

    fn branch(self) -> ControlFlow<Self.Value, Self.Residual>
    ...
}
```

**nhưng không expose đầy đủ trong v1.**

Thay vào đó compiler có semantic intrinsic cho:

```text
Result
Option
```

Sau khi language ổn định mới cân nhắc generalized `Try`.

Lý do: `?` là syntax nhỏ nhưng compiler semantics khá sâu.

---

# 43. Destructuring

Struct:

```text
let User { id, name } = user
```

Tuple:

```text
let (x, y) = point
```

Enum:

```text
let Some(value) = option
```

Array:

```text
let [a, b, ..rest] = values
```

Pattern system thống nhất với `match`.

---

# 44. Field shorthand

```text
let id = 10
let name = "Axiom"

let user = User {
    id,
    name
}
```

Không cần:

```text
User {
    id: id,
    name: name
}
```

---

# 45. Struct update

Có thể:

```text
let user2 = User {
    name: "Bob",
    ..user
}
```

Semantics ownership rõ:

- Copy field → copy;
- owning field → move;
- moved field không được dùng lại.

---

# 46. Constructor

**Không có constructor đặc biệt trong Core.**

Không:

```text
constructor()
new()
init()
```

Struct literal:

```text
User {
    id: 1,
    name: "A"
}
```

Function factory nếu cần:

```text
fn User.create(...) -> Result<User, Error>
```

Method:

```text
impl User {
    fn create(...) -> Result<Self, Error> {
        ...
    }
}
```

Điều này loại bỏ một khái niệm language khác.

---

# 47. `Self`

Cho phép:

```text
impl User {
    fn create(...) -> Self
}
```

`Self` chỉ là type alias ngữ cảnh.

---

# 48. Không có implicit `this`

Không:

```text
this.name
```

Chỉ:

```text
self.name
```

và `self` phải xuất hiện trong signature nếu method cần receiver.

---

# 49. Không có implicit constructor allocation

Đặc biệt:

```text
User { ... }
```

không có nghĩa:

```text
heap allocation
```

Nó chỉ tạo value.

Muốn dynamic storage:

```text
Box.new(User { ... })
```

và ngay cả `Box` cũng là semantic owned dynamic storage, compiler vẫn có thể eliminate allocation nếu storage identity không observable.

---

# 50. Syntax philosophy cuối cùng

Axiom nên cố giữ bộ từ khóa nhỏ:

```text
module
import
pub

struct
enum
trait
impl
type

fn
let
var
const
comptime

if
else
match
for
while
loop
break
continue
return

async
await

unsafe

true
false

as
in

self
Self
move
```

Không:

```text
class
interface
extends
implements
virtual
override
public
private
protected
new
delete
try
catch
throw
finally
defer
```

Một số từ có thể tồn tại trong tooling/attribute nhưng **không cần là language mechanism**.

---

# 51. Một chương trình Axiom hoàn chỉnh

Ví dụ kết hợp khá nhiều cơ chế:

```text
module app

import std.io
import std.fs

enum Error {
    Io(IoError)
    InvalidConfig
}

struct Config {
    port: u16
    host: String
}

impl Config {
    fn parse(data: view<u8>) -> Result<Self, Error> {
        // ...
    }
}

fn load_config(path: Path) -> Result<Config, Error> {
    let file = File.open(path)?
    let data = file.read_all()?
    Config.parse(data)
}

async fn run(path: Path) -> Result<(), Error> {
    let config = load_config(path)?
    
    println(config.host)
    
    Ok(())
}

fn main() -> Result<(), Error> {
    let path = Path("config.toml")
    run(path)
}
```

Điểm đáng chú ý:

**Không có một dòng nào cần:**

```text
&
&mut
*
class
new
delete
try
catch
throw
finally
defer
override
public/private/protected
```

nhưng vẫn có:

- ownership;
- deterministic Drop;
- views;
- traits;
- generics;
- async;
- Result;
- error propagation;
- unsafe escape hatch;
- zero-cost abstractions.

---

# 52. Một thay đổi tôi muốn chốt thêm: `self` syntax

Tôi đề xuất syntax cuối cùng:

```text
fn foo(self)
fn foo(view self)
fn foo(mut self)
```

tương ứng:

```text
T
view<T>
mut_view<T>
```

và **không cho `view mut self`**.

Nếu cần mutable receiver:

```text
mut self
```

Nếu cần explicit type:

```text
self: mut_view<T>
```

Như vậy programmer nhìn thấy ngay:

```text
self       ownership
view self  read capability
mut self   exclusive mutation
```

---

# 53. Điều quan trọng hơn syntax: parser phải đơn giản

Axiom không nên đi theo C++ với grammar context-sensitive khủng khiếp.

Mục tiêu:

```text
Lexer
 ↓
Parser
 ↓
AST
```

parser càng ít phải biết semantic type càng tốt.

Ví dụ generic:

```text
foo::<T>()
```

không cần.

Chỉ:

```text
foo<T>()
```

nếu grammar có thể resolve deterministic.

Compiler resolver sau parser xử lý ambiguity.

---

# 54. Syntax sugar phải biến mất sớm

Ví dụ:

```text
user.greet()
```

→ HIR:

```text
call greet(user)
```

`?`:

```text
x?
```

→ HIR/MIR:

```text
branch
return residual
extract value
```

`for`:

```text
for x in xs
```

→ iterator protocol.

Closure:

```text
|x| x + 1
```

→ closure object + capture metadata.

Method:

```text
x.foo()
```

→ resolved function/trait dispatch.

Mục tiêu:

> **MIR không biết programmer đã viết syntax nào.**

---

# 55. Đây là ranh giới rất quan trọng

Axiom có thể có syntax khá đẹp ở trên:

```text
user.greet()
for x in items
await future
value?
```

nhưng compiler semantic core chỉ cần hiểu một số operation cơ bản:

```text
MOVE
COPY
CALL
RETURN
BRANCH
SWITCH
LOAD
STORE
VIEW
DROP
ALLOC
DEALLOC
AWAIT
SPAWN
ATOMIC
LOCK
UNLOCK
```

Đây chính là cách đạt được:

> **Surface language đơn giản + compiler mạnh.**

---

# 56. Bước tiếp theo: CONST/COMPTIME/REFLECTION-001

Sau Syntax, phần hợp lý nhất cần chốt tiếp là **compile-time system**, vì nó quyết định:

```text
const
comptime
type information
derive
reflection
code generation
generic specialization
build scripts
target detection
```

Đặc biệt cần tránh biến Axiom thành một ngôn ngữ có **hai hoặc ba hệ thống ngôn ngữ độc lập** kiểu:

```text
runtime language
macro language
template language
```

Tôi sẽ thiết kế theo hướng:

> **Comptime dùng chính Axiom + cùng type system + cùng ownership/capability verifier, nhưng chạy trước runtime.**

Đây sẽ là phần quyết định rất lớn việc Axiom có thực sự đơn giản hơn C++/Rust hay không.