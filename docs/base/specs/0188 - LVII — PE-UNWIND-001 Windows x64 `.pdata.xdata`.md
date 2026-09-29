# LVII — PE-UNWIND-001: Windows x64 `.pdata/.xdata`

Đây là bước cần làm **trước khi coi Windows backend là production-capable**. Tôi đã kiểm tra lại tài liệu Windows hiện hành: Windows x64 dùng `RUNTIME_FUNCTION` trong `.pdata` trỏ tới `UNWIND_INFO` trong `.xdata`; unwind code mô tả các thay đổi của prologue đối với `RSP` và nonvolatile registers. Leaf function có thể không cần pdata/xdata. citeturn0search0turn0search9

Đồng thời, Windows x64 đặt các ràng buộc khá chặt lên prologue/epilogue để OS có thể unwind chính xác. citeturn0search2

---

## 1. Mục tiêu

Pipeline mới:

```text id="4qj7m2"
Machine IR
    ↓
Register Allocation
    ↓
Frame Layout
    ↓
Prologue/Epilogue Generation
    ↓
Unwind Analysis
    ↓
Unwind Info
    ↓
Machine Encoder
    ↓
COFF
    ↓
PE Linker
    ↓
.pdata + .xdata
    ↓
hello.exe
```

Điểm quan trọng:

> **Unwind metadata phải được sinh từ cùng một frame/prologue model với code machine.**

Không được generate `.xdata` bằng cách "đoán" từ byte code sau khi encode.

---

# 2. Chia trách nhiệm

### Frame builder

Quyết định:

```text id="h7m2x5"
stack_size
saved_registers
spill_slots
shadow_space
frame_pointer
```

### Prologue generator

Sinh:

```text id="a5p8q1"
push nonvolatile
sub rsp,...
set frame pointer
```

### Unwind builder

Quan sát **semantic prologue operations**:

```text id="g3w9v4"
SAVE_REG
ALLOC_STACK
SET_FRAME
SAVE_XMM
```

và chuyển thành:

```text id="v9s2k6"
UWOP_*
```

---

# 3. Không để unwind builder đọc raw bytes

Sai:

```text
Machine Bytes
   ↓
pattern matching
   ↓
guess unwind
```

Đúng:

```text
FramePlan
   ↓
ProloguePlan
   ├── Machine instructions
   └── Unwind operations
```

Ví dụ:

```text id="j2m8s4"
ProloguePlan {
    instructions[]
    unwind_ops[]
}
```

Hai output này phải được tạo **cùng lúc từ một semantic plan**.

---

# 4. Function classification

Thêm:

```text id="7s3p9a"
FunctionFrameKind =
    Leaf
    Frameless
    StackFrame
    FramePointer
    DynamicFrame
```

MVP:

```text
Leaf
Frameless
StackFrame
```

Chưa cần:

```text
DynamicFrame
```

---

# 5. Leaf function

Ví dụ:

```text id="m5q8x1"
fn answer() -> i32 {
    42
}
```

Machine:

```text id="6v3s8k"
mov eax,42
ret
```

Không:

```text
sub rsp,...
push ...
```

Có thể không cần:

```text
.pdata
.xdata
```

Windows unwinder có thể xử lý leaf function bằng cách mô phỏng return. citeturn0search0turn0search9

Đây rất tốt cho mục tiêu binary nhỏ.

---

# 6. Function gọi function

Ví dụ:

```text id="4p7n2w"
fn foo() -> i32 {
    bar()
}
```

thường cần stack frame/shadow space và do đó phải được mô tả bởi unwind metadata. Microsoft nêu rõ các function allocate stack, gọi function hoặc lưu nonvolatile register phải có prologue được mô tả trong unwind data. citeturn0search1

---

# 7. Windows nonvolatile registers

Ta đã có ABI:

```text id="8h4q7s"
RBX
RBP
RSI
RDI
R12
R13
R14
R15
```

và:

```text id="k3m7p2"
XMM6-XMM15
```

là nonvolatile theo Windows x64 ABI.

Nếu allocator dùng chúng trong function:

```text
save
...
restore
```

thì unwind metadata phải mô tả.

---

# 8. UWOP_PUSH_NONVOL

Ví dụ:

```text id="2f6s9d"
push rbx
```

semantic operation:

```text
SAVE_NONVOL RBX
```

→

```text
UWOP_PUSH_NONVOL
```

Microsoft mô tả `UWOP_PUSH_NONVOL` trong unwind code và yêu cầu thứ tự tương ứng với prologue. citeturn0search0

---

# 9. Stack allocation nhỏ

Ví dụ:

```text id="7q3m8v"
sub rsp, 40h
```

→

```text
UWOP_ALLOC_SMALL
```

Windows unwind format có encoding riêng cho allocation từ 8 đến 128 bytes với `UWOP_ALLOC_SMALL`. citeturn0search0

---

# 10. Stack allocation lớn

Nếu:

```text id="k5x2n9"
stack_size > 128
```

thì dùng:

```text id="w3p7a6"
UWOP_ALLOC_LARGE
```

Có hai encoding forms; một form dùng scaled size và form kia dùng full size. citeturn0search0

---

# 11. Stack probing

Nếu stack allocation vượt một page, Windows yêu cầu probing trước khi giảm `RSP`; tài liệu Microsoft mô tả việc sử dụng `__chkstk` cho allocation lớn. citeturn0search2

Vì vậy:

```text id="e7s4k1"
Frame size <= page
```

→ MVP bình thường.

Còn:

```text id="r2m9x5"
Frame size >= page
```

→

```text
StackProbeLowering
```

sẽ được thêm sau.

**Không được generate `sub rsp, 10000h` rồi coi như xong.**

---

# 12. `__chkstk` không phải compiler magic

Sau này có thể:

```text id="q8v3m5"
extern "system"
fn __chkstk() -> ...
```

hoặc Axiom compiler intrinsic/platform helper.

Nhưng linker không được tự chèn một symbol bí mật.

---

# 13. Frame pointer

Nếu:

```text id="j5n8q2"
RBP
```

được chọn làm frame pointer, unwind info phải mô tả:

```text id="v4s7m1"
FrameRegister
FrameRegisterOffset
```

Microsoft mô tả field này trong `UNWIND_INFO`; frame register là một nonvolatile register và offset được scale theo 16 bytes. citeturn0search0

---

# 14. Nhưng Axiom mặc định không cần RBP

Mục tiêu:

```text id="d6p3w9"
omit frame pointer
```

khi có thể.

Lợi ích:

- thêm một GPR khả dụng
- code nhỏ hơn
- ít instruction
- allocator linh hoạt hơn

Unwind data vẫn xử lý được frameless functions.

---

# 15. `UNWIND_INFO`

Representation:

```text id="z8k4p2"
UnwindInfo {
    version
    flags
    prolog_size
    unwind_code_count
    frame_register
    frame_offset
    unwind_codes[]
}
```

Đây là **semantic representation**, chưa phải bytes.

---

# 16. Version

Đối với Axiom x86-64 MVP:

```text id="1s7m3x"
UnwindVersion = 1
```

Không dùng Unwind V3.

Microsoft hiện mô tả Unwind V3 là cơ chế mới/preview và liên quan đến APX; code không dùng APX nên vẫn nên dùng conventional unwind information. citeturn0search10

Đây là lựa chọn đúng cho Axiom v0.1.

---

# 17. Unwind flags

MVP:

```text id="c9m5q1"
NONE
```

Sau này:

```text
EHANDLER
UHANDLER
CHAININFO
```

chỉ khi Axiom thực sự có exception/unwind handlers.

---

# 18. Axiom hiện tại: panic abort

Ta đã freeze:

```text id="n4x7s2"
panic = abort
```

Do đó function bình thường chưa cần language-specific exception handler.

Đây giúp `.xdata` MVP rất nhỏ.

---

# 19. `RUNTIME_FUNCTION`

`.pdata` chứa:

```text id="h8s3k5"
RUNTIME_FUNCTION {
    BeginAddress
    EndAddress
    UnwindInfoAddress
}
```

Các giá trị là image-relative RVAs.

Microsoft mô tả function table entry dùng Begin RVA, End RVA và RVA tới unwind information. citeturn0search0

---

# 20. Strong types

Tuyệt đối không dùng:

```text
u32 begin
u32 end
u32 unwind
```

khắp code.

Dùng:

```text id="p5k8x3"
Rva
```

cho cả ba.

Ví dụ:

```text id="t7m2q9"
RuntimeFunction {
    begin: Rva
    end: Rva
    unwind_info: Rva
}
```

Điều này tránh nhầm:

```text
FileOffset
RVA
VA
```

---

# 21. `.pdata` layout

```text id="q3v7m8"
.pdata
    RuntimeFunction #0
    RuntimeFunction #1
    RuntimeFunction #2
    ...
```

Mỗi record có fixed size.

Linker sau đó biết RVA của `.xdata`.

---

# 22. `.xdata`

```text id="w5n9s2"
.xdata
    UNWIND_INFO #0
    UNWIND_INFO #1
    ...
```

Mỗi function có thể có unwind record riêng.

Sau này có thể share/chaining.

---

# 23. Chưa cần chained unwind

MVP:

```text id="f8m3q6"
one function
→ one primary UNWIND_INFO
```

Không:

```text
CHAININFO
```

trừ khi compiler bắt đầu cần function fragments hoặc advanced code layout.

---

# 24. Prologue size

`UNWIND_INFO` chứa:

```text id="s7x4k2"
SizeOfProlog
```

và unwind code có offset trong prologue.

Microsoft xác định offset unwind operation theo vị trí trong prologue. citeturn0search0

Do đó prologue finalization phải xảy ra trước khi encode unwind metadata.

---

# 25. Unwind code representation

```text id="k2p8v5"
UnwindOp {
    code_offset
    operation
    info
    extra_data[]
}
```

Operations MVP:

```text id="m7s4q1"
PUSH_NONVOL
ALLOC_SMALL
ALLOC_LARGE
SET_FPREG
SAVE_NONVOL
SAVE_NONVOL_FAR
```

Sau đó:

```text
SAVE_XMM128
SAVE_XMM128_FAR
PUSH_MACHFRAME
```

khi cần.

---

# 26. Không encode unwind code quá sớm

Pipeline:

```text id="h4q9m2"
FramePlan
    ↓
ProloguePlan
    ↓
Machine instructions
    +
UnwindOps
    ↓
Final code layout
    ↓
UnwindEncoder
```

---

# 27. Prologue ordering

Windows unwind format có quy tắc về thứ tự các thao tác trong prologue; ví dụ `UWOP_PUSH_NONVOL` phải tương ứng với push trong prologue và unwind array được lưu theo thứ tự offset giảm dần. citeturn0search0

Do đó Axiom nên giữ:

```text id="x6s3p8"
PrologueOperation {
    semantic_order
    instruction_offset
}
```

rồi `UnwindEncoder` tự đảo/sắp xếp theo format.

Không bắt frontend phải biết thứ tự `.xdata`.

---

# 28. Epilogue

Đây là chỗ rất quan trọng.

Windows **không cần unwind metadata riêng cho mỗi epilogue** nếu epilogue tuân thủ canonical patterns; unwinder nhận diện epilogue bằng cách quét instruction stream. citeturn0search2

Vì vậy:

```text id="b5q8m1"
UnwindInfo
```

chỉ mô tả prologue.

---

# 29. Epilogue generator phải bị giới hạn

Ví dụ frameless:

```text id="g7x2s4"
add rsp, FRAME_SIZE
pop r15
pop r14
ret
```

là dạng hợp lệ.

Microsoft mô tả epilogue không-frame-pointer phải deallocate stack bằng `add RSP, constant`, restore nonvolatile registers rồi return/jump. citeturn0search2

---

# 30. Không cho optimizer tùy tiện chèn instruction vào epilogue

Đây là một invariant mới:

```text id="a9m5q7"
AEPI-20
Windows x64 epilogues are structurally verified.

AEPI-21
No arbitrary instruction may be scheduled into an epilogue.

AEPI-22
Return-value materialization occurs before the epilogue.

AEPI-23
Epilogue instructions obey Windows unwind-recognizable forms.
```

Điều này ảnh hưởng trực tiếp tới Machine Optimizer.

---

# 31. Return value

Sai:

```text id="j6s2p8"
add rsp,40h
mov eax,42
ret
```

nếu `mov` nằm trong vùng mà Windows nhận diện là epilogue.

Đúng:

```text id="k8q3v5"
mov eax,42
add rsp,40h
ret
```

Microsoft nêu rõ trong epilogue không được chèn việc load return value giữa các thao tác epilogue. citeturn0search2

---

# 32. Machine IR cần region markers

Thêm:

```text id="n7x4m2"
MachineRegion =
    Prologue
    Body
    Epilogue
```

Ví dụ:

```text id="q8s5p3"
MachineFunction
 ├── Prologue
 ├── Body
 └── Epilogues[]
```

Optimizer phải tôn trọng region.

---

# 33. Đây là thay đổi quan trọng

Trước đây:

```text id="c5v8m1"
MachineBlock
```

giờ thêm metadata:

```text id="w3q7s2"
MachineBlockKind =
    Normal
    Prologue
    Epilogue
```

Hoặc tốt hơn, function có:

```text id="h9m4x6"
PrologueRange
EpilogueRanges[]
```

---

# 34. Machine verifier

Thêm kiểm tra:

```text id="s2p6k8"
WindowsPrologueVerifier
WindowsEpilogueVerifier
UnwindVerifier
```

Kiểm:

```text
prologue instructions match unwind ops
saved registers are nonvolatile
stack allocation matches metadata
frame register matches metadata
epilogue canonical
return outside epilogue body
```

---

# 35. Large stack

Nếu:

```text id="k6x9q2"
stack_size >= 4096
```

frame lowering chuyển thành:

```text
load allocation size
call __chkstk
sub rsp,rax
```

hoặc equivalent ABI-compliant sequence.

Microsoft yêu cầu stack probing cho allocation từ một page trở lên. citeturn0search2

Đồng thời unwind metadata phải mô tả phần stack allocation đúng cách.

---

# 36. XMM saves

Windows x64 có nonvolatile:

```text id="p4s8m1"
XMM6-XMM15
```

Nếu register allocator spill/save chúng:

```text
SAVE_XMM128
```

Microsoft định nghĩa `UWOP_SAVE_XMM128` và `UWOP_SAVE_XMM128_FAR` cho trường hợp này. citeturn0search0

MVP có thể chưa cần nếu floating-point register allocation tránh nonvolatile XMM khi có thể.

Nhưng model phải tồn tại từ đầu.

---

# 37. Unwind builder repository

```text id="c7m2x9"
compiler/backend/x86_64/unwind/
├── model.ax
├── prologue.ax
├── epilogue.ax
├── ops.ax
├── encode.ax
├── pdata.ax
├── xdata.ax
├── verifier.ax
└── tests/
```

---

# 38. PE linker integration

Pipeline:

```text id="f8q3m6"
COFF .obj
   ↓
read .pdata/.xdata contributions
   ↓
merge
   ↓
assign final RVA
   ↓
relocate RuntimeFunction
   ↓
write PE .pdata/.xdata
```

---

# 39. Không regenerate unwind ở linker

Compiler đã biết:

```text
function
prologue
frame
unwind ops
```

nên COFF object phải chứa `.pdata/.xdata` contributions.

Linker chỉ:

```text
merge
relocate
layout
```

Không reverse-engineer compiler-generated code.

---

# 40. COFF section contributions

Object:

```text id="x4m8p2"
foo.obj
 ├── .text
 ├── .pdata
 └── .xdata
```

Linker:

```text id="w6q3s8"
.text
.pdata
.xdata
```

từ tất cả object.

---

# 41. Function range relocation

Giả sử object:

```text id="b5n7q1"
foo:
.text offset = 0x100
size = 0x50
```

`.pdata`:

```text id="r3m8x4"
Begin = 0x100
End   = 0x150
```

Sau section layout:

```text id="h7s2k9"
.text RVA = 0x1000
```

linker chuyển:

```text id="p8x4m6"
Begin = 0x1100
End   = 0x1150
```

và đó là RVA trong final image.

---

# 42. `.xdata` pointer

`RUNTIME_FUNCTION.UnwindData`:

```text id="z4m8q2"
RVA(.xdata record)
```

Linker patch sau khi layout `.xdata`.

---

# 43. Ordering `.pdata`

Function table nên deterministic:

```text id="v2x7m4"
sort by BeginAddress
```

Điều này cũng phù hợp với việc runtime tìm function table theo instruction address.

---

# 44. Acceptance test 1 — leaf

```axiom id="e5s8k2"
fn answer() -> i32 {
    42
}
```

Expected:

```text
.text
    mov eax,42
    ret

.pdata:
    absent or no entry for answer
```

---

# 45. Acceptance test 2 — call

```axiom id="q7m3x9"
fn answer() -> i32 {
    42
}

fn main() -> i32 {
    answer()
}
```

`main` cần frame theo Windows call ABI nếu generated code sử dụng stack/shadow space.

Expected:

```text
main
    prologue
    call answer
    epilogue
    ret
```

và:

```text
.pdata
    main RuntimeFunction
```

---

# 46. Acceptance test 3 — saved register

Tạo function đủ register pressure để allocator dùng:

```text id="m8x2q5"
RBX
```

Expected:

```text
push rbx
...
pop rbx
ret
```

và unwind:

```text id="s4p7n1"
UWOP_PUSH_NONVOL(RBX)
```

---

# 47. Acceptance test 4 — stack allocation

Function local:

```axiom id="w6q3m8"
var buffer: Array<u8, 64>
```

Expected:

```text id="r8x2p4"
sub rsp,...
...
add rsp,...
ret
```

và:

```text id="y5m7q3"
UWOP_ALLOC_SMALL
```

nếu kích thước phù hợp.

---

# 48. Acceptance test 5 — actual unwind

Đây mới là test quan trọng nhất.

Tạo nested functions:

```text id="p9x4m7"
A → B → C
```

sau đó ép một Windows exception/debug unwind ở giữa `B`.

Kiểm tra stack walk:

```text id="j3m8q2"
C
B
A
```

chính xác.

Không cần đưa C++ exception vào Axiom.

Chỉ cần Windows stack/unwind machinery nhận diện function frames đúng.

---

# 49. Acceptance test 6 — debugger

Sau khi CodeView chưa có, vẫn kiểm tra:

```text id="s7q2x5"
RtlLookupFunctionEntry
```

hoặc tương đương runtime inspection.

Mục tiêu:

```text
RIP in function
    ↓
RUNTIME_FUNCTION found
    ↓
UNWIND_INFO found
```

---

# 50. Debug information tách riêng

Không trộn:

```text id="m4x8q2"
.pdata/.xdata
```

với:

```text id="pdb/CodeView"
```

Unwind là **runtime correctness**.

Debug info là **developer tooling**.

Hai pipeline độc lập.

---

# 51. `panic = abort`

Với profile hiện tại:

```text id="f8q5m2"
panic()
    ↓
abort / terminate
```

không cần Axiom exception handler.

Nhưng Windows unwind vẫn cần cho:

- debugger
- stack walking
- OS exception machinery
- future panic/unwind profile.

---

# 52. Future `panic = unwind`

Sau này:

```text id="s3m7x9"
panic = unwind
```

sẽ thêm:

```text
UNW_FLAG_EHANDLER
```

và language-specific handler data.

Đó là một feature riêng:

```text
PANIC-UNWIND-001
```

Không làm chung với PE-UNWIND-001.

---

# 53. Unwind metadata không phải "runtime"

`.pdata/.xdata` là image metadata.

Không cần:

```text
Axiom runtime initialization
```

để Windows sử dụng chúng.

Đây phù hợp với mục tiêu runtime-free.

---

# 54. Binary size

Với leaf functions:

```text
no pdata
no xdata
```

nếu hợp lệ.

Do đó:

```text id="j8q3m5"
fn add(a:i32,b:i32)->i32 {
    a+b
}
```

có thể cực nhỏ:

```text
.text
    ...
```

mà không kéo theo runtime metadata không cần thiết.

---

# 55. Nhưng đừng tối ưu `.pdata` quá sớm

MVP ưu tiên:

```text id="x6m2q9"
correctness > smallest metadata
```

Sau khi verifier ổn định mới làm:

```text
unwind record deduplication
chained info
function folding
```

---

# 56. Invariants mới

```text id="AUNW-20"
Every non-leaf Windows x64 function requiring unwind support has valid unwind metadata.

AUNW-21
Leaf functions may omit unwind metadata.

AUNW-22
Unwind metadata is derived from the same FramePlan as machine code.

AUNW-23
Unwind offsets refer to actual prologue instruction boundaries.

AUNW-24
RUNTIME_FUNCTION addresses are image-relative RVAs.

AUNW-25
UNWIND_INFO version is explicit.

AUNW-26
Unwind operations describe only reversible prologue effects.

AUNW-27
Nonvolatile register saves are represented accurately.

AUNW-28
Stack allocation is represented accurately.

AUNW-29
Frame-register information is represented accurately.

AUNW-30
Windows x64 epilogues obey canonical unwind-recognizable forms.

AUNW-31
Machine optimization cannot invalidate unwind metadata.

AUNW-32
.pdata ordering is deterministic.

AUNW-33
.xdata encoding is deterministic.

AUNW-34
Linker relocates unwind RVAs after final section layout.

AUNW-35
Unwind metadata does not require the Axiom runtime.

AUNW-36
Unwind V3/APX is not part of v0.1.

AUNW-37
Stack probing is mandatory for large stack allocations requiring it.

AUNW-38
Unwind correctness is independently testable.
```

---

# 57. Một thay đổi quan trọng trong backend architecture

Ta đã có:

```text
Frame Layout
Prologue/Epilogue
```

nhưng giờ chính thức nâng chúng thành:

```text id="n5q8x2"
FramePlan
   │
   ├── StackLayout
   ├── SavedRegisters
   ├── ProloguePlan
   ├── EpiloguePlan[]
   └── UnwindPlan
```

Đây là abstraction tốt hơn rất nhiều so với việc:

```text
generate prologue
...
sau đó đoán unwind
```

---

# 58. Pipeline Windows hoàn chỉnh hơn

```text id="u7m3q9"
LIR
 ↓
Instruction Selection
 ↓
Machine IR
 ↓
Register Allocation
 ↓
Spill/Reload
 ↓
FramePlan
 ↓
Prologue/EpiloguePlan
 ↓
UnwindPlan
 ↓
Machine Verification
 ↓
Encoder
 ↓
COFF
 ↓
PE Linker
 ↓
.pdata/.xdata
 ↓
PE32+
```

Đây hiện là pipeline **đúng về mặt kiến trúc**, không chỉ đủ để tạo một demo `.exe`.

---

# 59. Milestone tiếp theo: `PE-UNWIND-002`

Sau phần này, ta cần làm **CodeView/PDB debugging** nhưng không nên làm ngay.

Trước đó cần hoàn thiện một thứ quan trọng hơn:

## `WIN-ABI-002 — Full Windows x64 ABI Lowering`

Bao gồm:

- integer arguments
- floating arguments
- aggregate arguments
- return values
- shadow space
- stack arguments
- variadic functions
- caller/callee saved
- XMM6–XMM15
- stack alignment
- `extern "system"`
- `extern "C"`
- function pointer ABI
- indirect calls

Bởi vì hiện tại ta mới có **khung ABI**, chưa có toàn bộ ABI lowering.

Sau đó:

```text
WIN-ABI-002
      ↓
PE-UNWIND-002
      ↓
CODEVIEW-001
      ↓
PDB-001
      ↓
ELF-001
```

Đây sẽ là hướng tiếp theo, và **không cần quay lại thiết kế language core**: core đã freeze; từ đây trọng tâm là làm cho Axiom thật sự trở thành một compiler/native toolchain hoàn chỉnh.