# BOOTSTRAP-098 — Axiom Module System, Name Resolution, Visibility & Import Architecture

**Trạng thái: FROZEN**

Mục tiêu:

> **Module system phải đủ mạnh cho project hàng triệu dòng code, nhưng programmer không phải quản lý namespace/import phức tạp. Name resolution phải deterministic, nhanh, incremental và thân thiện với AI.**

---

# 1. Tách 4 khái niệm

Axiom phân biệt rõ:

```text
Package
Module
Namespace
Declaration
```

### Package

Đơn vị dependency/version/build.

### Module

Đơn vị tổ chức source và semantic namespace.

### Namespace

Không gian chứa tên.

### Declaration

Symbol thực tế:

```text
fn
struct
enum
trait
const
type
```

Không được đồng nhất:

```text
file = module = namespace = package
```

---

# 2. Module không bắt buộc tương ứng 1 file

Có thể:

```text
module math
```

được định nghĩa từ nhiều source unit.

Ngược lại một source file có thể chứa nhiều nested module.

Filesystem chỉ là convention mặc định.

---

# 3. Mapping mặc định

Để dễ dùng, Axiom vẫn có convention:

```text
src/
    main.ax
    math.ax
    math/
        vector.ax
        matrix.ax
```

Ví dụ:

```text
math/vector.ax
```

có thể tương ứng:

```text
myapp.math.vector
```

Nhưng compiler không xem pathname là semantic identity.

---

# 4. Module identity

Module identity:

```text
ModuleId
```

thuộc:

```text
PackageId
+
ModulePath
```

Ví dụ:

```text
myapp.math.vector
```

Không phụ thuộc:

```text
C:\project\src\math\vector.ax
```

---

# 5. Qualified name

Canonical symbol name:

```text
package::module::name
```

Ví dụ:

```text
mathlib::vector::Vec3
```

Trong source thường chỉ cần:

```text
vector::Vec3
```

hoặc:

```text
Vec3
```

nếu đã import.

---

# 6. `::` dành cho namespace/type path

Axiom dùng:

```text
foo::bar
```

cho:

```text
module
type
trait
associated item
```

Ví dụ:

```text
math::Vec3
Result::unwrap
Option::Some
```

Không dùng `.` cho namespace.

`.` dành cho value/member/method:

```text
v.length()
user.name
```

---

# 7. Import là compile-time

```text
import std::io::File;
```

chỉ ảnh hưởng:

```text
name resolution
dependency graph
metadata loading
```

Không phải runtime execution.

---

# 8. Import không đồng nghĩa link

```text
import std::math::Vector;
```

không có nghĩa toàn bộ:

```text
std.math
```

được link vào executable.

Dead-code elimination và dependency analysis quyết định runtime artifact.

---

# 9. Import declaration

Canonical:

```text
import std::io::File;
```

Nghĩa là symbol:

```text
File
```

được đưa vào lexical namespace hiện tại.

---

# 10. Import nhiều symbol

```text
import std::io::{File, Socket, Stream};
```

Không cần:

```text
import std::io::File;
import std::io::Socket;
import std::io::Stream;
```

---

# 11. Module import

Có thể import namespace:

```text
import std::io;
```

sau đó:

```text
io::File
io::Socket
```

Nhưng Axiom **không tự động mở toàn bộ namespace vào scope**.

---

# 12. Wildcard import

Không khuyến khích:

```text
import std::io::*;
```

và trong Core v1:

> **Wildcard import không được phép mặc định.**

Lý do:

```text
name collision
API drift
AI ambiguity
incremental invalidation
```

Nếu cần, có thể có explicit tooling-only mechanism sau này.

---

# 13. Import alias

```text
import graphics::Color as GColor;
```

Sau đó:

```text
GColor::RGB(...)
```

---

# 14. Module alias

```text
import graphics::renderer as gfx;
```

dùng:

```text
gfx::Renderer
```

---

# 15. Re-export

Module có thể expose symbol từ module khác:

```text
pub use math::Vec3;
```

Ví dụ:

```text
myengine::prelude::Vec3
```

thực chất có thể re-export:

```text
math::Vec3
```

---

# 16. `use` hay `import`?

Axiom chọn **`import`** làm keyword chính.

Lý do:

```text
import
```

mang ý nghĩa trực tiếp:

> đưa declaration/module dependency vào namespace hiện tại.

Không dùng nhiều từ khóa khác nhau cho những semantics gần giống nhau.

---

# 17. Visibility

Core v1 có hai mức chính:

```text
private
pub
```

### private

Chỉ module định nghĩa và phạm vi con hợp lệ theo module ownership.

### pub

Có thể được sử dụng từ module/package được phép nhìn thấy declaration.

---

# 18. Package boundary

`pub` không đồng nghĩa:

```text
export binary symbol
```

Ví dụ:

```text
pub fn foo()
```

cho phép compiler/API consumer sử dụng.

Nhưng chưa chắc tạo ELF/PE/Mach-O exported symbol.

Muốn binary export:

```text
@export("foo")
```

---

# 19. Ba tầng visibility

Axiom phân biệt:

```text
Source Visibility
API Visibility
Binary Export
```

Ví dụ:

```text
private
pub
@export
```

Đây là ba semantics khác nhau.

---

# 20. Không có `pub(crate)` trong Core v1

Các modifier visibility quá chi tiết dễ tạo:

```text
pub(crate)
pub(super)
pub(in ...)
```

và làm module graph khó hiểu.

Axiom v1 giữ:

```text
private
pub
```

Nếu thực sự cần package-internal visibility, có thể thêm sau khi có use case thực tế.

---

# 21. Module con

Ví dụ:

```text
module graphics {
    module renderer {
        ...
    }
}
```

Canonical path:

```text
graphics::renderer
```

Nested module không nhất thiết tạo runtime object.

---

# 22. Private child module

```text
module graphics {
    module renderer {
        private_impl()
    }
}
```

`renderer` có thể không xuất hiện trong public API.

Compiler metadata vẫn biết nó tồn tại.

---

# 23. Public API graph

Compiler duy trì:

```text
PublicApiGraph
```

chỉ chứa những declaration có thể observable từ package boundary.

Điều này rất quan trọng cho incremental compilation.

---

# 24. Private implementation graph

Tách:

```text
PublicApiGraph
PrivateSemanticGraph
```

Nếu private implementation thay đổi mà public contract không đổi:

```text
downstream API analysis
```

có thể không invalidate.

---

# 25. Name resolution pipeline

Axiom dùng:

```text
Source
 ↓
Lexical scope
 ↓
Local declarations
 ↓
Imported declarations
 ↓
Module declarations
 ↓
Trait/associated lookup
 ↓
Generic constraints
 ↓
Resolved DeclarationId
```

Cuối cùng mọi symbol reference được canonicalize thành:

```text
DeclarationId
```

---

# 26. Không giữ symbol bằng string sau semantic resolution

Ban đầu:

```text
"Vec3"
```

sau resolution:

```text
DeclarationId(18472)
```

Các compiler phase sau dùng ID.

Điều này:

- nhanh;
- deterministic;
- tránh string comparison;
- tốt cho incremental;
- tốt cho AI tooling.

---

# 27. Lexical scope

Ví dụ:

```text
fn foo() {
    let x = 10;

    {
        let y = 20;
        ...
    }
}
```

Scope tree:

```text
FunctionScope
 ├── x
 └── BlockScope
      └── y
```

---

# 28. Shadowing

Cho phép local shadowing:

```text
let x = 1;

{
    let x = 2;
}
```

nhưng compiler có thể cảnh báo:

```text
SHADOWED_BINDING
```

nếu configuration yêu cầu.

---

# 29. Declaration shadowing

Không cho phép silent collision:

```text
import a::Foo;
import b::Foo;
```

nếu cả hai được đưa trực tiếp vào cùng namespace.

→ compile error.

---

# 30. Explicit alias giải quyết collision

```text
import a::Foo;
import b::Foo as BFoo;
```

rõ ràng:

```text
Foo
BFoo
```

AI agent cũng dễ xử lý.

---

# 31. Không dùng "last import wins"

Axiom tuyệt đối không có:

```text
import A::Foo;
import B::Foo;
```

rồi:

```text
Foo
```

tự động trỏ tới B.

Ambiguity phải là compile error.

---

# 32. Deterministic resolution

Cùng source:

```text
same source
same dependency graph
same compiler semantics
```

→ cùng `DeclarationId`.

Không phụ thuộc:

```text
import order
filesystem order
hash-map iteration order
parallel compilation order
```

---

# 33. Import order không có semantic effect

Hai source:

```text
import a::A;
import b::B;
```

và:

```text
import b::B;
import a::A;
```

phải có cùng semantics.

---

# 34. Local declarations ưu tiên imported declarations

Ví dụ:

```text
import foo::X;

fn X() {}
```

Reference:

```text
X
```

resolve tới local declaration.

Nhưng nếu collision không rõ ràng trong cùng declaration namespace → diagnostic.

---

# 35. Explicit qualification luôn thắng ambiguity

```text
foo::X
bar::X
```

không ambiguous.

---

# 36. Separate namespaces

Axiom có thể phân biệt namespace theo declaration kind:

```text
TypeNamespace
ValueNamespace
TraitNamespace
ModuleNamespace
```

Ví dụ:

```text
struct Foo {}
fn Foo() {}
```

có thể được cho phép nếu compiler xác định namespace khác nhau.

Tuy nhiên để giảm complexity, **không nên khai thác điều này quá mức trong source API**.

---

# 37. Khuyến nghị: type/value namespace tách nhưng syntax vẫn đơn giản

Ví dụ:

```text
struct User {}

fn User() {}
```

compiler có thể xử lý riêng.

Nhưng programmer không nên phải nhớ nhiều namespace rules.

---

# 38. Associated items

```text
Vec::new()
Vec::with_capacity()
```

là associated functions.

```text
value.length()
```

là method lookup.

Compiler không coi chúng là cùng một mechanism.

---

# 39. Method resolution

Theo baseline:

```text
1. inherent methods
2. trait implementations
3. explicitly imported extension methods
4. generic extensions
5. ambiguity/error
```

---

# 40. Extension methods

Ví dụ:

```text
fn length(v: view<Vec3>) -> usize
```

được gọi:

```text
v.length()
```

nếu module extension đã import.

Không import → không tự động tồn tại.

Điều này tránh "method pollution".

---

# 41. Trait method lookup

```text
trait Drawable {
    fn draw(self);
}
```

và:

```text
impl Drawable for Button { ... }
```

`button.draw()` có thể resolve tới trait implementation.

Compiler phải chứng minh trait implementation hợp lệ.

---

# 42. Generic extension

Ví dụ:

```text
fn is_empty<T>(x: view<T>) -> bool
```

có thể áp dụng nhiều type.

Nhưng chỉ được xem xét sau lookup cụ thể hơn.

---

# 43. Trait ambiguity

Nếu:

```text
TraitA::draw
TraitB::draw
```

đều phù hợp:

```text
x.draw()
```

→ compile error.

Programmer có thể viết:

```text
TraitA::draw(x)
```

hoặc syntax qualified tương đương.

---

# 44. Import không ảnh hưởng ownership

```text
import foo::Vec;
```

không tạo:

```text
runtime reference
ownership
allocation
```

Import chỉ là compile-time namespace operation.

---

# 45. Module initialization

Axiom **không có implicit module constructor chạy lúc import**.

```text
import foo;
```

không có nghĩa:

```text
foo.init()
```

runtime.

Đây là quyết định quan trọng để tránh global initialization order problems.

---

# 46. Static initialization

Nếu cần:

```text
static
```

phải có semantics explicit.

Compiler phân biệt:

```text
compile-time constant
static storage
runtime initialization
```

Không tạo constructor ngầm cho module.

---

# 47. Global mutable state

Không bị cấm tuyệt đối trong system layer.

Nhưng phải dùng explicit synchronization/storage semantics.

Ví dụ:

```text
static COUNTER: Atomic<i64>;
```

rõ ràng.

Không có:

```text
magic global singleton
```

do module import.

---

# 48. Prelude

Đã frozen ở BOOTSTRAP-094.

Implicit prelude:

```text
Option
Result
Some
None
Ok
Err
Copy
Clone
Drop
Send
Share
Iterator
IntoIterator
```

Không implicit:

```text
Vec
String
HashMap
File
Arc
Mutex
```

---

# 49. Prelude không được phép thay đổi âm thầm

Prelude là một phần semantic environment.

Nếu version package/compiler thay đổi prelude:

```text
name resolution
```

có thể thay đổi.

Vì vậy prelude version/config phải là build input.

---

# 50. Explicit no-prelude

System/freestanding code có thể:

```text
@no_prelude
```

để có environment tối thiểu.

Compiler vẫn phải cung cấp intrinsic language semantics.

---

# 51. No-prelude không có nghĩa no compiler support

Ví dụ:

```text
Option
```

không available.

Nhưng:

```text
if
match
move
drop
view
```

vẫn là language semantics.

---

# 52. Prelude collision

Nếu programmer định nghĩa:

```text
fn Result(...)
```

và prelude cũng có `Result`:

Axiom không nên silent shadow.

Compiler yêu cầu:

```text
explicit qualification
```

hoặc báo collision.

Mục tiêu là tránh code thay đổi nghĩa chỉ vì compiler/prelude version.

---

# 53. Source imports và AI

Compiler diagnostic nên nói:

```text
UNRESOLVED_NAME
```

và structured data:

```text
{
    "name": "Vec3",
    "scope": "...",
    "candidates": [...]
}
```

AI agent có thể tự sửa:

```text
import math::Vec3;
```

thay vì đoán.

---

# 54. Suggestion engine

Compiler có thể đưa:

```text
help: `Vec3` is declared in `math::vector`
suggestion: import math::vector::Vec3
```

Suggestion không có semantic effect cho tới khi source được sửa.

---

# 55. Name resolution database

Trong CompilerDB:

```text
ModuleDB
DeclarationDB
ImportDB
ScopeDB
NameResolutionDB
```

`NameResolutionDB` query dạng:

```text
resolve_name(scope, name)
resolve_path(scope, path)
resolve_method(type, name)
resolve_trait_method(type, trait, name)
```

---

# 56. Query-based architecture

Name resolution phải là query.

Ví dụ:

```text
resolve(ModuleId, Name)
```

có cache.

Nếu module A không thay đổi:

```text
resolve(A, X)
```

không cần tính lại.

---

# 57. Cycle handling

Module cycle:

```text
A imports B
B imports A
```

không nhất thiết phải cấm tuyệt đối.

Compiler có thể hỗ trợ **declaration-level cyclic dependency** nếu không tạo initialization cycle.

Đây là điểm khác package cycle.

---

# 58. Khuyến nghị

Axiom v1:

```text
Package cycle: reject
Module cycle: allow at declaration/type level
Runtime initialization cycle: impossible by default
```

Điều này linh hoạt hơn mà không tạo global initialization chaos.

---

# 59. Module cycle example

```text
module a {
    import b::B;
    pub struct A {
        b: B
    }
}
```

```text
module b {
    import a::A;
    pub struct B {
        a: A
    }
}
```

Trường hợp value-recursive trực tiếp có thể bị reject bởi type/layout rules.

Nhưng declaration references có thể tồn tại.

---

# 60. Recursive types

Nếu:

```text
A contains B
B contains A
```

by-value vô hạn → reject.

Phải dùng indirection/storage abstraction:

```text
Box
Handle
```

hoặc abstraction phù hợp.

Module cycle không giải quyết type recursion.

---

# 61. Import cycle không tạo runtime cycle

Vì:

```text
import = compile-time
```

nên:

```text
A imports B
B imports A
```

không đồng nghĩa hai module chạy constructor.

---

# 62. Namespace flattening

Không tự động flatten:

```text
import graphics;
```

thành:

```text
Renderer
Texture
Mesh
Color
...
```

Phải viết:

```text
graphics::Renderer
```

hoặc import explicit từng symbol.

Điều này giúp API ổn định.

---

# 63. Public re-export facade

Một package có thể tạo API đẹp:

```text
package::prelude
```

và re-export:

```text
Vec3
Color
Mesh
Renderer
```

Consumer:

```text
import engine::prelude::{Vec3, Color};
```

Đây là cách Axiom xây API facade thay vì wildcard.

---

# 64. Internal module structure có thể thay đổi

Nếu:

```text
engine::prelude::Vec3
```

re-export:

```text
engine::math::vector::Vec3
```

thì consumer không cần biết implementation path.

Đây là API stability mechanism.

---

# 65. Import path và public API path

Compiler phải phân biệt:

```text
DeclarationId
```

với:

```text
PublicPath
```

Một declaration có thể có nhiều public re-export paths.

Canonical identity vẫn chỉ có một.

---

# 66. Re-export không duplicate declaration

```text
engine::Vec3
engine::math::Vec3
```

có thể cùng trỏ tới:

```text
DeclarationId(123)
```

Không tạo hai type.

---

# 67. Type identity

Quan trọng:

```text
type alias
```

giữ identity.

```text
newtype
```

tạo identity mới.

Re-export không tạo identity mới.

---

# 68. Import alias không tạo type mới

```text
import foo::User as Person;
```

`Person` vẫn là:

```text
foo::User
```

không phải newtype.

---

# 69. Module alias cũng không tạo module mới

```text
import graphics::renderer as gfx;
```

chỉ tạo local binding:

```text
gfx → ModuleId
```

---

# 70. Generic lookup

Ví dụ:

```text
Vec<T>
```

compiler resolution:

```text
Vec
↓
DeclarationId
↓
GenericDefinition
↓
Substitution<T>
```

không tạo symbol bằng string:

```text
"Vec<i32>"
```

---

# 71. Generic instance identity

Đã frozen ở generic engine:

```text
GenericInstanceId =
    GenericDefinition
    +
    TypeArguments
    +
    ConstArguments
```

Module system chỉ resolve definition.

Monomorphization engine xử lý instance.

---

# 72. Visibility verification

Resolution phải kiểm tra:

```text
symbol exists?
symbol visible?
symbol imported?
symbol type-compatible?
```

Ví dụ private:

```text
module a {
    fn secret() {}
}
```

module khác:

```text
import a::secret;
```

→ `PRIVATE_DECLARATION`.

---

# 73. Diagnostic ổn định

Các lỗi chính:

```text
ERESOLVE_UNDEFINED
ERESOLVE_AMBIGUOUS
ERESOLVE_PRIVATE
ERESOLVE_INVALID_PATH
ERESOLVE_IMPORT_CYCLE
ERESOLVE_DUPLICATE_IMPORT
ERESOLVE_SHADOW
ERESOLVE_INVALID_REEXPORT
```

Mã ổn định, text có thể thay đổi.

---

# 74. AI-friendly resolution

Ví dụ compiler trả:

```text
ERESOLVE_UNDEFINED

name: Vec3

candidates:
  - math::Vec2
  - graphics::Vec3
  - physics::Vec3

suggestions:
  - import graphics::Vec3
  - import physics::Vec3
```

AI không cần phân tích text error bằng heuristic yếu.

---

# 75. Import suggestions không tự động áp dụng

Compiler chỉ đề xuất.

IDE/AI có thể tự sửa source nếu người dùng cho phép.

Compiler không tự modify source trong `check`.

---

# 76. Source/file identity

`SourceFileId`:

```text
SourceFileId
```

không phải module identity.

Một module có thể:

```text
multiple source files
```

và generated source cũng có thể đóng góp declaration.

---

# 77. Generated modules

Comptime có thể generate declaration:

```text
comptime generate_schema()
```

Generated declarations trở thành:

```text
DeclarationDB
```

như declaration bình thường.

Không có "special generated namespace" khác semantic model.

---

# 78. Generated declaration provenance

Compiler vẫn giữ:

```text
SourceSpan
GenerationOrigin
```

để diagnostic nói:

```text
generated from schema.ax:42
```

thay vì chỉ:

```text
generated code error
```

---

# 79. Macro namespace không tồn tại trong Core

Không có:

```text
macro namespace
```

riêng.

Lý do:

Axiom chưa có procedural macro system trong Core.

Comptime typed generation là mechanism chính.

---

# 80. Import performance

Với project lớn:

```text
1,000,000+ declarations
```

compiler không scan toàn bộ symbol table cho mỗi lookup.

Dùng:

```text
ScopeId
Name → DeclarationId index
Module export index
Trait index
```

và interned strings/symbol IDs.

---

# 81. Symbol interning

Source:

```text
"Renderer"
```

được intern:

```text
SymbolId
```

Sau đó compiler so sánh:

```text
SymbolId == SymbolId
```

thay vì string.

---

# 82. Hash table không ảnh hưởng semantics

Hash table có thể dùng để lookup.

Nhưng declaration resolution result không được phụ thuộc iteration order.

Hash randomization được phép miễn:

```text
semantic result identical
```

---

# 83. Parallel name resolution

Independent modules có thể resolve song song.

Compiler phải đảm bảo:

```text
parallel resolution
=
serial resolution
```

---

# 84. Lazy resolution

Không cần resolve toàn bộ universe nếu query không yêu cầu.

Ví dụ compile:

```text
foo()
```

chỉ cần resolve dependency graph cần thiết.

Đây là lợi thế của query-based CompilerDB.

---

# 85. Public API loading

Khi dependency đã có:

```text
.axmeta
```

consumer có thể resolve public declarations mà không cần parse implementation source.

---

# 86. Source package loading

Compiler pipeline:

```text
Package
 ↓
Load axmeta if available
 ↓
Resolve imports
 ↓
Load source only when required
```

Giúp compile package lớn nhanh hơn.

---

# 87. Versioned metadata

`.axmeta` phải chứa:

```text
compiler semantic version
metadata schema version
package identity
target-relevant information
```

Metadata không tương thích → compiler rebuild metadata.

---

# 88. ABI metadata

Nếu package cung cấp native library:

`.axmeta` có thể chứa:

```text
ABI
calling convention
repr
exports
link requirements
target
```

Không cần đọc object binary chỉ để type-check source consumer.

---

# 89. System modules

Platform modules:

```text
sys::windows
sys::linux
sys::macos
sys::android
sys::ios
sys::wasm
```

được chọn theo target.

Không được compile Windows-specific declaration vào Linux nếu `@cfg` loại nó.

---

# 90. Platform namespace isolation

Code:

```text
import sys::windows::Handle;
```

trên Linux:

```text
invalid target declaration
```

hoặc nếu protected bằng `@cfg`:

```text
excluded before resolution
```

---

# 91. Conditional declarations

Ví dụ:

```text
@cfg(target = "windows")
pub fn windows_only() {}
```

Declaration không tồn tại trong target khác.

Nó không phải declaration rồi bị runtime disabled.

---

# 92. Configuration phase

Thứ tự:

```text
Package configuration
        ↓
@cfg filtering
        ↓
Module graph
        ↓
Name resolution
        ↓
Type checking
```

Điều này giúp tránh resolve symbol từ code đã bị loại.

---

# 93. `@cfg` không được phụ thuộc runtime

Không:

```text
@cfg(if runtime_condition)
```

Chỉ build-time facts.

---

# 94. Environment-specific imports

Không khuyến khích:

```text
if windows import...
```

Thay vào đó:

```text
@cfg(target = "windows")
import sys::windows::...
```

hoặc platform abstraction.

---

# 95. Final architecture

```text
                     Package
                        │
                        ▼
                   Module Graph
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
        @cfg Filtering       Public Metadata
              │                   │
              └─────────┬─────────┘
                        ▼
                  Scope Graph
                        │
                        ▼
                 Name Resolution
                        │
             ┌──────────┼──────────┐
             ▼          ▼          ▼
          Types       Traits     Values
             │          │          │
             └──────────┼──────────┘
                        ▼
                  DeclarationId
                        │
                        ▼
                     HIR
```

---

# 96. Những thứ Axiom **không** làm

Để giữ architecture sạch, Core v1 **không** có:

```text
❌ wildcard import mặc định
❌ last-import-wins
❌ implicit module initialization
❌ global constructor registry
❌ macro namespace
❌ package-level runtime singleton
❌ implicit dependency download
❌ file path làm semantic identity
❌ import tạo runtime object
❌ pub = binary export
❌ re-export tạo type mới
❌ import order ảnh hưởng semantics
```

---

# 97. Các invariant frozen

Tóm tắt nhóm quan trọng:

```text
AMOD-20  Module identity is independent of filesystem path
AMOD-21  Package and module identity are distinct
AMOD-22  Import is compile-time
AMOD-23  Import does not imply runtime linking
AMOD-24  Import order does not affect semantics
AMOD-25  Name resolution is deterministic
AMOD-26  Resolved references use DeclarationId
AMOD-27  Ambiguous names are compile errors
AMOD-28  Wildcard import is not Core v1
AMOD-29  Explicit qualification resolves ambiguity
AMOD-30  Aliases do not create new type identity
AMOD-31  Re-export does not create new declaration identity
AMOD-32  Visibility is distinct from binary export
AMOD-33  @export is distinct from pub
AMOD-34  Prelude is part of compilation environment
AMOD-35  Prelude changes affect build identity
AMOD-36  No implicit module initialization
AMOD-37  Package cycles are rejected
AMOD-38  Module declaration cycles may be supported
AMOD-39  Runtime initialization cycles are not implicit
AMOD-40  Generated declarations re-enter normal resolution
AMOD-41  @cfg filtering precedes normal resolution
AMOD-42  Host/target module selection is deterministic
AMOD-43  Private implementation is distinct from public API
AMOD-44  Public re-export preserves declaration identity
AMOD-45  Symbol lookup is indexed
AMOD-46  Symbol interning is permitted
AMOD-47  Hash iteration order has no semantic effect
AMOD-48  Parallel resolution equals serial resolution
AMOD-49  Name resolution is incrementally cacheable
AMOD-50  Metadata may satisfy public resolution
AMOD-51  Metadata schema is versioned
AMOD-52  Import suggestions do not mutate source
AMOD-53  Compiler diagnostics have stable resolution codes
AMOD-54  Module imports do not imply ownership
AMOD-55  Module imports do not imply allocation
AMOD-56  Module imports do not imply runtime execution
AMOD-57  Extension methods require explicit import
AMOD-58  Method lookup order is deterministic
AMOD-59  Trait ambiguity is explicit
AMOD-60  Platform-specific declarations are target-qualified
AMOD-61  @cfg is compile-time selection
AMOD-62  Runtime conditions cannot control module selection
AMOD-63  No implicit dependency fetching
AMOD-64  Public API paths may be facades over internal modules
AMOD-65  Canonical declaration identity is independent of public path
AMOD-66  Source file identity is distinct from module identity
AMOD-67  Generated source retains provenance
AMOD-68  Name resolution operates over semantic IDs, not raw strings
AMOD-69  Lazy resolution is permitted
AMOD-70  Incremental resolution must preserve semantic equivalence
AMOD-71  Module system must remain usable in freestanding builds
AMOD-72  Module system must not require a monolithic runtime
```

---

## Kết quả

Axiom hiện có một module architecture khá sạch:

```text
Package
   │
   ├── Module
   │     └── Namespace
   │            └── Declaration
   │
   └── Public API
           └── Re-export
```

và compiler biến mọi reference cuối cùng thành:

```text
Name
 ↓
SymbolId
 ↓
DeclarationId
 ↓
Typed semantic entity
```

Điều này đặc biệt phù hợp với mục tiêu **AI-friendly compiler**: AI không cần đoán từ text xem `Vec3` là gì; compiler có thể trả trực tiếp `DeclarationId`, module, visibility, candidate list và lý do resolution thất bại.

### Task kế tiếp: **BOOTSTRAP-099 — Axiom Initialization, Static Storage, Global State & Program Entry**

Phần này cần khóa một vấn đề rất quan trọng còn lại:

```text
static
const
global
TLS
lazy initialization
startup
shutdown
main
freestanding entry
constructors
destructors
process exit
DLL/shared-library initialization
```

đặc biệt phải đảm bảo **không xuất hiện "global constructor/destructor hell" kiểu C++**, nhưng vẫn đủ mạnh để xây compiler, OS layer, GUI, game engine và ứng dụng native lớn.