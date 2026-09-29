# Part XXII — Modules · Packages · Workspace · API Boundary

Phần này cần giải quyết một việc tưởng đơn giản nhưng ảnh hưởng rất sâu đến compiler:

> **Axiom phải phân biệt rõ “code nằm ở đâu”, “tên được nhìn thấy ở đâu”, “package nào sở hữu type”, và “API nào thực sự ổn định”.**

Tôi cũng chốt luôn điểm còn treo từ trước:

> **Axiom v0.1 chỉ dùng `import`. Không cần `use` như một cơ chế thứ hai.**

`pub use` sẽ được thay bằng cơ chế re-export của `import`, để tránh hai hệ thống namespace gần giống nhau.

---

# XXII.1. Bốn khái niệm khác nhau

Axiom có:

```text
Module
Package
Artifact
Workspace
```

Không được trộn chúng.

```text
Workspace
 ├── Package A
 │    ├── Module X
 │    └── Module Y
 │
 └── Package B
      └── Module Z
```

### Module

Namespace semantic.

### Package

Đơn vị phân phối/biên dịch dependency.

### Artifact

Output:

```text
.exe
.dll
.so
.a
.o
.elf
.wasm
```

### Workspace

Nhóm nhiều package cùng phát triển.

---

# XXII.2. Module Không Đồng Nhất Với File

Đây là quyết định quan trọng.

Không nên:

```text
1 file = 1 module
```

là semantic rule.

MVP có thể ánh xạ:

```text
math/vector.ax
→ module math.vector
```

nhưng compiler semantic model chỉ quan tâm:

```text
module math.vector
```

File chỉ là source container.

Điều này cho phép sau này:

- generated source;
- multiple files;
- IDE virtual files;
- embedded source;
- package archives.

mà không phải thay đổi language semantics.

---

# XXII.3. Module Declaration

Syntax:

```axiom
module math.vector
```

Ví dụ:

```axiom
module math.vector

pub struct Vec2 {
    pub x: f32
    pub y: f32
}
```

Tên module là semantic identity.

---

# XXII.4. Module Identity

Module identity:

```text
PackageIdentity
+
ModulePath
```

Ví dụ:

```text
mathlib@2.1.0
math.vector
```

Không chỉ:

```text
math.vector
```

vì nhiều package có thể có module cùng tên.

---

# XXII.5. Import

Axiom v0.1:

```axiom
import math.vector
```

hoặc:

```axiom
import math.vector { Vec2, dot }
```

hoặc alias:

```axiom
import graphics.opengl as gl
```

---

# XXII.6. Không Có `use`

Tôi khuyên bỏ:

```axiom
use foo
```

khỏi Core.

Lý do:

`import` đã đủ để biểu diễn:

- dependency;
- name introduction;
- selected import;
- alias;
- re-export.

Một keyword thứ hai dễ làm người dùng phải nhớ:

```text
import khác use ở điểm nào?
```

Trong khi compiler cũng phải duy trì hai semantic concepts.

Axiom hướng tới:

> **One Semantic Question, One Mechanism.**

---

# XXII.7. Import Không Phải Copy Code

```axiom
import math.vector
```

không có nghĩa compiler paste source vào file hiện tại.

Nó tạo:

```text
name resolution edge
+
dependency edge
```

AST/HIR của module vẫn độc lập.

---

# XXII.8. Selected Import

```axiom
import math.vector { Vec2, dot }
```

Sau đó:

```axiom
let p = Vec2 { x: 1.0, y: 2.0 }
let d = dot(...)
```

Chỉ các symbol được chọn được đưa vào local namespace.

---

# XXII.9. Module Qualification

Không import symbol trực tiếp:

```axiom
import math.vector

let p = math.vector.Vec2 {
    x: 1.0,
    y: 2.0
}
```

Điều này rất hữu ích cho AI-generated code vì namespace vẫn rõ ràng.

---

# XXII.10. Alias

```axiom
import graphics.opengl as gl
```

sau đó:

```axiom
gl.create_buffer()
```

Alias chỉ thay đổi name resolution.

Nó không tạo type identity mới.

---

# XXII.11. Import Alias Symbol

Có thể:

```axiom
import math.vector { Vec2 as Vector2 }
```

Sau đó:

```axiom
let p: Vector2 = ...
```

`Vector2` vẫn là cùng type:

```text
Vector2 == math.vector.Vec2
```

---

# XXII.12. Re-export

Axiom cần re-export.

Ví dụ:

```axiom
module graphics

import graphics.opengl { Buffer }
pub import graphics.opengl { Buffer }
```

Nhưng syntax này hơi dư thừa.

Tôi đề xuất một form duy nhất:

```axiom
import graphics.opengl { pub Buffer }
```

Tuy nhiên syntax này làm import declaration mang cả visibility semantics.

Một phương án sạch hơn:

```axiom
pub import graphics.opengl { Buffer }
```

Tôi chọn phương án này cho v0.1.

Ví dụ:

```axiom
pub import math.vector { Vec2, Vec3 }
```

Package bên ngoài có thể:

```axiom
import math { Vec2 }
```

---

# XXII.13. Re-export Không Tạo Type Mới

```text
package A
    math.Vec2

package B
    pub import A.math { Vec2 }

package C
    import B { Vec2 }
```

Tất cả đều là:

```text
A.math.Vec2
```

Không phải:

```text
B.Vec2
```

type mới.

---

# XXII.14. Visibility

Axiom chỉ cần ba mức:

```text
private
internal
pub
```

### private

Chỉ module hiện tại.

### internal

Mọi module trong package.

### pub

Public package API.

Default:

```text
private
```

---

# XXII.15. Không Có `protected`

Không có:

```text
protected
friend
package-private
```

Lý do:

- không có class inheritance;
- trait đã giải quyết behavioral abstraction;
- `internal` đã đủ cho package-level implementation.

---

# XXII.16. Public Struct, Private Fields

Hoàn toàn hợp lệ:

```axiom
pub struct User {
    id: u64
    pub name: Text
}
```

Code bên ngoài:

```axiom
let u = User { ... }
```

không nhất thiết được phép set `id`.

Constructor có thể là:

```axiom
pub fn User.create(...) -> User
```

---

# XXII.17. Constructor Không Phải Language Primitive

Axiom không có:

```text
new
```

đặc biệt.

Constructor chỉ là function:

```axiom
pub fn create_user(id: u64) -> User {
    ...
}
```

hoặc associated function:

```axiom
impl User {
    pub fn create(id: u64) -> User {
        ...
    }
}
```

Điều này giữ struct/function model nhất quán.

---

# XXII.18. Public API Leakage

Không được:

```axiom
pub fn create() -> PrivateType
```

nếu caller không thể name/access `PrivateType`.

Compiler:

```text
AX_API_0001
public declaration exposes inaccessible type
```

Tương tự với:

- private trait;
- private associated type;
- private generic constraint.

---

# XXII.19. Generic Public API

Ví dụ:

```axiom
pub fn process<T: InternalTrait>(x: T) -> T
```

nếu `InternalTrait` private thì API không hợp lệ.

Compiler phải yêu cầu mọi semantic constraint cần thiết cho public API đều reachable.

---

# XXII.20. `impl Trait` và Public API

Có thể:

```axiom
pub fn make_iterator() -> impl Iterator<Item = User> {
    ...
}
```

Concrete type có thể private.

Public API chỉ expose:

```text
impl Iterator
```

Đây là một abstraction boundary hợp lệ.

---

# XXII.21. `dyn Trait`

Tương tự:

```axiom
pub fn make_renderer() -> Box<dyn Renderer>
```

Dynamic representation là public contract.

Concrete implementation có thể private.

---

# XXII.22. Visibility Không Đồng Nghĩa Linker Export

Rất quan trọng:

```text
pub
```

không có nghĩa:

```text
export symbol from executable/shared library
```

Ví dụ:

```axiom
pub fn foo() {}
```

có thể bị:

- inline;
- dead-strip;
- internalize;
- rename;
- eliminate.

Nếu muốn linker symbol:

```axiom
@export("foo")
extern "C" fn foo(...) { ... }
```

---

# XXII.23. API Boundary và ABI Boundary

Hai thứ hoàn toàn khác:

```text
API
ABI
```

API:

```text
type/function/trait semantics
```

ABI:

```text
calling convention
layout
symbol
alignment
register/stack convention
```

Một public API có thể không có stable ABI.

---

# XXII.24. Semantic API Fingerprint

Compiler cần tạo:

```text
Semantic API Fingerprint
```

bao gồm:

```text
public types
public functions
public constants
public traits
public impls
generic constraints
associated types
visibility
re-export graph
relevant attributes
```

Ví dụ:

```text
Package A v1
API fingerprint:
    93c8...
```

Nếu implementation private thay đổi:

```text
API fingerprint unchanged
```

→ dependent package có thể không cần semantic recompilation.

---

# XXII.25. Public Trait Impl Là API

Ví dụ:

```axiom
impl Display for User { ... }
```

Nếu `Display` là public trait thì implementation có thể thay đổi method resolution.

Do đó public impl phải nằm trong API fingerprint.

Đây là lý do:

> Trait implementation is part of semantic API.

---

# XXII.26. ABI Fingerprint

Tách riêng:

```text
Semantic API Fingerprint
ABI Fingerprint
```

ABI fingerprint bao gồm:

```text
@repr(C)
extern "C"
@export
calling convention
field layout
alignment
symbol names
ABI-visible generic instantiations
```

Một thay đổi semantic có thể không đổi ABI.

Một thay đổi ABI có thể không thay đổi high-level semantics.

---

# XXII.27. Package Identity

Package identity không chỉ là tên.

Conceptual:

```text
PackageIdentity =
    name
    version
    source
    content_hash
```

Ví dụ:

```text
math
2.1.0
registry://...
sha256:...
```

---

# XXII.28. Hai Version Cùng Tồn Tại

Package A có thể cần:

```text
math@1.x
```

Package B cần:

```text
math@2.x
```

Workspace có thể chứa cả:

```text
math@1
math@2
```

Type identity phải phân biệt:

```text
math@1::Vec2
math@2::Vec2
```

dù tên giống nhau.

Không implicit convert.

---

# XXII.29. Dependency Graph

Package graph phải là DAG:

```text
A
├── B
│   └── C
└── D
```

Không:

```text
A → B → A
```

ở package level.

Module graph bên trong package có thể có declaration dependency cycle nếu semantic model cho phép.

---

# XXII.30. Module Cycle

Ví dụ:

```text
module A
    imports B

module B
    imports A
```

Không nên cấm tuyệt đối.

Compiler có thể xử lý:

```text
declaration collection
→ name resolution
→ type resolution
→ body checking
```

theo SCC.

Tuy nhiên initialization cycle của runtime static không được tạo implicit.

---

# XXII.31. Không Có Hidden Module Initialization

Axiom không có:

```text
module constructor
global constructor magic
```

Ví dụ import module:

```axiom
import graphics
```

không được tự động chạy:

```text
graphics.init()
```

Điều này rất quan trọng cho:

- binary size;
- startup time;
- deterministic initialization;
- freestanding.

Nếu cần:

```axiom
graphics.init()?
```

phải gọi explicit.

---

# XXII.32. Static Initialization

`static` phải được initialize theo rule rõ ràng:

### Compile-time constant

```axiom
static MAX: usize = 1024
```

### Explicit runtime initialization

Phải qua API rõ ràng, không hidden constructor.

Không được có:

```text
C++ global object constructor model
```

trong Core.

---

# XXII.33. Package Resource Ownership

Package import không có nghĩa package "own" runtime resource.

Dependency graph là compile-time/build-time concept.

Runtime ownership chỉ tồn tại khi program tạo:

```text
File
Socket
Buffer
Thread
Device
...
```

---

# XXII.34. Package Feature

Package có thể có:

```text
features
```

nhưng:

> Feature không được thay đổi semantics của Axiom language.

Feature có thể chọn:

```text
backend
optional dependency
module
capability
implementation
```

nhưng không được biến:

```text
feature=foo
```

thành:

```text
`+` suddenly means something else
```

---

# XXII.35. Conditional Compilation

Axiom có thể dùng:

```axiom
@cfg(target = "windows")
```

hoặc:

```axiom
@cfg(feature = "gpu")
```

`@cfg` là semantic attribute.

Không cần preprocessor.

Ví dụ:

```axiom
@cfg(target = "windows")
fn platform_name() -> Text {
    "Windows"
}
```

---

# XXII.36. `@cfg` Không Tạo Một Language

Compiler parse syntax trước khi evaluate configuration.

Điều này tránh preprocessor-style:

```text
#if
    malformed syntax
#endif
```

Axiom parser vẫn biết structure.

---

# XXII.37. Conditional Declaration

Nếu declaration bị loại:

```text
@cfg(target = "linux")
fn foo()
```

thì symbol không tồn tại trong semantic environment của target khác.

Reference:

```axiom
foo()
```

→ normal unresolved symbol error.

---

# XXII.38. Package Target Matrix

Package có thể khai báo target support:

```text
windows-x86_64
linux-x86_64
linux-aarch64
macos-aarch64
android-aarch64
wasm32
```

Nhưng compiler target là authority cuối cùng.

Package metadata không thể ép compiler giả vờ một API tồn tại.

---

# XXII.39. Cross Compilation

Cross compile:

```text
host ≠ target
```

không được làm thay đổi semantic source.

Ví dụ:

```text
host = Windows
target = Linux
```

Comptime phải phân biệt:

```text
host information
target information
```

Không được lấy host CPU rồi giả định đó là target CPU.

---

# XXII.40. `usize` và Target

`usize` phụ thuộc target pointer width.

Ví dụ:

```text
x86-64 → 64 bit
aarch64 → 64 bit
wasm32 → 32 bit
```

`u64` luôn 64-bit.

Do đó API portable nên tránh dùng `usize` cho dữ liệu wire/serialization nếu width cố định được yêu cầu.

---

# XXII.41. Package-level Prelude

Axiom có thể có prelude nhỏ:

```text
bool
Option
Result
Array
view
...
```

Nhưng prelude phải:

- deterministic;
- nhỏ;
- versioned;
- không chứa random library imports.

Không wildcard import toàn bộ std.

---

# XXII.42. Wildcard Import

V0.1:

```axiom
import foo.*
```

**không hỗ trợ.**

Lý do:

- namespace pollution;
- ambiguous names;
- AI-generated code khó phân tích;
- API fingerprint khó truy vết;
- refactoring khó.

Explicit import tốt hơn:

```axiom
import foo { A, B, C }
```

---

# XXII.43. Ambiguous Import

Ví dụ:

```axiom
import a { User }
import b { User }

let x: User
```

→ compile error.

Compiler không tự chọn "import gần nhất".

Có thể giải quyết:

```axiom
import a as a
import b as b

let x: a.User
```

---

# XXII.44. Import Shadowing

Không nên cho import âm thầm shadow local symbol.

Ví dụ:

```axiom
import math { max }

fn f(max: i32) {
    ...
}
```

Local declaration có thể hợp lệ nếu language rule quy định lexical shadowing, nhưng compiler nên diagnostic cảnh báo khi import bị che khuất.

Không được để:

```text
import order
```

quyết định semantics một cách mơ hồ.

---

# XXII.45. Name Resolution Order

Chốt deterministic order:

```text
1. local bindings
2. parameters
3. current module declarations
4. explicit imports
5. package/public re-exports
6. prelude
```

Nếu nhiều candidate cùng priority:

```text
AMBIGUOUS
```

Không dùng heuristic.

---

# XXII.46. Extension Method và Module

Ví dụ:

```axiom
module math.vec

fn length(self: view<Vec2>) -> f32 { ... }
```

Module khác:

```axiom
import math.vec { length }

v.length()
```

Extension method chỉ được xem xét nếu symbol đã được import.

Không có global extension-method namespace vô hạn.

---

# XXII.47. Package Namespace Không Là Runtime Namespace

Package/module identity tồn tại ở compiler.

Runtime symbol có thể:

```text
mangled
inlined
removed
merged
```

Không được suy luận:

```text
module foo
```

→ runtime namespace `foo`.

Nếu muốn stable runtime symbol:

```axiom
@export("foo_bar")
```

---

# XXII.48. Private Type Identity

Private type vẫn có semantic identity.

Ví dụ:

```axiom
struct InternalId(u64)
```

không phải alias `u64`.

Nó vẫn là type distinct.

Compiler không được flatten semantic identity chỉ vì type private.

Nhưng có thể optimize representation.

---

# XXII.49. Newtype qua Package Boundary

```axiom
pub struct UserId(u64)
```

là type mới.

Code ngoài package không được implicit:

```axiom
let x: u64 = user_id
```

Phải có explicit conversion/accessor.

Điều này bảo vệ abstraction boundary.

---

# XXII.50. Package API và Generic Monomorphization

Nếu package public:

```axiom
pub fn sort<T: Ord>(...)
```

compiler có thể monomorphize ở consumer.

Nhưng package interface phải expose đủ semantic information:

```text
signature
trait constraints
associated types
relevant representation
```

Không cần expose private implementation.

---

# XXII.51. Package ABI

Package static library:

```text
libfoo.a
```

không nhất thiết có stable ABI.

Nếu muốn consumer khác compiler/version:

```text
extern "C"
@repr(C)
@export
```

hoặc một Axiom ABI version explicit.

---

# XXII.52. Axiom Native ABI

Native:

```text
extern "axiom"
```

có thể tồn tại conceptual, nhưng:

> Không stable across compiler versions trừ khi ABI version được freeze.

Điều này cho phép compiler freedom cực lớn.

---

# XXII.53. Package Versioning

Version semantics nên dùng:

```text
major.minor.patch
```

nhưng compiler không tự quyết định semantic compatibility chỉ bằng số version.

Có tools:

```text
axiom api-check
axiom abi-check
```

để phân tích actual change.

---

# XXII.54. API Compatibility

Có thể phân loại:

```text
source compatible
semantic compatible
ABI compatible
```

Ví dụ thêm private function:

```text
API: unchanged
ABI: unchanged
```

Đổi public function parameter:

```text
API: breaking
```

Đổi `@repr(C)` field:

```text
ABI: potentially breaking
```

---

# XXII.55. Workspace

Workspace:

```text
workspace/
    axiom.toml
    packages/
        app/
        math/
        graphics/
```

Workspace không phải một package khổng lồ.

Mỗi package có identity riêng.

---

# XXII.56. Workspace Dependency

Package trong workspace có thể:

```text
app → math
app → graphics
```

nhưng compiler vẫn coi chúng như package riêng.

Điều này cho phép:

- incremental build;
- independent API fingerprint;
- independent versioning;
- independent artifact.

---

# XXII.57. Package Graph và Build Graph

Phân biệt:

```text
Package Graph
```

và:

```text
Build Graph
```

Package graph:

```text
A depends on B
```

Build graph có thể chứa:

```text
comptime generator
shader compiler
resource compiler
generated source
object files
link step
```

Do đó build graph phong phú hơn package graph.

---

# XXII.58. Dependency Source

Package dependency có thể đến từ:

```text
registry
git
local path
archive
vendor
workspace
```

Package identity phải hash source content khi cần reproducibility.

---

# XXII.59. Lock File

`axiom.lock` freeze:

```text
package
version
source
content hash
dependency resolution
```

Build reproducible có thể dùng lock file.

---

# XXII.60. Offline Build

Nếu dependency đã vendor/cache:

```text
axiom build --offline
```

phải không cần network.

Comptime network capability nếu dependency yêu cầu thì build phải báo rõ.

Không silently fallback network.

---

# XXII.61. Package Security Boundary

Import package không cho package đó:

```text
filesystem access
network access
process execution
```

ở runtime hay comptime ngoài capability contract.

Package dependency ≠ trust of arbitrary host access.

---

# XXII.62. Normative Invariants

### Module

**AMOD-20 — Module Is A Semantic Namespace**

**AMOD-21 — File Is Not The Fundamental Module Identity**

**AMOD-22 — Module Identity Includes Package Identity**

**AMOD-23 — Import Creates Semantic Dependency/Name Resolution Edges**

**AMOD-24 — Import Does Not Textually Include Source**

**AMOD-25 — Name Resolution Is Deterministic**

**AMOD-26 — Ambiguous Names Are Errors**

**AMOD-27 — Wildcard Imports Are Not Core v0.1**

**AMOD-28 — Imported Names Cannot Implicitly Change Type Identity**

### Visibility

**AVIS-20 — Private Is The Default Visibility**

**AVIS-21 — Internal Is Package-Visible**

**AVIS-22 — Pub Is Public Package API**

**AVIS-23 — Visibility Does Not Imply Linker Export**

**AVIS-24 — Public APIs Cannot Expose Inaccessible Types**

**AVIS-25 — Public Generic Constraints Must Be Reachable**

### Re-export

**AMOD-29 — Re-export Does Not Create A New Type**

**AMOD-30 — Re-export Preserves Original Semantic Identity**

**AMOD-31 — Re-export Is Explicit**

### Package

**APKG-20 — Package Is A Distribution/Compilation Unit**

**APKG-21 — Workspace Is Not A Package**

**APKG-22 — Artifact Is Distinct From Package**

**APKG-23 — Package Identity Includes Versioned Source Identity**

**APKG-24 — Package Graph Is A DAG**

**APKG-25 — Multiple Package Versions May Coexist**

**APKG-26 — Package Versions Have Distinct Type Identity**

**APKG-27 — Dependency Resolution Is Deterministic**

**APKG-28 — Lock State Can Freeze Dependency Resolution**

**APKG-29 — Offline Builds Must Not Require Hidden Network Access**

### API

**AAPI-20 — Semantic API Fingerprint Is Distinct From ABI Fingerprint**

**AAPI-21 — Public Trait Implementations Affect Semantic API Identity**

**AAPI-22 — Private Implementation Changes Need Not Change API Identity**

**AAPI-23 — API Compatibility Is Not Automatically ABI Compatibility**

**AAPI-24 — ABI Compatibility Is Explicitly Checkable**

**AAPI-25 — Public `impl Trait` May Hide Private Concrete Types**

**AAPI-26 — Public `dyn Trait` Exposes Dynamic Representation Semantics**

### Initialization

**AMOD-32 — Import Has No Implicit Runtime Initialization**

**AMOD-33 — Hidden Module Constructors Are Not Core Semantics**

**AMOD-34 — Static Initialization Is Explicitly Defined**

### Configuration

**ACFG-20 — Conditional Compilation Is Semantic**

**ACFG-21 — Configuration Does Not Introduce A Preprocessor Language**

**ACFG-22 — Disabled Declarations Do Not Exist In The Target Semantic Environment**

**ACFG-23 — Features Cannot Change Core Language Semantics**

**ACFG-24 — Host And Target Configuration Are Distinct**

### Workspace/build

**APKG-30 — Workspace Members Retain Independent Package Identity**

**APKG-31 — Package Graph Is Distinct From Build Graph**

**APKG-32 — Build Graph May Contain Generated Artifacts**

**APKG-33 — Dependency Source Identity Is Reproducible**

**APKG-34 — Package Dependency Does Not Imply Host Capability**

**APKG-35 — Package Resolution Is Independent From Runtime Ownership**

**APKG-36 — Build Features Cannot Change Core Language Semantics**

**APKG-37 — Public API Fingerprints Include Relevant Re-exports**

**APKG-38 — Public Generic Constraints Are Part Of API Identity**

**APKG-39 — Cross Compilation Is Host-Independent At The Semantic Level**

**APKG-40 — Package Identity Is Distinct From Runtime Symbol Identity**

---

# XXII.63. Syntax cuối cùng

Sau khi chốt phần này, module syntax v0.1 có thể được coi là:

```axiom
module math.vector

pub import math.scalar { Scalar }

pub struct Vec2 {
    pub x: f32
    pub y: f32
}

pub fn dot(a: view<Vec2>, b: view<Vec2>) -> f32 {
    a.x * b.x + a.y * b.y
}
```

Consumer:

```axiom
module app

import math.vector { Vec2, dot }

fn main() {
    let a = Vec2 { x: 1.0, y: 2.0 }
    let b = Vec2 { x: 3.0, y: 4.0 }

    print(dot(view(a), view(b)))
}
```

Không cần:

```text
use
namespace
class package
friend
protected
wildcard import
preprocessor
```

---

# XXII.64. Một quyết định kiến trúc rất đáng giữ

Axiom hiện có một đường biên rất sạch:

```text
Source
  │
  ├── module / package
  │
  ├── type / trait / function
  │
  ├── ownership / capability
  │
  ├── comptime
  │
  └── runtime
```

và mỗi cơ chế có **một trách nhiệm**.

Đây chính là thứ sẽ giúp Axiom đạt mục tiêu ban đầu của bạn: **ngôn ngữ có thể mạnh hơn C ở abstraction level nhưng không biến thành một hệ thống hàng chục cơ chế chồng chéo mà programmer phải nhớ.**

---

## Tiếp theo — Part XXIII: Build System · Package Resolution · Reproducible Build · Incremental Compilation

Phần XXII đã chốt **semantic package/module model**. Part XXIII sẽ đi xuống build system thực tế:

```text
axiom.toml
axiom.lock
dependency resolver
registry
vendor
SIF
incremental compilation
semantic API fingerprint
ABI fingerprint
comptime build
generated artifacts
cross compilation
profiles
LTO
static/dynamic linking
reproducible build
offline build
cache
```

Đặc biệt sẽ thiết kế sao cho **Axiom cuối cùng có thể tự build compiler của chính nó mà không cần Cargo/CMake/MSBuild/LLVM**, nhưng vẫn có giai đoạn bootstrap thực tế để xây compiler từ con số 0.