Tiếp tục. Ta đi vào phần **Instruction Selection + Register Allocation**, nhưng tôi muốn làm rõ một nguyên tắc trước: **đừng thiết kế Axiom backend theo kiểu một bảng `LIR opcode → x86 opcode` đơn giản**. Một LIR operation có thể có nhiều cách hạ xuống, và lựa chọn tốt phụ thuộc vào context.

# AXIOM x86-64 INSTRUCTION SELECTION v0.1

## 1. Kiến trúc

```text id="k9zq0v"
Axiom LIR
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
Final Machine IR
    ↓
Encoder
```

Tách **Legalization** và **Instruction Selection** là rất đáng giá.

Ví dụ:

```text
i128 ADD
```

x86-64 không có integer register 128-bit tổng quát.

Legalizer biến:

```text
i128
```

thành conceptually:

```text
{lo:i64, hi:i64}
```

Sau đó instruction selector mới xử lý.

---

# 2. Legalization

Backend cần phân biệt:

```text id="c3u7jv"
Legal
Legalize
Expand
Reject
```

Ví dụ:

| LIR | x86-64 |
|---|---|
| i8 add | Legal |
| i16 add | Legal |
| i32 add | Legal |
| i64 add | Legal |
| i128 add | Expand |
| f32 add | Legal |
| f64 add | Legal |
| v4f32 add | Legal |
| v32f32 add | Expand |
| atomic i64 | Legal |
| exotic vector | Expand/Reject |

---

# 3. Legalization không được thay đổi semantics

Ví dụ:

```text id="p2lq6e"
IADD_CHECKED i128
```

không được biến thành:

```text id="q2h9m0"
IADD_WRAP
```

Legalizer phải tạo sequence tương đương:

```text id="4e3s7v"
lo_result
hi_result
overflow
```

và giữ nguyên semantics.

---

# 4. Instruction Selection nên pattern-based

Ví dụ LIR:

```text id="d9v2m5"
%3 = IADD %1, %2
```

Pattern:

```text id="b1h8b7"
IADD(GPR, GPR)
→ ADD reg, reg
```

Nhưng nếu:

```text id="3fj5z6"
%2 = CONST 1
%3 = IADD %1, %2
```

có thể chọn:

```text id="7n7p7a"
INC
```

hoặc:

```text id="t2y2r1"
ADD reg, 1
```

Backend có thể chọn cái phù hợp.

---

# 5. Nhưng đừng dùng peephole everywhere

Không nên biến selector thành một đống:

```text
if A and B and C and D...
```

Tốt hơn là có:

```text id="g0p4xq"
LIR pattern
→ Machine pattern
→ cost
→ constraints
```

Ví dụ conceptually:

```text id="ujgk4r"
Pattern {
    match: IADD(x, y)
    result: ADD(x, y)
    cost: 1
}
```

Một pattern khác:

```text id="1yn2xk"
Pattern {
    match: IADD(x, CONST(1))
    result: ADD_IMM(x, 1)
    cost: 1
}
```

---

# 6. Cost model

Backend cần một cost model đơn giản:

```text id="z7p9lf"
InstructionCost {
    latency
    throughput
    code_size
}
```

Nhưng **đừng cố mô phỏng CPU hoàn hảo**.

Ban đầu chỉ cần:

```text id="g4ut1d"
code_size
rough_cost
```

Sau này mới thêm microarchitecture-specific tuning.

---

# 7. Ví dụ ADD

LIR:

```text id="0c3t0v"
%3 = IADD %1, %2
```

Selector có thể tạo:

```text id="2q8w3s"
ADD64 %1, %2 → %3
```

Machine IR tạm thời:

```text id="5o6yuj"
%v3 = ADD64 %v1, %v2
```

Sau register allocation:

```text id="3b2n8k"
ADD64 RAX, RBX
```

---

# 8. Nhưng x86 ADD destructive

Đây là một vấn đề cực kỳ quan trọng.

LIR:

```text id="b0w4hr"
%3 = %1 + %2
```

có semantics:

```text id="g5c0h3"
%1 remains valid
%2 remains valid
%3 is new value
```

x86:

```text id="2p7zjp"
ADD RAX, RBX
```

thay đổi RAX.

Selector phải đảm bảo:

```text id="8zbb6u"
RAX = %3
```

và nếu `%1` vẫn được dùng sau đó, phải copy:

```text id="v5y7tj"
MOV RAX, %1
ADD RAX, %2
```

Đây chính là lý do **SSA + register allocation** rất quan trọng.

---

# 9. Copy coalescing

Nhưng không muốn:

```text id="a2h7nq"
MOV RAX, RDI
ADD RAX, RSI
```

nếu có thể trực tiếp:

```text id="k4b1h9"
ADD RDI, RSI
```

mà không phá live value.

Do đó register allocator nên có:

> **copy coalescing**

Nếu:

```text id="a7lq8z"
%3 = COPY %1
```

thì cố gắng assign:

```text id="r1m8q0"
%3 và %1 → cùng physical register
```

khi lifetime cho phép.

---

# 10. Đây là một điểm Axiom có thể rất mạnh

Ownership semantics giúp compiler biết khá nhiều về lifetime.

Ví dụ:

```axiom id="8g5m2c"
let y = x
```

nếu `x` bị move:

```text id="eq3k6s"
x → MOVED
y → OWNED
```

Sau MIR verification, compiler biết `x` không còn được đọc.

Điều này tạo cơ hội cho register allocator:

```text id="m3h4gk"
x và y
```

dùng cùng storage/register nếu semantics cho phép.

**Không cần `memcpy`.**

---

# 11. LOAD

LIR:

```text id="a9b7h2"
%v = LOAD i64, %addr
```

x86:

```text id="j8g4s1"
MOV RAX, [address]
```

Nếu address là:

```text id="1t8w4q"
base + offset
```

selector có thể tạo memory operand trực tiếp.

Ví dụ:

```text id="3t8w1k"
LOAD [RDI + 8]
```

→

```asm id="t4s2p7"
mov rax, [rdi+8]
```

---

# 12. STORE

LIR:

```text id="v5m3w9"
STORE i64, %addr, %value
```

x86:

```text id="l7q0pc"
MOV [addr], reg
```

Một nguyên tắc:

> LIR có address/value độc lập; Machine IR có thể fold address calculation vào memory operand.

Ví dụ:

```text id="q1k6dd"
%p = PTR_ADD %base, 16
STORE %p, %x
```

có thể trở thành:

```asm id="4x3c8y"
mov [rdi+16], rax
```

không cần register trung gian.

---

# 13. PTR_ADD

LIR:

```text id="k4n8ys"
%p = PTR_ADD %base, %offset
```

Không nhất thiết tạo machine `ADD`.

Nếu consumer là LOAD:

```text id="o6m3s4"
LOAD %p
```

selector có thể combine:

```text id="7m2k1a"
PTR_ADD + LOAD
```

thành một addressing mode.

Đây là **addressing-mode folding**.

---

# 14. ICMP

LIR:

```text id="4r3h2v"
%c = ICMP_LT %a, %b
```

x86:

```asm id="5r1x7b"
cmp a, b
setl c
```

Nhưng nếu ngay sau đó:

```text id="z2x8qp"
BR %c
```

không nhất thiết phải tạo `SETL`.

Có thể:

```asm id="1p5k9a"
cmp a, b
jl target
```

Do đó instruction selector cần nhìn **context**, không chỉ từng instruction độc lập.

---

# 15. Đây là lý do tôi đề xuất Machine IR có condition codes

LIR:

```text id="1v4w8k"
%c = ICMP_LT a,b
BR %c
```

Machine selector có thể tạo:

```text id="k9m5s4"
CMP a,b
JCC LT
```

mà không vật hóa `%c` thành register.

Nếu `%c` được dùng:

```text id="t4q7w3"
x = SELECT %c, a, b
```

có thể:

```asm id="u5p1q8"
cmp
cmovl
```

Một abstraction:

```text id="e4j7k0"
MachineCondition
```

rất hữu ích.

---

# 16. SELECT

LIR:

```text id="7m3w5x"
%r = SELECT %c, %a, %b
```

Có thể:

```text id="0v7r4h"
CMP
CMOV
```

hoặc:

```text id="8z3k5n"
branch
```

Backend cost model quyết định.

---

# 17. Branch inversion

Backend có thể đảo:

```text id="4r7p2m"
if !condition
```

thành:

```text id="c5j8q1"
if condition
```

để tối ưu layout:

```text id="q9m1xz"
fall-through = likely path
```

Đây là machine-level optimization, không ảnh hưởng semantics.

---

# 18. Branch probability

MIR/LIR có thể có optional metadata:

```text id="2s9v6h"
branch_probability:
    true = 0.8
    false = 0.2
```

Nhưng:

> Đây chỉ là optimization hint, không phải semantics.

Nếu hint sai, chương trình vẫn đúng.

---

# 19. CALL

LIR:

```text id="9s2w8m"
CALL @foo(a,b)
```

ABI lowering đã biết:

```text id="c5v7n1"
a → RDI
b → RSI
```

Machine IR:

```text id="e4k2p8"
CALL @foo
```

Register allocator phải biết:

```text id="j7f3m0"
caller_saved registers are clobbered
```

Ví dụ:

```text id="b2m9c6"
RAX
RCX
RDX
RSI
RDI
R8-R11
```

có thể bị clobber.

Nếu một live value đang ở RAX trước CALL:

```text id="x3c8q2"
spill/move
```

nếu cần.

---

# 20. CALL cũng là optimization barrier tương đối

Không phải tuyệt đối.

Compiler có thể:

- inline
- eliminate dead call
- reorder pure operations

nếu effect system chứng minh an toàn.

Nhưng nếu:

```text id="5z7m1c"
CALL unknown_external()
```

thì effect conservative:

```text id="x4n8b2"
may_read_memory
may_write_memory
may_throw/panic
may_observe
```

Tùy ABI/effect contract.

---

# 21. Tail call

LIR:

```text id="0k5w7z"
TAILCALL foo(...)
```

Machine backend chỉ được thực hiện nếu:

```text id="2p8r4c"
ABI-compatible
stack-compatible
register-compatible
frame-compatible
```

Nếu không:

```text id="h7x3q9"
CALL
RETURN
```

Không được giả định tail call luôn khả thi.

---

# 22. Memory alias optimization

Ví dụ:

```axiom id="1v5n8a"
fn f(mut_view<i64> a, mut_view<i64> b) {
    a[0] = 1
    b[0] = 2
}
```

Nếu verifier đã chứng minh:

```text id="4q7c1m"
region(a) DISJOINT region(b)
```

optimizer có thể giữ:

```text id="p6n9r3"
noalias
```

ở metadata.

Nếu không chứng minh được:

```text id="n2k5x8"
UNKNOWN
```

backend không được giả định disjoint.

Điều này cực kỳ quan trọng cho hiệu năng mà không cần bắt programmer viết annotation.

---

# 23. Axiom có thể có một lợi thế so với C ở đây

Trong C:

```c
void f(int *a, int *b)
```

compiler thường khó biết `a` và `b` không alias.

Axiom:

```axiom id="4s6j2p"
fn f(a: mut_view<i64>, b: mut_view<i64>)
```

được verifier kiểm tra provenance/region.

Nếu call site:

```text id="6w9p2a"
f(view(x.a), mut_view(x.b))
```

và fields disjoint:

```text id="r5k8c1"
x.a ∩ x.b = ∅
```

optimizer có thể biết điều đó.

**Không cần programmer viết `restrict`.**

Đây là một trong những lý do tôi nghĩ hệ thống `ownership + region + capability` hiện tại đáng giữ.

---

# 24. Register Allocation

Sau instruction selection:

```text id="0q7m2x"
%v0
%v1
%v2
%v3
...
```

Ta cần liveness.

Ví dụ:

```text id="8c3j5m"
%v0 live [1,4]
%v1 live [2,3]
%v2 live [3,6]
```

Nếu:

```text id="m7p4x2"
%v0
```

và:

```text id="j5k8c9"
%v2
```

không overlap:

```text id="h3q6w1"
→ cùng physical register
```

---

# 25. Linear Scan

Initial algorithm:

```text id="6z2v9n"
1. Build live intervals
2. Sort by start
3. Maintain active intervals
4. Allocate free register
5. Spill when needed
```

Pseudo:

```text id="r8c4m2"
for interval in intervals:
    expire_old()
    if register_available:
        assign()
    else:
        spill()
```

Đơn giản và đủ tốt cho compiler v0.1.

---

# 26. Spill

Nếu hết register:

```text id="8w4n6q"
%v7
```

được đưa vào:

```text id="x1c5p9"
StackSlot #3
```

Use:

```text id="p7m2d4"
LOAD RAX, [frame+slot3]
```

Def:

```text id="z9q4k6"
STORE [frame+slot3], RAX
```

Sau đó frame layout tính stack offset thật.

---

# 27. Spill cost

Không nên spill tùy tiện.

Cost đơn giản:

```text id="h8c2p1"
cost =
    use_count
    × estimated_memory_cost
```

Có thể ưu tiên spill:

- value ít dùng
- lifetime dài
- dễ recompute

Sau này mới có sophisticated heuristic.

---

# 28. Rematerialization

Ví dụ:

```text id="j7n4x2"
%v = CONST 0
```

Nếu `%v` bị spill:

không nhất thiết:

```asm
mov [stack], 0
```

sau đó reload.

Có thể rematerialize:

```asm
xor eax,eax
```

hoặc:

```asm
mov eax,0
```

Đây là optimization nhỏ nhưng rất hữu ích.

---

# 29. Phi elimination

Machine IR trước register allocation:

```text id="p3k7m9"
bb3:
    %x = PHI [
        %a from bb1,
        %b from bb2
    ]
```

Sau đó:

```text id="y4c8q1"
bb1:
    COPY %a, %x

bb2:
    COPY %b, %x
```

rồi coalescing cố làm:

```text id="w8m2p6"
%a
%b
%x
```

sử dụng cùng register nếu khả thi.

---

# 30. Một nguyên tắc rất đáng đóng

### Không tối ưu bằng cách phá semantics để đạt “zero-cost”.

Ví dụ:

```text id="m1q8c5"
ownership information
```

có thể cho phép optimizer loại bỏ move.

Nhưng không được:

```text id="v4k9p2"
bỏ DROP
```

nếu DROP có observable effect.

Ví dụ:

```axiom id="1d7x3m"
MutexGuard
```

Drop có thể unlock mutex.

Không được optimizer nghĩ:

> “Drop chỉ là bookkeeping nên xóa.”

Verifier/optimizer phải biết:

```text id="2p6k8n"
Drop has effect
```

---

# 31. Effect metadata xuống LIR

Đây là một điểm tôi đề xuất thêm.

MIR có effect rất giàu:

```text id="h8v2q7"
READ
WRITE
MOVE
DROP
ALLOC
LOCK
ATOMIC
IO
PANIC
```

Sau lowering, LIR chỉ giữ phần cần cho optimization:

```text id="c6m4x9"
MemoryEffect:
    None
    Read
    Write
    ReadWrite
    Atomic
    Volatile
    Unknown
```

Ví dụ:

```text id="y5p8r1"
CALL pure_fn
```

có thể:

```text id="d2k7v3"
MemoryEffect = None
```

Trong khi:

```text id="x4m9q6"
CALL unknown
```

→

```text id="n7c2p5"
MemoryEffect = Unknown
```

Điều này giúp optimizer mạnh mà vẫn nhỏ.

---

# 32. Đừng mang toàn bộ ownership system xuống Machine IR

Machine IR không cần biết:

```text id="8x5q2m"
OWNED
MOVED
PARTIAL
VIEW
CAPABILITY
PROVENANCE
```

Sau semantic verification:

```text id="r6n9c3"
ownership → erased
```

trừ metadata debug nếu compiler đang chạy debug mode.

Đây là **semantic erasure boundary**.

---

# 33. Debug mode có thể giữ nó

Ví dụ:

```text id="0f4x7q"
MachineDebugMetadata {
    source_span
    variable
    ownership_state?
    region?
}
```

Nhưng:

> Debug metadata không ảnh hưởng native semantics.

---

# 34. Tôi muốn thêm một tầng: MIR Optimizer vs Machine Optimizer

Hai tầng không nên trộn.

### MIR optimizer

Hiểu:

- ownership
- regions
- generic types
- traits
- effects
- high-level control flow

### Machine optimizer

Hiểu:

- registers
- instruction latency
- addressing modes
- CPU features
- branch layout
- instruction scheduling

```text id="5q8m1n"
MIR Optimizer
      ↓
LIR
      ↓
Machine Optimizer
```

Điều này giúp compiler không biến thành một optimizer khổng lồ duy nhất.

---

# 35. Vertical slice thực sự nên đạt tới đây

Ví dụ source:

```axiom id="q4r7m2"
fn max(a: i64, b: i64) -> i64 {
    if a > b {
        a
    } else {
        b
    }
}
```

LIR:

```text id="n8c2x6"
%cmp = ICMP_GT %a, %b
BR %cmp, bb1, bb2

bb1:
    RETURN %a

bb2:
    RETURN %b
```

Instruction selection:

```text id="v5k9p3"
CMP %a, %b
JCC GT, bb1
...
```

Register allocation:

```text id="m7q2c8"
a → RDI
b → RSI
```

Machine:

```asm id="d4n8x1"
cmp rdi, rsi
jg  .L1
mov rax, rsi
ret

.L1:
mov rax, rdi
ret
```

Machine optimizer có thể nhận ra:

```text id="y2p6q9"
conditional return
```

và biến thành:

```asm id="b7c3m5"
mov rax, rdi
cmp rdi, rsi
cmovle rax, rsi
ret
```

Đó là một ví dụ rất đẹp về toàn bộ pipeline.

---

# 36. Nhưng tôi không muốn v0.1 phụ thuộc vào CMOV

Backend ban đầu có thể sinh branch.

Sau đó machine optimizer mới thêm:

```text id="s4m8q2"
branch → cmov
```

Như vậy:

```text id="8c1p7z"
Instruction Selection
```

đơn giản hơn rất nhiều.

---

# 37. Milestone thực tế

Tôi sẽ chia thành:

### M0

```text
Machine IR
Physical registers
Basic blocks
```

### M1

```text
MOV
ADD
SUB
RET
```

→ compile `add`.

### M2

```text
CMP
JCC
JMP
```

→ compile `max`.

### M3

```text
PHI
loop
```

→ compile `sum`.

### M4

```text
CALL
```

→ Axiom function calls Axiom function.

### M5

```text
LOAD
STORE
```

→ struct/array.

### M6

```text
stack frame
spill
```

→ functions phức tạp.

### M7

```text
ELF object
```

→ `.o`.

### M8

```text
system linker
```

→ executable.

---

# 38. Và lúc này chúng ta mới nên quay lại ownership

Sau M8, có một executable native tối thiểu.

Sau đó:

```text id="z5q1m7"
Vec
Drop
Box
view
mut_view
Result
Option
```

được đưa vào pipeline.

Đặc biệt:

```text id="4v8n2c"
Vec<T>
```

sẽ kiểm tra được một vấn đề rất quan trọng của Axiom:

```text id="e6m3q9"
MAY_RELOCATE
```

có thực sự được compiler xử lý đúng không.

---

# 39. Tôi muốn chốt thêm một invariant

### ABK-01 — Backend Independence

> Không một quy tắc semantics của Axiom được định nghĩa bởi x86-64 backend.

Ví dụ backend không được nói:

> “Move là memcpy vì x86 có instruction này.”

Mà:

```text
Axiom semantics
      ↓
MIR
      ↓
LIR
      ↓
x86 implementation
```

---

### ABK-02 — Target Replacement

Nếu thay:

```text id="k8p4v2"
x86-64
```

bằng:

```text id="w6m2c9"
ARM64
```

thì:

```text id="e3q7n1"
AST
HIR
MIR
Verifier
Semantic Oracle
```

phải giữ nguyên.

---

### ABK-03 — Backend Completeness

Mọi LIR operation phải:

```text
LEGAL
hoặc
LEGALIZABLE
hoặc
DETERMINISTICALLY REJECTED
```

Không có:

```text
"chắc CPU này làm được"
```

---

### ABK-04 — No Silent Semantic Degradation

Target thiếu instruction không được khiến compiler âm thầm đổi semantics.

---

### ABK-05 — Machine Optimization Is Optional

Có hay không có machine optimizer **không được thay đổi kết quả chương trình**.

---

## Và tôi nghĩ chúng ta đã đến một mốc rất quan trọng

Từ đây, **không nên tiếp tục mở rộng compiler architecture theo chiều ngang quá nhiều**.

Chúng ta đã có:

```text
Language
   ↓
Type System
   ↓
Ownership
   ↓
Memory
   ↓
Concurrency
   ↓
HIR
   ↓
MIR
   ↓
Verifier
   ↓
Semantic Oracle
   ↓
ABI
   ↓
LIR
   ↓
Machine IR
   ↓
x86 Backend
```

Bây giờ việc đáng làm nhất là **đóng “Genesis Compiler Slice”**:

```text
fn add(a: i64, b: i64) -> i64
fn max(a: i64, b: i64) -> i64
fn sum(n: i64) -> i64
fn square(x: i64) -> i64
```

và yêu cầu agent xây **toàn bộ pipeline chạy được end-to-end**, dù ban đầu parser/typechecker còn cực kỳ nhỏ.

Sau khi 4 hàm này:

```text
source
→ MIR
→ Verified MIR
→ LIR
→ x86 Machine IR
→ machine bytes
→ ELF
→ executable
→ chạy thật
```

thành công, ta mới có cơ sở thực nghiệm để quyết định những phần còn lại của Axiom. Đây sẽ là **Genesis milestone**, thay vì tiếp tục tạo thêm một specification khổng lồ mà chưa có native binary nào được sinh ra.