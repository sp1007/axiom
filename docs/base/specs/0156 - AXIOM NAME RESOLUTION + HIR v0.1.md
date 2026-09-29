# AXIOM NAME RESOLUTION + HIR v0.1

Đây là lúc compiler bắt đầu chuyển từ **“hiểu cú pháp”** sang **“hiểu chương trình”**.

Mục tiêu của resolver:

```text id="5l9j7x"
AST
 ↓
Name Resolution
 ↓
Resolved HIR
```

Sau bước này, mọi reference quan trọng trong chương trình phải có **semantic identity rõ ràng**. Type checker tuyệt đối không nên phải đi tìm symbol từ string name một lần nữa.

---

# 1. Nguyên tắc cốt lõi

Resolver trả lời duy nhất:

> **Tên này đề cập tới entity nào?**

Không trả lời:

- type này có hợp lệ không
- function call có đúng argument không
- trait có được implement không
- ownership có hợp lệ không
- capability có conflict không

Những việc đó thuộc phase sau.

Ví dụ:

```axiom id="4z5c7j"
foo(x)
```

Resolver biến thành:

```text id="i6t4y0"
Call
├── callee → FunctionId(42)
└── argument → LocalId(7)
```

Nhưng chưa biết:

```text id="d5m0qv"
foo : fn(i32) -> i32
x   : i32
```

Type checker mới xác định.

---

# 2. Resolution pipeline

Đề xuất:

```text id="y0rjue"
AST
 │
 ├── Collect module declarations
 │
 ├── Collect imports
 │
 ├── Build scopes
 │
 ├── Bind declarations
 │
 ├── Resolve imports
 │
 ├── Resolve names
 │
 └── Produce HIR
          │
          ▼
     Typed HIR
```

Điểm quan trọng:

**Không resolve từng function ngay khi parser vừa tạo nó.**

Trước tiên phải collect declarations để hỗ trợ forward reference.

---

# 3. Forward reference

Axiom cho phép:

```axiom id="qkqk8n"
fn main() {
    foo()
}

fn foo() {}
```

Resolver phải tìm được `foo`.

Không được phụ thuộc thứ tự source declaration.

---

# 4. Function declarations cùng module

Ví dụ:

```axiom id="i9um3u"
fn a() {}
fn b() {}
fn c() {}
```

module scope:

```text id="5w7x9k"
a → FunctionId(1)
b → FunctionId(2)
c → FunctionId(3)
```

---

# 5. Symbol table

Không dùng:

```text id="7b8wqf"
Map<String, Symbol>
```

đơn giản như compiler toy.

Nên:

```text id="0qqg6d"
Scope
 └── NameMap<StringId, BindingSet>
```

và:

```text id="h1g8d5"
Binding {
    name: StringId
    symbol: SymbolId
    namespace: Namespace
    visibility
    declaration_span
}
```

---

# 6. Namespace

Axiom cần phân biệt namespace.

Tôi đề xuất tối thiểu:

```text id="n0f4u8"
ValueNamespace
TypeNamespace
ModuleNamespace
TraitNamespace
```

Nhưng không nên để programmer phải suy nghĩ quá nhiều về chúng.

Ví dụ:

```axiom id="s6f7a3"
struct User {}

fn User() {}
```

Có thể tồn tại nếu hai entity thuộc namespace khác nhau, nhưng **không nên khuyến khích**.

Một lựa chọn đơn giản hơn là:

> Axiom dùng **unified lexical namespace** cho tên declarations trong cùng scope, ngoại trừ các namespace được compiler bắt buộc để phân biệt type/value.

Tôi khuyến nghị thống nhất hơn nữa:

### User-facing rule

Tên declaration trong cùng scope:

```text
User
```

chỉ nên có một binding.

Không cho:

```text id="2xj7u4"
struct User {}
fn User() {}
```

Điều này giảm ambiguity rất nhiều.

Compiler nội bộ vẫn có thể có semantic categories riêng.

---

# 7. Local scope

Ví dụ:

```axiom id="o5f40u"
fn foo(x: i32) {
    let y = 10

    {
        let z = 20
        use(x)
        use(y)
        use(z)
    }

    use(x)
    use(y)
}
```

Scope tree:

```text id="k9d8g3"
FunctionScope
├── x
├── y
└── BlockScope
    └── z
```

`z` không tồn tại sau block.

---

# 8. Scope không phải lifetime

Đây là distinction quan trọng.

```text id="v0k73d"
Scope
```

là **name visibility**.

Trong khi:

```text id="q9a4kz"
Ownership lifetime
Capability lifetime
Storage lifetime
```

là semantic concepts khác.

Resolver không được cố giải quyết lifetime.

---

# 9. Shadowing

Axiom cho phép shadowing cục bộ:

```axiom id="e0i1yu"
let x = 10

{
    let x = 20
    use(x)
}

use(x)
```

Hai `x`:

```text id="v7a6bx"
LocalId(1)
LocalId(2)
```

khác nhau.

---

# 10. Shadowing cùng scope

Tôi khuyến nghị **cấm duplicate binding trong cùng scope**.

Không:

```axiom id="k2jv7w"
let x = 1
let x = 2
```

Compiler:

```text id="f1d2e4"
AX_NAME_0004
duplicate binding
```

Lý do:

- tránh typo
- giảm ambiguity
- AI-generated code dễ kiểm tra hơn
- semantic model đơn giản hơn.

Shadowing chỉ hợp lệ khi tạo scope mới.

---

# 11. Parameter shadowing

Không:

```axiom id="8qkm4k"
fn foo(x: i32) {
    let x = 10
}
```

vì cùng function scope.

Nhưng:

```axiom id="z0s9jr"
fn foo(x: i32) {
    {
        let x = 10
    }
}
```

hợp lệ.

---

# 12. Declaration collection

Resolver chạy pass:

```text id="3i9f6c"
collect_items(module)
```

Ví dụ:

```axiom id="4x4z4n"
struct User {}
enum Message {}
trait Display {}
fn main() {}
```

sẽ tạo:

```text id="c8fjq5"
StructId
EnumId
TraitId
FunctionId
```

trước khi resolve body.

---

# 13. Hai-phase declaration resolution

Tôi đề xuất:

### Phase A — Declaration collection

```text id="i0td1e"
module
 ├── collect structs
 ├── collect enums
 ├── collect traits
 ├── collect functions
 ├── collect constants
 ├── collect statics
 ├── collect aliases
 └── collect impl headers
```

### Phase B — Body resolution

```text id="j4e4m0"
resolve function bodies
resolve const expressions
resolve trait bodies
resolve impl bodies
```

Điều này cho phép forward references.

---

# 14. Module graph

Ví dụ:

```text id="2c8xgl"
app
├── main
├── math
│   └── vector
└── graphics
```

Resolver xây:

```text id="j32e4w"
ModuleGraph
```

Mỗi node:

```text id="6e4q8h"
ModuleId
```

và:

```text id="b6f3x8"
Module {
    package
    path
    parent
    children
    declarations
    imports
}
```

---

# 15. Module path

Source:

```axiom id="4y5hcv"
module math.vector
```

semantic identity:

```text id="w1p3cs"
PackageId + ["math", "vector"]
```

Không phải:

```text id="6h5p5x"
filesystem path only
```

---

# 16. File không phải module identity

Có thể:

```text id="s7h9y4"
math/vector.ax
```

và:

```text id="q7f5ac"
math/vector_generated.ax
```

đều đóng góp vào cùng semantic module nếu build/package system cho phép.

Do đó resolver làm việc với:

```text id="q9j37h"
ModuleId
```

không trực tiếp với filename.

---

# 17. Import resolution

Ví dụ:

```axiom id="ylzv7u"
import math.vector
```

Resolver trước tiên resolve module:

```text id="8ixh8n"
math.vector → ModuleId(12)
```

Sau đó import namespace.

---

# 18. Selective import

```axiom id="2i7kh1"
import math.vector { Vec2, dot }
```

Bindings:

```text id="5m8nqn"
Vec2 → imported symbol
dot  → imported symbol
```

Không copy symbol.

Nó là alias/reference đến semantic identity gốc.

---

# 19. Import alias

```axiom id="0pr6hh"
import graphics.opengl as gl
```

Scope:

```text id="0h5k6m"
gl → ModuleId(...)
```

Sau đó:

```axiom id="0od5w6"
gl.Buffer
```

resolver đi qua module.

---

# 20. Re-export

```axiom id="4m9l8s"
pub import graphics.opengl { Buffer }
```

Không tạo:

```text id="5w7lqj"
Buffer2
```

Mà:

```text id="q1w2qv"
Buffer
    ↓
original SymbolId
```

`pub import` chỉ tạo một **public namespace edge**.

---

# 21. Re-export không đổi type identity

Ví dụ:

```text id="4c6vl7"
graphics.opengl.Buffer
```

được re-export bởi:

```text id="3cl3qk"
graphics.Buffer
```

cả hai đều:

```text id="g5q09c"
StructId(42)
```

Điều này cực kỳ quan trọng cho API compatibility.

---

# 22. Prelude

Axiom có prelude nhỏ.

Ví dụ conceptual:

```text id="sl7r2g"
bool
i32
u32
usize
Option
Result
Copy
Drop
Send
Share
```

Nhưng prelude phải được compiler resolve như một **explicit semantic module**.

Không có magic lookup:

```text id="0cyo7c"
if not found:
    maybe builtin
```

Mọi thứ phải deterministic.

---

# 23. Resolution priority

Khóa:

```text id="f8jsm6"
1. local binding
2. parameter
3. current module
4. explicit import
5. public re-export
6. prelude
```

Tuy nhiên parameter thực chất nằm trong local scope.

Có thể implementation normalize thành:

```text id="m0n8w1"
local scope
current module
imports
prelude
```

---

# 24. Ambiguity

Ví dụ:

```axiom id="v12j1f"
import a { foo }
import b { foo }

foo()
```

→ error:

```text id="c7m5j2"
AX_NAME_0007
ambiguous name
```

Không chọn:

- import cuối
- import đầu
- alphabetically
- gần nhất

Không có heuristic.

---

# 25. Explicit qualification giải ambiguity

```axiom id="7b5r4f"
a.foo()
```

hoặc:

```axiom id="lq3y1m"
a.foo
```

tùy semantic path.

Resolver dùng qualification để xác định entity.

---

# 26. Name lookup không được dựa trên type inference

Ví dụ:

```axiom id="d1w7c4"
foo(x)
```

Nếu có:

```text id="f3m4v8"
foo(i32)
foo(Text)
```

resolver **không được** chọn dựa vào type của `x`.

Đây là lý do Axiom không nên có overload resolution kiểu C++.

Tên `foo` phải xác định được trước.

---

# 27. Overload

Tôi đề xuất Axiom v0.1:

> **Không có function overloading theo signature trong cùng namespace.**

Không:

```axiom id="z7b9c3"
fn print(x: i32)
fn print(x: Text)
```

Thay vào đó:

```text id="e6m1f2"
print_i32
print_text
```

hoặc trait methods/generic.

Điều này làm resolver và AI tooling đơn giản hơn rất nhiều.

---

# 28. Generic functions

```axiom id="6p6o4r"
fn max<T: Ord>(a: T, b: T) -> T
```

Resolver tạo:

```text id="d6r4m8"
FunctionId
GenericParamId(T)
```

Reference:

```axiom id="i8n1b5"
max
```

→ `FunctionId`.

Trait constraints được type/trait system xử lý sau.

---

# 29. Generic type parameters

```axiom id="l9m6g3"
struct Vec<T> {}
```

Trong body:

```axiom id="h0p9z8"
T
```

resolver:

```text id="l2k7m4"
T → GenericParamId
```

không phải tìm module/global symbol.

---

# 30. Associated types

```axiom id="x1v6u8"
trait Iterator {
    type Item
}
```

`Item` là:

```text id="9s5c7p"
AssociatedTypeId
```

không phải ordinary symbol.

---

# 31. `self`

Trong:

```axiom id="r5y3x9"
impl Vec2 {
    fn length(self: view<Self>) -> f32 {
        ...
    }
}
```

`Self` là:

```text id="m9x7d1"
SelfTypeParameter
```

Resolver context của impl biết:

```text id="d0j5r3"
Self = Vec2
```

nhưng HIR có thể giữ explicit `SelfType`.

---

# 32. `Self` vs `self`

Phải phân biệt:

```text id="m2z3ne"
Self
```

= type-level self.

```text id="f3x8qq"
self
```

= value/local parameter.

Đây là hai semantic entities khác nhau.

---

# 33. Local declaration timing

Ví dụ:

```axiom id="5w9x8n"
let x = x
```

Không được resolve RHS `x` thành chính binding mới nếu binding chưa initialized.

Quy tắc:

> Binding chỉ trở thành visible trong initializer nếu language specification explicitly allows recursive binding.

Axiom v0.1 **không cho recursive local binding**.

Do đó:

```text id="6v0b3m"
let x = x
```

→ unresolved `x`.

---

# 34. Function recursion

Function declaration khác local binding.

```axiom id="2r3d7m"
fn fact(n: u64) -> u64 {
    fact(n - 1)
}
```

hợp lệ vì function name được collect trước body resolution.

---

# 35. Mutual recursion

```axiom id="g9l5s2"
fn a() {
    b()
}

fn b() {
    a()
}
```

hợp lệ.

Declaration collection giải quyết được.

---

# 36. Constants/statics

```axiom id="0g4m7x"
const PI = ...
static GLOBAL = ...
```

đều được collect vào module scope.

Resolver không phân biệt value evaluation.

Type checker/comptime xử lý sau.

---

# 37. Type aliases

```axiom id="7j8x5v"
type UserId = u64
```

Resolver:

```text id="k5n7q2"
UserId → TypeAliasId
```

Type checker mới expand/resolve alias.

---

# 38. Newtype

```axiom id="8b5r9q"
struct UserId(u64)
```

là `StructId`, **không phải alias**.

Do đó:

```text id="y3n6j4"
UserId != u64
```

type identity khác.

---

# 39. Method lookup không nằm trong resolver

Ví dụ:

```axiom id="8f2y3d"
v.length()
```

Resolver chỉ resolve:

```text id="z9m3x8"
v
length
```

nhưng chưa quyết định `length` thuộc:

- inherent impl
- trait
- extension

Đó là **method resolution/type checking phase**.

Đây là distinction rất quan trọng.

---

# 40. HIR

HIR = **High-level Intermediate Representation**.

Mục tiêu:

> Xóa syntax ambiguity, giữ semantic structure trước type checking.

Ví dụ AST:

```axiom id="f3n7x0"
v.length()
```

HIR có thể:

```text id="b6m1q8"
MethodCall {
    receiver: LocalId(4)
    name: NameId(length)
}
```

Sau method resolution mới thành:

```text id="k0p4j2"
Call {
    function: FunctionId(...)
    args: [...]
}
```

Tôi khuyên chia:

```text id="7f1c9w"
Resolved HIR
```

và:

```text id="5g3h6q"
Typed HIR
```

---

# 41. Resolved HIR

Resolved HIR phải loại bỏ string-based references.

Không còn:

```text id="h1d7k3"
Name("foo")
```

mà:

```text id="q6z2w5"
SymbolRef(FunctionId(...))
```

Tương tự:

```text id="7u3m1b"
LocalRef(LocalId(...))
TypeRef(TypeSymbolId(...))
ModuleRef(ModuleId(...))
```

---

# 42. HIR local

Ví dụ:

```axiom id="x1r2y3"
fn add(a: i32, b: i32) -> i32 {
    let x = a + b
    x
}
```

HIR:

```text id="z8m4k2"
Function(FunctionId)
├── params
│   ├── LocalId(a)
│   └── LocalId(b)
└── body
    ├── Binding(LocalId(x))
    │   └── Binary
    │       ├── LocalRef(a)
    │       └── LocalRef(b)
    └── LocalRef(x)
```

Không còn name lookup ở downstream.

---

# 43. HIR không giải quyết type

Ví dụ:

```text id="x8z3p7"
a + b
```

HIR vẫn có:

```text id="p3x8n1"
BinaryOp(Add, a, b)
```

Type checker mới xác định:

- integer add
- float add
- overloaded trait operation nếu Axiom cho phép
- invalid operation

---

# 44. Scope data structure

Conceptual:

```text id="6r4q1s"
ScopeId
```

```text id="4p7y3m"
Scope {
    parent: Option<ScopeId>
    bindings: Map<StringId, Binding>
    kind: ScopeKind
}
```

`ScopeKind`:

```text id="y8q2r1"
Module
Function
Block
Trait
Impl
Generic
```

---

# 45. Scope stack

Resolver đi vào block:

```text id="9m3x5v"
push_scope()
```

ra block:

```text id="c8k4z7"
pop_scope()
```

Lookup:

```text id="d1r9p3"
current
 ↓
parent
 ↓
...
 ↓
module
 ↓
imports
 ↓
prelude
```

Nhưng implementation phải cache lookup để không O(depth) cho mọi identifier.

---

# 46. Resolution result

Không trả `Option<SymbolId>` đơn giản.

Nên:

```text id="q5v8m2"
ResolutionResult
├── Resolved(SymbolId)
├── Unresolved
├── Ambiguous([SymbolId])
└── InvalidContext
```

Điều này làm diagnostics chính xác.

---

# 47. Name diagnostics

Đề xuất:

```text id="j2q7p5"
AX_NAME_0001
unresolved name

AX_NAME_0002
unresolved type

AX_NAME_0003
unresolved module

AX_NAME_0004
duplicate binding

AX_NAME_0005
duplicate declaration

AX_NAME_0006
invalid import

AX_NAME_0007
ambiguous name

AX_NAME_0008
private item is not accessible

AX_NAME_0009
invalid re-export

AX_NAME_0010
invalid generic parameter reference
```

---

# 48. Accessibility

Resolver phải kiểm tra:

```text id="g8k2n1"
private
internal
pub
```

nhưng không kiểm tra ABI.

Ví dụ:

```text id="r2v7m4"
module a:
fn secret() {}

module b:
import a { secret }
```

→:

```text id="v7x3q9"
AX_NAME_0008
```

---

# 49. Visibility và re-export

Nếu:

```axiom id="m7c1z8"
pub import a { Foo }
```

thì module hiện tại expose `Foo`.

Nếu:

```axiom id="p9x4d2"
import a { Foo }
```

thì chỉ local scope thấy `Foo`.

Resolver phải phân biệt:

```text id="e8m3q1"
LocalImport
PublicReExport
```

---

# 50. Package boundary

`internal`:

```text id="b3r6y1"
```

được phép trong cùng package.

Không được package khác truy cập.

`pub`:

```text id="k8x2v5"
```

được phép qua package dependency.

Package identity đến từ PackageGraph.

---

# 51. Cyclic module imports

Module graph có thể có cycle semantic declaration:

```text id="w4m1q8"
a → b
b → a
```

Nhưng package graph vẫn phải DAG.

Resolver có thể xử lý module SCC:

```text id="r9c2x7"
Strongly Connected Component
```

để resolve declarations.

Tuy nhiên không được có hidden runtime initialization cycle.

---

# 52. Import cycle không phải runtime cycle

Ví dụ:

```text id="h2q8m3"
a imports b
b imports a
```

không có nghĩa:

```text id="j6v1x9"
a.init()
 → b.init()
 → a.init()
```

Axiom không có hidden module constructors.

Do đó import cycle chỉ là namespace dependency.

---

# 53. HIR normalization rules

Một số syntax được normalize:

```text id="z4y7k2"
method call
field shorthand
for
desugared imports
```

Nhưng một số thứ giữ nguyên:

```text id="q1w5m8"
if
match
async
closure
unsafe
comptime
```

vì downstream semantic analysis vẫn cần chúng.

---

# 54. `for` normalization

AST:

```axiom id="8x3j7p"
for x in items {
    foo(x)
}
```

HIR có thể giữ:

```text id="c4m9y1"
For {
    pattern
    iterable
    body
}
```

chứ chưa biến thành trait calls.

Sau type checking mới biết:

```text id="q6k2n8"
IntoIterator
Iterator
```

và MIR lowering mới tạo control flow.

---

# 55. Import normalization

AST:

```axiom id="g1n4v7"
import math.vector { Vec2 }
```

HIR/module environment:

```text id="s8y3k5"
Binding {
    name = Vec2
    target = StructId(...)
    origin = Import
}
```

Downstream không cần hiểu syntax import nữa.

---

# 56. HIR invariants

Khóa:

```text id="m4n8q2"
AHIR-20
Resolved HIR contains semantic IDs instead of unresolved declaration names.

AHIR-21
HIR does not require string-based name lookup for resolved references.

AHIR-22
HIR preserves source spans required for diagnostics.

AHIR-23
HIR is independent of filesystem layout.

AHIR-24
HIR does not perform final type inference.

AHIR-25
HIR does not perform ownership verification.

AHIR-26
HIR does not perform capability verification.

AHIR-27
HIR normalizes purely syntactic constructs when semantics are preserved.

AHIR-28
HIR preserves constructs required for later semantic lowering.

AHIR-29
HIR references are typed by semantic entity category.

AHIR-30
HIR identity does not depend on memory address.
```

---

# 57. Resolver invariants

```text id="q8x3m1"
ARESOLVE-20
Declaration collection precedes body resolution.

ARESOLVE-21
Forward function references are supported.

ARESOLVE-22
Mutual function recursion is supported.

ARESOLVE-23
Local shadowing is allowed only in nested scopes.

ARESOLVE-24
Duplicate bindings in one scope are errors.

ARESOLVE-25
Name resolution is deterministic.

ARESOLVE-26
Resolution does not depend on inferred types.

ARESOLVE-27
Ambiguous names are errors.

ARESOLVE-28
Imports create semantic bindings, not copied declarations.

ARESOLVE-29
Re-exports preserve original semantic identity.

ARESOLVE-30
Visibility is checked during semantic resolution.

ARESOLVE-31
Package identity participates in module identity.

ARESOLVE-32
Filesystem paths do not define semantic symbol identity.

ARESOLVE-33
Import cycles do not imply runtime initialization.

ARESOLVE-34
Generic parameters shadow outer names according to explicit scope rules.

ARESOLVE-35
Self and Self have distinct semantic categories.

ARESOLVE-36
Unresolved names never silently become dynamic values.
```

---

# 58. Một quyết định quan trọng: không có overload

Tôi muốn nhấn mạnh quyết định này.

Nếu Axiom có:

```axiom id="a2x8m7"
foo(i32)
foo(f32)
foo(Text)
```

thì resolver không thể xác định `foo` chỉ bằng name.

Sau đó compiler phải làm:

```text id="f8y2m6"
name lookup
→ candidate set
→ argument type inference
→ conversion ranking
→ specialization
→ ambiguity
```

Điều này làm:

- compiler
- diagnostics
- AI coding
- trait solver
- incremental compilation

phức tạp lên rất mạnh.

Axiom đã có:

- generic
- trait
- associated function
- extension method
- explicit conversion

nên **không cần overload function theo signature trong Core v0.1**.

---

# 59. Method dispatch vẫn đủ mạnh

Không overload không có nghĩa Axiom thiếu abstraction.

Ví dụ:

```axiom id="7x4q2m"
trait Add<Rhs> {
    type Output
    fn add(self: view<Self>, rhs: view<Rhs>) -> Self.Output
}
```

hoặc generic:

```axiom id="z8m3q1"
fn max<T: Ord>(a: T, b: T) -> T
```

và inherent methods:

```axiom id="c7y2n4"
impl Vec2 {
    fn length(self: view<Self>) -> f32
}
```

Như vậy semantics vẫn mạnh mà name resolution đơn giản.

---

# 60. Resolver → Type System boundary

Sau resolver, compiler có:

```text id="p5x7m2"
Source
 ↓
Lexer
 ↓
Parser
 ↓
AST
 ↓
Resolver
 ↓
HIR
```

Tại đây **không còn identifier resolution mơ hồ**.

Type checker có thể bắt đầu bằng:

```text id="e3q8n1"
infer_type(ExprId)
```

mà không cần:

```text id="x6m2r9"
lookup("foo")
lookup("x")
lookup("Vec")
```

Đây là nền tảng cực kỳ quan trọng cho compiler architecture.

---

# 61. Bước tiếp theo: Type System

Từ đây ta có thể xây Type System theo thứ tự:

```text id="k7m4p2"
Primitive Types
      ↓
TypeId / TypeInterner
      ↓
Type Equality
      ↓
Type Inference
      ↓
Generic Parameters
      ↓
Applied Generic Types
      ↓
Struct / Enum Types
      ↓
Function / Closure Types
      ↓
View / MutView
      ↓
Trait Bounds
      ↓
Associated Types
      ↓
dyn Trait / impl Trait
```

Nhưng **không nên bắt đầu bằng trait solver**.

Trước tiên phải khóa:

> **AXIOM TYPE SYSTEM KERNEL — TypeId, canonical type representation, unification/inference, coercion boundary, generic substitution và type equality.**

Đây là phần rất quan trọng vì nó quyết định liệu Axiom có giữ được mục tiêu **“compiler mạnh nhưng ngôn ngữ đơn giản”** hay cuối cùng biến thành một type system quá phức tạp.