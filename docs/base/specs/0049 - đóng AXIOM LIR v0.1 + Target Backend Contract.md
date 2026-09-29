Tiếp tục từ baseline đã đóng. Theo tôi, bước tiếp theo nên **đóng AXIOM LIR v0.1 + Target Backend Contract**. Đây là lớp rất quan trọng: nếu thiết kế sai, Axiom sẽ biến thành một “LLVM thứ hai” rất lớn; nếu quá thấp, frontend lại bị khóa vào x86/ARM.

## 1. Kiến trúc nên chốt

```text
Source
  ↓
AST
  ↓
HIR
  ↓
Typed HIR
  ↓
MIR
  │
  ├── Ownership
  ├── Capability / Region
  ├── Effect
  ├── Concurrency
  └── Async
  ↓
VERIFIED MIR
  ↓
Semantic Optimization
  ↓
ABI MIR
  ↓
AXIOM LIR          ← lớp chúng ta đang thiết kế
  ↓
Target Lowering
  ↓
Machine IR
  ↓
Register Allocation
  ↓
Instruction Selection
  ↓
Scheduling
  ↓
Machine Encoder
  ↓
Object Writer
  ↓
ELF / PE / Mach-O / WASM
```

Điểm cực kỳ quan trọng:

> **MIR là nơi chứa semantics. LIR không được trở thành nguồn định nghĩa semantics thứ hai.**

LIR chỉ là biểu diễn thấp hơn của một chương trình đã được xác minh.

---

# 2. Không nên xây LIR quá lớn

Tôi đề xuất Axiom chỉ có **3 tầng code representation**:

```text
MIR
 │
 │ semantic → ABI lowering
 ▼
LIR
 │
 │ target lowering
 ▼
Machine IR
```

Không cần:

```text
MIR
 ↓
HIR-LIR
 ↓
Generic-LIR
 ↓
Universal-LIR
 ↓
Target-LIR
 ↓
Pre-Machine-LIR
 ↓
Machine-LIR
```

Đó chính là con đường dẫn đến một compiler framework khổng lồ.

### Axiom LIR chỉ cần 3 nhóm

| Nhóm | Mục đích |
|---|---|
| LIR Core | primitive machine-independent |
| LIR Intrinsic | thao tác đặc biệt nhưng vẫn target-neutral |
| Target Lowering | biến thành Machine IR |

---

# 3. LIR Core

Tôi đề xuất instruction set ban đầu khoảng **40–60 semantic operations**, không phải hàng trăm.

## Integer

```text
IADD
ISUB
IMUL

IDIV
IDIV_UNSIGNED
IREM
IREM_UNSIGNED

IAND
IOR
IXOR
INOT

SHL
SHR
SHR_UNSIGNED

NEG
```

Nhưng có một nguyên tắc rất quan trọng:

### Không có overflow ambiguity

Ví dụ MIR:

```text
INTEGER_ADD_CHECKED
INTEGER_ADD_WRAP
INTEGER_ADD_SAT
```

xuống LIR phải vẫn giữ semantics:

```text
IADD.CHECKED
IADD.WRAP
IADD.SAT
```

hoặc canonicalize thành:

```text
IADD
  + overflow_mode
```

Tôi nghiêng về dạng thứ hai trong IR nội bộ:

```text
IADD {
    lhs
    rhs
    mode = WRAP
}
```

Compiler có thể tối ưu:

```text
WRAP → machine ADD
CHECKED → ADD + overflow branch
SAT → target-specific sequence
```

---

# 4. Không đưa CPU flags vào LIR

Đây là một quyết định quan trọng.

Không nên có:

```text
ADD → EFLAGS
CMP → FLAGS
JCC FLAGS
```

vì đó là x86 thinking.

Thay vào đó:

```text
CMP_EQ
CMP_NE
CMP_LT
CMP_LE
CMP_GT
CMP_GE
```

trả về:

```text
bool
```

Ví dụ:

```text
%3 = CMP_LT %a, %b
BR %3, block_true, block_false
```

ARM64, x86-64, RISC-V đều có thể tối ưu nó xuống instruction flags riêng.

### Lợi ích

Frontend không biết:

- EFLAGS
- NZCV
- condition codes
- register flags

Backend tự quyết định.

---

# 5. LIR register model

LIR dùng **virtual registers**.

Ví dụ:

```text
%0 : i64
%1 : i64
%2 : i64

%2 = IADD %0, %1
```

Không có:

```text
RAX
RBX
X0
X1
A0
T0
```

trong LIR.

Các thanh ghi thật chỉ xuất hiện ở Machine IR.

---

# 6. Typed virtual register

Tôi đề xuất:

```text
LIRType =
    i1
    i8
    i16
    i32
    i64
    i128
    f32
    f64
    ptr
    vector
```

Nhưng `i128` có thể được backend legalize thành:

```text
pair<i64, i64>
```

nếu CPU không hỗ trợ.

Điều này rất hợp với triết lý Axiom:

> **Ngôn ngữ có thể mạnh hơn phần cứng; backend chịu trách nhiệm hạ xuống.**

---

# 7. Pointer trong LIR

Đây là chỗ phải phân biệt rất rõ:

### MIR

Pointer vẫn mang semantics về:

- provenance
- ownership
- capability
- region
- lifetime

### LIR

Pointer chủ yếu trở thành machine address.

Ví dụ:

```text
%p : ptr
%v = LOAD i64, %p
```

Sau khi semantic verification đã hoàn tất.

Nhưng LIR vẫn cần metadata nếu optimizer còn cần alias information.

Ví dụ:

```text
LOAD %p
```

có thể kèm:

```text
alias_group = 17
```

hoặc:

```text
noalias_with = {3, 5}
```

nhưng:

> Metadata này **không tạo ra semantics**.

Nếu metadata sai, compiler phải coi đó là compiler bug, không phải chương trình có UB tự nhiên.

---

# 8. Memory model của LIR

Đây là phần tôi muốn giữ rất nhỏ.

## Load

```text
%v = LOAD T, address
```

## Store

```text
STORE T, address, value
```

## Atomic

```text
%v = ATOMIC_LOAD T, address, Acquire

ATOMIC_STORE T, address, value, Release

%old = ATOMIC_RMW Add, address, value, AcqRel

%ok, %old = ATOMIC_CAS
    address,
    expected,
    desired,
    AcqRel,
    Acquire
```

## Fence

```text
FENCE Acquire
FENCE Release
FENCE SeqCst
```

### Không được phép

Backend biến:

```text
Acquire
```

thành:

```text
Relaxed
```

chỉ vì target cho phép.

Đây là invariant bắt buộc.

---

# 9. Volatile phải khác Atomic

LIR:

```text
VOLATILE_LOAD
VOLATILE_STORE
```

khác:

```text
ATOMIC_LOAD
ATOMIC_STORE
```

Vì:

```text
volatile != synchronization
```

Volatile phục vụ:

- MMIO
- hardware registers
- device memory
- một số FFI/system cases

Atomic phục vụ memory synchronization/concurrency.

---

# 10. Addressing mode

Không nên đưa x86 addressing mode vào LIR:

```text
[r1 + r2*8 + 32]
```

vì ARM/RISC-V không giống vậy.

LIR nên có:

```text
ADDRESS {
    base
    index?
    scale?
    offset
}
```

nhưng thậm chí `scale` cũng không nên được xem là bắt buộc.

Có thể đơn giản hơn:

```text
%addr = PTR_ADD %base, %offset
%v = LOAD %addr
```

Target lowering có thể biến:

```text
PTR_ADD + LOAD
```

thành:

```text
mov rax, [rbx + rcx*8 + 32]
```

hoặc ARM:

```text
ldr x0, [x1, x2, lsl #3]
```

hoặc RISC-V:

```text
slli t0, t1, 3
add  t0, t0, t2
ld   a0, 0(t0)
```

### Tôi nghiêng về cách này.

LIR không cần cố mô tả mọi addressing mode của CPU.

---

# 11. Control flow

LIR dùng basic block:

```text
block0:
    %x = ...
    %c = CMP_LT %x, %y
    BR %c, block1, block2

block1:
    ...
    JUMP block3

block2:
    ...
    JUMP block3

block3:
    ...
```

Terminators:

```text
JUMP
BR
SWITCH
RETURN
TRAP
UNREACHABLE
```

Có thể thêm:

```text
TAILCALL
```

nhưng tail-call legality nên được ABI backend quyết định.

---

# 12. PHI có nên giữ không?

Có.

LIR vẫn có thể là **SSA-oriented**.

Ví dụ:

```text
block3:
    %x = PHI [
        (%a, block1),
        (%b, block2)
    ]
```

Sau đó Machine IR mới eliminate PHI thành register moves.

Điều này giúp:

- optimizer đơn giản
- SSA analysis
- register allocation
- giảm số lượng memory temporary

---

# 13. SELECT

Giữ:

```text
%r = SELECT %condition, %true_value, %false_value
```

Backend có thể biến thành:

```text
cmov
csel
conditional move
branch
```

Tùy target.

Đây là ví dụ điển hình cho nguyên tắc:

> LIR mô tả **ý định**, Machine IR quyết định **cách thực hiện**.

---

# 14. Memory copy

Không cần frontend tự sinh loop.

LIR nên có intrinsic:

```text
MEMCPY
MEMMOVE
MEMSET
```

Ví dụ:

```text
MEMCPY
    dst
    src
    size
    alignment
```

Target optimizer có thể biến thành:

- inline loads/stores
- vector instructions
- `rep movsb`
- libc call
- custom loop

Nhưng:

> không được mặc định phụ thuộc libc.

Nếu Axiom compiler tự generate code thì `memcpy` có thể được inline hoàn toàn.

---

# 15. Call

LIR:

```text
CALL {
    callee
    args
    returns
    abi
    effects
}
```

Ví dụ:

```text
%r = CALL @foo(%a, %b)
```

ABI lúc này đã được ABI lowering xác định.

Có thể có:

```text
@abi(axiom)
@abi(C)
@abi(system)
```

Nhưng Machine IR mới quyết định:

```text
arg0 → RDI
arg1 → RSI
return → RAX
```

hoặc:

```text
arg0 → X0
arg1 → X1
return → X0
```

---

# 16. Aggregate không nên tồn tại quá lâu

Một vấn đề quan trọng:

```axiom
struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

MIR có thể:

```text
Vec3
```

Nhưng sau ABI lowering:

```text
f32 x
f32 y
f32 z
```

hoặc:

```text
vector register
```

hoặc:

```text
memory address
```

tùy ABI.

Do đó:

```text
MIR
  ↓
ABI MIR
```

là nơi aggregate classification xảy ra.

LIR không nên trở thành một “struct IR”.

---

# 17. Stack

Tôi **không muốn LIR có `alloca`**.

Không:

```text
ALLOCA 128
```

trừ khi semantics thực sự yêu cầu.

LIR chỉ cần:

```text
LOAD
STORE
```

Machine backend tự tạo:

```text
stack slots
spill slots
outgoing argument area
saved registers
local frame
```

Điều này giữ:

```text
source variable != stack slot
```

đúng với memory model của Axiom.

---

# 18. LIR Intrinsics

Một số thứ không nên là instruction Core nhưng cần compiler hiểu.

Ví dụ:

```text
TRAP
DEBUG_BREAK
CPU_PAUSE
PREFETCH
BITCAST
BYTESWAP
BITCOUNT
LEADING_ZERO
TRAILING_ZERO
ROTATE
VECTOR_SHUFFLE
```

Nhóm này có thể gọi là:

```text
Axiom LIR Intrinsic
```

Backend có thể:

```text
intrinsic → instruction
intrinsic → sequence
intrinsic → runtime call
```

nhưng runtime call chỉ khi thực sự cần.

---

# 19. SIMD

Không nên thiết kế SIMD thành hàng trăm instruction trong Core.

LIR:

```text
Vector<T, N>
```

và một nhóm generic operations:

```text
VADD
VSUB
VMUL
VDIV
VAND
VOR
VXOR
VSHL
VSHR
VCOMPARE
VSELECT
VSHUFFLE
```

Ví dụ:

```text
v4f32
```

Backend:

```text
x86 → SSE/AVX/AVX2/AVX-512
ARM → NEON/SVE
RISC-V → RVV
```

Nếu target không hỗ trợ:

```text
vector → scalarize
```

hoặc báo unsupported nếu semantics yêu cầu native vector width.

---

# 20. Target Feature

Không nên viết:

```text
if x86_avx2
```

trong frontend.

Target capability nên được biểu diễn:

```text
Target {
    arch
    os
    abi
    features
}
```

Ví dụ:

```text
arch = x86_64
features = [sse2, avx2, bmi2]
```

hoặc:

```text
arch = aarch64
features = [neon]
```

Frontend chỉ có thể dùng feature gating ở cấp source/build.

Backend mới quyết định instruction.

---

# 21. Target Backend Contract

Đây là phần **quan trọng hơn cả LIR instruction set**.

Mỗi backend phải tuân thủ:

### TBC-01 — Semantic Preservation

Backend không được thay đổi semantics của LIR.

```text
LIR semantics == machine semantics
```

---

### TBC-02 — Memory Ordering

Không được yếu hóa:

```text
Acquire
Release
AcqRel
SeqCst
```

---

### TBC-03 — Overflow Semantics

Không được biến:

```text
CHECKED
```

thành:

```text
WRAP
```

hoặc ngược lại.

---

### TBC-04 — No Invented UB

Backend không được giả định:

```text
x cannot overflow
p cannot alias q
value is initialized
```

nếu LIR không chứng minh được.

---

### TBC-05 — Alias Metadata

Nếu alias information không chắc chắn:

```text
UNKNOWN
```

thì backend/optimizer phải xử lý như có thể alias.

Không được đoán.

---

### TBC-06 — Unsupported Operation

Nếu target không hỗ trợ trực tiếp:

```text
LIR op
 ↓
legalization
```

Nếu không thể legalize:

```text
deterministic compiler error
```

Không được âm thầm đổi semantics.

---

### TBC-07 — Target Optimization

Backend được phép:

```text
combine
fold
schedule
vectorize
fuse
remove
```

miễn là observable semantics giữ nguyên.

---

### TBC-08 — Register Allocation

Register allocator không được làm thay đổi semantics.

Đặc biệt:

```text
MOVE ownership
```

không đồng nghĩa:

```text
physical memcpy
```

---

### TBC-09 — ABI

Backend phải tuân thủ ABI lowering đã được xác định.

Không tự ý thay đổi:

- argument meaning
- return meaning
- calling convention
- alignment
- aggregate ownership semantics

---

### TBC-10 — Determinism

Cùng:

```text
source
compiler version
target
features
optimization profile
```

phải cho phép reproducible result theo build profile.

---

# 22. Machine IR mới là nơi “thật sự biết CPU”

Machine IR có thể có:

```text
PhysicalRegister
VirtualRegister
StackSlot
FrameIndex
MachineMemoryOperand
MachineInstruction
MachineBlock
```

Ví dụ x86:

```text
MOV RAX, RBX
ADD RAX, RCX
CMP RAX, RDX
JLT block3
```

ARM:

```text
ADD X0, X1, X2
CMP X0, X3
B.LT block3
```

RISC-V:

```text
ADD t0, t1, t2
SLT t3, t0, t4
BNE t3, zero, block3
```

Đây mới là nơi cho phép target-specific intelligence.

---

# 23. Register allocation

Không cần phát minh thuật toán ngay từ đầu.

Axiom có thể:

### Stage 1

```text
Linear Scan
```

ưu tiên:

- đơn giản
- dễ debug
- compile nhanh

### Stage 2

```text
Hybrid / Graph Coloring
```

khi muốn tối ưu code chất lượng cao.

Đây cũng phù hợp với triết lý:

> Compiler có thể tiến hóa mà không thay đổi language semantics.

---

# 24. Tôi đề xuất một điểm rất quan trọng: LIR không có GC Safepoint

Axiom không có GC mặc định.

Do đó không nên thiết kế LIR kiểu:

```text
SAFEPOINT
STACKMAP
GC_ROOT
```

như một primitive mặc định.

Nếu sau này một thư viện/runtime đặc biệt cần:

```text
GC
```

thì đó là runtime profile riêng.

Core compiler không bị kiến trúc GC chi phối.

---

# 25. LIR cũng không cần exception machinery

Không:

```text
LANDINGPAD
RESUME_EXCEPTION
CATCH
THROW
```

trong LIR Core.

Axiom sử dụng:

```text
Result
Option
Panic
Trap
```

Panic unwind nếu profile yêu cầu có thể được lowering thành:

```text
cleanup blocks
unwind metadata
runtime support
```

chứ không biến Axiom thành C++ exception IR.

---

# 26. LIR v0.1 đề xuất

Có thể đóng spec sơ bộ như sau:

```text
AXIOM LIR v0.1

Integer:
    IADD
    ISUB
    IMUL
    IDIV
    IDIV_U
    IREM
    IREM_U
    AND
    OR
    XOR
    NOT
    SHL
    SHR
    SHR_U
    NEG

Float:
    FADD
    FSUB
    FMUL
    FDIV
    FNEG
    FCMP

Compare:
    ICMP_EQ
    ICMP_NE
    ICMP_LT
    ICMP_LE
    ICMP_GT
    ICMP_GE

Conversion:
    CAST
    ZEXT
    SEXT
    TRUNC
    FEXT
    FTRUNC
    INT_TO_FLOAT
    FLOAT_TO_INT
    BITCAST

Memory:
    LOAD
    STORE
    VOLATILE_LOAD
    VOLATILE_STORE
    MEMCPY
    MEMMOVE
    MEMSET

Atomic:
    ATOMIC_LOAD
    ATOMIC_STORE
    ATOMIC_RMW
    ATOMIC_CAS
    FENCE

Control:
    PHI
    SELECT
    JUMP
    BR
    SWITCH
    RETURN
    TRAP
    UNREACHABLE

Call:
    CALL
    TAILCALL

Pointer:
    PTR_ADD
    PTR_DIFF

Vector:
    VADD
    VSUB
    VMUL
    VDIV
    VAND
    VOR
    VXOR
    VSHL
    VSHR
    VCMP
    VSELECT
    VSHUFFLE

Intrinsics:
    BITCOUNT
    CLZ
    CTZ
    ROTATE
    BYTESWAP
    PREFETCH
    DEBUG_BREAK
```

Không cần đóng từng opcode thành bất biến ngay. Nhưng **phạm vi** như vậy là hợp lý.

---

# 27. Một thay đổi kiến trúc tôi rất khuyến nghị

Không gọi LIR là:

> “Low-level version of MIR”

mà định nghĩa chính xác hơn:

> **Axiom LIR is the target-neutral machine-oriented representation produced after semantic verification and ABI lowering.**

Điều này giúp tránh một lỗi lớn:

```text
MIR
 ↓
LIR
 ↓
Machine IR
```

không phải ba compiler semantics khác nhau.

Mà là:

```text
MIR
= WHAT THE PROGRAM MEANS

LIR
= HOW THAT MEANING CAN BE EXPRESSED MACHINE-INDEPENDENTLY

Machine IR
= HOW THIS TARGET WILL EXECUTE IT
```

---

# 28. Và đây là ranh giới rất đẹp của Axiom

```text
                  LANGUAGE
                     │
                     ▼
                    MIR
                     │
        ┌────────────┴────────────┐
        │ Semantic Verification   │
        │ Ownership               │
        │ Region                  │
        │ Capability              │
        │ Concurrency             │
        │ Effects                 │
        └────────────┬────────────┘
                     │
                VERIFIED MIR
                     │
                     ▼
                 ABI LOWERING
                     │
                     ▼
                    LIR
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
        x86-64      ARM64      RISC-V
          │          │          │
          ▼          ▼          ▼
      Machine IR  Machine IR  Machine IR
          │          │          │
          ▼          ▼          ▼
        Native     Native     Native
```

Đây là kiến trúc tôi nghĩ rất phù hợp với mục tiêu ban đầu của bạn: **ngôn ngữ mạnh nhưng không bắt lập trình viên phải mang theo sự phức tạp của compiler**.

Đặc biệt, nó bảo vệ được một nguyên tắc mà chúng ta đã thống nhất trước đó:

> **Compiler có thể rất phức tạp; ngôn ngữ không nhất thiết phải phức tạp.**

### Bước tiếp theo tôi đề xuất

Sau LIR, nên đi thẳng vào **`AXIOM MACHINE IR + x86-64 BACKEND v0.1`** và làm một vertical slice thật sự:

```text
fn add(a: i64, b: i64) -> i64 {
    a + b
}

Axiom source
 → AST
 → HIR
 → MIR
 → Verified MIR
 → ABI MIR
 → LIR
 → x86-64 Machine IR
 → machine bytes
 → ELF/PE object
 → executable
```

Nếu vertical slice này chạy được, chúng ta sẽ có **“xương sống native compiler”** thực sự, thay vì tiếp tục thiết kế IR trên giấy.