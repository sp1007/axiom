# BOOTSTRAP-259 — AXIOM MACHINE IR, REGISTER MODEL, INSTRUCTION SELECTION & TARGET LOWERING

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là tầng backend cốt lõi nối ABI với machine code:

```text
Verified MIR
    ↓
Semantic Optimization
    ↓
ABI MIR
    ↓
Axiom LIR
    ↓
Machine IR
    ↓
Instruction Selection
    ↓
Register Allocation
    ↓
Prologue / Epilogue
    ↓
Machine Encoding
    ↓
Object
```

Mục tiêu của Axiom không phải tạo một backend “siêu tổng quát” nhưng nặng nề. Mục tiêu là:

> **Một backend có mô hình machine đủ mạnh để khai thác CPU hiện đại, nhưng kiến trúc đủ rõ ràng để sau này compiler Axiom có thể tự implement backend và self-host.**

---

# 1. Phân tầng backend

Không cho phép nhảy trực tiếp:

```text
AST → x86 instruction
```

Axiom sử dụng:

```text
MIR
 ↓
OptIR
 ↓
ABI MIR
 ↓
Axiom LIR
 ↓
Machine IR
 ↓
Machine Code
```

---

# 2. Axiom LIR

LIR vẫn còn mang tính target-independent.

Ví dụ:

```text
add i64
load
store
branch
call
return
compare
select
convert
atomic
```

Nó chưa nói:

```text
ADD RAX, RBX
```

---

# 3. Machine IR

Machine IR bắt đầu hiểu:

```text
register
register class
physical register
stack slot
immediate
memory operand
condition code
calling convention
target instruction
```

---

# 4. Machine IR không phải assembly text

Không tạo backend bằng cách sinh string:

```text
"mov rax, rbx"
```

Thay vào đó:

```text
MachineInstruction {
    opcode
    operands[]
    constraints
    flags
    implicit_uses
    implicit_defs
}
```

---

# 5. Virtual register

Instruction selection tạo:

```text
vreg0
vreg1
vreg2
```

thay vì ngay lập tức chọn:

```text
RAX
RBX
RCX
```

---

# 6. Vì sao?

Register allocation phải có quyền:

```text
vreg0 → RAX
vreg1 → XMM0
vreg2 → stack[32]
```

sau khi toàn bộ machine code được phân tích.

---

# 7. Register class

Mỗi virtual register có class:

```text
GPR
FPR
Vector
Mask
Special
```

Ví dụ:

```text
i64 → GPR
f64 → FPR
Vec4 → Vector
```

---

# 8. Register bank

Target có thể có nhiều register bank.

Ví dụ conceptual:

```text
IntegerBank
FloatBank
VectorBank
PredicateBank
```

---

# 9. Physical register

Target backend khai báo:

```text
PhysicalRegister {
    id
    name
    class
    width
    aliases
    caller_saved
    callee_saved
}
```

---

# 10. Register aliasing

Ví dụ x86:

```text
RAX
EAX
AX
AL
```

không phải bốn register độc lập.

Backend phải mô hình hóa alias.

---

# 11. Subregister

Machine IR cần hiểu:

```text
RAX[31:0]
```

khác với:

```text
RAX[63:0]
```

---

# 12. Register pressure

Compiler theo dõi:

```text
live virtual registers
```

để biết khi nào cần spill.

---

# 13. Spill

Nếu không đủ register:

```text
vreg
 ↓
stack slot
```

Compiler chèn:

```text
spill
reload
```

---

# 14. Spill không thay đổi semantics

Đây là physical implementation detail.

---

# 15. Stack slot

```text
StackSlot {
    size
    alignment
    kind
    lifetime
}
```

---

# 16. Stack slot lifetime

Compiler có thể reuse cùng stack slot cho hai locals nếu lifetime không overlap.

---

# 17. Stack coloring

Ví dụ:

```text
a sống [1..5]
b sống [6..10]
```

có thể dùng cùng slot.

---

# 18. Stack allocation ≠ semantic local

Một semantic local có thể:

```text
register
stack
eliminated
scalarized
```

---

# 19. Machine memory operand

Conceptual:

```text
MemoryOperand {
    base
    index
    scale
    displacement
    address_space
    alignment
}
```

---

# 20. x86

Có thể lower:

```text
base = RAX
index = RCX
scale = 4
disp = 16
```

thành addressing mode của x86.

---

# 21. ARM64

Không được ép ARM phải giả lập x86 addressing model.

ARM backend có memory operand riêng.

---

# 22. RISC-V

Tương tự.

---

# 23. Addressing model

LIR chỉ cần semantic:

```text
load(base + offset)
```

Machine backend quyết định cách materialize.

---

# 24. Instruction selection

Ví dụ LIR:

```text
z = add(x, y)
```

x86:

```text
ADD
```

ARM64:

```text
ADD
```

RISC-V:

```text
ADD
```

nhưng constraints khác nhau.

---

# 25. Complex operations

Ví dụ:

```text
multiply_add(a,b,c)
```

target có FMA:

```text
FMA
```

nếu semantics/profile cho phép.

---

# 26. Strict FP

Axiom mặc định strict FP.

Do đó compiler không tự biến:

```text
a*b+c
```

thành FMA nếu điều đó thay đổi observable floating-point semantics theo profile.

---

# 27. Fast math

Nếu:

```text
@fast_math
```

hoặc compilation profile cho phép:

compiler có thể dùng FMA/reassociation/etc.

---

# 28. Integer operations

LIR:

```text
add_checked
add_wrapping
add_saturating
```

không chỉ một `ADD`.

---

# 29. Vì vậy instruction selection không được suy diễn từ source operator đơn giản

Semantic operation đã được xác định trước.

---

# 30. Compare

Axiom:

```text
x < y
```

được lower thành target-specific compare/condition code.

---

# 31. Condition representation

Machine IR có thể dùng:

```text
ConditionCode
```

ví dụ:

```text
EQ
NE
LT
LE
GT
GE
```

---

# 32. Flags

Một số CPU dùng implicit flags.

Machine IR phải biểu diễn:

```text
implicit def: FLAGS
implicit use: FLAGS
```

---

# 33. Điều này rất quan trọng

Nếu:

```text
CMP
ADD
Jcc
```

thì optimizer phải biết instruction nào làm thay đổi flags.

---

# 34. Target instruction descriptor

Mỗi instruction:

```text
Opcode
Operands
OperandConstraints
RegisterUses
RegisterDefs
ImplicitUses
ImplicitDefs
Latency
Throughput
Size
SchedulingClass
```

---

# 35. Latency

Được dùng cho instruction scheduling.

---

# 36. Throughput

Được dùng để tối ưu loop/hot code.

---

# 37. Nhưng không đưa microarchitecture vào semantics

CPU timing không phải language semantics.

---

# 38. Target CPU model

```text
TargetCPU {
    ISA
    Extensions
    Features
    MicroArchitecture
}
```

---

# 39. ISA feature

Ví dụ:

```text
SSE2
AVX2
AVX512
NEON
SVE
RVV
```

---

# 40. Feature checking

Nếu source yêu cầu:

```text
@target(feature="avx2")
```

compiler phải kiểm tra target.

---

# 41. Multiversioning

Axiom có thể tạo:

```text
foo_default
foo_avx2
foo_avx512
```

và dispatch theo target/runtime feature nếu explicitly requested.

---

# 42. Không có hidden CPU dispatch

Compiler không tự thêm runtime CPU detection vào mọi binary.

---

# 43. Static target

Nếu binary target cố định AVX2:

→ direct AVX2 code.

---

# 44. Portable target

Có thể generate runtime dispatch library.

---

# 45. Instruction selection strategies

Axiom backend hỗ trợ:

```text
Pattern matching
DAG selection
Tree selection
Custom lowering
```

---

# 46. Không cần bắt đầu bằng một framework khổng lồ

Bootstrap backend nên dùng:

> **Pattern-based instruction selection + target-specific legalization hooks.**

---

# 47. Pattern

Conceptual:

```text
add(x, y)
→ ADD reg, reg
```

---

# 48. Memory pattern

```text
load(add(base, const))
→
target load [base + offset]
```

---

# 49. Constant folding

Nếu:

```text
add(x, 0)
```

semantic optimizer đã có thể loại bỏ trước machine selection.

---

# 50. Machine peephole

Sau instruction selection vẫn có:

```text
MachinePeephole
```

để xử lý target-specific patterns.

---

# 51. Legalization

Không phải mọi LIR operation đều có native instruction.

Ví dụ:

```text
u128_add
```

trên CPU không có native 128-bit integer.

---

# 52. Lowering

Có thể biến:

```text
u128_add
```

thành:

```text
ADD low
ADC high
```

---

# 53. Đây là target legalization

```text
LIR operation
 ↓
Legal
```

hoặc:

```text
LIR operation
 ↓
Expand
```

---

# 54. Expand không được thay đổi semantics

Đặc biệt:

- overflow
- carry
- traps
- atomicity
- volatile
- ordering.

---

# 55. Atomic legalization

Nếu CPU có:

```text
atomic RMW
```

dùng instruction trực tiếp.

Nếu không:

có thể dùng lock/runtime mechanism tùy target và semantic contract.

---

# 56. Nhưng compiler không được tự biến atomic thành ordinary load/store.

---

# 57. Memory ordering

Machine backend map:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

sang target-specific instruction/fence.

---

# 58. Fence

LIR:

```text
Fence(Acquire)
```

↓

target-specific barrier.

---

# 59. Volatile

Volatile operation phải giữ semantic observable memory access.

Không được:

```text
remove
merge
cache
reorder
```

trái với volatile contract.

---

# 60. Machine instruction flags

Mỗi memory instruction cần metadata:

```text
Load
Store
Atomic
Volatile
Barrier
```

---

# 61. Address space

Machine IR cần hỗ trợ:

```text
Default
GPU
MMIO
TLS
Device
Special
```

---

# 62. CPU MMIO

Volatile + explicit address-space semantics.

---

# 63. GPU

GPU backend không nên hack CPU Machine IR.

Nó dùng:

```text
GpuMachineIR
```

hoặc target-specific machine dialect.

---

# 64. Nhưng shared concepts

Cả CPU/GPU dùng:

```text
Register
Memory
Instruction
Call
Barrier
Atomic
AddressSpace
```

---

# 65. Machine IR interface

Conceptual:

```text
MachineTargetBackend {
    legalize()
    select()
    lower_call()
    lower_branch()
    lower_atomic()
    lower_memory()
    allocate_registers()
    emit_prologue()
    emit_epilogue()
    encode()
}
```

---

# 66. Backend independence

Frontend không được import:

```text
x86
ARM
RISC-V
```

---

# 67. Target backend registry

```text
TargetRegistry
 ├── x86_64
 ├── aarch64
 ├── riscv64
 ├── wasm32
 └── ...
```

---

# 68. Target-specific code isolated

Ví dụ:

```text
backend/
  x86/
  arm64/
  riscv/
  wasm/
```

---

# 69. Common backend

```text
backend/
  machine_ir/
  register/
  allocator/
  scheduler/
  peephole/
  encoder/
```

---

# 70. Instruction encoding

Machine IR:

```text
ADD RAX, RBX
```

↓

binary opcode bytes.

---

# 71. Encoder

Encoder chịu trách nhiệm:

```text
opcode
ModRM
SIB
immediate
prefix
REX
relocation
```

đối với x86.

---

# 72. ARM64

Encoder xử lý:

```text
instruction fields
immediates
register fields
branch displacement
```

---

# 73. RISC-V

Tương tự với các instruction formats.

---

# 74. Không sinh assembly trung gian mặc định

Axiom cuối cùng nên:

```text
Machine IR
 ↓
ObjectWriter
```

trực tiếp.

---

# 75. Nhưng assembly output vẫn hữu ích

Có:

```text
ax emit asm
```

cho debug/inspection.

---

# 76. Assembly output là diagnostic artifact

Không phải compiler pipeline bắt buộc.

---

# 77. Branch lowering

LIR:

```text
branch condition
```

↓

machine:

```text
CMP
Jcc
```

hoặc:

```text
CBZ
```

hoặc branch instruction tương ứng.

---

# 78. Conditional select

LIR:

```text
select(cond, a, b)
```

có thể lower:

```text
CMOV
CSEL
conditional instruction
```

nếu target có.

---

# 79. Branchless optimization

Có thể thay branch bằng arithmetic/select nếu semantics preserved.

---

# 80. Branch probability

OptIR có thể mang:

```text
likely
unlikely
profile_probability
```

Machine scheduler dùng chúng.

---

# 81. Không cho programmer điều khiển machine branch trực tiếp trong Core

Intrinsic/system layer có thể có khi cần.

---

# 82. Function call lowering

Machine backend nhận:

```text
ABICall
```

và tạo:

```text
register moves
stack setup
call
return value moves
```

---

# 83. Parallel move

Ví dụ:

```text
arg0 → RDI
arg1 → RSI
```

có thể có cycle:

```text
RDI → RSI
RSI → RDI
```

cần temporary register/stack.

---

# 84. ParallelMove

Machine IR nên có:

```text
ParallelMove {
    assignments[]
}
```

sau đó resolver phá cycle.

---

# 85. Return lowering

```text
return v
```

↓

ABI return registers/stack.

---

# 86. Call clobber

Machine IR call khai báo:

```text
defs = caller_saved registers
```

---

# 87. Register allocator phải coi call như clobber boundary.

---

# 88. Callee-saved

Nếu function dùng:

```text
RBX
```

backend phải save/restore nếu ABI yêu cầu.

---

# 89. Lazy save

Chỉ save register thực sự được dùng.

---

# 90. Prologue

Có thể bao gồm:

```text
stack allocation
callee-save
stack probes
security mechanisms
TLS setup
```

chỉ khi target/profile yêu cầu.

---

# 91. Stack probing

Large stack frame trên một số OS cần probing.

Target backend chịu trách nhiệm.

---

# 92. Stack canary

Security profile có thể thêm stack protection.

Không phải Core semantics.

---

# 93. Shadow stack / CET / PAC

Có thể target-specific.

---

# 94. W^X

Object/linker/security layer đảm bảo executable pages không writable đồng thời khi platform yêu cầu.

---

# 95. Register allocation

Axiom nên hỗ trợ:

```text
Linear Scan
Graph Coloring
Hybrid allocator
```

---

# 96. Bootstrap allocator

Ban đầu:

> **Linear Scan**

vì đơn giản, dễ self-host.

---

# 97. Optimizing allocator

Sau này:

> **Hybrid / graph-based allocator**

cho hot code.

---

# 98. Compiler chọn allocator theo profile

```text
debug → fast allocation
release → optimizing allocation
size → size-aware allocation
```

---

# 99. Không thay đổi semantics.

---

# 100. Live interval

Mỗi vreg có:

```text
start
end
uses
register class
constraints
```

---

# 101. Interference

Hai vreg sống đồng thời không thể dùng cùng register nếu class/constraints xung đột.

---

# 102. Register coalescing

Nếu:

```text
v1 = v2
```

compiler cố gắng assign cùng register.

---

# 103. Copy elimination

Ví dụ:

```text
MOV RAX, RBX
```

có thể biến mất nếu allocation phù hợp.

---

# 104. Phi elimination

SSA phi:

```text
x = φ(a,b)
```

được chuyển thành parallel moves tại CFG edges.

---

# 105. Critical edge

Phi lowering phải xử lý critical edge insertion khi cần.

---

# 106. Machine CFG

Machine IR vẫn có:

```text
BasicBlock
Edge
Successor
Predecessor
```

---

# 107. Exception/unwind edges

Nếu unwind enabled:

Machine CFG có thể cần exceptional control-flow metadata.

---

# 108. Panic abort

Nếu profile:

```text
panic=abort
```

backend đơn giản hơn.

---

# 109. Panic unwind

Nếu:

```text
panic=unwind
```

cần:

```text
unwind tables
landing pads
cleanup
```

---

# 110. Cleanup

Semantic Drop đã được elaborated trước backend.

Backend chỉ thực hiện physical control flow.

---

# 111. No hidden destructor machinery

Drop calls đã tồn tại semantic MIR.

---

# 112. Instruction scheduling

Sau register allocation hoặc trước tùy target:

```text
schedule instructions
```

---

# 113. Dependency graph

Scheduler phải respect:

```text
data dependency
memory dependency
atomic
volatile
call
barrier
flags
```

---

# 114. Memory dependency

Ordinary independent loads có thể reorder.

Volatile/atomic constraints thì không.

---

# 115. Call barrier

Unknown foreign call có broad memory effects.

Scheduler không được move memory operations qua nó nếu semantics cấm.

---

# 116. CPU-specific scheduling

Hot target có thể dùng:

```text
latency
throughput
port pressure
```

---

# 117. Nhưng bootstrap không cần mô hình CPU cực kỳ phức tạp.

---

# 118. CPU optimization tiers

```text
Tier 0:
correct selection

Tier 1:
peephole + basic scheduling

Tier 2:
register pressure + target scheduling

Tier 3:
microarchitecture tuning
```

---

# 119. Self-host roadmap

Compiler đầu tiên:

```text
Axiom frontend
 ↓
MIR
 ↓
external LLVM/LLD
```

nhưng kiến trúc semantic không phụ thuộc LLVM.

---

# 120. Backend v1

```text
Axiom MIR
 ↓
Axiom LIR
 ↓
LLVM bridge
```

---

# 121. Backend native

Sau đó:

```text
Axiom MIR
 ↓
Axiom LIR
 ↓
Axiom Machine IR
 ↓
Axiom Encoder
```

---

# 122. Đây là điểm rất quan trọng

**LLVM là bootstrap implementation, không phải semantic dependency của Axiom.**

---

# 123. Cuối cùng

```text
axc
 ├── frontend
 ├── verifier
 ├── optimizer
 ├── LIR
 ├── machine backend
 ├── object writer
 └── linker
```

đều có thể viết bằng Axiom.

---

# 124. Backend testing

Mỗi instruction pattern cần:

```text
LIR input
→ expected machine semantics
```

---

# 125. Encoder testing

```text
MachineInstruction
→ bytes
→ disassemble/reference
→ compare
```

---

# 126. Differential backend testing

Chạy cùng chương trình:

```text
ax-ref
ax-mir
LLVM backend
native backend
```

so sánh observable semantics.

---

# 127. Random instruction testing

Generate legal Machine IR:

```text
Machine IR
→ encoder
→ executable
→ result
```

---

# 128. Relocation testing

Backend + object writer phải test:

```text
local calls
external calls
branch
data address
TLS
GOT/PLT
imports
exports
```

---

# 129. Register allocator testing

Stress:

```text
high register pressure
call boundaries
subregisters
vector registers
spill
reload
phi
loops
```

---

# 130. Machine verifier

Trước encoding:

```text
MachineVerifier
```

kiểm tra:

- register class
- operand constraints
- physical register legality
- stack alignment
- call convention
- clobber
- instruction legality
- CFG
- branch targets
- memory operand
- relocation validity.

---

# 131. Không cho Machine IR không hợp lệ tới encoder.

---

# 132. Backend pipeline hoàn chỉnh

```text
ABI MIR
   ↓
LIR construction
   ↓
Target legalization
   ↓
Instruction selection
   ↓
Machine SSA/CFG
   ↓
Machine optimization
   ↓
Phi elimination
   ↓
Register allocation
   ↓
Spill/reload
   ↓
Register coalescing
   ↓
Prologue/epilogue
   ↓
Late peephole
   ↓
Branch relaxation
   ↓
Machine verification
   ↓
Instruction encoding
   ↓
Object
```

---

# 133. Branch relaxation

Ví dụ branch displacement quá lớn:

```text
short jump
```

không đủ.

Backend đổi thành:

```text
long jump
```

hoặc sequence tương ứng.

---

# 134. Đây là lý do encoding không nên làm một lần quá sớm.

---

# 135. Instruction size

x86 đặc biệt cần late layout vì instruction size biến đổi.

---

# 136. Layout feedback

```text
Machine layout
→ instruction offsets
→ branch distance
→ encoding choice
→ final offsets
```

có thể cần iterative relaxation.

---

# 137. ARM/RISC-V

Encoding thường regular hơn nhưng vẫn cần relocation/range handling.

---

# 138. Code alignment

Compiler có thể align hot functions/loops khi profile yêu cầu.

---

# 139. Size profile

`--profile size` ưu tiên:

```text
short encoding
fewer instructions
less alignment padding
less duplicate code
```

---

# 140. Speed profile

`--profile release` có thể ưu tiên:

```text
throughput
alignment
vectorization
unrolling
instruction selection
```

---

# 141. Size vs speed

Đây là codegen policy, không semantic difference.

---

# 142. CPU feature dispatch

Profile/configuration xác định.

Không hidden.

---

# 143. Machine IR debug

Compiler có thể:

```text
ax inspect --mir
ax inspect --lir
ax inspect --machine
ax emit asm
```

---

# 144. AI explain

Ví dụ:

```text
ax explain instruction foo
```

có thể trả:

```text
Operation:
    i64 multiply

Selected:
    IMUL

Reason:
    target x86-64
    scalar integer
    overflow semantics = wrapping

Alternative:
    library expansion not required
```

---

# 145. Register explanation

```text
why spilled?
```

→:

```text
Register pressure at call site:
17 GPR live values
available:
15
```

---

# 146. Điều này rất hữu ích cho AI agent.

---

# 147. CompilerDB additions

```text
MachineDB
TargetDB
RegisterDB
InstructionDB
SelectionDB
AllocationDB
ScheduleDB
EncodingDB
```

---

# 148. IDs

```text
MachineFunctionId
MachineBlockId
MachineInstructionId
VirtualRegisterId
PhysicalRegisterId
RegisterClassId
StackSlotId
InstructionPatternId
EncodingId
```

---

# 149. Target backend contract

Mỗi target phải định nghĩa:

```text
TargetSpec
RegisterFile
InstructionSet
CallingConvention
LegalTypes
LegalOperations
InstructionPatterns
LoweringRules
EncodingRules
RelocationRules
UnwindRules
ObjectFormat
```

---

# 150. Không để frontend biết chi tiết target.

---

# 151. Semantic invariants

```text
AMACHINE-20
Machine IR is derived only from verified semantic IR.

AMACHINE-21
Machine lowering cannot introduce semantic behavior not present in the source contract.

AMACHINE-22
Machine lowering must preserve observable behavior.

AMACHINE-23
Virtual registers are distinct from semantic source variables.

AMACHINE-24
Physical register assignment is a backend concern.

AMACHINE-25
Register classes are target-specific.

AMACHINE-26
Physical registers may have aliases and subregisters.

AMACHINE-27
Register aliasing must be represented explicitly.

AMACHINE-28
Spilling must preserve semantics.

AMACHINE-29
Stack slots are physical storage, not semantic variables.

AMACHINE-30
Stack-slot reuse requires non-overlapping physical lifetimes.

AMACHINE-31
Machine memory operands must respect target addressing rules.

AMACHINE-32
Target addressing modes must not leak into Core semantics.

AMACHINE-33
Instruction selection is target-specific.

AMACHINE-34
Instruction selection must preserve operation semantics.

AMACHINE-35
Illegal target operations must be legalized or expanded before encoding.

AMACHINE-36
Legalization must preserve overflow semantics.

AMACHINE-37
Legalization must preserve atomic semantics.

AMACHINE-38
Legalization must preserve volatile semantics.

AMACHINE-39
Legalization must preserve synchronization semantics.

AMACHINE-40
Legalization must preserve panic/termination semantics.

AMACHINE-41
Strict floating-point semantics must not be weakened by instruction selection.

AMACHINE-42
Fast-math transformations require explicit authorization.

AMACHINE-43
Atomic operations cannot be lowered to ordinary non-atomic operations.

AMACHINE-44
Volatile operations cannot be eliminated as ordinary dead loads/stores.

AMACHINE-45
Memory ordering must be preserved during machine lowering.

AMACHINE-46
Machine instruction implicit register uses/defs must be represented.

AMACHINE-47
Condition-code dependencies must be represented.

AMACHINE-48
Call instructions must model ABI register clobbers.

AMACHINE-49
Callee-saved register requirements must be honored.

AMACHINE-50
Caller-saved registers must not be assumed live across calls.

AMACHINE-51
ABI stack alignment must be preserved.

AMACHINE-52
Parallel argument moves must be resolved without semantic loss.

AMACHINE-53
Return values must obey ABI return classification.

AMACHINE-54
sret/caller-allocated returns must preserve ownership semantics.

AMACHINE-55
Phi elimination must preserve CFG semantics.

AMACHINE-56
Critical-edge handling must preserve control-flow semantics.

AMACHINE-57
Spill/reload insertion cannot invalidate memory or capability semantics.

AMACHINE-58
Machine scheduling must preserve data dependencies.

AMACHINE-59
Machine scheduling must preserve memory dependencies.

AMACHINE-60
Machine scheduling must preserve atomic and volatile ordering.

AMACHINE-61
Machine scheduling must preserve call effects.

AMACHINE-62
Machine scheduling must preserve condition-code dependencies.

AMACHINE-63
Instruction latency is an optimization fact, not language semantics.

AMACHINE-64
Microarchitectural tuning cannot alter observable program semantics.

AMACHINE-65
Target CPU features must be explicitly known by compilation configuration or explicit dispatch mechanisms.

AMACHINE-66
Axiom must not silently introduce runtime CPU feature dispatch.

AMACHINE-67
Target-specific instructions require corresponding target feature availability.

AMACHINE-68
Machine IR must be target-verifiable before encoding.

AMACHINE-69
Invalid Machine IR must never reach the encoder.

AMACHINE-70
Instruction encoding must be deterministic.

AMACHINE-71
Relocation requirements must be represented explicitly.

AMACHINE-72
Instruction size changes must be handled before final object emission.

AMACHINE-73
Branch relaxation must preserve branch semantics.

AMACHINE-74
Machine code layout must preserve required alignment contracts.

AMACHINE-75
Debug information must retain source-to-machine provenance.

AMACHINE-76
Machine transformations must preserve debug provenance where possible.

AMACHINE-77
Machine optimization may remove physical operations only when semantic equivalence is preserved.

AMACHINE-78
Equivalent machine operations may be merged only when observable identity is unaffected.

AMACHINE-79
Function-address observability constrains machine-level code merging.

AMACHINE-80
Machine code generation is independent of source-level pointer/reference syntax.

AMACHINE-81
Machine backend may use pointer representations internally without exposing them to safe Core.

AMACHINE-82
Machine backend may introduce physical temporaries without semantic temporaries.

AMACHINE-83
Physical copies do not imply semantic Copy.

AMACHINE-84
Semantic Move does not require physical movement.

AMACHINE-85
Machine backend must preserve ownership/drop behavior.

AMACHINE-86
Machine backend must preserve capability validity.

AMACHINE-87
Machine backend must preserve execution-domain constraints.

AMACHINE-88
GPU machine lowering is distinct from CPU machine lowering.

AMACHINE-89
GPU address spaces must not be confused with CPU address spaces.

AMACHINE-90
WASM machine lowering uses WASM-specific value and memory semantics.

AMACHINE-91
Backend target isolation must prevent frontend dependence on ISA details.

AMACHINE-92
Target backends must implement a common machine backend contract.

AMACHINE-93
A bootstrap LLVM backend may exist without making LLVM a language semantic dependency.

AMACHINE-94
The final compiler must be capable of replacing the bootstrap backend with native Axiom backends.

AMACHINE-95
Native Axiom backend design must be self-hostable.

AMACHINE-96
Machine IR must be serializable for debugging/testing.

AMACHINE-97
Instruction selection must be independently testable.

AMACHINE-98
Register allocation must be independently testable.

AMACHINE-99
Instruction encoding must be independently testable.

AMACHINE-100
Machine backend conformance is part of compiler correctness.

AMACHINE-101
Backend failures must be distinguishable from semantic compiler failures.

AMACHINE-102
AI tooling may inspect machine decisions but cannot override machine verification.

AMACHINE-103
Optimization profiles may change machine code but not language semantics.

AMACHINE-104
Size optimization may trade execution speed for binary size without changing semantics.

AMACHINE-105
Performance optimization may trade binary size for execution speed without changing semantics.

AMACHINE-106
Debug optimization settings must not change observable language semantics.

AMACHINE-107
Freestanding targets must not require hosted runtime machinery.

AMACHINE-108
Machine lowering must not introduce mandatory garbage collection.

AMACHINE-109
Machine lowering must not introduce mandatory reference counting.

AMACHINE-110
Machine lowering must not introduce mandatory object headers.

AMACHINE-111
Machine lowering must not require programmer-visible pointer syntax.

AMACHINE-112
Machine backend must support direct native object emission.

AMACHINE-113
Assembly emission is an optional diagnostic artifact.

AMACHINE-114
Object emission must not require assembly as an intermediate representation.

AMACHINE-115
The native backend must be capable of directly producing PE, ELF, Mach-O and WASM-compatible output paths through the appropriate object backend.

AMACHINE-116
Machine backend target selection is determined by TargetSpec.

AMACHINE-117
Machine backend must be deterministic for a fixed compiler semantic/codegen configuration.

AMACHINE-118
Machine code differences caused by optimization are allowed when semantics remain equivalent.

AMACHINE-119
Machine-level correctness is verified before object emission.

AMACHINE-120
The Machine IR is the final compiler abstraction before target-specific binary encoding.
```

---

# Axiom backend lúc này đã có hình dạng khá hoàn chỉnh

```text
                    AXIOM FRONTEND
                         │
                         ▼
                  Verified MIR
                         │
                         ▼
                   Semantic Opt
                         │
                         ▼
                     ABI MIR
                         │
                         ▼
                     Axiom LIR
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
            x86-64      ARM64      RISC-V
              │          │          │
              ▼          ▼          ▼
          Machine IR / Target IR
              │          │          │
              ▼          ▼          ▼
          RegAlloc / Scheduling / Peephole
              │
              ▼
          Machine Encoding
              │
              ▼
         Axiom Object Model
              │
              ▼
          PE / ELF / Mach-O
```

Điểm đáng chú ý là **LLVM không nằm trong kiến trúc semantic của Axiom**. LLVM có thể là backend bootstrap rất hữu ích, nhưng về mặt thiết kế cuối cùng Axiom đã có đủ các abstraction cần thiết để tự viết backend.

---

# BOOTSTRAP-260 — bước tiếp theo

Backend đã có Machine IR, nhưng còn một mảnh rất quan trọng trước khi đi sâu vào từng ISA:

## **AXIOM MEMORY CODEGEN, POINTER PROVENANCE, ADDRESS CALCULATION & LOAD/STORE LOWERING**

Tức là đi từ:

```text
Place
  ↓
Address
  ↓
Pointer Provenance
  ↓
Memory Access
  ↓
Load / Store
  ↓
Atomic / Volatile
  ↓
Machine Memory Operand
```

để khóa chặt một vấn đề cực kỳ quan trọng của Axiom:

> **Compiler được phép dùng pointer và address ở bên dưới, nhưng programmer không phải gánh complexity của pointer/reference; đồng thời optimizer tuyệt đối không được biến một access hợp lệ thành access sai provenance hoặc sai alias.**

Sau BOOTSTRAP-260, chúng ta sẽ có nền tảng đủ chắc để đi sâu vào **x86-64/ARM64/RISC-V backend**, thay vì thiết kế ISA backend khi memory semantics vẫn còn chưa khóa.