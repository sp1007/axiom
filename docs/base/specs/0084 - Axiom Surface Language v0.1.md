Tiếp tục. Với phần semantic đã khá đầy đủ, tôi nghĩ **không nên nhảy ngay vào viết grammar**. Trước tiên phải chốt một nguyên tắc: **surface language của Axiom phải tận dụng semantic model đã thiết kế, thay vì bắt programmer viết ra những thứ compiler đã có thể tự chứng minh.**

# Axiom Surface Language v0.1

## 1. Mục tiêu cú pháp

Axiom nên có 5 đặc điểm:

1. **Nhìn vào code là hiểu được ownership cơ bản.**
2. **Không có lifetime syntax.**
3. **Không có borrow syntax kiểu Rust.**
4. **Không có class/constructor/destructor syntax riêng.**
5. **Không biến mọi thứ thành annotation.**

Tôi đề xuất syntax có cảm giác gần C/C++/Rust/Go ở mức quen thuộc, nhưng semantic đơn giản hơn.

Ví dụ một chương trình hoàn chỉnh:

```axiom
import std.io

struct User {
    id: u64
    name: Text
}

fn greet(user: view<User>) {
    println("Hello, {user.name}")
}

fn main() {
    let user = User {
        id: 1
        name: "Axiom"
    }

    greet(user)
}
```

Điểm đáng chú ý:

```text
user
 ↓
view<User>
```

compiler tự tạo capability tạm thời khi gọi `greet`.

Không cần:

```text
&user
&'a User
borrow user
ref user
```

---

# 2. `let` và `var`

Tôi nghĩ nên giữ cực kỳ đơn giản:

```axiom
let x = 10
var y = 20
```

### `let`

Immutable binding:

```axiom
let x = 10
```

Không thể:

```axiom
x = 20
```

### `var`

Mutable binding:

```axiom
var x = 10
x = 20
```

Không cần:

```text
mut
mutable
const variable
```

vì `let`/`var` đã thể hiện trực tiếp ý định.

---

# 3. Type annotation

Cho phép:

```axiom
let x: i64 = 100
var name: Text = "Axiom"
```

Nhưng inference được ưu tiên:

```axiom
let x = 100
```

Compiler biết:

```text
x : i32
```

nếu không có contextual type khác.

---

# 4. Struct

Không có constructor magic:

```axiom
struct Point {
    x: f64
    y: f64
}
```

Khởi tạo:

```axiom
let p = Point {
    x: 10.0
    y: 20.0
}
```

Không cần:

```axiom
Point::new(...)
```

trừ khi programmer **thực sự muốn một function constructor**:

```axiom
fn point(x: f64, y: f64) -> Point {
    Point { x, y }
}
```

Điều này rất hợp với quan điểm trước đây:

> **Constructor không phải language primitive.**

---

# 5. Method syntax

Giữ method syntax vì nó rất tiện cho programmer, nhưng semantic vẫn là function.

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: view<Vec2>) -> f32 {
    sqrt(self.x * self.x + self.y * self.y)
}
```

Gọi:

```axiom
let v = Vec2 { x: 3, y: 4 }

let n = v.length()
```

Compiler hiểu:

```axiom
length(view(v))
```

Không có hidden `this`.

---

# 6. Mutation method

```axiom
fn scale(self: mut_view<Vec2>, factor: f32) {
    self.x *= factor
    self.y *= factor
}
```

Gọi:

```axiom
var v = Vec2 { x: 1, y: 2 }

v.scale(10)
```

Compiler tạo `mut_view` trong phạm vi call.

Không cần:

```axiom
fn scale(&mut self, ...)
```

Đây chính là nơi Axiom khác Rust rõ rệt.

---

# 7. Ownership phải thể hiện qua kiểu dữ liệu, không phải parameter modifier

Đây là quyết định tôi muốn giữ rất mạnh.

Không có:

```text
own T
& T
&mut T
in T
out T
inout T
```

Thay vào đó:

```axiom
T
view<T>
mut_view<T>
```

Ví dụ:

```axiom
fn consume(buffer: Buffer)
```

`Buffer` là owning value.

```axiom
fn inspect(buffer: view<Buffer>)
```

read-only capability.

```axiom
fn modify(buffer: mut_view<Buffer>)
```

exclusive mutable capability.

Đây là đủ.

---

# 8. Move syntax không cần keyword

Ví dụ:

```axiom
let a = Buffer(...)
let b = a
```

Nếu `Buffer` không `Copy`:

```text
a → MOVED
b → OWNER
```

Sau đó:

```axiom
use(a)
```

compiler báo lỗi.

Không cần:

```axiom
move(a)
```

trong trường hợp thông thường.

`move` chỉ cần xuất hiện nếu programmer muốn **ép closure capture**:

```axiom
let task = move || {
    use(buffer)
}
```

Đây là một trường hợp khác.

---

# 9. Copy phải explicit ở type level

Ví dụ:

```axiom
struct Point {
    x: f64
    y: f64
}

impl Copy for Point {}
```

Sau đó:

```axiom
let a = Point { x: 1, y: 2 }
let b = a
use(a)
use(b)
```

hợp lệ.

Điều này rất rõ:

```text
Copy → assignment có thể copy
non-Copy → assignment move
```

Không có phép copy ngầm một resource type.

---

# 10. Clone là hành động khác Copy

Nếu một object lớn/resource cần duplicate:

```axiom
let b = a.clone()
```

`clone()` là function/trait bình thường.

Điều này tránh một lỗi thiết kế phổ biến:

```text
Copy = "copy mọi thứ"
```

trong khi có những type cần:

```text
deep copy
resource duplication
allocation
reference count
```

---

# 11. `view` chỉ cần xuất hiện khi API yêu cầu nó

Đây là điểm UX rất quan trọng.

Programmer viết:

```axiom
fn print_name(name: view<Text>)
```

nhưng caller:

```axiom
let name = "Hưng"

print_name(name)
```

Không phải:

```axiom
print_name(view(name))
```

Vì conversion owner → ephemeral view đã được quyết định là implicit.

Chỉ khi muốn **lưu capability**:

```axiom
let v = view(name)
```

mới phải viết explicit.

Tương tự:

```axiom
let v = mut_view(buffer)
```

---

# 12. Tại sao không implicit view trong mọi trường hợp?

Nếu compiler cho phép:

```axiom
let v = name
```

rồi tự suy ra `v` là view thì programmer không biết:

```text
v là owner?
v là alias?
v có thể mutate?
v có lifetime nào?
```

Do đó:

```text
argument conversion → implicit
binding/storage       → explicit
return/escape         → explicit + checked
```

Đây là một quy tắc UX rất tốt.

---

# 13. `if`

Đơn giản:

```axiom
if x > 10 {
    foo()
} else {
    bar()
}
```

Không cần:

```text
then
endif
```

Expression:

```axiom
let result =
    if x > 10 {
        100
    } else {
        200
    }
```

Hai nhánh phải unify type.

---

# 14. `while`

```axiom
while x < 100 {
    x += 1
}
```

`for` dành cho iterable:

```axiom
for x in values {
    print(x)
}
```

Compiler lowering trực tiếp qua `Iterator`.

---

# 15. Range

```axiom
for i in 0..10 {
    ...
}
```

nghĩa:

```text
0 <= i < 10
```

Inclusive:

```axiom
0..=10
```

Không cần tạo một heap object.

Range nên là zero-cost abstraction.

---

# 16. `match`

```axiom
match value {
    Some(x) => use(x)
    None => fallback()
}
```

Struct:

```axiom
match point {
    Point { x, y } => ...
}
```

Enum:

```axiom
match result {
    Ok(value) => ...
    Err(error) => ...
}
```

Compiler kiểm tra exhaustiveness.

---

# 17. `match` không cần `return` trong từng arm

Ví dụ:

```axiom
let text = match result {
    Ok(value) => value
    Err(_) => "error"
}
```

Đây là expression.

Nếu một arm terminal:

```axiom
let value = match result {
    Ok(x) => x
    Err(e) => panic(e)
}
```

`panic()` có type `never`, nên vẫn unify được.

---

# 18. `?`

Tôi vẫn khuyến nghị giữ `?`.

```axiom
fn load() -> Result<Text, Error> {
    let file = open("data.txt")?
    let text = file.read()?
    Ok(text)
}
```

Semantic:

```text
Result
   ↓
match
   ├── Ok → continue
   └── Err → cleanup + return
```

Không phải exception.

Đây là một trong những syntax đáng giữ vì nó giảm boilerplate mà không tạo hidden runtime machinery.

---

# 19. Không cần `try/catch`

Axiom không cần:

```text
try
catch
throw
finally
```

Core chỉ cần:

```text
Result
Option
panic
?
```

Resource cleanup do compiler đảm bảo.

---

# 20. Struct update

Có thể cho syntax:

```axiom
let b = Point {
    ...a
    x: 20
}
```

nhưng tôi **chưa muốn đưa vào v0.1** nếu ownership semantics của partial move chưa được test đủ.

Đây là một feature tiện lợi nhưng không cần thiết để bootstrap.

---

# 21. Enum

Syntax:

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

Không cần enum value kiểu C:

```text
OK = 0
ERROR = 1
```

Nếu cần C ABI:

```axiom
@repr(C)
```

---

# 22. Trait

Syntax:

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

Tôi thích việc implementation **không cần lặp `trait` trong function**.

Compiler biết function nào implement method nào dựa vào signature.

---

# 23. Extension function

Đúng theo ý tưởng mà chúng ta đã bàn:

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: view<Vec2>) -> f32 {
    ...
}
```

Gọi:

```axiom
v.length()
```

Nếu function được import:

```axiom
import math.vec2.length
```

thì method xuất hiện.

Điều này giúp tránh namespace khổng lồ.

---

# 24. Generic syntax

Tôi đề xuất:

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

Multiple constraints:

```axiom
fn foo<T: A + B + C>(x: T) {
}
```

Hoặc nếu constraint phức tạp:

```axiom
fn foo<T>(x: T)
where T: A + B,
      T.Output: C
{
}
```

Nhưng **`where` chỉ cần cho trường hợp phức tạp**.

Không biến mọi function thành:

```axiom
fn foo<T>
where ...
```

---

# 25. Generic struct

```axiom
struct Box<T> {
    value: T
}
```

Const generic:

```axiom
struct Array<T, N: usize> {
    data: ...
}
```

Không cần:

```text
Array<T, const N: usize>
```

vì trong Axiom type parameter và compile-time value parameter có thể được phân biệt bởi kind/compiler metadata.

Tuy nhiên, nếu parser ambiguity trở thành vấn đề, có thể thêm:

```axiom
struct Array<T, #N: usize>
```

nhưng tôi **chưa khuyến nghị**. Cú pháp càng ít marker càng tốt.

---

# 26. Closure

```axiom
let add = |a, b| a + b
```

Capture:

```axiom
let factor = 10

let scale = |x| x * factor
```

Compiler tự xác định capture mode.

Nếu cần ép move:

```axiom
let task = move || {
    process(buffer)
}
```

Không cần:

```text
|&x|
|&mut x|
```

vì compiler inference.

---

# 27. Async

Syntax quen thuộc:

```axiom
async fn load() -> Result<Data, Error> {
    let a = fetch_a().await?
    let b = fetch_b().await?
    Ok(combine(a, b))
}
```

`async` không có nghĩa:

```text
spawn thread
```

và `.await` không có nghĩa:

```text
block OS thread
```

Nó chỉ tạo state machine.

Executor nằm ở library.

---

# 28. Module syntax

Tôi đề xuất:

```axiom
module app.user

pub struct User {
    ...
}

pub fn create() -> User {
    ...
}
```

Import:

```axiom
import app.user.User
import app.user.create
```

Hoặc:

```axiom
import app.user.*
```

nhưng wildcard import nên có warning/khuyến nghị tránh trong production.

---

# 29. Visibility chỉ cần `pub`

Private mặc định:

```axiom
struct User {
    id: u64
}
```

Public:

```axiom
pub struct User {
    pub id: u64
}
```

Không cần:

```text
public
private
protected
internal
friend
package-private
```

`pub` đủ.

---

# 30. Attributes

Attributes nên có nhưng phải phân tầng.

Ví dụ:

```axiom
@repr(C)
struct Foo {
    ...
}
```

```axiom
@export("foo")
extern "C" fn foo() {
}
```

```axiom
@align(64)
struct CacheLine<T> {
    value: T
}
```

Nhưng không được để attributes trở thành “ngôn ngữ thứ hai” chứa mọi semantic.

Nguyên tắc:

> **Attribute chỉ thay đổi một contract/compiler property đã được định nghĩa. Nó không tạo ra semantic magic tùy ý.**

---

# 31. `unsafe`

Syntax:

```axiom
unsafe {
    ...
}
```

hoặc:

```axiom
unsafe fn read(ptr: *const u8) -> u8 {
    ...
}
```

Nhưng như đã thống nhất:

> `unsafe` không có nghĩa “compiler tắt hết kiểm tra”.

Ví dụ type checking vẫn hoạt động.

Compiler chỉ chuyển trách nhiệm về các invariant mà nó không thể chứng minh.

---

# 32. Pointer syntax

Do user đặc biệt không thích pointer/reference bureaucracy, tôi sẽ **không làm pointer xuất hiện thường xuyên trong syntax**.

Chỉ khi system-level:

```axiom
var p: *mut u8
```

hoặc:

```axiom
let p = addr.as_ptr<T>()
```

Còn application code chủ yếu:

```axiom
T
view<T>
mut_view<T>
```

Đây là một khác biệt rất quan trọng của Axiom.

---

# 33. Không có `null`

Không:

```axiom
User?
```

nếu ý nghĩa là nullable pointer.

Thay vào đó:

```axiom
Option<User>
```

và:

```axiom
Some(user)
None
```

Compiler có thể niche-optimize:

```text
Option<Box<T>>
```

thành pointer + null representation nếu ABI/representation cho phép.

Nhưng programmer vẫn nhìn thấy ADT semantics.

---

# 34. Một chương trình thực tế

Nếu ghép các quyết định lại:

```axiom
module app

import std.io

struct User {
    id: u64
    name: Text
}

trait Printable {
    fn print(self: view<Self>)
}

impl Printable for User {
    fn print(self: view<User>) {
        println("{self.id}: {self.name}")
    }
}

fn find_user(id: u64) -> Option<User> {
    if id == 1 {
        Some(User {
            id: 1
            name: "Axiom"
        })
    } else {
        None
    }
}

fn main() {
    let user = find_user(1)?

    user.print()
}
```

Đây đã có:

```text
struct
trait
impl
method syntax
value semantics
Option
pattern semantics
ownership
implicit ephemeral view
generic-capable architecture
deterministic cleanup
```

nhưng không có:

```text
class
this
new/delete
GC
lifetime
borrow annotation
reference syntax
virtual method mặc định
exception
runtime object
```

---

# 35. Một thay đổi tôi đặc biệt khuyến nghị

Tôi nghĩ Axiom nên có một nguyên tắc syntax rất rõ:

> **Nếu một thông tin có thể suy ra một cách chắc chắn từ ngữ cảnh và việc suy luận đó không làm thay đổi semantic contract, programmer không phải viết nó.**

Ví dụ:

```axiom
v.length()
```

compiler suy ra:

```text
length(view(v))
```

```axiom
thread.spawn(|| work(data))
```

compiler suy ra capture và kiểm tra `Send`.

```axiom
let x = foo()
```

compiler suy ra type.

```axiom
let x = a + b
```

compiler suy ra operator implementation.

Nhưng nếu thông tin **thay đổi ownership/storage/runtime behavior**, phải explicit:

```axiom
view<T>
mut_view<T>
dyn Trait
Box<T>
unsafe
extern "C"
@repr(C)
move ||
```

Đây là ranh giới rất đẹp:

```text
                 Axiom syntax
                       │
          ┌────────────┴────────────┐
          │                         │
   compiler-inferable          semantic boundary
          │                         │
       implicit                   explicit
```

---

# 36. Tôi sẽ chốt thêm một nguyên tắc UX

### ASURF-01 — Semantic Visibility

> Syntax phải thể hiện những abstraction có chi phí hoặc thay đổi semantics observable; implementation details mà compiler có thể chứng minh thì không cần expose.

Ví dụ:

```text
dyn Trait       → explicit
Box<T>          → explicit semantic dynamic storage
unsafe          → explicit
extern "C"      → explicit
repr(C)         → explicit

register/stack  → không cần
heap allocation → không cần nếu không observable
lifetime        → không cần
borrow region   → không cần
vtable           → không cần
monomorphization → không cần
inlining         → không cần
register alloc   → không cần
```

Tôi nghĩ đây chính là thứ giúp Axiom đạt mục tiêu ban đầu của bạn: **ngôn ngữ mạnh, không cố ép programmer phải học “cơ chế bên dưới” chỉ để viết code an toàn.**

---

## Bước tiếp theo

Sau syntax, phần còn thiếu ở tầng ngôn ngữ không còn nhiều. Tôi đề xuất đi tiếp vào **“Axiom Built-in Types + Operators + Expressions”** và chốt rất kỹ:

- toán tử nào có trong Core;
- overload operator bằng trait thế nào;
- precedence/associativity;
- assignment và compound assignment;
- `++/--` có nên tồn tại không;
- cast `as`;
- `is` / pattern test;
- indexing `a[i]`;
- field access;
- function call;
- pipeline/chaining có nên có không;
- string interpolation;
- optional chaining có cần không;
- và đặc biệt **expression evaluation order**, để sau này compiler optimizer không được phép làm thay đổi semantics.

Đây là phần nên chốt trước khi viết grammar/lexer chính thức.