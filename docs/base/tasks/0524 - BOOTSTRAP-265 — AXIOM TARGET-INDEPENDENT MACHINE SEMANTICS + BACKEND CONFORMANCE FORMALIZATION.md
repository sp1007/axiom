# BOOTSTRAP-265 — AXIOM TARGET-INDEPENDENT MACHINE SEMANTICS + BACKEND CONFORMANCE FORMALIZATION

**TRẠNG THÁI: FROZEN / COMPLETED**

Task này đóng lại một khoảng trống quan trọng: chúng ta đã có nhiều backend, nhưng cần một **formal contract** để compiler biết chính xác một LIR operation được phép biến đổi thành machine code như thế nào và làm sao chứng minh backend không làm thay đổi semantics.

Mục tiêu:

> **Backend được tự do chọn instruction sequence, nhưng không được tự do chọn semantics.**

---

# 1. Ba tầng semantics

Axiom backend chính thức có ba tầng:

```text
Semantic Level
      │
      ▼
Axiom LIR Semantics
      │
      ▼
Machine Semantics
      │
      ▼
Target Encoding
```

Trong đó:

```text
Axiom LIR
```

là **semantic contract của backend**.

Còn:

```text
x86 instruction
ARM instruction
RV instruction
WASM instruction
```

là implementation.

---

# 2. Backend không được thay đổi semantics

Ví dụ:

```text
v3 = add.i32 v1, v2
```

có semantic:

```text
v3 = AxiomIntegerAdd(v1, v2)
```

x86 có thể:

```text
add
```

ARM:

```text
add
```

RISC-V:

```text
add
```

WASM:

```text
i32.add
```

nhưng cả bốn phải thực hiện cùng semantic operation.

---

# 3. Machine instruction không phải semantic primitive của Axiom

Không được thiết kế:

```text
LIR.ADD_X86
LIR.ADC_ARM
LIR.AMO_RV
```

trong common LIR.

Thay vào đó:

```text
LIR.ADD
LIR.ATOMIC_RMW
LIR.LOAD
LIR.STORE
```

---

# 4. Target backend contract

Chuẩn hóa thành:

```text
trait TargetBackend {
    target_spec()
    lower_abi()
    legalize()
    select()
    allocate()
    lower_frame()
    lower_memory()
    lower_atomic()
    lower_tls()
    lower_control_flow()
    schedule()
    verify()
    encode()
    emit_object()
}
```

Đây là **compiler-internal trait**, không phải Axiom Core trait.

---

# 5. Mỗi backend có TargetSpec

```text
TargetSpec {
    target_id
    architecture
    os
    environment
    abi
    object_format
    pointer_width
    endianness
    data_layout
    calling_conventions
    cpu_features
    simd_features
    atomic_features
    tls_model
    unwind_model
    memory_model
    runtime_profile
}
```

---

# 6. TargetSpec là dữ liệu

Frontend không được hard-code:

```text
if x86
if arm
if riscv
if wasm
```

Thay vào đó:

```text
target.query(feature)
target.query(type_width)
target.query(abi)
```

---

# 7. LIR operation contract

Mỗi LIR operation phải định nghĩa:

```text
OperationContract {
    inputs
    outputs
    types
    effects
    memory_effect
    control_effect
    trap_behavior
    atomic_ordering
    target_requirements
    legality
}
```

---

# 8. Ví dụ ADD

```text
ADD {
    lhs: Integer
    rhs: Integer
    result: Integer

    effects: Pure
    trap: None
}
```

---

# 9. Ví dụ LOAD

```text
LOAD {
    address
    type
    alignment
    volatility
    memory_order
}
```

Semantic contract bao gồm:

```text
initialization
provenance
access permission
alignment
width
representation
```

---

# 10. Ví dụ ATOMIC RMW

Không được coi:

```text
atomic_add
```

là một `LOAD + ADD + STORE`.

Semantic primitive là:

```text
ATOMIC_RMW
```

vì concurrency semantics khác hoàn toàn.

---

# 11. Effect preservation

Mỗi lowering phải bảo toàn:

```text
Read
Write
Allocate
Deallocate
Drop
Atomic
Volatile
IO
Panic
Synchronize
Foreign
```

---

# 12. Pure operation

Nếu:

```text
ADD
```

là pure thì compiler có thể:

```text
CSE
GVN
constant fold
reassociate
vectorize
```

nếu numeric semantics cho phép.

---

# 13. Volatile

Ví dụ:

```text
volatile_load
```

không được biến thành ordinary:

```text
load
```

chỉ vì machine instruction trông giống nhau.

---

# 14. Atomic

Tương tự:

```text
atomic_load(Acquire)
```

không được hạ thành:

```text
load
```

nếu làm mất ordering.

---

# 15. Trap semantics

Một operation có thể có:

```text
TrapBehavior {
    Never
    DefinedTrap
    TargetTrapMapped
    Panic
    Unreachable
}
```

---

# 16. Trap ≠ panic

Ví dụ WASM:

```text
unreachable
```

không tự động có nghĩa là Axiom panic.

Backend phải map đúng profile.

---

# 17. Target legalization

Một operation có thể:

```text
LIR operation
      ↓
supported directly
```

hoặc:

```text
LIR operation
      ↓
legal expansion
      ↓
multiple operations
```

---

# 18. Legal expansion

Ví dụ target không hỗ trợ một atomic width:

```text
Atomic<T>
```

Backend có thể:

```text
legal expansion
```

nếu vẫn bảo toàn semantics.

Nếu không thể:

```text
compile-time rejection
```

---

# 19. Không được silent weakening

Không được:

```text
unsupported atomic
        ↓
ordinary load/store
```

---

# 20. Instruction selection

Sau legalization:

```text
LIR
 ↓
Legal LIR
 ↓
Instruction Selection
```

---

# 21. Instruction selector

Selector chỉ được chọn instruction sequence thuộc:

```text
TargetInstructionSet
```

và thỏa:

```text
OperationContract
```

---

# 22. Instruction sequence semantics

Mỗi instruction sequence có:

```text
MachineEffect
```

Compiler cần biết sequence đó thực hiện:

```text
reads
writes
register effects
memory effects
control effects
flags
special registers
traps
```

---

# 23. FLAGS

x86 có flags.

Axiom machine semantic layer phải biểu diễn:

```text
ConditionValue
```

hoặc:

```text
CompareResult
```

thay vì bắt mọi backend phải có FLAGS.

---

# 24. ARM

ARM có condition flags nhưng backend có thể dùng:

```text
cmp
b.eq
```

hoặc materialize boolean.

---

# 25. RISC-V

RISC-V có thể:

```text
slt
beq
bne
```

mà không cần FLAGS register.

---

# 26. WASM

WASM:

```text
i32.eq
i32.lt_s
```

trả trực tiếp boolean.

---

# 27. Đây là bằng chứng LIR đúng

Common semantic:

```text
compare(a,b) → condition
```

Target implementation:

```text
x86 → flags
ARM → flags
RV64 → register boolean / branch
WASM → i32 boolean
```

---

# 28. Register model

Backend-specific:

```text
RegisterFile
```

không xuất hiện trong Axiom LIR.

---

# 29. WASM exception

WASM không có register allocation kiểu native.

Thay vào đó:

```text
locals
operand stack
```

Nhưng vẫn implement cùng semantic LIR.

---

# 30. Memory model contract

Mỗi backend phải implement:

```text
MemoryModelContract
```

bao gồm:

```text
load
store
atomic
volatile
fence
ordering
address space
alignment
```

---

# 31. Endianness

Semantic integer value độc lập endianness.

Memory representation:

```text
byte order
```

là TargetSpec.

---

# 32. Native little-endian

x86/ARM/RV64 hiện đại thường little-endian.

Nhưng Core không được phụ thuộc điều đó.

---

# 33. WASM

WASM linear memory cũng có byte ordering được định nghĩa theo WASM semantics.

Backend vẫn giữ abstraction.

---

# 34. Alignment contract

Mỗi load/store:

```text
required_alignment
```

Backend phải bảo đảm.

Nếu target hỗ trợ unaligned:

```text
legal
```

Nếu không:

```text
expand
```

hoặc reject.

---

# 35. Addressing

Axiom LIR:

```text
address(base, offset, scale)
```

không được giả định target hỗ trợ scale addressing.

---

# 36. x86

Có thể:

```text
base + index*scale + displacement
```

---

# 37. ARM

Có thể cần:

```text
add
load
```

hoặc addressing mode thích hợp.

---

# 38. RISC-V

Có thể:

```text
addi
load
```

---

# 39. WASM

Có thể:

```text
offset immediate
```

với linear memory.

---

# 40. Semantics vẫn giống nhau

Đây chính là lý do address calculation phải ở LIR abstraction.

---

# 41. Control flow contract

LIR hỗ trợ:

```text
Block
Branch
ConditionalBranch
Switch
Return
Call
TailCall
Trap
Unreachable
```

---

# 42. Target differences

Native:

```text
jump
conditional jump
```

WASM:

```text
br
br_if
br_table
```

---

# 43. Structured control flow

WASM backend có:

```text
CFGStructurer
```

nhưng không được đẩy requirement này vào LIR.

---

# 44. Calls

Semantic:

```text
CALL(function, args)
```

Target-specific:

```text
x86 → call
ARM → bl
RV64 → jal/jalr
WASM → call
```

---

# 45. Indirect calls

Semantic:

```text
CALL_INDIRECT
```

Target-specific:

```text
x86 → indirect call
ARM → blr
RV → jalr
WASM → call_indirect / call_ref
```

---

# 46. Tail call

Nếu Axiom semantic contract cho phép tail call:

```text
TAILCALL
```

Target có thể:

```text
native tail jump
```

hoặc:

```text
WASM return_call
```

nếu feature available.

Nếu target không hỗ trợ:

```text
legalize
```

nếu semantics cho phép.

---

# 47. ABI contract

ABI lowering là target-specific.

```text
Axiom Type
   ↓
ABI Classification
   ↓
Physical Arguments
   ↓
Physical Return
```

---

# 48. Aggregate return

Ví dụ struct:

```text
Point
```

có thể:

```text
register return
```

hoặc:

```text
sret
```

tùy target ABI.

---

# 49. Programmer không cần biết

Source:

```text
fn make_point() -> Point
```

không thay đổi.

---

# 50. Calling convention

Axiom internal:

```text
AxiomABI
```

và:

```text
C
System
WASM
Platform
```

là các ABI contracts khác nhau.

---

# 51. Register allocation

Sau instruction selection:

```text
VirtualRegister
       ↓
PhysicalRegister
```

hoặc WASM local.

---

# 52. Register allocation correctness

Phải bảo đảm:

```text
no conflicting live values
no illegal register
no clobbered live value
ABI constraints
special-register constraints
```

---

# 53. Spill

Nếu không đủ register:

```text
virtual register
      ↓
stack slot
```

---

# 54. Spill semantics

Spill/reload không được thay đổi:

```text
ownership
capability
drop
atomicity
volatile
```

---

# 55. Stack slots

Machine stack slot là implementation detail.

Nó không phải Axiom semantic `local`.

---

# 56. Escape

Một Axiom local có thể:

```text
register
stack
heap
eliminated
```

tùy optimization.

---

# 57. Frame lowering

Backend xác định:

```text
stack size
alignment
callee-saved
return address
unwind
TLS
shadow space
```

---

# 58. Windows x64

Có ABI-specific constraints như shadow space.

Không được đưa chúng vào Core.

---

# 59. ARM64/RV64

ABI frame rules khác.

---

# 60. WASM

Không có native stack frame ABI tương tự; backend representation khác.

---

# 61. Machine verifier

Đây là lớp bắt buộc:

```text
Machine IR
   ↓
MachineVerifier
   ↓
Encoder
```

---

# 62. MachineVerifier phải kiểm tra

```text
register legality
instruction legality
operand types
immediate ranges
memory width
alignment
atomic semantics
feature availability
branch targets
calling convention
stack/frame
special registers
relocations
```

---

# 63. WASM verifier

Kiểm tra:

```text
stack typing
block signatures
locals
tables
memory
function signatures
branch depth
feature flags
```

---

# 64. Không encoder trước verifier

Invariant:

```text
VERIFY → ENCODE
```

không:

```text
ENCODE → hope it is valid
```

---

# 65. Object verifier

Sau machine encoding:

```text
MachineCode
 ↓
AxiomObject
 ↓
ObjectVerifier
```

---

# 66. ObjectVerifier

Kiểm tra:

```text
symbols
relocations
section references
imports
exports
TLS
debug ranges
unwind
architecture
ABI
```

---

# 67. Linker verifier

Sau linking:

```text
FinalBinaryVerifier
```

kiểm tra:

```text
entry point
imports
relocations
sections
permissions
architecture
ABI
runtime dependencies
```

---

# 68. Semantic equivalence

Axiom định nghĩa:

```text
ObservableBehavior(P)
```

bao gồm:

```text
return values
Result
panic
termination
I/O
volatile
atomic
synchronization
FFI
external resources
```

---

# 69. Backend correctness

Với chương trình hợp lệ:

```text
Compile(P, TargetA)
```

và:

```text
Compile(P, TargetB)
```

phải có observable behavior tương đương trong các phần semantics mà cả hai target/profile hỗ trợ.

---

# 70. Không yêu cầu binary giống nhau

Ví dụ:

```text
x86:
    5 instructions

ARM:
    4 instructions

RV64:
    6 instructions

WASM:
    8 instructions
```

hoàn toàn hợp lệ.

---

# 71. Không yêu cầu performance giống nhau

Backend được tối ưu theo target.

---

# 72. Không yêu cầu layout giống nhau

Trừ khi source/ABI explicit yêu cầu:

```text
@repr(C)
@abi(stable)
```

---

# 73. Conformance matrix

Compiler phải có test matrix:

| Semantic area | x86-64 | ARM64 | RV64 | WASM32 | WASM64 |
|---|---:|---:|---:|---:|---:|
| integers | ✓ | ✓ | ✓ | ✓ | ✓ |
| floats | ✓ | ✓ | ✓ | ✓ | ✓ |
| structs | ✓ | ✓ | ✓ | ✓ | ✓ |
| enums | ✓ | ✓ | ✓ | ✓ | ✓ |
| ownership | ✓ | ✓ | ✓ | ✓ | ✓ |
| Drop | ✓ | ✓ | ✓ | ✓ | ✓ |
| views | ✓ | ✓ | ✓ | ✓ | ✓ |
| atomics | ✓ | ✓ | ✓ | feature | feature |
| async | ✓ | ✓ | ✓ | ✓ | ✓ |
| closures | ✓ | ✓ | ✓ | ✓ | ✓ |
| FFI | ✓ | ✓ | ✓ | ✓ | ✓ |
| SIMD | ✓ | ✓ | ✓ | feature | feature |
| TLS | ✓ | ✓ | ✓ | profile | profile |

---

# 74. Semantic test

Ví dụ:

```text
fn test() -> i32 {
    let a = 10
    let b = 20
    a + b
}
```

Không nên chỉ có assembly golden test.

Phải có:

```text
reference interpreter = 30
MIR interpreter       = 30
x86                   = 30
ARM64                 = 30
RV64                  = 30
WASM32                = 30
WASM64                = 30
```

---

# 75. Ownership test

Ví dụ semantic test:

```text
struct Resource {
    ...
}
```

Kiểm tra:

```text
exactly once Drop
```

trên tất cả backend.

---

# 76. Alias test

Kiểm tra:

```text
view
mut_view
disjoint fields
overlap rejection
```

không phụ thuộc backend.

---

# 77. Atomic litmus tests

Dùng các concurrency litmus tests để kiểm tra:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

---

# 78. Async tests

Kiểm tra:

```text
await suspension
state preservation
drop future
Send across await
```

---

# 79. FFI tests

Kiểm tra:

```text
calling convention
aggregate ABI
pointer representation
ownership
error ABI
```

---

# 80. Differential backend testing

Một test program:

```text
P
```

được compile:

```text
P → x86
P → ARM
P → RV
P → WASM
```

và so sánh observable result.

---

# 81. Random program generation

Test generator có thể tạo:

```text
arithmetic
struct
enum
match
closures
iterators
ownership
views
async
concurrency
```

---

# 82. Metamorphic testing

Ví dụ:

```text
x + 0
```

và:

```text
x
```

nếu semantics đảm bảo equivalence.

Sau đó compile cả hai target.

---

# 83. Translation validation

Mỗi optimization có:

```text
Before
After
```

và verifier xác nhận semantic equivalence hoặc preserved invariants.

---

# 84. Backend translation validation

Có thể kiểm tra:

```text
LIR
 ↓
Machine IR
```

bằng symbolic/interpretive semantics cho subset.

---

# 85. Machine interpreter

Nên có:

```text
ax-machine-ref
```

hoặc target-specific execution model phục vụ compiler testing.

Không nhất thiết là emulator hoàn chỉnh.

---

# 86. WASM reference

Có thể chạy `.wasm` bằng reference engine trong CI, nhưng compiler correctness không được phụ thuộc hoàn toàn vào engine bên ngoài.

---

# 87. Golden assembly

Vẫn hữu ích, nhưng chỉ để kiểm tra:

```text
code quality
instruction selection
size
ABI
optimization
```

không phải semantic authority.

---

# 88. Performance conformance

Tách khỏi correctness:

```text
Semantic Conformance
        ≠
Performance Benchmark
```

---

# 89. Size conformance

Tương tự:

```text
Binary Size
```

không phải correctness.

---

# 90. Reproducibility

Cùng:

```text
source
target
compiler semantic version
codegen version
features
profile
dependencies
comptime inputs
```

phải tạo artifact deterministic trong reproducible mode.

---

# 91. Backend cache identity

```text
BackendCacheKey {
    TargetId
    TargetFeatures
    ABI
    SemanticFingerprint
    CodegenFingerprint
    OptimizationProfile
}
```

---

# 92. Backend plugin architecture

Trong tương lai compiler có thể:

```text
builtin backend
```

hoặc:

```text
backend module
```

nhưng backend vẫn phải implement:

```text
TargetBackend Contract
```

---

# 93. Không cho backend thay đổi frontend semantics

Backend không được định nghĩa:

```text
ownership
trait resolution
Drop rules
type inference
```

---

# 94. Backend chỉ implement physical realization

```text
semantic fact
      ↓
physical implementation
```

---

# 95. Target-specific intrinsic

Intrinsic phải có:

```text
semantic definition
target requirements
fallback hoặc explicit unsupported
effects
safety contract
```

---

# 96. Ví dụ CPU intrinsic

```text
@intrinsic("x86.something")
```

không được trở thành Core semantic primitive.

Nó là target extension.

---

# 97. Inline assembly

`asm` phải khai báo:

```text
inputs
outputs
clobbers
memory effects
volatile
target
```

---

# 98. Unsafe

Inline assembly là unsafe/system territory.

---

# 99. Machine code verifier

Không tin hoàn toàn vào programmer-supplied asm metadata.

Compiler phải kiểm tra những gì có thể kiểm tra.

---

# 100. Backend failure

Backend không được tạo binary “có vẻ chạy được”.

Các trường hợp:

```text
unsupported
illegal
ABI conflict
feature unavailable
register allocation failure
relocation impossible
```

→ diagnostic có cấu trúc.

---

# 101. Target capability query

Compiler API:

```text
supports(operation)
supports(feature)
supports(type)
supports(atomic_width)
supports(vector_shape)
supports(abi)
```

---

# 102. Legalization result

Chuẩn hóa:

```text
Legal
Expanded
Conditional
Unsupported
```

---

# 103. Conditional

Ví dụ:

```text
SIMD
```

có thể legal nếu:

```text
TargetFeature::SIMD
```

---

# 104. Multi-versioning

Compiler có thể tạo:

```text
foo_baseline
foo_avx2
foo_avx512
```

và dispatch theo target feature.

---

# 105. Semantics không thay đổi

Các implementation phải tương đương.

---

# 106. CPU dispatcher

Dispatch runtime chỉ được dùng khi explicit/runtime profile cho phép.

---

# 107. WASM feature dispatch

Có thể compile artifact variants:

```text
baseline
simd
threads
```

nhưng platform loading contract phải rõ ràng.

---

# 108. Linker boundary

Backend không tự quyết định toàn bộ linking.

```text
Backend
  ↓
AxiomObject
  ↓
Linker
```

---

# 109. Object format độc lập ISA semantics

PE/ELF/Mach-O/WASM đều là serialization/linking format.

---

# 110. Compiler architecture cuối cùng

```text
                    AXIOM SOURCE
                         │
                         ▼
                  Semantic Compiler
                         │
                         ▼
                    Verified MIR
                         │
                         ▼
                       OptIR
                         │
                         ▼
                      ABI MIR
                         │
                         ▼
                      Axiom LIR
                         │
              ┌──────────┴──────────┐
              │ TargetBackend       │
              │ Contract            │
              └──────────┬──────────┘
                         │
       ┌─────────┬───────┼───────┬─────────┐
       ▼         ▼       ▼       ▼         ▼
     x86-64    ARM64    RV64   WASM32    WASM64
       │         │       │       │         │
       ▼         ▼       ▼       ▼         ▼
   Machine IR Machine IR ...  WASM IR   WASM IR
       │         │       │       │         │
       └─────────┴───────┼───────┴─────────┘
                         ▼
                    Machine Verify
                         │
                         ▼
                       Encoder
                         │
                         ▼
                    AxiomObject
                         │
                         ▼
                       Linker
                         │
                         ▼
                   Final Artifact
```

---

# 111. Formal backend invariant

Đây là invariant quan trọng nhất của task:

```text
ABACKEND-61
For every Verified Axiom LIR program P and supported target T,
the generated target program must preserve all observable Axiom semantics
defined for the selected target profile.
```

---

# 112. Bộ invariants `ABACKEND-61..100`

```text
ABACKEND-61
Every LIR operation has an explicit semantic contract.

ABACKEND-62
Target lowering must preserve LIR observable behavior.

ABACKEND-63
Instruction selection cannot redefine Axiom semantics.

ABACKEND-64
Legalization may expand operations only when semantics are preserved.

ABACKEND-65
Unsupported operations must be rejected or legally expanded.

ABACKEND-66
Unsupported atomics must never silently become ordinary memory operations.

ABACKEND-67
Volatile semantics must be preserved through all backend stages.

ABACKEND-68
Memory ordering must be preserved through all backend stages.

ABACKEND-69
Trap behavior must be explicitly modeled.

ABACKEND-70
A target trap must not silently replace an Axiom panic semantic.

ABACKEND-71
ABI lowering cannot alter source-level type semantics.

ABACKEND-72
Aggregate ABI classification is target-specific.

ABACKEND-73
Register allocation must be semantically transparent.

ABACKEND-74
Spilling must preserve ownership and memory semantics.

ABACKEND-75
Frame lowering must preserve calling and unwinding semantics.

ABACKEND-76
Address lowering must preserve provenance and access semantics.

ABACKEND-77
Target addressing modes are implementation details.

ABACKEND-78
Control-flow lowering must preserve semantic CFG behavior.

ABACKEND-79
WASM structured control flow is backend representation only.

ABACKEND-80
Machine instruction sequences must declare their machine-visible effects.

ABACKEND-81
Machine verification must precede encoding.

ABACKEND-82
Object verification must follow encoding.

ABACKEND-83
Linking must preserve symbol and relocation semantics.

ABACKEND-84
Target feature use must be explicitly declared.

ABACKEND-85
Unavailable target features cannot be emitted.

ABACKEND-86
Target-specific optimizations cannot weaken safety guarantees.

ABACKEND-87
Target-specific optimizations cannot alter observable behavior.

ABACKEND-88
Different physical layouts may represent the same semantic type.

ABACKEND-89
Different instruction sequences may represent the same LIR semantics.

ABACKEND-90
Assembly golden tests are not the semantic authority.

ABACKEND-91
Reference and differential execution are semantic validation mechanisms.

ABACKEND-92
Backend conformance tests are target-independent at the semantic level.

ABACKEND-93
All supported targets must pass common semantic conformance tests.

ABACKEND-94
Backend cache identity includes target and code-generation facts.

ABACKEND-95
Reproducible backend compilation is deterministic.

ABACKEND-96
Backend diagnostics must identify unsupported target requirements.

ABACKEND-97
Backend implementation details must not leak into Core syntax.

ABACKEND-98
Adding a target must not require changing existing Core semantics.

ABACKEND-99
Axiom LIR is the semantic portability boundary of the native compiler.

ABACKEND-100
No target backend is permitted to become a second semantic compiler.
```

---

# 113. Kết quả kiến trúc rất quan trọng

Sau 265, ta có thể tuyên bố một nguyên tắc mạnh:

> **Frontend quyết định chương trình có nghĩa gì. Backend chỉ quyết định thực hiện nghĩa đó bằng phần cứng/VM nào.**

Điều này giúp Axiom tránh một lỗi rất phổ biến ở các compiler architecture:

```text
language semantics
      ↓
bị ảnh hưởng bởi
      ↓
ISA quirks
```

Axiom đi theo hướng ngược lại:

```text
Language Semantics
       ↓
Verified MIR
       ↓
Target-independent optimization
       ↓
Axiom LIR
       ↓
Target realization
```

---

# 114. Backend hiện đã đủ nền tảng để chuyển sang phần khó hơn

Ta hiện đã có:

```text
x86-64
ARM64
RV64
WASM32
WASM64
```

và quan trọng hơn:

```text
TargetBackend Contract
TargetSpec
LIR semantics
Legalization
Machine verification
Object model
Cross-target conformance
```

Do đó **không nên tiếp tục thêm ISA một cách máy móc**.

Bước kế tiếp hợp lý là:

# **BOOTSTRAP-266 — AXIOM DEBUG INFO, UNWINDING, STACK TRACE & SOURCE-TO-MACHINE PROVENANCE**

Task này sẽ giải quyết một vấn đề thực tế cực quan trọng của một compiler native:

```text
Axiom source
    ↓
AST
    ↓
HIR
    ↓
MIR
    ↓
OptIR
    ↓
ABI MIR
    ↓
LIR
    ↓
Machine IR
    ↓
machine address
```

Khi chương trình crash hoặc debugger dừng tại một instruction, compiler phải có khả năng đi **ngược lại**:

```text
0x7FF... 
   ↓
function
   ↓
inlined function
   ↓
MIR instruction
   ↓
source statement
   ↓
file:line:column
   ↓
local variable / type / ownership state
```

và đồng thời xử lý:

- DWARF
- PDB/CodeView
- Mach-O debug
- WASM DWARF/source maps
- inline call stack
- optimized-out variables
- variable location changes
- stack unwinding
- panic stack trace
- async state-machine debugging
- closure debugging
- generated/comptime source mapping
- FFI frames
- native ↔ Axiom mixed stack
- zero-cost debug metadata stripping
- deterministic debug artifacts.

Đây là bước cần thiết trước khi đi sâu tiếp vào **link-time codegen / final native image / self-hosted compiler debugging**.