# BOOTSTRAP-418 — AXIOM LIR: LOW-LEVEL IR, STORAGE, ADDRESS SPACE & MACHINE-INDEPENDENT LOWERING

**Trạng thái:** SPECIFIED / FROZEN  
**Phụ thuộc:** 413 MIR, 416 Semantic Optimization, 417 ABI  
**Mục tiêu:** thiết kế **Axiom LIR** — tầng trung gian thấp hơn MIR nhưng vẫn chưa phụ thuộc một CPU cụ thể.

Đây là bước chuyển từ:

```text
"ý nghĩa chương trình"
```

sang:

```text
"chương trình sẽ được thực thi bằng những loại machine operation nào"
```

nhưng **chưa** quyết định instruction cụ thể của x86, ARM, RISC-V, WASM...

---

# 418.1. Vì sao cần LIR riêng?

Không nên:

```text
MIR → x86 assembly
```

trực tiếp.

MIR còn chứa quá nhiều semantic abstraction:

```text
ownership
Drop
traits
views
async
effects
high-level aggregate
```

Trong khi Machine IR cần:

```text
register
memory
address
load/store
branch
call
return
atomic
vector
```

Do đó:

```text
MIR
 ↓
ABI MIR
 ↓
Axiom LIR
 ↓
Machine IR
```

là ranh giới hợp lý.

---

# 418.2. MIR vs LIR

### MIR

Trả lời:

> Chương trình có semantics gì?

### LIR

Trả lời:

> Semantics đó được biểu diễn bằng low-level operations nào?

### Machine IR

Trả lời:

> CPU cụ thể thực hiện operations đó bằng instruction nào?

---

# 418.3. LIR không phải Assembly

LIR vẫn target-independent.

Ví dụ:

```text
LIR_ADD_I32
```

không phải:

```text
add eax, ebx
```

Tương tự:

```text
LIR_LOAD
```

không phải:

```text
ldr x0, [x1]
```

---

# 418.4. LIR Design Principle

Axiom LIR phải:

- nhỏ;
- explicit;
- SSA-friendly;
- machine-oriented;
- target-independent;
- dễ verify;
- dễ self-host;
- không phụ thuộc LLVM.

Không nên biến LIR thành một “LLVM clone”.

---

# 418.5. LIR Value

Mỗi LIR value:

```text id="j16r0u"
LirValue {
    id
    type
    representation
    class
}
```

Class:

```text id="k0h4ov"
INTEGER
FLOAT
VECTOR
POINTER
FLAGS
AGGREGATE
TOKEN
```

`TOKEN` dùng cho ordering/resource dependencies nội bộ compiler.

---

# 418.6. LIR Type

LIR không còn toàn bộ richness của Axiom Type System.

Các loại chính:

```text id="z4d7z8"
I8
I16
I32
I64
I128
U8
U16
U32
U64
U128
F32
F64
PTR
VECTOR
MASK
MEMORY
```

Aggregate lớn thường đã được ABI lowering.

---

# 418.7. Pointer ở LIR

Source language có thể tránh pointer syntax.

Nhưng LIR **bắt buộc** phải có pointer representation.

Ví dụ:

```text id="6a6z3a"
%p = address %x
```

Điều này không mâu thuẫn với thiết kế source language.

> Programmer không phải quản lý pointer; compiler vẫn phải có pointer để target machine.

---

# 418.8. Pointer Provenance

Pointer trong LIR phải mang metadata nội bộ:

```text id="8ab9dy"
PointerInfo {
    address_space
    provenance
    alignment
    bounds
    readonly
    writable
}
```

Machine code cuối cùng có thể chỉ còn một machine address.

Compiler giữ provenance trước codegen để không phá semantics.

---

# 418.9. Address Spaces

LIR hỗ trợ:

```text id="kw9cjb"
GENERIC
HOST
DEVICE
SHARED
LOCAL
CONSTANT
STACK
TLS
MMIO
EXTERNAL
```

Không phải target nào cũng hỗ trợ tất cả.

---

# 418.10. Memory Operation

LIR:

```text id="5m1w91"
LOAD
STORE
COPY
MEMSET
MEMCPY
```

có metadata:

```text id="j5x9oc"
type
alignment
volatile
atomic
ordering
address_space
alias_class
```

---

# 418.11. Load

Ví dụ:

```text id="fym6wr"
%v = load.i32 %ptr
```

Metadata:

```text id="6ujqgy"
alignment = 4
address_space = HOST
volatile = false
```

---

# 418.12. Store

```text id="m9jy3p"
store.i32 %value, %ptr
```

Nếu:

```text id="u4v4bf"
atomic = true
```

thì atomic ordering phải explicit.

---

# 418.13. Volatile

```text id="z29wgo"
load volatile
store volatile
```

không được:

- eliminate;
- reorder tùy tiện;
- merge tùy tiện.

Dùng cho:

- MMIO;
- hardware registers;
- externally observed memory.

---

# 418.14. Atomic

LIR hỗ trợ:

```text id="r5ecm2"
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
ATOMIC_FENCE
```

Ordering:

```text id="z2nq74"
RELAXED
ACQUIRE
RELEASE
ACQ_REL
SEQCST
```

---

# 418.15. Atomic Width

Backend phải kiểm tra target hỗ trợ:

```text id="fmb1sp"
8
16
32
64
128
```

Không được giả định mọi target hỗ trợ mọi width.

Nếu không native:

```text id="xq3h4y"
library/runtime fallback
```

hoặc compile error trong freestanding profile nếu không cho phép fallback.

---

# 418.16. Arithmetic Operations

LIR:

```text id="v8j7a4"
ADD
SUB
MUL
DIV
REM
NEG
ABS
MIN
MAX
```

có variant type-specific.

Ví dụ:

```text id="d8s5n8"
ADD_I32
ADD_U32
ADD_F32
```

Không dùng một `ADD` mơ hồ nếu semantics khác nhau.

---

# 418.17. Overflow Semantics

Integer operation phải encode semantics nếu cần:

```text id="m90m7g"
WRAP
CHECK
SATURATE
```

Ví dụ:

```text id="bf8t5j"
ADD_I32_WRAP
ADD_I32_CHECK
ADD_I32_SAT
```

Điều này ngăn backend biến semantics thành UB.

---

# 418.18. Shift

Shift cần semantics rõ:

```text id="w72v7d"
SHL
LSHR
ASHR
```

và compiler phải normalize shift count theo language rules.

---

# 418.19. Compare

```text id="e8h9xj"
CMP_EQ
CMP_NE
CMP_LT
CMP_LE
CMP_GT
CMP_GE
```

Integer và floating-point compare tách biệt.

Floating-point phải định nghĩa NaN semantics.

---

# 418.20. Floating-Point

LIR phải giữ:

```text id="y9g9nq"
rounding mode
exception behavior
fast-math profile
NaN semantics
signed zero semantics
```

nếu observable.

---

# 418.21. Vector

LIR hỗ trợ:

```text id="7j7xku"
VECTOR_SPLAT
VECTOR_LOAD
VECTOR_STORE
VECTOR_ADD
VECTOR_SUB
VECTOR_MUL
VECTOR_FMA
VECTOR_SHUFFLE
VECTOR_SELECT
```

Vector type:

```text id="5z3fbr"
<vector<T, N>>
```

---

# 418.22. Target-Neutral SIMD

Ví dụ:

```text id="9m3p7w"
<vector<f32, 4>>
```

có thể lower thành:

```text id="c4ymio"
SSE
AVX
NEON
SVE
RVV
```

backend quyết định instruction.

---

# 418.23. Mask

Vector comparison tạo:

```text id="5j8f4c"
mask<N>
```

Có thể dùng cho:

```text id="u9m9th"
VECTOR_SELECT
masked_load
masked_store
```

---

# 418.24. Control Flow

LIR CFG vẫn gồm:

```text id="0f7c6q"
BLOCK
BR
COND_BR
SWITCH
RETURN
UNREACHABLE
```

Nhưng không còn high-level:

```text id="8y7j5r"
match
for
async await
trait dispatch
```

---

# 418.25. Conditional Branch

```text id="w9t2pb"
condbr %cond, BB_true, BB_false
```

Target backend sau đó map thành:

```text id="g8x9h4"
conditional jump
```

---

# 418.26. Switch

```text id="s7y4k6"
switch %tag {
    0 -> BB0
    1 -> BB1
    default -> BBdefault
}
```

Backend có thể chọn:

- jump table;
- binary tree;
- range check;
- branch chain.

---

# 418.27. Phi / SSA

LIR tiếp tục hỗ trợ SSA:

```text id="2r7z9v"
%x = phi [v1, BB1], [v2, BB2]
```

Sau đó register allocator sẽ loại bỏ phi bằng parallel copy.

---

# 418.28. Memory SSA

Đối với memory:

```text id="k4v3ut"
LOAD
STORE
CALL
ATOMIC
```

compiler cần tracking memory dependencies.

Không nhất thiết expose Memory SSA như source-visible IR, nhưng LIR optimizer cần alias/memory dependency graph.

---

# 418.29. Call

```text id="4t9xw5"
CALL target(args)
```

metadata:

```text id="w7m8ku"
calling_convention
return_abi
argument_abi
clobbers
effects
nounwind
```

---

# 418.30. Indirect Call

```text id="r6k9u8"
CALL_INDIRECT %fnptr
```

phải chứa function signature/ABI metadata.

Backend không được đoán calling convention từ pointer bits.

---

# 418.31. Tail Call

LIR có:

```text id="f2a3c8"
TAILCALL
```

nếu ABI cho phép.

Compiler có thể biến recursion:

```text id="z4n7ax"
f() → f()
```

thành jump mà không tăng stack.

---

# 418.32. Calling Convention Lowering

ABI layer đã quyết định:

```text id="w9u8p4"
argument → register/stack
return → register/memory
```

LIR chỉ biểu diễn kết quả.

Ví dụ:

```text id="s8h7cc"
CALL @foo
```

với explicit ABI locations nội bộ.

---

# 418.33. Stack Model

LIR có semantic stack operations:

```text id="x3c7bp"
STACK_ALLOC
STACK_FREE
STACK_ADDRESS
```

Nhưng compiler có thể eliminate stack allocation.

---

# 418.34. Dynamic Stack Allocation

Nếu source/library yêu cầu dynamic stack:

```text id="o8t6mz"
STACK_ALLOC_DYNAMIC
```

phải ghi:

```text id="7x1e6v"
alignment
size
lifetime
```

Không được mặc định sử dụng OS heap.

---

# 418.35. Stack Lifetime

LIR verifier phải đảm bảo:

```text id="j8u4x5"
stack address
```

không escape sau frame lifetime nếu ABI không cho phép.

Escape:

```text id="8n8v2q"
return pointer to stack
```

phải bị MIR ownership verifier ngăn từ trước.

---

# 418.36. TLS

LIR có:

```text id="0i7g1e"
TLS_ADDRESS
```

để biểu diễn thread-local storage.

Backend mapping:

```text id="f7k8s4"
PE TLS
ELF TLS
Mach-O TLS
```

---

# 418.37. Global Address

```text id="3n6d9m"
GLOBAL_ADDRESS @symbol
```

Backend tạo relocation tương ứng.

---

# 418.38. Function Address

```text id="8h9k5z"
FUNCTION_ADDRESS @foo
```

cần phân biệt:

```text id="1x2r9j"
direct callable address
data pointer
PLT/GOT/import thunk
```

---

# 418.39. Relocation

LIR không cần encode relocation binary cụ thể.

Nhưng symbolic references phải tồn tại:

```text id="j0k8c6"
SymbolRef
RelocKind
Addend
```

Object writer xử lý sau.

---

# 418.40. Section Placement

LIR có metadata:

```text id="r5w3qm"
section = code
section = rodata
section = data
section = bss
section = tls
```

Backend/object writer có thể điều chỉnh.

---

# 418.41. Constant Pool

LIR hỗ trợ:

```text id="2y8x7v"
CONST_INT
CONST_FLOAT
CONST_VECTOR
CONST_BYTES
CONST_ADDRESS
```

Large constants có thể đưa vào constant pool.

---

# 418.42. String/Data Literals

Source:

```axiom id="k5s7m1"
"hello"
```

sau semantic lowering có thể trở thành:

```text id="4x5z9q"
GLOBAL_CONST @.str.1
```

Không cần runtime allocation.

---

# 418.43. Memory Copy

```text id="z1x9w2"
MEMCPY dst, src, size
```

compiler có thể:

- inline;
- vectorize;
- replace with loads/stores;
- gọi platform intrinsic.

---

# 418.44. `memmove` vs `memcpy`

Phải phân biệt:

```text id="a4q5r8"
MEMCPY
MEMMOVE
```

vì overlap semantics khác nhau.

Compiler chỉ dùng `MEMCPY` khi alias proof đảm bảo non-overlap.

---

# 418.45. Zero Initialization

```text id="f7j2k1"
MEMZERO
```

có thể map:

- memset;
- vector stores;
- OS page zero;
- linker `.bss`.

---

# 418.46. Bitcast

```text id="z8u2s7"
BITCAST<T>(x)
```

khác:

```text id="8k6s4p"
CAST<T>(x)
```

Bitcast giữ bit representation.

CAST thay đổi numeric/semantic value.

---

# 418.47. Pointer Arithmetic

LIR có thể có:

```text id="1h4q8b"
PTR_ADD
PTR_OFFSET
```

nhưng provenance phải được kiểm soát.

Không được để optimizer coi:

```text id="5d5f8j"
integer address arithmetic
```

tự động là valid pointer.

---

# 418.48. Bounds Metadata

Pointer derived từ view có thể mang:

```text id="x1z7u6"
bounds
```

Optimizer có thể dùng để:

```text id="9x7m3c"
bounds-check elimination
```

Sau khi machine lowering, metadata có thể biến mất.

---

# 418.49. Pointer Alignment

Mỗi pointer operation có thể có:

```text id="b7s5m2"
known_alignment
```

Ví dụ:

```text id="2w9k3e"
align >= 16
```

cho phép vectorized load.

Nếu alignment không chắc:

```text id="m4v8q1"
unaligned access
```

---

# 418.50. Alias Class

LIR memory operation có:

```text id="k5m6x8"
AliasClass
```

ví dụ:

```text id="0p3v9a"
NoAlias
ReadOnly
Mutable
Atomic
Volatile
External
Unknown
```

Compiler có thể dùng để tối ưu memory scheduling.

---

# 418.51. `NoAlias` chỉ từ Proof

Không được programmer viết tùy tiện:

```text id="w7j4v2"
noalias
```

rồi compiler tin.

LIR `NoAlias` chỉ xuất hiện từ:

```text id="n4x7u8"
ownership
capability
region
ABI
unsafe contract
```

đã được verify.

---

# 418.52. Exception/Panic Lowering

MIR:

```text id="0r3f9p"
PANIC
```

LIR có thể thành:

```text id="g8s6t1"
CALL panic_handler
UNREACHABLE
```

hoặc:

```text id="k9p2c4"
TRAP
```

hoặc unwind sequence.

---

# 418.53. `TRAP`

```text id="y2v5r7"
TRAP
```

là machine-visible termination event.

Không giống:

```text id="m4s6q8"
PANIC
```

vì panic có thể unwind.

---

# 418.54. Unwind

LIR cần:

```text id="z5c7m3"
INVOKE
LANDINGPAD
RESUME_UNWIND
```

chỉ khi target/profile hỗ trợ.

Nếu abort profile:

```text id="f7n2a4"
CALL → no-return
```

đủ.

---

# 418.55. Barrier

LIR:

```text id="r6u8w1"
COMPILER_BARRIER
MEMORY_BARRIER
DEVICE_BARRIER
```

phải phân biệt.

Compiler barrier:

> không reorder compiler operations qua barrier.

Memory barrier:

> machine memory ordering semantics.

Device barrier:

> GPU/device visibility.

---

# 418.56. GPU LIR

GPU-specific MIR sau lowering có thể thành:

```text id="d4q7n2"
KERNEL_ENTRY
THREAD_ID
BLOCK_ID
GRID_SIZE
BARRIER
DEVICE_LOAD
DEVICE_STORE
GPU_ATOMIC
```

Sau đó GPU backend map sang:

```text id="f9j5k3"
CUDA-like ISA
SPIR-V
DXIL
Metal
ROCm
```

Axiom LIR không nhất thiết phải là CUDA IR.

---

# 418.57. SIMD và GPU không phải hai type system

Cả hai dùng:

```text id="8m5r2v"
Vector
Memory
AddressSpace
Barrier
Atomic
```

khác execution domain.

Điều này giữ compiler architecture thống nhất.

---

# 418.58. Device Pointer

Device pointer:

```text id="q5n8s1"
PTR<DEVICE>
```

không được implicit convert thành:

```text id="7x4m9k"
PTR<HOST>
```

LIR verifier phải giữ address-space identity.

---

# 418.59. DMA / External Memory

LIR có:

```text id="w3j6r8"
EXTERNAL_LOAD
EXTERNAL_STORE
DMA_TRANSFER
```

nếu backend/runtime yêu cầu.

Ownership vẫn được kế thừa từ MIR.

---

# 418.60. LIR Lowering Example

Source:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

MIR:

```text id="0y7q4k"
%1 = load a
%2 = load b
%3 = add_i32 %1, %2
return %3
```

ABI MIR:

```text id="j6u2s5"
arg0 → ABI location 0
arg1 → ABI location 1
return → ABI return location
```

LIR:

```text id="4x6r8n"
bb0:
    %r0 = ARG 0
    %r1 = ARG 1
    %r2 = ADD_I32 %r0, %r1
    RETURN %r2
```

Machine backend sau đó quyết định:

```text id="k2w7m9"
x86:
    add

ARM:
    add

RISC-V:
    add
```

---

# 418.61. LIR Example với Memory

Source:

```axiom
fn inc(x: mut_view<i32>) {
    x[0] += 1
}
```

LIR:

```text id="p9s2v4"
%base = VIEW_PTR x
%old  = LOAD_I32 %base
%new  = ADD_I32 %old, 1
STORE_I32 %base, %new
```

Capability proof đã xảy ra ở MIR.

LIR chỉ còn memory semantics cần thiết.

---

# 418.62. LIR Example với Struct

```axiom
struct Point {
    x: f32
    y: f32
}
```

Sau scalarization:

```text id="e7p4n9"
%px = ...
%py = ...
```

Nếu address/layout không observable.

Nếu `@repr(C)` + FFI:

```text id="v3k6s1"
physical aggregate layout
```

phải được giữ.

---

# 418.63. LIR Example với Allocation

Source:

```axiom
let x = Box::new(T(...))
use(x)
```

Nếu allocation eliminated:

```text id="t2m7q5"
construct T
use T
```

Nếu allocation thật sự cần:

```text id="c9w4r8"
%mem = ALLOC size, align
...
DEALLOC %mem
```

Nhưng `ALLOC` vẫn target-independent.

---

# 418.64. LIR Allocation

```text id="e5k8p2"
ALLOC {
    size
    alignment
    address_space
    lifetime
    allocator_class
}
```

`allocator_class` có thể:

```text id="g1j3v7"
STACK
HEAP
ARENA
POOL
OS
DEVICE
EXTERNAL
UNKNOWN
```

Optimizer/backend có thể thay đổi implementation nếu semantic contract cho phép.

---

# 418.65. LIR Register Classes

LIR chưa gán register vật lý nhưng có thể yêu cầu:

```text id="s6x9k4"
INTEGER_REG
FLOAT_REG
VECTOR_REG
FLAGS_REG
ADDRESS_REG
```

Machine backend mapping tùy CPU.

---

# 418.66. Constraint

Instruction/call có thể yêu cầu:

```text id="y8w2n6"
required register class
fixed register
alignment
clobbers
```

Ví dụ một số ABI/hardware instruction cần register cụ thể.

---

# 418.67. LIR Verification

Verifier kiểm tra:

```text id="v6h3q9"
SSA correctness
type correctness
CFG correctness
memory ordering
address-space legality
alignment
atomic semantics
ABI correctness
pointer provenance
call signature
return convention
```

---

# 418.68. LIR không được chứa High-Level Semantic Unknowns

Trước Machine lowering, không được còn:

```text id="v2k5m8"
unresolved trait call
unknown type
unknown ownership
unknown Drop
unknown ABI
unknown effect
```

Nếu còn:

```text id="s9d4x1"
compiler error
```

---

# 418.69. LIR Canonical Form

Để dễ self-host và debug, Axiom định nghĩa canonical LIR:

```text id="f3h7k2"
SSA
explicit CFG
explicit memory operations
explicit calls
explicit ABI locations
explicit atomics
explicit address spaces
```

Canonicalization giúp:

- caching;
- deterministic compiler output;
- compiler testing;
- AI inspection.

---

# 418.70. LIR Serialization

Có thể có:

```text id="j8q4m6"
.axlir
```

nhưng đây là **internal compiler artifact**, không phải stable public binary interface.

Dùng cho:

- compiler cache;
- debugging;
- compiler bootstrap;
- regression testing;
- AI/compiler analysis.

---

# 418.71. CompilerDB

Thêm:

```text id="x3c8v5"
LIRDB
LIRFunctionDB
LIRBlockDB
LIRValueDB
LIRMemoryDB
LIRAddressSpaceDB
LIRPointerDB
LIRAtomicDB
LIRVectorDB
LIRCallDB
LIRAbiDB
LIRGlobalDB
LIRRelocationDB
LIRVerificationDB
LIRDebugDB
LIRGpuDB
```

---

# 418.72. Proofs

```text id="p4n8y2"
LIRLoweringProof
LIRTypeProof
LIRCFGProof
LIRMemoryProof
LIRPointerProvenanceProof
LIRAlignmentProof
LIRAtomicProof
LIRAddressSpaceProof
LIRCallABIProof
LIRReturnABIProof
LIRRelocationProof
LIRGpuProof
LIRVerificationProof
```

---

# 418.73. Invariants `ALIR`

```text id="8x4m7q"
ALIR-01  Every LIR value has a valid LIR type.
ALIR-02  Every definition dominates its uses.
ALIR-03  Every block has a valid terminator.
ALIR-04  Every call has a valid ABI contract.
ALIR-05  Every return follows the ABI return contract.
ALIR-06  Aggregate lowering preserves representation semantics.
ALIR-07  Pointer provenance is preserved through lowering.
ALIR-08  Integer address values are not implicitly valid pointers.
ALIR-09  Pointer address spaces cannot be silently mixed.
ALIR-10  Memory operations carry valid alignment information.
ALIR-11  Atomic operations carry explicit ordering.
ALIR-12  Volatile operations remain observable.
ALIR-13  MMIO operations remain externally observable.
ALIR-14  Unknown aliasing is not converted to NoAlias.
ALIR-15  Stack addresses cannot illegally escape their lifetime.
ALIR-16  ABI hidden parameters are internally consistent.
ALIR-17  Calling conventions are explicit.
ALIR-18  Tail calls satisfy ABI constraints.
ALIR-19  Variadic calls use compatible ABI rules.
ALIR-20  Panic/trap/unwind remain semantically distinct.
ALIR-21  GPU address spaces remain isolated.
ALIR-22  Device pointers cannot silently become host pointers.
ALIR-23  Allocation semantics remain explicit.
ALIR-24  Memory copy operations preserve overlap semantics.
ALIR-25  Bitcast is distinct from numeric conversion.
ALIR-26  Vector operations preserve lane semantics.
ALIR-27  LIR contains no unresolved high-level semantic entity.
ALIR-28  LIR lowering is deterministic for identical inputs.
ALIR-29  LIR remains verifiable before machine lowering.
ALIR-30  Machine lowering cannot reinterpret invalid LIR semantics.
```

---

# 418.74. Kiến trúc compiler lúc này

Axiom đã có một chuỗi lowering rất rõ:

```text
SOURCE
  │
  ▼
AST
  │
  ▼
HIR
  │
  ▼
Typed HIR
  │
  ▼
MIR
  │
  ├── Ownership
  ├── Capability
  ├── Effect
  ├── Concurrency
  ├── Async
  ├── GPU
  └── Drop
  │
  ▼
Verified MIR
  │
  ▼
Semantic Optimization
  │
  ▼
Optimized MIR
  │
  ▼
ABI Lowering
  │
  ▼
ABI MIR
  │
  ▼
AXIOM LIR
  │
  ▼
Machine IR
  │
  ▼
Register Allocation
  │
  ▼
Machine Encoder
  │
  ▼
Object
  │
  ▼
Linker
  │
  ▼
EXE / ELF / Mach-O / WASM / ...
```

Điểm quan trọng của 418:

> **LIR là lớp “dịch ngôn ngữ sang máy”, nhưng chưa phải lớp “dịch sang CPU”.**

Nhờ có lớp này, Axiom có thể hỗ trợ nhiều backend mà không phải viết lại toàn bộ compiler semantic:

```text
Axiom MIR
     ↓
 Axiom LIR
     ├── x86-64 backend
     ├── ARM64 backend
     ├── RISC-V backend
     ├── WASM backend
     ├── GPU backend
     └── future backend
```

Đồng thời đây cũng là nền tảng cần thiết để Axiom **tự viết machine code/object writer của chính mình**, thay vì phụ thuộc vĩnh viễn vào LLVM.

**BOOTSTRAP-418 — SPECIFIED / FROZEN.**