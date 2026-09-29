# BOOTSTRAP-192 — Interoperability, C ABI, C++, Objective-C, Swift, Rust, WASM & Foreign Boundaries

**TRẠNG THÁI: FROZEN / COMPLETED**

## 192.1. Nguyên tắc trung tâm

Axiom phải có khả năng bước vào thế giới C/C++/OS/native hiện tại mà **không kéo mô hình bộ nhớ của các ngôn ngữ đó vào Core**.

> **FFI là một semantic boundary, không phải một loại code đặc biệt làm mất toàn bộ safety của Axiom.**

Do đó:

```text
Axiom Safe Code
      │
      ▼
FFI Boundary
      │
      ├── ABI Contract
      ├── Ownership Contract
      ├── Capability Contract
      ├── Thread Contract
      ├── Error Contract
      └── Representation Contract
      │
      ▼
Foreign Code
```

Điểm rất quan trọng:

**Không phải cứ gọi C là toàn bộ hàm gọi trở thành `unsafe`.**

Thay vào đó, phần nguy hiểm được cô lập trong **FFI contract/wrapper**.

---

# 192.2. `extern` — khai báo ABI, không phải unsafe

Ví dụ:

```axiom
extern "C" fn strlen(s: *const u8) -> usize;
```

`extern "C"` chỉ nói:

> Hàm này sử dụng C ABI.

Nó **không tự động nói rằng hàm an toàn**.

Axiom phân biệt:

```text
ABI
≠
Safety
≠
Ownership
≠
Error semantics
```

Do đó có thể có:

```axiom
extern "C" fn foo(...) -> ...;
```

và một wrapper:

```axiom
fn foo_safe(...) -> Result<..., Error> {
    ...
}
```

Phần application chủ yếu sử dụng wrapper an toàn.

---

# 192.3. FFI Contract

Axiom bổ sung một semantic object:

```text
FfiContract
```

Contract có thể mô tả:

```text
ABI
Calling convention
Parameter representation
Return representation
Ownership
Borrow/capability
Nullability
Alignment
Validity
Thread safety
Send
Share
Error convention
Panic/exception behavior
Callback lifetime
Reentrancy
```

Ví dụ conceptually:

```axiom
@ffi(
    abi = "C",
    consumes = 0,
    returns_owned = true,
    nullable = false
)
extern "C" fn create() -> *mut Foo;
```

Nhưng đây là **FFI metadata**, không biến raw pointer thành safe Axiom ownership một cách tự động.

Muốn tạo ownership:

```text
raw foreign value
      ↓
validated boundary
      ↓
Axiom-owned abstraction
```

---

# 192.4. Raw pointer chỉ tồn tại ở boundary/system layer

Axiom Core vẫn giữ:

```axiom
*const T
*mut T
```

nhưng đây là machine-level unsafe representation.

Application code không cần viết:

```axiom
*p
p + 1
```

thường xuyên.

Thay vào đó:

```axiom
struct CString {
    ...
}
```

hoặc:

```axiom
struct File {
    ...
}
```

và wrapper xử lý pointer.

Mục tiêu:

> **C có thể dùng pointer; Axiom programmer không cần sống trong pointer world.**

---

# 192.5. Ownership của foreign memory

Đây là phần quan trọng nhất.

Axiom không được giả định:

```text
foreign pointer → owned
```

hay:

```text
foreign pointer → borrowed
```

một cách tự động.

Có các trạng thái:

```text
ForeignBorrowed
ForeignOwned
ForeignShared
ForeignOpaque
ForeignUnknown
```

Ví dụ API C:

```c
char* foo_create();
void foo_destroy(char*);
```

Wrapper có thể biến thành:

```axiom
struct Foo {
    handle: ...
}

impl Drop for Foo {
    fn drop(self) {
        foo_destroy(self.handle)
    }
}
```

Lúc này Axiom biết:

```text
Foo owns foreign resource
Foo is !Copy
Move transfers ownership
Drop calls foo_destroy
```

Compiler có thể áp dụng toàn bộ ownership machinery bình thường.

---

# 192.6. Foreign borrowed data

C API:

```c
const char* foo_name(Foo*);
```

không nên map thành:

```axiom
fn name(...) -> String
```

nếu API thực tế trả borrowed memory.

Wrapper nên biểu diễn:

```axiom
fn name(self: view<Foo>) -> Str
```

với contract:

```text
returned Str
    ↓
depends on Foo
```

Compiler giữ provenance.

Do đó:

```axiom
let name = foo.name();
drop(foo);
use(name);
```

bị reject nếu `name` thực sự phụ thuộc vào `foo`.

Đây chính là cách Axiom **bảo vệ programmer khỏi lifetime của C mà không yêu cầu programmer viết lifetime**.

---

# 192.7. Foreign mutable memory

C:

```c
void foo_get_buffer(Foo*, uint8_t** data, size_t* len);
```

Không được tự động tạo `mut_view<u8>`.

Boundary phải chứng minh:

```text
pointer valid
length valid
alignment valid
region owned by Foo
no conflicting access
lifetime tied to Foo
```

Sau đó wrapper có thể cung cấp:

```axiom
fn buffer(self: mut_view<Foo>) -> mut_view<u8>
```

Compiler tiếp tục kiểm tra capability như mọi API Axiom khác.

---

# 192.8. Foreign nullability

Không có:

```axiom
null
```

trong safe Core.

Nếu C API có nullable pointer:

```c
Foo* find(...);
```

wrapper nên chuyển thành:

```axiom
fn find(...) -> Option<FooView>
```

hoặc:

```axiom
Option<OwnedFoo>
```

tùy ownership contract.

Raw nullable pointer chỉ tồn tại ở boundary.

---

# 192.9. C strings

Không biến C string thành `String` tự động.

Phân biệt:

```text
Bytes
Str
String
CString
CStr
```

Ví dụ:

```text
String
   ↓ validate/encode
CString
   ↓
*const c_char
```

và ngược lại:

```text
*const c_char
   ↓ validate
CStr
   ↓
Str
```

UTF-8 validity phải được kiểm tra nếu chuyển sang `Str`.

---

# 192.10. C ABI representation

Axiom:

```axiom
@repr(C)
struct Foo {
    ...
}
```

có nghĩa:

- field layout C-compatible
- alignment C-compatible
- ABI classification phù hợp
- không field reordering tùy ý
- không niche/layout optimization phá vỡ C contract

Nhưng:

```axiom
@repr(C)
```

**không biến mọi type thành FFI-safe**.

Ví dụ ownership-bearing:

```text
String
Vec<T>
Arc<T>
closure
dyn Trait
```

không tự động trở thành C-compatible.

Phải có explicit FFI representation.

---

# 192.11. `FfiSafe`

Axiom có semantic trait/capability:

```text
FfiSafe<ABI>
```

Compiler có thể kiểm tra:

```text
primitive
@repr(C) struct
@repr(C) enum with valid contract
transparent newtype
raw pointer
extern function pointer
```

nhưng reject những type không có ABI contract rõ ràng.

`FfiSafe` không phải runtime interface.

---

# 192.12. C callbacks

Callbacks là nơi lifetime rất dễ sai.

C:

```c
register_callback(callback, user_data);
```

Axiom không cho phép đơn giản:

```axiom
register_callback(|| ...)
```

nếu C giữ callback lâu hơn lifetime của closure.

Compiler yêu cầu contract xác định:

```text
CALL_DURATION
CALLBACK_STORED
CALLBACK_THREAD
CALLBACK_CANCEL
```

Hai trường hợp:

### Synchronous callback

```text
register()
 └── callback được gọi trước khi return
```

có thể borrow trực tiếp.

### Stored callback

```text
register()
    ↓
C giữ callback
    ↓
callback sau này
```

phải có ownership mechanism:

```text
OwnedCallback
Arc
static callback
opaque context
explicit unregister
```

---

# 192.13. Callback lifetime dependency

Nếu foreign API giữ:

```text
callback + user_data
```

thì Axiom semantic model tạo dependency:

```text
ForeignRegistration
 ├── owns callback
 └── owns context
```

Khi registration bị Drop:

```text
unregister
→ callback no longer reachable
→ context can be dropped
```

Điều này cho phép compiler tránh:

```text
foreign callback → dangling closure environment
```

---

# 192.14. Foreign threads

Foreign library có thể tạo thread mà Axiom không biết.

Do đó:

```text
extern function
```

không mặc định được coi là:

```text
single-threaded
```

hay:

```text
thread-safe
```

FFI contract phải mô tả.

Ví dụ:

```text
ThreadSafe
Reentrant
MaySpawnThreads
CallsCallbackOnForeignThread
```

Nếu callback chạy trên foreign thread:

```text
Axiom callback
      ↓
foreign execution domain
      ↓
Send/Share verification
```

---

# 192.15. Foreign exceptions / C++ exceptions

Axiom **không đưa exception model vào Core**.

C++:

```text
throw
catch
```

không được phép xuyên qua Axiom ABI boundary mặc định.

Boundary phải chuyển:

```text
C++ exception
      ↓
foreign adapter
      ↓
Result<T, ForeignError>
```

Hoặc terminate nếu contract yêu cầu.

Tương tự Axiom panic không được mặc định xuyên sang C++.

---

# 192.16. C++ interoperability

C++ phức tạp hơn C vì có:

```text
classes
virtual functions
templates
exceptions
RTTI
constructors/destructors
overloading
operator overloading
multiple inheritance
ABI variation
```

Axiom **không cố map C++ type system trực tiếp vào Core**.

Thay vào đó:

```text
Axiom
 ↓
C-compatible shim / generated binding
 ↓
C++
```

hoặc explicit C++ ABI adapter khi platform/toolchain hỗ trợ.

Khuyến nghị:

> **C ABI là stable baseline. C++ ABI là platform/toolchain-specific interoperability layer.**

---

# 192.17. C++ classes

Một C++ class:

```text
class Foo
```

được nhìn từ Axiom như:

```text
opaque foreign type Foo
```

Ví dụ:

```axiom
extern "C++" type Foo;
```

Axiom không cần hiểu toàn bộ layout nội bộ.

Methods được expose qua adapter:

```text
Foo_create
Foo_destroy
Foo_get
Foo_set
```

hoặc C++ ABI binding có metadata tương ứng.

---

# 192.18. Virtual dispatch

C++ virtual function:

```text
Foo::draw()
```

không trở thành Axiom trait implementation tự động.

Nếu cần:

```text
foreign virtual interface
```

được biểu diễn như opaque ABI contract.

Ngược lại:

```axiom
trait Drawable
```

không tự động tạo C++ vtable.

Điều này giữ Core sạch.

---

# 192.19. Rust interoperability

Rust ABI ngoài `extern "C"` không nên được coi là stable mặc định.

Do đó baseline:

```text
Axiom ↔ Rust
        ↓
     C ABI
```

hoặc explicit agreed Axiom ABI trong tương lai.

Ownership của Rust object phải được wrapper mô tả rõ:

```text
create
borrow
clone
destroy
send
share
```

---

# 192.20. Swift / Objective-C

Tương tự:

```text
Axiom
 ↓
C ABI / Objective-C ABI / Swift C-compatible interface
```

Objective-C object ownership có:

```text
retain
release
autorelease
```

Axiom không giả định ARC semantics là ownership semantics của mình.

Adapter phải biến chúng thành:

```text
OwnedForeignObject
BorrowedForeignObject
```

và Drop/release tương ứng.

Swift value/reference semantics cũng không được map tự động thành Axiom `Copy`/`Move`.

---

# 192.21. WASM

WASM được chia thành hai lớp:

```text
Axiom Core
   ↓
WASM Core ABI
```

và:

```text
WASM Component / Interface boundary
```

Không được giả định rằng:

```text
Axiom pointer
```

có ý nghĩa giống nhau giữa mọi WASM host.

Memory:

```text
linear memory
```

là một storage domain đặc biệt.

Axiom compiler phải biết:

```text
WasmLinearMemory
WasmTable
WasmFunctionReference
HostImport
HostExport
```

---

# 192.22. WASM pointer model

Trong WASM:

```text
pointer = integer-like offset
```

nhưng Axiom semantic pointer provenance vẫn được duy trì.

Không được cho phép:

```axiom
usize → arbitrary safe pointer
```

chỉ vì WASM representation là integer.

Machine representation và semantic validity vẫn tách biệt.

---

# 192.23. WASM host calls

Host function:

```text
host.read(...)
```

được coi là foreign effect.

Compiler biết:

```text
IO
External
MayPanic
MayBlock
MayAllocate
```

nếu contract khai báo.

Điều này ảnh hưởng:

```text
optimization
async
effects
determinism
comptime
```

---

# 192.24. Dynamic libraries

Axiom hỗ trợ:

```text
Static library
Dynamic library
Shared object
DLL
Framework
Bundle
WASM module
```

Dynamic symbol không chỉ là:

```text
address
```

mà có capability:

```text
LibraryHandle
   └── SymbolHandle
```

`SymbolHandle` giữ dependency tới library.

Không thể:

```text
unload(library)
call(symbol)
```

mà không bị compiler/runtime contract phát hiện.

---

# 192.25. Dynamic loading + ownership

Concept:

```text
lib = load("foo")
sym = lib.symbol("foo")
```

`SymbolHandle` phụ thuộc:

```text
lib
```

Nếu:

```text
drop(lib)
```

trong khi `sym` còn sống → reject hoặc buộc compiler giữ library alive tùy API semantics.

Đây là ví dụ tốt cho nguyên tắc:

> **Capability dependency không chỉ dành cho memory; nó áp dụng cho external resources.**

---

# 192.26. System calls

System call không phải FFI thông thường ở semantic level.

Axiom system layer có:

```text
std::os::<platform>
std::sys::<platform>
```

và compiler hiểu một số primitive:

```text
syscall
interrupt
memory mapping
atomic primitive
TLS
CPU intrinsic
```

nhưng chúng vẫn nằm ngoài Safe Core.

---

# 192.27. ABI layering

Axiom có các tầng:

```text
Axiom ABI
C ABI
System ABI
Platform ABI
WASM ABI
Foreign ABI
```

Compiler không được trộn chúng.

Ví dụ:

```text
Axiom struct
   ↓ ABI lowering
C struct
   ↓
native code
```

ABI lowering xảy ra **sau semantic verification**.

---

# 192.28. FFI effect system

Foreign call có thể mang:

```text
Effect:
    Read
    Write
    IO
    Allocate
    Deallocate
    Atomic
    Synchronize
    Panic
    Foreign
    Callback
    Thread
```

Compiler không được coi foreign function là pure nếu không có contract.

Điều này ngăn optimizer biến:

```axiom
foo();
foo();
```

thành:

```axiom
foo();
```

chỉ vì return value không được sử dụng.

---

# 192.29. FFI purity

Cho phép explicit:

```axiom
@pure
extern "C" fn ...
```

nhưng annotation phải có cơ chế xác minh/trust boundary thích hợp.

Không nên có:

```text
@pure
```

như một lời nói dối có thể phá semantics.

Đối với foreign code không thể chứng minh, compiler mặc định conservative.

---

# 192.30. FFI wrapper generation

Đây sẽ là một điểm rất mạnh của Axiom.

Từ metadata:

```text
C header
C++ header
Objective-C header
WASM interface
```

tool có thể sinh:

```text
raw binding
    ↓
validated binding
    ↓
idiomatic Axiom wrapper
```

Ví dụ:

```text
libfoo.h
   ↓
ax bind
   ↓
foo.raw.ax
foo.ax
```

Application chỉ sử dụng:

```axiom
Foo
Result<T, FooError>
Str
view<T>
mut_view<T>
```

thay vì pointer/API rối rắm.

---

# 192.31. Foreign memory validation

Một foreign pointer chỉ có thể đi từ:

```text
Unknown
```

sang:

```text
Validated Capability
```

khi contract cung cấp đủ:

```text
validity
alignment
size
provenance
access
lifetime
```

Không có:

```text
"compiler tin tôi vì đây là FFI"
```

Unsafe boundary vẫn phải tạo semantic precondition rõ ràng.

---

# 192.32. `unsafe` tại FFI boundary

Thiết kế cuối cùng:

```text
Raw FFI
    ↓
unsafe adapter
    ↓
safe validated abstraction
    ↓
ordinary Axiom
```

Ví dụ application có thể hoàn toàn safe:

```axiom
let image = Image.load(path)?;
let pixels = image.pixels();
process(pixels);
```

Trong khi bên dưới:

```text
C API
pointer
malloc
callback
foreign lifetime
```

đã được cô lập.

Đây chính xác là mục tiêu:

> **Unsafe should be concentrated, not propagated.**

---

# 192.33. FFI boundary không làm mất verifier

Sau khi adapter tạo:

```text
Owned<T>
view<T>
mut_view<T>
Send<T>
Share<T>
```

compiler quay lại verifier bình thường.

Do đó:

```text
unsafe
 ↓
trusted contract
 ↓
safe semantic object
 ↓
ownership/capability verification resumes
```

Không có “vùng mù” kéo dài xuyên chương trình.

---

# 192.34. FFI ABI compatibility

Mỗi ABI-facing declaration có:

```text
AbiFingerprint
```

bao gồm:

```text
ABI
calling convention
parameter layout
return layout
struct repr
alignment
enum representation
symbol name
linkage
target
```

Nếu ABI thay đổi:

```text
binary incompatibility
```

phải được phát hiện.

---

# 192.35. FFI và package manager

FFI package có thể khai báo:

```text
native library
headers
link mode
library search
target conditions
ABI
SDK requirement
system framework
```

Ví dụ:

```text
Windows → foo.dll
Linux   → libfoo.so
macOS   → Foo.framework
iOS     → Foo.framework
```

Nhưng package manager không được biến system library thành package runtime giả.

---

# 192.36. FFI và reproducible build

Foreign dependencies phải tham gia build identity:

```text
header hash
ABI metadata
SDK version
native library identity
link flags
target
```

Nếu header thay đổi:

```text
binding fingerprint thay đổi
```

→ incremental compiler biết phần nào cần rebuild.

---

# 192.37. C ABI là interoperability baseline

Chốt:

```text
Axiom ↔ C
```

là tầng tương thích quan trọng nhất.

Các ngôn ngữ khác:

```text
C++       → C / explicit ABI adapter
Rust      → C / explicit ABI
Swift     → C / platform ABI
Objective-C → C / ObjC ABI
WASM      → WASM ABI / Component boundary
OS        → platform ABI
GPU       → GPU ABI
```

Điều này giảm đáng kể độ phức tạp Core.

---

# 192.38. Những thứ KHÔNG đưa vào Core

Không đưa vào Core:

- C++ exception model
- C++ inheritance
- Objective-C ARC
- Swift ARC
- Rust lifetime syntax
- Rust borrow syntax
- JNI-like universal object model
- universal foreign object
- universal FFI pointer abstraction
- implicit foreign ownership
- implicit foreign synchronization
- implicit foreign exception conversion
- implicit foreign string conversion

Tất cả nằm ở interoperability layer.

---

# 192.39. Invariants — BOOTSTRAP-192

### `AFFI-20`
FFI ABI selection shall be explicit.

### `AFFI-21`
ABI compatibility shall be distinct from semantic safety.

### `AFFI-22`
Foreign pointers shall not implicitly become Axiom ownership.

### `AFFI-23`
Foreign memory shall require an explicit ownership/capability contract before safe access.

### `AFFI-24`
Safe Axiom views crossing FFI boundaries shall preserve provenance and validity.

### `AFFI-25`
Unknown foreign aliasing shall never be treated as disjoint.

### `AFFI-26`
Foreign nullable pointers shall not become safe null values.

### `AFFI-27`
C strings shall remain distinct from Axiom UTF-8 strings.

### `AFFI-28`
Foreign callbacks shall have explicit lifetime semantics.

### `AFFI-29`
Foreign callback execution domains shall be explicit when they can execute asynchronously.

### `AFFI-30`
Foreign exceptions shall not cross Axiom boundaries implicitly.

### `AFFI-31`
Axiom panic shall not cross foreign ABI boundaries implicitly.

### `AFFI-32`
Foreign calls shall be conservatively modeled for effects unless a valid contract establishes stronger facts.

### `AFFI-33`
Dynamic symbols shall retain the lifetime dependency of their originating library.

### `AFFI-34`
Unloading a foreign library shall not invalidate a live safe symbol capability.

### `AFFI-35`
`@repr(C)` shall establish representation compatibility, not general FFI safety.

### `AFFI-36`
FFI-safe types shall satisfy explicit ABI representation requirements.

### `AFFI-37`
Foreign language object models shall not become Axiom Core object models.

### `AFFI-38`
C ABI shall be the primary stable foreign-language interoperability baseline.

### `AFFI-39`
C++ ABI compatibility shall be treated as platform/toolchain-specific unless explicitly stabilized.

### `AFFI-40`
Foreign memory converted into a safe Axiom capability shall re-enter normal verification.

### `AFFI-41`
Unsafe FFI adapters shall not disable ownership, capability, concurrency, or effect verification outside the established boundary.

### `AFFI-42`
FFI contracts shall participate in ABI fingerprints and incremental build identity.

### `AFFI-43`
Foreign dependencies shall be explicit build inputs.

### `AFFI-44`
Foreign execution shall not implicitly acquire Axiom OS authority.

### `AFFI-45`
FFI wrappers should concentrate unsafe code at the boundary rather than propagate unsafe operations into application code.

### `AFFI-46`
WASM linear-memory addresses shall not automatically acquire safe Axiom pointer provenance.

### `AFFI-47`
Cross-process or cross-module memory shall not imply Send, Share, or serialization safety.

### `AFFI-48`
FFI verification shall remain independent of optimization level.

---

# Kết luận BOOTSTRAP-192

Đây là một điểm rất quan trọng của kiến trúc Axiom.

Ta không cố làm:

```text
C/C++/Rust/Swift/ObjC
        ↓
"convert tất cả thành Axiom"
```

mà làm:

```text
              ┌───────────────┐
              │ Axiom Core    │
              │ Safe Semantic │
              └───────┬───────┘
                      │
                FFI Contract
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
       C            C++          Swift/ObjC
        │             │             │
        └─────────────┼─────────────┘
                      ▼
                Native ABI
```

**Compiler chịu phần khó. Programmer chỉ thấy abstraction đã được kiểm chứng.**

Điều này phù hợp rất mạnh với mục tiêu ban đầu của Axiom: **không bắt programmer phải sống với pointer/reference/lifetime bureaucracy chỉ vì đang gọi một thư viện native.**

---

# BOOTSTRAP-193 — Package/Module ABI, Versioning, API Evolution & Binary Compatibility

**TRẠNG THÁI: NEXT**

Sau khi đã có:

```text
185 Reflection/Metadata
187 Package Manager
188 Compiler Correctness
189 Tooling
190 Security
191 Diagnostics
192 FFI
```

thì còn một vấn đề lớn trước khi kiến trúc Axiom có thể xem là gần hoàn chỉnh:

> **Một thư viện Axiom được biên dịch hôm nay phải có thể được sử dụng bởi chương trình được biên dịch ngày mai như thế nào?**

Đây không còn là package management đơn thuần.

Cần giải quyết:

```text
Source compatibility
API compatibility
Semantic compatibility
ABI compatibility
Binary compatibility
Metadata compatibility
Generic compatibility
Trait compatibility
FFI compatibility
Plugin compatibility
Dynamic library compatibility
Hot reload compatibility
Compiler-version compatibility
```

Đặc biệt phải quyết định một vấn đề rất quan trọng:

### Axiom có nên có **stable Axiom ABI** không?

Nếu có, cần thiết kế:

```text
Axiom ABI v1
      │
      ├── calling convention
      ├── type layout
      ├── generic ABI
      ├── trait/dyn ABI
      ├── closure ABI
      ├── async ABI
      ├── error ABI
      ├── metadata ABI
      ├── symbol/versioning
      └── compatibility rules
```

và phải tránh biến nó thành một gánh nặng khiến compiler mất khả năng tối ưu.

**BOOOTSTRAP-193 sẽ giải quyết chính vấn đề này: ABI ổn định ở đâu, ABI tối ưu ở đâu, và làm sao Axiom vừa có binary compatibility vừa giữ được khả năng tối ưu aggressive.**