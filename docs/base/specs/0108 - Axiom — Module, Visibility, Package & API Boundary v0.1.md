Tiếp tục. Tôi sẽ đi thẳng vào phần **Module & Visibility Semantics**, vì đây là mảnh còn thiếu trước khi đóng băng syntax toàn ngôn ngữ.

# Axiom — Module, Visibility, Package & API Boundary v0.1

Mục tiêu:

> **Module là semantic namespace; file chỉ là cách tổ chức source. Package là đơn vị phân phối; ABI là một boundary khác hoàn toàn.**

Axiom không nên để `file`, `module`, `package`, `library`, `binary` nhập nhằng với nhau.

---

## 1. Bốn tầng phải tách biệt

```text
Package
  │
  ├── Module
  │     ├── Type
  │     ├── Function
  │     ├── Trait
  │     └── Constant
  │
  └── Artifact
         ├── static library
         ├── dynamic library
         └── executable
```

Và bên ngoài:

```text
Source visibility
        ≠
Package API
        ≠
Linker symbol visibility
        ≠
ABI visibility
```

Đây là nguyên tắc cần đóng băng.

---

# 2. Module không đồng nghĩa file

Không nên có quy tắc:

```text
1 file = 1 module
```

Ví dụ package:

```text
myapp/
├── axiom.toml
└── src/
    ├── main.ax
    ├── math/
    │   ├── vector.ax
    │   └── matrix.ax
    └── graphics/
        ├── renderer.ax
        └── texture.ax
```

Có thể semantic module là:

```text
myapp
├── math
│   ├── vector
│   └── matrix
└── graphics
    ├── renderer
    └── texture
```

File chỉ là source container.

---

# 3. Một module có thể nằm trên nhiều file

Điều này hữu ích cho project lớn.

Ví dụ:

```text
math/
├── vector.ax
├── matrix.ax
└── scalar.ax
```

đều có thể đóng góp vào:

```text
math
```

nhưng tôi **không muốn `partial module` syntax**.

Compiler/build system có thể assemble source units thành module.

Programmer không cần:

```text
partial module math
```

---

# 4. Nhưng v0.1 nên đơn giản hơn

Để compiler MVP dễ triển khai, tôi đề xuất:

> **Mỗi source unit mặc định tương ứng một module.**

Sau này build system có thể hỗ trợ module aggregation mà **không thay đổi semantic model**.

Như vậy:

```text
vector.ax
```

→ module `math.vector`.

---

# 5. Module declaration

Syntax đề xuất:

```axiom
module math.vector
```

Nếu source path đã xác định module thì declaration có thể optional.

Ví dụ:

```text
src/math/vector.ax
```

compiler mặc định suy ra:

```text
myapp.math.vector
```

`module` declaration dùng để xác nhận hoặc override có kiểm soát.

---

# 6. Import

```axiom
import math.vector
```

Sau đó:

```axiom
let v = Vector(...)
```

nếu symbol được export và prelude/import rules cho phép.

---

# 7. Không dùng textual include

Không có:

```text
#include
```

hay:

```text
include("file.ax")
```

Module dependency là semantic dependency.

---

# 8. Import một symbol

Có thể:

```axiom
import math.vector.Vector
```

hoặc tôi nghiêng về:

```axiom
import math.vector { Vector, dot }
```

Cách thứ hai dễ đọc và compiler dễ biểu diễn namespace dependency.

---

# 9. Alias

```axiom
import graphics.opengl as gl
```

Sau đó:

```axiom
gl.create_buffer(...)
```

---

# 10. Import module namespace

```axiom
import graphics.opengl
```

sử dụng:

```axiom
graphics.opengl.create_buffer(...)
```

Cũng nên hỗ trợ:

```axiom
import graphics.opengl as gl
```

để rút gọn.

---

# 11. `pub`

Private mặc định.

```axiom
fn internal_helper() { ... }

pub fn public_api() { ... }
```

Không có:

```text
public
protected
private
package
friend
```

hàng loạt keyword.

Chỉ cần:

```text
pub
```

và mặc định private.

---

# 12. Struct visibility

```axiom
pub struct User {
    pub id: UserId
    name: Text
}
```

Điều này cực kỳ quan trọng:

> `pub struct` không đồng nghĩa mọi field đều public.

Field:

```text
private mặc định
```

API có thể kiểm soát invariant.

---

# 13. Constructor không đặc biệt

Không có constructor language feature.

```axiom
pub fn user(id: UserId, name: Text) -> User {
    User {
        id,
        name,
    }
}
```

Do đó:

```text
class constructor
destructor
virtual method
```

đều không cần.

---

# 14. Public type nhưng private representation

Ví dụ:

```axiom
pub struct Password {
    bytes: Bytes
}
```

bên ngoài module không thể trực tiếp tạo:

```text
Password { ... }
```

nếu field private.

Phải dùng:

```axiom
Password.parse(...)
```

Đây là cách bảo vệ invariant rất sạch.

---

# 15. Trait visibility

```axiom
pub trait Drawable {
    fn draw(self: view<Self>, canvas: mut_view<Canvas>)
}
```

Trait public.

Implementation có thể private:

```axiom
impl Drawable for InternalType { ... }
```

hoặc public type nhưng implementation nội bộ.

---

# 16. Trait implementation visibility

Có một vấn đề quan trọng:

Nếu trait public và type public:

```axiom
pub trait ToText { ... }

pub struct User { ... }

impl ToText for User { ... }
```

thì implementation phải trở thành một phần observable của API.

Compiler phải đưa nó vào:

```text
Semantic Interface Fingerprint
```

Nếu không incremental compilation sẽ sai.

---

# 17. Generic public API

Ví dụ:

```axiom
pub fn max<T: Ord>(a: T, b: T) -> T
```

`Ord` cũng phải accessible.

Không cho:

```axiom
pub fn foo<T: PrivateTrait>(x: T)
```

nếu `PrivateTrait` không thể được resolve bởi caller.

Diagnostic:

```text
AX_API_0001

public declaration exposes private type/trait
```

---

# 18. Private type không được leak qua public API

Ví dụ:

```axiom
struct Secret { ... }

pub fn create() -> Secret
```

Không hợp lệ.

Tại sao?

Caller không thể name hoặc use `Secret` một cách hợp lệ.

Tôi đề xuất **cấm public signature exposure của private type**, kể cả khi type inference có thể che nó.

---

# 19. `impl` cũng có visibility implications

Ví dụ:

```axiom
struct Secret

pub fn make() -> Secret
```

không được.

Nhưng:

```axiom
pub fn make() -> impl PublicTrait
```

có thể hợp lệ nếu anonymous concrete type không cần public name.

Đây là nơi `impl Trait` rất hữu ích.

---

# 20. `impl Trait` public

Ví dụ:

```axiom
pub fn iterator() -> impl Iterator<Item = i32> {
    ...
}
```

Caller biết:

```text
behavior contract
```

nhưng không cần biết concrete type.

Static dispatch vẫn có thể giữ.

Không cần dynamic allocation.

---

# 21. `dyn Trait` public

Có thể:

```axiom
pub fn create() -> dyn Drawable
```

nhưng đây là dynamic abstraction rõ ràng.

ABI/library representation có thể là:

```text
data_ptr
dispatch_ptr
```

và có cost tương ứng.

---

# 22. Public ≠ linker export

Ví dụ:

```axiom
pub fn foo() {}
```

không nhất thiết tạo exported native symbol:

```text
foo
```

`pub` chỉ có semantic visibility trong package/module system.

Nếu muốn linker export:

```axiom
@export("my_foo")
pub extern "C" fn foo() {}
```

---

# 23. ABI boundary độc lập

Ta có:

```text
pub
 ↓
source/API visibility
```

và:

```text
@export
extern "C"
 ↓
native ABI boundary
```

Không được nhập hai khái niệm này thành một.

---

# 24. Package boundary

Tôi đề xuất:

```text
private
```

nghĩa là:

> chỉ module hiện tại và các child/internal semantic scopes được phép truy cập.

Còn:

```text
pub
```

nghĩa là:

> symbol thuộc public package API.

---

# 25. Có cần `internal` không?

Tôi nghĩ **có**, nhưng không nên biến nó thành một access modifier kiểu C#.

Đề xuất:

```axiom
internal fn helper() { ... }
```

nghĩa:

> visible trong toàn package, nhưng không xuất hiện trong public package API.

Điều này rất hữu ích.

---

# 26. `private` vs `internal` vs `pub`

```text
private
    ↓
module only

internal
    ↓
package

pub
    ↓
package consumers
```

Đây là ba mức đủ dùng.

Không cần:

```text
protected
friend
friend class
friend module
package-private
```

---

# 27. Nhưng private nested module?

Ví dụ:

```text
app
├── public_api
└── implementation
```

`implementation` có thể:

```axiom
internal
```

và public module re-export API cần thiết.

---

# 28. Friend không cần trong Core

Thay vì:

```text
friend module a
```

dùng:

```text
internal
```

hoặc tách abstraction thành module nội bộ.

Nếu cần access đặc biệt cho testing, build tooling có thể có test visibility mechanism.

Không làm language core phức tạp.

---

# 29. Re-export

Rất cần:

```axiom
pub use math.vector.Vector
```

hoặc:

```axiom
pub import math.vector { Vector }
```

Tôi đề xuất keyword riêng:

```axiom
pub use math.vector.Vector
```

`use` mang nghĩa:

> đưa một symbol vào namespace hiện tại.

---

# 30. Re-export không tạo type mới

Nếu:

```text
math.Vector
```

được re-export:

```text
graphics.Vector
```

thì:

```text
math.Vector == graphics.Vector
```

về type identity.

Không copy type.

---

# 31. Alias khác re-export

```axiom
pub use math.vector.Vector as Vec
```

thì:

```text
Vec
```

chỉ là một exported name khác.

Type identity vẫn là:

```text
math.vector.Vector
```

---

# 32. Type alias

```axiom
type UserId = u64
```

là alias.

Do đó:

```text
UserId
```

và:

```text
u64
```

cùng type identity.

---

# 33. Newtype

Nếu cần type identity mới:

```axiom
struct UserId(u64)
```

hoặc tuple struct tương đương.

Sau đó:

```text
UserId != u64
```

Đây là cách tránh misuse của primitive.

---

# 34. Không có `typedef` kiểu C

Axiom chỉ cần:

```text
type      → alias
struct    → new type
enum      → new type
```

rõ ràng.

---

# 35. Module circular dependency

Ví dụ:

```text
A → B
B → A
```

Có nên cấm hoàn toàn?

**Không.**

Module cycle không nhất thiết là semantic problem.

---

# 36. Cho phép declaration cycle

Ví dụ:

```text
A
 └── references public type from B

B
 └── references public type from A
```

có thể hợp lệ nếu compiler có thể resolve declarations.

---

# 37. Nhưng value initialization cycle phải cấm

Ví dụ:

```text
A.x = B.y
B.y = A.x
```

nếu runtime initialization xảy ra:

```text
cycle
```

→ lỗi.

Thậm chí tốt hơn:

> Không có implicit module initialization.

Do đó phần lớn vấn đề này biến mất.

---

# 38. Global initialization

Đã chốt:

```axiom
const X = ...
static Y = ...
```

phải được phân biệt.

`const`:

```text
compile time
```

`static` immutable:

```text
static storage
compile-time initialization nếu có thể
```

Runtime initialization:

```text
Lazy<T>
init()
```

explicit.

---

# 39. Không có hidden global constructors

Không:

```text
import module
    ↓
constructor chạy
```

Điều này cực kỳ tốt cho:

- deterministic startup;
- freestanding;
- binary size;
- linker dead stripping;
- dependency analysis.

---

# 40. Package identity

Type identity không chỉ là:

```text
module + name
```

Mà:

```text
PackageIdentity
+
ModulePath
+
TypeDefinition
```

Package identity gồm:

```text
name
version
source
content hash
```

như package model đã chốt.

---

# 41. Hai version package có thể cùng tồn tại

Ví dụ:

```text
app
├── math@1
└── graphics
     └── math@2
```

Thì:

```text
math@1.Vector
```

khác:

```text
math@2.Vector
```

dù cùng spelling:

```text
Vector
```

---

# 42. Type identity không phụ thuộc import alias

Ví dụ:

```axiom
import math.vector.Vector as V
```

`V` không tạo type mới.

Identity vẫn:

```text
package::math::vector::Vector
```

---

# 43. Generic identity

Ví dụ:

```axiom
Vec<UserId>
```

identity gồm:

```text
Vec definition
+
UserId type identity
```

không phải string name.

Compiler dùng interned TypeId.

---

# 44. Semantic Interface Fingerprint

Public module API phải tạo:

```text
SIF
```

bao gồm:

```text
public types
public fields
public functions
public signatures
public traits
public impls affecting resolution
generic bodies cần specialization
ABI contracts
relevant attributes
```

---

# 45. Private implementation không nên invalidate consumer compilation

Ví dụ:

```text
public fn foo(x: i32) -> i32
```

thay implementation:

```text
x + 1
```

thành:

```text
x + 2
```

Consumer không nhất thiết phải typecheck lại.

Có thể chỉ relink/recompile affected code theo optimization strategy.

---

# 46. Nhưng generic body khác

Ví dụ:

```axiom
pub fn map<T>(...)
```

body có thể cần downstream monomorphization.

Do đó generic implementation phải nằm trong semantic compilation artifact.

SIF phải fingerprint phần cần thiết.

---

# 47. Trait implementation ảnh hưởng resolution

Nếu thêm:

```axiom
impl Foo for Bar
```

thì method/operator resolution có thể thay đổi.

Do đó implementation public phải là API semantic dependency.

Đây là lý do trait coherence rất quan trọng.

---

# 48. Coherence

Không cho package A và package B tùy tiện tạo hàng loạt implementation gây ambiguity.

Cần quy tắc:

> Một trait/type pair chỉ có một authoritative implementation trong coherence domain.

V0.1 có thể áp dụng rule đơn giản:

```text
Trait local OR Type local
```

để package được phép định nghĩa impl.

Nếu cả trait lẫn type đều foreign:

```text
impl ForeignTrait for ForeignType
```

→ cấm.

---

# 49. Điều này tránh dependency hell

Nếu không:

```text
Package A
    impl TraitX for Vec<int>

Package B
    impl TraitX for Vec<int>
```

Caller import cả hai:

```text
which impl?
```

Không thể chấp nhận.

---

# 50. Module resolution

Resolution nên theo thứ tự:

```text
local declarations
↓
explicit imports
↓
module namespace
↓
prelude
```

Không nên có “magic search toàn package”.

---

# 51. Prelude

Có một prelude rất nhỏ:

```text
bool
Option
Result
Some
None
Ok
Err
Copy
Drop
view
mut_view
```

những thứ nền tảng có thể được auto-import.

Nhưng:

> Prelude phải nhỏ và ổn định.

Không biến prelude thành một đống standard library symbols.

---

# 52. Explicit import ưu tiên

Nếu hai module có:

```text
foo.Vector
bar.Vector
```

không được tự chọn.

Phải:

```axiom
import foo.Vector as FooVector
import bar.Vector as BarVector
```

hoặc qualified access.

---

# 53. Ambiguous import = compile error

Diagnostic:

```text
AX_RESOLVE_0004

ambiguous name: Vector

candidates:
    foo.Vector
    bar.Vector

suggestion:
    import one symbol with an alias
```

Rất phù hợp AI tooling.

---

# 54. Wildcard import

Tôi **không khuyến nghị**:

```axiom
import foo.*
```

trong v0.1.

Nó làm:

- namespace khó đọc;
- API dependency khó phân tích;
- IDE completion khó;
- AI reasoning khó;
- breaking changes khó phát hiện.

Nếu cần namespace:

```axiom
import foo
```

rồi:

```text
foo.Vector
```

---

# 55. Package public API manifest

Compiler có thể xuất:

```text
axiom inspect --api
```

Ví dụ:

```text
package: math
version: 1.2.0

pub:
    struct Vector2
    struct Vector3
    fn dot(...)
    trait Numeric
```

Đây là nền tảng rất tốt cho AI agent.

---

# 56. API diff

Tool:

```text
axiom api-check old.pkg new.pkg
```

có thể phát hiện:

```text
removed public function
changed field visibility
changed generic constraint
changed trait implementation
changed repr(C)
changed ABI
```

Không cần IDE tự đoán.

---

# 57. Public API không đồng nghĩa stable API

Axiom cần thêm một khái niệm:

```text
pub
```

= public.

Nhưng:

```text
@stable
```

= API compatibility contract.

Không nên mặc định mọi `pub` đều cam kết backward compatibility vĩnh viễn.

---

# 58. ABI stability

Tương tự:

```text
pub
```

không đảm bảo ABI stable.

Muốn ABI stable:

```text
extern "C"
```

hoặc ABI version contract tương lai.

---

# 59. Attributes

V0.1 nên giới hạn attribute semantic:

```axiom
@repr(C)
@repr(transparent)
@repr(packed)
@align(64)
@export("foo")
@entry
@cfg(...)
@interrupt
```

Không cho attribute tùy ý thay đổi compiler semantics.

---

# 60. Internal implementation attributes

Compiler có thể có:

```text
@compiler(...)
```

nhưng không nên trở thành public language contract.

---

# 61. Friend-like access cho test

Một vấn đề thực tế:

```text
private field
```

test muốn kiểm tra.

Không nên thêm `friend`.

Có thể:

```text
@cfg(test)
```

và test module nằm trong cùng module semantic scope.

Hoặc test API dùng public behavior thay vì private representation.

---

# 62. Circular package dependency

Tôi đề xuất:

> **Package graph phải là DAG. Module graph bên trong package có thể có cycle theo declaration rules.**

Điều này phù hợp package resolver.

```text
Package A → Package B
Package B → Package A
```

→ cấm.

Nhưng:

```text
Module A ↔ Module B
```

→ có thể hợp lệ.

---

# 63. Tại sao package phải DAG?

Để:

- dependency resolution;
- reproducible build;
- incremental compilation;
- cache;
- bootstrap;
- AI project graph;

đều đơn giản hơn.

---

# 64. Module cycle không được tạo recursive value layout

Ví dụ:

```text
struct A {
    b: B
}

struct B {
    a: A
}
```

→ infinite size.

Compiler reject.

Nhưng:

```text
struct A {
    b: Box<B>
}

struct B {
    a: Box<A>
}
```

→ hợp lệ.

---

# 65. Import cycle không phải runtime cycle

Do không có hidden initialization:

```text
A imports B
B imports A
```

chỉ là symbol dependency.

Không có:

```text
A constructor
→ B constructor
→ A constructor
```

ẩn phía sau.

Đây là một lợi thế lớn của Axiom.

---

# 66. Module visibility model cuối cùng

Tôi đề xuất đóng băng:

```text
                 Visibility

private
   │
   └── current module

internal
   │
   └── package

pub
   │
   └── package consumers

@export + extern ABI
   │
   └── native linker/FFI boundary
```

Không có `protected`.

Không có `friend`.

Không có implicit public.

---

# 67. Invariants

```text
AMOD-13  Module Is A Semantic Namespace
AMOD-14  File Is Not A Semantic Module Boundary
AMOD-15  Import Is A Semantic Dependency
AMOD-16  Textual Include Is Not Core
AMOD-17  Private Is The Default Visibility
AMOD-18  Internal Is Package-Visible Only
AMOD-19  Pub Defines Package API Visibility
AMOD-20  Pub Does Not Imply Linker Export
AMOD-21  Linker Export Requires Explicit ABI/Export Contract
AMOD-22  Public Fields Are Explicit
AMOD-23  Public APIs Cannot Expose Unreachable Private Types
AMOD-24  Impl Resolution Affects Semantic API Fingerprints
AMOD-25  Re-Export Does Not Create A New Type
AMOD-26  Type Alias Does Not Create A New Type
AMOD-27  Newtype Creates A Distinct Type Identity
AMOD-28  Package Identity Includes Version And Source Identity
AMOD-29  Import Aliases Do Not Change Type Identity
AMOD-30  Package Graph Is Acyclic
AMOD-31  Module Graph May Contain Declaration Cycles
AMOD-32  Runtime Initialization Cycles Are Not Implicitly Possible
AMOD-33  Recursive Value Layout Requires Finite Indirection
AMOD-34  Wildcard Imports Are Not Core v0.1
AMOD-35  Ambiguous Name Resolution Is A Compile Error
AMOD-36  Prelude Is Small And Explicitly Defined
AMOD-37  Public Generic Constraints Must Be Reachable
AMOD-38  Public Generic Implementations Participate In Semantic Fingerprinting
AMOD-39  Public Trait Implementations Affect Method Resolution
AMOD-40  Coherence Prevents Conflicting Foreign Trait Implementations
AMOD-41  Public Visibility Does Not Guarantee API Stability
AMOD-42  Stable API Requires An Explicit Stability Contract
AMOD-43  Stable ABI Requires An Explicit ABI Contract
AMOD-44  Source Visibility And ABI Visibility Are Independent
AMOD-45  Semantic Interface Fingerprints Drive Incremental Compilation
AMOD-46  Private Implementation Changes Need Not Invalidate Consumers
AMOD-47  Compiler Is The Authority For API Resolution
AMOD-48  IDE And AI Consume Compiler API Facts
AMOD-49  Module Metadata Cannot Redefine Core Semantics
AMOD-50  No Hidden Module Initialization
```

---

# 68. Một syntax mẫu bắt đầu khá hoàn chỉnh

```axiom
module graphics.renderer

import math.vector { Vector3 }
import graphics.texture as texture

pub struct Renderer {
    device: Device
    width: u32
    height: u32
}

pub trait Drawable {
    fn draw(
        self: view<Self>,
        renderer: mut_view<Renderer>
    ) -> Result<(), DrawError>
}

impl Drawable for Mesh {
    fn draw(
        self: view<Mesh>,
        renderer: mut_view<Renderer>
    ) -> Result<(), DrawError> {
        ...
    }
}

pub fn create_renderer(
    device: Device
) -> Result<Renderer, RendererError> {
    ...
}
```

Đây đã thể hiện gần như toàn bộ philosophy:

- không class;
- struct là data;
- function là behavior;
- trait là abstraction;
- method chỉ là syntax sugar;
- ownership không có lifetime syntax;
- `view`/`mut_view` thể hiện capability;
- Result là failure;
- private field bảo vệ invariant;
- public API rõ ràng;
- ABI không bị lẫn vào source visibility.

---

# 69. Tôi muốn chốt thêm một nguyên tắc rất quan trọng

### Không để module system trở thành một ngôn ngữ macro thứ hai.

Ví dụ không nên có:

```text
import dynamic_expression(...)
```

hoặc:

```text
import depending_on_runtime_value
```

Module resolution phải diễn ra:

```text
source
→ package graph
→ module graph
→ symbol resolution
```

hoàn toàn deterministic.

---

# 70. Axiom hiện đã có một tầng architecture khá rõ

```text
┌─────────────────────────────────────────────┐
│              Axiom Source                   │
├─────────────────────────────────────────────┤
│ Syntax / Modules / Visibility               │
├─────────────────────────────────────────────┤
│ Type / Trait / Generic                      │
├─────────────────────────────────────────────┤
│ Ownership / View / Resource                 │
├─────────────────────────────────────────────┤
│ Concurrency / Async / Atomic                │
├─────────────────────────────────────────────┤
│ Result / Panic / Failure                    │
├─────────────────────────────────────────────┤
│ MIR / Verification                          │
├─────────────────────────────────────────────┤
│ Optimization / ABI                          │
├─────────────────────────────────────────────┤
│ LIR / Machine IR                            │
├─────────────────────────────────────────────┤
│ Object / Linker / Runtime components        │
└─────────────────────────────────────────────┘
```

Và điểm rất đáng chú ý:

> **Phần lớn “feature cao cấp” của Axiom hiện đã được thiết kế sao cho có thể biến mất trước machine code.**

Generic → monomorphization  
Trait static dispatch → direct call  
Closure → function + environment hoặc bị erase  
`?` → branch  
Ownership → verifier/compiler facts  
View → capability + thường pointer/length  
Async → state machine  
Comptime → compile-time only  
Abstraction → machine-level code nếu cần, hoặc biến mất.

Đó chính là nền tảng để đạt mục tiêu **high-level UX nhưng performance gần với C/C++**.

---

## Bước kế tiếp: đóng băng Grammar v0.1

Bây giờ không nên tiếp tục thêm abstraction nữa. Ta đã đủ semantic primitives.

Tiếp theo tôi sẽ chuyển toàn bộ những quyết định trên thành **Axiom Surface Grammar v0.1**, gồm:

```text
1. identifiers / keywords
2. literals
3. comments
4. operators + precedence
5. expressions
6. statements
7. struct
8. enum
9. trait
10. impl
11. generic / where
12. function
13. closure
14. module/import/use
15. visibility
16. attributes
17. pattern matching
18. view/mut_view
19. async/await
20. unsafe
21. comptime
22. const/static
23. error propagation
24. exact grammar EBNF
```

Sau đó có thể lấy **một chương trình Axiom hoàn chỉnh**, đi xuyên từ source → AST → HIR → ownership → Verified MIR → LIR để kiểm tra xem syntax có thật sự nhất quán với toàn bộ architecture hay không.