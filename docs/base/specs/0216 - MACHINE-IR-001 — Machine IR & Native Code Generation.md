Tiếp tục với **MACHINE-IR-001**. Đây là lớp cuối trước khi Axiom thực sự phát ra byte machine code.

Mục tiêu của tầng này:

> **LIR mô tả “muốn làm gì”; Machine IR mô tả “CPU cụ thể có thể làm việc đó như thế nào”.**

---

# MACHINE-IR-001 — Machine IR & Native Code Generation

## 1. Kiến trúc tổng thể

Sau các quyết định trước:

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
Verified MIR
  ↓
ABI Lowering
  ↓
Axiom LIR
  ↓
LIR Optimization
  ↓
Target Legalization
  ↓
Machine IR
  ↓
Instruction Selection
  ↓
Register Allocation
  ↓
Spill / Reload
  ↓
Instruction Scheduling
  ↓
Peephole / Machine Optimization
  ↓
Machine Encoder
  ↓
Object
  ↓
Axiom Linker
  ↓
Executable
```

Có một điểm cần chỉnh so với cách gọi ở bước trước:

**Instruction Selection và Target Legalization nên là quá trình chuyển LIR → Machine IR**, không nhất thiết là hai IR hoàn toàn tách biệt.

---

# 2. Machine IR là gì?

Ví dụ LIR:

```text
%r = add i64 %a, %b
```

Machine IR trên x86-64 có thể trở thành:

```text
%v0 = ADD64 %vA, %vB
```

Sau register allocation:

```text
ADD64 RAX, RBX
```

Sau encoder:

```text
48 01 D8
```

Trên AArch64 cùng LIR:

```text
ADD X0, X1, X2
```

Do đó:

```text
LIR:
    add i64

Machine IR x86:
    ADD64

Machine IR ARM:
    ADDX
```

---

# 3. Machine IR phải target-specific

Không giống LIR, Machine IR biết:

```text
physical registers
register classes
instruction constraints
instruction encoding
calling convention
stack frame
ISA features
instruction latency
instruction throughput
```

Ví dụ x86:

```text
RAX
RBX
RCX
RDX
XMM0
XMM1
...
```

AArch64:

```text
X0
X1
...
X30
V0
...
```

---

# 4. Không hard-code x86 vào compiler core

Kiến trúc:

```text
MachineIR
 ├── TargetX86_64
 ├── TargetAArch64
 ├── TargetRISCV64
 └── TargetWASM
```

Mỗi target cung cấp:

```text
TargetDescription
RegisterFile
InstructionSet
CallingConvention
Legalizer
Encoder
FrameLowering
AsmPrinter
```

---

# 5. Target Description

Đề xuất:

```text
TargetDescription {
    architecture
    pointer_width
    endian
    registers
    register_classes
    instructions
    calling_conventions
    stack_rules
    alignment_rules
    features
}
```

Ví dụ:

```text
x86_64
    registers: 16 GPR + 16 XMM
    pointer: 64
    endian: little
```

---

# 6. Register Class

Machine IR không nên coi mọi register giống nhau.

Ví dụ:

```text
GPR64
GPR32
XMM128
XMM256
XMM512
FLAGS
```

AArch64:

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

Instruction sẽ yêu cầu register class.

---

# 7. Virtual Register

Trước allocation:

```text
%v0
%v1
%v2
```

là virtual registers.

Ví dụ:

```text
%v0:GPR64 = ADD64 %v1, %v2
```

Register allocator sau đó quyết định:

```text
%v0 → RAX
%v1 → RBX
%v2 → RCX
```

---

# 8. Physical Register

Sau allocation:

```text
RAX = ADD64 RBX, RCX
```

Từ thời điểm này:

> Không còn virtual register trong Final Machine IR.

---

# 9. Register aliases

x86 có:

```text
RAX
EAX
AX
AL
AH
```

Đây phải là **cùng một physical register family với các sub-register**.

Ví dụ:

```text
RAX
 ├── EAX
 ├── AX
 ├── AL
 └── AH
```

Machine backend phải biết:

```text
write EAX
```

có ảnh hưởng đến:

```text
RAX
```

Điều này rất quan trọng cho register allocator.

---

# 10. Register units

Đề xuất internal representation:

```text
PhysicalRegister
RegisterUnit[]
```

Ví dụ:

```text
RAX
→ units {RAX_low32, RAX_low16, RAX_low8, ...}
```

Instruction:

```text
write EAX
```

đánh dấu các register units liên quan là defined/clobbered.

---

# 11. Flags / condition codes

Không nên giả lập FLAGS như integer register thông thường.

x86:

```text
CMP
JZ
JL
```

có implicit dependency.

Machine IR:

```text
CMP64 RAX, RBX
JCC_EQ label
```

có metadata:

```text
defines_flags
uses_flags
```

AArch64 cũng có condition flags nhưng cơ chế khác.

Do đó:

> Condition-code semantics thuộc target backend.

---

# 12. Instruction descriptor

Mỗi instruction nên có machine description:

```text
InstructionDef {
    opcode
    operands
    input_constraints
    output_constraints
    implicit_inputs
    implicit_outputs
    clobbers
    encoding
    latency
    throughput
    size
}
```

Ví dụ conceptually:

```text
ADD64:
    input: GPR64
    input: GPR64
    output: GPR64
    flags: write
```

---

# 13. Instruction selection

Ví dụ:

```text
LIR:
%r = add i64 %a, %b
```

Target x86 có thể chọn:

```text
ADD64 %a, %b
```

Nhưng nếu:

```text
%r = add i64 %a, 1
```

có thể chọn:

```text
INC64
```

hoặc:

```text
ADD64 imm8
```

Compiler quyết định dựa trên:

```text
code size
latency
throughput
flags
CPU feature
register pressure
```

---

# 14. Không nhất thiết chọn instruction “ngắn nhất”

Ví dụ:

```text
INC
ADD 1
```

có thể khác về flags.

Axiom phải bảo toàn semantics.

Optimizer **không được** đổi:

```text
ADD
```

thành:

```text
INC
```

nếu observable flags semantics khác nhau.

Nếu flags không được dùng, đổi là hợp lệ.

---

# 15. Instruction legalization

Một LIR operation có thể không tồn tại trên target.

Ví dụ:

```text
i128 add
```

trên target không có native 128-bit integer instruction.

Legalizer biến thành:

```text
low64
high64
carry
```

Ví dụ:

```text
ADD128
→
ADD64 low
ADC64 high
```

---

# 16. Legalization categories

Mỗi target có thể khai báo:

```text
Legal
Expand
Promote
Split
Lower
Custom
Reject
```

Ví dụ:

```text
i128 add:
    x86-64 → Expand

f16 arithmetic:
    target A → Lower/Expand
```

---

# 17. Multi-result instruction

Một số machine instruction có nhiều kết quả.

Ví dụ:

```text
ADC
```

có:

```text
result
carry
```

Machine IR cần hỗ trợ:

```text
%sum, %carry = ADC64 %a, %b, %carry_in
```

Không nên ép mọi thứ thành một result.

---

# 18. Memory addressing

x86 có:

```text
base + index * scale + displacement
```

Machine IR nên biểu diễn address:

```text
MemOperand {
    base
    index
    scale
    displacement
    segment
    size
}
```

Ví dụ:

```text
MOV64 RAX, [RBX + RCX*8 + 16]
```

LIR:

```text
load %ptr
```

Machine selector có thể fold:

```text
gep
+
load
```

thành một memory operand.

---

# 19. Address computation optimization

LIR:

```text
%p = add %base, %offset
%v = load %p
```

x86 Machine IR:

```text
LOAD RAX, [RBX + RCX*4]
```

không cần:

```text
LEA tmp, ...
LOAD ...
```

nếu addressing mode hỗ trợ.

Đây là một trong các lý do không nên hạ LIR trực tiếp thành assembly quá sớm.

---

# 20. Stack frame

Machine backend tạo:

```text
MachineFrame {
    local_slots
    spill_slots
    outgoing_args
    saved_registers
    stack_alignment
    stack_size
}
```

Ví dụ:

```text
push rbp
sub rsp, 64
...
add rsp, 64
pop rbp
ret
```

Nhưng frame pointer không nhất thiết phải tồn tại.

---

# 21. Frame pointer elimination

Nếu target cho phép:

```text
-fomit-frame-pointer
```

không nên là source-level concept.

Machine backend tự quyết định:

```text
frame pointer needed?
```

Debug/unwind requirements có thể buộc giữ frame pointer hoặc dùng alternative unwind metadata.

---

# 22. Red zone

Một số ABI có red zone.

Machine target description:

```text
red_zone_size = N
```

Backend có thể dùng.

Nhưng nếu:

```text
interrupt
kernel
special ABI
```

không cho phép, target profile tắt nó.

---

# 23. Calling convention lowering

Ví dụ:

```axiom
fn add(a: i64, b: i64) -> i64
```

LIR:

```text
call @add(%a, %b)
```

Calling convention x86-64 SysV:

```text
%a → RDI
%b → RSI
return → RAX
```

Windows x64:

```text
%a → RCX
%b → RDX
return → RAX
```

AArch64:

```text
%a → X0
%b → X1
return → X0
```

Đây là **Machine IR lowering**, không phải source semantic.

---

# 24. ABI location

Đề xuất internal type:

```text
ABIOperandLocation {
    Register
    Stack
    Indirect
    Split
    Extend
    Coerce
}
```

Ví dụ:

```text
Vec3
→ XMM0 + XMM1
```

hoặc:

```text
LargeStruct
→ indirect via result pointer
```

---

# 25. Register allocation

Đây là phần cực kỳ quan trọng.

Input:

```text
%v0
%v1
%v2
...
```

Output:

```text
RAX
RBX
RCX
...
```

Axiom không nên khóa chỉ một allocator.

Có thể có:

```text
LinearScan
Greedy
GraphColoring
PBQP
```

---

# 26. MVP allocator

Để compiler tự bootstrap nhanh:

> **Linear Scan** là allocator đầu tiên.

Ưu điểm:

```text
đơn giản
nhanh
dễ debug
dễ self-host
```

Sau đó:

```text
Greedy allocator
```

cho performance production.

Không nên bắt đầu bằng graph-coloring phức tạp.

---

# 27. Live interval

Ví dụ:

```text
1: %a
2: %b
3: %c = add %a, %b
4: use %c
```

Live ranges:

```text
a: [1,3]
b: [2,3]
c: [3,4]
```

Allocator có thể reuse register khi lifetime kết thúc.

---

# 28. Spill

Nếu thiếu register:

```text
%v7
```

được spill:

```text
store %v7 → stack_slot
```

và reload:

```text
load stack_slot → %v7
```

Machine pass có thể tối ưu:

```text
spill
reload
```

để giảm memory traffic.

---

# 29. Register pressure

Optimizer nên biết register pressure.

Ví dụ vectorization tạo:

```text
20 live vectors
```

trong khi target chỉ có:

```text
16 vector registers
```

có thể khiến spill nặng.

Do đó vectorizer không chỉ tối ưu FLOPs.

Nó phải cân nhắc:

```text
register pressure
```

---

# 30. Caller / callee saved

Calling convention định nghĩa:

```text
CallerSaved
CalleeSaved
```

Ví dụ function sử dụng:

```text
RBX
```

nếu RBX callee-saved:

```text
save RBX
...
restore RBX
```

Machine frame manager tự chèn.

---

# 31. Prologue / epilogue insertion

Đây là machine pass:

```text
PrologueEpilogueInserter
```

Input:

```text
function body
```

Output:

```text
save registers
setup stack
body
restore registers
return
```

---

# 32. Shrink wrapping

Về sau có thể tối ưu:

```text
save callee-saved registers
```

chỉ trên các CFG path cần chúng.

Không cần cho MVP.

---

# 33. Instruction scheduling

Sau register allocation hoặc trước allocation tùy target:

```text
scheduler
```

cân nhắc:

```text
latency
throughput
dependencies
register pressure
memory dependencies
branch
```

Ví dụ:

```text
load
independent arithmetic
independent arithmetic
use load
```

có thể che latency.

---

# 34. CPU model

Compiler target nên phân biệt:

```text
architecture
CPU baseline
CPU features
optimization level
```

Ví dụ:

```text
x86_64
    baseline: SSE2
    features: AVX2, FMA
```

hoặc:

```text
-march=native
```

tương đương target feature detection.

---

# 35. Feature sets

Machine IR instruction có requirement:

```text
requires AVX2
requires BMI2
requires FMA
```

Nếu target không có:

```text
legalizer
```

phải reject hoặc lower.

Không bao giờ emit instruction unsupported rồi hy vọng CPU chạy.

---

# 36. CPU dispatch

Về sau có thể:

```axiom
@target_feature("avx2")
fn foo(...)
```

và:

```axiom
@multiversion
fn foo(...)
```

Compiler tạo:

```text
foo_baseline
foo_avx2
foo_avx512
dispatcher
```

Nhưng đây là library/compiler optimization layer, không cần Core v1.

---

# 37. Branch optimization

Machine pass:

```text
branch folding
block layout
fallthrough optimization
jump threading
```

Ví dụ:

```text
jmp L1
L1:
```

→ bỏ `jmp`.

---

# 38. Branch inversion

Có thể biến:

```text
if condition
    jump cold
else
    hot
```

thành:

```text
if !condition
    fallthrough hot
jump cold
```

để giảm branch.

---

# 39. Branch probability

LIR có thể có profile:

```text
branch_probability
```

Nguồn:

```text
static heuristic
PGO
user profile
```

Nhưng profile không thay đổi semantics.

---

# 40. PGO

Axiom nên thiết kế sẵn:

```text
ProfileData
```

cho:

```text
hot/cold
branch probability
call frequency
value profile
```

Compiler sau này có thể:

```text
axiom build --profile
axiom build --use-profile profile.axp
```

Không cần làm ngay trong MVP.

---

# 41. Peephole optimizer

Sau allocation:

```text
MOV RAX, RBX
MOV RBX, RAX
```

hoặc:

```text
ADD RAX, 0
```

có thể loại bỏ.

Machine peephole nhìn trực tiếp instruction sequence.

---

# 42. Machine-level constant folding

Ví dụ:

```text
MOV RAX, 5
ADD RAX, 3
```

→

```text
MOV RAX, 8
```

Nhưng LIR optimizer thường đã làm trước.

Machine optimizer chủ yếu xử lý:

```text
encoding-specific
register-specific
instruction-specific
```

cases.

---

# 43. Instruction encoding

Sau tất cả:

```text
Machine IR
```

→

```text
Machine Encoder
```

Ví dụ x86:

```text
MOV RAX, RBX
```

→ bytes.

Encoder phải xử lý:

```text
opcode
REX
ModRM
SIB
displacement
immediate
VEX
EVEX
```

AArch64:

```text
32-bit instruction encoding
```

RISC-V:

```text
16/32-bit compressed/normal instructions
```

---

# 44. Encoder không được gọi assembler

Đây là một quyết định quan trọng.

Không:

```text
Axiom
 ↓
assembly text
 ↓
GAS/NASM/MASM
 ↓
object
```

ở final architecture.

Phải:

```text
Axiom
 ↓
Machine IR
 ↓
Encoder
 ↓
raw object bytes
```

Điều này đạt mục tiêu:

> **Axiom tự tạo native object mà không phụ thuộc assembler.**

---

# 45. Object writer

Encoder sinh:

```text
.text bytes
.data bytes
.rodata bytes
.bss
symbols
relocations
debug info
unwind info
```

ObjectWriter đóng gói thành:

```text
ELF
COFF
Mach-O
WASM
```

---

# 46. Relocation

Ví dụ:

```text
call external_function
```

Machine encoder chưa biết address cuối cùng.

Nó tạo:

```text
relocation {
    offset
    type
    symbol
    addend
}
```

Linker xử lý sau.

---

# 47. Symbol table

Object:

```text
symbols:
    main
    foo
    bar
```

mỗi symbol:

```text
name
section
offset
size
binding
visibility
type
```

---

# 48. Linker architecture

Sau Machine backend:

```text
Object
  ↓
Axiom Linker
```

Linker cần:

```text
ObjectReader
SymbolResolver
SectionMerger
RelocationEngine
LayoutEngine
ImportExport
TLS
Unwind
Debug
ExecutableWriter
```

Đây sẽ là task riêng sau Machine IR.

---

# 49. Runtime dependency

Một function:

```axiom
fn main() {
    return
}
```

không nên tự động kéo vào:

```text
GC
thread runtime
async runtime
reflection
allocator
```

Binary dependency phải **capability-driven**.

Ví dụ:

```text
main
 ↓
println
 ↓
stdout
```

thì mới link stdout subsystem.

---

# 50. Freestanding

Axiom phải có:

```bash
axiomc --profile=freestanding
```

với:

```text
no OS runtime
no allocator
no thread runtime
no panic runtime
no std
```

Program có thể:

```text
entry point
↓
hardware
```

trực tiếp.

Điều này rất quan trọng cho:

```text
kernel
bootloader
embedded
firmware
OS components
```

---

# 51. Hosted

Profile bình thường:

```text
hosted
```

có thể cung cấp:

```text
OS
filesystem
threads
allocator
network
unicode
async
```

nhưng vẫn là library/runtime components.

---

# 52. GPU Machine IR

GPU không nên cố nhét hoàn toàn vào CPU Machine IR.

Kiến trúc:

```text
LIR
 ├── CPU Machine IR
 └── GPU Machine IR
```

Ví dụ:

```text
@kernel fn add(...)
```

→ GPU-specific backend.

Có thể target:

```text
SPIR-V
CUDA/PTX
Metal
Vulkan
DirectX
```

sau này.

Nhưng semantic LIR chung vẫn cho phép:

```text
load/store
atomic
vector
barrier
```

với execution domain rõ ràng.

---

# 53. WASM

WASM cũng là một target đặc biệt.

Không cần giả lập:

```text
physical register
```

vì WASM là stack machine.

Kiến trúc:

```text
LIR
 ↓
WASM lowering
 ↓
WASM binary encoder
```

có thể bypass phần lớn CPU register allocator.

Do đó Machine IR nên cho phép target backend chọn pipeline phù hợp.

---

# 54. Backend interface

Đề xuất:

```text
Backend {
    target()
    legalize(LIR)
    select_instructions(LIR)
    lower_abi()
    allocate_registers()
    lower_frame()
    schedule()
    optimize()
    encode()
    emit_object()
}
```

Nhưng API thực tế nên chia nhỏ để compiler test từng phase.

---

# 55. Backend correctness

Mỗi phase phải có verifier:

```text
LIRVerifier
MachineIRVerifier
RegisterAllocationVerifier
ObjectVerifier
```

Ví dụ MachineIRVerifier:

```text
mọi register hợp lệ
mọi operand đúng class
mọi physical register conflict hợp lệ
mọi instruction feature supported
mọi stack offset hợp lệ
mọi calling convention constraint đúng
```

---

# 56. Differential testing

Đây là thứ tôi đặc biệt khuyến nghị cho Axiom.

Trong giai đoạn bootstrap:

```text
Axiom backend
       │
       ├── own backend
       │
       └── LLVM/reference backend
```

Compile cùng source:

```text
Axiom → Own Backend
Axiom → LLVM
```

rồi so sánh:

```text
return values
stdout
memory behavior
ABI
```

LLVM chỉ là **oracle/bootstrap**, không phải dependency cuối cùng.

---

# 57. Machine-code tests

Không chỉ test source output.

Cần test trực tiếp:

```text
LIR → Machine IR
Machine IR → bytes
bytes → execution
```

Ví dụ:

```text
test:
    add i64
expected x86:
    specific encoding
```

và:

```text
execute
assert result
```

Điều này giúp encoder không bị regression.

---

# 58. Golden tests

Repository:

```text
tests/
    lexer/
    parser/
    hir/
    mir/
    lir/
    machine/
    encoder/
    object/
    linker/
    runtime/
```

Ví dụ:

```text
tests/machine/x86/add_i64.axmir
```

và:

```text
tests/encoder/x86/add_i64.expected
```

---

# 59. Fuzzing

Compiler cần fuzz:

```text
parser
type checker
MIR verifier
LIR verifier
instruction selector
encoder
object writer
linker
```

Đặc biệt:

> **Machine encoder phải fuzz cực mạnh.**

Vì một byte sai có thể tạo binary hợp lệ về hình thức nhưng crash lúc chạy.

---

# 60. Bootstrap strategy

Đây là roadmap thực tế:

### Stage 0

```text
Axiom frontend
    ↓
LLVM
```

### Stage 1

```text
Axiom frontend
    ↓
Axiom MIR
    ↓
Axiom LIR
    ↓
LLVM backend
```

### Stage 2

```text
Axiom frontend
    ↓
Axiom LIR
    ↓
x86-64 Machine IR
    ↓
Own encoder
    ↓
Own object writer
```

### Stage 3

```text
Own x86-64 linker
```

### Stage 4

```text
Axiom compiler
compiled by Axiom
```

### Stage 5

```text
Self-hosted Axiom compiler
```

---

# 61. Backend MVP nên chọn gì?

Để giảm rủi ro:

```text
Target #1 = x86-64 Linux
Target #2 = x86-64 Windows
Target #3 = AArch64 Linux/macOS
Target #4 = WASM32
Target #5 = RISC-V64
```

Không nên làm đồng thời tất cả.

x86-64 Linux là target tốt để kiểm chứng toàn bộ:

```text
Machine IR
register allocation
ELF
relocation
linking
syscall
```

---

# 62. Machine IR invariants

Chốt:

### AMIR-20
**Machine IR Is Target Specific**

### AMIR-21
**Physical Registers Are Explicit**

### AMIR-22
**Virtual Registers Exist Before Allocation**

### AMIR-23
**Register Classes Constrain Allocation**

### AMIR-24
**Register Aliases Are Explicitly Modeled**

### AMIR-25
**Instruction Constraints Are Target Contracts**

### AMIR-26
**Implicit Register Inputs/Outputs Are Explicitly Modeled**

### AMIR-27
**Condition Codes Are Target Resources**

### AMIR-28
**Instruction Selection Must Preserve LIR Semantics**

### AMIR-29
**Illegal Operations Must Be Expanded Or Rejected**

### AMIR-30
**ABI Locations Are Explicit After ABI Lowering**

### AMIR-31
**Stack Frames Are Backend Constructs**

### AMIR-32
**Spill Slots Are Backend Constructs**

### AMIR-33
**Register Allocation Cannot Change Semantics**

### AMIR-34
**Callee-Saved Registers Must Be Preserved**

### AMIR-35
**Caller-Saved Registers May Be Clobbered**

### AMIR-36
**Unsupported CPU Features Must Never Be Emitted**

### AMIR-37
**Instruction Encoding Is Independent From Instruction Selection**

### AMIR-38
**Relocations Are Preserved Until Linking**

### AMIR-39
**Machine IR Can Be Verified Independently**

### AMIR-40
**Final Machine IR Contains No Virtual Registers**

### AMIR-41
**Final Machine IR Contains Only Legal Target Instructions**

### AMIR-42
**Machine Encoder Does Not Require An External Assembler**

### AMIR-43
**Object Generation Does Not Require A Foreign Compiler**

### AMIR-44
**Backend Optimization Must Preserve ABI Contracts**

### AMIR-45
**CPU Backend And GPU Backend May Use Different Machine Pipelines**

### AMIR-46
**WASM May Bypass CPU Register Allocation**

### AMIR-47
**Target Features Are Explicit**

### AMIR-48
**Debug/Unwind Information Must Survive Machine Lowering**

### AMIR-49
**Machine Code Generation Is Deterministic**

### AMIR-50
**Axiom Can Eventually Generate Native Machine Code Without LLVM**

---

# 63. Một quyết định rất quan trọng cho mục tiêu “nhanh hơn C/C++”

Đừng đặt mục tiêu:

> “Axiom luôn phát ra instruction ít hơn C++.”

Điều đó không thể đảm bảo.

Mục tiêu kiến trúc nên là:

> **Axiom không áp đặt những abstraction runtime bắt buộc khiến optimizer mất cơ hội tạo machine code tốt.**

Ví dụ:

```axiom
fn sum(a: view<i32>) -> i32
```

sau toàn bộ pipeline có thể trở thành một loop SIMD:

```text
load vector
add vector
load vector
add vector
...
```

mà không còn:

```text
view object
ownership object
trait object
bounds object
```

nào trong binary.

Đó mới là lợi thế thực tế của thiết kế Axiom.

---

# 64. Bây giờ kiến trúc đã chạm đến native binary

Sau **ABI-001 + LIR-001 + MACHINE-IR-001**, phần compiler backend còn một mảnh cực lớn:

## **OBJECT/LINK-001 — Object Format & Native Linker**

Nó sẽ quyết định Axiom có thực sự đạt được mục tiêu:

```text
Axiom source
   ↓
own compiler
   ↓
own machine encoder
   ↓
own ELF/PE/Mach-O writer
   ↓
own linker
   ↓
.exe / ELF / Mach-O
```

không cần:

```text
LLVM
GCC
Clang
MSVC
NASM
GAS
ld
lld
```

ở trạng thái cuối.

Đây là bước tiếp theo hợp lý nhất, và cũng là nơi phải thiết kế **ELF/PE/COFF/Mach-O, relocations, symbol resolution, imports/exports, DLL/SO/DYLIB, TLS, startup object, entry point, static linking, dynamic linking và cuối cùng là executable layout**.