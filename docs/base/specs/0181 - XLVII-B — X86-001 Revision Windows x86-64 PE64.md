Đúng. Với mục tiêu **tự xây compiler và tự kiểm thử trên laptop Windows**, backend đầu tiên nên là **x86-64 Windows PE64/COFF**, không phải Linux ELF.

Ta vẫn giữ Linux ELF trong kiến trúc, nhưng đổi thứ tự triển khai:

```text
MVP backend priority

1. x86-64 Windows PE64 / COFF   ← máy phát triển
2. x86-64 Linux ELF
3. AArch64
4. RISC-V64
...
```

Điểm quan trọng: **Machine IR và instruction encoder dùng chung**. Chỉ `Target + ABI + ObjectFormat + Linker` thay đổi.

---

# XLVII-B — X86-001 Revision: Windows x86-64 PE64

Kiến trúc tổng thể:

```text
                    ┌── Windows x86-64
                    │     ├── MS ABI
                    │     ├── COFF
                    │     └── PE64
                    │
LIR → x86 Machine IR ┤
                    │
                    └── Linux x86-64
                          ├── SysV ABI
                          ├── ELF64
                          └── Linux startup
```

Như vậy chúng ta **không fork backend x86**.

---

# 1. Target đầu tiên

```text
Target {
    architecture: X86_64
    abi: WindowsX64
    object_format: PECOFF
    os: Windows
    environment: MSVC-compatible
}
```

Target triple nội bộ:

```text
x86_64-windows-ms
```

Tên cụ thể có thể thay đổi, nhưng semantic identity phải ổn định.

---

# 2. Windows x64 ABI

Đây là khác biệt quan trọng nhất so với System V.

Integer/pointer arguments:

```text
RCX
RDX
R8
R9
```

Floating-point arguments:

```text
XMM0
XMM1
XMM2
XMM3
```

Return:

```text
RAX
XMM0
```

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Windows ABI có thể trở thành:

```text
RCX = a
RDX = b
RAX = result
```

---

# 3. Shadow space / home space

Windows x64 yêu cầu caller dành:

```text
32 bytes
```

cho 4 register argument slots.

Do đó một call:

```text
call foo
```

không chỉ đơn giản là:

```text
CALL foo
```

Stack frame phải bảo đảm vùng shadow/home space.

Đây là một lý do rất tốt để ABI lowering nằm riêng khỏi semantic compiler.

---

# 4. Stack model

Frame:

```text
FrameLayout {
    locals
    spills
    saved_registers
    outgoing_args
    shadow_space
    alignment_padding
}
```

Windows:

```text
shadow_space = 32 bytes
```

và ABI pass tính toán alignment.

Không cho instruction selector tự ý cộng/trừ `RSP`.

---

# 5. Caller-saved Windows x64

Các GPR volatile:

```text
RAX
RCX
RDX
R8
R9
R10
R11
```

Các XMM:

```text
XMM0
XMM1
XMM2
XMM3
XMM4
XMM5
```

được xem là volatile.

---

# 6. Callee-saved Windows x64

GPR:

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

XMM:

```text
XMM6 ... XMM15
```

Đây là điểm khác đáng kể với System V.

Backend phải để ABI description quyết định, không hard-code vào allocator.

---

# 7. Register model phải sửa một điểm

Register class:

```text
GPR64
GPR32
GPR16
GPR8
XMM
FLAGS
```

nhưng mỗi ABI có:

```text
RegisterConvention {
    argument_registers
    return_registers
    caller_saved
    callee_saved
    reserved
    fixed_registers
}
```

Ví dụ:

```text
WindowsX64Convention
SysV64Convention
```

---

# 8. Machine IR vẫn giữ nguyên

Ví dụ:

```text
Machine IR

%v0 = ADD32 %a, %b
RETURN %v0
```

Không nên biến thành:

```text
RCX
RDX
RAX
```

quá sớm.

ABI lowering mới làm:

```text
Windows:
    a → ECX
    b → EDX
    result → EAX

Linux:
    a → EDI
    b → ESI
    result → EAX
```

Đây là kiến trúc đúng.

---

# 9. Windows PE/COFF

Thay vì:

```text
ELF64
```

ta có:

```text
PE32+ / PE64
    ↓
COFF object
```

Tên PE chính thức thường được gọi là PE32+ cho executable 64-bit.

Axiom có:

```text
ObjectFormat
    ├── COFF
    └── ELF
```

và:

```text
ExecutableFormat
    ├── PE64
    └── ELF64
```

---

# 10. Object pipeline Windows

```text
Machine IR
    ↓
x86 Encoder
    ↓
COFF Object
    ↓
Axiom PE Linker
    ↓
PE32+ EXE
```

Không:

```text
Axiom
 ↓
MASM
 ↓
LINK.EXE
```

vì mục tiêu cuối cùng của Axiom là **không phụ thuộc toolchain bên ngoài**.

Trong giai đoạn bootstrap có thể dùng linker hệ thống nếu cần, nhưng production compiler cuối cùng phải tự làm được.

---

# 11. COFF object

MVP cần:

```text
COFF Header
Section Table
.text
.rdata
.data
.bss
.relocation
Symbol Table
String Table
```

MVP đầu tiên thậm chí có thể tối giản:

```text
.text
.data
.rdata
.reloc
symbols
```

---

# 12. Section

Axiom abstraction:

```text
Section {
    name
    kind
    flags
    alignment
    data
    relocations
}
```

Windows mapping:

```text
.text   → executable + readable
.rdata  → readable
.data   → readable + writable
.bss    → readable + writable
```

PE linker sau này chuyển chúng thành PE sections.

---

# 13. Relocation

Không nên để encoder biết PE relocation.

Encoder chỉ tạo:

```text
Relocation {
    offset
    kind
    symbol
    addend
}
```

COFF writer chuyển thành relocation type phù hợp.

Ví dụ x86-64:

```text
REL32
ADDR64
ADDR32
```

MVP tập trung vào relocation cần cho:

```text
CALL
JMP
global address
data references
```

---

# 14. Symbol

```text
Symbol {
    name
    binding
    visibility
    section
    offset
    size
    kind
}
```

Ví dụ:

```text
main
_start
foo
global_value
```

---

# 15. Windows entry point

Không nên mặc định:

```text
main = PE entry point
```

như một abstraction chung.

Axiom nên có:

```text
@entry
fn main()
```

Compiler tạo startup layer:

```text
PE Entry
    ↓
Axiom startup
    ↓
main()
    ↓
ExitProcess / process termination
```

Nhưng freestanding cũng phải tồn tại:

```text
@entry
unsafe fn _start()
```

nếu người dùng muốn tự kiểm soát startup.

---

# 16. Không bắt buộc CRT

Đây là một mục tiêu rất quan trọng của Axiom.

Một chương trình:

```axiom
@entry
fn main() -> i32 {
    42
}
```

không nên bắt buộc:

```text
MSVCRT
ucrt
C runtime
```

chỉ để chạy.

Compiler/linker có thể tạo executable tối giản sử dụng Windows process termination API hoặc startup mechanism phù hợp.

---

# 17. Hai profile Windows

Nên có:

### Hosted

```text
axiom build
```

có:

```text
std
Windows API wrappers
filesystem
threads
network
etc.
```

### Freestanding

```text
axiom build --profile freestanding
```

có thể:

```text
core
intrinsics
PE loader contract
```

và không cần runtime.

---

# 18. Windows API

Windows API không thuộc Core.

Ví dụ:

```axiom
import os.windows
```

sẽ là library/system layer.

FFI:

```axiom
extern "system" fn ...
```

ABI `"system"` trên Windows x64 có thể map tới Windows x64 calling convention.

---

# 19. `extern "system"`

Đây là abstraction tốt:

```axiom
extern "system" fn MessageBoxW(...)
```

không cần programmer biết register ABI.

Compiler target quyết định:

```text
Windows → Windows ABI
Linux   → platform equivalent
```

Nếu ABI `"system"` có ý nghĩa target-specific.

Còn:

```axiom
extern "C"
```

là C ABI cụ thể.

---

# 20. Windows unwind/debug

Không đưa vào MVP executable đầu tiên.

Ban đầu:

```text
panic = abort
```

để backend đơn giản.

Sau đó mới thêm:

```text
Windows unwind metadata
PData
XData
SEH
```

và Linux:

```text
.eh_frame
DWARF
```

Điều này không ảnh hưởng semantic Drop vì semantic cleanup đã được xử lý trước Machine IR.

---

# 21. Debug information

Tách:

```text
Machine IR
```

khỏi:

```text
DebugInfo
```

Windows có thể sau này phát:

```text
CodeView/PDB
```

Linux:

```text
DWARF
```

Không để debug format xâm nhập compiler core.

---

# 22. Encoder architecture

Bây giờ tới phần thực sự quan trọng.

```text
MachineInstr
      ↓
X86 Encoder
      ↓
EncodedBytes + Relocations
```

Không dùng assembler.

---

# 23. X86 instruction encoding

Pipeline:

```text
Instruction
 ↓
Encoding Form
 ↓
Prefixes
 ↓
REX
 ↓
Opcode
 ↓
ModRM
 ↓
SIB
 ↓
Displacement
 ↓
Immediate
```

---

# 24. REX

64-bit register encoding cần:

```text
REX.W
REX.R
REX.X
REX.B
```

Representation:

```text
RexPrefix {
    w
    r
    x
    b
}
```

Ví dụ:

```text
REX.W
```

để instruction thao tác operand 64-bit.

---

# 25. ModRM

Representation:

```text
ModRM {
    mod
    reg
    rm
}
```

Ba trường:

```text
mod
reg
r/m
```

Ví dụ:

```text
MOV RAX, RBX
```

encoder tự sinh ModRM.

---

# 26. SIB

Representation:

```text
SIB {
    scale
    index
    base
}
```

Scale:

```text
1
2
4
8
```

Ví dụ:

```text
[RAX + RCX*4 + 16]
```

sẽ được lowering thành:

```text
ModRM + SIB + disp8
```

nếu displacement phù hợp.

---

# 27. Displacement selection

Encoder phải tự chọn:

```text
disp8
disp32
```

không phải Machine IR quyết định.

Ví dụ:

```text
[rax + 4]
```

→ disp8.

```text
[rax + 100000]
```

→ disp32.

---

# 28. Immediate selection

Tương tự:

```text
imm8
imm16
imm32
imm64
```

Encoding legal nhỏ nhất được chọn khi semantics cho phép.

---

# 29. Không optimize semantics trong encoder

Encoder **không được** quyết định:

```text
ADD → LEA
```

hay:

```text
MOV → XOR
```

Đó là instruction selection / machine optimization.

Encoder chỉ làm:

```text
MachineInstr
→ bytes
```

Điều này giữ architecture cực sạch.

---

# 30. Encoder API

```text
encode_function(
    MachineFunction,
    Target
) -> EncodedFunction
```

kết quả:

```text
EncodedFunction {
    bytes
    relocations
    symbol_offsets
    debug_locations
}
```

---

# 31. Encoder verifier

Trước khi encode:

```text
MachineVerifier
```

Sau khi encode:

```text
EncodingVerifier
```

kiểm:

```text
opcode legal
operand form legal
register encoding valid
ModRM valid
SIB valid
immediate width valid
REX valid
```

---

# 32. Đặc biệt: round-trip decoder

Để tự kiểm tra encoder, nên xây **decoder tối giản**.

Không cần decoder đầy đủ x86.

MVP:

```text
Axiom MachineInstr
        ↓ encode
bytes
        ↓ decode
MachineInstr'
```

và kiểm:

```text
semantic_equivalent(MachineInstr, MachineInstr')
```

Đây là một Oracle backend cực mạnh.

---

# 33. Encoder tests

Ví dụ:

```text
MOV EAX, 42
```

expect:

```text
B8 2A 00 00 00
```

```text
RET
```

expect:

```text
C3
```

```text
CALL foo
```

expect:

```text
E8 xx xx xx xx
```

với relocation thích hợp.

---

# 34. Register Allocation → Encoder

Pipeline hoàn chỉnh hiện tại:

```text
Verified MIR
    ↓
Optimizer
    ↓
LIR
    ↓
Instruction Selection
    ↓
Machine IR virtual registers
    ↓
ABI Lowering
    ↓
Register Allocation
    ↓
Frame Layout
    ↓
Spill/Reload
    ↓
Machine IR physical registers
    ↓
x86 Encoder
    ↓
COFF
```

---

# 35. Frame layout

Sau register allocation mới biết:

```text
spill count
saved registers
local stack objects
outgoing calls
```

nên:

```text
Register Allocation
        ↓
Frame Layout
        ↓
Prologue/Epilogue
```

là hợp lý.

Không nên tạo frame cố định từ AST/HIR.

---

# 36. Prologue Windows

Ví dụ function cần RBX:

```text
push rbx
sub rsp, frame_size
...
add rsp, frame_size
pop rbx
ret
```

Nhưng compiler phải có quyền chọn:

```text
push/pop
```

hoặc:

```text
mov [rsp+...], rbx
```

tùy frame layout/optimization.

---

# 37. Leaf optimization

Function:

```axiom
fn square(x: i64) -> i64 {
    x * x
}
```

có thể:

```text
IMUL RCX, RCX
MOV RAX, RCX
RET
```

không frame.

Nếu không cần callee-saved register và không có stack locals.

---

# 38. Windows executable vertical slice #1

Mục tiêu đầu tiên:

```axiom
@entry
fn main() -> i32 {
    42
}
```

Compiler phải tạo:

```text
main
```

Machine code:

```text
MOV EAX, 42
...
```

Startup:

```text
entry
    ↓
main
    ↓
exit(42)
```

Link thành:

```text
hello.exe
```

Chạy:

```powershell
.\hello.exe
$LASTEXITCODE
```

kết quả:

```text
42
```

Đây nên là **backend acceptance test số 1**.

---

# 39. Vertical slice #2

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}

@entry
fn main() -> i32 {
    add(20, 22)
}
```

Expected semantics:

```text
ECX = 20
EDX = 22
CALL add
EAX = 42
```

Đây đồng thời test:

```text
ABI
CALL
RETURN
register allocation
relocation
linker
entry
```

---

# 40. Vertical slice #3

Local variables:

```axiom
@entry
fn main() -> i32 {
    let a = 10
    let b = 20
    let c = a + b
    c + 12
}
```

Expected:

```text
42
```

Test:

```text
CONST
MOVE
ADD
register reuse
```

---

# 41. Vertical slice #4 — branch

```axiom
@entry
fn main() -> i32 {
    let x = 10

    if x > 5 {
        42
    } else {
        0
    }
}
```

Test:

```text
CMP
JG
basic blocks
FLAGS
control-flow
```

---

# 42. Vertical slice #5 — spill

Cố tình tạo nhiều live values:

```text
v0
v1
v2
...
vN
```

để ép:

```text
spill
reload
stack slots
frame
```

Acceptance test phải kiểm cả:

```text
-O0
-O1
```

---

# 43. Linux không bị bỏ

Sau khi Windows backend chạy:

```text
compiler/backend/x86_64/
```

chứa toàn bộ:

```text
registers
instruction selection
encoder
machine IR
frame
allocator
```

Còn:

```text
compiler/target/windows_x64/
compiler/target/linux_x64/
```

chứa:

```text
ABI
object format
linker
startup
debug format
platform features
```

Do đó thêm Linux tương đối nhẹ.

---

# 44. Kiến trúc repository được chỉnh lại

```text
compiler/
├── backend/
│   └── x86_64/
│       ├── machine_ir.ax
│       ├── registers.ax
│       ├── instructions.ax
│       ├── operands.ax
│       ├── flags.ax
│       ├── selector.ax
│       ├── regalloc/
│       ├── frame/
│       ├── encoder/
│       └── verifier/
│
├── targets/
│   ├── windows_x64/
│   │   ├── target.ax
│   │   ├── abi.ax
│   │   ├── coff.ax
│   │   ├── pe.ax
│   │   ├── linker.ax
│   │   └── startup.ax
│   │
│   └── linux_x64/
│       ├── target.ax
│       ├── abi.ax
│       ├── elf.ax
│       ├── linker.ax
│       └── startup.ax
```

Đây là thay đổi kiến trúc tôi khuyến nghị giữ lâu dài.

---

# 45. Invariant mới

```text
AX86TARGET-20
x86 instruction semantics are independent of operating-system ABI.

AX86TARGET-21
ABI classification is target-specific.

AX86TARGET-22
Object format is target-specific.

AX86TARGET-23
Register allocation is architecture-specific but ABI-aware.

AX86TARGET-24
The same x86 Machine IR may target Windows and Linux.

AX86TARGET-25
Windows x64 uses the Windows x64 calling convention.

AX86TARGET-26
Windows argument registers are RCX, RDX, R8, R9.

AX86TARGET-27
Windows requires caller-provided shadow/home space.

AX86TARGET-28
Windows callee-saved XMM registers are preserved when used.

AX86TARGET-29
PE/COFF emission does not require an assembler.

AX86TARGET-30
PE linking does not require the Microsoft linker in the final toolchain.

AX86TARGET-31
CRT dependency is optional, not intrinsic to Axiom.

AX86TARGET-32
Hosted and freestanding startup are distinct profiles.

AX86TARGET-33
Encoder does not perform semantic optimization.

AX86TARGET-34
Relocations survive encoding until object emission.

AX86TARGET-35
Machine code generation is deterministic.

AX86TARGET-36
Windows is the first x86-64 development target.

AX86TARGET-37
Linux x86-64 remains a first-class secondary target.
```

---

# 46. Thứ tự implementation mới

Từ đây chuỗi implementation nên là:

```text
XLVII  X86 Target + Machine IR        ✓
XLVIII Register Allocation
XLIX   Frame Layout + Prologue
L      x86 Instruction Selection
LI     x86 Encoder
LII    COFF Object Writer
LIII   PE64 Linker
LIV    Windows Startup / Entry
LV     First Native .EXE
LVI    Linux ELF Backend
LVII   Cross-target Backend Tests
```

Sau `LV`, Axiom đã có một cột mốc rất quan trọng:

```text
Axiom source
   ↓
Axiom compiler
   ↓
x86 machine code
   ↓
COFF
   ↓
PE64
   ↓
.EXE
```

**không assembler, không LLVM, không GCC, không MSVC linker trong đường cuối cùng.**

Và đây cũng là điểm tôi sẽ giữ làm nguyên tắc cho toàn bộ backend: **Windows không phải một “backend riêng”; x86 là backend, Windows là target/ABI/object/linker layer.** Điều này sẽ giúp Axiom sau này thêm Linux, macOS, Android và các kiến trúc khác mà không làm compiler core phình to.