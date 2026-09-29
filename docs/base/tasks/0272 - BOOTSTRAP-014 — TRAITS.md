Tiếp theo là **BOOTSTRAP-014 — Trait System + Static/Dynamic Dispatch**.

Đây là mảnh ghép trực tiếp sau Generic. Nếu Generic cho phép “viết một lần cho nhiều type”, thì Trait trả lời câu hỏi **“type đó phải có khả năng gì?”** mà không cần class/inheritance.

# BOOTSTRAP-014 — TRAITS

## 1. Nguyên tắc lõi

Axiom giữ mô hình:

```text
struct  = data
fn      = behavior
trait   = contract
impl    = implementation
```

Ví dụ:

```axiom
struct Point {
    x: f64,
    y: f64,
}

trait Printable {
    fn print(self);
}

impl Printable for Point {
    fn print(self) {
        ...
    }
}
```

Không có:

```text
class
inheritance
base class
virtual method table mặc định
object header
```

---

# 2. Trait không phải class

Trait:

```axiom
trait Add {
    fn add(self, rhs: Self) -> Self;
}
```

không tạo object.

Nó chỉ mô tả:

```text
"Type X có hành vi Add"
```

Compiler có thể hoàn toàn xóa trait sau khi resolution.

---

# 3. Generic + Trait

Đây mới là combination quan trọng:

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    ...
}
```

Compiler giải:

```text
T
↓
trait constraint Ord
↓
concrete type
↓
implementation
```

Ví dụ:

```text
max<i32>
```

→ tìm:

```text
impl Ord for i32
```

→ resolve implementation.

Sau đó MIR không cần trait solver nữa.

---

# 4. `impl Trait for Type`

Cú pháp chính thức:

```axiom
impl Printable for Point {
    fn print(self) {
        ...
    }
}
```

Compiler tạo:

```text
TraitImplId
```

với:

```text
trait = Printable
type  = Point
methods[]
associated_types[]
```

---

# 5. Inherent methods

Không cần:

```text
impl Point {
}
```

và class.

Ta vẫn cho phép:

```axiom
fn length(self: Point) -> f64 {
    ...
}
```

gọi:

```axiom
p.length()
```

Semantic:

```axiom
length(p)
```

Điều này đã là nguyên tắc của Axiom.

---

# 6. Inherent implementation

Tuy nhiên để tổ chức API tốt, nên có:

```axiom
impl Point {
    fn length(self) -> f64 {
        ...
    }
}
```

Đây **không phải class**.

Nó chỉ là namespace cho các function có receiver.

Semantic vẫn là:

```text
function(Point)
```

chứ không có hidden object.

---

# 7. Method resolution

Khi gặp:

```axiom
p.length()
```

compiler tìm theo thứ tự:

```text
1. inherent method
2. trait implementation
3. explicitly imported extension method
4. generic extension
```

Nếu có hai ứng viên cùng mức ưu tiên:

```text
compile error
```

Không chọn dựa vào import order.

---

# 8. Extension method

Ví dụ library:

```axiom
fn clamp(self: i32, min: i32, max: i32) -> i32 {
    ...
}
```

có thể gọi:

```axiom
x.clamp(0, 100)
```

nếu function được import.

Nhưng đây vẫn chỉ là:

```text
clamp(x, 0, 100)
```

Không sửa type `i32`.

---

# 9. Trait method default

Trait có thể cung cấp implementation mặc định:

```axiom
trait Printable {
    fn print(self) {
        ...
    }
}
```

Type có thể dùng mặc định:

```axiom
impl Printable for Point {}
```

hoặc override:

```axiom
impl Printable for Point {
    fn print(self) {
        ...
    }
}
```

Không cần `override` keyword trong v1.

---

# 10. Vì sao không cần `override`

Trong class inheritance, `override` hữu ích để phát hiện typo:

```text
virtual method
↓
override
```

Axiom không có inheritance.

Trait implementation được compiler resolve theo:

```text
TraitId + TypeId + MethodId
```

nên typo sẽ thành compile error.

---

# 11. Associated type

Axiom nên hỗ trợ:

```axiom
trait Iterator {
    type Item;

    fn next(self) -> Option<Self::Item>;
}
```

Implementation:

```axiom
impl Iterator for MyIterator {
    type Item = i32;

    fn next(self) -> Option<i32> {
        ...
    }
}
```

Đây là feature rất quan trọng cho standard library.

---

# 12. Associated constants

Có thể hỗ trợ:

```axiom
trait Numeric {
    const ZERO: Self;
}
```

và:

```axiom
impl Numeric for i32 {
    const ZERO: i32 = 0;
}
```

Đây vẫn là compile-time/static information.

---

# 13. Associated functions

Không phải mọi trait function đều cần receiver:

```axiom
trait Default {
    fn default() -> Self;
}
```

Gọi:

```axiom
let x = Point::default();
```

Trait resolution tìm implementation tương ứng.

---

# 14. Trait constraints

Syntax:

```axiom
fn sort<T: Ord>(x: mut_view<T>) {
    ...
}
```

hoặc:

```axiom
fn sort<T>(x: mut_view<T>)
where
    T: Ord,
{
    ...
}
```

Hai form có cùng semantic representation:

```text
GenericConstraintSet
```

---

# 15. Multiple constraints

```axiom
fn process<T: Read + Write + Send>(x: T) {
    ...
}
```

Compiler lưu:

```text
T:
    Read
    Write
    Send
```

Không có runtime metadata nếu tất cả đều static.

---

# 16. Trait solver

Đây là một compiler subsystem riêng:

```text
TraitSolver
```

Input:

```text
Type
Trait
Environment
```

Output:

```text
Implemented
NotImplemented
Ambiguous
Error
```

Ví dụ:

```text
Does i32 implement Ord?
→ Yes

Does File implement Send?
→ Yes

Does Rc<T> implement Send?
→ No
```

---

# 17. Trait solver phải hoàn tất trước MIR

Pipeline:

```text
Typed HIR
   ↓
Trait Resolution
   ↓
Generic Instantiation
   ↓
Ownership/Capability
   ↓
MIR
```

MIR không được chứa query:

```text
"Does T implement X?"
```

Đây là invariant cực kỳ quan trọng để backend không phụ thuộc type system.

---

# 18. Coherence

Axiom cần tránh tình trạng:

```text
trait X for T
```

được định nghĩa bởi nhiều module khác nhau và kết quả phụ thuộc import.

Quy tắc v1:

> Một implementation `(Trait, Type)` phải có một nguồn sở hữu rõ ràng.

Orphan rule:

```text
impl Trait for Type
```

được phép nếu:

```text
Trait là local
OR
Type là local
```

Không được nếu cả hai đều đến từ foreign package.

---

# 19. Ví dụ coherence

Package A:

```axiom
trait Serialize { ... }
```

Package B:

```axiom
struct User { ... }
```

Package C không được tùy tiện:

```axiom
impl Serialize for User
```

nếu cả `Serialize` và `User` đều foreign.

Nếu không có quy tắc này, dependency graph có thể tạo implementation conflict.

---

# 20. Không unrestricted specialization

Không cho v1:

```axiom
impl<T> Foo for T { ... }

impl Foo for i32 { ... }
```

rồi compiler phải quyết định implementation nào “đặc biệt hơn”.

Điều đó làm trait solver phức tạp và dễ tạo ambiguity.

V1:

```text
overlap → error
```

---

# 21. Static dispatch

Mặc định:

```axiom
fn print<T: Printable>(x: T) {
    x.print();
}
```

Nếu gọi:

```axiom
print(point);
```

compiler resolve thành:

```text
Point::print
```

và có thể inline.

Không có:

```text
vtable lookup
```

---

# 22. Đây là zero-cost abstraction

Source:

```axiom
fn process<T: Add>(a: T, b: T) -> T {
    return a.add(b);
}
```

Sau monomorphization:

```text
process<i32>
```

có thể trở thành trực tiếp:

```text
add i32
```

Trait abstraction biến mất.

---

# 23. Dynamic dispatch phải explicit

Nếu thực sự cần runtime polymorphism:

```axiom
dyn Printable
```

Ví dụ:

```axiom
fn print_all(items: view<dyn Printable>) {
    ...
}
```

hoặc thông qua owning storage:

```axiom
Box<dyn Printable>
```

Điểm quan trọng:

> **`dyn Trait` là yêu cầu runtime dynamic dispatch.**

Compiler không tự biến generic thành dynamic dispatch.

---

# 24. `dyn Trait` không phải ownership

```text
dyn Printable
```

chỉ nói:

```text
"interface được dùng dynamically"
```

Không nói:

```text
heap
ownership
reference counting
```

Có thể có:

```text
view<dyn Trait>
Box<dyn Trait>
Arc<dyn Trait>
```

mỗi cái có ownership/storage semantics riêng.

---

# 25. Vtable

`dyn Trait` thường được biểu diễn bằng:

```text
data pointer
vtable pointer
```

nhưng đây là **ABI implementation detail**.

MIR chỉ cần:

```text
DynCall {
    receiver,
    method_id,
    args
}
```

ABI lowering mới quyết định:

```text
fat pointer
vtable
calling convention
```

---

# 26. Không có hidden vtable

Struct bình thường:

```axiom
struct Point {
    x: f64,
    y: f64,
}
```

không chứa:

```text
vptr
```

Ngay cả khi `Point` implements 20 traits.

Vtable chỉ tồn tại ở dynamic-dispatch representation.

---

# 27. Dynamic dispatch không tự allocation

Ví dụ:

```axiom
let p: dyn Printable = point;
```

không được tự động biến thành:

```text
heap allocate
copy point
```

Nếu representation yêu cầu owning dynamic object, programmer phải yêu cầu:

```axiom
Box<dyn Printable>
```

hoặc abstraction tương ứng.

---

# 28. Trait object compatibility

Không phải trait nào cũng có thể trở thành `dyn Trait`.

Ví dụ method:

```axiom
trait Bad {
    fn clone(self) -> Self;
}
```

khó dynamic dispatch vì return type `Self` có kích thước động.

Compiler phải kiểm tra:

```text
ObjectSafety
```

trước khi cho phép:

```text
dyn Bad
```

---

# 29. Trait object không có generic method tùy ý

Ví dụ:

```axiom
trait Bad {
    fn foo<T>(self, x: T);
}
```

không thể tạo một vtable hữu hạn chứa mọi `T`.

Do đó dynamic trait compatibility phải reject trường hợp này, hoặc yêu cầu một abstraction khác.

---

# 30. Trait object method table

Conceptually:

```text
TraitObject {
    data
    vtable
}
```

Vtable:

```text
TraitVTable {
    drop
    size
    align
    method_0
    method_1
    ...
}
```

Nhưng Axiom không bắt buộc chính representation này.

Compiler có thể thay đổi ABI nội bộ.

---

# 31. `dyn Trait` ABI boundary

Nếu:

```axiom
extern fn f(x: dyn Trait)
```

thì không được coi đây là ABI ổn định mặc định.

Foreign ABI phải dùng representation explicit:

```text
@repr(C)
```

hoặc opaque handle / C-compatible vtable structure.

---

# 32. Trait + ownership

Trait không phá ownership.

Ví dụ:

```axiom
fn consume<T: Printable>(x: T) {
    ...
}
```

`T` là owning parameter.

Nếu `T` non-Copy:

```text
caller
  ↓ Move
consume
```

Nếu:

```axiom
fn inspect<T: Printable>(x: view<T>)
```

thì chỉ tạo READ capability.

---

# 33. Trait + `mut_view`

```axiom
fn update<T: Updatable>(x: mut_view<T>) {
    x.update();
}
```

Capability checker vẫn kiểm tra:

```text
WRITE
exclusive
region
provenance
lifetime
```

Trait solver không được làm mất các thông tin này.

---

# 34. Auto traits

Một số property compiler tự suy luận:

```text
Copy
Send
Share
Drop
```

Ví dụ:

```text
struct Pair<A,B>
```

compiler có thể suy ra:

```text
Copy(Pair<A,B>)
    iff Copy(A) && Copy(B)
```

Tương tự:

```text
Send(Pair<A,B>)
    iff Send(A) && Send(B)
```

Đây là **compiler-known semantic properties**, không nhất thiết là ordinary user traits.

---

# 35. Vì sao `Copy` không chỉ là trait bình thường?

Vì compiler phải biết `Copy` ở rất nhiều phase:

```text
ownership
MIR
move analysis
drop analysis
optimization
ABI
```

Nếu biến nó thành trait library bình thường, compiler sẽ tạo circular dependency.

Do đó:

```text
Copy = compiler semantic property
```

là hướng đúng.

---

# 36. Operator overloading

Có thể dùng trait:

```axiom
trait Add<Rhs> {
    type Output;

    fn add(self, rhs: Rhs) -> Self.Output;
}
```

Sau đó:

```axiom
a + b
```

lower thành:

```text
Add::add(a, b)
```

Nhưng không cho trait overload các control-flow operators tùy ý như:

```text
if
while
return
await
```

---

# 37. Operator syntax phải deterministic

Không cho nhiều `Add` implementation hợp lệ cho cùng:

```text
(A, B)
```

Nếu ambiguity:

```text
compile error
```

Không dùng “best match” heuristic phức tạp.

---

# 38. Trait aliases

Không cần v1.

Ví dụ:

```text
trait Numeric = Add + Sub + Mul + Div;
```

có thể thêm sau.

Ban đầu dùng:

```axiom
T: Add + Sub + Mul + Div
```

đã đủ.

---

# 39. Blanket implementation

Có thể cần:

```axiom
impl<T: Display> ToString for T {
    ...
}
```

Nhưng phải được kiểm soát bởi coherence.

Nếu compiler v1 chưa ổn định trait solver, nên giới hạn blanket impl trong bootstrap.

---

# 40. Trait resolution cache

Trait solver nên có:

```text
TraitQueryCache
```

key:

```text
TraitId
+
CanonicalType
+
GenericEnvironment
```

Ví dụ:

```text
(i32, Ord)
→ Yes
```

Không resolve lại hàng nghìn lần.

---

# 41. Trait cycle

Ví dụ:

```text
A<T> requires B<T>
B<T> requires A<T>
```

Compiler cần detect cycle.

Không được:

```text
infinite recursion
compiler crash
```

Mà phải trả diagnostic có cycle chain.

---

# 42. Trait solver không được phụ thuộc compilation order

Kết quả:

```text
Trait(T, X)
```

không phụ thuộc:

```text
module compile order
thread scheduling
hash iteration
```

Điều này quan trọng cho reproducible build.

---

# 43. Generic + Trait + MIR

Ví dụ:

```axiom
fn add_one<T: Add<i32, Output=T>>(x: T) -> T {
    return x + 1;
}
```

Call:

```axiom
add_one<i32>(10)
```

Pipeline:

```text
parse
 ↓
resolve generic
 ↓
trait solve
 ↓
select Add<i32> for i32
 ↓
monomorphize
 ↓
MIR
```

MIR cuối cùng có thể là:

```text
%1 = CONST i32 1
%2 = ADD %x, %1
RETURN %2
```

Không còn:

```text
T
TraitId
TraitSolver
```

---

# 44. Dynamic dispatch pipeline khác

```axiom
fn print(x: dyn Printable) {
    x.print();
}
```

Pipeline:

```text
HIR
 ↓
Object Safety
 ↓
Dyn Trait Resolution
 ↓
MIR DynCall
 ↓
ABI Lowering
 ↓
vtable/data representation
 ↓
indirect call
```

Đây là một trong rất ít trường hợp trait information thực sự dẫn đến runtime machinery.

---

# 45. Trait implementation không tạo allocation

```axiom
impl Printable for Point
```

không tạo:

```text
heap
runtime registry
global object table
```

Trait implementation là compiler metadata.

---

# 46. Không runtime type registry

Axiom không có:

```text
TypeRegistry
ObjectRegistry
ClassRegistry
```

trong runtime mặc định.

Nếu programmer cần runtime reflection:

```text
comptime reflection
→ explicit metadata emission
```

như đã thống nhất.

---

# 47. Trait + FFI

Không expose Axiom trait trực tiếp qua C ABI mặc định.

Thay vào đó:

```text
C-compatible struct
+
function pointers
+
opaque handle
```

Ví dụ:

```text
CPlugin {
    ctx: *mut void,
    process: extern "C" fn(...)
}
```

Đây chính là representation mà `dyn Trait` có thể lower tới khi programmer muốn ABI ổn định, nhưng FFI representation phải explicit.

---

# 48. Trait solver architecture

Đề xuất:

```text
compiler/traits/
├── trait_def
├── impl_def
├── environment
├── canonicalize
├── normalize
├── solver
├── coherence
├── object_safety
├── associated_type
├── auto_traits
└── cache
```

Không để trait logic rải rác trong type checker.

---

# 49. MIR boundary

Gate rất quan trọng:

```text
HIR
 ↓
TypeChecker
 ↓
TraitSolver
 ↓
GenericInstantiation
 ↓
OwnershipChecker
 ↓
CapabilityChecker
 ↓
MIR
```

Sau MIR:

```text
TraitSolver = OFF
GenericSolver = OFF
```

Backend chỉ xử lý concrete semantics.

---

# 50. Invariants

```text
ATRAIT-75  Trait Identity Is Nominal
ATRAIT-76  Trait Implementations Have Stable Identity
ATRAIT-77  Inherent Methods Are Ordinary Functions
ATRAIT-78  Method Syntax Does Not Imply Object Identity
ATRAIT-79  Static Dispatch Is Default
ATRAIT-80  Generic Trait Dispatch Is Compile-Time
ATRAIT-81  Trait Resolution Completes Before MIR
ATRAIT-82  MIR Contains Resolved Trait Dispatch
ATRAIT-83  Trait Constraints Do Not Require Runtime Metadata
ATRAIT-84  Trait Resolution Is Deterministic
ATRAIT-85  Trait Resolution Is Cacheable
ATRAIT-86  Coherence Is Deterministic
ATRAIT-87  Overlapping Implementations Are Rejected In v1
ATRAIT-88  Unrestricted Specialization Is Not Required
ATRAIT-89  Associated Types Are Compile-Time
ATRAIT-90  Associated Constants Are Compile-Time
ATRAIT-91  Default Trait Methods May Be Overridden
ATRAIT-92  Override Does Not Require A Keyword
ATRAIT-93  Dynamic Dispatch Requires Explicit dyn Trait
ATRAIT-94  Dynamic Dispatch Does Not Imply Allocation
ATRAIT-95  dyn Trait Does Not Imply Ownership
ATRAIT-96  dyn Trait Requires Object-Safe Interface
ATRAIT-97  Vtables Exist Only Where Dynamic Dispatch Requires Them
ATRAIT-98  Normal Structs Have No Implicit Vtable
ATRAIT-99  Trait Implementations Do Not Create Runtime Registries
ATRAIT-100 Trait Resolution Preserves Ownership Semantics
ATRAIT-101 Trait Resolution Preserves Capability Semantics
ATRAIT-102 Auto Traits Are Compiler-Known Properties
ATRAIT-103 Trait Cycles Are Diagnosed
ATRAIT-104 Trait Solver Does Not Depend On Compilation Order
ATRAIT-105 FFI Trait Representation Must Be Explicit
ATRAIT-106 Trait Metadata May Be Erased After Verification
```

---

# 51. BOOT-014 gate

```text
Trait declaration                  ✓
impl Trait for Type                ✓
Inherent impl                      ✓
Method resolution                  ✓
Default methods                    ✓
Override implementation            ✓
Trait constraints                  ✓
Multiple constraints               ✓
Associated type                   ✓
Associated constant               ✓
Associated function               ✓
Coherence                          ✓
Trait solver                       ✓
Solver cache                       ✓
Trait cycle detection              ✓
Auto Copy/Send/Share               ✓
Static dispatch                    ✓
dyn Trait object                   ✓
Object safety                      ✓
Vtable generation                  ✓
Ownership + traits                 ✓
Capability + traits                ✓
MIR resolved dispatch              ✓
No trait solver in backend         ✓
```

---

## Và đây là điểm rất quan trọng đối với triết lý Axiom

Sau Generic + Trait, mô hình ngôn ngữ của Axiom gần như đã hoàn chỉnh ở tầng abstraction:

```text
                 Axiom abstraction
                       │
        ┌──────────────┼──────────────┐
        │              │              │
      struct         generic         trait
        │              │              │
       data       compile-time      contract
        │              │              │
        └──────────────┼──────────────┘
                       ↓
                  concrete code
                       ↓
                    MIR
                       ↓
                native machine
```

Không cần:

```text
class
inheritance
GC
object header
implicit vtable
implicit boxing
runtime generic metadata
runtime type registry
borrow syntax
lifetime syntax
```

Trong đó **compiler có thể cực kỳ phức tạp bên trong**, nhưng lập trình viên chỉ phải nhìn thấy những abstraction thực sự có ý nghĩa.

Bước tiếp theo hợp lý sẽ là **BOOTSTRAP-015 — Closures + Function Values**, bởi lúc đó Axiom đã có Generic + Trait và cần giải quyết hoàn chỉnh callable abstraction trước khi đi sâu vào Comptime/Optimization.