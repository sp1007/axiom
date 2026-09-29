Tiếp tục.

# Axiom — Module, Namespace, Visibility & API Boundary v0.1

Đây là phần cần đóng băng vì nó liên kết trực tiếp:

```text
package
  ↓
module
  ↓
symbol
  ↓
visibility
  ↓
public API
  ↓
semantic interface
  ↓
incremental compilation
  ↓
ABI / package compatibility
```

Mục tiêu:

> **Module phải đơn giản với lập trình viên nhưng đủ chính xác để compiler, linker, package manager và AI tooling cùng hiểu một khái niệm duy nhất về API.**

---

# 1. Package ≠ Module ≠ File

Ba khái niệm phải tách biệt.

```text
Package
    = đơn vị phân phối/dependency

Module
    = namespace + semantic compilation unit

File
    = physical source container
```

Ví dụ:

```text
my_app/
├── axiom.toml
└── src/
    ├── main.axiom
    ├── math.axiom
    └── network/
        ├── http.axiom
        └── socket.axiom
```

Có thể tương ứng:

```text
package: my_app

modules:
    my_app
    my_app::math
    my_app::network::http
    my_app::network::socket
```

Nhưng **file không nhất thiết phải là module**.

---

# 2. Module là semantic namespace

Một module:

```text
my_app::math
```

có:

```text
symbols
imports
exports
visibility
semantic interface
```

Compiler làm việc với module này, không làm việc dựa trên đường dẫn file.

---

# 3. Module identity

Module identity:

```text
PackageIdentity
+
ModulePath
```

Ví dụ:

```text
my_app@1.2.0::math
```

Nhưng package version chưa đủ để xác định package hoàn toàn.

Ta đã chốt:

```text
PackageIdentity =
    name
    version
    source
    content_hash
```

Do đó semantic identity có thể là:

```text
PackageId::ModulePath::SymbolId
```

---

# 4. File mapping

Ta có thể cho phép:

```axiom
module math
```

trong file.

Hoặc convention:

```text
src/math.axiom
```

tự đại diện cho:

```text
my_app::math
```

Tôi khuyến nghị **cả hai**, nhưng compiler semantic identity không phụ thuộc tên file.

---

# 5. Một module có thể nhiều file

Đây là một khả năng hữu ích:

```text
network/
    http.axiom
    http_headers.axiom
    http_client.axiom
```

cùng thuộc:

```text
network::http
```

nếu manifest/module declaration xác định như vậy.

Điều này đặc biệt hữu ích cho module lớn.

---

# 6. Nhưng đừng để file fragment tự do

Không nên có cơ chế kiểu:

```text
#include "foo"
```

rồi text được ghép vào nhau.

Compiler vẫn thấy:

```text
Module
 ├── Declaration
 ├── Declaration
 └── Declaration
```

chứ không phải một file text khổng lồ.

---

# 7. Import

Syntax đề xuất:

```axiom
import std::math
```

Hoặc:

```axiom
import std::math::sin
```

---

# 8. Import module

```axiom
import std::collections
```

cho phép truy cập:

```axiom
collections::Vec
```

nếu symbol public.

---

# 9. Import symbol

```axiom
import std::collections::Vec
```

sau đó:

```axiom
let x = Vec<i32>.new()
```

---

# 10. Alias

```axiom
import std::collections::Vec as Vector
```

Không thay đổi semantic identity.

Chỉ tạo local name:

```text
Vector
    ↓
std::collections::Vec
```

---

# 11. Import nhiều symbol

Có thể hỗ trợ:

```axiom
import std::math::{sin, cos, sqrt}
```

nhưng đây chỉ là syntax sugar.

Semantic model vẫn là:

```text
ImportEdge
    source module
    selected symbols
    local aliases
```

---

# 12. Wildcard import

Tôi **không khuyến nghị**:

```axiom
import std::math::*
```

trong Core syntax.

Lý do:

- namespace pollution;
- ambiguity;
- API khó đọc;
- refactoring khó;
- AI khó xác định symbol đến từ đâu.

Nếu muốn, có thể cho trong prelude đặc biệt:

```text
prelude
```

---

# 13. Prelude

Axiom nên có một prelude rất nhỏ.

Ví dụ:

```text
bool
i32
u64
Option
Result
Some
None
Ok
Err
```

Nhưng không nên đưa cả:

```text
Vec
HashMap
File
Socket
Thread
```

vào namespace mặc định.

---

# 14. Explicit import là mặc định

Ví dụ:

```axiom
import std::collections::Vec
import std::io::File
```

làm dependency rõ ràng.

Điều này rất tốt cho:

- compiler;
- IDE;
- AI;
- code review;
- dependency analysis.

---

# 15. Visibility

Tôi đề xuất ban đầu chỉ cần:

```text
private
pub
```

Không cần:

```text
public
protected
internal
friend
package-private
```

ở Core v0.1.

---

# 16. Private mặc định

```axiom
fn helper() { ... }

pub fn run() { ... }
```

`helper` private.

`run` public.

---

# 17. Visibility theo module

Private nghĩa là:

> chỉ module khai báo và semantic descendants được phép truy cập.

Tôi đề xuất **không dùng class-style protected**.

---

# 18. Nested module

Ví dụ:

```text
app
├── parser
│   ├── lexer
│   └── ast
└── compiler
```

`app::parser::lexer` là descendant của:

```text
app::parser
```

Nhưng có một vấn đề.

Có nên cho `parser::lexer` truy cập private của `parser`?

Tôi đề xuất:

> **Không mặc định.**

Private là lexical/module ownership, không phải toàn bộ subtree.

---

# 19. Vì sao?

Nếu module:

```text
foo
```

có private:

```text
secret
```

thì việc tạo:

```text
foo::internal::something
```

không nên tự động có quyền truy cập `secret`.

Nếu cần chia sẻ, dùng explicit visibility.

---

# 20. `pub`

```axiom
pub struct User {
    pub id: u64
    name: Text
}
```

Ở đây:

```text
User
```

public.

Nhưng:

```text
name
```

private.

---

# 21. Private fields của public struct

Đây là cực kỳ quan trọng.

```axiom
pub struct File {
    handle: RawHandle
}
```

Người dùng có thể:

```axiom
let f = File.open(...)?
```

nhưng không thể:

```axiom
File { handle: ... }
```

nếu field private.

---

# 22. Struct literal và API encapsulation

Compiler phải kiểm tra toàn bộ field visibility.

Điều này cho phép:

```text
public type
+
private representation
```

mà không cần class.

---

# 23. Constructor không phải ngôn ngữ primitive

Ví dụ:

```axiom
pub fn File.open(path: Text) -> Result<File, Error>
```

chỉ là ordinary function/method.

Không cần:

```text
constructor
destructor
```

đặc biệt.

---

# 24. Public type nhưng private Drop details

Một type:

```axiom
pub struct File { ... }
```

có thể:

```text
Drop
```

private implementation.

User chỉ cần biết:

```text
File: !Copy
File: Drop
```

---

# 25. Trait visibility

Ví dụ:

```axiom
pub trait Serialize {
    fn serialize(self: view<Self>) -> Bytes
}
```

Trait public.

Implementation:

```axiom
impl Serialize for User { ... }
```

có thể private.

---

# 26. Nhưng public generic API cần public constraints

Ví dụ:

```axiom
pub fn sort<T: Ord>(x: mut_view<Vec<T>>) { ... }
```

`Ord` phải accessible tại API boundary.

Không thể public function phụ thuộc trait private.

---

# 27. Public API closure

Nếu:

```axiom
pub fn foo() -> impl Trait
```

trait phải public nếu client cần name/semantics của trait.

Nhưng concrete hidden type có thể private.

Đây là một trường hợp cần API normalization.

---

# 28. `impl Trait`

Ví dụ:

```axiom
pub fn make_iterator() -> impl Iterator<Item = i32>
```

Public API không expose concrete iterator type.

Compiler ghi vào semantic interface:

```text
return:
    opaque implementation of Iterator<Item=i32>
```

---

# 29. `dyn Trait`

```axiom
pub fn process(x: dyn Processor)
```

Trait phải public.

Concrete implementations không cần public.

---

# 30. Associated types

Nếu:

```axiom
pub trait Iterator {
    type Item
}
```

thì associated type là một phần public semantic contract.

---

# 31. Public generic body

Đây liên quan trực tiếp monomorphization.

Ví dụ:

```axiom
pub fn max<T: Ord>(a: T, b: T) -> T {
    ...
}
```

Package client có thể cần body/semantic representation để instantiate.

Do đó package artifact phải chứa:

```text
public generic semantic body
```

không chỉ machine code.

---

# 32. Nhưng không cần expose source

Artifact có thể chứa:

```text
Typed HIR / serialized generic IR
```

thay vì source text.

Điều này hỗ trợ:

- compiler optimization;
- privacy;
- incremental compilation;
- reproducibility.

---

# 33. Semantic Interface

Ta đã có SIF.

Tôi đề xuất module artifact chứa:

```text
Semantic Interface
├── public symbols
├── public types
├── public traits
├── generic signatures
├── associated types
├── constants
├── attributes
├── ABI contracts
└── semantic fingerprints
```

---

# 34. SIF

Semantic Interface Fingerprint phải phụ thuộc vào:

```text
public API
+
semantic behavior relevant to clients
```

không phụ thuộc:

```text
private implementation
```

trừ khi implementation được inline/specialize và vì vậy có semantic compilation dependency.

---

# 35. Ví dụ

Thay:

```axiom
fn private_helper() { ... }
```

không làm thay đổi SIF.

Nhưng thay:

```axiom
pub fn add(a: i32, b: i32) -> i32
```

thành:

```axiom
pub fn add(a: i64, b: i64) -> i64
```

→ SIF thay đổi.

---

# 36. Inline generic

Nếu:

```axiom
@inline
pub fn foo<T>(...)
```

client có thể phụ thuộc implementation.

Do đó compiler cần fingerprint riêng:

```text
API fingerprint
Implementation fingerprint
```

---

# 37. Đây là cách incremental compilation chính xác

Ví dụ:

```text
Module A
 ├── API fingerprint
 └── implementation fingerprint

Module B imports A
```

Nếu chỉ private implementation của A đổi:

```text
A API = unchanged
```

B không cần semantic re-typecheck.

Nếu generic implementation ảnh hưởng specialization:

```text
generic body fingerprint changed
```

B có thể cần re-specialize.

---

# 38. Re-export

Ví dụ:

```axiom
pub import math::Vec
```

Module hiện tại expose:

```text
current::Vec
```

nhưng semantic identity vẫn là:

```text
math::Vec
```

---

# 39. Re-export không tạo type mới

Đây là invariant.

```text
A::Vec
```

và:

```text
B::Vec
```

nếu B re-export A::Vec:

```text
same type identity
```

---

# 40. Type alias

```axiom
type UserId = u64
```

là alias.

Do đó:

```text
UserId == u64
```

về type identity.

---

# 41. Newtype

```axiom
struct UserId(u64)
```

là type khác.

```text
UserId != u64
```

nhưng có thể có:

```text
@repr(transparent)
```

nếu cần ABI compatibility.

---

# 42. Module cycles

Ta đã chốt:

> module cycles có thể tồn tại nếu declaration dependencies hợp lệ.

Ví dụ:

```text
A → B
B → A
```

không nhất thiết lỗi.

---

# 43. Nhưng value initialization cycle phải bị kiểm soát

Ví dụ:

```text
A static x depends on B::y
B static y depends on A::x
```

không được âm thầm tạo runtime initialization cycle.

Tốt nhất:

> **static initializer mặc định phải compile-time evaluable.**

Runtime lazy cycle là trách nhiệm library.

---

# 44. Recursive type

Module cycle:

```text
Node → Graph
Graph → Node
```

có thể hợp lệ.

Nhưng:

```axiom
struct Node {
    next: Node
}
```

không.

Phải:

```axiom
struct Node {
    next: Box<Node>
}
```

hoặc handle.

---

# 45. Import cycle không đồng nghĩa runtime dependency cycle

Đây là lý do module dependency nên phân loại:

```text
declaration dependency
type dependency
implementation dependency
runtime initialization dependency
```

Axiom chỉ cho phép những loại hợp lệ.

---

# 46. Package cycle

Package graph đã chốt:

> **package graph là DAG.**

Do đó:

```text
A → B
B → A
```

là lỗi resolver.

Module bên trong một package có thể cycle theo semantic rules.

---

# 47. Vì sao package không cycle?

Nếu package dependency cycle được phép:

```text
resolver
build order
version selection
```

trở nên phức tạp không cần thiết.

Module đã đủ linh hoạt cho mutual declarations.

---

# 48. Package facade

Package có thể chỉ expose:

```text
my_lib
```

và bên trong:

```text
internal
parser
codec
platform
```

Public API chỉ từ facade module.

---

# 49. `internal`

Tôi **không muốn thêm `internal` vào Core**.

Thay vào đó:

```text
private
pub
```

và package facade kiểm soát re-export.

Nếu một symbol không re-export:

```text
package user
```

không thấy nó.

---

# 50. Nhưng package nội bộ cần dùng chung giữa modules

Ví dụ:

```text
parser
codec
```

cần dùng:

```text
internal::Buffer
```

Có hai hướng.

### Hướng A

Đặt chúng cùng module parent và dùng private semantics.

### Hướng B

Có `pub(package)`.

Tôi nghiêng về **B**, nhưng không cần mở rộng visibility system quá sớm.

---

# 51. `pub(package)`

Có thể có:

```axiom
pub(package) struct InternalBuffer { ... }
```

nghĩa:

> accessible inside current package, not outside.

Đây hữu ích hơn `internal`.

---

# 52. `pub(module)`

Không cần nếu private đã mặc định và module decomposition được thiết kế tốt.

Nếu sau này cần, có thể thêm.

---

# 53. Visibility hierarchy

Tôi đề xuất v0.1:

```text
private
pub(package)
pub
```

Trong đó:

```text
private
    current module only

pub(package)
    current package

pub
    package consumers
```

Đây là đủ.

---

# 54. Friend

Không có:

```text
friend class
friend function
```

Nếu hai module cần chia sẻ implementation:

```text
pub(package)
```

hoặc refactor module boundary.

---

# 55. Namespace pollution

Không có global namespace.

Mọi declaration thuộc module:

```text
module::symbol
```

Ngay cả:

```text
main
```

thực chất có semantic identity:

```text
package::root::main
```

---

# 56. Entry point không phải public API

`main` là entry symbol/compiler convention.

Không cần:

```axiom
pub fn main()
```

để export API.

Compiler biết:

```text
@entry
```

hoặc hosted convention.

---

# 57. Linker symbol khác public symbol

Ví dụ:

```axiom
pub fn foo()
```

không nhất thiết tạo ELF/PE exported symbol.

Nó chỉ public ở language/package level.

Muốn linker export:

```axiom
@export("foo")
extern "C"
fn foo()
```

như đã chốt.

---

# 58. Đây là phân tầng rất quan trọng

```text
Language visibility
        ≠
Package visibility
        ≠
Compiler visibility
        ≠
Linker visibility
        ≠
OS dynamic export
```

Không được trộn.

---

# 59. API surface extraction

Compiler có thể:

```text
axiom api
```

trả:

```text
pub types
pub functions
pub traits
pub constants
pub modules
pub attributes
ABI exports
```

Đây là source cho:

- documentation;
- API compatibility;
- package registry;
- IDE;
- AI agent.

---

# 60. API stability

Không phải mọi public API đều ABI-stable.

Ví dụ:

```axiom
pub struct Foo { ... }
```

không có:

```text
stable binary layout
```

nếu không `repr(C)`.

Public source API:

```text
stable semantic interface
```

nhưng native ABI có thể thay đổi giữa compiler versions.

---

# 61. Public struct evolution

Nếu:

```axiom
pub struct User {
    pub id: u64
}
```

sau đó thêm:

```axiom
pub name: Text
```

vẫn có thể tương thích source theo một số cách.

Nhưng nếu external code dùng struct literal:

```axiom
User { id: 1 }
```

thì việc thêm required field có thể phá compilation.

Compiler API checker phải hiểu constructor/field initialization semantics.

---

# 62. Vì vậy struct literal public cần policy

Tôi đề xuất:

> **Public structs không mặc định cam kết layout hoặc construction compatibility.**

Nếu package muốn stable construction API:

```axiom
pub fn User.new(id: u64) -> User
```

Consumer dùng function.

---

# 63. `@non_exhaustive`

Đây là một attribute đáng có.

```axiom
@non_exhaustive
pub enum Error {
    Io,
    Parse
}
```

Consumer không được assume enum sẽ không có variant mới.

Điều này đặc biệt hữu ích cho library evolution.

---

# 64. Struct non-exhaustive

Tương tự:

```axiom
@non_exhaustive
pub struct Config { ... }
```

consumer không nên destructure exhaustively.

---

# 65. Pattern matching API boundary

Nếu public enum không `@non_exhaustive`:

```axiom
match error {
    Error::Io => ...
    Error::Parse => ...
}
```

compiler có thể coi exhaustive.

Nếu `@non_exhaustive`:

```text
future variants possible
```

consumer cần wildcard.

---

# 66. Visibility + traits

Một trait private không được leak ra public API.

Ví dụ:

```axiom
trait Internal {}
pub fn foo<T: Internal>(x: T) {}
```

không hợp lệ.

Compiler:

```text
AX_API_0001:
public item depends on private trait
```

---

# 67. Private type leak

Tương tự:

```axiom
struct InternalType {}

pub fn foo() -> InternalType
```

không hợp lệ nếu external code không thể name/use type.

Trừ trường hợp opaque type semantics như `impl Trait`.

---

# 68. Opaque return type

```axiom
pub fn make() -> impl Iterator<Item = i32>
```

được phép vì public contract chỉ cần:

```text
Iterator<Item=i32>
```

Concrete type identity compiler giữ private.

---

# 69. Public closure type

Không nên expose anonymous closure type name.

```axiom
pub fn callback() -> impl Fn(i32) -> i32
```

là một dạng opaque return.

---

# 70. Public generic constraints

API normalization phải tính:

```text
type bounds
associated types
where clauses
const generic constraints
effects nếu sau này exposed
```

Tất cả phải resolve được từ public dependency graph.

---

# 71. API graph

Compiler xây:

```text
Public API
    ↓
type dependencies
    ↓
trait dependencies
    ↓
associated type dependencies
    ↓
ABI dependencies
```

Nếu dependency đi vào private implementation mà không leak:

```text
OK
```

Nếu leak:

```text
ERROR
```

---

# 72. Đây chính là chỗ SIF rất mạnh

Semantic Interface Fingerprint có thể được xây từ **normalized public API graph** thay vì raw source.

Ví dụ:

```text
fn foo(x: i32) -> i32
```

hai source khác formatting:

```text
fn foo(x:i32)->i32
```

có cùng SIF.

---

# 73. SIF không phụ thuộc compiler optimization

Nếu compiler thay:

```text
foo
```

từ:

```text
call bar
```

thành:

```text
inline arithmetic
```

SIF không đổi nếu public semantic contract không đổi.

---

# 74. API diff

Ví dụ:

```text
axiom api-diff old.axapi new.axapi
```

có thể báo:

```text
Added:
    pub fn foo()

Removed:
    pub fn bar()

Changed:
    Baz::value: i32 → i64

Trait:
    + Ord requirement

ABI:
    unchanged
```

Không đánh giá “breaking” một cách mơ hồ; compiler phân loại theo compatibility rules.

---

# 75. API categories

Có thể phân loại:

```text
SOURCE_COMPATIBLE
SOURCE_BREAKING
ABI_COMPATIBLE
ABI_BREAKING
SEMANTIC_CHANGED
DOCUMENTATION_ONLY
```

Một thay đổi có thể:

```text
source compatible
ABI breaking
```

nếu `repr(C)` thay đổi.

---

# 76. Module invariants

Đóng băng:

```text
AMOD-13  Package Identity Is Distinct From Module Identity
AMOD-14  Module Is A Semantic Namespace
AMOD-15  File Is Not The Semantic Module Identity
AMOD-16  Imports Are Semantic Dependencies
AMOD-17  Explicit Imports Are Preferred
AMOD-18  Private Is The Default Visibility
AMOD-19  pub Exposes A Language-Level API
AMOD-20  pub(package) Exposes Package-Internal API
AMOD-21  No Friend Mechanism Is Required
AMOD-22  Re-export Does Not Create A New Type Identity
AMOD-23  Type Alias Does Not Create A New Type
AMOD-24  Newtype Creates A Distinct Type
AMOD-25  Linker Export Is Separate From Language Visibility
AMOD-26  Public API Cannot Leak Inaccessible Semantic Types
AMOD-27  Opaque Types May Hide Concrete Implementations
AMOD-28  Generic Public APIs Expose Their Required Semantic Constraints
AMOD-29  Module Cycles Are Allowed Only Under Semantic Rules
AMOD-30  Package Dependency Graph Remains A DAG
AMOD-31  No Hidden Runtime Module Initialization
AMOD-32  Public API Has A Normalized Semantic Representation
AMOD-33  SIF Is Derived From Semantic Interface
AMOD-34  Private Implementation Changes Need Not Invalidate Consumers
AMOD-35  Generic Implementation Changes May Invalidate Specialization
AMOD-36  Language Visibility Does Not Imply ABI Stability
AMOD-37  ABI Stability Requires Explicit ABI Contract
AMOD-38  API Diff Is Semantic
AMOD-39  @non_exhaustive Can Preserve Future Evolution
AMOD-40  Main/Entry Is Not Ordinary Public API
```

---

# 77. Kiến trúc module cuối cùng

Ta có:

```text
                    Package
                       │
             ┌─────────┴─────────┐
             │                   │
         Public API          Private API
             │                   │
          pub /                private
       pub(package)              │
             │                   │
             └─────────┬─────────┘
                       ↓
                 Semantic Graph
                       ↓
                 SIF / API IR
                       ↓
                Incremental Build
```

Và song song:

```text
pub
 │
 ├── language API
 │
 ├── documentation
 │
 ├── IDE
 │
 ├── package compatibility
 │
 └── AI semantic interface

@export
 │
 └── linker/ABI symbol
```

Hai đường này **không được nhập làm một**.

---

# 78. Một nguyên tắc tôi muốn khóa lại

### Public không có nghĩa “compiler phải giữ nguyên implementation”.

Ví dụ:

```axiom
pub fn distance(a: Vec2, b: Vec2) -> f32
```

Compiler hoàn toàn có thể biến nó thành:

```text
inline
SIMD
constant-fold
register-only
```

Public API chỉ mô tả **observable semantic contract**.

Đây chính là cách Axiom đạt:

> **high-level source + low-level performance.**

---

## Tiếp tục

Phần tiếp theo tôi sẽ đi vào một lớp rất quan trọng còn chưa được đóng băng hoàn toàn:

# **ABI Stability, FFI ABI, Versioning & Binary Compatibility**

Ta cần giải quyết cụ thể:

```text
Axiom ABI
C ABI
system ABI
stable ABI
plugin ABI
dynamic library ABI
generic ABI
repr(C)
repr(transparent)
opaque types
symbol versioning
struct evolution
enum evolution
calling convention evolution
compiler-version compatibility
```

và đặc biệt trả lời câu hỏi:

> **Axiom có nên có một “stable Axiom ABI” hay cố tình không có, để compiler được tự do tối ưu tối đa?**

Đây là quyết định ảnh hưởng trực tiếp tới khả năng xây **plugin system, dynamic library, hot reload và binary distribution**.