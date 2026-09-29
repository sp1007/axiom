# BOOTSTRAP-154 — FFI, C ABI, System ABI & Foreign Function Interface Safety
**STATUS: FROZEN / COMPLETED**

> **FFI là semantic boundary, không phải “unsafe zone” nơi compiler bỏ kiểm tra. Axiom phải giao tiếp được với thế giới bên ngoài mà vẫn giữ ownership, capability, ABI và memory safety ở phía Axiom.**

Đây là một trong những phần quan trọng nhất của Axiom. Nếu làm tốt, Axiom có thể dùng hệ sinh thái native hiện có mà **không cần biến C/C++ thành dependency của ngôn ngữ**.

---

# 1. Mục tiêu

Axiom phải hỗ trợ hai chiều:

```text
Axiom → Foreign
Foreign → Axiom
```

Ví dụ:

```text
Axiom
  ↓
Windows API
Linux API
C library
GPU API
Native SDK
```

và:

```text
C/C++/Rust/Swift/...
        ↓
    Axiom library
```

---

# 2. FFI không phải một loại type system riêng

FFI sử dụng các semantic type hiện có:

```text
i32
u64
f32
struct
enum
view
mut_view
raw pointer
function
```

nhưng thêm:

```text
FFI Contract
```

để mô tả representation + ownership + ABI.

---

# 3. Ba tầng ABI

Axiom cần phân biệt:

```text
Axiom ABI
C ABI
System ABI
```

### Axiom ABI

Tối ưu cho Axiom.

### C ABI

Interoperability phổ biến:

```text
extern "C"
```

### System ABI

Ví dụ:

```text
Windows x64
SysV AMD64
AArch64
WASM
```

System ABI không nhất thiết đồng nghĩa C ABI.

---

# 4. Foreign declaration

Ví dụ:

```ax
extern "C" {
    fn strlen(s: *const u8) -> usize;
}
```

Đây là declaration của symbol bên ngoài.

Nhưng:

```text
*const u8
```

là raw pointer → unsafe boundary.

Axiom không giả định ownership của `s`.

---

# 5. FFI-safe types

Không phải mọi Axiom type đều được phép đi qua C ABI.

Ví dụ có thể:

```text id="ffi01"
i8..i64
u8..u64
f32
f64
raw pointer
@repr(C) struct
@repr(C) enum với contract phù hợp
```

Nhưng không mặc định:

```text id="ffi02"
Vec<T>
String
closure
dyn Trait
Arc<T>
Future<T>
```

vì representation/ownership của chúng không phải C ABI.

---

# 6. `FfiSafe`

Axiom có marker/auto trait:

```text id="ffi03"
FfiSafe
```

Compiler tự xác định.

Ví dụ:

```ax
@repr(C)
struct Point {
    x: f32,
    y: f32
}
```

có thể được compiler xác nhận:

```text
Point: FfiSafe
```

Programmer không thể dùng `unsafe` để giả mạo property này.

---

# 7. `@repr(C)`

```ax
@repr(C)
struct Point {
    x: f32,
    y: f32
}
```

cam kết representation C-compatible.

Trong trường hợp này compiler không được tự do:

```text
reorder fields
```

như struct Axiom bình thường.

---

# 8. `@repr(C)` không biến mọi thứ thành C-compatible

Ví dụ:

```ax
@repr(C)
struct Foo {
    values: Vec<i32>
}
```

không tự động trở thành C-safe.

Compiler phải kiểm tra **đệ quy toàn bộ representation**.

---

# 9. Opaque foreign types

Rất cần cho OS/API.

Ví dụ:

```ax
extern type HWND;
extern type FILE;
extern type CGContext;
```

Axiom không biết layout.

Chỉ biết:

```text id="ffi04"
opaque identity
```

và sử dụng handle/pointer theo FFI contract.

---

# 10. Opaque handle

API kiểu:

```text id="ffi05"
HANDLE
FILE*
VkDevice
```

không nên buộc programmer phải biết cấu trúc bên trong.

Axiom wrapper có thể:

```ax
struct Window {
    handle: *mut ForeignWindow
}
```

với ownership contract rõ ràng.

---

# 11. Foreign ownership

Đây là phần cực kỳ quan trọng.

Foreign function có thể:

```text id="ffi06"
borrow
consume
return ownership
retain
release
```

Axiom phải biết contract.

Ví dụ:

```ax
extern "C" fn create_buffer() -> *mut Buffer;
extern "C" fn destroy_buffer(p: *mut Buffer);
```

Wrapper:

```text id="ffi07"
create_buffer
    → ownership enters Axiom

drop Buffer
    → destroy_buffer
```

---

# 12. Foreign allocator

Không được:

```text id="ffi08"
Axiom alloc
   ↓
foreign free
```

hoặc:

```text id="ffi09"
foreign alloc
   ↓
Axiom dealloc
```

trừ khi ABI contract xác nhận allocator compatibility.

Mỗi allocation domain cần được nhận diện:

```text id="ffi10"
AxiomAllocator
ForeignAllocator
OSAllocator
CustomAllocator
```

---

# 13. C strings

Axiom không có implicit C string.

Có:

```text id="ffi11"
String
Str
Bytes
```

và C ABI:

```text id="ffi12"
*const u8
```

Nếu cần:

```ax
cstr(s)
```

thì đây là explicit conversion/wrapper.

Không được:

```text
String → *const char
```

một cách ngầm định.

---

# 14. Null pointers

Safe Axiom:

```text id="ffi13"
no null
```

Foreign C API có thể trả:

```text id="ffi14"
NULL
```

Wrapper phải chuyển thành:

```text id="ffi15"
Option<...>
```

nếu semantics phù hợp.

Ví dụ:

```text
C pointer
 ↓
Option<ForeignHandle>
```

---

# 15. Raw pointer vẫn là unsafe

```ax
*const T
*mut T
```

chỉ là machine-level pointer.

Compiler không tự suy ra:

```text id="ffi16"
ownership
lifetime
validity
alignment
non-null
```

từ pointer.

---

# 16. FFI contract

Axiom nên có contract metadata:

```text id="ffi17"
FfiContract {
    abi
    calling_convention
    parameter_contracts
    return_contract
    ownership
    nullability
    alignment
    aliasing
    thread_safety
    unwind
    effects
}
```

---

# 17. Programmer không phải viết mọi contract

Nếu FFI declaration đủ đơn giản:

```ax
extern "C" fn abs(x: i32) -> i32;
```

compiler biết:

```text
ABI
types
calling convention
```

không cần annotation dư thừa.

Chỉ những semantics mà ABI không thể suy ra mới cần contract.

---

# 18. Ownership annotation ở FFI boundary

Ví dụ conceptual:

```ax
extern "C" {
    @returns_owned
    fn create() -> *mut Foo;

    @consumes
    fn destroy(foo: *mut Foo);
}
```

Các annotation này **không phải lifetime system**.

Chúng chỉ mô tả foreign contract.

---

# 19. FFI wrapper nên là safe abstraction

Mục tiêu:

```text id="ffi18"
unsafe FFI
     ↓
safe wrapper
     ↓
ordinary Axiom
```

Ví dụ programmer sử dụng:

```ax
let file = File.open(...)?;
file.write(data)?;
```

không cần biết bên dưới:

```text
*mut FILE
```

---

# 20. Foreign calls là conservative boundary

Nếu compiler không biết foreign function làm gì:

```text id="ffi19"
extern fn unknown(...)
```

thì:

```text
Alias = UNKNOWN
Effect = conservative
Escape = conservative
```

Compiler không được giả định:

```text
pure
readonly
noalias
```

---

# 21. Verified FFI contract

Nếu có contract:

```text id="ffi20"
extern {
    @reads_only
    fn inspect(...);
}
```

compiler phải có cơ chế xác nhận contract theo mức tin cậy.

Có thể chia:

```text
Verified
Trusted
Unverified
```

nhưng không được coi declaration bên ngoài là semantic proof nếu không có cơ sở.

---

# 22. Unsafe FFI

Một foreign call có thể nằm trong:

```ax
unsafe {
    foreign_call(...)
}
```

Nhưng:

```text
unsafe ≠ disable all compiler checks
```

Axiom vẫn kiểm tra:

```text
type
ABI
argument representation
ownership state
capability state
```

Chỉ các precondition không thể chứng minh mới thuộc trách nhiệm unsafe contract.

---

# 23. Calling convention

Axiom cần abstraction:

```text
CallingConvention
```

Ví dụ:

```text
Axiom
C
System
Fast
Vector
Wasm
TargetSpecific
```

Không hard-code calling convention vào parser.

---

# 24. `extern "C"`

Ví dụ:

```ax
extern "C" {
    fn malloc(size: usize) -> *mut u8;
}
```

Compiler:

```text
resolve symbol
 ↓
C ABI
 ↓
ABI classification
 ↓
Axiom LIR
 ↓
machine call
```

---

# 25. Export Axiom function

Axiom function có thể export:

```ax
@export("axiom_add")
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Nhưng:

```text
pub
```

không có nghĩa:

```text
native export
```

như đã frozen.

---

# 26. Exported ABI phải explicit

Nếu muốn C gọi:

```ax
@export("axiom_add", abi="C")
fn add(...)
```

hoặc dùng declaration style tương đương.

Compiler kiểm tra:

```text
FfiSafe
ABI
symbol
calling convention
```

---

# 27. Generic functions không export trực tiếp

Ví dụ:

```ax
fn max<T: Ord>(a: T, b: T) -> T
```

không thể export C ABI như một symbol duy nhất.

Phải specialize:

```text id="ffi21"
max<i32>
max<f64>
```

hoặc export một wrapper concrete.

---

# 28. Closures và callbacks

Capturing closure:

```ax
|x| foo(x)
```

không phải mặc định C function pointer.

Noncapturing closure có thể decay:

```text id="ffi22"
closure
 ↓
function pointer
```

nếu ABI phù hợp.

Capturing callback cần explicit environment contract:

```text id="ffi23"
callback function
+
context pointer
```

---

# 29. Callback lifetime

Foreign code có thể giữ callback lại.

Ví dụ:

```text id="ffi24"
register_callback(cb)
```

Compiler không thể giả định callback chỉ tồn tại trong call.

Nếu foreign API có:

```text id="ffi25"
callback retained
```

thì environment phải có ownership/storage contract.

---

# 30. Async callback

Foreign async APIs có thể:

```text id="ffi26"
start()
 ↓
callback later
```

Không được biến callback thành Future một cách mù quáng.

Wrapper có thể tạo:

```text id="ffi27"
Future<T>
```

nhưng phải giữ:

```text callback environment
buffer
foreign handle
```

đủ lâu.

---

# 31. Foreign threads

Nếu callback chạy trên foreign thread:

```text id="ffi28"
Foreign Thread
       ↓
Axiom callback
```

compiler/runtime phải xác định:

```text Send
Share
thread attachment
TLS
runtime availability
```

Không mặc định callback chạy trên Axiom thread.

---

# 32. FFI + Send/Share

Một foreign API giữ object rồi sử dụng trên thread khác:

```text id="ffi29"
```

phải có contract.

Nếu không biết:

```text id="ffi30"
→ conservative
```

Không tự suy luận `Send`.

---

# 33. FFI + async

`Future` không tự động là FFI-safe.

Cần adapter:

```text id="ffi31"
Foreign Async API
       ↓
FFI adapter
       ↓
Axiom Future
```

---

# 34. Variadic functions

Cần hỗ trợ:

```ax
extern "C" {
    fn printf(fmt: *const u8, ...) -> i32;
}
```

nhưng variadic boundary phải có semantics rõ.

Đặc biệt:

```text default argument promotions
ABI classification
target-specific varargs
```

không được tự đoán.

---

# 35. Variadic Axiom functions

Không nên cho phép Axiom function bình thường tự biến thành C variadic nếu không có ABI contract.

Đây là FFI/system feature.

---

# 36. Struct passing

Compiler phải quyết định:

```text id="ffi32"
register
stack
indirect
split
sret
```

theo C/System ABI.

Programmer không phải tự viết assembly-compatible layout.

---

# 37. Enum FFI

Enum Axiom:

```ax
enum Color {
    Red,
    Green,
    Blue
}
```

không mặc định C ABI.

Muốn interoperable:

```ax
@repr(C)
enum Color {
    ...
}
```

Compiler kiểm tra representation contract.

---

# 38. Tagged union

C union không hoàn toàn giống Axiom enum.

Nếu FFI có:

```text id="ffi33"
union
```

cần representation contract rõ ràng.

Không tự map:

```text C union == Axiom enum
```

---

# 39. Bitfields

C bitfields phụ thuộc compiler/ABI.

Không nên giả định chúng là ordinary Axiom fields.

Nên hỗ trợ qua:

```text id="ffi34"
@repr(C)
system/FFI layout contract
```

hoặc explicit bitfield declaration trong system layer.

---

# 40. Packed structures

```ax
@repr(packed)
```

có thể tạo unaligned access.

Do đó:

```text id="ffi35"
@repr(packed)
→ unsafe/system representation
```

Compiler không được tạo ordinary aligned reference/view rồi giả định alignment.

---

# 41. Alignment contract

FFI có thể yêu cầu:

```text id="ffi36"
align = N
```

Compiler kiểm tra trước khi tạo capability phù hợp.

---

# 42. Foreign memory

Memory từ foreign system:

```text id="ffi37"
malloc
mmap
GPU allocation
OS mapped memory
```

cần explicit storage domain:

```text id="ffi38"
EXTERNAL
```

Không mặc định coi nó là Axiom-owned heap.

---

# 43. Foreign memory → view

Nếu contract đảm bảo:

```text id="ffi39"
address
length
alignment
validity
lifetime
```

unsafe boundary có thể tạo:

```text id="ffi40"
view<T>
```

Sau đó Axiom verifier tiếp tục quản lý capability.

Đây chính là:

```text
unsafe establishes contract
        ↓
safe verification resumes
```

---

# 44. Memory mapped files

Ví dụ:

```text id="ffi41"
mmap
 ↓
external memory region
 ↓
view<u8>
```

Không cần copy toàn bộ dữ liệu.

Nhưng capability phải gắn với lifetime của mapping.

---

# 45. `munmap` / release

Nếu:

```text id="ffi42"
view
 ↓
unmap
```

compiler phải phát hiện:

```text id="ffi43"
live capability
```

và reject safe code.

---

# 46. Foreign exceptions

C++/foreign exception không nên tự động trở thành Axiom panic.

Boundary cần:

```text id="ffi44"
NoUnwind
Catch
Terminate
ForeignUnwind
```

tùy ABI/platform.

---

# 47. Unwind boundary

Nếu Axiom:

```text id="ffi45"
panic=unwind
```

vẫn không được mặc định unwind xuyên foreign ABI nếu ABI không cho phép.

Foreign unwind → Axiom phải có explicit compatibility contract.

---

# 48. `extern "C"` không đồng nghĩa `noexcept`

C ABI không tự xác định foreign function có throw/unwind hay không.

Compiler phải có contract riêng nếu cần.

---

# 49. Error ABI

Axiom:

```text id="ffi46"
Result<T,E>
```

không tự động có C representation.

Có thể tạo wrapper:

```text id="ffi47"
struct ResultCode {
    value: ...
    error: i32
}
```

với `@repr(C)`.

---

# 50. Error mapping

Foreign:

```text
errno
HRESULT
NTSTATUS
POSIX error
```

có thể được wrapper chuyển thành:

```text id="ffi48"
Result<T, Error>
```

Đây là library abstraction, không phải compiler magic.

---

# 51. FFI effects

Foreign call mặc định có thể:

```text
Read
Write
IO
Foreign
ExternalState
```

Nếu contract chứng minh ít hơn:

```text id="ffi49"
EffectSummary
```

có thể được refine.

---

# 52. FFI aliasing

Foreign function:

```text
fn foo(a: *mut T, b: *mut T)
```

không được mặc định:

```text
NO_ALIAS
```

unless contract guarantees it.

Điều này bảo vệ optimizer khỏi giả định C API sai.

---

# 53. FFI + compiler optimization

Compiler có thể:

```text
inline
remove
reorder around
```

foreign call **chỉ trong phạm vi effect/ABI semantics cho phép**.

Ví dụ:

```text
volatile foreign access
```

không được tối ưu như ordinary load.

---

# 54. FFI + volatile

Hardware registers:

```text
volatile read
volatile write
```

phải giữ observable access.

```text
volatile ≠ atomic
volatile ≠ synchronization
```

như memory model đã frozen.

---

# 55. Dynamic loading

Axiom có thể hỗ trợ:

```text
load_library()
lookup_symbol()
```

nhưng đây là:

```text
System / OS library
```

không phải Core primitive.

Dynamic symbol:

```text
unknown at compile time
```

→ conservative optimization boundary.

---

# 56. Function symbol lookup

Dynamic loading có thể trả:

```text
raw function pointer
```

Wrapper phải chuyển thành callable với ABI đã biết.

Không được tự động coi:

```text
*const u8
```

là callable Axiom function.

---

# 57. ABI mismatch

Nếu:

```text
Axiom declaration
```

không khớp:

```text
foreign symbol ABI
```

thì behavior có thể trở thành invalid unsafe contract.

Tooling phải cảnh báo mạnh hoặc reject khi metadata cho phép phát hiện.

---

# 58. FFI metadata

`.axmeta` nên lưu:

```text
FFI {
    symbol
    ABI
    calling_convention
    parameter_layout
    return_layout
    representation
    ownership
    effects
    unwind
}
```

để package binary sử dụng được mà không cần source.

---

# 59. C header interoperability

Axiom không nên bắt programmer viết lại toàn bộ C header bằng tay.

Có thể có tool:

```text
axc bindgen header.h
```

hoặc tương đương.

Pipeline:

```text
C Header
 ↓
C Parser
 ↓
FFI Declaration
 ↓
Axiom declarations
 ↓
normal verification
```

Generated declaration vẫn phải được kiểm tra.

---

# 60. C header parser không thuộc Core compiler

Để giữ compiler nhỏ:

```text id="ffi50"
axc
```

có thể có optional:

```text
ffi tools
```

Compiler core chỉ hiểu canonical FFI declarations.

---

# 61. Reverse binding

Axiom cũng cần:

```text id="ffi51"
axc export --header
```

tạo C header từ:

```ax
@export("axiom_add", abi="C")
fn add(...)
```

Generator lấy ABI metadata trực tiếp từ compiler.

Không tự đoán layout.

---

# 62. FFI package boundary

Package:

```text id="ffi52"
windows
linux
vulkan
opengl
sqlite
...
```

có thể cung cấp safe wrapper.

Ứng dụng:

```text
app
 ↓
safe Axiom API
 ↓
FFI package
 ↓
foreign ABI
```

Do đó ứng dụng không cần trực tiếp xử lý raw pointer.

---

# 63. Safe wrapper architecture

Mẫu chuẩn:

```text id="ffi53"
┌─────────────────────┐
│ Safe Axiom API      │
├─────────────────────┤
│ Ownership Adapter   │
│ Capability Adapter  │
│ Error Adapter       │
│ Thread Adapter      │
├─────────────────────┤
│ FFI Boundary        │
├─────────────────────┤
│ Foreign API         │
└─────────────────────┘
```

---

# 64. FFI và mục tiêu “không third-party dependency”

Cần hiểu chính xác:

Axiom không phụ thuộc:

```text
GCC
Clang
LLVM
```

để **biên dịch ngôn ngữ ở trạng thái production cuối cùng**.

Nhưng Axiom hoàn toàn có thể link:

```text
Windows system DLL
Linux system library
GPU driver
native SDK
```

nếu chương trình yêu cầu.

Đó là **platform dependency**, không phải compiler dependency.

---

# 65. FFI và static linking

Nếu có static library:

```text
libfoo.a
foo.lib
```

Axiom linker có thể:

```text
extract required objects
 ↓
section GC
 ↓
LTO where supported
```

để tránh kéo toàn bộ library vào binary.

---

# 66. FFI và shared libraries

Nếu dynamic:

```text
foo.dll
libfoo.so
libfoo.dylib
```

thì binary có:

```text
IMPORT dependency
```

và linker phải giữ symbol/ABI contract phù hợp.

---

# 67. FFI không được phá ownership verifier

Ví dụ:

```text
Axiom owner
 ↓
foreign call
 ↓
foreign retains pointer
 ↓
Axiom owner destroyed
```

Nếu foreign contract cho phép retention mà compiler không biết:

```text
Escape = Unknown/ExternalEscape
```

và safe ownership không được phép tiếp tục giả định pointer đã hết hiệu lực.

---

# 68. FFI boundary là nơi duy nhất được phép “trust”

Nhưng trust phải có hình thức:

```text
Trusted FFI Contract
```

không phải:

```text
unsafe {
    compiler.ignore_everything();
}
```

Đây là điểm rất quan trọng để giữ kiến trúc verifier đã xây ở `BOOTSTRAP-135`.

---

# 69. FFI inspection

CLI:

```text
axc inspect ffi foo
axc inspect ffi foo --abi
axc inspect ffi foo --ownership
axc inspect ffi foo --effects
axc inspect ffi foo --symbols
axc inspect ffi foo --layout
```

Ví dụ:

```text
Function: create_buffer
ABI: C
Return: *mut Buffer
Ownership: foreign → caller
Nullability: nullable
Effects: Allocate | Foreign
Unwind: forbidden
```

---

# 70. Invariants

Đóng băng:

### `AFFI-20`
FFI is an explicit semantic boundary.

### `AFFI-21`
Axiom ABI, C ABI and System ABI are distinct.

### `AFFI-22`
Foreign declarations require explicit ABI identity.

### `AFFI-23`
Only FFI-safe representations may cross a declared C ABI boundary.

### `AFFI-24`
`@repr(C)` establishes a representation contract.

### `AFFI-25`
`@repr(C)` does not automatically make nested non-FFI-safe types safe.

### `AFFI-26`
Opaque foreign types do not expose unknown layout.

### `AFFI-27`
Foreign ownership must not be inferred from raw pointer representation.

### `AFFI-28`
Foreign allocation and Axiom allocation domains are distinct unless explicitly compatible.

### `AFFI-29`
Axiom strings are not implicitly C strings.

### `AFFI-30`
Nullability is explicit at FFI boundaries.

### `AFFI-31`
Raw pointers do not establish safe capability provenance.

### `AFFI-32`
Foreign calls with unknown effects are conservative.

### `AFFI-33`
Unknown foreign aliasing is never treated as `NO_ALIAS`.

### `AFFI-34`
Foreign contracts may refine compiler knowledge only when explicitly established.

### `AFFI-35`
Unsafe FFI does not disable type, ABI or established verifier checks.

### `AFFI-36`
Unsafe FFI may establish trusted machine-level preconditions.

### `AFFI-37`
Safe verification resumes after a valid FFI contract boundary.

### `AFFI-38`
Foreign callbacks require explicit lifetime/storage contracts when retained.

### `AFFI-39`
Foreign-thread callbacks require appropriate Send/Share semantics.

### `AFFI-40`
Foreign async operations require explicit async adapters.

### `AFFI-41`
Foreign unwind cannot cross an ABI boundary without an explicit compatible contract.

### `AFFI-42`
Axiom panic is not automatically equivalent to a foreign exception.

### `AFFI-43`
Variadic ABI behavior is target-specific and explicit.

### `AFFI-44`
C structs require compatible representation before crossing C ABI.

### `AFFI-45`
Axiom enums do not automatically equal C enums/unions.

### `AFFI-46`
Packed representations require unsafe/system handling.

### `AFFI-47`
Alignment requirements are part of FFI validity.

### `AFFI-48`
Foreign memory is an explicit external storage domain.

### `AFFI-49`
Foreign memory may become a safe capability only after its validity contract is established.

### `AFFI-50`
Foreign memory cannot be unmapped while dependent safe capabilities remain live.

### `AFFI-51`
Exported Axiom functions require explicit native ABI/export contracts.

### `AFFI-52`
Generic functions require concrete specialization before C ABI export.

### `AFFI-53`
Capturing closures are not implicitly C function pointers.

### `AFFI-54`
Noncapturing closures may decay to compatible function pointers.

### `AFFI-55`
Dynamic symbol lookup cannot infer callable ABI from raw address alone.

### `AFFI-56`
FFI metadata is part of ABI/build metadata.

### `AFFI-57`
Generated FFI declarations re-enter ordinary compiler verification.

### `AFFI-58`
FFI wrappers may provide safe ownership/capability abstractions over unsafe foreign APIs.

### `AFFI-59`
System dependencies remain distinct from compiler dependencies.

### `AFFI-60`
FFI cannot weaken Axiom semantic verification.

### `AFFI-61`
FFI contracts participate in Effect, Alias, Escape and ABI analysis.

### `AFFI-62`
Unknown foreign behavior may reduce optimization freedom but cannot alter semantics.

### `AFFI-63`
FFI inspection must expose ABI and ownership contracts.

### `AFFI-64`
The final native compiler must be capable of consuming its own canonical FFI representation without requiring a third-party compiler.

---

# Một quyết định kiến trúc rất quan trọng đã được chốt

Axiom bây giờ có thể có một mô hình cực kỳ rõ:

```text
                    AXIOM SAFE WORLD
                           │
              ownership / capability / types
                           │
                           ↓
                  ┌─────────────────┐
                  │  FFI CONTRACT   │
                  └────────┬────────┘
                           │
                     unsafe boundary
                           │
                           ↓
                  FOREIGN / SYSTEM
```

Điều này giải quyết một mâu thuẫn trước đây:

> **Làm sao vừa bỏ pointer/reference bureaucracy khỏi lập trình viên, vừa có khả năng làm systems programming và gọi OS/native API?**

Câu trả lời là:

**Không loại bỏ pointer khỏi compiler. Chỉ loại bỏ việc programmer phải dùng pointer như công cụ quản lý bộ nhớ thông thường.**

Pointer tồn tại mạnh ở:

```text
unsafe
FFI
OS
driver
hardware
allocator
ABI
```

Trong application code, programmer chủ yếu dùng:

```text
value
owner
view
mut_view
handle
```

---

# BOOTSTRAP-155 — OS Abstraction, Syscall Layer, Platform APIs & Freestanding Environment

Bước tiếp theo nên đi xuống **thấp hơn FFI một tầng**: xác định Axiom giao tiếp với OS như thế nào.

Mục tiêu là không biến:

```text
Windows
Linux
macOS
Android
iOS
WASM
Embedded
Kernel
```

thành một đống API đặc thù nằm trong Core.

Kiến trúc dự kiến:

```text
                 Axiom Application
                         ↓
                  std::os / std
                         ↓
                 Platform Contract
                         ↓
              ┌──────────┼──────────┐
              ↓          ↓          ↓
          Windows      Linux      Darwin
              ↓          ↓          ↓
          Native ABI / Syscall / Kernel
```

Trong 155 sẽ chốt đặc biệt:

- OS abstraction có nên giống POSIX hay không;
- syscall trực tiếp;
- Windows NT API;
- Linux syscall;
- macOS/iOS Mach-O + Darwin;
- Android;
- WASM host environment;
- filesystem;
- process;
- threads;
- virtual memory;
- signals/faults;
- handles;
- sockets;
- clocks;
- environment;
- TLS;
- dynamic libraries;
- GUI/platform handles;
- kernel/freestanding;
- embedded;
- `no_std` tương đương nhưng theo triết lý Axiom;
- và quan trọng nhất: **Axiom phải có thể chạy mà không cần libc/POSIX runtime.**