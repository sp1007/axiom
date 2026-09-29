Tiếp theo là **BOOTSTRAP-010 — Enum + Match + Algebraic Data Model**. Đây là bước rất quan trọng vì `enum`, `Option`, `Result`, pattern matching và sau này cả niche optimization đều phụ thuộc vào nó.

# BOOTSTRAP-010 — AXIOM0 ENUM + MATCH

## 1. Quyết định kiến trúc

> **Enum là algebraic sum type. `match` là exhaustive pattern dispatch. Representation của enum thuộc Layout/ABI, không thuộc semantic MIR.**

Hai khái niệm phải tách:

```text
Enum semantics
    ↓
Variant identity
    ↓
Pattern matching
    ↓
MIR control flow
    ↓
Layout
    ↓
Tag / payload / niche representation
```

Ví dụ:

```axiom
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

Về semantic level, đây đơn giản là:

```text
Result = Ok(value) | Err(error)
```

Không cần biết runtime representation là:

```text
tag + payload
```

hay:

```text
niche encoding
```

hay một representation khác.

---

# 2. Enum identity

Ví dụ:

```axiom
enum Color {
    Red,
    Green,
    Blue,
}
```

Compiler tạo:

```text
EnumId(Color)
VariantId(Color.Red)
VariantId(Color.Green)
VariantId(Color.Blue)
```

Variant identity phải ổn định.

Không dùng số tag vật lý làm semantic identity.

---

# 3. Enum có thể chứa dữ liệu

Unit variant:

```axiom
enum Color {
    Red,
    Green,
}
```

Payload variant:

```axiom
enum Message {
    Quit,
    Number(i32),
    Text(String),
}
```

Mỗi variant có danh sách field riêng.

Internal model:

```text
VariantDef {
    id
    name
    fields[]
}
```

Ví dụ:

```text
Message
 ├── Quit
 ├── Number
 │    └── field0 : i32
 └── Text
      └── field0 : String
```

---

# 4. Variant không phải class/object

Ví dụ:

```axiom
let m = Message::Number(42);
```

không tạo:

```text
object header
vtable
GC metadata
runtime type pointer
```

Nó chỉ là một value có semantic variant.

---

# 5. Construct enum

Source:

```axiom
let m = Message::Number(42);
```

HIR:

```text
EnumConstruct {
    enum = Message
    variant = Number
    fields = [42]
}
```

MIR:

```text
%0 = enum_construct Message::Number(42)
```

Ở semantic MIR chưa cần nói:

```text
tag = 1
```

---

# 6. `match`

Ví dụ:

```axiom
fn value(m: Message) -> i32 {
    match m {
        Message::Quit => 0,
        Message::Number(n) => n,
        Message::Text(_) => -1,
    }
}
```

Compiler kiểm tra:

```text
Message::Quit
Message::Number
Message::Text
```

đã bao phủ toàn bộ enum.

Sau đó lower thành CFG.

Ví dụ conceptually:

```text
bb0:
    switch_variant m

bb1:
    // Quit
    return 0

bb2:
    // Number
    return n

bb3:
    // Text
    return -1
```

MIR không cần giữ high-level pattern matching.

---

# 7. Exhaustiveness là bắt buộc

Ví dụ:

```axiom
enum Color {
    Red,
    Green,
    Blue,
}

fn f(c: Color) -> i32 {
    match c {
        Color::Red => 1,
        Color::Green => 2,
    }
}
```

→ compile error.

Không được tự động sinh:

```text
default -> unreachable
```

trừ khi compiler chứng minh variant đó impossible.

---

# 8. Wildcard

Cho phép:

```axiom
match color {
    Color::Red => 1,
    _ => 0,
}
```

`_` có nghĩa:

> mọi pattern còn lại.

Compiler vẫn phải kiểm tra exhaustiveness.

---

# 9. Binding pattern

Ví dụ:

```axiom
match message {
    Message::Number(n) => n,
    _ => 0,
}
```

`n` là binding mới.

Ownership của `n` phụ thuộc pattern semantics.

Ví dụ enum chứa:

```text
String
```

nếu match theo move:

```axiom
match message {
    Message::Text(s) => use(s),
    ...
}
```

thì payload có thể được move ra.

---

# 10. Không copy payload vô điều kiện

Điểm này rất quan trọng.

```axiom
enum Message {
    Text(String),
}
```

Không được biến:

```axiom
Message::Text(s)
```

thành một physical copy của `String`.

Pattern matching phải tương thích ownership model.

---

# 11. Match theo reference/view

Khi cần inspect mà không consume value, sử dụng capability:

```axiom
match view(message) {
    ...
}
```

hoặc API/pattern lowering tương ứng.

Mục tiêu là:

```text
inspect
≠
consume
```

Compiler phải phân biệt hai trường hợp.

---

# 12. Match trên struct

Pattern có thể match struct:

```axiom
match point {
    Point { x: 0, y: 0 } => 1,
    Point { x, y } => x + y,
}
```

Compiler thực hiện:

```text
struct field projection
+
value comparison
+
binding
```

Không cần runtime reflection.

---

# 13. Nested pattern

Cho phép:

```axiom
match result {
    Result::Ok(Point { x, y }) => x + y,
    Result::Err(_) => 0,
}
```

Semantic lowering:

```text
match Result variant
        ↓
match Point fields
        ↓
bind x/y
        ↓
execute branch
```

---

# 14. Literal pattern

Ví dụ:

```axiom
match x {
    0 => 10,
    1 => 20,
    _ => 30,
}
```

Compiler có thể lower thành:

```text
switch x
```

hoặc:

```text
if x == 0
...
```

Backend quyết định tối ưu.

---

# 15. Range pattern

Đã có syntax:

```axiom
0..=9
```

Ví dụ:

```axiom
match x {
    0..=9 => 1,
    10..=99 => 2,
    _ => 3,
}
```

Verifier phải kiểm tra range hợp lệ theo type.

Không cho phép:

```axiom
10..=5
```

trừ khi semantics tương lai định nghĩa range ngược; v1 nên reject.

---

# 16. Match guard

Tôi đề xuất **chưa đưa guard tùy ý vào semantic core Stage-0**.

Ví dụ:

```axiom
Some(x) if x > 10 => ...
```

có thể hỗ trợ sau.

Lý do không phải vì guard khó về syntax.

Mà vì exhaustiveness analysis và usefulness analysis phức tạp hơn đáng kể.

Stage-0 nên hoàn thành:

```text
variant
literal
tuple
struct
binding
_
range
```

trước.

---

# 17. Pattern matrix

Compiler nên có một abstraction riêng:

```text
Pattern Matrix
```

thay vì hard-code:

```text
if enum
if struct
if tuple
...
```

Pipeline:

```text
Patterns
   ↓
Pattern Matrix
   ↓
Usefulness / Exhaustiveness
   ↓
Decision Tree
   ↓
MIR CFG
```

Đây là kiến trúc tốt hơn cho compiler về lâu dài.

---

# 18. Decision tree

Ví dụ:

```axiom
match x {
    0 => A,
    1 => B,
    2 => C,
    _ => D,
}
```

Compiler có thể tạo:

```text
        x
     /  |  \
    0   1   2
    A   B   C
     \  |  /
       D
```

Backend có thể chọn:

```text
if/else
binary search
jump table
bit test
```

Semantic MIR chỉ cần biểu diễn control flow hợp lệ.

---

# 19. Enum layout

Đây là nơi BOOT-009 Layout Engine mở rộng.

Có hai representation chính:

### Tagged representation

```text
+--------+-------------+
|  tag   |   payload   |
+--------+-------------+
```

Ví dụ:

```text
0 = Quit
1 = Number
2 = Text
```

### Niche representation

Compiler có thể tận dụng những bit-pattern không hợp lệ của payload.

Ví dụ conceptually:

```text
Option<NonNull<T>>
```

có thể biểu diễn `None` bằng một pointer value không hợp lệ cho `Some`.

Nhưng:

> Đây là optimization/layout decision, không phải semantic rule của `Option`.

---

# 20. `Option<T>`

Định nghĩa hoàn toàn bằng enum:

```axiom
enum Option<T> {
    Some(T),
    None,
}
```

Không cần compiler primitive `Option`.

Compiler chỉ cần hiểu:

```text
enum
pattern
ownership
niche optimization
```

Sau đó stdlib định nghĩa `Option`.

Đây là một ví dụ rất mạnh của:

> **Compiler primitive tối thiểu, nhưng semantic capability mạnh.**

---

# 21. `Result<T,E>`

Tương tự:

```axiom
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

`?` sau này chỉ là syntax/control-flow sugar.

Ví dụ:

```axiom
let x = foo()?;
```

lower thành:

```text
result = foo()

switch result:
    Ok(v):
        x = v

    Err(e):
        cleanup
        return Err(e)
```

Không có exception runtime.

---

# 22. Enum ownership

Ví dụ:

```axiom
enum Resource {
    Empty,
    File(FileHandle),
}
```

Nếu:

```text
Resource::File(handle)
```

được move:

```text
Resource ownership
      ↓
payload ownership
```

Compiler phải theo dõi variant state.

Không được drop payload của tất cả variant.

---

# 23. Drop enum

Ví dụ:

```axiom
enum Resource {
    None,
    File(File),
    Socket(Socket),
}
```

Khi Drop:

```text
switch active variant
    ↓
drop only active payload
```

Không được:

```text
drop File
drop Socket
```

vì chỉ một variant tồn tại.

---

# 24. Partial move trong enum

Ví dụ:

```axiom
enum Message {
    Pair(String, String),
}
```

Có thể conceptual state:

```text
Message::Pair(
    field0 = Owned,
    field1 = Moved
)
```

nếu enum không có custom Drop và semantics cho phép.

Sau đó có thể reinitialize field.

Nhưng custom Drop tiếp tục chịu restriction tương tự struct.

---

# 25. Enum + capability

Nếu:

```axiom
let v = view(message);
```

thì capability phải gắn với:

```text
message
```

và active variant/payload region.

Ví dụ:

```text
view<Message::Text payload>
```

không được tồn tại nếu variant đó không còn active.

Đây là một lý do enum state phải được biểu diễn trong semantic facts.

---

# 26. Enum discriminant không nhất thiết là integer field

Không nên expose trong Core:

```axiom
enum_value(x)
```

với giả định:

```text
enum_value = physical tag
```

Nếu cần discriminant cho FFI/ABI, đó là representation-level API.

Ví dụ `@repr(u8)` có thể được bổ sung để yêu cầu discriminant representation.

---

# 27. `@repr(u8)` / integer repr

Nên chuẩn bị kiến trúc cho:

```axiom
@repr(u8)
enum Color {
    Red,
    Green,
    Blue,
}
```

Khi đó ABI/layout bị ràng buộc.

Nhưng Stage-0 có thể chưa implement.

Mục đích là:

```text
Enum semantics
≠
Discriminant representation
```

tiếp tục được giữ sạch.

---

# 28. Invalid enum states

Safe Axiom không được cho phép tạo arbitrary invalid enum value.

Ví dụ nếu:

```text
Color = Red | Green | Blue
```

thì một bit pattern ngoài tập hợp hợp lệ không phải là một `Color` hợp lệ.

Raw memory construction:

```text
bytes → Color
```

phải nằm trong unsafe/FFI boundary và phải establish validity trước khi đưa trở lại safe semantic world.

---

# 29. MIR representation

Semantic MIR có thể dùng:

```text
ENUM_CONSTRUCT
SWITCH_VARIANT
EXTRACT_VARIANT_FIELD
```

nhưng đây là **semantic operations**, không phải physical tag loads.

Ví dụ:

```text
bb0:
    %m = enum_construct Message::Number(42)

bb1:
    switch_variant %m
        Number → bb2
        Quit   → bb3
        Text   → bb4
```

Sau đó optimization/layout lowering mới biến thành:

```text
load tag
cmp
branch
```

hoặc jump table/niche test.

---

# 30. Pattern compiler phải độc lập Layout

Ví dụ:

```axiom
match x {
    Option::None => 0,
    Option::Some(v) => v,
}
```

Pattern compiler chỉ biết:

```text
None
Some
```

Không biết:

```text
None = pointer 0
```

Điều này cho phép sau này thay đổi enum representation mà không phá frontend.

---

# 31. Exhaustiveness algorithm

Stage-0 có thể triển khai algorithm đơn giản trước:

### Enum

```text
variants covered?
```

### Bool

```text
true / false
```

### Tuple

```text
cross-product of component patterns
```

### Struct

```text
all fields covered
```

### Integer/range

Stage-0 có thể kiểm tra interval coverage.

Ví dụ:

```text
0..=9
10..=99
_
```

đầy đủ.

Nhưng:

```text
0..=9
20..=99
_
```

vẫn exhaustive vì `_`.

Không có `_`:

```text
0..=9
20..=99
```

→ thiếu `10..19`.

---

# 32. Diagnostics

Đề xuất:

```text
AX1701 non-exhaustive match
AX1702 unreachable pattern
AX1703 overlapping pattern
AX1704 invalid pattern
AX1705 impossible pattern
AX1706 invalid range
AX1707 unknown enum variant
AX1708 variant payload mismatch
AX1709 moved value used in pattern
AX1710 invalid enum construction
```

Compiler không cần đưa ra message dài dòng; quan trọng là:

```text
code
severity
span
expected
actual
related spans
```

---

# 33. Test ladder

### Enum cơ bản

```axiom
enum Color {
    Red,
    Green,
    Blue,
}
```

### Construction

```axiom
let c = Color::Red;
```

### Match

```axiom
match c {
    Color::Red => 1,
    Color::Green => 2,
    Color::Blue => 3,
}
```

→ `1`.

### Exhaustiveness fail

```axiom
match c {
    Color::Red => 1,
}
```

→ compile fail.

### Wildcard

```axiom
match c {
    Color::Red => 1,
    _ => 0,
}
```

### Payload

```axiom
enum Value {
    Int(i32),
    Bool(bool),
}
```

### Nested

```axiom
Option<Result<i32, Error>>
```

### Ownership

```text
move payload
use moved payload → error
```

### Drop

```text
only active variant payload is dropped
```

### Range

```text
0..=9
10..=19
_ 
```

### Optimization

```text
match constant enum → constant result
```

---

# 34. Invariants BOOT-010

```text
AENUM-20  Enum Identity Is Nominal
AENUM-21  Variant Identity Is Stable
AENUM-22  Variant Payloads Have Explicit Types
AENUM-23  Enum Construction Is Type Checked
AENUM-24  Match Is An Exhaustive Control-Flow Construct
AENUM-25  Non-Exhaustive Match Is A Compile Error
AENUM-26  Wildcard Covers Remaining Patterns
AENUM-27  Pattern Bindings Have Normal Ownership Semantics
AENUM-28  Matching Does Not Implicitly Copy Non-Copy Payloads
AENUM-29  Enum Payload Ownership Is Variant Sensitive
AENUM-30  Only Active Variant Payloads Are Dropped
AENUM-31  Enum Representation Is Separate From Enum Semantics
AENUM-32  Discriminant Representation Is Layout Controlled
AENUM-33  Niche Optimization Is Representation Only
AENUM-34  Invalid Enum States Cannot Exist In Safe Code
AENUM-35  Raw Enum Construction Requires Validity Proof
AENUM-36  Pattern Matching Is Independent Of Physical Tag Layout
AENUM-37  Match Lowering Produces Ordinary MIR CFG
AENUM-38  Pattern Compiler Is Independent Of Machine Representation
AENUM-39  Struct Patterns Use Field Identity
AENUM-40  Tuple Patterns Preserve Tuple Semantics
AENUM-41  Range Patterns Are Type Checked
AENUM-42  Unreachable Patterns Are Diagnosable
AENUM-43  Overlapping Patterns Are Diagnosable
AENUM-44  Option Is A Library Enum
AENUM-45  Result Is A Library Enum
AENUM-46  Question-Mark Propagation Is Control Flow
AENUM-47  Enum Drop Is Deterministic
AENUM-48  Partial Move Follows Aggregate Ownership Rules
AENUM-49  Custom Drop Restricts Partial Move
AENUM-50  Enum Semantics Do Not Require Runtime Type Metadata
```

---

# 35. BOOT-010 gate

Milestone chỉ pass khi toàn bộ pipeline này chạy được:

```text
Source
  ↓
Lexer
  ↓
Parser
  ↓
Resolver
  ↓
Type Checker
  ↓
Pattern Checker
  ↓
HIR
  ↓
Ownership Verification
  ↓
MIR
  ↓
MIR Interpreter
  ↓
x86-64 Codegen
  ↓
Native
```

với:

```text
enum declaration
enum construction
variant payload
match
exhaustiveness
wildcard
bindings
nested patterns
range patterns
ownership
drop
Option-like enum
Result-like enum
```

và đặc biệt phải có differential test:

```text
MIR Interpreter
       ==
Native Executable
```

ở:

```text
-O0
-O1
-O2
-O3
```

---

## Một điểm kiến trúc đáng chú ý

Sau BOOT-010, Axiom đã có đủ ba loại aggregate/algebraic cơ bản:

```text
struct   → Product Type
enum     → Sum Type
tuple    → Anonymous Product Type
```

và semantic expression model lúc này trở nên khá hoàn chỉnh:

```text
Expression
    │
    ├── VALUE
    │
    ├── PLACE
    │
    └── CONTROL FLOW
```

Trong đó:

```text
struct.field
array[index]
tuple.0
enum payload
```

đều có thể quy về **Place/Projection** khi cần.

Đây là nền rất tốt để bước tiếp theo xử lý **Option/Result + `?` + cleanup**, sau đó mới đi sâu hơn vào **ownership/capability thực chiến** thay vì phải sửa lại MIR sau này.