Tiếp tục từ baseline đã chốt, bước hợp lý nhất là **đóng băng Syntax v0.1**. Tôi sẽ ưu tiên cú pháp đủ mạnh cho systems programming nhưng tránh mang theo sự phức tạp của C++/Rust.

# AXIOM LANGUAGE SYNTAX v0.1

## 1. Nguyên tắc cú pháp

Axiom nên theo 5 nguyên tắc:

1. **Một cách chính để làm một việc.**
2. **Không có cú pháp phục vụ riêng cho compiler.**
3. **Không bắt programmer viết lifetime/borrow annotation.**
4. **Cú pháp ownership phải nhìn ra được khi nó quan trọng.**
5. **Syntax sugar phải hạ xuống một semantic primitive rõ ràng.**

Ví dụ:

```axiom
let data = load_file(path)
```

không cần:

```axiom
let data: FileData<'a> = ...
```

Compiler tự phân tích ownership/lifetime.

---

# 2. Function

Cú pháp cơ bản:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Expression cuối block là giá trị trả về.

Có thể viết rõ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    return a + b
}
```

Không cần `;` cho expression cuối.

Statement:

```axiom
let x = 10
let y = 20
let z = x + y
```

Tôi nghiêng về **không bắt buộc semicolon**.

Nhưng có thể cho phép:

```axiom
let x = 10;
let y = 20;
```

để dễ generate code và migration. Compiler coi `;` là optional separator.

---

# 3. `let` và `var`

Immutable mặc định:

```axiom
let x = 10
```

Mutable:

```axiom
var x = 10
x = 20
```

Điều này rất quan trọng với concurrency và optimizer.

Không cần:

```axiom
const
readonly
final
immutable
```

cho cùng một khái niệm.

---

# 4. Type annotation

Có thể bỏ annotation khi compiler suy luận được:

```axiom
let x = 100
let name = "Axiom"
let p = Point(10, 20)
```

Nhưng có thể chỉ rõ:

```axiom
let x: i32 = 100
let p: Point = Point(10, 20)
```

Compiler phải reject inference mơ hồ:

```axiom
let x = []
```

nếu không có context xác định `T`.

---

# 5. Struct

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

hoặc nếu có constructor function:

```axiom
fn point(x: f32, y: f32) -> Point {
    Point { x, y }
}
```

Không có constructor đặc biệt như C++.

---

# 6. Method

Đây là điểm tôi muốn giữ rất đơn giản.

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: Vec2) -> f32 {
    sqrt(self.x * self.x + self.y * self.y)
}
```

Gọi:

```axiom
let v = Vec2 { x: 3, y: 4 }

let n = v.length()
```

Compiler hạ:

```text
v.length()
     ↓
length(v)
```

### Mutable method

```axiom
fn normalize(mut_view self: Vec2) {
    ...
}
```

hoặc tốt hơn, vì `self` đặc biệt dễ gây thêm quy tắc, tôi đề xuất:

```axiom
fn normalize(self: mut_view<Vec2>) {
    ...
}
```

Như vậy **method không phải một loại function mới**.

---

# 7. View

Đây là một phần rất quan trọng của Axiom.

```axiom
fn sum(values: view<i32>) -> i32 {
    var result = 0

    for x in values {
        result += x
    }

    result
}
```

Gọi:

```axiom
let numbers = [1, 2, 3, 4]
let x = sum(numbers)
```

Compiler tạo temporary view.

Không cần programmer viết:

```axiom
&numbers
```

hay lifetime.

---

## Mutable view

```axiom
fn fill(values: mut_view<i32>, value: i32) {
    for x in values {
        x = value
    }
}
```

Caller:

```axiom
fill(numbers, 0)
```

Compiler biết `numbers` đang bị mutable-borrow/view trong phạm vi gọi.

Nếu đồng thời:

```axiom
let a = sum(numbers)
fill(numbers, 0)
```

hợp lệ vì view của `sum` đã kết thúc.

Nhưng:

```axiom
let v = make_view(numbers)

fill(numbers, 0)
```

nếu `v` vẫn sống thì compiler phải reject nếu hai access xung đột.

---

# 8. Move

Move không cần keyword.

```axiom
let buffer = Buffer.load(path)

consume(buffer)

print(buffer) // ERROR
```

`consume()` nhận ownership:

```axiom
fn consume(buffer: Buffer) {
    ...
}
```

Nếu muốn giữ giá trị:

```axiom
let copy = buffer
```

chỉ hợp lệ nếu `Buffer: Copy`.

Đây là một điểm tôi muốn Axiom **khác Rust**:

> Programmer không cần suy nghĩ bằng “borrow checker syntax”.

Họ chỉ cần hiểu:

**value / view / ownership**.

Compiler chịu trách nhiệm phần còn lại.

---

# 9. Explicit ownership transfer

Có một vấn đề: đôi khi programmer muốn biểu đạt rất rõ:

> “Tôi cố ý chuyển ownership.”

Tôi đề xuất **không cần `move` trong trường hợp thông thường**.

Nhưng có thể có:

```axiom
consume(move buffer)
```

với `move` là một **semantic assertion**, không phải một loại ownership mới.

Điều này hữu ích trong API quan trọng và diagnostics.

Ví dụ:

```axiom
spawn(move worker)
```

rất dễ đọc.

---

# 10. Enum

```axiom
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

```axiom
enum Option<T> {
    Some(T)
    None
}
```

Enum:

```axiom
enum Shape {
    Circle(f32)
    Rectangle(f32, f32)
    Point
}
```

Không cần class hierarchy.

---

# 11. Match

```axiom
match shape {
    Shape.Circle(r) => {
        pi * r * r
    }

    Shape.Rectangle(w, h) => {
        w * h
    }

    Shape.Point => {
        0
    }
}
```

Compiler bắt buộc exhaustive.

Không có `default` bắt buộc.

Có thể:

```axiom
_ => ...
```

nếu programmer thực sự muốn catch-all.

---

# 12. If

```axiom
if x > 10 {
    foo()
} else {
    bar()
}
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

Không cần `?:`.

Tôi đề xuất **không có ternary operator** trong Core.

---

# 13. Loop

### Infinite

```axiom
loop {
    process()
}
```

### While

```axiom
while running {
    process()
}
```

### For

```axiom
for item in items {
    process(item)
}
```

Range:

```axiom
for i in 0..10 {
    ...
}
```

Exclusive upper bound.

Inclusive:

```axiom
0..=10
```

---

# 14. Break / Continue

```axiom
loop {
    if done {
        break
    }

    if skip {
        continue
    }

    process()
}
```

Không cần label trong v0.1.

Nếu sau này cần nested-loop control, có thể thêm label mà không phá semantic model.

---

# 15. Trait

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

Trait không phải class/interface object.

---

# 16. Generic

```axiom
fn max<T: Comparable>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

Nhiều constraint:

```axiom
fn process<T: Send + Comparable>(x: T) {
    ...
}
```

Có thể dùng `where` sau này nếu constraint quá dài, nhưng **không cần đưa vào syntax v0.1 ngay lập tức**.

---

# 17. Generic struct

```axiom
struct Buffer<T> {
    data: ...
    length: usize
}
```

Sử dụng:

```axiom
let buffer: Buffer<u8>
```

Compiler monomorphize:

```text
Buffer<u8>
Buffer<i32>
Buffer<f32>
```

thành specialization thích hợp.

---

# 18. Associated type

Ví dụ:

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self.Item>
}
```

Implementation:

```axiom
impl Iterator for Numbers {
    type Item = i32

    ...
}
```

Đây là feature nên có vì nó làm generic API sạch hơn rất nhiều.

---

# 19. Operator

Không nên hard-code hàng chục operator vào compiler.

Ví dụ:

```axiom
a + b
```

có thể hạ thành:

```axiom
add(a, b)
```

thông qua trait/operator definition.

Ví dụ:

```axiom
trait Add<Rhs, Output> {
    fn add(self: Self, rhs: Rhs) -> Output
}
```

Nhưng compiler vẫn có intrinsic fast path cho primitive:

```text
i32 + i32
    ↓
machine ADD
```

Không được biến mọi phép cộng thành dynamic dispatch.

---

# 20. String

Tôi muốn tránh sai lầm lớn của C/C++:

```axiom
"hello"
```

không phải raw `char*`.

Nên có distinction:

```text
Bytes
Text
String
TextView
```

nhưng **chưa cần đóng băng toàn bộ string API ở Syntax v0.1**.

Literal:

```axiom
let name = "Axiom"
```

có type compiler-defined string literal / text literal, sau đó contextual conversion.

Byte literal có thể là:

```axiom
b"hello"
```

---

# 21. Error propagation

Nếu:

```axiom
fn load() -> Result<Data, Error> {
    let file = open(path)?
    let data = read(file)?
    Ok(data)
}
```

`?` chỉ là syntax sugar.

Semantic:

```text
Result propagation
```

Không có exception.

Điểm này cực kỳ quan trọng cho binary size:

```text
Result<T,E>
      ↓
ordinary control flow
      ↓
no hidden exception runtime
```

---

# 22. Panic

```axiom
panic("invalid state")
```

Hoặc:

```axiom
assert(x > 0)
```

Compiler có thể lower:

```text
panic
 ↓
runtime-free trap/abort
```

nếu profile `panic=abort`.

---

# 23. Unsafe

```axiom
unsafe {
    let ptr: *mut u8 = ...
    *ptr = 10
}
```

Hoặc:

```axiom
unsafe fn write_register(addr: usize, value: u32) {
    ...
}
```

Điểm quan trọng:

> `unsafe` không có nghĩa là compiler bỏ type checking.

Nó chỉ cho phép programmer sử dụng những primitive mà compiler không thể chứng minh an toàn.

---

# 24. Raw pointer

```axiom
*const T
*mut T
```

Dereference:

```axiom
unsafe {
    let value = *ptr
}
```

Pointer arithmetic cũng unsafe.

Không có:

```axiom
nullptr
```

trong safe language.

Nếu cần nullable pointer ở safe layer:

```axiom
Option<view<T>>
```

hoặc API abstraction thích hợp.

---

# 25. Async

```axiom
async fn fetch(url: Text) -> Result<Data, Error> {
    let response = await http.get(url)?
    response
}
```

`async` chỉ tạo coroutine/state machine.

Không có nghĩa:

```text
async == thread
```

Spawn task:

```axiom
spawn(fetch(url))
```

Compiler kiểm tra `Send` nếu task có khả năng migrate giữa execution contexts.

---

# 26. Thread

Tôi đề xuất API library:

```axiom
thread.spawn(fn() {
    worker()
})
```

hoặc ngắn hơn:

```axiom
spawn_thread(worker)
```

Không nên đưa scheduler/thread runtime vào language core.

---

# 27. Closure

```axiom
let add = |a, b| a + b
```

Có thể type:

```axiom
let add: fn(i32, i32) -> i32 =
    |a, b| a + b
```

Capture:

```axiom
let x = 10

let f = || x + 1
```

Compiler quyết định capture mode phù hợp.

Nếu cần explicit ownership transfer:

```axiom
let f = move || process(data)
```

Đây là một trong số ít nơi tôi cho rằng `move` đáng tồn tại trong syntax.

---

# 28. Module

```axiom
module math
```

Import:

```axiom
import math
```

Hoặc:

```axiom
import math.sqrt
import math.Vec2
```

Export:

```axiom
pub fn sqrt(...)
pub struct Vec2
```

Private mặc định.

Không cần:

```text
public/private/protected/internal/friend
```

hàng loạt như các ngôn ngữ lớn.

---

# 29. Alias và distinct type

Alias:

```axiom
type UserId = u64
```

`UserId` vẫn tương đương `u64`.

Distinct:

```axiom
type UserId = distinct u64
```

Khi đó:

```axiom
let id: UserId = 10
let n: u64 = id
```

không tự động hợp lệ.

Phải chuyển explicit.

Điều này cực kỳ hữu ích để tránh:

```text
UserId
FileId
ThreadId
SocketId
```

vô tình truyền nhầm cho nhau.

---

# 30. Visibility

Chỉ cần:

```axiom
pub
```

Ví dụ:

```axiom
pub struct Vec2 {
    pub x: f32
    pub y: f32
}
```

Mặc định private.

Tôi **không đề xuất `protected`**.

---

# 31. FFI

Ví dụ C ABI:

```axiom
@repr(C)
struct CPoint {
    x: f32
    y: f32
}

extern @abi(C) fn printf(format: *const u8, ...) -> i32
```

Nhưng variadic C có thể để trong FFI/system layer thay vì core safe language.

Axiom function export:

```axiom
@abi(C)
pub fn axiom_add(a: i32, b: i32) -> i32 {
    a + b
}
```

---

# 32. Representation

```axiom
@repr(C)
struct Point {
    x: f32
    y: f32
}
```

Native:

```axiom
struct Point {
    x: f32
    y: f32
}
```

không cam kết physical layout.

Điều này cho compiler quyền:

```text
reorder
pack
scalarize
register-pass
eliminate
```

khi ABI không yêu cầu layout cụ thể.

---

# 33. Attribute

Tôi không muốn biến attribute thành một “ngôn ngữ thứ hai”.

Chỉ dùng cho semantic/compiler boundary:

```axiom
@repr(C)
@inline
@noinline
@cold
@export
@section(".text.hot")
```

Nhưng cần phân loại:

```text
LANGUAGE ATTRIBUTE
ABI ATTRIBUTE
OPTIMIZATION HINT
TOOLING ATTRIBUTE
```

Không cho attribute tùy ý thay đổi semantics.

---

# 34. Những thứ tôi **không muốn** đưa vào Axiom

Đây có lẽ còn quan trọng hơn danh sách feature.

### Không có class

```text
class Foo : Bar
```

### Không có inheritance

Composition + trait.

### Không có virtual mặc định

Dynamic dispatch phải explicit.

### Không có GC

Không có:

```text
new object → GC
```

### Không có lifetime syntax

Không:

```text
'a
```

### Không có borrow syntax kiểu Rust

Không:

```text
&T
&mut T
```

Thay bằng:

```text
view<T>
mut_view<T>
```

### Không có exception

Không:

```text
try
catch
throw
```

trong Core.

### Không có implicit null

`Option<T>`.

### Không có operator overloading tùy tiện kiểu C++

Operator phải có semantic trait rõ ràng.

### Không có macro system trong Core v0.1

Đặc biệt không muốn một hệ macro có khả năng biến parser thành mê cung.

---

# 35. Một chương trình Axiom hoàn chỉnh

Ví dụ nhỏ nhưng cho thấy triết lý:

```axiom
module app

struct Point {
    x: f64
    y: f64
}

fn distance(a: view<Point>, b: view<Point>) -> f64 {
    let dx = a.x - b.x
    let dy = a.y - b.y

    sqrt(dx * dx + dy * dy)
}

enum Result<T, E> {
    Ok(T)
    Err(E)
}

fn main() -> i32 {
    let a = Point {
        x: 0.0
        y: 0.0
    }

    let b = Point {
        x: 3.0
        y: 4.0
    }

    let d = distance(a, b)

    print(d)

    0
}
```

Điểm đáng chú ý:

**Không có:**

```text
class
new
delete
&
*
lifetime
GC
exception
virtual
this
constructor
destructor
```

nhưng vẫn có:

- static typing
- ownership
- views
- deterministic destruction
- generic
- trait
- concurrency
- unsafe
- native ABI
- zero-cost abstraction.

---

# 36. Một quyết định tôi muốn chốt rất rõ

Axiom nên có **hai tầng ngôn ngữ**:

```text
                    AXIOM
                      │
          ┌───────────┴───────────┐
          │                       │
      SAFE AXIOM              UNSAFE AXIOM
          │                       │
  values/views/traits       raw pointers
  ownership               pointer arithmetic
  generics                volatile
  concurrency             hardware
  async                   FFI internals
          │                       │
          └────────── compiler ───┘
```

Nhưng **không phải hai ngôn ngữ riêng**.

`unsafe` chỉ mở thêm một tập primitive.

Điều này rất phù hợp mục tiêu của bạn:

> **Lập trình thông thường đơn giản; khi xuống tầng hệ thống thì không khóa tay programmer.**

---

## 37. Và đây là điểm tôi muốn sửa một chút so với tư duy ban đầu

Không nên đặt mục tiêu:

> “Axiom phải có ít feature.”

Mục tiêu nên là:

> **“Axiom có ít semantic concepts.”**

Đây là khác biệt rất lớn.

Ví dụ Axiom có thể có:

```text
struct
enum
trait
generic
closure
async
thread
view
mut_view
Result
Option
atomic
channel
```

rất nhiều feature.

Nhưng chúng quy về một số ít semantic primitives:

```text
VALUE
OWNERSHIP
VIEW
TYPE
TRAIT
CONTROL FLOW
RESOURCE
EXECUTION CONTEXT
MEMORY ACCESS
ABI
```

Compiler xử lý sự phức tạp.

**Programmer không phải gánh sự phức tạp đó.**

Đây có lẽ là hướng quan trọng nhất để Axiom đạt mục tiêu ban đầu: **mạnh như systems language nhưng cảm giác sử dụng đơn giản hơn C++/Rust**.

### Bước tiếp theo

Sau Syntax v0.1, tôi đề xuất **không nhảy ngay sang Standard Library**. Ta nên đóng một tầng rất quan trọng trước:

**`AXIOM SEMANTIC CORE v0.1`**

Trong đó formalize từng expression thành:

```text
Expression
  ↓
Type
  ↓
Value category
  ↓
Ownership state
  ↓
Access mode
  ↓
Evaluation order
  ↓
Cleanup obligation
  ↓
MIR
```

Đây chính là phần quyết định Axiom có thực sự **đơn giản nhưng nhanh** hay cuối cùng lại biến thành một Rust/C++ mới với cú pháp khác.