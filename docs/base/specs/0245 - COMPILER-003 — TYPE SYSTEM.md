Tiếp tục sang **COMPILER-003 — Canonical Type System + Type Inference + Trait Solver**.

Đây là một trong những phần quan trọng nhất của Axiom. Nếu type system thiết kế sai, các phần ownership, generic, trait, ABI, optimization phía sau đều sẽ trở nên phức tạp.

Mục tiêu lần này là tạo một type system **mạnh nhưng không biến Axiom thành dependent-type language**.

# COMPILER-003 — TYPE SYSTEM

## 1. Mục tiêu thiết kế

Axiom type system phải đạt:

```text
Static typing
Strong typing
Local type inference
Generic programming
Trait constraints
Associated types
Algebraic types
Zero-cost abstractions
Deterministic inference
Predictable diagnostics
```

Nhưng không đưa vào Core v1:

```text
Dependent types
Higher-kinded types
Type families
Implicit type parameters
General refinement types
Runtime type objects
Structural subtyping
Class inheritance
Nullability hierarchy
```

Nguyên tắc:

> **Compiler được phép suy luận type; programmer không phải viết lại những gì compiler đã biết. Nhưng public semantic boundaries phải rõ ràng.**

---

# 2. Canonical Type

Sau resolver, compiler không nên tiếp tục dùng AST type syntax làm type identity.

Ví dụ:

```axiom
Vec<i32>
```

AST có thể là:

```text
TypePath(
    Vec,
    [i32]
)
```

Sau type resolution:

```text
TypeId(1024)
```

`TypeId` mới là semantic identity.

---

# 3. TypeInterner

Tất cả canonical types đi qua:

```text
TypeInterner
```

Ví dụ:

```text
i32
```

chỉ có một canonical representation:

```text
TypeId::I32
```

Hai lần tạo:

```text
Vec<i32>
Vec<i32>
```

phải cho cùng semantic type:

```text
TypeId(500)
```

Không tạo hai object type khác nhau.

---

# 4. Type representation

Đề xuất:

```text
Type =
    Primitive
    Tuple
    Array
    Struct
    Enum
    Function
    Closure
    GenericParam
    GenericInstance
    View
    MutView
    RawPointer
    DynTrait
    TypeAliasResolved
    Never
    Unit
    InferenceVar
    Opaque
```

Sau inference hoàn tất, `InferenceVar` không được tồn tại trong Typed HIR/MIR.

---

# 5. Primitive types

Frozen baseline:

```text
bool

i8
i16
i32
i64

u8
u16
u32
u64

isize
usize

f32
f64

unit
never
```

`i128/u128` để phase sau.

Không tự thêm:

```text
char
decimal
long double
half
```

vào Core chỉ để tiện syntax.

---

# 6. `unit`

`unit` là một type thực sự:

```text
()
```

Ví dụ:

```axiom
fn log() -> unit {
    ...
}
```

có thể viết ngắn:

```axiom
fn log() {
    ...
}
```

`unit` có một giá trị:

```text
()
```

---

# 7. `never`

`never` biểu diễn computation không trả về:

```axiom
fn abort() -> never {
    panic("fatal");
}
```

Các expression kiểu `never` có thể coerce vào context cần type khác:

```axiom
let x: i32 = if condition {
    42
} else {
    panic("error")
};
```

Nhánh `panic()` có type `never`.

---

# 8. Tuple

```axiom
let x: (i32, f32) = (10, 3.14);
```

Canonical:

```text
Tuple[
    I32,
    F32
]
```

Tuple identity structural.

```text
(i32, f32)
```

luôn cùng type dù xuất hiện ở module khác.

---

# 9. Array

```axiom
[i32; 4]
```

là:

```text
Array {
    element: i32
    length: 4
}
```

Length là compile-time constant.

Do đó:

```text
[i32; 4]
[i32; 8]
```

là hai type khác nhau.

---

# 10. Array không phải Vec

Đây là semantic distinction:

```text
[i32; 4]
```

→ fixed-size value.

```text
Vec<i32>
```

→ dynamic collection abstraction.

Compiler không tự convert.

---

# 11. Struct type

```axiom
struct Point {
    x: f32,
    y: f32,
}
```

Canonical type:

```text
StructType {
    definition: StructId(Point)
    generic_args: []
}
```

`Point` là nominal type.

---

# 12. Nominal typing

Hai struct giống hệt field vẫn khác type:

```axiom
struct Meter {
    value: f32,
}

struct Second {
    value: f32,
}
```

Không được:

```text
Meter ← Second
```

chỉ vì layout giống nhau.

Đây là một quyết định rất quan trọng để tránh bug semantic.

---

# 13. Newtype / distinct

Axiom cần một cách tạo type mới nhưng representation có thể tương thích.

```axiom
type UserId = distinct u64;
```

Khi đó:

```text
UserId != u64
```

nhưng:

```text
@repr(transparent)
```

hoặc semantic transparent representation có thể cho ABI compatibility khi explicit.

Không có implicit conversion:

```axiom
let x: u64 = user_id; // error
```

phải explicit:

```axiom
let x = user_id as u64;
```

hoặc API accessor.

---

# 14. Type alias

Khác với `distinct`.

```axiom
type UserMap = Map<UserId, User>;
```

`UserMap` chỉ là alias.

Semantic:

```text
UserMap == Map<UserId, User>
```

Trong khi:

```text
type UserId = distinct u64;
```

là type mới.

---

# 15. Generic type

```axiom
struct Box<T> {
    value: T,
}
```

`Box<i32>`:

```text
GenericInstance {
    definition: StructId(Box)
    args: [i32]
}
```

`Box<f64>` khác.

---

# 16. Generic parameters

```axiom
fn identity<T>(x: T) -> T {
    x
}
```

`T` được biểu diễn bằng:

```text
GenericParamId
```

Không phải runtime type object.

Sau monomorphization:

```text
identity<i32>
identity<f64>
```

có thể trở thành những specialization machine-level khác nhau.

---

# 17. Function types

```axiom
fn(i32, i32) -> i32
```

là type.

Canonical:

```text
FunctionType {
    params: [i32, i32]
    return: i32
    calling_convention: Axiom
}
```

Calling convention phải là một phần type khi semantic khác nhau.

---

# 18. Function pointer vs function item

Một function cụ thể:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

có identity:

```text
FunctionId(add)
```

Khi convert thành function value:

```axiom
let f: fn(i32, i32) -> i32 = add;
```

mới trở thành function pointer/value.

Không nhất thiết function declaration bản thân là runtime pointer.

---

# 19. Closure type

```axiom
let add = |x| x + 1;
```

Closure có anonymous unique type.

Compiler tạo:

```text
ClosureType {
    closure_id: ClosureId
    captures: [...]
}
```

Closure type không phải:

```text
fn(i32) -> i32
```

nhưng có thể coerce thành function type **chỉ khi closure không capture**.

---

# 20. Capturing closure

```axiom
let factor = 10;

let f = |x| x * factor;
```

`f` có unique closure type.

Conceptually:

```text
Closure {
    code: FunctionId(...)
    environment: {
        factor: ...
    }
}
```

Representation thực tế compiler tự quyết định.

Không mặc định heap allocate.

---

# 21. `view<T>`

Canonical:

```text
View<T>
```

và:

```text
MutView<T>
```

là semantic types riêng.

`view<i32>` không phải:

```text
*i32
```

và cũng không phải:

```text
&i32
```

Nó là capability abstraction.

---

# 22. View covariance không tự động

Không nên cho compiler suy luận tùy tiện:

```text
view<Child> → view<Base>
```

vì Axiom không có general subtype hierarchy.

Generic covariance chỉ tồn tại khi abstraction đó định nghĩa rõ.

Điều này giữ type system đơn giản.

---

# 23. `mut_view<T>`

`mut_view<T>` có exclusive write semantics.

```axiom
fn increment(x: mut_view<i32>) {
    ...
}
```

Không thể implicit duplicate thành hai `mut_view`.

Đây không phải vấn đề type representation đơn thuần.

Type checker + capability checker cùng tham gia.

---

# 24. Raw pointer

```text
*const T
*mut T
```

là machine-level types.

Chúng không phải safe capabilities.

Ví dụ:

```axiom
unsafe fn read(p: *const i32) -> i32
```

Type system vẫn biết `p` là pointer.

Nhưng safety verifier quyết định việc dereference.

---

# 25. `dyn Trait`

```axiom
dyn Display
```

là existential dynamic trait abstraction.

Nó không tự imply:

```text
heap
allocation
object header
Arc
Box
```

Ví dụ API có thể yêu cầu:

```axiom
Box<dyn Display>
```

lúc đó `Box` mới đưa ra ownership/storage semantics.

---

# 26. Không có subtype system

Axiom không có:

```text
Animal
  ↑
Dog
```

và:

```text
Dog <: Animal
```

Thay vào đó:

```axiom
trait Animal {
    fn speak(self);
}

impl Animal for Dog {
    ...
}
```

Static generic:

```axiom
fn run<T: Animal>(x: T) {
    x.speak();
}
```

Dynamic:

```axiom
fn run(x: Box<dyn Animal>) {
    ...
}
```

Đây là hai abstraction khác nhau.

---

# 27. Type inference

Axiom cho inference mạnh trong local scope.

```axiom
let x = 10;
```

compiler suy ra:

```text
x: i32
```

nếu không có context khác.

Nhưng:

```axiom
pub fn get_value() {
    ...
}
```

return type phải được explicit.

Tôi đề xuất:

> **Public function declaration phải ghi return type.**

Ví dụ:

```axiom
pub fn parse(input: view<u8>) -> Result<Value, Error>
```

Không:

```axiom
pub fn parse(input: view<u8>) {
    ...
}
```

nếu compiler phải infer API type.

Private/local function có thể được phép inference return type nếu muốn giảm boilerplate, nhưng tôi vẫn nghiêng về explicit return type cho mọi named function để diagnostics và ABI ổn định.

---

# 28. Quy tắc inference

### Được inference

```axiom
let x = 10;
let y = x + 20;
let z = foo(x);
```

### Không inference qua public API

```axiom
pub fn foo(x: i32) -> i32
```

phải rõ.

### Generic parameter vẫn explicit

```axiom
fn identity<T>(x: T) -> T
```

không:

```text
fn identity(x) ...
```

Axiom không biến thành dynamically typed language.

---

# 29. Integer literal inference

Literal:

```axiom
42
```

ban đầu tạo:

```text
IntegerLiteralTypeVar
```

Context:

```axiom
let x: u64 = 42;
```

→ `42 : u64`.

Nếu không có constraint:

```axiom
let x = 42;
```

default:

```text
i32
```

Đây là một quyết định tốt vì:

- dễ hiểu;
- giống intuition của programmer;
- không tạo arbitrary-width integer.

---

# 30. Float literal

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

→ f32.

---

# 31. Không implicit integer ↔ float

Không:

```axiom
let x: f64 = 10;
```

nếu Axiom muốn strict numeric semantics.

Tôi đề xuất **cho phép literal conversion đặc biệt**:

```axiom
let x: f64 = 10;
```

vì `10` là literal chưa có concrete type.

Nhưng:

```axiom
let a: i32 = 10;
let b: f64 = a;
```

phải explicit:

```axiom
let b = a as f64;
```

Đây là distinction quan trọng:

> **Literal có thể adapt theo context; typed value thì không tự convert.**

---

# 32. Numeric narrowing

```axiom
let x: i64 = 100;
let y: i32 = x as i32;
```

Explicit.

Không:

```axiom
let y: i32 = x;
```

Compiler không đoán programmer muốn truncate.

---

# 33. Numeric operators

Không có promotion kiểu C:

```text
u8 + u64
```

không tự thành `u64`.

Phải có explicit conversion hoặc generic numeric abstraction.

Điều này làm arithmetic semantics cực kỳ deterministic.

---

# 34. Type unification

Inference engine cần:

```text
unify(A, B)
```

Ví dụ:

```axiom
let x = identity(42);
```

constraints:

```text
T = type(42)
return = T
```

sau default:

```text
T = i32
```

---

# 35. Unification variables

Internal:

```text
TypeVar(0)
TypeVar(1)
...
```

Chỉ tồn tại trong inference.

Không được leak ra:

- HIR final
- ABI
- MIR
- diagnostics cuối cùng.

Nếu không resolve được:

```text
AX1301 could not infer type
```

---

# 36. No global type inference

Không làm kiểu:

```axiom
let a = foo();
```

mà compiler chạy toàn project để đoán mọi thứ một cách không giới hạn.

Inference phải bounded bởi:

```text
function body
generic constraints
visible declarations
explicit types
```

Điều này giúp compile time predictable.

---

# 37. Coercion

Axiom nên có **rất ít coercion**.

Cho phép:

```text
never → T
```

và các coercion syntax-defined như:

```text
noncapturing closure → function pointer
```

Có thể có:

```text
T → view<T>
```

nhưng chỉ trong **ephemeral argument context**, đúng memory model đã đóng.

Không có:

```text
integer → float
pointer → integer
integer → pointer
T → dyn Trait
```

implicit tùy tiện.

---

# 38. `T → view<T>`

Ví dụ:

```axiom
fn sum(x: view<i32>) -> i32 {
    ...
}

let data = [1, 2, 3];

sum(data);
```

được compiler cho phép.

Nhưng:

```axiom
let v = data;
```

không tự biến thành view.

Nếu muốn lưu capability:

```axiom
let v = view(data);
```

Đây chính là boundary đã frozen.

---

# 39. Trait là constraint, không phải subtype

```axiom
fn print<T: Display>(x: T) {
    ...
}
```

không nói:

```text
T <: Display
```

mà nói:

```text
Display(T)
```

là obligation.

Trait solver giải obligation.

---

# 40. Trait obligation

Ví dụ:

```axiom
fn foo<T: Add>(x: T) {
    ...
}
```

compiler tạo:

```text
TraitObligation {
    trait: Add
    self_type: T
}
```

Solver tìm impl phù hợp.

---

# 41. Trait solver không chạy trong MIR

Đây là invariant quan trọng.

Trước MIR:

```text
Trait solving
```

phải hoàn tất.

MIR không chứa:

```text
"find implementation of Add<T>"
```

MIR chứa:

```text
FunctionId(Add_for_i32)
```

hoặc generic resolved operation.

Điều này giúp MIR:

- deterministic;
- optimizer-friendly;
- không phụ thuộc type solver.

---

# 42. Associated type

Axiom hỗ trợ:

```axiom
trait Iterator {
    type Item;

    fn next(mut self) -> Option<Self::Item>;
}
```

Implementation:

```axiom
impl Iterator for MyIterator {
    type Item = i32;

    ...
}
```

Solver cần equality constraint:

```text
< T as Iterator >::Item == i32
```

---

# 43. Associated type canonicalization

Internal type:

```text
AssociatedType {
    trait: Iterator
    self: T
    assoc: Item
}
```

Trait solver cố resolve thành concrete type.

Nếu chưa đủ information, giữ obligation.

Nhưng trước MIR phải resolve nếu ABI/codegen cần concrete representation.

---

# 44. Trait ambiguity

Ví dụ có hai impl không phân biệt được:

```text
impl<T> Trait for T
impl<T> Trait for Vec<T>
```

nếu cả hai candidate cùng hợp lệ.

Axiom v1 **không có unrestricted specialization**.

→ ambiguity/error.

Không tự chọn “specific hơn” bằng heuristic.

---

# 45. Specialization

Không đưa unrestricted specialization vào v1.

Nếu sau này cần:

```text
default impl
specialized impl
```

phải thiết kế thành semantic feature riêng.

Đây là một trong những thứ dễ làm trait solver trở thành nightmare.

---

# 46. Coherence

Mỗi:

```text
(Trait, Type)
```

chỉ có một coherent implementation trong compilation universe.

Ví dụ:

```axiom
impl Display for User {}
```

không thể có impl thứ hai tương đương.

Generic impl cũng phải kiểm tra coherence.

---

# 47. Auto traits

Compiler-known:

```text
Copy
Send
Share
Drop
```

không cần user định nghĩa.

Ví dụ:

```text
struct Point {
    x: i32,
    y: i32,
}
```

compiler có thể derive:

```text
Copy
Send
Share
```

nếu các field thỏa điều kiện.

---

# 48. Copy không phải bitwise-copy

Đây là semantic rule đã frozen.

```text
Copy(T)
```

nghĩa là:

> Có thể tạo thêm một value độc lập mà không tạo thêm ownership obligation.

Không phải:

```text
memcpy(T)
```

Do đó type có custom Drop:

```text
Copy = false
```

---

# 49. Send

`Send(T)`:

> ownership của một value `T` có thể chuyển sang execution domain khác theo concurrency rules.

Không có nghĩa:

```text
T Share
```

---

# 50. Share

`Share(T)`:

> value/storage của `T` có thể được chia sẻ concurrent theo safe semantics.

Ví dụ:

```text
Arc<T>
```

có thể `Send`/`Share` theo property của `T`.

Nhưng:

```text
Arc<Mutex<T>>
```

không có nghĩa `T` tự nhiên trở thành Share.

---

# 51. Trait solver và auto trait

Ví dụ:

```axiom
spawn(move || process(data));
```

Compiler cần query:

```text
Send(closure)
```

Closure capture:

```text
data: T
```

→ solver kiểm tra:

```text
Send(T)
```

Nếu false:

```text
AX13xx value cannot be transferred to another execution domain
```

Đây là cách Axiom tránh bắt programmer viết annotation.

---

# 52. Generic bounds

Có thể viết:

```axiom
fn send<T: Send>(value: T) {
    ...
}
```

hoặc:

```axiom
fn send<T>(value: T)
where
    T: Send,
{
    ...
}
```

Hai syntax cùng semantic.

---

# 53. Trait bounds không phải runtime check

```axiom
fn sort<T: Ord>(...)
```

không tạo runtime:

```text
if T implements Ord ...
```

Static dispatch → trait resolution compile-time.

---

# 54. `dyn Trait`

Dynamic dispatch mới tạo runtime metadata.

Conceptually:

```text
dyn Trait
 ├── data pointer
 └── vtable pointer
```

Nhưng layout thực tế là ABI concern.

Không đưa layout này vào general Type System representation.

Type system chỉ biết:

```text
DynTraitType {
    trait: TraitId
}
```

---

# 55. Generic static dispatch

Ví dụ:

```axiom
fn draw<T: Shape>(shape: T) {
    shape.draw();
}
```

Mặc định:

```text
static dispatch
```

Compiler monomorphize.

Không vtable.

Không allocation.

---

# 56. Explicit dynamic dispatch

Nếu programmer viết:

```axiom
fn draw(shape: Box<dyn Shape>) {
    shape.draw();
}
```

thì dynamic dispatch.

Đây là semantic boundary rõ ràng.

---

# 57. Type inference và public API

Tôi đề xuất đóng quy tắc:

### Local

Inference mạnh.

```axiom
let x = foo(bar(10));
```

### Private function

Có thể inference return nếu muốn.

### Public function

Parameter/return type phải explicit.

### Struct fields

Phải explicit.

### Enum variants

Phải explicit.

### Trait signatures

Phải explicit.

### FFI

Tất cả phải explicit.

Lý do:

> API là contract, không phải puzzle cho compiler.

---

# 58. Generic inference

Cho phép:

```axiom
fn identity<T>(x: T) -> T

let x = identity(10);
```

Compiler suy ra:

```text
T = i32
```

Không cần:

```axiom
identity::<i32>(10)
```

Nhưng turbofish vẫn tồn tại khi ambiguity:

```axiom
identity::<u64>(10)
```

---

# 59. Trait inference và method call

Đây là chỗ các phase nối vào nhau.

```axiom
x.add(y)
```

Pipeline:

```text
AST MethodCall
       ↓
Resolver
       ↓
candidate methods
       ↓
Type inference
       ↓
Trait obligations
       ↓
Trait solver
       ↓
Resolved FunctionId
       ↓
HIR Call
```

Sau đó:

```text
MIR
```

không còn method lookup.

---

# 60. Type checking order

Đề xuất:

```text
Declaration signatures
        ↓
Type declarations
        ↓
Generic declarations
        ↓
Trait declarations
        ↓
Impl headers
        ↓
Function bodies
        ↓
Comptime bodies
        ↓
Closure inference
        ↓
Trait solving
        ↓
Typed HIR
```

---

# 61. Không tạo “universal constraint solver”

Type inference và trait solver nên tách:

```text
TypeInference
    ↓
Unification
    ↓
TypeConstraints

TraitSolver
    ↓
TraitObligations
    ↓
ImplResolution
```

Chúng giao tiếp qua type system.

Không tạo một SMT-like monster.

---

# 62. Type errors

Stable diagnostics:

```text
AX1301 could not infer type
AX1302 type mismatch
AX1303 invalid numeric conversion
AX1304 unknown type
AX1305 generic argument count mismatch
AX1306 trait bound not satisfied
AX1307 ambiguous trait implementation
AX1308 associated type unresolved
AX1309 associated type mismatch
AX1310 invalid method receiver
AX1311 invalid coercion
AX1312 expected callable type
AX1313 incompatible function signature
AX1314 recursive type has infinite size
```

Ví dụ:

```axiom
let x: i32 = "hello";
```

diagnostic:

```text
error AX1302:
expected `i32`
found `Text`
```

---

# 63. Type error phải hiển thị nguồn gốc constraint

Ví dụ:

```axiom
fn foo<T: Add>(x: T) -> T {
    x + 1
}
```

Nếu literal `1` gây ambiguity, compiler nên nói:

```text
error:
cannot resolve `T + integer`

required by:
    x + 1

because:
    T: Add

help:
    constrain the integer type or provide an appropriate Add implementation
```

Không chỉ báo:

```text
type mismatch
```

đơn độc.

Điều này cực kỳ quan trọng cho AI-assisted programming.

---

# 64. Type layout chưa thuộc COMPILER-003

Type System biết:

```text
StructId
field types
```

nhưng chưa quyết định:

```text
offset
padding
alignment
size
register ABI classification
```

Đó là:

```text
TYPE/LAYOUT
ABI
```

phase sau.

Tuy nhiên:

```text
size_of<T>()
align_of<T>()
```

sẽ được type system expose dưới dạng compile-time query, còn layout engine mới tính giá trị.

---

# 65. Type identity vs representation

Hai type:

```text
UserId
u64
```

có thể có representation giống nhau:

```text
64-bit integer
```

nhưng:

```text
TypeId(UserId) != TypeId(u64)
```

Do đó:

```text
type identity
```

và:

```text
representation identity
```

luôn tách biệt.

Điều này phù hợp với TYPE-001 đã đóng.

---

# 66. Opaque type

Axiom cần opaque type cho ABI/module abstraction.

Ví dụ library có:

```axiom
pub type FileHandle = opaque;
```

Consumer biết:

```text
FileHandle
```

nhưng không biết representation.

Compiler chỉ được sử dụng các operations public.

Layout không leak qua module boundary.

---

# 67. Type equality

Có ba khái niệm:

```text
Definitional equality
Nominal equality
Representation equality
```

### Definitional

```text
type A = B;
```

alias:

```text
A == B
```

### Nominal

```text
distinct u64
```

khác.

### Representation

Có thể cùng:

```text
size = 8
alignment = 8
```

nhưng vẫn khác type.

---

# 68. Type System pipeline

```text
AST Type
   ↓
Name Resolution
   ↓
TypeRef
   ↓
Canonicalization
   ↓
TypeId
   ↓
Inference
   ↓
Constraints
   ↓
Trait Solver
   ↓
Typed HIR
```

---

# 69. TypeInterner architecture

Đề xuất:

```text
TypeInterner
├── Primitive cache
├── Tuple cache
├── Array cache
├── Function cache
├── GenericInstance cache
├── View cache
├── MutView cache
├── Pointer cache
├── DynTrait cache
└── Alias/Opaque registry
```

Key:

```text
TypeKey
```

Ví dụ:

```text
GenericInstance(
    StructId(Vec),
    [TypeId(I32)]
)
```

→ canonical `TypeId`.

---

# 70. Generic instantiation key

Đã đóng trước đó:

```text
GenericId
+ TypeArgs
+ ConstArgs
+ Target ABI Context
```

Nhưng cần phân biệt:

```text
semantic instantiation
```

và:

```text
codegen specialization
```

Hai `Vec<i32>` ở hai target khác nhau vẫn cùng semantic type nhưng machine representation/codegen có thể khác.

---

# 71. Type system không biết register ABI

Ví dụ:

```text
struct Pair {
    a: i64,
    b: i64
}
```

Type system biết:

```text
Pair
```

ABI layer mới quyết định:

```text
RDI/RSI
```

hay:

```text
stack
```

hay:

```text
X0/X1
```

Không để target-specific logic xâm nhập type checker.

---

# 72. Invariant lớn nhất

Sau COMPILER-003:

> **Typed HIR phải chứa canonical TypeId cho mọi semantic expression/value/parameter/field.**

Không được còn:

```text
"i32"
"Vec"
"T"
```

dưới dạng string để compiler quyết định semantics.

---

# 73. COMPILER-003 invariants

```text
ATYPE-70  Every Semantic Type Has Canonical Identity
ATYPE-71  Type Interning Is Deterministic
ATYPE-72  Nominal Types Are Not Structural Types
ATYPE-73  Type Aliases Preserve Type Identity
ATYPE-74  Distinct Types Create New Nominal Identity
ATYPE-75  Representation Equality Does Not Imply Type Equality
ATYPE-76  Generic Instances Have Canonical Identity
ATYPE-77  Generic Parameters Have Stable Identity
ATYPE-78  Type Inference Is Deterministic
ATYPE-79  Inference Variables Cannot Reach Final Typed HIR
ATYPE-80  Literal Types May Adapt To Explicit Context
ATYPE-81  Typed Numeric Values Do Not Implicitly Narrow
ATYPE-82  Integer-To-Float Conversion Is Not Implicit For Typed Values
ATYPE-83  Numeric Promotion Is Not Implicit
ATYPE-84  Never Can Coerce To Any Compatible Type
ATYPE-85  Unit Is A Concrete Type
ATYPE-86  Function Types Include Calling Convention When Semantically Relevant
ATYPE-87  Closure Types Are Distinct From Function Pointer Types
ATYPE-88  Noncapturing Closures May Coerce To Function Pointers
ATYPE-89  View And MutView Are Semantic Capability Types
ATYPE-90  Raw Pointers Are Distinct From Safe Capabilities
ATYPE-91  Dyn Trait Is Explicit Dynamic Dispatch Abstraction
ATYPE-92  Static Generic Dispatch Does Not Require Runtime Metadata
ATYPE-93  Trait Bounds Are Compile-Time Obligations
ATYPE-94  Trait Resolution Completes Before MIR
ATYPE-95  Associated Types Are Type-Level Equalities
ATYPE-96  Coherence Is Deterministic
ATYPE-97  Unrestricted Specialization Is Not Required
ATYPE-98  Auto Traits Are Compiler-Known Semantic Properties
ATYPE-99  Public API Types Are Explicit
ATYPE-100 Local Type Inference Is Permitted
ATYPE-101 Type Errors Are Stable Diagnostics
ATYPE-102 Type Identity Is Independent Of Storage Strategy
ATYPE-103 Type System Does Not Encode Target Register ABI
ATYPE-104 Type System Does Not Encode Object File Format
```

---

# 74. Bây giờ một vấn đề lớn đã xuất hiện

Đến đây Axiom đã có:

```text
AST
 ↓
Resolver
 ↓
HIR
 ↓
Type System
 ↓
Trait Solver
```

Bước kế tiếp **không nên vội sang codegen**.

Phần còn thiếu và cực kỳ quan trọng là:

```text
Ownership
Capability
Move
Copy
View
MutView
Drop
Partial Move
Alias/Region
Escape
Closure Capture
```

Đây chính là **COMPILER-004 — Ownership + Capability Checker**.

Và đây sẽ là nơi chúng ta biến nguyên tắc trước đây:

> **“Programmer không viết borrow/lifetime; compiler tự quản lý lifetime và alias proof.”**

thành thuật toán compiler thực sự.

Đặc biệt cần thiết kế một **Ownership State Machine + Capability Graph + Region Graph**, thay vì cố bắt chước Rust Borrow Checker. Mục tiêu là checker mạnh nhưng không biến Axiom thành ngôn ngữ mà programmer phải “đấu” với compiler.