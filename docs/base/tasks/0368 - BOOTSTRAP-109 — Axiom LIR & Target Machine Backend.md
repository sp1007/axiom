# BOOTSTRAP-109 — Axiom LIR & Target Machine Backend
**FROZEN / COMPLETED**

Đây là tầng biến **ABI MIR thành machine code có thể thực thi**.

Triết lý vẫn giữ nguyên:

> **Frontend hiểu ngôn ngữ. MIR hiểu semantics. OptIR hiểu optimization. ABI MIR hiểu binary contract. LIR hiểu cách biểu diễn chương trình trên một họ máy cụ thể.**

---

# 1. Vị trí chính thức

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
Verification
  ↓
Verified MIR
  ↓
OptIR
  ↓
Optimization
  ↓
ABI MIR
  ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━
        BOOTSTRAP-109
━━━━━━━━━━━━━━━━━━━━━━━━━━
  ↓
Axiom LIR
  ↓
Target Legalization
  ↓
Instruction Selection
  ↓
Machine IR
  ↓
Register Allocation
  ↓
Scheduling
  ↓
Prologue/Epilogue
  ↓
Machine Encoding
  ↓
Object Code
```

---

# 2. Tách Axiom LIR khỏi Machine IR

Đây là quyết định quan trọng.

## Axiom LIR

Target-aware nhưng chưa hoàn toàn phụ thuộc instruction set.

Ví dụ:

```text
LIR.Add
LIR.Sub
LIR.Mul
LIR.Load
LIR.Store
LIR.Call
LIR.Branch
LIR.Compare
LIR.Atomic
LIR.Vector
```

## Machine IR

Phụ thuộc target:

```text
X86.ADD
X86.LEA
X86.CMP
X86.JCC

ARM64.ADD
ARM64.CBZ
ARM64.LDR

RISCV.ADD
RISCV.BEQ
```

Do đó:

```text
ABI MIR
    ↓
Axiom LIR
    ↓
Machine IR
```

là một boundary rất sạch.

---

# 3. Axiom LIR không còn ownership semantics

Đến đây các khái niệm như:

```text
Ownership
Capability
view lifetime
Move state
Borrow-like state
```

đã được verifier xử lý.

LIR chỉ còn các physical consequences cần thiết:

```text
value
memory
control flow
call
atomic
volatile
ABI
target features
```

---

# 4. Nhưng semantics không được mất

“Ownership biến mất” không có nghĩa:

```text
Drop biến mất
```

Nếu Drop có observable effect:

```text
Drop
 ↓
call destructor
```

vẫn phải tồn tại.

Chỉ những compiler-only facts mới được erase.

---

# 5. LIR instruction model

Đề xuất:

```text
LirInstruction {
    opcode
    operands[]
    results[]
    memory_effect
    control_effect
    source_origin
}
```

Ví dụ:

```text
%3 = add %1, %2
%4 = load %ptr
store %4, %ptr2
call %fn
branch %bb3
```

---

# 6. Virtual registers

LIR không dùng physical register ngay.

Ví dụ:

```text
%v0
%v1
%v2
```

Sau này register allocator quyết định:

```text
%v0 → RAX
%v1 → RCX
%v2 → XMM0
```

Điều này giúp optimization/backend tách biệt.

---

# 7. Register classes

Mỗi virtual register có class:

```text
INTEGER
FLOAT
VECTOR
PREDICATE
ADDRESS
FLAGS
```

Target có thể mở rộng.

Ví dụ x86-64:

```text
GPR
XMM
YMM
ZMM
FLAGS
```

AArch64:

```text
GPR
FP/SIMD
NZCV
```

---

# 8. Không giả định mọi CPU có cùng register model

Axiom backend interface:

```text
TargetDescription {
    registers
    register_classes
    instructions
    calling_conventions
    addressing_modes
    features
    alignment
}
```

---

# 9. Instruction selection

Ví dụ LIR:

```text
x = x + y
```

x86-64 có thể:

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

Nhưng một LIR operation không nhất thiết map 1:1.

Ví dụ:

```text
multiply + add
```

có thể trở thành:

```text
FMA
```

nếu target hỗ trợ và semantics cho phép.

---

# 10. Legalization

Một LIR operation có thể không được target hỗ trợ trực tiếp.

Ví dụ:

```text
i128 add
```

trên CPU không có native 128-bit integer:

```text
i128
 ↓
low64 + high64
 ↓
ADC
```

Hoặc trên target khác:

```text
multiple instructions
```

Legalization biến operation thành tập operations mà target có thể thực hiện.

---

# 11. Wide integer

Axiom hỗ trợ:

```text
i128
u128
```

về type-system architecture.

Nhưng backend không cần giả định CPU native 128-bit.

Có thể lower thành:

```text
{ low: u64, high: u64 }
```

và compiler tối ưu tùy target.

---

# 12. Floating point

LIR phải phân biệt:

```text
f32
f64
```

và sau này:

```text
f16
bf16
```

Target feature quyết định instruction selection.

Không được silently thay đổi floating semantics chỉ để nhanh hơn.

---

# 13. Fast math

Không nên mặc định:

```text
-O3 => unsafe floating transformations
```

Nếu muốn relaxed floating semantics:

```text
@fast_math
```

hoặc compilation profile explicit.

Core semantics mặc định phải predictable.

---

# 14. SIMD

LIR có vector type:

```text
Vector<T, N>
```

hoặc internal equivalent.

Ví dụ:

```text
Vector<f32, 4>
```

có thể map:

```text
x86 → XMM
ARM64 → SIMD register
RISC-V → vector register
```

---

# 15. SIMD không phải language-only feature

Compiler có thể tự vectorize:

```text
scalar loop
 ↓
vector LIR
```

hoặc programmer dùng vector intrinsic/API.

Hai con đường đều đi qua cùng backend.

---

# 16. Target features

Compiler phải biết:

```text
SSE2
AVX2
AVX-512

NEON
SVE

RVV
```

Ví dụ:

```text
TargetFeatures {
    simd
    fma
    atomics
    crypto
    ...
}
```

---

# 17. `@target_feature`

Attribute đã frozen:

```text
@target_feature(...)
```

Nó tạo compilation constraint.

Không được compiler tự phát sinh instruction yêu cầu CPU feature mà executable không đảm bảo.

---

# 18. CPU feature dispatch

Nếu muốn binary chạy nhiều CPU:

```text
baseline implementation
+
optimized implementation
+
runtime feature selection
```

đây là library/runtime/system facility.

Không phải semantics của type system.

---

# 19. Addressing modes

Machine IR phải biểu diễn:

```text
base
index
scale
offset
```

Ví dụ x86:

```text
[base + index*8 + offset]
```

Axiom LIR có thể có abstract address:

```text
Address {
    base
    index
    scale
    offset
}
```

Target lowering quyết định có thể dùng addressing mode trực tiếp hay phải materialize address.

---

# 20. LEA-like optimization

Ví dụ:

```text
x = base + index * 8
```

x86 backend có thể:

```text
LEA
```

thay vì:

```text
MUL
ADD
```

nhưng ARM/RISC-V sẽ chọn chiến lược khác.

---

# 21. Flags / condition codes

Không nên biến flags thành ordinary semantic value quá sớm.

Machine IR cần biểu diễn implicit dependencies:

```text
ADD → FLAGS
CMP → FLAGS
JCC consumes FLAGS
```

để scheduler/register allocator không phá dependency.

---

# 22. ARM64 NZCV

Tương tự:

```text
CMP
 ↓
NZCV
 ↓
conditional branch
```

phải được Machine IR mô hình hóa.

---

# 23. Register allocation

Ban đầu:

```text
%v1
%v2
%v3
%v4
```

sau allocation:

```text
%v1 → RAX
%v2 → RBX
%v3 → XMM0
%v4 → RDX
```

---

# 24. Allocation strategy

Bootstrap compiler:

```text
Linear Scan
```

là lựa chọn hợp lý.

Sau khi compiler trưởng thành:

```text
Priority / Graph / Hybrid allocator
```

có thể được thêm.

Không cần khóa một algorithm duy nhất cho toàn đời compiler.

---

# 25. Live interval

Register allocator cần:

```text
LiveRange
```

Ví dụ:

```text
%v1:
[3, 15]
```

Hai values không overlap có thể dùng cùng physical register.

---

# 26. Register coalescing

Ví dụ:

```text
%v2 = %v1
```

Nếu:

```text
%v1 → RAX
%v2 → RBX
```

thì có thể gây move.

Coalescing cố:

```text
%v1 → RAX
%v2 → RAX
```

→ loại bỏ move.

---

# 27. Phi elimination

SSA có:

```text
%v3 = phi(%v1, %v2)
```

Machine code không có phi.

Lower thành:

```text
parallel copies
```

ở predecessor.

Sau đó:

```text
copy coalescing
```

loại bỏ copy dư thừa.

---

# 28. Spill

Nếu không đủ registers:

```text
virtual register
 ↓
stack slot
```

Ví dụ:

```text
store RAX, [rsp+32]
...
load RAX, [rsp+32]
```

Compiler cố:

- rematerialize;
- split live range;
- reuse registers;

trước khi spill.

---

# 29. Rematerialization

Nếu value:

```text
x = constant 42
```

thay vì spill:

```text
store 42
load
```

compiler có thể:

```text
materialize 42 again
```

rẻ hơn.

---

# 30. Stack frame

Backend tạo:

```text
StackFrame {
    locals
    spills
    outgoing_args
    alignment
    saved_registers
}
```

Target ABI quyết định chi tiết.

---

# 31. Stack allocation không đồng nghĩa runtime allocation

Đây là:

```text
machine stack
```

không phải:

```text
heap allocator
```

Axiom semantics vẫn giữ distinction.

---

# 32. Prologue / Epilogue

Backend sinh:

```text
prologue
    save registers
    allocate frame
    establish ABI state

body

epilogue
    restore registers
    deallocate frame
    return
```

Có thể tối ưu:

```text
leaf function
```

thành frame tối thiểu hoặc không frame.

---

# 33. Tail call

Nếu ABI và semantics cho phép:

```text
return f(x)
```

có thể:

```text
tail call f
```

thay vì:

```text
call f
return
```

Nhưng chỉ khi:

- calling convention compatible;
- stack state compatible;
- Drop obligations đã hoàn tất;
- no required post-call work.

---

# 34. Drop và tail call

Ví dụ:

```axiom id="7q3f8p"
fn f(x: Resource) -> i32 {
    return g();
}
```

Nếu `x` còn cần Drop trước return:

```text id="k4m8c2"
drop(x)
tail-call g
```

hoặc tail call không hợp lệ.

Do đó semantic cleanup phải được lower trước tail-call decision.

---

# 35. Atomic lowering

Semantic:

```text
AtomicLoad
AtomicStore
AtomicRMW
CompareExchange
```

xuống machine instruction phù hợp.

Ví dụ x86:

```text
LOCK CMPXCHG
```

ARM:

```text
LDXR/STXR
```

RISC-V:

```text
LR/SC
AMO
```

---

# 36. Memory ordering

Machine backend phải preserve:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Không được xem atomic order như optimization hint.

Nó là semantic contract.

---

# 37. Fences

Axiom:

```text
compiler ordering
≠
CPU memory fence
```

Machine backend phải phân biệt:

```text
CompilerBarrier
CPUFence
AtomicOperation
```

---

# 38. Volatile

Volatile lowering phải giữ:

```text
observable machine memory access
```

Compiler không được:

- remove;
- merge;
- reorder trái contract.

Volatile vẫn khác atomic.

---

# 39. Inline assembly

Axiom hỗ trợ:

```text
unsafe asm
```

nhưng Machine IR phải biết:

```text
inputs
outputs
clobbers
memory effects
flags
register constraints
```

Nếu programmer khai báo sai:

> trách nhiệm thuộc unsafe contract.

Nhưng compiler vẫn phải tôn trọng những dependency đã khai báo.

---

# 40. `asm` không được phá compiler model

Inline asm không nên là:

```text
magic black hole
```

mà có structured effects:

```text
AsmInstruction {
    template
    inputs
    outputs
    clobbers
    memory
}
```

---

# 41. Calls

Machine IR:

```text
Call {
    target
    args
    convention
    clobbers
    return_values
}
```

ABI đã phân loại args.

Register allocator mapping vào physical registers.

---

# 42. Indirect call

Ví dụ:

```text
fn_ptr()
```

→ machine:

```text
call reg
```

Dynamic trait:

```text
vtable[method_index]
```

→ load function pointer + indirect call.

---

# 43. Call clobber information

Target ABI phải cung cấp:

```text
caller_saved
callee_saved
```

Ví dụ x86-64:

```text
RAX
RCX
RDX
...
```

có thể caller-saved.

Backend dùng để spill/restore đúng.

---

# 44. Branch lowering

LIR:

```text
branch condition
```

Machine:

```text
CMP
JCC
```

hoặc ARM:

```text
CBZ
CBNZ
B.cond
```

hoặc RISC-V:

```text
BEQ
BNE
BLT
...
```

---

# 45. Branch relaxation

Khoảng cách branch có thể thay đổi sau layout.

Compiler cần:

```text
short branch
long branch
```

và có thể phải relax:

```text
short → long
```

ở cuối code generation.

---

# 46. Jump tables

`match`/switch có thể lower thành:

```text
if chain
binary decision tree
jump table
```

Optimizer quyết định dựa trên:

- density;
- range;
- profile;
- code size.

---

# 47. Code layout

Backend/linker nên phân biệt:

```text
hot code
cold code
```

PGO có thể cung cấp dữ liệu.

Có thể tổ chức:

```text
.text.hot
.text
.text.cold
```

tùy object format.

---

# 48. Basic block layout

Mục tiêu:

- giảm branch;
- fall-through hot path;
- cải thiện I-cache;
- giảm branch misprediction.

Nhưng semantics không đổi.

---

# 49. Constant pools

Một số target cần constant pool:

```text
large floating constants
vector constants
addresses
```

Backend quản lý placement và relocation.

---

# 50. Literal materialization

Compiler phải biết khi nào:

```text
immediate
```

có thể encode trực tiếp và khi nào cần:

```text
constant pool
multiple instructions
register materialization
```

---

# 51. x86-64 backend v1

Nên hỗ trợ trước:

```text
x86-64 System V
x86-64 Windows
```

với:

- GPR;
- SSE2;
- integer;
- floating;
- calls;
- atomics;
- TLS;
- unwind/debug;
- relocations.

---

# 52. AArch64 backend

Tiếp theo:

```text
AArch64
```

đặc biệt quan trọng cho:

- macOS;
- iOS;
- Android;
- ARM servers.

Support:

- GPR;
- FP/SIMD;
- atomics;
- TLS;
- calling conventions;
- branch;
- load/store;
- NEON.

---

# 53. RISC-V

Tiếp theo:

```text
RV64
```

với:

```text
I
M
A
F
D
C
```

và vector extension sau.

---

# 54. WASM

WASM không nên bị ép vào CPU Machine IR hoàn toàn.

Pipeline có thể:

```text
ABI MIR
 ↓
WASM LIR
 ↓
WASM encoder
```

vì execution model khác CPU native.

Nhưng semantic frontend/verification/optimization vẫn dùng chung.

---

# 55. GPU backend

Tương tự:

```text
GPU MIR / GPU LIR
```

có thể tách khỏi CPU Machine IR.

Ví dụ:

```text
CUDA-like target
SPIR-V
Metal
DirectX
```

là những backend riêng.

Không ép CPU register model vào GPU.

---

# 56. Backend interface

Đề xuất:

```text
trait TargetBackend {
    describe_target()
    lower_abi()
    legalize()
    select_instructions()
    allocate_registers()
    schedule()
    emit_object()
}
```

Nhưng implementation có thể dùng internal compiler interfaces thay vì public trait.

---

# 57. Target description

Mỗi target cung cấp:

```text
TargetInfo {
    Arch
    OS
    ABI
    Endianness
    PointerWidth
    Registers
    RegisterClasses
    Instructions
    Features
    AlignmentRules
    CallingConventions
    TLSModel
    RelocationModel
}
```

---

# 58. Target triple

Axiom cần target identity kiểu:

```text
x86_64-pc-windows
x86_64-unknown-linux
aarch64-apple-darwin
aarch64-apple-ios
aarch64-linux-android
wasm32-unknown
```

Format chính xác có thể được frozen ở build/target specification.

---

# 59. Machine instruction representation

Machine IR nên có:

```text
MachineInstruction {
    opcode
    explicit_operands
    implicit_uses
    implicit_defs
    memory_operands
    flags
    debug_location
}
```

Điểm `implicit_uses/defs` rất quan trọng.

Ví dụ:

```text
CMP
```

implicit define:

```text
FLAGS
```

`JNE` implicit use:

```text
FLAGS
```

---

# 60. Scheduling

Instruction scheduler phải hiểu:

```text
data dependency
memory dependency
atomic ordering
volatile
call
flags
register pressure
latency
throughput
```

Không được chỉ reorder theo opcode cost.

---

# 61. Scheduler không phá memory semantics

Ví dụ:

```text
AtomicRelease
AtomicAcquire
```

không thể reorder như ordinary loads.

Tương tự:

```text
volatile
```

và FFI side effects.

---

# 62. Instruction latency model

Target description có thể chứa:

```text
latency
throughput
resource usage
```

để scheduler và cost model tối ưu.

Không cần chính xác tuyệt đối; backend có thể version theo CPU family.

---

# 63. CPU-specific tuning

Có thể:

```text
-march=native
-mcpu=...
```

nhưng semantics không thay đổi.

Chỉ instruction selection/scheduling/cost model thay đổi.

---

# 64. Register allocator và debug

Khi:

```text
%x → RAX
```

debug information phải biết mapping.

Nếu spilled:

```text
%x → stack[rbp-32]
```

debugger vẫn phải theo được source variable ở mức hợp lý.

---

# 65. Debug information

Compiler cần duy trì:

```text
SourceSpan
MIR instruction
OptIR value
LIR instruction
Machine instruction
```

mapping.

Ví dụ:

```text
source line 42
 ↓
MIR #184
 ↓
OptValue #93
 ↓
Machine instruction #721
```

---

# 66. Unwind information

Nếu target hỗ trợ unwind:

```text
DWARF CFI
Windows unwind info
```

backend phải sinh đúng theo stack frame.

Nếu panic profile = abort:

```text
```

có thể giảm unwind metadata nếu không cần.

---

# 67. `panic=abort`

Cho binary nhỏ:

```text
panic = abort
```

có thể loại bỏ:

- unwind tables;
- personality functions;
- unwind runtime.

---

# 68. `panic=unwind`

Nếu chọn:

```text
panic = unwind
```

backend phải giữ:

- cleanup paths;
- unwind edges;
- unwind metadata;
- personality ABI.

Semantic Drop vẫn được đảm bảo.

---

# 69. Stack maps

Sau này nếu cần:

- async runtime;
- precise GC-like external systems;
- profiler;
- debugger;

có thể sinh stack maps.

Nhưng Core không yêu cầu GC.

---

# 70. No hidden runtime

Machine backend không được tự động thêm:

```text
GC runtime
object header
global scheduler
exception runtime
```

chỉ vì một language feature tồn tại.

Chỉ link runtime component khi program thực sự yêu cầu.

---

# 71. Binary size

Backend phải hỗ trợ:

```text
dead machine code elimination
section splitting
identical code folding
constant merging
instruction-size selection
```

khi target/linker cho phép.

---

# 72. Instruction-size optimization

Ví dụ x86:

```text
short encoding
```

có thể giảm binary size.

RISC-V:

```text
C extension
```

có thể giảm instruction size.

Nhưng chỉ dùng nếu target feature hợp lệ.

---

# 73. Peephole optimization

Machine backend có một pass nhỏ:

```text
MachinePeephole
```

Ví dụ:

```text
MOV RAX, RBX
MOV RBX, RAX
```

có thể tối ưu tùy context.

Nhưng không nên biến peephole thành nơi chứa semantic logic.

---

# 74. Machine-level optimization không thay thế OptIR

Phân chia:

### OptIR

```text
meaning-aware optimization
```

### Machine IR

```text
target-aware optimization
```

Ví dụ:

```text
vectorization
```

chủ yếu OptIR.

Trong khi:

```text
instruction scheduling
register coalescing
addressing mode selection
```

ở Machine IR.

---

# 75. Machine encoder

Cuối cùng:

```text
Machine IR
 ↓
Encoder
 ↓
bytes
```

Ví dụ conceptually:

```text
ADD RAX, RBX
 ↓
machine bytes
```

Encoder phải xử lý:

- opcode;
- prefixes;
- immediate;
- displacement;
- ModRM/SIB;
- instruction length;
- relocation placeholders.

---

# 76. Relocation không được hard-code trong encoder

Encoder tạo:

```text
Relocation {
    offset
    type
    symbol
    addend
}
```

ObjectWriter mới biết:

```text
ELF
PE/COFF
Mach-O
```

Điều này giữ backend và object format độc lập.

---

# 77. Branch relocation

Nếu target symbol chưa biết:

```text
call foo
```

encoder tạo relocation.

Linker sau đó resolve:

```text
foo → address
```

---

# 78. Position-independent code

Backend/ABI phải hỗ trợ:

```text
PIC
PIE
static
dynamic
```

tùy target.

Đặc biệt:

```text
.so
.dll
.dylib
```

sẽ cần relocation model khác executable static.

---

# 79. TLS lowering

TLS có thể dùng:

```text
target TLS instruction/model
```

không phải generic function call nếu target có native support.

---

# 80. Backend invariants — `ALIR-20..`

### `ALIR-20`
ABI MIR is the input to target lowering.

### `ALIR-21`
Axiom LIR remains semantically equivalent to ABI MIR.

### `ALIR-22`
Axiom LIR does not reintroduce source-level ownership or capability semantics.

### `ALIR-23`
Compiler-only ownership/capability metadata may be erased after verification.

### `ALIR-24`
Observable Drop behavior must remain represented until lowered into executable cleanup.

### `ALIR-25`
LIR uses virtual registers before physical register allocation.

### `ALIR-26`
Virtual registers have target-compatible register classes.

### `ALIR-27`
Instruction selection must preserve observable semantics.

### `ALIR-28`
Target legalization may expand one abstract operation into multiple machine operations.

### `ALIR-29`
Unsupported native-width operations must be lowered without changing semantics.

### `ALIR-30`
Floating-point transformations must respect the selected floating-point semantic profile.

### `ALIR-31`
SIMD transformations require valid target feature support.

### `ALIR-32`
Target features must never be used unless the compilation target guarantees them.

### `ALIR-33`
Addressing modes are target-specific implementation details.

### `ALIR-34`
Implicit machine operands such as flags must be explicitly represented in Machine IR dependencies.

### `ALIR-35`
SSA phi nodes must be eliminated before final machine emission.

### `ALIR-36`
Register allocation must preserve all data and control dependencies.

### `ALIR-37`
Spills must preserve value semantics and lifetime semantics.

### `ALIR-38`
Rematerialization may replace spills only when semantic equivalence is proven.

### `ALIR-39`
Stack slots are distinct from dynamic allocation.

### `ALIR-40`
Tail calls are legal only when ABI and cleanup conditions permit them.

### `ALIR-41`
Atomic operations must preserve their specified memory ordering.

### `ALIR-42`
Volatile operations must remain observable according to their contract.

### `ALIR-43`
Compiler barriers and CPU fences are distinct operations.

### `ALIR-44`
Inline assembly must declare required inputs, outputs, clobbers, and memory effects.

### `ALIR-45`
Undeclared inline-assembly effects cannot be silently assumed safe by the optimizer.

### `ALIR-46`
Calling conventions determine argument, return, and clobber behavior.

### `ALIR-47`
Caller-saved and callee-saved registers must be respected.

### `ALIR-48`
Instruction scheduling must preserve semantic dependencies.

### `ALIR-49`
Instruction scheduling must preserve atomic, volatile, synchronization, and foreign-call constraints.

### `ALIR-50`
Machine IR must preserve debug provenance.

### `ALIR-51`
Prologue and epilogue generation must satisfy target ABI requirements.

### `ALIR-52`
Unwind metadata must correspond to the generated stack frame.

### `ALIR-53`
Abort-only panic configurations may omit unnecessary unwind machinery.

### `ALIR-54`
Runtime components are never linked solely because backend features exist.

### `ALIR-55`
Machine encoding is separate from object-file generation.

### `ALIR-56`
Relocations are explicit data structures, not hidden encoder behavior.

### `ALIR-57`
Backend optimizations must remain target-semantics preserving.

### `ALIR-58`
CPU backends must not be required to model GPU execution semantics.

### `ALIR-59`
WASM and GPU targets may use specialized LIR/backend pipelines while sharing Axiom semantic stages.

### `ALIR-60`
The same verified semantic program must remain valid across supported targets.

### `ALIR-61`
Target-specific optimization may change performance and representation but not Axiom semantics.

### `ALIR-62`
Register allocation must not change observable program behavior.

### `ALIR-63`
Machine-level optimization must not introduce undefined behavior absent from Axiom semantics.

### `ALIR-64`
Generated machine code must satisfy the selected ABI.

### `ALIR-65`
The backend must preserve source-to-machine mapping where debug information is requested.

### `ALIR-66`
Machine encoding must produce deterministic output for the same compiler configuration and target.

### `ALIR-67`
Object-format details remain outside the machine encoder.

### `ALIR-68`
Backend architecture must permit multiple independent target implementations.

### `ALIR-69`
Axiom's native compiler must not require LLVM/Clang/GCC for final machine-code generation.

### `ALIR-70`
The backend must support eventual self-hosting entirely within Axiom.

---

# 81. Kiến trúc compiler hiện tại đã gần chạm “machine compiler”

Sau BOOTSTRAP-109, pipeline đã thành:

```text
                   AXIOM LANGUAGE
                         │
                         ▼
                 ┌──────────────┐
                 │   Frontend   │ 103
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │ Type System  │ 104
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │  HIR → MIR   │ 105
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │ Verification │ 106
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │    OptIR     │ 107
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │ ABI Lowering │ 108
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │    LIR       │ 109
                 └──────┬───────┘
                        ▼
                  Machine Code
```

Đây là **compiler core thực sự**, không còn chỉ là language specification.

---

# BOOTSTRAP-110 — Object Writer, Linker & Native Binary Generation

Bước kế tiếp hợp lý là đi nốt đoạn cuối:

```text
Machine Code
    ↓
ObjectFile
    ↓
Symbol Table
    ↓
Relocations
    ↓
Section Layout
    ↓
Link Graph
    ↓
Dead Stripping
    ↓
Library Resolution
    ↓
TLS / Imports / Exports
    ↓
Executable / Shared Library
```

và sẽ khóa native output cho:

- **Windows PE/COFF → `.exe`, `.dll`**
- **Linux/Unix ELF → executable, `.so`**
- **macOS/iOS Mach-O**
- **WASM**
- static libraries
- dynamic libraries
- symbol/export/import
- relocation
- TLS
- PIE/PIC
- entry point
- startup code
- linker script tương đương nếu cần
- static runtime component selection
- dead stripping
- COMDAT/generic deduplication
- reproducible linking
- cuối cùng là **Axiom tự viết Object Writer + Linker**, không cần LLVM/LLD trong compiler production.