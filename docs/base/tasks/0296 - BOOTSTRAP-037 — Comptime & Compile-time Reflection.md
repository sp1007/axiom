Tiếp tục với **BOOTSTRAP-037 — Comptime + Reflection Audit & Freeze**.

Phần này trước đây đã có khung khá đầy đủ. Mục tiêu lần này là **đóng spec**, tránh để `comptime` biến thành một ngôn ngữ lập trình thứ hai hoặc biến reflection thành runtime overhead bắt buộc.

# BOOTSTRAP-037 — Comptime & Compile-time Reflection

## 1. Nguyên tắc nền tảng

Axiom chỉ có **một semantics**:

```text
Axiom program
     │
     ├── runtime
     │
     └── compile time
```

`comptime` chỉ nói:

> Chạy một phần Axiom trước khi tạo executable.

Không có:

```text
Axiom Runtime Language
Axiom Macro Language
Axiom Meta Language
```

riêng biệt.

---

# 2. Ba khái niệm

Axiom phân biệt:

```text
const
comptime
runtime
```

### `const`

Giá trị phải biết tại compile time.

```axiom
const MAX = 1024
```

### `comptime`

Thực thi code tại compile time:

```axiom
comptime {
    ...
}
```

hoặc:

```axiom
comptime fn make_table(...) -> ...
```

### Runtime

Code bình thường.

```axiom
fn process(x: i32) -> i32 {
    ...
}
```

---

# 3. `const` không phải macro

Ví dụ:

```axiom
const BUFFER_SIZE = 1024
```

chỉ tạo compile-time value.

Không sinh source code.

---

# 4. `comptime fn`

Ví dụ:

```axiom
comptime fn factorial(n: usize) -> usize {
    if n == 0 {
        1
    } else {
        n * factorial(n - 1)
    }
}
```

Có thể:

```axiom
const N = factorial(10)
```

Compiler execute function.

---

# 5. Comptime function vẫn là Axiom function

Nó dùng:

- type system
- ownership
- Drop
- capability
- pattern matching
- generic
- Result/Option

giống runtime.

Đây là điểm rất quan trọng.

---

# 6. Comptime không được gọi runtime

Nếu:

```axiom
comptime fn build() -> Table
```

thì:

```axiom
fn runtime() {
    build()
}
```

không hợp lệ nếu `build()` yêu cầu compile-time execution.

Ngược lại, runtime function không thể tự nhiên chạy tại compile time.

---

# 7. Comptime evaluation

Compiler:

```text
AST
 ↓
resolve
 ↓
type-check
 ↓
comptime execution
 ↓
materialize result
```

Comptime không bypass compiler semantic checking.

---

# 8. Comptime VM

Compiler có thể có:

```text
Comptime VM / interpreter
```

nhưng đây là implementation detail.

Executable **không chứa** VM.

```text
Compiler
 ├── frontend
 ├── comptime VM
 ├── optimizer
 └── backend

Program
 └── runtime code
```

---

# 9. Comptime resources

Một object được tạo ở comptime:

```axiom
comptime {
    let x = BigTable(...)
}
```

không tự động tồn tại trong runtime.

Nó bị destroy khi comptime execution kết thúc.

---

# 10. Materialization

Nếu muốn đưa kết quả vào executable:

```axiom
const TABLE = build_table()
```

thì compiler materialize:

```text
comptime value
      ↓
runtime constant/data
      ↓
.rodata / code / metadata
```

---

# 11. Không materialize thì xóa

Ví dụ:

```axiom
comptime {
    let x = expensive_computation()
}
```

Nếu `x` không được dùng:

```text
x
↓
compile-time only
↓
discard
```

Executable không bị ảnh hưởng.

---

# 12. Comptime allocation

Comptime được phép allocation.

Ví dụ:

```text
Vec
String
HashMap
```

nhưng đó là **compiler memory**, không phải runtime heap.

Sau khi computation kết thúc:

```text
comptime allocation
      ↓
Drop
      ↓
compiler memory released
```

---

# 13. Không có GC riêng cho comptime

Nếu compiler dùng GC nội bộ để implement comptime VM thì đó là implementation detail.

Language semantics không phụ thuộc GC.

---

# 14. Comptime ownership

Ví dụ:

```axiom
comptime fn make() -> Buffer {
    ...
}
```

`Buffer` được Move/Drop theo semantics bình thường.

Không có:

```text
"comptime object không cần ownership"
```

---

# 15. Comptime `view`

`view<T>` vẫn obey capability rules.

Không thể:

```text
comptime owner
    ↓
view
    ↓
runtime
```

nếu owner đã biến mất.

---

# 16. Không escape compiler resource

Đây là invariant quan trọng:

> Resource tồn tại trong comptime world không thể vô tình escape sang runtime.

Chỉ **materialized value** mới có thể.

---

# 17. Ví dụ

Không hợp lệ:

```axiom
comptime fn get_buffer() -> view<u8> {
    let x = Buffer(...)
    view(x)
}
```

nếu `x` bị destroy sau comptime.

Compiler phải reject.

---

# 18. External effects

Comptime có thể cần:

```text
filesystem
environment
compiler metadata
network
tool execution
```

Nhưng không được mặc định unrestricted.

---

# 19. Capability model

Comptime environment có capabilities:

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

# 20. Default capabilities

Mặc định:

```text
ReadSource
ReadMetadata
```

là an toàn nhất.

Ví dụ reflection đọc type metadata không cần filesystem/network.

---

# 21. Filesystem

Nếu cần:

```axiom
comptime fn load_schema(...) ...
```

thì filesystem access phải explicit capability.

Conceptually:

```text
comptime capability filesystem.read
```

Không nhất thiết expose đúng syntax này trong v1; quan trọng là compiler/build system phải biết dependency.

---

# 22. External input trở thành dependency

Ví dụ:

```text
schema.json
```

được đọc ở comptime.

Thay đổi:

```text
schema.json
```

phải invalidate cache.

Do đó:

```text
Comptime Identity
=
source inputs
+
declared external inputs
+
compiler configuration
+
target
```

---

# 23. Cache

Ví dụ:

```axiom
const TABLE = generate_table(schema)
```

Compiler có thể cache:

```text
hash(schema)
+
hash(comptime function)
+
compiler version
+
target config
```

→ cached result.

---

# 24. Cache không được thay đổi semantics

Nếu cache hit:

```text
execute
```

và:

```text
reuse cached result
```

phải observable-equivalent.

Nếu không chắc:

```text
recompute
```

---

# 25. Determinism

Comptime phải deterministic **trong phạm vi declared inputs**.

Ví dụ:

```text
ReadSource
```

→ deterministic.

Nhưng:

```text
Time.now()
Random()
Network()
```

không deterministic.

---

# 26. Reproducible build

Compiler có thể có mode:

```text
--reproducible
```

Trong mode này:

```text
Time
Random
Network
Environment
```

bị cấm hoặc phải được freeze thành explicit input.

---

# 27. Environment variables

Nếu comptime đọc:

```text
HOME
BUILD_MODE
VERSION
```

thì environment phải trở thành build input.

Không được âm thầm làm:

```text
same source
different executable
```

mà incremental compiler không biết.

---

# 28. Random

Có thể cho phép:

```text
comptime random
```

nhưng phải có explicit seed nếu reproducibility yêu cầu.

Ví dụ conceptually:

```text
random(seed)
```

tốt hơn:

```text
random()
```

trong reproducible mode.

---

# 29. Network

Network capability nên:

```text
disabled by default
```

vì:

- non-deterministic
- security
- reproducibility
- build hangs
- supply-chain risk

---

# 30. Execute tool

Có thể cần:

```text
comptime
 ↓
execute_tool("some_generator")
```

nhưng đây là capability mạnh.

Compiler/build system phải:

- sandbox
- timeout
- declared inputs/outputs
- dependency tracking

---

# 31. Generated files

Nếu comptime tạo file:

```text
WriteGenerated
```

thì file đó phải nằm trong declared generated-output space.

Không được tùy ý sửa:

```text
/etc
C:\Windows
```

từ compiler.

---

# 32. Typed generation

Đây là quyết định rất quan trọng.

Không ưu tiên:

```axiom
generate("fn foo() { ... }")
```

rồi parser parse string.

Thay vào đó:

```text
Comptime
 ↓
typed declaration builder
 ↓
HIR
```

---

# 33. Vì sao?

Textual macro:

```text
String
 ↓
Parser
 ↓
AST
```

gây:

- hygiene problems
- source mapping khó
- syntax injection
- compiler phase complexity
- AI tooling khó hiểu.

Typed generation sạch hơn.

---

# 34. Generated declaration

Conceptually:

```text
TypeBuilder
FunctionBuilder
FieldBuilder
EnumBuilder
TraitBuilder
```

Nhưng API cụ thể có thể thiết kế sau.

---

# 35. Generated code phải re-verify

Không được:

```text
comptime generated
↓
trust
```

Mà:

```text
generated HIR
↓
name resolution
↓
type checking
↓
ownership
↓
capability
↓
MIR
```

giống code thường.

---

# 36. Stable compiler identity

Generated declarations phải có identity ổn định.

Nếu cùng input:

```text
same generated declaration identity
```

giúp:

- incremental compilation
- diagnostics
- caching
- debug info.

---

# 37. Reflection

Reflection mặc định là:

> **compile-time reflection**

Không phải runtime reflection.

---

# 38. `Type`

Compiler có thể expose:

```axiom
Type
```

nhưng:

```text
Type
```

là **compile-time value** trong Core.

Ví dụ conceptual:

```axiom
comptime fn inspect(T: Type) {
    ...
}
```

---

# 39. Runtime `Type`

Không mặc định tồn tại:

```text
RuntimeType
```

vì nếu có:

- metadata
- type descriptors
- strings
- lookup tables
- runtime size
- binary overhead

cho mọi type.

Axiom không muốn overhead này.

---

# 40. Runtime reflection explicit

Nếu application cần:

```text
TypeInfo
```

thì phải yêu cầu compiler materialize metadata.

Ví dụ conceptually:

```axiom
@reflect
struct User { ... }
```

hoặc API tương đương sau này.

---

# 41. Reflection không bypass visibility

Nếu:

```text
private field
```

thì module khác không được reflection đọc chỉ vì reflection tồn tại.

Reflection obey:

```text
visibility
module boundaries
```

---

# 42. Reflection APIs

Compile-time API nên cung cấp:

```text
type.name
type.size
type.align
fields
field.name
field.type
field.offset
enum variants
trait implementations
attributes
```

trong phạm vi visibility/contract cho phép.

---

# 43. Layout reflection

Các query đã freeze:

```text
size_of<T>()
align_of<T>()
offset_of(...)
```

là compile-time.

Nhưng cần phân biệt:

```text
query layout
```

với:

```text
guarantee layout
```

---

# 44. Default layout

```axiom
struct Foo {
    a: u8
    b: u64
}
```

Reflection có thể cho compiler-known:

```text
size
offset
alignment
```

nhưng programmer không được coi kết quả đó là ABI-stable nếu không có `@repr`.

---

# 45. `@repr` interaction

```axiom
@repr(C)
struct Foo { ... }
```

thì reflection có thể dùng layout contract.

Không có `@repr(C)`:

```text
layout = compiler-controlled
```

---

# 46. Generic reflection

Ví dụ:

```axiom
comptime fn inspect<T>() ...
```

Compiler resolve:

```text
T = User
```

sau đó reflection được thực hiện trên concrete type.

---

# 47. Generic + comptime

Ví dụ conceptual:

```axiom
comptime fn make_zero<T>() -> T {
    ...
}
```

Compiler cần biết:

```text
T constraints
```

trước khi execute.

Không cho comptime bypass trait checking.

---

# 48. Trait reflection

Có thể query:

```text
implements<T, Trait>
```

compile-time.

Ví dụ:

```axiom
comptime {
    if implements<T, Serialize> {
        ...
    }
}
```

---

# 49. Associated type reflection

Có thể inspect:

```text
Iterator::Item
```

sau khi trait resolution thành công.

Trait solver phải chạy trước hoặc phối hợp với comptime resolution.

---

# 50. Type identity

`Type` identity phải deterministic.

Không dùng:

```text
runtime pointer address
```

làm type identity.

Compiler identity:

```text
module
+
declaration
+
generic arguments
```

conceptually.

---

# 51. `type.name`

Tên type chủ yếu phục vụ:

- diagnostics
- generated code
- debug
- serialization generation

Không đảm bảo là stable ABI identifier.

Nếu cần stable name:

```text
explicit user-provided identifier
```

hoặc schema metadata.

---

# 52. Reflection và privacy

Một module có thể expose:

```text
pub reflection metadata
```

nhưng không đồng nghĩa:

```text
private fields become public
```

---

# 53. `@derive` và reflection

Đây là nơi `@derive` rất mạnh.

```axiom
@derive(Debug, Eq, Hash)
struct User {
    id: u64
    name: String
}
```

Compiler có thể:

```text
reflection
 ↓
generate typed implementation
```

Không cần procedural macro runtime.

---

# 54. Comptime pattern matching

Comptime code dùng:

```axiom
if
match
for
loop
```

bình thường.

Không cần meta-specific syntax.

---

# 55. Comptime error

Nếu user comptime code:

```text
invalid input
```

thì:

```text
comptime panic
```

→ compiler diagnostic.

Không phải runtime panic.

---

# 56. ICE khác comptime panic

Nếu compiler implementation bug:

```text
internal compiler invariant violated
```

→ ICE.

Hai loại phải phân biệt:

```text
User computation failure
        ≠
Compiler bug
```

---

# 57. Comptime `Result`

Comptime function vẫn có thể:

```axiom
comptime fn parse(...) -> Result<T, Error>
```

Caller xử lý:

```text
?
match
```

bình thường.

Nếu cuối cùng compile-time computation fail và không được handle:

```text
compiler diagnostic
```

---

# 58. Comptime panic message

Compiler nên hiển thị:

```text
comptime evaluation failed

at:
    config.ax:42

reason:
    invalid schema
```

và có source mapping về invocation.

---

# 59. Comptime stack trace

Compiler có thể giữ evaluation trace:

```text
generate()
 └── parse_schema()
      └── validate_field()
```

cho diagnostics.

Không tồn tại trong executable.

---

# 60. Parallel comptime

Nếu:

```text
A
B
C
```

không có dependency:

```text
A ─┐
B ─┼→ parallel
C ─┘
```

Compiler có thể parallelize.

Đây là optimization.

Không thay đổi semantics.

---

# 61. Comptime synchronization

Nếu user tạo:

```text
Mutex
Channel
Thread
```

trong comptime, về nguyên tắc semantics vẫn có thể tồn tại nhưng **không nên cho arbitrary OS interaction**.

Compiler environment có execution policy riêng.

MVP nên giới hạn concurrency trong comptime.

---

# 62. Comptime network/tooling security

Comptime có thể thực thi code gần như build script.

Do đó phải coi nó là:

> **trusted build code**

chứ không phải pure compile-time expression.

Sandbox/capability system cực kỳ quan trọng.

---

# 63. Comptime và package dependency

Nếu package A chạy comptime code từ package B:

```text
A
 ↓
comptime B
```

thì B phải nằm trong dependency graph.

Không có hidden compiler plugin dependency.

---

# 64. Compiler version

Comptime cache phải phụ thuộc compiler semantic version.

Nếu compiler thay đổi semantics:

```text
cache invalidation
```

tránh reuse stale result.

---

# 65. Target

Comptime:

```text
size_of<T>()
```

có thể phụ thuộc:

```text
target arch
pointer width
ABI
endianness
features
```

Do đó target là một phần cache identity.

---

# 66. `@cfg` vs comptime

Đây là distinction nên freeze:

```text
@cfg
```

= **select declarations/code**

```text
comptime
```

= **compute values/declarations**

Ví dụ:

```axiom
@cfg(target_os == "windows")
fn windows_api() ...
```

vs:

```axiom
const BUFFER = comptime make_buffer(...)
```

---

# 67. Compile-time constant folding ≠ user comptime

Compiler tự optimize:

```axiom
let x = 2 + 3
```

thành `5`.

Đây không nhất thiết là user-visible `comptime`.

Compiler có thể evaluate bất cứ expression nào khi safe và semantics preserved.

---

# 68. User comptime vs optimizer

```text
comptime
```

là semantic request:

> giá trị phải được tạo trước runtime.

Optimizer:

> nếu có thể, hãy tính trước.

Do đó:

```text
comptime
```

có stronger guarantee.

---

# 69. Comptime code không cần annotation cho mọi thứ

Không:

```axiom
comptime {
    comptime let x = ...
    comptime if ...
    comptime loop ...
}
```

Chỉ outer context xác định compile-time execution.

---

# 70. Reflection + runtime binary size

Default:

```text
reflection
 ↓
compiler only
```

không làm binary tăng.

Chỉ khi:

```text
explicit runtime metadata
```

thì compiler emit:

```text
.rodata
metadata tables
```

---

# 71. Serialization generation

Đây sẽ rất hữu ích về sau:

```text
comptime reflection
        ↓
derive Serialize
        ↓
generated optimized serializer
```

Không cần runtime reflection.

Đây là hướng rất phù hợp với mục tiêu **performance + binary size** của Axiom.

---

# 72. Comptime + GPU

`comptime` có thể generate:

```text
kernel specialization
tensor dimensions
tile sizes
```

nhưng generated kernel phải re-enter:

```text
GPU legality
ownership
capability
address-space
```

verification.

---

# 73. Comptime + ABI

Có thể generate:

```text
@repr(C)
```

structures hoặc FFI declarations.

Nhưng compiler vẫn validate ABI.

Comptime không được bypass ABI checker.

---

# 74. Comptime + unsafe

`unsafe` không có nghĩa:

```text
"escape comptime sandbox"
```

Ví dụ:

```text
comptime
  + unsafe
```

vẫn bị giới hạn bởi external capabilities.

---

# 75. Comptime filesystem dependency

Compiler build graph phải ghi:

```text
source.ax
 ↓
comptime
 ↓
schema.json
```

Nếu schema đổi:

```text
invalidate dependent artifacts
```

---

# 76. Generated output dependency

Nếu:

```text
comptime → generated.ax
```

thì generated output phải có deterministic identity và compiler-managed ownership.

Không để source tree bị sửa ngầm.

---

# 77. Không có procedural macro system v1

Tạm thời:

```text
NO:
procedural macros
compiler plugins
arbitrary AST mutation
arbitrary MIR mutation
```

vì chúng phá:

- determinism
- compiler stability
- tooling
- incremental cache
- security.

Typed generation + compiler-known derives là đủ cho Core v1.

---

# 78. Comptime capability escalation

Capability phải explicit.

Một function có:

```text
ReadFilesystem
```

không tự động truyền capability đó cho function khác nếu API không truyền capability.

Đây là hướng capability-based design.

---

# 79. Capability object

Về sau có thể:

```axiom
fn generate(fs: FileSystemCapability)
```

thay vì global:

```axiom
filesystem.read(...)
```

Điều này giúp dependency rõ ràng.

MVP có thể compiler/build environment inject capability.

---

# 80. Comptime sandbox

Mục tiêu:

```text
default
  ↓
sandboxed
  ↓
declared capability
  ↓
explicit effect
```

Không phải:

```text
compiler = arbitrary shell access
```

---

# 81. Invariants BOOTSTRAP-037

```text
ACOMP-20   Comptime uses Axiom semantics.

ACOMP-21   Comptime shares the Axiom type system.

ACOMP-22   Comptime resources cannot implicitly escape to runtime.

ACOMP-23   Comptime is deterministic within declared inputs.

ACOMP-24   Undeclared external state cannot affect reproducible evaluation.

ACOMP-25   Declared external inputs participate in comptime identity.

ACOMP-26   Comptime values may explicitly materialize into runtime data/code.

ACOMP-27   Unmaterialized comptime entities are erased.

ACOMP-28   Compile-time reflection does not imply runtime reflection.

ACOMP-29   Runtime reflection requires explicit metadata emission.

ACOMP-30   Comptime panic becomes a compiler diagnostic.

ACOMP-31   Comptime panic is distinct from compiler ICE.

ACOMP-32   Comptime respects ownership semantics.

ACOMP-33   Comptime respects capability semantics.

ACOMP-34   Comptime cannot bypass safety verification.

ACOMP-35   Generated code is re-verified.

ACOMP-36   External comptime effects are capability-gated.

ACOMP-37   External inputs participate in incremental compilation identity.

ACOMP-38   Comptime does not require runtime support.

ACOMP-39   Comptime VM is compiler-internal.

ACOMP-40   Compile-time metadata is not runtime metadata by default.

ACOMP-41   Independent comptime evaluations may execute in parallel.

ACOMP-42   Comptime cache reuse preserves semantics.

ACOMP-43   Typed generation is preferred over textual macros.

ACOMP-44   General compiler IR mutation is not exposed.

ACOMP-45   Reproducible builds may restrict external capabilities.

ACOMP-46   Comptime is Axiom semantics executed before runtime.

ACOMP-47   Comptime does not define a second programming language.

ACOMP-48   Comptime shares the Core type system.

ACOMP-49   Comptime shares ownership semantics.

ACOMP-50   Comptime shares capability semantics.

ACOMP-51   Comptime values are compile-time entities.

ACOMP-52   Comptime resources cannot implicitly escape runtime.

ACOMP-53   Runtime materialization is explicit.

ACOMP-54   Comptime execution is deterministic within declared inputs.

ACOMP-55   External inputs are part of comptime identity.

ACOMP-56   Undeclared external state cannot affect reproducible evaluation.

ACOMP-57   Comptime capabilities are explicit.

ACOMP-58   Comptime has a compiler-internal execution environment.

ACOMP-59   Comptime VM is not part of runtime.

ACOMP-60   Comptime panic produces a compiler diagnostic.

ACOMP-61   Comptime panic is distinct from compiler ICE.

ACOMP-62   Comptime Drop uses normal Drop semantics.

ACOMP-63   Comptime cannot bypass ownership verification.

ACOMP-64   Comptime cannot bypass capability verification.

ACOMP-65   Generated code is re-verified.

ACOMP-66   Typed generation is preferred over textual generation.

ACOMP-67   Generated declarations preserve stable compiler identity.

ACOMP-68   Arbitrary compiler IR mutation is not exposed.

ACOMP-69   Reflection is compile-time by default.

ACOMP-70   Reflection does not imply runtime metadata.

ACOMP-71   Runtime reflection requires explicit metadata emission.

ACOMP-72   Reflection respects visibility.

ACOMP-73   Type is a compile-time value.

ACOMP-74   Runtime type objects are not required.

ACOMP-75   size_of/align_of/offset_of are compile-time queries.

ACOMP-76   Representation observation respects repr contracts.

ACOMP-77   @cfg selects code; comptime computes values/declarations.

ACOMP-78   Compiler-known derives do not require runtime machinery.

ACOMP-79   Comptime dependencies participate in incremental compilation.

ACOMP-80   Comptime cache preserves semantics.

ACOMP-81   Independent comptime evaluations may run in parallel.

ACOMP-82   External effects are capability-gated.

ACOMP-83   Reproducible builds may restrict external capabilities.

ACOMP-84   Unmaterialized comptime code is erased.

ACOMP-85   Comptime does not imply runtime allocation.

ACOMP-86   Comptime allocation belongs to the compiler execution environment.

ACOMP-87   Comptime allocation does not imply runtime heap allocation.

ACOMP-88   Comptime functions cannot implicitly execute at runtime.

ACOMP-89   Runtime functions cannot implicitly execute at compile time.

ACOMP-90   Compile-time evaluation may depend on target configuration.

ACOMP-91   Target configuration participates in comptime cache identity.

ACOMP-92   Compiler version participates in semantic cache identity.

ACOMP-93   Comptime external dependencies participate in build graphs.

ACOMP-94   External filesystem access is not implicitly permitted.

ACOMP-95   Network access is disabled by default.

ACOMP-96   Arbitrary tool execution requires explicit capability.

ACOMP-97   Generated files are compiler-managed outputs.

ACOMP-98   Comptime cannot silently mutate arbitrary host state.

ACOMP-99   Comptime diagnostics preserve source invocation context.

ACOMP-100  Comptime generated declarations participate in ordinary name resolution.

ACOMP-101  Comptime generated declarations participate in ordinary type checking.

ACOMP-102  Comptime generated declarations participate in ownership verification.

ACOMP-103  Comptime generated declarations participate in capability verification.

ACOMP-104  Reflection cannot bypass module visibility.

ACOMP-105  Reflection cannot bypass representation contracts.

ACOMP-106  Reflection cannot create runtime metadata implicitly.

ACOMP-107  Runtime metadata emission is an explicit compilation decision.

ACOMP-108  Compile-time Type identity is deterministic.

ACOMP-109  Reflection results may depend on resolved generic arguments.

ACOMP-110  Trait reflection requires trait resolution.

ACOMP-111  Comptime does not provide a general procedural macro system.

ACOMP-112  Comptime does not expose unrestricted AST mutation.

ACOMP-113  Comptime does not expose unrestricted MIR mutation.

ACOMP-114  Unsafe does not bypass the comptime capability sandbox.

ACOMP-115  Comptime capability delegation is explicit.

ACOMP-116  Comptime parallelism cannot change observable semantics.

ACOMP-117  Comptime cache invalidation is dependency-aware.

ACOMP-118  Comptime materialization preserves representation contracts.

ACOMP-119  Comptime-generated GPU code undergoes GPU verification.

ACOMP-120  Comptime-generated FFI declarations undergo ABI verification.
```

# Freeze quyết định

Từ đây tôi xem các điểm sau là **Core v1 đã chốt**:

```text
                    COMPTIME
                       │
          ┌────────────┼────────────┐
          │            │            │
       compute      reflect      generate
          │            │            │
          └────────────┼────────────┘
                       ↓
                    Typed HIR
                       ↓
                Normal verification
                       ↓
                 Runtime artifact
```

Không có:

```text
❌ procedural macro language
❌ textual macro system
❌ runtime reflection mặc định
❌ compiler plugin API
❌ arbitrary IR mutation
❌ implicit filesystem/network access
❌ comptime runtime trong executable
```

Đây là một điểm rất mạnh của Axiom: **AI/code generator có thể sử dụng comptime rất mạnh, nhưng compiler vẫn giữ được một pipeline deterministic và có thể cache/verify được.**

---

## Tiếp theo: BOOTSTRAP-038

Ta sẽ **audit và freeze Async** dựa trên AASYNC-75…117 đã thiết kế trước đó.

Trọng tâm sẽ là một vấn đề quan trọng: **Future, async/await, cancellation, executor, async I/O và ownership/view qua suspension point**, đồng thời đảm bảo async không biến thành một runtime bắt buộc cho mọi chương trình Axiom.