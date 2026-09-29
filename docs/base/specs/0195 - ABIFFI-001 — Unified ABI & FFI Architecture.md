Tiếp tục với **ABI/FFI-001**. Đây là lúc nên khóa hẳn tầng ABI/FFI, vì nếu làm không kỹ thì về sau C ABI, Windows API, Linux syscall, Swift/Objective-C interop, Android NDK... sẽ kéo các chi tiết platform ngược vào compiler core.

# ABI/FFI-001 — Unified ABI & FFI Architecture

Mục tiêu:

```text
Axiom Type System
       ↓
   ABI Analysis
       ↓
┌─────────────────────────────┐
│ Calling Convention          │
│ Type Classification         │
│ Argument Passing            │
│ Return Passing              │
│ Aggregate Representation    │
│ Variadic Rules              │
│ Layout / Representation     │
│ Unwind / Panic Boundary     │
└─────────────────────────────┘
       ↓
Target ABI
       ↓
Machine IR
```

Điểm quan trọng nhất:

> **FFI không phải một tính năng riêng biệt nằm bên cạnh ABI. FFI là việc áp dụng một ABI cụ thể cho một semantic boundary.**

---

# 1. Ba tầng phải tách biệt

Axiom cần phân biệt:

```text
Source ABI
    ↓
Semantic ABI
    ↓
Machine ABI
```

## Source ABI

Ví dụ:

```axiom
extern "C"
fn foo(x: i32) -> i32
```

Đây là yêu cầu từ source.

## Semantic ABI

Compiler xác định:

```text
foo:
    parameter 0 = i32
    return = i32
    calling convention = C
```

## Machine ABI

Target xác định:

```text
Windows x64:
    x → RCX
    return → RAX

SysV AMD64:
    x → RDI
    return → RAX

AAPCS64:
    x → X0
    return → X0
```

Frontend không được biết các register này.

---

# 2. ABI descriptor

Đề xuất:

```text id="abi-descriptor"
AbiDescriptor {
    id: AbiId
    calling_convention: CallingConvention
    target: TargetId

    type_classifier
    argument_classifier
    return_classifier

    register_convention
    stack_policy

    aggregate_policy
    variadic_policy

    layout_policy
    unwind_policy

    panic_boundary
}
```

Không phải tất cả ABI đều cần mọi field giống nhau.

---

# 3. CallingConvention

Không nên biến thành enum nhỏ:

```text
C
System
Axiom
```

Mà:

```text id="calling-convention"
CallingConvention {
    name
    argument_rule
    return_rule
    aggregate_rule
    variadic_rule
    register_rule
    stack_rule
}
```

Các convention có thể gồm:

```text
axiom
C
system
stdcall
fastcall
vectorcall
aapcs64
sysv_amd64
```

MVP chỉ cần:

```text
axiom
C
system
sysv_amd64
aapcs64
```

với alias/platform mapping thích hợp.

---

# 4. `extern "C"` không có nghĩa "x86 C ABI"

Đây là invariant rất quan trọng.

```axiom
extern "C"
fn foo(x: i32) -> i32
```

trên:

```text
x86-64 Linux
```

dùng SysV C ABI.

Trên:

```text
x86-64 Windows
```

dùng Windows x64 C ABI.

Trên:

```text
AArch64 Linux
```

dùng AAPCS64.

Do đó:

```text id="c-abi-resolution"
extern "C"
       ↓
Target
       ↓
C ABI implementation
```

không phải:

```text
extern "C" → fixed ABI
```

---

# 5. `extern "system"`

`system` cũng phải được resolve theo target.

Ví dụ conceptual:

```text id="system-abi"
Windows:
    extern "system" → Windows system ABI

Linux:
    extern "system" → platform system ABI
```

Compiler không nên coi `"system"` là một register convention.

Nó là **ABI selector**.

---

# 6. Axiom ABI

`extern "axiom"` đại diện cho:

> ABI native của chính phiên bản compiler/target Axiom.

Ví dụ:

```axiom
extern "axiom"
fn foo(x: i32) -> i32
```

Không nên hứa ABI này ổn định giữa mọi compiler version.

Do đó:

```text id="axiom-abi"
"Axiom ABI"
    = compiler-defined
    = version-sensitive
    = target-sensitive
```

Nếu cần ABI ổn định:

```axiom
extern "C"
```

hoặc ABI versioned trong tương lai.

---

# 7. Type classification

Đây là phần khó nhất.

Compiler cần:

```text id="type-classifier"
AbiTypeClassification {
    source_type
    size
    alignment
    classes[]
    representation
}
```

Ví dụ:

```text
i32
```

có thể:

```text
Integer32
```

`f64`:

```text
Float64
```

Struct:

```axiom
struct Pair {
    a: i64
    b: i64
}
```

có thể:

```text
Integer64
Integer64
```

hoặc:

```text
Indirect
```

tùy ABI.

---

# 8. ABI không được thay đổi Axiom type semantics

Ví dụ:

```axiom
struct Pair {
    a: i64
    b: i64
}
```

Axiom semantic type vẫn là:

```text
Pair
```

ABI có thể biến nó thành:

```text
RAX = a
RDX = b
```

nhưng không được biến source type thành:

```text
Tuple<i64,i64>
```

trong semantic type system.

ABI representation chỉ tồn tại ở boundary.

---

# 9. Argument assignment

Tạo abstraction:

```text id="abi-assignment"
AbiAssignment {
    source_value: ValueId

    pieces: [
        AbiPiece
    ]
}
```

```text id="abi-piece"
AbiPiece {
    source_offset
    size
    class
    location
}
```

Location:

```text id="abi-location"
AbiLocation =
    Register(Register)
    Stack(offset)
    Indirect(Register)
    Memory(offset)
```

Sau này có thể:

```text
Split([
    Register(RAX),
    Register(RDX)
])
```

---

# 10. Ví dụ scalar

```axiom
extern "C"
fn add(a: i64, b: i64) -> i64
```

SysV:

```text
a → RDI
b → RSI
return → RAX
```

Windows:

```text
a → RCX
b → RDX
return → RAX
```

AArch64:

```text
a → X0
b → X1
return → X0
```

RISC-V:

```text
a → A0
b → A1
return → A0
```

Cùng một semantic function.

---

# 11. Ví dụ aggregate

```axiom
struct Pair {
    a: i64
    b: i64
}
```

Function:

```axiom
extern "C"
fn make_pair() -> Pair
```

ABI classifier có thể trả:

```text
Piece 0 → RAX
Piece 1 → RDX
```

Hoặc ABI khác:

```text
Indirect return
```

với hidden pointer.

Đây chính là lý do cần `AbiAssignment` thay vì:

```text
return_register: Register
```

---

# 12. Hidden arguments

Compiler phải có khái niệm:

```text id="hidden-abi-arg"
AbiHiddenArgument {
    kind:
        SRet
        Context
        This
        Metadata
        VariadicState
}
```

Nhưng source/debug layer phải biết:

```text
hidden argument != source argument
```

Ví dụ:

```axiom
fn create() -> BigStruct
```

ABI có thể biến thành machine-level:

```text
__create(out_ptr)
```

nhưng debugger vẫn phải hiển thị:

```text
create()
```

chứ không hiển thị một tham số giả.

---

# 13. Aggregate return bằng sret

Semantic:

```text
fn create() -> BigStruct
```

ABI lowering:

```text
hidden out_ptr
```

Machine-level conceptual:

```text
create(out_ptr)
```

Compiler phải theo dõi:

```text
ReturnValueOrigin
```

để debug mapping không nhầm.

---

# 14. Aggregate argument

Tương tự:

```axiom
struct Vec4 {
    x: f32
    y: f32
    z: f32
    w: f32
}
```

Một ABI có thể:

```text
pass in FP registers
```

ABI khác:

```text
pass in integer registers
```

hoặc:

```text
pass indirectly
```

Axiom type system không cần biết.

---

# 15. `@repr(C)`

Đây là nơi ABI kết nối với layout.

```axiom
@repr(C)
struct Foo {
    a: i32
    b: i64
}
```

có nghĩa:

```text
layout = C-compatible layout
```

Nhưng **không có nghĩa**:

```text
Foo always passed according to C ABI
```

Một type có C layout và một function có C calling convention là hai khái niệm khác nhau.

Ví dụ:

```text
@repr(C)
struct Foo
```

có thể được sử dụng trong:

```text
extern "C"
fn foo(Foo)
```

nhưng cũng có thể dùng trong Axiom ABI.

---

# 16. `@repr(transparent)`

Cần định nghĩa rõ:

```text
@repr(transparent)
struct Handle {
    raw: usize
}
```

có representation tương đương field duy nhất đủ điều kiện.

Điều này đặc biệt hữu ích FFI:

```axiom
@repr(transparent)
struct FileHandle {
    raw: usize
}
```

nhưng:

> `transparent` representation không tự động biến type thành primitive semantic type.

`FileHandle != usize`.

---

# 17. C ABI compatibility

Cần một verifier:

```text id="ffi-verifier"
FfiCompatibility
```

kiểm tra:

- type representation;
- alignment;
- size;
- field layout;
- enum representation;
- pointer representation;
- function calling convention;
- parameter/return ABI;
- ownership boundary;
- panic boundary.

Không được để compiler đơn giản nói:

```text
@repr(C) → OK
```

---

# 18. FFI type matrix

MVP nên xác định rõ:

| Axiom | C ABI |
|---|---|
| `i8` | compatible |
| `u8` | compatible |
| `i16` | compatible |
| `u16` | compatible |
| `i32` | compatible |
| `u32` | compatible |
| `i64` | compatible |
| `u64` | compatible |
| `isize` | target-sized integer |
| `usize` | target-sized unsigned |
| `f32` | compatible |
| `f64` | compatible |
| `bool` | **không tự động coi là C `_Bool` nếu chưa định nghĩa representation** |
| `Text` | không |
| `String` | không |
| `Vec<T>` | không |
| `view<T>` | chỉ khi explicit FFI representation |
| `mut_view<T>` | chỉ khi explicit FFI representation |
| `Option<T>` | chỉ với explicit ABI-compatible representation |
| `Result<T,E>` | không mặc định |
| closure | không |
| `dyn Trait` | không |
| raw pointer | có thể, với unsafe/FFI rules |
| `@repr(C) struct` | có thể |
| `@repr(C)` enum | có thể nếu representation được xác định |

Đây phải trở thành **machine-checkable rule**, không phải documentation.

---

# 19. FFI view

Axiom:

```axiom
extern "C"
fn process(data: view<u8>)
```

Không nên tự động coi là:

```text
uint8_t*
```

vì `view<T>` có semantic provenance/lifetime.

Tại ABI boundary, compiler có thể lower:

```text
view<T>
```

thành:

```text
(ptr, len)
```

nhưng chỉ khi ABI contract của function cho phép.

Do đó cần:

```text id="ffi-view"
@ffi
fn process(data: view<u8>)
```

hoặc một cơ chế tương đương sau này để nói:

```text
view<T> → pointer + length
```

Tôi khuyến nghị **không tạo syntax mới ngay v0.1**; dùng ABI metadata/intrinsic trước.

---

# 20. FFI ownership boundary

Đây là phần rất quan trọng với Axiom.

C không biết:

```text
Ownership
Drop
view lifetime
Send
Share
```

Do đó:

```axiom
extern "C"
fn foo(x: Box<T>)
```

không được mặc định hợp lệ.

Phải có explicit FFI representation.

Ví dụ library wrapper:

```axiom
extern "C"
fn c_create() -> *mut CThing

extern "C"
fn c_destroy(p: *mut CThing)
```

Axiom wrapper:

```text
create()
    ↓
unsafe FFI
    ↓
Box-like owner
```

Còn C chỉ thấy pointer.

---

# 21. `extern` boundary phải là effect boundary

Foreign function có thể:

- đọc memory;
- ghi memory;
- mutate global state;
- block;
- throw/longjmp;
- spawn threads;
- modify TLS;
- access OS;
- violate assumptions compiler cannot see.

Do đó:

```text id="foreign-call-effects"
ForeignCallEffect {
    memory: Unknown
    control_flow: MayReturn
    panic: Foreign
    threading: Unknown
}
```

Mặc định compiler phải conservative.

Sau này API có thể cung cấp annotations/contracts để tối ưu.

---

# 22. Nhưng không được làm FFI luôn opaque

Nếu mọi foreign function đều:

```text
MemoryEffect = Unknown
```

thì optimizer sẽ bị hạn chế rất nhiều.

Do đó có thể có metadata:

```text id="ffi-contract"
extern "C"
@readonly
fn strlen(...)
```

hoặc:

```text
@pure
```

nhưng **không nên đưa một effect system lớn vào Core ngay bây giờ**.

MVP:

```text
Unknown
ReadOnly
ReadWrite
```

đủ để xây compiler.

---

# 23. Panic qua FFI

Quy tắc phải rất rõ:

> Axiom panic không được tự động đi xuyên qua foreign ABI.

Ví dụ:

```text
Axiom
  ↓
extern "C"
  ↓
C
```

Nếu Axiom function panic:

```text
panic
```

thì boundary policy phải:

```text
abort
```

hoặc:

```text
catch → error return
```

nhưng không được để C vô tình unwind qua frame Axiom.

Ngược lại:

```text
C++ exception
```

không được tự động đi vào Axiom.

C++ ABI không phải Core v0.1.

---

# 24. Drop qua FFI

Nếu:

```axiom
struct Resource {
    ...
}
```

có Drop, không được export trực tiếp sang C nếu C không hiểu ownership.

Thay vào đó:

```text id="ffi-resource"
@repr(C)
struct ResourceHandle {
    raw: *mut CResource
}
```

và:

```text
fn close(handle: ResourceHandle)
```

Axiom wrapper chịu trách nhiệm Drop.

Đây chính là cách giữ Core sạch.

---

# 25. Callback ABI

Axiom closure:

```axiom
|x| x + 1
```

không thể tự động trở thành:

```text
int (*callback)(int)
```

vì closure có environment.

Cần:

```text id="callback-representation"
Callback {
    function_pointer
    context_pointer
}
```

C ABI thường yêu cầu:

```text
fn callback(userdata, value)
```

Axiom wrapper có thể tạo trampoline:

```text
Axiom closure
    ↓
trampoline
    ↓
C callback
```

MVP:

> Không tự động convert closure → C function pointer.

Function không capture có thể có conversion riêng sau này.

---

# 26. `extern "C" fn`

Một Axiom function:

```axiom
extern "C"
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

cần tạo:

```text
Axiom semantic function
       ↓
C ABI lowering
       ↓
linkage symbol
```

Nhưng:

```text
pub
```

không đồng nghĩa:

```text
exported symbol
```

Muốn export linker symbol:

```axiom
@export("add")
extern "C"
fn add(...)
```

như thiết kế trước đây.

---

# 27. Symbol identity

Cần tách:

```text
AxiomSymbol
LinkageSymbol
ForeignSymbol
ExportSymbol
DebugSymbol
```

Ví dụ:

```text
fn add(...)
```

có:

```text
AxiomSymbol = FunctionId(123)
```

và:

```text
LinkageSymbol = "add"
```

Không được dùng string `"add"` làm identity compiler-wide.

---

# 28. Name mangling

Axiom ABI:

```text
fn foo<T>(...)
```

có thể cần mangling.

C ABI:

```text
extern "C"
fn foo(...)
```

không được mangling theo Axiom generic scheme.

Do đó:

```text id="mangling"
Axiom ABI
    → Axiom mangling

C ABI
    → external symbol name as specified

system ABI
    → platform symbol rules
```

`@export("foo")` cho phép kiểm soát linkage name.

---

# 29. Generic FFI

Không cho:

```axiom
extern "C"
fn foo<T>(x: T)
```

một cách trực tiếp.

Generic không có C ABI representation tổng quát.

Cho phép:

```axiom
fn foo<T>(...)
```

và tạo concrete wrapper:

```axiom
@export("foo_i32")
extern "C"
fn foo_i32(x: i32) {
    foo::<i32>(x)
}
```

Compiler có thể hỗ trợ generate wrapper tự động sau này.

---

# 30. Trait FFI

Không cho:

```axiom
extern "C"
fn process(x: dyn Trait)
```

trực tiếp.

`dyn Trait` representation:

```text
data_ptr
dispatch_ptr
```

là Axiom-specific.

Nếu cần C API:

```text
opaque handle
+
function table
```

Ví dụ:

```text
C API
    ↓
opaque pointer
    ↓
Axiom dyn Trait wrapper
```

---

# 31. `Option<T>` FFI

Không được mặc định:

```text
Option<*mut T> == nullable pointer
```

trừ khi representation contract nói rõ.

Axiom semantic:

```text
Option<T>
```

là algebraic type.

ABI có thể tối ưu niche representation, nhưng FFI cần representation stable.

Do đó về sau:

```text
@repr(C)
enum ...
```

hoặc một FFI-specific representation.

Không để optimizer tự ý thay đổi FFI-visible representation.

---

# 32. ABI stability

Axiom cần ba mức:

### Internal ABI

```text
compiler version specific
```

### Package ABI

```text
Axiom compiler/toolchain controlled
```

### External ABI

```text
C/system/versioned ABI
```

FFI chỉ dựa trên external ABI.

---

# 33. Stable ABI boundary

Một function:

```axiom
@export("foo")
extern "C"
fn foo(x: i32) -> i32
```

phải tạo một ABI fingerprint:

```text id="abi-fingerprint"
AbiFingerprint {
    calling_convention
    parameter_representations
    return_representation
    layout_hash
    alignment
    visibility
}
```

Nếu ABI thay đổi:

```text
binary compatibility = broken
```

Compiler/linker/tooling có thể phát hiện.

---

# 34. FFI verifier

Tạo:

```text id="ffi-verifier-repo"
compiler/abi/
├── verifier.ax
├── compatibility.ax
├── layout.ax
├── ownership.ax
├── panic.ax
├── callback.ax
└── tests/
```

Diagnostics:

```text
AX_FFI_0001
    type is not FFI-compatible

AX_FFI_0002
    type has unstable representation

AX_FFI_0003
    function ABI mismatch

AX_FFI_0004
    aggregate cannot be represented by selected ABI

AX_FFI_0005
    ownership-bearing type crosses foreign boundary

AX_FFI_0006
    Axiom panic cannot cross foreign ABI

AX_FFI_0007
    closure cannot be used as foreign function pointer

AX_FFI_0008
    generic function cannot be exported with selected ABI

AX_FFI_0009
    trait object has no stable foreign representation

AX_FFI_0010
    foreign allocation domain is incompatible
```

---

# 35. FFI memory ownership

Đây là chỗ liên quan trực tiếp tới memory model Axiom.

Không được có:

```text
Axiom allocates
 ↓
C frees
```

một cách mặc định.

Cũng không:

```text
C malloc
 ↓
Axiom Drop
 ↓
Axiom free
```

trừ khi allocator domain được xác định.

Phải có:

```text id="ffi-allocator"
AllocationDomain {
    Axiom
    Foreign
    OS
    Custom(id)
}
```

và ownership transfer:

```text
ForeignOwned
AxiomOwned
Borrowed
```

---

# 36. CString

`Text` không phải C string.

Core/Std nên có:

```text
CString
CStrView
```

Conceptual:

```text
Text
   ↓ explicit conversion
CString
   ↓
extern "C"
```

Không tự động chuyển vì:

- UTF-8;
- NUL byte;
- ownership;
- lifetime.

---

# 37. FFI slice

Tương tự:

```text
view<u8>
```

không tự động đồng nghĩa:

```text
uint8_t*
```

FFI helper có thể tạo:

```text
CSpan<T> {
    ptr
    len
}
```

hoặc ABI tuple:

```text
(ptr, len)
```

Nhưng semantic Axiom view vẫn giữ provenance trước boundary.

---

# 38. Syscall không phải FFI thông thường

Một syscall:

```text
Linux write(...)
```

khác:

```text
extern "C" fn write(...)
```

vì syscall ABI:

```text
registers
syscall number
kernel boundary
```

Do đó:

```text
std.platform.linux.syscall
```

có thể dùng compiler intrinsic/system ABI riêng.

Không cần ép syscall thành C ABI.

---

# 39. ABI/FFI pipeline hoàn chỉnh

```text id="full-abi-pipeline"
Typed Function
       ↓
Resolve ABI
       ↓
Validate FFI
       ↓
Classify Types
       ↓
Assign Arguments
       ↓
Assign Return
       ↓
Insert Hidden ABI Arguments
       ↓
Lower Aggregate Representation
       ↓
Lower Variadic Boundary
       ↓
Generate ABI Call/Return
       ↓
Machine IR
```

---

# 40. ABI không được xâm nhập ownership checker

Ví dụ source:

```axiom
fn foo(x: String)
```

Ownership checker xử lý:

```text
String moved
```

ABI layer chỉ xử lý:

```text
representation of String
```

Nếu là Axiom ABI:

```text
String internal representation
```

Nếu là C ABI:

```text
String → not directly compatible
```

ABI verifier báo lỗi.

Không được để ABI layer tự quyết định ownership.

---

# 41. ABI không được xâm nhập type checker

Type checker biết:

```text
Pair
```

ABI biết:

```text
Pair → [I64, I64]
```

Nhưng ABI không được nói:

```text
Pair is actually two i64
```

Semantic type vẫn là `Pair`.

---

# 42. ABI/FFI acceptance suite

### ABI-001

```axiom
extern "C"
fn add(i32, i32) -> i32
```

### ABI-002

Six integer arguments.

### ABI-003

Eight AArch64/RISC-V arguments.

### ABI-004

FP arguments.

### ABI-005

Small aggregate.

### ABI-006

Large aggregate → sret.

### ABI-007

Mixed integer/FP aggregate.

### ABI-008

`@repr(C)` struct layout.

### ABI-009

`@repr(transparent)` newtype.

### ABI-010

Foreign function import.

### ABI-011

Axiom function export.

### ABI-012

Symbol rename with `@export`.

### ABI-013

Foreign allocation domain.

### ABI-014

Foreign callback.

### ABI-015

Closure rejection.

### ABI-016

Generic export rejection.

### ABI-017

Trait-object rejection.

### ABI-018

Panic boundary.

### ABI-019

FFI view.

### ABI-020

FFI C string.

---

# 43. Một điểm nên thay đổi trong Core

Sau audit này, tôi khuyến nghị **không thêm `extern "Rust"` hay `extern "C++"`** vào Core v1.

Giữ:

```text
extern "axiom"
extern "C"
extern "system"
```

và target-specific conventions nội bộ.

C++ ABI có quá nhiều vấn đề:

- name mangling;
- exception ABI;
- RTTI;
- vtables;
- object layout;
- multiple inheritance;
- compiler-version compatibility.

Axiom có thể interop C++ thông qua C adapter.

Điều này phù hợp mục tiêu:

> Core mạnh nhưng không cần mang toàn bộ complexity của C++ ABI vào language semantics.

---

# 44. ABI invariants

```text
AABI-20
ABI lowering does not alter source-level type identity.

AABI-21
Calling convention is target-resolved.

AABI-22
C ABI is target-specific.

AABI-23
System ABI is target-specific.

AABI-24
Axiom ABI is compiler-defined unless explicitly versioned.

AABI-25
ABI classification is deterministic.

AABI-26
Argument locations are ABI decisions.

AABI-27
Return locations are ABI decisions.

AABI-28
Aggregate representation is ABI-defined.

AABI-29
Hidden ABI arguments are not source parameters.

AABI-30
FFI representation must be explicitly valid.

AABI-31
@repr(C) controls representation, not ownership.

AABI-32
@repr(C) does not itself select calling convention.

AABI-33
Foreign calls have conservative memory effects by default.

AABI-34
Axiom panic cannot cross foreign ABI implicitly.

AABI-35
Foreign exceptions cannot enter Axiom implicitly.

AABI-36
Foreign allocation ownership must be explicit.

AABI-37
Closure-to-C-function conversion is not implicit.

AABI-38
Generic functions are not directly C-exportable.

AABI-39
Trait objects are not directly C ABI values.

AABI-40
FFI symbols are distinct from semantic symbol identity.

AABI-41
Exported ABI has a stable representation fingerprint.

AABI-42
ABI-visible layout cannot be changed by ordinary optimization.

AABI-43
Internal representation may be optimized when not ABI-visible.

AABI-44
FFI boundaries preserve required alignment and initialization invariants.

AABI-45
FFI does not bypass ownership verification.

AABI-46
FFI does not bypass capability verification.

AABI-47
Foreign pointers are unsafe unless wrapped by a proven abstraction.

AABI-48
ABI lowering occurs before physical register allocation.

AABI-49
Machine register selection is not part of source-level ABI semantics.

AABI-50
ABI subsystem is independent of any particular object format.
```

---

# 45. Kiến trúc compiler sau ABI-001

Bây giờ pipeline được làm sạch thành:

```text id="axiom-final-backend"
Source
 ↓
AST
 ↓
HIR
 ↓
Typed HIR
 ↓
Ownership / Capability / Drop
 ↓
MIR
 ↓
Verified MIR
 ↓
Semantic Optimization
 ↓
LIR-High
 ↓
LIR Legalization
 ↓
ABI Analysis
 ↓
Target Lowering
 ↓
Machine IR
 ↓
Register Allocation
 ↓
Frame Planning
 ↓
Prologue/Epilogue
 ↓
Machine Optimization
 ↓
Encoding
 ↓
Object
 ↓
Link
 ↓
Native Binary
```

Đây là kiến trúc backend tôi khuyến nghị đóng băng.

---

# 46. Một điều chỉnh nhỏ nhưng quan trọng

Thứ tự:

```text
LIR
 ↓
ABI
 ↓
Instruction Selection
```

không phải lúc nào cũng tuyến tính.

Thực tế nên cho phép:

```text
LIR
 ↓
┌───────────────────┐
│ ABI Classification│
└─────────┬─────────┘
          ↓
Target Legalization
          ↓
Instruction Selection
          ↓
Machine IR
```

và một số target-specific ABI constraints có thể quay lại ảnh hưởng ISel.

Vì vậy implementation tốt hơn là:

```text id="abi-lowering-loop"
LIR
 ↓
Target Legalizer
 ├── ABI classify
 ├── legalize aggregate
 ├── legalize calls
 ├── legalize returns
 └── legalize target operations
 ↓
ISel
 ↓
Machine IR
```

Không nên ép compiler thành một chuỗi pass cứng nhắc nếu một abstraction cần thông tin từ pass khác.

---

# 47. Bước tiếp theo: Mach-O-001

Sau khi ABI/FFI đã được tách sạch, target tiếp theo nên là:

**AArch64 macOS → Mach-O**

vì nó kiểm tra đồng thời:

```text
AArch64 backend
+
Apple ABI
+
Mach-O object
+
Mach-O linker
+
macOS startup
```

Kiến trúc sẽ là:

```text
                    ┌── Linux
                    │    ELF
                    │
AArch64 Machine IR ─┼── Android
                    │    ELF
                    │
                    └── macOS
                         Mach-O
```

Đây là bước tiếp theo có giá trị hơn việc thêm một ISA nữa, bởi lúc đó Axiom sẽ chứng minh được:

```text
same ISA
+
different ABI
+
different object format
+
different OS
```

mà không cần thay đổi frontend hay LIR.