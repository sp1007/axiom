Tiếp tục tự động sang **COMPILER-002 — Name Resolution, Module System, AST → HIR**.

Đây là bước rất quan trọng vì từ đây Axiom bắt đầu biến cú pháp “dễ viết” thành một representation có **identity và semantics rõ ràng**.

# COMPILER-002 — Resolver + HIR

## 1. Mục tiêu

Pipeline:

```text
Source
  ↓
Lexer
  ↓
Parser
  ↓
AST
  ↓
Name Resolution
  ↓
Desugaring
  ↓
HIR
```

Sau COMPILER-002, HIR phải đảm bảo:

- mọi tên đã được resolve;
- mọi symbol có identity ổn định;
- mọi module/import đã được xác định;
- mọi method call đã biết candidate set;
- mọi generic parameter có identity;
- mọi `self`/`Self` đã được resolve;
- syntax sugar cơ bản đã biến mất;
- HIR **chưa cần type-check hoàn chỉnh**;
- HIR chưa chứa ownership/capability verification.

Nguyên tắc:

> **AST trả lời “programmer viết gì”; HIR trả lời “compiler đang xử lý entity nào”.**

---

# 2. Symbol Identity

Không được dùng string làm identity nội bộ.

Ví dụ:

```axiom
fn foo() {}
```

không nên nội bộ được đại diện bằng:

```text
"foo"
```

mà:

```text
FunctionId(42)
```

Tương tự:

```text
ModuleId
StructId
EnumId
TraitId
ImplId
FieldId
VariantId
TypeAliasId
ConstId
LocalId
GenericParamId
```

### SymbolId

Đề xuất:

```text
SymbolId {
    module: ModuleId
    index: u32
}
```

hoặc đơn giản hơn:

```text
SymbolId = u64
```

với arena/interning nội bộ.

Compiler tuyệt đối không phụ thuộc vào địa chỉ RAM của object compiler.

---

# 3. Symbol Table

Mỗi scope có namespace:

```text
Scope {
    parent
    values
    types
    modules
    labels
}
```

Axiom nên **tách namespace type/value**.

Ví dụ:

```axiom
struct Foo {
    value: i32;
}

fn Foo() {
}
```

có thể tồn tại:

```text
type namespace:
    Foo → StructId

value namespace:
    Foo → FunctionId
```

Điều này giúp tránh những hạn chế không cần thiết.

---

# 4. Không cần namespace riêng cho method

Method:

```axiom
impl Vec {
    fn length(self) -> usize {}
}
```

không được đưa vào global value namespace như:

```text
length
```

Nó thuộc:

```text
ImplId → MethodSet
```

Do đó:

```axiom
v.length()
```

mới được resolver xử lý thông qua receiver type.

---

# 5. Module Identity

Module không đồng nhất với file.

Ví dụ:

```text
src/
    main.ax
    math.ax
```

có thể tạo:

```text
ModuleId(0) = crate
ModuleId(1) = crate::math
```

Filename chỉ là cách materialize module.

Điều này phù hợp với nguyên tắc đã chốt:

> Module identity là logical identity, không phải filename.

---

# 6. Module tree

Ví dụ:

```axiom
mod graphics;
mod audio;
```

tạo:

```text
crate
 ├── graphics
 └── audio
```

Inline:

```axiom
mod graphics {
    ...
}
```

cũng tạo cùng loại `ModuleId`.

Compiler không được phân biệt semantic giữa:

```text
graphics.ax
```

và:

```text
mod graphics { ... }
```

sau module loading.

---

# 7. Visibility

Axiom dùng:

```axiom
pub fn foo() {}
```

và:

```axiom
fn private() {}
```

Visibility model tối thiểu:

```text
Private
Public
```

Không đưa ngay hệ thống:

```text
pub(crate)
pub(super)
protected
friend
internal
```

vào v1.

Compiler có thể mở rộng sau mà không phá semantics hiện tại.

---

# 8. `use`

Ví dụ:

```axiom
use std::io::File;
```

Resolver xử lý thành:

```text
Import {
    source: std::io::File
    local_name: File
}
```

Alias:

```axiom
use std::io::File as InputFile;
```

→

```text
InputFile → FileId
```

Import không tạo symbol mới về mặt semantic.

Nó chỉ tạo **local binding tới symbol hiện hữu**.

---

# 9. Import group

```axiom
use std::io::{File, Reader, Writer};
```

được desugar thành:

```text
use std::io::File;
use std::io::Reader;
use std::io::Writer;
```

trong HIR/resolution graph.

---

# 10. Import module

```axiom
use std::io;
```

cho phép:

```axiom
io::File
```

Không tự động import toàn bộ symbol vào scope.

Đây là chủ ý để tránh namespace pollution.

---

# 11. Không có wildcard import trong Core v1

Tôi đề xuất **không hỗ trợ**:

```axiom
use std::io::*;
```

ở v1.

Lý do không phải vì compiler khó làm.

Mà vì nó làm:

- diagnostics khó hơn;
- AI sinh code khó predict hơn;
- dependency namespace khó đọc;
- name collision khó hiểu;
- incremental resolution phức tạp hơn.

Sau này library tooling có thể cho phép nếu thực sự cần.

---

# 12. Resolution hai pha

Một file/module không nên được resolve từ trên xuống đơn giản.

Ví dụ:

```axiom
fn a() {
    b();
}

fn b() {
}
```

phải hợp lệ.

Vì vậy module được xử lý:

### Phase 1 — Declaration collection

Thu thập:

```text
functions
structs
enums
traits
impls
types
consts
modules
```

### Phase 2 — Body resolution

Sau khi declaration namespace tồn tại:

```text
fn a body
→ b → FunctionId
```

Điều này cũng cho phép forward reference.

---

# 13. Forward declaration không cần

Không cần:

```axiom
fn b();

fn a() {
    b();
}

fn b() {}
```

Axiom không dùng header declaration như C.

Một declaration hoàn chỉnh là đủ.

---

# 14. Duplicate declaration

Ví dụ:

```axiom
fn foo() {}
fn foo() {}
```

→ compile error.

Nhưng overload **không phải mặc định**.

Tôi khuyến nghị:

> Axiom v1 không có function overloading theo parameter types.

Tức:

```axiom
fn print(i32) {}
fn print(f64) {}
```

không được phép cùng namespace.

Thay vào đó:

```axiom
print_i32()
print_f64()
```

hoặc trait/generic:

```axiom
fn print<T: Display>(value: T)
```

Lý do:

- resolver đơn giản;
- ABI đơn giản;
- diagnostics rõ;
- generic/trait solver chịu trách nhiệm abstraction;
- giảm ambiguity cho AI.

---

# 15. Generic parameter identity

```axiom
fn identity<T>(x: T) -> T {
    x
}
```

`T` không phải `TypeId`.

Nó là:

```text
GenericParamId(0)
```

Ví dụ:

```text
FunctionId = 20

GenericParams:
    T → GenericParamId(0)
```

Trong body:

```text
x: T
```

tham chiếu đến chính `GenericParamId(0)`.

---

# 16. `Self`

Trong trait:

```axiom
trait Display {
    fn display(self);
}
```

`Self` là implicit generic parameter đặc biệt của trait.

Trong impl:

```axiom
impl Display for User {
}
```

`Self` được instantiate thành:

```text
User
```

Trong inherent impl:

```axiom
impl User {
}
```

`Self = User`.

Không tạo runtime type object.

---

# 17. `self`

Parser nhận:

```axiom
fn length(self) -> usize
```

Resolver biến receiver thành parameter:

```text
Parameter {
    receiver_kind: Value
    local_id: LocalId
}
```

Tương tự:

```axiom
fn scale(mut self)
```

là mutable receiver.

Không có reference syntax.

---

# 18. HIR không còn syntax `self` đặc biệt

Sau desugar:

```text
fn length(self)
```

trở thành conceptually:

```text
fn length(__receiver: Self)
```

Nhưng HIR có thể vẫn đánh dấu:

```text
receiver = true
```

để method resolution/diagnostics dễ dàng.

Sau đó MIR không còn khái niệm method.

---

# 19. Method Resolution — điểm quan trọng nhất

Khi gặp:

```axiom
v.length()
```

compiler không lập tức biến thành function call.

Nó tạo:

```text
MethodCall {
    receiver = v
    name = length
    args = []
}
```

Type checking sau đó xác định receiver type.

Nhưng resolver có thể thu hẹp candidate set dựa trên:

- lexical/module scope;
- inherent impl;
- imported extension;
- trait namespace.

---

# 20. Thứ tự method lookup

Đóng theo thứ tự:

```text
1. Inherent methods
2. Trait methods explicitly available
3. Explicitly imported extension methods
4. Generic extension methods
```

Nếu có nhiều candidate cùng priority:

```text
compile error: ambiguous method
```

Không tự chọn theo “gần nhất” nếu có ambiguity thực sự.

---

# 21. Inherent method

```axiom
struct Vec2 {
    x: f32,
    y: f32,
}

impl Vec2 {
    fn length(self) -> f32 {
        ...
    }
}
```

`length` là inherent.

Không cần trait.

---

# 22. Trait method

```axiom
trait Printable {
    fn print(self);
}

impl Printable for User {
    fn print(self) {
    }
}
```

Khi trait nằm trong scope:

```axiom
use mylib::Printable;

user.print();
```

method có thể được resolve.

---

# 23. Extension method

Axiom không cần một language feature riêng cho extension method.

Ví dụ:

```axiom
fn is_even(x: i32) -> bool {
    x % 2 == 0
}
```

Nếu function được khai báo trong extension namespace phù hợp:

```axiom
use math::is_even;

x.is_even()
```

resolver có thể xem:

```text
is_even(x)
```

nhưng **chỉ khi function được explicitly imported**.

Đây chính là cách giữ method syntax mà không cần class.

---

# 24. Quy tắc extension

Một function được method-call candidate nếu:

```text
first parameter type
```

phù hợp receiver.

Ví dụ:

```axiom
fn length(v: Vec2) -> f32
```

cho phép:

```axiom
v.length()
```

Nhưng:

```axiom
fn length(x: i32) -> f32
```

không candidate cho `Vec2`.

---

# 25. Không tự động import extension toàn hệ thống

Đây là quyết định quan trọng.

Không:

```text
std::* extension methods
```

tự động xuất hiện.

Nếu muốn:

```axiom
use math::is_even;
```

thì mới có:

```axiom
x.is_even()
```

Điều này làm method lookup predictable.

---

# 26. Generic extension

Ví dụ:

```axiom
fn first<T>(items: view<T>) -> Option<T> {
    ...
}
```

có thể gọi:

```axiom
items.first()
```

nhưng chỉ sau khi extension được import.

Trait solver/type checker chịu trách nhiệm generic matching.

---

# 27. Không có implicit method allocation

Nếu:

```axiom
v.method()
```

resolve thành static function:

```text
method(v)
```

thì:

- không allocation;
- không object;
- không vtable;
- không runtime metadata.

Đây là syntax sugar thuần compile-time.

---

# 28. Dynamic dispatch

Nếu programmer viết:

```axiom
let x: dyn Display = ...;
```

thì compiler mới tạo dynamic dispatch semantics.

Thông thường phải có storage:

```axiom
Box<dyn Display>
Arc<dyn Display>
```

hoặc abstraction tương ứng.

Resolver chỉ xác định:

```text
dyn Display
```

Type system/ABI mới quyết định vtable layout.

---

# 29. `impl` identity

Mỗi:

```axiom
impl Trait for Type
```

có:

```text
ImplId
```

Ví dụ:

```text
ImplId(10)
TraitId(4)
Type = User
```

Method table:

```text
ImplId(10):
    display → FunctionId(82)
```

---

# 30. Coherence

Ngay từ resolver cần xây dữ liệu cho coherence.

Không cho:

```text
impl ForeignTrait for ForeignType
```

nếu cả trait và type đều không local.

Orphan rule v1:

> Một impl chỉ hợp lệ nếu trait hoặc type là local với package/module authority tương ứng.

Chi tiết package ownership sẽ được hoàn thiện ở compiler/package phase.

---

# 31. HIR

HIR nên ít node hơn AST.

Ví dụ AST:

```text
ForExpr
```

HIR:

```text
Loop
    Init
    Condition/Iterator state
    Body
```

AST:

```text
MethodCall
```

sau resolution:

```text
Call {
    callee: ResolvedFunction
    receiver: ...
}
```

AST:

```text
use
```

không còn trong HIR executable body.

---

# 32. HIR Declaration

Đề xuất:

```text
HirModule {
    id: ModuleId
    items: Vec<HirItem>
}
```

```text
HirItem =
    Function
    Struct
    Enum
    Trait
    Impl
    TypeAlias
    Const
    Static
    Module
    Extern
}
```

Mỗi declaration dùng stable ID.

---

# 33. HIR Function

```text
HirFunction {
    id: FunctionId
    name: SymbolName
    visibility: Visibility
    generics: GenericParams
    params: Vec<HirParam>
    return_type: HirTypeRef
    body: HirExpr
    attributes: Attributes
}
```

Ở COMPILER-002, `HirTypeRef` có thể vẫn chưa phải fully typed type.

Ví dụ:

```text
Vec<i32>
```

được resolve thành:

```text
TypePath {
    symbol: StructId(Vec)
    args: [i32]
}
```

nhưng canonical `TypeId` sẽ được Type System tạo sau.

---

# 34. HIR local

```axiom
let x = 10;
```

AST:

```text
LetStmt {
    pattern: Binding("x")
    initializer: 10
}
```

HIR:

```text
Let {
    local: LocalId(7)
    initializer: Literal(10)
}
```

Từ đây compiler không còn cần search string `"x"` để biết local nào.

---

# 35. Shadowing

Cho phép:

```axiom
let x = 10;

{
    let x = 20;
    print(x);
}

print(x);
```

Hai `x`:

```text
LocalId(1)
LocalId(2)
```

khác nhau.

Không phải cùng symbol.

---

# 36. Shadowing cùng scope

Tôi đề xuất **không cho phép**:

```axiom
let x = 10;
let x = 20;
```

trong cùng lexical scope.

Lý do:

- tránh typo;
- diagnostics đơn giản;
- AI sinh code dễ kiểm soát.

Nhưng nested scope shadowing hợp lệ.

Nếu muốn đổi giá trị:

```axiom
var x = 10;
x = 20;
```

---

# 37. Pattern binding

```axiom
let Some(x) = value;
```

Resolver tạo:

```text
LocalId(x)
```

nhưng semantic checker sau này quyết định pattern có exhaustive/irrefutable không.

---

# 38. Labels

Loop labels nếu cần:

```axiom
'outer: loop {
    loop {
        break 'outer;
    }
}
```

Tuy nhiên vì Axiom không dùng lifetime syntax, `'outer` dễ gây nhầm.

Tôi đề xuất syntax khác:

```axiom
outer: loop {
    loop {
        break outer;
    }
}
```

Parser phân biệt label context.

Như vậy:

```text
'label
```

không tồn tại trong language.

---

# 39. HIR không giữ syntax sugar không cần thiết

Ví dụ:

```axiom
v.length()
```

→ resolved call.

```axiom
for x in xs {}
```

→ iterator/control-flow HIR.

```axiom
else if
```

→ nested `if`.

```axiom
self
```

→ receiver local.

```axiom
use
```

→ module dependency metadata.

Mục tiêu:

> MIR không bao giờ phải biết parser từng có syntax gì.

---

# 40. Nhưng HIR chưa được phép “quá thấp”

Không biến ngay:

```axiom
if x {}
```

thành:

```text
BasicBlock 12
BasicBlock 13
Branch
```

Đó là MIR.

HIR vẫn giữ high-level semantic constructs:

```text
If
Match
Loop
Call
Closure
Async
```

MIR mới lower chúng thành CFG.

---

# 41. HIR Type Reference

Có ba trạng thái:

```text
UnresolvedTypePath
ResolvedTypeSymbol
CanonicalType
```

COMPILER-002 chỉ cần đạt:

```text
UnresolvedTypePath
        ↓
ResolvedTypeSymbol
```

COMPILER-003:

```text
ResolvedTypeSymbol
        ↓
Canonical TypeId
```

Điều này giữ phase boundary sạch.

---

# 42. Name resolution algorithm

Pipeline:

```text
1. Load module graph
2. Create ModuleIds
3. Create scopes
4. Collect declarations
5. Resolve imports
6. Resolve type names
7. Resolve value names
8. Resolve trait/impl names
9. Resolve method candidate sets
10. Create HIR
```

Nhưng body expression resolution có thể trì hoãn đến sau declaration collection.

---

# 43. Dependency graph

Module graph:

```text
A
├── B
├── C
└── D
```

Compiler cần phân biệt:

```text
declaration dependency
```

và:

```text
runtime initialization dependency
```

Ví dụ:

```axiom
const A = B;
const B = A;
```

có thể tạo cyclic dependency.

Không được resolver tự quyết định runtime semantics.

Build/compiler phase sau phải phát hiện cycle phù hợp.

---

# 44. Circular type declarations

Cho phép finite recursive types:

```axiom
struct Node {
    next: Option<Box<Node>>,
}
```

Resolver có thể tạo:

```text
Node → Node
```

mà không cần layout ngay.

Type layout phase sau mới kiểm tra finite representation.

---

# 45. Recursive value không indirection

```axiom
struct Bad {
    next: Bad,
}
```

resolver vẫn có thể resolve `Bad`.

Nhưng Type/Layout phase sẽ báo:

```text
recursive type has infinite size
```

Không đẩy semantic này vào resolver.

---

# 46. Resolver cache

Resolution nên cache:

```text
Name + Scope + Namespace
```

→ `SymbolId`.

Nhưng không dùng cache làm semantic authority.

Cache invalidation phải theo module semantic fingerprint.

---

# 47. Determinism

Cùng source + cùng dependency graph:

```text
SymbolId assignment
```

phải deterministic.

Không để hash map iteration order quyết định ID.

Ví dụ declaration order:

```text
foo
bar
baz
```

→ ID ổn định theo source/module order.

---

# 48. Diagnostics

Resolver:

```text
AX1201 unknown name
AX1202 unknown type
AX1203 unknown module
AX1204 private symbol
AX1205 duplicate declaration
AX1206 duplicate import
AX1207 ambiguous name
AX1208 ambiguous method
AX1209 invalid receiver
AX1210 unresolved trait
AX1211 invalid Self usage
AX1212 invalid generic parameter
AX1213 import cycle
```

Compiler phải đưa candidate suggestions:

```text
AX1201 unknown name `pritn`

help: did you mean `print`?
```

Nhưng suggestion không thay đổi AST tự động.

---

# 49. HIR invariant cực quan trọng

Sau resolver:

> **Không còn identifier string nào có vai trò semantic resolution trong HIR.**

Ví dụ:

```text
x
```

phải là:

```text
LocalId(42)
```

`Vec`:

```text
StructId(7)
```

`foo`:

```text
FunctionId(19)
```

`Display`:

```text
TraitId(3)
```

Đây là một invariant rất đáng giá cho compiler architecture.

---

# 50. COMPILER-002 invariants

```text
ARES-20  Every Semantic Declaration Has Stable Identity
ARES-21  Symbol Identity Is Independent Of Memory Address
ARES-22  Module Identity Is Logical
ARES-23  Type And Value Namespaces Are Distinct
ARES-24  Declaration Collection Precedes Body Resolution
ARES-25  Forward References Are Deterministic
ARES-26  Duplicate Same-Scope Declarations Are Rejected
ARES-27  Nested Scope Shadowing Is Explicitly Defined
ARES-28  Imports Do Not Create New Semantic Symbols
ARES-29  Wildcard Imports Are Not Core v1
ARES-30  Visibility Is Checked During Resolution
ARES-31  Method Lookup Is Deterministic
ARES-32  Inherent Methods Have Highest Priority
ARES-33  Explicit Trait Methods Are Resolvable
ARES-34  Explicit Extensions Are Resolvable
ARES-35  Ambiguous Method Resolution Is An Error
ARES-36  Method Syntax Does Not Imply Runtime Dispatch
ARES-37  Static Method Resolution Produces Direct Callee Identity
ARES-38  Dynamic Dispatch Requires Explicit dyn
ARES-39  Generic Parameters Have Stable Identity
ARES-40  Self Has Explicit Semantic Identity
ARES-41  self Is A Receiver Parameter
ARES-42  AST Syntax Sugar Does Not Survive Unnecessarily Into HIR
ARES-43  HIR Contains Resolved Symbol References
ARES-44  HIR Does Not Perform Final Type Checking
ARES-45  HIR Does Not Perform Ownership Verification
ARES-46  HIR Does Not Perform MIR-Level CFG Lowering
ARES-47  Resolver Is Deterministic
ARES-48  Symbol Assignment Does Not Depend On Hash Iteration Order
ARES-49  Recursive Type Names May Resolve Before Layout Checking
ARES-50  Resolution Diagnostics Are Stable And Machine-Readable
```

---

# 51. Kiến trúc compiler sau COMPILER-002

Đến đây kiến trúc đã khá rõ:

```text
                 SOURCE
                   │
                   ▼
              ┌─────────┐
              │  Lexer  │
              └────┬────┘
                   │
                   ▼
              ┌─────────┐
              │ Parser  │
              └────┬────┘
                   │
                  AST
                   │
                   ▼
        ┌────────────────────┐
        │ Module Loader      │
        │ Declaration        │
        │ Collector          │
        └─────────┬──────────┘
                  │
                  ▼
        ┌────────────────────┐
        │ Name Resolver      │
        │ Scope / Symbol     │
        │ Import / Method    │
        └─────────┬──────────┘
                  │
                  ▼
                 HIR
                  │
                  ▼
        ┌────────────────────┐
        │ Type System        │
        │ Trait Solver       │
        └─────────┬──────────┘
                  │
             Typed HIR
                  │
                  ▼
        Ownership / Capability
                  │
                  ▼
                 MIR
```

---

# 52. Một quyết định kiến trúc rất quan trọng

Axiom **không nên có một “universal resolver” khổng lồ**.

Nên tách:

```text
ModuleLoader
SymbolCollector
ImportResolver
NameResolver
MethodCandidateResolver
TraitResolver
TypeResolver
```

nhưng chúng dùng chung:

```text
SemanticDatabase
```

và:

```text
SymbolId
ModuleId
ScopeId
TypeRef
```

Như vậy compiler không biến thành một class/service vài chục nghìn dòng.

---

# 53. Semantic Database

Đề xuất:

```text
SemanticDatabase
├── modules
├── symbols
├── scopes
├── functions
├── structs
├── enums
├── traits
├── impls
├── aliases
├── constants
├── imports
└── source maps
```

Mỗi bảng có ID riêng.

Ví dụ:

```text
FunctionId → FunctionDef
StructId   → StructDef
TraitId    → TraitDef
ImplId     → ImplDef
```

Không dùng object graph con trỏ chằng chịt.

Điều này sẽ cực kỳ có lợi cho:

- incremental compilation;
- parallel compilation;
- IDE;
- serialization `.axm`;
- AI tooling;
- compiler debugging.

---

# 54. Và đây là nền tảng cho COMPILER-003

Bước tiếp theo là **TYPE-002 / COMPILER-003 — Canonical Type System + Type Inference + Trait Solver**.

Ở đó cần chốt những thứ rất quan trọng:

```text
TypeId
TypeInterner
primitive types
struct/enum types
generic types
type parameters
associated types
function types
tuple/array/view/mut_view
dyn Trait
never/unit
numeric inference
integer literal inference
unification
coercion
method receiver typing
trait obligations
associated type equality
generic instantiation
monomorphization boundary
```

Đặc biệt sẽ phải quyết định một vấn đề lớn của Axiom:

> **Axiom có type inference mạnh đến mức nào nhưng vẫn giữ được tính deterministic và diagnostics tốt?**

Tôi đề xuất tiếp tục theo hướng **inference mạnh cho local expressions nhưng không inference “mơ hồ” ở API/public boundary**. Điều này sẽ cho Axiom code ngắn như ngôn ngữ high-level nhưng ABI/API vẫn cực kỳ rõ ràng.