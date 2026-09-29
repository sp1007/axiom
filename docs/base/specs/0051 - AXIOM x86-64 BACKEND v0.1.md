Tiếp tục. Bây giờ tôi muốn đi xuống **x86-64 backend v0.1** ở mức đủ cụ thể để AI agent có thể bắt tay code, nhưng vẫn giữ kiến trúc mở cho ARM64/RISC-V sau này.

# AXIOM x86-64 BACKEND v0.1

Mục tiêu của backend đầu tiên:

```text
Axiom source
    ↓
AST
    ↓
HIR
    ↓
MIR
    ↓
Verified MIR
    ↓
ABI MIR
    ↓
LIR
    ↓
x86-64 Machine IR
    ↓
Machine Code
    ↓
ELF object
    ↓
Linux executable
```

**Chưa cần tự viết linker ở phase này.**

Dùng system linker trong bootstrap là hoàn toàn chấp nhận được.

---

# 1. Target đầu tiên

Chốt target:

```text
x86_64
OS: Linux
Object: ELF64
ABI: System V AMD64
Endian: little
Pointer: 64-bit
```

Target descriptor:

```text
Target {
    arch: x86_64
    os: linux
    abi: sysv_amd64
    object: elf64
    endian: little
    pointer_width: 64
}
```

Sau khi backend này ổn:

```text
x86_64-linux
        │
        ├── x86_64-windows
        ├── x86_64-macos
        ├── aarch64-linux
        ├── aarch64-macos
        └── riscv64-linux
```

sẽ tái sử dụng phần lớn frontend/MIR/LIR.

---

# 2. Không encode assembly text

Đừng đi theo kiến trúc:

```text
LIR
 ↓
"mov rax, rdi"
 ↓
assembler
```

Nếu mục tiêu cuối cùng là compiler độc lập, cách này tạo dependency không cần thiết.

Nên:

```text
LIR
 ↓
Machine IR
 ↓
Machine Encoder
 ↓
raw machine bytes
```

Ví dụ:

```text
48 01 F8
C3
```

sau đó ghi thẳng vào `.text`.

Assembler chỉ có thể là **bootstrap/debug tool**, không phải dependency semantic.

---

# 3. x86-64 Register File

Backend định nghĩa register classes.

### GPR

```text
RAX
RBX
RCX
RDX
RSI
RDI
RBP
RSP
R8
R9
R10
R11
R12
R13
R14
R15
```

### SIMD

```text
XMM0 ... XMM15
YMM0 ... YMM15
```

v0.1 có thể chỉ cần:

```text
GPR64
GPR32
XMM
```

Các width khác được thêm khi cần.

---

# 4. Physical register metadata

Mỗi register nên có metadata:

```text
PhysicalRegister {
    id
    name
    class
    width
    aliases
    caller_saved
    callee_saved
    reserved
}
```

Ví dụ:

```text
RAX:
    class = GPR
    caller_saved = true
    callee_saved = false
```

```text
RBX:
    class = GPR
    caller_saved = false
    callee_saved = true
```

```text
RSP:
    reserved = true
```

Compiler không được register-allocate `RSP` như GPR thông thường.

---

# 5. System V AMD64 calling convention

Integer/pointer arguments:

```text
1 → RDI
2 → RSI
3 → RDX
4 → RCX
5 → R8
6 → R9
```

Return:

```text
RAX
```

Floating-point:

```text
XMM0
XMM1
...
```

được dùng theo ABI classification.

---

# 6. ABI classification không nên nằm trong frontend

Ví dụ:

```axiom
fn foo(x: Vec3) -> Vec3
```

Frontend chỉ biết:

```text
Vec3
```

ABI classifier quyết định:

```text
Vec3
 ↓
3 × f32
 ↓
XMM registers?
memory?
```

Không để HIR/MIR biết RDI/XMM0.

---

# 7. ABI classification pipeline

Đề xuất:

```text
Type
 ↓
Logical ABI Shape
 ↓
ABI Classification
 ↓
Argument Location
 ↓
Machine Operand
```

Ví dụ:

```text
i64
 ↓
INTEGER
 ↓
GPR
 ↓
RDI
```

`f64`:

```text
f64
 ↓
SSE
 ↓
XMM
 ↓
XMM0
```

Struct:

```text
struct Pair {
    a: i64
    b: i64
}
```

có thể:

```text
INTEGER + INTEGER
```

→ hai GPR.

---

# 8. Return value

Không nên giả định:

```text
return → RAX
```

cho mọi type.

Ví dụ:

```text
i64 → RAX
f64 → XMM0
Pair<i64,i64> → RAX,RDX
large struct → hidden sret pointer
```

Đây chính là lý do cần ABI MIR.

---

# 9. Hidden return pointer

Ví dụ:

```axiom
fn make_big() -> BigStruct
```

ABI có thể biến thành conceptually:

```text
fn make_big(out: *mut BigStruct) -> void
```

Nhưng đây **không phải source-level transformation**.

ABI MIR biểu diễn:

```text
return_mode = Indirect
hidden_arg = sret
```

Machine backend mới đưa hidden argument vào register ABI phù hợp.

---

# 10. Stack alignment

System V AMD64 yêu cầu stack alignment phù hợp tại call boundary.

Backend phải có:

```text
FrameLayout {
    local_size
    spill_size
    outgoing_args
    saved_regs
    alignment
}
```

Không hardcode:

```text
sub rsp, 32
```

cho mọi hàm.

Frame layout phải được tính toán.

---

# 11. Leaf function optimization

Ví dụ:

```axiom
fn add(a: i64, b: i64) -> i64 {
    a + b
}
```

Machine IR:

```text
ADD RAX, RDI, RSI
RETURN RAX
```

Không cần:

```text
push rbp
mov rbp, rsp
...
pop rbp
```

Không cần stack frame.

---

# 12. Prologue/Epilogue chỉ khi cần

Một function có thể cần frame nếu:

- spill register
- local stack storage
- outgoing stack arguments
- callee-saved registers
- dynamic stack requirements
- unwind/debug requirements

Nếu không cần:

```text
prologue = none
epilogue = none
```

Đây là một optimization rất cơ bản nhưng quan trọng.

---

# 13. Register allocation example

LIR:

```text
%0 = ARG 0
%1 = ARG 1
%2 = IADD %0, %1
RETURN %2
```

ABI lowering:

```text
%0 → RDI
%1 → RSI
```

Machine IR:

```text
%v2 = ADD RDI, RSI
RETURN %v2
```

Register allocator có thể chọn:

```text
%v2 → RAX
```

Machine:

```asm
mov rax, rdi
add rax, rsi
ret
```

Hoặc backend nhận ra:

```text
lea rax, [rdi+rsi]
ret
```

Đây là peephole/target optimization.

---

# 14. Đừng ép backend phải tạo assembly đẹp

Mục tiêu backend:

> **correct machine code trước, optimal machine code sau.**

Ban đầu:

```text
mov rax, rdi
add rax, rsi
ret
```

hoàn toàn chấp nhận được.

Sau đó optimizer có thể biến thành:

```text
lea rax, [rdi+rsi]
ret
```

Không nên làm instruction selection quá thông minh ngay từ ngày đầu.

---

# 15. Machine instruction encoding

Backend cần một encoder dạng:

```text
encode(instruction) -> bytes
```

Ví dụ:

```text
MOV rax, rdi
```

→

```text
48 89 F8
```

```text
ADD rax, rsi
```

→

```text
48 01 F0
```

```text
RET
```

→

```text
C3
```

Encoder không cần biết AST/MIR/ownership.

Nó chỉ cần biết:

```text
MachineInstruction
```

---

# 16. Encoder nên chia thành các lớp

Đừng viết một hàm khổng lồ:

```text
encode_instruction(...)
```

Nên:

```text
x86/
├── registers
├── instruction
├── operand
├── encoding
│   ├── rex
│   ├── modrm
│   ├── sib
│   ├── immediate
│   └── displacement
└── encoder
```

---

# 17. REX

x86-64 encoding cần REX prefix trong nhiều trường hợp.

Conceptually:

```text
REX.W
REX.R
REX.X
REX.B
```

Encoder nên có abstraction:

```text
RexPrefix {
    w
    r
    x
    b
}
```

Không để từng opcode tự xử lý bit thủ công một cách hỗn loạn.

---

# 18. ModRM

Đây sẽ là một trong những primitive quan trọng nhất:

```text
ModRM {
    mod
    reg
    rm
}
```

Ví dụ:

```text
ADD rax, rbx
```

sẽ được encode thông qua:

```text
REX
opcode
ModRM
```

---

# 19. SIB

Memory operand:

```text
[base + index*scale + displacement]
```

cần:

```text
SIB {
    scale
    index
    base
}
```

Đây là lý do trước đó tôi nói:

> LIR không cần mô hình hóa x86 addressing mode; Machine IR có thể làm điều đó.

---

# 20. ELF Object Writer

Sau encoder:

```text
Machine code
```

cần ELF sections.

Tối thiểu:

```text
.text
.rodata
.data
.bss
.symtab
.strtab
.shstrtab
.rela.text
```

v0.1 có thể giảm tối đa:

```text
.text
.symtab
.strtab
.shstrtab
.rela.text
```

nếu chương trình cực nhỏ.

---

# 21. Symbol

Axiom function:

```axiom
fn add(...)
```

được biểu diễn:

```text
Symbol {
    name
    section
    offset
    size
    binding
    visibility
    type
}
```

Ví dụ:

```text
add:
    section = .text
    binding = LOCAL/GLOBAL
    type = FUNC
```

---

# 22. Relocation

Đây là phần không thể bỏ nếu có external function.

Ví dụ:

```axiom
extern fn puts(...)
```

Machine code chưa biết địa chỉ `puts`.

Object chứa:

```text
CALL ????
```

và relocation:

```text
R_X86_64_PLT32
```

hoặc loại phù hợp.

Do đó:

```text
Machine Encoder
```

không nên tự resolve mọi symbol.

Nó tạo:

```text
bytes + relocation records
```

Object writer ghi chúng vào ELF.

---

# 23. Internal vs external symbol

Axiom:

```axiom
fn foo() {}
fn bar() {
    foo()
}
```

Nếu compiler có thể resolve:

```text
foo
```

vẫn có thể tạo relocation nội bộ hoặc resolve sau layout.

Không nên hardcode address ngay trong instruction generation.

---

# 24. ELF writer không phải linker

Đây là ranh giới cần giữ.

```text
Compiler
 ↓
ELF object
```

sau đó:

```text
system linker
 ↓
executable
```

Compiler không cần biết toàn bộ executable layout ở phase này.

---

# 25. Test cực kỳ quan trọng

Mỗi layer phải test độc lập.

## Test encoder

```text
MOV RAX, RDI
→ expected bytes
```

```text
ADD RAX, RSI
→ expected bytes
```

```text
RET
→ C3
```

Đây là **golden encoding tests**.

---

# 26. Test ABI

Ví dụ:

```axiom
fn add(a: i64, b: i64) -> i64
```

Expected:

```text
a → RDI
b → RSI
return → RAX
```

Test không cần chạy executable.

---

# 27. Test LIR → Machine IR

Input:

```text
%2 = IADD %0, %1
```

Expected properties:

```text
operation = ADD
operand0 = allocated integer register
operand1 = allocated integer register
result = integer register
```

Không cần snapshot toàn bộ Machine IR quá cứng.

Ta đã thống nhất trước đó:

> Test semantic properties tốt hơn full IR snapshot.

---

# 28. Differential testing

Đây mới là vũ khí mạnh nhất.

Ví dụ:

```text
fn add(a: i64, b: i64) -> i64
```

chạy:

```text
MIR Interpreter
```

→

```text
42
```

Native executable:

```text
42
```

So sánh.

Pipeline:

```text
              ┌→ Semantic Oracle
Source → MIR ─┤
              └→ Native Backend
                   ↓
               Executable
                   ↓
               Result
```

Nếu:

```text
Oracle != Native
```

backend/compiler có bug.

---

# 29. Test property thay vì chỉ test examples

Ví dụ random:

```text
a,b ∈ i64
```

hàng nghìn cặp.

So sánh:

```text
interpreter(add(a,b))
native(add(a,b))
```

Đặc biệt:

```text
0
1
-1
MAX
MIN
MAX-1
MIN+1
```

và overflow.

Đây sẽ trở thành nền tảng cho **Axiom Compiler Fuzzing Harness** sau này.

---

# 30. Checked arithmetic phải test riêng

Ví dụ:

```text
MAX + 1
```

không được:

```text
wrap
```

nếu semantics là checked.

Oracle:

```text
Overflow
```

Native:

```text
Overflow
```

Hai kết quả phải giống.

---

# 31. Một vấn đề quan trọng: executable entry point

Function:

```axiom
fn main() {}
```

không nhất thiết là ELF entry point.

Bootstrap có thể sinh startup shim:

```text
_process_start
    ↓
axiom_main
    ↓
exit
```

Ban đầu thậm chí có thể để C runtime gọi:

```text
axiom_main
```

Nhưng về sau:

```text
Axiom startup object
```

sẽ đảm nhận việc này.

---

# 32. Freestanding sau này

Khi đã có:

```text
ELF object writer
```

ta có thể hướng đến:

```text
@entry
fn _start() -> !
```

và tạo:

```text
ELF executable
```

không cần libc.

Đây mới là milestone chứng minh:

> **Axiom thực sự có khả năng tự tạo native program mà không cần C compiler/runtime.**

---

# 33. Roadmap native compiler tôi đề xuất

### Phase N0 — Encoder

```text
x86-64 registers
REX
ModRM
SIB
immediates
displacements
RET
MOV
ADD
SUB
CMP
JMP
Jcc
CALL
```

### Phase N1 — Machine IR

```text
virtual regs
physical regs
blocks
instructions
frame
```

### Phase N2 — ABI

```text
System V AMD64
integer args
float args
returns
stack args
struct args
```

### Phase N3 — Register allocation

```text
liveness
linear scan
spill
reload
```

### Phase N4 — ELF

```text
.text
symbols
relocations
sections
ELF64
```

### Phase N5 — Vertical slice

```text
add
max
loop
call
```

### Phase N6 — Semantic integration

```text
Drop
Result
Option
ownership
views
closures
```

---

# 34. Sau đó mới làm ARM64

Điểm hay của kiến trúc hiện tại là ARM64 backend **không cần biết ownership**.

Nó chỉ nhận:

```text
LIR
```

và thực hiện:

```text
LIR
 ↓
ARM64 lowering
 ↓
ARM64 Machine IR
 ↓
ARM64 encoder
 ↓
Mach-O/ELF
```

Frontend giữ nguyên.

---

# 35. Và đây là lúc ta có thể kiểm chứng một trong những tham vọng lớn nhất của Axiom

Không phải:

> “Axiom có syntax đẹp.”

Mà là:

```text
Một chương trình Axiom có thể đi từ source
đến machine code native
mà không cần LLVM.
```

Sau đó:

```text
Axiom compiler
```

được viết bằng chính:

```text
Axiom
```

và compile chính nó.

Khi đó vòng lặp trở thành:

```text
Bootstrap compiler
       │
       ▼
Axiom compiler written in Axiom
       │
       ▼
Axiom compiler builds itself
       │
       ▼
Self-hosting
```

---

## Một quyết định nữa tôi nghĩ nên đóng ngay

**Đừng xây x86 backend thành một khối duy nhất.**

Hãy chia architecture:

```text
compiler/
├── backend/
│   ├── target/
│   │   ├── x86_64/
│   │   │   ├── target
│   │   │   ├── registers
│   │   │   ├── abi
│   │   │   ├── legalize
│   │   │   ├── selector
│   │   │   ├── regalloc
│   │   │   ├── frame
│   │   │   ├── encoder
│   │   │   └── elf
│   │   │
│   │   ├── aarch64/
│   │   ├── riscv64/
│   │   └── wasm/
│   │
│   ├── lir/
│   ├── machine_ir/
│   └── object/
```

`elf` cũng nên tách khỏi x86:

```text
backend/object/
├── elf/
├── coff/
├── macho/
└── wasm/
```

Vì ARM64 Linux cũng dùng ELF.

Như vậy sau này:

```text
x86_64 + ELF
ARM64 + ELF
RISC-V + ELF
```

sẽ chia sẻ object writer.

**Bước kế tiếp hợp lý nhất là đi vào `AXIOM x86-64 Instruction Selection v0.1`** — cụ thể hóa cách từng LIR operation (`IADD`, `ICMP`, `LOAD`, `STORE`, `BR`, `CALL`, `RETURN`, `MEMCPY`...) được legalize và chọn instruction, bao gồm cả register constraints và spill. Đây là điểm mà kiến trúc compiler bắt đầu chuyển từ “spec” thành một compiler có thể thực sự sinh byte máy.