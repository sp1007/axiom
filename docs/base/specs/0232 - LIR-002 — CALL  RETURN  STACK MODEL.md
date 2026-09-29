Tiếp tục với **LIR-002 — CALL / RETURN / STACK MODEL**. Đây là lớp rất quan trọng vì nó quyết định Axiom LIR có đủ mạnh để làm backend native thực sự hay không.

# LIR-002 — CALL / RETURN / STACK MODEL

## 1. Mục tiêu của LIR

Axiom LIR phải nằm đúng giữa:

```text
Verified MIR
      ↓
ABI Lowering
      ↓
       LIR
      ↓
Target Legalization
      ↓
Machine IR
```

LIR **không biết CPU cụ thể**.

Nó biết các khái niệm:

```text
Virtual Register
Memory
Stack Slot
Call
Return
Branch
Address
Load/Store
Atomic
Vector
ABI location
```

Nhưng chưa biết:

```text
RAX
RCX
XMM0
ADD rax, rbx
```

Như vậy cùng một LIR có thể đi tới:

```text
x86-64
AArch64
RISC-V64
```

---

# 2. Nguyên tắc quan trọng nhất

LIR không nên trở thành "LLVM IR phiên bản khác".

Axiom đã có MIR làm semantic IR.

LIR chỉ nên trả lời:

> **Giá trị này cần được biểu diễn và vận chuyển như thế nào để cuối cùng có thể thực hiện trên máy thật?**

Do đó:

```text
MIR
= semantic

LIR
= machine-independent low-level representation

Machine IR
= physical target representation
```

---

# 3. Virtual Register

LIR sử dụng virtual registers:

```text
v0
v1
v2
v3
```

Ví dụ:

```text
fn add(a: i64, b: i64) -> i64 {
    return a + b;
}
```

LIR:

```text
v0 = PARAM 0
v1 = PARAM 1
v2 = ADD v0, v1
RET v2
```

Không có:

```text
RDI
RSI
RAX
```

Register allocator về sau mới quyết định.

---

# 4. Register Class

Virtual register nên có class hoặc constraint:

```text
v0 : GPR
v1 : FPR
v2 : VECTOR
```

Ví dụ:

```text
v0 = PARAM i64
v1 = PARAM f64
v2 = ADD_FLOAT v1, v1
```

Backend biết:

```text
i64 → GPR
f64 → FPR
```

---

# 5. Nhưng không phải mọi giá trị đều là register

LIR cần hỗ trợ:

```text
Register
StackSlot
Memory
Immediate
Constant
Address
```

Ví dụ:

```text
LOAD v1, [v0 + 16]
```

và:

```text
STORE [v0 + 24], v2
```

---

# 6. Stack Slot

Stack slot là abstract storage:

```text
StackSlot {
    id
    size
    alignment
    lifetime
    kind
}
```

Ví dụ:

```text
slot0 : 8 bytes, align 8
slot1 : 32 bytes, align 16
```

Chưa có offset:

```text
-24(%rbp)
```

Frame layout pass sẽ quyết định.

---

# 7. Stack Slot không đồng nghĩa spill

Đây là phân biệt quan trọng.

Có hai nguồn:

### Semantic stack object

Ví dụ:

```text
large local struct
sret destination
outgoing argument
```

### Register spill

Do register allocator quyết định:

```text
v17 → spill slot
```

Không nên trộn chúng.

```text
StackSlot.kind =
    Local
    Spill
    IncomingArg
    OutgoingArg
    SRet
    Temp
```

---

# 8. CALL

Instruction:

```text
CALL callee
```

không nên tự chứa tất cả register mapping.

Trước CALL phải có:

```text
ABI assignment
```

Ví dụ:

```text
v0 = PARAM 0
v1 = PARAM 1

ARG_MOVE GPR0 <- v0
ARG_MOVE GPR1 <- v1

CALL foo
```

Nhưng vẫn chưa phải physical register.

Thay vào đó:

```text
ABI_ARG GPR_CLASS[0] <- v0
ABI_ARG GPR_CLASS[1] <- v1
```

Target lowering chuyển thành:

```text
RDI <- v0
RSI <- v1
```

---

# 9. ABI location nên tồn tại trong LIR

Ví dụ:

```text
ABI_ARG {
    location = ArgRegister(0)
    value = v0
}
```

hoặc:

```text
ABI_ARG {
    location = StackArg(16)
    value = v1
}
```

Điều này giúp ABI lowering hoàn tất trước Machine IR.

---

# 10. CALL result

Ví dụ:

```text
v2 = CALL foo(v0, v1)
```

sau ABI:

```text
CALL foo
ABI_RESULT v2 <- ReturnRegister(0)
```

Machine lowering:

```text
CALL foo
v2 = COPY RAX
```

Register allocator có thể tối ưu copy này.

---

# 11. Multi-value return

Ví dụ:

```text
struct Pair {
    a: u64
    b: u64
}
```

ABI:

```text
RAX = a
RDX = b
```

LIR:

```text
CALL make_pair

v0 = ABI_RESULT 0
v1 = ABI_RESULT 1

...
```

hoặc:

```text
v0, v1 = CALL make_pair
```

Tôi nghiêng về representation:

```text
CALL_RESULT {
    result_tuple_id
    parts[]
}
```

vì nó biểu diễn aggregate return rõ ràng hơn.

---

# 12. `sret`

Ví dụ:

```text
fn make_big() -> Big
```

ABI lowering:

```text
slot0 = STACK_ALLOC sizeof(Big)

ABI_ARG SRET <- ADDRESS(slot0)

CALL make_big

v0 = ADDRESS(slot0)
```

Semantic result vẫn là:

```text
Big
```

LIR physical strategy là:

```text
caller allocated storage
```

---

# 13. `SRET` không nhất thiết là stack

Ví dụ optimizer có thể đã có:

```text
v0 = some caller-owned object
```

hoặc:

```text
heap object
```

hoặc:

```text
register/scalarized aggregate
```

LIR chỉ nói:

```text
ADDRESS destination
```

không nói:

```text
must be stack
```

---

# 14. Stack pointer

Không nên để generic LIR trực tiếp dùng:

```text
SP
FP
RSP
```

Nên có:

```text
STACK_BASE
FRAME_BASE
```

trừ khi operation thực sự yêu cầu target-specific behavior.

Ví dụ:

```text
STACK_ADDR slot0
```

thay vì:

```text
RSP + 32
```

---

# 15. Frame lowering

Sau register allocation:

```text
StackSlot
```

được biến thành:

```text
frame_offset
```

Ví dụ:

```text
slot0 → -24
slot1 → -64
```

Sau đó target backend quyết định:

```text
RSP
RBP
FP
red-zone
```

---

# 16. Frame layout

Nên có pass riêng:

```text
FrameLayout
```

đầu vào:

```text
stack slots
callee saves
spill slots
outgoing arguments
alignment
red zone
```

đầu ra:

```text
StackFrame {
    size
    alignment
    locals[]
    spills[]
    outgoing_args[]
    callee_saves[]
    fp_required
}
```

---

# 17. Prologue / Epilogue

Không đưa prologue vào source-level MIR.

Machine lowering tạo:

```text
PROLOGUE
...
EPILOGUE
RET
```

Sau đó target-specific expansion:

x86-64 có thể thành:

```text
push rbp
mov rbp, rsp
sub rsp, N
```

AArch64 có thể hoàn toàn khác.

---

# 18. Callee-saved registers

Register allocator cần biết:

```text
caller_saved
callee_saved
```

nhưng LIR không hard-code tên register.

Ví dụ:

```text
RegisterClass GPR {
    caller_saved: [...]
    callee_saved: [...]
}
```

Target ABI cung cấp danh sách.

---

# 19. CALL clobbers

Một CALL phải mô tả register effects.

Ví dụ:

```text
CALL foo
```

có thể clobber:

```text
GPR caller-saved
FPR caller-saved
flags
```

Không phải:

```text
CALL
```

xóa toàn bộ virtual register state.

Register allocator sẽ dùng call-clobber information để quyết định spill/save.

---

# 20. Call clobber model

Đề xuất:

```text
CallClobber {
    registers
    register_classes
    flags
    memory
}
```

Ví dụ:

```text
CALL @pure_function
```

vẫn có thể clobber registers.

`pure` không nên trở thành machine assumption trừ khi compiler fact xác nhận.

---

# 21. Memory effect

CALL cần memory semantics.

Không phải mọi call đều giống nhau.

Ví dụ:

```text
fn foo()
```

có thể:

```text
read memory
write memory
```

Trong LIR:

```text
CALL {
    memory_effect = Unknown
}
```

Một intrinsic/compiler-known operation có thể:

```text
ReadOnly
WriteOnly
ReadWrite
NoMemory
```

Điều này giúp optimizer.

Nhưng nó là **compiler fact**, phù hợp với quyết định trước đây không tạo user-visible effect system.

---

# 22. CALL và alias analysis

Ví dụ:

```text
v1 = LOAD p
CALL foo()
v2 = LOAD p
```

Nếu:

```text
foo
```

có thể ghi memory:

```text
v2
```

không thể lấy từ cache cũ.

Nếu compiler chứng minh:

```text
foo: NoMemory
```

thì có thể giữ.

Do đó LIR call cần:

```text
MemoryEffect
```

nhưng không cần biến nó thành source syntax.

---

# 23. TailCall

LIR:

```text
TAILCALL foo
```

khác:

```text
CALL foo
RET
```

Tailcall lowering phải kiểm tra:

```text
same ABI?
compatible return?
frame removable?
arguments compatible?
unwind compatible?
```

Nếu không:

```text
TAILCALL
```

không hợp lệ.

---

# 24. MustTail

Không nên vội đưa:

```text
musttail
```

vào source v1.

Nhưng LIR có thể có:

```text
TailCallKind =
    Normal
    Guaranteed
```

Foreign/compiler intrinsic có thể yêu cầu guaranteed tail call.

---

# 25. Indirect call

```text
v0 = LOAD_FUNCTION_PTR
CALL_INDIRECT v0
```

ABI vẫn phải được xác định.

Ví dụ:

```text
fn(i32) -> i32
```

không được gọi bằng ABI của:

```text
extern "C" fn(i32) -> i32
```

nếu chúng khác nhau.

LIR:

```text
CALL_INDIRECT {
    target: v0
    abi: AxiomNative
}
```

---

# 26. `dyn Trait` call

Ví dụ:

```text
obj.draw()
```

sau semantic resolution:

```text
DYNAMIC_CALL {
    data
    vtable
    slot
}
```

Sau LIR:

```text
v0 = LOAD [vtable + method_offset]
CALL_INDIRECT v0
```

hoặc backend có thể có:

```text
VTABLE_CALL
```

để tối ưu sau.

---

# 27. Closure call

Capturing closure:

```text
f(x)
```

có thể thành:

```text
CALL_INDIRECT {
    code = f.code
    env  = f.environment
}
```

Noncapturing:

```text
CALL function_pointer
```

Inlining có thể xóa hoàn toàn abstraction.

---

# 28. Stack arguments

Nếu arguments vượt register budget:

```text
ABI_ARG StackArg(...)
```

Frame layout phải biết:

```text
outgoing argument area
```

Ví dụ:

```text
slot_out0
slot_out1
```

Không nên để mỗi CALL tự sửa `SP`.

Thay vào đó:

```text
CALL_FRAME_SETUP
CALL
```

hoặc frame layout reserve outgoing area.

---

# 29. Dynamic stack allocation

Axiom có thể cần:

```text
alloca
```

cho:

- dynamic local arrays
- FFI
- low-level system code

Nhưng:

```text
STACK_ALLOC_DYNAMIC
```

phải là explicit LIR operation.

Nó ảnh hưởng:

```text
frame pointer
stack alignment
unwind
stack probing
```

---

# 30. Stack probing

Windows hoặc các target có guard pages có thể yêu cầu stack probing với frame lớn.

Đây là target lowering:

```text
LIR:
STACK_ALLOC_DYNAMIC

↓

Machine:
stack probing sequence
```

Không để frontend biết.

---

# 31. `alloca` và capability

Nếu Axiom cho phép:

```text
let p = stack_alloc(...)
```

thì compiler phải theo dõi:

```text
storage lifetime
capability provenance
```

Không được để raw address sống sau frame.

Safe abstraction nên dùng compiler-managed storage.

---

# 32. Load/Store

LIR:

```text
LOAD
STORE
```

phải có:

```text
type
size
alignment
volatile
atomic
ordering
address_space
```

Ví dụ:

```text
LOAD {
    dst: v0
    addr: v1
    type: i32
    alignment: 4
    volatile: false
}
```

---

# 33. Address space

LIR phải có:

```text
AddressSpace =
    Generic
    Stack
    Global
    TLS
    Device
    Shared
    Constant
    ...
```

CPU backend có thể collapse nhiều loại thành Generic.

GPU backend không được.

---

# 34. Atomic

Atomic không nên biến thành:

```text
LOAD + STORE
```

ở LIR.

Ví dụ:

```text
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
FENCE
```

với:

```text
MemoryOrder
MemoryScope
```

Target lowering mới chọn instruction.

---

# 35. Volatile

Phải giữ riêng:

```text
VOLATILE_LOAD
VOLATILE_STORE
```

Không đồng nghĩa atomic.

Ví dụ:

```text
volatile = true
```

không tạo synchronization.

---

# 36. Memory barrier

LIR:

```text
FENCE
```

không nên biến thành CPU instruction ngay.

Ví dụ:

```text
FENCE Acquire
```

AArch64:

```text
DMB ish
```

x86-64 có thể cần rất ít hoặc không cần instruction tùy semantics.

---

# 37. Call/Return verifier

Trước Machine IR cần:

```text
LIRVerifier
```

kiểm tra:

### Call

- ABI hợp lệ
- argument count
- argument locations
- register classes
- variadic compatibility
- indirect call signature
- return locations
- clobbers
- memory effects
- tail-call constraints

### Return

- return values đúng ABI
- sret hoàn tất
- aggregate parts đầy đủ
- Drop/ownership đã xử lý
- stack frame hợp lệ

---

# 38. LIR instruction set tối thiểu

Tôi đề xuất MVP:

```text
CONST
COPY

ADD
SUB
MUL
DIV
REM

AND
OR
XOR
SHL
SHR

CMP
SELECT

LOAD
STORE
ADDRESS

ALLOCA
STACK_ADDR

PHI

BR
COND_BR
SWITCH

CALL
CALL_INDIRECT
TAILCALL
RET

ABI_ARG
ABI_RESULT
SRET

ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
FENCE

TRAP
UNREACHABLE
```

Không cần hàng trăm instruction ở LIR.

---

# 39. Phi và SSA

Axiom LIR nên vẫn là SSA.

Ví dụ:

```text
entry:
    v0 = PARAM 0
    BR cond, then, else

then:
    v1 = ADD v0, 1
    BR merge

else:
    v2 = ADD v0, 2
    BR merge

merge:
    v3 = PHI(v1, v2)
    RET v3
```

Register allocation sau đó phá SSA nếu cần.

---

# 40. Memory không phải SSA

Memory không nên biến thành:

```text
memory0
memory1
memory2
```

kiểu full memory SSA bắt buộc.

Axiom nên giữ:

```text
LOAD
STORE
```

với alias analysis riêng.

Compiler có thể tạo Memory SSA nội bộ khi optimization cần.

Điều này giữ LIR đơn giản hơn.

---

# 41. Calling convention không nằm trong CALL opcode duy nhất

Không nên:

```text
CALL_C
CALL_AXIOM
CALL_WIN64
CALL_SYSV
```

Thay vào đó:

```text
CALL {
    convention: ABIConvention
}
```

Target lowering đọc convention.

Như vậy:

```text
CALL
```

là một semantic low-level operation.

---

# 42. Inline assembly

Đây là phần cần quyết định.

Tôi đề xuất **không cho inline assembly trực tiếp trong LIR**.

Source/system layer có:

```text
asm(...)
```

được hạ thành:

```text
INLINE_ASM
```

với:

```text
inputs
outputs
clobbers
memory_effect
constraints
```

Sau đó Machine IR mới hiểu syntax/constraints của target.

Điều này tránh contaminating LIR với x86 assembly syntax.

---

# 43. Inline ASM phải khai báo clobber

Ví dụ conceptual:

```text
asm {
    "..."
    in(reg) x
    out(reg) y
    clobber(...)
}
```

Compiler phải biết:

```text
register effects
memory effects
flags
```

Nếu programmer khai báo sai trong `unsafe`:

```text
```

đó là trách nhiệm unsafe.

Nhưng compiler vẫn phải preserve những gì đã khai báo.

---

# 44. Calling convention + unsafe

Không nên coi:

```text
unsafe
```

là:

```text
ignore ABI
```

Unsafe chỉ cho phép programmer thực hiện operations compiler không thể prove.

ABI vẫn phải đúng.

---

# 45. LIR ownership

Một điểm đặc biệt:

MIR còn có:

```text
MOVE
DROP
```

LIR không nhất thiết cần semantic ownership.

Sau Verified MIR:

```text
MOVE
DROP
```

đã được elaborated.

LIR chỉ cần đảm bảo:

```text
value is materialized correctly
cleanup calls happen where required
```

Ví dụ:

```text
DROP Resource
```

có thể đã biến thành:

```text
CALL Resource.drop
```

hoặc inline code.

---

# 46. Nhưng Drop không nên luôn là CALL

Optimizer có thể thấy:

```text
Drop<i32>
```

không làm gì.

Xóa.

Hoặc:

```text
Drop<Vec>
```

inline:

```text
if capacity != 0:
    allocator.deallocate(...)
```

Hoặc toàn bộ Vec đã scalarize.

Do đó:

```text
Drop
```

là semantic MIR concept.

LIR chỉ chứa machine-observable consequence.

---

# 47. LIR memory model

LIR phải giữ đủ information để optimizer không phá:

```text
atomic
volatile
alias
alignment
address space
```

Nhưng có thể xóa:

```text
ownership
borrow region
trait constraint
generic parameter
```

nếu chúng không còn observable.

Đây là ranh giới rất đẹp:

```text
MIR = semantic proof
LIR = optimized physical intent
Machine IR = exact target mechanics
```

---

# 48. LIR invariant set

### ALIR-20
**LIR Is Below Semantic Verification**

### ALIR-21
**LIR Contains No Unresolved Ownership Rules**

### ALIR-22
**LIR Uses Virtual Registers**

### ALIR-23
**LIR Is Target-Independent Before Legalization**

### ALIR-24
**Physical Register Names Do Not Appear In Generic LIR**

### ALIR-25
**Register Classes Are Explicit**

### ALIR-26
**Stack Slots Are Abstract Before Frame Layout**

### ALIR-27
**Semantic Stack Objects Are Distinct From Spill Slots**

### ALIR-28
**ABI Arguments Are Explicitly Represented**

### ALIR-29
**ABI Results Are Explicitly Represented**

### ALIR-30
**sret Is Explicit In ABI/LIR**

### ALIR-31
**CALL Preserves ABI Contract**

### ALIR-32
**CALL Clobbers Are Explicit**

### ALIR-33
**CALL Memory Effects Are Represented**

### ALIR-34
**Tail Calls Require ABI Compatibility**

### ALIR-35
**Indirect Calls Preserve Function ABI**

### ALIR-36
**Dynamic Dispatch Is Explicit Before Lowering**

### ALIR-37
**Closure Environment Passing Is Explicit After Lowering**

### ALIR-38
**Stack Frame Layout Is A Separate Pass**

### ALIR-39
**Prologue/Epilogue Are Target-Lowered**

### ALIR-40
**Stack Allocation Does Not Imply Heap Allocation**

### ALIR-41
**Atomic Operations Remain Atomic In LIR**

### ALIR-42
**Volatile Is Distinct From Atomic**

### ALIR-43
**Address Spaces Are Preserved Until Target Lowering**

### ALIR-44
**Generic LIR Does Not Encode CPU Assembly Syntax**

### ALIR-45
**Inline Assembly Is An Explicit Low-Level Boundary**

### ALIR-46
**LIR Verification Precedes Machine Lowering**

### ALIR-47
**SSA Is Preserved Until Register Allocation**

### ALIR-48
**Memory SSA Is Optional Internal Optimization**

### ALIR-49
**LIR Does Not Require A Runtime**

### ALIR-50
**LIR Lowering Must Preserve Verified MIR Semantics**

---

# 49. Pipeline bây giờ

Axiom đã có:

```text
Source
  ↓
AST
  ↓
HIR
  ↓
Typed HIR
  ↓
Trait Resolution
  ↓
MIR
  ↓
Ownership / Capability / Async / Concurrency Verification
  ↓
Verified MIR
  ↓
ABI Classification
  ↓
ABI MIR
  ↓
Axiom LIR
  ↓
LIR Optimization
  ↓
Target Legalization
  ↓
Machine IR
  ↓
Register Allocation
  ↓
Frame Layout
  ↓
Prologue/Epilogue
  ↓
Machine Optimization
  ↓
Machine Encoder
  ↓
Object
  ↓
Linker
```

Có một điều chỉnh nhỏ tôi khuyên nên **đóng băng ngay**:

> **Frame Layout nên xảy ra sau Register Allocation**, nhưng allocator có thể cần một *provisional frame model* để biết outgoing arguments, dynamic stack alignment và reserved slots.

Do đó implementation thực tế:

```text
ABI Lowering
   ↓
LIR
   ↓
PreRA Frame Analysis
   ↓
Register Allocation
   ↓
Final Frame Layout
   ↓
Spill/Reload Resolution
   ↓
Prologue/Epilogue
```

chứ không nên ép thành pipeline tuyến tính tuyệt đối.

---

# 50. Bước tiếp theo: `MACHINE-IR-002 — Register/Memory/Instruction Model`

Đây là bước tiếp theo và cũng là nơi Axiom bắt đầu **thực sự nói chuyện với CPU**.

Ta cần đóng băng:

```text
PhysicalRegister
VirtualRegister
RegisterClass
RegisterAlias
SubRegister
RegisterMask
Flags
MemoryOperand
AddressingMode
Instruction
ImplicitUse
ImplicitDef
Clobber
ConditionCode
Branch
Call
Return
```

Đặc biệt cần thiết kế một `InstructionDescriptor` đủ mạnh để mô tả cả:

```text
x86:
    add rax, rbx
    addss xmm0, xmm1
    cmov
    setcc
    lea
    AVX/AVX2/AVX-512

AArch64:
    add
    madd
    ldr
    stp
    csel
    fadd

RISC-V:
    add
    ld
    sd
    beq
    mul
```

mà **không biến compiler thành một backend hard-code khổng lồ**.

Và đây chính là điểm chúng ta nên thiết kế tiếp theo: **instruction description + register model + addressing model**, trước khi bắt đầu viết instruction selector.