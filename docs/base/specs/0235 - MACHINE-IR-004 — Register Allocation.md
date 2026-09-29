Tiếp tục **MACHINE-IR-004 — Register Allocation & Spill/Reload**. Đây là phần rất quan trọng vì nó quyết định chất lượng codegen thực tế sau khi instruction selection đã hoàn tất.

# MACHINE-IR-004 — Register Allocation

## 1. Mục tiêu

Trước Register Allocation:

```text
v0
v1
v2
v3
v4
...
```

là **virtual registers** — số lượng gần như không giới hạn.

Sau Register Allocation:

```text
v0 → RAX
v1 → RBX
v2 → XMM0
v3 → RCX
...
```

và nếu không đủ register:

```text
v7 → [stack + 32]
```

Mục tiêu:

> Dùng ít memory traffic nhất trong khi vẫn thỏa tất cả register constraints của target.

---

# 2. Không nên bắt đầu bằng graph coloring

Có hai hướng kinh điển:

```text
Graph Coloring
Linear Scan
```

Tôi đề xuất Axiom:

```text
MVP:
    Linear Scan

Later:
    Advanced allocator
    + coalescing
    + live-range splitting
    + rematerialization
    + target-aware heuristics
```

Lý do:

- Linear Scan đơn giản hơn rất nhiều.
- Compile nhanh.
- Dễ debug.
- Phù hợp bootstrap compiler.
- Vẫn tạo code tốt cho phần lớn chương trình.
- Sau này có thể thay allocator mà không thay đổi MIR/LIR.

---

# 3. Virtual Register

Mỗi virtual register:

```text
VirtualRegister {
    id
    class
    width
    type
    def_count
    use_count
}
```

Ví dụ:

```text
v17 : GPR64
v18 : GPR64
v19 : FPR64
v20 : Vec128
```

Không nên gắn trực tiếp với CPU register.

---

# 4. Register Class

Ví dụ x86-64:

```text
GPR8
GPR16
GPR32
GPR64

XMM128
XMM256
XMM512
```

AArch64:

```text
GPR32
GPR64
FPR32
FPR64
V128
```

RISC-V:

```text
GPR32/GPR64
FPR32/FPR64
Vector
```

Register allocator không được đưa `v17:GPR64` vào XMM register.

---

# 5. Register aliases

CPU register không độc lập hoàn toàn.

x86:

```text
RAX
EAX
AX
AL
AH
```

Phải có register-unit model.

Ví dụ:

```text
RAX
 ├── EAX
 │    ├── AX
 │    │    ├── AL
 │    │    └── AH
```

Nếu:

```text
v1 → RAX
```

thì không thể đồng thời:

```text
v2 → EAX
```

nếu lifetime của hai giá trị overlap.

---

# 6. Register units

Thay vì kiểm tra tên register:

```text
RAX conflicts EAX
```

Machine IR có:

```text
RegisterUnit {
    id
}
```

Ví dụ:

```text
RAX = {U0,U1,U2,U3}
EAX = {U0,U1}
AX  = {U0}
AL  = {U0}
AH  = {U1}
```

Hai register conflict nếu:

```text
units(A) ∩ units(B) != ∅
```

Đây là mô hình rất sạch.

---

# 7. Live interval

Ví dụ:

```text
1: v1 = ...
2: v2 = ...
3: ADD v1,v2
4: ...
5: MUL v1
6: ...
```

`v1` sống:

```text
[1,5]
```

`v2`:

```text
[2,3]
```

Hai interval overlap → cần register khác nhau.

---

# 8. Liveness

Machine IR cần:

```text
USE
DEF
LIVE_IN
LIVE_OUT
```

theo basic block.

Công thức:

```text
LIVE_IN  = USE ∪ (LIVE_OUT - DEF)
LIVE_OUT = union(LIVE_IN(successors))
```

đây là nền tảng cho allocator.

---

# 9. SSA và Register Allocation

LIR/Machine IR trước RA vẫn có thể giữ SSA.

Ví dụ:

```text
if cond:
    v3 = ...
else:
    v4 = ...

v5 = phi(v3,v4)
```

Không nên ép thành physical register quá sớm.

Sau đó:

```text
SSA destruction
```

có thể chuyển:

```text
phi
```

thành:

```text
parallel copies
```

---

# 10. Parallel Copy

Ví dụ:

```text
v3 = phi(v1, v2)
```

cần:

```text
v3 <- v1
```

ở predecessor A,

```text
v3 <- v2
```

ở predecessor B.

Nhưng khi register assignment:

```text
v1 → RAX
v2 → RBX
v3 → RBX
```

ở predecessor A:

```text
RAX → RBX
```

Nếu có:

```text
v1 → RAX
v2 → RBX
```

và cần swap:

```text
RAX → RBX
RBX → RAX
```

không thể emit tuần tự đơn giản.

Phải dùng:

```text
ParallelCopy {
    RAX → RBX
    RBX → RAX
}
```

sau đó resolver xử lý cycle.

---

# 11. Fixed register constraints

Đây là một trong những lý do allocator phải hiểu Machine IR rất sâu.

Ví dụ x86:

```text
IDIV r/m64
```

yêu cầu:

```text
RAX = dividend
RDX = high half
```

và kết quả:

```text
RAX = quotient
RDX = remainder
```

Allocator phải ép:

```text
v_dividend → RAX
```

và:

```text
result → RAX/RDX
```

---

# 12. Tied operands

Ví dụ instruction:

```text
ADD rax, rbx
```

semantic:

```text
dst = dst + src
```

LIR có:

```text
v3 = ADD v3, v4
```

Machine instruction có constraint:

```text
def(dst) tied_to use(dst)
```

Allocator phải đặt:

```text
v3 input = v3 output
```

cùng physical register.

---

# 13. Early clobber

Một số instruction ghi output trước khi đọc hết input.

Ví dụ:

```text
instruction {
    def = R
    use = A,B
    early_clobber = R
}
```

`R` không được alias với input chưa được đọc.

Nếu không mô hình hóa:

→ allocator có thể tạo code sai.

Do đó constraint này đã phải có từ MACHINE-IR-002.

---

# 14. Call clobber

Ví dụ SysV x86-64:

```text
caller-saved:
RAX
RCX
RDX
RSI
RDI
R8-R11
```

Một giá trị sống qua:

```text
CALL foo
```

không thể đơn giản để trong caller-saved register.

Có ba lựa chọn:

```text
callee-saved register
spill trước CALL
recompute sau CALL
```

Allocator quyết định.

---

# 15. Call boundary

Ví dụ:

```text
v1 = ...
CALL foo()
USE v1
```

`v1` live xuyên call.

Allocator biết:

```text
live_across_call(v1) = true
```

→ ưu tiên callee-saved register.

---

# 16. Spill

Nếu:

```text
live registers > available registers
```

một virtual register phải spill.

Ví dụ:

```text
v17 → stack slot 24
```

Trước use:

```text
LOAD RAX, [SP+24]
ADD RAX, ...
```

Sau def:

```text
...
STORE [SP+24], RAX
```

---

# 17. Spill slot

Đừng coi spill slot là ordinary stack variable.

```text
StackSlot {
    id
    kind = Spill
    size
    alignment
}
```

Khác:

```text
Local
IncomingArg
OutgoingArg
SRet
Temp
```

Điều này giúp frame layout tối ưu hơn.

---

# 18. Spill không nhất thiết là một slot cố định duy nhất

Hai virtual registers:

```text
v1 live [1,10]
v2 live [20,30]
```

không overlap.

Có thể share:

```text
spill slot #3
```

→ giảm frame size.

---

# 19. Stack-slot coloring

Sau allocation:

```text
spill slot A [10,20]
spill slot B [21,40]
spill slot C [12,15]
```

A và C overlap.

B không overlap A/C.

Có thể:

```text
A → slot0
C → slot1
B → slot0
```

Đây là **stack-slot coloring**.

---

# 20. Spill cost

Không phải register nào cũng đáng spill như nhau.

Ví dụ:

```text
v1:
    use = 100
    loop depth = 10
```

vs:

```text
v2:
    use = 2
    loop depth = 1
```

Spill `v2` hợp lý hơn.

Cost có thể:

```text
spill_cost =
    use_frequency
    × loop_weight
    × reload_cost
```

---

# 21. Loop-aware allocation

Đây là optimization rất quan trọng.

Một spill bên ngoài loop:

```text
load
loop:
    use
    use
store
```

có thể tốt.

Nhưng:

```text
loop:
    load
    use
    store
```

có thể cực kỳ đắt.

Allocator nên tính loop depth.

---

# 22. Rematerialization

Không phải giá trị nào cũng cần spill.

Ví dụ:

```text
v1 = CONST 42
```

Nếu register thiếu:

```text
spill v1
```

không cần thiết.

Khi cần lại:

```text
MOV RAX, 42
```

→ **rematerialize**.

Tương tự:

```text
address = base + constant
```

nếu cheap.

---

# 23. Rematerializable flag

Machine instruction descriptor nên có:

```text
rematerializable = true
```

nhưng chỉ khi instruction:

- không side effect
- không memory
- cheap
- deterministic

Ví dụ:

```text
CONST
MOV immediate
simple address formation
```

---

# 24. Live-range splitting

Ví dụ:

```text
v1
│
├──── hot region ────┐
│                    │
├──── cold region ───┘
```

Có thể:

```text
hot → RAX
cold → stack
```

thay vì spill toàn bộ lifetime.

Đây là bước nâng cao nhưng kiến trúc nên hỗ trợ từ đầu.

---

# 25. Linear Scan MVP

Thuật toán:

```text
1. Compute liveness
2. Build live intervals
3. Sort intervals by start
4. Maintain active intervals
5. Allocate available register
6. Expire old intervals
7. Spill when necessary
8. Rewrite Machine IR
9. Repeat until no virtual register remains
```

Độ phức tạp thấp và phù hợp bootstrap.

---

# 26. Nhưng đừng khóa API vào Linear Scan

Nên có interface:

```text
RegisterAllocator {
    allocate(machine_function)
}
```

Implementations:

```text
LinearScanAllocator
GraphColoringAllocator
AdvancedAllocator
```

Sau này có thể benchmark và thay thế.

---

# 27. Coalescing

Ví dụ:

```text
v2 = COPY v1
```

nếu:

```text
v1 → RAX
v2 → RBX
```

thì có COPY:

```text
RAX → RBX
```

Nếu có thể:

```text
v1 → RAX
v2 → RAX
```

thì COPY biến mất.

Đây là **register coalescing**.

---

# 28. COPY elimination

Sau RA:

```text
COPY RAX,RAX
```

→ xóa.

Nếu:

```text
COPY RAX,RBX
```

không cần thiết do allocation tốt hơn:

→ xóa.

---

# 29. Two-address instruction

x86 có nhiều instruction dạng:

```text
dst = dst + src
```

Trong khi LIR:

```text
v3 = v1 + v2
```

Legalizer/selector có thể tạo:

```text
COPY v3,v1
ADD v3,v2
```

Allocator nên cố gắng:

```text
v3 và v1 → cùng register
```

để COPY biến mất.

---

# 30. Register pressure

Machine optimizer nên biết:

```text
pressure(GPR) = number of simultaneously-live GPR values
```

và:

```text
pressure(FPR)
pressure(Vector)
```

Đây là lý do instruction selection và register allocation không hoàn toàn độc lập.

Ví dụ vectorize mạnh:

```text
+ throughput
- register pressure
```

có thể làm spill.

Optimizer cần cost model cân bằng.

---

# 31. Register pressure trước selection

Có thể có:

```text
pressure estimate
```

ở LIR.

Không cần chính xác.

Mục tiêu là giúp selector/optimizer tránh tạo quá nhiều temporary.

---

# 32. Physical register reservation

Một số register không được allocator dùng:

x86:

```text
RSP
RIP
```

và có thể:

```text
RBP
```

nếu frame pointer được giữ.

AArch64:

```text
SP
```

RISC-V:

```text
x0
```

là zero register.

Machine target phải khai báo:

```text
reserved = true
```

---

# 33. Frame pointer

Axiom không nên bắt buộc frame pointer.

Có thể:

```text
-fomit-frame-pointer
```

mặc định ở optimized builds.

Nhưng debug/unwind có thể yêu cầu frame pointer.

Vì vậy:

```text
FramePolicy {
    Omit
    Keep
    RequiredForUnwind
}
```

---

# 34. Callee-saved register usage

Nếu function dùng:

```text
RBX
```

trên SysV:

```text
RBX
```

là callee-saved.

Prologue:

```text
push RBX
```

hoặc equivalent frame allocation.

Epilogue:

```text
restore RBX
```

Nhưng đây **không phải Register Allocator tự emit**.

Allocator chỉ báo:

```text
used_callee_saved = {RBX}
```

Frame/prologue pass chịu trách nhiệm.

---

# 35. Đây là ranh giới rất quan trọng

```text
Register Allocation
    ↓
which physical registers?

Frame Layout
    ↓
where are stack objects?

Prologue/Epilogue
    ↓
how preserve ABI state?
```

Không gộp ba thứ thành một pass khổng lồ.

---

# 36. Spill + CALL

Ví dụ:

```text
v1 = ...
CALL foo
USE v1
```

Nếu `v1` không thể đặt callee-saved:

```text
STORE [spill], v1
CALL foo
LOAD v1
```

Nếu đặt được:

```text
RBX = v1
CALL foo
USE RBX
```

Code tốt hơn.

---

# 37. ABI argument registers

Call:

```text
foo(a,b,c)
```

SysV:

```text
a → RDI
b → RSI
c → RDX
```

Machine IR trước RA:

```text
ABI_ARG v_a, #0
ABI_ARG v_b, #1
ABI_ARG v_c, #2
```

ABI lowering đã xác định location class.

Allocator sau đó giải quyết move vào physical register.

---

# 38. Argument move coalescing

Nếu:

```text
a → RDI
```

và `a` vốn đã được allocate:

```text
RDI
```

→ không cần move.

Đây là optimization rất đáng giá.

---

# 39. Return values

Ví dụ:

```text
return v1
```

ABI:

```text
v1 → RAX
```

Nếu allocator đã đặt:

```text
v1 → RAX
```

→ zero move.

---

# 40. Multi-register return

Ví dụ aggregate:

```text
return {a,b}
```

ABI có thể:

```text
a → RAX
b → RDX
```

Allocator phải xử lý hai fixed outputs.

---

# 41. SIMD registers

Không nên dùng chung pool:

```text
GPR
FPR
Vector
```

Trừ khi target thực sự alias chúng.

Ví dụ x86:

```text
GPR pool
XMM pool
```

độc lập.

---

# 42. Register width

Không nên coi:

```text
RAX
EAX
```

là hai register allocation candidate độc lập.

Chúng là cùng register units.

Nhưng Machine IR phải biết:

```text
32-bit write → zero-extends RAX
```

trên x86-64.

Ví dụ:

```text
MOV EAX, 1
```

làm:

```text
RAX = 1
```

Đây là semantics của instruction, không phải allocator.

---

# 43. Zero-extension optimization

Ví dụ:

```text
v1 : u32
```

được định nghĩa bằng:

```text
EAX
```

và sau đó cần:

```text
u64
```

không nhất thiết cần:

```text
MOVZX RAX,EAX
```

vì write vào EAX đã zero-extend.

Selector + register information có thể loại bỏ instruction.

---

# 44. Spill/reload insertion

Spill pass tạo:

```text
SPILL v1 → slot3
RELOAD slot3 → v1
```

trước khi physical assignment hoàn tất.

Sau đó rewrite:

```text
v1
```

thành physical register hoặc temporary.

---

# 45. Spill temporary

Một reload:

```text
LOAD RAX,[slot]
```

có thể conflict với live `RAX`.

Allocator phải chọn register tạm phù hợp.

Nếu không có register:

```text
spill/reload cascade
```

có thể xảy ra.

MVP allocator cần phát hiện và giới hạn.

---

# 46. Không cho spill vô hạn

Compiler phải có invariant:

```text
Nếu allocator không thể satisfy constraints:
    structured compiler diagnostic / backend ICE
```

Không được:

```text
loop forever
```

---

# 47. Impossible constraints

Ví dụ target instruction yêu cầu:

```text
output = RAX
input1 = RAX
input2 = RAX
```

nhưng semantics yêu cầu hai input độc lập.

Nếu constraint không thể satisfy:

```text
TargetLegalizationError
```

hoặc backend ICE nếu compiler đã chứng minh pattern hợp lệ.

---

# 48. Post-RA invariant

Sau Register Allocation:

```text
∀ instruction:
    no VirtualRegister
```

Chỉ còn:

```text
PhysicalRegister
StackSlot
Immediate
Memory
Symbol
Label
...
```

---

# 49. Nhưng StackSlot vẫn còn

Đúng.

Post-RA:

```text
RAX
RBX
StackSlot #3
```

vẫn hợp lệ.

Sau frame layout mới biến:

```text
StackSlot #3
```

thành:

```text
[SP + 64]
```

hoặc:

```text
[FP - 32]
```

---

# 50. Machine IR sau RA

Ví dụ trước:

```text
v1 = CONST 10
v2 = CONST 20
v3 = ADD v1,v2
RET v3
```

Sau:

```text
MOV RAX, 10
MOV RCX, 20
ADD RAX, RCX
RET RAX
```

Không còn:

```text
type
ownership
trait
view
future
Option
Result
```

Chúng đã biến mất từ các tầng trước.

---

# 51. Invariants

Đóng băng nhóm:

### ARA-20
**Every Virtual Register Has Exactly One Register Class**

### ARA-21
**Register Allocation Respects Register Classes**

### ARA-22
**Register Allocation Respects Register Units**

### ARA-23
**Overlapping Live Values Cannot Share Conflicting Register Units**

### ARA-24
**Fixed Register Constraints Are Mandatory**

### ARA-25
**Tied Operands Are Preserved**

### ARA-26
**Early-Clobber Constraints Are Preserved**

### ARA-27
**Call-Clobbered Registers Cannot Hold Required Live Values Across Calls**

### ARA-28
**Reserved Registers Are Never Allocated**

### ARA-29
**Spill Slots Have Explicit Stack-Storage Identity**

### ARA-30
**Spilling Preserves Program Semantics**

### ARA-31
**Reloads Occur Before Required Uses**

### ARA-32
**Spills Occur After Required Definitions**

### ARA-33
**Rematerialization Is Semantics-Preserving**

### ARA-34
**Register Coalescing Cannot Introduce Conflicts**

### ARA-35
**Parallel Copies Are Resolved Without Data Loss**

### ARA-36
**ABI Register Requirements Are Preserved**

### ARA-37
**Callee-Saved Register Usage Is Reported To Frame Lowering**

### ARA-38
**Stack Slots May Be Reused Only When Lifetimes Do Not Overlap**

### ARA-39
**Post-RA Machine IR Contains No Virtual Registers**

### ARA-40
**Post-RA Machine IR Contains Only Target-Legal Register Assignments**

### ARA-41
**Allocator Termination Is Guaranteed**

### ARA-42
**Allocator Behavior Is Deterministic For A Fixed Input**

### ARA-43
**Register Pressure Is A Compilation Cost, Not A Language Semantic**

### ARA-44
**Allocator Does Not Modify High-Level Program Semantics**

---

# 52. Backend lúc này

Chúng ta đã có:

```text
LIR
 ↓
Legalization
 ↓
Instruction Selection
 ↓
Machine IR
 ↓
Machine Optimization
 ↓
Register Allocation
 ↓
Spill / Reload
 ↓
Frame Layout
 ↓
Prologue / Epilogue
 ↓
Post-RA Optimization
 ↓
Machine Verify
 ↓
Encoding
```

Điểm tiếp theo rất tự nhiên là:

# `MACHINE-IR-005 — Frame Layout, Stack Frame & Prologue/Epilogue`

Phần này sẽ chốt một loạt vấn đề quan trọng còn lại:

```text
Stack frame
Red zone
Shadow space
Stack alignment
Outgoing argument area
Incoming arguments
Local variables
Spill slots
Dynamic stack allocation
Stack probes
Stack canaries
TLS
Callee-saved registers
Frame pointer
Unwind metadata
Windows x64
SysV x86-64
AArch64
RISC-V
```

Đặc biệt cần thiết kế sao cho **Axiom không mặc định tạo stack frame nặng nề**: một hàm đơn giản như

```text
fn add(a: i64, b: i64) -> i64 {
    a + b
}
```

phải có khả năng hạ trực tiếp thành kiểu:

```text
ADD return_register, arg_register
RET
```

**không stack frame, không runtime, không prologue/epilogue thừa** nếu ABI và target cho phép.