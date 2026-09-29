# BOOTSTRAP-354 — AXIOM MODULE, VISIBILITY, NAMESPACE & NAME RESOLUTION ENGINE

Sau pattern matching, bước tiếp theo nên khóa **module + namespace + name resolution**. Đây là lớp nền trước khi đi sâu hơn vào package ecosystem, macro/comptime generation, IDE và compiler self-hosting.

Mục tiêu:

> **Tên trong Axiom phải được resolve một cách xác định, nhanh, incremental và không phụ thuộc vào thứ tự khai báo hoặc thứ tự import.**

Đồng thời hệ thống module phải đủ mạnh để xây cả:

- ứng dụng;
- thư viện;
- OS;
- compiler;
- GPU library;
- package;
- plugin/component;
- multi-target project.

---

## 1. Tách 4 khái niệm

Axiom phải phân biệt rõ:

```text
Namespace
Module
Package
Compilation Unit
```

### Namespace

Không gian tên logic.

### Module

Đơn vị tổ chức source/API.

### Package

Đơn vị dependency/version/distribution.

### Compilation Unit

Đơn vị compiler có thể compile/cache/incremental.

Không được coi 4 khái niệm này là một.

---

# 2. Module tree

Một package:

```text
my_app/
    axiom.toml
    src/
        main.ax
        math/
            mod.ax
            vector.ax
        io/
            mod.ax
            file.ax
```

có thể tạo:

```text
my_app
├── main
├── math
│   └── vector
└── io
    └── file
```

Nhưng filesystem không nhất thiết phải quyết định semantic module hierarchy.

Compiler có:

```text
ModuleDB
```

làm source of truth.

---

# 3. Module declaration

Axiom có thể dùng:

```text
module math.vector
```

hoặc folder-based convention.

Khuyến nghị:

> **Module identity là semantic declaration; filesystem mapping chỉ là build convention.**

Như vậy compiler có thể hỗ trợ:

- generated modules;
- embedded modules;
- package archives;
- virtual source;
- IDE buffers;
- single-file programs.

---

# 4. Namespace

Trong một module:

```text
struct Vec3
fn dot(...)
const PI = ...
trait Numeric
```

các declaration nằm trong namespace.

Compiler không sử dụng một flat global symbol table.

---

# 5. Declaration identity

Tên không phải identity.

Ví dụ:

```text
math::Vec3
```

được resolve thành:

```text
DeclarationId(123)
```

Sau đó mọi compiler phase dùng:

```text
DeclarationId
```

thay vì string name.

Điều này rất quan trọng cho:

- incremental compilation;
- refactoring;
- IDE;
- rename;
- `.axif`;
- semantic hashing.

---

# 6. Qualified names

Syntax:

```text
math::Vec3
math::vector::dot
```

dùng để truy cập explicit namespace.

Không dùng `.` cho namespace vì `.` đã có semantic:

```text
object.field
object.method()
```

---

# 7. Import

Ví dụ:

```text
import math::Vec3
import math::vector::dot
```

hoặc:

```text
import math::{
    Vec3,
    vector::dot,
}
```

Import tạo local name binding.

Không copy declaration.

---

# 8. Import alias

```text
import graphics::Vector as GpuVector
```

Sau đó:

```text
GpuVector(...)
```

Tên gốc vẫn:

```text
graphics::Vector
```

Alias chỉ là local resolution mapping.

---

# 9. Module alias

```text
import graphics as gfx
```

sử dụng:

```text
gfx::Vector
gfx::Color
```

Compiler resolve alias ngay tại semantic analysis.

Không tồn tại runtime namespace.

---

# 10. Wildcard import

Không nên khuyến khích:

```text
import math::*
```

nhưng có thể hỗ trợ.

Nếu hỗ trợ:

- không tạo symbol duplication;
- ambiguity phải báo lỗi;
- explicit local declaration thắng wildcard;
- explicit import thắng wildcard.

Ví dụ:

```text
import a::*
import b::*

foo()
```

nếu cả hai export `foo`:

```text
compile error: ambiguous name
```

Không chọn ngẫu nhiên.

---

# 11. Name resolution phases

Resolver:

```text
Source
 ↓
Lexical Scope
 ↓
Local Binding Resolution
 ↓
Module Resolution
 ↓
Import Resolution
 ↓
Type/Value/Trait Namespace Resolution
 ↓
Overload/Generic Resolution
 ↓
DeclarationId
```

---

# 12. Namespace separation

Axiom nên có các namespace semantic riêng:

```text
Value namespace
Type namespace
Trait namespace
Module namespace
Macro/comptime namespace
```

Ví dụ:

```text
struct Foo { ... }
fn Foo(...) { ... }
```

có thể hợp lệ nếu chúng thuộc namespace khác nhau và syntax context phân biệt.

Tuy nhiên không nên lạm dụng nhiều namespace làm ngôn ngữ khó hiểu.

---

# 13. Type namespace

Khi parser gặp:

```text
let x: Foo
```

resolver tìm:

```text
Type namespace
```

Khi gặp:

```text
Foo(...)
```

context có thể yêu cầu:

```text
Value / constructor / callable
```

Resolver phải có contextual lookup rõ ràng.

---

# 14. Local scope

Ví dụ:

```text
fn f(x: i32) {
    let y = 10

    {
        let z = 20
        ...
    }
}
```

Scope tree:

```text
FunctionScope
 ├── x
 ├── y
 └── BlockScope
      └── z
```

Local `z` không tồn tại ngoài block.

---

# 15. Shadowing

Axiom có thể cho phép:

```text
let x = 1
let x = 2
```

nhưng semantic là **new binding**, không mutation.

Ví dụ:

```text
let x = 1
let x = x + 1
```

right-hand `x` resolve về binding cũ.

Sau declaration:

```text
x
```

resolve về binding mới.

---

# 16. Shadowing và ownership

Nếu:

```text
let x = Buffer(...)
let x = transform(x)
```

thì:

```text
old x
→ moved into transform
→ old binding dead
→ new x
```

Resolver chỉ xác định identity; ownership verifier xử lý move state.

Không trộn hai subsystem.

---

# 17. Visibility

Core visibility:

```text
private
module
package
public
```

Khuyến nghị semantic:

### private

Chỉ declaration scope/module hiện tại.

### module

Module và child modules theo rule.

### package

Toàn package.

### public

Export ra package consumers.

---

# 18. `public` không đồng nghĩa binary export

Một function:

```text
public fn helper()
```

không nhất thiết xuất symbol machine-level.

Compiler có thể:

```text
inline
LTO
remove
internalize
```

nếu không cần binary ABI.

Binary export phải explicit:

```text
@export
public fn api()
```

---

# 19. `@export`

```text
@export
public fn create_engine(...)
```

nghĩa:

- symbol phải tồn tại trong artifact;
- ABI phải được xác định;
- name mang ABI identity;
- linker phải giữ symbol.

Nếu cần C ABI:

```text
@export
extern "C" fn ...
```

---

# 20. Visibility và generics

Một public generic:

```text
public fn make<T: Trait>(x: T) -> Box<T>
```

có dependency API:

```text
Trait
Box
T
```

Compiler phải kiểm tra tất cả public semantic dependencies.

Không được public function phụ thuộc một private type mà consumer không thể name/resolve nếu signature expose type đó.

---

# 21. Private type trong public signature

Ví dụ:

```text
private struct Internal

public fn get() -> Internal
```

→ compile error hoặc phải áp dụng opaque-type mechanism rõ ràng.

Không được tạo public API không thể biểu diễn.

---

# 22. Opaque types

Axiom có thể hỗ trợ:

```text
public fn create() -> impl Trait
```

nhưng đây là **opaque compile-time type**, không phải `dyn Trait`.

Consumer biết:

```text
type implements Trait
```

nhưng không biết concrete representation.

Static dispatch vẫn có thể được sử dụng trong module/package boundary tùy ABI model.

---

# 23. `dyn Trait` khác `impl Trait`

```text
impl Trait
```

→ static/opaque concrete type.

```text
dyn Trait
```

→ runtime dynamic dispatch.

Không được nhập nhằng hai cơ chế.

---

# 24. Re-export

Module:

```text
public use internal::Vec3
```

cho phép:

```text
library::Vec3
```

dù implementation thực tế nằm:

```text
library::internal::vector::Vec3
```

Re-export tạo API surface mapping.

Không duplicate type identity.

---

# 25. Type identity qua re-export

Nếu:

```text
a::Vec3
```

được re-export:

```text
b::Vec3
```

thì vẫn là:

```text
same DeclarationId
```

Không tạo hai type.

Điều này cực kỳ quan trọng cho trait coherence.

---

# 26. Prelude

Standard library có thể có prelude:

```text
import std::prelude::*
```

nhưng compiler không nên có một global hidden prelude.

Mọi implicit names phải được specification rõ ràng.

Khuyến nghị:

> Core chỉ implicit những primitive names thực sự cần thiết; Std prelude là library convention.

---

# 27. Built-in names

Các primitive:

```text
i32
u64
f32
bool
usize
never
```

có thể được compiler-known.

Nhưng chúng vẫn phải có stable semantic identity:

```text
PrimitiveTypeId
```

không phải magic string.

---

# 28. Import cycle

Cho phép module dependency cycle ở mức declaration nếu có thể:

```text
A → B
B → A
```

nhưng compiler phải phân biệt:

```text
Declaration cycle
Initialization cycle
Compile-time execution cycle
```

Không phải mọi cycle đều hợp lệ.

---

# 29. Declaration cycle

Ví dụ:

```text
A:
    fn f(x: B::Type)

B:
    struct Type
```

có thể resolve qua multi-phase declaration collection.

Do đó không nên compile module theo kiểu:

```text
parse A
compile A completely
then B
```

mà cần:

```text
Collect declarations
→ resolve module graph
→ typecheck
```

---

# 30. Initialization cycle

Runtime static initialization:

```text
A::x → B::y
B::y → A::x
```

là vấn đề khác.

Axiom không nên cho phép hidden dynamic initialization cycle.

Static data nên ưu tiên:

```text
compile-time constant initialization
```

hoặc explicit runtime initialization.

---

# 31. Compile-time module cycle

Comptime:

```text
comptime fn a() {
    b()
}

comptime fn b() {
    a()
}
```

phải được phát hiện như execution cycle/recursion.

Không được compiler treo.

---

# 32. Module initialization

Axiom tránh mô hình:

```text
global constructor
```

kiểu C++.

Static initialization phải phân loại:

```text
ConstantInit
ComptimeInit
RuntimeInit
```

RuntimeInit phải explicit và có lifecycle rõ ràng.

Điều này giúp:

- startup nhanh;
- freestanding;
- deterministic initialization;
- tránh initialization order fiasco.

---

# 33. Name resolution independence

Resolver không được phụ thuộc:

```text
optimization level
target CPU
link order
filesystem traversal order
hash-map iteration order
```

Nếu nhiều declaration cùng candidate:

```text
ambiguity
```

phải được xác định deterministic.

---

# 34. Import visibility

Import không tự động bypass visibility.

Ví dụ:

```text
private fn secret()
```

không thể:

```text
import other::secret
```

chỉ vì biết fully-qualified name.

Resolver phải kiểm tra visibility sau lookup.

---

# 35. Qualified access

Compiler phải phân biệt:

```text
Type::associated_function()
Trait::method()
Module::function()
Enum::Variant
```

và:

```text
value.method()
value.field
```

Đây là contextual resolution, không phải một parser ambiguity vô tổ chức.

---

# 36. Associated names

Ví dụ:

```text
<T as Iterator>::Item
<T as Factory>::create()
```

resolver chuyển thành:

```text
TraitId
TypeId
AssociatedItemId
```

sau trait solver mới resolve concrete item.

---

# 37. Generic names

```text
fn f<T>(x: T)
```

`T` có:

```text
GenericParamId
```

không phải DeclarationId của type toàn cục.

Nếu nested generic:

```text
fn f<T>() {
    fn g<U>(x: U) { ... }
}
```

resolver phải tạo lexical generic environment.

---

# 38. Namespace imports không tạo runtime state

Ví dụ:

```text
import math::sqrt
```

không tạo:

```text
runtime module object
```

Import chỉ là compile-time resolution.

---

# 39. Module initialization and dead code

Nếu module chỉ chứa:

```text
fn unused()
```

và không có runtime initialization:

compiler có thể loại toàn module code khỏi final binary.

Module boundary không phải binary retention boundary.

---

# 40. Package boundary

Package dependency:

```text
app
 ├── core
 ├── graphics
 └── math
```

Compiler resolve:

```text
PackageId
ModuleId
DeclarationId
```

theo hierarchy.

Package manager đã được định nghĩa ở các task trước; task này chỉ định nghĩa semantic name resolution.

---

# 41. `.axif` integration

Public declaration có thể được export thành:

```text
library.axif
```

Artifact chứa:

```text
public types
traits
functions
constants
ABI
repr
generic constraints
visibility
semantic fingerprints
```

Consumer không cần parse toàn source library.

---

# 42. Incremental resolution

CompilerDB cần cache:

```text
NameQuery
ImportQuery
ModuleQuery
VisibilityQuery
ExportQuery
ReExportQuery
```

Key dựa trên semantic revision.

Nếu thay đổi private implementation:

```text
public API unchanged
```

consumer không cần re-resolve toàn bộ package.

---

# 43. Rename safety

IDE/compiler biết:

```text
DeclarationId
```

nên rename:

```text
Vec3 → Vector3
```

có thể dựa trên semantic references thay vì text search.

Không rename nhầm:

```text
Vec3
```

trong comment/string/unrelated module.

---

# 44. Namespace collision diagnostics

Ví dụ:

```text
import a::foo
import b::foo

foo()
```

diagnostic:

```text
AMB001
ambiguous name `foo`

candidates:
    a::foo
    b::foo
```

và structured data:

```text
AmbiguousName {
    query: foo
    candidates: [DeclarationId(...), ...]
}
```

---

# 45. Resolver architecture

Pipeline:

```text
Source
 ↓
Parse
 ↓
Module Discovery
 ↓
Declaration Collection
 ↓
Scope Construction
 ↓
Import Graph
 ↓
Name Lookup
 ↓
Visibility Check
 ↓
Trait/Type/Overload Resolution
 ↓
DeclarationId binding
```

Quan trọng:

> **Declaration collection phải xảy ra trước full type checking.**

Điều này cho phép forward references và module cycles hợp lệ.

---

# 46. CompilerDB additions

```text
ModuleDB
NamespaceDB
ScopeDB
NameDB
NameResolutionDB
ImportDB
ReExportDB
VisibilityDB
ExportDB
PreludeDB
PrimitiveNameDB
ModuleGraphDB
InitializationDB
OpaqueTypeDB
PublicApiDB
SymbolIdentityDB
```

---

# 47. Resolver invariants

```text
ANAME-01
Every resolved source name maps to a stable semantic identity.

ANAME-02
Name resolution is deterministic.

ANAME-03
Declaration identity is distinct from textual name.

ANAME-04
Filesystem layout does not define semantic identity by itself.

ANAME-05
Imports are compile-time resolution mechanisms.

ANAME-06
Imports do not create runtime namespace objects.

ANAME-07
Visibility is checked after candidate discovery.

ANAME-08
Private declarations cannot be accessed through qualified naming.

ANAME-09
Ambiguous names are compile errors.

ANAME-10
Compiler must not resolve ambiguity through declaration/import order.

ANAME-11
Re-export does not duplicate declaration identity.

ANAME-12
Public API cannot expose inaccessible private types.

ANAME-13
Public visibility does not imply binary symbol export.

ANAME-14
Binary export requires explicit ABI/export semantics.

ANAME-15
Generic parameters have distinct semantic identities.

ANAME-16
Associated names are resolved through trait/type semantics.

ANAME-17
Module declaration collection precedes full type checking.

ANAME-18
Valid declaration cycles may be supported.

ANAME-19
Runtime initialization cycles are distinct from declaration cycles.

ANAME-20
Comptime execution cycles are detected.

ANAME-21
Implicit prelude contents must be explicitly specified.

ANAME-22
Primitive types have stable semantic identities.

ANAME-23
Name resolution does not depend on optimization level.

ANAME-24
Name resolution does not depend on target optimization decisions.

ANAME-25
Name resolution supports incremental compilation.

ANAME-26
Public API identity is represented independently from source paths.

ANAME-27
Opaque types preserve abstraction without implying dynamic dispatch.

ANAME-28
dyn Trait remains explicit dynamic polymorphism.

ANAME-29
Module boundaries do not force runtime boundaries.

ANAME-30
All semantic references entering later compiler stages use resolved IDs, not raw strings.
```

---

# 48. Definition of Done

`BOOTSTRAP-354` hoàn thành khi Axiom có:

- module tree;
- namespace model;
- declaration identity;
- lexical scopes;
- imports;
- aliases;
- re-exports;
- visibility;
- package visibility;
- public API checking;
- explicit binary export;
- opaque types;
- prelude model;
- primitive-name resolution;
- associated-name resolution;
- generic-name resolution;
- module cycles;
- initialization classification;
- comptime cycle detection;
- deterministic ambiguity handling;
- incremental name resolution;
- `.axif` integration;
- IDE semantic references;
- rename-safe declaration identity;
- structured resolver diagnostics;
- module/import conformance tests.

### Kết quả quan trọng

Sau task này, Axiom có chuỗi identity rất sạch:

```text
text
  ↓
Name
  ↓
DeclarationId
  ↓
TypeId / FunctionId / TraitId / ModuleId
  ↓
GenericInstanceId
  ↓
MIR entities
  ↓
Machine symbols
```

Không một compiler pass quan trọng nào cần tiếp tục “tìm kiếm bằng tên chuỗi”.

Đây là điều rất quan trọng cho mục tiêu **compiler lớn nhưng ngôn ngữ không phức tạp**, đồng thời là nền móng cho incremental compilation, IDE, `.axif`, package system và self-hosting.