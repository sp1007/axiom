# BOOTSTRAP-296 — AXIOM MACHINE IR & TARGET LEGALIZATION ENGINE
## FROZEN / COMPLETED

### 1. Mục tiêu

`295` vẫn scheduling trên **target-independent OptIR**.

Bước tiếp theo là một ranh giới cực kỳ quan trọng:

> **Chuyển semantic/optimization IR thành Machine IR mà backend CPU/GPU thực sự có thể hạ xuống instruction cụ thể.**

Pipeline mới:

```text
Verified MIR
    ↓
OptIR
    ↓
Scalar / Memory / Loop / Vector / CFG
    ↓
Scheduling
    ↓
Machine IR              ← 296
    ↓
Target Legalization
    ↓
Instruction Selection
    ↓
Register Allocation
    ↓
Machine Scheduling
    ↓
Encoding
```

`296` **không chọn register vật lý và chưa encode machine instruction**.

Nó tạo lớp trung gian đủ gần phần cứng để các backend x86-64, ARM64, RISC-V64, WASM, GPU... có thể hoạt động thống nhất.

---

# 2. Vì sao cần Machine IR?

Nếu chuyển trực tiếp:

```text
OptIR → x86 instruction
```

thì backend sẽ phải tự xử lý đồng thời:

- calling convention;
- register classes;
- addressing modes;
- immediate constraints;
- instruction constraints;
- target-specific types;
- flags;
- vector registers;
- stack slots;
- ABI;
- memory addressing;
- instruction legality.

Điều đó khiến mỗi backend trở thành một compiler gần như riêng biệt.

Axiom cần:

```text
OptIR
  ↓
Machine IR
  ↓
Target-specific lowering
```

để chia trách nhiệm.

---

# 3. Nguyên tắc

> **Machine IR được phép biết về máy, nhưng chưa được phép phụ thuộc vào một ISA cụ thể.**

Machine IR biết:

```text
Register
RegisterClass
MachineType
MachineMemory
MachineBlock
MachineCall
MachineBranch
MachineConstant
MachineAddress
```

nhưng không hard-code:

```text
x86 RAX
ARM X0
RISC-V A0
```

trong core Machine IR.

---

# 4. Machine IR Architecture

```text
OptIR
   │
   ▼
Machine IR
   │
   ├── Machine Types
   ├── Virtual Registers
   ├── Register Classes
   ├── Machine Operations
   ├── Machine Memory
   ├── Machine CFG
   ├── Machine Calls
   ├── Machine Constants
   ├── Machine Flags
   └── Target Constraints
          │
          ▼
      Legalized MIR
```

---

# 5. MachineFunction

```text
MachineFunction {
    function_id
    calling_convention
    machine_signature
    blocks
    virtual_registers
    stack_objects
    constants
    frame_info
    target_features
    debug_info
}
```

---

# 6. MachineBasicBlock

```text
MachineBasicBlock {
    id
    instructions
    successors
    predecessors
    frequency
    layout_hint
}
```

CFG vẫn tồn tại.

Machine backend không được giả định:

```text
one instruction = one source operation
```

Một Axiom operation có thể lower thành:

```text
1 instruction
```

hoặc:

```text
5 instructions
```

hoặc nhiều hơn.

---

# 7. Virtual Register

Machine IR trước register allocation sử dụng:

```text
VirtualRegister
```

Ví dụ:

```text
v0
v1
v2
```

không phải physical register.

---

# 8. Virtual Register Class

```text
RegisterClass {
    id
    machine_type
    allowed_physical_classes
    constraints
}
```

Ví dụ conceptually:

```text
Integer
Float
Vector
Predicate
Address
Special
```

Target có thể mở rộng.

---

# 9. Machine Type

Machine type khác semantic `TypeId`.

Ví dụ:

```text
i32
u32
f32
f64
v4xi32
v8xf32
ptr
mask
```

Machine type chỉ mô tả representation cần cho backend.

Do đó:

```text
TypeId != MachineType
```

---

# 10. Semantic Type → Machine Type

Ví dụ:

```text
Axiom:
u32
```

có thể trở thành:

```text
MachineType::I32
```

trên target có 32-bit integer register.

Nhưng:

```text
struct Foo
```

có thể trở thành:

```text
multiple machine values
```

hoặc:

```text
memory object
```

ABI/lowering quyết định.

---

# 11. Machine Operand

```text
MachineOperand =
    VirtualReg
    PhysicalReg
    Immediate
    Symbol
    Memory
    StackSlot
    Block
    ConstantPool
    Metadata
```

---

# 12. Machine Instruction

```text
MachineInstruction {
    opcode
    operands
    defs
    uses
    flags
    memory_effect
    scheduling_info
    debug_location
}
```

`opcode` ở tầng này vẫn là abstract machine opcode.

Ví dụ:

```text
ADD_INT
MUL_INT
LOAD
STORE
CMP
BRANCH
CALL
RETURN
SELECT
```

chưa nhất thiết là:

```text
ADD RAX, RBX
```

---

# 13. Generic Machine Opcode

Ví dụ:

```text
ADD_INT v3, v1, v2
```

target backend có thể chọn:

```text
x86:
ADD r3, r2

ARM:
ADD X3, X1, X2

RISC-V:
ADD x3, x1, x2
```

---

# 14. Target Opcode

Sau legalization:

```text
Machine IR
    ↓
Target Machine IR
```

mới có:

```text
X86_ADD_RR
ARM_ADD_REG
RV_ADD
```

hoặc target-specific instruction family.

---

# 15. Legalization

Không phải mọi Machine IR operation đều trực tiếp tồn tại trên target.

Ví dụ:

```text
I128_ADD
```

trên target chỉ có 64-bit integer arithmetic.

Legalization có thể biến thành:

```text
low_add
high_add_with_carry
```

---

# 16. Legalization Rules

```text
LegalizationRule {
    operation
    target
    required_features
    legal_types
    lowering
    cost
}
```

---

# 17. Legal / Expand / Split

Mỗi machine operation có thể:

```text
Legal
```

hoặc:

```text
Promote
```

hoặc:

```text
Expand
```

hoặc:

```text
Split
```

hoặc:

```text
CustomLower
```

---

# 18. Example — 128-bit Add

```text
I128_ADD a, b
```

target:

```text
64-bit
```

có thể:

```text
ADD low(a), low(b)
ADC high(a), high(b)
```

Machine IR legalization phải biểu diễn dependency carry rõ ràng.

---

# 19. Carry / Flags

Một số ISA có flags:

```text
ADD
ADC
CMP
SETCC
```

Machine IR phải có abstraction cho:

```text
ConditionCode
FlagValue
FlagDependency
```

nhưng không để flags trở thành semantic language values.

---

# 20. Condition Codes

```text
ConditionCode =
    EQ
    NE
    LT
    LE
    GT
    GE
    ULT
    ULE
    UGT
    UGE
    ...
```

Target có thể map sang ISA-specific condition code.

---

# 21. Compare + Branch

OptIR:

```text
cmp(a,b)
if condition
```

Machine lowering có thể tạo:

```text
CMP
BRANCH_CC
```

hoặc target có instruction kết hợp.

---

# 22. Compare + Select

OptIR:

```text
select(a < b, x, y)
```

có thể thành:

```text
CMP
SELECT_CC
```

hoặc:

```text
CMP
SETCC
CMOV
```

Machine legalization quyết định.

---

# 23. Addressing Mode

Machine IR cần abstraction:

```text
MachineAddress {
    base
    index
    scale
    displacement
    symbol
}
```

Nhưng không được giả định mọi target hỗ trợ:

```text
base + index * scale + offset
```

---

# 24. Address Legalization

Ví dụ:

```text
A[i * 4 + 8]
```

x86 có thể biểu diễn bằng một addressing mode.

Một target khác có thể cần:

```text
shift
add
load
```

Do đó address expression trước legalization phải giữ semantic structure.

---

# 25. Memory Access

```text
MachineMemoryOperand {
    address
    size
    alignment
    access_kind
    ordering
    volatility
    alias_metadata
}
```

---

# 26. Memory Semantics

Machine IR **không được làm mất**:

```text
volatile
atomic
ordering
alignment
alias/provenance metadata
```

trước khi backend chứng minh chúng đã được lower đúng.

---

# 27. Atomic Lowering

Ví dụ:

```text
AtomicLoad<T>
```

có thể trở thành target-specific:

```text
LOAD_ACQUIRE
```

hoặc sequence phức tạp hơn.

Machine IR cần giữ:

```text
AtomicOrdering
AtomicScope
```

cho đến khi target legalization hoàn tất.

---

# 28. Fence

```text
Fence {
    ordering
    scope
}
```

không được biến thành ordinary instruction chỉ vì target có instruction giống hình thức.

---

# 29. Volatile

Machine memory operand:

```text
volatile = true
```

và scheduler/backend phải giữ semantics.

---

# 30. Stack Object

Machine IR giới thiệu:

```text
StackObject {
    id
    size
    alignment
    kind
    lifetime
    address_taken
}
```

Ví dụ:

```text
local variable
spill candidate
outgoing argument
return buffer
temporary
```

---

# 31. Stack Không Đồng Nghĩa Heap

Axiom tiếp tục giữ nguyên:

```text
stack != semantic requirement
heap != semantic requirement
```

Machine IR chỉ mô tả rằng target lowering cần storage object.

Optimizer vẫn có thể eliminate object nếu không cần.

---

# 32. Frame Information

```text
FrameInfo {
    local_size
    outgoing_arg_size
    alignment
    dynamic_stack
    saved_registers
    unwind_info
}
```

Ban đầu có thể chưa hoàn chỉnh.

Register allocator/backend sẽ bổ sung.

---

# 33. Calling Convention

Machine IR phải có:

```text
CallingConvention
```

ví dụ:

```text
Axiom
C
System
Fast
Vector
Platform
Wasm
GPU
```

nhưng ABI-specific details được target backend cung cấp.

---

# 34. Machine Call

```text
MachineCall {
    target
    calling_convention
    arguments
    results
    clobbers
    memory_effect
    tail_kind
}
```

---

# 35. Return

```text
MachineReturn {
    values
}
```

ABI lowering quyết định:

```text
register return
stack return
sret
multiple registers
```

---

# 36. Tail Call

Machine IR phải biểu diễn:

```text
TailCall
```

riêng với:

```text
Call
Return
```

vì target có constraints riêng.

---

# 37. Indirect Call

```text
CALL_REG v1
```

có thể là:

```text
function pointer
closure entry
dynamic dispatch
FFI callback
```

Machine IR không cần biết semantic source category nữa, nhưng phải giữ call ABI contract.

---

# 38. Dynamic Dispatch

Sau type/trait lowering:

```text
dyn Trait
```

có thể trở thành:

```text
load function pointer
indirect call
```

hoặc devirtualized direct call.

Machine IR chỉ nhận kết quả cuối cùng.

---

# 39. Closure Call

Closure environment có thể được:

```text
register
stack
memory
eliminated
```

Machine lowering phải không giả định closure luôn heap allocated.

---

# 40. Function Arguments

ABI lowering có thể phân loại:

```text
ArgumentLocation =
    Register
    Stack
    Indirect
    Split
    Coerce
```

Machine IR giữ thông tin này.

---

# 41. Return Value

Tương tự:

```text
ReturnLocation =
    Register
    MultipleRegisters
    Indirect
    Memory
```

---

# 42. Machine Constant

```text
MachineConstant =
    Integer
    Float
    Vector
    Address
    SymbolReference
    Aggregate
```

---

# 43. Constant Materialization

Không phải constant nào cũng có immediate encoding.

Ví dụ large integer:

```text
0x123456789ABCDEF0
```

có thể cần:

```text
load immediate sequence
```

Target legalization quyết định.

---

# 44. Symbolic Address

```text
SymbolAddress {
    symbol
    relocation
    addend
}
```

Cần giữ cho linker/object writer.

Không biến symbol thành raw numeric address trong compiler.

---

# 45. Relocation

Machine IR phải có abstraction:

```text
RelocationKind
```

nhưng relocation format cụ thể thuộc object writer.

Ví dụ:

```text
absolute
PC-relative
GOT
TLS
PLT
WASM index
```

---

# 46. TLS

TLS access cần giữ:

```text
TLSModel
```

để target/linker chọn representation phù hợp.

---

# 47. PIC / PIE

Machine lowering phải biết:

```text
PositionIndependentCode
PositionIndependentExecutable
```

nhưng semantic program không thay đổi.

---

# 48. Function Attributes

Machine function có thể giữ:

```text
NoReturn
Cold
Hot
NoInline
AlwaysInline
NoUnwind
Interrupt
Kernel
Foreign
```

nhưng chỉ những attribute đã được semantic/optimization layer xác nhận mới được backend sử dụng.

---

# 49. NoReturn

Nếu semantic function:

```text
never
```

thì machine CFG có thể kết thúc bằng:

```text
UNREACHABLE
```

---

# 50. Trap / Panic

Machine IR phải phân biệt:

```text
Panic
Trap
Unreachable
```

nếu target semantics khác nhau.

---

# 51. Machine Trap

Ví dụ:

```text
integer trap
bounds trap
explicit panic
illegal instruction
```

không nhất thiết cùng semantic origin.

Backend cần mapping chính xác.

---

# 52. Debug Provenance

Mỗi machine operation cần giữ:

```text
SourceSpan
InlineStack
InstructionOrigin
```

để debug có thể đi:

```text
source
 ↓
HIR
 ↓
MIR
 ↓
OptIR
 ↓
MachineIR
 ↓
Machine instruction
```

---

# 53. Optimization Provenance

Machine IR cũng cần biết:

```text
generated_by
```

ví dụ:

```text
ScalarFold
Vectorize
IfConvert
Scheduling
Legalization
ABI
```

để diagnostics/AI giải thích.

---

# 54. Machine IR Verification

Verifier cần kiểm tra:

```text
correct operand types
valid register classes
valid block references
valid CFG
valid memory operands
valid calling conventions
valid atomic ordering
valid stack objects
valid constants
valid target constraints
```

---

# 55. Machine IR Không Được Bypass Semantic Verification

Một operation không hợp lệ ở semantic level:

```text
invalid ownership
invalid capability
data race
invalid lifetime
```

không được “hợp pháp hóa” bằng cách biến thành machine instructions.

---

# 56. Legalization Không Phải Optimization

Ví dụ:

```text
I128_ADD
```

target không hỗ trợ trực tiếp.

Split thành:

```text
ADD
ADC
```

đây là:

```text
legalization
```

không phải optimization.

---

# 57. Legalization Có Cost Nhưng Không Có Quyền Phá Semantics

Có nhiều cách legalize:

```text
sequence A
sequence B
runtime helper
library call
```

Cost model chọn giữa những cách **đều semantic-equivalent**.

---

# 58. Runtime Helper

Ví dụ target không hỗ trợ operation:

```text
f128_div
```

có thể lower:

```text
runtime helper
```

nhưng nếu compiler profile là:

```text
freestanding
runtime-free
```

thì phải có alternative hoặc báo target limitation.

---

# 59. Runtime Dependency Explicit

Machine IR phải biết:

```text
requires_runtime_symbol
```

để build system/runtime composer biết binary có dependency gì.

Không được âm thầm link monolithic runtime.

---

# 60. Freestanding

Trong freestanding profile:

```text
no libc
no Axiom runtime
```

vẫn có thể generate machine code cho operation nếu target backend có implementation.

---

# 61. GPU Machine IR

GPU cũng dùng Machine IR architecture nhưng:

```text
CPU register
```

và:

```text
GPU register
```

không được giả định giống nhau.

GPU target cung cấp:

```text
GPURegisterClass
GPUAddressSpace
GPUInstruction
GPUBarrier
GPUKernelEntry
```

---

# 62. WASM

WASM cũng có Machine IR backend riêng:

```text
Machine IR
   ↓
WASM Legalization
   ↓
WASM stack/local representation
```

Không ép WASM phải giả lập CPU register model.

---

# 63. Machine IR Target Profiles

```text
TargetKind =
    CPU
    GPU
    WASM
    Device
    Firmware
```

Machine IR core dùng chung:

```text
CFG
operation
memory
call
constant
debug
```

target-specific layers mở rộng.

---

# 64. Machine IR Extension

```text
MachineTargetExtension {
    legalize
    instruction_classes
    register_classes
    addressing_modes
    calling_conventions
    atomic_lowering
    vector_lowering
    branch_lowering
}
```

---

# 65. Không Plugin ISA Trong Core v1

Axiom compiler core không cần dynamic backend plugin system.

Backend nên compile-time/static integrated trước.

Điều này giúp:

- dễ bootstrap;
- deterministic;
- dễ self-host;
- ít ABI/plugin complexity.

---

# 66. Machine IR Serialization

Machine IR có thể được serialize cho:

```text
debugging
compiler cache
backend testing
replay
AI analysis
```

nhưng serialized MIR phải có:

```text
compiler semantic version
target
features
ABI
MachineIR schema version
```

---

# 67. Cache

Machine IR cache không được coi là trusted.

Load lại phải:

```text
validate
target-check
schema-check
feature-check
```

trước code generation.

---

# 68. Target Features

Ví dụ:

```text
AVX2
AVX512
SVE
RVV
NEON
Atomics
GPU subgroup
```

Machine IR legalization phải biết target feature set.

Không được generate instruction yêu cầu feature chưa được bật.

---

# 69. Feature Fallback

Nếu:

```text
vector_width = 512
```

nhưng target chỉ có:

```text
256
```

legalizer có thể:

```text
split
```

hoặc:

```text
scalarize
```

nếu semantic/profitability cho phép.

---

# 70. Scalarization

Ví dụ:

```text
v4xf32 operation
```

target không hỗ trợ vector:

```text
scalar op 0
scalar op 1
scalar op 2
scalar op 3
```

Đây là legalization fallback.

---

# 71. Mask Legalization

Mask:

```text
v16xi1
```

có thể target hỗ trợ native predicate register.

Target khác có thể cần:

```text
bitmask
vector integer
branch sequence
```

Machine IR giữ semantic mask trước legalization cuối.

---

# 72. Gather/Scatter

Machine IR phải biểu diễn:

```text
Gather
Scatter
```

độc lập target.

Target có native gather:

```text
→ instruction
```

không có:

```text
→ scalar loop / helper / sequence
```

tùy cost.

---

# 73. Division

Machine IR:

```text
SDIV
UDIV
FDIV
```

target có thể:

```text
instruction
sequence
runtime helper
```

nhưng semantics giữ nguyên.

---

# 74. Wide Integer

Axiom hỗ trợ:

```text
i128/u128
```

về semantic/type-system layer.

Machine backend không nhất thiết cần native 128-bit register.

Legalizer chia nhỏ.

---

# 75. Multi-result Operations

Một machine operation có thể có nhiều result:

```text
ADD_WITH_CARRY
DIV_REM
MUL_WIDE
```

Machine IR phải hỗ trợ:

```text
defs = [v1, v2]
```

---

# 76. Tuple/Struct ABI Lowering

Semantic:

```text
fn f() -> Pair
```

Machine IR có thể trở thành:

```text
return v0, v1
```

hoặc:

```text
sret buffer
```

ABI layer quyết định.

---

# 77. Aggregate Passing

Machine IR phải hỗ trợ:

```text
by_value
by_register
split
indirect
```

không giả định mọi struct truyền qua pointer.

---

# 78. Address-Taken Semantics

Nếu source không expose address:

```text
struct S
```

có thể:

```text
scalarized
```

Nếu address observable:

```text
storage object
```

có thể cần giữ.

Machine lowering phải tôn trọng Escape/StableAddress proof.

---

# 79. Stable Address

Nếu:

```text
stable_address(S)
```

là contract:

Machine IR không được tự ý:

```text
scalarize
relocate
eliminate
```

storage làm mất stable address.

---

# 80. Final Machine IR Boundary

Sau legalization:

```text
Machine IR
```

phải đạt:

```text
all operations target-legal
all types target-legal
all calling conventions resolved
all memory operations legal
all atomic operations legal
all vector operations legal
all branches legal
all constants representable/lowerable
```

Sau đó mới:

```text
Instruction Selection
Register Allocation
```

---

# 81. Module Structure

```text
compiler/backend/machine/
├── mod.ax
│
├── function.ax
├── block.ax
├── instruction.ax
├── operand.ax
├── type.ax
├── constant.ax
├── symbol.ax
├── relocation.ax
├── stack_object.ax
├── frame.ax
├── register/
│   ├── class.ax
│   ├── virtual.ax
│   └── physical.ax
│
├── memory/
│   ├── operand.ax
│   ├── address.ax
│   ├── atomic.ax
│   └── volatile.ax
│
├── abi/
│   ├── calling_convention.ax
│   ├── argument.ax
│   ├── return.ax
│   └── call.ax
│
├── legalization/
│   ├── mod.ax
│   ├── legal.ax
│   ├── promote.ax
│   ├── expand.ax
│   ├── split.ax
│   ├── scalarize.ax
│   ├── vector.ax
│   ├── integer.ax
│   ├── memory.ax
│   ├── atomic.ax
│   └── branch.ax
│
├── target/
│   ├── extension.ax
│   ├── features.ax
│   ├── cost.ax
│   └── target_info.ax
│
├── verify/
│   ├── types.ax
│   ├── cfg.ax
│   ├── operands.ax
│   ├── memory.ax
│   └── abi.ax
│
└── tests/
```

---

# 82. Implementation Order

```text
1. MachineType
2. VirtualRegister
3. RegisterClass
4. MachineOperand
5. MachineInstruction
6. MachineBasicBlock
7. MachineFunction
8. Machine CFG
9. Machine memory operand
10. Machine address
11. Machine constants
12. Symbol references
13. Stack objects
14. Frame information
15. Calling convention representation
16. Machine call/return
17. condition codes
18. flag dependencies
19. atomic representation
20. volatile representation
21. target feature model
22. target legality model
23. generic legalization
24. integer legalization
25. wide-integer splitting
26. vector legalization
27. mask legalization
28. gather/scatter legalization
29. memory/address legalization
30. atomic legalization
31. branch legalization
32. ABI legalization
33. runtime-helper dependency tracking
34. CPU target extension interface
35. GPU target extension interface
36. WASM target extension interface
37. Machine IR verifier
38. proof/provenance propagation
39. debug provenance
40. Machine IR serialization
41. cache validation
42. adversarial tests
```

---

# 83. Adversarial Tests

### Test 1 — i128

```text
u128_add(a, b)
```

trên target 64-bit phải legalize thành sequence chính xác.

### Test 2 — unsupported vector

```text
v16xf32
```

trên target chỉ hỗ trợ `v8xf32` phải split/scalarize đúng.

### Test 3 — atomic ordering

Không được legalization làm mất Acquire/Release/SeqCst.

### Test 4 — volatile

Không được biến volatile thành ordinary load/store.

### Test 5 — stable address

Không được scalarize object có stable-address contract.

### Test 6 — FFI ABI

Argument/return phải đúng ABI.

### Test 7 — large constant

Constant không encode trực tiếp được phải materialize đúng.

### Test 8 — relocation

Symbol address phải giữ relocation information.

### Test 9 — PIC

Không hard-code absolute address khi target/profile yêu cầu PIC.

### Test 10 — tail call

Tail-call legality phải được giữ tới backend.

### Test 11 — GPU address space

Không được biến Device/Shared/Local address space thành generic host pointer.

### Test 12 — WASM

Không giả định WASM có physical register.

### Test 13 — register class

Operation không được nhận operand thuộc register class không hợp lệ.

### Test 14 — target feature

Không emit operation yêu cầu feature chưa bật.

### Test 15 — cache poisoning

Machine IR cache không hợp lệ phải bị reject và regenerate.

---

# 84. Frozen Invariants

### `AMIR-20..100`

```text
AMIR-20 — Machine IR Is Distinct From Semantic IR
AMIR-21 — Machine IR Is Distinct From Physical Machine Code
AMIR-22 — Semantic Type Identity Is Not Machine Type Identity
AMIR-23 — Machine IR Must Preserve Observable Semantics
AMIR-24 — Machine IR Must Preserve ABI Contracts
AMIR-25 — Machine IR Must Preserve Memory Semantics
AMIR-26 — Machine IR Must Preserve Atomic Semantics
AMIR-27 — Machine IR Must Preserve Volatile Semantics
AMIR-28 — Machine IR Must Preserve Panic Semantics
AMIR-29 — Machine IR Must Preserve Drop Semantics
AMIR-30 — Machine IR Must Preserve Ownership Semantics
AMIR-31 — Machine IR Must Preserve Capability Provenance
AMIR-32 — Machine IR Must Preserve Stable-Address Contracts
AMIR-33 — Machine IR Must Preserve Execution Domains
AMIR-34 — Machine IR Must Preserve Storage Domains
AMIR-35 — Machine IR Must Support Virtual Registers
AMIR-36 — Virtual Registers Must Be Independent Of Physical Registers
AMIR-37 — Register Classes Must Be Explicit
AMIR-38 — Machine Types Must Be Explicit
AMIR-39 — Machine Operands Must Be Typed
AMIR-40 — Machine CFG Must Be Explicit
AMIR-41 — Machine Memory Operations Must Carry Required Memory Metadata
AMIR-42 — Unknown Alias Must Not Become NoAlias During Lowering
AMIR-43 — Target Legalization Must Preserve Semantic Equivalence
AMIR-44 — Legalization Is Distinct From Optimization
AMIR-45 — Cost Cannot Override Legalization Correctness
AMIR-46 — Unsupported Operations Must Be Explicitly Legalized
AMIR-47 — Wide Integer Operations Must Have Defined Lowerings
AMIR-48 — Vector Operations Must Have Defined Lowerings
AMIR-49 — Mask Operations Must Have Defined Lowerings
AMIR-50 — Gather/Scatter Must Have Defined Lowerings
AMIR-51 — Atomic Operations Must Preserve Ordering
AMIR-52 — Volatile Operations Must Remain Observable
AMIR-53 — Condition Codes Must Preserve Comparison Semantics
AMIR-54 — Flag Dependencies Must Be Explicit
AMIR-55 — Memory Addressing Must Preserve Address Semantics
AMIR-56 — Pointer Provenance Must Not Be Reconstructed From Integers
AMIR-57 — Symbolic Addresses Must Preserve Relocation Information
AMIR-58 — PIC/PIE Constraints Must Be Preserved
AMIR-59 — TLS Semantics Must Be Preserved
AMIR-60 — Calling Conventions Must Be Explicit
AMIR-61 — Argument Locations Must Be Explicit After ABI Lowering
AMIR-62 — Return Locations Must Be Explicit After ABI Lowering
AMIR-63 — Tail Calls Must Have Explicit Legality
AMIR-64 — Runtime Helper Dependencies Must Be Explicit
AMIR-65 — Freestanding Profiles Must Not Silently Introduce Runtime Dependencies
AMIR-66 — Target Features Must Be Explicit
AMIR-67 — Illegal Target Features Must Not Be Emitted
AMIR-68 — Target-Specific Instructions Must Not Leak Into Generic Machine IR
AMIR-69 — CPU Register Models Must Not Be Imposed On WASM
AMIR-70 — CPU Memory Models Must Not Be Imposed On GPU Address Spaces
AMIR-71 — GPU Address Spaces Must Remain Explicit
AMIR-72 — Machine IR Must Be Verifiable
AMIR-73 — Invalid Machine IR Must Not Reach Instruction Selection
AMIR-74 — Machine IR Transformations Must Preserve Debug Provenance
AMIR-75 — Machine IR Must Preserve Optimization Provenance
AMIR-76 — Machine IR Serialization Must Be Versioned
AMIR-77 — Machine IR Cache Data Is Untrusted
AMIR-78 — Cached Machine IR Must Be Revalidated
AMIR-79 — Machine IR Generation Must Be Deterministic
AMIR-80 — Worker Count Must Not Change Machine IR Semantics
AMIR-81 — Legalization Must Not Bypass Semantic Verification
AMIR-82 — Legalization Must Not Invent Safety Proofs
AMIR-83 — Legalization Must Respect Existing Proof Contracts
AMIR-84 — Stable Address Must Prevent Illegal Scalarization
AMIR-85 — Observable Address Escape Must Be Preserved
AMIR-86 — Aggregate ABI Lowering Must Preserve Value Semantics
AMIR-87 — Multi-Result Operations Must Preserve Result Relationships
AMIR-88 — Machine IR Must Support Target-Specific Extensions Without Polluting Core Semantics
AMIR-89 — Machine IR Must Support Multiple Backend Families
AMIR-90 — Machine IR Must Not Assume A Single ISA
AMIR-91 — Machine IR Must Not Assume A Single Register File
AMIR-92 — Machine IR Must Not Assume A Single Memory Model Representation
AMIR-93 — Machine IR Must Not Assume A Single Calling Convention
AMIR-94 — Machine IR Must Not Assume A Single Instruction Width
AMIR-95 — Machine IR Must Not Assume A Single Vector Width
AMIR-96 — Failed Legalization Must Produce A Deterministic Diagnostic
AMIR-97 — Unsupported Target Features Must Be Diagnosed Explicitly
AMIR-98 — Machine IR Must Be Ready For Register Allocation
AMIR-99 — Machine IR Must Be Ready For Instruction Selection
AMIR-100 — Machine IR Is The Stable Boundary Between Optimization And Target Code Generation
```

---

## 85. Kiến trúc Axiom sau task này

Đến đây pipeline đã có một ranh giới rất sạch:

```text
              LANGUAGE SEMANTICS
                     │
                     ▼
               Verified MIR
                     │
                     ▼
              ┌─────────────┐
              │    OptIR    │
              └─────────────┘
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
    Scalar        Memory        Control
       │             │             │
       └──────┬──────┴──────┬──────┘
              ▼             ▼
            Loop        Vector
              │             │
              └──────┬──────┘
                     ▼
                Scheduling
                     │
                     ▼
             ┌──────────────┐
             │  Machine IR  │
             └──────────────┘
                     │
                     ▼
               Legalization
                     │
                     ▼
            Instruction Selection
                     │
                     ▼
             Register Allocation
                     │
                     ▼
            Machine Scheduling
                     │
                     ▼
                Encoding
```

Điểm đặc biệt của Axiom là **Machine IR không phá vỡ triết lý “compiler phức tạp, ngôn ngữ đơn giản”**: programmer không cần biết register class, addressing mode, carry flag, calling convention hay vector register. Đây là hoàn toàn trách nhiệm của compiler/backend.

**BOOTSTRAP-296 hoàn tất và được đóng băng.**