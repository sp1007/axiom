# BOOTSTRAP-186 — FFI, C ABI, Foreign Types & Safe Interoperability Boundary
**FROZEN / COMPLETED**

Đây là một trong những phần quan trọng nhất nếu Axiom thực sự muốn trở thành **systems language**. Mục tiêu không phải chỉ “gọi được C”, mà là:

> **Axiom phải có thể tương tác với thế giới native hiện tại mà không làm ô nhiễm mô hình ownership/capability/type safety của Axiom.**

Nguyên tắc trung tâm:

```text
Axiom Semantic World
        │
        │ explicit FFI boundary
        ▼
Foreign ABI World
        │
        ▼
C / OS / GPU / native libraries
```

FFI là **biên semantic**, không phải một kiểu “tắt type system”.

---

# 186.1. FFI không phải Core type system

Axiom Core không biến:

```text
C struct
C pointer
void*
FILE*
HANDLE
```

thành những type native đặc biệt.

Chúng được biểu diễn bằng **foreign declarations + ABI contracts**.

---

# 186.2. `extern`

Conceptual syntax:

```ax
extern "C" fn printf(format: *const u8, ...) -> i32;
```

Nhưng declaration này thuộc **foreign boundary**, không phải ordinary safe function.

---

# 186.3. ABI identifier

Axiom nên hỗ trợ ABI có tên:

```text
"C"
"system"
"stdcall"
"fastcall"
"vectorcall"
"wasm"
"axiom"
```

Platform chỉ cung cấp ABI thực tế phù hợp.

Không hard-code calling convention vào type system.

---

# 186.4. ABI là semantic contract

ABI descriptor phải xác định ít nhất:

```text
calling convention
parameter passing
return convention
stack/register convention
alignment
aggregate passing
enum representation
variadic rules
unwind convention
symbol naming
```

---

# 186.5. `extern fn` type

Function type nên có ABI information:

```text
fn(...) -> T
```

khác với:

```text
extern("C") fn(...) -> T
```

Hai function pointer type này không tự động tương thích.

---

# 186.6. Foreign declaration

Ví dụ:

```ax
extern "C" {
    fn malloc(size: usize) -> *mut u8;
    fn free(ptr: *mut u8);
}
```

Compiler biết:

```text
foreign
ABI = C
unsafe boundary
```

---

# 186.7. FFI function safety

Mặc định foreign function là:

```text
unsafe
```

nếu compiler không có contract chứng minh safe.

Ví dụ:

```ax
unsafe {
    malloc(...)
}
```

---

# 186.8. Safe wrapper

Library Axiom có thể bọc:

```ax
pub fn allocate(size: usize) -> Result<Buffer, AllocError>
```

bên trong:

```text
safe API
    ↓
verified wrapper
    ↓
unsafe FFI
```

Programmer phía trên không cần chạm raw pointer.

---

# 186.9. FFI không làm mất verifier

Đây là invariant rất quan trọng.

Sau:

```ax
unsafe { foreign_call(...) }
```

compiler **không reset ownership/capability state về unknown toàn bộ function**.

Chỉ các contract được khai báo mới được trust.

---

# 186.10. Foreign effect

Foreign call mặc định có:

```text
Effect::Foreign
```

và thường có thể thêm:

```text
Read
Write
Allocate
Deallocate
IO
Synchronize
Panic
```

nếu contract biết.

---

# 186.11. Conservative foreign call

Nếu compiler không biết:

```text
foo(p)
```

có sửa memory hay không, nó phải assume conservative:

```text
may read
may write
may escape
may synchronize
may throw/trap according to ABI
```

Không được tự đoán `const` semantics từ type.

---

# 186.12. Foreign contract

Có thể khai báo:

```text
@ffi(
    reads = [arg0],
    writes = [arg1],
    may_allocate = false,
    may_block = false,
)
```

Nhưng đây là **compiler/system metadata**, không phải bắt programmer ghi mọi FFI manually.

---

# 186.13. Comptime FFI import

Axiom nên hỗ trợ compiler-generated bindings:

```text
C header
   ↓
comptime/header parser
   ↓
foreign declarations
   ↓
Axiom wrapper
```

---

# 186.14. Bindings generator

Tooling:

```text
axc bindgen library.h
```

có thể generate:

```text
library.axffi
```

và metadata.

---

# 186.15. Không cần C compiler để dùng binding

Điều này rất phù hợp mục tiêu Axiom:

```text
C header
    ↓
Axiom FFI declaration
    ↓
Axiom compiler
    ↓
native call
```

Axiom không cần compile C source nếu library C đã tồn tại dạng binary.

---

# 186.16. Nhưng C source thì sao?

Nếu chỉ có:

```text
foo.c
foo.h
```

Axiom **không nên giả vờ rằng nó có thể compile C source**.

Có hai lựa chọn:

```text
C compiler bootstrap/toolchain
```

hoặc:

```text
Axiom C frontend
```

ở một giai đoạn tương lai.

FFI itself chỉ cần ABI/binary interoperability.

---

# 186.17. Static library

Axiom có thể link:

```text
libfoo.a
foo.lib
```

với foreign declarations.

---

# 186.18. Dynamic library

Có thể:

```text
foo.dll
libfoo.so
libfoo.dylib
```

thông qua dynamic loading model của BOOTSTRAP-185.

---

# 186.19. Link contract

Foreign library declaration cần biết:

```text
library name
target
link mode
ABI
required symbols
```

---

# 186.20. Symbol visibility

Không phải declaration nào cũng export.

Axiom phân biệt:

```text
pub
@export
extern
link_symbol
```

---

# 186.21. `@export`

Ví dụ:

```ax
@export("axiom_create")
pub fn create() -> ...
```

`pub` = source visibility.

`@export` = binary symbol visibility.

---

# 186.22. Symbol name

Axiom không nên mặc định dùng source name làm native symbol name trong mọi ABI.

Có thể:

```ax
@export("foo_v2")
fn foo(...)
```

---

# 186.23. Name mangling

Default Axiom ABI có thể mangled.

C ABI:

```text
extern "C"
```

sử dụng C-compatible symbol naming rules theo target.

---

# 186.24. FFI-safe type

Compiler cần trait/semantic property:

```text
FfiSafe
```

để xác định type nào có thể đi qua FFI.

---

# 186.25. Primitive FFI

Các loại cơ bản có mapping rõ:

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

Nhưng `usize`/`isize` mapping phụ thuộc target pointer width.

---

# 186.26. C integer types

Axiom library/system layer cung cấp:

```text
c_char
c_short
c_int
c_long
c_long_long
c_uint
...
```

vì C integer ABI phụ thuộc platform.

---

# 186.27. C bool

Không assume:

```text
bool == C bool
```

Axiom có explicit C ABI mapping.

---

# 186.28. C enum

C enum không mặc định là Axiom algebraic enum.

Cần:

```text
extern enum
```

hoặc generated declaration với ABI contract.

---

# 186.29. Axiom enum → C

Chỉ FFI-safe nếu representation explicit:

```ax
@repr(C)
enum Status {
    ...
}
```

---

# 186.30. Struct ABI

C struct:

```c
struct Point {
    int x;
    int y;
};
```

Axiom:

```ax
@repr(C)
struct Point {
    x: c_int,
    y: c_int,
}
```

---

# 186.31. Struct padding

Compiler phải dùng target C ABI rules.

Không tự áp dụng Axiom optimized layout.

---

# 186.32. Packed C structs

```text
@repr(packed)
```

là unsafe/system nếu access có thể tạo unaligned reference/capability.

---

# 186.33. Transparent wrapper

Axiom newtype:

```ax
@repr(transparent)
struct FileDescriptor(c_int);
```

có thể map ABI với underlying type.

---

# 186.34. Opaque C struct

Đây là pattern cực kỳ quan trọng:

```c
typedef struct Foo Foo;
```

Axiom:

```ax
extern opaque Foo;
```

Axiom không biết layout.

---

# 186.35. Opaque pointer

```text
Foo*
```

không đồng nghĩa ownership.

Foreign pointer chỉ là pointer capability theo FFI contract.

---

# 186.36. `void*`

Không nên biến `void*` thành:

```text
Any
```

mà biểu diễn như raw opaque pointer:

```text
*mut void
```

và conversion phải explicit/unsafe.

---

# 186.37. Null

Foreign APIs thường dùng:

```text
NULL
```

Trong safe Axiom:

```text
Option<NonNull<T>>
```

hoặc abstraction tương ứng.

Raw null pointer chỉ ở unsafe/FFI boundary.

---

# 186.38. Pointer ownership

Compiler không tự assume:

```text
T*
```

là owner.

Contract phải chỉ rõ:

```text
borrowed
owned
callee-owned
caller-owned
shared
nullable
```

---

# 186.39. Ownership annotations

FFI metadata có thể khai báo:

```text
arg0: borrowed
return: owned
```

để wrapper generator tự tạo ownership-safe abstraction.

---

# 186.40. `owned` foreign return

Ví dụ:

```text
foo_create() -> *mut Foo
```

nếu contract:

```text
return = owned
destroy = foo_destroy
```

wrapper có thể tạo:

```text
OwnedFoo
```

với Drop:

```text
foo_destroy(ptr)
```

---

# 186.41. Borrowed foreign pointer

```text
foo_get_name(foo) -> *const char
```

nếu lifetime phụ thuộc `foo`, wrapper phải preserve dependency.

Conceptually:

```text
Foo
 └── Str/view
```

không được để view sống sau Foo.

---

# 186.42. Foreign lifetime

Axiom không yêu cầu programmer viết:

```text
'a
```

cho FFI.

Compiler/wrapper generator xây dependency graph từ contract.

---

# 186.43. Mutable foreign pointer

Nếu:

```text
fn foo(*mut Buffer)
```

và contract says exclusive:

```text
WRITE
```

wrapper có thể nhận:

```text
mut_view<Buffer>
```

nếu representation/ABI cho phép.

---

# 186.44. C arrays

```c
void foo(int *p, size_t n);
```

không tự động biến thành:

```text
view<i32>
```

vì ABI thực tế là pointer + length.

Wrapper có thể expose:

```ax
fn foo(mut_view<i32>)
```

và lower thành:

```text
pointer + length
```

---

# 186.45. Slice ABI

`view<T>` không có một universal C ABI.

Compiler wrapper phải lower explicit theo contract:

```text
ptr + len
```

hoặc:

```text
ptr only
```

---

# 186.46. String FFI

Axiom `String` không mặc định tương thích:

```text
char*
```

vì:

```text
ownership
encoding
termination
mutability
```

khác nhau.

---

# 186.47. C string

Library có:

```text
CStr
CString
```

conceptually:

```text
CStr = borrowed NUL-terminated bytes
CString = owned NUL-terminated bytes
```

---

# 186.48. UTF-8 contract

C string không mặc định là UTF-8.

Conversion:

```text
CStr → Str
```

phải validate UTF-8.

---

# 186.49. String ownership

Nếu C API giữ pointer sau call:

```text
foo_set_name(ptr)
```

compiler không thể cho temporary string escape unless contract explicitly says it copies or borrows.

---

# 186.50. Callback

C:

```c
void register_callback(void (*cb)(void*), void* ctx);
```

Axiom cần phân biệt:

```text
function pointer
closure
capturing closure
```

---

# 186.51. Noncapturing callback

Noncapturing Axiom function:

```ax
fn callback(...)
```

có thể lower thành C function pointer.

---

# 186.52. Capturing closure

Capturing closure:

```ax
let state = ...;
let cb = || use(state);
```

không tự động trở thành:

```text
C function pointer
```

vì cần environment.

---

# 186.53. Closure trampoline

Library/runtime có thể tạo:

```text
C callback
   ↓
trampoline
   ↓
closure environment
```

nhưng environment lifetime phải được quản lý explicit.

---

# 186.54. Callback ownership

Nếu C library giữ callback:

```text
callback lifetime = registration lifetime
```

Axiom wrapper phải encode dependency.

---

# 186.55. Unregister

API:

```text
register()
unregister()
```

nên tạo capability:

```text
CallbackRegistration
```

Drop có thể unregister nếu operation không fallible hoặc wrapper policy phù hợp.

---

# 186.56. Thread callback

Nếu C library callback từ arbitrary thread:

```text
Callback
```

phải satisfy `Send`/`Share` requirements theo wrapper contract.

---

# 186.57. Async callback

Không biến callback thành `async fn` tự động.

Wrapper có thể:

```text
callback
→
event/channel
→
async task
```

---

# 186.58. Variadic functions

Axiom hỗ trợ C variadic ở FFI boundary:

```ax
extern "C" fn printf(fmt: *const c_char, ...) -> c_int;
```

Nhưng variadic calls cần restricted types theo C ABI.

---

# 186.59. Type checking variadic arguments

Không thể đảm bảo toàn bộ format semantics từ ABI.

Library nên có typed wrapper:

```text
format(...)
```

hoặc comptime format checking.

---

# 186.60. `setjmp` / `longjmp`

Đây là FFI hazard.

Axiom không cho phép `longjmp` xuyên qua live Axiom ownership frames trong safe code.

---

# 186.61. Foreign exceptions

C++ exception không được xuyên qua Axiom frame mặc định.

Boundary:

```text
C++ exception
    X
Axiom stack
```

Wrapper phải catch ở foreign side.

---

# 186.62. Unwind ABI

FFI contract phải chỉ rõ:

```text
NoUnwind
MayUnwind
AbortOnUnwind
```

---

# 186.63. Axiom panic → C

Default:

```text
Axiom panic
```

không tự unwind xuyên C ABI.

Export wrapper nên catch/convert hoặc abort theo declared contract.

---

# 186.64. C callback → Axiom panic

Không được mặc định unwind qua C.

Wrapper phải:

```text
catch panic
→
error/state/report
```

hoặc terminate theo contract.

---

# 186.65. Error code

C:

```text
int result
errno
GetLastError
```

không tự động trở thành `Result`.

Library wrapper map:

```text
C error
→
Axiom Error
```

---

# 186.66. `errno`

`errno` là thread-local external state.

Compiler effect model phải coi access là external effect.

---

# 186.67. Windows errors

`GetLastError()` có platform-specific semantics.

Axiom OS layer giữ nguyên native error code và cung cấp typed wrapper.

---

# 186.68. POSIX errors

Tương tự:

```text
errno
EAGAIN
EINTR
ENOENT
...
```

được map ở `std::os::unix`.

---

# 186.69. Allocator boundary

Đây là điểm cực kỳ quan trọng:

```text
Axiom allocator
≠
C malloc
≠
OS allocator
```

Không được:

```text
malloc()
↓
Axiom free()
```

trừ khi ABI contract đảm bảo.

---

# 186.70. Foreign-owned memory

Nếu C cấp:

```text
malloc
```

thì ownership abstraction phải sử dụng:

```text
free
```

cùng allocator domain.

---

# 186.71. Axiom-owned memory

Nếu Axiom cấp buffer cho C:

```text
Axiom Buffer
→
C
```

C chỉ được release nếu explicit contract cho phép.

---

# 186.72. Custom allocator

FFI contract có thể chỉ rõ:

```text
allocate
deallocate
reallocate
alignment
```

để tạo compatible ownership type.

---

# 186.73. FFI transfer

Cross-boundary ownership:

```text
Axiom owner
      ↓
FFI
```

là một semantic Move nếu contract chuyển ownership.

---

# 186.74. FFI borrow

Nếu C chỉ đọc:

```text
Axiom owner
      ↓
READ capability
      ↓
FFI
```

compiler có thể preserve alias assumptions.

---

# 186.75. FFI mutation

Nếu C sửa:

```text
mut_view
```

phải có exclusive access contract.

---

# 186.76. Unknown foreign aliasing

Nếu C API có:

```text
register_global(ptr)
```

và giữ pointer:

```text
Escape = ExternalEscape
```

Compiler phải biết owner không được relocate/destroy prematurely.

---

# 186.77. Foreign escape

Đây là lý do FFI effect model rất quan trọng.

```text
Axiom value
 ↓
foreign call
 ↓
ForeignEscape
```

có thể cấm stack promotion/relocation.

---

# 186.78. Foreign retained pointer

Nếu foreign library giữ pointer:

```text
storage must remain valid
```

cho đến unregister/destroy.

---

# 186.79. Stable address

Nếu C yêu cầu stable pointer:

```text
Box / pinned storage contract / external allocation
```

phải được dùng.

`Vec` relocation không được phép nếu pointer đang active.

---

# 186.80. `Pin` vẫn không thành Core primitive

Như đã frozen:

> Stable address là **storage contract**, không phải universal language primitive.

---

# 186.81. Memory-mapped structures

FFI/system layer có thể map:

```text
volatile memory
device memory
shared memory
```

nhưng không biến thành ordinary safe `T` nếu machine semantics khác.

---

# 186.82. Volatile FFI

Memory-mapped registers:

```text
volatile_read
volatile_write
```

là system/unsafe operations.

---

# 186.83. Atomic FFI

Foreign atomic object phải có explicit ABI and memory-order contract.

Không assume Axiom `Atomic<T>` layout tương thích C atomic.

---

# 186.84. Thread synchronization

Foreign library có thể cung cấp lock:

```text
pthread_mutex_t
CRITICAL_SECTION
```

Wrapper phải encode ownership/guard semantics.

---

# 186.85. Foreign mutex guard

Axiom wrapper có thể tạo:

```text
MutexGuard
```

với:

```text
Drop → unlock
```

nhưng native lock semantics nằm trong wrapper contract.

---

# 186.86. OS handles

Từ BOOTSTRAP-184:

```text
HANDLE
fd
socket
pid
```

là distinct resource types.

FFI chỉ là boundary để acquire/use chúng.

---

# 186.87. File descriptors

```text
c_int
```

không tự động là:

```text
File
```

Wrapper chuyển machine value thành owned resource sau khi xác lập ownership contract.

---

# 186.88. Dynamic symbols

Dynamic lookup:

```text
raw symbol
```

không tự động typed.

Cần:

```text
symbol ABI descriptor
```

sau đó mới thành callable capability.

---

# 186.89. Function pointer lifetime

Nếu symbol nằm trong dynamic library:

```text
Library
 └── FunctionSymbol
```

FunctionSymbol không được sống sau Library unload.

Đã liên kết trực tiếp với `ADYN-...` của BOOTSTRAP-185.

---

# 186.90. GPU FFI

GPU APIs:

```text
CUDA
Vulkan
Metal
DirectX
OpenCL
```

không được nhét vào Core.

Chúng là foreign/system libraries.

---

# 186.91. GPU handle

Ví dụ:

```text
VkBuffer
MTLBuffer*
CUdeviceptr
```

có wrapper riêng.

Không coi tất cả là `DeviceBuffer`.

---

# 186.92. Foreign GPU memory

Chỉ sau khi contract xác lập:

```text
ownership
storage domain
alignment
layout
lifetime
synchronization
```

mới chuyển thành Axiom GPU capability.

---

# 186.93. WASM FFI

WASM ABI là một FFI profile riêng:

```text
integer
float
pointer/index
multi-value
reference types
```

không mặc định giống C ABI.

---

# 186.94. Component model

Nếu Axiom hỗ trợ WASM Component Model sau này:

```text
WIT/interface
      ↓
Axiom binding generation
```

là một FFI adapter.

---

# 186.95. FFI metadata

Foreign declaration có metadata:

```text
FFIContract {
    ABI
    ownership
    nullability
    mutability
    lifetime dependency
    effects
    unwind
    thread behavior
    alignment
    representation
}
```

---

# 186.96. Contract generation

`bindgen` có thể generate phần lớn metadata từ:

```text
header
DWARF
Clang AST
IDL
WIT
SDK metadata
```

tùy ecosystem.

---

# 186.97. Header parsing

Axiom compiler không nhất thiết phải có C preprocessor đầy đủ trong Core.

`bindgen` có thể là external tooling trong bootstrap phase.

Về lâu dài Axiom có thể có:

```text
comptime C header parser
```

nếu đáng giá.

---

# 186.98. No third-party dependency at runtime

FFI không làm Axiom runtime phụ thuộc vào Clang/GCC/MSVC.

Sau khi binding được tạo:

```text
Axiom compiler
   ↓
native object
   ↓
native linker
```

---

# 186.99. Bootstrap toolchain

Trong giai đoạn bootstrap:

```text
Axiom compiler
   ↓
LLVM/LLD hoặc system linker
```

có thể được sử dụng.

Đây không phải semantic dependency của Axiom cuối cùng.

---

# 186.100. Final self-hosted FFI

Compiler Axiom cuối cùng cần tự hiểu:

```text
C ABI
platform ABI
object formats
linking
symbol resolution
```

ở mức cần thiết để build native binaries.

---

# 186.101. C++ interoperability

Axiom không cố “import C++ language” vào Core.

Thay vào đó:

```text
C++ wrapper
    ↓
extern "C"
    ↓
Axiom
```

là boundary khuyến nghị.

---

# 186.102. Why not direct C++ ABI?

C++ ABI phụ thuộc mạnh vào:

```text
compiler
standard library
ABI version
name mangling
templates
exceptions
RTTI
object layout
```

Do đó không nên trở thành Axiom Core ABI.

---

# 186.103. C++ generated bridge

Tooling có thể generate:

```text
C++ library
    ↓
small C ABI shim
    ↓
Axiom
```

---

# 186.104. Objective-C / Swift

Tương tự:

```text
Axiom
 ↓
platform ABI / C ABI / generated bridge
 ↓
Objective-C / Swift
```

được xử lý ở platform layer.

---

# 186.105. COM

Windows COM có thể được wrapper thành:

```text
interface
vtable
IUnknown ownership
HRESULT
```

nhưng không làm COM vtable trở thành Axiom trait object.

---

# 186.106. Axiom trait ↔ C vtable

Có thể generate adapter:

```text
Axiom Trait
      ↕
C vtable
```

nhưng phải explicit.

---

# 186.107. Ownership of vtable

Vtable capability phải sống đủ lâu với implementation/library mà nó trỏ tới.

---

# 186.108. ABI-safe trait object

Nếu muốn plugin ABI:

```text
extern "AxiomPlugin"
dyn Trait
```

phải có stable ABI descriptor.

Không sử dụng internal compiler vtable layout.

---

# 186.109. FFI generic prohibition

Không truyền generic Axiom type trực tiếp qua C ABI:

```text
extern "C" fn foo<T>(...)
```

trừ khi compiler monomorphizes thành concrete exported instance.

---

# 186.110. Generic export

Có thể:

```text
T
 ↓
specialize<T=i32>
 ↓
export concrete ABI function
```

---

# 186.111. FFI closures

Closure qua FFI chỉ khi compiler tạo explicit representation:

```text
function pointer
+
environment pointer
+
destroy function
```

---

# 186.112. Callback ABI descriptor

Một callback contract phải xác định:

```text
calling convention
thread context
ownership of context
lifetime
reentrancy
unregister
panic behavior
```

---

# 186.113. Reentrancy

Foreign callback có thể gọi ngược vào Axiom.

Compiler/runtime không assume:

```text
foreign_call
```

là non-reentrant.

---

# 186.114. Reentrant ownership

Nếu callback re-enter function đang giữ mutable capability, safe wrapper phải ngăn conflict.

Đây là nơi capability verifier và FFI effect model kết hợp.

---

# 186.115. Blocking FFI

Foreign call có thể:

```text
block
```

Nếu contract nói `MayBlock`, async wrapper không được giả vờ rằng call là nonblocking.

---

# 186.116. Async FFI adapter

Có thể:

```text
blocking foreign API
        ↓
worker thread
        ↓
Future
```

hoặc native callback/poll API.

Async abstraction nằm ở library/runtime.

---

# 186.117. Signal FFI

Signal handlers không được là ordinary arbitrary Axiom functions.

Dùng model:

```text
foreign signal
 ↓
atomic/event
 ↓
normal execution context
```

đã thống nhất với BOOTSTRAP-184.

---

# 186.118. FFI + comptime

Comptime có thể parse:

```text
header
IDL
metadata
```

nhưng gọi native runtime function trong comptime chỉ khi external execution capability cho phép và semantics được định nghĩa.

---

# 186.119. FFI + build system

Foreign dependency phải nằm trong build graph:

```text
package
 ├── Axiom source
 ├── axmeta
 ├── foreign headers
 ├── native library
 └── ABI contract
```

---

# 186.120. ABI fingerprint

Foreign declaration fingerprint bao gồm:

```text
ABI
target
signature
representation
calling convention
ownership contract
```

thay đổi → rebuild dependent bindings.

---

# 186.121. Header drift

Nếu:

```text
header v1
```

thay đổi nhưng `.axffi` không update, compiler không tự biết runtime library đã đổi.

Build system nên track header/library fingerprints.

---

# 186.122. ABI mismatch

Compiler phải phát hiện các mismatch có thể biết statically:

```text
wrong target
wrong ABI
wrong symbol
wrong calling convention
wrong representation
```

---

# 186.123. Runtime ABI mismatch

Một số mismatch chỉ phát hiện runtime:

```text
plugin version
dynamic symbol
driver version
OS API version
```

Loader/wrapper phải kiểm tra.

---

# 186.124. FFI unsafe boundary

Invariant:

> **Unsafe FFI does not disable semantic verification outside the exact foreign contract.**

Ví dụ:

```text
Foo owner
 ↓
unsafe C call
 ↓
only declared effects applied
 ↓
Foo state continues verified
```

---

# 186.125. Foreign memory provenance

Pointer returned từ C có provenance:

```text
Foreign
```

không tự biến thành Axiom-owned memory.

---

# 186.126. Foreign pointer → view

Chỉ tạo:

```text
view<T>
```

nếu contract xác lập:

```text
valid T representation
alignment
length
lifetime
read permission
```

---

# 186.127. Foreign pointer → mut_view

Cần thêm:

```text
exclusive mutation
```

và no-alias contract.

Nếu không chứng minh được → unsafe wrapper.

---

# 186.128. Foreign pointer → owner

Cần:

```text
ownership transfer
destructor/deallocator
layout
validity
```

---

# 186.129. Integer → pointer

Không được:

```text
u64 → safe pointer
```

Numeric address không tự có provenance.

Chỉ system/unsafe operation.

---

# 186.130. `memcpy`

FFI/system:

```text
memcpy
```

không phải generic safe copy của arbitrary `T`.

Compiler cần biết:

```text
byte-copy validity
overlap
alignment
initialization
```

---

# 186.131. `memmove`

Có thể overlap.

Wrapper semantics khác `memcpy`.

---

# 186.132. `memcmp`

Không phải semantic equality của Axiom types.

Padding/NaN/niche/representation khiến:

```text
memcmp(a,b) == 0
```

không đồng nghĩa:

```text
a == b
```

---

# 186.133. Serialization

Không dùng raw memory dump làm serialization mặc định.

Wire format là semantic contract riêng.

---

# 186.134. ABI vs wire format

Phân biệt:

```text
Memory representation
ABI representation
Wire representation
```

hoàn toàn.

---

# 186.135. Security boundary

Foreign code được coi là:

```text
untrusted with respect to Axiom invariants
```

cho tới khi wrapper contract xác lập điều ngược lại.

---

# 186.136. Safe FFI wrapper

Một wrapper tốt có dạng:

```text
safe input
 ↓
validate
 ↓
construct foreign representation
 ↓
unsafe FFI
 ↓
validate foreign output
 ↓
safe Axiom value
```

---

# 186.137. Wrapper generation

Axiom tooling nên hướng tới:

```text
C header
 ↓
bindgen
 ↓
raw ffi layer
 ↓
generated safe candidates
 ↓
human-reviewed contract
```

Không tự động tuyên bố mọi C API là safe.

---

# 186.138. FFI documentation

Mỗi unsafe FFI wrapper nên có machine-readable:

```text
/// SAFETY:
```

hoặc contract metadata.

Compiler/tooling có thể kiểm tra consistency.

---

# 186.139. FFI audit

CLI:

```text
axc inspect ffi package
```

có thể hiển thị:

```text
foreign calls
ownership transfers
external escapes
unsafe boundaries
unknown effects
ABI contracts
```

---

# 186.140. FFI graph

Compiler có thể xây:

```text
Axiom Owner
   ↓
Foreign Function
   ↓
Foreign Resource
   ↓
Destroy Function
```

và kiểm tra lifecycle.

---

# 186.141. FFI resource protocol

Tái sử dụng BOOTSTRAP-184:

```text
Acquire
Own
Use
Transfer
Close/Destroy
Drop
```

nhưng **không tạo universal Resource type**.

---

# 186.142. FFI + Drop

Nếu foreign resource destructor là infallible:

```text
Drop → destroy()
```

Nếu destructor có thể fail:

```text
close() -> Result
```

và Drop là best-effort/final release theo resource contract.

---

# 186.143. FFI destructor

Không được tự gọi foreign destructor nhiều lần.

Ownership verifier đảm bảo:

```text
exactly-once semantic cleanup
```

---

# 186.144. Foreign global state

Foreign global variables là external mutable state.

Compiler effect:

```text
Foreign
Read/Write
```

và optimizer không được giả định bất biến nếu không có contract.

---

# 186.145. Thread-local foreign state

`errno`, TLS APIs... được đánh dấu external TLS effects.

---

# 186.146. Signal-safe foreign calls

Signal context là execution domain đặc biệt.

Không được gọi arbitrary Axiom/foreign functions từ signal handler.

---

# 186.147. FFI and optimizer

Compiler **được tối ưu** foreign call nếu:

```text
pure/read-only
no observable external effects
contract permits
```

nhưng không được tự giả định purity.

---

# 186.148. Foreign call elimination

Một foreign call chỉ được eliminate nếu compiler chứng minh:

```text
no observable effect
```

theo contract.

---

# 186.149. Foreign call reordering

Không được reorder qua:

```text
IO
Atomic
Synchronization
Volatile
External state
```

nếu contract không cho phép.

---

# 186.150. FFI and LTO

Static foreign object/library có thể được LTO nếu compiler có IR hoặc compatible optimization metadata.

Dynamic library thì conservative.

---

# 186.151. Native object formats

Axiom linker/object writer phải hiểu:

```text
PE/COFF
ELF
Mach-O
WASM
```

và symbol/relocation semantics cần thiết cho FFI.

---

# 186.152. No mandatory C runtime

Axiom program không sử dụng C runtime:

```text
không phải link libc
```

trừ khi application/foreign dependency yêu cầu.

---

# 186.153. Freestanding FFI

Embedded:

```text
extern "C"
```

có thể gọi firmware/SDK ABI mà không cần OS runtime.

---

# 186.154. Kernel FFI

Kernel code có thể gọi:

```text
extern
```

nhưng FFI declaration phải compatible với kernel ABI.

---

# 186.155. Driver FFI

Device driver APIs thường cần:

```text
volatile
MMIO
interrupt
DMA
device memory
```

được khai báo trong system layer.

---

# 186.156. FFI and DMA

DMA buffer phải có explicit:

```text
stable address
alignment
storage domain
device visibility
lifetime
synchronization
```

Không dùng ordinary `Vec` mà không có contract.

---

# 186.157. Shared memory FFI

Shared memory:

```text
process A
 ↕
shared memory
 ↕
process B
```

không tự trở thành `Arc<T>`.

Cần explicit cross-process synchronization/layout contract.

---

# 186.158. ABI-generated views

Một API:

```text
foo(ptr, len)
```

có thể được expose an toàn:

```ax
fn foo(data: view<u8>) -> Result<...>
```

compiler lower đúng ABI.

Đây chính là mục tiêu **compiler hiểu nhiều hơn programmer phải viết**.

---

# 186.159. Safe abstraction principle

Programmer không nên phải viết:

```text
ptr = data.address()
len = data.length()
foo(ptr, len)
```

mỗi lần.

Thay vào đó:

```ax
foo(data)
```

và compiler/wrapper thực hiện ABI lowering.

---

# 186.160. FFI boundary summary

```text
                    AXIOM
                      │
             Ownership/Capability
                      │
                Safe wrapper
                      │
             ─── FFI boundary ───
                      │
             ABI + Contract
                      │
        ┌─────────────┼─────────────┐
        C            OS          GPU/WASM
```

---

# 186.161. Invariant đóng băng

### ABI

- **AFFI-20** — Foreign interoperability occurs through explicit ABI boundaries.
- **AFFI-21** — Foreign functions are not assumed safe without an explicit safety contract.
- **AFFI-22** — ABI identity is part of foreign function type identity.
- **AFFI-23** — Axiom ABI and foreign ABI are distinct.
- **AFFI-24** — ABI compatibility does not imply semantic compatibility.

### Ownership

- **AFFI-30** — Foreign pointers do not imply ownership.
- **AFFI-31** — Foreign ownership transfer must be explicit in the contract.
- **AFFI-32** — Foreign destruction must not occur more than once.
- **AFFI-33** — Foreign allocator domains must not be mixed without an explicit compatible contract.
- **AFFI-34** — Foreign retained pointers establish external escape/lifetime dependencies.
- **AFFI-35** — Stable foreign addresses require an explicit stable-storage contract.

### Capability

- **AFFI-40** — Foreign pointers cannot automatically become safe capabilities.
- **AFFI-41** — Pointer-to-view conversion requires validity, provenance, lifetime, alignment, and access proof.
- **AFFI-42** — Pointer-to-mut_view conversion additionally requires exclusive mutation proof.
- **AFFI-43** — Integer-to-pointer conversion does not establish valid provenance.
- **AFFI-44** — Unknown foreign aliasing is never treated as disjoint.
- **AFFI-45** — FFI does not erase verifier state outside the declared contract.

### Effects

- **AFFI-50** — Unknown foreign calls are conservatively effectful.
- **AFFI-51** — Foreign calls may declare precise effects.
- **AFFI-52** — Optimizers may exploit only proven foreign effect contracts.
- **AFFI-53** — Observable foreign effects cannot be eliminated or reordered incorrectly.
- **AFFI-54** — Foreign global state is external mutable state unless proven otherwise.

### Panic / unwind

- **AFFI-60** — Axiom panic must not implicitly unwind through foreign ABI boundaries.
- **AFFI-61** — Foreign exceptions must not implicitly unwind through Axiom frames.
- **AFFI-62** — Unwind behavior is an explicit ABI contract.
- **AFFI-63** — `setjmp`/`longjmp`-style control transfer cannot invalidate Axiom ownership state in safe code.

### Representation

- **AFFI-70** — Axiom layout is not C layout unless explicitly contracted.
- **AFFI-71** — `@repr(C)` establishes C-compatible representation where valid.
- **AFFI-72** — Opaque foreign types hide representation.
- **AFFI-73** — `void*` is not equivalent to dynamic `Any`.
- **AFFI-74** — Raw byte equality is not semantic value equality.
- **AFFI-75** — ABI representation is distinct from wire/serialization representation.

### Callbacks

- **AFFI-80** — Capturing closures are not implicitly C function pointers.
- **AFFI-81** — Callback lifetime must be explicit.
- **AFFI-82** — Callback thread/reentrancy behavior is part of the contract.
- **AFFI-83** — Callback panic/unwind behavior must be contained at the boundary.

### Tooling

- **AFFI-90** — Foreign bindings can be generated from external declarations/metadata.
- **AFFI-91** — Generated bindings do not automatically establish safety.
- **AFFI-92** — FFI dependencies participate in the build graph and artifact identity.
- **AFFI-93** — ABI mismatch must be diagnosed whenever statically detectable.
- **AFFI-94** — FFI inspection is available to compiler tooling and AI tooling.

---

# Trạng thái sau BOOTSTRAP-186

Axiom hiện đã có đủ một chuỗi rất quan trọng:

```text
                 AXIOM
                   │
     ┌─────────────┴─────────────┐
     │                           │
 Semantic World             Foreign World
     │                           │
 Ownership                  C / OS / GPU
 Capability                 Native libs
 Effects                    Dynamic libs
     │                           │
     └────── Explicit FFI ───────┘
                   │
             ABI Contract
                   │
             Safe Wrapper
```

Và một quyết định rất đáng giữ:

> **FFI không phải nơi compiler “bỏ cuộc”. FFI là nơi compiler chuyển từ những invariant Axiom có thể chứng minh sang những invariant được xác lập bởi foreign contract.**

Điều này cho phép Axiom vừa **low-level như C**, vừa không bắt người lập trình phải mang toàn bộ sự hỗn loạn của C pointer/ownership vào code Axiom.

---

# BOOTSTRAP-187 — Package Manager, Dependency Resolution, Reproducible Builds & Distribution

Bước tiếp theo là **đóng vòng build ecosystem**.

Ta đã có:

```text
Source
 ↓
Package graph
 ↓
CompilerDB
 ↓
.axmeta
 ↓
Native object
 ↓
Linker
 ↓
Executable
```

nhưng chưa chốt hoàn toàn:

- package identity
- version resolution
- dependency lock
- source registry
- binary packages
- local/path/git dependencies
- platform-specific dependencies
- feature resolution
- reproducible builds
- offline builds
- vendor dependencies
- source hash
- binary artifact identity
- package signing
- supply-chain verification
- cache
- incremental rebuild
- cross compilation
- SDK/target packs
- static/dynamic dependency selection
- dependency cycles
- workspace/monorepo
- build scripts
- generated source
- C/FFI dependencies
- system libraries
- package ABI compatibility
- package distribution mà **không biến Axiom thành một hệ sinh thái runtime khổng lồ**.

Đặc biệt cần chốt một nguyên tắc:

> **Package manager chỉ quản lý source, metadata, dependency và artifact; nó không được trở thành một phần bắt buộc của executable/runtime.**

Và đây cũng là nơi ta có thể thiết kế cơ chế để một project Axiom có thể:

```text
git clone
↓
axc build --offline
↓
native executable
```

với kết quả reproducible, không cần internet, không cần compiler bên thứ ba và không cần runtime package manager.