# BOOTSTRAP-326 — AXIOM FOREIGN FUNCTION INTERFACE (FFI) & INTEROP CONTRACT ENGINE

## 1. Mục tiêu

Axiom phải có khả năng gọi và được gọi bởi:

- C
- C++
- Rust/Swift/Objective-C ở mức ABI phù hợp
- Win32 / POSIX / Linux syscall interface
- macOS/iOS frameworks
- Android NDK
- thư viện native `.dll/.so/.dylib/.a/.lib`
- GPU/driver APIs
- các component/plugin của Axiom
- code assembly hoặc foreign object code

nhưng **FFI không được phá vỡ semantic model của Axiom**.

Nguyên tắc:

> **FFI là một semantic boundary, không chỉ là một function-call syntax.**

Axiom không được giả định rằng foreign code tuân thủ ownership, aliasing, lifetime, panic, thread-safety hoặc ABI của Axiom.

---

# 2. Ba lớp phải tách biệt

FFI Engine phải phân biệt:

```text
Foreign Source API
        ↓
Foreign ABI
        ↓
Axiom FFI Contract
        ↓
Axiom Semantic Model
        ↓
Axiom ABI
```

Ví dụ C:

```c
void process(const float* data, size_t len);
```

không được tự động biến thành:

```axiom
fn process(data: view<f32>)
```

chỉ vì hai biểu diễn có vẻ tương đương.

Compiler phải có **FFI contract** mô tả chính xác:

```text
pointer
length
ownership
mutability
lifetime
nullability
alignment
aliasing
threading
calling convention
error convention
allocator
```

---

# 3. FFI declaration

Axiom cần một dạng declaration rõ ràng:

```axiom
extern "C" {
    fn process(data: *const f32, len: usize);
}
```

Raw pointer tại FFI boundary là hợp lệ vì đây là machine-level contract.

Nhưng API public phía trên nên được bọc:

```axiom
fn process(data: view<f32>) {
    unsafe {
        foreign_process(data.ptr(), data.len())
    }
}
```

Tức là:

```text
Foreign API
    ↓
unsafe adapter
    ↓
safe Axiom API
```

Đây phải là pattern chuẩn của ecosystem.

---

# 4. FFI contract

Compiler tạo:

```text
FfiContract
```

gồm tối thiểu:

```text
FfiContract {
    abi
    calling_convention

    parameters[]
    return_type

    ownership[]
    mutability[]
    lifetime[]
    nullability[]
    alignment[]

    layout_contract
    representation_contract

    allocator_contract
    panic_contract
    unwind_contract

    threading_contract
    async_contract

    callback_contract

    error_contract

    variadic_contract
    platform_contract

    safety_requirements
}
```

---

# 5. Pointer contract

Pointer không được chỉ mang type.

Ví dụ:

```text
*const T
```

chỉ nói rằng đây là pointer tới `T`.

FFI contract phải có thêm:

```text
PointerContract {
    nullable
    pointee
    alignment
    valid_for
    ownership
    mutation
    aliasing
    lifetime
}
```

Ví dụ:

```text
const pointer
non-null
aligned(T)
valid for N elements
borrowed
read-only
caller-owned
valid during call
```

---

# 6. Các ownership mode FFI

Chuẩn hóa:

```text
BorrowedRead
BorrowedWrite
OwnedInput
OwnedOutput
Transferred
Shared
OpaqueHandle
ForeignManaged
Static
Unknown
```

Ví dụ:

```c
void foo(const char* text);
```

có thể khai báo:

```text
BorrowedRead
valid during call
null forbidden
NUL terminated
```

Trong khi:

```c
char* create_buffer();
```

có thể là:

```text
OwnedOutput
allocator = ForeignAllocator
caller must release with foreign_free
```

Hai API nhìn giống nhau ở C nhưng semantic hoàn toàn khác.

---

# 7. String FFI

Axiom tuyệt đối không được tự động coi:

```text
String
```

là:

```text
char*
```

Phải hỗ trợ các representation:

```text
Utf8Slice
Utf8NulTerminated
Utf16Slice
Utf16NulTerminated
RawBytes
CStringCompatible
ForeignString
OpaqueString
```

Ví dụ:

```axiom
extern "C" {
    fn puts(s: *const u8);
}
```

không tự động biết `s` là UTF-8.

Contract phải xác định encoding.

---

# 8. Struct / enum FFI

Struct mặc định của Axiom vẫn có layout compiler-controlled.

Do đó:

```axiom
struct Point {
    x: f32,
    y: f32,
}
```

không được mặc định truyền trực tiếp sang C.

Phải dùng:

```axiom
@repr(C)
struct Point {
    x: f32,
    y: f32,
}
```

Compiler kiểm tra:

```text
size
alignment
field offsets
padding
calling convention
aggregate passing
return ABI
```

---

# 9. Enum FFI

Enum Axiom:

```axiom
enum ResultCode {
    Ok,
    Failed,
}
```

không mặc định tương đương C enum.

FFI boundary phải xác định:

```text
discriminant type
discriminant values
size
alignment
valid range
representation
```

Ví dụ:

```axiom
@repr(C, u32)
enum ResultCode {
    Ok = 0,
    Failed = 1,
}
```

---

# 10. Option / Result tại FFI

Không được tự động truyền:

```axiom
Option<T>
Result<T, E>
```

qua foreign ABI.

Ví dụ:

```axiom
fn find(...) -> Option<Handle>
```

nếu export sang C phải có ABI adapter:

```text
bool find(..., Handle* out);
```

hoặc contract representation tương đương.

Semantic API và ABI API được tách biệt.

---

# 11. Error model

Foreign function có thể biểu diễn lỗi bằng:

```text
return code
errno
GetLastError
null
sentinel
exception
out parameter
callback
thread-local error
```

FFI contract phải khai báo error convention.

Ví dụ:

```text
ErrorConvention {
    ReturnCode
    Errno
    LastError
    NullSentinel
    OutParameter
    Exception
    None
}
```

Axiom adapter có thể chuyển thành:

```axiom
Result<T, Error>
```

nhưng compiler không được tự suy đoán.

---

# 12. Panic / exception boundary

Không cho phép foreign exception hoặc Axiom panic tự động xuyên boundary.

Ví dụ:

```text
Axiom panic
    X
    foreign C++
```

và:

```text
C++ exception
    X
    Axiom safe function
```

Boundary phải có contract.

Nếu cần:

```text
extern "C++"
    noexcept
```

hoặc adapter:

```text
try foreign call
catch
convert error
```

C++ exception ABI là target/toolchain-specific.

---

# 13. Allocator boundary

Đây là invariant rất quan trọng.

Không được:

```text
Axiom allocate
    ↓
C free()
```

hoặc:

```text
C malloc()
    ↓
Axiom deallocate()
```

trừ khi allocator contract xác nhận tương thích.

Mỗi allocation domain phải được nhận diện:

```text
AxiomAllocator
CRTAllocator
OSAllocator
ForeignAllocator
CustomAllocator
Arena
GPUAllocator
Unknown
```

Ownership transfer qua FFI phải mang allocator contract.

---

# 14. Callback

Foreign code có thể gọi ngược Axiom:

```c
typedef void (*callback)(int);
```

Axiom cần:

```axiom
extern "C" type Callback = fn(i32);
```

Nhưng callback closure có capture:

```axiom
fn(x) { ... }
```

không được tự động biến thành C function pointer.

Chỉ:

```text
non-capturing function
```

mới có thể decay thành foreign function pointer nếu ABI tương thích.

Capturing closure phải dùng:

```text
callback function pointer
+
opaque context pointer
```

hoặc một FFI-generated trampoline.

---

# 15. Callback lifetime

Đây là nơi FFI rất dễ phá ownership.

Ví dụ:

```text
register_callback(cb)
```

không rõ callback được giữ bao lâu.

Contract phải xác định:

```text
CallOnly
BorrowedUntilReturn
StoredUntilUnregister
StoredForLifetime
AsyncCallback
ForeignOwned
```

Nếu foreign library giữ callback:

```text
Axiom compiler phải biết callback có thể escape.
```

Điều này ảnh hưởng:

- closure environment
- lifetime
- component lifetime
- thread safety
- unload safety
- hot reload

---

# 16. Threading contract

Foreign function phải có metadata:

```text
ThreadContract {
    thread_safe
    may_spawn
    may_callback
    callback_threads
    thread_affinity
}
```

Ví dụ một API chỉ được gọi trên main thread:

```text
MainThreadOnly
```

Compiler/runtime tooling phải có khả năng kiểm tra contract này.

---

# 17. Async FFI

Foreign async API không được giả định là Axiom `Future`.

Có thể là:

```text
callback
poll handle
event handle
OS completion port
file descriptor
IOCP
epoll
kqueue
Android callback
GPU event
```

FFI adapter chuyển thành:

```axiom
async fn
```

nhưng:

```text
ForeignAsyncHandle
```

và:

```text
Axiom Future
```

là hai semantic abstraction khác nhau.

---

# 18. Variadic functions

C:

```c
printf(const char*, ...);
```

không được coi là ordinary function.

Phải có:

```text
VariadicContract
```

và type checking đặc biệt.

Core chỉ hỗ trợ một tập ABI-safe variadic types.

Không cho phép tùy tiện:

```axiom
extern "C" fn foo(...);
```

với arbitrary Axiom types.

---

# 19. `extern type`

Foreign opaque object phải có semantic representation:

```axiom
extern type FILE;
extern type CGContext;
extern type VkDevice;
```

Compiler không biết layout.

Chỉ được sử dụng thông qua:

```text
opaque handle
pointer
reference contract
FFI function
```

Không được:

```axiom
sizeof(FILE)
```

nếu foreign type không cung cấp layout.

---

# 20. FFI-safe trait

Không phải mọi Axiom type đều được phép export.

Compiler cần:

```text
FfiSafe
```

và kiểm tra:

```text
primitive
repr(C) struct
repr(C) enum
transparent type
raw pointer
function pointer
opaque handle
```

Các loại mặc định không FFI-safe:

```text
String
Vec
closure
dyn Trait
generic type
Future
trait object
internal enum representation
compiler-private struct
```

trừ khi có explicit contract.

---

# 21. FFI boundary và verifier

Khi gặp:

```text
extern call
```

Verifier tạo:

```text
ForeignCallEffect
```

với các giả định từ contract.

Ví dụ:

```text
may_read
may_write
may_allocate
may_deallocate
may_block
may_panic
may_callback
may_spawn
may_escape
may_sync
may_io
```

Nếu contract không biết:

```text
Unknown
```

thì optimizer phải conservative.

**Không được coi foreign function là pure chỉ vì declaration trông đơn giản.**

---

# 22. Unsafe boundary

Một FFI declaration không nhất thiết phải làm toàn bộ chương trình unsafe.

Mô hình:

```text
unsafe foreign primitive
        ↓
verified adapter
        ↓
safe API
```

Ví dụ:

```axiom
unsafe extern "C" {
    fn c_memcpy(
        dst: *mut u8,
        src: *const u8,
        n: usize
    );
}
```

wrapper:

```axiom
fn copy(
    dst: mut_view<u8>,
    src: view<u8>
) {
    assert(dst.len >= src.len)

    unsafe {
        c_memcpy(...)
    }
}
```

Sau wrapper, caller không cần biết pointer tồn tại.

---

# 23. FFI contract artifact

`.axif` phải có section:

```text
FFI_CONTRACTS
```

bao gồm:

```text
foreign ABI
foreign symbols
calling conventions
layout contracts
ownership contracts
allocator domains
error contracts
panic/unwind contracts
callback contracts
thread contracts
async contracts
security requirements
target restrictions
```

Như vậy `.axif` trở thành nguồn thông tin chính cho:

```text
compiler
linker
IDE
optimizer
ABI checker
security analyzer
AI tooling
```

---

# 24. FFI verification

Trước codegen:

```text
FFI Declaration
      ↓
ABI Resolution
      ↓
Layout Verification
      ↓
Ownership Contract Verification
      ↓
Effect Contract Verification
      ↓
Target Verification
      ↓
Safety Contract Verification
      ↓
Verified Foreign Boundary
```

Không có:

```text
"compiler cứ generate code rồi hy vọng"
```

---

# 25. FFI adapter generation

Compiler nên có khả năng sinh adapter tự động khi contract đủ thông tin.

Ví dụ semantic API:

```axiom
fn read_file(path: String) -> Result<Buffer, IoError>
```

Foreign API:

```c
int read_file(
    const char* path,
    void* buffer,
    size_t size
);
```

Compiler/library tooling có thể generate:

```text
String
 ↓
UTF-8 conversion
 ↓
NUL termination
 ↓
foreign call
 ↓
error conversion
 ↓
Buffer ownership
 ↓
Result
```

Nhưng **chỉ tự động hóa khi contract chứng minh được tính đúng đắn**.

---

# 26. FFI và optimizer

Foreign calls là optimization barrier mặc định theo effect contract.

Nếu contract nói:

```text
pure
readonly
noalias
nothrow
nosync
```

compiler có thể tối ưu mạnh hơn.

Ví dụ:

```text
@ffi(pure, readonly)
```

cho phép:

- CSE
- LICM
- DCE
- constant propagation
- hoisting

Nhưng attribute phải được xem như **semantic contract**, không phải lời hứa tùy tiện của programmer.

Khai báo sai là lỗi ABI/safety contract.

---

# 27. FFI và `@noalias`

Không đưa `restrict` vào Core syntax.

Tuy nhiên FFI contract có thể biểu diễn:

```text
NoAlias
```

vì foreign API có thể yêu cầu nó.

Ví dụ:

```c
void foo(float * restrict a,
         float * restrict b);
```

Axiom adapter có thể encode:

```text
parameter[0].aliasing = NoAliasWith(parameter[1])
```

Verifier sử dụng thông tin này khi gọi foreign function.

---

# 28. FFI target database

`AbiDB` cần thêm:

```text
ForeignAbiDB
```

hỗ trợ:

```text
C
C++
System
Win64
SysV64
AArch64
ARM32
WASM
ObjC
Swift-compatible subset
VectorCall
ThisCall
FastCall
stdcall
GPU ABIs
```

Không phải mọi target đều hỗ trợ mọi ABI.

Resolver phải reject ngay ở compile time.

---

# 29. C header / binding generation

Axiom tooling nên hỗ trợ:

```text
axiom ffi import header.h
```

và:

```text
axiom ffi export module.ax
```

Sinh:

```text
Axiom declarations
FFI contracts
layout declarations
constants
enums
functions
opaque types
callbacks
```

Nhưng parser C/C++ header không nên trở thành compiler front-end khổng lồ.

Nó nên là **interop tool/plugin layer**.

---

# 30. FFI boundary diagnostics

Diagnostic phải nói rõ semantic vấn đề.

Ví dụ:

```text
AXFFI042:
foreign function may retain parameter 0,
but argument is a temporary view.

The foreign contract requires:
    lifetime = stored_until_unregister

The supplied value has:
    lifetime = call

Use an owned buffer or an explicit long-lived storage contract.
```

Hoặc:

```text
AXFFI017:
attempt to deallocate memory in Axiom allocator
that is owned by ForeignAllocator(CRT).

Use the foreign release function declared by the FFI contract.
```

Đây là điểm rất quan trọng để Axiom tránh biến FFI thành vùng "unsafe hell".

---

# 31. Compiler architecture

Thêm:

```text
compiler/ffi/
    contract/
        ffi_contract.ax
        pointer_contract.ax
        ownership_contract.ax
        allocator_contract.ax
        callback_contract.ax
        thread_contract.ax
        async_contract.ax
        error_contract.ax

    resolve/
        ffi_resolver.ax
        abi_resolver.ax
        symbol_resolver.ax
        layout_checker.ax

    verify/
        ffi_verifier.ax
        ownership_checker.ax
        lifetime_checker.ax
        effect_checker.ax
        callback_checker.ax

    adapter/
        adapter_generator.ax
        string_adapter.ax
        buffer_adapter.ax
        error_adapter.ax
        callback_adapter.ax

    import/
        header_import.ax
        binding_generator.ax

    diagnostics/
        ffi_diagnostics.ax

    metadata/
        ffi_axif.ax
```

CompilerDB:

```text
FfiDB
ForeignTypeDB
FfiContractDB
FfiSymbolDB
FfiAdapterDB
```

---

# 32. API chính

```text
resolve_ffi_declaration()
validate_ffi_contract()
resolve_foreign_abi()
validate_foreign_type()
validate_ffi_layout()
validate_ffi_ownership()
validate_ffi_effects()
validate_ffi_callback()
validate_ffi_thread_contract()
validate_ffi_async_contract()

generate_ffi_adapter()
generate_c_binding()
generate_ffi_metadata()

check_ffi_call()
check_ffi_export()
check_foreign_symbol()

explain_ffi_failure()
diff_ffi_contract()
```

CLI:

```text
axiom ffi inspect
axiom ffi check
axiom ffi diff
axiom ffi import
axiom ffi export
axiom ffi bindings
axiom ffi explain
```

---

# 33. Các invariant bắt buộc

```text
AFFI-01
Foreign ABI must be explicit.

AFFI-02
Foreign layout must never be inferred from Axiom layout.

AFFI-03
Foreign ownership must be explicit or conservatively Unknown.

AFFI-04
Allocator domains must never be crossed implicitly.

AFFI-05
Foreign exceptions must never cross an Axiom boundary implicitly.

AFFI-06
Axiom panic must never cross a foreign boundary implicitly.

AFFI-07
Foreign callbacks must have explicit lifetime semantics.

AFFI-08
Foreign retained pointers must have explicit escape semantics.

AFFI-09
Unknown foreign effects are conservatively assumed.

AFFI-10
FFI declarations do not disable the verifier.

AFFI-11
Unsafe FFI may establish trusted preconditions but cannot corrupt verifier state silently.

AFFI-12
Only FfiSafe representations may cross a safe FFI boundary.

AFFI-13
Opaque foreign types have no assumed layout.

AFFI-14
Axiom String is never implicitly equivalent to C string.

AFFI-15
Axiom Vec is never implicitly equivalent to foreign array ownership.

AFFI-16
Axiom closures are not automatically foreign function pointers.

AFFI-17
Generic Axiom representation is not automatically FFI-stable.

AFFI-18
Foreign ABI compatibility must be target-specific.

AFFI-19
FFI metadata must participate in .axif fingerprints.

AFFI-20
FFI contract violations are compile-time errors whenever statically decidable.

AFFI-21
Unproven foreign assumptions must never become optimizer facts.

AFFI-22
Generated FFI adapters must pass normal type, ownership, capability and effect verification.

AFFI-23
FFI boundaries must preserve source-to-machine provenance.

AFFI-24
FFI must work in freestanding builds without forcing a runtime.

AFFI-25
FFI must integrate with dynamic components and plugin ABI.

AFFI-26
FFI contracts must participate in component unload safety.

AFFI-27
FFI contracts must participate in GPU host/device boundary validation.

AFFI-28
FFI contract serialization must be deterministic.

AFFI-29
FFI compatibility must be checkable independently of code generation.

AFFI-30
Axiom must never silently guess foreign semantics.
```

---

# 34. Quan hệ với các subsystem trước

```text
ABI-324
   ↓
FFI-326
   ↓
Component-325
   ↓
Linker
Runtime
Security
Async
Concurrency
GPU
Optimizer
.axif
```

Đặc biệt:

### ABI 324
quyết định **binary representation**.

### FFI 326
quyết định **foreign semantic contract**.

### Component 325
quyết định **dynamic code/resource boundary**.

Ba lớp này không được trộn thành một subsystem.

---

# 35. Kiến trúc cuối cùng

Axiom nên đạt mô hình:

```text
                ┌───────────────┐
                │ Axiom Semantic│
                │     Model     │
                └───────┬───────┘
                        │
              ┌─────────┴─────────┐
              │                   │
        Axiom ABI            FFI Contract
              │                   │
              │            ┌──────┴──────┐
              │            │             │
        Axiom binary    C/C++/OS      GPU/Foreign
              │            │             │
              └────────────┴─────────────┘
                           │
                    Native Machine Code
```

Điểm quan trọng nhất của task này:

> **Axiom không cố làm cho foreign code "trở thành Axiom". Axiom xây một contract có kiểm chứng để foreign code có thể được sử dụng mà không phá semantic guarantees của Axiom.**

Đây sẽ là nền tảng để Axiom thực sự dùng được các thư viện native hiện có trong khi vẫn giữ được mô hình **ownership + capability + effect + ABI + safety** đã thiết kế.