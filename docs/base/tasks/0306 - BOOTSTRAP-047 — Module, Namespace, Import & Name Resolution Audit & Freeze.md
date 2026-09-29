Tiếp tục.

# BOOTSTRAP-047 — Module, Namespace, Import & Name Resolution Audit & Freeze

Phần này nối tiếp BOOTSTRAP-042 và BOOTSTRAP-046. Mục tiêu là làm cho Axiom có **namespace rõ ràng, import đơn giản, compiler deterministic**, đồng thời cực kỳ thuận lợi cho AI agent tra cứu API.

Nguyên tắc chính:

> **Tên dùng để đọc source; Symbol ID dùng để compiler.**

Không để tên source-level trở thành nguồn ambiguity trong compiler.

---

# 1. Module ≠ file

Một module là đơn vị semantic.

Filesystem chỉ là một cách tổ chức.

Ví dụ:

```text
src/
    math.ax
    vector.ax
```

không có nghĩa compiler bắt buộc:

```text
1 file = 1 module
```

Một module có thể được chia thành nhiều file.

---

# 2. Package → Module → Declaration

Cấu trúc semantic:

```text
Package
  └── Module
       ├── Struct
       ├── Enum
       ├── Trait
       ├── Function
       ├── Constant
       └── Submodule
```

---

# 3. Namespace

Mỗi module tạo namespace riêng.

Ví dụ:

```axiom
module math

struct Vec2 {}
fn length(v: view<Vec2>) -> f32 {}
```

Tên đầy đủ:

```text
math::Vec2
math::length
```

---

# 4. `::` cho semantic qualification

Tôi đề xuất:

```axiom
math::Vec2
math::length
```

thay vì dùng `.` cho namespace.

`.` giữ nghĩa:

```text
field access
method access
```

---

# 5. Module path

Ví dụ:

```axiom
import graphics::math::Vec2
```

hoặc:

```axiom
import graphics::math
```

Tùy import declaration.

---

# 6. Import không execute code

Đã freeze từ 042:

```text
import
```

chỉ là compile-time dependency/name-resolution operation.

Không có:

```text
import → runtime initialization
```

---

# 7. Import declaration

Đề xuất cú pháp:

```axiom
import math::Vec2
import math::length
```

---

# 8. Import module

Có thể:

```axiom
import math
```

nhưng **không nên tự động đưa toàn bộ symbol vào local namespace**.

Thay vào đó:

```axiom
math::Vec2
math::length(v)
```

---

# 9. Selective import

```axiom
import math::{Vec2, length}
```

sau đó:

```axiom
let v: Vec2
length(v)
```

---

# 10. Import alias

```axiom
import very::long::module as math
```

sau đó:

```axiom
math::Vec2
```

---

# 11. Symbol alias

Có thể:

```axiom
import math::Vec2 as Vector
```

---

# 12. Re-export

Module có thể:

```axiom
pub use math::Vec2
```

để expose API qua namespace khác.

Ví dụ:

```text
graphics::Vec2
```

có thể thực chất re-export:

```text
math::Vec2
```

---

# 13. Re-export không duplicate type identity

Rất quan trọng.

Nếu:

```text
math::Vec2
graphics::Vec2
```

và graphics re-export math::Vec2 thì chúng vẫn là:

> **cùng một type identity.**

Không tạo type mới.

---

# 14. Newtype mới type identity

Ngược lại:

```axiom
struct Vector2(math::Vec2)
```

là type mới.

---

# 15. `pub`

Core v1:

```text
private
pub
```

đủ.

```axiom
pub struct User {}
```

---

# 16. Private mặc định

Không ghi `pub`:

```axiom
struct Internal {}
```

→ private module/package boundary theo visibility rules.

---

# 17. Visibility ≠ export

Đã freeze:

```text
pub
```

không có nghĩa:

```text
native symbol exported
```

Muốn native symbol:

```axiom
@export("axiom_create_user")
pub fn create_user(...)
```

---

# 18. Symbol identity

Compiler không nên định danh declaration chỉ bằng:

```text
name
```

Mà bằng semantic identity:

```text
PackageId
ModuleId
DeclarationId
```

---

# 19. Generic symbol identity

Generic:

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

là một generic declaration.

Instantiation:

```text
max<i32>
max<f64>
```

là các specialization khác nhau trong compiler IR.

---

# 20. Overloading

Axiom nên **hạn chế overload theo tên**.

Không nên cho:

```axiom
foo(i32)
foo(f32)
foo(String)
foo(Vec)
foo(...)
```

tràn lan.

Điều này đặc biệt quan trọng cho AI-generated code.

---

# 21. Function identity

Khuyến nghị:

> Một namespace không cho phép hai function cùng tên nếu không có một overload mechanism rõ ràng.

Core v1 có thể cho overload có kiểm soát dựa trên signature, nhưng không dựa trên implicit conversion.

---

# 22. Tôi nghiêng về overload có kiểm soát

Ví dụ:

```axiom
fn abs(x: i32) -> i32
fn abs(x: f32) -> f32
```

hợp lệ.

Compiler chọn dựa trên **exact type compatibility**.

---

# 23. Không conversion chain

Nếu:

```text
foo(i64)
```

và caller:

```text
u8
```

không được thử:

```text
u8 → i16 → i32 → i64
```

để tìm overload.

---

# 24. Numeric widening

Nếu sau này cho implicit widening, nó phải là một rule duy nhất, không phải chain tùy tiện.

Nhưng baseline hiện tại vẫn:

> numeric conversion explicit.

---

# 25. Name lookup phases

Compiler name resolution nên theo thứ tự:

```text
1. Local bindings
2. Parameters
3. Inherent/type namespace
4. Explicit imports
5. Module-local declarations
6. Prelude
```

Nhưng type namespace và value namespace cần phân biệt.

---

# 26. Separate namespaces

Axiom nên có ít nhất:

```text
Type namespace
Value namespace
Module namespace
```

Ví dụ:

```axiom
struct Foo {}
fn Foo() {}
```

có thể tồn tại mà không nhất thiết conflict nếu chúng thuộc namespace khác.

Tuy nhiên **không nên lạm dụng điều này trong source syntax**.

---

# 27. Trait namespace

Trait methods không được đưa toàn bộ vào global namespace.

```text
Trait::method
```

chỉ tham gia method resolution khi trait implementation phù hợp.

---

# 28. Extension namespace

Extension functions cũng không tự động global.

Chúng chỉ tham gia resolution nếu module chứa extension được import.

Điều này đã được freeze ở 046.

---

# 29. Ambiguity

Nếu:

```axiom
import A::foo
import B::foo
```

và gọi:

```axiom
foo(x)
```

→ compile error.

Không chọn dựa trên:

- import order;
- file order;
- package load order.

---

# 30. Explicit qualification

Giải quyết:

```axiom
A::foo(x)
B::foo(x)
```

---

# 31. Wildcard import

Tôi đề xuất **không có wildcard import trong Core v1**:

```axiom
import A::*
```

Lý do:

- namespace pollution;
- khó đọc;
- AI khó xác định origin;
- refactoring khó;
- ambiguity tăng.

---

# 32. Prelude

Một prelude nhỏ có thể implicit.

Ví dụ:

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
Eq
Iterator
```

---

# 33. Prelude phải machine-readable

Compiler metadata phải trả lời:

```text
symbol
fully qualified name
package
module
source location
visibility
type
generic parameters
trait bounds
attributes
```

---

# 34. Đây là điểm rất quan trọng cho AI

AI agent không cần đọc:

```text
10.000 file source
```

để biết API.

Compiler có thể tạo:

```text
axiom-api.meta
```

chứa semantic interface.

---

# 35. API metadata

Conceptually:

```json
{
  "symbol": "graphics::Vec2::length",
  "kind": "function",
  "receiver": "view<graphics::Vec2>",
  "returns": "f32",
  "visibility": "pub"
}
```

Đây chỉ là ví dụ format; **JSON không cần là format cuối cùng**.

Compiler nên dùng binary semantic metadata nhanh hơn.

---

# 36. Metadata không thay source semantics

Metadata là artifact compiler-generated.

Source vẫn là authority.

---

# 37. Public interface fingerprint

Mỗi module có semantic fingerprint dựa trên:

```text
public declarations
public types
public traits
public signatures
ABI contracts
comptime dependencies
relevant attributes
```

---

# 38. Private implementation không invalidate downstream

Nếu sửa:

```text
private fn helper()
```

mà public semantic interface không đổi:

→ downstream module không cần recompile.

---

# 39. Generic dependency

Nếu public function:

```axiom
pub fn sort<T: Ord>(...)
```

thì metadata phải chứa:

```text
T
Ord
associated requirements
```

để downstream resolve mà không đọc implementation.

---

# 40. Trait metadata

Metadata cần mô tả:

```text
trait name
associated types
associated constants
associated functions
required methods
default methods
supertrait constraints
object-safety information
```

---

# 41. Struct metadata

Public struct cần expose semantic fields nếu fields public.

Ví dụ:

```axiom
pub struct Point {
    pub x: f32
    y: f32
}
```

metadata phải biết:

```text
x → public
y → private
```

---

# 42. Layout metadata

Default layout không ổn định.

Không đưa physical offsets vào API metadata như một ABI guarantee.

Nếu:

```axiom
@repr(C)
```

thì metadata phải chứa representation contract.

---

# 43. Symbol names vs mangling

Internal Axiom symbol có thể mangled:

```text
_ZN...
```

nhưng source semantic identity vẫn:

```text
package::module::foo
```

---

# 44. Generic mangling

Compiler-generated symbol:

```text
foo<i32>
foo<f64>
```

có thể có khác nhau trong object file.

Không expose mangling format như stable ABI.

---

# 45. Stable ABI

Stable Axiom ABI sẽ cần versioning riêng.

Baseline:

> **C ABI ổn định trước; Axiom ABI có thể versioned về sau.**

Đã thống nhất ở FFI.

---

# 46. Module initialization

Axiom không nên có implicit:

```text
global constructor magic
```

nếu muốn runtime initialization thì phải explicit semantics.

Điều này giúp:

- freestanding;
- deterministic startup;
- linker đơn giản;
- binary nhỏ.

---

# 47. Static initialization

Compile-time constants:

```axiom
const PI: f64 = ...
```

không cần runtime initializer.

---

# 48. Runtime global state

Nếu cần mutable static:

```axiom
static var counter: Atomic<i64>
```

thì initialization phải obey static initialization rules.

Không tự động chạy arbitrary function trước `main`.

---

# 49. Circular imports

Module A:

```text
A → B
```

Module B:

```text
B → A
```

không nhất thiết luôn invalid.

Name/type dependency có thể hỗ trợ cycles nếu compiler có declaration phase.

---

# 50. Package cycles

Package dependency cycles:

```text
A → B → A
```

vẫn reject mặc định theo BOOTSTRAP-042.

---

# 51. Module cycles

Module cycle có thể cho phép nếu chỉ là declaration references.

Nhưng initialization/runtime dependency cycle không được implicit tồn tại.

---

# 52. Two-phase module resolution

Compiler:

```text
Phase 1:
collect declarations

Phase 2:
resolve bodies
```

Điều này cho phép:

```axiom
fn a() -> i32 { b() }
fn b() -> i32 { a() }
```

mà không phụ thuộc source order.

---

# 53. Source order

Source order không quyết định symbol visibility trong cùng module.

Trừ những construct explicitly ordered nếu sau này có.

---

# 54. Local bindings vẫn lexical

Ví dụ:

```axiom
{
    let x = 1
    {
        let x = 2
    }
}
```

inner `x` shadows outer `x`.

---

# 55. Shadowing

Tôi đề xuất cho phép shadowing local.

Nhưng compiler warning có thể báo nếu dễ gây lỗi.

---

# 56. Parameter shadowing

Không nên cho parameter bị redeclare cùng scope:

```axiom
fn foo(x: i32) {
    let x = ...
}
```

Có thể compiler error hoặc warning mạnh.

Để AI-generated code dễ phân tích, tôi nghiêng về **error trong cùng lexical scope**.

---

# 57. Pattern bindings

Pattern có thể tạo nhiều local names:

```axiom
match result {
    Ok(value) => ...
    Err(error) => ...
}
```

Resolver tạo binding IDs riêng.

---

# 58. Name resolution ≠ type inference

Resolver trước:

```text
name → DeclarationId
```

sau đó type checker:

```text
DeclarationId → Type
```

Không trộn hai hệ thống.

---

# 59. Trait resolution sau type resolution

Pipeline:

```text
Parse
 ↓
Name Resolution
 ↓
Type Resolution
 ↓
Trait Resolution
 ↓
Ownership/Capability
```

không để trait solver tự làm tất cả.

---

# 60. Method resolution

Theo 046:

```text
Inherent
→ Trait
→ Explicit Extension
→ Generic Extension
```

---

# 61. Import không thay đổi type identity

Import alias:

```axiom
import A::User as Person
```

không biến:

```text
A::User
```

thành type mới.

---

# 62. Re-export không phá orphan rule

Nếu package B re-export type của package A:

```text
B::User
```

thì B **không trở thành owner của type**.

---

# 63. Package ownership

Trait/type ownership dựa trên declaration origin, không dựa trên import path.

---

# 64. Versioned packages

Nếu:

```text
foo@1
foo@2
```

cùng tồn tại:

```text
foo@1::User
foo@2::User
```

là distinct nominal types.

Không implicit conversion.

---

# 65. Alias across versions

Không được alias để đánh lừa compiler thành cùng type.

Adapter/conversion phải explicit.

---

# 66. Build configuration

`@cfg` có thể làm declaration tồn tại/không tồn tại.

Name resolver chạy trên **configuration-selected source graph**.

---

# 67. Dead declarations

Compiler có thể loại bỏ unused private declarations.

Public declarations cần giữ theo artifact/export semantics.

---

# 68. Symbol reachability

Compiler/linker có thể:

```text
dead-code elimination
tree shaking
section GC
```

nhưng không xóa symbol observable qua:

```text
@export
dynamic symbol lookup
FFI
reflection metadata
```

---

# 69. Dynamic symbol lookup

Nếu chương trình dùng:

```text
Symbol::lookup("foo")
```

compiler không thể mặc định biết `"foo"` tương ứng declaration nào.

Explicit export/retention contract cần thiết.

---

# 70. Reflection

Compile-time reflection có thể enumerate:

```text
module.types()
module.functions()
type.fields()
type.methods()
```

nhưng chỉ những declaration mà visibility/metadata policy cho phép.

---

# 71. Runtime reflection

Không tự động.

Nếu muốn:

```text
runtime TypeInfo
```

phải explicit emit metadata.

---

# 72. AI semantic query

Đây là phần tôi muốn đưa thành một feature tooling chính thức:

```text
axiom query symbol graphics::Vec2
axiom query trait Iterator
axiom query implementations Trait
axiom query callers foo
axiom query type User
```

Đây **không phải language syntax**.

Là compiler/tooling protocol.

---

# 73. Machine-readable output

CLI hỗ trợ:

```text
--format=text
--format=json
--format=machine
```

hoặc một semantic protocol riêng.

AI agent có thể lấy:

```text
declaration
signature
constraints
docs
source location
dependencies
```

mà không phải parse text compiler output.

---

# 74. Diagnostics dùng DeclarationId

Diagnostic nội bộ:

```text
PackageId
ModuleId
DeclarationId
SpanId
TypeId
```

sau đó renderer chuyển thành source-level message.

---

# 75. IDE integration

Compiler server có thể cung cấp:

```text
go-to-definition
find-references
rename
type-at-position
trait-implementations
method-candidates
documentation
```

Không cần IDE tự xây một type checker khác.

---

# 76. Single semantic engine

Đây là nguyên tắc quan trọng:

```text
CLI
IDE
AI Agent
Build System
Debugger
```

đều nên sử dụng **cùng compiler semantic database**.

Không duplicate language semantics.

---

# 77. Incremental resolver

Declaration graph có fingerprint.

Nếu module không đổi:

```text
parse/resolution result
```

có thể lấy từ cache.

---

# 78. Determinism

Name resolution phải deterministic bất kể:

- filesystem enumeration order;
- parallel compilation order;
- thread scheduling;
- cache hit/miss.

---

# 79. Diagnostics stable IDs

Ví dụ:

```text
ENAME-001
ETYPE-...
ETRAIT-...
EMETHOD-...
EIMPORT-...
```

AI có thể xử lý error theo code thay vì đoán từ text.

---

# 80. Final namespace architecture

Axiom sẽ có:

```text
Package
  ↓
Module
  ↓
Namespace
  ├── Types
  ├── Values
  ├── Traits
  ├── Functions
  └── Submodules
```

và:

```text
Import
  ↓
Name Resolution
  ↓
DeclarationId
  ↓
Type Resolution
  ↓
Trait Resolution
```

---

# 81. Cú pháp đề xuất

Một module điển hình:

```axiom
module graphics::math

pub struct Vec2 {
    pub x: f32
    pub y: f32
}

pub fn length(v: view<Vec2>) -> f32 {
    sqrt(v.x * v.x + v.y * v.y)
}

pub trait Normalize {
    fn normalize(self: view<Self>) -> Self
}

impl Normalize for Vec2 {
    fn normalize(self: view<Vec2>) -> Vec2 {
        ...
    }
}
```

Module khác:

```axiom
import graphics::math::{Vec2, length, Normalize}

fn test(v: Vec2) {
    let n = v.normalize()
    let l = length(n)
}
```

Rất gần với mô hình bạn muốn:

> **struct + function**, sau đó trait bổ sung abstraction khi thực sự cần.

---

# BOOTSTRAP-047 — Invariants

```text
ANAME-20   Module is a semantic namespace unit.
ANAME-21   Filesystem layout is not module identity.
ANAME-22   Package, module, and declaration identities are distinct.
ANAME-23   Module namespaces are explicitly qualified.
ANAME-24   :: is the namespace qualification operator.
ANAME-25   . is reserved for member/field/method access semantics.
ANAME-26   Import is compile-time name-resolution dependency.
ANAME-27   Import does not imply runtime execution.
ANAME-28   Module import does not automatically inject all names into local scope.
ANAME-29   Selective imports may introduce explicitly named declarations.
ANAME-30   Import aliases do not create new type identities.
ANAME-31   Re-exports do not create new declaration identities.
ANAME-32   Newtypes create distinct nominal type identities.
ANAME-33   Visibility is distinct from native symbol export.
ANAME-34   pub does not imply @export.
ANAME-35   Native export requires an explicit export contract.
ANAME-36   Declaration identity is independent of source spelling.
ANAME-37   Generic declarations are distinct from their specializations.
ANAME-38   Generic specialization does not change source-level declaration identity.
ANAME-39   Overload resolution is compile-time.
ANAME-40   Overload resolution is deterministic.
ANAME-41   Implicit conversion chains cannot resolve overloads.
ANAME-42   Ambiguous imported names are compile-time errors.
ANAME-43   Explicit qualification resolves namespace ambiguity.
ANAME-44   Wildcard imports are not part of Core v1.
ANAME-45   Prelude is small and explicitly defined.
ANAME-46   Trait methods do not pollute the global value namespace.
ANAME-47   Extension methods require explicit import visibility.
ANAME-48   Extension methods cannot silently replace inherent methods.
ANAME-49   Trait resolution occurs after type/name resolution.
ANAME-50   Name resolution maps source names to DeclarationId.
ANAME-51   Type checking operates on resolved declarations.
ANAME-52   Trait solving is separate from lexical name resolution.
ANAME-53   Module declaration collection is independent of source order.
ANAME-54   Function bodies may refer to declarations defined later.
ANAME-55   Package dependency cycles are rejected by default.
ANAME-56   Declaration-only module cycles may be supported.
ANAME-57   Runtime initialization cycles are not implicit language behavior.
ANAME-58   Local shadowing is lexical and deterministic.
ANAME-59   Pattern bindings receive unique compiler identities.
ANAME-60   Public API metadata is compiler-generated semantic information.
ANAME-61   Public interface fingerprints support incremental compilation.
ANAME-62   Private implementation changes need not invalidate downstream code when public semantics are unchanged.
ANAME-63   Generic public APIs expose their constraints in interface metadata.
ANAME-64   Trait metadata exposes required and provided behavior.
ANAME-65   Representation metadata is exposed only when representation contracts exist.
ANAME-66   Default layout is not exposed as a stable ABI contract.
ANAME-67   Package version identity participates in nominal type identity.
ANAME-68   Re-export does not transfer type/trait ownership.
ANAME-69   Orphan/coherence rules use declaration origin.
ANAME-70   Compiler-generated symbols may use unstable mangling.
ANAME-71   Stable ABI symbol names require explicit export contracts.
ANAME-72   Dead-code elimination cannot remove semantically observable exports.
ANAME-73   Dynamic symbol lookup requires explicit retention/export semantics.
ANAME-74   Compile-time reflection uses resolved semantic declarations.
ANAME-75   Runtime reflection requires explicit metadata emission.
ANAME-76   Name resolution is deterministic across parallel and incremental compilation.
ANAME-77   Diagnostics identify semantic declarations independently of rendered text.
ANAME-78   Compiler diagnostics have stable machine-readable error identifiers.
ANAME-79   CLI, IDE, build tools, and AI tooling should share the compiler semantic engine.
ANAME-80   AI tooling may query semantic API metadata without parsing the entire source tree.
ANAME-81   Semantic query tooling does not alter language semantics.
ANAME-82   Import aliases do not affect ownership, trait, or ABI semantics.
ANAME-83   Configuration-selected declarations are resolved after configuration selection.
ANAME-84   Unused private declarations may be eliminated.
ANAME-85   Observable declarations remain reachable according to their explicit contracts.
ANAME-86   Module initialization is not an implicit arbitrary runtime execution mechanism.
ANAME-87   Compile-time constants do not require runtime initialization.
ANAME-88   Static runtime state requires explicit storage semantics.
ANAME-89   Source ordering does not determine declaration identity.
ANAME-90   Namespace resolution must remain predictable for both humans and AI agents.
```

---

## Một quyết định tôi cho rằng rất đáng giữ

Axiom đang hình thành một kiến trúc khá nhất quán:

```text
              STRUCT
                │
                │ data
                ▼
            FUNCTION
                │
                │ behavior
                ▼
              TRAIT
                │
        ┌───────┴────────┐
        │                │
   static generic     dyn Trait
        │                │
   compile-time       runtime
```

Trong khi namespace:

```text
Package
  ↓
Module
  ↓
Declaration
  ↓
DeclarationId
```

và compiler:

```text
Source
 ↓
Name Resolution
 ↓
Type Resolution
 ↓
Trait Resolution
 ↓
Ownership/Capability
 ↓
MIR
```

Điểm hay là **AI không cần hiểu “class hierarchy”** để sinh code Axiom. Nó chỉ cần hỏi:

> Type này có những function nào?  
> Trait nào được implement?  
> Function nào nhận `view<T>` / `mut_view<T>` / `T`?  
> Có extension nào đang import?  
> Có overload nào?  

Đó là một mô hình khá tự nhiên cho AI.

---

# BOOTSTRAP-048 — tiếp theo

Phần tiếp theo tôi sẽ chuyển sang **Standard Library + Runtime Architecture**.

Đây là phần đặc biệt quan trọng với mục tiêu ban đầu của bạn:

> **Không phụ thuộc third-party compiler/library, binary nhỏ, không runtime bắt buộc.**

Ta sẽ thiết kế cách Axiom có:

```text
axiom.core
axiom.mem
axiom.io
axiom.os
axiom.fs
axiom.net
axiom.thread
axiom.async
axiom.gpu
axiom.text
axiom.collections
axiom.math
```

nhưng chương trình chỉ link đúng thứ nó sử dụng, và **một chương trình Axiom tối giản có thể chạy mà gần như không có runtime**.