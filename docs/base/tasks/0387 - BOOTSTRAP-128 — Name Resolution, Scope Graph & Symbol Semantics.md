# BOOTSTRAP-128 — Name Resolution, Scope Graph & Symbol Semantics

**Trạng thái: FROZEN / COMPLETED**

Mục tiêu:

> Sau khi parser tạo AST, mọi tên trong chương trình phải được ánh xạ **deterministically** tới một `DeclarationId` hoặc một semantic error. Từ thời điểm này trở đi, compiler không còn dùng chuỗi tên làm identity chính.

Kiến trúc:

```text
AST
 │
 ├── Package / Module graph
 │
 ├── Scope graph
 │
 ├── Declaration collection
 │
 ├── Import resolution
 │
 ├── Name resolution
 │
 └── Symbol identity
          │
          ▼
      Resolved HIR
```

---

# 1. Symbol identity

Điểm rất quan trọng:

```text
"name = foo"
```

không phải identity.

Identity thật:

```text
DeclarationId
```

Ví dụ:

```text
PackageId  = 3
ModuleId   = 17
DeclarationId = 421
```

Sau resolution:

```text
foo → DeclarationId(421)
```

Các phase sau **không cần lookup string lại**.

---

# 2. Declaration

Mỗi declaration có metadata:

```text
Declaration {
    id: DeclarationId,
    kind: DeclarationKind,
    name: IdentifierId,
    module: ModuleId,
    visibility: Visibility,
    source_span: SourceSpan,
    attributes: Attributes,
}
```

`DeclarationKind`:

```text
Function
Struct
Enum
Trait
Const
Comptime
TypeAlias
Module
Field
Variant
GenericParameter
Local
Parameter
AssociatedItem
```

---

# 3. Symbol table không phải một hashmap duy nhất

Không nên thiết kế:

```text
HashMap<String, DeclarationId>
```

làm semantic model.

Thay vào đó:

```text
Scope
 ├── type namespace
 ├── value namespace
 ├── trait namespace
 ├── module namespace
 └── ...
```

với compiler-managed indexes.

---

# 4. Namespace model

Axiom nên có **distinct namespaces nhưng cho phép cùng spelling** khi không gây ambiguity.

Ví dụ:

```ax
struct User {}

fn User() {}
```

Có thể tồn tại trong type/value namespace riêng.

Nhưng trong một context cụ thể, lookup phải deterministic.

---

# 5. Type namespace

Bao gồm:

```text
struct
enum
trait
type alias
```

Ví dụ:

```ax
User
Result
Display
```

---

# 6. Value namespace

Bao gồm:

```text
fn
const
local
parameter
enum variant
```

Ví dụ:

```ax
foo()
MAX
x
Some(...)
```

---

# 7. Module namespace

Module name có namespace riêng để hỗ trợ:

```ax
std::io::File
```

Mỗi path segment có thể được resolve qua module/type/value namespace phù hợp.

---

# 8. Associated namespace

Associated items:

```ax
Type::function
Type::CONST
Type::Variant
```

được resolve sau khi `Type` đã được xác định.

Không đưa tất cả associated methods vào global namespace.

---

# 9. Scope graph

Mỗi lexical scope là node:

```text
Scope {
    id
    parent
    kind
    declarations
    imports
}
```

Ví dụ:

```ax
fn foo(x: i32) {
    let y = 10;

    if x > 0 {
        let z = 20;
    }
}
```

Scope graph:

```text
ModuleScope
    │
    └── FunctionScope
          ├── x
          ├── y
          │
          └── IfScope
                └── z
```

---

# 10. Scope kinds

Core:

```text
PackageScope
ModuleScope
FunctionScope
BlockScope
PatternScope
GenericScope
TraitScope
ImplScope
ClosureScope
ComptimeScope
```

Một số có thể là semantic sub-scope thay vì runtime scope.

---

# 11. Lexical lookup

Ví dụ:

```ax
let x = 1;

{
    let y = x;
}
```

Lookup `x`:

```text
BlockScope
   ↓
ModuleScope
   ↓
DeclarationId(x)
```

---

# 12. Shadowing

Cho phép:

```ax
let x = 1;

{
    let x = 2;
}
```

Trong inner scope:

```text
x → inner DeclarationId
```

Outer `x` vẫn tồn tại.

---

# 13. Shadowing không thay đổi declaration identity

Hai `x`:

```text
x₁ → DeclarationId(10)
x₂ → DeclarationId(20)
```

không phải cùng symbol.

Điều này cực kỳ quan trọng cho:

- IDE;
- debugger;
- AI;
- refactoring;
- ownership analysis.

---

# 14. Shadowing cùng scope

Không cho:

```ax
let x = 1;
let x = 2;
```

trong cùng lexical scope nếu không có cơ chế declaration đặc biệt.

Khuyến nghị:

> **Same-scope duplicate declarations là compile error.**

Tránh ambiguity.

---

# 15. Declaration collection trước body resolution

Đây là quyết định quan trọng.

Ví dụ:

```ax
fn a() {
    b();
}

fn b() {}
```

`b` vẫn resolve được.

Compiler làm:

```text
Pass 1:
collect declarations

Pass 2:
resolve bodies
```

---

# 16. Recursive function

Cho phép:

```ax
fn factorial(n: u64) -> u64 {
    if n == 0 {
        1
    } else {
        n * factorial(n - 1)
    }
}
```

`factorial` đã được đưa vào scope trước khi resolve body.

---

# 17. Mutual recursion

Cho phép:

```ax
fn even(n: i32) -> bool {
    if n == 0 { true }
    else { odd(n - 1) }
}

fn odd(n: i32) -> bool {
    if n == 0 { false }
    else { even(n - 1) }
}
```

Declaration collection làm việc này tự nhiên.

---

# 18. Recursive types

Cho phép declaration-level recursion:

```ax
enum Node {
    Empty,
    Next(Box<Node>),
}
```

Resolution:

```text
Node
 ↓
Box
 ↓
Node
```

Type checker xử lý infinite-size/type-cycle legality sau.

Resolver chỉ xác định symbol identity.

---

# 19. Generic parameter scope

```ax
fn foo<T>(x: T) -> T {
    x
}
```

Scope:

```text
FunctionScope
 ├── GenericScope
 │    └── T
 └── ParameterScope
      └── x
```

`T` chỉ tồn tại trong declaration's generic scope.

---

# 20. Generic shadowing

Không nên cho:

```ax
fn foo<T>() {
    let T = 10;
}
```

nếu type/value namespaces khác nhau thì có thể về mặt kỹ thuật, nhưng gây confusion.

Khuyến nghị:

> Cho phép distinct namespaces về semantic, nhưng tooling cảnh báo khi declaration shadow một generic/type symbol bằng cùng spelling.

Không biến warning thành semantic ambiguity.

---

# 21. Module

Ví dụ:

```ax
package app;

module network;
```

Module có:

```text
ModuleId
```

và scope riêng.

---

# 22. Module path

```ax
std::io::File
```

resolver:

```text
std
 ↓
io
 ↓
File
```

Mỗi segment được resolve theo namespace phù hợp.

---

# 23. Import

```ax
import std::io::File;
```

không copy declaration.

Nó tạo binding:

```text
File → DeclarationId(std.io.File)
```

---

# 24. Import alias

```ax
import std::io::File as IoFile;
```

binding:

```text
IoFile → DeclarationId(File)
```

Declaration identity không thay đổi.

---

# 25. Grouped import

```ax
import std::io::{File, Reader, Writer};
```

tạo ba bindings.

---

# 26. Import wildcard

Core v0.1:

> **Không cần wildcard import.**

Không hỗ trợ:

```ax
import std::io::*;
```

Lý do:

- namespace pollution;
- resolution khó hơn;
- diagnostics khó;
- AI khó hiểu dependency;
- refactoring khó.

Có thể xem xét sau.

---

# 27. Re-export

```ax
pub import std::io::File;
```

hoặc một syntax tương đương.

Ý nghĩa:

```text
external users
      ↓
current module
      ↓
File
```

Declaration identity vẫn là declaration gốc.

---

# 28. `pub`

`pub` là visibility, không phải export symbol.

Ví dụ:

```ax
pub fn foo() {}
```

có thể được dùng từ package/module phù hợp.

Nhưng không nhất thiết tạo native linker symbol.

Native export:

```ax
@export("foo")
```

là vấn đề ABI/linker riêng.

---

# 29. Visibility levels

Đề xuất Core:

```text
private
pub
```

`private` mặc định.

Không cần ngay lập tức có hàng loạt:

```text
pub(crate)
pub(super)
pub(package)
```

Nếu cần package-scoped visibility sau này, có thể mở rộng mà không phá model.

---

# 30. Private declaration

```ax
fn helper() {}
```

chỉ visible trong semantic visibility boundary đã định nghĩa.

Visibility checker chạy sau resolution hoặc tích hợp cùng resolver.

---

# 31. Visibility không ảnh hưởng identity

Private:

```text
DeclarationId(42)
```

public:

```text
DeclarationId(43)
```

đều là declaration bình thường.

Visibility chỉ quyết định **ai được phép reference**.

---

# 32. Import cycle

Module import:

```text
A → B
B → A
```

không nhất thiết là error.

Resolver xây module graph rồi resolve declarations.

Package cycle:

```text
Package A → Package B
Package B → Package A
```

đã frozen là **không hợp lệ** ở build graph.

---

# 33. Module cycles

Cho phép module cycle ở mức semantic nếu declarations có thể resolve.

Ví dụ:

```text
A::foo → B::bar
B::bar → A::foo
```

Declaration collection giúp xử lý.

Compiler phải phát hiện cycle nếu query semantic nào đó thực sự không thể resolve.

---

# 34. Import cycle diagnostics

Không báo:

```text
"something went wrong"
```

Mà structured graph:

```text
A → B → C → A
```

AI có thể nhận trực tiếp cycle path.

---

# 35. Name resolution algorithm

Concept:

```text
resolve_name(name, context):
    1. local lexical scope
    2. enclosing lexical scopes
    3. function/generic scopes
    4. module scope
    5. explicit imports
    6. re-exported names where allowed
    7. package/public resolution where applicable
    8. otherwise unresolved
```

Nhưng lookup thực tế phải phân biệt namespace.

---

# 36. No implicit global search

Axiom không nên tự động tìm:

```text
any function named foo
```

trong toàn package.

Phải có:

```text
local
module
import
qualified path
```

rõ ràng.

Điều này làm code dễ phân tích hơn.

---

# 37. Prelude

Standard prelude có thể tự động import một số declarations:

```ax
Option
Result
Copy
Clone
Iterator
```

nhưng compiler nên biểu diễn prelude như **implicit import edge**.

Không hard-code tên vào mọi semantic phase.

---

# 38. Prelude phải nhỏ

Không tự động đưa:

```text
File
Socket
HTTP
GPU
Thread
Arc
```

vào namespace mặc định.

Giảm namespace pollution và dependency ambiguity.

---

# 39. Associated items

Ví dụ:

```ax
User::new()
Result::Ok
Iterator::Item
```

Resolver đầu tiên resolve:

```text
User
```

sau đó:

```text
associated item "new"
```

---

# 40. Enum variants

```ax
enum Color {
    Red,
    Blue,
}
```

`Red` và `Blue` có identity riêng:

```text
VariantId
```

Không chỉ là strings.

---

# 41. Variant resolution

Qualified:

```ax
Color::Red
```

luôn deterministic.

Unqualified:

```ax
Red
```

chỉ được phép nếu variant đã được đưa vào value namespace theo explicit/import/prelude rules.

Khuyến nghị Core:

> **Không tự động inject toàn bộ enum variants vào lexical scope.**

---

# 42. Trait names

```ax
trait Display {}
```

`Display` thuộc type/trait namespace.

Trait solver sau này dùng:

```text
TraitId
```

không dùng string `"Display"`.

---

# 43. Trait associated items

```ax
trait Iterator {
    type Item;

    fn next(self: mut_view<Self>) -> Option<Self::Item>;
}
```

`Item` có:

```text
AssociatedTypeId
```

`next` có:

```text
FunctionId
```

---

# 44. Impl scope

```ax
impl Display for User {
    ...
}
```

tạo impl scope.

Bên trong:

- `Self`;
- generic parameters;
- associated items;
- trait context.

---

# 45. `Self`

`Self` là compiler-known generic type parameter-like entity.

Không resolve `Self` bằng ordinary global lookup.

Resolver tạo special binding:

```text
Self → SelfTypeParameter
```

trong impl/trait context.

---

# 46. Closure scope

```ax
let y = 10;

let f = |x| x + y;
```

Closure scope:

```text
ClosureScope
 ├── x
 └── captured y
```

`y` không được clone thành declaration mới.

Capture analysis sau đó tạo closure environment field.

---

# 47. Closure capture ≠ name resolution

Resolver xác định:

```text
y → DeclarationId(17)
```

Capture analysis sau đó quyết định:

```text
READ
MUT
MOVE
```

Đây là separation rất quan trọng.

---

# 48. Pattern bindings

```ax
match value {
    Some(x) => x,
    None => 0,
}
```

`x` chỉ tồn tại trong arm body.

Scope:

```text
MatchArmScope
 └── x
```

---

# 49. Pattern binding consistency

```ax
match value {
    Some(x) | Other(x) => x,
}
```

Nếu Axiom hỗ trợ or-pattern:

Các alternatives phải tạo binding tương thích.

Resolver tạo logical binding set rồi semantic checker xác nhận consistency.

---

# 50. `for` binding

```ax
for item in items {
    use(item);
}
```

`item` chỉ tồn tại trong loop body.

Không tồn tại sau:

```ax
use(item); // error
```

---

# 51. Block scope

```ax
{
    let x = 10;
}

x; // unresolved
```

Resolver phải phát hiện ngay.

---

# 52. Declaration order

Local declarations:

```ax
let a = b;
let b = 10;
```

khuyến nghị:

> **Không cho forward reference tới local declaration chưa được khai báo.**

Trong khi function/type declarations ở module level được collect trước.

Điều này làm local semantics dễ hiểu hơn.

---

# 53. Why different treatment?

Module:

```ax
fn a() { b(); }
fn b() {}
```

forward reference hữu ích.

Local:

```ax
let a = b;
let b = 1;
```

dễ tạo confusion và interaction với initialization/ownership.

Vì vậy:

```text
Top-level declarations → collect first
Local bindings → sequential
```

---

# 54. Constants

```ax
const A: i32 = B;
const B: i32 = 10;
```

Có thể cho phép declaration collection trước.

Const evaluation sau đó phát hiện cycle:

```text
A → B → A
```

---

# 55. Const cycle

Không phải resolver error thuần túy.

Resolver đã resolve:

```text
A → B
B → A
```

Const evaluator phát hiện:

```text
ECONST_CYCLE
```

---

# 56. Comptime declarations

Tương tự:

```ax
comptime fn generate() {}
```

Tên được resolve như function declaration.

Khả năng thực thi compile-time là semantic property, không phải namespace identity.

---

# 57. Generated declarations

Comptime có thể generate declaration.

Pipeline:

```text
Comptime
   ↓
Generated AST/HIR
   ↓
Declaration collection
   ↓
Normal name resolution
   ↓
Normal type/ownership verification
```

Generated code không được bypass resolver.

---

# 58. Hygiene

Axiom không có macro language Core v0.1.

Nhưng comptime-generated declarations vẫn cần namespace isolation.

Nguyên tắc:

> Generated identifier phải được tạo trong declaration context được xác định rõ ràng.

Không cho generated code vô tình overwrite declaration của source.

---

# 59. Generated declaration collision

Nếu comptime tạo:

```ax
fn foo() {}
```

và source cùng scope đã có:

```ax
fn foo() {}
```

→ duplicate declaration error.

Không silent overwrite.

---

# 60. Symbol interning

Identifier spelling:

```text
IdentifierId
```

được intern.

Nhưng:

```text
IdentifierId
```

không phải:

```text
DeclarationId
```

Một spelling có thể có hàng nghìn declarations.

---

# 61. Symbol lookup complexity

Mục tiêu:

```text
local lookup ≈ O(1)
module lookup ≈ O(1)
qualified path ≈ O(path length)
```

Không scan toàn source.

---

# 62. Scope representation

Có thể dùng:

```text
ScopeId
parent: ScopeId?
bindings: ScopeMap
```

`ScopeMap` có thể dùng persistent/hash structure để hỗ trợ incremental compiler.

---

# 63. Incremental name resolution

Nếu thay đổi body:

```ax
foo();
```

thành:

```ax
bar();
```

chỉ query resolution của expression đó và các dependent queries cần thiết bị invalidate.

Không resolve lại toàn package nếu declaration graph không đổi.

---

# 64. Declaration fingerprint

Declaration interface fingerprint nên bao gồm:

```text
name
kind
visibility
generic signature
type signature
trait relationships
attributes affecting semantics
ABI/export metadata
```

Body implementation không cần invalidate downstream interface consumers nếu interface không đổi.

---

# 65. Import fingerprint

Module dependency phải distinguish:

```text
import graph
```

và:

```text
semantic declaration dependency
```

Ví dụ module import `foo`, nhưng chỉ dùng `foo::A`.

Thay đổi private `foo::B` không cần invalidate consumer.

---

# 66. Resolution result

Không dùng:

```text
Option<DeclarationId>
```

đơn giản.

Nên có:

```text
ResolveResult =
    Resolved(DeclarationId)
    Unresolved(Name)
    Ambiguous(Candidates)
    Inaccessible(DeclarationId)
    InvalidPath(Path)
    Error(...)
```

---

# 67. Ambiguous name

Ví dụ hai explicit imports cùng tên:

```ax
import a::Foo;
import b::Foo;
```

sau đó:

```ax
Foo::new();
```

→ `EAMBIGUOUS_NAME`.

Compiler không chọn “import gần nhất” một cách tùy tiện.

---

# 68. Explicit disambiguation

User có thể viết:

```ax
a::Foo
b::Foo
```

để resolve deterministic.

---

# 69. Duplicate imports

```ax
import a::Foo;
import a::Foo;
```

không nên tạo hai semantic bindings.

Compiler có thể canonicalize thành một binding hoặc báo redundant import warning.

Không tạo ambiguity.

---

# 70. Import shadowing local

```ax
import foo::bar;

fn x() {
    let bar = 10;
}
```

local `bar` thắng import theo lexical scope.

Tooling nên hiển thị source:

```text
bar → Local DeclarationId
```

---

# 71. Explicit import beats implicit prelude

Nếu prelude có:

```text
Result
```

và module import:

```ax
import my::Result;
```

thì explicit import phải thắng prelude.

Nếu vẫn ambiguity giữa explicit imports → error.

---

# 72. Name resolution và extension methods

Resolver **không tự động search tất cả methods**.

Với:

```ax
x.foo()
```

nó resolve receiver `x` trước.

Method resolution phase sau mới tìm:

```text
inherent
trait
explicitly imported extension
generic extension
```

theo rules frozen.

---

# 73. Why separate method resolution?

Nếu resolver search toàn bộ traits ngay từ đầu:

```text
x.foo()
```

sẽ kéo type inference + trait solver vào name resolution.

Axiom tránh coupling này.

---

# 74. Field resolution

Tương tự:

```ax
x.name
```

Resolver biết `x`.

Type checker/layout resolver sau đó xác định:

```text
field name
```

Không dùng global symbol lookup cho fields.

---

# 75. Symbol graph

Compiler nên duy trì:

```text
SymbolGraph {
    declarations
    references
    imports
    exports
    calls
    type_refs
    trait_refs
}
```

Không nhất thiết build toàn bộ ngay; có thể query/incremental.

---

# 76. IDE capability

Với `DeclarationId`, IDE có thể:

```text
go_to_definition
find_references
rename
hover
call_hierarchy
type_hierarchy
```

mà không dựa vào text search.

---

# 77. AI capability

Compiler API:

```text
axc inspect symbol foo
axc inspect declaration 421
axc inspect references 421
axc inspect scope <position>
axc inspect resolve <position>
```

Có thể trả:

```json
{
  "name": "foo",
  "declaration_id": 421,
  "kind": "Function",
  "module": 17,
  "visibility": "private"
}
```

Điều này rất phù hợp với workflow AI agent của Axiom.

---

# 78. Error: unresolved name

Ví dụ:

```ax
foo();
```

nếu không có declaration:

```text
EUNRESOLVED_NAME
```

Structured payload:

```json
{
  "name": "foo",
  "scope": 81,
  "searched": [
    "local",
    "function",
    "module",
    "imports"
  ]
}
```

---

# 79. Error: inaccessible

Nếu declaration tồn tại nhưng private:

```text
EINACCESSIBLE_NAME
```

Không báo “not found”, vì symbol thực sự tồn tại.

Điều này giúp diagnostics và AI chính xác hơn.

---

# 80. Resolver architecture

Đề xuất:

```text
ModuleCollector
       ↓
DeclarationCollector
       ↓
ImportCollector
       ↓
ScopeBuilder
       ↓
NameResolver
       ↓
VisibilityChecker
       ↓
ResolvedAST / HIR
```

Các bước có thể được query/incremental hóa trong `CompilerDB`.

---

# 81. Resolver không giải quyết type

Ví dụ:

```ax
foo(x)
```

resolver:

```text
foo → FunctionId(42)
x   → LocalId(91)
```

Nhưng:

```text
Which overload?
What generic T?
Does x satisfy constraint?
```

để TypeDB/TraitDB xử lý.

---

# 82. Overloading

Axiom có compile-time overload resolution.

Resolver có thể trả:

```text
foo → OverloadSetId(42)
```

thay vì ép chọn một function quá sớm.

Sau type inference:

```text
OverloadSet
      ↓
Candidate filtering
      ↓
Trait/type constraints
      ↓
Selected FunctionId
```

---

# 83. Generic function

```ax
fn max<T: Ord>(a: T, b: T) -> T
```

Resolver xác định declaration:

```text
FunctionId(max)
```

Type checker tạo:

```text
GenericInstanceId(max<T=i32>)
```

---

# 84. Symbol identity across incremental revisions

`DeclarationId` không nên dựa vào memory address.

Nên dùng:

```text
generational/stable IDs
```

và semantic key khi cần tái nhận diện declaration giữa revisions.

Ví dụ:

```text
ModuleId + syntax node identity + declaration kind + stable anchor
```

---

# 85. Deletion/recreation

Nếu:

```ax
fn foo() {}
```

bị xóa rồi tạo lại `foo`, compiler không nên giả định declaration cũ vẫn là declaration mới.

Reference cache phải invalidate đúng.

---

# 86. Rename

Rename:

```text
foo → bar
```

thay đổi spelling nhưng declaration identity có thể được duy trì trong IDE transaction nếu source transformation xác định đó là cùng declaration.

Build semantic identity mới vẫn phải được fingerprint đúng.

---

# 87. Resolver + package graph

Resolver không tự download dependency.

Package/build system đã resolve:

```text
PackageId
Version
SourceIdentity
```

Resolver chỉ sử dụng package graph đã được BuildDB xác định.

---

# 88. No hidden dependency discovery

Compiler không tự:

```text
scan filesystem
search random package
```

để resolve unknown import.

Dependency phải nằm trong build graph.

Điều này rất quan trọng cho:

- reproducibility;
- security;
- offline build;
- AI agents;
- cache.

---

# 89. Standard prelude implementation

Prelude được biểu diễn:

```text
ImplicitImportSet
```

trong ModuleDB.

Do đó:

```text
std::core::Option
```

vẫn là declaration bình thường.

Không có magic duplicate type.

---

# 90. Resolution output

Sau phase này:

```text
foo
```

không còn chỉ là:

```text
Identifier("foo")
```

mà:

```text
ResolvedName {
    declaration: DeclarationId(421),
    namespace: Value,
    source_span: ...
}
```

Đây là một trong những mốc quan trọng nhất của frontend.

---

# 91. HIR boundary

AST:

```text
Call(
    Path("foo"),
    ...
)
```

↓

Resolved HIR:

```text
Call(
    FunctionId(421),
    ...
)
```

Từ HIR trở đi, string lookup gần như biến mất khỏi semantic pipeline.

---

# 92. Resolver performance

Mục tiêu:

```text
O(number of declarations + references)
```

trong trường hợp thông thường.

Qualified path:

```text
O(number of path segments)
```

Trait/method lookup không được kéo vào resolver.

---

# 93. Resolver parallelism

Có thể parallelize:

```text
module A resolution
module B resolution
module C resolution
```

sau khi declaration/import graph đủ ổn định.

Canonicalize results để output deterministic.

---

# 94. Resolver invariants

### `ARESOLVE-20`
Every successfully resolved name maps to a stable semantic identity.

### `ARESOLVE-21`
Declaration identity is distinct from identifier spelling.

### `ARESOLVE-22`
Identifier interning does not imply declaration identity.

### `ARESOLVE-23`
Name lookup is namespace-aware.

### `ARESOLVE-24`
Type and value namespaces are semantically distinct.

### `ARESOLVE-25`
Module namespace is explicitly represented.

### `ARESOLVE-26`
Local lexical lookup precedes enclosing scopes.

### `ARESOLVE-27`
Same-scope duplicate declarations are rejected unless explicitly permitted by a language rule.

### `ARESOLVE-28`
Lexical shadowing is deterministic.

### `ARESOLVE-29`
Top-level declarations are collected before body resolution.

### `ARESOLVE-30`
Forward references to top-level declarations are deterministic.

### `ARESOLVE-31`
Local bindings are sequentially introduced.

### `ARESOLVE-32`
Generic parameters have explicit scopes.

### `ARESOLVE-33`
Pattern bindings have lexical scopes.

### `ARESOLVE-34`
Closure captures do not create duplicate declaration identities.

### `ARESOLVE-35`
Import aliases preserve original declaration identity.

### `ARESOLVE-36`
Explicit imports cannot silently create ambiguous bindings.

### `ARESOLVE-37`
Import resolution does not search undeclared dependencies.

### `ARESOLVE-38`
Module cycles do not inherently imply declaration-resolution failure.

### `ARESOLVE-39`
Package dependency cycles are rejected by the build graph.

### `ARESOLVE-40`
Visibility is separate from declaration identity.

### `ARESOLVE-41`
Private and inaccessible declarations are distinguishable from unresolved names.

### `ARESOLVE-42`
Associated-item resolution occurs after its owning type/trait context is known.

### `ARESOLVE-43`
Method resolution is distinct from ordinary lexical name resolution.

### `ARESOLVE-44`
Field resolution is distinct from global symbol lookup.

### `ARESOLVE-45`
Overload sets may remain unresolved until type information is available.

### `ARESOLVE-46`
Generic instances are distinct from generic declarations.

### `ARESOLVE-47`
Resolver does not perform trait solving.

### `ARESOLVE-48`
Resolver does not perform ownership analysis.

### `ARESOLVE-49`
Resolver does not execute comptime code.

### `ARESOLVE-50`
Generated declarations re-enter ordinary declaration and resolution phases.

### `ARESOLVE-51`
Generated declarations cannot silently overwrite existing declarations.

### `ARESOLVE-52`
Resolution results are deterministic across compiler optimization levels.

### `ARESOLVE-53`
Resolution results are deterministic across parallel execution.

### `ARESOLVE-54`
Incremental resolution is semantically equivalent to clean resolution.

### `ARESOLVE-55`
Resolution caches never depend on process memory addresses.

### `ARESOLVE-56`
All semantic references downstream of HIR use stable IDs rather than source strings where possible.

### `ARESOLVE-57`
Resolver diagnostics are machine-readable.

### `ARESOLVE-58`
Ambiguous names are rejected rather than resolved arbitrarily.

### `ARESOLVE-59`
Resolution does not depend on target machine code generation.

### `ARESOLVE-60`
AI/IDE tooling can query declaration identity and resolution directly.

---

# 95. Frontend sau BOOTSTRAP-128

Axiom hiện có:

```text
                  Source
                    │
                 Lexer
                    │
              Green CST
                    │
                   AST
                    │
          ┌─────────▼─────────┐
          │  Name Resolution  │
          │                   │
          │ Scope Graph       │
          │ Module Graph      │
          │ Imports           │
          │ Visibility        │
          │ Declaration IDs   │
          └─────────┬─────────┘
                    │
              Resolved HIR
                    │
          ┌─────────┴─────────┐
          │                   │
        TypeDB              TraitDB
          │                   │
        ConstDB            GenericDB
          │                   │
          └─────────┬─────────┘
                    │
                 Comptime
                    │
                   HIR
                    │
                   MIR
```

Điểm đáng chú ý: **Axiom đã tách được ba loại “resolve” khác nhau**:

```text
1. Name Resolution
   "foo là declaration nào?"

2. Type Resolution
   "expression này có type gì?"

3. Method/Overload Resolution
   "trong các candidate này, function nào được chọn?"
```

Đây là kiến trúc tốt hơn nhiều so với việc nhét tất cả vào một resolver khổng lồ.

---

# BOOTSTRAP-129 — Type System, Type Inference & Type Identity

Task tiếp theo sẽ khóa **trung tâm semantic của Axiom**:

```text
Resolved HIR
     │
     ▼
   TypeDB
     │
     ├── Primitive types
     ├── Struct / Enum
     ├── Tuple / Array
     ├── Function / Closure
     ├── view / mut_view
     ├── Raw pointers
     ├── Generic types
     ├── Associated types
     ├── Type aliases
     ├── Newtypes
     ├── dyn Trait
     └── Never / Unit
```

Đặc biệt sẽ phải chốt rất kỹ:

- nominal vs structural typing;
- type identity;
- type aliases vs newtypes;
- inference;
- unification;
- numeric inference;
- generic inference;
- associated types;
- `Self`;
- `Option`/`Result`;
- function/closure types;
- `view<T>` / `mut_view<T>`;
- `dyn Trait`;
- unsized types;
- `Copy/Clone/Drop/Send/Share`;
- recursive types;
- type normalization;
- coercion/conversion;
- và quan trọng nhất: **làm sao có type system mạnh nhưng syntax vẫn đơn giản cho programmer và AI.**