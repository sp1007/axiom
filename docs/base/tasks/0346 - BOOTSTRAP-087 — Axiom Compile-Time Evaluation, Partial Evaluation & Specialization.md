# BOOTSTRAP-087 — Axiom Compile-Time Evaluation, Partial Evaluation & Specialization

**Trạng thái: FROZEN**

Đây là phần rất quan trọng vì Axiom đã có `const`, `comptime`, const generics, reflection, generic specialization và incremental compilation. Nếu không chốt ranh giới rõ ràng, compiler rất dễ biến thành một hệ thống “hai ngôn ngữ”: một ngôn ngữ runtime và một ngôn ngữ compile-time.

Axiom chọn hướng:

> **Comptime không phải ngôn ngữ thứ hai. Comptime là Axiom thông thường được thực thi sớm hơn.**

Và:

> **Compiler được phép tự động thực hiện partial evaluation khi chứng minh được nó không thay đổi semantics.**

---

# 1. Ba mức evaluation

Axiom có ba khái niệm:

```text
const
comptime
runtime
```

### `const`

Giá trị compile-time.

```ax
const PAGE_SIZE = 4096
const VERSION = 3
```

### `comptime`

Code bắt buộc chạy tại compile-time:

```ax
comptime {
    ...
}
```

hoặc:

```ax
comptime fn make_table(...) -> ...
```

### Runtime

Code bình thường:

```ax
fn calculate(x: i32) -> i32 {
    ...
}
```

---

# 2. `const` không phải macro

`const` chỉ tạo một giá trị compile-time.

Không:

```text
text substitution
AST substitution
token substitution
```

Compiler vẫn type-check bình thường.

---

# 3. `comptime` không phải macro language

Comptime có thể tính toán:

```text
values
types
declarations
metadata
generated declarations
```

nhưng kết quả phải quay lại pipeline semantic bình thường.

```text
Comptime
   ↓
Generated semantic objects
   ↓
Resolver
   ↓
Type checker
   ↓
Ownership verifier
   ↓
MIR
```

Không được có đường tắt:

```text
comptime → machine code trực tiếp
```

bỏ qua verifier.

---

# 4. Comptime dùng cùng type system

Ví dụ:

```ax
comptime fn square(x: i32) -> i32 {
    x * x
}
```

không có một kiểu `ComptimeInt` bí mật.

Nó dùng:

```text
i32
```

thật.

---

# 5. Ownership cũng giống runtime

Nếu comptime tạo một owning value:

```ax
comptime fn build() -> Buffer {
    ...
}
```

thì compiler vẫn phải theo dõi:

```text
Move
Copy
Clone
Drop
```

---

# 6. Capability cũng giống runtime

Nếu comptime có:

```ax
comptime {
    let v = view(data)
}
```

thì `view` vẫn là capability.

Không được vì đang compile-time mà bỏ qua lifetime/provenance rules.

---

# 7. Unsafe không bypass comptime sandbox

Một điểm cực kỳ quan trọng:

```ax
comptime {
    unsafe {
        ...
    }
}
```

**không** có nghĩa:

```text
được đọc filesystem tùy ý
được gọi process
được truy cập network
```

Unsafe chỉ giải quyết machine-level safety.

Comptime external effects vẫn phải qua capability system.

---

# 8. Comptime capability

Các external capabilities đã frozen:

```text
ReadSource
ReadMetadata
```

và capability mạnh hơn:

```text
ReadFilesystem
WriteGenerated
ExecuteTool
Environment
Network
Time
Random
```

---

# 9. Default sandbox

Comptime mặc định chỉ có quyền cần thiết.

Ví dụ:

```ax
comptime fn version() -> String {
    ...
}
```

không tự động được:

```text
read arbitrary file
spawn process
access network
```

---

# 10. Explicit capability request

Nếu cần:

```text
filesystem
```

phải có dependency/capability declaration tương ứng.

Điều này giúp build graph biết:

```text
source
  ↓
comptime dependency
  ↓
filesystem input
```

---

# 11. Comptime dependency trở thành build dependency

Nếu:

```ax
comptime fn load_schema(...) ...
```

đọc:

```text
schema.json
```

thì file đó phải nằm trong dependency graph.

Nếu thay đổi:

```text
schema.json
```

compiler biết cần invalidate phần nào.

---

# 12. Cache identity

Kết quả comptime không thể cache chỉ bằng source code.

Cache key phải bao gồm:

```text
source fingerprint
compiler semantic version
target
configuration
features
comptime inputs
capabilities
```

---

# 13. Time/Random

Các input như:

```text
Time
Random
Environment
Network
```

làm comptime không deterministic.

Reproducible build profile có thể:

```text
forbid
freeze
or explicitly declare
```

các input này.

---

# 14. Comptime result

Nếu:

```ax
const TABLE = make_table()
```

thì kết quả có thể được materialize vào executable:

```text
.rodata
.data
code
metadata
```

tùy representation.

Không cần runtime computation.

---

# 15. Materialization là boundary

Comptime value:

```text
compiler world
```

không tự động trở thành:

```text
runtime resource
```

Ví dụ compiler có một file handle trong quá trình comptime.

Không được:

```text
return file_handle
```

và biến nó thành runtime file handle.

---

# 16. Compile-time resource lifetime

Resource dùng trong comptime:

```text
open
read
write
close
```

phải được cleanup trong compiler execution environment.

Không kéo resource lifetime sang executable.

---

# 17. Generated declarations

Comptime có thể tạo declaration có type:

```text
struct
enum
fn
const
trait implementation
```

nhưng declaration phải quay lại:

```text
resolver
type checker
trait solver
verification
```

---

# 18. Không cho arbitrary IR mutation

Core v1 không có:

```text
modify MIR arbitrarily
modify backend IR arbitrarily
inject machine instruction
```

Comptime generation là **typed generation**.

---

# 19. `@derive`

Compiler-known generation:

```ax
@derive(Eq, Hash)
struct User {
    id: u64
}
```

được xem như một dạng typed compile-time generation.

---

# 20. Vì sao không procedural macro?

Không phải vì Axiom không đủ mạnh.

Mà vì procedural macro tạo thêm:

```text
syntax language
AST API
macro hygiene
expansion ordering
macro debugging
macro dependency
macro compatibility
```

Core hiện tại chưa cần.

---

# 21. Partial evaluation

Đây là phần compiler tự động.

Ví dụ:

```ax
fn multiply(x: i32) -> i32 {
    x * 10
}
```

Compiler có thể specialize khi:

```text
x = 7
```

thành:

```text
70
```

mà programmer không cần viết `comptime`.

---

# 22. `comptime` và optimizer khác nhau

Đây là ranh giới quan trọng.

### `comptime`

Programmer yêu cầu:

> Giá trị này phải được tính trước runtime.

### Optimizer

Compiler có quyền:

> Nếu có thể chứng minh tương đương, tôi sẽ tính trước.

---

# 23. Ví dụ

```ax
const A = expensive_compile_function()
```

→ bắt buộc compile-time.

Trong khi:

```ax
fn f() -> i32 {
    expensive_compile_function()
}
```

nếu không phải `comptime`, compiler **có thể** fold nó nếu semantics cho phép, nhưng không phải language guarantee.

---

# 24. Constant folding

OptIR có thể biến:

```text
1 + 2
```

thành:

```text
3
```

đây là optimization.

Không tạo dependency semantics vào `comptime`.

---

# 25. Constant propagation

Ví dụ:

```ax
let a = 10
let b = a * 2
return b
```

→:

```text
return 20
```

---

# 26. Branch specialization

```ax
if DEBUG {
    ...
} else {
    ...
}
```

nếu `DEBUG` là compile-time constant:

```text
dead branch
```

được loại bỏ.

---

# 27. Generic specialization

```ax
fn max<T: Ord>(a: T, b: T) -> T
```

khi instantiate:

```text
T = i32
```

compiler tạo specialized instance.

---

# 28. Specialization không phải runtime reflection

Không cần:

```text
type_info
generic metadata
```

trong executable.

---

# 29. Specialization pipeline

```text
Generic definition
      ↓
Substitution
      ↓
Constraint solving
      ↓
Typed HIR
      ↓
MIR
      ↓
Verification
      ↓
Optimization
```

---

# 30. Specialization phải re-verify

Không được giả định:

```text
generic đã verified
```

là:

```text
mọi specialization đã verified
```

Concrete instance phải đi qua semantic checks cần thiết.

---

# 31. Partial evaluation của function

Compiler có thể tạo:

```text
f(x, constant_A)
```

thành:

```text
f_specialized(x)
```

nếu có lợi.

Đây là compiler internal.

Không cần syntax.

---

# 32. Specialization explosion

Không instantiate mọi combination vô hạn.

Compiler cần:

```text
specialization cache
cost model
deduplication
instantiation limits
```

---

# 33. Generic deduplication

Hai generic instances semantic + target equivalent:

```text
f<i32>
```

ở nhiều modules có thể merge qua:

```text
COMDAT/linkonce
```

hoặc compiler-level dedup trước linker.

---

# 34. Comptime specialization

Programmer có thể yêu cầu specialization khi semantics cần:

```ax
comptime fn make(...)
```

Nhưng không được biến mọi generic thành compile-time code.

---

# 35. Type-level computation

Comptime có thể tính:

```text
type metadata
field count
field offsets
enum variants
```

thông qua reflection.

---

# 36. `Type` là compile-time value

Ví dụ conceptual:

```ax
comptime fn inspect<T>() {
    let size = size_of<T>()
    ...
}
```

`Type` không mặc định tồn tại runtime.

---

# 37. Runtime reflection

Nếu muốn runtime metadata:

```text
explicit metadata emission
```

Ví dụ:

```text
@reflect
```

hoặc library/compiler contract tương đương.

Không tự động nhúng toàn bộ type database vào executable.

---

# 38. Reflection phải tôn trọng visibility

Comptime reflection không được bypass:

```text
private
module visibility
representation contract
```

trừ compiler-internal mechanisms.

---

# 39. `size_of`

```ax
size_of<T>()
```

là compile-time.

Kết quả có thể dùng trong:

```text
array size
alignment
layout decisions
static assertions
```

---

# 40. `offset_of`

```ax
offset_of<T>(field)
```

chỉ có ý nghĩa khi layout contract phù hợp.

Nếu default struct layout compiler-controlled, programmer không được giả định offset ổn định giữa builds.

---

# 41. Compile-time assertion

Axiom nên có:

```ax
comptime assert(condition)
```

hoặc syntax compiler-defined tương đương.

Ví dụ:

```ax
comptime assert(size_of<Header>() == 16)
```

Nếu false:

```text
compile error
```

---

# 42. Compile-time diagnostic

Comptime failure phải tạo diagnostic có:

```text
error code
source span
comptime stack/context
input dependency
```

nếu có.

---

# 43. Comptime panic

Nếu comptime code:

```ax
panic(...)
```

→ compiler diagnostic.

Không tạo panic runtime.

---

# 44. Comptime infinite loop

Compiler phải có protection:

```text
evaluation budget
recursion limit
instruction budget
memory budget
```

để tránh compiler bị treo vô hạn.

---

# 45. Budget failure

Nếu vượt budget:

```text
compile-time evaluation exceeded configured limit
```

Không phải ICE.

User có thể điều chỉnh giới hạn bằng compiler/build configuration.

---

# 46. Recursion

Comptime recursion được phép nếu compiler có thể execute.

Không cần cấm recursive functions.

---

# 47. Comptime allocation

Compiler execution có thể allocate internal memory.

Nhưng:

```text
compiler heap
```

không phải:

```text
program heap
```

---

# 48. Comptime Drop

Compiler phải Drop các temporary/resource đúng semantics.

Nhưng physical deallocation do compiler runtime quản lý.

---

# 49. Comptime `Box`

Một `Box<T>` tạo trong comptime không ngụ ý executable cần heap allocation.

Nếu materialized thành constant data:

```text
compiler allocation
      ↓
serialized constant
```

---

# 50. Comptime generated code

Ví dụ conceptual:

```ax
comptime fn generate_lookup() -> ...
```

Kết quả phải trở thành typed declaration/value.

Sau đó compiler tiếp tục:

```text
Resolve
Type
Trait
Ownership
MIR
Verify
```

---

# 51. Generated code không được bypass safety

Đây là invariant rất quan trọng.

AI-generated hoặc comptime-generated code đều phải qua cùng verifier.

Không có:

```text
"compiler-generated nên trusted"
```

---

# 52. AI integration

Axiom có thể expose:

```text
semantic metadata
diagnostics
MIR
verification facts
specialization decisions
```

cho AI tooling.

Nhưng AI không được trở thành một phần semantic compiler.

---

# 53. AI không quyết định type

Ví dụ compiler gặp:

```ax
x + y
```

AI không được quyết định:

```text
"chắc programmer muốn f64"
```

Type resolver phải deterministic.

AI chỉ có thể:

```text
explain
suggest fix
generate source
```

---

# 54. Compile-time caching

Caching nên chia nhiều lớp:

```text
parse cache
semantic cache
comptime cache
generic cache
optimization cache
codegen cache
object cache
link cache
```

---

# 55. Comptime cache invalidation

Nếu function comptime không đổi nhưng input:

```text
schema.json
```

đổi:

```text
invalidate dependent result
```

không invalidate toàn project.

---

# 56. Dependency graph

Ví dụ:

```text
A.ax
 └── comptime read
       └── schema.json
```

Compiler DB lưu dependency edge.

---

# 57. Parallel comptime

Hai evaluation độc lập:

```text
C1
C2
```

có thể chạy song song.

Kết quả phải giống serial execution.

---

# 58. External side effects

Nếu comptime có:

```text
WriteGenerated
ExecuteTool
Network
```

thì compiler phải xử lý dependency/effect ordering.

Hai side effects có quan hệ ordering không được tùy tiện chạy song song.

---

# 59. Reproducible mode

Trong reproducible build:

```text
Time
Random
Environment
Network
```

phải được:

```text
forbid
or explicitly captured
```

để build identity xác định được.

---

# 60. Target-aware comptime

Comptime chạy trên:

```text
host compiler
```

nhưng semantic target là:

```text
target program
```

Hai khái niệm phải tách biệt.

---

# 61. Ví dụ cross compile

Build:

```text
x86-64 Linux
```

target:

```text
ARM64 Android
```

thì:

```text
size_of<T>
align_of<T>
target features
ABI
pointer width
```

phải dựa vào target khi semantics yêu cầu.

---

# 62. Host capabilities

Ngược lại, external tool:

```text
ExecuteTool
ReadFilesystem
```

chạy trên host.

Do đó comptime context cần:

```text
HostContext
TargetContext
```

tách biệt.

---

# 63. Comptime target feature

Có thể query:

```text
target.arch
target.os
target.pointer_width
target.features
```

ở compile-time.

---

# 64. `@cfg`

`@cfg` dùng để chọn declaration/code:

```ax
@cfg(target_os = "windows")
fn foo() { ... }
```

Code không được chọn không đi vào semantic pipeline tương ứng.

---

# 65. `comptime if`

Comptime có thể tính branch:

```ax
comptime if CONDITION {
    ...
}
```

Khác `@cfg` ở chỗ:

```text
@cfg
→ configuration selection

comptime
→ computation
```

---

# 66. Không trộn `@cfg` với value computation

Không nên dùng:

```text
comptime string parsing
```

để thay thế mọi configuration.

Configuration cần declarative và dễ inspect.

---

# 67. Partial evaluation và closures

Compiler có thể specialize closure environment:

```text
closure
+ constant capture
```

→ eliminate captured constant.

---

# 68. Partial evaluation và async

Nếu async function có compile-time-known branch:

```text
if constant {
    ...
}
```

compiler có thể loại bỏ branch trước khi tạo Future state machine.

Điều này giảm:

```text
state fields
suspension states
code size
```

---

# 69. Partial evaluation và GPU

GPU kernel:

```ax
@kernel
fn f<const N>(...)
```

có thể specialize theo:

```text
N
tile size
vector width
target capability
```

compile-time.

---

# 70. Partial evaluation và FFI

Không được specialize foreign function dựa trên giả định compiler không biết.

Foreign calls là conservative boundary trừ khi có contract.

---

# 71. Partial evaluation và unsafe

Unsafe code vẫn phải bảo toàn semantics.

Compiler có thể optimize:

```text
unsafe operation
```

nhưng không được biến một assumption thành semantic fact cho safe code nếu contract chưa được thiết lập.

---

# 72. Compile-time generated unsafe

Generated unsafe code không được exempt khỏi audit.

Compiler phải giữ source provenance:

```text
generated span
→ generator
→ source
```

để diagnostics/debugging.

---

# 73. Comptime source maps

Generated declaration nên có:

```text
SourceSpan
GeneratedSpan
Origin
```

để lỗi:

```text
type mismatch
```

có thể chỉ ra:

```text
generated by X from source Y
```

---

# 74. Deterministic evaluation

Cùng:

```text
source
inputs
compiler semantic version
target
configuration
```

phải cho cùng semantic result.

---

# 75. Compiler parallelism

Compiler có thể thay đổi:

```text
thread scheduling
evaluation order
query order
```

nếu kết quả semantic không đổi.

---

# 76. Memoization

Pure-ish comptime functions có thể memoize.

Nhưng compiler chỉ cache khi dependency/effect semantics cho phép.

Không cache blindly external side-effect computation.

---

# 77. Comptime purity không trở thành source effect system

Axiom không thêm:

```text
@pure
@const_fn
@effect
```

vào Core chỉ để phục vụ optimizer.

Compiler tự phân tích effects nội bộ.

---

# 78. EffectInfo

OptIR đã có:

```text
EffectInfo
```

nên compiler có thể biết:

```text
Pure
ReadOnly
Allocate
Write
IO
Foreign
Panic
Synchronize
```

mà không bắt programmer annotate mọi function.

---

# 79. Compile-time execution eligibility

Compiler có thể tự quyết định:

```text
constant fold
inline
specialize
evaluate
```

nhưng chỉ `const/comptime` mới tạo **language guarantee**.

---

# 80. No accidental runtime dependency

Một comptime-only computation:

```text
const LUT = make_lut()
```

không được kéo:

```text
comptime interpreter
```

vào executable.

---

# 81. Generated data

Nếu kết quả là bảng:

```text
LUT
```

executable chỉ chứa:

```text
.rodata
```

nếu đó là representation tối ưu.

---

# 82. Generated function

Nếu comptime tạo function:

```text
generated fn lookup(...)
```

chỉ machine code cần thiết được emit.

Unused generated declarations có thể bị DCE.

---

# 83. Generated type

Generated type không nhất thiết tồn tại runtime.

Nếu type chỉ phục vụ compile-time:

```text
type metadata
```

có thể bị erase hoàn toàn.

---

# 84. Reflection metadata

Runtime metadata chỉ tồn tại khi programmer/build contract yêu cầu.

Điều này giữ binary nhỏ.

---

# 85. Compile-time serialization

Comptime có thể generate:

```text
serializer
parser
lookup table
state machine
```

thay vì runtime reflection.

Đây là một trong những cơ chế quan trọng để Axiom đạt:

```text
high-level API
+
native performance
+
small binary
```

---

# 86. Derive optimization

Ví dụ:

```ax
@derive(Hash, Eq)
struct User {
    id: u64
    name: Str
}
```

Compiler có thể generate specialized implementation.

Sau optimization:

```text
generic abstraction
→ direct field operations
```

---

# 87. Compile-time code generation không đồng nghĩa code bloat

Compiler phải có:

```text
deduplication
dead declaration elimination
specialization cost model
```

---

# 88. Specialization policy

Compiler có thể chọn:

```text
monomorphize
share implementation
devirtualize
partially specialize
```

tùy cost model.

Semantic result giống nhau.

---

# 89. User control

Compiler flags có thể điều chỉnh:

```text
specialization budget
comptime budget
optimization level
code-size preference
```

nhưng không được thay đổi Core semantics.

---

# 90. Code-size vs speed

Compiler có thể có:

```text
-Osize
-Ospeed
-Obalanced
```

nhưng tất cả phải giữ semantics.

---

# 91. Comptime errors và incremental builds

Một comptime error chỉ invalidate dependent query/subgraph nếu có thể.

Không nhất thiết recompile toàn package.

---

# 92. Comptime and package boundaries

Package có thể export:

```text
public comptime fn
public generated type
public compile-time metadata
```

Interface metadata phải đủ để dependent package evaluate/resolve mà không cần source private.

---

# 93. `.axmeta`

Metadata có thể chứa:

```text
public declarations
type fingerprints
trait information
generic definitions/contracts
repr/ABI
comptime dependency information
```

Không chứa runtime compiler state thừa.

---

# 94. Semantic fingerprint

Comptime result cache phải invalidated khi thay đổi:

```text
semantic meaning
```

chứ không chỉ textual source hash.

---

# 95. Compiler version

Compiler semantic version nằm trong cache identity.

Một compiler bug fix không nhất thiết semantic change, nhưng compiler phải có policy rõ ràng để invalidate khi cần.

---

# 96. Comptime VM

Compiler có thể có:

```text
Comptime VM / interpreter
```

nhưng đây là **compiler implementation**, không phải language runtime.

Executable không link nó.

---

# 97. JIT không phải requirement

Axiom không cần JIT để thực hiện comptime.

Interpreter/VM/compiler evaluation đủ.

---

# 98. Comptime optimization

Compiler có thể optimize chính comptime program:

```text
constant folding
memoization
partial evaluation
parallel evaluation
dead branch elimination
```

nhưng kết quả semantic phải giống execution model.

---

# 99. Fundamental invariant

Toàn bộ hệ thống được rút gọn thành:

```text
Language semantics
       │
       ├── runtime execution
       │
       └── comptime execution
```

**không phải:**

```text
Language A
       +
Language B
```

---

# 100. Frozen Invariants — `ACOMP2-20..100`

**ACOMP2-20** — `const`, `comptime`, and runtime are distinct evaluation modes of the same Axiom language.

**ACOMP2-21** — Comptime is not a second source language.

**ACOMP2-22** — Comptime uses the ordinary Axiom type system.

**ACOMP2-23** — Comptime follows ordinary ownership semantics.

**ACOMP2-24** — Comptime follows ordinary Drop semantics.

**ACOMP2-25** — Comptime follows ordinary capability semantics.

**ACOMP2-26** — Comptime follows ordinary type and trait semantics.

**ACOMP2-27** — Unsafe does not bypass comptime sandbox restrictions.

**ACOMP2-28** — External comptime effects require explicit capabilities.

**ACOMP2-29** — Comptime capabilities participate in dependency tracking.

**ACOMP2-30** — Comptime external inputs contribute to cache identity.

**ACOMP2-31** — Reproducible builds constrain nondeterministic comptime inputs.

**ACOMP2-32** — Comptime values cannot implicitly become runtime external resources.

**ACOMP2-33** — Comptime resources are cleaned up in the compiler execution environment.

**ACOMP2-34** — `const` values are compile-time semantic values, not textual macros.

**ACOMP2-35** — `comptime fn` is callable only during compile-time evaluation.

**ACOMP2-36** — `comptime` blocks execute before required runtime execution.

**ACOMP2-37** — Compile-time failure produces compiler diagnostics rather than runtime panic.

**ACOMP2-38** — Comptime-generated declarations re-enter normal semantic compilation.

**ACOMP2-39** — Generated declarations are subject to normal name resolution.

**ACOMP2-40** — Generated declarations are subject to normal type checking.

**ACOMP2-41** — Generated declarations are subject to ownership verification.

**ACOMP2-42** — Generated declarations are subject to capability verification.

**ACOMP2-43** — Generated declarations are subject to ABI and representation verification when applicable.

**ACOMP2-44** — Core comptime does not permit arbitrary IR mutation.

**ACOMP2-45** — Core comptime does not provide an unrestricted procedural macro language.

**ACOMP2-46** — Typed generation is preferred over textual source generation.

**ACOMP2-47** — `@derive` generation is compiler-known typed generation.

**ACOMP2-48** — Compile-time reflection respects visibility rules.

**ACOMP2-49** — Compile-time reflection respects representation contracts.

**ACOMP2-50** — `Type` is a compile-time semantic value by default.

**ACOMP2-51** — Runtime type metadata is not emitted unless explicitly required.

**ACOMP2-52** — `size_of`, `align_of`, and applicable layout queries are compile-time operations.

**ACOMP2-53** — Default layout contracts do not imply stable physical offsets across builds.

**ACOMP2-54** — Compile-time assertions produce compile-time diagnostics on failure.

**ACOMP2-55** — Comptime evaluation is bounded against uncontrolled resource consumption.

**ACOMP2-56** — Evaluation-budget exhaustion is a normal compiler diagnostic, not an ICE.

**ACOMP2-57** — Comptime allocation is compiler-execution allocation unless explicitly materialized.

**ACOMP2-58** — Compiler allocation does not imply runtime heap allocation.

**ACOMP2-59** — Materialized comptime values use ordinary target representation rules.

**ACOMP2-60** — Comptime-generated data may be emitted directly into static program data.

**ACOMP2-61** — Unused generated declarations may be eliminated.

**ACOMP2-62** — Comptime-generated runtime code may be optimized normally.

**ACOMP2-63** — Partial evaluation is permitted as a compiler optimization.

**ACOMP2-64** — Partial evaluation does not require source-level `comptime`.

**ACOMP2-65** — `comptime` provides a programmer-visible compile-time guarantee.

**ACOMP2-66** — Ordinary optimizer folding provides no stronger compile-time guarantee unless specified.

**ACOMP2-67** — Constant folding must preserve language semantics.

**ACOMP2-68** — Constant propagation must preserve language semantics.

**ACOMP2-69** — Compile-time branch elimination must preserve language semantics.

**ACOMP2-70** — Generic specialization is compile-time semantic specialization.

**ACOMP2-71** — Concrete generic instances are subject to applicable semantic verification.

**ACOMP2-72** — Generic specialization does not imply runtime generic metadata.

**ACOMP2-73** — Generic specialization may be deduplicated when semantic and target contracts permit.

**ACOMP2-74** — Specialization is controlled to prevent unbounded code explosion.

**ACOMP2-75** — Compiler specialization may use a cost model.

**ACOMP2-76** — Specialization policy cannot change program semantics.

**ACOMP2-77** — Partial evaluation may specialize constant arguments.

**ACOMP2-78** — Partial evaluation may specialize closure environments.

**ACOMP2-79** — Partial evaluation may reduce async state-machine size.

**ACOMP2-80** — Partial evaluation may specialize GPU kernels.

**ACOMP2-81** — Foreign calls remain conservative unless an applicable contract exists.

**ACOMP2-82** — Unsafe assumptions cannot automatically become safe semantic facts.

**ACOMP2-83** — Generated unsafe code remains subject to the applicable unsafe boundaries.

**ACOMP2-84** — Generated code retains source provenance where practical.

**ACOMP2-85** — Comptime source mappings support diagnostics and debugging.

**ACOMP2-86** — Independent comptime evaluations may execute in parallel.

**ACOMP2-87** — Parallel comptime execution must be semantically equivalent to valid serial execution.

**ACOMP2-88** — External comptime side effects require ordering where semantics require it.

**ACOMP2-89** — Comptime caching requires dependency-aware invalidation.

**ACOMP2-90** — Comptime cache identity includes semantic compiler version.

**ACOMP2-91** — Comptime cache identity includes target and relevant configuration.

**ACOMP2-92** — Cross-compilation separates host execution context from target semantic context.

**ACOMP2-93** — Target-dependent compile-time queries use target semantics.

**ACOMP2-94** — `@cfg` performs configuration selection, while comptime performs computation/generation.

**ACOMP2-95** — Comptime does not imply a runtime dependency on the comptime evaluator.

**ACOMP2-96** — Compiler optimizations may erase compile-time abstractions completely.

**ACOMP2-97** — Runtime reflection is explicit rather than implicit.

**ACOMP2-98** — AI tooling may consume comptime/semantic metadata but cannot define language semantics.

**ACOMP2-99** — Comptime, specialization, and optimization share semantic foundations but remain distinct mechanisms.

**ACOMP2-100** — Axiom compile-time execution provides strong compile-time guarantees without creating a second programming language or mandatory runtime.

---

# Điểm kiến trúc rất đáng giá của Axiom

Sau BOOTSTRAP-087, mô hình compiler có thể được nhìn như:

```text
                    Axiom Program
                          │
             ┌────────────┴────────────┐
             │                         │
        Compile-time               Runtime
             │                         │
       const/comptime              normal code
             │                         │
             └────────────┬────────────┘
                          ↓
                  Same Type System
                          ↓
                   Same Semantics
                          ↓
                     Same MIR
                          ↓
                  Same Verification
                          ↓
                    Optimization
```

Trong khi optimizer có thêm một con đường:

```text
Runtime code
     ↓
Constant Analysis
     ↓
Partial Evaluation
     ↓
Specialization
     ↓
Optimized Runtime Code
```

Điều này rất phù hợp với mục tiêu Axiom: **ngôn ngữ có khả năng biểu đạt cao nhưng abstraction không nhất thiết xuất hiện trong binary**.

Đặc biệt, nó cho phép các hệ thống sau này như:

```text
Tensor<T, Shape>
SIMD<T, N>
GPU Kernel<Tile>
Serialization
Reflection
FFI binding generation
GUI declarations
AI-generated code
```

đều tận dụng cùng một cơ chế `comptime + generics + reflection + specialization`, thay vì mỗi subsystem lại phát minh một macro/metaprogramming mechanism riêng.

---

## Bước tiếp theo

**BOOTSTRAP-088 — Axiom SIMD, Vector Types, Auto-Vectorization & Portable Vector Semantics**

Phần này sẽ chốt một vấn đề rất quan trọng đối với mục tiêu **nhanh bằng/hơn C/C++**:

```text
vector<T, N>
SIMD
portable vector
mask
gather/scatter
horizontal reduction
alignment
vectorization
alias analysis
AVX2 / AVX-512
NEON
SVE
RISC-V Vector
GPU relationship
```

và đặc biệt xác định **SIMD có phải Core type hay chỉ là compiler intrinsic/library abstraction**, để Axiom vừa có SIMD hiệu năng cao vừa không biến Core thành một đống target-specific instruction.