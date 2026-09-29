Tiếp tục với **Type System v0.1**. Tôi đồng ý nên chốt `unit` và `never` trước, sau đó mới khóa inference/coercion/numeric model. Đây là nền móng để Axiom không bị “C++ hóa” về sau.

# Axiom Type System v0.1

Mục tiêu:

> **Type system phải đủ mạnh để compiler chứng minh an toàn, nhưng không biến programmer thành người viết annotation cho compiler.**

Tôi đề xuất mô hình:

```text
Type
├── Primitive
├── Aggregate
├── Algebraic
├── Function
├── Capability
├── Generic
└── Special
```

---

# 1. `unit` — kiểu không mang dữ liệu

Axiom nên có:

```text
unit
```

tương tự `()` trong Rust.

Ví dụ:

```axiom
fn log(message: Text) -> unit {
    ...
}
```

Có thể cho syntax:

```axiom
fn log(message: Text) {
    ...
}
```

và compiler hiểu return type mặc định là:

```text
unit
```

Một value `unit` không chứa thông tin hữu ích.

Compiler có thể hoàn toàn loại bỏ nó khỏi machine representation.

Ví dụ:

```axiom
fn foo() {
    println("hello");
}
```

không cần thực sự trả một value.

### Invariant

**ATY-01 — Unit Erasure**

`unit` không tạo runtime storage nếu ABI không yêu cầu.

---

# 2. `never` — kiểu không bao giờ trả control

Đây là type cực kỳ hữu ích:

```text
never
```

Ví dụ:

```axiom
fn fatal(message: Text) -> never {
    panic(message)
}
```

Hoặc:

```axiom
fn abort() -> never {
    ...
}
```

Một expression có type `never` nghĩa là:

```text
expression không bao giờ produce value
```

và:

```text
control không tiếp tục sau expression
```

---

# 3. `never` làm `if` đẹp hơn

Ví dụ:

```axiom
let x = if condition {
    42
} else {
    fatal("bad state")
};
```

Nhánh:

```text
42 : i64
```

nhánh kia:

```text
fatal(...) : never
```

Compiler có thể coi:

```text
never
```

là compatible với mọi expected type trong **control-flow sense**, vì nhánh đó không bao giờ tạo value.

Kết quả:

```text
x : i64
```

Không cần:

```text
as i64
```

---

# 4. `panic()` nên có type `never`

Do đó:

```axiom
fn panic(message: Text) -> never
```

và:

```axiom
fn unreachable() -> never
```

Điều này giúp compiler tự nhiên hiểu:

```axiom
if x < 0 {
    panic("negative");
}

use(x);
```

sau `panic` không cần phân tích một giá trị giả.

---

# 5. `return` cũng có thể xem như diverging expression

Về mặt compiler semantics:

```text
return x
```

không produce value cho caller expression.

Nó tạo:

```text
CONTROL_EXIT(Return)
```

Tôi không nhất thiết biến syntax `return` thành expression mà programmer có thể nhét ở mọi nơi. Nhưng trong type/control-flow system, nó có **diverging semantics tương đương `never`**.

---

# 6. `break` / `continue`

Tương tự:

```text
break
continue
```

không produce ordinary value.

Nhưng chúng khác `never` ở một điểm:

```text
break
```

đi tới loop exit.

```text
continue
```

đi tới loop header.

Do đó MIR vẫn giữ chúng là control-flow terminators.

---

# 7. Type hierarchy?

Tôi **không muốn Axiom có subtype hierarchy tổng quát**.

Không nên có:

```text
Dog <: Animal
Animal <: Object
Object <: Any
```

Đây là con đường dẫn đến:

- object model
- implicit conversions
- vtable
- variance phức tạp
- runtime type metadata.

Thay vào đó:

```text
Type
  │
  ├── trait implementation
  ├── generic constraint
  └── explicit conversion
```

Ví dụ:

```axiom
trait Drawable { ... }

struct Circle { ... }

impl Drawable for Circle { ... }
```

`Circle` **không trở thành subtype của Drawable**.

Nó chỉ thỏa:

```text
Circle implements Drawable
```

---

# 8. Trait bound thay cho subtype

Ví dụ:

```axiom
fn draw<T: Drawable>(x: T) {
    ...
}
```

ý nghĩa:

```text
T phải implement Drawable
```

Không phải:

```text
T is a subclass of Drawable
```

Static dispatch có thể trở thành:

```text
draw<Circle>
 ↓
specialized function
 ↓
direct machine call
```

Không cần vtable.

---

# 9. Type inference

Axiom nên có inference, nhưng **không nên cố suy luận mọi thứ**.

Ví dụ:

```axiom
let x = 42;
```

compiler biết:

```text
x : i64
```

theo default integer type.

Ví dụ:

```axiom
let p = Point {
    x: 10,
    y: 20
};
```

compiler biết:

```text
p : Point
```

Nhưng:

```axiom
let x = foo();
```

nếu `foo` overloaded/ambiguous:

```text
ERROR
```

Không được đoán ngẫu nhiên.

---

# 10. Numeric literal

Đây là chỗ cần thiết kế cẩn thận.

```axiom
42
```

không nên ngay lập tức là một machine `i64` trong parser.

AST:

```text
IntegerLiteral(42)
```

Type checker mới resolve:

```text
IntegerLiteral
      ↓
expected type?
      ↓
i32 / i64 / u32 / ...
```

Ví dụ:

```axiom
let x: u8 = 42;
```

→ hợp lệ nếu literal nằm trong range.

Nhưng:

```axiom
let x: u8 = 300;
```

→ compile error.

Không runtime truncation.

---

# 11. Default numeric type

Nếu không có context:

```axiom
let x = 42;
```

tôi đề xuất:

```text
i64
```

vì đây là lựa chọn tự nhiên cho systems language 64-bit hiện đại.

Nhưng không nên hard-code parser.

Type checker:

```text
unsuffixed integer
       ↓
expected type
       ↓
default i64
```

Có thể sau này default phụ thuộc target, nhưng tôi **không khuyến nghị**. Cùng source nên có semantics ổn định giữa target.

---

# 12. Float literal

```axiom
let x = 3.14;
```

default:

```text
f64
```

Nếu:

```axiom
let x: f32 = 3.14;
```

compiler convert literal trực tiếp sang `f32`, không phải:

```text
f64 → f32 runtime conversion
```

nếu constant có thể biểu diễn.

---

# 13. Không implicit numeric conversion giữa variables

Đây là một quyết định quan trọng.

Không cho:

```axiom
let a: i32 = 10;
let b: i64 = a;
```

tự động convert.

Phải:

```axiom
let b: i64 = a as i64;
```

Lý do:

```text
i32 → i64
```

có thể an toàn về range, nhưng:

```text
i64 → i32
```

có thể mất dữ liệu.

Nếu Axiom tự động làm một chiều thì programmer lại phải nhớ quy tắc đặc biệt.

Do đó:

> **Variable-to-variable numeric conversion luôn explicit.**

---

# 14. `as` không nên có một semantics duy nhất

Ví dụ:

```axiom
x as i32
```

phải được type checker phân biệt:

```text
safe widening
checked narrowing
reinterpretation
pointer conversion
```

Tôi đề xuất:

```text
as
```

chỉ cho **value conversion thông thường**.

Các trường hợp nguy hiểm hơn phải explicit API/intrinsic:

```text
checked_cast
wrapping_cast
reinterpret
ptr_cast
```

Ví dụ:

```axiom
let y = x.checked_as<i32>()?;
```

hoặc syntax tương đương sau này.

Không nên để:

```text
as
```

trở thành “cái gì cũng cast được”.

---

# 15. Boolean không phải integer

Không cho:

```axiom
if 1 {
}
```

hoặc:

```axiom
let x: i32 = true;
```

`bool` là type riêng.

Điều này giúp tránh một lượng lớn lỗi C-style.

---

# 16. Pointer cũng không phải integer

Không cho safe code:

```axiom
let x: usize = pointer;
```

hay:

```axiom
let p = 123 as *mut Foo;
```

Raw pointer conversion thuộc unsafe/system layer.

```text
usize ≠ pointer
```

dù machine representation có thể đều 64 bit.

Đây là distinction semantic rất quan trọng.

---

# 17. `Sized`

Axiom cần một khái niệm compiler-known:

```text
Sized
```

Nhưng programmer không nên phải viết nó trong hầu hết trường hợp.

Các type như:

```text
i64
Point
Array<T, 10>
Vec<T>
```

đều có known representation size.

Nhưng một số abstraction có thể không có size tĩnh:

```text
dyn Trait
view<T>        // tùy representation
unsized data
```

Generic:

```axiom
fn foo<T>(x: T) { ... }
```

mặc định có thể yêu cầu:

```text
T: Sized
```

Nếu muốn dynamic/unsized semantics thì explicit.

---

# 18. Nhưng đừng biến `Sized` thành Rust-style bureaucracy

Tôi đề xuất compiler inference:

```axiom
fn foo<T>(x: T)
```

compiler tự biết `T` cần `Sized` nếu ABI/operation yêu cầu.

Không bắt programmer liên tục viết:

```axiom
<T: Sized>
```

trừ khi thực sự cần express public constraint.

---

# 19. Tuple

Axiom nên có tuple:

```axiom
let x = (10, 20);
```

type:

```text
(i64, i64)
```

Nested:

```text
(i64, (f64, bool))
```

Tuple là value aggregate.

Không có:

```text
object header
```

Compiler có thể scalarize:

```text
(i64, i64)
```

thành hai registers.

---

# 20. Array

```axiom
let a = [1, 2, 3, 4];
```

type:

```text
Array<i64, 4>
```

Fixed size compile-time.

```text
Array<T, N>
```

là:

- inline/value
- contiguous
- ownership của elements
- size known khi compile.

Không heap mặc định.

---

# 21. `Vec` vẫn khác `Array`

```text
Array<T, N>
```

semantic:

```text
size = N
storage = inline
```

Trong khi:

```text
Vec<T>
```

semantic:

```text
dynamic length
dynamic capacity
ownership of storage
potential relocation
```

Do đó:

```axiom
fn foo(a: view<i64>)
```

có thể nhận cả:

```text
Array
Vec
slice
```

nếu contiguous region phù hợp.

---

# 22. Slice/View không nên là subtype collection

Đây là điểm quan trọng.

Không:

```text
Vec <: Collection
Array <: Collection
View <: Collection
```

theo object hierarchy.

Thay vào đó:

```text
Vec
 └── can produce view<T>

Array
 └── can produce view<T>

external memory
 └── can produce view<T>
```

và API generic dựa trên trait/capability.

Ví dụ:

```axiom
fn sum(v: view<i64>) -> i64
```

hoặc trait abstraction nếu cần.

---

# 23. Function type

Axiom cần first-class function type:

```text
fn(i64, i64) -> i64
```

Ví dụ:

```axiom
let f: fn(i64) -> i64 = square;
```

Function pointer khác closure.

```text
fn(...) -> ...
```

= function code pointer.

Closure:

```text
|x| x * factor
```

= code + environment.

Nếu closure không capture:

```text
|x| x * 2
```

compiler có thể convert thành function pointer nếu context yêu cầu.

---

# 24. Closure type nên anonymous

Không cần programmer đặt tên:

```text
Closure<Foo>
```

Compiler internal type:

```text
ClosureTypeId
```

Source chỉ thấy:

```axiom
let f = |x| x * 2;
```

Nếu pass vào generic:

```axiom
apply(f, 10);
```

compiler biết exact closure type.

Không cần runtime type object.

---

# 25. Generic type identity

Ví dụ:

```axiom
Vec<i64>
Vec<f64>
```

là hai instantiation của cùng generic definition.

Compiler có thể:

```text
monomorphize
```

hoặc:

```text
share code
```

nhưng semantic type identity vẫn khác:

```text
Vec<i64> != Vec<f64>
```

---

# 26. Type alias vs newtype

Đây là thứ tôi muốn chốt sớm.

### Alias

```axiom
type UserId = u64;
```

chỉ là alias.

Do đó:

```text
UserId == u64
```

về type identity.

### Newtype

```axiom
struct UserId(u64);
```

là type mới.

```text
UserId != u64
```

nhưng compiler có thể biểu diễn nó chính xác như:

```text
u64
```

nếu ABI/layout cho phép.

Đây là zero-cost abstraction rất hữu ích.

---

# 27. Newtype đặc biệt hữu ích cho systems programming

Ví dụ:

```axiom
struct FileHandle(u64);
struct SocketHandle(u64);
struct ProcessId(u64);
```

Compiler ngăn:

```axiom
send(socket, process_id)
```

nếu type không phù hợp.

Nhưng binary vẫn có thể chỉ là:

```text
u64
```

Không object overhead.

---

# 28. Type identity và representation phải tách nhau

Đây là nguyên tắc:

```text
Type Identity
      ≠
Memory Representation
```

Ví dụ:

```text
UserId
```

có type identity riêng nhưng:

```text
representation = u64
```

Có thể:

```text
Vec3
```

là:

```text
struct Vec3 { x:f32, y:f32, z:f32 }
```

và representation đúng 12 bytes nếu target/layout cho phép.

Compiler không được biến semantic distinction thành runtime overhead nếu không cần.

---

# 29. Coercion

Axiom nên **cực kỳ hạn chế implicit coercion**.

Tôi đề xuất chỉ có một số coercion compiler-known:

```text
T → view<T>
```

trong ephemeral call context đã quy định.

Ngoài ra:

```text
Array<T,N> → view<T>
Vec<T>       → view<T>
```

khi API yêu cầu view.

Nhưng không:

```text
i32 → i64
String → Text
T → dyn Trait
```

một cách tùy tiện.

---

# 30. `dyn Trait` là explicit coercion

Ví dụ:

```axiom
let x: dyn Drawable = circle;
```

đây là một **semantic type-erasure operation**.

Compiler tạo:

```text
data pointer
+
dispatch metadata
```

và có thể thêm:

```text
drop
size
alignment
```

metadata nếu ABI cần.

Điều quan trọng:

```text
Circle
```

không tự động biến thành:

```text
dyn Drawable
```

ở mọi nơi.

Nếu implicit, programmer sẽ khó biết khi nào dynamic dispatch xảy ra.

---

# 31. Type inference phải deterministic

Ví dụ:

```axiom
let x = foo(a);
```

Nếu có nhiều candidate:

```text
foo<i32>
foo<i64>
foo<f64>
```

và không đủ context:

```text
AMBIGUOUS_TYPE
```

Không được compiler chọn dựa vào:

- thứ tự declaration
- backend
- optimization
- implementation detail.

Đây là yêu cầu rất quan trọng cho AI-generated code.

---

# 32. Type errors nên có cấu trúc

Ví dụ:

```text
AX_TYPE_0001

expected:
    i64

found:
    Text

at:
    foo(x)

note:
    function parameter #1 requires i64
```

Compiler API có thể xuất JSON:

```text
{
  "code": "AX_TYPE_0001",
  "kind": "type_mismatch",
  "expected": "i64",
  "found": "Text",
  "span": ...
}
```

Điều này rất phù hợp mục tiêu **AI-friendly compiler** của Axiom.

---

# 33. Type system lúc này có cấu trúc khá gọn

```text
Type
│
├── Primitive
│   ├── bool
│   ├── i8..i64
│   ├── u8..u64
│   ├── isize
│   ├── usize
│   ├── f32
│   └── f64
│
├── Special
│   ├── unit
│   ├── never
│   └── Sized property
│
├── Aggregate
│   ├── struct
│   ├── tuple
│   └── array
│
├── Algebraic
│   └── enum
│
├── Callable
│   ├── function
│   └── closure
│
├── Capability
│   ├── view<T>
│   └── mut_view<T>
│
└── Dynamic
    └── dyn Trait
```

Generic/trait không phải một “runtime type category”; chúng là compile-time mechanisms.

---

# 34. Một quyết định nữa: không có implicit bottom/null/Any

Tôi đề xuất không có:

```text
null
Any
Object
dynamic
```

trong Core.

Thay vào đó:

```text
Option<T>
dyn Trait
generic<T>
```

mỗi cái có semantic rõ ràng.

Điều này giữ type system nhỏ.

---

# 35. Type checking pipeline

Kiến trúc compiler sẽ là:

```text
AST
 │
 ▼
Name Resolution
 │
 ▼
Type Inference
 │
 ├── literal resolution
 ├── generic inference
 ├── function resolution
 ├── trait constraints
 ├── coercion
 └── expected-type propagation
 │
 ▼
Typed HIR
 │
 ▼
MIR
```

Quan trọng:

> **MIR không còn ambiguity về type.**

Mọi `ValueId`, `LocalId`, `Place` đều đã có `TypeId`.

---

# 36. Và đây là một nguyên tắc tôi muốn thêm vào Axiom

### **ATY-02 — No Semantic Guessing**

Compiler không được tự ý chọn một meaning khi source có nhiều interpretation hợp lệ.

Ví dụ:

```text
overload ambiguity
generic ambiguity
numeric ambiguity
trait ambiguity
```

→ diagnostic.

Điều này đặc biệt quan trọng nếu mục tiêu là để AI agent viết Axiom code.

AI có thể sửa lỗi dựa trên:

```text
AX_TYPE_...
```

thay vì compiler “đoán hộ”.

---

## Type system gần như đã đủ để bước sang một phần rất quan trọng khác

Bây giờ Axiom có:

```text
Value
Ownership
Capability
Region
Effect
Type
Control Flow
```

Mảnh ghép tiếp theo tôi muốn thiết kế là **Pattern Matching + Algebraic Data Types + Destructuring**.

Nó sẽ giải quyết một loạt thứ cùng lúc:

```text
Option
Result
enum
struct destructuring
tuple destructuring
partial move
match guards
exhaustiveness
OR-pattern
pattern ownership
```

và đặc biệt sẽ kiểm tra xem **ownership model hiện tại có thực sự đủ sạch hay chưa**. Đây cũng là lúc ta có thể phát hiện những góc khó của `partial move + Drop + match` trước khi compiler được triển khai quá sâu.