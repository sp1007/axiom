Được. Bây giờ ta chuyển hẳn sang **AXIOM HIR v0.1**. Đây là bước quan trọng vì từ đây Axiom bắt đầu có một representation đủ cụ thể để AI agent có thể code compiler.

# AXIOM HIR v0.1

## 1. HIR có nhiệm vụ gì?

Ta không nên để AST đi thẳng xuống MIR.

```text
Source
  ↓
Lexer
  ↓
AST
  ↓
HIR
  ↓
Typed HIR
  ↓
MIR
```

AST phản ánh **cú pháp programmer viết**.

HIR phản ánh **ý nghĩa chương trình sau khi compiler đã resolve**.

Ví dụ:

```axiom
v.length()
```

AST có thể vẫn là:

```text
MethodCall(
    receiver = v,
    name = "length"
)
```

Nhưng HIR phải biến nó thành:

```text
Call(
    function = length,
    args = [v]
)
```

Nếu `length` đến từ trait:

```text
Call(
    resolved_impl = Drawable::length::<Point>,
    args = [...]
)
```

Tức là sau HIR, compiler không còn phải “đoán programmer muốn gọi cái gì”.

---

# 2. Nguyên tắc HIR

HIR phải thỏa 7 nguyên tắc:

```text
HIR-01  Syntax ambiguity eliminated
HIR-02  Names resolved
HIR-03  Types resolved
HIR-04  Method/trait dispatch resolved
HIR-05  Generic constraints resolved
HIR-06  Ownership intent preserved
HIR-07  No machine-level storage decisions yet
```

Điểm cuối rất quan trọng.

HIR **không được biết**:

```text
register RAX
stack offset 32
heap pointer
x86 calling convention
```

Đó là việc của MIR/LIR/backend.

---

# 3. AST → HIR

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

AST:

```text
FunctionDecl
├── name: add
├── params
│   ├── a: i32
│   └── b: i32
├── return: i32
└── body
    └── Binary(+)
        ├── a
        └── b
```

HIR:

```text
Function
├── id: FunctionId(0)
├── params
│   ├── LocalId(0): i32
│   └── LocalId(1): i32
├── return_type: i32
└── body
    Return
        BinaryAdd
            Local(0)
            Local(1)
```

Tên biến không còn quan trọng đối với semantic pipeline.

---

# 4. HIR IDs thay vì string

Không nên để HIR liên tục chứa:

```text
"name": "user"
"name": "buffer"
"name": "length"
```

Thay vào đó:

```text
SymbolId
TypeId
FunctionId
StructId
TraitId
ImplId
LocalId
FieldId
GenericParamId
RegionId
```

Ví dụ:

```text
LocalId(17)
FieldId(4)
FunctionId(82)
```

Compiler dùng arena/interner.

Điều này giúp:

- lookup O(1)/gần O(1)
- giảm memory
- diagnostics vẫn có source mapping
- AI agent dễ debug compiler internals
- HIR không phụ thuộc string comparison.

---

# 5. HIR Type

Type system đã định nghĩa trước đây:

```text
bool
i8 ... i64
u8 ... u64
isize
usize
f32
f64
struct
enum
tuple
array
view
mut_view
function
generic
```

HIR type:

```text
Type {
    kind
    properties
}
```

Ví dụ:

```text
i32
```

→

```text
TypeId(3)
```

`Vec<i32>`:

```text
TypeId(91)
```

Không cần runtime metadata.

---

# 6. Struct HIR

Source:

```axiom
struct Point {
    x: f32
    y: f32
}
```

HIR:

```text
StructDecl {
    id: StructId(3)
    name: "Point"

    fields:
        FieldId(0)
            name = "x"
            type = f32

        FieldId(1)
            name = "y"
            type = f32
}
```

HIR vẫn giữ source order vì diagnostics/debugging cần nó.

Nhưng **không có nghĩa ABI phải giữ field order**.

Đây là hai thứ khác nhau:

```text
HIR logical order
        ≠
ABI physical layout
```

---

# 7. Method syntax biến mất ở HIR

Source:

```axiom
v.length()
```

Nếu:

```axiom
fn length(self: Vec2) -> f32
```

HIR:

```text
Call {
    function = FunctionId(length)
    args = [
        Local(v)
    ]
}
```

Không cần node `MethodCall` sau resolution.

Đây là một simplification rất lớn cho MIR.

---

# 8. Trait method

Source:

```axiom
drawable.draw()
```

Nếu resolved static dispatch:

```text
Call {
    function = ImplFunctionId(
        Drawable,
        Circle,
        draw
    )
}
```

Nếu dynamic dispatch:

```text
DynamicCall {
    trait = Drawable
    method = draw
    receiver = ...
}
```

Nhưng dynamic dispatch phải là **explicit semantic choice**, không tự phát sinh chỉ vì compiler không biết type.

---

# 9. Operators

Source:

```axiom
a + b
```

HIR không nhất thiết phải giữ:

```text
BinaryOperator("+")
```

Sau operator resolution:

```text
Call {
    function = Add::add::<T>
    args = [a, b]
}
```

Nếu intrinsic primitive:

```text
IntrinsicAdd<i32>
```

Compiler có thể hạ trực tiếp.

Điều này cho phép:

```text
user-defined operator
```

và:

```text
primitive operator
```

dùng chung resolution model.

---

# 10. Nhưng không nên biến mọi primitive thành trait call

Đây là một điểm tôi muốn giữ rất rõ.

Source:

```axiom
a + b
```

không nhất thiết phải tạo runtime function call.

HIR có thể biểu diễn:

```text
Add {
    lhs
    rhs
    resolved_operator = IntrinsicI32Add
}
```

Sau đó MIR:

```text
ADD
```

Như vậy semantic abstraction không gây overhead.

---

# 11. Place trong HIR

Đây là một khái niệm rất quan trọng.

Ví dụ:

```axiom
user.age = 20
```

`user.age` không phải đơn thuần là VALUE.

Nó là **Place**.

HIR:

```text
Store {
    target = FieldPlace {
        base = Local(user)
        field = age
    }

    value = Const(20)
}
```

Place là tiền thân của MIR `Place`.

---

# 12. Ba loại expression

HIR nên phân biệt:

```text
VALUE
PLACE
CONTROL
```

### VALUE

```axiom
x + y
```

### PLACE

```axiom
x
x.field
array[i]
```

khi xuất hiện ở vị trí cần storage.

### CONTROL

```axiom
if
match
return
break
continue
```

Không nên dùng một Expression AST khổng lồ rồi bắt mọi pass tự đoán.

---

# 13. `x` có thể là VALUE hoặc PLACE

Ví dụ:

```axiom
let y = x
```

Compiler cần biết `x` được đọc:

```text
READ(x)
```

Trong:

```axiom
x = 10
```

`x` là write-place:

```text
WRITE(x)
```

Trong:

```axiom
consume(x)
```

`x` là move-place:

```text
MOVE(x)
```

Do đó HIR nên giữ:

```text
PlaceExpr
```

và context quyết định:

```text
READ
WRITE
MOVE
```

Ownership verifier về sau mới biến nó thành capability/state cụ thể.

---

# 14. View HIR

Source:

```axiom
let v = view(x)
```

HIR:

```text
CreateView {
    source = Place(x)
    mode = READ
    type = view<T>
}
```

Mutable:

```text
CreateView {
    source = Place(x)
    mode = WRITE
    type = mut_view<T>
}
```

Đây là semantic operation.

MIR sau này có:

```text
VIEW
VIEW_MUT
```

---

# 15. Move HIR

Thông thường:

```axiom
consume(x)
```

programmer không viết:

```text
move x
```

HIR resolution dựa vào parameter mode:

```text
consume(x: Buffer)
```

→ argument requirement:

```text
MOVE
```

Do đó HIR:

```text
CallArg {
    place = x
    mode = MOVE
}
```

Nếu:

```axiom
fn read(x: view<Buffer>)
```

thì:

```text
CallArg {
    place = x
    mode = READ
}
```

---

# 16. Đây là một điểm rất mạnh

Programmer không phải viết:

```axiom
borrow(x)
move(x)
borrow_mut(x)
```

Compiler biết từ type/signature.

Ví dụ:

```axiom
fn consume(x: Buffer)
fn read(x: view<Buffer>)
fn edit(x: mut_view<Buffer>)
```

Ba API đã nói rõ capability cần thiết.

---

# 17. HIR function signature

Ta nên chuẩn hóa thành:

```text
FunctionSignature {
    id
    generic_params
    parameters
    return_type
    calling_mode
    async
    unsafe
    visibility
}
```

Parameter:

```text
Parameter {
    local_id
    type
    passing_mode
}
```

Passing mode semantic:

```text
OWN
READ_VIEW
WRITE_VIEW
COPY
```

Không cần programmer-facing keyword cho tất cả.

Compiler suy ra từ type.

---

# 18. `async`

Source:

```axiom
async fn fetch() -> Result<Data, Error> {
    ...
}
```

HIR:

```text
Function {
    flags:
        ASYNC

    body:
        ...
}
```

Chưa tạo state machine ở HIR.

State machine là MIR lowering.

---

# 19. `await`

Source:

```axiom
let x = await fetch()
```

HIR:

```text
Await {
    future = Call(fetch)
}
```

MIR mới biến:

```text
AWAIT
```

thành suspension/resume semantics.

---

# 20. `if`

Source:

```axiom
if x > 0 {
    foo()
} else {
    bar()
}
```

HIR:

```text
If {
    condition = CompareGt(x, 0)

    then:
        Call(foo)

    else:
        Call(bar)
}
```

HIR vẫn structured.

MIR mới flatten:

```text
bb0
 ├── compare
 └── branch bb1/bb2

bb1
 └── foo
      ↓
     bb3

bb2
 └── bar
      ↓
     bb3
```

---

# 21. `match`

Source:

```axiom
match shape {
    Circle(r) => area_circle(r)
    Rectangle(w, h) => area_rect(w, h)
    Point => 0
}
```

HIR:

```text
Match {
    value = shape

    arms:
        Pattern::Enum(Circle, [r])
        Pattern::Enum(Rectangle, [w, h])
        Pattern::Enum(Point)
}
```

HIR pass phải kiểm tra:

- enum tồn tại
- variant tồn tại
- pattern binding
- type correctness
- exhaustiveness
- unreachable arm.

MIR sau đó mới biến thành `SWITCH`.

---

# 22. Generic HIR

Source:

```axiom
fn max<T: Comparable>(a: T, b: T) -> T
```

HIR:

```text
Function {
    generic_params:
        T

    constraints:
        Comparable(T)

    params:
        a: T
        b: T

    return:
        T
}
```

Chưa monomorphize.

Ví dụ:

```axiom
max(1, 2)
```

specialization pass tạo:

```text
max::<i32>
```

---

# 23. Generic resolution phải xảy ra trước ownership verification

Pipeline:

```text
Source
 ↓
AST
 ↓
Name resolution
 ↓
Type resolution
 ↓
Trait resolution
 ↓
Generic resolution
 ↓
Typed HIR
 ↓
MIR
 ↓
Ownership verifier
```

Không nên để ownership verifier phải giải trait/generic.

Nếu không verifier sẽ trở thành một compiler front-end thứ hai.

---

# 24. HIR không chứa implicit runtime behavior

Ví dụ:

```axiom
let x = a + b
```

HIR có thể nói:

```text
Add<i32>
```

nhưng không nói:

```text
CALL runtime_add_i32
```

Nếu backend có instruction native:

```text
ADD
```

thì hạ thẳng.

Tương tự:

```text
bounds check
```

là semantic requirement.

HIR có thể:

```text
Index {
    array
    index
    bounds_checked = REQUIRED
}
```

Optimizer/MIR có thể chứng minh:

```text
0 <= i < N
```

và xóa check.

---

# 25. HIR phải giữ source mapping

Mọi node quan trọng nên có:

```text
SourceSpan
```

Ví dụ:

```text
Call {
    function = FunctionId(42)
    args = [...]
    span = 183..194
}
```

Diagnostics:

```text
AX_OWN_0001
use of moved value `buffer`

source:
    use(buffer)
        ^^^^^^
```

HIR/MIR vẫn phải truy được source span.

---

# 26. HIR representation đề xuất

Có thể bắt đầu bằng:

```text
HIRModule
├── imports
├── types
├── structs
├── enums
├── traits
├── impls
├── globals
└── functions
```

Function:

```text
HIRFunction
├── id
├── name
├── signature
├── generic_params
├── locals
├── body
└── source_map
```

Expression:

```text
HIRExpr
├── kind
├── type
├── category
└── span
```

Statement:

```text
HIRStmt
├── kind
└── span
```

Place:

```text
HIRPlace
├── Local
├── Field
├── Index
├── Deref      // unsafe / controlled
└── ...
```

---

# 27. Nhưng tôi không muốn HIR trở thành “MIR phiên bản cao hơn”

Đây là cái bẫy cần tránh.

HIR vẫn nên giữ:

```text
if
match
loop
for
while
closure
defer-like structured cleanup? NO
```

MIR mới flatten control flow.

HIR:

```text
while condition {
    body
}
```

MIR:

```text
header
 ↓
condition
 ↓
body
 ↓
back-edge
```

Điều này làm HIR dễ phân tích và diagnostics đẹp hơn.

---

# 28. Closure HIR

Source:

```axiom
let f = |x| x + offset
```

HIR:

```text
Closure {
    params:
        x

    captures:
        offset

    body:
        Add(x, offset)
}
```

Capture analysis:

```text
offset:
    COPY
    hoặc MOVE
    hoặc VIEW
    hoặc MUT_VIEW
```

được resolve sau type/ownership analysis.

HIR phải giữ capture information đủ để MIR tạo environment.

---

# 29. HIR `unsafe`

Source:

```axiom
unsafe {
    *p = value
}
```

HIR:

```text
UnsafeBlock {
    body:
        Store(
            Deref(p),
            value
        )
}
```

Không biến toàn bộ subtree thành “unchecked”.

Các type checks vẫn chạy.

---

# 30. HIR Error Strategy

Một compiler thực tế không nên dừng ở lỗi đầu tiên.

Ví dụ:

```axiom
fn f(x: UnknownType) {
    y.not_exist()
    consume(x)
}
```

Compiler nên tạo **error-recovery HIR**:

```text
ErrorType
ErrorExpr
ErrorFunction
```

để báo nhiều lỗi trong một compile.

Nhưng:

> Error nodes không bao giờ được phép đi vào Verified MIR.

Pipeline:

```text
AST
 ↓
HIR + ErrorNodes
 ↓
diagnostics
 ↓
if errors
    STOP before MIR verification
```

---

# 31. HIR invariants

Tôi đề xuất freeze:

```text
AHIR-01
Every resolved identifier maps to a stable symbol ID.

AHIR-02
Every expression has exactly one resolved type or ErrorType.

AHIR-03
Every expression has a semantic category.

AHIR-04
Every place expression identifies a semantic storage location.

AHIR-05
Method calls are resolved before MIR.

AHIR-06
Trait dispatch is resolved before MIR unless explicitly dynamic.

AHIR-07
Generic constraints are resolved before ownership verification.

AHIR-08
HIR contains no target-specific machine representation.

AHIR-09
HIR preserves source mapping.

AHIR-10
HIR may contain structured control flow.

AHIR-11
HIR may contain error-recovery nodes, but Verified MIR may not.

AHIR-12
HIR does not imply physical allocation strategy.

AHIR-13
HIR does not imply ABI layout unless explicitly required by semantics.

AHIR-14
Ownership intent is represented explicitly enough for MIR lowering.

AHIR-15
HIR semantics are independent of LLVM or any external compiler.
```

---

# 32. Một quyết định kiến trúc rất quan trọng

Tôi đề xuất **không tạo một “Typed AST” riêng biệt quá lớn**.

Thay vào đó:

```text
AST
 ↓
Resolution
 ↓
HIR
```

AST chỉ phục vụ syntax/diagnostics.

HIR là representation semantic đầu tiên.

Điều này giảm compiler complexity:

```text
Lexer
Parser
AST
   ↓
HIR builder
   ↓
semantic passes
```

thay vì:

```text
AST
 ↓
AST normalized
 ↓
Typed AST
 ↓
Typed AST normalized
 ↓
HIR
```

---

# 33. HIR → MIR

Đây sẽ là bước tiếp theo.

Ví dụ:

```axiom
fn sum(a: i32, b: i32) -> i32 {
    a + b
}
```

HIR:

```text
Return(
    Add(
        Local(a),
        Local(b)
    )
)
```

MIR:

```text
bb0:
    %0 = LOAD a
    %1 = LOAD b
    %2 = ADD %0, %1
    RETURN %2
```

Nhưng với:

```axiom
fn f(x: Buffer<u8>) {
    consume(x)
}
```

MIR phải thể hiện resource flow:

```text
bb0:
    MOVE x -> arg0
    CALL consume
    RETURN
```

và Drop analysis sẽ quyết định có cleanup nào còn cần.

---

# 34. Một điểm tôi muốn sửa nhẹ từ thiết kế cũ

Trước đây ta định nghĩa MIR instruction:

```text
COPY
MOVE
LOAD
STORE
```

Tôi nghĩ nên phân biệt rõ:

### Value operation

```text
COPY
MOVE
```

### Place operation

```text
LOAD
STORE
FIELD
INDEX
```

Vì:

```text
FIELD
```

không thực sự đọc dữ liệu.

Nó tạo:

```text
Place(field)
```

Ví dụ:

```text
p.age = 10
```

nên MIR nên có:

```text
%place = FIELD_PLACE %p, age
STORE %place, 10
```

thay vì:

```text
FIELD %p, age
STORE ...
```

Điều này sẽ làm ownership verifier mạnh hơn rất nhiều.

---

# 35. Và từ đây xuất hiện cấu trúc MIR rất đẹp

```text
MIR
├── Values
│   └── SSA values
│
├── Places
│   ├── Local
│   ├── Field
│   ├── Index
│   └── Deref
│
├── Capabilities
│   ├── READ
│   ├── WRITE
│   ├── MOVE
│   └── OWN
│
├── Resources
│   ├── INIT
│   ├── OWNED
│   ├── MOVED
│   └── DROPPED
│
└── Control Flow
    ├── BasicBlock
    ├── Branch
    ├── Switch
    └── Return
```

Đây chính là representation mà verifier có thể “đọc” trực tiếp.

---

## Bước kế tiếp

Bây giờ **HIR đã đủ hình dạng để freeze ở mức v0.1**. Bước tiếp theo nên là đi sâu vào:

# **AXIOM MIR v0.1 — Semantic IR**

Không chỉ liệt kê instruction, mà sẽ thiết kế cụ thể:

- `Value`
- `Place`
- `Local`
- `BasicBlock`
- `Terminator`
- `Phi`
- `Capability`
- `Region`
- `OwnershipState`
- `Drop`
- `Call`
- `VIEW/VIEW_MUT`
- `ALLOC/DEALLOC`
- `SUSPEND/RESUME`
- representation của generic đã specialize
- cách lowering `if/match/loop`
- cách lowering closure
- cách lowering async thành state machine
- và quan trọng nhất: **một MIR có thể được verifier chứng minh là hợp lệ bằng algorithm cụ thể**, chứ không còn chỉ là specification trên giấy.

Sau MIR, chúng ta có thể xây **MIR Interpreter** trước backend native. Đây sẽ là “reference machine” của Axiom và là mốc rất quan trọng để tránh việc semantics bị backend x86/LLVM vô tình quyết định.