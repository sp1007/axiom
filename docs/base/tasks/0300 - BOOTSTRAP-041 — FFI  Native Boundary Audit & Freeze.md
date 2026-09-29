Tiếp tục theo chuỗi kiến trúc. Phần này rất quan trọng vì nó quyết định Axiom có thực sự đứng độc lập với C/C++ toolchain hay không.

# BOOTSTRAP-041 — FFI / Native Boundary Audit & Freeze

## 1. Mục tiêu

Axiom phải có thể:

```text
Axiom
 ├── gọi API hệ điều hành
 ├── gọi thư viện C
 ├── gọi thư viện native khác
 ├── export API cho C/C++/Rust/...
 ├── tạo static library
 ├── tạo shared library
 ├── tạo executable native
 ├── gọi syscall
 └── cuối cùng tự xây compiler/linker/toolchain của mình
```

Nhưng:

> **FFI không được làm bẩn semantic core của Axiom.**

Core language vẫn có:

```text
value
ownership
capability
type
trait
ABI
```

FFI là một **semantic boundary**.

---

# 2. Ba ABI phải phân biệt

Axiom có ít nhất:

```text
Axiom ABI
C ABI
System ABI
```

### Axiom ABI

Dùng giữa các module Axiom tương thích compiler/toolchain.

### C ABI

Dùng interoperability:

```text
C
C++
Rust extern C
Python native extension
...
```

### System ABI

Ví dụ:

```text
Windows
Linux
macOS
iOS
Android
WASM host
```

System ABI có thể khác C ABI.

---

# 3. Không dùng C ABI làm ABI nội bộ

Đây là quyết định quan trọng.

Không:

```text
Axiom compiler
    ↓
mọi function
    ↓
C ABI
```

Vì sẽ làm mất cơ hội:

- register passing tối ưu
- aggregate return tối ưu
- generic specialization
- internal calling convention
- zero-cost abstraction.

Thay vào đó:

```text
Axiom → Axiom ABI
FFI   → explicit foreign ABI
```

---

# 4. Syntax đề xuất

Ví dụ:

```axiom
extern "C" fn puts(s: *const u8) -> i32
```

hoặc:

```axiom
extern "system" fn ...
```

Tên ABI là semantic contract.

---

# 5. FFI function mặc định unsafe

Ví dụ:

```axiom
extern "C" fn malloc(size: usize) -> *mut u8
```

không nên biến thành safe API.

Calling foreign function trực tiếp thuộc unsafe/system boundary.

Wrapper an toàn:

```axiom
fn allocate(size: usize) -> Result<Buffer, AllocError> {
    unsafe {
        ...
    }
}
```

Sau wrapper, application code trở lại safe semantics.

---

# 6. Tại sao?

Compiler không thể biết foreign function thực sự làm gì.

Ví dụ declaration:

```axiom
extern "C" fn foo(x: *mut i32)
```

compiler không biết:

- `foo` có giữ pointer không
- có mutate không
- có free không
- có callback không
- có thread khác truy cập không
- có synchronization không.

Do đó boundary phải explicit.

---

# 7. FFI type safety

Không cho arbitrary Axiom type:

```axiom
extern "C" fn foo(x: String)
```

trừ khi `String` có explicit ABI contract.

FFI declaration chỉ được dùng:

```text
FFI-safe types
```

---

# 8. Primitive ABI

Các primitive cơ bản có thể map rõ:

```text
i8   → int8_t-like
u8   → uint8_t-like
i16
u16
i32
u32
i64
u64
f32
f64
```

Nhưng:

```text
isize
usize
```

phụ thuộc target word size.

---

# 9. `bool`

Cần ABI distinction.

Axiom:

```text
bool
```

không mặc định đồng nghĩa với C `_Bool` trong mọi ABI.

Khi FFI cần C-compatible representation:

```axiom
@repr(C)
struct ...
```

hoặc explicit ABI-safe boolean representation.

---

# 10. Struct FFI

Ví dụ:

```axiom
@repr(C)
struct Point {
    x: f32,
    y: f32,
}
```

bây giờ field layout có contract.

Không có `@repr(C)`:

```text
struct Point
```

không được coi là C ABI compatible.

---

# 11. Enum FFI

Enum Axiom:

```axiom
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

không tự động là C enum.

C enum ABI cần explicit integer representation:

```axiom
@repr(C, u32)
enum Status {
    Ok = 0,
    Failed = 1,
}
```

Syntax cụ thể có thể tinh chỉnh, semantic này cần freeze.

---

# 12. Tagged unions

Nếu cần tương tác với C:

```c
union
```

thì Axiom cần representation contract rõ ràng.

Không nên giả định:

```text
Axiom enum = C union
```

---

# 13. `@repr(transparent)`

Newtype:

```axiom
struct UserId(u64)
```

có thể:

```axiom
@repr(transparent)
struct UserId(u64)
```

→ ABI tương đương `u64` trong những boundary mà contract cho phép.

---

# 14. `@repr(packed)`

Có:

```axiom
@repr(packed)
```

nhưng system/unsafe-level.

Vì:

```text
packed field
    ↓
unaligned access
```

không nên trở thành bình thường trong safe code.

---

# 15. Alignment

```axiom
@repr(align(64))
struct CacheLine {
    ...
}
```

là representation contract.

Compiler phải bảo đảm.

---

# 16. Padding

Cũng như BOOTSTRAP-023:

Padding không phải semantic data.

Do đó không cho phép:

```text
memcmp(struct_a, struct_b)
```

được xem là semantic equality của Axiom struct.

---

# 17. String ABI

Đây là điểm cần đặc biệt rõ.

Axiom:

```text
String
```

là owned valid UTF-8.

Không phải C string.

C string:

```text
char*
```

là một abstraction khác.

---

# 18. Không implicit String → C string

Không cho:

```axiom
puts(my_string)
```

nếu `puts` yêu cầu C string.

Phải explicit conversion:

```axiom
my_string.as_c_str()
```

hoặc tương đương.

---

# 19. C string

Library/system layer có:

```text
CStr
CString
```

Ví dụ semantic:

```text
CStr
    non-owning NUL-terminated byte sequence

CString
    owning NUL-terminated byte sequence
```

UTF-8 validity không nhất thiết là invariant của `CStr`.

---

# 20. Slice ABI

Axiom:

```text
view<T>
```

không tự động là:

```text
T*
+
usize
```

trong mọi ABI.

Compiler có thể thường lower thành:

```text
ptr + len
```

nhưng đây là representation.

FFI boundary phải explicit.

---

# 21. C-compatible slice

Nếu cần:

```axiom
@repr(C)
struct Slice<T> {
    ptr: *const T,
    len: usize,
}
```

đây mới là ABI contract.

---

# 22. Raw pointer

Raw pointer:

```text
*const T
*mut T
```

là FFI/system primitive.

Nhưng raw pointer:

> không phải ownership.

---

# 23. Pointer provenance

FFI có thể nhận:

```text
*mut T
```

nhưng Axiom compiler không được giả định pointer có provenance hợp lệ chỉ vì type đúng.

Boundary chịu trách nhiệm establish contract.

---

# 24. Foreign pointer → safe view

Wrapper:

```text
unsafe foreign pointer
        ↓
validate
        ↓
view<T>
```

sau đó safe code có thể dùng capability.

---

# 25. Foreign pointer lifetime

Nếu foreign API giữ pointer sau khi function return:

```text
foo(ptr)
```

thì wrapper phải encode lifetime/storage contract.

Không thể để compiler mặc định coi pointer chỉ sống trong call nếu foreign API thực tế giữ nó.

---

# 26. Callback

Axiom function:

```text
fn callback(x: i32) -> i32
```

không mặc định tương đương C function pointer.

FFI callback phải có ABI:

```axiom
extern "C" fn callback(x: i32) -> i32
```

hoặc explicit adapter.

---

# 27. Capturing closure → C callback

Capturing closure:

```text
|x| ...
```

không thể trực tiếp biến thành:

```text
int (*callback)(int)
```

vì closure có environment.

C ABI adapter cần:

```text
function pointer
+
context pointer
```

---

# 28. Callback context

Library có thể cung cấp:

```text
Callback<T>
```

semantic:

```text
callback function
+
opaque context
+
ownership contract
```

---

# 29. Callback lifetime

Đây là một trong những FFI bug nguy hiểm nhất.

Ví dụ:

```text
register_callback(cb)
return
```

foreign library có thể gọi callback sau đó.

Compiler phải biết callback environment vẫn sống.

Wrapper phải giữ ownership.

---

# 30. Foreign exception

Không cho exception xuyên qua Axiom boundary.

Ví dụ:

```text
C++ exception
     ↓
Axiom function
```

không tự động trở thành Axiom panic/unwind.

---

# 31. Axiom panic → foreign

Ngược lại:

```text
Axiom panic
    ↓
extern "C"
```

không được unwind qua FFI mặc định.

Panic phải được:

```text
abort
catch/convert
```

theo explicit boundary policy.

---

# 32. ABI boundary là unwind boundary

Default:

```text
Axiom panic
      X
foreign stack
```

và:

```text
foreign exception
      X
Axiom stack
```

---

# 33. Dynamic library

Axiom cần:

```text
DynamicLibrary
Symbol<T>
```

library/system abstraction.

Ví dụ:

```text
load("foo.dll")
lookup("foo")
```

---

# 34. `Symbol<T>`

`Symbol<T>` không được tự động coi là safe callable.

Dynamic symbol type chỉ là:

```text
address
+
declared ABI/type
```

Việc address thực sự có đúng signature hay không là external assumption.

---

# 35. Dynamic symbol validation

Conceptually:

```text
unsafe lookup
      ↓
Symbol<extern "C" fn(...)>
```

Sau đó wrapper có thể expose safe API nếu contract đảm bảo.

---

# 36. Static library

Axiom compiler/linker phải hỗ trợ:

```text
libfoo.a
foo.lib
```

tùy target.

---

# 37. Shared library

Hỗ trợ:

```text
.so
.dll
.dylib
```

và target-specific equivalents.

---

# 38. Axiom static library

Axiom module có thể export:

```axiom
@export("axiom_add")
pub fn add(...)
```

`pub` và `@export` là hai khái niệm khác.

---

# 39. Visibility

```text
pub
```

= source/module visibility.

```text
@export
```

= binary symbol export contract.

Một function có thể:

```text
pub
```

nhưng không export native symbol.

---

# 40. Symbol naming

Axiom ABI có thể sử dụng mangled names.

C ABI:

```text
extern "C"
```

thì symbol naming phải theo ABI contract.

`@export("name")` cho explicit external name.

---

# 41. No `@no_mangle`

Không cần attribute riêng kiểu:

```text
@no_mangle
```

nếu:

```axiom
@export("foo")
```

đã định nghĩa symbol contract.

Đây phù hợp với BOOTSTRAP-036.

---

# 42. Allocator boundary

Đây là điểm phải cực kỳ nghiêm.

Không:

```text
Axiom alloc()
   ↓
C free()
```

hoặc ngược lại một cách mặc định.

Allocation domain phải rõ.

---

# 43. Foreign ownership categories

Một resource từ FFI có thể là:

```text
Borrowed
OwnedByAxiom
OwnedByForeign
Shared
HandleOnly
```

Wrapper phải encode category.

---

# 44. `OwnedByForeign`

Ví dụ:

```text
FILE*
```

Axiom không được tự động:

```text
free(FILE*)
```

nếu foreign API sở hữu resource.

---

# 45. `OwnedByAxiom`

Ngược lại nếu Axiom allocator tạo memory:

```text
Axiom alloc
```

foreign code phải dùng đúng deallocator.

---

# 46. Cross-boundary allocation

API phải cung cấp:

```text
allocate
deallocate
```

cùng allocator domain.

Không đoán.

---

# 47. String allocation

Không:

```text
Axiom String
   ↓
foreign free()
```

trừ khi representation/allocator contract explicit.

---

# 48. FFI resource wrapper

Ví dụ:

```axiom
struct File {
    raw: *mut CFile,
}

impl Drop for File {
    fn drop(self: owning Self) {
        unsafe {
            c_close(self.raw)
        }
    }
}
```

Đây là pattern chính.

---

# 49. Drop + FFI

Drop gọi foreign cleanup là hợp lệ.

Nhưng:

```text
Drop
```

không được propagate recoverable error.

Nếu:

```text
close() -> Result
```

có thể fail:

```text
file.close()?
```

phải được gọi explicit trước Drop.

---

# 50. Syscall

Syscall không phải C library call.

Có thể:

```text
extern "syscall"
```

hoặc compiler/system intrinsic.

Target-specific.

---

# 51. Syscall safety

Ví dụ:

```text
read(fd, ptr, len)
```

không nên expose trực tiếp cho safe code.

Safe wrapper:

```text
read(buffer: mut_view<u8>) -> Result<usize, IoError>
```

---

# 52. System ABI

Windows:

```text
system
```

Linux:

```text
syscall
```

macOS:

```text
system ABI
```

Android/iOS:

```text
platform ABI
```

Các ABI này nằm ở system layer.

---

# 53. Variadic FFI

C:

```text
printf(...)
```

cần hỗ trợ.

Nhưng:

```text
variadic
```

chỉ system/unsafe.

Không đưa variadic thành tính năng function bình thường của Axiom.

---

# 54. Format safety

Không nên expose:

```axiom
printf(format, ...)
```

làm high-level API.

Axiom formatting library có thể:

```text
format(...)
```

type-safe.

---

# 55. TLS

FFI cần hỗ trợ:

```text
@tls
```

đã có trong attribute model.

TLS ABI target-specific.

---

# 56. Interrupt

```text
@interrupt
```

là system ABI contract.

Không được gọi như function bình thường nếu target cấm.

---

# 57. Naked function

```text
@naked
```

system-level.

Compiler không được tự thêm:

```text
prologue
epilogue
```

trái contract.

---

# 58. Inline assembly

Đã thuộc BOOTSTRAP-036:

```text
unsafe
asm
```

phải khai báo:

```text
inputs
outputs
clobbers
memory effects
```

để optimizer không phá semantics.

---

# 59. FFI và alias analysis

Đây là điểm rất quan trọng.

Compiler **không được** giả định foreign function là pure/non-aliasing.

Ví dụ:

```text
extern fn foo(*mut i32, *mut i32)
```

có thể hai pointer alias.

Do đó:

```text
unknown foreign effects
```

là default.

---

# 60. Foreign effects

Axiom không có full effect system Core v1.

Thay vào đó FFI declaration có semantic metadata tối thiểu:

```text
ABI
unsafe
input/output
ownership
callback
unwind
memory effects
```

khi compiler cần.

---

# 61. `@noalias`

Không thêm source-level `@noalias` vào Core v1.

Nếu FFI/backend cần guarantee:

```text
system-level contract
```

có thể bổ sung sau.

---

# 62. Volatile

FFI/MMIO cần:

```text
volatile_load
volatile_store
```

intrinsic/system API.

Volatile:

> không phải synchronization.

---

# 63. Atomic FFI

Foreign atomic object chỉ an toàn nếu representation và memory model tương thích.

Không tự động cast:

```text
*CAtomic
```

→ `Atomic<T>`.

Wrapper phải establish ABI contract.

---

# 64. FFI synchronization

FFI call không tự động tạo:

```text
Acquire
Release
SeqCst
```

Compiler không được đoán.

Nếu foreign API đồng bộ:

```text
wrapper
```

phải establish appropriate synchronization semantics.

---

# 65. Thread callback

Foreign thread có thể gọi Axiom callback.

Runtime phải có explicit policy:

```text
foreign thread
      ↓
Axiom callback
```

Không mặc định foreign thread là Axiom-managed thread.

---

# 66. TLS trong foreign callback

Nếu callback cần Axiom TLS/runtime state:

```text
runtime attachment
```

có thể cần.

Không tự động giả định mọi foreign thread đã attach runtime.

---

# 67. Runtime-free FFI

Một chương trình:

```text
freestanding
```

vẫn có thể gọi:

```text
syscall
```

hoặc external symbol mà không link monolithic Axiom runtime.

---

# 68. No mandatory C runtime

Mục tiêu cuối:

```text
Axiom executable
```

có thể chạy:

```text
without libc
```

nếu program không cần libc.

Ví dụ freestanding:

```text
_start
syscall
exit
```

---

# 69. Nhưng libc interoperability

Hosted application vẫn có thể:

```text
extern "C"
```

và link libc.

Đây là option, không phải compiler dependency.

---

# 70. Linker

Axiom cuối cùng cần native linker capability.

Có hai giai đoạn:

### Bootstrap

Có thể sử dụng system linker/toolchain tạm thời.

### Final self-host

Axiom có:

```text
object writer
linker
archive writer
symbol resolver
relocation handling
```

theo target.

---

# 71. Compiler dependency ≠ target dependency

Mục tiêu:

```text
Axiom compiler
```

không phụ thuộc C compiler để compile Axiom.

Nhưng target OS vẫn có thể cung cấp:

```text
kernel
system ABI
loader
```

Đó không phải third-party compiler dependency.

---

# 72. Object formats

Axiom cần native writer cho:

```text
PE/COFF
ELF
Mach-O
WASM
```

và architecture:

```text
x86-64
ARM64
ARM32
RISC-V
...
```

theo roadmap.

---

# 73. Relocations

FFI/linking phụ thuộc:

```text
symbol
relocation
section
visibility
TLS
weak/strong binding
PLT/GOT
import/export
```

Đây thuộc native linker layer.

---

# 74. Import symbols

Có thể:

```axiom
extern "C" fn memcpy(...)
```

Compiler tạo external relocation.

Linker resolve.

---

# 75. Export symbols

```axiom
@export("foo")
pub fn foo(...) { ... }
```

→ symbol export.

---

# 76. Link directives

`@link` thuộc system/build layer.

Ví dụ conceptually:

```axiom
@link("user32")
extern "system" ...
```

Không phải semantic của ordinary function.

---

# 77. Library search

Compiler/build system có thể resolve:

```text
static library
shared library
framework
system library
```

nhưng library discovery không nên hard-code vào Core compiler.

---

# 78. Build metadata

FFI module cần machine-readable metadata:

```text
ABI
target
library
symbol
calling convention
repr
ownership
```

Điều này rất quan trọng cho AI tooling sau này.

---

# 79. AI-friendly FFI

Compiler diagnostic nên có structured data:

```json
{
  "code": "AFFI-104",
  "symbol": "foo",
  "reason": "type_not_ffi_safe",
  "type": "String",
  "required": "@repr(C) compatible type"
}
```

Không bắt AI phải parse prose.

---

# 80. FFI generated declarations

Comptime có thể generate FFI declarations.

Nhưng generated declarations vẫn phải:

```text
resolve
type-check
ABI-check
ownership-check
```

---

# 81. Bindgen

Axiom có thể về sau có:

```text
C header
   ↓
comptime/tool
   ↓
Axiom declarations
```

Nhưng bindgen không thuộc semantic Core.

---

# 82. C++ interop

Không nên cam kết:

```text
extern "C++"
```

full C++ ABI trong Core v1.

C++ ABI phức tạp:

- name mangling
- classes
- virtual tables
- exceptions
- templates
- compiler-specific ABI.

MVP:

```text
C ABI
```

trước.

---

# 83. C++ wrapper

Muốn dùng C++:

```text
C++ wrapper
      ↓
extern C
      ↓
Axiom
```

đây là boundary ổn định hơn.

---

# 84. Rust interop

Rust cũng có:

```text
extern "C"
```

nên Axiom có thể interop tốt thông qua C ABI mà không cần Rust ABI.

---

# 85. Axiom ABI stability

Không tuyên bố:

```text
Axiom ABI stable forever
```

ở v1.

Compiler version có thể thay đổi internal ABI.

Stable external ABI trước mắt:

```text
C ABI
```

và explicit system ABIs.

---

# 86. Axiom-to-Axiom ABI

Có thể có:

```text
Axiom ABI vN
```

sau khi compiler/LIR/layout đủ ổn định.

Package metadata ghi:

```text
compiler ABI version
language ABI version
target
features
```

---

# 87. Generic FFI

Không export generic function trực tiếp qua C ABI:

```axiom
@export
fn max<T>(...)
```

Không có C ABI tương ứng.

Compiler phải specialize:

```text
max_i32
max_f32
...
```

hoặc cung cấp wrapper concrete.

---

# 88. Trait object FFI

Không cho:

```text
dyn Trait
```

làm C ABI mặc định.

Nếu cần:

```text
explicit C-compatible vtable struct
```

với function pointers + context.

---

# 89. Closure FFI

Tương tự:

```text
closure
```

không tự động FFI-safe.

Phải tạo adapter.

---

# 90. Future FFI

Future không có ABI ổn định mặc định.

Async FFI dùng:

```text
callback
poll interface
opaque handle
completion object
```

explicit.

---

# 91. GPU FFI

GPU API handles:

```text
VkBuffer
MTLBuffer
CUDA pointer
...
```

được xử lý như external resources.

Không giả định chúng là ordinary Axiom pointer.

---

# 92. WASM

WASM là target ABI đặc biệt.

Axiom có thể export:

```text
extern "wasm"
```

hoặc target-specific ABI.

Host bindings phải explicit.

---

# 93. Java/Kotlin/Swift/Objective-C

Không đưa tất cả vào Core.

Native bridges:

```text
C ABI
Objective-C ABI
JNI
Swift/ObjC bridge
```

thuộc platform/system layer.

---

# 94. Ownership at FFI boundary

Đây là invariant quan trọng nhất:

> **Không có ownership transfer ngầm qua FFI.**

Nếu transfer:

```text
owned Axiom
    ↓
foreign
```

phải explicit.

Ngược lại cũng vậy.

---

# 95. Capability at FFI boundary

Foreign pointer chỉ có:

```text
machine-level address
```

không tự có:

```text
safe capability
```

Wrapper phải validate/establish capability.

---

# 96. Resource lifetime

Foreign operation đang chạy:

```text
async I/O
GPU operation
callback registration
OS request
```

không được để Drop reclaim resource sớm.

Cùng nguyên tắc với GPU/async.

---

# 97. FFI + async

Ví dụ:

```text
foreign_submit(buffer)
```

Nếu foreign API giữ buffer asynchronously:

```text
buffer
```

phải remain alive đến completion.

Wrapper nên biểu diễn:

```text
Operation<'semantic>
```

hoặc ownership-bearing Future/Handle.

Không cần expose lifetime syntax cho programmer.

---

# 98. FFI + concurrency

Foreign library có thể spawn threads.

Axiom không được tự động coi object là `Send`/`Share`.

Wrapper phải encode concurrency contract.

---

# 99. FFI boundary không phá safe core

Một điểm rất quan trọng:

```text
unsafe extern call
```

không có nghĩa:

```text
compiler stop checking everything
```

Sau boundary, verifier tiếp tục hoạt động với những gì đã được establish.

Giống unsafe memory model.

---

# 100. BOOTSTRAP-041 — Freeze invariants

```text
AFFI-20   Axiom ABI is distinct from C ABI.
AFFI-21   System ABI is distinct from C ABI.
AFFI-22   Internal Axiom calls use Axiom ABI by default.
AFFI-23   Foreign calls require an explicit ABI.
AFFI-24   Direct foreign calls are unsafe unless wrapped by a verified safe abstraction.
AFFI-25   FFI declarations admit only ABI-compatible types.
AFFI-26   Ordinary Axiom types are not automatically FFI-safe.
AFFI-27   @repr(C) establishes C-compatible representation where applicable.
AFFI-28   @repr(transparent) establishes transparent ABI representation.
AFFI-29   @repr(packed) is unsafe/system-level.
AFFI-30   Alignment contracts are explicit.
AFFI-31   Axiom String is not a C string.
AFFI-32   C strings require explicit representation.
AFFI-33   view<T> is not automatically a C ABI slice.
AFFI-34   Raw pointers do not imply ownership.
AFFI-35   Raw pointers do not imply safe capability.
AFFI-36   Foreign pointers require explicit provenance assumptions.
AFFI-37   Numeric addresses do not automatically become valid pointers.
AFFI-38   Foreign ownership transfer must be explicit.
AFFI-39   Allocator domains must not be guessed across FFI.
AFFI-40   Memory allocated by one ownership domain must be released by a compatible domain.
AFFI-41   Drop may perform foreign cleanup.
AFFI-42   Drop does not propagate recoverable cleanup errors.
AFFI-43   Explicit close/release APIs handle fallible cleanup.
AFFI-44   Foreign exceptions do not cross into Axiom by default.
AFFI-45   Axiom panic does not unwind through foreign ABI by default.
AFFI-46   FFI boundaries are unwind boundaries by default.
AFFI-47   Callback ABI must be explicit.
AFFI-48   Capturing closures are not ordinary C function pointers.
AFFI-49   Callback context ownership must be explicit.
AFFI-50   Callback lifetime must be explicitly established.
AFFI-51   Dynamic symbols require explicit ABI/type contracts.
AFFI-52   Dynamic symbol lookup does not prove symbol type correctness.
AFFI-53   @export establishes an external symbol contract.
AFFI-54   Visibility and binary export are distinct concepts.
AFFI-55   Generic functions are not directly C-ABI-exportable without specialization.
AFFI-56   dyn Trait is not automatically FFI-safe.
AFFI-57   Futures are not automatically FFI-safe.
AFFI-58   Closures are not automatically FFI-safe.
AFFI-59   Foreign calls do not imply synchronization.
AFFI-60   Foreign memory effects are not assumed pure.
AFFI-61   Foreign aliasing is conservatively treated unless explicitly contracted.
AFFI-62   FFI does not implicitly establish Acquire/Release semantics.
AFFI-63   Volatile access is distinct from atomic synchronization.
AFFI-64   Syscalls are explicit system-layer operations.
AFFI-65   C variadics are restricted to FFI/system contexts.
AFFI-66   Runtime-free programs may use FFI without a monolithic runtime.
AFFI-67   libc is optional, not a mandatory compiler dependency.
AFFI-68   Axiom can target native object formats without requiring a C compiler.
AFFI-69   Static and shared libraries are first-class native artifacts.
AFFI-70   Link directives belong to the system/build layer.
AFFI-71   Axiom ABI stability is versioned independently from source language syntax.
AFFI-72   Stable C ABI is prioritized before stable Axiom ABI.
AFFI-73   FFI-generated declarations are re-verified normally.
AFFI-74   Comptime cannot bypass FFI safety rules.
AFFI-75   Unsafe FFI does not disable unrelated compiler verification.
AFFI-76   Safe verification resumes after a foreign boundary only for established contracts.
AFFI-77   Foreign resources require explicit lifetime ownership.
AFFI-78   In-flight foreign operations retain required resource lifetime.
AFFI-79   Async foreign operations require explicit completion/lifetime semantics.
AFFI-80   Foreign-created threads do not automatically become Axiom-managed threads.
AFFI-81   Foreign concurrency properties must be encoded by wrappers/contracts.
AFFI-82   C++ ABI compatibility is not required by Core v1.
AFFI-83   C++ interoperability should primarily use C-compatible wrappers initially.
AFFI-84   GPU external handles are explicit foreign resources.
AFFI-85   WASM host bindings use explicit target ABI.
AFFI-86   Platform-specific ABIs belong to system layers.
AFFI-87   FFI representation is distinct from wire/serialization representation.
AFFI-88   FFI layout contracts are explicit.
AFFI-89   Compiler optimization cannot violate an ABI contract.
AFFI-90   FFI lowering occurs after semantic verification.
```

---

# Kết quả kiến trúc sau BOOTSTRAP-041

Axiom hiện đã có một biên khá rõ:

```text
                  ┌─────────────────────┐
                  │   Axiom Safe Core   │
                  │                     │
                  │ Type                │
                  │ Ownership           │
                  │ Capability          │
                  │ Concurrency         │
                  │ Async               │
                  │ GPU                 │
                  └──────────┬──────────┘
                             │
                    explicit unsafe/system
                             │
                  ┌──────────▼──────────┐
                  │   Native Boundary   │
                  │                     │
                  │ Axiom ABI            │
                  │ C ABI                │
                  │ System ABI           │
                  │ Syscall              │
                  │ FFI                  │
                  │ Raw pointer          │
                  │ Dynamic symbol       │
                  └──────────┬──────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
       OS/API             Libraries          Hardware
```

Điểm đáng chú ý là **unsafe không phải một “chế độ tắt compiler safety”**. Nó chỉ là nơi programmer được phép đưa vào những giả định mà compiler không thể tự chứng minh.

---

## Một quyết định kiến trúc rất quan trọng đã được chốt

Axiom **không cần phụ thuộc C để tồn tại về lâu dài**.

Lộ trình có thể là:

```text
Giai đoạn bootstrap:

Axiom compiler
     ↓
Axiom MIR
     ↓
LLVM / system assembler / system linker
```

sau đó:

```text
Axiom compiler
     ↓
Axiom MIR
     ↓
Axiom LIR
     ↓
Axiom Machine Encoder
     ↓
Axiom Object Writer
     ↓
Axiom Linker
     ↓
native executable
```

C ABI chỉ trở thành **cầu nối interoperability**, chứ không phải nền móng của compiler.

---

# Bước tiếp theo

Sau FFI, kiến trúc đã đủ nền tảng để chuyển sang phần **Build/Module/Package/Dependency System**.

Tôi đề xuất **BOOTSTRAP-042 — Module, Package, Dependency & Build System**. Phần đó sẽ quyết định:

```text
import/export
module visibility
package
dependency graph
workspace
build profiles
cross compilation
incremental compilation
artifact cache
comptime dependencies
native library dependencies
static/shared linking
reproducible build
package lock
```

và đặc biệt phải thiết kế sao cho **một dự án Axiom có thể build hoàn toàn không cần CMake/Cargo/npm/MSBuild hay package manager bên thứ ba**.