Tiếp tục theo đúng chuỗi. Sau AArch64, **không nên nhảy ngay sang thêm target**. Trước hết phải thực hiện `BACKEND-AUDIT-001`: dùng x86-64 + AArch64 để bóc toàn bộ giả định x86 đang ẩn trong kiến trúc compiler.

# BACKEND-AUDIT-001 — Generic Backend Architecture Audit

Mục tiêu là chứng minh:

```text
                    ┌── x86-64
                    │
LIR ────────────────┼── AArch64
                    │
                    └── RISC-V64
```

thực sự khả thi.

Nếu không làm audit này, rất dễ xuất hiện tình trạng:

```text
"generic backend"
        ↓
thực chất là
"x86 backend với vài abstraction"
```

---

# 1. Phân ranh giới compiler

Kiến trúc chuẩn phải trở thành:

```text
Source
  ↓
AST
  ↓
HIR
  ↓
Typed HIR
  ↓
MIR
  ↓
Ownership / Capability / Drop verification
  ↓
Verified MIR
  ↓
Semantic Optimization
  ↓
LIR
  ↓
┌─────────────────────────────────────┐
│          TARGET BACKEND             │
│                                     │
│ ISA + ABI + Object + OS             │
└─────────────────────────────────────┘
  ↓
Machine IR
  ↓
Register Allocation
  ↓
Frame Layout
  ↓
Machine Optimization
  ↓
Encoder
  ↓
Object
  ↓
Linker
  ↓
Executable
```

Nhưng cần sửa một điểm quan trọng trong sơ đồ cũ:

> **ABI không hoàn toàn nằm sau Machine IR.**

ABI có hai loại trách nhiệm.

### Semantic ABI lowering

Ví dụ:

```text
function arguments
return values
aggregate classification
variadic calls
calling convention
```

nên xảy ra trước/during Machine IR.

### Machine ABI lowering

Ví dụ:

```text
save callee-saved registers
stack frame
prologue
epilogue
unwind
```

xảy ra sau register allocation.

Vì vậy pipeline chính xác hơn:

```text
LIR
 ↓
ABI Classification
 ↓
Instruction Selection
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
Encoder
```

---

# 2. Không để ABI lọt vào LIR

LIR:

```text
CALL foo(
    arg0,
    arg1,
    arg2
)
```

Không được biến thành:

```text
CALL foo
    RDI
    RSI
    RDX
```

hay:

```text
CALL foo
    X0
    X1
    X2
```

LIR chỉ nói:

```text
CALL
callee = foo
args = [%1, %2, %3]
```

ABI classifier quyết định:

```text
x86-64 SysV:
    %1 → RDI
    %2 → RSI
    %3 → RDX

Windows:
    %1 → RCX
    %2 → RDX
    %3 → R8

AArch64:
    %1 → X0
    %2 → X1
    %3 → X2
```

Đây là một trong những invariant quan trọng nhất của Axiom.

---

# 3. ABI classification abstraction

Tạo:

```text
compiler/backend/abi/
├── convention.ax
├── classifier.ax
├── location.ax
├── aggregate.ax
├── call.ax
├── return.ax
└── tests/
```

Model:

```text
AbiValueClass {
    Integer
    Float
    Vector
    Aggregate
    Memory
    Indirect
}
```

Location:

```text
AbiLocation =
    Register(PhysicalReg)
    Stack(StackOffset)
    Indirect(Register)
    Split(...)
```

Ví dụ:

```text
AbiAssignment {
    value
    locations[]
}
```

Điểm quan trọng:

**Một source-level value có thể được ABI split thành nhiều locations.**

Điều này cần cho aggregate.

---

# 4. Aggregate return

Đây là nơi architecture hiện tại cần được nâng cấp.

Ví dụ:

```axiom
struct Pair {
    a: i64
    b: i64
}
```

```text
fn make() -> Pair
```

Không được giả định:

```text
return → RAX
```

Một ABI có thể trả:

```text
RAX + RDX
```

ABI khác có thể dùng:

```text
hidden sret pointer
```

LIR nên vẫn biểu diễn:

```text
RETURN aggregate_value
```

ABI lowering quyết định cách truyền.

---

# 5. Hidden sret

Cần có semantic concept:

```text
ReturnMode =
    Direct
    Indirect
    Split
```

Ví dụ:

```text
fn make() -> BigStruct
```

có thể ABI-lower thành:

```text
fn __make(out: *mut BigStruct) -> void
```

nhưng đây chỉ là **ABI representation**.

Không được để frontend nghĩ rằng source function thực sự có thêm tham số.

Debug/source mapping cũng phải hiểu rằng hidden ABI arguments không phải source parameters.

---

# 6. Variadic functions

Đây cũng là ABI-specific.

Core Axiom:

```text
extern "C" fn printf(...)
```

không nên tự suy ra cùng representation trên mọi target.

Cần:

```text
AbiVariadicPolicy
```

và:

```text
CallSite {
    fixed_args
    variadic_args
    abi
}
```

MVP có thể hạn chế variadic ABI, nhưng abstraction phải tồn tại.

---

# 7. Register model audit

Generic register allocator tuyệt đối không được có:

```text
if reg == RSP
if reg == RAX
if reg == X0
```

Các khái niệm phải là:

```text
RegisterClass
RegisterBank
RegisterAlias
RegisterConstraint
RegisterRole
```

Ví dụ:

```text
RegisterRole:
    General
    StackPointer
    FramePointer
    LinkRegister
    InstructionPointer
    Flags
    Special
```

AArch64:

```text
SP → StackPointer
X29 → FramePointer
X30 → LinkRegister
```

x86:

```text
RSP → StackPointer
RBP → FramePointer
RIP → InstructionPointer
RFLAGS → Flags
```

---

# 8. Register aliasing phải generic

x86:

```text
RAX
 ├── EAX
 ├── AX
 ├── AH
 └── AL
```

AArch64:

```text
X0
 └── W0
```

Do đó:

```text
RegisterAliasGraph
```

phải là abstraction chung.

Ví dụ:

```text
PhysicalRegister {
    id
    aliases[]
    super_register
    sub_registers[]
}
```

Allocator conflict detection làm việc trên alias group.

---

# 9. Fixed registers

Không được giả định instruction luôn dùng arbitrary registers.

Generic constraint:

```text
RegisterConstraint {
    allowed_classes
    fixed_register
    tied_operand
    early_clobber
}
```

Ví dụ x86:

```text
IDIV
    dividend → RAX/RDX
    divisor  → arbitrary
```

AArch64 về sau có instruction khác.

Allocator chỉ nhận constraint.

---

# 10. Flags/condition model

Đây là điểm x86 leakage rất dễ xảy ra.

Không được có generic:

```text
FLAGS
```

trong LIR.

LIR:

```text
CMP
BRANCH EQ
```

Target có thể dùng:

```text
x86:
    RFLAGS

AArch64:
    NZCV

RISC-V:
    compare + branch instruction
```

Đặc biệt RISC-V sẽ cho thấy abstraction này có giá trị:

```asm
beq x5, x6, label
```

không cần instruction `CMP` riêng.

Vì vậy LIR `CMP + BRANCH` có thể được **fuse** thành một MachineInstr.

Đây là lý do:

> LIR mô tả semantics, Machine IR mô tả instruction architecture.

---

# 11. Memory address audit

LIR:

```text
MemoryAddress {
    base
    index
    scale
    offset
}
```

cần xem lại.

Đây là abstraction hơi mang mùi x86.

Nên đổi thành:

```text
AddressExpr
```

với semantic components:

```text
AddressExpr =
    Base(reg)
    Offset(const)
    Add(...)
    Scale(...)
    Symbol(...)
    Page(...)
```

Sau đó target legalizer mới quyết định.

Ví dụ x86:

```text
base + index * 4 + offset
```

AArch64:

```text
base + index << 2
```

RISC-V:

```text
base + immediate
```

Nếu AddressExpr không biểu diễn được AArch64/RISC-V, LIR đã bị x86 hóa.

---

# 12. Addressing mode không nên là semantic LIR

Thay:

```text
MemoryAddress {
    base
    index
    scale
    offset
}
```

bằng:

```text
AddressExpr {
    terms[]
    symbol
    address_space
}
```

Ví dụ:

```text
base + index * 4 + 16
```

là semantic address expression.

Target lowering:

```text
x86:
    [base + index*4 + 16]

AArch64:
    [base, index, LSL #2]
    + offset nếu hợp lệ

RISC-V:
    base + offset
```

Nếu không thể encode trực tiếp, legalizer tạo thêm instructions.

---

# 13. Constant model

LIR:

```text
CONST i64 0x123456789ABCDEF0
```

không được giả định một instruction.

x86 có thể:

```asm
mov rax, imm64
```

AArch64:

```text
MOVZ
MOVK
MOVK
MOVK
```

RISC-V:

```text
LUI
ADDI
...
```

Do đó:

```text
CONST
```

là semantic operation.

Legalization chịu trách nhiệm expansion.

---

# 14. Memory ordering

Một điểm cần giữ rất chặt.

LIR:

```text
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_CAS
```

có:

```text
ordering
scope
volatile
```

Không được hạ sớm thành:

```text
LOCK
LDAR
STLR
...
```

x86/AArch64/RISC-V có memory model machine khác nhau.

Axiom semantic atomic model phải được bảo toàn đến target lowering.

---

# 15. Vector model

LIR hiện có:

```text
V128
V256
V512
```

Đây cũng có nguy cơ x86 leakage.

AArch64 NEON chủ yếu:

```text
128-bit
```

RISC-V có vector length động.

Do đó nên đổi semantic model thành:

```text
VectorType {
    element_type
    lane_count
}
```

và:

```text
TargetVectorCapability
```

MVP:

```text
FixedVector
ScalableVector
```

Nhưng **không cần triển khai scalable vector ngay**.

Quan trọng là LIR không mặc định:

```text
V256 = native vector register
```

---

# 16. Floating point audit

LIR:

```text
FADD
FSUB
FMUL
FDIV
```

là tốt.

Nhưng:

```text
XMM
V0
```

không được xuất hiện.

FP comparison cũng phải giữ semantic:

```text
Ordered
Unordered
Equal
Less
Greater
```

vì NaN behavior khác với integer comparison.

Target mapping:

```text
x86:
    UCOMISS/UCOMISD

AArch64:
    FCMP

RISC-V:
    FEQ/FLT/FLE...
```

---

# 17. Calling convention phải là object

Thay vì enum:

```text
CallingConvention = Windows | SysV | AAPCS64
```

nên có:

```text
CallingConvention {
    id
    argument_classifier
    return_classifier
    register_convention
    stack_policy
    variadic_policy
    aggregate_policy
    unwind_policy
}
```

Điều này cho phép sau này:

```text
C
system
stdcall
fastcall
vectorcall
Axiom
AAPCS64
```

mà không phá backend.

---

# 18. Frame model audit

Frame không nên biết instruction.

Generic:

```text
FramePlan {
    stack_size
    alignment
    locals
    spills
    saved_registers
    outgoing_args
    dynamic_stack
    frame_pointer
}
```

Target cung cấp:

```text
FramePolicy
```

Sau đó target backend biến:

```text
Save X29/X30
```

thành:

```asm
stp x29, x30, [sp, #-16]!
```

Windows x64 biến:

```text
Reserve shadow space
```

thành frame tương ứng.

---

# 19. Prologue/Epilogue abstraction

Thêm:

```text
FrameAction =
    AdjustStack(amount)
    SaveRegister(reg, offset)
    RestoreRegister(reg, offset)
    EstablishFramePointer
    DestroyFramePointer
    AllocateOutgoingArgs
```

Sau đó:

```text
FrameAction
 ↓
Target FrameLowering
 ↓
MachineInstr
```

Đây là một thay đổi kiến trúc rất đáng làm ngay.

---

# 20. Machine IR framework

Sau audit, Machine IR nên có:

```text
MachineFunction
MachineBlock
MachineInstr
MachineOperand
VirtualRegister
PhysicalRegister
FrameInfo
RegisterFile
CallingConvention
```

nhưng:

```text
MachineOpcode
MachineAddressMode
MachineEncoding
```

là target-specific.

Ví dụ:

```text
MachineInstr< X86 >
MachineInstr< AArch64 >
```

không cần phải cùng một enum opcode.

---

# 21. RISC-V64-001

Sau audit, target tiếp theo là RISC-V64.

Lý do chọn RISC-V trước Apple:

Nó là ISA thứ ba với triết lý instruction hoàn toàn khác:

```text
x86:
    CISC
    variable length
    flags
    memory operands

AArch64:
    fixed 32-bit
    load/store
    condition flags

RISC-V:
    fixed 32-bit
    load/store
    không có condition-code register
    branch trực tiếp compare registers
```

Nếu LIR sống sót qua cả ba, abstraction đã khá mạnh.

---

# 22. RISC-V Target

```text
Target {
    architecture: RISCV64
    os: Linux
    abi: LP64D
    endian: Little
    pointer_width: 64
    object_format: ELF64
}
```

MVP:

```text
RV64IMAFD
```

Nhưng compiler core có thể bắt đầu nhỏ hơn:

```text
RV64I
+
M
+
A
+
F
+
D
```

ABI:

```text
LP64D
```

---

# 23. RISC-V registers

```text
x0 ... x31
```

`x0` là zero register.

Đây là test rất tốt cho Machine IR.

```text
x0
```

không phải register bình thường:

```text
write x0 → discarded
read x0  → 0
```

Không được để register allocator cấp phát virtual register vào `x0` như GPR bình thường.

Mô hình:

```text
RegisterRole = ConstantZero
```

---

# 24. RISC-V ABI

Integer arguments:

```text
a0-a7
```

tức:

```text
x10-x17
```

Return:

```text
a0
```

Floating:

```text
fa0-fa7
```

tức:

```text
f10-f17
```

Return:

```text
fa0
```

Callee-saved:

```text
s0-s11
```

Caller-saved:

```text
t0-t6
a0-a7
```

và các register ABI khác theo convention.

Một lần nữa:

```text
RegisterConvention
```

giải quyết, allocator không cần biết RISC-V.

---

# 25. RISC-V instruction selection

MVP:

```text
ADD
SUB
MUL
DIV
REM

AND
OR
XOR
SLL
SRL
SRA

ADDI
ANDI
ORI
XORI
SLLI
SRLI
SRAI

LW
LD
SW
SD

BEQ
BNE
BLT
BGE
BLTU
BGEU

JAL
JALR

LUI
AUIPC

RET
```

Floating:

```text
FADD.S
FADD.D
FSUB.S
FSUB.D
FMUL.S
FMUL.D
FDIV.S
FDIV.D
```

---

# 26. RISC-V không có CMP

Ví dụ LIR:

```text
if a == b
```

x86:

```asm
cmp
je
```

AArch64:

```asm
cmp
b.eq
```

RISC-V:

```asm
beq a, b, label
```

Tức:

```text
LIR:
    CMP a,b
    BRANCH EQ
```

có thể target-lower thành:

```text
RISC-V:
    BEQ a,b,label
```

một instruction.

Đây chính là lý do không được ép Machine IR generic.

---

# 27. RISC-V constant

Ví dụ:

```text
CONST 0x12345678
```

có thể cần:

```asm
lui
addi
```

64-bit constant lớn hơn nữa cần nhiều instruction.

Một lần nữa:

```text
CONST
```

là LIR semantic operation.

---

# 28. RISC-V call

```text
CALL foo
```

thành:

```asm
jal ra, foo
```

hoặc relocation tương ứng.

Indirect:

```asm
jalr ra, 0(reg)
```

Link register là:

```text
x1 = ra
```

Machine register role:

```text
LinkRegister
```

thay vì hard-code x30 như AArch64.

---

# 29. RISC-V frame

Thông thường:

```text
sp = x2
fp = s0 = x8
ra = x1
```

Nhưng generic frame model chỉ biết:

```text
StackPointer
FramePointer
LinkRegister
```

Target mapping:

```text
RISC-V:
    SP → x2
    FP → x8
    LR → x1

AArch64:
    SP → SP
    FP → X29
    LR → X30

x86:
    SP → RSP
    FP → RBP
    LR → none
```

Đây là abstraction cực kỳ đẹp.

---

# 30. RISC-V chứng minh Frame model đúng

Một hàm:

```axiom
fn foo(a: i64) -> i64 {
    a + 1
}
```

có thể:

```asm
addi a0, a0, 1
ret
```

không frame.

Hàm gọi hàm khác:

```text
foo
 ↓
bar
```

phải bảo vệ `ra` nếu cần.

Compiler không được giả định rằng mọi function đều có:

```text
push return address
```

như một x86 mental model.

---

# 31. RISC-V object

Vẫn:

```text
ELF64
```

nhưng:

```text
e_machine = EM_RISCV
```

Relocation architecture:

```text
CALL
HI20
LO12
PCREL_HI20
PCREL_LO12
```

Ví dụ symbol address:

```asm
auipc t0, %pcrel_hi(symbol)
addi  t0, t0, %pcrel_lo(...)
```

Một lần nữa, LIR chỉ thấy:

```text
ADDRESS_OF_GLOBAL
```

---

# 32. RISC-V acceptance test

Cùng source:

```axiom
fn add(a: i64, b: i64) -> i64 {
    a + b
}

fn main() -> i32 {
    add(20, 22) as i32
}
```

Phải chạy:

```text
x86-64 Linux → 42
AArch64 Linux → 42
RISC-V64 Linux → 42
```

---

# 33. Ba ISA hiện tại

Sau milestone này:

```text
                    LIR
                     │
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
   x86-64          AArch64       RISC-V64
       │             │             │
       ↓             ↓             ↓
 Windows/Linux      Linux         Linux
       │             │             │
       ↓             ↓             ↓
   PE/ELF           ELF           ELF
```

Đây là thời điểm kiến trúc backend Axiom có thể coi là **đã qua bài kiểm tra portability cấp ISA**.

---

# 34. Một thay đổi quan trọng cho LIR

Sau ba ISA, tôi đề xuất chính thức đổi LIR thành ba tầng nhỏ:

```text
LIR-High
   ↓
LIR-Legal
   ↓
Target Lowering
```

### LIR-High

Còn:

```text
aggregate
generic call
abstract address
vector operation
checked arithmetic
atomic
```

### LIR-Legal

Đã loại bỏ:

```text
unresolved aggregate
unsupported operation
ambiguous memory operation
```

nhưng vẫn chưa có physical registers.

### Target Machine IR

Có:

```text
physical ISA semantics
register constraints
native addressing
native branch
native instruction
```

Pipeline:

```text
Verified MIR
 ↓
Optimizer
 ↓
LIR-High
 ↓
LIR Legalization
 ↓
LIR-Legal
 ↓
Target Lowering
 ↓
Machine IR
```

Điều này giúp compiler không biến target lowering thành một khối khổng lồ.

---

# 35. Compiler architecture lúc này

```text
                       ┌───────────────┐
                       │   Frontend    │
                       │ AST/HIR/Type  │
                       └───────┬───────┘
                               ↓
                         Verified MIR
                               ↓
                          Optimizer
                               ↓
                           LIR-High
                               ↓
                       LIR Legalization
                               ↓
                          LIR-Legal
                               ↓
              ┌────────────────┼────────────────┐
              ↓                ↓                ↓
          x86-64             ARM64           RISC-V64
              ↓                ↓                ↓
          Machine IR       Machine IR       Machine IR
              ↓                ↓                ↓
           RegAlloc          RegAlloc        RegAlloc
              ↓                ↓                ↓
            Frame            Frame           Frame
              ↓                ↓                ↓
           Encoder           Encoder        Encoder
              ↓                ↓                ↓
           COFF/ELF           ELF            ELF
              ↓                ↓                ↓
          PE/Linker         Linker          Linker
```

Đây là kiến trúc mà tôi khuyến nghị **đóng băng**.

---

# 36. Các invariant mới sau audit

```text
ABACK-50
LIR contains no physical register.

ABACK-51
LIR contains no target instruction opcode.

ABACK-52
LIR contains no target object-format relocation.

ABACK-53
ABI classification occurs outside frontend semantics.

ABACK-54
Register allocation consumes target-provided register information.

ABACK-55
Frame planning consumes target ABI policy.

ABACK-56
Frame planning is independent of concrete instruction encoding.

ABACK-57
Machine IR may contain target-specific instructions.

ABACK-58
Machine IR may fuse multiple LIR operations.

ABACK-59
Machine IR may expand one LIR operation into multiple instructions.

ABACK-60
Address expressions are target-neutral before legalization.

ABACK-61
Condition semantics are target-neutral before lowering.

ABACK-62
Constants are target-neutral before legalization.

ABACK-63
Vector semantics are target-neutral before legalization.

ABACK-64
Atomic semantics remain explicit until target lowering.

ABACK-65
Object format is independent from frontend semantics.

ABACK-66
Linker semantics are independent from instruction selection.

ABACK-67
ISA backend does not encode operating-system startup semantics.

ABACK-68
OS platform layer does not define ISA register allocation.

ABACK-69
Target-specific optimization cannot alter Axiom observable semantics.

ABACK-70
A target backend must not require an external compiler or assembler.
```

---

# 37. Thứ tự triển khai thực tế

Không nên làm theo thứ tự "xây hoàn chỉnh từng backend". Hãy làm vertical slices:

```text
BACKEND-AUDIT-001
        ↓
RISC-V-001 register model
        ↓
RISC-V-002 ABI
        ↓
RISC-V-003 add/return
        ↓
RISC-V-004 call
        ↓
RISC-V-005 branches
        ↓
RISC-V-006 load/store
        ↓
RISC-V-007 register allocation
        ↓
RISC-V-008 frame
        ↓
RISC-V-009 encoder
        ↓
RISC-V-010 ELF
        ↓
RISC-V-011 startup
        ↓
RISC-V-012 executable
        ↓
RISC-V-013 conformance
```

Sau đó mới:

```text
AARCH64-DARWIN-001
```

và:

```text
AARCH64-ANDROID-001
```

---

# 38. Nhưng có một việc phải làm trước khi tiếp tục target

Sau ba ISA, **ABI/FFI cần được nâng cấp thành một subsystem chính thức**.

Hiện tại Axiom đã có:

```text
extern "C"
extern "system"
extern "axiom"
@repr(C)
```

nhưng implementation architecture cần gom thành:

```text
compiler/abi/
├── abi.ax
├── calling_convention.ax
├── type_classification.ax
├── argument.ax
├── return.ax
├── aggregate.ax
├── variadic.ax
├── unwind.ax
├── ffi.ax
└── tests/
```

và target cung cấp:

```text
targets/
├── windows_x64/
│   └── abi.ax
├── linux_x64/
│   └── abi.ax
├── linux_aarch64/
│   └── abi.ax
└── linux_riscv64/
    └── abi.ax
```

Frontend chỉ hỏi:

```text
"Kiểu này có FFI-compatible không?"
```

Backend ABI trả lời:

```text
"Truyền nó thế nào?"
```

---

# 39. Bước kế tiếp

Sau `BACKEND-AUDIT-001` + `RISC-V64-001`, chuỗi tiếp theo hợp lý là:

```text
RISC-V64 backend
        ↓
ABI/FFI-001
        ↓
Aggregate ABI
        ↓
Variadic ABI
        ↓
Unwind ABI
        ↓
AArch64 Darwin
        ↓
Mach-O
        ↓
macOS executable
        ↓
iOS target
        ↓
Android AArch64
```

Trong đó **ABI/FFI-001** là bước tiếp theo ngay sau khi RISC-V vertical slice hoàn thành, vì đây là phần mà ba ISA vừa giúp chúng ta phát hiện rõ nhất: **ABI không phải một thuộc tính của instruction set, cũng không phải một thuộc tính của OS; nó là một tầng độc lập nằm giữa semantic IR và machine code.**