Được. Ta tiếp tục từ **LIR v0.1**, và tôi nghĩ bây giờ nên làm một việc quan trọng hơn việc thêm nhiều opcode: **đóng thiết kế Machine IR + backend đầu tiên**, đồng thời kiểm tra xem kiến trúc hiện tại có thực sự cho phép Axiom tạo native executable mà không cần LLVM hay không.

# AXIOM Machine IR v0.1

Mục tiêu:

> Machine IR là lớp duy nhất được phép biết sâu về CPU cụ thể.

Luồng:

```text
Verified MIR
    ↓
ABI MIR
    ↓
Axiom LIR
    ↓
Target Lowering
    ↓
Machine IR
    ↓
Register Allocation
    ↓
Scheduling
    ↓
Machine Encoding
    ↓
Object Writer
```

Machine IR **không còn target-neutral**.

---

## 1. Machine IR nên có 6 loại đối tượng

```text
MachineModule
MachineFunction
MachineBlock
MachineInstruction
MachineOperand
MachineFrame
```

### MachineModule

```text
MachineModule {
    target
    functions
    globals
    symbols
    relocations
    metadata
}
```

Ví dụ:

```text
target = x86_64-pc-windows-msvc
```

hoặc:

```text
target = x86_64-unknown-linux-gnu
```

---

# 2. MachineFunction

```text
MachineFunction {
    name
    calling_convention
    blocks
    virtual_registers
    physical_register_constraints
    frame
    attributes
}
```

Điểm quan trọng:

**MachineFunction vẫn có thể chứa virtual register.**

Không nên register-allocate ngay khi lowering.

```text
LIR
 ↓
Machine IR
 ↓
optimization
 ↓
register allocation
 ↓
Machine IR final
```

---

# 3. MachineOperand

Đây mới là nơi xuất hiện những thứ CPU-specific.

Ví dụ:

```text
MachineOperand =
    VirtualReg
    PhysicalReg
    Immediate
    Memory
    Label
    Symbol
    StackSlot
    FrameIndex
```

Ví dụ x86:

```text
RAX
RBX
RCX
RDX
XMM0
XMM1
```

ARM:

```text
X0
X1
X2
X3
V0
V1
```

RISC-V:

```text
x0
x1
x2
...
f0
f1
```

---

# 4. MachineInstruction

Ví dụ x86:

```text
MOV
ADD
SUB
IMUL
CMP
JCC
CALL
RET
```

Nhưng:

> Machine instruction **không nhất thiết phải tương ứng 1:1 với instruction thật**.

Có thể có pseudo-instruction:

```text
COPY
PHI
LOAD_ADDRESS
CALL_SYMBOL
RETURN_VALUE
PROLOGUE
EPILOGUE
```

Backend sẽ legalize chúng trước khi encode.

---

# 5. Tôi đề xuất thêm Machine Pseudo Instructions

Điều này sẽ làm backend đơn giản hơn rất nhiều.

Ví dụ:

```text
COPY %v1, %v2
```

Sau register allocation:

```text
COPY RAX, RBX
```

Sau peephole:

```text
; nếu không cần → loại bỏ
```

Tương tự:

```text
LOAD_CONST
LOAD_ADDRESS
CALL
RET
```

không nhất thiết phải ngay lập tức biến thành opcode machine.

---

# 6. Register Class

Đây là thứ LIR không cần biết.

x86-64:

```text
GPR64
GPR32
GPR16
GPR8

XMM
YMM
ZMM

FLAGS
```

ARM64:

```text
GPR64
GPR32
FP32
FP64
SIMD128
```

RISC-V:

```text
GPR
FPR
VECTOR
```

Nhưng có một điểm:

**FLAGS không nên trở thành virtual register bình thường.**

Ví dụ x86:

```text
CMP
JCC
```

có dependency implicit.

Machine IR có thể biểu diễn dependency đó bằng machine-specific operand/constraint.

---

# 7. Register constraints

Ví dụ một số instruction x86 bắt buộc operand phải ở register cụ thể.

Ví dụ division:

```text
RDX:RAX / operand
```

Backend phải mô tả:

```text
IDIV:
    input dividend → RAX/RDX
    divisor → GPR
    quotient → RAX
    remainder → RDX
```

Đây là **Machine IR concern**, không phải LIR.

---

# 8. Frame model

Machine backend cần:

```text
MachineFrame {
    stack_size
    alignment
    local_slots
    spill_slots
    outgoing_arg_area
    saved_registers
    unwind_info
}
```

Ví dụ:

```text
RBP-8
RBP-16
RBP-24
```

hoặc backend có thể omit frame pointer:

```text
RSP+offset
```

Axiom source không biết bất kỳ điều nào trong số này.

---

# 9. Stack frame không phải lúc nào cũng tồn tại

Một hàm:

```axiom
fn add(a: i64, b: i64) -> i64 {
    a + b
}
```

có thể compile thành:

```asm
lea rax, [rdi + rsi]
ret
```

Không stack.

Đây chính là lý do ta không được thiết kế language-level variable = stack slot.

---

# 10. Backend Contract hoàn chỉnh hơn

Ta có thể đóng thành:

```text
ABEC — Axiom Backend Contract
```

Backend phải cung cấp:

```text
TargetDescription
InstructionSet
RegisterFile
CallingConventions
TypeLegalizer
InstructionSelector
RegisterAllocator
FrameLowering
Scheduler
Encoder
ObjectWriter
RelocationModel
UnwindEmitter
DebugEmitter
```

Không nhất thiết tất cả đều là module độc lập trong compiler source, nhưng đây là **conceptual contract**.

---

# 11. TargetDescription

Ví dụ:

```text
TargetDescription {
    arch
    os
    abi
    endian
    pointer_width
    register_sets
    supported_types
    supported_vectors
    atomics
    calling_conventions
    object_format
}
```

x86-64 Linux:

```text
arch = x86_64
os = linux
abi = SystemV
pointer_width = 64
object_format = ELF
```

Windows:

```text
arch = x86_64
os = windows
abi = Win64
object_format = COFF/PE
```

ARM64:

```text
arch = aarch64
...
```

---

# 12. Type legalization

Đây là một tầng cực kỳ quan trọng.

Ví dụ Axiom:

```text
i128
```

nhưng target chỉ có:

```text
i64
```

Backend có thể biến:

```text
i128
```

thành:

```text
{ lo: i64, hi: i64 }
```

Tương tự:

```text
v16i32
```

trên CPU không có vector register phù hợp:

```text
scalar sequence
```

hoặc báo lỗi nếu programmer yêu cầu native-only operation.

---

# 13. Instruction Selection

Ví dụ LIR:

```text
%3 = IADD %1, %2
```

x86:

```asm
add rax, rbx
```

ARM:

```asm
add x0, x1, x2
```

RISC-V:

```asm
add a0, a1, a2
```

Một LIR instruction có thể thành:

```text
1 instruction
```

hoặc:

```text
2–20 instructions
```

Điều đó hoàn toàn bình thường.

---

# 14. Ví dụ quan trọng: checked addition

Axiom:

```axiom
fn add(a: i64, b: i64) -> Result<i64, Overflow> {
    checked_add(a, b)
}
```

LIR:

```text
%r, %overflow = IADD_CHECKED %a, %b
```

x86:

```asm
add rax, rbx
jo overflow
```

ARM64:

```asm
adds x0, x1, x2
b.vs overflow
```

RISC-V có thể cần sequence khác.

Frontend không cần biết.

Đây là bằng chứng kiến trúc LIR đang đúng hướng.

---

# 15. Nhưng có một vấn đề lớn: flags

Chúng ta vừa nói LIR không dùng CPU flags.

Điều đó vẫn đúng.

Nhưng Machine IR **được phép** có flags.

Ví dụ x86 Machine IR:

```text
ADD_FLAGS
BRANCH_OVERFLOW
```

hoặc:

```text
ADD
JCC overflow
```

Machine backend có thể biểu diễn implicit flag dependency.

Đây là nơi target-specific semantics xuất hiện.

---

# 16. Register allocation

Tôi đề xuất pipeline:

```text
Machine IR
    ↓
Machine optimization
    ↓
Liveness analysis
    ↓
Register allocation
    ↓
Spill insertion
    ↓
Register rewrite
    ↓
Peephole
    ↓
Scheduling
```

Ban đầu:

**Linear Scan**.

Không cần ngay graph-coloring cực kỳ phức tạp.

---

# 17. Nhưng Axiom cần một thứ khác: Allocation must understand constraints

Ví dụ:

```text
RAX
```

bị bắt buộc cho một operation.

Linear Scan phải hỗ trợ:

```text
fixed register
preferred register
register class
clobber set
```

Ví dụ:

```text
CALL foo
```

có:

```text
clobber = caller_saved
```

Backend biết điều này.

---

# 18. Calling Convention

Ta nên tách:

```text
Axiom ABI
System ABI
C ABI
```

thành `CallingConvention`.

Ví dụ:

```text
CallingConvention::Axiom
CallingConvention::C
CallingConvention::System
```

Nhưng target backend mới mapping:

```text
x86_64 SysV
```

thành:

```text
RDI
RSI
RDX
RCX
R8
R9
```

và:

```text
x86_64 Win64
```

thành:

```text
RCX
RDX
R8
R9
```

---

# 19. Axiom native ABI

Có một lợi thế rất lớn nếu Axiom không cố giữ native ABI ổn định.

Compiler có thể quyết định:

```text
Vec3 → XMM register
```

ở version này.

Version khác:

```text
Vec3 → GPR pair
```

mà không phá language semantics.

Chỉ:

```text
@abi(C)
@abi(system)
```

mới yêu cầu compatibility contract.

---

# 20. Object Writer

Sau Machine IR:

```text
Machine bytes
+
symbols
+
relocations
+
sections
```

→ Object Writer.

Axiom cần ít nhất:

```text
ELF
COFF
Mach-O
WASM
```

Nhưng **không nên làm cả bốn cùng lúc**.

Tôi sẽ chọn:

```text
Phase 1:
x86-64 + ELF
```

sau đó:

```text
x86-64 + PE/COFF
```

rồi:

```text
ARM64 + ELF
ARM64 + Mach-O
```

---

# 21. Tại sao ELF nên làm trước?

Không phải vì ELF tốt hơn về mặt ngôn ngữ.

Mà vì nó giúp kiểm thử compiler dễ:

```text
Axiom
 ↓
ELF object
 ↓
system linker
 ↓
Linux executable
```

Ta có thể kiểm tra:

```bash
readelf
objdump
```

để debug binary.

Sau đó mới tự viết linker.

---

# 22. Không nên viết linker quá sớm

Đây là điểm tôi muốn thay đổi so với mục tiêu ban đầu của dự án.

Mục tiêu cuối:

> Axiom không phụ thuộc compiler/linker bên thứ ba.

Nhưng **không có nghĩa bootstrap phải tự viết mọi thứ ngay từ đầu**.

Roadmap:

```text
Axiom frontend
    ↓
Axiom MIR
    ↓
Axiom LIR
    ↓
Axiom Machine IR
    ↓
Axiom encoder
    ↓
Axiom object writer
    ↓
system linker
```

Sau khi compiler ổn định:

```text
Axiom object
 ↓
Axiom linker
 ↓
native executable
```

Điều này giảm rất nhiều rủi ro.

---

# 23. Vertical Slice #1

Bây giờ tôi nghĩ chúng ta nên đóng một **Minimum Native Slice**.

Không phải:

> “implement Axiom language”.

Mà:

> “implement đủ Axiom để biến một function cực nhỏ thành native machine code”.

### Input

```axiom
fn add(a: i64, b: i64) -> i64 {
    a + b
}
```

### AST

```text
Function
 ├── name = add
 ├── params = [a:i64, b:i64]
 └── body
      └── return a+b
```

### HIR

```text
CALL? → no
ADD
```

### MIR

```text
bb0:
    %0 = READ a
    %1 = READ b
    %2 = IADD_WRAP %0, %1
    RETURN %2
```

### Verified MIR

```text
OK
```

### ABI MIR

Ví dụ System V:

```text
a → ABI_ARG_0
b → ABI_ARG_1
return → ABI_RETURN
```

### LIR

```text
%2 = IADD %0, %1
RETURN %2
```

### Machine IR

```text
%0 = RDI
%1 = RSI

%2 = ADD %0, %1

RETURN %2
```

### Encoder

```text
48 8D 04 37
C3
```

hoặc một sequence tương đương.

### Object

```text
add.o
```

### Link

```text
add executable
```

---

# 24. Vertical Slice #2: branch

Tiếp theo:

```axiom
fn max(a: i64, b: i64) -> i64 {
    if a > b {
        a
    } else {
        b
    }
}
```

MIR:

```text
bb0:
    %c = CMP_GT a, b
    BR %c, bb1, bb2

bb1:
    RETURN a

bb2:
    RETURN b
```

LIR:

```text
%c = ICMP_GT %a, %b
BR %c, bb1, bb2
```

x86 backend có thể tạo:

```asm
cmp rdi, rsi
cmovg rax, rdi
```

hoặc branch.

**Đó là quyết định backend.**

---

# 25. Vertical Slice #3: loop

```axiom
fn sum(n: i64) -> i64 {
    var i = 0
    var s = 0

    while i < n {
        s = s + i
        i = i + 1
    }

    s
}
```

Nếu pipeline này chạy được:

```text
loop
↓
CFG
↓
SSA
↓
PHI
↓
LIR
↓
Machine IR
```

thì compiler architecture đã chứng minh được rất nhiều thứ.

---

# 26. Vertical Slice #4: ownership

Sau arithmetic, cần ngay:

```axiom
fn consume(x: Buffer) {
    ...
}
```

kiểm tra:

```text
MOVE
DROP
```

Mục tiêu:

```text
Source
 ↓
MIR
 ↓
ownership verifier
 ↓
DROP elaboration
 ↓
LIR
```

và chứng minh rằng ownership không cần xuất hiện trong native instructions nếu không còn observable effect.

Ví dụ:

```text
MOVE x → y
```

có thể biến mất hoàn toàn về machine code.

---

# 27. Đây là một nguyên tắc rất quan trọng

Axiom không nên có:

```text
ownership runtime
borrow runtime
lifetime runtime
```

Ownership là **compile-time semantic property**.

Ví dụ:

```axiom
fn foo(x: Vec<i64>) -> i64 {
    let y = x
    y.len()
}
```

`x → y` có thể chỉ là:

```text
SSA rename
```

Không có:

```text
memcpy
free(x)
retain(y)
```

Đây chính là cách Axiom đạt zero-cost ownership.

---

# 28. Drop mới tạo machine effect

Ví dụ:

```axiom
fn foo() {
    let f = File.open("x")
}
```

MIR:

```text
ALLOC/OPEN
...
DROP f
```

Drop có thể trở thành:

```text
CALL File.close
```

Nếu resource abstraction yêu cầu.

Ngược lại:

```axiom
struct Point {
    x: f64
    y: f64
}
```

không có Drop.

Compiler không cần generate cleanup.

---

# 29. Một kiểm tra rất quan trọng cho kiến trúc hiện tại

Ta có:

```text
ownership
view
region
Send
Share
Drop
```

nhưng **tất cả đều có thể biến mất trước LIR** nếu không tạo observable machine behavior.

Đây là dấu hiệu tốt.

Ví dụ:

```text
view<T>
```

thường chỉ trở thành:

```text
pointer + length
```

và lifetime verification biến mất.

`Send` có thể biến mất.

`Share` có thể biến mất.

`Copy` có thể biến mất.

Ownership move có thể biến mất.

Nhưng:

```text
Mutex
Atomic
File.close
Allocation
```

có thể còn machine effects.

Đó chính là zero-cost abstraction theo nghĩa thực tế.

---

# 30. Một nguyên tắc tôi muốn đóng thành Axiom invariant

## **AZC-01 — Compile-Time Semantic Erasure**

> Semantic mechanisms that have no observable runtime effect shall not require runtime representation.

Ví dụ:

```text
Copy
Move
Send
Share
view lifetime
trait static dispatch
generic type parameter
ownership state
```

không được tự động tạo runtime metadata.

---

## AZC-02 — No Mandatory Semantic Runtime

Không có:

```text
axiom_runtime_object_header
axiom_gc
axiom_refcount
axiom_typeinfo
axiom_borrow_runtime
```

trừ khi abstraction cụ thể yêu cầu.

---

## AZC-03 — Representation Only When Observable

Nếu programmer yêu cầu:

```text
dynamic dispatch
stable address
FFI
reflection
atomic
allocation
```

thì representation tương ứng mới xuất hiện.

---

# 31. Kiến trúc lúc này đã khá hoàn chỉnh

```text
             AXIOM LANGUAGE
                   │
                   ▼
                  AST
                   │
                   ▼
                  HIR
                   │
                   ▼
               Typed HIR
                   │
                   ▼
                  MIR
                   │
       ┌───────────┼───────────┐
       │           │           │
   Ownership    Region      Effects
       │           │           │
       └───────────┼───────────┘
                   ▼
             VERIFIED MIR
                   │
                   ▼
          Semantic Optimizer
                   │
                   ▼
               ABI MIR
                   │
                   ▼
               AXIOM LIR
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
        x86-64    ARM64    RISC-V
          │        │        │
          ▼        ▼        ▼
       Machine IR
          │
          ▼
   Register Allocation
          │
          ▼
 Instruction Selection
          │
          ▼
   Machine Encoding
          │
          ▼
     Object Writer
          │
     ┌────┼─────┐
     ▼    ▼     ▼
    ELF  PE   Mach-O
          │
          ▼
       Linker
          │
          ▼
       Native EXE
```

**Tôi cho rằng từ đây không nên tiếp tục mở rộng danh sách tính năng ngôn ngữ nữa trong một thời gian.** Ta đã có Core, ownership, memory, concurrency, type system, module/package, ABI, MIR, verifier, interpreter, LIR. Nếu cứ thiết kế tiếp `Map`, `GUI`, `async API`, `reflection`, v.v. trước khi native slice chạy được thì rất dễ rơi vào tình trạng “specification rất lớn nhưng compiler chưa chứng minh được kiến trúc”.

Bước kỹ thuật tiếp theo hợp lý nhất là **đặc tả `AXIOM x86-64 Backend v0.1`**, bắt đầu từ **System V AMD64 ABI + ELF object writer + machine encoder**, rồi dùng 4 test bắt buộc:

```text
add()
max()
loop_sum()
checked_add()
```

Sau đó mới đưa ownership/Drop vào native slice.