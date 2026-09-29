# XLVIII — REGALLOC-001: Register Allocation

Ta tiếp tục từ Machine IR. Mục tiêu của phase này là biến:

```text
Virtual Registers
        ↓
Live Intervals
        ↓
Linear Scan
        ↓
Physical Registers + Spill Slots
```

và phải hoạt động đúng cho **Windows x64 trước**, nhưng không được khóa allocator vào Windows.

---

## 1. Kiến trúc

```text
Machine IR
    ↓
Liveness Analysis
    ↓
Live Intervals
    ↓
Register Constraint Analysis
    ↓
Linear Scan Allocator
    ↓
Spill/Reload
    ↓
Allocated Machine IR
```

Tôi đề xuất tách 4 thành phần:

```text
compiler/backend/x86_64/regalloc/
├── liveness.ax
├── interval.ax
├── constraints.ax
├── linear_scan.ax
├── spill.ax
└── tests/
```

---

# 2. Liveness Analysis

Machine IR không nên dựa vào lexical scope.

Ví dụ:

```text
bb0:
    %a = ...
    %b = ...
    %c = ADD %a, %b
    ...
    RETURN %c
```

`%a` chết sau instruction `ADD`.

Ta cần:

```text
LiveRange {
    start
    end
}
```

Nhưng với CFG, một value có thể sống qua nhiều block.

Do đó trước tiên tính:

```text
LIVE_IN[block]
LIVE_OUT[block]
```

theo dataflow:

```text
LIVE_OUT[B] =
    union LIVE_IN[S]
    for S in successors(B)

LIVE_IN[B] =
    USE[B] ∪ (LIVE_OUT[B] - DEF[B])
```

---

# 3. Instruction numbering

Mỗi instruction nhận một position:

```text
0
2
4
6
...
```

Tôi khuyên dùng khoảng cách `2` thay vì `1`.

Lý do: sau này có thể chèn instruction giữa:

```text
10
12
```

thành:

```text
10
11
12
```

mà không cần renumber toàn bộ.

Nếu quá nhiều insertion thì có thể renumber lại.

---

# 4. Live Interval

```text
LiveInterval {
    vreg
    class
    ranges[]
    uses[]
    weight
}
```

Ví dụ:

```text
%a:
    [2,8]

%b:
    [4,10]

%c:
    [8,14]
```

Không phải mọi interval đều liên tục.

Ví dụ branch:

```text
[a,b] + [f,h]
```

thì:

```text
ranges = [
    [a,b],
    [f,h]
]
```

Điều này rất quan trọng khi optimizer bắt đầu tạo CFG phức tạp.

---

# 5. Use Position

Mỗi use:

```text
UsePosition {
    position
    kind
    constraint
}
```

Ví dụ:

```text
USE
LAST_USE
FIXED_REGISTER
CALL_CLOBBER
```

Sau này có thể dùng use-distance để quyết định spill.

---

# 6. Register Constraint

Một value bình thường:

```text
%a : GPR64
```

có thể dùng:

```text
RAX RBX RCX ...
```

Nhưng một instruction có thể yêu cầu:

```text
RAX
```

Ví dụ:

```text
IDIV
```

vì x86 quy định dividend nằm ở:

```text
RDX:RAX
```

Do đó:

```text
RegisterConstraint {
    allowed
    fixed
    tied
}
```

---

# 7. Fixed Register

Machine instruction:

```text
IDIV rbx
```

semantic machine constraints:

```text
implicit_use  RAX
implicit_use  RDX
implicit_def  RAX
implicit_def  RDX
```

Allocator phải đảm bảo value đúng nằm ở các register đó.

Không giải quyết fixed register ở encoder.

---

# 8. CALL clobber

Đây là constraint cực kỳ quan trọng.

Windows x64:

```text
caller_saved =
    RAX RCX RDX R8 R9 R10 R11
```

Nếu:

```text
%a
CALL foo
USE %a
```

thì `%a` sống qua CALL.

Không được để `%a` trong:

```text
RAX
RCX
RDX
R8
R9
R10
R11
```

trừ khi allocator chèn save/reload.

---

# 9. Cách xử lý

Có hai lựa chọn:

### A. Callee-saved register

```text
%a → RBX
```

và frame pass save RBX.

### B. Spill

```text
STORE %a → [spill0]

CALL foo

LOAD [spill0] → register
```

Allocator chọn dựa trên cost.

---

# 10. Windows vs Linux

Allocator không nên hard-code:

```text
RAX RCX ...
```

thành caller-save.

Thay vào đó:

```text
RegisterConvention {
    caller_saved
    callee_saved
    argument_registers
    return_registers
}
```

Windows:

```text
caller_saved =
RAX RCX RDX R8 R9 R10 R11
```

SysV:

```text
caller_saved =
RAX RCX RDX RSI RDI
R8 R9 R10 R11
```

Allocator chỉ đọc convention.

---

# 11. Linear Scan

Thuật toán cơ bản:

```text
sort intervals by start

active = []

for current in intervals:
    expire_old_intervals(current.start)

    if register available:
        assign register

    else:
        choose spill candidate
        spill candidate
        assign its register to current
```

Deterministic ordering:

```text
(start,
 end,
 vreg_id)
```

Không phụ thuộc hash-map iteration.

---

# 12. Chọn spill candidate

MVP:

> Spill interval có next-use xa nhất.

Ví dụ:

```text
current = 20

a next use = 22
b next use = 1000
```

nên ưu tiên spill:

```text
b
```

vì chưa cần dùng sớm.

---

# 13. Spill cost

Về sau:

```text
spill_cost =
    use_count
    × loop_weight
    × register_pressure
```

Loop:

```text
while (...) {
    ...
}
```

phải có trọng số lớn hơn code chạy một lần.

Ví dụ:

```text
loop depth = 3
```

thì value trong loop có cost cao hơn value ngoài loop.

---

# 14. Register preference

Allocator không chỉ cần:

> register nào còn trống?

mà còn:

> register nào giúp tránh MOV?

Ví dụ:

```text
%a → RAX
%result cần RAX
```

thì tốt.

Nhưng:

```text
%a → RBX
MOV RAX,RBX
```

tạo thêm instruction.

Vì vậy:

```text
RegisterPreference {
    preferred[]
}
```

sẽ được thêm.

---

# 15. Coalescing

Ví dụ:

```text
%a = ...
%b = COPY %a
USE %b
```

Nếu:

```text
%a → RAX
%b → RAX
```

thì COPY biến mất.

MVP Linear Scan có thể làm local coalescing đơn giản:

```text
COPY a → b
```

ưu tiên cùng physical register nếu lifetime không conflict.

---

# 16. Parallel moves

ABI lowering thường tạo:

```text
%a → RCX
%b → RDX
```

Nếu source đã ở đúng register:

```text
%a = RCX
```

thì không phát sinh MOV.

Đây là một optimization rất đáng giá ở backend.

---

# 17. Spill slot

```text
SpillSlot {
    id
    size
    alignment
    class
}
```

Ví dụ:

```text
slot0: 8 bytes, align 8
slot1: 4 bytes, align 4
```

Spill slot cũng phải được reuse.

Nếu:

```text
a spill [2,10]
b spill [20,30]
```

có thể dùng cùng slot.

---

# 18. Spill Slot Allocation

Sau register allocation:

```text
Virtual spill slots
        ↓
Stack slot coloring
        ↓
Physical offsets
```

Ví dụ:

```text
slot0 → [RSP+8]
slot1 → [RSP+16]
slot2 → [RSP+8]
```

`slot0` và `slot2` không sống đồng thời.

---

# 19. Không dùng stack slot quá sớm

Đừng:

```text
%a → [rsp+8]
```

ngay từ semantic MIR.

Spill là:

> hậu quả của register pressure.

Không phải source-level storage.

---

# 20. Register Allocation Output

Input:

```text
%a:GPR64
%b:GPR64
%c:GPR64
```

Output:

```text
%a → RCX
%b → RDX
%c → RAX
```

hoặc:

```text
%a → RCX
%b → [spill0]
%c → RAX
```

---

# 21. Machine IR sau allocation

Trước:

```text
bb0:
    %v0 = MOVri 10
    %v1 = MOVri 20
    %v2 = ADD %v0, %v1
    RETURN %v2
```

Sau:

```text
bb0:
    ECX = MOVri 10
    EDX = MOVri 20
    EAX = ADD ECX, EDX
    RETURN EAX
```

---

# 22. Nhưng có thể tốt hơn

Optimizer/backend coalescing có thể nhận ra:

```text
MOV ECX,10
MOV EDX,20
ADD ECX,EDX
MOV EAX,ECX
```

và biến thành:

```text
MOV EAX,10
ADD EAX,20
RET
```

hoặc:

```text
MOV EAX,30
RET
```

nếu constant folding chưa làm việc đó.

Đây là lý do register allocation không phải optimization cuối cùng duy nhất.

---

# 23. Register allocator không thay đổi semantics

Invariant rất quan trọng:

```text
AREG-33
Register allocation may change physical storage only.
```

Không được:

```text
checked add → wrapping add
```

Không được:

```text
atomic → normal load
```

Không được:

```text
volatile → normal memory access
```

Không được:

```text
Drop → omitted
```

trừ khi optimization đã chứng minh Drop không observable.

---

# 24. Machine verifier sau allocation

Phải chạy lại:

```text
MachineVerifier
```

với các check mới:

```text
physical register hợp lệ
register class đúng
alias conflict
fixed register constraint
spill slot hợp lệ
call clobber
```

---

# 25. Frame Layout tiếp theo

Sau allocation ta có đủ thông tin:

```text
used callee-saved registers
spill slots
local stack objects
outgoing arguments
shadow space
```

→ tính frame:

```text
FrameLayout
```

---

# 26. Windows frame

Ví dụ function dùng:

```text
RBX
R12
```

và có:

```text
3 spill slots
```

Frame builder có thể tạo:

```text
saved RBX
saved R12
spill0
spill1
spill2
shadow space
alignment
```

---

# 27. Prologue/Epilogue Generation

Input:

```text
FrameLayout
```

Output:

```text
PROLOGUE:
    save callee-saved
    allocate stack

BODY

EPILOGUE:
    deallocate stack
    restore callee-saved
    RET
```

Nhưng prologue/epilogue phải là **Machine IR**, không emit bytes trực tiếp.

---

# 28. Tại sao?

Để encoder không biết:

```text
function frame
ABI
spill
callee-save
```

Encoder chỉ biết:

```text
PUSH
POP
MOV
SUB
ADD
RET
```

Kiến trúc sạch hơn rất nhiều.

---

# 29. Frame pointer

v0.1:

```text
frame_pointer = optional
```

Mặc định:

```text
omit frame pointer
```

nếu:

- không cần dynamic stack;
- không cần debug policy yêu cầu;
- không có target constraint.

Sau này `-fno-omit-frame-pointer` tương đương có thể hỗ trợ cho profiling/debug.

---

# 30. Stack probing

Windows có một vấn đề cần tính đến sau này: stack allocation rất lớn có thể cần stack probing.

Không nên nhét vào generic frame builder.

Tạo:

```text
StackProtectionPolicy
```

và Windows lowering quyết định.

MVP chỉ cần hỗ trợ frame nhỏ.

---

# 31. `alloca` / dynamic stack

Không đưa dynamic stack allocation vào MVP backend đầu tiên.

Khi thêm:

```axiom
let x = dynamic_stack(...)
```

hoặc intrinsic tương đương, frame model phải hỗ trợ:

```text
dynamic_stack = true
```

và lúc đó frame pointer có thể trở thành cần thiết.

---

# 32. REGALLOC tests

### Test 1

```text
1 virtual register
```

→ một physical register.

### Test 2

```text
2 overlapping GPR
```

→ khác register.

### Test 3

```text
non-overlapping
```

→ reuse register.

### Test 4

```text
value live across CALL
```

→ callee-saved hoặc spill.

### Test 5

```text
fixed RAX constraint
```

→ allocator xử lý đúng.

### Test 6

```text
GPR + XMM
```

→ không cross-class.

### Test 7

```text
register alias
```

→ `EAX` conflict `RAX`.

### Test 8

```text
forced spill
```

→ đúng load/store.

---

# 33. Test quan trọng nhất

Tạo một function có > số GPR khả dụng:

```text
v0
v1
v2
...
v20
```

sau đó:

```text
use(v0)
use(v1)
...
use(v20)
```

Expected:

```text
register allocation succeeds
```

không được crash compiler.

Nếu spill xảy ra:

```text
MachineVerifier
```

phải chứng minh mọi value vẫn đúng.

---

# 34. Allocation invariant hoàn chỉnh

```text
AREG-20
Every virtual register has a valid register class.

AREG-21
Overlapping live ranges cannot occupy conflicting storage.

AREG-22
Register aliases represent overlapping physical storage.

AREG-23
Fixed-register constraints are explicit.

AREG-24
CALL instructions model ABI clobbers.

AREG-25
Values live across calls are preserved.

AREG-26
Spill slots have valid size and alignment.

AREG-27
Reload restores the same semantic value.

AREG-28
Allocation is deterministic.

AREG-29
Allocation preserves machine semantics.

AREG-30
Allocation does not alter ownership semantics.

AREG-31
Spilling is compiler-internal storage.

AREG-32
Physical register assignment occurs after target lowering.

AREG-33
Register allocation cannot change observable arithmetic semantics.

AREG-34
Register allocation cannot remove required memory ordering.

AREG-35
Register allocation cannot remove required volatile operations.

AREG-36
Register allocation cannot invalidate ABI requirements.
```

---

# XLIX — FRAME-001: Frame Layout + Prologue/Epilogue

Bây giờ ta chốt frame model.

```text
Allocated Machine IR
        ↓
Frame Analysis
        ↓
Frame Layout
        ↓
Prologue/Epilogue
```

## FrameInfo

```text
FrameInfo {
    locals[]
    spills[]
    saved_registers[]
    outgoing_args_size
    shadow_space_size
    alignment
    stack_size
    has_frame_pointer
    has_dynamic_stack
}
```

---

## Windows x64 frame

Tối thiểu phải tính:

```text
shadow space = 32 bytes
```

ngoài:

```text
spill
local
saved-register
alignment
```

---

## Frame invariants

```text
AFRAME-20
Stack frame size is computed from actual frame requirements.

AFRAME-21
Stack alignment is valid at every call boundary.

AFRAME-22
Windows x64 reserves required shadow space.

AFRAME-23
Callee-saved registers are preserved exactly when required.

AFRAME-24
Leaf functions may omit a frame.

AFRAME-25
Frame pointer is optional unless required by semantics/backend constraints.

AFRAME-26
Spill slots do not overlap live stack objects.

AFRAME-27
Prologue and epilogue restore the original stack state.

AFRAME-28
Dynamic stack allocation is represented explicitly.

AFRAME-29
Frame construction is deterministic.

AFRAME-30
Frame layout is independent of source-level variable location.
```

---

# 35. Một điểm quan trọng cho mục tiêu "nhỏ như ASM"

Với:

```axiom
@entry
fn main() -> i32 {
    42
}
```

compiler **không nên tạo**:

```text
push rbp
mov rbp,rsp
sub rsp,...
...
add rsp,...
pop rbp
ret
```

nếu không cần.

Mục tiêu Machine IR cuối cùng phải có thể chỉ còn:

```text
MOV EAX, 42
RET
```

Startup riêng mới lo phần process entry.

Đây chính là cách Axiom đạt mục tiêu **abstraction không tạo overhead nếu không có semantic reason**.

---

Bước kế tiếp là **L — Instruction Selection**: biến các operation của LIR như `ADD_CHECKED`, `LOAD`, `STORE`, `BRANCH`, `CALL`, `CAST` thành các instruction form x86 cụ thể, bao gồm lựa chọn `MOV/LEA`, immediate form, `CMP+Jcc`, checked arithmetic và các fixed-register instruction. Sau đó mới đến encoder byte-level.