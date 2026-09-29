# BOOTSTRAP-077 — Axiom FFI / System ABI Deep Model & OS Interoperability

**Trạng thái: FROZEN**

Đây là bước tiếp theo sau mô hình Resource/IO. Mục tiêu lần này là làm rõ **ranh giới giữa Axiom và thế giới bên ngoài**: C ABI, OS API, syscall, shared library, callback, opaque handle, union/bitfield, C string, TLS, async callback…

Điểm quan trọng: **FFI không được làm bẩn semantic core của Axiom.** Axiom vẫn giữ ownership/capability/type safety ở phía trong; chỉ tại boundary mới phải mô tả chính xác những gì hệ thống bên ngoài thực sự làm.

---

# 1. Nguyên tắc nền tảng

Axiom có ba tầng ABI:

```text
                 Axiom program
                      │
               ┌──────▼──────┐
               │   Axiom ABI │
               └──────┬──────┘
                      │
             explicit FFI boundary
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
     C ABI        System ABI      GPU ABI
        │             │             │
        ▼             ▼             ▼
     libc/API       OS/kernel     Driver/runtime
```

Không có chuyện:

```text
Axiom type → tự đoán C type
Axiom String → tự động char*
Axiom Vec → tự động C array
Handle → tự động ownership
callback → tự động lifetime-safe
```

Mọi thứ phải có **representation contract**.

---

# 2. Axiom ABI ≠ C ABI

Axiom ABI tối ưu cho Axiom.

Ví dụ:

```ax
fn process(data: view<u8>) -> Result<usize, Error>
```

không có nghĩa ABI bên ngoài sẽ thấy:

```c
Result process(...);
```

Axiom compiler có quyền lower thành representation tối ưu.

Trong khi:

```ax
extern "C" fn process(data: CBytes) -> usize
```

là một **ABI contract**.

Do đó:

```text
Semantic Type
      ↓
Representation Contract
      ↓
ABI Contract
      ↓
Machine ABI
```

không được bỏ qua các tầng.

---

# 3. C ABI là interoperability ABI đầu tiên

Axiom nên coi C ABI là **foreign ABI chuẩn đầu tiên**, bởi nó là điểm giao của:

- C
- C++
- Rust
- Swift
- Objective-C
- OS APIs
- GPU libraries
- embedded APIs
- native libraries

Nhưng Axiom **không cần trở thành C compiler**.

Nó chỉ cần phát ra/nhận đúng:

```text
calling convention
argument layout
return layout
struct layout
alignment
symbol
relocation
stack convention
register convention
TLS
unwind contract
```

---

# 4. C-compatible types

Chỉ một tập type được mặc định hoặc explicit xác nhận là FFI-safe.

Ví dụ:

```ax
@repr(C)
struct Point {
    x: f32
    y: f32
}
```

Có thể dùng với:

```ax
extern "C" fn draw_point(p: Point)
```

Trong khi:

```ax
struct Point {
    x: f32
    y: f32
}
```

không mặc định có C layout.

---

# 5. Primitive mapping

Mapping cơ bản:

| Axiom | C ABI tương ứng |
|---|---|
| `i8` | `int8_t` |
| `u8` | `uint8_t` |
| `i16` | `int16_t` |
| `u16` | `uint16_t` |
| `i32` | `int32_t` |
| `u32` | `uint32_t` |
| `i64` | `int64_t` |
| `u64` | `uint64_t` |
| `f32` | `float` |
| `f64` | `double` |
| `bool` | không tự động coi là C `bool` |
| `usize` | target-sized unsigned |
| `isize` | target-sized signed |

Đặc biệt:

> `bool` của Axiom không được tự động đồng nhất với mọi ABI boolean của C.

FFI phải xác định representation.

---

# 6. C enum

C enum có vấn đề vì ABI/compiler khác nhau có thể lựa chọn underlying representation khác nhau.

Do đó:

```ax
@repr(C)
enum Color {
    Red
    Green
    Blue
}
```

chỉ có ý nghĩa khi Axiom định nghĩa rõ ABI contract tương ứng.

Đối với interoperability cần representation rõ ràng hơn:

```ax
@repr(u32)
enum Color {
    Red = 0
    Green = 1
    Blue = 2
}
```

Đây là representation contract, không chỉ là semantic enum.

---

# 7. Union

C union cần được hỗ trợ ở system/FFI layer.

Ví dụ:

```ax
@repr(C)
union Value {
    i: i32
    f: f32
}
```

Nhưng:

```text
union ≠ safe tagged union
```

Union không tự biết field nào đang active.

Do đó đọc member không có proof phù hợp phải thuộc unsafe/system semantics.

Axiom `enum` vẫn là lựa chọn safe mặc định.

---

# 8. Bitfield

Bitfield là một trong những thứ **không nên đưa vào Core type system**.

Ví dụ C:

```c
struct Flags {
    unsigned a : 1;
    unsigned b : 3;
    unsigned c : 4;
};
```

layout bitfield phụ thuộc ABI/compiler.

Axiom nên xử lý bằng:

```ax
@repr(C)
struct Flags {
    raw: u32
}
```

và cung cấp:

```ax
fn a(self) -> bool
fn set_a(self: mut_view<Self>, value: bool)
```

hoặc intrinsic/system bit operations.

Nếu cần import C bitfield thật sự, đó là:

```text
FFI representation extension
```

không phải Core semantic type.

---

# 9. C strings

Không có implicit:

```text
String → char*
```

Axiom phân biệt:

```text
String
Str
Bytes
CStr
CString
```

Ví dụ:

```ax
extern "C" fn puts(s: *const u8) -> i32
```

wrapper safe:

```ax
fn puts(text: Str) -> Result<(), Error>
```

wrapper chịu trách nhiệm:

```text
UTF-8 validity
NUL termination
lifetime
pointer validity
foreign ownership
```

---

# 10. `CStr` và `CString`

Nên có hai abstraction rõ ràng:

```text
CStr
    borrowed NUL-terminated C string

CString
    owned NUL-terminated C string
```

Không coi chúng là `String`.

Điều này giải quyết đồng thời:

- NUL byte
- lifetime
- ownership
- encoding
- foreign ABI.

---

# 11. C array / slice

C không có slice semantic.

Một API:

```c
void process(const uint8_t* data, size_t len);
```

không nên map trực tiếp thành:

```ax
extern "C" fn process(data: view<u8>)
```

trừ khi compiler định nghĩa một ABI lowering cụ thể cho C.

Thay vào đó:

```ax
@repr(C)
struct CBytes {
    data: *const u8
    len: usize
}
```

hoặc FFI declaration:

```ax
extern "C" fn process(data: *const u8, len: usize)
```

Safe wrapper:

```ax
fn process(data: view<u8>) -> Result<(), Error>
```

Như vậy:

```text
Axiom view
    ↓ wrapper
C pointer + length
```

rất rõ ràng.

---

# 12. Raw pointer tại FFI boundary

Raw pointer:

```ax
*const T
*mut T
```

chỉ là machine-level value.

Nó không nói:

- ai sở hữu?
- sống bao lâu?
- có NULL không?
- có đủ N phần tử không?
- có alias không?
- thread nào được dùng?

Do đó FFI contract phải bổ sung những thông tin này.

---

# 13. Foreign ownership contract

Mỗi foreign pointer/resource phải thuộc một ownership class:

```text
Borrowed
OwnedByAxiom
OwnedByForeign
Shared
HandleOnly
```

Ví dụ:

```ax
extern "C" fn malloc(size: usize) -> *mut u8
extern "C" fn free(ptr: *mut u8)
```

Axiom không được giả định:

```text
malloc → Box<u8>
```

vì allocator domain có thể khác.

Thay vào đó:

```text
ForeignAllocation
```

có explicit release:

```ax
foreign_free(ptr)
```

---

# 14. Allocator domain

Đây là một invariant rất quan trọng:

```text
Axiom allocator ≠ foreign allocator
```

Không được:

```text
axiom_alloc → C free()
C malloc → axiom deallocation
```

trừ khi ABI contract xác nhận cùng allocation domain.

Điều này đặc biệt quan trọng với:

- Windows DLL
- CRT
- COM
- Objective-C
- Swift
- plugin systems
- shared libraries.

---

# 15. Opaque handles

Rất nhiều OS API không trả object thực sự mà trả handle:

```text
HANDLE
fd
Mach port
HWND
HINSTANCE
pthread_t
GPU resource handle
```

Axiom nên dùng:

```ax
struct Handle<T> { ... }
```

nhưng phải nhớ:

> `Handle<T>` là logical identity, không phải ownership tự động.

Ví dụ:

```ax
struct FileHandle
```

có thể chỉ là:

```text
OS integer/pointer token
```

Ownership được xác định bởi wrapper:

```ax
File
```

chứ không phải bởi raw handle.

---

# 16. Borrowed handle

Có thể có:

```ax
struct BorrowedHandle<T>
```

nhưng không nhất thiết phải là Core primitive.

Thông thường library/system layer có thể biểu diễn:

```text
Handle<T>
Owned<T>
Borrowed<T>
```

với capability verification.

Mục tiêu là tránh biến mọi OS handle thành một hệ thống reference phức tạp.

---

# 17. Windows API

Windows API nên được xây ở System Library:

```text
axiom.windows
    kernel32
    user32
    advapi32
    ntdll
    ws2_32
    ...
```

Ví dụ:

```ax
extern "system" fn CreateFileW(...)
```

Không nên bắt programmer trực tiếp thao tác raw API trong application code.

System library cung cấp wrapper:

```ax
File.open(...)
```

Tầng dưới:

```text
File
 ↓
Windows implementation
 ↓
CreateFileW
```

---

# 18. POSIX

POSIX cũng là system library:

```text
axiom.posix
```

với:

```text
open
read
write
close
mmap
poll
epoll
pthread
socket
...
```

Không đưa POSIX vào language core.

---

# 19. Linux syscall

Syscall cần một tầng thấp hơn POSIX:

```text
Axiom
 ↓
Linux System API
 ↓
Linux syscall ABI
 ↓
kernel
```

Ví dụ:

```ax
syscall.read(...)
```

là system-level.

Nó có thể bypass libc hoàn toàn.

Điều này phù hợp mục tiêu:

> Axiom có thể tạo native executable không cần C runtime.

---

# 20. libc không phải dependency bắt buộc

Một chương trình:

```ax
fn main() {
    ...
}
```

không nhất thiết phải link:

```text
libc
libstdc++
libgcc
```

Nếu program chỉ cần syscall/freestanding functionality:

```text
Axiom startup
→ native code
→ syscall
```

là đủ.

Hosted runtime là lựa chọn.

---

# 21. macOS / Mach

macOS có nhiều tầng:

```text
Axiom
 ↓
Apple System Framework
 ↓
POSIX / Darwin
 ↓
Mach / kernel interface
```

Axiom nên expose:

```text
axiom.macos
axiom.darwin
axiom.mach
```

ở system library.

Không đưa Mach ports vào Core.

---

# 22. iOS

iOS là target ABI riêng dù dùng Mach-O/ARM64.

Cần phân biệt:

```text
target = iOS
ABI = Apple platform ABI
binary = Mach-O
```

và system framework imports.

Build system phải hiểu:

```text
architecture
deployment target
SDK
framework
linker flags
code signing
entitlements
```

nhưng signing/package không phải compiler semantic.

---

# 23. Android

Android tương tự:

```text
Axiom
 ↓
Android system layer
 ↓
Bionic / NDK ABI
 ↓
Linux kernel
```

Axiom cần hỗ trợ:

```text
ELF
AArch64
ARM
x86_64
JNI/NDK interoperability
```

nhưng JNI chỉ là system/application library.

---

# 24. WASM

WASM không nên giả lập như ELF.

Mô hình:

```text
Axiom
 ↓
WASM lowering
 ↓
WASM module
 ↓
imports / exports
 ↓
host
```

Ví dụ:

```ax
extern "wasm" fn host_log(ptr: i32, len: i32)
```

hoặc typed host binding do runtime/tooling tạo.

WASM memory:

```text
linear memory
```

là một storage domain riêng.

Không tự động đồng nhất với native pointer.

---

# 25. Callback

Callback là một trong những nơi dễ tạo dangling reference nhất.

C:

```c
register_callback(callback, context);
```

Axiom phải biết:

```text
callback lifetime
context lifetime
who owns callback
who owns context
when callback may execute
thread/domain
whether callback may outlive registration
```

Không được đơn giản hóa thành:

```ax
register_callback(|| ...)
```

rồi giả định compiler tự giải quyết mọi thứ.

---

# 26. Callback adapter

Capturing closure:

```ax
|event| handle(event)
```

không tự động là C function pointer.

Compiler có thể tạo:

```text
extern "C" callback trampoline
        +
context pointer
```

nhưng lifetime của context phải được xác định.

Conceptually:

```text
C callback
    ↓
function pointer
context pointer
    ↓
Axiom adapter
    ↓
closure
```

---

# 27. Callback lifetime contract

Các loại callback:

```text
CALLS_DURING_FUNCTION
CALLS_UNTIL_UNREGISTER
CALLS_AFTER_RETURN
CALLS_FOREVER
UNKNOWN
```

Trong safe wrapper, `UNKNOWN` không được phép tạo một borrowed closure có lifetime ngắn.

Nếu callback có thể tồn tại lâu:

```text
owned callback/context
```

hoặc explicit shared ownership.

---

# 28. Function pointers

Phân biệt:

```text
fn(...) -> T
```

với:

```text
closure
```

và:

```text
extern "C" fn(...) -> T
```

ABI là một phần của function type khi đi qua FFI.

Ví dụ:

```ax
type CCallback = extern "C" fn(*const u8, usize) -> i32
```

---

# 29. Variadic functions

C:

```c
printf(...)
```

không nên trở thành tính năng generic của Axiom.

Variadic chỉ:

```text
FFI/System
```

và phải khai báo explicit:

```ax
extern "C" fn printf(format: *const u8, ...) -> i32
```

Type checking của phần variadic bị giới hạn bởi C ABI.

Safe wrappers nên tránh variadic khi có thể.

---

# 30. Foreign exceptions

Không cho phép:

```text
C++ exception
      ↓
Axiom panic
```

tự động.

Cũng không:

```text
Axiom panic
      ↓
C++ exception
```

Axiom FFI boundary mặc định là:

```text
panic does not cross ABI boundary
```

Nếu cần interoperability đặc biệt, system adapter phải định nghĩa rõ unwind contract.

---

# 31. Thread-local storage

Axiom có:

```ax
@tls
static ...
```

nhưng ABI thực tế target-specific.

Các target có:

```text
ELF TLS
PE TLS
Mach-O TLS
WASM TLS emulation/runtime
```

Compiler/object writer/linker xử lý.

TLS identity:

```text
one logical variable
×
one execution thread
```

không phải shared memory.

---

# 32. Foreign synchronization

Một FFI call:

```ax
extern "C" fn foo(...)
```

**không mặc định có synchronization semantics**.

Compiler không được giả định:

```text
foreign call = full memory fence
```

Nếu API thực sự synchronization:

```text
FFI contract
```

phải khai báo hoặc wrapper cung cấp semantic synchronization.

---

# 33. Foreign aliasing

Đây là điểm rất quan trọng cho optimizer.

Ví dụ:

```ax
extern "C" fn foo(a: *mut i32, b: *mut i32)
```

Axiom không được giả định:

```text
a != b
```

Nếu C function contract không nói rõ.

Mặc định:

```text
foreign aliasing = UNKNOWN
```

→ optimizer phải bảo thủ.

Nếu API contract chứng minh non-alias:

```text
trusted noalias contract
```

thì mới được dùng cho optimization.

---

# 34. Foreign memory mutation

Foreign function có thể:

```text
READ
WRITE
ALLOCATE
DEALLOCATE
IO
ATOMIC
SYNCHRONIZE
UNKNOWN
```

Compiler cần FFI effect metadata.

Không cần expose thành effect system cho programmer.

Ví dụ compiler metadata:

```text
ForeignEffect {
    reads: ...
    writes: ...
    synchronization: ...
    ownership: ...
}
```

---

# 35. System calls

Syscall có semantics khác function call thông thường:

```text
side effects
kernel boundary
register clobbers
memory effects
error convention
```

Do đó:

```ax
@syscall
fn read(...)
```

là system declaration.

Compiler backend biết syscall ABI:

```text
x86-64 Linux
ARM64 Linux
...
```

---

# 36. Shared libraries

Axiom phải hỗ trợ:

```text
static library
shared library
dynamic loading
symbol lookup
```

Ví dụ:

```text
libfoo.so
foo.dll
libfoo.dylib
```

Nhưng:

```ax
Symbol<T>
```

không tự chứng minh symbol runtime có đúng type `T`.

Dynamic lookup là boundary không thể verify hoàn toàn.

---

# 37. Dynamic symbol loading

Ví dụ:

```ax
let symbol = library.get("foo")
```

không đủ để kết luận:

```text
foo : fn(i32) -> i32
```

Safe API nên yêu cầu:

```text
explicit ABI contract
```

hoặc dynamic validation.

Nếu type chỉ là programmer assertion:

```ax
unsafe {
    symbol.cast<extern "C" fn(i32) -> i32>()
}
```

sau boundary đó verifier tiếp tục hoạt động dựa trên contract.

---

# 38. Struct layout tại FFI

Quy tắc:

```text
Default struct
    → Axiom controlled

@repr(C)
    → C controlled contract

@repr(transparent)
    → underlying representation contract

@repr(packed)
    → unsafe

@repr(align(N))
    → alignment contract
```

Không có chuyện `pub struct` tự trở thành ABI stable.

---

# 39. Nested FFI types

Nếu:

```ax
@repr(C)
struct A {
    p: B
}
```

thì `B` cũng phải có representation contract tương thích.

FFI safety phải được kiểm tra **đệ quy**.

Không thể chỉ kiểm tra top-level struct.

---

# 40. Recursive opaque objects

C thường dùng:

```c
typedef struct Foo Foo;
```

Axiom nên hỗ trợ opaque foreign type:

```ax
extern type Foo
```

hoặc tương đương system-level declaration.

Programmer không biết layout:

```text
size = unknown
fields = inaccessible
representation = foreign
```

Chỉ được dùng qua pointer/handle theo contract.

---

# 41. `void*`

Không map:

```text
void* → Any
```

Trong Axiom.

Nó nên tương đương một opaque raw pointer:

```text
*mut opaque
```

Việc cast sang `T` là unsafe nếu không có contract.

Đây là cách tránh biến `void*` thành lỗ hổng type system.

---

# 42. Foreign opaque object ownership

Ví dụ:

```c
Foo* foo_create();
void foo_destroy(Foo*);
```

Axiom wrapper:

```ax
struct Foo {
    raw: *mut ForeignFoo
}
```

với:

```text
Move
Drop → foo_destroy
```

Nhưng `Foo` wrapper **không cần object header**.

Compiler có thể biến wrapper thành một pointer machine value.

---

# 43. Foreign reference counting

Nếu foreign API:

```text
retain()
release()
```

thì Axiom không tự biến nó thành `Arc<T>`.

Nó là một resource ownership model riêng.

Có thể tạo:

```text
ForeignShared<T>
```

ở library layer.

---

# 44. Objective-C / Swift

Không cần đưa Objective-C object model hoặc Swift ARC vào Core.

System libraries có thể cung cấp adapter:

```text
Axiom ownership
      ↓
foreign ownership contract
      ↓
ARC/ObjC runtime
```

Tương tự với COM:

```text
IUnknown AddRef/Release
```

có thể được wrapper thành explicit resource semantics.

---

# 45. GPU driver API

GPU driver handles cũng là FFI resources:

```text
VkDevice
VkBuffer
MTLBuffer
CUdeviceptr
...
```

Chúng không tự trở thành:

```text
DeviceBuffer<T>
```

Safe GPU library phải xây ownership/storage-domain contract.

---

# 46. FFI và `view`

Đây là quy tắc rất quan trọng:

```text
view<T>
```

là Axiom capability.

Nó **không phải C ABI type**.

Ví dụ wrapper:

```ax
fn native_read(buffer: mut_view<u8>) -> Result<usize, Error> {
    extern_read(buffer.ptr(), buffer.len())
}
```

nhưng `.ptr()` chỉ được dùng ở unsafe/system boundary.

Semantic pipeline:

```text
Axiom capability
     ↓
verified region
     ↓
raw pointer + length
     ↓
foreign call
```

---

# 47. FFI và Drop

Không để foreign cleanup:

```text
Drop → Result
```

Ví dụ:

```ax
fn close(self) -> Result<(), Error>
```

được phép.

Sau đó:

```text
Drop
```

chỉ là fallback cleanup.

Nếu foreign cleanup thất bại:

```text
record/log/abort policy
```

theo resource policy, không ném recoverable error ngược vào chương trình.

---

# 48. FFI và async

Foreign callback async không được tự động biến thành Axiom Future.

Có ba dạng:

```text
callback
poll
opaque async handle
```

Axiom async adapter:

```text
foreign operation
        ↓
owned state
        ↓
callback / poll
        ↓
Future
```

Future phải giữ tất cả resource/buffer cần thiết sống đến completion.

---

# 49. OS async APIs

Ví dụ:

```text
Linux io_uring
Windows IOCP
Apple dispatch/kqueue
WASM host async
```

không cần đưa vào Core.

Chúng là runtime/system libraries.

Nhưng compiler semantic model phải đủ để chúng có thể xây được:

```text
Future
ownership
capability
in-flight lifetime
Send
cancellation
```

---

# 50. Cancellation

FFI không được giả định:

```text
drop(Future) = cancel()
```

Foreign API phải có contract riêng:

```text
cancelable
non-cancelable
cancel-via-handle
completion-required
```

Đặc biệt OS I/O có thể tiếp tục sau khi Future bị drop.

Resource lifetime phải phản ánh điều đó.

---

# 51. Error mapping

Axiom không nên flatten tất cả thành:

```ax
Error
```

quá sớm.

Ví dụ system error có thể giữ:

```text
domain
code
native code
operation
```

Ví dụ conceptually:

```ax
struct OsError {
    code: i32
    domain: OsErrorDomain
}
```

Wrapper cấp cao có thể chuyển thành domain-specific error.

---

# 52. `errno`

Không coi `errno` là global Axiom variable bình thường.

Đó là foreign/TLS state.

System library có thể:

```ax
errno()
```

hoặc trực tiếp map error-return convention.

Compiler không được tự giả định mọi foreign call đều cập nhật errno.

---

# 53. ABI và `setjmp/longjmp`

Đây là một edge case quan trọng.

`longjmp` phá vỡ control-flow assumptions thông thường.

Không cho safe Core sử dụng trực tiếp.

Nếu hỗ trợ:

```text
unsafe/system FFI
```

và compiler phải biết boundary để không tạo code có semantic assumptions không hợp lệ.

---

# 54. ABI và signal/interrupt

Signal handlers/interrupt handlers không phải ordinary functions.

Có thể:

```ax
@interrupt
fn handler(...)
```

nhưng đây là System ABI.

Các restriction như:

```text
allowed operations
stack assumptions
register preservation
reentrancy
```

do target/system layer định nghĩa.

---

# 55. ABI và `@naked`

```ax
@naked
fn entry(...)
```

cho phép machine-level function không có prologue/epilogue thông thường.

Đây là:

```text
unsafe + system
```

Không thuộc ordinary application programming model.

---

# 56. FFI safety checker

Compiler cần một pass:

```text
FFI Contract Verification
```

kiểm tra:

```text
ABI
representation
alignment
size
field layout
pointer usage
ownership
Drop
calling convention
variadic rules
callback lifetime
unwind
Send/Share
synchronization
allocator domain
```

Ví dụ:

```text
extern "C" fn foo(String)
```

→ compile error.

Không cần programmer tự nhớ tất cả.

---

# 57. FFI boundary trong compiler pipeline

Pipeline được hoàn thiện thành:

```text
Typed HIR
    ↓
Ownership / Capability Verification
    ↓
Semantic Optimization
    ↓
FFI Contract Verification
    ↓
Representation/Layout
    ↓
ABI Lowering
    ↓
LIR
    ↓
Machine IR
```

Quan trọng:

> FFI verification diễn ra **sau semantic verification nhưng trước ABI lowering**.

---

# 58. Unsafe boundary

Mô hình chuẩn:

```text
Safe Axiom
    ↓
unsafe FFI/system boundary
    ↓
trusted precondition
    ↓
Safe Axiom
```

Không phải:

```text
unsafe
   ↓
compiler stops checking
```

Ví dụ:

```ax
unsafe {
    let p = foreign_get_buffer()
    let v = assume_view(p, len)
}
```

Sau đó `v` vẫn bị kiểm tra:

- lifetime
- alias
- mutation
- Send
- await
- Drop
- storage domain.

---

# 59. FFI contracts có thể là compiler metadata

Không cần thêm effect syntax phức tạp vào ngôn ngữ.

Compiler có thể lưu:

```text
FfiContract {
    abi
    calling_convention
    arg_representation
    return_representation
    ownership
    reads
    writes
    synchronization
    may_panic
    may_unwind
    callback_lifetime
    allocation_domain
}
```

Đây là **compiler semantic metadata**, không phải một ngôn ngữ phụ.

---

# 60. FFI wrapper architecture

Một OS API nên có ba tầng:

```text
┌──────────────────────────────┐
│ High-level safe API          │
│ File, Socket, Process, etc.  │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Safe platform adapter        │
│ ownership + Result + views   │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Raw FFI/System declarations  │
│ pointers + ABI + handles     │
└──────────────┬───────────────┘
               ↓
        OS / foreign world
```

Application programmer thường chỉ cần tầng đầu.

---

# 61. Không tạo “FFI language”

Đây là quyết định quan trọng.

Không tạo:

```text
C-like mini language
ABI DSL
ownership DSL
callback DSL
```

cho FFI.

Axiom declaration + attributes + explicit system types là đủ.

Ví dụ:

```ax
extern "C" fn foo(
    ptr: *mut u8,
    len: usize
) -> i32
```

và:

```ax
@repr(C)
struct Foo {
    ...
}
```

---

# 62. ABI compatibility ≠ semantic compatibility

Hai type có thể:

```text
same size
same alignment
same registers
```

nhưng vẫn không cùng semantic type.

Ví dụ:

```ax
struct UserId(u64)
struct FileDescriptor(u64)
```

có thể đều là 64-bit.

Nhưng không được:

```text
UserId → FileDescriptor
```

chỉ vì ABI giống nhau.

---

# 63. Representation compatibility

Ngược lại:

```ax
struct UserId(u64)
```

với:

```ax
@repr(transparent)
struct UserId(u64)
```

có thể có ABI compatibility với `u64` **nếu contract yêu cầu**.

Đây là lý do `@repr(transparent)` tồn tại.

---

# 64. FFI generic

Không cho:

```ax
extern "C" fn foo<T>(x: T)
```

mà không specialize.

Compiler phải materialize:

```text
foo<i32>
foo<f64>
foo<MyType>
```

và kiểm tra từng specialization có FFI-safe representation.

---

# 65. Trait object / closure / Future qua FFI

Mặc định:

```text
dyn Trait       ❌
capturing closure ❌
Future           ❌
Arc<T>           ❌
Mutex<T>         ❌
Vec<T>           ❌
String           ❌
```

không FFI-safe.

Muốn export phải có explicit C-facing wrapper.

Ví dụ:

```text
opaque handle + C functions
```

là cách ưu tiên.

---

# 66. Export API

Phân biệt:

```text
pub
```

và:

```text
@export("foo")
```

`pub` = source-level visibility.

`@export` = native symbol contract.

Ví dụ:

```ax
@export("axiom_add")
extern "C" fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

---

# 67. Import API

Foreign symbol cũng cần explicit:

```ax
extern "C" {
    fn foo(...)
}
```

Compiler tạo foreign declaration.

Linker/build system chịu trách nhiệm:

```text
library
symbol
search path
framework
import library
weak linkage
delay loading
```

---

# 68. Weak symbols

Axiom object/linker model cần hiểu:

```text
strong
weak
local
global
hidden
default
```

nhưng weak semantics không trở thành type-system feature.

---

# 69. Symbol versioning

Linux có:

```text
symbol@VERSION
```

và Windows/macOS có cơ chế tương ứng khác.

Đây là linker/platform feature.

Axiom package/build metadata có thể giữ:

```text
foreign library identity
symbol
version constraint
ABI
```

---

# 70. ABI versioning

Không nên hứa:

```text
Axiom ABI stable forever
```

ngay v1.

Chiến lược:

```text
C ABI → stable interoperability
Axiom ABI → versioned and initially compiler-version scoped
```

Sau khi language ABI đủ trưởng thành mới freeze stable Axiom ABI.

---

# 71. FFI và incremental compilation

FFI contract phải tham gia semantic fingerprint.

Nếu thay:

```ax
@repr(C)
struct Foo
```

thành layout khác:

```text
ABI fingerprint changes
```

→ dependent native code phải rebuild.

Tương tự:

```text
calling convention
export name
field layout
alignment
enum representation
```

---

# 72. FFI và package dependency

Package manifest cần biểu diễn native dependency:

```text
system library
shared library
static library
framework
SDK
```

Ví dụ conceptually:

```text
native dependency:
    name = user32
    platform = windows
```

Build system mới quyết định cách resolve.

Compiler không tự tải Internet.

---

# 73. Cross compilation

Một FFI declaration phải được kiểm tra theo **target**, không theo host.

Ví dụ compile:

```text
Windows host
→ Linux target
```

thì:

```text
sizeof(long)
calling convention
struct layout
syscall ABI
library names
```

phải theo Linux target.

Comptime host/target cũng phải phân biệt.

---

# 74. ABI matrix

Axiom compiler nên có target ABI database:

```text
Target
 ├─ Architecture
 ├─ Object format
 ├─ Data layout
 ├─ Calling conventions
 ├─ C ABI
 ├─ System ABI
 ├─ TLS
 ├─ unwind
 ├─ alignment
 └─ relocation model
```

Backend sử dụng database này.

---

# 75. Native platform layer

Kiến trúc thư viện cuối cùng:

```text
axiom.core
axiom.std
axiom.system
    ├── linux
    ├── windows
    ├── macos
    ├── ios
    ├── android
    ├── wasm
    └── gpu
```

Không phải compiler hard-code toàn bộ OS API.

Compiler chỉ cần biết:

```text
ABI mechanics
intrinsics
object format
target semantics
```

---

# 76. ABI / System / FFI separation

Ba khái niệm:

```text
ABI
    cách machine gọi function/data

FFI
    semantic boundary giữa Axiom và foreign code

System API
    API cụ thể của OS/platform
```

Ví dụ:

```text
C ABI = ABI
CreateFileW = System API
Axiom File = FFI-backed safe abstraction
```

---

# 77. FFI ownership graph

Compiler có thể biểu diễn:

```text
Axiom owner
   │
   └── foreign resource
          │
          ├── borrowed capabilities
          ├── callback
          └── in-flight operation
```

Drop/close chỉ được phép khi dependency graph cho phép.

Điều này kết nối trực tiếp với AIO-100 và AVERIFY.

---

# 78. Foreign callbacks + Send/Share

Nếu foreign API gọi callback từ worker thread:

```text
callback
   ↓
execution-domain transfer
```

thì closure/context phải thỏa:

```text
Send
```

Nếu callback đồng thời:

```text
Share
```

và synchronization contract.

Không được coi callback là ordinary function call chỉ vì ABI là function pointer.

---

# 79. Foreign thread ownership

Nếu foreign library tự tạo thread:

```text
foreign thread
```

Axiom không tự coi đó là:

```text
Axiom Thread
```

Nhưng callback crossing boundary phải được kiểm tra theo execution-domain semantics.

Đây là lý do `Send/Share` phải là semantic properties chứ không phụ thuộc implementation của Thread.

---

# 80. Final frozen rules

## FFI invariants — `AFFI2-20..100`

**AFFI2-20** — Axiom ABI and foreign ABI are distinct.

**AFFI2-21** — C ABI is the primary interoperability ABI.

**AFFI2-22** — Foreign ABI requires explicit declaration.

**AFFI2-23** — Representation contract precedes ABI lowering.

**AFFI2-24** — Default Axiom struct layout is not C layout.

**AFFI2-25** — `@repr(C)` establishes C representation contract.

**AFFI2-26** — `@repr(transparent)` establishes transparent representation contract.

**AFFI2-27** — `@repr(packed)` is unsafe/system-level.

**AFFI2-28** — FFI-safe types are explicitly constrained.

**AFFI2-29** — Axiom `String` is not implicitly a C string.

**AFFI2-30** — Axiom `view<T>` is not automatically a C slice.

**AFFI2-31** — Raw pointers do not imply ownership.

**AFFI2-32** — Raw pointers do not imply safe capability.

**AFFI2-33** — Foreign ownership must be explicit.

**AFFI2-34** — Foreign allocation domains must not be guessed.

**AFFI2-35** — Axiom allocation must not be released by foreign allocator without contract.

**AFFI2-36** — Foreign allocation must not be released by Axiom allocator without contract.

**AFFI2-37** — Opaque foreign types preserve abstraction boundaries.

**AFFI2-38** — `void*` does not become `Any`.

**AFFI2-39** — C unions are unsafe/system representations unless wrapped safely.

**AFFI2-40** — Bitfields are not Core semantic types.

**AFFI2-41** — C enum representation requires explicit ABI semantics.

**AFFI2-42** — Function pointer ABI is part of foreign function type.

**AFFI2-43** — Capturing closures are not automatically foreign function pointers.

**AFFI2-44** — Callback context lifetime must be explicit.

**AFFI2-45** — Callback execution domain must be respected.

**AFFI2-46** — Callback Send requirements must be verified.

**AFFI2-47** — Callback Share requirements must be verified.

**AFFI2-48** — Foreign callbacks do not automatically become Futures.

**AFFI2-49** — Foreign async completion retains required resources.

**AFFI2-50** — Dropping a foreign Future does not imply cancellation.

**AFFI2-51** — Variadic APIs are FFI/system-only.

**AFFI2-52** — Foreign exceptions do not automatically become Axiom panic.

**AFFI2-53** — Axiom panic does not automatically cross foreign ABI.

**AFFI2-54** — Foreign unwind contracts are explicit.

**AFFI2-55** — Foreign calls do not implicitly synchronize.

**AFFI2-56** — Foreign aliasing is conservative UNKNOWN unless contracted otherwise.

**AFFI2-57** — Foreign effects must be represented in compiler metadata.

**AFFI2-58** — System calls are explicit system-layer operations.

**AFFI2-59** — Syscall ABI is target-specific.

**AFFI2-60** — POSIX is a system library layer, not Core.

**AFFI2-61** — Windows API is a system library layer, not Core.

**AFFI2-62** — Linux syscall API is a system layer.

**AFFI2-63** — Mach interfaces are a system layer.

**AFFI2-64** — iOS system frameworks are platform libraries.

**AFFI2-65** — Android NDK/Bionic interfaces are platform libraries.

**AFFI2-66** — WASM imports/exports are explicit ABI boundaries.

**AFFI2-67** — WASM linear memory is a distinct storage domain.

**AFFI2-68** — GPU driver interfaces are explicit foreign/system APIs.

**AFFI2-69** — OS handles do not imply ownership.

**AFFI2-70** — `Handle<T>` is logical identity, not ownership.

**AFFI2-71** — Owned foreign resources require deterministic cleanup.

**AFFI2-72** — Foreign cleanup through Drop is non-fallible.

**AFFI2-73** — Fallible foreign cleanup uses explicit close/release operations.

**AFFI2-74** — TLS semantics are target-specific.

**AFFI2-75** — Foreign TLS state is not ordinary shared state.

**AFFI2-76** — Dynamic symbol lookup does not prove symbol type.

**AFFI2-77** — Dynamic symbol type assertions require an explicit unsafe boundary.

**AFFI2-78** — Exported functions require explicit native symbol contracts.

**AFFI2-79** — `pub` does not imply native symbol export.

**AFFI2-80** — Generic foreign functions require concrete specialization.

**AFFI2-81** — Generic FFI specializations must independently satisfy FFI safety.

**AFFI2-82** — Trait objects are not automatically FFI-safe.

**AFFI2-83** — Futures are not automatically FFI-safe.

**AFFI2-84** — Closures are not automatically FFI-safe.

**AFFI2-85** — Standard library containers are not automatically FFI-safe.

**AFFI2-86** — Foreign opaque objects may be wrapped by safe resource types.

**AFFI2-87** — Foreign reference counting does not imply Axiom `Arc`.

**AFFI2-88** — Foreign synchronization requires explicit semantics.

**AFFI2-89** — Foreign callback synchronization must be modeled.

**AFFI2-90** — FFI contracts participate in incremental semantic fingerprints.

**AFFI2-91** — Cross compilation uses target ABI, not host ABI.

**AFFI2-92** — Native library resolution belongs to the build/system layer.

**AFFI2-93** — Compiler does not implicitly fetch foreign dependencies.

**AFFI2-94** — FFI verification occurs before ABI lowering.

**AFFI2-95** — Unsafe FFI establishes trusted preconditions; it does not disable subsequent verification.

**AFFI2-96** — Safe verification resumes after a valid FFI boundary.

**AFFI2-97** — Foreign memory effects are conservatively modeled.

**AFFI2-98** — ABI compatibility does not imply semantic type compatibility.

**AFFI2-99** — FFI wrappers may erase to minimal native representations when semantics permit.

**AFFI2-100** — All FFI preserves Axiom ownership, capability, Drop, concurrency, async, storage, representation and ABI invariants.

---

# Kết luận kiến trúc

Sau BOOTSTRAP-077, Axiom đã có một boundary khá hoàn chỉnh:

```text
                    AXIOM
                      │
       ┌──────────────┼──────────────┐
       │              │              │
    Memory         Resource       Concurrency
       │              │              │
       └──────────────┼──────────────┘
                      │
                Semantic MIR
                      │
               Verified MIR
                      │
             Semantic Optimization
                      │
              Representation
                      │
                  ABI MIR
                      │
          ┌───────────┼───────────┐
          │           │           │
      Axiom ABI     C ABI     System ABI
          │           │           │
          └───────────┼───────────┘
                      │
             Native Machine Code
                      │
          PE / ELF / Mach-O / WASM
```

Đặc biệt, thiết kế này đạt được một mục tiêu quan trọng của Axiom: **programmer có thể viết high-level code khá sạch, nhưng compiler vẫn có đủ thông tin để tạo native code rất thấp-level khi cần.** FFI chỉ là một boundary có contract, không phải lý do để đưa pointer/lifetime/ABI complexity vào toàn bộ ngôn ngữ.

### Bước kiến trúc tiếp theo

Theo chuỗi hiện tại, bước hợp lý tiếp theo là:

**BOOTSTRAP-078 — Axiom SIMD / Vector / Matrix / Tensor Execution Model**

Tập trung vào việc Axiom có thể cạnh tranh C/C++ và đặc biệt hỗ trợ **AI/GPU/CPU numerical workloads** mà không biến SIMD/tensor thành một hệ type quá phức tạp:

- SIMD vector types
- scalar ↔ vector
- portable SIMD
- AVX2/AVX-512/NEON/SVE/RVV
- vectorization
- alignment
- masked operations
- gather/scatter
- reduction
- matrix/tensor primitives
- CPU ↔ GPU interoperability
- `@kernel`
- TensorView/shape/stride
- zero-copy
- auto-vectorization
- ABI của vector types
- FFI SIMD ABI
- overflow/NaN semantics
- và quan trọng nhất: **thiết kế sao cho code SIMD thủ công không trở thành bắt buộc để đạt hiệu năng cao**.