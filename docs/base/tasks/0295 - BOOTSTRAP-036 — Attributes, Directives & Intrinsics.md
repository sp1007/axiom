Tiếp tục với **BOOTSTRAP-036 — Attributes, Compiler Directives & Intrinsics**.

Đây là lúc cần ngăn Axiom rơi vào tình trạng có quá nhiều `@xxx` nhưng không biết cái nào thực sự là ngữ nghĩa ngôn ngữ, cái nào chỉ là hint cho compiler.

# BOOTSTRAP-036 — Attributes, Directives & Intrinsics

## 1. Tách 4 loại annotation

Axiom nên phân loại attribute thành 4 nhóm:

```text
Semantic Attribute
ABI / Representation Attribute
Optimization Hint
Target/System Attribute
```

Ví dụ:

```text
@repr(C)        → ABI
@export("foo")  → ABI
@inline         → optimization hint
@kernel         → execution-domain semantic
@syscall        → system ABI
@test            → tooling/build
```

Điều quan trọng:

> **Attribute không phải một ngôn ngữ thứ hai.**

---

# 2. Không cho arbitrary attributes

Không nên cho:

```axiom
@anything(...)
```

và compiler tự đoán.

Compiler phải có registry:

```text
AttributeRegistry
    ↓
name
kind
target
arguments
validation
semantic effect
```

Unknown attribute:

```text
ERROR_UNKNOWN_ATTRIBUTE
```

trừ namespace dành riêng cho tooling.

---

# 3. Namespace attribute

Để tránh xung đột package/tool:

```axiom
@axiom.repr(C)
@tool.some_attribute(...)
```

Nhưng Core có thể dùng short form:

```axiom
@repr(C)
```

Các attribute compiler-defined được reserve namespace `axiom`.

---

# 4. Attribute không thay đổi type semantics nếu chỉ là hint

Ví dụ:

```axiom
@inline
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

`@inline` không được biến:

```text
i32 + i32
```

thành semantic khác.

Nó chỉ là:

```text
optimization preference
```

---

# 5. Có 3 mức độ mạnh

Tôi đề xuất compiler phân loại:

### HINT

Compiler có thể bỏ qua:

```text
@inline
@noinline
@cold
```

### CONTRACT

Compiler **phải tôn trọng**:

```text
@repr(C)
@align(64)
@export("foo")
```

### SEMANTIC

Thay đổi semantics:

```text
@kernel
@tls
@interrupt
@syscall
```

---

# 6. Attribute registry

Conceptual:

```text
Attribute {
    name
    namespace
    kind
    allowed_targets
    arguments
    semantic_effect
    safety
}
```

Ví dụ:

```text
@inline
    kind = Hint
    target = Function

@repr(C)
    kind = ABIContract
    target = Type

@kernel
    kind = Semantic
    target = Function
```

---

# 7. `@repr`

Đã có:

```axiom
@repr(C)
@repr(transparent)
@repr(packed)
@repr(align(N))
```

Không nên để:

```axiom
@repr(random_internal_layout)
```

là user-facing.

Default layout vẫn compiler-controlled.

---

# 8. `@repr(C)`

Contract:

```text
field order
alignment
padding
size
ABI classification
```

theo target C ABI.

Không chỉ đơn giản là "field order giống source".

---

# 9. `@repr(transparent)`

Ví dụ:

```axiom
@repr(transparent)
struct UserId {
    value: u64
}
```

Cho phép ABI representation tương đương underlying representation trong các context mà contract quy định.

Semantic type vẫn khác:

```text
UserId != u64
```

---

# 10. `@repr(packed)`

Chỉ system/unsafe.

```axiom
@repr(packed)
struct Header {
    version: u8
    size: u32
}
```

Các field có thể unaligned.

Compiler phải ngăn safe code thực hiện access yêu cầu alignment không hợp lệ.

---

# 11. `@repr(align(N))`

Ví dụ:

```axiom
@repr(align(64))
struct CacheLine<T> {
    value: T
}
```

Ý nghĩa:

```text
alignment >= 64
```

Không có nghĩa object chắc chắn nằm ở cache line riêng biệt.

---

# 12. `@export`

```axiom
@export("process")
pub fn process(...)
```

Đây là ABI contract.

Compiler phải:

- tạo symbol
- giữ symbol reachable
- áp dụng ABI
- validate FFI-safe signature.

---

# 13. `@import`

Nếu cần explicit foreign symbol metadata:

```axiom
@import("kernel32")
extern "system" fn ...
```

Nhưng linking dependency nên tách khỏi function declaration.

Có thể:

```text
@link("kernel32")
```

ở module/package level.

---

# 14. `@link`

Ví dụ:

```axiom
@link("m")
extern "C" fn sin(x: f64) -> f64
```

Compiler/build system biết cần:

```text
libm
```

Nhưng `@link` không phải semantic function behavior.

Nó là build/link directive.

---

# 15. Link directive target

Có thể hỗ trợ:

```text
@link(name="foo", kind="static")
@link(name="foo", kind="dynamic")
```

nhưng phần lớn trường hợp compiler có thể để package/build metadata quản lý.

### Quyết định

> `@link` được hỗ trợ ở system/build layer, không phải dependency mechanism chính.

---

# 16. `@cfg`

Đã có:

```axiom
@cfg(target_os == "windows")
```

Nó **select code**, không execute computation.

Khác:

```text
@cfg
```

với:

```text
comptime
```

---

# 17. `@cfg` phải deterministic

Ví dụ:

```axiom
@cfg(target_arch == "x86_64")
```

Compiler biết.

Không cho:

```axiom
@cfg(random())
```

Configuration predicate phải thuộc tập compiler-known/build-declared inputs.

---

# 18. `@derive`

```axiom
@derive(Debug, Clone, Eq)
struct User {
    ...
}
```

Đây không phải macro text.

Compiler tạo typed declarations.

Đúng với:

```text
ACOMP-43
ACOMP-78
```

---

# 19. `@derive` compiler-known

v1 chỉ nên có:

```text
Debug
Clone
Copy
Eq
Ord
Hash
Default
```

nếu semantic requirements đáp ứng.

Không cho arbitrary derive plugin sửa compiler internals.

---

# 20. `@inline`

Hint:

```axiom
@inline
fn add(...) ...
```

Compiler có quyền:

```text
inline
hoặc không inline
```

nhưng phải ưu tiên nếu cost model cho phép.

---

# 21. `@always_inline`

Nếu cần system-level:

```axiom
@always_inline
```

nhưng tôi đề xuất **không freeze trong Core v1**.

Compiler có thể bỏ qua trong một số trường hợp.

---

# 22. `@noinline`

Compiler phải giữ function boundary về code generation.

Nhưng semantic behavior vẫn giống.

Dùng cho:

- profiling
- debugging
- code-size control
- recursion control

---

# 23. `@cold`

```axiom
@cold
fn error_path() -> never
```

Hint branch/function hiếm.

Optimizer có thể:

```text
hot/cold code splitting
```

---

# 24. `@noreturn`

Không cần attribute nếu return type là:

```text
never
```

Do đó:

```axiom
fn abort() -> never
```

tự đủ semantic information.

**Không thêm `@noreturn` như một duplicate semantic mechanism.**

---

# 25. `@pure`

Cần rất cẩn thận.

Một function:

```axiom
@pure
fn foo(...)
```

không được phép có observable effects.

Nhưng Axiom chưa có full effect system.

Do đó tôi đề xuất:

> **Không freeze `@pure` Core v1.**

Compiler có thể nội bộ suy luận purity để optimization.

---

# 26. `@const` / `@comptime`

Không dùng attribute để tạo hệ thống thứ hai.

Đã có:

```axiom
const
comptime fn
comptime {}
```

Do đó không cần:

```text
@const_fn
```

duplicate.

---

# 27. `@kernel`

Đây là semantic attribute:

```axiom
@kernel
fn add(...)
```

Nó chuyển function vào:

```text
ExecutionDomain::GPU
```

và kích hoạt kernel legality verification.

---

# 28. `@kernel` không phải optimization hint

Compiler không được coi:

```axiom
@kernel
```

là:

```text
"hãy thử chạy GPU"
```

Nó là explicit execution-domain contract.

---

# 29. `@tls`

```axiom
@tls
static state: State
```

là storage semantic:

```text
one instance / execution thread
```

Không phải optimization.

---

# 30. `@align`

```axiom
@align(64)
```

là representation/storage contract.

Compiler không được giảm alignment xuống 16 nếu programmer yêu cầu 64.

---

# 31. `@packed`

Không tạo attribute riêng nếu đã có:

```axiom
@repr(packed)
```

Tránh duplicate syntax.

---

# 32. `@interrupt`

System semantic:

```axiom
@interrupt
unsafe fn handler(...)
```

Compiler phải dùng appropriate ABI:

- register preservation
- interrupt return
- stack rules
- target-specific metadata.

---

# 33. `@naked`

```axiom
@naked
unsafe fn entry(...)
```

Contract:

> compiler không tạo ordinary function prologue/epilogue.

Chỉ system layer.

---

# 34. `@syscall`

System ABI:

```axiom
@syscall
unsafe fn syscall(...)
```

Target-specific lowering.

Ví dụ:

```text
Linux syscall
Windows syscall
firmware
kernel
```

Không portable semantic.

---

# 35. Intrinsic là gì?

Intrinsic khác attribute.

Intrinsic là operation mà compiler hiểu trực tiếp.

Ví dụ:

```text
simd_add
atomic_cmpxchg
read_cycle_counter
bit_reverse
leading_zeros
trap
memory_fence
```

---

# 36. Intrinsic không phải library magic

Ví dụ:

```axiom
x.leading_zeros()
```

có thể là library API.

Compiler nhận diện trait/intrinsic lowering.

Programmer không cần gọi:

```text
__builtin_clz()
```

như C compiler-specific extensions.

---

# 37. Intrinsic namespace

Không nên expose hàng trăm tên compiler-specific.

Có thể:

```text
std.intrinsic.*
```

hoặc compiler-known operations trong standard library.

Ví dụ:

```axiom
bit.reverse(x)
```

Compiler nhận diện và lower:

```text
BSWAP / REV / ...
```

nếu target hỗ trợ.

---

# 38. Intrinsic categories

### Arithmetic

```text
add_with_overflow
mul_with_overflow
```

### Bit

```text
leading_zeros
trailing_zeros
popcount
bit_reverse
```

### Atomic

```text
atomic_load
atomic_store
atomic_cas
```

### SIMD

```text
vector_add
shuffle
extract
insert
```

### Memory

```text
prefetch
fence
volatile_load
volatile_store
```

### Machine

```text
trap
cycle_counter
cpuid
```

---

# 39. Intrinsic phải có semantic specification

Không được định nghĩa:

```text
"compiler biết cái này"
```

là đủ.

Ví dụ:

```text
atomic_load
```

phải định nghĩa:

```text
atomicity
ordering
width
alignment
failure behavior
```

Backend chỉ là implementation.

---

# 40. Intrinsic fallback

Nếu intrinsic có portable semantic:

```axiom
bit.reverse(x)
```

target không có instruction:

```text
portable lowering
```

Compiler tạo sequence.

Không nên fail compile chỉ vì CPU không có instruction.

---

# 41. Target-specific intrinsic

Nếu thật sự target-specific:

```axiom
x86.mmx...
arm.neon...
```

nên nằm trong:

```text
target-specific module
```

thay vì pollute Core.

---

# 42. CPU feature detection

Compiler có:

```text
@cfg(cpu_feature("avx2"))
```

hoặc runtime:

```text
cpu.has_feature(...)
```

Hai thứ khác nhau.

### `@cfg`

compile-time selection.

### runtime feature check

runtime dispatch.

---

# 43. Multi-versioning

Sau này:

```text
foo_generic()
foo_avx2()
foo_avx512()
```

và dispatch:

```text
CPU feature
 ↓
function pointer
```

có thể được compiler/library hỗ trợ.

Không cần Core semantic feature.

---

# 44. `@target_feature`

Có thể cần:

```axiom
@target_feature("avx2")
fn process(...)
```

Ý nghĩa:

> Function được phép sử dụng instruction/features của target đó.

Compiler phải đảm bảo caller không gọi nó trên CPU không hỗ trợ nếu ABI/runtime contract không cho phép.

---

# 45. `@target_feature` không phải `@cfg`

Ví dụ:

```text
@cfg(avx2)
```

→ function tồn tại hoặc không.

```text
@target_feature(avx2)
```

→ function tồn tại, nhưng body được phép sử dụng AVX2.

---

# 46. `@no_mangle`

Không cần thiết nếu đã có:

```axiom
@export("foo")
```

Do đó:

> Không thêm `@no_mangle` vào Core.

`@export` đã biểu đạt chính xác ý định native symbol.

---

# 47. `@deprecated`

Tooling attribute:

```axiom
@deprecated("use new_api")
fn old_api(...)
```

Không thay đổi machine semantics.

Compiler warning.

---

# 48. `@must_use`

Tooling/semantic diagnostic:

```axiom
@must_use
fn open() -> Result<File, Error>
```

Compiler cảnh báo nếu kết quả bị bỏ.

Có thể compiler tự áp dụng cho:

```text
Result
Option
```

và một số resource types.

Không nhất thiết user phải annotate mọi nơi.

---

# 49. `@test`

Build/tooling attribute:

```axiom
@test
fn test_math() {
    ...
}
```

Compiler tạo test metadata.

Production build không include test entry point.

---

# 50. `@bench`

Tương tự:

```axiom
@bench
fn benchmark() ...
```

Tooling.

Không phải Core runtime.

---

# 51. `@doc`

Documentation metadata:

```axiom
@doc("...")
```

hoặc comment system.

Không nên đưa documentation vào semantic IR trừ khi tooling cần.

---

# 52. Attribute placement

Compiler phải validate:

```axiom
@kernel
struct X
```

→ error.

Nếu:

```text
@kernel
```

chỉ hợp lệ trên function.

Attribute registry chứa:

```text
allowed_target = Function
```

---

# 53. Attribute arguments

Phải có typed argument grammar.

Ví dụ:

```axiom
@align(64)
```

`64` phải là compile-time integer.

Không:

```axiom
@align(foo())
```

nếu `foo()` runtime.

---

# 54. Duplicate attributes

Ví dụ:

```axiom
@inline
@inline
fn foo()
```

Compiler nên warning/error.

Nhưng:

```axiom
@cfg(...)
@cfg(...)
```

có semantic combinator rules riêng.

---

# 55. Attribute ordering

Không để:

```text
@inline
@cold
```

có semantic khác:

```text
@cold
@inline
```

Attributes được xem như unordered metadata set, trừ attribute nào specification explicitly định nghĩa sequence.

---

# 56. Intrinsic vs unsafe

Không phải intrinsic nào cũng unsafe.

Ví dụ:

```axiom
popcount(x)
```

safe.

Trong khi:

```text
raw_load<T>(address)
```

unsafe.

Safety là property của operation, không phải vì nó là intrinsic.

---

# 57. Intrinsic vs architecture

Ví dụ:

```axiom
atomic.load(...)
```

là semantic operation.

Backend quyết định:

```text
LOCK XADD
LDAR
LWARX/STWCX
```

Programmer không cần biết.

---

# 58. Inline assembly là ngoại lệ

Asm là machine-level interface.

Do đó:

```axiom
unsafe asm { ... }
```

system-level.

Compiler phải parse/validate operand constraints.

---

# 59. Memory effects của asm

ASM contract phải mô tả:

```text
inputs
outputs
clobbers
memory read
memory write
control-flow
volatile
```

Nếu không, optimizer có thể reorder/remove sai.

---

# 60. Compiler directives

Ngoài attributes, compiler cần directives cho build:

```text
@cfg
@link
@target
```

Nhưng nên hạn chế.

Không tạo DSL build thứ hai bên trong source.

---

# 61. Source-level build configuration

Không nên:

```axiom
@download_package(...)
@install(...)
@execute(...)
```

trong source.

Dependency/build actions phải nằm ngoài language semantic.

Điều này giữ compiler deterministic.

---

# 62. Attribute capability

Một số attribute nguy hiểm:

```text
@naked
@interrupt
@packed
@syscall
@target_feature
```

phải yêu cầu:

```text
unsafe/system context
```

hoặc compiler target capability.

Không phải programmer bình thường có thể vô tình dùng.

---

# 63. Attribute audit

Mỗi attribute phải trả lời:

```text
1. Nó có thay đổi semantics không?
2. Có ảnh hưởng ABI không?
3. Compiler bắt buộc phải obey không?
4. Có target-specific không?
5. Có cần unsafe không?
6. Có thể thay bằng type/system semantics không?
7. Có cần tồn tại trong Core không?
```

Nếu không trả lời được → không thêm attribute.

---

# 64. Bộ attribute Core đề xuất

### Semantic

```text
@kernel
@tls
@cfg
```

### Representation / ABI

```text
@repr(...)
@align(...)
@export(...)
```

### System

```text
@naked
@interrupt
@syscall
```

### Optimization hints

```text
@inline
@noinline
@cold
```

### Compiler-generated

```text
@derive(...)
```

### Tooling

```text
@test
@bench
@deprecated
@must_use
```

### Target

```text
@target_feature(...)
```

Đây là bộ tương đối nhỏ nhưng đủ mạnh.

---

# 65. Những attribute **không nên thêm**

Tạm thời loại:

```text
@pure
@const_fn
@noreturn
@no_mangle
@heap
@stack
@gc
@borrow
@lifetime
@effect
@throws
@catch
@exception
```

vì chúng hoặc:

- duplicate semantics đã có,
- leak implementation,
- hoặc làm ngôn ngữ phức tạp.

---

# 66. Compiler intrinsic registry

Compiler nên có internal registry:

```text
Intrinsic {
    name
    type_signature
    safety
    effects
    target_constraints
    lowering
}
```

Ví dụ:

```text
popcount
    safe
    pure-ish
    target-independent semantic
    target-specific lowering

trap
    safe/system depending API
    noreturn
    target-specific lowering
```

---

# 67. Intrinsic lowering pipeline

```text
Source API
    ↓
Resolver
    ↓
Intrinsic identity
    ↓
Typed MIR
    ↓
Semantic optimization
    ↓
Target lowering
    ↓
Instruction
```

Không để parser/backend biết toàn bộ intrinsic.

---

# 68. Attribute lowering pipeline

```text
Source Attribute
       ↓
Attribute Resolver
       ↓
Validated Attribute IR
       ↓
Semantic / ABI / Optimization metadata
       ↓
MIR / ABI MIR / LIR
```

Điều này tránh việc backend phải parse source-level attributes.

---

# 69. AI-friendly metadata

Axiom compiler nên xuất metadata:

```text
attribute:
    name
    target
    kind
    arguments
    semantic_effect
    safety
    ABI_effect
```

AI agent có thể hiểu compiler behavior mà không cần đọc toàn bộ compiler source.

---

# 70. Invariants BOOTSTRAP-036

```text
AATTR-20   Attributes are typed compiler metadata.

AATTR-21   Unknown Core attributes are compile errors.

AATTR-22   Attribute validity depends on declaration target.

AATTR-23   Attribute ordering does not normally change semantics.

AATTR-24   Attributes are classified by semantic strength.

AATTR-25   Optimization hints may be ignored without changing semantics.

AATTR-26   ABI contracts cannot be ignored.

AATTR-27   Semantic attributes participate in semantic identity.

AATTR-28   Representation attributes participate in layout identity.

AATTR-29   Export attributes participate in symbol identity.

AATTR-30   @repr controls representation contracts.

AATTR-31   @repr(C) establishes C-compatible representation.

AATTR-32   @repr(transparent) preserves specified underlying representation.

AATTR-33   @repr(packed) is system/unsafe functionality.

AATTR-34   @repr(align(N)) establishes minimum alignment.

AATTR-35   @export creates an explicit native symbol contract.

AATTR-36   Public visibility does not imply native export.

AATTR-37   @cfg selects declarations; it does not execute runtime code.

AATTR-38   @cfg inputs are deterministic build/compiler inputs.

AATTR-39   @derive produces typed declarations rather than textual macros.

AATTR-40   @inline is an optimization hint.

AATTR-41   @noinline is an optimization constraint.

AATTR-42   @cold is an optimization hint.

AATTR-43   never type replaces a redundant noreturn semantic attribute.

AATTR-44   @kernel establishes a GPU execution-domain contract.

AATTR-45   @tls establishes per-thread storage semantics.

AATTR-46   @interrupt establishes a system interrupt ABI.

AATTR-47   @naked suppresses ordinary function prologue/epilogue generation.

AATTR-48   @syscall establishes a target-specific system ABI.

AATTR-49   System attributes are target-validated.

AATTR-50   Unsafe attributes cannot silently weaken ordinary safety verification.

AATTR-51   Intrinsics are compiler-recognized semantic operations.

AATTR-52   Intrinsic semantics are specified independently from target lowering.

AATTR-53   Target-specific intrinsics do not pollute portable Core semantics.

AATTR-54   Portable intrinsics may have target-specific lowering.

AATTR-55   Intrinsic safety is operation-specific.

AATTR-56   Inline assembly is a system-level interface.

AATTR-57   Inline assembly declares machine-relevant dependencies.

AATTR-58   Optimizer cannot reorder assembly against undeclared dependencies.

AATTR-59   Compiler directives must not become an unrestricted build language.

AATTR-60   Dependency resolution remains outside Core language semantics.

AATTR-61   Attributes cannot introduce implicit runtime dependencies.

AATTR-62   Tooling attributes do not alter production semantics.

AATTR-63   Test and benchmark declarations are removable from production builds.

AATTR-64   Attribute arguments are compile-time validated.

AATTR-65   Attribute semantics are represented explicitly in compiler IR.

AATTR-66   Backends do not parse source-level attributes directly.

AATTR-67   Attribute metadata participates in incremental compilation identity when semantically relevant.

AATTR-68   Optimization-only attributes need not affect semantic ABI identity.

AATTR-69   Compiler may reject contradictory attributes.

AATTR-70   Attribute registry is compiler-visible and machine-readable.

AATTR-71   Intrinsic registry is compiler-visible and machine-readable.

AATTR-72   Axiom avoids duplicate mechanisms for identical semantic questions.

AATTR-73   Attribute count should remain deliberately small.

AATTR-74   System-specific extensions must not redefine portable Core semantics.

AATTR-75   Attributes cannot bypass type, ownership, capability, or ABI verification.
```

---

# Kết luận BOOTSTRAP-036

Điểm tôi muốn **freeze** ở đây là:

> **Attribute là metadata có contract, không phải escape hatch tùy ý.**

Và:

> **Intrinsic là semantic operation được compiler hiểu, không phải compiler magic rải khắp source.**

Kiến trúc lúc này rất sạch:

```text
                   Axiom Source
                        │
              ┌─────────┴─────────┐
              │                   │
          Language             Attributes
          semantics            metadata
              │                   │
              └─────────┬─────────┘
                        ↓
                     Typed HIR
                        ↓
                       MIR
                        ↓
              ┌─────────┼─────────┐
              ↓         ↓         ↓
           Semantic     ABI      Target
           lowering   lowering   lowering
              │         │         │
              └─────────┴─────────┘
                        ↓
                  Machine Code
```

Như vậy compiler có thể ngày càng phức tạp bên trong, nhưng **ngôn ngữ không cần ngày càng phức tạp theo**.

### Tiếp theo: BOOTSTRAP-037

**Comptime + Reflection Audit & Freeze**

Phần này sẽ không thiết kế lại từ đầu vì Axiom đã có ACOMP-20…85. Ta sẽ audit và chốt các điểm còn thiếu:

- cú pháp `const` / `comptime`
- compile-time function
- `Type`
- reflection API
- generated declarations
- compile-time filesystem
- capability sandbox
- cache identity
- generic + comptime interaction
- `@derive`
- `@cfg`
- compile-time errors
- parallel comptime
- tránh biến comptime thành một "ngôn ngữ thứ hai".