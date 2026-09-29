# AXIOM LANGUAGE SPECIFICATION v0.1
# Part IX — Expressions · Evaluation · Operators · Conversion · Pattern Semantics

Phần này khóa một điểm rất quan trọng của Axiom: **chương trình phải có thứ tự đánh giá xác định**. Không được để compiler/backend tự chọn thứ tự rồi biến những khác biệt đó thành hành vi quan sát được.

Nguyên tắc:

> **Nếu thứ tự đánh giá có thể ảnh hưởng đến kết quả, Axiom phải quy định thứ tự.**

Đồng thời:

> **Compiler được tự do tối ưu sau khi semantic result đã được xác định.**

---

# 1. Semantic expression model

Mọi expression trong Axiom được compiler phân loại nội bộ thành một hoặc nhiều semantic category:

```text
VALUE
PLACE
CAPABILITY
NEVER
```

### VALUE

Expression tạo ra một giá trị.

```axiom
10 + 20
make_user()
user.name
```

### PLACE

Expression xác định một vị trí lưu trữ có thể đọc/ghi.

Ví dụ:

```axiom
user.name
array[i]
buffer[offset]
```

PLACE không nhất thiết tương ứng với địa chỉ vật lý.

### CAPABILITY

Expression tạo ra quyền truy cập không sở hữu:

```axiom
view(buffer)
mut_view(buffer)
```

Compiler theo dõi provenance và region của capability.

### NEVER

Expression không trả về vì control flow không tiếp tục:

```axiom
panic("failed")
unreachable()
return value
```

`never` có thể coerce về context expression thích hợp mà không tạo runtime conversion.

---

# 2. Evaluation order

Axiom sử dụng:

> **Strict deterministic left-to-right evaluation.**

Thứ tự mặc định:

```text
outer expression
    ↓
subexpressions từ trái → phải
    ↓
operator/function call
    ↓
result
```

Ví dụ:

```axiom
foo(a(), b(), c())
```

luôn:

```text
a()
b()
c()
foo(...)
```

Không được compiler biến thành:

```text
c()
a()
b()
```

dù machine code cuối cùng có thể reorder instruction **nếu không làm thay đổi observable semantics**.

---

# 3. Function-call evaluation

Với:

```axiom
receiver.method(arg1, arg2)
```

thứ tự semantic:

```text
1. evaluate receiver
2. resolve method
3. evaluate arg1
4. evaluate arg2
5. perform call
```

Ví dụ:

```axiom
items[index()].push(make_value())
```

semantic:

```text
items
index()
make_value()
push(...)
```

Method syntax vẫn chỉ là syntax sugar:

```axiom
items.push(x)
```

tương đương semantic với:

```axiom
push(items, x)
```

nhưng evaluation order của receiver vẫn được giữ.

---

# 4. Function arguments are evaluated exactly once

Mỗi argument được evaluate đúng một lần.

```axiom
foo(next(), next())
```

không được compiler gọi `next()` thêm lần nữa.

Điều này đặc biệt quan trọng với:

- side effects
- ownership transfer
- atomic operations
- I/O
- function calls
- unsafe operations

---

# 5. Short-circuit operators

`&&` và `||` là **control-flow operators**, không phải ordinary overloaded operators.

## `&&`

```axiom
a && b
```

semantic:

```text
evaluate a

if a == false:
    result = false
else:
    evaluate b
```

`b` có thể không được evaluate.

## `||`

```axiom
a || b
```

semantic:

```text
evaluate a

if a == true:
    result = true
else:
    evaluate b
```

Ví dụ:

```axiom
if ptr != null && ptr.is_valid() {
    ...
}
```

đảm bảo `ptr.is_valid()` chỉ chạy sau điều kiện đầu tiên.

---

# 6. No implicit eager evaluation

Axiom không cho phép compiler evaluate expression chỉ vì nó "có thể".

Ví dụ:

```axiom
false && dangerous()
```

`dangerous()` **không được gọi**.

Đây là semantic rule, không chỉ là optimization opportunity.

---

# 7. Operator precedence

Precedence v0.1:

```text
highest
    ()
    []
    .
    ?.

    unary: ! ~ - +

    * / %

    + -

    << >>

    &

    ^

    |

    < <= > >=

    == !=

    &&

    ||

    = += -= *= /= %= ...
lowest
```

Không có:

```text
++ 
--
?:
```

trong v0.1.

Parentheses luôn được phép để làm rõ ý định:

```axiom
(a + b) * c
```

---

# 8. Arithmetic operators

Primitive arithmetic:

```axiom
+ - * / %
```

Các toán tử này tuân theo type của operands.

Không có implicit numeric promotion kiểu C:

```text
u8 + i32
```

không tự động biến thành một kiểu thứ ba.

Compiler yêu cầu operands tương thích hoặc programmer phải chuyển đổi:

```axiom
x as i32 + y
```

---

# 9. Overflow

Ba nhóm semantics:

### Checked

```axiom
a + b
a - b
a * b
```

Nếu overflow xảy ra trong safe execution:

```text
panic/trap
```

### Wrapping

```axiom
a +% b
a -% b
a *% b
```

hoạt động modulo theo width của type.

### Saturating

```axiom
a +| b
a -| b
a *| b
```

giới hạn tại min/max.

Ví dụ:

```axiom
let x: u8 = 250
let y = x +| 20
```

kết quả:

```text
255
```

---

# 10. Division semantics

Integer division:

```axiom
a / b
```

với:

```text
b == 0
```

→ panic/trap.

Phép chia signed có trường hợp biểu diễn kết quả không representable, ví dụ:

```text
MIN_INT / -1
```

→ panic/trap trong checked operation.

Không có undefined behavior.

---

# 11. Comparison

Primitive comparable values hỗ trợ:

```axiom
==
!=
<
<=
>
>=
```

Nhưng compiler không tự tạo một conversion graph để ép hai type thành nhau.

Ví dụ:

```axiom
let a: i32 = 10
let b: i64 = 20

a < b
```

→ compile error.

Phải viết rõ:

```axiom
(a as i64) < b
```

---

# 12. Equality is semantic, not memory comparison

```axiom
a == b
```

không mặc định có nghĩa:

```text
memcmp(&a, &b)
```

Nếu type có equality semantics riêng, compiler resolve theo trait/intrinsic tương ứng.

Padding bytes, pointer representation nội bộ hoặc layout optimization không được làm thay đổi semantic equality.

---

# 13. Operator overloading

Operator overloading được thực hiện thông qua trait.

Ví dụ:

```axiom
a + b
```

có thể resolve tới:

```axiom
Add.add(a, b)
```

Nhưng compiler phải dùng **exact deterministic trait resolution**.

Không có:

```text
thử conversion A
→ thử overload B
→ thử conversion C
→ chọn overload "gần nhất"
```

Nếu có nhiều candidate hợp lệ:

```text
compile error
```

---

# 14. Operators with control-flow semantics cannot be overloaded

Các operator sau không được user-defined:

```axiom
&&
||
=
.
[]
? 
```

vì chúng mang semantic/control-flow đặc biệt.

Ví dụ:

```axiom
a && b
```

phải giữ short-circuit.

Nếu cho overload tùy ý, compiler không thể bảo đảm property này.

---

# 15. Indexing

```axiom
a[i]
```

là indexing operation.

Evaluation order:

```text
evaluate a
evaluate i
perform bounds/provenance check
load/access element
```

Ví dụ:

```axiom
buffer[next_index()]
```

`next_index()` chạy sau khi `buffer` đã được resolve.

---

# 16. Bounds checking

Safe indexing luôn có semantic bounds safety.

```axiom
array[i]
```

nếu:

```text
i >= length
```

→ panic/trap.

Compiler có quyền loại bỏ bounds check nếu chứng minh được:

```text
0 <= i < length
```

Ví dụ:

```axiom
for i in 0..array.len() {
    sum += array[i]
}
```

compiler có thể chứng minh bounds và loại bỏ check.

Đây là:

> **Optimization, không phải thay đổi semantic.**

---

# 17. Unchecked indexing

System-level code có thể yêu cầu unchecked access thông qua explicit unsafe API.

Ví dụ conceptual:

```axiom
unsafe {
    array.get_unchecked(i)
}
```

Không có:

```axiom
array[i]
```

tự nhiên trở thành unchecked chỉ vì compiler đang ở release mode.

---

# 18. Field access

```axiom
user.name
```

được evaluate:

```text
evaluate user
resolve field name
access field
```

Field projection không tạo ownership mới.

Nếu:

```axiom
user: User
```

thì:

```axiom
user.name
```

có thể là:

```text
PLACE
```

hoặc trở thành VALUE khi context yêu cầu read.

---

# 19. Field move

Với non-Copy field:

```axiom
let name = user.name
```

nếu `name` không phải Copy:

```text
user.name → name
```

là **MOVE**.

Sau đó:

```axiom
user.name
```

không còn hợp lệ.

Nhưng những field khác vẫn có thể còn usable nếu type cho phép partial move.

Ví dụ:

```axiom
struct User {
    name: Text
    age: i32
}

let name = user.name
print(user.age)
```

hợp lệ.

---

# 20. Copy expression

Nếu expression có type `T: Copy`, dùng nó trong value context có thể tạo semantic copy.

```axiom
let a: i32 = 10
let b = a
```

sau đó:

```axiom
use(a)
use(b)
```

đều hợp lệ.

`Copy` không yêu cầu compiler phải emit physical load/store.

Compiler có thể giữ cả hai logical values trong registers.

---

# 21. Move expression

Non-Copy value trong owning context được move.

```axiom
let a = make_buffer()
let b = a
```

sau đó:

```axiom
use(a)
```

→ compile error.

Move không có nghĩa:

```text
memcpy(a → b)
```

mà là:

```text
ownership(a) → ownership(b)
```

---

# 22. Explicit clone

Nếu programmer muốn tạo một bản sao tài nguyên/giá trị có chi phí:

```axiom
let b = a.clone()
```

`Clone` không phải `Copy`.

Ví dụ:

```axiom
let a = String.from("hello")
let b = a.clone()
```

có thể cần allocation.

Compiler không được tự biến:

```axiom
let b = a
```

thành:

```axiom
let b = a.clone()
```

---

# 23. Assignment

Assignment:

```axiom
x = value
```

có semantic result:

```text
()
```

Không được chain:

```axiom
a = b = c
```

vì assignment không tạo value.

Đây là chủ ý để tránh ambiguity giữa:

```text
value expression
ownership transfer
mutation
```

---

# 24. Assignment semantics

```axiom
x = expr
```

semantic:

```text
1. evaluate destination place
2. evaluate expr
3. verify access capability
4. drop old destination value if required
5. move/copy new value into destination
6. result = ()
```

Ví dụ:

```axiom
buffer = create_buffer()
```

nếu `buffer` đang chứa resource cũ, resource cũ được cleanup đúng ownership rules trước khi replacement hoàn tất.

---

# 25. Compound assignment

Các toán tử:

```axiom
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

là assignment operators.

```axiom
x += y
```

không tương đương textual rewrite đơn giản nếu việc evaluate `x` nhiều lần tạo side effect.

Semantic conceptual form:

```text
evaluate destination once
evaluate RHS once
perform operation
store result
```

Ví dụ:

```axiom
array[index()] += value
```

`index()` chỉ chạy **một lần**.

---

# 26. No hidden read/write alias violation

Compiler phải kiểm tra capability khi compound assignment xảy ra.

Ví dụ conceptual:

```axiom
mutate(x, view(x))
```

nếu API yêu cầu mutable capability và immutable capability đồng thời conflict → compile error.

Không có chuyện compiler "đoán rằng programmer biết mình đang làm gì".

Nếu thực sự cần aliasing đặc biệt:

```axiom
unsafe
```

hoặc abstraction synchronization/atomic phù hợp.

---

# 27. Temporary values

Temporary là semantic value được tạo trong expression và không có binding trực tiếp.

Ví dụ:

```axiom
foo(make_buffer())
```

Temporary `make_buffer()` sống đủ lâu để hoàn thành call.

Compiler xác định:

```text
creation
→ required uses
→ destruction
```

theo semantic lifetime.

---

# 28. Temporary lifetime

Temporary phải tồn tại cho tới khi tất cả semantic uses của expression hoàn tất.

Ví dụ:

```axiom
consume(make_resource())
```

resource không được Drop trước `consume`.

Sau khi call hoàn tất, nếu ownership không được chuyển đi:

```text
Drop temporary
```

được thực hiện.

---

# 29. Temporary lifetime is semantic, not lexical-only

Compiler có thể rút ngắn physical storage lifetime nếu không ảnh hưởng semantics.

Ví dụ:

```axiom
let x = make_large_value()
use(x)
other()
```

Nếu compiler chứng minh `x` không còn được sử dụng sau `use(x)`, storage có thể được giải phóng/reuse sớm.

Nhưng observable Drop semantics vẫn phải được bảo toàn.

---

# 30. View creation

Implicit owner → view conversion chỉ được phép tại **ephemeral call boundary**.

Ví dụ:

```axiom
fn sum(data: view<i32>) -> i32 {
    ...
}

sum(array)
```

được phép.

Compiler tạo capability tương ứng trong thời gian call.

---

# 31. No general implicit view conversion

Không cho:

```axiom
let v: view<i32> = array
```

phải viết:

```axiom
let v = view(array)
```

Tương tự:

```axiom
let v = mut_view(array)
```

Điều này ngăn compiler vô tình tạo một non-owning capability có lifetime khó nhìn thấy.

---

# 32. View expression

```axiom
view(x)
```

tạo:

```text
READ capability
```

không chuyển ownership.

```axiom
mut_view(x)
```

tạo:

```text
WRITE capability
```

và yêu cầu exclusive access.

---

# 33. View is not Copy

Một `view<T>` có thể được duplicate:

```axiom
let a = view(buffer)
let b = a
```

nếu capability rules cho phép.

Nhưng semantic này không gọi là `Copy`.

Lý do:

```text
Copy = duplication of value ownership semantics

view duplication = duplication of READ capability
```

Hai khái niệm này phải tiếp tục độc lập.

---

# 34. Mutable view is move-only

```axiom
let a = mut_view(buffer)
let b = a
```

sau đó:

```axiom
use(a)
```

→ invalid.

Không thể có hai mutable capability cùng region trong safe code.

---

# 35. Range expressions

Các dạng:

```axiom
a..b
a..=b
a..
..b
..=b
..
```

có semantic range value.

`a..b`:

```text
[start, end)
```

`a..=b`:

```text
[start, end]
```

Range endpoints được evaluate left-to-right.

Ví dụ:

```axiom
start()..end()
```

→

```text
start()
end()
```

---

# 36. Pattern semantics

Pattern được sử dụng trong:

```axiom
let
match
```

và về sau có thể mở rộng sang:

```text
if let
while let
for pattern in iterable
```

Pattern không phải expression thông thường.

Pattern có nhiệm vụ:

```text
inspect
decompose
bind
move/copy/view
```

---

# 37. Irrefutable patterns

Pattern irrefutable luôn match.

Ví dụ:

```axiom
let x = value
```

`x` là binding pattern.

Struct destructuring:

```axiom
let Vec2 { x, y } = point
```

luôn thành công nếu type đúng.

---

# 38. Refutable patterns

Pattern refutable có thể fail.

Ví dụ:

```axiom
match value {
    Some(x) => ...
    None => ...
}
```

`Some(x)` không phải lúc nào match.

Compiler yêu cầu `match` phải exhaustive.

---

# 39. Match scrutinee evaluated once

```axiom
match get_message() {
    Message.Quit => ...
    Message.Text(t) => ...
}
```

`get_message()` chỉ chạy **một lần**.

Không có việc mỗi arm evaluate lại scrutinee.

---

# 40. Match evaluation

Semantic:

```text
1. evaluate scrutinee
2. determine matching pattern
3. evaluate guard nếu có
4. bind pattern variables
5. execute selected arm
6. cleanup bindings/temporaries
```

Chỉ một arm được execute.

---

# 41. Match guards

Axiom v0.1 cho phép guard:

```axiom
match value {
    Some(x) if x > 10 => ...
    Some(x) => ...
    None => ...
}
```

Guard phải có type:

```text
bool
```

Guard được evaluate **sau khi pattern match**.

---

# 42. Guard restrictions

Guard không được làm thay đổi pattern matching semantics bằng ownership trick.

Đặc biệt, guard không được:

- move giá trị đã bind nếu việc đó làm pattern binding không còn hợp lệ;
- tạo capability sống vượt qua arm nếu provenance không hợp lệ;
- phá vỡ exhaustive analysis;
- thay đổi scrutinee.

Ví dụ:

```axiom
match resource {
    Resource(x) if consume(x) => ...
    ...
}
```

chỉ hợp lệ nếu ownership semantics của `x` cho phép.

Compiler không coi guard như một vùng "ngoài hệ thống ownership".

---

# 43. Destructuring

Struct:

```axiom
let Vec2 { x, y } = point
```

có thể:

- copy field nếu field `Copy`;
- move field nếu field non-Copy;
- bind view khi pattern/context yêu cầu view semantics.

Compiler phải tracking từng field.

---

# 44. Enum destructuring

Ví dụ:

```axiom
match message {
    Message.Text(text) => print(text)
    Message.Move { x, y } => move_to(x, y)
    Message.Quit => stop()
}
```

Payload được bind theo ownership rules.

Không có hidden deep copy.

---

# 45. Pattern binding default

Binding mặc định tuân theo expression ownership semantics:

```text
Copy type    → Copy
non-Copy     → Move
```

Ví dụ:

```axiom
match user {
    User { name, age } => ...
}
```

nếu `name: Text` thì `name` được move nếu pattern context sở hữu payload.

---

# 46. Explicit view pattern

Khi muốn đọc mà không move:

```axiom
match view(user) {
    ...
}
```

hoặc dùng API/pattern form được định nghĩa để bind capability.

Nguyên tắc:

> **Pattern không được âm thầm chuyển MOVE thành READ.**

Nếu programmer muốn giữ owner, phải có semantic indication phù hợp.

---

# 47. Wildcard

```axiom
_
```

không bind tên và không tạo ownership obligation.

Ví dụ:

```axiom
match result {
    Ok(_) => ...
    Err(_) => ...
}
```

Nếu payload non-Copy, `_` có thể được tiêu thụ theo semantic pattern mà không tạo binding; compiler phải đảm bảo resource vẫn được cleanup đúng.

---

# 48. Partial move through patterns

Được phép với type có compiler-derived Drop.

Ví dụ:

```axiom
struct User {
    name: Text
    age: i32
}

let User { name, age } = user
```

Sau đó `age` có thể tiếp tục tồn tại độc lập.

Nếu `User` có user-defined `Drop`, partial move bị cấm.

Điều này giữ invariant:

> compiler không phải chạy custom destructor trên một object đang ở trạng thái không hoàn chỉnh.

---

# 49. Pattern + Copy

Nếu field:

```axiom
age: i32
```

thì:

```axiom
let User { age, ... } = user
```

có thể copy `age`, owner `user` vẫn còn hợp lệ đối với field đó.

---

# 50. Pattern + view

Pattern trên:

```axiom
view(user)
```

không được move owned payload.

Ví dụ:

```axiom
let u = User { ... }

match view(u) {
    User { name, ... } => use(name)
}
```

`name` ở đây phải giữ semantics của READ capability.

Không được biến thành ownership transfer.

---

# 51. `?` operator

`?` là control-flow operator.

Ví dụ:

```axiom
let value = parse(text)?
```

conceptually:

```axiom
match parse(text) {
    Ok(v) => v
    Err(e) => return Err(e)
}
```

Nhưng compiler phải thực hiện cleanup đúng ownership semantics trước khi return.

---

# 52. `?` is not exception handling

Không có:

```text
throw
catch
exception object
stack unwinding bắt buộc
```

`?` chỉ là:

```text
pattern match + early return
```

Điều này cho phép compiler lower trực tiếp thành branch.

---

# 53. `?` and ownership

Ví dụ:

```axiom
fn process() -> Result<Output, Error> {
    let a = acquire_a()?
    let b = acquire_b()?

    produce(a, b)
}
```

Nếu `acquire_b()` fail:

```text
Drop b temporary if needed
Drop a
return Err(...)
```

Cleanup deterministic.

Không được leak `a`.

---

# 54. `?` conversion

`?` chỉ cho phép direct compatible error conversion.

Ví dụ:

```axiom
Result<T, E1>
```

vào function trả:

```axiom
Result<T, E2>
```

chỉ hợp lệ nếu compiler tìm thấy conversion trực tiếp được phép, ví dụ:

```axiom
impl From<E1> for E2
```

Không chạy một chuỗi conversion dài.

---

# 55. `panic`

```axiom
panic("invalid state")
```

có type:

```text
never
```

Nó không return.

Do đó:

```axiom
let x: i32 =
    if condition {
        10
    } else {
        panic("invalid")
    }
```

hợp lệ.

---

# 56. `never`

`never` là bottom-like control-flow type.

Các expression:

```axiom
panic(...)
unreachable()
return ...
break ...
continue ...
```

không tạo một normal value.

Compiler có thể dùng chúng trong type checking mà không cần runtime conversion.

---

# 57. `return` as expression control flow

`return x` không tạo value của function expression.

Nó kết thúc control-flow path.

Ví dụ:

```axiom
fn test(x: i32) -> i32 {
    if x < 0 {
        return 0
    }

    x
}
```

compiler xem:

```text
return 0
```

là terminating path.

---

# 58. `break` and `continue`

v0.1:

```axiom
break
continue
```

không có value.

Do đó:

```axiom
let x = loop {
    break 10
}
```

**không hợp lệ trong v0.1**.

Nếu sau này cần value-producing loop, đó là một semantic extension riêng, không được âm thầm thêm vào.

---

# 59. `comptime` expression

`comptime` sử dụng cùng expression semantics với runtime:

```text
same types
same ownership rules
same evaluation order
same overflow semantics
same pattern semantics
```

Ví dụ:

```axiom
const SIZE = comptime calculate_size()
```

Không được có:

```text
runtime semantics ≠ comptime semantics
```

trừ những operation bị capability system giới hạn.

---

# 60. Compile-time side effects

Comptime có thể có side effects trên compile-time resources nếu capability đã được cấp.

Nhưng:

```text
compile-time resource
```

không được tự động trở thành:

```text
runtime resource
```

Ví dụ file handle mở trong comptime không được escape thành runtime `File`.

---

# 61. Constant folding

Compiler có thể biến:

```axiom
let x = 10 * 20 + 5
```

thành:

```text
205
```

nhưng semantic result phải giống evaluation bình thường.

Nếu expression có side effect:

```axiom
foo() + bar()
```

không được constant-fold theo kiểu làm mất observable calls.

---

# 62. Expression optimization boundary

Compiler được phép:

- constant fold
- dead-code eliminate
- common-subexpression eliminate
- inline
- scalarize aggregate
- eliminate temporary
- eliminate allocation
- eliminate proven bounds checks
- reorder machine instructions

miễn là giữ:

```text
observable result
observable side effects
Drop behavior
panic/trap behavior
atomic ordering
volatile semantics
FFI semantics
```

---

# 63. Observable side effects

Axiom coi những thứ sau là observable semantic effects:

```text
I/O
volatile access
atomic operations
synchronization
FFI calls
panic/trap
resource cleanup
externally visible memory effects
program termination
```

Do đó compiler không được loại bỏ/reorder chúng tùy ý.

---

# 64. Function calls are not pure by default

Compiler không được giả định:

```axiom
foo()
```

là pure chỉ vì không thấy mutation trực tiếp.

Nếu function có side effects, evaluation order phải được giữ.

Pure-function optimization chỉ được phép khi compiler có semantic proof/effect information.

---

# 65. No hidden dereference

Axiom không có implicit pointer dereference kiểu:

```text
*p → p.field → tự động dereference
```

Raw pointer operations phải explicit trong unsafe/system code.

Điều này giúp:

```text
source semantics
```

không phụ thuộc vào một chuỗi implicit memory operations khó quan sát.

---

# 66. No implicit numeric conversion

Không có:

```text
i32 → i64 → f64 → custom type
```

conversion chain.

Mọi semantic conversion phải explicit:

```axiom
x as i64
x as f64
```

hoặc trait conversion rõ ràng.

---

# 67. `as` conversion

`as` được chia semantic thành các nhóm:

```text
numeric conversion
pointer conversion
enum/tag conversion
representation conversion
```

Compiler không cho phép một `as` expression tùy tiện làm mọi thứ.

Ví dụ:

```axiom
u64 as i32
```

có semantics được xác định rõ, bao gồm overflow/truncation behavior.

Pointer conversions thường yêu cầu `unsafe`.

---

# 68. `bit_cast`

```axiom
bit_cast<T>(value)
```

không phải semantic numeric conversion.

Nó yêu cầu representation compatibility:

```text
sizeof(source) == sizeof(destination)
alignment/validity constraints satisfied
```

`bit_cast` không được dùng để bypass ownership/lifetime safety.

---

# 69. No general `transmute`

Axiom v0.1 không có:

```axiom
transmute<T>(x)
```

một cách unrestricted.

Thay vào đó:

```text
as
bit_cast
ptr_cast
addr_cast
reinterpret_bytes
```

mỗi mechanism có semantic contract riêng.

Điều này phù hợp với nguyên tắc:

> **One Semantic Question, One Mechanism.**

---

# 70. Expression purity is not syntax

Axiom không dùng keyword kiểu:

```text
pure
```

trong v0.1 để thay đổi semantics.

Nếu sau này cần effect system, nó phải là semantic metadata/compiler analysis, không làm cho hai evaluation model khác nhau.

---

# 71. Expression semantic invariants

### AEXPR-20 — Evaluation Is Deterministic

Mọi expression có thứ tự evaluation được xác định.

### AEXPR-21 — Evaluation Order Is Left-To-Right

Các operand/subexpression được evaluate theo thứ tự trái → phải trừ các construct có control-flow semantics riêng.

### AEXPR-22 — Function Arguments Are Evaluated Once

Mỗi argument được evaluate đúng một lần.

### AEXPR-23 — Short-Circuit Is Semantic

`&&` và `||` không evaluate operand bị short-circuit.

### AEXPR-24 — Assignment Produces Unit

Assignment không tạo giá trị để chain.

### AEXPR-25 — Assignment Evaluates Destination Once

Destination của assignment/compound assignment không bị evaluate nhiều lần.

### AEXPR-26 — No Implicit Numeric Conversion

Numeric conversion phải explicit.

### AEXPR-27 — Operator Resolution Is Deterministic

Overload resolution không dựa trên implicit conversion ranking.

### AEXPR-28 — Control-Flow Operators Are Not Overloadable

Các operator có semantic control flow không thể bị user redefine.

### AEXPR-29 — Bounds Safety Is Semantic

Safe indexing luôn giữ bounds safety.

### AEXPR-30 — Bounds Checks May Be Eliminated

Compiler có thể bỏ bounds check khi chứng minh được safety.

### AEXPR-31 — Move Is An Ownership Transition

Move không yêu cầu physical memory copy.

### AEXPR-32 — Copy Is Semantic Duplication

Copy không yêu cầu physical memory copy.

### AEXPR-33 — Clone Is Explicit

Expensive/resource duplication không được compiler tự thêm.

### AEXPR-34 — Temporary Lifetime Preserves Observable Semantics

Temporary không được bị destroy trước semantic last-use.

### AEXPR-35 — Compiler May Shorten Physical Storage Lifetime

Miễn observable semantics không thay đổi.

### AEXPR-36 — View Conversion Is Explicit Except Call Boundary

Owner→view implicit conversion chỉ được phép tại ephemeral call boundary.

### AEXPR-37 — Mutable Capability Is Exclusive

Safe code không tạo overlapping mutable capabilities.

### AEXPR-38 — Match Scrutinee Is Evaluated Once

Scrutinee của `match` chỉ evaluate một lần.

### AEXPR-39 — Match Is Exhaustive

Mọi path của algebraic type phải được xử lý hoặc cover bằng wildcard hợp lệ.

### AEXPR-40 — Pattern Binding Preserves Ownership Semantics

Pattern không được âm thầm biến move thành copy hoặc read.

### AEXPR-41 — Partial Move Is Field-Precise

Partial move được tracking theo field/region.

### AEXPR-42 — Custom Drop Forbids Partial Move

Type có user-defined Drop không thể bị partial move.

### AEXPR-43 — Guard Cannot Bypass Ownership

Match guard vẫn chịu ownership/capability verification.

### AEXPR-44 — Question Mark Is Control Flow

`?` là early-return control flow, không phải exception.

### AEXPR-45 — Question Mark Preserves Cleanup

`?` không được bỏ qua cleanup của các owner đang sống.

### AEXPR-46 — Panic Has Never Type

`panic` không tạo normal value.

### AEXPR-47 — Never Has No Runtime Value

`never` biểu diễn terminating control-flow path.

### AEXPR-48 — Break Has No Value

`break` không tạo expression value trong v0.1.

### AEXPR-49 — Comptime Uses The Same Expression Semantics

Compile-time và runtime dùng cùng semantic model.

### AEXPR-50 — Constant Folding Preserves Semantics

Constant folding không được thay đổi observable behavior.

### AEXPR-51 — Optimization Preserves Observable Effects

Optimization không được loại bỏ/reorder semantic side effects trái phép.

### AEXPR-52 — No Hidden Dereference

Raw-pointer dereference không tự động xảy ra trong safe expression semantics.

### AEXPR-53 — Bit Cast Is Representation Conversion

`bit_cast` không phải numeric conversion.

### AEXPR-54 — Unrestricted Transmutation Is Not Core

Không có unrestricted type reinterpretation.

---

# 72. Ví dụ tổng hợp

```axiom
fn process(values: mut_view<i32>) -> Result<i32, Error> {
    var sum = 0

    for i in 0..values.len() {
        let x = values[i]

        if x < 0 {
            return Err(Error.InvalidValue)
        }

        sum += x
    }

    Ok(sum)
}
```

Semantic:

```text
values
  ↓
mutable capability
  ↓
loop
  ↓
index bounds verified
  ↓
read x
  ↓
checked arithmetic
  ↓
Result
```

Compiler có thể chứng minh:

```text
i < values.len()
```

và loại bỏ bounds check trong loop.

Không cần programmer viết:

```text
unsafe
```

chỉ để đạt performance.

---

# 73. Ví dụ ownership + `?`

```axiom
fn build() -> Result<Output, Error> {
    let config = load_config()?
    let data = load_data(&config)?
    let result = process(data)?

    Ok(result)
}
```

Về mặt semantic:

```text
load_config
    ↓
config owns resource
    ↓
load_data
    ↓
if failure:
    Drop config
    return Err
    ↓
process
    ↓
if failure:
    Drop remaining owners
    return Err
```

Nhưng source không phải viết:

```text
try
catch
finally
defer
```

Compiler quản lý cleanup.

Đây chính xác là triết lý:

> **Programmer quản lý ownership; compiler quản lý lifetime.**

---

# 74. Một quyết định quan trọng: không thêm `auto-ref` tổng quát

Sau khi khóa Part IX, tôi đề xuất **không thêm cơ chế kiểu Rust `&T`/`&mut T` hoặc auto-borrow/reborrow tổng quát vào Axiom v0.1**.

Axiom đã có:

```text
T
view<T>
mut_view<T>
```

và:

```axiom
foo(x)
```

tự tạo ephemeral view nếu parameter yêu cầu.

Như vậy:

```axiom
fn sum(x: view<i32>) -> i32
```

gọi:

```axiom
sum(array)
```

đủ rõ.

Không cần:

```text
&array
&mut array
&&array
&*x
reborrow
lifetime parameter
```

Đây là một trong những điểm có thể làm Axiom đơn giản hơn Rust mà vẫn giữ được phần lớn safety property quan trọng.

---

# 75. Kết luận Part IX

Sau phần này, expression semantics của Axiom đã có nền khá chặt:

```text
             Expression
                  │
        ┌─────────┴─────────┐
        │                   │
      VALUE              PLACE
        │                   │
      Copy/Move          Read/Write
        │                   │
        └───────┬───────────┘
                │
           Capability
          /           \
       view         mut_view
```

và control flow:

```text
expression
   │
   ├── normal value
   ├── move
   ├── copy
   ├── capability
   ├── Result/Option
   ├── panic
   ├── return
   ├── break
   └── continue
```

Không còn các vùng "compiler tự đoán" nguy hiểm về:

- evaluation order
- ownership
- implicit conversion
- temporary lifetime
- short-circuit
- pattern binding
- bounds safety
- `?`
- operator overload.

Đặc biệt, Axiom đang giữ được một cân bằng quan trọng:

> **Source language không bắt programmer quản lý compiler machinery, nhưng compiler vẫn có đủ semantic information để tối ưu rất sâu.**

---

# Part X — Functions · Closures · Calling Semantics

Phần tiếp theo cần khóa sâu hơn **function/closure model**, vì đây là nơi các quyết định về ownership, ABI, generic, `view`, `mut_view`, async và optimization gặp nhau.

Các điểm sẽ được khóa:

```text
1. Function declaration semantics
2. Parameter passing
3. Return values
4. Named vs positional arguments
5. Default arguments
6. Variadic functions
7. Generic functions
8. Function values
9. Function pointers
10. Closures
11. Capture modes
12. move closures
13. closure lifetime
14. closure → function pointer
15. non-capturing closure
16. escaping closure
17. recursive functions
18. tail calls
19. calling convention
20. ABI lowering
21. indirect calls
22. dyn Trait calls
23. generic monomorphization
24. async functions
25. function effects
26. `unsafe fn`
27. `extern fn`
28. `comptime fn`
29. `never` returns
30. function contracts
```

Điểm đặc biệt cần giải quyết ở Part X là **closure**: Axiom không có GC và không muốn lifetime syntax, nhưng vẫn phải cho phép:

```axiom
fn make_counter() -> fn() -> i32 {
    var n = 0

    || {
        n += 1
        n
    }
}
```

mà không biến closure thành một object có hidden runtime machinery.

Đây sẽ là một trong những phần quyết định Axiom có thực sự đạt được mục tiêu **"high-level nhưng native"** hay không.