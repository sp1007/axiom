Tiếp tục.

# Axiom — ABI Stability, FFI, Versioning & Binary Compatibility v0.1

Đây là nơi cần **rất dứt khoát**, vì nếu thiết kế sai ABI từ đầu thì sau này compiler bị trói vào layout/calling convention cũ và mất rất nhiều tự do tối ưu.

## 1. Quyết định lớn: không có Stable Axiom ABI mặc định

Tôi đề xuất khóa:

> **Axiom ABI mặc định là compiler-version/target dependent và không cam kết binary compatibility.**

Tức là:

```text
Axiom source
    ↓
Compiler v0.1
    ↓
Axiom ABI v0.1-internal
```

Compiler có toàn quyền thay đổi:

- register allocation;
- struct passing;
- return convention;
- closure representation;
- enum representation;
- generic instantiation;
- trait dispatch;
- calling convention nội bộ;
- symbol mangling;
- layout không được `repr` cố định.

Điều này cực kỳ quan trọng cho mục tiêu hiệu năng.

---

# 2. Tại sao không nên khóa ABI?

Ví dụ:

```axiom
struct Vec4 {
    x: f32
    y: f32
    z: f32
    w: f32
}
```

Compiler hôm nay có thể truyền:

```text
XMM0
XMM1
```

Ngày mai có thể:

```text
XMM0 + XMM1
```

hoặc scalarize:

```text
XMM0.x
XMM0.y
...
```

hoặc truyền qua stack.

Nếu Axiom ABI stable, compiler phải giữ các quyết định đó.

Nếu ABI internal:

> **semantic signature stable, physical calling convention tự do.**

---

# 3. Nhưng library binary thì sao?

Không thể yêu cầu người dùng compile toàn bộ thế giới mỗi lần.

Do đó Axiom cần **hai mô hình phân phối**.

### Model A — source/semantic package

```text
package → semantic artifact → compiler → native code
```

Đây là mặc định.

### Model B — stable binary boundary

```text
Axiom
   ↓
explicit ABI boundary
   ↓
C/system/stable ABI
   ↓
dynamic/static library
```

---

# 4. Stable ABI là explicit contract

Ví dụ:

```axiom
extern "C" fn process(x: CBuffer) -> CResult
```

thì compiler phải tuân thủ C ABI.

Không cần một “Axiom ABI stable” để làm việc này.

---

# 5. Nhưng plugin system thì C ABI hơi bất tiện

Đúng.

Do đó về sau có thể thêm:

```text
extern "axiom-stable"
```

nhưng đây phải là **một ABI versioned contract riêng**, không phải ABI mặc định.

Ví dụ:

```axiom
extern "axiom-stable-1"
pub fn plugin_init(api: PluginApi) -> Plugin
```

---

# 6. Stable ABI không được expose compiler internals

Sai lầm cần tránh:

```text
stable ABI
    ↓
Typed HIR
    ↓
MIR
```

Không.

Stable ABI chỉ định:

```text
types
layout
calling convention
symbol rules
error/return convention
versioning
```

Compiler vẫn được tự do optimize phía sau boundary.

---

# 7. ABI boundary

Kiến trúc:

```text
          Axiom internal world
                  │
                  │ arbitrary optimization
                  │
          ───── ABI boundary ─────
                  │
                  ↓
        stable representation
                  │
         C / system / plugin
```

ABI boundary là **semantic firewall**.

---

# 8. `repr(C)`

Đã có:

```axiom
@repr(C)
struct Point {
    x: f32
    y: f32
}
```

Điều này cam kết:

```text
C-compatible layout
```

nhưng **không biến toàn bộ Axiom struct thành C ABI**.

---

# 9. `repr(C)` chỉ giải quyết layout

Ví dụ:

```axiom
@repr(C)
struct Point {
    x: f32
    y: f32
}

extern "C"
fn draw(p: Point)
```

Hai thứ độc lập:

```text
@repr(C)
    → data representation

extern "C"
    → calling convention
```

Đây là thiết kế đúng.

---

# 10. `repr(transparent)`

Ví dụ:

```axiom
struct UserId(u64)
```

và:

```axiom
@repr(transparent)
struct UserId(u64)
```

ABI representation tương thích với `u64`.

Nhưng source type vẫn:

```text
UserId != u64
```

Điều này cực kỳ hữu ích cho FFI mà vẫn giữ type safety.

---

# 11. Opaque type

C library thường có:

```c
typedef struct Foo Foo;
```

Axiom:

```axiom
extern type Foo
```

Compiler không biết layout.

Chỉ biết:

```text
Foo = opaque foreign type
```

Không được:

```text
Foo { ... }
```

hoặc `size_of<Foo>()` nếu ABI không cung cấp kích thước.

---

# 12. Handle-based FFI

Ví dụ OS API:

```text
HANDLE
fd
socket
GPU object
```

không nên biến thành raw `usize` trong Axiom.

Có thể:

```axiom
struct FileHandle {
    raw: RawHandle
}
```

với:

```text
!Copy
Drop
```

và API wrapper.

Như vậy:

```text
C/OS handle
        ↓
Axiom resource type
```

---

# 13. Raw pointer ABI

Không tự động:

```text
*T → view<T>
```

ở FFI boundary.

Ví dụ:

```axiom
extern "C"
fn foo(data: *const u8, len: usize)
```

được phép.

Nhưng nếu muốn safe:

```axiom
fn foo_safe(data: view<u8>) -> Result<...>
```

wrapper phải kiểm tra:

- null;
- alignment;
- length;
- lifetime;
- provenance;
- ownership;
- thread access.

---

# 14. C string

Không được coi:

```text
Text == char*
```

Axiom giữ:

```text
Text
Bytes
CStr
CString
```

tách biệt.

Ví dụ:

```axiom
extern "C"
fn puts(s: *const u8)
```

wrapper:

```axiom
fn puts_safe(s: CStr)
```

---

# 15. Function pointer ABI

Một function pointer phải mang ABI identity.

Conceptually:

```text
fn(i32) -> i32
```

khác:

```text
extern "C" fn(i32) -> i32
```

vì calling convention khác.

Không được implicit convert.

---

# 16. Closure và FFI

Captureless closure:

```axiom
let f = |x: i32| x + 1
```

có thể chuyển thành function pointer **chỉ khi ABI tương thích**.

Capturing closure:

```axiom
let offset = 10
let f = |x| x + offset
```

không thể tự động biến thành:

```text
C function pointer
```

vì nó có environment.

Phải tạo trampoline/context rõ ràng.

---

# 17. ABI của closure không phải ABI public

Internal closure có thể là:

```text
fn_ptr + env_ptr
```

nhưng compiler có thể:

```text
inline
scalarize
eliminate
```

Stable ABI không được dựa vào representation này trừ khi một ABI contract explicit định nghĩa nó.

---

# 18. Trait ABI

Đây là điểm rất quan trọng.

```axiom
dyn Drawable
```

có thể conceptually:

```text
data pointer
dispatch pointer
```

nhưng **không được coi đó là stable Axiom ABI**.

Compiler có thể thay đổi:

```text
vtable layout
method ordering
metadata
dispatch representation
```

---

# 19. Static trait dispatch

```axiom
fn draw<T: Drawable>(x: T)
```

mặc định:

```text
monomorphization
```

Không có vtable.

Do đó:

```text
zero runtime dispatch
```

nếu optimizer có thể specialize.

---

# 20. Dynamic trait boundary

Nếu cần ABI stable plugin:

```text
PluginApi
```

không nên chỉ dùng:

```text
dyn Trait
```

mà nên định nghĩa một explicit ABI structure:

```text
data pointer
function pointers
ABI version
size
alignment
capabilities
```

Ví dụ conceptually:

```text
PluginApiV1 {
    version
    ctx
    create
    destroy
    process
}
```

---

# 21. Plugin ABI

Đề xuất architecture:

```text
Plugin
  │
  ├── ABI version
  ├── capabilities
  ├── function table
  └── opaque handles
```

Không để plugin phụ thuộc:

- Axiom private struct layout;
- compiler vtable;
- closure representation;
- generic ABI;
- internal allocator.

---

# 22. Vì sao function table tốt?

Plugin:

```text
plugin.dll
```

và host:

```text
app.exe
```

chỉ cần thống nhất:

```text
ABI contract
```

Không cần cùng compiler implementation.

---

# 23. Allocator boundary

Đây là một trong những nguồn crash phổ biến nhất của native library.

Không nên:

```text
Axiom module A allocates
        ↓
module B free()
```

nếu allocator không được đảm bảo tương thích.

Stable ABI nên quy định:

```text
create()
destroy()
```

cùng boundary.

Hoặc:

```text
alloc
realloc
free
```

cùng allocator domain.

---

# 24. `Text` / `Vec` không nên mặc định stable ABI

Một API:

```axiom
extern "axiom-stable"
fn get_names() -> Vec<Text>
```

không nên được cho phép tùy tiện.

Vì:

```text
Vec
Text
allocator
layout
Drop
```

đều có thể phụ thuộc compiler/runtime.

Stable boundary nên dùng:

```text
pointer + length
```

hoặc explicit ABI container.

---

# 25. Stable ABI buffer

Ví dụ:

```text
AbiSlice<T> {
    ptr
    len
}
```

nhưng đây là **ABI representation**, không phải `view<T>` semantic type.

Axiom safe wrapper có thể chuyển:

```text
AbiSlice<T>
    ↓ validation
view<T>
```

---

# 26. Stable ABI string

Có thể có:

```text
AbiStr {
    ptr
    len
    encoding
}
```

hoặc đơn giản hơn:

```text
AbiUtf8 {
    ptr
    len
}
```

với contract:

```text
UTF-8
non-null when len > 0
valid UTF-8
```

---

# 27. ABI versioning

Không dùng:

```text
version = 1
```

một cách đơn giản.

ABI identity nên gồm:

```text
ABI family
ABI major
ABI minor
target
architecture
endianness
pointer width
calling convention
representation contract
```

Conceptually:

```text
axiom-stable/1
x86_64
little-endian
system
```

---

# 28. Major vs minor

Ví dụ:

```text
stable ABI 1.0
```

→ `1.1`

có thể thêm field/function nếu contract quy định backward compatibility.

Nhưng:

```text
1.x → 2.x
```

có thể breaking.

---

# 29. Struct evolution

Stable ABI struct không được phép tùy tiện thay đổi layout.

Có hai kiểu.

### Frozen struct

```text
fixed layout
```

Thêm field:

```text
ABI breaking
```

### Extensible struct

Có:

```text
size
version
```

ở đầu:

```text
AbiConfig {
    size
    version
    ...
}
```

Host chỉ đọc phần mà nó biết.

---

# 30. Tôi khuyến nghị extensible ABI cho plugin

Ví dụ:

```text
PluginDescriptor {
    size
    abi_version
    flags
    init
    shutdown
}
```

Compiler có thể kiểm tra:

```text
provided size >= required prefix
```

---

# 31. Enum ABI

Axiom ADT:

```axiom
enum Result<T,E> {
    Ok(T)
    Err(E)
}
```

không stable layout mặc định.

Compiler có thể niche-optimize.

Nếu FFI:

```axiom
@repr(C)
enum ...
```

thì phải có explicit representation rules.

---

# 32. Không nên biến Axiom enum thành C enum

C enum:

```text
integer + named constants
```

Axiom enum:

```text
tag + payload variants
```

là hai semantic model khác nhau.

FFI enum phải có representation contract riêng.

---

# 33. Generic ABI

Đây là điểm tôi khuyên **không stable**.

```axiom
extern "axiom-stable"
fn foo<T>(x: T)
```

không nên cho phép trực tiếp.

Generic được specialize bởi compiler.

Nếu cần ABI stable:

```text
non-generic ABI wrapper
```

Ví dụ:

```text
foo_i32
foo_f32
foo_buffer
```

hoặc dynamic descriptor.

---

# 34. Vì sao?

Nếu stable generic ABI tồn tại, compiler phải quyết định:

- type metadata;
- monomorphization;
- layout;
- calling convention;
- symbol identity.

Điều đó đi ngược mục tiêu:

> Generic abstraction should erase.

---

# 35. Generic vẫn có thể dùng trong implementation

```text
stable wrapper
      ↓
generic internal implementation
      ↓
optimized machine code
```

Đây là mô hình tốt nhất.

---

# 36. Symbol mangling

Axiom internal symbol:

```text
foo<T>
```

có thể được mangled thành bất kỳ tên nào.

Không cam kết.

Nếu cần stable:

```axiom
@export("plugin_process")
extern "C"
fn process(...)
```

Tên linker được explicit.

---

# 37. Symbol versioning

Dynamic systems có thể hỗ trợ:

```text
plugin_process@AXIOM_1
```

nhưng symbol-versioning syntax không nên nằm trong Core.

Nó thuộc:

```text
target linker layer
```

---

# 38. Binary compatibility

Ta nên phân biệt:

```text
Source Compatibility
Semantic Compatibility
ABI Compatibility
Binary Compatibility
Behavioral Compatibility
```

Không được gọi tất cả là “compatible”.

---

# 39. Ví dụ

Thay implementation:

```text
O(n²) → O(n log n)
```

có thể:

```text
Source compatible
ABI compatible
Behaviorally compatible
```

nhưng performance khác.

Compiler không coi performance là semantic compatibility.

---

# 40. Compiler version

Axiom package mặc định:

```text
source/semantic artifact
```

nên compiler v0.5 có thể compile lại.

Binary artifact:

```text
Axiom native binary
```

không nhất thiết chạy được với ABI của compiler v0.6 nếu nó phụ thuộc dynamic Axiom runtime.

---

# 41. Runtime ABI cũng phải versioned

Nếu runtime component:

```text
allocator
async
panic unwind
reflection
```

có ABI giữa binary modules, phải có version contract.

Nhưng tốt nhất:

> Runtime components được static link/dead-strip mặc định.

Như vậy vấn đề nhỏ hơn.

---

# 42. Dynamic runtime

Nếu người dùng muốn:

```text
libaxiom_runtime.so
```

thì đây là một explicit deployment model.

Không phải default.

---

# 43. Hot reload

Hot reload không nên dựa vào arbitrary Axiom internal ABI.

Có:

```text
HotReload ABI
```

riêng.

Ví dụ:

```text
module_init
module_update
module_shutdown
```

với explicit state serialization/migration.

---

# 44. Đây là một insight quan trọng

**Hot reload không phải consequence của dynamic linking.**

Dynamic linking chỉ giải quyết:

```text
load code dynamically
```

Hot reload còn cần:

```text
state ownership
state migration
ABI stability
function pointer replacement
resource lifetime
```

Do đó tách chúng.

---

# 45. FFI safety

FFI boundary nên được compiler đánh dấu:

```text
FFI_ENTER
FFI_EXIT
```

để verifier biết:

```text
unknown foreign behavior
```

Compiler mặc định conservative.

Ví dụ foreign function có thể:

- mutate memory;
- retain pointer;
- call callback;
- spawn thread;
- throw C++ exception;
- longjmp.

Axiom không được giả định foreign code “hiền”.

---

# 46. FFI contract

Có thể cung cấp explicit contract:

```text
@ffi(noescape)
@ffi(readonly)
@ffi(noreturn)
```

nhưng tôi đề xuất **không mở rộng thành hàng chục source annotations trong v0.1**.

Ban đầu:

```text
safe wrapper
+
unsafe implementation
```

là đủ.

---

# 47. `extern "C"` không tự động unsafe

Giữ quyết định trước:

```text
extern "C"
```

chỉ nói:

> calling convention + ABI.

Không nói:

> operation unsafe.

Ví dụ:

```axiom
extern "C"
fn strlen(s: CStr) -> usize
```

có thể có safe wrapper.

---

# 48. `unsafe` là safety contract, ABI là representation contract

Đây là hai trục độc lập:

```text
               ABI
                │
        C ──────┼────── Axiom
                │
                │
Safety ─────────┼────────
safe            │       unsafe
```

Không được gộp.

---

# 49. Stable ABI nên có package declaration

Ví dụ conceptually:

```toml
[abi]
kind = "axiom-stable"
version = "1"
```

hoặc:

```axiom
@abi("axiom-stable-1")
```

Tôi nghiêng về **attribute tại boundary declaration**, vì ABI là property của declaration.

---

# 50. ABI compatibility checker

CLI:

```text
axiom abi-check old.axabi new.axabi
```

Có thể kiểm tra:

```text
function added
function removed
parameter changed
return changed
layout changed
alignment changed
calling convention changed
symbol changed
enum changed
```

---

# 51. ABI artifact

Package stable ABI có thể xuất:

```text
libfoo.so
foo.axabi
foo.axdoc
```

`foo.axabi` là machine-readable ABI description.

Nó không cần chứa compiler internals.

---

# 52. AI tooling được hưởng lợi trực tiếp

AI agent có thể hỏi:

```text
query abi Foo
query api Foo
query layout Foo
query symbol process
```

và nhận semantic facts thay vì phải đọc hàng nghìn dòng source.

---

# 53. Quyết định cuối cùng

Tôi đề xuất đóng băng:

```text
DEFAULT AXIOM ABI
    unstable
    compiler-controlled
    target-dependent

STABLE ABI
    explicit
    versioned
    representation-constrained

C ABI
    explicit

SYSTEM ABI
    explicit
```

---

# 54. ABI invariants

```text
AABI-41  Default Axiom ABI Is Not Stable
AABI-42  Compiler May Optimize Across Internal ABI Boundaries
AABI-43  Stable ABI Requires An Explicit Contract
AABI-44  ABI Stability Is Independent Of Source Visibility
AABI-45  repr(C) Controls Representation, Not Calling Convention
AABI-46  Calling Convention Is An Explicit ABI Property
AABI-47  repr(transparent) Preserves Distinct Source Type Identity
AABI-48  Opaque Foreign Types Have Unknown Internal Layout
AABI-49  Raw FFI Pointers Do Not Implicitly Become Safe Views
AABI-50  Closure Representation Is Not Stable ABI
AABI-51  Trait Dispatch Representation Is Not Stable ABI
AABI-52  Generic Axiom ABI Is Not Stable By Default
AABI-53  Stable ABI Genericity Requires Explicit Erased Representation
AABI-54  Linker Symbol Names Are Separate From Source Symbol Identity
AABI-55  Explicit Export Names Are Stable Only Under Their ABI Contract
AABI-56  Stable ABI Containers Must Define Ownership And Allocation
AABI-57  ABI Struct Evolution Requires An Explicit Compatibility Policy
AABI-58  Extensible ABI Structs Use Version/Size Contracts
AABI-59  Axiom ADTs Are Not Automatically C Enums
AABI-60  ABI Versioning Is Explicit
AABI-61  Major ABI Changes May Be Breaking
AABI-62  ABI Artifacts Are Machine-Readable
AABI-63  ABI Compatibility Is Independently Checkable
AABI-64  FFI Safety And ABI Representation Are Independent
AABI-65  Foreign Calls Are Conservative By Default
AABI-66  Stable ABI Does Not Expose Compiler Internals
AABI-67  Runtime ABI Is Versioned Separately
AABI-68  Hot Reload Requires Its Own Explicit ABI Contract
AABI-69  Dynamic Linking Does Not Imply Hot Reload
AABI-70  ABI Boundaries Preserve Internal Optimization Freedom
```

---

# 55. Bức tranh Axiom hiện tại

Đến đây kiến trúc đã khá rõ:

```text
                    AXIOM SOURCE
                         │
          ┌──────────────┴──────────────┐
          │                             │
       Semantic                    Attributes
          │                             │
          ↓                             ↓
        Typed HIR ──────────────── ABI contracts
          │
          ↓
       Verified MIR
          │
          ↓
      Optimization
          │
          ↓
       ABI MIR
          │
          ↓
        Axiom LIR
          │
          ↓
      Machine Code
```

Ở boundary:

```text
                   Axiom internal ABI
                         │
               ┌─────────┼─────────┐
               │         │         │
               ↓         ↓         ↓
             C ABI    System ABI  Stable ABI
               │         │         │
               └─────────┴─────────┘
                         ↓
                    native world
```

Đây là điểm cân bằng rất tốt giữa:

- **performance**
- **compiler freedom**
- **FFI**
- **dynamic libraries**
- **plugin**
- **binary distribution**
- **self-hosting**

mà không bắt compiler phải mang gánh nặng ABI ổn định vĩnh viễn.

---

# Tiếp tục: phần kế tiếp

Phần tiếp theo nên khóa một vấn đề còn **quan trọng hơn ABI**:

## **Concurrency + Threading + Parallelism Model hoàn chỉnh**

Không chỉ `Thread` và `async`, mà phải quyết định toàn bộ:

```text
thread
spawn
join
detach
Send
Share
Mutex
RwLock
atomic
channel
scope
structured concurrency
thread-local
work stealing
thread pool
parallel for
SIMD vs parallelism
async vs thread
cancellation
panic trong thread
resource cleanup
```

Đặc biệt cần giải quyết một câu hỏi lớn của Axiom:

> **Axiom có nên đưa `spawn`, `parallel`, `join`, `channel` vào Core syntax, hay chỉ giữ một mô hình concurrency cực nhỏ và để thư viện xây toàn bộ abstraction phía trên?**

Với mục tiêu của bạn là **không nhất thiết phải làm core nhỏ**, tôi sẽ đánh giá vấn đề này theo **chi phí compiler + chi phí runtime + ergonomics + khả năng tối ưu**, thay vì mặc định “càng ít core càng tốt”.