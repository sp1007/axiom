# BOOTSTRAP-174 — Reflection, Metadata, Compile-Time Introspection & Runtime Type Information
**FROZEN / COMPLETED**

Đây là phần rất quan trọng với Axiom vì nếu thiết kế sai, reflection có thể phá vỡ khá nhiều mục tiêu trước đó: binary nhỏ, runtime-free, zero-cost abstraction, tối ưu hóa mạnh và ABI linh hoạt.

Quyết định nền tảng:

> **Reflection mặc định là compile-time. Runtime reflection là một artifact capability, không phải đặc tính bắt buộc của mọi type hay mọi binary.**

---

## 174.1. Ba loại "reflection"

Axiom phân biệt hoàn toàn:

```text
Compile-time introspection
        ↓
Compiler metadata
        ↓
Runtime type information
```

### Compile-time

```ax id="1q8b2e"
comptime {
    Type::fields()
    Type::methods()
    Type::size()
    Type::align()
}
```

Không tạo runtime overhead.

### Compiler metadata

`.axmeta` chứa thông tin để compiler/tooling sử dụng.

Không nhất thiết được đưa vào executable.

### Runtime reflection

Chỉ tồn tại khi chương trình **explicitly yêu cầu**.

```text
Application
   │
   └── reflection feature
          ↓
      RTTI metadata
```

Không có reflection → linker strip metadata.

---

# 174.2. `Type` là compile-time value

Đã xác định trong Comptime:

```text
Type
```

là một compile-time semantic value.

Ví dụ conceptually:

```ax
comptime fn field_count<T>() -> usize {
    return Type<T>.fields().count();
}
```

`Type<T>` không phải object runtime.

---

# 174.3. Type identity

Mỗi type có semantic identity:

```text
TypeId
```

Compiler sử dụng:

```text
TypeId
GenericInstanceId
DeclarationId
FieldId
VariantId
TraitId
```

Không dùng tên string làm identity.

Ví dụ:

```ax
type A = User;
```

thì A và User vẫn cùng semantic type identity.

Trong khi:

```ax
struct UserId(u64);
```

là type mới.

---

# 174.4. Reflection API không dựa trên strings

Không nên thiết kế:

```ax
reflect("User")
```

làm cơ chế chính.

Thay vào đó:

```ax
comptime {
    let t = Type<User>;
}
```

Compiler có thể resolve trực tiếp:

```text
TypeId(User)
```

Điều này tránh:

- typo
- runtime lookup
- string comparison
- reflection ambiguity.

---

# 174.5. Type information có cấu trúc

Conceptual reflection model:

```text
TypeInfo
├── TypeId
├── Kind
├── Name
├── Module
├── Package
├── Visibility
├── GenericParameters
├── Fields
├── Variants
├── Traits
├── Methods
├── AssociatedItems
├── Attributes
├── Layout
└── ABI
```

Nhưng không phải tất cả field đều có runtime representation.

---

# 174.6. Type kind

Compiler reflection có thể phân biệt:

```text
Primitive
Struct
Tuple
Array
Enum
Function
Closure
Trait
DynTrait
View
MutView
RawPointer
GenericParameter
TypeAlias
Newtype
```

---

# 174.7. Field reflection

Ví dụ:

```ax
struct User {
    pub id: u64;
    pub name: String;
    secret: u32;
}
```

Comptime reflection có thể thấy:

```text
id
name
secret
```

nếu code có đủ visibility/privilege.

Nhưng external package chỉ thấy:

```text
pub id
pub name
```

Private fields vẫn private.

---

# 174.8. Reflection không bypass visibility

Đây là invariant rất quan trọng:

> **Reflection không phải backdoor của visibility.**

Nếu package A không được truy cập:

```text
B::User.secret
```

thì reflection của A cũng không được dùng để lấy `secret`.

Compiler reflection phải chịu cùng permission model.

---

# 174.9. Internal compiler reflection

Compiler có quyền nhìn semantic representation đầy đủ hơn user code.

Ví dụ compiler có thể biết:

```text
FieldId
physical offset
niche
Drop glue
ABI classification
```

nhưng user comptime chỉ được expose những metadata được phép.

---

# 174.10. Layout reflection

Các API:

```ax
size_of<T>()
align_of<T>()
offset_of<T, field>()
```

đã được định nghĩa.

Những API này **quan sát physical layout**.

Do đó chúng tạo representation dependency.

Ví dụ:

```ax
comptime const USER_SIZE = size_of<User>();
```

Nếu layout thay đổi:

```text
USER_SIZE
```

phải được recompute.

---

# 174.11. Layout reflection không tự khóa layout

Một điểm rất quan trọng.

Việc compiler có:

```ax
size_of<T>()
```

không có nghĩa mọi struct phải có layout ổn định.

Chỉ khi source thực sự quan sát:

```ax
offset_of
size_of
align_of
```

hoặc explicit ABI/repr contract, optimizer mới bị ràng buộc bởi observable representation.

---

# 174.12. `@repr(C)`

FFI reflection có thể yêu cầu:

```ax
@repr(C)
struct Foo { ... }
```

Compiler metadata lúc này phải chứa:

```text
size
alignment
field offsets
field types
ABI
```

để FFI generator có thể sử dụng.

---

# 174.13. Enum reflection

Ví dụ:

```ax
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

Comptime reflection có thể inspect:

```text
variants
variant names
payload types
attributes
```

nhưng không được mặc định expose:

```text
discriminant byte layout
```

trừ khi representation observation được phép.

---

# 174.14. Trait reflection

Có thể query:

```text
traits implemented by T
```

và:

```text
methods declared by Trait
associated types
associated constants
constraints
```

Nhưng trait reflection phải phân biệt:

```text
declared trait
vs
inherited/default behavior
vs
concrete implementation
```

vì Axiom không có class inheritance.

---

# 174.15. Generic reflection

Compiler có thể inspect:

```text
T
T: Trait
const N
```

và generic environment.

Ví dụ:

```ax
comptime fn make_array<T, const N: usize>() -> Array<T, N>
```

có thể dùng `N` tại compile time.

Không cần runtime generic metadata.

---

# 174.16. Associated type reflection

Ví dụ:

```ax
trait Iterator {
    type Item;
}
```

với:

```ax
T: Iterator
```

compiler có thể normalize:

```text
<T as Iterator>::Item
```

thành concrete TypeId khi đủ thông tin.

Reflection nhìn thấy **semantic projection**, không phải chỉ tên string.

---

# 174.17. Function reflection

Có thể inspect:

```text
FunctionInfo
├── FunctionId
├── name
├── parameters
├── return type
├── generic parameters
├── where constraints
├── effects
├── async
├── comptime
├── unsafe
├── calling convention
├── attributes
└── visibility
```

---

# 174.18. Effect reflection

Do Axiom đã có Effect System, reflection có thể biết:

```text
fn foo(...)
```

có thể:

```text
Read
Write
Allocate
IO
Atomic
Synchronize
Panic
Foreign
Suspend
GPU
```

Điều này đặc biệt hữu ích cho AI/compiler tooling.

---

# 174.19. Ownership reflection

Không nên expose toàn bộ verifier state như runtime concept.

Nhưng comptime/compiler tooling có thể biết:

```text
Copy
Clone
Drop
Send
Share
```

và các capability contracts phù hợp.

Ví dụ:

```text
is_copy<T>()
is_send<T>()
is_share<T>()
has_drop<T>()
```

được đánh giá compile time.

---

# 174.20. `view` / `mut_view` reflection

Có thể xác định:

```text
is_view<T>
is_mut_view<T>
```

nhưng capability lifetime vẫn là compiler semantic state.

Không tạo runtime "lifetime object".

---

# 174.21. Attributes

Attributes là metadata có cấu trúc:

```ax
@repr(C)
@export("foo")
@inline(always)
@target_feature("avx2")
```

Reflection có thể query attributes mà nó có quyền thấy.

Không biến attributes thành arbitrary string macro system.

---

# 174.22. Typed attributes

Axiom ưu tiên:

```text
Attribute {
    Kind
    Arguments
}
```

thay vì:

```text
"@some_random_string(...)"
```

Compiler có thể validate attribute schema.

---

# 174.23. `@derive`

Đây là một ứng dụng lớn của reflection.

Ví dụ:

```ax
@derive(Debug, Eq, Hash, Serialize)
struct User {
    ...
}
```

Compiler có thể:

```text
Type reflection
      ↓
derive generator
      ↓
generated declarations
      ↓
normal resolver
      ↓
normal type checking
      ↓
normal ownership verification
```

Không bypass compiler.

---

# 174.24. Serialization

Serialization không cần runtime reflection mặc định.

Ví dụ:

```ax
@derive(Serialize)
struct User { ... }
```

compiler tạo code tương đương semantic:

```text
User
 ↓
generated serializer
 ↓
ordinary Axiom code
```

Sau optimization:

```text
reflection machinery → 0
```

nếu không được yêu cầu runtime reflection.

Đây chính là hướng **zero-cost reflection**.

---

# 174.25. GUI generation

Tương tự:

```ax
@derive(GuiModel)
struct User {
    ...
}
```

có thể generate metadata/code tại compile time.

GUI framework không cần inspect mọi object runtime bằng reflection.

---

# 174.26. Database mapping

Ví dụ:

```ax
@derive(RowMapping)
struct User {
    id: u64;
    name: String;
}
```

Compiler có thể tạo:

```text
SQL row → User
User → SQL parameters
```

với field access trực tiếp.

Không cần:

```text
runtime string lookup
runtime field map
runtime dynamic type system
```

---

# 174.27. Runtime RTTI

Nếu thực sự cần:

```text
Any
plugin system
dynamic serializer
scripting
debugger
dynamic UI
```

program có thể opt-in:

```text
@runtime_reflect
struct User { ... }
```

Compiler emit metadata section:

```text
.axrtti
```

hoặc target-native metadata section.

---

# 174.28. Runtime metadata

RTTI entry conceptually:

```text
RuntimeTypeInfo
├── TypeId
├── name
├── size
├── alignment
├── kind
├── fields
├── variants
├── traits
└── operations
```

Nhưng chỉ emit những thành phần được yêu cầu.

---

# 174.29. Không có global RTTI registry bắt buộc

Không có:

```text
global TypeRegistry
```

được tự động khởi tạo trong mọi executable.

Nếu application không dùng RTTI:

```text
RTTI = 0 bytes
```

về mặt semantic requirement, modulo debug/tool metadata riêng biệt.

---

# 174.30. Runtime type ID

Không nên dựa vào:

```text
memory address of TypeInfo
```

để định danh type.

Type identity là semantic.

Runtime ID có thể là:

```text
TypeFingerprint
```

hoặc compiler-generated stable identifier theo ABI/runtime profile.

---

# 174.31. Type fingerprint

Conceptual:

```text
TypeFingerprint =
    semantic type identity
    + relevant ABI contract
```

Không dùng tên đơn thuần.

Hai type:

```text
A::User
B::User
```

khác nhau dù cùng tên.

---

# 174.32. Generic runtime reflection

Nếu:

```ax
fn print<T>(x: T)
```

không dùng RTTI thì:

```text
T metadata = 0
```

Compiler specialize code.

Nếu `print` yêu cầu runtime reflection:

```text
T → RuntimeTypeInfo
```

thì metadata được truyền explicit/ABI-lowered.

Không tạo hidden global lookup.

---

# 174.33. Reflection và dynamic dispatch

`dyn Trait` đã là explicit dynamic mechanism.

Không nên biến:

```text
dyn Trait
```

thành:

```text
all types carry RTTI
```

Dynamic dispatch chỉ cần metadata cần thiết cho trait object.

Static dispatch vẫn không có vtable.

---

# 174.34. Reflection và linker

Runtime reflection tạo reachability roots.

Nếu metadata nói:

```text
User
```

có thể được dynamically instantiated, linker không được xóa những declarations mà reflection contract yêu cầu.

Ngược lại, compile-time-only reflection không tạo runtime reachability root.

---

# 174.35. Reflection stripping

Build profile:

```text
release
size
```

có thể strip:

```text
unused RTTI
unused reflection metadata
debug metadata
source metadata
```

nếu không thuộc contract runtime.

---

# 174.36. Reflection sections

Binary có thể chứa:

```text
TEXT
RODATA
DATA
...
DEBUG
AXREFLECT
```

`AXREFLECT` chỉ xuất hiện nếu cần.

Linker có thể section-GC từng phần metadata.

---

# 174.37. Reflection và ABI

Runtime reflection metadata là một phần ABI nếu dynamic component sử dụng nó.

Do đó:

```text
Stable ABI + runtime reflection
```

phải định nghĩa:

```text
metadata schema version
TypeId rules
layout rules
calling rules
trait metadata
```

Không thể coi RTTI binary format là implementation detail nếu plugin phụ thuộc vào nó.

---

# 174.38. Reflection và shared libraries

Dynamic library:

```text
App
 ↓
libA
 ↓
libB
```

không được giả định tất cả type metadata nằm trong một executable.

Runtime reflection system phải hỗ trợ:

```text
local metadata
shared metadata
explicit registration
dynamic discovery
```

tùy runtime profile.

Nhưng **registration không được bắt buộc cho chương trình không dùng reflection**.

---

# 174.39. Plugin architecture

Plugin có thể export:

```text
@export("plugin_init")
```

và một explicit ABI descriptor.

Ví dụ concept:

```text
PluginDescriptor {
    abi_version
    api_version
    functions
    types
}
```

Không cần toàn bộ Axiom runtime type system giữa host/plugin.

---

# 174.40. C ABI reflection

C header generator có thể dùng compile-time reflection:

```text
Axiom type
    ↓
comptime reflection
    ↓
C declaration generator
```

Nhưng C ABI vẫn phải tuân thủ:

```text
@repr(C)
extern "C"
```

Reflection không biến một struct layout mặc định thành C-compatible.

---

# 174.41. FFI metadata

`.axmeta` có thể chứa:

```text
FfiSafe
repr
alignment
layout
calling convention
ownership
nullable/raw pointer status
string encoding
error ABI
```

Compiler có thể kiểm tra FFI boundary trước codegen.

---

# 174.42. Comptime file generation

Comptime có thể generate:

```text
schema
bindings
serialization code
C headers
GPU kernels
GUI descriptors
documentation
```

nhưng output phải trở lại build graph.

Ví dụ:

```text
Source
 ↓
Comptime
 ↓
Generated declarations
 ↓
Compiler verification
```

Generated code không được bypass:

```text
type checker
ownership verifier
capability verifier
ABI checker
```

---

# 174.43. Generated metadata dependency

Nếu comptime đọc:

```text
schema.json
```

thì schema trở thành build dependency.

Build identity bao gồm:

```text
schema hash
```

để tránh stale generated code.

---

# 174.44. Reflection và reproducible build

Reflection enumeration phải deterministic.

Ví dụ fields:

```text
[a, b, c]
```

không được thay đổi thứ tự theo:

```text
hash table order
parallel compiler completion order
machine thread timing
```

Nếu physical layout được observe thì thứ tự/offset phải theo representation contract.

---

# 174.45. Reflection enumeration order

Semantic declaration order nên là canonical order cho reflection:

```text
DeclarationOrder
```

Physical field reordering của optimizer không được thay đổi semantic reflection order.

Đây là một phân biệt cực kỳ quan trọng:

```text
semantic field order
≠
physical storage order
```

---

# 174.46. Reflection và optimization

Compiler có thể:

```text
struct fields
→ reorder physically
→ scalarize
→ eliminate field
```

nếu field không observable.

Nhưng nếu comptime program quan sát:

```text
offset_of
```

thì representation trở thành observable.

Nếu runtime reflection yêu cầu physical layout:

```text
layout must remain available
```

---

# 174.47. Reflection không phải serialization

Đây là hai hệ thống khác nhau:

```text
Reflection
    = inspect program/type metadata

Serialization
    = transform value ↔ external representation
```

Không được suy ra:

```text
memory layout == wire format
```

Serialization phải có schema/encoding riêng.

---

# 174.48. Reflection không phải debugger

Debug information:

```text
DWARF
PDB
dSYM
```

là developer metadata.

Runtime RTTI là application metadata.

Hai hệ thống không được gộp.

Một release binary có thể:

```text
debug info = stripped
RTTI = retained
```

hoặc ngược lại.

---

# 174.49. Reflection và AI

Đây sẽ là một tính năng rất mạnh.

AI/compiler interface có thể query:

```text
TypeId
fields
traits
effects
ownership properties
ABI
layout
generic constraints
generated code provenance
```

Ví dụ:

```text
axc inspect type User
axc inspect type User --layout
axc inspect type User --traits
axc inspect type User --abi
axc inspect type User --reflection
```

AI không cần parse source để biết toàn bộ semantic shape của type.

---

# 174.50. `.axmeta` không chỉ là documentation

Nó trở thành:

```text
Semantic Package Interface
```

cho:

```text
compiler
IDE
debugger
AI
documentation
binding generators
FFI tools
LTO
package manager
```

nhưng từng consumer chỉ được phép sử dụng metadata thuộc capability/visibility của nó.

---

# 174.51. Reflection capability model

Có thể chia:

```text
REFLECT_TYPE
REFLECT_DECLARATION
REFLECT_LAYOUT
REFLECT_ABI
REFLECT_SOURCE
REFLECT_PRIVATE
REFLECT_RUNTIME
```

Không phải application nào cũng được cấp toàn bộ.

---

# 174.52. Source reflection

Source-level metadata:

```text
source file
line
syntax
comments
documentation
```

không nên nằm trong runtime binary mặc định.

Nó thuộc:

```text
debug/source artifact
```

hoặc compiler tooling metadata.

---

# 174.53. Documentation generation

Compiler có thể dùng cùng metadata:

```text
.axmeta
   ↓
documentation generator
   ↓
API docs
```

Không cần một parser/documentation engine phải tự hiểu lại ngôn ngữ.

---

# 174.54. Reflection security

Không được cho phép reflection tự động expose:

```text
private secrets
memory addresses
unsafe internals
FFI handles
```

chỉ vì type có RTTI.

Sensitive data exposure phải là explicit contract.

---

# 174.55. `@secret`

Nếu type/value có security metadata:

```text
@secret
SecretKey
```

reflection phải tuân thủ policy:

```text
value = never printable
raw bytes = restricted
debug = redacted
reflection = restricted
```

Đây kết nối trực tiếp với Security Model.

---

# 174.56. Runtime dynamic invocation

Đây là phần nên **không đưa vào Core v0.1**.

Ví dụ:

```text
invoke_by_name("foo", args)
```

cần:

```text
dynamic type system
argument boxing
runtime dispatch
error model
ABI metadata
```

và dễ phá zero-cost.

Nếu cần, để library/runtime profile:

```text
std::reflect::dynamic
```

---

# 174.57. Core v0.1 không có `Any`

Đã thống nhất:

```text
No general Any/Object/null
```

Do đó runtime reflection không được dùng làm lý do đưa `Any` vào Core.

Có thể có library abstraction:

```text
DynamicValue
```

khi thực sự cần.

---

# 174.58. Reflection cost model

Có ba trường hợp:

### Không reflection

```text
compile-time reflection
→ generated code
→ reflection metadata eliminated
```

Runtime cost:

```text
≈ 0
```

### RTTI type-only

```text
TypeId → compact metadata
```

Có runtime metadata cost nhưng chỉ ở nơi dùng.

### Full dynamic reflection

```text
dynamic lookup
dynamic invocation
dynamic values
```

Chi phí do library/runtime profile chịu.

---

# 174.59. Reflection compilation pipeline

```text
Source
  ↓
Resolver
  ↓
TypeDB
  ↓
TraitDB
  ↓
Comptime Reflection
  ↓
Generated HIR
  ↓
Normal Verification
  ↓
Verified MIR
  ↓
Optimization
  ↓
Runtime RTTI emission ── only if requested
```

Không có nhánh đặc quyền bypass compiler.

---

# 174.60. Semantic source of truth

Reflection không phải semantic authority.

Thứ tự:

```text
Language semantics
       ↓
Compiler semantic model
       ↓
Reflection view
       ↓
Generated code / metadata
```

Không bao giờ:

```text
reflection metadata
       ↓
thay đổi semantics
```

---

# 174.61. Metadata layers

Axiom nên có ít nhất:

```text
.axmeta
   │
   ├── API metadata
   ├── generic metadata
   ├── ABI metadata
   ├── optimization metadata
   └── tooling metadata

.axrtti
   │
   └── runtime reflection only

.debug
   │
   └── debugger/source metadata
```

Không bắt buộc tất cả artifact cùng tồn tại.

---

# 174.62. Runtime metadata linker roots

RTTI metadata có thể tạo root:

```text
RuntimeReflectionRoot
```

Linker phải giữ đúng declarations mà metadata có thể reference.

Compiler-generated compile-time reflection **không** tạo root sau khi đã materialize code.

---

# 174.63. Dead metadata elimination

Ví dụ:

```text
@runtime_reflect(User)
```

nhưng không reflection `User.name`.

Compiler có thể emit:

```text
User type descriptor
```

mà không cần toàn bộ method/debug/source metadata.

Reflection metadata cũng phải được tree-shake.

---

# 174.64. Versioning

`.axmeta`:

```text
metadata schema version
```

`.axrtti`:

```text
runtime reflection ABI version
```

Hai version độc lập với:

```text
Axiom source language version
Axiom ABI version
```

---

# 174.65. Binary compatibility

Nếu runtime reflection là stable ABI:

```text
RTTI schema
+
ABI
+
TypeId rules
```

phải được versioned.

Nếu chỉ compile-time reflection:

```text
không có runtime compatibility obligation
```

---

# 174.66. Reflection and package privacy

Package A:

```text
pub struct Public
```

Package B không thể dùng reflection để biến:

```text
private implementation
```

thành public API.

Điều này bảo vệ abstraction boundary.

---

# 174.67. Opaque types

Axiom nên hỗ trợ **opaque/abstract API boundary** ở library/API layer.

Ví dụ concept:

```ax
pub opaque type Engine;
```

Consumer biết:

```text
Engine
```

nhưng không biết fields/layout.

Consumer có thể sử dụng public functions:

```ax
pub fn create() -> Engine;
pub fn run(mut_view<Engine>);
```

Điều này rất hữu ích cho ABI-stable libraries.

---

# 174.68. Opaque type reflection

External reflection thấy:

```text
Kind = Opaque
```

nhưng không thấy:

```text
private fields
layout
implementation
```

unless explicit privileged/compiler context.

---

# 174.69. Opaque type và optimization

Trong cùng compilation unit/LTO closed world, compiler có thể biết implementation.

Qua stable binary boundary:

```text
opaque
```

thực sự trở thành abstraction barrier.

Do đó:

```text
opaque source API
+
LTO
```

có thể vẫn optimize nếu implementation available.

Còn:

```text
opaque stable dynamic ABI
```

thì không.

---

# 174.70. Final reflection architecture

```text
                    Axiom Type System
                           │
                    ┌──────┴──────┐
                    ↓             ↓
              Compile-time    Runtime opt-in
               Reflection         RTTI
                    │               │
                    ↓               ↓
                Comptime         .axrtti
                    │               │
                    ↓               ↓
             Generated HIR     Dynamic systems
                    │
                    ↓
              Normal compiler
                    │
                    ↓
              Verified MIR
```

---

# 174.71. Invariants đóng băng

### Reflection

- **AREFLECT-20** — Compile-time reflection là mặc định.
- **AREFLECT-21** — Compile-time `Type` không phải runtime object.
- **AREFLECT-22** — Reflection không bypass visibility.
- **AREFLECT-23** — Reflection dùng semantic identities, không dùng string identity.
- **AREFLECT-24** — Reflection không thay đổi language semantics.
- **AREFLECT-25** — Generated code phải đi qua normal compiler verification.
- **AREFLECT-26** — Semantic declaration order deterministic.
- **AREFLECT-27** — Physical layout và semantic field order là hai khái niệm khác nhau.
- **AREFLECT-28** — Runtime reflection không bắt buộc.
- **AREFLECT-29** — Runtime reflection metadata phải explicit root.
- **AREFLECT-30** — Reflection metadata có thể bị strip khi không observable.

### Metadata

- **AMETA-20** — `.axmeta` là compiler/package semantic metadata.
- **AMETA-21** — `.axmeta` không mặc định là runtime metadata.
- **AMETA-22** — Metadata phải có schema/version identity.
- **AMETA-23** — Stale metadata không được authoritative.
- **AMETA-24** — Metadata visibility phải tuân thủ package visibility.
- **AMETA-25** — Compiler facts trong metadata không được override semantic verification.
- **AMETA-26** — Reflection metadata có thể được tree-shake.
- **AMETA-27** — Debug metadata và runtime reflection metadata độc lập.

### Runtime RTTI

- **ARTTI-20** — RTTI là opt-in.
- **ARTTI-21** — Không có global RTTI registry bắt buộc.
- **ARTTI-22** — Runtime TypeId không dựa trên memory address.
- **ARTTI-23** — RTTI ABI phải versioned nếu được chia sẻ qua binary boundary.
- **ARTTI-24** — RTTI không tự động tạo `Any`, Object hoặc dynamic invocation trong Core.
- **ARTTI-25** — Runtime metadata chỉ giữ những declarations được reflection contract yêu cầu.
- **ARTTI-26** — Dynamic reflection thuộc library/runtime profile.

### Opaque API

- **AOPAQUE-20** — Opaque type che implementation representation khỏi consumer.
- **AOPAQUE-21** — Opaque type vẫn có semantic type identity.
- **AOPAQUE-22** — Private representation không được expose qua reflection mặc định.
- **AOPAQUE-23** — Stable ABI của opaque type phải định nghĩa representation contract.
- **AOPAQUE-24** — Closed-world/LTO có thể optimize qua opaque boundary khi implementation khả dụng.

### Zero-cost

- **AZREFLECT-20** — Compile-time reflection có thể được erase hoàn toàn sau code generation.
- **AZREFLECT-21** — Không reflection → không mandatory RTTI runtime.
- **AZREFLECT-22** — Generated serialization/binding code không yêu cầu runtime reflection.
- **AZREFLECT-23** — Reflection không được ngăn optimization nếu metadata không observable.
- **AZREFLECT-24** — Runtime reflection cost phải do feature sử dụng nó chịu.

---

# BOOTSTRAP-174 hoàn tất

Điểm đáng giá nhất của thiết kế này là Axiom **không phải chọn giữa "ngôn ngữ có reflection mạnh" và "ngôn ngữ hiệu năng cao"**.

Có thể có:

```text
                  Reflection
                      │
          ┌───────────┴───────────┐
          ↓                       ↓
    Compile-time              Runtime
          │                       │
     mặc định                 opt-in
          │                       │
    generate code             RTTI
          │                       │
          ↓                       ↓
      0 runtime              có cost khi dùng
```

Vì vậy một chương trình systems-level đơn giản vẫn có thể đạt:

```text
No GC
No RTTI
No reflection runtime
No mandatory runtime
No hidden allocation
No hidden object header
```

trong khi framework/GUI/serialization/plugin/AI tooling vẫn có reflection rất mạnh.

---

# BOOTSTRAP-175 — Interoperability Architecture: C ABI, System ABI, Foreign Types, Bindings & Native Interop

Task kế tiếp nên khóa **cửa biên giữa Axiom và thế giới bên ngoài**.

Đây sẽ là bước rất quan trọng trước khi đi sâu tiếp vào runtime/library/platform:

```text
Axiom
  │
  ├── C
  ├── C++
  ├── OS APIs
  ├── system calls
  ├── shared libraries
  ├── native handles
  ├── callbacks
  ├── foreign memory
  ├── foreign strings
  ├── error codes
  ├── SIMD/ISA intrinsics
  ├── GPU APIs
  └── existing native binaries
```

Mục tiêu là **Axiom có thể thay thế C/C++ ở tầng systems nhưng vẫn gọi được gần như toàn bộ hệ sinh thái native hiện có**, mà không đưa pointer/reference/ABI complexity vào phần lớn code Axiom.