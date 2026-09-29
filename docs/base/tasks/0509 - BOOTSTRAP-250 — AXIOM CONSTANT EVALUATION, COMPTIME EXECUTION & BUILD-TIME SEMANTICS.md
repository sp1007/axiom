# BOOTSTRAP-250 — AXIOM CONSTANT EVALUATION, COMPTIME EXECUTION & BUILD-TIME SEMANTICS

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của task này là biến `const`/`comptime` từ một ý tưởng ngôn ngữ thành **một execution model mà compiler có thể triển khai trực tiếp**, đồng thời giữ nguyên triết lý:

> **Comptime mạnh, nhưng không trở thành một ngôn ngữ thứ hai.**

Axiom không nên có:
- macro language riêng;
- procedural macro language riêng;
- template language riêng;
- reflection language riêng;
- build-script language bắt buộc.

Thay vào đó:

> **Comptime là Axiom chạy trong compiler environment với một tập capability được kiểm soát.**

---

# 1. Ba chế độ execution

Axiom có đúng ba semantic execution modes:

```text
RUNTIME
COMPTIME
COMPILER-INTERNAL
```

### Runtime

Code chạy trong executable:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

### Comptime

Code chạy trong compiler:

```axiom
comptime fn make_value() -> i32 {
    42
}
```

### Compiler-internal

Các thuật toán compiler như:

```text
type checking
trait solving
layout
optimization
code generation
```

không phải Axiom program.

---

# 2. `const` và `comptime` khác nhau

Đây là distinction bắt buộc.

```axiom
const SIZE = 1024
```

nghĩa:

> Giá trị phải được xác định tại compile time.

Trong khi:

```axiom
comptime {
    generate_schema()
}
```

nghĩa:

> Thực thi Axiom code trong compiler environment.

---

# 3. `const` không phải macro

```axiom
const SIZE = 16
```

chỉ tạo một compile-time value.

Không sinh AST.

---

# 4. Comptime có thể sinh declaration

Ví dụ conceptually:

```axiom
comptime {
    generate_getters(Point)
}
```

có thể tạo:

```text
fn get_x(...)
fn get_y(...)
```

nhưng mechanism là **typed declaration generation**, không phải text replacement.

---

# 5. Không có textual macro trong Core v1

Không cho:

```text
generate("fn foo(...) {...}")
```

rồi parse lại như macro text.

Comptime generation phải đi qua compiler's typed representation.

---

# 6. Comptime pipeline

```text
Source
  ↓
Lexer
  ↓
Parser
  ↓
Resolution
  ↓
Typed HIR
  ↓
Comptime extraction
  ↓
Comptime VM
  ↓
Generated values/declarations
  ↓
HIR insertion
  ↓
Normal resolution
  ↓
Normal type checking
  ↓
Ownership/capability verification
```

---

# 7. Generated code không được bypass compiler

Nếu comptime tạo:

```text
struct Generated
```

thì declaration này vẫn phải qua:

```text
name resolution
type checking
trait solving
ownership verification
effect checking
ABI validation
```

---

# 8. Comptime VM

Compiler cần một execution engine riêng:

```text
ComptimeVM
```

Nó có thể bắt đầu bằng interpreter.

Sau này có thể:

```text
Interpreter
→ bytecode VM
→ optimized VM
→ native JIT
```

nhưng semantic behavior không thay đổi.

---

# 9. Không link ComptimeVM vào executable

Đây là invariant rất quan trọng.

Nếu program:

```text
const X = ...
```

thì compiler thực thi code đó.

Executable không chứa:

```text
ComptimeVM
```

trừ khi programmer explicitly sử dụng runtime interpreter/library.

---

# 10. Comptime uses ordinary Axiom semantics

Ví dụ:

```axiom
comptime fn factorial(n: u32) -> u32 {
    if n == 0 {
        1
    } else {
        n * factorial(n - 1)
    }
}
```

vẫn obey:

- type system;
- ownership;
- initialization;
- Drop;
- capability;
- effect;
- deterministic semantics.

---

# 11. Không có "comptime unsafe world"

Sai:

```text
comptime = compiler trusted
```

Đúng:

```text
comptime = Axiom semantics
           +
           compiler capability restrictions
```

---

# 12. Comptime ownership

Giá trị comptime vẫn có:

```text
Owned
Moved
Copied
Dropped
```

theo type semantics.

---

# 13. Comptime Drop

Nếu một comptime value sở hữu resource nội bộ, compiler phải cleanup deterministic.

Ví dụ:

```text
ComptimeBuffer
```

được Drop trong compiler environment.

Không có nghĩa runtime binary sẽ có buffer đó.

---

# 14. Comptime memory

Compiler VM có memory model riêng nhưng tương thích semantic model:

```text
Stack
Heap
Static
```

có thể là implementation detail của VM.

Program không được phụ thuộc vào địa chỉ vật lý của comptime memory.

---

# 15. Comptime pointer

Raw pointers vẫn unsafe.

Không có shortcut:

```text
comptime
→ unrestricted compiler memory
```

---

# 16. Comptime capabilities

Comptime external access được mô hình hóa bằng capability.

Baseline:

```text
ReadSource
ReadMetadata
```

---

# 17. Capability mở rộng

Các capability mạnh hơn:

```text
ReadFilesystem
WriteGenerated
ExecuteTool
Environment
Network
Time
Random
```

phải explicit.

---

# 18. Default sandbox

Comptime mặc định:

```text
no arbitrary filesystem
no network
no process execution
no environment dependency
no nondeterministic clock
no random entropy
```

trừ capability/profile cho phép.

---

# 19. Vì sao?

Nếu:

```axiom
const X = comptime read_file(...)
```

thì build có thể thay đổi chỉ vì filesystem thay đổi.

Do đó dependency phải được compiler biết.

---

# 20. Comptime input dependency

Mỗi external input tạo:

```text
ComptimeDependency
```

Ví dụ:

```text
source file
filesystem file
environment variable
tool output
network response
```

---

# 21. Build fingerprint

Artifact identity phải bao gồm:

```text
SourceHash
PackageHash
CompilerSemanticVersion
Target
Features
ComptimeInputs
ComptimeCapabilityPolicy
Profile
```

---

# 22. Network trong comptime

Không cấm tuyệt đối.

Nhưng phải explicit:

```text
Network capability
```

và build không còn mặc định hermetic.

---

# 23. Reproducible build

Trong reproducible mode:

```text
Time
Random
Network
Environment
```

bị hạn chế hoặc phải được cố định.

---

# 24. Hermetic build

Hermetic mode:

```text
external world = deny by default
```

Chỉ input nằm trong dependency graph được phép.

---

# 25. Offline build

Nếu comptime yêu cầu network mà network unavailable:

```text
build error
```

không fallback âm thầm sang dữ liệu khác.

---

# 26. Comptime cache

Compiler cache:

```text
ComptimeCache
```

key:

```text
FunctionSemanticFingerprint
Arguments
ComptimeDependencies
CompilerSemanticVersion
TargetRelevantFacts
CapabilityPolicy
```

---

# 27. Không cache theo source text đơn giản

Hai source khác nhau nhưng semantic equivalent có thể compiler optimize.

Tuy nhiên cache identity phải bảo đảm soundness; không dùng heuristic text hash đơn độc.

---

# 28. Cache result

Có thể cache:

```text
scalar value
aggregate value
Type information
generated declarations
metadata
```

---

# 29. Generated declaration cache

Nếu:

```text
generate_struct_schema(User)
```

không thay đổi:

compiler có thể reuse generated HIR.

---

# 30. Cache không thay đổi semantics

Cache hit và cache miss phải cho:

```text
identical semantic result
```

---

# 31. `const` evaluation

Constant evaluator xử lý:

```text
integer
float
bool
char
string literals
arrays
tuples
structs
enum values
generic constants
```

theo type rules.

---

# 32. Const expressions

Ví dụ:

```axiom
const N = 4 * 1024
```

compiler evaluate.

---

# 33. Const function

Một function được phép chạy comptime nếu semantic body đáp ứng comptime legality.

Có thể dùng:

```axiom
const fn ...
```

nhưng **không nên tạo thêm keyword nếu `comptime fn` đã đủ**.

Đề xuất:

```text
const = compile-time value requirement
comptime fn = compile-time executable function
```

---

# 34. Runtime function tại comptime

Một ordinary function có thể được compiler evaluate tại compile time nếu:

- semantics cho phép;
- arguments known;
- effects permitted;
- compiler có implementation.

Nhưng đây là **optimization**, không phải guarantee.

---

# 35. Guarantee boundary

```text
ordinary fn
→ compiler MAY fold

comptime fn
→ compiler MUST execute/resolve at compile time
```

---

# 36. Ví dụ

```axiom
fn square(x: i32) -> i32 {
    x * x
}

const A = square(4)
```

Compiler có thể fold.

Nhưng:

```axiom
comptime fn make_id() -> u64 { ... }
```

có compile-time guarantee.

---

# 37. Comptime evaluation failure

Ví dụ:

```axiom
const X = 1 / 0
```

→ compile-time diagnostic.

Không phải runtime panic.

---

# 38. Comptime panic

```axiom
comptime fn f() -> i32 {
    panic("bad")
}
```

→ compiler diagnostic.

---

# 39. ICE khác panic

Nếu compiler bug:

```text
ICE
```

khác:

```text
user comptime panic
```

Tooling phải phân biệt.

---

# 40. Comptime recursion

Được phép.

Compiler cần resource limits:

```text
max evaluation steps
max recursion depth
max memory
max generated declarations
max output size
```

---

# 41. Resource exhaustion

Nếu vượt limit:

```text
COMPTIME_LIMIT_EXCEEDED
```

Không phải compiler crash.

---

# 42. Deterministic limits

Compiler nên có predictable defaults và configuration.

---

# 43. Comptime concurrency

Compiler **có thể** parallelize independent comptime evaluations.

Nhưng semantic result phải deterministic.

---

# 44. Parallel execution

Ví dụ:

```text
A = comptime f()
B = comptime g()
```

Nếu không dependency:

```text
A || B
```

được compiler chạy parallel.

---

# 45. External effect ordering

Nếu:

```text
write_file(A)
write_file(B)
```

thứ tự observable thì compiler phải preserve.

---

# 46. Pure comptime

Pure computation có thể:

- cache;
- parallelize;
- memoize;
- fold;
- eliminate repeated evaluation.

---

# 47. Comptime effect system

Comptime reuse effect model:

```text
PURE
READ
WRITE
IO
PROCESS
NETWORK
...
```

nhưng domain là compiler environment.

---

# 48. Example

```text
ReadSource("foo.ax")
```

có:

```text
COMPTIME + READ_SOURCE
```

không phải runtime IO.

---

# 49. Generated file

```text
WriteGenerated(...)
```

có:

```text
COMPTIME + WRITE_GENERATED
```

---

# 50. Generated source không phải runtime asset

Nếu comptime tạo:

```text
generated.ax
```

đó là build artifact/input cho compiler, không phải runtime file trừ khi explicitly packaged.

---

# 51. Typed generation

Axiom preferred model:

```text
TypeBuilder
FunctionBuilder
EnumBuilder
StructBuilder
TraitBuilder
```

nhưng những builder này có thể là compiler-provided comptime APIs, không phải macro syntax.

---

# 52. Declaration representation

Conceptually:

```text
DeclarationSpec
```

chứa:

```text
name
visibility
type
generic parameters
attributes
body
```

---

# 53. Generated declaration identity

Generated declaration có stable semantic identity:

```text
GeneratedDeclId
```

dựa trên generation context.

---

# 54. Source provenance

Compiler phải biết:

```text
generated declaration
← comptime call
← source location
```

để diagnostic:

```text
generated function has type error
```

có thể trace ngược về generator.

---

# 55. Generated code diagnostics

Không chỉ:

```text
error at generated code
```

mà:

```text
generator source
→ generation site
→ generated declaration
→ failing semantic operation
```

---

# 56. Reflection

Compile-time reflection đọc compiler metadata.

Ví dụ conceptually:

```axiom
comptime fn fields<T>() -> ... {
    reflect(T).fields()
}
```

---

# 57. Reflection visibility

Reflection không được tự động phá visibility.

Private members chỉ visible nếu caller/compiler context có quyền.

---

# 58. Representation reflection

Compiler có thể expose:

```text
size_of
align_of
offset_of
field list
variant list
trait implementations
attributes
```

theo visibility/representation contract.

---

# 59. Runtime Type information

Compile-time reflection **không tạo runtime type object**.

Nếu cần runtime:

```text
TypeInfo
```

phải explicitly emit metadata.

---

# 60. `Type`

`Type<T>` là compile-time semantic value.

Không đồng nghĩa:

```text
runtime RTTI object
```

---

# 61. Type identity

Compiler có:

```text
TypeId
```

nhưng đây là compiler semantic ID.

Runtime `TypeId` là một abstraction khác.

---

# 62. Const generics

Baseline:

```axiom
struct Vec<T, const N: usize> {
    data: [N]T
}
```

Compiler phải evaluate `N`.

---

# 63. Const generic constraints

Ví dụ:

```text
N > 0
```

có thể là compile-time constraint.

Không cần runtime branch.

---

# 64. Const generic specialization

```text
Vec<T, 4>
Vec<T, 8>
```

có thể tạo specialized machine code.

---

# 65. Shape programming

Tensor:

```axiom
Tensor<f32, [2, 3, 4]>
```

shape có thể compile-time.

---

# 66. Units

Scientific computing:

```axiom
Quantity<f64, Meter>
```

được compile-time checked.

Không nhất thiết runtime overhead.

---

# 67. Comptime-generated methods

Ví dụ reflection có thể generate:

```text
serialize
deserialize
debug
hash
```

thay vì macro syntax.

---

# 68. `@derive`

`@derive` là compiler-known typed generation.

Ví dụ:

```axiom
@derive(Clone, Debug, Serialize)
struct User {
    id: u64
}
```

Compiler generate declarations qua cùng semantic pipeline.

---

# 69. Derive không phải magic unchecked

Generated implementations vẫn:

```text
resolve
type-check
trait-check
ownership-check
effect-check
```

---

# 70. Compiler-provided derive

Compiler có thể implement một số derive intrinsic:

```text
Copy
Clone
Eq
Hash
Debug
```

library có thể provide derive implementations khác.

---

# 71. Attribute evaluation

Attributes được parse độc lập.

Comptime/Compiler biết semantics sau resolution.

---

# 72. `@cfg`

`@cfg` khác comptime expression.

```text
@cfg(target_os = "windows")
```

loại declaration **trước semantic compilation của branch không phù hợp**.

---

# 73. Runtime `if`

```axiom
if condition { ... }
```

vẫn semantic runtime code nếu condition runtime.

---

# 74. Comptime `if`

Nếu condition compile-time:

```text
comptime if
```

không cần thêm syntax.

Có thể dùng:

```axiom
comptime {
    if condition {
        generate_a()
    } else {
        generate_b()
    }
}
```

---

# 75. Không thêm `#if`

Axiom không cần preprocessor.

---

# 76. Compile-time branch

Generated declaration selection:

```text
comptime {
    if size_of<T>() == 8 {
        ...
    }
}
```

---

# 77. Comptime loops

Ordinary:

```axiom
comptime {
    for field in reflect(T).fields() {
        ...
    }
}
```

Không cần macro-specific loop.

---

# 78. Comptime data structures

Có thể dùng:

```text
Vec
Map
String
Array
```

nhưng compiler implementation phải cung cấp efficient internal equivalents.

---

# 79. Comptime allocation

Allocation trong compiler VM không liên quan runtime allocation.

Compiler có thể garbage-collect **compiler VM memory internally** nếu cần.

Điều này không vi phạm:

> Axiom runtime không có mandatory GC.

---

# 80. Đây là distinction quan trọng

```text
Runtime language semantics:
    no mandatory GC

Compiler implementation:
    may use GC / arena / tracing internally
```

Compiler implementation freedom được giữ nguyên.

---

# 81. Comptime external resources

Nếu generator mở file:

```text
File
```

đó là compiler-side resource.

Ownership/Drop vẫn áp dụng.

---

# 82. No leaked compiler resource

Nếu comptime evaluation kết thúc:

```text
all compiler-side owned resources
→ deterministic cleanup
```

---

# 83. Comptime network response

Nếu network capability được bật:

response phải trở thành:

```text
build input
```

hoặc output phải explicitly materialized.

Không được hidden dependency.

---

# 84. Build graph integration

```text
Package Graph
     ↓
Comptime Dependency Graph
     ↓
Generated Artifacts
     ↓
CompilerDB
     ↓
Build Graph
```

---

# 85. Comptime-generated source

Nếu generated declaration phụ thuộc file `schema.json`:

```text
schema.json
→ fingerprint
→ generation
→ generated HIR
```

Schema đổi:

→ generator invalidated.

---

# 86. Fine-grained invalidation

Không invalidate toàn package nếu chỉ:

```text
schema field A
```

thay đổi mà generator dependency tracking có thể chứng minh phần khác unaffected.

---

# 87. Semantic dependency tracking

Compiler nên track:

```text
ComptimeDependency {
    input
    span/query
    fingerprint
}
```

---

# 88. Reflection query dependency

Nếu generator chỉ đọc:

```text
fields(User)
```

thì không nhất thiết invalidate vì thay đổi implementation body không liên quan.

---

# 89. Metadata dependency

Compiler metadata phải có dependency granularity.

---

# 90. Comptime and package boundaries

Generator có thể reflect public package API.

Private API chỉ nếu visibility permits.

---

# 91. Binary-only packages

`.axmeta` đủ metadata cho comptime consumer nếu API được publish.

Không cần source.

---

# 92. ABI-stable metadata

Stable ABI package phải publish đủ:

```text
types
layout contracts
functions
effects
ABI
attributes
```

cho permitted compile-time consumers.

---

# 93. Comptime and dynamic loading

Comptime cannot assume runtime-loaded plugin types exist.

Dynamic plugin reflection is runtime metadata territory.

---

# 94. Comptime and FFI

Comptime có thể inspect:

```text
extern declarations
repr(C)
ABI metadata
```

nhưng không tự động execute arbitrary foreign function.

---

# 95. Executing FFI at comptime

Mặc định:

```text
forbidden
```

trừ compiler-authorized deterministic tool/intrinsic contracts.

---

# 96. Vì sao?

Nếu:

```axiom
const X = extern_c_call()
```

compiler output có thể phụ thuộc:

- OS;
- environment;
- machine;
- external process.

Không deterministic.

---

# 97. Build tools

Nếu cần chạy compiler/tool:

```text
ExecuteTool
```

phải explicit capability.

Output được fingerprint.

---

# 98. Tool result identity

```text
ToolPath
ToolVersion
Arguments
Environment
InputFiles
Output
```

tham gia dependency identity tùy reproducibility policy.

---

# 99. No hidden shell

Comptime build execution không được mặc định:

```text
shell command string
```

Argument vector preferred.

---

# 100. Comptime security boundary

Comptime code có thể là third-party package.

Không được mặc định có:

```text
filesystem
network
process
```

authority.

---

# 101. Package capability declaration

Package có thể request:

```text
comptime capabilities:
    ReadSource
    ReadFilesystem
```

Build policy quyết định allow/deny.

---

# 102. User consent/policy

Compiler/build system có thể reject:

```text
package requests Network
```

nếu policy deny.

---

# 103. Capability escalation

Comptime function không được tự cấp thêm capability cho itself.

---

# 104. Unsafe không bypass sandbox

```axiom
unsafe {
    ...
}
```

không grant:

```text
Network
Filesystem
Process
```

authority.

---

# 105. Deterministic mode

Compiler có mode:

```text
--profile reproducible
```

với policy chặt.

---

# 106. Nondeterministic values

`Time`, `Random`, `Network` phải explicit.

---

# 107. Random in reproducible build

Có thể cho deterministic seed supplied by build.

Không dùng entropy ngoài hidden.

---

# 108. Comptime errors

Structured diagnostic:

```text
COMPTIME-E001
```

nên chứa:

```text
source location
call stack
evaluation step
capability
input dependency
```

---

# 109. Evaluation trace

Compiler tooling:

```text
ax explain comptime foo
```

có thể hiển thị:

```text
foo()
 ├─ reflect(User)
 ├─ fields()
 ├─ generate(...)
 └─ generated declaration #12
```

---

# 110. AI interface

AI có thể query:

```text
ComptimeValue
GeneratedDeclaration
ComptimeDependency
EvaluationTrace
CapabilityUse
```

nhưng không override compiler.

---

# 111. Comptime debugger

Compiler tooling có thể hỗ trợ:

```text
breakpoint
step
inspect value
inspect type
inspect generated declaration
```

nhưng đây là tooling, không phải language semantics.

---

# 112. Comptime stack trace

Phải preserve:

```text
source span
function
generation context
```

---

# 113. Generated source map

Generated declaration → generator source.

Điều này rất quan trọng cho AI-generated code.

---

# 114. Comptime + AI generation

AI có thể tạo:

```text
comptime generator
```

nhưng generated code vẫn phải pass verifier.

AI không trở thành trusted compiler stage.

---

# 115. Comptime + ownership verifier

Generated code:

```text
struct Foo { ... }
```

được verify bình thường.

Không có:

```text
generated code exemption
```

---

# 116. Comptime + effect verifier

Generator itself:

```text
Effects(generator)
```

được verify against capability policy.

Generated runtime function có effect summary riêng.

---

# 117. Generator effect ≠ generated effect

Ví dụ generator đọc schema:

```text
generator:
    COMPTIME + READ_FILESYSTEM
```

Generated serializer:

```text
runtime:
    READ/WRITE MEMORY
```

Không được trộn hai summary.

---

# 118. Comptime + target

Comptime chạy trên **host compiler environment**, nhưng có thể inspect target.

Phải phân biệt:

```text
Host
Target
```

---

# 119. Example

Cross compile:

```text
build machine = Linux x64
target = Windows ARM64
```

Comptime:

```text
host facts → compiler execution
target facts → target query
```

Không được nhầm.

---

# 120. Target-specific generation

```axiom
comptime {
    if target.os == Windows {
        ...
    }
}
```

được phép.

---

# 121. Target-dependent cache

Generated result phải include target-relevant facts.

---

# 122. Cross compilation correctness

Comptime code không được dùng host ABI như target ABI nếu query target layout.

---

# 123. `size_of<T>()`

Trong comptime generic context phải phụ thuộc **target layout** khi `T` sẽ runtime tồn tại trên target.

---

# 124. GPU comptime

Comptime có thể generate GPU kernels.

Nhưng generated kernel phải chạy:

```text
GPU legality verifier
```

---

# 125. GPU compile-time shape

Ví dụ:

```text
Tensor<T, [N,M]>
```

shape computation có thể hoàn toàn compile-time.

---

# 126. Comptime and shader generation

Không tạo shader text language riêng.

Axiom typed GPU declarations được generate.

---

# 127. Comptime and serialization

Một trong các use case chính:

```text
schema
→ comptime reflection
→ generated serializer
```

Không runtime reflection cần thiết.

---

# 128. Comptime and GUI

UI declaration metadata có thể generate:

```text
widget registration
routing
serialization
```

nhưng không cần runtime global registry.

---

# 129. Comptime and networking

RPC definitions:

```text
service declaration
→ generated client/server
```

qua typed generation.

---

# 130. Comptime and database

Schema:

```text
table metadata
→ generated typed queries
```

có thể compile-time verify.

---

# 131. Comptime and FFI

C headers có thể được represented by metadata generator/tool, nhưng generated bindings phải qua FFI verifier.

---

# 132. No mandatory build scripts

Comptime có thể cover nhiều build-time tasks.

Nhưng OS packaging/signing/resource compilation vẫn có thể cần external build tools.

Axiom không giả định mọi external process đều có thể thay bằng comptime.

---

# 133. Comptime package APIs

Thư viện có thể publish:

```text
comptime fn
comptime types
reflection helpers
derive providers
```

như ordinary package APIs.

---

# 134. Versioning

Comptime API là source API.

Thay đổi generator output có thể tạo semantic/API changes.

---

# 135. Generated declaration stability

Generated names phải deterministic.

Không dùng random IDs trong symbol names.

---

# 136. Hygiene

Typed generation tự nhiên tránh phần lớn macro hygiene problems.

Generated identifiers được compiler bind theo `DeclarationId`, không chỉ string substitution.

---

# 137. Name collision

Nếu generator tạo:

```text
fn serialize
```

và user đã có:

```text
fn serialize
```

resolver phải báo collision/ambiguity.

Không silently overwrite.

---

# 138. Namespace

Generated declaration được insert vào namespace xác định.

---

# 139. Circular generation

Generator A tạo declaration B, B trigger generator A:

compiler phải detect cycle.

---

# 140. Generation cycle

```text
GEN-A
 ↓
GEN-B
 ↓
GEN-A
```

→ diagnostic.

Không infinite recursion.

---

# 141. Reflection cycle

Type A references B references A không tự động là comptime cycle nếu metadata graph có thể resolve.

---

# 142. Comptime type construction

Compiler có thể expose typed APIs:

```text
make_struct(...)
make_function(...)
make_impl(...)
```

nhưng generated result phải be well-formed.

---

# 143. Well-formedness

Generator API nên reject impossible declarations early.

Ví dụ:

```text
invalid generic parameter
invalid visibility
duplicate field
```

---

# 144. Generated AST vs HIR

Đề xuất:

> Comptime generation produces **typed syntax/declaration IR**, not raw machine IR.

Không cho generator mutate MIR trực tiếp.

---

# 145. Vì sao không cho MIR mutation?

Nếu cho:

```text
comptime modify MIR
```

thì compiler trở thành open-ended metaprogramming system cực khó verify.

---

# 146. Core v1 boundary

Comptime được phép tạo:

```text
values
types
declarations
attributes
metadata
```

Không được arbitrary mutate:

```text
MIR
SSA
machine code
register allocation
linker
```

---

# 147. Compiler plugins

Compiler plugin không phải comptime.

Nếu sau này cần compiler extension:

```text
compiler plugin ABI
```

là một system/tooling layer riêng.

---

# 148. Comptime can call library code

Library code phải được compiled for comptime execution.

---

# 149. Dual-mode functions

Một function có thể có:

```text
runtime implementation
comptime evaluator
```

compiler có thể reuse same semantic function body.

---

# 150. Avoid duplicate languages

Không nên yêu cầu:

```text
runtime Axiom
comptime MacroLang
```

Thay vào đó:

```text
Axiom
+
Comptime environment
```

---

# 151. Comptime runtime library

Có thể có:

```text
std::comptime
```

chứa:

```text
reflection
generation
filesystem capability wrappers
build metadata
target information
```

---

# 152. Compiler intrinsic boundary

Một số API cần compiler support:

```text
size_of
align_of
offset_of
type_name
reflect
target_info
```

---

# 153. Intrinsics must have fallback semantics

Nếu intrinsic không available target:

compiler diagnostic hoặc library fallback.

---

# 154. Compile-time optimization

Compiler có thể evaluate ordinary pure function:

```text
const A = pure_fn(...)
```

nhưng không biến thành language guarantee nếu không declared comptime.

---

# 155. Constant folding vs comptime

```text
constant folding:
    optimizer optimization

comptime:
    semantic execution guarantee
```

Đây là distinction phải giữ.

---

# 156. Evaluation result materialization

Comptime result:

```text
42
```

có thể materialize thành runtime constant.

Không cần runtime code.

---

# 157. Generated static data

```text
const TABLE = comptime generate_table()
```

có thể emit:

```text
.rodata
```

trực tiếp.

---

# 158. Large generated data

Compiler có thể emit binary sections trực tiếp thay vì tạo source-level declarations.

Nhưng semantics vẫn phải defined.

---

# 159. Resource limits

Comptime phải có:

```text
StepLimit
MemoryLimit
RecursionLimit
GenerationLimit
ArtifactLimit
TimeLimit(optional)
```

---

# 160. Time limit

Compiler wall-clock timeout là implementation control, không phải semantic result.

Nếu timeout:

```text
build failed
```

không phải program semantics.

---

# 161. Deterministic resource limit

Step count ưu tiên hơn wall-clock cho reproducibility.

---

# 162. Floating point comptime

Comptime FP phải dùng defined target/semantic FP model.

Không được để host CPU silently change result nếu result is semantically target-dependent.

---

# 163. Integer comptime

Overflow obeys Axiom integer semantics:

```text
checked
wrapping
saturating
```

the same as runtime.

---

# 164. Comptime string

Unicode/string semantics giống runtime Axiom.

Compiler may internally optimize representation.

---

# 165. Comptime ownership and views

A `view<T>` cannot escape its comptime owner.

Generated runtime declaration cannot contain dangling comptime view.

---

# 166. Comptime-to-runtime boundary

Chỉ materializable values có thể cross boundary.

Ví dụ:

```text
comptime File
```

không thể trở thành runtime `File` object implicitly.

---

# 167. Explicit materialization

Compiler có thể serialize/emit data:

```text
comptime generated bytes
→ runtime static bytes
```

nhưng đây là explicit semantic transformation.

---

# 168. No capability leakage

Comptime:

```text
ReadFilesystem
```

không khiến runtime executable có filesystem authority.

---

# 169. No compiler-state leakage

Runtime không được truy cập:

```text
CompilerDB
SourceDB
ComptimeVM
```

trừ explicit tooling/runtime library.

---

# 170. Comptime security model

```text
Language semantics
        +
Capability policy
        +
Build trust policy
```

Ba tầng độc lập.

---

# 171. Trusted generator

Một generator có thể được đánh dấu trusted tool/package.

Nhưng generated code vẫn verify.

---

# 172. Untrusted generator

Không được cấp quyền mặc định.

---

# 173. Package lock integration

Comptime package dependencies phải được lock trong:

```text
axiom.lock
```

---

# 174. Generator reproducibility

Build system nên có:

```text
generator semantic fingerprint
```

để detect generator changes.

---

# 175. Compiler version

Compiler semantic version ảnh hưởng comptime result vì compiler reflection APIs có thể thay đổi semantics.

---

# 176. Reflection API version

Metadata/reflection schema cần versioned.

---

# 177. Backward compatibility

Một package compiled against older `.axmeta` cần compiler biết metadata version.

---

# 178. Generated artifact provenance

`.axmeta` có thể record:

```text
generated_by
generator fingerprint
inputs
target
compiler
```

---

# 179. AI provenance

AI-generated comptime code không có special semantic privilege.

Compiler chỉ thấy:

```text
Axiom source
```

và verify.

---

# 180. Final architecture

```text
                 ┌─────────────────────┐
                 │      Axiom Source   │
                 └──────────┬──────────┘
                            │
                     Parse / Resolve
                            │
                            ▼
                     Typed HIR / AST
                       │           │
                       │           │
                       ▼           ▼
                  Runtime       Comptime
                    HIR            HIR
                       │           │
                       │      Comptime VM
                       │           │
                       │      Reflection
                       │           │
                       │      Generation
                       │           │
                       │           ▼
                       │    Generated HIR
                       │           │
                       └──────┬────┘
                              ▼
                       Normal Verification
                              │
                              ▼
                        Verified MIR
                              │
                              ▼
                           OptIR
```

---

# 181. Compiler components

Thêm vào `CompilerDB`:

```text
ComptimeDB
ComptimeVM
ComptimeEvaluator
ComptimeDependencyDB
ComptimeCache
ReflectionDB
GenerationDB
GenerationProvenanceDB
```

---

# 182. Comptime query API

```text
EvaluateConst(expr)
EvaluateComptime(fn, args)
ReflectType(type)
GenerateDeclarations(generator)
ComptimeDependencies(item)
ComptimeEffects(item)
ComptimeFingerprint(item)
```

---

# 183. Core compiler invariant

```text
COMPTIME-20
Comptime uses Axiom semantic rules.

COMPTIME-21
Comptime is not a separate programming language.

COMPTIME-22
Const evaluation and comptime execution are distinct concepts.

COMPTIME-23
Comptime execution occurs in the compiler environment.

COMPTIME-24
Comptime execution does not imply runtime dependency.

COMPTIME-25
Comptime VM is not linked into runtime binaries by default.

COMPTIME-26
Comptime obeys type checking.

COMPTIME-27
Comptime obeys ownership semantics.

COMPTIME-28
Comptime obeys capability semantics.

COMPTIME-29
Comptime obeys effect semantics.

COMPTIME-30
Comptime cannot bypass safety verification.

COMPTIME-31
Comptime-generated code re-enters normal semantic verification.

COMPTIME-32
Generated code cannot directly mutate MIR or machine code.

COMPTIME-33
Textual macro substitution is not required by Core v1.

COMPTIME-34
Typed generation is the preferred metaprogramming mechanism.

COMPTIME-35
Compile-time reflection respects visibility.

COMPTIME-36
Compile-time reflection does not imply runtime reflection.

COMPTIME-37
Type metadata is compile-time data unless explicitly materialized.

COMPTIME-38
Comptime external capabilities are explicit.

COMPTIME-39
Comptime has sandboxed authority by default.

COMPTIME-40
Unsafe does not bypass comptime authority restrictions.

COMPTIME-41
External comptime inputs participate in dependency tracking.

COMPTIME-42
External comptime inputs participate in build identity.

COMPTIME-43
Comptime cache results must be semantically equivalent to cache misses.

COMPTIME-44
Cache identity includes all semantic dependencies.

COMPTIME-45
Comptime evaluation is deterministic for deterministic inputs.

COMPTIME-46
Compiler may parallelize independent comptime evaluations.

COMPTIME-47
Parallel comptime execution must preserve semantic determinism.

COMPTIME-48
Comptime evaluation cycles are detected.

COMPTIME-49
Comptime resource exhaustion produces structured diagnostics.

COMPTIME-50
Comptime panic is distinct from compiler ICE.

COMPTIME-51
Comptime memory is compiler execution memory.

COMPTIME-52
Comptime allocation does not imply runtime allocation.

COMPTIME-53
Comptime Drop is deterministic.

COMPTIME-54
Comptime capabilities cannot leak into runtime authority.

COMPTIME-55
Comptime-owned resources cannot escape into runtime implicitly.

COMPTIME-56
Comptime views cannot outlive their owners.

COMPTIME-57
Generated runtime values must have valid runtime representations.

COMPTIME-58
Generated declarations have compiler-tracked semantic identity.

COMPTIME-59
Generated declarations retain provenance to their generator.

COMPTIME-60
Diagnostics can trace generated code back to generation source.

COMPTIME-61
Generation name collisions are deterministic errors.

COMPTIME-62
Generation cycles are deterministic errors.

COMPTIME-63
Generated declarations participate in normal name resolution.

COMPTIME-64
Generated declarations participate in normal trait resolution.

COMPTIME-65
Generated declarations participate in normal ownership verification.

COMPTIME-66
Generated declarations participate in normal effect verification.

COMPTIME-67
Generated declarations participate in normal ABI verification.

COMPTIME-68
Comptime and runtime effect summaries are distinct.

COMPTIME-69
Comptime filesystem/network/process effects are not runtime effects.

COMPTIME-70
Host and target semantics are explicitly distinguished during comptime.

COMPTIME-71
Target-dependent compile-time layout uses target facts.

COMPTIME-72
Cross-compilation cannot silently substitute host layout for target layout.

COMPTIME-73
Comptime-generated GPU code is reverified under GPU legality rules.

COMPTIME-74
Comptime-generated FFI declarations are reverified under FFI rules.

COMPTIME-75
Comptime-generated serialization code is reverified under representation rules.

COMPTIME-76
Const generic values are compile-time validated.

COMPTIME-77
Const generic evaluation is deterministic.

COMPTIME-78
Constant folding is an optimization and is distinct from comptime guarantees.

COMPTIME-79
A comptime guarantee cannot be weakened into an optimizer-only behavior.

COMPTIME-80
An ordinary function may be constant-folded without becoming a comptime function.

COMPTIME-81
Comptime-generated static data may be emitted directly into runtime sections.

COMPTIME-82
Generated runtime data contains no implicit compiler authority.

COMPTIME-83
Comptime metadata is versioned.

COMPTIME-84
Comptime dependency changes invalidate affected generated results.

COMPTIME-85
Comptime dependency tracking is incremental where possible.

COMPTIME-86
Comptime results may be stored in compiler cache.

COMPTIME-87
Comptime cache invalidation is semantic, not timestamp-only.

COMPTIME-88
Comptime capability policy participates in build identity.

COMPTIME-89
Hermetic/reproducible builds may restrict comptime external capabilities.

COMPTIME-90
Network/time/random/environment dependencies are never hidden.

COMPTIME-91
Build-system policy may deny requested comptime capabilities.

COMPTIME-92
Third-party comptime code receives no implicit OS authority.

COMPTIME-93
AI-generated comptime code has the same semantic verification requirements as human-written code.

COMPTIME-94
Comptime tooling may expose evaluation traces.

COMPTIME-95
Comptime tooling cannot override semantic verification.

COMPTIME-96
Comptime semantics are independent of ComptimeVM implementation strategy.

COMPTIME-97
Compiler implementation may optimize comptime execution without changing results.

COMPTIME-98
Comptime failures are structured compiler diagnostics.

COMPTIME-99
Comptime semantics are part of the Semantic Oracle.

COMPTIME-100
A cache hit, interpreter execution, optimized VM execution, and future native comptime execution must produce observationally equivalent compile-time results.
```

---

# Một quyết định kiến trúc rất quan trọng đã được chốt

Với task này, Axiom về cơ bản **không cần macro system kiểu Rust/C++** để đạt khả năng metaprogramming mạnh.

Ta có:

```text
                Axiom
                  │
        ┌─────────┴─────────┐
        │                   │
     Runtime             Comptime
        │                   │
    ordinary code      ordinary Axiom
                            │
                 ┌──────────┼──────────┐
                 │          │          │
              Const    Reflection   Generation
                 │          │          │
                 └──────────┼──────────┘
                            │
                         Typed HIR
                            │
                       normal compiler
```

Điều này rất hợp với mục tiêu của Axiom:

> **Một ngôn ngữ duy nhất, một type system, một ownership model, một effect model, một verifier — nhưng compiler có thể chạy code trước runtime.**

Và quan trọng hơn, **compiler có thể phức tạp hơn rất nhiều mà programmer không phải học thêm một “macro language” thứ hai.**

---

## Task tiếp theo: **BOOTSTRAP-251 — AXIOM PATTERN MATCHING, DESTRUCTURING & EXHAUSTIVENESS ENGINE**

Task kế tiếp sẽ chốt phần còn lại của semantic frontend khá quan trọng:

```text
match
if let / pattern conditions
struct patterns
tuple patterns
enum patterns
array/slice patterns
binding modes
move/copy trong pattern
partial move
refutable/irrefutable pattern
guards
OR-patterns
range patterns
exhaustiveness
unreachable arms
pattern usefulness
pattern compiler → decision tree
```

Đặc biệt sẽ nối trực tiếp **Pattern Engine ↔ Ownership/Place Model ↔ Drop Verifier**, để `match` không trở thành một nguồn bug ownership/lifetime phức tạp.