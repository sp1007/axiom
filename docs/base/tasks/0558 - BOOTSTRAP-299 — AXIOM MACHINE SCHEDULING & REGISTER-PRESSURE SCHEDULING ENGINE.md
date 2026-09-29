# BOOTSTRAP-299 — AXIOM MACHINE SCHEDULING & REGISTER-PRESSURE SCHEDULING ENGINE
**FROZEN / COMPLETED**

## 1. Mục tiêu

`BOOTSTRAP-299` quyết định **thứ tự thực thi của các machine instruction** sau instruction selection và register allocation, nhằm khai thác tối đa:

- instruction-level parallelism (ILP),
- pipeline của CPU,
- execution ports,
- latency/throughput,
- memory-level parallelism,
- register pressure,
- cache locality,
- branch behavior.

Pipeline:

```text
Target Machine IR
      ↓
Instruction Selection
      ↓
Register Allocation
      ↓
Machine Scheduling        ← 299
      ↓
Allocated & Scheduled MIR
      ↓
Final Peephole / Machine Optimization
      ↓
Instruction Encoding
```

Nguyên tắc:

> **Scheduling chỉ được thay đổi thứ tự các instruction khi thứ tự mới tương đương về mặt semantic.**

Đặc biệt không được phá:

- atomic ordering,
- volatile ordering,
- synchronization,
- memory dependencies,
- exception/panic semantics,
- ownership/drop order,
- observable IO,
- FFI contracts.

---

# 2. Vì sao scheduling cần một task riêng?

Sau `298`, compiler đã biết:

```text
v1 → RAX
v2 → RBX
v3 → stack[32]
```

nhưng vẫn còn câu hỏi:

```text
Instruction nào chạy trước?
Instruction nào có thể chạy song song?
Instruction nào nên trì hoãn?
```

Ví dụ:

```text
load A
add
load B
multiply
```

có thể scheduling thành:

```text
load A
load B
add
multiply
```

nếu dependency cho phép.

CPU có thể bắt đầu hai memory operations sớm hơn.

---

# 3. Không được coi scheduling là “sort instruction”

Scheduling phải dựa trên dependency graph:

```text
Machine Instructions
        ↓
Dependency Analysis
        ↓
DAG
        ↓
Ready Set
        ↓
Cost / Target Model
        ↓
Instruction Selection
        ↓
Scheduled Blocks
```

---

# 4. Scheduling Domain

Đơn vị cơ bản:

```text
ScheduleRegion {
    entry
    instructions
    dependencies
    barriers
    exits
}
```

Thông thường scheduling theo basic block.

Nhưng kiến trúc phải cho phép:

```text
BasicBlock Scheduling
Trace Scheduling
Region Scheduling
Superblock Scheduling
```

về sau.

Không đưa toàn bộ function vào một scheduling DAG nếu không cần thiết.

---

# 5. Dependency Graph

```text
ScheduleNode {
    instruction
    predecessors
    successors
    latency
    resource_usage
    register_pressure
}
```

Các dependency chính:

```text
DATA
MEMORY
CONTROL
REGISTER
SIDE_EFFECT
ABI
```

---

# 6. Data Dependency

Ví dụ:

```text
ADD RAX, RBX
MUL RCX, RAX
```

Có:

```text
ADD → MUL
```

Không thể đảo.

Machine scheduler phải hiểu:

```text
RAW
WAR
WAW
```

nhưng cần phân biệt dependency thật và dependency giả.

---

# 7. Register Dependency

Sau allocation, physical registers đã tồn tại.

Ví dụ:

```text
MOV RAX, RBX
ADD RCX, RAX
```

có dependency:

```text
MOV → ADD
```

Scheduler phải hiểu cả:

- physical register,
- subregister,
- implicit register use,
- implicit register def.

Ví dụ target instruction có thể ngầm sử dụng:

```text
FLAGS
RAX
RDX
```

những dependency này phải nằm trong Machine Instruction metadata.

---

# 8. Memory Dependency

Memory dependency khó hơn register dependency.

Scheduler không được giả định:

```text
store [A]
load [B]
```

là độc lập nếu compiler không chứng minh:

```text
A != B
```

Axiom đã có:

```text
AliasInfo
MemorySSA
Capability
Effect
```

Do đó scheduler có thể dùng các proof trước đó.

---

# 9. Capability-aware Scheduling

Ví dụ:

```text
view<A> a
mut_view<B> b
```

và compiler đã chứng minh:

```text
A DISJOINT B
```

scheduler có thể reorder operations nếu các dependency khác cũng cho phép.

Nhưng:

```text
A UNKNOWN B
```

→ không được tự ý reorder memory accesses có khả năng conflict.

Nguyên tắc:

> **Scheduling được phép tận dụng proof, nhưng không được tự tạo proof.**

---

# 10. Atomic

Atomic instruction là scheduling barrier có semantics riêng.

Ví dụ:

```text
AtomicStore Release
AtomicLoad Acquire
```

không thể được đối xử như:

```text
ordinary load/store
```

Scheduler phải nhận:

```text
AtomicOrdering
AtomicScope
SynchronizationContract
```

và bảo toàn:

```text
SequencedBefore
SynchronizesWith
HappensBefore
```

---

# 11. Volatile

`volatile` không phải atomic.

Nhưng scheduler không được loại bỏ hoặc reorder volatile operations tùy tiện.

```text
volatile load
volatile store
```

có observable machine-level behavior.

Vì vậy:

```text
Volatile → SchedulingBarrier
```

theo target/ABI contract.

---

# 12. FFI

Foreign call mặc định:

```text
Unknown memory effects
Unknown register effects
Unknown side effects
```

trừ khi có contract.

Ví dụ:

```text
extern fn foo(...)
```

có thể ngăn scheduler đưa memory operation vượt qua call.

Nếu ABI/semantic contract chứng minh:

```text
ReadOnly
NoThrow
NoSync
NoMemoryWrite
```

scheduler có thể tối ưu mạnh hơn.

---

# 13. Panic / Trap

Ví dụ:

```text
load x
divide y
store z
```

nếu divide có thể panic/trap thì scheduler không thể tùy tiện đưa:

```text
store z
```

lên trước divide nếu điều đó làm thay đổi observable behavior khi panic xảy ra.

Do đó:

```text
PanicEffect
TrapEffect
```

là dependency.

---

# 14. Drop

Axiom có deterministic Drop.

Vì vậy scheduler phải cực kỳ cẩn thận.

Ví dụ:

```text
create resource
use resource
drop resource
```

Không được biến thành:

```text
create
drop
use
```

dù machine-level dependencies có vẻ cho phép.

Drop semantics đã được xác định ở semantic MIR.

Machine scheduler chỉ được reorder khi proof cho phép.

---

# 15. IO

Các operation:

```text
print
write
read
syscall
volatile device access
```

có thể có observable ordering.

Scheduler không được coi chúng là ordinary instructions.

```text
Effect::IO
```

tạo scheduling dependency phù hợp.

---

# 16. Latency Model

Mỗi instruction có:

```text
InstructionLatency {
    min
    max
}
```

Ví dụ conceptually:

```text
ADD   latency 1
MUL   latency 3
LOAD  latency variable
DIV   latency high
```

Không hard-code số này vào scheduler.

Target cung cấp:

```text
TargetSchedulingModel
```

---

# 17. Throughput Model

Latency chưa đủ.

Ví dụ hai instruction đều có latency thấp nhưng cùng cạnh tranh một execution resource.

Target model:

```text
InstructionCost {
    latency
    reciprocal_throughput
    resource_usage
}
```

Scheduler tối ưu cả:

```text
latency
+
throughput
```

---

# 18. Execution Resources

CPU có thể có các resource:

```text
ALU
LoadUnit
StoreUnit
BranchUnit
FPUnit
VectorUnit
DivideUnit
```

Instruction:

```text
ADD
```

có thể:

```text
resource = ALU
```

Instruction:

```text
LOAD
```

có thể:

```text
resource = LoadUnit
```

Scheduler tránh tạo sequence:

```text
LOAD
LOAD
LOAD
LOAD
...
```

nếu target resource model cho thấy bottleneck.

---

# 19. Ready Queue

Tại mỗi thời điểm:

```text
ReadySet
```

chứa instruction mà dependency đã hoàn tất.

Ví dụ:

```text
A → C
B → D

Ready = {A, B}
```

Scheduler chọn một instruction.

Sau khi chọn A:

```text
Ready = {B}
```

khi A hoàn tất dependency:

```text
C
```

có thể trở thành ready.

---

# 20. Scheduling Heuristic

Không khóa vào một heuristic.

```text
SchedulingPolicy {
    CriticalPath
    ResourcePressure
    RegisterPressure
    MemoryLatency
    BranchPriority
    TargetSpecific
}
```

Cost:

```text
ScheduleScore =
    CriticalPathBenefit
  + LatencyBenefit
  + ResourceBalance
  + MemoryLatencyBenefit
  - RegisterPressureCost
  - SpillRisk
```

Nhưng:

> Cost model không quyết định legality.

Legality phải được xác định trước.

---

# 21. Critical Path

Compiler tính:

```text
CriticalPathLength
```

cho dependency DAG.

Instruction nằm trên critical path thường có priority cao.

Ví dụ:

```text
A → B → C → D
```

trong khi:

```text
X → Y
```

thì scheduler ưu tiên chuỗi:

```text
A B C D
```

nếu target latency model cho thấy đây là bottleneck.

---

# 22. Register Pressure

Đây là phần đặc biệt quan trọng vì `298` vừa cấp physical registers.

Scheduling quá tham lam có thể làm:

```text
register pressure ↑
      ↓
spill ↑
      ↓
performance ↓
```

Do đó scheduler phải dự đoán:

```text
RegisterPressureDelta
```

khi đưa instruction vào schedule.

Ví dụ:

```text
LOAD A → RAX
LOAD B → RBX
LOAD C → RCX
LOAD D → RDX
```

có thể tốt về latency nhưng gây áp lực register.

Scheduler có thể trì hoãn một load.

---

# 23. Pressure-aware Scheduling

Mỗi candidate instruction có:

```text
PressureImpact
```

Ví dụ:

```text
instruction X
    +1 live register

instruction Y
    -1 live register
```

Nếu register pressure đang gần giới hạn:

```text
pressure > threshold
```

scheduler ưu tiên instruction làm giảm pressure.

---

# 24. Memory Latency Scheduling

Một load có latency lớn:

```text
LOAD [memory]
```

nên được phát hành sớm nếu:

- không conflict,
- address đã sẵn sàng,
- không phá register pressure quá mức.

Ví dụ:

```text
load A
compute X
compute Y
use A
```

thường tốt hơn:

```text
compute X
compute Y
load A
use A
```

nếu A là cache miss tiềm năng.

Target memory model có thể cung cấp:

```text
LoadLatencyClass
CacheBehaviorHint
```

nhưng scheduler không được giả định cache hit/miss chắc chắn.

---

# 25. Branch Scheduling

Branch có:

```text
BranchProbability
```

từ previous optimization/PGO nếu có.

Scheduler có thể ưu tiên instruction của hot path.

Nhưng không được thay đổi:

```text
control-flow semantics
```

Branch probability là cost information, không phải semantic fact.

---

# 26. Delay Slots

Axiom không nên đưa delay-slot logic vào generic scheduler.

Target-specific:

```text
TargetSchedulingModel
```

có thể khai báo:

```text
HasDelaySlot
```

Nếu target cần:

```text
branch
delay instruction
```

scheduler target-specific xử lý.

CPU hiện đại không có delay slot không chịu complexity này.

---

# 27. Pre-RA và Post-RA Scheduling

Axiom nên hỗ trợ hai phase:

```text
PreRA Scheduling
        ↓
Register Allocation
        ↓
PostRA Scheduling
```

### PreRA

Tối ưu:

- ILP,
- generic dependencies,
- machine latency,
- pressure estimation.

### PostRA

Tối ưu:

- physical registers,
- exact register dependencies,
- pipeline hazards,
- execution resources,
- exact pressure.

Không bắt buộc cả hai phase chạy cho mọi target/profile.

---

# 28. Scheduling không được phá allocation

Sau `298`, instruction có physical register constraints.

Scheduler không được biến:

```text
RAX → RBX
```

nếu không có register move/rewriting hợp lệ.

Scheduler chỉ reorder.

Nếu cần register reassignment:

```text
RegisterAllocation / post-RA optimization
```

phải xử lý riêng.

---

# 29. Instruction Bundle

Một số target yêu cầu instruction bundle:

```text
Bundle {
    instructions
    resource_constraints
}
```

Ví dụ VLIW hoặc GPU-like targets.

Generic scheduler hỗ trợ:

```text
InstructionBundleModel
```

nhưng CPU thông thường không cần.

---

# 30. Machine Barriers

Machine IR cần:

```text
SchedulingBarrier {
    kind
    ordering
    scope
}
```

Các barrier có thể đến từ:

```text
Atomic
Volatile
Fence
IO
Foreign
Synchronization
Control
Device
```

Không phải mọi barrier đều là:

```text
full compiler barrier
```

Scheduler phải hiểu mức độ chính xác.

---

# 31. Compiler Fence vs CPU Fence

Ví dụ:

```text
compiler_fence
```

ngăn compiler reorder.

Trong khi:

```text
CPU fence
```

là machine instruction có hardware memory-order semantics.

Axiom phải giữ chúng riêng:

```text
CompilerFence
HardwareFence
```

Một compiler fence có thể không phát ra instruction.

Một hardware fence phải phát ra instruction hoặc target-equivalent sequence.

---

# 32. GPU Scheduling

GPU scheduler không được ép dùng CPU pipeline model.

Target có thể định nghĩa:

```text
GPUInstructionModel {
    latency
    issue_width
    register_pressure
    occupancy
    memory_latency
    barrier_cost
}
```

GPU scheduling phải cân bằng:

```text
ILP
+
occupancy
+
register pressure
+
memory latency
```

Register pressure quá cao có thể giảm occupancy.

Vì vậy:

> GPU register pressure là một cost dimension khác CPU register pressure.

---

# 33. WASM

WASM có execution model khác CPU.

Scheduler có thể:

```text
None
```

hoặc chạy các simplification rất nhẹ.

Không ép WASM phải mô phỏng CPU pipeline.

---

# 34. Scheduler Architecture

```text id="5k0z5p"
MachineScheduler
├── RegionBuilder
├── DependencyBuilder
├── HazardAnalyzer
├── ReadyQueue
├── CriticalPath
├── ResourceModel
├── PressureModel
├── MemoryModel
├── BarrierModel
├── Policy
├── CandidateScorer
├── Scheduler
├── Verifier
└── Diagnostics
```

---

# 35. Target Scheduling Interface

```text id="5e4gk9"
trait TargetSchedulingModel {

    fn latency(inst: MachineInstruction) -> Latency

    fn resources(inst: MachineInstruction)
        -> ResourceUsage

    fn hazards(inst: MachineInstruction)
        -> HazardSet

    fn register_pressure_cost(inst: MachineInstruction)
        -> PressureCost

    fn can_issue(
        inst,
        state
    ) -> bool

    fn score(
        inst,
        state
    ) -> ScheduleScore
}
```

Đây là **target backend interface**, không phải Core language feature.

---

# 36. Dependency Builder

```text id="6x6x7u"
DependencyBuilder
    ├── RegisterDependency
    ├── MemoryDependency
    ├── ControlDependency
    ├── AtomicDependency
    ├── VolatileDependency
    ├── EffectDependency
    ├── ABI dependency
    └── BarrierDependency
```

Memory dependency sử dụng:

```text
AliasInfo
MemorySSA
EffectSummary
```

khi có thể.

---

# 37. Proof integration

Scheduler cũng sử dụng:

```text
ProofGateway
```

cho những reorder có semantic risk.

Ví dụ:

```text
CanReorder(A, B)
```

chỉ trả:

```text
YES
```

khi dependency analysis chứng minh được.

Không được:

```text
UNKNOWN → assume independent
```

Nguyên tắc:

> **Không chứng minh được độc lập → giữ dependency.**

---

# 38. Scheduling Transaction

Giống `287` và `298`:

```text
Analyze
   ↓
Build DAG
   ↓
Generate Candidate Schedule
   ↓
Legality Check
   ↓
Apply
   ↓
Machine Verification
   ↓
Commit
```

Nếu verifier fail:

```text
Rollback
```

---

# 39. Machine Scheduler Verifier

Sau scheduling:

### Dependency

```text
mọi dependency bắt buộc vẫn đúng
```

### Memory

```text
không có illegal memory reorder
```

### Atomic

```text
ordering preserved
```

### Volatile

```text
observable order preserved
```

### ABI

```text
call/return constraints preserved
```

### Register

```text
physical register semantics preserved
```

### Panic/Drop

```text
observable failure/cleanup ordering preserved
```

### Target hazards

```text
no illegal machine sequence
```

---

# 40. Scheduling và Drop

Một nguyên tắc đặc biệt:

```text
Drop order
```

là semantic property.

Machine scheduler chỉ được reorder các instruction **bên trong implementation của một semantic region** khi việc đó không thay đổi:

```text
Drop
Panic
IO
Synchronization
```

Ví dụ nếu destructor gọi syscall:

```text
drop(resource)
```

thì các machine instructions của destructor có observable effects.

Không được coi toàn bộ destructor là pure machine code.

---

# 41. Scheduling và Async

Sau async lowering, async state machine trở thành ordinary machine code.

Scheduler có thể tối ưu instruction bên trong state.

Nhưng không được:

```text
move instruction across suspension boundary
```

theo cách làm thay đổi:

```text
state machine semantics
```

Suspension đã được biểu diễn thành CFG/state-machine boundary từ các phase trước.

---

# 42. Scheduling và GPU

GPU barrier:

```text
barrier()
```

không phải ordinary function call.

Scheduler phải biết:

```text
WorkgroupBarrier
DeviceFence
MemoryFence
ExecutionBarrier
```

và bảo toàn scope.

---

# 43. Implementation Order

```text id="z9a9z7"
1. Machine scheduling region model
2. Dependency graph
3. Register dependency
4. Memory dependency
5. Effect/barrier dependency
6. Atomic/volatile dependency
7. Ready queue
8. Critical-path analysis
9. Basic list scheduler
10. Target latency model
11. Resource model
12. Register-pressure model
13. Pressure-aware scheduling
14. Memory-latency scheduling
15. Pre-RA scheduler
16. Post-RA scheduler
17. Branch/trace scheduling framework
18. Target-specific hazard models
19. GPU scheduling model
20. Scheduling verifier
21. ProofGateway integration
22. Deterministic replay
23. Optimization diagnostics
24. Adversarial tests
```

---

# 44. Implementation Tree

```text id="4rj9g3"
compiler/backend/scheduling/
├── mod.ax
│
├── region/
│   ├── region.ax
│   └── builder.ax
│
├── dependency/
│   ├── graph.ax
│   ├── node.ax
│   ├── edge.ax
│   ├── register.ax
│   ├── memory.ax
│   ├── control.ax
│   ├── atomic.ax
│   ├── volatile.ax
│   ├── effect.ax
│   └── barrier.ax
│
├── latency/
│   ├── model.ax
│   └── critical_path.ax
│
├── resource/
│   ├── resource.ax
│   ├── usage.ax
│   └── pressure.ax
│
├── ready/
│   ├── queue.ax
│   └── priority.ax
│
├── policy/
│   ├── policy.ax
│   ├── latency_first.ax
│   ├── throughput_first.ax
│   ├── pressure_aware.ax
│   └── balanced.ax
│
├── pre_ra/
│   └── scheduler.ax
│
├── post_ra/
│   └── scheduler.ax
│
├── target/
│   ├── generic.ax
│   ├── x86_64.ax
│   ├── arm64.ax
│   ├── riscv64.ax
│   ├── gpu.ax
│   └── wasm.ax
│
├── verify/
│   ├── dependency.ax
│   ├── memory.ax
│   ├── atomic.ax
│   ├── register.ax
│   └── hazard.ax
│
├── diagnostics/
├── replay/
└── tests/
```

---

# 45. Adversarial Tests

Phải có:

```text
independent arithmetic
dependent arithmetic
load/load
load/store
store/load
unknown alias
proven no-alias
atomic acquire/release
seq_cst
volatile
compiler fence
hardware fence
foreign call
IO
panic
drop
call clobber
fixed register
subregister
high register pressure
spill-heavy function
deep dependency chain
wide dependency DAG
nested loops
branch-heavy block
hot/cold path
vector instructions
mask instructions
GPU barrier
GPU memory fence
WASM target
```

Đặc biệt kiểm tra:

```text
Original semantic ordering
        ==
Scheduled semantic ordering
```

đối với toàn bộ observable effects.

---

# 46. Invariants đóng băng

### `ASCHED-20`
Scheduling không thay đổi observable program semantics.

### `ASCHED-21`
Instruction chỉ được reorder khi mọi dependency bắt buộc vẫn được bảo toàn.

### `ASCHED-22`
Unknown dependency không được coi là independence.

### `ASCHED-23`
Register dependencies phải được bảo toàn.

### `ASCHED-24`
Physical register aliases phải được tính vào dependency graph.

### `ASCHED-25`
Memory dependencies phải tôn trọng AliasInfo/MemorySSA.

### `ASCHED-26`
Atomic ordering không được bị phá.

### `ASCHED-27`
Volatile ordering không được bị phá.

### `ASCHED-28`
Compiler fence và hardware fence là hai semantic mechanisms riêng.

### `ASCHED-29`
FFI calls mặc định conservative nếu không có semantic contract.

### `ASCHED-30`
Panic/trap ordering không được thay đổi theo cách observable.

### `ASCHED-31`
Drop semantics không được thay đổi.

### `ASCHED-32`
IO ordering không được thay đổi.

### `ASCHED-33`
ABI constraints không được phá.

### `ASCHED-34`
Register pressure là cost, không phải semantic fact.

### `ASCHED-35`
Cost model không được override legality.

### `ASCHED-36`
Target-specific scheduling semantics phải nằm trong target scheduling model.

### `ASCHED-37`
GPU scheduling không được áp dụng CPU assumptions.

### `ASCHED-38`
WASM không bắt buộc phải có physical CPU scheduling.

### `ASCHED-39`
Scheduler chỉ được sử dụng proof đã tồn tại; không tự tạo semantic proof.

### `ASCHED-40`
Không chứng minh được independence → giữ dependency.

### `ASCHED-41`
Scheduling result phải deterministic với cùng input/compiler configuration.

### `ASCHED-42`
Scheduling failure không được làm thay đổi semantics; compiler phải fallback về legal schedule.

### `ASCHED-43`
Scheduled Machine IR phải được verify trước instruction encoding.

### `ASCHED-44`
Scheduler phải hỗ trợ pre-RA và post-RA scheduling độc lập.

### `ASCHED-45`
Scheduler không được tự ý thay đổi physical register assignment.

### `ASCHED-46`
Scheduling transaction phải rollback nếu verifier thất bại.

### `ASCHED-47`
Scheduling optimization không được làm mất debug provenance.

### `ASCHED-48`
Machine scheduler có thể sử dụng PGO/hotness nhưng PGO không thay đổi semantic legality.

### `ASCHED-49`
Register pressure phải được cân bằng với latency/throughput.

### `ASCHED-50`
Scheduler không được biến implementation storage thành semantic storage identity.

### `ASCHED-51`
Machine scheduler là optimization layer; semantic MIR vẫn là source of truth.

---

## Backend hiện tại

Sau `299`, pipeline đã trở thành:

```text
HIR
 ↓
MIR
 ↓
Verification
 ↓
Optimization
 ↓
OptIR
 ↓
Machine IR
 ↓
Legalization
 ↓
Instruction Selection
 ↓
Register Allocation
 ↓
Machine Scheduling             ← 299
 ↓
Final Machine Optimization
 ↓
Instruction Encoding
 ↓
Object Writer
 ↓
Linker
 ↓
Native Binary
```

Điểm tiếp theo hợp lý là **instruction-level finalization sau scheduling**: peephole/machine-combine, branch relaxation, late target optimization và chuẩn bị Machine IR cuối cùng trước khi encoder biến nó thành bytes.