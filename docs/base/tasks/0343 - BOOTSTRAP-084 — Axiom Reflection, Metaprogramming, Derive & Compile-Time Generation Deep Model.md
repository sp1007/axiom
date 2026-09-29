# BOOTSTRAP-084 — Axiom Reflection, Metaprogramming, Derive & Compile-Time Generation Deep Model

**Trạng thái: FROZEN**

Mục tiêu của phần này là khóa một ranh giới rất quan trọng:

```text
Generic
Comptime
Reflection
Derive
Code Generation
Macro
Runtime Reflection
```

Axiom sẽ **không** đi theo hướng “mọi thứ đều là macro/procedural macro”. Thay vào đó:

> **Axiom dùng type system + comptime + typed generation làm nền tảng metaprogramming.**

Điều này đặc biệt phù hợp với mục tiêu AI-friendly: AI có thể tạo cấu trúc chương trình rất mạnh mà compiler vẫn hiểu được semantic graph thay vì phải xử lý một đống textual macro expansion.

---

# 1. Sáu khái niệm phải tách biệt

```text
Generic
    ↓
compile-time abstraction over types/values

Comptime
    ↓
execute Axiom code during compilation

Reflection
    ↓
inspect compiler-known semantic information

Derive
    ↓
compiler generates typed declarations/implementations

Code Generation
    ↓
materialize declarations/types/functions from compile-time computation

Runtime Reflection
    ↓
explicit runtime metadata
```

Không khái niệm nào được mặc định thay thế khái niệm khác.

---

# 2. Generic

Generic trả lời:

> “Một đoạn code có thể hoạt động với nhiều type/value khác nhau như thế nào?”

Ví dụ:

```ax
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

Generic không phải metaprogramming.

Compiler specialization/monomorphization xử lý nó.

---

# 3. Comptime

Comptime trả lời:

> “Chạy logic này ngay trong quá trình compile được không?”

Ví dụ:

```ax
const BUFFER_SIZE = 1024

comptime fn make_size(x: usize) -> usize {
    x * 4
}
```

Comptime sử dụng chính semantics của Axiom.

Không tạo một ngôn ngữ scripting thứ hai.

---

# 4. Reflection

Reflection trả lời:

> “Compiler biết gì về type/declaration này?”

Ví dụ conceptual:

```ax
comptime {
    let t = type_of(User)
    let fields = fields_of(t)
}
```

Kết quả là **compiler metadata**, không phải runtime object.

---

# 5. Derive

Derive trả lời:

> “Từ semantic structure hiện tại, compiler có thể tự tạo implementation chuẩn nào?”

Ví dụ:

```ax
@derive(Debug, Eq, Hash)
struct User {
    id: u64
    name: String
}
```

Compiler có thể generate:

```text
Debug implementation
Eq implementation
Hash implementation
```

mà programmer không phải viết tay.

---

# 6. Code generation

Code generation mạnh hơn derive.

Ví dụ compiler có thể materialize:

```text
struct GeneratedMessage
fn serialize(...)
fn deserialize(...)
impl ...
```

từ metadata hoặc comptime input.

Nhưng generated code phải trở lại pipeline bình thường.

```text
Generated HIR
      ↓
Resolver
      ↓
Type checking
      ↓
Ownership
      ↓
Capability
      ↓
MIR
      ↓
Verification
```

**Không có đường tắt.**

---

# 7. Đây là invariant cực kỳ quan trọng

Generated code không được coi là trusted chỉ vì:

```text
compiler generated it
```

Nó vẫn phải qua semantic verification.

Điều này đã phù hợp với:

```text
ACOMP
AVERIFY
```

---

# 8. Không dùng textual macro làm nền tảng

Axiom v1 **không cần** macro kiểu:

```text
#define ...
```

hoặc procedural macro thao tác token stream tùy ý.

Lý do:

```text
text → text → parse → parse lại → semantic ambiguity
```

không phù hợp với:

- compiler deterministic
- AI tooling
- diagnostics
- incremental compilation
- semantic caching.

---

# 9. Typed generation

Thay vì:

```text
string = "fn foo(...) ..."
emit(string)
```

Axiom ưu tiên:

```text
Declaration
Type
Function
Field
TraitImpl
Expression
```

ở dạng compiler-known semantic entities.

---

# 10. Không cho arbitrary AST mutation trong Core v1

Không có:

```text
modify arbitrary AST
modify arbitrary HIR
modify arbitrary MIR
```

từ user comptime code.

Điều này bảo vệ compiler architecture:

```text
Source
 ↓
AST
 ↓
HIR
 ↓
Typed HIR
 ↓
MIR
```

không bị một macro phá invariant giữa các tầng.

---

# 11. `Type` là comptime value

Axiom có thể xem:

```text
Type
```

là một compile-time value.

Ví dụ conceptual:

```ax
comptime fn type_name<T>() -> Str {
    name_of(T)
}
```

Không có nghĩa executable phải chứa runtime type object.

---

# 12. Runtime type object không mặc định tồn tại

Đây là distinction:

```text
comptime Type
```

vs

```text
runtime TypeInfo
```

Mặc định chỉ cái đầu tiên tồn tại.

Muốn runtime reflection:

```text
@reflect
```

hoặc cơ chế tương đương phải explicit.

---

# 13. Runtime reflection là optional

Ví dụ:

```ax
@runtime_reflect
struct User {
    id: u64
    name: String
}
```

Compiler có thể emit metadata.

Nếu không sử dụng:

```text
no metadata
no reflection runtime
no runtime cost
```

---

# 14. Reflection metadata không được gắn vào object

Không:

```text
struct User {
    ...
    hidden_type_pointer
}
```

Không có mandatory object header.

Metadata có thể nằm trong:

```text
.rodata
metadata section
separate .axmeta
external reflection artifact
```

tùy target/profile.

---

# 15. Reflection categories

Reflection nên chia:

```text
Type Reflection
Declaration Reflection
Field Reflection
Enum Reflection
Trait Reflection
Generic Reflection
ABI/Representation Reflection
Target Reflection
Source Metadata
```

Không phải mọi loại reflection đều tồn tại ở runtime.

---

# 16. Type reflection

Compiler có thể biết:

```text
kind
size
alignment
fields
variants
traits
generic parameters
representation
```

Ví dụ:

```ax
comptime {
    size_of(User)
    align_of(User)
}
```

---

# 17. Field reflection

Conceptual API:

```text
fields_of(User)
```

trả compiler metadata.

Mỗi field có thể có:

```text
name
type
visibility
attributes
offset-if-defined
```

Nhưng `offset` chỉ hợp lệ khi representation contract cho phép.

---

# 18. Default layout vẫn compiler-controlled

Nếu:

```ax
struct User {
    a: u8
    b: u64
}
```

reflection không được biến:

```text
offset_of(User.b)
```

thành một ABI contract vĩnh viễn.

Reflection phải phân biệt:

```text
current compiler fact
```

và:

```text
stable representation contract
```

---

# 19. `@repr(C)` + reflection

Khi:

```ax
@repr(C)
struct Foo {
    a: u32
    b: u64
}
```

representation metadata có thể được sử dụng cho FFI/code generation.

Nhưng:

```text
reflection ≠ repr contract
```

---

# 20. Enum reflection

Compiler có thể inspect:

```text
enum Color {
    Red
    Green
    Blue
}
```

và lấy:

```text
variants
variant names
payload types
attributes
```

Điều này rất hữu ích cho:

- serializers
- CLI generators
- GUI bindings
- documentation
- protocol generators.

---

# 21. Trait reflection

Có thể inspect:

```text
traits_of(T)
methods_of(Trait)
associated_types
associated_constants
```

Nhưng reflection không được phép bypass trait solver.

---

# 22. Generic reflection

Compiler có thể inspect:

```text
generic parameters
bounds
const parameters
associated constraints
```

nhưng generic constraints vẫn được resolver/trait solver xác minh.

---

# 23. Reflection không bypass visibility

Một module không thể dùng ordinary reflection để biến private API thành public API.

Compiler vẫn phân biệt:

```text
private
pub
@export
```

---

# 24. Comptime visibility

Có thể có quyền reflection ở compile time rộng hơn runtime.

Nhưng vẫn phải có rule rõ:

```text
private semantic information
```

không mặc định trở thành:

```text
public generated API
```

---

# 25. Derive compiler-known

Core compiler có thể hỗ trợ một registry:

```text
Debug
Clone
Eq
Hash
Default
```

hoặc các derive chuẩn tương ứng.

Mỗi derive có semantic definition.

---

# 26. Derive không phải magic text expansion

Ví dụ:

```ax
@derive(Eq)
struct Point {
    x: i32
    y: i32
}
```

Compiler tạo semantic implementation tương đương:

```text
Eq(Point)
```

sau đó verifier kiểm tra như code bình thường.

---

# 27. User-defined derive

V1 **không cần** cho phép package tùy ý đăng ký procedural derive compiler plugin.

Thay vào đó, trước tiên có:

```text
compiler-known derive
+
typed comptime generation
```

Sau này có thể mở rộng.

---

# 28. Tại sao không procedural macro v1?

Vì procedural macro thường tạo:

```text
compiler inside compiler
```

với:

- token manipulation
- hygiene
- expansion order
- recursive expansion
- opaque diagnostics
- version coupling
- incremental invalidation phức tạp.

Axiom không cần gánh tất cả ngay từ Core.

---

# 29. Comptime declaration generation

Axiom có thể cho phép một API kiểu:

```text
generate_struct(...)
generate_function(...)
generate_impl(...)
```

nhưng các declaration này là typed semantic entities.

Không phải raw source text.

---

# 30. Generated declarations có identity

Mỗi generated declaration cần có:

```text
DeclarationId
GenerationOrigin
SourceSpan/GeneratedSpan
GeneratorIdentity
InputFingerprint
```

để compiler có thể debug và cache.

---

# 31. Generation origin

Compiler phải biết:

```text
User source
Derived
Comptime generated
Imported generated
Compiler synthesized
```

Nguồn gốc này cực kỳ hữu ích cho diagnostics.

---

# 32. Diagnostics của generated code

Nếu generated implementation lỗi:

```text
error AX...
generated declaration failed type checking
```

compiler nên hiển thị:

```text
generated from:
foo.ax:42

generator:
@derive(...)
```

AI cũng có thể truy ngược origin.

---

# 33. Source mapping

Generated code phải có source mapping:

```text
Generated HIR
    ↓
Generator source
    ↓
Original user declaration
```

Không để programmer gặp:

```text
error line ??? generated_file.tmp
```

mà không biết tại sao.

---

# 34. Generation cycle

Compiler phải phát hiện:

```text
generate A
 ↓
requires B
 ↓
generate A
```

và reject deterministic.

Không chạy vô hạn.

---

# 35. Generation depth/resource limit

Comptime/generation cần giới hạn:

```text
execution steps
memory
generated declarations
recursion depth
artifact size
```

để tránh compiler denial-of-service.

Các giới hạn này là compiler/build policy, không phải language semantic ambiguity.

---

# 36. Comptime purity không bắt buộc

Axiom không thêm full effect system chỉ để phân loại:

```text
pure comptime
impure comptime
```

Thay vào đó dùng capability model đã frozen.

---

# 37. Comptime external effects

Đã có:

```text
ReadSource
ReadMetadata
ReadFilesystem
WriteGenerated
ExecuteTool
Environment
Network
Time
Random
```

Quyền nào được cấp thì generator mới có quyền đó.

---

# 38. Generated output phải reproducible khi profile yêu cầu

Nếu:

```text
deterministic build
```

thì generator không được tùy ý dùng:

```text
time
random
network
environment
```

mà không nằm trong explicit dependency/input model.

---

# 39. Generation cache

Cache key cần bao gồm:

```text
generator semantic fingerprint
input types
input values
reflected declarations
comptime dependencies
external capabilities/inputs
compiler semantic version
target/config
```

---

# 40. Không cache dựa trên textual output בלבד

Không nên:

```text
hash(source text only)
```

vì semantic dependency có thể thay đổi dù generator source không đổi.

---

# 41. Typed generation và incremental compilation

Ví dụ:

```text
User
 ↓
@derive(Debug)
 ↓
Generated Debug impl
```

Nếu User thay đổi field:

```text
User fingerprint changed
        ↓
derive invalidated
        ↓
Debug impl regenerated
```

Các package không liên quan không cần rebuild.

---

# 42. Reflection dependency tracking

Nếu comptime generator đọc:

```text
fields_of(User)
```

Compiler phải ghi:

```text
generator depends on User's field schema
```

Nếu chỉ đọc:

```text
type size
```

thì dependency có thể hẹp hơn.

---

# 43. Fine-grained dependency

Đây là điểm rất quan trọng cho compiler tốc độ cao.

Không:

```text
User changed
→ rebuild everything
```

mà:

```text
field schema changed
→ invalidate consumers of field schema
```

---

# 44. Generic + comptime

Hai cơ chế có thể phối hợp:

```ax
comptime fn make_array<T, N>() -> Type {
    ...
}
```

nhưng semantic order phải rõ:

```text
resolve generic parameters
        ↓
evaluate comptime
        ↓
materialize generated entity
        ↓
type-check
```

Không để generic/comptime tạo vòng lặp semantic không xác định.

---

# 45. Comptime-generated generic

Generator có thể tạo:

```text
generic struct
generic function
generic impl
```

nhưng generated generic phải được đưa vào GenericDB bình thường.

---

# 46. Generic specialization + generation

Pipeline:

```text
Generic Definition
       ↓
Generation
       ↓
Generic Instance
       ↓
Monomorphization
       ↓
Optimization
```

Không cần runtime generic metadata.

---

# 47. Compile-time computation không tự tạo runtime code

Ví dụ:

```ax
const X = expensive_computation()
```

sau compilation có thể chỉ còn:

```text
constant X
```

Comptime VM không được link vào executable.

---

# 48. Comptime generated helper cũng có thể biến mất

Nếu generated function chỉ phục vụ compile-time:

```text
comptime helper
```

thì nó không tồn tại runtime.

Nếu được materialize cho runtime:

```text
explicit runtime declaration
```

thì mới codegen.

---

# 49. Generated code vẫn zero-cost

Ví dụ derive serialization tạo:

```text
serialize(User)
```

compiler có thể inline/specialize/eliminate abstraction như code bình thường.

Không có “reflection runtime call” nếu không cần.

---

# 50. Static reflection preferred

Cho:

```text
serializer
ORM
GUI binding
RPC
CLI
shader metadata
```

Axiom ưu tiên:

```text
inspect at compile time
generate specialized code
```

thay vì:

```text
runtime reflection
→ lookup field
→ dynamic dispatch
```

---

# 51. Runtime reflection chỉ khi thật sự cần

Ví dụ:

```text
plugin system
debugger
dynamic scripting
editor
serialization of unknown types
```

có thể cần runtime metadata.

Khi đó programmer yêu cầu explicit.

---

# 52. Reflection metadata format

Compiler không nên hard-code một runtime reflection ABI duy nhất.

Có thể emit:

```text
Axiom metadata
C-compatible metadata
custom application metadata
external .axmeta
```

tùy use case.

---

# 53. `.axmeta`

`.axmeta` đã được chọn cho semantic interface metadata.

Nó có thể chứa:

```text
public declarations
types
traits
generic definitions
ABI contracts
representation contracts
comptime dependencies
reflection metadata
diagnostic/source mapping metadata
```

nếu build yêu cầu.

---

# 54. `.axmeta` không phải runtime library

Một executable nhỏ không dùng reflection:

```text
không cần embed toàn bộ .axmeta
```

Metadata có thể bị strip.

---

# 55. AI-friendly reflection

Đây là một trong những lợi ích lớn nhất.

AI tool có thể hỏi compiler:

```text
What fields does TypeId 42 have?
What trait implementations exist?
Why does this generic constraint fail?
What generated declaration depends on this field?
```

thay vì parse source thủ công.

---

# 56. Compiler semantic query

Architecture hiện tại đã có:

```text
CompilerDB
```

và query model.

Reflection nên dùng **chính query engine đó**.

Không xây một hệ reflection song song.

---

# 57. Reflection = controlled CompilerDB view

Conceptually:

```text
CompilerDB
   │
   ├── TypeDB
   ├── TraitDB
   ├── DeclarationDB
   ├── LayoutDB
   ├── AbiDB
   └── ComptimeDB
          ↓
     Reflection API
```

Chỉ expose những facts mà semantic rules cho phép.

---

# 58. Reflection không được mutate CompilerDB trực tiếp

Không:

```text
reflection.set_type(...)
reflection.delete_function(...)
```

CompilerDB vẫn được compiler kiểm soát.

Generation sử dụng explicit API.

---

# 59. Typed declaration builder

Nếu cần API nội bộ:

```text
StructBuilder
FunctionBuilder
FieldBuilder
EnumBuilder
ImplBuilder
```

thì output phải là:

```text
GeneratedDeclaration
```

chứ không phải arbitrary AST pointer.

---

# 60. Hygiene

Vì Axiom không dựa trên textual macro, vấn đề macro hygiene giảm mạnh.

Generated declarations vẫn có:

```text
module identity
DeclarationId
namespace
visibility
```

nên name collision có thể được compiler xử lý semantic.

---

# 61. Name collision

Nếu generator tạo:

```text
fn serialize(...)
```

mà declaration đã tồn tại:

```text
compile error
```

trừ khi API generation explicitly yêu cầu replace/merge và rule đó được định nghĩa.

Không có silent overwrite.

---

# 62. Namespace isolation

Generator nên có thể tạo declarations trong namespace được chỉ định.

Không mặc định inject hàng trăm symbol vào scope hiện tại.

---

# 63. Generated private helpers

Generator có thể tạo helper private.

Các helper đó:

```text
không xuất hiện public API
```

trừ khi explicitly exported.

---

# 64. Public API fingerprint

Generated public declarations phải ảnh hưởng:

```text
semantic fingerprint
```

Private generated implementation thì chỉ ảnh hưởng downstream khi public semantic contract thay đổi.

---

# 65. Derive stability

Compiler-known derive phải có semantic version.

Ví dụ compiler update làm thay đổi generated code nhưng không thay đổi public semantics:

```text
private cache invalidation
```

Nếu thay đổi ABI/public behavior:

```text
interface fingerprint changes
```

---

# 66. Attribute arguments

Derive có thể nhận typed arguments:

```ax
@derive(Serialize(format: Json))
```

thay vì:

```text
@derive("Serialize(Json)")
```

Typed attributes dễ kiểm tra và AI dễ sinh chính xác hơn.

---

# 67. Attribute registry

Đã frozen từ BOOTSTRAP-036:

```text
attribute name
namespace
kind
arguments
targets
semantic effect
strength
```

Derive registry phải dùng cùng hệ thống.

---

# 68. No arbitrary compiler plugin in Core

Không cho package bình thường:

```text
load compiler binary
mutate CompilerDB
inject backend pass
```

Đây là compiler extension/trusted tooling, không phải language feature.

---

# 69. Compiler extension sau này

Nếu sau này cần compiler plugin:

```text
trusted compiler extension
```

phải có versioned API.

Không để:

```text
compiler internals
```

trở thành package ABI.

---

# 70. Macro textual compatibility

Nếu Axiom cần import C-style macros hoặc generate C headers:

```text
system/FFI tooling
```

có thể xử lý.

Nhưng textual macro không trở thành Core metaprogramming model.

---

# 71. Build-time code generation

Một generator có thể tạo:

```text
.ax source
```

cho tooling.

Nhưng generated source nên được compiler quản lý như artifact:

```text
generated/
```

và dependency tracked.

---

# 72. Source generation vs typed generation

Hai loại khác nhau:

```text
Typed Generation
    compiler semantic entity

Source Generation
    produces source files
```

Typed generation ưu tiên trong Core.

Source generation phù hợp:

- external tools
- codegen interoperability
- generated bindings
- developer-visible artifacts.

---

# 73. Generated source phải được recompiled normally

Không có:

```text
"generated nên compiler tin"
```

Generated source:

```text
source
 ↓
parse
 ↓
resolve
 ↓
type
 ↓
verify
```

như source bình thường.

---

# 74. Reflection of generated entities

Generated declarations sau khi materialize trở thành compiler entities bình thường.

Generator khác có thể inspect chúng nếu dependency graph cho phép.

---

# 75. Generation order

Không phụ thuộc thứ tự file traversal.

Compiler phải xây dependency graph:

```text
Generator A
Generator B
Generator C
```

và thực thi theo dependency topology.

Independent generators có thể chạy parallel.

---

# 76. Deterministic parallel generation

Nếu A và B độc lập:

```text
A || B
```

phải cho semantic result tương đương:

```text
A → B
```

nếu không có dependency.

---

# 77. Generation conflict

Nếu A và B cùng tạo:

```text
Foo
```

compiler phải báo conflict deterministic.

Không phụ thuộc thread scheduling.

---

# 78. Comptime panic

Đã frozen:

```text
comptime panic
```

→ compiler diagnostic.

Không tạo runtime panic.

---

# 79. Comptime resource cleanup

Comptime cũng dùng:

```text
Drop
ownership
capability
```

Resource dùng trong compiler environment phải được cleanup deterministic.

---

# 80. Generated code safety

Generated code phải tuân:

```text
ownership
capability
Drop
Send
Share
async
GPU
FFI
```

nếu tương ứng.

Ví dụ generator tạo `mut_view` sai:

```text
generated code rejected
```

chứ không tự động trusted.

---

# 81. Generated GPU code

Generator có thể tạo GPU kernel.

Nhưng:

```text
generate
 ↓
GPU legality
 ↓
ownership/capability
 ↓
GPU verification
```

vẫn phải chạy.

Đã frozen:

```text
AGPU-97
```

---

# 82. Generated FFI

Bindings generator có thể tạo:

```text
extern "C"
@repr(C)
```

declarations.

Nhưng FFI audit vẫn phải kiểm tra:

```text
ABI
layout
ownership
calling convention
```

---

# 83. Serialization generator

Một ví dụ rất phù hợp:

```ax
@derive(Serialize, Deserialize)
struct User {
    id: u64
    name: String
}
```

Compiler/library có thể generate specialized serializer.

Không cần runtime reflection.

---

# 84. GUI generator

Có thể:

```ax
@derive(PropertyEditor)
struct Transform {
    position: Vec3
    rotation: Quat
}
```

Generator inspect fields rồi tạo editor metadata/code.

---

# 85. RPC generator

Protocol declaration có thể được inspect tại compile time:

```text
Service
 ↓
reflection
 ↓
generated client
 ↓
generated server
```

Không cần runtime dynamic dispatch nếu không cần.

---

# 86. Tensor/GPU generator

Axiom GPU ecosystem có thể dùng comptime để tạo specialized kernels:

```text
Tensor<T, shape>
 ↓
comptime shape analysis
 ↓
generate specialized kernel
 ↓
GPU verification
 ↓
native GPU code
```

Điều này rất phù hợp mục tiêu AI/GPU của Axiom.

---

# 87. Compile-time specialization

Không nhất thiết generate source.

Compiler có thể trực tiếp specialize:

```text
generic
+
const parameter
+
target facts
```

thành specialized MIR.

Đây thường tốt hơn source generation.

---

# 88. Distinguish specialization from generation

```text
Specialization
= compiler derives implementation from existing generic

Generation
= creates new semantic declarations
```

Không nhập hai khái niệm.

---

# 89. Comptime values

Comptime có thể tính:

```text
array sizes
lookup tables
constants
state machines
format descriptors
dispatch tables
```

và materialize thành static data.

---

# 90. Comptime-generated data

Ví dụ:

```text
comptime generate lookup table
```

có thể trở thành:

```text
.rodata
```

mà không cần runtime initialization.

---

# 91. Static initialization

Nếu generated constant có thể materialize:

```text
static data
```

thì compiler ưu tiên materialize trực tiếp.

Không tạo startup runtime code nếu không cần.

---

# 92. No hidden initialization runtime

Comptime không được âm thầm biến:

```text
const table
```

thành:

```text
runtime constructor
```

nếu semantics không yêu cầu.

---

# 93. Compile-time function execution

`comptime fn` dùng cùng:

```text
type system
ownership
Drop
capability
```

với runtime Axiom.

Điều này giảm số lượng semantic models compiler phải duy trì.

---

# 94. Comptime VM

Compiler có thể có:

```text
Comptime VM / interpreter
```

nhưng đây là compiler implementation.

Không link vào executable.

---

# 95. Comptime native execution

Về sau compiler có thể JIT/compile comptime code nếu nhanh hơn.

Điều này không thay đổi semantics.

```text
Interpreter
or
JIT
or
native helper process
```

đều phải cho cùng semantic result.

---

# 96. Security boundary

Comptime execution phải tiếp tục tuân:

```text
sandbox
capabilities
resource limits
determinism profile
```

Không được trở thành cách chạy arbitrary host program trong compiler.

---

# 97. AI integration

Axiom compiler nên expose machine-readable reflection/generation API.

AI agent có thể yêu cầu:

```text
inspect_type
inspect_trait
inspect_fields
inspect_abi
inspect_generated_code
explain_generation_dependency
```

và compiler trả semantic data.

---

# 98. AI không được trở thành compiler semantic oracle

AI có thể:

```text
generate code
choose API
inspect diagnostics
request reflection
```

nhưng compiler quyết định:

```text
type correctness
ownership
capability
ABI
concurrency
```

Đây là ranh giới cực kỳ quan trọng.

---

# 99. Final metaprogramming architecture

Axiom v1 sẽ có:

```text
                    ┌──────────────┐
                    │   Generic    │
                    └──────┬───────┘
                           │
                    type/value abstraction
                           │
                           ▼
┌──────────────┐    ┌──────────────┐
│  Reflection  │───▶│   Comptime   │
└──────────────┘    └──────┬───────┘
                           │
                     typed generation
                           │
                           ▼
                  ┌──────────────────┐
                  │ Generated HIR    │
                  └────────┬─────────┘
                           │
                           ▼
                 Normal semantic pipeline
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      Ownership       Capability          Type
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                     Verified MIR
```

Runtime reflection nằm **ngoài** đường mặc định:

```text
runtime reflection
       ↓
explicit metadata
       ↓
optional runtime support
```

---

# 100. Frozen Invariants — `AMETA-20..100`

**AMETA-20** — Generic abstraction and metaprogramming are distinct mechanisms.

**AMETA-21** — Comptime is Axiom execution performed during compilation.

**AMETA-22** — Comptime uses the ordinary Axiom semantic model.

**AMETA-23** — Comptime is not a second programming language.

**AMETA-24** — Reflection inspects compiler-known semantic information.

**AMETA-25** — Compile-time reflection is the default reflection model.

**AMETA-26** — Runtime reflection is optional and explicit.

**AMETA-27** — Compile-time `Type` does not imply a runtime type object.

**AMETA-28** — Runtime reflection metadata does not require object headers.

**AMETA-29** — Reflection does not alter semantic type identity.

**AMETA-30** — Reflection does not automatically create representation or ABI contracts.

**AMETA-31** — `size_of`, `align_of` and `offset_of` obey representation contracts.

**AMETA-32** — Default compiler-controlled layout remains non-stable unless explicitly contracted.

**AMETA-33** — Reflection respects visibility rules.

**AMETA-34** — Reflection cannot silently convert private declarations into public API.

**AMETA-35** — Trait reflection does not bypass the trait solver.

**AMETA-36** — Generic reflection does not bypass generic constraint checking.

**AMETA-37** — Enum reflection observes semantic variants, not arbitrary memory layout.

**AMETA-38** — Runtime metadata emission is explicit.

**AMETA-39** — Runtime reflection incurs no mandatory cost when unused.

**AMETA-40** — `derive` is typed semantic generation.

**AMETA-41** — Compiler-known derives are verified as ordinary semantic implementations.

**AMETA-42** — Derived implementations do not become trusted merely because the compiler generated them.

**AMETA-43** — Generated declarations re-enter normal semantic analysis.

**AMETA-44** — Generated declarations undergo type checking.

**AMETA-45** — Generated declarations undergo ownership verification.

**AMETA-46** — Generated declarations undergo capability verification.

**AMETA-47** — Generated declarations undergo concurrency verification where applicable.

**AMETA-48** — Generated GPU code undergoes GPU legality and semantic verification.

**AMETA-49** — Generated FFI declarations undergo FFI and ABI verification.

**AMETA-50** — Arbitrary AST mutation is not part of Core v1.

**AMETA-51** — Arbitrary HIR mutation is not part of Core v1.

**AMETA-52** — Arbitrary MIR mutation is not part of Core v1.

**AMETA-53** — Textual procedural macros are not the foundational metaprogramming mechanism.

**AMETA-54** — Typed generation is preferred over textual source generation.

**AMETA-55** — Source generation and typed generation are distinct mechanisms.

**AMETA-56** — Generated source is compiled through the ordinary compiler pipeline.

**AMETA-57** — Generated declarations possess compiler identities.

**AMETA-58** — Generated declarations retain generation provenance.

**AMETA-59** — Generated declarations participate in source/semantic mapping.

**AMETA-60** — Diagnostics may trace generated entities to their generator and originating source.

**AMETA-61** — Generation dependencies participate in incremental compilation.

**AMETA-62** — Reflection dependencies participate in incremental invalidation.

**AMETA-63** — Generation cache identity includes semantic inputs.

**AMETA-64** — Generation cache identity includes relevant comptime dependencies.

**AMETA-65** — External comptime inputs participate in cache identity.

**AMETA-66** — Generation must be deterministic under deterministic build profiles.

**AMETA-67** — Independent generators may execute in parallel.

**AMETA-68** — Parallel generation must be semantically equivalent to deterministic serial generation.

**AMETA-69** — Generation conflicts are diagnosed deterministically.

**AMETA-70** — Generation cycles are rejected deterministically.

**AMETA-71** — Comptime execution is subject to resource limits.

**AMETA-72** — Comptime execution remains subject to capability restrictions.

**AMETA-73** — Unsafe does not bypass comptime sandbox restrictions.

**AMETA-74** — Comptime panic produces compiler failure diagnostics, not runtime panic.

**AMETA-75** — Comptime resources obey ownership and deterministic cleanup semantics.

**AMETA-76** — Comptime execution does not imply runtime allocation.

**AMETA-77** — Comptime helpers disappear from runtime unless explicitly materialized.

**AMETA-78** — Compile-time generated constants may materialize directly as static data.

**AMETA-79** — Comptime does not imply runtime initialization code.

**AMETA-80** — Specialization and generation are distinct compiler operations.

**AMETA-81** — Generic specialization may occur without source generation.

**AMETA-82** — Generated generic declarations enter the normal generic subsystem.

**AMETA-83** — Generated public declarations affect public semantic fingerprints.

**AMETA-84** — Private generated implementation need not invalidate unrelated downstream users.

**AMETA-85** — `.axmeta` may contain reflection and semantic metadata when requested.

**AMETA-86** — Runtime artifacts need not embed complete compiler metadata.

**AMETA-87** — Reflection is implemented through compiler semantic data rather than an independent semantic database.

**AMETA-88** — Reflection cannot directly mutate compiler semantic state.

**AMETA-89** — Typed generation uses explicit compiler generation interfaces.

**AMETA-90** — Generated names participate in ordinary namespace and collision rules.

**AMETA-91** — Generated declarations do not silently overwrite existing declarations.

**AMETA-92** — Generated helpers may remain private unless explicitly exported.

**AMETA-93** — Compiler extensions are distinct from ordinary language metaprogramming.

**AMETA-94** — Untrusted packages cannot arbitrarily mutate compiler internals.

**AMETA-95** — Compiler extension APIs, if introduced later, require explicit versioned contracts.

**AMETA-96** — AI tooling may inspect and generate semantic structures but does not determine language semantics.

**AMETA-97** — Compiler semantic verification remains authoritative over AI-generated code.

**AMETA-98** — Metaprogramming mechanisms must preserve ownership, capability, ABI, concurrency, GPU, FFI and security invariants.

**AMETA-99** — Metaprogramming abstractions should be erased when their observable runtime semantics permit.

**AMETA-100** — Axiom metaprogramming is based on generic abstraction, comptime execution, reflection and typed generation rather than unrestricted macro expansion.

---

## Trạng thái kiến trúc hiện tại

Sau phần này, ranh giới compile-time của Axiom đã khá sạch:

```text
                 Axiom Program
                       │
        ┌──────────────┼──────────────┐
        │              │              │
      Generic       Comptime      Reflection
        │              │              │
        │              └──────┬───────┘
        │                     │
        │               Typed Generation
        │                     │
        └──────────────┬──────┘
                       ▼
                  Normal HIR
                       ▼
                  Normal MIR
                       ▼
                Verified MIR
```

Và đặc biệt **không cần đưa procedural macro vào Core v1**.

Điều này cũng giúp Axiom giữ được triết lý đã thống nhất từ đầu:

> **Ngôn ngữ có thể mạnh; nhưng programmer không phải gánh complexity của compiler.**

### Bước tiếp theo

**BOOTSTRAP-085 — Axiom SIMD, Vector, Matrix, Numeric Computing & Hardware Acceleration Model**

Phần này sẽ khóa một mảng quan trọng còn thiếu đối với mục tiêu **hiệu năng ≥ C/C++ và AI/GPU**:

- SIMD portable vs native SIMD
- vector types
- auto-vectorization
- alignment
- packed/unpacked vector
- mask/predicate
- horizontal operations
- matrix/vector primitives
- FMA
- saturating arithmetic
- integer overflow/vector semantics
- CPU feature dispatch
- AVX2/AVX-512/NEON/SVE/RVV
- runtime CPU detection
- compile-time target specialization
- tensor primitives
- CPU ↔ GPU abstraction boundary
- và quan trọng nhất: **làm thế nào để Axiom có SIMD mạnh mà không biến SIMD thành một mớ intrinsic khó dùng như C/C++.**