Tiếp tục. Đây là phần tôi cho rằng **cực kỳ quan trọng đối với mục tiêu ban đầu của Axiom**: nếu frontend/type system rất đẹp nhưng ABI/backend thiết kế sai, cuối cùng compiler vẫn phải dựa vào LLVM hoặc sinh machine code kém.

Ta sẽ chốt **AXIOM ABI + FFI + Native Object Generation v0.1**.

---

# AXIOM ABI / NATIVE CODEGEN v0.1

## 1. Tách 4 tầng

Không được trộn semantic type với machine representation:

```text
Semantic Type
     ↓
Logical Representation
     ↓
ABI Representation
     ↓
Machine Representation
```

Ví dụ:

```axiom
struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

### Semantic

```text
Vec3
    x
    y
    z
```

### Logical representation

```text
3 × f32
```

### ABI representation

Có thể:

```text
registers
```

hoặc:

```text
stack
```

hoặc:

```text
caller-provided storage
```

### Machine representation

Ví dụ x86-64:

```text
XMM0
XMM1
```

hoặc stack slots.

**Programmer không được phụ thuộc vào ABI native này.**

---

# 2. Ba ABI chính

Axiom nên có:

```text
@abi(axiom)
@abi(C)
@abi(system)
```

### `axiom`

ABI tối ưu cho Axiom.

Compiler hoàn toàn kiểm soát.

### `C`

Tương thích C ABI.

Dùng cho:

- FFI
- plugin
- OS libraries
- native libraries
- interoperability

### `system`

Platform ABI.

Ví dụ Windows API hoặc syscall interface nếu cần.

---

# 3. Native Axiom ABI không cần stable

Ví dụ compiler:

```text
Axiom 0.1
```

có thể truyền:

```text
Vec3 → XMM0/XMM1
```

compiler tương lai:

```text
Axiom 0.2
```

có thể truyền bằng:

```text
XMM0
XMM1
```

hoặc:

```text
caller stack
```

Miễn semantic không thay đổi.

Nếu programmer cần binary compatibility:

```axiom
extern @abi(C)
```

hoặc ABI versioned trong tương lai.

---

# 4. Function call model

Một function:

```axiom
fn add(a: i32, b: i32) -> i32
```

semantic:

```text
inputs:
    a
    b

output:
    i32
```

ABI lowering quyết định:

```text
a → register/stack
b → register/stack
result → register/stack
```

MIR không được chứa quyết định CPU-specific này.

---

# 5. ABI MIR

Tôi đề xuất thêm một intermediate stage:

```text
Typed MIR
   ↓
ABI Lowering
   ↓
ABI MIR
   ↓
Axiom LIR
```

ABI MIR chịu trách nhiệm:

- argument passing
- return passing
- hidden parameters
- aggregate decomposition
- caller/callee storage
- varargs
- closure ABI
- dynamic dispatch ABI
- sret
- calling convention

---

# 6. Aggregate return

Ví dụ:

```axiom
fn make_point() -> Point
```

Không bắt buộc:

```text
malloc
```

Không bắt buộc temporary heap object.

Compiler có thể:

```text
caller allocates Point
        ↓
callee writes directly
```

conceptually:

```text
make_point(out: *mut Point)
```

nhưng **đây chỉ là ABI lowering**, không phải source semantic.

Điều này cực kỳ quan trọng cho hiệu năng.

---

# 7. Caller-allocated return

Ví dụ:

```axiom
fn create_buffer() -> LargeStruct
```

Semantic:

```text
return value
```

ABI có thể:

```text
caller:
    allocate result storage

callee:
    fill result storage

return:
    no copy
```

Compiler có thể eliminate:

```text
temporary
copy
move
```

---

# 8. Move không phải memcpy

Ví dụ:

```axiom
let b = a
```

nếu `a` non-Copy:

```text
ownership:
a → MOVED
b → OWNED
```

Không có yêu cầu:

```asm
memcpy(...)
```

Nếu:

```text
a
```

chỉ gồm register values, move có thể gần như:

```text
rename SSA value
```

Nếu là large aggregate:

```text
ownership transfer
```

có thể chỉ thay đổi metadata compiler.

---

# 9. Struct ABI classification

Axiom không nên có một rule riêng kiểu:

> mọi struct > 16 bytes đều pass bằng stack.

Thay vào đó:

```text
ABI backend
    ↓
classify aggregate
```

Ví dụ trên x86-64:

```text
small scalar-like aggregate
→ registers
```

larger:

```text
→ registers + stack
```

hoặc:

```text
→ memory
```

Backend quyết định theo target ABI.

---

# 10. Struct layout

Mặc định:

```axiom
struct A {
    a: u8
    b: u64
}
```

compiler có thể layout tối ưu.

Ví dụ:

```text
semantic:
a
b
```

physical:

```text
b
a
padding
```

hoặc layout khác nếu không có representation contract.

Nhưng:

```axiom
@repr(C)
struct A {
    a: u8
    b: u64
}
```

→ C-compatible layout.

---

# 11. `repr(C)` phải rất nghiêm ngặt

`repr(C)` không chỉ là:

```text
field order giống C
```

mà phải quy định:

- field order
- alignment
- padding
- scalar representation
- enum compatibility
- ABI classification theo C
- compatible calling convention khi liên quan.

Và nếu kiểu Axiom không có representation tương ứng an toàn:

```text
@repr(C)
```

→ compile error.

Không được tạo C ABI giả.

---

# 12. Pointer

Axiom phân biệt:

```text
*T
```

với:

```text
usize
```

Pointer không phải integer semantic.

Trong unsafe có:

```text
*const T
*mut T
```

Chuyển:

```text
pointer ↔ integer
```

là low-level operation và cần explicit/unsafe.

Điều này giúp tránh compiler phải coi mọi integer là potential pointer.

---

# 13. Pointer provenance

Đây là điểm rất quan trọng cho memory optimizer.

Axiom safe code có:

```text
view
    ↓
provenance
    ↓
region
```

Raw pointer:

```text
*mut T
```

không còn được compiler đảm bảo ownership.

Nhưng backend vẫn phải có một mô hình nhất quán.

Do đó:

```text
raw pointer arithmetic
```

không được làm cho safe optimizer giả định sai aliasing.

---

# 14. `usize` không phải pointer

Ví dụ:

```axiom
let p: *mut T = ...
let x: usize = p as usize
```

đây là explicit low-level operation.

Sau đó:

```axiom
let q = x as *mut T
```

không tự động khôi phục provenance safe.

Muốn dereference:

```axiom
unsafe {
    *q
}
```

Programmer chịu trách nhiệm.

---

# 15. Function pointer vs closure

Phải tách:

```text
fn(...) -> T
```

và closure.

Function pointer có thể:

```text
code address
```

Closure:

```text
environment
+
code
```

Conceptual ABI:

```text
closure:
    env_ptr
    call_ptr
```

Nhưng closure không escape thì compiler có thể biến:

```text
closure
```

thành:

```text
inline code
```

và xóa hoàn toàn environment.

---

# 16. Không có mandatory closure allocation

Ví dụ:

```axiom
fn apply(x: i32, f: fn(i32) -> i32) -> i32
```

Nếu closure:

```axiom
let offset = 10

apply(5, |x| x + offset)
```

compiler có thể:

```text
environment = { offset }
```

Nhưng nếu inline được:

```text
apply(5, ...)
```

có thể trở thành:

```text
5 + 10
```

Không heap.

---

# 17. Dynamic trait ABI

Nếu:

```axiom
dyn Drawable
```

được sử dụng, representation conceptually:

```text
data_ptr
dispatch_ptr
```

Dispatch table có thể:

```text
type metadata
method pointers
drop function
size/alignment metadata nếu cần
```

Nhưng **không được tồn tại nếu không dùng dynamic dispatch**.

---

# 18. Dynamic dispatch + ownership

Nếu:

```axiom
dyn Drawable
```

owning:

```text
data_ptr
dispatch_ptr
```

có thể cần:

```text
drop_ptr
```

để destruction đúng dynamic type.

Nếu:

```axiom
view<dyn Drawable>
```

thì không sở hữu object.

Do đó có thể chỉ cần:

```text
data_ptr
dispatch_ptr
```

Không có universal object header.

---

# 19. Generic ABI

Đây là một điểm Axiom có lợi thế.

Generic:

```axiom
fn foo<T>(x: T)
```

sau specialization:

```text
foo<i32>
foo<f32>
foo<MyStruct>
```

mỗi specialization có thể có ABI riêng.

Ví dụ:

```text
foo<i32>
    → register

foo<BigStruct>
    → caller storage
```

Không cần generic runtime metadata.

---

# 20. Symbol mangling

Native symbol cần encode:

```text
package
module
function
generic specialization
ABI
```

Ví dụ conceptually:

```text
_axiom_my_pkg_math_add_i32
```

Nhưng format không nên freeze quá sớm.

Programmer có thể override:

```axiom
@export("my_add")
pub extern @abi(C) fn add(...)
```

---

# 21. Symbol visibility

Có ba khái niệm:

```text
source visibility
link visibility
export visibility
```

Ví dụ:

```axiom
pub fn foo()
```

không nhất thiết có nghĩa:

```text
ELF global exported symbol
```

Compiler có thể dead-strip hoặc hide symbol.

Muốn binary export:

```axiom
@export("foo")
pub extern @abi(C) fn foo(...)
```

Tôi đề xuất giữ distinction này.

---

# 22. FFI

FFI phải explicit.

Ví dụ:

```axiom
extern @abi(C) {
    fn malloc(size: usize) -> *mut u8
    fn free(ptr: *mut u8)
}
```

Nhưng trong code safe:

```text
malloc
```

không tự động trở thành safe.

Phải có wrapper:

```axiom
fn allocate(size: usize) -> Result<Buffer, AllocError> {
    unsafe {
        ...
    }
}
```

Sau đó public API:

```text
safe
```

---

# 23. FFI effect contract

Compiler không thể biết arbitrary C function làm gì.

Ví dụ:

```text
extern fn foo(...)
```

mặc định:

```text
UNKNOWN EFFECT
```

Compiler phải conservative.

Nhưng có thể annotate:

```axiom
@effects(read)
extern @abi(C) fn strlen(...)
```

hoặc compiler intrinsic knowledge.

Điều này giúp optimizer.

Tuy nhiên tôi **không muốn bắt programmer viết effect annotations cho mọi FFI trong v0.1**.

Default conservative là đủ.

---

# 24. C string

Không có:

```text
Text == char*
```

Axiom cần explicit:

```text
CStr
```

hoặc:

```text
view<u8>
```

với contract null-terminated.

Ví dụ:

```axiom
extern @abi(C)
fn puts(s: *const u8) -> i32
```

wrapper:

```axiom
fn puts(text: view<Text>) -> Result<(), Error>
```

có thể tạo temporary C representation nếu cần.

---

# 25. FFI struct

```axiom
@repr(C)
struct CPoint {
    x: f32
    y: f32
}
```

Có thể truyền:

```axiom
extern @abi(C)
fn draw_point(p: CPoint)
```

Compiler phải đảm bảo ABI tương thích.

---

# 26. C enum / union

Safe Core không nên có arbitrary untagged union.

Nhưng FFI:

```axiom
@repr(C)
union CValue {
    i: i32
    f: f32
}
```

có thể tồn tại ở unsafe/system layer.

Truy cập field:

```text
unsafe
```

vì active variant không được compiler biết.

---

# 27. Variadic C

Có thể hỗ trợ:

```axiom
extern @abi(C) fn printf(format: *const u8, ...)
```

nhưng:

**không đưa variadic function vào generic system.**

Chỉ FFI ABI.

---

# 28. Syscall

Không cần:

```text
syscall
```

primitive của Core.

Platform layer có thể:

```axiom
extern @abi(system)
fn syscall(...)
```

hoặc architecture-specific intrinsic.

Điều này giữ Core portable.

---

# 29. Object file

Axiom không nên phát minh binary object format cuối cùng.

Native target:

```text
Windows → COFF/PE
Linux → ELF
macOS → Mach-O
WASM → WASM module
```

Compiler có:

```text
ObjectWriter
```

interface:

```text
TargetObjectWriter
```

Backend sinh:

```text
sections
symbols
relocations
debug info
```

---

# 30. ELF

Backend cần eventually hỗ trợ:

```text
ELF header
program headers
sections
symbols
relocations
TLS
dynamic linking
unwind/debug metadata
```

Nhưng không cần compiler frontend biết ELF.

Pipeline:

```text
LIR
 ↓
x86-64 backend
 ↓
machine code
 ↓
ELF writer
```

---

# 31. PE/COFF

Windows:

```text
Machine code
 ↓
COFF object
 ↓
link
 ↓
PE executable
```

Axiom linker tương lai sẽ xử lý:

```text
imports
exports
relocations
TLS
sections
subsystem
entry point
```

---

# 32. Mach-O

macOS/iOS:

```text
Mach-O
 ├── segments
 ├── sections
 ├── symbols
 ├── relocations
 ├── code signature integration
 └── platform metadata
```

Code signing là platform/deployment concern, không phải language semantics.

---

# 33. WASM

WASM khác native vì:

```text
stack/register machine model
```

và:

```text
linear memory
```

Nhưng Axiom semantic model không thay đổi.

Pipeline:

```text
Verified MIR
 ↓
WASM LIR
 ↓
WASM module
```

Không cần giả lập native pointer semantics một cách vụng về.

---

# 34. Machine backend architecture

Tôi đề xuất:

```text
Axiom LIR
     ↓
Target Lowering
     ↓
Machine IR
     ↓
Instruction Selection
     ↓
Register Allocation
     ↓
Scheduling
     ↓
Machine Encoder
     ↓
Object Writer
```

Mỗi target:

```text
backend/
    x86_64/
    arm64/
    riscv64/
    wasm32/
```

---

# 35. Machine IR

Không nên nhảy trực tiếp:

```text
MIR → bytes
```

Machine IR cần biểu diễn:

```text
VirtualRegister
PhysicalRegister
MachineInstruction
MemoryOperand
Immediate
Label
Call
Branch
Atomic
```

Ví dụ conceptually:

```text
ADD
    vreg1
    vreg2
    vreg3
```

sau register allocation:

```text
ADD
    rax
    rbx
    rax
```

---

# 36. Register allocation

Ban đầu không cần thuật toán quá phức tạp.

Có thể:

```text
Linear Scan
```

cho bootstrap.

Sau này:

```text
Graph Coloring
PBQP
hybrid allocator
```

Không ảnh hưởng language semantics.

Điều quan trọng là:

```text
MIR semantics
```

không phụ thuộc register allocation.

---

# 37. Instruction selection

Ban đầu:

```text
pattern matching
```

Ví dụ:

```text
INTEGER_ADD
```

x86:

```asm
add
```

ARM64:

```asm
add
```

RISC-V:

```asm
add
```

Complex instruction selection có thể bổ sung sau.

---

# 38. Intrinsic

Không nên đưa hàng nghìn CPU instructions vào Core syntax.

Ví dụ SIMD:

```axiom
simd.add(...)
```

là library/intrinsic abstraction.

Compiler có thể nhận diện:

```text
SIMD intrinsic
```

→ machine instruction.

Nếu CPU không hỗ trợ:

```text
fallback
```

hoặc compile error tùy API.

---

# 39. Atomic

MIR đã có:

```text
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
```

ABI/backend mapping:

```text
x86 → lock cmpxchg
ARM → ldaxr/stlxr...
RISC-V → amo...
```

Memory ordering semantic được quyết định **trước backend**.

Backend không được tự thay:

```text
Acquire
```

thành:

```text
Relaxed
```

chỉ vì "nhanh hơn".

---

# 40. Stack frame

Compiler phải quản lý:

```text
locals
spill slots
saved registers
return address
alignment
outgoing call arguments
unwind info
```

Nhưng source programmer không được mặc định:

```text
local = stack
```

Một local có thể:

```text
SSA
register
stack
eliminated
```

---

# 41. `alloca` không phải language primitive

Axiom không cần:

```text
alloca()
```

trong Core.

Compiler tự tạo stack storage khi cần.

Nếu programmer muốn dynamic stack allocation thì đó là platform/unsafe facility.

Điều này giữ storage abstraction sạch.

---

# 42. Unwind / panic

Axiom đã chọn:

```text
panic=abort
panic=unwind
```

### Abort

Binary nhỏ:

```text
panic
 ↓
exit/trap
```

### Unwind

Cần:

```text
unwind metadata
cleanup landing pads
personality/runtime component
```

Quan trọng:

**Drop semantics vẫn phải đúng trong cả hai profile.**

---

# 43. Exception không trở lại

Unwind không có nghĩa:

```text
try/catch exceptions
```

Nó chỉ là cơ chế:

```text
panic
 ↓
stack unwinding
 ↓
Drop
 ↓
termination
```

Core vẫn không có general exception mechanism.

---

# 44. Debug information

Axiom cần source mapping:

```text
Source
 ↓
AST
 ↓
HIR
 ↓
MIR
 ↓
machine
```

Debug artifact phải biết:

```text
machine address
→ source file
→ line/column
→ function
→ variable location
```

Có thể xuất:

```text
DWARF
PDB
```

tùy target.

---

# 45. Axiom debugger không cần tự xây ngay

Compiler nên sinh debug information chuẩn.

Sau đó:

```text
gdb
lldb
WinDbg
```

có thể debug.

Về sau mới xây:

```text
axiom debug
```

nếu muốn.

---

# 46. Stack trace

Panic có thể in:

```text
panic:
    file.ax:42
    parser.parse
    compiler.build
    main
```

Nhưng stack tracing là runtime/debug component.

Release freestanding có thể:

```text
panic → trap
```

---

# 47. Native startup

Executable:

```text
OS
 ↓
entry point
 ↓
Axiom startup
 ↓
initialize required runtime components
 ↓
main
 ↓
exit
```

Không hidden initialization ngoài dependency graph.

Ví dụ chương trình không dùng allocator:

```text
startup
```

không initialize heap runtime.

---

# 48. C runtime dependency

Bootstrap có thể phụ thuộc:

```text
CRT
system linker
assembler
```

Nhưng mục tiêu cuối:

```text
Axiom compiler
+
Axiom runtime components
+
OS ABI
```

có thể tạo executable mà không cần C compiler.

Đây là một milestone quan trọng.

---

# 49. Self-hosting roadmap

Tôi đề xuất không cố làm tất cả ngay.

### Stage 0

```text
Axiom compiler prototype
→ host language
→ LLVM/backend hoặc system assembler
```

### Stage 1

```text
Axiom frontend
→ own MIR
→ own interpreter
```

### Stage 2

```text
Axiom
→ own LIR
→ x86-64 machine code
→ object writer
```

### Stage 3

```text
Axiom compiler
→ Axiom source
→ native executable
```

### Stage 4

```text
Axiom compiler
→ self-hosted
```

### Stage 5

```text
Axiom linker
→ own ELF/PE/Mach-O
```

Không cần đợi Stage 5 mới gọi là self-hosting compiler.

---

# 50. Kiến trúc cuối cùng

Ta hiện có:

```text
                    AXIOM SOURCE
                         │
                         ↓
                  Parser / AST
                         │
                         ↓
                       HIR
                         │
            ┌────────────┼────────────┐
            │            │            │
         Types        Traits       Generics
            │            │            │
            └────────────┼────────────┘
                         ↓
                        MIR
                         │
            ┌────────────┼────────────┐
            │            │            │
        Ownership     Regions      Effects
            │            │            │
            └────────────┼────────────┘
                         ↓
                 Verified MIR
                         │
                 Async / Drop
                    lowering
                         ↓
                    Optimizer
                         ↓
                      Axiom LIR
                         ↓
                   ABI Lowering
                         ↓
                    Machine IR
                         ↓
                Register Allocation
                         ↓
                 Instruction Select
                         ↓
                  Machine Encoder
                         ↓
                   Object Writer
                         ↓
               ┌─────────┼─────────┐
               │         │         │
              ELF       PE      Mach-O
               │         │         │
               └─────────┼─────────┘
                         ↓
                       Linker
                         ↓
                 Native Executable
```

Và FFI đi xuyên qua ABI boundary:

```text
Axiom
  │
  ├── @abi(axiom)
  │
  ├── @abi(C)
  │
  └── @abi(system)
          ↓
       Native world
```

---

# 51. Những gì tôi sẽ freeze

Đề xuất thêm nhóm invariant:

```text
AABI-21
ABI lowering occurs after semantic verification.

AABI-22
Native ABI is compiler-controlled and not implicitly stable.

AABI-23
C ABI compatibility requires explicit representation/ABI selection.

AABI-24
Aggregate returns may use caller-provided storage.

AABI-25
Move does not imply physical copying.

AABI-26
Ordinary values have no mandatory heap/object header.

AABI-27
Closure environment representation is implementation-defined.

AABI-28
Dynamic trait representation exists only when dynamic dispatch is used.

AABI-29
Generic instantiation does not require runtime generic metadata.

AABI-30
Raw pointers are distinct from integer values.

AABI-31
FFI boundaries are explicit.

AABI-32
Unknown FFI effects are conservatively modeled.

AABI-33
Object formats are target-native.

AABI-34
Machine backend cannot redefine language semantics.

AABI-35
Register allocation cannot change observable semantics.

AABI-36
Debug information does not participate in program semantics.

AABI-37
Panic/unwind implementation is runtime/profile dependent.

AABI-38
Startup initialization is capability-driven.

AABI-39
Axiom does not require an Axiom VM for native execution.

AABI-40
Third-party compiler backends may be used during bootstrap but are not semantic dependencies.
```

---

## Một kết luận quan trọng

Đến đây, mục tiêu **"Axiom không phụ thuộc LLVM/C compiler về mặt kiến trúc"** đã trở nên khả thi về mặt thiết kế.

Nhưng có một điểm tôi muốn **không vội freeze**: **machine backend cụ thể**.

Trước khi viết x86-64 backend, ta nên thiết kế một thứ còn quan trọng hơn:

### **AXIOM LIR v0.1 + Target Backend Contract**

Nó sẽ quyết định Axiom có thực sự portable giữa:

```text
x86-64
ARM64
RISC-V
WASM
```

hay cuối cùng frontend lại vô tình phụ thuộc x86.

Và đặc biệt, ta cần thiết kế **LIR đủ thấp để sinh machine code tốt như C/C++, nhưng đủ giàu để compiler không phải biến thành một bản sao của LLVM**.

Đây cũng là chỗ tôi nghĩ cần xem xét nghiêm túc một ý tưởng cho Axiom: **không xây một "LLVM thứ hai" khổng lồ**, mà xây một LIR tương đối nhỏ, deterministic, gần machine nhưng vẫn giữ một số semantic metadata từ MIR để optimizer của Axiom có lợi thế về ownership/alias/region.