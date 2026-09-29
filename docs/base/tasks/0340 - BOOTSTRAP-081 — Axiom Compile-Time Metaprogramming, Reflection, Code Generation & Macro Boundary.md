# BOOTSTRAP-081 — Axiom Compile-Time Metaprogramming, Reflection, Code Generation & Macro Boundary

**Trạng thái: FROZEN**

Mục tiêu của phần này là khóa một vấn đề rất quan trọng:

> Axiom cần metaprogramming đủ mạnh để xây thư viện lớn, derive, generic specialization, AI-generated code, serialization, bindings, DSL-like APIs… nhưng **không biến Core thành một ngôn ngữ macro thứ hai**.

Axiom sẽ đi theo hướng:

```text
                    Axiom Source
                         │
              ┌──────────┴──────────┐
              │                     │
           Runtime               Comptime
              │                     │
              │              ordinary Axiom code
              │                     │
              │               Type / Reflection
              │                     │
              │               Typed Generation
              │                     │
              └──────────┬──────────┘
                         ▼
                    Generated HIR
                         │
                         ▼
                 Normal Verification
                         │
                         ▼
                    Normal MIR
```

Không có pipeline kiểu:

```text
Source
 → macro magic
 → AST mutation
 → macro expansion
 → another macro
 → compiler-specific hacks
```

---

# 1. Ba cơ chế phải tách biệt

Axiom có ba cơ chế:

### `const`

Giá trị compile-time.

```ax
const MAX_SIZE: usize = 1024
```

### `comptime`

Thực thi code tại compile time.

```ax
comptime {
    ...
}
```

hoặc:

```ax
comptime fn make_value() -> usize {
    ...
}
```

### Reflection / Generation

Quan sát type/declaration và tạo ra **typed declarations/code**.

Đây là ba thứ khác nhau:

```text
const      = compile-time value
comptime   = compile-time execution
reflection = compile-time information
generation = compile-time creation
```

---

# 2. Comptime không phải ngôn ngữ thứ hai

Một `comptime fn` sử dụng:

```text
type system
ownership
Copy/Move
Drop
capability
generic
pattern
control flow
```

giống runtime Axiom.

Ví dụ:

```ax
comptime fn square(x: i32) -> i32 {
    x * x
}
```

Không cần học thêm một syntax riêng.

---

# 3. Nhưng comptime có Execution Environment riêng

Runtime:

```text
CPU / GPU / OS
```

Comptime:

```text
Compiler VM / Interpreter
```

Compiler VM **không được link vào executable** chỉ vì chương trình sử dụng comptime.

---

# 4. Comptime resource isolation

Comptime mặc định không được tùy tiện:

```text
read filesystem
write filesystem
execute process
network
environment
time
random
```

Muốn làm phải có capability.

Ví dụ khái niệm:

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

---

# 5. Sandbox

Mặc định:

```text
comptime = sandboxed
```

Đặc biệt:

```ax
unsafe
```

**không phá sandbox**.

Đây là hai hệ thống độc lập:

```text
unsafe
    = machine-level safety boundary

comptime capability
    = compiler external-effect permission
```

---

# 6. Comptime side effects

Nếu comptime được cấp:

```text
ReadFilesystem
```

thì file đã đọc trở thành một dependency của compilation.

Compiler phải biết:

```text
Source
 └─> comptime
      └─> input.json
```

để cache/incremental compilation không dùng kết quả cũ sai.

---

# 7. Comptime identity

Cache identity phải bao gồm ít nhất:

```text
source dependencies
package dependencies
compiler semantic version
target
configuration
features
comptime inputs
```

Do đó:

```text
same source
+
same dependencies
+
same comptime inputs
+
same semantic compiler
```

→ có thể reuse kết quả.

---

# 8. Reproducible comptime

Trong reproducible mode:

```text
Time
Random
Network
Environment
```

bị hạn chế hoặc phải được explicit input.

Mục tiêu:

```text
same inputs
→ same semantic output
```

---

# 9. `Type` là compile-time value

Reflection có thể biểu diễn:

```ax
Type
```

nhưng:

```text
Type
```

không phải mặc định là runtime object.

Ví dụ:

```ax
comptime fn inspect<T>() {
    let t: Type = type_of<T>()
}
```

Toàn bộ thông tin có thể biến mất sau compile.

---

# 10. Runtime reflection không mặc định tồn tại

Axiom không tự nhét:

```text
type metadata
field names
trait metadata
reflection tables
```

vào executable.

Nếu ứng dụng cần:

```text
runtime reflection
```

phải explicit yêu cầu metadata emission.

Ví dụ conceptual:

```ax
@emit_metadata
struct User {
    id: u64
    name: String
}
```

---

# 11. Reflection không phá visibility

Nếu:

```ax
struct User {
    private_secret: u64
}
```

reflection từ module khác không được tự động bypass:

```text
private
```

Visibility vẫn là semantic rule.

---

# 12. Representation reflection

Có thể query:

```ax
size_of<T>()
align_of<T>()
offset_of<T, field>()
```

nhưng kết quả phản ánh **representation contract hiện tại**.

Không được suy ra:

```text
default layout = stable ABI
```

---

# 13. Semantic type vs representation

Reflection phải phân biệt:

```text
Type identity
Representation
ABI
```

Ví dụ:

```ax
struct UserId(u64)
```

và:

```ax
type UserId = u64
```

có representation tương tự nhưng semantic identity khác nhau.

---

# 14. Typed generation

Axiom ưu tiên:

```text
typed generation
```

thay vì:

```text
generate source string
parse source string
```

Ví dụ `@derive` có thể yêu cầu compiler tạo:

```text
impl Eq for User
impl Hash for User
impl Debug for User
```

dưới dạng semantic declarations.

---

# 15. Generated code trở lại pipeline bình thường

Đây là invariant cực mạnh:

```text
Generate
   ↓
HIR
   ↓
Resolve
   ↓
Type Check
   ↓
Ownership
   ↓
Capability
   ↓
MIR
   ↓
Verify
```

Generated code **không được bypass compiler verification**.

---

# 16. AI-generated code cũng vậy

Đây là điểm đặc biệt quan trọng với mục tiêu AI-friendly của Axiom.

AI có thể tạo:

```ax
struct
trait
impl
comptime
generated declaration
```

nhưng compiler vẫn là authority:

```text
AI → proposes code
Compiler → decides semantics
```

AI không được trở thành semantic oracle.

---

# 17. `@derive`

Core v1 cho phép compiler-known derives:

```ax
@derive(Eq, Hash, Debug)
struct User {
    id: u64
    name: String
}
```

Compiler tạo implementation typed.

---

# 18. Derive không phải macro language

`@derive` là:

```text
compiler-known semantic transformation
```

không phải:

```text
arbitrary AST program
```

Điều này giúp:

```text
diagnostics
determinism
incremental compilation
IDE support
AI tooling
```

dễ hơn rất nhiều.

---

# 19. Derive phải deterministic

Cùng:

```text
type
attributes
compiler semantic version
configuration
```

phải sinh cùng semantic declarations.

---

# 20. Generated declaration identity

Generated declarations phải có identity ổn định dựa trên:

```text
origin declaration
generator identity
generator version/semantic identity
generation parameters
```

Không dựa vào memory address của compiler.

---

# 21. Generated source mapping

Compiler nên giữ:

```text
generated declaration
       ↓
generator
       ↓
origin source
```

để diagnostic có thể nói:

```text
error in generated implementation
generated from:
User.ax:42
```

thay vì chỉ báo lỗi ở file compiler-generated tạm thời.

---

# 22. No arbitrary IR mutation

Core v1 **không cho** user code tùy tiện sửa:

```text
AST
HIR
MIR
LIR
Machine IR
```

đang được compiler xử lý.

Không có:

```text
mutate_mir(...)
inject_instruction(...)
delete_basic_block(...)
```

trong comptime.

---

# 23. Vì sao?

Nếu cho phép:

```text
comptime → arbitrary MIR mutation
```

thì semantic pipeline sẽ thành:

```text
type checking
      ↓
???
      ↓
someone changed MIR
      ↓
verification
      ↓
???
```

Compiler khó:

- incrementalize;
- cache;
- debug;
- reason;
- verify;
- reproduce.

---

# 24. Generation boundary

Axiom đặt boundary:

```text
Comptime
    ↓
Generate typed declarations/expressions
    ↓
Compiler semantic pipeline
```

không:

```text
Comptime
    ↓
modify compiler internals
```

---

# 25. Text generation

Có thể hỗ trợ:

```text
WriteGenerated
```

để generator tạo file source.

Nhưng đây là **external build artifact**, không phải bypass semantic pipeline.

Ví dụ:

```text
schema.json
   ↓
comptime generator
   ↓
generated.ax
   ↓
normal parser/compiler
```

---

# 26. Generated source phải dependency-tracked

Nếu:

```text
schema.json
```

thay đổi:

```text
generated.ax
```

phải được invalidate.

Build graph phải biết:

```text
schema
 ↓
generator
 ↓
generated source
 ↓
compiler
```

---

# 27. Text generation không được là cách ưu tiên

Thứ tự ưu tiên:

```text
1. compile-time value
2. typed generation
3. generated source
4. external tool
```

Typed generation tốt hơn textual generation vì compiler hiểu trực tiếp semantic structure.

---

# 28. External tools

Comptime có thể được cấp:

```text
ExecuteTool
```

nhưng đây là capability mạnh.

Ví dụ:

```text
OpenAPI
protobuf
shader compiler
code generator
```

Có thể chạy tool ở build time.

---

# 29. Tool output phải tracked

Compiler/build system phải biết:

```text
tool
arguments
environment
inputs
outputs
```

để incremental/reproducible build.

---

# 30. Compiler không tin output mù quáng

Generated declaration:

```text
tool output
```

vẫn phải:

```text
parse
resolve
type-check
verify
```

---

# 31. Comptime panic

Nếu:

```ax
comptime fn generate() {
    panic("invalid schema")
}
```

thì đây là:

```text
compiler diagnostic
```

không phải runtime panic.

---

# 32. ICE khác comptime failure

Phân biệt:

```text
comptime user failure
```

với:

```text
compiler implementation failure
```

Ví dụ:

```text
ACOMPTIME-ERROR
```

vs:

```text
ICE
```

---

# 33. Comptime allocation

Comptime có thể sử dụng allocation trong compiler VM.

Nhưng:

```text
comptime allocation
```

không có nghĩa executable sẽ có:

```text
runtime heap
```

---

# 34. Comptime Drop

Comptime resource phải được cleanup trong:

```text
compiler execution environment
```

Không được leak resource compiler chỉ vì source program tạo object trong comptime.

---

# 35. Comptime ownership

Các quy tắc:

```text
Move
Copy
Clone
Drop
```

vẫn tồn tại.

Comptime không phải vùng:

```text
GC everything
```

---

# 36. Comptime capability

`view<T>` / `mut_view<T>` trong comptime vẫn tuân:

```text
ownership
lifetime
alias
```

Không được bypass bằng lý do:

```text
"nó chỉ chạy lúc compile"
```

---

# 37. Compile-time constant vs optimizer

Đây là distinction quan trọng:

```text
const/comptime
```

là semantic guarantee.

Optimizer constant-folding:

```text
x + 1
```

chỉ là implementation optimization.

Do đó:

```text
comptime value
```

phải có kết quả tại compile time.

---

# 38. Optimizer vẫn có thể làm mạnh hơn

Ví dụ:

```ax
const N = 1024

fn f(x: i32) -> i32 {
    x * N
}
```

Compiler có thể inline/fold.

Nhưng:

```text
const
```

không phụ thuộc optimizer.

---

# 39. Compile-time branching

Có thể:

```ax
comptime if condition {
    ...
}
```

hoặc cơ chế tương đương.

Semantics:

```text
branch không được chọn
→ không trở thành runtime code
```

Khác:

```ax
if condition
```

là runtime branch.

---

# 40. `@cfg` vs `comptime`

`@cfg`:

```text
compile-time configuration selection
```

Ví dụ:

```ax
@cfg(target_os = "windows")
...
```

`comptime`:

```text
compile-time computation
```

Không trộn hai cơ chế.

---

# 41. Generic specialization

Generic:

```ax
fn max<T: Ord>(a: T, b: T) -> T
```

có thể được specialize tại compile time.

Đây là:

```text
generic instantiation
```

không phải macro.

---

# 42. Compile-time type computation

Có thể:

```ax
comptime fn storage_type<T>() -> Type {
    ...
}
```

nhưng Core v1 không trở thành dependent type theorem prover.

Không cho:

```text
arbitrary proof language
```

---

# 43. Const generic

Core v1 giới hạn const parameter ban đầu:

```text
integer
bool
```

Ví dụ:

```ax
struct Array<T, N: usize> {
    ...
}
```

Không cần mở rộng ngay sang:

```text
arbitrary type-level functions
```

---

# 44. Reflection query model

Compiler nên hỗ trợ các query kiểu:

```text
type_of<T>
size_of<T>
align_of<T>
fields<T>
variants<T>
traits<T>
methods<T>
associated_types<T>
```

nhưng mỗi query có:

```text
visibility
representation
semantic availability
```

rules riêng.

---

# 45. Reflection result

Reflection metadata nên là strongly typed.

Ví dụ conceptual:

```ax
FieldInfo {
    name: Str
    type: Type
    index: usize
}
```

Không trả:

```text
JSON blob
```

làm primitive mặc định.

---

# 46. Field names

Tên field có thể được reflection compile-time query.

Nhưng compiler không đảm bảo tên field trở thành:

```text
runtime string
```

nếu không materialize.

---

# 47. Materialization

Nếu muốn:

```text
runtime field name
```

phải explicit materialize:

```text
compile-time string
→ runtime String/Str
```

Lúc đó binary size có thể tăng.

---

# 48. Runtime metadata

Có thể build:

```text
@emit_metadata
```

để tạo:

```text
type descriptors
field descriptors
enum descriptors
trait metadata
```

nhưng metadata emission là optional.

---

# 49. No mandatory reflection runtime

Một chương trình:

```ax
fn main() {
    print("hello")
}
```

không vì Axiom có reflection mà tự động chứa:

```text
type registry
RTTI database
reflection runtime
```

---

# 50. Dynamic reflection

Nếu ứng dụng cần:

```text
deserialize arbitrary type
plugin discovery
runtime inspector
scripting
GUI property editor
```

thì library/application layer có thể request metadata.

---

# 51. Reflection and private implementation

Compiler có thể biết mọi private declaration nội bộ.

Nhưng reflection API phải tuân visibility boundary.

Điều này ngăn:

```text
reflection
```

trở thành một cách phá encapsulation.

---

# 52. Reflection and ABI

Reflection không tự tạo ABI contract.

```text
fields<T>()
```

không có nghĩa field order stable.

Nếu cần ABI:

```ax
@repr(C)
```

hoặc representation contract tương ứng.

---

# 53. Reflection and unsafe

Reflection không biến invalid representation thành valid representation.

Ví dụ biết:

```text
size_of<Color>() == 1
```

không có nghĩa:

```text
mọi u8 đều có thể tạo Color
```

---

# 54. Generated code and ownership

Generator tạo:

```ax
fn process(x: String) ...
```

thì function đó vẫn có:

```text
Move semantics
Drop
Send/Share
```

Không có "generated code exemption".

---

# 55. Generated code and capabilities

Generator tạo:

```ax
fn mutate(x: mut_view<T>) ...
```

thì capability verifier xử lý như code viết tay.

---

# 56. Generated code and unsafe

Generator có thể sinh unsafe code nếu API cho phép.

Nhưng:

```text
generated unsafe
```

vẫn phải chịu unsafe contract.

Không được coi generated code là trusted compiler code.

---

# 57. Trusted compiler-generated code

Chỉ compiler-internal transformations như:

```text
Drop glue
Future state machine
closure environment
derive implementation
```

có thể được compiler xem là trusted transformation.

Nhưng kết quả semantic cuối cùng vẫn phải phù hợp specification.

---

# 58. Generated declarations vs compiler lowering

Phân biệt:

```text
User-visible generation
```

và:

```text
Compiler lowering
```

Ví dụ:

```text
async fn
```

→ compiler tạo Future state machine.

Đây không phải user macro.

---

# 59. Macro syntax

Core v1 **không đóng gói một procedural macro language**.

Không có:

```text
macro fn transform_ast(...)
```

trong Core.

---

# 60. Tại sao không?

Procedural macro dễ tạo:

```text
hidden semantics
poor diagnostics
slow compile
non-determinism
dependency complexity
version coupling
```

và đặc biệt không tốt cho mục tiêu:

```text
AI-readable compiler architecture
```

---

# 61. Có thể có macro sau này

Nếu sau này cần macro, nó phải là:

```text
separate language/tooling layer
```

không được âm thầm mở rộng Core semantics.

---

# 62. Declarative macros

Axiom có thể cân nhắc sau này một macro dạng:

```text
pattern → typed syntax
```

nhưng không freeze vào Core v1.

---

# 63. Why typed generation wins

So sánh:

```text
text macro
    ↓
string
    ↓
parser
```

với:

```text
typed generator
    ↓
Declaration/HIR
```

Cách thứ hai giúp compiler biết ngay:

```text
type
source
ownership
generic parameters
dependencies
```

---

# 64. Incremental compilation

Generator result phải có fingerprint.

Ví dụ:

```text
GenerateEq(User)
```

chỉ invalidate khi:

```text
User semantic definition
hoặc generator semantics
```

thay đổi.

Không cần rebuild toàn project.

---

# 65. Dependency graph

Comptime dependency:

```text
Axiom source
 ├── TypeDB dependency
 ├── package dependency
 ├── source file dependency
 ├── generated declaration dependency
 └── external input dependency
```

được CompilerDB theo dõi.

---

# 66. Parallel comptime

Hai generator độc lập:

```text
GenerateA
GenerateB
```

có thể chạy song song.

Nếu cùng ghi external output:

```text
dependency conflict
```

phải được build system xử lý deterministic.

---

# 67. No hidden global state

Comptime không nên có global mutable compiler state kiểu:

```text
global_counter++
```

để quyết định semantic output.

Điều này phá:

```text
parallelism
determinism
cache
```

---

# 68. Randomness

Nếu comptime dùng random:

```text
Random
```

thì seed/input phải trở thành dependency.

Không được:

```text
build 1 → generated X
build 2 → generated Y
```

mà compiler không biết tại sao.

---

# 69. Time

Nếu generator dùng:

```text
Time
```

thì reproducible build phải:

```text
reject
```

hoặc yêu cầu explicit supplied timestamp.

---

# 70. Environment

Không được implicit:

```text
if ENV_VAR == ...
```

và vẫn tuyên bố build hoàn toàn reproducible.

Environment dependency phải tracked.

---

# 71. Network

Network trong comptime là capability mạnh nhất.

Mặc định:

```text
OFF
```

Nếu bật:

```text
URL
request parameters
response/content hash
```

phải được build graph xem là external input.

---

# 72. Build security

Một dependency package không nên mặc định có quyền:

```text
execute arbitrary process
read private filesystem
network
```

chỉ vì nó có comptime code.

Capability phải được cấp theo build policy.

---

# 73. Package capability policy

Build system có thể quy định:

```text
comptime:
    ReadSource = allowed
    ReadMetadata = allowed
    ReadFilesystem = denied
    ExecuteTool = denied
    Network = denied
```

Project có thể override explicit.

---

# 74. Compiler itself remains deterministic

Ngay cả khi comptime có external effects, compiler vẫn phải ghi nhận:

```text
inputs
outputs
permissions
```

để diagnostics/cache/build graph rõ ràng.

---

# 75. Generated file lifecycle

Generated files có thể nằm trong:

```text
build/generated/
```

và không nên được coi là source root bình thường trừ khi build graph khai báo.

Compiler quản lý chúng.

---

# 76. Stale generated files

Nếu generator không còn được sử dụng:

```text
old generated artifact
```

không được vô tình compile chỉ vì file vẫn còn trên disk.

Build graph quyết định artifact nào thuộc compilation.

---

# 77. Comptime error provenance

Diagnostic nên lưu:

```text
generator source
comptime call site
external dependency
generated declaration
```

Ví dụ:

```text
Schema.ax:17
   ↓
generate()
   ↓
schema.json
   ↓
generated declaration
   ↓
type error
```

AI tooling có thể truy ngược chain này.

---

# 78. Reflection query performance

Reflection compile-time nên là compiler query:

```text
TypeDB
DeclarationDB
TraitDB
LayoutDB
```

thay vì mỗi lần tạo một metadata tree mới.

Compiler cache/interner có thể reuse.

---

# 79. No runtime Type objects by accident

Compiler không được lower:

```ax
Type
```

thành runtime struct chỉ vì source code có reflection.

Nếu programmer không materialize:

```text
Type
```

biến mất trước ABI lowering.

---

# 80. No mandatory RTTI

Không có:

```text
virtual type registry
dynamic cast
RTTI header
```

trong Core.

`dyn Trait` chỉ có metadata/vtable khi explicit.

---

# 81. Compile-time reflection can inspect traits

Có thể query:

```text
implements<T, Trait>
```

hoặc tương đương.

Nhưng trait solver vẫn là authority.

Reflection không tự tạo trait implementation.

---

# 82. Reflection cannot invent semantic facts

Ví dụ:

```text
reflection says field X exists
```

không có nghĩa:

```text
field X is Copy
```

trừ khi TypeDB xác nhận.

---

# 83. Reflection cannot bypass privacy

Tương tự:

```text
private field
```

không trở thành public chỉ vì generator biết nó tồn tại.

---

# 84. Reflection cannot bypass safety

Không thể:

```text
reflect raw pointer
→ assume valid
```

hoặc:

```text
reflect layout
→ create invalid value
```

---

# 85. Compile-time generated unsafe

Nếu generator tạo:

```ax
unsafe fn ...
```

compiler diagnostic phải chỉ rõ:

```text
generated by X
originated from Y
unsafe operation Z
```

để audit được.

---

# 86. Comptime execution domain

Compiler VM có execution domain:

```text
COMPTIME
```

không phải:

```text
CPU
GPU
```

Nếu generator tạo GPU code:

```text
comptime
    ↓
GPU source/declaration
    ↓
GPU semantic verification
    ↓
GPU backend
```

---

# 87. Generated GPU code

GPU code vẫn phải kiểm tra:

```text
storage domain
execution domain
capability
ownership
synchronization
GPU legality
```

Comptime không bypass AGPU rules.

---

# 88. Generated FFI declarations

Ví dụ generator đọc:

```text
C header
```

tạo:

```ax
extern "C" ...
```

Các declaration này vẫn phải qua:

```text
ABI validation
representation checks
FFI safety checks
```

---

# 89. Bindgen belongs above Core

Một tool kiểu:

```text
C header
→ Axiom declarations
```

là package/tooling layer.

Không cần nhét C parser vào language Core.

---

# 90. Schema generators

Các generator kiểu:

```text
JSON schema
protobuf
OpenAPI
SQL schema
GPU kernel metadata
```

nên là ecosystem/tooling.

Core chỉ cần:

```text
comptime
reflection
typed generation
```

đủ làm nền.

---

# 91. Serialization derive

Một ví dụ lý tưởng:

```ax
@derive(Serialize, Deserialize)
struct User {
    id: u64
    name: String
}
```

Compiler/package generator có thể tạo implementation.

Không cần runtime reflection.

---

# 92. Zero-cost derive

Nếu `Serialize` được specialize cho:

```text
User
```

thì compiler có thể tạo code trực tiếp:

```text
write u64
write UTF-8
```

không cần:

```text
field lookup by string
runtime reflection
virtual dispatch
```

---

# 93. AI-friendly semantic introspection

Compiler có thể cung cấp:

```text
axiom inspect type User
axiom inspect traits User
axiom inspect layout User
axiom inspect generated User
axiom explain comptime
```

để AI agent hiểu semantic state.

---

# 94. Compiler machine-readable generation graph

AI có thể query:

```text
User
 ├── derives Eq
 ├── derives Hash
 ├── generated impl Eq
 ├── generated impl Hash
 └── dependencies
```

Điều này phù hợp trực tiếp với kiến trúc `CompilerDB`.

---

# 95. Macro boundary

Ranh giới cuối cùng:

```text
                 ┌───────────────────────────┐
                 │       Language Core       │
                 │                           │
                 │ const / comptime / Type   │
                 │ reflection / generation  │
                 └─────────────┬─────────────┘
                               │
                               ▼
                         Typed HIR
                               │
                               ▼
                    normal semantic pipeline
                               │
                               ▼
                            MIR
```

Không có:

```text
user → arbitrary MIR mutation
```

---

# 96. Future extension boundary

Nếu sau này Axiom cần:

```text
procedural macros
DSL compiler
custom syntax
compiler plugins
```

chúng phải nằm **ngoài Core v1**.

Có thể tạo:

```text
Axiom Macro SDK
Axiom Compiler Plugin SDK
```

nhưng đây là versioned tooling API, không phải language semantic primitive.

---

# 97. Compiler plugin không được phá verifier

Ngay cả plugin/compiler extension trong tương lai cũng không được:

```text
inject unverified machine semantics
```

Boundary cuối cùng vẫn là:

```text
Verified MIR
```

---

# 98. Semantic authority

Thứ tự authority:

```text
Language Specification
        ↓
Semantic verifier
        ↓
Compiler implementation
        ↓
Optimization
        ↓
Backend
```

Không:

```text
macro/plugin
        ↓
override language semantics
```

---

# 99. Core principle

Toàn bộ BOOTSTRAP-081 có thể cô đọng thành:

> **Axiom metaprogramming generates semantic objects, not compiler mutations.**

Và:

> **Generated code is ordinary Axiom code after generation.**

Đây là điểm giúp Axiom vừa mạnh vừa giữ được compiler architecture sạch.

---

# 100. Frozen Invariants — `AMETA-20..100`

**AMETA-20** — `const` represents compile-time values.

**AMETA-21** — `comptime` represents compile-time execution.

**AMETA-22** — Reflection represents compile-time semantic information.

**AMETA-23** — Typed generation represents compile-time creation of semantic declarations.

**AMETA-24** — Comptime uses Axiom type semantics.

**AMETA-25** — Comptime uses Axiom ownership semantics.

**AMETA-26** — Comptime uses Axiom Drop semantics.

**AMETA-27** — Comptime uses Axiom capability semantics.

**AMETA-28** — Comptime is not a second programming language.

**AMETA-29** — Comptime execution uses a compiler execution environment.

**AMETA-30** — Comptime execution environment is not linked into runtime programs.

**AMETA-31** — Comptime external effects are capability-gated.

**AMETA-32** — Comptime is sandboxed by default.

**AMETA-33** — `unsafe` does not bypass the comptime sandbox.

**AMETA-34** — Comptime external inputs participate in dependency tracking.

**AMETA-35** — Comptime cache identity includes semantic compiler identity.

**AMETA-36** — Comptime cache identity includes target/configuration where relevant.

**AMETA-37** — Comptime cache identity includes external inputs where relevant.

**AMETA-38** — Reproducible builds restrict uncontrolled comptime environmental effects.

**AMETA-39** — Comptime may execute independently parallelizable work concurrently.

**AMETA-40** — Comptime semantics remain deterministic for identical declared inputs.

**AMETA-41** — `Type` is a compile-time semantic value by default.

**AMETA-42** — Compile-time reflection does not imply runtime metadata.

**AMETA-43** — Runtime reflection requires explicit metadata materialization.

**AMETA-44** — Reflection respects visibility.

**AMETA-45** — Reflection respects representation contracts.

**AMETA-46** — Reflection does not establish ABI compatibility by itself.

**AMETA-47** — `size_of`, `align_of`, and `offset_of` are compile-time queries.

**AMETA-48** — Reflection cannot manufacture invalid values.

**AMETA-49** — Reflection cannot bypass ownership verification.

**AMETA-50** — Reflection cannot bypass capability verification.

**AMETA-51** — Reflection cannot bypass type invariants.

**AMETA-52** — Generated declarations are typed semantic entities.

**AMETA-53** — Generated declarations re-enter normal name resolution.

**AMETA-54** — Generated declarations re-enter normal type checking.

**AMETA-55** — Generated declarations re-enter ownership verification.

**AMETA-56** — Generated declarations re-enter capability verification.

**AMETA-57** — Generated declarations re-enter ABI verification where applicable.

**AMETA-58** — Generated declarations cannot bypass MIR verification.

**AMETA-59** — `@derive` is a compiler-known typed generation mechanism.

**AMETA-60** — Derive generation is deterministic.

**AMETA-61** — Generated declaration identity is stable and origin-aware.

**AMETA-62** — Generated code retains source provenance.

**AMETA-63** — Generated code diagnostics retain generator provenance where practical.

**AMETA-64** — Arbitrary user modification of AST/HIR/MIR/LIR is not Core v1 functionality.

**AMETA-65** — Comptime cannot arbitrarily mutate compiler IR.

**AMETA-66** — Textual source generation is distinct from typed generation.

**AMETA-67** — Generated source participates in the build dependency graph.

**AMETA-68** — Stale generated files do not become compilation inputs implicitly.

**AMETA-69** — External tool execution is capability-gated.

**AMETA-70** — External tool inputs and outputs are dependency-tracked.

**AMETA-71** — External tool output does not bypass semantic verification.

**AMETA-72** — Comptime panic is a compile-time diagnostic.

**AMETA-73** — Comptime failure is distinct from compiler implementation failure.

**AMETA-74** — Comptime resources are cleaned in the compiler execution environment.

**AMETA-75** — Comptime allocation does not imply runtime allocation.

**AMETA-76** — Comptime values cannot implicitly escape into runtime without materialization.

**AMETA-77** — Compile-time branching does not imply runtime branching.

**AMETA-78** — `@cfg` is configuration selection, distinct from general comptime computation.

**AMETA-79** — Generic specialization is compile-time semantic specialization, not macro expansion.

**AMETA-80** — Const generics are initially restricted to supported scalar domains.

**AMETA-81** — Axiom v1 does not require dependent-type theorem proving.

**AMETA-82** — Reflection queries use compiler semantic databases as their authority.

**AMETA-83** — Reflection results are strongly typed.

**AMETA-84** — Runtime metadata is emitted only when explicitly requested.

**AMETA-85** — Axiom has no mandatory RTTI runtime.

**AMETA-86** — Axiom has no mandatory reflection registry.

**AMETA-87** — Generated unsafe code remains subject to unsafe contracts.

**AMETA-88** — Generated GPU code is reverified against GPU semantics.

**AMETA-89** — Generated FFI declarations are reverified against FFI/ABI contracts.

**AMETA-90** — Generated async code preserves async ownership/lifetime semantics.

**AMETA-91** — Generated code cannot manufacture Send/Share facts.

**AMETA-92** — Generated code cannot manufacture aliasing facts.

**AMETA-93** — Generated code cannot manufacture safety facts.

**AMETA-94** — Compiler-generated lowering is distinct from user metaprogramming.

**AMETA-95** — Future macro systems must not bypass the Verified MIR boundary.

**AMETA-96** — Compiler plugins, if introduced later, are not Core v1 semantics.

**AMETA-97** — Semantic authority remains with the language specification and verifier.

**AMETA-98** — Optimization cannot change the semantic result of comptime generation.

**AMETA-99** — Metaprogramming should disappear from runtime unless its result is explicitly materialized.

**AMETA-100** — Axiom metaprogramming generates semantic objects rather than arbitrary compiler-state mutations.

---

## Một kết quả rất đáng chú ý

Sau BOOTSTRAP-081, Axiom đã có một mô hình khá hoàn chỉnh:

```text
             PROGRAMMER / AI
                    │
                    ▼
              Axiom Source
                    │
          ┌─────────┴─────────┐
          │                   │
       Runtime             Comptime
          │                   │
          │          Reflection / Generate
          │                   │
          │                   ▼
          │             Typed HIR
          │                   │
          └─────────┬─────────┘
                    ▼
              Semantic Pipeline
                    │
                    ▼
                  MIR
                    │
                    ▼
              Verified MIR
                    │
                    ▼
                 OptIR
                    │
                    ▼
             ABI / LIR / Machine
```

Điểm này đặc biệt phù hợp với mục tiêu **AI-friendly language** của Axiom: AI có thể sinh code, introspect type, tạo implementation, generate binding/schema/GPU/serialization code… nhưng **không cần AI phải hiểu hoặc điều khiển trực tiếp compiler internals**.

### Chuỗi kiến trúc tiếp theo

Sau 081, phần hợp lý nhất là:

**BOOTSTRAP-082 — Axiom SIMD, Vector, Tensor & Numeric Computing Model**

Phần này sẽ khóa luôn một vấn đề lớn còn lại của mục tiêu Axiom: **CPU SIMD + GPU + tensor/ML + numeric types**, đồng thời quyết định cách Axiom đạt hiệu năng kiểu C/C++ mà không biến ngôn ngữ thành một tập intrinsic khó dùng.