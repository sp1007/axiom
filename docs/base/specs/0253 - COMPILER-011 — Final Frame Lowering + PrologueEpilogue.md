Tiếp tục.

# COMPILER-011 — Final Frame Lowering + Prologue/Epilogue

Đây là bước nối **Register Allocation** với **Machine Encoding**.

Nguyên tắc chính:

> **Frame lowering không quyết định chương trình cần làm gì; nó chỉ biến các yêu cầu storage/ABI của function thành stack layout và machine-level entry/exit sequence.**

Pipeline:

```text
Physical Machine IR
        │
        ▼
Final Frame Analysis
        │
        ├── Spill slots
        ├── Callee-saved registers
        ├── Local stack objects
        ├── Outgoing arguments
        ├── SRet
        ├── Dynamic stack
        ├── Alignment
        ├── Security
        └── Debug/Unwind
        │
        ▼
Frame Layout
        │
        ▼
Prologue/Epilogue Lowering
        │
        ▼
Final Machine IR
        │
        ▼
Post-Frame Verification
        │
        ▼
Instruction Encoding
```

---

# 1. Không phải function nào cũng có stack frame

Đây phải là một nguyên tắc rất mạnh của Axiom.

Ví dụ:

```text
fn add(a: i64, b: i64) -> i64 {
    a + b
}
```

hoàn toàn có thể:

```text
add:
    add rax, rdx
    ret
```

Không cần:

```text
push rbp
mov rbp, rsp
sub rsp, 64
...
```

Do đó:

```text
needs_frame = false
```

là trường hợp bình thường.

### ARFRAME-20

> **Axiom does not require a stack frame for every function.**

---

# 2. Khi nào cần frame?

Frame chỉ xuất hiện nếu có ít nhất một requirement:

```text
NeedsFrame =
    SpillSlots
  | CalleeSaved
  | LocalStackStorage
  | OutgoingStackArgs
  | SRetStorage
  | DynamicStackAllocation
  | StackCanary
  | StackProbe
  | RequiredFramePointer
  | DebugRequirement
  | UnwindRequirement
  | TargetSecurityRequirement
```

Không có requirement:

```text
frame_size = 0
```

---

# 3. Hai loại stack storage phải tách biệt

Axiom đã có distinction:

```text
Semantic Storage
```

và:

```text
Compiler Storage
```

Frame phải giữ distinction này.

### Semantic stack object

Ví dụ source:

```text
var buffer: [1024]u8;
```

nếu address observable hoặc storage contract yêu cầu.

### Compiler stack object

Ví dụ:

```text
spill v17
```

Không tồn tại trong semantics của source.

Do đó:

```text
FrameObjectKind =
    Local
    Spill
    IncomingArg
    OutgoingArg
    SRet
    SavedRegister
    Canary
    Temporary
    AlignmentPadding
```

---

# 4. Frame object

Định nghĩa:

```text
FrameObject {
    id
    kind
    size
    alignment
    lifetime
    addressability
    preferred_region
    debug_identity
}
```

Ví dụ:

```text
spill0:
    kind = Spill
    size = 8
    align = 8

local3:
    kind = Local
    size = 64
    align = 16
```

---

# 5. Frame Layout không được phụ thuộc source variable

Một function có thể:

```text
source local x
```

nhưng compiler quyết định:

```text
register
```

→ không có frame object.

Ngược lại:

```text
v17
```

là compiler temporary nhưng register pressure cao:

```text
spill0
```

→ xuất hiện frame object.

Đây là lý do:

> **Source variable ≠ stack slot.**

---

# 6. Frame layout hai giai đoạn

Ta đã quyết định từ COMPILER-010:

### Pre-RA

Biết:

```text
dynamic_alloca
sret
outgoing_call_requirement
address_taken_local
ABI requirements
```

### Post-RA

Biết:

```text
spill slots
used callee-saved registers
actual stack requirements
```

Do đó:

```text
PreRAFrameAnalysis
        ↓
Register Allocation
        ↓
PostRAFrameAnalysis
        ↓
FinalFrameLayout
```

---

# 7. FinalFrameLayout

Đề xuất:

```text
FinalFrameLayout {
    frame_size
    stack_alignment

    objects[]
    spill_slots[]
    saved_registers[]

    outgoing_arg_area
    incoming_arg_area
    sret_area

    local_area
    dynamic_area

    canary_location
    shadow_stack_state

    frame_pointer
    stack_pointer_adjustment

    red_zone_usage
}
```

---

# 8. Frame base abstraction

Không hard-code:

```text
rbp
```

hoặc:

```text
rsp
```

vào generic frame engine.

Dùng:

```text
FrameBase =
    StackPointer
    FramePointer
    BasePointer
    TargetSpecific
```

Target quyết định.

Ví dụ x86-64:

```text
rsp + offset
```

hoặc:

```text
rbp - offset
```

AArch64:

```text
sp + offset
```

RISC-V:

```text
sp + offset
```

---

# 9. Frame pointer không bắt buộc

Mặc định:

```text
omit_frame_pointer = true
```

nếu ABI/target cho phép.

Ví dụ:

```text
push rbp
mov rbp,rsp
```

không cần thiết chỉ vì function có local variable.

Nếu stack layout cố định, compiler có thể dùng:

```text
rsp + offset
```

trực tiếp.

---

# 10. Khi nào cần frame pointer?

Ví dụ:

- target yêu cầu;
- dynamic stack allocation;
- debug profile yêu cầu;
- security profile yêu cầu;
- unwind policy;
- platform-specific ABI.

Do đó:

```text
FramePointerPolicy {
    Auto
    Omit
    Keep
    Required
}
```

---

# 11. Red Zone

Một số ABI, đặc biệt SysV x86-64, có red zone.

Function leaf có thể sử dụng vùng stack bên dưới `rsp` mà không điều chỉnh `rsp`, trong điều kiện ABI cho phép.

Ví dụ concept:

```text
rsp
 ↓
────────────
 red zone
────────────
```

Axiom nên hỗ trợ:

```text
RedZonePolicy =
    Disabled
    Enabled
    TargetDefault
```

Nhưng compiler phải biết khi nào không được dùng.

Ví dụ:

- interrupt;
- kernel;
- signal-sensitive context;
- target ABI không hỗ trợ.

---

# 12. Red zone không phải semantic storage

Nếu compiler đặt:

```text
spill0
```

vào red zone:

đó vẫn chỉ là:

```text
Compiler Storage
```

Không được biến red zone thành language-level guarantee.

---

# 13. Stack alignment

Final frame phải thỏa ABI:

```text
frame_base % required_alignment == required_value
```

Alignment có thể đến từ:

```text
local
spill
SIMD
ABI
call requirement
dynamic allocation
```

Ví dụ:

```text
max_alignment =
    max(
        local_alignment,
        spill_alignment,
        ABI_alignment
    )
```

sau đó frame size được round lên phù hợp.

---

# 14. Outgoing argument area

Một function có thể gọi:

```text
foo(a,b,c,d,e,f,g)
```

Một số ABI truyền một phần argument qua stack.

Frame cần:

```text
OutgoingArgArea
```

Nhưng không nên mặc định reserve một vùng lớn.

Có thể:

```text
max_outgoing_stack_args
```

được tính từ tất cả call sites.

Ví dụ:

```text
call foo → 16 bytes stack
call bar → 64 bytes stack
```

thì:

```text
outgoing_area = 64
```

nếu ABI cho phép reuse.

---

# 15. Call-site stack arguments

Một số ABI yêu cầu caller cleanup, một số khác có quy tắc khác.

Frame lowering phải lấy từ:

```text
CallingConvention
```

chứ không hard-code.

Ví dụ:

```text
CallFramePolicy {
    caller_allocates
    callee_allocates
    shadow_space
    alignment
    cleanup
}
```

---

# 16. Windows shadow space

Win64 có home/shadow space.

Axiom không nên tạo một quy tắc riêng trong generic code kiểu:

```text
if windows:
    add 32
```

Thay vào đó:

```text
CallingConvention::Win64
    → required_home_space = 32
```

Frame engine chỉ đọc ABI requirement.

Đây là pattern cần giữ cho mọi target.

---

# 17. SRet

Nếu function trả aggregate lớn bằng hidden return pointer:

```text
fn make_big() -> Big
```

ABI lowering có thể tạo:

```text
hidden sret pointer
```

Frame lowering phải biết:

```text
SRetMode =
    CallerProvided
    CalleeProvided
```

Thông thường Axiom ưu tiên:

> **Caller-allocated return storage khi ABI cho phép.**

Điều này tránh allocation không cần thiết.

---

# 18. Callee-saved registers

Sau RA:

```text
used_callee_saved = {
    RBX,
    R12
}
```

Frame layout tạo:

```text
SavedRegister {
    physical_reg
    location
    save_offset
    restore_offset
}
```

Prologue:

```text
save RBX
save R12
```

Epilogue:

```text
restore R12
restore RBX
```

Thứ tự phải phù hợp ABI/unwind.

---

# 19. Không nhất thiết dùng PUSH/POP

Đây là một quyết định đáng giữ.

Generic frame lowering không nên coi:

```text
push
pop
```

là bắt buộc.

Target có thể dùng:

```text
store [sp+offset]
load [sp+offset]
```

hoặc:

```text
stp/ldp
```

trên AArch64.

Ví dụ AArch64:

```text
stp x29, x30, [sp, #-16]!
```

đồng thời save hai register.

Do đó generic concept là:

```text
SAVE_REGISTER
RESTORE_REGISTER
```

Target lowering mới biến thành instruction cụ thể.

---

# 20. Prologue abstraction

Đề xuất:

```text
PrologueStep =
    AdjustStack(size)
    SetFramePointer
    SaveRegister(reg)
    InitializeCanary
    StackProbe(size)
    SecuritySetup
    TargetSpecific(...)
```

Epilogue:

```text
EpilogueStep =
    SecurityCheck
    RestoreRegister(reg)
    RestoreFramePointer
    AdjustStack(-size)
    Return
```

Sau đó target backend hạ thành Machine IR cụ thể.

---

# 21. Stack canary

Không đưa stack canary vào Core language semantics.

Nó thuộc:

```text
SecurityProfile
```

Ví dụ:

```text
SecurityProfile {
    stack_canary
    shadow_stack
    cet
    bti
    pac
    stack_probe
}
```

Nếu bật:

```text
canary_location
```

trở thành FrameObject.

Prologue:

```text
load canary
store frame.canary
```

Epilogue:

```text
load frame.canary
compare
trap if changed
```

---

# 22. W^X / executable stack

Frame lowering không trực tiếp quản lý W^X.

Nhưng target metadata phải đảm bảo:

```text
stack = RW
```

không:

```text
RWX
```

trừ khi explicit low-level profile yêu cầu.

---

# 23. Stack probes

Function:

```text
fn huge() {
    var x: [8MB]u8;
}
```

không thể luôn đơn giản:

```text
sub rsp, 8MB
```

trên một số platform, vì có stack guard-page semantics.

Target có thể yêu cầu:

```text
stack probes
```

Frame analysis:

```text
needs_stack_probe = frame_size > threshold
```

Sau đó:

```text
StackProbe(size)
```

được target-specific lowering.

---

# 24. Dynamic stack allocation

Axiom hỗ trợ low-level dynamic stack allocation.

Ví dụ:

```text
alloca(n)
```

Nhưng đây là system-level operation, không phải ordinary array semantics.

Frame phải phân biệt:

```text
FixedFrame
```

và:

```text
DynamicStackArea
```

Nếu dynamic stack tồn tại:

```text
rsp
```

không còn là base ổn định cho mọi fixed object.

Do đó có thể cần:

```text
frame pointer
```

hoặc target-specific stable base.

---

# 25. Dynamic stack lifetime

Dynamic allocation:

```text
alloca(n)
```

có lifetime gắn với execution frame/control region.

Không được:

```text
return pointer_to_dynamic_stack
```

trong safe Axiom nếu provenance không còn hợp lệ.

Đây đã được ownership/capability verifier xử lý trước.

Frame lowering chỉ hiện thực hóa contract đó.

---

# 26. Tail call

Tail call là trường hợp đặc biệt.

Ví dụ:

```text
fn f(x) {
    return g(x);
}
```

có thể:

```text
jmp g
```

thay vì:

```text
call g
ret
```

Nhưng chỉ nếu:

```text
ABI compatible
argument layout compatible
return ABI compatible
frame can be eliminated
callee preserves required state
```

Do đó:

```text
TailCallKind =
    None
    Eligible
    Guaranteed
```

---

# 27. Tail call phải hủy frame trước jump

Nếu function đã tạo frame:

```text
sub rsp, 128
```

thì trước tail jump cần:

```text
restore frame
jmp target
```

hoặc target-specific equivalent.

Nếu không thể, tail call không hợp lệ.

---

# 28. `musttail` không cần ở Core v1

Axiom không nên thêm:

```text
musttail
```

vào ngôn ngữ chỉ để ép backend.

Có thể có system-level attribute sau này:

```text
@must_tail
```

nhưng v1:

> compiler tự quyết định tail-call optimization nếu semantics/ABI cho phép.

---

# 29. Epilogue duplication

Có hai lựa chọn:

```text
return blocks
```

có thể:

```text
jump common_epilogue
```

hoặc:

```text
duplicate epilogue
```

Ví dụ:

```text
if error:
    restore
    ret

normal:
    restore
    ret
```

có thể lớn hơn nhưng branch tốt hơn.

Machine optimizer quyết định sau đó.

Frame lowering nên tạo representation có thể tối ưu.

---

# 30. Multiple epilogues

Machine IR nên cho phép:

```text
EpilogueRegion
```

ở nhiều basic block.

Không ép tất cả return về một block.

Điều này quan trọng cho:

- branch prediction;
- code size;
- tail calls;
- cold error paths.

---

# 31. Panic/unwind integration

Nếu:

```text
panic=abort
```

thì unwind metadata có thể không cần.

Nếu:

```text
panic=unwind
```

thì frame/prologue/epilogue phải có unwind state chính xác.

Ví dụ:

```text
entry
 ↓
save RBX
 ↓
sub rsp,64
 ↓
...
```

unwind engine phải biết tại mỗi instruction range:

```text
RBX saved at [rsp+offset]
CFA = rsp + offset
```

---

# 32. Unwind không được sinh từ source

Đây là nguyên tắc quan trọng:

```text
Source
   ↓
Machine
   ↓
Final Frame
   ↓
Unwind metadata
```

Không phải:

```text
Source
   ↓
Unwind guessed independently
```

Vì optimizer/backend có thể:

- bỏ frame;
- đổi save location;
- shrink-wrap;
- split epilogue.

---

# 33. Shrink wrapping

Một optimization tương lai rất đáng hỗ trợ:

```text
function:
    hot path
    ...
    cold path cần RBX
```

Không cần save RBX ở entry toàn function.

Có thể:

```text
entry
  │
  ├── hot → return
  │
  └── cold
        ↓
      save RBX
        ↓
      ...
        ↓
      restore
```

Đây gọi là:

> **Shrink wrapping**

MVP có thể chưa bật.

Nhưng Frame model không được cản trở nó.

---

# 34. Prologue/Epilogue là Machine IR transformations

Không nên để encoder tự sinh:

```text
push rbp
...
pop rbp
```

Encoder chỉ encode instruction.

Đúng pipeline:

```text
Frame Requirements
       ↓
Frame Layout
       ↓
Prologue/Epilogue Lowering
       ↓
Machine Instructions
       ↓
Machine Optimizer
       ↓
Encoder
```

Như vậy mọi instruction đều được verifier nhìn thấy trước encoding.

---

# 35. Final Machine IR

Sau COMPILER-011:

```text
Machine IR
```

phải gần như machine-executable.

Không còn:

```text
virtual register
abstract spill
abstract save register
abstract frame object
```

Nhưng vẫn có:

```text
SymbolRef
Relocation
Fixup
DebugLoc
Unwind marker
```

để Object/Encoder xử lý.

---

# 36. Frame references

Ví dụ trước frame:

```text
LOAD spill0
```

Sau frame layout:

```text
LOAD [RSP + 40]
```

hoặc:

```text
LOAD [RBP - 24]
```

Đây là bước quan trọng:

```text
AbstractStackSlot
        ↓
ConcreteFrameAddress
```

---

# 37. Offset validation

Target phải kiểm tra instruction có encode được offset hay không.

Ví dụ một instruction chỉ cho displacement:

```text
[-128,127]
```

nhưng frame offset là:

```text
4096
```

thì instruction selection/legalization phải repair:

```text
load [rsp + 4096]
```

thành sequence thích hợp.

Không để encoder âm thầm thất bại.

---

# 38. Large frame offsets

Có thể cần:

```text
scratch register
```

Ví dụ:

```text
mov r11, rsp
add r11, 4096
mov rax, [r11]
```

Nhưng `r11` có thể đang live.

Vì vậy frame finalization phải phối hợp với register constraints.

Đây là lý do:

> **Frame lowering vẫn có thể cần target-specific register repair sau RA.**

Không nên giả định mọi stack offset đều encode trực tiếp.

---

# 39. Final repair pass

Đề xuất thêm:

```text
PostFrameLegalization
```

Pipeline:

```text
Final Frame Layout
        ↓
Frame Lowering
        ↓
PostFrame Legalization
        ↓
Machine Optimization
        ↓
Machine Verify
        ↓
Encoder
```

Nó xử lý:

- large stack offsets;
- impossible addressing modes;
- target-specific prologue forms;
- stack probe sequence;
- special ABI cases.

---

# 40. Nhưng không được allocator vòng lặp vô hạn

Ví dụ:

```text
RA
 ↓
frame
 ↓
large offset requires scratch register
 ↓
scratch register causes spill
 ↓
RA again
```

Đây có thể tạo complexity.

MVP nên tránh bằng cách:

1. reserve target scratch register nếu cần;
2. hoặc frame layout chọn offset/addressing strategy phù hợp;
3. hoặc target-specific repair dùng register đã được ABI cho phép clobber.

Không nên tạo:

```text
RA → frame → RA → frame → RA...
```

trong compiler pipeline chính.

---

# 41. Frame scratch register

Có thể khai báo:

```text
FrameLoweringInfo {
    reserved_scratch_registers
}
```

Ví dụ target có:

```text
FrameScratchReg = R11
```

nhưng chỉ reserve khi cần.

Mục tiêu:

> Không làm giảm register pressure toàn bộ function chỉ vì một frame offset hiếm gặp.

---

# 42. Security và special functions

Các function:

```text
@interrupt
@naked
@entry
@kernel
```

không nên dùng generic prologue mặc định.

Ví dụ:

```text
@interrupt fn handler(...)
```

có thể yêu cầu:

- save special registers;
- special return instruction;
- no red zone;
- fixed stack;
- target-specific ABI.

Do đó:

```text
FrameLoweringMode =
    Normal
    Interrupt
    Naked
    Kernel
    Entry
    TargetSpecific
```

---

# 43. `@naked`

`@naked` nên là **system-level unsafe contract**.

Compiler không tự thêm:

```text
prologue
epilogue
```

Programmer chịu trách nhiệm.

Nhưng compiler vẫn có thể kiểm tra:

- syntax;
- target;
- ABI;
- forbidden operations.

Đây không phải "tắt compiler".

---

# 44. Fiber integration

Fiber đã được thiết kế có stack riêng.

Frame lowering không cần biết:

```text
Fiber
```

là gì.

Nó chỉ biết:

```text
execution stack ABI
```

Fiber runtime cung cấp stack.

Do đó cùng Machine Function có thể chạy trên:

```text
OS thread stack
fiber stack
custom execution stack
```

nếu ABI contract tương thích.

Đây là separation rất tốt.

---

# 45. GPU kernel

GPU kernel không nên bị ép vào CPU stack-frame model.

`@kernel`:

```text
ExecutionDomain = GPU
```

có backend frame model riêng:

```text
GPUFrameModel
```

Có thể:

- registers;
- local memory;
- shared memory;
- private stack;
- no conventional call stack.

Vì vậy:

> **Frame abstraction là generic, nhưng frame implementation target/execution-domain specific.**

---

# 46. Axiom nên có `FrameModel`

Đề xuất:

```text
FrameModel =
    CpuStackFrame
    GpuKernelFrame
    WasmStackFrame
    Custom
```

CPU:

```text
CpuFrameLowering
```

WASM:

```text
WasmFrameLowering
```

GPU:

```text
GpuFrameLowering
```

Không nên cố dùng x86 stack assumptions cho WASM/GPU.

---

# 47. WASM

WASM không phải register machine.

Do đó COMPILER-011 phải cho phép:

```text
FrameModel::Wasm
```

với:

```text
locals
operand stack
linear memory
```

Thay vì:

```text
rsp/rbp
```

Điều này phù hợp quyết định từ COMPILER-009:

```text
MachineIRModel =
    RegisterMachine
    | StackMachine
    | Hybrid
```

---

# 48. Final frame algorithm

Có thể đóng băng:

```text
finalize_frame(function):
    requirements = analyze_frame(function)

    objects = collect_frame_objects(function)

    alignment = compute_required_alignment(
        ABI,
        target,
        objects,
        security
    )

    save_area = allocate_callee_saved(
        used_callee_saved
    )

    spill_area = allocate_spills(
        spill_slots
    )

    local_area = allocate_locals(
        semantic_stack_objects
    )

    outgoing_area = allocate_outgoing_args(
        call_sites
    )

    dynamic_area = determine_dynamic_area(
        dynamic_alloca
    )

    frame_size = layout(
        all areas,
        alignment
    )

    return FinalFrameLayout(...)
```

---

# 49. Prologue generation

Conceptually:

```text
generate_prologue(frame):
    if frame.requires_stack_adjust:
        emit_stack_adjust(frame)

    if frame.requires_frame_pointer:
        emit_set_frame_pointer()

    for reg in frame.saved_registers:
        emit_save(reg)

    if frame.has_canary:
        emit_canary_setup()

    if frame.requires_stack_probe:
        emit_stack_probe()
```

Nhưng thứ tự thực tế:

```text
target ABI
```

quyết định.

---

# 50. Epilogue generation

```text
generate_epilogue(frame):
    if frame.has_canary:
        emit_canary_check()

    restore_saved_registers()

    restore_frame_pointer()

    restore_stack()

    return
```

Tất cả đều target-specific.

---

# 51. Final machine verification

Sau frame lowering:

```text
FinalMachineVerifier
```

phải kiểm tra:

### Register

```text
no virtual regs
all physical regs valid
```

### Stack

```text
all offsets assigned
alignment valid
frame size valid
```

### ABI

```text
callee-saved restored
return convention correct
stack alignment correct
shadow space correct
```

### Control flow

```text
every return has valid epilogue
tail call valid
no fallthrough into epilogue incorrectly
```

### Security

```text
canary initialized/checked
required stack probes present
```

### Unwind

```text
unwind state matches actual prologue/epilogue
```

---

# 52. Frame invariants

Đề xuất bộ chính thức:

### ARFRAME-20 — Frame Is Optional

Function không cần frame có thể có zero-size frame.

### ARFRAME-21 — Frame Requirements Are Explicit

Frame chỉ được tạo khi có requirement.

### ARFRAME-22 — Source Locals Are Not Automatically Stack Objects

Compiler có thể giữ local trong register/inline storage.

### ARFRAME-23 — Spill Slots Are Compiler Storage

Spill không phải semantic allocation.

### ARFRAME-24 — Semantic Storage And Spill Storage Are Distinct

Hai loại object không được nhầm lẫn.

### ARFRAME-25 — Final Frame Is Deterministic

Cùng target + Machine IR + policy phải cho layout deterministic.

### ARFRAME-26 — ABI Controls Stack Alignment

Frame phải tuân ABI.

### ARFRAME-27 — Target Controls Frame Representation

Generic compiler không hard-code stack layout của target.

### ARFRAME-28 — Frame Pointer Is Optional

FP chỉ được dùng khi cần hoặc policy yêu cầu.

### ARFRAME-29 — Red Zone Is ABI-Specific

Red zone không phải language semantic.

### ARFRAME-30 — Callee-Saved Registers Must Be Preserved

Register đã được sử dụng phải được save/restore đúng ABI.

### ARFRAME-31 — Caller-Saved Registers Need No Preservation

Compiler không tạo save/restore không cần thiết.

### ARFRAME-32 — Outgoing Argument Storage Is Reusable

Nếu ABI cho phép, các call site có thể dùng chung outgoing area.

### ARFRAME-33 — SRet Storage Is ABI-Defined

Aggregate return storage phải tuân ABI lowering.

### ARFRAME-34 — Dynamic Stack Is Distinct From Fixed Frame

Dynamic allocation không được nhầm với fixed frame objects.

### ARFRAME-35 — Dynamic Stack Cannot Escape Invalidly

Frame lowering không được tạo đường thoát làm dangling stack capability.

### ARFRAME-36 — Prologue Is Machine IR

Prologue phải xuất hiện trước encoding.

### ARFRAME-37 — Epilogue Is Machine IR

Epilogue phải xuất hiện trước encoding.

### ARFRAME-38 — Encoder Does Not Invent Prologue

Instruction encoder chỉ encode instruction đã có.

### ARFRAME-39 — Unwind Describes Actual Machine State

Unwind metadata phải khớp machine code thực tế.

### ARFRAME-40 — Security Features Are Profile-Driven

Canary/probe/shadow-stack không phải semantics mặc định của language.

### ARFRAME-41 — Tail Calls Require ABI Compatibility

Không được tạo tail call trái ABI.

### ARFRAME-42 — Tail Calls May Eliminate Frame

Tail-call lowering có thể bỏ hoàn toàn frame.

### ARFRAME-43 — Multiple Epilogues Are Valid

Compiler không bắt buộc single epilogue.

### ARFRAME-44 — Frame Layout Must Respect Alignment

Mọi object và frame đều đúng alignment.

### ARFRAME-45 — Large Offsets Must Be Legalized

Không được tạo memory operand không encode được.

### ARFRAME-46 — Frame Lowering Must Not Require Re-running Semantic Analysis

Semantic ownership/type checking đã hoàn tất trước backend.

### ARFRAME-47 — Frame Lowering Must Not Depend On Source Syntax

Chỉ Machine IR + ABI/target information.

### ARFRAME-48 — Frame Model Is Execution-Domain Specific

CPU/GPU/WASM có thể có frame model khác nhau.

### ARFRAME-49 — Final Frame Is Machine-Verifiable

Không được emit code nếu frame contract chưa verify.

### ARFRAME-50 — Prologue/Epilogue Optimization Preserves ABI

Shrink wrapping, epilogue duplication, tail calls... không được phá ABI/unwind/security semantics.

---

# 53. Điểm rất quan trọng: Axiom không nên có "stack vs heap" ở compiler backend

Đến đây kiến trúc của Axiom đã thể hiện khá rõ một triết lý:

```text
Source semantics
      ↓
Storage requirement
      ↓
Compiler optimization
      ↓
Register / Stack / Static / Heap / Device
```

Không phải:

```text
struct → stack
Box → heap
Vec → heap
```

một cách cứng nhắc.

Ví dụ:

```text
let x = Box::new(Point { x: 1, y: 2 });
```

về semantic là **owned dynamic storage**.

Nhưng nếu:

- không escape;
- address không observable;
- lifetime đơn giản;

compiler có thể scalarize/eliminate allocation.

Ngược lại:

```text
let p = raw_address(x);
```

làm address trở thành observable contract và optimizer phải giữ storage phù hợp.

Điều này hoàn toàn khớp với memory model Axiom đã đóng băng.

---

# 54. Backend hiện tại đã gần tới machine bytes

Sau COMPILER-011, pipeline hoàn chỉnh trở thành:

```text
Source
 ↓
AST
 ↓
HIR
 ↓
Typed HIR
 ↓
Ownership / Capability
 ↓
MIR
 ↓
MIR Optimization
 ↓
ABI / Layout
 ↓
LIR
 ↓
Legalization
 ↓
Instruction Selection
 ↓
Machine IR
 ↓
Register Allocation
 ↓
Spill / Reload
 ↓
Final Frame Layout
 ↓
Prologue / Epilogue
 ↓
Physical Machine IR
 ↓
Machine Optimization
 ↓
Machine Verification
 ↓
Instruction Encoding
 ↓
Object
 ↓
Linker
 ↓
Executable
```

Điểm còn thiếu trực tiếp ở backend là:

## **COMPILER-012 — Final Machine Verification + Instruction Encoding**

Ở đó chúng ta sẽ chốt cách Axiom **tự encode x86-64/AArch64/RISC-V**, bao gồm:

- instruction descriptors;
- operand encoding;
- x86 ModRM/SIB/REX/VEX/EVEX;
- AArch64 fixed-width encoding;
- RISC-V encoding;
- immediate legalization;
- branch relaxation;
- PC-relative displacement;
- symbol/fixup;
- relocations;
- literal pools;
- alignment/NOP;
- machine-level peephole trước encoding;
- byte-exact verifier;
- và đặc biệt **không cần assembler bên ngoài**.

Đây sẽ là bước cuối cùng trước khi đi vào **OBJECT-002 / self-host bootstrap thực tế**.