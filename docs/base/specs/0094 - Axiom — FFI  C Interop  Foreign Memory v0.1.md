Tiếp tục.

# Axiom — FFI / C Interop / Foreign Memory v0.1

Đây là phần Axiom phải **thực dụng tuyệt đối**. Một systems language mà FFI với C/C++ khó dùng thì rất khó thay thế C/C++ trong thực tế.

Mục tiêu:

> **Gọi C trực tiếp, ABI chính xác, không cần wrapper runtime; nhưng ranh giới FFI phải là semantic boundary rõ ràng để C không phá vỡ safe Axiom.**

---

## 1. Ba thế giới phải tách biệt

Axiom cần phân biệt:

```text
Axiom safe world
       │
       │ explicit FFI boundary
       ▼
C ABI world
       │
       ▼
Raw machine / OS / hardware
```

Không nên biến C pointer thành Axiom `view<T>` một cách tự động.

---

# 2. `extern "C"`

Syntax đề xuất:

```axiom
extern "C" {
    fn malloc(size: usize) -> *mut u8
    fn free(ptr: *mut u8)
}
```

Nhưng declaration này **chưa tự động làm function unsafe** chỉ vì ABI là C.

Phải phân biệt:

```text
ABI safety
```

và:

```text
operation safety
```

Ví dụ một C function:

```c
int add(int a, int b);
```

hoàn toàn có thể được khai báo safe:

```axiom
extern "C" fn add(a: i32, b: i32) -> i32
```

Nếu API contract thực sự safe.

Trong khi:

```c
void process(char *p);
```

có thể cần:

```axiom
unsafe extern "C" fn process(p: *mut u8)
```

---

# 3. `extern` không đồng nghĩa `unsafe`

Đây là điểm tôi muốn khóa.

Không nên thiết kế:

```axiom
extern "C" fn foo(...)
```

→ tự động unsafe.

Vì khi đó mọi API hệ điều hành đều trở nên khó dùng.

Thay vào đó:

```text
ABI declaration
```

là một chuyện.

```text
Safety contract
```

là chuyện khác.

---

# 4. C pointer vẫn là raw pointer

Ví dụ:

```axiom
extern "C" {
    fn read(fd: i32, buf: *mut u8, len: usize) -> isize
}
```

Axiom **không biến**:

```text
*mut u8
```

thành:

```text
mut_view<u8>
```

vì compiler không biết:

- buffer có đủ lớn không
- pointer có null không
- lifetime bao lâu
- function có giữ pointer lại không
- function có modify đúng extent không.

---

# 5. Wrapper an toàn

Thay vào đó, standard library viết wrapper:

```axiom
fn read(fd: FileDescriptor, buffer: mut_view<u8>) -> Result<usize, Error> {
    unsafe {
        c_read(fd.raw(), buffer.ptr(), buffer.len())
    }
}
```

Đây chính là kiến trúc:

```text
C unsafe contract
       ↓
small unsafe wrapper
       ↓
safe Axiom API
       ↓
application
```

Unsafe được **tập trung**, không lan truyền.

---

# 6. C string

C string là một vấn đề rất thường gặp.

Axiom `Text` không nên tương đương:

```text
char*
```

vì:

```text
Text
```

có semantic Unicode/length.

C string là:

```text
NUL-terminated byte sequence
```

Do đó cần một abstraction riêng, ví dụ:

```text
CStr
CString
```

conceptually:

```text
CStr
    = borrowed NUL-terminated bytes

CString
    = owned NUL-terminated bytes
```

Không implicit:

```text
Text → CStr
```

và cũng không implicit:

```text
CStr → Text
```

---

# 7. C string conversion

Có thể:

```axiom
let c = CString.from_text(text)?
```

và:

```axiom
let text = cstr.to_text()?
```

Conversion có thể fail vì:

- embedded NUL
- invalid UTF-8
- encoding khác.

Không được giả định C string là Unicode.

---

# 8. C arrays / buffers

C:

```c
void process(int *data, size_t len);
```

Axiom:

```axiom
extern "C" fn process(data: *mut i32, len: usize)
```

Ở safe wrapper:

```axiom
fn process(data: mut_view<i32>) {
    unsafe {
        c_process(data.ptr(), data.len())
    }
}
```

Đây là nơi `view<T>` cực kỳ hữu ích.

---

# 9. Nhưng FFI không được tự động tạo view

Ví dụ:

```axiom
unsafe {
    let p = c_function()
}
```

Không được tự động:

```text
p → view<T>
```

Muốn tạo view:

```axiom
unsafe {
    let v = view_from_raw(p, len)
}
```

với preconditions:

```text
pointer valid
alignment correct
extent valid
lifetime valid
aliasing valid
```

Sau đó compiler tiếp tục tracking `v` như capability bình thường.

---

# 10. Đây là một điểm cực mạnh

Ví dụ:

```axiom
unsafe {
    let p = get_buffer()
    let data = view_from_raw(p, 1024)
}

sum(data)
```

Sau khi `data` được tạo:

```text
raw pointer responsibility
        ↓
unsafe boundary
        ↓
validated capability
        ↓
normal Axiom ownership/view checking
```

Unsafe **không lan mãi về sau**.

---

# 11. FFI pointer lifetime

Nếu C API giữ pointer:

```c
void register_buffer(void *p);
```

thì Axiom không thể biết:

```text
C có giữ p không?
```

Vì vậy FFI declaration phải phân loại contract.

Ví dụ:

```text
BORROWED
CONSUMED
RETAINED
RETURNED
UNKNOWN
```

Nhưng tôi **không khuyến nghị** đưa toàn bộ các keyword này thành source syntax v0.1.

Thay vào đó dùng attributes/FFI contract metadata.

Ví dụ conceptually:

```text
@ffi_borrowed(1)
@ffi_noescape(1)
```

---

# 12. Tại sao không để compiler đoán?

Vì C:

```c
void register_buffer(void *p);
```

có thể:

```text
copy bytes
store pointer
spawn thread
return pointer later
```

Compiler Axiom không thể suy ra.

FFI boundary phải là:

> **unknown by default, explicit contract when safety matters.**

---

# 13. FFI escape classification

Mô hình escape hiện tại đã có:

```text
NO_ESCAPE
LOCAL_ESCAPE
CALL_ESCAPE
RETURN_ESCAPE
GLOBAL_ESCAPE
FFI_ESCAPE
UNKNOWN_ESCAPE
```

Với FFI:

```text
unknown C call
      ↓
FFI_ESCAPE
      ↓
conservative analysis
```

Điều này rất quan trọng cho optimizer.

---

# 14. C struct

Ví dụ:

```c
struct Point {
    int x;
    int y;
};
```

Axiom:

```axiom
@repr(C)
struct Point {
    x: i32
    y: i32
}
```

`@repr(C)` phải là semantic contract.

Compiler không được:

```text
reorder fields
```

theo layout tối ưu của Axiom.

---

# 15. Không có `repr(C)` → không được FFI trực tiếp

Ví dụ:

```axiom
struct Point {
    x: i32
    y: i32
}
```

không nên truyền trực tiếp qua C ABI nếu layout không được xác định.

Compiler có thể báo:

```text
AX_FFI_0003:
type `Point` has no foreign-compatible representation
```

Đây là một safety feature rất đáng giá.

---

# 16. `repr(transparent)`

Ví dụ:

```axiom
@repr(transparent)
struct FileDescriptor {
    raw: i32
}
```

Có thể ABI-compatible với:

```text
i32
```

nhưng vẫn giữ type identity:

```text
FileDescriptor != i32
```

Đây là cách rất tốt để tạo wrapper type zero-cost quanh C handles.

---

# 17. C opaque types

Rất nhiều C API dùng:

```c
typedef struct Foo Foo;
```

Không expose layout.

Axiom cần:

```axiom
extern type Foo
```

Conceptually:

```text
Foo
 ├── size = unknown
 ├── alignment = unknown
 └── representation = opaque
```

Không được:

```text
Foo.field
```

trong Axiom.

---

# 18. Opaque handle

Ví dụ:

```c
typedef struct sqlite3 sqlite3;
```

Axiom:

```axiom
extern type Sqlite3
```

API:

```axiom
extern "C" fn sqlite3_open(...) -> *mut Sqlite3
extern "C" fn sqlite3_close(db: *mut Sqlite3) -> i32
```

Safe wrapper:

```axiom
struct Database {
    raw: *mut Sqlite3
}
```

và Drop:

```text
Database.Drop()
    ↓
sqlite3_close()
```

---

# 19. Ownership của FFI handle

Đây là nơi `Drop` rất hữu ích.

Axiom wrapper:

```text
Database
```

là:

```text
!Copy
Owned
Drop
```

C API vẫn dùng raw pointer.

Application chỉ thấy:

```axiom
let db = Database.open(...)?
```

Không thấy:

```text
malloc
free
sqlite3_close
```

trừ khi cần system-level control.

---

# 20. FFI callback

Ví dụ C:

```c
typedef void (*callback)(int);
```

Axiom:

```axiom
extern "C" fn register_callback(cb: extern "C" fn(i32))
```

Captureless closure:

```axiom
register_callback(|x| println(x))
```

chỉ được tự chuyển thành C function pointer nếu:

```text
captureless
+
compatible ABI
```

Capturing closure:

```axiom
let prefix = ...
register_callback(|x| use(prefix))
```

**không thể** tự biến thành C function pointer.

---

# 21. C callback + userdata

Đây là pattern phổ biến:

```c
void register(callback cb, void *userdata);
```

Axiom nên hỗ trợ explicit pair:

```text
callback
userdata
```

Conceptually:

```axiom
extern "C" fn callback_trampoline(
    value: i32,
    userdata: *mut u8
)
```

Nhưng compiler không tự generate trampoline khi capture semantics có lifetime phức tạp.

Library helper có thể làm:

```text
CCallback<T>
```

với ownership rõ ràng.

---

# 22. Callback lifetime

Ví dụ:

```c
register_callback(cb);
```

nếu C giữ callback mãi:

```text
closure
   ↓
C
   ↓
indefinite lifetime
```

Axiom không được cho phép local closure capture local data rồi escape âm thầm.

Phải có:

```text
owned callback
+
explicit registration lifetime
```

hoặc:

```text
unsafe FFI contract
```

---

# 23. Variadic C

C:

```c
printf("%d %f", x, y);
```

không thể type-safe hoàn toàn bằng ordinary Axiom function signature.

Do đó:

```text
extern "C" variadic
```

chỉ nên tồn tại trong FFI.

Ví dụ:

```axiom
extern "C" {
    fn printf(format: *const u8, ...) -> i32
}
```

Không khuyến khích dùng trực tiếp.

Standard library tạo:

```axiom
print(...)
```

safe hơn.

---

# 24. C unions

C:

```c
union Value {
    int i;
    float f;
};
```

Axiom `union` đã có semantics hạn chế.

FFI:

```axiom
@repr(C)
union CValue {
    i: i32
    f: f32
}
```

Nhưng đọc field nào hợp lệ là **programmer responsibility** nếu C không có discriminant.

Do đó field access có thể yêu cầu:

```text
unsafe
```

hoặc wrapper type cung cấp invariant an toàn.

---

# 25. C bitfields

Không nên thêm bitfield vào Core chỉ vì C có nó.

Ví dụ:

```c
struct Flags {
    unsigned ready:1;
    unsigned mode:3;
};
```

Axiom nên dùng:

```axiom
@repr(C)
struct FlagsRaw {
    bits: u32
}
```

rồi wrapper getter/setter:

```text
ready()
mode()
set_ready()
set_mode()
```

hoặc compiler FFI tooling có thể generate binding.

Như vậy Core vẫn sạch.

---

# 26. C enum

C enum không giống Axiom ADT enum.

Không được giả định:

```text
C enum
==
Axiom enum
```

Axiom binding phải chỉ rõ representation:

```axiom
@repr(C)
enum CStatus: i32 {
    Ok = 0
    Error = 1
}
```

Nhưng semantics vẫn phải phân biệt với ADT enum có payload.

---

# 27. ABI integer types

C có:

```text
int
long
size_t
ptrdiff_t
```

Axiom nên có FFI aliases:

```text
c_int
c_uint
c_long
c_ulong
c_size
c_ptrdiff
```

vì kích thước `long` phụ thuộc ABI.

Không được map:

```text
C long → Axiom i64
```

một cách universal.

---

# 28. `bool`

C `_Bool`/`stdbool.h` và Axiom `bool` cần ABI mapping rõ.

Không nên giả định mọi foreign boolean đều giống nhau.

`repr(C)`/FFI type mapping phải xác định.

---

# 29. Floating point

`f32`/`f64` có thể map trực tiếp khi ABI compatible.

Nhưng compiler phải tôn trọng:

```text
NaN
signed zero
infinity
rounding
```

Không được áp dụng fast-math chỉ vì đi qua C ABI.

---

# 30. Calling convention

Axiom:

```axiom
extern "C"
extern "system"
extern "axiom"
```

Sau này có thể:

```text
stdcall
fastcall
vectorcall
aapcs
sysv64
win64
```

nhưng không nên expose tất cả thành language keywords.

Target-specific attributes có thể bổ sung khi thực sự cần.

---

# 31. Symbol name

Compiler mangling mặc định:

```text
fn foo<T>()
```

không cần giống C.

Nếu cần export symbol:

```axiom
@export("foo")
extern "C" fn foo(...)
```

`@export` là linker-visible symbol contract.

Không đồng nghĩa public source visibility.

---

# 32. Import symbol

Có thể:

```axiom
@import("libc", "malloc")
extern "C" fn malloc(...)
```

hoặc để linker/build system quyết định library.

Tôi nghiêng về việc **không hardcode tên `.dll/.so/.dylib` trong language syntax**.

Build system chịu trách nhiệm:

```text
link libc
link kernel32
link user32
...
```

Language chỉ mô tả ABI.

---

# 33. Dynamic loading

Không thuộc Core.

Library/system layer:

```text
DynamicLibrary
Symbol<T>
```

Ví dụ:

```axiom
let lib = DynamicLibrary.open("plugin")?
let fn = lib.symbol<extern "C" fn(i32) -> i32>("foo")?
```

Ở đây safety phụ thuộc programmer đảm bảo symbol signature đúng.

Có thể có:

```text
unsafe symbol cast
```

---

# 34. FFI và optimizer

Compiler phải biết foreign function effects.

Ví dụ một hàm C:

```text
unknown
```

có thể:

```text
READ memory
WRITE memory
IO
ALLOC
PANIC/abort
FFI
```

Do đó mặc định:

```text
FFI → conservative effect
```

Nếu declaration có contract:

```text
@pure
@readonly
@noescape
```

compiler có thể optimize mạnh hơn.

---

# 35. Không cho programmer tự gắn `@pure` tùy tiện

Đây là một điểm tôi muốn rất rõ.

Nếu viết:

```axiom
@pure
extern "C" fn dangerous(...)
```

thì compiler không thể kiểm chứng C implementation.

Do đó FFI attributes cần phân biệt:

```text
verified compiler property
```

và:

```text
unsafe programmer assertion
```

Ví dụ:

```text
@ffi_pure
```

có thể là unsafe contract.

Compiler không coi đó là sự thật tuyệt đối nếu profile yêu cầu kiểm chứng.

---

# 36. FFI contracts

Tôi đề xuất internal model:

```text
FFI Contract
├── ABI
├── calling convention
├── parameter ownership
├── pointer validity
├── noescape
├── effects
├── return ownership
├── alignment
└── representation
```

Nhưng **không expose toàn bộ thành cú pháp**.

Compiler có thể lấy từ:

1. built-in platform declarations
2. generated bindings
3. attributes
4. unsafe extern declarations.

---

# 37. Generated bindings

Axiom nên có tool:

```text
axiom bindgen
```

Input:

```text
C headers
```

Output:

```text
Axiom FFI declarations
```

Ví dụ:

```text
libc.h
    ↓
axiom bindgen
    ↓
libc.axiom
```

Điều này cực kỳ quan trọng cho ecosystem.

---

# 38. Nhưng bindgen không phải compiler dependency

Final Axiom compiler vẫn có thể build project nếu bindings đã generated.

Do đó:

```text
C compiler
```

không phải dependency runtime của Axiom.

Có thể dùng Clang/libclang để **generate bindings**, nhưng Axiom không phụ thuộc vào nó để compile source cuối cùng.

---

# 39. C++ FFI

Không nên hứa:

```text
extern "C++"
```

trong Core v0.1.

C++ ABI:

- name mangling
- class layout
- exceptions
- templates
- vtables
- RTTI
- compiler-specific ABI

rất phức tạp.

Axiom nên hỗ trợ C++ qua:

```text
C wrapper
```

trước.

Sau này có thể có dedicated C++ ABI tooling.

---

# 40. OS APIs

Windows:

```text
Win32
```

Linux:

```text
syscall
libc
```

macOS:

```text
Darwin
```

không thuộc language Core.

Nhưng FFI phải đủ mạnh để gọi chúng mà không cần runtime Axiom lớn.

---

# 41. `no_std` / freestanding

Axiom nên có profile:

```text
hosted
freestanding
kernel
embedded
```

Ví dụ:

```axiom
@entry
fn _start() -> never {
    ...
}
```

có thể bypass standard startup.

Đây là một yêu cầu rất phù hợp với mục tiêu systems language.

---

# 42. Foreign memory

Axiom cần một abstraction:

```text
ExternalMemory<T>
```

nhưng **không nhất thiết là Core type**.

Ví dụ:

```text
mmap
device memory
shared memory
DMA buffer
foreign allocator
```

đều có thể tạo:

```text
view<T>
```

sau khi unsafe code chứng minh preconditions.

---

# 43. DMA/MMIO

Đây là trường hợp không được đánh đồng với normal RAM.

Ví dụ:

```text
volatile load/store
```

phải tồn tại ở system layer.

Compiler không được:

```text
cache
reorder
eliminate
```

volatile operation như ordinary memory nếu semantics cấm.

Nhưng volatile cũng không trở thành synchronization primitive.

---

# 44. FFI ownership model hoàn chỉnh

Ta có:

```text
Axiom owner
    │
    ├── pass by value
    │
    ├── view → borrowed foreign call
    │
    ├── mut_view → mutable foreign call
    │
    └── raw pointer → unsafe FFI
```

Foreign function có thể:

```text
BORROW
CONSUME
RETURN
RETAIN
UNKNOWN
```

Nếu compiler không biết:

```text
conservative
```

Nếu cần safe wrapper:

```text
explicit unsafe boundary
```

---

# 45. Một ví dụ hoàn chỉnh

C API:

```c
typedef struct image image;

image *image_open(const char *path);
void image_free(image *img);
const unsigned char *image_data(image *img, size_t *len);
```

Axiom binding thô:

```axiom
extern type CImage

extern "C" {
    unsafe fn image_open(path: *const u8) -> *mut CImage
    unsafe fn image_free(img: *mut CImage)
    unsafe fn image_data(
        img: *mut CImage,
        len: *mut usize
    ) -> *const u8
}
```

Safe wrapper:

```text
Image
 ├── owns *mut CImage
 ├── Drop → image_free
 └── data() → view<u8>
```

Application:

```axiom
let image = Image.open("photo.png")?
let pixels = image.data()?

process(pixels)
```

Application hoàn toàn không cần biết C pointer tồn tại.

Đây chính là mức abstraction Axiom nên hướng tới.

---

# 46. FFI invariants

Chốt thêm:

```text
AFFI-01   FFI ABI Is Explicit
AFFI-02   C ABI Is First-Class
AFFI-03   FFI Does Not Imply Unsafe Automatically
AFFI-04   Raw Foreign Pointers Are Not Safe Views
AFFI-05   Foreign Memory Requires Explicit Validation
AFFI-06   Safe Wrappers May Encapsulate Unsafe FFI
AFFI-07   @repr(C) Freezes C-Compatible Layout
AFFI-08   Non-FFI Layout Is Not C-Compatible
AFFI-09   Opaque Foreign Types Have No Assumed Layout
AFFI-10   Foreign Handles May Be Owned Resources
AFFI-11   Foreign Ownership Must Be Explicit
AFFI-12   Foreign Pointer Retention Must Not Be Assumed Safe
AFFI-13   FFI Escape Is Conservatively Analyzed
AFFI-14   FFI Effects Are Conservative By Default
AFFI-15   FFI Contracts May Refine Effects
AFFI-16   FFI Contracts Are Not Automatically Trusted
AFFI-17   C Strings Are Distinct From Text
AFFI-18   C Arrays Are Distinct From Axiom Arrays
AFFI-19   C Unions Require Explicit Representation
AFFI-20   C Variadics Are FFI-Only
AFFI-21   C++ ABI Is Not Core v0.1
AFFI-22   Callback ABI Is Explicit
AFFI-23   Capturing Closure Cannot Implicitly Become C Function Pointer
AFFI-24   Dynamic Symbol Loading Is Library-Level
AFFI-25   FFI Does Not Require Axiom Runtime
AFFI-26   Foreign Calls Preserve ABI Semantics
AFFI-27   Volatile FFI Access Is Not Atomic Synchronization
AFFI-28   Generated Bindings Are Build Artifacts, Not Compiler Dependencies
AFFI-29   Freestanding Code May Use FFI Directly
AFFI-30   Unsafe FFI Cannot Erase Axiom Type/Ownership State
```

---

# Kiến trúc FFI cuối cùng

```text
                  Axiom
                    │
             Safe Axiom API
                    │
             ┌──────┴──────┐
             │             │
          Axiom ABI      C ABI
             │             │
             │        ┌────┴────┐
             │        │         │
             │       libc      OS API
             │        │         │
             └────────┴─────────┘
                       │
                 Raw Machine ABI
```

Và ở memory boundary:

```text
Axiom Value
     │
     ├── view<T>
     │
     ├── mut_view<T>
     │
     └── raw pointer
             │
             ▼
        FOREIGN MEMORY
             │
       unsafe validation
             │
             ▼
        Axiom capability
```

Điểm quan trọng nhất: **Axiom không cần lựa chọn giữa “safe nhưng không thể làm systems programming” và “powerful nhưng mọi thứ unsafe”.** Safe abstraction có thể nằm trên một lớp FFI/unsafe rất mỏng.

---

## Tiếp tục → SIMD, vectorization và data-oriented computing

Bước tiếp theo sẽ xử lý **SIMD/vector types, auto-vectorization, AoS/SoA, alignment, cache locality, `restrict`-like alias information và cách Axiom đạt hiệu năng C/C++ mà không bắt programmer viết intrinsic cho mọi thứ**.

Đây cũng là bước cần nối trực tiếp với mục tiêu ban đầu của bạn: **hiệu năng mạnh mà ngôn ngữ vẫn đơn giản.**