# LVIII — WIN-ABI-002: Hoàn thiện Windows x64 ABI Lowering

Ta tiếp tục đúng nhánh đã chốt. Đây là phần cần hoàn thành **trước CodeView/PDB**, vì debugger chỉ có ý nghĩa khi calling convention và stack frame đã hoàn toàn ổn định.

Mục tiêu:

```text
Axiom Function Signature
        ↓
ABI Classification
        ↓
Argument/Return Assignment
        ↓
Shadow Space / Stack Layout
        ↓
Parallel Moves
        ↓
Machine IR
```

Windows x64 ABI dùng 4 register argument positions cho integer/pointer (`RCX,RDX,R8,R9`) và 4 vị trí tương ứng cho floating-point (`XMM0..XMM3`); các argument tiếp theo đi trên stack. Với các hàm gọi hàm khác, caller phải dành 32-byte shadow/home space. Return integer/pointer dùng `RAX`, floating-point dùng `XMM0`. citehttps://learn.microsoft.com/en-us/cpp/build/x64-calling-convention?view=msvc-170

---

## 1. ABI lowering không thuộc register allocator

Đây là điểm cần khóa.

Sai:

```text
Type
 ↓
Register Allocator tự đoán argument register
```

Đúng:

```text
Typed function signature
        ↓
Windows ABI classifier
        ↓
ABI locations
        ↓
Register allocator
```

Register allocator chỉ quyết định **virtual register nào cuối cùng nằm ở physical register nào**.

ABI classifier quyết định **argument phải đến vị trí nào**.

---

# 2. ABI model

Thêm:

```text
WindowsX64ABI {
    integer_arg_registers = [
        RCX,
        RDX,
        R8,
        R9
    ]

    float_arg_registers = [
        XMM0,
        XMM1,
        XMM2,
        XMM3
    ]

    integer_return = RAX
    float_return = XMM0

    shadow_space = 32
}
```

Không hard-code những register này trong generic instruction selector.

---

# 3. ABI Location

```text
ABILocation =
    Register(RegisterId)
    Stack(StackOffset)
    Indirect(PointerLocation)
    Split(...)
```

MVP trước mắt:

```text
Register
Stack
Indirect
```

`Split` cần thiết cho aggregate phức tạp hơn.

---

# 4. Argument classification

Mỗi argument:

```text
ABIArg {
    source_type
    passing_mode
    locations[]
}
```

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32
```

→

```text
a → RCX
b → RDX
return → RAX
```

---

# 5. Floating point

```axiom
fn add(a: f64, b: f64) -> f64
```

→

```text
a → XMM0
b → XMM1
return → XMM0
```

Không chuyển `f64` sang GPR chỉ vì allocator đang thiếu XMM register.

ABI classification xảy ra trước allocator.

---

# 6. Mixed arguments

Ví dụ:

```axiom
fn f(
    a: i32,
    b: f64,
    c: i64,
    d: f32
)
```

Windows x64 sử dụng **position-based register slots**, không đơn giản là "integer đếm riêng, float đếm riêng".

Conceptually:

```text
position 0 → a → RCX
position 1 → b → XMM1
position 2 → c → R8
position 3 → d → XMM3
```

Đây là điểm rất quan trọng.

Không được làm:

```text
a → RCX
b → XMM0
c → RDX
d → XMM1
```

---

# 7. ABI slot model

Do đó classifier nên dùng:

```text
ABIArgSlot {
    index: 0..3
    int_register
    float_register
}
```

Mapping:

```text
slot 0: RCX / XMM0
slot 1: RDX / XMM1
slot 2: R8  / XMM2
slot 3: R9  / XMM3
```

---

# 8. Stack arguments

Argument thứ 5 trở đi:

```text
Stack(...)
```

Ví dụ:

```axiom
fn f(
    a:i64,
    b:i64,
    c:i64,
    d:i64,
    e:i64
)
```

→

```text
a → RCX
b → RDX
c → R8
d → R9
e → stack
```

---

# 9. Shadow space ≠ stack arguments

Hai khái niệm phải tách biệt:

```text
Shadow Space
    32 bytes
```

và:

```text
Stack Arguments
    additional argument area
```

Không được coi:

```text
5th argument
```

là một phần của 32-byte shadow space.

---

# 10. Caller frame

Conceptually:

```text
higher addresses
────────────────────
stack arguments
────────────────────
return address
────────────────────
shadow/home space
+0   RCX home
+8   RDX home
+16  R8 home
+24  R9 home
────────────────────
RSP
```

Exact placement trong prologue/entry phải được biểu diễn bằng `FrameLayout`, không rải offset magic trong ABI code.

---

# 11. Caller responsibility

Một function call:

```text
foo(a,b)
```

có thể cần:

```text
allocate shadow space
place stack arguments
move register arguments
CALL
restore stack
```

Nhưng nếu function frame đã có đủ outgoing area:

```text
FrameInfo.outgoing_args_size
```

thì không cần `sub/add rsp` quanh từng call.

---

# 12. Outgoing argument area

Frame planner:

```text
FrameInfo {
    outgoing_args_size
}
```

phải tính:

```text
max stack arguments of any call
```

trong function.

Ví dụ:

```text
foo() // 0 stack args
bar(a,b,c,d,e,f,g) // 3 stack args
baz(...) // 1 stack arg
```

→ frame reserve đủ cho call lớn nhất.

---

# 13. Tail call

MVP:

```text
tailcall = disabled
```

Đừng cố nhét tailcall vào ABI đầu tiên.

Sau này:

```text
TailCallLowering
```

phải đảm bảo:

- shadow space
- stack arguments
- callee ABI
- caller frame compatibility
- callee-saved register state

---

# 14. Register moves

Ví dụ:

```text
fn caller(a:i64,b:i64) {
    callee(b,a)
}
```

Caller cần:

```text
RCX = b
RDX = a
```

nhưng hiện tại:

```text
RCX = a
RDX = b
```

Không thể:

```text
MOV RCX,RDX
MOV RDX,RCX
```

vì mất giá trị.

---

# 15. Parallel move

Ta đã dự kiến `ParallelMoveResolver`.

Representation:

```text
ParallelMove {
    source
    destination
}
```

Ví dụ:

```text
RCX → RDX
RDX → RCX
```

resolver sinh:

```text
MOV temp,RCX
MOV RCX,RDX
MOV RDX,temp
```

hoặc sử dụng stack/scratch register phù hợp.

---

# 16. ABI moves phải xảy ra trước register allocation cuối

Pipeline:

```text
Virtual ABI locations
        ↓
Parallel Move
        ↓
Register Allocation
```

hoặc ABI lowering có thể tạo các fixed-register constraints rồi allocator xử lý.

Axiom nên chọn mô hình thứ hai:

```text
ABI assignment
    ↓
fixed constraints
    ↓
register allocation
```

để giảm số copy thừa.

---

# 17. Fixed register constraint

Ví dụ:

```text
argument #0
```

tạo:

```text
VReg %arg0
constraint = MustBe(RCX)
```

Allocator sẽ đặt `%arg0` vào `RCX`.

Nếu source value đang ở `RAX`, copy/coalescing xử lý sau.

---

# 18. Call clobbers

Windows caller-saved:

```text
RAX
RCX
RDX
R8
R9
R10
R11
```

và XMM0–XMM5 là volatile.

Do đó:

```text
CALL foo
```

Machine IR phải có implicit defs:

```text
RAX
RCX
RDX
R8
R9
R10
R11
XMM0..XMM5
```

---

# 19. Callee-saved

```text
RBX
RBP
RSI
RDI
R12
R13
R14
R15
```

và:

```text
XMM6..XMM15
```

Nếu function dùng chúng, frame/prologue phải preserve.

---

# 20. Đây kết nối trực tiếp với unwind

Ví dụ allocator quyết định:

```text
v17 → RBX
```

Frame planner phát hiện:

```text
RBX used
```

→

```text
save RBX
```

→

```text
UnwindPlan:
UWOP_PUSH_NONVOL RBX
```

Do đó pipeline thực sự:

```text
Register Allocation
        ↓
Used Callee-Saved Registers
        ↓
FramePlan
        ↓
UnwindPlan
```

---

# 21. Return values

Scalar:

```text
i8/i16/i32/i64/u*
pointer
```

→ `RAX`.

`f32/f64`:

```text
XMM0
```

`never`:

```text
no return
```

---

# 22. Small aggregates

Đây là phần cần cẩn thận.

Không được dùng quy tắc đơn giản:

```text
struct → pointer
```

cho mọi struct.

Windows x64 có quy tắc riêng cho aggregate; một số aggregate nhỏ có thể truyền qua register, trong khi các aggregate không phù hợp được truyền gián tiếp. Microsoft mô tả việc truyền/return aggregate theo kích thước và loại; các loại không phù hợp được truyền qua temporary/copy và pointer. citehttps://learn.microsoft.com/en-us/cpp/build/x64-calling-convention?view=msvc-170

---

# 23. Axiom ABI classifier nên tách

```text
classify_scalar()
classify_float()
classify_vector()
classify_aggregate()
classify_return()
```

Không viết:

```text
if size <= 8 → register
```

vì sẽ nhanh chóng sai với các loại aggregate đặc biệt.

---

# 24. `@repr(C)` không đồng nghĩa "Axiom ABI"

Một struct:

```axiom
@repr(C)
struct Pair {
    a: i32
    b: i32
}
```

có:

```text
C-compatible layout
```

nhưng khi gọi function:

```text
extern "C" fn foo(Pair)
```

ABI classifier phải dùng:

```text
C ABI
```

không phải Axiom ABI.

---

# 25. ABI profile

Thêm abstraction:

```text
ABIProfile {
    calling_convention
    data_layout
    argument_classifier
    return_classifier
    register_convention
    stack_rules
    aggregate_rules
}
```

Windows x64:

```text
WindowsX64ABI
```

Linux:

```text
SysVAMD64ABI
```

sẽ implement cùng interface.

---

# 26. `extern "system"`

```axiom
extern "system" fn Foo(...)
```

được resolve:

```text
target.platform.system_abi
```

Windows:

```text
WindowsX64ABI
```

Linux:

```text
SysVAMD64ABI
```

Nhưng `"system"` **không phải** alias cố định cho Windows ABI trong language semantics.

---

# 27. `extern "C"`

Trên Windows x64:

```text
extern "C"
```

và:

```text
extern "system"
```

có thể map vào cùng low-level calling convention trong nhiều trường hợp.

Nhưng compiler **không được collapse hai ABI identities**.

Vì semantic identity vẫn khác:

```text
C
System
```

---

# 28. Function pointer ABI

Ví dụ:

```axiom
type Callback = extern "system" fn(i32) -> i32
```

function pointer phải mang:

```text
CallingConvention
```

trong type identity.

Không được coi:

```text
extern "C" fn(...)
```

và:

```text
extern "system" fn(...)
```

là cùng type một cách vô điều kiện.

---

# 29. Indirect call

```text
fn call(f: Callback) -> i32 {
    f(42)
}
```

Machine IR:

```text
MOV ECX,42
CALL RAX
```

nếu callback pointer nằm trong RAX.

ABI call metadata vẫn phải xác định:

```text
CC = WindowsX64
```

---

# 30. Variadic functions

Windows x64 có quy tắc đặc biệt cho varargs/unprototyped functions, trong đó floating-point arguments cũng có yêu cầu truyền tương ứng qua GPR. citehttps://learn.microsoft.com/en-us/cpp/build/x64-calling-convention?view=msvc-170

Axiom v0.1:

```text
extern "C" fn printf(format: CStr, ...) -> i32
```

có thể hỗ trợ ở unsafe/FFI layer.

Nhưng **không đưa variadic vào safe generic function system**.

---

# 31. ABI metadata

Thêm vào Machine IR:

```text
CallSite {
    callee
    calling_convention
    args[]
    returns[]
    clobbers[]
    tail_kind
}
```

Sau lowering:

```text
CALL {
    target
    cc = WindowsX64
    implicit_clobbers = ...
}
```

---

# 32. Stack alignment

Windows x64 yêu cầu stack alignment phù hợp ngoài các vùng prologue/epilogue; Microsoft ghi nhận yêu cầu 16-byte alignment cho stack ở các vùng thông thường. citehttps://learn.microsoft.com/en-us/cpp/build/x64-calling-convention?view=msvc-170

Frame planner phải đảm bảo:

```text
(RSP alignment) % 16 == 0
```

ở các call boundary thích hợp.

---

# 33. Shadow space

Mỗi call:

```text
CALL foo
```

phải có caller-owned:

```text
32 bytes
```

home space.

Không cần function callee sử dụng nó.

Nó tồn tại vì ABI yêu cầu caller cung cấp.

---

# 34. Leaf function optimization

Nếu:

```text
fn f() -> i32 {
    42
}
```

không gọi function:

```text
no outgoing call
```

→ không cần shadow space chỉ vì ABI định nghĩa shadow space cho calls.

Đây là một optimization quan trọng cho binary nhỏ.

---

# 35. Function entry không tự động allocate shadow space

Cần tránh một lỗi phổ biến:

```text
every function:
    sub rsp, 32
```

Sai.

Shadow space là **caller responsibility for a call**, không phải mandatory per-function stack allocation.

Nếu function không gọi ai:

```text
sub rsp,32
```

là overhead vô ích.

---

# 36. `main`

`main` cũng không phải ngoại lệ về ABI.

Ta có:

```text
__axiom_start
    ↓
call main
```

Startup caller phải tuân thủ Windows ABI.

`main` nhận/return:

```text
i32
```

và startup chuyển:

```text
EAX → ECX
```

cho:

```text
ExitProcess
```

---

# 37. ABI lowering repository

```text
compiler/abi/windows_x64/
├── profile.ax
├── registers.ax
├── slots.ax
├── classify.ax
├── aggregate.ax
├── arguments.ax
├── returns.ax
├── calls.ax
├── stack.ax
├── varargs.ax
├── moves.ax
├── verifier.ax
└── tests/
```

---

# 38. Generic backend interface

Không để Windows ABI xâm nhập x86 instruction selector.

```text
compiler/abi/
├── abi.ax
├── classify.ax
├── location.ax
└── verifier.ax
```

Target:

```text
compiler/targets/windows_x64/abi.ax
```

Linux:

```text
compiler/targets/linux_x64/abi.ax
```

---

# 39. ABI tests

### Scalar

```text
fn f(i32) -> i32
```

Expected:

```text
RCX → RAX
```

### Four arguments

```text
fn f(i64,i64,i64,i64)
```

Expected:

```text
RCX RDX R8 R9
```

### Fifth

```text
fn f(i64,i64,i64,i64,i64)
```

Expected:

```text
5th → stack
```

### Float

```text
fn f(f64,f32)
```

Expected:

```text
XMM0 XMM1
```

### Mixed

```text
fn f(i64,f64,i32,f32)
```

Expected:

```text
RCX XMM1 R8 XMM3
```

### Return

```text
i64 → RAX
f64 → XMM0
```

---

# 40. Aggregate tests

Phải có matrix:

```text
struct S1 { a:i8 }
struct S2 { a:i32 }
struct S3 { a:i64 }
struct S4 { a:i32; b:i32 }
struct S5 { a:f64 }
struct S6 { ... }
```

với:

```text
argument
return
extern "C"
extern "system"
Axiom ABI
```

Không được chỉ test scalar.

---

# 41. ABI differential test

Một trong những test mạnh nhất:

```text
Axiom caller
    ↓
C callee
```

và:

```text
C caller
    ↓
Axiom extern "C" callee
```

So sánh kết quả.

Đây là phần rất quan trọng của `SPEC-30 Conformance`.

---

# 42. Windows ABI oracle

Không dùng MSVC compiler để **xây Axiom**, nhưng có thể dùng một compiler độc lập trong test suite để xác minh ABI.

Ví dụ:

```text
Axiom ABI lowering
        ↕
reference ABI behavior
```

Reference compiler chỉ là **oracle**, không phải dependency của Axiom compiler.

Đúng với nguyên tắc đã freeze:

```text
third-party compiler
    = optional verification tool

third-party compiler
    ≠ required build dependency
```

---

# 43. ABI verifier

```text
AX_ABI_0001
invalid argument location

AX_ABI_0002
invalid return location

AX_ABI_0003
stack argument overlaps shadow space

AX_ABI_0004
stack alignment violation

AX_ABI_0005
invalid fixed-register assignment

AX_ABI_0006
invalid calling convention

AX_ABI_0007
aggregate classification mismatch

AX_ABI_0008
call clobber set incomplete

AX_ABI_0009
callee-saved register preservation mismatch

AX_ABI_0010
invalid variadic ABI lowering
```

---

# 44. Invariants

```text
AWABI-20
ABI classification occurs before physical register allocation.

AWABI-21
ABI locations are explicit.

AWABI-22
Windows x64 uses position-based four-register argument slots.

AWABI-23
Integer/pointer arguments use RCX/RDX/R8/R9.

AWABI-24
Floating arguments use XMM0/XMM1/XMM2/XMM3.

AWABI-25
Integer/pointer returns use RAX.

AWABI-26
Floating returns use XMM0.

AWABI-27
Caller shadow space is distinct from stack arguments.

AWABI-28
Shadow space is required at call sites, not universally in every function.

AWABI-29
Caller-saved registers are represented as call clobbers.

AWABI-30
Callee-saved registers are preserved by the callee when used.

AWABI-31
Stack arguments are represented by FramePlan.

AWABI-32
Parallel moves are resolved without value corruption.

AWABI-33
Calling convention is part of function-pointer ABI identity.

AWABI-34
Aggregate ABI classification is type-aware.

AWABI-35
Axiom ABI and C ABI remain distinct semantic profiles.

AWABI-36
System ABI is target-dependent.

AWABI-37
ABI lowering is deterministic.

AWABI-38
ABI lowering does not depend on an external compiler.

AWABI-39
ABI tests may use independent compilers as verification oracles.

AWABI-40
ABI lowering and unwind generation share the same FramePlan.
```

---

# 45. Pipeline sau task này

Bây giờ Windows backend đã có:

```text
LIR
 ↓
x86 ISel
 ↓
Machine IR
 ↓
Windows ABI lowering        ← hoàn thiện
 ↓
Register Allocation
 ↓
FramePlan
 ↓
Prologue/Epilogue
 ↓
UnwindPlan
 ↓
Encoder
 ↓
COFF
 ↓
PE Linker
 ↓
Import/IAT
 ↓
.pdata/.xdata
 ↓
PE32+
```

Đây đã đủ nền để bước tiếp theo chuyển từ **"chạy được"** sang **"debug được"**.

---

# LIX — CODEVIEW-001 sẽ là bước kế tiếp

Ta sẽ xây:

```text
Axiom source
      ↓
Debug Location
      ↓
Machine instruction
      ↓
CodeView records
      ↓
`.debug$S`
      ↓
`.debug$T`
      ↓
PDB generation
      ↓
WinDbg / debugger
```

Nhưng có một nguyên tắc: **không tự viết PDB linker ngay lập tức**. Trước hết phải xây **Debug IR + CodeView object records**, sau đó mới quyết định PDB writer/linker architecture.

Điều này cho phép:

```text
Axiom Debug IR
      ├── CodeView/PDB
      ├── DWARF
      └── future debug formats
```

thay vì biến compiler thành một compiler chỉ biết Windows.