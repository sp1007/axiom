# BOOTSTRAP-185 — Reflection, Metadata, Runtime Type Information & Dynamic Loading
**FROZEN / COMPLETED**

Đây là phần chốt một nguyên tắc quan trọng của Axiom:

> **Axiom có reflection rất mạnh ở compile-time, nhưng runtime reflection là capability tùy chọn — không được biến thành overhead mặc định của mọi chương trình.**

Mục tiêu:

```text
Compile-time reflection
        ↓
      .axmeta
        ↓
┌───────┼────────┬──────────┐
IDE     AI      compiler   tooling
                         ↓
              optional runtime metadata
                         ↓
             plugin / scripting / GUI /
             serialization / hot reload
```

---

# 185.1. Ba loại metadata

Axiom phân biệt hoàn toàn:

```text
Compile Metadata
Runtime Metadata
Debug Metadata
```

### Compile Metadata

Phục vụ:

- compiler
- IDE
- AI
- generic programming
- comptime
- code generation

Không cần xuất vào executable.

### Runtime Metadata

Phục vụ:

- dynamic loading
- serialization
- plugin
- scripting
- runtime type inspection

Chỉ xuất khi chương trình yêu cầu.

### Debug Metadata

Phục vụ:

- debugger
- stack trace
- source mapping
- profiling

Không phải runtime reflection.

---

# 185.2. `.axmeta`

`.axmeta` là artifact metadata chính của Axiom.

Conceptual:

```text
.axmeta
├── Package
├── Module
├── Declaration
├── Type
├── Trait
├── Function
├── Generic
├── Const
├── ABI
├── Layout
├── Export
├── Effect
├── Capability
├── Source mapping
└── Compiler metadata
```

---

# 185.3. `.axmeta` không phải executable

Điều này rất quan trọng.

```text
program.ax
   ↓
program.axo
   ↓
program.exe

program.ax
   ↓
program.axmeta
```

Executable không bắt buộc chứa `.axmeta`.

---

# 185.4. Metadata không phải source code

`.axmeta` chứa semantic information đã canonicalize.

Không cần chứa toàn bộ source.

Ví dụ:

```text
FunctionId = 42
Name = foo
ReturnType = TypeId 18
Params = [...]
Effects = [Read]
ABI = Axiom
```

---

# 185.5. Stable IDs

Metadata sử dụng stable IDs:

```text
TypeId
FunctionId
TraitId
FieldId
VariantId
GenericInstanceId
```

không dùng tên string làm identity.

Tên chỉ là metadata.

---

# 185.6. Canonicalization

Hai compilation unit có semantic representation tương đương phải canonicalize metadata theo cùng quy tắc.

Điều này hỗ trợ:

- cache
- incremental compilation
- LTO
- AI tooling
- API diff

---

# 185.7. API fingerprint

Package có:

```text
PublicAPIFingerprint
```

được tính từ semantic public interface.

Bao gồm:

```text
public types
public functions
public traits
public associated items
public constants
generic constraints
ABI contracts
representation contracts
exports
```

---

# 185.8. Implementation fingerprint

Tách riêng:

```text
ImplementationFingerprint
```

cho:

- private functions
- private fields
- internal algorithms
- private constants
- internal generated code

---

# 185.9. Incremental consequence

Nếu thay:

```ax
fn private_algorithm() {
    ...
}
```

mà public semantics không đổi:

```text
PublicAPIFingerprint unchanged
```

dependent package không cần type-check lại toàn bộ.

---

# 185.10. API change

Nếu thay:

```ax
pub fn foo(x: i32) -> i32
```

thành:

```ax
pub fn foo(x: i64) -> i64
```

thì:

```text
PublicAPIFingerprint changed
        ↓
dependents invalidated
```

---

# 185.11. Semantic API fingerprint

Fingerprint không dựa đơn giản trên text.

Ví dụ đổi:

```ax
pub fn foo(x: i32) -> i32
```

format thành:

```ax
pub fn foo(
    x: i32
) -> i32
```

không làm API fingerprint thay đổi.

---

# 185.12. Comments

Thay documentation comment không nhất thiết invalidate code dependents.

Có thể có riêng:

```text
DocumentationFingerprint
```

---

# 185.13. Documentation metadata

`.axmeta` có thể chứa:

```text
/// Computes...
```

nhưng documentation không phải semantic contract trừ khi compiler attribute quy định khác.

---

# 185.14. Public type

```ax
pub struct User {
    ...
}
```

public type không đồng nghĩa public representation.

---

# 185.15. Private fields

Axiom cho phép:

```ax
pub struct User {
    id: u64,
    name: String,
}
```

Type public nhưng fields private.

External package có thể:

```ax
let user: User = ...
```

nhưng không:

```ax
user.id
```

---

# 185.16. Opaque representation

Đây là cách Axiom giữ ABI/API flexibility.

Public API có thể expose:

```text
pub struct HashMap<K,V>
```

nhưng không expose layout.

Compiler có thể thay:

```text
hash table
→
Swiss table
→
Robin Hood
→
tree hybrid
```

mà không phá source API.

---

# 185.17. Opaque type

Axiom nên hỗ trợ semantic opaque types ở package boundary.

Ví dụ conceptual:

```ax
pub opaque Session;
```

External package biết:

```text
Session là một type
```

nhưng không biết representation.

---

# 185.18. Opaque type operations

Package chỉ expose:

```ax
pub fn open(...) -> Session;
pub fn send(mut_view<Session>, ...) -> Result<...>;
pub fn close(Session) -> Result<...>;
```

Representation hoàn toàn private.

---

# 185.19. Opaque ≠ dyn Trait

Hai khái niệm khác nhau:

```text
opaque Type
    = compile-time concrete but hidden representation

dyn Trait
    = runtime dynamic dispatch
```

Opaque type không tự tạo vtable.

---

# 185.20. ABI opaque

Nếu opaque type đi qua stable binary ABI:

```text
ABI must define representation contract
```

hoặc truyền bằng:

```text
opaque handle
```

---

# 185.21. Public struct layout

Mặc định:

```text
pub struct Foo { ... }
```

không tạo stable binary layout.

Nếu cần:

```ax
@repr(C)
pub struct Foo {
    ...
}
```

---

# 185.22. Public enum

Thay đổi:

```ax
pub enum ResultKind {
    Ok,
    Error,
}
```

thành:

```ax
pub enum ResultKind {
    Ok,
    Error,
    Warning,
}
```

có thể phá exhaustive `match`.

Do đó đây là **source compatibility change**, dù layout chưa chắc thay đổi.

---

# 185.23. Non-exhaustive API

Để library có thể thêm enum variants, Axiom nên có:

```ax
@non_exhaustive
pub enum Error {
    Io,
    Permission,
}
```

Consumer phải có fallback:

```ax
match error {
    Error::Io => ...
    Error::Permission => ...
    _ => ...
}
```

---

# 185.24. Struct non-exhaustive

Tương tự:

```ax
@non_exhaustive
pub struct Config {
    ...
}
```

cho phép package thêm fields mà không phá external construction theo contract.

---

# 185.25. Public constructors

Một public struct có private fields thường được construct bằng:

```ax
Config::new(...)
```

thay vì:

```ax
Config { ... }
```

Điều này cho phép thay đổi representation.

---

# 185.26. Public trait

Trait là một phần rất nhạy cảm của API.

Ví dụ:

```ax
pub trait Reader {
    fn read(...);
}
```

Adding required method:

```ax
fn position(...);
```

có thể phá tất cả external implementations.

---

# 185.27. Default trait methods

Nếu method có default implementation:

```ax
pub trait Reader {
    fn read(...);

    fn position(...) {
        ...
    }
}
```

thêm method default có thể ít phá source compatibility hơn.

Nhưng vẫn cần xem xét:

- method resolution
- coherence
- object safety
- ABI
- semantic behavior

---

# 185.28. Trait object ABI

`dyn Trait` ABI không tự động stable.

Nếu library muốn dynamic plugin ABI:

```text
explicit ABI contract
```

phải được khai báo.

---

# 185.29. Generic public API

Ví dụ:

```ax
pub fn sort<T>(mut_view<T>) where T: Ord
```

API fingerprint phải bao gồm:

```text
T
Ord constraint
receiver/access mode
return type
effects/ABI-relevant contracts
```

---

# 185.30. Trait leakage

Một public function:

```ax
pub fn foo<T>(x: T) where T: InternalTrait
```

không thể expose `InternalTrait` nếu trait đó private.

Compiler phải báo lỗi API leakage.

---

# 185.31. Private type leakage

Tương tự:

```ax
fn private_type() -> InternalType
```

có thể private.

Nhưng:

```ax
pub fn get() -> InternalType
```

invalid nếu `InternalType` không public/opaque-exported.

---

# 185.32. Associated types

Public trait:

```ax
pub trait Iterator {
    type Item;
}
```

`Item` trở thành một phần public semantic API.

Thay đổi constraint/associated type semantics có thể invalidate dependents.

---

# 185.33. Associated constants

Tương tự:

```ax
type Item;
const SIZE: usize;
```

được fingerprint.

---

# 185.34. Associated functions

Cũng thuộc API contract.

---

# 185.35. Generic default arguments

Nếu Axiom hỗ trợ generic defaults trong tương lai, thay đổi default có thể thay đổi semantics của source không chỉ ABI.

Do đó phải fingerprint.

---

# 185.36. Const generic

Ví dụ:

```ax
pub fn matrix<T, const N: usize>(...)
```

`N` là semantic API component.

---

# 185.37. Feature flags

Feature:

```text
feature = "gpu"
feature = "network"
feature = "serde"
```

không được tạo semantics mơ hồ.

Build configuration phải xác định feature set trước semantic compilation.

---

# 185.38. Feature fingerprint

Artifact identity chứa:

```text
EnabledFeatures
```

Do đó:

```text
feature A
≠
feature B
```

là hai compilation identities.

---

# 185.39. Conditional API

```ax
@cfg(target_os = "windows")
pub fn native_handle(...)
```

API fingerprint phụ thuộc target configuration.

---

# 185.40. Target-specific metadata

Package metadata có thể chứa:

```text
API(target = windows)
API(target = linux)
API(target = wasm)
```

---

# 185.41. Target-specific dependency

Một package có thể:

```text
common
 ├── windows implementation
 ├── linux implementation
 └── wasm implementation
```

nhưng public portable API vẫn có thể thống nhất.

---

# 185.42. Re-export

Facade:

```ax
pub import internal::Client;
```

không tạo type mới.

`Client` vẫn cùng `TypeId`.

---

# 185.43. Facade package

Có thể thiết kế:

```text
my_framework
├── core
├── graphics
├── audio
└── networking
```

và facade:

```ax
import my_framework;
```

re-export các public APIs.

---

# 185.44. API identity qua re-export

Re-export không đổi:

```text
DeclarationId
TypeId
TraitId
```

Điều này tránh duplicate semantic identity.

---

# 185.45. Import hygiene

Import không làm thay đổi semantic meaning của declaration.

Import order không được thay đổi compilation result.

---

# 185.46. Namespace collision

Hai package có:

```text
foo::String
bar::String
```

không collision vì package identity khác nhau.

---

# 185.47. Dependency namespace

Dependency được namespace isolation:

```text
package_a::foo
package_b::foo
```

Không dựa vào global symbol namespace ở source level.

---

# 185.48. Multiple versions

Có thể:

```text
app
├── crypto@1
└── crypto@2
```

cùng tồn tại.

Package identity bao gồm:

```text
Name
Version
SourceIdentity
```

---

# 185.49. Type identity across versions

```text
crypto@1::Key
≠
crypto@2::Key
```

ngay cả nếu source definition giống hệt.

Đây là điều bắt buộc để tránh type confusion.

---

# 185.50. Dependency facade

Nếu muốn convert:

```text
KeyV1 → KeyV2
```

phải có explicit conversion.

Không implicit unify.

---

# 185.51. Binary dependency

`.axlib` / binary package phải mang:

```text
CompilerSemanticVersion
Target
Architecture
ABI
API fingerprint
Required features
Generic metadata
Link requirements
Runtime requirements
```

---

# 185.52. Binary package without source

Có thể compile:

```text
app
 ↓
vendor.axlib
```

không cần source.

Nếu API generic cần downstream specialization, binary phải có `.axmeta` đủ thông tin.

---

# 185.53. Generic metadata

Một binary library có:

```ax
pub fn map<T, U>(...)
```

phải export semantic generic metadata nếu cho phép downstream monomorphization.

---

# 185.54. Generic code body

Có hai chiến lược:

```text
A. export generic semantic/code metadata
B. precompile selected instances
```

Axiom nên hỗ trợ cả hai.

---

# 185.55. Cross-package specialization

Closed-world executable:

```text
Package A
    ↓
Package B
    ↓
LTO
    ↓
specialize
```

có thể optimize qua package boundary.

---

# 185.56. Dynamic library boundary

Dynamic library:

```text
A.so
```

là open-world.

Compiler không được assume implementation bất biến ngoài ABI contract.

---

# 185.57. Stable ABI

Axiom cần phân biệt:

```text
Source Compatibility
Binary Compatibility
ABI Stability
Semantic Compatibility
```

Không coi chúng là một.

---

# 185.58. Axiom ABI

Default Axiom ABI có thể **compiler-version dependent** trong giai đoạn đầu.

Ví dụ:

```text
Axiom ABI v0.1
```

không hứa binary compatibility vô thời hạn.

---

# 185.59. Stable C ABI

Khi cần lâu dài:

```ax
extern "C" fn ...
```

với FFI-safe types.

Đây mới là boundary stable được ưu tiên đầu tiên.

---

# 185.60. Plugin ABI

Không nên dùng trực tiếp internal Axiom ABI cho plugin lâu dài.

Nên có:

```text
Axiom Plugin ABI
```

phiên bản hóa riêng.

---

# 185.61. Plugin interface

Ví dụ conceptual:

```text
PluginDescriptor
PluginVersion
ABI Version
Exports
Capabilities
```

---

# 185.62. Dynamic loading

```ax
let plugin = Library::load(path)?;
```

sau đó:

```text
plugin
 ↓
symbol lookup
 ↓
typed function/interface
```

---

# 185.63. Symbol lookup

Raw lookup:

```text
get_symbol("foo")
```

chỉ trả opaque/raw symbol capability.

Typed conversion phải kiểm tra ABI signature.

---

# 185.64. Symbol type safety

Không được:

```text
raw symbol
→
arbitrary fn pointer
```

trong safe code.

Cần:

```text
ABI contract
```

hoặc unsafe.

---

# 185.65. Plugin ABI descriptor

Plugin có metadata:

```text
Plugin ABI
├── version
├── target
├── calling convention
├── type descriptors
├── exported functions
├── required capabilities
└── compatibility constraints
```

---

# 185.66. Version negotiation

Plugin loader có thể:

```text
required ABI
available ABI
```

và kiểm tra compatibility.

Không dựa vào string version đơn thuần.

---

# 185.67. ABI compatibility matrix

Compiler/tooling có thể kiểm tra:

```text
Source
Binary
ABI
Target
```

compatibility độc lập.

---

# 185.68. ABI break

Ví dụ đổi:

```text
struct layout
calling convention
enum representation
function parameter ABI
```

có thể phá binary compatibility ngay cả khi source API giống nhau.

---

# 185.69. `@repr(C)` boundary

`@repr(C)` ổn định representation theo C ABI contract trong subset FFI-safe.

Nó không biến toàn bộ Axiom semantics thành C semantics.

---

# 185.70. Serialization metadata

Runtime reflection có thể generate:

```text
TypeDescriptor
FieldDescriptor
VariantDescriptor
```

cho serialization.

Nhưng chỉ khi được yêu cầu.

---

# 185.71. Compile-time serialization

Thông thường tốt hơn:

```text
comptime reflection
        ↓
generate serializer
        ↓
ordinary native code
```

thay vì:

```text
runtime reflection
        ↓
generic interpreter
```

---

# 185.72. Zero-runtime-reflection

Program:

```ax
struct User {
    id: u64,
    name: String,
}
```

nếu không dùng runtime reflection:

```text
no TypeDescriptor
no runtime registry
no reflection runtime
```

được link.

---

# 185.73. Runtime reflection opt-in

Có thể:

```ax
@reflect
pub struct User {
    ...
}
```

Compiler emit descriptor.

---

# 185.74. Reflection granularity

Không chỉ:

```text
@reflect
```

toàn chương trình.

Có thể:

```text
@reflect(type)
@reflect(fields)
@reflect(methods)
@reflect(serialize)
```

để giảm binary size.

---

# 185.75. Reflection capability

Runtime reflection được xem như runtime capability:

```text
Reflection
```

Nếu không có capability:

```text
Type::runtime_descriptor()
```

không tồn tại.

---

# 185.76. Runtime type identity

Nếu runtime descriptor tồn tại:

```text
TypeDescriptor {
    TypeId
    package
    name
    layout?
    fields
    variants
    traits
}
```

Nhưng `TypeId` runtime không nhất thiết là memory pointer.

---

# 185.77. Runtime TypeId

Runtime TypeId phải ổn định trong phạm vi ABI/runtime contract.

Không dùng địa chỉ của descriptor làm identity.

---

# 185.78. Layout exposure

Runtime reflection chỉ được expose layout nếu contract cho phép.

Opaque type:

```text
size/alignment/layout
```

có thể bị che.

---

# 185.79. Private metadata

Runtime reflection không tự động bypass visibility.

Nếu type chỉ export public name:

```text
private fields
```

vẫn private.

---

# 185.80. Trusted reflection

System/debugging tool có thể request privileged metadata.

Ví dụ debugger biết private fields.

Nhưng đó là:

```text
Debug Metadata
```

không phải ordinary application reflection.

---

# 185.81. Dynamic type operations

Axiom không nên có:

```text
Object
Any
dynamic_cast_everything
```

trong Core.

Dynamic behavior phải explicit:

```text
dyn Trait
TypeDescriptor
Any-like library abstraction
```

---

# 185.82. `Any`

Nếu std cung cấp:

```text
Any
```

nó là type-erasure library abstraction.

Không phải universal root type.

---

# 185.83. Type erasure

`Any` có thể giữ:

```text
value
+
TypeId
+
destruction/copy/move operations
```

nhưng chỉ khi programmer yêu cầu.

---

# 185.84. No hidden boxing

Chuyển:

```text
T
```

sang:

```text
Any
```

không implicit.

Có thể allocation hoặc inline storage tùy implementation.

---

# 185.85. `dyn Trait` vs Any

```text
dyn Trait
```

= dynamic dispatch theo behavior.

```text
Any
```

= type erasure + runtime type identity.

Hai thứ khác nhau.

---

# 185.86. Reflection and Drop

Runtime metadata cho type có Drop phải biết destruction contract nếu type được dynamically owned.

---

# 185.87. Reflection and ownership

Reflection API không được phép bypass:

```text
Move
Drop
Capability
Visibility
```

---

# 185.88. Reflective field access

Nếu cho phép:

```ax
field = value.get_field("name");
```

thì operation phải chịu type/capability checking runtime.

Nhưng đây là optional dynamic facility.

---

# 185.89. Faster generated reflection

Axiom ưu tiên:

```text
comptime
 ↓
generated typed code
 ↓
direct field access
```

hơn:

```text
runtime string lookup
```

khi schema known compile-time.

---

# 185.90. Reflection architecture

```text
                Compiler
                   │
          ┌────────┴────────┐
          │                 │
     Compile Reflection   Runtime Metadata
          │                 │
       comptime          optional
          │                 │
       generated          plugin
          │              serialization
          │               scripting
          ↓                 ↓
       native code      runtime APIs
```

---

# 185.91. AI interface

`.axmeta` đặc biệt quan trọng cho AI.

AI có thể query:

```text
TypeId
FunctionId
TraitId
effects
ownership
ABI
generic constraints
source spans
dependencies
```

mà không cần parse toàn bộ project.

---

# 185.92. AI không được sửa semantics

AI có thể hỏi:

```text
why-not-call
why-trait-not-satisfied
why-view-invalid
why-specialization-failed
```

nhưng compiler vẫn là authority.

---

# 185.93. API diff

Tooling có thể:

```text
axc api-diff old.axmeta new.axmeta
```

và phân loại:

```text
Added
Removed
Changed
SourceBreaking
ABIBreaking
BehaviorRelevant
DocumentationOnly
```

---

# 185.94. Semantic versioning

Package version:

```text
MAJOR.MINOR.PATCH
```

được tooling kiểm tra dựa trên API diff.

Nhưng compiler không tự tuyên bố mọi change là semver-compatible chỉ vì version number.

---

# 185.95. Semver policy

Tooling có thể cảnh báo:

```text
API break without major version
```

nhưng package author chịu trách nhiệm release policy.

---

# 185.96. API stability levels

Có thể metadata:

```text
stable
experimental
deprecated
internal
```

để tooling hiểu maturity.

Không thay đổi type semantics.

---

# 185.97. Deprecation

```ax
@deprecated("use new_api")
pub fn old_api(...)
```

compiler cảnh báo.

Deprecation metadata thuộc `.axmeta`.

---

# 185.98. Removal

Deprecated API vẫn tồn tại cho tới khi package release thay đổi compatibility contract.

---

# 185.99. Binary cache

Artifact cache key dùng:

```text
SourceFingerprint
DependencyAPIFingerprint
CompilerSemanticVersion
Target
ABI
Features
ComptimeInputs
CodegenConfig
```

---

# 185.100. Implementation cache

Nếu chỉ implementation thay đổi:

```text
ImplementationFingerprint changed
PublicAPIFingerprint unchanged
```

dependents có thể reuse semantic metadata nhưng cần rebuild code nếu machine artifact phụ thuộc implementation.

---

# 185.101. Interface cache

`.axmeta` cho phép:

```text
package source
      ↓
public semantic interface
      ↓
.axmeta
      ↓
dependent compile
```

mà không cần source package.

---

# 185.102. LTO metadata

LTO có thể sử dụng:

```text
FunctionSummary
EffectSummary
AliasSummary
EscapeSummary
GenericSummary
ABI
Profile
```

nhưng dynamic boundary vẫn conservative.

---

# 185.103. Closed-world plugin

Nếu executable statically links plugin:

```text
closed world
```

LTO có thể optimize xuyên boundary.

---

# 185.104. Dynamic plugin

Nếu:

```text
dlopen(plugin)
```

thì:

```text
open world
```

và compiler không được assume toàn bộ target set.

---

# 185.105. Hot reload

Hot reload cần:

```text
stable ABI
stable state representation
function indirection
versioned plugin
```

Không phải Core language feature.

---

# 185.106. Hot reload and function pointers

Code address có thể thay đổi.

Do đó stable logical function identity phải khác machine address.

---

# 185.107. State migration

Nếu reload thay đổi:

```text
StateV1
→
StateV2
```

cần explicit migration:

```text
migrate(old_state) -> new_state
```

Compiler không tự đoán.

---

# 185.108. Plugin ownership

Plugin handle:

```text
Library
```

owns dynamic library.

Symbol/function capability phụ thuộc Library lifetime nếu platform yêu cầu.

---

# 185.109. Unload safety

Không được:

```text
drop(library)
call(plugin_fn)
```

nếu function capability còn phụ thuộc library.

Capability graph xử lý dependency này.

---

# 185.110. Reflection metadata lifetime

Runtime descriptor của loaded plugin phải không được sử dụng sau unload nếu descriptor nằm trong plugin image.

---

# 185.111. Copied metadata

Nếu cần descriptor sống độc lập:

```text
clone_metadata()
```

có thể copy metadata sang host-owned representation.

---

# 185.112. Metadata size

Runtime metadata phải có granular sections:

```text
TYPE
FIELD
TRAIT
METHOD
SERIALIZATION
PLUGIN
DEBUG
```

Linker chỉ giữ section được reference.

---

# 185.113. Section GC

Nếu:

```text
@reflect User
```

chỉ descriptor của `User` được giữ.

Không giữ toàn bộ type registry.

---

# 185.114. Reflection linker root

Reflection-preserved types trở thành linker roots.

Nhưng chỉ những declaration được annotate/reference.

---

# 185.115. Serialization

Serializer generated tại compile time có thể hoàn toàn không cần reflection runtime.

Ví dụ:

```text
User
 ↓
comptime
 ↓
encode_User()
decode_User()
```

---

# 185.116. Schema evolution

Serialization schema version là layer riêng:

```text
Type identity
≠
Wire schema identity
```

---

# 185.117. Wire compatibility

Thay đổi struct memory layout không nhất thiết phá serialized format.

Ngược lại, đổi serialized field ID có thể phá wire compatibility mà không thay memory layout.

---

# 185.118. Reflection ≠ serialization

Đây là distinction phải giữ:

```text
Reflection
Serialization
Debugging
ABI
```

là bốn contract khác nhau.

---

# 185.119. Runtime registry

Không có:

```text
global TypeRegistry
```

mặc định.

Nếu application muốn:

```text
TypeRegistry
```

library/runtime component tự tạo.

---

# 185.120. Startup overhead

Program không dùng reflection:

```text
startup = no reflection initialization
```

---

# 185.121. Binary-size consequence

Program không dùng:

```text
dyn Trait
Any
runtime reflection
dynamic loading
```

không phải trả overhead cho chúng.

---

# 185.122. Performance consequence

Compile-time reflection được erase sau generation.

Runtime reflection chịu runtime cost **chỉ khi programmer chọn nó**.

---

# 185.123. Security

Reflection không tự động expose:

```text
private memory
raw pointers
secret values
```

---

# 185.124. Secret metadata

`@secret`/constant-time contracts có thể ngăn compiler/tooling xuất metadata nhạy cảm ra runtime reflection.

---

# 185.125. Capability-aware reflection

Reflection API có thể yêu cầu:

```text
Reflection(Type)
Reflection(Layout)
Reflection(Private)
```

nhưng ordinary application chỉ có public metadata.

---

# 185.126. Compiler-generated descriptor

Conceptual:

```text
TypeDescriptor<User> {
    type_id
    name
    fields[]
    methods[]
    traits[]
}
```

Compiler generated, không phải user viết.

---

# 185.127. Descriptor ABI

Descriptor format phải versioned nếu truyền qua plugin boundary.

---

# 185.128. Plugin descriptor

Plugin có:

```text
PluginDescriptor
```

chứa ABI-compatible metadata.

Không nhất thiết sử dụng full compiler `.axmeta`.

---

# 185.129. `.axmeta` vs plugin metadata

```text
.axmeta
    ↓
compiler/IDE/AI/build

PluginDescriptor
    ↓
runtime loader
```

Plugin descriptor là subset/runtime-oriented representation.

---

# 185.130. Debug metadata

DWARF/PDB/dSYM vẫn là debug artifacts.

Không tái sử dụng chúng làm runtime reflection contract.

---

# 185.131. Source maps

Source mapping có thể nằm:

```text
.axmeta
debug artifact
```

tùy profile.

---

# 185.132. Reproducibility

Metadata generation phải deterministic:

```text
same source
same dependency graph
same compiler semantics
same target/config
→ same semantic metadata
```

trong reproducible mode.

---

# 185.133. Metadata privacy

Build có thể chọn:

```text
public metadata
private metadata
debug metadata
none
```

tùy artifact/profile.

---

# 185.134. Public binary package

Một binary library có thể phát hành:

```text
lib.axlib
lib.axmeta
```

mà không phát hành source.

---

# 185.135. Private implementation

`lib.axmeta` không cần chứa:

```text
private source
private implementation details
```

trừ metadata cần thiết cho approved optimization/ABI.

---

# 185.136. Optimization disclosure

Một library có thể chọn export:

```text
minimal metadata
optimization metadata
full compiler metadata
```

---

# 185.137. Trade-off

Full generic/LTO metadata:

```text
better optimization
larger artifact
more implementation disclosure
```

Minimal metadata:

```text
smaller
more ABI isolation
less cross-module optimization
```

---

# 185.138. Metadata profiles

Đề xuất:

```text
metadata=minimal
metadata=api
metadata=opt
metadata=full
```

---

# 185.139. AI metadata profile

Có thể có:

```text
metadata=ai
```

chứa semantic information hữu ích cho AI nhưng không nhất thiết chứa private implementation.

---

# 185.140. AI API

CLI:

```text
axc inspect api package
axc inspect type Type
axc inspect trait Trait
axc inspect abi Function
axc inspect effects Function
axc inspect metadata package
axc api-diff old.axmeta new.axmeta
```

---

# 185.141. Dynamic loading security

Dynamic library loading là external capability:

```text
DynamicLoad
```

không phải Core operation.

---

# 185.142. Plugin trust

Plugin không tự động được coi là safe Axiom code.

Có thể là:

```text
trusted Axiom ABI
C ABI
sandboxed process
WASM plugin
```

---

# 185.143. Process-isolated plugins

Nếu plugin không đáng tin cậy:

```text
Host
 ↓ IPC
Plugin Process
```

thay vì in-process dynamic loading.

Điều này tái sử dụng IPC model của BOOTSTRAP-184.

---

# 185.144. WASM plugin

WASM có thể là một plugin sandbox boundary.

Nhưng:

```text
WASM ABI
≠
Axiom ABI
```

phải có explicit adapter.

---

# 185.145. Reflection and WASM

WASM build không dùng runtime reflection vẫn giữ binary tối giản.

---

# 185.146. Runtime reflection and embedded

Embedded program thường không cần reflection.

Compiler có thể loại bỏ hoàn toàn metadata.

---

# 185.147. Kernel

Kernel profile không mặc định có:

```text
dynamic loading
reflection
filesystem
process runtime
```

---

# 185.148. GUI

GUI frameworks có thể sử dụng compile-time reflection:

```text
comptime
 ↓
widget metadata
 ↓
generated registration
```

thay vì universal runtime object system.

---

# 185.149. Scripting

Nếu cần scripting:

```text
ScriptValue
TypeDescriptor
CallRegistry
```

là library/runtime layer.

Không ép toàn bộ Axiom vào dynamic typing.

---

# 185.150. Final architecture

```text
                    AXIOM TYPE SYSTEM
                           │
            ┌──────────────┴──────────────┐
            │                             │
     Compile-time reflection       Runtime reflection
            │                             │
        Comptime                       Optional
            │                             │
       Generate code              TypeDescriptor
            │                     Any / dyn Trait
            ↓                     Plugin / Script
      Native zero-cost                    │
                                          ↓
                                  Optional runtime
```

---

# 185.151. Quyết định quan trọng nhất

Axiom **không đi theo hướng Java/.NET-style universal runtime metadata**.

Không có mặc định:

```text
Object
Type object
Global type registry
Universal GC
Universal runtime
Universal vtable
```

Thay vào đó:

```text
Static type
    ↓
Compile-time knowledge
    ↓
Erase
```

và chỉ khi programmer yêu cầu:

```text
Type
 ↓
runtime metadata
```

---

# 185.152. Các invariant đóng băng

### Metadata

- **AMETA-20** — Compile-time metadata is not runtime metadata.
- **AMETA-21** — Debug metadata is distinct from runtime reflection metadata.
- **AMETA-22** — `.axmeta` is not required to be embedded in executables.
- **AMETA-23** — Metadata identities use canonical semantic IDs.
- **AMETA-24** — Metadata generation is deterministic under reproducible builds.
- **AMETA-25** — Metadata does not alter program semantics.

### Reflection

- **AREFLECT-20** — Compile-time reflection is available without runtime reflection.
- **AREFLECT-21** — Runtime reflection is optional.
- **AREFLECT-22** — Runtime reflection must not impose mandatory overhead on programs that do not use it.
- **AREFLECT-23** — Reflection cannot bypass ownership, capability, Drop, or visibility rules.
- **AREFLECT-24** — Runtime type identity is distinct from memory address identity.
- **AREFLECT-25** — Opaque types may hide physical representation.
- **AREFLECT-26** — Runtime layout exposure requires an explicit representation contract.
- **AREFLECT-27** — Reflection metadata is granular and linkable independently.

### API

- **AAPI-20** — Public API identity is distinct from implementation identity.
- **AAPI-21** — API fingerprints are semantic, not textual.
- **AAPI-22** — Implementation-only changes do not invalidate unchanged public interfaces.
- **AAPI-23** — Public generic constraints are part of the API contract.
- **AAPI-24** — Public associated types/constants/functions are part of the API contract.
- **AAPI-25** — Private types cannot leak through public API without an explicit opaque contract.
- **AAPI-26** — Re-export does not create a new declaration identity.
- **AAPI-27** — Public visibility does not imply native symbol export.
- **AAPI-28** — Source compatibility and ABI compatibility are distinct.
- **AAPI-29** — API versioning cannot silently change semantic type identity.

### ABI / Plugin

- **AABIAPI-20** — Axiom ABI and C ABI are distinct contracts.
- **AABIAPI-21** — Default Axiom ABI need not be permanently stable across compiler generations unless explicitly versioned.
- **AABIAPI-22** — Stable plugin ABI requires an explicit versioned contract.
- **AABIAPI-23** — Dynamic loading is an open-world boundary.
- **AABIAPI-24** — Closed-world optimization may cross package boundaries when legally proven.
- **AABIAPI-25** — Dynamic boundaries require conservative assumptions.
- **AABIAPI-26** — Raw dynamic symbols cannot become arbitrary typed function calls in safe code.
- **AABIAPI-27** — Plugin/library lifetime constrains dependent function/symbol capabilities.

### Binary package

- **APKGAPI-20** — Binary packages must expose sufficient metadata for their declared consumption mode.
- **APKGAPI-21** — Generic downstream specialization requires corresponding generic metadata.
- **APKGAPI-22** — Multiple package versions have distinct semantic identities.
- **APKGAPI-23** — Feature configuration participates in artifact identity.
- **APKGAPI-24** — Target-specific APIs participate in target-specific interface fingerprints.
- **APKGAPI-25** — Documentation metadata is distinct from semantic API metadata.
- **APKGAPI-26** — Metadata disclosure level may be selected by artifact profile.

---

# Trạng thái kiến trúc sau BOOTSTRAP-185

Axiom hiện đã có một chuỗi khá hoàn chỉnh:

```text
Core Semantics
      ↓
Type / Trait
      ↓
Ownership / Capability
      ↓
MIR / Verification
      ↓
Effect / Alias / Escape
      ↓
Optimization
      ↓
ABI / LIR / Machine
      ↓
Object / Linker
      ↓
Runtime Composition
      ↓
OS / Process / IPC
      ↓
Metadata / Reflection / Plugin
```

Điểm đặc biệt là **không cần thêm Object Model** để đạt được những khả năng thường khiến ngôn ngữ phải có class/runtime lớn.

---

## BOOTSTRAP-186 — FFI, C ABI, Foreign Types & Safe Interoperability Boundary

Bước tiếp theo nên chốt **FFI thực sự ở mức hệ thống**.

Không chỉ `extern "C"` đơn giản, mà toàn bộ:

```text
Axiom
  ↕
C
  ↕
C++
  ↕
OS ABI
  ↕
System libraries
  ↕
GPU APIs
  ↕
WASM
```

bao gồm:

- ownership khi qua FFI
- callback
- function pointer
- opaque C types
- `void*`
- strings
- arrays/views
- struct/enum ABI
- allocator boundary
- error mapping
- thread/async FFI
- unwind boundary
- variadic functions
- ABI attributes
- dynamic libraries
- safe wrapper generation
- bindgen/comptime FFI generation
- cách Axiom gọi **hầu hết thư viện C mà không cần C/C++ compiler trong runtime/build cuối**
- và quan trọng nhất: **làm thế nào để FFI không phá vỡ toàn bộ ownership/capability verifier của Axiom**.