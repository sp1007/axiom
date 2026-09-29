# BOOTSTRAP-238 — AXIOM NAME RESOLUTION, MODULE SYSTEM & SYMBOL GRAPH

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là tầng biến syntax:

```text
foo()
User
Vec<i32>
x.length()
```

thành **semantic identity**:

```text
FunctionId
TypeId
DeclarationId
MethodCandidate
```

Nguyên tắc trung tâm:

> **Parser biết “cái tên trông như thế nào”; Resolver xác định “cái tên đó là cái gì”.**

Resolver tuyệt đối không được đoán khi có ambiguity.

---

# 1. Resolution pipeline

```text
AST
 │
 ├── Module Discovery
 │
 ├── Declaration Collection
 │
 ├── Scope Construction
 │
 ├── Import Resolution
 │
 ├── Name Resolution
 │
 ├── Path Resolution
 │
 ├── Associated Item Discovery
 │
 └── Method Candidate Discovery
        │
        ▼
Semantic Symbol Graph
```

Kết quả cuối:

```text
NameReference
    ↓
DeclarationId
```

hoặc:

```text
Unresolved
Ambiguous
Error
```

---

# 2. Declaration identity

Mọi declaration có identity ổn định trong CompilerDB:

```text
DeclarationId
```

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32
```

sinh:

```text
FunctionId
DeclarationId
```

Không dùng:

```text
memory address
source line
identifier string
```

làm identity.

---

# 3. Symbol graph

Compiler duy trì graph:

```text
Package
   │
   └── Module
        │
        ├── Declaration
        ├── Import
        ├── Export
        └── Submodule
```

và semantic edges:

```text
Reference ──→ Declaration
Import    ──→ Module/Declaration
Impl      ──→ Trait/Type
Method    ──→ Function
```

---

# 4. Module ≠ package

Axiom giữ distinction:

```text
Package
    distribution/dependency unit

Module
    source namespace/organization

Declaration
    semantic program entity
```

Ví dụ:

```text
package math
 ├── module vector
 ├── module matrix
 └── module simd
```

---

# 5. Module identity

```text
ModuleId
```

được xác định bởi package + module path.

Ví dụ:

```text
graphics::render
```

không chỉ là string.

Compiler có:

```text
PackageId
ModulePath
ModuleId
```

---

# 6. Module declaration

Canonical:

```axiom
module graphics::render
```

Compiler tạo:

```text
ModuleId(graphics::render)
```

Module path phải deterministic.

---

# 7. File/module relationship

Một module có thể tương ứng với:

```text
one source file
```

hoặc:

```text
multiple source files
```

nhưng semantic identity vẫn là:

```text
ModuleId
```

Đây là implementation/build-system concern.

---

# 8. Namespace model

Axiom không nên tạo quá nhiều namespace độc lập.

Core cần phân biệt tối thiểu:

```text
Value Namespace
Type Namespace
Trait/Behavior Namespace
Module Namespace
```

Nhưng implementation có thể dùng unified symbol table với namespace tag.

---

# 9. Value namespace

Bao gồm:

```text
functions
constants
local variables
parameters
enum constructors
associated values where applicable
```

Ví dụ:

```axiom
let x = 10
fn foo() {}
```

`x` và `foo` thuộc value namespace.

---

# 10. Type namespace

Bao gồm:

```text
struct
enum
type alias
builtin types
generic type parameters
associated types
```

Ví dụ:

```axiom
struct User {}
type UserId = u64
```

---

# 11. Trait namespace

Trait là declaration có behavior semantics.

```axiom
trait Display {}
```

Resolver cần nhận diện:

```text
Display → TraitId
```

nhưng trait constraints được Trait Solver xử lý sau.

---

# 12. Module namespace

Ví dụ:

```axiom
use graphics::render
```

`render` có thể resolve thành:

```text
ModuleId
```

Sau đó:

```axiom
render::Renderer
```

tiếp tục resolution.

---

# 13. Local scope

Scope tree:

```text
ModuleScope
 └── FunctionScope
      ├── ParameterScope
      └── BlockScope
           ├── BlockScope
           └── BlockScope
```

Mỗi scope có:

```text
ScopeId
ParentScope
Declarations
```

---

# 14. Lexical scoping

Ví dụ:

```axiom
let x = 10

{
    let x = 20
    use(x)
}

use(x)
```

Hai `x` là hai `DeclarationId`.

Inner scope shadow outer scope.

---

# 15. Shadowing

Shadowing được phép trong local scope.

```axiom
let x = 10
let x = x + 1
```

Nếu specification cho phép same-scope shadowing, declaration mới tạo identity mới.

Nếu không, parser/resolver báo duplicate declaration.

**Khuyến nghị:** cho phép shadowing ở local scope, nhưng không cho duplicate declaration trong cùng semantic namespace trừ các construct được overload/coherence rules cho phép.

---

# 16. Shadowing không thay đổi lịch sử reference

```axiom
let x = 10
use(x)

let x = 20
use(x)
```

Resolution:

```text
use #1 → DeclarationId_A
use #2 → DeclarationId_B
```

Không resolve lại reference cũ.

---

# 17. Scope lookup

Canonical:

```text
CurrentScope
    ↓
ParentScope
    ↓
...
ModuleScope
```

Tìm declaration gần nhất.

Nhưng nếu cùng scope có nhiều candidate không hợp lệ:

```text
Ambiguous
```

không chọn ngẫu nhiên.

---

# 18. Import

```axiom
use math::vector::Vec2
```

Import tạo binding:

```text
Vec2
   ↓
DeclarationId(Vec2)
```

Import không copy declaration.

---

# 19. Import alias

```axiom
use math::vector::Vec2 as Point
```

tạo:

```text
Point → Vec2 DeclarationId
```

Alias là binding mới, không phải type mới.

---

# 20. Wildcard import

Khuyến nghị Core v1:

```text
use module::*
```

**được phép nhưng không khuyến khích**, và phải có deterministic conflict rules.

Tốt hơn cho AI/compiler tooling là explicit imports.

---

# 21. Import conflict

Ví dụ:

```axiom
use a::Foo
use b::Foo
```

sau đó:

```axiom
Foo()
```

Nếu cả hai cùng candidate:

```text
AMBIGUOUS
```

Không dựa vào:

- import order
- file order
- hash order
- “candidate mới nhất”

để chọn.

---

# 22. Explicit qualification

Có thể giải quyết:

```axiom
a::Foo()
```

hoặc:

```axiom
b::Foo()
```

Resolver lúc này có một path rõ ràng.

---

# 23. Re-export

```axiom
pub use internal::Renderer
```

có nghĩa:

```text
internal::Renderer
       ↓
public module namespace
```

Không tạo declaration mới.

---

# 24. Re-export identity

Nếu:

```text
A::Foo
```

được re-export thành:

```text
B::Foo
```

thì:

```text
DeclarationId(B::Foo)
==
DeclarationId(A::Foo)
```

về semantic identity.

Chỉ có path/binding khác nhau.

---

# 25. Visibility

Resolver kiểm tra:

```text
private
pub(module)
pub(package)
pub
```

Visibility là property của declaration.

---

# 26. Visibility ≠ reachability

Một declaration có thể:

```text
reachable internally
```

nhưng không:

```text
publicly exported
```

Ngược lại public API phải có dependency visibility hợp lệ.

Ví dụ:

```axiom
struct PrivateType {}

pub fn foo() -> PrivateType
```

phải có rule rõ ràng về public API leakage.

Khuyến nghị: public signature không được expose inaccessible/private nominal types trừ opaque API mechanisms được định nghĩa riêng.

---

# 27. Package boundary

`pub(package)` nghĩa:

```text
same package
```

được access.

Package dependency:

```text
A → B
```

không có nghĩa A được access `pub(package)` của B.

---

# 28. Module boundary

`pub(module)`:

```text
declaration accessible from defining module and permitted descendants according to module visibility rule
```

Cần đóng băng chính xác semantics ancestor/descendant.

Khuyến nghị:

> `pub(module)` = accessible within defining module subtree.

---

# 29. Private declaration

Private mặc định:

```text
module-local
```

Không export qua package boundary.

---

# 30. Declaration collection

Resolver phải có phase đầu tiên:

```text
CollectDeclarations
```

trước khi resolve bodies.

Ví dụ:

```axiom
fn a() {
    b()
}

fn b() {}
```

`a` vẫn resolve được `b`.

Không phụ thuộc declaration order.

---

# 31. Mutual recursion

Cho phép:

```axiom
fn even(n: i32) -> bool {
    if n == 0 { true }
    else { odd(n - 1) }
}

fn odd(n: i32) -> bool {
    if n == 0 { false }
    else { even(n - 1) }
}
```

Declaration collection làm điều này tự nhiên.

---

# 32. Duplicate declarations

Trong cùng namespace/scope:

```axiom
fn foo() {}
fn foo() {}
```

→ error nếu Axiom không định nghĩa overload.

---

# 33. Function overloading

Để giữ compiler deterministic và AI-friendly:

> **Không nên có C++-style arbitrary function overloading trong Core.**

Tên:

```text
foo
```

nên map tới một semantic declaration rõ ràng.

Generic functions + traits xử lý phần lớn nhu cầu.

Nếu nhiều declarations cùng tên được phép trong một context đặc biệt, resolution phải tạo candidate set và overload resolver phải là subsystem riêng.

**Core v1: không dùng implicit overload resolution.**

---

# 34. Generic function resolution

```axiom
max<i32>(a, b)
```

Path resolution trước:

```text
max → FunctionId
```

Sau đó Generic Solver instantiate:

```text
GenericInstanceId
```

Resolver không tự solve type constraints.

---

# 35. Generic inference

```axiom
max(a, b)
```

Resolver chỉ xác định:

```text
max → FunctionId
```

Type inference mới xác định:

```text
T = i32
```

---

# 36. Associated items

Ví dụ:

```axiom
Vec::new()
```

Path:

```text
Vec
 ↓
TypeId
 ↓
associated item
 ↓
FunctionId
```

Đây là two-stage resolution.

---

# 37. Associated constants/types

Ví dụ conceptual:

```axiom
T::Item
T::MAX
T::make()
```

Resolver xác định candidate associated item.

Trait solver/type system quyết định implementation nào phù hợp.

---

# 38. Method resolution

Với:

```axiom
value.length()
```

resolver không chỉ lookup symbol `length` toàn cục.

Candidate order frozen từ Behavior Model:

```text
1. inherent methods
2. trait methods
3. explicitly imported extension methods
4. generic extension methods
```

---

# 39. Inherent method

```axiom
impl Vec2 {
    fn length(self: Vec2) -> f32 {}
}
```

Candidate:

```text
Vec2::length
```

---

# 40. Trait method

```axiom
trait Length {
    fn length(self: Self) -> f32
}
```

Nếu:

```axiom
impl Length for Vec2 {}
```

thì:

```text
value.length()
```

có thể resolve qua trait.

Trait solver phải xác định implementation hợp lệ.

---

# 41. Extension method

```axiom
fn length(v: Vec2) -> f32
```

nếu module import extension:

```axiom
use math::length
```

có thể gọi:

```axiom
v.length()
```

nhưng extension phải được explicit imported.

Không tự quét toàn bộ package universe.

---

# 42. Generic extension

Có thể có:

```axiom
fn first<T>(x: Collection<T>) -> Option<T>
```

Method candidate được xem xét sau explicit extensions.

---

# 43. Method ambiguity

Nếu:

```text
TraitA::length
TraitB::length
```

đều applicable:

```axiom
x.length()
```

→ ambiguity.

Không chọn dựa trên:

```text
import order
trait declaration order
compiler hash
```

Người lập trình phải disambiguate.

---

# 44. Explicit trait qualification

Có thể dùng dạng:

```text
TraitA::length(x)
```

hoặc syntax equivalent được đóng băng ở grammar.

Mục tiêu:

```text
zero ambiguity
```

---

# 45. Path resolution

Path:

```text
a::b::c
```

resolver đi từng segment:

```text
a
 ↓
b
 ↓
c
```

Mỗi segment có candidate namespace phù hợp.

---

# 46. Absolute vs relative paths

Axiom nên phân biệt:

```text
current-module-relative
package-root
external-package
```

Khuyến nghị syntax rõ ràng thay vì heuristic.

Ví dụ conceptual:

```text
self::foo
package::foo
external_package::foo
```

Chi tiết syntax phải đồng bộ với package system.

---

# 47. `self`

Trong module:

```axiom
self::Renderer
```

là current module.

Không nhầm với method receiver `self`.

Context parser/resolver phân biệt syntactically.

---

# 48. `super`

Nếu hỗ trợ:

```text
super::foo
```

chỉ có nghĩa module parent.

Không phải inheritance.

Đây là điểm quan trọng vì Axiom không có class inheritance.

---

# 49. No implicit global namespace

Axiom không có một “global soup” chứa tất cả symbols.

Mọi symbol phải thuộc:

```text
package
module
scope
```

trừ built-in/compiler-known declarations được expose qua explicit prelude mechanism.

---

# 50. Prelude

Axiom có thể có:

```text
std prelude
```

nhưng phải kiểm soát được.

Khuyến nghị:

```text
minimal prelude
```

chỉ chứa những thứ thiết yếu như:

```text
Option
Result
basic traits
core intrinsics wrappers
```

và compiler phải có API:

```text
explain why name resolved
```

---

# 51. Builtin types

```text
i32
u64
bool
f32
...
```

được resolver nhận diện qua compiler-known type namespace.

Nhưng chúng vẫn có:

```text
TypeId
```

không phải magic string rải khắp compiler.

---

# 52. Builtin functions

Không nên có hàng trăm magic builtins.

Ví dụ intrinsic:

```text
size_of
align_of
```

có thể được biểu diễn bằng:

```text
compiler-known declaration
```

và semantic rule riêng.

---

# 53. Symbol graph example

```axiom
module math::vector

pub struct Vec2 {
    x: f32
    y: f32
}

impl Vec2 {
    fn length(self: Vec2) -> f32 { ... }
}
```

Graph:

```text
ModuleId(math::vector)
 │
 ├── DeclarationId(Vec2)
 │      └── TypeId(Vec2)
 │
 └── Impl
      └── FunctionId(Vec2::length)
```

---

# 54. Reference graph

```axiom
fn foo(x: Vec2) {
    x.length()
}
```

semantic graph:

```text
foo
 │
 ├── x → ParameterDeclaration
 │
 └── length()
       ↓
   FunctionId(Vec2::length)
```

Sau resolver, HIR không cần giữ string `"length"` để quyết định semantics.

---

# 55. Resolution result

Chuẩn hóa:

```text
ResolveResult<T> =
    Resolved(T)
    Unresolved
    Ambiguous(Candidates)
    Inaccessible
    Invalid
    Error
```

Đặc biệt:

```text
Ambiguous ≠ Unresolved
```

AI/compiler tooling cần phân biệt hai trường hợp.

---

# 56. Ambiguity không được tự chữa

Nếu:

```text
Foo
```

có hai candidates:

```text
A::Foo
B::Foo
```

resolver:

```text
Ambiguous
```

Không:

```text
pick first
pick shortest
pick imported last
pick same file
pick most likely
```

---

# 57. Symbol resolution và AI

AI agent có thể hỏi:

```text
ax explain symbol Foo
```

Compiler trả:

```text
name: Foo
status: ambiguous
candidates:
    A::Foo
    B::Foo
required_action:
    explicit qualification
```

Đây chính là kiểu compiler interface phù hợp với mục tiêu AI-native.

---

# 58. Incremental resolution

CompilerDB query:

```text
resolve_name(scope, name)
```

có dependency:

```text
ScopeId
Name
ModuleRevision
ImportSet
DeclarationSet
```

Nếu một function body thay đổi nhưng module declarations không đổi:

```text
module symbol graph
```

có thể reuse.

---

# 59. Dependency graph

Resolution query phải ghi nhận:

```text
ResolverQuery
 ├── source revision
 ├── scope
 ├── imports
 ├── declarations
 └── result
```

để invalidation chính xác.

---

# 60. Cyclic imports

Ví dụ:

```text
A → B
B → A
```

Không phải mọi cycle đều sai.

Cần phân biệt:

```text
module graph cycle
```

với:

```text
initialization cycle
```

vì Axiom declarations có thể resolve qua cycle.

---

# 61. Module import cycle

Cho phép module graph cycle nếu chỉ liên quan declaration/type namespace và không tạo semantic impossibility.

Nhưng package dependency cycle theo BOOTSTRAP-187 vẫn bị cấm.

Do đó:

```text
Package cycle
    forbidden

Module cycle
    potentially allowed
```

---

# 62. Value initialization cycles

Nếu:

```axiom
const a = b
const b = a
```

đây không còn là resolution issue.

Resolver có thể resolve cả hai:

```text
a → ConstA
b → ConstB
```

Comptime/const evaluator phát hiện cycle.

---

# 63. Generic scope

Ví dụ:

```axiom
fn foo<T>(x: T) {}
```

scope:

```text
FunctionScope
 ├── GenericParam T
 └── Parameter x
```

`T` được resolve như type parameter.

---

# 64. Associated type scope

Trong trait:

```axiom
trait Iterator {
    type Item
}
```

`Item` có identity:

```text
AssociatedTypeId
```

Không phải ordinary module type.

---

# 65. Pattern binding resolution

```axiom
match value {
    Some(x) => x
}
```

`x` được tạo trong arm-local scope.

```text
MatchArmScope
    └── x
```

chỉ sống trong arm body/guard theo grammar.

---

# 66. Pattern binding conflict

```axiom
Some(x, x)
```

nếu pattern không cho phép duplicate binding:

```text
error
```

Resolver/pattern checker xử lý, không phải lexer.

---

# 67. Closure scope

```axiom
let f = |x| x + offset
```

Closure tạo:

```text
ClosureScope
 ├── x
 └── captured references
```

`offset` được resolved ở enclosing scope.

Capture mode được Closure Analysis xác định sau.

---

# 68. Local declaration ordering

Resolver phải biết declaration nào đã tồn tại tại điểm sử dụng nếu Axiom cấm use-before-declaration đối với local bindings.

Ví dụ:

```axiom
use(x)
let x = 10
```

có thể là:

```text
unresolved
```

Trong khi top-level function declarations có hoisting/collection như phần trên.

**Đây là distinction quan trọng:**

```text
module declarations
    collect first

local declarations
    lexical-order semantics
```

---

# 69. Namespace collisions

Ví dụ:

```axiom
struct Foo {}
fn Foo() {}
```

Nếu type/value namespace tách biệt:

```text
Foo(type)
Foo(value)
```

có thể cùng tồn tại.

Nhưng:

```axiom
let x: Foo
Foo()
```

resolver dùng expected syntactic namespace.

Điều này cho phép syntax mạnh mà không tạo ambiguity.

---

# 70. Type/value same name

Khuyến nghị **cho phép khác namespace**.

Ví dụ:

```axiom
struct Result {}

fn Result() {}
```

có thể hợp lệ nếu hai namespace khác nhau.

Nhưng tooling phải hiển thị namespace rõ ràng.

---

# 71. Import namespace

Import phải biết target namespace:

```text
ImportBinding {
    local_name
    target
    namespace
    visibility
}
```

Không chỉ:

```text
Map<String, DeclarationId>
```

---

# 72. Resolver architecture

Đề xuất:

```text
Resolver
├── ModuleResolver
├── DeclarationCollector
├── ScopeResolver
├── ImportResolver
├── PathResolver
├── NameResolver
├── MethodCandidateResolver
├── VisibilityChecker
└── SymbolGraphBuilder
```

Tất cả dùng:

```text
CompilerDB
```

---

# 73. Không để MethodResolver tự type-check

Method resolver có thể tạo:

```text
CandidateSet
```

nhưng applicability đầy đủ có thể cần:

```text
Type System
Trait Solver
```

Do đó:

```text
Name Resolution
    ↓
Candidate discovery
    ↓
Type/trait resolution
    ↓
Final callable selection
```

Không tạo dependency vòng.

---

# 74. Resolution vs type checking

Ví dụ:

```axiom
foo(x)
```

Resolver:

```text
foo → FunctionId
```

Type checker:

```text
x : T
foo expects U
T compatible U?
```

Trait solver:

```text
T: Trait?
```

Ba vấn đề khác nhau.

---

# 75. Semantic symbol graph output

Sau BOOTSTRAP-238:

```text
AST
 ↓
Resolution
 ↓
Resolved AST / HIR input
```

Ví dụ:

```text
NameExpr("Vec2")
```

→

```text
TypeRef {
    declaration: DeclarationId(42)
}
```

và:

```text
MethodCall("length")
```

→ candidate semantic identity.

---

# 76. Frozen invariants

```text id="9r8cwx"
ARESOLVE-20
Every declaration has a stable semantic identity.

ARESOLVE-21
Names are resolved through explicit lexical/module/package scopes.

ARESOLVE-22
Resolution is deterministic.

ARESOLVE-23
Resolution does not depend on memory addresses.

ARESOLVE-24
Resolution does not depend on hash iteration order.

ARESOLVE-25
Top-level declarations are collected before body resolution.

ARESOLVE-26
Local binding resolution follows defined lexical-order semantics.

ARESOLVE-27
Shadowing creates distinct declaration identities.

ARESOLVE-28
A reference resolves to exactly one declaration or an explicit non-resolved state.

ARESOLVE-29
Ambiguous references are never resolved heuristically.

ARESOLVE-30
Unresolved and ambiguous states are distinct.

ARESOLVE-31
Visibility is checked independently from declaration identity.

ARESOLVE-32
Re-export does not create a new declaration identity.

ARESOLVE-33
Imports create bindings, not declaration copies.

ARESOLVE-34
Package boundaries are distinct from module boundaries.

ARESOLVE-35
Module cycles are distinct from package dependency cycles.

ARESOLVE-36
Resolution of names is distinct from type inference.

ARESOLVE-37
Resolution of names is distinct from trait solving.

ARESOLVE-38
Resolution of names is distinct from ownership verification.

ARESOLVE-39
Generic inference is not performed by lexical name resolution.

ARESOLVE-40
Method resolution follows the defined candidate precedence.

ARESOLVE-41
Extension methods are not discovered from arbitrary package-global search.

ARESOLVE-42
Method ambiguity requires explicit disambiguation.

ARESOLVE-43
Associated item lookup preserves type/trait identity.

ARESOLVE-44
Pattern bindings create explicit lexical scopes.

ARESOLVE-45
Closure parameters create explicit lexical scopes.

ARESOLVE-46
Generic parameters create explicit semantic scopes.

ARESOLVE-47
Namespace identity is explicit.

ARESOLVE-48
Type and value namespaces may coexist without accidental collision.

ARESOLVE-49
Built-in declarations have compiler-known semantic identities.

ARESOLVE-50
No implicit universal global symbol namespace exists.

ARESOLVE-51
Public API visibility violations are detected before production code generation.

ARESOLVE-52
Incremental resolution invalidates only queries whose semantic dependencies changed.

ARESOLVE-53
Symbol graph edges preserve source provenance.

ARESOLVE-54
Resolver diagnostics expose candidates for ambiguity.

ARESOLVE-55
Resolver must never use probabilistic or AI-based symbol selection.

ARESOLVE-56
Partial-program resolution may produce Unknown/Incomplete results but never semantic proof.

ARESOLVE-57
Synthetic recovery nodes cannot establish declaration identity as production fact.

ARESOLVE-58
Resolution results are stable under unrelated declaration ordering changes.

ARESOLVE-59
Semantic identity is independent of source spelling aliases and re-export paths.

ARESOLVE-60
The resolver is a replaceable compiler stage whose observable semantics are defined by the Formal Semantic Kernel.
```

---

# 77. Compiler architecture sau 238

Axiom hiện đã có một chuỗi frontend rất rõ:

```text
                  SOURCE
                    │
                    ▼
                  Lexer
                    │
                    ▼
               TokenStream
                    │
                    ▼
            Lossless Syntax Tree
                    │
                    ▼
                   AST
                    │
                    ▼
        ┌─────────────────────────┐
        │      Resolution         │
        │                         │
        │ Module / Scope / Import │
        │ Name / Path / Method    │
        └────────────┬────────────┘
                     │
                     ▼
              DeclarationId
                     │
                     ▼
                    HIR
                     │
                     ▼
              Type / Trait System
                     │
                     ▼
                   MIR
```

Điểm đáng chú ý là đến đây Axiom đã tránh được một lỗi thiết kế phổ biến:

> **Không dùng một “compiler pass thần thánh” vừa parse, vừa resolve, vừa infer type, vừa kiểm tra ownership.**

Mỗi tầng có một semantic responsibility rõ ràng.

---

# TASK TIẾP THEO

## **BOOTSTRAP-239 — AXIOM TYPE SYSTEM & TYPE INFERENCE ENGINE**

Đây sẽ là một bước rất lớn.

Sẽ đóng đinh toàn bộ:

```text
Type
 ├── Primitive
 ├── Struct
 ├── Enum
 ├── Tuple
 ├── Array
 ├── Function
 ├── Closure
 ├── Generic
 ├── Type Parameter
 ├── Associated Type
 ├── view<T>
 ├── mut_view<T>
 ├── dyn Trait
 ├── Never
 └── Unit
```

và đặc biệt:

- type identity
- nominal vs structural typing
- type aliases vs newtypes
- generic inference
- unification
- type variables
- coercion
- numeric inference
- function type
- closure type
- `Self`
- associated types
- const generic types
- array length typing
- `Option`/`Result`
- `dyn Trait`
- `Copy`/`Clone`/`Drop`/`Send`/`Share` type facts
- type normalization
- canonical type representation
- type interning trong `TypeDB`
- cyclic type detection
- inference failure/ambiguity
- và quan trọng nhất: **làm thế nào để type system mạnh nhưng không biến Axiom thành một ngôn ngữ có type syntax và inference quá phức tạp đối với lập trình viên.**