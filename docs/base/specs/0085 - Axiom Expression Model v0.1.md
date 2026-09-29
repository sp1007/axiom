Tiếp tục. Tôi sẽ chốt **Expression Model + Operators + Evaluation Semantics**. Phần này tưởng nhỏ nhưng thực ra quyết định rất nhiều về compiler, optimizer và cảm giác sử dụng Axiom.

# Axiom Expression Model v0.1

## 1. Nguyên tắc nền

Tôi đề xuất Axiom chỉ có **một expression model thống nhất**:

> Mọi expression đều có một type và có thể tạo ra giá trị; statement chỉ là expression được dùng vì side effect hoặc control flow.

Ví dụ:

```axiom
let x = 10 + 20
```

`10 + 20` có type `i32`.

```axiom
let x = if condition {
    10
} else {
    20
}
```

`if` cũng có type `i32`.

Điều này giúp HIR/MIR đơn giản hơn rất nhiều.

---

# 2. Statements không cần quá nhiều loại

Các dạng chính:

```text
let
var
assignment
expression statement
if
while
for
match
return
break
continue
```

Không cần phân biệt một hệ thống statement/expression phức tạp như C++.

---

# 3. Block là expression

```axiom
let result = {
    let a = 10
    let b = 20

    a + b
}
```

`result == 30`.

Expression cuối block là giá trị block.

Nếu block kết thúc bằng statement không trả giá trị:

```axiom
{
    println("hello")
}
```

type là:

```text
unit
```

---

# 4. Không cần `;` bắt buộc

Tôi đề xuất Axiom **không dùng semicolon bắt buộc**.

```axiom
let x = 10
let y = 20

foo(x, y)
```

Semicolon chỉ cần trong trường hợp muốn ép expression thành statement hoặc giải quyết ambiguity:

```axiom
foo();
bar();
```

Nhưng tôi thậm chí nghiêng về việc **không có semicolon trong Core syntax**, nếu parser có thể xử lý newline rõ ràng.

### Tuy nhiên có một vấn đề

Code như:

```axiom
foo
(bar)
```

có thể bị hiểu thành:

```axiom
foo(bar)
```

Do đó Axiom cần quy tắc newline rất rõ.

Tôi đề xuất:

> **Newline chỉ kết thúc expression khi expression hiện tại đã syntactically complete.**

Ví dụ:

```axiom
let x =
    a +
    b +
    c
```

vẫn là một expression.

Nhưng:

```axiom
let x = foo()
let y = bar()
```

rõ ràng là hai expression.

---

# 5. Assignment không phải expression có giá trị

Đây là điểm tôi muốn Axiom khác C/C++.

Không cho:

```axiom
if (x = foo()) {
}
```

Assignment:

```axiom
x = foo()
```

có type:

```text
unit
```

hoặc được xem là statement-only expression.

Do đó không thể:

```axiom
let y = (x = 10)
```

Điều này loại bỏ một lượng bug khá lớn mà không mất nhiều sức mạnh.

---

# 6. Compound assignment

Có:

```axiom
x += y
x -= y
x *= y
x /= y
x %= y
```

Semantic tương đương:

```text
x = x + y
```

nhưng compiler không được thực sự evaluate `x` hai lần.

Đặc biệt với indexing:

```axiom
a[i] += f()
```

phải evaluate:

```text
a
i
f()
```

theo thứ tự xác định, rồi thực hiện mutation.

---

# 7. Không có `++` và `--`

Tôi khuyến nghị **loại bỏ**:

```text
i++
++i
i--
--i
```

Lý do:

- tạo nhiều semantics đặc biệt;
- prefix/postfix khác nhau;
- dễ gây side effect ẩn;
- không cần thiết.

Dùng:

```axiom
i += 1
i -= 1
```

đơn giản hơn.

---

# 8. Toán tử số học

Core:

```text
+
-
*
/
%
```

Unary:

```text
-x
+x
```

Nhưng semantics integer đã chốt:

```text
+ - * → checked mặc định
```

Overflow không được âm thầm wrap.

---

# 9. Wrapping và saturating

Giữ syntax đã đề xuất:

```axiom
a + b
a +% b
a +| b
```

Tương ứng:

```text
checked
wrapping
saturating
```

Ví dụ:

```axiom
let a = u8.max
let b = a +% 1
```

→ `0`.

```axiom
let c = a +| 1
```

→ `255`.

Tôi sẽ dùng cùng quy tắc cho:

```text
+%
-%
*%

+|
-|
*|
```

Không cần operator mới cho division vì overflow semantics của division có các trường hợp riêng.

---

# 10. Comparison

Core:

```text
==
!=
<
<=
>
>=
```

Kết quả luôn:

```text
bool
```

Không có C-style:

```axiom
if (x)
```

nếu `x` là integer.

Phải:

```axiom
if x != 0
```

---

# 11. Float comparison

Đây là chỗ cần quyết định kỹ.

IEEE floating-point có NaN nên:

```text
NaN == NaN
```

là false.

Và:

```text
NaN < x
NaN > x
```

đều false.

Do đó `==`, `<`, ... của `f32/f64` phải giữ semantics IEEE-compatible.

Nếu programmer cần total ordering:

```axiom
a.total_cmp(b)
```

qua library/trait.

Không cố làm float trở thành `Ord` thông thường nếu semantic không phù hợp.

---

# 12. Boolean operators

Core:

```text
!
&&
||
```

Có short-circuit:

```axiom
a && b
```

không evaluate `b` nếu `a == false`.

```axiom
a || b
```

không evaluate `b` nếu `a == true`.

Đây là **semantic**, không chỉ optimization.

---

# 13. Bitwise operators

Cho integer:

```text
&
|
^
~
<<
>>
```

Ví dụ:

```axiom
flags = flags | MASK
```

Không overload bitwise tùy tiện trên mọi type trong Core.

Operator traits có thể tồn tại cho những type phù hợp, nhưng compiler phải phân biệt rõ operator semantic.

---

# 14. Shift

Tôi khuyến nghị:

```axiom
x << n
x >> n
```

với shift count ngoài range → trap.

Ví dụ `u32`:

```text
x << 32
```

không được tự động biến thành:

```text
x << 0
```

Wrapping shift nếu cần:

```axiom
x.shl_wrap(n)
```

hoặc intrinsic/library.

Không nên thêm quá nhiều operator:

```text
<<<
>>>
```

chỉ để phục vụ một corner case.

---

# 15. Cast

Chỉ có một cú pháp:

```axiom
x as T
```

Ví dụ:

```axiom
let x = 100i64
let y = x as i32
```

Không có:

```text
(int)x
i32(x)
<T>x
reinterpret<T>(x)
```

trong Core.

---

# 16. Nhưng `as` không phải phép biến đổi tùy tiện

Ví dụ:

```axiom
ptr as usize
```

không nên tự động hợp lệ.

Pointer/address đã được tách semantic:

```text
pointer != integer
```

Phải dùng explicit operation ở unsafe/system layer:

```axiom
unsafe {
    ptr.addr()
}
```

và ngược lại:

```axiom
addr.as_ptr<T>()
```

Điều này bảo vệ abstraction.

---

# 17. `as` và checked conversion

Ví dụ:

```axiom
let x = 300i32 as u8
```

theo baseline:

```text
explicit narrowing
→ truncation
```

Nếu muốn kiểm tra:

```axiom
let x = 300i32.to_u8()?
```

hoặc:

```axiom
let x = checked_cast<u8>(300)?
```

Tôi thích API method/trait hơn là thêm syntax:

```text
x as? u8
```

vì tránh làm `as` trở thành một hệ thống conversion khổng lồ.

---

# 18. Equality không được dựa trên raw memory

```axiom
a == b
```

là semantic equality.

Không phải:

```text
memcmp(&a, &b)
```

vì:

- padding khác nhau;
- enum niche representation;
- float bit patterns;
- compiler-controlled layout.

Compiler có thể optimize equality thành byte comparison nếu chứng minh hợp lệ.

---

# 19. `=` chỉ assignment

```axiom
x = y
```

Không dùng:

```text
=
```

cho equality.

Equality là:

```axiom
x == y
```

Không có lý do để thay đổi quy ước này.

---

# 20. Field access

```axiom
user.name
point.x
```

Nếu field private:

```text
compile error
```

Compiler có thể scalarize:

```text
point.x
```

thành register.

Không cần object memory thực tế.

---

# 21. Method call

```axiom
user.print()
```

resolve thành:

```text
print(view(user))
```

hoặc:

```text
print(mut_view(user))
```

hoặc:

```text
print(user)
```

tùy signature.

Không có hidden receiver ABI.

---

# 22. Function call evaluation order

Đây là một quyết định **rất quan trọng**.

Axiom:

> **Evaluate callee trước, sau đó arguments từ trái sang phải.**

Ví dụ:

```axiom
foo(a(), b(), c())
```

luôn:

```text
foo
a()
b()
c()
```

theo semantic order.

Compiler vẫn có thể reorder machine instructions nếu chứng minh observable behavior không đổi.

Ví dụ nếu:

```text
a()
```

và:

```text
b()
```

đều PURE:

```text
a()
b()
```

có thể được tính theo thứ tự khác ở machine level.

Nhưng semantic result phải giống.

---

# 23. Không cho programmer phụ thuộc vào evaluation order của machine code

Đây là sự khác biệt:

```text
Source semantics:
    deterministic

Machine execution:
    optimizer freedom
```

Ví dụ:

```axiom
let x = f() + g()
```

source semantics:

```text
f()
→ g()
→ +
```

Compiler có thể phát lệnh CPU:

```text
g
f
add
```

nếu `f/g` không có observable dependency.

---

# 24. Indexing

```axiom
let x = array[i]
array[i] = value
```

Compiler lowering:

```text
bounds_check
→ address calculation
→ load/store
```

Nếu chứng minh:

```text
0 <= i < len
```

thì bounds check biến mất.

Đây là một ví dụ điển hình của:

> Safety check ở semantic layer, zero-cost ở machine layer.

---

# 25. Indexing không nhất thiết là compiler magic

Có thể định nghĩa trait/library:

```axiom
trait Indexable<Index> {
    type Output

    fn index(self: view<Self>, index: Index) -> view<Self.Output>
}
```

Nhưng compiler vẫn có thể recognize các trường hợp canonical:

```text
Array
Vec
view
```

để generate code trực tiếp.

Tức là:

```text
library abstraction
+
compiler optimization
```

chứ không nhất thiết biến mọi collection thành compiler primitive.

---

# 26. Slice syntax

Tôi đề xuất:

```axiom
a[start..end]
```

tạo `view<T>`.

Ví dụ:

```axiom
let part = data[10..20]
```

Compiler kiểm tra:

```text
10 <= 20
20 <= data.len
```

và tạo capability tới vùng đó.

Mutable:

```axiom
let part = mut_view(data[10..20])
```

hoặc syntax tốt hơn:

```axiom
let part = data[mut 10..20]
```

### Tôi chưa muốn chốt cú pháp thứ hai.

`mut_view(data)` đã đủ rõ và nhất quán hơn.

---

# 27. Optional access

Tôi **không khuyến nghị** đưa `?.` vào Core v0.1.

Ví dụ:

```axiom
user?.address?.city
```

nghe tiện nhưng tạo thêm semantic rules:

```text
Option propagation
method resolution
field access
ownership
temporary lifetime
```

Trong khi Axiom đã có:

```axiom
match
if let
?
```

Có thể bổ sung sau nếu thực tế cho thấy nó cần thiết.

---

# 28. String interpolation

Đây là feature đáng có vì rất hữu ích.

```axiom
let name = "Axiom"
println("Hello, {name}")
```

Compiler không nên coi đây là runtime reflection.

Nó lower thành kiểu:

```text
write("Hello, ")
write(name)
```

và optimizer có thể tối ưu.

Escape:

```axiom
"{value}"
```

được resolve compile-time.

---

# 29. Không dùng operator pipeline trong Core

Tôi biết syntax kiểu:

```text
x |> foo |> bar
```

rất đẹp.

Nhưng tôi đề xuất **không đưa vào Core v0.1**.

Vì:

```text
foo(x)
```

đã rõ.

Pipeline có thể trở thành library syntax/macro sau này nếu thật sự cần.

Axiom không cần tích lũy syntax chỉ vì “ngôn ngữ hiện đại thường có”.

---

# 30. Operator overloading

Axiom có operator traits:

```axiom
trait Add<Rhs> {
    type Output
    fn add(self: T, rhs: Rhs) -> Self.Output
}
```

và:

```axiom
a + b
```

resolve thành:

```text
Add::add(a, b)
```

Nhưng primitive operations:

```text
i64 + i64
f64 * f64
```

compiler intrinsic.

Điều này rất quan trọng cho performance.

Compiler không cần biến:

```axiom
a + b
```

thành dynamic trait dispatch.

---

# 31. Không cho user định nghĩa operator mới

Ví dụ không:

```text
operator <=>>
operator **
operator %%>
```

Chỉ cho implement **operator đã có**.

Lợi ích:

- parser đơn giản;
- precedence cố định;
- IDE dễ phân tích;
- AI dễ sinh code;
- không có DSL operator explosion.

Đây là một quyết định tôi khá mạnh tay.

---

# 32. Precedence

Nên gần các ngôn ngữ C-family để giảm learning curve:

```text
highest
    ()
    []
    .
    call
    unary ! - + ~
    * / %
    + -
    << >>
    < <= > >=
    == !=
    &
    ^
    |
    &&
    ||
    ??
    ...
lowest
```

Nhưng có một điểm:

### Tôi chưa muốn thêm `??` vào Core v0.1.

Option propagation đã có `?`.

Nếu sau này cần:

```axiom
x ?? default
```

có thể bổ sung.

---

# 33. Không có implicit truthiness

Sai:

```axiom
if count {
}
```

Đúng:

```axiom
if count != 0 {
}
```

Và:

```axiom
if option.is_some() {
}
```

hoặc:

```axiom
if let Some(x) = option {
}
```

Điều này làm code predictable hơn.

---

# 34. Null-coalescing cũng chưa cần

Không:

```text
null
??
?.
```

Safe core dùng:

```text
Option<T>
```

Điều này giữ type system sạch.

---

# 35. Comma operator không tồn tại

Không có:

```axiom
a(), b()
```

để tạo sequence expression.

Nếu cần sequence:

```axiom
a()
b()
```

hoặc block:

```axiom
{
    a()
    b()
}
```

Đơn giản hơn.

---

# 36. Ternary `?:` cũng không cần

Thay vì:

```axiom
let x = condition ? a : b
```

dùng:

```axiom
let x = if condition {
    a
} else {
    b
}
```

Tôi thích cách này hơn vì `if` đã là expression.

Không cần hai syntax cho cùng một semantic construct.

---

# 37. Đây là một điểm rất đáng giá cho compiler

Với expression system trên, HIR có thể khá gọn:

```text
Expression
├── Literal
├── Name
├── Unary
├── Binary
├── Call
├── MethodCall
├── Field
├── Index
├── Cast
├── Tuple
├── Array
├── Struct
├── Block
├── If
├── Match
├── Closure
├── Await
└── Range
```

Không cần hàng chục loại expression đặc biệt.

---

# 38. Và lowering trở nên sạch

Ví dụ:

```axiom
let x = foo(a + b)
```

HIR:

```text
Call(
    foo,
    [
        Binary(Add, a, b)
    ]
)
```

→ Typed HIR

```text
Call<T>
```

→ MIR:

```text
v1 = LOAD a
v2 = LOAD b
v3 = ADD v1, v2
v4 = CALL foo(v3)
STORE x, v4
```

Sau đó optimizer:

```text
inline foo
constant fold
scalarize
register allocation
```

Không có semantic ambiguity.

---

# 39. Một nguyên tắc nữa nên đóng băng

### AEXP-01 — Deterministic Evaluation

Expression evaluation order là deterministic ở semantic level.

### AEXP-02 — Left-to-Right Arguments

Arguments được evaluate trái → phải.

### AEXP-03 — No Assignment Value

Assignment có semantic result `unit`.

### AEXP-04 — No Implicit Truthiness

Chỉ `bool` được dùng trực tiếp làm condition.

### AEXP-05 — Explicit Conversion

Không có implicit user-defined conversion.

### AEXP-06 — Operator Closure

Chỉ các operator Core được phép overload.

### AEXP-07 — Semantic Equality

`==` là semantic equality, không phải representation equality.

### AEXP-08 — Short Circuit

`&&`/`||` short-circuit là semantic.

### AEXP-09 — Bounds Safety

Safe indexing không được tạo memory UB.

### AEXP-10 — Optimization Freedom

Compiler được reorder/eliminate/inline nếu observable semantics không đổi.

### AEXP-11 — Expression Uniformity

Control-flow constructs có thể là expressions nếu có giá trị.

### AEXP-12 — No Hidden Dynamic Dispatch

Operator/method/generic resolution không tự động tạo runtime dispatch.

---

# 40. Bức tranh syntax hiện tại

Axiom v0.1 lúc này đã có một hình khá rõ:

```text
VALUES
  ├── literals
  ├── variables
  ├── struct
  ├── enum
  ├── tuple
  ├── array
  └── closure

EXPRESSIONS
  ├── unary
  ├── binary
  ├── call
  ├── method call
  ├── field
  ├── index
  ├── cast
  ├── block
  ├── if
  ├── match
  ├── range
  └── await

CONTROL
  ├── if
  ├── while
  ├── for
  ├── match
  ├── return
  ├── break
  └── continue

TYPE/ABSTRACTION
  ├── struct
  ├── enum
  ├── trait
  ├── impl
  ├── generic
  ├── associated type
  ├── view<T>
  ├── mut_view<T>
  └── dyn Trait

SYSTEM BOUNDARY
  ├── unsafe
  ├── raw pointer
  ├── extern
  ├── repr
  └── attributes
```

Và đáng chú ý là **không có**:

```text
class
inheritance
GC syntax
lifetime syntax
borrow syntax
reference syntax
new/delete
exception
null
implicit conversion
virtual keyword
operator definition syntax
macro language
```

Đây đang trở thành một surface language khá sạch.

---

## Bước tiếp theo tôi muốn đi vào một phần còn quan trọng hơn syntax

**Axiom Resource & Ownership UX v0.1**.

Tức là lấy những semantics ownership/compiler verifier đã thiết kế và kiểm tra bằng hàng loạt tình huống thực tế:

```text
let a = resource
let b = a

function(a)
function(a)

struct {
    resource
}

array of resources

return resource

return view(resource)

closure captures resource

closure captures view

async {
    use(resource)
    await
    use(resource)
}

thread.spawn(...)

conditional move

loop move

partial move

early return

panic

Drop
```

Đây là bước tôi cho rằng **quan trọng nhất trước khi đóng syntax v0.1**, bởi vì nếu ownership UX ở những case này không thật sự mượt thì toàn bộ triết lý “compiler quản lý lifetime, programmer không phải viết borrow/lifetime” sẽ thất bại.