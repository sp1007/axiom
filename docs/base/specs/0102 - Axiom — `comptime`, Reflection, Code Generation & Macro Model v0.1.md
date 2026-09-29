Tiếp tục.

# Axiom — `comptime`, Reflection, Code Generation & Macro Model v0.1

Đây là chỗ tôi muốn **không bê nguyên mô hình macro của Rust/C++** vào Axiom.

Đề xuất chính:

> **Axiom không có một macro language thứ hai.**  
> Thay vào đó dùng `comptime` + reflection có kiểm soát + generated declarations/code.

Mục tiêu là đạt phần lớn sức mạnh của macro mà vẫn giữ:

- một hệ type system;
- một semantic model;
- compiler dễ phân tích;
- IDE hiểu được code sinh ra;
- AI agent dễ thao tác;
- không có “magic text substitution”.

---

# 1. Phân biệt 4 loại computation

Axiom cần phân biệt rõ:

```text
runtime
comptime
build-time
code generation
```

### Runtime

```axiom
fn square(x: i32) -> i32 {
    x * x
}
```

Chạy khi chương trình chạy.

### Comptime

```axiom
const SIZE = 1024
```

hoặc:

```axiom
comptime {
    ...
}
```

Chạy trong compiler.

### Build-time

Ví dụ:

```text
đọc schema
generate bindings
compile resource
```

Đây thuộc build system.

### Code generation

Tạo ra:

```text
types
functions
impls
constants
```

để compiler tiếp tục type-check.

---

# 2. Không dùng một cơ chế cho tất cả

Sai:

```text
macro {
    chạy bất cứ thứ gì
}
```

Đúng:

```text
Language semantics
    ├── const
    ├── comptime
    └── reflection

Build system
    └── build capabilities

Code generation
    └── generated AST/declarations
```

---

# 3. `const`

`const` là giá trị compile-time.

Ví dụ:

```axiom
const MAX_USERS: usize = 1000
```

Compiler phải evaluate được:

```text
1000
```

và không tạo storage runtime.

---

# 4. `const` không phải static

```axiom
const X: i32 = 42
```

không có identity/address.

Trong khi:

```axiom
static X: i32 = 42
```

có storage identity.

Do đó:

```axiom
&X
```

chỉ có ý nghĩa với `static`, không phải `const`.

---

# 5. `static`

```axiom
static VERSION: Text = "1.0"
```

có storage program-lifetime.

Immutable static có thể được đặt trong `.rodata`.

---

# 6. Mutable static

```axiom
static var COUNTER: Atomic<i64> = Atomic<i64>.new(0)
```

được phép nếu kiểu/khởi tạo hợp lệ.

Global mutable ordinary memory:

```axiom
static var X: i32 = 0
```

nên yêu cầu:

```text
unsafe
```

hoặc synchronization abstraction.

Tôi nghiêng về:

> **mutable global không đồng bộ là `unsafe` ở declaration/access boundary.**

---

# 7. Không có hidden global initialization

Đây là invariant rất quan trọng.

Không:

```text
module load
 ↓
constructor chạy
```

như một số runtime/object systems.

Axiom program phải có startup deterministic:

```text
OS
 ↓
startup
 ↓
main
```

---

# 8. Vì sao?

Nếu module có:

```axiom
static var x = expensive_init()
```

không được âm thầm biến thành:

```text
hidden global constructor
```

Điều đó làm:

- startup khó dự đoán;
- linker khó loại bỏ;
- freestanding khó hỗ trợ;
- dependency graph khó hiểu.

Thay vào đó initializer của static phải là **compile-time constant** hoặc cơ chế explicit lazy/runtime initialization.

---

# 9. `Lazy<T>`

Nếu cần runtime initialization:

```axiom
static CONFIG: Lazy<Config> = Lazy.new(|| load_config())
```

Đây là library abstraction.

Không phải compiler magic.

---

# 10. `thread_static`

Cần hỗ trợ TLS:

```axiom
thread_static var BUFFER: Buffer
```

Compiler hạ xuống TLS ABI.

Không phải mỗi lần truy cập phải gọi runtime function nếu target có TLS native.

---

# 11. `comptime`

Đây là phần mạnh nhất.

Tôi đề xuất:

```axiom
comptime fn factorial(n: usize) -> usize {
    if n == 0 {
        1
    } else {
        n * factorial(n - 1)
    }
}
```

Sau đó:

```axiom
const X = factorial(10)
```

---

# 12. Comptime dùng cùng semantic language

Đây là quyết định quan trọng:

Không tạo:

```text
Axiom runtime language
+
Axiom macro language
```

Mà:

```text
Axiom source
       ↓
same parser
       ↓
same type system
       ↓
same MIR semantics
       ↓
comptime interpreter
```

---

# 13. Comptime Oracle

Ta đã có Semantic Oracle.

Có thể dùng:

```text
Typed MIR
   ↓
Comptime evaluator
   ↓
Value
```

Do đó:

> **Comptime không cần một interpreter riêng về semantics.**

Nó chỉ là một execution mode của semantic engine.

---

# 14. Comptime deterministic

Mặc định `comptime` không được:

```text
network
process spawn
random system state
current time
arbitrary filesystem
FFI
```

Nếu cho phép, build mất reproducibility.

---

# 15. Capability-based comptime

Nếu thực sự cần:

```text
ReadSource
WriteGenerated
Environment
Filesystem
ExecuteTool
Network
```

phải cấp capability rõ ràng.

Ví dụ conceptual:

```text
comptime[ReadSource]
```

hoặc capability được cấp bởi build environment.

---

# 16. Không nên cho `comptime` quyền vô hạn

Nếu:

```text
comptime
```

có thể chạy:

```text
shell
network
filesystem
```

thì:

```text
compile source
```

thực chất trở thành:

```text
execute arbitrary program
```

và reproducible build gần như mất.

---

# 17. Comptime recursion

Cho phép:

```axiom
comptime fn fib(n: usize) -> usize { ... }
```

nhưng compiler cần:

```text
step limit
recursion limit
memory limit
```

để tránh:

```text
comptime
→ infinite loop
→ compiler hangs
```

---

# 18. Comptime value

Comptime có thể tạo:

```text
integer
float
bool
enum
struct
array
tuple
Text
type information
```

nhưng không được tùy tiện tạo runtime resource:

```text
File
Socket
Thread
Mutex
```

trừ khi chúng chỉ tồn tại như compile-time representation và không thực sự mở resource.

---

# 19. Comptime type computation

Cần cho phép một mức bounded type computation.

Ví dụ:

```axiom
comptime fn choose_type(...) -> Type
```

Nhưng tôi **không khuyến nghị dependent types**.

Không:

```text
Vector<T, arbitrary theorem-dependent expression>
```

đến mức type system trở thành theorem prover.

---

# 20. Bounded const generics đã đủ

Ví dụ:

```axiom
struct Matrix<T, const N: usize, const M: usize> {
    data: [T; N * M]
}
```

đây là mức rất hữu ích.

Không cần dependent type system đầy đủ.

---

# 21. Reflection

Reflection compile-time:

```axiom
comptime type_info(T)
```

có thể lấy:

```text
name
fields
field types
enum variants
traits
attributes
layout
size
alignment
```

---

# 22. Runtime reflection không mặc định

Không tạo:

```text
TypeInfo
```

ở runtime cho mọi type.

Nếu chương trình không dùng reflection:

```text
binary
```

không có reflection metadata.

Đúng với mục tiêu binary nhỏ.

---

# 23. Explicit runtime reflection

Nếu framework cần:

```axiom
reflect(T)
```

compiler có thể generate metadata.

Ví dụ:

```text
type name
field names
field offsets
enum variants
```

Chỉ phần được yêu cầu tồn tại.

---

# 24. Reflection không được phụ thuộc layout mặc định

Ví dụ reflection:

```text
fields(T)
```

trả:

```text
field identity
field type
```

nhưng không được giả định:

```text
field A luôn ở offset 0
```

trừ khi:

```axiom
@repr(C)
```

hoặc representation contract khác.

---

# 25. `@repr(C)` + reflection

Nếu:

```axiom
@repr(C)
struct Foo {
    a: i32
    b: f64
}
```

thì compile-time reflection có thể biết:

```text
size
alignment
offset
```

theo target ABI.

---

# 26. Generated code

Đây là phần thay macro.

Ví dụ serializer generator:

```text
schema
 ↓
comptime reflection
 ↓
generate impl
 ↓
type checker
 ↓
normal Axiom code
```

---

# 27. Generated AST, không generated text

Tôi khuyến nghị:

> **Code generation tạo semantic declarations/AST, không tạo chuỗi source text rồi parse lại nếu không cần.**

Thay vì:

```text
generate "fn foo() { ... }"
 ↓
parse string
```

làm:

```text
comptime
 ↓
DeclarationBuilder
 ↓
AST/HIR fragment
```

---

# 28. Vì sao?

Nếu generate text:

```text
AI/debugger/IDE
```

khó biết nguồn gốc declaration.

AST generation giữ:

```text
origin
source mapping
generator
generated node
```

---

# 29. Nhưng vẫn cần generated source

Có những trường hợp build tool cần tạo file:

```text
generated_bindings.axiom
```

Được phép ở build layer.

Nhưng compiler semantics vẫn xem đó là **source file bình thường**.

---

# 30. Hai loại generation

### Semantic generation

```text
comptime
```

→ trực tiếp tạo declaration.

### Build generation

```text
build tool
```

→ tạo source/artifact.

Không trộn hai loại.

---

# 31. Macro?

Tôi đề xuất **không có textual macro trong Core**.

Không:

```text
#define
```

Không:

```text
token substitution
```

Không:

```text
paste arbitrary syntax
```

---

# 32. Có cần procedural macro không?

Cũng không đưa vào v0.1.

Phần lớn use case có thể giải quyết bằng:

```text
comptime
reflection
generic
trait
generated declaration
```

---

# 33. Nhưng có thể cần syntax extension

Một số framework thực sự muốn:

```text
#[derive(...)]
```

Tôi đề xuất không gọi đó là macro.

Có thể có:

```axiom
@derive(Serialize, Deserialize)
struct User { ... }
```

Compiler/plugin generator xử lý semantic declaration.

---

# 34. `@derive`

Ví dụ:

```axiom
@derive(Debug, Eq, Hash)
struct User {
    id: u64
    name: Text
}
```

Compiler có thể generate:

```text
impl Debug for User
impl Eq for User
impl Hash for User
```

Nhưng semantics của `Debug`, `Eq`, `Hash` vẫn là trait/library.

---

# 35. Built-in derive vs arbitrary plugin

Không nên để mọi package tự nhúng compiler plugin vào compiler process.

Có ba mức:

```text
built-in derive
comptime generation
external build generator
```

Từ đơn giản đến mạnh.

---

# 36. Vì sao không compiler plugin tùy ý?

Nếu package có thể load arbitrary compiler plugin:

```text
compile package
→ execute native plugin inside compiler
```

thì:

- reproducibility khó;
- compiler stability khó;
- cross-compilation khó;
- sandboxing khó;
- compiler crash dễ hơn.

Do đó **không có arbitrary compiler plugin trong Core v0.1**.

---

# 37. Comptime package generation

Nếu package cần generate code:

```text
comptime module
```

được compile bằng chính Axiom.

Ví dụ:

```axiom
comptime fn generate_bindings(schema: Schema) -> GeneratedModule {
    ...
}
```

---

# 38. Generated module

Conceptually:

```text
module generated {
    ...
}
```

Compiler đưa generated declarations vào HIR.

Các declaration này tiếp tục:

```text
typecheck
ownership-check
trait-check
```

như code bình thường.

---

# 39. Generated code không được bypass verifier

Đây là invariant bắt buộc.

Không:

```text
generator
 ↓
"trust me"
 ↓
machine code
```

Mà:

```text
generator
 ↓
HIR
 ↓
normal verification
 ↓
MIR
```

---

# 40. Điều này rất hợp với AI

AI agent cũng có thể generate source.

Nhưng compiler vẫn:

```text
parse
typecheck
verify
```

AI không được cấp “trusted code” chỉ vì nó là AI.

---

# 41. Conditional compilation

Không dùng preprocessor.

Dùng:

```axiom
@cfg(os = "windows")
```

hoặc:

```axiom
@cfg(target_arch = "x86_64")
```

---

# 42. `cfg` phải được xử lý trước type checking phần bị loại

Ví dụ:

```axiom
@cfg(os = "windows")
fn foo() {
    windows_api()
}
```

Khi build Linux, declaration không tồn tại trong semantic graph.

---

# 43. Không dùng:

```text
#ifdef
#define
#include
```

Axiom source không phải C preprocessor language.

---

# 44. `cfg` expression

Có thể:

```axiom
@cfg(all(
    os = "linux",
    arch = "x86_64"
))
```

và:

```axiom
@cfg(any(
    arch = "aarch64",
    arch = "riscv64"
))
```

---

# 45. Target properties

`cfg` có thể truy cập:

```text
os
arch
abi
env
pointer_width
endianness
feature
profile
```

nhưng không được query arbitrary host environment trong semantic compilation.

---

# 46. Build configuration

Các feature package:

```text
feature = "gpu"
feature = "sqlite"
```

được đưa vào compilation identity.

Compiler có thể:

```axiom
@cfg(feature = "gpu")
```

---

# 47. Feature không được thay language semantics

Feature có thể:

```text
enable module
enable implementation
enable backend
```

không thể:

```text
thay đổi ý nghĩa của ownership
thay đổi `i32`
thay đổi trait resolution
```

---

# 48. Attributes

Attributes nên chia:

### Semantic

```text
@repr(C)
@align(64)
```

### Compiler

```text
@inline
@cold
@noinline
```

### Platform

```text
@cfg(...)
@interrupt
```

### Documentation

```text
@deprecated
@doc(...)
```

---

# 49. Attribute không được là “magic string soup”

Mỗi attribute phải có schema.

Ví dụ:

```text
@align(64)
```

compiler biết argument phải là:

```text
integer constant
```

Sai:

```text
@align("hello")
```

→ compiler diagnostic.

---

# 50. User-defined attributes

Có thể cho metadata:

```axiom
@serde(rename = "user_id")
```

nhưng compiler không tự hiểu.

Reflection/comptime generator đọc metadata.

Điều này giúp framework mở rộng mà không sửa Core.

---

# 51. Attribute namespace

Nên có:

```text
@core.repr(C)
@compiler.inline
@target.interrupt
@serde.rename("id")
```

thay vì hàng trăm tên global.

Có thể syntax ngắn:

```text
@repr(C)
```

là alias built-in.

---

# 52. Compile-time error

Nếu comptime generator phát hiện schema sai:

```axiom
comptime {
    compile_error("invalid schema")
}
```

Compiler báo lỗi tại compile time.

Đây là tương đương use case tốt của macro error.

---

# 53. Compile-time assertion

```axiom
comptime_assert(size_of(Foo) == 16)
```

Hoặc:

```axiom
const_assert(...)
```

Đặc biệt hữu ích cho FFI:

```axiom
comptime_assert(size_of(CHeader) == expected)
```

---

# 54. Compile-time layout validation

Ví dụ:

```axiom
comptime_assert(
    offset_of(Foo, header) == 0
)
```

chỉ hợp lệ nếu representation contract cho phép quan sát offset.

---

# 55. Comptime generated serialization

Một framework có thể làm:

```text
@derive(Serialize)
struct User {
    id: u64
    name: Text
}
```

Generator dùng reflection:

```text
fields(User)
```

→ generate trait implementation.

Runtime binary chỉ chứa code thực sự dùng.

---

# 56. Generic + comptime

Ví dụ:

```axiom
fn zeros<const N: usize>() -> Array<i32, N> {
    ...
}
```

Compiler specialization:

```text
zeros<16>
zeros<32>
```

Không cần runtime type metadata.

---

# 57. Comptime specialization không phải runtime branching

Không:

```text
if N == 16
```

ở runtime nếu `N` compile-time known.

Compiler có thể specialize:

```text
zeros<16>
```

thành code cụ thể.

---

# 58. Comptime resource limits

Compiler configuration:

```text
comptime_max_steps
comptime_max_memory
comptime_max_recursion
```

Mặc định deterministic.

---

# 59. Compiler timeout

Một build server có thể đặt:

```text
--comptime-timeout
```

nhưng timeout là infrastructure safety, không thay semantics.

---

# 60. Comptime cache

Kết quả:

```text
comptime fn parse_schema(...)
```

có thể cache theo:

```text
function semantic fingerprint
+
input value
+
compiler version
+
target
+
capabilities
```

Nếu deterministic.

---

# 61. Không cache nếu phụ thuộc environment

Nếu comptime được cấp:

```text
ReadEnvironment
```

thì environment fingerprint phải trở thành compilation input.

Không:

```text
same source
→ random cached result
```

---

# 62. Macro migration philosophy

Nếu sau này phát hiện cần macro mạnh hơn, không vội thêm textual macro.

Trước tiên hỏi:

```text
Có giải quyết bằng generic?
Có giải quyết bằng trait?
Có giải quyết bằng comptime?
Có giải quyết bằng reflection?
Có giải quyết bằng generated declaration?
Có giải quyết bằng build tool?
```

Chỉ nếu tất cả thất bại mới xem xét syntax extension.

---

# 63. Nếu cuối cùng cần macro

Có thể thiết kế **typed syntax transformation**:

```text
Token/AST
 ↓
typed macro
 ↓
AST
```

chứ không phải:

```text
string → string
```

Macro phải:

- có namespace;
- có input/output schema;
- deterministic mặc định;
- sandbox;
- source mapping;
- không bypass type checker;
- không bypass ownership verifier.

Nhưng tôi **không đưa nó vào v0.1**.

---

# 64. Đây là quyết định quan trọng

Tôi đề xuất đóng băng:

> **Axiom v0.1 không có general-purpose textual/procedural macro system.**

Thay vào đó:

```text
                    Metaprogramming
                           │
       ┌───────────────────┼───────────────────┐
       ↓                   ↓                   ↓
     const              comptime            reflection
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ↓
                  generated declarations
                           ↓
                     normal compiler
```

---

# 65. Comptime vs build script

Phải cực kỳ rõ:

| Nhu cầu | Cơ chế |
|---|---|
| Tính constant | `const` |
| Tính toán compile-time | `comptime` |
| Đọc type/field | reflection |
| Generate impl/function | comptime generation |
| Generate source file | build tool |
| Gọi compiler khác | build capability |
| Download schema | build capability + network |
| Link native library | build system |
| OS configuration | `@cfg` |
| Runtime metadata | explicit reflection |

---

# 66. Invariants mới

```text
ACOMP-01  Const Has No Runtime Storage Identity
ACOMP-02  Static Has Storage Identity
ACOMP-03  No Hidden Global Initialization
ACOMP-04  Runtime Initialization Is Explicit
ACOMP-05  Comptime Uses Axiom Semantic Model
ACOMP-06  Comptime Is Deterministic By Default
ACOMP-07  Comptime Has Resource Limits
ACOMP-08  Comptime Capabilities Are Explicit
ACOMP-09  Comptime Cannot Implicitly Perform Arbitrary I/O
ACOMP-10  Runtime Reflection Is Opt-In
ACOMP-11  Reflection Does Not Imply Stable Default Layout
ACOMP-12  Generated Code Is Normally Type-Checked
ACOMP-13  Generated Code Cannot Bypass Verification
ACOMP-14  Textual Macros Are Not Core
ACOMP-15  Procedural Macros Are Not Core v0.1
ACOMP-16  Built-In Derivation Is Semantic
ACOMP-17  Build Generation Is Separate From Comptime
ACOMP-18  Conditional Compilation Is Structured
ACOMP-19  cfg Cannot Redefine Language Semantics
ACOMP-20  Attributes Have Typed Schemas
ACOMP-21  User Metadata Does Not Implicitly Affect Semantics
ACOMP-22  Comptime Results May Be Cached Only When Inputs Are Known
ACOMP-23  Environment-Dependent Compilation Is Explicit
ACOMP-24  Compiler Plugins Cannot Arbitrarily Execute Inside Semantic Compilation
ACOMP-25  Metaprogramming Uses The Same Type/Ownership Model
```

---

# 67. Một thay đổi nhỏ nhưng quan trọng với kiến trúc trước

Trước đây ta nói:

```text
Compile-time reflection may expose type/field/enum/trait/constant info.
```

Bây giờ nên chính thức hóa thành:

```text
Reflection levels:

Level 0:
    no runtime metadata

Level 1:
    comptime reflection

Level 2:
    generated static metadata

Level 3:
    explicit runtime reflection
```

Programmer chọn mức cần thiết.

---

# 68. Kết quả

Axiom có thể đạt:

```text
Rust derive
    → @derive + comptime/reflection

C macros
    → const/comptime/generation

C++ templates
    → generics + comptime

code generation
    → generated declarations

build.rs
    → explicit build capabilities
```

nhưng không phải copy nguyên mô hình của bất kỳ ngôn ngữ nào.

---

# Tiếp tục → Module & Visibility Semantics

Phần kế tiếp ta sẽ **đóng băng module system**, bởi đây là nền tảng để những cơ chế trên hoạt động đúng:

```text
package
  ↓
module
  ↓
namespace
  ↓
visibility
  ↓
import/export
  ↓
re-export
  ↓
semantic interface
  ↓
incremental compilation
```

Đặc biệt cần giải quyết dứt điểm:

- `pub`, private và friend-like access;
- module vs file;
- circular dependencies;
- initialization;
- re-export;
- package/type identity;
- generic visibility;
- `internal`;
- API boundary;
- ABI/export boundary;
- và cách compiler xác định chính xác **“public API”** để package manager, IDE, AI agent và incremental compiler cùng sử dụng một semantic model.