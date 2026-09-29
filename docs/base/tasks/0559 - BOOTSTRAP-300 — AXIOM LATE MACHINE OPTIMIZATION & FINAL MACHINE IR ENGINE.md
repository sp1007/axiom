# BOOTSTRAP-300 — AXIOM LATE MACHINE OPTIMIZATION & FINAL MACHINE IR ENGINE
**FROZEN / COMPLETED**

## 1. Mục tiêu

`BOOTSTRAP-300` là lớp tối ưu **cuối cùng ở Machine IR**, chạy sau:

```text
Instruction Selection
        ↓
Register Allocation
        ↓
Machine Scheduling
        ↓
Late Machine Optimization     ← 300
        ↓
Final Machine IR
        ↓
Instruction Encoding
```

Nhiệm vụ chính:

- peephole optimization;
- machine instruction combining;
- redundant move elimination;
- late constant folding;
- branch simplification;
- compare/branch fusion;
- address-mode formation;
- instruction shortening;
- target-specific idiom recognition;
- loại bỏ instruction thừa sau register allocation;
- sửa các sequence do spill/reload tạo ra;
- tối ưu instruction sequence theo hardware cuối cùng.

Nguyên tắc:

> **Đây là optimization cuối cùng, không phải nơi định nghĩa semantics.**

---

# 2. Tại sao cần late optimization?

Các optimization trước đó không biết chính xác:

```text
RAX
RBX
RCX
stack[24]
```

sẽ được dùng thế nào.

Sau `298–299`, compiler mới biết chính xác:

- physical registers;
- spill/reload;
- register aliases;
- instruction order;
- target constraints;
- exact machine instruction sequence.

Vì vậy một số cơ hội chỉ xuất hiện ở cuối.

Ví dụ:

```text
MOV RAX, RBX
MOV RCX, RAX
```

có thể trở thành:

```text
MOV RCX, RBX
```

Hoặc:

```text
MOV RAX, 0
ADD RBX, RAX
```

có thể loại bỏ.

---

# 3. Late Machine IR

Sau scheduling, tạo snapshot:

```text
FinalizationInput {
    machine_function
    target
    abi
    register_assignment
    frame_info
    debug_info
}
```

Kết quả:

```text
FinalMachineFunction {
    blocks
    instructions
    physical_registers
    stack_operands
    symbols
    relocations
    frame_info
    debug_info
    encoding_hints
}
```

Đây vẫn là **IR**, chưa phải byte encoding.

---

# 4. Không được quay lại Semantic MIR

Late optimizer không được tự suy luận lại:

- ownership;
- lifetime;
- capability;
- type semantics;
- trait resolution;
- generic semantics.

Các facts cần thiết phải đến từ:

```text
Verified MIR
    ↓
OptIR
    ↓
Machine IR
```

và các proof/provenance tương ứng.

---

# 5. Các loại optimization

```text
LateMachineOptimizer
├── Peephole
├── MoveOptimization
├── CopyPropagation
├── ConstantOptimization
├── CompareBranchFusion
├── AddressModeFormation
├── BranchOptimization
├── LoadStoreOptimization
├── SpillReloadOptimization
├── InstructionCombine
├── TargetIdioms
├── InstructionShortening
└── FinalCleanup
```

---

# 6. Peephole Optimization

Peephole nhìn một cửa sổ instruction nhỏ:

```text
I0
I1
I2
I3
```

và tìm sequence tương đương nhưng tốt hơn.

Ví dụ:

```text
MOV RAX, RBX
MOV RBX, RAX
```

nếu semantics cho phép có thể loại bỏ/collapse.

Hoặc:

```text
ADD RAX, 0
```

→ loại bỏ nếu flags/observable effects không bị thay đổi.

---

# 7. Không được dùng peephole kiểu “text replacement”

Không làm:

```text
if string == "MOV X, 0":
    replace(...)
```

Thay vào đó:

```text
Pattern
    ↓
Machine semantics
    ↓
Legality proof
    ↓
Target cost
    ↓
Rewrite
```

Pattern phải typed:

```text
MachinePattern {
    operands
    register_constraints
    flags
    memory_effects
    implicit_effects
}
```

---

# 8. Flags phải được coi là giá trị machine-level

Đây là điểm rất quan trọng trên x86 và một số ISA.

Ví dụ:

```text
CMP RAX, RBX
JE label
```

không thể tùy tiện thay bằng sequence khác nếu sequence đó thay đổi:

```text
FLAGS
```

mà instruction tiếp theo sử dụng.

Machine IR phải biểu diễn:

```text
ImplicitDef(FLAGS)
ImplicitUse(FLAGS)
```

Late optimizer phải track chúng.

---

# 9. Dead Flag Definition

Nếu:

```text
ADD RAX, RBX
```

chỉ tồn tại để tạo FLAGS nhưng không có instruction nào dùng FLAGS, compiler có thể chọn instruction tương đương không tạo flags nếu target có.

Hoặc chọn instruction khác rẻ hơn.

Nhưng:

```text
ADD
```

và:

```text
LEA
```

không hoàn toàn tương đương nếu FLAGS observable.

Do đó:

```text
FlagLiveness
```

là một analysis riêng.

---

# 10. Compare + Branch Fusion

Ví dụ:

```text
CMP RAX, 0
JE label
```

có thể được target-specific combine thành instruction sequence tối ưu.

Hoặc:

```text
TEST RAX, RAX
JE label
```

thay cho compare với zero nếu semantics flags tương đương.

Late optimizer cần:

```text
CompareBranchRecognizer
```

và:

```text
ConditionCodeModel
```

---

# 11. Conditional Move

Một số branch nhỏ:

```text
CMP
Jcc
...
```

có thể chuyển thành:

```text
CMOVcc
```

nhưng **không được tự động làm chỉ vì số instruction ít hơn**.

Phải xét:

- branch predictability;
- latency;
- speculative execution;
- side effects;
- panic/trap;
- memory access;
- target cost.

Ví dụ một branch có thể tránh thực hiện một load có side effect. Không được biến nó thành speculative execution nếu semantics thay đổi.

---

# 12. Address Mode Formation

Một trong các tối ưu cuối quan trọng nhất.

Ví dụ:

```text
ADD RAX, RBX
LOAD RCX, [RAX]
```

target có thể hỗ trợ:

```text
LOAD RCX, [base + index]
```

hoặc:

```text
LOAD RCX, [RAX + RBX]
```

Compiler có thể combine arithmetic vào addressing mode.

Nhưng chỉ khi:

```text
address computation
```

không có observable side effect và target addressing mode hợp lệ.

---

# 13. Address Mode Model

```text
AddressExpression {
    base
    index
    scale
    displacement
    segment
}
```

Target cung cấp:

```text
TargetAddressMode {
    allowed_base
    allowed_index
    allowed_scale
    displacement_range
    alignment
}
```

Không hard-code x86 addressing mode vào generic optimizer.

---

# 14. Load/Store Combining

Ví dụ:

```text
LOAD RAX, [x]
STORE [y], RAX
```

có thể target hỗ trợ memory-to-memory operation hoặc sequence tối ưu hơn.

Nhưng compiler phải giữ:

- volatile;
- atomic;
- alignment;
- alias;
- memory ordering.

Không được biến:

```text
atomic load
```

thành:

```text
ordinary load
```

---

# 15. Redundant Move Elimination

Ví dụ:

```text
MOV RAX, RAX
```

→ loại bỏ.

Hoặc:

```text
MOV RAX, RBX
...
MOV RBX, RAX
```

có thể tối ưu nếu live-range và semantics cho phép.

Cần track:

```text
RegisterValueState
```

---

# 16. Register Copy Propagation

Sau allocation:

```text
RAX = RBX
...
use RAX
```

nếu RBX vẫn giữ cùng giá trị:

```text
use RBX
```

có thể loại bỏ MOV.

Nhưng phải xét:

```text
subregister writes
implicit defs
calls
memory
flags
```

---

# 17. Constant Materialization

Sau các transformation, có thể xuất hiện:

```text
MOV RAX, 1
MOV RBX, RAX
```

thay vì hai instruction:

```text
MOV RBX, 1
```

Late optimizer có thể combine.

Target-specific cost model quyết định:

- immediate;
- literal pool;
- constant materialization sequence;
- PC-relative constant;
- synthesized instruction.

---

# 18. Instruction Shortening

Ví dụ target có nhiều encoding:

```text
long encoding
short encoding
```

Late optimizer chọn encoding phù hợp.

Điều này đặc biệt quan trọng cho:

- x86 short branches;
- compressed RISC-V instructions;
- ARM64 instruction forms;
- WASM compact encodings.

Nhưng ở bước `300` chỉ chọn **machine form**.

Byte encoding thực tế vẫn thuộc `301+`.

---

# 19. Branch Optimization

Late branch optimizer có thể:

### Remove useless jump

```text
JMP next_block
```

→ bỏ.

### Invert branch

```text
JNE cold
JMP hot
```

có thể thành:

```text
JE hot
JMP cold
```

nếu target layout có lợi.

### Branch chaining

```text
JMP B
B:
    JMP C
```

→

```text
JMP C
```

nếu semantics cho phép.

---

# 20. Branch Relaxation Preparation

Branch encoding có thể phụ thuộc khoảng cách:

```text
short branch
long branch
```

Khoảng cách chỉ biết chính xác hơn khi code layout được quyết định.

`300` nên tạo:

```text
BranchForm {
    short
    near
    far
}
```

và đánh dấu:

```text
RelaxableBranch
```

Final encoder/layout engine sẽ quyết định byte form chính xác.

---

# 21. Spill/Reload Cleanup

`298` có thể tạo:

```text
STORE RAX, [slot]
...
LOAD RBX, [slot]
```

nhưng sau scheduling có thể phát hiện:

```text
STORE
LOAD
```

không cần thiết.

Ví dụ:

```text
STORE RAX → slot0
LOAD slot0 → RAX
```

→ loại bỏ cả hai nếu không có intervening observation.

Đây là một trong những nhiệm vụ quan trọng của `300`.

---

# 22. Spill/Reload Forwarding

Ví dụ:

```text
STORE RAX, [slot0]
LOAD [slot0], RBX
```

nếu:

```text
RAX
```

vẫn giữ giá trị và memory không bị observable:

```text
RBX = RAX
```

có thể thay thế.

Nhưng phải tôn trọng:

- volatile stack access nếu có;
- address observation;
- debug semantics;
- memory ordering.

---

# 23. Stack Slot Coalescing Late

Sau scheduling có thể phát hiện một số spill slot không overlap.

Late pass có thể merge:

```text
slot0
slot1
```

nếu frame layout chưa bị finalized.

Nếu frame đã fixed:

```text
FinalFrameLayoutLocked
```

thì không được thay đổi.

Do đó cần state:

```text
FrameState {
    Mutable
    Frozen
}
```

---

# 24. Instruction Combining

Ví dụ generic:

```text
SHL RAX, 1
ADD RAX, RBX
```

target có thể có instruction tương đương.

Hoặc:

```text
MUL x, constant_power_of_two
```

có thể combine thành shift nếu semantics chính xác.

Không dùng machine-level arithmetic assumptions trái với Axiom semantics.

Đặc biệt:

```text
checked
wrapping
saturating
```

phải được phân biệt từ các phase trước.

---

# 25. Integer Semantics

Late optimizer **không được giả định C/C++ signed-overflow UB**.

Ví dụ:

```text
checked_add
```

không thể tự biến thành:

```text
wrapping_add
```

chỉ vì instruction sequence ngắn hơn.

Tương tự:

```text
saturating_add
```

không được biến thành ordinary ADD.

Machine instruction phải giữ semantic mode.

---

# 26. Floating-Point

Không được tự ý biến:

```text
strict FP
```

thành:

```text
fast FP
```

Các phép:

```text
NaN
signed zero
rounding
exceptions
FMA
reassociation
```

phải theo FP contract đã được xác định ở các tầng trước.

Late optimizer chỉ được áp dụng:

```text
FastMathContract
```

nếu contract tồn tại.

---

# 27. Memory Optimization Boundary

`300` có thể tối ưu machine memory sequence nhưng không trở thành một MemorySSA optimizer thứ hai.

Ví dụ:

```text
LOAD
LOAD
```

nếu muốn thực hiện semantic memory optimization lớn:

```text
→ Memory Optimization Engine
```

Nếu chỉ:

```text
MOV RAX, RAX
```

hoặc:

```text
spill → reload
```

thì thuộc `300`.

Nguyên tắc:

> **Late machine optimization xử lý representation-level redundancy, không tái xây dựng semantic optimization pipeline.**

---

# 28. Security-sensitive instructions

Một số sequence có semantics security:

```text
constant-time code
barrier
serialization
speculation barrier
```

Late optimizer phải nhận:

```text
SecurityContract
```

và không được:

```text
remove barrier
combine away constant-time property
introduce data-dependent branch
```

nếu contract yêu cầu bảo toàn.

---

# 29. Debug Semantics

Late optimizer vẫn phải cập nhật:

```text
MachineDebugLocation
```

Nếu:

```text
MOV RAX, RBX
```

bị loại bỏ:

```text
source variable → RBX
```

phải được duy trì.

Không được để debugger trỏ tới register/value không còn tồn tại.

---

# 30. Patchable / Instrumented Code

Một số build mode có:

```text
sanitizer
profiling
instrumentation
hot patching
debug probes
```

Machine optimizer phải biết các instruction được đánh dấu:

```text
NonRemovable
Instrumentation
PatchPoint
Probe
```

Không được xóa hoặc reorder trái contract.

---

# 31. Target Idiom Recognition

Target backend có thể cung cấp:

```text
TargetIdiomRecognizer
```

Ví dụ:

```text
memset
memcpy
bit manipulation
population count
byte swap
rotate
CRC
AES
vector reduction
```

Nếu target có instruction đặc biệt:

```text
generic sequence
    ↓
target idiom
```

Nhưng legality phải được chứng minh trước cost.

---

# 32. CPU Target Examples

Architecture generic:

```text
compiler/backend/finalize/
```

Target extensions:

```text
x86_64:
    LEA
    TEST/CMP
    CMOV
    short branch
    BMI/BMI2
    POPCNT
    AES
    vector idioms

arm64:
    addressing modes
    conditional select
    fused operations
    load/store forms
    bitfield operations

riscv64:
    compressed forms
    addressing patterns
    bit-manipulation extensions
    vector idioms
```

Không được đưa target-specific semantics vào generic optimizer.

---

# 33. Final Machine IR Verifier

Đây là verifier cuối trước encoding.

Kiểm tra:

### Structural

```text
CFG hợp lệ
block references hợp lệ
instruction operands hợp lệ
```

### Registers

```text
physical register hợp lệ
subregister state hợp lệ
```

### Memory

```text
memory operand hợp lệ
alignment hợp lệ
address mode hợp lệ
```

### ABI

```text
call/return hợp lệ
stack alignment hợp lệ
callee-save semantics hợp lệ
```

### Flags

```text
implicit use/def hợp lệ
```

### Barriers

```text
atomic/volatile/fence semantics hợp lệ
```

### Security

```text
security contract preserved
```

### Debug

```text
debug mapping hợp lệ
```

---

# 34. Finalization Contract

```text id="w75p7g"
FinalMachineOptimizer::run(
    AllocatedMachineFunction
) -> FinalMachineFunction
```

Điều kiện đầu vào:

```text
MachineIRVerified
RegisterAllocationVerified
SchedulingVerified
```

Điều kiện đầu ra:

```text
FinalMachineIRVerified
```

Sau đó mới cho phép:

```text
InstructionEncoder
```

chạy.

---

# 35. Implementation Tree

```text id="ljt0ps"
compiler/backend/finalize/
├── mod.ax
│
├── peephole/
│   ├── pattern.ax
│   ├── matcher.ax
│   ├── rewrite.ax
│   └── window.ax
│
├── combine/
│   ├── instruction.ax
│   ├── arithmetic.ax
│   ├── compare_branch.ax
│   ├── load_store.ax
│   └── address.ax
│
├── move/
│   ├── eliminate.ax
│   ├── propagate.ax
│   └── coalesce.ax
│
├── constant/
│   ├── fold.ax
│   ├── materialize.ax
│   └── rematerialize.ax
│
├── branch/
│   ├── simplify.ax
│   ├── invert.ax
│   ├── chain.ax
│   └── relax.ax
│
├── memory/
│   ├── forwarding.ax
│   ├── spill_reload.ax
│   └── stack.ax
│
├── flags/
│   ├── liveness.ax
│   └── optimize.ax
│
├── address/
│   ├── expression.ax
│   ├── formation.ax
│   └── target.ax
│
├── idiom/
│   ├── recognizer.ax
│   └── target.ax
│
├── security/
│   └── contract.ax
│
├── debug/
│   └── mapping.ax
│
├── target/
│   ├── generic.ax
│   ├── x86_64.ax
│   ├── arm64.ax
│   ├── riscv64.ax
│   ├── wasm.ax
│   └── gpu.ax
│
├── verifier/
│   └── final.ax
│
├── diagnostics/
├── trace/
└── tests/
```

---

# 36. Implementation Order

```text
1. Final Machine IR snapshot
2. Machine instruction semantics
3. Flag liveness
4. Redundant move elimination
5. Copy propagation
6. Peephole matcher
7. Constant/materialization optimization
8. Compare/branch optimization
9. Branch cleanup
10. Address-mode formation
11. Spill/reload forwarding
12. Spill/reload elimination
13. Stack-slot late cleanup
14. Instruction combining
15. Target idiom recognition
16. Instruction shortening
17. Security-contract verification
18. Debug mapping
19. Target-specific final passes
20. Final Machine IR verifier
21. Deterministic replay/optimization trace
22. Adversarial tests
```

---

# 37. Adversarial Tests

Bắt buộc:

```text
MOV elimination
MOV chains
copy propagation
subregister moves
dead flags
live flags
CMP + branch
TEST + branch
branch inversion
branch chain
short/long branch
address formation
load/store forwarding
spill/reload elimination
spill/reload forwarding
stack-slot reuse
fixed register instruction
implicit FLAGS
atomic
volatile
fence
foreign call
panic
Drop
strict integer overflow
wrapping integer
saturating integer
strict FP
fast FP
NaN
signed zero
constant-time code
speculation barrier
debug locations
instrumentation points
GPU barrier
WASM
```

---

# 38. Invariants đóng băng

### `AFINAL-20`
Final machine optimization không thay đổi semantic program behavior.

### `AFINAL-21`
Final optimizer chỉ được biến đổi verified Machine IR.

### `AFINAL-22`
Mọi peephole transformation phải có semantic equivalence proof hoặc target-defined correctness contract.

### `AFINAL-23`
Flags là machine-level observable state khi instruction sau sử dụng chúng.

### `AFINAL-24`
Implicit register uses/defs phải được bảo toàn.

### `AFINAL-25`
Address-mode formation không được thay đổi address semantics.

### `AFINAL-26`
Atomic ordering không được bị phá.

### `AFINAL-27`
Volatile ordering không được bị phá.

### `AFINAL-28`
Compiler fence và hardware fence không được đánh đồng.

### `AFINAL-29`
Panic/trap behavior không được thay đổi.

### `AFINAL-30`
Deterministic Drop semantics không được thay đổi.

### `AFINAL-31`
FFI semantics không được thay đổi.

### `AFINAL-32`
Integer semantic mode phải được bảo toàn.

### `AFINAL-33`
Floating-point semantic mode phải được bảo toàn.

### `AFINAL-34`
Security contracts phải được bảo toàn.

### `AFINAL-35`
Instrumentation/PatchPoint/Probe không được tự ý loại bỏ.

### `AFINAL-36`
Debug provenance phải được duy trì sau transformation.

### `AFINAL-37`
Target-specific transformation phải nằm trong target backend contract.

### `AFINAL-38`
Late optimization không được tái định nghĩa ownership/capability semantics.

### `AFINAL-39`
Late optimizer không được tự tạo semantic proof từ UNKNOWN.

### `AFINAL-40`
Mọi transformation phải thông qua optimization legality contract.

### `AFINAL-41`
Failed optimization phải giữ nguyên legal input.

### `AFINAL-42`
Final Machine IR phải pass verifier trước encoding.

### `AFINAL-43`
Optimization result phải deterministic với cùng target/configuration/compiler revision.

### `AFINAL-44`
Instruction encoding không thuộc trách nhiệm của `300`.

### `AFINAL-45`
Object layout/linking không thuộc trách nhiệm của `300`.

### `AFINAL-46`
Final Machine IR phải chứa đủ thông tin để encoder không cần quay lại semantic MIR.

### `AFINAL-47`
Late optimization có thể giảm instruction count, latency, code size hoặc register/memory traffic nhưng không được đánh đổi correctness.

### `AFINAL-48`
Target cost model chỉ quyết định profitability, không quyết định legality.

### `AFINAL-49`
Machine-level optimization không được giả định UB của ngôn ngữ khác để tối ưu Axiom.

### `AFINAL-50`
Final Machine IR là representation cuối cùng trước binary encoding.

---

## Vị trí hiện tại của compiler

Sau `300`, chuỗi backend đã hoàn chỉnh về mặt kiến trúc đến ngay trước việc biến instruction thành bytes:

```text
                    AXIOM SEMANTIC
                         │
                         ▼
                    Verified MIR
                         │
                         ▼
                  Optimization / OptIR
                         │
                         ▼
                    Machine IR
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        Target Legalization   Target Features
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
     Late Machine Optimization
              │
              ▼
      FINAL MACHINE IR
              │
              ▼
        ┌──────────────┐
        │    ENCODER   │
        └──────────────┘
              │
              ▼
        Object / Binary
```

Từ đây, **`BOOTSTRAP-301` nên chuyển sang Instruction Encoding & Machine Code Emission**: thiết kế bộ mã hóa instruction tổng quát, operand encoding, immediate/displacement, relocation, branch relaxation và phát sinh bytes máy thực tế cho x86-64/ARM64/RISC-V64/WASM.