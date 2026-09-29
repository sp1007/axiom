# COMPILER-008 — ABI Lowering + Layout Engine

Đây là phase rất quan trọng vì từ đây Axiom bắt đầu chuyển từ **semantic language** sang **machine representation**.

Tôi chốt nguyên tắc lớn:

> **MIR biết “giá trị có ý nghĩa gì”; Layout/ABI biết “giá trị đó được đặt và truyền như thế nào trên target”.**

Pipeline:

```text
Optimized MIR
    │
    ▼
Type Layout Engine
    │
    ├── Struct Layout
    ├── Enum Layout
    ├── Tuple/Array Layout
    ├── Closure Layout
    ├── Future Layout
    ├── Trait Object Layout
    └── ABI Representation
            │
            ▼
      ABI Lowering
            │
            ├── Argument Classification
            ├── Return Classification
            ├── sret
            ├── Aggregate Scalarization
            ├── Calling Convention
            ├── Variadic ABI
            └── Dynamic Dispatch ABI
                    │
                    ▼
                   LIR
```

---

# 1. Hai khái niệm phải tách tuyệt đối

Axiom có:

```text
Type Semantics
Storage Layout
```

Ví dụ:

```axiom
struct Vec2 {
    x: f32,
    y: f32,
}
```

Semantic:

```text
Vec2 = { x: f32, y: f32 }
```

Nhưng representation có thể là:

```text
f32 + f32
```

hoặc:

```text
vector register
```

hoặc:

```text
memory[8]
```

Tùy ABI/optimization.

---

# 2. Layout không phải optimization

Layout engine phải trả lời:

> Nếu giá trị này cần materialize, representation hợp lệ là gì?

Optimizer trả lời:

> Có cần materialize nó hay không?

Ví dụ:

```text
Point { x: 1, y: 2 }
```

có layout:

```text
size = 8
align = 4
offset(x) = 0
offset(y) = 4
```

nhưng optimizer có thể không tạo object `Point` nào cả.

---

# 3. Layout Descriptor

Chốt cấu trúc nội bộ:

```text
Layout {
    size
    alignment
    fields[]
    abi_class
    representation
    niches
    padding
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

---

# 4. LayoutKind

```text
Scalar
ScalarPair
Aggregate
Array
Enum
Uninhabited
ZeroSized
Opaque
Vector
```

Ví dụ:

```text
i32 → Scalar
Vec2 → Aggregate
[u8; 16] → Array
Option<T> → Enum
never → Uninhabited
() → ZeroSized
```

---

# 5. Type identity ≠ layout identity

Hai type:

```text
Meters
Seconds
```

có thể:

```text
distinct Meters = i64
distinct Seconds = i64
```

nhưng cùng representation:

```text
i64
```

Do đó:

```text
TypeId != LayoutId
```

và cũng:

```text
Type identity != representation identity
```

---

# 6. Struct layout mặc định

Axiom mặc định:

> **Compiler-controlled layout.**

Ví dụ:

```axiom
struct A {
    a: u8,
    b: u64,
    c: u8,
}
```

Không bắt buộc:

```text
a @ 0
padding
b @ 8
c @ 16
```

Compiler có thể tối ưu layout.

Nhưng chỉ được thay đổi layout khi không có representation contract.

---

# 7. Khi nào layout trở thành observable?

Các trường hợp:

```text
@repr(C)
@repr(transparent)
@repr(packed)
@repr(align(N))
```

hoặc:

```text
extern "C"
FFI
raw pointer field access
offset_of
ABI boundary
```

Khi đó layout trở thành contract.

---

# 8. `@repr(C)`

Ví dụ:

```axiom
@repr(C)
struct Vec2 {
    x: f32,
    y: f32,
}
```

Layout phải tuân theo C-compatible target ABI.

Không được reorder field.

---

# 9. `@repr(transparent)`

```axiom
@repr(transparent)
struct UserId {
    value: u64,
}
```

cam kết representation tương đương field duy nhất trong các ABI contexts được phép.

Rất quan trọng cho FFI/newtype.

---

# 10. `@repr(packed)`

```text
@repr(packed)
```

cho phép bỏ alignment padding.

Nhưng field có thể unaligned.

Do đó:

```text
packed access
```

phải được compiler xử lý đặc biệt hoặc yêu cầu unsafe tùy operation/target.

Không được để backend vô tình tạo unaligned machine access không hợp lệ.

---

# 11. `@repr(align(N))`

Yêu cầu:

```text
alignment >= N
```

Compiler phải kiểm tra:

```text
N valid
N compatible target
```

---

# 12. Struct padding

Padding là:

```text
representation detail
```

không phải semantic field.

Không được coi padding là initialized user data.

Điều này rất quan trọng với:

- equality;
- hashing;
- serialization;
- bitcast;
- FFI.

---

# 13. Bitwise equality ≠ semantic equality

Ví dụ struct có padding.

Không được:

```text
memcmp(a, b) == 0
```

suy ra:

```text
a == b
```

trừ khi type representation contract cho phép.

---

# 14. Enum layout

Axiom enum:

```axiom
enum Option<T> {
    Some(T),
    None,
}
```

Semantic:

```text
Sum(Some(T), None)
```

Layout engine có thể chọn:

```text
tag + payload
```

hoặc niche representation.

---

# 15. Niche optimization

Ví dụ:

```text
Option<*const T>
```

nếu raw pointer representation có invalid/null state phù hợp, compiler có thể encode:

```text
None = null
Some(p) = p
```

thay vì:

```text
tag + pointer
```

Nhưng semantic `Option` vẫn không có null.

Null chỉ là **representation detail**.

---

# 16. Không được dựa vào niche nếu ABI không cho phép

Nếu:

```text
@repr(C)
```

hoặc ABI yêu cầu explicit tag:

```text
tag must exist
```

thì niche optimization bị giới hạn.

---

# 17. Enum discriminant

Mỗi enum variant có:

```text
VariantLayout {
    variant_id
    discriminant
    payload_layout
}
```

Discriminant có thể:

- explicit;
- compiler-assigned;
- optimized away bằng niche.

---

# 18. Match sau layout

MIR:

```text
SWITCH enum
```

sau layout có thể trở thành:

```text
switch tag
```

hoặc:

```text
null test
```

hoặc target-specific sequence.

Đây là ABI/layout lowering, không phải trait/type solving.

---

# 19. `Option<T>` không cần runtime abstraction

Ví dụ:

```axiom
fn find() -> Option<i32>
```

không có:

```text
Option runtime object
GC
heap allocation
```

Có thể trở thành:

```text
RAX = value
RDX = discriminant
```

hoặc thậm chí một register duy nhất nếu niche/ABI cho phép.

---

# 20. `Result<T,E>` tương tự

```axiom
Result<T,E>
```

là ordinary enum.

Không có hidden exception object.

Compiler có thể optimize:

```text
Ok
Err
```

thành register/flag/branch phù hợp.

---

# 21. Zero-sized types

```axiom
struct Marker {}
```

có:

```text
size = 0
```

nhưng vẫn có type identity và ownership semantics.

Không được mặc định biến:

```text
ZST
```

thành “không tồn tại” ở semantic MIR.

Sau optimization nó có thể biến mất hoàn toàn.

---

# 22. Arrays

```axiom
[u8; 16]
```

layout:

```text
size = 16
align = 1
```

General:

```text
size = element_size * count
```

có overflow checking ở compile time.

---

# 23. Tuple

```axiom
(i32, f64, u8)
```

được layout tương tự aggregate.

Tuple không có tên field nhưng vẫn có:

```text
field 0
field 1
field 2
```

---

# 24. Recursive type

```axiom
struct Node {
    next: Node
}
```

→ infinite size.

Compiler reject.

Nhưng:

```axiom
struct Node {
    next: Option<Box<Node>>
}
```

có finite layout.

---

# 25. Box layout

Semantic:

```text
Box<T>
```

là owning dynamic-storage abstraction.

Không định nghĩa:

```text
Box<T> = heap pointer
```

ở semantic level.

Khi address/storage identity thực sự cần:

```text
representation ≈ pointer
```

Nhưng optimizer có thể eliminate allocation trước đó.

---

# 26. Vec layout

Semantic:

```text
Vec<T> {
    storage
    length
    capacity
}
```

Không đóng đinh source-level representation.

ABI/internal representation có thể thường là:

```text
ptr
len
cap
```

nhưng đây không phải language guarantee.

---

# 27. View layout

`view<T>` là capability.

Representation điển hình:

```text
pointer + length
```

nhưng compiler có thể:

```text
scalarize
remove length
constant-fold length
keep pointer only
```

nếu semantics cho phép.

---

# 28. `mut_view<T>`

Thường:

```text
pointer + length
```

nhưng:

```text
mutability
provenance
alias capability
```

là semantic compiler facts, **không phải runtime metadata bắt buộc**.

Đây là điểm cực kỳ quan trọng.

Axiom không tạo:

```text
runtime borrow object
runtime lifetime object
```

chỉ để thực hiện safe code.

---

# 29. Capability erasure

Sau:

```text
Ownership verification
Capability verification
```

compiler có thể biến:

```text
BORROW_READ
BORROW_WRITE
```

thành:

```text
LOAD
STORE
```

và xóa capability token.

Đây là một trong những cơ chế chính để đạt zero-cost abstraction.

---

# 30. Function ABI

ABI lowering nhận:

```text
fn type
parameter types
return type
calling convention
target
```

và tạo:

```text
ABISignature {
    args[]
    results[]
    stack_args[]
    hidden_args[]
    sret?
    varargs?
}
```

---

# 31. Argument classification

Mỗi argument được phân loại:

```text
Direct
Indirect
Expand
Coerce
Ignore
Split
```

Ví dụ aggregate nhỏ:

```text
Vec2
```

có thể:

```text
Direct → FPR
```

aggregate lớn:

```text
Indirect → memory
```

---

# 32. Return classification

Tương tự:

```text
Direct
Indirect
Split
Void
```

Ví dụ:

```text
fn add(a: i32, b: i32) -> i32
```

→ direct register return.

---

# 33. Aggregate return

```axiom
fn make_point() -> Point
```

ABI có thể trả:

```text
RAX/RDX
```

hoặc:

```text
hidden sret pointer
```

hoặc target-specific register combination.

MIR không cần biết.

---

# 34. `sret`

Nếu ABI yêu cầu:

```text
fn make() -> Large
```

hạ thành conceptual:

```text
fn make(out: *mut Large)
```

nhưng:

> `sret` là ABI transformation, không phải source-level pointer semantics.

---

# 35. Caller-allocated return

Axiom cho phép:

```text
caller owns destination
callee initializes destination
```

Điều này giúp tránh:

```text
temporary heap allocation
copy
```

đối với aggregate lớn.

---

# 36. Move return

Ví dụ:

```axiom
fn create() -> Large {
    let x = ...
    return x;
}
```

không có nghĩa:

```text
copy x → return buffer
```

Compiler có thể:

```text
construct directly into caller destination
```

Đây là **return value optimization** ở mức semantic/ABI.

---

# 37. Parameter passing

Không phải mọi value parameter đều physical copy.

Ví dụ:

```axiom
fn consume(x: Large)
```

có thể truyền:

```text
registers
memory
pointer-to-caller-storage
```

tùy ABI.

Semantic vẫn là:

```text
ownership transferred
```

---

# 38. Copy parameter

```axiom
fn use(x: Vec2)
```

với `Vec2: Copy`:

semantic copy.

Physical implementation có thể chỉ là:

```text
same registers
```

nếu compiler tối ưu.

---

# 39. View parameter

```axiom
fn sum(v: view<i32>)
```

không tạo runtime borrow object.

ABI chỉ truyền representation cần thiết:

```text
ptr + len
```

hoặc optimized form.

---

# 40. `mut_view` ABI

```axiom
fn fill(v: mut_view<u8>)
```

ABI truyền storage access representation.

Compiler safety facts đã được verifier xử lý trước ABI.

---

# 41. Function pointer ABI

Function type phải chứa calling convention khi ABI-relevant:

```text
fn(i32) -> i32
```

và:

```text
extern "C" fn(i32) -> i32
```

không nhất thiết cùng function type.

---

# 42. Closure ABI

Closure:

```axiom
|x| x + captured
```

sau lowering:

```text
closure_env
+
function_pointer/code
```

Conceptual:

```text
fn invoke(env: *mut Env, x: i32) -> i32
```

Nhưng compiler có thể inline và xóa toàn bộ environment.

---

# 43. Capturing closure không bắt buộc heap

Ví dụ:

```axiom
fn foo() {
    let y = 10;
    let f = |x| x + y;
    f(20);
}
```

hoàn toàn có thể:

```text
register y
inline f
return 30
```

Không allocation.

---

# 44. `dyn Trait`

Dynamic dispatch là trường hợp thực sự cần runtime metadata.

Conceptual:

```text
dyn Trait {
    data_ptr
    vtable_ptr
}
```

Vtable chứa:

```text
method pointers
drop metadata where required
size/alignment metadata where required
```

nhưng exact ABI phải được chốt riêng.

---

# 45. `dyn Trait` không tự sở hữu data

```text
dyn Trait
```

chỉ là dynamic capability/representation.

Ownership nằm ở:

```text
Box<dyn Trait>
Arc<dyn Trait>
view<dyn Trait>
...
```

tùy abstraction.

---

# 46. Không implicit boxing

Đây là invariant rất quan trọng.

```axiom
let x: dyn Trait = Concrete();
```

không được compiler âm thầm:

```text
heap allocate
create vtable
```

nếu source không yêu cầu dynamic storage representation.

Dynamic dispatch phải là explicit abstraction.

---

# 47. Trait object ABI

Tôi đề xuất conceptual ABI:

```text
DynObject {
    data: pointer
    vtable: pointer
}
```

nhưng đây chỉ là initial ABI.

Axiom không nên cam kết vtable binary layout ổn định giữa compiler versions trừ khi explicit stable ABI mode.

---

# 48. Stable ABI

Nếu:

```text
@stable_abi
```

hoặc public binary ABI boundary:

compiler phải freeze:

- field layout;
- enum representation;
- calling convention;
- symbol;
- vtable format;
- alignment;
- size;
- versioning rules.

Không nên mặc định mọi Axiom type đều stable ABI.

---

# 49. Variadic

C-style:

```axiom
extern "C" fn printf(fmt: *const u8, ...) -> i32;
```

Variadic lowering phải giao cho target ABI:

```text
SysV64
Win64
AAPCS64
...
```

Không tự thiết kế một “Axiom varargs ABI” rồi ép foreign ABI vào.

---

# 50. ABI adaptation

Ví dụ Axiom:

```text
Axiom fn
```

gọi:

```text
extern "C" fn
```

Compiler tạo ABI adapter nếu cần:

```text
Axiom representation
        ↓
ABI adaptation
        ↓
C representation
        ↓
CALL
```

---

# 51. ABI adapter có thể được inline

Nếu adapter chỉ:

```text
register shuffle
cast
aggregate unpack
```

optimizer/backend có thể xóa phần lớn overhead.

---

# 52. Calling conventions

Initial:

```text
Axiom
C
System
Fast
Vector
SysV64
Win64
AAPCS64
Wasm
```

Target quyết định convention hợp lệ.

---

# 53. ABI không được phụ thuộc optimization level

Ví dụ:

```text
-O0
-O3
```

có thể physical code khác nhau nhưng observable ABI phải đúng.

Compiler không được:

```text
-O3 → đổi calling convention
```

trừ khi đó là internal function và ABI boundary không exposed.

---

# 54. Internal ABI optimization

Ngược lại, compiler **có thể** dùng private calling convention cho internal functions nếu:

```text
not externally visible
not address-observable across ABI
all callers controlled
```

Ví dụ:

```text
private fn helper()
```

có thể được:

- parameter register reshaping;
- return convention optimization;
- tail call;
- argument elimination.

---

# 55. Public ABI boundary

Các boundary:

```text
pub exported
extern
@export
dynamic library symbol
FFI
function pointer crossing ABI
```

phải freeze đúng ABI.

---

# 56. Layout cache

Layout là computation tương đối đắt.

Dùng:

```text
LayoutCache
```

key:

```text
TypeId
Target
ABI
repr attributes
generic arguments
address space
```

---

# 57. Recursive layout detection

Compiler cần cycle detector:

```text
LayoutStack
```

Ví dụ:

```text
A → B → C → A
```

nếu không có indirection:

```text
infinite-size diagnostic
```

---

# 58. Generic layout

```axiom
struct Pair<T,U> {
    a: T,
    b: U
}
```

mỗi instantiation có layout riêng:

```text
Pair<i32,u8>
Pair<f64,u64>
Pair<Vec3,Mat4>
```

Layout cache:

```text
GenericTypeId + TypeArgs + Target
```

---

# 59. Layout monomorphization

Không cần tạo physical layout cho generic type chưa được instantiate.

Điều này phù hợp với:

```text
lazy monomorphization
+
incremental compilation
```

---

# 60. Data layout target

TargetDescription phải cung cấp:

```text
pointer width
integer widths
alignment
endianness
native vector widths
aggregate ABI
atomic alignment
stack alignment
```

Không dùng một global “Axiom data layout”.

---

# 61. Endianness

Layout:

```text
field order
offset
size
alignment
```

không thay đổi chỉ vì endian.

Nhưng:

```text
integer byte representation
bitcast
serialization
raw memory
```

phải tôn trọng target endian.

---

# 62. `bitcast`

Phải phân biệt:

```text
CAST
BITCAST
```

`bitcast` chỉ hợp lệ khi representation tương thích.

Không được dùng:

```text
bitcast<T,U>
```

để phá type semantics tùy tiện.

---

# 63. Transparent newtype

Ví dụ:

```axiom
@repr(transparent)
struct FileDescriptor {
    raw: i32
}
```

có thể FFI trực tiếp như `i32`.

Đây là use case cực kỳ quan trọng.

---

# 64. Field offsets

`offset_of<T, field>` chỉ được constant-evaluate khi layout đã được xác định.

Nếu layout compiler-controlled và không có stable representation contract, API phải phản ánh rằng offset chỉ có ý nghĩa trong compiler-selected representation context.

Tôi **không khuyến nghị** biến mọi field offset thành ABI-stable mặc định.

---

# 65. Layout randomization

Không cần randomize layout.

Nhưng compiler được phép reorder private fields giữa compiler builds nếu không có representation contract.

Điều này giúp optimizer tự do hơn.

---

# 66. Security layout

Có thể sau này hỗ trợ:

```text
@no_reorder
@secret
@cache_align
```

nhưng không đưa quá nhiều annotation vào Core v1.

---

# 67. ABI Lowering output

Sau phase này:

```text
MIR
```

không còn đủ trừu tượng.

Ví dụ:

```text
RETURN Point
```

thành:

```text
ABI_RESULT RAX
ABI_RESULT RDX
RET
```

hoặc:

```text
SRET destination
RET
```

Lúc đó LIR có thể xử lý.

---

# 68. ABI Lowering không được phá ownership

Ví dụ:

```text
return x
```

sau ABI lowering có thể:

```text
STORE x → sret
```

nhưng semantic fact:

```text
x moved
```

đã được xác định trước đó.

Không được tạo thêm Drop cho `x`.

---

# 69. Cleanup + sret

Nếu:

```text
fn f() -> Large {
    let x = ...
    ...
    return x;
}
```

compiler phải đảm bảo:

```text
x initialized
x moved into return destination
x is not dropped afterward
other locals are dropped
```

Thứ tự cleanup phải chính xác.

---

# 70. ABI + panic

Nếu function panic trước return:

```text
sret destination
```

không được coi là returned initialized value.

Nếu unwind:

```text
cleanup graph
```

phải biết object nào đã initialized.

---

# 71. Async Future ABI

Async đã được lower thành Future state.

ABI chỉ thấy:

```text
Future<T>
```

Ví dụ:

```text
async fn foo() -> i32
```

conceptually:

```text
fn foo() -> FutureFoo
```

Layout engine tính:

```text
state
captured locals
suspension discriminant
drop state
```

---

# 72. Future không mặc định heap

Nếu:

```axiom
let f = foo();
let x = f.await;
```

compiler có thể đặt Future:

```text
stack
register
caller frame
```

Nếu:

```axiom
spawn(foo())
```

scheduler abstraction có thể yêu cầu storage phù hợp.

---

# 73. Future state layout

Compiler chỉ giữ:

```text
values live across await
```

Không giữ toàn bộ local scope.

Ví dụ:

```text
a
await
b
```

Nếu `a` chết trước await:

```text
a
```

không nằm trong Future state.

---

# 74. State discriminant

Future có thể cần:

```text
state = 0
state = 1
state = 2
...
```

nhưng compiler có thể encode state bằng:

- integer;
- niche;
- control-flow representation;

miễn semantics đúng.

---

# 75. Closure/Future layout có thể bị erase

Nếu:

```text
closure không escape
future được inline
```

thì:

```text
ClosureLayout
FutureLayout
```

có thể biến mất hoàn toàn.

Đây là abstraction erasure.

---

# 76. Layout và register allocation

Layout engine không quyết định:

```text
RAX
RBX
stack offset
```

Nó chỉ nói:

```text
representation
size
alignment
aggregate decomposition
```

Register allocator thuộc Machine IR.

---

# 77. Layout và instruction selection

Tương tự, layout không nói:

```text
MOV
LEA
FMOV
```

Nó chỉ tạo ABI/LIR facts.

---

# 78. ABI lowering architecture

Repository:

```text
compiler/
├── abi/
│   ├── layout/
│   │   ├── layout_engine/
│   │   ├── struct/
│   │   ├── enum/
│   │   ├── niche/
│   │   ├── aggregate/
│   │   ├── array/
│   │   ├── closure/
│   │   └── future/
│   │
│   ├── classify/
│   │   ├── arguments/
│   │   ├── returns/
│   │   ├── aggregates/
│   │   └── varargs/
│   │
│   ├── calling_convention/
│   │   ├── axiom/
│   │   ├── c/
│   │   ├── sysv64/
│   │   ├── win64/
│   │   ├── aapcs64/
│   │   └── wasm/
│   │
│   └── lowering/
│       ├── arguments/
│       ├── returns/
│       ├── sret/
│       ├── dyn_trait/
│       ├── closure/
│       └── async/
```

---

# 79. ABI interface

Nên có interface kiểu:

```text
AbiClassifier {
    classify_function(...)
    classify_argument(...)
    classify_return(...)
    classify_varargs(...)
}
```

và:

```text
LayoutEngine {
    layout_type(TypeId)
    layout_struct(StructId)
    layout_enum(EnumId)
    layout_array(...)
    layout_dyn_trait(...)
}
```

---

# 80. Invariants COMPILER-008

Tôi chốt:

```text
AABI-20  Type Semantics Are Independent Of Physical Layout
AABI-21  Layout Is Deterministic
AABI-22  Layout Is Target Specific
AABI-23  Type Identity Is Distinct From Layout Identity
AABI-24  Default Struct Layout Is Compiler Controlled
AABI-25  Explicit Representation Contracts Are Preserved
AABI-26  Repr(C) Preserves C-Compatible Layout
AABI-27  Repr(Transparent) Preserves Transparent Representation
AABI-28  Packed Layout Does Not Permit Invalid Unaligned Access
AABI-29  Explicit Alignment Is Preserved
AABI-30  Padding Is Not Semantic User Data
AABI-31  Bitwise Equality Is Not Assumed Semantic Equality
AABI-32  Enum Representation Preserves Variant Semantics
AABI-33  Niche Optimization Preserves Enum Semantics
AABI-34  Null Representation Does Not Introduce Safe Null Semantics
AABI-35  Recursive Layout Requires Finite Representation
AABI-36  ZST Semantics Remain Valid
AABI-37  Layout Cache Is Target And Representation Sensitive
AABI-38  Generic Layout Is Computed Per Instantiation
AABI-39  ABI Classification Is Separate From Semantic Type Checking
AABI-40  Calling Convention Is Explicit At ABI Boundaries
AABI-41  Aggregate Arguments May Be Direct Indirect Split Or Expanded
AABI-42  Aggregate Returns May Be Direct Split Or SRet
AABI-43  SRet Is An ABI Transformation
AABI-44  Caller-Allocated Returns Are Supported
AABI-45  Return Move Does Not Imply Additional Copy
AABI-46  ABI Lowering Preserves Ownership State
AABI-47  ABI Lowering Preserves Cleanup Semantics
AABI-48  ABI Lowering Preserves Panic Semantics
AABI-49  Closure ABI Does Not Imply Heap Allocation
AABI-50  Future ABI Does Not Imply Heap Allocation
AABI-51  View ABI Does Not Require Runtime Borrow Objects
AABI-52  Capability Metadata May Be Erased After Verification
AABI-53  Mutability Capability Is Not Runtime Metadata By Default
AABI-54  Dyn Trait Metadata Exists Only For Explicit Dynamic Dispatch
AABI-55  Dyn Trait Does Not Imply Ownership
AABI-56  Dyn Trait Does Not Imply Allocation
AABI-57  Implicit Boxing Is Forbidden
AABI-58  FFI Boundaries Preserve Declared ABI
AABI-59  Foreign Exceptions Do Not Cross ABI Implicitly
AABI-60  ABI Adapters May Be Optimized Away
AABI-61  Private Internal Functions May Use Optimized Internal ABI
AABI-62  Public ABI Boundaries Remain Stable
AABI-63  ABI Details Do Not Leak Into Semantic MIR
AABI-64  Register Assignment Is Deferred To LIR/Machine IR
AABI-65  Instruction Selection Is Deferred To Target Backend
AABI-66  Endianness Is Target Representation State
AABI-67  Bitcast Requires Representation Compatibility
AABI-68  Layout Does Not Imply Storage Materialization
AABI-69  Optimized-Out Aggregates Need No Physical Layout
AABI-70  ABI Lowering Is Deterministic
```

---

# 81. Một quyết định kiến trúc rất đáng giữ

Từ đây Axiom có **4 tầng representation** cực rõ:

```text
1. Semantic
   “Point là gì?”

2. Layout
   “Point nếu materialize thì có representation nào?”

3. ABI
   “Point đi qua function boundary như thế nào?”

4. Machine
   “Point thực sự dùng register/instruction nào?”
```

Không trộn bốn thứ này.

Đây là điều giúp compiler không trở thành một mớ logic C++/LLVM-style đan chéo.

---

# 82. Toàn bộ pipeline Axiom hiện tại

Sau COMPILER-008, kiến trúc đã gần hoàn chỉnh từ source tới machine:

```text
SOURCE
  │
Lexer / Parser
  │
AST
  │
Name Resolution
  │
HIR
  │
Type + Trait Solver
  │
Typed HIR
  │
Ownership / Capability
  │
Closure / Async Analysis
  │
Verified HIR
  │
MIR
  │
MIR Verification
  │
Semantic Optimization
  │
Optimized MIR
  │
┌──────────────────────────────┐
│ Layout Engine                │
│ ABI Classification           │
│ Struct / Enum / Future ABI   │
│ Closure / Dyn Trait ABI      │
│ sret / calling convention    │
└──────────────────────────────┘
  │
ABI MIR / LIR
  │
Target Legalization
  │
Machine IR
  │
Machine Optimization
  │
Register Allocation
  │
Frame Layout
  │
Prologue / Epilogue
  │
Instruction Encoding
  │
Object Writer
  │
Linker
  │
NATIVE EXECUTABLE
```

### Bước kế tiếp hợp lý nhất là **COMPILER-009 — Target Legalization + Instruction Selection**

Ở đó chúng ta sẽ chốt cách biến LIR trừu tượng thành **Machine IR thực sự** cho x86-64 trước, sau đó AArch64/RISC-V/WASM; đặc biệt phải giải quyết `i128` sau này, division, multiply, flags, addressing modes, atomics, vector/SIMD và cách **không phụ thuộc LLVM** ngay từ kiến trúc ban đầu.