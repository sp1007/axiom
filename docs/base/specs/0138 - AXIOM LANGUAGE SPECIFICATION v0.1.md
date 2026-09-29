# AXIOM LANGUAGE SPECIFICATION v0.1
# Part XIX — FFI · ABI · C Interop · Foreign Ownership

Phần này khóa nguyên tắc:

> **ABI là biên giới của machine contract, không phải biên giới của type system.**

Axiom phải gọi được C/OS/native library, đồng thời cho phép C gọi ngược vào Axiom, nhưng không được để ABI làm rò rỉ những semantic machinery như ownership, generic, trait solver hay compiler lifetime.

---

# 1. Bốn tầng phải luôn tách biệt

Axiom dùng:

```text
TYPE SEMANTICS
      ↓
DATA REPRESENTATION
      ↓
ABI REPRESENTATION
      ↓
MACHINE REPRESENTATION
```

Ví dụ:

```axiom
struct Vec2 {
    x: f32
    y: f32
}
```

Không có nghĩa ABI mặc định là:

```text
float x;
float y;
```

Chỉ khi:

```axiom
@repr(C)
struct Vec2 {
    x: f32
    y: f32
}
```

thì Axiom cam kết C-compatible representation.

---

# 2. Native ABI

Axiom có ABI mặc định:

```text
"axiom"
```

ABI này tối ưu cho compiler.

Nó có thể thay đổi theo:

- compiler version
- target
- optimization
- generic instantiation
- representation strategy

Không dùng native Axiom ABI làm stable external ABI mặc định.

---

# 3. Stable ABI

Nếu muốn ABI ổn định:

```axiom
extern "C" fn ...
```

hoặc một ABI versioned rõ ràng.

Ví dụ:

```axiom
extern "C" fn axiom_add(a: i32, b: i32) -> i32 {
    a + b
}
```

---

# 4. `extern`

`extern` xác định calling convention/ABI boundary.

Ví dụ:

```axiom
extern "C" fn malloc(size: usize) -> *mut u8
```

không nói rằng:

```text
malloc
```

là Axiom function.

Nó là foreign ABI contract.

---

# 5. `extern fn` không tự động unsafe

Có thể có:

```axiom
extern "C" fn strlen(...)
```

và wrapper:

```axiom
fn length(text: Text) -> usize {
    ...
}
```

Nếu wrapper đảm bảo contract thì public API vẫn safe.

Foreign declaration chỉ mô tả ABI.

---

# 6. Foreign function có thể yêu cầu unsafe

Nếu C API yêu cầu:

```text
non-null pointer
valid buffer
initialized memory
thread affinity
global initialization
```

thì declaration/wrapper phải encode boundary.

Ví dụ:

```axiom
unsafe extern "C" fn foo(p: *mut CThing)
```

---

# 7. C ABI không hiểu ownership

C chỉ thấy:

```text
pointer
size
value
```

C không biết:

```text
Move
Drop
Send
Share
view
mut_view
```

Do đó Axiom không được giả định C function tự hiểu ownership.

---

# 8. Ownership phải được encode ở wrapper

Ví dụ:

```text
C:
    create() -> CThing*
    destroy(CThing*)
```

Axiom:

```axiom
struct Thing {
    raw: *mut CThing
}
```

và:

```axiom
impl Drop for Thing {
    fn drop(self) {
        unsafe {
            c_destroy(self.raw)
        }
    }
}
```

Public API:

```text
Thing
```

có deterministic ownership.

---

# 9. Foreign ownership domain

Mỗi allocation thuộc một domain.

Ví dụ:

```text
Axiom allocator
C malloc
Windows HeapAlloc
COM allocator
GPU allocator
OS virtual memory
custom pool
```

Không được:

```text
C malloc
    ↓
Axiom free
```

trừ khi allocator contract xác nhận tương thích.

---

# 10. `@repr(C)`

`@repr(C)` yêu cầu representation tương thích với C ABI.

Ví dụ:

```axiom
@repr(C)
struct Point {
    x: f64
    y: f64
}
```

Compiler không được reorder fields để tối ưu layout.

---

# 11. `@repr(C)` không biến mọi type thành C-compatible

Ví dụ:

```axiom
@repr(C)
struct Foo<T> {
    value: T
}
```

không mặc định có nghĩa:

```text
Foo<T> is C ABI safe
```

Chỉ hợp lệ khi representation của `T` đã được xác định là C-compatible.

---

# 12. Generic ABI

Không cho:

```axiom
extern "C" fn foo<T>(x: T)
```

một cách tùy tiện.

Generic cần được:

```text
monomorphize
```

và export một concrete ABI hoặc bị reject.

Ví dụ:

```text
foo<i32>
foo<f64>
```

là hai machine-level instantiations khác nhau.

---

# 13. Không leak compiler type machinery

Không export trực tiếp:

```text
trait
impl
associated type
generic unresolved type
closure
opaque internal type
```

qua stable C ABI.

ABI chỉ nhận representation đã được xác định.

---

# 14. C primitive mapping

Axiom cần một lớp C ABI types:

```text
c_char
c_short
c_int
c_long
c_long_long

c_uint
c_ulong
...

c_size
c_ptrdiff
```

Không dùng:

```text
u64 == C long
```

một cách cố định.

Vì C ABI phụ thuộc target.

---

# 15. `usize` không phải `size_t` về mặt type identity

Trong Axiom:

```text
usize
```

là target pointer-width integer.

Trong C:

```text
size_t
```

là ABI-defined type.

Có thể tương thích representation trên target nhưng semantic identity vẫn khác.

---

# 16. C integer width

Ví dụ Linux x86-64:

```text
long = 64-bit
```

nhưng Windows x64:

```text
long = 32-bit
```

Axiom không được hardcode assumption.

C ABI layer chịu trách nhiệm.

---

# 17. C struct layout

```axiom
@repr(C)
struct CPoint {
    x: f32
    y: f32
}
```

Compiler phải tính:

```text
offset
alignment
size
padding
```

theo target C ABI.

---

# 18. Struct field order

Axiom native:

```text
compiler may reorder
```

C repr:

```text
declared order is ABI order
```

Đây là semantic boundary.

---

# 19. Padding

Padding bytes của `@repr(C)` struct:

```text
may exist
```

và không nhất thiết có giá trị semantic.

Không được tự động coi toàn bộ struct memory là meaningful bytes.

---

# 20. `repr(C)` + zero initialization

Không được suy luận:

```text
zero bytes == valid T
```

cho mọi C-compatible type.

Ví dụ pointer/enum/float/struct semantics có thể khiến assumption không đúng.

---

# 21. C enum

Axiom enum:

```axiom
enum Color {
    Red,
    Green,
    Blue,
}
```

là algebraic data type.

Không mặc định tương đương:

```c
enum Color { Red, Green, Blue };
```

---

# 22. C-compatible enum

Nếu cần:

```axiom
@repr(C)
enum Color {
    Red,
    Green,
    Blue,
}
```

representation phải được xác định theo ABI contract.

Nhưng C enum semantics và Axiom exhaustive enum semantics vẫn khác.

---

# 23. C enum unknown values

C code có thể truyền:

```text
999
```

vào field được khai báo enum-like.

Axiom safe enum không được tự động chấp nhận arbitrary discriminant.

Wrapper phải validate:

```text
raw integer
   ↓
Option<Color>
```

hoặc explicit unsafe conversion.

---

# 24. `union`

C union cần:

```axiom
@repr(C)
union Value {
    i: i32
    f: f32
}
```

nhưng union access là low-level operation.

Axiom không thể biết active member chỉ từ bytes.

Do đó union field access cần unsafe hoặc abstraction chứng minh active variant.

---

# 25. Union không phải enum

Union:

```text
same storage
multiple interpretations
```

Enum:

```text
tag + active payload
```

Không trộn hai semantic models.

---

# 26. Function pointer

C function pointer:

```text
typedef int (*Fn)(int);
```

Axiom cần representation tương ứng:

```text
fn(i32) -> i32
```

hoặc ABI-qualified:

```text
extern "C" fn(i32) -> i32
```

---

# 27. Axiom function vs C function

```text
fn(i32) -> i32
```

là Axiom calling convention.

```text
extern "C" fn(i32) -> i32
```

là C ABI function pointer.

Hai loại không mặc định interchangeable.

---

# 28. Callback

C callback:

```text
register_callback(fn)
```

Axiom:

```axiom
extern "C" fn callback(value: i32) {
    ...
}
```

Compiler phải generate đúng calling convention.

---

# 29. Closure không tự động là C callback

Không được:

```axiom
let closure = |x| x + captured
c_register(closure)
```

vì closure có environment.

C function pointer thường chỉ có:

```text
code pointer
```

Axiom closure conceptually:

```text
environment + code
```

---

# 30. Callback + userdata

Wrapper chuẩn:

```text
C API
    callback(void* userdata)
```

Axiom:

```text
userdata
   ↓
opaque context
   ↓
closure/environment
```

Ownership của context phải explicit.

---

# 31. Closure callback lifetime

Nếu C giữ callback:

```text
register_callback(cb)
```

thì Axiom không được cho phép closure environment chết trong khi C vẫn giữ pointer.

Phải có abstraction như:

```text
CallbackHandle
```

hoặc explicit lifetime/registration ownership.

---

# 32. Foreign callbacks và thread

C library có thể callback từ:

```text
same thread
worker thread
OS callback thread
interrupt-like context
```

Axiom wrapper phải biết contract.

Không tự giả định callback chạy trên caller thread.

---

# 33. Callback Send/Share

Nếu foreign library có thể callback đồng thời:

```text
CallbackContext
```

phải có synchronization contract.

Axiom không tự thêm mutex.

---

# 34. Variadic C functions

C:

```c
printf(...)
```

là ABI đặc biệt.

Axiom không nên hỗ trợ arbitrary variadic calls trong safe core.

Có thể:

```axiom
extern "C" fn printf(fmt: *const u8, ...) -> c_int
```

nhưng call boundary phải là unsafe/system-level.

---

# 35. Variadic type safety

Compiler không thể kiểm tra:

```text
"%d"
```

với:

```text
f64
```

ở arbitrary C varargs.

Do đó wrapper typed:

```text
Text.format(...)
```

nên được ưu tiên.

---

# 36. C strings

Axiom:

```text
Text
```

không mặc định là:

```text
char*
```

C string:

```text
char*
    NUL terminated
```

Axiom Text:

```text
Unicode text abstraction
```

khác semantics.

---

# 37. `CString`

Library nên có:

```text
CString
```

với invariant:

```text
no embedded NUL
NUL termination
```

để FFI.

---

# 38. C string input

Nếu C nhận:

```text
const char*
```

wrapper có thể:

```text
CStrView
```

không ownership.

Conceptually:

```text
view<u8>
```

nhưng có additional invariant:

```text
NUL terminated
```

---

# 39. C string output

Nếu C trả:

```text
char*
```

Axiom không được tự copy hoặc own.

Wrapper phải xác định:

```text
borrowed
owned
static
caller-freed
library-freed
```

---

# 40. Bytes vs Text

FFI layer nên ưu tiên:

```text
Bytes
view<u8>
mut_view<u8>
```

thay vì tự động convert mọi `char*` thành Text.

---

# 41. Error ABI

C thường dùng:

```text
int
NULL
errno
HRESULT
status code
```

Axiom public API nên convert thành:

```text
Result<T, E>
```

ở wrapper boundary.

Ví dụ:

```text
C:
    0 = success
    nonzero = error

Axiom:
    Result<T, Error>
```

---

# 42. `errno`

`errno` là thread-local state trên nhiều C environments.

Axiom wrapper phải coi nó là:

```text
thread-local foreign state
```

không phải global ordinary variable.

---

# 43. HRESULT/status codes

Không biến arbitrary integer thành panic.

Ví dụ:

```text
C status
 ↓
Result<(), Error>
```

là model chuẩn.

---

# 44. Panic không được vượt C ABI

Axiom:

```axiom
extern "C" fn callback(...) {
    ...
}
```

nếu bên trong panic:

```text
panic
 ↓
C boundary
```

không được mặc định unwind qua C.

---

# 45. FFI panic policy

Mặc định:

```text
panic
 ↓
catch at Axiom boundary
 ↓
abort / error translation
```

tùy explicit API.

Không cho:

```text
Axiom panic
    ↓
C stack
    ↓
undefined unwinding
```

---

# 46. C exception không phải Axiom panic

C++ exception cũng không được tự động map thành:

```text
panic
```

C++ ABI không thuộc Core v0.1.

Nếu cần:

```text
C++ wrapper
 ↓
extern "C"
 ↓
Axiom
```

---

# 47. Axiom exception model

Axiom không có general exceptions.

Do đó C++ wrapper nên convert:

```text
throw
 ↓
catch in C++ wrapper
 ↓
status/result
 ↓
Axiom
```

---

# 48. Axiom function exported to C

```axiom
@export("axiom_add")
extern "C" fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Hai concept phải tách:

```text
pub
```

và:

```text
@export
```

`pub` là language/package visibility.

`@export` là linker symbol visibility.

---

# 49. Symbol name

Native Axiom function:

```text
add
```

có thể bị mangling.

C export:

```text
axiom_add
```

cần exact symbol contract.

---

# 50. Name mangling

Axiom native ABI được phép:

```text
mangle package
module
type
generic
ABI version
```

C ABI:

```text
exact exported name
```

theo `@export`.

---

# 51. Symbol collision

Hai functions:

```text
@export("foo")
fn a()

@export("foo")
fn b()
```

→ compile/link error.

Compiler không âm thầm rename.

---

# 52. Visibility vs linker export

Có thể:

```text
pub fn internal_api()
```

nhưng không export linker symbol.

Ngược lại:

```text
@export(...)
```

phải có ABI-compatible signature.

---

# 53. Dynamic library

Axiom có thể tạo:

```text
.dll
.so
.dylib
```

nhưng export surface phải explicit.

Không export toàn bộ `pub` symbols mặc định.

---

# 54. Static library

Axiom có thể tạo:

```text
.a
.lib
```

và C linker có thể link.

Object format/ABI do target backend quản lý.

---

# 55. Generic exported function

Không cho:

```axiom
@export("foo")
fn foo<T>(x: T)
```

trực tiếp.

Phải export concrete function:

```axiom
@export("foo_i32")
fn foo_i32(x: i32)

@export("foo_f64")
fn foo_f64(x: f64)
```

---

# 56. Trait export

Không export:

```text
dyn Trait
```

qua C ABI mặc định.

Nếu cần C API:

```text
opaque handle
function table
explicit callbacks
```

---

# 57. `dyn Trait` ABI

Native Axiom:

```text
dyn Trait
```

conceptually:

```text
data_ptr
dispatch_ptr
```

nhưng layout không phải C ABI.

Do đó không leak qua `extern "C"`.

---

# 58. C-compatible dynamic interface

Có thể tạo:

```text
struct Api {
    void* context;
    int (*foo)(void*, ...);
    void (*destroy)(void*);
};
```

Axiom có thể biểu diễn bằng:

```text
@repr(C)
struct Api {
    context: *mut u8
    foo: extern "C" fn(...)
    destroy: extern "C" fn(...)
}
```

Đây là explicit ABI vtable.

---

# 59. This is preferable to leaking `dyn Trait`

Axiom trait:

```text
Trait
```

là semantic abstraction.

C ABI:

```text
function table
```

là machine contract.

Adapter layer nối hai bên.

---

# 60. Opaque types

C ABI rất phù hợp với:

```text
typedef struct AxiomObject AxiomObject;
```

Axiom:

```text
struct Object {
    ...
}
```

export:

```text
*mut Object
```

nhưng C chỉ biết opaque handle.

---

# 61. Opaque handle + ownership

C API:

```text
axiom_create() -> Object*
axiom_destroy(Object*)
```

Axiom wrapper:

```text
Box/ObjectHandle
```

có Drop gọi `axiom_destroy`.

---

# 62. Handle không nhất thiết là pointer

ABI có thể dùng:

```text
u64
```

hoặc:

```text
struct Handle {
    index: u32
    generation: u32
}
```

để tránh exposing address identity.

---

# 63. FFI views

Axiom:

```text
view<T>
```

qua C ABI thường trở thành:

```text
pointer + length
```

nhưng đây là ABI representation.

C không tự hiểu lifetime.

Wrapper phải đảm bảo:

```text
owner alive
region valid
length valid
```

---

# 64. Mutable view qua C

```text
mut_view<T>
```

có thể trở thành:

```text
T* + length
```

nhưng exclusive access guarantee phải được đảm bảo ở Axiom boundary.

Nếu C code giữ pointer lâu hơn call:

```text
```

Axiom không thể coi đó là ephemeral view.

Do đó FFI borrowing APIs phải explicit.

---

# 65. C callback giữ view

Nếu:

```text
callback(view)
```

và C lưu pointer:

```text
callback stores pointer
```

thì contract bị phá.

Wrapper cần copy hoặc explicit ownership transfer.

---

# 66. ABI boundary đóng băng representation

Trước:

```text
struct
```

compiler có freedom.

Sau:

```text
@repr(C)
```

representation bị ràng buộc.

Đây là:

> **Representation Freedom Ends At ABI Boundary.**

---

# 67. ABI và optimization

Compiler vẫn có thể:

```text
inline
constant-fold
vectorize
dead-code eliminate
```

nhưng không được thay đổi observable ABI representation.

---

# 68. ABI and LTO

Nếu toàn bộ chương trình Axiom:

```text
Axiom → Axiom
```

compiler có thể tối ưu xuyên function.

Nếu function exported C:

```text
C ABI boundary
```

phải được giữ nguyên.

---

# 69. FFI is not a compiler escape from semantics

Compiler vẫn phải biết:

```text
function may mutate memory
may panic?
may callback?
may block?
may spawn thread?
may access global state?
```

Nếu ABI declaration không biết, mặc định phải conservative.

---

# 70. Foreign function effects

Đây là điểm nên đưa vào compiler effect model tương lai:

```text
CALL
  reads memory
  writes memory
  may panic
  may block
  may callback
  may spawn
```

Không nhất thiết expose tất cả ở source v0.1, nhưng MIR/ABI metadata nên hỗ trợ.

---

# 71. Pure foreign functions

Một foreign function có thể được đánh dấu:

```text
@pure
```

chỉ khi contract đảm bảo.

Compiler mới được phép:

```text
CSE
common subexpression elimination
dead call elimination
```

Nếu không, foreign call mặc định có side effects.

---

# 72. `@noalias`

Chưa đưa `@noalias` thành source primitive Core v0.1.

Nhưng FFI/system ABI có thể cần metadata tương đương.

Ví dụ C:

```text
restrict
```

có thể được mô tả ở ABI layer.

Compiler dùng nó cho optimization nếu contract rõ.

---

# 73. C `restrict` không phải `mut_view`

Đây là distinction:

```text
mut_view
    language capability

restrict
    foreign optimizer contract
```

Có thể có quan hệ nhưng không đồng nhất.

---

# 74. Thread safety của foreign functions

Không mặc định:

```text
extern fn foo()
```

là thread-safe.

Nếu C library documentation nói:

```text
foo is thread-safe
```

wrapper có thể expose safe API.

---

# 75. Reentrancy

Foreign callback có thể reenter Axiom:

```text
Axiom
  ↓
C
  ↓
Axiom callback
```

Compiler/runtime phải hỗ trợ nếu ABI contract cho phép.

Nhưng callback phải có ownership/context hợp lệ.

---

# 76. Foreign thread enters Axiom

OS/C library có thể gọi Axiom callback từ foreign thread.

Axiom runtime **không được bắt buộc một global runtime** chỉ để callback tồn tại.

Thay vào đó ABI boundary có thể có:

```text
thread registration
TLS initialization
panic boundary
allocator boundary
```

chỉ khi cần.

---

# 77. Runtime registration

Nếu Axiom feature yêu cầu runtime state:

```text
AxiomThread.attach()
```

có thể là explicit library operation.

Không được hidden global constructor.

---

# 78. `main`

Hosted executable:

```axiom
fn main() -> Result<(), Error> {
    ...
}
```

Compiler tạo startup wrapper.

Startup có thể:

```text
initialize required runtime components
call main
translate Result
exit
```

Nhưng chỉ link những thành phần cần thiết.

---

# 79. Freestanding FFI

Freestanding:

```text
@entry fn start(...)
```

có thể không có:

```text
allocator
thread runtime
panic runtime
stdio
```

Axiom compiler vẫn tạo native machine code.

---

# 80. C header generation

Axiom nên có tool:

```text
axiom c-header
```

tạo:

```text
axiom_api.h
```

từ explicit C ABI declarations.

Không parse source Axiom bằng regex.

Compiler AST/ABI model phải là source of truth.

---

# 81. Header generation phải deterministic

Cùng:

```text
source
compiler
target
ABI configuration
```

→ cùng header semantic output.

---

# 82. Header không expose internal types

Chỉ export:

```text
@export
extern "C"
@repr(C)
```

API.

Không leak:

```text
internal
private
generic internal
trait implementation
```

---

# 83. ABI compatibility checking

Tool:

```text
axiom abi-check
```

có thể so sánh:

```text
old ABI
new ABI
```

và phát hiện:

```text
field offset changed
size changed
alignment changed
calling convention changed
symbol removed
parameter changed
return representation changed
```

---

# 84. Semantic API vs ABI API

Axiom cần hai fingerprints:

```text
Semantic API fingerprint
ABI fingerprint
```

Semantic:

```text
types
traits
impls
generic constraints
```

ABI:

```text
symbols
layout
calling convention
representation
```

Hai cái không đồng nhất.

---

# 85. ABI versioning

Native library có thể expose:

```text
AXIOM_ABI_1
AXIOM_ABI_2
```

hoặc symbol versioning tùy platform.

Không ép compiler giữ native ABI mãi mãi.

---

# 86. Dynamic linking

Dynamic library API nên có explicit:

```text
ABI version
feature version
struct size/version
```

để hỗ trợ forward/backward compatibility.

Ví dụ C-style:

```text
struct Api {
    usize size;
    usize version;
    ...
};
```

---

# 87. Struct extension

Nếu ABI struct có trailing fields:

```text
size/version
```

caller có thể kiểm tra.

Đây là library/API design, không phải Core language magic.

---

# 88. Calling conventions

Axiom ABI layer nên hỗ trợ:

```text
"C"
"system"
"stdcall"      // target-specific
"fastcall"     // target-specific
"vectorcall"   // target-specific
```

nhưng chỉ những convention target hỗ trợ mới hợp lệ.

---

# 89. System ABI

Windows API:

```text
extern "system"
```

có thể map tới target convention phù hợp.

Linux/POSIX thường dùng C ABI.

---

# 90. No C++ ABI in v0.1

Không cố implement:

```text
C++ name mangling
C++ object layout
vtable ABI
exceptions
RTTI
```

trong Core.

Nếu cần C++:

```text
C++ adapter
    ↓
C ABI
    ↓
Axiom
```

Đơn giản hơn và portable hơn.

---

# 91. Objective-C / Swift / COM

Không thuộc Core v0.1.

Có thể xây adapter layer:

```text
Axiom
 ↓
C ABI
 ↓
Objective-C / Swift / COM
```

và target-specific bindings.

---

# 92. OS APIs

Mục tiêu cuối:

```text
Axiom
   ↓
native ABI
   ↓
OS API
```

Ví dụ:

```text
Windows
Linux
macOS
Android
iOS
```

không cần C compiler để build Axiom.

Axiom compiler chỉ cần biết:

```text
ABI
object format
linking
system library symbols
```

---

# 93. Không cần C compiler

Đây là điểm quan trọng với mục tiêu ban đầu của bạn.

Final Axiom toolchain:

```text
Axiom source
    ↓
Axiom compiler
    ↓
Machine code
    ↓
Axiom object writer
    ↓
Axiom linker
    ↓
native executable
```

C compiler không nằm trong dependency bắt buộc.

---

# 94. Nhưng vẫn link được C library

Ví dụ:

```text
Axiom
 ↓
libc.so
```

hoặc:

```text
Axiom
 ↓
system DLL
```

Linking một foreign binary library không đồng nghĩa phụ thuộc vào C compiler.

---

# 95. Axiom own linker

Roadmap đã freeze:

```text
ELF64 x86-64
 ↓
PE/COFF
 ↓
Mach-O
 ↓
WASM
 ↓
ARM/RISC-V
```

Linker hiểu:

```text
symbols
sections
relocations
imports
exports
TLS
weak symbols
COMDAT/ICF
```

nhưng không hiểu ownership.

---

# 96. Object writer

Compiler backend tạo:

```text
Axiom LIR
 ↓
machine code
 ↓
relocation records
 ↓
object file
```

Object writer target-specific.

---

# 97. FFI contract summary

Một FFI function cần xác định:

```text
ABI
calling convention
parameter representation
return representation
ownership
alignment
nullability
lifetime
thread safety
panic behavior
error semantics
allocator domain
callback behavior
```

Không nhất thiết programmer phải viết tất cả bằng annotation.

Nhiều thứ đến từ type/ABI/wrapper design.

---

# 98. Ví dụ hoàn chỉnh

```axiom
@repr(C)
struct CPoint {
    x: f64
    y: f64
}

extern "C" fn c_distance(a: *const CPoint,
                         b: *const CPoint) -> f64

@export("axiom_distance")
extern "C"
fn distance(a: CPoint, b: CPoint) -> f64 {
    unsafe {
        c_distance(&a, &b)
    }
}
```

ABI boundary:

```text
CPoint
 ├── C layout
 ├── C calling convention
 └── f64 return
```

Axiom implementation vẫn có:

```text
ownership
Drop
type checking
unsafe boundary
```

---

# 99. FFI architecture

Mô hình cuối:

```text
                 AXIOM SEMANTICS
                       │
                ┌──────┴──────┐
                │             │
           Native ABI       C ABI
                │             │
                │       ┌─────┴─────┐
                │       │           │
              Axiom    C          OS API
                │       │           │
                └───────┴───────────┘
                        │
                  Machine ABI
                        │
              ELF / PE / Mach-O
```

---

# 100. Invariants chính thức

### AFFI-20 — ABI Is A Machine Contract

### AFFI-21 — Type Semantics Are Distinct From ABI Representation

### AFFI-22 — Native Axiom ABI Is Not Automatically Stable

### AFFI-23 — Stable External ABI Must Be Explicit

### AFFI-24 — `extern` Selects An Explicit ABI Contract

### AFFI-25 — C ABI Does Not Encode Axiom Ownership

### AFFI-26 — Foreign Ownership Must Be Explicitly Wrapped

### AFFI-27 — Foreign Allocation Domains Must Not Be Mixed

### AFFI-28 — `@repr(C)` Freezes C-Compatible Representation

### AFFI-29 — `@repr(C)` Does Not Make Arbitrary Generic Types C-Compatible

### AFFI-30 — Generic Types Must Not Leak Unresolved Representation Across Stable ABI

### AFFI-31 — Axiom Enums Are Not C Enums By Default

### AFFI-32 — C Union Access Requires Explicit Low-Level Semantics

### AFFI-33 — Axiom Function ABI Is Distinct From C Function ABI

### AFFI-34 — Closures Are Not Implicit C Function Pointers

### AFFI-35 — Callback Environment Lifetime Must Be Explicit

### AFFI-36 — Foreign Callbacks May Cross Thread Boundaries Only Under Explicit Contract

### AFFI-37 — C Variadic Calls Are Explicit Low-Level Operations

### AFFI-38 — Text Is Not Implicitly A C String

### AFFI-39 — C String Termination Is An Explicit Invariant

### AFFI-40 — Foreign Error Codes Are Converted Explicitly

### AFFI-41 — Panic Must Not Cross C ABI By Default

### AFFI-42 — C++ Exceptions Do Not Automatically Become Axiom Panics

### AFFI-43 — Linker Export Is Distinct From Language Visibility

### AFFI-44 — Exported Symbols Have Explicit ABI Names

### AFFI-45 — Generic Functions Are Not Direct Stable C ABI Exports

### AFFI-46 — Traits Are Not Direct C ABI Representations

### AFFI-47 — `dyn Trait` Is Not Implicitly C-Compatible

### AFFI-48 — Opaque Handles Are Valid FFI Abstractions

### AFFI-49 — FFI Views Do Not Transfer Ownership

### AFFI-50 — FFI Mutable Views Require Explicit Exclusive-Access Contracts

### AFFI-51 — ABI Boundaries Constrain Representation Optimization

### AFFI-52 — ABI Boundaries Do Not Disable Internal Optimization

### AFFI-53 — Foreign Calls Are Conservative Side-Effect Boundaries Unless Contracted Otherwise

### AFFI-54 — Foreign Thread Entry Requires Explicit Runtime/ABI Contract

### AFFI-55 — Axiom Does Not Require A C Compiler For Native Compilation

### AFFI-56 — C Libraries May Be Linked Without A C Compiler

### AFFI-57 — ABI Compatibility Is Independently Checkable

### AFFI-58 — Semantic API Compatibility Is Distinct From ABI Compatibility

### AFFI-59 — ABI Versioning Must Be Explicit

### AFFI-60 — Calling Convention Must Match Target ABI

### AFFI-61 — Native Linker Understands Machine Contracts, Not Axiom Ownership

### AFFI-62 — Foreign Functions Must Not Be Granted Stronger Semantics Than Their Contract

---

# Trạng thái sau Part XIX

Axiom hiện đã khóa được chuỗi:

```text
SAFE
 ↓
ownership / capability
 ↓
concurrency
 ↓
unsafe
 ↓
raw machine access
 ↓
FFI
 ↓
ABI
 ↓
native machine code
```

Đây là một architecture khá sạch:

> **Safe Axiom → explicit unsafe → explicit ABI → native machine contract.**

Không có bước nào cần "tắt toàn bộ compiler".

---

# Part XX — GPU · Accelerator · Device Memory · Kernel

Tiếp theo là một phần đặc biệt quan trọng vì Axiom mục tiêu không chỉ thay C/C++ cho CPU mà còn muốn có nền tảng tốt cho:

```text
CPU
GPU
NPU
DSP
CUDA-like devices
Metal
Vulkan
DirectX
OpenCL
custom accelerator
```

Phần XX sẽ khóa:

```text
@kernel
ExecutionDomain
Host / Device
DeviceBuffer
DeviceView
address spaces
host ↔ device ownership
GPU async/event
GPU atomics
workgroup/local memory
kernel legality
barriers
device synchronization
GPU pointer/provenance
kernel launch ABI
device ABI
GPU panic/error semantics
```

và quan trọng nhất:

> **Một semantic model của Axiom, nhiều execution domains — không tạo ra một “ngôn ngữ GPU thứ hai”.**