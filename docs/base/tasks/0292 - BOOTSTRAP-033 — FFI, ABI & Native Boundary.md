Tiếp tục. Ta vào **BOOTSTRAP-033 — FFI, ABI & Native Boundary**.

Đây là một trong những task quan trọng nhất của Axiom vì mục tiêu của bạn không chỉ là tạo ngôn ngữ mới mà còn phải **tạo native executable/library và sử dụng được thế giới native hiện có**.

---

# BOOTSTRAP-033 — FFI, ABI & Native Boundary

## 1. Tách 3 khái niệm

Axiom phải phân biệt tuyệt đối:

```text
Axiom Semantic Model
        │
        ↓
     Axiom ABI
        │
        ├──────────────┐
        ↓              ↓
   Native ABI       C ABI
```

### Axiom semantics

Quy định:

- ownership
- Drop
- `view`
- `mut_view`
- Send/Share
- type safety
- panic
- Result
- layout semantics

### Axiom ABI

Quy định compiler-to-compiler:

- calling convention
- argument passing
- return
- layout
- symbol
- generic instantiation
- closure representation
- async representation

### Foreign ABI

Ví dụ:

```text
C
C++
Win64
System V AMD64
AAPCS64
Objective-C
Swift ABI
GPU ABI
WASM ABI
```

Không được trộn ba tầng này.

---

# 2. FFI là semantic boundary

Ví dụ:

```axiom
extern "C" fn strlen(s: *const u8) -> usize
```

Axiom biết:

```text
C ABI
raw pointer
usize
```

nhưng không thể biết C function có thực sự đảm bảo:

```text
s != null
s points to NUL-terminated memory
```

Do đó boundary là:

```text
Safe Axiom
    ↓
explicit unsafe/native boundary
    ↓
Foreign code
```

---

# 3. `extern` không tự biến code thành unsafe

Ví dụ khai báo:

```axiom
extern "C" fn malloc(size: usize) -> *mut u8
```

bản thân declaration có thể hợp lệ.

Nhưng sử dụng kết quả:

```axiom
let p = malloc(100)
```

để tạo safe capability phải đi qua abstraction có contract.

Không để:

```text
extern = compiler stops checking
```

---

# 4. Raw pointer là boundary primitive

FFI dùng:

```text
*const T
*mut T
```

như đã chốt.

Nhưng:

```text
raw pointer ≠ ownership
raw pointer ≠ view
raw pointer ≠ valid memory
```

Đây là machine-level representation.

---

# 5. Chuyển pointer thành safe access

Ví dụ conceptual:

```axiom
unsafe {
    let p = foreign_get_buffer()
    let data = view_from_raw(p, len)
}
```

Unsafe operation phải establish:

```text
address valid
alignment valid
length valid
lifetime valid
provenance valid
access mode valid
```

Sau đó compiler có thể theo dõi:

```text
safe capability
```

từ boundary trở đi.

---

# 6. Không có "unsafe block = disable compiler"

Điều này cực kỳ quan trọng.

```axiom
unsafe {
    ...
}
```

không có nghĩa:

```text
ignore ownership
ignore Drop
ignore type system
ignore control flow
```

Nó chỉ cho phép các operation mà safe verifier không thể tự chứng minh.

---

# 7. C ABI

Axiom hỗ trợ:

```axiom
extern "C" fn foo(...)
```

và:

```axiom
@export("foo")
fn foo(...)
```

để tạo symbol native.

---

# 8. C-compatible type

Không phải mọi Axiom type đều tự động C-compatible.

Safe FFI types ban đầu:

```text
bool              nếu ABI contract xác định
i8..i64
u8..u64
isize
usize
f32
f64
raw pointers
@repr(C) structs
@repr(C) enums theo quy tắc
```

---

# 9. `@repr(C)` là FFI contract

Ví dụ:

```axiom
@repr(C)
struct Point {
    x: f32
    y: f32
}
```

Compiler phải đảm bảo layout tương thích C theo target ABI.

Không được reorder field.

Không được tự niche-optimize phá contract.

---

# 10. Default struct vẫn private

```axiom
struct Point {
    x: f32
    y: f32
}
```

không có guarantee:

```text
offset(x)
offset(y)
padding
alignment
ABI
```

trừ khi representation contract yêu cầu.

---

# 11. `@repr(C)` không biến semantics thành C

Ví dụ:

```axiom
@repr(C)
struct Resource {
    handle: u64
}
```

vẫn là Axiom type.

Nó chỉ cam kết representation.

Ownership/Drop vẫn là Axiom semantics.

---

# 12. C enum

C enum thực chất thường là integer representation.

Axiom enum:

```axiom
enum State {
    Ready,
    Running,
    Error
}
```

là algebraic type.

Không tự coi là C enum.

Nếu cần:

```axiom
@repr(C)
enum CState {
    ...
}
```

compiler phải áp dụng representation contract rõ ràng.

---

# 13. Không cho arbitrary enum ABI

Đây là điểm cần tránh.

Ví dụ enum:

```axiom
enum Value {
    Int(i64),
    Float(f64),
    Text(String)
}
```

không thể tự nhiên trở thành:

```text
C struct
```

C ABI-safe representation phải explicit.

---

# 14. String FFI

Axiom:

```text
String
```

không phải:

```text
char*
```

và không null-terminated mặc định.

Do đó:

```axiom
extern "C" fn puts(s: *const u8)
```

không nhận `String` trực tiếp.

---

# 15. C string

Nên có library/system types:

```text
CStr
CString
```

Conceptually:

```text
CStr
= borrowed NUL-terminated byte sequence

CString
= owned NUL-terminated byte sequence
```

Không nhất thiết Core phải có implementation chi tiết.

---

# 16. UTF-8 không tự động áp dụng cho C

FFI:

```text
C string
```

là bytes.

Axiom không được giả định:

```text
C string = UTF-8
```

trừ API contract.

Có thể:

```text
CStr → UTF8 validation → str
```

hoặc:

```text
str → encode → CString
```

nếu explicitly yêu cầu.

---

# 17. Slice FFI

Axiom:

```text
view<[T]>
```

không mặc định là C ABI type.

Khi FFI, programmer dùng explicit ABI structure:

```axiom
@repr(C)
struct SliceU8 {
    ptr: *const u8
    len: usize
}
```

hoặc compiler cung cấp predefined FFI helper.

---

# 18. Vì sao không freeze `view<T>` ABI?

Bởi vì `view<T>` là semantic capability.

Compiler có thể hiện thực bằng:

```text
pointer + length
```

nhưng ABI không nhất thiết phải vĩnh viễn là như vậy.

Giữ:

```text
semantic view
≠
physical representation
```

---

# 19. Axiom ABI có thể dùng optimized aggregate passing

Ví dụ:

```axiom
struct Vec2 {
    x: f32
    y: f32
}
```

Compiler có thể truyền:

```text
XMM register
```

thay vì memory.

ABI lowering quyết định.

---

# 20. Return values

Axiom function:

```axiom
fn make() -> LargeStruct
```

không có nghĩa:

```text
heap allocation
```

Compiler có thể dùng:

```text
register return
sret
caller-allocated return
multiple registers
```

theo target ABI.

Đã phù hợp `AMEM-28/29`.

---

# 21. FFI return ownership

Đây là vấn đề nguy hiểm.

Ví dụ:

```axiom
extern "C" fn create() -> *mut Resource
```

Axiom không được tự suy luận:

```text
Axiom owns Resource
```

Raw pointer chỉ là pointer.

Ownership phải được API wrapper xác định.

---

# 22. Foreign allocator boundary

Không được:

```text
foreign malloc
    ↓
Axiom Box
    ↓
Axiom free
```

nếu hai allocator không tương thích.

Ngược lại cũng vậy.

Đây là invariant đã có:

```text
AMEM-50
AMEM-51
```

---

# 23. Explicit ownership adapters

Ví dụ library:

```text
ForeignBuffer
```

có thể quy định:

```text
free_with_foreign_allocator()
```

hoặc:

```text
take_ownership()
```

hoặc:

```text
borrow()
```

Nhưng phải explicit.

---

# 24. `@export`

Public symbol và exported symbol là hai khái niệm.

```axiom
pub fn internal_api() { ... }
```

không nhất thiết tạo linker symbol public.

Muốn native export:

```axiom
@export("axiom_process")
pub fn process(...) { ... }
```

---

# 25. Symbol naming

Default Axiom ABI có thể name-mangle:

```text
_axiom$module$type$function...
```

C ABI:

```text
process
```

không mangling nếu `extern "C"`/export contract yêu cầu.

---

# 26. Symbol visibility

Compiler cần hỗ trợ:

```text
hidden
local
public
exported
weak
```

nhưng không nhất thiết expose toàn bộ ngay trong Core syntax.

Có thể:

```text
@visibility(hidden)
@export("foo")
```

system/compiler attributes.

---

# 27. Static library

Axiom compiler phải có thể tạo:

```text
libfoo.a
foo.lib
```

tùy target.

Nhưng static library không phải language semantic.

Đó là toolchain artifact.

---

# 28. Dynamic library

Tương tự:

```text
.dll
.so
.dylib
```

Axiom code có thể export/import symbols.

Runtime dynamic loading có thể là library:

```text
DynamicLibrary.open(...)
```

không phải Core primitive.

---

# 29. Calling convention

MVP nên hỗ trợ:

```text
axiom
C
system
```

và target-specific conventions khi cần:

```text
win64
sysv64
aapcs64
```

Syntax có thể:

```axiom
extern "C"
extern "system"
```

Target-specific:

```axiom
@callconv("win64")
```

---

# 30. Không expose machine convention trong ordinary code

Programmer không nên phải biết:

```text
RCX
RDX
R8
R9
XMM0
```

trừ system programming.

Compiler ABI layer chịu trách nhiệm.

---

# 31. Variadic C functions

C:

```c
printf(const char*, ...)
```

có thể gọi qua:

```axiom
extern "C" fn printf(fmt: *const u8, ...) -> i32
```

nhưng:

> Variadic foreign calls chỉ thuộc FFI/system boundary.

Không mở variadic Axiom function trong Core v1.

---

# 32. Type safety của variadic FFI

Compiler không thể kiểm tra hoàn toàn:

```text
printf("%d", f64)
```

Đây là foreign contract.

Do đó API safe wrapper nên dùng:

```text
format
```

thay vì expose raw variadic interface cho application code.

---

# 33. C++ FFI

Không nên cam kết:

```text
extern "C++"
```

ở Core v1 như C ABI.

C++ ABI phụ thuộc:

- compiler
- platform
- standard library
- ABI version.

Axiom có thể gọi C++ thông qua:

```text
extern "C" wrapper
```

đây là con đường ổn định hơn.

Sau này có thể thêm C++ ABI adapters.

---

# 34. Objective-C / Swift / Android

Không nên đưa tất cả vào Core type system.

Thay:

```text
Axiom ABI
    ↓
platform FFI layer
    ↓
Objective-C / Swift / JNI / NDK / etc.
```

Core chỉ cần đủ primitive:

```text
pointer
integer
struct
extern function
calling convention
symbol
```

---

# 35. Syscall

Axiom system layer có thể:

```axiom
@syscall(...)
fn syscall(...)
```

nhưng syscall là target-specific.

Ví dụ Linux và Windows hoàn toàn khác.

Không đưa syscall semantics vào portable Core.

---

# 36. `@naked`

Đã định hướng:

```axiom
@naked
unsafe fn ...
```

cho low-level entry points.

Compiler không tự thêm:

```text
prologue
epilogue
stack setup
```

ngoài contract.

---

# 37. `@interrupt`

System layer:

```axiom
@interrupt
unsafe fn handler(...)
```

ABI target-specific.

Compiler phải biết:

```text
interrupt calling convention
register preservation
return instruction
```

nhưng semantic implementation thuộc backend/platform.

---

# 38. Inline assembly

Axiom cần inline asm cho system-level programming.

Ví dụ conceptual:

```axiom
unsafe asm {
    "rdtsc"
}
```

Nhưng asm phải khai báo:

```text
inputs
outputs
clobbers
memory effects
```

Không nên chỉ là:

```text
asm("...")
```

vì optimizer cần biết dependency.

---

# 39. Inline asm không phá optimizer một cách vô hạn

Ví dụ:

```text
asm
```

có thể có:

```text
pure
readonly
volatile
memory
clobber
```

Nhưng mặc định conservative nếu chưa biết.

---

# 40. `volatile asm`

Nếu instruction observable:

```text
volatile
```

compiler không được loại bỏ chỉ vì kết quả không được dùng.

Tương tự volatile memory đã tách khỏi atomic.

---

# 41. FFI function effects

Không cần xây full effect system cho Core.

Nhưng ABI declaration cần một số machine-relevant properties:

```text
may_unwind
noreturn
pure
readonly
writes_memory
```

Có thể compiler attributes.

---

# 42. Foreign panic/unwind

Không được giả định foreign C function có Axiom panic semantics.

Nếu C function gọi:

```text
longjmp
C++ exception
SEH
```

đó là foreign ABI contract.

Axiom wrapper phải xác định boundary.

---

# 43. Panic qua FFI

MVP nên quy định:

> **Axiom panic không được mặc định xuyên qua `extern "C"` boundary.**

Nếu Axiom function export C ABI:

```text
Axiom panic
 ↓
defined boundary policy
```

thường:

```text
abort
```

hoặc:

```text
error return
```

nếu wrapper thiết kế như vậy.

Không để foreign caller gặp một Axiom exception/unwind object không hiểu.

---

# 44. `Result` qua FFI

Không nên export trực tiếp:

```axiom
fn foo() -> Result<T,E>
```

với C ABI trừ khi có representation contract.

Thay:

```axiom
@repr(C)
struct FooResult {
    status: i32
    ...
}
```

---

# 45. Callback ABI

Axiom function:

```axiom
fn callback(x: i32)
```

không tự động tương thích C callback.

Phải:

```axiom
extern "C" fn callback(x: i32)
```

nếu cần.

Non-capturing closure chỉ decay khi ABI tương thích.

---

# 46. Capturing callback

Foreign API:

```text
register_callback(fn, context)
```

Axiom wrapper có thể tạo:

```text
extern C function pointer
+
opaque context
```

và đảm bảo:

```text
context lifetime ≥ callback registration lifetime
```

Đây là ownership/capability problem, không phải chỉ ABI problem.

---

# 47. FFI thread callback

Nếu foreign library gọi callback trên thread khác:

```text
Foreign Thread
    ↓
Axiom callback
```

wrapper phải establish execution-domain contract.

Compiler không tự coi callback là:

```text
Send
Share
```

chỉ vì ABI là C.

---

# 48. FFI async callback

Tương tự:

```text
foreign completion callback
```

có thể wake Future.

Nhưng foreign library phải giữ buffer/context hợp lệ tới callback.

Axiom wrapper chịu trách nhiệm establish storage contract.

---

# 49. FFI và views

Không cho foreign function tự nhiên nhận:

```text
view<T>
```

trừ khi Axiom ABI có explicit representation contract.

Safe wrapper:

```text
view
 ↓
pointer + length
 ↓
extern C
```

và ngược lại:

```text
pointer + length
 ↓ unsafe validation
view
```

---

# 50. FFI boundary có thể là nơi tạo capability

Ví dụ:

```axiom
unsafe fn foreign_buffer(...) -> view<[u8]>
```

nếu contract đảm bảo:

```text
valid
aligned
length
lifetime
readability
```

thì sau boundary:

```text
safe view
```

được compiler quản lý.

Đây chính là nguyên tắc:

> **Unsafe establishes trusted preconditions; safe verification resumes afterward.**

---

# 51. ABI không được phá ownership

Ví dụ:

```axiom
fn consume(x: String)
```

nếu export C ABI thì không được giả định C biết cách destroy `String`.

Do đó:

```text
Axiom-owned type
```

chỉ đi qua C ABI nếu có explicit ABI contract.

---

# 52. FFI-safe ownership patterns

Ba pattern cơ bản:

```text
Borrow:
    foreign receives pointer/view
    foreign does not own

Transfer:
    foreign receives ownership
    foreign must use matching destructor

Opaque:
    foreign receives opaque handle
    Axiom remains owner
```

---

# 53. Opaque handles

Đây sẽ là pattern rất quan trọng.

Ví dụ:

```axiom
struct DatabaseHandle {
    raw: *mut CDatabase
}
```

Có thể giữ raw pointer private.

Public API:

```axiom
Database.open()
Database.query()
Database.close()
```

Application không cần chạm raw pointer.

---

# 54. `Handle<T>` và FFI

Đã có khái niệm logical identity.

FFI handle có thể là:

```text
opaque native handle
```

nhưng phải phân biệt:

```text
logical Handle<T>
```

với:

```text
raw foreign pointer
```

Không được trộn.

---

# 55. Dynamic symbol lookup

System library:

```axiom
let lib = DynamicLibrary.open("foo")
let symbol = lib.symbol("bar")
```

kết quả ban đầu là raw/opaque native address.

Muốn cast thành function:

```text
unsafe
```

và phải đảm bảo signature/ABI chính xác.

---

# 56. ABI mismatch là undefined foreign behavior

Ví dụ:

```text
C function:
    fn(u64)

Axiom declaration:
    fn(f64)
```

compiler không thể cứu được.

Do đó:

```text
FFI declaration correctness
```

là programmer responsibility.

Nhưng compiler vẫn kiểm tra được:

```text
Axiom side type consistency
ABI-supported types
calling convention
repr contracts
```

---

# 57. FFI metadata

Axiom compiler nên lưu machine-readable:

```text
ABI
calling convention
symbol
parameter types
return type
repr
alignment
ownership contract metadata
```

Điều này cực kỳ hữu ích cho AI agent và tooling.

---

# 58. Native header import

Về sau có thể có:

```text
axiom import c "foo.h"
```

nhưng **không nên là Core compiler requirement v1**.

Có thể xây tool:

```text
axiom-bindgen
```

sau đó sinh Axiom declarations.

---

# 59. Không phụ thuộc C compiler để build Axiom

Đây là mục tiêu của bạn.

Axiom compiler cuối cùng phải có:

```text
own lexer/parser
own semantic compiler
own optimizer
own code generator
own object writer
own linker
```

C compiler chỉ là:

```text
optional interoperability tool
```

không phải bootstrap dependency cuối cùng.

---

# 60. ABI versioning

Axiom ABI nên có:

```text
language version
ABI version
target triple
feature set
```

Ví dụ conceptual:

```text
Axiom ABI:
    target = x86_64-windows
    abi = axiom-v1
```

Không nên tuyên bố binary compatibility vô thời hạn ngay từ v0.1.

---

# 61. Stable C ABI trước

Chiến lược:

```text
Axiom internal ABI
    ↓
experimental

C ABI
    ↓
stable first
```

Sau khi compiler trưởng thành mới đóng băng:

```text
Axiom stable ABI
```

---

# 62. FFI boundary model

Toàn bộ kiến trúc:

```text
             AXIOM CODE
                  │
          safe semantics
                  │
          ┌───────▼───────┐
          │ FFI ADAPTER   │
          │               │
          │ repr / ABI    │
          │ ownership     │
          │ capability    │
          └───────┬───────┘
                  │
             unsafe boundary
                  │
          ┌───────▼───────┐
          │ FOREIGN CODE  │
          │ C / OS / GPU  │
          │ native libs   │
          └───────────────┘
```

Mục tiêu là **unsafe càng mỏng càng tốt**.

---

# 63. Invariants BOOTSTRAP-033

```text
AFFI-20   FFI is an explicit semantic boundary.

AFFI-21   Axiom semantics are distinct from ABI representation.

AFFI-22   Axiom ABI is distinct from foreign ABI.

AFFI-23   Foreign ABI must be explicitly selected.

AFFI-24   C ABI is explicitly requested.

AFFI-25   Foreign declarations do not disable Axiom verification.

AFFI-26   Raw pointers are non-owning by default.

AFFI-27   Raw pointers do not constitute safe capabilities.

AFFI-28   Pointer-to-capability conversion requires an unsafe contract.

AFFI-29   Safe verification resumes after an established FFI contract.

AFFI-30   @repr(C) establishes a C-compatible representation contract.

AFFI-31   Default Axiom layout is not automatically C-compatible.

AFFI-32   Axiom String is not a C string.

AFFI-33   C strings are explicit byte-oriented representations.

AFFI-34   UTF-8 validity is not assumed for foreign byte strings.

AFFI-35   view<T> does not imply a stable foreign ABI representation.

AFFI-36   FFI slices require explicit ABI representation.

AFFI-37   Foreign allocators are not interchangeable with Axiom allocators by default.

AFFI-38   Foreign allocation ownership must be explicit.

AFFI-39   Axiom ownership must not be inferred from raw foreign pointers.

AFFI-40   Foreign functions cannot implicitly transfer ownership.

AFFI-41   Ownership transfer requires an explicit API contract.

AFFI-42   @export creates an explicit native symbol boundary.

AFFI-43   Public visibility does not imply native symbol export.

AFFI-44   Axiom symbol mangling is distinct from C symbol naming.

AFFI-45   Calling convention is part of ABI identity.

AFFI-46   C variadic functions are restricted to FFI/system boundaries.

AFFI-47   Axiom variadic functions are not required by Core v1.

AFFI-48   C++ ABI compatibility is not guaranteed by C ABI compatibility.

AFFI-49   C++ interoperability should initially use explicit C wrappers.

AFFI-50   Foreign exceptions must not implicitly cross Axiom ABI boundaries.

AFFI-51   Axiom panic must not implicitly cross C ABI boundaries.

AFFI-52   FFI callbacks require explicit ABI contracts.

AFFI-53   Capturing closures are not C function pointers.

AFFI-54   Non-capturing closures may decay to compatible function pointers.

AFFI-55   Callback context lifetime must be explicitly established.

AFFI-56   Foreign callbacks do not automatically establish Send.

AFFI-57   Foreign callbacks do not automatically establish Share.

AFFI-58   FFI thread boundaries require explicit execution-domain contracts.

AFFI-59   FFI async completion requires explicit resource lifetime contracts.

AFFI-60   Foreign memory requires explicit ownership and lifetime contracts.

AFFI-61   Dynamic symbol lookup produces an unsafe native boundary.

AFFI-62   Function-pointer casts across ABI boundaries are unsafe.

AFFI-63   ABI mismatch is outside safe-language guarantees.

AFFI-64   ABI metadata is compiler-readable.

AFFI-65   FFI metadata participates in incremental compilation identity.

AFFI-66   Native libraries are optional dependencies of the Axiom compiler itself.

AFFI-67   Axiom does not require a C compiler for ordinary native compilation.

AFFI-68   Object generation is an Axiom compiler responsibility.

AFFI-69   Linking is a toolchain responsibility.

AFFI-70   Axiom may eventually provide its own linker.

AFFI-71   ABI versioning is explicit.

AFFI-72   Stable Axiom ABI requires an explicit stability contract.

AFFI-73   C ABI stability precedes stable Axiom ABI.

AFFI-74   FFI adapters should minimize unsafe surface area.

AFFI-75   Unsafe FFI boundaries cannot bypass structural Axiom verification.
```

---

# 64. Kết quả

Sau task này, Axiom có mô hình rất rõ:

```text
Axiom type
    │
    ├── ordinary
    │      → compiler-controlled representation
    │
    ├── @repr(...)
    │      → explicit representation contract
    │
    └── extern(...)
           → explicit ABI boundary
```

và:

```text
Safe Axiom
     ↓
ownership/capability verification
     ↓
FFI adapter
     ↓
unsafe boundary
     ↓
native world
```

Điều này cho phép Axiom vừa **an toàn và đơn giản ở phía trên**, vừa có thể xuống rất thấp khi cần.

---

## Tiếp theo

**BOOTSTRAP-034 — Modules, Packages, Visibility & Linking**.

Phần này sẽ giải quyết một vấn đề thực tế: một ngôn ngữ native không thể chỉ có `struct`/`fn`; phải định nghĩa thật rõ:

```text
module
import
export
package
namespace
visibility
cyclic dependency
initialization
static data
TLS
library boundary
symbol boundary
incremental compilation
package dependency
```

và đặc biệt phải thiết kế sao cho **Axiom compiler cuối cùng có thể tự build chính nó mà không cần CMake/Cargo/npm hay một build system bên ngoài làm semantic dependency**.