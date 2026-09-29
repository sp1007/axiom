# BOOTSTRAP-131 — Name Resolution, Imports, Modules & Visibility

**Trạng thái: FROZEN / COMPLETED**

Mục tiêu:

> Sau parser, mọi tên trong Axiom phải được ánh xạ **deterministic** tới đúng một semantic declaration hoặc báo lỗi rõ ràng.

Name resolution là cầu nối:

```text
Syntax
  ↓
Names / Paths
  ↓
Scopes
  ↓
Imports
  ↓
DeclarationId
  ↓
Typed HIR
```

Không có phase sau nào được tiếp tục dùng tên chuỗi để “tự tìm lại” declaration.

---

# 1. Declaration identity

Mọi declaration sau khi được thu thập có identity:

```text
DeclarationId
```

Ví dụ:

```ax
struct User {}
fn create_user() -> User {}
```

sẽ tạo:

```text
Decl(User)        → DeclarationId(42)
Decl(create_user) → DeclarationId(43)
```

Các phase sau dùng ID, không dùng `"User"` hay `"create_user"`.

---

# 2. Namespace model

Axiom sử dụng nhiều namespace semantic thay vì một namespace duy nhất.

Core v0.1:

```text
Type namespace
Value namespace
Trait namespace
Module namespace
Macro/comptime-generated namespace
```

Ví dụ:

```ax
struct User {}

fn User() {}
```

không mặc nhiên được coi là cùng một declaration.

Tuy nhiên syntax/context phải xác định compiler đang tìm:

```text
type User
```

hay:

```text
value User
```

---

# 3. Type/value namespace

Ví dụ:

```ax
struct User {
    id: u64,
}

fn User() -> u64 {
    42
}
```

có thể tồn tại:

```text
User → Type namespace
User → Value namespace
```

nhưng:

```ax
let x: User;
```

lookup type.

Còn:

```ax
let x = User();
```

lookup value.

---

# 4. Module namespace

```ax
module graphics;
```

tạo:

```text
ModuleId
```

Module không phải runtime object.

Nó chỉ là compilation/name-resolution unit.

---

# 5. Package

Package là boundary lớn hơn module:

```text
Package
 ├── module A
 ├── module B
 ├── module C
 └── ...
```

Package identity đã được định nghĩa trong Build System:

```text
Name
Version
SourceIdentity
```

---

# 6. Module path

Ví dụ:

```ax
graphics::Color
```

được resolve theo:

```text
graphics
   ↓
ModuleId
   ↓
Color
   ↓
DeclarationId
```

Không resolve bằng filesystem path trực tiếp sau khi module graph đã được xây dựng.

---

# 7. Filesystem ≠ module identity

Không được giả định:

```text
src/foo.ax
```

luôn semantic-equivalent với:

```text
module foo
```

Build/module configuration quyết định module identity.

Filesystem chỉ là source storage.

---

# 8. Root module

Mỗi package có một root module:

```text
Package
  ↓
RootModule
```

Các module con được nối vào module graph.

---

# 9. Module graph

```text
Package
   │
   ├── root
   │    ├── math
   │    ├── graphics
   │    └── io
   │
   └── tests
```

Module graph có thể có cycle.

Ví dụ:

```text
A → B
B → A
```

**module cycle không mặc định là package cycle.**

---

# 10. Package cycle

Ngược lại:

```text
Package A → Package B
Package B → Package A
```

bị cấm trong dependency graph chuẩn.

Đây là invariant của Build System.

---

# 11. Hai-phase declaration collection

Resolution không resolve body ngay lập tức.

Phase 1:

```text
Collect declarations
```

Phase 2:

```text
Resolve names
```

Ví dụ:

```ax
fn a() {
    b();
}

fn b() {}
```

hoàn toàn hợp lệ.

---

# 12. Forward reference

Không yêu cầu declaration phải xuất hiện trước use.

```ax
fn main() {
    foo();
}

fn foo() {}
```

resolve được.

---

# 13. Scope tree

Compiler xây:

```text
ScopeTree
```

Ví dụ:

```text
ModuleScope
 ├── FunctionScope
 │    ├── BlockScope
 │    └── BlockScope
 └── FunctionScope
```

Mỗi scope có parent:

```text
ScopeId → ParentScopeId
```

---

# 14. Lexical scope

Ví dụ:

```ax
let x = 1;

{
    let y = 2;

    {
        let z = 3;
    }
}
```

lookup:

```text
z → current scope
y → parent scope
x → outer scope
```

---

# 15. Shadowing

Axiom cho phép shadowing có kiểm soát:

```ax
let x = 10;

{
    let x = 20;
    ...
}
```

`x` bên trong trỏ tới declaration mới.

Không thay đổi declaration identity của `x` bên ngoài.

---

# 16. Shadowing không mutation

```ax
let x = 10;

{
    let x = 20;
}
```

là:

```text
x₁
x₂
```

không phải:

```text
x₁ mutated
```

---

# 17. Duplicate declaration

Trong cùng namespace/scope:

```ax
let x = 1;
let x = 2;
```

nếu context không cho phép shadowing cùng scope:

```text
ERROR: duplicate declaration
```

Không chọn declaration theo thứ tự parser.

---

# 18. Local shadowing vs import collision

Hai lỗi khác nhau:

```text
duplicate local declaration
```

và:

```text
ambiguous imported name
```

Diagnostic phải phân biệt.

---

# 19. Import cơ bản

```ax
import std::io::File;
```

sẽ đưa symbol `File` vào import namespace của module hiện tại.

Nó không copy declaration.

Nó tạo binding:

```text
File → DeclarationId
```

---

# 20. Import alias

```ax
import graphics::Color as PixelColor;
```

Sau đó:

```ax
let c: PixelColor;
```

resolve:

```text
PixelColor
    ↓
Color DeclarationId
```

Alias chỉ thay đổi local name.

---

# 21. Module-qualified access

Không cần import:

```ax
std::io::File
```

Path resolver đi từng component:

```text
std
 ↓
io
 ↓
File
```

---

# 22. Qualified path là semantic object

Internal:

```text
Path {
    segments: [...]
    namespace_hint
    source_span
}
```

Sau resolution:

```text
ResolvedPath {
    declaration: DeclarationId
}
```

---

# 23. `self` / `super`

Axiom nên hỗ trợ:

```ax
self::foo
super::foo
```

cho module navigation.

Ý nghĩa:

```text
self
→ current module

super
→ parent module
```

Không phải runtime receiver.

---

# 24. Type associated path

Ví dụ:

```ax
Vec<T>::new()
```

không được xử lý giống module path.

Parser/resolver phân biệt:

```text
ModulePath
TypeAssociatedPath
TraitQualifiedPath
ValuePath
```

---

# 25. Trait-qualified path

Khi ambiguity:

```ax
<T as FromBytes>::from_bytes(data)
```

resolver tạo:

```text
TraitQualifiedPath {
    self_type: T
    trait: FromBytes
    item: from_bytes
}
```

Sau đó TraitDB xử lý implementation.

---

# 26. Resolution và trait solving

Name resolution không tự giải trait.

Pipeline:

```text
Name Resolver
    ↓
TraitId / associated item identity
    ↓
Trait Solver
    ↓
Selected Impl
```

Tách trách nhiệm rõ ràng.

---

# 27. Method names

Với:

```ax
x.foo()
```

name resolver trước tiên xác định:

```text
foo
```

là method lookup candidate.

Trait solver/method resolver sau đó chọn implementation.

Không biến method lookup thành arbitrary global name search.

---

# 28. Extension methods

Extension import:

```ax
import std::math::ClampExt;
```

cho phép:

```ax
x.clamp(...)
```

nhưng extension method chỉ được xem xét nếu declaration/module đó nằm trong visible extension set.

---

# 29. Extension method pollution

Không tự động scan toàn bộ dependency graph để tìm:

```text
foo(x)
```

hay:

```text
x.foo()
```

Điều này vừa làm resolution chậm vừa tạo ambiguity khó đoán.

Extension methods phải có visibility/import provenance.

---

# 30. `pub`

```ax
pub struct User {}
```

cho phép declaration được dùng ngoài module theo visibility rules.

`pub` không có nghĩa:

```text
export native symbol
```

Đúng như ABI model đã frozen:

```text
pub
≠
@export
```

---

# 31. Visibility levels

Core v0.1 nên giữ đơn giản:

```text
private
pub
```

Mặc định:

```text
private
```

Không cần đưa một hệ thống `protected/internal/friend` phức tạp vào Core.

---

# 32. Private visibility

Private declaration chỉ accessible trong semantic visibility domain của module đã định nghĩa.

Compiler kiểm tra ở resolution stage.

---

# 33. Public type signature

Một declaration public không được expose type không accessible.

Ví dụ:

```ax
struct Public {
    private_field: Secret,
}
```

có thể hợp lệ nếu field không public.

Nhưng:

```ax
pub fn make() -> Secret
```

không hợp lệ nếu `Secret` không thể được dùng từ caller.

---

# 34. Visibility leak

Compiler phải kiểm tra public API:

```text
public declaration
    ↓
reachable semantic types
    ↓
traits
    ↓
associated types
    ↓
generic bounds
```

Không để private type “lọt” vào public contract một cách không hợp lệ.

---

# 35. Re-export

Axiom hỗ trợ:

```ax
pub import internal::User;
```

hoặc syntax tương đương để re-export.

Sau đó downstream có thể dùng:

```ax
package::User
```

mà không cần biết module nội bộ.

---

# 36. Re-export không tạo type mới

```text
internal::User
```

và:

```text
package::User
```

là cùng:

```text
DeclarationId
```

Không tạo alias type semantic mới.

---

# 37. Type alias

```ax
type UserId = u64;
```

là alias:

```text
UserId == u64
```

về type identity.

---

# 38. Newtype

```ax
struct UserId(u64);
```

là type mới:

```text
UserId != u64
```

Resolution chỉ xác định declaration; TypeDB quyết định identity.

---

# 39. Prelude

Axiom có thể có một prelude nhỏ:

```text
bool
Option
Result
Some
None
Ok
Err
Copy
Clone
```

nhưng:

> Prelude không được trở thành “global magic namespace” không thể tắt.

---

# 40. Prelude implementation

Compiler có thể coi prelude như một implicit import:

```text
current module
    +
prelude bindings
```

Nhưng compiler metadata vẫn phải ghi rõ binding provenance.

---

# 41. Prelude ambiguity

Nếu local/imported name trùng prelude:

```ax
let Option = ...;
```

local binding thắng theo scope rules.

Không có “compiler magic priority” ngoài resolution rules đã định nghĩa.

---

# 42. Glob import

Có thể hỗ trợ:

```ax
import std::collections::*;
```

nhưng không khuyến khích cho public API.

Glob import tạo một lazy import namespace thay vì copy toàn bộ declaration.

---

# 43. Glob ambiguity

Nếu:

```ax
import a::*;
import b::*;
```

và cả hai export:

```text
Foo
```

thì:

```ax
Foo
```

→ ambiguity.

Compiler không chọn theo import order.

Explicit import/qualification giải quyết ambiguity.

---

# 44. Import cycle

Ví dụ:

```text
A imports B
B imports A
```

không tự động lỗi nếu chỉ là module cycle.

Declaration collection phải hoàn thành trước resolution để cycle có thể resolve.

---

# 45. Initialization cycle

Đây là vấn đề khác:

```text
module A
    runtime init → B

module B
    runtime init → A
```

Không thuộc name resolution.

Nó phải được xử lý bởi initialization/runtime dependency analysis.

---

# 46. Generic names

Ví dụ:

```ax
fn foo<T>(x: T) {}
```

`T` tạo:

```text
GenericParamId
```

và được resolve trước module-level names trong function body.

---

# 47. Generic shadowing

Ví dụ:

```ax
struct T {}

fn foo<T>() {
    let x: T;
}
```

Trong function:

```text
T → GenericParamId
```

không phải struct `T`.

Đây là lexical shadowing.

---

# 48. Field names

Field:

```ax
struct User {
    name: String,
}
```

`name` không phải global declaration.

Nó có:

```text
FieldId
```

và được resolve qua:

```text
User + field name
```

---

# 49. Enum variants

```ax
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

Variants có:

```text
VariantId
```

và có namespace/path semantics riêng.

Có thể dùng:

```ax
Result::Ok(...)
```

---

# 50. Variant imports

Nếu cho phép:

```ax
import Result::Ok;
```

thì `Ok` trở thành local value binding tới:

```text
VariantId
```

Không tạo function wrapper.

---

# 51. Constructor semantics

Struct constructor syntax:

```ax
User {
    id: 10
}
```

không cần một runtime constructor function.

Resolver tạo semantic construction operation.

Nếu có:

```ax
User::new()
```

đó là ordinary associated function.

---

# 52. Constants

```ax
const MAX: usize = 100;
```

tạo value declaration:

```text
DeclarationId
```

và ConstDB sau đó kiểm tra compile-time evaluation.

---

# 53. `comptime` declarations

```ax
comptime fn make_name() -> ...
```

vẫn tạo declaration bình thường.

Comptime execution là phase sau resolution.

Không tạo một “compiler-only namespace” tách biệt về name identity.

---

# 54. Generated declarations

Comptime-generated declarations:

```text
Comptime
 ↓
Generated HIR/declarations
 ↓
Declaration collection
 ↓
Normal resolution
```

Không được bypass name resolver.

---

# 55. Generated declaration collision

Nếu comptime generate:

```text
Foo
```

trùng declaration hiện có:

```text
Foo
```

thì compiler xử lý như duplicate declaration.

Không có rule “generated wins”.

---

# 56. Macro tương lai

Macro system chưa frozen trong Core v0.1.

Nếu sau này thêm macro:

```text
macro expansion
```

phải xảy ra trước semantic name resolution của generated constructs.

Không cho macro expansion sửa trực tiếp resolved `DeclarationId` sau resolution.

---

# 57. Symbol visibility graph

Compiler duy trì:

```text
VisibilityGraph
```

với relation:

```text
Declaration
    ↓
DefiningModule
    ↓
Visibility
    ↓
AccessiblePackages/Modules
```

---

# 58. Package boundary

Private declaration từ dependency package không thể được import trực tiếp.

Ví dụ:

```text
package A
    private Foo

package B
    import A::Foo
```

→ visibility error.

---

# 59. Dependency metadata

Downstream compiler không cần source package đầy đủ nếu có:

```text
.axmeta
```

Metadata phải chứa:

```text
public declarations
types
traits
generic signatures
visibility
exports
ABI/repr information
```

đủ cho resolution/type checking.

---

# 60. `.axmeta` không expose private implementation

Private declarations không được đưa vào public metadata theo cách khiến downstream code có thể depend vào chúng.

Compiler có thể giữ internal metadata riêng cho build cache/compiler workspace.

---

# 61. Name resolution database

`CompilerDB` đã có:

```text
DeclarationDB
ModuleDB
PackageDB
```

BOOTSTRAP-131 bổ sung logic/query:

```text
module_scope(ModuleId)
declarations_in_scope(ScopeId)
resolve_name(ScopeId, Name, Namespace)
resolve_path(ModuleId, Path)
resolve_import(ModuleId, Import)
visibility(DeclarationId)
is_accessible(DeclarationId, AccessContext)
resolve_method(...)
```

---

# 62. Resolver result

Không trả string.

```text
ResolveResult =
    Resolved(ResolvedSymbol)
    Unresolved
    Ambiguous
    Inaccessible
    InvalidPath
```

`ResolvedSymbol` chứa semantic identity:

```text
DeclarationId
FieldId
VariantId
TraitId
ModuleId
GenericParamId
```

---

# 63. Resolution error không phải compiler crash

Ví dụ:

```ax
let x: DoesNotExist;
```

phải tạo:

```text
ERESOLVE_NOT_FOUND
```

và `ErrorSymbol` để compiler có thể tiếp tục phân tích phần còn lại.

---

# 64. Error recovery

Compiler dùng sentinel:

```text
ErrorSymbol
ErrorType
```

nhưng:

```text
ErrorSymbol != valid DeclarationId
```

Không được codegen từ unresolved symbol.

---

# 65. Ambiguity recovery

Nếu:

```ax
Foo
```

có hai candidates:

```text
a::Foo
b::Foo
```

resolver trả:

```text
Ambiguous {
    candidates: [...]
}
```

Diagnostic chỉ rõ cách disambiguate.

---

# 66. Deterministic lookup

Lookup order:

```text
1. Local lexical scope
2. Generic parameters
3. Explicit local imports
4. Module declarations
5. Re-exported names
6. Prelude
```

Nhưng thứ tự namespace/context phải được định nghĩa rõ, không dùng hash iteration.

---

# 67. Explicit import thắng glob

Nếu:

```ax
import a::Foo;
import b::*;
```

và `b::*` cũng có `Foo`, explicit import có thể được ưu tiên.

Đây là một rule hữu ích để giảm ambiguity.

Tuy nhiên:

> **Không bao giờ ưu tiên dựa trên import file order.**

---

# 68. Local declaration thắng import

```ax
import a::Foo;

fn Foo() {}
```

Khi context tìm value `Foo`, local declaration thắng imported `Foo`.

Nếu cùng scope có duplicate semantic declaration thì diagnostic vẫn được tạo theo namespace rules.

---

# 69. No implicit filesystem search

Compiler không làm:

```text
"Không tìm thấy Foo"
→ scan toàn workspace
→ thử mọi package
→ chọn một Foo
```

Điều này gây:

- nondeterminism;
- compile chậm;
- dependency coupling;
- AI khó giải thích.

---

# 70. Explicit dependencies

Muốn dùng external package:

```ax
import package::module::Foo;
```

package phải xuất hiện trong build graph.

Name resolver không tự thêm dependency.

---

# 71. Import does not execute code

Import chỉ là compile-time/module dependency.

Runtime initialization, nếu có, thuộc Runtime/Build model.

---

# 72. Circular imports

Resolver phải dùng trạng thái:

```text
UNVISITED
VISITING
RESOLVED
ERROR
```

để tránh recursion vô hạn.

---

# 73. Incremental resolution

Nếu module A thay đổi local function body nhưng public declarations không đổi:

```text
module A public fingerprint unchanged
```

các module downstream không cần resolve lại toàn bộ.

Nếu public declaration thay đổi:

```text
A public interface fingerprint changed
```

chỉ các dependent queries bị invalidation.

---

# 74. Interface fingerprint

Resolution/build cache dùng:

```text
InterfaceFingerprint
```

gồm semantic public surface:

```text
public names
types
generic parameters
trait bounds
associated items
visibility
exports
ABI-relevant declarations
```

Không hash comment/whitespace.

---

# 75. Implementation fingerprint

Tách:

```text
InterfaceFingerprint
ImplementationFingerprint
```

để:

```text
public API unchanged
```

không buộc downstream recompilation.

---

# 76. Name resolution và IDE

Cùng CompilerDB phục vụ:

```text
Go to definition
Find references
Rename
Completion
Hover
Import suggestions
```

Ví dụ:

```text
type_at(SourceSpan)
definition_at(SourceSpan)
references(DeclarationId)
```

---

# 77. Rename safety

Vì mọi use đã resolve tới:

```text
DeclarationId
```

rename không cần tìm text matching toàn project.

Chỉ sửa semantic references thuộc declaration đó.

Đây là lợi ích lớn của compiler architecture.

---

# 78. AI tooling

Agent có thể query:

```text
resolve("User", current_scope)
definition(DeclarationId)
references(DeclarationId)
visibility(DeclarationId)
imports(ModuleId)
dependents(DeclarationId)
```

thay vì đọc hàng nghìn file.

---

# 79. Structured resolution explanation

Ví dụ:

```json
{
  "query": "User",
  "namespace": "type",
  "scope": "module::api::create",
  "result": "resolved",
  "declaration": "package::model::User",
  "declaration_id": 1827,
  "via": "explicit_import"
}
```

Điều này rất phù hợp với mục tiêu AI-friendly của Axiom.

---

# 80. Invariants

### `ARES-20`
Every semantic name resolves to an explicit compiler identity.

### `ARES-21`
Resolution is deterministic.

### `ARES-22`
Resolution never depends on hash-map iteration order.

### `ARES-23`
Declaration identity is independent of source spelling after canonical resolution.

### `ARES-24`
Declaration identity is independent of memory address.

### `ARES-25`
Module identity is distinct from filesystem path.

### `ARES-26`
Package identity is distinct from module identity.

### `ARES-27`
Package dependency cycles are rejected.

### `ARES-28`
Module cycles may be supported.

### `ARES-29`
Declaration collection precedes body resolution.

### `ARES-30`
Forward references are supported.

### `ARES-31`
Lexical shadowing is deterministic.

### `ARES-32`
Shadowing creates distinct declaration identities.

### `ARES-33`
Duplicate declarations are diagnosed.

### `ARES-34`
Import bindings reference existing declarations.

### `ARES-35`
Import aliases do not create new types.

### `ARES-36`
Re-exports do not create new declarations.

### `ARES-37`
Type aliases preserve type identity.

### `ARES-38`
Newtypes create distinct type identity.

### `ARES-39`
Visibility is checked during semantic resolution.

### `ARES-40`
Private declarations cannot leak into inaccessible public contracts.

### `ARES-41`
`pub` does not imply native symbol export.

### `ARES-42`
Native export requires explicit ABI/export semantics.

### `ARES-43`
Glob imports cannot silently resolve ambiguity.

### `ARES-44`
Explicit imports are deterministic.

### `ARES-45`
Import order cannot alter semantics.

### `ARES-46`
Extension methods are visible only through their defined visibility/import rules.

### `ARES-47`
Method resolution is distinct from ordinary global name lookup.

### `ARES-48`
Trait-qualified paths are resolved semantically.

### `ARES-49`
Trait resolution is delegated to TraitDB/Solver.

### `ARES-50`
Field names resolve through type/field identity.

### `ARES-51`
Enum variants have stable semantic identities.

### `ARES-52`
Comptime-generated declarations re-enter ordinary resolution.

### `ARES-53`
Generated declarations cannot bypass duplicate-name checks.

### `ARES-54`
Unresolved names produce structured diagnostics.

### `ARES-55`
Error symbols cannot enter final code generation.

### `ARES-56`
Resolver cycles terminate.

### `ARES-57`
Incremental resolution is semantically equivalent to clean resolution.

### `ARES-58`
Public-interface changes invalidate affected downstream queries.

### `ARES-59`
Implementation-only changes need not invalidate downstream interface consumers.

### `ARES-60`
`.axmeta` is sufficient for downstream public name resolution.

### `ARES-61`
Private implementation details are not required by downstream semantic resolution.

### `ARES-62`
Name resolution does not implicitly add package dependencies.

### `ARES-63`
Import does not imply runtime execution.

### `ARES-64`
Resolver results use stable compiler IDs.

### `ARES-65`
Resolver diagnostics distinguish not-found, inaccessible, ambiguous, and invalid-path errors.

### `ARES-66`
IDE and CLI resolution use the same CompilerDB semantics.

### `ARES-67`
AI tooling can inspect resolution provenance.

### `ARES-68`
Resolution never performs uncontrolled workspace-wide symbol guessing.

### `ARES-69`
Resolution does not perform type inference or trait solving prematurely.

### `ARES-70`
Name resolution completes before Verified MIR.

---

# Kiến trúc frontend hiện tại

Đến đây frontend của Axiom đã có hình dạng khá rõ:

```text
                    SOURCE
                       │
                       ▼
                    Lexer
                       │
                       ▼
                     CST
                       │
                       ▼
                     AST
                       │
                       ▼
              Declaration Collection
                       │
                       ▼
                Module / Scope Graph
                       │
                       ▼
               Name Resolution
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
          TypeDB                TraitDB
            │                     │
            └──────────┬──────────┘
                       ▼
                 Typed HIR
                       │
                 ┌─────┴─────┐
                 ▼           ▼
             ConstDB       Comptime
                 │           │
                 └─────┬─────┘
                       ▼
                      MIR
```

Điểm quan trọng là **Name Resolution không làm quá nhiều việc**:

```text
Resolver:
    "Tên này là declaration nào?"

Type system:
    "Declaration đó có type gì?"

Trait solver:
    "Implementation nào thỏa contract?"

Verifier:
    "Code này có an toàn/đúng ownership/capability không?"

Optimizer:
    "Có thể biến nó thành code nhanh hơn thế nào?"
```

Đây là separation rất tốt cho mục tiêu compiler mạnh nhưng ngôn ngữ đơn giản.

---

# BOOTSTRAP-132 — Expression Semantics, Evaluation Order & Control Flow

Task tiếp theo nên khóa một phần cực kỳ quan trọng trước khi đi sâu hơn vào MIR:

```text
Expression
    ↓
Place / Value
    ↓
Evaluation order
    ↓
Side effects
    ↓
Control flow
    ↓
Result value
```

Cụ thể sẽ chốt:

- expression vs statement;
- value category;
- Place/Value semantics;
- deterministic evaluation order;
- function-call evaluation;
- argument evaluation;
- assignment;
- compound assignment;
- indexing;
- field access;
- method call;
- temporary lifetime;
- `if` expression;
- `match`;
- `loop`;
- `break value`;
- `return`;
- `?`;
- short-circuit `&&` / `||`;
- panic/trap;
- unreachable/`never`;
- sequencing;
- side effects;
- expression lowering xuống HIR/MIR;
- tránh undefined behavior kiểu C/C++;
- interaction với ownership/capability;
- interaction với async suspension;
- interaction với comptime.

**BOOTSTRAP-132** là bước tiếp theo.