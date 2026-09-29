Tiếp tục.

# BOOTSTRAP-057 — ABI Lowering, Calling Convention & Native Object Boundary

Đây là bước rất quan trọng vì từ đây Axiom bắt đầu chuyển từ **“ngôn ngữ có semantics”** sang **“ngôn ngữ có thể tự tạo binary native”**.

Mục tiêu:

> Một function Axiom sau khi semantic verification và optimization phải có thể được hạ xuống ABI cụ thể mà không cần thay đổi semantics.

---

# 1. Tách 4 khái niệm

Không được trộn:

```text
Type
Representation
ABI
Machine instruction
```

Ví dụ:

```text
struct Point {
    x: f32
    y: f32
}
```

Có thể có:

```text
Semantic Type
    ↓
Representation
    ↓
ABI classification
    ↓
register / stack
    ↓
machine instructions
```

---

# 2. ABI MIR

Pipeline:

```text
Verified MIR
    ↓
Semantic Optimization
    ↓
Representation Analysis
    ↓
Layout
    ↓
ABI Classification
    ↓
ABI MIR
    ↓
Axiom LIR
```

ABI MIR là nơi function call đã có **machine-independent calling convention semantics**.

---

# 3. Ví dụ đơn giản

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Semantic:

```text
add(i32, i32) -> i32
```

ABI lowering có thể thành:

```text
arg0 → integer register
arg1 → integer register
return → integer register
```

Nhưng register cụ thể thuộc target ABI.

---

# 4. Axiom ABI

Axiom cần một ABI nội bộ:

```text
extern "axiom"
```

hoặc mặc định:

```text
Axiom ABI
```

Đặc điểm:

- compiler-controlled
- tối ưu cho Axiom
- không bị ràng buộc bởi C ABI
- có thể thay đổi theo target/compiler version trước khi ABI stability được freeze.

---

# 5. C ABI

Interop:

```axiom
extern "C" fn ...
```

phải tuân theo target C ABI.

Ví dụ:

```text
Windows x64
Linux x64
macOS arm64
```

có ABI rules khác nhau.

Axiom compiler phải có backend ABI implementation riêng.

---

# 6. System ABI

Một số API cần:

```text
extern "system"
```

hoặc target-specific ABI.

Ví dụ Windows API có calling convention/ABI requirements riêng.

---

# 7. ABI không phải representation

Một type:

```text
struct Vec2
```

có layout:

```text
f32
f32
```

nhưng ABI có thể quyết định:

```text
XMM register
```

hoặc stack.

Layout và ABI classification là hai bước khác nhau.

---

# 8. Scalar arguments

Các primitive:

```text
i8
i16
i32
i64
u8
u16
u32
u64
f32
f64
```

được ABI classifier phân loại thành:

```text
Integer
Float
Pointer
Aggregate
```

---

# 9. Pointer ABI

Raw pointer:

```text
*const T
*mut T
```

ở native ABI thường là machine pointer.

Nhưng:

> Pointer representation không làm nó trở thành ownership capability.

ABI chỉ truyền machine value.

---

# 10. `view<T>`

Đây là điểm cần thiết kế kỹ.

Semantic:

```text
view<T>
```

không nhất thiết có một representation cố định.

Compiler có thể lower thành:

```text
(pointer, length)
```

hoặc:

```text
(pointer, length, metadata)
```

tùy type.

---

# 11. Internal view ABI

Trong Axiom ABI:

```text
view<T>
```

có thể được classified thành một **fat value**:

```text
data pointer
length / metadata
```

Nhưng đây là ABI implementation detail.

Source programmer không phải viết struct pointer+length.

---

# 12. FFI view

Không được tự động coi:

```text
view<T>
```

là:

```text
C struct { T* ptr; usize len; }
```

C ABI wrapper phải khai báo representation explicit.

---

# 13. `mut_view<T>`

Tương tự:

```text
mut_view<T>
```

có thể có:

```text
pointer + length
```

nhưng semantic exclusive capability **không được encode bằng pointer representation**.

Sau verification, capability proof có thể erase.

---

# 14. Capability erasure

Ví dụ:

```text
mut_view<f32>
```

sau semantic verification:

```text
Capability:
    exclusive write
    provenance
    lifetime
```

được discharge.

ABI chỉ còn:

```text
pointer
length
```

nếu đó là representation được chọn.

Đây chính là zero-cost abstraction.

---

# 15. Aggregate arguments

Ví dụ:

```text
struct Pair {
    a: i64
    b: i64
}
```

ABI có thể truyền:

```text
register + register
```

hoặc:

```text
stack
```

tùy target.

Không được quy định cứng trong language semantics.

---

# 16. Small aggregate optimization

Axiom ABI nên hỗ trợ:

```text
small struct → registers
```

nếu target ABI cho phép.

Điều này rất quan trọng với triết lý:

> struct thay class.

Struct không nên tự động biến thành heap object.

---

# 17. Large aggregate

Large struct có thể:

```text
caller-allocated
```

và truyền hidden return pointer:

```text
sret
```

nếu ABI yêu cầu.

---

# 18. Return value

Function:

```text
fn make_point() -> Point
```

không có nghĩa:

```text
heap allocate Point
```

Có thể:

```text
register return
```

hoặc:

```text
caller-provided return storage
```

---

# 19. Caller-allocated return

ABI MIR có thể biểu diễn:

```text
ReturnMode =
    Registers
    Stack
    Indirect(destination)
```

Ví dụ:

```text
caller:
    allocate Point storage
    call make_point(destination)
```

---

# 20. RVO/NRVO không cần source rule

Axiom không cần C++-style special return optimization semantics.

Value semantics + Move cho phép compiler tự tối ưu:

```text
local result
   ↓
caller storage
```

Không cần physical copy.

---

# 21. Move + ABI

```axiom
fn make() -> BigStruct
```

semantic:

```text
return ownership
```

ABI:

```text
maybe hidden destination pointer
```

Đây là hai tầng hoàn toàn khác nhau.

---

# 22. `Copy`

Copy semantics không yêu cầu physical copy tại ABI.

Ví dụ:

```text
x: i32
y = x
```

compiler có thể giữ một register/value nếu semantics cho phép.

---

# 23. `Drop`

Function argument có Drop:

```text
fn consume(x: Resource)
```

ABI truyền representation của `Resource`.

Drop semantics được xử lý trong MIR/codegen.

Không có ABI requirement phải có destructor pointer.

---

# 24. Không có implicit vtable cho Drop

Đây là điểm khác C++.

```text
Resource
```

không tự động cần:

```text
object header
vptr
```

Drop glue là compile-time known cho concrete type.

---

# 25. Generic Drop

```text
fn f<T>(x: T)
```

khi `T` concrete:

```text
T = Resource
```

compiler biết Drop implementation.

Specialized code có thể inline Drop.

---

# 26. Generic ABI

Một generic function:

```text
fn f<T>(x: T)
```

không thể export C ABI khi `T` chưa được specialize.

Do đó:

```text
@export
```

yêu cầu ABI-concrete signature.

---

# 27. Dyn Trait

```text
dyn Trait
```

là trường hợp ABI runtime metadata cần thiết.

Ví dụ conceptually:

```text
data pointer
+
vtable pointer
```

Nhưng exact representation thuộc ABI contract.

---

# 28. Vtable

Vtable chỉ tồn tại khi:

```text
dyn Trait
```

hoặc ABI/runtime abstraction yêu cầu.

Không tồn tại cho:

```text
struct
static trait dispatch
generic
```

---

# 29. Trait object ABI

Một trait object ABI cần xác định:

```text
method slots
drop operation
size/alignment metadata
type identity nếu cần
```

Nhưng không nên expose representation này trong ordinary Core source.

---

# 30. Closure ABI

Noncapturing closure:

```text
|x| x + 1
```

có thể lower thành:

```text
function pointer
```

Capturing closure:

```text
|x| x + captured
```

thành concept:

```text
environment pointer
+
function pointer
```

hoặc compiler-specific representation.

---

# 31. Capturing closure ≠ object

Environment là compiler-generated aggregate.

Không cần:

```text
class
virtual method
object header
```

---

# 32. Closure ABI optimization

Nếu inline:

```text
closure environment
```

có thể biến mất.

Do đó closure không mặc định allocation.

---

# 33. Function pointer ABI

Function pointer phải chứa:

```text
code address
```

và có ABI signature cụ thể.

Không được cast tùy tiện giữa các calling conventions.

---

# 34. `extern "C"`

Ví dụ:

```axiom
extern "C" fn add(a: i32, b: i32) -> i32
```

compiler phải:

```text
resolve C ABI
classify args
classify return
emit symbol
```

---

# 35. Export

```axiom
@export("axiom_add")
pub fn add(...)
```

có nghĩa:

```text
native symbol visible externally
```

không có nghĩa:

```text
source visibility
```

`pub` và `@export` vẫn độc lập.

---

# 36. Name mangling

Internal Axiom symbols có thể:

```text
mangle
```

để encode:

```text
package
module
function
generic instance
ABI
```

External exported symbols có explicit names.

---

# 37. Symbol identity

Compiler không được dựa vào source spelling đơn thuần.

Internally:

```text
DeclarationId
GenericInstanceId
```

→ symbol identity.

---

# 38. Weak/linkage semantics

Axiom system/build layer cần hỗ trợ các linkage classes:

```text
Internal
External
Weak
LinkOnce
COMDAT
TLS
Absolute
Section
```

tùy target.

Không phải tất cả đều Core source syntax.

---

# 39. Section placement

System layer có thể cần:

```text
@section(...)
```

nhưng chỉ nên là system/target attribute.

Không đưa linker implementation vào Core semantics.

---

# 40. TLS

Đã có:

```text
@tls
```

ABI lowering phải chuyển thành target TLS model.

Ví dụ:

```text
ELF TLS
PE TLS
Mach-O TLS
```

---

# 41. Alignment

```text
@align(64)
```

là representation contract.

ABI phải đảm bảo:

```text
alignment >= requested
```

nếu target hỗ trợ.

---

# 42. Packed

```text
@repr(packed)
```

có thể tạo unaligned fields.

ABI phải bảo toàn layout contract.

Access vào unaligned field có restrictions.

---

# 43. `repr(C)`

`@repr(C)` phải khóa:

```text
field order
alignment
padding
enum representation rules
```

theo C compatibility contract.

Không chỉ đơn giản là “field order giống C”.

---

# 44. Transparent

```text
@repr(transparent)
struct UserId(u64)
```

semantic type khác:

```text
u64
```

nhưng ABI representation tương thích theo contract.

Điều này rất hữu ích cho FFI/newtype.

---

# 45. Enum ABI

Default:

```text
compiler controlled
```

Compiler có thể:

```text
tag
payload
niche
```

tùy type.

---

# 46. C enum

`@repr(C)` enum phải tuân theo explicit ABI representation.

Không dùng niche optimization nếu phá C ABI contract.

---

# 47. Option ABI

Safe semantic:

```text
Option<T>
```

không quy định representation.

Compiler có thể tối ưu:

```text
null niche
integer niche
pointer niche
```

nếu type representation hợp lệ.

---

# 48. String ABI

Axiom `String` không tự động tương thích:

```text
char*
```

C boundary phải dùng explicit:

```text
CStr
CString
```

hoặc C-compatible representation.

---

# 49. Slice ABI

Axiom:

```text
view<T>
```

không tự động là:

```text
struct Slice {
    T* ptr;
    usize len;
}
```

FFI wrapper phải explicit.

---

# 50. FFI ownership

ABI không thể encode đầy đủ:

```text
OwnedByAxiom
OwnedByForeign
Borrowed
Shared
HandleOnly
```

Do đó ownership contract phải nằm trong FFI declaration/wrapper semantics.

---

# 51. Allocation boundary

Không được:

```text
Axiom alloc
   ↓
C free
```

một cách mặc định.

Allocation domain phải explicit.

---

# 52. ABI allocator functions

System layer có thể cung cấp:

```text
axiom_alloc
axiom_free
```

nhưng đây là explicit API.

Không phải mọi Axiom object đều phải đi qua chúng.

---

# 53. Panic ABI

Axiom panic không được mặc định xuyên qua C ABI.

Ví dụ:

```text
Axiom
  ↓
extern C
  ↓
foreign
```

Panic phải:

```text
catch/translate
```

hoặc terminate theo contract.

---

# 54. Foreign exception

C++ exception không tự động trở thành:

```text
Result<T,E>
```

Axiom wrapper phải explicitly translate.

---

# 55. Async ABI

```text
async fn
```

không được export C trực tiếp như function trả Future nội bộ nếu Future representation chưa có stable ABI.

C wrapper phải expose explicit ABI:

```text
start
poll
callback
handle
```

---

# 56. ABI stability

Axiom **không nên freeze Axiom ABI quá sớm**.

Ưu tiên:

```text
1. Internal Axiom ABI
2. C ABI compatibility
3. Stable system ABI
4. Stable Axiom ABI
```

Axiom ABI có thể thay đổi trong giai đoạn compiler phát triển.

---

# 57. Target ABI database

Compiler nên có:

```text
TargetABI {
    architecture
    os
    calling_convention
    register_classes
    stack_alignment
    aggregate_rules
    return_rules
    varargs_rules
    unwind_rules
    tls_rules
}
```

---

# 58. ABI classification algorithm

Conceptually:

```text
classify(type, context, target_abi)
```

trả:

```text
AbiValue {
    mode
    locations
    coercions
    extensions
    alignment
}
```

---

# 59. Locations

```text
Register
Stack
Indirect
Split
Ignored
```

Ví dụ aggregate:

```text
Split(
    GPR0,
    GPR1
)
```

---

# 60. ABI coercion

Một semantic type có thể cần ABI coercion:

```text
f32
```

→ target ABI register class.

Nhưng coercion không thay đổi source-level type semantics.

---

# 61. Variadic

Core Axiom:

```text
no general variadic
```

FFI/system:

```text
extern "C" fn printf(...)
```

được hỗ trợ theo target ABI.

Compiler phải implement default argument promotions theo C ABI khi cần.

---

# 62. Calling convention

Function type nên semantic distinction:

```text
fn(...)
```

vs ABI-specific function type.

Không được cast tùy tiện:

```text
cdecl
stdcall
fastcall
sysv64
win64
aapcs64
```

nếu calling convention khác.

---

# 63. Function attributes

Một số ABI properties có thể được lưu:

```text
CallingConvention
ReturnConvention
ParameterConvention
UnwindConvention
```

trong AbiSignature.

---

# 64. Unwind

Axiom panic strategy:

```text
abort
```

hoặc:

```text
unwind
```

ABI phải biết function có:

```text
may_unwind
nounwind
```

nhưng đây là compiler-derived/contract fact, không nhất thiết source annotation.

---

# 65. Object file boundary

Sau codegen:

```text
MachineCode
+
Symbols
+
Relocations
+
Sections
+
DebugInfo
```

→ Object.

---

# 66. ObjectWriter

Axiom cuối cùng phải tự có:

```text
PE/COFF writer
ELF writer
Mach-O writer
WASM writer
```

Không bắt buộc LLVM.

---

# 67. Relocations

Machine code có thể chứa:

```text
symbol references
address references
GOT/PLT
TLS references
section-relative references
```

ObjectWriter ghi relocation entries.

---

# 68. Linker

Về lâu dài Axiom cần:

```text
Axiom Linker
```

có khả năng:

```text
object files
static libraries
shared libraries
native executable
```

---

# 69. Không cần viết linker ngay

Bootstrap roadmap:

```text
Axiom compiler
    ↓
external linker
    ↓
native binary
```

sau đó:

```text
Axiom object writer
    ↓
Axiom linker
```

Cuối cùng:

```text
Axiom compiler + linker
```

đều self-hosted.

---

# 70. Static library

Artifact:

```text
libfoo.a
foo.lib
```

là archive các object files.

Axiom build system phải hiểu artifact này.

---

# 71. Shared library

```text
.so
.dll
.dylib
```

yêu cầu:

```text
export table
import table
relocations
platform loader semantics
```

---

# 72. Symbol visibility

Có ít nhất:

```text
internal
hidden
default/external
exported
```

Tùy target.

---

# 73. Dead code elimination

Linker/compiler phải biết:

```text
@export
FFI symbol
entry point
reflection metadata
```

để không xóa nhầm reachable symbol.

---

# 74. Entry point

Hosted:

```text
main
```

System/freestanding:

```text
@entry
```

hoặc target-specific entry mechanism.

Entry point không nhất thiết cần C runtime.

---

# 75. Minimal executable

Axiom phải cho phép:

```axiom
fn main() {
}
```

được link với runtime tối thiểu.

Không tự động kéo:

```text
GC
thread runtime
async runtime
network
Unicode database
reflection
```

nếu không dùng.

---

# 76. Freestanding

Ví dụ:

```text
-freestanding
```

có thể tạo:

```text
Axiom code
+
minimal startup
+
target object
```

không libc.

---

# 77. OS syscall

Ví dụ Linux:

```text
write(...)
```

có thể cuối cùng lower:

```text
syscall
```

mà không cần libc.

System layer chịu trách nhiệm.

---

# 78. Đây là nền tảng cho mục tiêu “không phụ thuộc compiler bên thứ ba”

Cuối cùng:

```text
Axiom source
 ↓
Axiom compiler
 ↓
Axiom LIR
 ↓
Axiom machine encoder
 ↓
Axiom object writer
 ↓
Axiom linker
 ↓
PE / ELF / Mach-O / WASM
```

Không cần:

```text
C compiler
LLVM
Clang
GCC
```

ở production toolchain.

---

# 79. Nhưng bootstrap vẫn có thể dùng backend ngoài

Trong giai đoạn đầu:

```text
Axiom frontend
 ↓
Verified MIR
 ↓
Axiom LIR
 ↓
LLVM/backend
```

là hoàn toàn hợp lý.

Điều cần freeze là:

> **LLVM/backend ngoài là bootstrap implementation dependency, không phải language semantic dependency.**

---

# 80. Frozen invariants — BOOTSTRAP-057

```text
AABI-20   Type semantics are distinct from physical representation.
AABI-21   Physical representation is distinct from ABI classification.
AABI-22   ABI lowering occurs after semantic verification and optimization.
AABI-23   ABI lowering cannot alter source-level ownership semantics.
AABI-24   ABI lowering cannot alter capability semantics.
AABI-25   Axiom ABI is distinct from C ABI and System ABI.
AABI-26   Default internal calls use the Axiom ABI.
AABI-27   Foreign calls require an explicit ABI contract.
AABI-28   Calling conventions are part of ABI function identity.
AABI-29   Function pointers with incompatible calling conventions are not implicitly interchangeable.
AABI-30   Scalar arguments use target-specific ABI classification.
AABI-31   Aggregate arguments use target-specific ABI classification.
AABI-32   Aggregate passing may use registers, stack or indirect storage.
AABI-33   Aggregate return may use registers or caller-provided storage.
AABI-34   Caller-allocated returns do not imply heap allocation.
AABI-35   Move semantics do not require physical copying at ABI boundaries.
AABI-36   Copy semantics do not require physical copying at ABI boundaries.
AABI-37   Drop semantics do not require object headers or virtual destructors.
AABI-38   Concrete Drop glue is compiler-resolved where possible.
AABI-39   Generic functions require concrete specialization for unresolved foreign ABI export.
AABI-40   dyn Trait may require runtime metadata.
AABI-41   Static trait dispatch does not require runtime vtables.
AABI-42   Closure environments are compiler-generated representations.
AABI-43   Capturing closures do not inherently require heap allocation.
AABI-44   Noncapturing closures may lower to function-compatible values.
AABI-45   view<T> representation is compiler-controlled internally.
AABI-46   mut_view<T> representation is compiler-controlled internally.
AABI-47   Capability proof may be erased after semantic verification.
AABI-48   Capability erasure cannot erase required runtime ownership or synchronization semantics.
AABI-49   Axiom view types are not automatically C-compatible slice types.
AABI-50   C-compatible slices require explicit representation contracts.
AABI-51   String is not automatically C string representation.
AABI-52   CStr/CString-style wrappers define explicit foreign string representation.
AABI-53   @repr(C) establishes an explicit C-compatible representation contract.
AABI-54   @repr(transparent) preserves the contracted underlying ABI representation.
AABI-55   @repr(packed) is unsafe/system-level.
AABI-56   Alignment contracts are preserved by ABI lowering.
AABI-57   Default struct layout remains compiler-controlled.
AABI-58   Default enum representation remains compiler-controlled.
AABI-59   Niche optimization cannot violate explicit representation contracts.
AABI-60   FFI ownership domains must be explicit.
AABI-61   FFI allocation domains must not be guessed.
AABI-62   Axiom panic does not implicitly cross foreign ABI boundaries.
AABI-63   Foreign exceptions do not implicitly become Axiom Result values.
AABI-64   Async functions do not implicitly expose unstable Future ABI through foreign interfaces.
AABI-65   Async FFI requires an explicit stable interaction contract.
AABI-66   Exported symbols are distinct from source visibility.
AABI-67   @export establishes an external symbol contract.
AABI-68   Internal symbol names may be mangled.
AABI-69   External exported symbol names may be explicitly specified.
AABI-70   TLS representation is target-ABI dependent.
AABI-71   Variadic functions are restricted to supported FFI/system ABIs.
AABI-72   ABI lowering preserves parameter and return type semantics.
AABI-73   ABI coercions do not change source-level type identity.
AABI-74   Unwind behavior is part of the applicable ABI contract.
AABI-75   Object files contain machine code plus required symbol and relocation information.
AABI-76   Object writers are target-specific backend components.
AABI-77   PE/COFF, ELF, Mach-O and WASM have distinct object/target implementations.
AABI-78   Linkage semantics are distinct from source visibility.
AABI-79   Dead-code elimination must preserve exported and externally reachable symbols.
AABI-80   Freestanding programs do not require a C runtime.
AABI-81   Native executable generation does not semantically depend on a C compiler.
AABI-82   LLVM or another external backend may be used for bootstrap implementation only.
AABI-83   Production Axiom toolchains are intended to provide their own native lowering path.
AABI-84   Axiom object generation must not require LLVM semantics.
AABI-85   Axiom linker is a long-term self-hosting toolchain component.
AABI-86   Static libraries are first-class Axiom artifacts.
AABI-87   Shared libraries are first-class Axiom artifacts.
AABI-88   Native startup code is target-specific and independently linkable.
AABI-89   Runtime components are linked only when required.
AABI-90   ABI stability is distinct from compiler internal ABI evolution.
AABI-91   Stable C ABI is prioritized before stable Axiom ABI.
AABI-92   ABI classification is deterministic for a given target and contract.
AABI-93   ABI decisions are represented explicitly in AbiSignature/ABI MIR.
AABI-94   Machine lowering cannot reinterpret ABI semantics.
AABI-95   Object/link transformations must preserve established ABI contracts.
```

---

## Hiện trạng sau BOOTSTRAP-057

Axiom bây giờ đã có một chuỗi khá hoàn chỉnh:

```text
SOURCE
  ↓
AST
  ↓
HIR
  ↓
Typed HIR
  ↓
MIR
  ↓
Semantic Verification
  │
  ├─ Ownership
  ├─ Capability
  ├─ Lifetime
  ├─ Drop
  ├─ Send/Share
  ├─ Async
  ├─ GPU
  └─ FFI
  ↓
VERIFIED MIR
  ↓
OptIR
  │
  ├─ SSA
  ├─ MemorySSA
  ├─ Alias
  ├─ Escape
  ├─ Range
  ├─ Loop
  └─ Vectorization
  ↓
ABI MIR
  │
  ├─ Calling convention
  ├─ Argument classification
  ├─ Return classification
  ├─ Layout
  └─ FFI
  ↓
Axiom LIR
  ↓
Machine IR
  ↓
Object
  ↓
Link
  ↓
EXE / ELF / Mach-O / WASM
```

Và một điểm rất quan trọng đã được khóa:

> **`view`, `mut_view`, ownership, Drop, trait, closure, generic... có thể là những abstraction rất mạnh ở source level nhưng không nhất thiết tồn tại trong binary.**

Đó chính là nền tảng để Axiom vừa **dễ viết như ngôn ngữ cấp cao**, vừa hướng tới **chi phí runtime gần với code viết tay cấp thấp**.

### Bước kế tiếp: BOOTSTRAP-058

**Machine IR + register allocation + instruction selection + instruction scheduling + stack frame + calling convention implementation + target backend architecture.**

Đây là lúc thiết kế **“Axiom tự sinh machine code”** ở mức thực sự thấp: x86-64, ARM64, RISC-V trước; sau đó mở rộng WASM/GPU.