Tiếp tục từ **COMPILER-009**, phần tiếp theo là:

# COMPILER-010 — Register Allocation + Spill/Reload + Frame Integration

## 1. Quyết định kiến trúc cốt lõi

Axiom không nên khóa allocator vào Linear Scan.

Kiến trúc nên là:

```text
Machine IR
   │
   ├── Liveness Analysis
   │
   ├── Register Pressure Analysis
   │
   ├── Register Allocation
   │      ├── Linear Scan      ← MVP
   │      ├── Greedy          ← tương lai
   │      └── Graph Coloring  ← có thể thêm sau
   │
   ├── Spill / Reload
   │
   ├── Coalescing
   │
   ├── Rematerialization
   │
   ├── Call / Fixed-Reg Repair
   │
   ├── Frame Requirements
   │
   └── Physical Machine IR
```

**Allocator chỉ chịu trách nhiệm biến virtual register thành physical register hoặc stack location.**

Nó **không được biết** ownership, `view`, `Drop`, borrow/capability, trait, async semantics...

Đây là ranh giới rất quan trọng:

> Semantic compiler quyết định **giá trị nào cần tồn tại**.  
> Register allocator quyết định **giá trị đó nằm ở register hay memory**.

---

# 2. Contract đầu vào / đầu ra

### Input

Machine IR sau instruction selection:

```text
v0 = CONST 10
v1 = CONST 20
v2 = ADD v0, v1
CALL foo(v2)
RET v2
```

Có thể chứa:

```text
VirtualRegister
PhysicalRegister
StackSlot
FixedRegister constraint
RegisterClass
TiedOperand
EarlyClobber
ImplicitUse
ImplicitDef
CallClobber
```

### Output

Machine IR sau allocation:

```text
rdi = 10
rsi = 20
rax = rdi + rsi
call foo
ret rax
```

hoặc nếu thiếu register:

```text
rsp + 32 = v0
...
v3 = load [rsp + 32]
```

Sau allocator:

```text
VirtualRegister
```

**không còn tồn tại.**

Invariant:

```text
PostRA Machine IR:
    no virtual registers
    no unresolved register classes
    no unresolved fixed-register constraints
    no unresolved tied operands
```

---

# 3. Register model

Ta đã có:

```text
Register
RegisterClass
RegisterUnit
RegisterAlias
```

Bây giờ bổ sung:

```text
VirtualRegister {
    id
    class
    width
    value_type
    preferred_registers
    constraints
}
```

Ví dụ:

```text
v17 : GPR64
v18 : GPR64
v19 : FPR64
v20 : Vec128
```

Physical:

```text
RAX
RBX
RCX
RDX
RSI
RDI
R8
...
```

Không dùng string `"rax"` trong allocator.

Phải dùng:

```text
PhysicalRegId::X86_RAX
```

Tên chỉ phục vụ debug/diagnostic/assembly output.

---

# 4. Register Class

Register class không chỉ là "tập register".

Nó phải mô tả khả năng allocation:

```text
RegisterClass {
    id
    registers
    alloc_order
    spill_size
    spill_alignment
    register_units
    caller_saved
    callee_saved
    preferred_width
}
```

Ví dụ:

```text
GPR64:
    RAX
    RBX
    RCX
    RDX
    RSI
    RDI
    R8...
```

```text
FPR64:
    XMM0...
```

```text
VEC128:
    XMM0...
```

Một register có thể thuộc nhiều class.

Ví dụ XMM register có thể phục vụ:

```text
F32
F64
Vec128
```

Nhưng allocator không được tự ý đổi class.

Instruction selector/legalizer đã xác định class hợp lệ.

---

# 5. Register Units

Đây là phần cực kỳ quan trọng với x86.

Ví dụ:

```text
RAX
EAX
AX
AL
AH
```

không phải bốn register độc lập.

Chúng chia sẻ register storage.

Do đó:

```text
RAX → units {U0,U1,U2,U3...}
EAX → same units
AX  → subset
AL  → subset
```

Allocator kiểm tra conflict dựa trên **RegisterUnit**, không chỉ `RegisterId`.

Điều này giải quyết:

```text
v0 -> RAX
v1 -> EAX
```

Không thể sống đồng thời nếu overlap.

---

# 6. Liveness

Allocator cần biết virtual register sống ở đâu.

Ví dụ:

```text
v1 = CONST 10
v2 = CONST 20
v3 = ADD v1, v2
CALL foo(v3)
RET v3
```

Ta có:

```text
v1: [def, use]
v2: [def, use]
v3: [def, use, use]
```

Nhưng không nên chỉ dùng một interval đơn giản cho kiến trúc dài hạn.

Nên định nghĩa:

```text
LiveRange {
    start
    end
}
```

và:

```text
LiveInterval {
    vreg
    ranges[]
    uses[]
    defs[]
    weight
    class
}
```

Ví dụ:

```text
v17:
    [10, 15]
    [31, 42]
```

Cho phép sau này split interval.

---

# 7. Vì sao không dùng interval duy nhất?

Ví dụ:

```text
v1 = ...
...
10.000 instructions
...
use v1
```

Nếu allocator coi:

```text
v1 live từ 1 → 10000
```

thì register bị chiếm gần như toàn bộ function.

Trong thực tế giá trị có thể có nhiều lifetime segment.

Vì vậy Axiom nên thiết kế ngay:

```text
LiveInterval
    └── LiveRange[]
```

Dù MVP Linear Scan ban đầu có thể sử dụng interval đơn giản.

Điều này tránh phải thiết kế lại Machine IR sau này.

---

# 8. Liveness là dataflow analysis

Không nên hard-code liveness trong allocator.

Tạo module riêng:

```text
compiler/machine/
    liveness/
        live_sets
        live_intervals
        register_pressure
```

API:

```text
LivenessAnalysis {
    compute(machine_function)
    live_in(block)
    live_out(block)
    interval(vreg)
}
```

Machine instruction phải khai báo:

```text
uses
defs
implicit_uses
implicit_defs
```

Ví dụ:

```text
CALL foo
```

không chỉ có argument registers.

Nó còn có:

```text
implicit_defs:
    caller_saved_registers
```

để allocator biết call phá các register nào.

---

# 9. Call Clobber

Đây là một trong những phần allocator dễ làm sai nhất.

Ví dụ SysV x86-64:

```text
RAX
RCX
RDX
RSI
RDI
R8
R9
R10
R11
```

là caller-saved.

Nếu:

```text
v1 = ...
call foo
use v1
```

thì allocator không thể để:

```text
v1 → RAX
```

trừ khi:

- spill trước call,
- hoặc v1 được đưa sang callee-saved register,
- hoặc v1 không thực sự sống qua call.

Machine IR phải biểu diễn call clobber rõ ràng.

Không được để allocator tự "đoán".

---

# 10. Callee-saved register

Ngược lại:

```text
RBX
RBP
R12
R13
R14
R15
```

có thể giữ value qua call.

Nhưng nếu function sử dụng chúng:

```text
v1 → RBX
```

thì function phải preserve RBX theo ABI.

Allocator không trực tiếp emit prologue ngay lập tức.

Nó tạo:

```text
UsedCalleeSaved {
    RBX
}
```

sau đó Frame/Prologue pass xử lý.

Điều này giữ separation:

```text
Register Allocation
        ↓
Frame Requirements
        ↓
Frame Layout
        ↓
Prologue/Epilogue
```

---

# 11. Fixed-register constraints

Ví dụ x86:

```text
DIV
IDIV
MUL
CMPXCHG
```

có register cố định.

Ví dụ:

```text
RAX:RDX / operand
```

Machine instruction phải khai báo:

```text
fixed_use
fixed_def
```

Ví dụ conceptually:

```text
IDIV {
    implicit_use  RAX
    implicit_use  RDX
    implicit_def  RAX
    implicit_def  RDX
}
```

Allocator phải:

1. đưa operand vào register cần thiết;
2. spill value đang chiếm register nếu cần;
3. thực hiện instruction;
4. xử lý kết quả;
5. tiếp tục allocation.

Không được encode các quy tắc này riêng trong Linear Scan.

---

# 12. Tied operands

Một số instruction yêu cầu:

```text
def == use
```

Ví dụ dạng:

```text
v1 = instruction v1, v2
```

Machine descriptor:

```text
tied_operand:
    def 0 ↔ use 0
```

Allocator phải đảm bảo cùng physical register.

Ví dụ:

```text
v3 = ADD_RMW v3, v4
```

có thể trở thành:

```text
RAX = ADD_RAX RAX, RCX
```

Không thể:

```text
RAX = ADD_RCX RAX, RCX
```

nếu target yêu cầu tied operand.

---

# 13. Early-clobber

Ví dụ instruction:

```text
DEF
USE
```

nhưng output được ghi trước khi tất cả input được đọc.

Khi đó:

```text
output register
```

không được overlap với một input nhất định.

Machine descriptor đã có:

```text
early_clobber = true
```

Allocator phải đưa constraint này vào interference.

Không nên xử lý bằng một hack riêng sau allocation.

---

# 14. Linear Scan MVP

MVP nên chọn **Linear Scan**.

Lý do:

- implementation nhỏ;
- dễ debug;
- phù hợp bootstrap;
- compile nhanh;
- đủ tốt cho compiler ban đầu.

Pipeline:

```text
Machine IR
   ↓
Liveness
   ↓
Live Intervals
   ↓
Sort intervals
   ↓
Linear Scan
   ↓
Register Assignment
   ↓
Spill decisions
   ↓
Spill/Reload insertion
   ↓
Coalescing
   ↓
Verify
```

---

# 15. Active set

Linear Scan duy trì:

```text
active = currently live intervals
```

Khi gặp interval mới:

```text
expire old intervals
```

Sau đó:

```text
available registers
```

Nếu còn:

```text
assign register
```

Nếu hết:

```text
spill
```

---

# 16. Spill heuristic

Không nên spill ngẫu nhiên interval cuối.

Cost nên xem:

```text
spill_cost =
    use_frequency
    × loop_depth_weight
    × reload_cost
    × register_pressure
```

Một value dùng bên trong loop:

```text
for (...) {
    use(v)
}
```

có giá trị spill rất cao.

Value dùng một lần ngoài loop:

```text
v = expensive()
...
use(v)
```

có thể spill dễ hơn.

MVP có thể đơn giản:

```text
cost = uses × loop_weight
```

Sau này nâng cấp.

---

# 17. Loop depth

Register allocator nên biết loop depth từ CFG.

Ví dụ:

```text
outside loop:
    cost × 1

loop depth 1:
    cost × 10

loop depth 2:
    cost × 100
```

Không nhất thiết cố định các con số này trong semantics.

Đó chỉ là allocation heuristic.

Có thể:

```text
AllocationCostModel
```

để target/backend thay đổi.

---

# 18. Spill không có nghĩa "đẩy toàn bộ value xuống stack"

Đây là điểm quan trọng.

Nếu:

```text
v1
```

được spill:

```text
stack_slot_3
```

thì instruction sử dụng nó:

```text
ADD v1, v2
```

không nhất thiết phải tạo:

```text
load v1
load v2
ADD
```

nếu target hỗ trợ memory operand.

Ví dụ x86:

```text
add rax, [rsp+32]
```

có thể dùng trực tiếp.

Nhưng Machine IR sau instruction selection cần cho phép backend quyết định.

Do đó spill/reload nên có:

```text
SPILL
RELOAD
```

ở mức allocator.

Sau đó Machine Optimization có thể fold:

```text
RELOAD + OP
```

thành:

```text
OP [stack]
```

nếu hợp lệ.

---

# 19. Spill slot

Spill slot khác hoàn toàn semantic local.

Định nghĩa:

```text
SpillSlot {
    id
    size
    alignment
    class
    lifetime
}
```

Ví dụ:

```text
spill0 : 8 bytes
spill1 : 16 bytes
spill2 : 32 bytes
```

Không được nhầm:

```text
local variable
```

với:

```text
register spill
```

Một source variable có thể:

```text
register
→ spill
→ register
```

nhiều lần.

---

# 20. Spill-slot coalescing

Hai virtual registers:

```text
v1
v2
```

không sống cùng lúc có thể dùng chung:

```text
spill0
```

Thay vì:

```text
spill0
spill1
```

Điều này giảm stack frame.

MVP có thể làm đơn giản:

```text
non-overlapping spill intervals → same slot
```

Sau này dùng stack-slot coloring.

---

# 21. Rematerialization

Đây là optimization rất đáng có.

Ví dụ:

```text
v1 = CONST 42
```

Nếu v1 bị spill, thay vì:

```text
store [spill0], 42
...
load v1, [spill0]
```

có thể đơn giản:

```text
mov rax, 42
```

Tức là **tái tạo value**.

Machine IR nên đánh dấu:

```text
Rematerializable
```

Ví dụ:

```text
CONST
simple address
small immediate
symbol address
```

Không rematerialize:

```text
load memory
function call
atomic
volatile
expensive computation
```

---

# 22. Rematerialization cost

Mỗi definition có:

```text
RematInfo {
    kind
    cost
    constraints
}
```

Ví dụ:

```text
CONST 5
cost = 1
```

có thể tốt hơn spill.

Nhưng:

```text
CONST 128-bit
```

có thể cần nhiều instruction.

Target quyết định cost.

---

# 23. Register Coalescing

Axiom sẽ thường sinh:

```text
v2 = COPY v1
```

đặc biệt sau:

- SSA destruction;
- phi lowering;
- ABI argument;
- return;
- closure environment;
- aggregate moves.

Allocator nên cố:

```text
v1 → RAX
v2 → RAX
```

để COPY biến mất.

Nhưng **không nên làm coalescing quá phức tạp ở MVP**.

Thiết kế:

```text
Coalescer {
    collect_moves()
    try_coalesce()
    eliminate_redundant_copies()
}
```

MVP:

```text
if v1 and v2 do not interfere:
    merge
```

Sau này có thể thêm Briggs/George-style heuristics.

---

# 24. SSA và phi

Machine IR trước allocation vẫn SSA-assisted.

Ví dụ:

```text
B1:
    v3 = ...
    br B3

B2:
    v4 = ...
    br B3

B3:
    v5 = PHI(v3, v4)
```

Sau register allocation, PHI không còn tồn tại như SSA semantics.

Cần:

```text
SSA destruction
```

thành parallel copies:

```text
B1:
    copy r1 → r3

B2:
    copy r2 → r3
```

Nhưng nếu:

```text
r1 = r2
r2 = r1
```

thì phải xử lý cycle.

Do đó cần:

```text
ParallelCopyResolver
```

có thể dùng temporary register hoặc spill slot.

---

# 25. Allocation không nên phá Machine IR semantics

Ví dụ:

```text
atomic load
```

không được biến thành:

```text
normal load
```

Allocator chỉ được thay:

```text
virtual location
```

bằng:

```text
physical register / stack location
```

Tương tự:

```text
volatile
atomic ordering
trap
call
memory effects
```

không thuộc trách nhiệm allocator.

---

# 26. Register pressure

Nên có analysis riêng:

```text
RegisterPressure {
    max_pressure[RegisterClass]
    pressure_at_instruction[]
}
```

Ví dụ:

```text
GPR pressure = 12
available GPR = 14
```

ổn.

Nếu:

```text
GPR pressure = 22
available GPR = 14
```

allocator biết vùng đó cần spill.

Thông tin này sau này còn được dùng bởi:

- instruction scheduling;
- loop optimization;
- inlining;
- vectorization;
- machine optimization.

---

# 27. Allocation Policy

Không hard-code:

```text
if x86 then LinearScan
```

Nên có:

```text
AllocationPolicy {
    algorithm
    optimization_level
    enable_coalescing
    enable_rematerialization
    enable_interval_split
    spill_strategy
}
```

Ví dụ:

```text
-O0:
    LinearScan
    minimal coalescing
    minimal rematerialization

-O1:
    LinearScan
    coalescing

-O2:
    LinearScan/Greedy
    coalescing
    rematerialization
    interval splitting

-O3:
    advanced allocator
```

Nhưng đây là implementation policy, **không phải semantics**.

---

# 28. Interval splitting

Ngay từ data model nên hỗ trợ:

```text
LiveInterval
    ├── Range A → RAX
    ├── Range B → spill0
    └── Range C → RBX
```

Ví dụ:

```text
v1
 │
 ├── hot loop → RAX
 │
 ├── cold block → spill
 │
 └── after loop → RBX
```

Linear Scan MVP có thể chưa dùng.

Nhưng interface phải không khóa nó.

---

# 29. Allocation Result

Nên có cấu trúc:

```text
AllocationResult {
    registers: Map<VReg, Location>
    spill_slots: SpillSlotTable
    used_callee_saved: Set<PhysicalReg>
    stack_requirements: StackRequirements
    inserted_moves: ...
    inserted_spills: ...
    inserted_reloads: ...
}
```

Location:

```text
Location =
    Register(PhysicalReg)
  | Stack(SpillSlot)
  | Rematerialize(RematInfo)
```

Sau khi finalize:

```text
Location
```

được materialize thành Machine operands.

---

# 30. Frame Integration

Đây là điểm phải phối hợp rất cẩn thận.

Trước RA:

```text
FrameRequirements
```

có thể biết:

```text
incoming args
outgoing args
dynamic alloca
local address-taken objects
sret
```

Sau RA mới biết:

```text
spill slots
used callee-saved
```

Do đó frame phải **2-phase**.

### Phase 1

```text
PreRAFrameAnalysis
```

xác định:

```text
needs_frame
needs_fp
needs_dynamic_stack
needs_outgoing_args
needs_sret
needs_unwind
```

### Phase 2

Sau allocator:

```text
FinalFrameLayout
```

thêm:

```text
spill slots
saved registers
alignment padding
canary
shadow stack metadata
```

---

# 31. Frame Layout

Ví dụ:

```text
High address
────────────────
incoming args
return area
────────────────
saved callee registers
────────────────
spill slots
────────────────
locals
────────────────
outgoing args
────────────────
alignment
────────────────
Low address
```

Nhưng layout thực tế target-specific.

Không được hard-code thứ tự trên thành language semantics.

---

# 32. Stack slot coloring

Sau allocation:

```text
spill0 lifetime [10,20]
spill1 lifetime [30,50]
spill2 lifetime [15,18]
```

Có thể:

```text
spill0 → offset 32
spill1 → offset 32
```

nếu không overlap.

Nhưng:

```text
spill2
```

overlap spill0 nên phải khác.

Đây là:

> **Stack-slot allocation là register allocation cấp memory.**

Nên thiết kế độc lập:

```text
StackSlotAllocator
```

---

# 33. Stack alignment

Final frame phải thỏa:

```text
frame_size % ABI_alignment == required_condition
```

Ví dụ SysV x86-64 có yêu cầu alignment đặc biệt tại CALL.

Allocator không tự xử lý alignment.

Nó chỉ cung cấp:

```text
spill size
spill alignment
```

Frame lowering tính tổng.

---

# 34. Zero-frame optimization

Đây là một mục tiêu quan trọng của Axiom.

Function:

```text
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

không nên sinh:

```text
push rbp
mov rbp,rsp
sub rsp,...
...
mov rsp,rbp
pop rbp
ret
```

nếu ABI không cần.

Có thể:

```text
lea eax,[rdi+rsi]
ret
```

hoặc tương đương.

Do đó:

```text
needs_frame = false
```

là trường hợp bình thường.

---

# 35. Frame pointer

Không mặc định bắt buộc FP.

Có thể:

```text
FramePointerPolicy {
    Omit
    Keep
    Required
}
```

Required khi:

- target/ABI yêu cầu;
- dynamic stack semantics cần;
- debug/unwind policy;
- sanitizer/security;
- platform constraint.

`-fno-omit-frame-pointer` tương đương có thể là profile/toolchain option, không phải language semantics.

---

# 36. Callee-saved integration

Ví dụ allocator dùng:

```text
RBX
R12
```

thì:

```text
used_callee_saved = {RBX,R12}
```

Frame lowering tạo:

```text
prologue:
    save RBX
    save R12
```

và:

```text
epilogue:
    restore R12
    restore RBX
```

Thứ tự phụ thuộc target ABI.

---

# 37. Call-preserved allocation

Allocator cần cost model biết:

```text
caller_saved
callee_saved
```

Ví dụ value sống xuyên qua nhiều call:

```text
v1
call A
call B
call C
use v1
```

dùng callee-saved register có thể rẻ hơn:

```text
spill/reload quanh từng call
```

Ngược lại value chỉ sống ngắn:

```text
v1
use v1
call A
```

caller-saved register tốt hơn.

Đây là lý do register class cần ABI information.

---

# 38. Multi-register values

Axiom hỗ trợ aggregate/multi-register ABI.

Ví dụ:

```text
128-bit value
```

có thể:

```text
RAX:RDX
```

hoặc:

```text
XMM0
```

tùy ABI.

Do đó không nên giả định:

```text
VReg → exactly one PhysicalReg
```

Mà:

```text
RegisterAssignment =
    OneRegister
  | RegisterTuple
```

hoặc biểu diễn:

```text
v128 → [RAX,RDX]
```

Các register phải thỏa:

- đúng class;
- đúng width;
- không illegal overlap;
- fixed constraints;
- tied constraints.

---

# 39. Spill multi-register value

Một multi-register value có thể cần:

```text
spill0 + spill1
```

với alignment phù hợp.

Không được biến nó thành hai value semantic độc lập.

Định nghĩa:

```text
SpillBundle {
    slots[]
    size
    alignment
}
```

---

# 40. Debug information

Allocator thay đổi location của source variable:

```text
RAX
→ spill0
→ RBX
```

Debug info phải biết location ranges.

Ví dụ:

```text
x:
    [0,20] → RAX
    [20,35] → stack[32]
    [35,50] → RBX
```

Do đó DebugLoc và variable-location tracking không được bị bỏ qua.

MVP có thể đơn giản hơn, nhưng data model phải cho phép location ranges.

---

# 41. Unwind

Allocator/frame pass phải đảm bảo unwind metadata khớp machine code.

Nếu:

```text
RBX
```

được save:

```text
push rbx
```

thì unwind info phải biết.

Nếu stack pointer thay đổi:

```text
sub rsp, 64
```

unwind state cũng phải phản ánh.

Không được generate unwind sau cùng bằng cách "đoán" từ source.

Nó phải dựa trên final frame/prologue sequence.

---

# 42. Physical Machine IR contract

Sau COMPILER-010:

```text
Physical Machine IR
```

phải có:

```text
Physical registers
Stack slots
Concrete memory operands
Concrete call constraints
Concrete callee-saved usage
No virtual registers
No unresolved allocation constraints
```

Nhưng vẫn có thể còn:

```text
abstract stack offsets
abstract prologue/epilogue markers
unresolved target fixups
```

vì Frame Lowering/Encoding chưa hoàn tất.

---

# 43. MachineVerifier sau RA

Verifier mới:

```text
PostRA MachineVerifier
```

kiểm tra:

### Registers

```text
no virtual registers
physical register valid
register class compatible
alias constraints valid
```

### Instructions

```text
fixed register satisfied
tied operand satisfied
early-clobber satisfied
implicit use/def valid
```

### Calls

```text
ABI argument locations valid
return registers valid
call-clobber correctness
```

### Stack

```text
stack slot valid
alignment valid
offset not yet necessarily finalized
```

### CFG

```text
valid successors
valid terminators
```

---

# 44. Allocation correctness invariant

Điểm quan trọng:

> Allocator không được làm thay đổi semantics của Machine IR.

Ta có:

```text
MachineIR_before_RA
        ≡
MachineIR_after_RA
```

theo machine-level semantic equivalence.

Register allocation chỉ thay đổi:

```text
location
```

chứ không thay đổi:

```text
value
ordering
memory semantics
atomic semantics
volatile semantics
call semantics
trap behavior
```

---

# 45. MIR interpreter vẫn là oracle

Không nên cố chạy interpreter của Machine IR để kiểm tra mọi thứ ngay từ đầu.

Ta có:

```text
Source
 ↓
MIR
 ↓
MIR Interpreter
```

là semantic oracle.

Sau đó:

```text
MIR
 ↓
LIR
 ↓
Machine IR
 ↓
RA
 ↓
Encoding
 ↓
Native
```

Test:

```text
MIR result == native result
```

trong bootstrap.

Đặc biệt test:

```text
high register pressure
spill
call
nested loops
fixed registers
atomic
volatile
multi-register return
```

---

# 46. Allocation stress tests

Cần có test chuyên dụng:

```text
register_pressure/
call_pressure/
fixed_register/
tied_operand/
early_clobber/
spill/
rematerialize/
coalesce/
multi_register/
callee_saved/
zero_frame/
dynamic_stack/
debug_location/
unwind/
```

Ví dụ test pressure:

```text
fn test() -> i64 {
    let a = ...
    let b = ...
    let c = ...
    ...
    return a+b+c+...
}
```

Compiler test phải cố tình tạo nhiều live values.

---

# 47. Fuzzing

Một fuzz case:

```text
random source
```

chạy:

```text
-O0
-O1
-O2
-O3
```

và:

```text
MIR interpreter
vs
native executable
```

Nếu khác:

```text
reduce testcase
```

Đặc biệt allocator rất thích hợp fuzz vì bug thường nằm ở:

```text
rare CFG
rare register constraint
rare spill location
```

---

# 48. Data structure tổng thể

Đề xuất:

```text
compiler/
└── backend/
    └── regalloc/
        ├── mod
        ├── liveness
        ├── intervals
        ├── pressure
        ├── linear_scan
        ├── coalesce
        ├── spill
        ├── rematerialize
        ├── stack_slots
        ├── constraints
        ├── allocation_result
        └── verifier
```

API chính:

```text
RegisterAllocator {
    allocate(
        machine_function,
        register_info,
        frame_requirements,
        allocation_policy
    ) -> AllocationResult
}
```

---

# 49. Không nên làm allocator thành "God module"

Tách rõ:

```text
Liveness
    ↓
Intervals
    ↓
Allocator
    ↓
Spill insertion
    ↓
Coalescing
    ↓
Stack-slot allocation
    ↓
Frame integration
```

Đặc biệt:

```text
RegisterAllocator
```

không nên tự:

- generate prologue;
- encode instruction;
- tính object relocation;
- xử lý ABI từ đầu;
- hiểu source variable;
- hiểu ownership.

---

# 50. Allocation pipeline chính thức

Tôi đề xuất đóng băng pipeline:

```text
Machine IR
    │
    ▼
Machine PreRA Verify
    │
    ▼
PreRA Frame Analysis
    │
    ▼
Liveness Analysis
    │
    ▼
Live Interval Construction
    │
    ▼
Register Pressure Analysis
    │
    ▼
Register Allocation
    │
    ├── Register Assignment
    ├── Spill
    ├── Reload
    ├── Rematerialization
    └── Coalescing
    │
    ▼
SSA / PHI Destruction
    │
    ▼
Stack Slot Coloring
    │
    ▼
PostRA Frame Requirements
    │
    ▼
Physical Machine IR
    │
    ▼
PostRA Verify
    │
    ▼
Final Frame Layout
    │
    ▼
Prologue / Epilogue
```

Điểm đáng chú ý: **Final Frame Layout chưa nằm hoàn toàn trong COMPILER-010**; COMPILER-010 cung cấp đủ thông tin để COMPILER-011 thực hiện frame lowering cuối cùng.

---

# 51. Invariants

Đề xuất đóng băng bộ invariant:

### ARALLOC-20 — Allocation Preserves Machine Semantics

Register allocation không thay đổi machine-level observable semantics.

### ARALLOC-21 — Every Virtual Register Has A Valid Location

Mỗi virtual register sau allocation phải có location hợp lệ hoặc được rematerialize.

### ARALLOC-22 — No Virtual Registers After Final Allocation

Physical Machine IR không còn virtual register.

### ARALLOC-23 — Register Class Constraints Are Preserved

Mọi assignment phải thuộc register class hợp lệ.

### ARALLOC-24 — Register Alias Conflicts Are Forbidden

Các register unit overlap không thể chứa các value sống đồng thời.

### ARALLOC-25 — Fixed Register Constraints Are Satisfied

Fixed-use/fixed-def phải được thỏa mãn.

### ARALLOC-26 — Tied Operands Are Preserved

Tied operands phải cùng physical location khi ABI/instruction yêu cầu.

### ARALLOC-27 — Early-Clobber Constraints Are Preserved

Early-clobber không được overlap với operand bị cấm.

### ARALLOC-28 — Call Clobbers Are Explicit

Allocator phải tính caller-clobbered registers.

### ARALLOC-29 — Callee-Saved Usage Is Reported

Mọi callee-saved register được dùng phải được báo cho frame lowering.

### ARALLOC-30 — Spill Does Not Change Value Semantics

Spill/reload chỉ thay đổi storage location.

### ARALLOC-31 — Spill Slots Have Valid Size And Alignment

Mọi spill slot phải đáp ứng layout requirement.

### ARALLOC-32 — Spill Slots May Be Reused

Các lifetime không overlap có thể dùng chung spill storage.

### ARALLOC-33 — Rematerialization Is Semantics-Preserving

Rematerialization chỉ áp dụng cho expression có semantics tương đương.

### ARALLOC-34 — Volatile Cannot Be Rematerialized Or Eliminated Incorrectly

Volatile semantics không được coi là ordinary computation.

### ARALLOC-35 — Atomic Operations Remain Atomic

Register allocation không phá atomic semantics.

### ARALLOC-36 — Register Allocation Is ABI-Aware

Call/return/fixed register constraints phải theo ABI hiện tại.

### ARALLOC-37 — Multi-Register Values Remain Atomic Semantic Values

Một semantic value có thể có nhiều physical locations nhưng không bị tách thành semantic values độc lập.

### ARALLOC-38 — Allocation Does Not Introduce Semantic Heap Allocation

Spill chỉ tạo stack storage/compiler storage, không phải language-level heap allocation.

### ARALLOC-39 — Allocation Does Not Imply A Stack Frame

Function chỉ có frame khi requirements thực sự cần.

### ARALLOC-40 — Zero-Frame Functions Are Valid

Không có local/spill/callee-save/outgoing/dynamic/debug/security requirement thì frame có thể bằng zero.

### ARALLOC-41 — Debug Locations Follow Allocation

Debug variable locations phải phản ánh register/stack transitions.

### ARALLOC-42 — Unwind Information Matches Frame State

Saved registers và stack transitions phải có thông tin unwind tương ứng.

### ARALLOC-43 — SSA Destruction Preserves Dataflow

PHI/parallel-copy lowering phải giữ nguyên semantics.

### ARALLOC-44 — Register Allocation Is Deterministic

Cùng Machine IR + target + policy → cùng allocation.

### ARALLOC-45 — Allocation Is Optimization-Level Independent Semantically

`-O0` và `-O3` có thể allocation khác nhau nhưng semantics giống nhau.

### ARALLOC-46 — Allocation Algorithm Is Replaceable

Machine IR không phụ thuộc Linear Scan.

### ARALLOC-47 — Liveness Is Independent From Allocation Algorithm

Allocator có thể dùng chung liveness/interval infrastructure.

### ARALLOC-48 — Spill Decisions Are Policy, Not Semantics

Heuristic thay đổi được mà không thay đổi language semantics.

### ARALLOC-49 — Frame Layout Is Separate From Register Assignment

Register allocator không trở thành frame-layout engine.

### ARALLOC-50 — Physical Machine IR Is Verifiable

Mọi allocation phải được MachineVerifier kiểm chứng.

### ARALLOC-51 — Register Units Define Physical Interference

Alias/partial-register conflict được kiểm tra ở unit level.

### ARALLOC-52 — Call-Preserved Values Must Survive Calls

Giá trị live xuyên call phải ở location được bảo toàn hoặc được spill/reload.

### ARALLOC-53 — Caller-Saved Values Cannot Be Assumed Preserved

Không được ngầm giả định caller-saved register giữ giá trị sau call.

### ARALLOC-54 — Spill/Reload Must Respect Address Space

Stack spill không được nhầm với Device/Global/TLS/External storage.

### ARALLOC-55 — Allocation Must Preserve Memory Ordering

Atomic ordering và volatile ordering không bị thay đổi.

### ARALLOC-56 — Stack Slot Identity Is Not Source Variable Identity

Spill slot là compiler storage, không phải semantic identity của source variable.

### ARALLOC-57 — Allocation May Be Recomputed

Allocator có thể chạy lại sau machine transformations nếu Machine IR contract vẫn hợp lệ.

### ARALLOC-58 — No External Assembler Is Required

Allocation không dựa vào assembler/linker bên ngoài.

### ARALLOC-59 — Allocation Results Are Target-Specific

Register assignment phụ thuộc target register file/ABI.

### ARALLOC-60 — Semantic Proofs Are Not Recreated By Allocator

Allocator tin vào Machine IR semantics đã được verify; nó không được trở thành ownership/type checker thứ hai.

---

# 52. Một quyết định rất quan trọng cho Axiom

Từ COMPILER-010 trở đi, kiến trúc Axiom đã đạt một điểm rất đẹp:

```text
                 SEMANTIC WORLD
                       │
Source → HIR → MIR → Optimized MIR
                       │
                       ▼
                 ABI / LIR WORLD
                       │
                       ▼
                 MACHINE WORLD
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
   Register Allocation        Frame Layout
          │                         │
          └────────────┬────────────┘
                       ▼
                Physical Machine IR
                       │
                       ▼
                 Machine Encoding
                       │
                       ▼
                    Object
```

Và quan trọng nhất:

> **Register allocation có thể cực kỳ phức tạp mà không làm ngôn ngữ Axiom phức tạp hơn đối với lập trình viên.**

Đây chính xác là nguyên tắc mà ta đã thống nhất từ đầu: **compiler có thể phức tạp, nhưng complexity đó phải được hấp thụ bên trong compiler thay vì đẩy sang programmer.**

### Trạng thái hiện tại

Sau COMPILER-010, chuỗi backend gần như đã hoàn chỉnh:

```text
COMPILER-005  MIR
COMPILER-006  Closure / Async lowering
COMPILER-007  Semantic MIR optimization
COMPILER-008  ABI / Layout
COMPILER-009  Legalization / Instruction Selection
COMPILER-010  Register Allocation / Spill / Reload
      ↓
COMPILER-011  Final Frame Lowering + Prologue/Epilogue
      ↓
COMPILER-012  Machine Verification + Encoding
      ↓
OBJECT-001    Object Writer
LINKER-001    Linker
BOOTSTRAP     Self-hosting
```

**Bước kế tiếp hợp lý nhất là COMPILER-011 — Final Frame Lowering + Prologue/Epilogue**, nơi ta chốt hoàn toàn stack frame, callee-saved, outgoing argument area, dynamic stack allocation, stack probes, red zone, shadow space, unwind state và cách biến Physical Machine IR thành machine code-ready IR.