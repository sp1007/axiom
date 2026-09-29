# BOOTSTRAP-298 — AXIOM REGISTER ALLOCATION, SPILL & RELOAD ENGINE
**FROZEN / COMPLETED**

## 1. Mục tiêu

`BOOTSTRAP-298` biến **Target Machine IR với virtual registers** thành Machine IR trong đó mỗi virtual register đã được ánh xạ vào:

- physical register,
- stack slot,
- hoặc giá trị được rematerialize khi cần.

Pipeline:

```text
Machine IR
    ↓
Instruction Selection
    ↓
Target Machine IR
    ↓
Register Allocation          ← 298
    ↓
Spill / Reload
    ↓
Allocated Machine IR
    ↓
Machine Scheduling
    ↓
Register/Stack Verification
    ↓
Instruction Encoding
```

Nguyên tắc quan trọng:

> **Register allocation chỉ thay đổi nơi giá trị được lưu trữ; nó không được thay đổi semantic của chương trình.**

Đặc biệt, register allocator **không được tự ý thay đổi**:

- ownership,
- lifetime,
- alias,
- capability,
- memory ordering,
- atomic semantics,
- volatile semantics,
- ABI semantics,
- panic/unwind behavior.

---

# 2. Input / Output

### Input

```text
TargetMachineFunction {
    blocks
    machine_instructions
    virtual_registers
    register_constraints
    call_clobbers
    target_features
    frame_requirements
    debug_info
}
```

Virtual register:

```text
VirtualRegister {
    id: VRegId
    class: RegisterClass
    type: MachineType
    width: RegisterWidth
    constraints: RegisterConstraintSet
}
```

### Output

```text
AllocatedMachineFunction {
    blocks
    machine_instructions
    physical_registers
    stack_slots
    frame_info
    spills
    rematerializations
    debug_mapping
}
```

Sau bước này:

```text
vreg17
```

có thể trở thành:

```text
RAX
```

hoặc:

```text
stack_slot_3
```

hoặc:

```text
rematerialize(constant)
```

---

# 3. Không chọn một thuật toán duy nhất

Axiom không nên khóa compiler vào Linear Scan hoặc Graph Coloring.

Thiết kế:

```text
RegisterAllocationEngine
        │
        ├── FastAllocator
        │
        ├── LinearScanAllocator
        │
        ├── GraphColoringAllocator
        │
        └── AdaptiveAllocator
```

Compiler chọn allocator dựa trên:

- kích thước function,
- register pressure,
- optimization profile,
- target,
- debug/release,
- compile-time budget,
- hot/cold information.

Ví dụ:

```text
Debug / tiny function
    → Fast / Linear Scan

Normal optimization
    → Linear Scan / Hybrid

Aggressive optimization
    → Graph Coloring / Hybrid

Very high register pressure
    → Adaptive allocator
```

Điều này tránh tình trạng compiler phải dùng một allocator cực kỳ phức tạp cho mọi function.

---

# 4. Register Class

Không coi tất cả register là giống nhau.

```text
RegisterClass {
    id
    registers
    spill_class
    width
    alignment
    aliases
    allocatable
}
```

Ví dụ conceptually:

```text
GPR32
GPR64

FPR32
FPR64

SIMD128
SIMD256
SIMD512

Predicate
Mask

Special
```

Một virtual register chỉ được cấp phát vào register class hợp lệ.

Ví dụ:

```text
v1 : GPR64
v2 : SIMD128
v3 : Predicate
```

không thể:

```text
v1 → XMM0
```

nếu target không cung cấp conversion/lowering tương ứng.

---

# 5. Register Alias

Physical register có thể overlap.

Ví dụ x86:

```text
RAX
 ├── EAX
 │    ├── AX
 │    │    ├── AH
 │    │    └── AL
```

Allocator phải hiểu:

```text
RAX aliases EAX
RAX aliases AX
AX aliases AH
AX aliases AL
```

Hai allocation không được cùng tồn tại nếu chúng conflict theo target alias model.

Không hard-code logic x86 vào allocator.

```text
TargetRegisterInfo
    ↓
AliasSet
    ↓
Allocator
```

ARM64/RISC-V/WASM/GPU có register model khác nhau.

---

# 6. Live Range

Đây là nền tảng của allocation.

Mỗi virtual register được phân tích:

```text
LiveRange {
    vreg
    segments
    uses
    defs
    holes
}
```

Ví dụ:

```text
v1:

block A:
    def v1
    use v1

block B:
    use v1

block C:
    use v1
```

Không nhất thiết:

```text
live(v1) = toàn bộ A → C
```

nếu có lifetime hole.

Do đó allocator cần:

```text
LiveInterval
LiveSegment
UsePosition
DefPosition
```

để giảm register pressure.

---

# 7. Live Interval

```text
LiveInterval {
    vreg
    segments: [LiveSegment]
    uses: [UsePosition]
    weight
    spill_cost
    fixed_constraints
}
```

Ví dụ:

```text
v1: [10,20)
    [35,42)

v2: [15,30)
```

Hai interval không conflict trong khoảng:

```text
20..35
```

Allocator có thể tận dụng register đó cho virtual register khác.

---

# 8. Interference

Hai virtual register conflict khi:

```text
LiveRange(A) ∩ LiveRange(B) != ∅
```

nhưng implementation không nhất thiết phải xây full O(N²) interference graph.

Có thể dùng:

```text
Live Interval Sweep
```

cho Linear Scan.

Hoặc:

```text
Interference Graph
```

cho Graph Coloring.

Compiler nên có abstraction:

```text
InterferenceModel
```

để allocator thay đổi implementation mà không ảnh hưởng Machine IR.

---

# 9. Fixed Register Constraints

Một số instruction yêu cầu register cụ thể.

Ví dụ conceptually:

```text
instruction requires RAX
```

hoặc:

```text
result must be in RDX:RAX
```

hoặc:

```text
operand tied to result
```

Machine IR phải biểu diễn rõ:

```text
FixedRegisterConstraint
```

không để allocator phải đoán.

---

# 10. Tied Operands

Một số instruction yêu cầu:

```text
input register == output register
```

Ví dụ:

```text
v3 = op(v3, v2)
```

Machine constraint:

```text
Tie {
    input: operand_0
    output: operand_0
}
```

Allocator phải đảm bảo constraint trước khi commit allocation.

---

# 11. Early Clobber

Một output có thể ghi register trước khi tất cả input được đọc.

Do đó:

```text
output ≠ conflicting input
```

phải được biểu diễn riêng:

```text
EarlyClobber
```

Không được coi instruction như một def/use bình thường.

---

# 12. Call Clobber

Function call có:

```text
CallerSaved
CalleeSaved
```

và target-specific ABI.

Ví dụ:

```text
Call
 ↓
clobber set
```

Allocator phải đảm bảo các giá trị live qua call nằm trong:

- callee-saved register,
- stack,
- hoặc được save/restore phù hợp.

Không hard-code ABI vào allocator.

```text
TargetABI
    ↓
CallClobberInfo
    ↓
RegisterAllocator
```

---

# 13. Register Pressure

Compiler cần theo dõi:

```text
RegisterPressure {
    class
    position
    live_count
    available_count
}
```

Ví dụ:

```text
GPR:
live = 10
available = 8
```

→ cần spill hoặc rematerialization.

Register pressure cũng được cung cấp ngược cho:

- instruction scheduling,
- loop optimization,
- inlining,
- vectorization,
- machine scheduling.

Do đó:

> Register allocator không phải subsystem cô lập.

---

# 14. Spill

Khi không đủ register:

```text
v17 → stack_slot_4
```

Compiler chèn:

```text
store v17 → [stack_slot_4]
```

và trước use:

```text
load [stack_slot_4] → physical_register
```

Nhưng đây chỉ là semantic model.

Target backend quyết định instruction cụ thể.

---

# 15. Spill Slot

```text
StackSlot {
    id
    size
    alignment
    type
    lifetime
    addressability
    preferred_offset
}
```

Compiler phải reuse stack slot khi lifetime không overlap.

Ví dụ:

```text
v1 spill → slot0
v2 spill → slot1
```

Nếu:

```text
lifetime(slot0) ∩ lifetime(slot1) = ∅
```

có thể:

```text
v1 → slot0
v2 → slot0
```

giảm stack frame.

---

# 16. Spill Slot không được phá Stable Address

Đây là điểm đặc biệt quan trọng với Axiom.

Register allocation không được nhầm:

```text
spill location
```

với:

```text
semantic storage identity
```

Nếu một object có:

```text
stable_address = true
```

thì compiler không thể tùy tiện:

```text
register → stack → register
```

nếu hành động đó làm thay đổi địa chỉ quan sát được.

Do đó:

```text
RegisterAllocation
        ↓
must respect
        ↓
StorageIdentity / AddressObservation
```

Đây là lý do `register allocator` phải nhận information từ các analysis trước đó.

---

# 17. Spill không được tạo alias giả

Ví dụ:

```text
a
b
```

được compiler chứng minh:

```text
NO_ALIAS
```

Allocator không được biến chúng thành cùng một storage location khi chúng còn sống.

Ngược lại, hai giá trị có lifetime không overlap có thể reuse stack slot.

Vì vậy:

```text
StackSlotReuse
```

phải dựa trên:

```text
Lifetime
+
AddressObservation
+
StorageContract
```

không chỉ dựa trên type.

---

# 18. Spill Cost

Không phải mọi virtual register đều đáng spill như nhau.

Cost model:

```text
SpillCost(vreg) =
    use_frequency
  × reload_cost
  × register_pressure
  × hotness
```

Có thể bổ sung:

```text
loop_depth
block_frequency
instruction_latency
memory_pressure
```

Một giá trị trong loop nóng:

```text
for (...) {
    use x
}
```

thường đắt để spill.

---

# 19. Rematerialization

Một số giá trị không cần spill/load.

Ví dụ:

```text
x = 42
```

thay vì:

```text
store 42 → stack
load stack → reg
```

có thể:

```text
materialize 42
```

tại use.

Các ứng viên:

- integer constants,
- addresses có thể tính lại,
- simple immediates,
- target-specific cheap expressions.

```text
RematerializationCandidate {
    instruction
    cost
    clobber_requirements
}
```

Compiler phải chứng minh rematerialization giữ nguyên semantics.

---

# 20. Copy Coalescing

Trước:

```text
v1 = v2
```

Nếu:

```text
v1 → RAX
v2 → RBX
```

cần:

```text
MOV RAX, RBX
```

Nhưng nếu allocator có thể:

```text
v1 → RAX
v2 → RAX
```

thì copy biến mất.

Do đó allocator có:

```text
CoalescingEngine
```

với:

```text
MoveAffinity
```

Mục tiêu:

```text
reduce copies
```

nhưng không được tăng spill quá mức.

---

# 21. Split Live Range

Thay vì:

```text
v1 → RAX
```

suốt function, allocator có thể:

```text
v1 → RAX
      ↓
     spill
      ↓
v1 → RBX
```

Hoặc:

```text
v1
├── segment A → RAX
├── segment B → stack
└── segment C → RCX
```

Do đó cần:

```text
LiveRangeSplitter
```

Split là một trong những công cụ quan trọng nhất để giảm spill.

---

# 22. Allocation Algorithm

Thiết kế hybrid:

```text
if function is trivial:
    FastAllocator

else if pressure is low:
    LinearScan

else:
    HybridAllocator

if aggressive optimization:
    GraphColoring / PBQP-like specialized strategy
```

Không cần đưa mọi thuật toán vào v0.1 compiler bootstrap.

Có thể triển khai:

### Phase 1

```text
Linear Scan
+
Spill
+
Reload
+
Coalescing
```

### Phase 2

```text
Live-range splitting
+
Rematerialization
+
Better spill cost
```

### Phase 3

```text
Graph Coloring / Hybrid
```

Nhưng interface phải được thiết kế ngay từ đầu để không khóa architecture.

---

# 23. Register Allocation Contract

Allocator nhận:

```text
AllocationInput {
    machine_function
    register_info
    abi_info
    live_ranges
    constraints
    block_frequency
    debug_info
}
```

trả:

```text
AllocationResult {
    assignments
    spills
    reloads
    stack_slots
    rematerializations
    frame_requirements
    preserved_registers
    diagnostics
}
```

---

# 24. Allocation phải transactional

Không sửa Machine IR trực tiếp trong lúc đang thử allocation.

```text
Snapshot
   ↓
Analyze
   ↓
Plan
   ↓
Assign
   ↓
Insert Spill/Reload
   ↓
Verify
   ↓
Commit
```

Nếu fail:

```text
Rollback
```

Điều này phù hợp trực tiếp với `BOOTSTRAP-287` transactional optimization model.

---

# 25. Register Allocation Verifier

Sau allocation bắt buộc verify:

### Register correctness

```text
No two conflicting live values
    use same physical register
```

### Class correctness

```text
physical register ∈ required class
```

### Fixed constraints

```text
all fixed-register constraints satisfied
```

### Tied operands

```text
all ties satisfied
```

### Early clobber

```text
no illegal overlap
```

### Call clobber

```text
live-across-call values preserved
```

### Stack

```text
stack slot size/alignment valid
```

### Spill

```text
every spill has valid reload
```

### Rematerialization

```text
rematerialized value semantically equivalent
```

### Debug

```text
source variable mapping remains valid
```

---

# 26. Physical Register State

Sau allocation, compiler cần tracking:

```text
PhysicalRegisterState {
    register
    owner
    subregister_state
    live
    dirty
}
```

Đặc biệt cần xử lý:

```text
partial register writes
```

trên các ISA có subregister.

Ví dụ x86:

```text
AL
AX
EAX
RAX
```

không phải bốn register độc lập.

---

# 27. Stack Frame Integration

Register allocator không hoàn toàn độc lập với frame layout.

Kết quả allocation có thể yêu cầu:

```text
spill slots
callee-save slots
outgoing call arguments
local storage
alignment
red-zone usage
dynamic stack allocation
```

Do đó:

```text
Register Allocation
        ↓
Frame Requirements
        ↓
Frame Layout
```

nhưng **final frame layout** vẫn nên là subsystem riêng.

Allocator chỉ tạo:

```text
FrameObjectRequirements
```

---

# 28. Debug Information

Optimization không được làm debug information mất hoàn toàn.

Compiler phải theo dõi:

```text
SourceVariable
    ↓
VirtualRegister
    ↓
PhysicalRegister / StackSlot / Constant
```

và khi split:

```text
x:
  [10,30) → RAX
  [30,45) → stack[16]
  [45,70) → RBX
```

Debug mapping phải phản ánh location theo từng range.

---

# 29. Register Allocation và Axiom semantics

Một nguyên tắc cần đóng băng:

> **Physical register là implementation storage, không phải semantic ownership.**

Ví dụ:

```text
let a = resource;
let b = a;
```

Nếu `a` move sang `b`, allocator không được coi việc hai giá trị từng cùng physical register là semantic sharing.

Tương tự:

```text
Move
Copy
Drop
view
mut_view
```

đã được xác định ở MIR/verification.

Register allocation chỉ thực hiện physical realization.

---

# 30. GPU / SIMD

Allocator phải hỗ trợ register class mở rộng:

```text
GPR
Vector
Mask
Predicate
Accumulator
Special
```

GPU có thể có:

```text
scalar registers
vector registers
predicate registers
special registers
```

và register pressure có thể ảnh hưởng mạnh đến occupancy.

Do đó target-specific allocator có thể cung cấp:

```text
RegisterPressureModel
OccupancyModel
```

nhưng semantic layer không phụ thuộc GPU.

---

# 31. WASM

WASM là trường hợp đặc biệt.

WASM backend có thể không có physical register allocation theo nghĩa CPU.

Do đó:

```text
RegisterAllocator
```

không được bắt buộc chạy cho mọi target.

Target pipeline có thể khai báo:

```text
RegisterAllocationModel::None
```

hoặc:

```text
VirtualStackMachine
```

Điều này giữ kiến trúc backend tổng quát.

---

# 32. Machine Scheduling Integration

Sau allocation:

```text
Allocated Machine IR
        ↓
Machine Scheduling
```

Nhưng scheduling có thể ảnh hưởng register pressure.

Do đó pipeline cho phép:

```text
pre-RA scheduling
        ↓
register allocation
        ↓
post-RA scheduling
```

hoặc target chọn:

```text
register allocation
        ↓
pressure-aware scheduling
```

`298` chỉ cung cấp pressure information và allocation result; scheduling thuộc task kế tiếp.

---

# 33. Implementation Tree

```text
compiler/backend/register_alloc/
├── mod.ax
│
├── model/
│   ├── allocation.ax
│   ├── assignment.ax
│   ├── constraint.ax
│   ├── register_class.ax
│   └── physical_state.ax
│
├── liveness/
│   ├── live_range.ax
│   ├── live_segment.ax
│   ├── use_position.ax
│   ├── interval.ax
│   └── analysis.ax
│
├── interference/
│   ├── graph.ax
│   ├── interval_sweep.ax
│   └── conflict.ax
│
├── linear_scan/
│   ├── allocator.ax
│   ├── active_set.ax
│   ├── expire.ax
│   └── split.ax
│
├── coloring/
│   ├── graph.ax
│   ├── simplify.ax
│   ├── select.ax
│   ├── spill.ax
│   └── coalesce.ax
│
├── spill/
│   ├── cost.ax
│   ├── slot.ax
│   ├── insertion.ax
│   ├── reload.ax
│   └── rematerialize.ax
│
├── coalesce/
│   ├── affinity.ax
│   ├── conservative.ax
│   └── copy_elim.ax
│
├── constraints/
│   ├── fixed.ax
│   ├── tied.ax
│   ├── early_clobber.ax
│   ├── call_clobber.ax
│   └── alias.ax
│
├── frame/
│   ├── requirement.ax
│   └── stack_slot.ax
│
├── debug/
│   └── location.ax
│
├── verifier/
│   ├── register.ax
│   ├── spill.ax
│   ├── constraint.ax
│   └── debug.ax
│
├── diagnostics/
├── cache/
└── tests/
```

---

# 34. Implementation Order

Thứ tự triển khai:

```text
1. Target RegisterInfo
2. Physical Register / Alias Model
3. Register Classes
4. Virtual Register Model
5. Liveness
6. Live Intervals
7. Interference
8. Linear Scan Allocator
9. Fixed Register Constraints
10. Tied Operands
11. Early Clobber
12. Call Clobber
13. Spill Slot Allocation
14. Spill/Reload Insertion
15. Stack Slot Reuse
16. Rematerialization
17. Copy Coalescing
18. Live Range Splitting
19. Allocation Verifier
20. Debug Location Tracking
21. Hybrid Allocator
22. Graph Coloring
23. Target-specific pressure models
24. Incremental/cache support
25. Adversarial/conformance tests
```

---

# 35. Adversarial Tests

Bắt buộc có test cho:

```text
single register pressure
high register pressure
nested loops
live across call
caller-saved register
callee-saved register
fixed register instruction
tied operands
early clobber
subregister alias
vector register pressure
mask register pressure
large stack frame
stack slot reuse
rematerialization
copy coalescing
failed coalescing
live-range split
spill inside loop
multiple spills
atomic instruction
volatile instruction
foreign call
panic path
unwind path
tail call
variadic call
debug location
stable-address value
non-addressable temporary
GPU register pressure
WASM no-register target
```

Đặc biệt:

```text
ownership semantics before allocation
==
ownership semantics after allocation
```

và:

```text
capability validity before allocation
==
capability validity after allocation
```

phải được kiểm chứng.

---

# 36. Các invariant đóng băng

### `AREG-20`
Register allocation không thay đổi semantic program behavior.

### `AREG-21`
Virtual register chỉ được allocate vào register class hợp lệ.

### `AREG-22`
Physical-register aliasing phải được target model mô tả chính xác.

### `AREG-23`
Conflicting live ranges không được chia sẻ physical register.

### `AREG-24`
Fixed-register constraints phải được thỏa mãn.

### `AREG-25`
Tied operands phải được bảo toàn.

### `AREG-26`
Early-clobber constraints phải được bảo toàn.

### `AREG-27`
Call-clobber semantics phải tuân thủ ABI.

### `AREG-28`
Spill/reload phải bảo toàn giá trị và semantics.

### `AREG-29`
Stack-slot reuse chỉ được phép khi lifetime và storage constraints cho phép.

### `AREG-30`
Stable-address semantics không được bị phá bởi allocation.

### `AREG-31`
Register allocation không được tạo alias semantic mới.

### `AREG-32`
Unknown storage relationship không được tự động coi là compatible.

### `AREG-33`
Rematerialization phải semantic-equivalent.

### `AREG-34`
Copy coalescing không được tạo register conflict.

### `AREG-35`
Allocation failure phải được xử lý deterministic.

### `AREG-36`
Allocation verifier là correctness boundary trước machine scheduling.

### `AREG-37`
Debug location mapping phải được cập nhật theo live ranges.

### `AREG-38`
Allocator không được phụ thuộc vào optimization level để thay đổi semantics.

### `AREG-39`
Allocator có thể tối ưu physical storage nhưng không được thay đổi ownership/capability/effect semantics.

### `AREG-40`
Target-specific register behavior phải nằm trong `TargetRegisterInfo`, không hard-code trong generic allocator.

### `AREG-41`
Register pressure là thông tin có thể cung cấp cho các compiler subsystem khác nhưng không phải semantic fact.

### `AREG-42`
WASM hoặc target không có physical register allocation có thể bỏ qua allocator thông qua target pipeline contract.

### `AREG-43`
GPU register allocation có thể có target-specific occupancy/pressure model nhưng không thay đổi Axiom semantic model.

### `AREG-44`
Allocated Machine IR phải có thể được verify độc lập trước khi chuyển sang Machine Scheduling.

### `AREG-45`
Allocation result phải deterministic với cùng compiler revision, target, ABI, features và optimization configuration.

### `AREG-46`
Cache allocation result không được được coi là trusted semantic proof; phải revalidate khi cần.

### `AREG-47`
Spill/reload insertion không được làm mất atomic, volatile, synchronization hoặc foreign-call ordering.

### `AREG-48`
Register allocation không được tự ý loại bỏ Drop, Panic, IO hoặc observable effect.

### `AREG-49`
Physical register location không phải ownership identity.

### `AREG-50`
Stack slot location không phải logical identity.

### `AREG-51`
Allocation chỉ được commit sau khi verifier xác nhận toàn bộ allocation constraints.

---

## Kết quả kiến trúc sau BOOTSTRAP-298

Backend hiện đã có:

```text
Semantic MIR
    ↓
Verified MIR
    ↓
Optimization
    ↓
OptIR
    ↓
Machine IR
    ↓
Target Legalization
    ↓
Instruction Selection
    ↓
Virtual-register Machine IR
    ↓
REGISTER ALLOCATION        ← 298
    ↓
Physical-register Machine IR
    ↓
Machine Scheduling
    ↓
Instruction Encoding
    ↓
Object
```

Điểm quan trọng là từ đây **Axiom không còn chỉ là compiler optimizer ở mức IR**; nó đã có kiến trúc backend đủ gần phần cứng để tiến tới **native machine-code generation thực sự**.