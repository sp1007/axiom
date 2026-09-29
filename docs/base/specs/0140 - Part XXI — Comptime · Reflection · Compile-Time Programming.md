# Part XXI — Comptime · Reflection · Compile-Time Programming

Mục tiêu của phần này là làm Axiom có **metaprogramming mạnh**, nhưng không rơi vào tình trạng:

- macro language thứ hai;
- compiler plugin tùy ý phá compiler;
- build script có toàn quyền máy;
- compile-time code có semantics khác runtime;
- compiler build không reproducible;
- programmer phải học một hệ thống ownership khác.

Nguyên tắc:

> **Compile-time is another execution phase, not another language.**

Và:

> **Comptime uses the same type system, ownership model, and semantic verifier as runtime code.**

---

# XXI.1. Ba loại compile-time construct

Axiom phân biệt rõ:

```text
const
comptime
reflection
```

### `const`

Tính giá trị compile-time đơn giản:

```axiom
const MAX_USERS: usize = 1024
```

### `comptime`

Chạy code tại compile-time:

```axiom
comptime fn make_table() -> Array<u32, 256> {
    ...
}
```

### Reflection

Cho phép chương trình **quan sát metadata của type/program** tại compile-time:

```text
fields(T)
methods(T)
variants(T)
type_name(T)
size_of(T)
align_of(T)
```

Ba cơ chế này không nên trộn lẫn.

---

# XXI.2. `const` không phải `static`

Ví dụ:

```axiom
const SIZE: usize = 1024
static BUFFER: Array<u8, 1024> = ...
```

Khác nhau:

```text
const
 └── compile-time value
     └── không có storage identity bắt buộc

static
 └── runtime storage
     └── có storage identity
```

Compiler có thể inline `const` hoàn toàn.

`static` có thể có địa chỉ observable.

Do đó:

> `const` không phải một biến runtime được tối ưu hóa.

---

# XXI.3. `comptime fn`

Ví dụ:

```axiom
comptime fn square(x: u64) -> u64 {
    x * x
}

const X = square(12)
```

Compiler thực hiện:

```text
parse
  ↓
type check
  ↓
MIR
  ↓
comptime execution
  ↓
result
  ↓
runtime MIR
```

Kết quả có thể trở thành constant:

```text
144
```

---

# XXI.4. Comptime dùng cùng Type System

Ví dụ này phải hợp lệ:

```axiom
comptime fn make() -> Vec2 {
    Vec2 {
        x: 1.0,
        y: 2.0
    }
}
```

Không cần một kiểu:

```text
ComptimeVec2
```

riêng.

Tương tự:

```text
ownership
Copy
Move
Drop
Result
Option
trait
generic
```

đều có semantics thống nhất.

---

# XXI.5. Comptime Ownership

Đây là điểm rất quan trọng.

Comptime vẫn có:

```text
OWNED
MOVED
DROPPED
```

Ví dụ:

```axiom
comptime fn build() {
    var x = Buffer.alloc(...)
    ...
}
```

Nếu `Buffer` là resource compile-time, nó vẫn phải được cleanup đúng semantics.

Compiler không được có một loophole:

```text
"vì đang compile nên memory không cần quản lý"
```

---

# XXI.6. Compile-Time Resource

Tuy nhiên cần phân biệt:

```text
compile-time resource
runtime resource
```

Ví dụ:

```axiom
comptime {
    let file = source.open(...)
}
```

file này tồn tại **trong compile-time world**.

Không được:

```axiom
const FILE = file
```

nếu `FILE` mang theo một open file handle runtime.

---

# XXI.7. Không Escape Compile-Time Resource

Invariant:

> Compile-time resources cannot escape into runtime.

Ví dụ không hợp lệ:

```axiom
comptime fn get_file() -> File {
    source.open(...)
}
```

nếu `File` là host runtime resource.

Compiler phải báo lỗi kiểu:

```text
AX_COMPTIME_ESCAPE_0001
compile-time resource cannot escape into runtime
```

---

# XXI.8. Compile-Time Input

Comptime cần biết chính xác nó được phép đọc gì.

Không nên cho:

```axiom
comptime {
    read("/etc/passwd")
}
```

một cách mặc định.

Thay vào đó capability:

```text
ReadSource
WriteGenerated
ExecuteTool
Network
Environment
Filesystem
```

---

# XXI.9. Capability-Based Comptime

Ví dụ:

```axiom
comptime fn generate(
    source: ReadSource
) -> GeneratedCode {
    ...
}
```

Hoặc compiler config:

```text
comptime capabilities:
    source
    generated
```

Nếu program muốn filesystem:

```text
filesystem capability
```

phải được cấp explicit.

---

# XXI.10. Tại sao cần capability?

Nếu compile-time code có thể tùy ý:

```text
network
clock
random
environment
filesystem
process
```

thì:

```text
same source
+
same compiler
+
same target
```

không còn đảm bảo cùng kết quả.

Điều đó phá:

- reproducible build;
- caching;
- incremental compilation;
- semantic hashing;
- distributed compilation.

---

# XXI.11. Deterministic Comptime

Mặc định:

```text
comptime execution = deterministic
```

theo input contract.

Ví dụ:

```axiom
comptime fn hash_name(name: Text) -> u64
```

cùng input → cùng output.

Không được âm thầm đọc:

```text
current_time
random()
environment variable
network
```

nếu capability không được khai báo.

---

# XXI.12. Explicit External Inputs

Nếu compile-time code cần environment:

```text
Environment
```

phải trở thành build input.

Semantic input có thể là:

```text
Source
CompilerVersion
Target
Profile
ComptimeCapabilities
EnvironmentInputs
GeneratedInputs
```

Do đó reproducibility engine có thể biết:

```text
build A != build B
```

vì:

```text
ENV_MODE khác nhau
```

thay vì compiler tự nhiên sinh binary khác.

---

# XXI.13. `comptime` không phải macro

Macro truyền thống thường:

```text
tokens
 ↓
token transformation
 ↓
tokens
 ↓
parse
```

Axiom không muốn đây là cơ chế Core.

Comptime hoạt động trên:

```text
typed values
types
reflection metadata
AST/HIR APIs nếu được cấp
```

Do đó:

```axiom
comptime fn generate()
```

không phải text substitution.

---

# XXI.14. Không có textual macro trong Core v0.1

Ví dụ kiểu:

```text
#define
```

hoặc:

```text
macro_rules!
```

hoặc arbitrary token manipulation:

```text
macro foo(tokens...) -> tokens
```

không thuộc Core v0.1.

Lý do không phải macro "xấu", mà vì Axiom muốn:

```text
semantic tooling
=
same compiler model
```

thay vì:

```text
parser
+
macro parser
+
macro expansion language
+
hygiene system
+
second type system
```

---

# XXI.15. `@derive`

Thay macro bằng semantic generation.

Ví dụ:

```axiom
@derive(Equal, Hash, Debug)
struct User {
    id: u64
    name: Text
}
```

Compiler biết semantics của:

```text
Equal
Hash
Debug
```

và sinh implementation.

Đây không phải textual expansion.

---

# XXI.16. `@derive` mở rộng

Compiler có thể có:

```text
@derive(
    Copy,
    Eq,
    Hash,
    Debug,
    Serialize,
    Deserialize
)
```

nhưng các derive ngoài Core có thể do package/library đăng ký theo một cơ chế comptime/semantic generation được kiểm soát.

Không cho phép:

```text
derive => arbitrary compiler mutation
```

---

# XXI.17. Reflection

Reflection mặc định là **compile-time reflection**.

Ví dụ conceptual:

```axiom
comptime fn field_count<T>() -> usize {
    reflect.fields<T>().len()
}
```

Compiler có thể trả:

```text
3
```

Không cần runtime metadata.

---

# XXI.18. Runtime Reflection Không Mặc Định

Ví dụ:

```axiom
type User = ...
```

không có nghĩa binary chứa:

```text
"User"
"id"
"name"
"email"
```

để runtime reflection.

Nếu muốn:

```axiom
@runtime_reflect
struct User { ... }
```

thì compiler có thể generate metadata.

Điều này phù hợp mục tiêu:

> zero-cost unless requested.

---

# XXI.19. Reflection Metadata

Reflection có thể expose:

```text
Type
Field
Variant
Function
Trait
Attribute
Layout
Visibility
GenericParameter
```

Ví dụ:

```text
type_name(T)
size_of(T)
align_of(T)
field_count(T)
variant_count(T)
```

Nhưng compiler phải phân biệt:

```text
semantic metadata
layout metadata
ABI metadata
```

---

# XXI.20. Type Reflection

Ví dụ:

```axiom
comptime fn size<T>() -> usize {
    reflect.size_of<T>()
}
```

`size_of<T>()` có thể compile thành constant.

Không cần runtime function call.

---

# XXI.21. Field Reflection

Conceptual API:

```axiom
comptime fn inspect<T>() {
    for field in reflect.fields<T>() {
        ...
    }
}
```

Compiler có thể expose:

```text
field.name
field.type
field.visibility
field.offset
field.attributes
```

nhưng `offset` chỉ có semantic meaning nếu layout đã được freeze.

---

# XXI.22. Layout Reflection

Đây là điểm cần cẩn thận.

Nếu:

```axiom
struct User {
    a: u8
    b: u64
}
```

layout mặc định compiler-controlled.

Do đó:

```axiom
reflect.offset_of<User>("b")
```

không nên trở thành stable cross-compiler contract.

Nó chỉ phản ánh:

> layout của compilation hiện tại.

Nếu cần stable layout:

```axiom
@repr(C)
struct User { ... }
```

sau đó ABI/layout reflection có thể có contract mạnh hơn.

---

# XXI.23. Reflection Không Được Phá Optimization

Ví dụ:

```axiom
let size = reflect.size_of<T>()
```

compiler có thể dùng constant.

Nhưng nếu reflection yêu cầu:

```text
field offset
```

thì offset trở thành observable.

Compiler không được sau đó tự ý reorder field.

Đây là nguyên tắc:

> **Reflection can make previously unobservable metadata observable.**

---

# XXI.24. Compile-Time Code Generation

Comptime có thể tạo:

```text
runtime values
types
implementations
generated source/artifacts
```

Nhưng cần phân biệt.

### Value generation

```axiom
const TABLE = comptime_make_table()
```

### Semantic generation

```axiom
@derive(...)
```

### Artifact generation

```text
generated file
generated resource
generated ABI data
```

Không nên coi tất cả là "macro".

---

# XXI.25. Generated Source

Nếu cho phép sinh source:

```text
WriteGenerated
```

thì source đó phải trở thành một **build input/output được quản lý**.

Không được có:

```text
generate hidden source somewhere
```

rồi compiler âm thầm đọc nó.

Build graph phải biết:

```text
source
 ↓
generator
 ↓
generated file
 ↓
compiler
```

---

# XXI.26. Generated Artifact Hash

Ví dụ:

```text
generator input
+
generator code
+
capabilities
+
compiler
```

→ hash.

Generated output có thể cache.

Điều này rất quan trọng với AI-generated code hoặc codegen lớn.

---

# XXI.27. Comptime Error

Comptime error là compile error.

Ví dụ:

```axiom
const X = comptime_fn()
```

nếu function trap:

```text
AX_COMPTIME_0001
compile-time execution failed
```

Compiler nên giữ:

```text
source location
comptime call stack
semantic diagnostic
```

Ví dụ:

```text
AX_COMPTIME_0002
division by zero during compile-time evaluation

at:
    make_table()
    generate()
    const LUT = ...
```

---

# XXI.28. Comptime Panic

Không nên biến panic runtime thành process crash của compiler.

Comptime execution phải chạy trong Oracle/sandbox-like execution environment.

Nếu:

```axiom
comptime {
    panic("bad")
}
```

thì compiler nhận:

```text
COMPTIME_PANIC
```

và báo diagnostic.

Compiler process không được bị arbitrary user code làm crash.

---

# XXI.29. Resource Limits

Comptime phải có giới hạn:

```text
max steps
max memory
max recursion depth
max generated output
max execution time
```

Ví dụ:

```text
AX_COMPTIME_LIMIT_0001
compile-time evaluation exceeded step limit
```

Điều này tránh:

```axiom
comptime fn infinite() {
    while true {}
}
```

làm compiler treo vô hạn.

---

# XXI.30. Comptime và Oracle

Đây là nơi kiến trúc Axiom rất đẹp.

Comptime có thể dùng **cùng semantic execution engine** với Oracle:

```text
Source
 ↓
HIR
 ↓
Typed MIR
 ↓
Verified MIR
 ↓
Oracle execution
```

Nhưng:

```text
Oracle ≠ production runtime
```

Oracle chỉ là reference semantics.

Sau compile-time evaluation, kết quả được đưa trở lại compiler IR.

---

# XXI.31. Không được dùng Comptime để bypass verifier

Ví dụ:

```axiom
comptime fn make_invalid() -> T {
    ...
}
```

không thể sinh ra value phá ownership/type invariant.

Comptime code cũng phải qua:

```text
type check
ownership verification
capability verification
```

giống runtime code.

---

# XXI.32. Comptime Generic

Ví dụ:

```axiom
comptime fn make_zero<T: Zero>() -> T {
    T.zero()
}
```

Trait solver hoạt động bình thường.

Nếu constraint ambiguous:

```text
AX_TRAIT_AMBIGUOUS
```

Không có "comptime magic" để compiler đoán.

---

# XXI.33. Comptime Type Generation

Axiom có thể cần generated types.

Ví dụ schema:

```text
User {
    id: u64
    name: Text
}
```

generator tạo:

```axiom
struct User {
    id: u64
    name: Text
}
```

Nhưng đây phải là semantic type generation, không đơn thuần text injection.

Nếu type generation được đưa vào Core, compiler phải tạo một **type identity ổn định** cho generated type.

---

# XXI.34. Type Identity

Generated types không được vô tình tạo:

```text
User#1
User#2
```

mỗi compile step.

Type identity phải phụ thuộc vào semantic origin:

```text
Package
Module
Declaration
Generation identity
```

Điều này đặc biệt quan trọng với incremental compilation.

---

# XXI.35. Comptime và Package Boundary

Một package không được tự ý đọc private internals của package khác chỉ vì đang chạy comptime.

Reflection phải tôn trọng visibility:

```text
private
internal
pub
```

Ví dụ package A:

```axiom
struct User {
    private secret: u64
}
```

Package B không thể:

```axiom
reflect.fields<User>().secret
```

nếu không có explicit capability/visibility rule.

---

# XXI.36. Public API và Comptime

Nếu public function dùng comptime:

```axiom
pub fn make<T: Trait>(...) ...
```

thì constraint cần thiết phải xuất hiện trong semantic API fingerprint.

Không thể:

```text
public signature
```

nhưng compiler ngầm yêu cầu thêm một trait.

---

# XXI.37. Compile-Time Side Effects

Mặc định:

```text
comptime
```

không được có side effect external.

Nếu có:

```text
filesystem
network
process
environment
```

thì phải explicit capability.

Ví dụ:

```text
comptime:
    ReadSource
```

không có nghĩa:

```text
Network
```

---

# XXI.38. Build Reproducibility

Axiom build identity nên được xem:

```text
BuildInput =
    source
    dependency graph
    compiler version
    target
    profile
    explicit comptime capabilities
    explicit environment inputs
```

Nếu tất cả giống nhau:

```text
semantic result
```

phải giống nhau.

Artifact byte-for-byte reproducibility có thể còn phụ thuộc linker/build timestamp nếu profile cho phép; nhưng semantic compilation không được phụ thuộc hidden state.

---

# XXI.39. Compile-Time Network

Network không bị cấm tuyệt đối.

Nhưng:

```text
Network
```

là explicit capability.

Ví dụ package build:

```text
comptime capability:
    network("https://...")
```

Sau đó network input phải trở thành build dependency/input.

Nếu không:

```text
offline build
```

không thể reproducibly validate.

---

# XXI.40. Execute Tool

Có thể cho:

```text
ExecuteTool
```

nhưng đây là capability rất mạnh.

Ví dụ:

```text
comptime → execute shader compiler
```

Kết quả phải được đưa vào build graph:

```text
Axiom source
   ↓
comptime
   ↓
external tool
   ↓
generated artifact
   ↓
compiler
```

Không được coi external tool là invisible magic.

---

# XXI.41. Compiler Plugin

Axiom **không cho arbitrary compiler plugin trong Core v0.1**.

Không:

```text
load DLL
→ mutate AST
→ mutate type checker
→ mutate optimizer
```

Điều này phá:

- compiler determinism;
- security;
- reproducibility;
- version compatibility;
- self-hosting simplicity.

Thay bằng:

```text
comptime
reflection
derive
compiler semantic APIs
```

---

# XXI.42. AI Integration

Điểm này rất phù hợp với mục tiêu Axiom hiện tại.

AI có thể được xem là:

```text
external tool / code generator
```

nhưng không phải semantic authority.

Ví dụ:

```text
AI
 ↓
generated Axiom source
 ↓
Axiom compiler
 ↓
type checker
 ↓
ownership verifier
 ↓
optimizer
```

Không:

```text
AI → compiler IR trực tiếp → machine code
```

trừ khi IR đó vẫn đi qua semantic verification.

---

# XXI.43. Reflection và Zero-Cost

Ví dụ:

```axiom
comptime fn describe<T>() -> Text {
    ...
}
```

Nếu kết quả chỉ được dùng compile-time:

```text
runtime metadata = 0
```

Nếu cần runtime reflection:

```axiom
@runtime_reflect
```

thì metadata được emit.

Do đó:

> Reflection is zero-cost unless runtime observability is explicitly requested.

---

# XXI.44. Comptime Optimization

Compiler được phép:

- evaluate constant expressions;
- partially evaluate functions;
- fold branches;
- specialize generics;
- precompute tables;
- eliminate comptime-only code;
- cache comptime results;
- memoize deterministic evaluations.

Nhưng không được thay đổi semantics.

---

# XXI.45. Comptime Cache

Cache key nên dựa trên:

```text
comptime function semantic hash
+
arguments
+
type arguments
+
compiler semantic version
+
target
+
capability inputs
```

Không nên chỉ hash source text.

Điều này giúp incremental build mạnh hơn.

---

# XXI.46. Reflection và ABI

Reflection về ABI chỉ được expose khi ABI đã được xác định.

Ví dụ:

```axiom
@repr(C)
struct Packet { ... }
```

có thể hỏi:

```text
offset_of
size_of
align_of
```

với contract ổn định hơn.

Còn default layout:

```text
compiler-controlled
```

thì chỉ là current compilation fact.

---

# XXI.47. Negative Examples

### Runtime resource escape

```axiom
comptime fn bad() -> File {
    File.open("x")
}
```

→ reject.

---

### Hidden environment

```axiom
comptime fn bad() -> usize {
    env.get("CPU_COUNT")
}
```

nếu environment capability không được cấp:

→ reject.

---

### Infinite comptime

```axiom
comptime fn bad() {
    while true {}
}
```

→ bounded execution error.

---

### Private reflection

```axiom
comptime fn inspect<T>() {
    reflect.private_fields<T>()
}
```

nếu không có quyền:

→ reject.

---

### Invalid generated code

Generator không được sinh ra IR/value bypass:

```text
type checker
ownership verifier
ABI checker
```

→ tất cả vẫn phải chạy.

---

# XXI.48. Normative Invariants

### Core

**ACOMP-20 — Comptime Uses The Normal Type System**

**ACOMP-21 — Comptime Uses The Normal Ownership Model**

**ACOMP-22 — Compile-Time Resources Cannot Escape Into Runtime**

**ACOMP-23 — Compile-Time Execution Is Deterministic Within Its Declared Inputs**

**ACOMP-24 — Comptime Is Not A Separate Core Language**

**ACOMP-25 — Comptime Code Must Pass Normal Semantic Verification**

### Capabilities

**ACOMP-26 — External Compile-Time Effects Require Explicit Capabilities**

**ACOMP-27 — Capability Scope Is Explicit**

**ACOMP-28 — Hidden Environment Dependence Is Forbidden**

**ACOMP-29 — Network Access Is An Explicit Build Input**

**ACOMP-30 — External Tool Execution Is An Explicit Build Input**

**ACOMP-31 — Filesystem Access Is Explicit**

**ACOMP-32 — Compile-Time Capability Cannot Imply Unrelated Capabilities**

### Determinism

**ACOMP-33 — Deterministic Comptime Has Stable Semantic Results**

**ACOMP-34 — Nondeterministic Inputs Must Be Explicit**

**ACOMP-35 — Comptime Execution Is Resource-Bounded**

**ACOMP-36 — Comptime Failure Is A Compiler Diagnostic**

**ACOMP-37 — Comptime Panic Cannot Crash The Compiler Process**

### Reflection

**AREFLECT-20 — Reflection Metadata Is Not Runtime Data By Default**

**AREFLECT-21 — Compile-Time Reflection Respects Visibility**

**AREFLECT-22 — Reflection Does Not Implicitly Freeze Representation**

**AREFLECT-23 — Layout Reflection Observes Only The Selected ABI/Layout Contract**

**AREFLECT-24 — Runtime Reflection Must Be Explicitly Requested**

**AREFLECT-25 — Reflection Metadata Has Semantic Identity**

**AREFLECT-26 — Reflection Cannot Bypass Type Safety**

### Generation

**AGEN-20 — Generated Code Must Pass Normal Compilation**

**AGEN-21 — Generated Types Have Stable Semantic Identity**

**AGEN-22 — Generated Artifacts Are Build Graph Nodes**

**AGEN-23 — Generated Outputs Are Cacheable By Semantic Inputs**

**AGEN-24 — Text Generation Does Not Bypass Semantic Verification**

**AGEN-25 — Derivation Is Semantic Generation, Not Token Substitution**

### Plugins

**ACOMP-38 — Arbitrary Compiler Plugins Are Not Core v0.1**

**ACOMP-39 — Comptime Cannot Mutate Compiler Semantics**

**ACOMP-40 — Comptime Cannot Disable Verification**

**ACOMP-41 — Compiler Semantic APIs Are Controlled Interfaces**

### Optimization

**ACOMP-42 — Compile-Time Evaluation May Be Eliminated After Evaluation**

**ACOMP-43 — Compile-Time Execution Has No Required Runtime Footprint**

**ACOMP-44 — Comptime Caching Must Preserve Semantics**

**ACOMP-45 — Reflection Observability Constrains Relevant Optimization**

---

# XXI.49. Kiến trúc cuối cùng của Compile-Time

Sau Part XXI, Axiom có thể hình dung:

```text
                         AXIOM PROGRAM
                              │
             ┌────────────────┴────────────────┐
             │                                 │
         COMPILE TIME                      RUNTIME
             │                                 │
      ┌──────┼──────┐                          │
      │      │      │                          │
    const  comptime reflection                 │
      │      │      │                          │
      └──────┴──────┘                          │
             │                                 │
             └──────── generated values ───────┘
                              │
                              ▼
                        VERIFIED MIR
```

Không có:

```text
macro language
plugin language
reflection runtime mặc định
GC runtime
```

Đây là một thiết kế rất phù hợp với mục tiêu **compiler mạnh nhưng ngôn ngữ không trở nên rối**.

---

# Tiếp theo: Part XXII — Modules · Packages · Workspace · API Boundary

Phần tiếp theo sẽ **đóng băng toàn bộ namespace/package system**, bao gồm một vấn đề khá quan trọng mà Axiom hiện vẫn còn vài điểm cần chuẩn hóa:

```text
module
import
use
pub
internal
private
package
workspace
dependency
version
type identity
API fingerprint
ABI fingerprint
cyclic module dependency
```

Đặc biệt sẽ phải chốt luôn **`import` và `use` có thực sự cần tồn tại đồng thời hay nên bỏ một keyword**, thay vì để syntax dư thừa trong Axiom.