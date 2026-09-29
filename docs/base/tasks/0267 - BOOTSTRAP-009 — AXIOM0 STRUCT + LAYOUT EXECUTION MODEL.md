Tiếp tục theo đúng ladder, bước kế tiếp là **BOOTSTRAP-009 — Struct + Layout Model**.

# BOOTSTRAP-009 — AXIOM0 STRUCT + LAYOUT EXECUTION MODEL

## 1. Quyết định kiến trúc

> **Struct là kiểu dữ liệu danh nghĩa (nominal type); field là thành phần ngữ nghĩa; layout vật lý là trách nhiệm của Layout Engine.**

Tách tuyệt đối:

```text
Struct semantics
    ↓
Field identity
    ↓
Place projection
    ↓
Ownership / Capability
    ↓
MIR
    ↓
Layout Engine
    ↓
Physical offsets / alignment / ABI representation
```

Điều này rất quan trọng.

Trong MIR:

```text
p.x
```

không được hiểu là:

```text
address(p) + 0
```

Mà chỉ là:

```text
Place(
    base = p,
    projection = Field(x)
)
```

Offset `0`, `4`, `8`... chỉ xuất hiện sau khi Layout Engine chạy.

---

# 2. Struct là nominal type

Ví dụ:

```axiom
struct Point {
    x: i32,
    y: i32,
}
```

`Point` có một `StructId` riêng.

Không được coi:

```text
struct Point { x:i32, y:i32 }
```

và:

```text
struct Other { x:i32, y:i32 }
```

là cùng type.

```axiom
let a: Point = ...
let b: Other = ...

a = b        // ERROR
```

Dù layout của chúng có thể hoàn toàn giống nhau.

Đây là:

```text
Type Identity != Representation Identity
```

---

# 3. Internal representation

Stage-0 có thể dùng:

```text
StructDef {
    id: StructId
    name: SymbolId
    fields: Vec<FieldDef>
    visibility: Visibility
    repr: ReprSpec
}
```

Field:

```text
FieldDef {
    id: FieldId
    name: SymbolId
    type: TypeId
    visibility: Visibility
    declaration_index: u32
}
```

Không dùng tên string làm identity.

Ví dụ:

```text
Point
 ├── FieldId(0) → x : i32
 └── FieldId(1) → y : i32
```

MIR dùng `FieldId`, không dùng `"x"`.

---

# 4. Field access

Source:

```axiom
p.x
```

AST có thể chứa tên `x`.

Resolver biến nó thành:

```text
FieldId(Point, x)
```

HIR:

```text
Place(
    base = Local(p),
    projection = Field(FieldId(x))
)
```

MIR:

```text
%1 = load p.x
```

hoặc khi gán:

```text
store 20 -> p.x
```

Nested:

```axiom
a.position.x
```

thành:

```text
Place {
    base: a,
    projections: [
        Field(position),
        Field(x)
    ]
}
```

Không cần tạo temporary pointer.

---

# 5. Struct literal

Syntax:

```axiom
let p = Point {
    x: 20,
    y: 22,
}
```

Ngữ nghĩa:

1. resolve `Point`
2. kiểm tra tất cả field
3. kiểm tra type
4. kiểm tra field nào đã được khởi tạo
5. đánh giá expression theo thứ tự trái → phải
6. tạo aggregate value
7. chuyển ownership của các field tương ứng

Ví dụ:

```axiom
fn make() -> i32 {
    let p = Point {
        x: 20,
        y: 22,
    }

    return p.x + p.y;
}
```

Kết quả:

```text
42
```

---

# 6. Không cho phép field tự động zero-init

Đây là điểm quan trọng đối với hiệu năng.

```axiom
var p: Point;

p.x = 10;
return p.y;
```

→ compile error.

Không được âm thầm biến thành:

```text
p.x = 10
p.y = 0
```

Trạng thái phải là:

```text
p.x = Owned
p.y = Uninit
```

và:

```text
return p.y
```

bị từ chối.

Điều này cho phép compiler giữ:

```text
uninitialized storage
```

giống cách compiler C/C++ tối ưu, nhưng safe Axiom không cho phép đọc rác.

---

# 7. Partial initialization

Cho phép:

```axiom
var p: Point;

p.x = 20;
p.y = 22;

return p.x + p.y;
```

Verifier theo dõi từng field:

```text
p
├── x: Initialized
└── y: Initialized
```

Không cần khởi tạo toàn bộ aggregate ngay từ đầu.

Điều này đặc biệt quan trọng cho struct lớn.

Ví dụ:

```axiom
struct Big {
    a: [1024]u8,
    b: [1024]u8,
    c: [1024]u8,
}
```

Compiler không được buộc chương trình phải tạo một temporary zero-filled 3 KB chỉ vì một field được khởi tạo sau đó.

---

# 8. Partial move

Với struct không có custom Drop:

```axiom
struct User {
    id: u64,
    name: String,
}
```

Có thể:

```axiom
let user = ...;

let name = move user.name;

print(name);
print(user.id);
```

Sau move:

```text
user
├── id   = Owned
└── name = Moved
```

Không được:

```axiom
print(user.name); // ERROR
```

Nhưng:

```axiom
print(user.id);   // OK
```

Đây chính là lý do Place phải field-sensitive.

---

# 9. Reinitialization

Sau khi move:

```axiom
let name = move user.name;
```

field:

```text
user.name = Moved
```

Có thể khởi tạo lại:

```axiom
user.name = String("new");
```

Sau đó:

```text
user
├── id   = Owned
└── name = Owned
```

và struct trở lại trạng thái fully initialized.

---

# 10. Copy struct

Struct có thể là `Copy` nếu toàn bộ semantic contents đáp ứng điều kiện Copy.

Ví dụ:

```axiom
struct Point {
    x: i32,
    y: i32,
}
```

Compiler có thể suy ra:

```text
Point : Copy
```

Nếu:

```axiom
let a = Point { x: 1, y: 2 };
let b = a;
```

thì:

```text
a = Owned
b = Owned
```

không phải:

```text
a = Moved
```

Nhưng:

```axiom
struct User {
    name: String,
}
```

không thể tự động trở thành `Copy`.

Vì `String` có ownership/resource semantics.

---

# 11. Copy không đồng nghĩa memcpy

Đây tiếp tục invariant đã đóng băng:

```text
Copy = semantic duplication
```

không phải:

```text
Copy = mandatory physical memcpy
```

Ví dụ:

```axiom
let b = a;
```

compiler hoàn toàn có thể biến thành:

```text
register duplication
```

hoặc:

```text
SSA value reuse
```

hoặc scalarize:

```text
a.x
a.y
```

mà không tạo aggregate vật lý.

---

# 12. ZST — Zero Sized Type

Axiom hỗ trợ:

```axiom
struct Marker {}
```

hoặc:

```axiom
struct Empty {}
```

Semantic size:

```text
size = 0
```

nhưng:

```text
ownership != absent
```

Ví dụ:

```axiom
let x = Marker {};
move x;
```

vẫn có ownership semantics.

Compiler có thể loại bỏ hoàn toàn storage vật lý nếu không có observable consequence.

---

# 13. Struct layout mặc định

Đây là một điểm tôi khuyến nghị **không thay đổi**.

Mặc định:

> **Struct layout là compiler-controlled.**

Compiler được phép:

- reorder fields
- chèn padding
- tối ưu alignment
- tận dụng niche
- scalarize
- loại bỏ storage không quan sát được

Ví dụ:

```axiom
struct S {
    a: u8,
    b: u64,
    c: u8,
}
```

Không được giả định source order tương ứng với:

```text
offset(a) < offset(b) < offset(c)
```

trong Axiom ABI nội bộ.

Điều này cho compiler nhiều freedom hơn C.

---

# 14. Nhưng source field identity không thay đổi

Cho dù compiler reorder:

```text
a
b
c
```

thành:

```text
b
a
c
```

thì:

```axiom
s.a
s.b
s.c
```

vẫn giữ nguyên semantics.

Field identity:

```text
FieldId
```

không phụ thuộc offset.

---

# 15. Khi nào layout trở thành observable?

Nếu chương trình làm:

```axiom
address_of(s)
```

hoặc FFI:

```axiom
extern "C"
```

hoặc:

```axiom
@repr(C)
```

thì layout/storage constraints trở thành semantic contract.

Đây chính là nguyên tắc:

> **Observable representation constrains optimization.**

---

# 16. `@repr(C)`

Ví dụ:

```axiom
@repr(C)
struct Point {
    x: i32,
    y: i32,
}
```

Khi đó Layout Engine phải tuân thủ C-compatible layout rules của target ABI.

Dùng cho:

- C FFI
- OS ABI
- device ABI
- shared memory
- binary structures
- interoperability

`@repr(C)` không biến struct thành class và cũng không tạo runtime overhead.

---

# 17. `@repr(transparent)`

Cho newtype:

```axiom
struct UserId(u64);
```

có thể:

```axiom
@repr(transparent)
struct UserId(u64);
```

Cam kết representation tương thích với underlying non-ZST field theo ABI rules.

Điều này rất hữu ích cho FFI:

```axiom
extern "C" fn get_user(id: UserId);
```

---

# 18. `@repr(packed)`

Ví dụ:

```axiom
@repr(packed)
struct Header {
    kind: u8,
    size: u32,
}
```

Có thể tạo field không aligned.

Do đó:

```axiom
header.size
```

không được compiler tự động coi là một aligned load bình thường.

Tôi đề xuất:

> `@repr(packed)` là system/unsafe-sensitive.

Có thể yêu cầu:

```axiom
unsafe {
    ...
}
```

hoặc buộc dùng API unaligned access.

Không được để packed silently tạo undefined behavior trong safe code.

---

# 19. `@repr(align(N))`

Ví dụ:

```axiom
@repr(align(64))
struct CacheLine {
    value: u64,
}
```

Layout Engine phải đảm bảo:

```text
alignment >= 64
```

Nhưng alignment requirement có thể tăng kích thước aggregate khi nằm trong array.

---

# 20. Layout Engine

Định nghĩa canonical:

```text
Layout {
    kind
    size
    alignment
    fields[]
    niches
    representation
    validity
    address_space
}
```

Field:

```text
FieldLayout {
    field_id
    offset
    size
    alignment
    layout
}
```

Ví dụ:

```text
Point

size      = 8
alignment = 4

x offset = 0
y offset = 4
```

Nhưng đây chỉ là **target/layout result**, không phải semantics của struct.

---

# 21. Layout cache

Layout nên được cache theo:

```text
TypeId
TargetId
ReprSpec
GenericArguments
ABIContext
```

Ví dụ:

```text
LayoutKey {
    type
    target
    repr
    abi
}
```

Không được cache đơn giản:

```text
StructId → Layout
```

vì cùng một type có thể có representation khác theo target/ABI context.

---

# 22. Recursive struct

Cấm:

```axiom
struct Node {
    next: Node,
}
```

vì:

```text
size(Node)
 = size(Node)
```

không có nghiệm hữu hạn.

Compiler phải báo lỗi kiểu:

```text
AX1501: recursive type has infinite size
```

Nhưng:

```axiom
struct Node {
    value: i32,
    next: Box<Node>,
}
```

hợp lệ.

Hoặc:

```axiom
struct Node {
    next: Option<Box<Node>>,
}
```

hợp lệ.

---

# 23. Layout của `Box<T>`

Đừng định nghĩa:

```text
Box<T> = heap pointer
```

ở semantic level.

Đúng hơn:

```text
Box<T>
    = owning dynamic-storage contract
```

Compiler có thể biến:

```axiom
let x = Box::new(Point { ... });
```

thành stack/register nếu:

- address không escape
- stable storage không observable
- allocation không observable

Nhưng nếu API yêu cầu stable address thì compiler phải giữ storage contract đó.

---

# 24. Array trong struct

Ví dụ:

```axiom
struct Matrix {
    values: [16]f32,
}
```

Place:

```text
m.values[3]
```

là:

```text
Place {
    base = m
    projections = [
        Field(values),
        Index(3)
    ]
}
```

Không cần biến thành pointer trong MIR semantic.

---

# 25. Field capability regions

Đây là nơi Struct + Ownership kết hợp rất mạnh.

Ví dụ:

```axiom
struct Pair {
    left: i32,
    right: i32,
}
```

Compiler có thể chứng minh:

```text
Region(pair.left)
DISJOINT
Region(pair.right)
```

Do đó:

```axiom
let a = mut_view(pair.left);
let b = mut_view(pair.right);
```

có thể hợp lệ.

Nhưng:

```axiom
let a = mut_view(pair);
let b = mut_view(pair);
```

→ conflict.

Và:

```axiom
let a = mut_view(pair.left);
let b = mut_view(pair.left);
```

→ conflict.

Không cần programmer viết lifetime.

---

# 26. Drop của struct

Nếu:

```axiom
struct User {
    id: u64,
    name: String,
}
```

và `String` có Drop, compiler tạo cleanup tương ứng.

Mặc định:

```text
drop(name)
drop(id)
```

theo reverse declaration/initialization order, tùy trạng thái initialized/moved thực tế.

Nếu:

```text
name = Moved
```

thì:

```text
drop(name)
```

không được phát sinh.

---

# 27. Custom Drop và partial move

Nếu user-defined Drop:

```axiom
impl Drop for User {
    fn drop(mut_view self) {
        ...
    }
}
```

thì:

```axiom
let name = move user.name;
```

không được cho phép nếu nó khiến compiler không thể bảo đảm invariant của custom destructor.

Vì vậy:

```text
Derived Drop
    → partial move có thể hỗ trợ

User-defined Drop
    → partial move bị cấm
```

Đây là trade-off hợp lý để giữ verifier đơn giản.

---

# 28. Equality không phải memcmp

Đây là invariant rất quan trọng.

Không được suy luận:

```text
a == b
```

tương đương:

```text
memcmp(&a, &b, sizeof(a)) == 0
```

vì struct có:

- padding
- niche
- multiple representations
- uninitialized padding
- compiler-controlled layout

Nếu muốn equality:

```text
impl Eq for Point {
    ...
}
```

thì so sánh semantic fields.

Compiler có thể optimize thành bit comparison **chỉ khi chứng minh được hợp lệ**.

---

# 29. `size_of`, `align_of`, `offset_of`

Nên giữ chúng ở compile-time/comptime:

```axiom
const SIZE = size_of<Point>();
const ALIGN = align_of<Point>();
const X = offset_of<Point, x>();
```

Nhưng:

```text
offset_of
```

chỉ có giá trị ổn định khi representation/layout contract cho phép.

Vì default layout có thể compiler-controlled, `offset_of` về bản chất làm representation trở thành observable tại compile-time.

Do đó cần cẩn thận: một khi source dùng offset, compiler phải tôn trọng layout tương ứng trong compilation unit/ABI contract đó.

---

# 30. Aggregate ABI

Struct semantics vẫn nằm ở MIR:

```text
return p
```

Layout/ABI mới quyết định:

```text
Direct
Indirect
Split
Expand
Coerce
SRet
```

Ví dụ:

```axiom
fn make_point() -> Point
```

không có nghĩa:

```text
return bằng memory
```

hay:

```text
return bằng registers
```

MIR chỉ nói:

```text
return Point
```

ABI classifier quyết định representation.

---

# 31. Struct không tạo hidden runtime metadata

Struct bình thường **không có**:

```text
vtable pointer
type pointer
object header
GC header
refcount header
runtime metadata
```

Trừ khi type/library abstraction thực sự yêu cầu.

Ví dụ:

```axiom
struct Point {
    x: i32,
    y: i32,
}
```

có thể thực sự chỉ là:

```text
8 bytes
```

trên target phù hợp.

---

# 32. Stage-0 implementation

Tôi đề xuất BOOTSTRAP-009 chỉ implement phần cần thiết trước.

### Stage-0 struct subset

```axiom
struct Point {
    x: i32,
    y: i32,
}
```

Hỗ trợ:

```text
struct declaration
field lookup
struct literal
field read
field write
nested struct
struct move
struct copy
partial initialization
partial move
```

Chưa cần ngay:

```text
repr(C)
repr(packed)
repr(align)
niche optimization
complex enum layout
offset_of
comptime reflection
```

Nhưng data model phải được thiết kế ngay để không phải phá kiến trúc sau này.

---

# 33. Layout algorithm MVP

Cho default Axiom layout Stage-0, có thể tạm dùng:

```text
field order = declaration order
alignment = max(field alignment)
offset = align_up(current_offset, field_alignment)
size = align_up(end, struct_alignment)
```

Ví dụ:

```text
struct S {
    a: u8,
    b: u32,
}
```

MVP:

```text
a: offset 0
padding: 1..3
b: offset 4

size = 8
align = 4
```

Nhưng phải ghi rõ:

> Đây là **MVP implementation policy**, không phải v1 semantic guarantee.

Sau này compiler có thể implement field reordering.

---

# 34. AST → HIR

AST:

```text
StructDecl(
    Point,
    [
        Field(x, i32),
        Field(y, i32)
    ]
)
```

Resolver:

```text
StructId(Point)
FieldId(Point.x)
FieldId(Point.y)
```

Typed HIR:

```text
StructLiteral {
    type: Point,
    fields: [
        (FieldId(x), Const(20)),
        (FieldId(y), Const(22))
    ]
}
```

Field access:

```text
PlaceProjection::Field(FieldId(x))
```

---

# 35. MIR example

Source:

```axiom
fn main() -> i32 {
    let p = Point { x: 20, y: 22 };
    return p.x + p.y;
}
```

MIR conceptually:

```text
bb0:
    %0 = const i32 20
    %1 = const i32 22

    %2 = aggregate Point {
        x = %0,
        y = %1
    }

    %3 = load %2.x
    %4 = load %2.y
    %5 = add checked %3, %4

    drop %2
    return %5
```

Sau optimization:

```text
return 42
```

hoàn toàn hợp lệ.

---

# 36. Test ladder

BOOT-009 cần ít nhất:

### Basic

```text
Point { x:20, y:22 } → 42
```

### Field read

```text
p.x
p.y
```

### Field write

```text
var p = ...
p.x = 42
```

### Nested

```text
Outer {
    inner: Point
}
```

### Copy

```text
let a = Point {...}
let b = a
```

### Move

```text
let a = NonCopy {...}
let b = a
use(a) // error
```

### Partial move

```text
let b = move a.x
use(a.y) // OK
use(a.x) // error
```

### Reinitialize

```text
a.x = ...
use(a.x) // OK
```

### Initialization

```text
var p: Point;
p.x = 1;
return p.y; // error
```

### Recursive type

```text
struct Node {
    next: Node
}
```

→ compile error.

### ZST

```text
struct Marker {}
```

→ valid.

---

# 37. Layout tests

Sau đó thêm:

```text
size_of<Point>()
align_of<Point>()
```

và snapshot:

```text
Point:
    size=8
    align=4
    x=0
    y=4
```

`@repr(C)`:

```text
@repr(C)
struct CPoint {
    x: i32,
    y: i32,
}
```

phải có layout ABI ổn định.

Packed:

```text
@repr(packed)
struct Packed {
    a: u8,
    b: u32,
}
```

phải kích hoạt packed/unaligned rules.

---

# 38. Invariants BOOT-009

Tôi đề xuất registry:

```text
ASTRUCT-20  Struct Identity Is Nominal
ASTRUCT-21  Field Identity Is Stable
ASTRUCT-22  Field Lookup Resolves To FieldId
ASTRUCT-23  Field Access Is A Place Projection
ASTRUCT-24  Struct Literal Evaluation Is Deterministic
ASTRUCT-25  Struct Initialization Is Field Sensitive
ASTRUCT-26  Uninitialized Fields Cannot Be Read
ASTRUCT-27  Field Reinitialization After Move Is Valid
ASTRUCT-28  Partial Move Is Field Sensitive
ASTRUCT-29  Copy Requires Semantic Copyability
ASTRUCT-30  Copy Does Not Imply Physical Memcpy
ASTRUCT-31  ZST Has Semantic Identity
ASTRUCT-32  Recursive Values Require Finite Indirection
ASTRUCT-33  Struct Layout Is Separate From Type Identity
ASTRUCT-34  Default Layout Is Compiler Controlled
ASTRUCT-35  Repr Contracts Constrain Layout
ASTRUCT-36  Packed Layout Is Alignment Sensitive
ASTRUCT-37  Transparent Layout Requires Representation Compatibility
ASTRUCT-38  Field Offsets Are Layout Facts
ASTRUCT-39  Padding Is Not Semantic Data
ASTRUCT-40  Semantic Equality Is Not Memcmp By Default
ASTRUCT-41  Layout Is Target/ABI Dependent
ASTRUCT-42  Layout Results Are Cacheable
ASTRUCT-43  Aggregate ABI Is Separate From Struct Semantics
ASTRUCT-44  Field Regions May Be Proven Disjoint
ASTRUCT-45  Custom Drop Restricts Partial Move
ASTRUCT-46  Derived Drop May Support Partial Move
ASTRUCT-47  Moved Fields Are Not Dropped
ASTRUCT-48  Struct Has No Implicit Runtime Header
ASTRUCT-49  Observable Representation Constrains Optimization
ASTRUCT-50  Struct Semantics Do Not Depend On Physical Storage
```

---

# 39. BOOT-009 gate

Chỉ đánh dấu hoàn thành khi:

```text
struct declaration       ✓
field resolver           ✓
struct literal           ✓
field Place               ✓
nested field Place        ✓
field initialization      ✓
field assignment          ✓
Copy aggregate            ✓
Move aggregate             ✓
partial move               ✓
reinitialization           ✓
ZST                       ✓
recursive-size check       ✓
layout engine MVP          ✓
MIR aggregate operations  ✓
MIR interpreter            ✓
native x86-64              ✓
O0                         ✓
optimized                 ✓
compile-fail tests         ✓
differential tests         ✓
```

Đặc biệt:

```text
source
   ↓
struct semantics
   ↓
Place
   ↓
MIR
   ↓
interpreter
```

phải hoạt động **trước** khi quan tâm đến offset vật lý.

---

## Một quyết định quan trọng cho Axiom

BOOT-009 củng cố một nguyên tắc mà tôi nghĩ rất phù hợp với mục tiêu của Axiom:

```text
                SOURCE
                  │
            ┌─────▼─────┐
            │  TYPE      │
            │  SEMANTICS │
            └─────┬─────┘
                  │
               FIELD
               PLACE
                  │
            ┌─────▼─────┐
            │    MIR     │
            │ "WHAT"     │
            └─────┬─────┘
                  │
            ┌─────▼─────┐
            │   LAYOUT   │
            │   + ABI    │
            │ "HOW"      │
            └─────┬─────┘
                  │
            MACHINE IR
```

**Không để layout vật lý lọt ngược lên semantic MIR.**

Đây là một trong những điểm giúp Axiom vừa **đơn giản cho programmer**, vừa cho compiler đủ freedom để tạo code gần C/C++ hoặc tốt hơn trong những trường hợp có thể chứng minh được.