# BOOTSTRAP-175 — Interoperability Architecture: C ABI, System ABI, Foreign Types, Bindings & Native Interop
**FROZEN / COMPLETED**

Mục tiêu của task này là khóa một nguyên tắc:

> **Axiom phải có khả năng sống độc lập, nhưng không được bị cô lập khỏi thế giới native.**

Axiom có thể tự build native binary, nhưng vẫn phải gọi được:

```text
C libraries
OS APIs
system calls
shared libraries
native DLL/SO/dylib
GPU APIs
existing native binaries
hardware interfaces
```

mà phần lớn programmer **không phải tự xử lý pointer/ABI/lifetime bằng tay**.

---

# 175.1. Bốn tầng interoperability

Không nên coi mọi FFI là một thứ.

```text
Axiom semantic boundary
        ↓
Foreign language ABI
        ↓
Platform/System ABI
        ↓
Machine ABI
```

Ví dụ:

```text
Axiom
 ↓
extern "C"
 ↓
C ABI
 ↓
Windows x64 ABI
 ↓
x86-64 machine
```

Mỗi tầng có contract riêng.

---

# 175.2. Axiom ABI

Axiom-to-Axiom mặc định:

```text
extern "axiom"
```

hoặc ABI mặc định.

ABI này được compiler kiểm soát.

Nó có thể sử dụng:

```text
register passing
scalarization
sret
niche
optimized aggregate representation
```

mà không phải tương thích C.

---

# 175.3. C ABI

C ABI là boundary đầu tiên được Axiom hỗ trợ ổn định.

```ax
extern "C" {
    fn malloc(size: usize) -> *mut u8;
}
```

Nhưng raw pointer xuất hiện ở đây là **FFI/system-level**, không phải programming model thông thường của Axiom.

---

# 175.4. FFI không làm raw pointer trở thành safe

Ví dụ:

```ax
extern "C" fn foo(p: *mut Data);
```

Không có nghĩa compiler tự hiểu:

```text
p owns Data
p valid forever
p non-null
p initialized
p unique
```

Tất cả phải đến từ FFI contract.

---

# 175.5. Foreign declaration

Một foreign function conceptually có:

```text
ForeignFunction {
    name
    calling_convention
    parameters
    return_type
    effects
    ownership_contract
    capability_contract
    thread_contract
    ABI
}
```

Không chỉ là:

```text
name + types
```

---

# 175.6. FFI contract

Ví dụ:

```ax
extern "C" {
    fn read(
        fd: i32,
        buffer: mut_view<u8>
    ) -> isize;
}
```

Compiler cần biết:

```text
buffer được ghi
fd được đọc
không ownership transfer
có external IO
```

Những thông tin này feed vào:

```text
EffectInfo
CapabilityInfo
AliasInfo
EscapeInfo
```

---

# 175.7. FFI conservative mặc định

Nếu compiler không biết foreign function làm gì:

```text
extern unknown_ffi(...)
```

thì:

```text
Alias = UNKNOWN
Effects = conservative
Escape = possible external
```

Không được giả định:

```text
pure
readonly
noalias
```

---

# 175.8. FFI contract có thể tăng precision

Ví dụ wrapper có contract đã được xác minh:

```text
foo:
    reads A
    writes B
    does not retain capability
```

Compiler có thể dùng:

```text
A/B region information
```

để tối ưu.

Nhưng contract phải có semantic basis.

Không có annotation kiểu:

```text
"trust me, noalias"
```

để ép compiler tin sai.

---

# 175.9. FFI ownership

Foreign function có thể:

```text
borrow
consume
return ownership
allocate
deallocate
retain
release
```

Axiom phải mô hình hóa rõ.

Ví dụ:

```text
C:
foo_create() → owned pointer
foo_destroy(pointer)
```

Wrapper Axiom có thể biến thành:

```ax
let x = Foo.create()?;
...
```

với `Foo` là owning type.

---

# 175.10. Safe FFI wrapper

Mục tiêu:

```text
Raw C API
    ↓
unsafe binding
    ↓
safe Axiom wrapper
    ↓
normal Axiom application
```

Ví dụ conceptually:

```text
C pointer
    ↓
validated ownership
    ↓
Box<Foo> / FooHandle
    ↓
safe API
```

Unsafe tập trung ở boundary.

---

# 175.11. Không để unsafe lan truyền

Một thư viện tốt không yêu cầu:

```ax
unsafe {
    c_api(...)
}
```

ở mọi call site.

Chỉ binding layer xử lý unsafe.

Application dùng:

```ax
foo.process(data)?;
```

Compiler vẫn verify toàn bộ safe semantics.

---

# 175.12. C structs

Axiom:

```ax
@repr(C)
struct Point {
    x: f32;
    y: f32;
}
```

có:

```text
C-compatible layout
C-compatible alignment
C-compatible field order
```

Nhưng `@repr(C)` không biến mọi Axiom type thành C-compatible.

---

# 175.13. FFI-safe type

Compiler trait/marker:

```text
FfiSafe
```

được compiler kiểm soát.

Các type phổ biến có thể FFI-safe:

```text
integers
floats
bool theo ABI contract
C-compatible enums
@repr(C) structs
transparent newtypes
raw pointers
C strings
opaque handles
```

Trong khi:

```text
String
Vec<T>
closures
dyn Trait
generic types
```

không tự động là C ABI-safe.

---

# 175.14. String FFI

Axiom `String`:

```text
UTF-8 valid
owned
growable
```

không tự động tương đương:

```text
char*
char**
wchar_t*
```

C API phải dùng explicit wrapper:

```text
CStr
CString
CBytes
```

hoặc tương đương.

---

# 175.15. UTF-8 contract

Nếu foreign API yêu cầu:

```text
const char*
```

Axiom không được giả định đó là UTF-8.

Có thể là:

```text
UTF-8
locale encoding
arbitrary bytes
protocol-defined encoding
```

Binding phải chỉ rõ.

---

# 175.16. Nullable foreign pointers

C có:

```text
NULL
```

Axiom safe Core không có null.

Binding:

```text
*const T
```

có thể biểu diễn nullable machine pointer ở unsafe boundary.

Safe wrapper chuyển thành:

```text
Option<NonNullHandle>
```

hoặc semantic equivalent.

---

# 175.17. `Option` ↔ nullable ABI

Compiler có thể lower:

```text
Option<NonNull<T>>
```

thành:

```text
nullable pointer
```

nếu ABI contract cho phép.

Đây là optimization/representation.

Programmer không cần dùng null trong Core.

---

# 175.18. Opaque C types

Nhiều C API:

```c
typedef struct Foo Foo;
```

không expose layout.

Axiom tương ứng:

```text
opaque Foo
```

Consumer chỉ được:

```text
FooHandle
foo_create
foo_destroy
foo_do
```

Không được access private representation.

---

# 175.19. Native handle

OS handles không nên bị giả lập thành pointer.

Ví dụ:

```text
Windows HANDLE
Linux fd
Mach port
GPU resource handle
```

có thể trở thành distinct nominal types:

```text
FileHandle
WindowHandle
GpuHandle
```

với explicit ownership semantics.

---

# 175.20. Handle ≠ pointer

Đây tiếp tục nguyên tắc đã đóng băng:

```text
Handle
    = logical/external identity

Pointer
    = machine address capability
```

Không chuyển đổi implicit.

---

# 175.21. OS system calls

Axiom không bắt buộc libc.

Có thể:

```text
Axiom
 ↓
System ABI
 ↓
kernel syscall
```

Ví dụ trên Linux:

```text
syscall ABI
```

trên Windows:

```text
NT/native/platform APIs
```

tùy system layer.

---

# 175.22. System ABI

System ABI bao gồm:

```text
calling convention
register convention
stack convention
syscall convention
TLS
exception/unwind
thread-local structures
dynamic loader ABI
```

Đây là target/backend concern, không phải Core language semantics.

---

# 175.23. Calling conventions

Axiom cần explicit ABI names khi interop:

```text
"C"
"system"
"stdcall"
"fastcall"
"vectorcall"
"syscall"
```

chỉ những convention target hỗ trợ mới hợp lệ.

Không nên hard-code mọi convention vào Core.

---

# 175.24. Calling convention validation

Compiler phải kiểm tra:

```text
parameter classes
return classes
registers
stack alignment
variadic rules
callee/caller saved
aggregate passing
```

trước ABI MIR.

---

# 175.25. Variadic C functions

Ví dụ:

```text
printf(...)
```

không nên được coi như ordinary variadic Axiom function.

C variadic ABI có rules riêng.

Binding phải dùng:

```text
extern "C" fn(...)
```

với compiler-known foreign varargs semantics.

Safe wrappers nên cung cấp typed API.

---

# 175.26. C varargs type safety

Axiom không cố biến:

```text
printf("%d", arbitrary)
```

thành safe generic dynamic formatting.

Nên khuyến khích:

```text
std::io::write(...)
```

hoặc format wrapper.

Raw C varargs chỉ nằm tại FFI boundary.

---

# 175.27. Callbacks

Foreign API có thể yêu cầu:

```text
register_callback(fn_ptr, userdata)
```

Axiom phải xử lý:

```text
function pointer
closure
environment lifetime
thread execution
callback lifetime
ABI
```

riêng biệt.

---

# 175.28. Noncapturing callback

Một closure không capture có thể decay:

```text
closure
 ↓
function pointer
```

nếu signature/ABI tương thích.

Không cần heap allocation.

---

# 175.29. Capturing callback

Capturing closure:

```text
closure = code + environment
```

không tự động là C function pointer.

Có thể dùng explicit trampoline:

```text
Axiom closure
 ↓
userdata
 ↓
extern callback trampoline
 ↓
closure environment
```

Binding library chịu trách nhiệm lifetime.

---

# 175.30. Callback lifetime

Nếu foreign library giữ callback:

```text
register(callback)
```

thì compiler phải biết callback escape:

```text
ExternalEscape
```

Closure environment không thể bị stack-destroy nếu foreign system vẫn có quyền gọi.

---

# 175.31. Threaded callbacks

Nếu foreign library có thể callback trên thread khác:

```text
callback
    ↓
ThreadEscape
```

thì captured state phải đáp ứng:

```text
Send
```

và shared state phải đáp ứng:

```text
Share
```

nếu cần.

---

# 175.32. Foreign async APIs

Foreign API có thể:

```text
start_io(...)
callback(...)
```

Axiom wrapper có thể chuyển thành:

```text
Future<T>
```

nhưng đây là library/runtime abstraction.

Không biến foreign callback thành `async` semantic primitive tự động.

---

# 175.33. Foreign resource cleanup

Nếu foreign API yêu cầu:

```text
create
destroy
```

Axiom wrapper nên dùng Drop:

```text
Foo {
    raw: ForeignHandle
}

impl Drop for Foo {
    ...
}
```

Nhưng:

```text
Drop
```

chỉ làm deterministic cleanup.

Nếu destroy có thể fail recoverably:

```text
foo.close() -> Result
```

được gọi explicit trước Drop.

---

# 175.34. Foreign allocator

Đây là boundary rất quan trọng.

Không được:

```text
Axiom allocator
    ↓
free(C allocation)
```

một cách tùy tiện.

Allocator ownership phải match:

```text
allocator domain
```

Ví dụ:

```text
malloc → free
CoTaskMemAlloc → CoTaskMemFree
custom_alloc → custom_free
```

---

# 175.35. Allocation domain

Axiom nên coi allocator domain là semantic metadata:

```text
AllocationDomain {
    allocator
    ownership
    deallocator
    alignment
}
```

Foreign memory chỉ được Drop bằng đúng contract.

---

# 175.36. Foreign memory

Foreign memory có thể được wrap:

```text
ForeignBuffer
```

với:

```text
owner
length
alignment
storage domain
deallocator
thread contract
```

Sau đó safe API có thể expose:

```text
view<T>
mut_view<T>
```

nếu capability contract hợp lệ.

---

# 175.37. Zero-copy FFI

Mục tiêu:

```text
C buffer
 ↓
mut_view<u8>
 ↓
Axiom processing
```

không cần copy.

Nhưng compiler phải biết:

```text
buffer lifetime
ownership
mutation
foreign invalidation
```

---

# 175.38. FFI aliasing

Nếu C function có:

```text
void foo(float* a, float* b);
```

Axiom không tự assume:

```text
a != b
```

Nếu API contract đảm bảo disjoint:

```text
a: mut_view<f32>
b: mut_view<f32>
```

binding có thể encode contract phù hợp.

Nếu không chứng minh được:

```text
UNKNOWN
```

và compiler bảo thủ.

---

# 175.39. Foreign function effects

Ví dụ:

```text
read(fd, buffer)
```

effect:

```text
IO
Write(buffer)
```

Không phải:

```text
Write(all memory)
```

nếu binding có contract region chính xác.

---

# 175.40. FFI memory ordering

Foreign synchronization API phải được mô tả.

Ví dụ:

```text
foreign_mutex_lock()
foreign_mutex_unlock()
```

binding phải map semantic synchronization vào Axiom memory model.

Nếu không:

```text
Foreign
```

và compiler không được reorder vượt qua boundary theo cách phá semantics.

---

# 175.41. FFI atomics

Nếu foreign API cung cấp atomic operations, binding phải xác định:

```text
atomicity
ordering
width
alignment
scope
```

Axiom không đoán từ tên function.

---

# 175.42. Volatile hardware

Hardware register:

```text
volatile load/store
```

phải được biểu diễn explicit.

Không được dùng:

```text
ordinary memory load
```

rồi hy vọng compiler "biết".

---

# 175.43. Memory-mapped I/O

System layer có thể cung cấp:

```text
DeviceRegion<T>
```

và chuyển thành:

```text
volatile view
```

với explicit capability.

Không đưa device memory vào ordinary `Vec<T>` semantics.

---

# 175.44. Inline assembly

Inline assembly thuộc:

```text
unsafe/system
```

và có structured contract:

```text
inputs
outputs
clobbers
memory effects
flags
volatile
side effects
target features
```

Không cho phép string assembly không kiểm soát như semantic Core primitive.

---

# 175.45. Native intrinsics

Axiom có thể expose:

```text
std::arch
```

với target-specific intrinsic wrappers.

Ví dụ:

```text
AVX2
AVX-512
NEON
SVE
RISC-V Vector
```

Compiler có thể lower trực tiếp.

---

# 175.46. Intrinsic availability

Compiler phải check:

```text
target architecture
target feature
ABI
```

Nếu instruction không tồn tại:

```text
compile error
```

hoặc explicit runtime dispatch.

Không được silently emit unsupported instruction.

---

# 175.47. Runtime CPU dispatch

Có thể:

```text
generic implementation
      +
AVX2 implementation
      +
AVX-512 implementation
```

và runtime chọn implementation.

Đây là library/system mechanism.

PGO có thể hỗ trợ quyết định, nhưng không biến profile thành semantic proof.

---

# 175.48. C++ interoperability

C++ không có một ABI duy nhất đủ portable giữa mọi compiler/version.

Vì vậy Axiom **không nên hứa C++ ABI tổng quát** trong Core.

Thay vào đó:

```text
C ABI = stable interoperability layer
```

và C++ binding thường qua:

```text
extern "C"
C shim
generated wrapper
```

---

# 175.49. Direct C++ ABI

Có thể hỗ trợ target-specific:

```text
extern "C++"
```

nhưng đây là **platform/compiler ABI integration**, không phải universal Axiom ABI guarantee.

Metadata phải chỉ rõ:

```text
compiler family
ABI version
target
C++ ABI mode
```

---

# 175.50. Name mangling

Axiom symbol:

```text
foo
```

không nhất thiết machine symbol phải là `foo`.

Compiler có:

```text
Axiom mangling
C unmangled
platform-specific mangling
```

`@export("foo")` khóa external name.

---

# 175.51. Symbol visibility

Phân biệt:

```text
pub
@export
symbol visibility
dynamic export
```

Ví dụ:

```text
pub
```

không làm symbol xuất hiện trong DLL/SO.

---

# 175.52. Shared library loading

System library có thể cung cấp:

```text
load_library()
lookup_symbol()
```

Nhưng đây là explicit dynamic loading.

Compiler không giả định mọi package là dynamic.

---

# 175.53. Open-world boundary

Dynamic loading:

```text
load_library(path)
```

tạo Open World.

Compiler không thể assume:

```text
all possible implementations known
```

Do đó hạn chế:

```text
devirtualization
DCE
ICF
whole-program assumptions
```

tại boundary.

---

# 175.54. Closed-world binary

Executable static link:

```text
all reachable objects known
```

cho phép:

```text
LTO
DCE
devirtualization
specialization
ICF
layout optimization
```

miễn semantics cho phép.

---

# 175.55. Plugin ABI

Axiom plugin nên ưu tiên:

```text
Stable C-like ABI
+
opaque handles
+
explicit function table
+
version descriptor
```

thay vì expose arbitrary internal Axiom types.

---

# 175.56. Plugin descriptor

Conceptual:

```text
PluginDescriptor {
    abi_version
    api_version
    capabilities
    init
    shutdown
    functions
}
```

Host kiểm tra compatibility trước khi sử dụng.

---

# 175.57. Capability negotiation

Plugin có thể khai báo:

```text
GPU
Filesystem
Network
GUI
Audio
...
```

Host không tự động cấp tất cả.

Đây phù hợp với capability-based system layer của Axiom.

---

# 175.58. Foreign type safety

Foreign type phải có category:

```text
Opaque
CStruct
CEnum
Handle
RawPointer
ForeignOwned
ForeignBorrowed
ForeignCallback
DeviceResource
```

Compiler dùng category để kiểm tra boundary.

---

# 175.59. Binding generator

Axiom nên có tool:

```text
axbind
```

hoặc compiler-integrated equivalent.

Input:

```text
C header
ABI metadata
platform metadata
```

Output:

```text
Axiom FFI declarations
safe wrapper skeleton
ownership annotations/contracts
```

---

# 175.60. Binding generator không chỉ parse header

Header C không đủ để biết:

```text
ownership
thread safety
lifetime
callback retention
encoding
allocator
```

Do đó binding metadata có thể thêm:

```text
axffi
```

contract file.

---

# 175.61. FFI contract example

Conceptual:

```text
foo_create:
    returns owned Foo

foo_get_data:
    returns borrowed read-only region
    lifetime = Foo

foo_process:
    reads input
    writes output
    does_not_retain = true

foo_destroy:
    consumes Foo
```

Compiler có thể chuyển thành Axiom semantic contracts.

---

# 175.62. FFI contract trust

Có ba mức:

```text
Verified
Trusted
Unknown
```

`Unknown` conservative.

`Trusted` thường dành cho:

```text
system bindings
hand-audited wrappers
compiler-known ABI
```

Không được coi arbitrary foreign declaration là verified safe.

---

# 175.63. Unsafe boundary

Architecture:

```text
                    Axiom
                      │
                 Safe program
                      │
               safe wrapper
                      │
                UNSAFE FFI
                      │
             Foreign contract
                      │
             Native environment
```

Unsafe là boundary, không phải toàn bộ application programming model.

---

# 175.64. Foreign exceptions

C++ exception/SEH/platform exception không được tự động trở thành Axiom `Result`.

Boundary phải explicit:

```text
foreign call
 ↓
exception handling adapter
 ↓
Result<T,E>
```

nếu muốn.

---

# 175.65. Panic ↔ foreign exception

Axiom:

```text
panic
```

và foreign exception là hai semantics khác nhau.

Không được mặc định để panic xuyên C ABI.

FFI boundary phải quy định:

```text
abort
catch
translate
forbid
```

---

# 175.66. Unwind ABI

Nếu:

```text
panic=unwind
```

thì Axiom unwind metadata phải tương thích target.

Nhưng C ABI function không tự động trở thành safe exception boundary.

---

# 175.67. Thread-local storage

Foreign TLS:

```text
errno
Windows TLS
pthread TLS
```

có thể được expose qua system library.

Không biến foreign TLS thành global mutable Axiom variable.

---

# 175.68. `errno`

Ví dụ C:

```text
errno
```

không nên map thành:

```text
global i32
```

một cách đơn giản.

Nó là thread-local external state.

Wrapper có thể:

```text
Result<T, OsError>
```

và đọc `errno` đúng thời điểm.

---

# 175.69. Foreign global variables

Có thể khai báo:

```text
extern static
```

nhưng semantics phải ghi:

```text
read
write
volatile?
atomic?
TLS?
```

Không coi foreign global là ordinary safe mutable global.

---

# 175.70. ABI adaptation layer

Axiom compiler nên có:

```text
Axiom semantic call
        ↓
FFI lowering
        ↓
ABI adaptation
        ↓
target calling convention
        ↓
machine call
```

Không để frontend biết register-level ABI details.

---

# 175.71. C ABI lowering

Ví dụ semantic:

```text
String
```

không được trực tiếp pass vào C.

Compiler/wrapper phải chuyển explicit thành:

```text
ptr + length
```

hoặc:

```text
const char*
```

tùy API.

Physical representation là ABI decision.

---

# 175.72. ABI ownership preservation

Một return:

```text
Foo
```

có semantic ownership transfer.

ABI có thể:

```text
register
sret
caller-allocated buffer
```

Nhưng:

```text
physical mechanism
≠
ownership semantics
```

giữ đúng nguyên tắc của AABI.

---

# 175.73. Cross-language `Drop`

Axiom Drop không được tự động chạy khi C code sở hữu object.

Boundary phải quy định:

```text
Axiom owns → Axiom Drop
C owns → C destructor
shared → explicit retain/release
```

---

# 175.74. Reference counting interoperability

Foreign library có thể có:

```text
retain()
release()
```

Axiom wrapper:

```text
ForeignShared<T>
```

có thể map vào Drop.

Nhưng compiler không tự biến nó thành `Arc<T>`.

---

# 175.75. Foreign synchronization wrappers

C mutex:

```text
pthread_mutex_t
```

có thể được wrap thành Axiom `Mutex<T>`-like abstraction.

Safe wrapper phải chứng minh:

```text
lock/unlock pairing
guard lifetime
no await crossing
ownership
```

---

# 175.76. Foreign async/event loop

Libuv/epoll/IOCP/kqueue/... có thể được wrap thành:

```text
std::async
std::io
```

Nhưng executor/event loop implementation không thuộc Core.

Axiom async semantic vẫn:

```text
Future + await
```

---

# 175.77. GPU interoperability

GPU resource:

```text
CUDA
Vulkan
Metal
DirectX
OpenCL
```

không tự động trở thành `DeviceBuffer<T>`.

Foreign resource có:

```text
External storage domain
```

và explicit contract.

---

# 175.78. Device pointer

Device pointer không được:

```text
*mut T → ordinary mut_view<T>
```

một cách implicit.

Phải xác định:

```text
storage domain
execution domain
access capability
lifetime
synchronization
```

---

# 175.79. Interop với WASM

WASM ABI là một ABI riêng:

```text
Axiom
 ↓
WASM LIR
 ↓
WASM module
```

Host imports/exports phải explicit.

Strings/buffers thường qua:

```text
pointer + length
```

hoặc generated interface.

---

# 175.80. WASM host boundary

Host function:

```text
import("env", "foo")
```

là foreign call.

Compiler phải biết:

```text
effects
memory interaction
ownership
```

nếu metadata có.

Nếu không:

```text
Foreign + conservative
```

---

# 175.81. Native library discovery

Build system có thể hỗ trợ:

```text
system library
pkg-config
framework
SDK
explicit path
```

nhưng dependency identity phải được ghi vào build metadata.

Không để:

```text
machine local environment
```

âm thầm thay đổi semantic artifact mà không được track.

---

# 175.82. Reproducible FFI build

Build identity cần chứa:

```text
foreign library identity
ABI version
headers/bindings hash
target SDK
link flags
```

khi chúng ảnh hưởng binary.

---

# 175.83. SDK/platform version

Ví dụ:

```text
Windows SDK
Android NDK
Apple SDK
Linux system ABI
```

có thể ảnh hưởng generated declarations/ABI.

Build graph phải track chúng khi cần.

---

# 175.84. FFI metadata trong `.axmeta`

Package metadata có thể ghi:

```text
extern symbols
ABI
calling conventions
foreign dependencies
FFI-safe types
ownership contracts
```

để downstream compiler không phải đoán.

---

# 175.85. C header generation

Ngược lại:

```text
Axiom
 ↓
@repr(C)
extern "C"
 ↓
axc emit-c-header
 ↓
foo.h
```

Compiler có thể tự sinh header.

Không cần parser thứ ba.

---

# 175.86. Header stability

Generated C header chỉ ổn định nếu:

```text
@abi(stable)
```

hoặc package contract tương đương.

Default Axiom representation không được giả định stable.

---

# 175.87. FFI testing

Compiler test suite cần có:

```text
Axiom ↔ C
Axiom ↔ system ABI
Axiom ↔ shared library
Axiom ↔ callbacks
Axiom ↔ foreign allocation
Axiom ↔ foreign threading
Axiom ↔ foreign atomics
Axiom ↔ foreign exceptions
```

và cross-target tests.

---

# 175.88. ABI probe

Axiom tool có thể cung cấp:

```text
axc inspect abi Foo
axc inspect ffi foo
axc emit-c-header
axc bind c-header.h
```

ABI inspector hiển thị:

```text
size
alignment
offset
parameter classification
return classification
calling convention
symbol
ownership
effects
```

---

# 175.89. AI-readable FFI diagnostics

Ví dụ:

```text
E_FFI_LAYOUT_MISMATCH

Axiom type: Foo
Foreign type: struct Foo

Expected:
  size = 32
  alignment = 8

Actual:
  size = 40
  alignment = 8

Reason:
  Axiom default representation is not C-compatible.

Suggestion:
  add @repr(C)
```

Đây rất phù hợp với compiler API cho AI.

---

# 175.90. Interoperability architecture hoàn chỉnh

```text
                         Axiom
                           │
                    Semantic Types
                           │
                    ┌──────┴──────┐
                    ↓             ↓
              Axiom ABI       FFI ABI
                    │             │
                    │       ┌─────┼─────┐
                    │       ↓     ↓     ↓
                    │       C    OS   GPU
                    │       │     │     │
                    │       ↓     ↓     ↓
                    │     Native System APIs
                    │             │
                    └──────┬──────┘
                           ↓
                    Target Machine ABI
                           ↓
                       Machine Code
```

---

# 175.91. Nguyên tắc tối quan trọng

Axiom phải đảm bảo:

```text
                    SAFE AXIOM
                         │
               compiler-managed
             ownership/capability
                         │
                  SAFE WRAPPER
                         │
                  UNSAFE BOUNDARY
                         │
                 FOREIGN CONTRACT
                         │
                  NATIVE WORLD
```

Không đảo ngược thành:

```text
Axiom application
    ↓
raw pointer everywhere
    ↓
manual lifetime
    ↓
manual ABI
```

Nếu vậy Axiom sẽ mất một trong những lợi thế lớn nhất mà chúng ta đã thiết kế.

---

# 175.92. Invariants đóng băng

### ABI

- **AFFI-20** — FFI là semantic boundary explicit.
- **AFFI-21** — Foreign declaration phải có ABI xác định.
- **AFFI-22** — C ABI là interoperability ABI ổn định đầu tiên.
- **AFFI-23** — Default Axiom ABI không mặc định C-compatible.
- **AFFI-24** — Calling convention phải được kiểm tra trước ABI MIR.
- **AFFI-25** — Foreign unknown call được xử lý conservative.
- **AFFI-26** — FFI không tự động bypass ownership/capability verification.

### Memory

- **AFFI-30** — Foreign pointer không tự động là owner.
- **AFFI-31** — Foreign pointer không tự động là safe capability.
- **AFFI-32** — Foreign allocation phải có allocator/deallocator contract.
- **AFFI-33** — Foreign memory có storage/ownership domain explicit.
- **AFFI-34** — Zero-copy FFI được hỗ trợ khi capability/lifetime được chứng minh.
- **AFFI-35** — Integer→pointer không tạo safe provenance.
- **AFFI-36** — Foreign memory có thể escape nhưng phải được compiler model.

### Ownership

- **AFFI-40** — Foreign ownership transfer phải explicit.
- **AFFI-41** — Axiom Drop chỉ cleanup resource mà Axiom contract sở hữu.
- **AFFI-42** — Foreign retain/release phải được biểu diễn bằng explicit wrapper semantics.
- **AFFI-43** — Foreign callback retention phải được model như escape.
- **AFFI-44** — Callback chạy trên execution domain khác phải tuân thủ Send/Share.

### Synchronization

- **AFFI-50** — Foreign synchronization phải có memory-order contract hoặc được xử lý conservative.
- **AFFI-51** — Foreign atomic operations phải chỉ rõ atomicity/order.
- **AFFI-52** — Foreign volatile access phải giữ semantics volatile.
- **AFFI-53** — Foreign blocking operation là effect và không được ngụy trang thành pure computation.

### Representation

- **AFFI-60** — `@repr(C)` là explicit C layout contract.
- **AFFI-61** — Axiom `String` không tự động là C string.
- **AFFI-62** — Nullable foreign pointer không tạo null trong Safe Core.
- **AFFI-63** — Opaque foreign types không expose representation.
- **AFFI-64** — Handle và pointer là hai semantic concepts khác nhau.
- **AFFI-65** — ABI representation không được thay đổi semantic ownership.

### Dynamic libraries

- **AFFI-70** — Dynamic loading tạo open-world boundary.
- **AFFI-71** — Open-world code không được dùng closed-world optimization assumptions.
- **AFFI-72** — Plugin ABI phải explicit và versioned.
- **AFFI-73** — Runtime symbol lookup không mặc định an toàn.
- **AFFI-74** — Stable plugin ABI ưu tiên opaque handles/function tables.

### Tooling

- **AFFI-80** — Binding generator phải tạo declaration có ABI information.
- **AFFI-81** — Header không đủ để suy ra ownership/thread/lifetime semantics.
- **AFFI-82** — FFI contract có thể bổ sung semantic information.
- **AFFI-83** — Trusted FFI contract không được tự động cấp semantic properties trái với verifier.
- **AFFI-84** — C header generation chỉ stable khi ABI contract stable.
- **AFFI-85** — FFI dependency identity phải tham gia reproducible build identity.

### Safety

- **AFFI-90** — Unsafe nên được tập trung tại FFI/system boundary.
- **AFFI-91** — Safe wrappers phải tái thiết lập Axiom safety invariants.
- **AFFI-92** — Foreign exceptions không tự động trở thành `Result`.
- **AFFI-93** — Axiom panic không tự động xuyên FFI boundary.
- **AFFI-94** — FFI không được làm suy yếu safe-code guarantees.

---

# BOOTSTRAP-175 hoàn tất

Sau task này, Axiom đã có một đường đi khá hoàn chỉnh:

```text
Axiom source
     ↓
Semantic type/ownership/capability
     ↓
Verified MIR
     ↓
Optimization
     ↓
Axiom ABI / FFI ABI
     ↓
System ABI
     ↓
Machine code
     ↓
Native binary
```

và theo chiều ngược lại:

```text
C / OS / GPU / native library
             ↓
       FFI declaration
             ↓
       Contract validation
             ↓
        Safe wrapper
             ↓
        Normal Axiom
```

Điểm quan trọng là **interop không phá vỡ triết lý của Axiom**: programmer chỉ phải chạm raw pointer/ABI details ở nơi thực sự cần.

---

# BOOTSTRAP-176 — Concurrency Runtime, Threading, Synchronization & Scheduler Implementation

Bước tiếp theo nên chuyển từ **semantic concurrency model đã đóng băng** sang **implementation architecture của concurrency runtime**:

```text
Thread
 ├── OS thread
 ├── TLS
 ├── stack
 └── lifecycle

Scheduler
 ├── worker
 ├── task queue
 ├── work stealing
 ├── affinity
 └── shutdown

Synchronization
 ├── Mutex
 ├── RwLock
 ├── Semaphore
 ├── Condvar
 ├── Atomics
 └── Channels

Async
 ├── Executor
 ├── Waker
 ├── Timer
 ├── IO completion
 └── cancellation

Structured concurrency
 ├── scope
 ├── JoinHandle
 ├── cancellation
 └── failure propagation
```

Mục tiêu của task này sẽ là khóa **cách Axiom thực sự chạy thread/task/async trên OS mà không biến toàn bộ chương trình thành một runtime nặng**, đồng thời giữ nguyên các semantic invariants của `Send`, `Share`, ownership, capability và memory model đã đóng băng.