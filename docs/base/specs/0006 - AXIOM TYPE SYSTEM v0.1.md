Tiếp tục. Ta khóa tiếp **Axiom Type System v0.1**. Tôi sẽ cố tình xử lý phần này theo hướng **ít cơ chế nhưng đủ mạnh**, tránh việc Axiom cuối cùng trở thành “Rust + C++ syntax khác”.

# AXIOM TYPE SYSTEM v0.1

**Status:** FROZEN  
**Depends on:** Core v0.1 + Memory Model v0.1

Mục tiêu:

> **Compiler phải có đủ thông tin để tối ưu và chứng minh safety, nhưng programmer không phải quản lý type machinery bằng tay.**

---

# 1. Mô hình type tổng quát

Axiom type system gồm hai khía cạnh khác nhau:

```text
TYPE
 │
 ├── Representation
 │      ├── scalar
 │      ├── aggregate
 │      ├── enum
 │      ├── function
 │      └── view
 │
 └── Properties
        ├── Copy
        ├── Drop
        ├── Send
        ├── Share
        ├── Sized
        └── ...
```

Đây là một quyết định quan trọng.

`Copy`, `Send`, `Drop` **không phải subtype**.

Chúng là **type properties/capabilities**.

---

# 2. Không có class hierarchy

Axiom không có:

```text
class
extends
base class
virtual method
```

Thay vào đó:

```text
struct
trait
impl
composition
generic constraint
```

Ví dụ:

```axiom
struct Circle {
    radius: f32
}

trait Shape {
    fn area(self) -> f32
}

impl Shape for Circle {
    fn area(self) -> f32 {
        3.14159 * self.radius * self.radius
    }
}
```

---

# 3. Struct là nominal type

Hai struct giống field **không tự động cùng type**.

```axiom
struct Point {
    x: i32
    y: i32
}

struct Coordinate {
    x: i32
    y: i32
}
```

Không được:

```axiom
let p: Point = Coordinate(...)
```

dù representation giống nhau.

Điều này tránh rất nhiều ambiguity.

---

# 4. Nhưng layout có thể giống nhau

Compiler vẫn có thể nhận ra:

```text
Point
Coordinate
```

cùng layout:

```text
i32
i32
```

và tối ưu representation.

Nhưng:

> **same representation ≠ same type.**

---

# 5. Primitive types

Core:

```text
bool

i8   i16   i32   i64
u8   u16   u32   u64

isize
usize

f32
f64
```

Không có implicit conversion tùy tiện.

---

# 6. Integer conversion

Ví dụ:

```axiom
let a: i32 = 100
let b: i64 = a
```

có thể được compiler cho phép nếu conversion được định nghĩa là safe widening.

Nhưng:

```axiom
let x: i32 = some_u64
```

không được tự động truncate.

Programmer phải nói rõ:

```axiom
let x = some_u64 as i32
```

hoặc API checked conversion.

---

# 7. Numeric conversion không được có hidden semantic cost

Một cast có thể:

```text
bit reinterpretation
numeric conversion
checked conversion
saturating conversion
wrapping conversion
```

phải phân biệt rõ.

Không được để:

```text
as
```

lúc thì reinterpret, lúc thì numeric conversion tùy context.

Syntax chi tiết có thể tách sang Numeric Spec, nhưng semantics phải rõ.

---

# 8. `Copy`

Type property:

```text
Copy
```

nghĩa:

> Giá trị có thể được sao chép mà không tạo thêm ownership obligation.

Compiler có thể tự suy luận:

```axiom
struct Point {
    x: f32
    y: f32
}
```

→ `Point : Copy`.

---

# 9. `Drop`

Nếu một struct chứa resource:

```axiom
struct File {
    handle: ...
}
```

nó có thể có:

```text
Drop
```

Nếu:

```text
A : Drop
```

thì:

```text
A
```

không mặc định là `Copy`.

Tức là:

```text
Copy + Drop
```

phải được kiểm soát chặt.

Tôi đề xuất **v0.1 không cho user tự định nghĩa type vừa `Copy` vừa có destructive Drop semantics**.

Điều này loại bỏ rất nhiều ambiguity.

---

# 10. Property propagation

Ví dụ:

```axiom
struct Point {
    x: f32
    y: f32
}
```

Compiler:

```text
Point:
    Copy
    !Drop
    Sized
```

Nếu:

```axiom
struct Line {
    a: Point
    b: Point
}
```

thì:

```text
Line:
    Copy
    !Drop
    Sized
```

Nếu:

```axiom
struct FileData {
    file: File
    data: Buffer
}
```

thì:

```text
FileData:
    !Copy
    Drop
    Sized
```

Compiler derive properties từ members.

---

# 11. `Sized`

Một type có kích thước compile-time known là `Sized`.

Ví dụ:

```text
i32
Point
Array<i32, 100>
```

là Sized.

Một view:

```text
view<T>
```

cũng có thể là Sized:

```text
pointer + length
```

Trong khi một số dynamic type có thể là:

```text
!Sized
```

---

# 12. Type properties không cần syntax everywhere

Không muốn programmer phải viết:

```text
struct X: Copy + Send + Share + Sized
```

nếu compiler có thể tự suy luận.

Ví dụ:

```axiom
struct Point {
    x: f32
    y: f32
}
```

compiler tự xác định.

Đây là một trong những cách Axiom giảm “trait noise”.

---

# 13. Khi nào programmer phải khai báo property?

Khi property không thể suy luận hoặc khi muốn constraint API.

Ví dụ:

```axiom
fn spawn<T: Send>(value: T)
```

Ở đây `Send` là requirement.

Không nhất thiết phải viết:

```axiom
struct Foo: Send
```

nếu compiler có thể chứng minh `Foo` là Send.

---

# 14. Auto properties

Tôi đề xuất:

```text
Copy
Send
Share
Sized
```

là **compiler-derived properties**.

Compiler kiểm tra cấu trúc type.

Ví dụ:

```text
struct A {
    x: i32
}
```

→ Send.

Nếu:

```text
struct B {
    x: SomeNonSendType
}
```

→ !Send.

---

# 15. Trait khác property

Trait:

```axiom
trait Drawable {
    fn draw(self)
}
```

không tự động propagate chỉ vì field có Drawable.

Đây là behavioral abstraction.

Do đó:

```text
Property:
    compiler semantic

Trait:
    programmer-defined behavior
```

---

# 16. Trait implementation

```axiom
impl Drawable for Circle {
    fn draw(self) { ... }
}
```

Có thể có một implementation phù hợp cho một type trong một module/package visibility domain.

Axiom nên tránh coherence nightmare của việc nhiều package cùng tự ý override trait implementation.

---

# 17. Trait coherence

Tôi đề xuất quy tắc đơn giản:

> **Một trait implementation phải thuộc về trait owner hoặc type owner.**

Tức là package của bạn không thể tùy tiện tạo:

```text
impl ForeignTrait for ForeignType
```

nếu cả hai đều thuộc package khác.

Điều này tránh “orphan impl problem”.

---

# 18. Generic

Generic là compile-time abstraction.

```axiom
fn max<T: Comparable>(a: T, b: T) -> T
```

Compiler tạo specialization khi cần.

Ví dụ:

```text
max<i32>
max<f32>
max<MyNumber>
```

---

# 19. Monomorphization là backend mặc định ban đầu

Tôi đề xuất:

```text
Generic source
      ↓
constraint resolution
      ↓
specialization
      ↓
concrete MIR
```

Điều này rất phù hợp mục tiêu performance.

Không cần generic runtime machinery mặc định.

---

# 20. Nhưng đừng biến generic thành template C++

Axiom generic không nên là:

```text
text substitution
```

mà là:

```text
typed generic AST/HIR
        ↓
type checking
        ↓
instantiation
        ↓
typed MIR
```

Do đó lỗi sẽ rõ ràng hơn C++ template.

---

# 21. Trait resolution

Ví dụ:

```axiom
fn render<T: Drawable>(x: T)
```

Compiler resolve:

```text
T = Circle
Circle implements Drawable
```

→ static dispatch.

Nếu không có implementation:

```text
COMPILE ERROR
```

Không có runtime fallback.

---

# 22. Method syntax

Ta vẫn giữ ý tưởng:

```axiom
fn length(self: Vec2) -> f32
```

và:

```axiom
v.length()
```

Compiler resolve thành:

```text
length(v)
```

Không có hidden object dispatch.

---

# 23. Method resolution

Nếu:

```axiom
v.length()
```

compiler tìm theo thứ tự:

```text
1. inherent function của type
2. applicable trait implementation
3. imported extension implementation
```

Nếu nhiều candidate cùng độ ưu tiên:

```text
AMBIGUOUS_METHOD
```

Không được âm thầm chọn theo heuristic.

---

# 24. Extension methods

Đây là một điểm rất mạnh của struct + function.

Một library có thể:

```axiom
fn clamp(self: f32, min: f32, max: f32) -> f32
```

và dùng:

```axiom
x.clamp(0, 1)
```

không cần sửa type `f32`.

Nhưng để tránh namespace pollution, extension function phải được import rõ.

---

# 25. Không có overload kiểu C++

Tôi khuyên Axiom **hạn chế overload**.

Ví dụ không nên có:

```text
foo(i32)
foo(f32)
foo(String)
foo(Buffer)
foo(...)
```

rồi compiler phải giải bài toán overload resolution cực kỳ phức tạp.

Thay vào đó:

```text
generic
trait
distinct names
```

Ví dụ:

```axiom
parse_int()
parse_float()
```

hoặc:

```axiom
parse<T>()
```

Điều này cực kỳ có lợi cho compiler và AI.

---

# 26. Nhưng có thể giữ một dạng overload có kiểm soát

Ví dụ operator:

```axiom
a + b
```

có thể resolve qua trait:

```text
Add<T>
```

thay vì C++ overload machinery.

---

# 27. Operator model

Conceptually:

```axiom
trait Add<Rhs> {
    type Output
    fn add(self, rhs: Rhs) -> Output
}
```

Nhưng syntax operator:

```axiom
a + b
```

compiler lower thành:

```text
Add::add(a, b)
```

Static dispatch.

---

# 28. Associated type

Một trait có thể cần output type:

```text
Iterator
    Item
```

Ví dụ:

```axiom
trait Iterator {
    type Item
    fn next(self) -> Option<Item>
}
```

Đây là một tính năng tôi cho rằng đáng có.

Nó giảm nhu cầu generic parameter quá dài.

---

# 29. Generic constraint

Ví dụ:

```axiom
fn sort<T: Comparable>(items: mut_view<T>)
```

Compiler biết:

```text
T
 ├── Comparable
 └── Sized
```

và có thể optimize.

---

# 30. Multiple constraints

Cho phép:

```axiom
fn foo<T: Comparable + Send>(x: T)
```

Nhưng compiler diagnostic phải cực kỳ rõ.

Ví dụ:

```text
T does not satisfy Send
because:
Foo
 └── field `handle`
      └── FileHandle is not Send
```

Đây là phần AI-agent sẽ cực kỳ hưởng lợi.

---

# 31. Associated constraints

Ví dụ:

```axiom
trait Container {
    type Item
}
```

có thể constraint:

```axiom
fn process<C: Container>
where C.Item: Send
```

Syntax cụ thể có thể để sau.

Semantics cần hỗ trợ.

---

# 32. Type inference

Axiom inference nên mạnh nhưng **không được đoán mơ hồ**.

Ví dụ:

```axiom
let x = 10
```

→ default integer type.

Nhưng:

```axiom
let x = []
```

nếu không có context:

```text
TYPE_INFERENCE_AMBIGUOUS
```

Không tự chọn `Array<i32>` một cách bí mật.

---

# 33. Literal polymorphism

Integer literal:

```text
42
```

không nhất thiết ngay lập tức phải là `i32`.

Compiler có thể giữ:

```text
integer literal
```

đến khi context xác định.

Ví dụ:

```axiom
let x: u64 = 42
```

→ `u64`.

Điều này làm generic numeric code đẹp hơn.

---

# 34. Tuple

Core có thể hỗ trợ tuple:

```axiom
let p = (10, 20)
```

type:

```text
(i32, i32)
```

Tuple nên là anonymous structural type, không phải nominal type.

---

# 35. Array

```axiom
[i32; 4]
```

là fixed-size value.

Size là một phần type:

```text
Array<i32, 4>
```

khác:

```text
Array<i32, 8>
```

Điều này hữu ích cho SIMD, embedded, compile-time optimization.

---

# 36. Slice/View

Memory Model định nghĩa:

```text
view<T>
mut_view<T>
```

Type System định nghĩa chúng là **non-owning types**.

Property:

```text
view<T>:
    Copy
    Sized
    !Drop
```

nhưng lifetime validity được compiler kiểm tra.

---

# 37. String

Core không nên biến `String` thành primitive.

Tách:

```text
bytes
string/text
```

Ví dụ:

```text
ByteBuffer
String
StringView
```

là library/core-adjacent types.

Điều này tránh ép Unicode implementation vào language primitive.

---

# 38. Enum

Enum là algebraic data type.

```axiom
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

Compiler biết variant layout.

Ví dụ nếu:

```text
T = pointer-sized
E = pointer-sized
```

compiler có thể tạo representation rất nhỏ.

---

# 39. Niche optimization

Compiler SHOULD có thể tối ưu:

```text
Option<Pointer>
```

thành:

```text
null = None
non-null = Some
```

nếu ABI và semantics cho phép.

Nhưng programmer không được phụ thuộc vào layout nếu không explicit representation.

---

# 40. No null

```text
Option<T>
```

thay thế nullable semantics.

Ví dụ:

```axiom
fn find(id: ID) -> Option<User>
```

match:

```axiom
match find(id) {
    Some(user) => ...
    None => ...
}
```

---

# 41. Type identity

Axiom có:

```text
Nominal:
    struct
    enum
    trait

Structural:
    tuple
    function type
    view
    array
```

Điều này tạo cân bằng tốt.

---

# 42. Type aliases

Cho phép:

```axiom
type UserId = u64
```

nhưng cần phân biệt:

```text
alias
```

với:

```text
newtype
```

Tôi đề xuất cả hai.

### Alias

```axiom
type UserId = u64
```

chỉ đổi tên.

### Newtype

```axiom
type UserId = distinct u64
```

tạo type mới.

Điều này cực kỳ hữu ích để tránh nhầm:

```text
UserId
OrderId
FileId
```

dù đều là `u64`.

---

# 43. `distinct` type

Ví dụ:

```axiom
type UserId = distinct u64
type OrderId = distinct u64
```

Không thể:

```axiom
let x: UserId = order_id
```

Nếu không explicit conversion.

Đây là một safety feature rất rẻ.

---

# 44. Dynamic type

Tôi không muốn `dynamic` nằm trong Core v0.1.

Nếu sau này cần:

```text
Any
Dynamic
Reflection object
```

thì thêm ở một spec riêng.

Core static type system không cần runtime dynamic dispatch mặc định.

---

# 45. `Any`

Nếu sau này có:

```text
Any
```

nó phải được hiểu là một abstraction runtime rõ ràng:

```text
data
type information
possibly vtable
```

Không được để `Any` biến mọi Axiom value thành object có hidden header.

---

# 46. Type erasure

Khi cần:

```text
trait object
```

compiler có thể tạo:

```text
data pointer
dispatch pointer
```

nhưng chỉ ở dynamic boundary.

Static generic:

```text
T: Trait
```

không cần object representation.

---

# 47. Static dispatch

Đây là default:

```axiom
fn draw<T: Drawable>(x: T)
```

Compiler:

```text
draw<Circle>
draw<Rectangle>
```

Có thể inline hoàn toàn.

---

# 48. Dynamic dispatch

Chỉ khi type bị erased:

```text
Drawable
```

compiler mới cần runtime dispatch.

Điều này giữ nguyên nguyên tắc:

> **Runtime cost must be explicit in the type abstraction.**

---

# 49. Closure type

Mỗi closure là một anonymous type.

Ví dụ:

```axiom
let offset = 10

let f = |x| x + offset
```

Compiler conceptually:

```text
struct Closure_0 {
    offset: i32
}

fn Closure_0_call(self, x: i32) -> i32
```

Nếu không escape:

```text
inline
```

không cần allocation.

---

# 50. Closure capture

Ba semantic modes:

```text
by-value
by-view
by-mut-view
```

Compiler có thể infer.

Ví dụ:

```axiom
let x = 10

let f = || x + 1
```

capture `x` bằng value/copy.

Nếu resource:

```text
Buffer
```

compiler có thể move.

Nếu mutable:

```text
var x
```

compiler cần xác định exclusive access.

---

# 51. Đây là chỗ Axiom có thể đơn giản hơn Rust

Rust bắt programmer thường xuyên quyết định:

```text
move
borrow
borrow mutably
lifetime
```

Axiom hướng tới:

```text
compiler infer
```

nhưng vẫn cho programmer escape hatch khi inference không đủ.

Ví dụ có thể sau này có:

```axiom
move x
view x
mut_view x
```

nhưng đây là explicit override, không phải syntax bắt buộc.

---

# 52. Type checking pipeline

Tôi đề xuất:

```text
AST
 ↓
Name Resolution
 ↓
Type Inference
 ↓
Trait Resolution
 ↓
Property Derivation
 ↓
Ownership Validation
 ↓
Generic Specialization
 ↓
Typed HIR
```

Sau đó mới:

```text
Typed HIR
 ↓
MIR
```

---

# 53. Diagnostic phải là first-class

Compiler không chỉ nói:

```text
type mismatch
```

mà phải nói:

```text
expected:
    view<i32>

found:
    view<f32>

argument #1 of `sum`
```

Hoặc:

```text
cannot send `FileBuffer` to another thread

because:
    FileBuffer
      └── handle: RawHandle
            └── not Send
```

Đây không phải UI decoration.

Nó nên là **structured diagnostic data** để AI agent có thể parse.

---

# 54. Đây là một yêu cầu quan trọng cho Axiom compiler

Compiler diagnostic nên có hai dạng:

```text
Human diagnostic
```

và:

```text
Machine diagnostic
```

Ví dụ machine:

```text
error_code:
AX_TYPE_0142

kind:
TYPE_MISMATCH

location:
...

expected:
...

found:
...

causes:
...
```

AI agent có thể dùng trực tiếp.

---

# 55. Type System invariants

Tôi đề xuất đóng băng các invariant:

### ATS-01

Every expression has exactly one resolved static type.

### ATS-02

No implicit unsafe numeric narrowing.

### ATS-03

Structs are nominal types.

### ATS-04

Enums are algebraic sum types.

### ATS-05

Traits define behavior, not inheritance.

### ATS-06

Type properties are distinct from behavioral traits.

### ATS-07

`Copy` is compiler-checkable.

### ATS-08

Owning non-Copy values use move semantics.

### ATS-09

`Drop` is deterministic.

### ATS-10

Generic code is statically type checked.

### ATS-11

Static dispatch is preferred/default.

### ATS-12

Dynamic dispatch requires an explicit type-erasure boundary.

### ATS-13

Method syntax is function syntax sugar.

### ATS-14

Type inference must be deterministic.

### ATS-15

Ambiguous inference MUST produce an error.

### ATS-16

Safe nullable semantics use `Option<T>`.

### ATS-17

Raw pointers are unsafe/system-level types.

### ATS-18

Type layout is not observable unless explicitly represented.

### ATS-19

Compiler diagnostics have stable machine-readable error identities.

### ATS-20

Type semantics MUST NOT depend on runtime GC/metadata.

---

# 56. Một điều tôi muốn loại khỏi Axiom

Sau khi thiết kế này, tôi nghĩ Axiom **không nên có**:

```text
class
inheritance
virtual
protected
friend
operator overloading machinery kiểu C++
implicit constructor
implicit conversion chains
GC by default
implicit RC
lifetime syntax
borrow syntax
template metaprogramming
macro-based type tricks
```

Không phải vì những thứ đó "xấu".

Mà vì Axiom đã có những primitive tốt hơn:

```text
struct
trait
impl
generic
distinct type
property
view
Option
Result
closure
compile-time execution
```

---

# 57. Mô hình cuối cùng

Nếu rút Type System thành một sơ đồ:

```text
                         TYPE
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
    VALUE TYPES       VIEW TYPES        FUNCTION TYPES
       │                  │                  │
 struct / enum        view<T>              fn(...)
 tuple / array        mut_view<T>          closure
       │                  │
       └──────────┬───────┘
                  │
             TYPE PROPERTIES
                  │
      ┌───────────┼────────────┐
      │           │            │
    Copy        Drop         Sized
      │           │
      └───────────┼────────────┐
                  │            │
                Send         Share
                  │            │
                  └─────┬──────┘
                        │
                     TRAITS
                        │
             ┌──────────┼──────────┐
             │          │          │
          static      generic    dynamic
          dispatch    dispatch    dispatch
```

Đây là Type System mà tôi nghĩ **đủ mạnh cho systems programming nhưng vẫn có cơ hội giữ compiler và language core nhỏ**.

---

## Bước tiếp theo: Concurrency Model

Sau Type System này, **Concurrency Model trở nên khá rõ**:

```text
Type Properties
      │
      ├── Send
      └── Share
            │
            ▼
       Concurrency
            │
     ┌──────┼───────┐
     ▼      ▼       ▼
   Thread  Async   Channel
     │      │       │
     └──────┼───────┘
            ▼
       Ownership
            │
            ▼
      Data-race-free
```

Phần tiếp theo tôi đề xuất không chỉ nói về `thread/async`, mà sẽ **thiết kế hẳn concurrency semantics của Axiom**: `Send/Share`, thread spawning, channel ownership transfer, atomics, memory ordering, mutex/RWLock, async state machine, cancellation, task lifetime, structured concurrency và đặc biệt là **cách làm concurrency mà không cần một async runtime khổng lồ**.