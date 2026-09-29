# L — ISel-001: X86-64 Instruction Selection

Ta đi tiếp từ **Register Allocation + Frame Layout** sang Instruction Selection.

Mục tiêu:

```text
LIR
 ↓
Legalization
 ↓
Instruction Selection
 ↓
x86 Machine IR
 ↓
Register Allocation
 ↓
Frame
 ↓
Encoder
```

Nhưng có một chỉnh sửa kiến trúc quan trọng: **một phần register allocation phải xảy ra sau ISel**, vì x86 có rất nhiều instruction constraint. Vì vậy pipeline thực tế nên là:

```text
Verified MIR
    ↓
Semantic Optimization
    ↓
LIR
    ↓
LIR Legalization
    ↓
Instruction Selection
    ↓
Machine IR (virtual registers)
    ↓
ABI Lowering
    ↓
Register Allocation
    ↓
Spill/Reload
    ↓
Frame Layout
    ↓
Prologue/Epilogue
    ↓
Machine Optimization
    ↓
Encoder
```

---

# 1. Vai trò của Instruction Selection

Ví dụ LIR:

```text
%3 = ADD I32 %1, %2
```

Không được trực tiếp encode.

ISel quyết định:

```text
ADD32rr
```

hoặc một form khác.

Ví dụ:

```text
%3 = ADD %1, 42
```

có thể chọn:

```text
ADD32ri
```

thay vì:

```text
MOV temp, 42
ADD32rr
```

Đây là nơi Axiom bắt đầu tận dụng đặc tính của x86.

---

# 2. Không để ISel phụ thuộc physical register

Input:

```text
%a:GPR32
%b:GPR32
```

Output:

```text
%v3:GPR32 = ADD32rr %a, %b
```

Chưa được:

```text
EAX = ADD EDI, ESI
```

Register allocation mới quyết định physical register.

---

# 3. Instruction Selection architecture

```text
compiler/backend/x86_64/selector/
├── selector.ax
├── legalize.ax
├── integer.ax
├── float.ax
├── memory.ax
├── control.ax
├── call.ax
├── aggregate.ax
├── compare.ax
├── overflow.ax
├── patterns.ax
└── tests/
```

---

# 4. Selection pattern

Thay vì một đống `if`, nên có pattern model:

```text
Pattern {
    match
    constraints
    result
    cost
}
```

Ví dụ:

```text
ADD(x, IMM8)
    →
ADD32ri
```

cost:

```text
1 instruction
```

Trong khi:

```text
MOV temp, IMM
ADD x, temp
```

cost:

```text
2 instructions
```

---

# 5. Nhưng không biến ISel thành optimizer

ISel được phép chọn form tốt hơn.

Nhưng không nên làm:

```text
ADD
SUB
MUL
```

→ chạy cả global optimizer.

Semantic optimization đã xảy ra ở MIR.

ISel chủ yếu:

> **legalize + select target instruction.**

---

# 6. Integer constants

Ví dụ:

```text
%v = CONST i32 42
```

→

```text
MOV32ri %v, 42
```

Không tạo memory.

---

# 7. 64-bit constants

x86 có giới hạn encoding.

Ví dụ:

```text
MOV RAX, 123
```

nếu immediate phù hợp có thể dùng form ngắn.

Nếu full 64-bit immediate:

```text
MOVABS RAX, imm64
```

hoặc compiler có thể tạo constant pool tùy context.

ISel cần:

```text
ConstantMaterializer
```

---

# 8. `ADD`

LIR:

```text
%3 = ADD I32 %1, %2
```

→

```text
ADD32rr %1, %2
```

Nếu `%1` được dùng lại:

```text
%3 = ADD %1,%2
```

không thể đơn giản mutate `%1` nếu `%1` còn live.

ISel có thể tạo:

```text
COPY %1 → %3
ADD %3,%2
```

Sau đó coalescer có thể loại COPY.

---

# 9. Three-address → x86 two-address

LIR:

```text
%3 = ADD %1, %2
```

x86:

```text
ADD dst, src
```

không phải:

```text
ADD dst, src1, src2
```

Do đó selector phải materialize:

```text
%3 = COPY %1
%3 = ADD %3, %2
```

Đây là một trong những lý do Machine IR cần virtual register.

---

# 10. `SUB`

Tương tự:

```text
%3 = SUB %1,%2
```

→

```text
COPY %1 → %3
SUB %3,%2
```

---

# 11. `AND/OR/XOR`

Tương tự:

```text
COPY lhs → result
AND result,rhs
```

Nhưng có một optimization đặc biệt:

```text
x ^ x
```

→ zero.

Tuy nhiên transformation này nên thuộc optimizer hơn là ISel.

---

# 12. Immediate arithmetic

```text
x + 42
```

→

```text
ADD32ri x, 42
```

nếu encoding hợp lệ.

Không:

```text
MOV temp,42
ADD x,temp
```

---

# 13. `LEA`

LIR:

```text
%3 = ADD %base, %index*4
```

có thể select:

```text
LEA %3, [%base + %index*4]
```

Nhưng chỉ nếu semantic operation thực sự tương ứng.

`LEA` không tạo flags.

Điều này rất quan trọng.

Nếu LIR:

```text
ADD
```

mà FLAGS sau đó được sử dụng:

```text
ADD
JO overflow
```

thì `LEA` không được dùng thay thế.

---

# 14. Overflow flags

Ví dụ Axiom:

```text
a + b
```

là checked arithmetic.

LIR:

```text
%r = ADD_CHECKED %a,%b
```

Selection:

```text
%r = COPY %a
ADD %r,%b
JO overflow_block
```

CFG:

```text
bb0
 ├── normal
 └── overflow
```

---

# 15. Wrapping arithmetic

Axiom:

```text
a +% b
```

LIR:

```text
ADD_WRAP
```

→

```text
ADD
```

Không cần overflow branch.

Đây là một trường hợp mà semantics trực tiếp map rất đẹp vào x86.

---

# 16. Saturating arithmetic

```text
a +| b
```

Không có một generic x86 integer instruction đơn giản cho mọi width.

ISel có thể tạo sequence.

Ví dụ conceptual:

```text
ADD
JO saturation_path
```

hoặc dùng SIMD instructions nếu vectorized.

Điều quan trọng:

```text
ADD_SAT
```

không bị hạ thành:

```text
ADD
```

một cách mất semantics.

---

# 17. Division

Unsigned:

```text
DIV
```

Signed:

```text
IDIV
```

Đây là fixed-register instruction.

Ví dụ:

```text
i64 a / b
```

cần:

```text
RDX:RAX / divisor
```

ISel phải phát sinh constraints:

```text
input dividend → RAX
high part → RDX
divisor → operand
result quotient → RAX
remainder → RDX
```

Không để encoder giải quyết.

---

# 18. Multiplication

`IMUL` có nhiều form:

```text
IMUL r,r
IMUL r,r,imm
```

Ví dụ:

```text
x * 10
```

có thể:

```text
IMUL r, r, 10
```

thay vì tạo constant register.

---

# 19. Shift

LIR:

```text
x << n
```

Có hai trường hợp.

### Constant count

```text
SHL r, imm8
```

### Variable count

x86 yêu cầu count ở:

```text
CL
```

nên phải tạo constraint:

```text
n → ECX
```

đây lại là một fixed-register problem.

---

# 20. Compare

LIR:

```text
CMP %a, %b
```

→

```text
CMP %a,%b
```

nhưng x86 `CMP` chỉ tạo FLAGS.

Nếu kết quả comparison được dùng như bool:

```text
x = a < b
```

có thể:

```text
CMP a,b
SETL result
```

---

# 21. Branch

LIR:

```text
BRANCH cond, bb_true, bb_false
```

x86:

```text
Jcc bb_true
JMP bb_false
```

Ví dụ:

```text
JG .Ltrue
JMP .Lfalse
```

---

# 22. Branch inversion

Nếu layout block:

```text
current
 → false
 → true
```

thì có thể chọn:

```text
Jcc false
JMP true
```

hoặc đảo condition.

Đây là machine-level CFG optimization.

Có thể đặt thành:

```text
MachineBlockLayout
```

sau ISel.

---

# 23. `TEST`

Một optimization rất quan trọng:

```text
if x == 0
```

có thể:

```text
TEST x,x
JE zero
```

thay vì:

```text
CMP x,0
JE zero
```

Nhưng transformation này nên được ghi rõ trong target pattern.

---

# 24. Memory Load

LIR:

```text
%v = LOAD [addr], I32
```

→

```text
MOV32rm %v,[addr]
```

Nếu load volatile:

```text
MOV32rm_VOLATILE
```

hoặc metadata tương đương.

Không được optimizer sau đó gộp/xóa volatile load.

---

# 25. Store

```text
STORE [addr], %v
```

→

```text
MOV32mr [addr],%v
```

---

# 26. Address calculation

LIR:

```text
%addr = ADDRESS(base + index*8 + 16)
```

có thể không cần `LEA` nếu address chỉ được dùng trong memory operand.

Ví dụ:

```text
LOAD [%base + %index*8 + 16]
```

trực tiếp:

```text
MOV RAX,[base + index*8 + 16]
```

Không tạo:

```text
LEA temp,...
MOV RAX,[temp]
```

Đây là một optimization rất quan trọng cho binary size/performance.

---

# 27. Pointer arithmetic

Axiom pointer/view semantics đã được kiểm chứng trước LIR.

Tại Machine IR:

```text
address calculation
```

là machine operation.

Ví dụ:

```text
view[i]
```

sau bounds verification có thể thành:

```text
base + i * sizeof(T)
```

và memory operand trực tiếp.

---

# 28. Bounds check

MIR:

```text
BOUNDS_CHECK index,len
LOAD
```

Nếu optimizer chưa chứng minh:

```text
CMP index,len
JAE panic
```

Nếu đã proven:

```text
LOAD
```

Không nên để x86 selector tự quyết định bỏ check.

---

# 29. Null check

Axiom safe reference/view không có null.

Raw pointer trong unsafe có thể null.

Nếu một operation có semantic null requirement, LIR phải biểu diễn rõ.

Không tự động assume:

```text
pointer != 0
```

chỉ vì x86 cho phép dereference.

---

# 30. Function call

LIR:

```text
CALL foo(args)
```

ISel trước ABI lowering tạo:

```text
CALL symbol(foo)
```

ABI pass sau đó quyết định:

```text
arg0 → RCX
arg1 → RDX
...
```

Tách hai bước.

---

# 31. Return

LIR:

```text
RETURN %v
```

ABI lowering:

```text
%v → RAX
```

Machine:

```text
RET
```

---

# 32. Tail call

Không đưa vào MVP ngay.

Nhưng Machine IR nên có:

```text
TAILCALL
```

để kiến trúc không khóa tương lai.

Sau này:

```text
return foo(x)
```

có thể biến thành jump/tailcall nếu ABI/frame cho phép.

---

# 33. Floating-point

`f32/f64`:

```text
ADDSS
ADDSD
SUBSS
SUBSD
MULSS
MULSD
DIVSS
DIVSD
```

v0.1:

```text
f32 → XMM
f64 → XMM
```

Machine IR:

```text
ADDSS %xmm0,%xmm1
```

hoặc virtual XMM registers trước allocation.

---

# 34. Float comparison

x86 có semantics flags khác integer.

Do đó không được dùng integer `CMP` abstraction một cách mù quáng.

Tạo target pattern:

```text
FCMP
```

→ appropriate x86 instruction sequence.

Đặc biệt phải xử lý:

```text
NaN
ordered
unordered
```

đúng theo Axiom floating-point semantics.

---

# 35. Floating-point semantics phải chốt

Axiom không được để backend tùy ý chọn:

```text
fast-math
```

nếu language semantics chưa cho phép.

v0.1:

```text
strict FP semantics
```

Optimizer chỉ reassociate/reduce operations nếu được semantic rules cho phép.

Sau này có thể thêm:

```text
@fast_math
```

hoặc compiler profile.

---

# 36. Cast

Integer:

```text
i32 → i64
```

→ sign extension:

```text
MOVSXD
```

Unsigned:

```text
u32 → u64
```

thường có zero-extension qua 32-bit register.

Ví dụ:

```text
MOV EAX, ECX
```

đã zero-extend lên RAX theo x86-64 semantics.

Selector nên tận dụng điều này.

---

# 37. Truncation

```text
i64 → i32
```

có thể:

```text
EAX
```

vì lower 32 bits được chọn.

Không cần instruction nếu value đã ở register phù hợp.

---

# 38. Bit cast

```text
bit_cast<f32,i32>
```

có thể:

```text
MOVD
```

hoặc register move tương ứng.

Đây khác:

```text
as
```

vì `as` có semantic conversion.

---

# 39. `view`

Ở LIR:

```text
view<T>
```

thường đã bị erase thành:

```text
pointer + length
```

hoặc proof-only nếu length không cần.

Machine backend không còn biết ownership.

Đây là đúng với nguyên tắc:

> compiler semantics trước, machine representation sau.

---

# 40. `dyn Trait`

LIR:

```text
DYNAMIC_CALL
```

được hạ thành:

```text
data_ptr
dispatch_ptr
```

rồi:

```text
load function pointer
indirect CALL
```

Machine:

```text
MOV RAX,[dispatch+slot]
CALL RAX
```

ABI pass vẫn xử lý arguments.

---

# 41. Intrinsic

Ví dụ:

```text
black_box(x)
```

có thể lower thành compiler barrier.

Không phải:

```text
CALL runtime_black_box
```

trừ khi target implementation yêu cầu.

---

# 42. Atomic

Ví dụ:

```text
atomic_load
```

không được hạ thành normal:

```text
MOV
```

nếu semantic atomicity yêu cầu instruction/sequence khác.

Windows/x86 backend sẽ tận dụng:

```text
LOCK
XCHG
CMPXCHG
XADD
```

theo atomic operation.

Phần này sẽ có target lowering riêng.

---

# 43. Volatile

Volatile load/store:

```text
VOLATILE_LOAD
VOLATILE_STORE
```

phải giữ đến machine instruction.

Không được:

```text
eliminate
merge
reorder
```

trái với semantics.

---

# 44. Instruction Selection cost

Pattern:

```text
Pattern {
    match
    instruction_sequence
    constraints
    cost
}
```

Cost không chỉ là instruction count.

Có thể:

```text
cost {
    code_size
    latency
    throughput
    register_pressure
}
```

MVP:

```text
primary = instruction_count
secondary = code_size
```

Sau này CPU model mới dùng latency/throughput.

---

# 45. CPU model

Không hard-code Skylake/Zen/etc. vào selector.

Target:

```text
CPUModel {
    name
    features
    instruction_costs
}
```

MVP:

```text
generic_x86_64
```

Sau này:

```text
zen4
skylake
haswell
...
```

---

# 46. Legalization

Một LIR operation có thể không tồn tại trực tiếp trên x86.

Ví dụ:

```text
I128_ADD
```

Nếu chưa hỗ trợ native:

```text
legalize
→ pair of I64
```

Hoặc:

```text
CALL intrinsic helper
```

Nhưng v0.1 chưa cần `i128/u128`, nên chưa phải ưu tiên.

---

# 47. Legalization invariant

```text id="isj6l0"
AISEL-20
Every LIR operation is either directly selectable or explicitly legalized.

AISEL-21
Legalization preserves LIR semantics.

AISEL-22
Instruction selection never changes ownership semantics.

AISEL-23
Instruction selection preserves arithmetic overflow semantics.

AISEL-24
Instruction selection preserves atomic ordering.

AISEL-25
Instruction selection preserves volatile semantics.

AISEL-26
Instruction selection preserves floating-point semantics.

AISEL-27
Instruction selection produces only target-legal Machine IR.

AISEL-28
Instruction selection may exploit target-specific instruction forms.

AISEL-29
Instruction selection does not require physical registers.

AISEL-30
Instruction selection is deterministic.

AISEL-31
Fixed-register constraints are represented explicitly.

AISEL-32
Instruction selection does not depend on assembler availability.

AISEL-33
Instruction selection may reduce redundant copies through target-aware patterns.

AISEL-34
Machine instruction cost is explicit.

AISEL-35
Target feature requirements are explicit.
```

---

# 48. Ví dụ hoàn chỉnh

Source:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Typed MIR:

```text
%r = ADD_CHECKED %a,%b
RETURN %r
```

LIR:

```text
%r = ADD_CHECKED I32 %a,%b
RETURN %r
```

ISel:

```text
%r = COPY %a
ADD32rr %r,%b
JO overflow
RETURN %r
```

ABI Windows:

```text
a → ECX
b → EDX
r → EAX
```

Machine virtual:

```text
%r = COPY %a
ADD32rr %r,%b
JO overflow
```

Register allocation:

```text
%a → ECX
%b → EDX
%r → EAX
```

Frame:

```text
no frame
```

Machine:

```text
MOV EAX, ECX
ADD EAX, EDX
JO .overflow
RET
```

Đây là backend pipeline hoàn chỉnh từ semantics đến machine instruction.

---

# 49. Nhưng optimizer có thể làm tốt hơn

Nếu compiler chứng minh:

```text
a,b ∈ safe range
```

và overflow impossible:

```text
ADD_CHECKED
```

có thể được hạ trực tiếp:

```text
ADD EAX, EDX
```

không `JO`.

Nếu function chỉ:

```axiom
fn add(a: i32,b:i32)->i32
```

thì overflow **không** tự nhiên biến mất.

Đây là điểm quan trọng: Axiom không hy sinh semantics để có benchmark đẹp.

---

# 50. ISel output acceptance tests

Phải có golden tests:

```text
tests/backend/x86_64/isel/
├── add.ax
├── add_checked.ax
├── add_wrap.ax
├── sub.ax
├── mul.ax
├── div.ax
├── shift_const.ax
├── shift_var.ax
├── compare.ax
├── branch.ax
├── load.ax
├── store.ax
├── float.ax
├── call.ax
├── return.ax
└── cast.ax
```

Mỗi test có:

```text
source
expected LIR
expected Machine IR
```

Chưa cần kiểm byte encoding ở layer này.

---

# LI — ENC-001: X86-64 Machine Encoder

Bây giờ mới xuống **byte-level**.

```text
Machine IR
    ↓
Instruction Form
    ↓
Prefix
    ↓
REX
    ↓
Opcode
    ↓
ModRM
    ↓
SIB
    ↓
Displacement
    ↓
Immediate
    ↓
Bytes
```

## 51. Encoder data model

```text
Encoder {
    encode(instr)
}
```

Các thành phần:

```text
X86Encoding {
    prefixes
    rex
    opcode
    modrm
    sib
    displacement
    immediate
}
```

---

# 52. Encoding forms

Không hard-code encoder bằng hàng nghìn `switch`.

Nên có:

```text
EncodingForm {
    opcode_bytes
    operand_encoding[]
    rex_policy
    modrm_policy
    immediate_policy
    displacement_policy
}
```

Ví dụ conceptual:

```text
ADD32rr
    opcode = 01 /r
    dst = ModRM.reg
    src = ModRM.rm
```

---

# 53. Register encoding

Mỗi register có:

```text
RegisterEncoding {
    code: 0..15
    requires_rex
}
```

Ví dụ:

```text
RAX = 0
RCX = 1
...
R8  = 0 + REX.B
```

---

# 54. REX generation

Encoder tự quyết định:

```text
REX.W
REX.R
REX.X
REX.B
```

Không để Machine IR ghi:

```text
REX.W = true
```

Machine IR chỉ nói:

```text
RAX
R8
```

Encoder biết cách biểu diễn chúng.

---

# 55. ModRM

Ví dụ:

```text
MOV EAX, ECX
```

encoder tạo:

```text
opcode
+
ModRM
```

Machine IR không chứa byte.

---

# 56. SIB

Ví dụ:

```text
MOV EAX,[RAX + RCX*4 + 8]
```

Encoder tự tạo:

```text
ModRM
SIB
disp8
```

---

# 57. Immediate

Encoder chọn encoding phù hợp.

Ví dụ:

```text
MOV EAX,42
```

→ immediate 32-bit.

```text
ADD EAX,1
```

→ có thể sử dụng compact immediate form.

---

# 58. Relocation

Encoder gặp:

```text
CALL foo
```

không biết final address.

Emit:

```text
E8 00 00 00 00
```

và:

```text
Relocation {
    offset
    type
    symbol = foo
}
```

COFF writer xử lý relocation.

---

# 59. Encoder không link

Không được:

```text
encoder → resolve foo
```

Encoder chỉ:

```text
machine instruction
→ bytes + relocation
```

---

# 60. Encoder round-trip

Đây là test cực kỳ quan trọng:

```text
MachineInstr
    ↓ encode
bytes
    ↓ decode
MachineInstr'
```

và:

```text
MachineInstr ≡ MachineInstr'
```

Không nhất thiết giữ nguyên textual form, nhưng semantic instruction phải tương đương.

---

# 61. Encoder milestone

```text
ENC-001 MOV reg,reg
ENC-002 MOV reg,imm
ENC-003 MOV load/store
ENC-004 ALU
ENC-005 shifts
ENC-006 CMP/TEST
ENC-007 branches
ENC-008 CALL/RET
ENC-009 LEA
ENC-010 fixed-register instructions
ENC-011 relocations
ENC-012 full encoder verifier
```

---

# 62. Sau encoder

Chuỗi implementation bây giờ là:

```text
L   Instruction Selection       ← đang hoàn thành
LI  x86 Encoder                 ← tiếp theo
LII COFF Object Writer
LIII PE64 Linker
LIV Windows Startup
LV  Native .EXE
```

Và **LII–LIV** mới là phần biến machine code thành một chương trình Windows thực sự.

Điểm đáng chú ý là từ đây compiler đã gần chạm “kim loại”: sau `LI`, Axiom không còn cần LLVM IR, LLVM codegen hay assembler để biến instruction thành bytes. Bước kế tiếp là **COFF-001**, nơi ta thiết kế object writer để xuất `.obj` PE/COFF trực tiếp.