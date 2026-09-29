Tiếp tục. Theo chuỗi thiết kế hiện tại, sau **TYPE-001** thì **ABI-001** là bước hợp lý nhất, vì từ đây Axiom phải xác định chính xác cách giá trị và hàm đi qua biên native/FFI trước khi thiết kế LIR và backend máy.

# ABI-001 — ABI, Calling Convention & Binary Interface

## 1. Mục tiêu

Axiom cần có **hai tầng ABI rõ ràng**:

```text
Axiom ABI
    ↓
Axiom ↔ Axiom
```

và:

```text
External ABI
    ↓
Axiom ↔ C / OS / runtime khác / DLL / SO / DYLIB / WASM
```

Nguyên tắc quan trọng:

> **Axiom ABI tối ưu cho Axiom. C ABI tối ưu cho khả năng tương tác. Không hy sinh ABI Axiom để giả lập C.**

Điều này cho phép compiler tự do tối ưu Axiom mạnh hơn.

---

# 2. Ba khái niệm phải tách biệt

Không nên gộp:

```text
Type representation
Calling convention
Linking ABI
```

Ví dụ:

```axiom
struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

Có ba câu hỏi khác nhau:

### Representation

Trong memory `Vec3` có layout thế nào?

```text
x y z
```

### Calling convention

Khi gọi:

```axiom
fn dot(a: Vec3, b: Vec3) -> f32
```

`a`, `b` truyền qua register hay stack?

### Linking ABI

Symbol bên ngoài tên gì?

```text
_Z3dot5Vec3S_
```

hay:

```text
dot
```

Ba vấn đề này phải được xử lý độc lập.

---

# 3. Axiom ABI mặc định

Đề xuất:

```axiom
fn add(a: i32, b: i32) -> i32
```

sử dụng:

```text
@abi(axiom)
```

một cách ngầm định.

Không cần viết:

```axiom
@abi(axiom)
```

trừ khi muốn override ABI mặc định.

Axiom ABI được phép thay đổi theo target nếu **observable semantics không thay đổi**.

Ví dụ:

```text
x86-64:
    register ABI A

AArch64:
    register ABI B

RISC-V:
    register ABI C
```

Nhưng ở cấp ngôn ngữ:

```axiom
fn f(x: i32) -> i32
```

vẫn có cùng semantic signature.

---

# 4. ABI không được rò rỉ vào source-level semantics

Đây là nguyên tắc rất quan trọng.

Ví dụ:

```axiom
fn distance(a: Vec3, b: Vec3) -> f32
```

Programmer **không cần biết**:

```text
a → xmm0/xmm1
b → xmm2/xmm3
return → xmm0
```

Đó là nhiệm vụ của backend.

Compiler có thể quyết định:

```text
register
stack
sret
caller allocation
split aggregate
scalar replacement
```

miễn là ABI contract được giữ.

---

# 5. Function ABI descriptor

Trong Typed IR/MIR, mỗi function nên có ABI metadata:

```text
FunctionABI {
    calling_convention
    parameter_abi[]
    return_abi
    variadic
    unwind_mode
    visibility
    linkage
}
```

Ví dụ:

```text
fn foo(Vec3, i64) -> BigStruct
```

có thể lower thành:

```text
params:
    Vec3 → register pair
    i64  → register

return:
    BigStruct → caller-provided storage
```

MIR không nên trực tiếp hard-code x86 register.

---

# 6. Calling convention

Core nên có một abstraction:

```axiom
@abi(axiom)
@abi(c)
@abi(system)
@abi(wasm)
```

về sau có thể:

```axiom
@abi(vectorcall)
@abi(thiscall)
@abi(fastcall)
```

nhưng chỉ khi target/backend cần.

Không nên đưa hàng chục calling convention vào semantic Core ngay từ đầu.

---

# 7. `extern`

FFI phải cực kỳ rõ ràng.

Ví dụ:

```axiom
extern "C" fn puts(s: *const u8) -> i32
```

hoặc:

```axiom
extern "C" {
    fn puts(s: *const u8) -> i32
}
```

`extern` nghĩa là:

> Function implementation nằm ngoài Axiom compilation unit/ABI domain.

Nó không tự động có nghĩa là unsafe.

Nhưng nếu signature sử dụng raw pointer hoặc ABI contract không thể kiểm chứng, call có thể yêu cầu `unsafe`.

---

# 8. C ABI

C ABI phải là **first-class external ABI**, không phải hack.

Ví dụ:

```axiom
@repr(C)
struct Point {
    x: f32
    y: f32
}

extern "C" fn distance(
    a: Point,
    b: Point
) -> f32
```

Compiler phải đảm bảo:

```text
layout
alignment
padding
calling convention
argument passing
return passing
symbol
```

phù hợp target C ABI.

---

# 9. `@repr(C)`

`@repr(C)` là một **representation contract**.

```axiom
@repr(C)
struct Point {
    x: f32
    y: f32
}
```

Nó không có nghĩa:

```text
"hãy compile function theo C ABI"
```

Do đó:

```axiom
@repr(C)
struct Point {}
```

và:

```axiom
extern "C" fn foo(...)
```

là hai cơ chế khác nhau.

Có thể dùng cả hai:

```axiom
@repr(C)
struct Point {
    x: f32
    y: f32
}

extern "C" fn foo(p: Point)
```

---

# 10. Axiom ABI và layout tối ưu

Đây là điểm rất có giá trị cho mục tiêu performance.

Mặc định:

```axiom
struct Transform {
    position: Vec3
    rotation: Quat
    scale: Vec3
}
```

không nhất thiết có layout C.

Compiler có thể:

```text
reorder
scalarize
split
pack
eliminate
```

nếu không có observable layout requirement.

Nhưng:

```axiom
@repr(C)
```

sẽ đóng layout cần thiết.

---

# 11. Return-value ABI

Axiom phải hỗ trợ ba dạng:

### Scalar return

```axiom
fn f() -> i64
```

thường:

```text
register
```

### Small aggregate return

```axiom
fn f() -> Vec2
```

có thể:

```text
register(s)
```

### Large aggregate

```axiom
fn f() -> LargeStruct
```

có thể lower thành:

```text
fn f(out: *mut LargeStruct) -> void
```

tức:

```text
sret
```

nhưng **sret chỉ là backend ABI lowering**, không phải source-level pointer.

---

# 12. Caller-allocated return

Axiom nên hỗ trợ mạnh caller allocation.

Ví dụ source:

```axiom
fn create() -> BigObject
```

không có nghĩa:

```text
malloc()
construct()
return pointer
```

Compiler có thể biến thành:

```text
caller allocates result storage
callee initializes it
```

Điều này rất phù hợp với memory model đã chốt:

```text
AMEM-28 Return Does Not Imply Heap Allocation
AMEM-29 Caller-Allocated Returns Are Permitted
```

và giúp giảm allocation cực mạnh.

---

# 13. Struct argument passing

Compiler phân loại aggregate:

```text
A → scalar
B → small aggregate
C → large aggregate
D → nontrivial/drop-bearing aggregate
```

Không nên định nghĩa bằng số byte cố định ở language level.

Ví dụ:

```axiom
struct Pair {
    a: i64
    b: i64
}
```

có thể pass:

```text
rdi, rsi
```

trên một target.

Nhưng target khác có thể:

```text
stack
```

Axiom semantics không thay đổi.

---

# 14. Drop-bearing argument

Đây là vấn đề quan trọng.

```axiom
struct File {
    handle: Handle
}

impl Drop for File { ... }
```

Nếu:

```axiom
fn process(f: File)
```

thì ABI phải biết:

```text
caller → callee ownership transfer
```

Nhưng physical ABI không nhất thiết phải truyền một pointer.

Có thể:

```text
register
stack
hidden temporary
```

Compiler vẫn phải duy trì ownership semantics.

Do đó:

> **ABI lowering không được làm mất ownership state của MIR.**

Ownership được resolve trước khi ABI lowering.

---

# 15. `view<T>` và `mut_view<T>` trong ABI

Đây là nơi semantic capability và ABI phải gặp nhau.

Source:

```axiom
fn sum(v: view<i32>) -> i32
```

không nhất thiết expose:

```text
struct {
    ptr;
    len;
}
```

nhưng thông thường có thể lower thành:

```text
ptr + len
```

hoặc target-specific equivalent.

Điều quan trọng:

```text
view ≠ raw pointer
```

ABI representation có thể giống pointer+length, nhưng semantic verifier vẫn biết:

```text
owner
provenance
region
read capability
lifetime
```

Sau khi verification hoàn tất, những metadata đó có thể bị erase.

---

# 16. `mut_view<T>`

Ví dụ:

```axiom
fn fill(v: mut_view<u8>, value: u8)
```

ABI có thể là:

```text
ptr
length
value
```

nhưng source-level semantics đảm bảo:

```text
exclusive WRITE capability
```

Không được biến representation giống nhau thành lý do cho phép aliasing sai.

---

# 17. Variadic functions

Cần hỗ trợ:

```axiom
extern "C" fn printf(
    fmt: *const u8,
    ...
) -> i32
```

Nhưng:

> Variadic không nên là cơ chế generic của Axiom.

Axiom generic function:

```axiom
fn log<T>(x: T)
```

khác hoàn toàn:

```text
C varargs
```

Varargs chủ yếu dành cho FFI.

---

# 18. Type-safe variadic API

Library Axiom nên ưu tiên:

```axiom
fn format<T>(...)
```

hoặc:

```axiom
fn write(args: FormatArgs)
```

thay vì:

```axiom
...
```

`...` chỉ cần cho ABI interoperability.

---

# 19. Symbol mangling

Axiom function:

```axiom
fn math::vector::dot(a: Vec3, b: Vec3)
```

không nên export symbol:

```text
dot
```

mặc định.

Compiler tạo mangled symbol:

```text
_axm$math$vector$dot$...
```

Tên chính xác chưa cần đóng ngay, nhưng phải encode đủ thông tin cần thiết để tránh collision.

Tuy nhiên:

```axiom
@export("dot")
fn dot(...)
```

cho phép symbol public ổn định.

---

# 20. `@export`

Đề xuất:

```axiom
@export("my_function")
pub fn my_function(...)
```

hoặc nếu tên source đã đủ:

```axiom
@export
pub fn my_function(...)
```

`@export` là explicit ABI boundary.

Không nên mặc định export toàn bộ `pub`.

---

# 21. Visibility và linking

Phân biệt:

```text
source visibility
linkage visibility
symbol visibility
```

Ví dụ:

```axiom
pub fn foo()
```

chỉ có nghĩa:

```text
module/package API
```

không nhất thiết:

```text
ELF global symbol
DLL export
Mach-O external symbol
```

Muốn binary-level export:

```axiom
@export("foo")
```

---

# 22. Static / dynamic library

Axiom compiler/linker pipeline cần tạo:

```text
.axo       // Axiom module/metadata, nếu cần
.o         // object
.a         // static library
.lib       // Windows static/import library
.so        // Linux shared object
.dll       // Windows dynamic library
.dylib     // macOS dynamic library
```

Không nhất thiết `.axo` phải tồn tại trong bản đầu tiên; nó là candidate cho incremental compilation/module metadata.

---

# 23. Object format

Axiom backend phải có abstraction:

```text
ObjectWriter
    ├── ELF
    ├── COFF/PE
    ├── Mach-O
    └── WASM
```

Frontend không biết:

```text
ELF section
Mach-O segment
PE section
```

Đó là target/linker layer.

---

# 24. Linker

Đây là một quyết định lớn.

Mục tiêu cuối cùng của Axiom là:

> Không phụ thuộc compiler/linker bên thứ ba.

Do đó kiến trúc nên là:

```text
Axiom Compiler
      ↓
Axiom LIR
      ↓
Machine Code
      ↓
Object Writer
      ↓
Axiom Linker
      ↓
Native Executable
```

Trong giai đoạn đầu có thể dùng:

```text
LLVM / system linker
```

nhưng đó chỉ là **bootstrap backend**.

Không được để architecture phụ thuộc vào nó.

---

# 25. Target triple

Axiom cần canonical target descriptor:

```text
architecture
vendor
os
environment
abi
endianness
pointer_width
features
```

Ví dụ:

```text
x86_64-pc-windows-msvc
x86_64-unknown-linux-gnu
aarch64-apple-darwin
aarch64-linux-android
wasm32-unknown-unknown
```

Nhưng nên tránh biến target triple thành một chuỗi magic mà compiler phải parse khắp nơi.

Internal representation:

```text
Target {
    arch
    os
    env
    abi
    endian
    pointer_width
    cpu
    features
}
```

---

# 26. Endianness

Axiom source semantics không phụ thuộc endian.

```axiom
let x: u32 = 0x12345678
```

có cùng numerical value.

Nhưng khi convert memory bytes:

```axiom
bytes_of(x)
```

phải có semantics rõ ràng.

Đề xuất:

```axiom
to_le_bytes()
to_be_bytes()
from_le_bytes()
from_be_bytes()
```

Không được mặc định:

```text
memory representation == serialization format
```

---

# 27. Pointer width

`usize` và `isize` phụ thuộc target.

Ví dụ:

```text
wasm32 → 32-bit
x86_64 → 64-bit
aarch64 → 64-bit
```

`usize` được dùng cho:

```text
index
length
allocation size
address-sized values
```

Không nên dùng `usize` cho protocol/network serialization nếu width phải cố định.

---

# 28. TLS ABI

Axiom đã có:

```text
static
TLS
local
dynamic
```

ABI phải hỗ trợ:

```axiom
@tls
static counter: u64
```

Compiler/backend có thể lower sang target TLS mechanism:

```text
ELF TLS
PE TLS
Mach-O TLS
```

Nhưng:

> TLS là storage contract, không phải compiler-global magic.

---

# 29. Panic ABI

Axiom không dùng C++ exception ABI làm semantic foundation.

Panic profile:

```text
@panic(abort)
@panic(unwind)
```

Trong:

```text
abort
```

không cần unwind runtime.

Trong:

```text
unwind
```

cần target-specific unwind metadata/runtime support.

Điều này phù hợp mục tiêu:

```text
freestanding + tiny binary
```

---

# 30. Unwind ABI

Không đưa unwind representation vào Core semantics.

Backend có:

```text
UnwindInfo
LandingPad
Cleanup
Personality
Exception/Unwind metadata
```

MIR chỉ cần biết:

```text
cleanup edges
drop obligations
panic paths
```

Sau đó ABI/backend quyết định:

```text
DWARF EH
Windows SEH
target-specific mechanism
```

---

# 31. FFI ownership

Đây là điểm cần đóng rất chặt.

Không được giả định:

```axiom
extern "C" fn free(ptr: *mut u8)
```

có thể nhận mọi Axiom allocation.

Mỗi allocation domain có ownership contract.

Ví dụ:

```text
Axiom allocator
    ≠
libc malloc
    ≠
Windows HeapAlloc
```

Do đó API FFI nên thiết kế:

```axiom
extern "C" fn create() -> *mut CObject
extern "C" fn destroy(x: *mut CObject)
```

thay vì:

```axiom
Box<T> → arbitrary C free()
```

Điều này trực tiếp củng cố:

```text
AMEM-50
AMEM-51
```

---

# 32. FFI type whitelist

Một `extern "C"` interface chỉ nên cho phép những type có ABI xác định.

Ví dụ hợp lệ:

```text
integers
floats
pointers
@repr(C) structs
@repr(C) enums
function pointers
arrays có ABI rõ
opaque handles
```

Không nên cho:

```text
trait object
closure capturing
arbitrary Axiom struct
view với ABI chưa xác định
generic type
```

trừ khi explicit ABI representation tồn tại.

Compiler phải reject thay vì âm thầm đoán.

---

# 33. Opaque FFI type

Ví dụ C:

```c
typedef struct MyHandle MyHandle;
```

Axiom:

```axiom
@opaque
extern type MyHandle
```

Sau đó:

```axiom
extern "C" fn create() -> *mut MyHandle
extern "C" fn destroy(x: *mut MyHandle)
```

Axiom không biết layout.

Đây là cách chuẩn để giữ ABI ổn định.

---

# 34. Stable ABI

Không phải mọi Axiom library đều cần stable ABI.

Mặc định:

```text
Axiom ABI = compiler-version dependent
```

Điều này cho phép compiler tối ưu mạnh.

Nếu muốn ABI ổn định:

```axiom
@stable_abi(version = 1)
```

hoặc module/package-level contract.

Stable ABI phải freeze:

```text
type layout
calling convention
symbol naming/export
alignment
enum representation
error ABI
panic/unwind policy
ownership boundary
allocator boundary
```

---

# 35. ABI versioning

Không nên encode compiler version trực tiếp vào semantic ABI.

Ví dụ không nên:

```text
Axiom ABI 0.7.391
```

Thay vào đó:

```text
Axiom ABI major/minor
```

Ví dụ:

```text
AXIOM_ABI_1
```

Compiler có thể có:

```text
compiler version 0.8
compiler version 0.9
```

nhưng cùng implement:

```text
ABI 1
```

nếu tương thích.

---

# 36. ABI compatibility

Có ba mức:

```text
Source compatibility
Binary compatibility
Semantic compatibility
```

Ví dụ thay:

```axiom
fn f(x: i32)
```

thành:

```axiom
fn f(x: i64)
```

có thể source migration được nhưng:

```text
binary ABI incompatible
```

Compiler/tooling nên có ABI checker.

---

# 37. ABI manifest

Đây là một thành phần rất đáng thêm.

Compiler có thể sinh:

```text
foo.abi
```

chứa machine-readable:

```text
function
symbol
calling convention
parameters
return
layout
alignment
visibility
ABI version
target
```

Ví dụ conceptually:

```text
ABI:
  function: foo
  symbol: axm$foo$...
  convention: axiom
  params:
    - i32
    - @repr(C) Point
  return:
    - f64
```

Điều này cực hữu ích cho:

- compiler
- linker
- debugger
- IDE
- AI agent
- ABI compatibility checker

---

# 38. ABI invariants

Chốt nhóm invariant:

### ABI-20
**Axiom ABI Is The Default Internal ABI**

### ABI-21
**External ABI Must Be Explicit**

### ABI-22
**Representation And Calling Convention Are Distinct**

### ABI-23
**Calling Convention Is A Backend Contract**

### ABI-24
**Source Semantics Do Not Depend On Physical Argument Registers**

### ABI-25
**Aggregate Passing Is Target Dependent**

### ABI-26
**Aggregate Return May Use Caller-Provided Storage**

### ABI-27
**SRet Is A Backend ABI Mechanism**

### ABI-28
**Ownership Semantics Survive ABI Lowering**

### ABI-29
**Capability Semantics May Erase After Verification**

### ABI-30
**View Representation Does Not Define View Semantics**

### ABI-31
**C ABI Requires Explicit External Representation**

### ABI-32
**Variadic ABI Is Primarily An FFI Mechanism**

### ABI-33
**Symbol Naming Is Independent From Source Visibility**

### ABI-34
**Binary Export Must Be Explicit**

### ABI-35
**FFI Must Not Assume Foreign Allocation Ownership**

### ABI-36
**Opaque Foreign Types Have No Axiom Layout Knowledge**

### ABI-37
**Stable ABI Requires Explicit Representation Contracts**

### ABI-38
**ABI Version Is Independent From Compiler Version**

### ABI-39
**Endian Is A Target Property, Not A Numeric Semantic Property**

### ABI-40
**Pointer Width Is Target Dependent**

### ABI-41
**TLS Is A Storage Contract**

### ABI-42
**Panic ABI Is Independent From Panic Semantics**

### ABI-43
**Unwind Representation Is Target Specific**

### ABI-44
**Axiom ABI Must Not Require C ABI Compatibility**

### ABI-45
**FFI Boundaries Must Be ABI-Checkable**

### ABI-46
**ABI Lowering Occurs After Semantic Verification**

### ABI-47
**ABI Lowering Must Preserve Observable Ownership And Lifetime Semantics**

### ABI-48
**Native Object Format Is A Backend Concern**

### ABI-49
**Linker Independence Is A Long-Term Architecture Requirement**

### ABI-50
**Axiom Must Be Capable Of Producing Native Binaries Without A Foreign Compiler**

---

# 39. Pipeline sau ABI-001

Như vậy pipeline hiện tại được khóa thành:

```text
Source
  ↓
Lexer / Parser
  ↓
AST
  ↓
Resolver
  ↓
HIR
  ↓
Typed HIR
  ↓
Closure / Async Analysis
  ↓
MIR
  ↓
Ownership
Capability
Effect
Concurrency
Pattern
Drop
  ↓
Verified MIR
  ↓
Semantic Optimization
  ↓
ABI Lowering
  ↓
Axiom LIR
  ↓
Target Lowering
  ↓
Machine IR
  ↓
Machine Optimization
  ↓
Register Allocation
  ↓
Spill / Reload
  ↓
Final Machine IR
  ↓
Machine Encoder
  ↓
Object Writer
  ↓
Axiom Linker
  ↓
Native Binary
```

Điểm rất quan trọng là **ABI Lowering nằm sau Verified MIR**, không trước.

---

# 40. Kiến trúc backend sau khi khóa ABI

Từ đây chúng ta có thể chuyển sang task tiếp theo:

## **LIR-001 — Axiom Low-Level IR**

Đây là bước rất quan trọng trước Machine Code.

LIR phải giải quyết:

```text
SSA
basic blocks
control flow
phi/select
virtual registers
memory operations
load/store
address calculation
call/return
ABI arguments
sret
atomic
volatile
SIMD
intrinsics
target features
stack slots
alignment
alias metadata
debug locations
unwind edges
```

Đặc biệt, tôi đề xuất **không nhảy thẳng từ MIR → x86/AArch64 machine code**.

Axiom nên có:

```text
MIR
 ↓
Axiom LIR
 ↓
Target-independent optimization
 ↓
Target-specific legalization
 ↓
Machine IR
```

để sau này một compiler duy nhất có thể hỗ trợ:

```text
x86-64
AArch64
RISC-V
WASM
ARM32
GPU
```

mà không biến frontend thành một đống logic target-specific.

**Task tiếp theo: LIR-001 — thiết kế hoàn chỉnh Axiom LIR, SSA và mô hình register/memory/control-flow.**