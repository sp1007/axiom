# BOOTSTRAP-276 — AXIOM NAME RESOLUTION, MODULE GRAPH & SYMBOL SYSTEM
**STATUS: FROZEN / COMPLETED**

## 1. Mục tiêu

Name resolution là cầu nối:

```text
Lossless Syntax
      ↓
AST
      ↓
Name Resolution
      ↓
Resolved HIR
      ↓
Type / Trait / Ownership
```

Mục tiêu của Axiom:

- Mỗi tên hợp lệ phải được resolve **deterministically**.
- Không phụ thuộc thứ tự file, thứ tự import hay worker.
- Không dùng heuristic để giải quyết ambiguity.
- Module graph và symbol graph phải là dữ liệu trung tâm của `CompilerDB`.
- Resolution phải incremental.
- `pub`/visibility được kiểm tra tại resolution boundary.
- Không để type checker tự xây một symbol system khác.
- Không để method resolution, trait resolution và ordinary name resolution trộn thành một cơ chế không thể debug.
- AI/IDE có thể truy vấn symbol graph trực tiếp.
- Circular module dependencies được xử lý ở graph level, không tạo recursive compiler state hỗn loạn.

Nguyên tắc:

> **Tên được resolve trước; ý nghĩa của thực thể được type system xác định sau.**

---

# 2. Kiến trúc tổng thể

```text
                    Package Graph
                         │
                         ▼
                    Module Graph
                         │
                         ▼
                  Declaration Graph
                         │
                         ▼
                    Symbol Graph
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          Value Name   Type Name   Trait Name
              │          │          │
              └──────────┼──────────┘
                         ▼
                  Path Resolution
                         │
                         ▼
                 Resolved HIR
                         │
                         ▼
              Type / Trait / Method
                    Resolution
```

Phải phân biệt:

```text
Module
Declaration
Symbol
Name
Path
Binding
Scope
```

Chúng không phải cùng một object.

---

# 3. Module ≠ Package

Axiom giữ phân biệt:

```text
Package
   ├── Module
   │    ├── Declaration
   │    └── Submodule
   └── Module
```

### Package

Đơn vị dependency/distribution.

Ví dụ:

```text
package graphics
```

### Module

Đơn vị namespace/source organization.

Ví dụ:

```text
module graphics::render
```

Một package có thể có nhiều module.

Một module không tự động là một package.

---

# 4. Module identity

Canonical:

```text
ModuleId
```

không phải:

```text
module name string
```

Module identity:

```text
PackageId + ModulePath
```

Ví dụ:

```text
graphics
graphics::render
graphics::render::vulkan
graphics::math
```

có:

```text
ModuleId(0)
ModuleId(1)
ModuleId(2)
ModuleId(3)
```

ID được cấp bởi `CompilerDB`.

---

# 5. Module record

Khuyến nghị:

```text
Module {
    id: ModuleId
    package: PackageId
    parent: Option<ModuleId>
    name: SymbolId
    path: ModulePath
    source_files: List<SourceFileId>
    declarations: DeclarationSet
    imports: ImportSet
    visibility: Visibility
}
```

`ModulePath` là semantic path, không phải filesystem path.

---

# 6. File ≠ Module

Một module có thể:

```text
1 module → 1 file
```

hoặc:

```text
1 module → nhiều source files
```

depending on package/build model.

Do đó resolver không được lấy:

```text
file name == module name
```

làm semantic assumption.

Filesystem mapping thuộc package/build layer.

---

# 7. Declaration identity

Mỗi top-level declaration có:

```text
DeclarationId
```

Ví dụ:

```text
fn foo()
struct User {}
enum Result {}
trait Iterator {}
const MAX = 10
```

mỗi declaration có ID riêng.

Declaration identity không phụ thuộc source line.

---

# 8. Declaration record

```text
Declaration {
    id: DeclarationId
    module: ModuleId
    name: SymbolId
    kind: DeclarationKind
    visibility: Visibility
    source_span: SourceSpan
}
```

`DeclarationKind`:

```text
Function
Struct
Enum
Trait
TypeAlias
Const
Static
Module
Import
Impl
```

`Impl` đặc biệt vì có thể không có ordinary user-facing name.

---

# 9. Symbol

Symbol là interned identifier identity:

```text
SymbolId
```

Ví dụ:

```text
foo
User
Iterator
length
```

Nếu source chứa:

```text
foo
foo
foo
```

ba occurrences có cùng:

```text
SymbolId
```

nhưng khác `SourceSpan`.

---

# 10. Symbol interning

CompilerDB có:

```text
SymbolInterner
```

API:

```text
intern("foo") -> SymbolId
resolve(SymbolId) -> SymbolData
```

Symbol interning phải deterministic trong semantic result.

Physical numeric ID không được trở thành cross-build ABI identity.

---

# 11. Name space

Axiom không dùng một namespace duy nhất.

Tối thiểu:

```text
ValueNamespace
TypeNamespace
TraitNamespace
ModuleNamespace
```

Ví dụ:

```text
struct User {}
fn User() {}
```

có thể tồn tại trong các namespace khác nhau nếu grammar/semantic rules cho phép.

Tuy nhiên không nên cho phép ambiguity vô nghĩa trong cùng context.

---

# 12. Recommended namespace model

```text
NamespaceKind
├── Value
├── Type
├── Trait
├── Module
└── Macro/Attribute   // reserved for future, not Core v1
```

Không đưa:

```text
Function
Variable
Const
Static
```

thành namespace riêng.

Chúng thuộc `Value`.

---

# 13. Why separate Type and Value namespace?

Cho phép:

```text
struct User {}
fn User() {}
```

nếu Axiom grammar muốn hỗ trợ.

Nhưng:

```text
let x: User
User(...)
```

có context khác nhau.

Resolver biết expected namespace.

Điều này giúp tránh heuristic.

---

# 14. Scope model

Axiom có:

```text
Package scope
Module scope
Item scope
Block scope
Pattern scope
Parameter scope
Generic scope
```

Ví dụ:

```text
module app

struct User {}

fn main(x: User) {
    let y = x
}
```

Scopes:

```text
ModuleScope
    │
    └── FunctionScope
          ├── ParameterScope
          └── BlockScope
```

---

# 15. Scope không phải runtime object

Scope chỉ là compiler semantic concept.

Không có runtime representation.

---

# 16. Scope tree

Mỗi semantic scope có:

```text
ScopeId
```

```text
Scope {
    id
    parent
    kind
    bindings
}
```

`ScopeId` được dùng bởi resolver, diagnostics, IDE.

---

# 17. Shadowing

Axiom cho phép local shadowing:

```text
let x = 10

{
    let x = 20
    print(x)
}

print(x)
```

Resolution:

```text
inner x → inner binding
outer x → outer binding
```

Shadowing không mutate symbol identity.

Hai declarations có:

```text
DeclarationId A
DeclarationId B
```

cùng:

```text
SymbolId x
```

---

# 18. Shadowing rule

Lookup:

```text
current scope
→ parent
→ ...
→ module
```

binding đầu tiên phù hợp namespace wins.

Không tìm kiếm tất cả rồi chọn declaration “có vẻ phù hợp”.

---

# 19. Ambiguity

Nếu cùng scope có hai binding cùng namespace:

```text
fn foo()
fn foo()
```

thì resolver báo:

```text
RES-E001 DuplicateDefinition
```

Không defer ambiguity tới optimizer/type checker.

---

# 20. Overloading

Axiom phải phân biệt:

```text
duplicate declaration
```

và:

```text
overload set
```

Nếu Core v1 cho phép function overloading, module scope có:

```text
foo(i32)
foo(f64)
```

được biểu diễn:

```text
OverloadSet {
    name: foo
    candidates: [FunctionId...]
}
```

Nhưng:

> **Name resolution chỉ tạo overload set; type checking mới chọn overload.**

Đây là boundary cực quan trọng.

---

# 21. Recommended overload policy

Axiom có thể hỗ trợ overload functions, nhưng nên giới hạn:

- cùng namespace;
- cùng module/package hoặc legal import;
- không dựa vào return type để resolve;
- generic constraints được xử lý bởi type/trait solver;
- ambiguity sau type checking là compile error.

Ví dụ:

```text
fn abs(x: i32) -> i32
fn abs(x: f64) -> f64
```

Tên:

```text
abs
```

resolve thành overload set.

Call:

```text
abs(10)
```

sau typing mới chọn `i32`.

---

# 22. Return type không dùng để overload

Không cho:

```text
fn foo() -> i32
fn foo() -> f64
```

cùng signature parameter rồi dựa vào expected return type để chọn.

Lý do:

```text
let x = foo()
```

có thể trở thành circular inference.

---

# 23. Path model

Axiom path:

```text
foo
graphics::render
graphics::render::Renderer
```

Semantic representation:

```text
Path {
    segments: [PathSegment]
}
```

Không dùng raw string split mỗi lần resolve.

---

# 24. Path segment

```text
PathSegment {
    symbol: SymbolId
    source_span: SourceSpan
    generic_args: Option<GenericArgs>
}
```

Ví dụ:

```text
Vec<i32>
```

có:

```text
Vec
generic_args = [i32]
```

Type arguments không được resolver tự type-check.

---

# 25. Absolute path

Có thể hỗ trợ:

```text
::graphics::render::Renderer
```

hoặc canonical syntax tương đương.

Absolute path bắt đầu từ package/root namespace.

---

# 26. Relative path

```text
render::Renderer
```

được lookup từ current module namespace trước.

Ví dụ:

```text
module graphics

module render

fn create() -> render::Renderer
```

`render` được resolve relative to current module.

---

# 27. `self`

Module self-reference:

```text
self::render::Renderer
```

resolve từ current module.

---

# 28. `super`

Parent module:

```text
super::Renderer
```

mỗi `super` đi lên đúng một module parent.

Root không có `super`.

---

# 29. `crate` / package root

Khuyến nghị Axiom dùng:

```text
package::...
```

hoặc:

```text
crate::...
```

nhưng phải chọn **một canonical spelling**.

Không nên có nhiều alias chỉ để thuận tiện.

Đề xuất:

```text
package::...
```

để nhất quán với Axiom package model.

---

# 30. `use`

Ví dụ:

```text
use graphics::render::Renderer
```

Tạo import binding:

```text
local name Renderer
→ target DeclarationId
```

Import không tạo duplicate declaration.

---

# 31. Import alias

```text
use graphics::render::Renderer as GpuRenderer
```

Binding:

```text
GpuRenderer → Renderer declaration
```

Original declaration vẫn có identity riêng.

---

# 32. Import visibility

`use` mặc định private.

```text
pub use graphics::render::Renderer
```

re-export declaration.

Đây là cách tạo public API facade.

---

# 33. Re-export

Module:

```text
module graphics

pub use graphics::render::Renderer
```

Consumer:

```text
use graphics::Renderer
```

Resolver phải biểu diễn:

```text
local symbol
    ↓
ImportBinding
    ↓
ReExport
    ↓
DeclarationId
```

Không copy declaration.

---

# 34. Import cycle

Ví dụ:

```text
A imports B
B imports A
```

Không phải mọi cycle đều lỗi.

Module graph có thể chứa cycle nếu chỉ là symbol reference cycle và declarations có thể được collected trước.

Ví dụ:

```text
A:
use B::Foo

B:
use A::Bar
```

có thể hợp lệ nếu cả hai declarations tồn tại.

Do đó:

> **Module dependency cycle ≠ semantic error tự động.**

---

# 35. Nhưng initialization cycle khác

Runtime/static initialization cycle:

```text
A.static → B.static
B.static → A.static
```

là vấn đề khác.

Nó thuộc global initialization analysis, không phải name resolution.

Resolver chỉ xác nhận symbol identity.

---

# 36. Module graph phases

Module construction nên có các phase:

```text
1. Discover modules
2. Create ModuleIds
3. Collect declarations
4. Build export namespaces
5. Process imports
6. Resolve paths
7. Build resolved symbol graph
8. Validate visibility
```

Không resolve imports trước khi declaration collection hoàn tất.

---

# 37. Two-pass module resolution

### Pass 1 — declaration collection

Thu thập:

```text
struct User
fn main
trait Display
module render
```

### Pass 2 — imports/path resolution

Resolve:

```text
use graphics::Renderer
```

Điều này cho phép declaration order không ảnh hưởng semantic result.

---

# 38. Source order independence

Hai source:

```text
fn a() {
    b()
}

fn b() {}
```

và:

```text
fn b() {}

fn a() {
    b()
}
```

phải resolve giống nhau.

Source order chỉ ảnh hưởng diagnostics ordering theo deterministic source ordering, không ảnh hưởng symbol semantics.

---

# 39. Visibility

Canonical:

```text
private
pub(module)
pub(package)
pub
```

### private

Chỉ current declaration/module visibility domain.

### `pub(module)`

Visible trong current module subtree theo rule đã frozen.

### `pub(package)`

Visible trong package.

### `pub`

Public package API.

---

# 40. Visibility check

Visibility được kiểm tra khi binding cross-boundary được sử dụng:

```text
source module
    ↓
target declaration
    ↓
is_visible(from, target)?
```

Không duplicate declarations chỉ để represent visibility.

---

# 41. Private declaration leak

Ví dụ:

```text
module a

struct Private {}

pub fn create() -> Private
```

Phải có rule riêng cho **public API visibility**.

Name resolution có thể resolve `Private`, nhưng API checker phải phát hiện public signature leak.

Đây không nên là duplicate resolver logic.

---

# 42. Public API boundary

Compiler query:

```text
public_api(ModuleId)
```

traverse:

```text
function signature
→ parameter types
→ return types
→ trait bounds
→ associated types
→ constants
```

Nếu private implementation detail xuất hiện ở public ABI/API theo rule, diagnostic.

---

# 43. Generic scope

Ví dụ:

```text
fn max<T: Ord>(a: T, b: T) -> T
```

scope:

```text
FunctionScope
└── GenericScope
      └── T
```

`T` thuộc type namespace.

---

# 44. Generic parameter collision

```text
fn foo<T, T>(x: T)
```

→ duplicate generic parameter.

```text
fn foo<T>(x: T) {
    let T = 10
}
```

type/value namespace khác nhau nên có thể hợp lệ tùy grammar.

Nhưng compiler diagnostics nên cảnh báo shadowing gây confusion nếu desired.

---

# 45. Pattern bindings

Ví dụ:

```text
match value {
    Some(x) => x
    None => 0
}
```

`x` được tạo trong pattern scope của arm.

Scope:

```text
Match
 ├── arm 1
 │    └── pattern bindings
 └── arm 2
      └── pattern bindings
```

`x` không tồn tại ngoài arm.

---

# 46. `let` binding

```text
let x = expr
```

Binding `x` có scope bắt đầu theo canonical language rule.

Khuyến nghị:

> initializer không nhìn thấy chính binding đang được khai báo.

Ví dụ:

```text
let x = x + 1
```

→ resolve RHS `x` tới outer binding nếu tồn tại; nếu không → unresolved name.

Không implicit self-reference.

---

# 47. Recursive functions

Top-level functions được collect trước nên:

```text
fn foo() {
    bar()
}

fn bar() {
    foo()
}
```

hoàn toàn có thể resolve.

Recursion legality không thuộc name resolver.

---

# 48. Recursive types

```text
struct Node {
    next: Node
}
```

Resolver có thể resolve `Node`.

Type layout phase mới phát hiện infinite-size type nếu không có indirection:

```text
Node
 → Node
 → Node
 → ...
```

Do đó:

> Resolver không được cố giải quyết semantic validity của type.

---

# 49. Associated items

Ví dụ:

```text
trait Iterator {
    type Item
    fn next(self: mut_view<Self>) -> Option<Self::Item>
}
```

`Item` là associated type.

Resolution path:

```text
T::Item
```

không phải ordinary module lookup.

Nó thuộc:

```text
AssociatedItemResolution
```

và phụ thuộc type/trait context.

---

# 50. Type-qualified paths

Ví dụ:

```text
<T as Iterator>::Item
```

nếu syntax này được giữ.

Resolver phải tạo:

```text
QualifiedPath {
    self_type = T
    trait = Iterator
    item = Item
}
```

Trait solver/type checker mới determine concrete associated item.

Không resolve `Item` như module symbol.

---

# 51. Method resolution boundary

Quan trọng:

```text
x.foo()
```

không được resolver biến ngay thành một function declaration.

Pipeline:

```text
parse x.foo()
      ↓
ordinary path/member syntax
      ↓
type checking
      ↓
method candidate discovery
      ↓
inherent method
      ↓
trait method
      ↓
imported extension
      ↓
generic extension
```

Đúng với behavior model đã frozen.

---

# 52. Field vs method

```text
x.foo
```

và:

```text
x.foo()
```

được parser phân biệt syntax.

Resolver không tự biến field thành method hoặc ngược lại.

Type checker quyết định member semantics.

---

# 53. Extension methods

Extension:

```text
fn length(self: String) -> usize
```

là ordinary declaration.

Nếu module được import:

```text
use text::extensions::length
```

thì method lookup có thể xem extension candidate.

Không có hidden global extension registry.

---

# 54. Trait method

```text
trait Printable {
    fn print(self: view<Self>)
}
```

`x.print()` được type/trait resolution xử lý.

Ordinary symbol resolver chỉ resolve:

```text
Printable
```

nếu path explicitly references trait.

---

# 55. `impl`

Ví dụ:

```text
impl Printable for User {
    fn print(self: view<User>) {}
}
```

`impl` tạo:

```text
ImplId
```

và semantic links:

```text
TraitId
SelfType
AssociatedItems
```

`impl` không trở thành module symbol `PrintableForUser`.

---

# 56. Symbol graph

CompilerDB nên có graph:

```text
SymbolGraph {
    declarations
    references
    imports
    reexports
    scopes
    modules
    visibility_edges
}
```

Reference:

```text
NameReference {
    span
    symbol
    namespace
    scope
    resolution
}
```

Resolution:

```text
Resolved(DeclarationId)
Unresolved
Ambiguous(Candidates)
InvalidVisibility
```

---

# 57. Resolution state

Không dùng `Option<DeclarationId>` vì không đủ thông tin.

Canonical:

```text
Resolution {
    Resolved(DeclarationId)
    OverloadSet(OverloadSetId)
    Module(ModuleId)
    Unresolved
    Ambiguous(CandidateSetId)
    Inaccessible(DeclarationId)
    InvalidPath
}
```

---

# 58. Ambiguous candidate set

Candidate set phải giữ:

```text
Candidate {
    declaration
    source
    import_path
    namespace
    visibility
}
```

để diagnostic có thể giải thích:

```text
`foo` refers to two imported declarations:
    graphics::foo
    math::foo
```

AI tooling cũng dùng cùng proof data.

---

# 59. Import conflict

Ví dụ:

```text
use a::foo
use b::foo
```

Nếu cả hai visible trong cùng namespace:

```text
foo()
```

→ ambiguity.

Không chọn:

- import cuối;
- import đầu;
- module gần hơn;
- declaration mới hơn.

---

# 60. Explicit disambiguation

Người dùng có thể viết:

```text
a::foo()
b::foo()
```

để resolve rõ ràng.

Không cần annotation đặc biệt.

---

# 61. Glob imports

Khuyến nghị:

```text
use module::*
```

**không nên là Core v1 feature** nếu không cần.

Nếu hỗ trợ sau này:

- glob không tạo binding ngay;
- tạo lazy candidate source;
- ambiguity deterministic;
- explicit imports ưu tiên hay không phải được spec rõ ràng.

Để giữ Core đơn giản, đề xuất:

> **Không có glob import trong v1.**

---

# 62. Import aliases

Alias là binding mới:

```text
use a::foo as bar
```

`bar` resolve trực tiếp tới same `DeclarationId`.

Không clone declaration metadata.

---

# 63. Unused imports

Resolution tạo fact:

```text
ImportUsageCount
```

Nếu:

```text
use foo::Bar
```

không được dùng:

warning:

```text
RES-W001 UnusedImport
```

Warning không thay đổi semantic result.

---

# 64. Unused declaration

Có thể phân tích sau resolution.

Không nên lexer/parser tự báo.

---

# 65. Module namespace construction

Mỗi module có:

```text
ModuleNamespace {
    values
    types
    traits
    modules
}
```

`ModuleNamespace` map:

```text
SymbolId → Binding
```

Binding:

```text
Single
OverloadSet
Module
Import
ReExport
```

---

# 66. Binding table

Ví dụ:

```text
values:
    foo → OverloadSet

types:
    User → DeclarationId

traits:
    Display → TraitId

modules:
    render → ModuleId
```

Không dùng một hash map:

```text
name → arbitrary declaration
```

vì không đủ semantic information.

---

# 67. Declaration collection

Collector scan AST top-level:

```text
struct User {}
fn foo() {}
trait Display {}
module render
```

và tạo declarations.

Collector chưa resolve:

```text
fn foo(x: User)
```

parameter type `User`.

Nó chỉ tạo declaration signature syntax.

---

# 68. Resolver

Resolver input:

```text
AST
ModuleGraph
DeclarationGraph
ScopeGraph
ImportGraph
```

output:

```text
ResolvedAST / HIR bindings
```

Ví dụ:

```text
foo(x)
```

becomes conceptually:

```text
Call(
    callee = ResolvedFunction(foo#123),
    args = [...]
)
```

---

# 69. Resolved HIR

Không nên để AST mutation trở thành semantic storage.

AST immutable.

HIR chứa semantic links:

```text
NameRef {
    syntax_node
    resolution
}
```

hoặc HIR expression directly references `DeclarationId`.

---

# 70. CompilerDB queries

Cần các query:

```text
module_of(SourceFileId)
module_children(ModuleId)
module_namespace(ModuleId)
declarations(ModuleId)
declaration(DeclarationId)
symbol(SymbolId)
scope(ScopeId)
scope_bindings(ScopeId)
imports(ModuleId)
resolve_path(PathId, ScopeId)
resolve_name(SymbolId, ScopeId, NamespaceKind)
resolve_reference(ReferenceId)
public_api(ModuleId)
references_to(DeclarationId)
```

Các query này phải dùng chung infrastructure từ BOOTSTRAP-274.

---

# 71. Incremental resolution

Nếu sửa:

```text
fn unrelated() {}
```

thì không invalidate toàn package.

Dependency:

```text
Source
 ↓
AST
 ↓
Declarations
 ↓
Namespace
 ↓
Only dependent resolution queries
```

Ví dụ sửa body `foo()` mà signature/name không đổi:

```text
module namespace
```

có thể không invalidate.

---

# 72. Declaration fingerprint

Mỗi declaration có semantic fingerprint:

```text
DeclarationFingerprint
```

phụ thuộc:

- name;
- kind;
- visibility;
- generic parameter structure;
- public signature;
- relevant attributes.

Body implementation fingerprint tách riêng khi có thể.

Điều này giúp incremental compiler không rebuild consumers khi public interface không đổi.

---

# 73. Symbol reference index

CompilerDB nên maintain reverse index:

```text
DeclarationId
    ↓
[ReferenceId...]
```

IDE query:

```text
find references
rename symbol
```

không cần full text grep.

---

# 74. Rename semantics

Rename `foo` phải dùng:

```text
DeclarationId
```

không phải string replacement.

Ví dụ:

```text
foo
foo_local
other::foo
```

chỉ rename đúng references tới target declaration.

Đây là một trong những lý do SymbolGraph phải là first-class infrastructure.

---

# 75. Qualified lookup algorithm

Cho:

```text
A::B::C
```

algorithm:

```text
resolve A
    ↓
must be Module / namespace-producing entity
    ↓
resolve B inside A
    ↓
must produce namespace/type-qualified context
    ↓
resolve C
```

Nếu intermediate `A` là function:

```text
A::B
```

→ invalid path.

Không fallback sang random namespace.

---

# 76. Namespace-producing entities

Path segment có thể produce:

```text
Module
Type
Trait
```

nhưng semantics khác nhau.

Ví dụ:

```text
graphics::render
```

module path.

```text
User::Id
```

associated/type namespace có thể cần type resolution.

```text
<T as Trait>::Item
```

qualified associated lookup.

Resolver phải preserve path category thay vì flatten thành string.

---

# 77. Package boundary

Package dependency graph từ BOOTSTRAP-187 cung cấp:

```text
PackageId A → PackageId B
```

Resolver chỉ được nhìn thấy exported namespace của dependency.

Không scan private declarations của dependency để “tìm cho bằng được”.

---

# 78. External package namespace

Consumer:

```text
use graphics::Renderer
```

Resolver:

```text
current package
    ↓
dependency alias
    ↓
package root module
    ↓
Renderer export
```

Dependency package source có thể:

- source;
- `.axlib`;
- binary + `.axmeta`.

Resolution không được phụ thuộc source availability nếu metadata đủ.

---

# 79. Binary-only packages

Nếu chỉ có:

```text
lib.axlib
lib.axmeta
```

resolver vẫn phải biết:

```text
exported modules
exported declarations
types
traits
ABI
generic metadata nếu cần
```

`.axmeta` là semantic interface.

---

# 80. Namespace export snapshot

Mỗi package có:

```text
PackageExportGraph
```

được fingerprint.

Consumer resolution cache key phụ thuộc export fingerprint.

Implementation body thay đổi nhưng export không đổi:

```text
consumer resolution cache remains valid
```

---

# 81. Visibility + re-export

Nếu:

```text
A::Private
```

private.

B:

```text
pub use A::Private
```

không được phép “nâng” visibility nếu A declaration không cho phép re-export theo rule.

Visibility check phải kiểm tra target's declared visibility.

---

# 82. Symbol resolution and generic declarations

Generic function:

```text
fn identity<T>(x: T) -> T
```

Name resolution chỉ resolve:

```text
identity → FunctionId
T → GenericParamId
```

Không instantiate generic ở resolver.

Instantiation thuộc GenericDB/type system.

---

# 83. Type aliases

```text
type UserId = u64
```

`UserId` resolve thành `TypeAlias DeclarationId`.

Type system sau đó normalize alias.

Resolver không biến `UserId` thành `u64`.

---

# 84. Newtypes

```text
struct UserId(u64)
```

`UserId` resolve thành `Struct DeclarationId`.

Type system giữ nominal identity.

---

# 85. Enum variants

Ví dụ:

```text
enum Option<T> {
    Some(T)
    None
}
```

Variants có:

```text
VariantId
```

Lookup:

```text
Option::Some
```

có thể được resolved thông qua enum namespace.

`Some` không nhất thiết là global symbol.

---

# 86. Variant namespace

Mỗi enum:

```text
EnumNamespace {
    variants: SymbolId → VariantId
}
```

Ví dụ:

```text
match x {
    Option::Some(v) => ...
}
```

resolver:

```text
Option → Enum
Some → Variant
```

Type checking kiểm tra payload/generic instantiation.

---

# 87. Struct fields

Struct field:

```text
struct User {
    name: String
}
```

`name` không phải global symbol.

Member lookup:

```text
user.name
```

được type-directed.

Compiler vẫn có:

```text
FieldId
```

nhưng không đưa field vào module namespace.

---

# 88. Associated functions

```text
impl User {
    fn new() -> User {}
}
```

`new` là associated item.

Không cần:

```text
User_new
```

global symbol.

`User::new()` được xử lý bởi associated-item/method resolution.

---

# 89. `Self`

Trong trait/impl:

```text
Self
```

là special type binding.

Resolver tạo:

```text
SelfTypeBinding
```

Không phải SymbolId lookup trong module.

---

# 90. Name resolution phases

Frozen pipeline:

```text
Source
 ↓
Lex
 ↓
Parse
 ↓
Module discovery
 ↓
Declaration collection
 ↓
Scope construction
 ↓
Import binding
 ↓
Path resolution
 ↓
Reference resolution
 ↓
Visibility checking
 ↓
Resolved HIR
```

Sau đó:

```text
Resolved HIR
 ↓
Type inference
 ↓
Trait solving
 ↓
Ownership/capability
```

---

# 91. Determinism

Resolution result phải độc lập với:

- file traversal order;
- hash map iteration order;
- import declaration order khi semantically equivalent;
- worker count;
- cache state;
- incremental/full compilation;
- target CPU.

Diagnostic ordering có thể canonicalize bằng:

```text
SourceSpan
DiagnosticCode
DeclarationId
```

---

# 92. Hash map determinism

Compiler internal hash maps có thể randomized để chống collision attack.

Nhưng semantic output không được phụ thuộc iteration order.

Mọi iteration observable phải sort/canonicalize.

---

# 93. Cycle handling

Resolver graph sử dụng SCC:

```text
Tarjan / Kosaraju / equivalent
```

để detect module/import cycles nếu một query cần cycle information.

Nhưng ordinary name resolution có thể resolve mutually recursive declarations.

Cycle detection phải tránh:

```text
query A
 → query B
 → query A
 → infinite recursion
```

Query engine BOOTSTRAP-274 phải detect query cycles.

---

# 94. Resolution query cycles vs language cycles

Hai thứ hoàn toàn khác:

```text
Compiler query cycle
```

là infrastructure problem.

```text
Program symbol/type recursion
```

là language semantic property.

Không được dùng một cái để định nghĩa cái kia.

---

# 95. Diagnostics

Core diagnostics:

```text
RES-E001 DuplicateDefinition
RES-E002 UnresolvedName
RES-E003 UnresolvedPath
RES-E004 AmbiguousName
RES-E005 AmbiguousImport
RES-E006 InaccessibleItem
RES-E007 InvalidPathTarget
RES-E008 InvalidModule
RES-E009 ImportCycle
RES-E010 DuplicateImportBinding
RES-E011 InvalidReExport
RES-E012 UnknownPackage
RES-E013 UnknownModule
RES-E014 InvalidGenericParameterReference
```

Không phải mọi diagnostic đều là hard error ở Partial Semantic Mode.

---

# 96. Explain resolution

Compiler phải có query:

```text
explain_resolution(reference)
```

Ví dụ:

```text
foo
```

trả:

```text
Reference:
    foo

Scope:
    FunctionScope #42

Lookup:
    FunctionScope → not found
    ModuleScope → found

Candidate:
    math::foo

Visibility:
    allowed

Result:
    DeclarationId #128
```

Đây là dữ liệu cực kỳ hữu ích cho AI agent.

---

# 97. AI-native symbol API

AXCP nên expose:

```text
query symbol "foo"
find declaration
find references
find imports
find exports
explain resolution
explain ambiguity
show module graph
show dependency path
```

Ví dụ AI hỏi:

```text
Why does `Renderer` resolve to this declaration?
```

Compiler trả proof tree thay vì AI phải đọc hàng nghìn file.

---

# 98. No heuristic resolution

Không bao giờ:

```text
if unresolved:
    search whole package
    pick closest name
```

Không bao giờ:

```text
if two candidates:
    choose one with matching type
```

ở name resolver.

Type-directed overload selection là phase sau.

---

# 99. Error recovery integration

Nếu parser tạo:

```text
ErrorNode
```

resolver có thể tạo:

```text
UnresolvedRecoveryReference
```

nhưng:

> Unknown/Incomplete không bao giờ được coi là proven resolution.

Phù hợp với BOOTSTRAP-191.

---

# 100. Symbol graph and IDE

IDE features trực tiếp dùng graph:

```text
Go to definition
Find references
Rename
Outline
Workspace symbols
Call hierarchy
Type hierarchy
Module hierarchy
Import graph
Dependency graph
```

Không cần reparse/regrep riêng cho từng feature.

---

# 101. CompilerDB additions

Bổ sung:

```text
ModuleDB
DeclarationDB
SymbolDB
ScopeDB
ImportDB
ResolutionDB
ExportDB
ReferenceDB
```

Nhưng chúng đều là logical storage/query domains trong `CompilerDB`, không phải những cache độc lập.

---

# 102. IDs

Cần:

```text
ModuleId
DeclarationId
SymbolId
ScopeId
ReferenceId
ImportId
ReExportId
OverloadSetId
CandidateSetId
VariantId
FieldId
```

Đã có trong baseline:

```text
PackageId
FunctionId
TypeId
TraitId
...
```

Các ID phải được thống nhất với existing ID model.

---

# 103. Resolution data model

Khuyến nghị:

```text
NameReference {
    id: ReferenceId
    syntax_span: SourceSpan
    scope: ScopeId
    symbol: SymbolId
    namespace: NamespaceKind
    resolution: Resolution
}
```

`Resolution`:

```text
Resolved(DeclarationId)
ResolvedModule(ModuleId)
ResolvedVariant(VariantId)
OverloadSet(OverloadSetId)
Ambiguous(CandidateSetId)
Unresolved
Inaccessible(DeclarationId)
Invalid
Incomplete
```

---

# 104. Method resolution deliberately excluded

BOOТSTRAP-276 không quyết định:

- trait candidate ranking;
- generic specialization;
- method receiver coercion;
- autoderef-like semantics;
- overload ranking;
- associated type normalization.

Những vấn đề đó thuộc:

```text
Type / Trait / Method Resolution
```

ở phase sau.

Điều này giữ compiler architecture sạch.

---

# 105. Example — complete resolution

Source:

```text
module app

use graphics::render::Renderer

fn main() {
    let r = Renderer::new()
}
```

Resolver:

```text
Module:
    app

Import:
    Renderer
      ↓
    graphics
      ↓
    render
      ↓
    Renderer DeclarationId #42
```

Local reference:

```text
Renderer
```

→ ImportBinding

→ DeclarationId #42.

Sau đó:

```text
Renderer::new()
```

mới chuyển sang associated-item/method resolution.

---

# 106. Example — ambiguity

```text
use graphics::Renderer
use ui::Renderer

fn main() {
    let x = Renderer()
}
```

Resolver:

```text
Renderer
 ├── graphics::Renderer
 └── ui::Renderer
```

Result:

```text
Ambiguous(CandidateSet)
```

Compiler không chọn một.

---

# 107. Example — shadowing

```text
use math::value

fn main() {
    let value = 10
    print(value)
}
```

Resolution:

```text
value in print(value)
    ↓
BlockScope binding
```

Không phải imported `math::value`.

---

# 108. Example — re-export

```text
module api

pub use internal::User
```

Consumer:

```text
use api::User
```

Graph:

```text
consumer::User
      ↓
Import
      ↓
api::User ReExport
      ↓
internal::User Declaration
```

Một declaration identity duy trì toàn bộ chain.

---

# 109. Example — recursive functions

```text
fn even(n: i32) -> bool {
    if n == 0 {
        true
    } else {
        odd(n - 1)
    }
}

fn odd(n: i32) -> bool {
    if n == 0 {
        false
    } else {
        even(n - 1)
    }
}
```

Declaration collection trước:

```text
even → FunctionId 1
odd  → FunctionId 2
```

Body resolution sau:

```text
odd → FunctionId 2
even → FunctionId 1
```

Không phụ thuộc declaration order.

---

# 110. Example — package boundary

Package A:

```text
pub struct User {}
struct Secret {}
```

Package B:

```text
use A::User     // valid
use A::Secret   // inaccessible
```

Resolver trả:

```text
User   → Resolved
Secret → Inaccessible
```

Không trả `Unresolved`, vì symbol tồn tại nhưng không accessible.

Diagnostic vì thế chính xác hơn.

---

# 111. Example — public API leak

```text
struct Secret {}

pub fn get() -> Secret {
    ...
}
```

Name resolution:

```text
Secret → StructId
```

thành công.

Public API checker sau đó:

```text
pub fn get
    ↓
return Secret
    ↓
Secret visibility insufficient
```

Đây là một ví dụ quan trọng về **resolution != semantic validity**.

---

# 112. Incremental dependency example

Nếu:

```text
graphics::Renderer
```

không thay đổi public declaration nhưng body thay đổi:

```text
fn render() { ... }
```

thì:

```text
Renderer declaration fingerprint unchanged
```

consumer symbol-resolution cache không cần invalidate.

Nếu đổi:

```text
pub struct Renderer
```

thành:

```text
struct Renderer
```

export graph thay đổi → consumers invalidate.

---

# 113. Filesystem separation

Không cho resolver trực tiếp:

```text
open("foo.ax")
```

để tìm module.

Build/package layer phải cung cấp:

```text
ModuleManifest
SourceFileSet
PackageGraph
```

Resolver chỉ dùng CompilerDB.

Điều này giữ:

```text
Filesystem
    ≠
Module semantics
```

và rất quan trọng cho incremental/remote/cache builds.

---

# 114. Security

Resolver không được follow arbitrary filesystem path từ source.

Package graph đã xác định dependency boundary.

Do đó source:

```text
use ../../../../secret
```

không có semantic effect.

---

# 115. Deterministic module discovery

Module discovery input:

```text
PackageManifest
```

phải canonicalize source list.

Không phụ thuộc filesystem enumeration order.

---

# 116. Symbol identity across compiler revisions

`SymbolId` nội bộ có thể thay đổi.

Không dùng `SymbolId` làm persistent ABI identity.

Persistent identity dùng:

```text
DeclarationFingerprint
QualifiedName
PackageIdentity
ABI metadata
```

tùy context.

---

# 117. Persistent metadata

`.axmeta` nên chứa:

```text
PackageIdentity
ModuleExports
DeclarationMetadata
TypeMetadata
TraitMetadata
Visibility
ABI
GenericMetadata
SymbolNames
SemanticFingerprints
```

Không cần lưu toàn bộ local scope của implementation body.

---

# 118. Cache boundary

Resolution cache key có thể gồm:

```text
SourceSemanticFingerprint
ImportedPackageExportFingerprint
LanguageVersion
ResolverVersion
```

Không cần phụ thuộc:

```text
OptimizationLevel
CPU model
Register allocator
```

trừ khi resolution rule thực sự phụ thuộc.

---

# 119. Testing

Phải có:

### Basic

```text
resolve local
resolve module
resolve package
resolve type
resolve function
```

### Namespace

```text
value/type/trait/module
```

### Scope

```text
shadowing
nested scopes
pattern scopes
generic scopes
```

### Imports

```text
alias
re-export
visibility
duplicate
ambiguity
```

### Cycles

```text
recursive functions
mutual modules
query cycles
```

### Incremental

```text
body-only edit
signature edit
rename
import edit
module add/remove
package dependency change
```

### Binary metadata

```text
source package
.axmeta-only package
```

---

# 120. Differential tests

So sánh:

```text
full resolution
```

với:

```text
incremental resolution
```

Kết quả semantic graph phải equivalent.

Không chỉ compare diagnostics text.

Compare:

```text
DeclarationId relationships
resolution targets
visibility result
overload sets
module exports
```

---

# 121. Adversarial tests

Bắt buộc:

```text
10,000 nested scopes
10,000 imports
10,000 re-exports
large overload sets
long qualified paths
deep module graphs
mutually recursive modules
duplicate symbols
Unicode-confusable identifiers
large generated symbol tables
```

Mục tiêu là tránh algorithm vô tình O(n²)/O(n³).

---

# 122. Complexity goals

Expected:

```text
Declaration collection       O(n)
Symbol interning             amortized O(1)
Scope insertion              amortized O(1)
Simple lookup                O(depth)
Qualified path               O(path_length)
Import binding               near O(imports)
Reference resolution         near O(references)
```

Module graph algorithms:

```text
O(V + E)
```

cho graph traversal/SCC.

Không được scan toàn package cho từng name.

---

# 123. Namespace indexing

Module namespace:

```text
HashMap<SymbolId, Binding>
```

với deterministic semantic output.

Overload candidates:

```text
SmallVec<DeclarationId>
```

hoặc equivalent compact structure.

Phần lớn names không overloaded, nên tránh allocation cho singleton binding.

---

# 124. Binding representation optimization

Khuyến nghị tagged representation:

```text
Binding
├── Single(DeclarationId)
├── OverloadSet(OverloadSetId)
├── Module(ModuleId)
├── Import(ImportId)
└── ReExport(ReExportId)
```

Có thể flatten import/re-export sau resolution thành direct declaration link cho fast queries, nhưng provenance phải giữ.

---

# 125. Resolution provenance

Ngay cả khi:

```text
use a::foo as bar
```

được flatten:

```text
bar → DeclarationId #42
```

compiler vẫn giữ:

```text
bar
  imported from a::foo
  via ImportId #7
```

để diagnostics/IDE explain.

---

# 126. Critical architecture principle

Không để các phase sau tự implement:

```text
"find a name"
```

Mọi semantic name lookup phải đi qua resolver/CompilerDB.

Ví dụ type checker cần `User`:

```text
TypeChecker
    ↓
resolve_type_name(...)
    ↓
ResolutionDB
```

Trait solver cần trait:

```text
TraitSolver
    ↓
resolve_trait(...)
```

IDE:

```text
LSP
    ↓
CompilerDB
```

Tất cả cùng một symbol graph.

---

# 127. Frozen invariants

```text id="6a3xjv"
ARESOLVE-20
Every semantic declaration has a stable compiler-local DeclarationId.

ARESOLVE-21
Every identifier occurrence retains its SourceSpan.

ARESOLVE-22
Symbol identity is distinct from declaration identity.

ARESOLVE-23
Symbol interning is deterministic.

ARESOLVE-24
Modules and packages are distinct semantic entities.

ARESOLVE-25
Module identity is independent of filesystem path representation.

ARESOLVE-26
Declaration collection precedes ordinary reference resolution.

ARESOLVE-27
Resolution does not depend on declaration source order.

ARESOLVE-28
Name resolution is namespace-aware.

ARESOLVE-29
Value, type, trait and module namespaces are distinct.

ARESOLVE-30
Scope lookup proceeds through explicit lexical scope parents.

ARESOLVE-31
Shadowing is deterministic.

ARESOLVE-32
Duplicate definitions are diagnosed explicitly.

ARESOLVE-33
Ambiguous names are never resolved heuristically.

ARESOLVE-34
Import bindings preserve target declaration identity.

ARESOLVE-35
Re-exports do not duplicate declarations.

ARESOLVE-36
Visibility is checked at semantic access boundaries.

ARESOLVE-37
Inaccessible symbols are distinguishable from unresolved symbols.

ARESOLVE-38
Overload sets are created by name resolution but selected by typing.

ARESOLVE-39
Return type alone cannot determine ordinary overload selection.

ARESOLVE-40
Generic instantiation is not performed by name resolution.

ARESOLVE-41
Associated-item lookup is distinct from ordinary module lookup.

ARESOLVE-42
Method resolution is distinct from ordinary name resolution.

ARESOLVE-43
Enum variants have enum-scoped identity.

ARESOLVE-44
Struct fields are not global namespace bindings.

ARESOLVE-45
Recursive declarations may be resolved before semantic validity checking.

ARESOLVE-46
Module cycles and compiler query cycles are distinct concepts.

ARESOLVE-47
Resolver never performs filesystem discovery directly.

ARESOLVE-48
Package dependency boundaries are enforced during resolution.

ARESOLVE-49
Binary-only packages can participate in resolution through .axmeta.

ARESOLVE-50
Resolution results are deterministic across worker counts.

ARESOLVE-51
Resolution results are independent of optimization level.

ARESOLVE-52
Resolution caches are dependency-driven.

ARESOLVE-53
Implementation-only changes do not invalidate consumers when public semantic fingerprints remain unchanged.

ARESOLVE-54
Public API export changes invalidate dependent resolution queries.

ARESOLVE-55
Reference-to-declaration relationships are queryable through CompilerDB.

ARESOLVE-56
Rename/refactoring uses declaration identity rather than textual replacement.

ARESOLVE-57
Resolution provenance remains available after import/re-export flattening.

ARESOLVE-58
Partial semantic resolution never treats unknown as proven.

ARESOLVE-59
AI tooling consumes the same authoritative symbol graph as compiler/IDE.

ARESOLVE-60
AI-generated edits must re-enter normal resolution and verification.

ARESOLVE-61
Resolver does not perform type inference.

ARESOLVE-62
Resolver does not perform trait selection.

ARESOLVE-63
Resolver does not perform ownership verification.

ARESOLVE-64
Resolver does not perform ABI selection.

ARESOLVE-65
Resolver does not use semantic heuristics to resolve ambiguity.

ARESOLVE-66
Every qualified path segment is resolved according to its namespace-producing context.

ARESOLVE-67
Source spelling and semantic symbol identity remain separately available.

ARESOLVE-68
Persistent package metadata does not depend on compiler-local SymbolId allocation.

ARESOLVE-69
Full and incremental resolution are semantically equivalent.

ARESOLVE-70
The symbol graph is authoritative for semantic name lookup.
```

---

# 128. Compiler architecture sau BOOTSTRAP-276

Frontend hiện tại:

```text
Source
  ↓
Lexer                         [236/275]
  ↓
Lossless Green Tree
  ↓
Parser                        [237]
  ↓
AST
  ↓
Module Discovery
  ↓
Declaration Collection
  ↓
Scope Construction
  ↓
Import / Export Graph
  ↓
Name Resolution              [276]
  ↓
Resolved HIR
  ↓
Type / Trait Resolution
  ↓
Typed HIR
  ↓
MIR
```

CompilerDB:

```text
CompilerDB
├── SourceDB
├── SyntaxDB
├── ModuleDB
├── DeclarationDB
├── SymbolDB
├── ScopeDB
├── ImportDB
├── ResolutionDB
├── TypeDB
├── TraitDB
├── GenericDB
├── ...
```

Đây là một mốc rất quan trọng: từ đây trở đi, **mọi phase phía sau không được tự xây lại cơ chế lookup tên riêng**.

---

## Task tiếp theo: BOOTSTRAP-277

**AXIOM TYPE REPRESENTATION & TYPE INTERNING ENGINE**

Task này sẽ khóa phần còn thiếu cực kỳ quan trọng trước type inference:

- `TypeId`;
- primitive types;
- struct/enum/trait/function/closure types;
- generic parameters;
- generic applications;
- type aliases vs newtypes;
- tuple/array/slice/view/mut_view;
- raw pointers;
- function types;
- `dyn Trait`;
- associated types;
- `Self`;
- `never`/`unit`;
- type interning;
- canonical type identity;
- type normalization;
- recursive types;
- type well-formedness;
- type fingerprints;
- target-independent vs target-dependent type facts;
- layout facts không được trộn vào semantic `TypeId`;
- type query architecture trong `CompilerDB`.

Đây sẽ là nền móng trực tiếp cho **type inference, overload resolution, trait solving và ownership verifier**.