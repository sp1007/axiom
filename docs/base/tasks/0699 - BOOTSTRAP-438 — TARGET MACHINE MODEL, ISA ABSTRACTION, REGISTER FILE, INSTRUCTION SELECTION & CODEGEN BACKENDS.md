# BOOTSTRAP-438 — TARGET MACHINE MODEL, ISA ABSTRACTION, REGISTER FILE, INSTRUCTION SELECTION & CODEGEN BACKENDS

**Trạng thái: COMPLETED / LOCKED**

Mục tiêu của 438 là biến LIR thành **machine code thực sự**, nhưng vẫn giữ backend tách khỏi frontend và không phụ thuộc LLVM/GCC/Clang.

Kiến trúc:

```text
LIR
 ↓
Target Lowering
 ↓
Machine IR
 ↓
Instruction Selection
 ↓
Register Allocation
 ↓
Stack Frame / ABI
 ↓
Machine Scheduling
 ↓
Peephole Optimization
 ↓
Machine Encoder
 ↓
Object File
```

Backend đầu tiên phải ưu tiên:

```text
x86-64
AArch64
WASM
```

Trong đó native bootstrap ưu tiên x86-64 trước.

---

## 438.1 — Target Model

Một target được mô tả bởi:

```text
Target {
    arch
    os
    abi
    object_format
    endian
    pointer_width
    cpu
    features
    relocation_model
    code_model
}
```

Ví dụ:

```text
x86_64-pc-windows-msvc
x86_64-unknown-linux-gnu
aarch64-unknown-linux
aarch64-apple-darwin
wasm32-unknown-none
```

Tên target chỉ là định danh; semantics nằm trong `TargetSpec`.

---

## 438.2 — TargetSpec

```text
TargetSpec {
    architecture
    operating_system
    environment
    abi
    object_format
    data_layout
    default_cpu
    supported_features
    linker_policy
}
```

---

## 438.3 — Architecture không đồng nghĩa ABI

Ví dụ:

```text
x86-64 + SysV64
x86-64 + Win64
```

cùng ISA nhưng calling convention khác.

Do đó:

```text
ISA ≠ ABI
```

---

## 438.4 — OS không quyết định hoàn toàn ABI

Một OS có thể hỗ trợ nhiều ABI/toolchain conventions.

Axiom không hard-code:

```text
OS → single ABI
```

---

## 438.5 — CPU feature model

Feature set:

```text
FeatureSet {
    sse2
    sse4_2
    avx
    avx2
    avx512
    aes
    fma
    bmi1
    bmi2
    ...
}
```

AArch64:

```text
neon
sve
sve2
crypto
fp16
bf16
...
```

---

## 438.6 — Feature dependency

Feature có thể phụ thuộc feature khác.

Ví dụ:

```text
AVX2
→ AVX
```

Compiler phải canonicalize feature set trước codegen.

---

## 438.7 — CPU baseline

Mỗi target có baseline CPU.

Build không chỉ rõ CPU:

```text
-target x86_64-linux
```

sử dụng baseline target.

---

## 438.8 — CPU tuning

Có thể:

```text
-mcpu=native
```

hoặc:

```text
-cpu=znver
-cpu=haswell
-cpu=generic
```

Nhưng output phải ghi lại CPU/features để reproducibility.

---

## 438.9 — Feature mismatch

Nếu source yêu cầu:

```text
@target_feature(avx2)
```

nhưng target không hỗ trợ:

```text
compile-time diagnostic
```

không được silently generate unsupported instructions.

---

## 438.10 — ISA Backend Interface

Mỗi backend:

```text
TargetBackend {
    lower
    legalize
    select
    allocate_registers
    layout_frame
    schedule
    encode
}
```

---

## 438.11 — Backend không được phụ thuộc parser

Dependency direction:

```text
Parser
 ↓
Semantic
 ↓
IR
 ↓
Target Backend
```

Không được ngược lại.

---

## 438.12 — Generic backend services

Dùng chung:

```text
CFG
SSA
register allocation framework
stack frame builder
machine scheduler framework
relocation framework
debug location
```

ISA-specific backend chỉ cung cấp target rules.

---

## 438.13 — Machine IR

Machine instruction:

```text
MachineInstr {
    opcode
    operands[]
    flags
    debug_loc
}
```

---

## 438.14 — Machine operands

```text
Reg
Imm
Mem
Label
Symbol
Block
ConstantPool
StackSlot
```

---

## 438.15 — Virtual Register

Instruction selection chủ yếu tạo:

```text
vreg0
vreg1
vreg2
```

thay vì physical registers.

---

## 438.16 — Physical Register

Register allocator chuyển:

```text
vreg
→ preg
```

---

## 438.17 — Register Class

Mỗi virtual register thuộc class:

```text
GPR
FPR
SIMD
Special
```

---

## 438.18 — Register bank

Machine backend có thể phân biệt register banks nếu ISA cần.

---

## 438.19 — Register constraints

Instruction có thể yêu cầu:

```text
same register
different register
specific register
register pair
fixed register
```

---

## 438.20 — Fixed registers

Ví dụ instruction có input/output bắt buộc ở register cụ thể.

Machine IR phải biểu diễn constraint này trước register allocation.

---

## 438.21 — Register aliases

x86:

```text
RAX
EAX
AX
AL
```

là các phần của cùng physical register.

Register allocator phải hiểu aliasing.

---

## 438.22 — x86-64 Register Set

GPR:

```text
RAX RBX RCX RDX
RSI RDI RBP RSP
R8  R9  R10 R11
R12 R13 R14 R15
```

SIMD:

```text
XMM0..XMM31
YMM0..YMM31
ZMM0..ZMM31
```

tùy CPU mode/features.

---

## 438.23 — x86 FLAGS

Flags không phải GPR bình thường.

Machine IR phải biểu diễn dependency của instructions lên flags.

---

## 438.24 — AArch64 Register Set

GPR:

```text
X0..X30
SP
```

32-bit views:

```text
W0..W30
```

SIMD/FP:

```text
V0..V31
```

---

## 438.25 — AArch64 zero register

```text
XZR/WZR
```

là architectural special register.

---

## 438.26 — AArch64 SP

`SP` không được coi như ordinary GPR.

---

## 438.27 — WASM register model

WASM không có physical register allocation theo nghĩa native.

Backend có thể lower:

```text
SSA values
→ WASM locals/stack machine
```

Do đó WASM là backend riêng.

---

# 438.28 — Instruction Definition Table

ISA backend phải có machine instruction database:

```text
InstructionDef {
    opcode
    operands
    register_constraints
    encoding
    size
    latency
    throughput
    flags_read
    flags_written
}
```

---

## 438.29 — Không hard-code encoder rải rác

Không viết:

```text
if opcode == ADD ...
```

ở hàng chục nơi.

Thay vào đó:

```text
InstructionDef
→ Encoder
```

---

## 438.30 — Instruction encoding

Mỗi instruction có encoder descriptor:

```text
EncodingPattern {
    prefixes
    opcode
    modrm
    sib
    immediate
    displacement
    rex
    ...
}
```

x86 có format phức tạp hơn nhưng vẫn dùng cùng abstraction.

---

## 438.31 — Encoder độc lập object writer

Đã khóa ở 420:

```text
Machine Encoder
≠
Object Writer
```

---

## 438.32 — x86 addressing mode

Machine operand:

```text
Mem {
    base
    index
    scale
    displacement
    segment
}
```

---

## 438.33 — x86 scale

Scale hợp lệ:

```text
1
2
4
8
```

---

## 438.34 — x86 RIP-relative

Hỗ trợ:

```text
RIP + displacement
```

cho:

- PIC;
- global access;
- symbol references;
- jump tables.

---

## 438.35 — AArch64 addressing

Hỗ trợ:

```text
base + immediate
base + register
base + scaled register
pre-index
post-index
```

tùy instruction.

---

## 438.36 — Large immediates

Backend phải tự chọn sequence.

Ví dụ AArch64:

```text
MOVZ
MOVK
MOVN
```

hoặc literal pool nếu phù hợp.

---

## 438.37 — x86 immediate selection

Compiler chọn encoding ngắn nhất hợp lệ.

Ví dụ:

```text
imm8
imm32
imm64
```

tùy instruction.

---

## 438.38 — Constant materialization

Một constant lớn có thể:

```text
register immediate
literal pool
constant pool
memory load
```

Cost model quyết định.

---

## 438.39 — Constant pool

Machine function có:

```text
ConstantPool
```

và linker/object layer tạo section phù hợp.

---

## 438.40 — Jump table

`switch` có thể lower thành:

```text
conditional branches
```

hoặc:

```text
jump table
```

---

## 438.41 — Jump-table threshold

Target backend cung cấp cost model.

Không có ngưỡng universal.

---

## 438.42 — Instruction Selection

LIR:

```text
add i64
```

→ x86:

```text
ADD
```

hoặc sequence khác tùy constraints.

---

## 438.43 — Pattern matching

Instruction selector sử dụng pattern:

```text
LIR pattern
→ machine pattern
```

---

## 438.44 — Selection DAG không bắt buộc

Axiom không cần copy nguyên mô hình LLVM SelectionDAG.

Có thể dùng:

```text
SSA graph
+
pattern matcher
+
legalization
```

đơn giản hơn.

---

## 438.45 — Legalization

Nếu operation không có instruction trực tiếp:

```text
LIR operation
→ legal equivalent sequence
```

---

## 438.46 — Integer division

Ví dụ division có thể yêu cầu register cố định trên x86.

Backend phải đưa constraint vào Machine IR.

---

## 438.47 — Wide arithmetic

Nếu Axiom sau này hỗ trợ `i128`:

```text
i128 operation
→ multi-register sequence
```

trên target không có native i128.

---

## 438.48 — Multiplication

Backend có thể chọn:

```text
IMUL
LEA
shift/add
```

theo cost model.

---

## 438.49 — Address arithmetic

Ví dụ:

```text
base + index * 8
```

x86 có thể fold trực tiếp vào addressing mode.

AArch64 có thể dùng scaled addressing khi hợp lệ.

---

## 438.50 — Address folding

Optimizer/backend được phép fold:

```text
ADD address
LOAD
```

thành:

```text
LOAD [base + offset]
```

nếu không thay đổi semantics.

---

## 438.51 — Load/store selection

Memory operation chứa:

```text
type
size
alignment
volatile
atomic
address space
```

---

## 438.52 — Alignment

Backend được cung cấp alignment guarantee.

Không tự giả định alignment lớn hơn.

---

## 438.53 — Unaligned access

Target backend quyết định instruction sequence hợp lệ.

---

## 438.54 — Atomic lowering

Atomic operation phải map tới target instruction sequence đúng memory ordering.

---

## 438.55 — x86 atomic

Có thể dùng:

```text
LOCK
CMPXCHG
XADD
XCHG
```

tùy operation.

---

## 438.56 — AArch64 atomic

Backend hỗ trợ các primitive phù hợp:

```text
LDXR/STXR
LDAXR/STLXR
CAS
SWP
LDADD
...
```

tùy architecture features.

---

## 438.57 — Atomic fallback

Nếu CPU baseline không có instruction phù hợp:

```text
runtime/libatomic-style implementation
```

có thể được dùng **nếu Axiom runtime component cung cấp**, không gọi third-party compiler runtime.

---

## 438.58 — Lock-free claim

Không được tự động tuyên bố operation lock-free.

Target capability table phải xác nhận.

---

## 438.59 — Function call lowering

Call:

```text
LIR Call
```

→

```text
ABI argument assignment
→ register/stack operands
→ call instruction
```

---

## 438.60 — Return lowering

Return values được ABI classifier phân loại trước khi machine emission.

---

## 438.61 — Struct return

Nếu ABI yêu cầu hidden sret:

```text
return aggregate
→ hidden pointer argument
```

---

## 438.62 — Variadic call

Backend phải biết ABI varargs rules.

---

## 438.63 — Function prologue

Machine backend tạo:

```text
save registers
stack allocation
stack alignment
TLS/frame setup
```

khi cần.

---

## 438.64 — Function epilogue

```text
restore registers
deallocate stack
return
```

---

## 438.65 — Leaf function optimization

Leaf function có thể tránh:

```text
stack frame
saved registers
```

nếu không cần.

---

## 438.66 — Frame elimination

Nếu function không cần stack:

```text
frame size = 0
```

---

## 438.67 — Register allocation

Bootstrap allocator có thể bắt đầu bằng:

```text
linear scan
```

---

## 438.68 — Production register allocator

Sau bootstrap:

```text
graph coloring
hoặc
optimized linear scan
```

tùy benchmark.

Không khóa vào một thuật toán duy nhất.

---

## 438.69 — Allocation objectives

Ưu tiên:

1. correctness;
2. register pressure;
3. performance;
4. code size.

Không sacrifice correctness.

---

## 438.70 — Spill cost

Spill heuristic xét:

```text
use frequency
loop depth
instruction cost
register class
```

---

## 438.71 — Rematerialization

Một value rẻ có thể được recompute thay vì spill.

Ví dụ:

```text
constant
simple address
small immediate
```

---

## 438.72 — Register coalescing

Nếu:

```text
v1 = copy v2
```

allocator có thể map:

```text
v1 → same register as v2
```

---

## 438.73 — Copy elimination

Sau allocation:

```text
mov rax, rax
```

phải được loại.

---

## 438.74 — Parallel copies

ABI lowering có thể tạo parallel copy:

```text
a → rdi
b → rsi
rdi → ...
```

Machine backend phải resolve cycles.

---

## 438.75 — Stack slots

Mỗi spill:

```text
StackSlot {
    size
    alignment
    offset
}
```

---

## 438.76 — Stack slot coloring

Các spill slots có lifetime không overlap có thể reuse cùng memory.

---

## 438.77 — Stack frame layout

Frame layout phải đảm bảo:

```text
ABI alignment
callee-saved registers
spills
locals
outgoing arguments
red zone/probing
```

---

## 438.78 — Dynamic stack allocation

`alloca` runtime size yêu cầu dynamic stack adjustment.

---

## 438.79 — Dynamic alloca + alignment

Backend phải align dynamic allocation theo requested alignment.

---

## 438.80 — Stack restore

Dynamic stack allocation phải được restore trước return hoặc cleanup path.

---

## 438.81 — Tail calls

Tail call chỉ được emit nếu:

```text
ABI compatible
stack frame compatible
calling convention permits
```

---

## 438.82 — Sibling calls

Có thể tối ưu ordinary call/return thành jump khi ABI cho phép.

---

## 438.83 — Branch lowering

LIR:

```text
Branch cond, A, B
```

→ target conditional branch.

---

## 438.84 — Compare + branch fusion

Backend có thể fuse:

```text
compare
branch
```

thành target pattern.

---

## 438.85 — Conditional move

Nếu cost model cho phép:

```text
branch
```

có thể thành:

```text
CMOV
```

hoặc AArch64 `CSEL`.

---

## 438.86 — Branch inversion

Backend có thể đảo condition để giảm jump.

---

## 438.87 — Block layout

Basic blocks được sắp xếp để:

- giảm taken branches;
- tăng fall-through;
- cải thiện I-cache.

---

## 438.88 — Hot/cold splitting

Cold blocks có thể được đưa ra vùng code riêng.

---

## 438.89 — Function alignment

Backend có thể align function entry.

Không mặc định align quá lớn vì code size.

---

## 438.90 — Loop alignment

Có thể align hot loop khi target cost model cho thấy lợi ích.

---

## 438.91 — Instruction scheduling

Machine scheduler xét:

```text
dependencies
latency
throughput
register pressure
```

---

## 438.92 — x86 scheduling

Backend có thể có CPU-specific scheduling models.

---

## 438.93 — Generic CPU model

Nếu không có model:

```text
generic conservative cost model
```

---

## 438.94 — AArch64 scheduling

Baseline scheduler trước, CPU-specific tuning sau.

---

## 438.95 — Instruction fusion

Backend có thể nhận diện target-specific fusion.

---

## 438.96 — Peephole pass

Ví dụ:

```text
mov rax, 0
```

có thể đổi thành zeroing idiom nếu target model xác nhận lợi ích.

---

## 438.97 — Redundant load elimination

Machine-level optimization được phép nếu memory semantics vẫn đúng.

---

## 438.98 — Machine dead-code elimination

Machine instructions không có side effects có thể bị loại.

---

## 438.99 — Flag dependency

Không được loại instruction chỉ vì output register không dùng nếu instruction có flags side effect được dùng sau đó.

---

## 438.100 — x86 partial-register hazards

Backend phải hiểu:

```text
AL
AX
EAX
RAX
```

dependencies.

---

## 438.101 — x86 zero-extension semantics

Ghi `EAX` tự động zero-extend vào `RAX`; backend có thể tận dụng semantics này.

---

## 438.102 — AArch64 W/X relation

Ghi `Wn` zero-extends architectural `Xn`.

Backend phải model chính xác.

---

## 438.103 — SIMD abstraction

LIR vector:

```text
vector<T,N>
```

có thể lower thành target SIMD.

---

## 438.104 — SIMD legalization

Nếu target không có vector width yêu cầu:

```text
wide vector
→ multiple smaller vectors
```

hoặc scalar fallback.

---

## 438.105 — Scalar fallback

Mọi portable SIMD primitive cần semantics fallback nếu API yêu cầu portability.

---

## 438.106 — FMA

FMA chỉ được generate khi:

```text
target supports FMA
```

và floating-point optimization rules cho phép.

---

## 438.107 — Fast math

Không bật mặc định.

Nếu user bật relaxed FP:

```text
-fast-math
```

compiler được phép thay đổi một số FP transformations theo contract.

---

## 438.108 — TLS lowering

TLS:

```text
ThreadLocalAddress
```

được target/ABI lowering.

---

## 438.109 — PIC/PIE

Backend hỗ trợ:

```text
PIC
PIE
static
```

---

## 438.110 — Code model

Target có:

```text
small
medium
large
```

hoặc architecture-specific equivalents.

Bootstrap chỉ cần subset thực tế.

---

## 438.111 — Symbol reference

Machine operand:

```text
SymbolRef {
    symbol
    relocation_kind
    addend
}
```

---

## 438.112 — Relocation

Machine backend tạo relocation request.

Object writer chuyển nó thành object relocation.

---

## 438.113 — Fixup

Instruction-local fixup:

```text
branch displacement
immediate relocation
PC-relative offset
```

được xử lý bởi encoder/linker pipeline đã thiết kế ở 420.

---

## 438.114 — Branch relaxation

Nếu displacement không fit:

```text
short branch
→ long branch
```

---

## 438.115 — Literal pool relocation

AArch64 literal references có thể cần relocation/fixup tương ứng.

---

## 438.116 — GOT/PLT lowering

Chỉ khi ABI/PIC yêu cầu.

---

## 438.117 — Import calls

Windows/Linux/macOS dynamic imports được object/linker layer xử lý.

Backend chỉ phát symbol reference đúng ABI.

---

## 438.118 — Exported symbols

Machine function giữ linkage:

```text
internal
private
public
weak
extern
```

---

## 438.119 — Linkage không phải visibility

Hai khái niệm được giữ riêng:

```text
source visibility
≠
object linkage
```

---

## 438.120 — Section selection

Function/data có thể được đặt vào:

```text
.text
.rodata
.data
.bss
.tls
```

hoặc target-specific sections.

---

## 438.121 — Function sections

Compiler có thể emit:

```text
.text.<function>
```

để linker GC từng function.

---

## 438.122 — Data sections

Tương tự cho private constants/data.

---

## 438.123 — COMDAT / equivalent

Generic instantiations có thể cần deduplication.

Object backend quyết định mechanism:

```text
COMDAT
weak
linkonce
```

tùy format.

---

## 438.124 — Generic code emission

Mỗi concrete generic instance:

```text
InstanceKey
→ MachineFunction
```

---

## 438.125 — Generic deduplication

Compiler/linker có thể deduplicate identical instances.

---

## 438.126 — Backend cache

Cache machine code theo:

```text
semantic hash
target
CPU
features
ABI
optimization profile
compiler version
```

---

## 438.127 — Target-independent optimizer

Optimizer trước machine lowering không được kiểm tra:

```text
RAX
X0
```

---

## 438.128 — Target-specific optimizer

Sau lowering mới được dùng:

```text
LEA
CMOV
CSEL
NEON
AVX2
```

---

## 438.129 — Backend feature query

Optimizer có thể hỏi:

```text
target.has("avx2")
target.has("neon")
```

thông qua Target API.

---

## 438.130 — No backend-specific leakage

Không cho frontend syntax trực tiếp phụ thuộc:

```text
RAX
X0
```

ngoại trừ explicit low-level/inline-asm facility sau này.

---

## 438.131 — Inline assembly

Không thuộc bootstrap core.

Nếu bổ sung:

```text
asm
```

phải khai báo:

- registers;
- inputs;
- outputs;
- clobbers;
- memory effects;
- target constraints.

---

## 438.132 — Unsafe assembly

Inline assembly luôn thuộc unsafe boundary.

---

## 438.133 — Backend tests

Mỗi instruction có:

```text
Machine instruction test
→ expected bytes
```

---

## 438.134 — Encoder golden tests

Ví dụ conceptual:

```text
ADD RAX, RBX
→ expected x86 bytes
```

Không cần expose byte sequence cho user.

---

## 438.135 — ABI machine tests

Function:

```text
fn add(a:i32,b:i32)->i32
```

phải test:

```text
argument registers
return register
stack frame
```

---

## 438.136 — Cross-language ABI tests

Axiom:

```text
Axiom function
↔ C function
```

được kiểm tra trên từng target.

---

## 438.137 — Object integration test

Pipeline:

```text
LIR
→ Machine IR
→ bytes
→ object
→ linker
→ executable
```

phải được test end-to-end.

---

## 438.138 — Runtime integration

Test:

```text
fn main() -> i32 {
    return 42
}
```

phải produce native executable chạy thực tế.

---

## 438.139 — First x86-64 milestone

Compiler tối thiểu phải emit:

```text
mov
add
sub
imul
cmp
conditional branch
call
ret
```

---

## 438.140 — First AArch64 milestone

Tối thiểu:

```text
mov
add
sub
mul
cmp
branch
bl
ret
```

---

## 438.141 — First WASM milestone

Tối thiểu:

```text
i32.const
i32.add
local.get
local.set
call
return
br
br_if
```

---

## 438.142 — Backend implementation order

### Phase A

```text
x86-64
integer
control flow
call
return
stack
```

### Phase B

```text
AArch64
```

### Phase C

```text
WASM
```

### Phase D

```text
SIMD
atomics
PIC
TLS
advanced CPU tuning
```

---

## 438.143 — Bootstrap backend dependency

Backend chỉ phụ thuộc:

```text
LIR
ABI
TargetSpec
Machine IR
Object API
```

Không phụ thuộc:

```text
LLVM
GCC
Clang
MSVC compiler
```

---

## 438.144 — Native linker dependency

Axiom có thể sử dụng:

- OS linker trong một số interoperability/build modes nếu được cấu hình;
- nhưng **self-contained Axiom linker** là implementation target đã khóa ở BOOTSTRAP-420.

Native compiler path chuẩn không yêu cầu third-party compiler.

---

## 438.145 — Cross compilation

Backend có thể generate target khác host.

Ví dụ:

```text
Windows host
→ AArch64 Linux binary
```

---

## 438.146 — Host ≠ Target

Compiler phải phân biệt:

```text
HostTarget
CompileTarget
```

---

## 438.147 — Runtime target

Comptime cũng phải biết target từ 431.

---

## 438.148 — Endianness

Backend nhận endian từ TargetSpec.

---

## 438.149 — Pointer width

Không hard-code pointer 64-bit.

WASM32 và future 32-bit targets phải được hỗ trợ bởi abstraction.

---

## 438.150 — Backend diagnostics

Ví dụ:

```text
E438001 Unsupported target feature
E438002 Illegal instruction
E438003 Register allocation failure
E438004 Invalid machine operand
E438005 ABI lowering failure
E438006 Relocation constraint failure
```

---

## 438.151 — Impossible backend state

Register allocator failure hoặc illegal machine instruction là:

```text
compiler internal error
```

nếu source đã qua semantic validation.

---

## 438.152 — Machine verifier

Sau instruction selection:

```text
verify_machine_ir()
```

Sau register allocation:

```text
verify_allocated_machine_ir()
```

Sau encoding:

```text
verify_encoded_instruction()
```

---

## 438.153 — Backend pipeline khóa

```text
LIR
 ↓
Target Legalization
 ↓
Instruction Selection
 ↓
Machine IR
 ↓
Machine Verification
 ↓
Register Allocation
 ↓
Stack Frame
 ↓
Machine Scheduling
 ↓
Peephole
 ↓
Branch Relaxation
 ↓
Machine Verification
 ↓
Encoder
 ↓
Fixups
 ↓
Object Writer
```

---

# 438.154 — Hard invariants

1. ISA và ABI độc lập.
2. Host và target độc lập.
3. Backend không phụ thuộc frontend.
4. Generic backend không chứa ISA assumptions.
5. ISA backend không thực hiện semantic type checking.
6. Machine IR explicit về registers.
7. Virtual registers tồn tại trước allocation.
8. Physical registers chỉ được yêu cầu khi cần.
9. Register constraints phải được verify.
10. Stack alignment phải đúng ABI.
11. Call/return phải đúng ABI.
12. Atomic ordering phải preserve.
13. Volatile semantics phải preserve.
14. Unsupported CPU instruction không được emit.
15. PIC/PIE semantics phải preserve.
16. Relocation không được encode sai format.
17. Machine encoder tách object writer.
18. Branch relaxation phải deterministic.
19. Backend output deterministic.
20. x86-64 và AArch64 là native-first backends.
21. WASM là backend riêng, không giả lập register machine.
22. Không phụ thuộc LLVM/GCC/Clang.
23. Machine verifier bắt lỗi trước object emission.
24. Machine code golden tests bắt buộc.
25. ABI integration tests bắt buộc.
26. Cross-target tests bắt buộc.
27. Backend cost model không được thay đổi semantics.
28. Target-specific optimization chỉ xuất hiện sau target lowering.
29. Cache machine code phải phụ thuộc target/features/ABI.
30. Compiler phải có đường đi từ `fn main() -> i32 { return 42 }` tới executable thực tế.

**BOOTSTRAP-438 hoàn tất.**

---

# BOOTSTRAP-439 — OBJECT FILE, LINKER, RELOCATION, SYMBOL RESOLUTION & NATIVE IMAGE CONSTRUCTION

Đây là bước tiếp theo để nối machine code của 438 với **EXE / ELF / Mach-O / static library / dynamic library**.

## 439.1 — Linker architecture

Axiom linker chia thành:

```text
Object Reader
 ↓
Symbol Index
 ↓
Archive Extraction
 ↓
Section Graph
 ↓
Symbol Resolution
 ↓
COMDAT/Weak Resolution
 ↓
Section Layout
 ↓
Address Assignment
 ↓
Relocation
 ↓
Relaxation
 ↓
Import/Export
 ↓
Unwind/Debug Sections
 ↓
Image Construction
 ↓
Native Artifact
```

---

## 439.2 — Object abstraction

```text
ObjectFile {
    format
    architecture
    sections[]
    symbols[]
    relocations[]
    metadata[]
}
```

---

## 439.3 — Section

```text
Section {
    name
    kind
    flags
    alignment
    data
    relocations
}
```

Kinds:

```text
Code
ReadOnlyData
Data
Bss
TLS
Debug
Unwind
Metadata
```

---

## 439.4 — Section flags

```text
Readable
Writable
Executable
Alloc
TLS
Debug
Discardable
```

---

## 439.5 — Symbol

```text
Symbol {
    name
    binding
    visibility
    section
    value
    size
    type
}
```

---

## 439.6 — Symbol bindings

```text
Local
Global
Weak
Import
Export
Undefined
```

---

## 439.7 — Symbol resolution

Resolution phải deterministic.

Ưu tiên dựa trên:

```text
strong definition
→ weak definition
→ undefined/import
```

với rules riêng cho từng object format.

---

## 439.8 — Duplicate symbol

Hai strong definitions cùng symbol:

```text
link error
```

---

## 439.9 — Weak symbol

Weak definition có thể bị thay thế bởi strong definition theo platform/object semantics.

---

## 439.10 — Undefined symbol

Sau resolution nếu còn undefined:

```text
link error
```

trừ import/dynamic-symbol contract.

---

## 439.11 — Archive

Static library:

```text
archive
 ├── object A
 ├── object B
 └── object C
```

---

## 439.12 — Archive index

Axiom tạo symbol index để chỉ extract object cần thiết.

---

## 439.13 — Archive extraction

Không link toàn bộ archive mặc định.

Chỉ lấy members đáp ứng unresolved symbols.

---

## 439.14 — Link order

Axiom linker phải deterministic và không phụ thuộc accidental filesystem order.

---

## 439.15 — Section merging

Các section tương thích được merge:

```text
.text.*
→ .text
.rodata.*
→ .rodata
```

tùy target.

---

## 439.16 — Section GC

Nếu enabled:

```text
unreachable function/data
→ removed
```

---

## 439.17 — Root symbols

Roots gồm:

```text
entry point
exported symbols
required runtime symbols
FFI-required symbols
explicit linker roots
```

---

## 439.18 — Dead section elimination

Graph:

```text
root
 ↓
symbol
 ↓
section
 ↓
relocation
 ↓
another symbol
```

chỉ giữ reachable graph.

---

## 439.19 — Relocation model

Canonical:

```text
Relocation {
    offset
    type
    symbol
    addend
    width
}
```

---

## 439.20 — Relocation formula

Mỗi relocation type định nghĩa explicit formula:

```text
S = symbol address
P = relocation address
A = addend
B = image/section base
```

Ví dụ:

```text
S + A
S + A - P
B + S + A
```

---

## 439.21 — Relocation overflow

Nếu giá trị không fit field:

```text
link error
```

hoặc relaxation nếu relocation type cho phép.

---

## 439.22 — Absolute relocation

```text
ABS32
ABS64
```

---

## 439.23 — PC-relative relocation

```text
PCREL32
PCREL64
```

---

## 439.24 — Branch relocation

Backend có thể phát symbolic branch:

```text
label/function
```

linker/encoder resolve displacement.

---

## 439.25 — GOT/PLT relocation

Chỉ tạo khi dynamic/PIC model yêu cầu.

---

## 439.26 — TLS relocation

Target-specific relocation types được abstraction hóa.

---

## 439.27 — Relocation application

Pipeline:

```text
assign addresses
→ calculate relocation
→ range check
→ patch bytes
```

---

## 439.28 — Relocation safety

Không patch object trước khi:

```text
symbol resolution
+
layout
```

hoàn tất.

---

## 439.29 — Address assignment

Linker tạo:

```text
VirtualAddress
FileOffset
```

cho sections.

---

## 439.30 — Alignment

Section start phải thỏa:

```text
address % alignment == 0
```

---

## 439.31 — Segment construction

ELF/Mach-O/PE có section/segment concepts khác nhau.

Axiom giữ:

```text
LogicalSection
```

và format backend map chúng thành format-native segments/sections.

---

## 439.32 — ELF backend

Phải emit:

```text
ELF header
program headers
section data
section headers
symbols
relocations
dynamic metadata
```

theo artifact mode.

---

## 439.33 — PE/COFF backend

Phải emit:

```text
DOS/PE headers
COFF data
sections
imports
exports
relocations
entry point
image metadata
```

---

## 439.34 — Mach-O backend

Phải emit:

```text
Mach header
load commands
segments
sections
symbols
relocations
exports/imports
```

---

## 439.35 — Static library

Axiom archive format tương thích platform conventions khi cần.

---

## 439.36 — Dynamic library

Axiom linker có thể tạo:

```text
ELF .so
PE .dll
Mach-O .dylib
```

theo target.

---

## 439.37 — Executable

Final image có:

```text
entry point
code
readonly data
data
imports
exports
relocations if needed
runtime metadata
```

---

## 439.38 — Entry point

Axiom source:

```text
main()
```

không nhất thiết là OS entry point.

Linker/runtime có thể tạo:

```text
OS entry
→ Axiom startup
→ main
```

---

## 439.39 — Minimal freestanding executable

Có thể bỏ runtime startup:

```text
entry → user function
```

cho embedded/freestanding use cases.

---

## 439.40 — Runtime startup

Nếu std runtime dùng:

```text
OS entry
→ initialize runtime
→ initialize TLS
→ initialize globals
→ call main
→ terminate
```

---

## 439.41 — Global initialization

Không cho phép hidden arbitrary initialization.

Compiler tạo explicit initialization records khi cần.

---

## 439.42 — Initialization ordering

Dependency graph xác định thứ tự.

Không dựa vào linker file order.

---

## 439.43 — Finalization

Nếu resource cần finalization:

```text
shutdown component
```

được explicit runtime mechanism.

---

## 439.44 — Import table

Dynamic executable có:

```text
Import {
    library
    symbol
}
```

---

## 439.45 — Export table

Public ABI functions có:

```text
Export {
    symbol
    optional ordinal/platform metadata
}
```

---

## 439.46 — Symbol mangling

Axiom symbol mangling phải:

```text
deterministic
versioned
collision-resistant
```

---

## 439.47 — C ABI symbol

`extern "c"`:

```text
no Axiom generic mangling
```

trừ platform-required decoration.

---

## 439.48 — Generic exported functions

Không export generic function trực tiếp.

Phải export concrete wrapper.

---

## 439.49 — Dynamic symbol visibility

Source:

```text
pub
```

không tự động có nghĩa:

```text
dynamic export
```

Export phải là ABI/linker decision.

---

## 439.50 — Linker script

Không bắt buộc ở bootstrap.

Axiom có internal layout policy trước.

---

## 439.51 — Custom linker script

Có thể hỗ trợ sau cho embedded/kernel/system programming.

---

## 439.52 — Section ordering

Default:

```text
.text
.rodata
.data
.bss
```

nhưng target backend quyết định physical layout.

---

## 439.53 — Read-only data

String literals/constants ưu tiên `.rodata`.

---

## 439.54 — Writable globals

Mutable static:

```text
.data
```

---

## 439.55 — Zero-initialized globals

Có thể nằm `.bss` để giảm file size.

---

## 439.56 — Constant deduplication

Identical private constants có thể merge nếu address identity không observable hoặc semantics cho phép.

---

## 439.57 — Address identity

Compiler không được merge objects nếu user có thể observe distinct addresses.

---

## 439.58 — Function address identity

Hai functions khác nhau không được merge nếu language semantics cho phép so sánh function identity/address.

---

## 439.59 — Identical Code Folding

ICF là optional và phải obey address identity semantics.

---

## 439.60 — Link-time optimization

LTO có thể:

```text
IR
→ linker
```

nhưng không bắt buộc bootstrap.

---

## 439.61 — Thin LTO-like mode

Có thể lưu summaries thay vì toàn bộ IR.

---

## 439.62 — LTO boundary

LTO không được phá ABI/public symbols.

---

## 439.63 — Incremental linking

Axiom có thể cache:

```text
object
section layout
symbol resolution
```

nhưng final artifact phải deterministic.

---

## 439.64 — Reproducible executable

Không embed:

```text
random timestamp
random IDs
host absolute path
```

trừ khi explicitly requested.

---

## 439.65 — Build timestamp

Nếu artifact cần timestamp:

```text
SOURCE_DATE_EPOCH
```

hoặc explicit reproducible-build configuration.

---

## 439.66 — Build ID

Build ID có thể là:

```text
content hash
```

thay vì random UUID.

---

## 439.67 — Debug symbols

Debug sections có thể nằm:

```text
inside artifact
```

hoặc:

```text
separate debug artifact
```

---

## 439.68 — Strip

CLI:

```text
axiom build --strip
```

có thể remove debug symbols.

---

## 439.69 — Symbol map

Compiler có thể emit machine-readable symbol map:

```text
address
size
source
function
```

---

## 439.70 — Unwind metadata

Native artifact có thể chứa:

```text
unwind tables
```

nếu panic/unwind/debugging yêu cầu.

---

## 439.71 — Panic abort build

Nếu:

```text
panic=abort
```

không cần full exception unwind infrastructure.

---

## 439.72 — Panic unwind build

Nếu:

```text
panic=unwind
```

linker giữ unwind sections/runtime support.

---

## 439.73 — FFI unwind boundary

Cross-language unwind không được tự động xuyên qua FFI boundary.

---

## 439.74 — Dynamic loader assumptions

Axiom linker phải encode đủ metadata để OS loader thực hiện:

```text
imports
relocations
TLS
entry point
segments
```

---

## 439.75 — Static executable

Static build có thể embed Axiom runtime components trực tiếp.

---

## 439.76 — Runtime pruning

Chỉ link runtime components actually used.

Ví dụ program chỉ:

```text
print
```

không tự kéo:

```text
network
async executor
GUI
```

---

## 439.77 — Capability graph

Runtime components có dependency graph:

```text
io
 └── allocator
runtime
 ├── allocator
 └── panic
async
 ├── thread
 └── io
```

---

## 439.78 — Dead runtime elimination

Unused component bị loại.

---

## 439.79 — Object format reader

Axiom linker cũng phải đọc:

```text
Axiom object
ELF object
COFF object
Mach-O object
```

ở mức cần thiết cho interoperability.

---

## 439.80 — External object interoperability

Có thể link native object do:

```text
C
Rust
assembly
other compatible toolchain
```

miễn ABI tương thích.

Điều này **không** có nghĩa Axiom compiler phụ thuộc vào các compiler đó.

---

## 439.81 — External library

Axiom có thể consume:

```text
.lib
.a
.so
.dll
.dylib
```

tùy target.

---

## 439.82 — Import library

Windows `.lib` import libraries cần được parse/consume.

---

## 439.83 — Library search

Build system resolve:

```text
library path
library name
target
ABI
```

deterministically.

---

## 439.84 — ABI mismatch

Nếu external library ABI không tương thích:

```text
link/build diagnostic
```

---

## 439.85 — Object architecture mismatch

Ví dụ:

```text
x86-64 object
+
AArch64 target
```

→ link error.

---

## 439.86 — Object endian mismatch

Không cho link object incompatible endian.

---

## 439.87 — Relocation architecture mismatch

Không apply relocation type của architecture khác.

---

## 439.88 — Versioned symbols

Linux-style versioned symbols có thể được hỗ trợ ở platform backend sau.

---

## 439.89 — Symbol visibility

Hỗ trợ:

```text
default
hidden
protected
local
```

khi format có concept tương ứng.

---

## 439.90 — Import/export diagnostics

Compiler/linker phải chỉ rõ:

```text
undefined symbol
where referenced
expected ABI
target
```

---

## 439.91 — Link map

Optional:

```text
axiom link --map
```

cho biết:

```text
sections
symbols
sizes
dead sections
relocations
```

---

## 439.92 — Binary size report

Compiler có thể báo:

```text
code
rodata
data
bss
runtime
debug
```

---

## 439.93 — Size regression

Build system có thể compare artifact size với baseline.

---

## 439.94 — Linker diagnostics

Ví dụ:

```text
E439001 Undefined symbol
E439002 Duplicate symbol
E439003 Relocation overflow
E439004 Architecture mismatch
E439005 Invalid object
E439006 ABI mismatch
E439007 Invalid entry point
E439008 Unsupported relocation
```

---

## 439.95 — Object verification

Axiom có:

```text
verify-object
verify-executable
```

ở mức cấu trúc.

---

## 439.96 — Executable verification

Kiểm tra:

```text
header
sections
entry
segment permissions
relocations
imports
exports
```

---

## 439.97 — W^X

Native executable mặc định tránh segment vừa writable vừa executable nếu target/platform policy cho phép.

---

## 439.98 — Section permissions

Code:

```text
RX
```

readonly data:

```text
R
```

writable data:

```text
RW
```

---

## 439.99 — NX stack

Native executable ưu tiên non-executable stack nếu platform hỗ trợ.

---

## 439.100 — RELRO-like hardening

Platform-specific hardening có thể là build profile option.

Không hard-code vào language semantics.

---

## 439.101 — ASLR/PIE

Supported through target/link profile.

---

## 439.102 — Security metadata

Artifact có thể chứa platform security metadata.

---

## 439.103 — Linker determinism

Symbol traversal, section order và archive extraction phải deterministic.

---

## 439.104 — Parallel linking

Có thể parallelize:

```text
object parsing
symbol indexing
relocation preparation
```

nhưng final ordering deterministic.

---

## 439.105 — Link graph

Linker duy trì:

```text
Object
Section
Symbol
Relocation
```

graph để reachability analysis.

---

## 439.106 — Incremental graph cache

Graph nodes có content hashes.

---

## 439.107 — Cache invalidation

Thay đổi một object chỉ invalidate các dependent nodes.

---

## 439.108 — Link cache

Final cache key:

```text
objects
libraries
link options
target
ABI
linker version
runtime components
```

---

## 439.109 — Native artifact identity

Artifact hash phải được tính sau final bytes.

---

## 439.110 — Artifact manifest

Có thể tạo:

```text
artifact.json
```

gồm:

```text
target
compiler
ABI
source hash
dependencies
runtime components
debug status
```

---

## 439.111 — Artifact provenance

Build metadata giúp AI/compiler tools trả lời:

```text
binary này được tạo từ source nào?
target nào?
compiler nào?
```

---

## 439.112 — Self-contained linker milestone

Minimal linker phải link:

```text
main.o
runtime.o
```

thành executable.

---

## 439.113 — First ELF milestone

```text
Axiom source
→ x86-64 machine code
→ ELF object
→ Axiom linker
→ Linux executable
→ exit 42
```

---

## 439.114 — First PE milestone

```text
Axiom source
→ x86-64 machine code
→ COFF
→ Axiom PE linker
→ Windows executable
```

---

## 439.115 — First Mach-O milestone

```text
Axiom source
→ AArch64/x86-64 code
→ Mach-O object
→ Axiom linker
→ executable
```

---

## 439.116 — Static library milestone

```text
axiom build --kind staticlib
```

→ `.a` / platform equivalent.

---

## 439.117 — Dynamic library milestone

```text
axiom build --kind dylib
```

→ `.so` / `.dll` / `.dylib`.

---

## 439.118 — WASM artifact

WASM không đi qua native object linker pipeline.

```text
LIR
 ↓
WASM backend
 ↓
WASM module
```

---

## 439.119 — WASM linking

Nếu cần multiple modules:

```text
WASM object/component abstraction
```

sẽ được xử lý riêng.

---

## 439.120 — Linker architecture invariant

```text
Frontend → IR
Backend → Machine/Object
Linker → Artifact
```

Ba tầng không được nhập thành một monolithic compiler phase.

---

## 439.121 — Hard invariants

1. Axiom có native object writer.
2. Axiom có native linker.
3. ELF/PE/Mach-O có backend riêng.
4. Object format không phụ thuộc frontend.
5. Relocation semantics explicit.
6. Symbol resolution deterministic.
7. Duplicate strong symbols là error.
8. Undefined symbols chỉ hợp lệ nếu import contract cho phép.
9. Archive extraction chỉ lấy required members.
10. Dead section elimination có thể bật.
11. Exported/FFI symbols là linker roots.
12. ABI mismatch phải được phát hiện.
13. Architecture mismatch phải được phát hiện.
14. Relocation overflow không được silently truncate.
15. Section alignment phải được preserve.
16. Code/data permissions phải được phân biệt.
17. Runtime components phải được prune.
18. Debug information có thể tách khỏi release artifact.
19. Reproducible build phải loại bỏ nondeterministic metadata.
20. Link output phải deterministic.
21. Static library phải được hỗ trợ.
22. Dynamic library phải được hỗ trợ.
23. Executable phải có configurable entry/startup.
24. Freestanding artifact phải có thể bỏ runtime.
25. External native libraries có thể được consume qua ABI.
26. Axiom compiler không phụ thuộc third-party compiler.
27. Axiom linker không cần LLVM linker.
28. Object reader hỗ trợ interoperability ở mức cần thiết.
29. Final artifact hash được tính từ final bytes.
30. Pipeline phải đạt được:

```text
Axiom
 ↓
Machine Code
 ↓
Object
 ↓
Axiom Linker
 ↓
Native Executable
```

**BOOTSTRAP-439 hoàn tất.**

---

# BOOTSTRAP-440 — DEBUG INFO, STACK UNWINDING, PANIC/EXCEPTION RUNTIME & NATIVE DEBUGGER CONTRACT

Task tiếp theo sẽ khóa phần **không ảnh hưởng đến release performance nhưng cực kỳ quan trọng để Axiom có thể debug như một ngôn ngữ hệ thống thực thụ**:

```text
Source
 ↓
AST/HIR/MIR
 ↓
Machine instruction
 ↓
Debug location
 ↓
DWARF / CodeView / dSYM
 ↓
Debugger
```

và:

- source ↔ machine mapping;
- local variable location tracking;
- inline function debug info;
- stack frames;
- DWARF;
- Windows CodeView/PDB integration;
- Mach-O/dSYM;
- panic stack trace;
- unwind tables;
- `panic=abort`;
- `panic=unwind`;
- native exception interoperability;
- async stack traces;
- optimized debugging;
- crash dump;
- symbol server/local symbol cache;
- deterministic debug artifacts;
- sanitizer/debugger integration;
- `axiom debug`;
- AI-readable crash reports;
- compiler-generated source maps.

**Chuỗi tiếp theo sẽ tiếp tục từ BOOTSTRAP-440 mà không reset số.**