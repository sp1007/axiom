# BOOTSTRAP-561 — COMPILER CODE GENERATION 3.0, INSTRUCTION SELECTION, MACHINE IR, REGISTER ALLOCATION, SCHEDULING, PROLOGUE/EPILOGUE & VERIFIED NATIVE LOWERING

**Trạng thái: COMPLETED / LOCKED**

`561` khóa toàn bộ tầng chuyển từ **Optimized MIR → Machine IR → native machine code**. Đây là tầng quyết định trực tiếp chất lượng mã máy, hiệu năng CPU, kích thước binary và khả năng Axiom tự tạo native executable mà không cần LLVM/GCC/Clang/MSVC làm compiler backend.

---

## 561.1. Vị trí trong pipeline

```text id="m4x7q2"
                     Optimized MIR
                          │
                          ▼
                  Target Lowering
                          │
                          ▼
                 Instruction Selection
                          │
                          ▼
                   Legalization
                          │
                          ▼
                     Machine IR
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
        Reg Classes   Machine CFG   Frame Info
             │            │            │
             └────────────┼────────────┘
                          ▼
                  Register Allocation
                          │
                          ▼
                 Spill / Reload
                          │
                          ▼
                Machine Scheduling
                          │
                          ▼
                Prologue / Epilogue
                          │
                          ▼
               Machine Optimization
                          │
                          ▼
                  Branch Relaxation
                          │
                          ▼
                 Machine Encoder
                          │
                          ▼
                    Object File
```

---

# 561.2. Machine IR là gì?

Machine IR (MIR-machine, để tránh nhầm với semantic MIR) là representation gần machine code nhưng vẫn đủ abstraction để:

- register allocation;
- scheduling;
- spilling;
- peephole;
- target-specific optimization;
- frame lowering.

---

# 561.3. Machine IR entity

```text id="q8n3v5"
MachineFunction {
    function_id
    blocks[]
    virtual_registers[]
    physical_registers[]
    frame_info
    calling_convention
    target_features
    debug_info
    unwind_info
}
```

---

# 561.4. Machine basic block

```text id="j5r9c1"
MachineBlock {
    id
    instructions[]
    successors[]
    predecessors[]
    frequency
}
```

---

# 561.5. Machine instruction

```text id="v2m7x4"
MachineInstruction {
    opcode
    operands[]
    implicit_uses[]
    implicit_defs[]
    constraints
    flags
    source_location
    provenance
}
```

---

# 561.6. Machine operands

Tối thiểu:

```text id="w8k1p6"
VirtualReg
PhysicalReg
Immediate
MemoryOperand
BlockRef
SymbolRef
ConstantPoolRef
StackSlot
RegisterMask
```

---

# 561.7. Virtual registers

Instruction selection tạo virtual registers thay vì ép ngay vào physical registers.

```text id="c4q9n2"
v0 = ADD v1, v2
```

---

# 561.8. Physical registers

Target backend định nghĩa:

```text id="x7m3p5"
GPR
FPR
Vector
Mask
Special
Predicate
```

tùy ISA.

---

# 561.9. Register class

Ví dụ x86-64:

```text id="a5f8k2"
GPR64
GPR32
XMM
YMM
ZMM
FLAGS
```

AArch64:

```text id="n6q2v8"
GPR
FP/SIMD
NZCV
```

---

# 561.10. Register aliasing

Backend phải biết:

```text id="r3x7m1"
RAX
 ├── EAX
 ├── AX
 ├── AL
 └── AH
```

là các views/aliases của cùng physical register resource.

---

# 561.11. Register units

Một physical register có thể được mô hình hóa bằng register units để phát hiện overlap.

---

# 561.12. Instruction selection

Mục tiêu:

```text id="p8v4m6"
MIR operation
      ↓
one or more
MachineInstructions
```

---

# 561.13. Selection strategy

Axiom hỗ trợ:

```text id="y6k1q3"
pattern matching
DAG selection
global selection
target-specific lowering
```

Implementation có thể kết hợp.

---

# 561.14. Pattern definition

Backend có thể khai báo:

```text id="b4m8x2"
Pattern {
    input
    conditions
    output
    cost
}
```

---

# 561.15. Example

Semantic:

```text id="g7q2n5"
a + b
```

x86-64:

```text id="c8v3m1"
add rax, rbx
```

AArch64:

```text id="m2x9k4"
add x0, x1, x2
```

---

# 561.16. Selection không được thay đổi semantics

Pattern chỉ hợp lệ khi:

```text id="t5p8z2"
source semantics
≡
machine semantics
```

---

# 561.17. Target-independent selection

Các operation phổ biến:

```text id="w1q6m9"
add
sub
mul
load
store
compare
branch
call
return
```

có thể được biểu diễn target-independently.

---

# 561.18. Target-specific operation

Ví dụ:

```text id="f3n7c5"
AES instruction
CRC
vector shuffle
bit manipulation
```

được expose khi target feature cho phép.

---

# 561.19. Target feature set

```text id="j8m2q6"
TargetFeatures {
    isa
    extensions[]
    tuning_cpu
    tuning_features[]
}
```

---

# 561.20. Feature legality

Machine instruction chỉ được chọn nếu target feature hỗ trợ.

---

# 561.21. CPU baseline

Mỗi target có baseline ISA.

Ví dụ conceptually:

```text id="v9x3p1"
x86-64 baseline
AArch64 baseline
```

sau đó mở rộng bằng feature flags.

---

# 561.22. Multi-versioning

Compiler có thể tạo:

```text id="c5m8k2"
generic implementation
optimized implementation
```

và runtime dispatch nếu explicit policy cho phép.

---

# 561.23. Runtime dispatch

```text id="n4q7x9"
if CPU supports AVX2:
    foo_avx2()
else:
    foo_generic()
```

---

# 561.24. No hidden ISA dependency

Binary không được sử dụng instruction ngoài target contract.

---

# 561.25. Legalization

MIR operation có thể không có direct machine instruction.

Ví dụ:

```text id="k8p2m5"
128-bit integer multiply
```

có thể lower thành sequence.

---

# 561.26. Legalization stages

```text id="x3v7n1"
Generic operation
      ↓
Target legal operation
      ↓
Machine instruction
```

---

# 561.27. Expand

Một operation có thể expand thành nhiều instructions.

---

# 561.28. Libcall

Compiler có thể generate runtime helper khi target không có instruction phù hợp.

Nhưng helper phải thuộc Axiom runtime/toolchain contract, không mặc định yêu cầu external compiler runtime.

---

# 561.29. Inline expansion

Các operation nhỏ có thể expand inline thay vì libcall.

---

# 561.30. Division

Integer division phải có lowering cho:

```text id="q5m8x2"
constant divisor
variable divisor
signed
unsigned
```

---

# 561.31. Division by constant

Optimizer/codegen có thể biến thành multiply/shift sequence khi semantics và cost model cho phép.

---

# 561.32. Wide integer lowering

Nếu target không có native width:

```text id="r2x6m9"
wide operation
→ multiple machine operations
```

---

# 561.33. Boolean lowering

Axiom `bool` semantics được map vào target representation mà không làm thay đổi logical semantics.

---

# 561.34. Compare lowering

So sánh có thể lower thành:

```text id="f6p3k8"
flags
setcc
branch
predicate
```

tùy target.

---

# 561.35. Condition codes

Backend phải model implicit flags.

```text id="w4n9q2"
ADD → FLAGS
CMP → FLAGS
BRANCH consumes FLAGS
```

---

# 561.36. Implicit operands

Machine instruction phải khai báo implicit register uses/defs.

---

# 561.37. Register constraints

Một instruction có thể yêu cầu operand ở register cụ thể.

Ví dụ concept:

```text id="j7m2v5"
division → specific registers
```

---

# 561.38. Fixed registers

Register allocator phải support fixed-register constraints.

---

# 561.39. Early-clobber

Backend phải biểu diễn operand bị overwrite trước khi tất cả input consumed nếu ISA yêu cầu.

---

# 561.40. Tied operands

Ví dụ:

```text id="c9x4n7"
output register == input register
```

phải được biểu diễn explicit.

---

# 561.41. Register allocator

Mục tiêu:

```text id="m8q3v1"
Virtual Registers
      ↓
Physical Registers
```

---

# 561.42. Allocation constraints

Allocator phải respect:

- register class;
- liveness;
- interference;
- fixed registers;
- calling convention;
- instruction constraints.

---

# 561.43. Liveness

Mỗi virtual register có:

```text id="p4k7x2"
def
uses
live range
```

---

# 561.44. Live interval

```text id="v1m8q5"
v0:
 [instruction 4 → instruction 17]
```

---

# 561.45. Interference

Hai live ranges overlap thì không thể cùng physical register nếu không alias-compatible.

---

# 561.46. Register allocation strategies

Axiom backend hỗ trợ:

```text id="x7q2n4"
Linear Scan
Graph Coloring
Priority-based allocation
Hybrid allocation
```

---

# 561.47. Default allocator

Production backend nên dùng **hybrid allocator**:

```text id="n5m9c3"
fast allocation
+
local splitting
+
priority optimization
```

để cân bằng compile-time và code quality.

---

# 561.48. Debug builds

Debug có thể ưu tiên allocation nhanh.

---

# 561.49. Release builds

Release có thể dùng aggressive allocation.

---

# 561.50. Register pressure

Cost model phải theo dõi:

```text id="q6x3k8"
live registers
register classes
spill risk
```

---

# 561.51. Register coalescing

Nếu:

```text id="j8v4m2"
v1 = v2
```

compiler có thể assign cùng register và loại move.

---

# 561.52. Aggressive coalescing

Không được làm tăng spill cost vượt profitability threshold.

---

# 561.53. Spill

Nếu không đủ registers:

```text id="c2m7x9"
virtual register
→ stack slot
```

---

# 561.54. Spill slot

```text id="r8p3v6"
StackSlot {
    id
    size
    alignment
    lifetime
}
```

---

# 561.55. Spill/reload

```text id="m4x8q1"
store v0 → [stack]
...
load [stack] → v0
```

---

# 561.56. Spill placement

Compiler nên spill gần các điểm áp lực register thay vì spill toàn bộ lifetime.

---

# 561.57. Live-range splitting

Một live range dài có thể split thành:

```text id="v7n2c5"
v0a
v0b
v0c
```

---

# 561.58. Rematerialization

Giá trị rẻ có thể recompute thay vì load từ stack.

Ví dụ:

```text id="p9q4m1"
constant
address
small immediate
```

---

# 561.59. Spill cost

Cost model:

```text id="x5k8v2"
load/store latency
memory pressure
loop frequency
register pressure
```

---

# 561.60. Register allocation correctness

Sau allocation:

```text id="h3m7q9"
no illegal overlap
no missing register
no unsatisfied constraints
```

---

# 561.61. Calling convention lowering

`421` cung cấp:

```text id="n8v2c4"
argument registers
return registers
stack arguments
callee saved
caller saved
alignment
varargs
```

---

# 561.62. Call lowering

```text id="j5q9x3"
MIR Call
 ↓
ABI argument assignment
 ↓
Machine Call
```

---

# 561.63. Struct return

Phải support:

```text id="v6m2k8"
register return
sret hidden pointer
multi-register return
```

---

# 561.64. Variadic calls

Backend phải emit ABI-compatible varargs setup.

---

# 561.65. Function pointer calls

Indirect call phải preserve target ABI.

---

# 561.66. Tail call

Tail call chỉ được emit khi:

- argument layout phù hợp;
- stack state phù hợp;
- ABI cho phép;
- return convention phù hợp.

---

# 561.67. Tail-call optimization

Nếu không đủ điều kiện:

```text id="x2q7m5"
ordinary call + return
```

---

# 561.68. Stack frame

```text id="c8m4v1"
StackFrame {
    size
    alignment
    locals[]
    spills[]
    outgoing_args
    saved_regs[]
}
```

---

# 561.69. Stack slots

Stack slot layout phải respect alignment.

---

# 561.70. Dynamic stack allocation

Axiom phải hỗ trợ explicit dynamic stack allocation nếu language/runtime API yêu cầu.

---

# 561.71. Stack probing

Target có stack-probing requirements phải được support.

---

# 561.72. Stack clash protection

Optional hardened mode có thể insert probes.

---

# 561.73. Red zone

SysV-like targets có thể sử dụng red zone khi ABI cho phép.

---

# 561.74. Shadow space

Win64 ABI phải support shadow space.

---

# 561.75. Stack alignment

Mỗi call site phải satisfy ABI-required alignment.

---

# 561.76. Prologue

Prologue chịu trách nhiệm:

- stack frame;
- callee-saved registers;
- frame pointer nếu cần;
- security metadata;
- stack probing.

---

# 561.77. Epilogue

Epilogue phải reverse resource/frame state tương ứng.

---

# 561.78. Multiple epilogues

Có thể có nhiều exit paths.

---

# 561.79. Epilogue sharing

Có thể merge epilogues nếu beneficial.

---

# 561.80. Shrink wrapping

Callee-saved registers/frame setup chỉ có thể được tạo ở paths thực sự cần chúng.

---

# 561.81. Frame pointer omission

Cho phép bỏ frame pointer khi debug/unwind/target policy cho phép.

---

# 561.82. Unwind contract

Nếu unwind enabled, prologue/epilogue phải có unwind metadata tương ứng.

---

# 561.83. Debug contract

Machine instruction phải preserve source location mapping ở mức có thể.

---

# 561.84. Instruction scheduling

Scheduling thay đổi thứ tự machine instructions trong phạm vi dependence legality.

---

# 561.85. Dependency DAG

```text id="q3m8v6"
I1 ──→ I3
I2 ──→ I3
I3 ──→ I4
```

---

# 561.86. Scheduling constraints

Phải respect:

```text id="f7x2n9"
data dependency
memory dependency
control dependency
register dependency
resource dependency
```

---

# 561.87. Latency

Mỗi instruction có target-specific latency model.

---

# 561.88. Throughput

Scheduler cũng xét reciprocal throughput.

---

# 561.89. Resource model

Ví dụ concept:

```text id="m6q1v8"
ALU
Load
Store
Branch
Vector
FP
```

---

# 561.90. CPU tuning

Target CPU tuning có thể thay đổi scheduling/cost nhưng không thay đổi semantics.

---

# 561.91. Generic schedule

Nếu CPU model không đủ chi tiết, backend dùng conservative schedule.

---

# 561.92. Instruction grouping

Scheduler có thể tận dụng instruction-level parallelism.

---

# 561.93. Load/store scheduling

Memory operations chỉ reorder khi memory model/alias proof cho phép.

---

# 561.94. Branch scheduling

Không được move instruction qua branch nếu có side effect không phù hợp.

---

# 561.95. Speculative machine execution

Pure instruction có thể được schedule sớm nếu không thay đổi observable trap/panic semantics.

---

# 561.96. Trap-sensitive instructions

Instruction có thể trap/panic phải được đánh dấu.

---

# 561.97. Machine effects

```text id="k4x8m2"
MayTrap
ReadsMemory
WritesMemory
Atomic
Volatile
Call
Barrier
```

---

# 561.98. Scheduling barrier

Barrier không được cross nếu semantics cấm.

---

# 561.99. Post-RA scheduling

Có thể schedule sau register allocation nhưng phải respect physical-register dependencies.

---

# 561.100. Pre-RA scheduling

Có thể schedule trước allocation để giảm pressure hoặc expose ILP.

---

# 561.101. Two-stage scheduling

Production pipeline:

```text id="w8q2m5"
Pre-RA
 ↓
Register Allocation
 ↓
Post-RA
```

---

# 561.102. Machine peephole

Peephole optimizer xử lý local instruction sequences.

---

# 561.103. Example

```text id="j5m9v3"
mov rax, 0
```

có thể thay bằng target-specific zero idiom nếu semantics/cost cho phép.

---

# 561.104. Redundant move

```text id="x2k7q8"
mov rax, rax
```

→ remove.

---

# 561.105. Compare/branch fusion

Target có thể fuse compare + branch nếu ISA hỗ trợ trực tiếp hoặc microarchitectural model cho phép.

---

# 561.106. Addressing-mode formation

```text id="n4q8m1"
add base + index * scale + offset
```

có thể combine thành một addressing mode nếu target hỗ trợ.

---

# 561.107. Addressing mode legality

Phải respect:

- base/index register class;
- scale;
- displacement size;
- segment/TLS mode.

---

# 561.108. LEA-like operations

Address computation có thể dùng arithmetic/address instruction khi legal và profitable.

---

# 561.109. Constant materialization

Compiler phải chọn sequence phù hợp:

```text id="v7x3m5"
small immediate
large immediate
constant pool
literal pool
```

---

# 561.110. Constant pool

Constants lớn có thể đặt vào read-only section.

---

# 561.111. Literal pools

AArch64-like target có thể cần literal pools với range constraints.

---

# 561.112. Pool placement

Pool placement phải ensure every reference reachable.

---

# 561.113. Branch encoding

Backend ban đầu có thể tạo abstract branch:

```text id="q9m2v6"
Branch target
```

rồi relaxation chọn encoding cuối.

---

# 561.114. Short branch

Nếu displacement fit:

```text id="c4x8n1"
short encoding
```

---

# 561.115. Long branch

Nếu không fit:

```text id="m7q3v5"
long encoding
```

---

# 561.116. Branch relaxation

Relaxation phải lặp đến stable layout.

---

# 561.117. Branch islands / veneers

Targets có range-limited branch phải hỗ trợ thunk/veneer.

---

# 561.118. Literal range relaxation

Tương tự với literal references.

---

# 561.119. PIC/PIE

Machine lowering phải support position-independent addressing.

---

# 561.120. GOT

External/dynamic symbols có thể dùng GOT khi target ABI yêu cầu.

---

# 561.121. PLT

Dynamic calls có thể use PLT hoặc direct mechanism phù hợp platform.

---

# 561.122. TLS

TLS access phải lower theo target TLS model:

```text id="f5m8q2"
local-exec
initial-exec
local-dynamic
general-dynamic
```

nếu platform hỗ trợ.

---

# 561.123. Relocations

Machine backend tạo relocation/fixup metadata thay vì hard-code final address.

---

# 561.124. Fixup

```text id="k3x7m9"
Fixup {
    offset
    kind
    symbol
    addend
    width
}
```

---

# 561.125. Machine encoder boundary

`561` không trực tiếp serialize ELF/PE/Mach-O.

Pipeline:

```text id="q8m4v2"
Machine IR
 ↓
EncodedInstruction
 ↓
Object writer
```

---

# 561.126. Integration với 420

`420` chịu trách nhiệm:

- machine encoding;
- object format;
- linker.

`561` chịu trách nhiệm tạo input chính xác cho encoder.

---

# 561.127. Instruction encoding validation

Encoder phải kiểm tra:

```text id="x5n8q1"
opcode
operand class
immediate range
register encoding
prefix/extension
```

---

# 561.128. Invalid encoding

Không được silently truncate.

---

# 561.129. Immediate legalization

Nếu immediate không fit encoding:

```text id="m2q7v5"
materialize constant
```

thay vì truncate.

---

# 561.130. Register allocation before encoding

Không encode virtual registers.

---

# 561.131. Machine verifier

Trước encoding:

```text id="c9x3m6"
verify_machine_function()
```

---

# 561.132. Machine verifier checks

Ít nhất:

```text id="n7v2k4"
CFG
register classes
physical register legality
constraints
stack frame
ABI
memory operands
branch targets
instruction legality
```

---

# 561.133. Post-RA verifier

Sau register allocation phải chạy verifier.

---

# 561.134. Post-frame verifier

Sau prologue/epilogue cũng phải verify.

---

# 561.135. Pre-encode verifier

Machine instruction phải legal trước encode.

---

# 561.136. Encoder round-trip

`552` có thể:

```text id="j4m8q2"
MachineInstruction
 → encode
 → decode
 → compare
```

---

# 561.137. Decode equivalence

Decoded instruction phải semantic-equivalent với encoded instruction.

---

# 561.138. Native execution differential test

Critical backend changes có thể:

```text id="x6q1m9"
reference execution
vs
generated execution
```

---

# 561.139. Register allocator validation

Randomized machine IR tests phải tìm:

- overlapping live ranges;
- invalid constraints;
- missing spills;
- corrupted callee-saved registers.

---

# 561.140. Stack frame validation

Compiler phải verify:

```text id="p5m9x3"
alignment
slot bounds
call alignment
save/restore symmetry
```

---

# 561.141. ABI validation

Golden tests cho:

```text id="v8q2m6"
scalar
struct
vector
float
large return
variadic
callback
```

---

# 561.142. Cross-platform ABI

Tối thiểu:

```text id="m3x7k1"
SysV x86-64
Win64 x86-64
AAPCS64
Apple AArch64
WASM
```

---

# 561.143. Debug preservation

Machine instruction provenance:

```text id="q6n2v8"
machine instruction
 ← MIR instruction
 ← HIR
 ← source span
```

---

# 561.144. Optimized-out values

Debug info phải biểu diễn honest state:

```text id="w4m8q1"
optimized out
```

không fabricate variable location.

---

# 561.145. Unwind preservation

Prologue/epilogue transformation phải update unwind info.

---

# 561.146. Security hardening

Machine backend có thể hỗ trợ optional:

- stack canary;
- CFI;
- shadow stack;
- branch protection;
- CET/PAC-like features.

---

# 561.147. Hardening is policy

Không được tự động bật instruction/hardening yêu cầu target capability ngoài configuration.

---

# 561.148. Stack canary

Nếu bật, prologue/epilogue phải preserve ABI/runtime contract.

---

# 561.149. CFI

Indirect call targets có thể được instrument nếu security profile yêu cầu.

---

# 561.150. Shadow stack

Target-supported shadow stack phải integrate với ABI/unwind/security metadata.

---

# 561.151. Instruction fusion

Microarchitectural fusion chỉ là profitability optimization.

---

# 561.152. CPU-specific tuning

`-mtune`-like behavior không được thay đổi language semantics.

---

# 561.153. Size optimization

Machine backend có thể chọn:

```text id="n8q3m5"
short encoding
smaller instruction
```

khi semantics equivalent.

---

# 561.154. Speed optimization

Có thể chọn sequence dài hơn nếu throughput/latency tốt hơn.

---

# 561.155. Multi-objective

Codegen nhận policy:

```text id="k2x7v4"
speed
size
compile_time
power
```

---

# 561.156. Machine cost model

Cost model phải phân biệt:

```text id="f9m3q6"
latency
throughput
code size
register pressure
uop pressure
memory pressure
```

khi model target hỗ trợ.

---

# 561.157. No universal CPU model

Nếu target information không đủ:

```text id="q4v8n2"
use conservative defaults
```

---

# 561.158. Backend extensibility

ISA backend interface:

```text id="m7x2k5"
TargetBackend {
    legalize()
    select()
    allocate()
    schedule()
    lower_frame()
    relax()
    encode()
}
```

---

# 561.159. Backend independence

Generic optimizer không được phụ thuộc vào implementation details của backend.

---

# 561.160. Backend-specific optimization

Target backend có thể thêm machine passes sau generic optimization.

---

# 561.161. Machine pass manager

Machine passes cũng dùng:

```text id="v5q9m1"
Pass
Analysis
Invalidation
Verification
Provenance
```

tương tự `560`.

---

# 561.162. Machine analysis

Tối thiểu:

```text id="x8m3q7"
LiveIntervals
RegisterPressure
MachineDominatorTree
BlockFrequency
BranchProbability
FrameInfo
Alias/Memory dependencies
```

---

# 561.163. Machine pass invalidation

Pass phải khai báo analysis preservation.

---

# 561.164. Machine-level fixpoint

Peephole/combining có thể iterate nhưng phải bounded.

---

# 561.165. Machine oscillation

Phải ngăn:

```text id="c6m1q8"
T1 → T2 → T1
```

---

# 561.166. Backend cache

Machine-level compilation result có thể cache theo:

```text id="n2x7v4"
optimized MIR fingerprint
target
features
ABI
codegen profile
compiler version
```

---

# 561.167. Cache correctness

Cache hit phải equivalent với fresh codegen.

---

# 561.168. Parallel codegen

Functions độc lập có thể codegen song song.

---

# 561.169. Deterministic codegen

Function ordering trong worker queue không được thay đổi semantic/native result.

---

# 561.170. Object section ordering

Deterministic section/symbol ordering thuộc `420`, nhưng machine backend phải cung cấp stable identities.

---

# 561.171. Linker relaxation

Machine backend phải cho linker đủ relocation information để linker relaxation hoạt động khi supported.

---

# 561.172. Link-time code generation

Axiom có thể giữ một machine-level representation đủ compact cho LTO/thin-LTO.

---

# 561.173. Whole-program visibility

Machine backend nhận visibility:

```text id="m4q8x2"
local
hidden
protected
public
weak
extern
```

tùy object format.

---

# 561.174. Symbol address observability

Không được merge/reorder code nếu address identity/ABI yêu cầu preserve.

---

# 561.175. Function sections

Mỗi function có thể nằm trong section riêng để linker GC/dead stripping.

---

# 561.176. COMDAT/weak semantics

Backend phải emit metadata cần thiết cho linker duplicate resolution.

---

# 561.177. TLS symbols

TLS symbol references phải giữ đúng relocation model.

---

# 561.178. Exception/unwind tables

Machine layout phải phối hợp với unwind section generation.

---

# 561.179. Panic paths

Panic paths có thể cold-section nhưng phải remain reachable theo semantics.

---

# 561.180. Native startup

Entry point và startup sequence thuộc runtime/object/linker nhưng codegen phải emit đúng ABI cho startup functions.

---

# 561.181. Freestanding

Freestanding codegen không được tự động tạo libc dependency.

---

# 561.182. Runtime helper policy

Nếu generated code cần helper:

```text id="q9m2x5"
Axiom runtime helper
```

phải được resolve explicit.

---

# 561.183. No hidden runtime dependency

Machine backend không được tự động gọi external C++ runtime.

---

# 561.184. Builtin expansion

Compiler builtins có thể lower trực tiếp thành machine instruction hoặc Axiom runtime helper.

---

# 561.185. Atomics

Atomic lowering phải map chính xác:

```text id="v7x4m1"
Relaxed
Acquire
Release
AcqRel
SeqCst
```

theo `424`.

---

# 561.186. Atomic width

Target phải hỗ trợ width tương ứng hoặc compiler phải lower tới runtime/library primitive nếu semantics cho phép.

---

# 561.187. Atomic fallback

Fallback phải preserve lock-free/non-lock-free contract nếu API expose property đó.

---

# 561.188. SIMD

Vector types phải lower đúng ABI.

---

# 561.189. Vector ABI

Function argument/return vector phải tuân target ABI.

---

# 561.190. GPU separation

GPU codegen không được giả định CPU machine backend.

GPU có backend pipeline riêng.

---

# 561.191. WASM

WASM backend dùng Machine IR tương thích với WASM instruction model nhưng không ép WASM vào CPU register allocator.

---

# 561.192. Target backend family

```text id="x5m8q3"
CPUBackend
GPUBackend
WASMBackend
```

có thể dùng shared generic lowering nhưng target-specific final stages.

---

# 561.193. AArch64

Backend phải hỗ trợ:

- fixed-width instruction encoding;
- register pairs;
- FP/SIMD;
- conditional branches;
- literal pools;
- relocation;
- ABI.

---

# 561.194. x86-64

Backend phải hỗ trợ:

- variable-length encoding;
- prefixes;
- REX/VEX/EVEX;
- addressing modes;
- flags;
- complex register constraints;
- short/near branches.

---

# 561.195. WASM

Backend phải hỗ trợ:

- stack-machine semantics;
- structured control flow;
- locals;
- globals;
- memory;
- table/function references;
- WASM ABI.

---

# 561.196. Machine correctness evidence

Mỗi native function có thể có:

```text id="j8q4m2"
MachineCodeEvidence {
    input_mir_hash
    machine_ir_hash
    target
    transformations[]
    encoding_hash
    validation[]
}
```

---

# 561.197. Integration với 552

Critical chain:

```text id="p3x7m9"
Optimized MIR
      ↓
Machine IR
      ↓
Machine transforms
      ↓
Encoded bytes
      ↓
Decode/semantic validation
```

---

# 561.198. Backend forensic mode

Khi wrong-code xuất hiện:

```text id="v2m8q5"
disable instruction selection
disable machine pass
disable register allocation optimization
disable scheduling
disable peephole
```

để isolate lỗi.

---

# 561.199. Native lowering contract

```text id="c7q3m1"
Language Semantics
       ↓
Optimized MIR
       ↓
Machine IR
       ↓
Physical Registers / Stack
       ↓
Machine Instructions
       ↓
Encoded Bytes
```

Mỗi bước phải có verifier và provenance đủ để truy nguyên.

---

# 561.200. HARD INVARIANTS

1. Machine IR phải có stable identity.
2. Machine IR không được dùng memory address làm semantic identity.
3. Mỗi MachineFunction phải có CFG hợp lệ.
4. Mỗi MachineBlock phải có terminator hợp lệ.
5. Machine instruction phải có opcode hợp lệ.
6. Operand phải thuộc operand class hợp lệ.
7. Virtual register phải thuộc register class đúng.
8. Physical register phải tồn tại trên target.
9. Register aliasing phải được model chính xác.
10. Instruction selection không được thay đổi semantics.
11. Pattern selection phải kiểm tra legality.
12. Target feature phải được kiểm tra trước khi emit instruction.
13. Không được emit unsupported instruction.
14. Không được silently truncate immediate.
15. Immediate overflow phải được legalize hoặc báo lỗi.
16. Legalization phải preserve semantics.
17. Expansion sequence phải semantic-equivalent với source operation.
18. Libcall phải explicit.
19. Libcall không được tự động tạo dependency vào compiler bên thứ ba.
20. Runtime helper phải thuộc Axiom runtime contract hoặc dependency explicit.
21. Virtual registers không được encode trực tiếp.
22. Register allocator phải resolve toàn bộ virtual registers.
23. Register class constraint phải được satisfy.
24. Fixed-register constraint phải được satisfy.
25. Tied operands phải được satisfy.
26. Early-clobber constraints phải được respect.
27. Implicit register defs/uses phải được model.
28. Register alias overlap phải được detect.
29. Hai interfering live ranges không được share physical register.
30. Spill slot phải có size hợp lệ.
31. Spill slot phải có alignment hợp lệ.
32. Spill/reload phải preserve value.
33. Live-range splitting phải preserve liveness semantics.
34. Rematerialization phải preserve exact value semantics.
35. Register coalescing không được tạo interference.
36. Register allocation phải preserve calling convention.
37. Caller-saved registers phải được xử lý đúng.
38. Callee-saved registers phải được preserve đúng.
39. Return registers phải đúng ABI.
40. Argument registers phải đúng ABI.
41. Stack arguments phải đúng ABI.
42. Hidden sret parameter phải đúng ABI.
43. Variadic ABI phải đúng.
44. Function-pointer calls phải đúng ABI.
45. Tail calls chỉ được emit khi ABI conditions satisfy.
46. Stack frame phải satisfy alignment.
47. Call-site stack alignment phải satisfy ABI.
48. Red-zone usage chỉ được dùng khi ABI cho phép.
49. Shadow-space requirements phải được respect.
50. Dynamic stack allocation phải preserve alignment.
51. Stack probing policy phải được respect.
52. Prologue phải preserve required registers.
53. Epilogue phải restore required registers.
54. Multiple exits phải có valid epilogues.
55. Shrink wrapping không được phá unwind semantics.
56. Frame-pointer omission không được phá configured debug/unwind requirements.
57. Unwind metadata phải khớp machine frame.
58. Debug metadata phải map machine code honestly.
59. Optimized-out values không được fabricate.
60. Machine scheduling phải preserve data dependencies.
61. Machine scheduling phải preserve memory dependencies.
62. Machine scheduling phải preserve control dependencies.
63. Machine scheduling phải preserve register dependencies.
64. Atomic ordering phải được preserve.
65. Volatile ordering phải được preserve.
66. Effectful operations không được schedule trái semantics.
67. Trap-sensitive operations phải được model.
68. Speculative execution trong compiler phải preserve observable trap semantics.
69. Scheduler không được tạo illegal dependency cycle.
70. Latency model không được thay đổi legality.
71. Throughput model không được thay đổi semantics.
72. CPU tuning không được thay đổi language semantics.
73. Machine peephole phải prove equivalence.
74. Redundant moves có thể remove khi register semantics tương đương.
75. Addressing-mode formation phải preserve effective address.
76. Constant materialization phải preserve exact value.
77. Constant pool reference phải remain reachable.
78. Literal pool placement phải satisfy range.
79. Branch target phải hợp lệ.
80. Branch displacement phải fit selected encoding.
81. Branch relaxation phải terminate.
82. Relaxation phải preserve branch target semantics.
83. Veneers/thunks phải preserve ABI.
84. PIC/PIE lowering phải preserve relocation semantics.
85. GOT references phải đúng relocation model.
86. PLT/dynamic-call references phải đúng ABI.
87. TLS lowering phải đúng TLS model.
88. Relocation metadata phải match machine instruction.
89. Fixup offsets phải nằm trong encoded instruction.
90. Fixup width phải đúng encoding.
91. Encoder phải reject invalid operand combinations.
92. Machine verifier phải chạy trước final encoding.
93. Post-RA verifier phải chạy.
94. Frame verifier phải chạy.
95. Pre-encode verifier phải chạy.
96. Encoded instruction phải round-trip validate được khi decoder có sẵn.
97. Decode result phải semantic-equivalent với source machine instruction.
98. Wrong encoding phải được phát hiện bởi validation.
99. Machine-level cache hit phải equivalent với fresh codegen.
100. Codegen cache identity phải include target.
101. Codegen cache identity phải include ABI.
102. Codegen cache identity phải include target features.
103. Codegen cache identity phải include optimization profile.
104. Codegen cache identity phải include relevant compiler version.
105. Parallel codegen không được thay đổi semantics.
106. Worker order không được thay đổi semantics.
107. Machine function output phải deterministic khi deterministic mode bật.
108. Object ordering không được phụ thuộc worker scheduling.
109. Function section identity phải stable.
110. Symbol identity phải stable.
111. Visibility phải được preserve.
112. Public ABI không được thay đổi bởi internal optimization.
113. Symbol address observability phải được respect.
114. ICF/merging chỉ được phép khi address semantics cho phép.
115. COMDAT/weak semantics phải preserve.
116. Exception/unwind sections phải remain consistent.
117. Panic paths phải remain semantically reachable.
118. Cold splitting không được lose panic/unwind behavior.
119. Security hardening phải là explicit policy.
120. Security hardening không được assume unsupported CPU.
121. Stack canary implementation phải ABI-correct.
122. CFI implementation phải preserve valid indirect calls.
123. Shadow-stack implementation phải preserve call/return semantics.
124. Constant-time policy phải survive machine optimization.
125. Realtime restrictions phải survive machine lowering.
126. `no_alloc` codegen không được introduce allocation.
127. `no_block` codegen không được introduce blocking runtime call.
128. `no_panic` codegen không được introduce new panic path.
129. Atomic operations phải preserve memory order.
130. Atomic width phải preserve API semantics.
131. SIMD lowering phải preserve vector semantics.
132. SIMD ABI phải be correct.
133. Vector register classes phải be correct.
134. Wide integer lowering phải preserve exact arithmetic semantics.
135. Division lowering phải preserve signedness.
136. Division edge cases phải preserve semantics.
137. Boolean lowering phải preserve logical semantics.
138. Compare lowering phải preserve signed/unsigned semantics.
139. Condition-code dependencies phải be explicit.
140. Flag clobbers phải be modeled.
141. Instruction selection phải account for implicit flags.
142. Register allocation phải account for implicit register definitions.
143. Scheduler phải account for implicit register dependencies.
144. Machine transformations phải retain provenance.
145. Machine instruction phải retain source mapping where possible.
146. Machine transformation must be traceable to `560`.
147. Machine validation must integrate with `552`.
148. Encoder validation must integrate with `420`.
149. ABI lowering must integrate with `421`.
150. Memory semantics must integrate with `422/423/445`.
151. Atomic semantics must integrate with `424`.
152. Debug/unwind must integrate with `440`.
153. Optimization evidence must integrate with `553/560`.
154. Query/cache identity must integrate with `554/559`.
155. Parallel codegen must integrate with `558`.
156. Incremental compilation must reuse machine results only when identity is valid.
157. Daemon must not alter codegen semantics.
158. Remote cache must not bypass machine validation where required.
159. Corrupt machine cache must be rejected.
160. Invalid target metadata must fail closed.
161. Unsupported ISA must produce diagnostic, not invalid bytes.
162. Unsupported ABI must produce diagnostic, not guessed calling convention.
163. Unsupported relocation must produce diagnostic.
164. Unsupported instruction encoding must produce diagnostic.
165. Register allocation failure must produce compiler diagnostic.
166. Stack-frame overflow beyond representable target limits must be diagnosed.
167. Branch range overflow must trigger relaxation or diagnostic.
168. Literal range overflow must trigger relocation/pool handling or diagnostic.
169. Machine fixpoint passes must be bounded.
170. Machine optimization oscillation must be detectable.
171. Machine pass dependencies must be explicit.
172. Machine analysis invalidation must be explicit.
173. Stale machine analysis must never be consumed.
174. Machine pass cache must be identity-bound.
175. Machine pass results must be deterministic.
176. Machine pass ordering must be deterministic under fixed pipeline.
177. Cost model must never override legality.
178. Profitability may reject a legal transformation.
179. Invalid transformation must never be committed.
180. Critical machine transformations must support rollback.
181. Backend forensic mode must isolate machine passes.
182. Register allocator bugs must be reproducible from machine IR.
183. Encoder bugs must be reproducible from isolated instruction records.
184. Linker relocation bugs must be distinguishable from codegen bugs.
185. Wrong-code reports must retain machine IR provenance.
186. Native execution differential tests must distinguish source UB from compiler miscompile.
187. Machine backend must support deterministic test seeds.
188. Fuzzed machine IR must not crash compiler.
189. Invalid machine IR must be rejected by verifier.
190. Backend must support serial fallback.
191. Serial and parallel codegen must be equivalent.
192. Different register allocator strategies must preserve semantics.
193. Different scheduler strategies must preserve semantics.
194. Different target tuning models must preserve semantics.
195. Different cache states must preserve semantics.
196. Different optimization budgets must preserve semantics.
197. Native artifacts must remain ABI-correct.
198. Native artifacts must remain object-format-correct.
199. Machine encoding must remain byte-correct.
200. **Final invariant:** từ `Optimized MIR` đến `Encoded Bytes`, Axiom phải có một chuỗi lowering **deterministic, ABI-correct, target-correct, verifiable và có provenance**, trong đó register allocation, scheduling, peephole, relaxation, caching và parallelism chỉ thay đổi cách tạo machine code chứ không được thay đổi semantics của chương trình.

**BOOTSTRAP-561: LOCKED.**

---

# NEXT — BOOTSTRAP-562

## COMPILER TARGET BACKEND 4.0 — X86-64, AARCH64, WASM, TARGET DESCRIPTION, ISA TABLEGEN, CPU FEATURES & MULTI-TARGET BACKEND VALIDATION

`561` đã khóa **pipeline codegen chung**. `562` sẽ khóa cách Axiom mô tả và triển khai từng ISA/target mà **không biến compiler thành một đống backend hard-code rời rạc**.

Kiến trúc dự kiến:

```text id="s4m8x2"
                       Axiom Target Model
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
              x86-64       AArch64       WASM
                 │            │            │
          ┌──────┴──────┐ ┌───┴────┐   ┌───┴────┐
          ▼             ▼ ▼        ▼   ▼        ▼
         ISA          ABI       ISA       ABI
         Spec         Spec      Spec      Spec
          │             │         │         │
          └─────────────┼─────────┼─────────┘
                        ▼
                  Target Backend
                        │
            ┌───────────┼───────────┐
            ▼           ▼           ▼
        Selection   Scheduling   Encoding
            │           │           │
            └───────────┼───────────┘
                        ▼
                  Validation
```

`562` sẽ đặc biệt khóa:

- declarative ISA description;
- instruction definitions;
- register definitions;
- register aliases;
- instruction operands;
- encoding tables;
- decoding tables;
- instruction legality;
- CPU feature hierarchy;
- feature implication/conflict;
- `-march`/`-mcpu`/`-mtune` tương đương của Axiom;
- x86-64 baseline + SSE/AVX/AVX2/AVX-512 và các extension liên quan;
- AArch64 base + SIMD/crypto/SVE/SVE2 khi target hỗ trợ;
- WASM MVP + SIMD + threads + bulk memory + reference types + exceptions/features theo target;
- ABI/ISA separation;
- target triples;
- CPU dispatch;
- cross-target testing;
- instruction encoder/decoder generation;
- differential validation với `552`;
- cách thêm **ISA mới** mà không phải sửa toàn bộ compiler core.

**NEXT TASK: BOOTSTRAP-562.**