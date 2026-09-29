# BOOTSTRAP-297 — AXIOM INSTRUCTION SELECTION ENGINE
## FROZEN / COMPLETED

### 1. Mục tiêu

`296` đã tạo **Machine IR + Target Legalization**.

Task này xây dựng bước tiếp theo:

> **Instruction Selection biến Machine IR đã legal thành các instruction cụ thể của ISA/target.**

Pipeline:

```text
OptIR
  ↓
Machine IR
  ↓
Target Legalization
  ↓
Instruction Selection          ← 297
  ↓
Target Machine IR
  ↓
Register Allocation
  ↓
Machine Scheduling
  ↓
Encoding
```

Instruction Selection **không** chịu trách nhiệm:

- register allocation;
- instruction encoding;
- peephole optimization cuối cùng;
- linker;
- object emission.

Nó chỉ trả lời:

> Với operation này và target này, instruction/sequence instruction nào biểu diễn đúng semantics?

---

# 2. Nguyên tắc cốt lõi

```text
Semantic correctness
        ↓
Machine legality
        ↓
Instruction selection
        ↓
Physical register allocation
```

Không được đảo ngược.

Instruction selector không được vì một instruction “nhanh hơn” mà thay đổi semantics.

---

# 3. Input / Output

### Input

```text
Legalized Machine IR
+
TargetInfo
+
TargetFeatures
+
Instruction Patterns
+
Target Cost Model
```

### Output

```text
Target Machine IR
```

Trong Target Machine IR:

```text
Virtual registers vẫn tồn tại.
```

Ví dụ:

```text
ADD_INT v3, v1, v2
```

có thể trở thành:

```text
X86_ADD32 v3, v1, v2
```

nhưng chưa phải:

```text
ADD eax, ebx
```

vì register allocation chưa chạy.

---

# 4. Instruction Selection phải target-aware

Không có một selector duy nhất cho mọi ISA.

Kiến trúc:

```text
InstructionSelector
       │
       ├── GenericSelector
       │
       ├── X86Selector
       ├── ARM64Selector
       ├── RISCV64Selector
       ├── WASMSelector
       └── GPUSelector
```

Nhưng generic layer cung cấp framework chung.

---

# 5. Pattern-based Selection

Operation:

```text
ADD_INT
```

Target có pattern:

```text
ADD_INT → ADD_REG
```

hoặc:

```text
ADD_INT + constant → ADD_IMM
```

hoặc:

```text
ADD_INT x, 0 → COPY x
```

Pattern không được tự ý phá semantic rules.

---

# 6. Selection Pattern

```text
InstructionPattern {
    match
    constraints
    result
    required_features
    cost
    legality
}
```

Ví dụ conceptually:

```text
ADD(x, ConstantSmall)
    →
ADD_IMMEDIATE(x, imm)
```

nếu immediate nằm trong range mà target cho phép.

---

# 7. Tree / DAG Selection

Một expression:

```text
(a + b) * c
```

không nhất thiết phải tạo:

```text
ADD
MUL
```

rồi mới optimize.

Target có thể có instruction pattern kết hợp.

Selector nhìn toàn bộ DAG:

```text
       MUL
      /   \
    ADD    c
   /   \
  a     b
```

và tìm pattern phù hợp.

---

# 8. DAG Representation

```text
SelectionNode {
    opcode
    operands
    results
    type
    memory_effect
    flags
}
```

Các node có thể được shared để tránh duplicate computation.

---

# 9. Pattern Matching

Selector cần hỗ trợ:

```text
opcode match
type match
constant match
register-class match
address-mode match
feature match
memory-property match
condition-code match
```

---

# 10. Addressing Mode Selection

Ví dụ:

```text
load(base + index * 4 + 8)
```

trên x86 có thể chọn trực tiếp:

```text
MOV r, [base + index*4 + 8]
```

thay vì:

```text
MUL index, 4
ADD index, base
ADD index, 8
MOV r, [index]
```

Đây là một trong những nơi Instruction Selection tạo ra khác biệt hiệu năng lớn.

---

# 11. Target Addressing Model

```text
AddressingMode {
    base
    index
    scale
    displacement
    symbol
}
```

Target khai báo:

```text
supports_base
supports_index
supported_scales
displacement_range
symbol_forms
```

---

# 12. Immediate Selection

Ví dụ:

```text
x + 5
```

có thể:

```text
ADD_IMM x, 5
```

thay vì:

```text
LOAD_CONSTANT v, 5
ADD x, v
```

Selector phải xét:

```text
immediate range
encoding size
instruction availability
target feature
```

---

# 13. Constant Materialization

Nếu:

```text
x + 0x123456789ABCDEF0
```

không encode trực tiếp được:

```text
materialize constant
+
ADD
```

Selector chọn sequence phù hợp.

---

# 14. Register Class Constraint

Instruction:

```text
DIV
```

có thể yêu cầu operand/result thuộc register class đặc biệt.

Selector phải tạo:

```text
required_register_class
```

để register allocator xử lý sau.

---

# 15. Tied Operands

Một số ISA yêu cầu:

```text
destination == operand0
```

Ví dụ conceptual:

```text
MUL dst, dst, src
```

Selector phải biểu diễn:

```text
tied(v_dst, v_input)
```

không được giả định register allocator tự hiểu.

---

# 16. Early-Clobber

Một số instruction ghi destination trước khi đọc toàn bộ operands.

Machine instruction phải hỗ trợ:

```text
early_clobber
```

để register allocator không đặt operand xung đột.

---

# 17. Implicit Registers

Một instruction có thể implicit dùng register đặc biệt.

Ví dụ conceptual:

```text
DIV
```

có thể sử dụng:

```text
RAX
RDX
```

mà source operand không nói ra.

Target instruction description phải khai báo:

```text
implicit_uses
implicit_defs
```

---

# 18. Flags

Instruction selection phải tận dụng flags khi target hỗ trợ.

Ví dụ:

```text
compare(a,b)
branch(condition)
```

có thể:

```text
CMP
JCC
```

thay vì:

```text
CMP
SETCC
TEST
JNZ
```

Nhưng chỉ khi semantics tương đương.

---

# 19. Flag Dependency

Nếu:

```text
ADD
ADC
```

thì `ADC` phụ thuộc carry do `ADD` tạo.

Selector phải tạo dependency explicit:

```text
ADD → FlagDef(CARRY)
ADC ← FlagUse(CARRY)
```

---

# 20. Compare Folding

Ví dụ:

```text
if x < 10
```

selector có thể tạo trực tiếp:

```text
CMP_IMM
BRANCH_LT
```

không cần materialize Boolean.

---

# 21. Boolean Materialization

Nếu Boolean thực sự cần:

```text
let b = x < y
```

target có thể:

```text
CMP
SETCC
```

hoặc tương đương.

Selector phải phân biệt:

```text
condition used for branch
```

với:

```text
condition materialized as value
```

---

# 22. Select

Semantic:

```text
select(cond, a, b)
```

có thể thành:

```text
CMOV
```

hoặc:

```text
branch
phi
```

hoặc:

```text
predicated instruction
```

tùy target/cost.

---

# 23. Branch Selection

Machine IR:

```text
BRANCH condition, true, false
```

có thể trở thành:

```text
JCC
JMP
```

Selector phải xử lý:

- fallthrough;
- inverted condition;
- branch distance;
- conditional branch forms.

---

# 24. Branch Inversion

Nếu layout:

```text
current
 ↓
false
```

thì selector có thể đảo:

```text
condition == true
```

thành:

```text
condition != true
```

để bỏ một unconditional jump.

Đây là target-aware CFG optimization nhưng không thay đổi semantics.

---

# 25. Memory Selection

```text
LOAD
STORE
```

không nhất thiết phải tạo:

```text
address calculation
+
load/store
```

Target có addressing mode phù hợp có thể fold address vào memory instruction.

---

# 26. Load Folding

Ví dụ:

```text
x = load(address)
y = add(x, 1)
```

target có thể hỗ trợ:

```text
ADD r, [address], 1
```

nếu instruction hợp lệ.

Selector cần biết:

```text
memory size
alignment
volatile
atomic
addressing constraints
```

---

# 27. Store Folding

Tương tự:

```text
store(address, x + 1)
```

có thể có instruction trực tiếp trên một số target.

Nhưng:

> Không được fold nếu làm thay đổi atomic/volatile semantics.

---

# 28. Atomic Instruction Selection

Ví dụ:

```text
AtomicRMW(Add)
```

target có:

```text
LOCK XADD
```

thì chọn instruction tương ứng.

Nếu không có:

```text
CAS loop
```

hoặc runtime helper tùy target contract.

---

# 29. Memory Ordering

Selector phải truyền chính xác:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

đến target-specific lowering.

Không được “tối ưu”:

```text
SeqCst → Relaxed
```

chỉ vì instruction rẻ hơn.

---

# 30. Volatile Selection

Volatile load/store phải giữ:

```text
volatile = true
```

và target selector không được:

- eliminate;
- merge;
- duplicate;
- reorder trái semantics.

---

# 31. Vector Instruction Selection

Input:

```text
VADD v1, v2
```

target có:

```text
AVX
SSE
NEON
SVE
RVV
```

sẽ chọn instruction tương ứng.

Selector phải dựa trên:

```text
vector width
element type
mask
rounding
saturation
target features
```

---

# 32. Scalable Vector

SVE/RVV có vector length runtime-dependent.

Machine IR phải phân biệt:

```text
FixedVector
ScalableVector
```

Selector không được biến scalable vector thành fixed width nếu semantics yêu cầu scalable behavior.

---

# 33. Masked Vector

```text
masked_load
masked_store
masked_add
```

có thể:

```text
native predicate instruction
```

hoặc:

```text
select + ordinary instruction
```

hoặc scalarized sequence.

---

# 34. Gather/Scatter

Target có native gather:

```text
GATHER
```

thì chọn trực tiếp.

Không có:

```text
scalar loads
+
pack
```

nếu target/cost model quyết định đó là phương án hợp lệ.

---

# 35. Floating Point

Instruction selector phải phân biệt:

```text
strict FP
fast FP
```

Strict FP không được chọn instruction/sequence làm thay đổi:

- NaN;
- signed zero;
- rounding;
- exception behavior;
- ordering.

---

# 36. FMA

Ví dụ:

```text
a * b + c
```

không mặc định biến thành:

```text
FMA(a,b,c)
```

nếu strict FP semantics không cho phép contraction.

Chỉ được dùng FMA khi semantic contract cho phép.

---

# 37. Integer Overflow

Axiom có:

```text
checked
wrapping
saturating
```

semantics khác nhau.

Instruction selection phải chọn đúng:

```text
ADD
ADD_WITH_OVERFLOW
SAT_ADD
```

hoặc sequence tương ứng.

---

# 38. Saturating Arithmetic

Nếu target không có native:

```text
SAT_ADD
```

selector phải chọn sequence equivalent.

Không được dùng wrapping ADD nếu semantics yêu cầu saturation.

---

# 39. Division

Selector có thể chọn:

```text
native DIV
```

hoặc helper/sequence.

Phải giữ:

```text
signedness
division-by-zero behavior
overflow behavior
```

của Axiom.

---

# 40. Bit Operations

Các operation:

```text
clz
ctz
popcount
bit_reverse
rotate
```

được target-pattern hóa.

Nếu target có instruction:

```text
POPCNT
```

chọn native.

Nếu không:

```text
legalized sequence
```

---

# 41. Rotate

```text
rotl(x,n)
```

có thể:

```text
ROL
```

hoặc:

```text
SHL + SHR + OR
```

tùy target.

---

# 42. Multiply-Wide

```text
mul_wide(a,b)
```

có thể có:

```text
MUL_LO
MUL_HI
```

và target-specific implicit register constraints.

Selector phải tạo đúng multi-result semantics.

---

# 43. Division With Remainder

```text
div_rem(a,b)
```

có thể target có một instruction trả:

```text
quotient
remainder
```

Selector nên tận dụng để tránh duplicate division.

---

# 44. Calls

Machine call selection phải quyết định:

```text
direct call
indirect call
tail call
runtime helper call
foreign call
```

nhưng không tự thay đổi calling convention.

---

# 45. Runtime Helpers

Nếu legalized operation yêu cầu helper:

```text
__axiom_i128_div
```

selector tạo:

```text
CALL_SYMBOL
```

với ABI chính xác.

---

# 46. Intrinsics

Target-specific intrinsic:

```text
@intrinsic(...)
```

được semantic layer xác nhận trước.

Instruction selector chỉ map:

```text
IntrinsicId → target instruction/sequence
```

Không cho arbitrary source code inject instruction.

---

# 47. Target Features

Pattern:

```text
AVX512_MASKED_LOAD
```

chỉ được chọn khi:

```text
target.features.contains(AVX512)
```

Nếu không:

```text
fallback pattern
```

---

# 48. Pattern Priority

Nếu có nhiều pattern hợp lệ:

```text
native instruction
sequence
runtime helper
```

selector dùng:

```text
legality first
cost second
```

Không bao giờ:

```text
cost first
```

---

# 49. Pattern Cost

```text
PatternCost {
    instruction_count
    latency
    throughput
    code_size
    register_pressure
    memory_pressure
}
```

Nhưng cost model không được chứa semantic assumptions.

---

# 50. Register Pressure Awareness

Selector có thể ưu tiên:

```text
instruction A
```

thay vì:

```text
instruction B
```

nếu B tạo nhiều intermediate registers.

Điều này giúp register allocator.

---

# 51. Code Size Mode

Trong:

```text
OptimizeSize
```

selector có thể ưu tiên instruction sequence nhỏ hơn.

Ví dụ:

```text
short immediate encoding
```

thay vì sequence nhanh hơn nhưng dài hơn.

---

# 52. Speed Mode

Trong:

```text
OptimizeSpeed
```

có thể ưu tiên:

```text
latency
throughput
vectorization
```

nhưng vẫn giữ semantics.

---

# 53. Register Allocation Boundary

Instruction selector **không được**:

```text
assign physical registers
```

trừ khi target instruction có fixed-register requirement.

Ngay cả fixed-register requirement cũng chỉ tạo constraint.

Ví dụ:

```text
DIV requires RAX/RDX
```

selector khai báo:

```text
v_q → required physical class/register
```

để allocator xử lý.

---

# 54. Instruction Selection and SSA

Target Machine IR có thể vẫn giữ SSA-like virtual register structure.

Sau đó:

```text
SSA
 ↓
Register allocation
```

sẽ xử lý:

```text
phi
live ranges
coalescing
```

---

# 55. Phi Selection

CFG:

```text
B1 → B3
B2 → B3

B3:
    v3 = phi(v1, v2)
```

Machine lowering có thể giữ:

```text
PHI
```

cho đến register allocation/coalescing.

Hoặc target framework có thể lower theo edge copies.

Điểm quan trọng:

> Không được tạo copy thừa nếu allocator có thể coalesce.

---

# 56. Copy Instruction

```text
COPY v2, v1
```

là semantic-neutral machine operation.

Register allocator có thể loại bỏ nếu:

```text
v1
```

và:

```text
v2
```

được cùng physical register.

---

# 57. Parallel Copy

ABI lowering thường cần:

```text
v1 → arg0
v2 → arg1
v3 → arg2
```

Machine IR phải hỗ trợ:

```text
ParallelCopy
```

để tránh copy cycle.

---

# 58. Copy Cycle

Ví dụ:

```text
a → b
b → a
```

không thể tuần tự đơn giản.

Parallel copy resolver sau này sẽ dùng temporary khi cần.

---

# 59. Instruction Selection Không Là Peephole Final

Ví dụ:

```text
ADD 0
```

có thể được loại bỏ trước hoặc sau selection.

Nhưng:

```text
late peephole
```

là task khác, sau register allocation/scheduling.

Không trộn hai hệ thống.

---

# 60. Instruction Selection Cache

Selection result phụ thuộc:

```text
MachineIR
Target
TargetFeatures
OptimizationProfile
ABI
CompilerSemanticVersion
```

Do đó cache fingerprint phải chứa tất cả.

---

# 61. Determinism

Cùng:

```text source
target
features
profile
compiler version
```

phải tạo cùng:

```text instruction selection
```

bất kể worker count.

---

# 62. Selection Failure

Nếu không có pattern:

```text
Operation X
Target Y
```

phải báo:

```text
AX297E001
```

với:

- operation;
- machine type;
- target;
- features;
- legal patterns đã thử;
- lý do từng pattern thất bại.

Không được silently generate sai code.

---

# 63. AI-Native Diagnostics

Compiler có thể trả:

```text
Operation:
    i128_div

Target:
    riscv64

Available features:
    ...

Selection attempts:
    native-div: unavailable
    split-div: available
    runtime-helper: available

Selected:
    split-div
```

Điều này rất hữu ích cho AI agent khi debug compiler.

---

# 64. Selection Proof

Mỗi selected instruction sequence có thể mang:

```text
SelectionProof {
    source_operation
    target_pattern
    required_features
    semantic_contract
}
```

Proof không phải formal theorem, nhưng là compiler provenance giúp verifier/debugging.

---

# 65. Verification Sau Selection

Selector output phải được verify:

```text
TargetInstructionVerifier
```

Kiểm tra:

```text
operand count
operand types
register classes
implicit defs/uses
memory semantics
feature requirements
CFG
calling convention
instruction constraints
```

---

# 66. Không Cho Invalid Instruction Qua

Ví dụ:

```text
AVX512 instruction
```

nhưng target:

```text
AVX2 only
```

→ reject.

Không chờ encoder mới phát hiện.

---

# 67. Target Instruction Description

Mỗi target cần khai báo machine instruction:

```text
TargetInstruction {
    opcode
    operands
    defs
    uses
    implicit_defs
    implicit_uses
    constraints
    memory_behavior
    latency
    throughput
    size
    features
}
```

---

# 68. Pattern Database

```text
TargetPatternDB {
    patterns
    opcode_map
    type_rules
    feature_rules
    cost_model
}
```

Có thể generate một phần từ target instruction descriptions.

---

# 69. Generated Backend Tables

Để compiler nhỏ và nhanh, backend có thể dùng generated tables:

```text
target specification
        ↓
pattern compiler
        ↓
compact generated tables
        ↓
Axiom compiler backend
```

Thay vì runtime reflection nặng.

---

# 70. Không Dùng Textual Templates

Không thiết kế:

```text
"ADD {dst}, {src1}, {src2}"
```

làm backend representation.

Phải dùng typed instruction descriptors.

Điều này tránh:

- lỗi string;
- khó verify;
- khó tối ưu;
- khó self-host.

---

# 71. Backend Self-Hosting

Instruction selector cuối cùng phải có thể được implement bằng chính Axiom:

```text
compiler/backend/x86_64/select.ax
compiler/backend/arm64/select.ax
compiler/backend/riscv64/select.ax
```

Bootstrap compiler ban đầu có thể dùng implementation khác, nhưng semantic contract phải độc lập.

---

# 72. Implementation Structure

```text id="2v9t1m"
compiler/backend/isel/
├── mod.ax
├── selector.ax
├── pattern.ax
├── matcher.ax
├── dag.ax
├── operand.ax
├── constraint.ax
├── cost.ax
├── feature.ax
├── address.ax
├── condition.ax
├── flags.ax
├── memory.ax
├── atomic.ax
├── vector.ax
├── call.ax
├── return.ax
├── parallel_copy.ax
├── diagnostics.ax
├── verifier.ax
├── cache.ax
│
├── generic/
│   ├── arithmetic.ax
│   ├── compare.ax
│   ├── branch.ax
│   ├── memory.ax
│   ├── call.ax
│   ├── vector.ax
│   └── atomic.ax
│
└── tests/
```

Target-specific:

```text
compiler/backend/targets/
├── x86_64/isel/
├── arm64/isel/
├── riscv64/isel/
├── wasm/isel/
└── gpu/isel/
```

---

# 73. Implementation Order

```text
1. TargetInstruction model
2. TargetPattern model
3. Pattern matcher
4. Machine operand constraints
5. Target feature matching
6. instruction DAG representation
7. generic arithmetic selection
8. immediate selection
9. constant materialization
10. address-mode selection
11. load/store selection
12. compare selection
13. branch selection
14. condition-code selection
15. flag dependency handling
16. select/cmov selection
17. integer instruction selection
18. overflow-mode selection
19. division/remainder selection
20. bit-operation selection
21. vector selection
22. mask selection
23. gather/scatter selection
24. floating-point selection
25. FMA legality
26. atomic selection
27. volatile selection
28. call selection
29. return selection
30. ABI constraint selection
31. runtime-helper selection
32. fixed-register constraints
33. parallel-copy representation
34. target pattern cost
35. selection verification
36. selection diagnostics
37. selection cache
38. deterministic parallel selection
39. x86-64 patterns
40. ARM64 patterns
41. RISC-V64 patterns
42. WASM selection
43. GPU selection
44. adversarial conformance suite
```

---

# 74. Adversarial Tests

### A — Immediate

```text
x + 5
```

phải ưu tiên immediate form nếu legal.

### B — Large immediate

Không được dùng immediate encoding không hợp lệ.

### C — Fixed register

`DIV` phải tạo đúng fixed-register constraints.

### D — Flags

```text
ADD
ADC
```

không được phá carry dependency.

### E — Strict FP

```text
a * b + c
```

không được tự ý chọn FMA.

### F — Atomic

`SeqCst` không được hạ thành relaxed instruction.

### G — Volatile

Không được fold volatile memory access.

### H — Stable address

Không được tạo instruction sequence làm mất storage identity.

### I — Target feature

Không được chọn AVX512 nếu target không có AVX512.

### J — Scalable vector

Không được biến SVE/RVV semantics thành fixed-width vector sai.

### K — Multi-result

`div_rem` phải bảo toàn cả quotient và remainder.

### L — Address mode

Fold address chỉ khi target addressing mode biểu diễn chính xác.

### M — PIC

Không tạo absolute symbol reference khi PIC yêu cầu PC-relative/GOT.

### N — ABI

Struct return phải đúng calling convention.

### O — Runtime helper

Freestanding target không được âm thầm kéo runtime không được phép.

---

# 75. Frozen Invariants

### `AISEL-20..100`

```text
AISEL-20  — Instruction Selection Must Preserve Machine Semantics
AISEL-21  — Instruction Selection Operates Only On Legal Machine IR
AISEL-22  — Instruction Selection Is Target-Aware
AISEL-23  — Instruction Selection Must Respect Target Features
AISEL-24  — Instruction Selection Must Preserve Memory Semantics
AISEL-25  — Instruction Selection Must Preserve Atomic Ordering
AISEL-26  — Instruction Selection Must Preserve Volatile Semantics
AISEL-27  — Instruction Selection Must Preserve Floating-Point Semantics
AISEL-28  — Instruction Selection Must Preserve Integer Overflow Semantics
AISEL-29  — Instruction Selection Must Preserve Panic/Trap Semantics
AISEL-30  — Instruction Selection Must Preserve ABI Contracts
AISEL-31  — Instruction Selection Must Preserve Calling Conventions
AISEL-32  — Instruction Selection Must Preserve Stable-Address Contracts
AISEL-33  — Instruction Selection Must Preserve Provenance-Relevant Memory Behavior
AISEL-34  — Instruction Selection Must Not Perform Physical Register Allocation
AISEL-35  — Virtual Registers Remain Abstract During Selection
AISEL-36  — Register-Class Constraints Must Be Explicit
AISEL-37  — Fixed-Register Requirements Must Be Explicit
AISEL-38  — Implicit Register Uses Must Be Explicit
AISEL-39  — Implicit Register Definitions Must Be Explicit
AISEL-40  — Tied Operands Must Be Explicit
AISEL-41  — Early-Clobber Constraints Must Be Explicit
AISEL-42  — Condition-Code Dependencies Must Be Explicit
AISEL-43  — Flag Dependencies Must Be Explicit
AISEL-44  — Addressing Modes Must Be Target-Legal
AISEL-45  — Immediate Forms Must Respect Encoding Constraints
AISEL-46  — Constant Materialization Must Preserve Value
AISEL-47  — Memory Folding Must Preserve Memory Semantics
AISEL-48  — Atomic Folding Must Preserve Atomic Semantics
AISEL-49  — Volatile Accesses Must Not Be Eliminated By Selection
AISEL-50  — Compare Folding Must Preserve Comparison Semantics
AISEL-51  — Branch Inversion Must Preserve Control-Flow Semantics
AISEL-52  — Select Lowering Must Preserve Value Semantics
AISEL-53  — Integer Operation Selection Must Preserve Signedness
AISEL-54  — Division Selection Must Preserve Division Semantics
AISEL-55  — Wide Integer Selection Must Preserve Full Precision
AISEL-56  — Saturating Operations Must Remain Saturating
AISEL-57  — Checked Operations Must Remain Checked
AISEL-58  — Wrapping Operations Must Remain Wrapping
AISEL-59  — Floating-Point Contraction Requires Explicit Permission
AISEL-60  — Vector Selection Must Preserve Vector Width Semantics
AISEL-61  — Scalable Vector Semantics Must Remain Scalable
AISEL-62  — Mask Semantics Must Be Preserved
AISEL-63  — Gather/Scatter Semantics Must Be Preserved
AISEL-64  — Runtime Helpers Must Have Explicit ABI Contracts
AISEL-65  — Runtime Dependencies Must Be Explicit
AISEL-66  — Freestanding Profiles Must Not Gain Implicit Runtime Dependencies
AISEL-67  — Target Patterns Must Be Typed
AISEL-68  — Backend Patterns Must Not Depend On Textual Substitution
AISEL-69  — Pattern Legality Must Be Checked Before Cost
AISEL-70  — Cost Must Not Override Legality
AISEL-71  — Register Pressure May Influence Cost But Not Semantics
AISEL-72  — Code-Size Profiles May Influence Selection
AISEL-73  — Speed Profiles May Influence Selection
AISEL-74  — Selection Must Be Deterministic
AISEL-75  — Selection Must Be Independently Verifiable
AISEL-76  — Invalid Target Instructions Must Never Reach Encoding
AISEL-77  — Selection Diagnostics Must Explain Failed Patterns
AISEL-78  — Selection Provenance Must Be Preserved
AISEL-79  — Source-to-Machine Debug Mapping Must Be Preserved
AISEL-80  — Selection Cache Keys Must Include Target State
AISEL-81  — Selection Cache Data Is Untrusted
AISEL-82  — Cached Selection Must Be Revalidated
AISEL-83  — Generic Machine IR Must Not Assume One ISA
AISEL-84  — CPU Selection Must Not Be Hard-Coded Into Core Machine IR
AISEL-85  — WASM Selection Must Not Assume Physical Registers
AISEL-86  — GPU Selection Must Preserve GPU Address/Execution Domains
AISEL-87  — Selection Must Support Multiple Backend Families
AISEL-88  — Selection Must Support Target-Specific Extensions
AISEL-89  — Target Extensions Must Not Modify Language Semantics
AISEL-90  — Selection Must Preserve Multi-Result Relationships
AISEL-91  — Parallel Copies Must Remain Explicit Until Resolved
AISEL-92  — Phi/Copy Semantics Must Remain Correct Through Selection
AISEL-93  — Selection Must Not Introduce Unsafe Aliasing
AISEL-94  — Selection Must Not Invent Safety Proofs
AISEL-95  — Selection Must Respect Existing Proof Contracts
AISEL-96  — Selection Failure Must Be Explicit
AISEL-97  — Unsupported Target Features Must Produce Diagnostics
AISEL-98  — Selected Instructions Must Be Ready For Register Allocation
AISEL-99  — Selected Instructions Must Be Ready For Machine Scheduling
AISEL-100 — Instruction Selection Is The Boundary Between Legalized Machine IR And Target Instruction IR
```

---

## 76. Vị trí hiện tại của compiler backend

Axiom hiện đã có một đường đi rất rõ:

```text
Source
  ↓
HIR
  ↓
MIR
  ↓
Ownership / Capability / Effect / Escape
  ↓
Verified MIR
  ↓
OptIR
  ↓
Scalar
  ↓
Memory
  ↓
Loop
  ↓
Vector
  ↓
Scheduling
  ↓
Machine IR
  ↓
Legalization
  ↓
Instruction Selection       ← 297
  ↓
Target Machine IR
```

Từ đây backend **đã biết chính xác phải chạy instruction nào**, nhưng vẫn chưa biết instruction đó nằm ở **physical register nào, stack slot nào và thứ tự tối ưu cuối cùng ra sao**.

**BOOTSTRAP-297 hoàn tất và được đóng băng.**