Tiếp tục với **BOOTSTRAP-016 — Comptime + Compile-time Reflection**.

Đây là phần rất quan trọng với triết lý Axiom, vì nếu thiết kế tốt thì Axiom có thể có sức mạnh metaprogramming rất lớn mà **không cần macro language riêng, không cần runtime reflection và không cần compiler plugin API phức tạp**.

# BOOTSTRAP-016 — COMPTIME + REFLECTION

## 1. Nguyên tắc nền tảng

> **Comptime là Axiom chạy trước runtime, không phải một ngôn ngữ thứ hai.**

Có ba thế giới:

```text
const
  = compile-time value

comptime
  = compile-time execution

runtime
  = normal execution
```

Ví dụ:

```axiom
const SIZE: usize = 1024;

comptime {
    ...
}

fn main() {
    ...
}
```

Cả `const`, `comptime` và runtime đều sử dụng **cùng type system và semantic model**.

---

# 2. Không tạo "Axiom Meta Language"

Không thiết kế kiểu:

```text
Axiom
   +
Macro Language
   +
Reflection Language
   +
Template Language
```

Thay vào đó:

```text
Axiom source
     │
     ├── runtime execution
     │
     └── comptime execution
```

Khác nhau chủ yếu ở **thời điểm thực thi và capability được phép sử dụng**.

---

# 3. `const`

`const` là compile-time value.

```axiom
const PI: f64 = 3.1415926535;
const SIZE: usize = 1024;
```

Compiler có thể materialize:

```text
SIZE → immediate 1024
```

hoặc:

```text
SIZE → constant data
```

Không cần runtime storage nếu không lấy address.

---

# 4. `comptime`

`comptime` là execution:

```axiom
comptime {
    let x = calculate();
    ...
}
```

Compiler chạy code này trong compile-time environment.

Kết quả có thể:

- tạo constant
- tạo type information
- generate declarations
- generate data
- validate configuration
- embed resource

---

# 5. Comptime function

```axiom
comptime fn factorial(n: usize) -> usize {
    if n == 0 {
        return 1;
    }

    return n * factorial(n - 1);
}
```

Sau đó:

```axiom
const F: usize = factorial(10);
```

Compiler evaluate:

```text
factorial(10)
→ 3628800
```

Runtime không cần chứa `factorial`.

---

# 6. Comptime function không phải runtime function

Nếu:

```axiom
comptime fn generate() -> Type
```

thì không được gọi:

```axiom
let x = generate();
```

ở runtime.

Compiler báo lỗi.

Ngược lại, runtime function cũng không tự động được gọi ở comptime nếu nó có operation không hợp lệ trong comptime environment.

---

# 7. Nhưng semantics giống nhau

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    return a + b;
}
```

Nếu compiler cho phép function này chạy trong comptime context:

```axiom
const X = comptime add(10, 20);
```

thì arithmetic, ownership, overflow semantics vẫn phải giống runtime.

Không có:

```text
runtime integer rules
≠
comptime integer rules
```

---

# 8. Comptime VM

Compiler cần một execution engine:

```text
compiler/comptime/
├── interpreter
├── evaluator
├── memory
├── values
├── capabilities
├── reflection
└── cache
```

Có thể gọi:

```text
Comptime VM
```

nhưng đây là **compiler-internal**.

Executable cuối cùng không chứa nó.

---

# 9. Không nhất thiết interpret từng instruction

Comptime backend có thể ban đầu là interpreter:

```text
Axiom HIR/MIR
    ↓
Comptime Interpreter
```

Sau này có thể:

```text
Axiom MIR
    ↓
Comptime Optimizer
    ↓
native helper process
```

hoặc JIT.

Đó là implementation detail.

Semantic contract không phụ thuộc cách compiler execute comptime.

---

# 10. Ownership trong comptime

Đây là điểm cực kỳ quan trọng.

Nếu comptime:

```axiom
comptime {
    let buffer = Buffer(...);
}
```

thì `buffer` vẫn có:

```text
ownership
move
copy
drop
```

như runtime.

Không được tạo một memory model hoàn toàn khác.

---

# 11. Comptime resources không escape

Ví dụ:

```axiom
comptime {
    let file = open("data.bin");
}
```

`file` thuộc compile-time world.

Không được:

```text
comptime resource
        ↓
runtime pointer
```

một cách ngầm định.

Muốn đưa dữ liệu vào runtime:

```text
comptime resource
       ↓ materialize
runtime constant/data
```

---

# 12. Materialization

Ví dụ:

```axiom
comptime {
    let data = read_file("model.bin");
    emit_bytes("MODEL", data);
}
```

Kết quả có thể là:

```text
.rodata
└── MODEL
```

Runtime chỉ thấy:

```text
MODEL bytes
```

không thấy compile-time file handle.

---

# 13. Comptime capability model

Đây là phần nên chốt rõ.

Comptime không mặc định có toàn quyền máy tính.

Các capability nội bộ:

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

Ban đầu mặc định chỉ nên cho:

```text
ReadSource
ReadMetadata
```

Các capability khác phải explicit.

---

# 14. Vì sao cần capability?

Nếu không:

```axiom
comptime {
    network_download(...);
}
```

có thể làm build:

```text
non-deterministic
unsafe
non-reproducible
```

và compiler trở thành một execution engine tùy ý.

Axiom không nên đi hướng đó.

---

# 15. Explicit capability

Conceptually:

```axiom
comptime fn generate() 
    requires ReadFilesystem
{
    ...
}
```

Tuy nhiên **không nhất thiết expose một effect syntax như `requires` trong v1**.

Có thể ban đầu capability được cấp bởi:

```text
comptime context
compiler configuration
explicit API
```

và compiler kiểm tra capability nội bộ.

Điều này phù hợp quyết định trước đó:

> Axiom không có general user-visible effect system trong v1.

---

# 16. Comptime filesystem

Cho phép API compiler/std chuyên dụng:

```axiom
comptime {
    let data = comptime_fs.read("assets/data.bin");
}
```

Compiler ghi dependency:

```text
source.ax
   ↓
data.bin
```

vào incremental dependency graph.

---

# 17. External input là một phần của identity

Nếu:

```text
comptime read("config.json")
```

thì semantic identity không chỉ là:

```text
source code
```

mà:

```text
source
+
config.json content/hash
```

Nếu file thay đổi:

```text
→ comptime result invalidated
```

---

# 18. Determinism

Comptime phải deterministic với declared inputs.

Ví dụ:

```text
source
+
explicit filesystem files
+
compiler target
+
declared configuration
```

→ cùng kết quả.

Không được implicit:

```text
current time
random
network
machine hostname
CPU count
```

ảnh hưởng kết quả mà compiler không biết.

---

# 19. Reproducible build mode

Có thể có:

```text
--reproducible
```

Khi bật:

```text
Time
Random
Network
Environment
```

bị cấm hoặc phải được freeze/declaratively supplied.

Ví dụ:

```text
BUILD_TIMESTAMP
```

được truyền như explicit input.

---

# 20. Reflection

Reflection mặc định là **compile-time reflection**.

Ví dụ:

```axiom
comptime {
    let fields = reflect(Point).fields();
}
```

Compiler có thể trả metadata:

```text
Point
├── x: f64
└── y: f64
```

Không cần runtime reflection.

---

# 21. `Type`

Compiler có thể có compile-time value:

```text
Type
```

Ví dụ conceptually:

```axiom
const T: Type = type_of(Point);
```

`Type` này tồn tại ở comptime.

Không có nghĩa executable chứa:

```text
RuntimeTypeObject
```

---

# 22. Runtime type object không mặc định

Nếu:

```axiom
fn type_name<T>() -> String
```

không có nghĩa Axiom phải nhúng metadata của mọi `T`.

Nếu muốn runtime reflection:

```text
explicit metadata emission
```

mới tạo data.

---

# 23. Reflection API

Nên thiết kế theo typed metadata:

```text
TypeInfo
FieldInfo
VariantInfo
TraitInfo
FunctionInfo
AttributeInfo
```

nhưng chúng có thể là compiler-only values.

Ví dụ:

```axiom
comptime fn fields(T: Type) -> ...
```

---

# 24. Không textual macro

Axiom **không nên** có:

```text
macro_expand("struct Foo { ... }")
```

hoặc:

```text
generate_source_string(...)
```

rồi parser lại string đó.

Thay vào đó:

```text
comptime
    ↓
Typed declaration generation
    ↓
HIR
```

---

# 25. Typed generation

Ví dụ muốn generate struct:

```text
comptime metadata
      ↓
DeclarationBuilder
      ↓
StructDecl
      ↓
HIR
```

Compiler không phải:

```text
string
↓
lexer
↓
parser
```

lần nữa.

Điều này giúp:

- không lỗi syntax generation khó hiểu
- không injection qua text
- compiler giữ type identity
- diagnostics tốt hơn

---

# 26. Nhưng không cho arbitrary HIR mutation

Không nên expose:

```text
modify MIR node 1847
replace type
inject arbitrary compiler pass
```

cho user comptime.

Nếu làm vậy, Axiom sẽ biến compiler API thành một framework plugin khổng lồ.

V1:

> Comptime có thể tạo **typed declarations/data**, không tùy ý sửa compiler IR.

---

# 27. `@derive`

Axiom có thể có compiler-known derive:

```axiom
@derive(Debug, Clone, Eq, Hash)
struct User {
    id: u64,
    name: String,
}
```

Compiler thực hiện:

```text
derive request
↓
comptime/compiler intrinsic
↓
typed implementation
```

Không cần procedural macro language.

---

# 28. Derive không phải magic runtime

Ví dụ:

```axiom
@derive(Clone)
struct Point { ... }
```

sau compilation:

```text
Point::clone
```

là function bình thường.

Không có:

```text
RuntimeDeriveEngine
```

---

# 29. Compiler-known derives v1

Nên giới hạn ban đầu:

```text
Debug
Clone
Eq
Hash
Default
```

và các trait cơ bản khác.

Không cho user tạo compiler plugin tùy ý.

---

# 30. `@cfg` và `comptime`

Phân biệt rõ:

```text
@cfg
    = lựa chọn declaration theo target/config

comptime
    = thực thi tính toán
```

Ví dụ:

```axiom
@cfg(os = "windows")
fn foo() { ... }

@cfg(os = "linux")
fn foo() { ... }
```

Trong khi:

```axiom
comptime fn calculate_size() -> usize {
    ...
}
```

là computation.

---

# 31. Target information

Comptime được đọc:

```text
target.arch
target.os
target.ptr_width
target.endian
target.features
target.abi
```

Ví dụ:

```axiom
comptime {
    if target.arch == "x86_64" {
        ...
    }
}
```

---

# 32. Nhưng target selection nên dùng `@cfg`

Nếu chỉ muốn loại bỏ code:

```axiom
@cfg(arch = "x86_64")
fn optimized() { ... }
```

nên dùng `@cfg`.

Nếu muốn tính toán:

```axiom
const REGISTER_SIZE =
    comptime calculate_register_size(target);
```

thì dùng comptime.

---

# 33. Generic + comptime

Ví dụ:

```axiom
comptime fn make_default<T>() -> T {
    ...
}
```

Compiler phải resolve:

```text
T
↓
TypeId
↓
comptime execution
```

Comptime có thể dùng:

- type information
- associated types
- constants
- reflection

nhưng không được bỏ qua ownership/type safety.

---

# 34. Reflection + generic

Ví dụ conceptually:

```axiom
comptime fn field_count<T>() -> usize {
    return reflect(T).fields().len();
}
```

Sau đó:

```axiom
const N = field_count<MyStruct>();
```

Compiler tính:

```text
MyStruct
→ reflection
→ fields
→ count
→ constant
```

Runtime không cần reflection.

---

# 35. Reflection + layout

Comptime có:

```text
size_of(T)
align_of(T)
offset_of(T, field)
```

Nhưng phải phân biệt:

```text
type semantics
```

với:

```text
representation contract
```

Ví dụ `offset_of` quan sát physical layout.

Do đó nếu programmer phụ thuộc layout ổn định giữa compiler versions:

```text
@repr(C)
```

hoặc representation contract tương ứng phải được dùng.

---

# 36. Comptime-generated code phải re-verify

Đây là invariant cực mạnh:

```text
Comptime
   ↓
Generated HIR
   ↓
Type checking
   ↓
Trait solving
   ↓
Ownership
   ↓
Capability
   ↓
MIR
```

Không có đường tắt:

```text
comptime generated code → machine
```

---

# 37. Comptime không bypass unsafe

Ngay cả:

```axiom
comptime {
    unsafe {
        ...
    }
}
```

cũng không được biến thành:

```text
"compiler trusts everything"
```

`unsafe` chỉ bypass những proof obligations được định nghĩa là unsafe boundary.

Comptime capability sandbox vẫn còn.

---

# 38. Comptime panic

Nếu:

```axiom
comptime fn divide(a, b) {
    if b == 0 {
        panic();
    }
}
```

thì:

```text
runtime panic
```

không xảy ra.

Compiler nhận:

```text
comptime panic
```

và phát diagnostic:

```text
AXxxxx comptime evaluation failed
```

kèm source span và evaluation trace nếu có.

---

# 39. Comptime panic khác ICE

Rất quan trọng:

```text
User comptime panic
    ≠
Compiler internal assertion failure
```

Ví dụ:

```text
AX2101 COMPTIME_EVAL_FAILED
```

là user error.

Trong khi:

```text
ICE-001
```

là compiler bug.

---

# 40. Comptime memory

Comptime VM vẫn cần memory model:

```text
stack
arena
values
aggregates
```

nhưng đây là compiler-internal.

Memory được giải phóng khi evaluation kết thúc.

Không có runtime heap leak từ comptime.

---

# 41. Comptime Drop

Nếu comptime tạo:

```axiom
let x = SomeResource(...);
```

và resource có Drop:

```text
evaluation end
↓
Drop
```

giống runtime.

Nhưng external resource capability phải có policy rõ ràng.

---

# 42. External tool execution

Có thể hỗ trợ sau:

```text
ExecuteTool
```

Ví dụ:

```text
comptime
    run("codegen-tool", ...)
```

nhưng **không phải mặc định**.

Nếu bật:

```text
tool command
arguments
environment
output
version
```

nên trở thành declared dependency.

---

# 43. Network

Không nên mặc định cho:

```text
comptime network
```

Build system không nên âm thầm download dependency khi compiler compile source.

Nếu muốn:

```text
explicit build step
```

hoặc explicit capability.

---

# 44. Random

Random cũng phải explicit.

Không:

```text
comptime random()
```

mà không ảnh hưởng cache key.

Nếu deterministic random:

```text
comptime random(seed)
```

thì `seed` là input.

---

# 45. Incremental cache

Comptime result có thể cache:

```text
ComptimeCacheKey {
    function
    arguments
    target
    compiler_semantic_version
    external_inputs
}
```

Nếu tất cả giống nhau:

```text
→ reuse result
```

---

# 46. Cache không được thay đổi semantics

Nếu comptime function có external side effect:

```text
WriteGenerated
ExecuteTool
```

compiler phải biết effect đó để không đơn giản cache như pure computation.

Do đó:

```text
pure deterministic comptime
```

cache dễ.

```text
external-effect comptime
```

cần dependency/effect tracking.

---

# 47. Parallel comptime

Các evaluation độc lập:

```text
A
B
C
```

có thể compiler chạy:

```text
A ─┐
B ─┼→ parallel
C ─┘
```

nhưng:

```text
comptime semantics
```

không được phụ thuộc execution order.

---

# 48. Comptime source generation

Nếu cần generate nhiều declarations:

```text
comptime
    ↓
Declaration list
    ↓
HIR insertion
```

Ví dụ:

```text
generate enum variants
generate serialization methods
generate lookup tables
generate platform bindings
```

rất phù hợp.

---

# 49. Comptime không phải macro hygiene problem

Vì không generate source text nên không phải xử lý hàng loạt vấn đề:

```text
macro variable capture
identifier hygiene
token pasting
source reparsing
macro expansion order
```

Compiler giữ trực tiếp:

```text
SymbolId
TypeId
DeclId
FieldId
```

---

# 50. Comptime + attributes

Reflection có thể đọc:

```axiom
@serializable
struct User {
    @required
    id: u64,
}
```

Comptime reflection:

```text
attributes(User)
```

→ metadata typed.

Không cần parse comment/string.

---

# 51. Attribute values

Attributes nên có typed arguments:

```axiom
@align(64)
@repr(C)
@export("foo")
```

thay vì mọi thứ là raw text.

Compiler có thể validate sớm.

---

# 52. Comptime-generated attributes

Không nên cho arbitrary dynamic mutation của compiler attributes trong v1.

Ví dụ không:

```text
generate raw "@something(...)"
```

mà nên có typed builder/API nếu feature thực sự cần.

---

# 53. Reflection privacy

Comptime reflection phải tôn trọng visibility.

Ví dụ module khác không thể tự động inspect:

```text
private fields
private declarations
```

trừ khi compiler API/attribute cho phép.

Không để reflection trở thành cách bypass module encapsulation.

---

# 54. Reflection không phá ownership

Nếu reflection trả:

```text
FieldInfo
```

thì đó là metadata.

Không phải:

```text
runtime pointer to field
```

Nếu muốn truy cập field dynamically ở runtime, đó là một abstraction khác và phải explicit.

---

# 55. Runtime reflection

Axiom có thể hỗ trợ:

```text
@emit_metadata
```

hoặc tương đương.

Ví dụ:

```axiom
@runtime_reflection
struct User {
    ...
}
```

Compiler lúc đó emit:

```text
.rodata
TypeMetadata
FieldMetadata
...
```

Nhưng đây là opt-in.

---

# 56. Không runtime metadata mặc định

Một chương trình:

```axiom
fn main() {
    ...
}
```

không vì Axiom có reflection mà tự nhiên chứa:

```text
all type names
all field names
all trait names
all function signatures
```

Điều này rất quan trọng với mục tiêu binary nhỏ.

---

# 57. Comptime và binary size

Code:

```text
comptime
    calculate_table()
```

nếu chỉ materialize:

```text
const table
```

thì compiler có thể bỏ hoàn toàn:

```text
calculate_table()
```

khỏi executable.

Đây chính là:

```text
ACOMP-27
Unmaterialized Comptime Code Is Erased
```

---

# 58. Ví dụ mạnh

```axiom
comptime fn make_sine_table<const N: usize>() -> [N]f32 {
    ...
}

const TABLE = make_sine_table<1024>();
```

Executable chỉ chứa:

```text
TABLE
```

Không chứa:

```text
make_sine_table
comptime VM
reflection engine
```

nếu không được runtime sử dụng.

---

# 59. Comptime và code generation

Pipeline đầy đủ:

```text
Source
  ↓
AST
  ↓
HIR
  ↓
Comptime evaluation
  ↓
Generated typed declarations
  ↓
HIR
  ↓
Type/Trait
  ↓
Ownership/Capability
  ↓
MIR
```

Comptime nằm **trước semantic verification cuối cùng**, không bypass nó.

---

# 60. Invariants

```text
ACOMP-46  Comptime Is Axiom Semantics Executed At Compile Time
ACOMP-47  Comptime Does Not Define A Second Language
ACOMP-48  Comptime Shares The Core Type System
ACOMP-49  Comptime Shares Ownership Semantics
ACOMP-50  Comptime Shares Capability Semantics
ACOMP-51  Comptime Values Are Compile-Time Entities
ACOMP-52  Comptime Resources Cannot Implicitly Escape To Runtime
ACOMP-53  Runtime Materialization Is Explicit
ACOMP-54  Comptime Execution Is Deterministic Within Declared Inputs
ACOMP-55  External Inputs Are Part Of Comptime Identity
ACOMP-56  Undeclared External State Cannot Affect Reproducible Evaluation
ACOMP-57  Comptime Capabilities Are Explicit
ACOMP-58  Comptime Has A Compiler-Internal Execution Environment
ACOMP-59  Comptime VM Is Not Part Of The Runtime
ACOMP-60  Comptime Panic Produces A Compiler Diagnostic
ACOMP-61  Comptime Panic Is Distinct From Compiler ICE
ACOMP-62  Comptime Drop Uses Normal Drop Semantics
ACOMP-63  Comptime Cannot Bypass Ownership Verification
ACOMP-64  Comptime Cannot Bypass Capability Verification
ACOMP-65  Generated Code Is Re-verified
ACOMP-66  Typed Generation Is Preferred Over Textual Generation
ACOMP-67  Generated Declarations Preserve Stable Compiler Identity
ACOMP-68  Arbitrary Compiler IR Mutation Is Not Exposed
ACOMP-69  Reflection Is Compile-Time By Default
ACOMP-70  Reflection Does Not Imply Runtime Metadata
ACOMP-71  Runtime Reflection Requires Explicit Metadata Emission
ACOMP-72  Reflection Respects Visibility
ACOMP-73  Type Is A Compile-Time Value
ACOMP-74  Runtime Type Objects Are Not Required
ACOMP-75  size_of/align_of/offset_of Are Compile-Time Queries
ACOMP-76  Representation Observation Respects Repr Contracts
ACOMP-77  @cfg Selects Code; Comptime Computes Values/Declarations
ACOMP-78  Compiler-Known Derives Do Not Require Runtime Machinery
ACOMP-79  Comptime Dependencies Participate In Incremental Compilation
ACOMP-80  Comptime Cache Preserves Semantics
ACOMP-81  Independent Comptime Evaluations May Run In Parallel
ACOMP-82  External Effects Are Capability-Gated
ACOMP-83  Reproducible Builds May Restrict External Capabilities
ACOMP-84  Unmaterialized Comptime Code Is Erased
ACOMP-85  Comptime Does Not Imply Runtime Allocation
```

---

# 61. BOOTSTRAP-016 gate

```text
const evaluation                 ✓
comptime function                ✓
comptime block                   ✓
comptime VM                      ✓
same type semantics              ✓
same ownership semantics         ✓
same Drop semantics              ✓
typed reflection                ✓
Type compile-time value          ✓
field reflection                ✓
variant reflection               ✓
attributes                       ✓
size_of/align_of/offset_of       ✓
generic + comptime               ✓
typed declaration generation     ✓
generated HIR re-verification    ✓
comptime diagnostics             ✓
comptime cache                   ✓
incremental dependencies         ✓
target information               ✓
reproducible mode                ✓
runtime metadata opt-in          ✓
comptime code erased             ✓
no runtime comptime VM           ✓
```

---

## Một quyết định kiến trúc tôi đặc biệt khuyến nghị giữ

Axiom có thể đạt metaprogramming rất mạnh bằng **3 tầng**, thay vì tạo macro system riêng:

```text
┌──────────────────────────────┐
│          Runtime             │
│ normal Axiom program         │
└──────────────┬───────────────┘
               │
        explicit materialize
               │
┌──────────────▼───────────────┐
│          Comptime            │
│ Axiom + reflection           │
│ typed generation             │
└──────────────┬───────────────┘
               │
         compiler metadata
               │
┌──────────────▼───────────────┐
│       Compiler Internals      │
│ AST/HIR/MIR/ABI/Backend       │
└──────────────────────────────┘
```

**Không cho tầng Comptime tùy ý sửa MIR/compiler internals.**

Điều này giúp Axiom vừa có khả năng metaprogramming rất mạnh, vừa giữ compiler architecture sạch và deterministic.

### Và một hệ quả rất hay

Sau BOOT-013 → BOOT-016, Axiom đã có:

```text
Generic
   +
Trait
   +
Closure
   +
Comptime
   +
Reflection
```

đủ để xây phần lớn `std` bằng chính Axiom.

**Bước tiếp theo nên là BOOTSTRAP-017 — Async/Future + State Machine**, vì đây là abstraction cuối cùng khá lớn trước khi chuyển sang các phần concurrency/runtime và sau đó quay lại tối ưu hóa compiler.