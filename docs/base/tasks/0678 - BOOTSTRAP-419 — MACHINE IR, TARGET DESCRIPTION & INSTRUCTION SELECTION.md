# BOOTSTRAP-419 — MACHINE IR, TARGET DESCRIPTION & INSTRUCTION SELECTION

**Trạng thái:** SPECIFIED / FROZEN  
**Phụ thuộc:** 418 LIR, 417 ABI, 416 Optimization  
**Mục tiêu:** định nghĩa tầng **Machine IR (MIR-Machine / MIRx)** và cơ chế biến Axiom LIR thành mã máy cụ thể cho x86-64, ARM64, RISC-V, WASM và các target khác.

Đây là bước đầu tiên mà compiler thực sự phải hiểu **CPU/ISA cụ thể**.

---

# 419.1. Ba tầng phải được giữ riêng

Sau 419, kiến trúc compiler có:

```text
Axiom MIR
    │
    │ semantic
    ▼
Axiom LIR
    │
    │ target-independent low level
    ▼
Machine IR
    │
    │ target-specific
    ▼
Machine Code
```

Trong đó:

### MIR

```text
"Điều gì phải xảy ra?"
```

### LIR

```text
"Thao tác machine-independent nào cần thực hiện?"
```

### Machine IR

```text
"ISA cụ thể nào sẽ thực hiện?"
```

---

# 419.2. Machine IR không phải Assembly Text

Machine IR vẫn là compiler IR.

Ví dụ:

```text
%r1 = ADD %r2, %r3
```

thay vì:

```asm
add rax, rbx
```

Machine IR có:

- register;
- instruction;
- operand;
- basic block;
- physical register;
- virtual register;
- register constraints;
- clobbers;
- scheduling information.

---

# 419.3. Target Description

Compiler phải có một **Target Description Model**.

```text
Target
 ├── Architecture
 ├── ISA
 ├── ABI
 ├── OS
 ├── Object Format
 ├── Register File
 ├── Instruction Set
 ├── Calling Convention
 ├── Alignment
 ├── Atomic Capabilities
 ├── SIMD Features
 └── CPU Features
```

Ví dụ:

```text
x86_64-windows-msvc
x86_64-linux-gnu
aarch64-linux
aarch64-ios
riscv64-linux
wasm32
```

---

# 419.4. Target ≠ Architecture

Phải phân biệt:

```text
Architecture:
    x86_64

OS:
    Windows

ABI:
    MSVC

Object:
    PE/COFF
```

với:

```text
x86_64
Linux
SysV ABI
ELF
```

Cùng ISA nhưng ABI/object/runtime khác.

---

# 419.5. Target Triple

Axiom có target identity:

```text
architecture-os-abi
```

và metadata mở rộng:

```text
target {
    arch
    os
    abi
    object_format
    endian
    pointer_width
    cpu
    features
}
```

---

# 419.6. Endianness

Target description phải khai báo:

```text
little
big
```

LIR semantic operations như:

```text
load
store
bitcast
byte extraction
```

được lower theo target endian.

---

# 419.7. Pointer Width

Target có:

```text
32-bit
64-bit
```

hoặc mô hình đặc biệt.

`usize`/`isize` được map theo target pointer width.

Không hard-code:

```text
usize = u64
```

---

# 419.8. Register File

Machine IR mô hình hóa:

```text
RegisterClass
```

Ví dụ x86-64:

```text
GPR
XMM
YMM
ZMM
FLAGS
```

ARM64:

```text
GPR
FP/SIMD
NZCV
```

RISC-V:

```text
GPR
FPR
Vector
```

---

# 419.9. Virtual Register

Instruction selection tạo:

```text
vreg0
vreg1
vreg2
```

chưa biết physical register.

Ví dụ:

```text
v1 = ADD v2, v3
```

Sau register allocation:

```text
RAX = ADD RBX, RCX
```

---

# 419.10. Physical Register

Machine IR có namespace riêng:

```text
$rax
$rbx
$x0
$x1
$a0
$a1
```

Physical register chỉ xuất hiện khi:

- ABI yêu cầu;
- instruction constraint yêu cầu;
- register allocation đã chạy;
- inline assembly yêu cầu.

---

# 419.11. Register Classes

Ví dụ:

```text
INTEGER
FLOAT
VECTOR
MASK
FLAGS
SPECIAL
```

Một operand yêu cầu:

```text
GPR
```

không thể được allocator đặt vào:

```text
XMM
```

nếu instruction không hỗ trợ.

---

# 419.12. Register Aliasing

x86:

```text
RAX
EAX
AX
AL
```

là các view của cùng physical register.

Machine target model phải biểu diễn alias:

```text
RegisterAliasGroup
```

Điều này rất quan trọng cho register allocator.

---

# 419.13. Instruction Definition

Mỗi instruction:

```text
MachineInstruction {
    opcode
    operands
    defs
    uses
    implicit_defs
    implicit_uses
    clobbers
    constraints
}
```

Ví dụ conceptually:

```text
ADD_GPR
    def: dst
    use: lhs
    use: rhs
    def: flags
```

---

# 419.14. Instruction Semantics

Mỗi opcode phải có semantic description.

Ví dụ:

```text
ADD:
    dst = lhs + rhs
    flags = ...
```

Compiler không nên chỉ lưu mnemonic.

Semantic model cần phục vụ:

- verification;
- optimization;
- scheduling;
- emulator/test backend;
- formal validation.

---

# 419.15. Instruction Selection

LIR:

```text
ADD_I32 %a, %b
```

có thể lower thành:

```text
x86:
    ADD32

ARM64:
    ADD32

RISC-V:
    ADD32
```

Instruction selector chọn opcode dựa trên:

```text
type
register class
target features
cost
instruction legality
addressing modes
ABI constraints
```

---

# 419.16. Pattern-Based Selection

Axiom có thể dùng instruction patterns:

```text
LIR pattern:
    ADD(LOAD(a), LOAD(b))
```

match:

```text
target instruction with memory operand
```

Ví dụ target có thể hỗ trợ:

```text
ADD reg, [mem]
```

thì không cần tạo register trung gian cho load.

---

# 419.17. Addressing Mode Folding

Ví dụ LIR:

```text
load(base + index * 4 + offset)
```

x86 có thể lower trực tiếp:

```text
[base + index*4 + offset]
```

ARM/RISC-V có các addressing modes khác.

Do đó addressing mode là target-specific optimization.

---

# 419.18. Addressing Mode Abstraction

Machine IR nên biểu diễn:

```text
AddressOperand {
    base
    index
    scale
    offset
    symbol
}
```

nếu target hỗ trợ.

Backend có thể legalize nếu không hỗ trợ.

---

# 419.19. Instruction Cost Model

Target description có cost:

```text
latency
throughput
size
register_pressure
microarchitecture_hint
```

Không nên chỉ tối ưu theo “ít instruction nhất”.

Ví dụ:

```text
2 instructions
```

có thể nhanh hơn:

```text
1 instruction
```

nếu instruction kia có latency rất lớn.

---

# 419.20. CPU Feature Set

Target có:

```text
baseline features
optional features
```

Ví dụ x86:

```text
SSE2
SSE4.2
AVX
AVX2
AVX512
AES
BMI
FMA
```

ARM:

```text
NEON
SVE
SVE2
AES
CRC
```

---

# 419.21. Feature Detection

Axiom hỗ trợ:

```text
@target_feature(...)
```

ở mức compiler metadata.

Ví dụ:

```text
@target_feature("avx2")
fn process(...) { ... }
```

Compiler phải đảm bảo caller không gọi function này trên CPU không có AVX2, trừ khi dispatch contract cho phép.

---

# 419.22. Multi-Versioning

Compiler có thể tạo:

```text
process_baseline
process_avx2
process_avx512
```

và dispatcher:

```text
CPU feature detection
        ↓
appropriate implementation
```

Đây là library/compiler feature, không bắt programmer viết assembly.

---

# 419.23. CPU Dispatch

Axiom có semantic abstraction:

```text
target_dispatch
```

Compiler có thể generate:

```text
if CPU supports AVX2:
    call avx2
else:
    call baseline
```

Dispatcher phải được verify để không gọi unsupported instructions.

---

# 419.24. Instruction Legalization

Không phải LIR operation nào cũng có instruction trực tiếp.

Ví dụ:

```text
128-bit integer divide
```

target có thể không hỗ trợ.

Legalizer có thể biến:

```text
DIV_I128
```

thành:

```text
runtime helper
```

hoặc:

```text
multi-instruction sequence
```

---

# 419.25. Runtime Helper

Compiler có internal helper:

```text
__axiom_i128_div
```

nếu target thiếu hardware support.

Nhưng helper không phải “mandatory runtime” của mọi program.

Chỉ link nếu cần.

---

# 419.26. Runtime-Free Principle

Nếu chương trình chỉ dùng:

```text
integer
float
memory
syscalls/FFI
```

và target hỗ trợ trực tiếp:

```text
no helper
no runtime
```

Binary không kéo theo runtime lớn.

---

# 419.27. Division Lowering

Ví dụ:

```text
DIV_U64
```

compiler có thể chọn:

```text
native div
```

hoặc:

```text
constant divisor optimization
```

hoặc:

```text
magic multiplication
```

tùy optimizer/target.

---

# 419.28. Constant Division

```text
x / 10
```

có thể được lower thành multiplication/shift nếu semantic integer division cho phép.

Phải bảo toàn:

- signedness;
- rounding;
- overflow/trap semantics.

---

# 419.29. Instruction Fusion

Target backend có thể nhận diện:

```text
MUL
ADD
```

và tạo:

```text
FMA
```

nếu floating-point profile cho phép.

Không được tự ý dùng FMA trong strict FP nếu làm thay đổi observable rounding.

---

# 419.30. Machine Flags

Flags register phải được mô hình hóa.

Ví dụ:

```text
CMP
JE
```

có dependency:

```text
CMP → FLAGS → JE
```

Optimizer không được xóa/ghi đè flags giữa chúng nếu dependency còn tồn tại.

---

# 419.31. Flags Optimization

Compiler có thể chọn instruction:

```text
TEST
```

thay vì:

```text
CMP x, 0
```

nếu semantic tương đương.

Đây là machine-level optimization.

---

# 419.32. Conditional Select

LIR:

```text
select(cond, a, b)
```

target có thể dùng:

```text
CMOV
CSEL
conditional instruction
branch
```

Cost model quyết định.

---

# 419.33. Branch vs Branchless

Không mặc định:

```text
branchless = faster
```

Compiler dùng:

```text
branch probability
latency
vectorization
target microarchitecture
```

để chọn.

---

# 419.34. Branch Probability

Machine IR có:

```text
branch_probability
```

nguồn từ:

- static analysis;
- profile-guided optimization;
- programmer hint nếu sau này cho phép;
- runtime profile.

Không ảnh hưởng semantics.

---

# 419.35. Profile-Guided Optimization

Axiom hỗ trợ PGO:

```text
build instrument
 ↓
run workload
 ↓
collect profile
 ↓
rebuild optimized
```

Profile có thể chứa:

```text
branch frequency
call frequency
hot functions
loop trip counts
cache behavior hints
```

---

# 419.36. Deterministic Build

PGO profile là build input.

Do đó:

```text
profile hash
```

phải trở thành BuildDB dependency.

Hai build với profile khác nhau không được coi là cùng artifact.

---

# 419.37. Instruction Scheduling

Sau selection:

```text
Machine IR
```

scheduler có thể reorder instructions trong basic block.

Nhưng phải giữ:

```text
data dependencies
memory dependencies
atomic ordering
volatile ordering
ABI constraints
```

---

# 419.38. Dependency Graph

Mỗi instruction có:

```text
DataDependency
MemoryDependency
ControlDependency
ResourceDependency
```

Scheduler dùng graph này.

---

# 419.39. Load/Store Scheduling

Load/store có thể reorder nếu:

```text
alias analysis
```

chứng minh không conflict.

Atomic/volatile có restriction mạnh hơn.

---

# 419.40. Register Pressure

Instruction scheduling phải cân bằng:

```text
latency
throughput
register pressure
```

Một schedule ít instruction nhưng làm register spill nhiều có thể chậm hơn.

---

# 419.41. Machine IR Spill Model

Register allocator có thể tạo:

```text
SPILL
RELOAD
```

hoặc trực tiếp:

```text
STORE stackslot
LOAD stackslot
```

Machine IR phải hỗ trợ stack slots.

---

# 419.42. Stack Slot

```text
StackSlot {
    size
    alignment
    lifetime
    type
}
```

Stack slot coloring có thể reuse storage nếu lifetime không overlap.

---

# 419.43. Stack Slot Reuse

Ví dụ:

```text
x sống [BB1..BB3]
y sống [BB4..BB6]
```

có thể dùng cùng stack slot.

Giảm:

```text
stack frame size
```

---

# 419.44. Register Allocation

Axiom không nên khóa allocator vào một thuật toán.

Có thể hỗ trợ:

```text
Linear Scan
Graph Coloring
PBQP-like
Hybrid
```

Profile:

```text
fast compile
balanced
maximum performance
```

---

# 419.45. Default Allocator

Đề xuất:

```text
release:
    hybrid allocator

debug:
    fast linear-scan

size:
    pressure-aware allocator
```

Nhưng đây là compiler strategy, không phải language semantics.

---

# 419.46. Register Allocation Correctness

Allocator phải đảm bảo:

```text
no conflicting live values
physical register class valid
fixed register constraints satisfied
caller/callee-save rules satisfied
spill correctness
```

---

# 419.47. Calling Convention Lowering

Machine IR phải biết:

```text
caller-saved
callee-saved
argument registers
return registers
stack alignment
shadow space
red zone
```

theo ABI.

Ví dụ x86-64 Windows và SysV không được dùng chung assumption.

---

# 419.48. Prologue / Epilogue

Machine lowering tạo:

```text
PROLOGUE
EPILOGUE
```

hoặc expanded instructions:

```text
save registers
allocate stack
restore registers
return
```

Compiler có thể omit frame pointer nếu:

```text
debug/unwind requirements
```

cho phép.

---

# 419.49. Frame Pointer

Default optimized:

```text
omit frame pointer
```

nếu target/unwind/debug cho phép.

Debug/sanitize profile có thể yêu cầu giữ frame pointer.

---

# 419.50. Stack Canary / Security

Security profile có thể thêm:

```text
stack canary
shadow stack
CFI
stack probing
```

nhưng đây là compiler/security profile, không phải mandatory overhead.

---

# 419.51. Stack Probing

Large stack allocation:

```text
STACK_ALLOC huge
```

có thể cần OS-specific probing.

Target backend chịu trách nhiệm.

---

# 419.52. Instruction Encoding

Sau register allocation/scheduling:

```text
Machine IR
 ↓
Machine Encoding
```

encoder tạo bytes.

Ví dụ conceptually:

```text
ADD RAX, RBX
 ↓
opcode bytes
```

Encoder phải:

- deterministic;
- validate operands;
- calculate instruction size;
- emit relocations.

---

# 419.53. No Textual Assembly Required

Axiom compiler cuối cùng **không cần**:

```text
generate .asm
↓
invoke external assembler
```

Thay vào đó:

```text
Machine IR
 ↓
Axiom Encoder
 ↓
Object Writer
```

Điều này rất quan trọng đối với mục tiêu:

> Không phụ thuộc compiler bên thứ ba.

---

# 419.54. Object Writer Boundary

Encoder tạo:

```text
Machine bytes
Relocations
Symbols
Sections
Debug mappings
Unwind metadata
```

Object writer tạo:

```text
ELF
PE/COFF
Mach-O
WASM
```

---

# 419.55. Inline Assembly

Axiom có thể hỗ trợ:

```text
asm(...)
```

nhưng phải là **unsafe/system feature**.

Compiler cần biết:

```text
inputs
outputs
clobbers
memory effects
register constraints
```

Nếu inline asm không khai báo đúng:

```text
unsafe contract violation
```

---

# 419.56. Inline Assembly không phá Optimizer

Asm block phải khai báo:

```text
readonly?
writes_memory?
clobbers?
```

Ví dụ:

```text
asm volatile
```

không được DCE.

---

# 419.57. Machine Intrinsics

Một số operations nên biểu diễn bằng intrinsic:

```text
bit_reverse
population_count
leading_zeros
trailing_zeros
rotate
prefetch
fence
CRC
AES
```

Source API có thể là ordinary Axiom functions/compiler intrinsics.

Compiler chọn instruction.

---

# 419.58. Builtin vs Library

Không nên biến mọi CPU instruction thành keyword.

Ví dụ:

```text
count_ones(x)
```

là library/compiler intrinsic.

Backend quyết định:

```text
POPCNT
software sequence
```

Programmer không cần biết ISA.

---

# 419.59. Target-Specific Intrinsics

Có thể có module:

```text
std::arch::x86
std::arch::arm
std::arch::riscv
```

dành cho code cần kiểm soát ISA.

Nhưng đây là **advanced/system layer**, không phải cách viết code thông thường.

---

# 419.60. Machine IR Example

LIR:

```text
%3 = ADD_I64 %1, %2
```

x86-64 Machine IR:

```text
v0 = COPY arg0
v1 = COPY arg1
v2 = ADD64 v0, v1
RETURN v2
```

Sau allocation:

```text
RAX = ARG0
RDX = ARG1
RAX = ADD64 RAX, RDX
RETURN RAX
```

Encoder:

```text
machine bytes
```

---

# 419.61. ARM64 Example

Cùng LIR:

```text
%3 = ADD_I64 %1, %2
```

Machine IR:

```text
x0 = ARG0
x1 = ARG1
x0 = ADD x0, x1
RETURN x0
```

Không cần thay đổi semantic compiler.

---

# 419.62. RISC-V Example

```text
a0 = ARG0
a1 = ARG1
a0 = ADD a0, a1
RETURN a0
```

Đây là lý do LIR rất quan trọng.

---

# 419.63. WASM

WASM không phải CPU register machine.

Do đó Machine IR backend có thể dùng:

```text
virtual stack slots
locals
WASM values
```

Target model phải cho phép backend architecture khác biệt mà không phá frontend.

---

# 419.64. Machine Backend Interface

Axiom backend interface:

```text
TargetBackend {
    legalize()
    select_instructions()
    lower_abi()
    allocate_registers()
    schedule()
    emit_code()
    emit_relocations()
}
```

Các backend không cần chung implementation nội bộ.

---

# 419.65. Target Description DSL

Để compiler tự host dễ hơn, target metadata nên có schema declarative:

```text
target {
    registers { ... }
    instructions { ... }
    classes { ... }
    calling_conventions { ... }
    features { ... }
}
```

Compiler có thể generate một phần backend machinery.

---

# 419.66. Không nên hard-code ISA khắp compiler

Sai:

```text
if x86 ...
if arm ...
if riscv ...
```

rải khắp codebase.

Đúng:

```text
generic compiler
    ↓
TargetModel
    ↓
TargetBackend
```

Điều này cực kỳ quan trọng khi Axiom tự host.

---

# 419.67. CompilerDB

Thêm:

```text
MachineDB
TargetDB
TargetFeatureDB
RegisterDB
RegisterClassDB
InstructionDB
InstructionPatternDB
InstructionCostDB
InstructionSelectionDB
AddressingModeDB
MachineCFGDB
MachineMemoryDB
MachineCallDB
MachineSchedulingDB
RegisterAllocationDB
SpillDB
StackFrameDB
MachineDebugDB
MachineEncodingDB
```

---

# 419.68. Proof Artifacts

```text
InstructionSelectionProof
TargetLegalityProof
RegisterClassProof
AddressingModeProof
CallingConventionMachineProof
RegisterAllocationProof
SpillCorrectnessProof
StackFrameProof
InstructionSchedulingProof
MachineEncodingProof
TargetFeatureProof
MachineVerificationProof
```

---

# 419.69. Invariants `AMACH`

```text id="d1k7x4"
AMACH-01  Every Machine IR instruction belongs to the selected target ISA.
AMACH-02  Every operand matches the instruction operand class.
AMACH-03  Register classes are respected.
AMACH-04  Physical register aliases are modeled correctly.
AMACH-05  Fixed-register constraints are respected.
AMACH-06  ABI argument locations are preserved.
AMACH-07  ABI return locations are preserved.
AMACH-08  Caller/callee-save rules are preserved.
AMACH-09  Stack alignment requirements are preserved.
AMACH-10  Stack slots have valid size and alignment.
AMACH-11  Register allocation has no overlapping physical assignments.
AMACH-12  Spill/reload preserves value semantics.
AMACH-13  Instruction scheduling preserves dependencies.
AMACH-14  Memory dependencies are preserved.
AMACH-15  Atomic ordering is preserved.
AMACH-16  Volatile ordering is preserved.
AMACH-17  Branch targets are valid.
AMACH-18  Unreachable blocks cannot become reachable accidentally.
AMACH-19  Unsupported instructions are never emitted.
AMACH-20  Target feature requirements are satisfied.
AMACH-21  Multi-version dispatch never executes unsupported code.
AMACH-22  Inline assembly constraints are respected.
AMACH-23  Instruction encoding matches Machine IR.
AMACH-24  Relocations correspond to valid symbolic references.
AMACH-25  Prologue/epilogue preserve ABI requirements.
AMACH-26  Security instrumentation preserves program semantics.
AMACH-27  Debug mappings remain valid where possible.
AMACH-28  Identical Machine IR + target state produces deterministic encoding.
AMACH-29  Encoded machine code is validated before object emission.
AMACH-30  Machine lowering cannot introduce semantic behavior absent from verified LIR.
```

---

# 419.70. Kiến trúc backend sau 419

Axiom lúc này có pipeline hoàn chỉnh từ semantic đến machine:

```text
                 Axiom Source
                       │
                       ▼
                    HIR/MIR
                       │
                       ▼
                 Verified MIR
                       │
                       ▼
               Semantic Optimize
                       │
                       ▼
                   ABI MIR
                       │
                       ▼
                  Axiom LIR
                       │
             ┌─────────┼─────────┐
             │         │         │
             ▼         ▼         ▼
          x86-64     ARM64     RISC-V
             │         │         │
             └─────────┼─────────┘
                       ▼
                  Machine IR
                       │
              ┌────────┴────────┐
              ▼                 ▼
       Register Allocation   Scheduling
              │                 │
              └────────┬────────┘
                       ▼
                Machine Encoding
                       │
                       ▼
                 Object Writer
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
            ELF       PE       Mach-O
```

Điểm quan trọng nhất của 419:

> **Từ đây Axiom không còn phụ thuộc vào “compiler backend của người khác” về mặt kiến trúc.**

LLVM/Clang có thể vẫn được dùng trong **bootstrap implementation** nếu cần, nhưng thiết kế cuối cùng đã có đường đi:

```text
Axiom source
→ Axiom MIR
→ Axiom LIR
→ Axiom Machine IR
→ Axiom encoder
→ Axiom object
→ Axiom linker
```

Đây là nền tảng thực tế để đạt mục tiêu **self-hosting + native compiler + không cần assembler/compiler bên thứ ba trong bản hoàn chỉnh**.

**BOOTSTRAP-419 — SPECIFIED / FROZEN.**